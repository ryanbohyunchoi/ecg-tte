# Handoff — ecg-tte pipeline

## What this repo is
Target trial emulation of 32 RCT-DUPLICATE trials using Yale OMOP EHR. Methodological advance:
hybrid PSM + ECG waveform embedding (cosine-distance) matching. Code written locally → push →
pull → run on Yale H100 cluster.

## Pipeline (current, upgraded)
```
stage1_build_pool.py    → {trial}/pool/pool.parquet + ecg_candidates.parquet
stage2_embed.py         → embeddings/{fileID}.npy + embedding_manifest.json
stage3_filter.py        → runs/{run}/comet_cohort.parquet + attrition.csv
stage3_5_enrich.py      → cohort_enriched.parquet + smd_baseline.csv   [PLANNED, not yet written]
stage4_analyze.py       → HRs, forest plot, post-adjustment SMD         [needs RICH_COVS + IPTW wiring]
stage5_meta.py          → cross-trial meta-analysis vs published HRs
```

## Current status (2026-06-30)

### Drug master ✅ DONE
12 shards in `/home/rbc58/mnt/ecg-tte/drugs/`. QC verified:
- home_meds_*.parquet (3 files): 58M rows, 824K unique MRNs, 100% date fill
- All arm drugs present: SACUBITRIL ~37K rows, ENALAPRIL ~54K rows
- **Merged for stage1:** `/home/rbc58/mnt/ecg-tte/drugs/home_meds_merged.parquet` (already built)
- Use `home_meds_merged.parquet` for stage1 `--drug-master` (oral drugs only; inpatient shards NOT for index events)

### PARADIGM-HF Stage 1 — IN PROGRESS
Run script: `bash trials/paradigm/run_stage1.sh`

Bugs fixed this session:
1. MRN mismatch: person table has `MR` prefix; drug_master is numeric-only. Fixed in `parse_person_table` — strips leading alpha chars.
2. Echo path: correct file is `echo_accession_number.parquet` (has EF column); `echo.parquet` lacks EF.

**Last run output before next attempt:**
- 17,765 pool patients (sacubitril_valsartan: 9,367 / enalapril: 8,398) ✓
- Crashed at echo load — fixed in latest commit (aa26275)

**Next:** `git pull && bash trials/paradigm/run_stage1.sh` — should complete now.

After stage1 completes, check:
```bash
ls -lh /home/rbc58/mnt/ecg-tte/runs/paradigm_hf/pool/
# Expect: pool.parquet, ecg_candidates.parquet, drug_master_pool.parquet,
#         conditions_pool.parquet, build_manifest.json
```

### Covariate upgrade ✅ DONE (cohort_utils.py)
`COMORBIDITY_ICD` expanded 7 → 32 Elixhauser/Charlson categories.
New constants: `LAB_CONCEPTS` (5 lab concepts), `VITAL_CONCEPTS` (2 vital concepts),
`OBSERVATION_ZCODES` (8 Z-code flags from observation_occurrence).
New loaders: `load_observation_icd10`, `load_measurement`.
New helpers: `add_zcode_flags`, `add_measurement_covariates`.

OMOP measurement extract has only 5 lab concepts (eGFR, creatinine, total-chol, HDL, HbA1c)
and 2 vital concepts (SBP, BMI) — confirmed by `explore_omop_sources.py`. Not a rich lab panel.
Observation_occurrence contains Z-codes (Z94.0=transplant, Z95.1=CABG, Z99.2=dialysis, etc.)
not primary diagnosis ICD — use as supplement to condition_occurrence.

### stage3_5_enrich.py — NOT YET WRITTEN
Next major coding task. Reads I/E-passed cohort, pulls pre-index labs/vitals/Z-codes/expanded
comorbidities for cohort patients only, outputs cohort_enriched.parquet + smd_baseline.csv.
See plan: `/Users/ryanchoi/.claude/plans/okay-lets-start-with-iterative-perlis.md`

### stage4_analyze.py — needs RICH_COVS + IPTW wiring (NOT YET DONE)
- Replace hardcoded `STRUCTURED_COVS` (11) with config-driven RICH_COVS (~83 covariates)
- Wire dead `ipw_hr` function (line 166) as primary PSM-adjustment arm (stabilized IPTW, L2 logistic)
- Move pre-adjustment SMD to stage3.5; stage4 keeps post-adjustment SMD only

## Correct cluster paths (verified 2026-06-30)
```
ECG signals:      /mnt/raid0/bb2238/signals/preprocessed/all_ecgs/{fileID}.npy
ECG metadata:     /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet
Echo metadata:    /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet  ← has EF
Drug master NEW:  /home/rbc58/mnt/ecg-tte/drugs/home_meds_merged.parquet          ← stage1 input
Drug shards:      /home/rbc58/mnt/ecg-tte/drugs/                                  ← 12 files
OMOP person:      /mnt/raid0/bb2238/ecg_ascvd/omop_database/person/person.parquet
OMOP condition:   /mnt/raid0/bb2238/ecg_ascvd/omop_database/condition_occurrence/
OMOP death:       /mnt/raid0/bb2238/ecg_ascvd/omop_database/death/death.parquet
OMOP measurement: /mnt/raid0/bb2238/ecg_ascvd/omop_database/measurement/
OMOP observation: /mnt/raid0/bb2238/ecg_ascvd/omop_database/observation_occurrence/
OMOP obs_period:  /mnt/raid0/bb2238/ecg_ascvd/omop_database/observation_period/observation_period.parquet
Output root:      /home/rbc58/mnt/ecg-tte/runs/
Drug master OLD:  /mnt/raid0/rbc58/mm_vhd/drug/drug_master.parquet  ← DO NOT USE for TTE index
```

**MRN format:** person table `PAT_MRN_ID` has `MR` prefix (e.g. MR1234567). Drug master and
all new files use numeric-only MRN. `parse_person_table` now strips leading alpha → fixed.

**No visit_occurrence in OMOP extract** — `observation_period` lacks start_date too (only end_date).
HF hospitalization endpoint falls back to condition-date proxy (slight event overestimate, acceptable).

## Priority order for next session
1. `git pull && bash trials/paradigm/run_stage1.sh` — should complete now (echo fix in aa26275)
2. Verify pool outputs: check arm n, date range ≥ 2015-07-07, EF fill rate
3. Run stage2 (embed pool ECGs): `python scripts/stage2_embed.py --pool-dir .../paradigm_hf/pool --ecg-dir /mnt/raid0/bb2238/signals/preprocessed/all_ecgs --output-dir .../embeddings`
4. Run stage3: `python scripts/stage3_filter.py --config configs/paradigm_hf.yaml --pool-dir .../paradigm_hf/pool --output-dir .../runs/paradigm_hf/run1`
5. Write `stage3_5_enrich.py` (new enrichment + baseline SMD stage)
6. Modify `stage4_analyze.py` (RICH_COVS + IPTW)
7. 32-trial re-run (required_icd fix): `bash scripts/run_stage34.sh`

## PARADIGM-HF design notes
- Arms: sacubitril/valsartan (ENTRESTO) vs enalapril
- `skip_washout: true` on sacubitril arm (switching trial — prior ACEi expected)
- `min-index-date: 2015-07-07` (Entresto FDA approval)
- HFrEF gate: LVEF ≤ 40% OR I50 ICD
- Endpoint: CV death + HF hospitalization, 3yr follow-up; published HR 0.80 [0.73–0.87]
- Exclude `acei_arb` from PSM covariates (valsartan = ARB → structurally confounded)
- Full trial plan: `trials/paradigm/PLAN.md`

## 32-trial pipeline status (pre-PARADIGM-HF work)
Latest full run: **OK=27 SKIPPED=0 FAILED=5**

CRITICAL FIX pushed but NOT yet re-run: `inclusion.required_icd` stage gate was a no-op in
stage3 for 28/32 trials. Fixed in stage3_filter.py step 1c. Re-run required after PARADIGM-HF.

Known failures: d5896 (pool stale), impact/ontarget/savor_timi/transcend (undiagnosed).
