#!/usr/bin/env python
"""v1.3 I1: plasmode simulation (docs/PROTOCOL_V1_3_AMENDMENT.md).

Real cohort, real covariates and real treatment assignment (imputation 1). Outcome model: Cox of the
real primary outcome (trial horizon) on treatment + standardised clinical core covariates (ridge 0.01);
baseline cumulative hazard smoothed by a Weibull fit (log H0 on log t), so simulated times are
continuous. Scenario linear predictor: log(HR_true) * T + sum_j kappa_j * beta_j * x_j, with kappa = the
physiology multiplier for core-9 covariates (1 otherwise; 0 for medications/utilisation in
"phys_only"). Censoring: administrative (trial horizon, end of data).

Per arm, the matched set is fixed (it does not depend on the outcome). Truth per arm = marginal log HR
in that arm's matched population from counterfactual outcomes under both treatments (5 copies).
Output (aggregate): per-replicate log HR and SE per arm and scenario, and the truths.
"""
import os

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
from multiprocessing import Pool  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from lifelines import CoxPHFitter  # noqa: E402

from trial_specs import COD_END, DEATH_END, OUTCOMES  # noqa: E402
from v13_common import Trial, cox, match, outcomes, ps_logit  # noqa: E402

ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "R+",
        "sparse+noise32", "sparse+shufECG", "hdPS200+noise32", "hdPS200+shufECG"]
SCEN = {"base": dict(kappa=1.0, hr=0.8, phys_only=False), "none": dict(kappa=0.0, hr=0.8, phys_only=False),
        "strong": dict(kappa=2.0, hr=0.8, phys_only=False), "null": dict(kappa=1.0, hr=1.0, phys_only=False),
        "phys_only": dict(kappa=1.0, hr=0.8, phys_only=True)}
G = {}


def simulate(lp, lam, rho, C, rng):
    u = rng.uniform(size=len(lp))
    tev = (-np.log(u) / (lam * np.exp(lp))) ** (1 / rho)
    return np.minimum(tev, C), (tev <= C).astype(int)


def one(job):
    scen, rep = job
    lp0, trt, lam, rho, C, M = G["lp0"][scen], G["T"].t, G["lam"], G["rho"], G["C"], G["M"]
    rng = np.random.default_rng(1_000_000 * list(SCEN).index(scen) + rep)
    lp = lp0 + np.log(SCEN[scen]["hr"]) * trt
    tt, ee = simulate(lp, lam, rho, C, rng)
    out = []
    for a, (idx, cl) in M.items():
        if idx is None:
            b, se = cox(tt, ee, trt)
        else:
            b, se = cox(tt[idx], ee[idx], trt[idx], cluster=cl)
        out.append(dict(scenario=scen, rep=rep, arm=a, loghr=b, se=se))
    return out


def truth(scen, idx, copies=20):
    """Marginal log HR in the population `idx` from counterfactual outcomes under both treatments
    (common random numbers across the two treatments)."""
    lp0, lam, rho, C = G["lp0"][scen], G["lam"], G["rho"], G["C"]
    sel = np.arange(len(lp0)) if idx is None else idx
    rng = np.random.default_rng(99)
    b = np.log(SCEN[scen]["hr"])
    ts, es, xs = [], [], []
    for _ in range(copies):
        u = rng.uniform(size=len(sel))
        for x in (0, 1):
            tev = (-np.log(u) / (lam * np.exp(lp0[sel] + b * x))) ** (1 / rho)
            ts.append(np.minimum(tev, C[sel])); es.append((tev <= C[sel]).astype(int)); xs.append(np.full(len(sel), x))
    d = pd.DataFrame({"t": np.concatenate(ts), "e": np.concatenate(es), "x": np.concatenate(xs)})
    return float(CoxPHFitter().fit(d, "t", "e").params_["x"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--output-dir", required=True)
    a = ap.parse_args()
    T = Trial(a.trial)
    t, e, ok, H, O = outcomes(a.trial, T.key, T.keys)
    # outcome model on patients with outcomes
    Z = (T.X_core - T.X_core.mean(0)) / np.where(T.X_core.std(0) > 0, T.X_core.std(0), 1)
    var = T.X_core[ok].std(0) > 0
    cols = [c for c, v in zip(T.core, var) if v]
    d = pd.DataFrame(Z[ok][:, var], columns=cols)
    d["treated"], d["t"], d["e"] = T.t[ok], t[ok], e[ok]
    cph = CoxPHFitter(penalizer=0.01).fit(d, "t", "e")
    beta = cph.params_.reindex(T.core).fillna(0.0).to_numpy()
    # Weibull smoothing of the Breslow baseline (lifelines baseline is at the covariate means = 0 here)
    bh = cph.baseline_cumulative_hazard_
    tb, Hb = bh.index.to_numpy(float), bh.iloc[:, 0].to_numpy(float)
    m = (tb > 0) & (Hb > 0)
    rho, loglam = np.polyfit(np.log(tb[m]), np.log(Hb[m]), 1)
    lam = float(np.exp(loglam))
    # lifelines centres covariates at their means: baseline for treated = 0 is H0 * exp(-beta_T * mean(treated))
    lam *= float(np.exp(-cph.params_["treated"] * d.treated.mean()))
    phys = np.isin(T.core, T.phys)
    medutil = np.isin(T.core, T.meds + T.util)
    lp0 = {}
    for s, cfg in SCEN.items():
        k = np.where(phys, cfg["kappa"], 1.0)
        if cfg["phys_only"]:
            k = np.where(medutil, 0.0, k)
        lp0[s] = Z @ (beta * k)
    uses_cause = any(c in ("cv_death", "chd_death") for c in OUTCOMES[T.key])
    end = pd.Timestamp(COD_END if uses_cause else DEATH_END)
    C = np.minimum(H, (end - T.index_date).dt.days.to_numpy(float)).clip(min=1)
    X = T.arms(ARMS)
    M = {}
    for arm in ARMS:
        if X[arm] is None:
            M[arm] = (None, None)
        else:
            idx, cl, _ = match(ps_logit(X[arm], T.t), T.t)
            M[arm] = (idx, cl)
    G.update(T=T, lp0=lp0, lam=lam, rho=rho, C=C, M=M)
    os.makedirs(a.output_dir, exist_ok=True)
    tr = [dict(scenario=s, arm=arm, truth_loghr=truth(s, M[arm][0]), conditional_loghr=float(np.log(SCEN[s]["hr"])))
          for s in SCEN for arm in ARMS]
    pd.DataFrame(tr).assign(trial=a.trial).to_csv(f"{a.output_dir}/truth_{a.trial}.csv", index=False)
    jobs = [(s, r) for s in SCEN for r in range(a.reps)]
    with Pool(a.workers) as p:
        res = [r for rr in p.imap_unordered(one, jobs, chunksize=4) for r in rr]
    pd.DataFrame(res).assign(trial=a.trial).to_csv(f"{a.output_dir}/reps_{a.trial}.csv", index=False)
    meta = dict(trial=a.trial, n=len(T.t), weibull_rho=round(float(rho), 3), events_real=int(e[ok].sum()),
                real_event_rate=round(float(e[ok].mean()), 4),
                sim_event_rate_base=round(float(simulate(lp0["base"] + np.log(0.8) * T.t, lam, rho, C, np.random.default_rng(7))[1].mean()), 4), phys=T.phys, n_meds_util=int(medutil.sum()))
    json.dump(meta, open(f"{a.output_dir}/meta_{a.trial}.json", "w"), indent=2)
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
