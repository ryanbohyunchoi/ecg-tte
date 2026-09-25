# Directional consistency and closeness to the RCT (post-hoc v1.4 addition G; exploratory)

Point estimates from the full cohort (imputation 1); 95% CIs from 200 paired bootstrap replicates (patients resampled within trial, RCT estimate drawn from its CI).

## all (18 trials: allhat, aristotle, ascot, cabana, carolina, comet, east-afnet4, elite-ii, empa-reg, emperor-preserved, life, ontarget, paradigm-hf-seq, plato, rely, rocket-af, transform-hf, value)

| arm | trials | direction | direction_sigRCT | regulatory | within25 | pearson | pearson_ci | slope | mean_abs |
|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 18 | 0.61 | 0.78 | 0.56 | 0.56 | 0.32 | -0.03–0.60 | 0.88 | 0.27 |
| Demographics | 18 | 0.61 | 0.78 | 0.50 | 0.50 | 0.26 | -0.09–0.60 | 0.68 | 0.27 |
| ECG only | 18 | 0.67 | 0.89 | 0.50 | 0.78 | 0.37 | 0.00–0.65 | 0.73 | 0.21 |
| Demographics + ECG | 18 | 0.83 | 1.00 | 0.50 | 0.78 | 0.45 | -0.07–0.66 | 0.94 | 0.20 |
| Sparse | 18 | 0.67 | 0.89 | 0.44 | 0.78 | 0.33 | -0.16–0.58 | 0.51 | 0.17 |
| Sparse + ECG | 18 | 0.72 | 1.00 | 0.44 | 0.83 | 0.28 | -0.10–0.61 | 0.42 | 0.16 |
| hdPS200 | 18 | 0.72 | 0.78 | 0.28 | 0.72 | 0.23 | -0.14–0.51 | 0.28 | 0.17 |
| hdPS200 + ECG | 18 | 0.67 | 0.78 | 0.44 | 0.83 | 0.19 | -0.18–0.56 | 0.21 | 0.15 |
| Clinical PS | 18 | 0.78 | 1.00 | 0.33 | 0.94 | 0.53 | 0.01–0.67 | 0.70 | 0.14 |
| R+ physiology ref | 18 | 0.72 | 1.00 | 0.44 | 0.78 | 0.29 | -0.11–0.59 | 0.30 | 0.16 |

Differences between arms (first − second; for mean_abs negative favours the first arm):

| comparison | metric | difference | lo | hi | share_boot_favouring |
|---|---|---|---|---|---|
| Sparse + ECG − Sparse | direction | 0.056 | -0.111 | 0.167 | 0.635 |
| Sparse + ECG − Sparse | regulatory | 0.000 | -0.112 | 0.222 | 0.595 |
| Sparse + ECG − Sparse | within25 | 0.056 | -0.056 | 0.278 | 0.665 |
| Sparse + ECG − Sparse | pearson | -0.048 | -0.158 | 0.304 | 0.725 |
| Sparse + ECG − Sparse | mean_abs | -0.011 | -0.063 | 0.010 | 0.885 |
| hdPS200 + ECG − hdPS200 | direction | -0.056 | -0.111 | 0.167 | 0.510 |
| hdPS200 + ECG − hdPS200 | regulatory | 0.167 | -0.112 | 0.224 | 0.585 |
| hdPS200 + ECG − hdPS200 | within25 | 0.111 | -0.111 | 0.222 | 0.600 |
| hdPS200 + ECG − hdPS200 | pearson | -0.038 | -0.283 | 0.294 | 0.540 |
| hdPS200 + ECG − hdPS200 | mean_abs | -0.024 | -0.049 | 0.027 | 0.685 |
| ECG only − Unadjusted | direction | 0.056 | -0.056 | 0.167 | 0.785 |
| ECG only − Unadjusted | regulatory | -0.056 | -0.111 | 0.167 | 0.460 |
| ECG only − Unadjusted | within25 | 0.222 | -0.056 | 0.278 | 0.800 |
| ECG only − Unadjusted | pearson | 0.050 | -0.074 | 0.153 | 0.770 |
| ECG only − Unadjusted | mean_abs | -0.062 | -0.080 | -0.033 | 1.000 |
| Demographics + ECG − Demographics | direction | 0.222 | -0.056 | 0.222 | 0.765 |
| Demographics + ECG − Demographics | regulatory | 0.000 | -0.111 | 0.222 | 0.630 |
| Demographics + ECG − Demographics | within25 | 0.278 | -0.056 | 0.222 | 0.730 |
| Demographics + ECG − Demographics | pearson | 0.188 | -0.084 | 0.241 | 0.810 |
| Demographics + ECG − Demographics | mean_abs | -0.067 | -0.089 | -0.011 | 0.995 |
| Sparse + ECG − Clinical PS | direction | -0.056 | -0.113 | 0.167 | 0.410 |
| Sparse + ECG − Clinical PS | regulatory | 0.111 | -0.111 | 0.278 | 0.705 |
| Sparse + ECG − Clinical PS | within25 | -0.111 | -0.167 | 0.167 | 0.315 |
| Sparse + ECG − Clinical PS | pearson | -0.250 | -0.299 | 0.200 | 0.405 |
| Sparse + ECG − Clinical PS | mean_abs | 0.022 | -0.025 | 0.052 | 0.240 |
| hdPS200 + ECG − Clinical PS | direction | -0.111 | -0.167 | 0.167 | 0.255 |
| hdPS200 + ECG − Clinical PS | regulatory | 0.111 | -0.222 | 0.222 | 0.330 |
| hdPS200 + ECG − Clinical PS | within25 | -0.111 | -0.167 | 0.168 | 0.450 |
| hdPS200 + ECG − Clinical PS | pearson | -0.341 | -0.461 | 0.168 | 0.235 |
| hdPS200 + ECG − Clinical PS | mean_abs | 0.008 | -0.041 | 0.042 | 0.535 |

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

| comparison | metric | difference | lo | hi | share_boot_favouring |
|---|---|---|---|---|---|
| Sparse + ECG − Sparse | direction | 0.000 | -0.125 | 0.125 | 0.180 |
| Sparse + ECG − Sparse | regulatory | 0.000 | -0.250 | 0.250 | 0.360 |
| Sparse + ECG − Sparse | within25 | 0.125 | -0.125 | 0.250 | 0.360 |
| Sparse + ECG − Sparse | pearson | 0.011 | -0.220 | 0.237 | 0.530 |
| Sparse + ECG − Sparse | mean_abs | -0.024 | -0.049 | 0.038 | 0.690 |
| hdPS200 + ECG − hdPS200 | direction | -0.125 | -0.128 | 0.125 | 0.220 |
| hdPS200 + ECG − hdPS200 | regulatory | 0.125 | -0.250 | 0.253 | 0.445 |
| hdPS200 + ECG − hdPS200 | within25 | 0.125 | -0.250 | 0.250 | 0.325 |
| hdPS200 + ECG − hdPS200 | pearson | 0.033 | -0.274 | 0.308 | 0.510 |
| hdPS200 + ECG − hdPS200 | mean_abs | -0.030 | -0.057 | 0.052 | 0.610 |
| ECG only − Unadjusted | direction | 0.000 | -0.125 | 0.125 | 0.155 |
| ECG only − Unadjusted | regulatory | -0.125 | -0.125 | 0.125 | 0.035 |
| ECG only − Unadjusted | within25 | 0.250 | -0.003 | 0.375 | 0.635 |
| ECG only − Unadjusted | pearson | -0.018 | -0.134 | 0.057 | 0.340 |
| ECG only − Unadjusted | mean_abs | -0.064 | -0.080 | -0.006 | 0.995 |
| Demographics + ECG − Demographics | direction | 0.125 | -0.125 | 0.125 | 0.170 |
| Demographics + ECG − Demographics | regulatory | -0.125 | -0.250 | 0.250 | 0.240 |
| Demographics + ECG − Demographics | within25 | 0.375 | -0.125 | 0.250 | 0.480 |
| Demographics + ECG − Demographics | pearson | -0.001 | -0.166 | 0.125 | 0.460 |
| Demographics + ECG − Demographics | mean_abs | -0.058 | -0.079 | 0.016 | 0.905 |
| Sparse + ECG − Clinical PS | direction | -0.125 | -0.125 | 0.250 | 0.295 |
| Sparse + ECG − Clinical PS | regulatory | 0.125 | -0.125 | 0.500 | 0.690 |
| Sparse + ECG − Clinical PS | within25 | 0.000 | -0.128 | 0.253 | 0.330 |
| Sparse + ECG − Clinical PS | pearson | 0.005 | -0.169 | 0.373 | 0.780 |
| Sparse + ECG − Clinical PS | mean_abs | -0.019 | -0.062 | 0.045 | 0.605 |
| hdPS200 + ECG − Clinical PS | direction | -0.125 | -0.128 | 0.250 | 0.320 |
| hdPS200 + ECG − Clinical PS | regulatory | 0.000 | -0.250 | 0.375 | 0.365 |
| hdPS200 + ECG − Clinical PS | within25 | 0.000 | -0.250 | 0.250 | 0.310 |
| hdPS200 + ECG − Clinical PS | pearson | -0.062 | -0.266 | 0.328 | 0.500 |
| hdPS200 + ECG − Clinical PS | mean_abs | -0.010 | -0.056 | 0.055 | 0.510 |

## physiology (8 trials: cabana, comet, east-afnet4, elite-ii, emperor-preserved, life, paradigm-hf-seq, transform-hf)

| arm | trials | direction | direction_sigRCT | regulatory | within25 | pearson | pearson_ci | slope | mean_abs |
|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 8 | 0.50 | 0.60 | 0.62 | 0.62 | 0.27 | -0.24–0.68 | 0.89 | 0.33 |
| Demographics | 8 | 0.50 | 0.60 | 0.62 | 0.38 | 0.21 | -0.29–0.69 | 0.64 | 0.33 |
| ECG only | 8 | 0.62 | 0.80 | 0.62 | 0.75 | 0.39 | -0.13–0.79 | 0.89 | 0.22 |
| Demographics + ECG | 8 | 1.00 | 1.00 | 0.50 | 0.88 | 0.47 | -0.17–0.77 | 1.09 | 0.21 |
| Sparse | 8 | 0.62 | 0.80 | 0.50 | 0.75 | 0.34 | -0.25–0.74 | 0.64 | 0.19 |
| Sparse + ECG | 8 | 0.75 | 1.00 | 0.50 | 0.88 | 0.43 | -0.11–0.79 | 0.79 | 0.18 |
| hdPS200 | 8 | 0.88 | 0.80 | 0.25 | 0.75 | 0.45 | -0.16–0.74 | 0.44 | 0.15 |
| hdPS200 + ECG | 8 | 0.75 | 0.80 | 0.50 | 0.75 | 0.57 | -0.08–0.84 | 0.62 | 0.13 |
| Clinical PS | 8 | 0.88 | 1.00 | 0.38 | 0.88 | 0.44 | -0.15–0.76 | 0.62 | 0.15 |
| R+ physiology ref | 8 | 0.75 | 1.00 | 0.50 | 0.88 | 0.42 | -0.11–0.76 | 0.42 | 0.15 |

Differences between arms (first − second; for mean_abs negative favours the first arm):

| comparison | metric | difference | lo | hi | share_boot_favouring |
|---|---|---|---|---|---|
| Sparse + ECG − Sparse | direction | 0.125 | -0.125 | 0.375 | 0.690 |
| Sparse + ECG − Sparse | regulatory | 0.000 | -0.250 | 0.375 | 0.585 |
| Sparse + ECG − Sparse | within25 | 0.125 | -0.125 | 0.375 | 0.615 |
| Sparse + ECG − Sparse | pearson | 0.088 | -0.087 | 0.301 | 0.895 |
| Sparse + ECG − Sparse | mean_abs | -0.012 | -0.105 | 0.015 | 0.940 |
| hdPS200 + ECG − hdPS200 | direction | -0.125 | -0.125 | 0.375 | 0.530 |
| hdPS200 + ECG − hdPS200 | regulatory | 0.250 | -0.128 | 0.375 | 0.475 |
| hdPS200 + ECG − hdPS200 | within25 | 0.000 | -0.125 | 0.375 | 0.490 |
| hdPS200 + ECG − hdPS200 | pearson | 0.120 | -0.163 | 0.406 | 0.790 |
| hdPS200 + ECG − hdPS200 | mean_abs | -0.022 | -0.071 | 0.037 | 0.725 |
| ECG only − Unadjusted | direction | 0.125 | -0.125 | 0.375 | 0.830 |
| ECG only − Unadjusted | regulatory | 0.000 | -0.125 | 0.250 | 0.465 |
| ECG only − Unadjusted | within25 | 0.125 | -0.125 | 0.375 | 0.715 |
| ECG only − Unadjusted | pearson | 0.120 | 0.016 | 0.203 | 0.985 |
| ECG only − Unadjusted | mean_abs | -0.104 | -0.128 | -0.047 | 1.000 |
| Demographics + ECG − Demographics | direction | 0.500 | 0.000 | 0.375 | 0.830 |
| Demographics + ECG − Demographics | regulatory | -0.125 | -0.128 | 0.375 | 0.550 |
| Demographics + ECG − Demographics | within25 | 0.500 | -0.125 | 0.375 | 0.710 |
| Demographics + ECG − Demographics | pearson | 0.257 | 0.024 | 0.267 | 0.995 |
| Demographics + ECG − Demographics | mean_abs | -0.116 | -0.145 | -0.030 | 1.000 |
| Sparse + ECG − Clinical PS | direction | -0.125 | -0.250 | 0.250 | 0.415 |
| Sparse + ECG − Clinical PS | regulatory | 0.125 | -0.253 | 0.375 | 0.565 |
| Sparse + ECG − Clinical PS | within25 | 0.000 | -0.250 | 0.250 | 0.330 |
| Sparse + ECG − Clinical PS | pearson | -0.013 | -0.159 | 0.223 | 0.545 |
| Sparse + ECG − Clinical PS | mean_abs | 0.031 | -0.037 | 0.072 | 0.270 |
| hdPS200 + ECG − Clinical PS | direction | -0.125 | -0.250 | 0.375 | 0.300 |
| hdPS200 + ECG − Clinical PS | regulatory | 0.125 | -0.375 | 0.250 | 0.275 |
| hdPS200 + ECG − Clinical PS | within25 | -0.125 | -0.250 | 0.375 | 0.450 |
| hdPS200 + ECG − Clinical PS | pearson | 0.127 | -0.281 | 0.515 | 0.760 |
| hdPS200 + ECG − Clinical PS | mean_abs | -0.022 | -0.089 | 0.036 | 0.800 |

## RCT significant (9 trials: aristotle, comet, east-afnet4, empa-reg, emperor-preserved, life, paradigm-hf-seq, plato, rely)

| arm | trials | direction | direction_sigRCT | regulatory | within25 | pearson | pearson_ci | slope | mean_abs |
|---|---|---|---|---|---|---|---|---|---|
| Unadjusted | 9 | 0.78 | 0.78 | 0.78 | 0.67 | 0.57 | 0.18–0.72 | 0.99 | 0.18 |
| Demographics | 9 | 0.78 | 0.78 | 0.67 | 0.56 | 0.41 | 0.05–0.67 | 0.67 | 0.18 |
| ECG only | 9 | 0.89 | 0.89 | 0.67 | 0.89 | 0.65 | 0.17–0.82 | 0.84 | 0.13 |
| Demographics + ECG | 9 | 1.00 | 1.00 | 0.56 | 0.89 | 0.66 | 0.12–0.83 | 0.87 | 0.12 |
| Sparse | 9 | 0.89 | 0.89 | 0.56 | 0.89 | 0.64 | -0.02–0.72 | 0.59 | 0.11 |
| Sparse + ECG | 9 | 1.00 | 1.00 | 0.56 | 0.89 | 0.45 | -0.10–0.84 | 0.39 | 0.11 |
| hdPS200 | 9 | 0.78 | 0.78 | 0.22 | 0.78 | 0.22 | -0.36–0.65 | 0.18 | 0.15 |
| hdPS200 + ECG | 9 | 0.78 | 0.78 | 0.44 | 0.78 | 0.13 | -0.26–0.77 | 0.14 | 0.15 |
| Clinical PS | 9 | 1.00 | 1.00 | 0.33 | 1.00 | 0.74 | 0.02–0.85 | 0.76 | 0.10 |
| R+ physiology ref | 9 | 1.00 | 1.00 | 0.56 | 0.89 | 0.50 | -0.08–0.86 | 0.40 | 0.12 |

Differences between arms (first − second; for mean_abs negative favours the first arm):

| comparison | metric | difference | lo | hi | share_boot_favouring |
|---|---|---|---|---|---|
| Sparse + ECG − Sparse | direction | 0.111 | -0.111 | 0.225 | 0.610 |
| Sparse + ECG − Sparse | regulatory | 0.000 | -0.222 | 0.333 | 0.520 |
| Sparse + ECG − Sparse | within25 | 0.000 | -0.111 | 0.333 | 0.540 |
| Sparse + ECG − Sparse | pearson | -0.194 | -0.323 | 0.463 | 0.675 |
| Sparse + ECG − Sparse | mean_abs | 0.003 | -0.066 | 0.035 | 0.705 |
| hdPS200 + ECG − hdPS200 | direction | 0.000 | -0.111 | 0.222 | 0.520 |
| hdPS200 + ECG − hdPS200 | regulatory | 0.222 | -0.222 | 0.333 | 0.455 |
| hdPS200 + ECG − hdPS200 | within25 | 0.000 | -0.222 | 0.222 | 0.465 |
| hdPS200 + ECG − hdPS200 | pearson | -0.083 | -0.358 | 0.493 | 0.630 |
| hdPS200 + ECG − hdPS200 | mean_abs | -0.003 | -0.059 | 0.045 | 0.575 |
| ECG only − Unadjusted | direction | 0.111 | 0.000 | 0.222 | 0.800 |
| ECG only − Unadjusted | regulatory | -0.111 | -0.222 | 0.222 | 0.330 |
| ECG only − Unadjusted | within25 | 0.222 | -0.111 | 0.444 | 0.710 |
| ECG only − Unadjusted | pearson | 0.079 | -0.208 | 0.244 | 0.640 |
| ECG only − Unadjusted | mean_abs | -0.044 | -0.080 | 0.002 | 0.960 |
| Demographics + ECG − Demographics | direction | 0.222 | 0.000 | 0.225 | 0.915 |
| Demographics + ECG − Demographics | regulatory | -0.111 | -0.222 | 0.333 | 0.545 |
| Demographics + ECG − Demographics | within25 | 0.333 | -0.111 | 0.333 | 0.660 |
| Demographics + ECG − Demographics | pearson | 0.246 | -0.198 | 0.363 | 0.785 |
| Demographics + ECG − Demographics | mean_abs | -0.060 | -0.100 | 0.018 | 0.900 |
| Sparse + ECG − Clinical PS | direction | 0.000 | -0.222 | 0.222 | 0.395 |
| Sparse + ECG − Clinical PS | regulatory | 0.222 | -0.111 | 0.444 | 0.750 |
| Sparse + ECG − Clinical PS | within25 | -0.111 | -0.225 | 0.222 | 0.290 |
| Sparse + ECG − Clinical PS | pearson | -0.295 | -0.516 | 0.367 | 0.455 |
| Sparse + ECG − Clinical PS | mean_abs | 0.014 | -0.057 | 0.068 | 0.425 |
| hdPS200 + ECG − Clinical PS | direction | -0.222 | -0.333 | 0.111 | 0.140 |
| hdPS200 + ECG − Clinical PS | regulatory | 0.111 | -0.444 | 0.222 | 0.130 |
| hdPS200 + ECG − Clinical PS | within25 | -0.222 | -0.333 | 0.222 | 0.195 |
| hdPS200 + ECG − Clinical PS | pearson | -0.610 | -0.728 | 0.230 | 0.145 |
| hdPS200 + ECG − Clinical PS | mean_abs | 0.054 | -0.035 | 0.086 | 0.205 |

Definitions: direction = same side of HR 1 as the RCT; direction_sigRCT = same, among RCTs whose CI excludes 1; regulatory = same significance and direction (RCT-DUPLICATE); within25 = emulated HR within 0.8–1.25× the RCT HR; slope = calibration slope of emulated on RCT log HR (1 = ideal).

