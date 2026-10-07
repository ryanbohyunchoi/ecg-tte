#!/usr/bin/env python
"""paper2 PS-Flags source panels (HANDOFF_PAPER2.md §1.5, §4 "PS-Flags source").

Reuses the diagnosis query of scripts/build_preindex_panel.py (that script cannot be imported: its query builder is a
closure inside main(), and run as-is it also builds rx / px / lab / visit features over the full history, which paper2
does not use). The dx logic is copied verbatim:
  window   t.condition_start_date >= idx - INTERVAL L DAY AND t.condition_start_date < idx   (index day excluded)
  feature  'dx_' || upper(substr(replace(condition_source_value, '.', ''), 1, 3))           (ICD-10 3-character)
  value    count(DISTINCT condition_start_date) per patient x feature
  roster   person_id taken directly from the roster (all 38 rosters carry person_id)
with L = 36500 days (full pre-index history; HANDOFF §4: --lookback-days 36500 --min-prevalence 0.01).

Roster = the cohort file v13_common.Trial reads for the index date ({A}/{cdir}/restricted_cohort.parquet, cdir from
v13_common.PRIMARY / EXTRA). This step writes counts for every code with roster prevalence >= 0.1 % (a storage bound
only). The analysis design (paper2_grid.flags_matrix) reindexes to T.keys (load_trial cohort), binarises (count > 0),
drops roles["exposure_features"] and keeps codes with prevalence >= 1 % in T.keys; only codes matching the ICD-10
3-character pattern [A-Z][0-9][0-9A-Z] are kept.

Usage: ps_flags.py build [--threads 16]  -> OUT/flags/restricted_flags_<trial>.parquet, OUT/flags/flags_build.csv (aggregates)
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from v13_common import A, EXTRA, PRIMARY  # noqa: E402

GOLD = "/mnt/raid0/rbc58/omop/gold"
LOOKBACK = 36500
STORE_MIN_PREV = 0.001
OUT = A / "claude-v21-paper2" / "core" / "flags"
ICD10_3 = r"^dx_[A-Z][0-9][0-9A-Z]$"


def trials():
    sys.path.insert(0, str(HERE.parent / "v20"))
    import sens_primary32 as SP
    return list(SP.ALL)


def roster(n):
    cdir = {**PRIMARY, **EXTRA}[n][1]
    ro = pd.read_parquet(A / cdir / "restricted_cohort.parquet", columns=["patient_key", "person_id", "index_date"])
    return ro.drop_duplicates("patient_key"), cdir


def build(threads, only=None):
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    g = glob.glob(f"{GOLD}/condition_occurrence/**/*.parquet", recursive=True)
    con = duckdb.connect()
    con.execute(f"SET threads={threads}")
    rows = []
    for n in (only or trials()):
        t0 = time.time()
        coh, cdir = roster(n)
        con.register("coh_df", coh)
        con.execute("CREATE OR REPLACE TABLE pmap AS SELECT patient_key, CAST(index_date AS DATE) AS idx, "
                    "CAST(person_id AS BIGINT) person_id FROM coh_df")
        npat = con.execute("SELECT count(DISTINCT patient_key) FROM pmap").fetchone()[0]
        q = f"""SELECT m.patient_key, m.idx, t.condition_start_date AS day,
                       'dx_' || upper(substr(replace(condition_source_value, '.', ''), 1, 3)) AS f
                FROM read_parquet({g}, hive_partitioning=true) t JOIN pmap m USING (person_id)
                WHERE t.condition_start_date >= m.idx - INTERVAL {LOOKBACK} DAY AND t.condition_start_date < m.idx"""
        con.execute(f"""CREATE OR REPLACE TABLE x AS SELECT patient_key, f, count(DISTINCT day) AS c,
                               min(date_diff('day', day, idx)) AS lo, max(date_diff('day', day, idx)) AS hi
                        FROM ({q}) WHERE f IS NOT NULL GROUP BY 1, 2""")
        d = con.execute(f"""SELECT patient_key, f, c FROM x WHERE f IN (SELECT f FROM x GROUP BY f
                            HAVING count(DISTINCT patient_key) >= {STORE_MIN_PREV * npat})""").df()
        w = con.execute("SELECT max(hi), min(lo) FROM x").fetchone()
        span = con.execute("SELECT median(h) FROM (SELECT patient_key, max(hi) h FROM x GROUP BY 1)").fetchone()[0]
        W = d.pivot(index="patient_key", columns="f", values="c").reindex(coh.patient_key.unique()).fillna(0).astype("uint16")
        n_nonicd = int((~W.columns.str.match(ICD10_3)).sum())
        W.index.name = "patient_key"
        W.reset_index().to_parquet(OUT / f"restricted_flags_{n}.parquet")
        prev = (W > 0).mean()
        n_nodx = int((~(W > 0).any(axis=1)).sum())  # suppress the any-dx percentage if 1-10 patients have no dx (B1)
        rows.append(dict(trial=n, roster_dir=cdir, roster_n=len(coh), linked_n=int(npat), lookback_days=LOOKBACK,
                         n_codes_stored=W.shape[1], n_codes_roster_ge1pct=int((prev >= 0.01).sum()),
                         n_codes_not_icd10_3char=n_nonicd, pct_with_any_dx=(round(100 * float((W > 0).any(axis=1).mean()), 2) if not (1 <= n_nodx < 11) else None),
                         min_days_before_index=int(w[1]), max_days_before_index=int(w[0]), median_history_days=float(span),
                         secs=round(time.time() - t0, 1)))
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(OUT / ("flags_build.csv" if not only else "flags_build_partial.csv"), index=False)
    print("done", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--trials", default="")
    a = ap.parse_args()
    build(a.threads, [x for x in a.trials.split(",") if x] or None)
