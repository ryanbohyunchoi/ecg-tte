#!/usr/bin/env python
"""v2.0 UKB arm (exploratory; plan docs/v20/UKB_ANALYSIS_PLAN.md): plasmode with CMR physiology as the hidden
confounder, ECG embedding vs polygenic scores (PGS) as proxies, and descriptive held-out CMR balance.

Base populations: the v1.5 UKB prevalent-user cohorts at the imaging visit (ONTARGET, ASCOT, ALLHAT), read-only.
Confounders (Bai CMR IDPs, imaging visit, same visit as the ECG), clinical orientation:
  lvef (24103, sign -1), lvedvi (24100 / BSA 22427, +1), lvmi (24105 / BSA, +1).
Design and arms as scripts/v19/g2_simulation.py and scripts/v20/g2b_simulation_ext.py (see the plan); the UKB
event rate is rescaled to a simulated null event rate of ~20% (prespecified) except in the 'realrate' sensitivity.

Usage: ukb_cmr_plasmode.py prep | run --design main|trtC|realrate | summarize | balance | figure
Outputs (aggregates, umask 077): /mnt/raid0/rbc58/ecg-tte/audits/claude-v20-ukb-analysis/
  restricted_* files hold participant-level matrices and never leave that directory.
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
sys.path.insert(0, str(HERE.parent))
import g2_simulation as G2  # noqa: E402  (pure functions only: simulate, cox_fast, cv_r2)
from v13_common import A, cox, match, ps_logit  # noqa: E402

OUT = A / "claude-v20-ukb-analysis"
DOCS = HERE.parent.parent / "docs" / "v20"
COHORTS = ["ontarget", "ascot", "allhat"]
CMR = OUT / "restricted_cmr_i2.parquet"
PGS_DIR = Path("/mnt/raid0/rbc58/prs/prs_output/ukb")
PGS = ["af", "as", "cad", "dcm", "hcm", "hf"]
# DCM: the locally scored file is the HERMES MTAG score (PGS004862), which borrows strength from LV imaging traits that
# include UK Biobank CMR (sample overlap with our confounders). The primary set uses the non-MTAG GWAMA score
# (PGS004861), scored on the same genotypes into OUT (deviation 2 in docs/v20/UKB_ANALYSIS.md); the MTAG score is kept
# only as a diagnostic R^2 ("dcm_mtag").
PGS_FILE = {p: PGS_DIR / p / f"{p.upper()}_PRS_output.sscore" for p in PGS}
PGS_FILE["dcm"] = OUT / "restricted_DCM_PGS004861.sscore"
PGS_FILE["dcm_mtag"] = PGS_DIR / "dcm" / "DCM_PRS_output.sscore"
DATA_END = pd.Timestamp("2022-10-31")
EPOCH = pd.Timestamp("1970-01-01")
# name -> (label, valid range, clinical sign)
CONF = {"lvef": ("CMR LVEF", (10, 90), -1.0), "lvedvi": ("CMR LVEDV index", (20, 300), 1.0),
        "lvmi": ("CMR LV mass index", (15, 200), 1.0)}
SCEN = G2.SCEN
OR_ALL = sorted(set(s[0] for s in SCEN))
HRS = G2.HRS
TRUE_HR = 0.8
FRAC, COPIES, MIN_ARM, MIN_CELL = 0.8, 5, 300, 11
TARGET_EVENT = 0.20
DESIGNS = {
    "main": dict(trt_demo=True, rate="target", arms=["unmatched", "base", "ECG", "shufECG", "PGS", "PGSECG", "ECGonly",
                                                     "shufECGonly", "PGSonly", "oracle"]),
    "trtC": dict(trt_demo=False, rate="target", arms=["unmatched", "ECGonly", "shufECGonly", "PGSonly", "PGSECGonly", "oracleonly"]),
    "realrate": dict(trt_demo=True, rate="real", arms=["unmatched", "base", "ECG", "PGS", "ECGonly", "PGSonly", "oracle"],
                     cells=[("ontarget", "lvef")]),
}
LAB = {"unmatched": "Unmatched", "base": "Demographic PS", "ECG": "Demographic PS + ECG", "shufECG": "Demo + permuted ECG",
       "PGS": "Demographic PS + PGS", "PGSECG": "Demographic PS + PGS + ECG", "ECGonly": "ECG only",
       "shufECGonly": "Permuted ECG only", "PGSonly": "PGS only", "PGSECGonly": "PGS + ECG only",
       "oracle": "Demographic PS + C (oracle)", "oracleonly": "C only (oracle)"}
PANEL = {  # held-out CMR balance panel: name -> (field, index to BSA?)
    "lvef": ("24103-2.0", False), "lvedvi": ("24100-2.0", True), "lvesvi": ("24101-2.0", True), "lvsvi": ("24102-2.0", True),
    "lv_ci": ("24104-2.0", True), "lvmi": ("24105-2.0", True), "rvedvi": ("24106-2.0", True), "rvef": ("24109-2.0", False),
    "lavi_max": ("24110-2.0", True), "laef": ("24113-2.0", False), "ravi_max": ("24114-2.0", True)}
G = {}


def sup(n):
    n = int(n)
    return "<11" if 1 <= n <= 10 else n


# ---------------------------------------------------------------- inputs
def cmr_table():
    d = pd.read_parquet(CMR)
    d["eid"] = d.eid.astype(str)
    bsa = d["22427-2.0"].where(d["22427-2.0"].between(1.0, 3.0))
    out = pd.DataFrame({"eid": d.eid})
    for k, (f, idx) in PANEL.items():
        out[k] = d[f] / bsa if idx else d[f]
    return out.set_index("eid")


def pgs_table():
    cols = {}
    for p, f in PGS_FILE.items():
        s = pd.read_csv(f, sep="\t", dtype={"IID": str})
        cols[p] = s.set_index("IID")["SCORE1_AVG"]
    P = pd.DataFrame(cols)
    return (P - P.mean()) / P.std()


def load_cohort(tr):
    d = A / f"claude-v15-ukb-{tr}"
    c = pd.read_parquet(d / "cohort.parquet")
    b = pd.read_parquet(d / "baseline.parquet").set_index("pid")
    o = pd.read_parquet(d / "outcomes.parquet").set_index("pid")
    e = pd.read_parquet(d / "ecg_embedding.parquet").set_index("pid")
    roles = json.load(open(d / "roles.json"))
    rct = json.load(open(d / "rct.json"))
    c["pid"] = c.pid.astype(str)
    return c.set_index("pid"), b, o, e, roles, rct


def pcs(X, k=32):
    from sklearn.decomposition import PCA
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
    return PCA(k, random_state=0).fit_transform(Xs)


def core_matrix(b, roles):
    keep = [c for c in b.columns if c not in ("pid",)]
    X = b[keep].astype(float)
    miss = [c for c in X.columns if X[c].isna().any()]
    for c in miss:
        X[c + "_missing"] = X[c].isna().astype(float)
        X[c] = X[c].fillna(X[c].median())
    X = X.loc[:, X.std() > 0]
    return X


# ---------------------------------------------------------------- prep
def prep():
    from lifelines import CoxPHFitter
    from scipy.optimize import brentq
    from scipy.special import expit
    os.umask(0o077)
    cmr, P = cmr_table(), pgs_table()
    rows, checks = [], {}
    for ti, tr in enumerate(COHORTS):
        c, b, o, e, roles, rct = load_cohort(tr)
        ids = [i for i in c.index if i in e.index]
        E = np.vstack(e.loc[ids, "embedding"].to_numpy()).astype(float)
        pc = pcs(E, 32)
        shuf = pc[np.random.default_rng(1000 + ti).permutation(len(ids))]
        base = pd.DataFrame(index=ids)
        base["t"] = c.loc[ids, "treated"].to_numpy()
        base["y_t"] = o.loc[ids, "t"].to_numpy(float)
        base["y_e"] = o.loc[ids, "e"].to_numpy(int)
        idx_date = EPOCH + pd.to_timedelta(c.loc[ids, "index_day"].to_numpy(), unit="D")
        base["Cadm"] = np.minimum(rct["horizon_days"], (DATA_END - idx_date).days.to_numpy(float)).clip(min=1)
        demo = b.loc[ids, roles["demo"]].to_numpy(float)
        core = core_matrix(b.loc[ids], roles)
        pg = P.reindex(ids)[PGS]
        pg_mtag = P.reindex(ids)["dcm_mtag"].to_numpy(float)
        cm = cmr.reindex(ids)
        arr = dict(t=base.t.to_numpy(np.int8), y_t=base.y_t.to_numpy(), y_e=base.y_e.to_numpy(np.int8), Cadm=base.Cadm.to_numpy(),
                   demo=demo, ecg=pc, shuf=shuf, pgs=pg.to_numpy(float))
        checks[tr] = dict(n_cohort=len(c), n_ecg=len(ids), n_ecg_cmr=int(cm.lvef.notna().sum()), n_ecg_pgs=int(pg.notna().all(1).sum()),
                          n_ecg_cmr_pgs=int((cm.lvef.notna() & pg.notna().all(1)).sum()), real_event_rate=float(base.y_e.mean()))
        for ci, (k, (lab, (lo, hi), sign)) in enumerate(CONF.items()):
            v = cm[k].to_numpy(float).copy()
            v[(v < lo) | (v > hi)] = np.nan
            S = ~np.isnan(v) & pg.notna().all(1).to_numpy()
            Si = np.where(S)[0]
            nt, nc = int(base.t.to_numpy()[S].sum()), int((1 - base.t.to_numpy()[S]).sum())
            r = dict(cohort=tr, conf=k, ti=ti, ci=ci, n_obs=int(S.sum()), n_obs_t=nt, n_obs_c=nc, eligible=bool(min(nt, nc) >= MIN_ARM))
            yz = (v[Si] - v[Si].mean()) / v[Si].std()
            X1, Ec, Pg = demo[Si], pc[Si], arr["pgs"][Si]
            r.update(r2_ecg=G2.cv_r2(Ec, yz), r2_pgs=G2.cv_r2(Pg, yz), r2_pgs_ecg=G2.cv_r2(np.hstack([Pg, Ec]), yz),
                     r2_demo=G2.cv_r2(X1, yz), r2_demo_ecg=G2.cv_r2(np.hstack([X1, Ec]), yz),
                     r2_demo_pgs=G2.cv_r2(np.hstack([X1, Pg]), yz), r2_shuf=G2.cv_r2(shuf[Si], yz))
            r["r2_partial_ecg"] = (r["r2_demo_ecg"] - r["r2_demo"]) / (1 - r["r2_demo"])
            r["r2_partial_pgs"] = (r["r2_demo_pgs"] - r["r2_demo"]) / (1 - r["r2_demo"])
            r["r2_dcm_gwama"] = G2.cv_r2(Pg[:, [PGS.index("dcm")]], yz)
            r["r2_dcm_mtag_diag"] = G2.cv_r2(pg_mtag[Si][:, None], yz) if not np.isnan(pg_mtag[Si]).any() else np.nan
            r["smd_real"] = float(yz[base.t.to_numpy()[Si] == 1].mean() - yz[base.t.to_numpy()[Si] == 0].mean())
            if r["eligible"]:
                tS = base.t.to_numpy()[Si]
                lpd = ps_logit(X1, tS)
                lpd = lpd - lpd.mean()
                Xc = core.iloc[Si].to_numpy(float)
                sd = Xc.std(0)
                kp = sd > 0
                Z = (Xc[:, kp] - Xc[:, kp].mean(0)) / sd[kp]
                dd = pd.DataFrame(Z, columns=[f"z{j}" for j in range(Z.shape[1])])
                dd["treated"], dd["tt"], dd["ee"] = tS, base.y_t.to_numpy()[Si], base.y_e.to_numpy()[Si]
                cph = CoxPHFitter(penalizer=0.01).fit(dd, "tt", "ee")
                beta = cph.params_.drop("treated").reindex(dd.columns[:-3]).to_numpy()
                bh = cph.baseline_cumulative_hazard_
                tb, Hb = bh.index.to_numpy(float), bh.iloc[:, 0].to_numpy(float)
                m = (tb > 0) & (Hb > 0)
                rho, loglam = np.polyfit(np.log(tb[m]), np.log(Hb[m]), 1)
                lam = float(np.exp(loglam)) * float(np.exp(-cph.params_["treated"] * tS.mean()))
                lpc = Z @ beta
                pbar = float(tS.mean())
                Cad = base.Cadm.to_numpy()[Si]
                tsim = (np.random.default_rng(8).uniform(size=len(Si)) < expit(lpd + np.log(pbar / (1 - pbar)))).astype(int)
                erate = lambda kk: float(np.mean(1 - np.exp(-kk * lam * np.exp(lpc + np.log(TRUE_HR) * tsim) * Cad ** rho)))
                kmult = brentq(lambda kk: erate(kk) - TARGET_EVENT, 1e-3, 1e4)
                czs = sign * yz
                alpha_d = {orr: brentq(lambda a: expit(a + lpd + np.log(orr) * czs).mean() - pbar, -30, 30) for orr in OR_ALL}
                alpha_c = {orr: brentq(lambda a: expit(a + np.log(orr) * czs).mean() - pbar, -30, 30) for orr in OR_ALL}
                arr[f"{k}__rows"], arr[f"{k}__cz"], arr[f"{k}__lpd"], arr[f"{k}__lpc"] = Si, czs, lpd, lpc
                r.update(rho=float(rho), lam=lam, kmult=float(kmult), pbar=pbar, real_event_rate=float(dd.ee.mean()),
                         sim_event_rate_real=erate(1.0), sim_event_rate_target=erate(kmult), n_core=int(kp.sum()),
                         alpha_d=json.dumps({str(a): v for a, v in alpha_d.items()}),
                         alpha_c=json.dumps({str(a): v for a, v in alpha_c.items()}))
            rows.append(r)
        np.savez(OUT / f"restricted_prep_{tr}.npz", **arr)
        print(tr, checks[tr], flush=True)
    R = pd.DataFrame(rows)
    for col in [c for c in R.columns if c.startswith("n_")]:
        R[col] = R[col].map(lambda x: np.nan if 1 <= x <= 10 else x)
    R.to_csv(OUT / "prep_conf.csv", index=False)
    json.dump({k: {kk: (sup(vv) if kk.startswith("n_") else vv) for kk, vv in v.items()} for k, v in checks.items()},
              open(OUT / "prep_checks.json", "w"), indent=1)
    print(R[["cohort", "conf", "n_obs_t", "n_obs_c", "eligible", "r2_ecg", "r2_pgs", "r2_partial_ecg", "r2_partial_pgs"]].round(3).to_string())


# ---------------------------------------------------------------- simulation
def load(tr):
    if tr not in G:
        G.clear()
        G[tr] = dict(np.load(OUT / f"restricted_prep_{tr}.npz"))
    return G[tr]


def one(job):
    tr, k, rep, design, info = job
    from scipy.special import expit
    cfg = DESIGNS[design]
    D = load(tr)
    Si, cz, lpd, lpc = D[f"{k}__rows"], D[f"{k}__cz"], D[f"{k}__lpd"], D[f"{k}__lpc"]
    lam0 = info["lam"] * (info["kmult"] if cfg["rate"] == "target" else 1.0)
    rho = info["rho"]
    alpha = {float(a): v for a, v in json.loads(info["alpha_d" if cfg["trt_demo"] else "alpha_c"]).items()}
    ti, ci = info["ti"], info["ci"]
    N = len(Si)
    sub = np.sort(np.random.default_rng([50_000 + rep, ti, ci]).choice(N, int(round(FRAC * N)), replace=False))
    rows = Si[sub]
    czs, lpds, lpcs, Cadm = cz[sub], lpd[sub], lpc[sub], D["Cadm"][rows]
    X1, Ec, Sh, Pg = D["demo"][rows], D["ecg"][rows], D["shuf"][rows], D["pgs"][rows]
    blocks = {"base": X1, "ECG": np.hstack([X1, Ec]), "shufECG": np.hstack([X1, Sh]), "PGS": np.hstack([X1, Pg]),
              "PGSECG": np.hstack([X1, Pg, Ec]), "ECGonly": Ec, "shufECGonly": Sh, "PGSonly": Pg, "PGSECGonly": np.hstack([Pg, Ec]),
              "oracle": np.column_stack([X1, czs]), "oracleonly": czs[:, None]}
    arms = [a for a in cfg["arms"] if a != "unmatched"]
    out = []
    for oi, orr in enumerate(OR_ALL):
        lin = alpha[orr] + (lpds if cfg["trt_demo"] else 0.0) + np.log(orr) * czs
        trt = (np.random.default_rng([60_000 + rep, ti, ci, oi]).uniform(size=len(rows)) < expit(lin)).astype(int)
        if min(trt.sum(), (1 - trt).sum()) < 50:
            continue
        M = {"unmatched": (np.arange(len(rows)), None)}
        for a in arms:
            idx, cl, _ = match(ps_logit(blocks[a], trt), trt)
            M[a] = (idx, cl)
        for hry in [s[1] for s in SCEN if s[0] == orr]:
            hi = HRS.index(hry) if hry in HRS else -1
            lam = lam0 / float(np.mean(np.exp(np.log(hry) * cz)))
            lp0 = lpcs + np.log(hry) * czs
            u = np.random.default_rng([70_000 + rep, ti, ci, oi, hi + 1]).uniform(size=len(rows))
            tt, ee = G2.simulate(lp0 + np.log(TRUE_HR) * trt, lam, rho, Cadm, u)
            U = np.random.default_rng([80_000 + rep, ti, ci, oi, hi + 1]).uniform(size=(COPIES, len(rows)))
            for a, (idx, cl) in M.items():
                bb, se = cox(tt[idx], ee[idx], trt[idx], cluster=cl)
                ts, es, xs = [], [], []
                for kk in range(COPIES):
                    for x in (0, 1):
                        t_, e_ = G2.simulate(lp0[idx] + np.log(TRUE_HR) * x, lam, rho, Cadm[idx], U[kk, idx])
                        ts.append(t_); es.append(e_); xs.append(np.full(len(idx), x))
                truth = G2.cox_fast(np.concatenate(ts), np.concatenate(es), np.concatenate(xs))
                out.append(dict(cohort=tr, conf=k, or_t=orr, hr_y=hry, rep=rep, arm=a, loghr=bb, se=se, truth=truth,
                                n_an=len(idx), n_t=int(trt[idx].sum()), events=int(ee[idx].sum())))
    return out


def run(design, reps, workers):
    from multiprocessing import Pool
    os.umask(0o077)
    P = pd.read_csv(OUT / "prep_conf.csv")
    P = P[P.eligible]
    cells = DESIGNS[design].get("cells")
    if cells:
        P = P[[(r.cohort, r.conf) in cells for r in P.itertuples()]]
    info = {(r.cohort, r.conf): dict(lam=r.lam, rho=r.rho, kmult=r.kmult, alpha_d=r.alpha_d, alpha_c=r.alpha_c,
                                     ti=int(r.ti), ci=int(r.ci)) for r in P.itertuples()}
    jobs = [(tr, k, rep, design, info[(tr, k)]) for (tr, k) in info for rep in range(reps)]
    t0, res = time.time(), []
    with Pool(workers) as p:
        for i, o in enumerate(p.imap(one, jobs, chunksize=2)):
            res.extend(o)
            if i % 50 == 0:
                print(f"{design} {i}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    pd.DataFrame(res).to_csv(OUT / f"reps_{design}.csv", index=False)
    print("done", design, len(res), f"{time.time() - t0:.0f}s", flush=True)


# ---------------------------------------------------------------- summaries (as g2b_simulation_ext.pooled, UKB cells)
def errs(R):
    R = R.copy()
    R["err"] = R.loghr - R.truth
    R["cover"] = np.where(R.se.notna(), (np.abs(R.err) <= 1.96 * R.se).astype(float), np.nan)
    return R


def pooled(R, arms, ref_arms, B=1000, seed=0):
    W = R.pivot_table(index=["cohort", "conf", "or_t", "hr_y", "rep"], columns="arm", values="err").reset_index()
    nul = W[W.or_t == 1.0].drop(columns=["or_t", "hr_y"]).set_index(["cohort", "conf", "rep"])
    ex = W[W.or_t != 1.0].set_index(["cohort", "conf", "rep"])
    have = [a for a in arms if a in W.columns]
    exc = ex[have] - nul.reindex(ex.index)[have]
    exc[["or_t", "hr_y"]] = ex[["or_t", "hr_y"]]
    rng = np.random.default_rng(seed)
    out = []
    for lab, data in (("raw", ex.reset_index()), ("null-corrected", exc.reset_index())):
        for conf in list(CONF) + ["all"]:
            d = data if conf == "all" else data[data.conf == conf]
            if not len(d):
                continue
            key = ["cohort", "conf", "or_t", "hr_y"]
            cm = d.groupby(key)[have].mean()
            groups = [g[have].to_numpy() for _, g in d.groupby(key)]
            boots = np.empty((B, len(have)))
            for bi in range(B):
                boots[bi] = np.sum([g[rng.integers(0, len(g), len(g))].mean(0) for g in groups], axis=0)
            sums = cm.sum().to_numpy()
            for i, a in enumerate(have):
                r = dict(analysis=lab, conf=conf, arm=a, k_cells=d[["cohort", "conf"]].drop_duplicates().shape[0], mean_bias=cm[a].mean())
                for rf in ref_arms:
                    if rf in have:
                        j = have.index(rf)
                        r[f"pct_vs_{rf}"] = 100 * (1 - sums[i] / sums[j])
                        r[f"mcse_vs_{rf}"] = float(np.std(100 * (1 - boots[:, i] / boots[:, j]), ddof=1))
                out.append(r)
    perf = []
    for conf in list(CONF) + ["all"]:
        d = R[R.or_t != 1.0] if conf == "all" else R[(R.or_t != 1.0) & (R.conf == conf)]
        for a in have:
            g = d[d.arm == a].groupby(["cohort", "conf", "or_t", "hr_y"])
            nrep, bias, esd = g.err.count(), g.err.mean(), g.loghr.std()
            if not len(nrep):
                continue
            rmse = np.sqrt(g.err.apply(lambda x: np.mean(x ** 2)))
            cov = 100 * g.cover.mean()
            perf.append(dict(conf=conf, arm=a, k=len(nrep), bias=bias.mean(), bias_mcse=np.sqrt(np.mean(esd ** 2 / nrep) / len(nrep)),
                             emp_se=esd.mean(), rmse=rmse.mean(), coverage=cov.mean(),
                             coverage_mcse=np.sqrt(np.mean(cov * (100 - cov) / nrep)) / np.sqrt(len(nrep))))
    return pd.DataFrame(out), pd.DataFrame(perf)


def summarize():
    os.umask(0o077)
    for design in DESIGNS:
        f = OUT / f"reps_{design}.csv"
        if not f.exists():
            continue
        R = errs(pd.read_csv(f))
        refs = ("unmatched", "base") if design != "trtC" else ("unmatched",)
        S, Pf = pooled(R, DESIGNS[design]["arms"], refs)
        S.to_csv(OUT / f"pooled_{design}.csv", index=False)
        Pf.to_csv(OUT / f"performance_{design}.csv", index=False)
        # per cohort x conf (null-corrected, vs unmatched / base), for the R^2 relationship
        cells = []
        for (tr, k), g in R.groupby(["cohort", "conf"]):
            Sc, _ = pooled(g, DESIGNS[design]["arms"], refs, B=200)
            Sc = Sc[(Sc.analysis == "null-corrected") & (Sc.conf == k)]
            for rr in Sc.itertuples():
                cells.append(dict(cohort=tr, conf=k, arm=rr.arm, **{c: getattr(rr, c) for c in Sc.columns if c.startswith("pct_vs_")}))
        pd.DataFrame(cells).to_csv(OUT / f"cells_{design}.csv", index=False)
        print(design)
        print(S[S.analysis == "null-corrected"].round(2).to_string())


# ---------------------------------------------------------------- held-out CMR balance (real exposure; descriptive)
def smd_vec(V, t, idx):
    sd = np.sqrt((np.nanvar(V[t == 1], 0, ddof=1) + np.nanvar(V[t == 0], 0, ddof=1)) / 2)
    S, ts = V[idx], t[idx]
    return np.abs(np.nanmean(S[ts == 1], 0) - np.nanmean(S[ts == 0], 0)) / sd


def balance():
    os.umask(0o077)
    cmr = cmr_table()
    rows = []
    for ti, tr in enumerate(COHORTS):
        D = dict(np.load(OUT / f"restricted_prep_{tr}.npz"))
        c, b, o, e, roles, rct = load_cohort(tr)
        ids = [i for i in c.index if i in e.index]
        cm = cmr.reindex(ids)
        B = cm.lvef.notna().to_numpy() & ~np.isnan(D["pgs"]).any(1)
        Bi = np.where(B)[0]
        t = D["t"][Bi].astype(int)
        V = cm.iloc[Bi][list(PANEL)].to_numpy(float)
        X1, Ec, Sh, Pg = D["demo"][Bi], D["ecg"][Bi], D["shuf"][Bi], D["pgs"][Bi]
        blocks = {"base": X1, "ECG": np.hstack([X1, Ec]), "shufECG": np.hstack([X1, Sh]), "PGS": np.hstack([X1, Pg]),
                  "PGSECG": np.hstack([X1, Pg, Ec])}
        res = {"unmatched": smd_vec(V, t, np.arange(len(t)))}
        npairs = {}
        for a, X in blocks.items():
            idx, _, _ = match(ps_logit(X, t), t)
            res[a] = smd_vec(V, t, idx)
            npairs[a] = len(idx) // 2
        for a, s in res.items():
            r = dict(cohort=tr, arm=a, n_t=sup(t.sum()), n_c=sup((1 - t).sum()), n_pairs=sup(npairs.get(a, 0)) if a != "unmatched" else np.nan,
                     mean_abs_smd=float(np.nanmean(s)), pct_lt_0_1=float(100 * np.mean(s[~np.isnan(s)] < 0.1)))
            r.update({f"smd_{k}": float(v) for k, v in zip(PANEL, s)})
            rows.append(r)
    Bt = pd.DataFrame(rows)
    Bt.to_csv(OUT / "balance_cmr.csv", index=False)
    print(Bt[["cohort", "arm", "n_t", "n_c", "n_pairs", "mean_abs_smd", "pct_lt_0_1", "smd_lvef", "smd_lvmi", "smd_lavi_max"]].round(3).to_string())


# ---------------------------------------------------------------- figure
def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    P = pd.read_csv(OUT / "prep_conf.csv")
    Cl = pd.read_csv(OUT / "cells_trtC.csv")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    for arm, r2col, col, mk in (("ECGonly", "r2_ecg", "#d9544f", "o"), ("PGSonly", "r2_pgs", "#0d0f3a", "s"),
                                ("PGSECGonly", "r2_pgs_ecg", "#7a7fb0", "^")):
        d = Cl[Cl.arm == arm].merge(P, on=["cohort", "conf"])
        ax[0].scatter(d[r2col], d.pct_vs_unmatched, c=col, marker=mk, label=LAB[arm], s=45)
    x = np.linspace(0, 0.45, 10)
    ax[0].plot(x, 100 * x, "--", c="grey", lw=1, label="y = 100 × R²")
    ax[0].set_xlabel("Cross-fitted R² of proxy for the CMR confounder")
    ax[0].set_ylabel("% of confounder-induced bias removed (vs unmatched)")
    ax[0].legend(fontsize=8, frameon=False)
    ax[0].set_title("a  Proxy strength and bias removed (treatment driven by C)", fontsize=10, loc="left")
    S = pd.read_csv(OUT / "pooled_main.csv")
    S = S[(S.analysis == "null-corrected")]
    arms = ["ECG", "PGS", "PGSECG", "oracle"]
    confs = list(CONF)
    w = 0.2
    for j, a in enumerate(arms):
        vals = [S[(S.conf == k) & (S.arm == a)].pct_vs_base.squeeze() for k in confs]
        ax[1].bar(np.arange(len(confs)) + (j - 1.5) * w, vals, w, label=LAB[a].replace("Demographic PS", "Demo PS"))
    ax[1].set_xticks(np.arange(len(confs)), [CONF[k][0] for k in confs], fontsize=9)
    ax[1].set_ylabel("% of demographic-PS bias removed (null-corrected)")
    ax[1].set_ylim(-10, 122)
    ax[1].legend(fontsize=8, frameon=False, ncol=2, loc="upper center")
    ax[1].set_title("b  Added to the demographic PS", fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(DOCS / "UKB_CMR_plasmode.png", dpi=160)
    print("figure saved")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--design", default="main")
    ap.add_argument("--reps", type=int, default=50)
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    {"prep": prep, "summarize": summarize, "balance": balance, "figure": figure}.get(a.cmd, lambda: run(a.design, a.reps, a.workers))()
