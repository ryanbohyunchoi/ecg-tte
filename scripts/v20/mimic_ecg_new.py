#!/usr/bin/env python
"""v2.0 MIMIC-IV: ECG selection -> conversion -> BCL embedding -> link for the new trials (SOAP II, ELITE II,
PEPTIC), reusing scripts/v15/v15_mimic_ecg_pipeline.py unchanged except for the trial/BCL directories
(<OUT>/trials/<k>, <OUT>/bcl/<k>) and the candidate GPUs (0, 1, 7; free per nvidia-smi on 2026-09-30; the
pipeline re-checks nvidia-smi and waits if busy). Same checkpoint, x1000 uV fix, latest ECG in
[t0 - 365 d, t0]. Aggregates only.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v15"))
import v15_mimic_ecg_pipeline as P  # noqa: E402

OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-mimic-replication")
P.tdir = lambda k: OUT / "trials" / k
P.bdir = lambda k: OUT / "bcl" / k
P.GPUS = (0, 1, 7)

if __name__ == "__main__":
    for k in sys.argv[1:]:
        P.bdir(k).mkdir(parents=True, exist_ok=True)
        if not (P.bdir(k) / "input/prepare_summary.json").exists():
            P.prepare(k, workers=24)
        P.embed(k)
        P.link(k)
