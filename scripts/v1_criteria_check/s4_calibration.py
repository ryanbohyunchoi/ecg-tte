#!/usr/bin/env python
"""Step 4: random-removal calibration for the per-trial impact of each exclusion fix.

For every exclusion variant in s3_reanalysis.FIX, remove the same number of patients per arm at random (30 seeded
replicates; numpy default_rng(20261008 + replicate)) and recompute the P1 base / P1 + ECG main-configuration cells
exactly as in s3 (E.run_cell, row subset, T.ecg_pc kept). The observed change (fix minus unchanged) in mean |SMD|
(58 items) and |Δ log HR| is compared with the 5th-95th percentile of the random-removal changes: a change inside
that range is indistinguishable from rematching noise of removing that many patients.
Output: OUT/calibration.csv (aggregate)."""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import sys  # noqa: E402
from multiprocessing import Pool  # noqa: E402

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v1_criteria_check")
import s3_reanalysis as S3  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

K, E, AF, SP = S3.K, S3.E, S3.AF, S3.SP
NREP = 30


def metrics(cl):
    C = pd.DataFrame(cl)
    o = {}
    for a in ("base", "ECG"):
        F, _ = SP.per_trial(C[C.arm == a].set_index("trial", drop=False))
        o[f"m58_{a}"], o[f"absd_{a}"] = F.m58.iloc[0], F.absd.iloc[0]
    return o


def task(n):
    K.umask()
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    F = pd.read_parquet(K.OUT / "flags" / f"restricted_flags_{n}.parquet").set_index("patient_key")
    assert F.index.equals(T.keys)
    base = metrics(S3.cells(T, n, None, "unchanged"))
    out = []
    for v, flags in S3.FIX[n].items():
        drop = F[flags].any(axis=1).to_numpy()
        obs = metrics(S3.cells(T, n, np.where(~drop)[0], v))
        it, ic = np.where(T.t == 1)[0], np.where(T.t == 0)[0]
        kt, kc = int(drop[T.t == 1].sum()), int(drop[T.t == 0].sum())
        reps = []
        for b in range(NREP):
            rng = np.random.default_rng(20261008 + b)
            d = np.zeros(len(T.t), bool)
            d[rng.choice(it, kt, replace=False)] = True
            d[rng.choice(ic, kc, replace=False)] = True
            reps.append(metrics(S3.cells(T, n, np.where(~d)[0], f"rand{b}")))
        Rp = pd.DataFrame(reps)
        for m in ("m58_base", "m58_ECG", "absd_base", "absd_ECG"):
            ch = Rp[m] - base[m]
            lo, hi = np.percentile(ch, [5, 95])
            dv = obs[m] - base[m]
            out.append(dict(trial=n, label=K.FLAGGED[n], variant=v, metric=m, unchanged=base[m], fixed=obs[m], change=dv,
                            rand_p05=lo, rand_p95=hi, outside_random_90=bool(dv < lo or dv > hi)))
    print(n, "done", flush=True)
    return out


if __name__ == "__main__":
    K.umask()
    with Pool(12) as p:
        res = p.map(task, list(S3.FIX), chunksize=1)
    D = pd.DataFrame([x for r in res for x in r])
    D.to_csv(K.OUT / "calibration.csv", index=False)
    pd.set_option("display.width", 250)
    print(D.round(4).to_string(index=False))
