#!/usr/bin/env bash
# Long-tail balance v2 grid: imputations 1..5 x split seeds 0..4, run in parallel, then pooled.
# Usage: run_longtail_v2.sh OUT_DIR BASELINE_DIR PANEL DICTIONARY ECG_GLOB EHR_GLOB PHENOTYPES PROG_SCORES [LABEL]
# Launch detached:  setsid nohup scripts/run_longtail_v2.sh ... > OUT.log 2>&1 < /dev/null &
set -euo pipefail
umask 077
OUT=$1; BASE=$2; PANEL=$3; DICT=$4; ECG=$5; EHR=$6; PH=$7; PROG=$8; LABEL=${9:-}; MSET=${METHOD_SET:-full}
PY=${PY:-/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir "$OUT"   # refuses to reuse an existing run
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8
for imp in 1 2 3 4 5; do for seed in 0 1 2 3 4; do
  "$PY" "$HERE/eval_longtail_balance.py" --baseline-dir "$BASE" --imputation $imp --split-seed $seed \
    --panel "$PANEL" --panel-dictionary "$DICT" --ecg-emb-glob "$ECG" --ehr-emb-glob "$EHR" \
    --ecg-phenotypes "$PH" --prognostic-scores "$PROG" --label "$LABEL" --method-set "$MSET" --output-dir "$OUT" \
    > "$OUT/log_imp${imp}_seed${seed}.txt" 2>&1 &
  while [ "$(jobs -rp | wc -l)" -ge 12 ]; do sleep 2; done
done; done
wait
"$PY" "$HERE/summarize_longtail.py" "$OUT"
touch "$OUT/ALL_DONE"
