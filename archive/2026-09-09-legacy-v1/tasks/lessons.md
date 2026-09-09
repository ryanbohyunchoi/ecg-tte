# Lessons

Correction log — record non-obvious mistakes and the fix so they aren't repeated.
Format per entry: **Symptom → Root cause → Fix → Guardrail.**

---

## Do not impute structurally-complete binary covariates

- **Symptom:** temptation to run every covariate through the imputer to "fill missing values."
- **Root cause:** comorbidity / medication / ICD-proxy flags encode absence as literal `0`
  via `.isin(...).astype(int)` (`cohort_utils.py:1304,1381`; `conds_within`). They never
  contain `NaN` — "no code" and "truly missing" are indistinguishable **by design**.
- **Fix:** imputation is confined to continuous covariates with real `NaN` (echo EF,
  ECG intervals, labs, vitals). Binaries pass through untouched (`0` = observed-absent).
  See `scripts/imputation.py::split_covariates`.
- **Guardrail:** imputing a 0-encoded binary fabricates comorbidities and biases the PS model.

## Caliper must be on logit(PS) in SD units, not raw PS

- **Symptom:** matched-N and balance shift unpredictably when the covariate set changes.
- **Root cause:** the old `structured_psm` caliper (0.25) was compared against Euclidean
  distance on the **raw** propensity score, whose spread depends on how many features
  LASSO retained — so a fixed raw caliper is a moving target.
- **Fix:** match on `logit(PS)` with caliper `= 0.20 × SD(logit(PS))` (Austin default).
- **Guardrail:** report `caliper_sd × SD` and the resulting width each run.

## MICE: match within, pool effects — never pool PS or matched sets

- **Root cause of bias if violated:** averaging propensity scores or matched sets across
  imputations mixes draws and breaks Rubin's-rules variance accounting.
- **Fix:** per imputation, fit PS → match → Cox; pool **log-HR** with Rubin's rules
  (`pool_rubin`). Freeze the LASSO feature set on imputation #1 so the PS model is
  identical across draws. Include treatment + Nelson-Aalen cumulative hazard + event
  indicator in the imputation predictor matrix (White & Royston); never impute the outcome.

## A new pool covariate must clear TWO output whitelists, not one

- **Symptom:** labs/vitals loaded in stage1 (print confirmed counts) but were
  absent from the stage3 cohort and the balance table.
- **Root cause:** two independent column whitelists gate the flow —
  `POOL_COLS` in `stage1_build_pool.py` (before `pool.parquet` write) AND
  `OUTPUT_COLS` in `stage3_filter.py` (before the cohort write). A covariate
  dropped by either never reaches stage4. Only the stage3 gate was updated first.
- **Fix:** add new config-driven covariates (labs/vitals `+ _measured`, zcodes)
  to `config_flag_cols` in stage1 **and** `_cfg_flag_names` in stage3.
- **Guardrail:** after wiring a new covariate, run `feature_inventory.py --cohort`
  on the rebuilt cohort — "ABSENT" there means a whitelist dropped it.

## Bound MICE draws; sparse covariates need a missingness cap

- `IterativeImputer(sample_posterior=True)` draws outside physiologic range
  (EF>100) → variance inflates ~10×, deflating SMD and faking good balance.
  Fix: per-column `min_value`/`max_value` = observed [min,max] + post-clip.
- Matching on a >50%-missing (majority-imputed) covariate inflates FMI for a
  usually-weak confounder. `--max-missing-frac` (default 0.5) drops it from the
  PS model but keeps it in the balance table. On PARADIGM this cut FMI 0.46→0.15.
- Complete-case can flip the effect direction vs MICE when missingness is
  differential by arm (PARADIGM EF: 17% treated vs 36% control) — CC HR 1.14
  ("harm") vs MICE 0.91 ("benefit"). Prefer MICE; report CC as sensitivity only.

## `--n-imputations 1` is a backward-compat contract

- `1` must reproduce the legacy complete-case numbers byte-for-byte. Imputation +
  pooling engages only at `m ≥ 2`. Verify before/after on an existing run.
