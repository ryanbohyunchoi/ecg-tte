#!/usr/bin/env python
"""v1.7: verify that each built confirmation trial loads through the v1.6 engine (v16_engine.load_trial, cache=False)
and write a READY marker. Loading only: no run_cell, no PS, no matching, no balance, no HR.

Checks per trial (aggregates only, counts 1-10 suppressed): analysis-population n and arm sizes, ECG PC and hdPS
level shapes, held-out matrix columns, outcome rows usable, RCT benchmark present, covars / covars2b / NCO files
present for every analysis key. Marker: /mnt/raid0/rbc58/ecg-tte/audits/claude-v17-trials/<trial>.READY (JSON).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v16"))
sys.path.insert(0, str(HERE.parent))
import v16_engine as E  # noqa: E402
from v13_common import A, V17  # noqa: E402

Q = A / "claude-v17-trials"


def sup(n):
    n = int(n)
    return n if (n == 0 or n >= 11) else "<11"


def main(names):
    os.umask(0o077)
    for n in names:
        try:
            T = E.load_trial(n, cache=False)
            keys = pd.Index(T.keys)
            files = {"covars": A / "claude-v17-covars" / f"{n}.parquet", "covars2b": A / "claude-v17-covars2b" / f"{n}.parquet",
                     "s5_nco": A / "claude-v17-s5-nco" / "extract" / f"restricted_nco_{n}.parquet",
                     "outcomes_v13": A / f"claude-{n}-outcomes-v13" / "restricted_outcomes_v13.parquet",
                     "hf_v14": A / f"claude-{n}-hf-v14" / "restricted_hf_outcome.parquet"}
            cov = {}
            for k, f in files.items():
                cov[k] = (round(float(keys.isin(pd.read_parquet(f, columns=["patient_key"]).patient_key).mean()), 4) if f.exists() else None)
            comp = E.var_components(T.H)
            info = dict(trial=n, key=T.key, n=sup(len(keys)), n_treated=sup(T.t.sum()), n_control=sup((1 - T.t).sum()),
                        ecg_pc_shape=list(T.ecg_pc.shape), hdps_levels=int(T.lv_np.shape[1]), heldout_components=int(T.H.shape[1]),
                        heldout_vars_available=int(sum(1 for v in comp.values() if v)), n_outcome_usable=sup(T.y_ok.sum()),
                        horizon_days=int(T.horizon), rct_loghr=round(T.rb, 4), rct_se=round(T.rs, 4), file_key_coverage=cov,
                        load_ok=True)
            ok = all(v is not None and v >= 0.999 for k, v in cov.items() if k != "hf_v14") and len(keys) > 0
            info["ready"] = bool(ok)
        except Exception as e:  # noqa: BLE001
            info = dict(trial=n, load_ok=False, ready=False, error=f"{type(e).__name__}: {e}"[:500])
        if info["ready"]:
            (Q / f"{n}.READY").write_text(json.dumps(info, indent=1) + "\n")
        print(json.dumps(info), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(V17))
