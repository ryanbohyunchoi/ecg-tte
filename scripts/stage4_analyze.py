"""
ecg-tte-prep/stage4_analyze.py

Stage 4: Comparator ladder + balance table + forest plot.
Generic analysis pipeline for ecg-tte. Comparator ladder:
  Unadjusted Cox → Adjusted Cox → PSM-sparse → PSM-rich → ECG-NN matching.
Pass --published-hr to overlay the RCT ground truth on the forest plot.

Comparator ladder (the "story"):
  1. Unadjusted Cox                  — reference; expect confounded HR > 0.83
  2. Adjusted Cox                    — age, sex, key comorbidities; partial correction
  3. PSM-sparse                      — age, sex, EF (traditional minimal)
  4. PSM-rich                        — adds ECG intervals, medications, comorbidities
  5. PSM on BCL embeddings           — embedding propensity score
  6. ECG NN PRIMARY                  — cosine ≤ abs_threshold (pre-specified)
  7. ECG NN p100                     — no threshold; reported alongside PRIMARY
  8. ECG NN sweep                    — cosine p25/50/75/90/100 (supplementary)
  9. Forest plot

Denominator standardization (--denominator flag):
  strict  (default) — all methods run on D = (ECG-available) ∩ (rich-covariates complete).
  natural           — each method on its natural subset (legacy behaviour).
  both              — strict primary ladder + ECG-NN sensitivity on the larger ecg_available cohort.

Balance reporting:
  For each matching method the balance table is computed twice:
    (a) full SMD_COLS — 18 covariates (for transparency / supplement)
    (b) held-out only — covariates NOT used by that method during matching
  Held-out balance is the fair comparison metric: PSM-rich cannot claim credit
  for balancing features it directly matched on, while ECG-NN's held-out set is
  the full 18 (it sees no structured covariates during matching).

Diagnostics (--diagnostics flag, default on):
  arm_summary, event rates, KM curves, index-date distribution,
  immortal-time check, match-distance distribution.

Usage:
    python trialemulation/methods/comet/analyze_comet.py \\
        --cohort     /mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet/runs/default/comet_cohort.parquet \\
        --embed-dir  /mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet/embeddings/biometric \\
        --output-dir /mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet/runs/default \\
        --denominator strict
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
    summarize_split, compute_cci, cci_smd,
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
    print(f"  {label:<50} HR={res['hr']:.3f} "
          f"[{res['ci_low']:.3f}–{res['ci_high']:.3f}]  p={res['p']:.4f}  n={res['n']}")


# ── PSM helpers ───────────────────────────────────────────────────────────────

def _greedy_match(
    df: pd.DataFrame,
    ps: np.ndarray,
    k: int,
    caliper: float,
    treated_arm: str,
    control_arm: str,
) -> pd.DataFrame:
    """Shared greedy 1:k matching on propensity score."""
    df = df.copy().reset_index(drop=True)
    df["ps"] = ps
    treated_idx = df.index[df["arm"] == treated_arm].tolist()
    control_idx = df.index[df["arm"] == control_arm].tolist()
    n_nb = min(k * 2, len(control_idx))
    nn = NearestNeighbors(n_neighbors=n_nb, metric="euclidean")
    nn.fit(df.loc[control_idx, ["ps"]].values)
    dists, indices = nn.kneighbors(df.loc[treated_idx, ["ps"]].values)

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
    caliper: float = 0.25,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    seed: int = 42,
    use_lasso: bool = True,
) -> pd.DataFrame:
    """
    Propensity score matching with optional LASSO feature selection (LEGEND-T2D style).
    When use_lasso=True: L1-penalized logistic regression with 5-fold CV selects
    non-zero-coefficient features; ordinary LR is then refit on selected features.
    """
    from sklearn.linear_model import LogisticRegressionCV
    avail = [c for c in covariates if c in df.columns]
    if not avail:
        return pd.DataFrame()
    feat = df[avail].copy().astype(float)
    feat.replace([np.inf, -np.inf], np.nan, inplace=True)
    complete = feat.notna().all(axis=1)
    n_dropped = (~complete).sum()
    if n_dropped > 0:
        print(f"  PSM complete-case: dropping {n_dropped:,} rows with missing covariates "
              f"({complete.sum():,} remain)")
    else:
        print(f"  PSM complete-case: 0 rows dropped ({complete.sum():,} rows complete) ✓")
    df   = df[complete].reset_index(drop=True)
    feat = feat[complete].reset_index(drop=True)
    sc   = StandardScaler()
    X    = sc.fit_transform(feat.values)
    y    = (df["arm"] == treated_arm).astype(int).values

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
        sel_feats = [f for f, s in zip(avail, sel_mask) if s]
        print(f"  LASSO selected {sel_mask.sum()}/{len(avail)} features  "
              f"(best C={lasso_clf.C_[0]:.4f})")
        print(f"  Selected covariates: {sel_feats}")
        if sel_mask.sum() == 0:
            print("  WARNING: LASSO removed all features — falling back to all candidates")
            sel_mask = _np.ones(len(avail), dtype=bool)
        X = X[:, sel_mask]

    clf = LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs", random_state=seed)
    clf.fit(X, y)
    ps  = clf.predict_proba(X)[:, 1]
    return _greedy_match(df, ps, k, caliper, treated_arm, control_arm)


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

    caliper = caliper_sd * ps.std()
    print(f"  PS caliper: {caliper_sd} SD × PS_std={ps.std():.4f} → caliper={caliper:.4f}")

    # L2-normalise embeddings for cosine distance
    norms = np.linalg.norm(X_emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X_norm = X_emb / norms

    # For each treated: find controls within PS caliper, take closest by cosine
    pairs = []
    for ti in tp:
        in_cal = cp[np.abs(ps[cp] - ps[ti]) <= caliper]
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
    p.add_argument("--structured-caliper", type=float, default=0.25)
    p.add_argument("--match-ratio",        type=int,   default=1)
    p.add_argument("--forest-xlim",        default="0.3,1.6")
    p.add_argument("--seed",               type=int,   default=42)
    p.add_argument("--drug-pool",          default="",
                   help="Path to drug_master_pool.parquet for GDMT flags (bb_90d, sglt2i_90d).")
    p.add_argument("--exclude-psm-cols",   type=str,   default="",
                   help="Comma-separated columns to drop from PSM and adjusted Cox "
                        "(e.g. 'acei_arb_90d' when structurally confounded with treatment).")
    return p.parse_args()


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

    print(f"Rich PSM covariates ({len(RICH_PSM_COVS)}): {RICH_PSM_COVS}")
    print(f"Adjusted Cox covariates ({len(ADJ_COVS)}): {ADJ_COVS}")

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

    # ── 1:1 downsample for unmatched Cox ─────────────────────────────────────
    cohort_1to1 = sample_1to1(cohort, TREATED, CONTROL, args.seed)

    # ── 1. Unadjusted Cox ────────────────────────────────────────────────────
    print(f"\n1. Unadjusted Cox  (1:1 n={len(cohort_1to1):,})")
    r1 = cox_hr(cohort_1to1, treated_arm=TREATED)
    print_res("Unadjusted", r1)
    results_summary.append({"label": "Unadjusted Cox", **r1})

    # ── 2. Adjusted Cox ───────────────────────────────────────────────────────
    print(f"\n2. Adjusted Cox  ({len(ADJ_COVS)} covariates, 1:1 n={len(cohort_1to1):,})")
    r2 = cox_hr(cohort_1to1, covariates=ADJ_COVS, treated_arm=TREATED)
    print_res("Adjusted Cox", r2)
    results_summary.append({"label": "Adjusted Cox", **r2})

    # ── 3. Rich PSM ──────────────────────────────────────────────────────────
    print(f"\n3. Rich PSM  ({len(RICH_PSM_COVS)} covariates, caliper={args.structured_caliper})")
    try:
        psm_matched = structured_psm(cohort, RICH_PSM_COVS, k=k,
                                     caliper=args.structured_caliper,
                                     treated_arm=TREATED, control_arm=CONTROL,
                                     seed=args.seed)
        if not psm_matched.empty:
            r3 = cox_hr(psm_matched, treated_arm=TREATED, strata=["match_id"])
            print_res(f"Rich PSM 1:{k}  n={len(psm_matched):,}", r3)
            results_summary.append({"label": "Rich PSM", **r3})
            post_matched["PSM"] = psm_matched

            # KM plot
            try:
                plot_km(psm_matched, out / "km_PSM.png",
                        treated_arm=TREATED, control_arm=CONTROL,
                        title=f"KM — Rich PSM ({TRIAL})",
                        event_col=_EVENT_COL, duration_col=_TIME_COL)
                print("  KM → km_PSM.png")
            except Exception as e:
                print(f"  KM failed: {e}")
        else:
            print("  No matches — try --structured-caliper 0.5")
    except Exception as e:
        print(f"  Rich PSM failed: {e}")

    # ── Balance table pre vs post PSM ─────────────────────────────────────────
    if "PSM" in post_matched:
        bal_tables = write_balance_tables(
            cohort, post_matched, output_dir=out,
            cols=SMD_COLS, treated_arm=TREATED, control_arm=CONTROL,
        )
        if "PSM" in bal_tables:
            tbl = bal_tables["PSM"]
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
