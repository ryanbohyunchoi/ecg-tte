# v1.4 post-hoc F — the ECG on its own (18 trials; exploratory)

## Agreement (all trials; imputation 1 point estimates)

| arm | trials | mean_abs_vs_RCT | mean_abs_vs_Rplus | estimate_agreement | std_diff_agreement |
|---|---|---|---|---|---|
| Unadjusted | 18 | 0.279 | 0.200 | 6 | 9 |
| Demographics only | 18 | 0.265 | 0.177 | 8 | 10 |
| ECG only | 18 | 0.223 | 0.133 | 8 | 12 |
| Demographics + ECG | 18 | 0.208 | 0.151 | 8 | 11 |
| Sparse (demo + dx) | 18 | 0.182 | 0.081 | 10 | 11 |
| Sparse + ECG | 18 | 0.162 | 0.062 | 10 | 14 |
| Clinical PS | 18 | 0.137 | 0.057 | 10 | 13 |
| R+ physiology ref | 18 | 0.159 | 0.000 | 9 | 14 |

## Agreement (physiology trials; imputation 1 point estimates)

| arm | trials | mean_abs_vs_RCT | mean_abs_vs_Rplus | estimate_agreement | std_diff_agreement |
|---|---|---|---|---|---|
| Unadjusted | 8 | 0.340 | 0.233 | 3 | 5 |
| Demographics only | 8 | 0.320 | 0.219 | 3 | 5 |
| ECG only | 8 | 0.248 | 0.141 | 5 | 6 |
| Demographics + ECG | 8 | 0.225 | 0.170 | 4 | 6 |
| Sparse (demo + dx) | 8 | 0.212 | 0.109 | 5 | 5 |
| Sparse + ECG | 8 | 0.180 | 0.090 | 6 | 6 |
| Clinical PS | 8 | 0.145 | 0.058 | 5 | 6 |
| R+ physiology ref | 8 | 0.160 | 0.000 | 4 | 7 |

## Agreement (control trials; imputation 1 point estimates)

| arm | trials | mean_abs_vs_RCT | mean_abs_vs_Rplus | estimate_agreement | std_diff_agreement |
|---|---|---|---|---|---|
| Unadjusted | 10 | 0.231 | 0.174 | 3 | 4 |
| Demographics only | 10 | 0.221 | 0.144 | 5 | 5 |
| ECG only | 10 | 0.202 | 0.126 | 3 | 6 |
| Demographics + ECG | 10 | 0.194 | 0.136 | 4 | 5 |
| Sparse (demo + dx) | 10 | 0.157 | 0.059 | 5 | 6 |
| Sparse + ECG | 10 | 0.147 | 0.040 | 4 | 8 |
| Clinical PS | 10 | 0.132 | 0.056 | 5 | 7 |
| R+ physiology ref | 10 | 0.159 | 0.000 | 5 | 7 |

Plasmode source: claude-v14-ecgonly/pl-ss (pl-ss = 80% subsampling without replacement, valid for matching; pl = bootstrap resampling)

## Plasmode: mean |bias| by arm (true conditional HR 0.8; 1.0 in null)

| arm | base | none | null | phys_only | strong |
|---|---|---|---|---|---|
| Unadjusted | 0.192 | 0.164 | 0.191 | 0.155 | 0.222 |
| Demographics only | 0.166 | 0.143 | 0.165 | 0.120 | 0.198 |
| ECG only | 0.153 | 0.130 | 0.149 | 0.125 | 0.182 |
| Demographics + ECG | 0.136 | 0.112 | 0.135 | 0.097 | 0.165 |
| Sparse (demo + dx) | 0.059 | 0.041 | 0.060 | 0.044 | 0.084 |
| Sparse + ECG | 0.055 | 0.039 | 0.055 | 0.040 | 0.078 |
| Clinical PS | 0.022 | 0.021 | 0.019 | 0.020 | 0.026 |
| R+ physiology ref | 0.019 | 0.017 | 0.016 | 0.018 | 0.025 |

Share of the unadjusted bias removed (base scenario): Demographics only 13%; ECG only 20%; Demographics + ECG 29%; Sparse (demo + dx) 69%; Sparse + ECG 71%; Clinical PS 88%; R+ physiology ref 90%

Reduction in |bias| (positive = first arm less biased), 95% Monte Carlo CI:

| scenario | contrast | trials | bias_reduction | lo | hi |
|---|---|---|---|---|---|
| base | ECG only vs unadjusted | 18 | 0.0389 | 0.0368 | 0.0406 |
| base | ECG only vs demographics | 18 | 0.0137 | 0.0114 | 0.0160 |
| base | Demographics + ECG vs demographics | 18 | 0.0301 | 0.0279 | 0.0327 |
| base | ECG only vs sparse | 18 | -0.0935 | -0.0966 | -0.0897 |
| base | Demographics + ECG vs sparse | 18 | -0.0771 | -0.0798 | -0.0731 |
| base | Sparse + ECG vs sparse | 18 | 0.0039 | 0.0014 | 0.0061 |
| phys_only | ECG only vs unadjusted | 18 | 0.0299 | 0.0280 | 0.0316 |
| phys_only | ECG only vs demographics | 18 | -0.0053 | -0.0081 | -0.0026 |
| phys_only | Demographics + ECG vs demographics | 18 | 0.0225 | 0.0188 | 0.0249 |
| phys_only | ECG only vs sparse | 18 | -0.0808 | -0.0835 | -0.0780 |
| phys_only | Demographics + ECG vs sparse | 18 | -0.0529 | -0.0563 | -0.0504 |
| phys_only | Sparse + ECG vs sparse | 18 | 0.0044 | 0.0019 | 0.0072 |
| strong | ECG only vs unadjusted | 18 | 0.0400 | 0.0374 | 0.0424 |
| strong | ECG only vs demographics | 18 | 0.0164 | 0.0143 | 0.0189 |
| strong | Demographics + ECG vs demographics | 18 | 0.0328 | 0.0304 | 0.0350 |
| strong | ECG only vs sparse | 18 | -0.0971 | -0.1000 | -0.0937 |
| strong | Demographics + ECG vs sparse | 18 | -0.0807 | -0.0838 | -0.0774 |
| strong | Sparse + ECG vs sparse | 18 | 0.0064 | 0.0033 | 0.0089 |
| null | ECG only vs unadjusted | 18 | 0.0412 | 0.0393 | 0.0429 |
| null | ECG only vs demographics | 18 | 0.0157 | 0.0134 | 0.0180 |
| null | Demographics + ECG vs demographics | 18 | 0.0297 | 0.0274 | 0.0320 |
| null | ECG only vs sparse | 18 | -0.0892 | -0.0924 | -0.0863 |
| null | Demographics + ECG vs sparse | 18 | -0.0752 | -0.0778 | -0.0723 |
| null | Sparse + ECG vs sparse | 18 | 0.0054 | 0.0025 | 0.0073 |

## Real data: mean over trials of err(first)² − err(second)² (negative = first closer)

Inference: exact sign-flip test across trials (p_signflip); bootstrap interval descriptive only.

| target | contrast | trials | mean_d_sqerr | p_signflip | share_trials_closer | loo_min | loo_max | without_cabana | lo | hi |
|---|---|---|---|---|---|---|---|---|---|---|
| RCT | ECG only vs unadjusted | 18 | -0.0750 | 0.0073 | 0.7778 | -0.0811 | -0.0265 | -0.0265 | -0.0925 | -0.0462 |
| RCT | ECG only vs demographics | 18 | -0.0415 | 0.0167 | 0.5556 | -0.0458 | -0.0234 | -0.0234 | -0.0764 | -0.0226 |
| RCT | Demographics + ECG vs demographics | 18 | -0.0512 | 0.0207 | 0.7778 | -0.0576 | -0.0223 | -0.0223 | -0.0867 | -0.0331 |
| RCT | ECG only vs sparse | 18 | 0.0341 | 0.0629 | 0.2778 | 0.0163 | 0.0375 | 0.0163 | 0.0095 | 0.0653 |
| RCT | Demographics + ECG vs sparse | 18 | 0.0244 | 0.1536 | 0.4444 | 0.0114 | 0.0280 | 0.0175 | -0.0013 | 0.0522 |
| RCT | Sparse + ECG vs sparse | 18 | -0.0166 | 0.4965 | 0.7778 | -0.0243 | -0.0001 | -0.0001 | -0.0451 | 0.0086 |
| R+ | ECG only vs unadjusted | 18 | -0.0525 | 0.0020 | 0.7778 | -0.0564 | -0.0212 | -0.0212 | -0.0646 | -0.0330 |
| R+ | ECG only vs demographics | 18 | -0.0251 | 0.0245 | 0.7222 | -0.0274 | -0.0139 | -0.0139 | -0.0507 | -0.0082 |
| R+ | Demographics + ECG vs demographics | 18 | -0.0185 | 0.4785 | 0.6667 | -0.0273 | -0.0004 | -0.0004 | -0.0606 | -0.0203 |
| R+ | ECG only vs sparse | 18 | 0.0216 | 0.0030 | 0.2222 | 0.0118 | 0.0233 | 0.0118 | 0.0087 | 0.0480 |
| R+ | Demographics + ECG vs sparse | 18 | 0.0281 | 0.0024 | 0.2222 | 0.0203 | 0.0301 | 0.0253 | 0.0048 | 0.0388 |
| R+ | Sparse + ECG vs sparse | 18 | -0.0084 | 0.3404 | 0.5556 | -0.0098 | -0.0008 | -0.0008 | -0.0179 | 0.0059 |

