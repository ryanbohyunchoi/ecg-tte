#!/usr/bin/env python
"""v2.0 G2 extension (exploratory): the v1.9 G2 plasmode (scripts/v19/g2_simulation.py, docs/v19/G2_SIMULATION.md)
with new arms, on the same prepared cells, seeds, grid and replicates.

Questions
  Q1  How much of the C-induced bias does the ECG remove by itself, i.e. a PS on the 32 ECG PCs only (no
      demographics)?  Arms ECGonly and shufECGonly (placebo).  Because the v1.9 treatment model also contains the real
      demographic PS logit, ECG-only leaves demographic confounding; the C-induced part is isolated with the v1.9
      null-corrected excess error (error in a scenario minus error in the null scenario, same arm / subsample), and a
      clean variant "trtC" re-simulates treatment from C alone (no demographic term).
  Q2  Richer PS rungs: sparse (T.X_dx = demo + trial diagnoses), sparse+ECG, hdPS200 (T.X_dx + the 200 top hdPS
      recurrence levels, re-ranked on the simulated treatment within each replicate, as v13_common.Trial.hd), hdPS+ECG,
      clinical (T.X_core minus C's own analogue: lvef for LVEF, bmi for BMI, creatinine for eGFR; nothing for
      NT-proBNP), clinical+ECG.
  Checks  true HR 1.0 and 0.6 (common random numbers: identical subsamples, treatment and uniforms; only the true
      treatment effect changes), arms unmatched/base/ECG/oracle/ECGonly, scenarios null, (1.5,1.5) and (2,2).

Reproduction gate: with this code the v1.9 arms (unmatched, base, ECG, oracle) reproduce v19 reps.csv exactly.
The v1.9 arms are then taken from v19 reps.csv (same seeds) and only the new arms are computed.

Usage: g2b_simulation_ext.py prep | gate | run --variant main|trtC|hr1.0|hr0.6 | summarize | figure
Outputs (aggregates only, umask 077): /mnt/raid0/rbc58/ecg-tte/audits/claude-v20-g2-ext/ (restricted matrices in
cache_ext/; reps_<variant>.csv are replicate-level aggregates, no patient rows).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v19"))
import g2_simulation as G2  # noqa: E402  (reads the v19 prep/cache; never writes: we only call pure functions)
from v13_common import A, cox, match, ps_logit  # noqa: E402

V19 = A / "claude-v19-g2-simulation"
OUT = A / "claude-v20-g2-ext"
CX = OUT / "cache_ext"
DOCS = HERE.parent.parent / "docs" / "v20"
CONF = G2.CONF
OR_ALL = sorted(set(s[0] for s in G2.SCEN))  # [1.0, 1.25, 1.5, 2.0]: rng index oi as in v1.9
NEW_ARMS = ["ECGonly", "shufECGonly", "sparse", "sparseECG", "hdPS", "hdPSECG", "clin", "clinECG"]
V19_ARMS = ["unmatched", "base", "ECG", "shufECG", "noise32", "oracle"]
LAB = {"unmatched": "Unmatched", "base": "Demographic PS", "ECG": "Demographic PS + ECG", "shufECG": "Demo + permuted ECG",
       "noise32": "Demo + noise", "oracle": "Demographic PS + C (oracle)", "ECGonly": "ECG only", "shufECGonly": "Permuted ECG only",
       "sparse": "Sparse PS", "sparseECG": "Sparse PS + ECG", "hdPS": "hdPS200", "hdPSECG": "hdPS200 + ECG",
       "clin": "Clinical PS (minus C analogue)", "clinECG": "Clinical PS + ECG"}
VARIANTS = {
    "main": dict(true_hr=0.8, trt_demo=True, arms=NEW_ARMS, scen=G2.SCEN),
    "trtC": dict(true_hr=0.8, trt_demo=False, arms=["unmatched", "base", "ECG", "ECGonly", "shufECGonly", "oracle"], scen=G2.SCEN),
    "hr1.0": dict(true_hr=1.0, trt_demo=True, arms=["unmatched", "base", "ECG", "ECGonly", "oracle"], scen=[(1.0, 1.0), (1.5, 1.5), (2.0, 2.0)]),
    "hr0.6": dict(true_hr=0.6, trt_demo=True, arms=["unmatched", "base", "ECG", "ECGonly", "oracle"], scen=[(1.0, 1.0), (1.5, 1.5), (2.0, 2.0)]),
    "gate": dict(true_hr=0.8, trt_demo=True, arms=["base", "ECG", "oracle"], scen=G2.SCEN),
    # clinically oriented ("adverse", as the v1.9 post-hoc variant): LVEF and eGFR sign-flipped (higher Cz = lower
    # LVEF / eGFR); NT-proBNP and BMI are unchanged, so only the LVEF and eGFR cells are run
    "adv": dict(true_hr=0.8, trt_demo=True, arms=NEW_ARMS, scen=G2.SCEN, sign="adverse", confs=["lvef", "egfr"]),
    "trtC_adv": dict(true_hr=0.8, trt_demo=False, arms=["unmatched", "base", "ECG", "ECGonly", "shufECGonly", "oracle"], scen=G2.SCEN,
                     sign="adverse", confs=["lvef", "egfr"]),
    "gate_adv": dict(true_hr=0.8, trt_demo=True, arms=["base", "ECG", "oracle"], scen=G2.SCEN, sign="adverse", confs=["lvef", "egfr"]),
}
ADV_SIGN = {"lvef": -1.0, "ntprobnp": 1.0, "bmi": 1.0, "egfr": -1.0}
G = {}


# ---------------------------------------------------------------- prep: sparse / clinical / hdPS matrices per trial
def prep_one(n):
    import v18_af_confirm as AF
    E = AF.V.E
    _, OLD, _ = G2.trial_list()
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    D = dict(np.load(G2.CACHE / f"restricted_prep_{n}.npz"))
    # identity check against the v1.9 cache (same patients, same order)
    same = (np.array_equal(D["demo"], T.cov[T.demo].to_numpy(float)) and np.array_equal(D["ecg"], T.ecg_pc.astype(float)))
    if not same:
        raise RuntimeError(f"{n}: v1.9 cache does not match the reloaded trial")
    core = list(T.core)
    lv = T.lv.to_numpy()
    if not np.isin(np.unique(lv), [0, 1]).all():
        raise RuntimeError(f"{n}: hdPS levels not binary")
    os.umask(0o077)
    CX.mkdir(parents=True, exist_ok=True)
    np.savez(CX / f"restricted_ext_{n}.npz", dx=T.X_dx.astype(float), core=T.X_core.astype(float), lv=lv.astype(np.uint8),
             core_names=np.array(core), dx_names=np.array(list(T.demo) + list(T.dxc)))
    info = dict(trial=n, n_dx=T.X_dx.shape[1], n_core=T.X_core.shape[1], n_lv=lv.shape[1],
                removed={c: [k for k in core if k == CONF[c][3]] for c in CONF})
    print(n, info["n_dx"], info["n_core"], info["n_lv"], flush=True)
    return info


def prep(workers):
    from multiprocessing import Pool
    P = pd.read_csv(V19 / "prep_conf.csv")
    trials = sorted(P[P.eligible].trial.unique())
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(min(workers, len(trials))) as p:
        res = p.map(prep_one, trials, chunksize=1)
    pd.DataFrame([{**r, "removed": json.dumps(r["removed"])} for r in res]).to_csv(OUT / "prep_ext.csv", index=False)


# ---------------------------------------------------------------- simulation
def load(n):
    if n not in G:
        G.clear()
        G[n] = (dict(np.load(G2.CACHE / f"restricted_prep_{n}.npz")), dict(np.load(CX / f"restricted_ext_{n}.npz")))
    return G[n]


def hd_top(L, trt, k=200):
    """hdPS top-k levels ranked on the (simulated) treatment, as eval_longtail_balance.hdps_rank."""
    p1 = L[trt == 1].mean(0) + 1e-3
    p0 = L[trt == 0].mean(0) + 1e-3
    s = np.abs(np.log(p1 / p0))
    return np.argsort(-s, kind="stable")[:k]


def one(job):
    n, c, rep, info, variant = job
    from scipy.optimize import brentq
    from scipy.special import expit
    V = VARIANTS[variant]
    D, X = load(n)
    Si, cz, lpd, lpc = D[f"{c}__rows"], D[f"{c}__cz"], D[f"{c}__lpd"], D[f"{c}__lpc"]
    if V.get("sign") == "adverse":
        cz = ADV_SIGN[c] * cz
    lam0, rho = info["lam"], info["rho"]
    alpha = {float(k): v for k, v in json.loads(info["alpha"]).items()}
    if not V["trt_demo"]:  # treatment from C only: recalibrate the intercept to the real treated share (full S)
        alpha = {o: brentq(lambda a: expit(a + np.log(o) * cz).mean() - info["pbar"], -30, 30) for o in OR_ALL}
    ti, ci = info["idx"], list(CONF).index(c)
    N = len(Si)
    sub = np.sort(np.random.default_rng([50_000 + rep, ti, ci]).choice(N, int(round(G2.FRAC * N)), replace=False))
    rows = Si[sub]
    czs, lpds, lpcs, Cadm = cz[sub], lpd[sub], lpc[sub], D["Cadm"][rows]
    if not V["trt_demo"]:
        lpds = np.zeros_like(lpds)
    X1, ecg = D["demo"][rows], D["ecg"][rows]
    dx, L = X["dx"][rows], X["lv"][rows]
    names = list(X["core_names"])
    keep = [j for j, k in enumerate(names) if k != CONF[c][3]]
    core = X["core"][rows][:, keep]
    blocks = {"base": lambda t: X1, "ECG": lambda t: np.hstack([X1, ecg]), "shufECG": lambda t: np.hstack([X1, D["shuf"][rows]]),
              "noise32": lambda t: np.hstack([X1, D["noise"][rows]]), "oracle": lambda t: np.column_stack([X1, czs]),
              "ECGonly": lambda t: ecg, "shufECGonly": lambda t: D["shuf"][rows],
              "sparse": lambda t: dx, "sparseECG": lambda t: np.hstack([dx, ecg]),
              "hdPS": lambda t: np.hstack([dx, L[:, hd_top(L, t)]]), "hdPSECG": lambda t: np.hstack([dx, L[:, hd_top(L, t)], ecg]),
              "clin": lambda t: core, "clinECG": lambda t: np.hstack([core, ecg])}
    scen = V["scen"]
    out = []
    for orr in sorted(set(s[0] for s in scen)):
        oi = OR_ALL.index(orr)
        trt = (np.random.default_rng([60_000 + rep, ti, ci, oi]).uniform(size=len(rows)) <
               expit(alpha[orr] + lpds + np.log(orr) * czs)).astype(int)
        if min(trt.sum(), (1 - trt).sum()) < 50:
            continue
        M = {}
        for a in V["arms"]:
            if a == "unmatched":
                M[a] = (np.arange(len(rows)), None)
            else:
                idx, cl, _ = match(ps_logit(blocks[a](trt), trt), trt)
                M[a] = (idx, cl)
        for hry in [s[1] for s in scen if s[0] == orr]:
            hi = G2.HRS.index(hry) if hry in G2.HRS else -1
            lam = lam0 / float(np.mean(np.exp(np.log(hry) * cz)))
            lp0 = lpcs + np.log(hry) * czs
            u = np.random.default_rng([70_000 + rep, ti, ci, oi, hi + 1]).uniform(size=len(rows))
            tt, ee = G2.simulate(lp0 + np.log(V["true_hr"]) * trt, lam, rho, Cadm, u)
            U = np.random.default_rng([80_000 + rep, ti, ci, oi, hi + 1]).uniform(size=(G2.COPIES, len(rows)))
            for a, (idx, cl) in M.items():
                b, se = cox(tt[idx], ee[idx], trt[idx], cluster=cl)
                ts, es, xs = [], [], []
                for k in range(G2.COPIES):
                    for x in (0, 1):
                        t_, e_ = G2.simulate(lp0[idx] + np.log(V["true_hr"]) * x, lam, rho, Cadm[idx], U[k, idx])
                        ts.append(t_); es.append(e_); xs.append(np.full(len(idx), x))
                tr = G2.cox_fast(np.concatenate(ts), np.concatenate(es), np.concatenate(xs))
                out.append(dict(trial=n, conf=c, or_t=orr, hr_y=hry, rep=rep, arm=a, loghr=b, se=se, truth=tr,
                                n_an=len(idx), n_t=int(trt[idx].sum()), events=int(ee[idx].sum())))
    return out


def cells():
    P = pd.read_csv(V19 / "prep_conf.csv")
    P = P[P.eligible]
    return {(r.trial, r.conf): dict(lam=r.lam, rho=r.rho, alpha=r.alpha, idx=int(r.idx), pbar=r.pbar) for r in P.itertuples()}


def run(variant, reps, workers, only=None):
    from multiprocessing import Pool
    os.umask(0o077)
    info = cells()
    if only:
        info = {k: v for k, v in info.items() if k in only}
    if VARIANTS[variant].get("confs"):
        info = {k: v for k, v in info.items() if k[1] in VARIANTS[variant]["confs"]}
    jobs = [(n, c, rep, info[(n, c)], variant) for (n, c) in info for rep in range(reps)]
    t0 = time.time()
    res = []
    with Pool(workers) as p:
        for k, o in enumerate(p.imap(one, jobs, chunksize=4)):
            res.extend(o)
            if k % 200 == 0:
                print(f"{variant} {k}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    R = pd.DataFrame(res)
    R.to_csv(OUT / f"reps_{variant}.csv", index=False)
    print("done", variant, len(R), f"{time.time() - t0:.0f}s", flush=True)
    return R


def gate(workers, variant="gate"):
    """v1.9 arms must reproduce v19 reps.csv (or reps_adverse.csv) exactly on the same seeds (3 cells x 3 replicates)."""
    adv = variant == "gate_adv"
    ref = pd.read_csv(V19 / ("reps_adverse.csv" if adv else "reps.csv"), float_precision="round_trip")  # default parser is not round-trip exact
    pick = [("comet", "lvef"), ("aristotle", "lvef"), ("plato", "egfr")] if adv else [("comet", "lvef"), ("aristotle", "bmi"), ("plato", "egfr")]
    info = cells()
    pick = [k for k in pick if k in info][:3] or list(info)[:3]
    jobs = [(n, c, rep, info[(n, c)], variant) for (n, c) in pick for rep in range(3)]
    from multiprocessing import Pool
    with Pool(min(workers, len(jobs))) as p:
        R = pd.DataFrame([x for o in p.map(one, jobs) for x in o])
    # compare after the same CSV round trip the reference went through
    import io
    buf = io.StringIO(); R.to_csv(buf, index=False); buf.seek(0)
    R = pd.read_csv(buf, float_precision="round_trip")
    key = ["trial", "conf", "or_t", "hr_y", "rep", "arm"]
    m = R.merge(ref, on=key, suffixes=("", "_ref"))
    dev = {v: float(np.nanmax(np.abs(m[v] - m[f"{v}_ref"]))) for v in ("loghr", "se", "truth", "n_an", "n_t", "events")}
    ok = len(m) == len(R) and all(d == 0 for d in dev.values())
    print("gate rows", len(R), "matched", len(m), "max |dev|", dev, "PASS" if ok else "FAIL", flush=True)
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([dict(rows=len(R), matched=len(m), **{f"maxdev_{k}": v for k, v in dev.items()}, passed=ok)]).to_csv(OUT / f"{variant}.csv", index=False)
    if not ok:
        raise SystemExit("reproduction gate failed")


# ---------------------------------------------------------------- summaries
def excluded():
    return pd.read_csv(V19 / "excluded_cells.csv")


def errs(R):
    bad = excluded().assign(_x=1)
    R = R.merge(bad, on=["trial", "conf"], how="left")
    R = R[R._x.isna()].drop(columns="_x").copy()
    R["err"] = R.loghr - R.truth
    R["cover"] = np.where(R.se.notna(), (np.abs(R.err) <= 1.96 * R.se).astype(float), np.nan)
    return R


def pooled(R, arms, ref_arms=("unmatched", "base"), B=1000, seed=0):
    """Pooled % of bias removed over trial x C x non-null scenario cells (ratio of summed cell-mean errors), raw and
    null-corrected, with Monte Carlo SE from resampling replicates within cells; plus bias, empirical SE, RMSE,
    coverage, each with MCSE (Morris et al. 2019)."""
    W = R.pivot_table(index=["trial", "conf", "or_t", "hr_y", "rep"], columns="arm", values="err")
    Wr = W.reset_index()
    nul = Wr[Wr.or_t == 1.0].drop(columns=["or_t", "hr_y"]).set_index(["trial", "conf", "rep"])
    ex = Wr[Wr.or_t != 1.0].set_index(["trial", "conf", "rep"])
    have = [a for a in arms if a in W.columns]
    exc = ex[have] - nul.reindex(ex.index)[have] if len(nul) else None
    if exc is not None:
        exc[["or_t", "hr_y"]] = ex[["or_t", "hr_y"]]
        exc = exc.reset_index()
    raw = ex.reset_index()
    rng = np.random.default_rng(seed)
    out = []
    for lab, data in (("raw", raw), ("null-corrected", exc)):
        if data is None:
            continue
        for conf in list(CONF) + ["all"]:
            d = data if conf == "all" else data[data.conf == conf]
            if not len(d):
                continue
            cm = d.groupby(["trial", "conf", "or_t", "hr_y"])[have].mean()
            # bootstrap replicates within each cell (Monte Carlo error)
            groups = [g[have].to_numpy() for _, g in d.groupby(["trial", "conf", "or_t", "hr_y"])]
            boots = np.empty((B, len(have)))
            for b in range(B):
                boots[b] = np.sum([g[rng.integers(0, len(g), len(g))].mean(0) for g in groups], axis=0)
            sums = cm.sum().to_numpy()
            for i, a in enumerate(have):
                r = dict(analysis=lab, conf=conf, arm=a, k_cells=d[["trial", "conf"]].drop_duplicates().shape[0],
                         mean_bias=cm[a].mean())
                for rf in ref_arms:
                    if rf not in have:
                        continue
                    j = have.index(rf)
                    r[f"pct_vs_{rf}"] = 100 * (1 - sums[i] / sums[j])
                    r[f"mcse_vs_{rf}"] = float(np.std(100 * (1 - boots[:, i] / boots[:, j]), ddof=1))
                out.append(r)
    S = pd.DataFrame(out)
    # performance measures on the raw non-null cells, averaged over cells
    perf = []
    for conf in list(CONF) + ["all"]:
        d = R[(R.or_t != 1.0)] if conf == "all" else R[(R.or_t != 1.0) & (R.conf == conf)]
        for a in have:
            g = d[d.arm == a]
            c = g.groupby(["trial", "conf", "or_t", "hr_y"])
            nrep = c.err.count()
            bias, esd = c.err.mean(), c.loghr.std()
            rmse = np.sqrt(c.err.apply(lambda e: np.mean(e ** 2)))
            cov = 100 * c.cover.mean()
            perf.append(dict(conf=conf, arm=a, k=len(nrep), mean_reps=nrep.mean(), bias=bias.mean(),
                             bias_mcse=np.sqrt(np.mean((esd ** 2) / nrep) / len(nrep)),
                             emp_se=esd.mean(), emp_se_mcse=np.sqrt(np.mean(esd ** 2 / (2 * (nrep - 1)))) / np.sqrt(len(nrep)),
                             rmse=rmse.mean(), coverage=cov.mean(),
                             coverage_mcse=np.sqrt(np.mean(cov * (100 - cov) / nrep)) / np.sqrt(len(nrep))))
    return S, pd.DataFrame(perf)


def summarize():
    os.umask(0o077)
    v19 = errs(pd.read_csv(V19 / "reps.csv"))
    main = errs(pd.read_csv(OUT / "reps_main.csv"))
    R = pd.concat([v19, main], ignore_index=True)
    arms = V19_ARMS + NEW_ARMS
    S, Pf = pooled(R, arms, ref_arms=("unmatched", "base", "sparse", "hdPS", "clin"))
    S.to_csv(OUT / "pooled_main.csv", index=False)
    Pf.to_csv(OUT / "performance_main.csv", index=False)
    # added value of ECG over each PS (pooled, raw and null-corrected): % of that PS's remaining bias removed
    add = []
    for lab in ("raw", "null-corrected"):
        for conf in list(CONF) + ["all"]:
            s = S[(S.analysis == lab) & (S.conf == conf)].set_index("arm")
            for ps, pe in (("base", "ECG"), ("sparse", "sparseECG"), ("hdPS", "hdPSECG"), ("clin", "clinECG")):
                if ps in s.index and pe in s.index:
                    add.append(dict(analysis=lab, conf=conf, ps=ps, ecg_arm=pe, ps_pct_vs_unm=s.loc[ps, "pct_vs_unmatched"],
                                    ps_ecg_pct_vs_unm=s.loc[pe, "pct_vs_unmatched"],
                                    ecg_added_pct_of_ps_bias=s.loc[pe, f"pct_vs_{ps}"], mcse=s.loc[pe, f"mcse_vs_{ps}"]))
    pd.DataFrame(add).to_csv(OUT / "ecg_added_value.csv", index=False)
    for v in ("trtC", "hr1.0", "hr0.6"):
        f = OUT / f"reps_{v}.csv"
        if not f.exists():
            continue
        Rv = errs(pd.read_csv(f))
        arms_v = VARIANTS[v]["arms"]
        Sv, Pv = pooled(Rv, arms_v, ref_arms=("unmatched", "base"))
        Sv.to_csv(OUT / f"pooled_{v}.csv", index=False)
        Pv.to_csv(OUT / f"performance_{v}.csv", index=False)
    # clinically oriented set ("clin-orient"): LVEF and eGFR from the adverse runs (v19 reps_adverse + reps_adv),
    # NT-proBNP and BMI from the as-designed runs (identical by construction)
    if (OUT / "reps_adv.csv").exists():
        adv = pd.concat([errs(pd.read_csv(V19 / "reps_adverse.csv")), errs(pd.read_csv(OUT / "reps_adv.csv"))], ignore_index=True)
        Rc = pd.concat([adv[adv.conf.isin(["lvef", "egfr"])], R[R.conf.isin(["ntprobnp", "bmi"])]], ignore_index=True)
        Sc, Pc = pooled(Rc, arms, ref_arms=("unmatched", "base", "sparse", "hdPS", "clin"))
        Sc.to_csv(OUT / "pooled_cliniorient.csv", index=False)
        Pc.to_csv(OUT / "performance_cliniorient.csv", index=False)
        addc = []
        for lab in ("raw", "null-corrected"):
            for conf in list(CONF) + ["all"]:
                s_ = Sc[(Sc.analysis == lab) & (Sc.conf == conf)].set_index("arm")
                for ps, pe in (("base", "ECG"), ("sparse", "sparseECG"), ("hdPS", "hdPSECG"), ("clin", "clinECG")):
                    if ps in s_.index and pe in s_.index:
                        addc.append(dict(analysis=lab, conf=conf, ps=ps, ecg_arm=pe, ps_pct_vs_unm=s_.loc[ps, "pct_vs_unmatched"],
                                         ps_ecg_pct_vs_unm=s_.loc[pe, "pct_vs_unmatched"],
                                         ecg_added_pct_of_ps_bias=s_.loc[pe, f"pct_vs_{ps}"], mcse=s_.loc[pe, f"mcse_vs_{ps}"]))
        pd.DataFrame(addc).to_csv(OUT / "ecg_added_value_cliniorient.csv", index=False)
    if (OUT / "reps_trtC_adv.csv").exists() and (OUT / "reps_trtC.csv").exists():
        ta, tm = errs(pd.read_csv(OUT / "reps_trtC_adv.csv")), errs(pd.read_csv(OUT / "reps_trtC.csv"))
        Rt = pd.concat([ta[ta.conf.isin(["lvef", "egfr"])], tm[tm.conf.isin(["ntprobnp", "bmi"])]], ignore_index=True)
        St, Pt = pooled(Rt, VARIANTS["trtC"]["arms"], ref_arms=("unmatched", "base"))
        St.to_csv(OUT / "pooled_trtC_cliniorient.csv", index=False)
        Pt.to_csv(OUT / "performance_trtC_cliniorient.csv", index=False)
    # true-HR check reference: the same scenarios from the 0.8 run
    sub = R[R.arm.isin(["unmatched", "base", "ECG", "ECGonly", "oracle"]) &
            (((R.or_t == 1.0) & (R.hr_y == 1.0)) | ((R.or_t == 1.5) & (R.hr_y == 1.5)) | ((R.or_t == 2.0) & (R.hr_y == 2.0)))]
    Sr, Pr = pooled(sub, ["unmatched", "base", "ECG", "ECGonly", "oracle"], ref_arms=("unmatched", "base"))
    Sr.to_csv(OUT / "pooled_hr0.8_subset.csv", index=False)
    Pr.to_csv(OUT / "performance_hr0.8_subset.csv", index=False)
    print(S[S.conf == "all"].round(2).to_string())


def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    f = OUT / "pooled_cliniorient.csv"
    S = pd.read_csv(f if f.exists() else OUT / "pooled_main.csv")
    S = S[S.analysis == "null-corrected"]
    confs = ["lvef", "ntprobnp", "bmi", "egfr", "all"]
    rungs = [("Unmatched", None, None), ("ECG only", "ECGonly", None), ("Demographic", "base", "ECG"), ("Sparse", "sparse", "sparseECG"),
             ("hdPS200", "hdPS", "hdPSECG"), ("Clinical\n(minus C)", "clin", "clinECG")]
    fig, axes = plt.subplots(1, 5, figsize=(17, 4.2), sharey=True)
    for ax, c in zip(axes, confs):
        s = S[S.conf == c].set_index("arm").pct_vs_unmatched
        xs = np.arange(len(rungs))
        for i, (lab, a0, a1) in enumerate(rungs):
            if a0 and a0 in s:
                ax.bar(i - 0.18 if a1 else i, s[a0], 0.36, color="#9aa0b8" if a0 != "ECGonly" else "#d9544d")
            if a1 and a1 in s:
                ax.bar(i + 0.18, s[a1], 0.36, color="#d9544d")
        if "oracle" in s:
            ax.axhline(s["oracle"], color="#0c1040", ls="--", lw=1)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_xticks(xs)
        ax.set_xticklabels([r[0] for r in rungs], rotation=45, ha="right", fontsize=9)
        ax.set_title({"all": "All confounders"}.get(c, CONF.get(c, (None,) * 5)[4]), fontsize=11)
    axes[0].set_ylabel("% of C-induced bias removed\nvs unmatched (null-corrected)")
    from matplotlib.patches import Patch
    axes[-1].legend(handles=[Patch(color="#9aa0b8", label="PS alone"), Patch(color="#d9544d", label="with ECG / ECG only"),
                             plt.Line2D([], [], color="#0c1040", ls="--", label="demographic PS + C (oracle)")], fontsize=8, loc="lower right")
    fig.tight_layout()
    DOCS.mkdir(parents=True, exist_ok=True)
    fig.savefig(DOCS / "G2_EXT_bias_by_rung.png", dpi=150)
    print("figure saved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "gate", "run", "summarize", "figure"])
    ap.add_argument("--variant", default="main", choices=list(VARIANTS))
    ap.add_argument("--reps", type=int, default=50)
    ap.add_argument("--workers", type=int, default=40)
    a = ap.parse_args()
    os.umask(0o077)
    if a.cmd == "prep":
        prep(a.workers)
    elif a.cmd == "gate":
        gate(a.workers, a.variant if a.variant.startswith("gate") else "gate")
    elif a.cmd == "run":
        run(a.variant, a.reps, a.workers)
    elif a.cmd == "summarize":
        summarize()
    else:
        figure()
