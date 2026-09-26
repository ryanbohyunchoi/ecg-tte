# v1.6 extra covariates (race, hyperlipidemia, T2D, CAD, held-out balance candidates)

Built by `scripts/v16/build_v16_covars.py` (exploratory, for `docs/V16_SWEEP_PLAN.md` axis S1 and extra
held-out balance variables). Restricted per-trial files:
`/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars/<trial>.parquet`, keyed by `patient_key`, one row per
row of the trial's cohort roster (`restricted_cohort.parquet`, a superset of `v13_common.Trial.keys`),
with `treated` included. All values are measured strictly before the cohort `index_date`.

## Conventions
- **Windows match `build_core_baseline.py`:** diagnoses = any ICD-10 prefix (dots removed) dated in
  [index−365, index−1]; medication orders = `drug_exposure` token match (same tokeniser,
  `trial_common.create_drug_tokens`); index day excluded.
- **Code source:** OMOP gold `condition_occurrence` **plus** `observation` (OMOP routed many Z/R/W codes,
  e.g. Z68 BMI codes and W00–W19 fall codes, to `observation`). The v1.1 baseline used
  `condition_occurrence` only; all E/I/F codes live there, so for E78/E11/F17 the two agree. All gold
  source values are ICD-10-CM (no ICD-9); SNOMED `condition_concept_id` was not used.
- **Race / ethnicity:** Yale Epic patient table (`clinical-sources-v1` snapshot `Data_2025_04_03_patients`,
  `PATIENT_RACE_ALL`, `PATIENT_ETHNICITY`), linked roster `person_id` → gold `person.person_source_value`
  (MRN) → `PAT_MRN_ID` (digits, leading zeros stripped). Chosen over OMOP `person` because OMOP folds
  "Not Listed" race into Unknown and **maps unknown ethnicity to "Not Hispanic"** (no unknown category).
  Time-invariant (current registration value).

## Definitions
| Column | Definition |
|---|---|
| `race_white` | only listed race is White (after dropping "Unknown"/"Not Listed") |
| `race_black` | any listed race Black or African American (incl. multiracial) |
| `race_asian` | any listed race Asian, Asian Indian, Chinese, Filipino, Japanese, Korean, Vietnamese; not Black |
| `race_other_unknown` | none of the above: AIAN, NHPI, Middle Eastern/North African, other multiracial, Unknown, Not Listed, unlinked |
| `race_unknown` | no informative race (Unknown / Not Listed / blank / unlinked); subset of `race_other_unknown` |
| `race_multiple` | two or more informative races listed |
| `hispanic` | ethnicity Hispanic or Latina/o/x, Puerto Rican, Mexican/Mexican American/Chicano/a, Cuban (unknown → 0) |
| `ethnicity_unknown` | ethnicity Unknown / blank / unlinked |
| `hyperlipidemia` | E78.0–E78.5 (excludes E78.6 lipoprotein deficiency, E78.7 bile-acid, E78.8/E78.9 other) |
| `statin_order_90d` / `statin_order_365d` | statin order in [index−90 / −365, index−1]; tokens = `trial_specs.STATIN` + pravachol, mevacor, lescol, livalo, zypitamag, vytorin, caduet, altoprev. Several trials already carry `statin_order` (90 d) in their v1.1 baseline/PS |
| `hld_or_statin` | `hyperlipidemia` OR `statin_order_365d` (sensitivity; statin is treatment-adjacent, not a pure confounder) |
| `t2d` | E11 (type 2 only; existing v1.1 `diabetes` = E08–E11, E13) |
| `diabetes_v11`, `hypertension_v11`, `hospital_admissions_v11` | copied from `claude-<trial>-baseline-v11/restricted_baseline_observed.parquet` |
| `cad_ihd` | copy of v1.1 `ischemic_heart_disease_or_mi` (I20–I25, 365 d): covers stable angina, ACS, chronic IHD, old MI → sufficient as CAD |
| `tobacco_current` | F17 (nicotine dependence) or Z72.0 (Z72.0 has zero rows in gold) |
| `tobacco_ever` | `tobacco_current` or Z87.891 (history of nicotine dependence) |
| `obesity` | E66.0/.1/.2/.8/.9 (E66.3 overweight excluded) or Z68.3x/Z68.4x (BMI ≥ 30) |
| `frailty_count` | number of 13 frailty-indicator domains with ≥1 code (dx-only adaptation of the Kim/Segal claims frailty indicator domains; DME HCPCS too sparse in gold): dementia (F01–F03, G30, G31); delirium/cognitive (F05, R41); falls (W00–W19, R29.6, Z91.81); gait/mobility (R26); weakness/debility (R53, M62.81); malnutrition/weight loss (E40–E46, R63.4, R63.6, R64); pressure ulcer (L89); incontinence (R32, N39.4, R15); care dependence (Z74, Z99.3); parkinsonism (G20, G21); depression (F32, F33); sensory impairment (H54, H90, H91); osteoporosis/hip fracture (M80, M81, S72). Not a validated index |
| `frailty_any`, `frailty_ge2` | `frailty_count` ≥ 1 / ≥ 2 |
| `inpatient_days_365` | inpatient (9201) days in stays starting in [index−365, index−1], truncated at index−1 (v14 stay-merge rules) |
| `prior_hf_hosp_365` | inpatient stay starting ≥ index−365 and **ending ≤ index−1** with an I50 code dated within the stay |
| `prior_hf_hosp_365_v14` | copy of `claude-<trial>-hf-v14` flag: stay starting in [index−365, **index**] with I50 → can include the index stay (not strictly pre-index; kept for reference) |

## Not built / gaps
- **Area deprivation (ADI):** no ADI/SVI/ZCTA table exists on raid0 (searched file names to depth 6), and
  OMOP gold has no `location` table. The Epic patient table has a current ZIP, so ADI is feasible if a
  ZIP/ZCTA-level ADI file is provided (current address, not address at index).
- **Smoking status from social history / observation values:** not in gold; only dx codes are available.
- **Prior hospitalisations:** already exists (`hospital_admissions`, 9201 visit count in 365 d) but it is in
  the v1.1 core set and so in clinical/sparse PS designs; `inpatient_days_365` is offered as a
  held-out utilisation variable instead.
- Held-out status: none of the new columns are in any existing PS except the v11 copies and
  `statin_order_*` (equal or close to `statin_order` in trials that use it).

## Linkage and coverage
- Roster rows linked to the Yale Epic patient table: 100.00% (unlinked rows get race/ethnicity unknown).
- Agreement of the 4-level race used here with OMOP `race_concept_id` (collapsed the same way): 99.6%.

| Trial | treated arm | comparator arm | roster rows | Trial keys | Trial keys covered |
|---|---|---|---|---|---|
| comet | metoprolol_tartrate_candidate | carvedilol_candidate | 7,499 | 6,381 | 6,381 |
| paradigm-hf-seq | sacubitril_valsartan | acei | 6,880 | 5,129 | 5,129 |
| transform-hf | torsemide | furosemide | 18,799 | 15,657 | 15,657 |
| elite-ii | arb | acei | 4,892 | 3,222 | 3,222 |
| life | arb | beta_blocker | 3,131 | 3,131 | 3,131 |
| plato | ticagrelor | clopidogrel | 7,980 | 6,759 | 6,759 |
| aristotle | apixaban | warfarin | 25,862 | 18,771 | 18,771 |
| rocket-af | rivaroxaban | warfarin | 10,954 | 7,055 | 7,055 |
| rely | dabigatran | warfarin | 6,714 | 4,172 | 4,172 |
| allhat | amlodipine | thiazide | 58,535 | 26,592 | 26,592 |
| emperor-preserved-v2 | sglt2i | dpp4i | 3,110 | 2,417 | 2,417 |
| east-afnet4 | antiarrhythmic | rate_control | 19,295 | 16,109 | 16,109 |
| cabana-v2 | af_ablation | antiarrhythmic | 15,882 | 13,133 | 13,133 |
| ontarget | arb | acei | 33,255 | 14,853 | 14,853 |
| value | arb | amlodipine | 64,974 | 26,657 | 26,657 |
| ascot | amlodipine | beta_blocker | 59,023 | 26,021 | 26,021 |
| empa-reg | sglt2i | dpp4i | 9,689 | 5,649 | 5,649 |
| carolina | linagliptin | glimepiride | 4,709 | 1,794 | 1,794 |

## Prevalence by arm (analysis population = v13_common.Trial keys)
Binary: count (%) of treated / comparator; `<11` = count or its complement in 1–10 (suppressed). Numeric: mean (sd). SMD = treated − comparator, pooled-SD; unadjusted. Missing = fraction NaN (only `prior_hf_hosp_365_v14`/v11 copies can be NaN).

Maximum missing fraction across trials: none.

### comet (treated n = 2,633; comparator n = 3,748)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 2,105 (79.9%) | 2,522 (67.3%) | +0.290 |
| race_black | 304 (11.5%) | 795 (21.2%) | -0.263 |
| race_asian | 40 (1.5%) | 60 (1.6%) | -0.007 |
| race_other_unknown | 184 (7.0%) | 371 (9.9%) | -0.105 |
| race_unknown | 176 (6.7%) | 348 (9.3%) | -0.096 |
| race_multiple | <11 | 13 (0.3%) | -0.015 |
| hispanic | 215 (8.2%) | 377 (10.1%) | -0.066 |
| ethnicity_unknown | 20 (0.8%) | 41 (1.1%) | -0.035 |
| hyperlipidemia | 1,664 (63.2%) | 2,193 (58.5%) | +0.096 |
| statin_order_90d | 1,027 (39.0%) | 1,363 (36.4%) | +0.054 |
| statin_order_365d | 1,317 (50.0%) | 1,822 (48.6%) | +0.028 |
| hld_or_statin | 1,916 (72.8%) | 2,586 (69.0%) | +0.083 |
| t2d | 951 (36.1%) | 1,502 (40.1%) | -0.082 |
| diabetes_v11 | 963 (36.6%) | 1,519 (40.5%) | -0.081 |
| cad_ihd | 1,681 (63.8%) | 2,253 (60.1%) | +0.077 |
| hypertension_v11 | 2,192 (83.3%) | 3,148 (84.0%) | -0.020 |
| tobacco_current | 498 (18.9%) | 785 (20.9%) | -0.051 |
| tobacco_ever | 1,464 (55.6%) | 1,963 (52.4%) | +0.065 |
| obesity | 647 (24.6%) | 928 (24.8%) | -0.004 |
| frailty_any | 1,514 (57.5%) | 1,683 (44.9%) | +0.254 |
| frailty_ge2 | 875 (33.2%) | 837 (22.3%) | +0.245 |
| prior_hf_hosp_365 | 683 (25.9%) | 864 (23.1%) | +0.067 |
| prior_hf_hosp_365_v14 | 1,926 (73.1%) | 2,527 (67.4%) | +0.126 |
| frailty_count | 1.40 (sd 1.81) | 0.92 (sd 1.41) | +0.294 |
| inpatient_days_365 | 12.61 (sd 18.68) | 8.77 (sd 12.76) | +0.240 |
| hospital_admissions_v11 | 1.43 (sd 1.25) | 1.12 (sd 1.10) | +0.270 |

### paradigm-hf-seq (treated n = 1,223; comparator n = 3,906)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 829 (67.8%) | 2,768 (70.9%) | -0.067 |
| race_black | 281 (23.0%) | 752 (19.3%) | +0.091 |
| race_asian | 18 (1.5%) | 40 (1.0%) | +0.040 |
| race_other_unknown | 95 (7.8%) | 346 (8.9%) | -0.039 |
| race_unknown | 90 (7.4%) | 330 (8.4%) | -0.040 |
| race_multiple | <11 | 18 (0.5%) | -0.008 |
| hispanic | 118 (9.6%) | 435 (11.1%) | -0.049 |
| ethnicity_unknown | <11 | 37 (0.9%) | -0.033 |
| hyperlipidemia | 868 (71.0%) | 2,676 (68.5%) | +0.054 |
| statin_order_90d | 484 (39.6%) | 1,308 (33.5%) | +0.127 |
| statin_order_365d | 761 (62.2%) | 2,555 (65.4%) | -0.066 |
| hld_or_statin | 984 (80.5%) | 3,183 (81.5%) | -0.026 |
| t2d | 522 (42.7%) | 1,617 (41.4%) | +0.026 |
| diabetes_v11 | 528 (43.2%) | 1,630 (41.7%) | +0.029 |
| cad_ihd | 837 (68.4%) | 2,309 (59.1%) | +0.195 |
| hypertension_v11 | 1,090 (89.1%) | 3,371 (86.3%) | +0.086 |
| tobacco_current | 235 (19.2%) | 728 (18.6%) | +0.015 |
| tobacco_ever | 677 (55.4%) | 2,033 (52.0%) | +0.066 |
| obesity | 353 (28.9%) | 921 (23.6%) | +0.120 |
| frailty_any | 590 (48.2%) | 2,117 (54.2%) | -0.119 |
| frailty_ge2 | 304 (24.9%) | 1,236 (31.6%) | -0.151 |
| prior_hf_hosp_365 | 526 (43.0%) | 1,196 (30.6%) | +0.259 |
| prior_hf_hosp_365_v14 | 864 (70.6%) | 2,020 (51.7%) | +0.396 |
| frailty_count | 1.05 (sd 1.59) | 1.27 (sd 1.67) | -0.130 |
| inpatient_days_365 | 8.11 (sd 11.74) | 6.75 (sd 13.10) | +0.109 |
| hospital_admissions_v11 | 1.26 (sd 1.39) | 1.01 (sd 1.47) | +0.180 |

### transform-hf (treated n = 697; comparator n = 14,960)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 532 (76.3%) | 11,701 (78.2%) | -0.045 |
| race_black | 119 (17.1%) | 2,073 (13.9%) | +0.089 |
| race_asian | <11 | 138 (0.9%) | -0.023 |
| race_other_unknown | 41 (5.9%) | 1,048 (7.0%) | -0.046 |
| race_unknown | 35 (5.0%) | 990 (6.6%) | -0.068 |
| race_multiple | <11 | 38 (0.3%) | +0.006 |
| hispanic | 39 (5.6%) | 1,145 (7.7%) | -0.083 |
| ethnicity_unknown | <11 | 186 (1.2%) | +0.004 |
| hyperlipidemia | 443 (63.6%) | 8,545 (57.1%) | +0.132 |
| statin_order_90d | 96 (13.8%) | 3,600 (24.1%) | -0.265 |
| statin_order_365d | 187 (26.8%) | 5,539 (37.0%) | -0.220 |
| hld_or_statin | 464 (66.6%) | 9,379 (62.7%) | +0.081 |
| t2d | 305 (43.8%) | 4,711 (31.5%) | +0.255 |
| diabetes_v11 | 308 (44.2%) | 4,766 (31.9%) | +0.256 |
| cad_ihd | 378 (54.2%) | 6,588 (44.0%) | +0.205 |
| hypertension_v11 | 564 (80.9%) | 11,124 (74.4%) | +0.158 |
| tobacco_current | 78 (11.2%) | 2,083 (13.9%) | -0.083 |
| tobacco_ever | 332 (47.6%) | 6,891 (46.1%) | +0.031 |
| obesity | 264 (37.9%) | 3,264 (21.8%) | +0.356 |
| frailty_any | 352 (50.5%) | 8,040 (53.7%) | -0.065 |
| frailty_ge2 | 202 (29.0%) | 4,790 (32.0%) | -0.066 |
| prior_hf_hosp_365 | 207 (29.7%) | 1,884 (12.6%) | +0.428 |
| prior_hf_hosp_365_v14 | 453 (65.0%) | 12,317 (82.3%) | -0.401 |
| frailty_count | 1.20 (sd 1.70) | 1.29 (sd 1.71) | -0.052 |
| inpatient_days_365 | 9.57 (sd 16.20) | 5.97 (sd 10.85) | +0.262 |
| hospital_admissions_v11 | 1.13 (sd 1.47) | 0.99 (sd 1.17) | +0.105 |

### elite-ii (treated n = 1,469; comparator n = 1,753)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 1,150 (78.3%) | 1,435 (81.9%) | -0.090 |
| race_black | 200 (13.6%) | 194 (11.1%) | +0.078 |
| race_asian | <11 | 18 (1.0%) | -0.038 |
| race_other_unknown | 109 (7.4%) | 106 (6.0%) | +0.055 |
| race_unknown | 104 (7.1%) | 102 (5.8%) | +0.051 |
| race_multiple | <11 | <11 | +0.022 |
| hispanic | 109 (7.4%) | 103 (5.9%) | +0.062 |
| ethnicity_unknown | 19 (1.3%) | 20 (1.1%) | +0.014 |
| hyperlipidemia | 841 (57.2%) | 937 (53.5%) | +0.076 |
| statin_order_90d | 332 (22.6%) | 481 (27.4%) | -0.112 |
| statin_order_365d | 523 (35.6%) | 677 (38.6%) | -0.062 |
| hld_or_statin | 928 (63.2%) | 1,078 (61.5%) | +0.035 |
| t2d | 462 (31.4%) | 510 (29.1%) | +0.051 |
| diabetes_v11 | 468 (31.9%) | 516 (29.4%) | +0.053 |
| cad_ihd | 741 (50.4%) | 912 (52.0%) | -0.032 |
| hypertension_v11 | 1,051 (71.5%) | 1,227 (70.0%) | +0.034 |
| tobacco_current | 136 (9.3%) | 199 (11.4%) | -0.069 |
| tobacco_ever | 591 (40.2%) | 750 (42.8%) | -0.052 |
| obesity | 250 (17.0%) | 233 (13.3%) | +0.104 |
| frailty_any | 696 (47.4%) | 943 (53.8%) | -0.129 |
| frailty_ge2 | 386 (26.3%) | 595 (33.9%) | -0.168 |
| prior_hf_hosp_365 | 302 (20.6%) | 336 (19.2%) | +0.035 |
| prior_hf_hosp_365_v14 | 898 (61.1%) | 1,153 (65.8%) | -0.096 |
| frailty_count | 1.11 (sd 1.66) | 1.30 (sd 1.70) | -0.118 |
| inpatient_days_365 | 5.83 (sd 12.76) | 6.64 (sd 13.21) | -0.063 |
| hospital_admissions_v11 | 0.82 (sd 1.10) | 0.98 (sd 1.17) | -0.139 |

### life (treated n = 1,239; comparator n = 1,892)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 752 (60.7%) | 1,286 (68.0%) | -0.152 |
| race_black | 358 (28.9%) | 419 (22.1%) | +0.155 |
| race_asian | 15 (1.2%) | 18 (1.0%) | +0.025 |
| race_other_unknown | 114 (9.2%) | 169 (8.9%) | +0.009 |
| race_unknown | 113 (9.1%) | 155 (8.2%) | +0.033 |
| race_multiple | <11 | <11 | +0.022 |
| hispanic | 124 (10.0%) | 176 (9.3%) | +0.024 |
| ethnicity_unknown | 27 (2.2%) | 26 (1.4%) | +0.061 |
| hyperlipidemia | 559 (45.1%) | 929 (49.1%) | -0.080 |
| statin_order_90d | 133 (10.7%) | 285 (15.1%) | -0.129 |
| statin_order_365d | 291 (23.5%) | 529 (28.0%) | -0.102 |
| hld_or_statin | 621 (50.1%) | 1,008 (53.3%) | -0.063 |
| t2d | 269 (21.7%) | 441 (23.3%) | -0.038 |
| diabetes_v11 | 276 (22.3%) | 453 (23.9%) | -0.040 |
| cad_ihd | 173 (14.0%) | 406 (21.5%) | -0.197 |
| hypertension_v11 | 884 (71.3%) | 1,424 (75.3%) | -0.089 |
| tobacco_current | 127 (10.3%) | 253 (13.4%) | -0.097 |
| tobacco_ever | 342 (27.6%) | 593 (31.3%) | -0.082 |
| obesity | 156 (12.6%) | 301 (15.9%) | -0.095 |
| frailty_any | 420 (33.9%) | 777 (41.1%) | -0.148 |
| frailty_ge2 | 173 (14.0%) | 416 (22.0%) | -0.210 |
| prior_hf_hosp_365 | 0 (0.0%) | 0 (0.0%) | +0.000 |
| prior_hf_hosp_365_v14 | 20 (1.6%) | 62 (3.3%) | -0.108 |
| frailty_count | 0.59 (sd 1.06) | 0.84 (sd 1.35) | -0.205 |
| inpatient_days_365 | 1.94 (sd 9.05) | 4.30 (sd 12.34) | -0.218 |
| hospital_admissions_v11 | 0.32 (sd 0.89) | 0.64 (sd 1.07) | -0.325 |

### plato (treated n = 4,011; comparator n = 2,748)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 3,108 (77.5%) | 2,191 (79.7%) | -0.055 |
| race_black | 446 (11.1%) | 320 (11.6%) | -0.017 |
| race_asian | 90 (2.2%) | 44 (1.6%) | +0.047 |
| race_other_unknown | 367 (9.1%) | 193 (7.0%) | +0.078 |
| race_unknown | 349 (8.7%) | 187 (6.8%) | +0.071 |
| race_multiple | 11 (0.3%) | <11 | +0.004 |
| hispanic | 399 (9.9%) | 215 (7.8%) | +0.075 |
| ethnicity_unknown | 60 (1.5%) | 30 (1.1%) | +0.036 |
| hyperlipidemia | 2,333 (58.2%) | 1,847 (67.2%) | -0.188 |
| statin_order_90d | 863 (21.5%) | 960 (34.9%) | -0.301 |
| statin_order_365d | 1,365 (34.0%) | 1,318 (48.0%) | -0.286 |
| hld_or_statin | 2,540 (63.3%) | 2,027 (73.8%) | -0.226 |
| t2d | 1,195 (29.8%) | 1,020 (37.1%) | -0.156 |
| diabetes_v11 | 1,214 (30.3%) | 1,033 (37.6%) | -0.155 |
| cad_ihd | 2,463 (61.4%) | 2,221 (80.8%) | -0.439 |
| hypertension_v11 | 2,530 (63.1%) | 2,089 (76.0%) | -0.284 |
| tobacco_current | 678 (16.9%) | 498 (18.1%) | -0.032 |
| tobacco_ever | 1,651 (41.2%) | 1,404 (51.1%) | -0.200 |
| obesity | 725 (18.1%) | 591 (21.5%) | -0.086 |
| frailty_any | 1,269 (31.6%) | 1,257 (45.7%) | -0.293 |
| frailty_ge2 | 519 (12.9%) | 648 (23.6%) | -0.278 |
| prior_hf_hosp_365 | 164 (4.1%) | 242 (8.8%) | -0.193 |
| prior_hf_hosp_365_v14 | 1,028 (25.6%) | 936 (34.1%) | -0.185 |
| frailty_count | 0.56 (sd 1.06) | 1.00 (sd 1.54) | -0.332 |
| inpatient_days_365 | 2.79 (sd 6.72) | 5.57 (sd 10.24) | -0.321 |
| hospital_admissions_v11 | 0.69 (sd 0.89) | 1.04 (sd 1.10) | -0.352 |

### aristotle (treated n = 15,419; comparator n = 3,352)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 13,201 (85.6%) | 2,781 (83.0%) | +0.073 |
| race_black | 1,246 (8.1%) | 349 (10.4%) | -0.081 |
| race_asian | 152 (1.0%) | 43 (1.3%) | -0.028 |
| race_other_unknown | 820 (5.3%) | 179 (5.3%) | -0.001 |
| race_unknown | 765 (5.0%) | 170 (5.1%) | -0.005 |
| race_multiple | 32 (0.2%) | <11 | -0.007 |
| hispanic | 739 (4.8%) | 176 (5.3%) | -0.021 |
| ethnicity_unknown | 255 (1.7%) | 32 (1.0%) | +0.062 |
| hyperlipidemia | 9,348 (60.6%) | 1,851 (55.2%) | +0.110 |
| statin_order_90d | 3,741 (24.3%) | 950 (28.3%) | -0.093 |
| statin_order_365d | 5,779 (37.5%) | 1,352 (40.3%) | -0.059 |
| hld_or_statin | 10,181 (66.0%) | 2,050 (61.2%) | +0.101 |
| t2d | 4,126 (26.8%) | 955 (28.5%) | -0.039 |
| diabetes_v11 | 4,173 (27.1%) | 964 (28.8%) | -0.038 |
| cad_ihd | 5,789 (37.5%) | 1,513 (45.1%) | -0.155 |
| hypertension_v11 | 11,229 (72.8%) | 2,326 (69.4%) | +0.076 |
| tobacco_current | 1,374 (8.9%) | 315 (9.4%) | -0.017 |
| tobacco_ever | 6,208 (40.3%) | 1,295 (38.6%) | +0.033 |
| obesity | 3,396 (22.0%) | 655 (19.5%) | +0.061 |
| frailty_any | 7,466 (48.4%) | 1,545 (46.1%) | +0.047 |
| frailty_ge2 | 4,211 (27.3%) | 858 (25.6%) | +0.039 |
| prior_hf_hosp_365 | 1,650 (10.7%) | 445 (13.3%) | -0.079 |
| prior_hf_hosp_365_v14 | 4,597 (29.8%) | 1,265 (37.7%) | -0.168 |
| frailty_count | 1.13 (sd 1.64) | 1.03 (sd 1.52) | +0.062 |
| inpatient_days_365 | 5.67 (sd 12.71) | 8.22 (sd 14.46) | -0.187 |
| hospital_admissions_v11 | 0.83 (sd 1.16) | 1.03 (sd 1.26) | -0.171 |

### rocket-af (treated n = 3,633; comparator n = 3,422)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 3,099 (85.3%) | 2,843 (83.1%) | +0.061 |
| race_black | 304 (8.4%) | 358 (10.5%) | -0.072 |
| race_asian | 27 (0.7%) | 42 (1.2%) | -0.049 |
| race_other_unknown | 203 (5.6%) | 179 (5.2%) | +0.016 |
| race_unknown | 192 (5.3%) | 169 (4.9%) | +0.016 |
| race_multiple | <11 | <11 | +0.002 |
| hispanic | 196 (5.4%) | 178 (5.2%) | +0.009 |
| ethnicity_unknown | 65 (1.8%) | 32 (0.9%) | +0.074 |
| hyperlipidemia | 1,912 (52.6%) | 1,870 (54.6%) | -0.040 |
| statin_order_90d | 640 (17.6%) | 962 (28.1%) | -0.252 |
| statin_order_365d | 1,144 (31.5%) | 1,367 (39.9%) | -0.177 |
| hld_or_statin | 2,123 (58.4%) | 2,071 (60.5%) | -0.042 |
| t2d | 823 (22.7%) | 966 (28.2%) | -0.128 |
| diabetes_v11 | 833 (22.9%) | 974 (28.5%) | -0.127 |
| cad_ihd | 1,108 (30.5%) | 1,527 (44.6%) | -0.295 |
| hypertension_v11 | 2,410 (66.3%) | 2,349 (68.6%) | -0.049 |
| tobacco_current | 338 (9.3%) | 314 (9.2%) | +0.004 |
| tobacco_ever | 1,231 (33.9%) | 1,312 (38.3%) | -0.093 |
| obesity | 677 (18.6%) | 659 (19.3%) | -0.016 |
| frailty_any | 1,432 (39.4%) | 1,557 (45.5%) | -0.123 |
| frailty_ge2 | 729 (20.1%) | 865 (25.3%) | -0.125 |
| prior_hf_hosp_365 | 250 (6.9%) | 459 (13.4%) | -0.218 |
| prior_hf_hosp_365_v14 | 708 (19.5%) | 1,289 (37.7%) | -0.411 |
| frailty_count | 0.84 (sd 1.42) | 1.01 (sd 1.51) | -0.120 |
| inpatient_days_365 | 3.84 (sd 12.24) | 8.22 (sd 15.31) | -0.316 |
| hospital_admissions_v11 | 0.61 (sd 1.15) | 1.02 (sd 1.26) | -0.348 |

### rely (treated n = 702; comparator n = 3,470)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 628 (89.5%) | 2,882 (83.1%) | +0.187 |
| race_black | 32 (4.6%) | 363 (10.5%) | -0.225 |
| race_asian | <11 | 43 (1.2%) | +0.004 |
| race_other_unknown | 33 (4.7%) | 182 (5.2%) | -0.025 |
| race_unknown | 32 (4.6%) | 172 (5.0%) | -0.019 |
| race_multiple | <11 | <11 | +0.005 |
| hispanic | 31 (4.4%) | 179 (5.2%) | -0.035 |
| ethnicity_unknown | 13 (1.9%) | 33 (1.0%) | +0.077 |
| hyperlipidemia | 335 (47.7%) | 1,902 (54.8%) | -0.142 |
| statin_order_90d | 128 (18.2%) | 971 (28.0%) | -0.233 |
| statin_order_365d | 222 (31.6%) | 1,383 (39.9%) | -0.172 |
| hld_or_statin | 381 (54.3%) | 2,104 (60.6%) | -0.129 |
| t2d | 139 (19.8%) | 989 (28.5%) | -0.204 |
| diabetes_v11 | 140 (19.9%) | 998 (28.8%) | -0.206 |
| cad_ihd | 186 (26.5%) | 1,551 (44.7%) | -0.387 |
| hypertension_v11 | 439 (62.5%) | 2,392 (68.9%) | -0.135 |
| tobacco_current | 46 (6.6%) | 323 (9.3%) | -0.102 |
| tobacco_ever | 227 (32.3%) | 1,333 (38.4%) | -0.127 |
| obesity | 90 (12.8%) | 675 (19.5%) | -0.181 |
| frailty_any | 254 (36.2%) | 1,589 (45.8%) | -0.196 |
| frailty_ge2 | 123 (17.5%) | 884 (25.5%) | -0.194 |
| prior_hf_hosp_365 | 39 (5.6%) | 465 (13.4%) | -0.270 |
| prior_hf_hosp_365_v14 | 124 (17.7%) | 1,302 (37.5%) | -0.455 |
| frailty_count | 0.71 (sd 1.26) | 1.02 (sd 1.52) | -0.221 |
| inpatient_days_365 | 3.26 (sd 8.29) | 8.29 (sd 15.57) | -0.403 |
| hospital_admissions_v11 | 0.58 (sd 0.96) | 1.02 (sd 1.26) | -0.399 |

### allhat (treated n = 18,098; comparator n = 8,494)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 13,984 (77.3%) | 6,474 (76.2%) | +0.025 |
| race_black | 2,419 (13.4%) | 1,242 (14.6%) | -0.036 |
| race_asian | 313 (1.7%) | 111 (1.3%) | +0.035 |
| race_other_unknown | 1,382 (7.6%) | 667 (7.9%) | -0.008 |
| race_unknown | 1,310 (7.2%) | 632 (7.4%) | -0.008 |
| race_multiple | 54 (0.3%) | 15 (0.2%) | +0.025 |
| hispanic | 1,454 (8.0%) | 682 (8.0%) | +0.000 |
| ethnicity_unknown | 378 (2.1%) | 177 (2.1%) | +0.000 |
| hyperlipidemia | 9,350 (51.7%) | 4,184 (49.3%) | +0.048 |
| statin_order_90d | 3,219 (17.8%) | 1,334 (15.7%) | +0.056 |
| statin_order_365d | 5,758 (31.8%) | 2,727 (32.1%) | -0.006 |
| hld_or_statin | 10,454 (57.8%) | 4,802 (56.5%) | +0.025 |
| t2d | 4,071 (22.5%) | 1,714 (20.2%) | +0.057 |
| diabetes_v11 | 4,143 (22.9%) | 1,738 (20.5%) | +0.059 |
| cad_ihd | 4,221 (23.3%) | 1,619 (19.1%) | +0.104 |
| hypertension_v11 | 13,546 (74.8%) | 6,032 (71.0%) | +0.086 |
| tobacco_current | 1,924 (10.6%) | 735 (8.7%) | +0.067 |
| tobacco_ever | 6,041 (33.4%) | 2,315 (27.3%) | +0.134 |
| obesity | 2,210 (12.2%) | 1,191 (14.0%) | -0.054 |
| frailty_any | 7,883 (43.6%) | 2,859 (33.7%) | +0.204 |
| frailty_ge2 | 4,299 (23.8%) | 1,248 (14.7%) | +0.231 |
| prior_hf_hosp_365 | 0 (0.0%) | 0 (0.0%) | +0.000 |
| prior_hf_hosp_365_v14 | 324 (1.8%) | 119 (1.4%) | +0.031 |
| frailty_count | 0.97 (sd 1.53) | 0.61 (sd 1.10) | +0.277 |
| inpatient_days_365 | 3.24 (sd 8.28) | 1.75 (sd 6.38) | +0.202 |
| hospital_admissions_v11 | 0.55 (sd 0.94) | 0.32 (sd 0.68) | +0.271 |

### emperor-preserved-v2 (treated n = 1,477; comparator n = 940)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 1,020 (69.1%) | 626 (66.6%) | +0.053 |
| race_black | 310 (21.0%) | 199 (21.2%) | -0.004 |
| race_asian | 19 (1.3%) | 17 (1.8%) | -0.042 |
| race_other_unknown | 128 (8.7%) | 98 (10.4%) | -0.060 |
| race_unknown | 114 (7.7%) | 91 (9.7%) | -0.070 |
| race_multiple | <11 | <11 | +0.026 |
| hispanic | 159 (10.8%) | 104 (11.1%) | -0.010 |
| ethnicity_unknown | 17 (1.2%) | <11 | +0.019 |
| hyperlipidemia | 1,196 (81.0%) | 699 (74.4%) | +0.159 |
| statin_order_90d | 441 (29.9%) | 302 (32.1%) | -0.049 |
| statin_order_365d | 738 (50.0%) | 528 (56.2%) | -0.125 |
| hld_or_statin | 1,257 (85.1%) | 767 (81.6%) | +0.094 |
| t2d | 1,215 (82.3%) | 846 (90.0%) | -0.225 |
| diabetes_v11 | 1,217 (82.4%) | 847 (90.1%) | -0.225 |
| cad_ihd | 902 (61.1%) | 511 (54.4%) | +0.136 |
| hypertension_v11 | 1,361 (92.1%) | 842 (89.6%) | +0.089 |
| tobacco_current | 239 (16.2%) | 116 (12.3%) | +0.110 |
| tobacco_ever | 805 (54.5%) | 464 (49.4%) | +0.103 |
| obesity | 791 (53.6%) | 355 (37.8%) | +0.321 |
| frailty_any | 890 (60.3%) | 619 (65.9%) | -0.116 |
| frailty_ge2 | 514 (34.8%) | 408 (43.4%) | -0.177 |
| prior_hf_hosp_365 | 592 (40.1%) | 435 (46.3%) | -0.125 |
| prior_hf_hosp_365_v14 | 942 (63.8%) | 641 (68.2%) | -0.093 |
| frailty_count | 1.43 (sd 1.74) | 1.77 (sd 1.92) | -0.185 |
| inpatient_days_365 | 10.31 (sd 20.95) | 12.30 (sd 20.09) | -0.097 |
| hospital_admissions_v11 | 1.29 (sd 1.71) | 1.55 (sd 1.93) | -0.145 |

### east-afnet4 (treated n = 3,462; comparator n = 12,647)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 2,951 (85.2%) | 10,241 (81.0%) | +0.114 |
| race_black | 268 (7.7%) | 1,502 (11.9%) | -0.139 |
| race_asian | 39 (1.1%) | 138 (1.1%) | +0.003 |
| race_other_unknown | 204 (5.9%) | 766 (6.1%) | -0.007 |
| race_unknown | 193 (5.6%) | 726 (5.7%) | -0.007 |
| race_multiple | <11 | 32 (0.3%) | -0.017 |
| hispanic | 178 (5.1%) | 808 (6.4%) | -0.054 |
| ethnicity_unknown | 42 (1.2%) | 166 (1.3%) | -0.009 |
| hyperlipidemia | 2,465 (71.2%) | 8,693 (68.7%) | +0.054 |
| statin_order_90d | 1,458 (42.1%) | 4,069 (32.2%) | +0.207 |
| statin_order_365d | 1,961 (56.6%) | 6,885 (54.4%) | +0.044 |
| hld_or_statin | 2,692 (77.8%) | 9,595 (75.9%) | +0.045 |
| t2d | 1,193 (34.5%) | 4,284 (33.9%) | +0.012 |
| diabetes_v11 | 1,204 (34.8%) | 4,323 (34.2%) | +0.013 |
| cad_ihd | 1,956 (56.5%) | 5,996 (47.4%) | +0.183 |
| hypertension_v11 | 3,017 (87.1%) | 10,716 (84.7%) | +0.069 |
| tobacco_current | 484 (14.0%) | 1,588 (12.6%) | +0.042 |
| tobacco_ever | 1,861 (53.8%) | 6,073 (48.0%) | +0.115 |
| obesity | 1,008 (29.1%) | 3,178 (25.1%) | +0.090 |
| frailty_any | 1,891 (54.6%) | 7,561 (59.8%) | -0.104 |
| frailty_ge2 | 1,078 (31.1%) | 4,675 (37.0%) | -0.123 |
| prior_hf_hosp_365 | 596 (17.2%) | 2,627 (20.8%) | -0.091 |
| prior_hf_hosp_365_v14 | 1,575 (45.5%) | 4,579 (36.2%) | +0.190 |
| frailty_count | 1.26 (sd 1.65) | 1.50 (sd 1.83) | -0.139 |
| inpatient_days_365 | 9.25 (sd 15.43) | 9.11 (sd 17.90) | +0.008 |
| hospital_admissions_v11 | 1.38 (sd 1.35) | 1.23 (sd 1.50) | +0.100 |

### cabana-v2 (treated n = 1,573; comparator n = 11,560)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 1,426 (90.7%) | 9,912 (85.7%) | +0.153 |
| race_black | 61 (3.9%) | 928 (8.0%) | -0.176 |
| race_asian | 19 (1.2%) | 111 (1.0%) | +0.024 |
| race_other_unknown | 67 (4.3%) | 609 (5.3%) | -0.047 |
| race_unknown | 65 (4.1%) | 565 (4.9%) | -0.036 |
| race_multiple | <11 | 23 (0.2%) | -0.002 |
| hispanic | 59 (3.8%) | 589 (5.1%) | -0.065 |
| ethnicity_unknown | 39 (2.5%) | 137 (1.2%) | +0.097 |
| hyperlipidemia | 863 (54.9%) | 7,531 (65.1%) | -0.211 |
| statin_order_90d | 166 (10.6%) | 3,646 (31.5%) | -0.533 |
| statin_order_365d | 423 (26.9%) | 5,142 (44.5%) | -0.373 |
| hld_or_statin | 950 (60.4%) | 8,088 (70.0%) | -0.202 |
| t2d | 239 (15.2%) | 3,575 (30.9%) | -0.380 |
| diabetes_v11 | 242 (15.4%) | 3,615 (31.3%) | -0.382 |
| cad_ihd | 444 (28.2%) | 5,711 (49.4%) | -0.445 |
| hypertension_v11 | 987 (62.7%) | 9,079 (78.5%) | -0.352 |
| tobacco_current | 91 (5.8%) | 1,345 (11.6%) | -0.209 |
| tobacco_ever | 483 (30.7%) | 5,559 (48.1%) | -0.361 |
| obesity | 359 (22.8%) | 3,117 (27.0%) | -0.096 |
| frailty_any | 428 (27.2%) | 6,056 (52.4%) | -0.532 |
| frailty_ge2 | 125 (7.9%) | 3,505 (30.3%) | -0.593 |
| prior_hf_hosp_365 | 185 (11.8%) | 2,019 (17.5%) | -0.162 |
| prior_hf_hosp_365_v14 | 254 (16.1%) | 5,109 (44.2%) | -0.642 |
| frailty_count | 0.40 (sd 0.82) | 1.24 (sd 1.69) | -0.628 |
| inpatient_days_365 | 2.03 (sd 5.53) | 8.83 (sd 16.46) | -0.554 |
| hospital_admissions_v11 | 0.41 (sd 0.88) | 1.21 (sd 1.42) | -0.686 |

### ontarget (treated n = 7,102; comparator n = 7,751)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 5,374 (75.7%) | 5,834 (75.3%) | +0.009 |
| race_black | 965 (13.6%) | 1,028 (13.3%) | +0.010 |
| race_asian | 143 (2.0%) | 126 (1.6%) | +0.029 |
| race_other_unknown | 620 (8.7%) | 763 (9.8%) | -0.038 |
| race_unknown | 585 (8.2%) | 737 (9.5%) | -0.045 |
| race_multiple | 26 (0.4%) | 17 (0.2%) | +0.027 |
| hispanic | 659 (9.3%) | 854 (11.0%) | -0.058 |
| ethnicity_unknown | 159 (2.2%) | 147 (1.9%) | +0.024 |
| hyperlipidemia | 3,868 (54.5%) | 3,923 (50.6%) | +0.077 |
| statin_order_90d | 1,162 (16.4%) | 1,599 (20.6%) | -0.110 |
| statin_order_365d | 2,245 (31.6%) | 2,582 (33.3%) | -0.036 |
| hld_or_statin | 4,338 (61.1%) | 4,490 (57.9%) | +0.064 |
| t2d | 2,162 (30.4%) | 2,498 (32.2%) | -0.039 |
| diabetes_v11 | 2,183 (30.7%) | 2,536 (32.7%) | -0.043 |
| cad_ihd | 2,314 (32.6%) | 2,607 (33.6%) | -0.022 |
| hypertension_v11 | 4,665 (65.7%) | 4,789 (61.8%) | +0.081 |
| tobacco_current | 648 (9.1%) | 891 (11.5%) | -0.078 |
| tobacco_ever | 1,993 (28.1%) | 2,490 (32.1%) | -0.089 |
| obesity | 903 (12.7%) | 939 (12.1%) | +0.018 |
| frailty_any | 2,420 (34.1%) | 2,971 (38.3%) | -0.089 |
| frailty_ge2 | 1,107 (15.6%) | 1,525 (19.7%) | -0.107 |
| prior_hf_hosp_365 | 0 (0.0%) | 0 (0.0%) | +0.000 |
| prior_hf_hosp_365_v14 | 219 (3.1%) | 280 (3.6%) | -0.029 |
| frailty_count | 0.65 (sd 1.20) | 0.81 (sd 1.38) | -0.122 |
| inpatient_days_365 | 1.86 (sd 7.23) | 2.79 (sd 7.81) | -0.124 |
| hospital_admissions_v11 | 0.33 (sd 0.71) | 0.51 (sd 0.83) | -0.229 |

### value (treated n = 10,208; comparator n = 16,449)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 8,006 (78.4%) | 11,914 (72.4%) | +0.140 |
| race_black | 1,157 (11.3%) | 2,849 (17.3%) | -0.171 |
| race_asian | 189 (1.9%) | 249 (1.5%) | +0.026 |
| race_other_unknown | 856 (8.4%) | 1,437 (8.7%) | -0.013 |
| race_unknown | 802 (7.9%) | 1,357 (8.2%) | -0.014 |
| race_multiple | 35 (0.3%) | 59 (0.4%) | -0.003 |
| hispanic | 889 (8.7%) | 1,591 (9.7%) | -0.033 |
| ethnicity_unknown | 259 (2.5%) | 317 (1.9%) | +0.041 |
| hyperlipidemia | 4,678 (45.8%) | 7,696 (46.8%) | -0.019 |
| statin_order_90d | 1,115 (10.9%) | 2,378 (14.5%) | -0.106 |
| statin_order_365d | 2,588 (25.4%) | 4,498 (27.3%) | -0.045 |
| hld_or_statin | 5,272 (51.6%) | 8,600 (52.3%) | -0.013 |
| t2d | 1,878 (18.4%) | 3,488 (21.2%) | -0.070 |
| diabetes_v11 | 1,912 (18.7%) | 3,548 (21.6%) | -0.071 |
| cad_ihd | 1,746 (17.1%) | 3,149 (19.1%) | -0.053 |
| hypertension_v11 | 6,617 (64.8%) | 12,170 (74.0%) | -0.200 |
| tobacco_current | 739 (7.2%) | 2,081 (12.7%) | -0.182 |
| tobacco_ever | 2,380 (23.3%) | 5,601 (34.1%) | -0.239 |
| obesity | 1,175 (11.5%) | 2,080 (12.6%) | -0.035 |
| frailty_any | 2,861 (28.0%) | 6,984 (42.5%) | -0.306 |
| frailty_ge2 | 1,125 (11.0%) | 3,666 (22.3%) | -0.306 |
| prior_hf_hosp_365 | 0 (0.0%) | 0 (0.0%) | +0.000 |
| prior_hf_hosp_365_v14 | 159 (1.6%) | 235 (1.4%) | +0.011 |
| frailty_count | 0.48 (sd 1.00) | 0.91 (sd 1.45) | -0.344 |
| inpatient_days_365 | 1.14 (sd 4.66) | 3.20 (sd 8.37) | -0.304 |
| hospital_admissions_v11 | 0.22 (sd 0.59) | 0.53 (sd 0.97) | -0.382 |

### ascot (treated n = 13,238; comparator n = 12,783)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 8,330 (62.9%) | 9,884 (77.3%) | -0.318 |
| race_black | 3,185 (24.1%) | 1,588 (12.4%) | +0.305 |
| race_asian | 271 (2.0%) | 197 (1.5%) | +0.038 |
| race_other_unknown | 1,452 (11.0%) | 1,114 (8.7%) | +0.076 |
| race_unknown | 1,377 (10.4%) | 1,050 (8.2%) | +0.075 |
| race_multiple | 70 (0.5%) | 25 (0.2%) | +0.055 |
| hispanic | 1,743 (13.2%) | 1,184 (9.3%) | +0.124 |
| ethnicity_unknown | 244 (1.8%) | 246 (1.9%) | -0.006 |
| hyperlipidemia | 5,178 (39.1%) | 5,516 (43.2%) | -0.082 |
| statin_order_90d | 1,442 (10.9%) | 1,619 (12.7%) | -0.055 |
| statin_order_365d | 2,823 (21.3%) | 2,964 (23.2%) | -0.045 |
| hld_or_statin | 5,783 (43.7%) | 6,106 (47.8%) | -0.082 |
| t2d | 2,734 (20.7%) | 2,571 (20.1%) | +0.013 |
| diabetes_v11 | 2,794 (21.1%) | 2,632 (20.6%) | +0.013 |
| cad_ihd | 996 (7.5%) | 1,691 (13.2%) | -0.188 |
| hypertension_v11 | 9,550 (72.1%) | 8,368 (65.5%) | +0.145 |
| tobacco_current | 2,121 (16.0%) | 1,466 (11.5%) | +0.133 |
| tobacco_ever | 4,390 (33.2%) | 3,738 (29.2%) | +0.085 |
| obesity | 2,174 (16.4%) | 2,114 (16.5%) | -0.003 |
| frailty_any | 4,737 (35.8%) | 4,155 (32.5%) | +0.069 |
| frailty_ge2 | 2,051 (15.5%) | 1,753 (13.7%) | +0.050 |
| prior_hf_hosp_365 | 0 (0.0%) | 0 (0.0%) | +0.000 |
| prior_hf_hosp_365_v14 | 115 (0.9%) | 482 (3.8%) | -0.194 |
| frailty_count | 0.65 (sd 1.14) | 0.58 (sd 1.09) | +0.064 |
| inpatient_days_365 | 2.78 (sd 8.28) | 2.55 (sd 8.32) | +0.028 |
| hospital_admissions_v11 | 0.47 (sd 1.00) | 0.43 (sd 0.90) | +0.040 |

### empa-reg (treated n = 3,159; comparator n = 2,490)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 2,194 (69.5%) | 1,627 (65.3%) | +0.088 |
| race_black | 549 (17.4%) | 498 (20.0%) | -0.067 |
| race_asian | 74 (2.3%) | 49 (2.0%) | +0.026 |
| race_other_unknown | 342 (10.8%) | 316 (12.7%) | -0.058 |
| race_unknown | 317 (10.0%) | 297 (11.9%) | -0.061 |
| race_multiple | 19 (0.6%) | <11 | +0.056 |
| hispanic | 419 (13.3%) | 391 (15.7%) | -0.069 |
| ethnicity_unknown | 46 (1.5%) | 23 (0.9%) | +0.049 |
| hyperlipidemia | 2,465 (78.0%) | 1,786 (71.7%) | +0.146 |
| statin_order_90d | 831 (26.3%) | 668 (26.8%) | -0.012 |
| statin_order_365d | 1,600 (50.6%) | 1,356 (54.5%) | -0.076 |
| hld_or_statin | 2,674 (84.6%) | 1,987 (79.8%) | +0.127 |
| t2d | 2,514 (79.6%) | 2,056 (82.6%) | -0.076 |
| diabetes_v11 | 2,520 (79.8%) | 2,065 (82.9%) | -0.081 |
| cad_ihd | 2,094 (66.3%) | 1,449 (58.2%) | +0.168 |
| hypertension_v11 | 2,681 (84.9%) | 2,053 (82.4%) | +0.065 |
| tobacco_current | 475 (15.0%) | 353 (14.2%) | +0.024 |
| tobacco_ever | 1,492 (47.2%) | 1,112 (44.7%) | +0.052 |
| obesity | 1,180 (37.4%) | 670 (26.9%) | +0.225 |
| frailty_any | 1,480 (46.9%) | 1,311 (52.7%) | -0.116 |
| frailty_ge2 | 731 (23.1%) | 741 (29.8%) | -0.150 |
| prior_hf_hosp_365 | 691 (21.9%) | 434 (17.4%) | +0.112 |
| prior_hf_hosp_365_v14 | 1,111 (35.2%) | 599 (24.1%) | +0.245 |
| frailty_count | 0.95 (sd 1.42) | 1.25 (sd 1.71) | -0.186 |
| inpatient_days_365 | 5.81 (sd 12.82) | 6.73 (sd 14.09) | -0.068 |
| hospital_admissions_v11 | 0.83 (sd 1.35) | 0.95 (sd 1.59) | -0.080 |

### carolina (treated n = 962; comparator n = 832)

| Variable | Treated | Comparator | SMD |
|---|---|---|---|
| race_white | 580 (60.3%) | 603 (72.5%) | -0.260 |
| race_black | 232 (24.1%) | 117 (14.1%) | +0.258 |
| race_asian | 21 (2.2%) | 26 (3.1%) | -0.059 |
| race_other_unknown | 129 (13.4%) | 86 (10.3%) | +0.095 |
| race_unknown | 126 (13.1%) | 83 (10.0%) | +0.098 |
| race_multiple | <11 | <11 | -0.029 |
| hispanic | 164 (17.0%) | 111 (13.3%) | +0.103 |
| ethnicity_unknown | 13 (1.4%) | 14 (1.7%) | -0.027 |
| hyperlipidemia | 596 (62.0%) | 435 (52.3%) | +0.196 |
| statin_order_90d | 116 (12.1%) | 104 (12.5%) | -0.013 |
| statin_order_365d | 306 (31.8%) | 240 (28.8%) | +0.064 |
| hld_or_statin | 649 (67.5%) | 496 (59.6%) | +0.164 |
| t2d | 726 (75.5%) | 558 (67.1%) | +0.186 |
| diabetes_v11 | 730 (75.9%) | 564 (67.8%) | +0.181 |
| cad_ihd | 315 (32.7%) | 221 (26.6%) | +0.136 |
| hypertension_v11 | 694 (72.1%) | 527 (63.3%) | +0.189 |
| tobacco_current | 108 (11.2%) | 83 (10.0%) | +0.041 |
| tobacco_ever | 343 (35.7%) | 220 (26.4%) | +0.200 |
| obesity | 186 (19.3%) | 153 (18.4%) | +0.024 |
| frailty_any | 425 (44.2%) | 255 (30.6%) | +0.282 |
| frailty_ge2 | 216 (22.5%) | 97 (11.7%) | +0.290 |
| prior_hf_hosp_365 | 85 (8.8%) | 36 (4.3%) | +0.182 |
| prior_hf_hosp_365_v14 | 149 (15.5%) | 70 (8.4%) | +0.219 |
| frailty_count | 0.91 (sd 1.41) | 0.51 (sd 0.99) | +0.326 |
| inpatient_days_365 | 4.23 (sd 11.70) | 1.63 (sd 6.28) | +0.277 |
| hospital_admissions_v11 | 0.56 (sd 0.99) | 0.28 (sd 0.74) | +0.314 |
