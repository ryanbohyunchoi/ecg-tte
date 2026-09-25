#!/usr/bin/env python
"""v1.3 I3/I4/I5: within-trial paired bootstrap of every arm (docs/PROTOCOL_V1_3_AMENDMENT.md).

Replicate 0 = the full cohort (point estimate); replicates 1..B resample patients with replacement.
Every replicate refits hdPS ranking, PS and matching for every arm, then the pair-clustered Cox model
(primary outcome, trial horizon). Imputation 1, pool split seed 0. Output: aggregate CSV of
(rep, arm, loghr, se, pairs). No patient-level output.
"""
import os

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
from multiprocessing import Pool  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from v13_common import Trial, cox, match, outcomes, ps_logit  # noqa: E402

ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "R+",
        "sparse+noise32", "sparse+shufECG", "hdPS200+noise32", "hdPS200+shufECG",
        "sparse+ECG8", "sparse+ECG16", "sparse+ECG64", "sparse+ECGpheno",
        "hdPS200+ECG8", "hdPS200+ECG16", "hdPS200+ECG64", "hdPS200+ECGpheno"]
G = {}


def one(rep):
    T, tt, ee, ok, arms = G["T"], G["t"], G["e"], G["ok"], G["arms"]
    N = len(T.t)
    rows = np.arange(N) if rep == 0 else np.random.default_rng(10_000 + rep).integers(0, N, N)
    t = T.t[rows]
    X = T.arms(arms, rows=rows)
    out = []
    for a in arms:
        if X[a] is None:
            m = ok[rows]
            b, se = cox(tt[rows][m], ee[rows][m], t[m])
            out.append(dict(rep=rep, arm=a, loghr=b, se=se, pairs=np.nan))
            continue
        lg = ps_logit(X[a], t)
        idx, cl, w = match(lg, t)
        m = ok[rows][idx]
        b, se = cox(tt[rows][idx][m], ee[rows][idx][m], t[idx][m], cluster=cl[m])
        out.append(dict(rep=rep, arm=a, loghr=b, se=se, pairs=len(idx) // 2))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--with-shd", action="store_true")
    ap.add_argument("--enc2", default=None, help="parquet patient_key + embedding (second ECG encoder)")
    ap.add_argument("--output-csv", required=True)
    a = ap.parse_args()
    T = Trial(a.trial, with_shd=a.with_shd)
    if a.enc2:
        from eval_longtail_balance import emb, pcs
        E2 = emb(a.enc2).reindex(T.keys)
        assert E2.notna().all().all(), "enc2 missing for cohort patients"
        T.enc2 = pcs(E2.to_numpy(float), 32)
    t, e, ok, H, _ = outcomes(a.trial, T.key, T.keys)
    G.update(T=T, t=t, e=e, ok=ok, arms=a.arms.split(","))
    with Pool(a.workers) as p:
        res = [r for rr in p.imap_unordered(one, range(a.reps + 1)) for r in rr]
    df = pd.DataFrame(res).sort_values(["rep", "arm"])
    df.insert(0, "trial", a.trial)
    df.to_csv(a.output_csv, index=False)
    print(json.dumps(dict(trial=a.trial, reps=a.reps, n=len(T.t), horizon_days=H)))


if __name__ == "__main__":
    main()
