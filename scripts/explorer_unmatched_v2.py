#!/usr/bin/env python
"""Unmatched |SMD| of the 58 held-out items on the spec-v2 fixed cohorts, for the balance explorer's cohort toggle
(scripts/build_balance_explorer.py; queue docs/queue/QUEUE_2026_10_08.md step C).

v16_engine.run_cell(T, X=None, rows) = crude (unweighted, all rows), the engine path of the version 1 unmatched values.
Gate: rows = the full version 1 cohort must reproduce audits/claude-v18-embed-compare/results.csv (half full, rung none,
arm unmatched) to csv round-trip precision. Spec-v2 rows = not drop_v2 (scripts/v2_cohorts/grid.py drop_rows).
Output (restricted, patient-free but per-trial): audits/claude-balance-explorer/restricted_unmatched_v2.parquet,
unmatched_gate.json.
Usage: explorer_unmatched_v2.py [--workers 24]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "v2_cohorts"))
import v2common as K  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import grid as GR  # noqa: E402

E, VN = K.E, K.VN
SCR = K.A / "claude-balance-explorer"
V18 = K.A / "claude-v18-embed-compare/results.csv"


def task(n):
    K.umask()
    T = GR.load(n)
    full = np.arange(len(T.t))
    _, drop = GR.drop_rows(n, "drop_v2")
    out = []
    for cohort, rows in (("v1", full), ("v2", np.where(~drop)[0])):
        o = E.run_cell(T, None, rows=rows, cstat=None)
        out.append(dict(trial=n, cohort=cohort, **{f"smd:{c}": o[f"smd:{c}"] for c in VN}))
    print(n, flush=True)
    return out


def main():
    from multiprocessing import get_context
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    K.umask()
    SCR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with get_context("fork").Pool(min(a.workers, 32)) as p:
        res = p.map(task, K.ALL, chunksize=1)
    R = pd.DataFrame([x for o in res for x in o])
    R.to_parquet(SCR / "restricted_unmatched_v2.parquet")
    U = pd.read_csv(V18)
    U = U[(U.half == "full") & (U.rung == "none") & (U.arm_role == "unmatched")].set_index("trial").loc[K.ALL]
    X = R[R.cohort == "v1"].set_index("trial").loc[K.ALL]
    cols = [f"smd:{c}" for c in VN]
    A_, B_ = X[cols].abs().to_numpy(float), U[cols].abs().to_numpy(float)
    st = dict(trials=len(K.ALL), items=len(VN), max_abs_dev=float(np.nanmax(np.abs(A_ - B_))),
              nan_mismatch=int((np.isnan(A_) ^ np.isnan(B_)).sum()), secs=round(time.time() - t0))
    st["passed"] = bool(st["max_abs_dev"] <= 1e-12 and st["nan_mismatch"] == 0)
    (SCR / "unmatched_gate.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
