#!/usr/bin/env python
"""v1.9 sensitivity: outpatient initiators (docs/v19/SENS_OUTPATIENT_PLAN.md, committed ac0a347 before any result).

Code path = the 38-trial analysis: scripts/v18/v18_af_confirm.py (trial list, V18 covariate paths, P5 list of s11_p5)
-> scripts/v17/v17_confirm.task (unchanged) -> scripts/v16/v16_engine.run_cell(rows=).  The only change is the row set:
v17_confirm.halves(T, i)[h] is intersected with a population mask (all / outpt / inpt), so PS, matching, SMD pooled SDs,
the covars2b column filter and Cox are re-fitted within the restricted rows.  E.run_cell is wrapped only to add the
number of primary-outcome events in the analysed (matched) sample (n_events); nothing else is touched.

Index setting (S4 rule, s4_subgroups.prep / make_outpatient_cohort.py): inpatient = index date within an OMOP gold
visit 9201 [start, coalesce(end, start)]; ED (descriptive) = not inpatient and index date within a 9203 visit;
outpatient = not inpatient.

Usage:
  sens_outpatient.py prep                       -> OUT/restricted_setting_<trial>.parquet (patient_key, flags)
  sens_outpatient.py run --pop all|outpt|inpt [--trials a,b] [--workers 20]
                                                -> OUT/restricted_results_<pop>.parquet (unsuppressed aggregates),
                                                   OUT/results_<pop>.csv (counts 1-10 suppressed), OUT/log_<pop>.json
  sens_outpatient.py verify [--trials carolina,laaos3]   pop=all vs claude-v17-confirm / claude-v18-af-confirm (max dev 0)
  sens_outpatient.py summarize                  -> OUT/{setting,power,per_trial,summary,domains,restriction}.csv,
                                                   OUT/tables.md (-> docs/v19/SENS_OUTPATIENT.md)
Aggregates only; OUT umask 077; counts 1-10 suppressed in every written csv / md.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v18"))
sys.path.insert(0, str(HERE.parent / "v17"))
sys.path.insert(0, str(HERE.parent / "v16"))
sys.path.insert(0, str(HERE.parent))
import v18_af_confirm as F  # noqa: E402  (sets V.ALL = 38, V.P2DX = P5 list, V18 cdirs)

import argparse  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

V = F.V
E = V.E
S8 = V.S8
from v13_common import EXTRA, PRIMARY  # noqa: E402

A = V.A
OUT = A / "claude-v19-sens-outpatient"
DOCS = HERE.parent.parent / "docs" / "v19"
ALL = list(F.ALL)
KEY = F.KEY
ROLES = V.ROLES
PSS = ("P1", "P5")
NPERM = 20000
MIN_ARM, MIN_ARM_HALF = 100, 50
CNT = ["n", "n_t", "n_c", "n_pairs", "n_events"]

# ---- a priori classification (plan section 2)
HOSP = ["transform-hf", "plato", "valiant", "amplify", "prove-it", "laaos3"]
PROC = ["cabana-v2", "protect-af", "raft-af"]
OUT29 = [t for t in ALL if t not in HOSP + PROC]
OUT32 = [t for t in ALL if t not in HOSP]
assert len(OUT29) == 29 and len(OUT32) == 32 and len(ALL) == 38


# ---------------------------------------------------------------- prep: setting flags
def prep(trials):
    import duckdb
    from trial_common import rp
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET threads=16")
    vo = rp("/mnt/raid0/rbc58/omop/gold", "visit_occurrence")
    for n in trials:
        cdir = {**PRIMARY, **EXTRA}[n][1]
        coh = pd.read_parquet(f"{A}/{cdir}/restricted_cohort.parquet")[["patient_key", "person_id", "index_date"]]
        con.register("c", coh)
        q = """SELECT DISTINCT c.patient_key FROM c JOIN {vo} v ON v.person_id = c.person_id AND v.visit_concept_id = {vc}
               AND CAST(c.index_date AS DATE) BETWEEN v.visit_start_date AND coalesce(v.visit_end_date, v.visit_start_date)"""
        ip = set(con.execute(q.format(vo=vo, vc=9201)).df().patient_key)
        ed = set(con.execute(q.format(vo=vo, vc=9203)).df().patient_key)
        con.unregister("c")
        f = coh[["patient_key"]].drop_duplicates().copy()
        f["inpatient_index"] = f.patient_key.isin(ip)
        f["ed_index"] = f.patient_key.isin(ed) & ~f.inpatient_index
        f.to_parquet(OUT / f"restricted_setting_{n}.parquet", index=False)
        os.chmod(OUT / f"restricted_setting_{n}.parquet", 0o600)
        print(f"prep {n} done", flush=True)


def flags(T):
    f = pd.read_parquet(OUT / f"restricted_setting_{T.n}.parquet").set_index("patient_key").reindex(T.keys)
    assert f.inpatient_index.notna().all(), f"{T.n}: analysis keys missing from the cohort flags"
    return f.inpatient_index.to_numpy(bool), f.ed_index.to_numpy(bool)


# ---------------------------------------------------------------- restriction hooks (the only changes)
POP = {"pop": "all"}
_halves0 = V.halves
_run_cell0 = E.run_cell


def mask(T):
    inp, _ = flags(T)
    return {"all": np.ones(len(T.t), bool), "outpt": ~inp, "inpt": inp}[POP["pop"]]


def halves_pop(T, i):
    H = _halves0(T, i)
    if POP["pop"] == "all":
        return H
    m = mask(T)
    return {h: r[m[r]] for h, r in H.items()}


def run_cell_ev(T, X, t=None, rows=None, **kw):
    o = _run_cell0(T, X, t=t, rows=rows, **kw)
    rr = np.arange(len(T.t)) if rows is None else np.asarray(rows)
    s_idx = np.arange(len(rr)) if X is None else S8._LAST["m"][0]
    ye, ok = T.y_e[rr][s_idx], T.y_ok[rr][s_idx]
    o["n_events"] = int(np.asarray(ye)[np.asarray(ok, bool)].sum())
    return o


V.halves = halves_pop
E.run_cell = run_cell_ev


def load(n):
    return E.load_trial(n) if n in V.OLD else E.load_trial(n, cache=False)


def task(args):
    n, half, pop = args
    POP["pop"] = pop
    t0 = time.time()
    T = load(n)
    r = halves_pop(T, ALL.index(n))[half]
    tt = T.t[r]
    thr = MIN_ARM if half == "full" else MIN_ARM_HALF
    rf = halves_pop(T, ALL.index(n))["full"]
    full_ok = min(T.t[rf].sum(), (1 - T.t[rf]).sum()) >= MIN_ARM
    meta = dict(trial=n, half=half, pop=pop)
    if half == "full" and pop == "all":
        inp, ed = flags(T)
        ev = np.asarray(T.y_e)[np.asarray(T.y_ok, bool)]
        meta.update(n_all=len(T.t), n_t=int(T.t.sum()), n_c=int((1 - T.t).sum()),
                    **{f"inp_{a}": int(inp[T.t == v].sum()) for a, v in (("t", 1), ("c", 0))},
                    **{f"ed_{a}": int(ed[T.t == v].sum()) for a, v in (("t", 1), ("c", 0))},
                    events_all=int(ev.sum()),
                    events_outpt=int(np.asarray(T.y_e)[np.asarray(T.y_ok, bool) & ~inp].sum()),
                    n_outpt_t=int((~inp & (T.t == 1)).sum()), n_outpt_c=int((~inp & (T.t == 0)).sum()))
    if not full_ok or min(tt.sum(), (1 - tt).sum()) < thr:
        meta.update(skipped=True, reason=f"arm < {MIN_ARM} (full)" if not full_ok else f"half arm < {thr}")
        print(f"{n} {half} {pop} skipped", flush=True)
        return [], meta
    out, log = V.task((n, half))
    for o in out:
        o["pop"] = pop
    meta.update(skipped=False, secs=round(time.time() - t0, 1), **{k: v for k, v in log.items() if k in ("seed", "hf_column")})
    print(f"{n} {half} {pop} {time.time() - t0:.0f}s", flush=True)
    return out, meta


def suppress_df(D):
    D = D.copy()
    for c in [c for c in D.columns if c in CNT or c.startswith(("n_", "inp_", "ed_", "events_"))]:
        if pd.api.types.is_numeric_dtype(D[c]):
            D[c] = D[c].astype(float).where(~D[c].between(1, 10, inclusive="both"), np.nan)
    return D


def run(trials, workers, pop):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    tk = sorted([(n, h, pop) for n in trials for h in ("full", "A", "B")], key=lambda x: (x[1] != "full", x[0] not in ("ascot", "value", "allhat")))
    with Pool(min(workers, len(tk), 24)) as p:
        res = p.map(task, tk, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    R["ps"] = R.ps.replace({"P2": "P5"})
    R["set"] = np.where(R.trial.isin(F.AF5), "v18af5", R["set"])
    Mt = pd.DataFrame([m for _, m in res])
    for nm, D in ((f"restricted_results_{pop}.parquet", R), (f"restricted_meta_{pop}.parquet", Mt)):
        D.to_parquet(OUT / nm, index=False)
        os.chmod(OUT / nm, 0o600)
    suppress_df(R).to_csv(OUT / f"results_{pop}.csv", index=False)
    (OUT / f"log_{pop}.json").write_text(suppress_df(Mt).to_json(orient="records", indent=1))
    print("done", pop, flush=True)


# ---------------------------------------------------------------- verification (pop = all vs reference files)
def verify(trials):
    R = pd.read_parquet(OUT / "restricted_results_all.parquet")
    R = R[R.trial.isin(trials)]
    Q = pd.concat([F.ref33(), pd.read_csv(F.OUT / "results_af5.csv")], ignore_index=True)
    cols = [c for c in R.columns if c in Q.columns and c not in ("trial", "key", "set", "idx", "half", "ps", "arm_role", "secs")
            and pd.api.types.is_numeric_dtype(R[c])]
    rows = []
    for (n, h, ps, role), g in R.groupby(["trial", "half", "ps", "arm_role"]):
        q = Q[(Q.trial == n) & (Q.half == h) & (Q.ps == ps) & (Q.arm_role == role)]
        assert len(g) == 1 and len(q) == 1, (n, h, ps, role, len(g), len(q))
        a, b = g.iloc[0], q.iloc[0]
        d = 0.0
        for c in cols:
            if pd.isna(a[c]) and pd.isna(b[c]):
                continue
            d = max(d, np.inf if (pd.isna(a[c]) or pd.isna(b[c])) else abs(float(a[c]) - float(b[c])))
        rows.append(dict(trial=n, half=h, ps=ps, arm=role, ncols=len(cols), maxdev=d))
    Vd = pd.DataFrame(rows)
    Vd.to_csv(OUT / "verify.csv", index=False)
    print(Vd.groupby(["trial", "ps"]).maxdev.max().to_string())
    print("trials", Vd.trial.nunique(), "cells", len(Vd), "columns", len(cols), "overall max deviation", Vd.maxdev.max())
    return Vd.maxdev.max()


# ---------------------------------------------------------------- statistics
sf = V.signflip_1s
GROUPS = list(E.GROUPS)


def sf2(d):
    d = pd.Series(d).dropna()
    if len(d) == 0:
        return np.nan
    return min(1.0, 2 * min(sf(d.to_numpy()), sf(-d.to_numpy())))


def metrics(g):
    M = V.trial_metrics(g)
    for G in GROUPS:
        cs = [f"smd:{c}" for c, _, gg in E.VARS if gg == G]
        sm = g[cs].abs()
        M[f"lt01_g:{G}"] = (100 * (sm < 0.1).sum(1) / sm.notna().sum(1)).to_numpy()
        M[f"msmd_g:{G}"] = sm.mean(1).to_numpy()
    M["n_pairs"] = g.n_pairs.to_numpy()
    return M


def build_M(R):
    R = R[R.arm_role != "unmatched"]
    assert R.groupby(["trial", "half", "ps", "arm_role"]).size().max() == 1
    return {h: {ps: {r: metrics(R[(R.half == h) & (R.ps == ps) & (R.arm_role == r)]) for r in ROLES} for ps in PSS}
            for h in ("full", "A", "B")}


def analyse(M, trials, seed=0, nperm=NPERM):
    CL = V.cluster_of()
    out = []
    for ps in PSS:
        F_ = {r: M["full"][ps][r].loc[trials] for r in ROLES}
        for m in V.METRICS:
            sgn = 1 if m in V.HIGHER else -1
            b, e, s, z = (F_[r][m] for r in ROLES)
            d = sgn * (e - b)
            row = dict(ps=ps, metric=m, n=len(trials), base=b.mean(), ecg=e.mean(), shuf=s.mean(), noise=z.mean(),
                       d_ecg_minus_base=(e - b).mean(), k_better=f"{int((d > 0).sum())}/{int(d.notna().sum())}",
                       p=sf(d), p_vs_shuf=sf(sgn * (e - s)), p_vs_noise=sf(sgn * (e - z)))
            lab = [CL[KEY[t]] for t in trials]
            cl = pd.Series(d.to_numpy(), index=lab).groupby(level=0).mean()
            row.update(n_clusters=len(cl), cluster_p=sf(cl.to_numpy()),
                       cluster_p_vs_shuf=sf(pd.Series((sgn * (e - s)).to_numpy(), index=lab).groupby(level=0).mean().to_numpy()))
            row["loo_max_p"] = max(sf(d.drop(t)) for t in trials) if len(trials) > 1 else np.nan
            for h in ("A", "B"):
                ta = [t for t in trials if t in M[h][ps]["base"].index and t in M[h][ps]["ECG"].index]
                row[f"p_{h}"] = sf(sgn * (M[h][ps]["ECG"].loc[ta][m] - M[h][ps]["base"].loc[ta][m]))
            if m in ("absd", "z2"):
                rb, rs = F_["base"].rb.to_numpy(), F_["base"].rs.to_numpy()
                lb, sb, le, se_ = F_["base"].loghr.to_numpy(), F_["base"].se.to_numpy(), F_["ECG"].loghr.to_numpy(), F_["ECG"].se.to_numpy()

                def st(ix):
                    q, v = rb[ix], rs[ix]
                    if m == "absd":
                        return np.nanmean(np.abs(le - q) - np.abs(lb - q))
                    return np.nanmean((le - q) ** 2 / (se_ ** 2 + v ** 2) - (lb - q) ** 2 / (sb ** 2 + v ** 2))
                obs = st(np.arange(len(trials)))
                rng = np.random.default_rng(seed)
                null = np.array([st(rng.permutation(len(trials))) for _ in range(nperm)])
                row.update(bshuf_obs=obs, bshuf_p=float((null <= obs + 1e-12).mean()))
            out.append(row)
    return out


def sets_def(ok_out, ok_inp):
    """-> {set name: (trials, {trial: pop})}; ok_* = trials analysable in that population."""
    S = {}
    for nm, trs in (("OUT-29", OUT29), ("OUT-32", OUT32)):
        tr = [t for t in trs if t in ok_out]
        S[f"{nm} outpt"] = (tr, {t: "outpt" for t in tr})
        S[f"{nm} all (same trials)"] = (tr, {t: "all" for t in tr})
        S[f"{nm} all (full set)"] = (trs, {t: "all" for t in trs})
    S["HOSP-6 all"] = (HOSP, {t: "all" for t in HOSP})
    hi = [t for t in HOSP if t in ok_inp]
    S["HOSP inpt"] = (hi, {t: "inpt" for t in hi})
    S["HOSP inpt: all (same trials)"] = (hi, {t: "all" for t in hi})
    ho = [t for t in HOSP if t in ok_out]
    S["HOSP outpt (suppl.)"] = (ho, {t: "outpt" for t in ho})
    S["HOSP outpt: all (same trials)"] = (ho, {t: "all" for t in ho})
    mx = [t for t in ALL if (t in HOSP) or (t in ok_out)]
    S["Mixed-38 setting-matched"] = (mx, {t: ("all" if t in HOSP else "outpt") for t in mx})
    S["Mixed-38: all (same trials)"] = (mx, {t: "all" for t in mx})
    return S


def fmt_p(p):
    return "–" if pd.isna(p) else (f"{p:.3f}" if p >= 0.001 else f"{p:.1e}")


def summarize():
    os.umask(0o077)
    RR = {p: pd.read_parquet(OUT / f"restricted_results_{p}.parquet") for p in ("all", "outpt", "inpt")}
    MT = pd.concat([pd.read_parquet(OUT / f"restricted_meta_{p}.parquet") for p in ("all", "outpt", "inpt")], ignore_index=True)
    ok = {p: set(MT[(MT["pop"] == p) & (MT.half == "full") & (~MT.skipped.astype(bool))].trial) for p in ("outpt", "inpt")}
    # half cells missing for analysable trials are dropped per half in analyse()
    R = pd.concat([RR[p].assign(pop=p) for p in RR], ignore_index=True)
    CL = V.cluster_of()
    J = json.loads((V.DOCS / "trial_selection.json").read_text())

    # ---- setting table (plan section 1)
    m0 = MT[(MT["pop"] == "all") & (MT.half == "full")].set_index("trial").loc[ALL]
    st = []
    for n in ALL:
        x = m0.loc[n]

        def pct(k, d):
            return np.nan if 1 <= k <= 10 or 1 <= d - k <= 10 else 100 * k / d
        st.append(dict(trial=n, rct_setting="hospital" if n in HOSP else ("outpatient (procedure arm)" if n in PROC else "outpatient"),
                       pct_inpatient=pct(x.inp_t + x.inp_c, x.n_all), pct_inpatient_arm1=pct(x.inp_t, x.n_t),
                       pct_inpatient_arm0=pct(x.inp_c, x.n_c), pct_ed_not_inpatient=pct(x.ed_t + x.ed_c, x.n_all),
                       pct_ed_arm1=pct(x.ed_t, x.n_t), pct_ed_arm0=pct(x.ed_c, x.n_c)))
    ST = pd.DataFrame(st)
    ST.to_csv(OUT / "setting.csv", index=False)

    # ---- power table (plan section 4)
    def cell(pop, n, ps, role, col):
        g = RR[pop]
        g = g[(g.trial == n) & (g.half == "full") & (g.ps == ps) & (g.arm_role == role)]
        return float(g[col].iloc[0]) if len(g) else np.nan
    def sp(k, d):  # % retained; suppressed if the retained or the dropped count is 1-10
        return np.nan if 1 <= k <= 10 or 1 <= d - k <= 10 else 100 * k / d
    pw = []
    for n in ALL:
        x = m0.loc[n]
        sm_all, sm_out = min(x.n_t, x.n_c), min(x.n_outpt_t, x.n_outpt_c)
        rec = dict(trial=n, rct_setting=ST.set_index("trial").rct_setting[n],
                   pct_retained=sp(x.n_outpt_t + x.n_outpt_c, x.n_all),
                   pct_retained_arm1=sp(x.n_outpt_t, x.n_t), pct_retained_arm0=sp(x.n_outpt_c, x.n_c),
                   pct_smaller_arm_retained=sp(sm_out, sm_all),
                   pct_events_retained_cohort=np.nan if 1 <= x.events_outpt <= 10 else 100 * x.events_outpt / x.events_all,
                   feasible_all=bool(sm_all >= 300 and x.events_all >= 50), feasible_outpt=bool(sm_out >= 300 and x.events_outpt >= 50),
                   analysable_outpt=n in ok["outpt"])
        for ps in PSS:
            for role in ("base", "ECG"):
                a, o = cell("all", n, ps, role, "n_pairs"), cell("outpt", n, ps, role, "n_pairs")
                rec[f"pct_pairs_{ps}_{role}"] = np.nan if (pd.isna(o) or 1 <= o <= 10) else 100 * o / a
        ea, eo = cell("all", n, "P1", "base", "n_events"), cell("outpt", n, "P1", "base", "n_events")
        rec["pct_events_retained_P1_matched"] = np.nan if (pd.isna(eo) or 1 <= eo <= 10) else 100 * eo / ea
        for ps, role in (("P1", "base"), ("P1", "ECG"), ("P5", "base"), ("P5", "ECG")):
            rec[f"se_ratio_{ps}_{role}"] = cell("outpt", n, ps, role, "se") / cell("all", n, ps, role, "se")
        pw.append(rec)
    PW = pd.DataFrame(pw)
    PW.to_csv(OUT / "power.csv", index=False)

    # ---- inference per set
    Mc = {}

    def M_for(popmap):
        k = tuple(sorted(popmap.items()))
        if k not in Mc:
            parts = [R[(R.trial == t) & (R["pop"] == p)] for t, p in popmap.items()]
            Mc[k] = build_M(pd.concat(parts, ignore_index=True))
        return Mc[k]
    SETS = sets_def(ok["outpt"], ok["inpt"])
    rows, dom = [], []
    for nm, (trs, pm) in SETS.items():
        if len(trs) < 2:
            continue
        M = M_for(pm)
        for r in analyse(M, trs):
            rows.append(dict(set=nm, **r))
        for ps in PSS:
            for role in ROLES:
                Fm = M["full"][ps][role].loc[trs]
                dom.append(dict(set=nm, ps=ps, arm=role, n=len(trs), **{f"lt01:{G}": Fm[f"lt01_g:{G}"].mean() for G in GROUPS},
                                **{f"msmd:{G}": Fm[f"msmd_g:{G}"].mean() for G in GROUPS}))
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "summary.csv", index=False)
    D = pd.DataFrame(dom)
    # domain-level ECG vs base sign-flip p
    for nm, (trs, pm) in SETS.items():
        if len(trs) < 2:
            continue
        M = M_for(pm)
        for ps in PSS:
            for G in GROUPS:
                dd = M["full"][ps]["ECG"].loc[trs][f"lt01_g:{G}"] - M["full"][ps]["base"].loc[trs][f"lt01_g:{G}"]
                D.loc[(D.set == nm) & (D.ps == ps) & (D.arm == "ECG"), f"p_lt01:{G}"] = sf(dd)
    D.to_csv(OUT / "domains.csv", index=False)

    # ---- direct restriction effect (outpt minus all, same trials)
    rs = []
    for nm, trs in (("OUT-29", [t for t in OUT29 if t in ok["outpt"]]), ("OUT-32", [t for t in OUT32 if t in ok["outpt"]])):
        Mo, Ma = M_for({t: "outpt" for t in trs}), M_for({t: "all" for t in trs})
        for ps in PSS:
            for role in ROLES:
                for m in ("lt01", "x_lt01", "mean_smd", "absd", "cons"):
                    d = Mo["full"][ps][role].loc[trs][m] - Ma["full"][ps][role].loc[trs][m]
                    better = d > 0 if m in V.HIGHER else d < 0
                    rs.append(dict(set=nm, ps=ps, arm=role, metric=m, n=len(trs), all=Ma["full"][ps][role].loc[trs][m].mean(),
                                   outpt=Mo["full"][ps][role].loc[trs][m].mean(), d_outpt_minus_all=d.mean(),
                                   k_outpt_better=f"{int(better.sum())}/{int(d.notna().sum())}", p_two_sided=sf2(d)))
    RS = pd.DataFrame(rs)
    RS.to_csv(OUT / "restriction.csv", index=False)

    # ---- per-trial HR table
    pt = []
    for n in ALL:
        rec = dict(trial=n, cluster=CL[KEY[n]], fidelity=bool(J["trials"][KEY[n]]["fidelity_include"]),
                   rct_hr=float(np.exp(cell("all", n, "P1", "base", "rb"))))
        for pop in ("all", "outpt"):
            for ps in PSS:
                for role, lab in (("base", "base"), ("ECG", "ecg"), ("shufECG", "shuf")):
                    lh = cell(pop, n, ps, role, "loghr")
                    rec[f"{pop}_{ps}_hr_{lab}"] = np.exp(lh)
                    rec[f"{pop}_{ps}_absd_{lab}"] = abs(lh - cell(pop, n, ps, role, "rb"))
            rec[f"{pop}_hr_unmatched"] = np.exp(cell(pop, n, "none", "unmatched", "loghr"))
        pt.append(rec)
    PT = pd.DataFrame(pt)
    PT.to_csv(OUT / "per_trial.csv", index=False)
    for f in OUT.glob("*.csv"):
        os.chmod(f, 0o600)
    write_tables(ST, PW, S, D, RS, PT, ok)


def write_tables(ST, PW, S, D, RS, PT, ok):
    L = ["# v1.9 outpatient-initiator sensitivity: tables (generated by scripts/v19/sens_outpatient.py summarize)", "",
         "Aggregates only; percentages and ratios; values derived from counts 1–10 are suppressed (–).", ""]
    L += ["## T1. Index setting (% of analysed initiators; inpatient = index date within a 9201 stay; ED = within a 9203 visit, not inpatient)", "",
          "| Trial | RCT setting | % inpatient | arm 1 | arm 0 | % ED | ED arm 1 | ED arm 0 |", "|---|---|---|---|---|---|---|---|"]

    def f1(v):
        return "–" if pd.isna(v) else f"{v:.1f}"
    for _, r in ST.iterrows():
        L.append(f"| {r.trial} | {r.rct_setting} | {f1(r.pct_inpatient)} | {f1(r.pct_inpatient_arm1)} | {f1(r.pct_inpatient_arm0)} | "
                 f"{f1(r.pct_ed_not_inpatient)} | {f1(r.pct_ed_arm1)} | {f1(r.pct_ed_arm0)} |")
    L += ["", "## T2. Cohort and power after outpatient restriction (outpatient / all initiators)", "",
          "| Trial | RCT setting | % retained | % smaller arm | % pairs P1 base | % pairs P1 ECG | % pairs P5 base | % events (cohort) | % events (P1 matched) | SE ratio P1 base | SE ratio P1 ECG | SE ratio P5 base | feasible all | feasible outpt |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in PW.iterrows():
        L.append(f"| {r.trial} | {r.rct_setting} | {f1(r.pct_retained)} | {f1(r.pct_smaller_arm_retained)} | {f1(r.pct_pairs_P1_base)} | "
                 f"{f1(r.pct_pairs_P1_ECG)} | {f1(r.pct_pairs_P5_base)} | {f1(r.pct_events_retained_cohort)} | {f1(r.pct_events_retained_P1_matched)} | "
                 f"{r.se_ratio_P1_base:.3f} | {r.se_ratio_P1_ECG:.3f} | {r.se_ratio_P5_base:.3f} | {'yes' if r.feasible_all else 'no'} | {'yes' if r.feasible_outpt else 'no'} |")
    for nm, trs in (("OUT-29", OUT29), ("OUT-32", OUT32), ("HOSP-6", HOSP)):
        P = PW[PW.trial.isin(trs)]
        q = P[["pct_retained", "pct_smaller_arm_retained", "pct_pairs_P1_base", "pct_events_retained_cohort", "se_ratio_P1_base",
               "se_ratio_P1_ECG", "se_ratio_P5_base"]].quantile([0.25, 0.5, 0.75])
        L += ["", f"**{nm}** median (IQR): retained {q.pct_retained[.5]:.1f}% ({q.pct_retained[.25]:.1f}–{q.pct_retained[.75]:.1f}); "
              f"smaller arm {q.pct_smaller_arm_retained[.5]:.1f}%; P1 pairs {q.pct_pairs_P1_base[.5]:.1f}%; cohort events "
              f"{q.pct_events_retained_cohort[.5]:.1f}%; SE ratio P1 base {q.se_ratio_P1_base[.5]:.3f} "
              f"({q.se_ratio_P1_base[.25]:.3f}–{q.se_ratio_P1_base[.75]:.3f}), P1 ECG {q.se_ratio_P1_ECG[.5]:.3f}, P5 base {q.se_ratio_P5_base[.5]:.3f}. "
              f"Feasible: all initiators {int(P.feasible_all.sum())}/{len(P)}, outpatient {int(P.feasible_outpt.sum())}/{len(P)}; "
              f"analysable (≥ {MIN_ARM} per arm) {int(P.analysable_outpt.sum())}/{len(P)}."]
    L += ["", "## T3. ECG vs base across trials (one-sided exact sign-flip; bshuf = within-set benchmark shuffle)", "",
          "| Set | PS | metric | n | base | +ECG | +perm ECG | k better | p | p vs perm | cluster p | p A | p B | LOO max p | bshuf p |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in S[S.metric.isin(["lt01", "x_lt01", "absd", "cons"])].iterrows():
        L.append(f"| {r.set} | {r.ps} | {r.metric} | {r.n} | {r.base:.3f} | {r.ecg:.3f} | {r.shuf:.3f} | {r.k_better} | {fmt_p(r.p)} | "
                 f"{fmt_p(r.p_vs_shuf)} | {fmt_p(r.cluster_p)} | {fmt_p(r.p_A)} | {fmt_p(r.p_B)} | {fmt_p(r.loo_max_p)} | {fmt_p(r.get('bshuf_p'))} |")
    L += ["", "## T4. Direct restriction effect (outpatient-only minus all initiators, same trials; two-sided exact sign-flip)", "",
          "| Set | PS | arm | metric | n | all | outpt | Δ | k outpt better | p |", "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in RS[RS.arm.isin(["base", "ECG"])].iterrows():
        L.append(f"| {r.set} | {r.ps} | {r.arm} | {r.metric} | {r.n} | {r['all']:.3f} | {r.outpt:.3f} | {r.d_outpt_minus_all:+.3f} | {r.k_outpt_better} | {fmt_p(r.p_two_sided)} |")
    L += ["", "## T5. Domain balance (% of the domain's held-out variables with |SMD| < 0.1, mean over trials; p = ECG vs base)", ""]
    hd = "| Set | PS | arm | " + " | ".join(GROUPS) + " |"
    L += [hd, "|" + "---|" * (3 + len(GROUPS))]
    for _, r in D[D.set.isin(["OUT-29 outpt", "OUT-29 all (same trials)", "HOSP-6 all"]) & D.arm.isin(["base", "ECG"])].iterrows():
        vals = []
        for G in GROUPS:
            v = f"{r[f'lt01:{G}']:.1f}"
            if r.arm == "ECG" and f"p_lt01:{G}" in r and not pd.isna(r[f"p_lt01:{G}"]):
                v += f" (p {fmt_p(r[f'p_lt01:{G}'])})"
            vals.append(v)
        L.append(f"| {r.set} | {r.ps} | {r.arm} | " + " | ".join(vals) + " |")
    L += ["", "## T6. Per-trial HR (outpatient-RCT drug trials; P1)", "",
          "| Trial | RCT HR | all base | all +ECG | outpt base | outpt +ECG | outpt +perm | |Δ| all base→ECG | |Δ| outpt base→ECG |",
          "|---|---|---|---|---|---|---|---|---|"]
    for _, r in PT[PT.trial.isin(OUT32)].iterrows():
        L.append(f"| {r.trial} | {r.rct_hr:.2f} | {r.all_P1_hr_base:.2f} | {r.all_P1_hr_ecg:.2f} | {r.outpt_P1_hr_base:.2f} | {r.outpt_P1_hr_ecg:.2f} | "
                 f"{r.outpt_P1_hr_shuf:.2f} | {r.all_P1_absd_base:.3f}→{r.all_P1_absd_ecg:.3f} | {r.outpt_P1_absd_base:.3f}→{r.outpt_P1_absd_ecg:.3f} |")
    (OUT / "tables.md").write_text("\n".join(L) + "\n")
    os.chmod(OUT / "tables.md", 0o600)
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["prep", "run", "verify", "summarize"])
    ap.add_argument("--trials", default=None)
    ap.add_argument("--pop", default="outpt", choices=["all", "outpt", "inpt"])
    ap.add_argument("--workers", type=int, default=20)
    a = ap.parse_args()
    os.umask(0o077)
    if a.cmd == "prep":
        prep(a.trials.split(",") if a.trials else ALL)
    elif a.cmd == "run":
        trs = a.trials.split(",") if a.trials else (HOSP if a.pop == "inpt" else ALL)
        run(trs, a.workers, a.pop)
    elif a.cmd == "verify":
        verify(a.trials.split(",") if a.trials else ["carolina", "laaos3"])
    else:
        summarize()


if __name__ == "__main__":
    main()
