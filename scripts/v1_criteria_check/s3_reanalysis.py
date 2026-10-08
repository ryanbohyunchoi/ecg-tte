#!/usr/bin/env python
"""Step 3: paper 1 primary analysis with the exclusion-type cohort fixes, per trial and pooled (S32).

Cells: PS-Demo (P1) base vs P1 + ECG (32 PCs), main configuration (1:1 greedy caliper 0.2 SD of the PS logit, L2 C = 1),
computed exactly as scripts/v20/sens_primary32.py task(): E.run_cell on the v16_engine trial object (load_trial as there),
cstat=None; a fix is a row subset (rows = analysed positions not flagged; X = design rows). ECG PCs are NOT recomputed:
T.ecg_pc (PCA fitted on the full analysed cohort, unsupervised) is kept, as in v1 subset analyses
(scripts/v1_audit/code/sens_no_index_day_ecg.py). Outcome fixes (secondary): T.y_t / T.y_e replaced on a shallow copy.

Gate: the unchanged-cohort cells must reproduce audits/claude-v20-sens-primary32/restricted_cells.parquet
(P1, main, base k0 / ECG k32) for every column (max |dev| reported; must be 0).

Outputs (OUT = audits/claude-v1-criteria): restricted_fix_cells.parquet (restricted), gate.csv, per_trial_fixes.csv
(aggregate; retained n suppressed when any arm's removed count is 1-10), pooled.csv.
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import copy  # noqa: E402
import sys  # noqa: E402
from multiprocessing import Pool  # noqa: E402

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v20")
import sens_primary32 as SP  # noqa: E402  (imports the v1 engine exactly as the published run)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v1_criteria_check")
import common as K  # noqa: E402

E, AF, V = SP.E, SP.AF, SP.V
VN = SP.VN
COLS = ["n", "n_t", "n_c", "n_pairs", "loghr", "se"] + [f"smd:{c}" for c in VN]

# exclusion fixes: trial -> {variant: list of flag columns OR-ed}; "all" = every exclusion fix for the trial (pooled)
FIX = {
    "comet": {"succinate_365": ["fx_comet_succinate"], "lvef_gt35": ["fx_comet_lvef35"], "all": ["fx_comet_succinate", "fx_comet_lvef35"]},
    "elite-ii": {"all": ["fx_arni"]},
    "valiant": {"arni": ["fx_arni"], "ef_unknown_no_hf": ["ef_unknown_no_hf"], "ef_hf_incl_index_echo": ["fx_valiant_ef_hf"],
                "all": ["fx_arni", "fx_valiant_ef_hf"]},
    "emperor-preserved-v2": {"all": ["fx_saxalo"]},
    "declare": {"saxalo": ["fx_saxalo"], "sglt2_washout": ["fx_washout"], "all": ["fx_saxalo", "fx_washout"]},
    "leader": {"all": ["fx_washout"]}, "sustain6": {"all": ["fx_washout"]}, "rewind": {"all": ["fx_washout"]},
    "canvas": {"all": ["fx_washout"]},
    "carolina": {"all": ["fx_carolina_age"]},
    "laaos3": {"af_ge_idx_minus1": ["first_af_ge_idx_minus1"], "all": ["fx_laaos3_postop_af"]},
    "life": {"hedged_strict": ["fx_life_hedged_strict"], "all": ["fx_life_hedged_primary"]},
}
OUTFIX = ["amplify", "lodestar", "prove-it"]  # outcome fixes (secondary)


def outcome_fix(T, n):
    """new (y_t, y_e) for the outcome fix; restricted, in memory."""
    import s2_flags as S
    from trial_common import code_like, rp
    from trial_specs import CABG_CODES, DEATH_END, HORIZON_MONTHS, PCI_CODES, PRIMARY_BILLING
    D, con = S.setup(n)
    assert (pd.Index(D.patient_key) == T.keys).all()
    S.stays(con)
    idx = D.set_index("patient_key").index_date
    key = {"amplify": "amplify", "lodestar": "lodestar", "prove-it": "prove_it"}[n]
    H = int(round(HORIZON_MONTHS[key] * 30.4375))
    yt, ye = T.y_t.copy().astype(float), T.y_e.copy().astype(int)
    if n in ("lodestar", "prove-it"):
        lo = "x.idx + INTERVAL 30 DAY" if n == "prove-it" else "x.idx_stay_end + INTERVAL 1 DAY"
        rv = con.execute(f"""SELECT x.patient_key, min(p.procedure_date) d FROM idxstay x JOIN {rp(S.G, 'procedure_occurrence')} p
            ON p.person_id = x.person_id WHERE p.procedure_date >= {lo}
              AND {code_like('upper(p.procedure_source_value)', PCI_CODES + CABG_CODES)} GROUP BY 1""").df().set_index("patient_key").d
        rt = (pd.to_datetime(rv.reindex(T.keys)) - idx.reindex(T.keys)).dt.days.to_numpy(float)
        hit = np.isfinite(rt) & (rt <= yt) & T.y_ok
        yt[hit], ye[hit] = rt[hit], 1
    else:  # AMPLIFY: recurrent VTE = first stay after the index stay with a primary hospital-billing VTE code
        ev = con.execute(f"""SELECT x.patient_key, min(st.s) d FROM idxstay x JOIN stays st ON st.person_id = x.person_id AND st.s > x.idx_stay_end
            JOIN {rp(S.G, 'condition_occurrence')} c ON c.person_id = x.person_id AND c.condition_start_date BETWEEN st.s AND st.e
            WHERE c.condition_status_source_value = '{PRIMARY_BILLING}' AND {code_like("upper(replace(c.condition_source_value, '.', ''))", S.VTE)}
            GROUP BY 1""").df().set_index("patient_key").d
        dd = con.execute(f"SELECT k.patient_key, min(d.death_date) dd FROM k JOIN {rp(S.G, 'death')} d USING (person_id) GROUP BY 1").df().set_index("patient_key").dd
        i = idx.reindex(T.keys)
        evd = pd.to_datetime(ev.reindex(T.keys))
        ddd = pd.to_datetime(dd.reindex(T.keys))
        ddd = ddd.where(~(ddd < i))
        end = pd.Series(pd.Timestamp(DEATH_END), index=T.keys).clip(upper=i + pd.Timedelta(days=max(H, int(round(60 * 30.4375)))))
        stop = pd.concat([evd, end, ddd], axis=1).min(axis=1)
        event = evd.notna() & (evd <= end) & ~(ddd < evd)
        stop = stop.where(~event, evd)
        t = (stop - i).dt.days.astype(float)
        t = t.where(t > 0, 0.5).to_numpy()
        yt = np.minimum(t, H)
        ye = (event.to_numpy() & (t <= H)).astype(int)
    con.close()
    return yt, ye


def cells(T, n, rows, tag, Tuse=None):
    TT = T if Tuse is None else Tuse
    r_all = np.arange(len(T.t))
    X1 = T.cov.iloc[r_all][T.demo].to_numpy(float)
    XE = np.hstack([X1, T.ecg_pc])
    est, psm = SP.CONFIGS["main"]
    out = []
    for arm, X in (("base", X1), ("ECG", XE)):
        o = E.run_cell(TT, X if rows is None else X[rows], rows=r_all if rows is None else rows, estimator=est, ps_model=psm, cstat=None)
        out.append(dict(trial=n, key=SP.KEY[n], variant=tag, arm=arm, k_pcs=0 if arm == "base" else 32, rb=T.rb, rs=T.rs, ex58="",
                        **{c: o[c] for c in COLS}))
    return out


def task(n):
    K.umask()
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    F = pd.read_parquet(K.OUT / "flags" / f"restricted_flags_{n}.parquet").set_index("patient_key")
    assert F.index.equals(T.keys), n
    assert (F.treated.to_numpy() == T.t).all(), n
    out = cells(T, n, None, "unchanged")
    meta = []
    for v, flags in FIX.get(n, {}).items():
        drop = F[flags].any(axis=1).to_numpy()
        rows = np.where(~drop)[0]
        out += cells(T, n, rows, v)
        meta.append(dict(trial=n, variant=v, n=len(drop), removed=int(drop.sum()), removed_t=int(drop[T.t == 1].sum()),
                         removed_c=int(drop[T.t == 0].sum()), n_t=int((T.t == 1).sum()), n_c=int((T.t == 0).sum())))
    if n in OUTFIX:
        yt, ye = outcome_fix(T, n)
        T2 = copy.copy(T)
        T2.y_t, T2.y_e = yt, ye
        out += cells(T, n, None, "outcome_fix", Tuse=T2)
        meta.append(dict(trial=n, variant="outcome_fix", n=len(yt), events_old=int((T.y_e[T.y_ok] == 1).sum()),
                         events_new=int((ye[T.y_ok] == 1).sum())))
    print(n, "done", flush=True)
    return out, meta


# ---------------------------------------------------------------- pooled
def pooled_contrast(R, trials):
    """paper 1 primary contrast (S32 set, main, P1 ECG vs base) via sens_primary32.per_trial / contrast_row."""
    CL = V.cluster_of()
    g = {a: R[R.arm == a].set_index("trial", drop=False).loc[trials] for a in ("base", "ECG")}
    Fb, SMb = SP.per_trial(g["base"])
    Fa, SMa = SP.per_trial(g["ECG"])
    c = SP.contrast_row(Fa, Fb, trials, "one", CL, SMa, SMb)
    return dict(n_trials=len(trials), relred=c["relred"], relred_lo=c["relred_lo"], relred_hi=c["relred_hi"],
                m58_base=c["m58_b"], m58_ecg=c["m58_a"], m58_p=c["m58_p"], lt01_p=c["lt01_p"],
                absd_base=c["absd_b"], absd_ecg=c["absd_a"], absd_better=c["absd_better"], absd_p=c["absd_p"])


def published_cells():
    R = pd.read_parquet(SP.OUT / "restricted_cells.parquet")
    R = R[(R.rung == "P1") & (R.config == "main") & (((R.arm == "base") & (R.k_pcs == 0)) | ((R.arm == "ECG") & (R.k_pcs == 32)))]
    return R


def fmt_retained(m):
    small = any(1 <= m[c] < K.MIN_CELL for c in ("removed_t", "removed_c"))
    if small:
        return f"~{100 * (1 - m['removed'] / m['n']):.0f}% (arm cell <11)", f"~{100 * m['removed'] / m['n']:.0f}%"
    return f"{m['n'] - m['removed']} ({100 * (1 - m['removed'] / m['n']):.1f}%)", f"{K.sup(m['removed'])} ({K.pct(m['removed'], m['n'])}%)"


def main(workers):
    K.umask()
    trials = list(FIX) + OUTFIX
    with Pool(min(workers, len(trials))) as p:
        res = p.map(task, trials, chunksize=1)
    C = pd.DataFrame([x for o, _ in res for x in o])
    M = pd.DataFrame([x for _, m in res for x in m])
    C.to_parquet(K.OUT / "restricted_fix_cells.parquet")
    M.to_parquet(K.OUT / "restricted_fix_meta.parquet")
    # ---- gate
    P = published_cells()
    g = []
    for n in trials:
        for a in ("base", "ECG"):
            x = C[(C.trial == n) & (C.variant == "unchanged") & (C.arm == a)].iloc[0]
            y = P[(P.trial == n) & (P.arm == a)].iloc[0]
            dev = max(float(np.nan_to_num(abs(float(x[c]) - float(y[c])), nan=0.0)) for c in COLS)
            nanm = sum(int(np.isnan(float(x[c])) ^ np.isnan(float(y[c]))) for c in COLS)
            g.append(dict(trial=n, arm=a, maxdev=dev, nan_mismatch=nanm))
    G = pd.DataFrame(g)
    G.to_csv(K.OUT / "gate.csv", index=False)
    print(G.to_string(index=False))
    print("GATE maxdev", G.maxdev.max(), "nan mismatches", G.nan_mismatch.sum(), flush=True)
    if G.maxdev.max() > 0 or G.nan_mismatch.sum() > 0:
        print("GATE FAILED: stopping before any comparison", flush=True)
        return
    summarize()


def summarize():
    K.umask()
    C = pd.read_parquet(K.OUT / "restricted_fix_cells.parquet")
    M = pd.read_parquet(K.OUT / "restricted_fix_meta.parquet")
    # ---- per trial
    rows = []
    for (n, v), g in C.groupby(["trial", "variant"], sort=False):
        b, e = g[g.arm == "base"], g[g.arm == "ECG"]
        Fb, _ = SP.per_trial(b.set_index("trial", drop=False))
        Fe, _ = SP.per_trial(e.set_index("trial", drop=False))
        r = dict(trial=n, label=K.FLAGGED[n], in_S32=n in SP.S32, variant=v, n_analysed=int(b.n.iloc[0]) if v == "unchanged" else None,
                 m58_base=Fb.m58.iloc[0], m58_ecg=Fe.m58.iloc[0], absd_base=Fb.absd.iloc[0], absd_ecg=Fe.absd.iloc[0],
                 loghr_base=Fb.loghr.iloc[0], loghr_ecg=Fe.loghr.iloc[0], rct_loghr=Fb.rb.iloc[0], pairs_ge11=bool(min(b.n_pairs.iloc[0], e.n_pairs.iloc[0]) >= 11))
        if v not in ("unchanged", "outcome_fix"):
            m = M[(M.trial == n) & (M.variant == v)].iloc[0]
            r["retained"], r["removed"] = fmt_retained(m)
        if v == "outcome_fix":
            m = M[(M.trial == n) & (M.variant == v)].iloc[0]
            r["retained"] = "all (outcome changed)"
            r["removed"] = f"events {K.sup(m.events_old)} -> {K.sup(m.events_new)}"
        rows.append(r)
    PT = pd.DataFrame(rows)
    PT.to_csv(K.OUT / "per_trial_fixes.csv", index=False)
    pd.set_option("display.width", 250)
    print(PT.round(4).to_string(index=False))
    # ---- pooled
    P = published_cells()
    S32 = SP.S32
    base = P[P.trial.isin(SP.ALL)].copy()
    out = []
    out.append(dict(analysis="published cells (gate: must equal 11.4%, 0.251 -> 0.205)", set="S32", **pooled_contrast(base, S32)))
    allfix = C[C.variant == "all"]
    R1 = pd.concat([base[~base.trial.isin(allfix.trial)], allfix], ignore_index=True)
    out.append(dict(analysis="all exclusion-type fixes applied simultaneously", set="S32", **pooled_contrast(R1, S32)))
    of = C[C.variant == "outcome_fix"]
    R2 = pd.concat([R1[~R1.trial.isin(of.trial)], of], ignore_index=True)
    out.append(dict(analysis="exclusion fixes + outcome fixes (AMPLIFY primary-billing VTE; LODESTAR/PROVE IT + revascularisation)",
                    set="S32", **pooled_contrast(R2, S32)))
    # leave-one-fix-in (each trial's fix alone)
    for n in sorted(set(allfix.trial) & set(S32)):
        Rn = pd.concat([base[base.trial != n], allfix[allfix.trial == n]], ignore_index=True)
        out.append(dict(analysis=f"only {K.FLAGGED[n]} fixed", set="S32", **pooled_contrast(Rn, S32)))
    # proposed downgrades (design-level / >20% affected) removed from the primary set, fixes applied to the rest
    for lab, drop in (("S32 minus design-level MAJOR (CABANA, TRANSFORM-HF, AMPLIFY)", ["cabana-v2", "transform-hf", "amplify"]),
                      ("S32 minus all proposed MAJOR (CABANA, TRANSFORM-HF, AMPLIFY, LAAOS III, COMET, VALIANT, LIFE)",
                       ["cabana-v2", "transform-hf", "amplify", "laaos3", "comet", "valiant", "life"])):
        tr = [t for t in S32 if t not in drop]
        out.append(dict(analysis=lab + ", published cells", set=f"S{len(tr)}", **pooled_contrast(base, tr)))
        out.append(dict(analysis=lab + ", remaining fixes applied", set=f"S{len(tr)}", **pooled_contrast(R1, tr)))
    PO = pd.DataFrame(out)
    PO.to_csv(K.OUT / "pooled.csv", index=False)
    print(PO.round(4).to_string(index=False))


if __name__ == "__main__":
    if sys.argv[1:] == ["summarize"]:
        summarize()
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 15)
