#!/usr/bin/env bash
# trials/paradigm/run_stage4.sh — Stage 4 analysis for PARADIGM-HF
# Run from repo root: bash trials/paradigm/run_stage4.sh [--run-name NAME] [--denominator strict|both]
set -euo pipefail

OUT_ROOT="/home/rbc58/mnt/ecg-tte/runs"
EMBED_DIR="/mnt/raid0/rbc58/ecg-tte/embeddings"
RUN_NAME="default"
DENOMINATOR="strict"
LOG_DIR="${OUT_ROOT}/_logs"

while [[ $# -gt 0 ]]; do
    case $1 in
        --run-name)    RUN_NAME="$2"; shift 2 ;;
        --denominator) DENOMINATOR="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/paradigm_hf_stage4.log"
RUN_DIR="${OUT_ROOT}/paradigm_hf/runs/${RUN_NAME}"
COHORT="${RUN_DIR}/comet_cohort.parquet"

if [[ ! -f "$COHORT" ]]; then
    echo "[stage4] ERROR: cohort not found at $COHORT — run stage3 first."
    exit 1
fi

echo "[stage4] Analyzing PARADIGM-HF → run: $RUN_NAME  denominator: $DENOMINATOR"
python -u scripts/stage4_analyze.py \
    --cohort           "$COHORT" \
    --output-dir       "$RUN_DIR" \
    --treated-arm      sacubitril_valsartan \
    --control-arm      acei \
    --trial-name       PARADIGM-HF \
    --reference-hr     0.80 \
    --drug-pool        "${OUT_ROOT}/paradigm_hf/pool/drug_master_pool.parquet" \
    --exclude-psm-cols acei_arb_90d \
    --event-col        event_death \
    --time-col         time_to_death \
    2>&1 | tee "$LOG"

# acei_arb_90d excluded from PSM: sacubitril/valsartan contains valsartan (ARB),
# so this covariate is structurally confounded with treatment assignment.

echo "[stage4] Done."
echo "  Results: ${RUN_DIR}/results_summary.csv"
echo "  Log    : $LOG"
