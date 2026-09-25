# v1.3 exploratory robustness program — trial set: primary (10 trials)

Trials: comet, paradigm-hf-seq, transform-hf, elite-ii, life, plato, aristotle, rocket-af, rely, allhat

All analyses are exploratory (registered 2026-09-25 after phase 2; tag protocol-v1.3).

## I1 Plasmode simulation

**Scenario base** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 10 | -0.009 | 0.027 | 0.104 | 0.947 |
| R clinical | 10 | -0.013 | 0.036 | 0.104 | 0.951 |
| M3 hdPS200 | 10 | -0.021 | 0.040 | 0.109 | 0.934 |
| M4 hdPS200+ECG | 10 | -0.008 | 0.030 | 0.106 | 0.948 |
| M1 sparse | 10 | -0.030 | 0.052 | 0.113 | 0.890 |
| M2 sparse+ECG | 10 | -0.012 | 0.042 | 0.108 | 0.899 |
| M0 unadjusted | 10 | -0.091 | 0.194 | 0.218 | 0.347 |

**Scenario phys_only** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 10 | -0.013 | 0.018 | 0.102 | 0.949 |
| R clinical | 10 | -0.017 | 0.028 | 0.107 | 0.939 |
| M3 hdPS200 | 10 | -0.033 | 0.038 | 0.108 | 0.937 |
| M4 hdPS200+ECG | 10 | -0.022 | 0.027 | 0.107 | 0.949 |
| M1 sparse | 10 | -0.036 | 0.042 | 0.110 | 0.911 |
| M2 sparse+ECG | 10 | -0.027 | 0.030 | 0.106 | 0.924 |
| M0 unadjusted | 10 | -0.097 | 0.159 | 0.188 | 0.496 |

**Scenario strong** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 10 | -0.015 | 0.033 | 0.101 | 0.943 |
| R clinical | 10 | -0.018 | 0.040 | 0.101 | 0.941 |
| M3 hdPS200 | 10 | -0.029 | 0.053 | 0.108 | 0.931 |
| M4 hdPS200+ECG | 10 | -0.016 | 0.042 | 0.105 | 0.932 |
| M1 sparse | 10 | -0.047 | 0.067 | 0.119 | 0.851 |
| M2 sparse+ECG | 10 | -0.026 | 0.050 | 0.114 | 0.866 |
| M0 unadjusted | 10 | -0.113 | 0.212 | 0.232 | 0.327 |

**Scenario none** (true conditional HR 0.8; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 10 | -0.010 | 0.023 | 0.104 | 0.948 |
| R clinical | 10 | -0.010 | 0.028 | 0.102 | 0.953 |
| M3 hdPS200 | 10 | -0.013 | 0.035 | 0.106 | 0.929 |
| M4 hdPS200+ECG | 10 | 0.000 | 0.025 | 0.105 | 0.941 |
| M1 sparse | 10 | -0.006 | 0.040 | 0.105 | 0.918 |
| M2 sparse+ECG | 10 | 0.003 | 0.039 | 0.107 | 0.918 |
| M0 unadjusted | 10 | -0.071 | 0.176 | 0.202 | 0.396 |

**Scenario null** (true conditional HR 1.0; bias vs the arm's marginal truth; log-HR scale)

| arm | trials | mean_bias | mean_abs_bias | mean_rmse | mean_coverage |
|---|---|---|---|---|---|
| R+ physiology ref | 10 | -0.010 | 0.028 | 0.097 | 0.947 |
| R clinical | 10 | -0.015 | 0.038 | 0.096 | 0.948 |
| M3 hdPS200 | 10 | -0.020 | 0.044 | 0.102 | 0.933 |
| M4 hdPS200+ECG | 10 | -0.007 | 0.031 | 0.101 | 0.940 |
| M1 sparse | 10 | -0.027 | 0.053 | 0.106 | 0.885 |
| M2 sparse+ECG | 10 | -0.013 | 0.044 | 0.106 | 0.888 |
| M0 unadjusted | 10 | -0.091 | 0.193 | 0.214 | 0.324 |

Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:

| scenario | contrast | trials | bias_reduction | lo | hi | relative_reduction |
|---|---|---|---|---|---|---|
| base | C1 | 10 | 0.011 | 0.006 | 0.014 | 0.202 |
| base | C2 | 10 | 0.010 | 0.004 | 0.013 | 0.247 |
| base | sparse+noise32-vs-sparse | 10 | -0.008 | -0.012 | -0.003 | -0.146 |
| base | sparse+shufECG-vs-sparse | 10 | -0.007 | -0.010 | -0.004 | -0.140 |
| base | sparse+ECG-vs-sparse+shufECG | 10 | 0.018 | 0.014 | 0.021 | 0.300 |
| base | hdPS200+noise32-vs-hdPS200 | 10 | -0.000 | -0.006 | 0.006 | -0.011 |
| base | hdPS200+shufECG-vs-hdPS200 | 10 | 0.003 | -0.003 | 0.008 | 0.073 |
| base | hdPS200+ECG-vs-hdPS200+shufECG | 10 | 0.007 | 0.003 | 0.009 | 0.188 |
| none | C1 | 10 | 0.000 | -0.003 | 0.004 | 0.012 |
| none | C2 | 10 | 0.010 | 0.005 | 0.014 | 0.285 |
| none | sparse+noise32-vs-sparse | 10 | -0.002 | -0.008 | 0.002 | -0.063 |
| none | sparse+shufECG-vs-sparse | 10 | -0.005 | -0.010 | -0.001 | -0.130 |
| none | sparse+ECG-vs-sparse+shufECG | 10 | 0.006 | 0.001 | 0.011 | 0.125 |
| none | hdPS200+noise32-vs-hdPS200 | 10 | 0.002 | -0.004 | 0.007 | 0.053 |
| none | hdPS200+shufECG-vs-hdPS200 | 10 | -0.000 | -0.006 | 0.005 | -0.010 |
| none | hdPS200+ECG-vs-hdPS200+shufECG | 10 | 0.010 | 0.006 | 0.013 | 0.292 |
| null | C1 | 10 | 0.009 | 0.005 | 0.012 | 0.168 |
| null | C2 | 10 | 0.013 | 0.008 | 0.015 | 0.287 |
| null | sparse+noise32-vs-sparse | 10 | -0.006 | -0.011 | -0.002 | -0.107 |
| null | sparse+shufECG-vs-sparse | 10 | -0.008 | -0.012 | -0.005 | -0.156 |
| null | sparse+ECG-vs-sparse+shufECG | 10 | 0.017 | 0.013 | 0.021 | 0.280 |
| null | hdPS200+noise32-vs-hdPS200 | 10 | 0.003 | -0.002 | 0.008 | 0.068 |
| null | hdPS200+shufECG-vs-hdPS200 | 10 | 0.006 | 0.001 | 0.009 | 0.127 |
| null | hdPS200+ECG-vs-hdPS200+shufECG | 10 | 0.007 | 0.004 | 0.010 | 0.184 |
| phys_only | C1 | 10 | 0.013 | 0.008 | 0.016 | 0.296 |
| phys_only | C2 | 10 | 0.011 | 0.008 | 0.014 | 0.288 |
| phys_only | sparse+noise32-vs-sparse | 10 | 0.007 | 0.002 | 0.011 | 0.176 |
| phys_only | sparse+shufECG-vs-sparse | 10 | 0.003 | -0.002 | 0.006 | 0.081 |
| phys_only | sparse+ECG-vs-sparse+shufECG | 10 | 0.009 | 0.007 | 0.013 | 0.235 |
| phys_only | hdPS200+noise32-vs-hdPS200 | 10 | 0.007 | 0.002 | 0.013 | 0.187 |
| phys_only | hdPS200+shufECG-vs-hdPS200 | 10 | 0.004 | -0.001 | 0.009 | 0.103 |
| phys_only | hdPS200+ECG-vs-hdPS200+shufECG | 10 | 0.007 | 0.002 | 0.013 | 0.206 |
| strong | C1 | 10 | 0.016 | 0.013 | 0.019 | 0.244 |
| strong | C2 | 10 | 0.012 | 0.009 | 0.014 | 0.218 |
| strong | sparse+noise32-vs-sparse | 10 | -0.005 | -0.010 | -0.001 | -0.071 |
| strong | sparse+shufECG-vs-sparse | 10 | -0.007 | -0.011 | -0.004 | -0.108 |
| strong | sparse+ECG-vs-sparse+shufECG | 10 | 0.023 | 0.021 | 0.027 | 0.318 |
| strong | hdPS200+noise32-vs-hdPS200 | 10 | 0.005 | -0.000 | 0.011 | 0.098 |
| strong | hdPS200+shufECG-vs-hdPS200 | 10 | 0.004 | -0.001 | 0.008 | 0.078 |
| strong | hdPS200+ECG-vs-hdPS200+shufECG | 10 | 0.007 | 0.003 | 0.013 | 0.151 |

## I3 Within-trial paired bootstrap (200 replicates per trial)

Mean over trials of err(arm)² − err(comparator)² (negative = the first arm is closer to the target); 95% CI across bootstrap replicates; leave-one-trial-out range of the point estimate.

| target | contrast | trials | mean_d_sqerr | lo | hi | share_trials_closer | loo_min | loo_max |
|---|---|---|---|---|---|---|---|---|
| RCT | C1 | 10 | 0.0058 | -0.0372 | 0.0292 | 0.7000 | -0.0062 | 0.0093 |
| RCT | C2 | 10 | 0.0040 | -0.0441 | 0.0523 | 0.6000 | -0.0128 | 0.0118 |
| RCT | sparse+noise32-vs-sparse | 10 | 0.0062 | -0.0331 | 0.0282 | 0.4000 | 0.0038 | 0.0082 |
| RCT | sparse+shufECG-vs-sparse | 10 | 0.0039 | -0.0420 | 0.0350 | 0.4000 | 0.0008 | 0.0055 |
| RCT | sparse+ECG-vs-sparse+shufECG | 10 | 0.0020 | -0.0367 | 0.0324 | 0.6000 | -0.0070 | 0.0065 |
| RCT | hdPS200+noise32-vs-hdPS200 | 10 | -0.0220 | -0.0423 | 0.0243 | 0.8000 | -0.0254 | -0.0106 |
| RCT | hdPS200+shufECG-vs-hdPS200 | 10 | -0.0144 | -0.0363 | 0.0376 | 0.4000 | -0.0184 | -0.0026 |
| RCT | hdPS200+ECG-vs-hdPS200+shufECG | 10 | 0.0185 | -0.0306 | 0.0479 | 0.5000 | -0.0101 | 0.0270 |
| RCT | sparse+ECG8-vs-sparse | 10 | 0.0107 | -0.0397 | 0.0255 | 0.5000 | -0.0020 | 0.0155 |
| RCT | sparse+ECG16-vs-sparse | 10 | 0.0026 | -0.0376 | 0.0316 | 0.5000 | -0.0021 | 0.0062 |
| RCT | sparse+ECG-vs-sparse | 10 | 0.0058 | -0.0372 | 0.0292 | 0.7000 | -0.0062 | 0.0093 |
| RCT | sparse+ECG64-vs-sparse | 10 | -0.0004 | -0.0356 | 0.0236 | 0.5000 | -0.0037 | 0.0036 |
| RCT | sparse+ECGpheno-vs-sparse | 10 | -0.0041 | -0.0430 | 0.0235 | 0.7000 | -0.0062 | 0.0003 |
| RCT | hdPS200+ECG8-vs-hdPS200 | 10 | -0.0180 | -0.0439 | 0.0293 | 0.8000 | -0.0204 | -0.0115 |
| RCT | hdPS200+ECG16-vs-hdPS200 | 10 | -0.0187 | -0.0320 | 0.0405 | 0.7000 | -0.0224 | -0.0121 |
| RCT | hdPS200+ECG-vs-hdPS200 | 10 | 0.0040 | -0.0441 | 0.0523 | 0.6000 | -0.0128 | 0.0118 |
| RCT | hdPS200+ECG64-vs-hdPS200 | 10 | -0.0082 | -0.0381 | 0.0302 | 0.6000 | -0.0141 | -0.0037 |
| RCT | hdPS200+ECGpheno-vs-hdPS200 | 10 | -0.0052 | -0.0451 | 0.0345 | 0.7000 | -0.0134 | 0.0009 |
| R | C1 | 10 | 0.0102 | -0.0174 | 0.0172 | 0.4000 | 0.0011 | 0.0122 |
| R | C2 | 10 | 0.0150 | -0.0251 | 0.0295 | 0.3000 | 0.0014 | 0.0176 |
| R | sparse+noise32-vs-sparse | 10 | 0.0041 | -0.0150 | 0.0157 | 0.3000 | 0.0029 | 0.0053 |
| R | sparse+shufECG-vs-sparse | 10 | 0.0011 | -0.0121 | 0.0222 | 0.5000 | -0.0014 | 0.0022 |
| R | sparse+ECG-vs-sparse+shufECG | 10 | 0.0091 | -0.0220 | 0.0164 | 0.2000 | 0.0025 | 0.0105 |
| R | hdPS200+noise32-vs-hdPS200 | 10 | -0.0099 | -0.0279 | 0.0191 | 0.7000 | -0.0131 | 0.0006 |
| R | hdPS200+shufECG-vs-hdPS200 | 10 | -0.0038 | -0.0224 | 0.0261 | 0.3000 | -0.0093 | 0.0070 |
| R | hdPS200+ECG-vs-hdPS200+shufECG | 10 | 0.0189 | -0.0207 | 0.0297 | 0.5000 | -0.0056 | 0.0252 |
| R | sparse+ECG8-vs-sparse | 10 | 0.0107 | -0.0140 | 0.0174 | 0.3000 | 0.0006 | 0.0124 |
| R | sparse+ECG16-vs-sparse | 10 | 0.0080 | -0.0136 | 0.0183 | 0.3000 | 0.0051 | 0.0096 |
| R | sparse+ECG-vs-sparse | 10 | 0.0102 | -0.0174 | 0.0172 | 0.4000 | 0.0011 | 0.0122 |
| R | sparse+ECG64-vs-sparse | 10 | 0.0009 | -0.0161 | 0.0160 | 0.5000 | -0.0005 | 0.0019 |
| R | sparse+ECGpheno-vs-sparse | 10 | -0.0005 | -0.0199 | 0.0135 | 0.4000 | -0.0017 | 0.0022 |
| R | hdPS200+ECG8-vs-hdPS200 | 10 | -0.0043 | -0.0320 | 0.0224 | 0.5000 | -0.0071 | 0.0024 |
| R | hdPS200+ECG16-vs-hdPS200 | 10 | -0.0033 | -0.0219 | 0.0327 | 0.4000 | -0.0058 | 0.0023 |
| R | hdPS200+ECG-vs-hdPS200 | 10 | 0.0150 | -0.0251 | 0.0295 | 0.3000 | 0.0014 | 0.0176 |
| R | hdPS200+ECG64-vs-hdPS200 | 10 | 0.0042 | -0.0246 | 0.0268 | 0.3000 | -0.0014 | 0.0093 |
| R | hdPS200+ECGpheno-vs-hdPS200 | 10 | 0.0064 | -0.0272 | 0.0276 | 0.4000 | 0.0005 | 0.0092 |
| R+ | C1 | 10 | -0.0016 | -0.0182 | 0.0178 | 0.5000 | -0.0034 | 0.0005 |
| R+ | C2 | 10 | 0.0037 | -0.0297 | 0.0230 | 0.6000 | -0.0011 | 0.0070 |
| R+ | sparse+noise32-vs-sparse | 10 | -0.0001 | -0.0132 | 0.0189 | 0.6000 | -0.0018 | 0.0011 |
| R+ | sparse+shufECG-vs-sparse | 10 | 0.0002 | -0.0157 | 0.0221 | 0.4000 | -0.0008 | 0.0019 |
| R+ | sparse+ECG-vs-sparse+shufECG | 10 | -0.0019 | -0.0206 | 0.0177 | 0.6000 | -0.0035 | -0.0002 |
| R+ | hdPS200+noise32-vs-hdPS200 | 10 | -0.0010 | -0.0257 | 0.0189 | 0.5000 | -0.0030 | 0.0017 |
| R+ | hdPS200+shufECG-vs-hdPS200 | 10 | 0.0067 | -0.0277 | 0.0241 | 0.4000 | 0.0036 | 0.0079 |
| R+ | hdPS200+ECG-vs-hdPS200+shufECG | 10 | -0.0030 | -0.0249 | 0.0228 | 0.8000 | -0.0087 | 0.0001 |
| R+ | sparse+ECG8-vs-sparse | 10 | -0.0005 | -0.0150 | 0.0171 | 0.5000 | -0.0022 | 0.0016 |
| R+ | sparse+ECG16-vs-sparse | 10 | -0.0024 | -0.0171 | 0.0205 | 0.6000 | -0.0039 | -0.0006 |
| R+ | sparse+ECG-vs-sparse | 10 | -0.0016 | -0.0182 | 0.0178 | 0.5000 | -0.0034 | 0.0005 |
| R+ | sparse+ECG64-vs-sparse | 10 | -0.0034 | -0.0174 | 0.0129 | 0.7000 | -0.0043 | -0.0024 |
| R+ | sparse+ECGpheno-vs-sparse | 10 | 0.0066 | -0.0197 | 0.0169 | 0.5000 | -0.0013 | 0.0084 |
| R+ | hdPS200+ECG8-vs-hdPS200 | 10 | -0.0003 | -0.0251 | 0.0206 | 0.7000 | -0.0020 | 0.0024 |
| R+ | hdPS200+ECG16-vs-hdPS200 | 10 | -0.0032 | -0.0275 | 0.0279 | 0.6000 | -0.0051 | -0.0008 |
| R+ | hdPS200+ECG-vs-hdPS200 | 10 | 0.0037 | -0.0297 | 0.0230 | 0.6000 | -0.0011 | 0.0070 |
| R+ | hdPS200+ECG64-vs-hdPS200 | 10 | 0.0089 | -0.0252 | 0.0233 | 0.5000 | -0.0003 | 0.0121 |
| R+ | hdPS200+ECGpheno-vs-hdPS200 | 10 | -0.0074 | -0.0275 | 0.0236 | 0.6000 | -0.0101 | 0.0006 |

## I6 Multiverse (4 PS models × 5 hdPS split seeds × 10 estimators = 200 specifications; imputation 1)

Per specification: mean over trials of |log HR − target|; difference first arm − comparator (negative favours the first arm).

| contrast | target | metric | specs | share_favouring | median_diff | q10 | q90 | base_spec_diff |
|---|---|---|---|---|---|---|---|---|
| C1 | rct | mean_abs | 200 | 0.9250 | -0.0145 | -0.0349 | -0.0030 | 0.0009 |
| C1 | rct | mean_sq | 200 | 0.7250 | -0.0059 | -0.0142 | 0.0063 | 0.0058 |
| C1 | rplus | mean_abs | 200 | 0.6500 | -0.0079 | -0.0206 | 0.0274 | -0.0121 |
| C1 | rplus | mean_sq | 200 | 0.7500 | -0.0019 | -0.0050 | 0.0105 | -0.0018 |
| C2 | rct | mean_abs | 200 | 0.8150 | -0.0121 | -0.0343 | 0.0068 | -0.0169 |
| C2 | rct | mean_sq | 200 | 0.6100 | -0.0018 | -0.0157 | 0.0076 | 0.0040 |
| C2 | rplus | mean_abs | 200 | 0.6350 | -0.0042 | -0.0308 | 0.0140 | 0.0083 |
| C2 | rplus | mean_sq | 200 | 0.6050 | -0.0010 | -0.0099 | 0.0041 | 0.0034 |
| sparse+noise32-vs-sparse | rct | mean_abs | 200 | 0.4900 | 0.0002 | -0.0172 | 0.0266 | 0.0172 |
| sparse+noise32-vs-sparse | rct | mean_sq | 200 | 0.5600 | -0.0007 | -0.0105 | 0.0115 | 0.0062 |
| sparse+noise32-vs-sparse | rplus | mean_abs | 200 | 0.4800 | 0.0011 | -0.0110 | 0.0174 | -0.0075 |
| sparse+noise32-vs-sparse | rplus | mean_sq | 200 | 0.5400 | -0.0001 | -0.0027 | 0.0031 | -0.0002 |
| sparse+shufECG-vs-sparse | rct | mean_abs | 200 | 0.6000 | -0.0014 | -0.0223 | 0.0093 | 0.0090 |
| sparse+shufECG-vs-sparse | rct | mean_sq | 200 | 0.7750 | -0.0028 | -0.0125 | 0.0030 | 0.0039 |
| sparse+shufECG-vs-sparse | rplus | mean_abs | 200 | 0.5000 | -0.0000 | -0.0104 | 0.0106 | -0.0040 |
| sparse+shufECG-vs-sparse | rplus | mean_sq | 200 | 0.6250 | -0.0003 | -0.0026 | 0.0046 | 0.0003 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_abs | 200 | 0.8000 | -0.0140 | -0.0326 | 0.0150 | -0.0081 |
| sparse+ECG-vs-sparse+shufECG | rct | mean_sq | 200 | 0.6500 | -0.0043 | -0.0083 | 0.0208 | 0.0020 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_abs | 200 | 0.6500 | -0.0085 | -0.0273 | 0.0294 | -0.0080 |
| sparse+ECG-vs-sparse+shufECG | rplus | mean_sq | 200 | 0.7500 | -0.0017 | -0.0073 | 0.0128 | -0.0021 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_abs | 200 | 0.5650 | -0.0010 | -0.0325 | 0.0194 | -0.0538 |
| hdPS200+noise32-vs-hdPS200 | rct | mean_sq | 200 | 0.5800 | -0.0012 | -0.0167 | 0.0109 | -0.0220 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_abs | 200 | 0.4650 | 0.0009 | -0.0206 | 0.0153 | 0.0064 |
| hdPS200+noise32-vs-hdPS200 | rplus | mean_sq | 200 | 0.5250 | -0.0001 | -0.0077 | 0.0051 | -0.0012 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_abs | 200 | 0.6450 | -0.0038 | -0.0271 | 0.0180 | -0.0266 |
| hdPS200+shufECG-vs-hdPS200 | rct | mean_sq | 200 | 0.7000 | -0.0017 | -0.0146 | 0.0073 | -0.0144 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_abs | 200 | 0.5700 | -0.0015 | -0.0234 | 0.0194 | 0.0345 |
| hdPS200+shufECG-vs-hdPS200 | rplus | mean_sq | 200 | 0.6050 | -0.0004 | -0.0107 | 0.0064 | 0.0065 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_abs | 200 | 0.7350 | -0.0069 | -0.0229 | 0.0079 | 0.0096 |
| hdPS200+ECG-vs-hdPS200+shufECG | rct | mean_sq | 200 | 0.4950 | 0.0003 | -0.0129 | 0.0108 | 0.0185 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_abs | 200 | 0.5800 | -0.0026 | -0.0274 | 0.0165 | -0.0262 |
| hdPS200+ECG-vs-hdPS200+shufECG | rplus | mean_sq | 200 | 0.5900 | -0.0008 | -0.0102 | 0.0078 | -0.0031 |

## I7 Exact sign-flip permutation (frozen phase-2 estimates vs RCT) and leave-one-trial-out

| contrast | trials | mean_d_sqerr | p_signflip | loo_min | loo_max | trials_ecg_closer |
|---|---|---|---|---|---|---|
| C1 | 10 | 0.0058 | 0.9414 | -0.0062 | 0.0093 | 7 |
| C2 | 10 | 0.0040 | 0.9531 | -0.0128 | 0.0118 | 6 |

**Detectability.** Trials needed to detect the plasmode-expected reduction in |log HR − RCT| (paired t, two-sided α = 0.05, 80% power), using the between-trial SD of the frozen phase-2 paired differences:

| contrast | scenario | expected_gain | sd_paired_abs_diff | trials_needed |
|---|---|---|---|---|
| C1 | base | 0.011 | 0.076 | 408.000 |
| C1 | phys_only | 0.013 | 0.076 | 289.000 |
| C1 | strong | 0.016 | 0.076 | 171.000 |
| C2 | base | 0.010 | 0.083 | 545.000 |
| C2 | phys_only | 0.011 | 0.083 | 457.000 |
| C2 | strong | 0.012 | 0.083 | 405.000 |

## I9 E-values for the disagreement with the RCT (HR ratio; rare-outcome approximation)

| arm | median_evalue | max_evalue |
|---|---|---|
| M0 unadjusted | 1.69 | 3.05 |
| M1 sparse | 1.52 | 1.87 |
| M2 sparse+ECG | 1.47 | 2.35 |
| M3 hdPS200 | 1.49 | 2.51 |
| M4 hdPS200+ECG | 1.46 | 3.04 |
| R clinical | 1.49 | 1.79 |

## Part II: closer to the trial (agreement with the RCT per analysis)

Validation: max |log HR(design primary) − log HR(phase 2)| = 4.44e-16 over 60 arm-trials.

| analysis | arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|---|
| primary | R+ physiology ref | 10 | 0.132 | 5 | 9 | 1.022 | 0.081 | 0.800 |
| primary | R clinical | 10 | 0.122 | 7 | 9 | 0.995 | 0.075 | 0.900 |
| primary | M3 hdPS200 | 10 | 0.164 | 6 | 6 | 1.329 | 0.131 | 0.600 |
| primary | M4 hdPS200+ECG | 10 | 0.147 | 6 | 8 | 1.068 | 0.078 | 0.800 |
| primary | M1 sparse | 10 | 0.127 | 7 | 8 | 1.148 | 0.123 | 0.700 |
| primary | M2 sparse+ECG | 10 | 0.128 | 6 | 9 | 1.037 | 0.094 | 0.700 |
| primary | M0 unadjusted | 10 | 0.241 | 3 | 5 | 2.563 | 0.301 | 0.400 |
| strict | R+ physiology ref | 10 | 0.214 | 3 | 9 | 1.096 | 0.135 | 0.800 |
| strict | R clinical | 10 | 0.156 | 6 | 10 | 0.821 | 0.000 | 1.000 |
| strict | M3 hdPS200 | 10 | 0.224 | 3 | 10 | 1.240 | 0.135 | 1.000 |
| strict | M4 hdPS200+ECG | 10 | 0.259 | 5 | 9 | 1.058 | 0.128 | 0.900 |
| strict | M1 sparse | 10 | 0.200 | 5 | 6 | 1.270 | 0.159 | 0.600 |
| strict | M2 sparse+ECG | 10 | 0.293 | 4 | 8 | 1.254 | 0.155 | 0.800 |
| strict | M0 unadjusted | 10 | 0.279 | 3 | 5 | 2.115 | 0.279 | 0.400 |
| transport | R+ physiology ref | 10 | 0.206 | 3 | 9 | 1.062 | 0.135 | 0.900 |
| transport | R clinical | 10 | 0.189 | 4 | 10 | 0.947 | 0.073 | 1.000 |
| transport | M3 hdPS200 | 10 | 0.275 | 2 | 8 | 1.500 | 0.205 | 0.800 |
| transport | M4 hdPS200+ECG | 10 | 0.225 | 3 | 9 | 1.105 | 0.156 | 0.900 |
| transport | M1 sparse | 10 | 0.187 | 4 | 9 | 1.170 | 0.148 | 0.800 |
| transport | M2 sparse+ECG | 10 | 0.200 | 4 | 10 | 1.089 | 0.113 | 0.900 |
| transport | M0 unadjusted | 10 | 0.294 | 3 | 5 | 2.211 | 0.317 | 0.400 |
| transport_ess20 | R+ physiology ref | 10 | 0.154 | 4 | 9 | 1.013 | 0.117 | 0.900 |
| transport_ess20 | R clinical | 10 | 0.152 | 5 | 10 | 0.935 | 0.069 | 1.000 |
| transport_ess20 | M3 hdPS200 | 10 | 0.237 | 3 | 8 | 1.441 | 0.191 | 0.800 |
| transport_ess20 | M4 hdPS200+ECG | 10 | 0.199 | 4 | 9 | 1.078 | 0.146 | 0.900 |
| transport_ess20 | M1 sparse | 10 | 0.155 | 5 | 9 | 1.103 | 0.135 | 0.800 |
| transport_ess20 | M2 sparse+ECG | 10 | 0.159 | 4 | 10 | 1.066 | 0.098 | 0.900 |
| transport_ess20 | M0 unadjusted | 10 | 0.265 | 3 | 4 | 2.256 | 0.312 | 0.300 |
| pp_naive_365 | R+ physiology ref | 10 | 0.163 | 4 | 10 | 1.137 | 0.129 | 0.700 |
| pp_naive_365 | R clinical | 10 | 0.137 | 5 | 9 | 0.980 | 0.086 | 0.900 |
| pp_naive_365 | M3 hdPS200 | 10 | 0.165 | 6 | 8 | 1.151 | 0.128 | 0.800 |
| pp_naive_365 | M4 hdPS200+ECG | 10 | 0.159 | 5 | 8 | 1.018 | 0.087 | 0.800 |
| pp_naive_365 | M1 sparse | 10 | 0.213 | 2 | 7 | 1.634 | 0.197 | 0.500 |
| pp_naive_365 | M2 sparse+ECG | 10 | 0.218 | 2 | 6 | 1.600 | 0.189 | 0.600 |
| pp_naive_365 | M0 unadjusted | 10 | 0.341 | 1 | 3 | 3.115 | 0.393 | 0.100 |
| pp_ipcw_365 | R+ physiology ref | 10 | 0.161 | 4 | 10 | 1.082 | 0.119 | 0.900 |
| pp_ipcw_365 | R clinical | 10 | 0.135 | 5 | 9 | 0.929 | 0.071 | 0.900 |
| pp_ipcw_365 | M3 hdPS200 | 10 | 0.170 | 5 | 8 | 1.103 | 0.121 | 0.800 |
| pp_ipcw_365 | M4 hdPS200+ECG | 10 | 0.162 | 4 | 9 | 0.967 | 0.078 | 0.800 |
| pp_ipcw_365 | M1 sparse | 10 | 0.215 | 2 | 7 | 1.572 | 0.195 | 0.500 |
| pp_ipcw_365 | M2 sparse+ECG | 10 | 0.217 | 3 | 7 | 1.511 | 0.183 | 0.600 |
| pp_ipcw_365 | M0 unadjusted | 10 | 0.345 | 1 | 3 | 3.005 | 0.391 | 0.100 |
| pp_ipcw_180 | R+ physiology ref | 10 | 0.203 | 2 | 8 | 1.110 | 0.140 | 0.800 |
| pp_ipcw_180 | R clinical | 10 | 0.180 | 4 | 10 | 1.027 | 0.117 | 0.800 |
| pp_ipcw_180 | M3 hdPS200 | 10 | 0.208 | 4 | 10 | 1.174 | 0.139 | 0.800 |
| pp_ipcw_180 | M4 hdPS200+ECG | 10 | 0.169 | 5 | 10 | 0.929 | 0.038 | 1.000 |
| pp_ipcw_180 | M1 sparse | 10 | 0.250 | 2 | 6 | 1.634 | 0.242 | 0.600 |
| pp_ipcw_180 | M2 sparse+ECG | 10 | 0.267 | 2 | 7 | 1.620 | 0.237 | 0.600 |
| pp_ipcw_180 | M0 unadjusted | 10 | 0.393 | 2 | 2 | 2.982 | 0.435 | 0.200 |
| pp_ipcw_730 | R+ physiology ref | 10 | 0.142 | 6 | 9 | 1.029 | 0.106 | 0.800 |
| pp_ipcw_730 | R clinical | 10 | 0.129 | 6 | 9 | 0.941 | 0.079 | 0.900 |
| pp_ipcw_730 | M3 hdPS200 | 10 | 0.148 | 6 | 9 | 1.067 | 0.118 | 0.800 |
| pp_ipcw_730 | M4 hdPS200+ECG | 10 | 0.129 | 7 | 8 | 0.865 | 0.055 | 0.800 |
| pp_ipcw_730 | M1 sparse | 10 | 0.172 | 3 | 9 | 1.420 | 0.168 | 0.600 |
| pp_ipcw_730 | M2 sparse+ECG | 10 | 0.177 | 3 | 9 | 1.341 | 0.140 | 0.700 |
| pp_ipcw_730 | M0 unadjusted | 10 | 0.302 | 1 | 4 | 2.907 | 0.359 | 0.100 |
| pp_naive_switch | R+ physiology ref | 10 | 0.149 | 6 | 8 | 1.159 | 0.126 | 0.600 |
| pp_naive_switch | R clinical | 10 | 0.135 | 6 | 8 | 1.076 | 0.110 | 0.800 |
| pp_naive_switch | M3 hdPS200 | 10 | 0.155 | 6 | 8 | 1.234 | 0.143 | 0.700 |
| pp_naive_switch | M4 hdPS200+ECG | 10 | 0.134 | 7 | 8 | 0.988 | 0.074 | 0.700 |
| pp_naive_switch | M1 sparse | 10 | 0.170 | 4 | 8 | 1.530 | 0.175 | 0.700 |
| pp_naive_switch | M2 sparse+ECG | 10 | 0.177 | 3 | 8 | 1.463 | 0.151 | 0.800 |
| pp_naive_switch | M0 unadjusted | 10 | 0.297 | 1 | 3 | 3.085 | 0.359 | 0.100 |
| pp_ipcw_switch | R+ physiology ref | 10 | 0.148 | 6 | 8 | 1.110 | 0.120 | 0.700 |
| pp_ipcw_switch | R clinical | 10 | 0.135 | 6 | 8 | 1.031 | 0.102 | 0.800 |
| pp_ipcw_switch | M3 hdPS200 | 10 | 0.153 | 6 | 8 | 1.178 | 0.142 | 0.700 |
| pp_ipcw_switch | M4 hdPS200+ECG | 10 | 0.129 | 7 | 9 | 0.904 | 0.059 | 0.700 |
| pp_ipcw_switch | M1 sparse | 10 | 0.170 | 4 | 8 | 1.451 | 0.169 | 0.700 |
| pp_ipcw_switch | M2 sparse+ECG | 10 | 0.176 | 3 | 8 | 1.395 | 0.147 | 0.800 |
| pp_ipcw_switch | M0 unadjusted | 10 | 0.298 | 1 | 4 | 2.966 | 0.356 | 0.100 |
| runin90 | R+ physiology ref | 10 | 0.136 | 6 | 10 | 0.337 | 0.000 | 1.000 |
| runin90 | R clinical | 10 | 0.224 | 3 | 10 | 0.504 | 0.000 | 1.000 |
| runin90 | M3 hdPS200 | 10 | 0.281 | 4 | 9 | 0.859 | 0.124 | 0.900 |
| runin90 | M4 hdPS200+ECG | 10 | 0.300 | 2 | 10 | 0.825 | 0.104 | 1.000 |
| runin90 | M1 sparse | 10 | 0.362 | 2 | 9 | 0.996 | 0.212 | 0.900 |
| runin90 | M2 sparse+ECG | 10 | 0.283 | 5 | 9 | 0.795 | 0.126 | 0.900 |
| runin90 | M0 unadjusted | 10 | 0.267 | 4 | 6 | 1.717 | 0.297 | 0.600 |

## I8 Empirical calibration with expanded negative controls

Systematic error estimated from negative controls (per trial, pooled across trials if < 8 usable NCOs):

| arm | mean_mu | mean_abs_mu | mean_sigma | median_nco |
|---|---|---|---|---|
| R+ physiology ref | 0.069 | 0.086 | 0.042 | 20.000 |
| R clinical | 0.059 | 0.087 | 0.038 | 20.500 |
| M3 hdPS200 | 0.051 | 0.074 | 0.104 | 20.000 |
| M4 hdPS200+ECG | 0.066 | 0.099 | 0.106 | 18.000 |
| M1 sparse | 0.023 | 0.054 | 0.088 | 21.000 |
| M2 sparse+ECG | 0.051 | 0.095 | 0.091 | 20.000 |
| M0 unadjusted | 0.022 | 0.086 | 0.132 | 22.000 |

- C1 (M2 sparse+ECG − M1 sparse): mean Δσ = +0.002 (sign-flip p = 0.781); mean Δ|μ| = +0.041 (p = 0.072)
- C2 (M4 hdPS200+ECG − M3 hdPS200): mean Δσ = +0.002 (sign-flip p = 0.932); mean Δ|μ| = +0.025 (p = 0.398)

Agreement with the RCT after empirical calibration of the primary estimates:

| arm | trials | mean_abs_dlog | estimate_agreement | std_diff_agreement | mean_abs_z | tau | coverage |
|---|---|---|---|---|---|---|---|
| R+ physiology ref | 10 | 0.162 | 5 | 8 | 1.216 | 0.166 | 0.700 |
| R clinical | 10 | 0.182 | 5 | 8 | 1.372 | 0.196 | 0.800 |
| M3 hdPS200 | 10 | 0.165 | 5 | 9 | 1.149 | 0.123 | 0.800 |
| M4 hdPS200+ECG | 10 | 0.185 | 4 | 9 | 1.143 | 0.109 | 0.900 |
| M1 sparse | 10 | 0.161 | 7 | 9 | 1.260 | 0.192 | 0.900 |
| M2 sparse+ECG | 10 | 0.187 | 4 | 9 | 1.437 | 0.207 | 0.800 |
| M0 unadjusted | 10 | 0.281 | 2 | 6 | 2.166 | 0.351 | 0.500 |

## Pre-specified decision rules

- C1 rule 1 (plasmode base: bias-reduction CI excludes 0, > 0): **met**
- C1 rule 1b (plasmode phys_only, supportive): **met**
- C1 rule 3 (plasmode base: less biased than shuffled-ECG placebo): **met**
- C2 rule 1 (plasmode base: bias-reduction CI excludes 0, > 0): **met**
- C2 rule 1b (plasmode phys_only, supportive): **met**
- C2 rule 3 (plasmode base: less biased than shuffled-ECG placebo): **met**
- C1 rule 2 (bootstrap vs RCT: CI < 0): **not met**
- C1 rule 2 (bootstrap vs R+: CI < 0): **not met**
- C1 rule 3 (beats shuffled-ECG placebo vs R+: CI < 0): **not met**
- C1 rule 4b (leave-one-out: sign holds in every set vs R+): **not met**
- C2 rule 2 (bootstrap vs RCT: CI < 0): **not met**
- C2 rule 2 (bootstrap vs R+: CI < 0): **not met**
- C2 rule 3 (beats shuffled-ECG placebo vs R+: CI < 0): **not met**
- C2 rule 4b (leave-one-out: sign holds in every set vs R+): **not met**
- C1 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **met**
- C1 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **not met**
- C1 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **not met**
- C1 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rct, mean_abs: >= 80% of specifications favour ECG): **met**
- C2 rule 4a (multiverse vs rct, mean_sq: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_abs: >= 80% of specifications favour ECG): **not met**
- C2 rule 4a (multiverse vs rplus, mean_sq: >= 80% of specifications favour ECG): **not met**
