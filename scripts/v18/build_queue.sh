#!/usr/bin/env bash
# v1.8 AF confirmation trials: build to the analysis-ready state of v16_engine.load_trial (no grid, no phase 2, no
# PS / matching / balance / HR). Specs registered (commit 6221162) and V18 registry committed before this ran.
set -u; umask 077
cd /home/rbc58/github/ecg-tte/scripts
ROOT=/mnt/raid0/rbc58/ecg-tte; A=$ROOT/audits; SH=$ROOT/shared; PY=$ROOT/software/tte-analysis/bin/python
BCL=$ROOT/software/bcl-smoke-runtime-zZ5FVVsd; MOS=$ROOT/software/mosaic-env; Q=$A/claude-v18-trials
CK=/mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/CNN0_lead_time_transformer_10s_500Hz_BCL_LR0.0001_Dropout0.5_08_26_2026/trained_12lead_30.pt
ST=$Q/status; say(){ echo "$(date +%H:%M:%S) $*" >> $ST; }
TH=8
waitgpu(){ while true; do u=$(nvidia-smi -i $1 --query-gpu=memory.used --format=csv,noheader,nounits); [ "$u" -lt 1000 ] && return; sleep 60; done; }
one(){ N=$1; T=$2; G1=$3; G2=$4; C=$A/claude-$N-cohort-v1; ROSTER=$C/restricted_cohort.parquet; L=$Q/logs/$N; mkdir -p $L
  say "$N start"
  [ -d $C ] || $PY build_trial_cohort.py --trial $T --threads $TH --output-dir $C > $L/cohort.log 2>&1 || { say "$N cohort FAILED"; return; }
  [ -d $A/claude-$N-baseline-v11 ] || $PY build_core_baseline.py --trial $T --roster $ROSTER --threads $TH --output-dir $A/claude-$N-baseline-v11 > $L/baseline.log 2>&1 || { say "$N baseline FAILED"; return; }
  [ -d $A/claude-$N-panel-v2 ] || $PY build_preindex_panel.py --cohort-csv $ROSTER --omop-root /mnt/raid0/rbc58/omop/gold --threads $TH --output-dir $A/claude-$N-panel-v2 > $L/panel.log 2>&1 || { say "$N panel FAILED"; return; }
  [ -d $A/claude-$N-bcl/input ] || $PY select_cohort_ecgs.py select --cohort $ROSTER --output-dir $A/claude-$N-bcl/input > $L/select.log 2>&1 || { say "$N select FAILED"; return; }
  waitgpu $G1; say "$N BCL on GPU $G1"
  ( CUDA_VISIBLE_DEVICES=$G1 $BCL/env/bin/python bcl_embed_uv.py --upstream-dir $BCL/upstream -- --checkpoint-path $CK \
    --input-file $A/claude-$N-bcl/input/restricted_input.csv --formats-csv $A/claude-$N-bcl/input/restricted_formats_no250.csv \
    --data-roots /mnt/raid0/bb2238/signals/preprocessed/all_ecgs --output-dir $A/claude-$N-bcl/embeddings --batch-size 64 \
    --num-workers 4 --shard-size 512 --no-quality-filter --no-deduplicate --no-partial --no-amp --no-overwrite \
    --no-ddp-autodetect > $A/claude-$N-bcl/run.log 2>&1 ) & PB=$!
  ( mkdir $SH/claude-$N-meds-v2 && $PY build_comet_meds.py --source-report $C --gold-root /mnt/raid0/rbc58/omop/gold \
      --concept /mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv --output-dir $SH/claude-$N-meds-v2/meds > $SH/claude-$N-meds-v2/build.log 2>&1
    mkdir $A/claude-$N-clmbr-codeonly; waitgpu $G2
    CUDA_VISIBLE_DEVICES=$G2 LD_PRELOAD=$MOS/lib/libstdc++.so.6 $MOS/bin/python encode_comet_clmbr.py \
      --meds-root $SH/claude-$N-meds-v2/meds --model-root /mnt/raid0/eo287/clmbr --numeric-mode code-only --max-tokens 4096 \
      --limit 0 --output-dir $A/claude-$N-clmbr-codeonly/report > $A/claude-$N-clmbr-codeonly/run.log 2>&1 ) & PC=$!
  R=$A/claude-$N-progref-v1
  $PY build_prognostic_reference.py --trial $T --cohort $ROSTER --threads $TH --output-dir $R/reference > $L/progref.log 2>&1
  $PY build_core_baseline.py --trial $T --roster $R/reference/restricted_reference.parquet --imputations 0 --threads $TH --output-dir $R/baseline > $L/progref_baseline.log 2>&1
  $PY build_preindex_panel.py --cohort-csv $R/reference/restricted_reference.parquet --omop-root /mnt/raid0/rbc58/omop/gold --threads $TH \
    --dictionary $A/claude-$N-panel-v2/panel_dictionary.csv --output-dir $R/panel > $L/progref_panel.log 2>&1
  $PY fit_prognostic_score.py --reference $R/reference/restricted_reference.parquet --reference-baseline $R/baseline/restricted_baseline_observed.parquet \
    --reference-panel $R/panel/restricted_panel.parquet --cohort-baseline $A/claude-$N-baseline-v11/restricted_baseline_observed.parquet \
    --cohort-panel $A/claude-$N-panel-v2/restricted_panel.parquet --output-dir $R/scores-v3 > $L/progref_fit.log 2>&1 || say "$N progscore FAILED"
  $PY build_physiology_panel_v2.py --roster $ROSTER --threads $TH --output-dir $A/claude-$N-physpanel-v11 > $L/physpanel.log 2>&1 || say "$N physpanel FAILED"
  wait $PB; say "$N BCL done ($(grep -c . $A/claude-$N-bcl/input/restricted_input.csv) input lines)"
  $PY select_cohort_ecgs.py link --selection-dir $A/claude-$N-bcl/input --embeddings-dir $A/claude-$N-bcl/embeddings > $A/claude-$N-bcl/link.json 2> $L/link.log || say "$N link FAILED"
  $PY train_ecg_phenotype_heads.py --phenotype-set $A/claude-ecg-phenotype-set/restricted_phenotype_set.parquet \
    --phenotype-embeddings $A/claude-ecg-phenotype-set/embeddings --cohort-embeddings-glob "$A/claude-$N-bcl/restricted_embeddings_part-*.parquet" \
    --exclude-cohort $ROSTER --output-dir $A/claude-$N-phenotypes > $L/phenotypes.log 2>&1 || say "$N phenotypes FAILED"
  wait $PC; say "$N CLMBR done"
  # outcomes (registered specs; aggregate summaries are pooled over arms)
  $PY extract_outcomes.py --trial $T --roster $ROSTER --threads $TH --output-dir $A/claude-$N-outcomes-v1 > $L/outcomes_v1.log 2>&1 || say "$N outcomes-v1 FAILED"
  $PY v13_extract.py --trial $T --roster $ROSTER --threads $TH --output-dir $A/claude-$N-outcomes-v13 > $L/outcomes_v13.log 2>&1 || say "$N outcomes-v13 FAILED"
  $PY v14_extract.py --trial $T --roster $ROSTER --threads $TH --output-dir $A/claude-$N-hf-v14 > $L/hf_v14.log 2>&1 || say "$N hf-v14 FAILED"
  $PY v16/s5_nco_extract.py --trials $N --threads $TH --out $A/claude-v18-s5-nco/extract > $L/s5_nco.log 2>&1 || say "$N s5-nco FAILED"
  say "$N built"; }
git -C /home/rbc58/github/ecg-tte rev-parse HEAD > $Q/code-commit.txt
# usage: build_queue.sh "n1:key1 n2:key2" "n3:key3 ..." G1 G2 G3 G4 ["all trial names"]   (two chains; GPUs checked idle before each use)
# resumable: pre-BCL steps whose output directory exists are skipped (a queue stopped while waiting for a GPU)
L1="$1"; L2="$2"; GA=$3; GB=$4; GC=$5; GD=$6
( for s in $L1; do IFS=: read N T <<< "$s"; one $N $T $GA $GB; done ) &
( for s in $L2; do IFS=: read N T <<< "$s"; one $N $T $GC $GD; done ) &
wait; say "PER-TRIAL DONE"
# held-out covariate panels (blind: no by-arm summaries / SMD)
ALL=${7:-$(for s in $L1 $L2; do echo -n "${s%%:*} "; done)}  # optional 7th arg: all trials for the covars builders (resume)
$PY v16/build_v16_covars.py --threads 16 --trials $ALL --out $A/claude-v18-covars --blind > $Q/logs/covars.log 2>&1 || say "covars FAILED"
$PY v16/build_v16_covars2.py --threads 16 --trials $ALL --out $A/claude-v18-covars2b --blind > $Q/logs/covars2b.log 2>&1 || say "covars2b FAILED"
say "ALL DONE"; touch $Q/BUILD_DONE
