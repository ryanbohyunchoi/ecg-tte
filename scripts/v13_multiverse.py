#!/usr/bin/env python
"""v1.3 I6 (+ I5 point estimates): multiverse of analysis choices for one trial.

Full factorial: PS model {l2 C=1, C=0.1, C=100, gbm (5-fold cross-fitted)} x hdPS pool split seed 0-4
x estimator {matching caliper 0.05/0.1/0.2/0.5 x ratio 1:1/1:3, stabilised IPTW (trimmed 1/99%), overlap
weights}. Imputation 1; additionally imputations 1-5 for the base specification (l2 C=1, seed 0,
caliper 0.2, 1:1). Primary outcome at the trial horizon. Aggregate output only.
"""
import os

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import argparse  # noqa: E402
from multiprocessing import Pool  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from v13_common import Trial, cox, match, outcomes, ps_logit, weights  # noqa: E402

ARMS = ["sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "R+",
        "sparse+noise32", "sparse+shufECG", "hdPS200+noise32", "hdPS200+shufECG",
        "sparse+ECG8", "sparse+ECG16", "sparse+ECG64", "sparse+ECGpheno",
        "hdPS200+ECG8", "hdPS200+ECG16", "hdPS200+ECG64", "hdPS200+ECGpheno"]
MODELS = {"l2_C1": ("l2", 1.0), "l2_C0.1": ("l2", 0.1), "l2_C100": ("l2", 100.0), "gbm": ("gbm", None)}
ESTS = [("match", c, r) for c in (0.05, 0.1, 0.2, 0.5) for r in (1, 3)] + [("iptw", None, None), ("overlap", None, None)]
G = {}


def estimate(lg, tr, t, e, ok):
    out = []
    for kind, cal, ratio in ESTS:
        if kind == "match":
            idx, cl, w = match(lg, tr, cal=cal, ratio=ratio)
            m = ok[idx]
            b, se = cox(t[idx][m], e[idx][m], tr[idx][m], w=None if ratio == 1 else w[m], cluster=cl[m])
            lab = f"match_cal{cal}_1to{ratio}"
        else:
            w = weights(lg, tr, kind)
            b, se = cox(t[ok], e[ok], tr[ok], w=w[ok])
            lab = kind
        out.append((lab, b, se))
    return out


def job(args):
    imp, model, seed = args
    n = G["n"]
    T = Trial(n, imputation=imp, split_seed=seed)
    t, e, ok, _, _ = outcomes(n, T.key, T.keys)
    arms = ARMS if imp == 1 else ARMS[:6]
    if seed > 0:  # only hdPS arms and the seeded noise placebo depend on the split seed
        arms = [a for a in arms if a.startswith("hdPS") or "noise" in a]
    X = T.arms(arms)
    kind, C = MODELS[model]
    rows = []
    for a in arms:
        lg = ps_logit(X[a], T.t, model=kind, C=C or 1.0, seed=seed)
        ests = estimate(lg, T.t, t, e, ok) if imp == 1 else [
            ("match_cal0.2_1to1",) + tuple(estimate(lg, T.t, t, e, ok)[4][1:])]
        for lab, b, se in ests:
            rows.append(dict(trial=n, imputation=imp, model=model, seed=seed, estimator=lab, arm=a, loghr=b, se=se))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--output-csv", required=True)
    a = ap.parse_args()
    G["n"] = a.trial
    jobs = [(1, m, s) for m in MODELS for s in range(5)] + [(i, "l2_C1", 0) for i in range(2, 6)]
    with Pool(a.workers) as p:
        res = [r for rr in p.imap_unordered(job, jobs) for r in rr]
    pd.DataFrame(res).to_csv(a.output_csv, index=False)


if __name__ == "__main__":
    main()
