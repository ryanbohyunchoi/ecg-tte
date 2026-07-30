# ECG-TTE: Target Trial Emulation Pipeline

Replicates **RCT-DUPLICATE** (Wang et al., JAMA 2023) across 32 cardiac/CV/metabolic trials using Yale EHR (OMOP CDM + local drug/echo/ECG tables), with a methodological advance: **hybrid confounding control** via PSM on EHR covariates PLUS ECG waveform embedding matching (cosine-distance threshold).

## Pipeline Overview

```
Stage 0: Feasibility check   → GO/NO-GO per trial
Stage 1: EHR cohort pool     → wide candidate pool with all covariates
Stage 2: ECG embedding       → embed ECGs within window (< 90d of index)
Stage 3: Apply I/E criteria  → filtered cohort
Stage 4: Outcome analysis    → Cox regression, PSM, ECG-NN comparator ladder
Stage 5: Meta-analysis       → cross-trial aggregate
```

All outputs go to `/home/rbc58/mnt/ecg-tte/{trial_key}/`.

## Architecture

### Config-driven design
Each trial is defined by a per-trial YAML config in `configs/`. See `configs/_schema.md` for the full schema.

```
configs/
  _schema.md          ← schema documentation
  comet.yaml          ← COMET (regression gate)
  leader.yaml         ← LEADER (liraglutide)
  aristotle.yaml      ← ARISTOTLE (apixaban vs warfarin)
  ... (32 trials total)
```

### Key scripts

| Script | Purpose |
|---|---|
| `scripts/stage0_feasibility.py` | Per-trial feasibility check (aggregate-only) |
| `scripts/stage1_build_pool.py` | Build wide candidate pool (config-driven) |
| `scripts/stage2_embed.py` | Embed ECGs in pool using BCL encoder |
| `scripts/stage3_filter.py` | Apply trial-specific I/E criteria |
| `scripts/stage4_analyze.py` | Cox regression + PSM + ECG-NN analyses |
| `scripts/cohort_utils.py` | Shared helpers (arm identification, endpoints, loaders) |
| `scripts/lint_configs.py` | Validate all configs/*.yaml |
| `scripts/balance.py` | SMD computation (77-covariate set = full RICH-PSM coverage) |

## Running Stage 0 (Feasibility)

```bash
# All trials
python scripts/stage0_feasibility.py \
    --config-dir       configs/ \
    --person-parquet   /home/rbc58/mnt/ascvd/omop_database/person/person.parquet \
    --condition-dir    /home/rbc58/mnt/ascvd/omop_database/condition_occurrence \
    --drug-master      /mnt/raid0/rbc58/mm_vhd/drug/drug_master.parquet \
    --echo-meta        /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \
    --ecg-meta         /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \
    --death-parquet    /home/rbc58/mnt/ascvd/omop_database/death/death.parquet \
    --output-dir       /home/rbc58/mnt/ecg-tte/_feasibility

# Quick smoke test (5000 persons)
python scripts/stage0_feasibility.py --config configs/comet.yaml ... --limit-persons 5000
```

## Running Stage 1 (Pool Build)

```bash
python scripts/stage1_build_pool.py \
    --config           configs/comet.yaml \
    --person-parquet   /home/rbc58/mnt/ascvd/omop_database/person/person.parquet \
    --condition-dir    /home/rbc58/mnt/ascvd/omop_database/condition_occurrence \
    --drug-master      /mnt/raid0/rbc58/mm_vhd/drug/drug_master.parquet \
    --echo-meta        /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \
    --ecg-meta         /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \
    --death-parquet    /home/rbc58/mnt/ascvd/omop_database/death/death.parquet \
    --output-root      /home/rbc58/mnt/ecg-tte

# With composite endpoint (visit/procedure tables)
python scripts/stage1_build_pool.py \
    --config configs/aristotle.yaml \
    ... \
    --visit-dir     /home/rbc58/mnt/ascvd/omop_database/visit_occurrence \
    --procedure-dir /home/rbc58/mnt/ascvd/omop_database/procedure_occurrence
```

**COMET regression gate**: running with `configs/comet.yaml` produces output identical to the original COMET-specific stage1.

## Stage 1 Output

```
{output-root}/{trial_key}/pool/
  pool.parquet                 ← full candidate pool
  drug_master_pool.parquet     ← drug records for pool patients
  conditions_pool.parquet      ← condition records for pool patients
  ecg_candidates.parquet       ← ECGs within ±pool_window_days of index
  build_manifest.json          ← run metadata (arm counts, git SHA, paths)
```

## Lint Configs

```bash
python scripts/lint_configs.py                  # validate all configs/*.yaml
python scripts/lint_configs.py configs/comet.yaml
```

## Key Design Decisions

### ECG window < 90 days
All configs enforce `ecg.window_days < 90` (validated on load). The pool caches ECGs ±365d; Stage 3 narrows to the trial-specific window.

### Active comparator design
For placebo-controlled RCTs, the EHR emulation uses an active comparator arm (e.g., SGLT2i vs DPP4i instead of SGLT2i vs placebo). This mirrors RCT-DUPLICATE's approach and is documented per-trial in each config.

### CV death proxy
Yale's death table is date-only (no `cause_concept_id`). All-cause mortality is used as a proxy for CV mortality. Composite endpoints add HF hospitalization (`inpatient_icd`) to capture heart failure events.

### COMET backward compatibility
The new generic stage1 produces all columns the legacy COMET-specific stage1 produced:
- `stage3_alias` in `comet.yaml` → `first_carv_date`, `prior_meto_days`, etc.
- Medication flags: stage1 builds `loop_diuretic_90d`, `acei_arb_90d`, etc.; stage3 **strips** the `_90d` suffix (`loop_diuretic`, ...), which is what `balance.py` SMD_COLS and the rich PSM reference.

### balance.py SMD_COLS
`SMD_COLS` is a 77-covariate superset covering everything the rich PSM matches on (so the balance table / Love plot report every matched covariate), plus reported-but-not-matched extras (extended ECG axes, trial-specific exclusion proxies). Names use the post-stage3 convention (medication `_90d` stripped). `build_balance_table` emits a NaN row for any covariate absent from a trial's cohort.

## Trials

32 trials from RCT-DUPLICATE, grouped by therapeutic area:

| Area | Trials |
|---|---|
| Beta-blockers (HFrEF) | COMET |
| ARNI vs ACEi (HFrEF) | PARADIGM-HF |
| GLP-1 RA (T2D/CV) | LEADER, LEAD-2 |
| SGLT2i (T2D/CV/CKD) | DECLARE-TIMI58, EMPA-REG, CANVAS, DAPA-CKD |
| DPP-4i (T2D/CV) | CARMELINA, TECOS, SAVOR-TIMI 53, CAROLINA |
| Antiplatelet (ACS) | TRITON-TIMI38, PLATO, ISAR-REACT5 |
| Anticoagulation (AF) | ARISTOTLE, RE-LY, ROCKET AF |
| Anticoagulation (VTE) | EINSTEIN DVT, EINSTEIN PE, RE-COVER II, AMPLIFY, RECORD1 |
| RAS inhibitors | TRANSCEND, ONTARGET |
| Osteoporosis | HORIZON-PFT, VERO |
| Respiratory (Asthma) | P04334, D5896 |
| Respiratory (COPD) | IMPACT, POET-COPD, INSPIRE |

---

## Change Log

### 2026-07-28 — MICE imputation + PSM/balance upgrade (`psm-mice-imputation`)
- **`scripts/imputation.py`** (new): MICE (sklearn `IterativeImputer`) for missing **continuous** covariates (echo EF, ECG intervals, labs, vitals). Structurally 0-encoded binaries are never imputed (`split_covariates`); adds a missing-indicator for informative-missingness covariates (`ef_at_index`); imputation model includes treatment + Nelson-Aalen cumulative hazard (White & Royston); outcome never imputed.
- **`scripts/stage4_analyze.py`**: `--n-imputations` (default 1 = legacy complete-case, byte-identical; ≥2 = MICE). Per-imputation PS→match→Cox pooled with **Rubin's rules** (`pool_rubin`, `_pool_over_imputations`, `structured_psm_pooled`), FMI reported. **Caliper fix**: matching now on `logit(PS)` at `--caliper-sd × SD` (Austin 0.2 default) instead of raw-PS 0.25 — `--structured-caliper` kept as deprecated alias. Wired the previously-dead `--denominator {strict,both}` audit (fixes a `run_stage34.sh` argparse crash). Fixed duplicate cohort-load; refreshed stale docstrings.
- **`scripts/balance.py`**: `pooled_balance_table` averages SMD across imputations with complete-case sensitivity columns (`smd_pre_cc`/`smd_post_cc`). `SMD_COLS` expanded 37→77 (full RICH-PSM coverage; fixed medication _90d naming drift; +labs/vitals).
- **`scripts/stage1_build_pool.py` / `stage3_filter.py`**: wired labs/vitals/Z-codes into the pool via `--measurement-dir` / `--observation-dir` (config keys `covariates.labs/vitals/zcodes`); columns pass Stage 3's `OUTPUT_COLS` gate. Requires a Stage-1 re-run to populate.
- **`configs/`**: `paradigm_hf.yaml`, `comet.yaml`, `_schema.md` document the new `labs`/`vitals`/`zcodes` covariate keys.
- **`tasks/lessons.md`** (new): correction log (do-not-impute-binaries, logit caliper, match-within-pool-effects).
- Verified: m=1 reproduces legacy Unadjusted/Adjusted HRs exactly; `pool_rubin` `se=√T`; labs/vitals flow through MICE + balance end-to-end.

### 2026-06-07 — Multi-trial foundation (Stage 0 + Stage 1)
- **`scripts/cohort_utils.py`**: Complete generalization — KEYWORD_REGISTRY, MEDICATION_KEYWORDS, `identify_arms_generic`, `compute_adherence_metrics_generic`, `build_composite_endpoint`, `load_visit_occurrence`, `load_procedure_occurrence`, `conds_within` (public), `validate_config`, `load_trial_config`, `resolve_keywords`. COMET backward-compat via thin wrappers.
- **`scripts/stage1_build_pool.py`**: Refactored to config-driven. Accepts `--config`, `--output-root`, `--visit-dir`, `--procedure-dir`, `--limit-persons`. Produces generic per-trial pools; COMET output preserved via `stage3_alias` columns.
- **`scripts/stage0_feasibility.py`**: New — per-trial GO/NO-GO feasibility checker (aggregate-only outputs). Supports `--config` (one trial) or `--config-dir` (all trials).
- **`scripts/lint_configs.py`**: New — validates all configs/*.yaml via `validate_config()`.
- **`configs/`**: New directory with `_schema.md`, `comet.yaml`, and 31 trial configs (all RCT-DUPLICATE trials).
- **`scripts/stage3_filter.py`**: Added `--cohort-filename` arg (default `comet_cohort.parquet`) for multi-trial output naming.

### 2026-06-10 — Stage 2 multi-GPU + Stage 3/4 generalization, full pipeline run on VERO
- **`scripts/stage2_embed.py`**: Vendored `MLP` projector into new `scripts/clip_model.py` (fixes `ModuleNotFoundError: models.clip_model` when run from `scripts/`). Added `nn.DataParallel` for multi-GPU.
- **`scripts/run_stage2.sh`**: New — embeds all 32 trial pools into one shared, fileID-deduped `EMBED_DIR`. Added `--gpu` flag (`CUDA_VISIBLE_DEVICES`, comma-list = DataParallel).
- **`scripts/run_stage34.sh`**: New — loops Stage 3 (filter) → Stage 4 (comparator ladder + forest plot) over all 32 trials, reading arm names/published HR from `configs/<trial>.yaml`.
- **`scripts/stage3_filter.py`**: Generalized COMET-only hardcoding that broke non-COMET trials:
  - `Attrition.log()` now counts per actual `pool["arm"]` value (was hardcoded `carvedilol`/`metoprolol`).
  - Naive new-user lookback (step 2) now generic over `pool["arm"].unique()` × `prior_<other_arm>_days` (was `prior_meto_days`/`prior_carv_days` only).
  - New `--require-hfref` flag (default `True`, COMET unchanged) gates the HFrEF inclusion criterion (block 4); non-HF trials set `require-hfref: false`.
  - Block 8 cardiac exclusions (CCB/other-BB/recent-MI/AV-block/ESRD/hepatic/valvular) now skip with a `NOTE` if the pool lacks the column, instead of `KeyError`.
  - `filter_manifest.json` / final print now report per-arm counts dynamically instead of `n_carvedilol`/`n_metoprolol`.
- **`configs/vero.yaml`**: Added `require-hfref: false` (osteoporosis trial — COMET HFrEF criterion N/A).
- Verified: `bash scripts/run_stage34.sh --trials "vero"` runs Stage 3 + Stage 4 end-to-end on the cluster, producing `comet_cohort.parquet`, `attrition.csv`, `filter_manifest.json`, `results_summary.csv`, `forest.png`. Strict-denominator ECG cohort is small (n=71/674) since VERO is non-cardiac; PSM/ECG-NN/hybrid rungs fail to converge on this trial as expected (n_per_arm ~22-35) — not a pipeline bug.
- **PSM covariate set collapsed**: `stage4_analyze.py` SPARSE_COVS/RICH_COVS removed, replaced by single `STRUCTURED_COVS` (11 covs: age_at_index, sex_binary, race_black, afib, htn, dm, cad_mi, copd, hyperlipidemia, stroke, prior_hf_code_1yr; column-existence filtered per trial). `denominators.py build_masks()`/`missingness_audit()` updated to single-list signature; `psm_sparse_eligible`/`psm_rich_eligible` → `psm_eligible`.
- **Full 32-trial run, COMET succeeded; d5896 crashed** with `ZeroDivisionError` (control arm n=0 in strict D — config bug, treated arm's bare `BUDESONIDE` keyword swallowed budesonide-alone patients). `set -euo pipefail` aborted the whole loop here, so trials after d5896 never ran.
  - `stage4_analyze.py`: added empty-arm guard (n_t==0 or n_c==0 → diagnostic message + `sys.exit(1)`) instead of crashing in lifelines.
  - `run_stage34.sh`: stage3/stage4 calls now capture exit code via `${PIPESTATUS[0]}`, `continue` to next trial on failure, track `FAIL_COUNT`, report `OK/SKIPPED/FAILED` in summary.
  - `configs/d5896.yaml`: fixed arm `formulation_filter` (treated requires FORMOTEROL, control excludes FORMOTEROL/SYMBICORT). **Requires Stage 1 pool rebuild for d5896** to take effect (arm assignment happens in stage1).
- Full 32-trial run after these fixes: `OK=27 SKIPPED=0 FAILED=5` (d5896 + 4 others, not yet diagnosed).
- **`scripts/stage5_meta.py`**: New — Stage 5 cross-trial meta-analysis (RCT-DUPLICATE style). Reads each trial's `results_summary.csv` (5 ladder rungs: Unadjusted Cox, Adjusted Cox, Structured PSM, ECG-NN PRIMARY, PS+ECG-NN) and `published_hr`/`published_hr_ci` from `configs/<trial>.yaml`. Outputs `meta_results.csv` (per trial × method: log-HR diff, standardized estimate difference `z_pooled`, regulatory agreement, CI overlap), `meta_summary.csv` (per-method Pearson r vs published, mean/var of log-HR diff and z_pooled, agreement rates), and `meta_scatter.png` / `meta_variance.png` / `meta_zscore.png`. Trials with `published_hr: null` (lead2) or missing `results_summary.csv` are skipped with a NOTE.
