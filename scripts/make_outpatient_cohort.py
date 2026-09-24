"""Primary-analysis cohort (Ryan, 2026-09-24): restrict a trial cohort to outpatient initiators.

Drops patients whose index order date falls within an inpatient visit (9201,
visit_start_date..visit_end_date, OMOP gold). Output has the same contract as
build_trial_cohort.py (restricted_cohort.parquet, summary.json, attrition.csv, manifest.json)
with one extra attrition step, so MEDS/baseline/evaluation code is unchanged.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import connect, new_private_dir, rp, sha256, suppress, write_manifest  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cohort-dir", required=True)
ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
ap.add_argument("--output-dir", required=True)
a = ap.parse_args()
src = Path(a.cohort_dir)
out = new_private_dir(a.output_dir)
coh = pd.read_parquet(src / "restricted_cohort.parquet")
con = connect(32)
con.register("c", coh[["patient_key", "person_id", "index_date"]])
ip = set(con.execute(f"""SELECT DISTINCT c.patient_key FROM c JOIN {rp(a.omop_dir, 'visit_occurrence')} v
    ON v.person_id = c.person_id AND v.visit_concept_id = 9201
    AND CAST(c.index_date AS DATE) BETWEEN v.visit_start_date AND coalesce(v.visit_end_date, v.visit_start_date)""").df().patient_key)
keep = coh[~coh.patient_key.isin(ip)].copy()
keep.to_parquet(out / "restricted_cohort.parquet")
s = json.load(open(src / "summary.json")) if (src / "summary.json").exists() else {}
arms = list(dict.fromkeys(coh.treatment_arm))
step = dict(step="outpatient_initiation_only", **{arm: suppress((keep.treatment_arm == arm).sum()) for arm in arms})
att = s.get("attrition", []) + [step]
pd.DataFrame(att).to_csv(out / "attrition.csv", index=False)
s.update(n=int(len(keep)), by_arm={k: suppress(v) for k, v in keep.treatment_arm.value_counts().items()},
         attrition=att, spec_version=str(s.get("spec_version", "comet_jdat")) + "+outpatient",
         source_cohort=str(src), excluded_inpatient_initiators=int(len(ip)))
json.dump(s, open(out / "summary.json", "w"), indent=2, default=str)
write_manifest(out, dict(script_sha256=sha256(Path(__file__)), source_cohort=str(src)))
print(json.dumps(step))
