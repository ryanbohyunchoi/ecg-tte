# Multi-trial long-tail replication: run sequence

Contract and design choices: `docs/DECISIONS.md` (2026-09-23, "Multi-trial replication
contract v1"). Specs: `scripts/trial_specs.py`. Envs are those in `master.md`. Every step
writes a fresh private directory and refuses to reuse one.

```bash
cd /home/rbc58/github/ecg-tte; umask 077
PY=/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python
BCL=/mnt/raid0/rbc58/ecg-tte/software/bcl-smoke-runtime-zZ5FVVsd
MOS=/mnt/raid0/rbc58/ecg-tte/software/mosaic-env
A=/mnt/raid0/rbc58/ecg-tte/audits; T=paradigm_hf; N=paradigm   # trial key / short name

# 1. cohort, core baseline (+5 imputations), panel v2   (seconds each)
$PY scripts/build_trial_cohort.py --trial $T --output-dir $A/claude-$N-cohort-v1
$PY scripts/build_core_baseline.py --trial $T --roster $A/claude-$N-cohort-v1/restricted_cohort.parquet --output-dir $A/claude-$N-baseline-v1
$PY scripts/build_preindex_panel.py --cohort-csv $A/claude-$N-cohort-v1/restricted_cohort.parquet --omop-root /mnt/raid0/rbc58/omop/gold --output-dir $A/claude-$N-panel-v2

# 2. ECG: select (365 d, index day allowed) -> fixed BCL on an idle GPU -> link
$PY scripts/select_cohort_ecgs.py select --cohort $A/claude-$N-cohort-v1/restricted_cohort.parquet --output-dir $A/claude-$N-bcl/input
nvidia-smi   # pick an idle device
CUDA_VISIBLE_DEVICES=0 setsid nohup $BCL/env/bin/python scripts/bcl_embed_uv.py --upstream-dir $BCL/upstream -- \
  --checkpoint-path /mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/CNN0_lead_time_transformer_10s_500Hz_BCL_LR0.0001_Dropout0.5_08_26_2026/trained_12lead_30.pt \
  --input-file $A/claude-$N-bcl/input/restricted_input.csv --formats-csv $A/claude-$N-bcl/input/restricted_formats_no250.csv \
  --data-roots /mnt/raid0/bb2238/signals/preprocessed/all_ecgs --output-dir $A/claude-$N-bcl/embeddings \
  --batch-size 64 --num-workers 8 --shard-size 512 --no-quality-filter --no-deduplicate --no-partial --no-amp \
  --no-overwrite --no-ddp-autodetect > $A/claude-$N-bcl/run.log 2>&1 < /dev/null &
$PY scripts/select_cohort_ecgs.py link --selection-dir $A/claude-$N-bcl/input --embeddings-dir $A/claude-$N-bcl/embeddings
$PY scripts/train_ecg_phenotype_heads.py --phenotype-set $A/claude-ecg-phenotype-set/restricted_phenotype_set.parquet \
  --phenotype-embeddings $A/claude-ecg-phenotype-set/embeddings --cohort-embeddings-glob "$A/claude-$N-bcl/restricted_embeddings_part-*.parquet" \
  --exclude-cohort $A/claude-$N-cohort-v1/restricted_cohort.parquet --output-dir $A/claude-$N-phenotypes

# 3. CLMBR code-only: per-cohort MEDS (~3 min) -> frozen encoder (~2 min on one H100)
mkdir /mnt/raid0/rbc58/ecg-tte/shared/claude-$N-meds-v2
(cd scripts && setsid nohup $PY build_comet_meds.py --source-report $A/claude-$N-cohort-v1 --gold-root /mnt/raid0/rbc58/omop/gold \
  --concept /mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv --output-dir /mnt/raid0/rbc58/ecg-tte/shared/claude-$N-meds-v2/meds \
  > /mnt/raid0/rbc58/ecg-tte/shared/claude-$N-meds-v2/build.log 2>&1 < /dev/null &)
mkdir $A/claude-$N-clmbr-codeonly
(cd scripts && CUDA_VISIBLE_DEVICES=1 LD_PRELOAD=$MOS/lib/libstdc++.so.6 setsid nohup $MOS/bin/python encode_comet_clmbr.py \
  --meds-root /mnt/raid0/rbc58/ecg-tte/shared/claude-$N-meds-v2/meds --model-root /mnt/raid0/eo287/clmbr --numeric-mode code-only \
  --max-tokens 4096 --limit 0 --output-dir $A/claude-$N-clmbr-codeonly/report > $A/claude-$N-clmbr-codeonly/run.log 2>&1 < /dev/null &)

# 4. external prognostic reference (never cohort patients) and scores
R=$A/claude-$N-progref-v1
$PY scripts/build_prognostic_reference.py --trial $T --cohort $A/claude-$N-cohort-v1/restricted_cohort.parquet --output-dir $R/reference
$PY scripts/build_core_baseline.py --trial $T --roster $R/reference/restricted_reference.parquet --imputations 0 --output-dir $R/baseline
$PY scripts/build_preindex_panel.py --cohort-csv $R/reference/restricted_reference.parquet --omop-root /mnt/raid0/rbc58/omop/gold \
  --dictionary $A/claude-$N-panel-v2/panel_dictionary.csv --output-dir $R/panel
$PY scripts/fit_prognostic_score.py --reference $R/reference/restricted_reference.parquet --reference-baseline $R/baseline/restricted_baseline_observed.parquet \
  --reference-panel $R/panel/restricted_panel.parquet --cohort-baseline $A/claude-$N-baseline-v1/restricted_baseline_observed.parquet \
  --cohort-panel $A/claude-$N-panel-v2/restricted_panel.parquet --output-dir $R/scores-v3

# 5. long-tail v2 grid (5 imputations x 5 splits, ~2 min), pooled to summary_pooled.csv
setsid nohup scripts/run_longtail_v2.sh $A/claude-longtail-v2-$N $A/claude-$N-baseline-v1 $A/claude-$N-panel-v2/restricted_panel.parquet \
  $A/claude-$N-panel-v2/panel_dictionary.csv "$A/claude-$N-bcl/restricted_embeddings_part-*.parquet" \
  "$A/claude-$N-clmbr-codeonly/report/restricted_embeddings_part-*.parquet" $A/claude-$N-phenotypes/restricted_cohort_phenotypes.parquet \
  $R/scores-v3/restricted_prognostic_scores.parquet $T > $A/claude-longtail-v2-$N.log 2>&1 < /dev/null &
```

COMET runs through the same evaluator. `scripts/export_comet_baseline.py` converts the saved MICE
common inputs to `audits/claude-comet-baseline-export-v2`. The panel is
`claude-comet-preindex-panel-v2` with the **v1 dictionary**, so v1 splits are kept. The prognostic
inputs are under `claude-comet-progref-v1` (roster: the MICE-prep cohort, linked by exact
person_source_value). The output is `audits/claude-longtail-v2-comet`.
