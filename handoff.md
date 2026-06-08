# Handoff — ecg-tte pipeline

## What this repo is
Target trial emulation of 32 RCT-DUPLICATE (Wang et al. JAMA 2023) cardiac trials using Yale OMOP EHR. Methodological advance: hybrid PSM + ECG waveform embedding (cosine-distance) matching. All code runs on Yale H100 cluster; write locally → push → pull → run.

## Current status (2026-06-07)
Stage 0 (feasibility checker) and Stage 1 (pool builder) foundation built. All 32 trial configs written and validated. Stage 0 ran successfully with `--limit-persons 5000` smoke test; full run OOM-killed → fix pushed (see below).

### Pending on cluster
- `git pull` to get the OOM fix
- Re-run Stage 0 sweep (see command below)
- After Stage 0 passes: run Stage 1 for GO trials

## What was built this session

### New files
| File | Purpose |
|---|---|
| `scripts/stage0_feasibility.py` | Per-trial GO/NO-GO checker; aggregate-only outputs |
| `scripts/stage1_build_pool.py` | Config-driven pool builder (replaces COMET-specific) |
| `scripts/lint_configs.py` | Validates all configs/*.yaml |
| `scripts/cohort_utils.py` | Complete rewrite — generic arm ID, endpoint builder, loaders |
| `configs/_schema.md` | YAML schema docs |
| `configs/comet.yaml` | COMET regression gate config |
| `configs/*.yaml` (32 total) | All RCT-DUPLICATE trial configs |
| `README.md` | Project overview |
| `.gitignore` | Excludes parquet/csv/data dirs |

### Key modifications
- `scripts/stage3_filter.py` — added `--cohort-filename` arg (backward-compat shim)

## Architecture

### Config-driven design
Each trial = one YAML in `configs/`. Stage 1 reads `--config configs/{trial}.yaml`. All clinical logic (arms, I/E criteria, endpoints, ECG window) in YAML; all data paths on CLI.

### Stage flow
```
stage0_feasibility.py  →  _feasibility/feasibility_{trial}.json + summary.csv
stage1_build_pool.py   →  {trial}/pool/pool.parquet + ecg_candidates.parquet
stage2_embed.py        →  embeddings/{fileID}.npy + embedding_manifest.json
stage3_filter.py       →  runs/{run}/comet_cohort.parquet  (still COMET-locked; multi-trial deferred)
stage4_analyze.py      →  forest plots, KM curves, Cox + PSM + ECG-NN ladder
```

### COMET backward compat
Running stage1 with `configs/comet.yaml` produces identical output to old COMET-specific stage1.
`stage3_alias` in comet.yaml → `first_carv_date`, `prior_meto_days` alias columns preserved.

### Key constraints (do not change)
- `balance.py` `SMD_COLS` frozen at 37 — don't edit
- `ecg.window_days` always < 90 (enforced by `validate_config()`)
- Death table is date-only — all-cause mortality proxies CV death everywhere
- Stage 3 arm masks still hardcode carv/meto → full multi-trial Stage 3 is future work

## Cluster paths
```
ECG signals:    /mnt/raid0/bb2238/signals/preprocessed/all_ecgs/{fileID}.npy
ECG metadata:   /home/rbc58/mnt/ecg-tte/ecg_metadata.parquet
Echo metadata:  /home/rbc58/mnt/ecg-tte/echo_accession_number.parquet
Drug master:    /home/rbc58/mnt/ecg-tte/drug_master.parquet
OMOP person:    /home/rbc58/mnt/ascvd/omop_database/person/person.parquet
OMOP condition: /home/rbc58/mnt/ascvd/omop_database/condition_occurrence/
OMOP death:     /home/rbc58/mnt/ascvd/omop_database/death/death.parquet
OMOP visit:     /home/rbc58/mnt/ascvd/omop_database/visit_occurrence/
Output root:    /home/rbc58/mnt/ecg-tte/
```

## Last bug fixed (not yet re-tested on cluster)
**Problem**: Stage 0 OOM-killed when loading full person table + drug master.  
**Root cause**: `pd.read_parquet` loaded all columns (person table has 50+ cols; drug master is huge).  
**Fix** (committed, pushed): `parse_person_table` and `load_drug_master` in `cohort_utils.py` now read parquet schema first (zero memory), then request only needed columns. Should cut memory 5-10×.

## Commands to run next

### 1. Pull fix on cluster
```bash
cd /home/rbc58/github/ecg-tte
git pull
```

### 2. Stage 0 — single trial test (confirm OOM fix works)
```bash
python scripts/stage0_feasibility.py \
    --config configs/comet.yaml \
    --person-parquet /home/rbc58/mnt/ascvd/omop_database/person/person.parquet \
    --condition-dir  /home/rbc58/mnt/ascvd/omop_database/condition_occurrence \
    --drug-master    /home/rbc58/mnt/ecg-tte/drug_master.parquet \
    --echo-meta      /home/rbc58/mnt/ecg-tte/echo_accession_number.parquet \
    --ecg-meta       /home/rbc58/mnt/ecg-tte/ecg_metadata.parquet \
    --death-parquet  /home/rbc58/mnt/ascvd/omop_database/death/death.parquet \
    --output-dir     /home/rbc58/mnt/ecg-tte/_feasibility
```

### 3. Stage 0 — full 32-trial sweep (one process per trial for memory safety)
```bash
nohup bash -c '
for cfg in configs/*.yaml; do
    echo "=== $cfg ==="
    python scripts/stage0_feasibility.py \
        --config "$cfg" \
        --person-parquet /home/rbc58/mnt/ascvd/omop_database/person/person.parquet \
        --condition-dir  /home/rbc58/mnt/ascvd/omop_database/condition_occurrence \
        --drug-master    /home/rbc58/mnt/ecg-tte/drug_master.parquet \
        --echo-meta      /home/rbc58/mnt/ecg-tte/echo_accession_number.parquet \
        --ecg-meta       /home/rbc58/mnt/ecg-tte/ecg_metadata.parquet \
        --death-parquet  /home/rbc58/mnt/ascvd/omop_database/death/death.parquet \
        --output-dir     /home/rbc58/mnt/ecg-tte/_feasibility
done
' > /home/rbc58/mnt/ecg-tte/_feasibility/stage0_sweep.log 2>&1 &
echo "PID: $!"
tail -f /home/rbc58/mnt/ecg-tte/_feasibility/stage0_sweep.log
```

### 4. Check results
```bash
cat /home/rbc58/mnt/ecg-tte/_feasibility/feasibility_summary.csv
```

### 5. Stage 1 — COMET regression gate (run after Stage 0 shows GO)
```bash
python scripts/stage1_build_pool.py \
    --config configs/comet.yaml \
    --person-parquet /home/rbc58/mnt/ascvd/omop_database/person/person.parquet \
    --condition-dir  /home/rbc58/mnt/ascvd/omop_database/condition_occurrence \
    --drug-master    /home/rbc58/mnt/ecg-tte/drug_master.parquet \
    --echo-meta      /home/rbc58/mnt/ecg-tte/echo_accession_number.parquet \
    --ecg-meta       /home/rbc58/mnt/ecg-tte/ecg_metadata.parquet \
    --death-parquet  /home/rbc58/mnt/ascvd/omop_database/death/death.parquet \
    --output-root    /home/rbc58/mnt/ecg-tte
```

## Validation checks after Stage 1 COMET
Compare new generic stage1 output vs old:
- `n_carvedilol` and `n_metoprolol` in `build_manifest.json` should match prior run
- Pool columns must include: `first_carv_date`, `prior_meto_days`, `first_meto_date`, `prior_carv_days` (via stage3_alias)
- `event_death`, `time_to_death` must exist (stage3/4 read these)
- `loop_diuretic_90d`, `acei_arb_90d` must exist (balance.py SMD_COLS)

## What's NOT done yet (future sessions)
- Full multi-trial Stage 3 (currently COMET-locked)
- Stage 5 meta-analysis
- PARADIGM-HF ef inclusion in stage3 (config has `ef.threshold: 40.0` but stage3 doesn't read it generically yet)
- Per-trial balance table / SMD_COLS expansion beyond 37
