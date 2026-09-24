#!/usr/bin/env bash
# Full per-trial pipeline (docs/RUN_LONGTAIL_REPLICATION.md), unattended.
# Usage: run_trial_pipeline.sh TRIAL_KEY NAME COHORT_DIR BCL_GPU CLMBR_GPU
#   COHORT_DIR = existing build_trial_cohort.py output. Stops with FAILED_FEASIBILITY if the
#   smaller arm with a selected ECG is < MIN_ARM (default 300).
set -euo pipefail
umask 077
T=$1; N=$2; COH=$3; GPU_BCL=$4; GPU_CLM=$5; MIN_ARM=${MIN_ARM:-300}
ROOT=/mnt/raid0/rbc58/ecg-tte; A=$ROOT/audits; SH=$ROOT/shared
PY=$ROOT/software/tte-analysis/bin/python
BCL=$ROOT/software/bcl-smoke-runtime-zZ5FVVsd; MOS=$ROOT/software/mosaic-env
CK=/mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/CNN0_lead_time_transformer_10s_500Hz_BCL_LR0.0001_Dropout0.5_08_26_2026/trained_12lead_30.pt
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
STATUS=$A/claude-$N-pipeline.status
say(){ echo "$(date +%H:%M:%S) $*" | tee -a "$STATUS"; }
ROSTER=$COH/restricted_cohort.parquet
say "start $T"
$PY build_core_baseline.py --trial $T --roster $ROSTER --output-dir $A/claude-$N-baseline-v1 > $A/claude-$N-baseline-v1.log 2>&1
$PY build_preindex_panel.py --cohort-csv $ROSTER --omop-root /mnt/raid0/rbc58/omop/gold --output-dir $A/claude-$N-panel-v2 > /dev/null
$PY select_cohort_ecgs.py select --cohort $ROSTER --output-dir $A/claude-$N-bcl/input > /dev/null
MINARM=$($PY -c "
import pandas as pd
c=pd.read_parquet('$ROSTER'); s=pd.read_parquet('$A/claude-$N-bcl/input/restricted_selection.parquet')
print(int(c[c.patient_key.isin(s.patient_key)].treated.value_counts().reindex([0,1]).fillna(0).min()))")
say "baseline/panel/ecg-select done; smaller arm with ECG = $MINARM"
if [ "$MINARM" -lt "$MIN_ARM" ]; then say "FAILED_FEASIBILITY"; touch $A/claude-$N-FAILED_FEASIBILITY; exit 0; fi
# GPU jobs in parallel: BCL and MEDS->CLMBR
( CUDA_VISIBLE_DEVICES=$GPU_BCL $BCL/env/bin/python bcl_embed_uv.py --upstream-dir $BCL/upstream -- --checkpoint-path $CK \
    --input-file $A/claude-$N-bcl/input/restricted_input.csv --formats-csv $A/claude-$N-bcl/input/restricted_formats_no250.csv \
    --data-roots /mnt/raid0/bb2238/signals/preprocessed/all_ecgs --output-dir $A/claude-$N-bcl/embeddings --batch-size 64 \
    --num-workers 8 --shard-size 512 --no-quality-filter --no-deduplicate --no-partial --no-amp --no-overwrite \
    --no-ddp-autodetect > $A/claude-$N-bcl/run.log 2>&1 ) &
PID_BCL=$!
( mkdir $SH/claude-$N-meds-v2 && $PY build_comet_meds.py --source-report $COH --gold-root /mnt/raid0/rbc58/omop/gold \
    --concept /mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv --output-dir $SH/claude-$N-meds-v2/meds > $SH/claude-$N-meds-v2/build.log 2>&1
  grep -q complete_cohort_meds $SH/claude-$N-meds-v2/meds/summary.json
  mkdir $A/claude-$N-clmbr-codeonly
  CUDA_VISIBLE_DEVICES=$GPU_CLM LD_PRELOAD=$MOS/lib/libstdc++.so.6 $MOS/bin/python encode_comet_clmbr.py \
    --meds-root $SH/claude-$N-meds-v2/meds --model-root /mnt/raid0/eo287/clmbr --numeric-mode code-only --max-tokens 4096 \
    --limit 0 --output-dir $A/claude-$N-clmbr-codeonly/report > $A/claude-$N-clmbr-codeonly/run.log 2>&1 ) &
PID_CLM=$!
# prognostic reference meanwhile (CPU)
R=$A/claude-$N-progref-v1
$PY build_prognostic_reference.py --trial $T --cohort $ROSTER --output-dir $R/reference > /dev/null
$PY build_core_baseline.py --trial $T --roster $R/reference/restricted_reference.parquet --imputations 0 --output-dir $R/baseline > /dev/null
$PY build_preindex_panel.py --cohort-csv $R/reference/restricted_reference.parquet --omop-root /mnt/raid0/rbc58/omop/gold \
  --dictionary $A/claude-$N-panel-v2/panel_dictionary.csv --output-dir $R/panel > /dev/null
$PY fit_prognostic_score.py --reference $R/reference/restricted_reference.parquet --reference-baseline $R/baseline/restricted_baseline_observed.parquet \
  --reference-panel $R/panel/restricted_panel.parquet --cohort-baseline $A/claude-$N-baseline-v1/restricted_baseline_observed.parquet \
  --cohort-panel $A/claude-$N-panel-v2/restricted_panel.parquet --output-dir $R/scores-v3 > /dev/null
say "prognostic scores done"
wait $PID_BCL; say "BCL done: $(grep -c 'shards complete' $A/claude-$N-bcl/run.log) completion line"
$PY select_cohort_ecgs.py link --selection-dir $A/claude-$N-bcl/input --embeddings-dir $A/claude-$N-bcl/embeddings > $A/claude-$N-bcl/link.json
$PY train_ecg_phenotype_heads.py --phenotype-set $A/claude-ecg-phenotype-set/restricted_phenotype_set.parquet \
  --phenotype-embeddings $A/claude-ecg-phenotype-set/embeddings --cohort-embeddings-glob "$A/claude-$N-bcl/restricted_embeddings_part-*.parquet" \
  --exclude-cohort $ROSTER --output-dir $A/claude-$N-phenotypes > /dev/null
wait $PID_CLM; say "CLMBR done"
$PY probe_embeddings.py --baseline-observed $A/claude-$N-baseline-v1/restricted_baseline_observed.parquet \
  --ecg-glob "$A/claude-$N-bcl/restricted_embeddings_part-*.parquet" \
  --ehr-glob "$A/claude-$N-clmbr-codeonly/report/restricted_embeddings_part-*.parquet" --out $A/claude-$N-bcl/probe_gate.json > /dev/null
ARGS=($A/claude-$N-baseline-v1 $A/claude-$N-panel-v2/restricted_panel.parquet $A/claude-$N-panel-v2/panel_dictionary.csv
      "$A/claude-$N-bcl/restricted_embeddings_part-*.parquet" "$A/claude-$N-clmbr-codeonly/report/restricted_embeddings_part-*.parquet"
      $A/claude-$N-phenotypes/restricted_cohort_phenotypes.parquet $R/scores-v3/restricted_prognostic_scores.parquet $T)
./run_longtail_v2.sh $A/claude-longtail-v2-$N "${ARGS[@]}" > $A/claude-longtail-v2-$N.log 2>&1
say "full grid done"
METHOD_SET=sparse ./run_longtail_v2.sh $A/claude-sparse-dx-$N "${ARGS[@]}" > $A/claude-sparse-dx-$N.log 2>&1
say "sparse grid done"; touch $A/claude-$N-PIPELINE_DONE
