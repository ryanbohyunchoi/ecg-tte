#!/usr/bin/env bash
# Spec-v2 cohort pipeline after gate A has passed (grid.py gate): fixed-cohort grids, assembly, summaries.
# Run detached:  tmux new-session -d -s v2coh 'bash scripts/v2_cohorts/run_all.sh'
set -euo pipefail
umask 077
PY=/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python
D=$(cd "$(dirname "$0")" && pwd)
L=/mnt/raid0/rbc58/ecg-tte/audits/claude-v2-cohorts/logs
$PY - <<'EOF'
import json
s = json.load(open("/mnt/raid0/rbc58/ecg-tte/audits/claude-v2-cohorts/cells/gate_status.json"))
assert s["passed"], "gate A failed"
EOF
$PY "$D/flags.py" apply > "$L/apply.log" 2>&1
for v in v2 v2old v2meas; do
  $PY "$D/grid.py" run --variant "$v" --workers 32 > "$L/run_$v.log" 2>&1
done
$PY "$D/grid.py" assemble > "$L/assemble.log" 2>&1
$PY "$D/summarize.py" run --workers 32 > "$L/summarize.log" 2>&1
echo ALL_DONE >> "$L/summarize.log"
