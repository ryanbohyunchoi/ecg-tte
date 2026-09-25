"""Sensitivity cohort (v1.1): restrict a trial cohort to index dates on/after --start (default
2016-07-31, when the echo sources first cover the full 365-day pre-index window). Same output
contract as build_trial_cohort.py, with one extra attrition step."""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import new_private_dir, sha256, suppress, write_manifest  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cohort-dir", required=True)
ap.add_argument("--start", default="2016-07-31")
ap.add_argument("--output-dir", required=True)
a = ap.parse_args()
src = Path(a.cohort_dir)
out = new_private_dir(a.output_dir)
coh = pd.read_parquet(src / "restricted_cohort.parquet")
keep = coh[pd.to_datetime(coh.index_date) >= pd.Timestamp(a.start)].copy()
keep.to_parquet(out / "restricted_cohort.parquet")
s = json.load(open(src / "summary.json")) if (src / "summary.json").exists() else {}
step = dict(step=f"index_on_or_after_{a.start}", **{arm: suppress((keep.treatment_arm == arm).sum()) for arm in dict.fromkeys(coh.treatment_arm)})
s.update(n=int(len(keep)), by_arm={k: suppress(v) for k, v in keep.treatment_arm.value_counts().items()},
         attrition=s.get("attrition", []) + [step], source_cohort=str(src))
json.dump(s, open(out / "summary.json", "w"), indent=2, default=str)
pd.DataFrame(s["attrition"]).to_csv(out / "attrition.csv", index=False)
write_manifest(out, dict(script_sha256=sha256(Path(__file__)), source_cohort=str(src)))
print(json.dumps(step))
