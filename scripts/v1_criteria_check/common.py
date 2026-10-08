"""Shared helpers for the version 1 cohort-criteria check (docs/v1_criteria_check/TRIAL_CRITERIA_CHECK.md).

Read-only on every input. Restricted per-patient files are written only under OUT (umask 077); everything printed or
written to a non-restricted CSV is aggregate, with counts 1-10 suppressed.
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/rbc58/github/ecg-tte")
sys.path.insert(0, str(REPO / "scripts"))
from v13_common import A, EXTRA, PRIMARY, paths  # noqa: E402

OUT = A / "claude-v1-criteria"
GOLD = "/mnt/raid0/rbc58/omop/gold"
ECG_META = "/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet"
ECHO_META = "/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet"
COMET_MED_SQLITE = A / "comet-candidates-c2FSBqdW/report/restricted_candidates.sqlite"
MIN_CELL = 11

# flagged trials: engine name (sens_primary32.ALL) -> label
FLAGGED = {"cabana-v2": "CABANA", "laaos3": "LAAOS III", "comet": "COMET", "transform-hf": "TRANSFORM-HF",
           "elite-ii": "ELITE II", "emperor-preserved-v2": "EMPEROR-Preserved", "life": "LIFE", "valiant": "VALIANT",
           "carolina": "CAROLINA", "leader": "LEADER", "sustain6": "SUSTAIN-6", "rewind": "REWIND",
           "declare": "DECLARE-TIMI 58", "canvas": "CANVAS", "amplify": "AMPLIFY", "lodestar": "LODESTAR",
           "prove-it": "PROVE IT-TIMI 22"}


def umask():
    os.umask(0o077)


def cohort_dir(n):
    return A / {**PRIMARY, **EXTRA}[n][1]


def analysed_keys(n):
    """Analysed keys K exactly as v13_common.Trial (completed covariates n ECG emb n CLMBR emb n phenotypes n panel),
    with person_id, treated, treatment_arm, index_date from the cohort roster. Restricted (in memory only)."""
    B = f"{A}/claude-{n}-baseline-v11"
    cov = pd.read_parquet(f"{B}/restricted_completed_01.parquet", columns=["patient_key", "treated"]).set_index("patient_key")
    P = paths(n)
    ecg = pd.concat([pd.read_parquet(f, columns=["patient_key"]) for f in sorted(glob.glob(P["ecg"]))]).patient_key
    ehr = (f"{A}/comet-clmbr-full-NAyb4G2x/report/restricted_embeddings_part-*.parquet" if n == "comet"
           else f"{A}/claude-{n}-clmbr-codeonly/report/restricted_embeddings_part-*.parquet")
    clm = pd.concat([pd.read_parquet(f, columns=["patient_key"]) for f in sorted(glob.glob(ehr))]).patient_key
    ph = pd.read_parquet(P["ph"], columns=["patient_key"]).patient_key
    pan = pd.read_parquet(P["panel"], columns=["patient_key"]).patient_key
    K = cov.index
    for ix in (pd.Index(ecg), pd.Index(clm), pd.Index(ph), pd.Index(pan)):
        K = K.intersection(ix)
    K = K.sort_values()
    ro = pd.read_parquet(cohort_dir(n) / "restricted_cohort.parquet").drop_duplicates("patient_key").set_index("patient_key")
    D = ro.reindex(K)[["person_id", "treatment_arm", "treated", "index_date"]].copy()
    D["treated_cov"] = cov.treated.reindex(K).astype(int).to_numpy()
    D["index_date"] = pd.to_datetime(D.index_date)
    D.index.name = "patient_key"
    return D.reset_index()


def sup(n):
    """suppressed count as string."""
    n = int(n)
    return str(n) if (n == 0 or n >= MIN_CELL) else "<11"


def pct(k, n, nd=1):
    """percentage string; suppressed when the count is 1-10."""
    k, n = int(k), int(n)
    if n == 0:
        return "NA"
    if 1 <= k < MIN_CELL:
        return f"<{max(100 * MIN_CELL / n, 0.1):.{nd}f}"
    return f"{100 * k / n:.{nd}f}"


def cnt_pct(k, n):
    k, n = int(k), int(n)
    if 1 <= n - k < MIN_CELL:  # complement 1-10 would be derivable
        return f"all but <11 (>{100 - 100 * MIN_CELL / n:.1f}%)"
    return f"{sup(k)} ({pct(k, n)}%)"


def suppress_df(D, cols):
    D = D.copy()
    for c in cols:
        v = pd.to_numeric(D[c], errors="coerce")
        b = (v >= 1) & (v < MIN_CELL)
        D[c] = D[c].astype(object)
        D.loc[b, c] = "<11"
    return D
