# v1.3 exploratory robustness program — trial set: combined (18 trials)

Trials: comet, paradigm-hf-seq, transform-hf, elite-ii, life, plato, aristotle, rocket-af, rely, allhat, emperor-preserved, east-afnet4, cabana, ontarget, value, ascot, empa-reg, carolina

All analyses are exploratory (registered 2026-09-25 after phase 2; tag protocol-v1.3).

## I1 Plasmode simulation — resampled cohort, PS and matching refitted per replicate (deviation 6; decides rule 1)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.008 | 0.020 | 0.092 | 0.945 |
| R clinical | 18 | -0.010 | 0.020 | 0.090 | 0.941 |
| M3 hdPS200 | 18 | -0.012 | 0.033 | 0.098 | 0.928 |
| M4 hdPS200+ECG | 18 | -0.011 | 0.035 | 0.101 | 0.922 |
| M1 sparse | 18 | -0.034 | 0.057 | 0.110 | 0.842 |
| M2 sparse+ECG | 18 | -0.028 | 0.053 | 0.107 | 0.851 |
| M0 unadjusted | 18 | -0.104 | 0.189 | 0.211 | 0.379 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.015 | 0.019 | 0.093 | 0.947 |
| R clinical | 18 | -0.015 | 0.020 | 0.090 | 0.950 |
| M3 hdPS200 | 18 | -0.025 | 0.036 | 0.100 | 0.924 |
| M4 hdPS200+ECG | 18 | -0.024 | 0.033 | 0.101 | 0.923 |
| M1 sparse | 18 | -0.031 | 0.039 | 0.100 | 0.899 |
| M2 sparse+ECG | 18 | -0.031 | 0.039 | 0.098 | 0.911 |
| M0 unadjusted | 18 | -0.100 | 0.150 | 0.176 | 0.525 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.014 | 0.019 | 0.089 | 0.950 |
| R clinical | 18 | -0.013 | 0.022 | 0.087 | 0.943 |
| M3 hdPS200 | 18 | -0.023 | 0.046 | 0.103 | 0.903 |
| M4 hdPS200+ECG | 18 | -0.021 | 0.046 | 0.106 | 0.897 |
| M1 sparse | 18 | -0.053 | 0.081 | 0.125 | 0.777 |
| M2 sparse+ECG | 18 | -0.048 | 0.074 | 0.121 | 0.792 |
| M0 unadjusted | 18 | -0.127 | 0.217 | 0.236 | 0.353 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.010 | 0.014 | 0.092 | 0.947 |
| R clinical | 18 | -0.012 | 0.019 | 0.088 | 0.952 |
| M3 hdPS200 | 18 | -0.005 | 0.022 | 0.096 | 0.935 |
| M4 hdPS200+ECG | 18 | -0.003 | 0.023 | 0.097 | 0.936 |
| M1 sparse | 18 | -0.019 | 0.040 | 0.098 | 0.899 |
| M2 sparse+ECG | 18 | -0.016 | 0.037 | 0.099 | 0.896 |
| M0 unadjusted | 18 | -0.086 | 0.164 | 0.186 | 0.430 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.015 | 0.018 | 0.086 | 0.948 |
| R clinical | 18 | -0.013 | 0.019 | 0.086 | 0.945 |
| M3 hdPS200 | 18 | -0.013 | 0.035 | 0.095 | 0.918 |
| M4 hdPS200+ECG | 18 | -0.012 | 0.034 | 0.096 | 0.922 |
| M1 sparse | 18 | -0.037 | 0.061 | 0.108 | 0.833 |
| M2 sparse+ECG | 18 | -0.032 | 0.054 | 0.104 | 0.848 |
| M0 unadjusted | 18 | -0.104 | 0.189 | 0.209 | 0.354 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 18 | 0.004 | 0.002 | 0.006 | 0.075 |
| base | C2 | 18 | -0.002 | -0.005 | -0.000 | -0.069 |
| base | sparse+noise32-vs-sparse | 18 | -0.001 | -0.003 | 0.001 | -0.022 |
| base | sparse+shufECG-vs-sparse | 18 | -0.002 | -0.004 | -0.000 | -0.039 |
| base | sparse+ECG-vs-sparse+shufECG | 18 | 0.007 | 0.004 | 0.008 | 0.110 |
| base | hdPS200+noise32-vs-hdPS200 | 18 | -0.002 | -0.004 | 0.000 | -0.052 |
| base | hdPS200+shufECG-vs-hdPS200 | 18 | -0.000 | -0.003 | 0.002 | -0.003 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 18 | -0.002 | -0.004 | 0.000 | -0.065 |
| none | C1 | 18 | 0.003 | 0.000 | 0.004 | 0.073 |
| none | C2 | 18 | -0.001 | -0.004 | 0.002 | -0.061 |
| none | sparse+noise32-vs-sparse | 18 | 0.000 | -0.002 | 0.002 | 0.012 |
| none | sparse+shufECG-vs-sparse | 18 | -0.003 | -0.005 | -0.001 | -0.065 |
| none | sparse+ECG-vs-sparse+shufECG | 18 | 0.006 | 0.003 | 0.007 | 0.130 |
| none | hdPS200+noise32-vs-hdPS200 | 18 | -0.000 | -0.003 | 0.002 | -0.000 |
| none | hdPS200+shufECG-vs-hdPS200 | 18 | -0.002 | -0.005 | 0.001 | -0.104 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.001 | -0.002 | 0.003 | 0.039 |
| null | C1 | 18 | 0.007 | 0.005 | 0.009 | 0.119 |
| null | C2 | 18 | 0.001 | -0.001 | 0.003 | 0.024 |
| null | sparse+noise32-vs-sparse | 18 | -0.000 | -0.002 | 0.002 | -0.004 |
| null | sparse+shufECG-vs-sparse | 18 | -0.001 | -0.003 | 0.001 | -0.014 |
| null | sparse+ECG-vs-sparse+shufECG | 18 | 0.008 | 0.006 | 0.010 | 0.131 |
| null | hdPS200+noise32-vs-hdPS200 | 18 | -0.000 | -0.002 | 0.002 | -0.011 |
| null | hdPS200+shufECG-vs-hdPS200 | 18 | 0.001 | -0.001 | 0.003 | 0.043 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 18 | -0.001 | -0.003 | 0.002 | -0.020 |
| phys_only | C1 | 18 | 0.000 | -0.002 | 0.002 | 0.003 |
| phys_only | C2 | 18 | 0.003 | -0.000 | 0.005 | 0.087 |
| phys_only | sparse+noise32-vs-sparse | 18 | 0.002 | -0.000 | 0.004 | 0.038 |
| phys_only | sparse+shufECG-vs-sparse | 18 | 0.001 | -0.002 | 0.003 | 0.015 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 18 | -0.000 | -0.003 | 0.002 | -0.012 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 18 | 0.001 | -0.001 | 0.004 | 0.040 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 18 | 0.002 | -0.001 | 0.004 | 0.057 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.001 | -0.001 | 0.003 | 0.032 |
| strong | C1 | 18 | 0.007 | 0.005 | 0.009 | 0.087 |
| strong | C2 | 18 | -0.000 | -0.002 | 0.002 | -0.008 |
| strong | sparse+noise32-vs-sparse | 18 | 0.001 | -0.002 | 0.003 | 0.009 |
| strong | sparse+shufECG-vs-sparse | 18 | -0.003 | -0.005 | -0.001 | -0.032 |
| strong | sparse+ECG-vs-sparse+shufECG | 18 | 0.010 | 0.007 | 0.012 | 0.115 |
| strong | hdPS200+noise32-vs-hdPS200 | 18 | -0.002 | -0.004 | 0.000 | -0.043 |
| strong | hdPS200+shufECG-vs-hdPS200 | 18 | -0.003 | -0.005 | -0.001 | -0.068 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.003 | 0.000 | 0.005 | 0.056 |

## I1 Plasmode simulation — fixed matched sets, as registered (flawed: conflates chance imbalance with bias)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.011 | 0.021 | 0.090 | 0.948 |
| R clinical | 18 | -0.014 | 0.029 | 0.089 | 0.953 |
| M3 hdPS200 | 18 | -0.017 | 0.034 | 0.095 | 0.937 |
| M4 hdPS200+ECG | 18 | -0.012 | 0.032 | 0.095 | 0.934 |
| M1 sparse | 18 | -0.036 | 0.056 | 0.105 | 0.864 |
| M2 sparse+ECG | 18 | -0.029 | 0.051 | 0.104 | 0.866 |
| M0 unadjusted | 18 | -0.107 | 0.189 | 0.209 | 0.382 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.015 | 0.020 | 0.089 | 0.948 |
| R clinical | 18 | -0.015 | 0.026 | 0.092 | 0.942 |
| M3 hdPS200 | 18 | -0.031 | 0.038 | 0.095 | 0.931 |
| M4 hdPS200+ECG | 18 | -0.023 | 0.033 | 0.097 | 0.927 |
| M1 sparse | 18 | -0.031 | 0.042 | 0.098 | 0.907 |
| M2 sparse+ECG | 18 | -0.029 | 0.036 | 0.097 | 0.913 |
| M0 unadjusted | 18 | -0.101 | 0.153 | 0.177 | 0.521 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.014 | 0.027 | 0.088 | 0.945 |
| R clinical | 18 | -0.017 | 0.036 | 0.089 | 0.945 |
| M3 hdPS200 | 18 | -0.027 | 0.051 | 0.099 | 0.913 |
| M4 hdPS200+ECG | 18 | -0.021 | 0.046 | 0.099 | 0.890 |
| M1 sparse | 18 | -0.053 | 0.078 | 0.119 | 0.792 |
| M2 sparse+ECG | 18 | -0.045 | 0.071 | 0.118 | 0.790 |
| M0 unadjusted | 18 | -0.128 | 0.217 | 0.235 | 0.352 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.009 | 0.019 | 0.089 | 0.953 |
| R clinical | 18 | -0.010 | 0.024 | 0.088 | 0.956 |
| M3 hdPS200 | 18 | -0.008 | 0.026 | 0.090 | 0.944 |
| M4 hdPS200+ECG | 18 | -0.001 | 0.023 | 0.091 | 0.944 |
| M1 sparse | 18 | -0.014 | 0.037 | 0.092 | 0.924 |
| M2 sparse+ECG | 18 | -0.011 | 0.040 | 0.095 | 0.917 |
| M0 unadjusted | 18 | -0.084 | 0.161 | 0.184 | 0.434 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.011 | 0.024 | 0.086 | 0.945 |
| R clinical | 18 | -0.015 | 0.033 | 0.086 | 0.945 |
| M3 hdPS200 | 18 | -0.017 | 0.038 | 0.091 | 0.933 |
| M4 hdPS200+ECG | 18 | -0.011 | 0.032 | 0.092 | 0.924 |
| M1 sparse | 18 | -0.034 | 0.059 | 0.102 | 0.849 |
| M2 sparse+ECG | 18 | -0.030 | 0.055 | 0.103 | 0.846 |
| M0 unadjusted | 18 | -0.105 | 0.189 | 0.208 | 0.351 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 18 | 0.005 | 0.002 | 0.007 | 0.081 |
| base | C2 | 18 | 0.002 | -0.001 | 0.004 | 0.062 |
| base | sparse+noise32-vs-sparse | 18 | -0.009 | -0.012 | -0.006 | -0.164 |
| base | sparse+shufECG-vs-sparse | 18 | -0.006 | -0.008 | -0.005 | -0.113 |
| base | sparse+ECG-vs-sparse+shufECG | 18 | 0.011 | 0.008 | 0.013 | 0.174 |
| base | hdPS200+noise32-vs-hdPS200 | 18 | -0.002 | -0.006 | 0.001 | -0.070 |
| base | hdPS200+shufECG-vs-hdPS200 | 18 | 0.000 | -0.003 | 0.003 | 0.012 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.002 | -0.001 | 0.003 | 0.051 |
| none | C1 | 18 | -0.003 | -0.005 | -0.001 | -0.085 |
| none | C2 | 18 | 0.003 | 0.001 | 0.006 | 0.127 |
| none | sparse+noise32-vs-sparse | 18 | -0.005 | -0.007 | -0.002 | -0.122 |
| none | sparse+shufECG-vs-sparse | 18 | -0.004 | -0.007 | -0.002 | -0.113 |
| none | sparse+ECG-vs-sparse+shufECG | 18 | 0.001 | -0.002 | 0.004 | 0.026 |
| none | hdPS200+noise32-vs-hdPS200 | 18 | 0.003 | -0.001 | 0.006 | 0.098 |
| none | hdPS200+shufECG-vs-hdPS200 | 18 | -0.002 | -0.005 | 0.002 | -0.074 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.005 | 0.002 | 0.007 | 0.187 |
| null | C1 | 18 | 0.004 | 0.001 | 0.006 | 0.062 |
| null | C2 | 18 | 0.005 | 0.002 | 0.007 | 0.144 |
| null | sparse+noise32-vs-sparse | 18 | -0.008 | -0.011 | -0.005 | -0.131 |
| null | sparse+shufECG-vs-sparse | 18 | -0.007 | -0.010 | -0.005 | -0.124 |
| null | sparse+ECG-vs-sparse+shufECG | 18 | 0.011 | 0.008 | 0.013 | 0.166 |
| null | hdPS200+noise32-vs-hdPS200 | 18 | 0.000 | -0.003 | 0.003 | 0.005 |
| null | hdPS200+shufECG-vs-hdPS200 | 18 | 0.002 | -0.001 | 0.004 | 0.051 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.004 | 0.001 | 0.005 | 0.099 |
| phys_only | C1 | 18 | 0.006 | 0.003 | 0.008 | 0.138 |
| phys_only | C2 | 18 | 0.004 | 0.002 | 0.006 | 0.111 |
| phys_only | sparse+noise32-vs-sparse | 18 | 0.003 | -0.000 | 0.006 | 0.074 |
| phys_only | sparse+shufECG-vs-sparse | 18 | 0.001 | -0.003 | 0.003 | 0.018 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 18 | 0.005 | 0.003 | 0.008 | 0.123 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 18 | 0.004 | 0.001 | 0.008 | 0.113 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 18 | 0.001 | -0.002 | 0.004 | 0.034 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.003 | -0.000 | 0.006 | 0.080 |
| strong | C1 | 18 | 0.007 | 0.005 | 0.009 | 0.095 |
| strong | C2 | 18 | 0.005 | 0.003 | 0.007 | 0.096 |
| strong | sparse+noise32-vs-sparse | 18 | -0.009 | -0.012 | -0.007 | -0.119 |
| strong | sparse+shufECG-vs-sparse | 18 | -0.007 | -0.009 | -0.005 | -0.091 |
| strong | sparse+ECG-vs-sparse+shufECG | 18 | 0.015 | 0.013 | 0.017 | 0.171 |
| strong | hdPS200+noise32-vs-hdPS200 | 18 | -0.000 | -0.004 | 0.003 | -0.003 |
| strong | hdPS200+shufECG-vs-hdPS200 | 18 | 0.001 | -0.002 | 0.003 | 0.018 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.004 | 0.002 | 0.007 | 0.080 |

## I3 Within-trial paired bootstrap (200 replicates per trial)

Mean over trials of err(arm)² − err(comparator)² (negative = the first arm is closer to the target); 95% CI across bootstrap replicates; leave-one-trial-out range of the point estimate.

| target | contrast | trials | mean_d_sqerr | lo | hi | share_trials_closer | loo_min | loo_max |
|---|---|---|---|---|---|---|---|---|
| RCT | C1 | 18 | -0.0009 | -0.0436 | 0.0052 | 0.7778 | -0.0076 | 0.0006 |
| RCT | C2 | 18 | -0.0018 | -0.0297 | 0.0277 | 0.6111 | -0.0110 | 0.0020 |
| RCT | sparse+noise32-vs-sparse | 18 | 0.0191 | -0.0218 | 0.0191 | 0.3333 | 0.0065 | 0.0212 |
| RCT | sparse+shufECG-vs-sparse | 18 | 0.0094 | -0.0262 | 0.0236 | 0.3889 | 0.0018 | 0.0110 |
| RCT | sparse+ECG-vs-sparse+shufECG | 18 | -0.0102 | -0.0442 | 0.0079 | 0.6667 | -0.0157 | -0.0020 |
| RCT | hdPS200+noise32-vs-hdPS200 | 18 | -0.0090 | -0.0217 | 0.0141 | 0.6111 | -0.0137 | -0.0022 |
| RCT | hdPS200+shufECG-vs-hdPS200 | 18 | -0.0103 | -0.0212 | 0.0239 | 0.5556 | -0.0123 | -0.0038 |
| RCT | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.0085 | -0.0215 | 0.0300 | 0.5556 | -0.0072 | 0.0125 |
| RCT | sparse+ECG8-vs-sparse | 18 | 0.0050 | -0.0300 | 0.0194 | 0.5556 | -0.0020 | 0.0072 |
| RCT | sparse+ECG16-vs-sparse | 18 | 0.0080 | -0.0291 | 0.0153 | 0.5556 | 0.0009 | 0.0102 |
| RCT | sparse+ECG-vs-sparse | 18 | -0.0009 | -0.0436 | 0.0052 | 0.7778 | -0.0076 | 0.0006 |
| RCT | sparse+ECG64-vs-sparse | 18 | -0.0132 | -0.0502 | 0.0009 | 0.6667 | -0.0157 | -0.0032 |
| RCT | sparse+ECGpheno-vs-sparse | 18 | -0.0137 | -0.0462 | -0.0009 | 0.7778 | -0.0154 | -0.0064 |
| RCT | hdPS200+ECG8-vs-hdPS200 | 18 | -0.0116 | -0.0276 | 0.0197 | 0.7222 | -0.0129 | -0.0078 |
| RCT | hdPS200+ECG16-vs-hdPS200 | 18 | -0.0149 | -0.0253 | 0.0233 | 0.7778 | -0.0167 | -0.0112 |
| RCT | hdPS200+ECG-vs-hdPS200 | 18 | -0.0018 | -0.0297 | 0.0277 | 0.6111 | -0.0110 | 0.0020 |
| RCT | hdPS200+ECG64-vs-hdPS200 | 18 | -0.0093 | -0.0267 | 0.0172 | 0.6667 | -0.0125 | -0.0070 |
| RCT | hdPS200+ECGpheno-vs-hdPS200 | 18 | -0.0085 | -0.0333 | 0.0208 | 0.7778 | -0.0130 | -0.0054 |
| R | C1 | 18 | 0.0054 | -0.0149 | 0.0075 | 0.5556 | 0.0003 | 0.0062 |
| R | C2 | 18 | 0.0071 | -0.0161 | 0.0188 | 0.4444 | -0.0006 | 0.0082 |
| R | sparse+noise32-vs-sparse | 18 | 0.0078 | -0.0110 | 0.0093 | 0.3333 | 0.0031 | 0.0086 |
| R | sparse+shufECG-vs-sparse | 18 | 0.0036 | -0.0093 | 0.0136 | 0.4444 | 0.0009 | 0.0043 |
| R | sparse+ECG-vs-sparse+shufECG | 18 | 0.0019 | -0.0181 | 0.0060 | 0.4444 | -0.0021 | 0.0051 |
| R | hdPS200+noise32-vs-hdPS200 | 18 | -0.0081 | -0.0143 | 0.0126 | 0.6667 | -0.0097 | -0.0025 |
| R | hdPS200+shufECG-vs-hdPS200 | 18 | -0.0035 | -0.0143 | 0.0170 | 0.3889 | -0.0064 | 0.0022 |
| R | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.0106 | -0.0145 | 0.0182 | 0.6111 | -0.0028 | 0.0135 |
| R | sparse+ECG8-vs-sparse | 18 | 0.0064 | -0.0104 | 0.0131 | 0.3333 | 0.0008 | 0.0071 |
| R | sparse+ECG16-vs-sparse | 18 | 0.0070 | -0.0118 | 0.0088 | 0.4444 | 0.0047 | 0.0077 |
| R | sparse+ECG-vs-sparse | 18 | 0.0054 | -0.0149 | 0.0075 | 0.5556 | 0.0003 | 0.0062 |
| R | sparse+ECG64-vs-sparse | 18 | -0.0013 | -0.0175 | 0.0078 | 0.5556 | -0.0022 | 0.0012 |
| R | sparse+ECGpheno-vs-sparse | 18 | -0.0024 | -0.0181 | 0.0054 | 0.5556 | -0.0031 | -0.0004 |
| R | hdPS200+ECG8-vs-hdPS200 | 18 | -0.0023 | -0.0180 | 0.0163 | 0.5556 | -0.0037 | 0.0014 |
| R | hdPS200+ECG16-vs-hdPS200 | 18 | -0.0013 | -0.0142 | 0.0199 | 0.5000 | -0.0028 | 0.0018 |
| R | hdPS200+ECG-vs-hdPS200 | 18 | 0.0071 | -0.0161 | 0.0188 | 0.4444 | -0.0006 | 0.0082 |
| R | hdPS200+ECG64-vs-hdPS200 | 18 | 0.0006 | -0.0135 | 0.0187 | 0.4444 | -0.0025 | 0.0031 |
| R | hdPS200+ECGpheno-vs-hdPS200 | 18 | 0.0026 | -0.0159 | 0.0162 | 0.5000 | -0.0008 | 0.0038 |
| R+ | C1 | 18 | -0.0010 | -0.0158 | 0.0076 | 0.5556 | -0.0018 | 0.0002 |
| R+ | C2 | 18 | 0.0020 | -0.0192 | 0.0131 | 0.5556 | -0.0006 | 0.0036 |
| R+ | sparse+noise32-vs-sparse | 18 | 0.0087 | -0.0107 | 0.0118 | 0.5000 | 0.0011 | 0.0099 |
| R+ | sparse+shufECG-vs-sparse | 18 | 0.0054 | -0.0106 | 0.0149 | 0.3889 | 0.0010 | 0.0066 |
| R+ | sparse+ECG-vs-sparse+shufECG | 18 | -0.0063 | -0.0209 | 0.0071 | 0.7222 | -0.0074 | -0.0017 |
| R+ | hdPS200+noise32-vs-hdPS200 | 18 | -0.0005 | -0.0156 | 0.0124 | 0.4444 | -0.0015 | 0.0010 |
| R+ | hdPS200+shufECG-vs-hdPS200 | 18 | 0.0034 | -0.0158 | 0.0156 | 0.5000 | 0.0016 | 0.0040 |
| R+ | hdPS200+ECG-vs-hdPS200+shufECG | 18 | -0.0014 | -0.0175 | 0.0138 | 0.6667 | -0.0043 | 0.0003 |
| R+ | sparse+ECG8-vs-sparse | 18 | 0.0005 | -0.0109 | 0.0108 | 0.4444 | -0.0003 | 0.0017 |
| R+ | sparse+ECG16-vs-sparse | 18 | 0.0032 | -0.0119 | 0.0105 | 0.6111 | -0.0010 | 0.0044 |
| R+ | sparse+ECG-vs-sparse | 18 | -0.0010 | -0.0158 | 0.0076 | 0.5556 | -0.0018 | 0.0002 |
| R+ | sparse+ECG64-vs-sparse | 18 | -0.0056 | -0.0196 | 0.0030 | 0.6111 | -0.0067 | -0.0005 |
| R+ | sparse+ECGpheno-vs-sparse | 18 | 0.0002 | -0.0185 | 0.0051 | 0.5000 | -0.0043 | 0.0044 |
| R+ | hdPS200+ECG8-vs-hdPS200 | 18 | -0.0001 | -0.0156 | 0.0141 | 0.6667 | -0.0010 | 0.0014 |
| R+ | hdPS200+ECG16-vs-hdPS200 | 18 | -0.0018 | -0.0183 | 0.0171 | 0.6111 | -0.0026 | -0.0004 |
| R+ | hdPS200+ECG-vs-hdPS200 | 18 | 0.0020 | -0.0192 | 0.0131 | 0.5556 | -0.0006 | 0.0036 |
| R+ | hdPS200+ECG64-vs-hdPS200 | 18 | 0.0042 | -0.0146 | 0.0144 | 0.5556 | -0.0010 | 0.0056 |
| R+ | hdPS200+ECGpheno-vs-hdPS200 | 18 | -0.0048 | -0.0167 | 0.0145 | 0.6111 | -0.0061 | -0.0004 |

## I5 Supervised SHD logits and second ECG encoder (PRESENT-SHD LVEF<40 CNN penultimate layer, 32 PCs); SHD-scored cohort

| target | contrast | trials | mean_d_sqerr | lo | hi | share_trials_closer | loo_min | loo_max |
|---|---|---|---|---|---|---|---|---|
| RCT | C1 | 18 | -0.0009 | -0.0436 | 0.0052 | 0.7778 | -0.0076 | 0.0006 |
| RCT | C2 | 18 | -0.0018 | -0.0297 | 0.0277 | 0.6111 | -0.0110 | 0.0020 |
| RCT | sparse+SHD-vs-sparse | 18 | -0.0174 | -0.0475 | 0.0024 | 0.7778 | -0.0194 | -0.0087 |
| RCT | sparse+ENC2-vs-sparse | 18 | -0.0103 | -0.0449 | 0.0007 | 0.5000 | -0.0140 | -0.0006 |
| RCT | hdPS200+SHD-vs-hdPS200 | 18 | -0.0172 | -0.0282 | 0.0180 | 0.7778 | -0.0184 | -0.0140 |
| RCT | hdPS200+ENC2-vs-hdPS200 | 18 | 0.0012 | -0.0336 | 0.0106 | 0.6667 | -0.0110 | 0.0041 |
| R | C1 | 18 | 0.0054 | -0.0149 | 0.0075 | 0.5556 | 0.0003 | 0.0062 |
| R | C2 | 18 | 0.0071 | -0.0161 | 0.0188 | 0.4444 | -0.0006 | 0.0082 |
| R | sparse+SHD-vs-sparse | 18 | -0.0029 | -0.0154 | 0.0060 | 0.5556 | -0.0035 | -0.0006 |
| R | sparse+ENC2-vs-sparse | 18 | 0.0018 | -0.0181 | 0.0059 | 0.4444 | -0.0005 | 0.0044 |
| R | hdPS200+SHD-vs-hdPS200 | 18 | 0.0040 | -0.0121 | 0.0198 | 0.4444 | 0.0005 | 0.0069 |
| R | hdPS200+ENC2-vs-hdPS200 | 18 | 0.0259 | -0.0160 | 0.0150 | 0.4444 | 0.0114 | 0.0281 |
| R+ | C1 | 18 | -0.0010 | -0.0158 | 0.0076 | 0.5556 | -0.0018 | 0.0002 |
| R+ | C2 | 18 | 0.0020 | -0.0192 | 0.0131 | 0.5556 | -0.0006 | 0.0036 |
| R+ | sparse+SHD-vs-sparse | 18 | -0.0033 | -0.0169 | 0.0050 | 0.5556 | -0.0048 | 0.0015 |
| R+ | sparse+ENC2-vs-sparse | 18 | -0.0047 | -0.0194 | 0.0036 | 0.6667 | -0.0059 | 0.0003 |
| R+ | hdPS200+SHD-vs-hdPS200 | 18 | 0.0042 | -0.0130 | 0.0172 | 0.5000 | 0.0014 | 0.0059 |
| R+ | hdPS200+ENC2-vs-hdPS200 | 18 | 0.0127 | -0.0155 | 0.0139 | 0.5000 | 0.0039 | 0.0146 |

## I6 Multiverse (4 PS models × 5 hdPS split seeds × 10 estimators = 200 specifications; imputation 1)

Per specification: mean over trials of |log HR − target|; difference first arm − comparator (negative favours the first arm).

| contrast | target | metric | specs | share_favouring | median_diff | q10 | q90 | base_spec_diff |
|---|---|---|---|---|---|---|---|---|
| C1 | rct | mean_abs | 200 | 1.0000 | -0.0222 | -0.0366 | -0.0065 | -0.0114 |
| C1 | rct | mean_sq | 200 | 0.9750 | -0.0146 | -0.0224 | -0.0067 | -0.0009 |
| C1 | rplus | mean_abs | 200 | 0.8250 | -0.0069 | -0.0193 | 0.0022 | -0.0085 |
| C1 | rplus | mean_sq | 200 | 0.8750 | -0.0041 | -0.0080 | 0.0014 | -0.0011 |
| C2 | rct | mean_abs | 200 | 0.8550 | -0.0116 | -0.0304 | 0.0020 | -0.0241 |
| C2 | rct | mean_sq | 200 | 0.7700 | -0.0035 | -0.0176 | 0.0031 | -0.0018 |
| C2 | rplus | mean_abs | 200 | 0.5850 | -0.0026 | -0.0187 | 0.0109 | 0.0044 |
| C2 | rplus | mean_sq | 200 | 0.5750 | -0.0006 | -0.0057 | 0.0038 | 0.0018 |
| sparse+noise32-vs-sparse | rct | mean_abs | 200 | 0.4650 | 0.0010 | -0.0128 | 0.0194 | 0.0281 |
| sparse+noise32-vs-sparse | rct | mean_sq | 200 | 0.4850 | 0.0005 | -0.0115 | 0.0136 | 0.0191 |
| sparse+noise32-vs-sparse | rplus | mean_abs | 200 | 0.4200 | 0.0014 | -0.0071 | 0.0186 | 0.0102 |
| sparse+noise32-vs-sparse | rplus | mean_sq | 200 | 0.5100 | -0.0000 | -0.0046 | 0.0072 | 0.0086 |
| sparse+shufECG-vs-sparse | rct | mean_abs | 200 | 0.7250 | -0.0014 | -0.0135 | 0.0074 | 0.0080 |
| sparse+shufECG-vs-sparse | rct | mean_sq | 200 | 0.6500 | -0.0013 | -0.0087 | 0.0049 | 0.0094 |
| sparse+shufECG-vs-sparse | rplus | mean_abs | 200 | 0.2750 | 0.0038 | -0.0042 | 0.0134 | 0.0078 |
| sparse+shufECG-vs-sparse | rplus | mean_sq | 200 | 0.2250 | 0.0010 | -0.0030 | 0.0053 | 0.0054 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_abs | 200 | 0.9750 | -0.0198 | -0.0377 | -0.0055 | -0.0194 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_sq | 200 | 0.9500 | -0.0133 | -0.0200 | -0.0050 | -0.0102 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_abs | 200 | 0.8000 | -0.0138 | -0.0271 | 0.0025 | -0.0163 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_sq | 200 | 0.8000 | -0.0059 | -0.0094 | 0.0012 | -0.0065 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_abs | 200 | 0.5050 | -0.0004 | -0.0174 | 0.0149 | -0.0272 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_sq | 200 | 0.5350 | -0.0004 | -0.0070 | 0.0079 | -0.0090 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_abs | 200 | 0.4350 | 0.0017 | -0.0132 | 0.0113 | 0.0038 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_sq | 200 | 0.4300 | 0.0001 | -0.0048 | 0.0037 | -0.0006 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_abs | 200 | 0.5800 | -0.0021 | -0.0132 | 0.0123 | -0.0250 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_sq | 200 | 0.6150 | -0.0012 | -0.0063 | 0.0045 | -0.0103 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_abs | 200 | 0.5200 | -0.0007 | -0.0146 | 0.0139 | 0.0172 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_sq | 200 | 0.5950 | -0.0002 | -0.0061 | 0.0041 | 0.0033 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_abs | 200 | 0.8750 | -0.0109 | -0.0263 | 0.0011 | 0.0009 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_sq | 200 | 0.7650 | -0.0023 | -0.0133 | 0.0038 | 0.0085 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_abs | 200 | 0.5550 | -0.0021 | -0.0178 | 0.0132 | -0.0128 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_sq | 200 | 0.5700 | -0.0005 | -0.0055 | 0.0046 | -0.0015 |

## I7 Exact sign-flip permutation (frozen phase-2 estimates vs RCT) and leave-one-trial-out

| contrast | trials | mean_d_sqerr | p_signflip | loo_min | loo_max | trials_ecg_closer | p_sign_test_supplementary |
|---|---|---|---|---|---|---|---|
| C1 | 18 | -0.0009 | 0.9861 | -0.0076 | 0.0006 | 14 | 0.0309 |
| C2 | 18 | -0.0018 | 0.9158 | -0.0110 | 0.0020 | 11 | 0.4807 |

**Detectability.** Trials needed to detect the plasmode-expected reduction in |log HR − RCT| (paired t, two-sided α = 0.05, 80% power), using the between-trial SD of the frozen phase-2 paired differences:

| contrast | scenario | expected_gain | sd_paired_abs_diff | trials_needed |
|---|---|---|---|---|
| C1 | base | 0.004 | 0.059 | 1453.000 |
| C1 | phys_only | 0.000 | 0.059 | 1970218.000 |
| C1 | strong | 0.007 | 0.059 | 542.000 |
| C2 | base | -0.002 | 0.075 | inf |
| C2 | phys_only | 0.003 | 0.075 | 4552.000 |
| C2 | strong | -0.000 | 0.075 | inf |

## I9 E-values for the disagreement with the RCT (HR ratio; rare-outcome approximation)

| arm | median_evalue | max_evalue |
|---|---|---|
| M0 unadjusted | 1.69 | 7.04 |
| M1 sparse | 1.64 | 3.56 |
| M2 sparse+ECG | 1.56 | 3.53 |
| M3 hdPS200 | 1.64 | 2.51 |
| M4 hdPS200+ECG | 1.49 | 3.04 |
| R clinical | 1.53 | 2.43 |

## Part II: closer to the trial (agreement with the RCT per analysis)

Validation: max |log HR(design primary) − log HR(phase 2)| = 4.44e-16 over 108 arm-trials.

| analysis | arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|---|
| primary | R+ physiology ref | 18 | 0.145 | 8 | 15 | 1.273 | 0.107 | 0.667 |
| primary | R clinical | 18 | 0.141 | 12 | 14 | 1.254 | 0.116 | 0.722 |
| primary | M3 hdPS200 | 18 | 0.171 | 8 | 10 | 1.563 | 0.154 | 0.556 |
| primary | M4 hdPS200+ECG | 18 | 0.147 | 10 | 13 | 1.284 | 0.122 | 0.611 |
| primary | M1 sparse | 18 | 0.172 | 10 | 11 | 1.629 | 0.171 | 0.556 |
| primary | M2 sparse+ECG | 18 | 0.161 | 10 | 14 | 1.428 | 0.149 | 0.556 |
| primary | M0 unadjusted | 18 | 0.273 | 7 | 9 | 2.799 | 0.310 | 0.444 |
| strict | R+ physiology ref | 18 | 0.214 | 7 | 14 | 1.281 | 0.148 | 0.667 |
| strict | R clinical | 18 | 0.191 | 9 | 16 | 1.193 | 0.140 | 0.778 |
| strict | M3 hdPS200 | 18 | 0.225 | 6 | 15 | 1.486 | 0.170 | 0.833 |
| strict | M4 hdPS200+ECG | 18 | 0.238 | 8 | 14 | 1.307 | 0.158 | 0.722 |
| strict | M1 sparse | 18 | 0.239 | 8 | 10 | 1.657 | 0.229 | 0.556 |
| strict | M2 sparse+ECG | 18 | 0.295 | 7 | 13 | 1.652 | 0.215 | 0.667 |
| strict | M0 unadjusted | 18 | 0.340 | 6 | 9 | 2.606 | 0.364 | 0.444 |
| transport | R+ physiology ref | 18 | 0.195 | 6 | 17 | 1.038 | 0.108 | 0.833 |
| transport | R clinical | 18 | 0.180 | 8 | 17 | 1.012 | 0.110 | 0.833 |
| transport | M3 hdPS200 | 18 | 0.239 | 5 | 14 | 1.418 | 0.196 | 0.778 |
| transport | M4 hdPS200+ECG | 18 | 0.199 | 7 | 15 | 1.117 | 0.153 | 0.778 |
| transport | M1 sparse | 18 | 0.205 | 6 | 14 | 1.335 | 0.191 | 0.722 |
| transport | M2 sparse+ECG | 18 | 0.206 | 8 | 16 | 1.218 | 0.169 | 0.778 |
| transport | M0 unadjusted | 18 | 0.313 | 6 | 8 | 2.385 | 0.350 | 0.389 |
| transport_ess20 | R+ physiology ref | 18 | 0.167 | 7 | 17 | 1.041 | 0.097 | 0.833 |
| transport_ess20 | R clinical | 18 | 0.161 | 9 | 17 | 1.023 | 0.100 | 0.833 |
| transport_ess20 | M3 hdPS200 | 18 | 0.219 | 6 | 14 | 1.439 | 0.189 | 0.778 |
| transport_ess20 | M4 hdPS200+ECG | 18 | 0.186 | 8 | 15 | 1.136 | 0.146 | 0.778 |
| transport_ess20 | M1 sparse | 18 | 0.186 | 7 | 14 | 1.333 | 0.180 | 0.722 |
| transport_ess20 | M2 sparse+ECG | 18 | 0.186 | 8 | 16 | 1.244 | 0.157 | 0.778 |
| transport_ess20 | M0 unadjusted | 18 | 0.297 | 6 | 7 | 2.438 | 0.336 | 0.333 |
| pp_naive_365 | R+ physiology ref | 18 | 0.185 | 8 | 15 | 1.327 | 0.157 | 0.667 |
| pp_naive_365 | R clinical | 18 | 0.176 | 9 | 14 | 1.303 | 0.169 | 0.778 |
| pp_naive_365 | M3 hdPS200 | 18 | 0.195 | 10 | 12 | 1.473 | 0.181 | 0.611 |
| pp_naive_365 | M4 hdPS200+ECG | 18 | 0.181 | 9 | 12 | 1.308 | 0.155 | 0.611 |
| pp_naive_365 | M1 sparse | 18 | 0.264 | 6 | 11 | 2.012 | 0.258 | 0.500 |
| pp_naive_365 | M2 sparse+ECG | 18 | 0.246 | 6 | 11 | 1.809 | 0.238 | 0.556 |
| pp_naive_365 | M0 unadjusted | 18 | 0.382 | 4 | 6 | 3.236 | 0.398 | 0.222 |
| pp_ipcw_365 | R+ physiology ref | 18 | 0.185 | 8 | 15 | 1.278 | 0.150 | 0.778 |
| pp_ipcw_365 | R clinical | 18 | 0.174 | 9 | 14 | 1.249 | 0.160 | 0.778 |
| pp_ipcw_365 | M3 hdPS200 | 18 | 0.198 | 8 | 12 | 1.412 | 0.176 | 0.611 |
| pp_ipcw_365 | M4 hdPS200+ECG | 18 | 0.186 | 8 | 13 | 1.270 | 0.148 | 0.611 |
| pp_ipcw_365 | M1 sparse | 18 | 0.265 | 6 | 11 | 1.944 | 0.254 | 0.500 |
| pp_ipcw_365 | M2 sparse+ECG | 18 | 0.244 | 7 | 12 | 1.728 | 0.232 | 0.611 |
| pp_ipcw_365 | M0 unadjusted | 18 | 0.383 | 4 | 6 | 3.140 | 0.397 | 0.222 |
| pp_ipcw_180 | R+ physiology ref | 18 | 0.286 | 4 | 12 | 1.584 | 0.225 | 0.667 |
| pp_ipcw_180 | R clinical | 18 | 0.276 | 6 | 14 | 1.593 | 0.237 | 0.667 |
| pp_ipcw_180 | M3 hdPS200 | 18 | 0.279 | 6 | 13 | 1.668 | 0.250 | 0.611 |
| pp_ipcw_180 | M4 hdPS200+ECG | 18 | 0.259 | 8 | 13 | 1.487 | 0.230 | 0.667 |
| pp_ipcw_180 | M1 sparse | 18 | 0.354 | 5 | 10 | 2.192 | 0.328 | 0.500 |
| pp_ipcw_180 | M2 sparse+ECG | 18 | 0.355 | 4 | 11 | 2.114 | 0.308 | 0.556 |
| pp_ipcw_180 | M0 unadjusted | 18 | 0.471 | 4 | 5 | 3.311 | 0.461 | 0.278 |
| pp_ipcw_730 | R+ physiology ref | 18 | 0.161 | 10 | 14 | 1.230 | 0.129 | 0.667 |
| pp_ipcw_730 | R clinical | 18 | 0.154 | 10 | 14 | 1.196 | 0.136 | 0.778 |
| pp_ipcw_730 | M3 hdPS200 | 18 | 0.176 | 9 | 13 | 1.396 | 0.163 | 0.611 |
| pp_ipcw_730 | M4 hdPS200+ECG | 18 | 0.149 | 11 | 12 | 1.152 | 0.126 | 0.667 |
| pp_ipcw_730 | M1 sparse | 18 | 0.216 | 7 | 13 | 1.788 | 0.222 | 0.556 |
| pp_ipcw_730 | M2 sparse+ECG | 18 | 0.207 | 7 | 13 | 1.621 | 0.196 | 0.611 |
| pp_ipcw_730 | M0 unadjusted | 18 | 0.343 | 4 | 8 | 3.084 | 0.364 | 0.222 |
| pp_naive_switch | R+ physiology ref | 18 | 0.160 | 10 | 13 | 1.347 | 0.134 | 0.556 |
| pp_naive_switch | R clinical | 18 | 0.151 | 10 | 13 | 1.286 | 0.140 | 0.722 |
| pp_naive_switch | M3 hdPS200 | 18 | 0.169 | 9 | 13 | 1.490 | 0.166 | 0.611 |
| pp_naive_switch | M4 hdPS200+ECG | 18 | 0.143 | 11 | 12 | 1.219 | 0.126 | 0.611 |
| pp_naive_switch | M1 sparse | 18 | 0.200 | 8 | 12 | 1.827 | 0.207 | 0.611 |
| pp_naive_switch | M2 sparse+ECG | 18 | 0.190 | 7 | 12 | 1.643 | 0.185 | 0.667 |
| pp_naive_switch | M0 unadjusted | 18 | 0.318 | 5 | 7 | 3.129 | 0.349 | 0.222 |
| pp_ipcw_switch | R+ physiology ref | 18 | 0.158 | 10 | 13 | 1.295 | 0.127 | 0.611 |
| pp_ipcw_switch | R clinical | 18 | 0.149 | 10 | 13 | 1.235 | 0.131 | 0.722 |
| pp_ipcw_switch | M3 hdPS200 | 18 | 0.167 | 9 | 13 | 1.419 | 0.163 | 0.611 |
| pp_ipcw_switch | M4 hdPS200+ECG | 18 | 0.138 | 11 | 14 | 1.140 | 0.118 | 0.611 |
| pp_ipcw_switch | M1 sparse | 18 | 0.198 | 8 | 12 | 1.743 | 0.200 | 0.611 |
| pp_ipcw_switch | M2 sparse+ECG | 18 | 0.186 | 7 | 12 | 1.563 | 0.177 | 0.667 |
| pp_ipcw_switch | M0 unadjusted | 18 | 0.316 | 5 | 8 | 3.020 | 0.346 | 0.222 |
| runin90 | R+ physiology ref | 15 | 0.138 | 9 | 15 | 0.401 | 0.000 | 1.000 |
| runin90 | R clinical | 15 | 0.215 | 4 | 15 | 0.547 | 0.000 | 1.000 |
| runin90 | M3 hdPS200 | 15 | 0.248 | 7 | 12 | 0.950 | 0.170 | 0.800 |
| runin90 | M4 hdPS200+ECG | 15 | 0.276 | 3 | 13 | 0.991 | 0.203 | 0.867 |
| runin90 | M1 sparse | 15 | 0.305 | 3 | 13 | 0.989 | 0.139 | 0.867 |
| runin90 | M2 sparse+ECG | 15 | 0.254 | 7 | 14 | 0.872 | 0.086 | 0.867 |
| runin90 | M0 unadjusted | 17 | 0.239 | 6 | 11 | 1.766 | 0.260 | 0.588 |

## I8 Empirical calibration with expanded negative controls

Systematic error estimated from negative controls (per trial, pooled across trials if < 8 usable NCOs):

| arm | mean_mu | mean_abs_mu | mean_sigma | median_nco |
|---|---|---|---|---|
| R+ physiology ref | 0.043 | 0.071 | 0.029 | 21.500 |
| R clinical | 0.042 | 0.074 | 0.027 | 22.000 |
| M3 hdPS200 | 0.047 | 0.067 | 0.062 | 20.500 |
| M4 hdPS200+ECG | 0.035 | 0.071 | 0.067 | 19.500 |
| M1 sparse | 0.022 | 0.069 | 0.074 | 21.500 |
| M2 sparse+ECG | 0.040 | 0.087 | 0.069 | 20.500 |
| M0 unadjusted | 0.025 | 0.071 | 0.110 | 23.000 |

- C1 (M2 sparse+ECG − M1 sparse): mean Δσ = -0.006 (sign-flip p = 0.624); mean Δ|μ| = +0.017 (p = 0.259)
- C2 (M4 hdPS200+ECG − M3 hdPS200): mean Δσ = +0.006 (sign-flip p = 0.715); mean Δ|μ| = +0.003 (p = 0.894)

Agreement with the RCT after empirical calibration of the primary estimates:

| arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|
| R+ physiology ref | 18 | 0.160 | 8 | 14 | 1.374 | 0.140 | 0.611 |
| R clinical | 18 | 0.180 | 8 | 13 | 1.524 | 0.167 | 0.667 |
| M3 hdPS200 | 18 | 0.174 | 8 | 13 | 1.489 | 0.165 | 0.667 |
| M4 hdPS200+ECG | 18 | 0.164 | 8 | 14 | 1.323 | 0.141 | 0.722 |
| M1 sparse | 18 | 0.203 | 9 | 15 | 1.612 | 0.223 | 0.722 |
| M2 sparse+ECG | 18 | 0.202 | 7 | 13 | 1.662 | 0.203 | 0.667 |
| M0 unadjusted | 18 | 0.306 | 5 | 10 | 2.254 | 0.317 | 0.500 |

## Stratified by trial role (physiology vs control)

| role | trials | contrast | plasmode_rs_bias_reduction | pl_lo | pl_hi | boot_RCT_d | boot_RCT_lo | boot_RCT_hi | boot_R+_d | boot_R+_lo | boot_R+_hi | multiverse_share_rct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| physiology | 8 | C1 | 0.0093 | 0.0043 | 0.0114 | -0.0068 | -0.0785 | -0.0015 | 0.0004 | -0.0318 | 0.0040 | 0.9750 |
| physiology | 8 | C2 | -0.0076 | -0.0108 | -0.0043 | -0.0038 | -0.0314 | 0.0123 | -0.0011 | -0.0329 | 0.0215 | 0.9050 |
| control | 10 | C1 | 0.0003 | -0.0028 | 0.0041 | 0.0039 | -0.0316 | 0.0291 | -0.0020 | -0.0136 | 0.0146 | 0.7500 |
| control | 10 | C2 | 0.0020 | -0.0012 | 0.0045 | -0.0002 | -0.0356 | 0.0549 | 0.0045 | -0.0161 | 0.0222 | 0.6800 |

## Pre-specified decision rules

- C1 rule 1 (plasmode [rs] base: bias-reduction CI excludes 0, > 0): **met**
- C1 rule 1b (plasmode [rs] phys_only, supportive): **not met**
- C1 rule 3 (plasmode [rs] base: less biased than shuffled-ECG placebo): **met**
- C2 rule 1 (plasmode [rs] base: bias-reduction CI excludes 0, > 0): **not met**
- C2 rule 1b (plasmode [rs] phys_only, supportive): **not met**
- C2 rule 3 (plasmode [rs] base: less biased than shuffled-ECG placebo): **not met**
- C1 rule 2 (bootstrap vs RCT: CI < 0): **not met**
- C1 rule 2 (bootstrap vs R+: CI < 0): **not met**
- C1 rule 3 (beats shuffled-ECG placebo vs R+: CI < 0): **not met**
- C1 rule 4b (leave-one-out: sign holds in every set vs R+): **not met**
- C2 rule 2 (bootstrap vs RCT: CI < 0): **not met**
- C2 rule 2 (bootstrap vs R+: CI < 0): **not met**
- C2 rule 3 (beats shuffled-ECG placebo vs R+: CI < 0): **not met**
- C2 rule 4b (leave-one-out: sign holds in every set vs R+): **not met**
- C1 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **met**
- C2 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **met**
- C2 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **not met**
