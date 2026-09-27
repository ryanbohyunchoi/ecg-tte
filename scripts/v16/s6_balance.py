#!/usr/bin/env python
"""v1.6 sweep S6: extended held-out balance measures, ECG vs no-ECG (docs/V16_SWEEP_PLAN.md, exploratory).

Rungs (base PS designs); each run as base, base+ECG (32 BCL PCs), base+shufECG (same PCs, rows permuted with
T.shuffle_perm), base+noise32 (T.noise32); plus unmatched once per trial/half.
   demo           age, sex, index_year (T.demo)                         (= S1 r1_demo)
   min7           age, sex, race block, t2d, cad_ihd, hypertension_v11, hyperlipidemia (claude-v16-covars; = S1 r3_min7)
   sparse         T.X_dx                                                (= S1 r5_sparse)
   sparse_drop50  D.X_dx with D = T.degraded(0.5, seed 0); balance on the TRUE (undegraded) held-out matrix
   hdPS200        sparse + top-200 hdPS levels ranked on the analysed rows' treatment (= S1 r7_hdPS200)
   clinical       T.X_core; panel components in the PS (meds, util, observed vitals/labs of T.phys) are
                  excluded from every S6 measure (engine mean_smd / cstat are reported as is, plus *_ho)
Estimator: 1:1 greedy caliper-0.2 matching on an L2 (C=1) logistic PS (engine defaults). Halves: full, A, B.

The matched sample for the extra measures comes from `matched_sample` (replicates run_cell's ps_logit + match;
n_pairs and the engine mean |SMD| recomputed from it are checked against run_cell for every cell).

Held-out panel: the engine matrix T.H (58 variables) and optionally an EXTRA held-out DataFrame (index =
patient_key, numeric columns; `--extra DIR` reads DIR/<trial>.parquet). Extra columns are added as components
"X::<col>"; per cell, any extra column that is in (or a named proxy of) that cell's PS is dropped (PS_NAMES,
PROXY). Output column `panel` = "p58" or "x<name>".

Measures (matched sample, lower = better):
 a. outcome-weighted imbalance. Ridge logistic model of the primary event by horizon (T.y_e, rows with T.y_ok)
    on Z_all (all held-out components, median-imputed + missingness indicators, standardised by the pooled
    within-arm SD of the analysed rows), fitted in the COMPARATOR arm of the analysed (unmatched) rows; C chosen
    by 3-fold CV log-loss over CGRID. Δ_j = treated − comparator mean of Z_j in the matched sample.
      ob_signed = |Σ β_j Δ_j| (logit units), ob_abs = Σ |β_j||Δ_j|,
      prog_ho_smd = |SMD| of the held-out prognostic score (5-fold cross-fitted in comparators, full-fit for
      treated), pooled SD of the score in the analysed rows.
 b. distributional (Z_core = non-B components): vr_logdev = mean |log(var_T/var_C)| over continuous components
    (observed values, winsorised 1/99 pct; ≥ 50 observed per arm), ks_mean = mean two-sample KS statistic over the same; energy = energy distance
    (V-statistic) of standardised Z_core between arms, ≤ 5,000 per arm (seeded subsample). Permutation p for
    energy (2,000 per arm, 200 perms) in PERM_TRIALS (full cohort).
 c. missingness balance: |SMD| of "measured" indicators: echo_done (T.echo_any; echo masked before ECHO_START),
    BNP done, each lab done (pp_LAB__*, obs_ creatinine/potassium/sodium/hemoglobin), vitals done
    (obs_ sbp/dbp/heart_rate/bmi/lvef). miss_mean (all), miss_echo, miss_bnp, miss_lab.
 d. subgroup balance: mean |SMD| over the 58 variables (+ extras) within age ≥ 65, < 65, male, female strata of
    the matched sample (pooled SD of analysed rows); sub_smd = mean of the 4 strata, sub_max = max.
 e. Mahalanobis: maha_all / maha_core = sqrt(Δ' (S + λI)^-1 Δ) on Z_all / Z_core, S = pooled within-arm
    covariance of the analysed rows, λ = LAMBDA.
Engine metrics (absd, z2, mean_smd, cstat) are carried through from run_cell.

Inference (summarize): paired exact sign-flip over trials (E.summarize_pairs) for ECG vs base / shufECG / noise;
comparator-clustered sign-flip (audit_v16.CLUSTER), leave-one-trial-out max p, halves, placebo rule,
BH-FDR per metric over rungs and within measure family (metrics × rungs).

Usage: s6_balance.py run [--trials a,b] [--workers 40] [--extra DIR --panel NAME] [--out DIR]
       s6_balance.py summarize [--out DIR] [--doc]
Aggregates only.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import ks_2samp  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v16_engine as E  # noqa: E402
from audit_v16 import CLUSTER  # noqa: E402
from v13_common import match, ps_logit, weights  # noqa: E402
from v13_summarize import md  # noqa: E402
from v13_summarize import sign_flip as _sign_flip_ref  # noqa: E402
from functools import lru_cache  # noqa: E402
import itertools  # noqa: E402


@lru_cache(None)
def _flips(k):
    return np.array(list(itertools.product([-1, 1], repeat=k)), dtype=np.float64)


def sign_flip(d):
    """Same statistic and exact p as v13_summarize.sign_flip (k <= 20), with cached sign matrices."""
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    if len(d) > 20:
        return _sign_flip_ref(d)
    obs = d.mean()
    null = _flips(len(d)) @ np.abs(d) / len(d)
    return float(obs), float(np.mean(np.abs(null) >= abs(obs) - 1e-12))


E.sign_flip = sign_flip  # used by E.summarize_pairs

SWEEP = "s6-balance"
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s6-balance")
DOCS = HERE.parent.parent / "docs" / "v16"
COV = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars")
COV2 = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars2")
RACE = ["race_black", "race_asian", "race_other_unknown", "hispanic", "ethnicity_unknown"]
MIN7 = ["t2d", "cad_ihd", "hypertension_v11", "hyperlipidemia"]
CELLS = [("demo", "demo"), ("min7", "minimal-7"), ("sparse", "sparse"), ("sparse_drop50", "sparse, 50% code dropout"),
         ("hdPS200", "hdPS200"), ("clinical", "clinical")]
CELL_LAB = dict(CELLS)
CELL_POS = {c: i for i, (c, _) in enumerate(CELLS)}
ROLES = ["base", "ECG", "shufECG", "noise"]
CGRID = [1e-4, 3e-4, 0.001, 0.003, 0.01, 0.03, 0.1]
LAMBDA = 0.1
NMAX_E, NPERM_SUB, NPERM = 5000, 2000, 200
PERM_TRIALS = ["comet", "plato", "rely", "empa-reg"]
# names in a PS -> extra (held-out) columns that are the same construct or a near-copy (dropped for that cell)
PROXY = {"diabetes": ["t2d", "diabetes_v11", "diabetes_any"], "t2d": ["diabetes_v11", "diabetes"],
         "hypertension": ["hypertension_v11"], "hypertension_v11": ["hypertension"],
         "ischemic_heart_disease_or_mi": ["cad_ihd"], "cad_ihd": ["ischemic_heart_disease_or_mi"],
         "hospital_admissions": ["hospital_admissions_v11", "inpatient_days_365"],
         "hyperlipidemia": ["hld_or_statin"], "bmi": ["obesity"],
         "race_black": ["race_white", "race_unknown", "race_multiple"], "hispanic": ["ethnicity_unknown"],
         "statin_order": ["statin_order_90d"], "age_at_index": ["charlson_age_score"]}
FAMILY = {"a": ["ob_signed", "ob_abs", "prog_ho_smd"], "b": ["vr_logdev", "ks_mean", "energy"],
          "c": ["miss_mean", "miss_echo", "miss_bnp", "miss_lab"], "d": ["sub_smd", "sub_max"],
          "e": ["maha_all", "maha_core"], "rct": ["absd", "z2"], "engine": ["mean_smd", "cstat", "mean_smd_ho", "cstat_ho"],
          "x": ["xsmd", "xsmd_other", "xsmd_prox"]}
FAM_LAB = {"a": "a. outcome-weighted", "b": "b. distributional", "c": "c. missingness", "d": "d. subgroup",
           "e": "e. Mahalanobis", "rct": "RCT agreement (reference)", "engine": "engine balance (reference)", "x": "extra-panel mean |SMD|"}
MLAB = {"ob_signed": "|Σβ·Δ| (logit)", "ob_abs": "Σ|β||Δ|", "prog_ho_smd": "held-out prognostic score |SMD|",
        "vr_logdev": "mean |log VR|", "ks_mean": "mean KS", "energy": "energy distance",
        "miss_mean": "missingness |SMD| (all)", "miss_echo": "echo-done |SMD|", "miss_bnp": "BNP-done |SMD|",
        "miss_lab": "lab-done |SMD| (mean)", "sub_smd": "subgroup mean |SMD| (4 strata)", "sub_max": "worst stratum mean |SMD|",
        "maha_all": "Mahalanobis (all comp.)", "maha_core": "Mahalanobis (core comp.)", "absd": "|Δlog HR| vs RCT",
        "z2": "z² vs RCT", "mean_smd": "58-var mean |SMD| (engine)", "cstat": "held-out C (engine)",
        "mean_smd_ho": "58-var |SMD|, held-out-from-PS", "cstat_ho": "C, held-out-from-PS", "xsmd": "extra covariates mean |SMD|",
        "xsmd_other": "extra, non-ECG-proximal mean |SMD|", "xsmd_prox": "extra, ECG-proximal mean |SMD|"}
METRICS = [m for f in ("rct", "engine", "a", "b", "c", "d", "e", "x") for m in FAMILY[f]]
LAB_VARS = ["obs_creatinine", "obs_potassium", "obs_sodium", "obs_hemoglobin"]
VIT_VARS = ["obs_sbp", "obs_dbp", "obs_heart_rate", "obs_bmi", "obs_lvef"]


def halves(T, i):
    """full / A / B row positions; A/B = seeded split stratified by treatment (as S1/S2)."""
    rng = np.random.default_rng(16060 + i)
    A = []
    for g in (0, 1):
        idx = np.where(T.t == g)[0]
        idx = idx[rng.permutation(len(idx))]
        A.append(idx[: len(idx) // 2])
    A = np.sort(np.concatenate(A))
    B = np.setdiff1d(np.arange(len(T.t)), A)
    return {"full": np.arange(len(T.t)), "A": A, "B": B}


def load_new(T):
    C = pd.read_parquet(COV / f"{T.n}.parquet").set_index("patient_key").reindex(T.keys)
    assert C.treated.astype(int).to_numpy().tolist() == T.t.tolist()
    return C


def _split(x):
    return {v.strip() for v in str(x).replace(";", ",").split(",") if v.strip()} if isinstance(x, str) else set()


def load_extra(T, d: Path):
    """Extra held-out panel for T.keys from d/<trial>.parquet (numeric columns except ids / treatment).
    If d has dictionary.csv / trial_variable_status.csv (claude-v16-covars2): keep only status 'kept*' for this
    trial and drop any variable with status *leak* / dropped* or exposure_leak == yes (e.g. INR in warfarin trials), and collect per variable the PS core variables it
    partly duplicates (dictionary ps_overlap_candidates + per-trial 'PS overlap: ...' note) and its block tag.
    Returns (X, overlap: {col: set}, block: {col: str})."""
    X = pd.read_parquet(d / f"{T.n}.parquet")
    if "patient_key" in X.columns:
        X = X.set_index("patient_key")
    X = X[~X.index.duplicated()].reindex(T.keys)
    if "treated" in X:
        tr = X.pop("treated")
        ok = tr.notna()
        assert (tr[ok].astype(int).to_numpy() == T.t[ok.to_numpy()]).all()
    drop = [c for c in X.columns if c in ("person_id", "index_date", "patient_key") or not pd.api.types.is_numeric_dtype(X[c])]
    X = X.drop(columns=drop).astype(float)
    overlap = {c: set() for c in X.columns}
    block = {c: "other" for c in X.columns}
    if (d / "trial_variable_status.csv").exists():
        st = pd.read_csv(d / "trial_variable_status.csv")
        st = st[st.trial == T.n]
        kept = set(st[st.status.astype(str).str.startswith("kept")].variable)
        leak = set(st[st.status.astype(str).str.contains("leak") | st.status.astype(str).str.startswith("dropped")].variable)
        if "exposure_leak" in st:
            leak |= set(st[st.exposure_leak.astype(str).str.lower().isin(["yes", "true", "1"])].variable)
        X = X[[c for c in X.columns if c in kept and c not in leak]]
        for v, note in zip(st.variable, st.note):
            if v in overlap and isinstance(note, str) and note.startswith("PS overlap:"):
                overlap[v] |= _split(note[len("PS overlap:"):])
        if "ps_overlap" in st:
            for v, po in zip(st.variable, st.ps_overlap):
                if v in overlap:
                    overlap[v] |= _split(po)
    if (d / "dictionary.csv").exists():
        dic = pd.read_csv(d / "dictionary.csv").set_index("variable")
        for v in X.columns:
            if v in dic.index:
                if "ps_overlap_candidates" in dic:
                    overlap[v] |= _split(dic.loc[v, "ps_overlap_candidates"])
                if "block" in dic and isinstance(dic.loc[v, "block"], str):
                    block[v] = dic.loc[v, "block"]
                for lc in [c for c in dic.columns if "leak" in c.lower()]:  # optional per-trial leak tag
                    if T.n in _split(dic.loc[v, lc]) or str(dic.loc[v, lc]).lower() in ("true", "1", "all"):
                        X = X.drop(columns=[v])
                        break
    overlap = {c: overlap[c] for c in X.columns}
    block = {c: block[c] for c in X.columns}
    return X, overlap, block


# ---------------------------------------------------------------- designs
def base_designs(T, C, D, rows, t):
    """cell -> (X, PS source names, 58-panel VARS excluded). D = T.degraded(0.5, 0)."""
    cov = T.cov.iloc[rows]
    m7 = np.hstack([cov[["age_at_index", "male"]].to_numpy(float), C[RACE].to_numpy(float)[rows], C[MIN7].to_numpy(float)[rows]])
    dx = T.X_dx[rows]
    Hk = T.hd(200, t=t, rows=rows)
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    dxn = T.demo + T.dxc
    return {"demo": (cov[T.demo].to_numpy(float), list(T.demo), set()),
            "min7": (m7, ["age_at_index", "male"] + RACE + MIN7 + ["diabetes", "ischemic_heart_disease_or_mi", "hypertension"], set()),
            "sparse": (dx, dxn, set()),
            "sparse_drop50": (D.X_dx[rows], dxn, set()),
            "hdPS200": (np.hstack([dx, Hk]), dxn, set()),
            "clinical": (T.X_core[rows], list(T.core), clin_ex)}


def excluded_extra(ps_names, extra_cols, overlap=None):
    """Extra columns dropped for a cell: same name as a PS variable, a PROXY of one, or tagged as partly
    duplicating a PS variable of this cell (overlap)."""
    ex = set(ps_names)
    for nm in ps_names:
        ex |= set(PROXY.get(nm, []))
    ps = set(ps_names)
    overlap = overlap or {}
    return [c for c in extra_cols if c in ex or (overlap.get(c, set()) & ps)]


# ---------------------------------------------------------------- matched sample helper
def matched_sample(X, t, estimator=("match", 0.2, 1), ps_model=("l2", 1.0), seed=0):
    """Replicates E.run_cell's PS fit + match/weights. Returns (s_idx, s_w, cluster, n_pairs); X None = unmatched."""
    N = len(t)
    if X is None:
        return np.arange(N), np.ones(N), None, np.nan
    mk, C = ps_model[0], ps_model[1] if len(ps_model) > 1 and ps_model[1] is not None else 1.0
    lg = ps_logit(np.asarray(X, float), t, model=mk, C=C, seed=seed)
    if estimator[0] == "match":
        s_idx, cl, s_w = match(lg, t, cal=estimator[1], ratio=estimator[2])
        return s_idx, s_w, cl, int(len(np.unique(cl)))
    w = weights(lg, t, estimator[0])
    s_idx = np.where(w > 0)[0]
    return s_idx, w[s_idx], None, np.nan


# ---------------------------------------------------------------- per-(trial, half, varset) preparation
def _impute_std(V, t):
    miss = np.isnan(V)
    keep = ~miss.all(0)
    V, miss = V[:, keep], miss[:, keep]
    med = np.nanmedian(V, axis=0)
    Z = np.where(miss, med[None, :], V)
    mi = miss[:, miss.any(0)].astype(float)
    Z = np.hstack([Z, mi])
    mu = Z.mean(0)
    sd = np.sqrt((Z[t == 1].var(0, ddof=1) + Z[t == 0].var(0, ddof=1)) / 2)
    ok = np.isfinite(sd) & (sd > 0)
    return (Z[:, ok] - mu[ok]) / sd[ok]


def _pooled_cov_inv(Z, t):
    Zc = Z.copy()
    for g in (0, 1):
        Zc[t == g] -= Zc[t == g].mean(0)
    S = Zc.T @ Zc / (len(t) - 2)
    return np.linalg.inv(S + LAMBDA * np.eye(S.shape[0]))


def _fit_outcome(Z, y, fitmask, seed=0):
    """Ridge logistic in rows fitmask; C by 3-fold CV log-loss. Returns (beta, lp_crossfit, C)."""
    Zf, yf = Z[fitmask], y[fitmask]
    if min(yf.sum(), (1 - yf).sum()) < 20:
        return None, None, np.nan
    best, bC = np.inf, CGRID[0]
    for C in CGRID:
        ll = 0.0
        for tr, te in StratifiedKFold(3, shuffle=True, random_state=seed).split(Zf, yf):
            m = LogisticRegression(C=C, max_iter=2000).fit(Zf[tr], yf[tr])
            p = np.clip(m.predict_proba(Zf[te])[:, 1], 1e-9, 1 - 1e-9)
            ll -= np.sum(yf[te] * np.log(p) + (1 - yf[te]) * np.log(1 - p))
        if ll < best:
            best, bC = ll, C
    full = LogisticRegression(C=bC, max_iter=2000).fit(Zf, yf)
    lp = Z @ full.coef_[0] + full.intercept_[0]
    idx = np.where(fitmask)[0]
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(Zf, yf):
        m = LogisticRegression(C=bC, max_iter=2000).fit(Zf[tr], yf[tr])
        lp[idx[te]] = Zf[te] @ m.coef_[0] + m.intercept_[0]
    return full.coef_[0], lp, bC


class Prep:
    """Held-out matrices for one (trial, half, varset): Hdf = component DataFrame (analysed rows)."""

    def __init__(self, T, rows, t, Hdf, extra_cols, seed):
        self.t = t
        self.cols = list(Hdf.columns)
        V = Hdf.to_numpy(float)
        self.V = V
        self.core_cols = [c for c in self.cols if not c.startswith("B::")]
        ci = [self.cols.index(c) for c in self.core_cols]
        self.Zall = _impute_std(V, t)
        self.Zcore = _impute_std(V[:, ci], t)
        self.Sinv_all = _pooled_cov_inv(self.Zall, t)
        self.Sinv_core = _pooled_cov_inv(self.Zcore, t)
        ye = T.y_e[rows].astype(int)
        ok = T.y_ok[rows].astype(bool)
        self.beta, self.lp, self.C = _fit_outcome(self.Zall, ye, ok & (t == 0), seed=seed)
        if self.lp is not None:
            self.lp_sd = np.sqrt((self.lp[t == 1].var(ddof=1) + self.lp[t == 0].var(ddof=1)) / 2)
        # continuous core components (observed-only values)
        self.cont = [j for j in ci if len(np.unique(V[~np.isnan(V[:, j]), j])) > 2]
        # winsorised copy (1st/99th pct of analysed rows) for variance ratios
        with np.errstate(invalid="ignore"):
            lo, hi = np.nanpercentile(V[:, self.cont], 1, axis=0), np.nanpercentile(V[:, self.cont], 99, axis=0)
        self.Vw = {j: np.clip(V[:, j], lo[k], hi[k]) for k, j in enumerate(self.cont)}
        # missingness indicators
        mcols = {}
        mcols["echo_done"] = T.echo_any[rows].astype(float)
        if "pp_BNP__ntprobnp" in self.cols:
            mcols["bnp_done"] = (~np.isnan(V[:, self.cols.index("pp_BNP__ntprobnp")])).astype(float)
        for c in self.cols:
            if c.startswith("pp_LAB__") or c in LAB_VARS:
                mcols[f"lab_done:{c}"] = (~np.isnan(V[:, self.cols.index(c)])).astype(float)
            elif c in VIT_VARS:
                mcols[f"vit_done:{c}"] = (~np.isnan(V[:, self.cols.index(c)])).astype(float)
            elif c.startswith("X::") and np.isnan(V[:, self.cols.index(c)]).any():
                mcols[f"x_done:{c}"] = (~np.isnan(V[:, self.cols.index(c)])).astype(float)
        self.mnames = list(mcols)
        self.M = np.column_stack([mcols[k] for k in self.mnames])
        # component -> variable groups for (sub)group SMD: 58 VARS + each extra column as its own variable
        vc = E.var_components(Hdf)
        self.vgroups = [[self.cols.index(x) for x in vc[c]] for c, _, _ in E.VARS if vc[c]]
        self.xidx = [self.cols.index(c) for c in self.cols if c.startswith("X::")]
        self.vgroups += [[j] for j in self.xidx]
        with np.errstate(invalid="ignore", divide="ignore"):
            self.sd = np.sqrt((np.nanvar(V[t == 1], axis=0, ddof=1) + np.nanvar(V[t == 0], axis=0, ddof=1)) / 2)
        self.age65 = T.cov.age_at_index.to_numpy()[rows] >= 65
        self.male = T.cov.male.to_numpy()[rows] > 0.5
        self.erng_seed = seed


def _smd_vec(V, sd, s_idx, s_w, s_t):
    S = V[s_idx]
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.abs(E._wmean(S[s_t == 1], s_w[s_t == 1]) - E._wmean(S[s_t == 0], s_w[s_t == 0])) / sd
    d[~np.isfinite(sd) | (sd == 0)] = np.nan
    return d


def _var_mean(comp, groups):
    vals = [np.nanmean(comp[g]) if np.isfinite(comp[g]).any() else np.nan for g in groups]
    vals = np.array(vals, float)
    return float(np.nanmean(vals)) if np.isfinite(vals).any() else np.nan


def _dist_sum(A, B):
    """Sum of Euclidean distances between rows of A and B (chunked)."""
    a2 = (A ** 2).sum(1)
    b2 = (B ** 2).sum(1)
    s = 0.0
    for i in range(0, len(A), 1000):
        G = a2[i:i + 1000, None] + b2[None, :] - 2 * A[i:i + 1000] @ B.T
        s += np.sqrt(np.maximum(G, 0)).sum()
    return s


def energy_distance(X, Y):
    return 2 * _dist_sum(X, Y) / (len(X) * len(Y)) - _dist_sum(X, X) / len(X) ** 2 - _dist_sum(Y, Y) / len(Y) ** 2


def energy_perm(X, Y, nperm=NPERM, seed=0):
    Z = np.vstack([X, Y])
    z2 = (Z ** 2).sum(1)
    D = np.sqrt(np.maximum(z2[:, None] + z2[None, :] - 2 * Z @ Z.T, 0))
    n1 = len(X)
    rng = np.random.default_rng(seed)

    def stat(lab):
        a = lab.astype(float)
        b = 1 - a
        na, nb = a.sum(), b.sum()
        Da = D @ a
        return 2 * (b @ Da) / (na * nb) - (a @ Da) / na ** 2 - (b @ (D @ b)) / nb ** 2

    lab0 = np.r_[np.ones(n1), np.zeros(len(Y))].astype(bool)
    obs = stat(lab0)
    null = np.array([stat(rng.permutation(lab0)) for _ in range(nperm)])
    return float(obs), float((1 + (null >= obs).sum()) / (nperm + 1))


def measures(P: Prep, s_idx, s_w, perm=False):
    t = P.t
    s_t = t[s_idx]
    r = {}
    T1, T0 = s_idx[s_t == 1], s_idx[s_t == 0]
    w1, w0 = s_w[s_t == 1], s_w[s_t == 0]

    def dmean(Z):
        return (w1 @ Z[T1]) / w1.sum() - (w0 @ Z[T0]) / w0.sum()

    # a. outcome-weighted
    if P.beta is not None:
        dl = dmean(P.Zall)
        r["ob_signed"] = float(abs(P.beta @ dl))
        r["ob_abs"] = float(np.abs(P.beta) @ np.abs(dl))
        dlp = (w1 @ P.lp[T1]) / w1.sum() - (w0 @ P.lp[T0]) / w0.sum()
        r["prog_ho_smd"] = float(abs(dlp) / P.lp_sd)
        r["outcome_C"] = P.C
    else:
        r.update(ob_signed=np.nan, ob_abs=np.nan, prog_ho_smd=np.nan, outcome_C=np.nan)
    # e. Mahalanobis
    da, dc = dmean(P.Zall), dmean(P.Zcore)
    r["maha_all"] = float(np.sqrt(max(da @ P.Sinv_all @ da, 0)))
    r["maha_core"] = float(np.sqrt(max(dc @ P.Sinv_core @ dc, 0)))
    # b. distributional (observed values; matching weights are 1)
    lv, ks = [], []
    for j in P.cont:
        x1, x0 = P.V[T1, j], P.V[T0, j]
        x1, x0 = x1[~np.isnan(x1)], x0[~np.isnan(x0)]
        if len(x1) < 50 or len(x0) < 50:
            continue
        w1_, w0_ = P.Vw[j][T1], P.Vw[j][T0]
        v1, v0 = np.nanvar(w1_, ddof=1), np.nanvar(w0_, ddof=1)
        if v1 > 0 and v0 > 0:
            lv.append(abs(np.log(v1 / v0)))
        ks.append(ks_2samp(x1, x0).statistic)
    r["vr_logdev"] = float(np.mean(lv)) if lv else np.nan
    r["ks_mean"] = float(np.mean(ks)) if ks else np.nan
    r["n_cont"] = len(ks)
    rng = np.random.default_rng(P.erng_seed)
    s1 = T1 if len(T1) <= NMAX_E else rng.choice(T1, NMAX_E, replace=False)
    s0 = T0 if len(T0) <= NMAX_E else rng.choice(T0, NMAX_E, replace=False)
    r["energy"] = float(energy_distance(P.Zcore[s1], P.Zcore[s0]))
    if perm:
        rng2 = np.random.default_rng(P.erng_seed + 1)
        p1 = T1 if len(T1) <= NPERM_SUB else rng2.choice(T1, NPERM_SUB, replace=False)
        p0 = T0 if len(T0) <= NPERM_SUB else rng2.choice(T0, NPERM_SUB, replace=False)
        r["energy_sub2k"], r["energy_perm_p"] = energy_perm(P.Zcore[p1], P.Zcore[p0], seed=P.erng_seed)
    # c. missingness
    msd = np.sqrt((P.M[t == 1].var(0, ddof=1) + P.M[t == 0].var(0, ddof=1)) / 2)
    mm = _smd_vec(P.M, msd, s_idx, s_w, s_t)
    names = np.array(P.mnames)
    r["miss_mean"] = float(np.nanmean(mm[~np.char.startswith(names, "x_done")])) if np.isfinite(mm).any() else np.nan
    r["miss_echo"] = float(mm[P.mnames.index("echo_done")])
    r["miss_bnp"] = float(mm[P.mnames.index("bnp_done")]) if "bnp_done" in P.mnames else np.nan
    lab = mm[np.char.startswith(names, "lab_done")]
    r["miss_lab"] = float(np.nanmean(lab)) if np.isfinite(lab).any() else np.nan
    xm = mm[np.char.startswith(names, "x_done")]
    r["miss_x"] = float(np.nanmean(xm)) if len(xm) and np.isfinite(xm).any() else np.nan
    # d. subgroup (58 VARS + extras)
    comp = _smd_vec(P.V, P.sd, s_idx, s_w, s_t)
    r["ho_smd_all"] = _var_mean(comp, P.vgroups)
    r["xsmd"] = r["xsmd_prox"] = r["xsmd_other"] = np.nan
    if P.xidx:
        xv = comp[P.xidx]
        r["xsmd"] = float(np.nanmean(xv)) if np.isfinite(xv).any() else np.nan
        blk = np.array([getattr(P, "xblock", {}).get(P.cols[j], "other") for j in P.xidx])
        for nm, m in (("xsmd_prox", blk == "ecg_proximal"), ("xsmd_other", blk != "ecg_proximal")):
            if m.any() and np.isfinite(xv[m]).any():
                r[nm] = float(np.nanmean(xv[m]))
        r["n_x_prox"] = int((blk == "ecg_proximal").sum())
    subs = {}
    for nm, mask in (("age65p", P.age65), ("age_lt65", ~P.age65), ("male", P.male), ("female", ~P.male)):
        keep = mask[s_idx]
        si, sw, st = s_idx[keep], s_w[keep], s_t[keep]
        if min((st == 1).sum(), (st == 0).sum()) < 20:
            subs[nm] = np.nan
            continue
        subs[nm] = _var_mean(_smd_vec(P.V, P.sd, si, sw, st), P.vgroups)
    for nm, v in subs.items():
        r[f"sub:{nm}"] = v
    sv = np.array(list(subs.values()), float)
    r["sub_smd"] = float(np.nanmean(sv)) if np.isfinite(sv).any() else np.nan
    r["sub_max"] = float(np.nanmax(sv)) if np.isfinite(sv).any() else np.nan
    return r


# ---------------------------------------------------------------- one task = (trial, half, cell)
def task(args):
    n, half, cell, extra_dir, panel, drop_block = args
    t0 = time.time()
    i = E.TRIALS.index(n)
    T = E.load_trial(n)
    C = load_new(T)
    rows = halves(T, i)[half]
    t = T.t[rows]
    D = T.degraded(0.5, 0) if cell == "sparse_drop50" else T
    assert D.H is T.H
    X, ps_names, ex58 = base_designs(T, C, D, rows, t)[cell] if cell != "unmatched" else (None, [], set())
    Hf = T.H
    vc = E.var_components(Hf)
    drop = {x for c in ex58 for x in vc[c]}
    Hc = Hf[[c for c in Hf.columns if c not in drop]]
    xcols, xdrop = [], []
    if extra_dir is not None:
        Xe, ovl, blk = load_extra(T, Path(extra_dir))
        if drop_block:
            Xe = Xe[[c for c in Xe.columns if blk[c] != drop_block]]
        xdrop = excluded_extra(ps_names, list(Xe.columns), ovl)
        Xe = Xe.drop(columns=xdrop)
        Xe = Xe.loc[:, Xe.notna().any() & (Xe.nunique() > 1)]
        xcols = list(Xe.columns)
        Hc = pd.concat([Hc, Xe.add_prefix("X::")], axis=1)
    Hrows = Hc.iloc[rows]
    P = Prep(T, rows, t, Hrows, xcols, seed=16060 + i)
    P.xblock = {f"X::{c}": blk[c] for c in xcols} if xcols else {}
    perm = n in PERM_TRIALS and half == "full"
    pc = T.ecg_pc[rows]
    arms = [("unmatched", "unmatched", None)] if cell == "unmatched" else \
        [("base", CELL_LAB[cell], X), ("ECG", f"{CELL_LAB[cell]}+ECG", np.hstack([X, pc])),
         ("shufECG", f"{CELL_LAB[cell]}+shufECG", np.hstack([X, T.ecg_pc[T.shuffle_perm][rows]])),
         ("noise", f"{CELL_LAB[cell]}+noise32", np.hstack([X, T.noise32[rows]]))]
    out = []
    Hv = Hf.to_numpy(float)[rows]
    for role, label, Xa in arms:
        r = E.run_cell(D, Xa, rows=rows, heldout=Hf)
        s_idx, s_w, cl, npairs = matched_sample(Xa, t)
        if not (np.isnan(npairs) and np.isnan(r["n_pairs"])) and npairs != r["n_pairs"]:
            raise RuntimeError(f"match replication mismatch {n} {half} {cell} {role}: {npairs} vs {r['n_pairs']}")
        # engine mean |SMD| recomputed from the replicated matched sample
        comp = E.smd_components(Hv, t, s_idx, s_w, t[s_idx])
        cs = pd.Series(comp, index=Hf.columns)
        sv = pd.Series({c: (cs[vc[c]].dropna().mean() if len(cs[vc[c]].dropna()) else np.nan) for c, _, _ in E.VARS})
        rep_dev = abs(float(sv.mean()) - r["mean_smd"])
        ho = [c for c, _, _ in E.VARS if c not in ex58]
        r["mean_smd_ho"] = float(sv[ho].mean())
        r["cstat_ho"] = r["cstat"] if not ex58 else E.balance_cstat(Hc.iloc[rows][[c for c in Hc.columns if not c.startswith("X::")]].to_numpy(float)[s_idx],
                                                                   t[s_idx], s_w, model=("l2", 0.01), seed=0)
        m = measures(P, s_idx, s_w, perm=perm)
        out.append(dict(sweep=SWEEP, cell=cell, rung=CELL_POS.get(cell, -1), panel=panel, trial=n, half=half, arm_role=role,
                        arm_label=label, **r, **m, rep_npairs=npairs, rep_dev_mean_smd=rep_dev, n_extra=len(xcols),
                        n_extra_dropped=len(xdrop), n_Zall=P.Zall.shape[1], n_Zcore=P.Zcore.shape[1], rb=T.rb, rs=T.rs))
    print(f"{n} {half} {cell} {panel} done {time.time() - t0:.0f}s", flush=True)
    return out


def run(trials, workers, out, extra_dir, panel, drop_block=None):
    from multiprocessing import Pool
    os.umask(0o077)
    out.mkdir(parents=True, exist_ok=True)
    size = {n: len(E.load_trial(n).t) for n in trials}
    tasks = [(n, h, c, extra_dir, panel, drop_block) for n in trials for h in ("full", "A", "B") for c in ["unmatched"] + [c for c, _ in CELLS]]
    tasks.sort(key=lambda x: -size[x[0]])
    res = []
    t0 = time.time()
    with Pool(min(workers, len(tasks), 40)) as p:
        for k, r in enumerate(p.imap_unordered(task, tasks, chunksize=1)):
            res.extend(r)
            if (k + 1) % 25 == 0 or k + 1 == len(tasks):
                print(f"{k + 1}/{len(tasks)} tasks {time.time() - t0:.0f}s", flush=True)
    df = pd.DataFrame(res)
    f = out / f"results_{panel}.csv"
    df.to_csv(f, index=False)
    print("wrote", f, df.shape)


# ---------------------------------------------------------------- summaries
def cluster_loo(d: pd.Series):
    d = d.dropna()
    cl = d.groupby(d.index.map(CLUSTER)).mean()
    loo = [sign_flip(d.drop(k).to_numpy())[1] for k in d.index]
    return dict(cluster_d=float(cl.mean()), cluster_k=f"{int((cl < 0).sum())}/{len(cl)}", cluster_p=sign_flip(cl.to_numpy())[1],
                loo_p_max=float(max(loo)), loo_n_ge05=int(sum(p >= 0.05 for p in loo)))


def pairs(df, a, b, half, mets):
    g = df[(df.half == half) & df.arm_role.isin([a, b])].copy()
    g["arm"] = g.arm_role
    base = E.summarize_pairs(g[["cell", "trial", "arm", "loghr", "se", "rb", "rs", "mean_smd", "cstat"]], ["cell"], a, b)
    for m in mets:
        if m in ("absd", "z2", "mean_smd", "cstat"):
            continue
        h = g[["cell", "trial", "arm", "loghr", "se", "rb", "rs"]].assign(mean_smd=g[m])
        s = E.summarize_pairs(h, ["cell"], a, b)[["cell", "d_mean_smd", "k_mean_smd", "p_mean_smd"]]
        base = base.merge(s.rename(columns={"d_mean_smd": f"d_{m}", "k_mean_smd": f"k_{m}", "p_mean_smd": f"p_{m}"}), on="cell")
    base["half"] = half
    return base


def summarize_panel(df, panel, out):
    df = df[df.panel == panel].copy()
    df["absd"] = (df.loghr - df.rb).abs()
    df["z2"] = (df.loghr - df.rb) ** 2 / (df.se ** 2 + df.rs ** 2)
    mets = [m for m in METRICS if m in df and df[m].notna().any()]
    cells = [c for c, _ in CELLS]
    S = pd.concat([pairs(df, "ECG", b, h, mets) for h in ("full", "A", "B") for b in ("base", "shufECG", "noise")], ignore_index=True)
    S["panel"] = panel
    V = []
    for c in cells:
        for m in mets:
            row = dict(panel=panel, cell=c, metric=m, family=next(f for f, ms in FAMILY.items() if m in ms))
            for h in ("full", "A", "B"):
                for b in ("base", "shufECG", "noise"):
                    s = S[(S.cell == c) & (S.half == h) & (S.arm_b == b)].iloc[0]
                    row[f"d_{b}_{h}"], row[f"p_{b}_{h}"] = s[f"d_{m}"], s[f"p_{m}"]
                    if b == "base":
                        row[f"k_{h}"] = s[f"k_{m}"]
            g = df[(df.half == "full") & (df.cell == c)]
            e = g[g.arm_role == "ECG"].set_index("trial")[m]
            bb = g[g.arm_role == "base"].set_index("trial")[m]
            row.update(cluster_loo(e - bb.reindex(e.index)))
            row["base_mean"], row["ecg_mean"] = float(bb.mean()), float(e.mean())
            V.append(row)
    V = pd.DataFrame(V)
    V["q_metric"] = np.nan
    for m in mets:
        k = V.metric == m
        V.loc[k, "q_metric"] = E.bh_fdr(V.loc[k, "p_base_full"])
    V["q_family"] = np.nan
    for f in V.family.unique():
        k = V.family == f
        V.loc[k, "q_family"] = E.bh_fdr(V.loc[k, "p_base_full"])
    V["sig"] = (V.p_base_full < 0.05) & (V.d_base_full < 0)
    V["worse"] = (V.p_base_full < 0.05) & (V.d_base_full > 0)
    V["placebo_ok"] = (V.d_shufECG_full < 0) & (V.d_noise_full < 0)
    V["ecg_specific"] = V.sig & V.placebo_ok
    V["halves_dir"] = (np.sign(V.d_base_A) == np.sign(V.d_base_full)) & (np.sign(V.d_base_B) == np.sign(V.d_base_full))
    V["halves_sig"] = V.halves_dir & (V.p_base_A < 0.05) & (V.p_base_B < 0.05)
    V["robust"] = V.ecg_specific & (V.q_family < 0.05) & (V.cluster_p < 0.05) & (V.loo_p_max < 0.05) & V.halves_dir
    # levels
    L = df.groupby(["half", "cell", "arm_role"])[[m for m in mets] + ["n_pairs"]].mean().reset_index()
    L["panel"] = panel
    return S, V, L, df


def summarize(out, doc):
    fs = sorted(out.glob("results_*.csv"))
    df = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    df.to_csv(out / "results.csv", index=False)
    panels = [p for p in ("p58",) if p in set(df.panel)] + sorted(p for p in set(df.panel) if p != "p58")
    SS, VV, LL = [], [], []
    for p in panels:
        S, V, L, _ = summarize_panel(df, p, out)
        SS.append(S), VV.append(V), LL.append(L)
    S, V, L = (pd.concat(x, ignore_index=True) for x in (SS, VV, LL))
    S.to_csv(out / "summary_pairs.csv", index=False)
    V.to_csv(out / "verdicts.csv", index=False)
    L.to_csv(out / "levels.csv", index=False)
    heatmap(V, panels)
    if doc:
        write_md(df, V, L, panels, out)


def heatmap(V, panels):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    DOCS.mkdir(parents=True, exist_ok=True)
    cells = [c for c, _ in CELLS]
    fig, axs = plt.subplots(len(panels), 1, figsize=(22, 4.2 * len(panels) + 1), squeeze=False)
    for ax, p in zip(axs[:, 0], panels):
        v = V[V.panel == p]
        mets = [m for m in METRICS if m in set(v.metric)]
        M = np.full((len(cells), len(mets)), np.nan)
        Dd = M.copy()
        Pp = M.copy()
        R = np.zeros_like(M, dtype=object)
        for i, c in enumerate(cells):
            for j, m in enumerate(mets):
                r = v[(v.cell == c) & (v.metric == m)].iloc[0]
                Pp[i, j], Dd[i, j] = r.p_base_full, r.d_base_full
                M[i, j] = -np.sign(r.d_base_full) * -np.log10(max(r.p_base_full, 1e-5))
                R[i, j] = "††" if r.robust else ("†" if r.ecg_specific else "")
        im = ax.imshow(M, cmap="RdBu", vmin=-5, vmax=5, aspect="auto")
        for i in range(len(cells)):
            for j in range(len(mets)):
                dtxt = f"{Dd[i, j]:+.3f}" if abs(Dd[i, j]) < 10 else f"{Dd[i, j]:+.1f}"
                ax.text(j, i, f"{dtxt}\np={Pp[i, j]:.3f}{R[i, j]}", ha="center", va="center", fontsize=6.3,
                        color="white" if abs(M[i, j]) > 3 else "#0b0b0b", fontweight="bold" if Pp[i, j] < 0.05 else "normal")
        ax.set_xticks(range(len(mets)))
        ax.set_xticklabels([MLAB[m] for m in mets], rotation=35, ha="right", fontsize=7.5)
        ax.set_yticks(range(len(cells)))
        ax.set_yticklabels([CELL_LAB[c] for c in cells], fontsize=8)
        ax.set_title(f"panel {p}: ECG − base (full cohort, 18 trials). Colour = signed −log10 sign-flip p (blue = ECG better). "
                     "† ECG-specific (p<0.05, beats both placebos in direction); †† robust (+ family BH q<0.05, cluster p<0.05, "
                     "LOO max p<0.05, same direction in both halves)", fontsize=8.5)
        fig.colorbar(im, ax=ax, shrink=0.8, label="signed −log10 p")
    fig.tight_layout()
    fig.savefig(DOCS / "S6_BALANCE_heatmap.png", dpi=130)
    plt.close(fig)


def write_md(df, V, L, panels, out):
    audit_f, kf_f = out / "audit.md", out / "key_findings.md"
    audit = audit_f.read_text() if audit_f.exists() else "(audit section not found)"
    keyf = kf_f.read_text() if kf_f.exists() else "(key findings not yet written)"
    cells = [c for c, _ in CELLS]

    def ft(d, p):
        return (f"{d:+.4f}" if abs(d) < 1 else f"{d:+.2f}") + f" ({p:.3f})"

    txt = [f"# v1.6 S6 — extended held-out balance measures, ECG vs no-ECG ({time.strftime('%Y-%m-%d')})\n",
           "**Exploratory, post-hoc specification (docs/V16_SWEEP_PLAN.md).** 18 trials; 1:1 greedy caliper-0.2 matching on an L2 "
           "(C=1) logistic PS; imputation 1, pool-split seed 0. ECG = 32 BCL PCs; placebos `shufECG` (rows permuted) and `noise32`. "
           "d = mean over trials of (ECG arm − comparator); every measure is 'lower = better', so negative d = ECG better. "
           "p = exact sign-flip over trials. Script `scripts/v16/s6_balance.py`; aggregates in "
           "`/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s6-balance/`.\n",
           "## Key findings (plain language)\n", keyf + "\n",
           "![S6 heat map](S6_BALANCE_heatmap.png)\n",
           "## Automatic flags\n",
           "*ECG-specific*: ECG vs base p<0.05 with d<0 AND d(ECG−shufECG)<0 AND d(ECG−noise)<0 (direction only). *Robust*: "
           "ECG-specific AND BH q<0.05 within measure family (metrics × 6 rungs) AND comparator-clustered sign-flip p<0.05 "
           "(10 clusters) AND leave-one-trial-out max p<0.05 AND same direction in both halves (within-trial split halves of the "
           "same 18 trials, not independent replication). Panels: `p58` = engine 58-variable panel only; `x2all` = 58 + "
           "claude-v16-covars2 (per trial: status kept, exposure-leak variables removed; per cell: PS duplicates removed); "
           "`x2np` = as x2all but without the dictionary `ecg_proximal` block (HF, cardiomyopathy, arrhythmia, conduction, "
           "devices, rate/rhythm drugs, ECG counts, CHA2DS2-VASc; 48 registered). Missingness measures (family c) use the 58-panel "
           "labs/echo only, so they are identical across panels.\n"]
    for p in panels:
        v = V[V.panel == p]
        txt.append(f"### panel {p}\n")
        rows = []
        for m in [m for m in METRICS if m in set(v.metric)]:
            w = v[v.metric == m].set_index("cell")
            rows.append({"metric": MLAB[m].replace("|", "\\|"), "family": FAM_LAB[w.family.iloc[0]],
                         "p<0.05 better": ", ".join(CELL_LAB[c] for c in cells if w.loc[c, "sig"]) or "–",
                         "ECG-specific": ", ".join(CELL_LAB[c] for c in cells if w.loc[c, "ecg_specific"]) or "–",
                         "robust": ", ".join(CELL_LAB[c] for c in cells if w.loc[c, "robust"]) or "–",
                         "robust + p<0.05 in both halves": ", ".join(CELL_LAB[c] for c in cells if w.loc[c, "robust"] and w.loc[c, "halves_sig"]) or "–",
                         "ECG worse (p<0.05)": ", ".join(CELL_LAB[c] for c in cells if w.loc[c, "worse"]) or "–"})
        txt.append(md(pd.DataFrame(rows)) + "\n")
    txt += ["## Measures\n",
            "| family | metric | definition |\n|---|---|---|\n"
            "| a | ob_signed | \\|Σ_j β_j Δ_j\\|: β = ridge logistic (event by horizon) on all held-out components (median-imputed + "
            "missingness indicators, standardised by pooled within-arm SD), fitted in the comparator arm of the unmatched analysed rows, "
            "C by 3-fold CV; Δ_j = matched treated − comparator mean. = difference in mean held-out prognostic logit |\n"
            "| a | ob_abs | Σ_j \\|β_j\\|\\|Δ_j\\| (outcome-relevant imbalance, no cancellation) |\n"
            "| a | prog_ho_smd | \\|SMD\\| of the held-out prognostic score (5-fold cross-fitted in comparators) |\n"
            "| b | vr_logdev | mean \\|log(var_T/var_C)\\| over continuous non-code components (util, prog_full, observed vitals/labs, echo; ≥ 50 observed per arm), observed values winsorised at the 1st/99th percentile of the analysed rows |\n"
            "| b | ks_mean | mean two-sample KS statistic over the same components |\n"
            "| b | energy | energy distance between arms on standardised core components (+ indicators), ≤ 5,000 per arm |\n"
            "| c | miss_* | \\|SMD\\| of 'measured' indicators: echo done (any echo, masked pre-2016), NT-proBNP done, each lab done (miss_lab = mean), "
            "vitals done; miss_mean = mean over all |\n"
            "| d | sub_smd / sub_max | mean over 58 variables of \\|SMD\\| within age ≥65, <65, male, female strata of the matched sample; mean / max of the 4 strata |\n"
            f"| e | maha_* | sqrt(Δ'(S+{LAMBDA}·I)^-1 Δ), S = pooled within-arm covariance of standardised components (analysed rows); all components / non-code core |\n"
            "| engine | absd, z2, mean_smd, cstat | run_cell outputs; *_ho = held-out-from-PS subset (differs only for clinical) |\n",
            "Clinical: the PS contains meds, utilisation and the observed vitals/labs (completed); those components are removed from "
            "every S6 measure (not their missingness indicators, which are not in the PS).\n"]
    for p in panels:
        v = V[V.panel == p]
        txt.append(f"## Full results, panel {p}\n")
        txt.append("Each cell: d (sign-flip p). vs base = ECG − base; cluster = comparator-clustered p; LOO = max p leaving one trial out; "
                   "q_fam = BH within measure family.\n")
        for m in [m for m in METRICS if m in set(v.metric)]:
            w = v[v.metric == m].set_index("cell")
            rows = []
            for c in cells:
                r = w.loc[c]
                rows.append({"rung": CELL_LAB[c], "base": r.base_mean, "ECG": r.ecg_mean, "k": r.k_full,
                             "vs base": ft(r.d_base_full, r.p_base_full), "q_metric": r.q_metric, "q_fam": r.q_family,
                             "vs shufECG": ft(r.d_shufECG_full, r.p_shufECG_full), "vs noise": ft(r.d_noise_full, r.p_noise_full),
                             "cluster": f"{r.cluster_k} p={r.cluster_p:.3f}", "LOO max p": r.loo_p_max,
                             "half A": ft(r.d_base_A, r.p_base_A), "half B": ft(r.d_base_B, r.p_base_B),
                             "flag": "robust" if r.robust else ("ECG-specific" if r.ecg_specific else ("WORSE" if r.worse else ""))})
            txt += [f"### {MLAB[m]} (`{m}`)\n", md(pd.DataFrame(rows), 4) + "\n"]
        # unmatched reference and placebo-vs-base null
        u = df[(df.panel == p) & (df.half == "full") & (df.arm_role == "unmatched")]
        um = {MLAB[m].replace("|", "\\|"): float(u[m].mean()) for m in [m for m in METRICS if m in set(v.metric)] if m in u}
        txt += [f"Unmatched reference (panel {p}, full, mean over trials): " + "; ".join(f"{k} {x:.4g}" for k, x in um.items()) + "\n"]
    # energy permutation
    ep = df[df.energy_perm_p.notna()] if "energy_perm_p" in df else pd.DataFrame()
    if len(ep):
        tab = ep.pivot_table(index=["panel", "trial", "cell"], columns="arm_role", values="energy_perm_p").reset_index()
        tab["cell"] = tab.cell.map(lambda c: CELL_LAB.get(c, c))
        txt += ["## Energy-distance permutation p (2,000 per arm subsample, 200 permutations; full cohort)\n",
                "Small p = arms still distributionally distinguishable on held-out core components after matching.\n",
                md(tab, 3) + "\n"]
    txt += ["## Audit\n", audit + "\n",
            "## Limitations\n",
            "Exploratory; measures chosen post hoc. One imputation, one pool split; halves are within-trial patient splits, not "
            "independent replication. 18 overlapping trials (10 comparator clusters); per-trial measures are strongly correlated "
            "across measures (they all read the same matched sets), so the families are not independent evidence. Outcome model is "
            "logistic on the event indicator by horizon (ignores censoring before horizon). Energy distance is subsampled (≤ 5,000 "
            "per arm; seeded, same seed for every arm of a trial/half). Echo-done is masked before the echo data start, so it also "
            "reflects index year. External confirmation deferred.\n"]
    (DOCS / "S6_BALANCE.md").write_text("\n".join(txt))
    print("wrote", DOCS / "S6_BALANCE.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["run", "summarize"])
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--extra", default=None, help="dir with <trial>.parquet extra held-out panel")
    ap.add_argument("--panel", default="p58")
    ap.add_argument("--drop-block", default=None, help="drop extra variables with this dictionary block tag (e.g. ecg_proximal)")
    ap.add_argument("--doc", action="store_true")
    a = ap.parse_args()
    os.umask(0o077)
    if a.mode == "run":
        run(a.trials.split(","), a.workers, Path(a.out), a.extra, a.panel, a.drop_block)
    else:
        summarize(Path(a.out), a.doc)


if __name__ == "__main__":
    main()
