# CLMBR sensitivity analysis and RCT-DUPLICATE-style correlation (18 trials; post-hoc addition I; exploratory)

CLMBR-T (code-only, 768-d) patient embeddings, 64 PCs, as in the phase-1 grid. Real data: full-cohort estimates (imputation 1).

## RCT-DUPLICATE panel with correlation (Pearson r of log HRs; Fisher 95% CI)

| arm | trials | pearson_r | r_lo | r_hi | r_loo | spearman | significance_agreement | estimate_agreement | std_diff_agreement | ratio_of_ratios | dispersion_phi | mean_abs_dlog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 18 | 0.31 | -0.19 | 0.68 | 0.19–0.39 | 0.28 | 0.56 | 0.33 | 0.50 | 0.87 | 13.84 | 0.28 |
| ECG only | 18 | 0.34 | -0.15 | 0.69 | 0.19–0.44 | 0.33 | 0.50 | 0.44 | 0.67 | 0.89 | 6.89 | 0.22 |
| CLMBR only | 18 | 0.36 | -0.12 | 0.71 | 0.23–0.45 | 0.25 | 0.33 | 0.56 | 0.72 | 1.00 | 3.62 | 0.15 |
| CLMBR + ECG | 18 | 0.41 | -0.07 | 0.73 | 0.27–0.47 | 0.33 | 0.39 | 0.39 | 0.61 | 0.97 | 3.14 | 0.16 |
| Sparse | 18 | 0.30 | -0.19 | 0.67 | 0.17–0.43 | 0.28 | 0.44 | 0.56 | 0.61 | 0.93 | 4.70 | 0.18 |
| Sparse + ECG | 18 | 0.28 | -0.22 | 0.66 | 0.12–0.43 | 0.27 | 0.44 | 0.56 | 0.78 | 0.95 | 3.41 | 0.16 |
| Sparse + CLMBR | 18 | 0.32 | -0.18 | 0.68 | 0.17–0.40 | 0.25 | 0.28 | 0.39 | 0.78 | 1.00 | 2.70 | 0.15 |
| Sparse + CLMBR + ECG | 18 | 0.33 | -0.16 | 0.69 | 0.12–0.54 | 0.28 | 0.39 | 0.50 | 0.78 | 1.00 | 2.07 | 0.14 |
| hdPS200 | 18 | 0.24 | -0.25 | 0.64 | 0.12–0.42 | 0.16 | 0.28 | 0.50 | 0.56 | 0.99 | 3.28 | 0.16 |
| hdPS200 + ECG | 18 | 0.13 | -0.36 | 0.56 | -0.05–0.44 | 0.09 | 0.39 | 0.50 | 0.72 | 1.00 | 2.71 | 0.16 |
| hdPS200 + CLMBR | 18 | 0.29 | -0.21 | 0.67 | 0.14–0.38 | 0.20 | 0.22 | 0.44 | 0.72 | 1.00 | 2.78 | 0.15 |
| hdPS200 + CLMBR + ECG | 18 | 0.32 | -0.17 | 0.69 | 0.09–0.46 | 0.21 | 0.33 | 0.56 | 0.72 | 1.00 | 2.39 | 0.13 |
| Clinical PS | 18 | 0.54 | 0.09 | 0.80 | 0.44–0.63 | 0.54 | 0.39 | 0.56 | 0.72 | 0.96 | 2.72 | 0.14 |
| R+ physiology ref | 18 | 0.29 | -0.20 | 0.67 | 0.12–0.44 | 0.16 | 0.44 | 0.50 | 0.78 | 0.95 | 2.80 | 0.16 |

## Paired comparisons (exact sign-flip across trials; r difference CI by resampling trials)

| comparison | trials | closer | mean_diff_abs | p_abs | mean_diff_z2 | p_z2 | diff_pearson_r | r_diff_lo | r_diff_hi | p_mcnemar_estimate |
|---|---|---|---|---|---|---|---|---|---|---|
| CLMBR only vs Unadjusted | 18 | 14/18 | -0.126 | 0.039 | -10.540 | 0.001 | 0.056 | -0.225 | 0.226 | 0.219 |
| CLMBR only vs ECG only | 18 | 12/18 | -0.069 | 0.143 | -4.135 | 0.082 | 0.026 | -0.194 | 0.176 | 0.688 |
| CLMBR + ECG vs CLMBR only | 18 | 9/18 | 0.011 | 0.538 | -0.362 | 0.651 | 0.042 | -0.075 | 0.174 | 0.250 |
| Sparse + CLMBR vs Sparse | 18 | 10/18 | -0.030 | 0.598 | -2.340 | 0.106 | 0.015 | -0.261 | 0.146 | 0.250 |
| Sparse + CLMBR vs Sparse + ECG | 18 | 9/18 | -0.010 | 0.824 | -0.937 | 0.390 | 0.038 | -0.237 | 0.224 | 0.250 |
| Sparse + CLMBR + ECG vs Sparse + CLMBR | 18 | 14/18 | -0.016 | 0.148 | -0.601 | 0.026 | 0.011 | -0.233 | 0.209 | 0.500 |
| hdPS200 + CLMBR vs hdPS200 | 18 | 11/18 | -0.012 | 0.455 | -0.512 | 0.258 | 0.046 | -0.150 | 0.206 | 1.000 |
| hdPS200 + CLMBR + ECG vs hdPS200 + CLMBR | 18 | 13/18 | -0.022 | 0.010 | -0.362 | 0.032 | 0.035 | -0.143 | 0.170 | 0.500 |
| Sparse + CLMBR vs Clinical PS | 18 | 9/18 | 0.014 | 0.582 | -0.173 | 0.751 | -0.218 | -0.590 | -0.014 | 0.250 |
| hdPS200 + CLMBR + ECG vs Clinical PS | 18 | 9/18 | -0.010 | 0.748 | -0.456 | 0.529 | -0.213 | -0.680 | 0.074 | 1.000 |

## Plasmode (80% subsampling): mean |bias| by arm

| PS | base | none | null | phys_only | strong |
|---|---|---|---|---|---|
| Unadjusted | 0.192 | 0.164 | 0.191 | 0.155 | 0.222 |
| ECG only | 0.153 | 0.130 | 0.149 | 0.125 | 0.182 |
| CLMBR only | 0.068 | 0.062 | 0.066 | 0.064 | 0.079 |
| CLMBR + ECG | 0.065 | 0.057 | 0.061 | 0.060 | 0.072 |
| Sparse | 0.059 | 0.041 | 0.060 | 0.044 | 0.084 |
| Sparse + ECG | 0.055 | 0.039 | 0.055 | 0.040 | 0.078 |
| Sparse + CLMBR | 0.033 | 0.020 | 0.031 | 0.032 | 0.048 |
| Sparse + CLMBR + ECG | 0.033 | 0.023 | 0.031 | 0.031 | 0.050 |
| hdPS200 | 0.034 | 0.021 | 0.034 | 0.030 | 0.044 |
| hdPS200 + ECG | 0.034 | 0.021 | 0.031 | 0.031 | 0.044 |
| hdPS200 + CLMBR | 0.031 | 0.019 | 0.030 | 0.032 | 0.043 |
| hdPS200 + CLMBR + ECG | 0.031 | 0.020 | 0.028 | 0.029 | 0.039 |
| Clinical PS | 0.022 | 0.021 | 0.019 | 0.020 | 0.026 |
| R+ physiology ref | 0.019 | 0.017 | 0.016 | 0.018 | 0.025 |

Share of unadjusted bias removed (base): ECG only 20%; CLMBR only 64%; CLMBR + ECG 66%; Sparse 69%; Sparse + ECG 71%; Sparse + CLMBR 83%; Sparse + CLMBR + ECG 83%; hdPS200 82%; hdPS200 + ECG 82%; hdPS200 + CLMBR 84%; hdPS200 + CLMBR + ECG 84%; Clinical PS 88%; R+ physiology ref 90%

Reduction in |bias| (positive = first arm less biased), 95% Monte Carlo CI:

| scenario | comparison | trials | bias_reduction | lo | hi |
|---|---|---|---|---|---|
| base | CLMBR only vs Unadjusted | 18 | 0.1231 | 0.1203 | 0.1253 |
| base | CLMBR only vs ECG only | 18 | 0.0842 | 0.0811 | 0.0872 |
| base | CLMBR + ECG vs CLMBR only | 18 | 0.0037 | 0.0014 | 0.0057 |
| base | Sparse + CLMBR vs Sparse | 18 | 0.0262 | 0.0232 | 0.0284 |
| base | Sparse + CLMBR vs Sparse + ECG | 18 | 0.0222 | 0.0185 | 0.0245 |
| base | Sparse + CLMBR + ECG vs Sparse + CLMBR | 18 | 0.0000 | -0.0026 | 0.0022 |
| base | hdPS200 + CLMBR vs hdPS200 | 18 | 0.0031 | 0.0003 | 0.0055 |
| base | hdPS200 + CLMBR + ECG vs hdPS200 + CLMBR | 18 | 0.0005 | -0.0017 | 0.0029 |
| base | Sparse + CLMBR vs Clinical PS | 18 | -0.0106 | -0.0142 | -0.0077 |
| base | hdPS200 + CLMBR + ECG vs Clinical PS | 18 | -0.0085 | -0.0122 | -0.0037 |
| phys_only | CLMBR only vs Unadjusted | 18 | 0.0912 | 0.0893 | 0.0932 |
| phys_only | CLMBR only vs ECG only | 18 | 0.0614 | 0.0587 | 0.0637 |
| phys_only | CLMBR + ECG vs CLMBR only | 18 | 0.0033 | 0.0010 | 0.0054 |
| phys_only | Sparse + CLMBR vs Sparse | 18 | 0.0128 | 0.0103 | 0.0150 |
| phys_only | Sparse + CLMBR vs Sparse + ECG | 18 | 0.0085 | 0.0052 | 0.0113 |
| phys_only | Sparse + CLMBR + ECG vs Sparse + CLMBR | 18 | 0.0004 | -0.0020 | 0.0027 |
| phys_only | hdPS200 + CLMBR vs hdPS200 | 18 | -0.0028 | -0.0049 | 0.0003 |
| phys_only | hdPS200 + CLMBR + ECG vs hdPS200 + CLMBR | 18 | 0.0039 | 0.0008 | 0.0057 |
| phys_only | Sparse + CLMBR vs Clinical PS | 18 | -0.0119 | -0.0147 | -0.0085 |
| phys_only | hdPS200 + CLMBR + ECG vs Clinical PS | 18 | -0.0090 | -0.0123 | -0.0058 |
| strong | CLMBR only vs Unadjusted | 18 | 0.1430 | 0.1410 | 0.1449 |
| strong | CLMBR only vs ECG only | 18 | 0.1031 | 0.0997 | 0.1057 |
| strong | CLMBR + ECG vs CLMBR only | 18 | 0.0065 | 0.0039 | 0.0086 |
| strong | Sparse + CLMBR vs Sparse | 18 | 0.0369 | 0.0338 | 0.0393 |
| strong | Sparse + CLMBR vs Sparse + ECG | 18 | 0.0305 | 0.0277 | 0.0328 |
| strong | Sparse + CLMBR + ECG vs Sparse + CLMBR | 18 | -0.0022 | -0.0044 | 0.0006 |
| strong | hdPS200 + CLMBR vs hdPS200 | 18 | 0.0011 | -0.0023 | 0.0041 |
| strong | hdPS200 + CLMBR + ECG vs hdPS200 + CLMBR | 18 | 0.0032 | 0.0006 | 0.0053 |
| strong | Sparse + CLMBR vs Clinical PS | 18 | -0.0216 | -0.0237 | -0.0173 |
| strong | hdPS200 + CLMBR + ECG vs Clinical PS | 18 | -0.0135 | -0.0163 | -0.0092 |

