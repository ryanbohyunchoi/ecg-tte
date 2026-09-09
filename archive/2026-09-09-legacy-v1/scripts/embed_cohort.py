"""
trialemulation/embed_cohort.py

Extract ECG embeddings for each cohort patient at their index date.

For each patient:
  - Find the ECG recorded closest to (and before) the index date (±365 days)
  - Embed with the chosen encoder
  - Save as {output_dir}/{subdir}/{person_id}.npy

--model-type options:
  clip      Load ECGFounder backbone from a CLIP checkpoint → 1024D features
            (original behaviour, output subdir: multimodal/)
  ecg_sim   Load full ECGSimilarityEncoder (backbone + projector) from a
            biometric/echo-sim checkpoint → 512D L2-normalised features
            (output subdir: ecg_sim/)

Use --also-unimodal to additionally embed with the original pretrained
ECGFounder (no fine-tuning) for ablation comparison (output: unimodal/).

Usage:
    python trialemulation/embed_cohort.py \\
        --cohort       /mnt/raid0/rbc58/cardiomap/trialemulation/cohort.parquet \\
        --ecg-meta     /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \\
        --ecg-dir      /mnt/raid0/bb2238/signals/preprocessed/all_ecgs \\
        --checkpoint   /mnt/raid0/rbc58/cardiomap/experiments/ecg_sim_from_biometric/best.pt \\
        --model-type   ecg_sim \\
        --output-dir   /mnt/raid0/rbc58/cardiomap/trialemulation/embeddings \\
        --ecg-repo-dir /tmp/ECGFounder \\
        --also-unimodal
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.eval_downstream import load_clip_ecgfounder, load_original_ecgfounder
from models.clip_model import MLP

# ── ECGFounder config (shared with training scripts) ──────────────────────────
HF_REPO     = "PKUDigitalHealth/ECGFounder"
HF_FILENAME = "12_lead_ECGFounder.pth"

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
# ─────────────────────────────────────────────────────────────────────────────


def load_sim_ecgfounder(
    checkpoint_path: str,
    repo_dir:        str,
    device:          torch.device,
) -> nn.Module:
    """
    Load ECGSimilarityEncoder (backbone + projector) from a biometric or
    echo-sim checkpoint. Returns L2-normalised projected embeddings.

    Infers embed_dim automatically from projector weight shapes.
    """
    # Ensure ECGFounder repo is available
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

    # ── Backbone ──────────────────────────────────────────────────────────────
    backbone_state = {
        k[len("ecg_encoder."):]: v
        for k, v in state.items()
        if k.startswith("ecg_encoder.")
    }
    backbone = Net1D(**NET1D_CFG)
    backbone.load_state_dict(backbone_state, strict=True)

    # ── Projector ─────────────────────────────────────────────────────────────
    proj_state = {
        k[len("projector."):]: v
        for k, v in state.items()
        if k.startswith("projector.")
    }

    # Infer embed_dim from the final linear layer's output shape
    out_w     = proj_state.get("net.3.weight")
    embed_dim = int(out_w.shape[0]) if out_w is not None else 512

    projector = MLP(1024, embed_dim, embed_dim)
    if proj_state:
        projector.load_state_dict(proj_state, strict=True)
        print(f"  Projector loaded (embed_dim={embed_dim})")
    else:
        print("  WARNING: no projector keys found — using random projector")

    # ── Wrap ──────────────────────────────────────────────────────────────────
    class _SimilarityEncoder(nn.Module):
        def __init__(self, backbone: nn.Module, projector: nn.Module) -> None:
            super().__init__()
            self.ecg_encoder = backbone
            self.projector   = projector

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            out  = self.ecg_encoder(x)
            feat = out[1] if isinstance(out, (tuple, list)) else out
            return F.normalize(self.projector(feat), dim=-1)

    model = _SimilarityEncoder(backbone, projector)
    print(f"  ECGSimilarityEncoder loaded from {Path(checkpoint_path).name}")
    return model.to(device).eval()


# ── Dataset ───────────────────────────────────────────────────────────────────

class CohortECGDataset(Dataset):
    """
    One ECG per cohort patient — the recording closest to (and before) index_date.
    Returns (ecg_signal, person_id_str).
    """

    def __init__(
        self,
        cohort:          pd.DataFrame,
        ecg_meta:        pd.DataFrame,
        ecg_dir:         str,
        max_days_before: int = 365,
    ) -> None:
        ecg_root = Path(ecg_dir)
        records  = []

        for _, row in tqdm(cohort.iterrows(), total=len(cohort), desc="Matching ECGs"):
            pid        = str(int(row["person_id"]))
            mrn        = str(row["MRN"])
            index_date = pd.Timestamp(row["index_date"])

            pt_ecgs = ecg_meta[ecg_meta["_mrn"] == mrn].copy()
            pt_ecgs = pt_ecgs[pt_ecgs["_ecg_date"] <= index_date]
            pt_ecgs = pt_ecgs[pt_ecgs["_ecg_date"] >= index_date - pd.Timedelta(days=max_days_before)]

            if pt_ecgs.empty:
                continue

            best = pt_ecgs.sort_values("_ecg_date").iloc[-1]
            fid  = str(best["_fid"])
            p    = ecg_root / f"{fid}.npy"

            if not p.is_file():
                continue
            try:
                if np.load(p, mmap_mode="r").shape != (5000, 12):
                    continue
            except Exception:
                continue

            records.append({"person_id": pid, "path": p})

        self.records = records
        print(f"Cohort patients with matched ECG: {len(records):,} / {len(cohort):,}")

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, str]:
        rec = self.records[idx]
        arr = np.load(rec["path"])                      # (5000, 12)
        arr = np.nan_to_num(arr, nan=0.0).T             # (12, 5000)
        return torch.from_numpy(arr.astype(np.float32)), rec["person_id"]


def load_ecg_metadata(ecg_meta_path: str) -> pd.DataFrame:
    meta      = pd.read_parquet(ecg_meta_path)
    orig_cols = list(meta.columns)

    fid_col  = next((c for c in orig_cols if c == "fileID"),
                    next((c for c in orig_cols if c.lower() == "fileid"), None))
    mrn_col  = next((c for c in orig_cols if c.lower() == "mrn"), None)
    date_col = next((c for c in orig_cols
                     if "ecg" in c.lower() and "date" in c.lower()), None)
    if date_col is None:
        date_col = next((c for c in orig_cols if "date" in c.lower()), None)

    if not all([mrn_col, fid_col, date_col]):
        raise ValueError(f"Cannot find required cols. Available: {orig_cols}")

    meta["_mrn"]      = meta[mrn_col].astype(str)
    meta["_fid"]      = meta[fid_col].astype(str).str.replace(".npy", "", regex=False)
    meta["_ecg_date"] = pd.to_datetime(meta[date_col], errors="coerce")
    return meta.dropna(subset=["_ecg_date"])


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Embed cohort ECGs at index date")
    parser.add_argument("--cohort",        required=True)
    parser.add_argument("--ecg-meta",      required=True)
    parser.add_argument("--ecg-dir",
                        default="/mnt/raid0/bb2238/signals/preprocessed/all_ecgs")
    parser.add_argument("--checkpoint",    required=True,
                        help="Path to model checkpoint")
    parser.add_argument("--model-type",    default="clip",
                        choices=["clip", "ecg_sim"],
                        help="clip: backbone only → 1024D  |  "
                             "ecg_sim: backbone+projector → 512D L2-norm")
    parser.add_argument("--output-dir",    required=True)
    parser.add_argument("--ecg-repo-dir",  default="/tmp/ECGFounder")
    parser.add_argument("--also-unimodal", action="store_true",
                        help="Also embed with original ECGFounder for ablation")
    parser.add_argument("--batch-size",    type=int, default=256)
    parser.add_argument("--num-workers",   type=int, default=8)
    parser.add_argument("--max-days",      type=int, default=365)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    subdir     = "ecg_sim" if args.model_type == "ecg_sim" else "multimodal"
    (output_dir / subdir).mkdir(parents=True, exist_ok=True)
    if args.also_unimodal:
        (output_dir / "unimodal").mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── Load cohort + ECG metadata ────────────────────────────────────────────
    cohort   = pd.read_parquet(args.cohort)
    ecg_meta = load_ecg_metadata(args.ecg_meta)

    ds = CohortECGDataset(cohort, ecg_meta, args.ecg_dir,
                          max_days_before=args.max_days)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False,
                        num_workers=args.num_workers,
                        pin_memory=torch.cuda.is_available())

    # ── Load encoder(s) ───────────────────────────────────────────────────────
    if args.model_type == "ecg_sim":
        print("Loading ECGSimilarityEncoder (biometric + echo-sim) …")
        main_encoder = load_sim_ecgfounder(args.checkpoint, args.ecg_repo_dir, device)
    else:
        print("Loading CLIP-trained ECGFounder …")
        main_encoder = load_clip_ecgfounder(args.checkpoint, args.ecg_repo_dir, device)

    uni_encoder = None
    if args.also_unimodal:
        print("Loading original ECGFounder (unimodal baseline) …")
        uni_encoder = load_original_ecgfounder(args.ecg_repo_dir, device)

    # ── Extract and save ──────────────────────────────────────────────────────
    def embed_and_save(encoder: nn.Module, save_dir: Path) -> None:
        encoder.eval()
        with torch.no_grad():
            for ecg_sigs, person_ids in tqdm(loader, desc=f"Embedding → {save_dir.name}"):
                ecg_sigs = ecg_sigs.to(device)
                out  = encoder(ecg_sigs)
                feat = (out[1] if isinstance(out, (tuple, list)) else out).cpu().numpy()
                for pid, emb in zip(person_ids, feat):
                    np.save(save_dir / f"{pid}.npy", emb)

    embed_and_save(main_encoder, output_dir / subdir)
    if uni_encoder:
        embed_and_save(uni_encoder, output_dir / "unimodal")

    print(f"\nDone. Embeddings saved → {output_dir / subdir}")
    if uni_encoder:
        print(f"           Unimodal → {output_dir / 'unimodal'}")


if __name__ == "__main__":
    main()
