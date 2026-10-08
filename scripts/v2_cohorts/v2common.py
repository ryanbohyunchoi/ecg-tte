"""Shared paths, trial sets and suppression helpers for the spec-v2 cohort fixes (docs/v2_cohorts/COHORT_FIXES.md).

Version 1 code is imported unchanged (scripts/v21/paper2_grid.py, scripts/v20/sens_primary32.py, scripts/v1_ps10/ps10.py,
scripts/v1_psclin_nolvef/psclin_nolvef.py, scripts/v1_criteria_check/*). Every file written by this package goes under
OUT (umask 077). Restricted (patient-level) files are named restricted_*; everything else is aggregate with counts 1-10
suppressed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
for p in ("v1_criteria_check", "v1_psclin_nolvef", "v1_ps10", "v21", "v20", "v18", ""):
    q = str(HERE.parent / p) if p else str(HERE.parent)
    if q not in sys.path:
        sys.path.insert(0, q)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import paper2_grid as P2  # noqa: E402

SP, E, V, C, AF = P2.SP, P2.E, P2.V, P2.C, P2.AF
A = SP.A
OUT = A / "claude-v2-cohorts"
FLG, CEL, SUM, LOG = OUT / "flags", OUT / "cells", OUT / "summary", OUT / "logs"
CRIT = A / "claude-v1-criteria"
GOLD = "/mnt/raid0/rbc58/omop/gold"
ALL, KEY, VN, GROUP, NONCODED = P2.ALL, P2.KEY, P2.VN, P2.GROUP, P2.NONCODED
CONFIGS, S32, S38 = P2.CONFIGS, P2.S32, P2.S38
MIN_CELL = 11

# reference cells (version 1 cohorts)
REF_V21 = P2.OUT / "restricted_cells.parquet"
REF_PS10 = A / "claude-v1-ps10" / "cells" / "restricted_cells.parquet"
REF_PSCLIN = A / "claude-v1-psclin-nolvef" / "cells" / "restricted_cells.parquet"

RUNGS = ["P1", "P5", "PS10", "Flags", "hdPS200", "clinical", "clinical_nolvef"]
ARMS = ["base", "ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"]
C32_RUNGS = ["P1", "P5", "clinical", "clinical_nolvef"]  # CLMBR32 (main config) exists for these rungs in version 1
KPC = P2.KPC

# provisional 29-trial set (framework v2.0 adjudication), engine names
LABEL_NAME = P2.LABEL_NAME
_Q = json.loads((ROOT / "docs/emulation_quality_v2/quality_v2_final.json").read_text())
S29 = [LABEL_NAME[x] for x in _Q["analysed_set"]]
S29 = [n for n in ALL if n in set(S29)]
assert len(S29) == 29, len(S29)
SETS = {"S32": S32, "S29": S29, "S38": S38}
NAME = {v: k for k, v in LABEL_NAME.items()}


def umask():
    os.umask(0o077)


def sup(k):
    k = int(k)
    return str(k) if (k == 0 or k >= MIN_CELL) else "<11"


def pct(k, n, nd=1):
    k, n = int(k), int(n)
    if n == 0:
        return "NA"
    if 1 <= k < MIN_CELL:
        return f"<{max(100 * MIN_CELL / n, 0.1):.{nd}f}"
    if 1 <= n - k < MIN_CELL:
        return f">{100 - 100 * MIN_CELL / n:.{nd}f}"
    return f"{100 * k / n:.{nd}f}"
