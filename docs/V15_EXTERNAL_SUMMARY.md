# v1.5 external first pass: MIMIC-IV and UK Biobank (exploratory)

Protocol: `docs/PROTOCOL_V1_5_EXTERNAL.md` (tag `protocol-v1.5`, with a deviation log).
Interface: `docs/V15_INTERFACE.md`. Code: `scripts/v15/`. All results below are aggregate.

## What was built

**MIMIC-IV.** Five in-hospital-initiation, new-user, active-comparator emulations. All five passed
the feasibility rule.

| Trial | Arm 1 | Arm 2 |
|---|---|---|
| PLATO | ticagrelor | clopidogrel |
| ARISTOTLE | apixaban | warfarin |
| ROCKET AF | rivaroxaban | warfarin |
| TRANSFORM-HF | torsemide | furosemide |
| COMET | metoprolol | carvedilol |

- **ECGs:** 18,034 MIMIC-IV-ECG waveforms were converted to the Yale layout (aVL/aVF reordered,
  mV scale verified) and embedded with the same BCL checkpoint. The embedding statistics match
  Yale's.
- **Horizon:** 12 months.
- **Imprecise trials:** ARISTOTLE and ROCKET AF have few events.

**UK Biobank.** Three prevalent-user, active-comparator comparisons anchored at the imaging visit,
where the ECG was recorded:

| Comparison | Benchmark |
|---|---|
| ARB vs ACEi | ONTARGET |
| amlodipine vs thiazide | ALLHAT |
| amlodipine vs beta-blocker | ASCOT-BPLA |

- **ECGs:** all 93,262 imaging ECGs embedded.
- **CLMBR arms** are analysed in the subset with embeddings (about 67–76% of each cohort).
- **Infeasible:** DOAC vs warfarin, because UKB coding 4 has no DOACs; and GP new-user designs,
  because no GP prescribing data are on disk.

**Engine validation.** On the Yale LIFE trial, the v1.5 engine reproduces the Yale estimates
exactly when given the same design and patients. The remaining differences come from
interface-level choices: single imputation, all-feature hdPS, and 5 excluded patients.

## Pooled with Yale (post-hoc summary; 26 emulations)

Paired per emulation, first arm minus second arm. Negative values mean the ECG arm is closer to
the RCT. Exact sign-flip tests across emulations.

| Contrast | Set | Closer to RCT | Sign test p | Mean Δ\|Δlog HR\| (sign-flip p) | Mean Δ precision-standardised z² (sign-flip p) |
|---|---|---|---|---|---|
| **Sparse + ECG vs sparse** | **All 26** | **20/26** | **0.009** | −0.031 (0.058) | **−1.11 (0.009)** |
| | Yale 18 | 14/18 | 0.031 | −0.020 (0.27) | −1.40 (0.024) |
| | External 8 | 6/8 | 0.29 | −0.056 (0.16) | −0.45 (0.22) |
| hdPS200 + ECG vs hdPS200 | All 26 | 15/26 | 0.56 | −0.011 (0.46) | −0.46 (0.17) |
| | External 8 | 5/8 | 0.73 | −0.032 (0.21) | −0.23 (0.29) |

**Caution.**
- Several RCTs serve as the benchmark in more than one cohort: ARISTOTLE, ROCKET AF, PLATO,
  TRANSFORM-HF and COMET in both Yale and MIMIC; ONTARGET, ALLHAT and ASCOT in both Yale and UKB.
  Their benchmark errors are therefore shared, and the 26 emulations are not fully independent.
- This pooled summary is post hoc.
- The external designs differ from Yale's: in-hospital first orders in MIMIC, prevalent users in
  UKB, and all-cause death standing in for CV death in UKB.

## Engine summary (all 8 external trials)

# v1.5 external first pass — cohort: all

Exploratory (protocol v1.5). Benchmarks are rct.json our_orientation; SE from the reported CI. Pair counts in brackets. Event counts < 11 suppressed upstream. Aggregates only.

## Trial directories

| trial | markers | analysed | plasmode | n_clmbr_subset | clinical_pairs | pairs_rule_150 | n_treated | n_control | events_treated | events_control | imprecise(<30 events/arm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | cohort,ecg,outcomes | True | True | <NA> | 1312 | pass | 1556 | 3576 | 18 | 81 | yes |
| mimic-comet | cohort,ecg,outcomes | True | True | <NA> | 738 | pass | 4101 | 743 | 981 | 130 |  |
| mimic-plato | cohort,ecg,outcomes | True | True | <NA> | 394 | pass | 441 | 2433 | 89 | 677 |  |
| mimic-rocket_af | cohort,ecg,outcomes | True | True | <NA> | 898 | pass | 905 | 5591 | 11 | 116 | yes |
| mimic-transform_hf | cohort,ecg,outcomes | True | True | <NA> | 903 | pass | 940 | 3466 | 251 | 764 |  |
| ukb-allhat | cohort,ecg,outcomes | True | True | 3543 | 1279 | pass | 3446 | 1374 | 85 | 45 |  |
| ukb-aristotle | infeasible | False | False | <NA> | <NA> |  | <NA> | <NA> | nan | nan |  |
| ukb-ascot | cohort,ecg,outcomes | True | True | 3912 | 1032 | pass | 3452 | 1910 | 88 | 99 |  |
| ukb-ontarget | cohort,ecg,outcomes | True | True | 5683 | 2563 | pass | 2567 | 4931 | 124 | 243 |  |

## Hazard ratios per trial (HR (95% CI) [pairs]) — full analysed cohort

| trial | rct | N | unmatched | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | 0.79 (0.66–0.95) | 5132 | 0.50 (0.30–0.83) | 0.52 (0.29–0.93) [1466] | 0.62 (0.33–1.17) [1439] | 0.39 (0.20–0.75) [1343] | 0.42 (0.21–0.83) [1289] | 0.49 (0.28–0.86) [1553] | 0.44 (0.24–0.82) [1312] |
| mimic-comet | 1.21 (1.07–1.35) | 4844 | 1.41 (1.17–1.69) | 1.32 (1.06–1.64) [743] | 1.06 (0.84–1.35) [742] | 1.12 (0.89–1.42) [716] | 1.05 (0.83–1.33) [718] | 1.37 (1.09–1.72) [741] | 1.24 (0.99–1.55) [738] |
| mimic-plato | 0.84 (0.77–0.92) | 2874 | 0.71 (0.57–0.89) | 0.93 (0.69–1.25) [411] | 0.90 (0.68–1.21) [411] | 0.99 (0.72–1.38) [354] | 0.87 (0.64–1.19) [352] | 0.89 (0.67–1.18) [441] | 0.96 (0.71–1.29) [394] |
| mimic-rocket_af | 0.88 (0.75–1.04) | 6496 | 0.56 (0.30–1.03) | 0.51 (0.25–1.07) [902] | 0.56 (0.27–1.19) [901] | 0.77 (0.36–1.66) [901] | 0.83 (0.37–1.87) [900] | 0.56 (0.26–1.17) [905] | 0.57 (0.27–1.20) [898] |
| mimic-transform_hf | 1.02 (0.89–1.17) | 4406 | 1.24 (1.07–1.43) | 1.20 (1.01–1.43) [940] | 1.06 (0.89–1.26) [940] | 0.99 (0.82–1.20) [808] | 1.08 (0.89–1.32) [806] | 1.08 (0.91–1.29) [940] | 1.25 (1.03–1.51) [903] |
| ukb-allhat | 0.98 (0.90–1.07) | 4820 | 0.89 (0.62–1.28) | 0.79 (0.51–1.23) [1374] | 0.88 (0.57–1.37) [1345] | 0.67 (0.42–1.08) [1280] | 0.72 (0.45–1.17) [1255] | 0.88 (0.56–1.38) [1372] | 0.76 (0.47–1.21) [1279] |
| ukb-ascot | 0.90 (0.79–1.02) | 5362 | 0.52 (0.39–0.69) | 0.77 (0.48–1.22) [978] | 0.68 (0.44–1.06) [1007] | 0.73 (0.44–1.21) [995] | 0.74 (0.46–1.19) [964] | 0.60 (0.43–0.84) [1837] | 0.71 (0.46–1.08) [1032] |
| ukb-ontarget | 1.01 (0.94–1.09) | 7498 | 1.01 (0.81–1.25) | 1.07 (0.83–1.37) [2567] | 1.00 (0.78–1.29) [2561] | 0.96 (0.74–1.23) [2486] | 0.95 (0.74–1.22) [2477] | 1.06 (0.82–1.36) [2567] | 0.97 (0.76–1.25) [2563] |

## Hazard ratios — CLMBR subset (patients with a CLMBR embedding; like-for-like CLMBR comparisons)

| trial | rct | unmatched [clmbr-subset] | sparse [clmbr-subset] | sparse+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | hdPS200+ECG [clmbr-subset] | CLMBR | sparse+CLMBR | sparse+CLMBR+ECG | hdPS200+CLMBR |
|---|---|---|---|---|---|---|---|---|---|---|
| ukb-allhat | 0.98 (0.90–1.07) | 0.86 (0.60–1.24) | 0.76 (0.49–1.18) [1109] | 0.82 (0.54–1.26) [1064] | 0.83 (0.53–1.30) [1003] | 0.72 (0.44–1.17) [964] | 0.68 (0.43–1.08) [1102] | 0.77 (0.49–1.20) [1091] | 0.88 (0.56–1.37) [1037] | 0.74 (0.46–1.20) [971] |
| ukb-ascot | 0.90 (0.79–1.02) | 0.51 (0.38–0.68) | 0.80 (0.51–1.28) [723] | 0.86 (0.54–1.35) [739] | 0.69 (0.41–1.14) [726] | 0.81 (0.49–1.34) [692] | 0.50 (0.33–0.75) [1037] | 0.64 (0.41–0.99) [749] | 0.83 (0.54–1.29) [739] | 0.68 (0.41–1.11) [705] |
| ukb-ontarget | 1.01 (0.94–1.09) | 1.05 (0.85–1.31) | 0.97 (0.76–1.24) [1903] | 0.94 (0.74–1.20) [1902] | 0.91 (0.71–1.18) [1803] | 1.01 (0.78–1.32) [1804] | 0.94 (0.73–1.20) [1901] | 1.04 (0.81–1.34) [1902] | 0.98 (0.76–1.26) [1898] | 1.06 (0.82–1.37) [1817] |

## Secondary benchmarks (not in the panel or contrasts)

| trial | benchmark | endpoint | rct_hr | rct_lo | rct_hi | arm | hr | lo | hi | pairs | d_log | z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | unmatched | 0.94 | 0.46 | 1.92 | – | -0.19 | -0.50 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | sparse | 1.11 | 0.47 | 2.61 | 2567.00 | -0.02 | -0.04 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | sparse+ECG | 1.01 | 0.44 | 2.34 | 2561.00 | -0.11 | -0.25 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | hdPS200 | 0.84 | 0.36 | 1.94 | 2486.00 | -0.30 | -0.68 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | hdPS200+ECG | 0.63 | 0.29 | 1.39 | 2477.00 | -0.58 | -1.41 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | ECGonly | 0.94 | 0.41 | 2.12 | 2567.00 | -0.19 | -0.44 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | clinical | 0.72 | 0.32 | 1.62 | 2563.00 | -0.45 | -1.06 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | unmatched [clmbr-subset] | 0.99 | 0.48 | 2.05 | – | -0.13 | -0.34 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | sparse [clmbr-subset] | 0.85 | 0.38 | 1.89 | 1903.00 | -0.29 | -0.69 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | sparse+ECG [clmbr-subset] | 0.73 | 0.34 | 1.60 | 1902.00 | -0.43 | -1.06 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | hdPS200 [clmbr-subset] | 0.77 | 0.34 | 1.76 | 1803.00 | -0.39 | -0.89 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | hdPS200+ECG [clmbr-subset] | 0.91 | 0.38 | 2.14 | 1804.00 | -0.22 | -0.49 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | CLMBR | 0.79 | 0.36 | 1.73 | 1901.00 | -0.36 | -0.88 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | sparse+CLMBR | 0.92 | 0.40 | 2.08 | 1902.00 | -0.21 | -0.49 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | sparse+CLMBR+ECG | 1.00 | 0.43 | 2.31 | 1898.00 | -0.12 | -0.28 |
| ukb-ontarget | elite_ii | all-cause mortality | 1.13 | 0.95 | 1.34 | hdPS200+CLMBR | 0.83 | 0.36 | 1.93 | 1817.00 | -0.31 | -0.70 |

## RCT-DUPLICATE panel per arm

Pearson r descriptive only (>= 3 trials); phi = Heyard dispersion Q/(k-1) (1 = disagreement explained by sampling error).

| arm | trials | significance_agreement | estimate_agreement | std_diff_agreement | pearson_r | kappa | ratio_of_ratios | ror_lo | ror_hi | I2 | dispersion_phi | mean_abs_dlog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| unmatched | 8 | 0.75 | 0.12 | 0.88 | 0.90 | 0.61 | 0.89 | 0.74 | 1.08 | 0.70 | 3.39 | 0.26 |
| sparse | 8 | 0.75 | 0.25 | 1.00 | 0.80 | 0.54 | 1.03 | 0.90 | 1.16 | 0.11 | 1.12 | 0.22 |
| sparse+ECG | 8 | 0.62 | 0.38 | 1.00 | 0.74 | 0.00 | 0.95 | 0.85 | 1.07 | 0.00 | 0.57 | 0.16 |
| hdPS200 | 8 | 0.75 | 0.50 | 0.88 | 0.68 | 0.41 | 0.93 | 0.82 | 1.05 | 0.03 | 1.03 | 0.22 |
| hdPS200+ECG | 8 | 0.75 | 0.50 | 1.00 | 0.72 | 0.41 | 0.93 | 0.82 | 1.05 | 0.00 | 0.77 | 0.19 |
| ECGonly | 8 | 0.75 | 0.38 | 0.88 | 0.85 | 0.53 | 0.96 | 0.83 | 1.11 | 0.33 | 1.50 | 0.22 |
| clinical | 8 | 0.62 | 0.25 | 1.00 | 0.78 | 0.23 | 0.98 | 0.84 | 1.13 | 0.31 | 1.44 | 0.24 |
| unmatched [clmbr-subset] | 3 | 0.67 | 0.33 | 0.67 | 1.00 | 0.00 | 0.81 | 0.55 | 1.18 | 0.79 | 4.70 | 0.25 |
| sparse [clmbr-subset] | 3 | 1.00 | 0.67 | 1.00 | 0.52 | – | 0.91 | 0.74 | 1.11 | 0.00 | 0.34 | 0.14 |
| sparse+ECG [clmbr-subset] | 3 | 1.00 | 0.67 | 1.00 | 0.45 | – | 0.92 | 0.75 | 1.12 | 0.00 | 0.10 | 0.10 |
| hdPS200 [clmbr-subset] | 3 | 1.00 | 0.00 | 1.00 | 1.00 | – | 0.87 | 0.70 | 1.07 | 0.00 | 0.16 | 0.18 |
| hdPS200+ECG [clmbr-subset] | 3 | 1.00 | 0.67 | 1.00 | 0.43 | – | 0.93 | 0.74 | 1.15 | 0.00 | 0.59 | 0.14 |
| CLMBR | 3 | 0.67 | 0.00 | 0.67 | 0.96 | 0.00 | 0.74 | 0.53 | 1.02 | 0.54 | 2.18 | 0.35 |
| sparse+CLMBR | 3 | 0.67 | 0.33 | 1.00 | 0.92 | 0.00 | 0.89 | 0.70 | 1.12 | 0.20 | 1.25 | 0.21 |
| sparse+CLMBR+ECG | 3 | 1.00 | 0.67 | 1.00 | 0.88 | – | 0.95 | 0.77 | 1.16 | 0.00 | 0.05 | 0.07 |
| hdPS200+CLMBR | 3 | 1.00 | 0.33 | 1.00 | 0.82 | – | 0.92 | 0.73 | 1.16 | 0.07 | 1.08 | 0.20 |

## Paired contrasts (negative = first arm closer to the RCT)

| contrast | first | second | trial | d_abs | d_z2 | abs_first | abs_second |
|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | mimic-aristotle | -0.190 | -1.324 | 0.235 | 0.426 |
| C1 | sparse+ECG | sparse | mimic-comet | 0.038 | 0.371 | 0.127 | 0.089 |
| C1 | sparse+ECG | sparse | mimic-plato | -0.026 | -0.164 | 0.073 | 0.099 |
| C1 | sparse+ECG | sparse | mimic-rocket_af | -0.099 | -0.712 | 0.443 | 0.542 |
| C1 | sparse+ECG | sparse | mimic-transform_hf | -0.124 | -1.888 | 0.040 | 0.164 |
| C1 | sparse+ECG | sparse | ukb-allhat | -0.111 | -0.677 | 0.107 | 0.218 |
| C1 | sparse+ECG | sparse | ukb-ascot | 0.113 | 0.959 | 0.274 | 0.161 |
| C1 | sparse+ECG | sparse | ukb-ontarget | -0.050 | -0.174 | 0.006 | 0.056 |
| C2 | hdPS200+ECG | hdPS200 | mimic-aristotle | -0.064 | -1.004 | 0.644 | 0.707 |
| C2 | hdPS200+ECG | hdPS200 | mimic-comet | 0.061 | 0.721 | 0.134 | 0.074 |
| C2 | hdPS200+ECG | hdPS200 | mimic-plato | -0.132 | -0.899 | 0.037 | 0.169 |
| C2 | hdPS200+ECG | hdPS200 | mimic-rocket_af | -0.074 | -0.087 | 0.055 | 0.128 |
| C2 | hdPS200+ECG | hdPS200 | mimic-transform_hf | 0.031 | 0.181 | 0.060 | 0.029 |
| C2 | hdPS200+ECG | hdPS200 | ukb-allhat | -0.070 | -0.813 | 0.303 | 0.373 |
| C2 | hdPS200+ECG | hdPS200 | ukb-ascot | -0.015 | -0.013 | 0.193 | 0.208 |
| C2 | hdPS200+ECG | hdPS200 | ukb-ontarget | 0.007 | 0.053 | 0.061 | 0.054 |
| ECGonly | ECGonly | unmatched | mimic-aristotle | 0.012 | -0.301 | 0.472 | 0.461 |
| ECGonly | ECGonly | unmatched | mimic-comet | -0.030 | -1.053 | 0.128 | 0.157 |
| ECGonly | ECGonly | unmatched | mimic-plato | -0.106 | -1.663 | 0.061 | 0.167 |
| ECGonly | ECGonly | unmatched | mimic-rocket_af | 0.003 | -0.570 | 0.458 | 0.455 |
| ECGonly | ECGonly | unmatched | mimic-transform_hf | -0.135 | -3.364 | 0.059 | 0.194 |
| ECGonly | ECGonly | unmatched | ukb-allhat | 0.011 | -0.048 | 0.106 | 0.095 |
| ECGonly | ECGonly | unmatched | ukb-ascot | -0.138 | -6.720 | 0.411 | 0.549 |
| ECGonly | ECGonly | unmatched | ukb-ontarget | 0.044 | 0.112 | 0.045 | 0.001 |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | ukb-allhat | -0.083 | -0.646 | 0.175 | 0.258 |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | ukb-ascot | -0.065 | -0.175 | 0.048 | 0.113 |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | ukb-ontarget | 0.028 | 0.189 | 0.071 | 0.043 |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | ukb-allhat | 0.146 | 1.001 | 0.308 | 0.162 |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | ukb-ascot | -0.163 | -0.856 | 0.108 | 0.272 |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | ukb-ontarget | -0.101 | -0.582 | 0.002 | 0.104 |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | ukb-allhat | 0.241 | 1.902 | 0.368 | 0.127 |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | ukb-ascot | 0.019 | -5.196 | 0.592 | 0.573 |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | ukb-ontarget | 0.036 | 0.215 | 0.077 | 0.040 |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | ukb-allhat | -0.015 | -0.150 | 0.244 | 0.258 |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | ukb-ascot | 0.230 | 2.000 | 0.343 | 0.113 |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | ukb-ontarget | -0.010 | -0.049 | 0.032 | 0.043 |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | ukb-allhat | -0.131 | -0.879 | 0.113 | 0.244 |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | ukb-ascot | -0.267 | -2.108 | 0.076 | 0.343 |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | ukb-ontarget | -0.002 | -0.005 | 0.031 | 0.032 |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | ukb-allhat | -0.062 | -0.383 | 0.113 | 0.175 |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | ukb-ascot | 0.028 | 0.067 | 0.076 | 0.048 |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | ukb-ontarget | -0.040 | -0.243 | 0.031 | 0.071 |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | ukb-allhat | 0.118 | 0.770 | 0.280 | 0.162 |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | ukb-ascot | 0.014 | 0.177 | 0.285 | 0.272 |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | ukb-ontarget | -0.054 | -0.450 | 0.050 | 0.104 |

Across trials (exact sign-flip; descriptive):

| contrast | first | second | trials | closer | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 |
|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 8 | 6/8 | -0.056 | 0.156 | -0.451 | 0.219 |
| C2 | hdPS200+ECG | hdPS200 | 8 | 5/8 | -0.032 | 0.211 | -0.233 | 0.289 |
| ECGonly | ECGonly | unmatched | 8 | 4/8 | -0.042 | 0.188 | -1.701 | 0.023 |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | 3 | 2/3 | -0.040 | 0.500 | -0.211 | 0.750 |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | 3 | 2/3 | -0.040 | 0.750 | -0.145 | 1.000 |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | 3 | 0/3 | 0.099 | 0.250 | -1.026 | 1.000 |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | 3 | 2/3 | 0.068 | 1.000 | 0.600 | 1.000 |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | 3 | 3/3 | -0.133 | 0.250 | -0.997 | 0.250 |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | 3 | 2/3 | -0.025 | 0.500 | -0.186 | 0.500 |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | 3 | 1/3 | 0.026 | 0.750 | 0.166 | 0.750 |

## Plasmode bias per arm (true conditional HR 0.8; truth = marginal HR in the arm's matched population)

| trial | scenario | arm | reps | truth | bias | bias_lo | bias_hi | emp_sd | rmse | coverage |
|---|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | base | unmatched | 200 | -0.222 | -0.042 | -0.078 | -0.007 | 0.254 | 0.257 | 0.965 |
| mimic-aristotle | base | sparse | 200 | -0.248 | -0.009 | -0.048 | 0.030 | 0.279 | 0.279 | 0.975 |
| mimic-aristotle | base | sparse+ECG | 200 | -0.207 | -0.044 | -0.082 | -0.004 | 0.281 | 0.284 | 0.970 |
| mimic-aristotle | base | hdPS200 | 200 | -0.217 | 0.067 | 0.024 | 0.110 | 0.308 | 0.314 | 0.950 |
| mimic-aristotle | base | hdPS200+ECG | 200 | -0.236 | 0.067 | 0.022 | 0.113 | 0.337 | 0.343 | 0.975 |
| mimic-aristotle | base | ECGonly | 200 | -0.223 | -0.023 | -0.064 | 0.018 | 0.294 | 0.294 | 0.945 |
| mimic-aristotle | base | clinical | 200 | -0.231 | 0.001 | -0.042 | 0.043 | 0.310 | 0.309 | 0.975 |
| mimic-aristotle | phys_only | unmatched | 200 | -0.215 | 0.065 | 0.033 | 0.096 | 0.228 | 0.237 | 0.960 |
| mimic-aristotle | phys_only | sparse | 200 | -0.211 | 0.043 | 0.005 | 0.082 | 0.280 | 0.283 | 0.980 |
| mimic-aristotle | phys_only | sparse+ECG | 200 | -0.218 | 0.035 | -0.004 | 0.074 | 0.290 | 0.291 | 0.970 |
| mimic-aristotle | phys_only | hdPS200 | 200 | -0.222 | 0.056 | 0.013 | 0.098 | 0.308 | 0.312 | 0.960 |
| mimic-aristotle | phys_only | hdPS200+ECG | 200 | -0.248 | 0.083 | 0.042 | 0.123 | 0.306 | 0.317 | 0.970 |
| mimic-aristotle | phys_only | ECGonly | 200 | -0.210 | 0.084 | 0.049 | 0.118 | 0.258 | 0.270 | 0.960 |
| mimic-aristotle | phys_only | clinical | 200 | -0.227 | 0.033 | -0.008 | 0.074 | 0.298 | 0.299 | 0.975 |
| mimic-comet | base | unmatched | 200 | -0.204 | 0.164 | 0.151 | 0.179 | 0.100 | 0.192 | 0.655 |
| mimic-comet | base | sparse | 200 | -0.204 | 0.058 | 0.041 | 0.076 | 0.133 | 0.144 | 0.950 |
| mimic-comet | base | sparse+ECG | 200 | -0.213 | 0.058 | 0.040 | 0.077 | 0.138 | 0.149 | 0.935 |
| mimic-comet | base | hdPS200 | 200 | -0.203 | 0.012 | -0.007 | 0.031 | 0.140 | 0.140 | 0.950 |
| mimic-comet | base | hdPS200+ECG | 200 | -0.212 | 0.019 | -0.001 | 0.039 | 0.145 | 0.146 | 0.930 |
| mimic-comet | base | ECGonly | 200 | -0.205 | 0.108 | 0.091 | 0.126 | 0.127 | 0.167 | 0.855 |
| mimic-comet | base | clinical | 200 | -0.211 | 0.021 | 0.004 | 0.039 | 0.129 | 0.131 | 0.955 |
| mimic-comet | phys_only | unmatched | 200 | -0.208 | 0.130 | 0.117 | 0.143 | 0.095 | 0.161 | 0.770 |
| mimic-comet | phys_only | sparse | 200 | -0.208 | 0.030 | 0.012 | 0.049 | 0.130 | 0.133 | 0.945 |
| mimic-comet | phys_only | sparse+ECG | 200 | -0.215 | 0.026 | 0.008 | 0.044 | 0.127 | 0.130 | 0.965 |
| mimic-comet | phys_only | hdPS200 | 200 | -0.216 | 0.025 | 0.007 | 0.042 | 0.126 | 0.128 | 0.985 |
| mimic-comet | phys_only | hdPS200+ECG | 200 | -0.214 | 0.015 | -0.002 | 0.033 | 0.129 | 0.130 | 0.945 |
| mimic-comet | phys_only | ECGonly | 200 | -0.212 | 0.097 | 0.079 | 0.115 | 0.128 | 0.161 | 0.905 |
| mimic-comet | phys_only | clinical | 200 | -0.207 | 0.001 | -0.018 | 0.018 | 0.133 | 0.133 | 0.935 |
| mimic-plato | base | unmatched | 200 | -0.195 | -0.234 | -0.250 | -0.216 | 0.125 | 0.265 | 0.545 |
| mimic-plato | base | sparse | 200 | -0.185 | 0.036 | 0.012 | 0.058 | 0.164 | 0.167 | 0.960 |
| mimic-plato | base | sparse+ECG | 200 | -0.200 | 0.032 | 0.010 | 0.055 | 0.163 | 0.165 | 0.945 |
| mimic-plato | base | hdPS200 | 200 | -0.190 | 0.063 | 0.039 | 0.087 | 0.176 | 0.187 | 0.950 |
| mimic-plato | base | hdPS200+ECG | 200 | -0.196 | 0.068 | 0.043 | 0.094 | 0.188 | 0.200 | 0.930 |
| mimic-plato | base | ECGonly | 200 | -0.197 | -0.117 | -0.138 | -0.096 | 0.152 | 0.192 | 0.875 |
| mimic-plato | base | clinical | 200 | -0.181 | -0.002 | -0.026 | 0.022 | 0.175 | 0.175 | 0.950 |
| mimic-plato | phys_only | unmatched | 200 | -0.205 | -0.327 | -0.344 | -0.310 | 0.126 | 0.351 | 0.310 |
| mimic-plato | phys_only | sparse | 200 | -0.187 | -0.004 | -0.025 | 0.018 | 0.162 | 0.161 | 0.960 |
| mimic-plato | phys_only | sparse+ECG | 200 | -0.214 | 0.003 | -0.018 | 0.024 | 0.147 | 0.147 | 0.980 |
| mimic-plato | phys_only | hdPS200 | 200 | -0.197 | 0.013 | -0.012 | 0.038 | 0.185 | 0.185 | 0.950 |
| mimic-plato | phys_only | hdPS200+ECG | 200 | -0.200 | 0.018 | -0.008 | 0.044 | 0.188 | 0.188 | 0.960 |
| mimic-plato | phys_only | ECGonly | 200 | -0.196 | -0.202 | -0.224 | -0.180 | 0.162 | 0.259 | 0.780 |
| mimic-plato | phys_only | clinical | 200 | -0.197 | 0.004 | -0.018 | 0.027 | 0.167 | 0.167 | 0.955 |
| mimic-rocket_af | base | unmatched | 200 | -0.217 | -0.149 | -0.197 | -0.106 | 0.314 | 0.347 | 0.975 |
| mimic-rocket_af | base | sparse | 200 | -0.241 | 0.005 | -0.054 | 0.062 | 0.401 | 0.400 | 0.965 |
| mimic-rocket_af | base | sparse+ECG | 200 | -0.225 | -0.026 | -0.082 | 0.030 | 0.389 | 0.389 | 0.970 |
| mimic-rocket_af | base | hdPS200 | 200 | -0.225 | 0.059 | -0.001 | 0.119 | 0.425 | 0.428 | 0.960 |
| mimic-rocket_af | base | hdPS200+ECG | 200 | -0.218 | -0.003 | -0.062 | 0.052 | 0.405 | 0.404 | 0.960 |
| mimic-rocket_af | base | ECGonly | 200 | -0.241 | -0.096 | -0.148 | -0.042 | 0.390 | 0.401 | 0.960 |
| mimic-rocket_af | base | clinical | 200 | -0.235 | 0.016 | -0.042 | 0.076 | 0.427 | 0.426 | 0.935 |
| mimic-rocket_af | phys_only | unmatched | 200 | -0.237 | -0.077 | -0.120 | -0.031 | 0.333 | 0.341 | 0.935 |
| mimic-rocket_af | phys_only | sparse | 200 | -0.216 | 0.033 | -0.027 | 0.096 | 0.456 | 0.456 | 0.940 |
| mimic-rocket_af | phys_only | sparse+ECG | 200 | -0.181 | -0.010 | -0.067 | 0.048 | 0.424 | 0.423 | 0.950 |
| mimic-rocket_af | phys_only | hdPS200 | 200 | -0.207 | -0.035 | -0.095 | 0.025 | 0.444 | 0.445 | 0.940 |
| mimic-rocket_af | phys_only | hdPS200+ECG | 200 | -0.187 | -0.059 | -0.119 | 0.003 | 0.447 | 0.450 | 0.930 |
| mimic-rocket_af | phys_only | ECGonly | 200 | -0.214 | -0.080 | -0.134 | -0.025 | 0.401 | 0.408 | 0.945 |
| mimic-rocket_af | phys_only | clinical | 200 | -0.208 | -0.053 | -0.110 | 0.005 | 0.427 | 0.429 | 0.950 |
| mimic-transform_hf | base | unmatched | 200 | -0.210 | 0.024 | 0.013 | 0.036 | 0.085 | 0.088 | 0.945 |
| mimic-transform_hf | base | sparse | 200 | -0.215 | 0.042 | 0.028 | 0.056 | 0.103 | 0.111 | 0.935 |
| mimic-transform_hf | base | sparse+ECG | 200 | -0.218 | 0.019 | 0.006 | 0.033 | 0.102 | 0.104 | 0.955 |
| mimic-transform_hf | base | hdPS200 | 200 | -0.204 | -0.021 | -0.036 | -0.005 | 0.110 | 0.112 | 0.970 |
| mimic-transform_hf | base | hdPS200+ECG | 200 | -0.202 | -0.027 | -0.043 | -0.011 | 0.114 | 0.116 | 0.940 |
| mimic-transform_hf | base | ECGonly | 200 | -0.209 | 0.031 | 0.018 | 0.045 | 0.097 | 0.102 | 0.950 |
| mimic-transform_hf | base | clinical | 200 | -0.202 | -0.012 | -0.025 | 0.003 | 0.107 | 0.108 | 0.960 |
| mimic-transform_hf | phys_only | unmatched | 200 | -0.212 | -0.023 | -0.034 | -0.011 | 0.083 | 0.086 | 0.970 |
| mimic-transform_hf | phys_only | sparse | 200 | -0.213 | -0.019 | -0.032 | -0.005 | 0.101 | 0.102 | 0.985 |
| mimic-transform_hf | phys_only | sparse+ECG | 200 | -0.214 | -0.022 | -0.036 | -0.008 | 0.101 | 0.103 | 0.970 |
| mimic-transform_hf | phys_only | hdPS200 | 200 | -0.209 | -0.038 | -0.052 | -0.023 | 0.106 | 0.112 | 0.970 |
| mimic-transform_hf | phys_only | hdPS200+ECG | 200 | -0.206 | -0.042 | -0.058 | -0.026 | 0.117 | 0.125 | 0.955 |
| mimic-transform_hf | phys_only | ECGonly | 200 | -0.214 | -0.016 | -0.031 | -0.002 | 0.104 | 0.105 | 0.955 |
| mimic-transform_hf | phys_only | clinical | 200 | -0.208 | -0.014 | -0.027 | 0.001 | 0.101 | 0.102 | 0.970 |
| ukb-allhat | base | unmatched | 200 | -0.228 | 0.089 | 0.057 | 0.121 | 0.221 | 0.238 | 0.925 |
| ukb-allhat | base | sparse | 200 | -0.211 | -0.022 | -0.060 | 0.016 | 0.263 | 0.264 | 0.960 |
| ukb-allhat | base | sparse+ECG | 200 | -0.216 | 0.008 | -0.028 | 0.043 | 0.255 | 0.255 | 0.960 |
| ukb-allhat | base | hdPS200 | 200 | -0.196 | -0.080 | -0.119 | -0.041 | 0.277 | 0.287 | 0.940 |
| ukb-allhat | base | hdPS200+ECG | 200 | -0.257 | -0.050 | -0.092 | -0.008 | 0.293 | 0.297 | 0.960 |
| ukb-allhat | base | ECGonly | 200 | -0.210 | 0.049 | 0.012 | 0.084 | 0.252 | 0.256 | 0.970 |
| ukb-allhat | base | clinical | 200 | -0.195 | 0.017 | -0.023 | 0.055 | 0.280 | 0.279 | 0.950 |
| ukb-allhat | base | unmatched [clmbr-subset] | 200 | -0.220 | 0.089 | 0.059 | 0.118 | 0.214 | 0.231 | 0.965 |
| ukb-allhat | base | sparse [clmbr-subset] | 200 | -0.220 | -0.009 | -0.045 | 0.026 | 0.266 | 0.265 | 0.965 |
| ukb-allhat | base | sparse+ECG [clmbr-subset] | 200 | -0.202 | -0.017 | -0.053 | 0.017 | 0.258 | 0.258 | 0.955 |
| ukb-allhat | base | hdPS200 [clmbr-subset] | 200 | -0.210 | -0.067 | -0.109 | -0.026 | 0.308 | 0.314 | 0.945 |
| ukb-allhat | base | hdPS200+ECG [clmbr-subset] | 200 | -0.226 | -0.069 | -0.114 | -0.025 | 0.308 | 0.315 | 0.940 |
| ukb-allhat | base | CLMBR | 200 | -0.222 | 0.018 | -0.018 | 0.051 | 0.246 | 0.246 | 0.970 |
| ukb-allhat | base | sparse+CLMBR | 200 | -0.229 | 0.031 | -0.007 | 0.068 | 0.264 | 0.265 | 0.955 |
| ukb-allhat | base | sparse+CLMBR+ECG | 200 | -0.222 | -0.001 | -0.038 | 0.035 | 0.267 | 0.266 | 0.975 |
| ukb-allhat | base | hdPS200+CLMBR | 200 | -0.227 | -0.033 | -0.077 | 0.008 | 0.305 | 0.306 | 0.935 |
| ukb-allhat | phys_only | unmatched | 200 | -0.211 | 0.076 | 0.048 | 0.103 | 0.204 | 0.217 | 0.965 |
| ukb-allhat | phys_only | sparse | 200 | -0.235 | 0.015 | -0.019 | 0.047 | 0.249 | 0.249 | 0.970 |
| ukb-allhat | phys_only | sparse+ECG | 200 | -0.207 | -0.015 | -0.051 | 0.022 | 0.263 | 0.262 | 0.970 |
| ukb-allhat | phys_only | hdPS200 | 200 | -0.234 | 0.031 | -0.008 | 0.069 | 0.286 | 0.287 | 0.955 |
| ukb-allhat | phys_only | hdPS200+ECG | 200 | -0.221 | 0.009 | -0.028 | 0.045 | 0.262 | 0.262 | 0.980 |
| ukb-allhat | phys_only | ECGonly | 200 | -0.223 | 0.076 | 0.039 | 0.111 | 0.266 | 0.276 | 0.945 |
| ukb-allhat | phys_only | clinical | 200 | -0.207 | 0.016 | -0.022 | 0.052 | 0.268 | 0.268 | 0.950 |
| ukb-allhat | phys_only | unmatched [clmbr-subset] | 200 | -0.217 | 0.118 | 0.084 | 0.149 | 0.234 | 0.262 | 0.925 |
| ukb-allhat | phys_only | sparse [clmbr-subset] | 200 | -0.223 | 0.007 | -0.033 | 0.045 | 0.277 | 0.277 | 0.945 |
| ukb-allhat | phys_only | sparse+ECG [clmbr-subset] | 200 | -0.219 | 0.031 | -0.005 | 0.066 | 0.266 | 0.267 | 0.965 |
| ukb-allhat | phys_only | hdPS200 [clmbr-subset] | 200 | -0.196 | -0.033 | -0.075 | 0.007 | 0.306 | 0.307 | 0.945 |
| ukb-allhat | phys_only | hdPS200+ECG [clmbr-subset] | 200 | -0.216 | 0.009 | -0.031 | 0.048 | 0.301 | 0.301 | 0.940 |
| ukb-allhat | phys_only | CLMBR | 200 | -0.219 | 0.022 | -0.021 | 0.061 | 0.292 | 0.293 | 0.945 |
| ukb-allhat | phys_only | sparse+CLMBR | 200 | -0.226 | 0.034 | -0.005 | 0.073 | 0.286 | 0.288 | 0.940 |
| ukb-allhat | phys_only | sparse+CLMBR+ECG | 200 | -0.218 | 0.027 | -0.014 | 0.066 | 0.289 | 0.289 | 0.955 |
| ukb-allhat | phys_only | hdPS200+CLMBR | 200 | -0.222 | 0.013 | -0.032 | 0.052 | 0.308 | 0.307 | 0.950 |
| ukb-ascot | base | unmatched | 200 | -0.231 | -0.324 | -0.346 | -0.302 | 0.159 | 0.360 | 0.435 |
| ukb-ascot | base | sparse | 200 | -0.212 | -0.070 | -0.099 | -0.039 | 0.226 | 0.236 | 0.950 |
| ukb-ascot | base | sparse+ECG | 200 | -0.208 | -0.037 | -0.070 | -0.004 | 0.237 | 0.239 | 0.955 |
| ukb-ascot | base | hdPS200 | 200 | -0.219 | 0.009 | -0.027 | 0.043 | 0.254 | 0.253 | 0.955 |
| ukb-ascot | base | hdPS200+ECG | 200 | -0.224 | 0.003 | -0.032 | 0.037 | 0.246 | 0.246 | 0.965 |
| ukb-ascot | base | ECGonly | 200 | -0.214 | -0.262 | -0.290 | -0.235 | 0.202 | 0.330 | 0.720 |
| ukb-ascot | base | clinical | 200 | -0.221 | 0.047 | 0.013 | 0.080 | 0.244 | 0.247 | 0.955 |
| ukb-ascot | base | unmatched [clmbr-subset] | 200 | -0.218 | -0.354 | -0.376 | -0.332 | 0.162 | 0.389 | 0.410 |
| ukb-ascot | base | sparse [clmbr-subset] | 200 | -0.226 | -0.069 | -0.103 | -0.035 | 0.247 | 0.256 | 0.955 |
| ukb-ascot | base | sparse+ECG [clmbr-subset] | 200 | -0.217 | -0.071 | -0.107 | -0.037 | 0.258 | 0.267 | 0.950 |
| ukb-ascot | base | hdPS200 [clmbr-subset] | 200 | -0.214 | -0.007 | -0.044 | 0.031 | 0.270 | 0.269 | 0.955 |
| ukb-ascot | base | hdPS200+ECG [clmbr-subset] | 200 | -0.209 | -0.041 | -0.076 | -0.004 | 0.260 | 0.263 | 0.970 |
| ukb-ascot | base | CLMBR | 200 | -0.229 | -0.084 | -0.113 | -0.055 | 0.210 | 0.225 | 0.940 |
| ukb-ascot | base | sparse+CLMBR | 200 | -0.234 | -0.030 | -0.069 | 0.008 | 0.270 | 0.271 | 0.955 |
| ukb-ascot | base | sparse+CLMBR+ECG | 200 | -0.221 | -0.047 | -0.079 | -0.014 | 0.235 | 0.239 | 0.960 |
| ukb-ascot | base | hdPS200+CLMBR | 200 | -0.221 | -0.051 | -0.087 | -0.014 | 0.274 | 0.278 | 0.935 |
| ukb-ascot | phys_only | unmatched | 200 | -0.219 | -0.108 | -0.129 | -0.086 | 0.156 | 0.189 | 0.935 |
| ukb-ascot | phys_only | sparse | 200 | -0.244 | -0.013 | -0.047 | 0.022 | 0.250 | 0.250 | 0.970 |
| ukb-ascot | phys_only | sparse+ECG | 200 | -0.250 | 0.001 | -0.032 | 0.038 | 0.250 | 0.249 | 0.975 |
| ukb-ascot | phys_only | hdPS200 | 200 | -0.222 | -0.011 | -0.047 | 0.024 | 0.254 | 0.254 | 0.955 |
| ukb-ascot | phys_only | hdPS200+ECG | 200 | -0.207 | -0.044 | -0.081 | -0.004 | 0.285 | 0.288 | 0.960 |
| ukb-ascot | phys_only | ECGonly | 200 | -0.225 | -0.057 | -0.083 | -0.031 | 0.188 | 0.196 | 0.945 |
| ukb-ascot | phys_only | clinical | 200 | -0.222 | 0.037 | 0.004 | 0.071 | 0.253 | 0.255 | 0.965 |
| ukb-ascot | phys_only | unmatched [clmbr-subset] | 200 | -0.224 | -0.081 | -0.108 | -0.056 | 0.189 | 0.205 | 0.905 |
| ukb-ascot | phys_only | sparse [clmbr-subset] | 200 | -0.203 | -0.048 | -0.088 | -0.006 | 0.300 | 0.303 | 0.955 |
| ukb-ascot | phys_only | sparse+ECG [clmbr-subset] | 200 | -0.223 | -0.035 | -0.074 | 0.007 | 0.281 | 0.282 | 0.970 |
| ukb-ascot | phys_only | hdPS200 [clmbr-subset] | 200 | -0.228 | -0.022 | -0.063 | 0.017 | 0.295 | 0.295 | 0.930 |
| ukb-ascot | phys_only | hdPS200+ECG [clmbr-subset] | 200 | -0.225 | -0.027 | -0.070 | 0.015 | 0.301 | 0.301 | 0.960 |
| ukb-ascot | phys_only | CLMBR | 200 | -0.222 | -0.004 | -0.040 | 0.031 | 0.262 | 0.261 | 0.905 |
| ukb-ascot | phys_only | sparse+CLMBR | 200 | -0.210 | -0.061 | -0.100 | -0.022 | 0.281 | 0.287 | 0.955 |
| ukb-ascot | phys_only | sparse+CLMBR+ECG | 200 | -0.218 | -0.044 | -0.088 | -0.001 | 0.309 | 0.311 | 0.925 |
| ukb-ascot | phys_only | hdPS200+CLMBR | 200 | -0.227 | -0.033 | -0.075 | 0.010 | 0.312 | 0.313 | 0.950 |
| ukb-ontarget | base | unmatched | 200 | -0.213 | 0.015 | -0.003 | 0.032 | 0.124 | 0.125 | 0.945 |
| ukb-ontarget | base | sparse | 200 | -0.201 | 0.006 | -0.013 | 0.024 | 0.132 | 0.132 | 0.950 |
| ukb-ontarget | base | sparse+ECG | 200 | -0.213 | 0.021 | 0.002 | 0.039 | 0.135 | 0.136 | 0.965 |
| ukb-ontarget | base | hdPS200 | 200 | -0.217 | 0.028 | 0.008 | 0.048 | 0.145 | 0.147 | 0.935 |
| ukb-ontarget | base | hdPS200+ECG | 200 | -0.226 | 0.050 | 0.031 | 0.069 | 0.140 | 0.148 | 0.955 |
| ukb-ontarget | base | ECGonly | 200 | -0.218 | 0.027 | 0.007 | 0.047 | 0.143 | 0.146 | 0.930 |
| ukb-ontarget | base | clinical | 200 | -0.204 | -0.020 | -0.040 | -0.001 | 0.141 | 0.142 | 0.955 |
| ukb-ontarget | base | unmatched [clmbr-subset] | 200 | -0.217 | 0.008 | -0.011 | 0.026 | 0.132 | 0.132 | 0.955 |
| ukb-ontarget | base | sparse [clmbr-subset] | 200 | -0.211 | -0.009 | -0.030 | 0.012 | 0.148 | 0.148 | 0.965 |
| ukb-ontarget | base | sparse+ECG [clmbr-subset] | 200 | -0.209 | -0.022 | -0.043 | -0.001 | 0.149 | 0.151 | 0.965 |
| ukb-ontarget | base | hdPS200 [clmbr-subset] | 200 | -0.216 | 0.004 | -0.017 | 0.026 | 0.154 | 0.154 | 0.940 |
| ukb-ontarget | base | hdPS200+ECG [clmbr-subset] | 200 | -0.204 | -0.007 | -0.030 | 0.015 | 0.156 | 0.156 | 0.965 |
| ukb-ontarget | base | CLMBR | 200 | -0.217 | 0.001 | -0.022 | 0.021 | 0.155 | 0.154 | 0.950 |
| ukb-ontarget | base | sparse+CLMBR | 200 | -0.216 | -0.010 | -0.031 | 0.010 | 0.149 | 0.149 | 0.960 |
| ukb-ontarget | base | sparse+CLMBR+ECG | 200 | -0.211 | -0.007 | -0.029 | 0.014 | 0.155 | 0.155 | 0.950 |
| ukb-ontarget | base | hdPS200+CLMBR | 200 | -0.224 | 0.019 | -0.003 | 0.038 | 0.150 | 0.151 | 0.955 |
| ukb-ontarget | phys_only | unmatched | 200 | -0.217 | -0.023 | -0.041 | -0.004 | 0.132 | 0.134 | 0.970 |
| ukb-ontarget | phys_only | sparse | 200 | -0.215 | -0.006 | -0.026 | 0.017 | 0.154 | 0.154 | 0.965 |
| ukb-ontarget | phys_only | sparse+ECG | 200 | -0.215 | -0.002 | -0.023 | 0.021 | 0.153 | 0.153 | 0.960 |
| ukb-ontarget | phys_only | hdPS200 | 200 | -0.219 | 0.007 | -0.015 | 0.029 | 0.158 | 0.158 | 0.980 |
| ukb-ontarget | phys_only | hdPS200+ECG | 200 | -0.224 | 0.013 | -0.010 | 0.036 | 0.161 | 0.161 | 0.955 |
| ukb-ontarget | phys_only | ECGonly | 200 | -0.215 | -0.002 | -0.023 | 0.020 | 0.155 | 0.155 | 0.955 |
| ukb-ontarget | phys_only | clinical | 200 | -0.212 | -0.016 | -0.038 | 0.006 | 0.154 | 0.155 | 0.955 |
| ukb-ontarget | phys_only | unmatched [clmbr-subset] | 200 | -0.216 | -0.015 | -0.034 | 0.005 | 0.141 | 0.141 | 0.965 |
| ukb-ontarget | phys_only | sparse [clmbr-subset] | 200 | -0.224 | -0.003 | -0.024 | 0.018 | 0.156 | 0.156 | 0.960 |
| ukb-ontarget | phys_only | sparse+ECG [clmbr-subset] | 200 | -0.210 | -0.016 | -0.038 | 0.007 | 0.163 | 0.163 | 0.940 |
| ukb-ontarget | phys_only | hdPS200 [clmbr-subset] | 200 | -0.221 | -0.002 | -0.025 | 0.022 | 0.172 | 0.171 | 0.945 |
| ukb-ontarget | phys_only | hdPS200+ECG [clmbr-subset] | 200 | -0.211 | -0.024 | -0.047 | -0.001 | 0.164 | 0.166 | 0.970 |
| ukb-ontarget | phys_only | CLMBR | 200 | -0.211 | -0.029 | -0.051 | -0.006 | 0.162 | 0.164 | 0.955 |
| ukb-ontarget | phys_only | sparse+CLMBR | 200 | -0.230 | 0.010 | -0.012 | 0.033 | 0.168 | 0.167 | 0.925 |
| ukb-ontarget | phys_only | sparse+CLMBR+ECG | 200 | -0.225 | 0.000 | -0.023 | 0.023 | 0.162 | 0.162 | 0.950 |
| ukb-ontarget | phys_only | hdPS200+CLMBR | 200 | -0.216 | -0.006 | -0.030 | 0.020 | 0.181 | 0.181 | 0.925 |

## Plasmode bias reduction (|bias second| - |bias first|; positive = first arm less biased; MC 95% CI)

| trial | scenario | contrast | bias_second | bias_first | abs_bias_reduction | lo | hi | pct_reduction |
|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | base | C1 | -0.009 | -0.044 | -0.035 | -0.055 | 0.019 | -373.971 |
| mimic-aristotle | base | C2 | 0.067 | 0.067 | 0.000 | -0.023 | 0.023 | 0.548 |
| mimic-aristotle | base | ECGonly | -0.042 | -0.023 | 0.019 | -0.009 | 0.036 | 45.238 |
| mimic-aristotle | phys_only | C1 | 0.043 | 0.035 | 0.007 | -0.018 | 0.032 | 17.448 |
| mimic-aristotle | phys_only | C2 | 0.056 | 0.083 | -0.027 | -0.053 | -0.002 | -48.889 |
| mimic-aristotle | phys_only | ECGonly | 0.065 | 0.084 | -0.019 | -0.038 | -0.001 | -29.021 |
| mimic-comet | base | C1 | 0.058 | 0.058 | -0.000 | -0.018 | 0.017 | -0.163 |
| mimic-comet | base | C2 | 0.012 | 0.019 | -0.007 | -0.022 | 0.009 | -57.538 |
| mimic-comet | base | ECGonly | 0.164 | 0.108 | 0.056 | 0.045 | 0.067 | 33.989 |
| mimic-comet | phys_only | C1 | 0.030 | 0.026 | 0.004 | -0.011 | 0.020 | 14.463 |
| mimic-comet | phys_only | C2 | 0.025 | 0.015 | 0.010 | -0.005 | 0.024 | 38.539 |
| mimic-comet | phys_only | ECGonly | 0.130 | 0.097 | 0.033 | 0.021 | 0.044 | 25.109 |
| mimic-plato | base | C1 | 0.036 | 0.032 | 0.003 | -0.013 | 0.019 | 9.540 |
| mimic-plato | base | C2 | 0.063 | 0.068 | -0.005 | -0.022 | 0.012 | -7.857 |
| mimic-plato | base | ECGonly | -0.234 | -0.117 | 0.116 | 0.103 | 0.129 | 49.762 |
| mimic-plato | phys_only | C1 | -0.004 | 0.003 | 0.001 | -0.015 | 0.017 | 23.094 |
| mimic-plato | phys_only | C2 | 0.013 | 0.018 | -0.005 | -0.022 | 0.013 | -35.864 |
| mimic-plato | phys_only | ECGonly | -0.327 | -0.202 | 0.125 | 0.112 | 0.138 | 38.278 |
| mimic-rocket_af | base | C1 | 0.005 | -0.026 | -0.022 | -0.056 | 0.048 | -477.781 |
| mimic-rocket_af | base | C2 | 0.059 | -0.003 | 0.055 | -0.047 | 0.087 | 94.188 |
| mimic-rocket_af | base | ECGonly | -0.149 | -0.096 | 0.053 | 0.020 | 0.086 | 35.493 |
| mimic-rocket_af | phys_only | C1 | 0.033 | -0.010 | 0.023 | -0.054 | 0.075 | 68.992 |
| mimic-rocket_af | phys_only | C2 | -0.035 | -0.059 | -0.024 | -0.053 | 0.016 | -68.916 |
| mimic-rocket_af | phys_only | ECGonly | -0.077 | -0.080 | -0.003 | -0.035 | 0.029 | -3.340 |
| mimic-transform_hf | base | C1 | 0.042 | 0.019 | 0.023 | 0.010 | 0.035 | 53.964 |
| mimic-transform_hf | base | C2 | -0.021 | -0.027 | -0.006 | -0.016 | 0.004 | -29.071 |
| mimic-transform_hf | base | ECGonly | 0.024 | 0.031 | -0.008 | -0.015 | 0.000 | -31.291 |
| mimic-transform_hf | phys_only | C1 | -0.019 | -0.022 | -0.003 | -0.014 | 0.007 | -16.512 |
| mimic-transform_hf | phys_only | C2 | -0.038 | -0.042 | -0.004 | -0.016 | 0.006 | -11.740 |
| mimic-transform_hf | phys_only | ECGonly | -0.023 | -0.016 | 0.006 | -0.003 | 0.015 | 27.082 |
| ukb-allhat | base | C1 | -0.022 | 0.008 | 0.014 | -0.034 | 0.046 | 63.601 |
| ukb-allhat | base | C2 | -0.080 | -0.050 | 0.030 | 0.003 | 0.056 | 37.715 |
| ukb-allhat | base | ECGonly | 0.089 | 0.049 | 0.040 | 0.021 | 0.059 | 44.979 |
| ukb-allhat | base | C1 [sub] | -0.009 | -0.017 | -0.008 | -0.029 | 0.021 | -96.381 |
| ukb-allhat | base | C2 [sub] | -0.067 | -0.069 | -0.002 | -0.030 | 0.025 | -2.810 |
| ukb-allhat | base | CLMBR vs unmatched [sub] | 0.089 | 0.018 | 0.071 | 0.042 | 0.087 | 79.620 |
| ukb-allhat | base | sparse+CLMBR vs sparse [sub] | -0.009 | 0.031 | -0.023 | -0.054 | 0.038 | -260.556 |
| ukb-allhat | base | sparse+CLMBR+ECG vs sparse+CLMBR | 0.031 | -0.001 | 0.030 | -0.033 | 0.048 | 96.680 |
| ukb-allhat | base | sparse+CLMBR+ECG vs sparse+ECG [sub] | -0.017 | -0.001 | 0.016 | -0.025 | 0.034 | 93.905 |
| ukb-allhat | base | hdPS200+CLMBR vs hdPS200 [sub] | -0.067 | -0.033 | 0.034 | 0.006 | 0.060 | 51.329 |
| ukb-allhat | phys_only | C1 | 0.015 | -0.015 | -0.001 | -0.042 | 0.038 | -5.029 |
| ukb-allhat | phys_only | C2 | 0.031 | 0.009 | 0.022 | -0.020 | 0.046 | 70.016 |
| ukb-allhat | phys_only | ECGonly | 0.076 | 0.076 | 0.000 | -0.024 | 0.024 | 0.135 |
| ukb-allhat | phys_only | C1 [sub] | 0.007 | 0.031 | -0.025 | -0.044 | 0.025 | -374.817 |
| ukb-allhat | phys_only | C2 [sub] | -0.033 | 0.009 | 0.024 | -0.039 | 0.059 | 72.774 |
| ukb-allhat | phys_only | CLMBR vs unmatched [sub] | 0.118 | 0.022 | 0.096 | 0.066 | 0.114 | 81.345 |
| ukb-allhat | phys_only | sparse+CLMBR vs sparse [sub] | 0.007 | 0.034 | -0.028 | -0.048 | 0.024 | -420.982 |
| ukb-allhat | phys_only | sparse+CLMBR+ECG vs sparse+CLMBR | 0.034 | 0.027 | 0.007 | -0.021 | 0.032 | 20.182 |
| ukb-allhat | phys_only | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.031 | 0.027 | 0.004 | -0.023 | 0.030 | 12.422 |
| ukb-allhat | phys_only | hdPS200+CLMBR vs hdPS200 [sub] | -0.033 | 0.013 | 0.020 | -0.045 | 0.058 | 60.485 |
| ukb-ascot | base | C1 | -0.070 | -0.037 | 0.033 | 0.005 | 0.059 | 46.743 |
| ukb-ascot | base | C2 | 0.009 | 0.003 | 0.006 | -0.022 | 0.026 | 65.600 |
| ukb-ascot | base | ECGonly | -0.324 | -0.262 | 0.062 | 0.046 | 0.076 | 19.086 |
| ukb-ascot | base | C1 [sub] | -0.069 | -0.071 | -0.002 | -0.033 | 0.029 | -2.541 |
| ukb-ascot | base | C2 [sub] | -0.007 | -0.041 | -0.034 | -0.052 | 0.019 | -471.622 |
| ukb-ascot | base | CLMBR vs unmatched [sub] | -0.354 | -0.084 | 0.270 | 0.250 | 0.291 | 76.290 |
| ukb-ascot | base | sparse+CLMBR vs sparse [sub] | -0.069 | -0.030 | 0.039 | 0.006 | 0.071 | 56.102 |
| ukb-ascot | base | sparse+CLMBR+ECG vs sparse+CLMBR | -0.030 | -0.047 | -0.017 | -0.046 | 0.014 | -55.019 |
| ukb-ascot | base | sparse+CLMBR+ECG vs sparse+ECG [sub] | -0.071 | -0.047 | 0.024 | -0.003 | 0.053 | 33.636 |
| ukb-ascot | base | hdPS200+CLMBR vs hdPS200 [sub] | -0.007 | -0.051 | -0.043 | -0.064 | 0.012 | -610.112 |
| ukb-ascot | phys_only | C1 | -0.013 | 0.001 | 0.012 | -0.027 | 0.034 | 91.337 |
| ukb-ascot | phys_only | C2 | -0.011 | -0.044 | -0.032 | -0.060 | 0.013 | -284.287 |
| ukb-ascot | phys_only | ECGonly | -0.108 | -0.057 | 0.051 | 0.037 | 0.064 | 46.886 |
| ukb-ascot | phys_only | C1 [sub] | -0.048 | -0.035 | 0.013 | -0.018 | 0.043 | 28.016 |
| ukb-ascot | phys_only | C2 [sub] | -0.022 | -0.027 | -0.005 | -0.033 | 0.024 | -21.320 |
| ukb-ascot | phys_only | CLMBR vs unmatched [sub] | -0.081 | -0.004 | 0.077 | 0.027 | 0.089 | 94.662 |
| ukb-ascot | phys_only | sparse+CLMBR vs sparse [sub] | -0.048 | -0.061 | -0.013 | -0.045 | 0.018 | -27.206 |
| ukb-ascot | phys_only | sparse+CLMBR+ECG vs sparse+CLMBR | -0.061 | -0.044 | 0.017 | -0.014 | 0.045 | 27.440 |
| ukb-ascot | phys_only | sparse+CLMBR+ECG vs sparse+ECG [sub] | -0.035 | -0.044 | -0.010 | -0.040 | 0.022 | -28.223 |
| ukb-ascot | phys_only | hdPS200+CLMBR vs hdPS200 [sub] | -0.022 | -0.033 | -0.010 | -0.041 | 0.020 | -46.986 |
| ukb-ontarget | base | C1 | 0.006 | 0.021 | -0.015 | -0.025 | 0.008 | -238.194 |
| ukb-ontarget | base | C2 | 0.028 | 0.050 | -0.022 | -0.036 | -0.009 | -79.371 |
| ukb-ontarget | base | ECGonly | 0.015 | 0.027 | -0.012 | -0.021 | -0.001 | -79.562 |
| ukb-ontarget | base | C1 [sub] | -0.009 | -0.022 | -0.013 | -0.024 | 0.007 | -142.659 |
| ukb-ontarget | base | C2 [sub] | 0.004 | -0.007 | -0.003 | -0.020 | 0.018 | -58.710 |
| ukb-ontarget | base | CLMBR vs unmatched [sub] | 0.008 | 0.001 | 0.008 | -0.015 | 0.014 | 92.931 |
| ukb-ontarget | base | sparse+CLMBR vs sparse [sub] | -0.009 | -0.010 | -0.001 | -0.013 | 0.011 | -13.440 |
