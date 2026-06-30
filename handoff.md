# Handoff — ecg-tte pipeline

## What this repo is
Target trial emulation of 32 RCT-DUPLICATE (Wang et al. JAMA 2023) trials using Yale OMOP EHR. Methodological advance: hybrid PSM + ECG waveform embedding (cosine-distance) matching. All code runs on Yale H100 cluster; write locally → push → pull → run.

## Pipeline (current)
```
stage1_build_pool.py   → {trial}/pool/ecg_candidates.parquet (config-driven, all 32 trials)
stage2_embed.py        → embeddings/{fileID}.npy + embedding_manifest.json (shared across trials)
stage3_filter.py       → runs/{run}/comet_cohort.parquet + attrition.csv (generic, all 32 trials)
stage4_analyze.py      → results_summary.csv + forest.png + balance tables (generic, all 32 trials)
stage5_meta.py          → cross-trial meta-analysis vs published RCT HRs
```

## Current status (2026-06-29)

### Drug master rebuild (IN PROGRESS on cluster right now)
The existing `drug_master.parquet` at `/home/rbc58/mnt/ecg-tte/drug_master.parquet` was built
from `CarDS_ECG` source — inpatient/ECG-adjacent drugs, NOT a reliable outpatient Rx file.

**New build running now (PID 562590):**
```bash
# Check progress:
tail -20 /home/rbc58/mnt/ecg-tte/drugs/build_log.txt
# Check what's written:
ls -lh /home/rbc58/mnt/ecg-tte/drugs/
```

Output: `/home/rbc58/mnt/ecg-tte/drugs/` — one parquet per source file:
```
home_meds_t2dm.parquet              ← outpatient prescriptions, T2DM cohort
home_meds_cmp.parquet               ← outpatient prescriptions, CMP cohort
home_meds_implementation.parquet    ← outpatient prescriptions, IMPLEMENTATION cohort
outpatient_admin_*.parquet          ← clinic-admin drugs (contrast, antiemetics — NOT Rx)
inpatient_*_{1,2}.parquet           ← hospital meds (covariates only, NOT TTE index)
```

**Schema:** `MRN, drug_name, order_date, generic_name, pharm_class, route, frequency,
dose, dose_unit, order_status, order_class, end_date, discontinue_date,
discontinue_reason, setting, cohort, source_file`

**`setting` column semantics:**
- `home_meds` → real outpatient prescriptions → USE for TTE index event identification
- `outpatient_admin` → procedure drugs (contrast, antiemetics) → covariates only
- `inpatient` → hospital meds → covariates only, NEVER TTE index

**Load for TTE (home meds only):**
```python
import pandas as pd
from pathlib import Path
dm = pd.concat([pd.read_parquet(p) for p in Path('/home/rbc58/mnt/ecg-tte/drugs').glob('home_meds_*.parquet')])
```

**Source raw files confirmed (explored 2026-06-29):**
- T2DM: `/home/rbc58/mnt/t2dm-jdat-data/2380791_CarDS_Outcomes_DM2_Meds.txt` etc.
- CMP: `/home/rbc58/mnt/cmp-jdat-data/2356781_CarDS_Aim_1_Meds.txt` etc.
- IMPL: `/home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15/CarDS_2435227_Meds.txt` etc.

**If job dies mid-run:** re-run same command with `--skip-existing` — it resumes:
```bash
cd /home/rbc58/github/ecg-tte && git pull
nohup python scripts/build_drug_master.py \
    --t2dm-dir   /home/rbc58/mnt/t2dm-jdat-data \
    --cmp-dir    /home/rbc58/mnt/cmp-jdat-data \
    --impl-dir   /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
    --output-dir /home/rbc58/mnt/ecg-tte/drugs \
    --skip-existing \
    > /home/rbc58/mnt/ecg-tte/drugs/build_log.txt 2>&1 &
```

### PARADIGM-HF — next trial after drug master is ready
SACUBITRIL/VALSARTAN vs ENALAPRIL in HFrEF (LVEF ≤ 40%). Config: `configs/paradigm_hf.yaml`.

Key design decisions already implemented:
- `skip_washout: true` on sacubitril arm — PARADIGM-HF is a SWITCHING trial
  (ARNI starters come FROM prior ACEi); naive cross-arm washout would gut the treated arm
- `min-index-date: "2015-07-07"` (Entresto FDA approval date)
- Composite endpoint: CV death + HF hospitalization (`event_primary`/`time_to_primary`)
- Stage 3 + Stage 4 already handle composite endpoints via auto-detection

**Once drug_master is ready, run Stage 1:**
```bash
python scripts/stage1_build_pool.py \
    --config configs/paradigm_hf.yaml \
    --drug-master /home/rbc58/mnt/ecg-tte/drugs/home_meds_*.parquet \
    --output-root /home/rbc58/mnt/ecg-tte \
    --visit-dir /home/rbc58/mnt/ascvd/omop_database/visit_occurrence
```
Note: `--visit-dir` required for HF hospitalization endpoint.

### 32-trial pipeline status (as of 2026-06-10, pre-drug-master work)
Latest full run: **OK=27 SKIPPED=0 FAILED=5**

#### CRITICAL FIX (pushed, NOT yet re-run on cluster)
`inclusion.required_icd` (disease-population gate) was computed by stage1 but **never
filtered** by stage3. Affects 28/32 trials. Fixed in stage3 (step 1c). Full re-run required:
```bash
bash scripts/run_stage34.sh
```

#### Known failures
- **d5896**: config fixed (formulation_filter added), pool stale → needs Stage 1 rebuild
  ```bash
  python -u scripts/stage1_build_pool.py --config configs/d5896.yaml --output-root /home/rbc58/mnt/ecg-tte
  bash scripts/run_stage34.sh --trials "d5896"
  ```
- **4 others (impact, ontarget, savor_timi, transcend — TBD)**: undiagnosed, may resolve after required_icd fix

## Architecture

### Config-driven design
Each trial = one YAML in `configs/`. All clinical logic (arms, I/E criteria, endpoints, ECG window,
published HR) in YAML; all data paths on CLI. `arms:` entries support `formulation_filter: {require: [...],
exclude: [...]}` ANDed onto the keyword-OR mask. `skip_washout: true` per arm disables cross-arm
prior-use check (needed for switching trials like PARADIGM-HF).

### `cohort_utils.py::identify_arms_generic()`
Arm assignment via earliest first-dispense date per arm. Ties go to first arm in `arms_spec`.
Produces `prior_<arm_name>_days` for every arm pair.

### `stage3_filter.py`
Generic across trials. Handles composite endpoints (`event_primary`/`time_to_primary`).
Per-arm `skip_washout` logic reads from `args._yaml_cfg`.

### `stage4_analyze.py`
5-rung comparator ladder. Auto-detects `event_primary`/`time_to_primary` if present.
`--event-col` / `--time-col` CLI override also available.

### `stage5_meta.py`
Cross-trial meta-analysis. Reads `results_summary.csv` + `published_hr` from configs.
Run after full 32-trial stage3+4 completes.

### Streamlit drug explorer (new)
```bash
streamlit run scripts/drug_explorer_app.py -- \
    --drug-master /home/rbc58/mnt/ecg-tte/drugs/home_meds_cmp.parquet
# Local: ssh -L 8501:localhost:8501 <cluster>, open http://localhost:8501
```

## Cluster paths
```
ECG signals:     /mnt/raid0/bb2238/signals/preprocessed/all_ecgs/{fileID}.npy
ECG metadata:    /home/rbc58/mnt/ecg-tte/ecg_metadata.parquet
Echo metadata:   /home/rbc58/mnt/ecg-tte/echo_accession_number.parquet
Drug master OLD: /home/rbc58/mnt/ecg-tte/drug_master.parquet  ← CarDS_ECG source, DO NOT USE
Drug master NEW: /home/rbc58/mnt/ecg-tte/drugs/*.parquet      ← building now
OMOP person:     /home/rbc58/mnt/ascvd/omop_database/person/person.parquet
OMOP condition:  /home/rbc58/mnt/ascvd/omop_database/condition_occurrence/
OMOP death:      /home/rbc58/mnt/ascvd/omop_database/death/death.parquet
OMOP visit:      /home/rbc58/mnt/ascvd/omop_database/visit_occurrence/
Output root:     /home/rbc58/mnt/ecg-tte/
Embed dir:       /mnt/raid0/rbc58/ecg-tte/embeddings
Raw EHR meds:    see CLAUDE.md "Raw EHR Medication Sources" section
```

## Priority order for next session
1. Verify drug_master build completed — check `ls -lh /home/rbc58/mnt/ecg-tte/drugs/`
2. Spot-check: sacubitril/enalapril present in home_meds shards (use drug_explorer_app.py)
3. Run PARADIGM-HF Stage 1 with new drug_master
4. Re-run full 32-trial stage3+4 (`bash scripts/run_stage34.sh`) — required_icd fix
5. Rebuild d5896 Stage 1 pool
6. Diagnose 4 unknown failures (may resolve after step 4)
7. Re-run stage5_meta.py
