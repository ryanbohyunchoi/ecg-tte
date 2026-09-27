#!/usr/bin/env python
"""S10 (post hoc, PI request 2026-09-27): PS = demographics (age, sex, index year) + HTN, T2D, CAD, AF, obesity, HF (hf_any_365; Elixhauser CHF where hf_any_365 was dropped for <1% prevalence),
with vs without ECG32 (+ shufECG, noise32 placebos), caliper 0.2 and 0.1, 18 trials, halves full/A/B.
Held-out balance: 58-panel (BMI reported both in and out, since obesity is in the PS). Aggregates only.
"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import sys  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v16_engine as E  # noqa: E402
from s1_ladder import halves  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = A / "claude-v16-s10-demo6"


def one(i):
    n = E.TRIALS[i]
    T = E.load_trial(n)
    C1 = pd.read_parquet(A / "claude-v16-covars" / f"{n}.parquet").set_index("patient_key").reindex(T.keys)
    C2 = pd.read_parquet(A / "claude-v16-covars2b" / f"{n}.parquet").set_index("patient_key").reindex(T.keys)
    base = np.column_stack([T.cov[T.demo].to_numpy(float), C1[["hypertension_v11", "t2d", "cad_ihd", "obesity"]].to_numpy(float),
                            T.cov["atrial_fibrillation"].to_numpy(float), (C2["hf_any_365"] if "hf_any_365" in C2 else C2["elx_chf"]).to_numpy(float)])
    base = np.nan_to_num(base)
    arms = {"base": base, "ECG": np.hstack([base, T.ecg_pc]), "shufECG": np.hstack([base, T.ecg_pc[T.shuffle_perm]]),
            "noise": np.hstack([base, T.noise32])}
    rows = []
    for h, r in halves(T, i).items():
        for cal in (0.2, 0.1):
            for role, X in [("unmatched", None)] + list(arms.items()):
                if role == "unmatched" and cal == 0.1:
                    continue
                o = E.run_cell(T, None if X is None else X[r], rows=r, estimator=("match", cal, 1))
                rows.append(dict(trial=n, half=h, caliper=cal, arm_role=role, rb=T.rb, rs=T.rs, **o))
    return rows


if __name__ == "__main__":
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(18) as p:
        R = [x for rs in p.map(one, range(len(E.TRIALS))) for x in rs]
    pd.DataFrame(R).to_csv(OUT / "results.csv", index=False)
    print("done", len(R))
