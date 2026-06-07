"""
trialemulation/methods/comet/diagnostics.py

Diagnostic suite for the COMET comparator ladder.
All functions emit aggregate-only outputs — no patient-level data is printed or saved.

Key functions
-------------
arm_summary          — per-arm baseline characteristics + SMD in D
event_rate_by_arm    — events per 1000 person-years per arm
plot_km              — Kaplan-Meier curves with log-rank p-value
plot_index_date_distribution  — histogram of index_date per arm
check_immortal_time  — distribution of selected_ecg_days_from_index per arm
match_distance_summary — per-pair cosine distance distribution for NN matching
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_WARN_SMD = 0.20


# ── helpers ───────────────────────────────────────────────────────────────────

def _smd(a: np.ndarray, b: np.ndarray) -> float:
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled = np.sqrt((a.var() + b.var()) / 2 + 1e-8)
    return float(abs(a.mean() - b.mean()) / pooled)


def _is_binary(vals: np.ndarray) -> bool:
    cc = vals[~np.isnan(vals)]
    return set(np.unique(cc)) <= {0.0, 1.0}


# ── Arm summary ───────────────────────────────────────────────────────────────

def arm_summary(
    cohort: pd.DataFrame,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    covariates: list[str] | None = None,
) -> pd.DataFrame:
    """
    Per-arm means / proportions + SMD for every requested covariate.
    Default covariate list covers all SMD_COLS plus follow-up and ECG timing.
    Returns a DataFrame with columns: covariate, treated, control, smd, flag.
    """
    if covariates is None:
        covariates = [
            "age_at_index", "ef_at_index", "sex_binary", "race_black",
            "hr_at_index", "QRS_Duration", "PR_Interval",
            "afib", "htn", "dm", "cad_mi", "copd", "hyperlipidemia", "stroke",
            "loop_diuretic", "acei_arb", "aldosterone_antag", "prior_hf_code_1yr",
            "time_to_death", "event_death",
            "selected_ecg_days_from_index",
        ]
    a = cohort[cohort["arm"] == treated_arm]
    b = cohort[cohort["arm"] == control_arm]
    rows = []
    for col in covariates:
        if col not in cohort.columns:
            continue
        av = a[col].values.astype(float)
        bv = b[col].values.astype(float)
        binary = _is_binary(np.concatenate([av, bv]))
        am = float(np.nanmean(av))
        bm = float(np.nanmean(bv))
        smd = _smd(av, bv)
        rows.append({
            "covariate": col, "is_binary": binary,
            treated_arm: am, control_arm: bm,
            "smd": smd,
            "flag": " !" if (not np.isnan(smd) and smd > _WARN_SMD) else "",
        })
    return pd.DataFrame(rows)


def print_arm_summary(df: pd.DataFrame, label: str = "D") -> None:
    print(f"\n  Arm summary — {label}:")
    hdr = (f"  {'Covariate':<26} {df.columns[2]:>13} "
           f"{df.columns[3]:>13} {'SMD':>7}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for _, r in df.iterrows():
        smd_s = f"{r['smd']:.3f}" if not np.isnan(r["smd"]) else "  —  "
        col_name = df.columns[2]
        ctrl_name = df.columns[3]
        v_t = f"{r[col_name]:.3f}"
        v_c = f"{r[ctrl_name]:.3f}"
        print(f"  {r['covariate']:<26}  {v_t:>13}  {v_c:>13}  {smd_s:>7}{r['flag']}")


# ── Event rates ───────────────────────────────────────────────────────────────

def event_rate_by_arm(
    cohort: pd.DataFrame,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
) -> pd.DataFrame:
    """
    Events per 1000 person-years per arm.
    Requires columns: arm, event_death, time_to_death (days).
    """
    rows = []
    for arm in [treated_arm, control_arm]:
        sub = cohort[cohort["arm"] == arm]
        n_events = int(sub["event_death"].sum())
        py = sub["time_to_death"].sum() / 365.25 / 1000.0  # in kPY
        rate = n_events / py if py > 0 else float("nan")
        event_pct = 100 * n_events / len(sub) if len(sub) > 0 else float("nan")
        rows.append({
            "arm": arm, "n": len(sub),
            "events": n_events, "event_pct": round(event_pct, 1),
            "person_years": round(py * 1000, 1),
            "events_per_1k_PY": round(rate, 2),
        })
    return pd.DataFrame(rows)


def print_event_rates(df: pd.DataFrame) -> None:
    print(f"\n  Event rates:")
    for _, r in df.iterrows():
        print(f"  {r['arm']:<14}  n={r['n']:,}  events={r['events']:,} "
              f"({r['event_pct']:.1f}%)  {r['events_per_1k_PY']:.2f}/1000 PY")


# ── Kaplan-Meier ──────────────────────────────────────────────────────────────

def plot_km(
    matched: pd.DataFrame,
    output_path: Path,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    title: str = "",
) -> None:
    """
    Kaplan-Meier survival curves with 95% CI and log-rank p-value.
    Requires time_to_death and event_death columns.
    """
    try:
        from lifelines import KaplanMeierFitter
        from lifelines.statistics import logrank_test
    except ImportError:
        print("  [KM] lifelines not available — skipping")
        return

    T_t = matched.loc[matched["arm"] == treated_arm, "time_to_death"]
    E_t = matched.loc[matched["arm"] == treated_arm, "event_death"]
    T_c = matched.loc[matched["arm"] == control_arm, "time_to_death"]
    E_c = matched.loc[matched["arm"] == control_arm, "event_death"]

    if len(T_t) < 10 or len(T_c) < 10:
        return

    lr = logrank_test(T_t, T_c, event_observed_A=E_t, event_observed_B=E_c)
    fig, ax = plt.subplots(figsize=(7, 4))
    for T, E, label, color in [
        (T_t, E_t, treated_arm, "steelblue"),
        (T_c, E_c, control_arm, "tomato"),
    ]:
        kmf = KaplanMeierFitter()
        kmf.fit(T, E, label=f"{label} (n={len(T):,})")
        kmf.plot_survival_function(ax=ax, ci_show=False, color=color)

    ax.set_title(title or "Kaplan-Meier", fontsize=11)
    ax.set_xlabel("Days from index date", fontsize=10)
    ax.set_ylabel("Survival probability", fontsize=10)
    ax.legend(fontsize=9, frameon=False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  KM plot → {output_path.name}  (log-rank p={lr.p_value:.4f})")


# ── Index-date distribution ───────────────────────────────────────────────────

def plot_index_date_distribution(
    cohort: pd.DataFrame,
    output_path: Path,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
) -> None:
    """Histogram of index_date per arm to detect calendar confounding."""
    if "index_date" not in cohort.columns:
        print("  [index_date_dist] index_date not in cohort — skipping")
        return

    fig, ax = plt.subplots(figsize=(8, 3.5))
    for arm, color in [(treated_arm, "steelblue"), (control_arm, "tomato")]:
        dates = pd.to_datetime(cohort.loc[cohort["arm"] == arm, "index_date"])
        years = dates.dt.year + dates.dt.month / 12
        ax.hist(years, bins=40, alpha=0.5, label=arm, color=color, density=True)
    ax.set_xlabel("Index date (year)", fontsize=10)
    ax.set_ylabel("Density", fontsize=10)
    ax.set_title("Index date distribution by arm", fontsize=11)
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  Index-date distribution → {output_path.name}")


# ── Immortal-time check ───────────────────────────────────────────────────────

def check_immortal_time(
    cohort: pd.DataFrame,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
) -> pd.DataFrame:
    """
    Distribution of selected_ecg_days_from_index per arm.
    Negative = ECG before index (correct for mode='before').
    Any positive values or systematic arm-level drift = potential immortal-time bias.
    """
    col = "selected_ecg_days_from_index"
    if col not in cohort.columns:
        print(f"  [immortal_time] {col} not available — skipping")
        return pd.DataFrame()

    rows = []
    print(f"\n  Immortal-time check ({col}):")
    for arm in [treated_arm, control_arm]:
        vals = cohort.loc[cohort["arm"] == arm, col].dropna()
        if len(vals) == 0:
            continue
        n_pos = int((vals > 0).sum())
        pct_pos = 100 * n_pos / len(vals)
        rows.append({
            "arm": arm, "n": len(vals),
            "mean_days": round(vals.mean(), 1),
            "median_days": round(vals.median(), 1),
            "min_days": int(vals.min()),
            "max_days": int(vals.max()),
            "n_post_index": n_pos,
            "pct_post_index": round(pct_pos, 1),
        })
        flag = " ← WARNING: ECG after index!" if n_pos > 0 else " ✓"
        print(f"  {arm:<14}  mean={vals.mean():.1f}d  median={vals.median():.1f}d  "
              f"[{int(vals.min())}, {int(vals.max())}]  "
              f"post-index: {n_pos:,} ({pct_pos:.1f}%){flag}")
    return pd.DataFrame(rows)


# ── Match-distance distribution ───────────────────────────────────────────────

def match_distance_summary(
    matched: pd.DataFrame,
    output_path: Path,
    title: str = "",
) -> dict:
    """
    Plot histogram of per-pair cosine match distances.
    Requires a 'match_distance' column in the matched DataFrame (set by nn_match).
    Control rows carry the distance; treated rows have NaN.
    """
    if "match_distance" not in matched.columns:
        print("  [match_dist] match_distance column not found — skipping")
        return {}

    dists = matched["match_distance"].dropna().values
    if len(dists) == 0:
        return {}

    stats = {
        "n_pairs": len(dists),
        "p25": float(np.percentile(dists, 25)),
        "p50": float(np.percentile(dists, 50)),
        "p75": float(np.percentile(dists, 75)),
        "p90": float(np.percentile(dists, 90)),
        "max": float(dists.max()),
    }
    print(f"  Match distance — p25={stats['p25']:.4f}  p50={stats['p50']:.4f}  "
          f"p75={stats['p75']:.4f}  p90={stats['p90']:.4f}  max={stats['max']:.4f}")

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.hist(dists, bins=50, color="steelblue", edgecolor="none", alpha=0.8)
    ax.axvline(stats["p50"], color="red", ls="--", lw=1.2, label=f"median={stats['p50']:.3f}")
    ax.set_xlabel("Cosine distance (treated → matched control)", fontsize=10)
    ax.set_ylabel("Pairs", fontsize=10)
    ax.set_title(title or "Match distance distribution", fontsize=11)
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  Match-distance plot → {output_path.name}")
    return stats
