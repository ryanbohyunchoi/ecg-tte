# RCT-DUPLICATE metric panel, ratio of ratios and Heyard-style dispersion (post-hoc v1.4 addition H; exploratory)

18 trials; full-cohort point estimates (imputation 1). Paired inference: exact sign-flip across trials and McNemar.

Blinded closeness rating (RCT-DUPLICATE rubric): close = ['aristotle', 'carolina', 'elite-ii', 'rely', 'rocket-af']

## Panel — all (18 trials)

| arm | trials | significance_agreement | estimate_agreement | std_diff_agreement | pearson_r | r_loo_min | r_loo_max | kappa | ratio_of_ratios | ror_lo | ror_hi | I2 | dispersion_phi | mean_abs_dlog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 18 | 0.56 | 0.33 | 0.50 | 0.31 | 0.19 | 0.39 | 0.27 | 0.87 | 0.74 | 1.02 | 0.93 | 13.84 | 0.28 |
| Demographics | 18 | 0.50 | 0.44 | 0.56 | 0.27 | 0.16 | 0.34 | 0.17 | 0.88 | 0.76 | 1.01 | 0.90 | 9.75 | 0.27 |
| ECG only | 18 | 0.50 | 0.44 | 0.67 | 0.34 | 0.19 | 0.44 | 0.14 | 0.89 | 0.79 | 1.00 | 0.85 | 6.89 | 0.22 |
| Demographics + ECG | 18 | 0.50 | 0.44 | 0.61 | 0.42 | 0.32 | 0.52 | 0.13 | 0.91 | 0.81 | 1.02 | 0.84 | 6.08 | 0.21 |
| Sparse | 18 | 0.44 | 0.56 | 0.61 | 0.30 | 0.17 | 0.43 | 0.04 | 0.93 | 0.84 | 1.03 | 0.79 | 4.70 | 0.18 |
| Sparse + ECG | 18 | 0.44 | 0.56 | 0.78 | 0.28 | 0.12 | 0.43 | 0.04 | 0.95 | 0.87 | 1.04 | 0.71 | 3.41 | 0.16 |
| hdPS200 | 18 | 0.28 | 0.50 | 0.56 | 0.24 | 0.12 | 0.42 | -0.32 | 0.99 | 0.90 | 1.08 | 0.69 | 3.28 | 0.16 |
| hdPS200 + ECG | 18 | 0.39 | 0.50 | 0.72 | 0.13 | -0.05 | 0.44 | -0.12 | 1.00 | 0.92 | 1.08 | 0.63 | 2.71 | 0.16 |
| Clinical PS | 18 | 0.39 | 0.56 | 0.72 | 0.54 | 0.44 | 0.63 | -0.06 | 0.96 | 0.88 | 1.04 | 0.63 | 2.72 | 0.14 |
| R+ physiology ref | 18 | 0.44 | 0.50 | 0.78 | 0.29 | 0.12 | 0.44 | 0.04 | 0.95 | 0.88 | 1.03 | 0.64 | 2.80 | 0.16 |

Paired comparisons (negative mean differences favour the first arm):

| comparison | trials | mean_diff_abs | p_signflip_abs | closer | mean_diff_z2 | p_signflip_z2 | estimate_agreement_gained | lost | p_mcnemar |
|---|---|---|---|---|---|---|---|---|---|
| Sparse + ECG vs Sparse | 18 | -0.020 | 0.267 | 14/18 | -1.403 | 0.024 | 1 | 1 | 1.000 |
| hdPS200 + ECG vs hdPS200 | 18 | -0.002 | 0.919 | 10/18 | -0.565 | 0.242 | 2 | 2 | 1.000 |
| ECG only vs Unadjusted | 18 | -0.057 | 0.031 | 14/18 | -6.404 | 0.002 | 4 | 2 | 0.688 |
| Demographics + ECG vs Demographics | 18 | -0.058 | 0.034 | 14/18 | -3.667 | 0.006 | 2 | 2 | 1.000 |
| Sparse + ECG vs Clinical PS | 18 | 0.024 | 0.387 | 9/18 | 0.764 | 0.197 | 1 | 1 | 1.000 |
| hdPS200 + ECG vs Clinical PS | 18 | 0.022 | 0.636 | 9/18 | -0.147 | 0.830 | 2 | 3 | 1.000 |

## Panel — close (blinded rubric) (5 trials)

| arm | trials | significance_agreement | estimate_agreement | std_diff_agreement | pearson_r | r_loo_min | r_loo_max | kappa | ratio_of_ratios | ror_lo | ror_hi | I2 | dispersion_phi | mean_abs_dlog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 5 | 0.80 | 0.40 | 0.60 | 0.55 | 0.29 | 0.80 | 0.62 | 0.80 | 0.64 | 0.99 | 0.73 | 3.73 | 0.23 |
| Demographics | 5 | 0.60 | 0.40 | 0.60 | 0.37 | 0.17 | 0.77 | 0.17 | 0.79 | 0.63 | 1.00 | 0.69 | 3.25 | 0.27 |
| ECG only | 5 | 0.60 | 0.60 | 0.80 | 0.47 | 0.16 | 0.79 | 0.17 | 0.85 | 0.70 | 1.03 | 0.57 | 2.32 | 0.20 |
| Demographics + ECG | 5 | 0.60 | 0.60 | 0.80 | 0.53 | 0.14 | 0.85 | 0.17 | 0.83 | 0.68 | 1.01 | 0.57 | 2.34 | 0.21 |
| Sparse | 5 | 0.60 | 0.80 | 1.00 | 0.52 | 0.01 | 0.86 | 0.17 | 0.89 | 0.79 | 1.01 | 0.00 | 0.88 | 0.16 |
| Sparse + ECG | 5 | 0.60 | 0.60 | 1.00 | 0.12 | -0.39 | 0.84 | 0.17 | 0.96 | 0.82 | 1.12 | 0.31 | 1.46 | 0.16 |
| hdPS200 | 5 | 0.60 | 0.40 | 0.60 | 0.00 | -0.60 | 0.88 | 0.17 | 0.91 | 0.75 | 1.10 | 0.49 | 1.97 | 0.23 |
| hdPS200 + ECG | 5 | 0.60 | 0.80 | 0.80 | -0.25 | -0.64 | 0.96 | 0.17 | 0.98 | 0.80 | 1.19 | 0.52 | 2.08 | 0.21 |
| Clinical PS | 5 | 0.60 | 0.80 | 1.00 | 0.88 | 0.76 | 0.99 | 0.17 | 0.88 | 0.77 | 1.00 | 0.00 | 0.25 | 0.13 |
| R+ physiology ref | 5 | 0.60 | 0.60 | 1.00 | 0.07 | -0.39 | 1.00 | 0.17 | 0.90 | 0.78 | 1.05 | 0.19 | 1.23 | 0.19 |

Paired comparisons (negative mean differences favour the first arm):

| comparison | trials | mean_diff_abs | p_signflip_abs | closer | mean_diff_z2 | p_signflip_z2 | estimate_agreement_gained | lost | p_mcnemar |
|---|---|---|---|---|---|---|---|---|---|
| Sparse + ECG vs Sparse | 5 | -0.000 | 1.000 | 4/5 | -0.011 | 1.000 | 0 | 1 | 1.000 |
| hdPS200 + ECG vs hdPS200 | 5 | -0.021 | 0.750 | 3/5 | -0.342 | 0.625 | 2 | 0 | 0.500 |
| ECG only vs Unadjusted | 5 | -0.028 | 0.625 | 3/5 | -3.247 | 0.250 | 1 | 0 | 1.000 |
| Demographics + ECG vs Demographics | 5 | -0.066 | 0.312 | 4/5 | -1.998 | 0.125 | 1 | 0 | 1.000 |
| Sparse + ECG vs Clinical PS | 5 | 0.028 | 0.812 | 2/5 | 0.317 | 0.812 | 0 | 1 | 1.000 |
| hdPS200 + ECG vs Clinical PS | 5 | 0.075 | 0.938 | 3/5 | 0.789 | 0.938 | 1 | 1 | 1.000 |

## Panel — not close (blinded rubric) (13 trials)

| arm | trials | significance_agreement | estimate_agreement | std_diff_agreement | pearson_r | r_loo_min | r_loo_max | kappa | ratio_of_ratios | ror_lo | ror_hi | I2 | dispersion_phi | mean_abs_dlog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 13 | 0.46 | 0.31 | 0.46 | 0.24 | 0.04 | 0.34 | 0.14 | 0.89 | 0.74 | 1.08 | 0.94 | 17.54 | 0.30 |
| Demographics | 13 | 0.46 | 0.46 | 0.54 | 0.23 | 0.07 | 0.34 | 0.14 | 0.91 | 0.77 | 1.07 | 0.92 | 12.05 | 0.26 |
| ECG only | 13 | 0.46 | 0.38 | 0.62 | 0.31 | 0.08 | 0.40 | 0.10 | 0.90 | 0.78 | 1.04 | 0.89 | 8.81 | 0.23 |
| Demographics + ECG | 13 | 0.46 | 0.38 | 0.54 | 0.39 | 0.24 | 0.49 | 0.10 | 0.94 | 0.82 | 1.07 | 0.87 | 7.47 | 0.21 |
| Sparse | 13 | 0.38 | 0.46 | 0.46 | 0.30 | 0.11 | 0.39 | -0.03 | 0.93 | 0.83 | 1.06 | 0.84 | 6.31 | 0.19 |
| Sparse + ECG | 13 | 0.38 | 0.54 | 0.69 | 0.38 | 0.18 | 0.50 | -0.03 | 0.95 | 0.85 | 1.05 | 0.77 | 4.34 | 0.16 |
| hdPS200 | 13 | 0.15 | 0.54 | 0.54 | 0.36 | 0.20 | 0.47 | -0.49 | 1.01 | 0.91 | 1.11 | 0.74 | 3.82 | 0.14 |
| hdPS200 + ECG | 13 | 0.31 | 0.38 | 0.69 | 0.37 | 0.14 | 0.47 | -0.22 | 1.01 | 0.92 | 1.10 | 0.68 | 3.12 | 0.14 |
| Clinical PS | 13 | 0.31 | 0.46 | 0.62 | 0.41 | 0.22 | 0.49 | -0.16 | 0.98 | 0.89 | 1.07 | 0.72 | 3.59 | 0.14 |
| R+ physiology ref | 13 | 0.38 | 0.46 | 0.69 | 0.38 | 0.16 | 0.45 | -0.03 | 0.96 | 0.88 | 1.06 | 0.71 | 3.48 | 0.15 |

Paired comparisons (negative mean differences favour the first arm):

| comparison | trials | mean_diff_abs | p_signflip_abs | closer | mean_diff_z2 | p_signflip_z2 | estimate_agreement_gained | lost | p_mcnemar |
|---|---|---|---|---|---|---|---|---|---|
| Sparse + ECG vs Sparse | 13 | -0.028 | 0.086 | 10/13 | -1.939 | 0.010 | 1 | 0 | 1.000 |
| hdPS200 + ECG vs hdPS200 | 13 | 0.005 | 0.802 | 7/13 | -0.650 | 0.285 | 0 | 2 | 0.500 |
| ECG only vs Unadjusted | 13 | -0.068 | 0.030 | 11/13 | -7.619 | 0.006 | 3 | 2 | 1.000 |
| Demographics + ECG vs Demographics | 13 | -0.054 | 0.098 | 10/13 | -4.308 | 0.024 | 1 | 2 | 1.000 |
| Sparse + ECG vs Clinical PS | 13 | 0.022 | 0.255 | 7/13 | 0.936 | 0.237 | 1 | 0 | 1.000 |
| hdPS200 + ECG vs Clinical PS | 13 | 0.002 | 0.941 | 6/13 | -0.507 | 0.536 | 1 | 2 | 1.000 |

## Heyard-style weighted meta-regression of Δlog HR on closeness (per arm)

phi_residual = residual multiplicative dispersion (1 = remaining disagreement explained by sampling error).

| arm | trials | phi_residual | intercept | close_coef |
|---|---|---|---|---|
| Unadjusted | 18 | 14.090 | -0.059 | -0.195 |
| Demographics | 18 | 9.849 | -0.059 | -0.199 |
| ECG only | 18 | 7.189 | -0.084 | -0.098 |
| Demographics + ECG | 18 | 6.185 | -0.055 | -0.145 |
| Sparse | 18 | 4.951 | -0.058 | -0.054 |
| Sparse + ECG | 18 | 3.624 | -0.050 | -0.004 |
| hdPS200 | 18 | 3.360 | -0.012 | -0.100 |
| hdPS200 + ECG | 18 | 2.859 | -0.013 | -0.037 |
| Clinical PS | 18 | 2.754 | -0.027 | -0.103 |
| R+ physiology ref | 18 | 2.920 | -0.044 | -0.064 |

