#!/usr/bin/env python
"""Expanded held-out panel (covars2b, non-ECG-proximal, v18_embed_compare exclusions per PS rung incl. hdPS overlap),
per-variable |SMD| for every PS rung x arm (base, ECG, CLMBR, CLMBR+ECG, shufECG, shufCLMBR, noise96) + unmatched,
38 trials, full cohort. Same designs/matching as v18_embed_compare (verified: 58-panel mean_smd reproduces).
Output (aggregate): audits/claude-v19-expanded-buckets/per_var_all_rungs.csv"""
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
import v18_embed_compare as M  # noqa: E402
E, S6, S8, V, C = M.E, M.S6, M.S8, M.V, M.C
from expanded_buckets import BUCKET  # noqa: E402
OUT = V.A / "claude-v19-expanded-buckets"


def one(n):
    i = M.ALL.index(n)
    T = E.load_trial(n) if n in M.OLD else E.load_trial(n, cache=False)
    b5, psn5, _ = C.designs(T, n, C.P5DX)
    b2, psn2, _ = C.designs(T, n, C.P2DX)
    d2 = V.cdirs(n)[1]
    Xe, ovl = V.xpanel(T, d2)
    hk = S6.HDPS_KEYS.get((T.n, str(d2)), {})
    dom = pd.read_csv(d2 / "dictionary.csv").set_index("variable").domain
    r = M.halves(T, i)["full"]
    t = T.t[r]
    X1 = T.cov.iloc[r][T.demo].to_numpy(float)
    dx = T.X_dx[r]
    Hk = T.hd(200, t=t, rows=r)
    sel = S6.hdps_selected(T, r, t, 200)
    xdrop_hd = {c for c in Xe.columns if S6.hdps_overlap(hk.get(c, set()), sel)}
    dxn = list(T.demo) + list(T.dxc)
    rung = {"P1": (X1, list(T.demo), set()), "P5": (b5[r], psn5, set()), "P2": (b2[r], psn2, set()),
            "sparse": (dx, dxn, set()), "hdPS200": (np.hstack([dx, Hk]), dxn, xdrop_hd), "clinical": (T.X_core[r], list(T.core), set())}
    CL = T.clm_pc
    nz96 = np.random.default_rng(M.NOISE96_SEED0 + i).normal(size=(len(T.t), 96))
    blk = {"clm": CL[r], "shc": CL[T.shuffle_perm][r], "ecg": T.ecg_pc[r], "she": T.ecg_pc[T.shuffle_perm][r], "nz96": nz96[r]}
    rows = []

    def panel(psn, extra):
        drop = set(S6.excluded_extra(psn, list(Xe.columns), ovl)) | {c for c in Xe.columns if S8.composite_overlap(c, psn)} | set(extra)
        U = Xe.drop(columns=sorted(drop)).iloc[r]
        U = U.loc[:, (U.notna().sum() > 0) & (U.nunique() > 1)]
        return U[[c for c in U.columns if dom.get(c, "") in BUCKET]]

    def emit(rg, role, X, U, chk=None):
        S8._LAST.clear()
        o = E.run_cell(T, X, rows=r, estimator=("match", 0.2, 1))
        if chk is not None:
            assert abs(o["mean_smd"] - chk) < 1e-9, (n, rg, role, o["mean_smd"], chk)
        s_idx, s_w = (np.arange(len(t)), np.ones(len(t))) if X is None else S8._LAST["m"]
        v = E.smd_components(U.to_numpy(float), t, s_idx, s_w, t[s_idx])
        for c, x in zip(U.columns, v):
            if np.isfinite(x):
                rows.append(dict(trial=n, rung=rg, arm=role, var=c, bucket=BUCKET[dom[c]], smd=abs(float(x))))

    ref = pd.read_csv(OUT.parent / "claude-v18-embed-compare/results.csv", usecols=["trial", "half", "rung", "arm_role", "mean_smd"])
    ref = ref[(ref.trial == n) & (ref.half == "full")].set_index(["rung", "arm_role"]).mean_smd
    emit("none", "unmatched", None, panel([], set()), ref.get(("none", "unmatched")))
    for rg, (X, psn, xdh) in rung.items():
        U = panel(psn, xdh)
        for role in M.ARMS:
            emit(rg, role, np.hstack([X] + [blk[b] for b in M.COMP[role]]), U, ref.get((rg, role)))
    print(n, flush=True)
    return rows


if __name__ == "__main__":
    os.umask(0o077)
    with Pool(20) as p:
        R = pd.DataFrame([x for rs in p.map(one, M.ALL) for x in rs])
    R.to_csv(OUT / "per_var_all_rungs.csv", index=False)
    print("done", R.trial.nunique(), R.rung.nunique(), R.arm.nunique(), len(R))
