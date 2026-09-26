# v1.3 exploratory robustness program — trial set: extension (8 trials)

Trials: emperor-preserved-v2, east-afnet4, cabana-v2, ontarget, value, ascot, empa-reg, carolina

All analyses are exploratory (registered 2026-09-25 after phase 2; tag protocol-v1.3).

## I1 Plasmode simulation — 80% subsample without replacement, PS and matching refitted per replicate (audit fix; decides rule 1)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.015 | 0.019 | 0.080 | 0.954 |
| R clinical | 8 | -0.017 | 0.026 | 0.081 | 0.942 |
| M3 hdPS200 | 8 | -0.016 | 0.029 | 0.086 | 0.943 |
| M4 hdPS200+ECG | 8 | -0.015 | 0.033 | 0.087 | 0.940 |
| M1 sparse | 8 | -0.054 | 0.073 | 0.110 | 0.805 |
| M2 sparse+ECG | 8 | -0.051 | 0.068 | 0.107 | 0.823 |
| M0 unadjusted | 8 | -0.130 | 0.189 | 0.208 | 0.495 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.014 | 0.020 | 0.082 | 0.946 |
| R clinical | 8 | -0.013 | 0.022 | 0.078 | 0.958 |
| M3 hdPS200 | 8 | -0.020 | 0.033 | 0.086 | 0.932 |
| M4 hdPS200+ECG | 8 | -0.019 | 0.034 | 0.087 | 0.931 |
| M1 sparse | 8 | -0.029 | 0.045 | 0.090 | 0.892 |
| M2 sparse+ECG | 8 | -0.030 | 0.043 | 0.090 | 0.909 |
| M0 unadjusted | 8 | -0.109 | 0.150 | 0.171 | 0.610 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.018 | 0.028 | 0.084 | 0.935 |
| R clinical | 8 | -0.018 | 0.031 | 0.085 | 0.929 |
| M3 hdPS200 | 8 | -0.026 | 0.047 | 0.099 | 0.892 |
| M4 hdPS200+ECG | 8 | -0.029 | 0.048 | 0.101 | 0.875 |
| M1 sparse | 8 | -0.075 | 0.108 | 0.141 | 0.709 |
| M2 sparse+ECG | 8 | -0.069 | 0.099 | 0.134 | 0.728 |
| M0 unadjusted | 8 | -0.157 | 0.235 | 0.254 | 0.426 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.018 | 0.018 | 0.083 | 0.943 |
| R clinical | 8 | -0.019 | 0.024 | 0.082 | 0.932 |
| M3 hdPS200 | 8 | -0.011 | 0.017 | 0.084 | 0.941 |
| M4 hdPS200+ECG | 8 | -0.011 | 0.016 | 0.083 | 0.942 |
| M1 sparse | 8 | -0.036 | 0.045 | 0.092 | 0.892 |
| M2 sparse+ECG | 8 | -0.034 | 0.043 | 0.092 | 0.892 |
| M0 unadjusted | 8 | -0.105 | 0.144 | 0.166 | 0.547 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.012 | 0.018 | 0.076 | 0.953 |
| R clinical | 8 | -0.015 | 0.022 | 0.075 | 0.946 |
| M3 hdPS200 | 8 | -0.016 | 0.032 | 0.083 | 0.931 |
| M4 hdPS200+ECG | 8 | -0.017 | 0.031 | 0.083 | 0.934 |
| M1 sparse | 8 | -0.053 | 0.073 | 0.108 | 0.783 |
| M2 sparse+ECG | 8 | -0.050 | 0.070 | 0.105 | 0.807 |
| M0 unadjusted | 8 | -0.130 | 0.189 | 0.206 | 0.459 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 8 | 0.005 | 0.003 | 0.008 | 0.071 |
| base | C2 | 8 | -0.003 | -0.006 | -0.000 | -0.116 |
| base | sparse+noise32-vs-sparse | 8 | -0.001 | -0.003 | 0.002 | -0.010 |
| base | sparse+shufECG-vs-sparse | 8 | -0.000 | -0.003 | 0.002 | -0.006 |
| base | sparse+ECG-vs-sparse+shufECG | 8 | 0.006 | 0.003 | 0.008 | 0.077 |
| base | hdPS200+noise32-vs-hdPS200 | 8 | -0.002 | -0.005 | 0.001 | -0.064 |
| base | hdPS200+shufECG-vs-hdPS200 | 8 | -0.004 | -0.007 | -0.001 | -0.153 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.001 | -0.002 | 0.004 | 0.032 |
| none | C1 | 8 | 0.002 | -0.000 | 0.005 | 0.046 |
| none | C2 | 8 | 0.000 | -0.003 | 0.003 | 0.013 |
| none | sparse+noise32-vs-sparse | 8 | 0.002 | -0.000 | 0.004 | 0.047 |
| none | sparse+shufECG-vs-sparse | 8 | 0.001 | -0.002 | 0.003 | 0.011 |
| none | sparse+ECG-vs-sparse+shufECG | 8 | 0.002 | -0.001 | 0.004 | 0.035 |
| none | hdPS200+noise32-vs-hdPS200 | 8 | 0.002 | -0.002 | 0.005 | 0.143 |
| none | hdPS200+shufECG-vs-hdPS200 | 8 | -0.000 | -0.004 | 0.004 | -0.013 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.000 | -0.003 | 0.004 | 0.026 |
| null | C1 | 8 | 0.003 | 0.001 | 0.005 | 0.042 |
| null | C2 | 8 | 0.001 | -0.002 | 0.003 | 0.037 |
| null | sparse+noise32-vs-sparse | 8 | -0.001 | -0.003 | 0.002 | -0.007 |
| null | sparse+shufECG-vs-sparse | 8 | -0.002 | -0.004 | 0.001 | -0.022 |
| null | sparse+ECG-vs-sparse+shufECG | 8 | 0.005 | 0.002 | 0.007 | 0.063 |
| null | hdPS200+noise32-vs-hdPS200 | 8 | 0.001 | -0.001 | 0.003 | 0.038 |
| null | hdPS200+shufECG-vs-hdPS200 | 8 | 0.001 | -0.001 | 0.004 | 0.045 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.000 | -0.003 | 0.002 | -0.008 |
| phys_only | C1 | 8 | 0.002 | -0.000 | 0.005 | 0.046 |
| phys_only | C2 | 8 | -0.001 | -0.004 | 0.001 | -0.039 |
| phys_only | sparse+noise32-vs-sparse | 8 | 0.001 | -0.001 | 0.004 | 0.027 |
| phys_only | sparse+shufECG-vs-sparse | 8 | 0.001 | -0.001 | 0.004 | 0.033 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 8 | 0.001 | -0.002 | 0.003 | 0.013 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 8 | 0.003 | -0.001 | 0.005 | 0.084 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 8 | -0.001 | -0.004 | 0.001 | -0.038 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.000 | -0.003 | 0.002 | -0.001 |
| strong | C1 | 8 | 0.009 | 0.006 | 0.011 | 0.083 |
| strong | C2 | 8 | -0.001 | -0.004 | 0.001 | -0.031 |
| strong | sparse+noise32-vs-sparse | 8 | -0.000 | -0.003 | 0.002 | -0.004 |
| strong | sparse+shufECG-vs-sparse | 8 | -0.002 | -0.004 | 0.001 | -0.016 |
| strong | sparse+ECG-vs-sparse+shufECG | 8 | 0.011 | 0.008 | 0.013 | 0.097 |
| strong | hdPS200+noise32-vs-hdPS200 | 8 | -0.004 | -0.006 | -0.001 | -0.087 |
| strong | hdPS200+shufECG-vs-hdPS200 | 8 | -0.001 | -0.004 | 0.001 | -0.028 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.000 | -0.003 | 0.002 | -0.003 |

## I1 Plasmode simulation — bootstrap resample with replacement (deviation 6; duplicates distort matching — superseded)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.015 | 0.020 | 0.075 | 0.939 |
| R clinical | 8 | -0.016 | 0.024 | 0.074 | 0.939 |
| M3 hdPS200 | 8 | -0.020 | 0.031 | 0.083 | 0.929 |
| M4 hdPS200+ECG | 8 | -0.019 | 0.032 | 0.086 | 0.916 |
| M1 sparse | 8 | -0.053 | 0.073 | 0.107 | 0.762 |
| M2 sparse+ECG | 8 | -0.050 | 0.068 | 0.104 | 0.781 |
| M0 unadjusted | 8 | -0.131 | 0.190 | 0.208 | 0.436 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.018 | 0.020 | 0.075 | 0.949 |
| R clinical | 8 | -0.017 | 0.020 | 0.074 | 0.943 |
| M3 hdPS200 | 8 | -0.026 | 0.034 | 0.085 | 0.908 |
| M4 hdPS200+ECG | 8 | -0.025 | 0.034 | 0.086 | 0.907 |
| M1 sparse | 8 | -0.032 | 0.042 | 0.087 | 0.866 |
| M2 sparse+ECG | 8 | -0.031 | 0.043 | 0.086 | 0.873 |
| M0 unadjusted | 8 | -0.114 | 0.149 | 0.170 | 0.561 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.024 | 0.029 | 0.076 | 0.944 |
| R clinical | 8 | -0.021 | 0.031 | 0.076 | 0.931 |
| M3 hdPS200 | 8 | -0.032 | 0.049 | 0.094 | 0.859 |
| M4 hdPS200+ECG | 8 | -0.031 | 0.050 | 0.098 | 0.861 |
| M1 sparse | 8 | -0.079 | 0.108 | 0.136 | 0.695 |
| M2 sparse+ECG | 8 | -0.071 | 0.098 | 0.129 | 0.709 |
| M0 unadjusted | 8 | -0.159 | 0.235 | 0.251 | 0.403 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.014 | 0.016 | 0.074 | 0.940 |
| R clinical | 8 | -0.014 | 0.021 | 0.073 | 0.943 |
| M3 hdPS200 | 8 | -0.007 | 0.018 | 0.080 | 0.932 |
| M4 hdPS200+ECG | 8 | -0.009 | 0.016 | 0.081 | 0.931 |
| M1 sparse | 8 | -0.032 | 0.042 | 0.083 | 0.889 |
| M2 sparse+ECG | 8 | -0.030 | 0.041 | 0.084 | 0.887 |
| M0 unadjusted | 8 | -0.102 | 0.143 | 0.162 | 0.503 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.018 | 0.018 | 0.074 | 0.938 |
| R clinical | 8 | -0.017 | 0.021 | 0.073 | 0.937 |
| M3 hdPS200 | 8 | -0.019 | 0.030 | 0.081 | 0.920 |
| M4 hdPS200+ECG | 8 | -0.021 | 0.030 | 0.081 | 0.924 |
| M1 sparse | 8 | -0.054 | 0.074 | 0.107 | 0.749 |
| M2 sparse+ECG | 8 | -0.049 | 0.067 | 0.102 | 0.768 |
| M0 unadjusted | 8 | -0.129 | 0.189 | 0.205 | 0.409 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 8 | 0.005 | 0.002 | 0.007 | 0.065 |
| base | C2 | 8 | -0.002 | -0.004 | 0.001 | -0.061 |
| base | sparse+noise32-vs-sparse | 8 | 0.002 | -0.000 | 0.004 | 0.025 |
| base | sparse+shufECG-vs-sparse | 8 | -0.001 | -0.003 | 0.001 | -0.012 |
| base | sparse+ECG-vs-sparse+shufECG | 8 | 0.006 | 0.003 | 0.008 | 0.076 |
| base | hdPS200+noise32-vs-hdPS200 | 8 | 0.001 | -0.001 | 0.003 | 0.031 |
| base | hdPS200+shufECG-vs-hdPS200 | 8 | -0.002 | -0.005 | 0.000 | -0.082 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.001 | -0.002 | 0.003 | 0.019 |
| none | C1 | 8 | 0.001 | -0.001 | 0.003 | 0.019 |
| none | C2 | 8 | 0.002 | -0.001 | 0.004 | 0.119 |
| none | sparse+noise32-vs-sparse | 8 | 0.002 | 0.000 | 0.005 | 0.058 |
| none | sparse+shufECG-vs-sparse | 8 | 0.001 | -0.002 | 0.003 | 0.013 |
| none | sparse+ECG-vs-sparse+shufECG | 8 | 0.000 | -0.002 | 0.003 | 0.006 |
| none | hdPS200+noise32-vs-hdPS200 | 8 | 0.004 | 0.000 | 0.006 | 0.201 |
| none | hdPS200+shufECG-vs-hdPS200 | 8 | -0.001 | -0.004 | 0.003 | -0.047 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.003 | -0.001 | 0.005 | 0.158 |
| null | C1 | 8 | 0.007 | 0.004 | 0.009 | 0.094 |
| null | C2 | 8 | -0.000 | -0.003 | 0.002 | -0.016 |
| null | sparse+noise32-vs-sparse | 8 | 0.004 | 0.001 | 0.006 | 0.047 |
| null | sparse+shufECG-vs-sparse | 8 | -0.001 | -0.003 | 0.001 | -0.015 |
| null | sparse+ECG-vs-sparse+shufECG | 8 | 0.008 | 0.005 | 0.010 | 0.108 |
| null | hdPS200+noise32-vs-hdPS200 | 8 | 0.001 | -0.001 | 0.004 | 0.044 |
| null | hdPS200+shufECG-vs-hdPS200 | 8 | 0.001 | -0.002 | 0.004 | 0.049 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.002 | -0.004 | 0.002 | -0.068 |
| phys_only | C1 | 8 | -0.000 | -0.003 | 0.002 | -0.005 |
| phys_only | C2 | 8 | -0.000 | -0.003 | 0.002 | -0.003 |
| phys_only | sparse+noise32-vs-sparse | 8 | -0.001 | -0.003 | 0.002 | -0.013 |
| phys_only | sparse+shufECG-vs-sparse | 8 | -0.001 | -0.003 | 0.001 | -0.019 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 8 | 0.001 | -0.002 | 0.003 | 0.014 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 8 | 0.004 | 0.001 | 0.006 | 0.106 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 8 | -0.000 | -0.003 | 0.002 | -0.003 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.000 | -0.002 | 0.003 | -0.000 |
| strong | C1 | 8 | 0.009 | 0.007 | 0.012 | 0.087 |
| strong | C2 | 8 | -0.000 | -0.003 | 0.002 | -0.005 |
| strong | sparse+noise32-vs-sparse | 8 | -0.001 | -0.003 | 0.001 | -0.007 |
| strong | sparse+shufECG-vs-sparse | 8 | -0.003 | -0.005 | -0.001 | -0.026 |
| strong | sparse+ECG-vs-sparse+shufECG | 8 | 0.012 | 0.009 | 0.014 | 0.110 |
| strong | hdPS200+noise32-vs-hdPS200 | 8 | -0.001 | -0.004 | 0.001 | -0.022 |
| strong | hdPS200+shufECG-vs-hdPS200 | 8 | -0.002 | -0.004 | 0.001 | -0.034 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.001 | -0.002 | 0.004 | 0.029 |

## I1 Plasmode simulation — fixed matched sets, as registered (flawed: conflates chance imbalance with bias)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.018 | 0.018 | 0.073 | 0.949 |
| R clinical | 8 | -0.019 | 0.026 | 0.072 | 0.956 |
| M3 hdPS200 | 8 | -0.015 | 0.028 | 0.077 | 0.938 |
| M4 hdPS200+ECG | 8 | -0.014 | 0.037 | 0.083 | 0.907 |
| M1 sparse | 8 | -0.058 | 0.075 | 0.106 | 0.777 |
| M2 sparse+ECG | 8 | -0.055 | 0.067 | 0.101 | 0.799 |
| M0 unadjusted | 8 | -0.133 | 0.190 | 0.206 | 0.449 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.016 | 0.021 | 0.072 | 0.950 |
| R clinical | 8 | -0.015 | 0.025 | 0.074 | 0.943 |
| M3 hdPS200 | 8 | -0.026 | 0.035 | 0.080 | 0.915 |
| M4 hdPS200+ECG | 8 | -0.025 | 0.040 | 0.085 | 0.897 |
| M1 sparse | 8 | -0.030 | 0.047 | 0.087 | 0.865 |
| M2 sparse+ECG | 8 | -0.034 | 0.045 | 0.087 | 0.874 |
| M0 unadjusted | 8 | -0.113 | 0.153 | 0.171 | 0.563 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.020 | 0.026 | 0.072 | 0.946 |
| R clinical | 8 | -0.019 | 0.034 | 0.076 | 0.943 |
| M3 hdPS200 | 8 | -0.023 | 0.047 | 0.085 | 0.884 |
| M4 hdPS200+ECG | 8 | -0.026 | 0.053 | 0.092 | 0.829 |
| M1 sparse | 8 | -0.077 | 0.109 | 0.133 | 0.714 |
| M2 sparse+ECG | 8 | -0.072 | 0.099 | 0.127 | 0.703 |
| M0 unadjusted | 8 | -0.157 | 0.235 | 0.249 | 0.400 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.014 | 0.016 | 0.071 | 0.953 |
| R clinical | 8 | -0.012 | 0.021 | 0.071 | 0.953 |
| M3 hdPS200 | 8 | -0.002 | 0.015 | 0.071 | 0.954 |
| M4 hdPS200+ECG | 8 | -0.004 | 0.021 | 0.073 | 0.945 |
| M1 sparse | 8 | -0.031 | 0.041 | 0.080 | 0.911 |
| M2 sparse+ECG | 8 | -0.028 | 0.041 | 0.080 | 0.912 |
| M0 unadjusted | 8 | -0.100 | 0.143 | 0.161 | 0.500 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 8 | -0.019 | 0.026 | 0.073 | 0.937 |
| R clinical | 8 | -0.018 | 0.029 | 0.071 | 0.943 |
| M3 hdPS200 | 8 | -0.016 | 0.034 | 0.076 | 0.933 |
| M4 hdPS200+ECG | 8 | -0.017 | 0.036 | 0.081 | 0.894 |
| M1 sparse | 8 | -0.056 | 0.080 | 0.107 | 0.757 |
| M2 sparse+ECG | 8 | -0.054 | 0.072 | 0.102 | 0.761 |
| M0 unadjusted | 8 | -0.131 | 0.193 | 0.207 | 0.407 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 8 | 0.008 | 0.006 | 0.011 | 0.111 |
| base | C2 | 8 | -0.008 | -0.011 | -0.006 | -0.293 |
| base | sparse+noise32-vs-sparse | 8 | 0.002 | -0.000 | 0.004 | 0.025 |
| base | sparse+shufECG-vs-sparse | 8 | 0.007 | 0.005 | 0.009 | 0.098 |
| base | sparse+ECG-vs-sparse+shufECG | 8 | 0.001 | -0.001 | 0.003 | 0.014 |
| base | hdPS200+noise32-vs-hdPS200 | 8 | -0.000 | -0.003 | 0.003 | -0.006 |
| base | hdPS200+shufECG-vs-hdPS200 | 8 | -0.006 | -0.008 | -0.004 | -0.202 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.003 | -0.005 | -0.000 | -0.076 |
| none | C1 | 8 | -0.000 | -0.002 | 0.002 | -0.011 |
| none | C2 | 8 | -0.006 | -0.009 | -0.002 | -0.371 |
| none | sparse+noise32-vs-sparse | 8 | 0.004 | 0.002 | 0.006 | 0.087 |
| none | sparse+shufECG-vs-sparse | 8 | 0.005 | 0.003 | 0.008 | 0.130 |
| none | sparse+ECG-vs-sparse+shufECG | 8 | -0.006 | -0.008 | -0.004 | -0.161 |
| none | hdPS200+noise32-vs-hdPS200 | 8 | 0.004 | 0.002 | 0.006 | 0.278 |
| none | hdPS200+shufECG-vs-hdPS200 | 8 | -0.003 | -0.005 | -0.000 | -0.221 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 8 | -0.002 | -0.006 | 0.001 | -0.123 |
| null | C1 | 8 | 0.008 | 0.006 | 0.010 | 0.099 |
| null | C2 | 8 | -0.002 | -0.005 | 0.000 | -0.065 |
| null | sparse+noise32-vs-sparse | 8 | 0.002 | 0.000 | 0.004 | 0.027 |
| null | sparse+shufECG-vs-sparse | 8 | 0.006 | 0.004 | 0.008 | 0.077 |
| null | sparse+ECG-vs-sparse+shufECG | 8 | 0.002 | -0.000 | 0.004 | 0.024 |
| null | hdPS200+noise32-vs-hdPS200 | 8 | -0.001 | -0.003 | 0.001 | -0.033 |
| null | hdPS200+shufECG-vs-hdPS200 | 8 | -0.003 | -0.006 | -0.001 | -0.086 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.001 | -0.001 | 0.003 | 0.020 |
| phys_only | C1 | 8 | 0.002 | -0.000 | 0.004 | 0.045 |
| phys_only | C2 | 8 | -0.005 | -0.007 | -0.003 | -0.137 |
| phys_only | sparse+noise32-vs-sparse | 8 | -0.001 | -0.003 | 0.001 | -0.013 |
| phys_only | sparse+shufECG-vs-sparse | 8 | 0.003 | 0.000 | 0.005 | 0.058 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 8 | -0.001 | -0.003 | 0.001 | -0.013 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 8 | 0.004 | 0.002 | 0.006 | 0.119 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 8 | -0.006 | -0.008 | -0.004 | -0.162 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.001 | -0.001 | 0.003 | 0.021 |
| strong | C1 | 8 | 0.010 | 0.008 | 0.012 | 0.093 |
| strong | C2 | 8 | -0.006 | -0.008 | -0.004 | -0.130 |
| strong | sparse+noise32-vs-sparse | 8 | -0.003 | -0.005 | -0.001 | -0.023 |
| strong | sparse+shufECG-vs-sparse | 8 | 0.007 | 0.005 | 0.009 | 0.061 |
| strong | sparse+ECG-vs-sparse+shufECG | 8 | 0.004 | 0.001 | 0.005 | 0.034 |
| strong | hdPS200+noise32-vs-hdPS200 | 8 | -0.003 | -0.005 | 0.000 | -0.056 |
| strong | hdPS200+shufECG-vs-hdPS200 | 8 | -0.009 | -0.011 | -0.007 | -0.182 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.002 | 0.000 | 0.006 | 0.044 |

## I3 Within-trial paired bootstrap (200 replicates per trial)

Mean over trials of err(arm)² − err(comparator)² (negative = the first arm is closer to the target); 95% CI across bootstrap replicates; leave-one-trial-out range of the point estimate.

**Inference:** the exact sign-flip test across trials (p_signflip) is the valid test; the bootstrap CI (lo, hi) re-matches on resamples with duplicate patients, which is not valid for matching estimators (audit), and is shown for description only.

| target | contrast | trials | mean_d_sqerr | p_signflip | lo | hi | share_trials_closer | loo_min | loo_max | without_cabana |
|---|---|---|---|---|---|---|---|---|---|---|
| RCT | C1 | 8 | -0.0446 | 0.0156 | -0.0658 | 0.0013 | 0.8750 | -0.0512 | -0.0087 | -0.0087 |
| RCT | C2 | 8 | 0.0048 | 0.7031 | -0.0210 | 0.0219 | 0.5000 | -0.0041 | 0.0104 | -0.0041 |
| RCT | sparse+noise32-vs-sparse | 8 | -0.0061 | 0.7422 | -0.0416 | 0.0374 | 0.5000 | -0.0135 | 0.0057 | 0.0057 |
| RCT | sparse+shufECG-vs-sparse | 8 | -0.0218 | 0.5234 | -0.0353 | 0.0375 | 0.3750 | -0.0267 | 0.0002 | 0.0002 |
| RCT | sparse+ECG-vs-sparse+shufECG | 8 | -0.0228 | 0.0234 | -0.0676 | -0.0004 | 0.8750 | -0.0265 | -0.0088 | -0.0088 |
| RCT | hdPS200+noise32-vs-hdPS200 | 8 | 0.0074 | 0.3906 | -0.0204 | 0.0240 | 0.2500 | 0.0015 | 0.0110 | 0.0015 |
| RCT | hdPS200+shufECG-vs-hdPS200 | 8 | 0.0038 | 0.9375 | -0.0145 | 0.0211 | 0.7500 | -0.0069 | 0.0079 | -0.0069 |
| RCT | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.0010 | 0.8438 | -0.0257 | 0.0260 | 0.5000 | -0.0032 | 0.0043 | 0.0028 |
| RCT | sparse+ECG8-vs-sparse | 8 | -0.0134 | 0.3750 | -0.0359 | 0.0339 | 0.6250 | -0.0175 | -0.0011 | -0.0011 |
| RCT | sparse+ECG16-vs-sparse | 8 | -0.0180 | 0.2891 | -0.0400 | 0.0269 | 0.8750 | -0.0227 | -0.0019 | -0.0019 |
| RCT | sparse+ECG-vs-sparse | 8 | -0.0446 | 0.0156 | -0.0658 | 0.0013 | 0.8750 | -0.0512 | -0.0087 | -0.0087 |
| RCT | sparse+ECG64-vs-sparse | 8 | -0.0624 | 0.1328 | -0.0816 | -0.0150 | 0.7500 | -0.0734 | -0.0060 | -0.0060 |
| RCT | sparse+ECGpheno-vs-sparse | 8 | -0.0538 | 0.0234 | -0.0769 | -0.0056 | 0.8750 | -0.0619 | -0.0093 | -0.0093 |
| RCT | hdPS200+ECG8-vs-hdPS200 | 8 | 0.0094 | 0.7578 | -0.0217 | 0.0139 | 0.5000 | -0.0019 | 0.0120 | -0.0019 |
| RCT | hdPS200+ECG16-vs-hdPS200 | 8 | -0.0027 | 0.5703 | -0.0244 | 0.0174 | 0.7500 | -0.0071 | 0.0003 | -0.0071 |
| RCT | hdPS200+ECG-vs-hdPS200 | 8 | 0.0048 | 0.7031 | -0.0210 | 0.0219 | 0.5000 | -0.0041 | 0.0104 | -0.0041 |
| RCT | hdPS200+ECG64-vs-hdPS200 | 8 | -0.0048 | 0.6641 | -0.0274 | 0.0195 | 0.7500 | -0.0137 | -0.0017 | -0.0137 |
| RCT | hdPS200+ECGpheno-vs-hdPS200 | 8 | 0.0024 | 0.9609 | -0.0302 | 0.0202 | 0.6250 | -0.0104 | 0.0065 | -0.0104 |
| R | C1 | 8 | -0.0139 | 0.3281 | -0.0257 | 0.0047 | 0.7500 | -0.0166 | -0.0005 | -0.0005 |
| R | C2 | 8 | -0.0130 | 0.5547 | -0.0140 | 0.0153 | 0.6250 | -0.0179 | 0.0009 | 0.0009 |
| R | sparse+noise32-vs-sparse | 8 | -0.0031 | 0.7812 | -0.0142 | 0.0168 | 0.3750 | -0.0051 | 0.0016 | 0.0016 |
| R | sparse+shufECG-vs-sparse | 8 | -0.0087 | 0.4766 | -0.0133 | 0.0171 | 0.5000 | -0.0102 | -0.0001 | -0.0001 |
| R | sparse+ECG-vs-sparse+shufECG | 8 | -0.0052 | 0.3750 | -0.0276 | 0.0020 | 0.7500 | -0.0067 | -0.0005 | -0.0005 |
| R | hdPS200+noise32-vs-hdPS200 | 8 | -0.0111 | 0.6172 | -0.0125 | 0.0155 | 0.5000 | -0.0138 | 0.0005 | 0.0005 |
| R | hdPS200+shufECG-vs-hdPS200 | 8 | -0.0150 | 0.5000 | -0.0142 | 0.0118 | 0.5000 | -0.0177 | -0.0000 | -0.0000 |
| R | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.0020 | 0.6875 | -0.0175 | 0.0180 | 0.7500 | -0.0009 | 0.0033 | 0.0009 |
| R | sparse+ECG8-vs-sparse | 8 | -0.0046 | 0.7422 | -0.0130 | 0.0139 | 0.5000 | -0.0057 | 0.0005 | 0.0005 |
| R | sparse+ECG16-vs-sparse | 8 | -0.0064 | 0.6172 | -0.0148 | 0.0099 | 0.6250 | -0.0076 | 0.0002 | 0.0002 |
| R | sparse+ECG-vs-sparse | 8 | -0.0139 | 0.3281 | -0.0257 | 0.0047 | 0.7500 | -0.0166 | -0.0005 | -0.0005 |
| R | sparse+ECG64-vs-sparse | 8 | -0.0168 | 0.6484 | -0.0267 | -0.0008 | 0.6250 | -0.0209 | 0.0012 | 0.0012 |
| R | sparse+ECGpheno-vs-sparse | 8 | -0.0165 | 0.1250 | -0.0252 | 0.0010 | 0.7500 | -0.0191 | -0.0009 | -0.0009 |
| R | hdPS200+ECG8-vs-hdPS200 | 8 | -0.0165 | 0.1719 | -0.0134 | 0.0190 | 0.7500 | -0.0194 | -0.0008 | -0.0008 |
| R | hdPS200+ECG16-vs-hdPS200 | 8 | -0.0100 | 0.0625 | -0.0133 | 0.0132 | 0.7500 | -0.0115 | -0.0021 | -0.0021 |
| R | hdPS200+ECG-vs-hdPS200 | 8 | -0.0130 | 0.5547 | -0.0140 | 0.0153 | 0.6250 | -0.0179 | 0.0009 | 0.0009 |
| R | hdPS200+ECG64-vs-hdPS200 | 8 | -0.0140 | 0.2578 | -0.0121 | 0.0175 | 0.6250 | -0.0171 | -0.0014 | -0.0014 |
| R | hdPS200+ECGpheno-vs-hdPS200 | 8 | -0.0180 | 0.1719 | -0.0149 | 0.0151 | 0.6250 | -0.0208 | -0.0021 | -0.0021 |
| R+ | C1 | 8 | -0.0169 | 0.5391 | -0.0305 | 0.0043 | 0.6250 | -0.0202 | 0.0003 | 0.0003 |
| R+ | C2 | 8 | -0.0085 | 0.7266 | -0.0137 | 0.0136 | 0.5000 | -0.0123 | 0.0020 | 0.0020 |
| R+ | sparse+noise32-vs-sparse | 8 | -0.0027 | 0.8750 | -0.0194 | 0.0196 | 0.3750 | -0.0051 | 0.0032 | 0.0032 |
| R+ | sparse+shufECG-vs-sparse | 8 | -0.0098 | 0.8281 | -0.0158 | 0.0190 | 0.5000 | -0.0120 | 0.0011 | 0.0011 |
| R+ | sparse+ECG-vs-sparse+shufECG | 8 | -0.0071 | 0.3203 | -0.0317 | 0.0000 | 0.8750 | -0.0091 | -0.0008 | -0.0008 |
| R+ | hdPS200+noise32-vs-hdPS200 | 8 | -0.0076 | 0.7812 | -0.0122 | 0.0141 | 0.3750 | -0.0097 | 0.0013 | 0.0013 |
| R+ | hdPS200+shufECG-vs-hdPS200 | 8 | -0.0106 | 0.6406 | -0.0136 | 0.0107 | 0.6250 | -0.0128 | 0.0005 | 0.0005 |
| R+ | hdPS200+ECG-vs-hdPS200+shufECG | 8 | 0.0021 | 0.5703 | -0.0114 | 0.0147 | 0.5000 | -0.0003 | 0.0029 | 0.0015 |
| R+ | sparse+ECG8-vs-sparse | 8 | -0.0050 | 0.8516 | -0.0159 | 0.0173 | 0.3750 | -0.0069 | 0.0014 | 0.0014 |
| R+ | sparse+ECG16-vs-sparse | 8 | -0.0069 | 0.8828 | -0.0179 | 0.0145 | 0.6250 | -0.0089 | 0.0015 | 0.0015 |
| R+ | sparse+ECG-vs-sparse | 8 | -0.0169 | 0.5391 | -0.0305 | 0.0043 | 0.6250 | -0.0202 | 0.0003 | 0.0003 |
| R+ | sparse+ECG64-vs-sparse | 8 | -0.0216 | 0.8281 | -0.0329 | -0.0003 | 0.5000 | -0.0266 | 0.0028 | 0.0028 |
| R+ | sparse+ECGpheno-vs-sparse | 8 | -0.0199 | 0.7969 | -0.0321 | -0.0000 | 0.5000 | -0.0232 | 0.0006 | 0.0006 |
| R+ | hdPS200+ECG8-vs-hdPS200 | 8 | -0.0116 | 0.4297 | -0.0120 | 0.0138 | 0.7500 | -0.0139 | -0.0001 | -0.0001 |
| R+ | hdPS200+ECG16-vs-hdPS200 | 8 | -0.0075 | 0.0859 | -0.0119 | 0.0113 | 0.7500 | -0.0088 | -0.0014 | -0.0014 |
| R+ | hdPS200+ECG-vs-hdPS200 | 8 | -0.0085 | 0.7266 | -0.0137 | 0.0136 | 0.5000 | -0.0123 | 0.0020 | 0.0020 |
| R+ | hdPS200+ECG64-vs-hdPS200 | 8 | -0.0102 | 0.3516 | -0.0128 | 0.0144 | 0.5000 | -0.0122 | -0.0007 | -0.0007 |
| R+ | hdPS200+ECGpheno-vs-hdPS200 | 8 | -0.0130 | 0.2109 | -0.0151 | 0.0151 | 0.6250 | -0.0153 | -0.0015 | -0.0015 |

## I5 Supervised SHD logits and second ECG encoder (PRESENT-SHD LVEF<40 CNN penultimate layer, 32 PCs); SHD-scored cohort

| target | contrast | trials | mean_d_sqerr | p_signflip | share_trials_closer | loo_min | loo_max |
|---|---|---|---|---|---|---|---|
| RCT | C1 | 8 | -0.0446 | 0.0156 | 0.8750 | -0.0512 | -0.0087 |
| RCT | C2 | 8 | 0.0048 | 0.7031 | 0.5000 | -0.0041 | 0.0104 |
| RCT | sparse+SHD-vs-sparse | 8 | -0.0490 | 0.0391 | 0.8750 | -0.0571 | -0.0113 |
| RCT | sparse+ENC2-vs-sparse | 8 | -0.0422 | 0.0938 | 0.7500 | -0.0518 | -0.0113 |
| RCT | hdPS200+SHD-vs-hdPS200 | 8 | -0.0015 | 0.7812 | 0.6250 | -0.0065 | 0.0030 |
| RCT | hdPS200+ENC2-vs-hdPS200 | 8 | -0.0029 | 0.6484 | 0.5000 | -0.0079 | 0.0021 |
| R | C1 | 8 | -0.0139 | 0.3281 | 0.7500 | -0.0166 | -0.0005 |
| R | C2 | 8 | -0.0130 | 0.5547 | 0.6250 | -0.0179 | 0.0009 |
| R | sparse+SHD-vs-sparse | 8 | -0.0149 | 0.1016 | 0.6250 | -0.0171 | -0.0010 |
| R | sparse+ENC2-vs-sparse | 8 | -0.0098 | 0.8438 | 0.3750 | -0.0133 | 0.0025 |
| R | hdPS200+SHD-vs-hdPS200 | 8 | -0.0101 | 0.3125 | 0.6250 | -0.0124 | -0.0011 |
| R | hdPS200+ENC2-vs-hdPS200 | 8 | -0.0114 | 0.0547 | 0.7500 | -0.0132 | -0.0028 |
| R+ | C1 | 8 | -0.0169 | 0.5391 | 0.6250 | -0.0202 | 0.0003 |
| R+ | C2 | 8 | -0.0085 | 0.7266 | 0.5000 | -0.0123 | 0.0020 |
| R+ | sparse+SHD-vs-sparse | 8 | -0.0171 | 0.8516 | 0.5000 | -0.0203 | 0.0010 |
| R+ | sparse+ENC2-vs-sparse | 8 | -0.0107 | 0.8906 | 0.5000 | -0.0146 | 0.0052 |
| R+ | hdPS200+SHD-vs-hdPS200 | 8 | -0.0071 | 0.4609 | 0.6250 | -0.0089 | -0.0001 |
| R+ | hdPS200+ENC2-vs-hdPS200 | 8 | -0.0078 | 0.2500 | 0.6250 | -0.0093 | -0.0010 |

## I6 Multiverse (4 PS models × 5 hdPS split seeds × 10 estimators = 200 specifications; imputation 1)

Per specification: mean over trials of |log HR − target|; difference first arm − comparator (negative favours the first arm).

| contrast | target | metric | specs | share_favouring | median_diff | q10 | q90 | base_spec_diff |
|---|---|---|---|---|---|---|---|---|
| C1 | rct | mean_abs | 200 | 0.9500 | -0.0288 | -0.0502 | -0.0090 | -0.0462 |
| C1 | rct | mean_sq | 200 | 0.9750 | -0.0355 | -0.0494 | -0.0201 | -0.0446 |
| C1 | rplus | mean_abs | 200 | 0.9750 | -0.0272 | -0.0426 | -0.0145 | -0.0275 |
| C1 | rplus | mean_sq | 200 | 0.9750 | -0.0153 | -0.0227 | -0.0098 | -0.0169 |
| C2 | rct | mean_abs | 200 | 0.7600 | -0.0110 | -0.0302 | 0.0130 | 0.0166 |
| C2 | rct | mean_sq | 200 | 0.7050 | -0.0041 | -0.0130 | 0.0067 | 0.0048 |
| C2 | rplus | mean_abs | 200 | 0.5100 | -0.0002 | -0.0134 | 0.0139 | -0.0126 |
| C2 | rplus | mean_sq | 200 | 0.5600 | -0.0002 | -0.0028 | 0.0030 | -0.0085 |
| sparse+noise32-vs-sparse | rct | mean_abs | 200 | 0.5150 | -0.0011 | -0.0188 | 0.0184 | 0.0099 |
| sparse+noise32-vs-sparse | rct | mean_sq | 200 | 0.5250 | -0.0002 | -0.0260 | 0.0116 | -0.0061 |
| sparse+noise32-vs-sparse | rplus | mean_abs | 200 | 0.4900 | 0.0005 | -0.0162 | 0.0139 | 0.0153 |
| sparse+noise32-vs-sparse | rplus | mean_sq | 200 | 0.5700 | -0.0006 | -0.0136 | 0.0069 | -0.0027 |
| sparse+shufECG-vs-sparse | rct | mean_abs | 200 | 0.6000 | -0.0038 | -0.0119 | 0.0143 | -0.0046 |
| sparse+shufECG-vs-sparse | rct | mean_sq | 200 | 0.5000 | -0.0001 | -0.0244 | 0.0108 | -0.0218 |
| sparse+shufECG-vs-sparse | rplus | mean_abs | 200 | 0.4250 | 0.0039 | -0.0178 | 0.0120 | -0.0060 |
| sparse+shufECG-vs-sparse | rplus | mean_sq | 200 | 0.4500 | 0.0003 | -0.0115 | 0.0048 | -0.0098 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_abs | 200 | 0.9750 | -0.0344 | -0.0486 | -0.0056 | -0.0416 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_sq | 200 | 1.0000 | -0.0259 | -0.0443 | -0.0200 | -0.0228 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_abs | 200 | 1.0000 | -0.0291 | -0.0482 | -0.0157 | -0.0215 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_sq | 200 | 1.0000 | -0.0141 | -0.0232 | -0.0068 | -0.0071 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_abs | 200 | 0.4400 | 0.0021 | -0.0131 | 0.0236 | 0.0222 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_sq | 200 | 0.3250 | 0.0017 | -0.0045 | 0.0146 | 0.0074 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_abs | 200 | 0.3150 | 0.0053 | -0.0090 | 0.0224 | -0.0082 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_sq | 200 | 0.3050 | 0.0011 | -0.0024 | 0.0054 | -0.0076 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_abs | 200 | 0.4700 | 0.0012 | -0.0140 | 0.0223 | 0.0028 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_sq | 200 | 0.4300 | 0.0011 | -0.0054 | 0.0102 | 0.0038 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_abs | 200 | 0.4300 | 0.0029 | -0.0147 | 0.0214 | -0.0181 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_sq | 200 | 0.3950 | 0.0004 | -0.0034 | 0.0043 | -0.0106 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_abs | 200 | 0.8300 | -0.0118 | -0.0314 | 0.0073 | 0.0137 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_sq | 200 | 0.8300 | -0.0052 | -0.0141 | 0.0025 | 0.0010 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_abs | 200 | 0.5500 | -0.0010 | -0.0196 | 0.0114 | 0.0055 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_sq | 200 | 0.6250 | -0.0005 | -0.0043 | 0.0028 | 0.0021 |

## I7 Exact sign-flip permutation (frozen phase-2 estimates vs RCT) and leave-one-trial-out

| contrast | trials | mean_d_sqerr | p_signflip | loo_min | loo_max | trials_ecg_closer | p_sign_test_supplementary |
|---|---|---|---|---|---|---|---|
| C1 | 8 | -0.0446 | 0.0156 | -0.0512 | -0.0087 | 7 | 0.0703 |
| C2 | 8 | 0.0048 | 0.7031 | -0.0041 | 0.0104 | 4 | 1.0000 |

**Detectability.** Trials needed to detect the plasmode-expected reduction in |log HR − RCT| (paired t, two-sided α = 0.05, 80% power), using the between-trial SD of the frozen phase-2 paired differences:

| contrast | scenario | expected_gain | sd_paired_abs_diff | trials_needed |
|---|---|---|---|---|
| C1 | base | 0.005 | 0.057 | 936.000 |
| C1 | phys_only | 0.002 | 0.057 | 6040.000 |
| C1 | strong | 0.009 | 0.057 | 319.000 |
| C2 | base | -0.003 | 0.085 | inf |
| C2 | phys_only | -0.001 | 0.085 | inf |
| C2 | strong | -0.001 | 0.085 | inf |

## I9 E-values for the disagreement with the RCT (HR ratio; rare-outcome approximation)

| arm | median_evalue | max_evalue |
|---|---|---|
| M0 unadjusted | 1.71 | 7.90 |
| M1 sparse | 1.69 | 4.43 |
| M2 sparse+ECG | 1.61 | 3.59 |
| M3 hdPS200 | 1.59 | 1.93 |
| M4 hdPS200+ECG | 1.67 | 1.98 |
| R clinical | 1.56 | 2.64 |

## Part II: closer to the trial (agreement with the RCT per analysis)

Validation: max |log HR(design primary) − log HR(phase 2)| = 0.00e+00 over 48 arm-trials.

| analysis | arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|---|
| primary | R+ physiology ref | 8 | 0.172 | 3 | 5 | 1.640 | 0.104 | 0.500 |
| primary | R clinical | 8 | 0.171 | 5 | 5 | 1.622 | 0.112 | 0.500 |
| primary | M3 hdPS200 | 8 | 0.159 | 3 | 4 | 1.722 | 0.143 | 0.500 |
| primary | M4 hdPS200+ECG | 8 | 0.175 | 2 | 5 | 1.780 | 0.145 | 0.250 |
| primary | M1 sparse | 8 | 0.249 | 3 | 3 | 2.356 | 0.200 | 0.375 |
| primary | M2 sparse+ECG | 8 | 0.203 | 4 | 5 | 1.938 | 0.155 | 0.375 |
| primary | M0 unadjusted | 8 | 0.327 | 4 | 4 | 3.201 | 0.318 | 0.500 |
| strict | R+ physiology ref | 8 | 0.216 | 4 | 5 | 1.538 | 0.155 | 0.500 |
| strict | R clinical | 8 | 0.209 | 4 | 6 | 1.603 | 0.197 | 0.500 |
| strict | M3 hdPS200 | 8 | 0.204 | 3 | 6 | 1.706 | 0.184 | 0.750 |
| strict | M4 hdPS200+ECG | 8 | 0.155 | 5 | 6 | 1.373 | 0.138 | 0.625 |
| strict | M1 sparse | 8 | 0.305 | 2 | 4 | 2.304 | 0.294 | 0.500 |
| strict | M2 sparse+ECG | 8 | 0.284 | 3 | 5 | 2.137 | 0.239 | 0.500 |
| strict | M0 unadjusted | 8 | 0.418 | 2 | 4 | 3.372 | 0.436 | 0.500 |
| transport | R+ physiology ref | 8 | 0.190 | 4 | 7 | 1.095 | 0.134 | 0.625 |
| transport | R clinical | 8 | 0.184 | 4 | 6 | 1.183 | 0.167 | 0.625 |
| transport | M3 hdPS200 | 8 | 0.172 | 4 | 6 | 1.190 | 0.194 | 0.750 |
| transport | M4 hdPS200+ECG | 8 | 0.162 | 5 | 6 | 1.103 | 0.167 | 0.625 |
| transport | M1 sparse | 8 | 0.267 | 2 | 5 | 1.756 | 0.292 | 0.625 |
| transport | M2 sparse+ECG | 8 | 0.216 | 4 | 6 | 1.394 | 0.225 | 0.625 |
| transport | M0 unadjusted | 8 | 0.377 | 3 | 3 | 2.853 | 0.431 | 0.375 |
| transport_ess20 | R+ physiology ref | 8 | 0.189 | 4 | 7 | 1.160 | 0.124 | 0.625 |
| transport_ess20 | R clinical | 8 | 0.189 | 4 | 6 | 1.253 | 0.148 | 0.625 |
| transport_ess20 | M3 hdPS200 | 8 | 0.169 | 4 | 6 | 1.290 | 0.186 | 0.750 |
| transport_ess20 | M4 hdPS200+ECG | 8 | 0.164 | 5 | 6 | 1.180 | 0.157 | 0.625 |
| transport_ess20 | M1 sparse | 8 | 0.263 | 2 | 5 | 1.830 | 0.269 | 0.625 |
| transport_ess20 | M2 sparse+ECG | 8 | 0.222 | 4 | 6 | 1.502 | 0.202 | 0.625 |
| transport_ess20 | M0 unadjusted | 8 | 0.377 | 3 | 3 | 2.917 | 0.404 | 0.375 |
| pp_naive_365 | R+ physiology ref | 7 | 0.157 | 3 | 4 | 1.582 | 0.171 | 0.571 |
| pp_naive_365 | R clinical | 7 | 0.153 | 3 | 4 | 1.655 | 0.175 | 0.571 |
| pp_naive_365 | M3 hdPS200 | 7 | 0.204 | 3 | 3 | 2.014 | 0.232 | 0.429 |
| pp_naive_365 | M4 hdPS200+ECG | 7 | 0.203 | 2 | 3 | 1.994 | 0.223 | 0.429 |
| pp_naive_365 | M1 sparse | 7 | 0.208 | 3 | 3 | 2.238 | 0.230 | 0.429 |
| pp_naive_365 | M2 sparse+ECG | 7 | 0.168 | 3 | 4 | 1.852 | 0.180 | 0.429 |
| pp_naive_365 | M0 unadjusted | 7 | 0.244 | 3 | 3 | 2.851 | 0.301 | 0.429 |
| pp_ipcw_365 | R+ physiology ref | 7 | 0.156 | 3 | 5 | 1.513 | 0.164 | 0.571 |
| pp_ipcw_365 | R clinical | 7 | 0.155 | 3 | 4 | 1.601 | 0.169 | 0.571 |
| pp_ipcw_365 | M3 hdPS200 | 7 | 0.199 | 3 | 3 | 1.901 | 0.230 | 0.429 |
| pp_ipcw_365 | M4 hdPS200+ECG | 7 | 0.204 | 2 | 3 | 1.897 | 0.217 | 0.429 |
| pp_ipcw_365 | M1 sparse | 7 | 0.210 | 3 | 3 | 2.169 | 0.229 | 0.429 |
| pp_ipcw_365 | M2 sparse+ECG | 7 | 0.166 | 3 | 4 | 1.772 | 0.177 | 0.571 |
| pp_ipcw_365 | M0 unadjusted | 7 | 0.243 | 3 | 3 | 2.755 | 0.302 | 0.429 |
| pp_ipcw_180 | R+ physiology ref | 7 | 0.301 | 1 | 3 | 2.139 | 0.275 | 0.429 |
| pp_ipcw_180 | R clinical | 7 | 0.301 | 1 | 3 | 2.251 | 0.280 | 0.429 |
| pp_ipcw_180 | M3 hdPS200 | 7 | 0.317 | 2 | 3 | 2.418 | 0.348 | 0.429 |
| pp_ipcw_180 | M4 hdPS200+ECG | 7 | 0.331 | 1 | 2 | 2.388 | 0.326 | 0.286 |
| pp_ipcw_180 | M1 sparse | 7 | 0.333 | 2 | 3 | 2.679 | 0.310 | 0.429 |
| pp_ipcw_180 | M2 sparse+ECG | 7 | 0.320 | 1 | 3 | 2.506 | 0.271 | 0.429 |
| pp_ipcw_180 | M0 unadjusted | 7 | 0.337 | 2 | 3 | 3.200 | 0.389 | 0.429 |
| pp_ipcw_730 | R+ physiology ref | 7 | 0.140 | 4 | 5 | 1.498 | 0.127 | 0.429 |
| pp_ipcw_730 | R clinical | 7 | 0.130 | 3 | 5 | 1.481 | 0.129 | 0.571 |
| pp_ipcw_730 | M3 hdPS200 | 7 | 0.173 | 3 | 3 | 1.869 | 0.192 | 0.429 |
| pp_ipcw_730 | M4 hdPS200+ECG | 7 | 0.176 | 2 | 3 | 1.845 | 0.186 | 0.429 |
| pp_ipcw_730 | M1 sparse | 7 | 0.170 | 3 | 3 | 2.028 | 0.185 | 0.429 |
| pp_ipcw_730 | M2 sparse+ECG | 7 | 0.150 | 3 | 3 | 1.763 | 0.154 | 0.429 |
| pp_ipcw_730 | M0 unadjusted | 7 | 0.226 | 2 | 3 | 2.777 | 0.261 | 0.429 |
| pp_naive_switch | R+ physiology ref | 7 | 0.146 | 4 | 5 | 1.663 | 0.119 | 0.429 |
| pp_naive_switch | R clinical | 7 | 0.135 | 3 | 5 | 1.614 | 0.119 | 0.571 |
| pp_naive_switch | M3 hdPS200 | 7 | 0.175 | 3 | 3 | 2.018 | 0.179 | 0.429 |
| pp_naive_switch | M4 hdPS200+ECG | 7 | 0.174 | 2 | 3 | 1.977 | 0.173 | 0.429 |
| pp_naive_switch | M1 sparse | 7 | 0.164 | 3 | 3 | 2.084 | 0.163 | 0.429 |
| pp_naive_switch | M2 sparse+ECG | 7 | 0.133 | 3 | 3 | 1.730 | 0.137 | 0.429 |
| pp_naive_switch | M0 unadjusted | 7 | 0.196 | 3 | 3 | 2.719 | 0.240 | 0.429 |
| pp_ipcw_switch | R+ physiology ref | 7 | 0.145 | 4 | 5 | 1.597 | 0.114 | 0.429 |
| pp_ipcw_switch | R clinical | 7 | 0.135 | 3 | 5 | 1.562 | 0.116 | 0.571 |
| pp_ipcw_switch | M3 hdPS200 | 7 | 0.172 | 3 | 3 | 1.920 | 0.177 | 0.429 |
| pp_ipcw_switch | M4 hdPS200+ECG | 7 | 0.173 | 2 | 3 | 1.885 | 0.170 | 0.429 |
| pp_ipcw_switch | M1 sparse | 7 | 0.165 | 3 | 3 | 2.030 | 0.162 | 0.429 |
| pp_ipcw_switch | M2 sparse+ECG | 7 | 0.133 | 3 | 4 | 1.681 | 0.133 | 0.429 |
| pp_ipcw_switch | M0 unadjusted | 7 | 0.197 | 3 | 3 | 2.650 | 0.240 | 0.429 |
| runin90 | R+ physiology ref | 5 | 0.141 | 3 | 5 | 0.530 | 0.000 | 1.000 |
| runin90 | R clinical | 5 | 0.199 | 1 | 5 | 0.632 | 0.000 | 1.000 |
| runin90 | M3 hdPS200 | 5 | 0.181 | 3 | 3 | 1.134 | 0.190 | 0.600 |
| runin90 | M4 hdPS200+ECG | 5 | 0.229 | 1 | 3 | 1.321 | 0.300 | 0.600 |
| runin90 | M1 sparse | 5 | 0.191 | 1 | 4 | 0.976 | 0.073 | 0.800 |
| runin90 | M2 sparse+ECG | 5 | 0.195 | 2 | 5 | 1.026 | 0.051 | 0.800 |
| runin90 | M0 unadjusted | 7 | 0.202 | 2 | 5 | 1.851 | 0.215 | 0.571 |

## I8 Empirical calibration with expanded negative controls

Systematic error estimated from negative controls (per trial, pooled across trials if < 8 usable NCOs):

| arm | mean_mu | mean_abs_mu | mean_sigma | median_nco |
|---|---|---|---|---|
| R+ physiology ref | 0.020 | 0.066 | 0.013 | 23.000 |
| R clinical | 0.025 | 0.076 | 0.014 | 23.500 |
| M3 hdPS200 | 0.040 | 0.049 | 0.011 | 22.500 |
| M4 hdPS200+ECG | 0.018 | 0.038 | 0.034 | 22.500 |
| M1 sparse | -0.004 | 0.077 | 0.072 | 22.500 |
| M2 sparse+ECG | 0.012 | 0.056 | 0.041 | 22.500 |
| M0 unadjusted | 0.030 | 0.059 | 0.076 | 24.500 |

- C1 (M2 sparse+ECG − M1 sparse): mean Δσ = -0.031 (sign-flip p = 0.047); mean Δ|μ| = -0.021 (p = 0.117)
- C2 (M4 hdPS200+ECG − M3 hdPS200): mean Δσ = +0.022 (sign-flip p = 0.312); mean Δ|μ| = -0.012 (p = 0.703)

Agreement with the RCT after empirical calibration of the primary estimates:

| arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|
| R+ physiology ref | 8 | 0.181 | 3 | 5 | 1.732 | 0.110 | 0.500 |
| R clinical | 8 | 0.191 | 2 | 5 | 1.839 | 0.116 | 0.375 |
| M3 hdPS200 | 8 | 0.176 | 3 | 4 | 1.846 | 0.154 | 0.500 |
| M4 hdPS200+ECG | 8 | 0.179 | 2 | 5 | 1.786 | 0.151 | 0.375 |
| M1 sparse | 8 | 0.256 | 3 | 6 | 1.919 | 0.194 | 0.500 |
| M2 sparse+ECG | 8 | 0.207 | 4 | 5 | 1.818 | 0.128 | 0.625 |
| M0 unadjusted | 8 | 0.350 | 3 | 4 | 2.534 | 0.289 | 0.375 |

## Stratified by trial role (physiology vs control)

| role | trials | contrast | plasmode_rs_bias_reduction | pl_lo | pl_hi | RCT_d | RCT_p_signflip | R+_d | R+_p_signflip | multiverse_share_rct |
|---|---|---|---|---|---|---|---|---|---|---|
| physiology | 3 | C1 | 0.0159 | 0.0111 | 0.0208 | -0.1035 | 0.2500 | -0.0461 | 0.5000 | 0.9500 |
| physiology | 3 | C2 | -0.0014 | -0.0069 | 0.0040 | 0.0309 | 0.5000 | -0.0216 | 0.7500 | 0.6850 |
| control | 5 | C1 | -0.0012 | -0.0039 | 0.0016 | -0.0093 | 0.1250 | 0.0006 | 0.9375 | 0.9000 |
| control | 5 | C2 | -0.0046 | -0.0076 | -0.0016 | -0.0109 | 0.3125 | -0.0007 | 0.9375 | 0.7750 |

## Pre-specified decision rules

- C1 rule 1 (plasmode [ss] base: bias-reduction CI excludes 0, > 0): **met**
- C1 rule 1b (plasmode [ss] phys_only, supportive): **not met**
- C1 rule 3 (plasmode [ss] base: less biased than shuffled-ECG placebo): **met**
- C2 rule 1 (plasmode [ss] base: bias-reduction CI excludes 0, > 0): **not met**
- C2 rule 1b (plasmode [ss] phys_only, supportive): **not met**
- C2 rule 3 (plasmode [ss] base: less biased than shuffled-ECG placebo): **not met**
- C1 rule 2 (vs RCT: mean Δ squared error < 0, exact sign-flip p < 0.05; audit fix): **met**
- C1 rule 2 (vs R+: mean Δ squared error < 0, exact sign-flip p < 0.05; audit fix): **not met**
- C1 rule 3 (beats shuffled-ECG placebo vs R+: sign-flip p < 0.05): **not met**
- C1 rule 4b (leave-one-out: sign holds in every set vs R+): **not met**
- C2 rule 2 (vs RCT: mean Δ squared error < 0, exact sign-flip p < 0.05; audit fix): **not met**
- C2 rule 2 (vs R+: mean Δ squared error < 0, exact sign-flip p < 0.05; audit fix): **not met**
- C2 rule 3 (beats shuffled-ECG placebo vs R+: sign-flip p < 0.05): **not met**
- C2 rule 4b (leave-one-out: sign holds in every set vs R+): **not met**
- C1 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **met**
- C2 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **not met**
