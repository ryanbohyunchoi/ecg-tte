"""
trialemulation/methods/comet/balance.py

Universal covariate balance table builder for trial emulation.

Fixes vs. legacy analyze.py:
  - SMD_COLS defined ONCE here; imported by every comparator (no drift).
  - build_balance_table() always writes both pre and post SMD on the same row.
  - n_nonmissing per cell is reported so EF missingness is never silent.
  - smd_pre_imputed / smd_post_imputed (mean-imputed) alongside complete-case SMD.
  - Reusable across all 7 trials; cells get NaN where covariates don't apply.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

# ── Balance covariate list ────────────────────────────────────────────────────
# Superset of everything the rich PSM matches on (so the balance table / Love plot
# report every matched covariate) PLUS a few reported-but-not-matched extras
# (extended ECG axes; trial-specific exclusion-proxy flags). Column names use the
# post-stage3 convention (medication _90d suffix STRIPPED — matches the cohort).
# Kept in sync with stage4_analyze._RICH_PSM_CANDIDATES; build_balance_table emits
# a NaN row for any covariate absent from a given trial's cohort, so trial-specific
# entries are harmless when unused.
SMD_COLS: list[str] = [
    # Demographics (3)
    "age_at_index", "sex_binary", "race_black",
    # Echo (1)
    "ef_at_index",
    # HF severity (6): 3 HFrEF ICD proxies + 2 HF-ICD windows + prior HF code
    "hfref_icd_5y", "hfref_icd_24m", "hfref_icd_subcoded_i502_24m",
    "hf_icd_1y", "hf_icd_2y", "prior_hf_code_1yr",
    # Comorbidities — core (7)
    "afib", "htn", "dm", "cad_mi", "copd", "hyperlipidemia", "stroke",
    # Comorbidities — multi-window / additional (21)
    "afib_1y", "afib_5y", "dm_1y", "cad_1y", "cad_5y", "stroke_1y",
    "ckd_3", "anemia_2y", "pvd_5y", "osa_5y", "hypothyroid_5y",
    "depression_2y", "ventricular_arrh_2y", "cardiac_device_5y",
    "aki_1y", "atrial_flutter_2y", "hyponatremia_1y", "hyperkalemia_1y",
    "valvular_2y", "obesity_5y", "iron_deficiency_2y",
    # Comorbidities — trial-specific exclusion proxies (reported, not matched) (8)
    "lvh_5y", "valvular_disease_5y", "recent_mi_acs_60d", "recent_revasc_60d",
    "av_block_2_3_24m", "esrd_5y", "hepatic_failure_5y", "asthma_5y",
    # Baseline medications — 90d lookback, stage3-stripped names (11)
    "loop_diuretic", "acei_arb", "aldosterone_antag", "digoxin", "statin",
    "nitrate", "beta_blocker", "warfarin", "doac", "antiplatelet", "amiodarone",
    # GDMT polypharmacy (stage4-computed) (2)
    "bb_90d", "sglt2i_90d",
    # ECG — core intervals (3)
    "hr_at_index", "QRS_Duration", "PR_Interval",
    # ECG — extended axes (5; present when ecg_metadata has these columns)
    "QTc", "QT_Interval", "QRS_Axis", "P_Axis", "T_Axis",
    # Labs & vitals (7; present when stage1 run with --measurement-dir)
    "lab_egfr", "lab_creatinine", "lab_chol_total", "lab_hdl", "lab_hba1c",
    "vital_sbp", "vital_bmi",
    # Adherence (2) + calendar (1)
    "n_refills_assigned_90d", "n_refills_assigned_180d", "index_year",
]
assert len(SMD_COLS) == len(set(SMD_COLS)), \
    f"SMD_COLS has duplicates: {[c for c in SMD_COLS if SMD_COLS.count(c) > 1]}"
assert len(SMD_COLS) == 77, f"SMD_COLS length changed: {len(SMD_COLS)}"

BALANCE_TARGET_SMD = 0.10
BALANCE_WARN_SMD   = 0.20
BALANCE_VR_LO      = 0.50
BALANCE_VR_HI      = 2.00
BALANCE_KS_MAX     = 0.10


# ── Core statistics ───────────────────────────────────────────────────────────

def _smd_stats(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float, float]:
    """(mean_a, mean_b, pooled_sd, smd) for complete-case arrays."""
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan"), float("nan"), float("nan")
    ma, mb = a.mean(), b.mean()
    pooled_sd = np.sqrt((a.var() + b.var()) / 2 + 1e-8)
    return ma, mb, pooled_sd, abs(ma - mb) / pooled_sd


def _is_binary(a: np.ndarray, b: np.ndarray) -> bool:
    uniq = set(np.unique(np.concatenate([a, b])))
    return uniq <= {0.0, 1.0}


def _balance_for_col(
    a_all: np.ndarray,     # treated, including NaN
    b_all: np.ndarray,     # control, including NaN
) -> dict:
    """Compute all balance metrics for one covariate (treated vs control)."""
    a_cc = a_all[~np.isnan(a_all)]
    b_cc = b_all[~np.isnan(b_all)]

    result: dict = {
        "n_treated":         len(a_all),
        "n_control":         len(b_all),
        "n_missing_treated": int(np.isnan(a_all).sum()),
        "n_missing_control": int(np.isnan(b_all).sum()),
    }

    # Complete-case
    ma, mb, _, smd = _smd_stats(a_cc, b_cc)
    result.update({
        "mean_treated": ma, "mean_control": mb,
        "sd_treated":   float(a_cc.std()) if len(a_cc) >= 2 else float("nan"),
        "sd_control":   float(b_cc.std()) if len(b_cc) >= 2 else float("nan"),
        "smd":          smd,
    })

    # Mean-imputed (report separately for transparency on EF missingness)
    a_imp = a_all.copy(); a_imp[np.isnan(a_imp)] = float(np.nanmean(a_all)) if np.any(~np.isnan(a_all)) else 0
    b_imp = b_all.copy(); b_imp[np.isnan(b_imp)] = float(np.nanmean(b_all)) if np.any(~np.isnan(b_all)) else 0
    _, _, _, smd_imp = _smd_stats(a_imp, b_imp)
    result["smd_imputed"] = smd_imp

    # VR and KS (continuous only)
    binary = _is_binary(a_cc, b_cc) if len(a_cc) >= 2 and len(b_cc) >= 2 else True
    if binary or len(a_cc) < 2 or len(b_cc) < 2:
        result["vr"] = float("nan")
        result["ks"] = float("nan")
    else:
        result["vr"] = float(a_cc.var() / (b_cc.var() + 1e-8))
        result["ks"] = float(ks_2samp(a_cc, b_cc).statistic)

    result["is_binary"] = binary
    return result


# ── Main balance-table builder ────────────────────────────────────────────────

def build_balance_table(
    df_pre:  pd.DataFrame,
    df_post: Optional[pd.DataFrame],
    cols:    list[str] = SMD_COLS,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    label:   str = "",
) -> pd.DataFrame:
    """
    Build a row-per-covariate balance table with pre and post columns.

    df_pre:  full cohort (or embedded subset) before matching.
    df_post: matched cohort (may be None for unadjusted analyses).

    Columns in output:
      covariate, is_binary,
      n_treated_pre, n_control_pre, n_missing_treated_pre, n_missing_control_pre,
      mean_treated_pre, mean_control_pre, sd_treated_pre, sd_control_pre,
      smd_pre, smd_pre_imputed, vr_pre, ks_pre,
      (same _post columns if df_post provided),
      pct_bias_reduction, balanced_post
    """
    rows = []
    a_pre_full = df_pre[df_pre["arm"] == treated_arm]
    b_pre_full = df_pre[df_pre["arm"] == control_arm]

    for col in cols:
        row: dict = {"covariate": col}

        if col not in df_pre.columns:
            row.update({k: float("nan") for k in [
                "smd_pre", "smd_post", "pct_bias_reduction", "balanced_post"
            ]})
            rows.append(row)
            continue

        a_pre = a_pre_full[col].values.astype(float)
        b_pre = b_pre_full[col].values.astype(float)
        pre_stats = _balance_for_col(a_pre, b_pre)
        for k, v in pre_stats.items():
            row[f"{k}_pre"] = v

        if df_post is not None and col in df_post.columns:
            a_post = df_post[df_post["arm"] == treated_arm][col].values.astype(float)
            b_post = df_post[df_post["arm"] == control_arm][col].values.astype(float)
            post_stats = _balance_for_col(a_post, b_post)
            for k, v in post_stats.items():
                row[f"{k}_post"] = v

            smd_pre  = pre_stats["smd"]
            smd_post = post_stats["smd"]
            if not (np.isnan(smd_pre) or np.isnan(smd_post)) and smd_pre > 0:
                row["pct_bias_reduction"] = 100 * (smd_pre - smd_post) / smd_pre
            else:
                row["pct_bias_reduction"] = float("nan")
            row["balanced_post"] = (not np.isnan(smd_post)) and (smd_post < BALANCE_TARGET_SMD)
        else:
            row["pct_bias_reduction"] = float("nan")
            row["balanced_post"] = False

        rows.append(row)

    tbl = pd.DataFrame(rows)
    if label:
        tbl.insert(0, "comparator", label)
    return tbl


def pooled_balance_table(
    pre_frames: list[pd.DataFrame],
    post_frames: Optional[list[pd.DataFrame]],
    cc_pre: pd.DataFrame,
    cc_post: Optional[pd.DataFrame] = None,
    cols: list[str] = SMD_COLS,
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
    label: str = "",
) -> pd.DataFrame:
    """
    Balance table averaged across m imputed datasets (MI-pooled SMD diagnostics).

    Builds build_balance_table() per imputation, then averages the numeric
    metrics (smd_pre/smd_post/vr/ks/pct_bias_reduction) over the m tables. In an
    imputed frame there is no NaN, so each per-imputation SMD is the full-data
    SMD; the mean over m is the standard MI balance diagnostic.

    Complete-case SMDs (cc_pre / cc_post) are merged as smd_pre_cc / smd_post_cc
    sensitivity columns. With a single imputation this collapses to the ordinary
    build_balance_table output plus the _cc columns.
    """
    if len(pre_frames) == 1 and (post_frames is None or len(post_frames) == 1):
        base = build_balance_table(
            pre_frames[0],
            post_frames[0] if post_frames else None,
            cols=cols, treated_arm=treated_arm, control_arm=control_arm, label=label,
        )
    else:
        per_imp = []
        for i, pre in enumerate(pre_frames):
            post = post_frames[i] if post_frames and i < len(post_frames) else None
            per_imp.append(build_balance_table(
                pre, post, cols=cols,
                treated_arm=treated_arm, control_arm=control_arm,
            ))
        stacked = pd.concat(per_imp, ignore_index=True)
        num_cols = stacked.select_dtypes(include=[np.number]).columns.tolist()
        base = (stacked.groupby("covariate", sort=False)[num_cols]
                .mean().reset_index())
        # Preserve covariate order from cols.
        base["covariate"] = pd.Categorical(base["covariate"], categories=cols, ordered=True)
        base = base.sort_values("covariate").reset_index(drop=True)
        base["covariate"] = base["covariate"].astype(str)
        if label:
            base.insert(0, "comparator", label)

    # Merge complete-case SMD sensitivity columns.
    cc = build_balance_table(cc_pre, cc_post, cols=cols,
                             treated_arm=treated_arm, control_arm=control_arm)
    cc = cc.set_index("covariate")
    base["smd_pre_cc"] = base["covariate"].map(cc["smd_pre"]) if "smd_pre" in cc else float("nan")
    if "smd_post" in cc.columns:
        base["smd_post_cc"] = base["covariate"].map(cc["smd_post"])
    return base


def build_balance_summary(comparator_tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Concatenate per-comparator balance tables into a long-format summary CSV."""
    frames = []
    for label, tbl in comparator_tables.items():
        t = tbl.copy()
        if "comparator" not in t.columns:
            t.insert(0, "comparator", label)
        frames.append(t)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ── Printing ──────────────────────────────────────────────────────────────────

def print_balance_table(tbl: pd.DataFrame, indent: str = "    ") -> None:
    """Pretty-print a balance table (pre/post SMD, VR, KS)."""
    header = f"{'Covariate':<22} {'SMD_pre':>8} {'SMD_post':>9} {'VR_pre':>7} {'KS_pre':>7}"
    print(f"{indent}{header}")
    print(f"{indent}{'-'*22}  {'-'*8}  {'-'*8}  {'-'*7}  {'-'*7}")
    for _, r in tbl.iterrows():
        smd_pre  = r.get("smd_pre",  float("nan"))
        smd_post = r.get("smd_post", float("nan"))
        vr_pre   = r.get("vr_pre",   float("nan"))
        ks_pre   = r.get("ks_pre",   float("nan"))
        flag = ""
        if not np.isnan(smd_pre) and smd_pre > BALANCE_WARN_SMD:
            flag += " !"
        if not np.isnan(vr_pre) and (vr_pre < BALANCE_VR_LO or vr_pre > BALANCE_VR_HI):
            flag += " !"
        fmt = lambda v: f"{v:.3f}" if not np.isnan(v) else "  — "
        print(
            f"{indent}{r['covariate']:<22}  {fmt(smd_pre):>8}  {fmt(smd_post):>8}  "
            f"{fmt(vr_pre):>7}  {fmt(ks_pre):>7}{flag}"
        )


# ── I/O ───────────────────────────────────────────────────────────────────────

def write_balance_tables(
    pre:          pd.DataFrame,
    post_matched: dict[str, pd.DataFrame],
    output_dir:   Path,
    cols:         list[str] = SMD_COLS,
    treated_arm:  str = "carvedilol",
    control_arm:  str = "metoprolol",
) -> dict[str, pd.DataFrame]:
    """
    Build and write balance_table_{comparator}.csv for each comparator.
    Also writes balance_summary.csv (long format, pivotable).
    Returns dict of label → table.
    """
    tables = {}
    for label, df_post in post_matched.items():
        tbl = build_balance_table(
            pre, df_post, cols=cols,
            treated_arm=treated_arm, control_arm=control_arm, label=label
        )
        safe_label = label.replace(" ", "_").replace(":", "").replace("/", "_")
        out = output_dir / f"balance_table_{safe_label}.csv"
        tbl.to_csv(out, index=False)
        tables[label] = tbl

    summary = build_balance_summary(tables)
    summary.to_csv(output_dir / "balance_summary.csv", index=False)
    return tables


# ── Held-out balance split ────────────────────────────────────────────────────

def summarize_split(
    tbl: pd.DataFrame,
    in_model_covs: list[str],
) -> dict:
    """
    Split a balance table into in-model vs. held-out covariates and return
    balanced counts for each group at BALANCE_TARGET_SMD.

    In-model: covariates the matching method directly optimized.
    Held-out: covariates the method never saw — the fair comparison metric.

    Returns dict with keys:
      n_in_model_total, n_in_model_balanced,
      n_held_out_total, n_held_out_balanced
    """
    if "smd_post" not in tbl.columns or "covariate" not in tbl.columns:
        return {"n_in_model_total": 0, "n_in_model_balanced": 0,
                "n_held_out_total": 0, "n_held_out_balanced": 0}

    def _count(mask: pd.Series) -> tuple[int, int]:
        sub = tbl[mask]
        total = len(sub)
        balanced = int(
            (sub["smd_post"].notna() & (sub["smd_post"] < BALANCE_TARGET_SMD)).sum()
        )
        return total, balanced

    in_mask  = tbl["covariate"].isin(in_model_covs)
    n_in_t,  n_in_b  = _count(in_mask)
    n_ho_t,  n_ho_b  = _count(~in_mask)
    return {
        "n_in_model_total":    n_in_t,
        "n_in_model_balanced": n_in_b,
        "n_held_out_total":    n_ho_t,
        "n_held_out_balanced": n_ho_b,
    }


# ── Charlson Comorbidity Index (partial from available columns) ───────────────

CCI_COMPONENTS: dict[str, int] = {
    "cad_mi":            1,   # myocardial infarction
    "prior_hf_code_1yr": 1,   # congestive heart failure
    "stroke":            1,   # cerebrovascular disease
    "copd":              1,   # chronic pulmonary disease
    "dm":                1,   # diabetes mellitus (uncomplicated)
}

def compute_cci(df: pd.DataFrame) -> pd.Series:
    """Partial Charlson score (0–5) from available binary flags."""
    cci = pd.Series(0.0, index=df.index)
    for col, weight in CCI_COMPONENTS.items():
        if col in df.columns:
            cci += df[col].fillna(0.0) * weight
    return cci


def cci_smd(df: pd.DataFrame, treated_arm: str, control_arm: str) -> float:
    """SMD of partial CCI score between arms (uses same pooled-SD formula as SMD_COLS)."""
    t = compute_cci(df[df["arm"] == treated_arm]).values
    c = compute_cci(df[df["arm"] == control_arm]).values
    _, _, _, smd = _smd_stats(t, c)
    return smd


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_love(
    smd_pre:   pd.Series,
    smd_post:  pd.Series,
    output_path: Path,
    title: str = "Covariate Balance — Love Plot",
    post_label: str = "Post-match",
) -> None:
    cols = [c for c in smd_pre.index if c in smd_post.index]
    pre_v  = [smd_pre.get(c,  float("nan")) for c in cols]
    post_v = [smd_post.get(c, float("nan")) for c in cols]
    valid  = [(c, p, q) for c, p, q in zip(cols, pre_v, post_v)
              if not (np.isnan(p) and np.isnan(q))]
    if not valid:
        return
    labels, pre_v, post_v = zip(*valid)

    fig, ax = plt.subplots(figsize=(7, 1.2 + 0.45 * len(labels)))
    y = list(range(len(labels)))
    ax.scatter(pre_v,  y, marker="o", s=55, color="tomato",    label="Pre-match",  zorder=3)
    ax.scatter(post_v, y, marker="D", s=45, color="steelblue", label=post_label,   zorder=3)
    for i, (p, q) in enumerate(zip(pre_v, post_v)):
        if not (np.isnan(p) or np.isnan(q)):
            ax.plot([p, q], [i, i], color="gray", linewidth=0.8, zorder=2)
    ax.axvline(BALANCE_TARGET_SMD, color="green",  ls="--", lw=1.0, alpha=0.7,
               label=f"SMD={BALANCE_TARGET_SMD}")
    ax.axvline(BALANCE_WARN_SMD,   color="orange", ls="--", lw=1.0, alpha=0.7,
               label=f"SMD={BALANCE_WARN_SMD}")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Standardised Mean Difference", fontsize=10)
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=8, loc="lower right")
    ax.set_xlim(left=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_love_multimethod(
    smd_pre: pd.Series,
    method_smds: dict[str, pd.Series],
    output_path: Path,
    title: str = "Covariate Balance",
) -> None:
    """
    Grouped horizontal bar chart: one group per covariate, bars ordered
    Pre-match → PSM → ECG-NN → PS+ECG-NN (left-to-right in legend,
    top-to-bottom within each covariate group).
    """
    all_covs = [c for c in smd_pre.index if not np.isnan(smd_pre.get(c, float("nan")))]
    if not all_covs:
        return

    series_list   = [smd_pre] + list(method_smds.values())
    series_labels = ["Pre-match"] + list(method_smds.keys())
    n_series = len(series_list)
    colors   = ["#888888", "#2166ac", "#d6604d", "#762a83"]

    bar_h   = 0.15
    offsets = [(i - (n_series - 1) / 2) * bar_h for i in range(n_series)]
    n_covs  = len(all_covs)

    fig, ax = plt.subplots(figsize=(9, max(6, n_covs * 0.45)))

    import matplotlib.patches as mpatches
    legend_handles = []
    for si, (label, series, color) in enumerate(
        zip(series_labels, series_list, colors[:n_series])
    ):
        vals = [series.get(c, float("nan")) for c in all_covs]
        for j, v in enumerate(vals):
            if np.isnan(v):
                continue
            ax.barh(
                j + offsets[si], max(v, 0.005),
                height=bar_h * 0.88,
                color=color, alpha=0.85,
            )
        legend_handles.append(mpatches.Patch(color=color, alpha=0.85, label=label))

    ax.axvline(BALANCE_TARGET_SMD, color="black", ls="--", lw=1.0, alpha=0.45)
    legend_handles.append(mpatches.Patch(color="black", alpha=0.45, label=f"SMD = {BALANCE_TARGET_SMD}"))
    ax.set_yticks(list(range(n_covs)))
    ax.set_yticklabels(all_covs, fontsize=13)
    ax.set_xlabel("Standardised Mean Difference", fontsize=14)
    ax.set_title(title, fontsize=15)
    ax.legend(handles=legend_handles, fontsize=12, loc="lower right")
    ax.set_xlim(left=0)
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
