"""
scripts/explore_omop_sources.py

Read-only schema + frequency inspector for OMOP sources not yet used by the pipeline:
  measurement_labs, measurement_vitals, observation_occurrence (ICD10),
  observation_period, death, person.

Run BEFORE writing loaders — output defines concept_id → covariate name maps.

Usage:
    python scripts/explore_omop_sources.py \\
        --omop-dir    /mnt/raid0/bb2238/ecg_ascvd/omop_database \\
        --out-dir     /home/rbc58/mnt/ecg-tte/omop_inspection \\
        [--n-lab-shards 5]   # number of measurement_labs shards to sample (default 5)
        [--n-obs-shards 5]   # number of observation_icd10 shards to sample (default 5)
        [--top-n 100]        # top-N concept/code rows per source (default 100)

Outputs (all in --out-dir):
    schema_summary.txt          -- dtypes + row counts per source
    lab_concept_freq.csv        -- top measurement_concept_id for labs
    vital_concept_freq.csv      -- top measurement_concept_id for vitals
    observation_code_freq.csv   -- top observation_source_value (ICD10 codes)
    death_schema.txt            -- death table column inspection
    person_schema.txt           -- person table column inspection

No patient data written — concept IDs and aggregate counts only.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _schema_summary(path: Path) -> str:
    """Return dtype/column summary from parquet metadata (no data read)."""
    schema = pq.read_schema(path)
    lines = [f"  File    : {path.name}",
             f"  Columns : {len(schema)}"]
    for field in schema:
        lines.append(f"    {field.name:<45} {field.type}")
    return "\n".join(lines)


def _row_count(path: Path) -> int:
    meta = pq.read_metadata(path)
    return meta.num_rows


def _sample_shards(paths: list[Path], n: int) -> list[Path]:
    """Take every k-th shard so we get a spread."""
    if len(paths) <= n:
        return paths
    step = len(paths) // n
    return [paths[i] for i in range(0, len(paths), step)][:n]


def _concept_freq(shards: list[Path],
                  concept_col: str,
                  name_col: str | None = None,
                  value_col: str | None = None,
                  top_n: int = 100) -> pd.DataFrame:
    """
    Aggregate concept_id frequency across shards.
    Returns DataFrame with: concept_id, concept_name (if col exists),
    row_count, pct_of_sampled, example_value (if value_col given).
    """
    frames = []
    for p in shards:
        cols = [concept_col]
        if name_col:
            cols.append(name_col)
        if value_col:
            cols.append(value_col)
        # Only read needed columns
        df = pd.read_parquet(p, columns=[c for c in cols if c])
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    total = len(combined)

    if name_col and name_col in combined.columns:
        agg = (combined
               .groupby([concept_col, name_col], dropna=False)
               .size()
               .reset_index(name="row_count"))
    else:
        agg = (combined
               .groupby(concept_col, dropna=False)
               .size()
               .reset_index(name="row_count"))

    agg = agg.sort_values("row_count", ascending=False).head(top_n)
    agg["pct_of_sampled"] = (100 * agg["row_count"] / total).round(2)

    if value_col and value_col in combined.columns:
        # Attach one example value per concept
        ex = (combined[combined[value_col].notna()]
              .groupby(concept_col)[value_col]
              .first()
              .reset_index()
              .rename(columns={value_col: "example_value"}))
        agg = agg.merge(ex, on=concept_col, how="left")

    return agg.reset_index(drop=True)


def _inspect_single(path: Path, top_n: int, log) -> pd.DataFrame:
    """Print schema + value freq for a single small table (death, person, obs_period)."""
    log(f"\n{'─'*60}")
    log(f"TABLE: {path.name}  ({_row_count(path):,} rows)")
    schema = pq.read_schema(path)
    log(f"  Columns:")
    for field in schema:
        log(f"    {field.name:<45} {field.type}")

    df = pd.read_parquet(path)
    log(f"\n  Null counts:")
    for col in df.columns:
        n_null = df[col].isna().sum()
        pct = 100 * n_null / max(len(df), 1)
        log(f"    {col:<45} {n_null:>10,} null  ({pct:5.1f}%)")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="Inspect OMOP sources for concept mapping")
    ap.add_argument("--omop-dir",     type=Path, required=True,
                    help="Root of OMOP DB, e.g. /mnt/raid0/bb2238/ecg_ascvd/omop_database")
    ap.add_argument("--out-dir",      type=Path, required=True,
                    help="Output directory for inspection CSVs and schema text")
    ap.add_argument("--n-lab-shards", type=int, default=5,
                    help="Number of measurement_labs shards to sample (default 5)")
    ap.add_argument("--n-obs-shards", type=int, default=5,
                    help="Number of observation_icd10 shards to sample (default 5)")
    ap.add_argument("--n-vital-shards", type=int, default=5,
                    help="Number of measurement_vitals shards to sample (default 5)")
    ap.add_argument("--top-n",        type=int, default=100,
                    help="Top-N rows in frequency tables (default 100)")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.out_dir / "schema_summary.txt"
    log_f = open(log_path, "w")

    def log(msg: str = "") -> None:
        print(msg)
        log_f.write(msg + "\n")

    log(f"OMOP Inspection — {args.omop_dir}")
    log(f"Output dir     — {args.out_dir}")
    log()

    # ── 1. measurement_labs ───────────────────────────────────────────────────
    lab_dir = args.omop_dir / "measurement"
    lab_shards = sorted(lab_dir.glob("measurement_labs_*.parquet"))
    vital_shards = sorted(lab_dir.glob("measurement_vitals_*.parquet"))

    if not lab_shards:
        log(f"WARNING: no measurement_labs_*.parquet in {lab_dir}")
    else:
        log(f"\n{'═'*60}")
        log(f"MEASUREMENT LABS  ({len(lab_shards)} shards total)")
        # Schema from first shard
        log(_schema_summary(lab_shards[0]))
        total_rows = sum(_row_count(p) for p in lab_shards)
        log(f"\n  Total rows (all shards): {total_rows:,}")

        sample = _sample_shards(lab_shards, args.n_lab_shards)
        log(f"  Sampling {len(sample)} shards for concept frequency")

        # Detect concept column
        schema_cols = [f.name for f in pq.read_schema(lab_shards[0])]
        concept_col = next(
            (c for c in ["measurement_concept_id", "concept_id"] if c in schema_cols),
            None
        )
        name_col = next(
            (c for c in ["measurement_source_value", "concept_name", "measurement_source_concept_id"]
             if c in schema_cols),
            None
        )
        value_col = next(
            (c for c in ["value_as_number", "value_as_concept_id"] if c in schema_cols),
            None
        )

        log(f"  concept_col={concept_col}  name_col={name_col}  value_col={value_col}")

        if concept_col:
            lab_freq = _concept_freq(sample, concept_col, name_col, value_col, args.top_n)
            out = args.out_dir / "lab_concept_freq.csv"
            lab_freq.to_csv(out, index=False)
            log(f"  → {out}  ({len(lab_freq)} rows)")
            log(f"\n  Top 20 lab concepts:")
            for _, row in lab_freq.head(20).iterrows():
                name = row.get(name_col, "") if name_col else ""
                log(f"    {str(row[concept_col]):<12}  {str(name)[:40]:<42}  {row['row_count']:>10,}  ({row['pct_of_sampled']:.1f}%)")

    # ── 2. measurement_vitals ─────────────────────────────────────────────────
    if not vital_shards:
        log(f"\nWARNING: no measurement_vitals_*.parquet in {lab_dir}")
    else:
        log(f"\n{'═'*60}")
        log(f"MEASUREMENT VITALS  ({len(vital_shards)} shards total)")
        log(_schema_summary(vital_shards[0]))
        total_rows = sum(_row_count(p) for p in vital_shards)
        log(f"\n  Total rows (all shards): {total_rows:,}")

        sample = _sample_shards(vital_shards, args.n_vital_shards)
        log(f"  Sampling {len(sample)} shards for concept frequency")

        schema_cols = [f.name for f in pq.read_schema(vital_shards[0])]
        concept_col = next(
            (c for c in ["measurement_concept_id", "concept_id"] if c in schema_cols), None
        )
        name_col = next(
            (c for c in ["measurement_source_value", "concept_name"] if c in schema_cols), None
        )
        value_col = next(
            (c for c in ["value_as_number"] if c in schema_cols), None
        )

        log(f"  concept_col={concept_col}  name_col={name_col}  value_col={value_col}")

        if concept_col:
            vital_freq = _concept_freq(sample, concept_col, name_col, value_col, args.top_n)
            out = args.out_dir / "vital_concept_freq.csv"
            vital_freq.to_csv(out, index=False)
            log(f"  → {out}  ({len(vital_freq)} rows)")
            log(f"\n  Top 20 vital concepts:")
            for _, row in vital_freq.head(20).iterrows():
                name = row.get(name_col, "") if name_col else ""
                log(f"    {str(row[concept_col]):<12}  {str(name)[:40]:<42}  {row['row_count']:>10,}  ({row['pct_of_sampled']:.1f}%)")

    # ── 3. observation_occurrence (ICD10) ─────────────────────────────────────
    obs_dir = args.omop_dir / "observation_occurrence"
    obs_shards = sorted(obs_dir.glob("observation_icd10_*.parquet"))

    if not obs_shards:
        log(f"\nWARNING: no observation_icd10_*.parquet in {obs_dir}")
    else:
        log(f"\n{'═'*60}")
        log(f"OBSERVATION_OCCURRENCE (ICD10)  ({len(obs_shards)} shards)")
        log(_schema_summary(obs_shards[0]))
        total_rows = sum(_row_count(p) for p in obs_shards)
        log(f"\n  Total rows (all shards): {total_rows:,}")

        sample = _sample_shards(obs_shards, args.n_obs_shards)
        log(f"  Sampling {len(sample)} shards for code frequency")

        schema_cols = [f.name for f in pq.read_schema(obs_shards[0])]
        concept_col = next(
            (c for c in ["observation_source_value", "observation_concept_id",
                          "value_source_value", "condition_source_value"]
             if c in schema_cols),
            None
        )
        name_col = next(
            (c for c in ["value_as_string", "observation_source_concept_id"]
             if c in schema_cols),
            None
        )

        log(f"  concept_col={concept_col}  name_col={name_col}")

        if concept_col:
            obs_freq = _concept_freq(sample, concept_col, name_col, None, args.top_n)
            out = args.out_dir / "observation_code_freq.csv"
            obs_freq.to_csv(out, index=False)
            log(f"  → {out}  ({len(obs_freq)} rows)")
            log(f"\n  Top 30 ICD10 codes:")
            for _, row in obs_freq.head(30).iterrows():
                name = row.get(name_col, "") if name_col else ""
                log(f"    {str(row[concept_col]):<12}  {str(name)[:40]:<42}  {row['row_count']:>10,}")

    # ── 4. observation_period ─────────────────────────────────────────────────
    obs_period_path = args.omop_dir / "observation_period" / "observation_period.parquet"
    if obs_period_path.exists():
        log(f"\n{'═'*60}")
        df = _inspect_single(obs_period_path, args.top_n, log)
        if "observation_period_start_date" in df.columns and "observation_period_end_date" in df.columns:
            log(f"\n  Date ranges:")
            log(f"    start: {df['observation_period_start_date'].min()} → {df['observation_period_start_date'].max()}")
            log(f"    end  : {df['observation_period_end_date'].min()} → {df['observation_period_end_date'].max()}")
        out_txt = args.out_dir / "observation_period_schema.txt"
        out_txt.write_text(f"observation_period rows: {len(df):,}\nColumns: {list(df.columns)}\n")
    else:
        log(f"\nWARNING: {obs_period_path} not found")

    # ── 5. death ─────────────────────────────────────────────────────────────
    death_dir = args.omop_dir / "death"
    death_paths = sorted(death_dir.glob("*.parquet"))
    if not death_paths:
        log(f"\nWARNING: no parquets in {death_dir}")
    else:
        log(f"\n{'═'*60}")
        for dp in death_paths:
            df = _inspect_single(dp, args.top_n, log)
            if "death_date" in df.columns:
                log(f"\n  death_date range: {df['death_date'].min()} → {df['death_date'].max()}")
                log(f"  death_date null : {df['death_date'].isna().sum():,}")
        out_txt = args.out_dir / "death_schema.txt"
        out_txt.write_text("\n".join([f"{p.name}: {_row_count(p):,} rows" for p in death_paths]) + "\n")

    # ── 6. person ─────────────────────────────────────────────────────────────
    person_path = args.omop_dir / "person" / "person.parquet"
    if person_path.exists():
        log(f"\n{'═'*60}")
        df = _inspect_single(person_path, args.top_n, log)
        # Show unique concept counts without patient data
        for col in ["gender_concept_id", "race_concept_id", "ethnicity_concept_id"]:
            if col in df.columns:
                vc = df[col].value_counts()
                log(f"\n  {col} distribution:")
                for val, cnt in vc.head(10).items():
                    log(f"    {val}: {cnt:,}")
        out_txt = args.out_dir / "person_schema.txt"
        out_txt.write_text(f"person rows: {len(df):,}\nColumns: {list(df.columns)}\n")
    else:
        log(f"\nWARNING: {person_path} not found")

    # ── 7. observation (single file) ──────────────────────────────────────────
    obs_path = args.omop_dir / "observation" / "observation.parquet"
    if obs_path.exists():
        log(f"\n{'═'*60}")
        log(f"OBSERVATION (single file)")
        log(_schema_summary(obs_path))
        log(f"  Rows: {_row_count(obs_path):,}")
        schema_cols = [f.name for f in pq.read_schema(obs_path)]
        concept_col = next(
            (c for c in ["observation_concept_id", "observation_source_value"] if c in schema_cols), None
        )
        if concept_col:
            obs_single_freq = _concept_freq([obs_path], concept_col, None, None, 50)
            out = args.out_dir / "observation_single_freq.csv"
            obs_single_freq.to_csv(out, index=False)
            log(f"  → {out}")

    log(f"\n{'═'*60}")
    log(f"Done. All outputs in {args.out_dir}")
    log_f.close()


if __name__ == "__main__":
    main()
