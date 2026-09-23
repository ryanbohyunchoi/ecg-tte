#!/usr/bin/env bash
# Run by Ryan on H100 only. Fresh RAID output; existing artifacts are read-only.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
umask 077
COMET_R_ENV=/mnt/raid0/rbc58/ecg-tte/software/mice-r-v2-tyXlJyw1/env
unset R_HOME
export R_LIBS="$COMET_R_ENV/lib/R/library"
export R_LIBS_USER="$COMET_R_ENV/lib/R/library"
export R_LIBS_SITE="$COMET_R_ENV/lib/R/library"
# Keep numerical libraries single-threaded for reproducible ties and small matrices.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
COMPARE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-cosine-comparison-v2-XXXXXXXX)
export TMPDIR="$COMPARE_RUN/tmp"
mkdir -p "$TMPDIR"
echo "Report directory: $COMPARE_RUN/report"
/home/rbc58/miniconda3/envs/mosaic/bin/python scripts/compare_comet_clmbr.py --metoprolol-anchor \
  --embeddings /mnt/raid0/rbc58/ecg-tte/audits/comet-clmbr-full-NAyb4G2x/report \
  --mice /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-v2-w5ZRCHzh/report \
  --rscript "$COMET_R_ENV/bin/Rscript" \
  --output-dir "$COMPARE_RUN/report" || {
    cat "$COMPARE_RUN/report/summary.json"
    exit 1
  }
cat "$COMPARE_RUN/report/summary.json"
