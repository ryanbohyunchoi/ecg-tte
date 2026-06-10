# Handoff — ecg-tte pipeline

## What this repo is
Target trial emulation of 32 RCT-DUPLICATE (Wang et al. JAMA 2023) trials using Yale OMOP EHR. Methodological advance: hybrid PSM + ECG waveform embedding (cosine-distance) matching. All code runs on Yale H100 cluster; write locally → push → pull → run.

## Pipeline (current)
```
stage1_build_pool.py   → {trial}/pool/ecg_candidates.parquet (config-driven, all 32 trials)
stage2_embed.py        → embeddings/{fileID}.npy + embedding_manifest.json (shared across trials)
stage3_filter.py       → runs/{run}/comet_cohort.parquet + attrition.csv (generic, all 32 trials)
stage4_analyze.py      → results_summary.csv + forest.png + balance tables (generic, all 32 trials)
stage5_meta.py          → cross-trial meta-analysis vs published RCT HRs (NEW, not yet run)
```

## Current status (2026-06-10)
Stages 1–4 fully generalized — all 32 trials run through `bash scripts/run_stage34.sh` (loop is now resilient: per-trial failures no longer abort the batch). Latest full run: **OK=27 SKIPPED=0 FAILED=5**. `stage5_meta.py` written + smoke-tested locally, not yet run on cluster.

### Comparator ladder (5 rungs, stage4_analyze.py)
1. Unadjusted Cox
2. Adjusted Cox (age, sex, race) — `ADJ_COVS`
3. Structured PSM — `STRUCTURED_COVS` (11 covs: age_at_index, sex_binary, race_black, afib, htn, dm, cad_mi, copd, hyperlipidemia, stroke, prior_hf_code_1yr; column-existence filtered per trial)
4. ECG-NN PRIMARY — cosine ≤ `--abs-threshold` (default 0.30)
5. PS+ECG-NN — PS-caliper on `STRUCTURED_COVS` + cosine NN (the "hybrid")

Note: there is NO separate sparse/rich PSM split anymore — collapsed to single `STRUCTURED_COVS`. CLAUDE.md's description of the ladder (6 rungs incl. PSM-sparse/PSM-rich/embedding-PSM) is now stale relative to the code — not yet reconciled.

`--denominator strict` (default): D = ecg_available ∩ psm_eligible (`denominators.py build_masks`).

### Pending failures (not yet diagnosed)
5 of 32 trials FAILED in the latest `run_stage34.sh` run. One is **d5896** (known cause, see below). The other 4 are unidentified — need:
```bash
cd /home/rbc58/mnt/ecg-tte/_logs
for f in *_stage34.log; do
  if grep -qE "FAILED \(exit|ERROR" "$f"; then
    echo "=== $f ==="
    grep -E "FAILED \(exit|ERROR|Error|Traceback" "$f" | tail -5
  fi
done
```

### d5896 — known issue, fix written but needs Stage 1 rebuild
Root cause: treated arm's bare `BUDESONIDE` keyword also matched budesonide-alone (Pulmicort/Rhinocort) → 328:1 arm split → empty control arm in strict D → would crash with `ZeroDivisionError` in lifelines (now caught gracefully via empty-arm guard in stage4, exits 1 with diagnostic instead of crashing the whole batch).
`configs/d5896.yaml` arm `formulation_filter` already fixed (treated requires FORMOTEROL, control excludes FORMOTEROL/SYMBICORT) — **but arm assignment happens in stage1**, so this requires a Stage 1 pool rebuild for d5896:
```bash
python -u scripts/stage1_build_pool.py --config configs/d5896.yaml --output-root /home/rbc58/mnt/ecg-tte
bash scripts/run_stage34.sh --trials "d5896"
```

## Architecture

### Config-driven design
Each trial = one YAML in `configs/`. All clinical logic (arms, I/E criteria, endpoints, ECG window, published HR) in YAML; all data paths on CLI. `arms:` entries support `formulation_filter: {require: [...], exclude: [...]}` ANDed onto the keyword-OR mask.

### `cohort_utils.py::identify_arms_generic()`
Arm assignment via earliest first-dispense date per arm. **Ties go to the first arm in `arms_spec` (= treated arm) wins.** Produces `prior_<arm_name>_days` for every arm pair, plus `stage3_alias` columns for COMET backward-compat.

### `stage3_filter.py`
Generic across trials: dynamic per-arm attrition counts, generic new-user lookback (`prior_<other_arm>_days`), `--require-hfref` flag (default True, set `false` for non-HF trials), column-existence-guarded exclusion blocks (NOTE+skip if pool lacks a COMET-specific covariate).

### `run_stage34.sh`
Loops Stage 3 → Stage 4 over all configs. Each stage's exit code captured via `${PIPESTATUS[0]}`; nonzero → `FAIL_COUNT++`, `continue` to next trial (does NOT abort the batch). Final line: `Stage3+4 complete: OK=.. SKIPPED=.. FAILED=..`.

### `stage5_meta.py` (new)
Reads each trial's `runs/<run_name>/results_summary.csv` + `published_hr`/`published_hr_ci` from `configs/<trial>.yaml`. For all 5 ladder rungs, computes per-trial log-HR diff vs published, standardized estimate difference (`z_pooled`), regulatory agreement (benefit/harm/null vs 1), CI overlap. Aggregates per method: Pearson r (log HR emulated vs published), mean/var of log-HR diff, mean/var of `z_pooled`, agreement rates. Outputs `meta_results.csv`, `meta_summary.csv`, `meta_scatter.png`, `meta_variance.png`, `meta_zscore.png`. Trials with `published_hr: null` (lead2) or missing `results_summary.csv` (failed trials) are skipped with a NOTE.

### Key constraints (do not change without checking)
- `balance.py` `SMD_COLS` frozen at 37 — used for balance tables/love plots regardless of `STRUCTURED_COVS`.
- `ecg.window_days` always < 90 (enforced by `validate_config()`).
- Death table is date-only — all-cause mortality proxies CV death everywhere.
- `--meto-formulation tartrate_only` path in stage3_filter.py is intentionally COMET-only (non-default flag).

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
Embed dir:      /mnt/raid0/rbc58/ecg-tte/embeddings
```

## Commands to run next

### 1. Pull latest
```bash
cd /home/rbc58/github/ecg-tte
git pull
```

### 2. Diagnose the 4 unknown stage3/4 failures
See "Pending failures" command above. Paste tracebacks back for fixes.

### 3. Rebuild d5896 Stage 1 pool + rerun (after config fix, see above)

### 4. Run Stage 5 meta-analysis (once results exist for ≥3 trials)
```bash
python scripts/stage5_meta.py \
    --output-root /home/rbc58/mnt/ecg-tte \
    --config-dir configs \
    --run-name default
```
Outputs → `/home/rbc58/mnt/ecg-tte/_meta/default/`

## What's NOT done yet (future sessions)
- Diagnose + fix the 4 non-d5896 stage3/4 failures.
- Rebuild d5896 Stage 1 pool with corrected arm config, rerun stage3+4.
- Run stage5_meta.py on full cluster results once all/most trials green.
- Reconcile CLAUDE.md's 6-rung ladder description with actual 5-rung `STRUCTURED_COVS`-based ladder.
- PARADIGM-HF `ef.threshold: 40.0` not yet read generically by stage3.
