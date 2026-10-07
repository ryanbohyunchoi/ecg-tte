#!/usr/bin/env python
"""v2.1 (paper2, HANDOFF_PAPER2.md section 3.6): PS-CVD5 analog in the MIMIC-IV replication, +/- ECG.

PS-CVD5 (MIMIC) = demographics (v1.5 `demo`: age, sex, estimated index year) + diagnosis flags for hypertension,
type 2 diabetes, CAD/IHD, atrial fibrillation and heart failure, with the v1.5 concept prefixes
(v15_mimic_common.CONCEPTS); T2D is new: ICD-10 E11, ICD-9 250.x0 / 250.x2. Staged diagnoses_icd, read in place.
Primary window (`cvd5`): EARLIER admissions only (admittime < index admittime, index admission excluded), the
v1.5 audit-fixed convention (v15_mimic_auditfix.py); it reproduces the built trials' baseline dx exactly.
Sensitivity bases: `cvd5_anydm` (any diabetes, v1.5 `diabetes`, E08-E13 / 250, instead of T2D) and `cvd5_incl`
(index admission included, admittime <= index admittime; the window of the v20 new-trial builder).
Flags that are constant within the analysed rows (the gate condition, e.g. AF in the AF trials) are dropped.

Imports scripts/v20/mimic_replication.py (held-out panel, design for the v20 bases, sign-flip) and
mimic_summary.py (balance / agreement summaries); neither is modified. The v20 output dir is read only.

Subcommands
  flags      build the CVD5 flags per trial (restricted parquet, <OUT>/flags/<k>.parquet) and check the rebuilt
             v1.5 concepts against baseline.parquet (aggregate discordance counts, 1-10 suppressed)
  analyze    per trial: bases demo / sparse (gate) and cvd5 / cvd5_anydm x arms base / ECG / permECG x
             populations all / no_index_day_ecg; same panel, matching, Cox and metrics as v20
  gate       demo and sparse rows must equal v20 results/<k>_arms.csv and _vars.csv exactly (max abs diff 0)
  summarize  v20 summary metrics (mimic_summary.balance / agreement) for cvd5 bases + cross-base contrasts
Outputs: /mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/mimic/ (umask 077). Aggregates only are printed.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import json  # noqa: E402
import sys  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v20"))
import mimic_replication as M  # noqa: E402  (also puts scripts/ and scripts/v15 on sys.path)
import mimic_summary as MS  # noqa: E402
from eval_longtail_balance import smd_vector  # noqa: E402
from v13_common import cox, match, ps_logit  # noqa: E402
from v15_mimic_common import CONCEPTS  # noqa: E402

os.umask(0o077)
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/mimic")
TRIALS = M.BUILT + M.NEW
T2D9 = [f"250{x}{y}" for x in range(10) for y in (0, 2)]
FLAGDEF = {"hypertension": CONCEPTS["hypertension"], "t2d": (["E11"], T2D9), "diabetes": CONCEPTS["diabetes"],
           "ischemic_heart_disease_or_mi": CONCEPTS["ischemic_heart_disease_or_mi"],
           "atrial_fibrillation": CONCEPTS["atrial_fibrillation"], "heart_failure": CONCEPTS["heart_failure"]}
_C5 = ["hypertension", "t2d", "ischemic_heart_disease_or_mi", "atrial_fibrillation", "heart_failure"]
CVD5 = {"cvd5": _C5, "cvd5_anydm": [c if c != "t2d" else "diabetes" for c in _C5], "cvd5_incl": [c + "__incl" for c in _C5]}
BASES = ["demo", "sparse"] + list(CVD5)
ARMS = ("base", "ECG", "permECG")


def sup(n):
    n = int(n)
    return f"<{M.VA.SUPPRESS}" if 0 < n < M.VA.SUPPRESS else n


# ------------------------------------------------------------------ flags
def flags(k):
    import duckdb
    it = pd.read_parquet(M.tdir(k) / "index_time.parquet")[["pid", "subject_id", "hadm_id"]]
    it = it.assign(pid=it.pid.astype(str), subject_id=it.subject_id.astype(str), hadm_id=it.hadm_id.astype(str))
    con = duckdb.connect()
    con.execute("SET threads=8")
    con.register("c", it)
    rows = [(n, 10, p) for n, (c10, c9) in FLAGDEF.items() for p in c10] + \
           [(n, 9, p) for n, (c10, c9) in FLAGDEF.items() for p in c9]
    con.register("concept", pd.DataFrame(rows, columns=["concept", "v", "prefix"]))
    q = f"""
        WITH ix AS (SELECT c.pid, c.subject_id, c.hadm_id, a.admittime FROM c JOIN read_parquet('{M.STAGE}/admissions.parquet') a
                    ON CAST(a.subject_id AS VARCHAR) = c.subject_id AND CAST(a.hadm_id AS VARCHAR) = c.hadm_id)
        SELECT DISTINCT ix.pid, k.concept FROM ix
        JOIN read_parquet('{M.STAGE}/admissions.parquet') ad ON CAST(ad.subject_id AS VARCHAR) = ix.subject_id
             AND {{win}}
        JOIN read_parquet('{M.STAGE}/diagnoses_icd.parquet') d ON CAST(d.subject_id AS VARCHAR) = ix.subject_id
             AND CAST(d.hadm_id AS VARCHAR) = CAST(ad.hadm_id AS VARCHAR)
        JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)"""
    # prior = earlier admissions only (v1.5 audit fix, docs/AUDIT_V15_2026_09_26.md M2); incl = index admission too
    dx = {"prior": con.execute(q.format(win="ad.admittime < ix.admittime AND CAST(ad.hadm_id AS VARCHAR) <> ix.hadm_id")).df(),
          "incl": con.execute(q.format(win="ad.admittime <= ix.admittime")).df()}
    n_ix = con.execute(f"""SELECT count(DISTINCT c.pid) FROM c JOIN read_parquet('{M.STAGE}/admissions.parquet') a
        ON CAST(a.subject_id AS VARCHAR) = c.subject_id AND CAST(a.hadm_id AS VARCHAR) = c.hadm_id""").fetchone()[0]
    F = pd.DataFrame(index=pd.Index(it.pid.drop_duplicates(), name="pid"))
    for w, sfx in (("prior", ""), ("incl", "__incl")):
        for n in FLAGDEF:
            F[n + sfx] = F.index.isin(dx[w].loc[dx[w].concept == n, "pid"]).astype(float)
    (OUT / "flags").mkdir(parents=True, exist_ok=True)
    F.reset_index().to_parquet(OUT / "flags" / f"{k}.parquet", index=False)
    # check vs v1.5 (audit-fixed) / v20 baseline columns (aggregates only)
    ba = pd.read_parquet(M.tdir(k) / "baseline.parquet").assign(pid=lambda x: x.pid.astype(str)).drop_duplicates("pid").set_index("pid")
    chk = dict(trial=k, n=len(F), index_admission_found=n_ix)
    for n in FLAGDEF:
        chk[f"prev_{n}"] = round(float(100 * F[n].mean()), 1)
        chk[f"prev_{n}__incl"] = round(float(100 * F[n + "__incl"].mean()), 1)
        for sfx in ("", "__incl"):
            if n in ba:
                b = ba[n].reindex(F.index)
                chk[f"discord_{n}{sfx}"] = sup(int((b.notna() & (b != F[n + sfx])).sum()))
            else:
                chk[f"discord_{n}{sfx}"] = "absent"
    chk["t2d_within_anydm"] = bool(((F.t2d == 1) <= (F.diabetes == 1)).all())
    print(json.dumps(chk), flush=True)
    return chk


# ------------------------------------------------------------------ analysis (mirrors mimic_replication.analyze_trial)
def design(D, rows_mask, base, arm, perm, C):
    if base in M.BASES:
        r, t, idx, cl = M.run_design(D, rows_mask, base, arm, perm)
        return r, t, idx, cl, np.nan
    r = np.where(rows_mask)[0]
    t = D.t[r]
    Cr = C[base][r]
    Cr = Cr[:, Cr.std(0) > 0]  # gate condition / constant flags carry no information
    parts = [D.Gm["demo"][r], Cr]
    if arm == "ECG":
        parts.append(D.ecg_pc[r])
    elif arm == "permECG":
        parts.append(D.ecg_pc[perm][r])
    X = np.hstack(parts)
    lg = ps_logit(X, t)
    idx, cl, _ = match(lg, t)
    return r, t, idx, cl, Cr.shape[1]


def analyze(k):
    D = M.VA.TrialData(M.tdir(k))
    F = pd.read_parquet(OUT / "flags" / f"{k}.parquet").set_index("pid").reindex(D.pids)
    assert F.notna().all().all(), "flags missing for analysed pids"
    C = {b: F[v].to_numpy(float) for b, v in CVD5.items()}
    return run_trial(k, D, BASES, OUT / "results", C)


def run_trial(k, D, bases, outdir, C=None):
    """mimic_replication.analyze_trial for a given TrialData, list of bases (v20 BASES or CVD5 keys) and output dir."""
    rct = json.load(open(D.dir / "rct.json"))
    rb = np.log(rct["our_orientation"])
    rs = (np.log(rct["our_hi"]) - np.log(rct["our_lo"])) / (2 * 1.96)
    perm = np.random.default_rng(M.SEED).permutation(len(D.t))
    lag = D.lag if D.lag is not None else np.full(len(D.t), np.nan)
    pops = {"all": np.ones(len(D.t), bool), "no_index_day_ecg": ~(lag < 1)}
    rows, vrows = [], []
    for base in bases:
        V, cols, blk, MI, mi_cols = M.panel_for(D, k, base if base in M.BASES else "demo")
        for pop, mask in pops.items():
            if min((D.t[mask] == 1).sum(), (D.t[mask] == 0).sum()) < 50:
                continue
            r = np.where(mask)[0]
            t = D.t[r]
            s_un = smd_vector(V[r], t, np.where(t == 1)[0], np.where(t == 0)[0])
            for arm in ARMS:
                r, t, idx, cl, ndx = design(D, mask, base, arm, perm, C)
                mt, mc = idx[t[idx] == 1], idx[t[idx] == 0]
                s = smd_vector(V[r], t, mt, mc)
                smi = smd_vector(MI[r], t, mt, mc) if MI is not None else np.array([])
                ok = np.isfinite(s)
                T, E = D.T[r], D.E[r].astype(int)
                b, se = cox(T[idx], E[idx], t[idx], cluster=cl)
                row = dict(trial=k, base=base, arm=arm, pop=pop, n_pairs=len(idx) // 2, n_vars=int(ok.sum()),
                           pct_bal=float(100 * np.mean(s[ok] < 0.1)), mean_smd=float(np.mean(s[ok])),
                           mean_smd_unmatched=float(np.nanmean(s_un)),
                           pct_bal_miss=float(100 * np.mean(smi[np.isfinite(smi)] < 0.1)) if len(smi) else np.nan,
                           loghr=b, se=se, rct_loghr=rb, rct_se=rs, rct_measure=rct.get("measure", "HR"),
                           events=int(E[idx].sum()) if E[idx].sum() >= 11 else -1)
                for bb in sorted(set(blk)):
                    j = [i for i, x in enumerate(blk) if x == bb and np.isfinite(s[i])]
                    row[f"mean_smd_{bb}"] = float(np.mean(s[j])) if j else np.nan
                    row[f"pct_bal_{bb}"] = float(100 * np.mean(s[j] < 0.1)) if j else np.nan
                row["n_dx_flags_in_ps"] = ndx
                rows.append(row)
                for c, bb, x, xu in zip(cols, blk, s, s_un):
                    vrows.append(dict(trial=k, base=base, arm=arm, pop=pop, var=c, block=bb, abs_smd=x, abs_smd_unmatched=xu))
    outdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(outdir / f"{k}_arms.csv", index=False)
    pd.DataFrame(vrows).to_csv(outdir / f"{k}_vars.csv", index=False)
    print(k, "done", flush=True)
    return k


# ------------------------------------------------------------------ gate
def gate():
    out = []
    for k in TRIALS:
        for kind, keys in (("arms", ["base", "arm", "pop"]), ("vars", ["base", "arm", "pop", "var"])):
            ref = pd.read_csv(M.OUT / "results" / f"{k}_{kind}.csv")
            new = pd.read_csv(OUT / "results" / f"{k}_{kind}.csv")
            new = new[new.base.isin(["demo", "sparse"])]
            ref = ref[ref.base.isin(["demo", "sparse"])]
            a, b = ref.set_index(keys).sort_index(), new.set_index(keys)[ref.columns.drop(keys)].sort_index()
            same_index = a.index.equals(b.index)
            num = a.select_dtypes("number").columns
            d = (a[num] - b.loc[a.index, num]).abs().max().max() if same_index else np.inf
            nan_ok = bool((a[num].isna() == b.loc[a.index, num].isna()).all().all()) if same_index else False
            obj = [c for c in a.columns if c not in num]
            obj_ok = bool((a[obj] == b.loc[a.index, obj]).all().all()) if same_index else False
            out.append(dict(trial=k, table=kind, rows=len(a), same_rows=same_index, max_abs_diff=float(d),
                            nan_pattern_equal=nan_ok, text_equal=obj_ok))
    g = pd.DataFrame(out)
    ok = bool(g.same_rows.all() and (g.max_abs_diff == 0).all() and g.nan_pattern_equal.all() and g.text_equal.all())
    # summary-level check on the published v20 demo / sparse numbers
    v20 = json.load(open(M.OUT / "summary/summary.json"))["balance"]
    A = load()
    sd = []
    for key, ref in v20.items():
        s, base, pop = key.split("|")
        if base not in ("demo", "sparse"):
            continue
        b = MS.balance(A, [t for t in MS.SETS[s]], base, pop)
        for m in ("pct_bal_base", "pct_bal_ECG", "relred_ECG", "relred_permECG"):
            sd.append(abs(b[m] - ref[m]))
        sd += [abs(x - y) for x, y in zip(b["relred_ECG_ci"], ref["relred_ECG_ci"])]
    ok = ok and max(sd) == 0
    (OUT / "gate").mkdir(parents=True, exist_ok=True)
    g.to_csv(OUT / "gate/gate.csv", index=False)
    print(g.to_string(index=False), f"\nsummary-level max abs diff {max(sd)}", "\nGATE", "PASS" if ok else "FAIL", flush=True)
    for f in ("PASS", "FAIL"):
        (OUT / "gate" / f).unlink(missing_ok=True)
    (OUT / "gate" / ("PASS" if ok else "FAIL")).write_text(json.dumps(dict(n=len(g), summary_max_diff=max(sd))))
    return ok


# ------------------------------------------------------------------ summary
def load():
    return pd.concat([pd.read_csv(OUT / "results" / f"{k}_arms.csv") for k in TRIALS], ignore_index=True)


def contrast(A, trials, a1, a0, pop):
    """(base, arm) a1 vs a0: mean % balanced, Delta pts, relative reduction in mean |SMD| (v20 bootstrap),
    sign-flip p; agreement: mean |d log HR|, trials closer, sign-flip p."""
    S = A[(A["pop"] == pop) & A.trial.isin(trials)].set_index(["trial", "base", "arm"])
    x1, x0 = S.xs(a1, level=("base", "arm"), drop_level=True), S.xs(a0, level=("base", "arm"), drop_level=True)
    tr = x1.index.intersection(x0.index)
    x1, x0 = x1.loc[tr], x0.loc[tr]
    d = (x1.pct_bal - x0.pct_bal).to_numpy()
    mb, ma = x0.mean_smd.to_numpy(), x1.mean_smd.to_numpy()
    e1, e0 = (x1.loghr - x1.rct_loghr).abs(), (x0.loghr - x0.rct_loghr).abs()
    dd = (e0 - e1).dropna().to_numpy()
    return dict(k=len(tr), pct0=float(x0.pct_bal.mean()), pct1=float(x1.pct_bal.mean()), dpts=float(d.mean()),
                better=f"{int((d > 0).sum())}/{len(d)}", p_pts=M.exact_signflip(d),
                smd0=float(mb.mean()), smd1=float(ma.mean()), relred=float(100 * (1 - ma.mean() / mb.mean())),
                relred_ci=MS.boot_rr(mb, ma), lower=f"{int((ma < mb).sum())}/{len(mb)}", p_smd=M.exact_signflip(mb - ma),
                absd0=float(e0.mean()), absd1=float(e1.mean()), closer=f"{int((dd > 0).sum())}/{len(dd)}",
                p_closer=M.exact_signflip(dd))


def summarize():
    A = load()
    (OUT / "summary").mkdir(parents=True, exist_ok=True)
    sets = {"primary7": MS.SETS["primary7"], "all8": MS.SETS["all8"]}
    summ = dict(balance={}, agreement={}, contrasts={}, per_trial={})
    for s, tr in sets.items():
        for base in BASES:
            for pop in ("all", "no_index_day_ecg"):
                key = f"{s}|{base}|{pop}"
                summ["balance"][key] = MS.balance(A, tr, base, pop)
                summ["agreement"][key] = MS.agreement(A, tr, base, pop)
                if base in CVD5:
                    for lab, a1, a0 in ((f"{base} base vs demo base", (base, "base"), ("demo", "base")),
                                        (f"{base}+ECG vs demo+ECG", (base, "ECG"), ("demo", "ECG")),
                                        (f"{base} base vs sparse base", (base, "base"), ("sparse", "base")),
                                        (f"{base}+ECG vs sparse base", (base, "ECG"), ("sparse", "base"))):
                        summ["contrasts"][f"{key}|{lab}"] = contrast(A, tr, a1, a0, pop)
    P = A[A["pop"] == "all"]
    for r in P.itertuples():
        summ["per_trial"].setdefault(r.trial, {})[f"{r.base}|{r.arm}"] = dict(
            pct_bal=round(r.pct_bal, 1), mean_smd=round(r.mean_smd, 4), hr=round(float(np.exp(r.loghr)), 3),
            lo=round(float(np.exp(r.loghr - 1.96 * r.se)), 3), hi=round(float(np.exp(r.loghr + 1.96 * r.se)), 3),
            n_pairs=int(r.n_pairs), n_vars=int(r.n_vars), n_dx=None if pd.isna(r.n_dx_flags_in_ps) else int(r.n_dx_flags_in_ps),
            rct=round(float(np.exp(r.rct_loghr)), 3))
    json.dump(summ, open(OUT / "summary/summary.json", "w"), indent=1, default=float)
    L = ["# MIMIC-IV PS-CVD5 analog: generated tables (aggregates only)", "",
         "## Balance within base PS (26-item held-out panel; mean over trials)", "",
         "| Set | Base PS | Population | k | % bal base | % bal +ECG | Δ pts | better | p | rel. red. mean |SMD| +ECG [95% CI] | lower | p | % bal +perm | Δ perm | rel. red. perm |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, b in summ["balance"].items():
        s, base, pop = key.split("|")
        ci = b["relred_ECG_ci"]
        L.append(f"| {s} | {base} | {pop} | {b['k']} | {b['pct_bal_base']:.1f} | {b['pct_bal_ECG']:.1f} | {b['dpts_ECG']:+.1f} | "
                 f"{b['better_ECG']} | {b['p_ECG']:.3f} | {b['relred_ECG']:.1f} [{ci[0]:.1f}, {ci[1]:.1f}] | {b['lower_smd_ECG']} | "
                 f"{b['p_smd_ECG']:.3f} | {b['pct_bal_permECG']:.1f} | {b['dpts_permECG']:+.1f} | {b['relred_permECG']:.1f} |")
    L += ["", "## By block: relative reduction in mean |SMD| with ECG (A core labs/vitals, B additional labs, D utilisation)", "",
          "| Set | Base PS | Population | A | B | D |", "|---|---|---|---|---|---|"]
    for key, b in summ["balance"].items():
        s, base, pop = key.split("|")
        L.append(f"| {s} | {base} | {pop} | " + " | ".join(f"{b.get(f'relred_ECG_block{x}', np.nan):.1f}" for x in "ABD") + " |")
    L += ["", "## RCT agreement (trial primary outcome)", "",
          "| Set | Base PS | Population | Arm | k | r | estimate agreement | std-diff agreement | mean |Δ log HR| | ECG closer | p |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, ag in summ["agreement"].items():
        s, base, pop = key.split("|")
        for arm in ARMS:
            g = ag[arm]
            extra = f"{ag['ECG_vs_base']['closer']} | {ag['ECG_vs_base']['p']:.3f}" if arm == "ECG" else " | "
            L.append(f"| {s} | {base} | {pop} | {arm} | {g['k']} | {g['r']:.2f} | {g['est_agree']} | {g['std_agree']} | {g['mean_abs_diff']:.3f} | {extra} |")
    L += ["", "## Cross-base contrasts", "",
          "| Set | Population | Contrast | k | % bal 0 → 1 | Δ pts (better; p) | rel. red. mean |SMD| [95% CI] (lower; p) | mean |Δ log HR| 0 → 1 | closer (p) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for key, c in summ["contrasts"].items():
        s, base, pop, lab = key.split("|")
        ci = c["relred_ci"]
        L.append(f"| {s} | {pop} | {lab} | {c['k']} | {c['pct0']:.1f} → {c['pct1']:.1f} | {c['dpts']:+.1f} ({c['better']}; {c['p_pts']:.3f}) | "
                 f"{c['relred']:.1f} [{ci[0]:.1f}, {ci[1]:.1f}] ({c['lower']}; {c['p_smd']:.3f}) | {c['absd0']:.3f} → {c['absd1']:.3f} | "
                 f"{c['closer']} ({c['p_closer']:.3f}) |")
    L += ["", "## Per trial (full ECG cohort)", "",
          "| Trial | Base PS | Arm | dx flags in PS | pairs | vars | % bal | mean |SMD| | HR (95% CI) | RCT |", "|---|---|---|---|---|---|---|---|---|---|"]
    for t in TRIALS:
        for kk, v in summ["per_trial"][t].items():
            base, arm = kk.split("|")
            L.append(f"| {MS.NAMES.get(t, t)} | {base} | {arm} | {'' if v['n_dx'] is None else v['n_dx']} | {v['n_pairs']} | {v['n_vars']} | "
                     f"{v['pct_bal']} | {v['mean_smd']} | {v['hr']} ({v['lo']}–{v['hi']}) | {v['rct']} |")
    (OUT / "summary/tables.md").write_text("\n".join(L) + "\n")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    if cmd == "flags":
        ch = [flags(k) for k in TRIALS]
        (OUT / "flags").mkdir(exist_ok=True)
        pd.DataFrame(ch).to_csv(OUT / "flags/flag_check.csv", index=False)
    elif cmd == "analyze":
        with Pool(8) as p:
            p.map(analyze, TRIALS)
    elif cmd == "gate":
        sys.exit(0 if gate() else 1)
    elif cmd == "summarize":
        assert (OUT / "gate" / "PASS").exists(), "gate has not passed"
        summarize()
