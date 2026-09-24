"""Shared helpers for the multi-trial pipeline (DuckDB over OMOP gold parquet).

No patient-level data is printed by anything here. Callers write restricted
outputs into private (umask 077) run directories.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import duckdb

MIN_CELL = 11


def connect(threads: int = 32, memory_limit: str | None = "200GB") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"SET threads={threads}")
    if memory_limit:
        con.execute(f"SET memory_limit='{memory_limit}'")
    con.execute("SET preserve_insertion_order=false")
    return con


def rp(gold: str, table: str) -> str:
    """read_parquet expression for a gold table (hive-partitioned or flat)."""
    return f"read_parquet('{gold.rstrip('/')}/{table}/**/*.parquet', hive_partitioning=1, union_by_name=1)"


def mrn_key(col: str) -> str:
    """Digits only, leading zeros stripped; empty -> NULL (ECG/echo metadata linkage)."""
    return f"nullif(ltrim(regexp_replace(CAST({col} AS VARCHAR), '[^0-9]', '', 'g'), '0'), '')"


def sql_list(values) -> str:
    return ",".join("'" + str(v).replace("'", "''") + "'" for v in values)


def code_like(col: str, prefixes) -> str:
    return "(" + " OR ".join(f"{col} LIKE '{p}%'" for p in prefixes) + ")"


def create_drug_tokens(con, gold: str, keywords, table: str = "dtok", person_filter: str | None = None):
    """Distinct (person_id, date, token) for drug orders whose '-'-split lowercase
    drug_source_value contains one of `keywords`."""
    kw = sql_list(sorted({k.lower() for k in keywords}))
    pf = f"AND person_id IN (SELECT person_id FROM {person_filter})" if person_filter else ""
    con.execute(f"""CREATE OR REPLACE TEMP TABLE {table} AS
        SELECT DISTINCT person_id, d, tok FROM (
            SELECT person_id, drug_exposure_start_date d,
                   unnest(string_split(lower(drug_source_value), '-')) tok
            FROM {rp(gold, 'drug_exposure')}
            WHERE drug_source_value IS NOT NULL AND drug_exposure_start_date IS NOT NULL {pf})
        WHERE tok IN ({kw})""")


def suppress(n: int, min_cell: int = MIN_CELL):
    n = int(n)
    return n if (n == 0 or n >= min_cell) else f"<{min_cell}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def new_private_dir(path: str | Path) -> Path:
    """Create a fresh private directory; refuse to reuse an existing run."""
    os.umask(0o077)
    p = Path(path)
    p.mkdir(parents=True, exist_ok=False, mode=0o700)
    return p


def write_manifest(out: Path, extra: dict) -> None:
    outputs = {f.name: sha256(f) for f in sorted(out.iterdir()) if f.is_file() and f.name != "manifest.json"}
    json.dump(dict(outputs=outputs, **extra), open(out / "manifest.json", "w"), indent=2, default=str)
