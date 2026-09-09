#!/usr/bin/env bash
# trials/paradigm/run_stage3.sh — Stage 3 cohort filter for PARADIGM-HF
# Run from repo root: bash trials/paradigm/run_stage3.sh [--run-name NAME]
set -euo pipefail

OUT_ROOT="/home/rbc58/mnt/ecg-tte/runs"
RUN_NAME="default"
LOG_DIR="${OUT_ROOT}/_logs"

while [[ $# -gt 0 ]]; do
    case $1 in
        --run-name) RUN_NAME="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/paradigm_hf_stage3.log"

echo "[stage3] Filtering PARADIGM-HF cohort → run: $RUN_NAME"
python -u scripts/stage3_filter.py \
    --config              configs/paradigm_hf.yaml \
    --pool-dir            "${OUT_ROOT}/paradigm_hf/pool" \
    --output-dir          "${OUT_ROOT}/paradigm_hf" \
    --run-name            "$RUN_NAME" \
    --min-fills           2 \
    --persistence-days    180 \
    2>&1 | tee "$LOG"

echo "[stage3] Done."
echo "  Cohort : ${OUT_ROOT}/paradigm_hf/runs/${RUN_NAME}/comet_cohort.parquet"
echo "  Attrition: ${OUT_ROOT}/paradigm_hf/runs/${RUN_NAME}/attrition.csv"
echo "  Log    : $LOG"
