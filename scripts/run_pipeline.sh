#!/usr/bin/env bash
# run_pipeline.sh
# Usage: bash scripts/run_pipeline.sh [--config-dir configs/] [--trials "comet aristotle rales"]
# Runs stage0 feasibility for each trial; if GO, runs stage1 build_pool.
# Logs per-trial output to $LOG_DIR.

set -euo pipefail

# ── Paths (edit these) ────────────────────────────────────────────────────────
PERSON_PARQUET="/home/rbc58/mnt/ascvd/omop_database/person/person.parquet"
CONDITION_DIR="/home/rbc58/mnt/ascvd/omop_database/condition_occurrence"
DRUG_MASTER="/home/rbc58/mnt/ecg-tte/drug_master.parquet"
ECHO_META="/home/rbc58/mnt/ecg-tte/metadata/echo_accession_number.parquet"
ECG_META="/home/rbc58/mnt/ecg-tte/metadata/ecg_metadata.parquet"
DEATH_PARQUET="/home/rbc58/mnt/ascvd/omop_database/death/death.parquet"
OUTPUT_ROOT="/home/rbc58/mnt/ecg-tte"
FEASIBILITY_DIR="/home/rbc58/mnt/ecg-tte/_feasibility"
LOG_DIR="/home/rbc58/mnt/ecg-tte/_logs"

CONFIG_DIR="configs"
SKIP_STAGE0=0   # set to 1 to skip feasibility and run stage1 for all trials

# ── Parse args ────────────────────────────────────────────────────────────────
TRIALS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --config-dir) CONFIG_DIR="$2"; shift 2 ;;
        --trials)     read -ra TRIALS <<< "$2"; shift 2 ;;
        --skip-stage0) SKIP_STAGE0=1; shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

mkdir -p "$FEASIBILITY_DIR" "$LOG_DIR"

# Collect config files
if [[ ${#TRIALS[@]} -gt 0 ]]; then
    CONFIG_FILES=()
    for t in "${TRIALS[@]}"; do
        CONFIG_FILES+=("$CONFIG_DIR/${t}.yaml")
    done
else
    mapfile -t CONFIG_FILES < <(ls "$CONFIG_DIR"/*.yaml | grep -v '_schema')
fi

COMMON_ARGS=(
    --person-parquet  "$PERSON_PARQUET"
    --condition-dir   "$CONDITION_DIR"
    --drug-master     "$DRUG_MASTER"
    --echo-meta       "$ECHO_META"
    --ecg-meta        "$ECG_META"
    --death-parquet   "$DEATH_PARQUET"
)

GO_COUNT=0
NOGO_COUNT=0
SKIPPED_COUNT=0

for cfg in "${CONFIG_FILES[@]}"; do
    trial=$(basename "$cfg" .yaml)
    log="$LOG_DIR/${trial}.log"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Trial: $trial"

    if [[ $SKIP_STAGE0 -eq 1 ]]; then
        verdict="GO"
    else
        echo "  [stage0] feasibility check → $log"
        python -u scripts/stage0_feasibility.py \
            --config "$cfg" \
            "${COMMON_ARGS[@]}" \
            --output-dir "$FEASIBILITY_DIR" \
            2>&1 | tee "$log"

        json="$FEASIBILITY_DIR/feasibility_${trial}.json"
        if [[ ! -f "$json" ]]; then
            echo "  [stage0] ERROR: no JSON output, skipping stage1"
            (( SKIPPED_COUNT++ )) || true
            continue
        fi
        verdict=$(python -c "import json; print(json.load(open('$json'))['go_nogo'])")
    fi

    if [[ "$verdict" == "GO" ]]; then
        echo "  [stage0] GO — launching stage1"
        (( GO_COUNT++ )) || true
        python -u scripts/stage1_build_pool.py \
            --config "$cfg" \
            "${COMMON_ARGS[@]}" \
            --output-root "$OUTPUT_ROOT" \
            2>&1 | tee -a "$log"
        echo "  [stage1] done → $OUTPUT_ROOT/$trial/pool/"
    else
        echo "  [stage0] NO-GO — skipping stage1"
        (( NOGO_COUNT++ )) || true
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Pipeline complete: GO=$GO_COUNT  NO-GO=$NOGO_COUNT  SKIPPED=$SKIPPED_COUNT"
echo "Logs: $LOG_DIR"
