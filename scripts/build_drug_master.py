"""
scripts/build_drug_master.py

Build drug_master.parquet from raw EHR medication .txt files across cohorts.

Sources (three cohorts x three file types):
  *_Meds.txt                 -- setting=home_meds        (real outpatient prescriptions)
  *_Outpatient_Enc_Med_Admin -- setting=outpatient_admin (procedure/clinic-admin drugs)
  *_Hosp_Enc_Med_Admin_*     -- setting=inpatient        (hospital administration)

File type semantics (confirmed by data exploration 2026-06):
  home_meds:
    Real CV prescriptions (metoprolol, carvedilol, lisinopril, furosemide, warfarin...)
    ORDER_CLASS="Historical Med" (~26-58%) = patient-reported at intake; still valid evidence
    ORDER_CLASS="Normal"/"Print" = prescriptions written at clinic visits
    USE for TTE index event identification (first prescription of arm drug)

  outpatient_admin:
    Procedure/clinic drugs: contrast agents, antiemetics, sedation (60-81% FREQUENCY=ONCE)
    NOT outpatient prescriptions despite the file name
    Include in master (useful for covariates: received IV iron, IVIG, etc.)
    EXCLUDE from TTE index event identification

  inpatient:
    Hospital meds: saline, propofol, heparin flush, opioids
    Include for covariates only; NEVER use as TTE index event

Date column strategy:
  home_meds:        ORDER_INST = when prescription was written (correct)
  outpatient_admin: TAKEN_TIME = when drug was actually administered (ORDER_INST = order time)
  inpatient:        TAKEN_TIME = actual administration time

Output schema (compatible with cohort_utils.load_drug_master):
  MRN, drug_name, order_date, generic_name, pharm_class, route, frequency,
  dose, dose_unit, order_status, order_class, end_date, discontinue_date,
  discontinue_reason, setting, cohort

Usage (on cluster):
    python scripts/build_drug_master.py \\
        --t2dm-dir   /home/rbc58/mnt/t2dm-jdat-data \\
        --cmp-dir    /home/rbc58/mnt/cmp-jdat-data \\
        --impl-dir   /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \\
        --output     /mnt/raid0/rbc58/mm_vhd/drug/drug_master_v2.parquet

    # Home meds only (smallest, fastest, sufficient for most TTE trials):
    python scripts/build_drug_master.py ... --home-meds-only

    # Skip inpatient (medium size):
    python scripts/build_drug_master.py ... --no-inpatient

    # Dry run -- print file existence + sizes, no output written:
    python scripts/build_drug_master.py ... --dry-run
"""

from __future__ import annotations

import argparse
import gc
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


# ── File specs per cohort ─────────────────────────────────────────────────────
# (label, filename, setting, use_taken_time)
# use_taken_time=True: prefer TAKEN_TIME over ORDER_INST as order_date
COHORT_SPECS: dict[str, list[tuple[str, str, str, bool]]] = {
    "t2dm": [
        ("meds_list",        "2380791_CarDS_Outcomes_DM2_Meds.txt",                     "home_meds",        False),
        ("outpt_med_admin",  "2380791_CarDS_Outcomes_DM2_Outpatient_Enc_Med_Admin.txt", "outpatient_admin", True),
        ("hosp_med_admin_1", "2380791_CarDS_Outcomes_DM2_Hosp_Enc_Med_Admin_1.txt",     "inpatient",        True),
        ("hosp_med_admin_2", "2380791_CarDS_Outcomes_DM2_Hosp_Enc_Med_Admin_2.txt",     "inpatient",        True),
    ],
    "cmp": [
        ("meds_list",        "2356781_CarDS_Aim_1_Meds.txt",                            "home_meds",        False),
        ("outpt_med_admin",  "2356781_CarDS_Aim_1_Outpatient_Enc_Med_Admin.txt",        "outpatient_admin", True),
        ("hosp_med_admin_1", "2356781_CarDS_Aim_1_Hosp_Enc_Med_Admin_1.txt",            "inpatient",        True),
        ("hosp_med_admin_2", "2356781_CarDS_Aim_1_Hosp_Enc_Med_Admin_2.txt",            "inpatient",        True),
    ],
    "implementation": [
        ("meds_list",        "CarDS_2435227_Meds.txt",                                  "home_meds",        False),
        ("outpt_med_admin",  "CarDS_2435227_Outpatient_Enc_Med_Admin.txt",              "outpatient_admin", True),
        ("hosp_med_admin_1", "CarDS_2435227_Hosp_Enc_Med_Admin_1.txt",                 "inpatient",        True),
        ("hosp_med_admin_2", "CarDS_2435227_Hosp_Enc_Med_Admin_2.txt",                 "inpatient",        True),
    ],
}

# Column name candidates -- tried in order, first match wins
MRN_CANDS        = ["PAT_MRN_ID", "pat_mrn_id", "MRN", "mrn"]
DRUG_CANDS       = ["MEDICATION_NAME", "medication_name", "DRUG_NAME", "drug_name"]
# For home_meds: ORDER_INST is the prescription date
# For med_admin: TAKEN_TIME is actual admin time; ORDER_INST is just when ordered
ORDER_DATE_CANDS = ["ORDER_INST", "order_inst", "ORDER_DATE", "order_date",
                    "START_DATE", "start_date"]
TAKEN_TIME_CANDS = ["TAKEN_TIME", "taken_time", "CONTACT_DATE", "contact_date"]
GENERIC_CANDS    = ["SIMPLE_GENERIC", "simple_generic", "GENERIC_NAME", "generic_name"]
PHARM_CANDS      = ["PHARM_CLASS", "pharm_class"]
ROUTE_CANDS      = ["MEDICATION_ROUTE", "medication_route", "ROUTE_SIMPLE", "route_simple",
                    "ROUTE", "route"]
FREQ_CANDS       = ["FREQUENCY", "frequency", "FREQ_NAME", "freq_name", "FREQ", "freq"]
DOSE_CANDS       = ["DOSE", "dose", "MEDICATION_DOSE", "medication_dose",
                    "HV_DISCRETE_DOSE", "hv_discrete_dose"]
DOSE_UNIT_CANDS  = ["DOSE_UNIT", "dose_unit", "MEDICATION_UNIT", "medication_unit",
                    "HV_DOSE_UNIT", "hv_dose_unit"]
STATUS_CANDS     = ["ORDER_STATUS", "order_status"]
CLASS_CANDS      = ["ORDER_CLASS", "order_class", "ORDERING_MODE", "ordering_mode"]
END_CANDS        = ["END_DATE", "end_date", "DISCONTINUE_TIME", "discontinue_time",
                    "DISCON_TIME", "discon_time"]
DISC_REASON_CANDS = ["REASON_FOR_DISCONTINUE", "reason_for_discontinue",
                     "DISCONTINUE_REASON", "discontinue_reason", "DISCON_REASON"]


def _first_match(cols_upper: dict[str, str], candidates: list[str]) -> str | None:
    """cols_upper: {UPPER_COLNAME: original_colname}"""
    for c in candidates:
        if c.upper() in cols_upper:
            return cols_upper[c.upper()]
    return None


def _detect_sep(path: Path) -> str:
    with open(path, "r", encoding="latin-1") as f:
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
    use_taken_time: bool,
    chunksize: int = 200_000,
) -> pd.DataFrame | None:

    if not path.exists():
        print(f"    MISSING: {path.name}")
        return None

    sep = _detect_sep(path)
    print(f"    Reading {path.name}  sep={'TAB' if sep==chr(9) else sep!r}  "
          f"date={'TAKEN_TIME' if use_taken_time else 'ORDER_INST'}")

    chunks_out = []
    total_in = 0
    try:
        reader = pd.read_csv(
            path, sep=sep, chunksize=chunksize,
            low_memory=False, encoding="latin-1",
        )
        for chunk in reader:
            total_in += len(chunk)
            # Strip BOM from first column name if present
            chunk.columns = [c.strip().lstrip("﻿").lstrip("\xef\xbb\xbf")
                             for c in chunk.columns]
            cu = {c.upper(): c for c in chunk.columns}

            mrn_col  = _first_match(cu, MRN_CANDS)
            drug_col = _first_match(cu, DRUG_CANDS)

            if mrn_col is None or drug_col is None:
                print(f"    WARNING: {path.name} missing MRN or drug col -- "
                      f"cols: {list(chunk.columns[:8])}")
                return None

            # Date: use TAKEN_TIME for admin files, ORDER_INST for prescription files
            if use_taken_time:
                date_col = _first_match(cu, TAKEN_TIME_CANDS) or _first_match(cu, ORDER_DATE_CANDS)
            else:
                date_col = _first_match(cu, ORDER_DATE_CANDS)

            out = pd.DataFrame()
            out["MRN"]       = chunk[mrn_col].astype(str).str.strip()
            # Strip leading non-numeric prefix (Epic MRNs are pure numeric)
            out["MRN"]       = out["MRN"].str.replace(r"^[A-Za-z]+", "", regex=True)
            out["drug_name"] = chunk[drug_col].astype(str).str.strip()

            out["order_date"] = (
                pd.to_datetime(chunk[date_col], errors="coerce")
                if date_col else pd.NaT
            )

            # Optional columns
            for out_col, cands in [
                ("generic_name",       GENERIC_CANDS),
                ("pharm_class",        PHARM_CANDS),
                ("route",              ROUTE_CANDS),
                ("frequency",          FREQ_CANDS),
                ("dose",               DOSE_CANDS),
                ("dose_unit",          DOSE_UNIT_CANDS),
                ("order_status",       STATUS_CANDS),
                ("order_class",        CLASS_CANDS),
                ("end_date",           END_CANDS),
                ("discontinue_reason", DISC_REASON_CANDS),
            ]:
                src = _first_match(cu, cands)
                out[out_col] = chunk[src].values if src else pd.NA

            out["setting"]     = setting
            out["cohort"]      = cohort
            out["source_file"] = path.name

            # Drop blank drug names and MRNs
            mask = (
                out["drug_name"].notna()
                & (out["drug_name"] != "")
                & (out["drug_name"] != "nan")
                & out["MRN"].notna()
                & (out["MRN"] != "")
                & (out["MRN"] != "nan")
            )
            out = out[mask]
            chunks_out.append(out)
            gc.collect()

    except Exception as e:
        print(f"    ERROR reading {path.name}: {e}")
        return None

    if not chunks_out:
        return None

    result = pd.concat(chunks_out, ignore_index=True)
    print(f"    -> {total_in:,} rows in, {len(result):,} rows kept")
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
    p.add_argument("--home-meds-only", action="store_true",
                   help="Only read *_Meds.txt files (fastest, sufficient for TTE index)")
    p.add_argument("--no-inpatient", action="store_true",
                   help="Skip *_Hosp_Enc_Med_Admin files")
    p.add_argument("--dry-run", action="store_true",
                   help="Print file existence + sizes, do not write output")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Build drug_master -> {args.output}")
    print(f"Started: {datetime.now().isoformat()}")

    dirs = {
        "t2dm":           Path(args.t2dm_dir)  if args.t2dm_dir  else None,
        "cmp":            Path(args.cmp_dir)   if args.cmp_dir   else None,
        "implementation": Path(args.impl_dir)  if args.impl_dir  else None,
    }

    # Safety: abort if output path is inside any source directory
    out_resolved = Path(args.output).resolve()
    for cohort, base in dirs.items():
        if base is None:
            continue
        base_resolved = base.resolve()
        try:
            out_resolved.relative_to(base_resolved)
            print(f"ERROR: --output is inside source dir {base_resolved} -- refusing to write into source data")
            sys.exit(1)
        except ValueError:
            pass  # not a subdirectory -- safe

    if args.dry_run:
        print("\n[DRY RUN] File inventory:")
        for cohort, base in dirs.items():
            if base is None:
                print(f"  {cohort}: no path provided")
                continue
            for _, fname, setting, _ in COHORT_SPECS[cohort]:
                if args.home_meds_only and setting != "home_meds":
                    continue
                if args.no_inpatient and setting == "inpatient":
                    continue
                fp = base / fname
                exists = fp.exists()
                size = f"{fp.stat().st_size / 1e6:.0f} MB" if exists else "MISSING"
                print(f"  {cohort:<18} {setting:<18} {fname}  [{size}]")
        return

    all_parts: list[pd.DataFrame] = []

    for cohort, base in dirs.items():
        if base is None:
            print(f"\n[{cohort}] skipped -- no path provided")
            continue
        print(f"\n{'─'*60}")
        print(f"  Cohort: {cohort}  |  {base}")
        for _, fname, setting, use_taken_time in COHORT_SPECS[cohort]:
            if args.home_meds_only and setting != "home_meds":
                continue
            if args.no_inpatient and setting == "inpatient":
                continue
            fp = base / fname
            part = _read_med_file(fp, setting, cohort, use_taken_time)
            if part is not None:
                all_parts.append(part)
            gc.collect()

    if not all_parts:
        print("ERROR: no data loaded -- check paths")
        return

    dm = pd.concat(all_parts, ignore_index=True)
    print(f"\nTotal rows before dedup: {len(dm):,}")

    dedup_cols = ["MRN", "drug_name", "order_date", "setting"]
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
    print(f"  Date range    : {dm['order_date'].min().date()} -> {dm['order_date'].max().date()}")
    print(f"\n  By setting:")
    for s, n in dm["setting"].value_counts().items():
        pct = 100 * n / len(dm)
        print(f"    {s:<22}  {n:>12,}  ({pct:.1f}%)")
    print(f"\n  By cohort:")
    for c, n in dm["cohort"].value_counts().items():
        pct = 100 * n / len(dm)
        print(f"    {c:<22}  {n:>12,}  ({pct:.1f}%)")
    if "order_class" in dm.columns:
        print(f"\n  order_class (home_meds only):")
        sub = dm[dm["setting"] == "home_meds"]
        for v, n in sub["order_class"].value_counts().head(8).items():
            pct = 100 * n / len(sub)
            print(f"    {str(v):<30}  {n:>10,}  ({pct:.1f}%)")
    print(f"{'='*65}")

    # ── Save ──────────────────────────────────────────────────────────────────
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    dm.to_parquet(out, index=False, compression="snappy")
    print(f"\nSaved -> {out}  ({out.stat().st_size / 1e6:.0f} MB)")
    print(f"Done: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
