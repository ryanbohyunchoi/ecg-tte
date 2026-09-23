#!/usr/bin/env bash
# Run on H100 only, in a session with one allocated GPU. All new files stay on RAID.
set -euo pipefail
umask 077
cd "$HOME/github/ecg-tte"
mkdir -p /mnt/raid0/rbc58/ecg-tte/software /mnt/raid0/rbc58/ecg-tte/audits
BCL_BUILD=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/software/bcl-smoke-runtime-XXXXXXXX)
export CONDA_PKGS_DIRS=/mnt/raid0/rbc58/ecg-tte/software/conda-pkgs
export TMPDIR="$BCL_BUILD/tmp"
export XDG_CACHE_HOME="$BCL_BUILD/cache"
export PYTHONNOUSERSITE=1
unset PYTHONPATH PYTHONHOME LD_PRELOAD
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$CONDA_PKGS_DIRS"
echo "Runtime directory: $BCL_BUILD"
git clone https://github.com/CarDS-Yale/ECG-signal-pipeline.git "$BCL_BUILD/upstream"
git -C "$BCL_BUILD/upstream" checkout --detach d359c04d1f5e6c810f76751777535918870704b7
conda env create --prefix "$BCL_BUILD/env" --file "$BCL_BUILD/upstream/torch_env.yml"
conda list --prefix "$BCL_BUILD/env" --explicit > "$BCL_BUILD/conda-explicit.txt"
BCL_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-smoke-XXXXXXXX)
echo "Report directory: $BCL_RUN/report"
# Preserve the scheduler's CUDA_VISIBLE_DEVICES; the wrapper uses one visible GPU.
conda run --no-capture-output --prefix "$BCL_BUILD/env" python scripts/run_comet_bcl_smoke.py \
  --prep-report /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-smoke-prep-SWznZWZE/report \
  --upstream-repo "$BCL_BUILD/upstream" \
  --output-dir "$BCL_RUN/report" || {
    if [ -f "$BCL_RUN/report/summary.json" ]; then cat "$BCL_RUN/report/summary.json"; fi
    exit 1
  }
cat "$BCL_RUN/report/summary.json"
