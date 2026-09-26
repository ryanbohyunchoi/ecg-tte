# v1.5 external first pass: MIMIC-IV and UK Biobank. Corrected after the independent audit (exploratory)

- Protocol: `docs/PROTOCOL_V1_5_EXTERNAL.md` (tag `protocol-v1.5`; deviation log and audit corrections).
- Audit: `docs/AUDIT_V15_2026_09_26.md`.
- Code: `scripts/v15/`.
- Everything below is aggregate and post hoc relative to the Yale phase 2.

## Corrections applied

1. **Pooled inference.** The headline pools by RCT: 18 distinct RCTs, exact sign-flip.
2. **MIMIC baseline.** Diagnoses and the hdPS panel now come from earlier admissions only. Index
   discharge codes previously leaked in, including adverse-effect and INR codes.
3. **MIMIC outcomes.** An MI or stroke readmission within 28 days counts only as I22 or as the
   primary diagnosis.
4. **UK Biobank.**
   - The ECG is labelled as an on-treatment covariate.
   - Eligibility and CV-death sensitivity analyses were added. CV death uses the derived flags in
     `ukb_working_file.csv`, censored at 2020-12-31.
5. **Engine validation.** Given Yale's exact design and population, the engine reproduces Yale
   bit-for-bit (differences below 1e-16). Matched arms are sensitive to 5-patient differences in
   the population.

## Headline: Yale + external, pooled by RCT (18 RCTs, 26 emulations, exact sign-flip)

| Contrast | RCTs closer | Sign test p | Mean Δ\|Δlog HR\| (p) | Mean Δ precision-standardised z² (p) |
|---|---|---|---|---|
| Sparse + ECG vs sparse | 12/18 | 0.24 | −0.035 (0.21) | **−1.31 (0.044)** |
| hdPS200 + ECG vs hdPS200 | 10/18 | 0.82 | −0.003 (0.90) | −0.28 (0.42) |
| **ECG only vs unadjusted** | **14/18** | **0.031** | **−0.059 (0.025)** | **−5.86 (0.001)** |

- **Per emulation (descriptive only):** C1 closer in 19/26; ECG only 19/26.
- **Yale vs external, same direction across the 8 shared RCTs:**
  - C1: 6/8 (discordant: ASCOT, PLATO).
  - C2: 6/8.

## External trials only (corrected MIMIC + UKB main; 8 trials)

**Contrasts** (exact sign-flip):

| Contrast | Trials closer | Mean Δ\|Δlog HR\| (p) |
|---|---|---|
| C1 (sparse + ECG vs sparse) | 5/8 | −0.095 (0.39) |
| C2 (hdPS200 + ECG vs hdPS200) | 6/8 | −0.055 (0.22) |

**Panel:**

| Arm | Mean \|Δlog HR\| | φ | Estimate agreement |
|---|---|---|---|
| Unadjusted | 0.26 | 3.73 | 0.12 |
| Sparse | 0.24 | 1.27 | 0.50 |
| **Sparse + ECG** | **0.14** | **0.91** | 0.38 |
| hdPS200 | 0.20 | 1.02 | 0.25 |
| hdPS200 + ECG | 0.15 | 0.61 | 0.50 |
| Clinical | 0.25 | 1.49 | 0.38 |

**Plasmode**, pooled bias reduction:
- C1: +0.013 (MC CI 0.005 to 0.025).
- C2: −0.005 (−0.015 to 0.009).
- ECG only vs unadjusted: +0.037 (0.026 to 0.042).

**Negative-control calibration** (MIMIC). Adding the ECG does not reduce systematic error for C1
(lower |μ| in 0 of 4 trials). hdPS200 + ECG has the lowest σ.

**Sensitivity analyses** (full tables below):
- **UKB eligibility-matched:** C1 closer in 3/3; sparse + ECG mean |Δ| 0.039 vs 0.180 for sparse.
- **UKB CV death** (2020 censoring): too few events; every arm, including unadjusted, sits far from
  the RCTs.

## Engine summaries


### summary_all

# v1.5 external first pass — cohort: all

Exploratory (protocol v1.5). Benchmarks are rct.json our_orientation; SE from the reported CI. Pair counts in brackets. Event counts < 11 suppressed upstream. Aggregates only. Analysed N = the ECG-linked subset. UKB: prevalent users, and the ECG is an on-treatment covariate (recorded at the exposure-defining visit).

Engine validation (Yale LIFE, exact Yale design and population): unmatched, sparse, sparse+ECG, hdPS200, hdPS200+ECG and clinical log HRs reproduce Yale imputation-1 rep 0 to < 1e-15 (docs: compare_yale_exact.csv).

## Trial directories

| trial | markers | analysed | plasmode | n_clmbr_subset | clinical_pairs | pairs_rule_150 | n_treated | n_control | events_treated | events_control | imprecise(<30 events/arm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | cohort,ecg,outcomes | True | True | <NA> | 1327 | pass | 1556 | 3576 | 16 | 69 | yes |
| mimic-comet | cohort,ecg,outcomes | True | True | <NA> | 739 | pass | 4101 | 743 | 981 | 130 |  |
| mimic-plato | cohort,ecg,outcomes | True | True | <NA> | 422 | pass | 441 | 2433 | 63 | 571 |  |
| mimic-rocket_af | cohort,ecg,outcomes | True | True | <NA> | 901 | pass | 905 | 5591 | 11 | 99 | yes |
| mimic-transform_hf | cohort,ecg,outcomes | True | True | <NA> | 904 | pass | 940 | 3466 | 251 | 764 |  |
| ukb-allhat | cohort,ecg,outcomes | True | True | 3543 | 1279 | pass | 3446 | 1374 | 85 | 45 |  |
| ukb-aristotle | infeasible | False | False | <NA> | <NA> |  | <NA> | <NA> | nan | nan |  |
| ukb-ascot | cohort,ecg,outcomes | True | True | 3912 | 1032 | pass | 3452 | 1910 | 88 | 99 |  |
| ukb-ontarget | cohort,ecg,outcomes | True | True | 5683 | 2563 | pass | 2567 | 4931 | 124 | 243 |  |

## Hazard ratios per trial (HR (95% CI) [pairs]) — full analysed cohort

| trial | rct | N | unmatched | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | 0.79 (0.66–0.95) | 5132 | 0.52 (0.30–0.89) | 0.49 (0.26–0.89) [1477] | 0.55 (0.29–1.05) [1478] | 0.51 (0.25–1.03) [1264] | 0.58 (0.31–1.11) [1263] | 0.49 (0.27–0.89) [1553] | 0.37 (0.19–0.74) [1327] |
| mimic-comet | 1.21 (1.07–1.35) | 4844 | 1.41 (1.17–1.69) | 1.35 (1.09–1.67) [738] | 1.24 (0.98–1.56) [740] | 1.22 (0.98–1.53) [709] | 1.04 (0.81–1.33) [708] | 1.37 (1.09–1.72) [741] | 1.17 (0.93–1.48) [739] |
| mimic-plato | 0.84 (0.77–0.92) | 2874 | 0.59 (0.45–0.76) | 0.77 (0.56–1.06) [441] | 0.71 (0.52–0.96) [432] | 0.92 (0.66–1.28) [426] | 0.89 (0.61–1.29) [399] | 0.78 (0.57–1.08) [441] | 0.81 (0.57–1.16) [422] |
| mimic-rocket_af | 0.88 (0.75–1.04) | 6496 | 0.65 (0.35–1.21) | 0.44 (0.22–0.88) [902] | 0.89 (0.39–2.02) [900] | 0.67 (0.31–1.45) [892] | 0.90 (0.39–2.04) [896] | 0.70 (0.32–1.54) [905] | 0.54 (0.26–1.11) [901] |
| mimic-transform_hf | 1.02 (0.89–1.17) | 4406 | 1.24 (1.07–1.43) | 1.10 (0.93–1.32) [940] | 1.23 (1.02–1.48) [940] | 1.21 (0.99–1.48) [808] | 1.13 (0.93–1.37) [801] | 1.08 (0.91–1.29) [940] | 1.23 (1.02–1.48) [904] |
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
| unmatched | 8 | 0.75 | 0.12 | 0.75 | 0.93 | 0.61 | 0.88 | 0.71 | 1.08 | 0.73 | 3.73 | 0.26 |
| sparse | 8 | 0.75 | 0.50 | 1.00 | 0.85 | 0.53 | 0.97 | 0.84 | 1.11 | 0.21 | 1.27 | 0.24 |
| sparse+ECG | 8 | 0.62 | 0.38 | 1.00 | 0.89 | 0.23 | 0.99 | 0.88 | 1.12 | 0.00 | 0.91 | 0.14 |
| hdPS200 | 8 | 0.62 | 0.25 | 1.00 | 0.77 | 0.00 | 0.99 | 0.88 | 1.12 | 0.02 | 1.02 | 0.20 |
| hdPS200+ECG | 8 | 0.62 | 0.50 | 1.00 | 0.68 | 0.00 | 0.95 | 0.84 | 1.07 | 0.00 | 0.61 | 0.15 |
| ECGonly | 8 | 0.75 | 0.38 | 0.88 | 0.92 | 0.53 | 0.95 | 0.83 | 1.10 | 0.23 | 1.29 | 0.19 |
| clinical | 8 | 0.62 | 0.38 | 0.88 | 0.82 | 0.23 | 0.93 | 0.79 | 1.09 | 0.33 | 1.49 | 0.25 |
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
| C1 | sparse+ECG | sparse | mimic-aristotle | -0.126 | -1.117 | 0.360 | 0.486 |
| C1 | sparse+ECG | sparse | mimic-comet | -0.084 | -0.761 | 0.028 | 0.112 |
| C1 | sparse+ECG | sparse | mimic-plato | 0.082 | 0.809 | 0.168 | 0.086 |
| C1 | sparse+ECG | sparse | mimic-rocket_af | -0.687 | -3.640 | 0.010 | 0.697 |
| C1 | sparse+ECG | sparse | mimic-transform_hf | 0.107 | 2.029 | 0.186 | 0.079 |
| C1 | sparse+ECG | sparse | ukb-allhat | -0.111 | -0.677 | 0.107 | 0.218 |
| C1 | sparse+ECG | sparse | ukb-ascot | 0.113 | 0.959 | 0.274 | 0.161 |
| C1 | sparse+ECG | sparse | ukb-ontarget | -0.050 | -0.174 | 0.006 | 0.056 |
| C2 | hdPS200+ECG | hdPS200 | mimic-aristotle | -0.136 | -0.600 | 0.304 | 0.441 |
| C2 | hdPS200+ECG | hdPS200 | mimic-comet | 0.135 | 1.134 | 0.148 | 0.013 |
| C2 | hdPS200+ECG | hdPS200 | mimic-plato | -0.037 | -0.194 | 0.054 | 0.091 |
| C2 | hdPS200+ECG | hdPS200 | mimic-rocket_af | -0.251 | -0.455 | 0.021 | 0.273 |
| C2 | hdPS200+ECG | hdPS200 | mimic-transform_hf | -0.071 | -1.233 | 0.101 | 0.172 |
| C2 | hdPS200+ECG | hdPS200 | ukb-allhat | -0.070 | -0.813 | 0.303 | 0.373 |
| C2 | hdPS200+ECG | hdPS200 | ukb-ascot | -0.015 | -0.013 | 0.193 | 0.208 |
| C2 | hdPS200+ECG | hdPS200 | ukb-ontarget | 0.007 | 0.053 | 0.061 | 0.054 |
| ECGonly | ECGonly | unmatched | mimic-aristotle | 0.053 | 0.184 | 0.473 | 0.419 |
| ECGonly | ECGonly | unmatched | mimic-comet | -0.030 | -1.053 | 0.128 | 0.157 |
| ECGonly | ECGonly | unmatched | mimic-plato | -0.289 | -6.280 | 0.071 | 0.360 |
| ECGonly | ECGonly | unmatched | mimic-rocket_af | -0.076 | -0.533 | 0.224 | 0.300 |
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

Across trials (sign-flip: exact enumeration up to 20 trials, else MC; descriptive):

| contrast | first | second | trials | closer | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 | signflip |
|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 8 | 5/8 | -0.095 | 0.391 | -0.322 | 0.648 | exact |
| C2 | hdPS200+ECG | hdPS200 | 8 | 6/8 | -0.055 | 0.219 | -0.265 | 0.305 | exact |
| ECGonly | ECGonly | unmatched | 8 | 5/8 | -0.070 | 0.133 | -2.213 | 0.055 | exact |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | 3 | 2/3 | -0.040 | 0.500 | -0.211 | 0.750 | exact |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | 3 | 2/3 | -0.040 | 0.750 | -0.145 | 1.000 | exact |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | 3 | 0/3 | 0.099 | 0.250 | -1.026 | 1.000 | exact |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | 3 | 2/3 | 0.068 | 1.000 | 0.600 | 1.000 | exact |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | 3 | 3/3 | -0.133 | 0.250 | -0.997 | 0.250 | exact |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | 3 | 2/3 | -0.025 | 0.500 | -0.186 | 0.500 | exact |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | 3 | 1/3 | 0.026 | 0.750 | 0.166 | 0.750 | exact |

## Pooled Yale + external — HEADLINE: RCT-clustered (post hoc; corrections item 1)

Yale phase-2 (imputation 1, rep 0; 18 trials) + external v1.5 emulations (main cohorts only; sensitivity variants excluded). Paired differences are averaged within each RCT benchmark (trial_specs key), then tested across RCTs (exact sign-flip; two-sided sign test on the count). Negative = first arm closer to the RCT.

| contrast | first | second | rcts | emulations | closer | p_sign | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 | signflip |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 18 | 26 | 12/18 | 0.238 | -0.035 | 0.212 | -1.312 | 0.044 | exact |
| C2 | hdPS200+ECG | hdPS200 | 18 | 26 | 10/18 | 0.815 | -0.003 | 0.904 | -0.282 | 0.421 | exact |
| ECGonly | ECGonly | unmatched | 18 | 26 | 14/18 | 0.031 | -0.059 | 0.025 | -5.864 | 0.001 | exact |

Per-emulation (descriptive only; emulations of the same RCT share its benchmark and are not independent):

| contrast | emulations | closer | p_sign | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 | signflip |
|---|---|---|---|---|---|---|---|---|
| C1 | 26 | 19/26 | 0.029 | -0.043 | 0.147 | -1.071 | 0.026 | MC 20k (seed 0) |
| C2 | 26 | 16/26 | 0.327 | -0.018 | 0.328 | -0.473 | 0.166 | MC 20k (seed 0) |
| ECGonly | 26 | 19/26 | 0.029 | -0.061 | 0.006 | -5.115 | 0.000 | MC 20k (seed 0) |

Yale vs external direction of Δ|log HR − RCT| per shared RCT:

| contrast | key | external | yale_d_abs | external_d_abs | same_direction |
|---|---|---|---|---|---|
| C1 | allhat | ukb-allhat | -0.008 | -0.111 | True |
| C1 | aristotle | mimic-aristotle | -0.051 | -0.126 | True |
| C1 | ascot | ukb-ascot | -0.031 | 0.113 | False |
| C1 | comet | mimic-comet | -0.004 | -0.084 | True |
| C1 | ontarget | ukb-ontarget | -0.022 | -0.050 | True |
| C1 | plato | mimic-plato | -0.053 | 0.082 | False |
| C1 | rocket_af | mimic-rocket_af | -0.044 | -0.687 | True |
| C1 | transform_hf | mimic-transform_hf | 0.006 | 0.107 | True |
| C2 | allhat | ukb-allhat | -0.116 | -0.070 | True |
| C2 | aristotle | mimic-aristotle | -0.051 | -0.136 | True |
| C2 | ascot | ukb-ascot | -0.087 | -0.015 | True |
| C2 | comet | mimic-comet | -0.049 | 0.135 | False |
| C2 | ontarget | ukb-ontarget | 0.001 | 0.007 | True |
| C2 | plato | mimic-plato | 0.034 | -0.037 | False |
| C2 | rocket_af | mimic-rocket_af | -0.147 | -0.251 | True |
| C2 | transform_hf | mimic-transform_hf | -0.004 | -0.071 | True |
| ECGonly | allhat | ukb-allhat | -0.091 | 0.011 | False |
| ECGonly | aristotle | mimic-aristotle | -0.128 | 0.053 | False |
| ECGonly | ascot | ukb-ascot | -0.021 | -0.138 | True |
| ECGonly | comet | mimic-comet | -0.028 | -0.030 | True |
| ECGonly | ontarget | ukb-ontarget | -0.033 | 0.044 | False |
| ECGonly | plato | mimic-plato | -0.083 | -0.289 | True |
| ECGonly | rocket_af | mimic-rocket_af | -0.128 | -0.076 | True |
| ECGonly | transform_hf | mimic-transform_hf | 0.046 | -0.135 | False |

Same direction: C1 6/8, C2 6/8, ECGonly 4/8

## Negative-control outcomes and empirical calibration (OHDSI style)

Usable NCO estimate = NaN rows dropped per NCO, >= 11 NCO events in the arm's analysed sample. Systematic-error model b ~ N(mu, sigma^2 + se^2) (v13 fit_syserr); per trial when >= 6 usable NCOs, else the cohort-pooled fit.

Usable NCOs per trial: mimic-aristotle 9, mimic-comet 9, mimic-plato 8, mimic-rocket_af 9, mimic-transform_hf 9, ukb-allhat 3, ukb-ascot 3, ukb-ontarget 3

### Systematic error pooled across the cohort's trials, per arm

| cohort | arm | trials | nco_estimates | mu | abs_mu | sigma | share_ci_excl_1 |
|---|---|---|---|---|---|---|---|
| mimic | ECGonly | 5 | 34 | -0.028 | 0.028 | 0.139 | 0.118 |
| mimic | clinical | 5 | 34 | -0.002 | 0.002 | 0.061 | 0.000 |
| mimic | hdPS200 | 5 | 34 | -0.058 | 0.058 | 0.091 | 0.088 |
| mimic | hdPS200+ECG | 5 | 33 | -0.032 | 0.032 | 0.029 | 0.030 |
| mimic | sparse | 5 | 33 | 0.053 | 0.053 | 0.211 | 0.091 |
| mimic | sparse+ECG | 5 | 33 | 0.024 | 0.024 | 0.236 | 0.091 |
| mimic | unmatched | 5 | 44 | -0.038 | 0.038 | 0.172 | 0.114 |
| ukb | CLMBR | 3 | 8 | -0.015 | 0.015 | 0.000 | 0.000 |
| ukb | ECGonly | 3 | 9 | -0.054 | 0.054 | 0.096 | 0.111 |
| ukb | clinical | 3 | 8 | -0.144 | 0.144 | 0.226 | 0.250 |
| ukb | hdPS200 | 3 | 9 | -0.058 | 0.058 | 0.000 | 0.111 |
| ukb | hdPS200 [clmbr-subset] | 3 | 8 | -0.054 | 0.054 | 0.000 | 0.000 |
| ukb | hdPS200+CLMBR | 3 | 8 | -0.102 | 0.102 | 0.000 | 0.125 |
| ukb | hdPS200+ECG | 3 | 8 | -0.178 | 0.178 | 0.232 | 0.250 |
| ukb | hdPS200+ECG [clmbr-subset] | 3 | 8 | -0.074 | 0.074 | 0.000 | 0.000 |
| ukb | sparse | 3 | 8 | -0.107 | 0.107 | 0.114 | 0.125 |
| ukb | sparse [clmbr-subset] | 3 | 9 | -0.061 | 0.061 | 0.099 | 0.111 |
| ukb | sparse+CLMBR | 3 | 9 | -0.042 | 0.042 | 0.088 | 0.111 |
| ukb | sparse+CLMBR+ECG | 3 | 8 | -0.034 | 0.034 | 0.000 | 0.000 |
| ukb | sparse+ECG | 3 | 9 | -0.058 | 0.058 | 0.178 | 0.111 |
| ukb | sparse+ECG [clmbr-subset] | 3 | 8 | -0.053 | 0.053 | 0.151 | 0.125 |
| ukb | unmatched | 3 | 9 | -0.107 | 0.107 | 0.190 | 0.333 |
| ukb | unmatched [clmbr-subset] | 3 | 9 | -0.100 | 0.100 | 0.184 | 0.333 |

### Per-trial fits (trials with >= 6 usable NCOs), summarised per arm

| cohort | arm | trials_estimable | mean_abs_mu | mean_sigma | mean_share_ci_excl_1 |
|---|---|---|---|---|---|
| mimic | ECGonly | 4 | 0.138 | 0.051 | 0.122 |
| mimic | clinical | 4 | 0.086 | 0.078 | 0.000 |
| mimic | hdPS200 | 4 | 0.166 | 0.000 | 0.094 |
| mimic | hdPS200+ECG | 4 | 0.130 | 0.052 | 0.031 |
| mimic | sparse | 4 | 0.148 | 0.103 | 0.094 |
| mimic | sparse+ECG | 4 | 0.198 | 0.044 | 0.094 |
| mimic | unmatched | 5 | 0.226 | 0.022 | 0.114 |

Per-trial mu (NCO log HR bias):

| trial | unmatched | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|
| mimic-aristotle | -0.041 | -0.049 | -0.105 | -0.186 | -0.158 | -0.058 | -0.095 |
| mimic-comet | -0.001 | 0.035 | -0.108 | 0.036 | 0.054 | -0.134 | 0.086 |
| mimic-plato | -0.627 | – | – | – | – | – | – |
| mimic-rocket_af | -0.210 | -0.109 | -0.115 | -0.223 | -0.115 | -0.158 | -0.033 |
| mimic-transform_hf | 0.250 | 0.399 | 0.464 | 0.219 | 0.192 | 0.200 | 0.129 |

### Does adding ECG (or CLMBR) reduce systematic error? (per-trial fits; negative = first arm lower; exact sign-flip)

| contrast | first | second | trials | lower_abs_mu | mean_d_abs_mu | p_signflip_abs_mu | mean_d_sigma | p_signflip_sigma | signflip |
|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 4 | 0/4 | 0.050 | 0.125 | -0.059 | 0.625 | exact |
| C2 | hdPS200+ECG | hdPS200 | 4 | 3/4 | -0.036 | 0.250 | 0.052 | 0.750 | exact |
| ECGonly | ECGonly | unmatched | 4 | 2/4 | 0.012 | 0.875 | 0.023 | 1.000 | exact |

### RCT agreement after calibration of the primary estimates

| arm | trials | significance_agreement | estimate_agreement | std_diff_agreement | pearson_r | kappa | ratio_of_ratios | ror_lo | ror_hi | I2 | dispersion_phi | mean_abs_dlog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| unmatched | 8 | 0.75 | 0.38 | 1.00 | 0.74 | 0.53 | 1.02 | 0.87 | 1.19 | 0.34 | 1.51 | 0.19 |
| sparse | 8 | 0.62 | 0.25 | 0.88 | 0.81 | 0.20 | 0.87 | 0.74 | 1.03 | 0.20 | 1.24 | 0.24 |
| sparse+ECG | 8 | 0.75 | 0.38 | 1.00 | 0.84 | 0.43 | 0.97 | 0.83 | 1.14 | 0.00 | 0.63 | 0.16 |
| hdPS200 | 8 | 0.62 | 0.50 | 1.00 | 0.72 | 0.00 | 0.96 | 0.85 | 1.09 | 0.00 | 0.40 | 0.12 |
| hdPS200+ECG | 8 | 0.62 | 0.62 | 1.00 | 0.57 | 0.00 | 0.95 | 0.81 | 1.12 | 0.00 | 0.24 | 0.11 |
| ECGonly | 8 | 0.75 | 0.50 | 0.88 | 0.91 | 0.53 | 0.96 | 0.81 | 1.13 | 0.34 | 1.51 | 0.18 |
| clinical | 8 | 0.75 | 0.50 | 1.00 | 0.80 | 0.41 | 0.96 | 0.82 | 1.12 | 0.00 | 0.74 | 0.20 |
| unmatched [clmbr-subset] | 3 | 0.67 | 0.33 | 1.00 | 1.00 | 0.00 | 0.90 | 0.62 | 1.29 | 0.44 | 1.80 | 0.21 |
| sparse [clmbr-subset] | 3 | 1.00 | 0.67 | 1.00 | 0.52 | – | 0.95 | 0.75 | 1.21 | 0.00 | 0.26 | 0.09 |
| sparse+ECG [clmbr-subset] | 3 | 1.00 | 0.67 | 1.00 | 0.45 | – | 0.96 | 0.73 | 1.26 | 0.00 | 0.07 | 0.05 |
| hdPS200 [clmbr-subset] | 3 | 1.00 | 0.33 | 1.00 | 1.00 | – | 0.92 | 0.74 | 1.13 | 0.00 | 0.16 | 0.12 |
| hdPS200+ECG [clmbr-subset] | 3 | 1.00 | 0.33 | 1.00 | 0.43 | – | 1.00 | 0.80 | 1.24 | 0.00 | 0.59 | 0.11 |
| CLMBR | 3 | 0.67 | 0.33 | 0.67 | 0.96 | 0.00 | 0.75 | 0.54 | 1.03 | 0.54 | 2.18 | 0.33 |
| sparse+CLMBR | 3 | 1.00 | 0.00 | 1.00 | 0.92 | – | 0.93 | 0.74 | 1.17 | 0.00 | 0.99 | 0.19 |
| sparse+CLMBR+ECG | 3 | 1.00 | 1.00 | 1.00 | 0.88 | – | 0.98 | 0.80 | 1.20 | 0.00 | 0.05 | 0.04 |
| hdPS200+CLMBR | 3 | 1.00 | 0.00 | 1.00 | 0.82 | – | 1.02 | 0.81 | 1.28 | 0.07 | 1.08 | 0.17 |

Paired contrasts after calibration:

| contrast | first | second | trials | closer | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 | signflip |
|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 8 | 5/8 | -0.073 | 0.344 | -1.073 | 0.211 | exact |
| C2 | hdPS200+ECG | hdPS200 | 8 | 4/8 | -0.009 | 0.844 | -0.150 | 0.625 | exact |
| ECGonly | ECGonly | unmatched | 8 | 4/8 | -0.009 | 0.867 | -0.033 | 0.867 | exact |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | 3 | 3/3 | -0.041 | 0.250 | -0.153 | 0.250 | exact |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | 3 | 1/3 | -0.010 | 1.000 | 0.057 | 0.750 | exact |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | 3 | 1/3 | 0.117 | 0.500 | 1.705 | 0.500 | exact |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | 3 | 0/3 | 0.103 | 0.250 | 0.566 | 0.250 | exact |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | 3 | 3/3 | -0.151 | 0.250 | -0.741 | 0.250 | exact |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | 3 | 2/3 | -0.007 | 0.750 | -0.022 | 0.750 | exact |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | 3 | 1/3 | 0.046 | 0.500 | 0.410 | 0.500 | exact |

## Plasmode bias per arm (true conditional HR 0.8; truth = marginal HR in the arm's matched population)

The outcome model excludes the ECG (as at Yale), so ECG arms can reduce plasmode bias only through their correlation with the clinical covariates; C1 reductions near zero are expected by construction.

| trial | scenario | arm | reps | truth | bias | bias_lo | bias_hi | emp_sd | rmse | coverage |
|---|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | base | unmatched | 200 | -0.220 | -0.035 | -0.071 | 0.001 | 0.263 | 0.265 | 0.970 |
| mimic-aristotle | base | sparse | 200 | -0.239 | -0.007 | -0.047 | 0.033 | 0.306 | 0.306 | 0.970 |
| mimic-aristotle | base | sparse+ECG | 200 | -0.214 | -0.034 | -0.075 | 0.006 | 0.302 | 0.303 | 0.985 |
| mimic-aristotle | base | hdPS200 | 200 | -0.209 | 0.063 | 0.019 | 0.110 | 0.338 | 0.343 | 0.980 |
| mimic-aristotle | base | hdPS200+ECG | 200 | -0.235 | 0.069 | 0.023 | 0.118 | 0.346 | 0.352 | 0.955 |
| mimic-aristotle | base | ECGonly | 200 | -0.244 | -0.012 | -0.053 | 0.030 | 0.300 | 0.299 | 0.965 |
| mimic-aristotle | base | clinical | 200 | -0.235 | 0.001 | -0.047 | 0.052 | 0.362 | 0.361 | 0.950 |
| mimic-aristotle | phys_only | unmatched | 200 | -0.227 | 0.101 | 0.069 | 0.133 | 0.240 | 0.259 | 0.940 |
| mimic-aristotle | phys_only | sparse | 200 | -0.238 | 0.126 | 0.084 | 0.168 | 0.308 | 0.332 | 0.950 |
| mimic-aristotle | phys_only | sparse+ECG | 200 | -0.214 | 0.107 | 0.064 | 0.151 | 0.312 | 0.329 | 0.950 |
| mimic-aristotle | phys_only | hdPS200 | 200 | -0.231 | 0.058 | 0.013 | 0.102 | 0.324 | 0.328 | 0.955 |
| mimic-aristotle | phys_only | hdPS200+ECG | 200 | -0.220 | 0.038 | -0.009 | 0.084 | 0.337 | 0.338 | 0.965 |
| mimic-aristotle | phys_only | ECGonly | 200 | -0.232 | 0.116 | 0.077 | 0.153 | 0.281 | 0.303 | 0.960 |
| mimic-aristotle | phys_only | clinical | 200 | -0.252 | 0.025 | -0.019 | 0.068 | 0.319 | 0.319 | 0.980 |
| mimic-comet | base | unmatched | 200 | -0.209 | 0.156 | 0.143 | 0.170 | 0.100 | 0.185 | 0.650 |
| mimic-comet | base | sparse | 200 | -0.219 | 0.055 | 0.036 | 0.073 | 0.136 | 0.146 | 0.925 |
| mimic-comet | base | sparse+ECG | 200 | -0.206 | 0.044 | 0.028 | 0.060 | 0.124 | 0.131 | 0.950 |
| mimic-comet | base | hdPS200 | 200 | -0.201 | -0.012 | -0.031 | 0.009 | 0.148 | 0.148 | 0.940 |
| mimic-comet | base | hdPS200+ECG | 200 | -0.206 | 0.002 | -0.018 | 0.022 | 0.139 | 0.139 | 0.955 |
| mimic-comet | base | ECGonly | 200 | -0.215 | 0.107 | 0.090 | 0.125 | 0.128 | 0.167 | 0.885 |
| mimic-comet | base | clinical | 200 | -0.206 | 0.004 | -0.014 | 0.022 | 0.137 | 0.137 | 0.945 |
| mimic-comet | phys_only | unmatched | 200 | -0.212 | 0.127 | 0.112 | 0.140 | 0.098 | 0.160 | 0.785 |
| mimic-comet | phys_only | sparse | 200 | -0.223 | 0.029 | 0.009 | 0.048 | 0.140 | 0.143 | 0.935 |
| mimic-comet | phys_only | sparse+ECG | 200 | -0.205 | 0.015 | -0.002 | 0.033 | 0.128 | 0.128 | 0.960 |
| mimic-comet | phys_only | hdPS200 | 200 | -0.207 | -0.000 | -0.020 | 0.019 | 0.139 | 0.138 | 0.940 |
| mimic-comet | phys_only | hdPS200+ECG | 200 | -0.218 | 0.023 | 0.004 | 0.042 | 0.135 | 0.137 | 0.955 |
| mimic-comet | phys_only | ECGonly | 200 | -0.210 | 0.087 | 0.069 | 0.105 | 0.129 | 0.155 | 0.895 |
| mimic-comet | phys_only | clinical | 200 | -0.213 | 0.010 | -0.009 | 0.029 | 0.136 | 0.136 | 0.955 |
| mimic-plato | base | unmatched | 200 | -0.197 | -0.246 | -0.265 | -0.227 | 0.137 | 0.281 | 0.610 |
| mimic-plato | base | sparse | 200 | -0.199 | 0.076 | 0.049 | 0.103 | 0.194 | 0.208 | 0.920 |
| mimic-plato | base | sparse+ECG | 200 | -0.203 | 0.013 | -0.012 | 0.038 | 0.179 | 0.179 | 0.955 |
| mimic-plato | base | hdPS200 | 200 | -0.207 | 0.063 | 0.037 | 0.090 | 0.187 | 0.197 | 0.925 |
| mimic-plato | base | hdPS200+ECG | 200 | -0.194 | 0.061 | 0.036 | 0.087 | 0.188 | 0.197 | 0.925 |
| mimic-plato | base | ECGonly | 200 | -0.190 | -0.119 | -0.143 | -0.095 | 0.171 | 0.208 | 0.890 |
| mimic-plato | base | clinical | 200 | -0.201 | 0.023 | -0.003 | 0.046 | 0.176 | 0.177 | 0.965 |
| mimic-plato | phys_only | unmatched | 200 | -0.202 | -0.398 | -0.417 | -0.378 | 0.143 | 0.423 | 0.215 |
| mimic-plato | phys_only | sparse | 200 | -0.209 | -0.082 | -0.108 | -0.057 | 0.187 | 0.204 | 0.925 |
| mimic-plato | phys_only | sparse+ECG | 200 | -0.209 | -0.114 | -0.138 | -0.089 | 0.174 | 0.207 | 0.955 |
| mimic-plato | phys_only | hdPS200 | 200 | -0.200 | -0.079 | -0.105 | -0.051 | 0.195 | 0.210 | 0.945 |
| mimic-plato | phys_only | hdPS200+ECG | 200 | -0.198 | -0.056 | -0.086 | -0.027 | 0.213 | 0.220 | 0.925 |
| mimic-plato | phys_only | ECGonly | 200 | -0.208 | -0.230 | -0.256 | -0.204 | 0.187 | 0.296 | 0.760 |
| mimic-plato | phys_only | clinical | 200 | -0.197 | 0.019 | -0.007 | 0.047 | 0.194 | 0.194 | 0.955 |
| mimic-rocket_af | base | unmatched | 200 | -0.218 | -0.046 | -0.091 | -0.000 | 0.322 | 0.324 | 0.975 |
| mimic-rocket_af | base | sparse | 200 | -0.221 | 0.000 | -0.061 | 0.063 | 0.454 | 0.453 | 0.945 |
| mimic-rocket_af | base | sparse+ECG | 200 | -0.230 | 0.006 | -0.048 | 0.063 | 0.397 | 0.396 | 0.970 |
| mimic-rocket_af | base | hdPS200 | 200 | -0.185 | -0.008 | -0.064 | 0.047 | 0.416 | 0.415 | 0.975 |
| mimic-rocket_af | base | hdPS200+ECG | 200 | -0.250 | 0.071 | 0.009 | 0.129 | 0.426 | 0.431 | 0.970 |
| mimic-rocket_af | base | ECGonly | 200 | -0.233 | -0.012 | -0.070 | 0.045 | 0.417 | 0.416 | 0.970 |
| mimic-rocket_af | base | clinical | 200 | -0.228 | 0.011 | -0.051 | 0.075 | 0.445 | 0.444 | 0.945 |
| mimic-rocket_af | phys_only | unmatched | 200 | -0.218 | 0.020 | -0.023 | 0.064 | 0.333 | 0.333 | 0.925 |
| mimic-rocket_af | phys_only | sparse | 200 | -0.244 | 0.079 | 0.022 | 0.137 | 0.434 | 0.440 | 0.935 |
| mimic-rocket_af | phys_only | sparse+ECG | 200 | -0.204 | 0.048 | -0.011 | 0.107 | 0.430 | 0.431 | 0.950 |
| mimic-rocket_af | phys_only | hdPS200 | 200 | -0.202 | -0.013 | -0.075 | 0.052 | 0.448 | 0.447 | 0.960 |
| mimic-rocket_af | phys_only | hdPS200+ECG | 200 | -0.216 | -0.027 | -0.082 | 0.035 | 0.428 | 0.428 | 0.960 |
| mimic-rocket_af | phys_only | ECGonly | 200 | -0.236 | 0.055 | -0.000 | 0.111 | 0.412 | 0.415 | 0.935 |
| mimic-rocket_af | phys_only | clinical | 200 | -0.229 | -0.022 | -0.082 | 0.039 | 0.450 | 0.449 | 0.920 |
| mimic-transform_hf | base | unmatched | 200 | -0.210 | 0.027 | 0.016 | 0.038 | 0.080 | 0.084 | 0.965 |
| mimic-transform_hf | base | sparse | 200 | -0.209 | 0.082 | 0.069 | 0.095 | 0.094 | 0.124 | 0.900 |
| mimic-transform_hf | base | sparse+ECG | 200 | -0.209 | 0.048 | 0.035 | 0.061 | 0.096 | 0.107 | 0.960 |
| mimic-transform_hf | base | hdPS200 | 200 | -0.200 | 0.004 | -0.012 | 0.019 | 0.108 | 0.108 | 0.975 |
| mimic-transform_hf | base | hdPS200+ECG | 200 | -0.212 | -0.001 | -0.016 | 0.014 | 0.107 | 0.107 | 0.975 |
| mimic-transform_hf | base | ECGonly | 200 | -0.219 | 0.051 | 0.039 | 0.065 | 0.097 | 0.109 | 0.945 |
| mimic-transform_hf | base | clinical | 200 | -0.212 | -0.011 | -0.025 | 0.004 | 0.107 | 0.108 | 0.960 |
| mimic-transform_hf | phys_only | unmatched | 200 | -0.208 | -0.007 | -0.019 | 0.004 | 0.086 | 0.086 | 0.965 |
| mimic-transform_hf | phys_only | sparse | 200 | -0.208 | 0.053 | 0.038 | 0.067 | 0.107 | 0.119 | 0.930 |
| mimic-transform_hf | phys_only | sparse+ECG | 200 | -0.212 | 0.024 | 0.010 | 0.039 | 0.103 | 0.106 | 0.960 |
| mimic-transform_hf | phys_only | hdPS200 | 200 | -0.206 | 0.015 | -0.000 | 0.030 | 0.106 | 0.107 | 0.960 |
| mimic-transform_hf | phys_only | hdPS200+ECG | 200 | -0.211 | 0.006 | -0.009 | 0.021 | 0.107 | 0.107 | 0.975 |
| mimic-transform_hf | phys_only | ECGonly | 200 | -0.218 | 0.011 | -0.004 | 0.026 | 0.109 | 0.110 | 0.950 |
| mimic-transform_hf | phys_only | clinical | 200 | -0.217 | -0.008 | -0.023 | 0.007 | 0.108 | 0.108 | 0.980 |
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
| mimic-aristotle | base | C1 | -0.007 | -0.034 | -0.028 | -0.049 | 0.026 | -410.758 |
| mimic-aristotle | base | C2 | 0.063 | 0.069 | -0.006 | -0.037 | 0.024 | -9.796 |
| mimic-aristotle | base | ECGonly | -0.035 | -0.012 | 0.023 | -0.024 | 0.039 | 64.818 |
| mimic-aristotle | phys_only | C1 | 0.126 | 0.107 | 0.019 | -0.009 | 0.047 | 15.326 |
| mimic-aristotle | phys_only | C2 | 0.058 | 0.038 | 0.019 | -0.010 | 0.048 | 33.673 |
| mimic-aristotle | phys_only | ECGonly | 0.101 | 0.116 | -0.015 | -0.037 | 0.006 | -15.058 |
| mimic-comet | base | C1 | 0.055 | 0.044 | 0.010 | -0.006 | 0.027 | 19.153 |
| mimic-comet | base | C2 | -0.012 | 0.002 | 0.010 | -0.017 | 0.024 | 86.313 |
| mimic-comet | base | ECGonly | 0.156 | 0.107 | 0.049 | 0.037 | 0.060 | 31.179 |
| mimic-comet | phys_only | C1 | 0.029 | 0.015 | 0.013 | -0.004 | 0.030 | 46.495 |
| mimic-comet | phys_only | C2 | -0.000 | 0.023 | -0.022 | -0.034 | 0.012 | -14450.722 |
| mimic-comet | phys_only | ECGonly | 0.127 | 0.087 | 0.040 | 0.027 | 0.051 | 31.379 |
| mimic-plato | base | C1 | 0.076 | 0.013 | 0.063 | 0.038 | 0.081 | 82.918 |
| mimic-plato | base | C2 | 0.063 | 0.061 | 0.002 | -0.013 | 0.016 | 3.005 |
| mimic-plato | base | ECGonly | -0.246 | -0.119 | 0.127 | 0.112 | 0.141 | 51.572 |
| mimic-plato | phys_only | C1 | -0.082 | -0.114 | -0.032 | -0.051 | -0.013 | -38.673 |
| mimic-plato | phys_only | C2 | -0.079 | -0.056 | 0.022 | 0.004 | 0.041 | 28.332 |
| mimic-plato | phys_only | ECGonly | -0.398 | -0.230 | 0.168 | 0.153 | 0.184 | 42.294 |
| mimic-rocket_af | base | C1 | 0.000 | 0.006 | -0.006 | -0.038 | 0.044 | -6073.606 |
| mimic-rocket_af | base | C2 | -0.008 | 0.071 | -0.063 | -0.103 | 0.046 | -835.011 |
| mimic-rocket_af | base | ECGonly | -0.046 | -0.012 | 0.034 | -0.033 | 0.061 | 73.168 |
| mimic-rocket_af | phys_only | C1 | 0.079 | 0.048 | 0.031 | -0.018 | 0.075 | 39.342 |
| mimic-rocket_af | phys_only | C2 | -0.013 | -0.027 | -0.014 | -0.044 | 0.033 | -107.190 |
| mimic-rocket_af | phys_only | ECGonly | 0.020 | 0.055 | -0.035 | -0.066 | 0.012 | -173.083 |
| mimic-transform_hf | base | C1 | 0.082 | 0.048 | 0.034 | 0.022 | 0.045 | 41.335 |
| mimic-transform_hf | base | C2 | 0.004 | -0.001 | 0.003 | -0.010 | 0.011 | 77.311 |
| mimic-transform_hf | base | ECGonly | 0.027 | 0.051 | -0.025 | -0.033 | -0.017 | -92.707 |
| mimic-transform_hf | phys_only | C1 | 0.053 | 0.024 | 0.028 | 0.016 | 0.040 | 53.593 |
| mimic-transform_hf | phys_only | C2 | 0.015 | 0.006 | 0.009 | -0.006 | 0.019 | 62.303 |
| mimic-transform_hf | phys_only | ECGonly | -0.007 | 0.011 | -0.004 | -0.023 | 0.016 | -49.723 |
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
| ukb-ontarget | base | sparse+CLMBR+ECG vs sparse+CLMBR | -0.010 | -0.007 | 0.004 | -0.011 | 0.015 | 35.093 |
| ukb-ontarget | base | sparse+CLMBR+ECG vs sparse+ECG [sub] | -0.022 | -0.007 | 0.015 | -0.010 | 0.025 | 69.657 |
| ukb-ontarget | base | hdPS200+CLMBR vs hdPS200 [sub] | 0.004 | 0.019 | -0.014 | -0.025 | 0.014 | -327.208 |
| ukb-ontarget | phys_only | C1 | -0.006 | -0.002 | 0.004 | -0.013 | 0.014 | 62.183 |
| ukb-ontarget | phys_only | C2 | 0.007 | 0.013 | -0.006 | -0.017 | 0.010 | -96.191 |
| ukb-ontarget | phys_only | ECGonly | -0.023 | -0.002 | 0.021 | -0.016 | 0.027 | 92.353 |
| ukb-ontarget | phys_only | C1 [sub] | -0.003 | -0.016 | -0.012 | -0.024 | 0.013 | -370.968 |
| ukb-ontarget | phys_only | C2 [sub] | -0.002 | -0.024 | -0.022 | -0.032 | 0.017 | -1120.502 |
| ukb-ontarget | phys_only | CLMBR vs unmatched [sub] | -0.015 | -0.029 | -0.015 | -0.026 | -0.000 | -100.881 |
| ukb-ontarget | phys_only | sparse+CLMBR vs sparse [sub] | -0.003 | 0.010 | -0.007 | -0.023 | 0.018 | -212.919 |
| ukb-ontarget | phys_only | sparse+CLMBR+ECG vs sparse+CLMBR | 0.010 | 0.000 | 0.010 | -0.016 | 0.021 | 96.499 |
| ukb-ontarget | phys_only | sparse+CLMBR+ECG vs sparse+ECG [sub] | -0.016 | 0.000 | 0.015 | -0.017 | 0.026 | 97.674 |
| ukb-ontarget | phys_only | hdPS200+CLMBR vs hdPS200 [sub] | -0.002 | -0.006 | -0.004 | -0.016 | 0.013 | -199.629 |
| pooled (8; mean |bias|) | base | C1 | 0.040 | 0.026 | 0.013 | 0.005 | 0.025 | – |
| pooled (8; mean |bias|) | base | C2 | 0.033 | 0.038 | -0.005 | -0.015 | 0.009 | – |
| pooled (8; mean |bias|) | base | ECGonly | 0.117 | 0.080 | 0.037 | 0.026 | 0.042 | – |
| pooled (3; mean |bias|) | base | C1 [sub] | 0.029 | 0.037 | -0.008 | -0.020 | 0.008 | – |
| pooled (3; mean |bias|) | base | C2 [sub] | 0.026 | 0.039 | -0.013 | -0.025 | 0.008 | – |
| pooled (3; mean |bias|) | base | CLMBR vs unmatched [sub] | 0.150 | 0.034 | 0.116 | 0.102 | 0.124 | – |
| pooled (3; mean |bias|) | base | sparse+CLMBR vs sparse [sub] | 0.029 | 0.024 | 0.005 | -0.010 | 0.029 | – |
| pooled (3; mean |bias|) | base | sparse+CLMBR+ECG vs sparse+CLMBR | 0.024 | 0.018 | 0.006 | -0.018 | 0.017 | – |
| pooled (3; mean |bias|) | base | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.037 | 0.018 | 0.018 | -0.001 | 0.029 | – |
| pooled (3; mean |bias|) | base | hdPS200+CLMBR vs hdPS200 [sub] | 0.026 | 0.034 | -0.008 | -0.018 | 0.016 | – |
| pooled (8; mean |bias|) | phys_only | C1 | 0.050 | 0.041 | 0.009 | -0.003 | 0.018 | – |
| pooled (8; mean |bias|) | phys_only | C2 | 0.027 | 0.027 | -0.000 | -0.008 | 0.011 | – |
| pooled (8; mean |bias|) | phys_only | ECGonly | 0.107 | 0.079 | 0.028 | 0.020 | 0.036 | – |
| pooled (3; mean |bias|) | phys_only | C1 [sub] | 0.019 | 0.027 | -0.008 | -0.019 | 0.015 | – |
| pooled (3; mean |bias|) | phys_only | C2 [sub] | 0.019 | 0.020 | -0.001 | -0.023 | 0.019 | – |
| pooled (3; mean |bias|) | phys_only | CLMBR vs unmatched [sub] | 0.071 | 0.019 | 0.053 | 0.034 | 0.060 | – |
| pooled (3; mean |bias|) | phys_only | sparse+CLMBR vs sparse [sub] | 0.019 | 0.035 | -0.016 | -0.029 | 0.007 | – |
| pooled (3; mean |bias|) | phys_only | sparse+CLMBR+ECG vs sparse+CLMBR | 0.035 | 0.024 | 0.011 | -0.006 | 0.024 | – |
| pooled (3; mean |bias|) | phys_only | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.027 | 0.024 | 0.003 | -0.015 | 0.016 | – |
| pooled (3; mean |bias|) | phys_only | hdPS200+CLMBR vs hdPS200 [sub] | 0.019 | 0.017 | 0.002 | -0.021 | 0.021 | – |

## Balance capture % (labs_vitals, full cohort; observed values; blank where unmatched excess < 0.02)

| trial | k | unmatched_excess | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | 8 | 0.225 | 8.4 | 18.5 | 66.5 | 65.5 | 19.5 | 103.5 |
| mimic-comet | 8 | 0.137 | 27.3 | 35.2 | 58.8 | 54.3 | 20.2 | 103.1 |
| mimic-plato | 8 | 0.124 | 57.0 | 57.2 | 41.7 | 65.2 | 68.2 | 102.1 |
| mimic-rocket_af | 8 | 0.240 | 12.4 | 26.5 | 88.8 | 83.9 | 9.6 | 108.6 |
| mimic-transform_hf | 8 | 0.100 | 4.2 | 20.7 | 67.4 | 59.4 | 17.6 | 117.2 |
| ukb-allhat | 9 | 0.054 | -25.8 | 24.5 | 61.3 | 78.1 | 61.3 | 133.2 |
| ukb-ascot | 9 | 0.128 | 52.3 | 68.2 | 86.4 | 95.0 | 19.0 | 111.6 |
| ukb-ontarget | 9 | 0.032 | 68.4 | 56.1 | 26.3 | 46.4 | 21.9 | 119.8 |

Median capture % across trials: sparse 20, sparse+ECG 31, hdPS200 64, hdPS200+ECG 65, ECGonly 20, clinical 110

## Balance capture % (phys, full cohort; observed values; blank where unmatched excess < 0.02)

| trial | k | unmatched_excess | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | 8 | 0.225 | 8.4 | 18.5 | 66.5 | 65.5 | 19.5 | 103.5 |
| mimic-comet | 8 | 0.137 | 27.3 | 35.2 | 58.8 | 54.3 | 20.2 | 103.1 |
| mimic-plato | 8 | 0.124 | 57.0 | 57.2 | 41.7 | 65.2 | 68.2 | 102.1 |
| mimic-rocket_af | 8 | 0.240 | 12.4 | 26.5 | 88.8 | 83.9 | 9.6 | 108.6 |
| mimic-transform_hf | 8 | 0.100 | 4.2 | 20.7 | 67.4 | 59.4 | 17.6 | 117.2 |
| ukb-allhat | 5 | 0.078 | -5.9 | 43.5 | 48.1 | 76.6 | 61.6 | 117.9 |
| ukb-ascot | 5 | 0.148 | 44.6 | 78.2 | 89.1 | 97.1 | 23.8 | 106.0 |
| ukb-ontarget | 5 | 0.036 | 50.1 | 29.0 | -5.8 | 38.8 | 30.5 | 120.4 |

Median capture % across trials: sparse 20, sparse+ECG 32, hdPS200 63, hdPS200+ECG 65, ECGonly 22, clinical 107

## Balance capture % (labs_vitals, CLMBR subset; observed values; blank where unmatched excess < 0.02)

| trial | k | unmatched_excess | sparse [clmbr-subset] | sparse+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | hdPS200+ECG [clmbr-subset] | CLMBR | sparse+CLMBR | sparse+CLMBR+ECG | hdPS200+CLMBR |
|---|---|---|---|---|---|---|---|---|---|---|
| ukb-allhat | 9 | 0.054 | 11.5 | 51.6 | 60.0 | 96.1 | -15.1 | -2.6 | 54.6 | 69.6 |
| ukb-ascot | 9 | 0.135 | 48.1 | 79.1 | 94.1 | 80.2 | 41.6 | 63.0 | 68.9 | 96.9 |
| ukb-ontarget | 9 | 0.025 | 59.9 | 81.4 | 61.0 | 94.3 | 26.9 | 49.5 | 18.0 | 57.8 |

Median capture % across trials: sparse [clmbr-subset] 48, sparse+ECG [clmbr-subset] 79, hdPS200 [clmbr-subset] 61, hdPS200+ECG [clmbr-subset] 94, CLMBR 27, sparse+CLMBR 50, sparse+CLMBR+ECG 55, hdPS200+CLMBR 70


### summary_sensitivity

# v1.5 sensitivity analyses (post-audit; never pooled into the main analyses)

MIMIC: pre-audit specification (index-admission diagnoses in baseline/panel; no 28-day new-event rule) vs corrected primary (earlier-admission diagnoses; 28-day rule). UKB: main cohorts vs the trials' own eligibility criteria (elig), CV-death composites censored 2020-12-31 (cvd) and both (elig-cvd). The UKB ECG is an on-treatment covariate (recorded at the exposure-defining visit).

## HRs by version — mimic (HR (95% CI) [pairs])

| trial | arm | mimic pre-audit | mimic corrected |
|---|---|---|---|
| mimic-aristotle | unmatched | 0.50 (0.30–0.83) | 0.52 (0.30–0.89) |
| mimic-aristotle | sparse | 0.52 (0.29–0.93) [1466] | 0.49 (0.26–0.89) [1477] |
| mimic-aristotle | sparse+ECG | 0.62 (0.33–1.17) [1439] | 0.55 (0.29–1.05) [1478] |
| mimic-aristotle | hdPS200 | 0.39 (0.20–0.75) [1343] | 0.51 (0.25–1.03) [1264] |
| mimic-aristotle | hdPS200+ECG | 0.42 (0.21–0.83) [1289] | 0.58 (0.31–1.11) [1263] |
| mimic-aristotle | ECGonly | 0.49 (0.28–0.86) [1553] | 0.49 (0.27–0.89) [1553] |
| mimic-aristotle | clinical | 0.44 (0.24–0.82) [1312] | 0.37 (0.19–0.74) [1327] |
| mimic-comet | unmatched | 1.41 (1.17–1.69) | 1.41 (1.17–1.69) |
| mimic-comet | sparse | 1.32 (1.06–1.64) [743] | 1.35 (1.09–1.67) [738] |
| mimic-comet | sparse+ECG | 1.06 (0.84–1.35) [742] | 1.24 (0.98–1.56) [740] |
| mimic-comet | hdPS200 | 1.12 (0.89–1.42) [716] | 1.22 (0.98–1.53) [709] |
| mimic-comet | hdPS200+ECG | 1.05 (0.83–1.33) [718] | 1.04 (0.81–1.33) [708] |
| mimic-comet | ECGonly | 1.37 (1.09–1.72) [741] | 1.37 (1.09–1.72) [741] |
| mimic-comet | clinical | 1.24 (0.99–1.55) [738] | 1.17 (0.93–1.48) [739] |
| mimic-plato | unmatched | 0.71 (0.57–0.89) | 0.59 (0.45–0.76) |
| mimic-plato | sparse | 0.93 (0.69–1.25) [411] | 0.77 (0.56–1.06) [441] |
| mimic-plato | sparse+ECG | 0.90 (0.68–1.21) [411] | 0.71 (0.52–0.96) [432] |
| mimic-plato | hdPS200 | 0.99 (0.72–1.38) [354] | 0.92 (0.66–1.28) [426] |
| mimic-plato | hdPS200+ECG | 0.87 (0.64–1.19) [352] | 0.89 (0.61–1.29) [399] |
| mimic-plato | ECGonly | 0.89 (0.67–1.18) [441] | 0.78 (0.57–1.08) [441] |
| mimic-plato | clinical | 0.96 (0.71–1.29) [394] | 0.81 (0.57–1.16) [422] |
| mimic-rocket_af | unmatched | 0.56 (0.30–1.03) | 0.65 (0.35–1.21) |
| mimic-rocket_af | sparse | 0.51 (0.25–1.07) [902] | 0.44 (0.22–0.88) [902] |
| mimic-rocket_af | sparse+ECG | 0.56 (0.27–1.19) [901] | 0.89 (0.39–2.02) [900] |
| mimic-rocket_af | hdPS200 | 0.77 (0.36–1.66) [901] | 0.67 (0.31–1.45) [892] |
| mimic-rocket_af | hdPS200+ECG | 0.83 (0.37–1.87) [900] | 0.90 (0.39–2.04) [896] |
| mimic-rocket_af | ECGonly | 0.56 (0.26–1.17) [905] | 0.70 (0.32–1.54) [905] |
| mimic-rocket_af | clinical | 0.57 (0.27–1.20) [898] | 0.54 (0.26–1.11) [901] |
| mimic-transform_hf | unmatched | 1.24 (1.07–1.43) | 1.24 (1.07–1.43) |
| mimic-transform_hf | sparse | 1.20 (1.01–1.43) [940] | 1.10 (0.93–1.32) [940] |
| mimic-transform_hf | sparse+ECG | 1.06 (0.89–1.26) [940] | 1.23 (1.02–1.48) [940] |
| mimic-transform_hf | hdPS200 | 0.99 (0.82–1.20) [808] | 1.21 (0.99–1.48) [808] |
| mimic-transform_hf | hdPS200+ECG | 1.08 (0.89–1.32) [806] | 1.13 (0.93–1.37) [801] |
| mimic-transform_hf | ECGonly | 1.08 (0.91–1.29) [940] | 1.08 (0.91–1.29) [940] |
| mimic-transform_hf | clinical | 1.25 (1.03–1.51) [903] | 1.23 (1.02–1.48) [904] |

## Contrasts (mean Δ|log HR − RCT|, negative = first arm closer; exact sign-flip, descriptive) and panel — mimic

| version | contrast | trials | closer | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 |
|---|---|---|---|---|---|---|---|
| mimic pre-audit | C1 | 5 | 4/5 | -0.080 | 0.188 | -0.744 | 0.188 |
| mimic pre-audit | C2 | 5 | 3/5 | -0.036 | 0.375 | -0.218 | 0.500 |
| mimic pre-audit | ECGonly | 5 | 3/5 | -0.051 | 0.250 | -1.390 | 0.062 |
| mimic pre-audit | panel: unmatched | 5 | est.agree 0.00; phi 2.95 | 0.287 | – | – | – |
| mimic pre-audit | panel: sparse | 5 | est.agree 0.20; phi 1.43 | 0.264 | – | – | – |
| mimic pre-audit | panel: sparse+ECG | 5 | est.agree 0.40; phi 0.71 | 0.184 | – | – | – |
| mimic pre-audit | panel: hdPS200 | 5 | est.agree 0.60; phi 1.31 | 0.222 | – | – | – |
| mimic pre-audit | panel: hdPS200+ECG | 5 | est.agree 0.60; phi 1.04 | 0.186 | – | – | – |
| mimic pre-audit | panel: ECGonly | 5 | est.agree 0.40; phi 1.26 | 0.236 | – | – | – |
| mimic pre-audit | panel: clinical | 5 | est.agree 0.20; phi 1.73 | 0.275 | – | – | – |
| mimic corrected | C1 | 5 | 3/5 | -0.142 | 0.438 | -0.536 | 0.688 |
| mimic corrected | C2 | 5 | 4/5 | -0.072 | 0.312 | -0.270 | 0.500 |
| mimic corrected | ECGonly | 5 | 4/5 | -0.095 | 0.188 | -2.209 | 0.125 |
| mimic corrected | panel: unmatched | 5 | est.agree 0.00; phi 3.71 | 0.286 | – | – | – |
| mimic corrected | panel: sparse | 5 | est.agree 0.60; phi 1.85 | 0.292 | – | – | – |
| mimic corrected | panel: sparse+ECG | 5 | est.agree 0.40; phi 1.14 | 0.150 | – | – | – |
| mimic corrected | panel: hdPS200 | 5 | est.agree 0.20; phi 0.86 | 0.198 | – | – | – |
| mimic corrected | panel: hdPS200+ECG | 5 | est.agree 0.60; phi 0.67 | 0.126 | – | – | – |
| mimic corrected | panel: ECGonly | 5 | est.agree 0.40; phi 0.97 | 0.191 | – | – | – |
| mimic corrected | panel: clinical | 5 | est.agree 0.40; phi 2.11 | 0.295 | – | – | – |

## HRs by version — ukb (HR (95% CI) [pairs])

| trial | arm | ukb main | ukb elig | ukb cvd | ukb elig-cvd |
|---|---|---|---|---|---|
| ukb-allhat | unmatched | 0.89 (0.62–1.28) | 0.96 (0.67–1.40) | 0.63 (0.36–1.09) | 0.74 (0.42–1.30) |
| ukb-allhat | sparse | 0.79 (0.51–1.23) [1374] | 0.91 (0.59–1.41) [1328] | 0.58 (0.29–1.14) [1127] | 0.61 (0.30–1.22) [1066] |
| ukb-allhat | sparse+ECG | 0.88 (0.57–1.37) [1345] | 0.94 (0.61–1.45) [1303] | 0.68 (0.35–1.33) [1084] | 0.82 (0.43–1.59) [1048] |
| ukb-allhat | hdPS200 | 0.67 (0.42–1.08) [1280] | 0.67 (0.41–1.11) [1228] | 0.41 (0.19–0.89) [1026] | 0.70 (0.33–1.48) [980] |
| ukb-allhat | hdPS200+ECG | 0.72 (0.45–1.17) [1255] | 0.84 (0.53–1.34) [1211] | 0.69 (0.35–1.37) [980] | 0.88 (0.44–1.76) [932] |
| ukb-allhat | ECGonly | 0.88 (0.56–1.38) [1372] | 1.17 (0.75–1.82) [1324] | 0.80 (0.43–1.50) [1120] | 0.71 (0.35–1.44) [1077] |
| ukb-allhat | clinical | 0.76 (0.47–1.21) [1279] | 0.70 (0.43–1.15) [1240] | 0.65 (0.31–1.34) [1046] | 0.48 (0.21–1.11) [1002] |
| ukb-ascot | unmatched | 0.52 (0.39–0.69) | 0.64 (0.43–0.94) | 0.32 (0.20–0.51) | 0.47 (0.25–0.88) |
| ukb-ascot | sparse | 0.77 (0.48–1.22) [978] | 0.69 (0.38–1.24) [739] | 0.44 (0.20–0.96) [744] | 0.48 (0.17–1.40) [586] |
| ukb-ascot | sparse+ECG | 0.68 (0.44–1.06) [1007] | 0.85 (0.49–1.48) [750] | 0.64 (0.31–1.35) [766] | 0.67 (0.29–1.59) [588] |
| ukb-ascot | hdPS200 | 0.73 (0.44–1.21) [995] | 0.72 (0.40–1.30) [710] | 0.52 (0.25–1.08) [753] | 0.50 (0.17–1.50) [551] |
| ukb-ascot | hdPS200+ECG | 0.74 (0.46–1.19) [964] | 0.49 (0.25–0.96) [659] | 0.53 (0.23–1.20) [699] | 0.49 (0.18–1.32) [512] |
| ukb-ascot | ECGonly | 0.60 (0.43–0.84) [1837] | 0.71 (0.43–1.18) [968] | 0.30 (0.16–0.55) [1388] | 0.58 (0.26–1.31) [759] |
| ukb-ascot | clinical | 0.71 (0.46–1.08) [1032] | 0.75 (0.41–1.36) [763] | 0.63 (0.30–1.30) [770] | 0.36 (0.11–1.14) [596] |
| ukb-ontarget | unmatched | 1.01 (0.81–1.25) | 1.21 (0.90–1.63) | 1.22 (0.91–1.63) | 1.56 (1.07–2.28) |
| ukb-ontarget | sparse | 1.07 (0.83–1.37) [2567] | 1.23 (0.86–1.76) [723] | 1.11 (0.79–1.56) [1950] | 1.46 (0.92–2.32) [545] |
| ukb-ontarget | sparse+ECG | 1.00 (0.78–1.29) [2561] | 1.03 (0.74–1.44) [719] | 1.27 (0.90–1.79) [1947] | 1.48 (0.93–2.36) [543] |
| ukb-ontarget | hdPS200 | 0.96 (0.74–1.23) [2486] | 1.30 (0.88–1.93) [662] | 1.16 (0.82–1.65) [1849] | 1.34 (0.83–2.17) [476] |
| ukb-ontarget | hdPS200+ECG | 0.95 (0.74–1.22) [2477] | 1.23 (0.84–1.82) [643] | 1.18 (0.83–1.67) [1852] | 1.30 (0.79–2.13) [470] |
| ukb-ontarget | ECGonly | 1.06 (0.82–1.36) [2567] | 1.30 (0.90–1.87) [731] | 1.25 (0.89–1.75) [1951] | 1.54 (0.97–2.45) [555] |
| ukb-ontarget | clinical | 0.97 (0.76–1.25) [2563] | 1.21 (0.84–1.75) [725] | 1.25 (0.88–1.76) [1945] | 1.42 (0.89–2.25) [545] |

## Contrasts (mean Δ|log HR − RCT|, negative = first arm closer; exact sign-flip, descriptive) and panel — ukb

| version | contrast | trials | closer | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 |
|---|---|---|---|---|---|---|---|
| ukb main | C1 | 3 | 2/3 | -0.016 | 1.000 | 0.036 | 1.000 |
| ukb main | C2 | 3 | 2/3 | -0.026 | 0.500 | -0.258 | 0.750 |
| ukb main | ECGonly | 3 | 1/3 | -0.028 | 1.000 | -2.219 | 0.750 |
| ukb main | C1 [sub] | 3 | 2/3 | -0.040 | 0.500 | -0.211 | 0.750 |
| ukb main | C2 [sub] | 3 | 2/3 | -0.040 | 0.750 | -0.145 | 1.000 |
| ukb main | CLMBR vs unmatched [sub] | 3 | 0/3 | 0.099 | 0.250 | -1.026 | 1.000 |
| ukb main | sparse+CLMBR vs sparse [sub] | 3 | 2/3 | 0.068 | 1.000 | 0.600 | 1.000 |
| ukb main | sparse+CLMBR+ECG vs sparse+CLMBR | 3 | 3/3 | -0.133 | 0.250 | -0.997 | 0.250 |
| ukb main | sparse+CLMBR+ECG vs sparse+ECG [sub] | 3 | 2/3 | -0.025 | 0.500 | -0.186 | 0.500 |
| ukb main | hdPS200+CLMBR vs hdPS200 [sub] | 3 | 1/3 | 0.026 | 0.750 | 0.166 | 0.750 |
| ukb main | panel: unmatched | 3 | est.agree 0.33; phi 3.92 | 0.215 | – | – | – |
| ukb main | panel: sparse | 3 | est.agree 0.33; phi 0.68 | 0.145 | – | – | – |
| ukb main | panel: sparse+ECG | 3 | est.agree 0.33; phi 0.51 | 0.129 | – | – | – |
| ukb main | panel: hdPS200 | 3 | est.agree 0.33; phi 0.69 | 0.212 | – | – | – |
| ukb main | panel: hdPS200+ECG | 3 | est.agree 0.33; phi 0.41 | 0.186 | – | – | – |
| ukb main | panel: ECGonly | 3 | est.agree 0.33; phi 2.00 | 0.188 | – | – | – |
| ukb main | panel: clinical | 3 | est.agree 0.33; phi 0.51 | 0.179 | – | – | – |
| ukb elig | C1 | 3 | 3/3 | -0.142 | 0.250 | -0.627 | 0.250 |
| ukb elig | C2 | 3 | 2/3 | 0.039 | 1.000 | 0.088 | 1.000 |
| ukb elig | ECGonly | 3 | 1/3 | 0.040 | 0.750 | -0.302 | 1.000 |
| ukb elig | C1 [sub] | 3 | 1/3 | 0.050 | 0.750 | 0.613 | 0.750 |
| ukb elig | C2 [sub] | 3 | 0/3 | 0.132 | 0.250 | 1.294 | 0.250 |
| ukb elig | CLMBR vs unmatched [sub] | 3 | 2/3 | -0.031 | 1.000 | -0.948 | 0.500 |
| ukb elig | sparse+CLMBR vs sparse [sub] | 3 | 2/3 | 0.006 | 1.000 | 0.132 | 1.000 |
| ukb elig | sparse+CLMBR+ECG vs sparse+CLMBR | 3 | 2/3 | -0.023 | 0.750 | 0.031 | 1.000 |
| ukb elig | sparse+CLMBR+ECG vs sparse+ECG [sub] | 3 | 3/3 | -0.066 | 0.250 | -0.450 | 0.250 |
| ukb elig | hdPS200+CLMBR vs hdPS200 [sub] | 3 | 0/3 | 0.112 | 0.250 | 0.748 | 0.250 |
| ukb elig | panel: unmatched | 3 | est.agree 0.33; phi 2.01 | 0.179 | – | – | – |
| ukb elig | panel: sparse | 3 | est.agree 0.33; phi 0.97 | 0.180 | – | – | – |
| ukb elig | panel: sparse+ECG | 3 | est.agree 1.00; phi 0.04 | 0.039 | – | – | – |
| ukb elig | panel: hdPS200 | 3 | est.agree 0.00; phi 2.06 | 0.283 | – | – | – |
| ukb elig | panel: hdPS200+ECG | 3 | est.agree 0.00; phi 2.16 | 0.322 | – | – | – |
| ukb elig | panel: ECGonly | 3 | est.agree 0.00; phi 1.15 | 0.219 | – | – | – |
| ukb elig | panel: clinical | 3 | est.agree 0.00; phi 1.44 | 0.233 | – | – | – |
| ukb cvd | C1 | 3 | 2/3 | -0.140 | 0.500 | -0.762 | 0.750 |
| ukb cvd | C2 | 3 | 2/3 | -0.180 | 0.500 | -1.419 | 0.500 |
| ukb cvd | ECGonly | 3 | 1/3 | -0.047 | 1.000 | -2.412 | 0.250 |
| ukb cvd | C1 [sub] | 3 | 1/3 | 0.083 | 0.750 | 0.924 | 0.500 |
| ukb cvd | C2 [sub] | 3 | 2/3 | -0.032 | 1.000 | -0.200 | 1.000 |
| ukb cvd | CLMBR vs unmatched [sub] | 3 | 1/3 | 0.005 | 1.000 | -2.583 | 0.250 |
| ukb cvd | sparse+CLMBR vs sparse [sub] | 3 | 1/3 | 0.093 | 0.750 | 0.747 | 0.750 |
| ukb cvd | sparse+CLMBR+ECG vs sparse+CLMBR | 3 | 1/3 | -0.143 | 1.000 | -0.850 | 0.750 |
| ukb cvd | sparse+CLMBR+ECG vs sparse+ECG [sub] | 3 | 1/3 | -0.132 | 1.000 | -1.027 | 1.000 |
| ukb cvd | hdPS200+CLMBR vs hdPS200 [sub] | 3 | 3/3 | -0.283 | 0.250 | -1.640 | 0.250 |
| ukb cvd | panel: unmatched | 3 | est.agree 0.00; phi 9.20 | 0.552 | – | – | – |
| ukb cvd | panel: sparse | 3 | est.agree 0.00; phi 2.54 | 0.448 | – | – | – |
| ukb cvd | panel: sparse+ECG | 3 | est.agree 0.00; phi 1.71 | 0.308 | – | – | – |
| ukb cvd | panel: hdPS200 | 3 | est.agree 0.00; phi 3.45 | 0.523 | – | – | – |
| ukb cvd | panel: hdPS200+ECG | 3 | est.agree 0.00; phi 1.62 | 0.344 | – | – | – |
| ukb cvd | panel: ECGonly | 3 | est.agree 0.00; phi 6.69 | 0.505 | – | – | – |
| ukb cvd | panel: clinical | 3 | est.agree 0.00; phi 1.75 | 0.328 | – | – | – |
| ukb elig-cvd | C1 | 3 | 2/3 | -0.207 | 0.500 | -0.753 | 0.500 |
| ukb elig-cvd | C2 | 3 | 2/3 | -0.078 | 0.500 | -0.223 | 0.500 |
| ukb elig-cvd | ECGonly | 3 | 2/3 | -0.063 | 0.750 | -1.577 | 0.250 |
| ukb elig-cvd | C1 [sub] | 3 | 1/3 | 0.049 | 0.750 | 0.102 | 0.750 |
| ukb elig-cvd | C2 [sub] | 3 | 2/3 | 0.055 | 1.000 | 0.693 | 1.000 |
| ukb elig-cvd | CLMBR vs unmatched [sub] | 3 | 3/3 | -0.056 | 0.250 | -1.613 | 0.250 |
| ukb elig-cvd | sparse+CLMBR vs sparse [sub] | 3 | 1/3 | 0.079 | 0.500 | 0.838 | 0.500 |
| ukb elig-cvd | sparse+CLMBR+ECG vs sparse+CLMBR | 3 | 1/3 | 0.097 | 0.750 | 0.093 | 1.000 |
| ukb elig-cvd | sparse+CLMBR+ECG vs sparse+ECG [sub] | 3 | 1/3 | 0.128 | 0.500 | 0.829 | 0.500 |
| ukb elig-cvd | hdPS200+CLMBR vs hdPS200 [sub] | 3 | 0/3 | 0.134 | 0.250 | 0.595 | 0.250 |
| ukb elig-cvd | panel: unmatched | 3 | est.agree 0.00; phi 4.84 | 0.457 | – | – | – |
| ukb elig-cvd | panel: sparse | 3 | est.agree 0.00; phi 2.72 | 0.489 | – | – | – |
| ukb elig-cvd | panel: sparse+ECG | 3 | est.agree 0.00; phi 1.39 | 0.282 | – | – | – |
| ukb elig-cvd | panel: hdPS200 | 3 | est.agree 0.00; phi 1.57 | 0.400 | – | – | – |
| ukb elig-cvd | panel: hdPS200+ECG | 3 | est.agree 0.00; phi 1.23 | 0.322 | – | – | – |
| ukb elig-cvd | panel: ECGonly | 3 | est.agree 0.00; phi 2.40 | 0.395 | – | – | – |
| ukb elig-cvd | panel: clinical | 3 | est.agree 0.00; phi 3.57 | 0.656 | – | – | – |


## Co-primary external outcome: all-cause death (registered 2026-09-26; verified RCT mortality benchmarks)

# v1.5 external first pass — cohort: death

Exploratory (protocol v1.5). Benchmarks are rct.json our_orientation; SE from the reported CI. Pair counts in brackets. Event counts < 11 suppressed upstream. Aggregates only. Analysed N = the ECG-linked subset. UKB: prevalent users, and the ECG is an on-treatment covariate (recorded at the exposure-defining visit).

Engine validation (Yale LIFE, exact Yale design and population): unmatched, sparse, sparse+ECG, hdPS200, hdPS200+ECG and clinical log HRs reproduce Yale imputation-1 rep 0 to < 1e-15 (docs: compare_yale_exact.csv).

## Trial directories

| trial | markers | analysed | plasmode | n_clmbr_subset | clinical_pairs | pairs_rule_150 | n_treated | n_control | events_treated | events_control | imprecise(<30 events/arm) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | cohort,ecg,outcomes | True | True | <NA> | 1327 | pass | 1556 | 3576 | 254 | 710 |  |
| mimic-comet | cohort,ecg,outcomes | True | True | <NA> | 739 | pass | 4101 | 743 | 981 | 130 |  |
| mimic-plato | cohort,ecg,outcomes | True | True | <NA> | 422 | pass | 441 | 2433 | 43 | 425 |  |
| mimic-rocket_af | cohort,ecg,outcomes | True | True | <NA> | 901 | pass | 905 | 5591 | 108 | 1032 |  |
| mimic-transform_hf | cohort,ecg,outcomes | True | True | <NA> | 904 | pass | 940 | 3466 | 251 | 764 |  |
| ukb-allhat | cohort,ecg,outcomes | True | True | 3543 | 1664 | pass | 5159 | 1750 | 86 | 33 |  |
| ukb-ascot | cohort,ecg,outcomes | True | True | 3912 | 1494 | pass | 5118 | 2681 | 89 | 69 |  |
| ukb-ontarget | cohort,ecg,outcomes | True | True | 5683 | 3556 | pass | 3561 | 6668 | 52 | 115 |  |

## Hazard ratios per trial (HR (95% CI) [pairs]) — full analysed cohort

| trial | rct | N | unmatched | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | 0.89 (0.80–0.99) | 5132 | 0.81 (0.70–0.93) | 0.79 (0.67–0.94) [1477] | 0.85 (0.71–1.01) [1478] | 0.72 (0.60–0.87) [1264] | 0.73 (0.60–0.88) [1263] | 0.87 (0.73–1.03) [1553] | 0.91 (0.76–1.08) [1327] |
| mimic-comet | 1.20 (1.07–1.35) | 4844 | 1.41 (1.17–1.69) | 1.35 (1.09–1.67) [738] | 1.24 (0.98–1.56) [740] | 1.22 (0.98–1.53) [709] | 1.04 (0.81–1.33) [708] | 1.37 (1.09–1.72) [741] | 1.17 (0.93–1.48) [739] |
| mimic-plato | 0.78 (0.69–0.89) | 2874 | 0.54 (0.39–0.74) | 0.74 (0.50–1.07) [441] | 0.65 (0.45–0.95) [432] | 0.90 (0.60–1.35) [426] | 0.92 (0.59–1.45) [399] | 0.73 (0.50–1.07) [441] | 0.75 (0.50–1.14) [422] |
| mimic-rocket_af | 0.92 (0.82–1.03) | 6496 | 0.62 (0.51–0.75) | 0.72 (0.56–0.92) [902] | 0.73 (0.57–0.93) [900] | 0.75 (0.58–0.96) [892] | 0.82 (0.64–1.05) [896] | 0.66 (0.52–0.84) [905] | 0.85 (0.65–1.10) [901] |
| mimic-transform_hf | 1.02 (0.89–1.17) | 4406 | 1.24 (1.07–1.43) | 1.10 (0.93–1.32) [940] | 1.23 (1.02–1.48) [940] | 1.21 (0.99–1.48) [808] | 1.13 (0.93–1.37) [801] | 1.08 (0.91–1.29) [940] | 1.23 (1.02–1.48) [904] |
| ukb-allhat | 0.96 (0.90–1.03) | 6909 | 1.10 (0.73–1.65) | 1.05 (0.65–1.70) [1750] | 1.01 (0.62–1.65) [1724] | 0.81 (0.48–1.39) [1656] | 0.87 (0.51–1.49) [1636] | 0.86 (0.50–1.48) [1748] | 0.90 (0.53–1.52) [1664] |
| ukb-ascot | 0.89 (0.81–0.98) | 7799 | 0.73 (0.53–1.00) | 0.80 (0.49–1.30) [1412] | 0.88 (0.53–1.45) [1455] | 0.86 (0.53–1.41) [1442] | 0.82 (0.50–1.33) [1393] | 1.00 (0.71–1.42) [2584] | 0.95 (0.59–1.55) [1494] |
| ukb-ontarget | 0.98 (0.90–1.07) | 10229 | 0.88 (0.63–1.22) | 0.80 (0.55–1.14) [3560] | 0.79 (0.55–1.14) [3557] | 0.91 (0.62–1.34) [3472] | 0.81 (0.55–1.18) [3478] | 0.86 (0.59–1.24) [3561] | 1.02 (0.69–1.50) [3556] |

## Hazard ratios — CLMBR subset (patients with a CLMBR embedding; like-for-like CLMBR comparisons)

| trial | rct | unmatched [clmbr-subset] | sparse [clmbr-subset] | sparse+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | hdPS200+ECG [clmbr-subset] | CLMBR | sparse+CLMBR | sparse+CLMBR+ECG | hdPS200+CLMBR |
|---|---|---|---|---|---|---|---|---|---|---|
| ukb-allhat | 0.96 (0.90–1.03) | 1.08 (0.70–1.66) | 0.96 (0.58–1.62) [1109] | 1.24 (0.78–2.00) [1065] | 0.82 (0.47–1.42) [1000] | 0.92 (0.52–1.63) [950] | 0.93 (0.56–1.55) [1102] | 0.86 (0.49–1.49) [1091] | 1.19 (0.71–1.99) [1036] | 0.88 (0.49–1.57) [974] |
| ukb-ascot | 0.89 (0.81–0.98) | 0.70 (0.50–0.98) | 0.88 (0.50–1.54) [723] | 0.87 (0.52–1.45) [738] | 1.00 (0.60–1.68) [737] | 0.83 (0.46–1.50) [686] | 0.67 (0.41–1.07) [1037] | 0.80 (0.49–1.31) [749] | 0.96 (0.56–1.67) [741] | 0.78 (0.45–1.36) [717] |
| ukb-ontarget | 0.98 (0.90–1.07) | 0.88 (0.62–1.25) | 0.77 (0.52–1.14) [1903] | 0.88 (0.59–1.32) [1901] | 1.00 (0.65–1.53) [1794] | 0.73 (0.49–1.10) [1801] | 0.82 (0.55–1.22) [1901] | 0.70 (0.48–1.03) [1902] | 0.82 (0.56–1.20) [1897] | 0.85 (0.55–1.30) [1802] |

## RCT-DUPLICATE panel per arm

Pearson r descriptive only (>= 3 trials); phi = Heyard dispersion Q/(k-1) (1 = disagreement explained by sampling error).

| arm | trials | significance_agreement | estimate_agreement | std_diff_agreement | pearson_r | kappa | ratio_of_ratios | ror_lo | ror_hi | I2 | dispersion_phi | mean_abs_dlog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| unmatched | 8 | 0.62 | 0.12 | 0.75 | 0.89 | 0.41 | 0.92 | 0.78 | 1.09 | 0.70 | 3.35 | 0.21 |
| sparse | 8 | 0.62 | 0.38 | 1.00 | 0.85 | 0.35 | 0.95 | 0.86 | 1.05 | 0.00 | 0.94 | 0.13 |
| sparse+ECG | 8 | 0.38 | 0.50 | 1.00 | 0.83 | -0.08 | 0.97 | 0.87 | 1.08 | 0.06 | 1.06 | 0.12 |
| hdPS200 | 8 | 0.50 | 0.38 | 1.00 | 0.67 | 0.06 | 0.95 | 0.85 | 1.07 | 0.10 | 1.11 | 0.13 |
| hdPS200+ECG | 8 | 0.62 | 0.25 | 1.00 | 0.50 | 0.27 | 0.92 | 0.82 | 1.02 | 0.00 | 0.74 | 0.14 |
| ECGonly | 8 | 0.50 | 0.38 | 0.88 | 0.78 | 0.11 | 0.97 | 0.87 | 1.08 | 0.12 | 1.14 | 0.12 |
| clinical | 8 | 0.38 | 0.88 | 1.00 | 0.85 | -0.14 | 1.03 | 0.92 | 1.14 | 0.00 | 0.39 | 0.07 |
| unmatched [clmbr-subset] | 3 | 1.00 | 0.00 | 1.00 | 0.78 | 1.00 | 0.90 | 0.72 | 1.12 | 0.00 | 0.78 | 0.15 |
| sparse [clmbr-subset] | 3 | 0.67 | 0.67 | 1.00 | -0.31 | 0.00 | 0.89 | 0.67 | 1.17 | 0.00 | 0.36 | 0.09 |
| sparse+ECG [clmbr-subset] | 3 | 0.67 | 0.33 | 1.00 | 0.33 | 0.00 | 1.03 | 0.79 | 1.35 | 0.00 | 0.68 | 0.13 |
| hdPS200 [clmbr-subset] | 3 | 0.67 | 0.33 | 1.00 | -0.32 | 0.00 | 1.00 | 0.75 | 1.33 | 0.00 | 0.26 | 0.10 |
| hdPS200+ECG [clmbr-subset] | 3 | 0.67 | 0.67 | 1.00 | -0.29 | 0.00 | 0.84 | 0.63 | 1.13 | 0.00 | 0.31 | 0.13 |
| CLMBR | 3 | 0.67 | 0.33 | 1.00 | 0.82 | 0.00 | 0.84 | 0.64 | 1.10 | 0.00 | 0.26 | 0.17 |
| sparse+CLMBR | 3 | 0.67 | 0.00 | 1.00 | -0.38 | 0.00 | 0.81 | 0.61 | 1.06 | 0.00 | 0.33 | 0.19 |
| sparse+CLMBR+ECG | 3 | 0.67 | 0.33 | 1.00 | -0.14 | 0.00 | 0.99 | 0.75 | 1.30 | 0.00 | 0.75 | 0.16 |
| hdPS200+CLMBR | 3 | 0.67 | 0.00 | 1.00 | 0.86 | 0.00 | 0.88 | 0.65 | 1.19 | 0.00 | 0.01 | 0.12 |

## Paired contrasts (negative = first arm closer to the RCT)

| contrast | first | second | trial | d_abs | d_z2 | abs_first | abs_second |
|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | mimic-aristotle | -0.062 | -1.012 | 0.051 | 0.114 |
| C1 | sparse+ECG | sparse | mimic-comet | -0.084 | -0.763 | 0.028 | 0.112 |
| C1 | sparse+ECG | sparse | mimic-plato | 0.122 | 0.721 | 0.182 | 0.059 |
| C1 | sparse+ECG | sparse | mimic-rocket_af | -0.016 | -0.343 | 0.236 | 0.251 |
| C1 | sparse+ECG | sparse | mimic-transform_hf | 0.107 | 2.029 | 0.186 | 0.079 |
| C1 | sparse+ECG | sparse | ukb-allhat | -0.041 | -0.098 | 0.052 | 0.093 |
| C1 | sparse+ECG | sparse | ukb-ascot | -0.098 | -0.189 | 0.014 | 0.112 |
| C1 | sparse+ECG | sparse | ukb-ontarget | 0.003 | 0.014 | 0.212 | 0.209 |
| C2 | hdPS200+ECG | hdPS200 | mimic-aristotle | -0.004 | -0.262 | 0.204 | 0.208 |
| C2 | hdPS200+ECG | hdPS200 | mimic-comet | 0.135 | 1.131 | 0.148 | 0.013 |
| C2 | hdPS200+ECG | hdPS200 | mimic-plato | 0.030 | 0.102 | 0.170 | 0.140 |
| C2 | hdPS200+ECG | hdPS200 | mimic-rocket_af | -0.092 | -1.523 | 0.116 | 0.207 |
| C2 | hdPS200+ECG | hdPS200 | mimic-transform_hf | -0.071 | -1.233 | 0.101 | 0.172 |
| C2 | hdPS200+ECG | hdPS200 | ukb-allhat | -0.071 | -0.242 | 0.094 | 0.165 |
| C2 | hdPS200+ECG | hdPS200 | ukb-ascot | 0.056 | 0.102 | 0.086 | 0.031 |
| C2 | hdPS200+ECG | hdPS200 | ukb-ontarget | 0.124 | 0.850 | 0.194 | 0.070 |
| ECGonly | ECGonly | unmatched | mimic-aristotle | -0.074 | -1.138 | 0.026 | 0.100 |
| ECGonly | ECGonly | unmatched | mimic-comet | -0.030 | -1.054 | 0.128 | 0.157 |
| ECGonly | ECGonly | unmatched | mimic-plato | -0.307 | -4.359 | 0.059 | 0.367 |
| ECGonly | ECGonly | unmatched | mimic-rocket_af | -0.064 | -5.890 | 0.333 | 0.398 |
| ECGonly | ECGonly | unmatched | mimic-transform_hf | -0.135 | -3.364 | 0.059 | 0.194 |
| ECGonly | ECGonly | unmatched | ukb-allhat | -0.027 | -0.266 | 0.108 | 0.135 |
| ECGonly | ECGonly | unmatched | ukb-ascot | -0.078 | -0.950 | 0.118 | 0.196 |
| ECGonly | ECGonly | unmatched | ukb-ontarget | 0.025 | 0.080 | 0.136 | 0.111 |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | ukb-allhat | 0.255 | 1.130 | 0.259 | 0.004 |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | ukb-ascot | 0.008 | 0.004 | 0.020 | 0.011 |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | ukb-ontarget | -0.132 | -1.138 | 0.110 | 0.242 |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | ukb-allhat | -0.112 | -0.289 | 0.045 | 0.157 |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | ukb-ascot | -0.054 | -0.151 | 0.065 | 0.119 |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | ukb-ontarget | 0.270 | 1.851 | 0.291 | 0.021 |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | ukb-allhat | -0.084 | -0.243 | 0.030 | 0.114 |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | ukb-ascot | 0.045 | -0.489 | 0.291 | 0.246 |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | ukb-ontarget | 0.079 | 0.450 | 0.183 | 0.104 |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | ukb-allhat | 0.111 | 0.164 | 0.115 | 0.004 |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | ukb-ascot | 0.095 | 0.167 | 0.106 | 0.011 |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | ukb-ontarget | 0.094 | 1.357 | 0.336 | 0.242 |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | ukb-allhat | 0.097 | 0.462 | 0.211 | 0.115 |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | ukb-ascot | -0.026 | -0.090 | 0.080 | 0.106 |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | ukb-ontarget | -0.154 | -1.958 | 0.182 | 0.336 |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | ukb-allhat | -0.048 | -0.504 | 0.211 | 0.259 |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | ukb-ascot | 0.060 | 0.074 | 0.080 | 0.020 |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | ukb-ontarget | 0.072 | 0.537 | 0.182 | 0.110 |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | ukb-allhat | -0.070 | -0.227 | 0.087 | 0.157 |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | ukb-ascot | 0.011 | 0.006 | 0.129 | 0.119 |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | ukb-ontarget | 0.125 | 0.413 | 0.146 | 0.021 |

Across trials (sign-flip: exact enumeration up to 20 trials, else MC; descriptive):

| contrast | first | second | trials | closer | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 | signflip |
|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 8 | 5/8 | -0.008 | 0.789 | 0.045 | 0.945 | exact |
| C2 | hdPS200+ECG | hdPS200 | 8 | 4/8 | 0.013 | 0.688 | -0.134 | 0.656 | exact |
| ECGonly | ECGonly | unmatched | 8 | 7/8 | -0.086 | 0.016 | -2.118 | 0.016 | exact |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | 3 | 1/3 | 0.044 | 0.750 | -0.002 | 1.000 | exact |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | 3 | 2/3 | 0.035 | 1.000 | 0.470 | 1.000 | exact |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | 3 | 1/3 | 0.013 | 1.000 | -0.094 | 0.750 | exact |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | 3 | 0/3 | 0.100 | 0.250 | 0.563 | 0.250 | exact |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | 3 | 2/3 | -0.028 | 0.750 | -0.529 | 0.750 | exact |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | 3 | 1/3 | 0.028 | 0.500 | 0.036 | 0.750 | exact |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | 3 | 1/3 | 0.022 | 0.750 | 0.064 | 0.750 | exact |

## Death outcome — RCT-clustered pooled analyses (exact sign-flip; negative = first arm closer to the RCT)

External = the 8 death emulations (one per RCT). Combined = external + Yale phase-2 estimates for the trials whose RCT benchmark is all-cause death (COMET, TRANSFORM-HF, ELITE II; imputation 1, rep 0), averaged within RCT.

### external death only

| contrast | first | second | rcts | emulations | closer | p_sign | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 | signflip |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 8 | 8 | 5/8 | 0.727 | -0.008 | 0.789 | 0.045 | 0.945 | exact |
| C2 | hdPS200+ECG | hdPS200 | 8 | 8 | 4/8 | 1.000 | 0.013 | 0.688 | -0.134 | 0.656 | exact |
| ECGonly | ECGonly | unmatched | 8 | 8 | 7/8 | 0.070 | -0.086 | 0.016 | -2.118 | 0.016 | exact |

### combined external death + Yale death-benchmark trials

| contrast | first | second | rcts | emulations | closer | p_sign | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 | signflip |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 9 | 11 | 6/9 | 0.508 | -0.013 | 0.590 | -0.093 | 0.672 | exact |
| C2 | hdPS200+ECG | hdPS200 | 9 | 11 | 4/9 | 1.000 | 0.007 | 0.750 | -0.146 | 0.586 | exact |
| ECGonly | ECGonly | unmatched | 9 | 11 | 8/9 | 0.039 | -0.069 | 0.012 | -1.738 | 0.008 | exact |

Yale vs external direction per shared RCT:

| contrast | key | external | yale_d_abs | external_d_abs | same_direction |
|---|---|---|---|---|---|
| C1 | comet | mimic-comet | -0.004 | -0.084 | True |
| C1 | transform_hf | mimic-transform_hf | 0.006 | 0.107 | True |
| C2 | comet | mimic-comet | -0.049 | 0.135 | False |
| C2 | transform_hf | mimic-transform_hf | -0.004 | -0.071 | True |
| ECGonly | comet | mimic-comet | -0.028 | -0.030 | True |
| ECGonly | transform_hf | mimic-transform_hf | 0.046 | -0.135 | False |

## Calendar-year balance, UKB (|SMD| of index_year per arm)

| trial | unmatched | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical | unmatched [clmbr-subset] | sparse [clmbr-subset] | sparse+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | hdPS200+ECG [clmbr-subset] | CLMBR | sparse+CLMBR | sparse+CLMBR+ECG | hdPS200+CLMBR |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ukb-allhat | 0.400 | 0.019 | 0.002 | 0.009 | 0.006 | 0.421 | 0.040 | 0.294 | 0.052 | 0.025 | 0.024 | 0.027 | 0.115 | 0.000 | 0.008 | 0.024 |
| ukb-ascot | 0.139 | 0.182 | 0.020 | 0.021 | 0.038 | 0.175 | 0.025 | 0.121 | 0.132 | 0.071 | 0.005 | 0.075 | 0.048 | 0.067 | 0.007 | 0.029 |
| ukb-ontarget | 0.056 | 0.017 | 0.011 | 0.009 | 0.012 | 0.060 | 0.003 | 0.007 | 0.025 | 0.027 | 0.006 | 0.002 | 0.017 | 0.003 | 0.002 | 0.006 |

Unmatched mean index year (treated vs control): ukb-allhat 2020.14 vs 2019.01; ukb-ascot 2020.07 vs 2019.68; ukb-ontarget 2019.69 vs 2019.53

## Negative-control outcomes and empirical calibration (OHDSI style)

Usable NCO estimate = NaN rows dropped per NCO, >= 11 NCO events in the arm's analysed sample. Systematic-error model b ~ N(mu, sigma^2 + se^2) (v13 fit_syserr); per trial when >= 6 usable NCOs, else the cohort-pooled fit.

Usable NCOs per trial: mimic-aristotle 9, mimic-comet 9, mimic-plato 8, mimic-rocket_af 9, mimic-transform_hf 9, ukb-allhat 3, ukb-ascot 3, ukb-ontarget 3

### Systematic error pooled across the cohort's trials, per arm

| cohort | arm | trials | nco_estimates | mu | abs_mu | sigma | share_ci_excl_1 |
|---|---|---|---|---|---|---|---|
| mimic | ECGonly | 5 | 34 | -0.028 | 0.028 | 0.139 | 0.118 |
| mimic | clinical | 5 | 34 | -0.002 | 0.002 | 0.061 | 0.000 |
| mimic | hdPS200 | 5 | 34 | -0.058 | 0.058 | 0.091 | 0.088 |
| mimic | hdPS200+ECG | 5 | 33 | -0.032 | 0.032 | 0.029 | 0.030 |
| mimic | sparse | 5 | 33 | 0.053 | 0.053 | 0.211 | 0.091 |
| mimic | sparse+ECG | 5 | 33 | 0.024 | 0.024 | 0.236 | 0.091 |
| mimic | unmatched | 5 | 44 | -0.038 | 0.038 | 0.172 | 0.114 |
| ukb | CLMBR | 3 | 9 | -0.019 | 0.019 | 0.000 | 0.000 |
| ukb | ECGonly | 3 | 9 | -0.020 | 0.020 | 0.102 | 0.111 |
| ukb | clinical | 3 | 9 | -0.095 | 0.095 | 0.000 | 0.111 |
| ukb | hdPS200 | 3 | 9 | -0.061 | 0.061 | 0.000 | 0.111 |
| ukb | hdPS200 [clmbr-subset] | 3 | 9 | -0.011 | 0.011 | 0.000 | 0.111 |
| ukb | hdPS200+CLMBR | 3 | 9 | -0.031 | 0.031 | 0.000 | 0.111 |
| ukb | hdPS200+ECG | 3 | 9 | -0.064 | 0.064 | 0.000 | 0.111 |
| ukb | hdPS200+ECG [clmbr-subset] | 3 | 9 | -0.115 | 0.115 | 0.113 | 0.000 |
| ukb | sparse | 3 | 9 | -0.021 | 0.021 | 0.000 | 0.111 |
| ukb | sparse [clmbr-subset] | 3 | 9 | -0.061 | 0.061 | 0.099 | 0.111 |
| ukb | sparse+CLMBR | 3 | 9 | -0.042 | 0.042 | 0.088 | 0.111 |
| ukb | sparse+CLMBR+ECG | 3 | 9 | -0.036 | 0.036 | 0.000 | 0.000 |
| ukb | sparse+ECG | 3 | 9 | -0.048 | 0.048 | 0.000 | 0.111 |
| ukb | sparse+ECG [clmbr-subset] | 3 | 9 | -0.156 | 0.156 | 0.157 | 0.111 |
| ukb | unmatched | 3 | 9 | -0.107 | 0.107 | 0.190 | 0.333 |
| ukb | unmatched [clmbr-subset] | 3 | 9 | -0.100 | 0.100 | 0.184 | 0.333 |

### Per-trial fits (trials with >= 6 usable NCOs), summarised per arm

| cohort | arm | trials_estimable | mean_abs_mu | mean_sigma | mean_share_ci_excl_1 |
|---|---|---|---|---|---|
| mimic | ECGonly | 4 | 0.138 | 0.051 | 0.122 |
| mimic | clinical | 4 | 0.086 | 0.078 | 0.000 |
| mimic | hdPS200 | 4 | 0.166 | 0.000 | 0.094 |
| mimic | hdPS200+ECG | 4 | 0.130 | 0.052 | 0.031 |
| mimic | sparse | 4 | 0.148 | 0.103 | 0.094 |
| mimic | sparse+ECG | 4 | 0.198 | 0.044 | 0.094 |
| mimic | unmatched | 5 | 0.226 | 0.022 | 0.114 |

Per-trial mu (NCO log HR bias):

| trial | unmatched | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|
| mimic-aristotle | -0.041 | -0.049 | -0.105 | -0.186 | -0.158 | -0.058 | -0.095 |
| mimic-comet | -0.001 | 0.035 | -0.108 | 0.036 | 0.054 | -0.134 | 0.086 |
| mimic-plato | -0.627 | – | – | – | – | – | – |
| mimic-rocket_af | -0.210 | -0.109 | -0.115 | -0.223 | -0.115 | -0.158 | -0.033 |
| mimic-transform_hf | 0.250 | 0.399 | 0.464 | 0.219 | 0.192 | 0.200 | 0.129 |

### Does adding ECG (or CLMBR) reduce systematic error? (per-trial fits; negative = first arm lower; exact sign-flip)

| contrast | first | second | trials | lower_abs_mu | mean_d_abs_mu | p_signflip_abs_mu | mean_d_sigma | p_signflip_sigma | signflip |
|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 4 | 0/4 | 0.050 | 0.125 | -0.059 | 0.625 | exact |
| C2 | hdPS200+ECG | hdPS200 | 4 | 3/4 | -0.036 | 0.250 | 0.052 | 0.750 | exact |
| ECGonly | ECGonly | unmatched | 4 | 2/4 | 0.012 | 0.875 | 0.023 | 1.000 | exact |

### RCT agreement after calibration of the primary estimates

| arm | trials | significance_agreement | estimate_agreement | std_diff_agreement | pearson_r | kappa | ratio_of_ratios | ror_lo | ror_hi | I2 | dispersion_phi | mean_abs_dlog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| unmatched | 8 | 0.75 | 0.50 | 1.00 | 0.61 | 0.56 | 1.01 | 0.91 | 1.11 | 0.02 | 1.03 | 0.13 |
| sparse | 8 | 0.38 | 0.50 | 0.88 | 0.75 | -0.21 | 0.86 | 0.76 | 0.98 | 0.00 | 0.71 | 0.14 |
| sparse+ECG | 8 | 0.62 | 0.25 | 1.00 | 0.77 | 0.31 | 0.99 | 0.88 | 1.11 | 0.00 | 0.73 | 0.14 |
| hdPS200 | 8 | 0.50 | 0.75 | 1.00 | 0.72 | 0.00 | 0.99 | 0.89 | 1.10 | 0.00 | 0.15 | 0.06 |
| hdPS200+ECG | 8 | 0.50 | 0.62 | 1.00 | 0.35 | 0.00 | 0.95 | 0.85 | 1.07 | 0.00 | 0.27 | 0.09 |
| ECGonly | 8 | 0.62 | 0.38 | 0.88 | 0.79 | 0.31 | 1.01 | 0.91 | 1.13 | 0.00 | 0.99 | 0.12 |
| clinical | 8 | 0.50 | 0.62 | 1.00 | 0.72 | 0.00 | 1.06 | 0.94 | 1.19 | 0.00 | 0.23 | 0.09 |
| unmatched [clmbr-subset] | 3 | 0.67 | 0.33 | 1.00 | 0.78 | 0.00 | 1.01 | 0.74 | 1.36 | 0.00 | 0.43 | 0.12 |
| sparse [clmbr-subset] | 3 | 0.67 | 0.67 | 1.00 | -0.31 | 0.00 | 0.95 | 0.70 | 1.28 | 0.00 | 0.30 | 0.10 |
| sparse+ECG [clmbr-subset] | 3 | 0.67 | 0.33 | 1.00 | 0.33 | 0.00 | 1.21 | 0.88 | 1.67 | 0.00 | 0.47 | 0.20 |
| hdPS200 [clmbr-subset] | 3 | 0.67 | 0.33 | 1.00 | -0.32 | 0.00 | 1.01 | 0.76 | 1.35 | 0.00 | 0.26 | 0.10 |
| hdPS200+ECG [clmbr-subset] | 3 | 0.67 | 0.33 | 1.00 | -0.29 | 0.00 | 0.95 | 0.69 | 1.32 | 0.00 | 0.26 | 0.10 |
| CLMBR | 3 | 0.67 | 0.33 | 1.00 | 0.82 | 0.00 | 0.86 | 0.66 | 1.12 | 0.00 | 0.26 | 0.15 |
| sparse+CLMBR | 3 | 0.67 | 0.33 | 1.00 | -0.38 | 0.00 | 0.84 | 0.63 | 1.13 | 0.00 | 0.29 | 0.14 |
| sparse+CLMBR+ECG | 3 | 0.67 | 0.00 | 1.00 | -0.14 | 0.00 | 1.03 | 0.78 | 1.35 | 0.00 | 0.75 | 0.17 |
| hdPS200+CLMBR | 3 | 0.67 | 0.67 | 1.00 | 0.86 | 0.00 | 0.91 | 0.67 | 1.23 | 0.00 | 0.01 | 0.09 |

Paired contrasts after calibration:

| contrast | first | second | trials | closer | mean_d_abs | p_signflip_abs | mean_d_z2 | p_signflip_z2 | signflip |
|---|---|---|---|---|---|---|---|---|---|
| C1 | sparse+ECG | sparse | 8 | 6/8 | -0.002 | 0.922 | -0.608 | 0.828 | exact |
| C2 | hdPS200+ECG | hdPS200 | 8 | 3/8 | 0.034 | 0.312 | 0.182 | 0.148 | exact |
| ECGonly | ECGonly | unmatched | 8 | 4/8 | -0.009 | 0.836 | -0.027 | 0.953 | exact |
| C1 [sub] | sparse+ECG [clmbr-subset] | sparse [clmbr-subset] | 3 | 1/3 | 0.100 | 0.750 | 0.519 | 0.750 | exact |
| C2 [sub] | hdPS200+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | 3 | 2/3 | -0.004 | 1.000 | 0.026 | 1.000 | exact |
| CLMBR vs unmatched [sub] | CLMBR | unmatched [clmbr-subset] | 3 | 1/3 | 0.028 | 1.000 | 0.316 | 0.500 | exact |
| sparse+CLMBR vs sparse [sub] | sparse+CLMBR | sparse [clmbr-subset] | 3 | 0/3 | 0.045 | 0.250 | 0.393 | 0.250 | exact |
| sparse+CLMBR+ECG vs sparse+CLMBR | sparse+CLMBR+ECG | sparse+CLMBR | 3 | 1/3 | 0.026 | 0.750 | -0.117 | 1.000 | exact |
| sparse+CLMBR+ECG vs sparse+ECG [sub] | sparse+CLMBR+ECG | sparse+ECG [clmbr-subset] | 3 | 2/3 | -0.029 | 0.750 | -0.243 | 0.750 | exact |
| hdPS200+CLMBR vs hdPS200 [sub] | hdPS200+CLMBR | hdPS200 [clmbr-subset] | 3 | 2/3 | -0.013 | 0.750 | -0.036 | 1.000 | exact |

## Plasmode bias per arm (true conditional HR 0.8; truth = marginal HR in the arm's matched population)

The outcome model excludes the ECG (as at Yale), so ECG arms can reduce plasmode bias only through their correlation with the clinical covariates; C1 reductions near zero are expected by construction.

| trial | scenario | arm | reps | truth | bias | bias_lo | bias_hi | emp_sd | rmse | coverage |
|---|---|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | base | unmatched | 200 | -0.213 | -0.100 | -0.111 | -0.089 | 0.079 | 0.128 | 0.775 |
| mimic-aristotle | base | sparse | 200 | -0.208 | -0.117 | -0.130 | -0.105 | 0.089 | 0.147 | 0.795 |
| mimic-aristotle | base | sparse+ECG | 200 | -0.203 | -0.128 | -0.141 | -0.115 | 0.094 | 0.159 | 0.745 |
| mimic-aristotle | base | hdPS200 | 200 | -0.209 | -0.084 | -0.098 | -0.069 | 0.105 | 0.134 | 0.860 |
| mimic-aristotle | base | hdPS200+ECG | 200 | -0.213 | -0.076 | -0.088 | -0.062 | 0.096 | 0.122 | 0.905 |
| mimic-aristotle | base | ECGonly | 200 | -0.205 | -0.092 | -0.105 | -0.079 | 0.094 | 0.131 | 0.815 |
| mimic-aristotle | base | clinical | 200 | -0.209 | -0.016 | -0.028 | -0.004 | 0.090 | 0.091 | 0.970 |
| mimic-aristotle | phys_only | unmatched | 200 | -0.215 | -0.133 | -0.144 | -0.122 | 0.079 | 0.155 | 0.665 |
| mimic-aristotle | phys_only | sparse | 200 | -0.215 | -0.145 | -0.157 | -0.132 | 0.092 | 0.171 | 0.670 |
| mimic-aristotle | phys_only | sparse+ECG | 200 | -0.202 | -0.158 | -0.171 | -0.145 | 0.092 | 0.183 | 0.600 |
| mimic-aristotle | phys_only | hdPS200 | 200 | -0.212 | -0.089 | -0.104 | -0.074 | 0.106 | 0.138 | 0.875 |
| mimic-aristotle | phys_only | hdPS200+ECG | 200 | -0.216 | -0.079 | -0.093 | -0.065 | 0.100 | 0.127 | 0.895 |
| mimic-aristotle | phys_only | ECGonly | 200 | -0.214 | -0.111 | -0.125 | -0.098 | 0.094 | 0.145 | 0.780 |
| mimic-aristotle | phys_only | clinical | 200 | -0.210 | -0.007 | -0.021 | 0.007 | 0.101 | 0.101 | 0.950 |
| mimic-comet | base | unmatched | 200 | -0.209 | 0.156 | 0.143 | 0.170 | 0.100 | 0.185 | 0.650 |
| mimic-comet | base | sparse | 200 | -0.219 | 0.055 | 0.036 | 0.073 | 0.136 | 0.146 | 0.925 |
| mimic-comet | base | sparse+ECG | 200 | -0.206 | 0.044 | 0.028 | 0.060 | 0.124 | 0.131 | 0.950 |
| mimic-comet | base | hdPS200 | 200 | -0.201 | -0.012 | -0.031 | 0.009 | 0.148 | 0.148 | 0.940 |
| mimic-comet | base | hdPS200+ECG | 200 | -0.206 | 0.002 | -0.018 | 0.022 | 0.139 | 0.139 | 0.955 |
| mimic-comet | base | ECGonly | 200 | -0.215 | 0.107 | 0.090 | 0.125 | 0.128 | 0.167 | 0.885 |
| mimic-comet | base | clinical | 200 | -0.206 | 0.004 | -0.014 | 0.022 | 0.137 | 0.137 | 0.945 |
| mimic-comet | phys_only | unmatched | 200 | -0.212 | 0.127 | 0.112 | 0.140 | 0.098 | 0.160 | 0.785 |
| mimic-comet | phys_only | sparse | 200 | -0.223 | 0.029 | 0.009 | 0.048 | 0.140 | 0.143 | 0.935 |
| mimic-comet | phys_only | sparse+ECG | 200 | -0.205 | 0.015 | -0.002 | 0.033 | 0.128 | 0.128 | 0.960 |
| mimic-comet | phys_only | hdPS200 | 200 | -0.207 | -0.000 | -0.020 | 0.019 | 0.139 | 0.138 | 0.940 |
| mimic-comet | phys_only | hdPS200+ECG | 200 | -0.218 | 0.023 | 0.004 | 0.042 | 0.135 | 0.137 | 0.955 |
| mimic-comet | phys_only | ECGonly | 200 | -0.210 | 0.087 | 0.069 | 0.105 | 0.129 | 0.155 | 0.895 |
| mimic-comet | phys_only | clinical | 200 | -0.213 | 0.010 | -0.009 | 0.029 | 0.136 | 0.136 | 0.955 |
| mimic-plato | base | unmatched | 200 | -0.187 | -0.248 | -0.269 | -0.227 | 0.149 | 0.289 | 0.765 |
| mimic-plato | base | sparse | 200 | -0.202 | 0.147 | 0.118 | 0.177 | 0.213 | 0.259 | 0.885 |
| mimic-plato | base | sparse+ECG | 200 | -0.177 | 0.028 | 0.000 | 0.056 | 0.194 | 0.196 | 0.970 |
| mimic-plato | base | hdPS200 | 200 | -0.202 | 0.099 | 0.073 | 0.127 | 0.203 | 0.226 | 0.935 |
| mimic-plato | base | hdPS200+ECG | 200 | -0.195 | 0.092 | 0.063 | 0.120 | 0.210 | 0.229 | 0.930 |
| mimic-plato | base | ECGonly | 200 | -0.174 | -0.118 | -0.146 | -0.091 | 0.194 | 0.227 | 0.925 |
| mimic-plato | base | clinical | 200 | -0.185 | 0.024 | -0.004 | 0.050 | 0.193 | 0.194 | 0.975 |
| mimic-plato | phys_only | unmatched | 200 | -0.207 | -0.457 | -0.482 | -0.430 | 0.185 | 0.493 | 0.330 |
| mimic-plato | phys_only | sparse | 200 | -0.204 | -0.081 | -0.114 | -0.048 | 0.242 | 0.255 | 0.945 |
| mimic-plato | phys_only | sparse+ECG | 200 | -0.206 | -0.130 | -0.164 | -0.096 | 0.233 | 0.267 | 0.945 |
| mimic-plato | phys_only | hdPS200 | 200 | -0.216 | -0.064 | -0.098 | -0.029 | 0.249 | 0.257 | 0.940 |
| mimic-plato | phys_only | hdPS200+ECG | 200 | -0.185 | -0.074 | -0.110 | -0.038 | 0.271 | 0.281 | 0.920 |
| mimic-plato | phys_only | ECGonly | 200 | -0.206 | -0.283 | -0.313 | -0.252 | 0.220 | 0.359 | 0.780 |
| mimic-plato | phys_only | clinical | 200 | -0.192 | 0.014 | -0.023 | 0.049 | 0.251 | 0.251 | 0.965 |
| mimic-rocket_af | base | unmatched | 200 | -0.205 | -0.330 | -0.345 | -0.314 | 0.110 | 0.348 | 0.145 |
| mimic-rocket_af | base | sparse | 200 | -0.213 | -0.151 | -0.170 | -0.133 | 0.131 | 0.200 | 0.835 |
| mimic-rocket_af | base | sparse+ECG | 200 | -0.206 | -0.191 | -0.210 | -0.172 | 0.134 | 0.233 | 0.735 |
| mimic-rocket_af | base | hdPS200 | 200 | -0.209 | -0.127 | -0.147 | -0.108 | 0.136 | 0.186 | 0.850 |
| mimic-rocket_af | base | hdPS200+ECG | 200 | -0.210 | -0.152 | -0.171 | -0.132 | 0.136 | 0.204 | 0.795 |
| mimic-rocket_af | base | ECGonly | 200 | -0.209 | -0.260 | -0.279 | -0.239 | 0.135 | 0.293 | 0.470 |
| mimic-rocket_af | base | clinical | 200 | -0.215 | -0.062 | -0.080 | -0.044 | 0.129 | 0.143 | 0.960 |
| mimic-rocket_af | phys_only | unmatched | 200 | -0.209 | -0.350 | -0.364 | -0.335 | 0.104 | 0.365 | 0.095 |
| mimic-rocket_af | phys_only | sparse | 200 | -0.213 | -0.172 | -0.190 | -0.155 | 0.135 | 0.218 | 0.780 |
| mimic-rocket_af | phys_only | sparse+ECG | 200 | -0.208 | -0.189 | -0.208 | -0.169 | 0.139 | 0.234 | 0.740 |
| mimic-rocket_af | phys_only | hdPS200 | 200 | -0.214 | -0.101 | -0.119 | -0.082 | 0.132 | 0.166 | 0.925 |
| mimic-rocket_af | phys_only | hdPS200+ECG | 200 | -0.214 | -0.122 | -0.141 | -0.104 | 0.138 | 0.184 | 0.875 |
| mimic-rocket_af | phys_only | ECGonly | 200 | -0.210 | -0.271 | -0.288 | -0.254 | 0.128 | 0.300 | 0.505 |
| mimic-rocket_af | phys_only | clinical | 200 | -0.209 | -0.047 | -0.067 | -0.027 | 0.141 | 0.149 | 0.950 |
| mimic-transform_hf | base | unmatched | 200 | -0.210 | 0.027 | 0.016 | 0.038 | 0.080 | 0.084 | 0.965 |
| mimic-transform_hf | base | sparse | 200 | -0.209 | 0.082 | 0.069 | 0.095 | 0.094 | 0.124 | 0.900 |
| mimic-transform_hf | base | sparse+ECG | 200 | -0.209 | 0.048 | 0.035 | 0.061 | 0.096 | 0.107 | 0.960 |
| mimic-transform_hf | base | hdPS200 | 200 | -0.200 | 0.004 | -0.012 | 0.019 | 0.108 | 0.108 | 0.975 |
| mimic-transform_hf | base | hdPS200+ECG | 200 | -0.212 | -0.001 | -0.016 | 0.014 | 0.107 | 0.107 | 0.975 |
| mimic-transform_hf | base | ECGonly | 200 | -0.219 | 0.051 | 0.039 | 0.065 | 0.097 | 0.109 | 0.945 |
| mimic-transform_hf | base | clinical | 200 | -0.212 | -0.011 | -0.025 | 0.004 | 0.107 | 0.108 | 0.960 |
| mimic-transform_hf | phys_only | unmatched | 200 | -0.208 | -0.007 | -0.019 | 0.004 | 0.086 | 0.086 | 0.965 |
| mimic-transform_hf | phys_only | sparse | 200 | -0.208 | 0.053 | 0.038 | 0.067 | 0.107 | 0.119 | 0.930 |
| mimic-transform_hf | phys_only | sparse+ECG | 200 | -0.212 | 0.024 | 0.010 | 0.039 | 0.103 | 0.106 | 0.960 |
| mimic-transform_hf | phys_only | hdPS200 | 200 | -0.206 | 0.015 | -0.000 | 0.030 | 0.106 | 0.107 | 0.960 |
| mimic-transform_hf | phys_only | hdPS200+ECG | 200 | -0.211 | 0.006 | -0.009 | 0.021 | 0.107 | 0.107 | 0.975 |
| mimic-transform_hf | phys_only | ECGonly | 200 | -0.218 | 0.011 | -0.004 | 0.026 | 0.109 | 0.110 | 0.950 |
| mimic-transform_hf | phys_only | clinical | 200 | -0.217 | -0.008 | -0.023 | 0.007 | 0.108 | 0.108 | 0.980 |
| ukb-allhat | base | unmatched | 200 | -0.220 | 0.161 | 0.127 | 0.194 | 0.241 | 0.290 | 0.930 |
| ukb-allhat | base | sparse | 200 | -0.237 | 0.111 | 0.071 | 0.153 | 0.288 | 0.308 | 0.945 |
| ukb-allhat | base | sparse+ECG | 200 | -0.233 | 0.087 | 0.044 | 0.128 | 0.308 | 0.319 | 0.955 |
| ukb-allhat | base | hdPS200 | 200 | -0.209 | 0.031 | -0.012 | 0.075 | 0.312 | 0.313 | 0.960 |
| ukb-allhat | base | hdPS200+ECG | 200 | -0.220 | 0.058 | 0.020 | 0.096 | 0.274 | 0.280 | 0.980 |
| ukb-allhat | base | ECGonly | 200 | -0.215 | 0.116 | 0.072 | 0.160 | 0.308 | 0.328 | 0.960 |
| ukb-allhat | base | clinical | 200 | -0.208 | 0.035 | -0.007 | 0.078 | 0.313 | 0.314 | 0.965 |
| ukb-allhat | base | unmatched [clmbr-subset] | 200 | -0.222 | 0.141 | 0.101 | 0.180 | 0.293 | 0.325 | 0.935 |
| ukb-allhat | base | sparse [clmbr-subset] | 200 | -0.245 | 0.078 | 0.026 | 0.123 | 0.352 | 0.360 | 0.945 |
| ukb-allhat | base | sparse+ECG [clmbr-subset] | 200 | -0.227 | 0.060 | 0.006 | 0.111 | 0.387 | 0.390 | 0.925 |
| ukb-allhat | base | hdPS200 [clmbr-subset] | 200 | -0.229 | 0.043 | -0.010 | 0.097 | 0.384 | 0.386 | 0.920 |
| ukb-allhat | base | hdPS200+ECG [clmbr-subset] | 200 | -0.232 | 0.051 | -0.009 | 0.110 | 0.432 | 0.434 | 0.945 |
| ukb-allhat | base | CLMBR | 200 | -0.231 | 0.077 | 0.033 | 0.119 | 0.311 | 0.319 | 0.965 |
| ukb-allhat | base | sparse+CLMBR | 200 | -0.228 | 0.071 | 0.019 | 0.123 | 0.368 | 0.374 | 0.945 |
| ukb-allhat | base | sparse+CLMBR+ECG | 200 | -0.240 | 0.098 | 0.049 | 0.146 | 0.349 | 0.362 | 0.950 |
| ukb-allhat | base | hdPS200+CLMBR | 200 | -0.238 | 0.056 | -0.000 | 0.111 | 0.404 | 0.407 | 0.960 |
| ukb-allhat | phys_only | unmatched | 200 | -0.212 | 0.109 | 0.075 | 0.144 | 0.254 | 0.276 | 0.935 |
| ukb-allhat | phys_only | sparse | 200 | -0.216 | 0.029 | -0.015 | 0.074 | 0.316 | 0.317 | 0.930 |
| ukb-allhat | phys_only | sparse+ECG | 200 | -0.218 | 0.027 | -0.010 | 0.067 | 0.281 | 0.281 | 0.980 |
| ukb-allhat | phys_only | hdPS200 | 200 | -0.219 | 0.062 | 0.021 | 0.104 | 0.304 | 0.310 | 0.960 |
| ukb-allhat | phys_only | hdPS200+ECG | 200 | -0.203 | 0.016 | -0.029 | 0.064 | 0.334 | 0.333 | 0.935 |
| ukb-allhat | phys_only | ECGonly | 200 | -0.228 | 0.065 | 0.022 | 0.112 | 0.320 | 0.325 | 0.940 |
| ukb-allhat | phys_only | clinical | 200 | -0.230 | 0.065 | 0.021 | 0.110 | 0.334 | 0.340 | 0.925 |
| ukb-allhat | phys_only | unmatched [clmbr-subset] | 200 | -0.230 | 0.132 | 0.093 | 0.170 | 0.281 | 0.309 | 0.930 |
| ukb-allhat | phys_only | sparse [clmbr-subset] | 200 | -0.232 | 0.035 | -0.015 | 0.081 | 0.341 | 0.342 | 0.950 |
| ukb-allhat | phys_only | sparse+ECG [clmbr-subset] | 200 | -0.210 | 0.022 | -0.026 | 0.067 | 0.338 | 0.338 | 0.960 |
| ukb-allhat | phys_only | hdPS200 [clmbr-subset] | 200 | -0.219 | 0.047 | -0.004 | 0.094 | 0.339 | 0.341 | 0.945 |
| ukb-allhat | phys_only | hdPS200+ECG [clmbr-subset] | 200 | -0.232 | 0.033 | -0.017 | 0.081 | 0.359 | 0.360 | 0.950 |
| ukb-allhat | phys_only | CLMBR | 200 | -0.227 | 0.008 | -0.042 | 0.055 | 0.353 | 0.352 | 0.955 |
| ukb-allhat | phys_only | sparse+CLMBR | 200 | -0.232 | 0.051 | 0.004 | 0.098 | 0.345 | 0.348 | 0.945 |
| ukb-allhat | phys_only | sparse+CLMBR+ECG | 200 | -0.226 | 0.041 | -0.006 | 0.087 | 0.345 | 0.346 | 0.940 |
| ukb-allhat | phys_only | hdPS200+CLMBR | 200 | -0.218 | 0.053 | 0.002 | 0.101 | 0.369 | 0.372 | 0.955 |
| ukb-ascot | base | unmatched | 200 | -0.240 | -0.177 | -0.202 | -0.151 | 0.186 | 0.256 | 0.835 |
| ukb-ascot | base | sparse | 200 | -0.211 | -0.068 | -0.107 | -0.028 | 0.298 | 0.305 | 0.955 |
| ukb-ascot | base | sparse+ECG | 200 | -0.210 | -0.062 | -0.107 | -0.014 | 0.338 | 0.343 | 0.925 |
| ukb-ascot | base | hdPS200 | 200 | -0.235 | -0.003 | -0.045 | 0.038 | 0.308 | 0.308 | 0.940 |
| ukb-ascot | base | hdPS200+ECG | 200 | -0.218 | -0.032 | -0.075 | 0.013 | 0.326 | 0.327 | 0.935 |
| ukb-ascot | base | ECGonly | 200 | -0.222 | -0.136 | -0.167 | -0.103 | 0.234 | 0.270 | 0.895 |
| ukb-ascot | base | clinical | 200 | -0.245 | 0.006 | -0.036 | 0.051 | 0.322 | 0.321 | 0.935 |
| ukb-ascot | base | unmatched [clmbr-subset] | 200 | -0.220 | -0.203 | -0.233 | -0.174 | 0.216 | 0.295 | 0.810 |
| ukb-ascot | base | sparse [clmbr-subset] | 200 | -0.225 | -0.038 | -0.087 | 0.009 | 0.347 | 0.348 | 0.960 |
| ukb-ascot | base | sparse+ECG [clmbr-subset] | 200 | -0.202 | -0.055 | -0.104 | -0.007 | 0.354 | 0.358 | 0.950 |
| ukb-ascot | base | hdPS200 [clmbr-subset] | 200 | -0.237 | -0.034 | -0.077 | 0.013 | 0.328 | 0.329 | 0.960 |
| ukb-ascot | base | hdPS200+ECG [clmbr-subset] | 200 | -0.184 | -0.083 | -0.131 | -0.035 | 0.354 | 0.363 | 0.950 |
| ukb-ascot | base | CLMBR | 200 | -0.228 | -0.024 | -0.065 | 0.018 | 0.305 | 0.305 | 0.925 |
| ukb-ascot | base | sparse+CLMBR | 200 | -0.224 | -0.017 | -0.067 | 0.032 | 0.369 | 0.368 | 0.935 |
| ukb-ascot | base | sparse+CLMBR+ECG | 200 | -0.224 | -0.010 | -0.059 | 0.038 | 0.361 | 0.361 | 0.940 |
| ukb-ascot | base | hdPS200+CLMBR | 200 | -0.230 | -0.017 | -0.064 | 0.031 | 0.364 | 0.364 | 0.940 |
| ukb-ascot | phys_only | unmatched | 200 | -0.231 | -0.061 | -0.086 | -0.035 | 0.188 | 0.197 | 0.940 |
| ukb-ascot | phys_only | sparse | 200 | -0.215 | -0.041 | -0.078 | -0.004 | 0.265 | 0.268 | 0.965 |
| ukb-ascot | phys_only | sparse+ECG | 200 | -0.213 | -0.042 | -0.083 | 0.002 | 0.310 | 0.312 | 0.945 |
| ukb-ascot | phys_only | hdPS200 | 200 | -0.247 | 0.030 | -0.012 | 0.069 | 0.293 | 0.294 | 0.960 |
| ukb-ascot | phys_only | hdPS200+ECG | 200 | -0.228 | -0.014 | -0.060 | 0.030 | 0.336 | 0.335 | 0.935 |
| ukb-ascot | phys_only | ECGonly | 200 | -0.246 | -0.005 | -0.037 | 0.026 | 0.232 | 0.231 | 0.960 |
| ukb-ascot | phys_only | clinical | 200 | -0.230 | 0.038 | -0.000 | 0.074 | 0.264 | 0.266 | 0.970 |
| ukb-ascot | phys_only | unmatched [clmbr-subset] | 200 | -0.216 | -0.049 | -0.080 | -0.020 | 0.219 | 0.223 | 0.945 |
| ukb-ascot | phys_only | sparse [clmbr-subset] | 200 | -0.207 | -0.045 | -0.092 | 0.002 | 0.350 | 0.352 | 0.955 |
| ukb-ascot | phys_only | sparse+ECG [clmbr-subset] | 200 | -0.230 | -0.027 | -0.072 | 0.020 | 0.346 | 0.346 | 0.955 |
| ukb-ascot | phys_only | hdPS200 [clmbr-subset] | 200 | -0.218 | -0.032 | -0.082 | 0.021 | 0.383 | 0.384 | 0.945 |
| ukb-ascot | phys_only | hdPS200+ECG [clmbr-subset] | 200 | -0.226 | -0.023 | -0.072 | 0.026 | 0.360 | 0.360 | 0.975 |
| ukb-ascot | phys_only | CLMBR | 200 | -0.225 | 0.007 | -0.033 | 0.047 | 0.289 | 0.289 | 0.950 |
| ukb-ascot | phys_only | sparse+CLMBR | 200 | -0.199 | -0.071 | -0.118 | -0.024 | 0.341 | 0.347 | 0.960 |
| ukb-ascot | phys_only | sparse+CLMBR+ECG | 200 | -0.232 | -0.026 | -0.073 | 0.023 | 0.348 | 0.348 | 0.965 |
| ukb-ascot | phys_only | hdPS200+CLMBR | 200 | -0.234 | -0.031 | -0.083 | 0.019 | 0.382 | 0.382 | 0.955 |
| ukb-ontarget | base | unmatched | 200 | -0.221 | 0.037 | 0.011 | 0.063 | 0.196 | 0.199 | 0.940 |
| ukb-ontarget | base | sparse | 200 | -0.220 | 0.011 | -0.016 | 0.040 | 0.208 | 0.208 | 0.960 |
| ukb-ontarget | base | sparse+ECG | 200 | -0.222 | 0.019 | -0.011 | 0.048 | 0.221 | 0.221 | 0.950 |
| ukb-ontarget | base | hdPS200 | 200 | -0.218 | 0.015 | -0.014 | 0.044 | 0.221 | 0.221 | 0.955 |
| ukb-ontarget | base | hdPS200+ECG | 200 | -0.229 | 0.019 | -0.011 | 0.047 | 0.220 | 0.221 | 0.945 |
| ukb-ontarget | base | ECGonly | 200 | -0.225 | 0.048 | 0.018 | 0.076 | 0.211 | 0.216 | 0.955 |
| ukb-ontarget | base | clinical | 200 | -0.233 | -0.002 | -0.031 | 0.027 | 0.217 | 0.216 | 0.940 |
| ukb-ontarget | base | unmatched [clmbr-subset] | 200 | -0.212 | 0.017 | -0.013 | 0.049 | 0.223 | 0.223 | 0.940 |
| ukb-ontarget | base | sparse [clmbr-subset] | 200 | -0.242 | 0.032 | -0.003 | 0.070 | 0.258 | 0.259 | 0.930 |
| ukb-ontarget | base | sparse+ECG [clmbr-subset] | 200 | -0.217 | 0.004 | -0.030 | 0.039 | 0.250 | 0.250 | 0.945 |
| ukb-ontarget | base | hdPS200 [clmbr-subset] | 200 | -0.224 | -0.015 | -0.052 | 0.020 | 0.266 | 0.266 | 0.950 |
| ukb-ontarget | base | hdPS200+ECG [clmbr-subset] | 200 | -0.235 | -0.004 | -0.039 | 0.030 | 0.252 | 0.252 | 0.965 |
| ukb-ontarget | base | CLMBR | 200 | -0.240 | 0.023 | -0.011 | 0.057 | 0.247 | 0.247 | 0.950 |
| ukb-ontarget | base | sparse+CLMBR | 200 | -0.235 | 0.005 | -0.029 | 0.040 | 0.254 | 0.254 | 0.950 |
| ukb-ontarget | base | sparse+CLMBR+ECG | 200 | -0.220 | -0.004 | -0.038 | 0.032 | 0.254 | 0.254 | 0.940 |
| ukb-ontarget | base | hdPS200+CLMBR | 200 | -0.216 | -0.028 | -0.062 | 0.008 | 0.256 | 0.257 | 0.950 |
| ukb-ontarget | phys_only | unmatched | 200 | -0.204 | -0.015 | -0.043 | 0.012 | 0.198 | 0.199 | 0.950 |
| ukb-ontarget | phys_only | sparse | 200 | -0.216 | -0.002 | -0.033 | 0.029 | 0.224 | 0.223 | 0.925 |
| ukb-ontarget | phys_only | sparse+ECG | 200 | -0.212 | -0.005 | -0.034 | 0.026 | 0.213 | 0.212 | 0.950 |
| ukb-ontarget | phys_only | hdPS200 | 200 | -0.229 | 0.027 | -0.005 | 0.060 | 0.238 | 0.239 | 0.940 |
| ukb-ontarget | phys_only | hdPS200+ECG | 200 | -0.227 | 0.016 | -0.015 | 0.047 | 0.227 | 0.227 | 0.950 |
| ukb-ontarget | phys_only | ECGonly | 200 | -0.196 | -0.008 | -0.040 | 0.025 | 0.238 | 0.238 | 0.935 |
| ukb-ontarget | phys_only | clinical | 200 | -0.225 | 0.022 | -0.011 | 0.054 | 0.232 | 0.232 | 0.940 |
| ukb-ontarget | phys_only | unmatched [clmbr-subset] | 200 | -0.222 | 0.009 | -0.023 | 0.043 | 0.243 | 0.242 | 0.945 |
| ukb-ontarget | phys_only | sparse [clmbr-subset] | 200 | -0.218 | -0.010 | -0.045 | 0.026 | 0.259 | 0.258 | 0.950 |
| ukb-ontarget | phys_only | sparse+ECG [clmbr-subset] | 200 | -0.224 | 0.021 | -0.015 | 0.059 | 0.274 | 0.274 | 0.955 |
| ukb-ontarget | phys_only | hdPS200 [clmbr-subset] | 200 | -0.229 | 0.015 | -0.020 | 0.052 | 0.270 | 0.269 | 0.960 |
| ukb-ontarget | phys_only | hdPS200+ECG [clmbr-subset] | 200 | -0.222 | -0.004 | -0.038 | 0.033 | 0.261 | 0.261 | 0.950 |
| ukb-ontarget | phys_only | CLMBR | 200 | -0.233 | 0.014 | -0.022 | 0.052 | 0.270 | 0.269 | 0.955 |
| ukb-ontarget | phys_only | sparse+CLMBR | 200 | -0.230 | 0.022 | -0.013 | 0.062 | 0.273 | 0.273 | 0.945 |
| ukb-ontarget | phys_only | sparse+CLMBR+ECG | 200 | -0.215 | -0.002 | -0.040 | 0.038 | 0.280 | 0.280 | 0.930 |
| ukb-ontarget | phys_only | hdPS200+CLMBR | 200 | -0.202 | -0.020 | -0.058 | 0.019 | 0.283 | 0.283 | 0.935 |

## Plasmode bias reduction (|bias second| - |bias first|; positive = first arm less biased; MC 95% CI)

| trial | scenario | contrast | bias_second | bias_first | abs_bias_reduction | lo | hi | pct_reduction |
|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | base | C1 | -0.117 | -0.128 | -0.011 | -0.018 | -0.004 | -9.358 |
| mimic-aristotle | base | C2 | -0.084 | -0.076 | 0.009 | -0.001 | 0.018 | 10.356 |
| mimic-aristotle | base | ECGonly | -0.100 | -0.092 | 0.008 | 0.002 | 0.014 | 8.143 |
| mimic-aristotle | phys_only | C1 | -0.145 | -0.158 | -0.014 | -0.021 | -0.006 | -9.436 |
| mimic-aristotle | phys_only | C2 | -0.089 | -0.079 | 0.010 | 0.002 | 0.019 | 11.423 |
| mimic-aristotle | phys_only | ECGonly | -0.133 | -0.111 | 0.022 | 0.015 | 0.028 | 16.483 |
| mimic-comet | base | C1 | 0.055 | 0.044 | 0.010 | -0.006 | 0.027 | 19.153 |
| mimic-comet | base | C2 | -0.012 | 0.002 | 0.010 | -0.017 | 0.024 | 86.313 |
| mimic-comet | base | ECGonly | 0.156 | 0.107 | 0.049 | 0.037 | 0.060 | 31.179 |
| mimic-comet | phys_only | C1 | 0.029 | 0.015 | 0.013 | -0.004 | 0.030 | 46.495 |
| mimic-comet | phys_only | C2 | -0.000 | 0.023 | -0.022 | -0.034 | 0.012 | -14450.722 |
| mimic-comet | phys_only | ECGonly | 0.127 | 0.087 | 0.040 | 0.027 | 0.051 | 31.379 |
| mimic-plato | base | C1 | 0.147 | 0.028 | 0.119 | 0.098 | 0.141 | 80.981 |
| mimic-plato | base | C2 | 0.099 | 0.092 | 0.008 | -0.011 | 0.025 | 7.755 |
| mimic-plato | base | ECGonly | -0.248 | -0.118 | 0.131 | 0.112 | 0.149 | 52.628 |
| mimic-plato | phys_only | C1 | -0.081 | -0.130 | -0.049 | -0.073 | -0.026 | -60.724 |
| mimic-plato | phys_only | C2 | -0.064 | -0.074 | -0.010 | -0.033 | 0.012 | -15.795 |
| mimic-plato | phys_only | ECGonly | -0.457 | -0.283 | 0.174 | 0.157 | 0.191 | 37.991 |
| mimic-rocket_af | base | C1 | -0.151 | -0.191 | -0.040 | -0.054 | -0.025 | -26.312 |
| mimic-rocket_af | base | C2 | -0.127 | -0.152 | -0.024 | -0.036 | -0.013 | -19.087 |
| mimic-rocket_af | base | ECGonly | -0.330 | -0.260 | 0.070 | 0.059 | 0.081 | 21.216 |
| mimic-rocket_af | phys_only | C1 | -0.172 | -0.189 | -0.017 | -0.032 | -0.002 | -9.918 |
| mimic-rocket_af | phys_only | C2 | -0.101 | -0.122 | -0.022 | -0.034 | -0.009 | -21.455 |
| mimic-rocket_af | phys_only | ECGonly | -0.350 | -0.271 | 0.078 | 0.067 | 0.090 | 22.380 |
| mimic-transform_hf | base | C1 | 0.082 | 0.048 | 0.034 | 0.022 | 0.045 | 41.335 |
| mimic-transform_hf | base | C2 | 0.004 | -0.001 | 0.003 | -0.010 | 0.011 | 77.311 |
| mimic-transform_hf | base | ECGonly | 0.027 | 0.051 | -0.025 | -0.033 | -0.017 | -92.707 |
| mimic-transform_hf | phys_only | C1 | 0.053 | 0.024 | 0.028 | 0.016 | 0.040 | 53.593 |
| mimic-transform_hf | phys_only | C2 | 0.015 | 0.006 | 0.009 | -0.006 | 0.019 | 62.303 |
| mimic-transform_hf | phys_only | ECGonly | -0.007 | 0.011 | -0.004 | -0.023 | 0.016 | -49.723 |
| ukb-allhat | base | C1 | 0.111 | 0.087 | 0.024 | -0.012 | 0.059 | 21.887 |
| ukb-allhat | base | C2 | 0.031 | 0.058 | -0.027 | -0.055 | 0.005 | -87.277 |
| ukb-allhat | base | ECGonly | 0.161 | 0.116 | 0.045 | 0.016 | 0.074 | 28.101 |
| ukb-allhat | base | C1 [sub] | 0.078 | 0.060 | 0.018 | -0.018 | 0.052 | 22.912 |
| ukb-allhat | base | C2 [sub] | 0.043 | 0.051 | -0.008 | -0.042 | 0.024 | -17.747 |
| ukb-allhat | base | CLMBR vs unmatched [sub] | 0.141 | 0.077 | 0.064 | 0.040 | 0.088 | 45.307 |
| ukb-allhat | base | sparse+CLMBR vs sparse [sub] | 0.078 | 0.071 | 0.007 | -0.027 | 0.039 | 8.659 |
| ukb-allhat | base | sparse+CLMBR+ECG vs sparse+CLMBR | 0.071 | 0.098 | -0.026 | -0.061 | 0.006 | -37.193 |
| ukb-allhat | base | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.060 | 0.098 | -0.038 | -0.074 | -0.005 | -62.558 |
| ukb-allhat | base | hdPS200+CLMBR vs hdPS200 [sub] | 0.043 | 0.056 | -0.013 | -0.045 | 0.020 | -29.212 |
| ukb-allhat | phys_only | C1 | 0.029 | 0.027 | 0.002 | -0.026 | 0.030 | 6.485 |
| ukb-allhat | phys_only | C2 | 0.062 | 0.016 | 0.047 | -0.001 | 0.071 | 74.825 |
| ukb-allhat | phys_only | ECGonly | 0.109 | 0.065 | 0.044 | 0.016 | 0.073 | 40.469 |
| ukb-allhat | phys_only | C1 [sub] | 0.035 | 0.022 | 0.013 | -0.027 | 0.045 | 36.224 |
| ukb-allhat | phys_only | C2 [sub] | 0.047 | 0.033 | 0.014 | -0.018 | 0.043 | 29.882 |
| ukb-allhat | phys_only | CLMBR vs unmatched [sub] | 0.132 | 0.008 | 0.123 | 0.056 | 0.139 | 93.646 |
| ukb-allhat | phys_only | sparse+CLMBR vs sparse [sub] | 0.035 | 0.051 | -0.016 | -0.048 | 0.017 | -46.332 |
| ukb-allhat | phys_only | sparse+CLMBR+ECG vs sparse+CLMBR | 0.051 | 0.041 | 0.010 | -0.022 | 0.042 | 19.897 |
| ukb-allhat | phys_only | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.022 | 0.041 | -0.019 | -0.048 | 0.021 | -83.794 |
| ukb-allhat | phys_only | hdPS200+CLMBR vs hdPS200 [sub] | 0.047 | 0.053 | -0.006 | -0.038 | 0.025 | -12.273 |
| ukb-ascot | base | C1 | -0.068 | -0.062 | 0.005 | -0.031 | 0.040 | 7.778 |
| ukb-ascot | base | C2 | -0.003 | -0.032 | -0.029 | -0.054 | 0.028 | -873.837 |
| ukb-ascot | base | ECGonly | -0.177 | -0.136 | 0.041 | 0.025 | 0.057 | 23.214 |
| ukb-ascot | base | C1 [sub] | -0.038 | -0.055 | -0.017 | -0.061 | 0.027 | -43.942 |
| ukb-ascot | base | C2 [sub] | -0.034 | -0.083 | -0.050 | -0.087 | -0.010 | -148.328 |
| ukb-ascot | base | CLMBR vs unmatched [sub] | -0.203 | -0.024 | 0.178 | 0.148 | 0.200 | 87.976 |
| ukb-ascot | base | sparse+CLMBR vs sparse [sub] | -0.038 | -0.017 | 0.021 | -0.027 | 0.055 | 55.258 |
| ukb-ascot | base | sparse+CLMBR+ECG vs sparse+CLMBR | -0.017 | -0.010 | 0.007 | -0.030 | 0.037 | 42.369 |
| ukb-ascot | base | sparse+CLMBR+ECG vs sparse+ECG [sub] | -0.055 | -0.010 | 0.045 | -0.021 | 0.075 | 82.086 |
| ukb-ascot | base | hdPS200+CLMBR vs hdPS200 [sub] | -0.034 | -0.017 | 0.016 | -0.027 | 0.047 | 48.268 |
| ukb-ascot | phys_only | C1 | -0.041 | -0.042 | -0.001 | -0.040 | 0.036 | -2.158 |
| ukb-ascot | phys_only | C2 | 0.030 | -0.014 | 0.015 | -0.052 | 0.055 | 52.193 |
| ukb-ascot | phys_only | ECGonly | -0.061 | -0.005 | 0.056 | 0.012 | 0.067 | 91.715 |
| ukb-ascot | phys_only | C1 [sub] | -0.045 | -0.027 | 0.018 | -0.027 | 0.058 | 39.682 |
| ukb-ascot | phys_only | C2 [sub] | -0.032 | -0.023 | 0.009 | -0.029 | 0.044 | 29.444 |
| ukb-ascot | phys_only | CLMBR vs unmatched [sub] | -0.049 | 0.007 | 0.042 | -0.023 | 0.066 | 84.938 |
| ukb-ascot | phys_only | sparse+CLMBR vs sparse [sub] | -0.045 | -0.071 | -0.026 | -0.062 | 0.013 | -57.495 |
| ukb-ascot | phys_only | sparse+CLMBR+ECG vs sparse+CLMBR | -0.071 | -0.026 | 0.045 | -0.001 | 0.077 | 63.775 |
| ukb-ascot | phys_only | sparse+CLMBR+ECG vs sparse+ECG [sub] | -0.027 | -0.026 | 0.001 | -0.033 | 0.037 | 5.412 |
| ukb-ascot | phys_only | hdPS200+CLMBR vs hdPS200 [sub] | -0.032 | -0.031 | 0.001 | -0.035 | 0.036 | 4.384 |
| ukb-ontarget | base | C1 | 0.011 | 0.019 | -0.008 | -0.025 | 0.013 | -72.860 |
| ukb-ontarget | base | C2 | 0.015 | 0.019 | -0.003 | -0.021 | 0.014 | -22.575 |
| ukb-ontarget | base | ECGonly | 0.037 | 0.048 | -0.011 | -0.025 | 0.003 | -29.540 |
| ukb-ontarget | base | C1 [sub] | 0.032 | 0.004 | 0.028 | -0.024 | 0.046 | 87.246 |
| ukb-ontarget | base | C2 [sub] | -0.015 | -0.004 | 0.011 | -0.019 | 0.028 | 73.073 |
| ukb-ontarget | base | CLMBR vs unmatched [sub] | 0.017 | 0.023 | -0.006 | -0.022 | 0.011 | -37.356 |
| ukb-ontarget | base | sparse+CLMBR vs sparse [sub] | 0.032 | 0.005 | 0.028 | -0.024 | 0.045 | 85.355 |
| ukb-ontarget | base | sparse+CLMBR+ECG vs sparse+CLMBR | 0.005 | -0.004 | 0.000 | -0.021 | 0.022 | 9.705 |
| ukb-ontarget | base | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.004 | -0.004 | -0.000 | -0.022 | 0.023 | -3.683 |
| ukb-ontarget | base | hdPS200+CLMBR vs hdPS200 [sub] | -0.015 | -0.028 | -0.013 | -0.031 | 0.015 | -84.273 |
| ukb-ontarget | phys_only | C1 | -0.002 | -0.005 | -0.003 | -0.017 | 0.017 | -183.161 |
| ukb-ontarget | phys_only | C2 | 0.027 | 0.016 | 0.011 | -0.011 | 0.029 | 41.017 |
| ukb-ontarget | phys_only | ECGonly | -0.015 | -0.008 | 0.007 | -0.017 | 0.019 | 47.575 |
| ukb-ontarget | phys_only | C1 [sub] | -0.010 | 0.021 | -0.010 | -0.044 | 0.038 | -102.401 |
| ukb-ontarget | phys_only | C2 [sub] | 0.015 | -0.004 | 0.012 | -0.028 | 0.035 | 74.918 |
| ukb-ontarget | phys_only | CLMBR vs unmatched [sub] | 0.009 | 0.014 | -0.005 | -0.021 | 0.012 | -55.965 |
| ukb-ontarget | phys_only | sparse+CLMBR vs sparse [sub] | -0.010 | 0.022 | -0.012 | -0.047 | 0.037 | -119.266 |
| ukb-ontarget | phys_only | sparse+CLMBR+ECG vs sparse+CLMBR | 0.022 | -0.002 | 0.021 | -0.032 | 0.040 | 92.492 |
| ukb-ontarget | phys_only | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.021 | -0.002 | 0.019 | -0.031 | 0.037 | 91.866 |
| ukb-ontarget | phys_only | hdPS200+CLMBR vs hdPS200 [sub] | 0.015 | -0.020 | -0.004 | -0.047 | 0.042 | -26.317 |
| pooled (8; mean |bias|) | base | C1 | 0.093 | 0.076 | 0.017 | 0.009 | 0.025 | – |
| pooled (8; mean |bias|) | base | C2 | 0.047 | 0.054 | -0.007 | -0.014 | 0.002 | – |
| pooled (8; mean |bias|) | base | ECGonly | 0.154 | 0.116 | 0.039 | 0.033 | 0.044 | – |
| pooled (3; mean |bias|) | base | C1 [sub] | 0.050 | 0.040 | 0.010 | -0.017 | 0.027 | – |
| pooled (3; mean |bias|) | base | C2 [sub] | 0.031 | 0.046 | -0.016 | -0.036 | 0.002 | – |
| pooled (3; mean |bias|) | base | CLMBR vs unmatched [sub] | 0.120 | 0.042 | 0.079 | 0.065 | 0.091 | – |
| pooled (3; mean |bias|) | base | sparse+CLMBR vs sparse [sub] | 0.050 | 0.031 | 0.019 | -0.008 | 0.034 | – |
| pooled (3; mean |bias|) | base | sparse+CLMBR+ECG vs sparse+CLMBR | 0.031 | 0.037 | -0.006 | -0.025 | 0.009 | – |
| pooled (3; mean |bias|) | base | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.040 | 0.037 | 0.003 | -0.024 | 0.018 | – |
| pooled (3; mean |bias|) | base | hdPS200+CLMBR vs hdPS200 [sub] | 0.031 | 0.034 | -0.003 | -0.023 | 0.014 | – |
| pooled (8; mean |bias|) | phys_only | C1 | 0.069 | 0.074 | -0.005 | -0.012 | 0.003 | – |
| pooled (8; mean |bias|) | phys_only | C2 | 0.048 | 0.044 | 0.005 | -0.007 | 0.013 | – |
| pooled (8; mean |bias|) | phys_only | ECGonly | 0.157 | 0.105 | 0.052 | 0.043 | 0.057 | – |
| pooled (3; mean |bias|) | phys_only | C1 [sub] | 0.030 | 0.023 | 0.007 | -0.018 | 0.031 | – |
| pooled (3; mean |bias|) | phys_only | C2 [sub] | 0.032 | 0.020 | 0.012 | -0.012 | 0.027 | – |
| pooled (3; mean |bias|) | phys_only | CLMBR vs unmatched [sub] | 0.063 | 0.010 | 0.053 | 0.022 | 0.063 | – |
| pooled (3; mean |bias|) | phys_only | sparse+CLMBR vs sparse [sub] | 0.030 | 0.048 | -0.018 | -0.038 | 0.007 | – |
| pooled (3; mean |bias|) | phys_only | sparse+CLMBR+ECG vs sparse+CLMBR | 0.048 | 0.023 | 0.025 | -0.002 | 0.039 | – |
| pooled (3; mean |bias|) | phys_only | sparse+CLMBR+ECG vs sparse+ECG [sub] | 0.023 | 0.023 | 0.001 | -0.023 | 0.018 | – |
| pooled (3; mean |bias|) | phys_only | hdPS200+CLMBR vs hdPS200 [sub] | 0.032 | 0.034 | -0.003 | -0.026 | 0.020 | – |

## Balance capture % (labs_vitals, full cohort; observed values; blank where unmatched excess < 0.02)

| trial | k | unmatched_excess | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | 8 | 0.225 | 8.4 | 18.5 | 66.5 | 65.5 | 19.5 | 103.5 |
| mimic-comet | 8 | 0.137 | 27.3 | 35.2 | 58.8 | 54.3 | 20.2 | 103.1 |
| mimic-plato | 8 | 0.124 | 57.0 | 57.2 | 41.7 | 65.2 | 68.2 | 102.1 |
| mimic-rocket_af | 8 | 0.240 | 12.4 | 26.5 | 88.8 | 83.9 | 9.6 | 108.6 |
| mimic-transform_hf | 8 | 0.100 | 4.2 | 20.7 | 67.4 | 59.4 | 17.6 | 117.2 |
| ukb-allhat | 9 | 0.057 | -15.8 | 39.5 | 76.5 | 104.6 | 57.4 | 122.8 |
| ukb-ascot | 9 | 0.107 | 39.3 | 59.1 | 84.8 | 87.1 | 11.0 | 106.8 |
| ukb-ontarget | 9 | 0.032 | 38.9 | 90.0 | 66.8 | 67.3 | 49.2 | 136.7 |

Median capture % across trials: sparse 20, sparse+ECG 37, hdPS200 67, hdPS200+ECG 66, ECGonly 20, clinical 108

## Balance capture % (phys, full cohort; observed values; blank where unmatched excess < 0.02)

| trial | k | unmatched_excess | sparse | sparse+ECG | hdPS200 | hdPS200+ECG | ECGonly | clinical |
|---|---|---|---|---|---|---|---|---|
| mimic-aristotle | 8 | 0.225 | 8.4 | 18.5 | 66.5 | 65.5 | 19.5 | 103.5 |
| mimic-comet | 8 | 0.137 | 27.3 | 35.2 | 58.8 | 54.3 | 20.2 | 103.1 |
| mimic-plato | 8 | 0.124 | 57.0 | 57.2 | 41.7 | 65.2 | 68.2 | 102.1 |
| mimic-rocket_af | 8 | 0.240 | 12.4 | 26.5 | 88.8 | 83.9 | 9.6 | 108.6 |
| mimic-transform_hf | 8 | 0.100 | 4.2 | 20.7 | 67.4 | 59.4 | 17.6 | 117.2 |
| ukb-allhat | 5 | 0.080 | -0.6 | 56.4 | 67.6 | 88.8 | 66.7 | 120.1 |
| ukb-ascot | 5 | 0.130 | 43.0 | 76.6 | 83.9 | 89.8 | 16.5 | 97.2 |
| ukb-ontarget | 5 | 0.043 | 31.2 | 74.6 | 48.3 | 65.4 | 43.0 | 132.3 |

Median capture % across trials: sparse 20, sparse+ECG 46, hdPS200 67, hdPS200+ECG 65, ECGonly 20, clinical 106

## Balance capture % (labs_vitals, CLMBR subset; observed values; blank where unmatched excess < 0.02)

| trial | k | unmatched_excess | sparse [clmbr-subset] | sparse+ECG [clmbr-subset] | hdPS200 [clmbr-subset] | hdPS200+ECG [clmbr-subset] | CLMBR | sparse+CLMBR | sparse+CLMBR+ECG | hdPS200+CLMBR |
|---|---|---|---|---|---|---|---|---|---|---|
| ukb-allhat | 9 | 0.054 | 11.5 | 51.0 | 84.3 | 109.3 | -15.1 | -2.6 | 70.8 | 40.9 |
| ukb-ascot | 9 | 0.135 | 48.1 | 66.7 | 81.0 | 84.4 | 41.6 | 63.0 | 81.6 | 72.1 |
| ukb-ontarget | 9 | 0.025 | 59.9 | 46.5 | 92.3 | 76.8 | 26.9 | 49.5 | 74.3 | 91.3 |

Median capture % across trials: sparse [clmbr-subset] 48, sparse+ECG [clmbr-subset] 51, hdPS200 [clmbr-subset] 84, hdPS200+ECG [clmbr-subset] 84, CLMBR 27, sparse+CLMBR 50, sparse+CLMBR+ECG 74, hdPS200+CLMBR 72

