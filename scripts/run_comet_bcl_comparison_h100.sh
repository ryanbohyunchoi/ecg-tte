#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$HOME/github/ecg-tte"
BCL_COMPARE=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-comparison-XXXXXXXX)
export TMPDIR="$BCL_COMPARE/tmp"
mkdir -p "$TMPDIR"
echo "Comparison directory: $BCL_COMPARE"
COMET_PY=/home/rbc58/miniconda3/envs/mosaic/bin/python
COMET_R_ENV=/mnt/raid0/rbc58/ecg-tte/software/mice-r-v2-tyXlJyw1/env
unset R_HOME PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
export R_LIBS="$COMET_R_ENV/lib/R/library" R_LIBS_USER="$COMET_R_ENV/lib/R/library" R_LIBS_SITE="$COMET_R_ENV/lib/R/library"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
COMET_CPP=$("$COMET_PY" - <<'PY'
import sys
from pathlib import Path
p=Path(sys.prefix)/'lib/libstdc++.so.6'
if not p.is_file():raise SystemExit('Missing environment C++ runtime')
print(p.resolve())
PY
)
"$COMET_PY" scripts/prepare_comet_bcl_comparison.py \
  --full-report /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-full-lMQtaSyg/report \
  --output-dir "$BCL_COMPARE/linked"
# Scope the SciPy runtime workaround to Python; leave the R environment isolated.
LD_PRELOAD="$COMET_CPP" "$COMET_PY" scripts/compare_comet_clmbr.py --bcl --global-optimal \
  --embeddings "$BCL_COMPARE/linked" \
  --mice /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-v2-w5ZRCHzh/report \
  --rscript "$COMET_R_ENV/bin/Rscript" \
  --output-dir "$BCL_COMPARE/report" || {
    if [ -f "$BCL_COMPARE/report/summary.json" ]; then cat "$BCL_COMPARE/report/summary.json"; fi
    exit 1
  }
cat "$BCL_COMPARE/report/summary.json"
echo "Love plot: $BCL_COMPARE/report/comparison_love_plots.pdf"
