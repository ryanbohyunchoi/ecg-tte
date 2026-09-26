# v1.4 — where does the ECG add information? (exploratory; tag protocol-v1.4)

## Plasmode: bias reduction from adding the ECG (log-HR scale; positive = ECG arm less biased)

| pool | scenario | contrast | trials | bias_reduction | lo | hi | relative |
|---|---|---|---|---|---|---|---|
| density_high | base | C1 | 17 | 0.0027 | -0.0017 | 0.0067 | 0.0453 |
| density_high | base | C2 | 15 | -0.0012 | -0.0071 | 0.0045 | -0.0277 |
| density_high | phys_only | C1 | 17 | 0.0046 | 0.0011 | 0.0092 | 0.1037 |
| density_high | phys_only | C2 | 15 | -0.0064 | -0.0122 | 0.0030 | -0.2999 |
| density_low | base | C1 | 18 | -0.0002 | -0.0051 | 0.0055 | -0.0054 |
| density_low | base | C2 | 18 | 0.0033 | -0.0025 | 0.0086 | 0.0736 |
| density_low | phys_only | C1 | 18 | -0.0026 | -0.0080 | 0.0031 | -0.0783 |
| density_low | phys_only | C2 | 18 | -0.0028 | -0.0096 | 0.0017 | -0.0691 |
| density_mid | base | C1 | 18 | 0.0038 | 0.0002 | 0.0087 | 0.0740 |
| density_mid | base | C2 | 18 | -0.0019 | -0.0099 | 0.0049 | -0.0461 |
| density_mid | phys_only | C1 | 18 | -0.0004 | -0.0036 | 0.0039 | -0.0094 |
| density_mid | phys_only | C2 | 18 | -0.0032 | -0.0103 | 0.0027 | -0.0972 |
| dropout_0 | base | C1 | 18 | 0.0047 | 0.0021 | 0.0071 | 0.0797 |
| dropout_0 | base | C2 | 18 | -0.0011 | -0.0034 | 0.0011 | -0.0319 |
| dropout_0 | none | C1 | 18 | 0.0033 | 0.0005 | 0.0049 | 0.0795 |
| dropout_0 | none | C2 | 18 | -0.0009 | -0.0035 | 0.0013 | -0.0391 |
| dropout_0 | null | C1 | 18 | 0.0085 | 0.0061 | 0.0103 | 0.1342 |
| dropout_0 | null | C2 | 18 | 0.0006 | -0.0015 | 0.0027 | 0.0158 |
| dropout_0 | phys_only | C1 | 18 | -0.0001 | -0.0024 | 0.0025 | -0.0023 |
| dropout_0 | phys_only | C2 | 18 | 0.0039 | 0.0007 | 0.0059 | 0.1089 |
| dropout_0 | strong | C1 | 18 | 0.0084 | 0.0061 | 0.0103 | 0.0992 |
| dropout_0 | strong | C2 | 18 | 0.0004 | -0.0018 | 0.0023 | 0.0088 |
| dropout_0.5 | base | C1 | 18 | 0.0115 | 0.0084 | 0.0138 | 0.1153 |
| dropout_0.5 | base | C2 | 18 | 0.0049 | 0.0028 | 0.0072 | 0.1037 |
| dropout_0.5 | phys_only | C1 | 18 | 0.0081 | 0.0059 | 0.0105 | 0.1161 |
| dropout_0.5 | phys_only | C2 | 18 | 0.0042 | 0.0021 | 0.0065 | 0.0964 |
| dropout_0.75 | base | C1 | 18 | 0.0155 | 0.0134 | 0.0176 | 0.1228 |
| dropout_0.75 | base | C2 | 18 | 0.0080 | 0.0060 | 0.0105 | 0.1321 |
| dropout_0.75 | phys_only | C1 | 18 | 0.0105 | 0.0078 | 0.0129 | 0.1193 |
| dropout_0.75 | phys_only | C2 | 18 | 0.0079 | 0.0059 | 0.0109 | 0.1527 |
| dropout_0.9 | base | C1 | 18 | 0.0225 | 0.0205 | 0.0250 | 0.1518 |
| dropout_0.9 | base | C2 | 18 | 0.0084 | 0.0065 | 0.0106 | 0.1157 |
| dropout_0.9 | phys_only | C1 | 18 | 0.0165 | 0.0146 | 0.0189 | 0.1563 |
| dropout_0.9 | phys_only | C2 | 18 | 0.0102 | 0.0073 | 0.0121 | 0.1738 |
| echo_no | base | C1 | 18 | 0.0120 | 0.0080 | 0.0162 | 0.1612 |
| echo_no | base | C2 | 18 | 0.0014 | -0.0066 | 0.0057 | 0.0313 |
| echo_no | phys_only | C1 | 18 | 0.0016 | -0.0025 | 0.0060 | 0.0337 |
| echo_no | phys_only | C2 | 18 | -0.0054 | -0.0120 | 0.0020 | -0.1311 |
| echo_subcohort | echo_base | C1 | 18 | 0.0105 | 0.0056 | 0.0152 | 0.1281 |
| echo_subcohort | echo_base | C2 | 17 | -0.0157 | -0.0234 | -0.0048 | -0.3232 |
| echo_subcohort | echo_only | C1 | 18 | -0.0032 | -0.0096 | 0.0021 | -0.0946 |
| echo_subcohort | echo_only | C2 | 16 | -0.0043 | -0.0107 | 0.0020 | -0.1114 |
| echo_subcohort | echo_strong | C1 | 18 | 0.0047 | -0.0001 | 0.0094 | 0.0480 |
| echo_subcohort | echo_strong | C2 | 17 | 0.0024 | -0.0075 | 0.0082 | 0.0301 |
| echo_yes | base | C1 | 18 | 0.0109 | 0.0045 | 0.0143 | 0.1549 |
| echo_yes | base | C2 | 16 | -0.0047 | -0.0123 | 0.0016 | -0.1190 |
| echo_yes | phys_only | C1 | 18 | -0.0005 | -0.0055 | 0.0041 | -0.0102 |
| echo_yes | phys_only | C2 | 16 | 0.0020 | -0.0066 | 0.0068 | 0.0530 |
| hf_outcome | base | C1 | 18 | 0.0010 | -0.0006 | 0.0026 | 0.0215 |
| hf_outcome | base | C2 | 18 | 0.0017 | -0.0000 | 0.0033 | 0.0543 |
| hf_outcome | phys_only | C1 | 18 | 0.0030 | 0.0012 | 0.0042 | 0.0920 |
| hf_outcome | phys_only | C2 | 18 | 0.0040 | 0.0027 | 0.0056 | 0.1340 |

Mean |bias| by arm (across trials):

| pool | scenario | M1 sparse | M2 sparse+ECG | M3 hdPS200 | M4 hdPS200+ECG | R clinical | R+ physiology ref |
|---|---|---|---|---|---|---|---|
| density_high | base | 0.059 | 0.056 | 0.043 | 0.059 | 0.024 | 0.028 |
| density_high | phys_only | 0.045 | 0.040 | 0.029 | 0.055 | 0.018 | 0.017 |
| density_low | base | 0.039 | 0.039 | 0.044 | 0.041 | 0.027 | 0.029 |
| density_low | phys_only | 0.033 | 0.035 | 0.041 | 0.043 | 0.020 | 0.022 |
| density_mid | base | 0.051 | 0.048 | 0.041 | 0.042 | 0.031 | 0.026 |
| density_mid | phys_only | 0.039 | 0.040 | 0.033 | 0.037 | 0.026 | 0.027 |
| dropout_0 | base | 0.059 | 0.054 | 0.033 | 0.034 | 0.021 | 0.021 |
| dropout_0 | none | 0.041 | 0.038 | 0.022 | 0.023 | 0.019 | 0.015 |
| dropout_0 | null | 0.063 | 0.055 | 0.035 | 0.035 | 0.019 | 0.018 |
| dropout_0 | phys_only | 0.040 | 0.040 | 0.036 | 0.032 | 0.021 | 0.020 |
| dropout_0 | strong | 0.085 | 0.076 | 0.047 | 0.046 | 0.024 | 0.022 |
| dropout_0.5 | base | 0.099 | 0.088 | 0.048 | 0.043 | 0.032 | 0.030 |
| dropout_0.5 | phys_only | 0.070 | 0.062 | 0.043 | 0.039 | 0.028 | 0.028 |
| dropout_0.75 | base | 0.126 | 0.110 | 0.060 | 0.052 | 0.038 | 0.033 |
| dropout_0.75 | phys_only | 0.088 | 0.077 | 0.052 | 0.044 | 0.034 | 0.032 |
| dropout_0.9 | base | 0.148 | 0.126 | 0.073 | 0.064 | 0.044 | 0.037 |
| dropout_0.9 | phys_only | 0.106 | 0.089 | 0.059 | 0.049 | 0.037 | 0.035 |
| echo_no | base | 0.074 | 0.062 | 0.046 | 0.045 | 0.027 | 0.027 |
| echo_no | phys_only | 0.049 | 0.047 | 0.041 | 0.047 | 0.024 | 0.024 |
| echo_subcohort | echo_base | 0.082 | 0.072 | 0.047 | 0.064 | 0.042 | 0.028 |
| echo_subcohort | echo_only | 0.033 | 0.037 | 0.040 | 0.046 | 0.036 | 0.025 |
| echo_subcohort | echo_strong | 0.098 | 0.093 | 0.079 | 0.076 | 0.058 | 0.030 |
| echo_yes | base | 0.070 | 0.059 | 0.055 | 0.042 | 0.028 | 0.028 |
| echo_yes | phys_only | 0.046 | 0.046 | 0.041 | 0.038 | 0.026 | 0.029 |
| hf_outcome | base | 0.048 | 0.047 | 0.031 | 0.029 | 0.020 | 0.019 |
| hf_outcome | phys_only | 0.033 | 0.030 | 0.030 | 0.026 | 0.018 | 0.018 |

## Real data: mean over trials of err(ECG arm)² − err(comparator)² (negative = ECG closer)

Inference by the exact sign-flip test across trials; bootstrap interval (boot_lo, boot_hi) descriptive only (re-matching on resamples with duplicates is not valid for matching estimators).

| pool | contrast | target | trials | mean_d_sqerr | p_signflip | closer | loo_min | loo_max | without_cabana | boot_lo | boot_hi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| density_high | C1 | RCT | 17 | 0.0063 | 0.5490 | 11 | -0.0007 | 0.0111 | -0.0007 | -0.0542 | 0.0221 |
| density_high | C1 | R+ | 17 | -0.0021 | 0.9387 | 9 | -0.0055 | 0.0076 | -0.0055 | -0.0273 | 0.0219 |
| density_high | C2 | RCT | 17 | 0.0084 | 0.3075 | 5 | 0.0047 | 0.0135 | 0.0088 | -0.0635 | 0.2158 |
| density_high | C2 | R+ | 17 | 0.0034 | 0.5982 | 11 | -0.0010 | 0.0053 | 0.0036 | -0.0904 | 0.2186 |
| density_low | C1 | RCT | 18 | 0.0029 | 0.8708 | 9 | -0.0083 | 0.0085 | 0.0063 | -0.0826 | 0.0476 |
| density_low | C1 | R+ | 18 | 0.0074 | 0.2245 | 6 | 0.0041 | 0.0112 | 0.0074 | -0.0458 | 0.0490 |
| density_low | C2 | RCT | 18 | -0.0018 | 0.9408 | 10 | -0.0150 | 0.0020 | -0.0001 | -0.1791 | 0.1560 |
| density_low | C2 | R+ | 18 | 0.0079 | 0.6769 | 8 | -0.0033 | 0.0121 | 0.0069 | -0.1012 | 0.1207 |
| density_mid | C1 | RCT | 18 | 0.0074 | 0.6892 | 9 | -0.0040 | 0.0176 | -0.0040 | -0.0670 | 0.0506 |
| density_mid | C1 | R+ | 18 | 0.0015 | 0.8734 | 7 | -0.0022 | 0.0077 | -0.0022 | -0.0422 | 0.0477 |
| density_mid | C2 | RCT | 18 | -0.0075 | 0.6208 | 10 | -0.0115 | 0.0029 | -0.0102 | -0.0760 | 0.2462 |
| density_mid | C2 | R+ | 18 | -0.0161 | 0.1472 | 10 | -0.0194 | -0.0094 | -0.0165 | -0.0950 | 0.1945 |
| dropout_0.5 | C1 | RCT | 18 | -0.0308 | 0.1542 | 13 | -0.0376 | -0.0086 | -0.0086 | -0.0549 | 0.0001 |
| dropout_0.5 | C1 | R+ | 18 | -0.0091 | 0.5322 | 12 | -0.0127 | 0.0004 | 0.0004 | -0.0217 | -0.0006 |
| dropout_0.5 | C2 | RCT | 18 | 0.0142 | 0.9410 | 11 | -0.0061 | 0.0177 | 0.0149 | -0.0385 | 0.0232 |
| dropout_0.5 | C2 | R+ | 18 | 0.0064 | 0.9989 | 15 | -0.0056 | 0.0085 | 0.0068 | -0.0145 | 0.0168 |
| dropout_0.75 | C1 | RCT | 18 | -0.0452 | 0.0099 | 15 | -0.0492 | -0.0234 | -0.0234 | -0.0707 | -0.0103 |
| dropout_0.75 | C1 | R+ | 18 | -0.0132 | 0.3380 | 14 | -0.0198 | -0.0039 | -0.0039 | -0.0357 | -0.0049 |
| dropout_0.75 | C2 | RCT | 18 | -0.0163 | 0.0512 | 10 | -0.0180 | -0.0090 | -0.0090 | -0.0481 | 0.0126 |
| dropout_0.75 | C2 | R+ | 18 | -0.0033 | 0.2217 | 12 | -0.0046 | -0.0018 | -0.0042 | -0.0124 | 0.0150 |
| dropout_0.9 | C1 | RCT | 18 | -0.0578 | 0.2811 | 10 | -0.0725 | -0.0103 | -0.0103 | -0.0870 | -0.0301 |
| dropout_0.9 | C1 | R+ | 18 | -0.0279 | 0.1895 | 9 | -0.0331 | -0.0061 | -0.0061 | -0.0423 | -0.0104 |
| dropout_0.9 | C2 | RCT | 18 | -0.0277 | 0.0631 | 12 | -0.0312 | -0.0113 | -0.0113 | -0.0546 | 0.0106 |
| dropout_0.9 | C2 | R+ | 18 | -0.0034 | 0.4000 | 8 | -0.0048 | -0.0012 | -0.0038 | -0.0207 | 0.0147 |
| echo_no | C1 | RCT | 18 | -0.0201 | 0.7120 | 9 | -0.0322 | 0.0089 | 0.0089 | -0.0778 | 0.0382 |
| echo_no | C1 | R+ | 18 | 0.0040 | 0.7404 | 7 | 0.0003 | 0.0125 | 0.0125 | -0.0369 | 0.0401 |
| echo_no | C2 | RCT | 18 | 0.0092 | 0.6674 | 8 | 0.0008 | 0.0227 | 0.0125 | -0.0718 | 0.1192 |
| echo_no | C2 | R+ | 18 | -0.0115 | 0.7396 | 7 | -0.0152 | 0.0047 | -0.0141 | -0.0684 | 0.1077 |
| echo_yes | C1 | RCT | 18 | 0.0007 | 0.9679 | 7 | -0.0109 | 0.0161 | 0.0161 | -0.0693 | 0.0775 |
| echo_yes | C1 | R+ | 18 | -0.0088 | 0.4296 | 12 | -0.0154 | -0.0018 | -0.0018 | -0.0886 | 0.0888 |
| echo_yes | C2 | RCT | 18 | -0.0341 | 0.1925 | 10 | -0.0407 | -0.0185 | -0.0329 | -0.1558 | 0.2362 |
| echo_yes | C2 | R+ | 18 | -0.0083 | 0.7138 | 9 | -0.0145 | 0.0063 | -0.0109 | -0.1322 | 0.2162 |
| hf_outcome | C1 | R+ | 18 | -0.0047 | 0.0006 | 16 | -0.0052 | -0.0042 | -0.0043 | -0.0070 | 0.0040 |
| hf_outcome | C2 | R+ | 18 | -0.0000 | 0.9967 | 9 | -0.0015 | 0.0008 | -0.0000 | -0.0073 | 0.0054 |

## Hypotheses

| hypothesis | contrast | trials | test | estimate | lo | hi | supported |
|---|---|---|---|---|---|---|---|
| A (low vs high code density) | C1 | 17 | plasmode base: reduction(density_low) − reduction(density_high) | -0.0036 | -0.0099 | 0.0039 | False |
| A (low vs high code density) | C1 | 17 | plasmode phys_only: reduction(density_low) − reduction(density_high) | -0.0069 | -0.0141 | -0.0007 | False |
| A (low vs high code density) | C1 | 17 | real data vs R+: d(density_low) − d(density_high); lo = sign-flip p | 0.0099 | 0.4964 | – | False |
| C (no echo vs echo) | C1 | 18 | plasmode base: reduction(echo_no) − reduction(echo_yes) | 0.0011 | -0.0035 | 0.0090 | False |
| C (no echo vs echo) | C1 | 18 | plasmode phys_only: reduction(echo_no) − reduction(echo_yes) | 0.0021 | -0.0032 | 0.0089 | False |
| C (no echo vs echo) | C1 | 18 | real data vs R+: d(echo_no) − d(echo_yes); lo = sign-flip p | 0.0129 | 0.1868 | – | False |
| B (dropout 0.75 vs 0) | C1 | 18 | plasmode base: reduction(dropout_0.75) − reduction(dropout_0) | 0.0108 | 0.0078 | 0.0143 | True |
| B (dropout 0.75 vs 0) | C1 | 18 | plasmode phys_only: reduction(dropout_0.75) − reduction(dropout_0) | 0.0106 | 0.0068 | 0.0137 | True |
| D (echo physiology as hidden confounder) | C1 | 18 | plasmode echo_only: bias reduction | -0.0032 | -0.0096 | 0.0021 | False |
| D (echo physiology as hidden confounder) | C1 | 18 | plasmode echo_base: bias reduction | 0.0105 | 0.0056 | 0.0152 | True |
| D (echo physiology as hidden confounder) | C1 | 18 | plasmode echo_strong: bias reduction | 0.0047 | -0.0001 | 0.0094 | False |
| E (HF hospitalisation outcome) | C1 | 18 | plasmode base: bias reduction | 0.0010 | -0.0006 | 0.0026 | False |
| E (HF hospitalisation outcome) | C1 | 18 | real data vs R+ (lo = sign-flip p) | -0.0047 | 0.0006 | – | True |
| A (low vs high code density) | C2 | 15 | plasmode base: reduction(density_low) − reduction(density_high) | 0.0084 | -0.0002 | 0.0174 | False |
| A (low vs high code density) | C2 | 15 | plasmode phys_only: reduction(density_low) − reduction(density_high) | 0.0024 | -0.0083 | 0.0098 | False |
| A (low vs high code density) | C2 | 17 | real data vs R+: d(density_low) − d(density_high); lo = sign-flip p | 0.0026 | 0.8682 | – | False |
| C (no echo vs echo) | C2 | 16 | plasmode base: reduction(echo_no) − reduction(echo_yes) | 0.0041 | -0.0061 | 0.0119 | False |
| C (no echo vs echo) | C2 | 16 | plasmode phys_only: reduction(echo_no) − reduction(echo_yes) | -0.0052 | -0.0109 | 0.0051 | False |
| C (no echo vs echo) | C2 | 18 | real data vs R+: d(echo_no) − d(echo_yes); lo = sign-flip p | -0.0032 | 0.9043 | – | False |
| B (dropout 0.75 vs 0) | C2 | 18 | plasmode base: reduction(dropout_0.75) − reduction(dropout_0) | 0.0091 | 0.0062 | 0.0123 | True |
| B (dropout 0.75 vs 0) | C2 | 18 | plasmode phys_only: reduction(dropout_0.75) − reduction(dropout_0) | 0.0040 | 0.0014 | 0.0082 | True |
| D (echo physiology as hidden confounder) | C2 | 16 | plasmode echo_only: bias reduction | -0.0043 | -0.0107 | 0.0020 | False |
| D (echo physiology as hidden confounder) | C2 | 17 | plasmode echo_base: bias reduction | -0.0157 | -0.0234 | -0.0048 | False |
| D (echo physiology as hidden confounder) | C2 | 17 | plasmode echo_strong: bias reduction | 0.0024 | -0.0075 | 0.0082 | False |
| E (HF hospitalisation outcome) | C2 | 18 | plasmode base: bias reduction | 0.0017 | -0.0000 | 0.0033 | False |
| E (HF hospitalisation outcome) | C2 | 18 | real data vs R+ (lo = sign-flip p) | -0.0000 | 0.9967 | – | False |
| B (dropout; subsampled plasmode — primary after audit) | C1 | 18 | plasmode base: reduction(dropout 0.5) − reduction(intact); reductions +0.0096 vs +0.0040 | 0.0057 | 0.0025 | 0.0097 | True |
| B (dropout; subsampled plasmode — primary after audit) | C1 | 18 | plasmode base: reduction(dropout 0.75) − reduction(intact); reductions +0.0177 vs +0.0040 | 0.0137 | 0.0103 | 0.0176 | True |
| B (dropout; subsampled plasmode — primary after audit) | C1 | 18 | plasmode base: reduction(dropout 0.9) − reduction(intact); reductions +0.0207 vs +0.0040 | 0.0168 | 0.0138 | 0.0206 | True |
| B (dropout; subsampled plasmode — primary after audit) | C1 | 18 | plasmode phys_only: reduction(dropout 0.5) − reduction(intact); reductions +0.0041 vs +0.0006 | 0.0034 | 0.0002 | 0.0076 | True |
| B (dropout; subsampled plasmode — primary after audit) | C1 | 18 | plasmode phys_only: reduction(dropout 0.75) − reduction(intact); reductions +0.0088 vs +0.0006 | 0.0082 | 0.0048 | 0.0120 | True |
| B (dropout; subsampled plasmode — primary after audit) | C1 | 18 | plasmode phys_only: reduction(dropout 0.9) − reduction(intact); reductions +0.0158 vs +0.0006 | 0.0151 | 0.0120 | 0.0191 | True |
| B (dropout; subsampled plasmode — primary after audit) | C2 | 18 | plasmode base: reduction(dropout 0.5) − reduction(intact); reductions +0.0039 vs -0.0002 | 0.0040 | 0.0007 | 0.0077 | True |
| B (dropout; subsampled plasmode — primary after audit) | C2 | 18 | plasmode base: reduction(dropout 0.75) − reduction(intact); reductions +0.0082 vs -0.0002 | 0.0084 | 0.0047 | 0.0125 | True |
| B (dropout; subsampled plasmode — primary after audit) | C2 | 18 | plasmode base: reduction(dropout 0.9) − reduction(intact); reductions +0.0084 vs -0.0002 | 0.0085 | 0.0058 | 0.0125 | True |
| B (dropout; subsampled plasmode — primary after audit) | C2 | 18 | plasmode phys_only: reduction(dropout 0.5) − reduction(intact); reductions +0.0042 vs +0.0051 | -0.0009 | -0.0041 | 0.0036 | False |
| B (dropout; subsampled plasmode — primary after audit) | C2 | 18 | plasmode phys_only: reduction(dropout 0.75) − reduction(intact); reductions +0.0049 vs +0.0051 | -0.0002 | -0.0026 | 0.0045 | False |
| B (dropout; subsampled plasmode — primary after audit) | C2 | 18 | plasmode phys_only: reduction(dropout 0.9) − reduction(intact); reductions +0.0084 vs +0.0051 | 0.0032 | 0.0001 | 0.0072 | True |

Stratum feasibility (smaller arm >= 100 required): see docs/v14/strata.csv

| pool | trials_feasible | median_n |
|---|---|---|
| density_high | 18 | 2281 |
| density_low | 20 | 2324 |
| density_mid | 20 | 2302 |
| echo_no | 20 | 2862 |
| echo_subcohort | 20 | 2758 |
| echo_yes | 20 | 2764 |

