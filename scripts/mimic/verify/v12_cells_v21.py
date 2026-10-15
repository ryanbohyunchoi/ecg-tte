"""Verifier: results/ (new analysis code) base / ECG / permECG cells of the cvd5 bases vs step0 (= v21) cells."""
import json
import numpy as np
import pandas as pd

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
TR8 = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2", "peptic"]
BASES = ["cvd5", "cvd5_anydm", "cvd5_incl"]
worst, rows_ok = 0.0, True
for res in ("results", "results_prior"):
    print(res, "gate_v21.json:", json.load(open(f"{OUT}/{res}/gate_v21.json")))
    for k in TR8:
        for kind, keys, cols in (("arms", ["base", "arm", "pop"], ["n_pairs", "pct_bal", "mean_smd", "loghr", "se"]),
                                 ("vars", ["base", "arm", "pop", "var"], ["abs_smd", "abs_smd_unmatched"])):
            a = pd.read_csv(f"{OUT}/step0/results/{k}_{kind}.csv")
            b = pd.read_csv(f"{OUT}/{res}/{k}_{kind}.csv")
            a = a[a.base.isin(BASES)].set_index(keys).sort_index()
            b = b[b.arm.isin(["base", "ECG", "permECG"])].set_index(keys).sort_index()
            if not a.index.equals(b.index):
                rows_ok = False
                print(k, kind, "row sets differ")
                continue
            x, y = a[cols].to_numpy(float), b[cols].to_numpy(float)
            rows_ok &= bool(np.array_equal(np.isnan(x), np.isnan(y)))
            worst = max(worst, float(np.nanmax(np.abs(x - y))))
    print(res, "vs step0: same rows and NaN pattern", rows_ok, "max |diff|", worst)
