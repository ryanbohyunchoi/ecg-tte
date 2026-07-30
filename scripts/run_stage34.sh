#!/usr/bin/env bash
# run_stage34.sh
# Usage: bash scripts/run_stage34.sh [--trials "plato poet_copd"] [--denominator strict|both] [--run-name default]
#
# For each trial: stage3_filter.py (cohort + attrition) then stage4_analyze.py
# (comparator ladder: unadjusted/adjusted Cox, PSM-sparse/rich, ECG-NN, hybrid).
# Reads treated/control arm names, trial display name, and published HR from
# configs/<trial>.yaml. Per-trial results land in
# $OUTPUT_ROOT/<trial>/runs/<run-name>/results_summary.csv

set -euo pipefail

# ── Paths (edit these) ────────────────────────────────────────────────────────
OUTPUT_ROOT="/home/rbc58/mnt/ecg-tte"
EMBED_DIR="/mnt/raid0/rbc58/ecg-tte/embeddings"
CONFIG_DIR="configs"
LOG_DIR="$OUTPUT_ROOT/_logs"

RUN_NAME="default"
DENOMINATOR="strict"

# ── Parse args ────────────────────────────────────────────────────────────────
TRIALS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --trials)      read -ra TRIALS <<< "$2"; shift 2 ;;
        --denominator) DENOMINATOR="$2"; shift 2 ;;
        --run-name)    RUN_NAME="$2"; shift 2 ;;
        --embed-dir)   EMBED_DIR="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

mkdir -p "$LOG_DIR"

if [[ ${#TRIALS[@]} -eq 0 ]]; then
    mapfile -t TRIALS < <(ls "$CONFIG_DIR"/*.yaml | grep -v '_schema' | xargs -n1 basename | sed 's/\.yaml$//')
fi

OK_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

for trial in "${TRIALS[@]}"; do
    cfg="$CONFIG_DIR/${trial}.yaml"
    pool_dir="$OUTPUT_ROOT/$trial/pool"
    out_dir="$OUTPUT_ROOT/$trial"
    run_dir="$out_dir/runs/$RUN_NAME"
    log="$LOG_DIR/${trial}_stage34.log"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Trial: $trial"

    if [[ ! -f "$pool_dir/ecg_candidates.parquet" ]]; then
        echo "  SKIP — no pool at $pool_dir"
        (( SKIP_COUNT++ )) || true
        continue
    fi

    echo "  [stage3] filtering → $run_dir"
    set +e
    python -u scripts/stage3_filter.py \
        --config "$cfg" \
        --pool-dir "$pool_dir" \
        --output-dir "$out_dir" \
        --run-name "$RUN_NAME" \
        2>&1 | tee "$log"
    rc=${PIPESTATUS[0]}
    set -e
    if [[ $rc -ne 0 ]]; then
        echo "  [stage3] FAILED (exit $rc) — skipping trial"
        (( FAIL_COUNT++ )) || true
        continue
    fi

    # ── Pull arm names / display name / published HR from the trial config ────
    read -r treated control name ref_hr <<< "$(python3 - "$cfg" <<'PYEOF'
import sys, yaml
d = yaml.safe_load(open(sys.argv[1]))
arms = d.get("arms", [])
treated = next(a["name"] for a in arms if a.get("role") == "treated")
control = next(a["name"] for a in arms if a.get("role") == "control")
name = d["trial"]["name"].replace(" ", "_")
hr = d["trial"].get("published_hr")
print(treated, control, name, hr if hr is not None else "NA")
PYEOF
)"

    echo "  [stage4] analyzing → $run_dir"
    args=(
        --cohort      "$run_dir/comet_cohort.parquet"
        --embed-dir   "$EMBED_DIR"
        --output-dir  "$run_dir"
        --treated-arm "$treated"
        --control-arm "$control"
        --trial-name  "$name"
        --denominator "$DENOMINATOR"
        --drug-pool   "$pool_dir/drug_master_pool.parquet"
    )
    if [[ "$ref_hr" != "NA" ]]; then
        args+=(--reference-hr "$ref_hr")
    fi

    set +e
    python -u scripts/stage4_analyze.py "${args[@]}" 2>&1 | tee -a "$log"
    rc=${PIPESTATUS[0]}
    set -e
    if [[ $rc -ne 0 ]]; then
        echo "  [stage4] FAILED (exit $rc)"
        (( FAIL_COUNT++ )) || true
        continue
    fi

    echo "  [done] → $run_dir/results_summary.csv"
    (( OK_COUNT++ )) || true
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Stage3+4 complete: OK=$OK_COUNT  SKIPPED=$SKIP_COUNT  FAILED=$FAIL_COUNT"
echo "Logs: $LOG_DIR"
