#!/usr/bin/env bash
# Reuse the successful smoke environment; no package installation or old-output reuse.
set -euo pipefail
umask 077
cd "$HOME/github/ecg-tte"
BCL_RUNTIME=/mnt/raid0/rbc58/ecg-tte/software/bcl-smoke-runtime-zZ5FVVsd
BCL_FULL=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-full-XXXXXXXX)
export TMPDIR="$BCL_FULL/tmp" XDG_CACHE_HOME="$BCL_FULL/cache" PYTHONNOUSERSITE=1
unset PYTHONPATH PYTHONHOME LD_PRELOAD
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
echo "Run directory: $BCL_FULL"
/home/rbc58/miniconda3/envs/mosaic/bin/python scripts/prepare_comet_bcl_smoke.py --full \
  --report /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-input-v2-C9ftzPbQ/report \
  --output-dir "$BCL_FULL/input"
conda list --prefix "$BCL_RUNTIME/env" --explicit > "$BCL_FULL/conda-explicit.txt"
conda run --no-capture-output --prefix "$BCL_RUNTIME/env" python scripts/run_comet_bcl_smoke.py \
  --prep-report "$BCL_FULL/input" \
  --upstream-repo "$BCL_RUNTIME/upstream" \
  --reference-smoke /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-smoke-Ik5VklyT/report \
  --output-dir "$BCL_FULL/report" || {
    if [ -f "$BCL_FULL/report/summary.json" ]; then cat "$BCL_FULL/report/summary.json"; fi
    exit 1
  }
cat "$BCL_FULL/report/summary.json"
