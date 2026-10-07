# PS-Flags: source panels and window check (paper2, step B)

Written 2026-10-07 by the step-B agent. Code: `scripts/v21/ps_flags.py` (source panels) and `scripts/v21/paper2_grid.py::flags_matrix` (the design used in the PS). Restricted panels: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/flags/restricted_flags_<trial>.parquet`; aggregates: `core/flags/flags_build.csv` and `core/log.json`.

## What PS-Flags is

PS-Flags = PS-Demo (age, sex, index year; `T.demo`) + one yes/no flag per ICD-10 3-character diagnosis code. No dates, no counts, no recency.

| Item | Rule |
|---|---|
| Source | OMOP gold `condition_occurrence`, `condition_source_value` (100% of condition rows map to an ICD10CM source concept in 2005–2024, so there is no ICD-9 mixing) |
| Feature | `dx_` + first 3 characters of the source code with the dot removed (the `build_preindex_panel.py` rule, copied verbatim) |
| Window | `condition_start_date >= index − 36,500 d` and `condition_start_date < index`, i.e. the full pre-index history; **the index day is excluded** |
| Value | binarised: distinct-day count > 0 |
| Cohort | flags are reindexed to `T.keys` from `v16_engine.load_trial` (the exact cohort of sens_primary32 / v18; already intersected with ECG and CLMBR-T availability). Patients with no diagnosis in the window get all zeros |
| Prevalence | kept if prevalence ≥ 1% **in `T.keys`** (and < 100%) |
| Exposure features | `roles["exposure_features"]` removed. These are all `rx_` drug-name features, so 0 dx flags were removed in every trial |
| Pattern check | only `dx_[A-Z][0-9][0-9A-Z]` kept; 0 stored codes failed the pattern in any trial |

**Why an importer instead of running `build_preindex_panel.py`.** Its query builder is a closure inside `main()`, so it cannot be imported. Run as-is, it would also build rx/px/lab/visit features over the full history, which paper2 does not use. `ps_flags.py` copies the dx SQL verbatim: the same window predicate, feature expression and distinct-day count. Two things differ:
- `person_id` is taken directly from the roster, which the script also does when the roster has `person_id`. All 38 rosters have it.
- The prevalence filter is applied later, on `T.keys`, not on the roster. The source panel stores every code with ≥0.1% roster prevalence. That bound never binds: `T.keys` is ≥ 41% of every roster (lowest VALUE, 41%), so a code at ≥1% in `T.keys` is at ≥0.41% in the roster.

The roster is the cohort file `v13_common.Trial` reads for the index date (`{A}/{cdir}/restricted_cohort.parquet`). Every one of the 38 × `T.keys` is present in its roster (`n_keys_not_in_roster` = 0).

## Window check against the CLMBR-T input window (docs/v18/CLMBR_LEAKAGE.md)

| | PS-Flags | CLMBR-T input |
|---|---|---|
| Start | index − 36,500 d (= all available history; data effectively start in 2012) | all available history |
| End | `condition_start_date < index date` → last day = index − 1 | events with time < index midnight (`build_comet_meds.py`: `t >= cut` dropped, cut = index date 00:00; date-only events stamped 00:00) → last day = index − 1 |
| Index day | excluded | excluded |
| Same index date | roster index date = `T.index_date` source | MEDS roster index date = cohort index date for every analysed patient (CLMBR_LEAKAGE §a) |
| Condition source | `condition_source_value` (ICD-10-CM) | `condition_concept_id` (standard concept) of the same rows, plus drugs, procedures, measurement codes and visits |
| Truncation | none | last 4,096 tokens. Truncation affects 0.3–5.7% of roster patients per trial (`claude-<trial>-clmbr-codeonly/report/summary.json`: highest RAFT-AF 5.7%, PROTECT AF 5.6%, EMPEROR-Preserved 5.3%), so for those patients CLMBR-T sees *less* early history than PS-Flags |

**Verdict.** The windows match: same index date, same end (index − 1), index day excluded in both, and full history in both. Observed `min_days_before_index` = 1 in every trial, so no index-day row enters the flags.

The only asymmetry is CLMBR-T's 4,096-token truncation. It is small, and it works *against* CLMBR-T in the head-to-head. PS-Flags therefore has at least the diagnosis information CLMBR-T has, minus timing, counts and the non-diagnosis domains.

## Feature counts per trial

Number of flags in the PS (`n_flags`): median 529, range 426–622. That is 426–622 binary columns plus 3 demographic columns.

`retain_Flags_base_main` = matched anchors / smaller arm, PS-Flags base, 1:1 caliper 0.2. Compare with P5 base: median 0.99, min 0.37 (`core/retention_sens.csv`, `core/per_trial.csv`). Suppressed cells (1–10 pairs) are shown as < 0.02.

**Overfitting and retention.** Several hundred binary flags in an L2 (C = 1) logistic PS separate the arms strongly in small cohorts.
- In PROTECT AF (1,442 patients, 622 flags), PS-Flags keeps fewer than 11 matched pairs (retention < 0.02). Its in-sample PS AUC is 1.00 (`review/restricted_flag_proxies.csv`).
- With `m13` (1:3 matching) plus embeddings, PROTECT AF has no pair within the caliper at all. These three cells are recorded as failed (`cell_failed`), and the trial drops out of those contrasts.
- **Flags-base retention, main configuration:**
  - S32: median 0.72; 13/32 trials < 0.70; mean 0.735 over the 31 trials with ≥ 11 pairs;
  - S38: median 0.78;
  - P5 base for comparison: median 0.99 in both sets.
- **Cross-validated C** (5-fold log-loss, `paper2_grid.py flagscv`, per-trial values in `core/flagscv_log.csv`) is 3e-4 to 3e-3 for PS-Flags, i.e. 300–3,000× stronger regularisation than the specified C = 1. The CV-tuned PS-Flags is reported as a fairness sensitivity in `PAPER2_RESULTS.md` §4.

**Privacy.** Cells with 1–10 matched pairs are suppressed. So are the columns that would recover their counts:
- `ess_t`, `ess_c` and `retain` in `core/cells.csv` and `core/per_trial.csv`;
- the most-prevalent-flag prevalence when its complement is 1–10 patients (`flag_prev_max`, PROTECT AF);
- `pct_with_any_dx` in `flags/flags_build.csv` when 1–10 patients have no diagnosis.

These blanks are applied by `paper2_grid.py privacy`, which also scans every CSV in `core/`.

This is a property of the specified design (the same L2 PS model as every other rung), not of the panel. It is reported, not corrected.

| trial | set | roster_n | n_keys | n_keys_not_in_roster | n_codes_stored | n_expo_removed | n_flags | flag_prev_median | flag_prev_max | min_days_before_index | median_history_years | retain_Flags_base_main |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| comet | S32 | 7499 | 6381 | 0 | 985 | 0 | 508 | 0.033 | 0.922 | 1 | 3.400 | 0.70 |
| paradigm-hf-seq | S32 | 6880 | 5129 | 0 | 1007 | 0 | 542 | 0.037 | 0.958 | 1 | 5.100 | 0.92 |
| transform-hf | S32 | 18799 | 15657 | 0 | 1005 | 0 | 533 | 0.034 | 0.835 | 1 | 5.000 | 0.95 |
| elite-ii | S32 | 4892 | 3222 | 0 | 928 | 0 | 498 | 0.034 | 0.842 | 1 | 4.000 | 0.69 |
| life | S32 | 3131 | 3131 | 0 | 937 | 0 | 490 | 0.029 | 0.884 | 1 | 4.600 | 0.81 |
| plato | S32 | 7980 | 6759 | 0 | 945 | 0 | 479 | 0.030 | 0.795 | 1 | 4.600 | 0.78 |
| aristotle | S32 | 25862 | 18771 | 0 | 953 | 0 | 526 | 0.033 | 0.828 | 1 | 5.200 | 0.77 |
| rocket-af | S32 | 10954 | 7055 | 0 | 900 | 0 | 495 | 0.030 | 0.823 | 1 | 3.500 | 0.56 |
| rely | S32 | 6714 | 4172 | 0 | 867 | 0 | 465 | 0.032 | 0.821 | 1 | 2.800 | 0.96 |
| allhat | S38 only | 58535 | 26592 | 0 | 887 | 0 | 468 | 0.027 | 0.899 | 1 | 4.500 | 1.00 |
| emperor-preserved-v2 | S32 | 3110 | 2417 | 0 | 1022 | 0 | 609 | 0.046 | 0.986 | 1 | 7.100 | 0.35 |
| east-afnet4 | S32 | 19295 | 16109 | 0 | 983 | 0 | 552 | 0.035 | 0.902 | 1 | 4.700 | 0.98 |
| cabana-v2 | S32 | 15882 | 13133 | 0 | 978 | 0 | 544 | 0.034 | 0.926 | 1 | 5.100 | 0.98 |
| ontarget | S38 only | 33255 | 14853 | 0 | 868 | 0 | 461 | 0.027 | 0.788 | 1 | 4.100 | 0.83 |
| value | S38 only | 64974 | 26657 | 0 | 886 | 0 | 470 | 0.028 | 0.877 | 1 | 4.500 | 0.99 |
| ascot | S38 only | 59023 | 26021 | 0 | 916 | 0 | 468 | 0.028 | 0.862 | 1 | 4.400 | 0.82 |
| empa-reg | S32 | 9689 | 5649 | 0 | 989 | 0 | 577 | 0.040 | 0.980 | 1 | 5.900 | 0.55 |
| carolina | S32 | 4709 | 1794 | 0 | 934 | 0 | 505 | 0.032 | 0.945 | 1 | 4.400 | 0.55 |
| leader | S32 | 7071 | 3782 | 0 | 936 | 0 | 548 | 0.037 | 0.966 | 1 | 4.500 | 0.89 |
| sustain6 | S32 | 7134 | 3727 | 0 | 1002 | 0 | 604 | 0.043 | 0.986 | 1 | 7.600 | 0.43 |
| rewind | S38 only | 14742 | 6049 | 0 | 925 | 0 | 546 | 0.035 | 0.964 | 1 | 4.900 | 0.87 |
| declare | S38 only | 16176 | 6967 | 0 | 937 | 0 | 548 | 0.036 | 0.960 | 1 | 4.800 | 0.52 |
| canvas | S32 | 15311 | 6037 | 0 | 925 | 0 | 524 | 0.034 | 0.951 | 1 | 4.000 | 0.96 |
| tecos | S32 | 5373 | 2925 | 0 | 902 | 0 | 512 | 0.034 | 0.926 | 1 | 4.200 | 0.71 |
| carmelina | S32 | 2672 | 1546 | 0 | 1007 | 0 | 565 | 0.040 | 0.955 | 1 | 5.100 | 0.39 |
| valiant | S32 | 3002 | 2096 | 0 | 822 | 0 | 426 | 0.027 | 0.667 | 1 | 3.300 | 0.71 |
| insight | S32 | 20008 | 8847 | 0 | 873 | 0 | 456 | 0.029 | 0.940 | 1 | 4.800 | 0.94 |
| affirm | S32 | 23030 | 17634 | 0 | 938 | 0 | 535 | 0.036 | 0.956 | 1 | 4.800 | 0.96 |
| af-chf | S32 | 7060 | 5558 | 0 | 968 | 0 | 551 | 0.038 | 0.957 | 1 | 4.500 | 0.92 |
| precision | S32 | 13991 | 5310 | 0 | 969 | 0 | 542 | 0.037 | 0.853 | 1 | 4.700 | 0.65 |
| amplify | S32 | 6885 | 5080 | 0 | 1095 | 0 | 621 | 0.038 | 0.744 | 1 | 5.900 | 0.58 |
| lodestar | S32 | 35032 | 22277 | 0 | 960 | 0 | 532 | 0.032 | 0.805 | 1 | 5.200 | 0.41 |
| prove-it | S32 | 5382 | 4379 | 0 | 900 | 0 | 456 | 0.029 | 0.732 | 1 | 3.300 | 0.93 |
| frail-af | S32 | 5137 | 3714 | 0 | 866 | 0 | 484 | 0.036 | 0.993 | 1 | 3.900 | 0.94 |
| laaos3 | S32 | 2869 | 2621 | 0 | 992 | 0 | 535 | 0.034 | 0.878 | 1 | 6.100 | 0.73 |
| protect-af | S32 | 1809 | 1442 | 0 | 1069 | 0 | 622 | 0.046 | >0.99 (complement suppressed) | 1 | 7.500 | <0.02 (fewer than 11 matched pairs) |
| raft-af | S32 | 3575 | 3003 | 0 | 1044 | 0 | 606 | 0.045 | 0.985 | 1 | 6.300 | 0.52 |
| active-w | S32 | 4939 | 3139 | 0 | 899 | 0 | 481 | 0.033 | 0.853 | 1 | 3.300 | 0.57 |

Columns: roster_n = cohort roster size; n_keys = analysed cohort (T.keys); n_codes_stored = codes with >= 0.1% roster prevalence in the source panel; n_expo_removed = exposure features removed among dx codes; flag_prev_* = prevalence of kept flags in T.keys; min_days_before_index = smallest (index - diagnosis date) in the window; median_history_years = median over patients of (index - earliest diagnosis date).
