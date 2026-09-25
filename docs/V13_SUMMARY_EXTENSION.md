# v1.3 exploratory robustness program — trial set: extension (8 trials)

Trials: emperor-preserved, east-afnet4, cabana, ontarget, value, ascot, empa-reg, carolina

All analyses are exploratory (registered 2026-09-25 after phase 2; tag protocol-v1.3).

## I1 Plasmode simulation — resampled cohort, PS and matching refitted per replicate (deviation 6; decides rule 1)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.014 | 0.018 | 0.077 | 0.941 |
| R clinical | 8 | -0.013 | 0.021 | 0.076 | 0.936 |
| M3 hdPS200 | 8 | -0.018 | 0.029 | 0.083 | 0.930 |
| M4 hdPS200+ECG | 8 | -0.020 | 0.034 | 0.086 | 0.916 |
| M1 sparse | 8 | -0.049 | 0.069 | 0.104 | 0.793 |
| M2 sparse+ECG | 8 | -0.047 | 0.065 | 0.102 | 0.806 |
| M0 unadjusted | 8 | -0.125 | 0.184 | 0.202 | 0.422 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.014 | 0.018 | 0.076 | 0.949 |
| R clinical | 8 | -0.014 | 0.018 | 0.075 | 0.942 |
| M3 hdPS200 | 8 | -0.025 | 0.033 | 0.083 | 0.919 |
| M4 hdPS200+ECG | 8 | -0.026 | 0.035 | 0.086 | 0.916 |
| M1 sparse | 8 | -0.030 | 0.041 | 0.086 | 0.890 |
| M2 sparse+ECG | 8 | -0.029 | 0.041 | 0.084 | 0.893 |
| M0 unadjusted | 8 | -0.106 | 0.141 | 0.161 | 0.554 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.018 | 0.023 | 0.075 | 0.946 |
| R clinical | 8 | -0.016 | 0.025 | 0.075 | 0.937 |
| M3 hdPS200 | 8 | -0.029 | 0.047 | 0.091 | 0.879 |
| M4 hdPS200+ECG | 8 | -0.030 | 0.049 | 0.096 | 0.871 |
| M1 sparse | 8 | -0.069 | 0.098 | 0.127 | 0.698 |
| M2 sparse+ECG | 8 | -0.065 | 0.092 | 0.121 | 0.711 |
| M0 unadjusted | 8 | -0.148 | 0.224 | 0.239 | 0.388 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.012 | 0.014 | 0.074 | 0.943 |
| R clinical | 8 | -0.012 | 0.019 | 0.071 | 0.947 |
| M3 hdPS200 | 8 | -0.007 | 0.018 | 0.080 | 0.931 |
| M4 hdPS200+ECG | 8 | -0.008 | 0.017 | 0.079 | 0.939 |
| M1 sparse | 8 | -0.030 | 0.039 | 0.081 | 0.894 |
| M2 sparse+ECG | 8 | -0.028 | 0.039 | 0.083 | 0.893 |
| M0 unadjusted | 8 | -0.101 | 0.142 | 0.161 | 0.482 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.020 | 0.020 | 0.075 | 0.939 |
| R clinical | 8 | -0.016 | 0.020 | 0.073 | 0.937 |
| M3 hdPS200 | 8 | -0.018 | 0.028 | 0.080 | 0.924 |
| M4 hdPS200+ECG | 8 | -0.019 | 0.028 | 0.081 | 0.927 |
| M1 sparse | 8 | -0.050 | 0.070 | 0.103 | 0.781 |
| M2 sparse+ECG | 8 | -0.047 | 0.066 | 0.100 | 0.789 |
| M0 unadjusted | 8 | -0.123 | 0.182 | 0.198 | 0.400 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 8 | 0.004 | 0.001 | 0.006 | 0.055 |
| base | C2 | 8 | -0.005 | -0.007 | -0.002 | -0.155 |
| base | sparse+noise32-vs-sparse | 8 | -0.001 | -0.004 | 0.001 | -0.020 |
| base | sparse+shufECG-vs-sparse | 8 | -0.000 | -0.003 | 0.002 | -0.007 |
| base | sparse+ECG-vs-sparse+shufECG | 8 | 0.004 | 0.001 | 0.007 | 0.062 |
| base | hdPS200+noise32-vs-hdPS200 | 8 | -0.001 | -0.003 | 0.002 | -0.022 |
| base | hdPS200+shufECG-vs-hdPS200 | 8 | -0.000 | -0.004 | 0.002 | -0.007 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.004 | -0.007 | -0.000 | -0.147 |
| none | C1 | 8 | 0.000 | -0.003 | 0.002 | 0.001 |
| none | C2 | 8 | 0.001 | -0.002 | 0.004 | 0.061 |
| none | sparse+noise32-vs-sparse | 8 | 0.002 | -0.000 | 0.004 | 0.047 |
| none | sparse+shufECG-vs-sparse | 8 | -0.001 | -0.003 | 0.002 | -0.021 |
| none | sparse+ECG-vs-sparse+shufECG | 8 | 0.001 | -0.002 | 0.003 | 0.022 |
| none | hdPS200+noise32-vs-hdPS200 | 8 | 0.003 | 0.000 | 0.006 | 0.178 |
| none | hdPS200+shufECG-vs-hdPS200 | 8 | -0.001 | -0.004 | 0.003 | -0.058 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.002 | -0.001 | 0.005 | 0.113 |
| null | C1 | 8 | 0.004 | 0.002 | 0.006 | 0.061 |
| null | C2 | 8 | 0.000 | -0.002 | 0.003 | 0.006 |
| null | sparse+noise32-vs-sparse | 8 | 0.001 | -0.001 | 0.004 | 0.021 |
| null | sparse+shufECG-vs-sparse | 8 | -0.001 | -0.003 | 0.002 | -0.010 |
| null | sparse+ECG-vs-sparse+shufECG | 8 | 0.005 | 0.002 | 0.007 | 0.070 |
| null | hdPS200+noise32-vs-hdPS200 | 8 | 0.000 | -0.002 | 0.003 | 0.004 |
| null | hdPS200+shufECG-vs-hdPS200 | 8 | 0.002 | -0.003 | 0.004 | 0.055 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.001 | -0.004 | 0.003 | -0.053 |
| phys_only | C1 | 8 | 0.000 | -0.002 | 0.003 | 0.006 |
| phys_only | C2 | 8 | -0.002 | -0.004 | 0.001 | -0.060 |
| phys_only | sparse+noise32-vs-sparse | 8 | 0.002 | -0.001 | 0.004 | 0.038 |
| phys_only | sparse+shufECG-vs-sparse | 8 | 0.001 | -0.002 | 0.003 | 0.016 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 8 | -0.000 | -0.003 | 0.002 | -0.010 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 8 | 0.003 | 0.001 | 0.006 | 0.098 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 8 | 0.000 | -0.003 | 0.003 | 0.010 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.002 | -0.005 | 0.001 | -0.071 |
| strong | C1 | 8 | 0.006 | 0.004 | 0.009 | 0.064 |
| strong | C2 | 8 | -0.002 | -0.005 | 0.001 | -0.041 |
| strong | sparse+noise32-vs-sparse | 8 | -0.002 | -0.004 | 0.000 | -0.019 |
| strong | sparse+shufECG-vs-sparse | 8 | -0.003 | -0.005 | -0.001 | -0.029 |
| strong | sparse+ECG-vs-sparse+shufECG | 8 | 0.009 | 0.007 | 0.012 | 0.090 |
| strong | hdPS200+noise32-vs-hdPS200 | 8 | -0.002 | -0.005 | 0.000 | -0.050 |
| strong | hdPS200+shufECG-vs-hdPS200 | 8 | 0.000 | -0.003 | 0.003 | 0.002 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.002 | -0.006 | 0.001 | -0.043 |

## I1 Plasmode simulation — fixed matched sets, as registered (flawed: conflates chance imbalance with bias)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.014 | 0.014 | 0.074 | 0.948 |
| R clinical | 8 | -0.014 | 0.021 | 0.071 | 0.955 |
| M3 hdPS200 | 8 | -0.013 | 0.025 | 0.077 | 0.942 |
| M4 hdPS200+ECG | 8 | -0.017 | 0.033 | 0.082 | 0.917 |
| M1 sparse | 8 | -0.043 | 0.061 | 0.095 | 0.831 |
| M2 sparse+ECG | 8 | -0.052 | 0.064 | 0.098 | 0.823 |
| M0 unadjusted | 8 | -0.126 | 0.183 | 0.198 | 0.426 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.017 | 0.023 | 0.074 | 0.947 |
| R clinical | 8 | -0.013 | 0.024 | 0.074 | 0.946 |
| M3 hdPS200 | 8 | -0.027 | 0.037 | 0.080 | 0.922 |
| M4 hdPS200+ECG | 8 | -0.026 | 0.041 | 0.086 | 0.899 |
| M1 sparse | 8 | -0.024 | 0.041 | 0.082 | 0.902 |
| M2 sparse+ECG | 8 | -0.032 | 0.044 | 0.085 | 0.897 |
| M0 unadjusted | 8 | -0.106 | 0.146 | 0.163 | 0.551 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.014 | 0.020 | 0.071 | 0.949 |
| R clinical | 8 | -0.015 | 0.031 | 0.074 | 0.949 |
| M3 hdPS200 | 8 | -0.025 | 0.048 | 0.087 | 0.891 |
| M4 hdPS200+ECG | 8 | -0.028 | 0.052 | 0.092 | 0.838 |
| M1 sparse | 8 | -0.060 | 0.092 | 0.119 | 0.719 |
| M2 sparse+ECG | 8 | -0.069 | 0.096 | 0.123 | 0.696 |
| M0 unadjusted | 8 | -0.146 | 0.224 | 0.238 | 0.383 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.009 | 0.013 | 0.070 | 0.959 |
| R clinical | 8 | -0.009 | 0.019 | 0.071 | 0.959 |
| M3 hdPS200 | 8 | -0.002 | 0.015 | 0.070 | 0.962 |
| M4 hdPS200+ECG | 8 | -0.003 | 0.020 | 0.073 | 0.947 |
| M1 sparse | 8 | -0.024 | 0.034 | 0.075 | 0.932 |
| M2 sparse+ECG | 8 | -0.028 | 0.041 | 0.080 | 0.917 |
| M0 unadjusted | 8 | -0.099 | 0.143 | 0.160 | 0.482 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.012 | 0.020 | 0.073 | 0.944 |
| R clinical | 8 | -0.015 | 0.026 | 0.072 | 0.942 |
| M3 hdPS200 | 8 | -0.013 | 0.031 | 0.077 | 0.932 |
| M4 hdPS200+ECG | 8 | -0.016 | 0.034 | 0.081 | 0.903 |
| M1 sparse | 8 | -0.043 | 0.066 | 0.096 | 0.806 |
| M2 sparse+ECG | 8 | -0.051 | 0.069 | 0.099 | 0.794 |
| M0 unadjusted | 8 | -0.124 | 0.185 | 0.200 | 0.386 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 8 | -0.003 | -0.005 | -0.001 | -0.049 |
| base | C2 | 8 | -0.008 | -0.010 | -0.006 | -0.308 |
| base | sparse+noise32-vs-sparse | 8 | -0.011 | -0.013 | -0.009 | -0.184 |
| base | sparse+shufECG-vs-sparse | 8 | -0.005 | -0.007 | -0.003 | -0.083 |
| base | sparse+ECG-vs-sparse+shufECG | 8 | 0.002 | 0.000 | 0.004 | 0.031 |
| base | hdPS200+noise32-vs-hdPS200 | 8 | -0.005 | -0.007 | -0.002 | -0.189 |
| base | hdPS200+shufECG-vs-hdPS200 | 8 | -0.003 | -0.005 | 0.000 | -0.110 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.005 | -0.008 | -0.002 | -0.178 |
| none | C1 | 8 | -0.008 | -0.010 | -0.005 | -0.228 |
| none | C2 | 8 | -0.005 | -0.007 | -0.002 | -0.340 |
| none | sparse+noise32-vs-sparse | 8 | -0.007 | -0.009 | -0.005 | -0.209 |
| none | sparse+shufECG-vs-sparse | 8 | -0.003 | -0.005 | -0.001 | -0.089 |
| none | sparse+ECG-vs-sparse+shufECG | 8 | -0.005 | -0.007 | -0.002 | -0.127 |
| none | hdPS200+noise32-vs-hdPS200 | 8 | 0.003 | 0.000 | 0.007 | 0.231 |
| none | hdPS200+shufECG-vs-hdPS200 | 8 | -0.004 | -0.006 | -0.001 | -0.263 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.001 | -0.004 | 0.002 | -0.061 |
| null | C1 | 8 | -0.003 | -0.005 | -0.001 | -0.043 |
| null | C2 | 8 | -0.003 | -0.006 | -0.001 | -0.111 |
| null | sparse+noise32-vs-sparse | 8 | -0.010 | -0.012 | -0.008 | -0.156 |
| null | sparse+shufECG-vs-sparse | 8 | -0.006 | -0.008 | -0.004 | -0.092 |
| null | sparse+ECG-vs-sparse+shufECG | 8 | 0.003 | 0.001 | 0.005 | 0.046 |
| null | hdPS200+noise32-vs-hdPS200 | 8 | -0.003 | -0.005 | -0.001 | -0.109 |
| null | hdPS200+shufECG-vs-hdPS200 | 8 | -0.003 | -0.005 | 0.000 | -0.085 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.001 | -0.004 | 0.001 | -0.024 |
| phys_only | C1 | 8 | -0.003 | -0.005 | -0.000 | -0.065 |
| phys_only | C2 | 8 | -0.004 | -0.006 | -0.002 | -0.115 |
| phys_only | sparse+noise32-vs-sparse | 8 | -0.002 | -0.004 | 0.000 | -0.057 |
| phys_only | sparse+shufECG-vs-sparse | 8 | -0.003 | -0.005 | -0.000 | -0.063 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 8 | -0.000 | -0.002 | 0.002 | -0.001 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 8 | 0.001 | -0.002 | 0.003 | 0.019 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 8 | -0.002 | -0.004 | 0.000 | -0.055 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.002 | -0.005 | -0.000 | -0.057 |
| strong | C1 | 8 | -0.004 | -0.005 | -0.002 | -0.039 |
| strong | C2 | 8 | -0.003 | -0.006 | -0.001 | -0.071 |
| strong | sparse+noise32-vs-sparse | 8 | -0.015 | -0.017 | -0.013 | -0.161 |
| strong | sparse+shufECG-vs-sparse | 8 | -0.007 | -0.009 | -0.005 | -0.076 |
| strong | sparse+ECG-vs-sparse+shufECG | 8 | 0.003 | 0.001 | 0.005 | 0.034 |
| strong | hdPS200+noise32-vs-hdPS200 | 8 | -0.007 | -0.009 | -0.005 | -0.142 |
| strong | hdPS200+shufECG-vs-hdPS200 | 8 | -0.003 | -0.005 | -0.001 | -0.065 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.000 | -0.003 | 0.002 | -0.006 |

## I3 Within-trial paired bootstrap (200 replicates per trial)

Mean over trials of err(arm)² − err(comparator)² (negative = the first arm is closer to the target); 95% CI across bootstrap replicates; leave-one-trial-out range of the point estimate.

| target | contrast | trials | mean_d_sqerr | lo | hi | share_trials_closer | loo_min | loo_max |
|---|---|---|---|---|---|---|---|---|
| RCT | C1 | 8 | -0.0092 | -0.0763 | 0.0006 | 0.8750 | -0.0107 | -0.0078 |
| RCT | C2 | 8 | -0.0091 | -0.0218 | 0.0314 | 0.6250 | -0.0119 | -0.0054 |
| RCT | sparse+noise32-vs-sparse | 8 | 0.0351 | -0.0345 | 0.0350 | 0.2500 | 0.0068 | 0.0427 |
| RCT | sparse+shufECG-vs-sparse | 8 | 0.0162 | -0.0355 | 0.0390 | 0.3750 | -0.0012 | 0.0211 |
| RCT | sparse+ECG-vs-sparse+shufECG | 8 | -0.0254 | -0.0689 | 0.0025 | 0.7500 | -0.0296 | -0.0077 |
| RCT | hdPS200+noise32-vs-hdPS200 | 8 | 0.0073 | -0.0169 | 0.0217 | 0.3750 | -0.0019 | 0.0117 |
| RCT | hdPS200+shufECG-vs-hdPS200 | 8 | -0.0052 | -0.0220 | 0.0246 | 0.7500 | -0.0092 | -0.0024 |
| RCT | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.0039 | -0.0285 | 0.0264 | 0.6250 | -0.0055 | -0.0013 |
| RCT | sparse+ECG8-vs-sparse | 8 | -0.0021 | -0.0377 | 0.0382 | 0.6250 | -0.0046 | -0.0007 |
| RCT | sparse+ECG16-vs-sparse | 8 | 0.0147 | -0.0425 | 0.0285 | 0.6250 | -0.0015 | 0.0185 |
| RCT | sparse+ECG-vs-sparse | 8 | -0.0092 | -0.0763 | 0.0006 | 0.8750 | -0.0107 | -0.0078 |
| RCT | sparse+ECG64-vs-sparse | 8 | -0.0291 | -0.0922 | -0.0084 | 0.8750 | -0.0355 | -0.0072 |
| RCT | sparse+ECGpheno-vs-sparse | 8 | -0.0257 | -0.0813 | -0.0020 | 0.8750 | -0.0297 | -0.0097 |
| RCT | hdPS200+ECG8-vs-hdPS200 | 8 | -0.0036 | -0.0224 | 0.0163 | 0.6250 | -0.0055 | -0.0014 |
| RCT | hdPS200+ECG16-vs-hdPS200 | 8 | -0.0102 | -0.0229 | 0.0169 | 0.8750 | -0.0120 | -0.0083 |
| RCT | hdPS200+ECG-vs-hdPS200 | 8 | -0.0091 | -0.0218 | 0.0314 | 0.6250 | -0.0119 | -0.0054 |
| RCT | hdPS200+ECG64-vs-hdPS200 | 8 | -0.0108 | -0.0271 | 0.0185 | 0.7500 | -0.0150 | -0.0085 |
| RCT | hdPS200+ECGpheno-vs-hdPS200 | 8 | -0.0125 | -0.0281 | 0.0168 | 0.8750 | -0.0143 | -0.0106 |
| R | C1 | 8 | -0.0005 | -0.0274 | 0.0054 | 0.7500 | -0.0014 | -0.0001 |
| R | C2 | 8 | -0.0028 | -0.0128 | 0.0246 | 0.6250 | -0.0037 | -0.0014 |
| R | sparse+noise32-vs-sparse | 8 | 0.0123 | -0.0175 | 0.0130 | 0.3750 | 0.0015 | 0.0146 |
| R | sparse+shufECG-vs-sparse | 8 | 0.0066 | -0.0145 | 0.0171 | 0.3750 | 0.0006 | 0.0081 |
| R | sparse+ECG-vs-sparse+shufECG | 8 | -0.0072 | -0.0282 | 0.0021 | 0.7500 | -0.0090 | -0.0007 |
| R | hdPS200+noise32-vs-hdPS200 | 8 | -0.0060 | -0.0123 | 0.0165 | 0.6250 | -0.0080 | 0.0001 |
| R | hdPS200+shufECG-vs-hdPS200 | 8 | -0.0032 | -0.0151 | 0.0151 | 0.5000 | -0.0041 | -0.0005 |
| R | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.0004 | -0.0149 | 0.0219 | 0.7500 | -0.0011 | 0.0014 |
| R | sparse+ECG8-vs-sparse | 8 | 0.0010 | -0.0159 | 0.0154 | 0.3750 | 0.0002 | 0.0016 |
| R | sparse+ECG16-vs-sparse | 8 | 0.0057 | -0.0193 | 0.0102 | 0.6250 | 0.0000 | 0.0068 |
| R | sparse+ECG-vs-sparse | 8 | -0.0005 | -0.0274 | 0.0054 | 0.7500 | -0.0014 | -0.0001 |
| R | sparse+ECG64-vs-sparse | 8 | -0.0041 | -0.0308 | 0.0017 | 0.6250 | -0.0064 | 0.0016 |
| R | sparse+ECGpheno-vs-sparse | 8 | -0.0048 | -0.0307 | 0.0026 | 0.7500 | -0.0061 | -0.0003 |
| R | hdPS200+ECG8-vs-hdPS200 | 8 | 0.0001 | -0.0117 | 0.0196 | 0.6250 | -0.0008 | 0.0008 |
| R | hdPS200+ECG16-vs-hdPS200 | 8 | 0.0012 | -0.0149 | 0.0203 | 0.6250 | -0.0021 | 0.0027 |
| R | hdPS200+ECG-vs-hdPS200 | 8 | -0.0028 | -0.0128 | 0.0246 | 0.6250 | -0.0037 | -0.0014 |
| R | hdPS200+ECG64-vs-hdPS200 | 8 | -0.0038 | -0.0123 | 0.0223 | 0.6250 | -0.0055 | -0.0017 |
| R | hdPS200+ECGpheno-vs-hdPS200 | 8 | -0.0022 | -0.0136 | 0.0211 | 0.6250 | -0.0029 | -0.0011 |
| R+ | C1 | 8 | -0.0001 | -0.0304 | 0.0043 | 0.6250 | -0.0009 | 0.0008 |
| R+ | C2 | 8 | -0.0001 | -0.0151 | 0.0183 | 0.5000 | -0.0011 | 0.0009 |
| R+ | sparse+noise32-vs-sparse | 8 | 0.0197 | -0.0213 | 0.0149 | 0.3750 | 0.0029 | 0.0227 |
| R+ | sparse+shufECG-vs-sparse | 8 | 0.0118 | -0.0176 | 0.0199 | 0.3750 | 0.0022 | 0.0137 |
| R+ | sparse+ECG-vs-sparse+shufECG | 8 | -0.0119 | -0.0338 | 0.0038 | 0.8750 | -0.0145 | -0.0014 |
| R+ | hdPS200+noise32-vs-hdPS200 | 8 | 0.0002 | -0.0119 | 0.0160 | 0.3750 | -0.0009 | 0.0013 |
| R+ | hdPS200+shufECG-vs-hdPS200 | 8 | -0.0007 | -0.0130 | 0.0148 | 0.6250 | -0.0015 | 0.0001 |
| R+ | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.0006 | -0.0144 | 0.0190 | 0.5000 | -0.0008 | 0.0011 |
| R+ | sparse+ECG8-vs-sparse | 8 | 0.0018 | -0.0162 | 0.0172 | 0.3750 | 0.0009 | 0.0026 |
| R+ | sparse+ECG16-vs-sparse | 8 | 0.0101 | -0.0238 | 0.0120 | 0.6250 | 0.0011 | 0.0117 |
| R+ | sparse+ECG-vs-sparse | 8 | -0.0001 | -0.0304 | 0.0043 | 0.6250 | -0.0009 | 0.0008 |
| R+ | sparse+ECG64-vs-sparse | 8 | -0.0083 | -0.0361 | 0.0007 | 0.5000 | -0.0113 | 0.0036 |
| R+ | sparse+ECGpheno-vs-sparse | 8 | -0.0077 | -0.0357 | 0.0029 | 0.5000 | -0.0096 | 0.0013 |
| R+ | hdPS200+ECG8-vs-hdPS200 | 8 | 0.0002 | -0.0111 | 0.0154 | 0.6250 | -0.0004 | 0.0006 |
| R+ | hdPS200+ECG16-vs-hdPS200 | 8 | 0.0001 | -0.0134 | 0.0168 | 0.6250 | -0.0013 | 0.0011 |
| R+ | hdPS200+ECG-vs-hdPS200 | 8 | -0.0001 | -0.0151 | 0.0183 | 0.5000 | -0.0011 | 0.0009 |
| R+ | hdPS200+ECG64-vs-hdPS200 | 8 | -0.0018 | -0.0119 | 0.0168 | 0.6250 | -0.0026 | -0.0009 |
| R+ | hdPS200+ECGpheno-vs-hdPS200 | 8 | -0.0016 | -0.0129 | 0.0163 | 0.6250 | -0.0022 | -0.0006 |

## I5 Supervised SHD logits and second ECG encoder (PRESENT-SHD LVEF<40 CNN penultimate layer, 32 PCs); SHD-scored cohort

| target | contrast | trials | mean_d_sqerr | lo | hi | share_trials_closer | loo_min | loo_max |
|---|---|---|---|---|---|---|---|---|
| RCT | C1 | 8 | -0.0092 | -0.0763 | 0.0006 | 0.8750 | -0.0107 | -0.0078 |
| RCT | C2 | 8 | -0.0091 | -0.0218 | 0.0314 | 0.6250 | -0.0119 | -0.0054 |
| RCT | sparse+SHD-vs-sparse | 8 | -0.0307 | -0.0769 | 0.0010 | 0.8750 | -0.0361 | -0.0113 |
| RCT | sparse+ENC2-vs-sparse | 8 | -0.0326 | -0.0790 | -0.0058 | 0.8750 | -0.0409 | -0.0121 |
| RCT | hdPS200+SHD-vs-hdPS200 | 8 | -0.0135 | -0.0309 | 0.0107 | 0.8750 | -0.0156 | -0.0108 |
| RCT | hdPS200+ENC2-vs-hdPS200 | 8 | -0.0135 | -0.0344 | 0.0088 | 0.6250 | -0.0167 | -0.0085 |
| R | C1 | 8 | -0.0005 | -0.0274 | 0.0054 | 0.7500 | -0.0014 | -0.0001 |
| R | C2 | 8 | -0.0028 | -0.0128 | 0.0246 | 0.6250 | -0.0037 | -0.0014 |
| R | sparse+SHD-vs-sparse | 8 | -0.0059 | -0.0232 | 0.0030 | 0.6250 | -0.0070 | -0.0008 |
| R | sparse+ENC2-vs-sparse | 8 | -0.0033 | -0.0287 | 0.0005 | 0.3750 | -0.0059 | 0.0024 |
| R | hdPS200+SHD-vs-hdPS200 | 8 | 0.0038 | -0.0101 | 0.0207 | 0.5000 | -0.0018 | 0.0060 |
| R | hdPS200+ENC2-vs-hdPS200 | 8 | 0.0314 | -0.0111 | 0.0232 | 0.6250 | -0.0029 | 0.0377 |
| R+ | C1 | 8 | -0.0001 | -0.0304 | 0.0043 | 0.6250 | -0.0009 | 0.0008 |
| R+ | C2 | 8 | -0.0001 | -0.0151 | 0.0183 | 0.5000 | -0.0011 | 0.0009 |
| R+ | sparse+SHD-vs-sparse | 8 | -0.0095 | -0.0314 | 0.0027 | 0.5000 | -0.0116 | 0.0011 |
| R+ | sparse+ENC2-vs-sparse | 8 | -0.0065 | -0.0346 | -0.0005 | 0.5000 | -0.0097 | 0.0052 |
| R+ | hdPS200+SHD-vs-hdPS200 | 8 | 0.0021 | -0.0113 | 0.0170 | 0.5000 | -0.0003 | 0.0034 |
| R+ | hdPS200+ENC2-vs-hdPS200 | 8 | 0.0193 | -0.0095 | 0.0202 | 0.5000 | -0.0012 | 0.0231 |

## I6 Multiverse (4 PS models × 5 hdPS split seeds × 10 estimators = 200 specifications; imputation 1)

Per specification: mean over trials of |log HR − target|; difference first arm − comparator (negative favours the first arm).

| contrast | target | metric | specs | share_favouring | median_diff | q10 | q90 | base_spec_diff |
|---|---|---|---|---|---|---|---|---|
| C1 | rct | mean_abs | 200 | 0.9750 | -0.0278 | -0.0547 | -0.0104 | -0.0268 |
| C1 | rct | mean_sq | 200 | 0.9750 | -0.0211 | -0.0458 | -0.0086 | -0.0092 |
| C1 | rplus | mean_abs | 200 | 0.8000 | -0.0163 | -0.0363 | 0.0084 | -0.0040 |
| C1 | rplus | mean_sq | 200 | 0.8250 | -0.0087 | -0.0193 | 0.0021 | -0.0001 |
| C2 | rct | mean_abs | 200 | 0.7550 | -0.0149 | -0.0397 | 0.0121 | -0.0331 |
| C2 | rct | mean_sq | 200 | 0.7500 | -0.0063 | -0.0181 | 0.0057 | -0.0091 |
| C2 | rplus | mean_abs | 200 | 0.5050 | -0.0001 | -0.0157 | 0.0188 | -0.0005 |
| C2 | rplus | mean_sq | 200 | 0.5400 | -0.0002 | -0.0024 | 0.0051 | -0.0001 |
| sparse+noise32-vs-sparse | rct | mean_abs | 200 | 0.4150 | 0.0026 | -0.0188 | 0.0231 | 0.0417 |
| sparse+noise32-vs-sparse | rct | mean_sq | 200 | 0.4600 | 0.0008 | -0.0172 | 0.0235 | 0.0351 |
| sparse+noise32-vs-sparse | rplus | mean_abs | 200 | 0.3800 | 0.0038 | -0.0137 | 0.0227 | 0.0323 |
| sparse+noise32-vs-sparse | rplus | mean_sq | 200 | 0.4550 | 0.0005 | -0.0096 | 0.0127 | 0.0197 |
| sparse+shufECG-vs-sparse | rct | mean_abs | 200 | 0.5000 | 0.0000 | -0.0152 | 0.0123 | 0.0067 |
| sparse+shufECG-vs-sparse | rct | mean_sq | 200 | 0.5000 | 0.0001 | -0.0062 | 0.0140 | 0.0162 |
| sparse+shufECG-vs-sparse | rplus | mean_abs | 200 | 0.3000 | 0.0051 | -0.0048 | 0.0242 | 0.0226 |
| sparse+shufECG-vs-sparse | rplus | mean_sq | 200 | 0.3000 | 0.0019 | -0.0041 | 0.0111 | 0.0118 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_abs | 200 | 0.9500 | -0.0299 | -0.0546 | -0.0059 | -0.0335 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_sq | 200 | 0.9750 | -0.0258 | -0.0431 | -0.0079 | -0.0254 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_abs | 200 | 1.0000 | -0.0268 | -0.0371 | -0.0069 | -0.0266 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_sq | 200 | 0.9250 | -0.0117 | -0.0191 | -0.0039 | -0.0119 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_abs | 200 | 0.3900 | 0.0033 | -0.0147 | 0.0238 | 0.0060 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_sq | 200 | 0.3450 | 0.0023 | -0.0061 | 0.0112 | 0.0073 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_abs | 200 | 0.4450 | 0.0009 | -0.0129 | 0.0186 | 0.0004 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_sq | 200 | 0.4050 | 0.0002 | -0.0021 | 0.0040 | 0.0002 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_abs | 200 | 0.4500 | 0.0025 | -0.0171 | 0.0258 | -0.0230 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_sq | 200 | 0.4800 | 0.0007 | -0.0080 | 0.0110 | -0.0052 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_abs | 200 | 0.5600 | -0.0015 | -0.0145 | 0.0182 | -0.0043 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_sq | 200 | 0.5550 | -0.0001 | -0.0032 | 0.0034 | -0.0007 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_abs | 200 | 0.8750 | -0.0154 | -0.0366 | 0.0018 | -0.0101 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_sq | 200 | 0.8900 | -0.0059 | -0.0192 | 0.0001 | -0.0039 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_abs | 200 | 0.4850 | 0.0011 | -0.0155 | 0.0182 | 0.0039 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_sq | 200 | 0.5200 | -0.0001 | -0.0026 | 0.0057 | 0.0006 |

## I7 Exact sign-flip permutation (frozen phase-2 estimates vs RCT) and leave-one-trial-out

| contrast | trials | mean_d_sqerr | p_signflip | loo_min | loo_max | trials_ecg_closer | p_sign_test_supplementary |
|---|---|---|---|---|---|---|---|
| C1 | 8 | -0.0092 | 0.0156 | -0.0107 | -0.0078 | 7 | 0.0703 |
| C2 | 8 | -0.0091 | 0.1797 | -0.0119 | -0.0054 | 5 | 0.7266 |

**Detectability.** Trials needed to detect the plasmode-expected reduction in |log HR − RCT| (paired t, two-sided α = 0.05, 80% power), using the between-trial SD of the frozen phase-2 paired differences:

| contrast | scenario | expected_gain | sd_paired_abs_diff | trials_needed |
|---|---|---|---|---|
| C1 | base | 0.004 | 0.020 | 220.000 |
| C1 | phys_only | 0.000 | 0.020 | 46640.000 |
| C1 | strong | 0.006 | 0.020 | 82.000 |
| C2 | base | -0.005 | 0.068 | inf |
| C2 | phys_only | -0.002 | 0.068 | inf |
| C2 | strong | -0.002 | 0.068 | inf |

## I9 E-values for the disagreement with the RCT (HR ratio; rare-outcome approximation)

| arm | median_evalue | max_evalue |
|---|---|---|
| M0 unadjusted | 1.71 | 7.04 |
| M1 sparse | 1.69 | 3.56 |
| M2 sparse+ECG | 1.61 | 3.53 |
| M3 hdPS200 | 1.72 | 1.93 |
| M4 hdPS200+ECG | 1.56 | 1.92 |
| R clinical | 1.56 | 2.43 |

## Part II: closer to the trial (agreement with the RCT per analysis)

Validation: max |log HR(design primary) − log HR(phase 2)| = 0.00e+00 over 48 arm-trials.

| analysis | arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|---|
| primary | R+ physiology ref | 8 | 0.161 | 3 | 6 | 1.586 | 0.097 | 0.500 |
| primary | R clinical | 8 | 0.164 | 5 | 5 | 1.577 | 0.105 | 0.500 |
| primary | M3 hdPS200 | 8 | 0.181 | 2 | 4 | 1.856 | 0.153 | 0.500 |
| primary | M4 hdPS200+ECG | 8 | 0.148 | 4 | 5 | 1.554 | 0.120 | 0.375 |
| primary | M1 sparse | 8 | 0.228 | 3 | 3 | 2.230 | 0.175 | 0.375 |
| primary | M2 sparse+ECG | 8 | 0.201 | 4 | 5 | 1.917 | 0.151 | 0.375 |
| primary | M0 unadjusted | 8 | 0.313 | 4 | 4 | 3.093 | 0.299 | 0.500 |
| strict | R+ physiology ref | 8 | 0.214 | 4 | 5 | 1.513 | 0.161 | 0.500 |
| strict | R clinical | 8 | 0.236 | 3 | 6 | 1.657 | 0.198 | 0.500 |
| strict | M3 hdPS200 | 8 | 0.226 | 3 | 5 | 1.793 | 0.195 | 0.625 |
| strict | M4 hdPS200+ECG | 8 | 0.212 | 3 | 5 | 1.618 | 0.161 | 0.500 |
| strict | M1 sparse | 8 | 0.288 | 3 | 4 | 2.141 | 0.280 | 0.500 |
| strict | M2 sparse+ECG | 8 | 0.299 | 3 | 5 | 2.150 | 0.251 | 0.500 |
| strict | M0 unadjusted | 8 | 0.415 | 3 | 4 | 3.220 | 0.430 | 0.500 |
| transport | R+ physiology ref | 8 | 0.181 | 3 | 8 | 1.009 | 0.095 | 0.750 |
| transport | R clinical | 8 | 0.170 | 4 | 7 | 1.093 | 0.140 | 0.625 |
| transport | M3 hdPS200 | 8 | 0.194 | 3 | 6 | 1.316 | 0.207 | 0.750 |
| transport | M4 hdPS200+ECG | 8 | 0.167 | 4 | 6 | 1.133 | 0.167 | 0.625 |
| transport | M1 sparse | 8 | 0.227 | 2 | 5 | 1.540 | 0.222 | 0.625 |
| transport | M2 sparse+ECG | 8 | 0.214 | 4 | 6 | 1.378 | 0.220 | 0.625 |
| transport | M0 unadjusted | 8 | 0.336 | 3 | 3 | 2.602 | 0.368 | 0.375 |
| transport_ess20 | R+ physiology ref | 8 | 0.182 | 3 | 8 | 1.075 | 0.088 | 0.750 |
| transport_ess20 | R clinical | 8 | 0.172 | 4 | 7 | 1.134 | 0.129 | 0.625 |
| transport_ess20 | M3 hdPS200 | 8 | 0.198 | 3 | 6 | 1.436 | 0.200 | 0.750 |
| transport_ess20 | M4 hdPS200+ECG | 8 | 0.169 | 4 | 6 | 1.210 | 0.158 | 0.625 |
| transport_ess20 | M1 sparse | 8 | 0.225 | 2 | 5 | 1.620 | 0.204 | 0.625 |
| transport_ess20 | M2 sparse+ECG | 8 | 0.219 | 4 | 6 | 1.468 | 0.205 | 0.625 |
| transport_ess20 | M0 unadjusted | 8 | 0.336 | 3 | 3 | 2.666 | 0.348 | 0.375 |
| pp_naive_365 | R+ physiology ref | 8 | 0.212 | 4 | 5 | 1.564 | 0.142 | 0.625 |
| pp_naive_365 | R clinical | 8 | 0.225 | 4 | 5 | 1.708 | 0.163 | 0.625 |
| pp_naive_365 | M3 hdPS200 | 8 | 0.233 | 4 | 4 | 1.874 | 0.181 | 0.375 |
| pp_naive_365 | M4 hdPS200+ECG | 8 | 0.209 | 4 | 4 | 1.671 | 0.124 | 0.375 |
| pp_naive_365 | M1 sparse | 8 | 0.328 | 4 | 4 | 2.484 | 0.263 | 0.500 |
| pp_naive_365 | M2 sparse+ECG | 8 | 0.281 | 4 | 5 | 2.070 | 0.225 | 0.500 |
| pp_naive_365 | M0 unadjusted | 8 | 0.432 | 3 | 3 | 3.387 | 0.382 | 0.375 |
| pp_ipcw_365 | R+ physiology ref | 8 | 0.214 | 4 | 5 | 1.522 | 0.138 | 0.625 |
| pp_ipcw_365 | R clinical | 8 | 0.223 | 4 | 5 | 1.648 | 0.156 | 0.625 |
| pp_ipcw_365 | M3 hdPS200 | 8 | 0.233 | 3 | 4 | 1.799 | 0.180 | 0.375 |
| pp_ipcw_365 | M4 hdPS200+ECG | 8 | 0.216 | 4 | 4 | 1.650 | 0.123 | 0.375 |
| pp_ipcw_365 | M1 sparse | 8 | 0.328 | 4 | 4 | 2.409 | 0.262 | 0.500 |
| pp_ipcw_365 | M2 sparse+ECG | 8 | 0.279 | 4 | 5 | 2.000 | 0.224 | 0.625 |
| pp_ipcw_365 | M0 unadjusted | 8 | 0.432 | 3 | 3 | 3.308 | 0.389 | 0.375 |
| pp_ipcw_180 | R+ physiology ref | 8 | 0.389 | 2 | 4 | 2.176 | 0.258 | 0.500 |
| pp_ipcw_180 | R clinical | 8 | 0.397 | 2 | 4 | 2.301 | 0.265 | 0.500 |
| pp_ipcw_180 | M3 hdPS200 | 8 | 0.368 | 2 | 3 | 2.285 | 0.289 | 0.375 |
| pp_ipcw_180 | M4 hdPS200+ECG | 8 | 0.370 | 3 | 3 | 2.183 | 0.254 | 0.250 |
| pp_ipcw_180 | M1 sparse | 8 | 0.484 | 3 | 4 | 2.889 | 0.356 | 0.375 |
| pp_ipcw_180 | M2 sparse+ECG | 8 | 0.465 | 2 | 4 | 2.732 | 0.315 | 0.500 |
| pp_ipcw_180 | M0 unadjusted | 8 | 0.569 | 2 | 3 | 3.722 | 0.471 | 0.375 |
| pp_ipcw_730 | R+ physiology ref | 8 | 0.185 | 4 | 5 | 1.481 | 0.100 | 0.500 |
| pp_ipcw_730 | R clinical | 8 | 0.186 | 4 | 5 | 1.514 | 0.112 | 0.625 |
| pp_ipcw_730 | M3 hdPS200 | 8 | 0.211 | 3 | 4 | 1.807 | 0.157 | 0.375 |
| pp_ipcw_730 | M4 hdPS200+ECG | 8 | 0.173 | 4 | 4 | 1.511 | 0.098 | 0.500 |
| pp_ipcw_730 | M1 sparse | 8 | 0.271 | 4 | 4 | 2.248 | 0.210 | 0.500 |
| pp_ipcw_730 | M2 sparse+ECG | 8 | 0.245 | 4 | 4 | 1.971 | 0.184 | 0.500 |
| pp_ipcw_730 | M0 unadjusted | 8 | 0.395 | 3 | 4 | 3.305 | 0.344 | 0.375 |
| pp_naive_switch | R+ physiology ref | 8 | 0.173 | 4 | 5 | 1.582 | 0.074 | 0.500 |
| pp_naive_switch | R clinical | 8 | 0.171 | 4 | 5 | 1.549 | 0.083 | 0.625 |
| pp_naive_switch | M3 hdPS200 | 8 | 0.186 | 3 | 5 | 1.809 | 0.129 | 0.500 |
| pp_naive_switch | M4 hdPS200+ECG | 8 | 0.154 | 4 | 4 | 1.508 | 0.064 | 0.500 |
| pp_naive_switch | M1 sparse | 8 | 0.238 | 4 | 4 | 2.199 | 0.170 | 0.500 |
| pp_naive_switch | M2 sparse+ECG | 8 | 0.208 | 4 | 4 | 1.867 | 0.153 | 0.500 |
| pp_naive_switch | M0 unadjusted | 8 | 0.343 | 4 | 4 | 3.185 | 0.306 | 0.375 |
| pp_ipcw_switch | R+ physiology ref | 8 | 0.171 | 4 | 5 | 1.526 | 0.058 | 0.500 |
| pp_ipcw_switch | R clinical | 8 | 0.167 | 4 | 5 | 1.490 | 0.063 | 0.625 |
| pp_ipcw_switch | M3 hdPS200 | 8 | 0.183 | 3 | 5 | 1.721 | 0.124 | 0.500 |
| pp_ipcw_switch | M4 hdPS200+ECG | 8 | 0.149 | 4 | 5 | 1.435 | 0.054 | 0.500 |
| pp_ipcw_switch | M1 sparse | 8 | 0.232 | 4 | 4 | 2.107 | 0.159 | 0.500 |
| pp_ipcw_switch | M2 sparse+ECG | 8 | 0.199 | 4 | 4 | 1.774 | 0.137 | 0.500 |
| pp_ipcw_switch | M0 unadjusted | 8 | 0.339 | 4 | 4 | 3.088 | 0.304 | 0.375 |
| runin90 | R+ physiology ref | 5 | 0.141 | 3 | 5 | 0.530 | 0.000 | 1.000 |
| runin90 | R clinical | 5 | 0.199 | 1 | 5 | 0.632 | 0.000 | 1.000 |
| runin90 | M3 hdPS200 | 5 | 0.181 | 3 | 3 | 1.134 | 0.190 | 0.600 |
| runin90 | M4 hdPS200+ECG | 5 | 0.229 | 1 | 3 | 1.321 | 0.300 | 0.600 |
| runin90 | M1 sparse | 5 | 0.191 | 1 | 4 | 0.976 | 0.073 | 0.800 |
| runin90 | M2 sparse+ECG | 5 | 0.195 | 2 | 5 | 1.026 | 0.051 | 0.800 |
| runin90 | M0 unadjusted | 7 | 0.199 | 2 | 5 | 1.835 | 0.215 | 0.571 |

## I8 Empirical calibration with expanded negative controls

Systematic error estimated from negative controls (per trial, pooled across trials if < 8 usable NCOs):

| arm | mean_mu | mean_abs_mu | mean_sigma | median_nco |
|---|---|---|---|---|
| R+ physiology ref | 0.010 | 0.052 | 0.013 | 22.500 |
| R clinical | 0.021 | 0.057 | 0.014 | 23.000 |
| M3 hdPS200 | 0.042 | 0.059 | 0.011 | 22.500 |
| M4 hdPS200+ECG | -0.003 | 0.035 | 0.018 | 22.000 |
| M1 sparse | 0.021 | 0.090 | 0.056 | 22.500 |
| M2 sparse+ECG | 0.027 | 0.077 | 0.041 | 22.500 |
| M0 unadjusted | 0.029 | 0.052 | 0.081 | 24.500 |

- C1 (M2 sparse+ECG − M1 sparse): mean Δσ = -0.014 (sign-flip p = 0.094); mean Δ|μ| = -0.013 (p = 0.438)
- C2 (M4 hdPS200+ECG − M3 hdPS200): mean Δσ = +0.007 (sign-flip p = 0.594); mean Δ|μ| = -0.023 (p = 0.820)

Agreement with the RCT after empirical calibration of the primary estimates:

| arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|
| R+ physiology ref | 8 | 0.158 | 3 | 6 | 1.572 | 0.109 | 0.500 |
| R clinical | 8 | 0.179 | 3 | 5 | 1.713 | 0.114 | 0.500 |
| M3 hdPS200 | 8 | 0.186 | 3 | 4 | 1.912 | 0.154 | 0.500 |
| M4 hdPS200+ECG | 8 | 0.139 | 4 | 5 | 1.547 | 0.126 | 0.500 |
| M1 sparse | 8 | 0.255 | 2 | 6 | 2.060 | 0.193 | 0.500 |
| M2 sparse+ECG | 8 | 0.219 | 3 | 4 | 1.942 | 0.115 | 0.500 |
| M0 unadjusted | 8 | 0.336 | 3 | 4 | 2.364 | 0.265 | 0.500 |

## Stratified by trial role (physiology vs control)

| role | trials | contrast | plasmode_rs_bias_reduction | pl_lo | pl_hi | boot_RCT_d | boot_RCT_lo | boot_RCT_hi | boot_R+_d | boot_R+_lo | boot_R+_hi | multiverse_share_rct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| physiology | 3 | C1 | 0.0074 | 0.0027 | 0.0114 | -0.0091 | -0.1905 | 0.0022 | -0.0013 | -0.0823 | 0.0037 | 0.9250 |
| physiology | 3 | C2 | -0.0089 | -0.0137 | -0.0039 | -0.0060 | -0.0519 | 0.0286 | 0.0008 | -0.0280 | 0.0442 | 0.6700 |
| control | 5 | C1 | 0.0017 | -0.0016 | 0.0039 | -0.0093 | -0.0261 | 0.0173 | 0.0006 | -0.0090 | 0.0125 | 0.9000 |
| control | 5 | C2 | -0.0019 | -0.0051 | 0.0014 | -0.0109 | -0.0227 | 0.0341 | -0.0007 | -0.0141 | 0.0199 | 0.7750 |

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
- C2 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **not met**
