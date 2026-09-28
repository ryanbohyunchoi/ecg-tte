#!/usr/bin/env python
"""v1.9 G3 (docs/v18/V19_GERMAN_STYLE_PLAN.md): AI-ECG prognostic and predictive enrichment, 38 trials. Exploratory.

Risk scores (per trial, fitted in the trial's full cohort of initiators, rows with a usable outcome T.y_ok; no treatment term):
  5-fold cross-fitted (StratifiedKFold on the event indicator, shuffle, random_state = 19030 + i; one row = one patient,
  so folds are by patient) L2-penalised Cox (lifelines, penalizer PEN = 0.01, l1_ratio 0; features standardised on the
  training fold, zero-variance columns dropped) of the primary outcome, follow-up capped at the trial horizon (T.y_t,
  T.y_e). The out-of-fold linear predictor is the score (higher = higher risk).
    ECG      T.ecg_pc (32 ECG-embedding PCs)                                                 -> primary AI-ECG score
    ECG64    T.ecg_pc64 (64 PCs)                                                             -> sensitivity
    CLIN     T.X_dx (demographics + sparse diagnosis flags = the "sparse" PS design)         -> clinical comparator
    CLMBR    T.clm_pc (64 CLMBR-T PCs)
    ECG+CLIN T.ecg_pc + T.X_dx
    shufECG  T.ecg_pc[T.shuffle_perm] (placebo; expected HR/SD ~ 1, C ~ 0.5)
    PROG     external prognostic score prog_full (claude-<n>-progref-v1/scores-v3; L2 logistic fitted on 30,000
             reference patients outside the cohort, 1-year generic outcome, ~900 panel features); not cross-fitted,
             not trial-outcome specific. Its linear predictor is heavy-tailed, so its HR per SD / interaction use the
             rank-based inverse-normal transform of the score within the population (C-index / quantiles unaffected).
Populations: unm = all initiators in the trial cohort (unmatched); m_sparse = sparse-PS 1:1 caliper-0.2 matched sample
  (T.X_dx, L2 C = 1; the engine's `sparse` cell, reproduced against claude-v18-embed-compare/results.csv) -> PRIMARY
  matched population; m_P1 (T.demo) and m_clin (T.X_core) secondary.
Prognostic: Cox of outcome on the score standardised within the population (HR per SD; pair-clustered robust SE in matched
  samples, robust SE unmatched); Harrell's C (lifelines concordance_index); bootstrap (B = 200; pairs in matched, patients
  unmatched; score fixed) SEs for C and paired Delta-C.
Enrichment (German et al. approach): required events D = 4 (z_0.975 + z_0.80)^2 / (log HR_RCT)^2 (Schoenfeld, 1:1) is
  unchanged by enrichment when the relative effect is assumed constant; enrolled N = D / p, p = Kaplan-Meier cumulative
  incidence at the horizon (arms pooled) in the population or in its top 25% / 50% by score (threshold = quantile within
  the population). Reduction = 1 - p_full / p_top. Screening N = N_top / fraction. Bootstrap CI.
Predictive: Cox on the matched sample with treatment, z (score standardised in the matched sample) and treatment x z,
  pair-clustered robust SE; per trial, DerSimonian-Laird pooled, BH-FDR within score x population over trials and over all.

Usage: g3_enrichment.py run [--trials a,b] [--workers 20] | summarize | figures
Outputs: /mnt/raid0/rbc58/ecg-tte/audits/claude-v19-g3-enrichment/ (umask 077; aggregates; counts 1-10 suppressed).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import norm  # noqa: E402

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v18"))
import v18_embed_compare as EC  # noqa: E402

E = EC.E
from lifelines import CoxPHFitter  # noqa: E402
from lifelines.utils import concordance_index  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

A = EC.A
OUT = A / "claude-v19-g3-enrichment"
DOCS = HERE.parent.parent / "docs" / "v19"
ALL, OLD, CATEGORY = EC.ALL, EC.OLD, EC.CATEGORY
PEN = 0.01
NB = 200
SCORES = ["ECG", "ECG64", "CLIN", "CLMBR", "ECG+CLIN", "shufECG", "PROG"]
POPS = ["unm", "m_sparse", "m_P1", "m_clin"]
FRACS = (0.25, 0.5)
MIN_CELL = 11
ZSUM = norm.ppf(0.975) + norm.ppf(0.80)


def fit_cox(X, yt, ye, pen=PEN):
    sd = X.std(0)
    keep = sd > 0
    X = X[:, keep]
    mu, sd = X.mean(0), X.std(0)
    d = pd.DataFrame((X - mu) / sd, columns=[f"x{j}" for j in range(X.shape[1])])
    d["T"], d["E"] = yt, ye
    m = CoxPHFitter(penalizer=pen, l1_ratio=0.0).fit(d, "T", "E")
    b = m.params_.to_numpy()
    return lambda Z: ((Z[:, keep] - mu) / sd) @ b


def crossfit(X, yt, ye, seed):
    s = np.full(len(yt), np.nan)
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(X, ye):
        s[te] = fit_cox(X[tr], yt[tr], ye[tr])(X[te])
    return s


def coxm(df, cols, cluster=None):
    kw = dict(duration_col="T", event_col="E", robust=True)
    d = df[cols + ["T", "E"]].copy()
    if cluster is not None:
        d["cl"] = cluster
        kw["cluster_col"] = "cl"
    try:
        m = CoxPHFitter().fit(d, **kw)
        return m.params_, m.standard_errors_
    except Exception:
        return None, None


def km_inc(t, e, H):
    """Kaplan-Meier cumulative incidence at H (times already capped at H)."""
    o = np.argsort(t, kind="stable")
    t, e = t[o], e[o]
    n = len(t)
    ut, idx = np.unique(t, return_index=True)
    d = np.add.reduceat(e, idx)
    at = n - idx
    ok = (ut <= H) & (d > 0)
    return float(1 - np.prod(1 - d[ok] / at[ok]))


def enrich(t, e, s, H):
    out = {"p_full": km_inc(t, e, H)}
    for f in FRACS:
        top = s >= np.quantile(s, 1 - f)
        out[f"p_top{int(f * 100)}"] = km_inc(t[top], e[top], H)
        out[f"ev_top{int(f * 100)}"] = int(e[top].sum())
        out[f"n_top{int(f * 100)}"] = int(top.sum())
    return out


def cidx(t, e, s):
    return float(concordance_index(t, -s, e))


def task(n):
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    ok = T.y_ok.astype(bool)
    yt, ye = T.y_t, T.y_e.astype(int)
    H = T.horizon
    log = dict(trial=n, idx=i, n_ok=int(ok.sum()), events_ok=int(ye[ok].sum()), horizon_days=int(H))
    # ---- scores (cross-fitted on ok rows of the full cohort)
    feats = {"ECG": T.ecg_pc, "ECG64": T.ecg_pc64, "CLIN": T.X_dx, "CLMBR": T.clm_pc, "ECG+CLIN": np.hstack([T.ecg_pc, T.X_dx]),
             "shufECG": T.ecg_pc[T.shuffle_perm]}
    S = {}
    oki = np.where(ok)[0]
    for k, X in feats.items():
        s = np.full(len(yt), np.nan)
        s[oki] = crossfit(np.asarray(X, float)[oki], yt[oki], ye[oki], 19030 + i)
        S[k] = s
    pf = T.H["prog_full"].to_numpy(float) if "prog_full" in T.H else np.full(len(yt), np.nan)
    S["PROG"] = pf
    log["prog_missing_frac_ok"] = float(np.isnan(pf[ok]).mean())
    # ---- populations
    pops = {"unm": (oki, None)}
    Xps = {"m_sparse": T.X_dx, "m_P1": T.cov[T.demo].to_numpy(float), "m_clin": T.X_core}
    for p, X in Xps.items():
        lg = E.ps_logit(np.asarray(X, float), T.t)
        s_idx, cl, _ = E.match(lg, T.t, cal=0.2, ratio=1)
        m = ok[s_idx]
        if p == "m_sparse":  # reproduce the engine/embed-compare sparse cell
            b, se = E.cox(yt[s_idx][m], ye[s_idx][m], T.t[s_idx][m], cluster=cl[m])
            log.update(repro_sparse_loghr=b, repro_sparse_se=se, repro_sparse_pairs=int(len(np.unique(cl))))
        pops[p] = (s_idx[m], cl[m])
    prog, enr, pred, boot = [], [], [], []
    rng = np.random.default_rng(190300 + i)
    for p, (rows, cl) in pops.items():
        tt, ee, tr = yt[rows], ye[rows], T.t[rows]
        base = dict(trial=n, category=CATEGORY[n], idx=i, pop=p, rb=T.rb, rs=T.rs, n=len(rows), events=int(ee.sum()),
                    n_t=int(tr.sum()), n_c=int((1 - tr).sum()))
        D = 4 * ZSUM ** 2 / T.rb ** 2 if abs(T.rb) > 1e-9 else np.nan
        for k in SCORES:
            s = S[k][rows]
            okk = np.isfinite(s)
            if okk.mean() < 0.99 or okk.sum() < 50:
                continue
            s_, tt_, ee_, tr_ = s[okk], tt[okk], ee[okk], tr[okk]
            cl_ = None if cl is None else cl[okk]
            if k == "PROG":  # heavy-tailed external linear predictor: rank-based inverse-normal z (HR per SD of normal scores)
                from scipy.stats import rankdata
                z = norm.ppf(rankdata(s_) / (len(s_) + 1))
                z = (z - z.mean()) / z.std()
            else:
                z = (s_ - s_.mean()) / s_.std()
            df = pd.DataFrame(dict(T=tt_, E=ee_, z=z, trt=tr_, tz=tr_ * z))
            b, se = coxm(df, ["z"], cl_)
            r = dict(base, score=k, n_score=int(okk.sum()),
                     loghr_sd=np.nan if b is None else float(b["z"]), se_sd=np.nan if se is None else float(se["z"]),
                     cindex=cidx(tt_, ee_, s_))
            prog.append(r)
            en = enrich(tt_, ee_, s_, H)
            er = dict(base, score=k, D_events=D, **en)
            for f in FRACS:
                q = int(f * 100)
                er[f"red{q}"] = 1 - en["p_full"] / en[f"p_top{q}"] if en[f"p_top{q}"] > 0 else np.nan
                er[f"N_full"] = D / en["p_full"] if en["p_full"] > 0 else np.nan
                er[f"N_top{q}"] = D / en[f"p_top{q}"] if en[f"p_top{q}"] > 0 else np.nan
                er[f"screen{q}"] = er[f"N_top{q}"] / f
            enr.append(er)
            if p != "unm":
                b, se = coxm(df, ["trt", "z", "tz"], cl_)
                pr = dict(base, score=k)
                if b is not None:
                    pr.update(b_trt=float(b["trt"]), se_trt=float(se["trt"]), b_z=float(b["z"]), se_z=float(se["z"]),
                              b_int=float(b["tz"]), se_int=float(se["tz"]))
                    pr["p_int"] = float(2 * norm.sf(abs(pr["b_int"] / pr["se_int"])))
                pred.append(pr)
        # ---- bootstrap (unm and primary matched only): C-index, log(p_full/p_top)
        if p not in ("unm", "m_sparse"):
            continue
        ks = [k for k in SCORES if np.isfinite(S[k][rows]).mean() >= 0.99]
        if cl is None:
            groups = None
        else:
            u, inv = np.unique(cl, return_inverse=True)
            flat = np.argsort(inv, kind="stable")
            gl = np.bincount(inv)
            starts = np.r_[0, np.cumsum(gl)[:-1]]
            groups = len(u)
        for bi in range(NB):
            if groups is None:
                bb = rng.integers(0, len(rows), len(rows))
            else:
                pick = rng.integers(0, groups, groups)
                bb = np.concatenate([flat[starts[g]:starts[g] + gl[g]] for g in pick])
            tb, eb = tt[bb], ee[bb]
            rec = dict(trial=n, pop=p, b=bi)
            for k in ks:
                s = S[k][rows][bb]
                f = np.isfinite(s)
                rec[f"c:{k}"] = cidx(tb[f], eb[f], s[f])
                en = enrich(tb[f], eb[f], s[f], H)
                for fr in FRACS:
                    q = int(fr * 100)
                    rec[f"lr{q}:{k}"] = np.log(en["p_full"] / en[f"p_top{q}"]) if en[f"p_top{q}"] > 0 and en["p_full"] > 0 else np.nan
            boot.append(rec)
    log["secs"] = round(time.time() - t0, 1)
    print(f"{n} {log['secs']}s", flush=True)
    return prog, enr, pred, boot, log


def suppress(D, cols=("n", "events", "n_t", "n_c", "n_score", "ev_top25", "ev_top50", "n_top25", "n_top50")):
    D = D.copy()
    for c in cols:
        if c in D:
            v = pd.to_numeric(D[c], errors="coerce")
            D.loc[(v >= 1) & (v < MIN_CELL), c] = np.nan
    return D


def run(trials, workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "lodestar", "affirm", "aristotle", "east-afnet4", "cabana-v2", "transform-hf", "ontarget")
    tk = sorted(trials, key=lambda x: x not in big)
    with Pool(min(workers, len(tk))) as p:
        res = p.map(task, tk, chunksize=1)
    tag = "" if set(trials) == set(ALL) else "_partial"
    for j, name in enumerate(("prognostic", "enrichment", "predictive", "bootstrap")):
        D = pd.DataFrame([x for r in res for x in r[j]])
        (suppress(D) if name != "bootstrap" else D).to_csv(OUT / f"{name}{tag}.csv", index=False)
    (OUT / f"log{tag}.json").write_text(json.dumps([r[4] for r in res], indent=1, default=float))
    print("done", flush=True)


# ================================================================ summarize
def dl(d, v):
    d, v = np.asarray(d, float), np.asarray(v, float)
    k = np.isfinite(d) & np.isfinite(v) & (v > 0)
    d, v = d[k], v[k]
    if len(d) < 2:
        return dict(mu=np.nan, se=np.nan, tau2=np.nan, I2=np.nan, k=len(d))
    w = 1 / v
    mf = (w * d).sum() / w.sum()
    Q = (w * (d - mf) ** 2).sum()
    C = w.sum() - (w ** 2).sum() / w.sum()
    t2 = max(0.0, (Q - (len(d) - 1)) / C)
    ws = 1 / (v + t2)
    mu = (ws * d).sum() / ws.sum()
    return dict(mu=mu, se=np.sqrt(1 / ws.sum()), tau2=t2, I2=max(0.0, (Q - (len(d) - 1)) / Q) if Q > 0 else 0.0, k=len(d))


def signflip2(d):
    from v13_summarize import sign_flip
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    return sign_flip(d)[1] if len(d) else np.nan


def summarize():
    P = pd.read_csv(OUT / "prognostic.csv")
    En = pd.read_csv(OUT / "enrichment.csv")
    Pr = pd.read_csv(OUT / "predictive.csv")
    B = pd.read_csv(OUT / "bootstrap.csv")
    L = pd.DataFrame(json.load(open(OUT / "log.json")))
    # --- repro check
    R = pd.read_csv(A / "claude-v18-embed-compare/results.csv")
    R = R[(R.half == "full") & (R.rung == "sparse") & (R.arm_role == "base")].set_index("trial")
    L["ref_loghr"] = L.trial.map(R.loghr)
    L["ref_pairs"] = L.trial.map(R.n_pairs)
    L["repro_dev"] = (L.repro_sparse_loghr - L.ref_loghr).abs()
    L.to_csv(OUT / "log_check.csv", index=False)
    # --- bootstrap SEs
    bse = []
    for (n, p), g in B.groupby(["trial", "pop"]):
        r = dict(trial=n, pop=p)
        for c in g.columns:
            if c.startswith(("c:", "lr")):
                r["se_" + c] = g[c].std()
        for a, b in (("ECG", "CLIN"), ("ECG+CLIN", "CLIN"), ("CLMBR", "ECG"), ("CLMBR", "CLIN"), ("ECG", "shufECG"), ("ECG64", "ECG"),
                     ("ECG+CLIN", "ECG")):
            if f"c:{a}" in g and f"c:{b}" in g:
                r[f"se_dc:{a}-{b}"] = (g[f"c:{a}"] - g[f"c:{b}"]).std()
            for q in (25, 50):
                if f"lr{q}:{a}" in g and f"lr{q}:{b}" in g:
                    r[f"se_dlr{q}:{a}-{b}"] = (g[f"lr{q}:{a}"] - g[f"lr{q}:{b}"]).std()
        bse.append(r)
    BS = pd.DataFrame(bse).set_index(["trial", "pop"])
    P = P.join(BS, on=["trial", "pop"])
    P["se_c"] = [r.get(f"se_c:{r['score']}", np.nan) for _, r in P.iterrows()]
    En = En.join(BS, on=["trial", "pop"])
    for q in (25, 50):
        En[f"lr{q}"] = np.log(En.p_full / En[f"p_top{q}"])
        En[f"se_lr{q}"] = [r.get(f"se_lr{q}:{r['score']}", np.nan) for _, r in En.iterrows()]
        # percentile bootstrap CI for reduction = 1 - exp(lr)
        En[f"red{q}_lo"] = np.nan
        En[f"red{q}_hi"] = np.nan
    for (n, p), g in B.groupby(["trial", "pop"]):
        for q in (25, 50):
            for k in SCORES:
                c = f"lr{q}:{k}"
                if c in g:
                    lo, hi = np.nanpercentile(g[c], [2.5, 97.5])
                    m = (En.trial == n) & (En["pop"] == p) & (En.score == k)
                    En.loc[m, f"red{q}_lo"] = 1 - np.exp(hi)
                    En.loc[m, f"red{q}_hi"] = 1 - np.exp(lo)
    P["hr_sd"] = np.exp(P.loghr_sd)
    P["p_sd"] = 2 * norm.sf(np.abs(P.loghr_sd / P.se_sd))
    P.to_csv(OUT / "prognostic_per_trial.csv", index=False)
    En.to_csv(OUT / "enrichment_per_trial.csv", index=False)
    # --- pooled prognostic
    rows = []
    for (p, k), g in P.groupby(["pop", "score"]):
        m = dl(g.loghr_sd, g.se_sd ** 2)
        mc = dl(g.cindex, g.se_c ** 2)
        rows.append(dict(pop=p, score=k, k=m["k"], hr_sd=np.exp(m["mu"]), lo=np.exp(m["mu"] - 1.96 * m["se"]),
                         hi=np.exp(m["mu"] + 1.96 * m["se"]), I2=m["I2"], tau2=m["tau2"], c_pooled=mc["mu"], c_lo=mc["mu"] - 1.96 * mc["se"],
                         c_hi=mc["mu"] + 1.96 * mc["se"], c_mean=g.cindex.mean(), c_min=g.cindex.min(), c_max=g.cindex.max(),
                         n_sig=int((g.p_sd < 0.05).sum())))
    PP = pd.DataFrame(rows)
    PP.to_csv(OUT / "prognostic_pooled.csv", index=False)
    # --- pooled by category (AF, HF)
    rows = []
    for cat in ("AF", "HF", "DM", "HTN", "ACS/post-MI", "Other"):
        for (p, k), g in P[P.category == cat].groupby(["pop", "score"]):
            m = dl(g.loghr_sd, g.se_sd ** 2)
            rows.append(dict(category=cat, pop=p, score=k, k=m["k"], hr_sd=np.exp(m["mu"]), lo=np.exp(m["mu"] - 1.96 * m["se"]),
                             hi=np.exp(m["mu"] + 1.96 * m["se"]), c_mean=g.cindex.mean()))
    PC = pd.DataFrame(rows)
    PC.to_csv(OUT / "prognostic_by_category.csv", index=False)
    # --- paired Delta C across trials (bootstrap SE -> DL; sign-flip across trials)
    rows = []
    for p in ("unm", "m_sparse"):
        g = P[P["pop"] == p].pivot(index="trial", columns="score", values="cindex")
        for a, b in (("ECG", "CLIN"), ("ECG+CLIN", "CLIN"), ("CLMBR", "ECG"), ("CLMBR", "CLIN"), ("ECG", "shufECG"), ("ECG64", "ECG"),
                     ("ECG+CLIN", "ECG"), ("ECG", "PROG")):
            if a not in g or b not in g:
                continue
            d = (g[a] - g[b]).dropna()
            se = BS.xs(p, level="pop").reindex(d.index).get(f"se_dc:{a}-{b}")
            m = dl(d, se ** 2) if se is not None else dict(mu=np.nan, se=np.nan, I2=np.nan)
            rows.append(dict(pop=p, a=a, b=b, n_trials=len(d), mean_dC=d.mean(), k_pos=f"{int((d > 0).sum())}/{len(d)}",
                             p_signflip=signflip2(d.to_numpy()), dl_dC=m["mu"], dl_lo=m["mu"] - 1.96 * m["se"], dl_hi=m["mu"] + 1.96 * m["se"],
                             n_trials_sig=int((np.abs(d / se) > 1.96).sum()) if se is not None else np.nan))
    DC = pd.DataFrame(rows)
    DC.to_csv(OUT / "cindex_paired.csv", index=False)
    # --- matched vs unmatched HR per SD
    rows = []
    for k in SCORES:
        a = P[(P["pop"] == "m_sparse") & (P.score == k)].set_index("trial").loghr_sd
        b = P[(P["pop"] == "unm") & (P.score == k)].set_index("trial").loghr_sd
        d = (a - b).dropna()
        rows.append(dict(score=k, n_trials=len(d), mean_dlog=d.mean(), ratio_geo=np.exp(d.mean()), k_lower_in_matched=f"{int((d < 0).sum())}/{len(d)}",
                         p_signflip=signflip2(d.to_numpy())))
    MU = pd.DataFrame(rows)
    MU.to_csv(OUT / "matched_vs_unmatched.csv", index=False)
    # --- pooled enrichment
    rows = []
    for (p, k), g in En.groupby(["pop", "score"]):
        r = dict(pop=p, score=k)
        for q in (25, 50):
            m = dl(g[f"lr{q}"], g[f"se_lr{q}"] ** 2)
            r.update({f"red{q}_pooled": 1 - np.exp(m["mu"]), f"red{q}_lo": 1 - np.exp(m["mu"] + 1.96 * m["se"]),
                      f"red{q}_hi": 1 - np.exp(m["mu"] - 1.96 * m["se"]), f"red{q}_median": g[f"red{q}"].median(),
                      f"red{q}_min": g[f"red{q}"].min(), f"red{q}_max": g[f"red{q}"].max(), f"I2_{q}": m["I2"], "k": m["k"]})
        rows.append(r)
    EP = pd.DataFrame(rows)
    EP.to_csv(OUT / "enrichment_pooled.csv", index=False)
    rows = []
    for p in ("unm", "m_sparse"):
        g = En[En["pop"] == p]
        for q in (25, 50):
            w = g.pivot(index="trial", columns="score", values=f"lr{q}")
            for a, b in (("ECG", "CLIN"), ("ECG+CLIN", "CLIN"), ("CLMBR", "ECG"), ("ECG", "shufECG")):
                d = -(w[a] - w[b]).dropna()  # > 0: a gives larger enrichment (larger event-rate ratio)
                se = BS.xs(p, level="pop").reindex(d.index).get(f"se_dlr{q}:{a}-{b}")
                m = dl(d, se ** 2)
                rows.append(dict(pop=p, frac=q, a=a, b=b, n_trials=len(d), k_a_better=f"{int((d > 0).sum())}/{len(d)}",
                                 mean_dlogratio=d.mean(), p_signflip=signflip2(d.to_numpy()), dl=m["mu"], dl_lo=m["mu"] - 1.96 * m["se"],
                                 dl_hi=m["mu"] + 1.96 * m["se"]))
    ED = pd.DataFrame(rows)
    ED.to_csv(OUT / "enrichment_paired.csv", index=False)
    # --- predictive
    Pr["q_within"] = np.nan
    for (p, k), g in Pr.groupby(["pop", "score"]):
        Pr.loc[g.index, "q_within"] = E.bh_fdr(g.p_int.to_numpy())
    Pr["q_all"] = E.bh_fdr(Pr.p_int.to_numpy())
    Pr.to_csv(OUT / "predictive_per_trial.csv", index=False)
    rows = []
    for (p, k), g in Pr.groupby(["pop", "score"]):
        m = dl(g.b_int, g.se_int ** 2)
        rows.append(dict(pop=p, score=k, k=m["k"], ratio_hr_per_sd=np.exp(m["mu"]), lo=np.exp(m["mu"] - 1.96 * m["se"]),
                         hi=np.exp(m["mu"] + 1.96 * m["se"]), p=2 * norm.sf(abs(m["mu"] / m["se"])), I2=m["I2"],
                         n_p05=int((g.p_int < 0.05).sum()), n_q10_within=int((g.q_within < 0.10).sum()), min_q_within=g.q_within.min()))
    PRP = pd.DataFrame(rows)
    PRP.to_csv(OUT / "predictive_pooled.csv", index=False)
    print(L[["trial", "repro_sparse_loghr", "ref_loghr", "repro_dev", "repro_sparse_pairs", "ref_pairs", "secs"]].to_string())
    print(PP.round(3).to_string())
    print(DC.round(4).to_string())
    print(MU.round(3).to_string())
    print(EP.round(3).to_string())
    print(ED.round(4).to_string())
    print(PRP.round(3).to_string())


def tables():
    from v13_summarize import md
    P = pd.read_csv(OUT / "prognostic_per_trial.csv")
    En = pd.read_csv(OUT / "enrichment_per_trial.csv")
    Pr = pd.read_csv(OUT / "predictive_per_trial.csv")
    order = _order()
    L = []
    f = lambda b, s: f"{np.exp(b):.2f} ({np.exp(b - 1.96 * s):.2f}-{np.exp(b + 1.96 * s):.2f})"
    for pop, lab in (("m_sparse", "sparse-PS matched"), ("unm", "all initiators (unmatched)"), ("m_P1", "P1-matched"), ("m_clin", "clinical-PS matched")):
        rows = []
        for t in order:
            r = dict(trial=t, cat=CATEGORY[t])
            g = P[(P.trial == t) & (P["pop"] == pop)].set_index("score")
            if not len(g):
                continue
            r["n"], r["events"] = [("<11" if not np.isfinite(v) else f"{int(v)}") for v in (g.n.iloc[0], g.events.iloc[0])]
            for k in ("ECG", "CLIN", "CLMBR", "ECG+CLIN", "PROG", "shufECG"):
                if k in g.index:
                    r[f"HR/SD {k}"] = f(g.loc[k, "loghr_sd"], g.loc[k, "se_sd"])
            for k in ("ECG", "CLIN", "CLMBR", "ECG+CLIN", "PROG", "shufECG"):
                if k in g.index:
                    r[f"C {k}"] = round(g.loc[k, "cindex"], 3)
            rows.append(r)
        L += [f"### Prognostic, {lab}\n", md(pd.DataFrame(rows), 3) + "\n"]
    for pop in ("m_sparse", "unm"):
        rows = []
        for t in order:
            g = En[(En.trial == t) & (En["pop"] == pop)].set_index("score")
            r = dict(trial=t, cat=CATEGORY[t], rct_hr=round(float(np.exp(g.rb.iloc[0])), 2), p_full=round(g.p_full.iloc[0], 3),
                     N_full=f"{g.N_full.iloc[0]:,.0f}" if np.isfinite(g.N_full.iloc[0]) else "n/a (RCT HR = 1)")
            for k in ("ECG", "CLIN", "CLMBR", "ECG+CLIN"):
                r[f"{k} top25 p"] = round(g.loc[k, "p_top25"], 3)
                r[f"{k} red25 %"] = f"{100 * g.loc[k, 'red25']:.0f} ({100 * g.loc[k, 'red25_lo']:.0f}, {100 * g.loc[k, 'red25_hi']:.0f})"
                r[f"{k} red50 %"] = f"{100 * g.loc[k, 'red50']:.0f}"
            rows.append(r)
        L += [f"### Enrichment, {pop}\n", md(pd.DataFrame(rows), 3) + "\n"]
    for pop in ("m_sparse", "m_P1", "m_clin"):
        rows = []
        for t in order:
            g = Pr[(Pr.trial == t) & (Pr["pop"] == pop)].set_index("score")
            r = dict(trial=t, cat=CATEGORY[t])
            for k in ("ECG", "CLIN", "CLMBR", "ECG+CLIN", "PROG"):
                if k in g.index and np.isfinite(g.loc[k, "b_int"]):
                    r[f"{k} ratio"] = f(g.loc[k, "b_int"], g.loc[k, "se_int"])
                    r[f"{k} p (q)"] = f"{g.loc[k, 'p_int']:.3f} ({g.loc[k, 'q_within']:.2f})"
            rows.append(r)
        L += [f"### Predictive (treatment x score, ratio of HR per SD treated vs comparator), {pop}\n", md(pd.DataFrame(rows), 3) + "\n"]
    (OUT / "tables.md").write_text("\n".join(L))


COL = {"ECG":"#2a78d6", "CLIN": "#eb6834", "CLMBR": "#1baf7a", "ECG+CLIN": "#eda100"}
LAB = {"ECG": "AI-ECG (32 PCs)", "CLIN": "Clinical (demo + dx)", "CLMBR": "CLMBR-T (64 PCs)", "ECG+CLIN": "ECG + clinical"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=7)
    ax.xaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def _order():
    return [t for c in ("AF", "HF", "DM", "HTN", "ACS/post-MI", "Other") for t in ALL if CATEGORY[t] == c]


def figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    DOCS.mkdir(parents=True, exist_ok=True)
    P = pd.read_csv(OUT / "prognostic_per_trial.csv")
    PP = pd.read_csv(OUT / "prognostic_pooled.csv")
    En = pd.read_csv(OUT / "enrichment_per_trial.csv")
    EP = pd.read_csv(OUT / "enrichment_pooled.csv")
    order = _order()
    ks = ["ECG", "CLIN", "CLMBR"]
    # ---- forest
    fig, axes = plt.subplots(1, 2, figsize=(10, 11), sharey=True)
    ylab = [f"{t} ({CATEGORY[t]})" for t in order] + [""] + [f"Pooled: {LAB[k]}" for k in ks]
    for ax, pop, title in zip(axes, ("m_sparse", "unm"), ("Emulated trial population (sparse-PS matched)", "All initiators in the trial cohort")):
        for j, k in enumerate(ks):
            g = P[(P["pop"] == pop) & (P.score == k)].set_index("trial").reindex(order)
            y = np.arange(len(order)) + (j - 1) * 0.25
            lo, hi = np.exp(g.loghr_sd - 1.96 * g.se_sd), np.exp(g.loghr_sd + 1.96 * g.se_sd)
            ax.hlines(y, lo, hi, color=COL[k], lw=1.2)
            ax.plot(np.exp(g.loghr_sd), y, "o", ms=4, color=COL[k], mec="white", mew=0.6, label=LAB[k])
            pr = PP[(PP["pop"] == pop) & (PP.score == k)].iloc[0]
            yp = len(order) + 1 + j
            ax.hlines(yp, pr.lo, pr.hi, color=COL[k], lw=2)
            ax.plot(pr.hr_sd, yp, "D", ms=6, color=COL[k], mec="white", mew=0.6)
            ax.text(pr.hi * 1.04, yp, f"{pr.hr_sd:.2f} ({pr.lo:.2f}-{pr.hi:.2f})", color=INK2, fontsize=7, va="center")
        ax.axvline(1, color=INK2, lw=0.8)
        ax.set_xscale("log")
        ax.set_xlim(0.7, 3.8)
        ax.set_xticks([0.8, 1, 1.25, 1.5, 2, 2.5, 3])
        ax.set_xticklabels(["0.8", "1", "1.25", "1.5", "2", "2.5", "3"])
        ax.set_title(title, fontsize=9, color=INK, loc="left")
        ax.set_xlabel("HR per SD of cross-fitted risk score (95% CI)", fontsize=8, color=INK2)
        _style(ax)
    axes[0].set_yticks(np.arange(len(ylab)))
    axes[0].set_yticklabels(ylab, fontsize=7, color=INK)
    axes[0].invert_yaxis()
    h, lb = axes[0].get_legend_handles_labels()
    fig.legend(h, lb, loc="upper left", bbox_to_anchor=(0.02, 0.975), ncol=3, fontsize=8, frameon=False)
    fig.suptitle("G3 prognostic enrichment: HR per SD of AI-ECG vs clinical vs CLMBR-T risk score, 38 trials (exploratory)",
                 fontsize=10, color=INK, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(DOCS / "G3_prognostic_forest.png", dpi=160)
    plt.close(fig)
    # ---- sample size
    ks = ["ECG", "CLIN", "CLMBR", "ECG+CLIN"]
    ylab = [f"{t} ({CATEGORY[t]})" for t in order] + [""] + [f"Pooled: {LAB[k]}" for k in ks]
    fig, axes = plt.subplots(1, 2, figsize=(10, 11), sharey=True)
    for ax, q in zip(axes, (25, 50)):
        for j, k in enumerate(ks):
            g = En[(En["pop"] == "m_sparse") & (En.score == k)].set_index("trial").reindex(order)
            y = np.arange(len(order)) + (j - 1.5) * 0.2
            ax.hlines(y, 100 * g[f"red{q}_lo"], 100 * g[f"red{q}_hi"], color=COL[k], lw=0.9, alpha=0.8)
            ax.plot(100 * g[f"red{q}"], y, "o", ms=3.5, color=COL[k], mec="white", mew=0.5, label=LAB[k])
            pr = EP[(EP["pop"] == "m_sparse") & (EP.score == k)].iloc[0]
            yp = len(order) + 1 + j
            ax.hlines(yp, 100 * pr[f"red{q}_lo"], 100 * pr[f"red{q}_hi"], color=COL[k], lw=2)
            ax.plot(100 * pr[f"red{q}_pooled"], yp, "D", ms=6, color=COL[k], mec="white", mew=0.6)
            ax.text(100 * pr[f"red{q}_hi"] + 2, yp, f"{100 * pr[f'red{q}_pooled']:.0f}% ({100 * pr[f'red{q}_lo']:.0f}-{100 * pr[f'red{q}_hi']:.0f})",
                    color=INK2, fontsize=7, va="center")
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_xlim(-30, 80)
        ax.set_title(f"Enrol top {q}% of score", fontsize=9, color=INK, loc="left")
        ax.set_xlabel("Reduction in enrolled patients vs unenriched (%; Schoenfeld, RCT HR)", fontsize=8, color=INK2)
        _style(ax)
    axes[0].set_yticks(np.arange(len(ylab)))
    axes[0].set_yticklabels(ylab, fontsize=7, color=INK)
    axes[0].invert_yaxis()
    h, lb = axes[0].get_legend_handles_labels()
    fig.legend(h, lb, loc="upper left", bbox_to_anchor=(0.02, 0.975), ncol=4, fontsize=8, frameon=False)
    fig.suptitle("G3 sample-size reduction from prognostic enrichment, sparse-PS matched trial population (exploratory)",
                 fontsize=10, color=INK, x=0.02, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(DOCS / "G3_sample_size.png", dpi=160)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run", "summarize", "tables", "figures"])
    ap.add_argument("--trials", default=",".join(ALL))
    ap.add_argument("--workers", type=int, default=20)
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.trials.split(","), a.workers)
    elif a.cmd == "summarize":
        summarize()
    elif a.cmd == "tables":
        tables()
    else:
        figures()


if __name__ == "__main__":
    main()
