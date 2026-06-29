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
) -> pd.DataFrame:
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
    sc  = StandardScaler()
    clf = LogisticRegression(max_iter=2000, C=1.0, solver="saga", random_state=seed)
    X   = sc.fit_transform(feat.values)
    clf.fit(X, (df["arm"] == treated_arm).astype(int).values)
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

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="COMET Stage 4: comparator ladder + balance + forest plot"
    )
    p.add_argument("--cohort",           required=True)
    p.add_argument("--embed-dir",        required=True)
    p.add_argument("--output-dir",       required=True)
    p.add_argument("--match-ratio",      type=int,   default=1)
    p.add_argument("--abs-threshold",    type=float, default=0.30,
                   help="Primary cosine distance threshold (default 0.30 ≈ similarity ≥ 0.70)")
    p.add_argument("--caliper",          type=float, default=0.05,
                   help="ECG embedding PSM caliper")
    p.add_argument("--structured-caliper", type=float, default=0.25)
    p.add_argument("--ps-caliper-sd", type=float, default=0.20,
                   help="PS-caliper width as fraction of PS SD for PS+ECG-NN method (default 0.20)")
    p.add_argument("--drug-pool", default="",
                   help="Path to drug_master_pool.parquet for GDMT polypharmacy computation "
                        "(bb_90d, sglt2i_90d, gdmt_count). Default: auto-detect as sibling of cohort.")
    p.add_argument("--treated-arm",      default="carvedilol")
    p.add_argument("--control-arm",      default="metoprolol")
    p.add_argument("--trial-name",       default="COMET")
    p.add_argument("--reference-hr",     type=float, default=COMET_HR)
    p.add_argument("--event-col",        default="",
                   help="Event indicator column (default: auto-detect — uses event_primary "
                        "if present in cohort and has events, else event_death).")
    p.add_argument("--time-col",         default="",
                   help="Time-to-event column (default: auto-detect — pairs with --event-col).")
    p.add_argument("--forest-xlim",      default="0.3,1.6",
                   help="Forest plot x-axis limits as 'lo,hi' (default: 0.3,1.6)")
    p.add_argument("--seed",             type=int,   default=42)
    p.add_argument(
        "--denominator",
        choices=["strict", "natural", "both"],
        default="strict",
        help=(
            "strict  — all methods on D = (ECG-available) ∩ (rich-covariates complete); "
            "natural — each method on its natural subset (legacy); "
            "both    — strict primary ladder + ECG-NN sensitivity on ecg_available"
        ),
    )
    p.add_argument("--no-diagnostics", action="store_true",
                   help="Skip diagnostic outputs (KM, arm summary, immortal-time check)")
    p.add_argument("--no-ef", action="store_true",
                   help="Remove ef_at_index from PSM covariate sets; allows patients without echo into D")
    afib_grp = p.add_mutually_exclusive_group()
    afib_grp.add_argument("--exclude-afib", action="store_true",
                          help="Restrict analysis to afib=0 patients (non-afib stratum)")
    afib_grp.add_argument("--afib-only", action="store_true",
                          help="Restrict analysis to afib=1 patients (afib stratum)")
    p.add_argument("--exact-match-cols", type=str, default="",
                   help="Comma-separated cohort columns for exact matching inside ECG-NN "
                        "(e.g. 'afib'). Does not affect PSM or Cox methods.")
    p.add_argument("--exclude-psm-cols", type=str, default="",
                   help="Comma-separated covariate columns to drop from PSM, Cox, and balance "
                        "tables (e.g. 'acei_arb' for PARADIGM where it is structural).")
    p.add_argument("--exclude-match-cols", type=str, default="",
                   help="Comma-separated columns to drop from PSM covariates, ECG-NN+Comorbidity "
                        "tabular cols, and doubly-robust adjustment — but KEEP in SMD balance table. "
                        "Use for variables like race_black that should be reported but not used "
                        "for matching (e.g. '--exclude-match-cols race_black').")
    p.add_argument("--multimodal-comorbidity-cols", type=str,
                   default="",
                   help="Comma-separated columns for the ECG+comorbidity matcher. "
                        "Default '' = use STRUCTURED_COVS (same as Structured PSM). "
                        "Pass an explicit list to override.")
    p.add_argument("--calendar-match", action="store_true",
                   help="Exact-match ECG-NN within index_year (calendar-time stratum).")
    p.add_argument("--multimodal-comorbidity-weight", type=float, default=1.0,
                   help="Weight on comorbidity distance relative to cosine distance (default 1.0).")
    p.add_argument("--adjust-matched-cols", default="ef_at_index,race_black",
                   help="Comma-separated covariates for doubly-robust within-pair Cox on ECG-NN "
                        "matched sets. Removes residual confounding the encoder can't see. "
                        "Default 'ef_at_index,race_black'. Pass '' to disable.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    TREATED, CONTROL = args.treated_arm, args.control_arm
    TRIAL,   REF_HR  = args.trial_name,  args.reference_hr
    run_diag = not args.no_diagnostics
    exact_match_cols = [c.strip() for c in args.exact_match_cols.split(",") if c.strip()] or []
    if args.calendar_match:
        exact_match_cols = list(dict.fromkeys(exact_match_cols + ["index_year"]))
        print(f"  [--calendar-match] ECG-NN will exact-match within index_year")
    exact_match_cols = exact_match_cols or None
    if exact_match_cols:
        print(f"  [--exact-match-cols] ECG-NN exact-match cols: {exact_match_cols}")
    MATCHED_ADJ_COLS = [c.strip() for c in args.adjust_matched_cols.split(",") if c.strip()]
    if MATCHED_ADJ_COLS:
        print(f"  [--adjust-matched-cols] doubly-robust Cox will adjust for: {MATCHED_ADJ_COLS}")

    # ── Load cohort ───────────────────────────────────────────────────────────
    cohort = pd.read_parquet(args.cohort)
    cohort["person_id"] = cohort["person_id"].astype(str)
    if "sex_binary" not in cohort.columns:
        cohort["sex_binary"] = (cohort["sex"] == "F").astype(float)
    if "index_date" in cohort.columns:
        cohort["index_year"] = pd.to_datetime(cohort["index_date"]).dt.year

    if args.exclude_afib:
        n_before = len(cohort)
        cohort = cohort[cohort["afib"] == 0].reset_index(drop=True)
        print(f"  [--exclude-afib] Restricted to afib=0: {n_before:,} → {len(cohort):,} patients")
    elif args.afib_only:
        n_before = len(cohort)
        cohort = cohort[cohort["afib"] == 1].reset_index(drop=True)
        print(f"  [--afib-only] Restricted to afib=1: {n_before:,} → {len(cohort):,} patients")

    # ── Outcome column selection ──────────────────────────────────────────────
    # Explicit CLI override > auto-detect from cohort.
    global _EVENT_COL, _TIME_COL
    if args.event_col and args.time_col:
        _EVENT_COL, _TIME_COL = args.event_col, args.time_col
    elif (
        "event_primary" in cohort.columns
        and "time_to_primary" in cohort.columns
        and cohort["event_primary"].sum() > 0
    ):
        _EVENT_COL, _TIME_COL = "event_primary", "time_to_primary"
    else:
        _EVENT_COL, _TIME_COL = "event_death", "time_to_death"
    print(f"  [outcome] {_EVENT_COL} / {_TIME_COL}")

    print(f"Cohort: {len(cohort):,}  "
          + "  ".join(f"{k}={v:,}" for k, v in sorted(cohort["arm"].value_counts().to_dict().items())))
    print(f"Events: {cohort[_EVENT_COL].sum():,}  ({_EVENT_COL})")
    print(f"\nReference HR ({TRIAL} published): {REF_HR}")
    print(f"{'='*70}")

    # Covariate sets (defined early — used by denominator masks and methods)
    if args.no_ef:
        print("  [--no-ef] ef_at_index not included in PSM covariate sets (already excluded)")
    ADJ_COVS = ["age_at_index", "sex_binary", "race_black"]

    # Drop excluded columns from PSM/Cox covariate sets ONLY — NOT from SMD display.
    # Kept in SMD_COLS so the balance table shows held-out balance for all features,
    # including ECG intervals and medications that PSM/PS+ECG-NN don't match on.
    _excl = [c.strip() for c in args.exclude_psm_cols.split(",") if c.strip()]
    SMD_COLS = list(_balance_mod.SMD_COLS)  # local copy — never filtered by _excl
    if _excl:
        print(f"  [--exclude-psm-cols] dropping from PSM/Cox covariate sets (kept in SMD): {_excl}")

    # --exclude-match-cols: remove from matching/adjustment but NOT from SMD display.
    _excl_match = [c.strip() for c in args.exclude_match_cols.split(",") if c.strip()]
    if _excl_match:
        print(f"  [--exclude-match-cols] dropping from matching/adjustment only (kept in SMD): {_excl_match}")
        ADJ_COVS         = [c for c in ADJ_COVS         if c not in _excl_match]
        MATCHED_ADJ_COLS = [c for c in MATCHED_ADJ_COLS if c not in _excl_match]

    # GDMT polypharmacy: compute bb_90d, sglt2i_90d, gdmt_count from drug_master_pool.
    drug_pool_path = args.drug_pool or str(Path(args.cohort).parent.parent / "drug_master_pool.parquet")
    cohort = _add_gdmt_flags(cohort, drug_pool_path)

    # CCI scalar (partial Charlson from existing comorbidity flags).
    cohort["cci_score"] = compute_cci(cohort)

    # STRUCTURED_COVS: covariate set for Structured PSM and PS-caliper in PS+ECG-NN.
    _structured_base = [
        "age_at_index", "sex_binary", "race_black",
        "afib", "htn", "dm", "cad_mi", "copd", "hyperlipidemia", "stroke",
        "prior_hf_code_1yr",
    ]
    STRUCTURED_COVS = [
        c for c in _structured_base
        if c in cohort.columns and c not in _excl and c not in _excl_match
    ]
    print(f"  STRUCTURED_COVS ({len(STRUCTURED_COVS)}): {STRUCTURED_COVS}")

    # Which covariates each method had direct access to during matching.
    # PS+ECG-NN uses STRUCTURED_COVS for the PS model (caliper), so those
    # are "in-model" — held-out balance shows only ECG-derived features.
    IN_MODEL_COVS = {
        "PSM":            STRUCTURED_COVS,
        "ECG-NN-PRIMARY": [],
        "PS+ECG-NN":      STRUCTURED_COVS,
    }

    # ── Load embeddings ───────────────────────────────────────────────────────
    print(f"\nLoading BCL embeddings from {args.embed_dir} …")
    emb_df, X_raw = load_embeddings(args.embed_dir, cohort)
    if len(emb_df) == 0:
        raise RuntimeError("No embeddings found — run embed_comet.py first.")
    print(f"Embeddings: {len(emb_df):,} / {len(cohort):,}  "
          + "  ".join(f"{k}={v:,}" for k, v in sorted(emb_df["arm"].value_counts().to_dict().items())))

    norms = np.linalg.norm(X_raw, axis=1)
    print(f"  Embedding norms: mean={norms.mean():.4f} std={norms.std():.4f}")

    # ── Denominator audit ─────────────────────────────────────────────────────
    print(f"\nBuilding denominator masks …")
    masks = build_masks(cohort, emb_df, STRUCTURED_COVS)
    audit_df = audit_table(cohort, masks, treated_arm=TREATED, control_arm=CONTROL)
    print(f"\n  Denominator audit (relative to full cohort n={len(cohort):,}):")
    print_audit(audit_df)
    audit_df.to_csv(out / "denominator_audit.csv", index=False)

    miss_df = missingness_audit(cohort, STRUCTURED_COVS, masks["echo_complete"])
    miss_df.to_csv(out / "missingness_audit.csv", index=False)
    print(f"\n  Per-covariate missingness within echo_complete (n={int(masks['echo_complete'].sum()):,}):")
    for _, r in miss_df.iterrows():
        print(f"    {r['covariate']:<22}  missing={int(r['n_missing']):>5}  ({r['pct_missing']:.1f}%)")

    # ── Active analysis population ────────────────────────────────────────────
    use_strict = args.denominator in ("strict", "both")

    if use_strict:
        strict_mask = masks["intersection_strict"]
        cohort_d = cohort[strict_mask].reset_index(drop=True)
        strict_pids = set(cohort_d["person_id"].astype(str))
        strict_emb_mask = emb_df["person_id"].astype(str).isin(strict_pids)
        emb_d = emb_df[strict_emb_mask].reset_index(drop=True)
        X_d   = X_raw[strict_emb_mask.values]
        n_d   = len(cohort_d)
        denom_label = f"strict D (n={n_d:,})"
        print(f"\n  Strict intersection D: {n_d:,} patients  "
              f"({TREATED}={(cohort_d['arm'] == TREATED).sum():,}  "
              f"{CONTROL}={(cohort_d['arm'] == CONTROL).sum():,})")
        print(f"  Embeddings in D: {len(emb_d):,}/{n_d:,}")
        if len(emb_d) != n_d:
            print(f"  WARNING: {n_d - len(emb_d):,} patients in D are missing .npy files")
    else:
        cohort_d    = cohort
        emb_d       = emb_df
        X_d         = X_raw
        denom_label = f"ecg_available (n={len(emb_df):,})"

    n_t = (emb_d["arm"] == TREATED).sum()
    n_c = (emb_d["arm"] == CONTROL).sum()

    if n_t == 0 or n_c == 0:
        print(f"\n  ERROR: one arm is empty in {denom_label} "
              f"({TREATED}={n_t:,}, {CONTROL}={n_c:,}) — cannot run comparator ladder.")
        print("  Likely cause: arm misclassification in the Stage 1 pool "
              "(check configs/<trial>.yaml arm keywords/formulation_filter).")
        sys.exit(1)

    k   = _check_pool(n_t, n_c, args.match_ratio)

    # ── Diagnostics: arm summary + event rates + index date ──────────────────
    if run_diag:
        print(f"\n{'='*60}")
        print(f"  Cohort diagnostics — {denom_label}")
        print(f"{'='*60}")
        arm_df = arm_summary(cohort_d, treated_arm=TREATED, control_arm=CONTROL)
        print_arm_summary(arm_df, label=denom_label)
        arm_df.to_csv(out / "arm_summary_D.csv", index=False)

        er_df = event_rate_by_arm(cohort_d, treated_arm=TREATED, control_arm=CONTROL,
                                   event_col=_EVENT_COL, duration_col=_TIME_COL)
        print_event_rates(er_df)

        check_immortal_time(cohort_d, treated_arm=TREATED, control_arm=CONTROL)\
            .to_csv(out / "immortal_time_check.csv", index=False)

        plot_index_date_distribution(cohort_d, out / "index_date_dist.png",
                                     treated_arm=TREATED, control_arm=CONTROL)

    results_summary: list[dict] = []   # 5 core methods → primary forest plot
    supplemental_rows: list[dict] = []  # all other methods → CSV only
    post_matched: dict[str, pd.DataFrame] = {}

    # ── 1:1 balanced cohort for Cox/IPW methods ───────────────────────────────
    cohort_1to1 = sample_1to1(cohort_d, TREATED, CONTROL, args.seed)
    n1_t = (cohort_1to1["arm"] == TREATED).sum()
    n1_c = (cohort_1to1["arm"] == CONTROL).sum()
    print(f"\n  1:1 balanced cohort for Cox/IPW: {len(cohort_1to1):,} "
          f"({TREATED}={n1_t:,}  {CONTROL}={n1_c:,})")
    denom_label_1to1 = f"1:1 sampled (n={len(cohort_1to1):,})"

    # ── 1. Unadjusted Cox ─────────────────────────────────────────────────────
    print(f"\n1. Unadjusted Cox ({denom_label_1to1})")
    r1 = cox_hr(cohort_1to1, treated_arm=TREATED)
    print_res(f"Unadjusted ({denom_label_1to1})", r1)
    results_summary.append({"label": "Unadjusted Cox", "denominator": denom_label_1to1, **r1})

    # ── 2. Adjusted Cox ───────────────────────────────────────────────────────
    print(f"\n2. Adjusted Cox (age, sex, race) — {denom_label_1to1}")
    r2 = cox_hr(cohort_1to1, covariates=ADJ_COVS, treated_arm=TREATED)
    if r2["n"] < len(cohort_1to1):
        print(f"  (complete case: {r2['n']:,}/{len(cohort_1to1):,} rows used)")
    print_res(f"Adjusted Cox n={r2['n']:,}", r2)
    results_summary.append({"label": "Adjusted Cox (age,sex,race)", "denominator": denom_label_1to1, **r2})


    # ── Pre-match balance (analysis population) ───────────────────────────────
    bal_pre = build_balance_table(emb_d, None, cols=SMD_COLS,
                                  treated_arm=TREATED, control_arm=CONTROL,
                                  label="pre_match")

    # ── 3. Structured PSM ────────────────────────────────────────────────────
    k_spsm = _check_pool((cohort_d["arm"] == TREATED).sum(),
                         (cohort_d["arm"] == CONTROL).sum(), args.match_ratio)
    print(f"\n3. Structured PSM — {len(STRUCTURED_COVS)} covariates (1:{k_spsm}) — {denom_label}")
    try:
        spsm = structured_psm(cohort_d, STRUCTURED_COVS, k=k_spsm,
                              caliper=args.structured_caliper,
                              treated_arm=TREATED, control_arm=CONTROL,
                              seed=args.seed)
        if not spsm.empty:
            r3 = cox_hr(spsm, treated_arm=TREATED, strata=["match_id"])
            print_res(f"Structured PSM 1:{k_spsm} n={len(spsm):,}", r3)
            results_summary.append({"label": "Structured PSM", "denominator": denom_label, **r3})
            post_matched["PSM"] = spsm
        else:
            print("  No matches — try --structured-caliper 0.5")
    except Exception as e:
        print(f"  Structured PSM failed: {e}")

    # ── 5. ECG NN PRIMARY ────────────────────────────────────────────────────
    print(f"\n5. ECG NN PRIMARY — cosine d≤{args.abs_threshold}, 1:{k} — {denom_label}")
    try:
        nn_primary, summ_primary = nn_match(emb_d, X_d, k=k, metric="cosine",
                                             threshold=args.abs_threshold,
                                             treated_arm=TREATED, control_arm=CONTROL,
                                             exact_cols=exact_match_cols)
        if not nn_primary.empty and len(nn_primary) >= 10:
            print(f"  Attrition: {summ_primary['n_treated_matched']:,}/{summ_primary['n_treated_attempted']:,} treated matched")
            r6 = cox_hr(nn_primary, treated_arm=TREATED, strata=["match_id"])
            print_res(f"ECG NN d≤{args.abs_threshold} PRIMARY n={len(nn_primary):,}", r6)
            results_summary.append({
                "label": f"ECG-NN (cosine ≤{args.abs_threshold})",
                "denominator": denom_label, **r6
            })
            if MATCHED_ADJ_COLS:
                try:
                    r6_adj = cox_hr(nn_primary, covariates=MATCHED_ADJ_COLS,
                                    treated_arm=TREATED, strata=["match_id"])
                    adj_label = f"ECG-NN PRIMARY (adj {','.join(MATCHED_ADJ_COLS)})"
                    print_res(adj_label, r6_adj)
                    # Print only; does NOT replace primary ECG-NN entry in results_summary
                except Exception as e:
                    print(f"  Adjusted matched Cox (PRIMARY) failed: {e}")
            post_matched["ECG-NN-PRIMARY"] = nn_primary
            nn_primary.to_parquet(out / "primary_match.parquet", index=False)
            print(f"  primary_match.parquet saved")
        else:
            print(f"  Too few matches at d≤{args.abs_threshold}")
    except Exception as e:
        print(f"  ECG NN PRIMARY failed: {e}")

    # ── 5. PS-caliper + ECG-NN ──────────────────────────────────────────────
    # Hard PS caliper on STRUCTURED_COVS → guarantees comorbidity balance.
    # Within caliper, nearest-neighbour by cosine → optimises ECG balance.
    print(f"\n5. PS-caliper + ECG-NN ({args.ps_caliper_sd} SD caliper, {len(STRUCTURED_COVS)} PS covs) — {denom_label}")
    print(f"  PS covariates: {STRUCTURED_COVS}")
    try:
        nn_mm, summ_mm = ps_ecg_match(
            emb_d, X_d,
            structured_cols=STRUCTURED_COVS,
            caliper_sd=args.ps_caliper_sd,
            treated_arm=TREATED, control_arm=CONTROL,
            seed=args.seed,
        )
        if not nn_mm.empty and len(nn_mm) >= 10:
            print(f"  Attrition: {summ_mm['n_treated_matched']:,}/{summ_mm['n_treated_attempted']:,} treated matched")
            r5b = cox_hr(nn_mm, treated_arm=TREATED, strata=["match_id"])
            print_res(f"PS+ECG-NN n={len(nn_mm):,}", r5b)
            results_summary.append({"label": "PS+ECG-NN", "denominator": denom_label, **r5b})
            if MATCHED_ADJ_COLS:
                try:
                    r5b_adj = cox_hr(nn_mm, covariates=MATCHED_ADJ_COLS,
                                     treated_arm=TREATED, strata=["match_id"])
                    print_res(f"PS+ECG-NN (adj {','.join(MATCHED_ADJ_COLS)})", r5b_adj)
                except Exception as e:
                    print(f"  Adjusted matched Cox (PS+ECG-NN) failed: {e}")
            post_matched["PS+ECG-NN"] = nn_mm
        else:
            print(f"  Too few matches — try --ps-caliper-sd 0.30")
    except Exception as e:
        print(f"  PS+ECG-NN failed: {e}")

    # ── KM plots + match-distance (per matched method) ────────────────────────
    if run_diag:
        print(f"\n{'='*60}")
        print(f"  Per-match diagnostics")
        print(f"{'='*60}")
        for label, mdf in post_matched.items():
            if mdf.empty or len(mdf) < 20:
                continue
            try:
                plot_km(mdf, out / f"km_{label.replace(' ', '_')}.png",
                        treated_arm=TREATED, control_arm=CONTROL,
                        title=f"KM — {label} ({denom_label})",
                        event_col=_EVENT_COL, duration_col=_TIME_COL)
            except Exception as e:
                print(f"  KM {label} failed: {e}")
            if label in ("ECG-NN-PRIMARY", "PS+ECG-NN"):
                try:
                    match_distance_summary(
                        mdf, out / f"match_distance_{label.replace(' ', '_').replace('+', 'plus')}.png",
                        title=f"Match distance — {label}",
                    )
                except Exception as e:
                    print(f"  Match distance {label} failed: {e}")

    # ── Balance tables ────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  Covariate Balance Summary")
    print(f"{'='*60}")
    balance_tables = write_balance_tables(
        emb_d, post_matched, output_dir=out,
        cols=SMD_COLS, treated_arm=TREATED, control_arm=CONTROL,
    )

    print("\n  Pre-match balance:")
    print_balance_table(bal_pre)

    # Full SMD_COLS balance + held-out split
    held_out_tables: dict[str, pd.DataFrame] = {}
    print(f"\n  Balance split (in-model vs held-out, threshold SMD<{0.10}):")
    print(f"  {'Method':<22} {'in-model':>14}  {'held-out':>14}")
    print(f"  {'-'*22}  {'-'*14}  {'-'*14}")
    for label, tbl in balance_tables.items():
        if "smd_post" not in tbl.columns:
            continue
        in_model = IN_MODEL_COVS.get(label, [])
        sp = summarize_split(tbl, in_model)
        in_s  = (f"{sp['n_in_model_balanced']}/{sp['n_in_model_total']}"
                 if sp['n_in_model_total'] > 0 else "(none)")
        ho_s  = f"{sp['n_held_out_balanced']}/{sp['n_held_out_total']}"
        print(f"  {label:<22}  {in_s:>14}  {ho_s:>14}  ← headline")

        # Build held-out-only table for output
        held_out_covs = [c for c in SMD_COLS if c not in in_model]
        if held_out_covs:
            ho_tbl = build_balance_table(
                emb_d, post_matched[label], cols=held_out_covs,
                treated_arm=TREATED, control_arm=CONTROL, label=label
            )
            held_out_tables[label] = ho_tbl

    # Write held-out CSVs
    if held_out_tables:
        from balance import build_balance_summary
        ho_summary = build_balance_summary(held_out_tables)
        ho_summary.to_csv(out / "balance_summary_held_out.csv", index=False)

    # Pre vs post SMD — comparison: PSM, ECG-NN-PRIMARY, PS+ECG-NN
    _bal_labels = [l for l in ["PSM", "ECG-NN-PRIMARY", "PS+ECG-NN"]
                   if l in balance_tables]
    for _bal_label in _bal_labels:
        tbl = balance_tables[_bal_label]
        if "smd_pre" in tbl.columns and "smd_post" in tbl.columns:
            print(f"\n  {_bal_label} pre vs post-match SMD (all covariates):")
            print(f"  {'Covariate':<24} {'SMD_pre':>8}  {'SMD_post':>8}  {'Delta':>8}")
            print(f"  {'-'*24}  {'-'*8}  {'-'*8}  {'-'*8}")
            t = tbl.set_index("covariate")
            _fmt = lambda v: f"{v:>8.3f}" if not pd.isna(v) else "       —"
            for cov in SMD_COLS:
                if cov not in t.index:
                    continue
                pre  = t.loc[cov, "smd_pre"]
                post = t.loc[cov, "smd_post"] if "smd_post" in t.columns else float("nan")
                if pd.isna(pre):
                    continue
                flag  = " !" if (not pd.isna(post) and post > 0.1) else ""
                delta = f"{post-pre:>+8.3f}" if not pd.isna(post) else "       —"
                print(f"  {cov:<24}  {_fmt(pre)}  {_fmt(post)}  {delta}{flag}")

    # ── Charlson CCI (partial) pre/post matching ─────────────────────────────
    print(f"\n  Charlson CCI (partial, max=5 — MI, HF, stroke, COPD, DM):")
    print(f"  {'Method':<26}  {'treated':>8}  {'control':>8}  {'SMD':>8}")
    print(f"  {'-'*26}  {'-'*8}  {'-'*8}  {'-'*8}")
    cci_pre_smd_val = cci_smd(emb_d, TREATED, CONTROL)
    t_cci_pre = compute_cci(emb_d[emb_d["arm"] == TREATED])
    c_cci_pre = compute_cci(emb_d[emb_d["arm"] == CONTROL])
    print(f"  {'Pre-match':<26}  {t_cci_pre.mean():>8.2f}  {c_cci_pre.mean():>8.2f}  {cci_pre_smd_val:>8.3f}")
    cci_post_smds: dict[str, float] = {}
    for _cci_lbl, _cci_key in [("PSM", "PSM"), ("ECG-NN", "ECG-NN-PRIMARY"), ("PS+ECG-NN", "PS+ECG-NN")]:
        pm_df = post_matched.get(_cci_key)
        if pm_df is None or pm_df.empty:
            cci_post_smds[_cci_lbl] = float("nan")
            continue
        s = cci_smd(pm_df, TREATED, CONTROL)
        cci_post_smds[_cci_lbl] = s
        t_c = compute_cci(pm_df[pm_df["arm"] == TREATED])
        c_c = compute_cci(pm_df[pm_df["arm"] == CONTROL])
        print(f"  {_cci_lbl:<26}  {t_c.mean():>8.2f}  {c_c.mean():>8.2f}  {s:>8.3f}")

    # ── Multi-method love plot (pre-match / PSM / NN / NN+Tabular) ───────────
    # Use pre-match SMD from bal_pre; post SMD from balance_tables per method.
    smd_pre_series = bal_pre.set_index("covariate")["smd_pre"].copy()

    method_smds_love: dict[str, pd.Series] = {}
    for _lv_lbl, _lv_key in [("PSM", "PSM"), ("ECG-NN", "ECG-NN-PRIMARY"), ("PS+ECG-NN", "PS+ECG-NN")]:
        if _lv_key in balance_tables and "smd_post" in balance_tables[_lv_key].columns:
            s = balance_tables[_lv_key].set_index("covariate")["smd_post"].copy()
            method_smds_love[_lv_lbl] = s

    if method_smds_love:
        plot_love_multimethod(
            smd_pre_series, method_smds_love,
            out / "love_plot_multimethod.png",
            title=f"{TRIAL} — Covariate Balance by Method",
        )
        print(f"\n  Multi-method love plot → love_plot_multimethod.png")

    # ── Single-method love plot (ECG-NN-PRIMARY held-out) ────────────────────
    best_label = "ECG-NN-PRIMARY" if "ECG-NN-PRIMARY" in held_out_tables else None
    if best_label and best_label in held_out_tables:
        ho_tbl = held_out_tables[best_label]
        if "smd_pre" in ho_tbl.columns and "smd_post" in ho_tbl.columns:
            pre_s  = ho_tbl.set_index("covariate")["smd_pre"]
            post_s = ho_tbl.set_index("covariate")["smd_post"]
            plot_love(pre_s, post_s, out / "love_plot_held_out.png",
                      title=f"Held-out Balance — {best_label}",
                      post_label=best_label)
    if best_label and best_label in balance_tables:
        tbl = balance_tables[best_label]
        if "smd_pre" in tbl.columns and "smd_post" in tbl.columns:
            plot_love(tbl.set_index("covariate")["smd_pre"],
                      tbl.set_index("covariate")["smd_post"],
                      out / "love_plot.png", post_label=best_label)

    # ── Results summary CSV ───────────────────────────────────────────────────
    all_results = results_summary + supplemental_rows
    pd.DataFrame(all_results).to_csv(out / "results_summary.csv", index=False)
    print(f"\n  results_summary.csv saved → {out}")

    # ── Primary forest plot ───────────────────────────────────────────────────
    primary_rows = [r for r in results_summary if not np.isnan(r.get("hr", float("nan")))]
    if primary_rows:
        _xlim = tuple(float(v) for v in args.forest_xlim.split(","))
        forest_plot(primary_rows, out / "forest.png",
                    match_ratio=k, trial_name=TRIAL, reference_hr=REF_HR,
                    treated_label=TREATED, control_label=CONTROL,
                    xlim=_xlim)

    print(f"\n{'='*70}")
    print(f"  Results → {out}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
