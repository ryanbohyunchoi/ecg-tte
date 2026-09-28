#!/usr/bin/env python
"""Expanded held-out panel (covars2b, non-ECG-proximal, same exclusions as v17_confirm) by clinical bucket,
demographics PS (P1) without vs with ECG (and permuted-ECG placebo, unmatched), 38 trials, full cohort.
Output (aggregate): audits/claude-v19-expanded-buckets/{per_var.csv, per_bucket.csv}."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import sys  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v18"))
sys.path.insert(0, str(HERE.parent / "v17"))
import v18_af_confirm  # noqa: E402,F401  (patches trial list / paths)
import v17_confirm as V  # noqa: E402
E, S6, S8 = V.E, V.S6, V.S8
OUT = V.A / "claude-v19-expanded-buckets"
BUCKET = {"comorbidity": "Comorbidities", "elixhauser": "Comorbidities", "charlson": "Comorbidities",
          "medication": "Medications", "utilisation": "Healthcare use & testing", "lab_vital": "Additional labs & vitals",
          "device_procedure": "Devices & procedures", "score": "Risk & frailty scores", "preventive": "Preventive care"}


def one(n):
    T = E.load_trial(n) if n in V.OLD else E.load_trial(n, cache=False)
    d2 = V.cdirs(n)[1]
    Xe, ovl = V.xpanel(T, d2)
    dom = pd.read_csv(d2 / "dictionary.csv").set_index("variable").domain
    t = T.t
    psn = list(T.demo)
    drop = set(S6.excluded_extra(psn, list(Xe.columns), ovl)) | {c for c in Xe.columns if S8.composite_overlap(c, psn)}
    U = Xe.drop(columns=sorted(drop))
    U = U.loc[:, (U.notna().sum() > 0) & (U.nunique() > 1)]
    U = U[[c for c in U.columns if dom.get(c, "") in BUCKET]]
    XV = U.to_numpy(float)
    X1 = T.cov[T.demo].to_numpy(float)
    arms = {"unmatched": None, "base": X1, "ECG": np.hstack([X1, T.ecg_pc]), "shufECG": np.hstack([X1, T.ecg_pc[T.shuffle_perm]])}
    rows = []
    for a, X in arms.items():
        S8._LAST.clear()
        E.run_cell(T, X, estimator=("match", 0.2, 1))
        s_idx, s_w = (np.arange(len(t)), np.ones(len(t))) if X is None else S8._LAST["m"]
        v = E.smd_components(XV, t, s_idx, s_w, t[s_idx])
        for c, x in zip(U.columns, v):
            if np.isfinite(x):
                rows.append(dict(trial=n, arm=a, var=c, bucket=BUCKET[dom[c]], smd=abs(float(x))))
    print(n, len(U.columns), flush=True)
    return rows


if __name__ == "__main__":
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(19) as p:
        R = pd.DataFrame([r for rs in p.map(one, V.ALL) for r in rs])
    R.to_csv(OUT / "per_var.csv", index=False)
    B = R.groupby(["trial", "arm", "bucket"]).smd.agg(lt01=lambda s: 100 * (s < 0.1).mean(), mean_smd="mean", n_vars="size").reset_index()
    B.to_csv(OUT / "per_bucket.csv", index=False)
    print("done", R.trial.nunique(), "trials")
