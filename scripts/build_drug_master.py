"""
scripts/build_drug_master.py

Build drug_master.parquet from raw EHR medication .txt files across cohorts.

Sources (three cohorts × three file types):
  *_Meds.txt                   → setting=home_meds        (outpatient prescriptions)
  *_Outpatient_Enc_Med_Admin   → setting=outpatient_admin (clinic-administered)
  *_Hosp_Enc_Med_Admin_*       → setting=inpatient        (hospital administration)

Output schema (compatible with cohort_utils.load_drug_master):
  MRN, drug_name, order_date, generic_name, pharm_class, route, frequency,
  dose, dose_unit, order_status, end_date, discontinue_date, setting, cohort

TTE pipeline usage:
  - Index event identification: filter setting IN ('home_meds', 'outpatient_admin')
  - Covariate extraction: all settings OK
  - Inpatient-only drugs: setting='inpatient', never used as index event

Usage (on cluster):
    python scripts/build_drug_master.py \\
        --t2dm-dir   /home/rbc58/mnt/t2dm-jdat-data \\
        --cmp-dir    /home/rbc58/mnt/cmp-jdat-data \\
        --impl-dir   /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \\
        --output     /mnt/raid0/rbc58/mm_vhd/drug/drug_master_v2.parquet

    # Skip inpatient (smaller, faster, TTE-only):
    python scripts/build_drug_master.py ... --no-inpatient

    # Dry run: print files + row counts, no output written:
    python scripts/build_drug_master.py ... --dry-run
"""

from __future__ import annotations

import argparse
import gc
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from tqdm import tqdm


# ── File specs per cohort ─────────────────────────────────────────────────────
# (label, filename, setting)
COHORT_SPECS: dict[str, list[tuple[str, str, str]]] = {
    "t2dm": [
        ("meds_list",        "2380791_CarDS_Outcomes_DM2_Meds.txt",                     "home_meds"),
        ("outpt_med_admin",  "2380791_CarDS_Outcomes_DM2_Outpatient_Enc_Med_Admin.txt", "outpatient_admin"),
        ("hosp_med_admin_1", "2380791_CarDS_Outcomes_DM2_Hosp_Enc_Med_Admin_1.txt",     "inpatient"),
        ("hosp_med_admin_2", "2380791_CarDS_Outcomes_DM2_Hosp_Enc_Med_Admin_2.txt",     "inpatient"),
    ],
    "cmp": [
        ("meds_list",        "2356781_CarDS_Aim_1_Meds.txt",                            "home_meds"),
        ("outpt_med_admin",  "2356781_CarDS_Aim_1_Outpatient_Enc_Med_Admin.txt",        "outpatient_admin"),
        ("hosp_med_admin_1", "2356781_CarDS_Aim_1_Hosp_Enc_Med_Admin_1.txt",            "inpatient"),
        ("hosp_med_admin_2", "2356781_CarDS_Aim_1_Hosp_Enc_Med_Admin_2.txt",            "inpatient"),
    ],
    "implementation": [
        ("meds_list",        "CarDS_2435227_Meds.txt",                                  "home_meds"),
        ("outpt_med_admin",  "CarDS_2435227_Outpatient_Enc_Med_Admin.txt",              "outpatient_admin"),
        ("hosp_med_admin_1", "CarDS_2435227_Hosp_Enc_Med_Admin_1.txt",                 "inpatient"),
        ("hosp_med_admin_2", "CarDS_2435227_Hosp_Enc_Med_Admin_2.txt",                 "inpatient"),
    ],
}

# Column name candidates (tried in order, first match wins)
MRN_CANDS       = ["PAT_MRN_ID", "pat_mrn_id", "MRN", "mrn"]
DRUG_CANDS      = ["MEDICATION_NAME", "medication_name", "DRUG_NAME", "drug_name",
                   "MED_NAME", "med_name"]
DATE_CANDS      = ["ORDER_INST", "order_inst", "ORDER_DATE", "order_date",
                   "CONTACT_DATE", "contact_date", "TAKEN_TIME", "taken_time",
                   "START_DATE", "start_date", "MED_ORDER_DATE", "med_order_date"]
GENERIC_CANDS   = ["SIMPLE_GENERIC", "simple_generic", "GENERIC_NAME", "generic_name"]
PHARM_CANDS     = ["PHARM_CLASS", "pharm_class"]
ROUTE_CANDS     = ["ROUTE_SIMPLE", "route_simple", "ROUTE", "route"]
FREQ_CANDS      = ["FREQ_NAME", "freq_name", "FREQUENCY", "frequency", "FREQ", "freq"]
DOSE_CANDS      = ["HV_DISCRETE_DOSE", "hv_discrete_dose", "DOSE", "dose",
                   "MIN_DISCRETE_DOSE", "min_discrete_dose"]
DOSE_UNIT_CANDS = ["HV_DOSE_UNIT", "hv_dose_unit", "DOSE_UNIT", "dose_unit"]
STATUS_CANDS    = ["ORDER_STATUS", "order_status", "MED_ORDER_STATUS", "med_order_status"]
END_CANDS       = ["END_DATE", "end_date", "DISCON_TIME", "discon_time",
                   "DISCONTINUE_TIME", "discontinue_time", "STOP_DATE", "stop_date"]
DISC_CANDS      = ["DISCONTINUE_REASON", "discontinue_reason", "DISCON_REASON",
                   "discon_reason"]


def _first_match(cols_upper: dict[str, str], candidates: list[str]) -> str | None:
    """cols_upper: {UPPER_NAME: original_name}"""
    for c in candidates:
        if c.upper() in cols_upper:
            return cols_upper[c.upper()]
    return None


def _detect_sep(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
    if "\t" in header:
        return "\t"
    if "|" in header:
        return "|"
    return ","


def _read_med_file(
    path: Path,
    setting: str,
    cohort: str,
    chunksize: int = 200_000,
) -> pd.DataFrame | None:

    if not path.exists():
        print(f"    MISSING: {path.name}")
        return None

    sep = _detect_sep(path)
    print(f"    Reading {path.name}  sep={'TAB' if sep==chr(9) else sep!r}")

    chunks_out = []
    total_in = 0
    try:
        reader = pd.read_csv(
            path, sep=sep, chunksize=chunksize,
            low_memory=False, encoding="utf-8", errors="replace",
        )
        for chunk in reader:
            total_in += len(chunk)
            chunk.columns = [c.strip() for c in chunk.columns]
            cu = {c.upper(): c for c in chunk.columns}

            mrn_col    = _first_match(cu, MRN_CANDS)
            drug_col   = _first_match(cu, DRUG_CANDS)
            date_col   = _first_match(cu, DATE_CANDS)

            if mrn_col is None or drug_col is None:
                # Can't use this file — log and bail
                print(f"    WARNING: {path.name} missing MRN or drug col — skipping "
                      f"(cols: {list(chunk.columns[:10])}...)")
                return None

            out = pd.DataFrame()
            out["MRN"]       = chunk[mrn_col].astype(str).str.strip()
            out["MRN"]       = out["MRN"].str.replace(r"^[A-Za-z]+", "", regex=True)
            out["drug_name"] = chunk[drug_col].astype(str).str.strip()

            if date_col:
                out["order_date"] = pd.to_datetime(chunk[date_col], errors="coerce")
            else:
                out["order_date"] = pd.NaT

            # Optional columns — map if present
            for out_col, cands in [
                ("generic_name",     GENERIC_CANDS),
                ("pharm_class",      PHARM_CANDS),
                ("route",            ROUTE_CANDS),
                ("frequency",        FREQ_CANDS),
                ("dose",             DOSE_CANDS),
                ("dose_unit",        DOSE_UNIT_CANDS),
                ("order_status",     STATUS_CANDS),
                ("end_date",         END_CANDS),
                ("discontinue_date", DISC_CANDS),
            ]:
                src = _first_match(cu, cands)
                out[out_col] = chunk[src] if src else pd.NA

            out["setting"] = setting
            out["cohort"]  = cohort

            # Drop rows with no drug name
            out = out[out["drug_name"].notna() & (out["drug_name"] != "") & (out["drug_name"] != "nan")]
            # Drop rows with no MRN
            out = out[out["MRN"].notna() & (out["MRN"] != "") & (out["MRN"] != "nan")]

            chunks_out.append(out)
            gc.collect()

    except Exception as e:
        print(f"    ERROR reading {path.name}: {e}")
        return None

    if not chunks_out:
        return None

    result = pd.concat(chunks_out, ignore_index=True)
    print(f"    → {total_in:,} rows in, {len(result):,} rows kept")
    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build drug_master.parquet from raw EHR med txt files"
    )
    p.add_argument("--output", required=True,
                   help="Output path for drug_master.parquet")
    p.add_argument("--t2dm-dir",  default=os.getenv("T2DM_S3", ""),
                   help="T2DM cohort base dir (default: $T2DM_S3)")
    p.add_argument("--cmp-dir",   default=os.getenv("CMP_S3", ""),
                   help="CMP cohort base dir (default: $CMP_S3)")
    p.add_argument("--impl-dir",  default="",
                   help="IMPLEMENTATION data dir (full path to Data-YYYY-MM-DD folder)")
    p.add_argument("--no-inpatient", action="store_true",
                   help="Skip *_Hosp_Enc_Med_Admin files (faster, TTE-only)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print file existence + sizes, do not write output")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Build drug_master → {args.output}")
    print(f"Started: {datetime.now().isoformat()}")

    dirs = {
        "t2dm":           Path(args.t2dm_dir)  if args.t2dm_dir  else None,
        "cmp":            Path(args.cmp_dir)   if args.cmp_dir   else None,
        "implementation": Path(args.impl_dir)  if args.impl_dir  else None,
    }

    if args.dry_run:
        print("\n[DRY RUN] File inventory:")
        for cohort, base in dirs.items():
            if base is None:
                print(f"  {cohort}: no path provided")
                continue
            for _, fname, setting in COHORT_SPECS[cohort]:
                if args.no_inpatient and setting == "inpatient":
                    continue
                fp = base / fname
                exists = fp.exists()
                size   = f"{fp.stat().st_size / 1e6:.0f} MB" if exists else "MISSING"
                print(f"  {cohort:<18} {setting:<18} {fname}  [{size}]")
        return

    all_parts: list[pd.DataFrame] = []

    for cohort, base in dirs.items():
        if base is None:
            print(f"\n[{cohort}] skipped — no path provided")
            continue
        print(f"\n{'─'*60}")
        print(f"  Cohort: {cohort}  |  {base}")
        for _, fname, setting in COHORT_SPECS[cohort]:
            if args.no_inpatient and setting == "inpatient":
                continue
            fp = base / fname
            part = _read_med_file(fp, setting, cohort)
            if part is not None:
                all_parts.append(part)
            gc.collect()

    if not all_parts:
        print("ERROR: no data loaded — check paths")
        return

    dm = pd.concat(all_parts, ignore_index=True)
    print(f"\nTotal rows before dedup: {len(dm):,}")

    dedup_cols = ["MRN", "drug_name", "order_date"]
    before = len(dm)
    dm = dm.drop_duplicates(subset=dedup_cols)
    print(f"After dedup: {len(dm):,}  (removed {before - len(dm):,})")

    dm = dm.dropna(subset=["MRN", "order_date"])
    print(f"After drop null MRN/date: {len(dm):,}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  DRUG MASTER SUMMARY")
    print(f"  Rows          : {len(dm):,}")
    print(f"  Unique MRNs   : {dm['MRN'].nunique():,}")
    print(f"  Unique drugs  : {dm['drug_name'].nunique():,}")
    print(f"  Date range    : {dm['order_date'].min().date()} → {dm['order_date'].max().date()}")
    print(f"\n  By setting:")
    for s, n in dm["setting"].value_counts().items():
        pct = 100 * n / len(dm)
        print(f"    {s:<22}  {n:>12,}  ({pct:.1f}%)")
    print(f"\n  By cohort:")
    for c, n in dm["cohort"].value_counts().items():
        pct = 100 * n / len(dm)
        print(f"    {c:<22}  {n:>12,}  ({pct:.1f}%)")
    print(f"{'='*65}")

    # ── Save ──────────────────────────────────────────────────────────────────
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    dm.to_parquet(out, index=False, compression="snappy")
    print(f"\nSaved → {out}  ({out.stat().st_size / 1e6:.0f} MB)")
    print(f"Done: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
