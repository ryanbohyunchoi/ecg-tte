# v1.4 post-hoc F — the ECG on its own (18 trials; exploratory)

## Agreement (all trials; imputation 1 point estimates)

| arm | trials | mean_abs_vs_RCT | mean_abs_vs_Rplus | estimate_agreement | std_diff_agreement |
|---|---|---|---|---|---|
| Unadjusted | 18 | 0.273 | 0.203 | 6 | 9 |
| Demographics only | 18 | 0.268 | 0.184 | 8 | 10 |
| ECG only | 18 | 0.211 | 0.133 | 8 | 12 |
| Demographics + ECG | 18 | 0.201 | 0.155 | 8 | 11 |
| Sparse (demo + dx) | 18 | 0.172 | 0.079 | 10 | 11 |
| Sparse + ECG | 18 | 0.161 | 0.070 | 10 | 14 |
| Clinical PS | 18 | 0.139 | 0.062 | 10 | 13 |
| R+ physiology ref | 18 | 0.155 | 0.000 | 9 | 15 |

## Agreement (physiology trials; imputation 1 point estimates)

| arm | trials | mean_abs_vs_RCT | mean_abs_vs_Rplus | estimate_agreement | std_diff_agreement |
|---|---|---|---|---|---|
| Unadjusted | 8 | 0.325 | 0.240 | 3 | 5 |
| Demographics only | 8 | 0.326 | 0.235 | 3 | 5 |
| ECG only | 8 | 0.221 | 0.142 | 5 | 6 |
| Demographics + ECG | 8 | 0.209 | 0.179 | 4 | 6 |
| Sparse (demo + dx) | 8 | 0.191 | 0.103 | 5 | 5 |
| Sparse + ECG | 8 | 0.179 | 0.108 | 6 | 6 |
| Clinical PS | 8 | 0.148 | 0.069 | 5 | 6 |
| R+ physiology ref | 8 | 0.152 | 0.000 | 4 | 8 |

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

## Plasmode: mean |bias| by arm (true conditional HR 0.8; 1.0 in null)

| arm | base | none | null | phys_only | strong |
|---|---|---|---|---|---|
| Unadjusted | 0.189 | 0.164 | 0.189 | 0.150 | 0.217 |
| Demographics only | 0.164 | 0.141 | 0.165 | 0.116 | 0.190 |
| ECG only | 0.151 | 0.129 | 0.150 | 0.124 | 0.174 |
| Demographics + ECG | 0.136 | 0.112 | 0.138 | 0.096 | 0.160 |
| Sparse (demo + dx) | 0.057 | 0.040 | 0.061 | 0.039 | 0.081 |
| Sparse + ECG | 0.053 | 0.037 | 0.054 | 0.039 | 0.074 |
| Clinical PS | 0.020 | 0.019 | 0.019 | 0.020 | 0.022 |
| R+ physiology ref | 0.020 | 0.014 | 0.018 | 0.019 | 0.019 |

Share of the unadjusted bias removed (base scenario): Demographics only 13%; ECG only 20%; Demographics + ECG 28%; Sparse (demo + dx) 70%; Sparse + ECG 72%; Clinical PS 90%; R+ physiology ref 90%

Reduction in |bias| (positive = first arm less biased), 95% Monte Carlo CI:

| scenario | contrast | trials | bias_reduction | lo | hi |
|---|---|---|---|---|---|
| base | ECG only vs unadjusted | 18 | 0.0382 | 0.0364 | 0.0399 |
| base | ECG only vs demographics | 18 | 0.0127 | 0.0106 | 0.0148 |
| base | Demographics + ECG vs demographics | 18 | 0.0276 | 0.0255 | 0.0299 |
| base | ECG only vs sparse | 18 | -0.0936 | -0.0963 | -0.0901 |
| base | Demographics + ECG vs sparse | 18 | -0.0788 | -0.0813 | -0.0752 |
| base | Sparse + ECG vs sparse | 18 | 0.0043 | 0.0016 | 0.0064 |
| phys_only | ECG only vs unadjusted | 18 | 0.0268 | 0.0254 | 0.0290 |
| phys_only | ECG only vs demographics | 18 | -0.0077 | -0.0099 | -0.0046 |
| phys_only | Demographics + ECG vs demographics | 18 | 0.0203 | 0.0180 | 0.0227 |
| phys_only | ECG only vs sparse | 18 | -0.0843 | -0.0865 | -0.0815 |
| phys_only | Demographics + ECG vs sparse | 18 | -0.0563 | -0.0587 | -0.0536 |
| phys_only | Sparse + ECG vs sparse | 18 | 0.0001 | -0.0023 | 0.0024 |
| strong | ECG only vs unadjusted | 18 | 0.0432 | 0.0409 | 0.0447 |
| strong | ECG only vs demographics | 18 | 0.0166 | 0.0143 | 0.0190 |
| strong | Demographics + ECG vs demographics | 18 | 0.0306 | 0.0286 | 0.0332 |
| strong | ECG only vs sparse | 18 | -0.0934 | -0.0959 | -0.0912 |
| strong | Demographics + ECG vs sparse | 18 | -0.0793 | -0.0822 | -0.0764 |
| strong | Sparse + ECG vs sparse | 18 | 0.0070 | 0.0044 | 0.0091 |
| null | ECG only vs unadjusted | 18 | 0.0384 | 0.0365 | 0.0401 |
| null | ECG only vs demographics | 18 | 0.0148 | 0.0126 | 0.0171 |
| null | Demographics + ECG vs demographics | 18 | 0.0275 | 0.0254 | 0.0298 |
| null | ECG only vs sparse | 18 | -0.0890 | -0.0918 | -0.0863 |
| null | Demographics + ECG vs sparse | 18 | -0.0764 | -0.0791 | -0.0737 |
| null | Sparse + ECG vs sparse | 18 | 0.0073 | 0.0049 | 0.0088 |

## Real-data paired bootstrap: mean over trials of err(first)² − err(second)² (negative = first closer)

| target | contrast | trials | mean_d_sqerr | lo | hi | share_trials_closer |
|---|---|---|---|---|---|---|
| RCT | ECG only vs unadjusted | 18 | -0.0791 | -0.0977 | -0.0483 | 0.7778 |
| RCT | ECG only vs demographics | 18 | -0.0677 | -0.0897 | -0.0253 | 0.6111 |
| RCT | Demographics + ECG vs demographics | 18 | -0.0698 | -0.1003 | -0.0344 | 0.7778 |
| RCT | ECG only vs sparse | 18 | 0.0303 | 0.0014 | 0.0554 | 0.3333 |
| RCT | Demographics + ECG vs sparse | 18 | 0.0282 | -0.0059 | 0.0559 | 0.4444 |
| RCT | Sparse + ECG vs sparse | 18 | -0.0009 | -0.0436 | 0.0052 | 0.7778 |
| R+ | ECG only vs unadjusted | 18 | -0.0579 | -0.0654 | -0.0315 | 0.7778 |
| R+ | ECG only vs demographics | 18 | -0.0443 | -0.0551 | -0.0115 | 0.6667 |
| R+ | Demographics + ECG vs demographics | 18 | -0.0332 | -0.0605 | -0.0196 | 0.6111 |
| R+ | ECG only vs sparse | 18 | 0.0204 | 0.0065 | 0.0438 | 0.1667 |
| R+ | Demographics + ECG vs sparse | 18 | 0.0315 | 0.0044 | 0.0363 | 0.2222 |
| R+ | Sparse + ECG vs sparse | 18 | -0.0010 | -0.0158 | 0.0076 | 0.5556 |

