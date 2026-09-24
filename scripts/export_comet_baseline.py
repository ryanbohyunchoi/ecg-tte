"""Export the saved COMET MICE common inputs into the generic baseline-dir format
read by eval_longtail_balance.py (v2): restricted_completed_XX.parquet,
restricted_baseline_observed.parquet (mask True -> NaN) and roles.json.

treated = 1 for metoprolol tartrate (the smaller arm; as in v1). No values change.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

HELDOUT = ["lvef", "sbp", "dbp", "heart_rate", "bmi", "creatinine", "potassium", "sodium", "hemoglobin"]

ap = argparse.ArgumentParser()
ap.add_argument("--common-inputs", required=True)
ap.add_argument("--output-dir", required=True)
a = ap.parse_args()
out = Path(a.output_dir)
out.mkdir(parents=True, exist_ok=False, mode=0o700)
keys = json.load(open(f"{a.common_inputs}/restricted_row_keys.json"))
mask = pd.DataFrame(json.load(open(f"{a.common_inputs}/restricted_missingness_mask.json")), index=keys)
for i in range(1, 6):
    cov = pd.read_csv(f"{a.common_inputs}/restricted_completed_{i:02d}.csv")
    cov.index = keys
    cov["male"] = cov.pop("recorded_sex").astype(str).str.lower().str.startswith("m").astype(float)
    treated = cov.pop("treatment_arm").astype(str).str.contains("metoprolol").astype(int)
    cov = cov.astype(float)
    cols = ["age_at_index", "male"] + [c for c in cov.columns if c not in ("age_at_index", "male")]
    cov = cov[cols]
    cov.insert(0, "treated", treated)
    cov.index.name = "patient_key"
    cov.reset_index().to_parquet(out / f"restricted_completed_{i:02d}.parquet")
    if i == 1:
        o = cov.copy()
        for c in mask.columns:
            if c in o:
                o.loc[mask[c].astype(bool).to_numpy(), c] = float("nan")
        o.reset_index().to_parquet(out / "restricted_baseline_observed.parquet")
core = [c for c in cols]
json.dump(dict(trial="comet", core=core, demo=["age_at_index", "male", "index_year"],
               claims=[c for c in core if c not in HELDOUT], heldout_physiology=HELDOUT,
               report_covariates=["lvef", "atrial_fibrillation", "creatinine", "sbp"], imputations=5,
               exposure_features=["rx_carvedilol", "rx_coreg", "rx_metoprolol", "rx_lopressor", "rx_toprol"]),
          open(out / "roles.json", "w"), indent=2)
print(dict(n=len(keys), treated=int(treated.sum()), mask_cols=list(mask.columns)[:12]))
