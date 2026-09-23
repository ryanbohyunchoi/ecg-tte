#!/usr/bin/env bash
# Run by Ryan on H100 only. Fresh RAID output; existing artifacts are read-only.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
umask 077
CLMBR_PY=/home/rbc58/miniconda3/envs/mosaic/bin/python
CLMBR_CPP_RUNTIME=$("$CLMBR_PY" -c 'import sys; from pathlib import Path; print((Path(sys.prefix)/"lib/libstdc++.so.6").resolve())')
test -f "$CLMBR_CPP_RUNTIME"
export LD_PRELOAD="$CLMBR_CPP_RUNTIME"
"$CLMBR_PY" -c 'from scipy.optimize import linear_sum_assignment; print("Assignment solver import passed")'
COMET_R_ENV=/mnt/raid0/rbc58/ecg-tte/software/mice-r-v2-tyXlJyw1/env
unset R_HOME
export R_LIBS="$COMET_R_ENV/lib/R/library"
export R_LIBS_USER="$COMET_R_ENV/lib/R/library"
export R_LIBS_SITE="$COMET_R_ENV/lib/R/library"
# Keep numerical libraries single-threaded for reproducible ties and small matrices.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
GRID_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-cosine-caliper-grid-XXXXXXXX)
export TMPDIR="$GRID_RUN/tmp"
mkdir -p "$TMPDIR"
echo "Grid directory: $GRID_RUN"
failed=0
for cutoff in 0.20 0.30 0.40; do
  echo "Running cosine caliper $cutoff"
  "$CLMBR_PY" scripts/compare_comet_clmbr.py --global-optimal --cosine-caliper "$cutoff" \
    --embeddings /mnt/raid0/rbc58/ecg-tte/audits/comet-clmbr-full-NAyb4G2x/report \
    --mice /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-v2-w5ZRCHzh/report \
    --rscript "$COMET_R_ENV/bin/Rscript" \
    --output-dir "$GRID_RUN/caliper-$cutoff/report" || failed=1
done
"$CLMBR_PY" scripts/summarize_comet_calipers.py "$GRID_RUN"
echo "Saved grid summary: $GRID_RUN/grid_summary.json"
exit "$failed"
