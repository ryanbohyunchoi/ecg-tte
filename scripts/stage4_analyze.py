"""
stage4_analyze.py

Stage 4: Comparator ladder + balance table + forest plot.
Generic analysis pipeline for ecg-tte. Pass --published-hr to overlay the
RCT ground truth on the forest plot.

Comparator ladder (as run by main()):
  1. Unadjusted Cox        — reference; expect confounded HR
  2. Adjusted Cox          — age, sex, EF, key comorbidities (_ADJ_COX_CANDIDATES, 13 covs)
  3. Rich PSM              — LASSO-selected subset of _RICH_PSM_CANDIDATES (62 covs),
                             logit(PS) caliper at --caliper-sd × SD (Austin 0.2 default)
  4. Forest plot           — with optional --published-hr overlay
  (embedding_psm / ps_ecg_match / nn_match exist as library functions but are
   not wired into the current main() ladder.)

Missing covariate handling (--n-imputations):
  1 (default) — complete-case (listwise deletion); reproduces legacy numbers.
  m ≥ 2       — MICE (scripts/imputation.py) imputes continuous covariates
                (EF, ECG intervals, labs, vitals), matches within each of m
                imputed datasets, pools log-HR via Rubin's rules. Structurally
                0-encoded binaries are never imputed. See imputation.py.

Denominator standardization (--denominator flag):
  strict (default) — ladder run on D = (ECG-available) ∩ (rich-covariates complete).
                     Under imputation (m≥2) this becomes a complete-case sensitivity rung.
  both             — strict complete-case rung emitted alongside the imputed primary.
  A denominator_audit.csv / missingness_audit.csv are always written.

Balance reporting:
  SMD table over the full SMD_COLS set (77 covariates; see balance.py). Under
  imputation the reported SMD is averaged across the m imputed datasets, with
  complete-case SMDs kept as sensitivity columns.

Diagnostics (--diagnostics flag, default on):
  arm_summary, event rates, KM curves, index-date distribution,
  immortal-time check, match-distance distribution.

Usage:
    python scripts/stage4_analyze.py \\
        --cohort     runs/<trial>/comet_cohort.parquet \\
        --embed-dir  embeddings/biometric \\
        --output-dir runs/<trial> \\
        --n-imputations 5 --caliper-sd 0.20 --denominator strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import balance as _balance_mod
from balance import (
    SMD_COLS, build_balance_table, write_balance_tables,
    print_balance_table, plot_love, plot_love_multimethod,
    summarize_split, compute_cci, cci_smd, pooled_balance_table,
)
from denominators import build_masks, audit_table, print_audit, missingness_audit
from diagnostics import (
    arm_summary, print_arm_summary, event_rate_by_arm, print_event_rates,
    plot_km, plot_index_date_distribution, check_immortal_time,
    match_distance_summary,
)

COMET_HR = 0.83

# Outcome column names — set by main() via auto-detection or --event-col/--time-col.
# Module-level so cox_hr/ipw_hr pick them up without thread-safety concerns
# (single-process single-trial runs only).
_EVENT_COL: str = "event_death"
_TIME_COL:  str = "time_to_death"


# ── I/O ───────────────────────────────────────────────────────────────────────

def load_embeddings(
    embed_dir: str,
    cohort: pd.DataFrame,
    fid_col: str = "selected_ecg_fileID",
) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Load BCL embeddings keyed by fileID from cohort[fid_col].
    Returns (emb_cohort, X_raw) — subset of cohort with valid embeddings.
    """
    root = Path(embed_dir)
    rows, vecs = [], []
    for i, row in cohort.iterrows():
        fid = str(row.get(fid_col, ""))
        if not fid or fid == "nan" or fid == "<NA>":
            continue
        p = root / f"{fid}.npy"
        if p.is_file():
            rows.append(i)
            vecs.append(np.load(p))
    if not rows:
        return pd.DataFrame(), np.empty((0, 1))
    emb_df = cohort.loc[rows].reset_index(drop=True)
    X_raw  = np.stack(vecs)
    return emb_df, X_raw


# ── Cox PH ────────────────────────────────────────────────────────────────────

def cox_hr(
    df: pd.DataFrame,
    covariates: list[str] | None = None,
    treated_arm: str = "carvedilol",
    strata: list[str] | None = None,
    weights_col: str | None = None,
    robust: bool = False,
) -> dict:
    try:
        from lifelines import CoxPHFitter
    except ImportError:
        raise ImportError("pip install lifelines")

    ec = _EVENT_COL
    tc = _TIME_COL
    d = df.copy()
    d["arm_binary"] = (d["arm"] == treated_arm).astype(int)
    cols = [tc, ec, "arm_binary"]
    cov_cols = [c for c in (covariates or []) if c in d.columns]
    cols += cov_cols
    strata_cols = [c for c in (strata or []) if c in d.columns]
    cols += strata_cols
    if weights_col and weights_col in d.columns:
        cols.append(weights_col)

    d = d[list(dict.fromkeys(cols))].dropna()
    # Drop covariates constant overall or within either arm (the latter causes perfect
    # separation — e.g. aldosterone_antag==1 for all MRA treated patients)
    degenerate = []
    for c in [c for c in cov_cols if c in d.columns]:
        if d[c].nunique() <= 1:
            degenerate.append(c)
        elif any(d.loc[d["arm_binary"] == v, c].nunique() <= 1
                 for v in d["arm_binary"].unique()):
            print(f"  NOTE: dropping {c!r} — constant within one arm (perfect separator)")
            degenerate.append(c)
    if degenerate:
        d = d.drop(columns=degenerate)
    cph = CoxPHFitter()
    cph.fit(d, duration_col=tc, event_col=ec,
            strata=strata_cols if strata_cols else None,
            weights_col=weights_col if weights_col and weights_col in d.columns else None,
            robust=robust)
    s = cph.summary.loc["arm_binary"]
    return {
        "hr":        float(np.exp(s["coef"])),
        "ci_low":    float(np.exp(s["coef lower 95%"])),
        "ci_high":   float(np.exp(s["coef upper 95%"])),
        "p":         float(s["p"]),
        "n":         len(d),
        "log_hr":    float(s["coef"]),
        "se_log_hr": float(s["se(coef)"]),
    }


def ipw_hr(
    df: pd.DataFrame,
    treated_arm: str,
    control_arm: str,
    covariates: list[str],
    seed: int = 42,
) -> dict:
    """Stabilized IPW Cox — propensity fit on covariates, trimmed [1%, 99%]."""
    ec = _EVENT_COL
    tc = _TIME_COL
    d = df.copy()
    cov_cols = [c for c in covariates if c in d.columns]
    keep_cols = [tc, ec, "arm"] + cov_cols
    d = d[keep_cols].dropna()
    d["arm_binary"] = (d["arm"] == treated_arm).astype(int)
    # Drop covariates constant overall or within either arm
    cov_cols = [
        c for c in cov_cols
        if d[c].nunique() > 1
        and all(d.loc[d["arm_binary"] == v, c].nunique() > 1
                for v in d["arm_binary"].unique())
    ]
    X = d[cov_cols].values
    y = d["arm_binary"].values
    sc  = StandardScaler()
    X_s = sc.fit_transform(X)
    lr  = LogisticRegression(max_iter=1000, random_state=seed, solver="lbfgs")
    lr.fit(X_s, y)
    ps  = lr.predict_proba(X_s)[:, 1]
    ps  = np.clip(ps, 0.01, 0.99)
    p_t = y.mean()
    w   = np.where(y == 1, p_t / ps, (1 - p_t) / (1 - ps))
    d["ipw_weight"] = w
    return cox_hr(d, treated_arm=treated_arm, weights_col="ipw_weight", robust=True)


def print_res(label: str, res: dict) -> None:
    line = (f"  {label:<50} HR={res['hr']:.3f} "
            f"[{res['ci_low']:.3f}–{res['ci_high']:.3f}]  p={res['p']:.4f}  n={res['n']}")
    if res.get("m", 1) and res.get("m", 1) > 1:
        line += f"  [MI m={res['m']}, FMI={res.get('fmi', float('nan')):.2f}]"
    print(line)


# ── Multiple-imputation pooling (Rubin's rules) ───────────────────────────────

def pool_rubin(log_hrs: list[float], se_log_hrs: list[float]) -> dict:
    """
    Pool m per-imputation log-HR estimates with Rubin's rules.

      Qbar = mean(log_hr)                 (pooled point estimate, log scale)
      Ubar = mean(se^2)                   (within-imputation variance)
      B    = var(log_hr, ddof=1)          (between-imputation variance)
      T    = Ubar + (1 + 1/m) * B         (total variance)
    CI uses a t reference with Barnard-Rubin-style df; HR/CI returned on the
    exp scale. FMI = fraction of missing information. Pooling is on log-HR —
    never average HRs directly.
    """
    log_hrs = [x for x in log_hrs if x is not None and np.isfinite(x)]
    se = [s for s in se_log_hrs if s is not None and np.isfinite(s)]
    m = min(len(log_hrs), len(se))
    if m == 0:
        return {"hr": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                "p": float("nan"), "n": 0, "m": 0, "fmi": float("nan"),
                "log_hr": float("nan"), "se_log_hr": float("nan")}
    log_hrs = np.asarray(log_hrs[:m], float)
    se = np.asarray(se[:m], float)
    Qbar = float(log_hrs.mean())
    Ubar = float((se ** 2).mean())
    B = float(log_hrs.var(ddof=1)) if m >= 2 else 0.0
    T = Ubar + (1.0 + 1.0 / m) * B
    se_pool = float(np.sqrt(T)) if T > 0 else 0.0
    # Old-Rubin df; r = relative increase in variance due to nonresponse.
    if B > 0 and Ubar > 0 and m >= 2:
        r = (1.0 + 1.0 / m) * B / Ubar
        df_rubin = (m - 1) * (1.0 + 1.0 / r) ** 2
        fmi = (r + 2.0 / (df_rubin + 3.0)) / (r + 1.0)
    else:
        r, df_rubin, fmi = 0.0, float("inf"), 0.0
    from scipy.stats import t as _t, norm as _norm
    tcrit = _t.ppf(0.975, df_rubin) if np.isfinite(df_rubin) else 1.959963985
    z = Qbar / se_pool if se_pool > 0 else float("inf")
    if se_pool <= 0:
        p = float("nan")
    elif np.isfinite(df_rubin):
        p = float(2.0 * _t.sf(abs(z), df_rubin))
    else:
        # B≈0 (covariates fully observed): pooled estimate degenerate to a single
        # draw — use the normal approximation rather than reporting NaN.
        p = float(2.0 * _norm.sf(abs(z)))
    return {
        "hr":        float(np.exp(Qbar)),
        "ci_low":    float(np.exp(Qbar - tcrit * se_pool)),
        "ci_high":   float(np.exp(Qbar + tcrit * se_pool)),
        "p":         p,
        "n":         0,  # caller overwrites with mean matched n
        "log_hr":    Qbar,
        "se_log_hr": se_pool,
        "m":         m,
        "fmi":       float(fmi),
        "df_rubin":  float(df_rubin),
    }


def _pool_over_imputations(fn, imputations: list[pd.DataFrame], **kwargs) -> dict:
    """
    Run estimator `fn(df, **kwargs) -> res-dict` on each imputed dataset and pool
    with Rubin's rules. `fn` must return log_hr / se_log_hr / n keys (cox_hr,
    ipw_hr, and the PSM wrapper all do). Returns the pooled result dict with the
    mean matched n. Single-element lists pass through unchanged.
    """
    if len(imputations) == 1:
        return fn(imputations[0], **kwargs)
    results = []
    for d in imputations:
        try:
            r = fn(d, **kwargs)
        except Exception as e:
            print(f"  MI: estimator failed on one imputation ({e}) — skipping")
            continue
        if r and np.isfinite(r.get("log_hr", float("nan"))):
            results.append(r)
    if not results:
        return {"hr": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                "p": float("nan"), "n": 0, "m": 0, "fmi": float("nan")}
    pooled = pool_rubin([r["log_hr"] for r in results],
                        [r["se_log_hr"] for r in results])
    pooled["n"] = int(np.mean([r["n"] for r in results]))
    return pooled


# ── PSM helpers ───────────────────────────────────────────────────────────────

def _greedy_match(
    df: pd.DataFrame,
    score: np.ndarray,
    k: int,
    caliper: float,
    treated_arm: str,
    control_arm: str,
) -> pd.DataFrame:
    """
    Shared greedy 1:k matching on a caller-supplied 1-D matching score.
    `score` and `caliper` must be in the same units (e.g. logit(PS) with the
    caliper already scaled to SD units of logit(PS)).
    """
    df = df.copy().reset_index(drop=True)
    df["_mscore"] = score
    treated_idx = df.index[df["arm"] == treated_arm].tolist()
    control_idx = df.index[df["arm"] == control_arm].tolist()
    n_nb = min(k * 2, len(control_idx))
    nn = NearestNeighbors(n_neighbors=n_nb, metric="euclidean")
    nn.fit(df.loc[control_idx, ["_mscore"]].values)
    dists, indices = nn.kneighbors(df.loc[treated_idx, ["_mscore"]].values)

    used = set()
    rows = []
    for mid, (ti, di, ii) in enumerate(zip(treated_idx, dists, indices)):
        mc = []
        for d, ci in zip(di, ii):
            ri = control_idx[ci]
            if d <= caliper and ri not in used:
                used.add(ri); mc.append(ri)
            if len(mc) == k:
                break
        if mc:
            r = df.loc[ti].copy(); r["match_id"] = mid; rows.append(r)
            for ri in mc:
                r = df.loc[ri].copy(); r["match_id"] = mid; rows.append(r)
    return pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()


def structured_psm(
    df: pd.DataFrame,
    covariates: list[str],
    k: int = 1,
    caliper_sd: float = 0.20,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    seed: int = 42,
    use_lasso: bool = True,
    fixed_features: list[str] | None = None,
    verbose: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Propensity score matching with optional LASSO feature selection (LEGEND-T2D style).
    Matches on logit(PS) with a caliper of `caliper_sd × SD(logit(PS))` (Austin 0.2).

    When use_lasso=True and fixed_features is None: L1-penalized logistic
    regression with 5-fold CV selects non-zero-coefficient features. When
    fixed_features is provided, LASSO is skipped and exactly those columns are
    used — this freezes the PS model across imputations (no across-draw drift).

    Returns (matched_df, selected_features). selected_features can be fed back as
    fixed_features on subsequent imputations.
    """
    from sklearn.linear_model import LogisticRegressionCV
    avail = [c for c in covariates if c in df.columns]
    if not avail:
        return pd.DataFrame(), []
    feat = df[avail].copy().astype(float)
    feat.replace([np.inf, -np.inf], np.nan, inplace=True)
    complete = feat.notna().all(axis=1)
    n_dropped = (~complete).sum()
    if verbose:
        if n_dropped > 0:
            print(f"  PSM complete-case: dropping {n_dropped:,} rows with missing covariates "
                  f"({complete.sum():,} remain)")
        else:
            print(f"  PSM complete-case: 0 rows dropped ({complete.sum():,} rows complete) ✓")
    df   = df[complete].reset_index(drop=True)
    feat = feat[complete].reset_index(drop=True)
    y    = (df["arm"] == treated_arm).astype(int).values

    if fixed_features is not None:
        sel_feats = [c for c in fixed_features if c in feat.columns]
        if not sel_feats:
            return pd.DataFrame(), []
        sc = StandardScaler()
        X  = sc.fit_transform(feat[sel_feats].values)
    else:
        sc = StandardScaler()
        X  = sc.fit_transform(feat.values)
        sel_feats = list(avail)
        if use_lasso and len(avail) > 1:
            import numpy as _np
            lasso_clf = LogisticRegressionCV(
                Cs=_np.logspace(-3, 1, 20),
                cv=5,
                penalty="l1",
                solver="saga",
                max_iter=2000,
                random_state=seed,
                scoring="roc_auc",
            )
            lasso_clf.fit(X, y)
            coef = lasso_clf.coef_[0]
            sel_mask = coef != 0
            if verbose:
                print(f"  LASSO selected {sel_mask.sum()}/{len(avail)} features  "
                      f"(best C={lasso_clf.C_[0]:.4f})")
                print(f"  Selected covariates: {[f for f, s in zip(avail, sel_mask) if s]}")
            if sel_mask.sum() == 0:
                if verbose:
                    print("  WARNING: LASSO removed all features — falling back to all candidates")
                sel_mask = _np.ones(len(avail), dtype=bool)
            X = X[:, sel_mask]
            sel_feats = [f for f, s in zip(avail, sel_mask) if s]

    clf = LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs", random_state=seed)
    clf.fit(X, y)
    ps  = clf.predict_proba(X)[:, 1]
    eps = 1e-6
    ps_c = np.clip(ps, eps, 1 - eps)
    logit_ps = np.log(ps_c / (1 - ps_c))
    caliper = caliper_sd * float(logit_ps.std())
    if verbose:
        print(f"  Caliper: {caliper_sd} SD × logit_PS_std={logit_ps.std():.4f} → {caliper:.4f}")
    return _greedy_match(df, logit_ps, k, caliper, treated_arm, control_arm), sel_feats


def structured_psm_pooled(
    imputations: list[pd.DataFrame],
    covariates: list[str],
    k: int = 1,
    caliper_sd: float = 0.20,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    seed: int = 42,
    use_lasso: bool = True,
    strata: list[str] | None = None,
) -> tuple[dict, list[pd.DataFrame]]:
    """
    Rich PSM across m imputed datasets: fit PS → match → strata Cox per dataset,
    pool log-HR with Rubin's rules. The LASSO feature set is frozen on the first
    imputation and reused for the rest so the PS model is identical across draws.

    Returns (pooled_result_dict, matched_frames). For a single imputation this is
    exactly the legacy single-dataset PSM (no pooling), returned with m absent.
    """
    strata = strata or ["match_id"]
    matched_frames: list[pd.DataFrame] = []
    res_list: list[dict] = []
    frozen: list[str] | None = None
    for i, d in enumerate(imputations):
        first = i == 0
        matched, sel = structured_psm(
            d, covariates, k=k, caliper_sd=caliper_sd,
            treated_arm=treated_arm, control_arm=control_arm, seed=seed,
            use_lasso=use_lasso, fixed_features=frozen, verbose=first,
        )
        if first:
            frozen = sel
        if matched is None or matched.empty:
            continue
        matched_frames.append(matched)
        try:
            res_list.append(cox_hr(matched, treated_arm=treated_arm, strata=strata))
        except Exception as e:
            print(f"  MI PSM: Cox failed on imputation {i} ({e}) — skipping")

    if not res_list:
        return ({"hr": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                 "p": float("nan"), "n": 0}, matched_frames)
    if len(res_list) == 1:
        return res_list[0], matched_frames
    pooled = pool_rubin([r["log_hr"] for r in res_list],
                        [r["se_log_hr"] for r in res_list])
    pooled["n"] = int(np.mean([r["n"] for r in res_list]))
    return pooled, matched_frames


def embedding_psm(
    df: pd.DataFrame,
    X_raw: np.ndarray,
    k: int = 1,
    caliper: float = 0.05,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    seed: int = 42,
) -> pd.DataFrame:
    sc  = StandardScaler()
    clf = LogisticRegression(max_iter=2000, C=1.0, solver="saga", random_state=seed)
    clf.fit(sc.fit_transform(X_raw), (df["arm"] == treated_arm).astype(int).values)
    ps  = clf.predict_proba(sc.transform(X_raw))[:, 1]
    return _greedy_match(df.copy().reset_index(drop=True), ps, k, caliper, treated_arm, control_arm)


def nn_match(
    df: pd.DataFrame,
    X_raw: np.ndarray,
    k: int = 1,
    metric: str = "cosine",
    threshold: float | None = None,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    exact_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    df = df.copy().reset_index(drop=True)
    X  = X_raw if metric == "cosine" else StandardScaler().fit_transform(X_raw)
    tm = (df["arm"] == treated_arm).values
    cm = (df["arm"] == control_arm).values
    tp_all = np.where(tm)[0]
    cp_all = np.where(cm)[0]

    if exact_cols:
        # Partition treated and control positions by exact-match key
        keys = df[exact_cols].apply(lambda r: tuple(r), axis=1).values
        strata = sorted(set(keys[tm]))
    else:
        strata = [None]

    used, rows, all_dists, mid = set(), [], [], 0
    n_attempted = len(tp_all)

    for stratum in strata:
        if stratum is None:
            tp = tp_all
            cp = cp_all
        else:
            tp = tp_all[np.array([keys[i] == stratum for i in tp_all])]
            cp = cp_all[np.array([keys[i] == stratum for i in cp_all])]
        if len(tp) == 0 or len(cp) == 0:
            continue
        nb = min(max(k * 20, 100), len(cp))
        nn = NearestNeighbors(n_neighbors=nb, metric=metric)
        nn.fit(X[cp])
        dists, indices = nn.kneighbors(X[tp])

        for ti, di, ii in zip(tp, dists, indices):
            mc, md = [], []
            for d, ci in zip(di, ii):
                ri = cp[ci]
                if (threshold is None or d <= threshold) and ri not in used:
                    used.add(ri); mc.append(ri); md.append(d)
                if len(mc) == k:
                    break
            if mc:
                r = df.iloc[ti].copy()
                r["match_id"] = mid
                r["match_distance"] = float("nan")
                rows.append(r)
                for ri, d in zip(mc, md):
                    r = df.iloc[ri].copy()
                    r["match_id"] = mid
                    r["match_distance"] = d
                    rows.append(r)
                all_dists.extend(md)
                mid += 1

    matched = pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()
    n_t = len(set(matched.loc[matched["arm"] == treated_arm, "match_id"])) if not matched.empty else 0
    summary = {
        "n_treated_attempted": n_attempted,
        "n_treated_matched": n_t,
        "n_total_rows": len(matched),
        "median_match_distance": float(np.median(all_dists)) if all_dists else float("nan"),
        "max_match_distance":    float(np.max(all_dists))    if all_dists else float("nan"),
    }
    return matched, summary


def nn_match_multimodal(
    df: pd.DataFrame,
    X_raw: np.ndarray,
    comorbidity_cols: list[str],
    cosine_threshold: float = 0.30,
    comorbidity_weight: float = 1.0,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    exact_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Two-stage ECG+comorbidity matching:
      1. Gate: require cosine distance <= cosine_threshold
      2. Within gate, rank pairs by: cosine_dist + comorbidity_weight * comorbidity_dist
         where comorbidity_dist = mean |x_t - x_c| over comorbidity_cols (z-score normalized)
      Greedy 1:1 matching sorted by combined score ascending.
      exact_cols: columns to exact-match within (e.g. index_year for calendar-time matching).
    """
    df = df.copy().reset_index(drop=True)
    tm = (df["arm"] == treated_arm).values
    cm = (df["arm"] == control_arm).values
    tp_all = np.where(tm)[0]
    cp_all = np.where(cm)[0]
    n_attempted = len(tp_all)

    # Partition into exact-match strata if requested
    if exact_cols:
        keys = df[exact_cols].apply(lambda r: tuple(r), axis=1).values
        strata = sorted(set(keys[tm]))
    else:
        strata = [None]

    valid_cols = [c for c in comorbidity_cols if c in df.columns]
    if valid_cols:
        C_raw = df[valid_cols].values.astype(float)
        col_std = C_raw.std(axis=0)
        col_std[col_std == 0] = 1.0
        C = (C_raw - C_raw.mean(axis=0)) / col_std
    else:
        C = None

    pairs = []
    for stratum in strata:
        if stratum is None:
            tp, cp = tp_all, cp_all
        else:
            tp = tp_all[np.array([keys[i] == stratum for i in tp_all])]
            cp = cp_all[np.array([keys[i] == stratum for i in cp_all])]
        if len(tp) == 0 or len(cp) == 0:
            continue
        nn = NearestNeighbors(n_neighbors=len(cp), metric="cosine")
        nn.fit(X_raw[cp])
        dists, indices = nn.kneighbors(X_raw[tp])
        for ti, di, ii in zip(tp, dists, indices):
            for d, ci_idx in zip(di, ii):
                if d > cosine_threshold:
                    break
                ci = cp[ci_idx]
                comorbidity_dist = float(np.mean(np.abs(C[ti] - C[ci]))) if C is not None else 0.0
                combined = d + comorbidity_weight * comorbidity_dist
                pairs.append((combined, d, int(ti), int(ci)))

    pairs.sort(key=lambda x: x[0])
    used_t, used_c = set(), set()
    rows, all_dists, mid = [], [], 0

    for combined, cosine_d, ti, ci in pairs:
        if ti in used_t or ci in used_c:
            continue
        used_t.add(ti)
        used_c.add(ci)
        r = df.iloc[ti].copy(); r["match_id"] = mid; r["match_distance"] = cosine_d
        rows.append(r)
        r = df.iloc[ci].copy(); r["match_id"] = mid; r["match_distance"] = cosine_d
        rows.append(r)
        all_dists.append(cosine_d)
        mid += 1

    matched = pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()
    summary = {
        "n_treated_attempted": n_attempted,
        "n_treated_matched":   len(used_t),
        "n_total_rows":        len(matched),
        "median_match_distance": float(np.median(all_dists)) if all_dists else float("nan"),
        "max_match_distance":    float(np.max(all_dists))    if all_dists else float("nan"),
    }
    return matched, summary


def ps_ecg_match(
    df: pd.DataFrame,
    X_raw: np.ndarray,
    structured_cols: list[str],
    caliper_sd: float = 0.20,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    seed: int = 42,
) -> tuple[pd.DataFrame, dict]:
    """
    PS-calipered ECG nearest-neighbour matching (two-stage).

    Stage 1 — hard caliper on propensity score fitted to structured_cols:
        |PS_treated - PS_control| <= caliper_sd × SD(PS)
        Guarantees balance on measured clinical confounders.

    Stage 2 — within-caliper greedy 1:1 by cosine distance on ECG embeddings:
        Optimises balance on unmeasured ECG features (QRS duration, morphology,
        conduction intervals) that the PS model cannot see.

    Methodological basis: PS-caliper + auxiliary distance matching is standard
    in PE literature (Rosenbaum & Rubin 1985; Stuart 2010).  Each stage does
    what it is designed for; neither distorts the other.
    """
    df = df.copy().reset_index(drop=True)
    avail = [c for c in structured_cols if c in df.columns]
    if not avail:
        return pd.DataFrame(), {"n_treated_matched": 0, "n_treated_attempted": 0}

    feat = df[avail].astype(float)
    feat.replace([np.inf, -np.inf], np.nan, inplace=True)
    complete = feat.notna().all(axis=1)
    n_dropped = (~complete).sum()
    if n_dropped:
        print(f"  PS+ECG complete-case: dropping {n_dropped:,} rows ({complete.sum():,} remain)")

    df_cc   = df[complete].reset_index(drop=True)
    feat_cc = feat[complete].reset_index(drop=True)
    X_emb   = X_raw[complete.values]          # aligned to df_cc

    tm = (df_cc["arm"] == treated_arm).values
    cm = (df_cc["arm"] == control_arm).values
    tp = np.where(tm)[0]
    cp = np.where(cm)[0]

    # Fit propensity score
    sc  = StandardScaler()
    clf = LogisticRegression(max_iter=2000, C=1.0, solver="saga", random_state=seed)
    clf.fit(sc.fit_transform(feat_cc.values), tm.astype(int))
    ps = clf.predict_proba(sc.transform(feat_cc.values))[:, 1]

    # Caliper on logit(PS) in SD units (Austin), consistent with structured_psm.
    _eps = 1e-6
    ps_c = np.clip(ps, _eps, 1 - _eps)
    logit_ps = np.log(ps_c / (1 - ps_c))
    caliper = caliper_sd * logit_ps.std()
    print(f"  PS caliper: {caliper_sd} SD × logit_PS_std={logit_ps.std():.4f} → caliper={caliper:.4f}")

    # L2-normalise embeddings for cosine distance
    norms = np.linalg.norm(X_emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X_norm = X_emb / norms

    # For each treated: find controls within PS caliper, take closest by cosine
    pairs = []
    for ti in tp:
        in_cal = cp[np.abs(logit_ps[cp] - logit_ps[ti]) <= caliper]
        if len(in_cal) == 0:
            continue
        cosine_dists = 1.0 - float(X_norm[ti] @ X_norm[in_cal].T) if len(in_cal) == 1 \
            else 1.0 - (X_norm[ti] @ X_norm[in_cal].T)
        best = int(np.argmin(cosine_dists))
        pairs.append((float(np.min(cosine_dists)), int(ti), int(in_cal[best])))

    # Greedy 1:1 — sort by cosine distance ascending
    pairs.sort(key=lambda x: x[0])
    used_t, used_c = set(), set()
    rows, dists, mid = [], [], 0
    for d, ti, ci in pairs:
        if ti in used_t or ci in used_c:
            continue
        used_t.add(ti); used_c.add(ci)
        r = df_cc.iloc[ti].copy(); r["match_id"] = mid; r["match_distance"] = d
        rows.append(r)
        r = df_cc.iloc[ci].copy(); r["match_id"] = mid; r["match_distance"] = d
        rows.append(r)
        dists.append(d)
        mid += 1

    matched = pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()
    summary = {
        "n_treated_attempted":   len(tp),
        "n_treated_matched":     len(used_t),
        "n_total_rows":          len(matched),
        "median_match_distance": float(np.median(dists)) if dists else float("nan"),
        "max_match_distance":    float(np.max(dists))    if dists else float("nan"),
    }
    return matched, summary


# ── Plots ─────────────────────────────────────────────────────────────────────

def forest_plot(
    results: list[dict], output_path: Path,
    match_ratio: int, trial_name: str, reference_hr: float,
    treated_label: str = "carvedilol", control_label: str = "metoprolol",
    xlim: tuple[float, float] = (0.3, 1.6),
) -> None:
    # Per-method color (all markers are diamonds)
    def _color(label: str) -> str:
        lc = label.lower()
        if "unadjusted" in lc:
            return "#888888"
        if "adjusted" in lc and "unadjusted" not in lc:
            return "#555555"
        if "ps+ecg" in lc or "ps-caliper" in lc:
            return "#762a83"
        if "psm" in lc or "propensity" in lc:
            return "#2166ac"
        if "ecg" in lc or "nn" in lc:
            return "#d6604d"
        return "#888888"

    y = list(range(len(results)))

    fig, ax = plt.subplots(figsize=(11, 2.5 + len(results) * 0.75))

    for i, (r, yi) in enumerate(zip(results, y)):
        color = _color(r["label"])
        xerr_lo = r["hr"] - r["ci_low"]
        xerr_hi = r["ci_high"] - r["hr"]
        ax.errorbar(
            r["hr"], yi,
            xerr=[[xerr_lo], [xerr_hi]],
            fmt="D", color=color, ecolor=color,
            capsize=4, markersize=16, markeredgewidth=0.8,
            markeredgecolor="white", lw=2.5,
        )
        pval = r.get("p", float("nan"))
        n    = r.get("n", 0)
        p_str = f"p={pval:.3f}" if pval >= 0.001 else "p<0.001"
        ax.text(
            1.03, yi,
            f"HR {r['hr']:.2f} [{r['ci_low']:.2f}–{r['ci_high']:.2f}]  {p_str}  n={n:,}",
            transform=ax.get_yaxis_transform(), clip_on=False,
            va="center", ha="left", fontsize=13, color="#333333",
        )

    ax.axvline(reference_hr, color="#cccccc", ls="-", lw=1.5)
    ax.axvline(1.0, color="#444444", ls=":", lw=1.0)
    ax.set_xlim(*xlim)
    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] for r in results], fontsize=15)
    ax.set_xlabel(f"Hazard Ratio ({treated_label} vs. {control_label})", fontsize=15)
    ax.set_title(f"{trial_name} Emulation (HR={reference_hr})", fontsize=16)
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Forest plot → {output_path}")


def _add_gdmt_flags(cohort: pd.DataFrame, drug_pool_path: str) -> pd.DataFrame:
    """
    Compute GDMT polypharmacy flags (90d pre-index) from drug_master_pool.parquet.
    Adds: bb_90d, sglt2i_90d, gdmt_count (0–5: BB+ACEi/ARB+MRA+loop+SGLT2i).
    Falls back gracefully if file is missing.
    """
    from cohort_utils import (
        CARVEDILOL, METOPROLOL, OTHER_BB, ACEI_KEYWORDS, ARB_KEYWORDS,
        LOOP_DIURETICS, ALDOSTERONE_ANTAG, SGLT2I, drug_mask,
    )
    p = Path(drug_pool_path)
    if not p.is_file():
        print(f"  [GDMT] {p.name} not found — bb_90d/sglt2i_90d set to 0, gdmt_count from pool flags only")
        cohort["bb_90d"]     = 0
        cohort["sglt2i_90d"] = 0
        gdmt_cols = ["bb_90d", "acei_arb", "aldosterone_antag", "loop_diuretic", "sglt2i_90d"]
        avail = [c for c in gdmt_cols if c in cohort.columns]
        cohort["gdmt_count"] = cohort[avail].fillna(0).astype(int).sum(axis=1)
        return cohort

    # Push cohort MRNs into the parquet read to avoid loading all 400k+ pool records.
    cohort_mrns = cohort["MRN"].astype(str).str.strip().tolist()
    print(f"  [GDMT] reading drug_master_pool.parquet for {len(cohort_mrns):,} cohort MRNs …")
    dm = pd.read_parquet(p, columns=["MRN", "drug_upper", "_date"],
                         filters=[("MRN", "in", cohort_mrns)])
    print(f"  [GDMT] loaded {len(dm):,} drug records")
    dm["MRN"]        = dm["MRN"].astype(str).str.strip()
    dm["drug_upper"] = dm["drug_upper"].astype(str).str.upper()
    dm["_date"]      = pd.to_datetime(dm["_date"], errors="coerce")

    idx = cohort[["MRN", "index_date"]].copy()

    def _flag(keywords: list[str]) -> "pd.Series":
        sub = dm[drug_mask(dm["drug_upper"], keywords)].merge(idx, on="MRN", how="inner")
        lo  = sub["index_date"] - pd.Timedelta(days=90)
        active = (sub["_date"] >= lo) & (sub["_date"] <= sub["index_date"])
        return cohort["MRN"].isin(set(sub.loc[active, "MRN"])).astype(int)

    BB_KEYWORDS = CARVEDILOL + METOPROLOL + OTHER_BB
    cohort["bb_90d"]     = _flag(BB_KEYWORDS)
    cohort["sglt2i_90d"] = _flag(SGLT2I)

    gdmt_cols = ["bb_90d", "acei_arb", "aldosterone_antag", "loop_diuretic", "sglt2i_90d"]
    avail = [c for c in gdmt_cols if c in cohort.columns]
    cohort["gdmt_count"] = cohort[avail].fillna(0).astype(int).sum(axis=1)
    print(f"  [GDMT] bb_90d={cohort['bb_90d'].sum():,}  sglt2i_90d={cohort['sglt2i_90d'].sum():,}  "
          f"gdmt_count median={cohort['gdmt_count'].median():.1f}  "
          f"mean={cohort['gdmt_count'].mean():.2f}")
    return cohort


def _check_pool(n_t: int, n_c: int, k: int) -> int:
    if n_c < n_t * k:
        safe_k = max(1, n_c // n_t)
        print(f"  WARNING: control pool ({n_c}) < {n_t}×{k}. Falling back to 1:{safe_k}.")
        return safe_k
    return k


def sample_1to1(
    df: pd.DataFrame,
    treated_arm: str,
    control_arm: str,
    seed: int = 42,
) -> pd.DataFrame:
    """Randomly downsample the majority arm to achieve 1:1 balance."""
    treated = df[df["arm"] == treated_arm]
    control = df[df["arm"] == control_arm]
    n = min(len(treated), len(control))
    rng = np.random.default_rng(seed)
    t_idx = rng.choice(len(treated), size=n, replace=False)
    c_idx = rng.choice(len(control), size=n, replace=False)
    return pd.concat([
        treated.iloc[t_idx],
        control.iloc[c_idx],
    ]).reset_index(drop=True)


# ── Main ──────────────────────────────────────────────────────────────────────

# Rich PSM candidate pool — LASSO selects the non-zero-coefficient subset at runtime.
# Column names reflect stage3 rename_map: medication flags have no _90d suffix.
# Requires stage1 rerun whenever new condition_flags are added to the YAML config.
_RICH_PSM_CANDIDATES: list[str] = [
    # Demographics
    "age_at_index", "sex_binary", "race_black",
    # Echo
    "ef_at_index",
    # HF severity / coding history
    "hfref_icd_5y", "hfref_icd_24m", "hfref_icd_subcoded_i502_24m",
    "hf_icd_1y", "hf_icd_2y",
    # Comorbidities (ever / long-term)
    "afib", "htn", "dm", "cad_mi", "copd", "hyperlipidemia", "stroke",
    # Comorbidities — recent / multi-window
    "afib_1y", "afib_5y", "dm_1y", "cad_1y", "cad_5y", "stroke_1y",
    "ckd_3", "anemia_2y", "pvd_5y", "osa_5y", "hypothyroid_5y",
    "depression_2y", "ventricular_arrh_2y", "cardiac_device_5y",
    "aki_1y", "atrial_flutter_2y",
    "hyponatremia_1y", "hyperkalemia_1y",
    "valvular_2y", "obesity_5y", "iron_deficiency_2y",
    # Medications 90d pre-index (stage3 renames _90d → no suffix)
    "loop_diuretic", "aldosterone_antag", "digoxin",
    "statin", "nitrate", "beta_blocker",
    "warfarin", "doac", "antiplatelet", "amiodarone",
    # ECG intervals
    "hr_at_index", "QRS_Duration", "PR_Interval",
    # Labs & vitals (present when stage1 run with --measurement-dir; MICE-imputed)
    "lab_egfr", "lab_creatinine", "lab_chol_total", "lab_hdl", "lab_hba1c",
    "vital_sbp", "vital_bmi",
    # GDMT polypharmacy (stage4-computed from drug_master_pool)
    "bb_90d", "sglt2i_90d",
    # Adherence
    "n_refills_assigned_90d", "n_refills_assigned_180d",
    # Calendar time (index year — controls for secular trends in prescribing)
    "index_year",
]

_ADJ_COX_CANDIDATES: list[str] = [
    "age_at_index", "sex_binary", "race_black",
    "ef_at_index",
    "afib", "htn", "dm", "cad_mi", "copd", "hyperlipidemia", "stroke",
    "loop_diuretic", "beta_blocker",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage 4: unadjusted Cox / adjusted Cox / rich PSM"
    )
    p.add_argument("--cohort",             required=True)
    p.add_argument("--embed-dir",          default="",
                   help="Embedding directory (optional — reserved for future ECG methods)")
    p.add_argument("--output-dir",         required=True)
    p.add_argument("--treated-arm",        default="carvedilol")
    p.add_argument("--control-arm",        default="metoprolol")
    p.add_argument("--trial-name",         default="COMET")
    p.add_argument("--reference-hr",       type=float, default=COMET_HR)
    p.add_argument("--event-col",          default="")
    p.add_argument("--time-col",           default="")
    p.add_argument("--caliper-sd",         type=float, default=0.20,
                   help="Matching caliper in SD units of logit(PS) (Austin 0.2 default).")
    p.add_argument("--structured-caliper", type=float, default=None,
                   help="DEPRECATED alias for --caliper-sd (was a raw-PS caliper). "
                        "If set, its value is used as --caliper-sd.")
    p.add_argument("--n-imputations",      type=int,   default=1,
                   help="MICE imputations for missing continuous covariates. "
                        "1 = complete-case (legacy behavior, reproduces prior numbers); "
                        "5 recommended for reporting.")
    p.add_argument("--max-missing-frac",   type=float, default=0.5,
                   help="Drop covariates more than this fraction missing from the PS "
                        "model (still reported in the balance table). 1.0 = keep all.")
    p.add_argument("--denominator",        choices=["strict", "both"], default="strict",
                   help="strict = ladder on ECG-available ∩ rich-covariates-complete "
                        "(a complete-case sensitivity rung under imputation). "
                        "both = also emit the strict complete-case rung alongside the imputed primary.")
    p.add_argument("--match-ratio",        type=int,   default=1)
    p.add_argument("--forest-xlim",        default="0.3,1.6")
    p.add_argument("--seed",               type=int,   default=42)
    p.add_argument("--drug-pool",          default="",
                   help="Path to drug_master_pool.parquet for GDMT flags (bb_90d, sglt2i_90d).")
    p.add_argument("--exclude-psm-cols",   type=str,   default="",
                   help="Comma-separated columns to drop from PSM and adjusted Cox "
                        "(e.g. 'acei_arb_90d' when structurally confounded with treatment).")
    args = p.parse_args()
    if args.structured_caliper is not None:
        print("  NOTE: --structured-caliper is deprecated; using its value for --caliper-sd. "
              "The caliper is now on logit(PS) in SD units, not raw PS.")
        args.caliper_sd = args.structured_caliper
    return args


def main() -> None:
    args = parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    TREATED, CONTROL = args.treated_arm, args.control_arm
    TRIAL,   REF_HR  = args.trial_name,  args.reference_hr

    # ── Load cohort ───────────────────────────────────────────────────────────
    cohort = pd.read_parquet(args.cohort)
    cohort["person_id"] = cohort["person_id"].astype(str)
    if "sex_binary" not in cohort.columns:
        cohort["sex_binary"] = (cohort["sex"] == "F").astype(float)

    # ── Outcome ───────────────────────────────────────────────────────────────
    global _EVENT_COL, _TIME_COL
    if args.event_col and args.time_col:
        _EVENT_COL, _TIME_COL = args.event_col, args.time_col
    elif "event_primary" in cohort.columns and cohort["event_primary"].sum() > 0:
        _EVENT_COL, _TIME_COL = "event_primary", "time_to_primary"
    else:
        _EVENT_COL, _TIME_COL = "event_death", "time_to_death"

    n_treated = (cohort["arm"] == TREATED).sum()
    n_control = (cohort["arm"] == CONTROL).sum()
    print(f"Cohort: {len(cohort):,}  {TREATED}={n_treated:,}  {CONTROL}={n_control:,}")
    print(f"Outcome: {_EVENT_COL}  events={cohort[_EVENT_COL].sum():,}")
    print(f"Reference HR ({TRIAL}): {REF_HR}")
    print(f"{'='*60}")

    if n_treated == 0 or n_control == 0:
        print(f"ERROR: empty arm — cannot run. Check arm keywords in config.")
        sys.exit(1)

    # ── Derived columns ───────────────────────────────────────────────────────
    if "index_date" in cohort.columns:
        cohort["index_year"] = pd.to_datetime(cohort["index_date"]).dt.year

    # ── GDMT flags ────────────────────────────────────────────────────────────
    drug_pool_path = args.drug_pool or str(Path(args.cohort).parent.parent / "drug_master_pool.parquet")
    cohort = _add_gdmt_flags(cohort, drug_pool_path)

    # ── Covariate sets ────────────────────────────────────────────────────────
    _excl = {c.strip() for c in args.exclude_psm_cols.split(",") if c.strip()}
    if _excl:
        print(f"Excluded from PSM/Cox: {sorted(_excl)}")

    RICH_PSM_COVS = [
        c for c in _RICH_PSM_CANDIDATES
        if c in cohort.columns and c not in _excl
    ]
    ADJ_COVS = [
        c for c in _ADJ_COX_CANDIDATES
        if c in cohort.columns and c not in _excl
    ]
    SMD_COLS = list(_balance_mod.SMD_COLS)

    # Drop covariates that are more than --max-missing-frac missing from the PS
    # model: matching on a majority-imputed covariate adds noise for (usually)
    # weak confounders and inflates FMI. They stay in SMD_COLS, so balance is
    # still reported (reported-only, like structurally-excluded covariates).
    if args.max_missing_frac < 1.0:
        _miss = {c: float(cohort[c].isna().mean()) for c in RICH_PSM_COVS if c in cohort.columns}
        _too_sparse = sorted(c for c, f in _miss.items() if f > args.max_missing_frac)
        if _too_sparse:
            print(f"Dropping {len(_too_sparse)} covariate(s) >{args.max_missing_frac:.0%} "
                  f"missing from PSM (kept in balance): "
                  f"{[(c, f'{_miss[c]:.0%}') for c in _too_sparse]}")
            RICH_PSM_COVS = [c for c in RICH_PSM_COVS if c not in _too_sparse]

    print(f"Rich PSM covariates ({len(RICH_PSM_COVS)}): {RICH_PSM_COVS}")
    print(f"Adjusted Cox covariates ({len(ADJ_COVS)}): {ADJ_COVS}")

    # ── Denominator audit (ECG-available ∩ rich-covariates-complete) ──────────
    try:
        emb_df = load_embeddings(args.embed_dir, cohort) if args.embed_dir else pd.DataFrame()
    except Exception as e:
        print(f"  NOTE: embedding load skipped ({e})")
        emb_df = pd.DataFrame()
    try:
        masks = build_masks(cohort, emb_df, RICH_PSM_COVS)
        audit = audit_table(cohort, masks, TREATED, CONTROL, event_col=_EVENT_COL)
        print_audit(audit)
        audit.to_csv(out / "denominator_audit.csv", index=False)
        miss = missingness_audit(cohort, RICH_PSM_COVS, masks.get("echo_complete"))
        miss.to_csv(out / "missingness_audit.csv", index=False)
        strict_mask = masks.get("intersection_strict")
    except Exception as e:
        print(f"  NOTE: denominator audit skipped ({e})")
        strict_mask = None

    # ── Multiple imputation of missing continuous covariates ──────────────────
    added_ind: list[str] = []
    if args.n_imputations >= 2:
        from imputation import make_imputations
        _impute_covs = sorted(set(RICH_PSM_COVS) | set(ADJ_COVS) | set(SMD_COLS))
        imputations, added_ind = make_imputations(
            cohort, _impute_covs, n_imputations=args.n_imputations, seed=args.seed,
            treatment_col="arm", treated_arm=TREATED,
            event_col=_EVENT_COL, time_col=_TIME_COL,
        )
        for c in added_ind:
            if c not in RICH_PSM_COVS:
                RICH_PSM_COVS.append(c)
            if c not in SMD_COLS:
                SMD_COLS.append(c)
        print(f"MICE: {len(imputations)} imputed datasets; indicators added: {added_ind}")
    else:
        imputations = [cohort]

    # Strict complete-case cohort (sensitivity rung under imputation).
    strict_cohort = (cohort[strict_mask].reset_index(drop=True)
                     if strict_mask is not None and strict_mask.any() else cohort)

    # ── Arm summary ───────────────────────────────────────────────────────────
    arm_df = arm_summary(cohort, treated_arm=TREATED, control_arm=CONTROL)
    print_arm_summary(arm_df, label="full cohort")
    arm_df.to_csv(out / "arm_summary.csv", index=False)

    er_df = event_rate_by_arm(cohort, treated_arm=TREATED, control_arm=CONTROL,
                               event_col=_EVENT_COL, duration_col=_TIME_COL)
    print_event_rates(er_df)
    plot_index_date_distribution(cohort, out / "index_date_dist.png",
                                 treated_arm=TREATED, control_arm=CONTROL)

    # ── Pre-match balance ─────────────────────────────────────────────────────
    bal_pre = build_balance_table(cohort, None, cols=SMD_COLS,
                                  treated_arm=TREATED, control_arm=CONTROL,
                                  label="pre_match")
    print("\nPre-match balance:")
    print_balance_table(bal_pre)

    results_summary: list[dict] = []
    post_matched: dict[str, pd.DataFrame] = {}
    k = _check_pool(n_treated, n_control, args.match_ratio)
    _mi = args.n_imputations >= 2
    _denom_label = f"imputed(m={args.n_imputations})" if _mi else "complete-case"

    # ── 1. Unadjusted Cox ────────────────────────────────────────────────────
    print(f"\n1. Unadjusted Cox  (1:1)")
    def _unadj(d):
        return cox_hr(sample_1to1(d, TREATED, CONTROL, args.seed), treated_arm=TREATED)
    r1 = _pool_over_imputations(_unadj, imputations)
    print_res("Unadjusted", r1)
    results_summary.append({"label": "Unadjusted Cox", "denominator": _denom_label, **r1})

    # ── 2. Adjusted Cox ───────────────────────────────────────────────────────
    print(f"\n2. Adjusted Cox  ({len(ADJ_COVS)} covariates, 1:1)")
    def _adj(d):
        return cox_hr(sample_1to1(d, TREATED, CONTROL, args.seed),
                      covariates=ADJ_COVS, treated_arm=TREATED)
    r2 = _pool_over_imputations(_adj, imputations)
    print_res("Adjusted Cox", r2)
    results_summary.append({"label": "Adjusted Cox", "denominator": _denom_label, **r2})

    # ── 3. Rich PSM ──────────────────────────────────────────────────────────
    print(f"\n3. Rich PSM  ({len(RICH_PSM_COVS)} covariates, caliper-sd={args.caliper_sd})")
    matched_frames: list[pd.DataFrame] = []
    try:
        r3, matched_frames = structured_psm_pooled(
            imputations, RICH_PSM_COVS, k=k, caliper_sd=args.caliper_sd,
            treated_arm=TREATED, control_arm=CONTROL, seed=args.seed,
        )
        if matched_frames:
            psm_matched = matched_frames[0]
            print_res(f"Rich PSM 1:{k}", r3)
            results_summary.append({"label": "Rich PSM", "denominator": _denom_label, **r3})
            post_matched["PSM"] = psm_matched

            # KM plot (first imputation)
            try:
                plot_km(psm_matched, out / "km_PSM.png",
                        treated_arm=TREATED, control_arm=CONTROL,
                        title=f"KM — Rich PSM ({TRIAL})",
                        event_col=_EVENT_COL, duration_col=_TIME_COL)
                print("  KM → km_PSM.png")
            except Exception as e:
                print(f"  KM failed: {e}")
        else:
            print("  No matches — try a larger --caliper-sd")
    except Exception as e:
        print(f"  Rich PSM failed: {e}")

    # ── 3b. Rich PSM strict complete-case sensitivity (under imputation) ───────
    if _mi and args.denominator == "both":
        print(f"\n3b. Rich PSM — strict complete-case sensitivity (n={len(strict_cohort):,})")
        try:
            cc_matched, _ = structured_psm(
                strict_cohort, RICH_PSM_COVS, k=k, caliper_sd=args.caliper_sd,
                treated_arm=TREATED, control_arm=CONTROL, seed=args.seed,
            )
            if cc_matched is not None and not cc_matched.empty:
                r3cc = cox_hr(cc_matched, treated_arm=TREATED, strata=["match_id"])
                print_res(f"Rich PSM (complete-case) 1:{k}  n={len(cc_matched):,}", r3cc)
                results_summary.append({"label": "Rich PSM (complete-case)",
                                        "denominator": "complete-case", **r3cc})
        except Exception as e:
            print(f"  Strict-CC PSM failed: {e}")

    # ── Balance table pre vs post PSM ─────────────────────────────────────────
    if "PSM" in post_matched:
        # MI-pooled balance (averaged over imputations) + complete-case sensitivity cols.
        tbl = pooled_balance_table(
            imputations, matched_frames,
            cc_pre=cohort, cc_post=post_matched["PSM"],
            cols=SMD_COLS, treated_arm=TREATED, control_arm=CONTROL, label="PSM",
        )
        tbl.to_csv(out / "balance_table_PSM.csv", index=False)
        if not tbl.empty:
            if "smd_pre" in tbl.columns and "smd_post" in tbl.columns:
                print(f"\nRich PSM pre vs post-match SMD:")
                print(f"  {'Covariate':<28}  {'pre':>6}  {'post':>6}  {'delta':>7}")
                print(f"  {'-'*28}  {'-'*6}  {'-'*6}  {'-'*7}")
                t = tbl.set_index("covariate")
                for cov in SMD_COLS:
                    if cov not in t.index:
                        continue
                    pre = t.loc[cov, "smd_pre"]
                    post = t.loc[cov, "smd_post"]
                    if pd.isna(pre):
                        continue
                    flag = " !" if (not pd.isna(post) and post > 0.1) else ""
                    pre_s  = f"{pre:.3f}"  if not pd.isna(pre)  else "   —"
                    post_s = f"{post:.3f}" if not pd.isna(post) else "   —"
                    delta_s = f"{post-pre:+.3f}" if not pd.isna(post) else "     —"
                    print(f"  {cov:<28}  {pre_s:>6}  {post_s:>6}  {delta_s:>7}{flag}")

            smd_pre_s = bal_pre.set_index("covariate")["smd_pre"]
            smd_post_s = tbl.set_index("covariate")["smd_post"]
            try:
                plot_love(smd_pre_s, smd_post_s, out / "love_plot_PSM.png",
                          title=f"{TRIAL} — Rich PSM Balance",
                          post_label="Rich PSM")
                print("\n  Love plot → love_plot_PSM.png")
            except Exception as e:
                print(f"  Love plot failed: {e}")

    # ── Results CSV + forest plot ─────────────────────────────────────────────
    pd.DataFrame(results_summary).to_csv(out / "results_summary.csv", index=False)

    primary_rows = [r for r in results_summary if not np.isnan(r.get("hr", float("nan")))]
    if primary_rows:
        _xlim = tuple(float(v) for v in args.forest_xlim.split(","))
        forest_plot(primary_rows, out / "forest.png",
                    match_ratio=k, trial_name=TRIAL, reference_hr=REF_HR,
                    treated_label=TREATED, control_label=CONTROL,
                    xlim=_xlim)
        print("  Forest plot → forest.png")

    print(f"\n{'='*60}")
    print(f"  Results → {out}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
