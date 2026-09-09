# PARADIGM-HF Trial Plan

## Trial summary
- **RCT:** McMurray JJV et al., N Engl J Med 2014;371:993-1004
- **Arms:** Sacubitril/valsartan (ENTRESTO) vs enalapril
- **Endpoint:** CV death + HF hospitalization (composite); 3yr follow-up
- **Published HR:** 0.80 [0.73–0.87]
- **Config:** `configs/paradigm_hf.yaml`

## Goal (this emulation)
Full-featured TTE with maximally-permissive 50–100 covariate matching:
1. PSM-rich (IPTW, preserve full n) + 1:1 PSM comparator
2. ECG-embedding NN (cosine ≤ 0.30)
3. ECG + PSM hybrid
4. Baseline covariate balance (SMD) produced BEFORE modeling in stage3.5

## Pipeline steps

| Step | Script | Status | Output |
|------|--------|--------|--------|
| 0 | `explore_omop_sources.py` | **TODO** | `omop_inspection/{lab,vital,obs}_concept_freq.csv` |
| 1a | Expand `COMORBIDITY_ICD` + labs/vital concept maps in `cohort_utils.py` | TODO | — |
| 1b | New OMOP loaders (`load_measurement`, `load_observation_icd10`) in `cohort_utils.py` | TODO | — |
| S1 | `stage1_build_pool.py` + paradigm_hf config | TODO | `pool/pool.parquet`, `ecg_candidates.parquet` |
| S2 | `stage2_embed.py` | TODO | `embeddings/*.npy` |
| S3 | `stage3_filter.py --config paradigm_hf.yaml` | TODO | `comet_cohort.parquet`, `attrition.csv` |
| S3.5 | `stage3_5_enrich.py` (NEW) | TODO | `cohort_enriched.parquet`, `smd_baseline.csv` |
| S4 | `stage4_analyze.py` (modified: RICH_COVS + IPTW) | TODO | HRs, forest plot, post-adj SMD |

## Stage 1 run command (cluster)

```bash
python scripts/stage1_build_pool.py \
    --config            configs/paradigm_hf.yaml \
    --person-parquet    /mnt/raid0/bb2238/ecg_ascvd/omop_database/person/person.parquet \
    --condition-dir     /mnt/raid0/bb2238/ecg_ascvd/omop_database/condition_occurrence \
    --death-parquet     /mnt/raid0/bb2238/ecg_ascvd/omop_database/death/death.parquet \
    --drug-master       /home/rbc58/mnt/ecg-tte/drugs/home_meds_*.parquet \
    --echo-meta         /mnt/raid0/rbc58/mm_vhd/metadata/echo_metadata.parquet \
    --ecg-meta          /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \
    --visit-dir         /mnt/raid0/bb2238/ecg_ascvd/omop_database/visit_occurrence \
    --output-root       /home/rbc58/mnt/ecg-tte/runs \
    2>&1 | tee /home/rbc58/mnt/ecg-tte/runs/paradigm_hf_stage1.log
```

Note: `--drug-master` takes glob — pass home_meds shards only (setting=home_meds)
to avoid inpatient administrations becoming index events.

## Key design choices

### New-user definition
`first_ever_arm_dispense` on `home_meds` setting only.
- SACUBITRIL/ENTRESTO first home-med dispense → treated arm index date
- ENALAPRIL/VASOTEC first home-med dispense → control arm index date
- `skip_washout: true` on sacubitril arm (prior ACEi expected by design, not an exclusion)
- `min-index-date: 2015-07-07` (FDA approval date for Entresto)

### 50–100 covariate strategy
| Source | Type | Count (target) | Lookback |
|--------|------|----------------|---------|
| `COMORBIDITY_ICD` expanded | Binary ICD | ~35 Elixhauser | ever / 5yr |
| `MEDICATION_KEYWORDS` | Binary drug | ~20 groups | 90d |
| `LAB_CONCEPTS` (from Step 0) | Continuous + `_measured` flag | ~20 labs | 365d pre-index |
| `VITAL_CONCEPTS` (from Step 0) | Continuous + `_measured` flag | ~5 vitals | 365d pre-index |
| ECG intervals | Continuous | 3 (RR, PR, QRS) | at index |
| Echo EF | Continuous | 1 | at index |
| Demographics | Mixed | ~4 (age, sex, race_black, age²) | — |

Total target: ~88 covariates before interaction terms.

### IPTW specification
- Estimator: stabilized IPTW using `LogisticRegression(penalty='l2', C=0.1, max_iter=1000)`
  (L2 regularization — 50-100 covariates risk separation without it)
- Trim: [0.01, 0.99] (existing `ipw_hr` in stage4_analyze.py:166)
- Outcome model: weighted Cox (existing lifelines `CoxPHFitter`)
- SMD post-IPTW: weighted SMD using `effective_sample_size` weights in `balance.py`

### Endpoint definition
- Primary: CV death (all-cause proxy) OR HF hospitalization (I50 + inpatient visit, concept_ids 9201/262)
- Follow-up: 1095 days (3 years)
- Requires `--visit-dir` for inpatient HF hosp gate

### Known confound
`acei_arb` covariate structurally confounded with sacubitril/valsartan treatment
(valsartan = ARB component). Exclude from PSM covariate set via
`--exclude-psm-cols acei_arb` in stage4.

## Feasibility estimate (from drug_master QC)
- SACUBITRIL/ENTRESTO pts (home_meds): ~12K across cohorts
- ENALAPRIL/VASOTEC pts (home_meds): ~14K across cohorts
- After HFrEF gate (EF≤40% or I50), prior washout (sacubitril arm waived), age≥18:
  expect 500–3000 per arm. Minimum threshold: 50/arm per config.

## Pre-check: `required_icd` fix
Confirm `stage3_filter.py` Round 6 fix (required_icd now applied) is merged before run.
PARADIGM-HF required_icd = `hf_icd_ever` (I50 ever). Without fix, non-HF patients
enter the cohort.

## Run notes (fill in after each stage)
### Stage 0 (explore_omop_sources)
- Date run:
- Key finding:
- Concept IDs selected:

### Stage 1
- Date run:
- n pool:
- n sacubitril arm:
- n enalapril arm:
- index date range:

### Stage 3
- n after HFrEF gate:
- n after washout:
- final cohort:

### Stage 3.5
- n covariates in enriched parquet:
- labs fill rate:
- pre-adjustment SMD max:
- pre-adjustment SMD median:

### Stage 4
- IPTW HR:
- 1:1 PSM HR:
- ECG-NN HR:
- ECG+PSM HR:
- Published HR: 0.80 [0.73–0.87]
