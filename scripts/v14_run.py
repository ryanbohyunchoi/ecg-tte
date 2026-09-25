#!/usr/bin/env python
"""v1.4 engine (docs/PROTOCOL_V1_4_AMENDMENT.md). One trial, one or more modes:
  strata   A (code-density tertiles) and C (echo / no echo among index >= 2016-07-31): real-data paired
           bootstrap and resampled plasmode within each stratum
  dropout  B: codes deleted with p in {0.5, 0.75, 0.9}; bootstrap + plasmode (outcomes from true covariates)
  echo     D: plasmode in the echo subcohort, outcome model includes measured echo physiology
  hf       E: HF hospitalisation outcome; bootstrap (target R+) + plasmode fitted on that outcome
Aggregate CSVs only (per-replicate log HRs, truths).
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

from trial_specs import COD_END, DEATH_END, HORIZON_MONTHS, OUTCOMES  # noqa: E402
from v13_common import A, Trial, cox, match, outcomes, ps_logit  # noqa: E402

ARMS = ["sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "R+"]
STD_SCEN = {"base": dict(phys=1.0, medutil=1.0, echo=0.0), "phys_only": dict(phys=1.0, medutil=0.0, echo=0.0)}
ECHO_SCEN = {"echo_base": dict(phys=1.0, medutil=1.0, echo=1.0), "echo_strong": dict(phys=1.0, medutil=1.0, echo=2.0),
             "echo_only": dict(phys=0.0, medutil=0.0, echo=1.0)}
HR_TRUE = 0.8
G = {}


# ---------------------------------------------------------------- outcome model / simulation
def outcome_model(T, t, e, rows, extra=None):
    """Cox on standardised core (+ extra) covariates in `rows`; returns (Z over all patients, beta, lam, rho, groups)."""
    X = T.X_core.copy()
    names = list(T.core)
    if extra is not None:
        X = np.hstack([X, extra])
        names += [f"echo_{i}" for i in range(extra.shape[1])]
    mu, sd = X[rows].mean(0), X[rows].std(0)
    var = sd > 0
    Z = np.zeros_like(X)
    Z[:, var] = (X[:, var] - mu[var]) / sd[var]
    d = pd.DataFrame(Z[rows][:, var], columns=[n for n, v in zip(names, var) if v])
    d["treated"], d["t"], d["e"] = T.t[rows], t[rows], e[rows]
    cph = CoxPHFitter(penalizer=0.01).fit(d, "t", "e")
    beta = cph.params_.reindex(names).fillna(0.0).to_numpy()
    bh = cph.baseline_cumulative_hazard_
    tb, Hb = bh.index.to_numpy(float), bh.iloc[:, 0].to_numpy(float)
    m = (tb > 0) & (Hb > 0)
    rho, loglam = np.polyfit(np.log(tb[m]), np.log(Hb[m]), 1)
    lam = float(np.exp(loglam) * np.exp(-cph.params_["treated"] * d.treated.mean()))
    grp = np.array(["phys" if n in T.phys else "medutil" if n in T.meds + T.util else "echo" if n.startswith("echo_") else "other"
                    for n in names])
    return Z, beta, lam, float(rho), grp


def lp_for(Z, beta, grp, cfg):
    k = np.ones(len(beta))
    for g in ("phys", "medutil", "echo"):
        k[grp == g] = cfg[g]
    return Z @ (beta * k)


def simulate(lp, lam, rho, C, rng):
    tev = (-np.log(rng.uniform(size=len(lp))) / (lam * np.exp(lp))) ** (1 / rho)
    return np.minimum(tev, C), (tev <= C).astype(int)


def truth(lp0, lam, rho, C, copies=20):
    rng = np.random.default_rng(99)
    ts, es, xs = [], [], []
    for _ in range(copies):
        u = rng.uniform(size=len(lp0))
        for x in (0, 1):
            tev = (-np.log(u) / (lam * np.exp(lp0 + np.log(HR_TRUE) * x))) ** (1 / rho)
            ts.append(np.minimum(tev, C)); es.append((tev <= C).astype(int)); xs.append(np.full(len(lp0), x))
    d = pd.DataFrame({"t": np.concatenate(ts), "e": np.concatenate(es), "x": np.concatenate(xs)})
    return float(CoxPHFitter().fit(d, "t", "e").params_["x"])


# ---------------------------------------------------------------- workers
def _pl_rep(rep):
    Tm, pool, lps, lam, rho, C = G["Tm"], G["pool"], G["lps"], G["lam"], G["rho"], G["C"]
    r0 = np.random.default_rng(50_000 + rep)
    fr = G.get("subsample")
    rows = pool[np.sort(r0.choice(len(pool), int(round(fr * len(pool))), replace=False))] if fr else pool[r0.integers(0, len(pool), len(pool))]
    trt = Tm.t[rows]
    X = Tm.arms(ARMS, rows=rows)
    M = {a: match(ps_logit(X[a], trt), trt)[:2] for a in ARMS}
    out = []
    for j, (sc, lp0) in enumerate(lps.items()):
        rng = np.random.default_rng(7_000_000 + 1_000_000 * j + rep)
        tt, ee = simulate(lp0[rows] + np.log(HR_TRUE) * trt, lam, rho, C[rows], rng)
        for a, (idx, cl) in M.items():
            b, se = cox(tt[idx], ee[idx], trt[idx], cluster=cl)
            out.append(dict(scenario=sc, rep=rep, arm=a, loghr=b, se=se))
    return out


def _bs_rep(rep):
    Tm, pool, t, e, ok = G["Tm"], G["pool"], G["t"], G["e"], G["ok"]
    rows = pool if rep == 0 else pool[np.random.default_rng(10_000 + rep).integers(0, len(pool), len(pool))]
    trt = Tm.t[rows]
    X = Tm.arms(ARMS, rows=rows)
    out = []
    for a in ARMS:
        idx, cl, _ = match(ps_logit(X[a], trt), trt)
        m = ok[rows][idx]
        b, se = cox(t[rows][idx][m], e[rows][idx][m], trt[idx][m], cluster=cl[m])
        out.append(dict(rep=rep, arm=a, loghr=b, se=se, pairs=len(idx) // 2))
    return out


def run_plasmode(Tm, pool, lps, lam, rho, C, reps, workers):
    X = Tm.arms(ARMS, rows=pool)
    tr = []
    for a in ARMS:
        idx, _, _ = match(ps_logit(X[a], Tm.t[pool]), Tm.t[pool])
        rr = pool[idx]
        for sc, lp0 in lps.items():
            tr.append(dict(scenario=sc, arm=a, truth_loghr=truth(lp0[rr], lam, rho, C[rr])))
    G.update(Tm=Tm, pool=pool, lps=lps, lam=lam, rho=rho, C=C)
    with Pool(workers) as p:
        res = [r for rr in p.imap_unordered(_pl_rep, range(reps)) for r in rr]
    return pd.DataFrame(res), pd.DataFrame(tr)


def run_boot(Tm, pool, t, e, ok, reps, workers):
    G.update(Tm=Tm, pool=pool, t=t, e=e, ok=ok)
    with Pool(workers) as p:
        return pd.DataFrame([r for rr in p.imap_unordered(_bs_rep, range(reps + 1)) for r in rr])


def admin_C(T, H, uses_cause):
    end = pd.Timestamp(COD_END if uses_cause else DEATH_END)
    return np.minimum(H, (end - T.index_date).dt.days.to_numpy(float)).clip(min=1)


def feasible(T, pool, min_arm=100):
    tt = T.t[pool]
    return min((tt == 1).sum(), (tt == 0).sum()) >= min_arm


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--modes", default="strata,dropout,echo,hf")
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--subsample", type=float, default=None, help="plasmode: subsample fraction without replacement (audit fix)")
    a = ap.parse_args()
    O = a.output_dir
    G["subsample"] = a.subsample
    T = Trial(a.trial)
    t, e, ok, H, _ = outcomes(a.trial, T.key, T.keys)
    uses_cause = any(c in ("cv_death", "chd_death") for c in OUTCOMES[T.key])
    C = admin_C(T, H, uses_cause)
    everyone = np.arange(len(T.t))
    meta = dict(trial=a.trial, n=len(T.t), pools={})
    Z, beta, lam, rho, grp = outcome_model(T, t, e, np.where(ok)[0])
    std_lps = {sc: lp_for(Z, beta, grp, cfg) for sc, cfg in STD_SCEN.items()}

    def save(df, name, **cols):
        for k, v in cols.items():
            df.insert(0, k, v)
        df.insert(0, "trial", a.trial)
        f = f"{O}/{name}_{a.trial}_{cols['mode']}.csv"
        df.to_csv(f, mode="a", header=not os.path.exists(f), index=False)

    for mode in a.modes.split(","):
        if mode == "strata":
            q1, q2 = np.quantile(T.density, [1 / 3, 2 / 3])
            pools = {"density_low": everyone[T.density <= q1], "density_mid": everyone[(T.density > q1) & (T.density <= q2)],
                     "density_high": everyone[T.density > q2],
                     "echo_yes": everyone[T.post2016 & T.echo_any], "echo_no": everyone[T.post2016 & ~T.echo_any]}
            for pn, pool in pools.items():
                meta["pools"][pn] = dict(n=int(len(pool)), feasible=bool(feasible(T, pool)))
                if not feasible(T, pool):
                    continue
                save(run_boot(T, pool, t, e, ok, a.reps, a.workers), "boot", mode=mode, pool=pn)
                R, Tr = run_plasmode(T, pool, std_lps, lam, rho, C, a.reps, a.workers)
                save(R, "plasmode", mode=mode, pool=pn)
                save(Tr, "truth", mode=mode, pool=pn)
        elif mode == "dropout":
            for pdrop in (0.5, 0.75, 0.9):
                D = T.degraded(pdrop)
                pn = f"dropout_{pdrop}"
                save(run_boot(D, everyone, t, e, ok, a.reps, a.workers), "boot", mode=mode, pool=pn)
                R, Tr = run_plasmode(D, everyone, std_lps, lam, rho, C, a.reps, a.workers)
                save(R, "plasmode", mode=mode, pool=pn)
                save(Tr, "truth", mode=mode, pool=pn)
        elif mode == "dropout_pl":  # audit fix: dropout plasmode only (use with --subsample)
            for pdrop in (0.0, 0.5, 0.75, 0.9):
                D = T.degraded(pdrop) if pdrop > 0 else T
                pn = f"dropout_{pdrop}"
                R, Tr = run_plasmode(D, everyone, std_lps, lam, rho, C, a.reps, a.workers)
                save(R, "plasmode", mode=mode, pool=pn)
                save(Tr, "truth", mode=mode, pool=pn)
        elif mode == "echo":
            pool = everyone[T.post2016 & T.echo_lv & ok]
            meta["pools"]["echo_subcohort"] = dict(n=int(len(pool)), feasible=bool(feasible(T, pool)))
            if feasible(T, pool):
                E = T.PP_echo.to_numpy(float)
                keep = np.isfinite(E[pool]).mean(0) >= 0.2
                E = E[:, keep]
                med = np.nanmedian(E[pool], axis=0)
                E = np.where(np.isfinite(E), E, med)
                Ze, be, lam_e, rho_e, grp_e = outcome_model(T, t, e, pool, extra=E)
                lps = {sc: lp_for(Ze, be, grp_e, cfg) for sc, cfg in ECHO_SCEN.items()}
                meta["echo_measures_used"] = int(keep.sum())
                R, Tr = run_plasmode(T, pool, lps, lam_e, rho_e, C, a.reps, a.workers)
                save(R, "plasmode", mode=mode, pool="echo_subcohort")
                save(Tr, "truth", mode=mode, pool="echo_subcohort")
        elif mode == "hf":
            Hf = pd.read_parquet(f"{A}/claude-{a.trial}-hf-v14/restricted_hf_outcome.parquet").set_index("patient_key").reindex(T.keys)
            okh = (Hf.t_hf.notna() & (Hf.exclude == 0)).to_numpy()
            th = np.minimum(Hf.t_hf.to_numpy(float), H)
            eh = ((Hf.e_hf == 1) & (Hf.t_hf <= H)).to_numpy(int)
            meta["hf_events"] = int(eh[okh].sum()) if eh[okh].sum() >= 11 else "<11"
            if eh[okh].sum() < 50:
                continue
            save(run_boot(T, everyone, th, eh, okh, a.reps, a.workers), "boot", mode=mode, pool="hf_outcome")
            Zh, bh_, lam_h, rho_h, grp_h = outcome_model(T, th, eh, np.where(okh)[0])
            lps = {sc: lp_for(Zh, bh_, grp_h, cfg) for sc, cfg in STD_SCEN.items()}
            Ch = np.minimum(H, (pd.Timestamp(DEATH_END) - T.index_date).dt.days.to_numpy(float)).clip(min=1)
            R, Tr = run_plasmode(T, everyone, lps, lam_h, rho_h, Ch, a.reps, a.workers)
            save(R, "plasmode", mode=mode, pool="hf_outcome")
            save(Tr, "truth", mode=mode, pool="hf_outcome")
    json.dump(meta, open(f"{O}/meta_{a.trial}_{a.modes.replace(',', '-')}.json", "w"), indent=2, default=str)
    print(json.dumps(meta, default=str))


if __name__ == "__main__":
    main()
