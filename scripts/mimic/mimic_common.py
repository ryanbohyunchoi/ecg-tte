"""Shared paths and helpers for the consolidated MIMIC-IV external validation (docs/mimic/MIMIC_EXTERNAL_VALIDATION.md).

Imports the v20 / v21 MIMIC modules without modifying them. All outputs go under OUT (umask 077); MIMIC staged
tables, the v15 / v20 / v21 MIMIC output dirs, the CLMBR-T checkpoint and the OMOP vocabulary are read only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v21"))
sys.path.insert(0, str(HERE.parent / "v20"))
sys.path.insert(0, str(HERE.parent / "v15"))
sys.path.insert(0, str(HERE.parent))

os.umask(0o077)
AUD = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = AUD / "claude-mimic-clmbr-20261014"
STAGE = AUD / "claude-v15-mimic-shared/stage"
V21 = AUD / "claude-v21-paper2/mimic"
MODEL = Path("/mnt/raid0/eo287/clmbr")
VOCAB = Path("/mnt/raid0/rbc58/mosaic/mapping")
MEDS = OUT / "meds"
CLMBR = OUT / "clmbr"
SEED_BOOT = 20261001
N_BOOT = 4000
SUPPRESS = 11  # counts 1-10 are suppressed


def sup(n):
    n = int(n)
    return f"<{SUPPRESS}" if 0 < n < SUPPRESS else n


def clmbr_codes():
    """Code-type strings of the CLMBR-T dictionary, exported once from dictionary.msgpack with the mosaic env (the
    analysis env has no msgpack); the export records the dictionary sha256, checked here against the checkpoint."""
    import hashlib
    import json
    d = json.load(open(OUT / "vocab" / "clmbr_code_strings.json"))
    assert d["dictionary_sha256"] == hashlib.sha256(open(MODEL / "dictionary.msgpack", "rb").read()).hexdigest()
    return set(d["codes"])


def relred_ci(B, Ev, nb=N_BOOT, seed=SEED_BOOT):
    """Relative reduction 100 * (1 - mean(Ev) / mean(B)) over trials, percentile CI from a trial bootstrap with a
    fresh fixed-seed generator; same algorithm as scripts/v20/sens_primary32.relred_ci (4,000 resamples, seed
    20261001, the paper convention)."""
    import numpy as np
    B, Ev = np.asarray(B, float), np.asarray(Ev, float)
    ok = np.isfinite(B) & np.isfinite(Ev)
    B, Ev = B[ok], Ev[ok]
    est = 100 * (1 - Ev.mean() / B.mean())
    rng = np.random.default_rng(seed)
    I = rng.integers(0, len(B), size=(nb, len(B)))
    bs = 100 * (1 - Ev[I].mean(1) / B[I].mean(1))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return float(est), float(lo), float(hi)


def status(line):
    """One line per step to OUT/STATUS.md."""
    from datetime import datetime
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "STATUS.md", "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} {line}\n")
