#!/usr/bin/env python
"""v1.9 G2 (docs/v18/V19_GERMAN_STYLE_PLAN.md): plasmode-style simulation of how much confounding by a held-out
physiological variable C the ECG embedding removes, as a function of the ECG's cross-fitted R² for C. Exploratory.

Design (per trial of the 38 = v18_af_confirm.ALL, per confounder C in {echo LVEF, log NT-proBNP, BMI, eGFR}):
  * S = patients with a usable outcome (T.y_ok) and C observed (valid range); skip the trial x C combination if
    either REAL arm in S has < 300 patients.  Cz = C standardised in S (NT-proBNP on the log scale).
  * Real covariates, real ECG PCs (T.ecg_pc, 32), real index dates / administrative censoring (min(horizon, end of
    death or cause-of-death data - index), as scripts/v13_plasmode.py) are kept.
  * Treatment is re-simulated: logit P(T=1) = a + eta_demo + log(OR_T) * Cz, eta_demo = real PS logit of the real
    treatment on T.demo in S (L2 C = 1, as v13_common.ps_logit), a calibrated so that mean P = real treated share in S.
    OR_T per SD in {1.25, 1.5, 2}, plus a null check OR_T = 1.
  * Outcome: Weibull proportional hazards, lp = Zcore beta + log(HR_Y) * Cz + log(0.8) * T, with beta from a Cox fit
    (penalizer 0.01) of the real outcome on the real treatment + standardised T.X_core in S (minus the column that is
    C's own analogue: lvef / bmi / creatinine), baseline = Weibull smoothing of the Breslow hazard (v13_plasmode);
    lambda is divided by mean(exp(log(HR_Y) Cz)) so the event rate stays near the real one.  HR_Y per SD in
    {1.25, 1.5, 2}; with OR_T = 1 only HR_Y = 1.  Conditional true log HR = log(0.8).
  * Replicates: 80% subsampling of S without replacement (the valid plasmode of docs/AUDIT_2026_09_25.md; the
    with-replacement bootstrap with re-matching is not used), 50 per scenario; per replicate the treatment is
    re-drawn, every PS refitted and every arm re-matched (1:1 greedy caliper 0.2 SD of the logit, v13_common.match),
    Cox with pair-clustered robust SE (v13_common.cox).
  * Arms: unmatched | P1 base (T.demo) | +ECG32 | +shufECG32 (T.ecg_pc[T.shuffle_perm]) | +noise32 (T.noise32) |
    oracle = base + Cz.  C is in no PS except the oracle.
  * Truth per replicate x arm x scenario: marginal log HR in that arm's analysed (matched) population from
    counterfactual outcomes under both treatments (5 copies, common random numbers; single-covariate Newton Cox,
    validated against lifelines in `check`).
Real-data R²: 5-fold cross-fitted ridge (RidgeCV) R² of Cz on ECG32 in S; also demo alone, demo + ECG32, partial
  R²(ECG | demo) = (R²(demo+ECG) - R²(demo)) / (1 - R²(demo)), and shufECG32 / noise32 placebos.
Endpoints: bias = mean(loghr - truth); % bias removed vs unmatched = 100 * (1 - bias_arm / bias_unmatched) and vs
  base = 100 * (1 - bias_arm / bias_base) (ratios of mean biases over replicates; replicate-resampling CI);
  coverage = % of replicates with |loghr - truth| <= 1.96 se.

Usage: g2_simulation.py prep [--trials] | check | run [--reps 50] | summarize | figure | report
Outputs (aggregates only, umask 077): /mnt/raid0/rbc58/ecg-tte/audits/claude-v19-g2-simulation/; restricted per-trial
  arrays in cache/restricted_prep_<trial>.npz; docs/v19/G2_bias_vs_R2.png, docs/v19/G2_SIMULATION.md.
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
sys.path.insert(0, str(HERE.parent / "v18"))
sys.path.insert(0, str(HERE.parent / "v16"))
sys.path.insert(0, str(HERE.parent))
from v13_common import A, cox, match, ps_logit  # noqa: E402

OUT = Path(os.environ.get("G2_OUT", A / "claude-v19-g2-simulation"))
CACHE = OUT / "cache"
DOCS = Path(os.environ.get("G2_DOCS", HERE.parent.parent / "docs" / "v19"))
# name -> (T.H column, valid range, log scale, X_core analogue dropped from the outcome model, label)
CONF = {"lvef": ("pp_LVFUNC__ef", (5, 90), False, "lvef", "Echo LVEF"),
        "ntprobnp": ("pp_BNP__ntprobnp", (5, 1e5), True, None, "NT-proBNP (log)"),
        "bmi": ("obs_bmi", (12, 80), False, "bmi", "BMI"),
        "egfr": ("pp_LAB__egfr", (1, 200), False, "creatinine", "eGFR")}
ORS = [1.25, 1.5, 2.0]
HRS = [1.25, 1.5, 2.0]
SCEN = [(1.0, 1.0)] + [(o, h) for o in ORS for h in HRS]
TRUE_HR = 0.8
ARMS = ["unmatched", "base", "ECG", "shufECG", "noise32", "oracle"]
MIN_ARM = 300
FRAC = 0.8
COPIES = 5
MIN_CELL = 11
G = {}
# post-hoc sensitivity variants (logged in docs/v19/G2_SIMULATION.md): "adverse" = C oriented clinically adverse (LVEF and
# eGFR sign-flipped, so higher Cz = lower LVEF / eGFR); "conly" = outcome depends on C and treatment only (Zcore beta = 0)
VARIANT = os.environ.get("G2_VARIANT", "main")
SUF = "" if VARIANT == "main" else f"_{VARIANT}"
SIGN = {"lvef": -1.0, "ntprobnp": 1.0, "bmi": 1.0, "egfr": -1.0} if VARIANT == "adverse" else {c: 1.0 for c in CONF}


def trial_list():
    import v18_af_confirm as AF
    return list(AF.ALL), list(AF.V.OLD), list(AF.AF5)


# ---------------------------------------------------------------- fast Cox (single binary covariate, Breslow)
def cox_fast(t, e, x, iters=25):
    o = np.lexsort((-e, -t))  # descending time; within ties events first (irrelevant: risk set uses group ends)
    t, e, x = t[o], e[o].astype(float), x[o].astype(float)
    # risk set of i = all j with t_j >= t_i -> cumulative sums up to the last index of the tie group
    last = np.r_[np.nonzero(np.diff(t))[0], len(t) - 1]
    grp_end = np.repeat(last, np.diff(np.r_[-1, last]))
    b = 0.0
    for _ in range(iters):
        w = np.exp(b * x)
        S0 = np.cumsum(w)[grp_end]
        S1 = np.cumsum(w * x)[grp_end]
        p = S1 / S0
        U = np.sum(e * (x - p))
        I = np.sum(e * p * (1 - p))
        if I <= 0:
            return np.nan
        step = U / I
        b += step
        if abs(step) < 1e-10:
            break
    return float(b)


def simulate(lp, lam, rho, C, u):
    tev = (-np.log(u) / (lam * np.exp(lp))) ** (1 / rho)
    return np.minimum(tev, C), (tev <= C).astype(int)


# ---------------------------------------------------------------- prep
def clean_c(T, name):
    col, (lo, hi), lg, _, _ = CONF[name]
    if col not in T.H:
        return np.full(len(T.t), np.nan)
    v = T.H[col].to_numpy(float).copy()
    v[(v < lo) | (v > hi)] = np.nan
    return np.log(v) if lg else v


def cv_r2(X, y, seed=0):
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import KFold
    from sklearn.preprocessing import StandardScaler
    pred = np.zeros(len(y))
    for tr, te in KFold(5, shuffle=True, random_state=seed).split(X):
        sc = StandardScaler().fit(X[tr])
        m = RidgeCV(alphas=np.logspace(-2, 4, 13)).fit(sc.transform(X[tr]), y[tr])
        pred[te] = m.predict(sc.transform(X[te]))
    return float(1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2))


def prep_one(n):
    from lifelines import CoxPHFitter
    from trial_specs import COD_END, DEATH_END, OUTCOMES
    import v18_af_confirm as AF
    E = AF.V.E
    ALL, OLD, AF5 = trial_list()
    t0 = time.time()
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    i = ALL.index(n)
    # engine reproduction: P1 base, full cohort, vs the v1.7 / v1.8 result files
    X1 = T.cov[T.demo].to_numpy(float)
    o = E.run_cell(T, X1, estimator=("match", 0.2, 1), cstat=None)
    ref = pd.read_csv(A / ("claude-v18-af-confirm/results_af5.csv" if n in AF5 else "claude-v17-confirm/results_all.csv"))
    ref = ref[(ref.trial == n) & (ref.half == "full") & (ref.ps == "P1") & (ref.arm_role == "base")]
    meta = dict(trial=n, key=T.key, idx=i, n=len(T.t), engine_loghr=o["loghr"], engine_se=o["se"], engine_pairs=o["n_pairs"],
                ref_loghr=float(ref.loghr.iloc[0]) if len(ref) else np.nan, ref_pairs=float(ref.n_pairs.iloc[0]) if len(ref) else np.nan)
    meta["repro_absdev"] = abs(meta["engine_loghr"] - meta["ref_loghr"])
    uses_cause = any(c in ("cv_death", "chd_death") for c in OUTCOMES[T.key])
    end = pd.Timestamp(COD_END if uses_cause else DEATH_END)
    Cadm = np.minimum(T.horizon, (end - T.index_date).dt.days.to_numpy(float)).clip(min=1)
    arr = dict(t=T.t.astype(np.int8), y_t=T.y_t.astype(float), y_e=T.y_e.astype(np.int8), y_ok=T.y_ok.astype(bool),
               demo=X1, ecg=T.ecg_pc.astype(float), shuf=T.ecg_pc[T.shuffle_perm].astype(float), noise=T.noise32.astype(float),
               Cadm=Cadm)
    rows = []
    for c in CONF:
        v = clean_c(T, c)
        S = T.y_ok & ~np.isnan(v) & ~np.isnan(Cadm)
        nt, nc = int(T.t[S].sum()), int((1 - T.t[S]).sum())
        r = dict(trial=n, key=T.key, idx=i, conf=c, n_obs=int(S.sum()), n_obs_t=nt, n_obs_c=nc, obs_frac=float(S.mean()),
                 eligible=bool(min(nt, nc) >= MIN_ARM))
        if S.sum() >= 50:
            y = v[S]
            yz = (y - y.mean()) / y.std()
            r.update(r2_ecg=cv_r2(T.ecg_pc[S], yz), r2_demo=cv_r2(X1[S], yz), r2_demo_ecg=cv_r2(np.hstack([X1[S], T.ecg_pc[S]]), yz),
                     r2_shuf=cv_r2(T.ecg_pc[T.shuffle_perm][S], yz), r2_noise=cv_r2(T.noise32[S], yz))
            r["r2_partial"] = (r["r2_demo_ecg"] - r["r2_demo"]) / (1 - r["r2_demo"])
            # real-data confounding strength of C (for context): SMD between real arms, Cox HR per SD (unadjusted)
            tS = T.t[S]
            r["smd_real"] = float((yz[tS == 1].mean() - yz[tS == 0].mean()))
        if r["eligible"]:
            Si = np.where(S)[0]
            yz = (v[Si] - v[Si].mean()) / v[Si].std()
            lpd = ps_logit(X1[Si], T.t[Si])
            lpd = lpd - lpd.mean()
            core = [k for k in T.core if k != CONF[c][3]]
            Xc = T.cov.iloc[Si][core].to_numpy(float)
            sd = Xc.std(0)
            keep = sd > 0
            Z = (Xc[:, keep] - Xc[:, keep].mean(0)) / sd[keep]
            d = pd.DataFrame(Z, columns=[core[j] for j in np.where(keep)[0]])
            d["treated"], d["tt"], d["ee"] = T.t[Si], T.y_t[Si], T.y_e[Si]
            cph = CoxPHFitter(penalizer=0.01).fit(d, "tt", "ee")
            beta = cph.params_.drop("treated").reindex(d.columns[:-3]).to_numpy()
            bh = cph.baseline_cumulative_hazard_
            tb, Hb = bh.index.to_numpy(float), bh.iloc[:, 0].to_numpy(float)
            m = (tb > 0) & (Hb > 0)
            rho, loglam = np.polyfit(np.log(tb[m]), np.log(Hb[m]), 1)
            lam = float(np.exp(loglam)) * float(np.exp(-cph.params_["treated"] * d.treated.mean()))
            lpc = Z @ beta
            pbar = float(T.t[Si].mean())
            from scipy.optimize import brentq
            from scipy.special import expit
            alpha = {}
            for orr in sorted(set(s[0] for s in SCEN)):
                g = np.log(orr) * yz
                alpha[orr] = brentq(lambda a: expit(a + lpd + g).mean() - pbar, -30, 30)
            arr[f"{c}__rows"] = Si
            arr[f"{c}__cz"] = yz
            arr[f"{c}__lpd"] = lpd
            arr[f"{c}__lpc"] = lpc
            r.update(rho=float(rho), lam=lam, pbar=pbar, real_event_rate=float(T.y_e[Si].mean()), n_core=int(keep.sum()),
                     alpha=json.dumps({str(k): v for k, v in alpha.items()}))
            u = np.random.default_rng(7).uniform(size=len(Si))
            tsim = (np.random.default_rng(8).uniform(size=len(Si)) < expit(alpha[1.0] + lpd)).astype(int)
            r["sim_event_rate_null"] = float(simulate(lpc + np.log(TRUE_HR) * tsim, lam, rho, Cadm[Si], u)[1].mean())
        rows.append(r)
    os.umask(0o077)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE / f"restricted_prep_{n}.npz", **arr)
    meta["secs"] = round(time.time() - t0, 1)
    print(n, meta["secs"], "s repro dev", meta["repro_absdev"], flush=True)
    return meta, rows


def prep(trials, workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(min(workers, len(trials))) as p:
        res = p.map(prep_one, trials, chunksize=1)
    M = pd.DataFrame([m for m, _ in res])
    R = pd.DataFrame([r for _, rr in res for r in rr])
    tag = "" if len(trials) >= 38 else "_partial"
    M.to_csv(OUT / f"prep_meta{tag}.csv", index=False)
    suppress(R).to_csv(OUT / f"prep_conf{tag}.csv", index=False)
    print(M[["trial", "engine_loghr", "ref_loghr", "repro_absdev"]].to_string())
    print(R[["trial", "conf", "n_obs_t", "n_obs_c", "eligible"] + [c for c in ("r2_ecg", "r2_partial") if c in R]].round(3).to_string())


def suppress(D):
    D = D.copy()
    for c in [c for c in D.columns if c.startswith("n_")]:
        v = pd.to_numeric(D[c], errors="coerce")
        D.loc[(v >= 1) & (v < MIN_CELL), c] = np.nan
    return D


# ---------------------------------------------------------------- simulation
def load_prep(n):
    if n not in G:
        G.clear()
        G[n] = dict(np.load(CACHE / f"restricted_prep_{n}.npz"))
    return G[n]


def one(job):
    """One replicate of one trial x confounder: every scenario, every arm."""
    n, c, rep, info = job
    from scipy.special import expit
    D = load_prep(n)
    Si, cz, lpd, lpc = D[f"{c}__rows"], SIGN[c] * D[f"{c}__cz"], D[f"{c}__lpd"], D[f"{c}__lpc"]
    if VARIANT == "conly":
        lpc = np.zeros_like(lpc)
    lam0, rho, alpha = info["lam"], info["rho"], {float(k): v for k, v in json.loads(info["alpha"]).items()}
    ti, ci = info["idx"], list(CONF).index(c)
    N = len(Si)
    sub = np.sort(np.random.default_rng([50_000 + rep, ti, ci]).choice(N, int(round(FRAC * N)), replace=False))
    rows = Si[sub]
    czs, lpds, lpcs, Cadm = cz[sub], lpd[sub], lpc[sub], D["Cadm"][rows]
    X1 = D["demo"][rows]
    blocks = {"base": X1, "ECG": np.hstack([X1, D["ecg"][rows]]), "shufECG": np.hstack([X1, D["shuf"][rows]]),
              "noise32": np.hstack([X1, D["noise"][rows]]), "oracle": np.column_stack([X1, czs])}
    out = []
    for orr in sorted(set(s[0] for s in SCEN)):
        oi = sorted(set(s[0] for s in SCEN)).index(orr)
        trt = (np.random.default_rng([60_000 + rep, ti, ci, oi]).uniform(size=len(rows)) <
               expit(alpha[orr] + lpds + np.log(orr) * czs)).astype(int)
        if min(trt.sum(), (1 - trt).sum()) < 50:
            continue
        M = {"unmatched": (np.arange(len(rows)), None)}
        for a, X in blocks.items():
            idx, cl, _ = match(ps_logit(X, trt), trt)
            M[a] = (idx, cl)
        for hry in [s[1] for s in SCEN if s[0] == orr]:
            hi = HRS.index(hry) if hry in HRS else -1
            lam = lam0 / float(np.mean(np.exp(np.log(hry) * cz)))
            lp0 = lpcs + np.log(hry) * czs
            u = np.random.default_rng([70_000 + rep, ti, ci, oi, hi + 1]).uniform(size=len(rows))
            tt, ee = simulate(lp0 + np.log(TRUE_HR) * trt, lam, rho, Cadm, u)
            U = np.random.default_rng([80_000 + rep, ti, ci, oi, hi + 1]).uniform(size=(COPIES, len(rows)))
            for a, (idx, cl) in M.items():
                b, se = cox(tt[idx], ee[idx], trt[idx], cluster=cl)
                # truth in the analysed population (counterfactual, common random numbers)
                ts, es, xs = [], [], []
                for k in range(COPIES):
                    for x in (0, 1):
                        t_, e_ = simulate(lp0[idx] + np.log(TRUE_HR) * x, lam, rho, Cadm[idx], U[k, idx])
                        ts.append(t_); es.append(e_); xs.append(np.full(len(idx), x))
                tr = cox_fast(np.concatenate(ts), np.concatenate(es), np.concatenate(xs))
                out.append(dict(trial=n, conf=c, or_t=orr, hr_y=hry, rep=rep, arm=a, loghr=b, se=se, truth=tr,
                                n_an=len(idx), n_t=int(trt[idx].sum()), events=int(ee[idx].sum())))
    return out


def run(reps, workers, trials=None):
    from multiprocessing import Pool
    os.umask(0o077)
    P = pd.read_csv(OUT / "prep_conf.csv")
    P = P[P.eligible]
    if trials:
        P = P[P.trial.isin(trials)]
    info = {(r.trial, r.conf): dict(lam=r.lam, rho=r.rho, alpha=r.alpha, idx=int(r.idx)) for r in P.itertuples()}
    jobs = [(n, c, rep, info[(n, c)]) for (n, c) in info for rep in range(reps)]  # grouped by trial (cache locality)
    t0 = time.time()
    res = []
    with Pool(workers) as p:
        for k, o in enumerate(p.imap(one, jobs, chunksize=5)):
            res.extend(o)
            if k % 500 == 0:
                print(f"{k}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    R = pd.DataFrame(res)
    R.to_csv(OUT / (f"reps{SUF}.csv" if not trials else "reps_partial.csv"), index=False)
    print("done", len(R), f"{time.time() - t0:.0f}s", flush=True)


def check():
    """Fast Cox vs lifelines on simulated counterfactual data from one prepped trial; one-replicate smoke."""
    from lifelines import CoxPHFitter
    P = pd.read_csv(OUT / "prep_conf.csv")
    P = P[P.eligible].iloc[0]
    job = (P.trial, P.conf, 0, dict(lam=P.lam, rho=P.rho, alpha=P.alpha, idx=int(P.idx)))
    t0 = time.time()
    o = pd.DataFrame(one(job))
    print(f"one replicate {P.trial} {P.conf}: {time.time() - t0:.1f}s, {len(o)} rows")
    print(o.groupby(["or_t", "hr_y", "arm"]).loghr.first().unstack().round(3))
    rng = np.random.default_rng(1)
    devs = []
    for k in range(5):
        n = 3000
        x = rng.integers(0, 2, n)
        tev = rng.weibull(1.3, n) * np.exp(-0.3 * x + rng.normal(0, 0.5, n))
        C = np.where(rng.uniform(size=n) < 0.3, 0.5, 5.0)
        t, e = np.minimum(tev, C), (tev <= C).astype(int)
        b1 = cox_fast(t, e, x)
        b2 = float(CoxPHFitter().fit(pd.DataFrame(dict(t=t, e=e, x=x)), "t", "e").params_["x"])
        devs.append(abs(b1 - b2))
    print("fast Cox vs lifelines max |dev|", max(devs))


# ---------------------------------------------------------------- summaries
def _ratio_ci(a, b, reps_boot=2000, seed=0):
    """100 * (1 - mean(a)/mean(b)) and a replicate-resampling percentile CI (Monte Carlo error only)."""
    a, b = np.asarray(a), np.asarray(b)
    ok = ~np.isnan(a) & ~np.isnan(b)
    a, b = a[ok], b[ok]
    if len(a) < 10:
        return np.nan, np.nan, np.nan
    pt = 100 * (1 - a.mean() / b.mean())
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(a), (reps_boot, len(a)))
    bs = 100 * (1 - a[ix].mean(1) / b[ix].mean(1))
    return pt, *np.percentile(bs, [2.5, 97.5])


def summarize():
    os.umask(0o077)
    R = pd.read_csv(OUT / f"reps{SUF}.csv")
    P = pd.read_csv(OUT / "prep_conf.csv")
    # outcome-model calibration failure (simulated null event rate < half the real rate): excluded from every summary
    bad = P[P.eligible & (P.sim_event_rate_null < 0.5 * P.real_event_rate)][["trial", "conf"]]
    bad.to_csv(OUT / f"excluded_cells{SUF}.csv", index=False)
    print("excluded (calibration failure):", bad.to_dict("records"))
    R = R.merge(bad.assign(_x=1), on=["trial", "conf"], how="left")
    R = R[R._x.isna()].drop(columns="_x")
    R["err"] = R.loghr - R.truth
    R["cover"] = (np.abs(R.err) <= 1.96 * R.se).astype(float)
    R.loc[R.se.isna(), "cover"] = np.nan
    W = R.pivot_table(index=["trial", "conf", "or_t", "hr_y", "rep"], columns="arm", values="err")
    rows = []
    for (n, c, o, h), g in W.groupby(level=[0, 1, 2, 3]):
        rr = R[(R.trial == n) & (R.conf == c) & (R.or_t == o) & (R.hr_y == h)]
        for a in ARMS:
            ra = rr[rr.arm == a]
            r = dict(trial=n, conf=c, or_t=o, hr_y=h, arm=a, n_reps=int(ra.loghr.notna().sum()), bias=g[a].mean(),
                     mcse=g[a].std() / np.sqrt(g[a].notna().sum()), emp_sd=ra.loghr.std(), mean_se=ra.se.mean(),
                     coverage=100 * ra.cover.mean(), truth=ra.truth.mean(), n_an=ra.n_an.mean(), events=ra.events.mean())
            if o != 1.0:
                r["pct_removed_vs_unm"], r["pru_lo"], r["pru_hi"] = _ratio_ci(g[a], g["unmatched"])
                r["pct_removed_vs_base"], r["prb_lo"], r["prb_hi"] = _ratio_ci(g[a], g["base"])
            rows.append(r)
    S = pd.DataFrame(rows).merge(P[["trial", "conf", "r2_ecg", "r2_demo", "r2_demo_ecg", "r2_partial", "r2_shuf", "r2_noise"]],
                                 on=["trial", "conf"], how="left")
    S.to_csv(OUT / f"summary_by_trial{SUF}.csv", index=False)
    # pooled across trials (mean of per-trial biases; trials weighted equally), per confounder and overall
    pool = []
    for keys, g in S.groupby(["conf", "or_t", "hr_y", "arm"]):
        pool.append(dict(zip(["conf", "or_t", "hr_y", "arm"], keys), n_trials=g.trial.nunique(), bias=g.bias.mean(),
                         coverage=g.coverage.mean(), med_prb=g.pct_removed_vs_base.median(), med_pru=g.pct_removed_vs_unm.median()))
    for keys, g in S.groupby(["or_t", "hr_y", "arm"]):
        pool.append(dict(zip(["or_t", "hr_y", "arm"], keys), conf="all", n_trials=len(g), bias=g.bias.mean(),
                         coverage=g.coverage.mean(), med_prb=g.pct_removed_vs_base.median(), med_pru=g.pct_removed_vs_unm.median()))
    Pm = pd.DataFrame(pool)
    # pooled % removed = 1 - sum of biases / sum of base biases (ratio of mean biases over trial x confounder cells)
    b = S.pivot_table(index=["trial", "conf", "or_t", "hr_y"], columns="arm", values="bias").reset_index()
    for a in ARMS:
        for ref in ("base", "unmatched"):
            col = f"pooled_pct_vs_{ref}"
            for keys, g in list(b.groupby(["conf", "or_t", "hr_y"])) + [((("all",) + k), g) for k, g in b.groupby(["or_t", "hr_y"])]:
                if keys[1] == 1.0:
                    continue
                m = (Pm.conf == keys[0]) & (Pm.or_t == keys[1]) & (Pm.hr_y == keys[2]) & (Pm.arm == a)
                Pm.loc[m, col] = 100 * (1 - g[a].sum() / g[ref].sum())
    Pm.to_csv(OUT / f"summary_pooled{SUF}.csv", index=False)
    # relationship: per trial x confounder, % removed by +ECG vs base (pooled over the 9 grid cells as a ratio of summed
    # biases) against R²; weighted least squares slope (weights = base bias) and Spearman
    rel = []
    Rg = W.reset_index()
    Rg = Rg[Rg.or_t != 1.0]
    for (n, c), g in Rg.groupby(["trial", "conf"]):
        r = dict(trial=n, conf=c)
        for a in ("ECG", "shufECG", "noise32", "oracle"):
            # per-replicate grid-summed error: sum over the 9 cells of rep-matched errors (cells share rep index)
            ga = g.groupby("rep")[[a, "base", "unmatched"]].sum()
            r[f"prb_{a}"], r[f"prb_{a}_lo"], r[f"prb_{a}_hi"] = _ratio_ci(ga[a], ga["base"])
            r[f"pru_{a}"] = _ratio_ci(ga[a], ga["unmatched"])[0]
        r["base_bias_grid_mean"] = g["base"].mean()
        r["base_bias_strong"] = g[(g.or_t == 2.0) & (g.hr_y == 2.0)]["base"].mean()
        r["prb_ECG_strong"] = _ratio_ci(g[(g.or_t == 2.0) & (g.hr_y == 2.0)]["ECG"], g[(g.or_t == 2.0) & (g.hr_y == 2.0)]["base"])[0]
        rel.append(r)
    Rl = pd.DataFrame(rel).merge(P[["trial", "conf", "n_obs", "r2_ecg", "r2_demo", "r2_partial", "r2_shuf"]], on=["trial", "conf"])
    Rl.to_csv(OUT / f"relationship{SUF}.csv", index=False)
    from scipy.stats import spearmanr
    fits = []
    for c in list(CONF) + ["all"]:
        g = Rl if c == "all" else Rl[Rl.conf == c]
        if len(g) < 3:
            continue
        for xv in ("r2_partial", "r2_ecg"):
            x, y = g[xv].to_numpy(), g.prb_ECG.to_numpy()
            ok = np.isfinite(x) & np.isfinite(y)
            rs, p = spearmanr(x[ok], y[ok])
            w = g.base_bias_grid_mean.clip(lower=1e-6).to_numpy()[ok]
            # WLS of y on x (with intercept) and through the origin
            Xd = np.column_stack([np.ones(ok.sum()), x[ok]])
            coef = np.linalg.lstsq(Xd * np.sqrt(w)[:, None], y[ok] * np.sqrt(w), rcond=None)[0]
            slope0 = float(np.sum(w * x[ok] * y[ok]) / np.sum(w * x[ok] ** 2))
            fits.append(dict(conf=c, x=xv, k=int(ok.sum()), spearman=rs, p=p, wls_intercept=coef[0], wls_slope=coef[1],
                             slope_origin=slope0, mean_x=x[ok].mean(), mean_prb=np.average(y[ok], weights=w),
                             median_prb=np.median(y[ok])))
    F = pd.DataFrame(fits)
    F.to_csv(OUT / f"relationship_fits{SUF}.csv", index=False)
    print(F.round(3).to_string())
    # sensitivity (post hoc): (i) null-corrected excess bias = err(cell) - err(null cell, same trial x C x replicate; the
    # replicate shares the subsample rows), removing each arm's non-C (design) bias; (ii) leave LODESTAR out (its P1 base
    # arm is biased under the null); pooled % of base bias removed over the 9-cell grid
    Wr = W.reset_index()
    nul = Wr[Wr.or_t == 1.0].drop(columns=["or_t", "hr_y"]).set_index(["trial", "conf", "rep"])
    ex = Wr[Wr.or_t != 1.0].set_index(["trial", "conf", "rep"])
    exc = ex[ARMS] - nul.reindex(ex.index)[ARMS]
    exc[["or_t", "hr_y"]] = ex[["or_t", "hr_y"]]
    exc = exc.reset_index()
    sens = []
    for lab, data, drop in (("raw", Wr[Wr.or_t != 1.0], False), ("null-corrected", exc, False), ("raw, no LODESTAR", Wr[Wr.or_t != 1.0], True),
                            ("null-corrected, no LODESTAR", exc, True)):
        d = data[data.trial != "lodestar"] if drop else data
        cb = d.groupby(["trial", "conf", "or_t", "hr_y"])[ARMS].mean().reset_index()
        for c in list(CONF) + ["all"]:
            g = cb if c == "all" else cb[cb.conf == c]
            r = dict(analysis=lab, conf=c, k=len(g[["trial", "conf"]].drop_duplicates()), bias_base=g.base.mean())
            for a in ARMS:
                r[f"%rm_{a}"] = 100 * (1 - g[a].sum() / g.base.sum())
            sens.append(r)
        # per trial x C relationship on this version
        if lab == "null-corrected":
            per = []
            for (n, c), g in d.groupby(["trial", "conf"]):
                ga = g.groupby("rep")[["ECG", "base"]].sum()
                per.append(dict(trial=n, conf=c, prb_ECG_nc=_ratio_ci(ga.ECG, ga.base)[0], base_excess=g.base.mean()))
            Pn = pd.DataFrame(per).merge(Rl[["trial", "conf", "r2_partial"]], on=["trial", "conf"])
            Pn.to_csv(OUT / f"relationship_nullcorr{SUF}.csv", index=False)
            rs, p = spearmanr(Pn.r2_partial, Pn.prb_ECG_nc)
            w = Pn.base_excess.clip(lower=1e-6)
            sens.append(dict(analysis="null-corrected: per-cell % removed by ECG vs partial R²", conf="all", k=len(Pn), spearman=rs,
                             spearman_p=p, slope_origin=float(np.sum(w * Pn.r2_partial * Pn.prb_ECG_nc) / np.sum(w * Pn.r2_partial ** 2))))
    Sn = pd.DataFrame(sens)
    Sn.to_csv(OUT / f"sensitivity{SUF}.csv", index=False)
    print(Sn.round(3).to_string())
    print(Pm[(Pm.conf == "all")].round(3).to_string())


def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    Pm = pd.read_csv(OUT / f"summary_pooled{SUF}.csv")
    Rl = pd.read_csv(OUT / f"relationship{SUF}.csv")
    DOCS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(13, 4.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.35], wspace=0.38)
    for j, (arm, ttl) in enumerate((("base", "a  Bias after P1 base matching (log HR)"),
                                     ("ECG", "b  % of base bias removed by +ECG32"))):
        ax = fig.add_subplot(gs[0, j])
        g = Pm[(Pm.conf == "all") & (Pm.arm == arm) & (Pm.or_t != 1.0)]
        val = "bias" if arm == "base" else "pooled_pct_vs_base"
        M = g.pivot(index="or_t", columns="hr_y", values=val).reindex(index=ORS[::-1], columns=HRS)
        cmap = "Oranges" if arm == "base" else "Blues"
        vmax = np.nanmax(M.values) if arm == "base" else 100
        im = ax.imshow(M.values, cmap=cmap, vmin=0, vmax=vmax, aspect="auto")
        for (a, b), v in np.ndenumerate(M.values):
            ax.text(b, a, f"{v:.3f}" if arm == "base" else f"{v:.0f}%", ha="center", va="center",
                    color="white" if v > 0.6 * vmax else "#222", fontsize=9)
        ax.set_xticks(range(3)); ax.set_xticklabels([f"{h:g}" for h in HRS])
        ax.set_yticks(range(3)); ax.set_yticklabels([f"{o:g}" for o in ORS[::-1]])
        ax.set_xlabel("C effect on outcome (HR per SD)"); ax.set_ylabel("C effect on treatment (OR per SD)")
        ax.set_title(ttl, loc="left", fontsize=9.5)
        for s in ax.spines.values():
            s.set_visible(False)
    ax = fig.add_subplot(gs[0, 2])
    cols = {"lvef": "#2a6fdb", "ntprobnp": "#d1495b", "bmi": "#2e933c", "egfr": "#8d6cab"}
    lo_, hi_ = -80, 100
    for c, col in cols.items():
        g = Rl[Rl.conf == c]
        if len(g):
            y = g.prb_ECG.clip(lo_, hi_)
            inr = g.prb_ECG.between(lo_, hi_)
            ax.errorbar(g.r2_partial[inr], y[inr], yerr=[(g.prb_ECG - g.prb_ECG_lo)[inr], (g.prb_ECG_hi - g.prb_ECG)[inr]], fmt="o",
                        ms=4.5, color=col, ecolor=col, elinewidth=0.5, alpha=0.85, label=f"{CONF[c][4]} (k={len(g)})")
            if (~inr).any():
                ax.scatter(g.r2_partial[~inr], y[~inr], marker="v", s=28, color=col, alpha=0.85)
    ax.scatter(Rl.r2_shuf.clip(lower=-0.02), Rl.prb_shufECG.clip(lo_, hi_), marker="x", s=12, color="#999",
               label="+shufECG32 placebo (x = its own R²)")
    orc = float(100 * (1 - Rl.prb_oracle.median() / 100)) if False else float(Rl.prb_oracle.median())
    ax.axhline(orc, color="#e0a800", lw=0.9, ls=":", label=f"oracle (base + C), median {orc:.0f}%")
    xx = np.linspace(0, max(0.05, float(np.nanmax(Rl.r2_partial)) * 1.1), 50)
    ax.plot(xx, 100 * xx, color="#444", lw=0.9, ls="--", label="y = 100 × R² (linear-proxy expectation)")
    ax.axhline(0, color="#bbb", lw=0.7)
    ax.set_ylim(lo_ - 5, hi_ + 5)
    ax.set_xlabel("Cross-fitted partial R² of ECG32 for C given demographics (real data)")
    ax.set_ylabel("% of base bias removed by +ECG32 (9-cell grid)")
    ax.set_title("c  Bias removed vs how well the ECG predicts C", loc="left", fontsize=9.5)
    ax.legend(fontsize=6.8, frameon=False, loc="lower right", ncol=1)
    ax.text(0.01, 0.01, "▼ = outside axis range (base bias ≈ 0)", transform=ax.transAxes, fontsize=6.5, color="#666")
    fig.savefig(DOCS / f"G2_bias_vs_R2{SUF}.png", dpi=170, bbox_inches="tight")
    print("figure written")


def report():
    """Tables for docs/v19/G2_SIMULATION.md (the prose verdict is written by hand above the generated block)."""
    from v13_summarize import md
    P = suppress(pd.read_csv(OUT / "prep_conf.csv"))
    M = pd.read_csv(OUT / "prep_meta.csv")
    S = pd.read_csv(OUT / f"summary_by_trial{SUF}.csv")
    Pm = pd.read_csv(OUT / f"summary_pooled{SUF}.csv")
    Rl = pd.read_csv(OUT / f"relationship{SUF}.csv")
    F = pd.read_csv(OUT / f"relationship_fits{SUF}.csv")
    L = []
    L.append("## A. Audit checks\n")
    L.append(f"* Engine reproduction (P1 base, full cohort, 1:1 caliper 0.2) vs `claude-v17-confirm/results_all.csv` and "
             f"`claude-v18-af-confirm/results_af5.csv`: {int((M.repro_absdev < 1e-8).sum())}/{len(M)} trials identical "
             f"(max |Δlog HR| {M.repro_absdev.max():.1e}).")
    nul = Pm[(Pm.conf == "all") & (Pm.or_t == 1.0)].set_index("arm")
    L.append("* Null scenario (OR_T = 1, HR_Y = 1: treatment depends on demographics only), mean bias across trial × confounder "
             "cells: " + ", ".join(f"{a} {nul.loc[a, 'bias']:+.3f} (coverage {nul.loc[a, 'coverage']:.0f}%)" for a in ARMS) + ".")
    L.append("\n## B. Pooled over all trial × confounder cells (equal weight per cell)\n")
    L.append("bias = mean(log HR − truth); pooled % removed = 100 × (1 − Σ bias_arm / Σ bias_ref) over cells; median % = median of "
             "per-cell ratios; coverage = mean over cells of the 95% CI coverage of the replicate truth.\n")
    g = Pm[Pm.conf == "all"].copy()
    g["cell"] = g.or_t.map("{:g}".format) + " / " + g.hr_y.map("{:g}".format)
    for val, lab in (("bias", "Bias (log HR)"), ("pooled_pct_vs_base", "% of base bias removed (pooled)"),
                     ("pooled_pct_vs_unmatched", "% of unmatched bias removed (pooled)"), ("coverage", "Coverage of 95% CI (%)")):
        t = g.pivot_table(index="cell", columns="arm", values=val, sort=False)[ARMS].reset_index()
        t = t.rename(columns={"cell": "OR_T / HR_Y"})
        L.append(f"**{lab}**\n\n" + md(t, 1 if val != "bias" else 3) + "\n")
    L.append("## C. By confounder (pooled over the 9 non-null grid cells; % = pooled ratio of summed biases)\n")
    rows = []
    b = S[S.or_t != 1.0].pivot_table(index=["trial", "conf", "or_t", "hr_y"], columns="arm", values="bias").reset_index()
    cv = S[S.or_t != 1.0].pivot_table(index=["trial", "conf", "or_t", "hr_y"], columns="arm", values="coverage").reset_index()
    for c in list(CONF) + ["all"]:
        gb = b if c == "all" else b[b.conf == c]
        gc = cv if c == "all" else cv[cv.conf == c]
        gr = Rl if c == "all" else Rl[Rl.conf == c]
        if not len(gb):
            continue
        r = dict(confounder=CONF[c][4] if c != "all" else "all", k_trials=gb.trial.nunique(),
                 mean_r2_ecg=gr.r2_ecg.mean(), mean_partial_r2=gr.r2_partial.mean(), bias_unm=gb.unmatched.mean(), bias_base=gb.base.mean())
        for a in ("ECG", "shufECG", "noise32", "oracle"):
            r[f"%rm_{a}"] = 100 * (1 - gb[a].sum() / gb.base.sum())
        r["%rm_ECG_vs_unm"] = 100 * (1 - gb.ECG.sum() / gb.unmatched.sum())
        r["cov_base"], r["cov_ECG"], r["cov_oracle"] = gc.base.mean(), gc.ECG.mean(), gc.oracle.mean()
        rows.append(r)
    L.append(md(pd.DataFrame(rows), 3) + "\n")
    L.append("## D. % bias removed by +ECG32 vs the ECG's real-data R² for C (one point per trial × confounder)\n")
    L.append("y = % of base bias removed by +ECG32 (ratio of grid-summed biases); x = cross-fitted R² (r2_ecg: ECG32 alone; "
             "r2_partial: ECG32 given demographics). WLS weights = mean base bias; slope_origin = WLS slope through 0 "
             "(1.0 = removes 100 × R² %).\n")
    L.append(md(F, 3) + "\n")
    L.append("## E. Every simulated trial × confounder cell\n")
    L.append("prb_* = % of base bias removed (9-cell grid; 95% replicate-resampling interval = Monte Carlo error only); "
             "pru_ECG = % of unmatched bias removed; *_strong = OR_T 2 / HR_Y 2 cell.\n")
    e = Rl[["trial", "conf", "n_obs", "r2_ecg", "r2_partial", "r2_shuf", "base_bias_grid_mean", "prb_ECG", "prb_ECG_lo", "prb_ECG_hi",
            "prb_shufECG", "prb_noise32", "prb_oracle", "pru_ECG", "base_bias_strong", "prb_ECG_strong"]]
    L.append(md(suppress(e), 2) + "\n")
    L.append("## F. Real-data R² of the ECG for each confounder, all 38 trials × 4 confounders (incl. skipped cells)\n")
    L.append("Cross-fitted (5-fold) ridge R² in patients with C observed (and a usable outcome); n_obs_t / n_obs_c = real arms. "
             "eligible = both real arms ≥ 300 (simulated). smd_real = real-data standardised difference in C (treated − control).\n")
    f = P[["trial", "conf", "n_obs_t", "n_obs_c", "eligible", "r2_ecg", "r2_demo", "r2_demo_ecg", "r2_partial", "r2_shuf", "r2_noise", "smd_real"]]
    L.append(md(f, 3) + "\n")
    agg = P.groupby("conf")[["r2_ecg", "r2_partial", "r2_shuf", "r2_noise"]].agg(["median", "min", "max"]).round(3)
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    L.append("Summary by confounder (all 38 trials):\n\n" + md(agg.reset_index(), 3) + "\n")
    (OUT / f"report_tables{SUF}.md").write_text("\n".join(L))
    print("tables written", OUT / f"report_tables{SUF}.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["prep", "check", "run", "summarize", "figure", "report"])
    ap.add_argument("--trials", default=None)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--reps", type=int, default=50)
    a = ap.parse_args()
    os.umask(0o077)
    if a.cmd == "prep":
        prep(a.trials.split(",") if a.trials else trial_list()[0], a.workers)
    elif a.cmd == "check":
        check()
    elif a.cmd == "run":
        run(a.reps, a.workers, a.trials.split(",") if a.trials else None)
    elif a.cmd == "summarize":
        summarize()
    elif a.cmd == "figure":
        figure()
    else:
        report()


if __name__ == "__main__":
    main()
