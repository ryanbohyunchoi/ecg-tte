#!/usr/bin/env bash
# run_bio_embed.sh
# Embed ECGs (<=30d from a qualifying echo) for up to 50K individuals with
# EF<40, using the existing BCL biometric encoder. Output for unsupervised
# LVSD subphenotyping.
#
# Usage: bash scripts/run_bio_embed.sh [--gpu 0,1] [--output-dir PATH]

set -euo pipefail

ECHO_META="/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet"
ECG_META="/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet"
ECG_DIR="/mnt/raid0/bb2238/signals/preprocessed/all_ecgs"
CHECKPOINT="/mnt/raid0/rbc58/cardiomap/experiments/ecg_biometric/best.pt"
ECG_REPO_DIR="/tmp/ECGFounder"
OUTPUT_DIR="/mnt/raid0/rbc58/bio/v1"

EF_THRESHOLD=40
WINDOW_DAYS=30
MAX_INDIVIDUALS=50000
BATCH_SIZE=256
NUM_WORKERS=8
GPU_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --gpu)             GPU_ID="$2"; shift 2 ;;
        --output-dir)      OUTPUT_DIR="$2"; shift 2 ;;
        --checkpoint)      CHECKPOINT="$2"; shift 2 ;;
        --ef-threshold)    EF_THRESHOLD="$2"; shift 2 ;;
        --window-days)     WINDOW_DAYS="$2"; shift 2 ;;
        --max-individuals) MAX_INDIVIDUALS="$2"; shift 2 ;;
        --batch-size)      BATCH_SIZE="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -n "$GPU_ID" ]]; then
    export CUDA_VISIBLE_DEVICES="$GPU_ID"
fi

mkdir -p "$OUTPUT_DIR"

python -u scripts/bio_embed.py \
    --echo-meta       "$ECHO_META" \
    --ecg-meta        "$ECG_META" \
    --ecg-dir         "$ECG_DIR" \
    --checkpoint      "$CHECKPOINT" \
    --ecg-repo-dir    "$ECG_REPO_DIR" \
    --output-dir      "$OUTPUT_DIR" \
    --ef-threshold    "$EF_THRESHOLD" \
    --window-days     "$WINDOW_DAYS" \
    --max-individuals "$MAX_INDIVIDUALS" \
    --batch-size      "$BATCH_SIZE" \
    --num-workers     "$NUM_WORKERS" \
    2>&1 | tee "$OUTPUT_DIR/bio_embed.log"

echo "Done → $OUTPUT_DIR"
