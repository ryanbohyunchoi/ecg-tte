"""
scripts/explore_drug_data.py

Explore drug data sources to assess inpatient vs outpatient record separation.
Examines:
  1. drug_master schema + value distributions (Yale EHR table)
  2. OMOP drug_exposure table (standard; has drug_type_concept_id for setting)
  3. Cross-reference: same patients in both tables?

Answers the key TTE question: are we accidentally using inpatient drug orders
as index events? Inpatient-only initiators introduce immortal time bias.

Usage (on cluster):
    python scripts/explore_drug_data.py \\
        --drug-master /mnt/raid0/rbc58/mm_vhd/drug/drug_master.parquet \\
        --drug-exposure-dir /home/rbc58/mnt/ascvd/omop_database/drug_exposure \\
        --keywords "SACUBITRIL,ENTRESTO,ENALAPRIL,VASOTEC" \\
        --n-sample 500000

    # drug_exposure dir optional — if absent, only drug_master is examined.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


# ── OMOP drug_type_concept_id labels ──────────────────────────────────────────
# Full list at https://athena.ohdsi.org/ → domain Drug
DRUG_TYPE_LABELS = {
    38000175: "Prescription dispensed in pharmacy",
    38000176: "Drug administration record",
    38000177: "Prescription written",
    38000178: "Dispensed in Home",
    38000179: "Physician administered drug",
    38000180: "Inpatient administration",
    43542356: "Physician administered drug (identified as procedure)",
    44787730: "Patient Self-Reported Medication",
    45754907: "Prescription dispensed through mail-order pharmacy",
    581373:   "Dispensed in pharmacy",
    581452:   "Inpatient administration of an over-the-counter drug",
}

INPATIENT_CONCEPT_IDS = {38000180, 38000176, 581452, 43542356}


def _header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def explore_drug_master(path: str, keywords: list[str], n_sample: int) -> pd.DataFrame:
    _header("drug_master")

    schema = pq.read_schema(path)
    print(f"  Schema ({len(schema.names)} cols): {schema.names}")

    print(f"\n  Reading first {n_sample:,} rows …")
    pf = pq.ParquetFile(path)
    chunks = []
    n_read = 0
    for batch in pf.iter_batches(batch_size=500_000):
        df = batch.to_pandas()
        df.columns = [c.strip() for c in df.columns]
        chunks.append(df)
        n_read += len(df)
        if n_read >= n_sample:
            break
    dm = pd.concat(chunks, ignore_index=True).head(n_sample)
    print(f"  Loaded {len(dm):,} rows")

    # Drug name column
    drug_col = next((c for c in dm.columns if c.lower() == "drug_name"), None)
    if drug_col:
        dm["drug_upper"] = dm[drug_col].astype(str).str.upper()
    else:
        print("  WARNING: drug_name column not found")
        return dm

    # Date column
    date_col = next((c for c in dm.columns
                     if c.lower() in ("order_date", "start_date")), None)
    if date_col:
        dm["_date"] = pd.to_datetime(dm[date_col], errors="coerce")
        print(f"\n  Date col: {date_col!r}  "
              f"range {dm['_date'].min().date()} → {dm['_date'].max().date()}")

    # order_status distribution
    if "order_status" in dm.columns:
        print(f"\n  order_status value counts (top 15):")
        vc = dm["order_status"].value_counts().head(15)
        for val, n in vc.items():
            print(f"    {str(val):<35}  {n:>10,}")
    else:
        print("\n  NOTE: order_status column NOT present in drug_master")

    # frequency distribution (inpatient orders often say "ONCE", "Q4H", etc.)
    if "frequency" in dm.columns:
        print(f"\n  frequency value counts (top 20):")
        vc = dm["frequency"].value_counts().head(20)
        for val, n in vc.items():
            print(f"    {str(val):<35}  {n:>10,}")

    # Keyword-matched records
    pattern = "|".join(keywords)
    mask = dm["drug_upper"].str.contains(pattern, regex=True, na=False)
    matched = dm[mask].copy()
    print(f"\n  Records matching {keywords}: {len(matched):,} / {len(dm):,} "
          f"({100*len(matched)/len(dm):.2f}%)")

    if not matched.empty:
        print(f"\n  Matched drug_name values (top 30):")
        for val, n in matched[drug_col].value_counts().head(30).items():
            print(f"    {str(val):<55}  {n:>8,}")

        if "order_status" in matched.columns:
            print(f"\n  Matched → order_status (top 10):")
            for val, n in matched["order_status"].value_counts().head(10).items():
                print(f"    {str(val):<35}  {n:>8,}")

        if "frequency" in matched.columns:
            print(f"\n  Matched → frequency (top 15):")
            for val, n in matched["frequency"].value_counts().head(15).items():
                print(f"    {str(val):<35}  {n:>8,}")

        if date_col:
            print(f"\n  Matched → date range: "
                  f"{matched['_date'].min().date()} → {matched['_date'].max().date()}")
            # Year distribution
            if "_date" in matched.columns:
                yr = matched["_date"].dt.year.value_counts().sort_index()
                print(f"\n  Matched → records per year:")
                for year, n in yr.items():
                    bar = "█" * min(40, int(40 * n / yr.max()))
                    print(f"    {year}  {n:>7,}  {bar}")

    return matched


def explore_drug_exposure(
    drug_exp_dir: str,
    keywords: list[str],
    n_sample: int,
) -> pd.DataFrame | None:
    _header("OMOP drug_exposure")

    exp_dir = Path(drug_exp_dir)
    shards = sorted(exp_dir.glob("drug_exposure*.parquet"))
    if not shards:
        print(f"  No drug_exposure shards in {exp_dir}")
        return None
    print(f"  Found {len(shards)} shards")

    schema = pq.read_schema(str(shards[0]))
    print(f"  Schema ({len(schema.names)} cols): {schema.names}")

    WANT = [
        "person_id", "drug_concept_id", "drug_type_concept_id",
        "drug_source_value", "drug_source_concept_id",
        "drug_exposure_start_date", "drug_exposure_start_datetime",
        "visit_occurrence_id", "quantity", "days_supply",
        "route_concept_id", "route_source_value",
    ]
    avail = {c.lower(): c for c in schema.names}
    cols_to_read = [avail[c] for c in WANT if c in avail]
    print(f"  Reading cols: {cols_to_read}")

    chunks = []
    n_read = 0
    for shard in shards:
        try:
            df = pd.read_parquet(shard, columns=cols_to_read)
        except Exception as e:
            print(f"  WARNING: shard {shard.name} failed: {e}")
            continue
        chunks.append(df)
        n_read += len(df)
        if n_read >= n_sample:
            break
    if not chunks:
        print("  No data loaded from drug_exposure")
        return None

    de = pd.concat(chunks, ignore_index=True).head(n_sample)
    print(f"\n  Loaded {len(de):,} rows")

    # drug_type_concept_id distribution
    if "drug_type_concept_id" in de.columns:
        print(f"\n  drug_type_concept_id distribution (ALL records):")
        vc = de["drug_type_concept_id"].value_counts()
        for cid, n in vc.items():
            label = DRUG_TYPE_LABELS.get(int(cid), "UNKNOWN")
            is_inp = " ← INPATIENT" if int(cid) in INPATIENT_CONCEPT_IDS else ""
            print(f"    {int(cid):>10}  {label:<45}  {n:>10,}{is_inp}")
    else:
        print("  NOTE: drug_type_concept_id not present")

    # Keyword-matched via drug_source_value
    src_col = next(
        (c for c in de.columns if "source_value" in c.lower() and "drug" in c.lower()),
        None,
    )
    if src_col:
        de["drug_upper"] = de[src_col].astype(str).str.upper()
        pattern = "|".join(keywords)
        mask = de["drug_upper"].str.contains(pattern, regex=True, na=False)
        matched = de[mask].copy()
        print(f"\n  Records matching {keywords}: {len(matched):,} / {len(de):,}")

        if not matched.empty and "drug_type_concept_id" in matched.columns:
            print(f"\n  Matched → drug_type_concept_id (INPATIENT vs OUTPATIENT):")
            vc2 = matched["drug_type_concept_id"].value_counts()
            for cid, n in vc2.items():
                label = DRUG_TYPE_LABELS.get(int(cid), "UNKNOWN")
                is_inp = " ← INPATIENT" if int(cid) in INPATIENT_CONCEPT_IDS else ""
                pct = 100 * n / len(matched)
                print(f"    {int(cid):>10}  {label:<45}  {n:>8,}  ({pct:.1f}%){is_inp}")

            n_inp = matched["drug_type_concept_id"].isin(INPATIENT_CONCEPT_IDS).sum()
            print(f"\n  SUMMARY: {n_inp:,} / {len(matched):,} "
                  f"({100*n_inp/len(matched):.1f}%) matched records are INPATIENT")

        return matched

    return de


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Explore drug data sources for inpatient/outpatient separation"
    )
    p.add_argument("--drug-master",       required=True)
    p.add_argument("--drug-exposure-dir", default="",
                   help="OMOP drug_exposure shard dir (optional)")
    p.add_argument("--keywords",
                   default="SACUBITRIL,ENTRESTO,ENALAPRIL,VASOTEC,ENALAPRILAT",
                   help="Comma-separated drug keywords to spotlight (default: PARADIGM-HF drugs)")
    p.add_argument("--n-sample",          type=int, default=500_000,
                   help="Max rows to read from each source (default 500k)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    keywords = [k.strip().upper() for k in args.keywords.split(",") if k.strip()]
    print(f"Keywords: {keywords}")

    dm_matched = explore_drug_master(args.drug_master, keywords, args.n_sample)

    if args.drug_exposure_dir:
        de_matched = explore_drug_exposure(
            args.drug_exposure_dir, keywords, args.n_sample
        )
    else:
        _header("OMOP drug_exposure")
        print("  --drug-exposure-dir not provided — skipping")
        print("  To check inpatient/outpatient split via drug_type_concept_id, pass:")
        print("  --drug-exposure-dir /home/rbc58/mnt/ascvd/omop_database/drug_exposure")
        de_matched = None

    # ── Conclusions ───────────────────────────────────────────────────────────
    _header("Conclusions for TTE index event definition")
    print("""
  Key question: are inpatient drug administrations contaminating arm assignment?

  Inpatient index events cause immortal time bias:
    - Patient admitted, receives drug once (IV or hospital formulary substitution)
    - Gets assigned to that arm with index = admission date
    - Cannot "not receive" the drug after discharge → immortal time before discharge
    - Mortality during admission attributed to drug exposure incorrectly

  What to look for:
    drug_master:
      order_status = "Completed"/"Active" → likely outpatient prescription fill
      order_status = "Verified"/"Ordered" → could be inpatient order
      frequency = "Q4H", "Q8H", "ONCE"   → inpatient dosing pattern
      frequency = "DAILY", "BID"          → could be outpatient or inpatient

    drug_exposure (OMOP):
      drug_type_concept_id = 38000180 (Inpatient administration) → EXCLUDE from index
      drug_type_concept_id = 38000175 (Prescription dispensed)    → KEEP
      drug_type_concept_id = 38000177 (Prescription written)      → KEEP

  Recommended fix (if inpatient contamination found):
    Option A: Filter drug_master to outpatient fills only via order_status/frequency
    Option B: Join on OMOP drug_exposure drug_type_concept_id, exclude inpatient
    Option C: Add --require-outpatient flag + min-fills ≥ 2 (inpatient one-offs
              will fail the ≥2 fills adherence check in stage3)
""")


if __name__ == "__main__":
    main()
