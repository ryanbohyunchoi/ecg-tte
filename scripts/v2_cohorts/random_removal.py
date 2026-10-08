#!/usr/bin/env python
"""Random-removal calibration for the pooled primary contrast (supporting analysis; aggregates only).

For each draw b = 1..B and each trial with a spec-v2 exclusion, remove the SAME number of patients per arm as the spec-v2
rules remove, chosen at random (np.random.default_rng(20261008 + 1000 * b + trial index)); refit PS-CVD5 base, + ECG,
+ CLMBR-T and + both in the main configuration with PCs recomputed within the reduced cohort (as grid.py pc='within').
Outcome re-definitions are applied as in v2. Unchanged trials keep their version 1 cells. The pooled relative reduction
(54 items) and |dlog HR| for the 32 / 29 / 38 sets are then compared with the spec-v2 values: does the v1 -> v2 change
exceed what removing the same number of patients at random produces?

Usage: random_removal.py run [--draws 20] [--workers 32]  -> OUT/summary/restricted_random_removal_cells.parquet,
       random_removal.csv (per draw pooled aggregates), random_removal_summary.csv
"""
from __future__ import annotations

import argparse
import copy
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2common as K  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import grid as GR  # noqa: E402
import summarize as SU  # noqa: E402
from eval_longtail_balance import pcs  # noqa: E402

E, C = K.E, K.C
ARMS4 = ["base", "ECG", "CLMBR", "ECG+CLMBR"]


def task(args):
    n, draws = args
    K.umask()
    t0 = time.time()
    T = GR.load(n)
    D = pd.read_parquet(K.FLG / f"restricted_drop_{n}.parquet").set_index("patient_key")
    assert D.index.equals(T.keys)
    drop = D.drop_v2.to_numpy(bool)
    TT = T
    of = K.FLG / f"restricted_outcome_{n}.parquet"
    if of.exists():
        O = pd.read_parquet(of).set_index("patient_key")
        TT = copy.copy(T)
        TT.y_t, TT.y_e = O.y_t.to_numpy(float), O.y_e.to_numpy(int)
    b5, _, _ = C.designs(T, n, C.P5DX)
    craw = GR.clm_raw(T)
    i = K.ALL.index(n)
    est, psm = K.CONFIGS["main"]
    out = []
    for b in range(1, draws + 1):
        rng = np.random.default_rng(20261008 + 1000 * b + i)
        keep = np.ones(len(T.t), bool)
        for a in (1, 0):
            pos = np.where(T.t == a)[0]
            k = int(drop[pos].sum())
            if k:
                keep[rng.choice(pos, k, replace=False)] = False
        rows = np.where(keep)[0]
        ecg = pcs(GR.subset(T.ecg_raw, rows), 64)[:, :32]
        clm = pcs(GR.subset(craw, rows), 64)
        blk = {"base": [], "ECG": [ecg], "CLMBR": [clm], "ECG+CLMBR": [clm, ecg]}
        for a in ARMS4:
            X = np.hstack([b5[rows]] + blk[a])
            o = E.run_cell(TT, X, rows=rows, estimator=est, ps_model=psm, cstat=None)
            out.append(dict(draw=b, trial=n, key=K.KEY[n], idx=i, rung="P5", config="main", arm=a, k_pcs=K.KPC[a], rb=T.rb,
                            rs=T.rs, ex58="", p_ps=X.shape[1], cell_failed="",
                            **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c")},
                            retain=o["n_pairs"] / min(o["n_t"], o["n_c"]), **{f"smd:{c}": o[f"smd:{c}"] for c in K.VN}))
    print(n, f"{time.time() - t0:.0f}s", flush=True)
    return out


def pooled(Z, label):
    F, SM, RET, _ = SU.load_F(Z)
    K.P2._G.update(F=F, SM=SM, CL=K.V.cluster_of(), RET=RET, SETS=K.SETS)
    rows = []
    for sname in K.SETS:
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            Fa, Fb = F[("P5", "main", a)], F[("P5", "main", "base")]
            tr = K.SETS[sname]
            Fa2, Fb2 = K.SP.paired_balance(Fa, Fb, K.P2.mask(SM[("P5", "main", a)], K.NONCODED),
                                           K.P2.mask(SM[("P5", "main", "base")], K.NONCODED), tr)
            b_, a_ = Fb2.loc[tr, "m58"].to_numpy(), Fa2.loc[tr, "m58"].to_numpy()
            ok = np.isfinite(a_) & np.isfinite(b_)
            rr = 100 * (1 - a_[ok].mean() / b_[ok].mean())
            la, lb = Fa.loc[tr, "absd"], Fb.loc[tr, "absd"]
            okp = la.notna() & lb.notna()
            rows.append(dict(source=label, set=sname, arm=a, relred54=rr, absd_b=float(lb[okp].mean()), absd_a=float(la[okp].mean())))
    return rows


def run(draws, workers):
    from multiprocessing import get_context
    K.umask()
    tk = [n for n in K.ALL if pd.read_parquet(K.FLG / f"restricted_drop_{n}.parquet").drop_v2.any()]
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "insight", "declare", "aristotle", "rewind")
    tk = sorted(tk, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    with get_context("fork").Pool(min(workers, len(tk))) as p:
        res = p.map(task, [(n, draws) for n in tk], chunksize=1)
    R = pd.DataFrame([x for o in res for x in o])
    R.to_parquet(K.SUM / "restricted_random_removal_cells.parquet")
    V1 = GR.reference()
    V1 = V1[(V1.rung == "P5") & (V1.config == "main") & V1.arm.isin(ARMS4)]
    V2 = pd.read_parquet(K.CEL / "restricted_cells_v2_all.parquet")
    V2 = V2[(V2.rung == "P5") & (V2.config == "main") & V2.arm.isin(ARMS4)]
    rows = pooled(V1, "v1") + pooled(V2, "v2")
    # outcome-redefined trials without exclusions (none expected) keep v2 cells; unchanged trials keep v1 cells
    keepv2 = V2[~V2.trial.isin(tk)]
    for b in range(1, draws + 1):
        Z = pd.concat([R[R.draw == b].drop(columns="draw"), keepv2[R.columns.drop("draw")]], ignore_index=True)
        rows += [dict(r, draw=b) for r in pooled(Z, "random")]
    P = pd.DataFrame(rows)
    P.to_csv(K.SUM / "random_removal.csv", index=False)
    out = []
    for (sname, a), g in P.groupby(["set", "arm"]):
        rnd = g[g.source == "random"]
        v1 = g[g.source == "v1"].iloc[0]
        v2 = g[g.source == "v2"].iloc[0]
        out.append(dict(set=sname, arm=a, relred54_v1=v1.relred54, relred54_v2=v2.relred54, relred54_random_median=rnd.relred54.median(),
                        relred54_random_p5=rnd.relred54.quantile(0.05), relred54_random_p95=rnd.relred54.quantile(0.95),
                        frac_random_le_v2=float((rnd.relred54 <= v2.relred54).mean()), draws=len(rnd),
                        absd_gain_v1=v1.absd_b - v1.absd_a, absd_gain_v2=v2.absd_b - v2.absd_a,
                        absd_gain_random_median=(rnd.absd_b - rnd.absd_a).median(),
                        absd_gain_random_p5=(rnd.absd_b - rnd.absd_a).quantile(0.05),
                        absd_gain_random_p95=(rnd.absd_b - rnd.absd_a).quantile(0.95)))
    S = pd.DataFrame(out)
    S.to_csv(K.SUM / "random_removal_summary.csv", index=False)
    print(S.round(3).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--draws", type=int, default=20)
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    run(a.draws, min(a.workers, 32))
