"""
trialemulation/methods/comet/denominators.py

Denominator mask utilities for the COMET comparator ladder.
Builds named boolean masks over the cohort, runs a denominator audit,
and exposes the strict intersection D = (ECG-available) ∩ (rich-covariates complete).
"""
from __future__ import annotations

import pandas as pd


def build_masks(
    cohort: pd.DataFrame,
    emb_df: pd.DataFrame,
    sparse_covs: list[str],
    rich_covs: list[str],
) -> dict[str, pd.Series]:
    """
    Return named boolean masks (indexed on cohort.index) for each denominator subgroup.

    Keys
    ----
    full                — all rows (always True)
    ecg_available       — has a valid embedding on disk (matched by person_id to emb_df)
    echo_complete       — ef_at_index is non-null
    psm_sparse_eligible — non-null on every covariate in sparse_covs
    psm_rich_eligible   — non-null on every covariate in rich_covs
    intersection_strict — ecg_available & psm_rich_eligible  [headline denominator D]
    """
    idx = cohort.index
    full = pd.Series(True, index=idx)

    ecg_pids = set(emb_df["person_id"].astype(str)) if not emb_df.empty else set()
    ecg_available = cohort["person_id"].astype(str).isin(ecg_pids)

    if "ef_at_index" in cohort.columns:
        echo_complete = cohort["ef_at_index"].notna()
    else:
        echo_complete = pd.Series(False, index=idx)

    avail_sp = [c for c in sparse_covs if c in cohort.columns]
    psm_sparse_eligible = (
        cohort[avail_sp].notna().all(axis=1) if avail_sp else pd.Series(False, index=idx)
    )

    avail_ri = [c for c in rich_covs if c in cohort.columns]
    psm_rich_eligible = (
        cohort[avail_ri].notna().all(axis=1) if avail_ri else pd.Series(False, index=idx)
    )

    intersection_strict = ecg_available & psm_rich_eligible

    return {
        "full":                 full,
        "ecg_available":        ecg_available,
        "echo_complete":        echo_complete,
        "psm_sparse_eligible":  psm_sparse_eligible,
        "psm_rich_eligible":    psm_rich_eligible,
        "intersection_strict":  intersection_strict,
    }


def audit_table(
    cohort: pd.DataFrame,
    masks: dict[str, pd.Series],
    treated_arm: str = "carvedilol",
    control_arm: str = "metoprolol",
) -> pd.DataFrame:
    """
    One row per named subset.
    Columns: name, n_total, n_treated, n_control, n_events, share_of_full
    """
    n_full = int(masks["full"].sum())
    rows = []
    for name, mask in masks.items():
        sub = cohort[mask]
        rows.append({
            "name":          name,
            "n_total":       len(sub),
            "n_treated":     int((sub["arm"] == treated_arm).sum()),
            "n_control":     int((sub["arm"] == control_arm).sum()),
            "n_events":      int(sub["event_death"].sum()) if "event_death" in sub.columns else None,
            "share_of_full": round(len(sub) / n_full, 4) if n_full > 0 else None,
        })
    return pd.DataFrame(rows)


def missingness_audit(
    cohort: pd.DataFrame,
    rich_covs: list[str],
    base_mask: pd.Series,
) -> pd.DataFrame:
    """
    Per-covariate missingness within the echo_complete subset.
    Returns columns: covariate, n_present, n_missing, pct_missing (sorted descending).
    """
    sub = cohort[base_mask]
    rows = []
    for c in rich_covs:
        if c not in sub.columns:
            rows.append({"covariate": c, "n_present": 0,
                         "n_missing": len(sub), "pct_missing": 100.0})
            continue
        n_present = int(sub[c].notna().sum())
        n_missing  = len(sub) - n_present
        rows.append({"covariate": c, "n_present": n_present,
                     "n_missing": n_missing,
                     "pct_missing": round(100 * n_missing / max(len(sub), 1), 2)})
    return pd.DataFrame(rows).sort_values("pct_missing", ascending=False)


def print_audit(df: pd.DataFrame) -> None:
    hdr = (f"  {'Subset':<25} {'n_total':>8}  {'treated':>8}  "
           f"{'control':>8}  {'events':>7}  {'%full':>6}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for _, r in df.iterrows():
        ev = f"{int(r['n_events']):>7}" if r["n_events"] is not None else "      —"
        sh = f"{r['share_of_full'] * 100:>5.1f}%" if r["share_of_full"] is not None else "     —"
        print(f"  {r['name']:<25} {int(r['n_total']):>8,}  "
              f"{int(r['n_treated']):>8,}  {int(r['n_control']):>8,}  {ev}  {sh}")
