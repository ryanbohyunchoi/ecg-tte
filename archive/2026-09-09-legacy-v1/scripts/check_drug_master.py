"""
check_drug_master.py — sanity-check drug_master shard(s) or a merged parquet.

Usage:
    # Check all shards in output dir (build_drug_master.py per-source mode):
    python scripts/check_drug_master.py --shard-dir /mnt/raid0/rbc58/mm_vhd/drug/shards/

    # Check a single merged parquet:
    python scripts/check_drug_master.py --file /mnt/raid0/rbc58/mm_vhd/drug/drug_master_v2.parquet

    # Check single file, sample drug names to stdout:
    python scripts/check_drug_master.py --file ... --show-samples
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

REQUIRED_COLS = ["MRN", "drug_name", "order_date", "setting", "cohort"]
OPTIONAL_COLS = ["generic_name", "pharm_class", "route", "frequency",
                 "dose", "dose_unit", "order_status", "end_date", "discontinue_date"]
VALID_SETTINGS = {"home_meds", "outpatient_admin", "inpatient"}
VALID_COHORTS  = {"t2dm", "cmp", "implementation"}

# Drugs expected to be present (arm keywords from PARADIGM-HF + COMET trials)
PROBE_DRUGS = [
    "SACUBITRIL", "ENTRESTO",         # PARADIGM-HF treated arm
    "ENALAPRIL", "VASOTEC",           # PARADIGM-HF control arm
    "CARVEDILOL", "COREG",            # COMET treated arm
    "METOPROLOL", "LOPRESSOR",        # COMET control arm
]


def _load(path: Path) -> pd.DataFrame:
    print(f"\n{'─'*60}")
    print(f"Loading: {path.name}  ({path.stat().st_size / 1e6:.1f} MB)")
    df = pd.read_parquet(path)
    print(f"  Rows: {len(df):,}   Cols: {df.columns.tolist()}")
    return df


def _check_shard(df: pd.DataFrame, name: str) -> list[str]:
    issues = []

    # Required columns
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        issues.append(f"MISSING required cols: {missing}")

    if "MRN" in df.columns:
        n_mrn = df["MRN"].notna().sum()
        n_blank_mrn = (df["MRN"].astype(str).str.strip() == "").sum()
        print(f"  Unique MRNs      : {df['MRN'].nunique():,}")
        print(f"  Null MRN         : {df['MRN'].isna().sum():,}")
        print(f"  Blank MRN        : {n_blank_mrn:,}")
        if n_blank_mrn > 0:
            issues.append(f"{n_blank_mrn:,} blank MRNs")

    if "drug_name" in df.columns:
        null_drug = df["drug_name"].isna().sum()
        blank_drug = (df["drug_name"].astype(str).str.strip() == "").sum()
        print(f"  Null drug_name   : {null_drug:,}")
        print(f"  Blank drug_name  : {blank_drug:,}")
        if null_drug + blank_drug > 0:
            issues.append(f"{null_drug + blank_drug:,} null/blank drug_name")

    if "order_date" in df.columns:
        n_date = df["order_date"].notna().sum()
        pct = 100 * n_date / max(len(df), 1)
        print(f"  order_date fill  : {n_date:,} / {len(df):,} ({pct:.1f}%)")
        if df["order_date"].notna().any():
            print(f"  Date range       : {df['order_date'].min()} → {df['order_date'].max()}")
        if pct < 50:
            issues.append(f"order_date only {pct:.0f}% filled")

    if "setting" in df.columns:
        vals = set(df["setting"].dropna().unique())
        bad = vals - VALID_SETTINGS
        print(f"  Settings         : {sorted(vals)}")
        if bad:
            issues.append(f"Unknown settings: {bad}")

    if "cohort" in df.columns:
        vals = set(df["cohort"].dropna().unique())
        bad = vals - VALID_COHORTS
        print(f"  Cohorts          : {sorted(vals)}")
        if bad:
            issues.append(f"Unknown cohorts: {bad}")

    return issues


def _probe_drugs(df: pd.DataFrame) -> None:
    if "drug_name" not in df.columns:
        return
    drug_upper = df["drug_name"].astype(str).str.upper()
    print("\n  Probe drug hits (arm keywords):")
    for kw in PROBE_DRUGS:
        n = drug_upper.str.contains(kw, na=False).sum()
        mrns = df.loc[drug_upper.str.contains(kw, na=False), "MRN"].nunique() if "MRN" in df.columns else "?"
        flag = "" if n > 0 else "  ← NOT FOUND"
        print(f"    {kw:<20} {n:>8,} rows  {mrns:>6} pts{flag}")


def _sample_drugs(df: pd.DataFrame, n: int = 30) -> None:
    if "drug_name" not in df.columns:
        return
    sample = df["drug_name"].dropna().value_counts().head(n)
    print(f"\n  Top-{n} drug names by frequency:")
    for name, cnt in sample.items():
        print(f"    {cnt:>8,}  {name}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Sanity-check drug_master parquet(s)")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--shard-dir", type=Path, help="Directory of per-source shard parquets")
    grp.add_argument("--file",      type=Path, help="Single merged parquet file")
    ap.add_argument("--show-samples", action="store_true",
                    help="Print top drug names to stdout")
    ap.add_argument("--glob", default="*.parquet",
                    help="Glob pattern when using --shard-dir (default: *.parquet)")
    args = ap.parse_args()

    all_issues: dict[str, list[str]] = {}

    if args.file:
        df = _load(args.file)
        issues = _check_shard(df, args.file.name)
        _probe_drugs(df)
        if args.show_samples:
            _sample_drugs(df)
        all_issues[args.file.name] = issues

    else:
        shards = sorted(args.shard_dir.glob(args.glob))
        if not shards:
            print(f"No parquets found in {args.shard_dir} matching '{args.glob}'")
            sys.exit(1)
        print(f"Found {len(shards)} shard(s) in {args.shard_dir}")
        dfs = []
        for path in shards:
            df = _load(path)
            issues = _check_shard(df, path.name)
            _probe_drugs(df)
            if args.show_samples:
                _sample_drugs(df)
            all_issues[path.name] = issues
            dfs.append(df)

        # Combined stats
        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            print(f"\n{'═'*60}")
            print(f"COMBINED ({len(shards)} shards)")
            print(f"  Total rows       : {len(combined):,}")
            print(f"  Unique MRNs      : {combined['MRN'].nunique():,}" if "MRN" in combined else "")
            _probe_drugs(combined)

    # Summary
    print(f"\n{'═'*60}")
    print("ISSUE SUMMARY")
    any_issue = False
    for fname, issues in all_issues.items():
        if issues:
            any_issue = True
            print(f"  {fname}:")
            for iss in issues:
                print(f"    ✗ {iss}")
        else:
            print(f"  {fname}: OK")

    if any_issue:
        sys.exit(1)
    else:
        print("\nAll checks passed.")


if __name__ == "__main__":
    main()
