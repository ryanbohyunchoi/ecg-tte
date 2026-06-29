"""
scripts/build_drug_master.py

Rebuild drug_master.parquet from raw S3 medication files across all cohorts.

Replaces the PREVENT-ATC-filtered drug_exposure ETL. Key differences:
  - No ATC filtering: keeps all drugs (pipeline uses string matching, not ATC)
  - Reads from all available S3 cohort sources (ECG_ASCVD, T2DM, CMP, etc.)
  - Preserves setting column (outpatient/inpatient) from source directory name
  - Output format matches what load_drug_master() in cohort_utils.py expects:
    MRN, drug_name, order_date, source, [optional: end_date, discontinue_date,
    discontinue_reason, order_status, frequency, route, dose, dose_unit]

Raw file expected columns (Epic Clarity/Caboodle export):
  PAT_MRN_ID    — patient MRN
  ORDER_INST    — order datetime (= drug_exposure_start_datetime)
  MEDICATION_NAME / DRUG_NAME — drug name string (pipeline matches on this)
  SIMPLE_GENERIC — generic name (kept as generic_name for reference)
  PHARM_CLASS   — pharmacological class (kept for reference)
  [optional] ROUTE, FREQ, DOSE, DOSE_UNIT, ORDER_STATUS, DISCONTINUE_TIME,
             DISCONTINUE_REASON, END_DATE

Usage:
    python scripts/build_drug_master.py \\
        --sources outpatient=/path/to/ecg_ascvd/outpmeds \\
                  outpatient=/path/to/t2dm/outpmeds \\
                  outpatient=/path/to/cmp/outpmeds \\
                  inpatient=/path/to/ecg_ascvd/inpmeds \\
        --output  /mnt/raid0/rbc58/mm_vhd/drug/drug_master_v2.parquet \\
        --n-limit 0

    # Or use config-based discovery:
    python scripts/build_drug_master.py \\
        --config-module config.config \\
        --output /mnt/raid0/rbc58/mm_vhd/drug/drug_master_v2.parquet

    # Dry run: just print what files would be read
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
import polars as pl
from tqdm import tqdm

# ── Column aliases — handles varying Epic export naming conventions ────────────
MRN_CANDIDATES     = ["PAT_MRN_ID", "MRN", "pat_mrn_id", "mrn"]
DATE_CANDIDATES    = ["ORDER_INST", "order_inst", "ORDER_DATE", "order_date",
                      "START_DATE", "start_date", "drug_exposure_start_datetime"]
DRUG_CANDIDATES    = ["MEDICATION_NAME", "medication_name", "DRUG_NAME", "drug_name",
                      "drug_source_value"]
GENERIC_CANDIDATES = ["SIMPLE_GENERIC", "simple_generic", "GENERIC_NAME", "generic_name"]
PHARM_CANDIDATES   = ["PHARM_CLASS", "pharm_class"]
ROUTE_CANDIDATES   = ["ROUTE", "route"]
FREQ_CANDIDATES    = ["FREQ", "freq", "FREQUENCY", "frequency"]
DOSE_CANDIDATES    = ["DOSE", "dose"]
DOSE_UNIT_CANDS    = ["DOSE_UNIT", "dose_unit"]
STATUS_CANDIDATES  = ["ORDER_STATUS", "order_status"]
DISC_DATE_CANDS    = ["DISCONTINUE_TIME", "discontinue_time", "DISCONTINUE_DATE",
                      "discontinue_date"]
DISC_REASON_CANDS  = ["DISCONTINUE_REASON", "discontinue_reason"]
END_DATE_CANDS     = ["END_DATE", "end_date", "drug_exposure_end_datetime"]


def _first_col(df_cols: list[str], candidates: list[str]) -> str | None:
    col_set = set(df_cols)
    return next((c for c in candidates if c in col_set), None)


def _read_source_dir(
    source_dir: Path,
    setting: str,
    cohort_tag: str,
) -> pd.DataFrame | None:
    """
    Read all parquet files under source_dir, standardise column names,
    return a tidy DataFrame or None if no files found.

    setting: "outpatient" | "inpatient" — stored in output `setting` column
    cohort_tag: e.g. "ecg_ascvd", "t2dm", "cmp" — stored in `cohort` column
    """
    files = list(source_dir.rglob("*.parquet"))
    if not files:
        print(f"  SKIP {source_dir} — no parquet files found")
        return None

    chunks = []
    for fp in tqdm(files, desc=f"  {cohort_tag}/{setting}"):
        try:
            lazy = pl.scan_parquet(str(fp))
            schema_cols = lazy.schema.names()
            want_cols = []
            for clist in [MRN_CANDIDATES, DATE_CANDIDATES, DRUG_CANDIDATES,
                          GENERIC_CANDIDATES, PHARM_CANDIDATES, ROUTE_CANDIDATES,
                          FREQ_CANDIDATES, DOSE_CANDIDATES, DOSE_UNIT_CANDS,
                          STATUS_CANDIDATES, DISC_DATE_CANDS, DISC_REASON_CANDS,
                          END_DATE_CANDS]:
                col = _first_col(schema_cols, clist)
                if col and col not in want_cols:
                    want_cols.append(col)
            df = lazy.select(want_cols).collect().to_pandas()
        except Exception as e:
            print(f"  WARNING: {fp.name} failed: {e}")
            continue

        if df.empty:
            continue

        # Standardise column names
        rename = {}
        for col, cands in [
            ("MRN",               MRN_CANDIDATES),
            ("order_date",        DATE_CANDIDATES),
            ("drug_name",         DRUG_CANDIDATES),
            ("generic_name",      GENERIC_CANDIDATES),
            ("pharm_class",       PHARM_CANDIDATES),
            ("route",             ROUTE_CANDIDATES),
            ("frequency",         FREQ_CANDIDATES),
            ("dose",              DOSE_CANDIDATES),
            ("dose_unit",         DOSE_UNIT_CANDS),
            ("order_status",      STATUS_CANDIDATES),
            ("discontinue_date",  DISC_DATE_CANDS),
            ("discontinue_reason", DISC_REASON_CANDS),
            ("end_date",          END_DATE_CANDS),
        ]:
            src = _first_col(list(df.columns), cands)
            if src and src != col:
                rename[src] = col
        if rename:
            df = df.rename(columns=rename)

        # Strip MRN prefix (Epic exports often "E123456" → "123456")
        if "MRN" in df.columns:
            df["MRN"] = df["MRN"].astype(str).str.strip()
            # Remove leading non-numeric prefix (e.g. "E", "Y")
            df["MRN"] = df["MRN"].str.replace(r"^[A-Za-z]+", "", regex=True)

        # Parse order_date
        if "order_date" in df.columns:
            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
            df = df.dropna(subset=["order_date"])

        # Drop rows with no drug name
        if "drug_name" in df.columns:
            df = df.dropna(subset=["drug_name"])
            df = df[df["drug_name"].astype(str).str.strip() != ""]

        df["setting"] = setting
        df["cohort"]  = cohort_tag
        chunks.append(df)
        gc.collect()

    if not chunks:
        return None

    return pd.concat(chunks, ignore_index=True)


def _discover_sources_from_config(config_module: str) -> list[tuple[str, str, Path]]:
    """
    Auto-discover source dirs from config module.
    Returns list of (setting, cohort_tag, path).
    """
    import importlib
    cfg = importlib.import_module(config_module)

    sources = []
    for attr, tag in [
        ("ECG_ASCVD_S3", "ecg_ascvd"),
        ("T2DM_S3",      "t2dm"),
        ("CMP_S3",       "cmp"),
    ]:
        base = getattr(cfg, attr, None)
        if not base:
            print(f"  Config attribute {attr} not found — skipping")
            continue
        base = Path(base)
        for subdir, setting in [("outpmeds", "outpatient"), ("inpmeds", "inpatient")]:
            p = base / subdir
            if p.exists():
                sources.append((setting, tag, p))
                print(f"  Found: {setting} {tag} → {p}")
            else:
                print(f"  Missing: {p} — skipping")
    return sources


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Rebuild drug_master from raw S3 medication files (all drugs, no ATC filter)"
    )
    p.add_argument("--output", required=True,
                   help="Output path for drug_master.parquet")

    src_grp = p.add_mutually_exclusive_group(required=True)
    src_grp.add_argument(
        "--sources", nargs="+", metavar="SETTING=PATH",
        help="Space-separated list of setting=path pairs. "
             "SETTING must be 'outpatient' or 'inpatient'. "
             "Example: outpatient=/s3/ecg_ascvd/outpmeds inpatient=/s3/ecg_ascvd/inpmeds"
    )
    src_grp.add_argument(
        "--config-module", default=None,
        help="Python config module with ECG_ASCVD_S3/T2DM_S3/CMP_S3 paths "
             "(e.g. config.config). Auto-discovers outpmeds/inpmeds subdirs."
    )
    p.add_argument("--cohort-tag", default="",
                   help="Cohort tag when using --sources (default: derived from path)")
    p.add_argument("--n-limit", type=int, default=0,
                   help="Limit total output rows for testing (0 = no limit)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print files that would be read without writing output")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Build drug_master → {args.output}")
    print(f"Started: {datetime.now().isoformat()}")

    # ── Collect source dirs ───────────────────────────────────────────────────
    sources: list[tuple[str, str, Path]] = []

    if args.config_module:
        sources = _discover_sources_from_config(args.config_module)
    else:
        for spec in args.sources:
            if "=" not in spec:
                print(f"  WARNING: invalid --sources entry {spec!r} (expected SETTING=PATH)")
                continue
            setting, path_str = spec.split("=", 1)
            setting = setting.strip().lower()
            if setting not in ("outpatient", "inpatient"):
                print(f"  WARNING: setting must be 'outpatient' or 'inpatient', got {setting!r}")
                continue
            p = Path(path_str.strip())
            tag = args.cohort_tag or p.parent.name
            sources.append((setting, tag, p))

    if not sources:
        print("ERROR: no valid source directories found")
        sys.exit(1)

    if args.dry_run:
        print("\n[DRY RUN] Would read from:")
        for setting, tag, p in sources:
            files = list(p.rglob("*.parquet"))
            print(f"  {setting:<12} {tag:<15} {p}  ({len(files)} parquet files)")
        return

    # ── Read and combine ──────────────────────────────────────────────────────
    all_parts = []
    for setting, tag, src_dir in sources:
        print(f"\nReading {setting} / {tag} from {src_dir}")
        part = _read_source_dir(src_dir, setting, tag)
        if part is not None:
            print(f"  → {len(part):,} rows")
            all_parts.append(part)
        gc.collect()

    if not all_parts:
        print("ERROR: no data loaded from any source")
        sys.exit(1)

    dm = pd.concat(all_parts, ignore_index=True)
    print(f"\nTotal rows before dedup: {len(dm):,}")

    # ── Dedup (same MRN + drug_name + order_date = same dispense record) ─────
    dedup_cols = [c for c in ["MRN", "drug_name", "order_date"] if c in dm.columns]
    before = len(dm)
    dm = dm.drop_duplicates(subset=dedup_cols)
    print(f"After dedup: {len(dm):,}  (removed {before - len(dm):,} duplicates)")

    # Drop rows without MRN or order_date
    dm = dm.dropna(subset=[c for c in ["MRN", "order_date"] if c in dm.columns])
    print(f"After drop-na key cols: {len(dm):,}")

    if args.n_limit > 0:
        dm = dm.head(args.n_limit)
        print(f"[--n-limit] truncated to {len(dm):,} rows")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  drug_master summary")
    print(f"  Rows          : {len(dm):,}")
    print(f"  Unique MRNs   : {dm['MRN'].nunique():,}")
    if "drug_name" in dm.columns:
        print(f"  Unique drugs  : {dm['drug_name'].nunique():,}")
    if "order_date" in dm.columns:
        print(f"  Date range    : {dm['order_date'].min().date()} → {dm['order_date'].max().date()}")
    if "setting" in dm.columns:
        print(f"\n  By setting:")
        for s, n in dm["setting"].value_counts().items():
            print(f"    {s:<15}  {n:>12,}")
    if "cohort" in dm.columns:
        print(f"\n  By cohort:")
        for c, n in dm["cohort"].value_counts().items():
            print(f"    {c:<15}  {n:>12,}")
    print(f"{'='*60}")

    # ── Save ──────────────────────────────────────────────────────────────────
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    dm.to_parquet(out, index=False)
    print(f"\nSaved → {out}")
    print(f"Done: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
