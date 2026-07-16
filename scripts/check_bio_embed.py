"""
check_bio_embed.py

Sanity-check bio_embed.py output. Verifies embedding/manifest alignment,
matrix integrity (no NaN/zero rows, L2-normalised), and cohort constraints
(one ECG/individual, EF<threshold, gap within window).

Usage:
    python scripts/check_bio_embed.py --dir /mnt/raid0/rbc58/bio/v1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="bio_embed output dir")
    ap.add_argument("--ef-threshold", type=float, default=40.0)
    ap.add_argument("--window-days", type=int, default=30)
    args = ap.parse_args()

    d = Path(args.dir)
    emb  = np.load(d / "embeddings.npy")
    man  = pd.read_parquet(d / "manifest.parquet")
    meta = json.load(open(d / "bio_embed_manifest.json"))

    checks: list[tuple[str, bool, str]] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    # ── Alignment ─────────────────────────────────────────────────────────────
    chk("emb rows == manifest rows", emb.shape[0] == len(man),
        f"emb={emb.shape}, manifest={len(man)}")
    chk("manifest rows == meta.n_individuals", len(man) == meta["n_individuals"],
        f"{len(man)} vs {meta['n_individuals']}")
    chk("row col == index order",
        "row" in man.columns and (man["row"].values == np.arange(len(man))).all())

    # ── Matrix integrity ──────────────────────────────────────────────────────
    chk("dtype float32", emb.dtype == np.float32, str(emb.dtype))
    chk("no NaN/Inf", not (np.isnan(emb).any() or np.isinf(emb).any()))
    zero = int((np.abs(emb).sum(1) == 0).sum())
    chk("no all-zero rows (failed embeds)", zero == 0, f"{zero} zero rows")
    norms = np.linalg.norm(emb, axis=1)
    chk("L2-normalised (~1.0)", bool(np.allclose(norms, 1.0, atol=1e-3)),
        f"min={norms.min():.4f} max={norms.max():.4f}")
    chk("all rows unique", len(np.unique(emb, axis=0)) == emb.shape[0])

    # ── Cohort constraints ────────────────────────────────────────────────────
    chk("one ECG per individual (unique MRN)", man["MRN"].nunique() == len(man),
        f"{man['MRN'].nunique()} unique / {len(man)}")
    chk("unique fileID", man["fileID"].nunique() == len(man),
        f"{man['fileID'].nunique()} unique / {len(man)}")
    chk(f"EF < {args.ef_threshold}", man["EF"].max() < args.ef_threshold,
        f"EF max={man['EF'].max()}")
    chk(f"gap <= {args.window_days}d",
        man["ecg_echo_gap_days"].abs().max() <= args.window_days,
        f"max abs gap={man['ecg_echo_gap_days'].abs().max()}")
    chk("no null EF/dates",
        not man[["EF", "EchoDate", "ECGDate"]].isna().any().any())

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}\nbio_embed check — {d}\n{'='*60}")
    print(f"embeddings : {emb.shape}  ({emb.dtype})")
    print(f"individuals: {len(man):,}")
    print(f"checkpoint : {meta.get('checkpoint')}")
    print(f"git_sha    : {meta.get('git_sha')}\n")

    all_ok = True
    for name, ok, detail in checks:
        flag = "PASS" if ok else "FAIL"
        all_ok &= ok
        line = f"  [{flag}] {name}"
        if detail and not ok:
            line += f"  -> {detail}"
        print(line)

    print(f"\nEF distribution:\n{man['EF'].describe().to_string()}")
    print(f"\ngap days (ECG - echo):\n{man['ecg_echo_gap_days'].describe().to_string()}")
    print(f"\n{'ALL CHECKS PASSED' if all_ok else '*** SOME CHECKS FAILED ***'}")
    raise SystemExit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
