# v1.6 engine validation (2026-09-26)

`scripts/v16/v16_engine.py --validate`, 18 trials × 6 arms (imputation 1, split seed 0, 1:1 caliper-0.2 matching, L2 C=1 PS). Aggregates only.

**Status: PASS** (estimates: pass, tol 0.0001; held-out |SMD| vs `longtail_imp1_seed0.csv`: pass, tol 1e-06).

## (a) log HR / SE vs `claude-v13-bootstrap/bs_<trial>.csv` (rep 0) and (b) held-out |SMD|

max_d_* = max over arms of |engine − saved|. max_ps_logit_dev = `check_against_saved` (rebuilt PS logit vs saved phase-2 logit). max_dev_smd_imp1 = max over arms × variables of |engine − longtail_imp1_seed0|; *_pooled = vs summary_pooled.csv (mean over 5 imputations × 5 pool-split seeds, so non-zero by design). avail_mismatch = variables available in one source but not the other.

| trial | max_d_loghr | max_d_se | max_ps_logit_dev | max_dev_smd_imp1 | max_dev_smd_pooled | mean_dev_smd_pooled | n_vars | avail_mismatch | n_components | secs_build | secs_cache_load | secs_arms_6 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| comet | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.067181 | 0.007620 | 58 | 0 | 700 | 1.100000 | 0.060000 | 0.040000 |
| paradigm-hf-seq | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.187313 | 0.010518 | 58 | 0 | 593 | 0.900000 | 0.040000 | 0.030000 |
| transform-hf | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.224179 | 0.018534 | 58 | 0 | 587 | 2.100000 | 0.220000 | 0.110000 |
| elite-ii | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.232157 | 0.016417 | 58 | 0 | 507 | 0.600000 | 0.020000 | 0.020000 |
| life | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.175870 | 0.014475 | 58 | 0 | 509 | 0.500000 | 0.030000 | 0.020000 |
| plato | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.137534 | 0.008615 | 58 | 0 | 495 | 0.800000 | 0.040000 | 0.040000 |
| aristotle | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.189452 | 0.010871 | 58 | 0 | 530 | 2.400000 | 0.190000 | 0.120000 |
| rocket-af | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.107076 | 0.012119 | 58 | 0 | 519 | 1.100000 | 0.060000 | 0.040000 |
| rely | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.413216 | 0.023613 | 57 | 0 | 546 | 0.700000 | 0.030000 | 0.030000 |
| allhat | 0.000040 | 0.000000 | 0.000000 | 0.000000 | 0.107252 | 0.007362 | 58 | 0 | 361 | 2.900000 | 0.280000 | 0.100000 |
| emperor-preserved-v2 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.168676 | 0.015727 | 58 | 0 | 645 | 0.600000 | 0.030000 | 0.020000 |
| east-afnet4 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.137035 | 0.006991 | 58 | 0 | 674 | 2.200000 | 0.230000 | 0.200000 |
| cabana-v2 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.130142 | 0.011088 | 58 | 0 | 648 | 1.900000 | 0.140000 | 0.200000 |
| ontarget | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.086408 | 0.005887 | 58 | 0 | 342 | 1.500000 | 0.070000 | 0.070000 |
| value | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.054583 | 0.005136 | 58 | 0 | 335 | 2.700000 | 0.260000 | 0.100000 |
| ascot | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.053970 | 0.005465 | 58 | 0 | 345 | 3.100000 | 0.250000 | 0.080000 |
| empa-reg | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.220272 | 0.012685 | 58 | 0 | 513 | 0.900000 | 0.040000 | 0.030000 |
| carolina | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.309857 | 0.019687 | 58 | 0 | 349 | 0.400000 | 0.010000 | 0.000000 |

Non-zero estimate deviations: ALLHAT sparse arm |Δlog HR| = 4.0e-5 (SE 1.6e-7), identical pair count. The engine's matched set for that arm is identical, patient for patient and pair for pair, to the saved phase-2 matches (`restricted_matches_imp1_seed0.parquet`); the saved bootstrap rep 0 differs at the 5th decimal (most likely a floating-point near-tie in greedy matching or Cox convergence in that earlier run). All other trial × arm estimates agree to < 1e-8. RELY has 57/58 variables (GLS is NaN in both the engine and the saved outputs: unobserved or zero variance).

## Why engine vs `summary_pooled.csv` differs

summary_pooled averages each metric over 25 runs (imputations 1–5 × pool-split seeds 0–4). The seed changes which panel features are in hdPS pool A vs held-out pool B (so `B_mean` and the hdPS arms change) and the imputation changes meds/util and the matched sets of every arm. The engine fixes imputation 1, seed 0 and reproduces `longtail_imp1_seed0.csv` (the (1, 0) member of that average); the pooled deviation is the imputation/seed spread, not an engine error.

## Arm means across trials (engine)

cstat = 5-fold cross-fitted AUC of treatment from all held-out components (median-imputed + missing indicators) in the matched sample; l2 = logistic C = 0.01, gbm = HistGBM (unmatched/sparse/sparse+ECG only).

| arm | mean_smd | cstat_l2 | cstat_gbm | smd_prog |
|---|---|---|---|---|
| unmatched | 0.140 | 0.738 | 0.748 | 0.167 |
| sparse | 0.107 | 0.665 | 0.674 | 0.078 |
| sparse+ECG | 0.101 | 0.651 | 0.665 | 0.071 |
| hdPS200 | 0.091 | 0.593 | – | 0.047 |
| hdPS200+ECG | 0.081 | 0.587 | – | 0.040 |
| clinical (reference) | 0.081 | 0.630 | – | 0.060 |

## Paired smoke test of `summarize_pairs` (a − b; negative favours a)

| arm_a | arm_b | n_trials | d_absd | k_absd | p_absd | d_z2 | k_z2 | p_z2 | d_mean_smd | k_mean_smd | p_mean_smd | d_cstat | k_cstat | p_cstat | cons_a | phi_a | cons_b | phi_b | q_absd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sparse+ECG | sparse | 18 | -0.020 | 14/18 | 0.264 | -1.403 | 14/18 | 0.024 | -0.007 | 14/18 | 0.026 | -0.013 | 15/18 | 0.023 | 77.778 | 3.411 | 61.111 | 4.696 | 0.397 |
| hdPS200+ECG | hdPS200 | 18 | -0.002 | 10/18 | 0.918 | -0.565 | 10/18 | 0.242 | -0.010 | 15/18 | 0.003 | -0.007 | 12/18 | 0.048 | 72.222 | 2.706 | 55.556 | 3.275 | 0.918 |
| sparse | unmatched | 18 | -0.098 | 15/18 | 0.019 | -9.081 | 15/18 | 0.002 | -0.032 | 17/18 | 0.000 | -0.074 | 18/18 | 0.000 | 61.111 | 4.696 | 50.000 | 13.843 | 0.056 |

## Runtime (seconds per cell, 1 thread; includes PS fit, matching, Cox, 58-variable SMD and C-statistic)

| arm | cstat_model | median | max |
|---|---|---|---|
| clinical (reference) | l2 | 0.37 | 2.85 |
| hdPS200 | l2 | 0.41 | 3.14 |
| hdPS200+ECG | l2 | 0.39 | 3.11 |
| sparse | gbm | 20.80 | 39.76 |
| sparse | l2 | 0.42 | 3.23 |
| sparse+ECG | gbm | 20.23 | 39.29 |
| sparse+ECG | l2 | 0.81 | 9.78 |
| unmatched | gbm | 30.33 | 41.54 |
| unmatched | l2 | 0.90 | 4.04 |

Other estimators / PS model (sparse+ECG, l2 C-statistic):

| estimator | median | max |
|---|---|---|
| ('iptw',) | 0.80 | 3.86 |
| ('match', 0.05, 1) | 0.38 | 2.80 |
| ('match', 0.2, 3) | 0.74 | 9.78 |
| ('overlap',) | 0.77 | 3.54 |
| gbm-PS match | 2.05 | 5.28 |

Median seconds per cell by trial (l2 C-statistic, 1:1 matching; all six arms):

| trial | n | median_secs_per_cell |
|---|---|---|
| comet | 6381 | 0.56 |
| paradigm-hf-seq | 5129 | 0.29 |
| transform-hf | 15657 | 0.28 |
| elite-ii | 3222 | 0.24 |
| life | 3131 | 0.26 |
| plato | 6759 | 0.41 |
| aristotle | 18771 | 0.66 |
| rocket-af | 7055 | 0.42 |
| rely | 4172 | 0.17 |
| allhat | 26592 | 2.40 |
| emperor-preserved-v2 | 2417 | 0.15 |
| east-afnet4 | 16109 | 1.15 |
| cabana-v2 | 13133 | 0.43 |
| ontarget | 14853 | 1.52 |
| value | 26657 | 2.91 |
| ascot | 26021 | 3.08 |
| empa-reg | 5649 | 0.33 |
| carolina | 1794 | 0.14 |

Trial build (uncached) median 1 s (max 3 s); cached load median 0.1 s. Building the six designs with `T.arms` (incl. hdPS re-ranking) median 0.0 s (max 0.2 s) per trial; not included in the per-cell times. A trial × cell with the gbm C-statistic costs roughly the gbm row above.
