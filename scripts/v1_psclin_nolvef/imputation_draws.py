#!/usr/bin/env python
"""Imputation-draw sensitivity for PS-Clinical with and without LVEF (main configuration only).

The baseline imputation is stochastic (IterativeImputer(sample_posterior=True)); the version 1 grid uses draw 1. This
re-runs the main-configuration cells (1:1, caliper 0.2, L2 C = 1) for draws 1-5:
  clinical#k         with LVEF: the existing restricted_completed_0k tables (build_core_baseline.impute, seed 20260923 + k - 1)
  clinical_nolvef#k  without LVEF: build_core_baseline.impute(obs without lvef, treated, m=5), same seeds (draw 1 = primary)
Arms base, ECG, shufECG, CLMBR, ECG+CLMBR. Summary: relative reduction in mean |SMD| (54 items, leakage-clean masks of
psclin_nolvef.py, F1 rule) per draw, and on per-trial |SMD| averaged over the 5 draws.
Usage: imputation_draws.py run [--workers 24] ; imputation_draws.py summarize
Outputs: audits/claude-v1-psclin-nolvef/impdraws/ (restricted cells parquet; aggregate csv)."""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psclin_nolvef as M  # noqa: E402

P2, SP, E, A = M.P2, M.SP, M.E, M.A
OUT = M.OUT / "impdraws"
K = 5
ARMS = ["base", "ECG", "shufECG", "CLMBR", "ECG+CLMBR"]


def task(n):
    from build_core_baseline import impute
    t0 = time.time()
    T = E.load_trial(n) if n in M.AF.V.OLD else E.load_trial(n, cache=False)
    t, r = T.t, np.arange(len(T.t))
    B = A / f"claude-{n}-baseline-v11"
    obs = pd.read_parquet(B / "restricted_baseline_observed.parquet").set_index("patient_key")
    tr = obs.pop("treated").to_numpy()
    Z0 = impute(obs.drop(columns=["lvef"]), tr, K)
    cols, cols_nl = list(T.cov.columns), [c for c in T.cov.columns if c != "lvef"]
    prim = pd.read_parquet(M.imp_path(n)).set_index("patient_key").loc[T.keys, cols_nl].to_numpy(float)
    assert np.array_equal(Z0[0].loc[T.keys, cols_nl].to_numpy(float), prim)  # draw 1 = primary table
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    nl_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys if c != "lvef"}
    perm, CLM = T.shuffle_perm, T.clm_pc
    blk = {"ECG": [T.ecg_pc], "shufECG": [T.ecg_pc[perm]], "CLMBR": [CLM[r]], "ECG+CLMBR": [CLM[r], T.ecg_pc], "base": []}
    est, psm = M.CONFIGS["main"]
    out = []
    for k in range(1, K + 1):
        Wk = pd.read_parquet(B / f"restricted_completed_{k:02d}.parquet").set_index("patient_key").loc[T.keys, cols].astype(float).to_numpy()
        if k == 1:
            assert np.array_equal(Wk, T.X_core)
        des = {f"clinical#{k}": (Wk, clin_ex), f"clinical_nolvef#{k}": (Z0[k - 1].loc[T.keys, cols_nl].astype(float).to_numpy(), nl_ex)}
        for rg, (X, ex) in des.items():
            for a in ARMS:
                o = E.run_cell(T, np.hstack([X[r]] + blk[a]), rows=r, estimator=est, ps_model=psm, cstat=None)
                out.append(dict(trial=n, rung=rg, draw=k, base_rung=rg.split("#")[0], config="main", arm=a, ex58=";".join(sorted(ex)),
                                cell_failed="", rb=T.rb, rs=T.rs, **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se")},
                                retain=np.nan, **{f"smd:{c}": o[f"smd:{c}"] for c in M.VN}))
    print(f"{n} {time.time() - t0:.0f}s", flush=True)
    return out


def run(workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle")
    tk = sorted(M.ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    with Pool(min(workers, len(tk))) as p:
        res = p.map(task, tk, chunksize=1)
    R = pd.DataFrame([x for o in res for x in o])
    R.to_parquet(OUT / "restricted_cells.parquet")
    print("done", flush=True)


def summarize():
    os.umask(0o077)
    R = pd.read_parquet(OUT / "restricted_cells.parquet")
    # gate: draw 1 equals the main grid cells of psclin_nolvef.py
    G = pd.read_parquet(M.CEL / "restricted_cells.parquet")
    dev = 0.0
    for rg in ("clinical", "clinical_nolvef"):
        for a in ARMS:
            x = R[(R.rung == f"{rg}#1") & (R.arm == a)].set_index("trial").sort_index()
            y = G[(G.rung == rg) & (G.config == "main") & (G.arm == a)].set_index("trial").sort_index()
            cc = ["loghr", "se", "n_pairs"] + [f"smd:{c}" for c in M.VN]
            d = np.abs(x[cc].to_numpy(float) - y[cc].to_numpy(float))
            dev = max(dev, float(np.nanmax(d)))
    SM = {}
    for (rg, a), g in R.groupby(["rung", "arm"]):
        g = g.set_index("trial", drop=False).loc[M.ALL]
        _, Sk = SP.per_trial(g)
        f = M.failed(g).to_numpy()
        Sk.loc[f, :] = np.nan
        base = rg.split("#")[0]
        m = set(M.MASK_RUNG[base]) | set(M.MASK_ARM.get(a, []))
        Sk.loc[:, [c for c in Sk.columns if c in m]] = np.nan
        SM[(rg, a)] = Sk[M.NONCODED]
    rows = []
    for sname, tr in (("S32", M.S32), ("S38", M.S38)):
        for base in ("clinical", "clinical_nolvef"):
            for a in ARMS[1:]:
                for k in list(range(1, K + 1)) + ["avg"]:
                    if k == "avg":
                        Sa = sum(SM[(f"{base}#{j}", a)].loc[tr] for j in range(1, K + 1)) / K
                        Sb = sum(SM[(f"{base}#{j}", "base")].loc[tr] for j in range(1, K + 1)) / K
                    else:
                        Sa, Sb = SM[(f"{base}#{k}", a)].loc[tr], SM[(f"{base}#{k}", "base")].loc[tr]
                    msk = Sa.isna() | Sb.isna()
                    ma, mb = Sa.mask(msk).mean(1), Sb.mask(msk).mean(1)
                    e, lo, hi, kk = SP.relred_ci(mb, ma)
                    d = (mb - ma).to_numpy()
                    rows.append(dict(set=sname, rung=base, arm=a, draw=k, m54_b=float(mb.mean()), m54_a=float(ma.mean()), relred54=e,
                                     lo=lo, hi=hi, k=kk, better=f"{int((d > 0).sum())}/{int(np.isfinite(d).sum())}", p=SP.p1s(d)))
    D = pd.DataFrame(rows)
    D.to_csv(OUT / "imputation_draws.csv", index=False)
    S = D[D.draw != "avg"].groupby(["set", "rung", "arm"]).relred54.agg(["min", "median", "max", "mean"]).round(2)
    S.to_csv(OUT / "imputation_draws_range.csv")
    print("draw-1 gate maxdev", dev)
    print(S.to_string())
    print(D[D.draw == "avg"].round(3).to_string(index=False))
    (OUT / "gate_draw1.txt").write_text(f"draw 1 vs psclin_nolvef main cells: maxdev {dev}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "summarize"])
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    run(min(a.workers, 24)) if a.cmd == "run" else summarize()
