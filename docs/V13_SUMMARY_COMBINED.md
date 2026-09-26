# v1.3 exploratory robustness program — trial set: combined (18 trials)

Trials: comet, paradigm-hf-seq, transform-hf, elite-ii, life, plato, aristotle, rocket-af, rely, allhat, emperor-preserved-v2, east-afnet4, cabana-v2, ontarget, value, ascot, empa-reg, carolina

All analyses are exploratory (registered 2026-09-25 after phase 2; tag protocol-v1.3).

## I1 Plasmode simulation — 80% subsample without replacement, PS and matching refitted per replicate (audit fix; decides rule 1)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.010 | 0.019 | 0.098 | 0.958 |
| R clinical | 18 | -0.013 | 0.022 | 0.098 | 0.948 |
| M3 hdPS200 | 18 | -0.012 | 0.034 | 0.104 | 0.945 |
| M4 hdPS200+ECG | 18 | -0.010 | 0.034 | 0.106 | 0.938 |
| M1 sparse | 18 | -0.036 | 0.059 | 0.118 | 0.856 |
| M2 sparse+ECG | 18 | -0.031 | 0.055 | 0.117 | 0.869 |
| M0 unadjusted | 18 | -0.107 | 0.192 | 0.216 | 0.434 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.014 | 0.018 | 0.101 | 0.946 |
| R clinical | 18 | -0.014 | 0.020 | 0.098 | 0.952 |
| M3 hdPS200 | 18 | -0.022 | 0.030 | 0.104 | 0.939 |
| M4 hdPS200+ECG | 18 | -0.020 | 0.031 | 0.105 | 0.939 |
| M1 sparse | 18 | -0.034 | 0.044 | 0.108 | 0.908 |
| M2 sparse+ECG | 18 | -0.032 | 0.040 | 0.108 | 0.914 |
| M0 unadjusted | 18 | -0.102 | 0.155 | 0.183 | 0.576 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.015 | 0.025 | 0.101 | 0.942 |
| R clinical | 18 | -0.016 | 0.026 | 0.099 | 0.942 |
| M3 hdPS200 | 18 | -0.023 | 0.044 | 0.111 | 0.912 |
| M4 hdPS200+ECG | 18 | -0.023 | 0.044 | 0.113 | 0.906 |
| M1 sparse | 18 | -0.057 | 0.084 | 0.136 | 0.793 |
| M2 sparse+ECG | 18 | -0.051 | 0.078 | 0.132 | 0.807 |
| M0 unadjusted | 18 | -0.132 | 0.222 | 0.245 | 0.394 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.013 | 0.017 | 0.100 | 0.951 |
| R clinical | 18 | -0.014 | 0.021 | 0.098 | 0.944 |
| M3 hdPS200 | 18 | -0.007 | 0.021 | 0.104 | 0.939 |
| M4 hdPS200+ECG | 18 | -0.006 | 0.021 | 0.104 | 0.940 |
| M1 sparse | 18 | -0.021 | 0.041 | 0.106 | 0.908 |
| M2 sparse+ECG | 18 | -0.018 | 0.039 | 0.106 | 0.908 |
| M0 unadjusted | 18 | -0.088 | 0.164 | 0.190 | 0.490 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.011 | 0.016 | 0.093 | 0.951 |
| R clinical | 18 | -0.012 | 0.019 | 0.092 | 0.947 |
| M3 hdPS200 | 18 | -0.011 | 0.034 | 0.099 | 0.932 |
| M4 hdPS200+ECG | 18 | -0.012 | 0.031 | 0.100 | 0.934 |
| M1 sparse | 18 | -0.036 | 0.060 | 0.114 | 0.846 |
| M2 sparse+ECG | 18 | -0.033 | 0.055 | 0.112 | 0.858 |
| M0 unadjusted | 18 | -0.107 | 0.191 | 0.213 | 0.416 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 18 | 0.004 | 0.001 | 0.006 | 0.067 |
| base | C2 | 18 | 0.000 | -0.002 | 0.002 | 0.000 |
| base | sparse+noise32-vs-sparse | 18 | -0.002 | -0.004 | 0.001 | -0.031 |
| base | sparse+shufECG-vs-sparse | 18 | -0.002 | -0.004 | 0.000 | -0.031 |
| base | sparse+ECG-vs-sparse+shufECG | 18 | 0.006 | 0.004 | 0.008 | 0.095 |
| base | hdPS200+noise32-vs-hdPS200 | 18 | -0.001 | -0.003 | 0.002 | -0.015 |
| base | hdPS200+shufECG-vs-hdPS200 | 18 | -0.001 | -0.003 | 0.001 | -0.027 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.001 | -0.001 | 0.003 | 0.026 |
| none | C1 | 18 | 0.001 | -0.001 | 0.004 | 0.036 |
| none | C2 | 18 | 0.001 | -0.002 | 0.003 | 0.030 |
| none | sparse+noise32-vs-sparse | 18 | 0.001 | -0.001 | 0.003 | 0.017 |
| none | sparse+shufECG-vs-sparse | 18 | -0.002 | -0.005 | -0.000 | -0.052 |
| none | sparse+ECG-vs-sparse+shufECG | 18 | 0.004 | 0.001 | 0.006 | 0.084 |
| none | hdPS200+noise32-vs-hdPS200 | 18 | -0.000 | -0.003 | 0.002 | -0.001 |
| none | hdPS200+shufECG-vs-hdPS200 | 18 | -0.001 | -0.004 | 0.002 | -0.045 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.002 | -0.001 | 0.004 | 0.071 |
| null | C1 | 18 | 0.005 | 0.003 | 0.007 | 0.090 |
| null | C2 | 18 | 0.004 | 0.001 | 0.005 | 0.104 |
| null | sparse+noise32-vs-sparse | 18 | -0.000 | -0.003 | 0.002 | -0.005 |
| null | sparse+shufECG-vs-sparse | 18 | -0.001 | -0.004 | 0.001 | -0.017 |
| null | sparse+ECG-vs-sparse+shufECG | 18 | 0.006 | 0.004 | 0.009 | 0.105 |
| null | hdPS200+noise32-vs-hdPS200 | 18 | 0.002 | -0.000 | 0.004 | 0.064 |
| null | hdPS200+shufECG-vs-hdPS200 | 18 | 0.002 | -0.001 | 0.004 | 0.054 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.002 | -0.001 | 0.004 | 0.053 |
| phys_only | C1 | 18 | 0.004 | 0.002 | 0.007 | 0.099 |
| phys_only | C2 | 18 | -0.001 | -0.003 | 0.001 | -0.043 |
| phys_only | sparse+noise32-vs-sparse | 18 | 0.007 | 0.004 | 0.009 | 0.151 |
| phys_only | sparse+shufECG-vs-sparse | 18 | 0.003 | 0.000 | 0.005 | 0.061 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 18 | 0.002 | -0.001 | 0.004 | 0.040 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 18 | 0.001 | -0.002 | 0.003 | 0.023 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 18 | -0.002 | -0.004 | 0.000 | -0.062 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.001 | -0.002 | 0.004 | 0.018 |
| strong | C1 | 18 | 0.006 | 0.004 | 0.009 | 0.076 |
| strong | C2 | 18 | -0.000 | -0.002 | 0.002 | -0.005 |
| strong | sparse+noise32-vs-sparse | 18 | 0.001 | -0.002 | 0.003 | 0.012 |
| strong | sparse+shufECG-vs-sparse | 18 | -0.001 | -0.004 | 0.001 | -0.012 |
| strong | sparse+ECG-vs-sparse+shufECG | 18 | 0.007 | 0.005 | 0.010 | 0.087 |
| strong | hdPS200+noise32-vs-hdPS200 | 18 | -0.003 | -0.005 | -0.001 | -0.074 |
| strong | hdPS200+shufECG-vs-hdPS200 | 18 | -0.004 | -0.006 | -0.002 | -0.099 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.004 | 0.002 | 0.006 | 0.086 |

## I1 Plasmode simulation — bootstrap resample with replacement (deviation 6; duplicates distort matching — superseded)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.008 | 0.021 | 0.091 | 0.944 |
| R clinical | 18 | -0.012 | 0.021 | 0.089 | 0.943 |
| M3 hdPS200 | 18 | -0.013 | 0.033 | 0.098 | 0.928 |
| M4 hdPS200+ECG | 18 | -0.010 | 0.034 | 0.101 | 0.922 |
| M1 sparse | 18 | -0.036 | 0.059 | 0.111 | 0.828 |
| M2 sparse+ECG | 18 | -0.030 | 0.054 | 0.108 | 0.840 |
| M0 unadjusted | 18 | -0.107 | 0.192 | 0.214 | 0.385 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.016 | 0.020 | 0.092 | 0.948 |
| R clinical | 18 | -0.016 | 0.021 | 0.089 | 0.951 |
| M3 hdPS200 | 18 | -0.025 | 0.036 | 0.101 | 0.919 |
| M4 hdPS200+ECG | 18 | -0.023 | 0.032 | 0.102 | 0.919 |
| M1 sparse | 18 | -0.031 | 0.040 | 0.100 | 0.888 |
| M2 sparse+ECG | 18 | -0.032 | 0.040 | 0.099 | 0.902 |
| M0 unadjusted | 18 | -0.103 | 0.154 | 0.180 | 0.528 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.017 | 0.022 | 0.090 | 0.949 |
| R clinical | 18 | -0.015 | 0.024 | 0.088 | 0.941 |
| M3 hdPS200 | 18 | -0.024 | 0.047 | 0.104 | 0.894 |
| M4 hdPS200+ECG | 18 | -0.021 | 0.046 | 0.107 | 0.892 |
| M1 sparse | 18 | -0.057 | 0.085 | 0.129 | 0.776 |
| M2 sparse+ECG | 18 | -0.050 | 0.076 | 0.124 | 0.791 |
| M0 unadjusted | 18 | -0.132 | 0.222 | 0.242 | 0.360 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.011 | 0.015 | 0.092 | 0.946 |
| R clinical | 18 | -0.013 | 0.019 | 0.088 | 0.950 |
| M3 hdPS200 | 18 | -0.005 | 0.022 | 0.096 | 0.935 |
| M4 hdPS200+ECG | 18 | -0.003 | 0.023 | 0.098 | 0.933 |
| M1 sparse | 18 | -0.020 | 0.041 | 0.098 | 0.897 |
| M2 sparse+ECG | 18 | -0.017 | 0.038 | 0.099 | 0.894 |
| M0 unadjusted | 18 | -0.087 | 0.165 | 0.187 | 0.440 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.014 | 0.018 | 0.086 | 0.948 |
| R clinical | 18 | -0.013 | 0.019 | 0.086 | 0.945 |
| M3 hdPS200 | 18 | -0.014 | 0.035 | 0.096 | 0.916 |
| M4 hdPS200+ECG | 18 | -0.013 | 0.035 | 0.096 | 0.920 |
| M1 sparse | 18 | -0.039 | 0.063 | 0.110 | 0.819 |
| M2 sparse+ECG | 18 | -0.033 | 0.055 | 0.105 | 0.839 |
| M0 unadjusted | 18 | -0.107 | 0.192 | 0.212 | 0.359 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 18 | 0.005 | 0.002 | 0.007 | 0.080 |
| base | C2 | 18 | -0.001 | -0.003 | 0.001 | -0.032 |
| base | sparse+noise32-vs-sparse | 18 | 0.000 | -0.002 | 0.003 | 0.002 |
| base | sparse+shufECG-vs-sparse | 18 | -0.002 | -0.005 | -0.000 | -0.041 |
| base | sparse+ECG-vs-sparse+shufECG | 18 | 0.007 | 0.005 | 0.009 | 0.116 |
| base | hdPS200+noise32-vs-hdPS200 | 18 | -0.001 | -0.003 | 0.001 | -0.030 |
| base | hdPS200+shufECG-vs-hdPS200 | 18 | -0.001 | -0.003 | 0.001 | -0.034 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.000 | -0.002 | 0.002 | 0.002 |
| none | C1 | 18 | 0.003 | 0.001 | 0.005 | 0.079 |
| none | C2 | 18 | -0.001 | -0.004 | 0.002 | -0.039 |
| none | sparse+noise32-vs-sparse | 18 | 0.001 | -0.001 | 0.003 | 0.018 |
| none | sparse+shufECG-vs-sparse | 18 | -0.002 | -0.004 | -0.000 | -0.048 |
| none | sparse+ECG-vs-sparse+shufECG | 18 | 0.005 | 0.002 | 0.007 | 0.122 |
| none | hdPS200+noise32-vs-hdPS200 | 18 | 0.000 | -0.003 | 0.002 | 0.009 |
| none | hdPS200+shufECG-vs-hdPS200 | 18 | -0.002 | -0.005 | 0.002 | -0.099 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.001 | -0.002 | 0.003 | 0.055 |
| null | C1 | 18 | 0.008 | 0.006 | 0.010 | 0.134 |
| null | C2 | 18 | 0.001 | -0.001 | 0.003 | 0.016 |
| null | sparse+noise32-vs-sparse | 18 | 0.001 | -0.001 | 0.003 | 0.011 |
| null | sparse+shufECG-vs-sparse | 18 | -0.001 | -0.003 | 0.001 | -0.016 |
| null | sparse+ECG-vs-sparse+shufECG | 18 | 0.010 | 0.007 | 0.011 | 0.148 |
| null | hdPS200+noise32-vs-hdPS200 | 18 | 0.000 | -0.002 | 0.002 | 0.004 |
| null | hdPS200+shufECG-vs-hdPS200 | 18 | 0.001 | -0.001 | 0.003 | 0.041 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 18 | -0.001 | -0.003 | 0.002 | -0.026 |
| phys_only | C1 | 18 | -0.000 | -0.002 | 0.002 | -0.002 |
| phys_only | C2 | 18 | 0.004 | 0.001 | 0.006 | 0.109 |
| phys_only | sparse+noise32-vs-sparse | 18 | 0.001 | -0.002 | 0.003 | 0.014 |
| phys_only | sparse+shufECG-vs-sparse | 18 | -0.000 | -0.002 | 0.002 | -0.002 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 18 | -0.000 | -0.002 | 0.002 | -0.000 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 18 | 0.002 | -0.001 | 0.004 | 0.044 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 18 | 0.002 | -0.001 | 0.004 | 0.051 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.002 | -0.000 | 0.004 | 0.061 |
| strong | C1 | 18 | 0.008 | 0.006 | 0.010 | 0.099 |
| strong | C2 | 18 | 0.000 | -0.002 | 0.002 | 0.009 |
| strong | sparse+noise32-vs-sparse | 18 | 0.001 | -0.001 | 0.003 | 0.015 |
| strong | sparse+shufECG-vs-sparse | 18 | -0.003 | -0.005 | -0.000 | -0.030 |
| strong | sparse+ECG-vs-sparse+shufECG | 18 | 0.011 | 0.009 | 0.013 | 0.125 |
| strong | hdPS200+noise32-vs-hdPS200 | 18 | -0.001 | -0.004 | 0.001 | -0.030 |
| strong | hdPS200+shufECG-vs-hdPS200 | 18 | -0.004 | -0.006 | -0.002 | -0.083 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.004 | 0.002 | 0.006 | 0.085 |

## I1 Plasmode simulation — fixed matched sets, as registered (flawed: conflates chance imbalance with bias)

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.013 | 0.023 | 0.090 | 0.948 |
| R clinical | 18 | -0.016 | 0.031 | 0.090 | 0.953 |
| M3 hdPS200 | 18 | -0.018 | 0.035 | 0.095 | 0.936 |
| M4 hdPS200+ECG | 18 | -0.011 | 0.033 | 0.096 | 0.929 |
| M1 sparse | 18 | -0.042 | 0.062 | 0.110 | 0.840 |
| M2 sparse+ECG | 18 | -0.031 | 0.053 | 0.105 | 0.855 |
| M0 unadjusted | 18 | -0.110 | 0.192 | 0.212 | 0.392 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.014 | 0.019 | 0.089 | 0.950 |
| R clinical | 18 | -0.016 | 0.027 | 0.092 | 0.940 |
| M3 hdPS200 | 18 | -0.030 | 0.037 | 0.095 | 0.927 |
| M4 hdPS200+ECG | 18 | -0.023 | 0.033 | 0.097 | 0.926 |
| M1 sparse | 18 | -0.033 | 0.044 | 0.100 | 0.890 |
| M2 sparse+ECG | 18 | -0.030 | 0.037 | 0.098 | 0.902 |
| M0 unadjusted | 18 | -0.104 | 0.157 | 0.180 | 0.526 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.017 | 0.030 | 0.088 | 0.944 |
| R clinical | 18 | -0.018 | 0.037 | 0.090 | 0.942 |
| M3 hdPS200 | 18 | -0.026 | 0.051 | 0.098 | 0.910 |
| M4 hdPS200+ECG | 18 | -0.021 | 0.047 | 0.099 | 0.886 |
| M1 sparse | 18 | -0.061 | 0.086 | 0.125 | 0.790 |
| M2 sparse+ECG | 18 | -0.046 | 0.072 | 0.120 | 0.794 |
| M0 unadjusted | 18 | -0.133 | 0.222 | 0.240 | 0.359 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.012 | 0.020 | 0.089 | 0.950 |
| R clinical | 18 | -0.011 | 0.025 | 0.088 | 0.953 |
| M3 hdPS200 | 18 | -0.008 | 0.026 | 0.090 | 0.940 |
| M4 hdPS200+ECG | 18 | -0.002 | 0.023 | 0.091 | 0.943 |
| M1 sparse | 18 | -0.017 | 0.040 | 0.094 | 0.914 |
| M2 sparse+ECG | 18 | -0.011 | 0.040 | 0.095 | 0.915 |
| M0 unadjusted | 18 | -0.084 | 0.162 | 0.184 | 0.442 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 18 | -0.014 | 0.027 | 0.086 | 0.942 |
| R clinical | 18 | -0.016 | 0.034 | 0.085 | 0.946 |
| M3 hdPS200 | 18 | -0.018 | 0.039 | 0.090 | 0.933 |
| M4 hdPS200+ECG | 18 | -0.011 | 0.033 | 0.092 | 0.920 |
| M1 sparse | 18 | -0.040 | 0.065 | 0.106 | 0.828 |
| M2 sparse+ECG | 18 | -0.031 | 0.056 | 0.104 | 0.832 |
| M0 unadjusted | 18 | -0.109 | 0.193 | 0.211 | 0.361 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 18 | 0.010 | 0.007 | 0.012 | 0.153 |
| base | C2 | 18 | 0.002 | -0.001 | 0.004 | 0.053 |
| base | sparse+noise32-vs-sparse | 18 | -0.003 | -0.006 | -0.001 | -0.054 |
| base | sparse+shufECG-vs-sparse | 18 | -0.001 | -0.003 | 0.001 | -0.012 |
| base | sparse+ECG-vs-sparse+shufECG | 18 | 0.010 | 0.008 | 0.012 | 0.164 |
| base | hdPS200+noise32-vs-hdPS200 | 18 | -0.000 | -0.004 | 0.003 | -0.009 |
| base | hdPS200+shufECG-vs-hdPS200 | 18 | -0.001 | -0.004 | 0.002 | -0.026 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.003 | 0.001 | 0.004 | 0.077 |
| none | C1 | 18 | 0.000 | -0.002 | 0.002 | 0.002 |
| none | C2 | 18 | 0.003 | -0.000 | 0.006 | 0.118 |
| none | sparse+noise32-vs-sparse | 18 | 0.000 | -0.003 | 0.003 | 0.005 |
| none | sparse+shufECG-vs-sparse | 18 | -0.001 | -0.003 | 0.002 | -0.013 |
| none | sparse+ECG-vs-sparse+shufECG | 18 | 0.001 | -0.002 | 0.003 | 0.014 |
| none | hdPS200+noise32-vs-hdPS200 | 18 | 0.003 | -0.000 | 0.006 | 0.110 |
| none | hdPS200+shufECG-vs-hdPS200 | 18 | -0.002 | -0.004 | 0.002 | -0.064 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.005 | 0.002 | 0.007 | 0.171 |
| null | C1 | 18 | 0.008 | 0.006 | 0.011 | 0.130 |
| null | C2 | 18 | 0.006 | 0.003 | 0.008 | 0.153 |
| null | sparse+noise32-vs-sparse | 18 | -0.002 | -0.005 | 0.000 | -0.033 |
| null | sparse+shufECG-vs-sparse | 18 | -0.002 | -0.004 | 0.000 | -0.028 |
| null | sparse+ECG-vs-sparse+shufECG | 18 | 0.010 | 0.008 | 0.012 | 0.154 |
| null | hdPS200+noise32-vs-hdPS200 | 18 | 0.001 | -0.002 | 0.004 | 0.030 |
| null | hdPS200+shufECG-vs-hdPS200 | 18 | 0.002 | -0.001 | 0.003 | 0.045 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.004 | 0.003 | 0.006 | 0.113 |
| phys_only | C1 | 18 | 0.008 | 0.005 | 0.010 | 0.178 |
| phys_only | C2 | 18 | 0.004 | 0.002 | 0.006 | 0.107 |
| phys_only | sparse+noise32-vs-sparse | 18 | 0.004 | 0.001 | 0.007 | 0.087 |
| phys_only | sparse+shufECG-vs-sparse | 18 | 0.003 | 0.000 | 0.005 | 0.070 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 18 | 0.005 | 0.003 | 0.007 | 0.116 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 18 | 0.006 | 0.003 | 0.009 | 0.158 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 18 | -0.000 | -0.003 | 0.003 | -0.010 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.004 | 0.001 | 0.008 | 0.115 |
| strong | C1 | 18 | 0.014 | 0.012 | 0.015 | 0.158 |
| strong | C2 | 18 | 0.004 | 0.002 | 0.006 | 0.074 |
| strong | sparse+noise32-vs-sparse | 18 | -0.004 | -0.007 | -0.002 | -0.044 |
| strong | sparse+shufECG-vs-sparse | 18 | -0.001 | -0.003 | 0.001 | -0.012 |
| strong | sparse+ECG-vs-sparse+shufECG | 18 | 0.015 | 0.012 | 0.017 | 0.169 |
| strong | hdPS200+noise32-vs-hdPS200 | 18 | 0.002 | -0.002 | 0.005 | 0.034 |
| strong | hdPS200+shufECG-vs-hdPS200 | 18 | -0.001 | -0.005 | 0.001 | -0.030 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.005 | 0.003 | 0.009 | 0.100 |

## I3 Within-trial paired bootstrap (200 replicates per trial)

Mean over trials of err(arm)² − err(comparator)² (negative = the first arm is closer to the target); 95% CI across bootstrap replicates; leave-one-trial-out range of the point estimate.

**Inference:** the exact sign-flip test across trials (p_signflip) is the valid test; the bootstrap CI (lo, hi) re-matches on resamples with duplicate patients, which is not valid for matching estimators (audit), and is shown for description only.

| target | contrast | trials | mean_d_sqerr | p_signflip | lo | hi | share_trials_closer | loo_min | loo_max | without_cabana |
|---|---|---|---|---|---|---|---|---|---|---|
| RCT | C1 | 18 | -0.0166 | 0.4965 | -0.0451 | 0.0086 | 0.7778 | -0.0243 | -0.0001 | -0.0001 |
| RCT | C2 | 18 | 0.0043 | 0.7567 | -0.0250 | 0.0277 | 0.5556 | -0.0045 | 0.0085 | 0.0007 |
| RCT | sparse+noise32-vs-sparse | 18 | 0.0007 | 0.9224 | -0.0278 | 0.0228 | 0.4444 | -0.0019 | 0.0060 | 0.0060 |
| RCT | sparse+shufECG-vs-sparse | 18 | -0.0076 | 0.7869 | -0.0261 | 0.0246 | 0.3889 | -0.0098 | 0.0023 | 0.0023 |
| RCT | sparse+ECG-vs-sparse+shufECG | 18 | -0.0090 | 0.3736 | -0.0393 | 0.0085 | 0.7222 | -0.0145 | -0.0025 | -0.0025 |
| RCT | hdPS200+noise32-vs-hdPS200 | 18 | -0.0090 | 0.3347 | -0.0225 | 0.0198 | 0.5556 | -0.0123 | -0.0022 | -0.0123 |
| RCT | hdPS200+shufECG-vs-hdPS200 | 18 | -0.0063 | 0.5195 | -0.0221 | 0.0213 | 0.5556 | -0.0113 | 0.0004 | -0.0113 |
| RCT | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.0107 | 0.8314 | -0.0247 | 0.0295 | 0.5000 | -0.0049 | 0.0147 | 0.0120 |
| RCT | sparse+ECG8-vs-sparse | 18 | -0.0000 | 0.9977 | -0.0270 | 0.0191 | 0.5556 | -0.0074 | 0.0058 | 0.0058 |
| RCT | sparse+ECG16-vs-sparse | 18 | -0.0066 | 0.5585 | -0.0317 | 0.0170 | 0.6667 | -0.0096 | 0.0007 | 0.0007 |
| RCT | sparse+ECG-vs-sparse | 18 | -0.0166 | 0.4965 | -0.0451 | 0.0086 | 0.7778 | -0.0243 | -0.0001 | -0.0001 |
| RCT | sparse+ECG64-vs-sparse | 18 | -0.0280 | 0.2722 | -0.0477 | -0.0046 | 0.6111 | -0.0313 | -0.0027 | -0.0027 |
| RCT | sparse+ECGpheno-vs-sparse | 18 | -0.0262 | 0.0541 | -0.0454 | 0.0013 | 0.7778 | -0.0286 | -0.0063 | -0.0063 |
| RCT | hdPS200+ECG8-vs-hdPS200 | 18 | -0.0058 | 0.4516 | -0.0269 | 0.0190 | 0.6667 | -0.0113 | -0.0017 | -0.0113 |
| RCT | hdPS200+ECG16-vs-hdPS200 | 18 | -0.0116 | 0.0572 | -0.0238 | 0.0222 | 0.7222 | -0.0139 | -0.0077 | -0.0139 |
| RCT | hdPS200+ECG-vs-hdPS200 | 18 | 0.0043 | 0.7567 | -0.0250 | 0.0277 | 0.5556 | -0.0045 | 0.0085 | 0.0007 |
| RCT | hdPS200+ECG64-vs-hdPS200 | 18 | -0.0067 | 0.2935 | -0.0235 | 0.0164 | 0.6667 | -0.0104 | -0.0042 | -0.0104 |
| RCT | hdPS200+ECGpheno-vs-hdPS200 | 18 | -0.0018 | 0.8383 | -0.0315 | 0.0209 | 0.6667 | -0.0073 | 0.0016 | -0.0073 |
| R | C1 | 18 | -0.0005 | 0.8677 | -0.0157 | 0.0071 | 0.5556 | -0.0060 | 0.0058 | 0.0058 |
| R | C2 | 18 | 0.0026 | 0.6413 | -0.0161 | 0.0179 | 0.4444 | -0.0054 | 0.0092 | 0.0092 |
| R | sparse+noise32-vs-sparse | 18 | 0.0009 | 0.7797 | -0.0110 | 0.0105 | 0.3333 | 0.0000 | 0.0031 | 0.0031 |
| R | sparse+shufECG-vs-sparse | 18 | -0.0032 | 0.5821 | -0.0086 | 0.0128 | 0.5000 | -0.0048 | 0.0006 | 0.0006 |
| R | sparse+ECG-vs-sparse+shufECG | 18 | 0.0027 | 0.6136 | -0.0155 | 0.0071 | 0.4444 | -0.0011 | 0.0052 | 0.0052 |
| R | hdPS200+noise32-vs-hdPS200 | 18 | -0.0104 | 0.3011 | -0.0151 | 0.0122 | 0.6111 | -0.0121 | -0.0049 | -0.0056 |
| R | hdPS200+shufECG-vs-hdPS200 | 18 | -0.0088 | 0.4431 | -0.0148 | 0.0148 | 0.3889 | -0.0120 | -0.0023 | -0.0023 |
| R | hdPS200+ECG-vs-hdPS200+shufECG | 18 | 0.0114 | 0.7281 | -0.0127 | 0.0175 | 0.6111 | -0.0020 | 0.0143 | 0.0115 |
| R | sparse+ECG8-vs-sparse | 18 | 0.0039 | 0.6091 | -0.0098 | 0.0123 | 0.3889 | -0.0019 | 0.0065 | 0.0065 |
| R | sparse+ECG16-vs-sparse | 18 | 0.0016 | 0.6912 | -0.0099 | 0.0105 | 0.4444 | -0.0003 | 0.0048 | 0.0048 |
| R | sparse+ECG-vs-sparse | 18 | -0.0005 | 0.8677 | -0.0157 | 0.0071 | 0.5556 | -0.0060 | 0.0058 | 0.0058 |
| R | sparse+ECG64-vs-sparse | 18 | -0.0070 | 0.7647 | -0.0157 | 0.0048 | 0.5556 | -0.0082 | 0.0010 | 0.0010 |
| R | sparse+ECGpheno-vs-sparse | 18 | -0.0076 | 0.4029 | -0.0172 | 0.0042 | 0.5556 | -0.0086 | -0.0007 | -0.0007 |
| R | hdPS200+ECG8-vs-hdPS200 | 18 | -0.0097 | 0.3412 | -0.0186 | 0.0139 | 0.6111 | -0.0115 | -0.0029 | -0.0029 |
| R | hdPS200+ECG16-vs-hdPS200 | 18 | -0.0063 | 0.2879 | -0.0129 | 0.0201 | 0.5556 | -0.0078 | -0.0028 | -0.0028 |
| R | hdPS200+ECG-vs-hdPS200 | 18 | 0.0026 | 0.6413 | -0.0161 | 0.0179 | 0.4444 | -0.0054 | 0.0092 | 0.0092 |
| R | hdPS200+ECG64-vs-hdPS200 | 18 | -0.0039 | 0.6440 | -0.0120 | 0.0207 | 0.4444 | -0.0073 | 0.0019 | 0.0019 |
| R | hdPS200+ECGpheno-vs-hdPS200 | 18 | -0.0044 | 0.6876 | -0.0147 | 0.0156 | 0.5000 | -0.0082 | 0.0029 | 0.0029 |
| R+ | C1 | 18 | -0.0084 | 0.3404 | -0.0179 | 0.0059 | 0.5556 | -0.0098 | -0.0008 | -0.0008 |
| R+ | C2 | 18 | -0.0017 | 0.7844 | -0.0175 | 0.0138 | 0.5556 | -0.0046 | 0.0030 | 0.0030 |
| R+ | sparse+noise32-vs-sparse | 18 | -0.0013 | 0.7628 | -0.0115 | 0.0136 | 0.5000 | -0.0023 | 0.0013 | 0.0013 |
| R+ | sparse+shufECG-vs-sparse | 18 | -0.0042 | 0.6591 | -0.0107 | 0.0144 | 0.4444 | -0.0050 | 0.0006 | 0.0006 |
| R+ | sparse+ECG-vs-sparse+shufECG | 18 | -0.0042 | 0.2087 | -0.0200 | 0.0073 | 0.7222 | -0.0052 | -0.0014 | -0.0014 |
| R+ | hdPS200+noise32-vs-hdPS200 | 18 | -0.0039 | 0.4827 | -0.0140 | 0.0115 | 0.4444 | -0.0051 | -0.0001 | -0.0001 |
| R+ | hdPS200+shufECG-vs-hdPS200 | 18 | -0.0010 | 0.9476 | -0.0148 | 0.0153 | 0.5000 | -0.0031 | 0.0041 | 0.0041 |
| R+ | hdPS200+ECG-vs-hdPS200+shufECG | 18 | -0.0008 | 0.8540 | -0.0149 | 0.0137 | 0.6667 | -0.0036 | 0.0010 | -0.0012 |
| R+ | sparse+ECG8-vs-sparse | 18 | -0.0025 | 0.5504 | -0.0110 | 0.0110 | 0.4444 | -0.0035 | 0.0003 | 0.0003 |
| R+ | sparse+ECG16-vs-sparse | 18 | -0.0044 | 0.3345 | -0.0119 | 0.0114 | 0.6111 | -0.0053 | -0.0008 | -0.0008 |
| R+ | sparse+ECG-vs-sparse | 18 | -0.0084 | 0.3404 | -0.0179 | 0.0059 | 0.5556 | -0.0098 | -0.0008 | -0.0008 |
| R+ | sparse+ECG64-vs-sparse | 18 | -0.0115 | 0.2943 | -0.0197 | 0.0030 | 0.6111 | -0.0130 | -0.0009 | -0.0009 |
| R+ | sparse+ECGpheno-vs-sparse | 18 | -0.0052 | 0.6634 | -0.0180 | 0.0063 | 0.5000 | -0.0100 | 0.0041 | 0.0041 |
| R+ | hdPS200+ECG8-vs-hdPS200 | 18 | -0.0053 | 0.4570 | -0.0163 | 0.0119 | 0.7222 | -0.0065 | -0.0002 | -0.0002 |
| R+ | hdPS200+ECG16-vs-hdPS200 | 18 | -0.0051 | 0.1326 | -0.0154 | 0.0163 | 0.6667 | -0.0062 | -0.0025 | -0.0025 |
| R+ | hdPS200+ECG-vs-hdPS200 | 18 | -0.0017 | 0.7844 | -0.0175 | 0.0138 | 0.5556 | -0.0046 | 0.0030 | 0.0030 |
| R+ | hdPS200+ECG64-vs-hdPS200 | 18 | 0.0004 | 0.9154 | -0.0137 | 0.0167 | 0.5000 | -0.0049 | 0.0050 | 0.0050 |
| R+ | hdPS200+ECGpheno-vs-hdPS200 | 18 | -0.0099 | 0.2205 | -0.0170 | 0.0140 | 0.6111 | -0.0115 | -0.0050 | -0.0050 |

## I5 Supervised SHD logits and second ECG encoder (PRESENT-SHD LVEF<40 CNN penultimate layer, 32 PCs); SHD-scored cohort

| target | contrast | trials | mean_d_sqerr | p_signflip | share_trials_closer | loo_min | loo_max |
|---|---|---|---|---|---|---|---|
| RCT | C1 | 18 | -0.0166 | 0.4965 | 0.7778 | -0.0243 | -0.0001 |
| RCT | C2 | 18 | 0.0043 | 0.7567 | 0.5556 | -0.0045 | 0.0085 |
| RCT | sparse+SHD-vs-sparse | 18 | -0.0256 | 0.0174 | 0.7778 | -0.0281 | -0.0086 |
| RCT | sparse+ENC2-vs-sparse | 18 | -0.0146 | 0.4803 | 0.4444 | -0.0185 | -0.0002 |
| RCT | hdPS200+SHD-vs-hdPS200 | 18 | -0.0119 | 0.0450 | 0.6667 | -0.0145 | -0.0083 |
| RCT | hdPS200+ENC2-vs-hdPS200 | 18 | 0.0059 | 0.9167 | 0.6111 | -0.0060 | 0.0087 |
| R | C1 | 18 | -0.0005 | 0.8677 | 0.5556 | -0.0060 | 0.0058 |
| R | C2 | 18 | 0.0026 | 0.6413 | 0.4444 | -0.0054 | 0.0092 |
| R | sparse+SHD-vs-sparse | 18 | -0.0069 | 0.3182 | 0.5556 | -0.0077 | -0.0007 |
| R | sparse+ENC2-vs-sparse | 18 | -0.0011 | 0.9562 | 0.4444 | -0.0036 | 0.0045 |
| R | hdPS200+SHD-vs-hdPS200 | 18 | -0.0021 | 0.7930 | 0.5000 | -0.0060 | 0.0020 |
| R | hdPS200+ENC2-vs-hdPS200 | 18 | 0.0068 | 0.7423 | 0.5000 | -0.0037 | 0.0114 |
| R+ | C1 | 18 | -0.0084 | 0.3404 | 0.5556 | -0.0098 | -0.0008 |
| R+ | C2 | 18 | -0.0017 | 0.7844 | 0.5556 | -0.0046 | 0.0030 |
| R+ | sparse+SHD-vs-sparse | 18 | -0.0067 | 0.7670 | 0.5556 | -0.0083 | 0.0014 |
| R+ | sparse+ENC2-vs-sparse | 18 | -0.0065 | 0.5466 | 0.6667 | -0.0079 | 0.0003 |
| R+ | hdPS200+SHD-vs-hdPS200 | 18 | 0.0001 | 0.9912 | 0.5556 | -0.0029 | 0.0034 |
| R+ | hdPS200+ENC2-vs-hdPS200 | 18 | 0.0007 | 0.9064 | 0.5556 | -0.0033 | 0.0039 |

## I6 Multiverse (4 PS models × 5 hdPS split seeds × 10 estimators = 200 specifications; imputation 1)

Per specification: mean over trials of |log HR − target|; difference first arm − comparator (negative favours the first arm).

| contrast | target | metric | specs | share_favouring | median_diff | q10 | q90 | base_spec_diff |
|---|---|---|---|---|---|---|---|---|
| C1 | rct | mean_abs | 200 | 1.0000 | -0.0240 | -0.0331 | -0.0096 | -0.0201 |
| C1 | rct | mean_sq | 200 | 1.0000 | -0.0166 | -0.0254 | -0.0123 | -0.0166 |
| C1 | rplus | mean_abs | 200 | 0.9000 | -0.0134 | -0.0254 | -0.0014 | -0.0189 |
| C1 | rplus | mean_sq | 200 | 0.9250 | -0.0068 | -0.0110 | -0.0007 | -0.0085 |
| C2 | rct | mean_abs | 200 | 0.8350 | -0.0111 | -0.0244 | 0.0028 | -0.0020 |
| C2 | rct | mean_sq | 200 | 0.7350 | -0.0031 | -0.0122 | 0.0038 | 0.0043 |
| C2 | rplus | mean_abs | 200 | 0.5950 | -0.0018 | -0.0170 | 0.0080 | -0.0010 |
| C2 | rplus | mean_sq | 200 | 0.6050 | -0.0006 | -0.0069 | 0.0027 | -0.0019 |
| sparse+noise32-vs-sparse | rct | mean_abs | 200 | 0.4700 | 0.0006 | -0.0132 | 0.0162 | 0.0139 |
| sparse+noise32-vs-sparse | rct | mean_sq | 200 | 0.5450 | -0.0006 | -0.0120 | 0.0063 | 0.0007 |
| sparse+noise32-vs-sparse | rplus | mean_abs | 200 | 0.4800 | 0.0001 | -0.0092 | 0.0133 | 0.0026 |
| sparse+noise32-vs-sparse | rplus | mean_sq | 200 | 0.5450 | -0.0002 | -0.0054 | 0.0033 | -0.0013 |
| sparse+shufECG-vs-sparse | rct | mean_abs | 200 | 0.5750 | -0.0016 | -0.0128 | 0.0042 | 0.0030 |
| sparse+shufECG-vs-sparse | rct | mean_sq | 200 | 0.7750 | -0.0019 | -0.0140 | 0.0013 | -0.0076 |
| sparse+shufECG-vs-sparse | rplus | mean_abs | 200 | 0.4250 | 0.0011 | -0.0076 | 0.0080 | -0.0049 |
| sparse+shufECG-vs-sparse | rplus | mean_sq | 200 | 0.5250 | -0.0000 | -0.0055 | 0.0027 | -0.0042 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_abs | 200 | 0.9750 | -0.0224 | -0.0348 | -0.0069 | -0.0230 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_sq | 200 | 0.9500 | -0.0137 | -0.0241 | -0.0056 | -0.0090 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_abs | 200 | 0.8750 | -0.0155 | -0.0283 | 0.0047 | -0.0140 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_sq | 200 | 0.8000 | -0.0062 | -0.0140 | 0.0021 | -0.0043 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_abs | 200 | 0.5300 | -0.0008 | -0.0179 | 0.0153 | -0.0200 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_sq | 200 | 0.5150 | -0.0001 | -0.0084 | 0.0076 | -0.0090 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_abs | 200 | 0.3750 | 0.0024 | -0.0140 | 0.0147 | -0.0001 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_sq | 200 | 0.4450 | 0.0001 | -0.0048 | 0.0046 | -0.0041 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_abs | 200 | 0.5800 | -0.0020 | -0.0138 | 0.0126 | -0.0135 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_sq | 200 | 0.6250 | -0.0011 | -0.0065 | 0.0058 | -0.0063 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_abs | 200 | 0.4900 | 0.0003 | -0.0138 | 0.0161 | 0.0111 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_sq | 200 | 0.5850 | -0.0002 | -0.0053 | 0.0045 | -0.0011 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_abs | 200 | 0.8400 | -0.0093 | -0.0237 | 0.0027 | 0.0115 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_sq | 200 | 0.7100 | -0.0023 | -0.0113 | 0.0041 | 0.0107 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_abs | 200 | 0.5850 | -0.0023 | -0.0206 | 0.0107 | -0.0121 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_sq | 200 | 0.6000 | -0.0008 | -0.0066 | 0.0045 | -0.0008 |

## I7 Exact sign-flip permutation (frozen phase-2 estimates vs RCT) and leave-one-trial-out

| contrast | trials | mean_d_sqerr | p_signflip | loo_min | loo_max | trials_ecg_closer | p_sign_test_supplementary |
|---|---|---|---|---|---|---|---|
| C1 | 18 | -0.0166 | 0.4971 | -0.0243 | -0.0001 | 14 | 0.0309 |
| C2 | 18 | 0.0043 | 0.7589 | -0.0045 | 0.0085 | 10 | 0.8145 |

**Detectability.** Trials needed to detect the plasmode-expected reduction in |log HR − RCT| (paired t, two-sided α = 0.05, 80% power), using the between-trial SD of the frozen phase-2 paired differences:

| contrast | scenario | expected_gain | sd_paired_abs_diff | trials_needed |
|---|---|---|---|---|
| C1 | base | 0.004 | 0.071 | 2516.000 |
| C1 | phys_only | 0.004 | 0.071 | 2034.000 |
| C1 | strong | 0.006 | 0.071 | 948.000 |
| C2 | base | 0.000 | 0.083 | 377228440.000 |
| C2 | phys_only | -0.001 | 0.083 | inf |
| C2 | strong | -0.000 | 0.083 | inf |

## I9 E-values for the disagreement with the RCT (HR ratio; rare-outcome approximation)

| arm | median_evalue | max_evalue |
|---|---|---|
| M0 unadjusted | 1.69 | 7.90 |
| M1 sparse | 1.64 | 4.43 |
| M2 sparse+ECG | 1.56 | 3.59 |
| M3 hdPS200 | 1.50 | 2.51 |
| M4 hdPS200+ECG | 1.52 | 3.04 |
| R clinical | 1.53 | 2.64 |

## Part II: closer to the trial (agreement with the RCT per analysis)

Validation: max |log HR(design primary) − log HR(phase 2)| = 4.44e-16 over 108 arm-trials.

| analysis | arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|---|
| primary | R+ physiology ref | 18 | 0.150 | 8 | 14 | 1.297 | 0.112 | 0.667 |
| primary | R clinical | 18 | 0.144 | 12 | 14 | 1.274 | 0.121 | 0.722 |
| primary | M3 hdPS200 | 18 | 0.162 | 9 | 10 | 1.504 | 0.150 | 0.556 |
| primary | M4 hdPS200+ECG | 18 | 0.160 | 8 | 13 | 1.385 | 0.131 | 0.556 |
| primary | M1 sparse | 18 | 0.182 | 10 | 11 | 1.685 | 0.186 | 0.556 |
| primary | M2 sparse+ECG | 18 | 0.162 | 10 | 14 | 1.437 | 0.151 | 0.556 |
| primary | M0 unadjusted | 18 | 0.279 | 7 | 9 | 2.847 | 0.319 | 0.444 |
| strict | R+ physiology ref | 18 | 0.215 | 7 | 14 | 1.292 | 0.146 | 0.667 |
| strict | R clinical | 18 | 0.180 | 10 | 16 | 1.168 | 0.141 | 0.778 |
| strict | M3 hdPS200 | 18 | 0.215 | 6 | 16 | 1.447 | 0.163 | 0.889 |
| strict | M4 hdPS200+ECG | 18 | 0.213 | 10 | 15 | 1.198 | 0.144 | 0.778 |
| strict | M1 sparse | 18 | 0.247 | 7 | 10 | 1.730 | 0.240 | 0.556 |
| strict | M2 sparse+ECG | 18 | 0.289 | 7 | 13 | 1.647 | 0.208 | 0.667 |
| strict | M0 unadjusted | 18 | 0.341 | 5 | 9 | 2.673 | 0.370 | 0.444 |
| transport | R+ physiology ref | 18 | 0.199 | 7 | 16 | 1.077 | 0.126 | 0.778 |
| transport | R clinical | 18 | 0.187 | 8 | 16 | 1.052 | 0.129 | 0.833 |
| transport | M3 hdPS200 | 18 | 0.229 | 6 | 14 | 1.362 | 0.191 | 0.778 |
| transport | M4 hdPS200+ECG | 18 | 0.197 | 8 | 15 | 1.104 | 0.153 | 0.778 |
| transport | M1 sparse | 18 | 0.222 | 6 | 14 | 1.430 | 0.231 | 0.722 |
| transport | M2 sparse+ECG | 18 | 0.207 | 8 | 16 | 1.225 | 0.171 | 0.778 |
| transport | M0 unadjusted | 18 | 0.331 | 6 | 8 | 2.496 | 0.380 | 0.389 |
| transport_ess20 | R+ physiology ref | 18 | 0.170 | 8 | 16 | 1.079 | 0.113 | 0.778 |
| transport_ess20 | R clinical | 18 | 0.169 | 9 | 16 | 1.076 | 0.115 | 0.833 |
| transport_ess20 | M3 hdPS200 | 18 | 0.207 | 7 | 14 | 1.374 | 0.183 | 0.778 |
| transport_ess20 | M4 hdPS200+ECG | 18 | 0.183 | 9 | 15 | 1.123 | 0.146 | 0.778 |
| transport_ess20 | M1 sparse | 18 | 0.203 | 7 | 14 | 1.426 | 0.218 | 0.722 |
| transport_ess20 | M2 sparse+ECG | 18 | 0.187 | 8 | 16 | 1.260 | 0.157 | 0.778 |
| transport_ess20 | M0 unadjusted | 18 | 0.315 | 6 | 7 | 2.550 | 0.363 | 0.333 |
| pp_naive_365 | R+ physiology ref | 17 | 0.161 | 7 | 14 | 1.320 | 0.159 | 0.647 |
| pp_naive_365 | R clinical | 17 | 0.144 | 8 | 13 | 1.258 | 0.160 | 0.765 |
| pp_naive_365 | M3 hdPS200 | 17 | 0.181 | 9 | 11 | 1.507 | 0.196 | 0.647 |
| pp_naive_365 | M4 hdPS200+ECG | 17 | 0.177 | 7 | 11 | 1.420 | 0.179 | 0.647 |
| pp_naive_365 | M1 sparse | 17 | 0.211 | 5 | 10 | 1.883 | 0.228 | 0.471 |
| pp_naive_365 | M2 sparse+ECG | 17 | 0.197 | 5 | 10 | 1.704 | 0.204 | 0.529 |
| pp_naive_365 | M0 unadjusted | 17 | 0.301 | 4 | 6 | 3.006 | 0.353 | 0.235 |
| pp_ipcw_365 | R+ physiology ref | 17 | 0.159 | 7 | 15 | 1.260 | 0.152 | 0.765 |
| pp_ipcw_365 | R clinical | 17 | 0.144 | 8 | 13 | 1.206 | 0.151 | 0.765 |
| pp_ipcw_365 | M3 hdPS200 | 17 | 0.181 | 8 | 11 | 1.431 | 0.191 | 0.647 |
| pp_ipcw_365 | M4 hdPS200+ECG | 17 | 0.179 | 6 | 12 | 1.350 | 0.172 | 0.647 |
| pp_ipcw_365 | M1 sparse | 17 | 0.213 | 5 | 10 | 1.818 | 0.224 | 0.471 |
| pp_ipcw_365 | M2 sparse+ECG | 17 | 0.196 | 6 | 11 | 1.618 | 0.197 | 0.588 |
| pp_ipcw_365 | M0 unadjusted | 17 | 0.303 | 4 | 6 | 2.902 | 0.350 | 0.235 |
| pp_ipcw_180 | R+ physiology ref | 17 | 0.244 | 3 | 11 | 1.534 | 0.220 | 0.647 |
| pp_ipcw_180 | R clinical | 17 | 0.230 | 5 | 13 | 1.531 | 0.227 | 0.647 |
| pp_ipcw_180 | M3 hdPS200 | 17 | 0.253 | 6 | 13 | 1.687 | 0.268 | 0.647 |
| pp_ipcw_180 | M4 hdPS200+ECG | 17 | 0.236 | 6 | 12 | 1.530 | 0.243 | 0.706 |
| pp_ipcw_180 | M1 sparse | 17 | 0.284 | 4 | 9 | 2.064 | 0.289 | 0.529 |
| pp_ipcw_180 | M2 sparse+ECG | 17 | 0.289 | 3 | 10 | 1.985 | 0.270 | 0.529 |
| pp_ipcw_180 | M0 unadjusted | 17 | 0.370 | 4 | 5 | 3.072 | 0.412 | 0.294 |
| pp_ipcw_730 | R+ physiology ref | 17 | 0.141 | 10 | 14 | 1.222 | 0.129 | 0.647 |
| pp_ipcw_730 | R clinical | 17 | 0.129 | 9 | 14 | 1.163 | 0.129 | 0.765 |
| pp_ipcw_730 | M3 hdPS200 | 17 | 0.158 | 9 | 12 | 1.397 | 0.171 | 0.647 |
| pp_ipcw_730 | M4 hdPS200+ECG | 17 | 0.148 | 9 | 11 | 1.268 | 0.151 | 0.647 |
| pp_ipcw_730 | M1 sparse | 17 | 0.171 | 6 | 12 | 1.670 | 0.197 | 0.529 |
| pp_ipcw_730 | M2 sparse+ECG | 17 | 0.166 | 6 | 12 | 1.515 | 0.168 | 0.588 |
| pp_ipcw_730 | M0 unadjusted | 17 | 0.271 | 3 | 7 | 2.853 | 0.319 | 0.235 |
| pp_naive_switch | R+ physiology ref | 17 | 0.148 | 10 | 13 | 1.367 | 0.138 | 0.529 |
| pp_naive_switch | R clinical | 17 | 0.135 | 9 | 13 | 1.297 | 0.139 | 0.706 |
| pp_naive_switch | M3 hdPS200 | 17 | 0.163 | 9 | 11 | 1.557 | 0.178 | 0.588 |
| pp_naive_switch | M4 hdPS200+ECG | 17 | 0.150 | 9 | 11 | 1.396 | 0.152 | 0.588 |
| pp_naive_switch | M1 sparse | 17 | 0.168 | 7 | 11 | 1.758 | 0.192 | 0.588 |
| pp_naive_switch | M2 sparse+ECG | 17 | 0.159 | 6 | 11 | 1.573 | 0.165 | 0.647 |
| pp_naive_switch | M0 unadjusted | 17 | 0.256 | 4 | 6 | 2.934 | 0.313 | 0.235 |
| pp_ipcw_switch | R+ physiology ref | 17 | 0.147 | 10 | 13 | 1.310 | 0.133 | 0.588 |
| pp_ipcw_switch | R clinical | 17 | 0.135 | 9 | 13 | 1.250 | 0.134 | 0.706 |
| pp_ipcw_switch | M3 hdPS200 | 17 | 0.161 | 9 | 11 | 1.483 | 0.176 | 0.588 |
| pp_ipcw_switch | M4 hdPS200+ECG | 17 | 0.147 | 9 | 12 | 1.308 | 0.147 | 0.588 |
| pp_ipcw_switch | M1 sparse | 17 | 0.168 | 7 | 11 | 1.689 | 0.187 | 0.588 |
| pp_ipcw_switch | M2 sparse+ECG | 17 | 0.158 | 6 | 12 | 1.513 | 0.161 | 0.647 |
| pp_ipcw_switch | M0 unadjusted | 17 | 0.256 | 4 | 7 | 2.836 | 0.311 | 0.235 |
| runin90 | R+ physiology ref | 15 | 0.138 | 9 | 15 | 0.401 | 0.000 | 1.000 |
| runin90 | R clinical | 15 | 0.215 | 4 | 15 | 0.547 | 0.000 | 1.000 |
| runin90 | M3 hdPS200 | 15 | 0.248 | 7 | 12 | 0.950 | 0.170 | 0.800 |
| runin90 | M4 hdPS200+ECG | 15 | 0.276 | 3 | 13 | 0.991 | 0.203 | 0.867 |
| runin90 | M1 sparse | 15 | 0.305 | 3 | 13 | 0.989 | 0.139 | 0.867 |
| runin90 | M2 sparse+ECG | 15 | 0.254 | 7 | 14 | 0.872 | 0.086 | 0.867 |
| runin90 | M0 unadjusted | 17 | 0.240 | 6 | 11 | 1.772 | 0.260 | 0.588 |

## I8 Empirical calibration with expanded negative controls

Systematic error estimated from negative controls (per trial, pooled across trials if < 8 usable NCOs):

| arm | mean_mu | mean_abs_mu | mean_sigma | median_nco |
|---|---|---|---|---|
| R+ physiology ref | 0.048 | 0.077 | 0.029 | 22.000 |
| R clinical | 0.044 | 0.082 | 0.027 | 22.000 |
| M3 hdPS200 | 0.047 | 0.063 | 0.062 | 21.000 |
| M4 hdPS200+ECG | 0.045 | 0.072 | 0.074 | 20.500 |
| M1 sparse | 0.010 | 0.063 | 0.082 | 22.000 |
| M2 sparse+ECG | 0.034 | 0.077 | 0.069 | 21.500 |
| M0 unadjusted | 0.026 | 0.074 | 0.107 | 23.000 |

- C1 (M2 sparse+ECG − M1 sparse): mean Δσ = -0.013 (sign-flip p = 0.365); mean Δ|μ| = +0.014 (p = 0.353)
- C2 (M4 hdPS200+ECG − M3 hdPS200): mean Δσ = +0.012 (sign-flip p = 0.457); mean Δ|μ| = +0.008 (p = 0.642)

Agreement with the RCT after empirical calibration of the primary estimates:

| arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|
| R+ physiology ref | 18 | 0.170 | 8 | 13 | 1.445 | 0.142 | 0.611 |
| R clinical | 18 | 0.186 | 7 | 13 | 1.580 | 0.170 | 0.611 |
| M3 hdPS200 | 18 | 0.170 | 8 | 13 | 1.459 | 0.164 | 0.667 |
| M4 hdPS200+ECG | 18 | 0.182 | 6 | 14 | 1.429 | 0.151 | 0.667 |
| M1 sparse | 18 | 0.203 | 10 | 15 | 1.548 | 0.219 | 0.722 |
| M2 sparse+ECG | 18 | 0.196 | 8 | 14 | 1.606 | 0.202 | 0.722 |
| M0 unadjusted | 18 | 0.312 | 5 | 10 | 2.330 | 0.329 | 0.444 |

## Stratified by trial role (physiology vs control)

| role | trials | contrast | plasmode_rs_bias_reduction | pl_lo | pl_hi | RCT_d | RCT_p_signflip | R+_d | R+_p_signflip | multiverse_share_rct |
|---|---|---|---|---|---|---|---|---|---|---|
| physiology | 8 | C1 | 0.0093 | 0.0050 | 0.0124 | -0.0422 | 0.0859 | -0.0164 | 0.6562 | 0.9750 |
| physiology | 8 | C2 | -0.0020 | -0.0051 | 0.0017 | 0.0100 | 0.4297 | -0.0095 | 0.5078 | 0.8700 |
| control | 10 | C1 | -0.0004 | -0.0033 | 0.0032 | 0.0039 | 0.9980 | -0.0020 | 0.5234 | 0.7500 |
| control | 10 | C2 | 0.0016 | -0.0019 | 0.0043 | -0.0002 | 0.9902 | 0.0045 | 0.5391 | 0.6800 |

## Pre-specified decision rules

- C1 rule 1 (plasmode [ss] base: bias-reduction CI excludes 0, > 0): **met**
- C1 rule 1b (plasmode [ss] phys_only, supportive): **met**
- C1 rule 3 (plasmode [ss] base: less biased than shuffled-ECG placebo): **met**
- C2 rule 1 (plasmode [ss] base: bias-reduction CI excludes 0, > 0): **not met**
- C2 rule 1b (plasmode [ss] phys_only, supportive): **not met**
- C2 rule 3 (plasmode [ss] base: less biased than shuffled-ECG placebo): **not met**
- C1 rule 2 (vs RCT: mean Δ squared error < 0, exact sign-flip p < 0.05; audit fix): **not met**
- C1 rule 2 (vs R+: mean Δ squared error < 0, exact sign-flip p < 0.05; audit fix): **not met**
- C1 rule 3 (beats shuffled-ECG placebo vs R+: sign-flip p < 0.05): **not met**
- C1 rule 4b (leave-one-out: sign holds in every set vs R+): **met**
- C2 rule 2 (vs RCT: mean Δ squared error < 0, exact sign-flip p < 0.05; audit fix): **not met**
- C2 rule 2 (vs R+: mean Δ squared error < 0, exact sign-flip p < 0.05; audit fix): **not met**
- C2 rule 3 (beats shuffled-ECG placebo vs R+: sign-flip p < 0.05): **not met**
- C2 rule 4b (leave-one-out: sign holds in every set vs R+): **not met**
- C1 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **met**
- C2 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **met**
- C2 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **not met**
