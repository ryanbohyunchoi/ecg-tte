"""
scripts/explore_med_sources.py

Explore raw EHR medication .txt files across T2DM, CMP, and IMPLEMENTATION cohorts.
Reads headers + aggregate stats ONLY — no patient-level data printed.

Three file types per cohort:
  *_Meds.txt                  — active med list (home/outpatient prescriptions)
  *_Outpatient_Enc_Med_Admin  — clinic-administered drugs
  *_Hosp_Enc_Med_Admin_*      — inpatient administration

Output:
  - Column names per file type
  - Row counts
  - Value distributions for categorical med columns (drug name top-N, route, order_type, etc.)
  - Date range
  - Whether separators are tab/pipe/comma

Usage (on cluster):
    python scripts/explore_med_sources.py \\
        --t2dm-dir   /home/rbc58/mnt/t2dm-jdat-data \\
        --cmp-dir    /home/rbc58/mnt/cmp-jdat-data \\
        --impl-dir   /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \\
        --n-rows     50000
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


# ── File name patterns per cohort ─────────────────────────────────────────────
# Each entry: (label, glob_pattern, setting)
COHORT_FILE_PATTERNS = {
    "t2dm": [
        ("meds_list",        "2380791_CarDS_Outcomes_DM2_Meds.txt",                  "home_meds"),
        ("outpt_med_admin",  "2380791_CarDS_Outcomes_DM2_Outpatient_Enc_Med_Admin.txt", "outpatient_admin"),
        ("hosp_med_admin_1", "2380791_CarDS_Outcomes_DM2_Hosp_Enc_Med_Admin_1.txt",  "inpatient"),
        ("hosp_med_admin_2", "2380791_CarDS_Outcomes_DM2_Hosp_Enc_Med_Admin_2.txt",  "inpatient"),
    ],
    "cmp": [
        ("meds_list",        "2356781_CarDS_Aim_1_Meds.txt",                "home_meds"),
        ("outpt_med_admin",  "2356781_CarDS_Aim_1_Outpatient_Enc_Med_Admin.txt", "outpatient_admin"),
        ("hosp_med_admin_1", "2356781_CarDS_Aim_1_Hosp_Enc_Med_Admin_1.txt", "inpatient"),
        ("hosp_med_admin_2", "2356781_CarDS_Aim_1_Hosp_Enc_Med_Admin_2.txt", "inpatient"),
    ],
    "implementation": [
        ("meds_list",        "CarDS_2435227_Meds.txt",                         "home_meds"),
        ("outpt_med_admin",  "CarDS_2435227_Outpatient_Enc_Med_Admin.txt",      "outpatient_admin"),
        ("hosp_med_admin_1", "CarDS_2435227_Hosp_Enc_Med_Admin_1.txt",          "inpatient"),
        ("hosp_med_admin_2", "CarDS_2435227_Hosp_Enc_Med_Admin_2.txt",          "inpatient"),
    ],
}

# Columns we care about — try many naming conventions
MRN_CANDIDATES    = ["PAT_MRN_ID", "pat_mrn_id", "MRN", "mrn"]
DRUG_CANDIDATES   = ["MEDICATION_NAME", "medication_name", "DRUG_NAME", "drug_name",
                     "GENERIC_NAME", "generic_name", "MED_NAME", "med_name", "NAME"]
DATE_CANDIDATES   = ["ORDER_INST", "order_inst", "ORDER_DATE", "order_date",
                     "CONTACT_DATE", "contact_date", "START_DATE", "start_date",
                     "TAKEN_TIME", "taken_time", "MED_ORDER_DATE"]
CAT_COLS          = ["ORDER_STATUS", "MEDICATION_NAME", "SIMPLE_GENERIC",
                     "PHARM_CLASS", "THERA_CLASS", "ROUTE", "ROUTE_SIMPLE",
                     "ORDER_CLASS", "FREQUENCY", "FREQ_NAME", "DOSE_UNIT",
                     "DISPENSE_AS_WRITTEN", "MEDICATION_ID"]


def _detect_sep(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
    if "\t" in header:
        return "\t"
    if "|" in header:
        return "|"
    return ","


def _first_match(cols: list[str], candidates: list[str]) -> str | None:
    col_set = set(c.upper() for c in cols)
    for c in candidates:
        if c.upper() in col_set:
            # return actual col name (original case)
            return next(x for x in cols if x.upper() == c.upper())
    return None


def _header(text: str) -> None:
    print(f"\n{'='*65}")
    print(f"  {text}")
    print(f"{'='*65}")


def explore_file(path: Path, label: str, setting: str, n_rows: int) -> dict:
    """
    Read first n_rows of a med txt file.
    Print schema + aggregate stats. Return summary dict.
    """
    if not path.exists():
        print(f"  MISSING: {path.name}")
        return {"path": str(path), "exists": False}

    sep = _detect_sep(path)
    print(f"\n  [{label}]  setting={setting}  sep={'TAB' if sep==chr(9) else sep!r}")
    print(f"  File: {path.name}")

    try:
        df = pd.read_csv(path, sep=sep, nrows=n_rows, low_memory=False,
                         encoding="latin-1")
    except Exception as e:
        print(f"  ERROR reading: {e}")
        return {"path": str(path), "exists": True, "error": str(e)}

    cols = list(df.columns)
    print(f"  Rows loaded : {len(df):,}  (first {n_rows:,} of full file)")
    print(f"  Columns ({len(cols)}): {cols}")

    # Identify key columns
    mrn_col  = _first_match(cols, MRN_CANDIDATES)
    drug_col = _first_match(cols, DRUG_CANDIDATES)
    date_col = _first_match(cols, DATE_CANDIDATES)

    print(f"  MRN col     : {mrn_col}")
    print(f"  Drug col    : {drug_col}")
    print(f"  Date col    : {date_col}")

    if mrn_col:
        print(f"  Unique MRNs : {df[mrn_col].nunique():,}")

    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        valid = dates.dropna()
        if len(valid):
            print(f"  Date range  : {valid.min().date()} → {valid.max().date()}")
        else:
            print(f"  Date range  : unparseable — sample vals: {df[date_col].dropna().head(3).tolist()}")

    # Value distributions for categorical columns
    present_cats = [c for c in CAT_COLS if c in [x.upper() for x in cols]]
    for cat_upper in present_cats:
        actual = next(c for c in cols if c.upper() == cat_upper)
        vc = df[actual].dropna().astype(str).str.strip()
        vc = vc[vc != ""].value_counts()
        if vc.empty:
            print(f"\n  {actual}: ALL BLANK")
        else:
            top_n = 20 if actual.upper() in ("MEDICATION_NAME", "SIMPLE_GENERIC",
                                              "GENERIC_NAME", "DRUG_NAME") else 12
            print(f"\n  {actual} (top {top_n}, {vc.sum():,} non-blank):")
            for val, n in vc.head(top_n).items():
                pct = 100 * n / vc.sum()
                print(f"    {str(val):<50}  {n:>8,}  ({pct:.1f}%)")

    return {
        "path": str(path),
        "exists": True,
        "label": label,
        "setting": setting,
        "n_rows": len(df),
        "cols": cols,
        "mrn_col": mrn_col,
        "drug_col": drug_col,
        "date_col": date_col,
        "sep": sep,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Explore raw EHR med files — schema + aggregate stats only"
    )
    p.add_argument("--t2dm-dir",   default=os.getenv("T2DM_S3", ""),
                   help="T2DM cohort base dir (default: $T2DM_S3)")
    p.add_argument("--cmp-dir",    default=os.getenv("CMP_S3", ""),
                   help="CMP cohort base dir (default: $CMP_S3)")
    p.add_argument("--impl-dir",   default="",
                   help="IMPLEMENTATION data dir (full path to Data-YYYY-MM-DD folder)")
    p.add_argument("--n-rows",     type=int, default=50_000,
                   help="Rows to read per file (default 50k — schema + distributions only)")
    p.add_argument("--file-types", default="meds_list,outpt_med_admin,hosp_med_admin_1",
                   help="Comma-separated file type labels to explore "
                        "(default: meds_list,outpt_med_admin,hosp_med_admin_1). "
                        "Use 'all' to include hosp_med_admin_2 as well.")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    dirs = {
        "t2dm":           Path(args.t2dm_dir) if args.t2dm_dir else None,
        "cmp":            Path(args.cmp_dir)  if args.cmp_dir  else None,
        "implementation": Path(args.impl_dir) if args.impl_dir  else None,
    }

    want_types = (
        None if args.file_types.strip().lower() == "all"
        else set(args.file_types.split(","))
    )

    all_summaries: list[dict] = []

    for cohort, base_dir in dirs.items():
        if base_dir is None:
            print(f"\n[{cohort}] skipped — no path provided")
            continue
        _header(f"Cohort: {cohort}  |  {base_dir}")
        patterns = COHORT_FILE_PATTERNS.get(cohort, [])
        for label, fname, setting in patterns:
            if want_types and label not in want_types:
                continue
            fp = base_dir / fname
            s = explore_file(fp, label, setting, args.n_rows)
            s["cohort"] = cohort
            all_summaries.append(s)

    # ── Cross-file schema comparison ──────────────────────────────────────────
    _header("Schema comparison across file types")

    by_label: dict[str, list[dict]] = {}
    for s in all_summaries:
        if not s.get("exists") or s.get("error"):
            continue
        by_label.setdefault(s["label"], []).append(s)

    for label, items in by_label.items():
        print(f"\n  [{label}]")
        for s in items:
            print(f"    {s['cohort']:<18}  mrn={s.get('mrn_col'):<20}  "
                  f"drug={s.get('drug_col'):<25}  date={s.get('date_col')}")

    # ── Recommendations ───────────────────────────────────────────────────────
    _header("Recommendations for drug_master build")
    print("""
  DECISION TREE for each file type:

  1. *_Meds.txt (home_meds)
     ├─ Columns: likely MEDICATION_NAME, ORDER_INST (or ORDER_DATE), ORDER_STATUS
     ├─ Contains: active outpatient prescriptions + historical med list
     ├─ Use for: TTE index event (first dispense of arm drug)
     └─ Watch for: meds from hospitalisation that get added to "home med list" on discharge
        → mitigate with ORDER_STATUS != "Discontinued" or require ≥2 records

  2. *_Outpatient_Enc_Med_Admin.txt (outpatient_admin)
     ├─ Columns: likely MEDICATION_NAME, TAKEN_TIME (or CONTACT_DATE)
     ├─ Contains: drugs administered at outpatient clinic visits (injections, infusions)
     ├─ Use for: PCSK9i, GLP-1 injectables, zoledronic acid — drugs given in clinic
     └─ NOT suitable as sole index for oral daily drugs (won't capture pharmacy fills)

  3. *_Hosp_Enc_Med_Admin_*.txt (inpatient)
     ├─ Columns: likely MEDICATION_NAME, TAKEN_TIME
     ├─ Contains: every dose given during inpatient stay (IV saline, heparin, etc.)
     ├─ Use for: COVARIATES ONLY (e.g., "received IV heparin during index hospitalisation")
     └─ NEVER use as TTE index event — immortal time bias guaranteed

  STRATEGY:
    Build unified drug_master from *_Meds.txt (primary) + *_Outpatient_Enc_Med_Admin.txt
    Tag each row with setting=home_meds|outpatient_admin|inpatient
    Stage 1 then filters on setting when assigning index dates (default: home_meds only)
""")


if __name__ == "__main__":
    main()
