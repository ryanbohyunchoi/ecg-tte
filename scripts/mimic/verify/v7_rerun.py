"""Verifier check 7: independent re-run of the new CLMBR-T glue for a few trials (cvd5 | all): own embedding join by
(trial, pid), own 64-PC PCA (sklearn), own ridge PS (sklearn, C=1, standardised), the shared greedy matcher
(v13_common.match, already validated by the Step 0 reproduction), own |SMD|. Compares aggregate cell values
(mean |SMD|, % < 0.1, log HR) with results/<k>_arms.csv. Prints only |differences| and match flags."""
import glob
import json
import os
import sys

if "--single-thread" in sys.argv:  # the code under test sets these to 1 (mimic_common)
    for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[_v] = "1"

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

S = "/home/rbc58/github/ecg-tte/scripts"
for p in (f"{S}/v21", f"{S}/v20", f"{S}/v15", S):
    sys.path.insert(0, p)
import mimic_replication as M  # noqa: E402
import mimic_cvd5 as C5  # noqa: E402
import v15_analyze as VA  # noqa: E402
from v13_common import match, cox  # noqa: E402

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"


def smd(v, t, mt, mc):
    a, b = v[t == 1], v[t == 0]
    sd = np.sqrt((np.nanvar(a, 0, ddof=1) + np.nanvar(b, 0, ddof=1)) / 2)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.abs(np.nanmean(v[mt], 0) - np.nanmean(v[mc], 0)) / sd
    d[~np.isfinite(sd) | (sd == 0)] = np.nan
    return d


def logit(X, t):
    p = LogisticRegression(C=1.0, max_iter=5000).fit(StandardScaler().fit_transform(X), t).predict_proba(StandardScaler().fit_transform(X))[:, 1]
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def emb(run, k, pids):
    E = pd.concat([pd.read_parquet(f, columns=["trial", "pid", "embedding"]) for f in sorted(glob.glob(f"{OUT}/clmbr/{run}/restricted_embeddings_part-*.parquet"))])
    E = E[E.trial == k].set_index("pid")
    assert E.index.is_unique
    return np.stack(E.loc[pd.Index(pids).astype(str)].embedding.to_numpy()).astype(float)


SVD = "--svd" in sys.argv
RUNS = (("prior_full", "results_prior"),) if "--prior-only" in sys.argv else (("full", "results"), ("prior_full", "results_prior"))
for run, res in RUNS:
    for k in [a for a in sys.argv[1:] if not a.startswith("--")]:
        D = VA.TrialData(M.tdir(k))
        F = pd.read_parquet(f"{OUT}/step0/flags/{k}.parquet").set_index("pid").reindex(D.pids)
        Cr = F[C5.CVD5["cvd5"]].to_numpy(float)
        Cr = Cr[:, Cr.std(0) > 0]
        E0 = emb(run, k, D.pids)
        if SVD:  # plain numpy SVD on the centred matrix (own code; the same algorithm family as the code under test)
            U, Sv, _ = np.linalg.svd(E0 - E0.mean(0), full_matrices=False)
            Z = U[:, :64] * Sv[:64]
            print(f"{run} {k}: singular value ratio PC64/PC65 {Sv[63] / Sv[64]:.6f}")
        else:
            Z = PCA(64, svd_solver="full").fit_transform(E0)
        perm = np.random.default_rng(20261001).permutation(len(D.t))
        V, cols, blk, _, _ = M.panel_for(D, k, "demo")
        t = D.t
        R = pd.read_csv(f"{OUT}/{res}/{k}_arms.csv")
        R = R[(R.base == "cvd5") & (R["pop"] == "all")].set_index("arm")
        for arm, extra in (("CLMBR", [Z]), ("ECG+CLMBR", [D.ecg_pc, Z]), ("permCLMBR", [Z[perm]])):
            X = np.hstack([D.Gm["demo"], Cr] + extra)
            lg = logit(X, t)
            idx, cl, _ = match(lg, t)
            mt, mc = idx[t[idx] == 1], idx[t[idx] == 0]
            s = smd(V, t, mt, mc)
            ok = np.isfinite(s)
            b, se = cox(D.T[idx], D.E[idx].astype(int), t[idx], cluster=cl)
            r = R.loc[arm]
            print(f"{run} {k} {arm}: n_inputs equal {X.shape[1] == r.n_inputs}; same n_pairs {len(idx) // 2 == r.n_pairs}; "
                  f"|d mean_smd| {abs(np.mean(s[ok]) - r.mean_smd):.2e}; |d pct_bal| {abs(100 * np.mean(s[ok] < .1) - r.pct_bal):.2e}; "
                  f"|d loghr| {abs(b - r.loghr):.2e}", flush=True)
