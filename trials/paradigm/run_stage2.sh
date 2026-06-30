#!/usr/bin/env bash
# trials/paradigm/run_stage2.sh — Stage 2 ECG embedding for PARADIGM-HF
# Run from repo root: bash trials/paradigm/run_stage2.sh
set -euo pipefail

OUT_ROOT="/home/rbc58/mnt/ecg-tte/runs"
EMBED_DIR="/mnt/raid0/rbc58/ecg-tte/embeddings"
ECG_DIR="/mnt/raid0/bb2238/signals/preprocessed/all_ecgs"
CHECKPOINT="/mnt/raid0/rbc58/cardiomap/experiments/ecg_biometric/best.pt"
ECG_REPO_DIR="/tmp/ECGFounder"
LOG="${OUT_ROOT}/paradigm_hf_stage2.log"

mkdir -p "$EMBED_DIR" "$(dirname "$LOG")"

echo "[stage2] Embedding PARADIGM-HF pool ECGs → $EMBED_DIR"
python -u scripts/stage2_embed.py \
    --pool-dir      "${OUT_ROOT}/paradigm_hf/pool" \
    --checkpoint    "$CHECKPOINT" \
    --output-dir    "$EMBED_DIR" \
    --ecg-dir       "$ECG_DIR" \
    --ecg-repo-dir  "$ECG_REPO_DIR" \
    --batch-size    256 \
    --num-workers   8 \
    2>&1 | tee "$LOG"

echo "[stage2] Done. Embeddings: $EMBED_DIR"
echo "  Log: $LOG"
