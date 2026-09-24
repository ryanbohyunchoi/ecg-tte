"""Sensitivity: restrict a baseline dir to outpatient initiators.

Keeps patients whose index date does not fall within an inpatient visit (9201,
visit_start_date..visit_end_date) in OMOP gold. Writes a new baseline dir with the same
files (completed imputations, observed table, roles.json) for eval_longtail_balance.py.
Imputed values are reused as is (not refitted in the subset).
"""
import argparse
import json
import shutil
from pathlib import Path

import duckdb
import pandas as pd

from trial_common import rp

ap = argparse.ArgumentParser()
ap.add_argument("--baseline-dir", required=True)
ap.add_argument("--cohort", required=True, help="parquet with patient_key, person_id, index_date")
ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
ap.add_argument("--output-dir", required=True)
a = ap.parse_args()
out = Path(a.output_dir)
out.mkdir(parents=True, exist_ok=False, mode=0o700)
con = duckdb.connect()
con.execute("SET threads=32")
con.register("c", pd.read_parquet(a.cohort)[["patient_key", "person_id", "index_date"]])
ip = con.execute(f"""SELECT DISTINCT c.patient_key FROM c JOIN {rp(a.omop_dir, 'visit_occurrence')} v
    ON v.person_id = c.person_id AND v.visit_concept_id = 9201
    AND CAST(c.index_date AS DATE) BETWEEN v.visit_start_date AND coalesce(v.visit_end_date, v.visit_start_date)""").df()
drop = set(ip.patient_key)
B = Path(a.baseline_dir)
counts = {}
for f in sorted(B.glob("restricted_*.parquet")):
    d = pd.read_parquet(f)
    d = d[~d.patient_key.isin(drop)]
    d.to_parquet(out / f.name)
    counts = d.treated.value_counts().to_dict()
shutil.copy(B / "roles.json", out / "roles.json")
json.dump(dict(source=str(B), excluded_inpatient_initiators=len(drop), remaining_by_treated={str(k): int(v) for k, v in counts.items()}),
          open(out / "summary.json", "w"), indent=2)
print(json.dumps(dict(excluded=len(drop), remaining=counts)))
