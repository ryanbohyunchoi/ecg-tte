#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
umask 077
REVIEW_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-observed-review-XXXXXXXX)
GRID_ROOT=/mnt/raid0/rbc58/ecg-tte/audits/comet-cosine-caliper-grid-XhRUMLhu
/home/rbc58/miniconda3/envs/mosaic/bin/python scripts/review_comet_representation_balance.py \
  --reports "$GRID_ROOT/caliper-0.20/report" "$GRID_ROOT/caliper-0.30/report" "$GRID_ROOT/caliper-0.40/report" \
  --output-dir "$REVIEW_RUN/report"
