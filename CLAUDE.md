# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Target trial emulation (TTE) of cardiovascular RCTs using Yale EHR + OMOP data. Hypothesis: hybrid matching via PSM + cosine similarity on ECG waveform embeddings improves emulation fidelity over PSM alone. Framework follows RCT-duplicate (JAMA 2022; https://jamanetwork.com/journals/jama/fullarticle/2804067).

Pipeline is templated for 32-trial expansion. 
## Pipeline Architecture (`scripts/`)

Four-stage sequential pipeline. Stages 1–3 produce parquet/npy intermediates cached on disk; Stage 4 reads them.

```
stage1_build_pool.py   → pool/ecg_candidates.parquet
                                ↓
stage2_embed.py        → embeddings/{fileID}.npy + embedding_manifest.json
                                ↓
stage3_filter.py       → runs/{run_name}/comet_cohort.parquet + attrition.csv
                                ↓
stage4_analyze.py      → forest plots, balance tables, KM curves, diagnostics
```

**Stage 1** (`stage1_build_pool.py`): Wide candidate pool builder. Reads OMOP (person, condition_occurrence, drug_master) + ECG metadata. Identifies carvedilol/metoprolol new-user pairs, attaches all covariates (ICD proxies, drugs, echo EF, ECG intervals). Run once per data refresh.

**Stage 2** (`stage2_embed.py`): Embeds ALL pool ECGs via BCL encoder (ECGFounder backbone Net1D → MLP projector → 512D L2-normalised). Reads `ecg_candidates.parquet`. Resumable: skips already-embedded fileIDs. Does not embed per-patient — embeds every unique fileID so Stage 3 can change the ECG selection window without re-embedding.

**Stage 3** (`stage3_filter.py`): Fast filter (< 1 min, no OMOP reads). Applies configurable I/E criteria via CLI args or YAML. Outputs `comet_cohort.parquet` + `attrition.csv` + `filter_manifest.json` (all args + git SHA). Override arm names and criteria per trial via `--config path/to/yaml`.

**Stage 4** (`stage4_analyze.py`): Comparator ladder:
1. Unadjusted Cox
2. Adjusted Cox (age, sex, key comorbidities)
3. PSM-sparse (age, sex, htn, t2d, cad )
4. PSM-rich (same as RCT-duplicate)
5. ECG nearest-neighbour PRIMARY (pre-specified cosine threshold <0.3)
6. Hybrid PSM + ECG NN approach  
8. Forest plot with optional `--published-hr` overlay

Denominator standardization: `--denominator strict` (default) runs all methods on D = (ECG-available) ∩ (rich-covariates complete). Use `--denominator both` to add ECG-NN sensitivity on the larger ECG-available cohort.

## Key Design Decisions

## Cluster Paths

- ECG signals: `/mnt/raid0/bb2238/signals/preprocessed/all_ecgs/{fileID}.npy`
- ECG metadata: `/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet`
- OMOP person: `/home/rbc58/mnt/ascvd/omop_database/person/person.parquet`
- OMOP condition: `/home/rbc58/mnt/ascvd/omop_database/condition_occurrence/condition_occurrence_*.parquet`
- Experiment outputs: `/home/rbc58/mnt/ecg-tte` or `/mnt/raid0/rbc58/` (project subdirs)

## Cluster Workflow

- Code written locally, pushed to GitHub, pulled and run on Yale H100 cluster.
- **Never hardcode local paths.** All data paths via CLI args or YAML config.
- **All scripts runnable from CLI** with `argparse`. No training/inference locally.

## Patient Data Safety

- **Never print, log, or expose patient-level data** (MRNs, AccessionNumbers, dates, ages, names).
- **Never commit CSVs, label files, or any files with patient identifiers.**
- Add `*.csv`, `data/`, `labels/` to `.gitignore` as needed.

## Stack

```
torch>=2.1.0, numpy, pandas, pyarrow, wandb, PyYAML, tqdm, einops, lifelines, sklearn, scipy, matplotlib
```

YAML configs via PyYAML; `argparse` for CLI overrides. `wandb` for experiment tracking. `lifelines` for survival analysis.

## Workflow Rules

1. **Plan first**: write plan to `tasks/todo.md` before implementation; check in before starting.
2. **Track progress**: mark items complete as you go; update `tasks/lessons.md` after corrections.
3. **Log changes**: add entry to `README.md` for every new experiment or change each session.
4. **Subagents**: offload exploration/research to subagents to keep main context clean.
5. **Verify before done**: prove it works; never mark complete without evidence.
6. **Bug reports**: fix autonomously — no hand-holding needed.
