# v1.4 — where does the ECG add information? (exploratory; tag protocol-v1.4)

## Plasmode: bias reduction from adding the ECG (log-HR scale; positive = ECG arm less biased)

| pool | scenario | contrast | trials | bias_reduction | lo | hi | relative |
|---|---|---|---|---|---|---|---|
| density_high | base | C1 | 16 | -0.0008 | -0.0055 | 0.0032 | -0.0172 |
| density_high | base | C2 | 15 | -0.0023 | -0.0092 | 0.0044 | -0.0561 |
| density_high | phys_only | C1 | 16 | 0.0031 | -0.0015 | 0.0073 | 0.0997 |
| density_high | phys_only | C2 | 15 | -0.0047 | -0.0117 | 0.0025 | -0.2578 |
| density_low | base | C1 | 18 | -0.0032 | -0.0086 | 0.0020 | -0.0867 |
| density_low | base | C2 | 18 | 0.0049 | -0.0013 | 0.0103 | 0.1169 |
| density_low | phys_only | C1 | 18 | -0.0017 | -0.0072 | 0.0035 | -0.0472 |
| density_low | phys_only | C2 | 18 | -0.0042 | -0.0101 | 0.0017 | -0.0986 |
| density_mid | base | C1 | 18 | 0.0033 | -0.0006 | 0.0085 | 0.0687 |
| density_mid | base | C2 | 18 | -0.0008 | -0.0081 | 0.0060 | -0.0223 |
| density_mid | phys_only | C1 | 18 | -0.0011 | -0.0047 | 0.0029 | -0.0291 |
| density_mid | phys_only | C2 | 18 | -0.0085 | -0.0148 | -0.0009 | -0.2875 |
| dropout_0 | base | C1 | 18 | 0.0043 | 0.0014 | 0.0064 | 0.0750 |
| dropout_0 | base | C2 | 18 | -0.0022 | -0.0046 | -0.0002 | -0.0686 |
| dropout_0 | none | C1 | 18 | 0.0029 | 0.0002 | 0.0045 | 0.0732 |
| dropout_0 | none | C2 | 18 | -0.0013 | -0.0036 | 0.0014 | -0.0605 |
| dropout_0 | null | C1 | 18 | 0.0073 | 0.0050 | 0.0092 | 0.1187 |
| dropout_0 | null | C2 | 18 | 0.0008 | -0.0010 | 0.0027 | 0.0240 |
| dropout_0 | phys_only | C1 | 18 | 0.0001 | -0.0021 | 0.0026 | 0.0030 |
| dropout_0 | phys_only | C2 | 18 | 0.0031 | -0.0001 | 0.0051 | 0.0873 |
| dropout_0 | strong | C1 | 18 | 0.0070 | 0.0047 | 0.0089 | 0.0874 |
| dropout_0 | strong | C2 | 18 | -0.0003 | -0.0022 | 0.0019 | -0.0076 |
| dropout_0.5 | base | C1 | 18 | 0.0130 | 0.0101 | 0.0150 | 0.1296 |
| dropout_0.5 | base | C2 | 18 | 0.0049 | 0.0023 | 0.0068 | 0.1033 |
| dropout_0.5 | phys_only | C1 | 18 | 0.0084 | 0.0061 | 0.0108 | 0.1208 |
| dropout_0.5 | phys_only | C2 | 18 | 0.0046 | 0.0021 | 0.0070 | 0.1066 |
| dropout_0.75 | base | C1 | 18 | 0.0160 | 0.0139 | 0.0182 | 0.1282 |
| dropout_0.75 | base | C2 | 18 | 0.0075 | 0.0051 | 0.0103 | 0.1281 |
| dropout_0.75 | phys_only | C1 | 18 | 0.0110 | 0.0082 | 0.0133 | 0.1280 |
| dropout_0.75 | phys_only | C2 | 18 | 0.0075 | 0.0055 | 0.0100 | 0.1487 |
| dropout_0.9 | base | C1 | 18 | 0.0222 | 0.0201 | 0.0246 | 0.1511 |
| dropout_0.9 | base | C2 | 18 | 0.0098 | 0.0074 | 0.0120 | 0.1355 |
| dropout_0.9 | phys_only | C1 | 18 | 0.0164 | 0.0142 | 0.0186 | 0.1564 |
| dropout_0.9 | phys_only | C2 | 18 | 0.0111 | 0.0084 | 0.0133 | 0.1897 |
| echo_no | base | C1 | 18 | 0.0113 | 0.0076 | 0.0154 | 0.1552 |
| echo_no | base | C2 | 18 | -0.0013 | -0.0088 | 0.0049 | -0.0312 |
| echo_no | phys_only | C1 | 18 | 0.0007 | -0.0035 | 0.0048 | 0.0168 |
| echo_no | phys_only | C2 | 18 | -0.0063 | -0.0119 | 0.0015 | -0.1582 |
| echo_subcohort | echo_base | C1 | 18 | 0.0090 | 0.0035 | 0.0138 | 0.1094 |
| echo_subcohort | echo_base | C2 | 17 | -0.0172 | -0.0251 | -0.0055 | -0.3598 |
| echo_subcohort | echo_only | C1 | 18 | -0.0037 | -0.0095 | 0.0013 | -0.1132 |
| echo_subcohort | echo_only | C2 | 16 | -0.0041 | -0.0112 | 0.0024 | -0.1075 |
| echo_subcohort | echo_strong | C1 | 18 | 0.0059 | 0.0009 | 0.0101 | 0.0624 |
| echo_subcohort | echo_strong | C2 | 17 | 0.0024 | -0.0078 | 0.0083 | 0.0313 |
| echo_yes | base | C1 | 18 | 0.0086 | 0.0023 | 0.0119 | 0.1270 |
| echo_yes | base | C2 | 16 | -0.0054 | -0.0128 | 0.0007 | -0.1365 |
| echo_yes | phys_only | C1 | 18 | -0.0018 | -0.0064 | 0.0029 | -0.0392 |
| echo_yes | phys_only | C2 | 16 | 0.0035 | -0.0060 | 0.0083 | 0.0909 |
| hf_outcome | base | C1 | 18 | 0.0009 | -0.0006 | 0.0026 | 0.0198 |
| hf_outcome | base | C2 | 18 | 0.0025 | 0.0008 | 0.0044 | 0.0775 |
| hf_outcome | phys_only | C1 | 18 | 0.0025 | 0.0006 | 0.0042 | 0.0761 |
| hf_outcome | phys_only | C2 | 18 | 0.0052 | 0.0033 | 0.0065 | 0.1682 |

Mean |bias| by arm (across trials):

| pool | scenario | M1 sparse | M2 sparse+ECG | M3 hdPS200 | M4 hdPS200+ECG | R clinical | R+ physiology ref |
|---|---|---|---|---|---|---|---|
| density_high | base | 0.045 | 0.046 | 0.045 | 0.061 | 0.024 | 0.030 |
| density_high | phys_only | 0.031 | 0.028 | 0.027 | 0.034 | 0.017 | 0.017 |
| density_low | base | 0.037 | 0.041 | 0.042 | 0.037 | 0.026 | 0.030 |
| density_low | phys_only | 0.036 | 0.038 | 0.043 | 0.047 | 0.021 | 0.023 |
| density_mid | base | 0.047 | 0.044 | 0.036 | 0.036 | 0.030 | 0.025 |
| density_mid | phys_only | 0.038 | 0.040 | 0.030 | 0.038 | 0.027 | 0.027 |
| dropout_0 | base | 0.057 | 0.053 | 0.033 | 0.035 | 0.020 | 0.020 |
| dropout_0 | none | 0.040 | 0.037 | 0.022 | 0.023 | 0.019 | 0.014 |
| dropout_0 | null | 0.061 | 0.054 | 0.035 | 0.034 | 0.019 | 0.018 |
| dropout_0 | phys_only | 0.039 | 0.039 | 0.036 | 0.033 | 0.020 | 0.019 |
| dropout_0 | strong | 0.081 | 0.074 | 0.046 | 0.046 | 0.022 | 0.019 |
| dropout_0.5 | base | 0.100 | 0.087 | 0.047 | 0.042 | 0.032 | 0.031 |
| dropout_0.5 | phys_only | 0.070 | 0.061 | 0.043 | 0.038 | 0.029 | 0.030 |
| dropout_0.75 | base | 0.124 | 0.108 | 0.059 | 0.051 | 0.039 | 0.033 |
| dropout_0.75 | phys_only | 0.086 | 0.075 | 0.051 | 0.043 | 0.033 | 0.032 |
| dropout_0.9 | base | 0.147 | 0.124 | 0.072 | 0.062 | 0.045 | 0.036 |
| dropout_0.9 | phys_only | 0.105 | 0.088 | 0.059 | 0.047 | 0.037 | 0.035 |
| echo_no | base | 0.073 | 0.061 | 0.042 | 0.044 | 0.027 | 0.029 |
| echo_no | phys_only | 0.044 | 0.043 | 0.040 | 0.046 | 0.022 | 0.023 |
| echo_subcohort | echo_base | 0.082 | 0.073 | 0.047 | 0.065 | 0.041 | 0.027 |
| echo_subcohort | echo_only | 0.033 | 0.036 | 0.040 | 0.045 | 0.036 | 0.025 |
| echo_subcohort | echo_strong | 0.095 | 0.089 | 0.077 | 0.074 | 0.057 | 0.030 |
| echo_yes | base | 0.068 | 0.059 | 0.055 | 0.043 | 0.029 | 0.028 |
| echo_yes | phys_only | 0.045 | 0.047 | 0.043 | 0.038 | 0.026 | 0.029 |
| hf_outcome | base | 0.048 | 0.047 | 0.032 | 0.030 | 0.018 | 0.018 |
| hf_outcome | phys_only | 0.032 | 0.030 | 0.031 | 0.026 | 0.018 | 0.017 |

## Real-data paired bootstrap: mean over trials of err(ECG arm)² − err(comparator)² (negative = ECG closer)

| pool | contrast | target | trials | mean_d_sqerr | lo | hi |
|---|---|---|---|---|---|---|
| density_high | C1 | RCT | 16 | 0.0073 | -0.0332 | 0.0194 |
| density_high | C1 | R+ | 16 | -0.0024 | -0.0204 | 0.0254 |
| density_high | C2 | RCT | 16 | 0.0011 | -0.0515 | 0.1058 |
| density_high | C2 | R+ | 16 | -0.0018 | -0.0480 | 0.0983 |
| density_low | C1 | RCT | 18 | 0.0215 | -0.0788 | 0.0551 |
| density_low | C1 | R+ | 18 | 0.0088 | -0.0407 | 0.0472 |
| density_low | C2 | RCT | 18 | 0.0039 | -0.1785 | 0.1352 |
| density_low | C2 | R+ | 18 | 0.0103 | -0.1063 | 0.1246 |
| density_mid | C1 | RCT | 18 | 0.0274 | -0.0600 | 0.0518 |
| density_mid | C1 | R+ | 18 | 0.0078 | -0.0418 | 0.0451 |
| density_mid | C2 | RCT | 18 | -0.0104 | -0.0651 | 0.1671 |
| density_mid | C2 | R+ | 18 | -0.0184 | -0.0740 | 0.1347 |
| dropout_0.5 | C1 | RCT | 18 | -0.0389 | -0.0652 | -0.0055 |
| dropout_0.5 | C1 | R+ | 18 | -0.0129 | -0.0241 | 0.0020 |
| dropout_0.5 | C2 | RCT | 18 | 0.0112 | -0.0391 | 0.0183 |
| dropout_0.5 | C2 | R+ | 18 | 0.0064 | -0.0156 | 0.0169 |
| dropout_0.75 | C1 | RCT | 18 | -0.0560 | -0.0789 | -0.0163 |
| dropout_0.75 | C1 | R+ | 18 | -0.0179 | -0.0341 | -0.0049 |
| dropout_0.75 | C2 | RCT | 18 | -0.0152 | -0.0389 | 0.0118 |
| dropout_0.75 | C2 | R+ | 18 | -0.0026 | -0.0122 | 0.0149 |
| dropout_0.9 | C1 | RCT | 18 | -0.0438 | -0.0916 | -0.0283 |
| dropout_0.9 | C1 | R+ | 18 | -0.0189 | -0.0452 | -0.0090 |
| dropout_0.9 | C2 | RCT | 18 | -0.0266 | -0.0561 | 0.0091 |
| dropout_0.9 | C2 | R+ | 18 | -0.0033 | -0.0158 | 0.0179 |
| echo_no | C1 | RCT | 18 | -0.0247 | -0.0663 | 0.0390 |
| echo_no | C1 | R+ | 18 | 0.0017 | -0.0365 | 0.0379 |
| echo_no | C2 | RCT | 18 | 0.0063 | -0.0810 | 0.0949 |
| echo_no | C2 | R+ | 18 | -0.0117 | -0.0645 | 0.0870 |
| echo_yes | C1 | RCT | 18 | 0.0060 | -0.0662 | 0.0646 |
| echo_yes | C1 | R+ | 18 | -0.0068 | -0.0852 | 0.0822 |
| echo_yes | C2 | RCT | 18 | -0.0280 | -0.1535 | 0.2238 |
| echo_yes | C2 | R+ | 18 | -0.0132 | -0.1298 | 0.2224 |
| hf_outcome | C1 | R+ | 18 | -0.0040 | -0.0084 | 0.0039 |
| hf_outcome | C2 | R+ | 18 | -0.0008 | -0.0075 | 0.0051 |

## Hypotheses

| hypothesis | contrast | trials | test | estimate | lo | hi | supported |
|---|---|---|---|---|---|---|---|
| A (low vs high code density) | C1 | 16 | plasmode base: reduction(density_low) − reduction(density_high) | -0.0036 | -0.0101 | 0.0044 | False |
| A (low vs high code density) | C1 | 16 | plasmode phys_only: reduction(density_low) − reduction(density_high) | -0.0044 | -0.0117 | 0.0029 | False |
| A (low vs high code density) | C1 | 16 | bootstrap vs R+: d(density_low) − d(density_high) | 0.0133 | -0.0400 | 0.0526 | False |
| C (no echo vs echo) | C1 | 18 | plasmode base: reduction(echo_no) − reduction(echo_yes) | 0.0027 | -0.0020 | 0.0103 | False |
| C (no echo vs echo) | C1 | 18 | plasmode phys_only: reduction(echo_no) − reduction(echo_yes) | 0.0025 | -0.0036 | 0.0092 | False |
| C (no echo vs echo) | C1 | 18 | bootstrap vs R+: d(echo_no) − d(echo_yes) | 0.0085 | -0.1006 | 0.0792 | False |
| B (dropout 0.75 vs 0) | C1 | 18 | plasmode base: reduction(dropout_0.75) − reduction(dropout_0) | 0.0117 | 0.0086 | 0.0154 | True |
| B (dropout 0.75 vs 0) | C1 | 18 | plasmode phys_only: reduction(dropout_0.75) − reduction(dropout_0) | 0.0109 | 0.0076 | 0.0141 | True |
| D (echo physiology as hidden confounder) | C1 | 18 | plasmode echo_only: bias reduction | -0.0037 | -0.0095 | 0.0013 | False |
| D (echo physiology as hidden confounder) | C1 | 18 | plasmode echo_base: bias reduction | 0.0090 | 0.0035 | 0.0138 | True |
| D (echo physiology as hidden confounder) | C1 | 18 | plasmode echo_strong: bias reduction | 0.0059 | 0.0009 | 0.0101 | True |
| E (HF hospitalisation outcome) | C1 | 18 | plasmode base: bias reduction | 0.0009 | -0.0006 | 0.0026 | False |
| E (HF hospitalisation outcome) | C1 | 18 | bootstrap vs R+ | -0.0040 | -0.0084 | 0.0039 | False |
| A (low vs high code density) | C2 | 15 | plasmode base: reduction(density_low) − reduction(density_high) | 0.0099 | 0.0005 | 0.0186 | True |
| A (low vs high code density) | C2 | 15 | plasmode phys_only: reduction(density_low) − reduction(density_high) | 0.0002 | -0.0095 | 0.0080 | False |
| A (low vs high code density) | C2 | 16 | bootstrap vs R+: d(density_low) − d(density_high) | 0.0129 | -0.1040 | 0.0943 | False |
| C (no echo vs echo) | C2 | 16 | plasmode base: reduction(echo_no) − reduction(echo_yes) | 0.0016 | -0.0083 | 0.0100 | False |
| C (no echo vs echo) | C2 | 16 | plasmode phys_only: reduction(echo_no) − reduction(echo_yes) | -0.0077 | -0.0135 | 0.0025 | False |
| C (no echo vs echo) | C2 | 18 | bootstrap vs R+: d(echo_no) − d(echo_yes) | 0.0015 | -0.2270 | 0.1458 | False |
| B (dropout 0.75 vs 0) | C2 | 18 | plasmode base: reduction(dropout_0.75) − reduction(dropout_0) | 0.0098 | 0.0067 | 0.0134 | True |
| B (dropout 0.75 vs 0) | C2 | 18 | plasmode phys_only: reduction(dropout_0.75) − reduction(dropout_0) | 0.0044 | 0.0021 | 0.0088 | True |
| D (echo physiology as hidden confounder) | C2 | 16 | plasmode echo_only: bias reduction | -0.0041 | -0.0112 | 0.0024 | False |
| D (echo physiology as hidden confounder) | C2 | 17 | plasmode echo_base: bias reduction | -0.0172 | -0.0251 | -0.0055 | False |
| D (echo physiology as hidden confounder) | C2 | 17 | plasmode echo_strong: bias reduction | 0.0024 | -0.0078 | 0.0083 | False |
| E (HF hospitalisation outcome) | C2 | 18 | plasmode base: bias reduction | 0.0025 | 0.0008 | 0.0044 | True |
| E (HF hospitalisation outcome) | C2 | 18 | bootstrap vs R+ | -0.0008 | -0.0075 | 0.0051 | False |

Stratum feasibility (smaller arm >= 100 required): see docs/v14/strata.csv

| pool | trials_feasible | median_n |
|---|---|---|
| density_high | 16 | 2281 |
| density_low | 18 | 2324 |
| density_mid | 18 | 2302 |
| echo_no | 18 | 2862 |
| echo_subcohort | 18 | 2758 |
| echo_yes | 18 | 2764 |

