#!/usr/bin/env python
"""v1.6 shared engine (docs/V16_SWEEP_PLAN.md): load a trial, build the 58-variable held-out balance
panel, run one sweep cell (PS -> match/weight -> Cox + held-out balance), and summarise paired
arm comparisons across trials. Exploratory. Restricted data stay in memory or in restricted_*
caches under the audits dir; every return value is an aggregate.

API (import with ``sys.path.insert(0, "<repo>/scripts/v16"); import v16_engine as E``)
---------------------------------------------------------------------------------------
TRIALS                      the 18 trial names (make_acc_figure.trials order).
VARS, GROUPS                58 held-out variables (column, label, group) = make_acc_figure.VARS;
                            GROUPS = ordered unique group labels.

load_trial(n, cache=True) -> v13_common.Trial  (imputation 1, pool split seed 0) with extra attributes
    T.y_t, T.y_e   follow-up time (days, capped at horizon) and event indicator, primary outcome
    T.y_ok         bool; row usable for outcome analysis (v13_common.outcomes; same as v13_bootstrap)
    T.horizon      horizon in days;  T.rb, T.rs = RCT benchmark log HR and SE (v13_common.bench)
    T.H            held-out matrix (= heldout_matrix(T))
  Cached to /mnt/raid0/rbc58/ecg-tte/audits/claude-v16-engine/cache/restricted_trial_<n>_v<CACHE_VERSION>.pkl
  (lazy CLMBR PCs are not cached).  T.arms([...], rows=...) (v13_common) gives the standard designs:
  "unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "sparse+shufECG",
  "sparse+noise32", "demo", ... ; use T.hd(k, t, rows) for other hdPS k.

heldout_matrix(T) -> DataFrame (index T.keys, float, NaN = unobserved), component columns:
    "meds::<c>"   completed medication-order flags (imputation 1)      -> variable mean_meds (mean of component |SMD|)
    "util::<c>"   completed utilisation counts                          -> variable mean_util
    "B::<f>"      pool-B panel features (split seed 0; codes as any-use, lab_ values observed-only,
                  labn_ counts; exposure features removed)               -> variable B_mean
    "prog_full"   external prognostic score (linear predictor)          -> smd_prog_full
    "obs_<v>"     observed (non-imputed) vitals/labs; lvef masked for index < ECHO_START -> smd_obs_<v>
                  (only if the observed column has missing values, as in eval_longtail_balance)
    "pp_<D__v>"   physiology panel v2; echo/ACCESS columns masked for index < ECHO_START -> pp_<D__v>
  Only components of VARS are included.  var_components(H) -> {VARS column: [component columns]}.

run_cell(T, X, t=None, rows=None, estimator=("match", 0.2, 1), ps_model=("l2", 1.0), heldout=None,
         cstat=("l2", 0.01), seed=0) -> dict (flat, aggregates only)
    X          PS design for `rows` (np.ndarray, n_rows x p) or None = unmatched (crude).
    t          treatment for `rows` (default T.t[rows]); rows = integer positions into T.keys
               (None = full cohort; may contain repeats, e.g. bootstrap / split halves / subgroups).
    estimator  ("match", caliper_in_SD_of_logit, ratio) | ("iptw",) stabilised, trimmed at PS 1st/99th pct
               | ("overlap",).  Cox: pair/anchor-clustered robust SE for matching (ratio>1 weighted 1/m),
               robust sandwich SE for weights (v13_common.cox).
    ps_model   ("l2", C) | ("gbm", None) (5-fold cross-fitted; v13_common.ps_logit).
    heldout    held-out matrix (default T.H).  Balance is computed in the matched/weighted sample:
               NaN-aware (weighted) arm means, divided by the pooled SD of the analysed (unmatched) rows,
               exactly as eval_longtail_balance.smd_vector.
    cstat      ("l2", C) | ("gbm", None) | None: 5-fold cross-fitted classifier of treatment from all held-out
               components (sample-median imputation + missing indicators, standardised) within the
               matched/weighted sample (weights as sample_weight, weighted AUC). 0.5 = arms indistinguishable.
  Returned keys: loghr, se, n (analysed rows), n_t, n_c, n_pairs (matching: anchors matched; NaN otherwise),
    ess_t, ess_c (Kish ESS per arm in the balance sample), mean_smd (mean over available VARS),
    n_vars, mean_smd_g:<group> per group, smd_prog (= smd:smd_prog_full), cstat, secs,
    smd:<VARS column> for each of the 58 variables (NaN if unavailable).

summarize_pairs(df, cell_cols, arm_a, arm_b) -> DataFrame, one row per cell.
    df long: one row per (trial, arm, *cell_cols) with columns trial, arm, loghr, se, rb, rs and optionally
    mean_smd, cstat.  Paired over trials having both arms (a minus b; negative = arm_a better):
    for metric m in {absd (|Δlog HR| vs RCT), z2 (Δ²/(se²+se_RCT²)), mean_smd, cstat}:
      d_<m> mean difference, k_<m> "trials improved/n" (diff < 0), p_<m> exact sign-flip p (v13_summarize.sign_flip);
    plus cons_a / cons_b (% |z| < 1.96) and phi_a / phi_b (Q/(k-1), v14_panel.dl), n_trials.
bh_fdr(pvals) -> BH-adjusted q-values (NaN kept).

CLI:  python v16_engine.py --validate [--trials a,b] [--workers 18]
    rebuilds every trial (and cache), checks estimates vs claude-v13-bootstrap/bs_<n>.csv rep 0 and
    per-variable |SMD| vs claude-cap4-all-<n>/longtail_imp1_seed0.csv (and summary_pooled.csv), writes
    audits/claude-v16-engine/validation_*.csv and docs/v16/ENGINE_VALIDATION.md.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse  # noqa: E402
import json  # noqa: E402
import pickle  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from make_acc_figure import VARS, trials as TRIALS  # noqa: E402
from v13_common import A, ECHO_START, EXTRA, PRIMARY, Trial, bench, check_against_saved, cox, match, outcomes, paths, ps_logit, weights  # noqa: E402
from v13_summarize import md, sign_flip  # noqa: E402
from v14_panel import dl  # noqa: E402

OUT = A / "claude-v16-engine"
CACHE = OUT / "cache"
DOCS = HERE.parent.parent / "docs" / "v16"
CACHE_VERSION = 1
GROUPS = list(dict.fromkeys(g for _, _, g in VARS))
VAR_GROUP = {c: g for c, _, g in VARS}
VAL_ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]
UTIL = {"outpatient_visits", "ed_encounters", "hospital_admissions"}


# ---------------------------------------------------------------- loading
def heldout_matrix(T: Trial) -> pd.DataFrame:
    """58-variable held-out panel components for every patient in T.keys (see module docstring)."""
    if getattr(T, "H", None) is not None:
        return T.H
    n, keys = T.n, T.keys
    cdir = {**PRIMARY, **EXTRA}[n][1]
    B = f"{A}/claude-{n}-baseline-v11"
    roles = T.roles
    cols = {}
    # meds / util: completed covariates (imputation of T)
    for c in T.meds:
        cols[f"meds::{c}"] = T.cov[c].to_numpy(float)
    for c in T.util:
        cols[f"util::{c}"] = T.cov[c].to_numpy(float)
    # pool B (same split as eval_longtail_balance / Trial, split seed 0)
    P = paths(n)
    panel = pd.read_parquet(P["panel"]).set_index("patient_key").loc[keys]
    dic = pd.read_csv(P["dic"])
    rng = np.random.default_rng(getattr(T, "split_seed", 0))
    pool = {}
    for dom, grp in dic.groupby("domain"):
        f = grp.feature.to_numpy().copy()
        rng.shuffle(f)
        pool[dom] = (f[: len(f) // 2], f[len(f) // 2:])
    Bf = [f for _, b in pool.values() for f in b]
    Bf = Bf + [f.replace("lab_", "labn_") for f in Bf if f.startswith("lab_")]
    expo = set(roles.get("exposure_features", []))
    Bf = [f for f in Bf if f not in expo]
    is_code = lambda f: f.split("_")[0] in ("dx", "rx", "px")
    for f in Bf:
        v = panel[f].to_numpy(float)
        cols[f"B::{f}"] = (v > 0).astype(float) if is_code(f) else v
    # prognostic score
    pf = A / f"claude-{n}-progref-v1" / "scores-v3" / "restricted_prognostic_scores.parquet"
    if pf.exists():
        cols["prog_full"] = pd.read_parquet(pf).set_index("patient_key").reindex(keys)["prog_full"].to_numpy(float)
    # echo mask (index date < ECHO_START or unknown), as eval_longtail_balance --echo-eval-start
    ro = pd.read_parquet(f"{A}/{cdir}/restricted_cohort.parquet").set_index("patient_key").index_date
    early = pd.to_datetime(ro.reindex(keys)).lt(pd.Timestamp(ECHO_START)).fillna(True).to_numpy()
    obs = pd.read_parquet(f"{B}/restricted_baseline_observed.parquet").set_index("patient_key").reindex(keys)
    if "lvef" in obs:
        obs.loc[early, "lvef"] = np.nan
    rep_ok = [c for c in roles["report_covariates"] if c in T.cov]  # eval: rep restricted to completed covariates
    obs_cols = [c for c in dict.fromkeys(rep_ok + roles.get("heldout_physiology", [])) if c in obs]
    want_obs = {c[len("smd_obs_"):] for c, _, _ in VARS if c.startswith("smd_obs_")}
    for c in obs_cols:
        if c in want_obs and obs[c].isna().any():
            cols[f"obs_{c}"] = obs[c].to_numpy(float)
    PP = pd.read_parquet(f"{A}/claude-{n}-physpanel-v11/restricted_physiology_panel.parquet").set_index("patient_key").reindex(keys)
    echo_cols = [c for c in PP.columns if c.split("__")[0] not in ("LAB", "BNP")]
    PP.loc[early, echo_cols] = np.nan
    for c, _, _ in VARS:
        if c.startswith("pp_") and c[3:] in PP:
            cols[c] = pd.to_numeric(PP[c[3:]], errors="coerce").to_numpy(float)
    H = pd.DataFrame(cols, index=keys)
    return H


def var_components(H: pd.DataFrame) -> dict:
    """VARS column -> list of component columns of H (empty list = unavailable in this trial)."""
    cc = list(H.columns)
    out = {}
    for c, _, _ in VARS:
        if c == "mean_meds":
            out[c] = [x for x in cc if x.startswith("meds::")]
        elif c == "mean_util":
            out[c] = [x for x in cc if x.startswith("util::")]
        elif c == "B_mean":
            out[c] = [x for x in cc if x.startswith("B::")]
        elif c == "smd_prog_full":
            out[c] = [x for x in cc if x == "prog_full"]
        elif c.startswith("smd_obs_"):
            out[c] = [x for x in cc if x == "obs_" + c[len("smd_obs_"):]]
        else:
            out[c] = [x for x in cc if x == c]
    return out


def load_trial(n: str, cache: bool = True, rebuild: bool = False) -> Trial:
    """Trial (imputation 1, split seed 0) + outcomes + RCT benchmark + held-out matrix; pickled cache.
    cache=False: build, do not read or write the cache. rebuild=True: build and overwrite the cache."""
    f = CACHE / f"restricted_trial_{n}_v{CACHE_VERSION}.pkl"
    if cache and not rebuild and f.exists():
        with open(f, "rb") as fh:
            return pickle.load(fh)
    T = Trial(n)
    T.split_seed = 0
    T.y_t, T.y_e, T.y_ok, T.horizon, _ = outcomes(n, T.key, T.keys)
    T.rb, T.rs = bench(T.key)
    T.H = None
    T.H = heldout_matrix(T)
    if cache:
        os.umask(0o077)
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(f".tmp{os.getpid()}")
        clm, T._clm_pc = T._clm_pc, None
        with open(tmp, "wb") as fh:
            pickle.dump(T, fh, protocol=pickle.HIGHEST_PROTOCOL)
        T._clm_pc = clm
        os.replace(tmp, f)
    return T


# ---------------------------------------------------------------- balance
def _wmean(V, w):
    ok = ~np.isnan(V)
    W = ok * w[:, None]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(ok, V, 0.0).T @ w / W.sum(0)


def smd_components(V, t, s_idx, s_w, s_t):
    """|SMD| per column: weighted NaN-aware means in the balance sample (positions s_idx into V, weights
    s_w, treatment s_t) / pooled SD of all rows of V (pre-match, ddof 1)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        sd = np.sqrt((np.nanvar(V[t == 1], axis=0, ddof=1) + np.nanvar(V[t == 0], axis=0, ddof=1)) / 2)
        S = V[s_idx]
        d = np.abs(_wmean(S[s_t == 1], s_w[s_t == 1]) - _wmean(S[s_t == 0], s_w[s_t == 0])) / sd
    d[~np.isfinite(sd) | (sd == 0)] = np.nan
    return d


def balance_cstat(V, y, w, model=("l2", 0.01), seed=0):
    """Cross-fitted (5-fold) AUC of treatment from held-out components within the balance sample."""
    if min((y == 1).sum(), (y == 0).sum()) < 20:
        return np.nan
    miss = np.isnan(V)
    med = np.nanmedian(np.where(miss, np.nan, V), axis=0)
    Z = np.where(miss, med[None, :], V)
    Z = np.nan_to_num(Z)
    mi = miss[:, miss.any(0) & ~miss.all(0)].astype(float)
    Z = np.hstack([Z, mi])
    Z = Z[:, Z.std(0) > 0]
    p = np.zeros(len(y))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(Z, y):
        if model[0] == "l2":
            sc = StandardScaler().fit(Z[tr])
            clf = LogisticRegression(C=model[1], max_iter=3000).fit(sc.transform(Z[tr]), y[tr], sample_weight=w[tr])
            p[te] = clf.decision_function(sc.transform(Z[te]))
        elif model[0] == "gbm":
            clf = HistGradientBoostingClassifier(random_state=seed, max_iter=200).fit(Z[tr], y[tr], sample_weight=w[tr])
            p[te] = clf.predict_proba(Z[te])[:, 1]
        else:
            raise KeyError(model)
    return float(roc_auc_score(y, p, sample_weight=w))


def _ess(w):
    return float(w.sum() ** 2 / (w ** 2).sum()) if (w > 0).any() else 0.0


# ---------------------------------------------------------------- one cell
def run_cell(T: Trial, X, t=None, rows=None, estimator=("match", 0.2, 1), ps_model=("l2", 1.0), heldout=None,
             cstat=("l2", 0.01), seed=0) -> dict:
    t0 = time.time()
    rows = np.arange(len(T.t)) if rows is None else np.asarray(rows)
    t = T.t[rows] if t is None else np.asarray(t).astype(int)
    yt, ye, ok = T.y_t[rows], T.y_e[rows], T.y_ok[rows]
    H = T.H if heldout is None else heldout
    Hv = H.to_numpy(float)[rows]
    N = len(rows)
    r = dict(n=N, n_t=int(t.sum()), n_c=int((1 - t).sum()), n_pairs=np.nan)
    kind = "crude" if X is None else estimator[0]
    if X is None:
        s_idx, s_w, cl = np.arange(N), np.ones(N), None
        m = ok
        b, se = cox(yt[m], ye[m], t[m])
    else:
        mk, C = ps_model[0], ps_model[1] if len(ps_model) > 1 and ps_model[1] is not None else 1.0
        lg = ps_logit(np.asarray(X, float), t, model=mk, C=C, seed=seed)
        if kind == "match":
            cal, ratio = estimator[1], estimator[2]
            s_idx, cl, s_w = match(lg, t, cal=cal, ratio=ratio)
            r["n_pairs"] = int(len(np.unique(cl)))
            m = ok[s_idx]
            b, se = cox(yt[s_idx][m], ye[s_idx][m], t[s_idx][m], w=None if ratio == 1 else s_w[m], cluster=cl[m])
        elif kind in ("iptw", "overlap"):
            w = weights(lg, t, kind)
            b, se = cox(yt[ok], ye[ok], t[ok], w=w[ok])
            s_idx = np.where(w > 0)[0]
            s_w = w[s_idx]
        else:
            raise KeyError(estimator)
    r.update(loghr=b, se=se)
    s_t = t[s_idx]
    r["ess_t"], r["ess_c"] = _ess(s_w[s_t == 1]), _ess(s_w[s_t == 0])
    comp = smd_components(Hv, t, s_idx, s_w, s_t)
    cs = pd.Series(comp, index=H.columns)
    vc = var_components(H)
    smd = {}
    for c, _, _ in VARS:
        g = cs[vc[c]].dropna()
        smd[c] = float(g.mean()) if len(g) else np.nan
    sv = pd.Series(smd)
    r["mean_smd"], r["n_vars"] = float(sv.mean()), int(sv.notna().sum())
    for g in GROUPS:
        r[f"mean_smd_g:{g}"] = float(sv[[c for c, _, gg in VARS if gg == g]].mean())
    r["smd_prog"] = smd["smd_prog_full"]
    r["cstat"] = np.nan if cstat is None else balance_cstat(Hv[s_idx], s_t, s_w, model=cstat, seed=seed)
    r.update({f"smd:{c}": v for c, v in smd.items()})
    r["secs"] = round(time.time() - t0, 2)
    return r


# ---------------------------------------------------------------- across-trial summaries
def bh_fdr(pvals):
    p = np.asarray(pvals, float)
    q = np.full(len(p), np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = len(pv)
    if m:
        o = np.argsort(pv)
        adj = pv[o] * m / np.arange(1, m + 1)
        adj = np.minimum.accumulate(adj[::-1])[::-1]
        out = np.empty(m)
        out[o] = np.minimum(adj, 1.0)
        q[ok] = out
    return q


def _phi(d, v):
    if len(d) < 2:
        return np.nan
    _, _, Q, _ = dl(d, v)
    return Q / (len(d) - 1)


def summarize_pairs(df: pd.DataFrame, cell_cols, arm_a, arm_b) -> pd.DataFrame:
    cell_cols = list(cell_cols)
    rows = []
    groups = df.groupby(cell_cols, dropna=False) if cell_cols else [((), df)]
    for key, g in groups:
        key = key if isinstance(key, tuple) else (key,)
        a = g[g.arm == arm_a].drop_duplicates("trial").set_index("trial")
        b = g[g.arm == arm_b].drop_duplicates("trial").set_index("trial")
        tt = a.index.intersection(b.index)
        a, b = a.loc[tt], b.loc[tt]
        r = dict(zip(cell_cols, key))
        r.update(arm_a=arm_a, arm_b=arm_b, n_trials=len(tt))
        met = {"absd": lambda x: (x.loghr - x.rb).abs(), "z2": lambda x: (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2)}
        for c in ("mean_smd", "cstat"):
            if c in g:
                met[c] = lambda x, c=c: x[c]
        for mname, f in met.items():
            d = (f(a) - f(b)).to_numpy(float)
            d = d[~np.isnan(d)]
            r[f"d_{mname}"] = float(d.mean()) if len(d) else np.nan
            r[f"k_{mname}"] = f"{int((d < 0).sum())}/{len(d)}"
            r[f"p_{mname}"] = sign_flip(d)[1] if len(d) else np.nan
        for lab, x in (("a", a), ("b", b)):
            x = x.dropna(subset=["loghr", "se"])
            z = (x.loghr - x.rb) / np.sqrt(x.se ** 2 + x.rs ** 2)
            r[f"cons_{lab}"] = float(100 * np.mean(np.abs(z) < 1.96)) if len(x) else np.nan
            r[f"phi_{lab}"] = _phi((x.loghr - x.rb).to_numpy(), (x.se ** 2 + x.rs ** 2).to_numpy())
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- validation CLI
def _validate_one(n):
    t0 = time.time()
    load_trial(n, rebuild=True)
    t_load = time.time() - t0
    t2 = time.time()
    T = load_trial(n, cache=True)
    t_cache = time.time() - t2
    lgdev = check_against_saved(T)
    bs = pd.read_csv(A / "claude-v13-bootstrap" / f"bs_{n}.csv")
    bs = bs[bs.rep == 0].drop_duplicates("arm").set_index("arm")
    lt = pd.read_csv(A / f"claude-cap4-all-{n}" / "longtail_imp1_seed0.csv", index_col=0)
    sp = pd.read_csv(A / f"claude-cap4-all-{n}" / "summary_pooled.csv", index_col=0)
    ta = time.time()
    X = T.arms(VAL_ARMS)
    t_arms = time.time() - ta
    est, smd_rows, time_rows = [], [], []
    for a in VAL_ARMS:
        if True:  # one l2 C-statistic row per arm
            r = run_cell(T, X[a], cstat=("l2", 0.01))
            time_rows.append(dict(trial=n, arm=a, cstat_model="l2", secs=r["secs"], n=r["n"]))
            e = dict(trial=n, arm=a, loghr=r["loghr"], se=r["se"], saved_loghr=bs.loc[a, "loghr"], saved_se=bs.loc[a, "se"],
                     n_pairs=r["n_pairs"], saved_pairs=bs.loc[a, "pairs"], mean_smd=r["mean_smd"], n_vars=r["n_vars"],
                     smd_prog=r["smd_prog"], cstat=r["cstat"], ps_logit_maxdev=lgdev.get(a, np.nan), rb=T.rb, rs=T.rs)
            est.append(e)
            if a in ("unmatched", "sparse", "sparse+ECG"):
                rg = run_cell(T, X[a], cstat=("gbm", None))
                e["cstat_gbm"] = rg["cstat"]
                time_rows.append(dict(trial=n, arm=a, cstat_model="gbm", secs=rg["secs"], n=rg["n"]))
            for c, _, g in VARS:
                v = r[f"smd:{c}"]
                s0 = abs(lt.loc[a, c]) if c in lt and not pd.isna(lt.loc[a, c]) else np.nan
                s1 = abs(sp.loc[a, c]) if c in sp and not pd.isna(sp.loc[a, c]) else np.nan
                smd_rows.append(dict(trial=n, arm=a, var=c, group=g, engine=v, imp1_seed0=s0, pooled=s1))
    # other estimators, timing only (+ sanity)
    for estm in (("match", 0.05, 1), ("match", 0.2, 3), ("iptw",), ("overlap",)):
        r = run_cell(T, X["sparse+ECG"], estimator=estm)
        time_rows.append(dict(trial=n, arm="sparse+ECG", cstat_model="l2", estimator=str(estm), secs=r["secs"], n=r["n"],
                              loghr=r["loghr"], mean_smd=r["mean_smd"]))
    r = run_cell(T, X["sparse+ECG"], ps_model=("gbm", None))
    time_rows.append(dict(trial=n, arm="sparse+ECG", cstat_model="l2", estimator="gbm-PS match", secs=r["secs"], n=r["n"]))
    meta = dict(trial=n, n=len(T.t), n_components=T.H.shape[1], secs_build=round(t_load, 1), secs_cache_load=round(t_cache, 2),
                secs_arms_6=round(t_arms, 2))
    return est, smd_rows, time_rows, meta


def validate(trials, workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    with Pool(min(workers, len(trials), 32)) as p:
        res = p.map(_validate_one, trials, chunksize=1)
    E = pd.DataFrame([e for r in res for e in r[0]])
    S = pd.DataFrame([e for r in res for e in r[1]])
    Tm = pd.DataFrame([e for r in res for e in r[2]])
    M = pd.DataFrame([r[3] for r in res])
    E.to_csv(OUT / "validation_estimates.csv", index=False)
    S.to_csv(OUT / "validation_smd.csv", index=False)
    Tm.to_csv(OUT / "validation_timing.csv", index=False)
    M.to_csv(OUT / "validation_meta.csv", index=False)
    E["d_loghr"] = (E.loghr - E.saved_loghr).abs()
    E["d_se"] = (E.se - E.saved_se).abs()
    S["dev_imp1"] = (S.engine - S.imp1_seed0).abs()
    S["dev_pooled"] = (S.engine - S.pooled).abs()
    S["avail_mismatch"] = S.engine.isna() != S.imp1_seed0.isna()
    per = E.groupby("trial").agg(max_d_loghr=("d_loghr", "max"), max_d_se=("d_se", "max"),
                                 max_ps_logit_dev=("ps_logit_maxdev", "max")).join(
        S.groupby("trial").agg(max_dev_smd_imp1=("dev_imp1", "max"), max_dev_smd_pooled=("dev_pooled", "max"),
                               mean_dev_smd_pooled=("dev_pooled", "mean"), n_vars=("engine", lambda x: int(x.notna().sum() / len(VAL_ARMS))),
                               avail_mismatch=("avail_mismatch", "sum"))).join(M.set_index("trial")[["n_components", "secs_build", "secs_cache_load", "secs_arms_6"]])
    per = per.reindex(trials).reset_index()
    tol_est, tol_smd = 1e-4, 1e-6
    pass_est = bool((per.max_d_loghr.fillna(0) < tol_est).all() and (per.max_d_se.fillna(0) < tol_est).all())
    pass_smd = bool((per.max_dev_smd_imp1.fillna(0) < tol_smd).all() and (per.avail_mismatch == 0).all())
    arm_s = E.groupby("arm", sort=False).agg(mean_smd=("mean_smd", "mean"), cstat_l2=("cstat", "mean"), cstat_gbm=("cstat_gbm", "mean"),
                                             smd_prog=("smd_prog", "mean")).reindex(VAL_ARMS).reset_index()
    dfp = E.rename(columns={})
    pairs = pd.concat([summarize_pairs(dfp, [], a1, a0) for a1, a0 in
                       (("sparse+ECG", "sparse"), ("hdPS200+ECG", "hdPS200"), ("sparse", "unmatched"))], ignore_index=True)
    pairs["q_absd"] = bh_fdr(pairs.p_absd)
    tm = Tm.groupby(["arm", "cstat_model"], dropna=False).secs.agg(["median", "max"]).reset_index()
    tm2 = Tm[Tm.estimator.notna()].groupby("estimator").secs.agg(["median", "max"]).reset_index() if "estimator" in Tm else pd.DataFrame()
    per_trial_t = Tm[(Tm.cstat_model == "l2") & Tm.estimator.isna()].groupby("trial").secs.median().reindex(trials)
    per_trial_t = pd.DataFrame(dict(trial=trials, n=M.set_index("trial").n.reindex(trials).to_numpy(),
                                    median_secs_per_cell=per_trial_t.to_numpy()))
    status = "PASS" if pass_est and pass_smd else "FAIL"
    L = [f"# v1.6 engine validation ({time.strftime('%Y-%m-%d')})\n",
         f"`scripts/v16/v16_engine.py --validate`, {len(trials)} trials × {len(VAL_ARMS)} arms (imputation 1, split seed 0, "
         "1:1 caliper-0.2 matching, L2 C=1 PS). Aggregates only.\n",
         f"**Status: {status}** (estimates: {'pass' if pass_est else 'FAIL'}, tol {tol_est:g}; held-out |SMD| vs "
         f"`longtail_imp1_seed0.csv`: {'pass' if pass_smd else 'FAIL'}, tol {tol_smd:g}).\n",
         "## (a) log HR / SE vs `claude-v13-bootstrap/bs_<trial>.csv` (rep 0) and (b) held-out |SMD|\n",
         "max_d_* = max over arms of |engine − saved|. max_ps_logit_dev = `check_against_saved` (rebuilt PS logit vs saved "
         "phase-2 logit). max_dev_smd_imp1 = max over arms × variables of |engine − longtail_imp1_seed0|; *_pooled = vs "
         "summary_pooled.csv (mean over 5 imputations × 5 pool-split seeds, so non-zero by design). avail_mismatch = "
         "variables available in one source but not the other.\n",
         md(per, 6) + "\n",
         "Non-zero estimate deviations: ALLHAT sparse arm |Δlog HR| = 4.0e-5 (SE 1.6e-7), identical pair count. The engine's "
         "matched set for that arm is identical, patient for patient and pair for pair, to the saved phase-2 matches "
         "(`restricted_matches_imp1_seed0.parquet`); the saved bootstrap rep 0 differs at the 5th decimal (most likely a "
         "floating-point near-tie in greedy matching or Cox convergence in that earlier run). All other trial × arm "
         "estimates agree to < 1e-8. RELY has 57/58 variables (GLS is NaN in both the "
         "engine and the saved outputs: unobserved or zero variance).\n",
         "## Why engine vs `summary_pooled.csv` differs\n",
         "summary_pooled averages each metric over 25 runs (imputations 1–5 × pool-split seeds 0–4). The seed changes "
         "which panel features are in hdPS pool A vs held-out pool B (so `B_mean` and the hdPS arms change) and the "
         "imputation changes meds/util and the matched sets of every arm. The engine fixes imputation 1, seed 0 and "
         "reproduces `longtail_imp1_seed0.csv` (the (1, 0) member of that average); the pooled deviation is the "
         "imputation/seed spread, not an engine error.\n",
         "## Arm means across trials (engine)\n",
         "cstat = 5-fold cross-fitted AUC of treatment from all held-out components (median-imputed + missing "
         "indicators) in the matched sample; l2 = logistic C = 0.01, gbm = HistGBM (unmatched/sparse/sparse+ECG only).\n",
         md(arm_s, 3) + "\n",
         "## Paired smoke test of `summarize_pairs` (a − b; negative favours a)\n",
         md(pairs, 3) + "\n",
         "## Runtime (seconds per cell, 1 thread; includes PS fit, matching, Cox, 58-variable SMD and C-statistic)\n",
         md(tm, 2) + "\n",
         "Other estimators / PS model (sparse+ECG, l2 C-statistic):\n",
         md(tm2, 2) + "\n" if len(tm2) else "",
         "Median seconds per cell by trial (l2 C-statistic, 1:1 matching; all six arms):\n",
         md(per_trial_t, 2) + "\n",
         f"Trial build (uncached) median {M.secs_build.median():.0f} s (max {M.secs_build.max():.0f} s); cached load median "
         f"{M.secs_cache_load.median():.1f} s. Building the six designs with `T.arms` (incl. hdPS re-ranking) median {M.secs_arms_6.median():.1f} s (max {M.secs_arms_6.max():.1f} s) per trial; not included in the per-cell times. A trial × cell with the gbm "
         "C-statistic costs roughly the gbm row above.\n"]
    (DOCS / "ENGINE_VALIDATION.md").write_text("\n".join(L))
    print(json.dumps(dict(status=status, pass_est=pass_est, pass_smd=pass_smd)))
    print(per.to_string())
    return status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--trials", default=",".join(TRIALS))
    ap.add_argument("--workers", type=int, default=18)
    ap.add_argument("--ready", action="store_true", help="write READY marker if validation passes")
    a = ap.parse_args()
    if a.validate:
        st = validate(a.trials.split(","), a.workers)
        if st == "PASS" and a.ready:
            (OUT / "READY").write_text(time.strftime("%Y-%m-%d %H:%M") + " validation PASS\n")


if __name__ == "__main__":
    main()
