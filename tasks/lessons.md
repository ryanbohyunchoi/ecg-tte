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

## `--n-imputations 1` is a backward-compat contract

- `1` must reproduce the legacy complete-case numbers byte-for-byte. Imputation +
  pooling engages only at `m ≥ 2`. Verify before/after on an existing run.
