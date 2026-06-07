"""
ecg-tte-prep/stage2_embed.py

Stage 2: Embed ALL pool ECGs with the ECG encoder (backbone + projector).
Generic — not trial-specific. Reads ecg_candidates.parquet from Stage 1 pool/.

Reads ecg_candidates.parquet from pool/, embeds every unique fileID
using the BCL biometric encoder (backbone + projector), saves as
{fileID}.npy in the output directory.

Resumable: skips fileIDs that already have .npy files on disk.
Writes embedding_manifest.json recording which fileIDs were embedded.

IMPORTANT: We embed ALL candidate ECGs (every fileID in the ±365d pool),
not just the "selected" one per patient. This means filter_comet.py can
change --ecg-window-days (e.g., 60d → 30d) without re-embedding.
analyze_comet.py looks up embeddings by fileID from the filtered cohort's
`selected_ecg_fileID` column.

Usage:
    python trialemulation/methods/comet/embed_comet.py \\
        --pool-dir    /mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet/pool \\
        --checkpoint  /mnt/raid0/rbc58/cardiomap/experiments/ecg_biometric/best.pt \\
        --output-dir  /mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet/embeddings/biometric \\
        --ecg-dir     /mnt/raid0/bb2238/signals/preprocessed/all_ecgs \\
        --ecg-repo-dir /tmp/ECGFounder \\
        --batch-size  256
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root

from models.clip_model import MLP  # noqa: E402

NET1D_CFG = dict(
    in_channels     = 12,
    base_filters    = 64,
    ratio           = 1.0,
    filter_list     = [64, 160, 160, 400, 400, 1024, 1024],
    m_blocks_list   = [2, 2, 2, 3, 3, 4, 4],
    kernel_size     = 16,
    stride          = 2,
    groups_width    = 16,
    n_classes       = 150,
    return_features = True,
)


# ── Model loader ──────────────────────────────────────────────────────────────

def load_bcl_encoder(
    checkpoint_path: str,
    repo_dir:        str,
    device:          torch.device,
) -> nn.Module:
    """
    Load BCL biometric encoder (backbone + projector) from checkpoint.
    Returns model producing 512D L2-normalized embeddings.
    """
    repo = Path(repo_dir)
    if not repo.exists():
        import subprocess
        subprocess.run(
            ["git", "clone", "https://github.com/PKUDigitalHealth/ECGFounder", repo_dir],
            check=True,
        )
    if repo_dir not in sys.path:
        sys.path.insert(0, repo_dir)

    from net1d import Net1D  # noqa: PLC0415

    ckpt  = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    state = ckpt.get("model_state", ckpt)

    backbone_state = {k[len("ecg_encoder."):]: v
                      for k, v in state.items() if k.startswith("ecg_encoder.")}
    backbone = Net1D(**NET1D_CFG)
    backbone.load_state_dict(backbone_state, strict=True)

    proj_state = {k[len("projector."):]: v
                  for k, v in state.items() if k.startswith("projector.")}
    out_w     = proj_state.get("net.3.weight")
    embed_dim = int(out_w.shape[0]) if out_w is not None else 512
    projector = MLP(1024, embed_dim, embed_dim)
    if proj_state:
        projector.load_state_dict(proj_state, strict=True)
        print(f"  BCL projector loaded (embed_dim={embed_dim})")
    else:
        print("  WARNING: no projector keys — using random projector")

    class BCLEncoder(nn.Module):
        def __init__(self, backbone: nn.Module, projector: nn.Module) -> None:
            super().__init__()
            self.ecg_encoder = backbone
            self.projector   = projector

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            out  = self.ecg_encoder(x)
            feat = out[1] if isinstance(out, (tuple, list)) else out
            return F.normalize(self.projector(feat), dim=-1)

    model = BCLEncoder(backbone, projector)
    print(f"  BCL encoder loaded from {Path(checkpoint_path).name}")
    return model.to(device).eval()


# ── Dataset ───────────────────────────────────────────────────────────────────

class PoolECGDataset(Dataset):
    """
    One ECG per unique fileID in ecg_candidates.parquet.
    Returns (ecg_signal, fileID_str).
    """

    def __init__(self, candidates: pd.DataFrame, ecg_dir: str,
                 already_done: set[str]) -> None:
        ecg_root = Path(ecg_dir)
        records  = []

        for fid in tqdm(candidates["fileID"].unique(), desc="Resolving ECG files"):
            if fid in already_done:
                continue
            p = ecg_root / f"{fid}.npy"
            if not p.is_file():
                continue
            try:
                arr = np.load(p, mmap_mode="r")
                if arr.shape != (5000, 12):
                    continue
            except Exception:
                continue
            records.append({"fileID": fid, "path": p})

        self.records = records
        print(f"ECGs to embed: {len(records):,}  "
              f"(skipped already-done: {len(already_done):,})")

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, str]:
        rec = self.records[idx]
        arr = np.load(rec["path"])
        arr = np.nan_to_num(arr, nan=0.0).T          # (12, 5000)
        return torch.from_numpy(arr.astype(np.float32)), rec["fileID"]


# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="COMET Stage 2: embed all pool ECGs with BCL biometric encoder"
    )
    p.add_argument("--pool-dir",    required=True,
                   help="Directory containing ecg_candidates.parquet")
    p.add_argument("--checkpoint",  required=True,
                   help="BCL biometric checkpoint (.pt)")
    p.add_argument("--output-dir",  required=True,
                   help="Where to save {fileID}.npy files")
    p.add_argument("--ecg-dir",
                   default="/mnt/raid0/bb2238/signals/preprocessed/all_ecgs",
                   help="Directory of {fileID}.npy ECG signal files")
    p.add_argument("--ecg-repo-dir", default="/tmp/ECGFounder",
                   help="Local path to ECGFounder git repo (cloned if missing)")
    p.add_argument("--batch-size",  type=int, default=256)
    p.add_argument("--num-workers", type=int, default=8)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if "ecg_sim_from_biometric" in args.checkpoint:
        print("WARNING: checkpoint is the echo-sim fine-tune — for COMET trial emulation "
              "use ecg_biometric/best.pt (biometric encoder). See README Session 9.")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Load candidate list ───────────────────────────────────────────────────
    cands_path = Path(args.pool_dir) / "ecg_candidates.parquet"
    if not cands_path.exists():
        raise FileNotFoundError(f"ecg_candidates.parquet not found at {cands_path}. "
                                "Run make_comet.py first.")
    candidates = pd.read_parquet(cands_path)
    print(f"Total unique fileIDs in pool: {candidates['fileID'].nunique():,}")

    # ── Resumability: skip already-embedded fileIDs ───────────────────────────
    already_done = {p.stem for p in out_dir.glob("*.npy")}
    print(f"Already embedded: {len(already_done):,}")

    # ── Model ─────────────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print("Loading BCL biometric encoder …")
    model = load_bcl_encoder(args.checkpoint, args.ecg_repo_dir, device)

    # ── Dataset / loader ──────────────────────────────────────────────────────
    ds = PoolECGDataset(candidates, args.ecg_dir, already_done)
    if len(ds) == 0:
        print("Nothing to embed — all fileIDs already processed.")
        return

    loader = DataLoader(
        ds, batch_size=args.batch_size, shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    # ── Embed and save ────────────────────────────────────────────────────────
    n_saved = 0
    with torch.no_grad():
        for ecg_sigs, file_ids in tqdm(loader, desc="Embedding"):
            ecg_sigs = ecg_sigs.to(device)
            out  = model(ecg_sigs)
            feat = (out[1] if isinstance(out, (tuple, list)) else out).cpu().numpy()
            for fid, emb in zip(file_ids, feat):
                save_path = out_dir / f"{fid}.npy"
                save_path.parent.mkdir(parents=True, exist_ok=True)
                np.save(save_path, emb)
                n_saved += 1

    total_done = len(already_done) + n_saved
    print(f"\nEmbedded this run: {n_saved:,}")
    print(f"Total fileIDs embedded: {total_done:,}")

    # ── Manifest ──────────────────────────────────────────────────────────────
    manifest = {
        "embedded_at":   datetime.now().isoformat(),
        "checkpoint":    args.checkpoint,
        "n_this_run":    n_saved,
        "n_total":       total_done,
        "output_dir":    str(out_dir),
    }
    with open(out_dir / "embedding_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved → {out_dir / 'embedding_manifest.json'}")
    print(f"\nNext: run filter_comet.py with --embed-dir {out_dir}")


if __name__ == "__main__":
    main()
