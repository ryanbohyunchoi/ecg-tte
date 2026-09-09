#!/usr/bin/env bash
# run_stage2.sh
# Usage: bash scripts/run_stage2.sh [--trials "plato poet_copd"] [--checkpoint PATH] [--output-dir PATH]
#
# Runs stage2_embed.py for each trial's pool/ecg_candidates.parquet.
# Embeddings are written to one shared --output-dir (keyed by fileID), so
# fileIDs already embedded for one trial are skipped (resumable) when
# processing the next trial.

set -euo pipefail

# ── Paths (edit these) ────────────────────────────────────────────────────────
OUTPUT_ROOT="/home/rbc58/mnt/ecg-tte"
ECG_DIR="/mnt/raid0/bb2238/signals/preprocessed/all_ecgs"
ECG_REPO_DIR="/tmp/ECGFounder"
CHECKPOINT="/mnt/raid0/rbc58/cardiomap/experiments/ecg_biometric/best.pt"
EMBED_DIR="/mnt/raid0/rbc58/ecg-tte/embeddings"
LOG_DIR="$OUTPUT_ROOT/_logs"

CONFIG_DIR="configs"
BATCH_SIZE=256
NUM_WORKERS=8
GPU_ID=""   # e.g. "0" or "0,1" — sets CUDA_VISIBLE_DEVICES (comma-list = DataParallel)

# ── Parse args ────────────────────────────────────────────────────────────────
TRIALS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --trials)      read -ra TRIALS <<< "$2"; shift 2 ;;
        --checkpoint)  CHECKPOINT="$2"; shift 2 ;;
        --output-dir)  EMBED_DIR="$2"; shift 2 ;;
        --ecg-dir)     ECG_DIR="$2"; shift 2 ;;
        --batch-size)  BATCH_SIZE="$2"; shift 2 ;;
        --gpu)         GPU_ID="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -n "$GPU_ID" ]]; then
    export CUDA_VISIBLE_DEVICES="$GPU_ID"
fi

mkdir -p "$EMBED_DIR" "$LOG_DIR"

# Collect trial names (from configs/, or --trials override)
if [[ ${#TRIALS[@]} -eq 0 ]]; then
    mapfile -t TRIALS < <(ls "$CONFIG_DIR"/*.yaml | grep -v '_schema' | xargs -n1 basename | sed 's/\.yaml$//')
fi

for trial in "${TRIALS[@]}"; do
    pool_dir="$OUTPUT_ROOT/$trial/pool"
    log="$LOG_DIR/${trial}_stage2.log"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Trial: $trial"

    if [[ ! -f "$pool_dir/ecg_candidates.parquet" ]]; then
        echo "  [stage2] SKIP — no ecg_candidates.parquet at $pool_dir"
        continue
    fi

    echo "  [stage2] embedding pool ECGs → $EMBED_DIR"
    python -u scripts/stage2_embed.py \
        --pool-dir     "$pool_dir" \
        --checkpoint   "$CHECKPOINT" \
        --output-dir   "$EMBED_DIR" \
        --ecg-dir      "$ECG_DIR" \
        --ecg-repo-dir "$ECG_REPO_DIR" \
        --batch-size   "$BATCH_SIZE" \
        --num-workers  "$NUM_WORKERS" \
        2>&1 | tee "$log"

    echo "  [stage2] done → $EMBED_DIR"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Stage2 complete for ${#TRIALS[@]} trial(s)"
echo "Embeddings: $EMBED_DIR"
echo "Logs: $LOG_DIR"
