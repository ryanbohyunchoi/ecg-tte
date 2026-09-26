#!/usr/bin/env python
"""Aggregate validation of the MIMIC -> Yale npy conversion and of the BCL embeddings.

(1) Per-lead amplitude after the BCL preprocessing baseline step (x - 500-sample median filter):
    median per-record SD and median max|x| per lead, MIMIC converted vs a random Yale sample.
    Also Einthoven/Goldberger identities (III = II - I, aVL = I - II/2, aVF = II - I/2) as
    relative mean-abs residuals, which confirm the lead order.
(2) Embedding stats (mean pairwise cosine, mean unit-vector norm, PC spectrum) for MIMIC
    trials vs the Yale ARISTOTLE BCL reference embeddings (same checkpoint, uV fix).
Writes aggregate JSON only.
"""
import argparse
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import median_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v15_mimic_ecg_convert import NPY_ROOT  # noqa: E402
from v15_mimic_ecg_pipeline import AUD, emb_stats, tdir  # noqa: E402

YALE = "/mnt/raid0/bb2238/signals/preprocessed/all_ecgs"
YALE_EMB = AUD / "claude-aristotle-bcl/restricted_embeddings_part-00000.parquet"
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]


def amp_stats(paths):
    A = np.stack([np.load(p)[:5000, :12].astype(np.float64) for p in paths])
    A = A - median_filter(A, size=(1, 500, 1))
    rel = lambda a, b: float(np.median(np.abs(a - b).mean(1) / (np.abs(a).mean(1) + 1e-9)))  # noqa: E731
    I, II, III, aVR, aVL, aVF = (A[:, :, k] for k in range(6))
    return dict(n=len(paths),
                median_sd_mV={l: round(float(v), 4) for l, v in zip(LEADS, np.median(A.std(1), 0))},
                median_maxabs_mV={l: round(float(v), 3) for l, v in zip(LEADS, np.median(np.abs(A).max(1), 0))},
                identity_residual=dict(III=round(rel(III, II - I), 3), aVR=round(rel(aVR, -(I + II) / 2), 3),
                                       aVL=round(rel(aVL, I - II / 2), 3), aVF=round(rel(aVF, II - I / 2), 3)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--trials", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    random.seed(0)
    mim = [os.path.join(NPY_ROOT, f) for f in os.listdir(NPY_ROOT) if f.endswith(".npy") and not f.startswith(".")]
    mim = random.sample(mim, min(a.n, len(mim)))
    yal = []
    for d in sorted(os.listdir(YALE))[::5]:
        with os.scandir(os.path.join(YALE, d)) as it:
            for i, e in enumerate(it):
                if e.name.endswith(".npy") and e.is_file():
                    yal.append(e.path)
                if i >= 100:
                    break
    yal = random.sample(yal, a.n)
    res = dict(amplitude=dict(mimic=amp_stats(mim), yale=amp_stats(yal)))
    ye = pd.read_parquet(YALE_EMB)
    res["embedding"] = {"yale_aristotle": emb_stats(np.stack(ye.embedding.map(np.asarray).to_list()))}
    for t in a.trials:
        p = tdir(t) / "ecg_embedding.parquet"
        if p.exists():
            e = pd.read_parquet(p)
            res["embedding"][f"mimic_{t}"] = emb_stats(np.stack(e.embedding.map(np.asarray).to_list()))
    json.dump(res, open(a.out, "w"), indent=2)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
