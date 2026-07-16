"""
bio_embed.py

Standalone embedding job for LVSD (EF<40) subphenotyping.

Pulls every individual with a qualifying echo EF < threshold, finds the ECG
recorded within a window (default +/-30 days) of a qualifying echo, keeps the
nearest ECG per individual, caps to N individuals, and embeds each ECG with the
existing BCL biometric encoder (ECGFounder Net1D backbone -> MLP projector ->
512D L2-normalised). Emits a single embedding matrix + a manifest for downstream
unsupervised clustering / subphenotype discovery.

NOT trial-specific. Reuses:
  - load_echo_meta / load_ecg_meta  (cohort_utils.py)
  - load_bcl_encoder                (stage2_embed.py)

Outputs (to --output-dir):
  embeddings.npy      float32 (N, 512)  L2-normalised, row-aligned to manifest
  manifest.parquet    row -> MRN, fileID, EF, EchoDate, ECGDate, ecg_echo_gap_days
  bio_embed_manifest.json   run metadata (args, counts, checkpoint, git SHA)

Usage:
    python scripts/bio_embed.py \\
        --echo-meta   /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \\
        --ecg-meta    /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \\
        --ecg-dir     /mnt/raid0/bb2238/signals/preprocessed/all_ecgs \\
        --checkpoint  /mnt/raid0/rbc58/cardiomap/experiments/ecg_biometric/best.pt \\
        --ecg-repo-dir /tmp/ECGFounder \\
        --output-dir  /mnt/raid0/rbc58/bio/v1 \\
        --ef-threshold 40 --window-days 30 --max-individuals 50000
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts/

from cohort_utils import load_echo_meta, load_ecg_meta  # noqa: E402
from stage2_embed import load_bcl_encoder               # noqa: E402


# ── Cohort selection ──────────────────────────────────────────────────────────

def select_cohort(
    echo_meta_path:  str,
    ecg_meta_path:   str,
    ecg_dir:         str,
    ef_threshold:    float,
    window_days:     int,
    max_individuals: int,
    seed:            int,
) -> pd.DataFrame:
    """
    One nearest-to-echo ECG per individual with a qualifying echo EF < threshold.
    Returns columns: MRN, fileID, EF, EchoDate, ECGDate, ecg_echo_gap_days, path.
    """
    print(f"Loading echo metadata … (EF < {ef_threshold})")
    echo = load_echo_meta(echo_meta_path)          # MRN, EchoDate, EF (10..80 sane range)
    echo = echo[echo["EF"] < ef_threshold].copy()
    print(f"  qualifying echos: {len(echo):,}  "
          f"individuals: {echo['MRN'].nunique():,}")

    lvsd_mrns = set(echo["MRN"].unique())
    print("Loading ECG metadata …")
    ecg = load_ecg_meta(ecg_meta_path, mrns=lvsd_mrns)   # MRN, fileID, ECGDate, ...
    ecg = ecg[["MRN", "fileID", "ECGDate"]].copy()
    print(f"  ECGs for LVSD individuals: {len(ecg):,}")

    # ── Match ECG to a qualifying echo within +/- window_days ─────────────────
    # For each individual keep the *lowest-EF* qualifying echo as the reference
    # (most severe LVSD), then require an ECG within the window of that echo.
    echo_ref = (echo.sort_values(["MRN", "EF"])
                    .groupby("MRN", as_index=False)
                    .first())                              # MRN, EchoDate, EF
    m = ecg.merge(echo_ref, on="MRN", how="inner")
    m["ecg_echo_gap_days"] = (m["ECGDate"] - m["EchoDate"]).dt.days
    m = m[m["ecg_echo_gap_days"].abs() <= window_days].copy()
    print(f"  ECG within +/-{window_days}d of reference echo: {len(m):,}  "
          f"individuals: {m['MRN'].nunique():,}")

    # nearest ECG per individual (smallest absolute gap; tie -> earliest date)
    m["abs_gap"] = m["ecg_echo_gap_days"].abs()
    m = (m.sort_values(["MRN", "abs_gap", "ECGDate"])
           .groupby("MRN", as_index=False)
           .first())
    print(f"  one ECG/individual: {len(m):,}")

    # ── Verify signal file exists + correct shape ─────────────────────────────
    ecg_root = Path(ecg_dir)
    keep_rows = []
    for row in tqdm(m.itertuples(index=False), total=len(m), desc="Resolving signals"):
        p = ecg_root / f"{row.fileID}.npy"
        if not p.is_file():
            continue
        try:
            if np.load(p, mmap_mode="r").shape != (5000, 12):
                continue
        except Exception:
            continue
        keep_rows.append({**row._asdict(), "path": str(p)})
    coh = pd.DataFrame(keep_rows)
    print(f"  with valid (5000,12) signal on disk: {len(coh):,}")

    if len(coh) == 0:
        raise RuntimeError("No individuals with a valid ECG signal — check --ecg-dir.")

    # ── Cap to max_individuals (seeded sample) ────────────────────────────────
    if len(coh) > max_individuals:
        coh = coh.sample(n=max_individuals, random_state=seed)
        print(f"  sampled down to {max_individuals:,} individuals (seed={seed})")

    coh = coh.sort_values("MRN").reset_index(drop=True)
    return coh[["MRN", "fileID", "EF", "EchoDate", "ECGDate",
                "ecg_echo_gap_days", "path"]]


# ── Dataset ───────────────────────────────────────────────────────────────────

class ECGDataset(Dataset):
    """Returns (signal (12,5000) float32, row_index int) — row-aligned to cohort."""

    def __init__(self, cohort: pd.DataFrame) -> None:
        self.paths = cohort["path"].tolist()

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        arr = np.load(self.paths[idx])
        arr = np.nan_to_num(arr, nan=0.0).T            # (12, 5000)
        return torch.from_numpy(arr.astype(np.float32)), idx


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Embed ECGs (<=window of qualifying echo) for EF<threshold "
                    "individuals with the BCL biometric encoder."
    )
    p.add_argument("--echo-meta", required=True,
                   help="Echo metadata parquet (MRN, EchoDate, EF)")
    p.add_argument("--ecg-meta", required=True,
                   help="ECG metadata parquet (MRN, fileID, ECGDate)")
    p.add_argument("--ecg-dir",
                   default="/mnt/raid0/bb2238/signals/preprocessed/all_ecgs",
                   help="Directory of {fileID}.npy ECG signal files")
    p.add_argument("--checkpoint", required=True,
                   help="BCL biometric checkpoint (.pt)")
    p.add_argument("--output-dir", required=True,
                   help="Output directory (e.g. /mnt/raid0/rbc58/bio/v1)")
    p.add_argument("--ecg-repo-dir", default="/tmp/ECGFounder",
                   help="Local path to ECGFounder git repo (cloned if missing)")
    p.add_argument("--ef-threshold", type=float, default=40.0)
    p.add_argument("--window-days", type=int, default=30)
    p.add_argument("--max-individuals", type=int, default=50000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--num-workers", type=int, default=8)
    return p.parse_args()


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent,
        ).decode().strip()
    except Exception:
        return "unknown"


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Cohort ────────────────────────────────────────────────────────────────
    cohort = select_cohort(
        args.echo_meta, args.ecg_meta, args.ecg_dir,
        args.ef_threshold, args.window_days, args.max_individuals, args.seed,
    )
    n = len(cohort)
    print(f"\nFinal cohort: {n:,} individuals × 1 ECG")

    # ── Model ─────────────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print("Loading BCL biometric encoder …")
    model = load_bcl_encoder(args.checkpoint, args.ecg_repo_dir, device)
    if torch.cuda.device_count() > 1:
        print(f"  Using {torch.cuda.device_count()} GPUs via DataParallel")
        model = nn.DataParallel(model)

    # ── Embed (row-aligned to cohort) ─────────────────────────────────────────
    loader = DataLoader(
        ECGDataset(cohort), batch_size=args.batch_size, shuffle=False,
        num_workers=args.num_workers, pin_memory=torch.cuda.is_available(),
    )
    embeddings = np.zeros((n, 512), dtype=np.float32)
    with torch.no_grad():
        for sigs, idxs in tqdm(loader, desc="Embedding"):
            sigs = sigs.to(device)
            out  = model(sigs)
            feat = (out[1] if isinstance(out, (tuple, list)) else out).cpu().numpy()
            embeddings[idxs.numpy()] = feat.astype(np.float32)

    if embeddings.shape[1] != 512:
        print(f"  NOTE: embed_dim = {embeddings.shape[1]} (not 512)")

    # ── Save ──────────────────────────────────────────────────────────────────
    emb_path = out_dir / "embeddings.npy"
    np.save(emb_path, embeddings)
    manifest = cohort.drop(columns=["path"]).copy()
    manifest.insert(0, "row", np.arange(n))
    man_path = out_dir / "manifest.parquet"
    manifest.to_parquet(man_path, index=False)

    meta = {
        "created_at":      datetime.now().isoformat(),
        "git_sha":         git_sha(),
        "checkpoint":      args.checkpoint,
        "ef_threshold":    args.ef_threshold,
        "window_days":     args.window_days,
        "max_individuals": args.max_individuals,
        "seed":            args.seed,
        "n_individuals":   n,
        "embed_dim":       int(embeddings.shape[1]),
        "embeddings":      str(emb_path),
        "manifest":        str(man_path),
    }
    with open(out_dir / "bio_embed_manifest.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)

    print(f"\nSaved:")
    print(f"  {emb_path}   ({embeddings.shape})")
    print(f"  {man_path}   ({n:,} rows)")
    print(f"  {out_dir / 'bio_embed_manifest.json'}")
    print("\nNext: load embeddings.npy + manifest.parquet for clustering "
          "(UMAP/HDBSCAN, k-means, etc.).")


if __name__ == "__main__":
    main()
