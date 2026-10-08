#!/usr/bin/env python
"""Data checks for the rescore on the spec-v2 fixed cohorts (docs/emulation_quality_v2/RESCORE_V2_COHORTS.md; queue
2026-10-08 step D). Framework section 3.3 quantities only; no outcome contrast, no effect estimate.

Per trial, version 1 analysed cohort and spec-v2 fixed cohort (rows = not drop_v2; AMPLIFY / LODESTAR / PROVE IT outcomes
re-defined as in scripts/v2_cohorts/grid.py):
  DC-DA-size  smaller-arm size (band < 500 / >= 500) and pooled primary-outcome events within the horizon (band < 100 / >= 100)
  DC-DA-meas  share of the cohort with an echo EF in [index - 365, index - 1] (scripts/v2_cohorts/flags.py 'ef'); band < 50% / >= 50%
Version 1 bands are a check against the adjudicated DA.b scores (quality_v2_final.json).
Outputs (audits/claude-eq2-v2cohorts/, umask 077): restricted_dc.parquet (exact values), dc_bands.csv (bands and EF shares only).
Usage: dc_v2_cohorts.py [--workers 16]
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v2_cohorts"))
import v2common as K  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import grid as GR  # noqa: E402

OUT = K.A / "claude-eq2-v2cohorts"


def task(n):
    K.umask()
    T = GR.load(n)
    _, drop = GR.drop_rows(n, "drop_v2")
    M = pd.read_parquet(K.FLG / f"restricted_meas_{n}.parquet").set_index("patient_key").loc[T.keys]
    ye_v2 = T.y_e
    ofile = K.FLG / f"restricted_outcome_{n}.parquet"
    if ofile.exists():
        ye_v2 = pd.read_parquet(ofile).set_index("patient_key").loc[T.keys].y_e.to_numpy(int)
    out = []
    for cohort, rows, ye in (("v1", np.arange(len(T.t)), T.y_e), ("v2", np.where(~drop)[0], ye_v2)):
        t, ok = T.t[rows], T.y_ok[rows]
        out.append(dict(trial=n, cohort=cohort, n=len(rows), arm1=int(t.sum()), arm0=int((1 - t).sum()),
                        smaller=int(min(t.sum(), (1 - t).sum())), events=int((np.asarray(ye)[rows][ok] == 1).sum()),
                        ef_measured=float(np.isfinite(M.ef.to_numpy(float)[rows]).mean())))
    print(n, flush=True)
    return out


def main():
    from multiprocessing import get_context
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    K.umask()
    OUT.mkdir(parents=True, exist_ok=True)
    with get_context("fork").Pool(min(a.workers, 32)) as p:
        res = p.map(task, K.ALL, chunksize=1)
    R = pd.DataFrame([x for o in res for x in o])
    R.to_parquet(OUT / "restricted_dc.parquet")
    B = R[["trial", "cohort"]].copy()
    B["label"] = B.trial.map(K.NAME)
    B["smaller_arm_band"] = np.where(R.smaller >= 500, ">=500", "<500")
    B["events_band"] = np.where(R.events >= 100, ">=100", "<100")
    B["da_b"] = ((R.smaller < 500) | (R.events < 100)).astype(int)
    B["ef_measured_pct"] = (100 * R.ef_measured).round(1)
    B["ef_measured_band"] = np.where(R.ef_measured >= 0.5, ">=50%", "<50%")
    B.to_csv(OUT / "dc_bands.csv", index=False)
    print(B.to_string(index=False))


if __name__ == "__main__":
    main()
