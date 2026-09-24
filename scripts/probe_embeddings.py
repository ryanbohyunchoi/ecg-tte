"""Probe gate + anisotropy for a trial's ECG and CLMBR embeddings (aggregate JSON)."""
import argparse
import json

import pandas as pd

import embedding_utils as U
import eval_longtail_balance as E

ap = argparse.ArgumentParser()
ap.add_argument("--baseline-observed", required=True)
ap.add_argument("--ecg-glob", required=True)
ap.add_argument("--ehr-glob", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
obs = pd.read_parquet(a.baseline_observed).set_index("patient_key")
lab = U.labels_from_covariates(obs.rename(columns={"male": "sex_binary"}))
res = {}
for nm, g, mod in (("ecg", a.ecg_glob, "ecg"), ("clmbr", a.ehr_glob, "ehr")):
    X = E.emb(g)
    r = U.probe_gate(X.to_numpy(float), lab.loc[X.index], mod)
    an = U.anisotropy_report(X.to_numpy(float))
    res[nm] = dict(n=len(X), mean_unit_norm=round(an["mean_unit_norm"], 3), gate=r.to_dict("records"))
json.dump(res, open(a.out, "w"), indent=1, default=str)
print(json.dumps({k: [(g["label"], g["auc"]) for g in v["gate"]] for k, v in res.items()}))
