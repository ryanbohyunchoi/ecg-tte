#!/usr/bin/env bash
# v1.8 AF count-only feasibility screen (cohort -> ECG selection -> pooled counts + record overlap). No arm-level outcome or balance.
set -u; umask 077
cd /home/rbc58/github/ecg-tte/scripts
PY=/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python; S=/mnt/raid0/rbc58/ecg-tte/audits/claude-v18-screen; mkdir -p $S
one(){ t=$1
  $PY build_trial_cohort.py --trial $t --threads 8 --output-dir $S/$t-cohort > $S/$t-cohort.log 2>&1 || { echo "$t cohort FAILED" >> $S/status; return; }
  $PY select_cohort_ecgs.py select --cohort $S/$t-cohort/restricted_cohort.parquet --output-dir $S/$t-ecgsel > $S/$t-ecgsel.log 2>&1 || { echo "$t select FAILED" >> $S/status; return; }
  $PY v18/screen_feasibility.py --trial $t --threads 8 --cohort-dir $S/$t-cohort --selection-dir $S/$t-ecgsel --out-json $S/$t.json > $S/$t-screen.log 2>&1 || { echo "$t screen FAILED" >> $S/status; return; }
  echo "$t done" >> $S/status; }
L1="$1"; L2="$2"
( for t in $L1; do one $t; done ) &
( for t in $L2; do one $t; done ) &
wait; echo ALLDONE >> $S/status
