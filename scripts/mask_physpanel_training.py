"""Leakage-safe copy of a physiology panel v2 for the SHD arm: echo-derived columns (all domains
except LAB and BNP) are set missing for patients in the PRESENT-SHD training MRNs, so that echo
balance is scored only in patients whose echo labels were never seen by the SHD models. Every arm
is then evaluated on this same masked panel."""
import argparse
import json
from pathlib import Path

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--panel", required=True)
ap.add_argument("--train-mrns", default="/mnt/raid0/rbc58/mosaic/present_shd_train_mrns.txt")
ap.add_argument("--output-dir", required=True)
a = ap.parse_args()
out = Path(a.output_dir)
out.mkdir(parents=True, exist_ok=False, mode=0o700)
digits = lambda s: s.astype(str).str.replace(r"\D", "", regex=True).str.lstrip("0")
P = pd.read_parquet(a.panel).set_index("patient_key")
train = set(digits(pd.read_csv(a.train_mrns, header=None, dtype=str)[0]))
m = digits(pd.Series(P.index, index=P.index)).isin(train).to_numpy()
echo_cols = [c for c in P.columns if c.split("__")[0] not in ("LAB", "BNP")]
P.loc[m, echo_cols] = float("nan")
P.reset_index().to_parquet(out / "restricted_physiology_panel.parquet")
json.dump(dict(n=int(len(P)), masked_share=round(float(m.mean()), 4), masked_columns=len(echo_cols)), open(out / "summary.json", "w"))
print(json.dumps(dict(masked_share=round(float(m.mean()), 4))))
