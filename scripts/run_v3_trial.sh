#!/usr/bin/env bash
# v3 rerun (Ryan decisions 2026-09-24): primary = outpatient initiators (re-imputed, sklearn
# chained equations for every trial incl. COMET), secondary = all initiators; expanded
# physiology evaluation panel; sparse set with dx-all and hdPS comparators.
# Usage: run_v3_trial.sh N TRIAL_KEY COHORT_DIR ECG_DIR CLMBR_GLOB PHENO PANEL DICT PROG
set -euo pipefail; umask 077
N=$1; T=$2; COH=$3; ECGD=$4; EHR=$5; PH=$6; PANEL=$7; DICT=$8; PROG=$9
A=/mnt/raid0/rbc58/ecg-tte/audits; PY=/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python
cd "$(dirname "$0")"; ST=$A/claude-v3-$N.status; say(){ echo "$(date +%H:%M:%S) $*" >> $ST; }
ECG="$ECGD/restricted_embeddings_part-*.parquet"
say start
$PY make_outpatient_cohort.py --cohort-dir $COH --output-dir $A/claude-$N-cohort-op > /dev/null
$PY build_core_baseline.py --trial $T --roster $A/claude-$N-cohort-op/restricted_cohort.parquet --output-dir $A/claude-$N-baseline-op > /dev/null
if [ "$T" = comet ]; then
  $PY build_core_baseline.py --trial comet --roster $COH/restricted_cohort.parquet --output-dir $A/claude-comet-baseline-omop > /dev/null
  BALL=$A/claude-comet-baseline-omop
else BALL=$A/claude-$N-baseline-v1; fi
$PY build_physiology_panel.py --roster $COH/restricted_cohort.parquet --output-dir $A/claude-$N-physpanel-v1 > /dev/null
say "cohort/baseline/physpanel done"
export PHYS=$A/claude-$N-physpanel-v1/restricted_physiology_panel.parquet
METHOD_SET=sparse ./run_longtail_v2.sh $A/claude-v3-sparse-$N $A/claude-$N-baseline-op $PANEL $DICT "$ECG" "$EHR" $PH $PROG $T > /dev/null 2>&1; say "primary sparse done"
./run_longtail_v2.sh $A/claude-v3-full-$N $A/claude-$N-baseline-op $PANEL $DICT "$ECG" "$EHR" $PH $PROG $T > /dev/null 2>&1; say "primary full done"
METHOD_SET=sparse ./run_longtail_v2.sh $A/claude-v3-sparse-all-$N $BALL $PANEL $DICT "$ECG" "$EHR" $PH $PROG $T > /dev/null 2>&1; say "secondary sparse done"
./run_longtail_v2.sh $A/claude-v3-full-all-$N $BALL $PANEL $DICT "$ECG" "$EHR" $PH $PROG $T > /dev/null 2>&1; say "secondary full done"
touch $A/claude-v3-$N.DONE
