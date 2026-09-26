# Directional consistency and closeness to the RCT (post-hoc v1.4 addition G; exploratory)

Point estimates from the full cohort (imputation 1). Inference for arm differences: exact McNemar (binary metrics) and sign-flip (mean |Δ|) tests across trials. Bootstrap intervals (lo, hi) are descriptive only: re-matching on resamples with duplicate patients is not valid for matching estimators (audit 2026-09-25).

## all (18 trials: allhat, aristotle, ascot, cabana-v2, carolina, comet, east-afnet4, elite-ii, empa-reg, emperor-preserved-v2, life, ontarget, paradigm-hf-seq, plato, rely, rocket-af, transform-hf, value)

| arm | trials | direction | direction_sigRCT | regulatory | within25 | pearson | pearson_ci | slope | mean_abs |
|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 18 | 0.61 | 0.78 | 0.56 | 0.56 | 0.31 | -0.09–0.57 | 0.89 | 0.28 |
| Demographics | 18 | 0.61 | 0.78 | 0.50 | 0.50 | 0.27 | -0.12–0.54 | 0.70 | 0.27 |
| ECG only | 18 | 0.67 | 0.89 | 0.50 | 0.78 | 0.34 | -0.04–0.60 | 0.74 | 0.22 |
| Demographics + ECG | 18 | 0.83 | 1.00 | 0.50 | 0.78 | 0.42 | -0.07–0.56 | 0.94 | 0.21 |
| Sparse | 18 | 0.67 | 0.89 | 0.44 | 0.78 | 0.30 | -0.17–0.51 | 0.54 | 0.18 |
| Sparse + ECG | 18 | 0.72 | 1.00 | 0.44 | 0.83 | 0.28 | -0.10–0.62 | 0.42 | 0.16 |
| hdPS200 | 18 | 0.72 | 0.78 | 0.28 | 0.78 | 0.24 | -0.14–0.48 | 0.28 | 0.16 |
| hdPS200 + ECG | 18 | 0.67 | 0.78 | 0.39 | 0.83 | 0.13 | -0.17–0.55 | 0.15 | 0.16 |
| Clinical PS | 18 | 0.78 | 1.00 | 0.39 | 0.94 | 0.54 | -0.05–0.64 | 0.72 | 0.14 |
| R+ physiology ref | 18 | 0.72 | 1.00 | 0.44 | 0.78 | 0.29 | -0.17–0.55 | 0.33 | 0.16 |

Differences between arms (first − second; for mean_abs negative favours the first arm):

| comparison | metric | difference | exact_test | lo | hi |
|---|---|---|---|---|---|
| Sparse + ECG − Sparse | direction | 0.056 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.111 | 0.167 |
| Sparse + ECG − Sparse | regulatory | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.111 | 0.222 |
| Sparse + ECG − Sparse | within25 | 0.056 | McNemar exact: 2 gained vs 1 lost, p = 1.000 | -0.057 | 0.278 |
| Sparse + ECG − Sparse | pearson | -0.023 |  | -0.146 | 0.256 |
| Sparse + ECG − Sparse | mean_abs | -0.020 | sign-flip p = 0.264 | -0.063 | 0.015 |
| hdPS200 + ECG − hdPS200 | direction | -0.056 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.111 | 0.167 |
| hdPS200 + ECG − hdPS200 | regulatory | 0.111 | McNemar exact: 2 gained vs 0 lost, p = 0.500 | -0.167 | 0.222 |
| hdPS200 + ECG − hdPS200 | within25 | 0.056 | McNemar exact: 2 gained vs 1 lost, p = 1.000 | -0.111 | 0.222 |
| hdPS200 + ECG − hdPS200 | pearson | -0.113 |  | -0.264 | 0.255 |
| hdPS200 + ECG − hdPS200 | mean_abs | -0.002 | sign-flip p = 0.916 | -0.047 | 0.025 |
| ECG only − Unadjusted | direction | 0.056 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.056 | 0.167 |
| ECG only − Unadjusted | regulatory | -0.056 | McNemar exact: 1 gained vs 2 lost, p = 1.000 | -0.111 | 0.167 |
| ECG only − Unadjusted | within25 | 0.222 | McNemar exact: 4 gained vs 0 lost, p = 0.125 | -0.056 | 0.278 |
| ECG only − Unadjusted | pearson | 0.030 |  | -0.072 | 0.137 |
| ECG only − Unadjusted | mean_abs | -0.057 | sign-flip p = 0.033 | -0.078 | -0.027 |
| Demographics + ECG − Demographics | direction | 0.222 | McNemar exact: 4 gained vs 0 lost, p = 0.125 | -0.056 | 0.222 |
| Demographics + ECG − Demographics | regulatory | 0.000 | McNemar exact: 1 gained vs 1 lost, p = 1.000 | -0.111 | 0.222 |
| Demographics + ECG − Demographics | within25 | 0.278 | McNemar exact: 6 gained vs 1 lost, p = 0.125 | -0.056 | 0.222 |
| Demographics + ECG − Demographics | pearson | 0.149 |  | -0.073 | 0.201 |
| Demographics + ECG − Demographics | mean_abs | -0.058 | sign-flip p = 0.035 | -0.089 | -0.014 |
| Sparse + ECG − Clinical PS | direction | -0.056 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.111 | 0.167 |
| Sparse + ECG − Clinical PS | regulatory | 0.056 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.111 | 0.278 |
| Sparse + ECG − Clinical PS | within25 | -0.111 | McNemar exact: 0 gained vs 2 lost, p = 0.500 | -0.222 | 0.167 |
| Sparse + ECG − Clinical PS | pearson | -0.257 |  | -0.307 | 0.154 |
| Sparse + ECG − Clinical PS | mean_abs | 0.024 | sign-flip p = 0.386 | -0.021 | 0.057 |
| hdPS200 + ECG − Clinical PS | direction | -0.111 | McNemar exact: 1 gained vs 3 lost, p = 0.625 | -0.167 | 0.167 |
| hdPS200 + ECG − Clinical PS | regulatory | 0.000 | McNemar exact: 1 gained vs 1 lost, p = 1.000 | -0.224 | 0.167 |
| hdPS200 + ECG − Clinical PS | within25 | -0.111 | McNemar exact: 0 gained vs 2 lost, p = 0.500 | -0.167 | 0.167 |
| hdPS200 + ECG − Clinical PS | pearson | -0.406 |  | -0.419 | 0.169 |
| hdPS200 + ECG − Clinical PS | mean_abs | 0.022 | sign-flip p = 0.640 | -0.039 | 0.041 |

## close emulation (8 trials: aristotle, carolina, comet, elite-ii, life, ontarget, plato, rocket-af)

| arm | trials | direction | direction_sigRCT | regulatory | within25 | pearson | pearson_ci | slope | mean_abs |
|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 8 | 0.75 | 1.00 | 0.75 | 0.62 | 0.85 | 0.47–0.94 | 1.83 | 0.23 |
| Demographics | 8 | 0.75 | 1.00 | 0.75 | 0.50 | 0.79 | 0.40–0.93 | 1.54 | 0.22 |
| ECG only | 8 | 0.75 | 1.00 | 0.62 | 0.88 | 0.83 | 0.45–0.94 | 1.48 | 0.16 |
| Demographics + ECG | 8 | 0.88 | 1.00 | 0.62 | 0.88 | 0.79 | 0.35–0.91 | 1.45 | 0.16 |
| Sparse | 8 | 0.75 | 1.00 | 0.62 | 0.88 | 0.87 | 0.38–0.93 | 0.96 | 0.11 |
| Sparse + ECG | 8 | 0.75 | 1.00 | 0.62 | 1.00 | 0.88 | 0.34–0.92 | 0.92 | 0.08 |
| hdPS200 | 8 | 0.88 | 1.00 | 0.38 | 0.88 | 0.78 | 0.20–0.91 | 0.89 | 0.12 |
| hdPS200 + ECG | 8 | 0.75 | 1.00 | 0.50 | 1.00 | 0.81 | 0.20–0.90 | 0.76 | 0.09 |
| Clinical PS | 8 | 0.88 | 1.00 | 0.50 | 1.00 | 0.87 | 0.22–0.89 | 0.98 | 0.10 |
| R+ physiology ref | 8 | 0.75 | 1.00 | 0.62 | 1.00 | 0.83 | 0.10–0.89 | 0.79 | 0.11 |

Differences between arms (first − second; for mean_abs negative favours the first arm):

| comparison | metric | difference | exact_test | lo | hi |
|---|---|---|---|---|---|
| Sparse + ECG − Sparse | direction | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.125 | 0.125 |
| Sparse + ECG − Sparse | regulatory | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.250 | 0.250 |
| Sparse + ECG − Sparse | within25 | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.125 | 0.250 |
| Sparse + ECG − Sparse | pearson | 0.011 |  | -0.220 | 0.237 |
| Sparse + ECG − Sparse | mean_abs | -0.024 | sign-flip p = 0.156 | -0.049 | 0.038 |
| hdPS200 + ECG − hdPS200 | direction | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.128 | 0.125 |
| hdPS200 + ECG − hdPS200 | regulatory | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.250 | 0.253 |
| hdPS200 + ECG − hdPS200 | within25 | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.250 | 0.250 |
| hdPS200 + ECG − hdPS200 | pearson | 0.033 |  | -0.274 | 0.308 |
| hdPS200 + ECG − hdPS200 | mean_abs | -0.030 | sign-flip p = 0.227 | -0.057 | 0.052 |
| ECG only − Unadjusted | direction | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.125 | 0.125 |
| ECG only − Unadjusted | regulatory | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.125 | 0.125 |
| ECG only − Unadjusted | within25 | 0.250 | McNemar exact: 2 gained vs 0 lost, p = 0.500 | -0.003 | 0.375 |
| ECG only − Unadjusted | pearson | -0.018 |  | -0.134 | 0.057 |
| ECG only − Unadjusted | mean_abs | -0.064 | sign-flip p = 0.016 | -0.080 | -0.006 |
| Demographics + ECG − Demographics | direction | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.125 | 0.125 |
| Demographics + ECG − Demographics | regulatory | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.250 | 0.250 |
| Demographics + ECG − Demographics | within25 | 0.375 | McNemar exact: 3 gained vs 0 lost, p = 0.250 | -0.125 | 0.250 |
| Demographics + ECG − Demographics | pearson | -0.001 |  | -0.166 | 0.125 |
| Demographics + ECG − Demographics | mean_abs | -0.058 | sign-flip p = 0.164 | -0.079 | 0.016 |
| Sparse + ECG − Clinical PS | direction | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.125 | 0.250 |
| Sparse + ECG − Clinical PS | regulatory | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.125 | 0.500 |
| Sparse + ECG − Clinical PS | within25 | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.128 | 0.253 |
| Sparse + ECG − Clinical PS | pearson | 0.005 |  | -0.169 | 0.373 |
| Sparse + ECG − Clinical PS | mean_abs | -0.019 | sign-flip p = 0.469 | -0.062 | 0.045 |
| hdPS200 + ECG − Clinical PS | direction | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.128 | 0.250 |
| hdPS200 + ECG − Clinical PS | regulatory | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.250 | 0.375 |
| hdPS200 + ECG − Clinical PS | within25 | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.250 | 0.250 |
| hdPS200 + ECG − Clinical PS | pearson | -0.062 |  | -0.266 | 0.328 |
| hdPS200 + ECG − Clinical PS | mean_abs | -0.010 | sign-flip p = 0.594 | -0.056 | 0.055 |

## physiology (8 trials: cabana-v2, comet, east-afnet4, elite-ii, emperor-preserved-v2, life, paradigm-hf-seq, transform-hf)

| arm | trials | direction | direction_sigRCT | regulatory | within25 | pearson | pearson_ci | slope | mean_abs |
|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 8 | 0.50 | 0.60 | 0.62 | 0.62 | 0.26 | -0.28–0.65 | 0.92 | 0.34 |
| Demographics | 8 | 0.50 | 0.60 | 0.62 | 0.38 | 0.23 | -0.32–0.59 | 0.68 | 0.32 |
| ECG only | 8 | 0.62 | 0.80 | 0.62 | 0.75 | 0.35 | -0.19–0.76 | 0.93 | 0.25 |
| Demographics + ECG | 8 | 1.00 | 1.00 | 0.50 | 0.88 | 0.43 | -0.20–0.70 | 1.10 | 0.23 |
| Sparse | 8 | 0.62 | 0.80 | 0.50 | 0.75 | 0.32 | -0.26–0.66 | 0.72 | 0.21 |
| Sparse + ECG | 8 | 0.75 | 1.00 | 0.50 | 0.88 | 0.43 | -0.15–0.75 | 0.80 | 0.18 |
| hdPS200 | 8 | 0.88 | 0.80 | 0.25 | 0.88 | 0.55 | -0.26–0.71 | 0.44 | 0.13 |
| hdPS200 + ECG | 8 | 0.75 | 0.80 | 0.38 | 0.75 | 0.45 | -0.03–0.80 | 0.48 | 0.15 |
| Clinical PS | 8 | 0.88 | 1.00 | 0.50 | 0.88 | 0.46 | -0.16–0.76 | 0.67 | 0.14 |
| R+ physiology ref | 8 | 0.75 | 1.00 | 0.50 | 0.88 | 0.41 | -0.23–0.77 | 0.50 | 0.16 |

Differences between arms (first − second; for mean_abs negative favours the first arm):

| comparison | metric | difference | exact_test | lo | hi |
|---|---|---|---|---|---|
| Sparse + ECG − Sparse | direction | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.125 | 0.375 |
| Sparse + ECG − Sparse | regulatory | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.125 | 0.375 |
| Sparse + ECG − Sparse | within25 | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.125 | 0.375 |
| Sparse + ECG − Sparse | pearson | 0.107 |  | -0.066 | 0.235 |
| Sparse + ECG − Sparse | mean_abs | -0.032 | sign-flip p = 0.273 | -0.101 | 0.017 |
| hdPS200 + ECG − hdPS200 | direction | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.128 | 0.375 |
| hdPS200 + ECG − hdPS200 | regulatory | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.250 | 0.250 |
| hdPS200 + ECG − hdPS200 | within25 | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.128 | 0.250 |
| hdPS200 + ECG − hdPS200 | pearson | -0.098 |  | -0.153 | 0.407 |
| hdPS200 + ECG − hdPS200 | mean_abs | 0.028 | sign-flip p = 0.367 | -0.081 | 0.044 |
| ECG only − Unadjusted | direction | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.125 | 0.375 |
| ECG only − Unadjusted | regulatory | 0.000 | McNemar exact: 1 gained vs 1 lost, p = 1.000 | -0.125 | 0.250 |
| ECG only − Unadjusted | within25 | 0.125 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.125 | 0.375 |
| ECG only − Unadjusted | pearson | 0.090 |  | 0.006 | 0.176 |
| ECG only − Unadjusted | mean_abs | -0.092 | sign-flip p = 0.055 | -0.120 | -0.043 |
| Demographics + ECG − Demographics | direction | 0.500 | McNemar exact: 4 gained vs 0 lost, p = 0.125 | 0.000 | 0.375 |
| Demographics + ECG − Demographics | regulatory | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.250 | 0.253 |
| Demographics + ECG − Demographics | within25 | 0.500 | McNemar exact: 4 gained vs 0 lost, p = 0.125 | -0.125 | 0.375 |
| Demographics + ECG − Demographics | pearson | 0.201 |  | 0.011 | 0.232 |
| Demographics + ECG − Demographics | mean_abs | -0.095 | sign-flip p = 0.055 | -0.137 | -0.040 |
| Sparse + ECG − Clinical PS | direction | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.250 | 0.250 |
| Sparse + ECG − Clinical PS | regulatory | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.250 | 0.375 |
| Sparse + ECG − Clinical PS | within25 | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.250 | 0.250 |
| Sparse + ECG − Clinical PS | pearson | -0.031 |  | -0.155 | 0.186 |
| Sparse + ECG − Clinical PS | mean_abs | 0.036 | sign-flip p = 0.258 | -0.028 | 0.077 |
| hdPS200 + ECG − Clinical PS | direction | -0.125 | McNemar exact: 1 gained vs 2 lost, p = 1.000 | -0.250 | 0.375 |
| hdPS200 + ECG − Clinical PS | regulatory | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.375 | 0.250 |
| hdPS200 + ECG − Clinical PS | within25 | -0.125 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.250 | 0.250 |
| hdPS200 + ECG − Clinical PS | pearson | -0.007 |  | -0.164 | 0.396 |
| hdPS200 + ECG − Clinical PS | mean_abs | 0.009 | sign-flip p = 0.844 | -0.090 | 0.029 |

## RCT significant (9 trials: aristotle, comet, east-afnet4, empa-reg, emperor-preserved-v2, life, paradigm-hf-seq, plato, rely)

| arm | trials | direction | direction_sigRCT | regulatory | within25 | pearson | pearson_ci | slope | mean_abs |
|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 9 | 0.78 | 0.78 | 0.78 | 0.67 | 0.57 | 0.18–0.71 | 0.99 | 0.18 |
| Demographics | 9 | 0.78 | 0.78 | 0.67 | 0.56 | 0.42 | 0.01–0.66 | 0.69 | 0.18 |
| ECG only | 9 | 0.89 | 0.89 | 0.67 | 0.89 | 0.64 | 0.16–0.82 | 0.83 | 0.14 |
| Demographics + ECG | 9 | 1.00 | 1.00 | 0.56 | 0.89 | 0.65 | 0.11–0.82 | 0.86 | 0.12 |
| Sparse | 9 | 0.89 | 0.89 | 0.56 | 0.89 | 0.64 | -0.02–0.72 | 0.59 | 0.10 |
| Sparse + ECG | 9 | 1.00 | 1.00 | 0.56 | 0.89 | 0.45 | -0.07–0.82 | 0.39 | 0.11 |
| hdPS200 | 9 | 0.78 | 0.78 | 0.22 | 0.78 | 0.23 | -0.33–0.65 | 0.19 | 0.15 |
| hdPS200 + ECG | 9 | 0.78 | 0.78 | 0.33 | 0.78 | 0.09 | -0.28–0.74 | 0.08 | 0.17 |
| Clinical PS | 9 | 1.00 | 1.00 | 0.44 | 1.00 | 0.75 | -0.00–0.88 | 0.77 | 0.09 |
| R+ physiology ref | 9 | 1.00 | 1.00 | 0.56 | 0.89 | 0.51 | -0.08–0.82 | 0.41 | 0.11 |

Differences between arms (first − second; for mean_abs negative favours the first arm):

| comparison | metric | difference | exact_test | lo | hi |
|---|---|---|---|---|---|
| Sparse + ECG − Sparse | direction | 0.111 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.111 | 0.222 |
| Sparse + ECG − Sparse | regulatory | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.222 | 0.333 |
| Sparse + ECG − Sparse | within25 | 0.000 | McNemar exact: 1 gained vs 1 lost, p = 1.000 | -0.114 | 0.333 |
| Sparse + ECG − Sparse | pearson | -0.196 |  | -0.317 | 0.453 |
| Sparse + ECG − Sparse | mean_abs | 0.005 | sign-flip p = 0.883 | -0.067 | 0.038 |
| hdPS200 + ECG − hdPS200 | direction | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.114 | 0.225 |
| hdPS200 + ECG − hdPS200 | regulatory | 0.111 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.222 | 0.333 |
| hdPS200 + ECG − hdPS200 | within25 | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.222 | 0.222 |
| hdPS200 + ECG − hdPS200 | pearson | -0.145 |  | -0.365 | 0.487 |
| hdPS200 + ECG − hdPS200 | mean_abs | 0.025 | sign-flip p = 0.324 | -0.065 | 0.043 |
| ECG only − Unadjusted | direction | 0.111 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.003 | 0.222 |
| ECG only − Unadjusted | regulatory | -0.111 | McNemar exact: 1 gained vs 2 lost, p = 1.000 | -0.222 | 0.222 |
| ECG only − Unadjusted | within25 | 0.222 | McNemar exact: 2 gained vs 0 lost, p = 0.500 | -0.111 | 0.444 |
| ECG only − Unadjusted | pearson | 0.075 |  | -0.196 | 0.234 |
| ECG only − Unadjusted | mean_abs | -0.042 | sign-flip p = 0.242 | -0.080 | 0.001 |
| Demographics + ECG − Demographics | direction | 0.222 | McNemar exact: 2 gained vs 0 lost, p = 0.500 | 0.000 | 0.222 |
| Demographics + ECG − Demographics | regulatory | -0.111 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.225 | 0.333 |
| Demographics + ECG − Demographics | within25 | 0.333 | McNemar exact: 4 gained vs 1 lost, p = 0.375 | -0.111 | 0.333 |
| Demographics + ECG − Demographics | pearson | 0.233 |  | -0.230 | 0.376 |
| Demographics + ECG − Demographics | mean_abs | -0.060 | sign-flip p = 0.125 | -0.107 | 0.013 |
| Sparse + ECG − Clinical PS | direction | 0.000 | McNemar exact: 0 gained vs 0 lost, p = 1.000 | -0.114 | 0.222 |
| Sparse + ECG − Clinical PS | regulatory | 0.111 | McNemar exact: 1 gained vs 0 lost, p = 1.000 | -0.111 | 0.444 |
| Sparse + ECG − Clinical PS | within25 | -0.111 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.333 | 0.222 |
| Sparse + ECG − Clinical PS | pearson | -0.306 |  | -0.504 | 0.316 |
| Sparse + ECG − Clinical PS | mean_abs | 0.019 | sign-flip p = 0.785 | -0.056 | 0.067 |
| hdPS200 + ECG − Clinical PS | direction | -0.222 | McNemar exact: 0 gained vs 2 lost, p = 0.500 | -0.333 | 0.111 |
| hdPS200 + ECG − Clinical PS | regulatory | -0.111 | McNemar exact: 0 gained vs 1 lost, p = 1.000 | -0.444 | 0.222 |
| hdPS200 + ECG − Clinical PS | within25 | -0.222 | McNemar exact: 0 gained vs 2 lost, p = 0.500 | -0.333 | 0.222 |
| hdPS200 + ECG − Clinical PS | pearson | -0.666 |  | -0.753 | 0.190 |
| hdPS200 + ECG − Clinical PS | mean_abs | 0.082 | sign-flip p = 0.207 | -0.032 | 0.090 |

Definitions: direction = same side of HR 1 as the RCT; direction_sigRCT = same, among RCTs whose CI excludes 1; regulatory = same significance and direction (RCT-DUPLICATE); within25 = emulated HR within 0.8–1.25× the RCT HR; slope = calibration slope of emulated on RCT log HR (1 = ideal).

