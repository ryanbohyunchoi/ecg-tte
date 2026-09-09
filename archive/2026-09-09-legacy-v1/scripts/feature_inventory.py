"""
feature_inventory.py

Inventory of every structured feature that feeds propensity-score matching and
covariate balance, so you can see — before running stage4 — what is included,
what is missing, and how much.

For each canonical feature it reports:
  - membership: which sets use it (RICH_PSM, ADJ_COX, SMD balance)
  - type: binary vs continuous (data-inferred when a cohort is given)
  - handling: imputed by MICE? has a missing-indicator?
  - presence: is the column actually in the cohort?  (absent = will silently
    read as NaN / drop out of balance — the actionable signal)
  - missingness: n_present / pct_missing / n_unique, overall and per arm

Canonical lists are imported live from stage4_analyze / balance / imputation, so
this stays in sync with the pipeline.

Usage
-----
Catalog only (no data, runs anywhere):
    python scripts/feature_inventory.py

Against a real cohort (on the cluster):
    python scripts/feature_inventory.py \
        --cohort runs/paradigm/comet_cohort.parquet \
        --treated-arm sacubitril_valsartan --control-arm enalapril \
        --out runs/paradigm/feature_inventory.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import stage4_analyze as S
import balance as B
import imputation as I

# ── Canonical sets (live) ─────────────────────────────────────────────────────
RICH = list(S._RICH_PSM_CANDIDATES)
ADJ = list(S._ADJ_COX_CANDIDATES)
SMD = list(B.SMD_COLS)
CONTINUOUS_MISSING = set(I.CONTINUOUS_MISSING)
INDICATOR = set(I.MISSING_INDICATOR_COVS)

# Coarse grouping for readable summaries (prefix / membership based).
def _group(name: str) -> str:
    if name in ("age_at_index", "sex_binary", "race_black"):
        return "demographics"
    if name.startswith("ef_at_index"):
        return "echo"
    if name in ("hr_at_index", "RR_Interval", "PR_Interval", "QRS_Duration",
                "QTc", "QT_Interval", "QRS_Axis", "P_Axis", "T_Axis"):
        return "ecg_interval"
    if name.startswith("lab_"):
        return "lab"
    if name.startswith("vital_"):
        return "vital"
    if name.startswith("z_"):
        return "zcode"
    if name.startswith("n_refills"):
        return "adherence"
    if name == "index_year":
        return "calendar"
    if any(name.startswith(p) or name == p for p in (
        "loop_diuretic", "acei_arb", "aldosterone_antag", "digoxin", "statin",
        "nitrate", "beta_blocker", "warfarin", "doac", "antiplatelet",
        "amiodarone", "bb_90d", "sglt2i")):
        return "medication"
    if name.startswith(("hfref", "hf_icd", "prior_hf")):
        return "hf_severity"
    return "comorbidity"


def build_inventory(cohort: pd.DataFrame | None,
                    treated_arm: str, control_arm: str) -> pd.DataFrame:
    feats = sorted(set(RICH) | set(ADJ) | set(SMD))
    cols = set(cohort.columns) if cohort is not None else None
    if cohort is not None:
        t_mask = cohort["arm"] == treated_arm
        c_mask = cohort["arm"] == control_arm

    rows = []
    for f in feats:
        present = (f in cols) if cols is not None else None
        rec = {
            "feature":     f,
            "group":       _group(f),
            "in_rich_psm": f in RICH,
            "in_adj_cox":  f in ADJ,
            "in_smd":      f in SMD,
            "imputed_mice": f in CONTINUOUS_MISSING,
            "missing_indicator": f in INDICATOR,
            "present":     present,
        }
        if cohort is not None and present:
            col = pd.to_numeric(cohort[f], errors="coerce")
            n = len(col)
            n_present = int(col.notna().sum())
            uniq = col.dropna().unique()
            binary = set(np.unique(uniq)) <= {0.0, 1.0} if len(uniq) else True
            rec.update({
                "type":        "binary" if binary else "continuous",
                "n_present":   n_present,
                "pct_missing": round(100 * (n - n_present) / n, 1) if n else None,
                "pct_missing_treated": round(100 * col[t_mask].isna().mean(), 1),
                "pct_missing_control": round(100 * col[c_mask].isna().mean(), 1),
                "n_unique":    int(len(uniq)),
            })
        else:
            # No data: infer type from CONTINUOUS_MISSING membership only.
            rec.update({
                "type": "continuous" if f in CONTINUOUS_MISSING else "binary?",
                "n_present": None, "pct_missing": None,
                "pct_missing_treated": None, "pct_missing_control": None,
                "n_unique": None,
            })
        rows.append(rec)
    return pd.DataFrame(rows)


def print_report(inv: pd.DataFrame, has_data: bool) -> None:
    print(f"\n{'='*78}")
    print("STRUCTURED FEATURE INVENTORY  (PSM + covariate balance)")
    print(f"{'='*78}")
    print(f"Canonical set sizes:  RICH_PSM={len(RICH)}  ADJ_COX={len(ADJ)}  "
          f"SMD_balance={len(SMD)}  |  distinct union={len(inv)}")
    print(f"MICE-imputed continuous covariates defined: {len(CONTINUOUS_MISSING)}   "
          f"missing-indicators: {sorted(INDICATOR)}")

    # Membership overlaps (naming drift is the usual culprit here).
    only_smd = inv[(inv.in_smd) & (~inv.in_rich_psm)]["feature"].tolist()
    only_rich = inv[(inv.in_rich_psm) & (~inv.in_smd)]["feature"].tolist()
    print(f"\nIn SMD-balance but NOT in RICH-PSM ({len(only_smd)}):")
    print("   " + ", ".join(only_smd) if only_smd else "   —")
    print(f"In RICH-PSM but NOT in SMD-balance ({len(only_rich)}) — matched-on but not balance-reported:")
    print("   " + ", ".join(only_rich) if only_rich else "   —")

    if has_data:
        absent = inv[inv.present == False]["feature"].tolist()  # noqa: E712
        print(f"\n⚠  Canonical features ABSENT from cohort ({len(absent)}) "
              f"— read as NaN / dropped from balance:")
        for f in absent:
            tags = [t for t, on in [("RICH", f in RICH), ("ADJ", f in ADJ),
                                    ("SMD", f in SMD)] if on]
            print(f"     {f:<32} [{','.join(tags)}]")

    # Per-group summary.
    print(f"\n{'Group':<14} {'#feat':>5} {'present':>7} {'binary':>6} {'contin':>6} "
          f"{'med %miss':>10}")
    print("-" * 60)
    for g, sub in inv.groupby("group"):
        present = int((sub.present == True).sum()) if has_data else len(sub)  # noqa: E712
        nb = int((sub.type == "binary").sum())
        nc = int((sub.type == "continuous").sum())
        med = sub["pct_missing"].dropna()
        med_s = f"{med.median():.1f}" if has_data and len(med) else "—"
        print(f"{g:<14} {len(sub):>5} {present:>7} {nb:>6} {nc:>6} {med_s:>10}")

    if has_data:
        print(f"\nContinuous features by missingness (worst first):")
        cont = inv[(inv.type == "continuous") & (inv.present == True)]  # noqa: E712
        cont = cont.sort_values("pct_missing", ascending=False)
        print(f"  {'feature':<24} {'%miss':>6} {'%miss_T':>8} {'%miss_C':>8} "
              f"{'n_present':>9} {'imputed':>8}")
        for _, r in cont.iterrows():
            print(f"  {r['feature']:<24} {r['pct_missing']:>6} "
                  f"{r['pct_missing_treated']:>8} {r['pct_missing_control']:>8} "
                  f"{int(r['n_present']):>9} {'yes' if r['imputed_mice'] else 'no':>8}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inventory of PSM/balance structured features.")
    p.add_argument("--cohort", default="", help="cohort parquet (omit for catalog-only).")
    p.add_argument("--treated-arm", default="carvedilol")
    p.add_argument("--control-arm", default="metoprolol")
    p.add_argument("--out", default="", help="optional CSV output path.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cohort = None
    if args.cohort:
        cohort = pd.read_parquet(args.cohort)
        if "sex_binary" not in cohort.columns and "sex" in cohort.columns:
            cohort["sex_binary"] = (cohort["sex"] == "F").astype(float)
    inv = build_inventory(cohort, args.treated_arm, args.control_arm)
    print_report(inv, has_data=cohort is not None)
    if args.out:
        inv.to_csv(args.out, index=False)
        print(f"\nInventory → {args.out}")


if __name__ == "__main__":
    main()
