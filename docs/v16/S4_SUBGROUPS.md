# v1.6 sweep S4: populations / effect modifiers (2026-09-26)

Exploratory (post-hoc specification, `docs/V16_SWEEP_PLAN.md`). Script `scripts/v16/s4_subgroups.py`; long results `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s4-subgroups/results.csv`, summaries `summary.csv`, `metaregression.csv` (restricted dir, gitignored). Bases demo (age, sex, index year) and sparse; ECG = 32 BCL PCs; 1:1 caliper-0.2 matching on an L2 (C=1) PS re-fitted within each stratum; held-out balance and C-statistic computed in the stratum's matched set. Arms: base, base+ECG, base+shufECG, base+noise32; unmatched reference. Halves A/B = seeded patient split within trial (seed 16060 + trial index, stratified by treatment); strata are defined on the full trial cohort then intersected with the half. d = mean over trials of (ECG − base); negative = ECG better for all four metrics (|Δlog HR|, z², mean held-out |SMD|, held-out C-statistic). p = exact sign-flip; q = BH-FDR over all 48 full-cohort cells (both bases, row and trial-level strata) per metric. Trial x stratum skipped if either arm < 100 (full) or < 50 (per half); tests need >= 6 trials. **ECG-specific** = ECG vs base p < 0.05 with d < 0 AND ECG beats shufECG and noise32 in direction. **Replicated** = half A and half B d have the same sign as full.

<!-- KEYFINDINGS -->
## Key findings (plain language)

Figures: `S4_SUBGROUPS_forest.png` (ECG − base per stratum with 95% t-interval, sign-flip p and number of trials k; demo and sparse bases), `S4_SUBGROUPS_heatmap.png` (d and p for every cell, full / half A / half B). 46 full-cohort cells: 2 bases × (14 row strata + 9 testable trial-level strata). The 'close emulation = yes' stratum has only 5 trials, so it is shown but not tested.

1. **Held-out balance improves with ECG in almost every population, and the gain is ECG-specific.** No cell shows significant harm on any metric.
   - C-statistic: 33/46 cells have p < 0.05 with the ECG better and beat both placebos in direction. 29 of these also replicate in sign in both halves with q < 0.05.
   - Cells with p < 0.05 in **both** halves and also p < 0.05 against both shufECG and noise32 (the strictest reading):
     - demo base: ECG lag ≤ 90 d, ECG lag ≤ 30 d, echo = yes, echo = no, age ≥ 65, female, male, non-close emulations.
     - sparse base: echo = no and non-close emulations.
   - Mean held-out |SMD|: the same pattern, but concentrated on the demo base. 9 cells meet the strictest reading, all demo: all, lag ≤ 90, lag ≤ 30, echo = yes, age ≥ 65, female, male, physiology role, non-close.
   - On the sparse base the |SMD| gains are small, about −0.01 (for example −0.007 at 'all', q = 0.05). None meets the strictest reading.
2. **Agreement with RCT HRs: nominal gains, none survives FDR.**
   - z²: 15/46 cells have p < 0.05, ECG better and beating both placebos in direction. All 15 keep the same sign in both halves.
   - The lowest z² q-value is 0.08: demo 'all' d = −3.7, p = 0.006; demo lag ≤ 30 d; demo density T2; sparse lag ≤ 90 d.
   - Only 2 z² cells reach p < 0.05 in **both** halves:
     - sparse 'all': d = −1.40; half A p = 0.013; half B p = 0.030; q = 0.11.
     - sparse non-close emulations: 13 trials; d = −1.94; half A p = 0.036; half B p = 0.018; q = 0.09.
   - |Δlog HR|: 7 cells nominal, 0 survive FDR (minimum q 0.09), and none has p < 0.05 in both halves.
   - Consistency at 'all' (% of trials with |z| < 1.96), base → ECG: demo 56 → 61%; sparse 61 → 78%. The placebos reach 50–72%.
   - Dispersion φ is lower with ECG than base in 42/48 cells (all 48, including the untested 'close emulation = yes'), for example sparse 'all' 4.7 → 3.4 and demo 'all' 9.8 → 6.1. shufECG φ is lower than base in only 20/48. The exceptions include both low-confounding tertiles, sparse female, sparse inpatient and sparse control-role.
3. **Effect modifier that matters for RCT agreement: confounding magnitude.**
   - The ECG gain in |Δlog HR| and z² is concentrated in trials whose unadjusted estimate is far from the RCT.
   - Top tertile of |unadjusted − RCT|:
     - demo: z² d = −8.6, |Δlog HR| −0.11.
     - sparse: z² −3.5, |Δlog HR| −0.06.
     - Each has p = 0.031, the minimum possible with 6 trials. Neither survives FDR (q ≈ 0.1–0.2), and not every half reaches p < 0.05.
   - Lowest tertile: no gain; the point estimates slightly favour the base.
   - Meta-regression, univariable, per SD of confounding magnitude:
     - demo: |Δlog HR| slope −0.062, p = 0.004 (half A p = 0.007, half B p = 0.024); z² −5.3, p = 0.001 (A 0.003, B 0.056). The placebo slopes have the opposite sign, so this is ECG-specific.
     - sparse: z² −2.6, p < 0.001 (A 0.015, B 0.014). But shufECG shows part of the same slope (z² −1.3, p = 0.022), so part of the sparse slope reflects the base error rather than ECG information.
   - Caveat: confounding magnitude is measured against the same RCT benchmark used in the outcome, so part of this is regression toward the benchmark. The placebo control addresses this only partly.
4. **Populations that do not modify the ECG gain** (no significant subgroup difference visible; within-stratum estimates overlap):
   - **ECG recency:** lag ≤ 30 d, ≤ 90 d and all (≤ 365 d) give similar gains, with no recency gradient.
   - **Echo availability:** the balance gain is somewhat larger where echo is available (C-statistic: demo −0.027 vs −0.017; sparse −0.022 vs −0.011), plausibly because the held-out panel then contains echo variables. The RCT-agreement gain is not larger with echo (demo |Δlog HR| d = 0.000 with echo).
   - **Code density:** no monotone gradient. In the joint meta-regression, % echo and density are collinear, and their conditional slopes (positive for % echo, with a negative density slope on the demo base) are not interpretable.
   - **Age, sex and care setting:** no gradient on either base.
   - **Trial role:** physiology trials show larger point gains (demo z² −5.9 vs −1.8; |Δlog HR| −0.095, p = 0.055, k = 8) but nothing significant. The meta-regression physiology slope is significant only for the C-statistic (demo p = 0.040; sparse p = 0.021; both halves p < 0.05 on sparse).
   - **Trial size:** no pattern.
5. **Bottom line.**
   - ECG-specific, replicated balance gains appear across essentially all patient populations, strongest on the demo base.
   - Gains in RCT agreement are nominal and replicate in direction but do not survive FDR in any population.
   - The only consistent modifier of the RCT-agreement gain is how confounded the crude comparison is, and that finding carries the caveats in point 3.
   - Everything here is exploratory and hypothesis-generating. External MIMIC/UKB confirmation is deferred.
<!-- /KEYFINDINGS -->

## |Δlog HR| vs RCT (ECG − base; full cohort, with half A/B replication)

| base | family | stratum | k | d ECG−base | 95% lo | 95% hi | improved | p | q | d vs shuf | p vs shuf | d vs noise | p vs noise | ECG-specific | d half A | p A | d half B | p B | replicated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | recency | lag<=365 (all) | 18 | -0.058 | -0.110 | -0.005 | 14/18 | 0.034 | 0.220 | -0.062 | 0.083 | -0.051 | 0.120 | True | -0.040 | 0.105 | -0.054 | 0.128 | True |
| demo | recency | lag<=90 | 18 | -0.028 | -0.070 | 0.013 | 12/18 | 0.172 | 0.439 | -0.056 | 0.028 | -0.078 | 0.003 | False | -0.040 | 0.217 | -0.045 | 0.212 | True |
| demo | recency | lag<=30 | 18 | -0.055 | -0.104 | -0.005 | 13/18 | 0.019 | 0.220 | -0.054 | 0.040 | -0.065 | 0.018 | True | -0.053 | 0.131 | -0.052 | 0.081 | True |
| demo | echo | echo=yes | 18 | 0.000 | -0.064 | 0.064 | 6/18 | 0.999 | 0.999 | -0.009 | 0.760 | -0.044 | 0.244 | False | -0.062 | 0.225 | 0.068 | 0.527 | False |
| demo | echo | echo=no | 18 | -0.028 | -0.079 | 0.023 | 12/18 | 0.263 | 0.466 | -0.032 | 0.332 | -0.040 | 0.132 | False | -0.060 | 0.002 | -0.006 | 0.903 | True |
| demo | density | density=T1 (low) | 18 | -0.050 | -0.132 | 0.032 | 12/18 | 0.216 | 0.466 | -0.028 | 0.528 | -0.065 | 0.168 | False | -0.014 | 0.728 | -0.005 | 0.979 | True |
| demo | density | density=T2 | 18 | -0.073 | -0.122 | -0.024 | 15/18 | 0.006 | 0.148 | -0.074 | 0.008 | -0.059 | 0.027 | True | 0.012 | 0.690 | -0.019 | 0.560 | False |
| demo | density | density=T3 (high) | 17 | -0.023 | -0.072 | 0.026 | 7/17 | 0.339 | 0.538 | -0.042 | 0.019 | -0.034 | 0.165 | False | -0.012 | 0.677 | -0.029 | 0.375 | True |
| demo | age | age<65 | 18 | -0.047 | -0.129 | 0.035 | 10/18 | 0.255 | 0.466 | -0.120 | 0.007 | -0.130 | 0.006 | False | -0.057 | 0.182 | -0.151 | 0.005 | True |
| demo | age | age>=65 | 18 | -0.022 | -0.057 | 0.013 | 11/18 | 0.204 | 0.466 | -0.033 | 0.095 | -0.045 | 0.039 | False | -0.044 | 0.263 | -0.046 | 0.094 | True |
| demo | sex | sex=female | 18 | -0.054 | -0.113 | 0.004 | 11/18 | 0.068 | 0.287 | -0.060 | 0.017 | -0.021 | 0.512 | False | -0.072 | 0.135 | -0.020 | 0.665 | True |
| demo | sex | sex=male | 18 | -0.023 | -0.086 | 0.040 | 10/18 | 0.455 | 0.619 | -0.031 | 0.229 | -0.035 | 0.236 | False | -0.035 | 0.390 | -0.060 | 0.100 | True |
| demo | setting | setting=outpatient | 18 | -0.029 | -0.079 | 0.020 | 11/18 | 0.234 | 0.466 | -0.029 | 0.276 | -0.031 | 0.388 | False | -0.120 | 0.018 | -0.066 | 0.107 | True |
| demo | setting | setting=inpatient | 18 | -0.019 | -0.072 | 0.034 | 9/18 | 0.505 | 0.645 | -0.019 | 0.514 | -0.032 | 0.226 | False | -0.021 | 0.589 | -0.078 | 0.018 | True |
| demo | role | role=physiology | 8 | -0.095 | -0.191 | 0.000 | 6/8 | 0.055 | 0.287 | -0.114 | 0.078 | -0.102 | 0.062 | False | -0.078 | 0.164 | -0.132 | 0.055 | True |
| demo | role | role=control | 10 | -0.028 | -0.093 | 0.038 | 8/10 | 0.363 | 0.557 | -0.020 | 0.625 | -0.010 | 0.791 | False | -0.010 | 0.418 | 0.009 | 0.807 | False |
| demo | closeness | close emulation=yes | 5 | -0.066 | -0.194 | 0.062 | 4/5 | – | – | -0.065 | – | -0.044 | – | False | 0.030 | – | 0.031 | – | False |
| demo | closeness | close emulation=no | 13 | -0.054 | -0.120 | 0.012 | 10/13 | 0.098 | 0.300 | -0.061 | 0.186 | -0.054 | 0.197 | False | -0.067 | 0.024 | -0.087 | 0.039 | True |
| demo | confounding | |unadj-RCT| T1 (low) | 6 | 0.045 | -0.034 | 0.123 | 2/6 | 0.219 | 0.466 | 0.048 | 0.438 | 0.066 | 0.281 | False | 0.002 | 1.000 | 0.039 | 0.469 | True |
| demo | confounding | |unadj-RCT| T2 | 6 | -0.106 | -0.171 | -0.040 | 6/6 | 0.031 | 0.220 | -0.085 | 0.062 | -0.067 | 0.031 | True | -0.030 | 0.312 | -0.086 | 0.031 | True |
| demo | confounding | |unadj-RCT| T3 (high) | 6 | -0.112 | -0.211 | -0.013 | 6/6 | 0.031 | 0.220 | -0.148 | 0.094 | -0.153 | 0.031 | True | -0.092 | 0.156 | -0.115 | 0.188 | True |
| demo | size | N T1 (low) | 6 | -0.081 | -0.182 | 0.020 | 5/6 | 0.125 | 0.338 | -0.094 | 0.094 | -0.058 | 0.312 | False | -0.013 | 0.875 | -0.024 | 0.688 | True |
| demo | size | N T2 | 6 | -0.020 | -0.156 | 0.117 | 4/6 | 0.656 | 0.794 | -0.009 | 0.906 | -0.031 | 0.594 | False | -0.068 | 0.031 | -0.037 | 0.812 | True |
| demo | size | N T3 (high) | 6 | -0.072 | -0.169 | 0.025 | 5/6 | 0.125 | 0.338 | -0.082 | 0.156 | -0.065 | 0.156 | False | -0.040 | 0.188 | -0.101 | 0.062 | True |
| sparse | recency | lag<=365 (all) | 18 | -0.020 | -0.055 | 0.015 | 14/18 | 0.264 | 0.466 | -0.023 | 0.088 | -0.034 | 0.053 | False | -0.059 | 0.042 | -0.034 | 0.231 | True |
| sparse | recency | lag<=90 | 18 | -0.055 | -0.084 | -0.025 | 15/18 | 0.002 | 0.086 | -0.031 | 0.096 | -0.068 | 0.002 | True | -0.020 | 0.233 | -0.021 | 0.322 | True |
| sparse | recency | lag<=30 | 18 | -0.011 | -0.043 | 0.020 | 11/18 | 0.465 | 0.619 | -0.009 | 0.639 | -0.005 | 0.777 | False | -0.021 | 0.271 | -0.025 | 0.618 | True |
| sparse | echo | echo=yes | 18 | 0.026 | -0.025 | 0.076 | 7/18 | 0.296 | 0.486 | 0.027 | 0.254 | 0.015 | 0.492 | False | 0.007 | 0.733 | 0.018 | 0.746 | True |
| sparse | echo | echo=no | 18 | -0.009 | -0.073 | 0.054 | 11/18 | 0.783 | 0.831 | -0.022 | 0.334 | -0.040 | 0.136 | False | -0.046 | 0.090 | -0.041 | 0.240 | True |
| sparse | density | density=T1 (low) | 18 | -0.006 | -0.059 | 0.046 | 9/18 | 0.797 | 0.831 | -0.015 | 0.655 | 0.008 | 0.808 | False | -0.025 | 0.638 | -0.081 | 0.042 | True |
| sparse | density | density=T2 | 18 | -0.007 | -0.064 | 0.051 | 9/18 | 0.811 | 0.831 | -0.031 | 0.232 | -0.030 | 0.420 | False | -0.011 | 0.827 | -0.016 | 0.694 | True |
| sparse | density | density=T3 (high) | 17 | 0.007 | -0.029 | 0.043 | 11/17 | 0.680 | 0.802 | 0.029 | 0.138 | -0.016 | 0.479 | False | -0.027 | 0.305 | -0.027 | 0.367 | False |
| sparse | age | age<65 | 18 | -0.050 | -0.103 | 0.004 | 15/18 | 0.069 | 0.287 | -0.058 | 0.271 | -0.109 | 0.069 | False | 0.071 | 0.605 | 0.071 | 0.350 | False |
| sparse | age | age>=65 | 18 | -0.031 | -0.066 | 0.005 | 14/18 | 0.087 | 0.300 | -0.018 | 0.430 | -0.012 | 0.515 | False | -0.023 | 0.403 | 0.015 | 0.520 | False |
| sparse | sex | sex=female | 18 | -0.012 | -0.047 | 0.023 | 8/18 | 0.471 | 0.619 | 0.014 | 0.300 | -0.004 | 0.755 | False | -0.047 | 0.439 | -0.064 | 0.107 | True |
| sparse | sex | sex=male | 18 | -0.016 | -0.059 | 0.027 | 9/18 | 0.463 | 0.619 | -0.015 | 0.472 | -0.045 | 0.012 | False | -0.034 | 0.099 | -0.015 | 0.606 | True |
| sparse | setting | setting=outpatient | 18 | -0.022 | -0.059 | 0.015 | 11/18 | 0.230 | 0.466 | -0.013 | 0.504 | 0.003 | 0.870 | False | -0.013 | 0.758 | 0.011 | 0.720 | False |
| sparse | setting | setting=inpatient | 18 | 0.015 | -0.040 | 0.070 | 10/18 | 0.572 | 0.711 | 0.000 | 0.997 | 0.002 | 0.937 | False | 0.019 | 0.432 | -0.027 | 0.297 | False |
| sparse | role | role=physiology | 8 | -0.032 | -0.092 | 0.029 | 6/8 | 0.273 | 0.466 | -0.031 | 0.141 | -0.050 | 0.047 | False | -0.045 | 0.258 | -0.056 | 0.195 | True |
| sparse | role | role=control | 10 | -0.011 | -0.062 | 0.041 | 8/10 | 0.740 | 0.831 | -0.017 | 0.387 | -0.021 | 0.428 | False | -0.071 | 0.096 | -0.015 | 0.695 | True |
| sparse | closeness | close emulation=yes | 5 | -0.000 | -0.129 | 0.129 | 4/5 | – | – | -0.016 | – | -0.030 | – | False | -0.116 | – | 0.003 | – | False |
| sparse | closeness | close emulation=no | 13 | -0.028 | -0.062 | 0.007 | 10/13 | 0.086 | 0.300 | -0.026 | 0.049 | -0.035 | 0.020 | False | -0.038 | 0.120 | -0.048 | 0.128 | True |
| sparse | confounding | |unadj-RCT| T1 (low) | 6 | 0.020 | -0.068 | 0.109 | 3/6 | 0.812 | 0.831 | -0.008 | 0.875 | -0.033 | 0.438 | False | -0.088 | 0.469 | -0.024 | 0.750 | False |
| sparse | confounding | |unadj-RCT| T2 | 6 | -0.017 | -0.065 | 0.031 | 5/6 | 0.406 | 0.603 | -0.009 | 0.625 | -0.017 | 0.219 | False | -0.060 | 0.031 | -0.019 | 0.375 | True |
| sparse | confounding | |unadj-RCT| T3 (high) | 6 | -0.063 | -0.126 | -0.001 | 6/6 | 0.031 | 0.220 | -0.052 | 0.031 | -0.052 | 0.031 | True | -0.029 | 0.312 | -0.058 | 0.219 | True |
| sparse | size | N T1 (low) | 6 | 0.015 | -0.087 | 0.116 | 4/6 | 0.812 | 0.831 | -0.008 | 0.875 | -0.032 | 0.500 | False | -0.104 | 0.344 | -0.026 | 0.688 | False |
| sparse | size | N T2 | 6 | -0.049 | -0.120 | 0.023 | 5/6 | 0.094 | 0.300 | -0.043 | 0.031 | -0.047 | 0.031 | False | -0.017 | 0.438 | -0.097 | 0.062 | True |
| sparse | size | N T3 (high) | 6 | -0.026 | -0.048 | -0.004 | 5/6 | 0.062 | 0.287 | -0.018 | 0.406 | -0.023 | 0.156 | False | -0.057 | 0.125 | 0.023 | 0.562 | False |

## z² (ECG − base; full cohort, with half A/B replication)

| base | family | stratum | k | d ECG−base | 95% lo | 95% hi | improved | p | q | d vs shuf | p vs shuf | d vs noise | p vs noise | ECG-specific | d half A | p A | d half B | p B | replicated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | recency | lag<=365 (all) | 18 | -3.667 | -6.548 | -0.785 | 14/18 | 0.006 | 0.078 | -4.671 | 0.021 | -4.499 | 0.015 | True | -2.625 | 0.032 | -3.243 | 0.083 | True |
| demo | recency | lag<=90 | 18 | -1.858 | -4.261 | 0.545 | 12/18 | 0.133 | 0.227 | -3.542 | 0.023 | -4.044 | 0.002 | False | -1.896 | 0.150 | -2.216 | 0.116 | True |
| demo | recency | lag<=30 | 18 | -3.314 | -6.249 | -0.379 | 13/18 | 0.002 | 0.078 | -2.867 | 0.013 | -3.717 | 0.007 | True | -1.434 | 0.230 | -1.743 | 0.067 | True |
| demo | echo | echo=yes | 18 | -0.545 | -2.374 | 1.284 | 6/18 | 0.595 | 0.636 | -1.602 | 0.149 | -1.572 | 0.159 | False | -1.381 | 0.110 | -0.732 | 0.671 | True |
| demo | echo | echo=no | 18 | -1.862 | -4.011 | 0.287 | 12/18 | 0.053 | 0.137 | -2.580 | 0.021 | -2.331 | 0.015 | False | -1.730 | 0.004 | -1.641 | 0.137 | True |
| demo | density | density=T1 (low) | 18 | -1.335 | -3.438 | 0.768 | 12/18 | 0.208 | 0.299 | -0.696 | 0.487 | -1.200 | 0.251 | False | -0.853 | 0.126 | -0.411 | 0.578 | True |
| demo | density | density=T2 | 18 | -1.839 | -3.197 | -0.481 | 15/18 | 0.007 | 0.078 | -1.686 | 0.011 | -1.555 | 0.004 | True | -0.208 | 0.783 | -0.361 | 0.358 | True |
| demo | density | density=T3 (high) | 17 | -0.446 | -2.372 | 1.480 | 8/17 | 0.687 | 0.718 | -0.731 | 0.145 | -1.560 | 0.055 | False | -0.948 | 0.033 | -0.522 | 0.338 | True |
| demo | age | age<65 | 18 | -2.830 | -6.523 | 0.863 | 9/18 | 0.053 | 0.137 | -3.685 | 0.002 | -4.428 | 0.009 | False | -1.851 | 0.026 | -1.834 | 0.008 | True |
| demo | age | age>=65 | 18 | -2.053 | -4.244 | 0.139 | 11/18 | 0.024 | 0.111 | -2.543 | 0.010 | -3.062 | 0.008 | True | -2.769 | 0.057 | -2.089 | 0.014 | True |
| demo | sex | sex=female | 18 | -2.417 | -4.744 | -0.089 | 12/18 | 0.025 | 0.111 | -1.990 | 0.018 | -2.222 | 0.138 | True | -1.678 | 0.077 | -2.167 | 0.028 | True |
| demo | sex | sex=male | 18 | -2.332 | -5.531 | 0.868 | 9/18 | 0.159 | 0.252 | -2.950 | 0.008 | -2.715 | 0.069 | False | -2.275 | 0.049 | -1.985 | 0.036 | True |
| demo | setting | setting=outpatient | 18 | -1.234 | -3.421 | 0.953 | 11/18 | 0.235 | 0.327 | -1.489 | 0.236 | -1.495 | 0.347 | False | -1.695 | 0.016 | -1.478 | 0.081 | True |
| demo | setting | setting=inpatient | 18 | -0.772 | -2.203 | 0.658 | 9/18 | 0.295 | 0.367 | -1.301 | 0.175 | -0.687 | 0.432 | False | -0.502 | 0.715 | -1.725 | 0.003 | True |
| demo | role | role=physiology | 8 | -5.943 | -12.318 | 0.431 | 6/8 | 0.055 | 0.137 | -8.771 | 0.078 | -7.888 | 0.055 | False | -4.609 | 0.188 | -6.965 | 0.055 | True |
| demo | role | role=control | 10 | -1.845 | -4.097 | 0.406 | 8/10 | 0.082 | 0.172 | -1.390 | 0.275 | -1.788 | 0.166 | False | -1.038 | 0.068 | -0.266 | 0.828 | True |
| demo | closeness | close emulation=yes | 5 | -1.998 | -4.803 | 0.807 | 4/5 | – | – | -1.904 | – | -2.808 | – | False | -0.020 | – | 0.227 | – | False |
| demo | closeness | close emulation=no | 13 | -4.308 | -8.329 | -0.288 | 10/13 | 0.024 | 0.111 | -5.734 | 0.050 | -5.149 | 0.065 | True | -3.627 | 0.018 | -4.578 | 0.067 | True |
| demo | confounding | |unadj-RCT| T1 (low) | 6 | 0.948 | -0.975 | 2.872 | 2/6 | 0.250 | 0.329 | 1.029 | 0.312 | 0.990 | 0.375 | False | 0.079 | 0.938 | 0.514 | 0.281 | True |
| demo | confounding | |unadj-RCT| T2 | 6 | -3.395 | -6.022 | -0.768 | 6/6 | 0.031 | 0.111 | -2.923 | 0.062 | -2.116 | 0.031 | True | -0.874 | 0.344 | -3.655 | 0.031 | True |
| demo | confounding | |unadj-RCT| T3 (high) | 6 | -8.553 | -15.991 | -1.116 | 6/6 | 0.031 | 0.111 | -12.118 | 0.062 | -12.372 | 0.031 | True | -7.081 | 0.094 | -6.589 | 0.281 | True |
| demo | size | N T1 (low) | 6 | -3.928 | -10.991 | 3.134 | 5/6 | 0.094 | 0.172 | -5.901 | 0.094 | -5.776 | 0.125 | False | -2.867 | 0.844 | -3.272 | 0.688 | True |
| demo | size | N T2 | 6 | -3.286 | -11.393 | 4.820 | 4/6 | 0.312 | 0.378 | -4.274 | 0.750 | -4.705 | 0.344 | False | -3.416 | 0.031 | -3.807 | 0.469 | True |
| demo | size | N T3 (high) | 6 | -3.786 | -6.921 | -0.650 | 5/6 | 0.062 | 0.137 | -3.837 | 0.062 | -3.016 | 0.062 | False | -1.593 | 0.156 | -2.650 | 0.281 | True |
| sparse | recency | lag<=365 (all) | 18 | -1.403 | -2.769 | -0.037 | 14/18 | 0.024 | 0.111 | -1.128 | 0.026 | -1.562 | 0.015 | True | -1.475 | 0.013 | -1.223 | 0.030 | True |
| sparse | recency | lag<=90 | 18 | -1.452 | -2.483 | -0.421 | 15/18 | 0.005 | 0.078 | -1.220 | 0.059 | -2.015 | 0.001 | True | -0.660 | 0.117 | -0.308 | 0.402 | True |
| sparse | recency | lag<=30 | 18 | -0.830 | -1.918 | 0.259 | 11/18 | 0.129 | 0.227 | -0.867 | 0.127 | -0.611 | 0.269 | False | -0.505 | 0.168 | -0.720 | 0.168 | True |
| sparse | echo | echo=yes | 18 | -0.710 | -1.979 | 0.559 | 7/18 | 0.262 | 0.335 | -0.182 | 0.793 | -0.188 | 0.740 | False | -0.302 | 0.350 | -0.280 | 0.736 | True |
| sparse | echo | echo=no | 18 | -1.024 | -2.013 | -0.036 | 11/18 | 0.042 | 0.129 | -1.012 | 0.054 | -1.450 | 0.018 | True | -0.770 | 0.039 | -0.800 | 0.054 | True |
| sparse | density | density=T1 (low) | 18 | -0.573 | -1.451 | 0.305 | 9/18 | 0.190 | 0.282 | -0.614 | 0.323 | -0.171 | 0.649 | False | -0.533 | 0.329 | -0.529 | 0.104 | True |
| sparse | density | density=T2 | 18 | -0.354 | -1.450 | 0.741 | 9/18 | 0.515 | 0.608 | -0.327 | 0.360 | -0.859 | 0.257 | False | -0.319 | 0.636 | -0.692 | 0.140 | True |
| sparse | density | density=T3 (high) | 17 | -0.464 | -1.681 | 0.752 | 11/17 | 0.553 | 0.621 | 0.176 | 0.624 | -1.187 | 0.123 | False | -0.267 | 0.439 | -0.454 | 0.141 | True |
| sparse | age | age<65 | 18 | -1.077 | -2.117 | -0.036 | 15/18 | 0.040 | 0.129 | -2.228 | 0.062 | -2.066 | 0.037 | True | -0.207 | 0.584 | -0.173 | 0.801 | True |
| sparse | age | age>=65 | 18 | -1.408 | -2.754 | -0.062 | 14/18 | 0.017 | 0.111 | -1.527 | 0.065 | -0.759 | 0.145 | True | -0.270 | 0.600 | -0.289 | 0.437 | True |
| sparse | sex | sex=female | 18 | -0.206 | -0.918 | 0.507 | 10/18 | 0.553 | 0.621 | 0.092 | 0.691 | -0.264 | 0.590 | False | -0.156 | 0.764 | -0.741 | 0.055 | True |
| sparse | sex | sex=male | 18 | -0.756 | -2.038 | 0.526 | 9/18 | 0.249 | 0.329 | -0.480 | 0.360 | -1.065 | 0.009 | False | -1.440 | 0.036 | -0.915 | 0.091 | True |
| sparse | setting | setting=outpatient | 18 | -0.606 | -1.443 | 0.231 | 10/18 | 0.149 | 0.244 | -1.147 | 0.204 | -0.278 | 0.611 | False | -0.663 | 0.347 | -0.305 | 0.479 | True |
| sparse | setting | setting=inpatient | 18 | 0.081 | -0.907 | 1.069 | 10/18 | 0.888 | 0.888 | -0.279 | 0.529 | -0.145 | 0.707 | False | 0.297 | 0.469 | -0.352 | 0.451 | False |
| sparse | role | role=physiology | 8 | -2.068 | -5.107 | 0.970 | 6/8 | 0.086 | 0.172 | -1.865 | 0.094 | -2.639 | 0.047 | False | -1.527 | 0.102 | -1.901 | 0.070 | True |
| sparse | role | role=control | 10 | -0.871 | -2.166 | 0.423 | 8/10 | 0.174 | 0.267 | -0.539 | 0.248 | -0.700 | 0.205 | False | -1.433 | 0.072 | -0.681 | 0.234 | True |
| sparse | closeness | close emulation=yes | 5 | -0.011 | -1.683 | 1.661 | 4/5 | – | – | -0.100 | – | -0.442 | – | False | -0.774 | – | -0.125 | – | True |
| sparse | closeness | close emulation=no | 13 | -1.939 | -3.749 | -0.129 | 10/13 | 0.010 | 0.094 | -1.524 | 0.013 | -1.992 | 0.012 | True | -1.744 | 0.036 | -1.645 | 0.018 | True |
| sparse | confounding | |unadj-RCT| T1 (low) | 6 | 0.288 | -0.801 | 1.376 | 3/6 | 0.750 | 0.767 | -0.085 | 0.875 | -0.553 | 0.438 | False | -0.419 | 0.594 | -0.639 | 0.469 | False |
| sparse | confounding | |unadj-RCT| T2 | 6 | -0.996 | -2.079 | 0.088 | 5/6 | 0.062 | 0.137 | -0.976 | 0.438 | -0.945 | 0.219 | False | -1.277 | 0.031 | -0.654 | 0.344 | True |
| sparse | confounding | |unadj-RCT| T3 (high) | 6 | -3.502 | -7.512 | 0.507 | 6/6 | 0.031 | 0.111 | -2.325 | 0.031 | -3.187 | 0.031 | True | -2.729 | 0.156 | -2.376 | 0.094 | True |
| sparse | size | N T1 (low) | 6 | -0.555 | -3.013 | 1.903 | 4/6 | 0.594 | 0.636 | -1.105 | 0.625 | -2.007 | 0.375 | False | -0.729 | 0.312 | -0.472 | 0.375 | True |
| sparse | size | N T2 | 6 | -2.351 | -6.441 | 1.740 | 5/6 | 0.094 | 0.172 | -1.704 | 0.031 | -2.149 | 0.031 | False | -1.014 | 0.406 | -2.902 | 0.062 | True |
| sparse | size | N T3 (high) | 6 | -1.304 | -3.131 | 0.523 | 5/6 | 0.062 | 0.137 | -0.576 | 0.281 | -0.529 | 0.156 | False | -2.681 | 0.062 | -0.295 | 0.656 | True |

## mean held-out |SMD| (ECG − base; full cohort, with half A/B replication)

| base | family | stratum | k | d ECG−base | 95% lo | 95% hi | improved | p | q | d vs shuf | p vs shuf | d vs noise | p vs noise | ECG-specific | d half A | p A | d half B | p B | replicated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | recency | lag<=365 (all) | 18 | -0.0233 | -0.0318 | -0.0149 | 17/18 | <0.001 | <0.001 | -0.0280 | <0.001 | -0.0228 | <0.001 | True | -0.0191 | 0.003 | -0.0226 | <0.001 | True |
| demo | recency | lag<=90 | 18 | -0.0233 | -0.0327 | -0.0139 | 16/18 | <0.001 | <0.001 | -0.0268 | <0.001 | -0.0241 | <0.001 | True | -0.0271 | <0.001 | -0.0195 | 0.004 | True |
| demo | recency | lag<=30 | 18 | -0.0182 | -0.0263 | -0.0102 | 15/18 | <0.001 | 0.002 | -0.0184 | <0.001 | -0.0180 | 0.001 | True | -0.0144 | 0.032 | -0.0187 | 0.002 | True |
| demo | echo | echo=yes | 18 | -0.0265 | -0.0376 | -0.0154 | 17/18 | <0.001 | <0.001 | -0.0225 | 0.007 | -0.0241 | 0.002 | True | -0.0210 | <0.001 | -0.0317 | <0.001 | True |
| demo | echo | echo=no | 18 | -0.0110 | -0.0235 | 0.0016 | 15/18 | 0.083 | 0.098 | -0.0168 | <0.001 | -0.0130 | 0.061 | False | -0.0226 | 0.118 | -0.0178 | 0.036 | True |
| demo | density | density=T1 (low) | 18 | -0.0142 | -0.0286 | 0.0002 | 12/18 | 0.051 | 0.076 | -0.0092 | 0.093 | -0.0139 | 0.046 | False | -0.0068 | 0.556 | -0.0177 | 0.049 | True |
| demo | density | density=T2 | 18 | -0.0163 | -0.0271 | -0.0055 | 14/18 | 0.005 | 0.017 | -0.0197 | <0.001 | -0.0208 | 0.003 | True | -0.0102 | 0.122 | -0.0128 | 0.065 | True |
| demo | density | density=T3 (high) | 17 | -0.0200 | -0.0348 | -0.0052 | 14/17 | 0.002 | 0.008 | -0.0195 | <0.001 | -0.0190 | 0.004 | True | -0.0220 | 0.003 | -0.0138 | 0.112 | True |
| demo | age | age<65 | 18 | -0.0200 | -0.0337 | -0.0062 | 14/18 | 0.006 | 0.017 | -0.0153 | 0.114 | -0.0197 | 0.030 | True | -0.0227 | 0.017 | -0.0416 | <0.001 | True |
| demo | age | age>=65 | 18 | -0.0180 | -0.0249 | -0.0110 | 17/18 | <0.001 | <0.001 | -0.0243 | <0.001 | -0.0197 | <0.001 | True | -0.0227 | 0.003 | -0.0222 | <0.001 | True |
| demo | sex | sex=female | 18 | -0.0230 | -0.0343 | -0.0117 | 17/18 | <0.001 | <0.001 | -0.0337 | <0.001 | -0.0275 | 0.002 | True | -0.0114 | 0.012 | -0.0163 | 0.006 | True |
| demo | sex | sex=male | 18 | -0.0233 | -0.0354 | -0.0112 | 15/18 | <0.001 | 0.004 | -0.0206 | 0.008 | -0.0225 | <0.001 | True | -0.0194 | 0.006 | -0.0173 | 0.016 | True |
| demo | setting | setting=outpatient | 18 | -0.0135 | -0.0195 | -0.0075 | 16/18 | <0.001 | <0.001 | -0.0146 | 0.010 | -0.0162 | 0.007 | True | -0.0082 | 0.294 | -0.0082 | 0.140 | True |
| demo | setting | setting=inpatient | 18 | -0.0195 | -0.0350 | -0.0040 | 15/18 | 0.001 | 0.005 | -0.0185 | 0.015 | -0.0223 | <0.001 | True | -0.0121 | 0.156 | -0.0217 | 0.004 | True |
| demo | role | role=physiology | 8 | -0.0264 | -0.0403 | -0.0125 | 8/8 | 0.008 | 0.021 | -0.0340 | 0.008 | -0.0277 | 0.008 | True | -0.0221 | 0.047 | -0.0299 | 0.039 | True |
| demo | role | role=control | 10 | -0.0208 | -0.0335 | -0.0082 | 9/10 | 0.004 | 0.014 | -0.0232 | 0.006 | -0.0188 | 0.002 | True | -0.0167 | 0.055 | -0.0167 | 0.004 | True |
| demo | closeness | close emulation=yes | 5 | -0.0250 | -0.0522 | 0.0021 | 4/5 | – | – | -0.0322 | – | -0.0218 | – | False | -0.0114 | – | -0.0132 | – | True |
| demo | closeness | close emulation=no | 13 | -0.0226 | -0.0322 | -0.0131 | 13/13 | <0.001 | 0.002 | -0.0264 | <0.001 | -0.0231 | <0.001 | True | -0.0220 | <0.001 | -0.0262 | <0.001 | True |
| demo | confounding | |unadj-RCT| T1 (low) | 6 | -0.0252 | -0.0420 | -0.0083 | 5/6 | 0.062 | 0.076 | -0.0336 | 0.062 | -0.0262 | 0.031 | False | -0.0187 | 0.125 | -0.0367 | 0.031 | True |
| demo | confounding | |unadj-RCT| T2 | 6 | -0.0175 | -0.0272 | -0.0078 | 6/6 | 0.031 | 0.053 | -0.0187 | 0.031 | -0.0122 | 0.031 | True | -0.0082 | 0.344 | -0.0088 | 0.281 | True |
| demo | confounding | |unadj-RCT| T3 (high) | 6 | -0.0273 | -0.0525 | -0.0022 | 6/6 | 0.031 | 0.053 | -0.0317 | 0.031 | -0.0299 | 0.031 | True | -0.0303 | 0.031 | -0.0223 | 0.062 | True |
| demo | size | N T1 (low) | 6 | -0.0146 | -0.0277 | -0.0015 | 5/6 | 0.062 | 0.076 | -0.0226 | 0.062 | -0.0167 | 0.031 | False | -0.0024 | 0.812 | -0.0174 | 0.250 | True |
| demo | size | N T2 | 6 | -0.0360 | -0.0565 | -0.0156 | 6/6 | 0.031 | 0.053 | -0.0361 | 0.031 | -0.0329 | 0.031 | True | -0.0323 | 0.031 | -0.0301 | 0.031 | True |
| demo | size | N T3 (high) | 6 | -0.0193 | -0.0317 | -0.0068 | 6/6 | 0.031 | 0.053 | -0.0254 | 0.031 | -0.0187 | 0.031 | True | -0.0225 | 0.031 | -0.0204 | 0.062 | True |
| sparse | recency | lag<=365 (all) | 18 | -0.0067 | -0.0133 | 0.0000 | 14/18 | 0.026 | 0.053 | -0.0061 | 0.059 | -0.0079 | 0.004 | True | -0.0029 | 0.504 | -0.0083 | 0.033 | True |
| sparse | recency | lag<=90 | 18 | -0.0068 | -0.0150 | 0.0014 | 10/18 | 0.100 | 0.115 | -0.0072 | 0.093 | -0.0076 | 0.039 | False | -0.0063 | 0.201 | -0.0097 | 0.023 | True |
| sparse | recency | lag<=30 | 18 | -0.0103 | -0.0179 | -0.0028 | 14/18 | 0.008 | 0.021 | -0.0088 | 0.024 | -0.0117 | 0.005 | True | -0.0091 | 0.137 | -0.0105 | 0.028 | True |
| sparse | echo | echo=yes | 18 | -0.0089 | -0.0173 | -0.0005 | 15/18 | 0.039 | 0.061 | -0.0092 | 0.014 | -0.0087 | 0.071 | True | -0.0037 | 0.382 | -0.0016 | 0.830 | True |
| sparse | echo | echo=no | 18 | -0.0157 | -0.0295 | -0.0019 | 12/18 | 0.025 | 0.053 | -0.0103 | 0.099 | -0.0106 | 0.081 | True | -0.0078 | 0.249 | -0.0036 | 0.524 | True |
| sparse | density | density=T1 (low) | 18 | -0.0104 | -0.0261 | 0.0053 | 12/18 | 0.180 | 0.197 | -0.0145 | 0.008 | -0.0115 | 0.095 | False | 0.0024 | 0.727 | -0.0034 | 0.737 | False |
| sparse | density | density=T2 | 18 | -0.0103 | -0.0205 | -0.0000 | 12/18 | 0.044 | 0.067 | -0.0044 | 0.345 | -0.0097 | 0.089 | True | -0.0050 | 0.400 | -0.0126 | 0.041 | True |
| sparse | density | density=T3 (high) | 17 | -0.0058 | -0.0118 | 0.0002 | 12/17 | 0.059 | 0.076 | -0.0079 | 0.046 | -0.0120 | 0.008 | False | 0.0102 | 0.383 | -0.0032 | 0.594 | False |
| sparse | age | age<65 | 18 | -0.0041 | -0.0199 | 0.0117 | 11/18 | 0.594 | 0.607 | -0.0029 | 0.753 | -0.0093 | 0.221 | False | -0.0040 | 0.581 | -0.0075 | 0.314 | True |
| sparse | age | age>=65 | 18 | -0.0056 | -0.0126 | 0.0014 | 11/18 | 0.111 | 0.125 | -0.0084 | 0.048 | -0.0076 | 0.002 | False | -0.0028 | 0.417 | -0.0009 | 0.859 | True |
| sparse | sex | sex=female | 18 | -0.0072 | -0.0149 | 0.0005 | 14/18 | 0.062 | 0.076 | -0.0079 | 0.053 | -0.0097 | 0.041 | False | -0.0149 | 0.001 | -0.0075 | 0.232 | True |
| sparse | sex | sex=male | 18 | -0.0098 | -0.0179 | -0.0017 | 14/18 | 0.018 | 0.045 | -0.0092 | 0.041 | -0.0112 | 0.020 | True | -0.0047 | 0.336 | -0.0103 | 0.066 | True |
| sparse | setting | setting=outpatient | 18 | -0.0120 | -0.0196 | -0.0044 | 15/18 | 0.002 | 0.008 | -0.0074 | 0.020 | -0.0142 | <0.001 | True | -0.0063 | 0.169 | -0.0190 | 0.001 | True |
| sparse | setting | setting=inpatient | 18 | -0.0121 | -0.0233 | -0.0010 | 15/18 | 0.034 | 0.057 | -0.0100 | 0.103 | -0.0109 | 0.116 | True | -0.0036 | 0.585 | -0.0142 | 0.025 | True |
| sparse | role | role=physiology | 8 | -0.0121 | -0.0269 | 0.0026 | 7/8 | 0.062 | 0.076 | -0.0099 | 0.102 | -0.0128 | 0.023 | False | -0.0061 | 0.352 | -0.0164 | 0.023 | True |
| sparse | role | role=control | 10 | -0.0023 | -0.0073 | 0.0027 | 7/10 | 0.322 | 0.345 | -0.0030 | 0.375 | -0.0040 | 0.104 | False | -0.0003 | 0.957 | -0.0019 | 0.670 | True |
| sparse | closeness | close emulation=yes | 5 | -0.0002 | -0.0121 | 0.0116 | 3/5 | – | – | 0.0002 | – | -0.0049 | – | False | 0.0110 | – | 0.0041 | – | False |
| sparse | closeness | close emulation=no | 13 | -0.0091 | -0.0177 | -0.0006 | 11/13 | 0.007 | 0.021 | -0.0085 | 0.027 | -0.0091 | 0.009 | True | -0.0082 | 0.055 | -0.0131 | 0.002 | True |
| sparse | confounding | |unadj-RCT| T1 (low) | 6 | -0.0088 | -0.0334 | 0.0158 | 3/6 | 0.469 | 0.490 | -0.0043 | 0.719 | -0.0155 | 0.062 | False | 0.0025 | 0.844 | -0.0113 | 0.281 | False |
| sparse | confounding | |unadj-RCT| T2 | 6 | -0.0030 | -0.0059 | -0.0000 | 5/6 | 0.062 | 0.076 | -0.0094 | 0.062 | -0.0034 | 0.344 | False | -0.0048 | 0.281 | -0.0113 | 0.031 | True |
| sparse | confounding | |unadj-RCT| T3 (high) | 6 | -0.0082 | -0.0138 | -0.0025 | 6/6 | 0.031 | 0.053 | -0.0045 | 0.062 | -0.0049 | 0.125 | True | -0.0064 | 0.094 | -0.0024 | 0.719 | True |
| sparse | size | N T1 (low) | 6 | 0.0013 | -0.0072 | 0.0098 | 3/6 | 0.688 | 0.688 | -0.0000 | 1.000 | -0.0089 | 0.094 | False | 0.0115 | 0.312 | -0.0023 | 0.719 | False |
| sparse | size | N T2 | 6 | -0.0151 | -0.0341 | 0.0038 | 5/6 | 0.062 | 0.076 | -0.0131 | 0.062 | -0.0086 | 0.250 | False | -0.0131 | 0.031 | -0.0177 | 0.062 | True |
| sparse | size | N T3 (high) | 6 | -0.0062 | -0.0142 | 0.0018 | 6/6 | 0.031 | 0.053 | -0.0051 | 0.125 | -0.0063 | 0.125 | True | -0.0071 | 0.094 | -0.0050 | 0.438 | True |

## held-out C-statistic (ECG − base; full cohort, with half A/B replication)

| base | family | stratum | k | d ECG−base | 95% lo | 95% hi | improved | p | q | d vs shuf | p vs shuf | d vs noise | p vs noise | ECG-specific | d half A | p A | d half B | p B | replicated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | recency | lag<=365 (all) | 18 | -0.0175 | -0.0284 | -0.0066 | 15/18 | 0.004 | 0.017 | -0.0241 | <0.001 | -0.0233 | <0.001 | True | -0.0145 | 0.089 | -0.0279 | <0.001 | True |
| demo | recency | lag<=90 | 18 | -0.0224 | -0.0335 | -0.0113 | 16/18 | <0.001 | 0.003 | -0.0236 | <0.001 | -0.0249 | <0.001 | True | -0.0315 | <0.001 | -0.0248 | 0.002 | True |
| demo | recency | lag<=30 | 18 | -0.0150 | -0.0276 | -0.0024 | 15/18 | 0.021 | 0.042 | -0.0227 | <0.001 | -0.0198 | 0.001 | True | -0.0195 | 0.003 | -0.0168 | <0.001 | True |
| demo | echo | echo=yes | 18 | -0.0270 | -0.0418 | -0.0122 | 14/18 | <0.001 | 0.003 | -0.0270 | <0.001 | -0.0257 | <0.001 | True | -0.0264 | 0.010 | -0.0322 | <0.001 | True |
| demo | echo | echo=no | 18 | -0.0168 | -0.0304 | -0.0031 | 14/18 | 0.005 | 0.017 | -0.0146 | 0.011 | -0.0216 | <0.001 | True | -0.0221 | 0.023 | -0.0200 | <0.001 | True |
| demo | density | density=T1 (low) | 18 | -0.0081 | -0.0243 | 0.0080 | 12/18 | 0.313 | 0.360 | -0.0195 | 0.003 | -0.0127 | 0.197 | False | -0.0110 | 0.398 | -0.0118 | 0.230 | True |
| demo | density | density=T2 | 18 | -0.0190 | -0.0355 | -0.0025 | 12/18 | 0.017 | 0.037 | -0.0235 | 0.002 | -0.0296 | <0.001 | True | -0.0018 | 0.854 | -0.0238 | 0.004 | True |
| demo | density | density=T3 (high) | 17 | -0.0243 | -0.0404 | -0.0081 | 15/17 | 0.006 | 0.017 | -0.0202 | 0.010 | -0.0211 | 0.001 | True | -0.0344 | 0.002 | -0.0142 | 0.139 | True |
| demo | age | age<65 | 18 | -0.0230 | -0.0339 | -0.0121 | 15/18 | <0.001 | 0.003 | -0.0186 | 0.044 | -0.0116 | 0.322 | True | -0.0195 | 0.114 | -0.0368 | <0.001 | True |
| demo | age | age>=65 | 18 | -0.0195 | -0.0287 | -0.0103 | 16/18 | <0.001 | 0.004 | -0.0192 | 0.002 | -0.0175 | 0.001 | True | -0.0331 | <0.001 | -0.0163 | 0.014 | True |
| demo | sex | sex=female | 18 | -0.0165 | -0.0304 | -0.0026 | 14/18 | 0.018 | 0.037 | -0.0245 | <0.001 | -0.0202 | 0.002 | True | -0.0214 | 0.016 | -0.0202 | <0.001 | True |
| demo | sex | sex=male | 18 | -0.0228 | -0.0379 | -0.0077 | 12/18 | 0.005 | 0.017 | -0.0242 | <0.001 | -0.0187 | <0.001 | True | -0.0198 | 0.002 | -0.0234 | <0.001 | True |
| demo | setting | setting=outpatient | 18 | -0.0209 | -0.0380 | -0.0037 | 14/18 | 0.013 | 0.031 | -0.0239 | 0.007 | -0.0237 | <0.001 | True | -0.0227 | 0.051 | -0.0103 | 0.298 | True |
| demo | setting | setting=inpatient | 18 | -0.0174 | -0.0277 | -0.0072 | 16/18 | 0.002 | 0.011 | -0.0235 | <0.001 | -0.0212 | 0.004 | True | -0.0422 | 0.001 | -0.0161 | 0.108 | True |
| demo | role | role=physiology | 8 | -0.0264 | -0.0512 | -0.0016 | 6/8 | 0.047 | 0.065 | -0.0350 | 0.016 | -0.0328 | 0.023 | True | -0.0261 | 0.180 | -0.0465 | 0.008 | True |
| demo | role | role=control | 10 | -0.0103 | -0.0173 | -0.0034 | 9/10 | 0.006 | 0.017 | -0.0154 | 0.002 | -0.0157 | 0.002 | True | -0.0053 | 0.219 | -0.0130 | 0.021 | True |
| demo | closeness | close emulation=yes | 5 | -0.0012 | -0.0229 | 0.0205 | 3/5 | – | – | -0.0125 | – | -0.0162 | – | False | 0.0046 | – | -0.0094 | – | False |
| demo | closeness | close emulation=no | 13 | -0.0237 | -0.0362 | -0.0113 | 12/13 | 0.001 | 0.008 | -0.0285 | <0.001 | -0.0260 | <0.001 | True | -0.0219 | 0.045 | -0.0350 | <0.001 | True |
| demo | confounding | |unadj-RCT| T1 (low) | 6 | -0.0193 | -0.0456 | 0.0069 | 4/6 | 0.188 | 0.233 | -0.0277 | 0.031 | -0.0273 | 0.031 | False | -0.0103 | 0.594 | -0.0359 | 0.062 | True |
| demo | confounding | |unadj-RCT| T2 | 6 | -0.0091 | -0.0322 | 0.0139 | 5/6 | 0.375 | 0.411 | -0.0136 | 0.062 | -0.0120 | 0.188 | False | -0.0030 | 0.625 | -0.0193 | 0.094 | True |
| demo | confounding | |unadj-RCT| T3 (high) | 6 | -0.0239 | -0.0446 | -0.0033 | 6/6 | 0.031 | 0.048 | -0.0309 | 0.031 | -0.0306 | 0.031 | True | -0.0303 | 0.125 | -0.0285 | 0.031 | True |
| demo | size | N T1 (low) | 6 | -0.0111 | -0.0435 | 0.0212 | 3/6 | 0.438 | 0.468 | -0.0250 | 0.062 | -0.0282 | 0.094 | False | -0.0073 | 0.844 | -0.0383 | 0.062 | True |
| demo | size | N T2 | 6 | -0.0232 | -0.0397 | -0.0067 | 6/6 | 0.031 | 0.048 | -0.0265 | 0.031 | -0.0209 | 0.031 | True | -0.0227 | 0.062 | -0.0232 | 0.062 | True |
| demo | size | N T3 (high) | 6 | -0.0181 | -0.0377 | 0.0015 | 6/6 | 0.031 | 0.048 | -0.0208 | 0.031 | -0.0209 | 0.031 | True | -0.0135 | 0.125 | -0.0222 | 0.031 | True |
| sparse | recency | lag<=365 (all) | 18 | -0.0133 | -0.0249 | -0.0016 | 15/18 | 0.023 | 0.044 | -0.0176 | 0.004 | -0.0156 | 0.002 | True | -0.0203 | <0.001 | -0.0133 | 0.055 | True |
| sparse | recency | lag<=90 | 18 | -0.0116 | -0.0211 | -0.0022 | 15/18 | 0.017 | 0.037 | -0.0146 | 0.003 | -0.0180 | 0.001 | True | -0.0117 | 0.119 | -0.0107 | 0.106 | True |
| sparse | recency | lag<=30 | 18 | -0.0162 | -0.0273 | -0.0051 | 13/18 | 0.004 | 0.017 | -0.0191 | <0.001 | -0.0171 | 0.002 | True | -0.0173 | 0.015 | -0.0096 | 0.128 | True |
| sparse | echo | echo=yes | 18 | -0.0215 | -0.0351 | -0.0080 | 16/18 | <0.001 | 0.003 | -0.0236 | <0.001 | -0.0213 | <0.001 | True | -0.0349 | 0.001 | 0.0038 | 0.805 | False |
| sparse | echo | echo=no | 18 | -0.0106 | -0.0188 | -0.0024 | 15/18 | 0.006 | 0.017 | -0.0129 | 0.003 | -0.0149 | 0.010 | True | -0.0265 | 0.006 | -0.0205 | 0.025 | True |
| sparse | density | density=T1 (low) | 18 | -0.0038 | -0.0202 | 0.0125 | 10/18 | 0.640 | 0.640 | -0.0058 | 0.431 | -0.0013 | 0.869 | False | -0.0148 | 0.023 | -0.0198 | 0.037 | True |
| sparse | density | density=T2 | 18 | -0.0133 | -0.0256 | -0.0009 | 11/18 | 0.029 | 0.048 | -0.0143 | 0.055 | -0.0151 | 0.008 | True | -0.0269 | 0.002 | -0.0184 | 0.012 | True |
| sparse | density | density=T3 (high) | 17 | -0.0205 | -0.0349 | -0.0062 | 14/17 | 0.008 | 0.020 | -0.0126 | 0.108 | -0.0195 | 0.003 | True | -0.0276 | 0.016 | -0.0244 | 0.017 | True |
| sparse | age | age<65 | 18 | -0.0191 | -0.0314 | -0.0067 | 14/18 | 0.004 | 0.017 | -0.0123 | 0.031 | -0.0141 | 0.115 | True | -0.0136 | 0.178 | -0.0205 | 0.053 | True |
| sparse | age | age>=65 | 18 | -0.0093 | -0.0214 | 0.0028 | 10/18 | 0.122 | 0.161 | -0.0175 | <0.001 | -0.0126 | 0.009 | False | -0.0071 | 0.150 | -0.0134 | 0.121 | True |
| sparse | sex | sex=female | 18 | -0.0161 | -0.0318 | -0.0004 | 12/18 | 0.045 | 0.065 | -0.0136 | 0.065 | -0.0114 | 0.121 | True | -0.0083 | 0.128 | -0.0147 | 0.107 | True |
| sparse | sex | sex=male | 18 | -0.0148 | -0.0250 | -0.0047 | 14/18 | 0.005 | 0.017 | -0.0201 | <0.001 | -0.0189 | <0.001 | True | -0.0183 | 0.004 | -0.0155 | 0.082 | True |
| sparse | setting | setting=outpatient | 18 | -0.0069 | -0.0206 | 0.0069 | 11/18 | 0.307 | 0.360 | -0.0146 | 0.016 | -0.0173 | 0.001 | False | -0.0093 | 0.340 | -0.0162 | 0.075 | True |
| sparse | setting | setting=inpatient | 18 | -0.0111 | -0.0264 | 0.0043 | 13/18 | 0.146 | 0.187 | -0.0101 | 0.243 | -0.0123 | 0.047 | False | -0.0086 | 0.325 | -0.0156 | 0.166 | True |
| sparse | role | role=physiology | 8 | -0.0237 | -0.0475 | 0.0000 | 7/8 | 0.047 | 0.065 | -0.0305 | 0.031 | -0.0272 | 0.016 | True | -0.0365 | 0.008 | -0.0292 | 0.031 | True |
| sparse | role | role=control | 10 | -0.0049 | -0.0158 | 0.0061 | 8/10 | 0.352 | 0.394 | -0.0074 | 0.121 | -0.0064 | 0.061 | False | -0.0074 | 0.078 | -0.0005 | 0.953 | True |
| sparse | closeness | close emulation=yes | 5 | 0.0057 | -0.0209 | 0.0324 | 3/5 | – | – | -0.0022 | – | -0.0004 | – | False | -0.0120 | – | 0.0098 | – | False |
| sparse | closeness | close emulation=no | 13 | -0.0206 | -0.0329 | -0.0082 | 12/13 | <0.001 | 0.004 | -0.0235 | 0.002 | -0.0215 | <0.001 | True | -0.0235 | 0.003 | -0.0221 | <0.001 | True |
| sparse | confounding | |unadj-RCT| T1 (low) | 6 | -0.0156 | -0.0462 | 0.0150 | 5/6 | 0.250 | 0.303 | -0.0215 | 0.188 | -0.0214 | 0.094 | False | -0.0222 | 0.156 | -0.0152 | 0.438 | True |
| sparse | confounding | |unadj-RCT| T2 | 6 | -0.0035 | -0.0184 | 0.0114 | 4/6 | 0.562 | 0.588 | -0.0125 | 0.219 | -0.0090 | 0.344 | False | -0.0147 | 0.125 | -0.0056 | 0.250 | True |
| sparse | confounding | |unadj-RCT| T3 (high) | 6 | -0.0207 | -0.0470 | 0.0057 | 6/6 | 0.031 | 0.048 | -0.0188 | 0.062 | -0.0165 | 0.031 | True | -0.0240 | 0.031 | -0.0190 | 0.094 | True |
| sparse | size | N T1 (low) | 6 | -0.0106 | -0.0493 | 0.0281 | 4/6 | 0.594 | 0.607 | -0.0192 | 0.250 | -0.0180 | 0.156 | False | -0.0221 | 0.094 | -0.0123 | 0.562 | True |
| sparse | size | N T2 | 6 | -0.0128 | -0.0349 | 0.0092 | 5/6 | 0.062 | 0.085 | -0.0128 | 0.281 | -0.0148 | 0.156 | False | -0.0179 | 0.125 | -0.0115 | 0.125 | True |
| sparse | size | N T3 (high) | 6 | -0.0163 | -0.0236 | -0.0091 | 6/6 | 0.031 | 0.048 | -0.0208 | 0.031 | -0.0141 | 0.031 | True | -0.0211 | 0.031 | -0.0160 | 0.062 | True |

## Consistency (% trials |z| < 1.96) and dispersion φ per arm (full cohort)

| base | stratum | n_trials | cons_unmatched | cons_base | cons_ECG | cons_shufECG | cons_noise | phi_unmatched | phi_base | phi_ECG | phi_shufECG | phi_noise |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo | lag<=365 (all) | 18 | 50.00 | 55.56 | 61.11 | 50.00 | 55.56 | 13.84 | 9.75 | 6.08 | 11.12 | 10.90 |
| demo | lag<=90 | 18 | 50.00 | 61.11 | 66.67 | 55.56 | 55.56 | 12.09 | 7.80 | 5.89 | 9.67 | 9.86 |
| demo | lag<=30 | 18 | 55.56 | 50.00 | 66.67 | 55.56 | 55.56 | 10.63 | 8.64 | 5.11 | 8.07 | 8.72 |
| demo | echo=yes | 18 | 61.11 | 61.11 | 55.56 | 55.56 | 55.56 | 8.54 | 5.78 | 5.18 | 6.92 | 6.76 |
| demo | echo=no | 18 | 33.33 | 61.11 | 72.22 | 55.56 | 61.11 | 9.43 | 5.15 | 3.30 | 6.03 | 5.81 |
| demo | density=T1 (low) | 18 | 50.00 | 66.67 | 66.67 | 72.22 | 66.67 | 5.33 | 3.73 | 2.03 | 3.02 | 3.36 |
| demo | density=T2 | 18 | 50.00 | 66.67 | 77.78 | 66.67 | 72.22 | 7.20 | 4.51 | 2.60 | 4.39 | 4.13 |
| demo | density=T3 (high) | 17 | 70.59 | 70.59 | 76.47 | 64.71 | 64.71 | 4.77 | 3.16 | 2.69 | 3.49 | 4.37 |
| demo | age<65 | 18 | 38.89 | 66.67 | 77.78 | 55.56 | 66.67 | 9.69 | 7.55 | 4.04 | 8.17 | 8.66 |
| demo | age>=65 | 18 | 55.56 | 61.11 | 61.11 | 55.56 | 55.56 | 10.39 | 7.17 | 4.83 | 7.61 | 8.21 |
| demo | sex=female | 18 | 38.89 | 55.56 | 66.67 | 50.00 | 55.56 | 10.56 | 8.26 | 5.40 | 7.67 | 7.98 |
| demo | sex=male | 18 | 55.56 | 66.67 | 72.22 | 66.67 | 50.00 | 10.35 | 7.54 | 4.93 | 7.96 | 7.71 |
| demo | setting=outpatient | 18 | 61.11 | 66.67 | 77.78 | 66.67 | 72.22 | 7.01 | 3.75 | 2.24 | 4.01 | 4.03 |
| demo | setting=inpatient | 18 | 55.56 | 61.11 | 66.67 | 61.11 | 55.56 | 6.59 | 5.39 | 4.48 | 5.95 | 5.29 |
| demo | role=physiology | 8 | 62.50 | 62.50 | 75.00 | 50.00 | 62.50 | 17.54 | 13.37 | 6.51 | 16.30 | 15.04 |
| demo | role=control | 10 | 40.00 | 50.00 | 50.00 | 50.00 | 50.00 | 8.23 | 6.09 | 4.59 | 6.10 | 5.96 |
| demo | close emulation=yes | 5 | 60.00 | 60.00 | 80.00 | 60.00 | 60.00 | 3.73 | 3.25 | 2.34 | 3.71 | 3.79 |
| demo | close emulation=no | 13 | 46.15 | 53.85 | 53.85 | 46.15 | 53.85 | 17.54 | 12.05 | 7.47 | 13.86 | 13.24 |
| demo | |unadj-RCT| T1 (low) | 6 | 100.00 | 100.00 | 83.33 | 100.00 | 100.00 | 0.61 | 0.33 | 1.53 | 0.32 | 0.37 |
| demo | |unadj-RCT| T2 | 6 | 50.00 | 66.67 | 83.33 | 50.00 | 66.67 | 4.73 | 5.43 | 2.49 | 5.38 | 4.41 |
| demo | |unadj-RCT| T3 (high) | 6 | 0.00 | 0.00 | 16.67 | 0.00 | 0.00 | 39.92 | 27.02 | 16.31 | 31.50 | 31.68 |
| demo | N T1 (low) | 6 | 83.33 | 83.33 | 83.33 | 66.67 | 83.33 | 6.70 | 6.03 | 1.70 | 7.07 | 6.17 |
| demo | N T2 | 6 | 33.33 | 50.00 | 33.33 | 50.00 | 50.00 | 16.28 | 10.38 | 7.85 | 12.67 | 12.54 |
| demo | N T3 (high) | 6 | 33.33 | 33.33 | 66.67 | 33.33 | 33.33 | 14.56 | 11.39 | 7.14 | 11.36 | 10.12 |
| sparse | lag<=365 (all) | 18 | 50.00 | 61.11 | 77.78 | 66.67 | 72.22 | 13.84 | 4.70 | 3.41 | 4.59 | 4.91 |
| sparse | lag<=90 | 18 | 50.00 | 66.67 | 83.33 | 72.22 | 66.67 | 12.09 | 3.78 | 2.49 | 3.70 | 4.60 |
| sparse | lag<=30 | 18 | 55.56 | 72.22 | 72.22 | 72.22 | 77.78 | 10.63 | 3.36 | 2.66 | 3.43 | 3.12 |
| sparse | echo=yes | 18 | 61.11 | 66.67 | 72.22 | 77.78 | 77.78 | 8.54 | 4.00 | 3.24 | 3.43 | 3.44 |
| sparse | echo=no | 18 | 33.33 | 72.22 | 77.78 | 77.78 | 66.67 | 9.43 | 3.14 | 2.35 | 3.10 | 3.43 |
| sparse | density=T1 (low) | 18 | 50.00 | 72.22 | 77.78 | 83.33 | 72.22 | 5.33 | 2.04 | 1.40 | 2.11 | 1.71 |
| sparse | density=T2 | 18 | 50.00 | 72.22 | 83.33 | 72.22 | 77.78 | 7.20 | 2.85 | 2.40 | 2.80 | 3.38 |
| sparse | density=T3 (high) | 17 | 70.59 | 70.59 | 70.59 | 76.47 | 64.71 | 4.77 | 3.10 | 2.60 | 2.42 | 3.84 |
| sparse | age<65 | 18 | 38.89 | 77.78 | 88.89 | 72.22 | 77.78 | 9.69 | 3.86 | 2.62 | 5.05 | 4.97 |
| sparse | age>=65 | 18 | 55.56 | 72.22 | 66.67 | 66.67 | 72.22 | 10.39 | 4.41 | 2.90 | 4.53 | 3.72 |
| sparse | sex=female | 18 | 38.89 | 61.11 | 66.67 | 72.22 | 61.11 | 10.56 | 3.37 | 3.38 | 3.23 | 3.68 |
| sparse | sex=male | 18 | 55.56 | 83.33 | 77.78 | 83.33 | 77.78 | 10.35 | 3.95 | 3.16 | 3.74 | 4.31 |
| sparse | setting=outpatient | 18 | 61.11 | 83.33 | 83.33 | 83.33 | 83.33 | 7.01 | 2.72 | 1.94 | 3.26 | 2.35 |
| sparse | setting=inpatient | 18 | 55.56 | 77.78 | 77.78 | 72.22 | 66.67 | 6.59 | 2.63 | 2.80 | 3.10 | 2.97 |
| sparse | role=physiology | 8 | 62.50 | 62.50 | 75.00 | 62.50 | 62.50 | 17.54 | 6.37 | 4.10 | 5.99 | 7.00 |
| sparse | role=control | 10 | 40.00 | 60.00 | 80.00 | 70.00 | 80.00 | 8.23 | 2.58 | 2.61 | 2.61 | 2.52 |
| sparse | close emulation=yes | 5 | 60.00 | 100.00 | 100.00 | 100.00 | 100.00 | 3.73 | 0.88 | 1.46 | 1.02 | 1.22 |
| sparse | close emulation=no | 13 | 46.15 | 46.15 | 69.23 | 53.85 | 61.54 | 17.54 | 6.31 | 4.34 | 6.08 | 6.46 |
| sparse | |unadj-RCT| T1 (low) | 6 | 100.00 | 100.00 | 100.00 | 100.00 | 100.00 | 0.61 | 0.51 | 0.89 | 0.90 | 1.20 |
| sparse | |unadj-RCT| T2 | 6 | 50.00 | 50.00 | 83.33 | 66.67 | 66.67 | 4.73 | 2.79 | 2.12 | 3.30 | 2.89 |
| sparse | |unadj-RCT| T3 (high) | 6 | 0.00 | 33.33 | 50.00 | 33.33 | 50.00 | 39.92 | 12.37 | 8.35 | 11.24 | 12.33 |
| sparse | N T1 (low) | 6 | 83.33 | 83.33 | 83.33 | 83.33 | 83.33 | 6.70 | 2.35 | 1.90 | 2.64 | 4.11 |
| sparse | N T2 | 6 | 33.33 | 66.67 | 66.67 | 66.67 | 66.67 | 16.28 | 4.76 | 3.33 | 4.02 | 4.40 |
| sparse | N T3 (high) | 6 | 33.33 | 33.33 | 83.33 | 50.00 | 66.67 | 14.56 | 5.65 | 4.33 | 5.12 | 4.94 |

## Trial-level strata (subsets of the 18 trials at stratum 'all')

Confounding magnitude = |unmatched log HR − RCT log HR| in the full trial cohort; size = analysed N; tertiles by rank.

| family | stratum | k | trials |
|---|---|---|---|
| role | role=physiology | 8 | east-afnet4, transform-hf, cabana-v2, comet, paradigm-hf-seq, elite-ii, emperor-preserved-v2, life |
| role | role=control | 10 | allhat, aristotle, ascot, value, ontarget, rocket-af, plato, empa-reg, rely, carolina |
| closeness | close emulation=yes | 5 | aristotle, rocket-af, rely, elite-ii, carolina |
| closeness | close emulation=no | 13 | east-afnet4, allhat, ascot, value, transform-hf, cabana-v2, ontarget, comet, plato, paradigm-hf-seq, empa-reg, emperor-preserved-v2, life |
| confounding | |unadj-RCT| T1 (low) | 6 | transform-hf, comet, empa-reg, rely, emperor-preserved-v2, carolina |
| confounding | |unadj-RCT| T2 | 6 | east-afnet4, ascot, ontarget, plato, elite-ii, life |
| confounding | |unadj-RCT| T3 (high) | 6 | allhat, aristotle, value, cabana-v2, rocket-af, paradigm-hf-seq |
| size | N T1 (low) | 6 | paradigm-hf-seq, rely, elite-ii, emperor-preserved-v2, life, carolina |
| size | N T2 | 6 | cabana-v2, ontarget, comet, rocket-af, plato, empa-reg |
| size | N T3 (high) | 6 | east-afnet4, allhat, aristotle, ascot, value, transform-hf |

## Trial-level meta-regression of the ECG gain (ECG − base at stratum 'all')

Weighted least squares, weight = 1/(SE_base² + SE_RCT²); predictors: confounding magnitude (|unadj − RCT|), % patients with echo (post-2016 echo measure), log(1 + median code density), physiology role (1/0). Univariable slopes: permutation p (10,000 permutations of the predictor). Joint model: each predictor permuted with the others fixed (2,000 permutations). slope_per_sd = slope × SD of the predictor across trials. Negative slope = larger ECG gain with higher predictor values.

| base | half | contrast | metric | model | predictor | k | slope | slope_per_sd | perm_p |
|---|---|---|---|---|---|---|---|---|---|
| demo | full | ECG - base | absd | univariable | conf | 18 | -0.1949 | -0.0622 | 0.004 |
| demo | full | ECG - base | absd | univariable | pct_echo | 18 | 0.0004 | 0.0057 | 0.778 |
| demo | full | ECG - base | absd | univariable | log_density | 18 | -0.0112 | -0.0045 | 0.827 |
| demo | full | ECG - base | absd | univariable | physiology | 18 | -0.0553 | -0.0275 | 0.171 |
| demo | full | ECG - base | absd | joint (4 predictors) | conf | 18 | -0.1587 | -0.0507 | 0.035 |
| demo | full | ECG - base | absd | joint (4 predictors) | pct_echo | 18 | 0.0039 | 0.0544 | 0.004 |
| demo | full | ECG - base | absd | joint (4 predictors) | log_density | 18 | -0.0338 | -0.0135 | 0.464 |
| demo | full | ECG - base | absd | joint (4 predictors) | physiology | 18 | -0.1149 | -0.0571 | 0.006 |
| demo | full | ECG - base | z2 | univariable | conf | 18 | -16.6442 | -5.3139 | <0.001 |
| demo | full | ECG - base | z2 | univariable | pct_echo | 18 | 0.0148 | 0.2070 | 0.911 |
| demo | full | ECG - base | z2 | univariable | log_density | 18 | -1.5048 | -0.5997 | 0.766 |
| demo | full | ECG - base | z2 | univariable | physiology | 18 | -3.7810 | -1.8788 | 0.237 |
| demo | full | ECG - base | z2 | joint (4 predictors) | conf | 18 | -14.3936 | -4.5954 | 0.002 |
| demo | full | ECG - base | z2 | joint (4 predictors) | pct_echo | 18 | 0.3080 | 4.2977 | <0.001 |
| demo | full | ECG - base | z2 | joint (4 predictors) | log_density | 18 | -6.0239 | -2.4005 | 0.024 |
| demo | full | ECG - base | z2 | joint (4 predictors) | physiology | 18 | -5.9531 | -2.9581 | 0.012 |
| demo | full | ECG - base | mean_smd | univariable | conf | 18 | -0.0172 | -0.0055 | 0.112 |
| demo | full | ECG - base | mean_smd | univariable | pct_echo | 18 | -0.0003 | -0.0044 | 0.171 |
| demo | full | ECG - base | mean_smd | univariable | log_density | 18 | -0.0084 | -0.0034 | 0.285 |
| demo | full | ECG - base | mean_smd | univariable | physiology | 18 | -0.0039 | -0.0020 | 0.544 |
| demo | full | ECG - base | mean_smd | joint (4 predictors) | conf | 18 | -0.0230 | -0.0073 | 0.093 |
| demo | full | ECG - base | mean_smd | joint (4 predictors) | pct_echo | 18 | -0.0007 | -0.0091 | 0.015 |
| demo | full | ECG - base | mean_smd | joint (4 predictors) | log_density | 18 | 0.0036 | 0.0014 | 0.705 |
| demo | full | ECG - base | mean_smd | joint (4 predictors) | physiology | 18 | 0.0080 | 0.0040 | 0.303 |
| demo | full | ECG - base | cstat | univariable | conf | 18 | -0.0206 | -0.0066 | 0.227 |
| demo | full | ECG - base | cstat | univariable | pct_echo | 18 | -0.0004 | -0.0053 | 0.332 |
| demo | full | ECG - base | cstat | univariable | log_density | 18 | -0.0171 | -0.0068 | 0.201 |
| demo | full | ECG - base | cstat | univariable | physiology | 18 | -0.0200 | -0.0100 | 0.040 |
| demo | full | ECG - base | cstat | joint (4 predictors) | conf | 18 | -0.0169 | -0.0054 | 0.317 |
| demo | full | ECG - base | cstat | joint (4 predictors) | pct_echo | 18 | 0.0006 | 0.0089 | 0.058 |
| demo | full | ECG - base | cstat | joint (4 predictors) | log_density | 18 | -0.0211 | -0.0084 | 0.068 |
| demo | full | ECG - base | cstat | joint (4 predictors) | physiology | 18 | -0.0182 | -0.0090 | 0.057 |
| sparse | full | ECG - base | absd | univariable | conf | 18 | -0.1175 | -0.0375 | 0.003 |
| sparse | full | ECG - base | absd | univariable | pct_echo | 18 | -0.0002 | -0.0021 | 0.776 |
| sparse | full | ECG - base | absd | univariable | log_density | 18 | -0.0064 | -0.0026 | 0.729 |
| sparse | full | ECG - base | absd | univariable | physiology | 18 | -0.0028 | -0.0014 | 0.843 |
| sparse | full | ECG - base | absd | joint (4 predictors) | conf | 18 | -0.1238 | -0.0395 | 0.008 |
| sparse | full | ECG - base | absd | joint (4 predictors) | pct_echo | 18 | -0.0005 | -0.0075 | 0.292 |
| sparse | full | ECG - base | absd | joint (4 predictors) | log_density | 18 | -0.0067 | -0.0027 | 0.716 |
| sparse | full | ECG - base | absd | joint (4 predictors) | physiology | 18 | 0.0152 | 0.0075 | 0.330 |
| sparse | full | ECG - base | z2 | univariable | conf | 18 | -8.1217 | -2.5930 | <0.001 |
| sparse | full | ECG - base | z2 | univariable | pct_echo | 18 | 0.0345 | 0.4817 | 0.427 |
| sparse | full | ECG - base | z2 | univariable | log_density | 18 | 0.8404 | 0.3349 | 0.581 |
| sparse | full | ECG - base | z2 | univariable | physiology | 18 | -0.0773 | -0.0384 | 0.949 |
| sparse | full | ECG - base | z2 | joint (4 predictors) | conf | 18 | -7.7424 | -2.4719 | <0.001 |
| sparse | full | ECG - base | z2 | joint (4 predictors) | pct_echo | 18 | 0.0159 | 0.2212 | 0.611 |
| sparse | full | ECG - base | z2 | joint (4 predictors) | log_density | 18 | 1.3287 | 0.5295 | 0.214 |
| sparse | full | ECG - base | z2 | joint (4 predictors) | physiology | 18 | -1.3474 | -0.6695 | 0.141 |
| sparse | full | ECG - base | mean_smd | univariable | conf | 18 | 0.0013 | 0.0004 | 0.880 |
| sparse | full | ECG - base | mean_smd | univariable | pct_echo | 18 | -0.0004 | -0.0059 | 0.114 |
| sparse | full | ECG - base | mean_smd | univariable | log_density | 18 | -0.0105 | -0.0042 | 0.324 |
| sparse | full | ECG - base | mean_smd | univariable | physiology | 18 | -0.0107 | -0.0053 | 0.085 |
| sparse | full | ECG - base | mean_smd | joint (4 predictors) | conf | 18 | -0.0028 | -0.0009 | 0.757 |
| sparse | full | ECG - base | mean_smd | joint (4 predictors) | pct_echo | 18 | -0.0009 | -0.0124 | 0.002 |
| sparse | full | ECG - base | mean_smd | joint (4 predictors) | log_density | 18 | 0.0234 | 0.0093 | 0.008 |
| sparse | full | ECG - base | mean_smd | joint (4 predictors) | physiology | 18 | -0.0089 | -0.0044 | 0.285 |
| sparse | full | ECG - base | cstat | univariable | conf | 18 | -0.0087 | -0.0028 | 0.657 |
| sparse | full | ECG - base | cstat | univariable | pct_echo | 18 | -0.0007 | -0.0097 | 0.193 |
| sparse | full | ECG - base | cstat | univariable | log_density | 18 | -0.0255 | -0.0101 | 0.176 |
| sparse | full | ECG - base | cstat | univariable | physiology | 18 | -0.0283 | -0.0140 | 0.021 |
| sparse | full | ECG - base | cstat | joint (4 predictors) | conf | 18 | -0.0072 | -0.0023 | 0.705 |
| sparse | full | ECG - base | cstat | joint (4 predictors) | pct_echo | 18 | 0.0001 | 0.0019 | 0.764 |
| sparse | full | ECG - base | cstat | joint (4 predictors) | log_density | 18 | -0.0082 | -0.0033 | 0.632 |
| sparse | full | ECG - base | cstat | joint (4 predictors) | physiology | 18 | -0.0251 | -0.0125 | 0.046 |

Placebo control: the same univariable regressions for shufECG − base and noise32 − base (2,000 permutations). A slope that also appears for the placebos reflects the base arm's error, not ECG information.

| base | half | contrast | metric | model | predictor | k | slope | slope_per_sd | perm_p |
|---|---|---|---|---|---|---|---|---|---|
| demo | full | shufECG - base | absd | univariable | conf | 18 | 0.0937 | 0.0299 | 0.020 |
| demo | full | shufECG - base | absd | univariable | pct_echo | 18 | 0.0007 | 0.0097 | 0.444 |
| demo | full | shufECG - base | absd | univariable | log_density | 18 | 0.0282 | 0.0112 | 0.379 |
| demo | full | shufECG - base | absd | univariable | physiology | 18 | 0.0402 | 0.0200 | 0.070 |
| demo | full | shufECG - base | z2 | univariable | conf | 18 | 8.3768 | 2.6744 | 0.082 |
| demo | full | shufECG - base | z2 | univariable | pct_echo | 18 | 0.0900 | 1.2554 | 0.425 |
| demo | full | shufECG - base | z2 | univariable | log_density | 18 | 4.8030 | 1.9140 | 0.175 |
| demo | full | shufECG - base | z2 | univariable | physiology | 18 | 4.8195 | 2.3948 | 0.026 |
| demo | full | shufECG - base | mean_smd | univariable | conf | 18 | 0.0031 | 0.0010 | 0.727 |
| demo | full | shufECG - base | mean_smd | univariable | pct_echo | 18 | 0.0002 | 0.0032 | 0.308 |
| demo | full | shufECG - base | mean_smd | univariable | log_density | 18 | 0.0127 | 0.0051 | 0.082 |
| demo | full | shufECG - base | mean_smd | univariable | physiology | 18 | 0.0102 | 0.0051 | 0.088 |
| demo | full | shufECG - base | cstat | univariable | conf | 18 | 0.0020 | 0.0006 | 0.764 |
| demo | full | shufECG - base | cstat | univariable | pct_echo | 18 | 0.0003 | 0.0043 | 0.074 |
| demo | full | shufECG - base | cstat | univariable | log_density | 18 | 0.0120 | 0.0048 | 0.045 |
| demo | full | shufECG - base | cstat | univariable | physiology | 18 | 0.0087 | 0.0043 | 0.060 |
| demo | full | noise - base | absd | univariable | conf | 18 | 0.0964 | 0.0308 | 0.034 |
| demo | full | noise - base | absd | univariable | pct_echo | 18 | 0.0013 | 0.0176 | 0.224 |
| demo | full | noise - base | absd | univariable | log_density | 18 | 0.0401 | 0.0160 | 0.267 |
| demo | full | noise - base | absd | univariable | physiology | 18 | 0.0366 | 0.0182 | 0.195 |
| demo | full | noise - base | z2 | univariable | conf | 18 | 8.7196 | 2.7839 | 0.084 |
| demo | full | noise - base | z2 | univariable | pct_echo | 18 | 0.0806 | 1.1251 | 0.550 |
| demo | full | noise - base | z2 | univariable | log_density | 18 | 4.8281 | 1.9240 | 0.251 |
| demo | full | noise - base | z2 | univariable | physiology | 18 | 4.3802 | 2.1765 | 0.144 |
| demo | full | noise - base | mean_smd | univariable | conf | 18 | 0.0056 | 0.0018 | 0.553 |
| demo | full | noise - base | mean_smd | univariable | pct_echo | 18 | 0.0002 | 0.0034 | 0.429 |
| demo | full | noise - base | mean_smd | univariable | log_density | 18 | 0.0118 | 0.0047 | 0.273 |
| demo | full | noise - base | mean_smd | univariable | physiology | 18 | 0.0097 | 0.0048 | 0.324 |
| demo | full | noise - base | cstat | univariable | conf | 18 | 0.0048 | 0.0015 | 0.546 |
| demo | full | noise - base | cstat | univariable | pct_echo | 18 | 0.0001 | 0.0017 | 0.641 |
| demo | full | noise - base | cstat | univariable | log_density | 18 | 0.0085 | 0.0034 | 0.284 |
| demo | full | noise - base | cstat | univariable | physiology | 18 | 0.0090 | 0.0045 | 0.088 |
| sparse | full | shufECG - base | absd | univariable | conf | 18 | -0.0721 | -0.0230 | 0.014 |
| sparse | full | shufECG - base | absd | univariable | pct_echo | 18 | 0.0011 | 0.0156 | 0.089 |
| sparse | full | shufECG - base | absd | univariable | log_density | 18 | 0.0332 | 0.0132 | 0.131 |
| sparse | full | shufECG - base | absd | univariable | physiology | 18 | 0.0224 | 0.0111 | 0.211 |
| sparse | full | shufECG - base | z2 | univariable | conf | 18 | -3.9329 | -1.2556 | 0.021 |
| sparse | full | shufECG - base | z2 | univariable | pct_echo | 18 | 0.0467 | 0.6518 | 0.362 |
| sparse | full | shufECG - base | z2 | univariable | log_density | 18 | 1.8352 | 0.7313 | 0.300 |
| sparse | full | shufECG - base | z2 | univariable | physiology | 18 | 1.3709 | 0.6812 | 0.333 |
| sparse | full | shufECG - base | mean_smd | univariable | conf | 18 | -0.0061 | -0.0019 | 0.398 |
| sparse | full | shufECG - base | mean_smd | univariable | pct_echo | 18 | -0.0002 | -0.0024 | 0.216 |
| sparse | full | shufECG - base | mean_smd | univariable | log_density | 18 | -0.0054 | -0.0021 | 0.279 |
| sparse | full | shufECG - base | mean_smd | univariable | physiology | 18 | -0.0037 | -0.0018 | 0.344 |
| sparse | full | shufECG - base | cstat | univariable | conf | 18 | -0.0100 | -0.0032 | 0.189 |
| sparse | full | shufECG - base | cstat | univariable | pct_echo | 18 | -0.0001 | -0.0011 | 0.634 |
| sparse | full | shufECG - base | cstat | univariable | log_density | 18 | -0.0013 | -0.0005 | 0.819 |
| sparse | full | shufECG - base | cstat | univariable | physiology | 18 | 0.0037 | 0.0018 | 0.397 |
| sparse | full | noise - base | absd | univariable | conf | 18 | -0.0592 | -0.0189 | 0.113 |
| sparse | full | noise - base | absd | univariable | pct_echo | 18 | 0.0002 | 0.0034 | 0.744 |
| sparse | full | noise - base | absd | univariable | log_density | 18 | 0.0219 | 0.0087 | 0.420 |
| sparse | full | noise - base | absd | univariable | physiology | 18 | 0.0240 | 0.0119 | 0.251 |
| sparse | full | noise - base | z2 | univariable | conf | 18 | -1.6871 | -0.5386 | 0.377 |
| sparse | full | noise - base | z2 | univariable | pct_echo | 18 | 0.0380 | 0.5297 | 0.519 |
| sparse | full | noise - base | z2 | univariable | log_density | 18 | 2.0979 | 0.8360 | 0.324 |
| sparse | full | noise - base | z2 | univariable | physiology | 18 | 1.8997 | 0.9440 | 0.285 |
| sparse | full | noise - base | mean_smd | univariable | conf | 18 | -0.0070 | -0.0022 | 0.283 |
| sparse | full | noise - base | mean_smd | univariable | pct_echo | 18 | -0.0001 | -0.0009 | 0.633 |
| sparse | full | noise - base | mean_smd | univariable | log_density | 18 | -0.0010 | -0.0004 | 0.822 |
| sparse | full | noise - base | mean_smd | univariable | physiology | 18 | 0.0018 | 0.0009 | 0.601 |
| sparse | full | noise - base | cstat | univariable | conf | 18 | -0.0141 | -0.0045 | 0.117 |
| sparse | full | noise - base | cstat | univariable | pct_echo | 18 | 0.0001 | 0.0008 | 0.815 |
| sparse | full | noise - base | cstat | univariable | log_density | 18 | -0.0020 | -0.0008 | 0.810 |
| sparse | full | noise - base | cstat | univariable | physiology | 18 | 0.0003 | 0.0001 | 0.979 |

Half A / half B replication of the meta-regression (ECG − base):

| base | half | contrast | metric | model | predictor | k | slope | slope_per_sd | perm_p |
|---|---|---|---|---|---|---|---|---|---|
| demo | A | ECG - base | absd | univariable | conf | 18 | -0.1979 | -0.0632 | 0.007 |
| demo | A | ECG - base | absd | univariable | pct_echo | 18 | -0.0007 | -0.0096 | 0.722 |
| demo | A | ECG - base | absd | univariable | log_density | 18 | -0.0550 | -0.0219 | 0.409 |
| demo | A | ECG - base | absd | univariable | physiology | 18 | -0.0743 | -0.0369 | 0.078 |
| demo | A | ECG - base | absd | joint (4 predictors) | conf | 18 | -0.1685 | -0.0538 | 0.062 |
| demo | A | ECG - base | absd | joint (4 predictors) | pct_echo | 18 | 0.0059 | 0.0819 | <0.001 |
| demo | A | ECG - base | absd | joint (4 predictors) | log_density | 18 | -0.1711 | -0.0682 | <0.001 |
| demo | A | ECG - base | absd | joint (4 predictors) | physiology | 18 | -0.0743 | -0.0369 | 0.046 |
| demo | A | ECG - base | z2 | univariable | conf | 18 | -15.3839 | -4.9115 | 0.003 |
| demo | A | ECG - base | z2 | univariable | pct_echo | 18 | -0.0218 | -0.3049 | 0.889 |
| demo | A | ECG - base | z2 | univariable | log_density | 18 | -3.0586 | -1.2188 | 0.587 |
| demo | A | ECG - base | z2 | univariable | physiology | 18 | -4.2395 | -2.1066 | 0.199 |
| demo | A | ECG - base | z2 | joint (4 predictors) | conf | 18 | -13.3695 | -4.2684 | 0.030 |
| demo | A | ECG - base | z2 | joint (4 predictors) | pct_echo | 18 | 0.4277 | 5.9681 | <0.001 |
| demo | A | ECG - base | z2 | joint (4 predictors) | log_density | 18 | -12.8025 | -5.1018 | <0.001 |
| demo | A | ECG - base | z2 | joint (4 predictors) | physiology | 18 | -3.9658 | -1.9706 | 0.119 |
| demo | A | ECG - base | mean_smd | univariable | conf | 18 | -0.0208 | -0.0066 | 0.127 |
| demo | A | ECG - base | mean_smd | univariable | pct_echo | 18 | -0.0005 | -0.0073 | 0.050 |
| demo | A | ECG - base | mean_smd | univariable | log_density | 18 | -0.0141 | -0.0056 | 0.119 |
| demo | A | ECG - base | mean_smd | univariable | physiology | 18 | -0.0077 | -0.0038 | 0.288 |
| demo | A | ECG - base | mean_smd | joint (4 predictors) | conf | 18 | -0.0289 | -0.0092 | 0.048 |
| demo | A | ECG - base | mean_smd | joint (4 predictors) | pct_echo | 18 | -0.0010 | -0.0144 | <0.001 |
| demo | A | ECG - base | mean_smd | joint (4 predictors) | log_density | 18 | 0.0061 | 0.0024 | 0.480 |
| demo | A | ECG - base | mean_smd | joint (4 predictors) | physiology | 18 | 0.0114 | 0.0057 | 0.095 |
| demo | A | ECG - base | cstat | univariable | conf | 18 | -0.0446 | -0.0142 | 0.162 |
| demo | A | ECG - base | cstat | univariable | pct_echo | 18 | -0.0006 | -0.0077 | 0.496 |
| demo | A | ECG - base | cstat | univariable | log_density | 18 | -0.0300 | -0.0119 | 0.274 |
| demo | A | ECG - base | cstat | univariable | physiology | 18 | -0.0333 | -0.0166 | 0.064 |
| demo | A | ECG - base | cstat | joint (4 predictors) | conf | 18 | -0.0352 | -0.0112 | 0.277 |
| demo | A | ECG - base | cstat | joint (4 predictors) | pct_echo | 18 | 0.0022 | 0.0307 | <0.001 |
| demo | A | ECG - base | cstat | joint (4 predictors) | log_density | 18 | -0.0751 | -0.0299 | <0.001 |
| demo | A | ECG - base | cstat | joint (4 predictors) | physiology | 18 | -0.0251 | -0.0125 | 0.183 |
| demo | B | ECG - base | absd | univariable | conf | 18 | -0.2358 | -0.0753 | 0.024 |
| demo | B | ECG - base | absd | univariable | pct_echo | 18 | -0.0017 | -0.0240 | 0.494 |
| demo | B | ECG - base | absd | univariable | log_density | 18 | -0.0902 | -0.0359 | 0.300 |
| demo | B | ECG - base | absd | univariable | physiology | 18 | -0.1227 | -0.0610 | 0.058 |
| demo | B | ECG - base | absd | joint (4 predictors) | conf | 18 | -0.2032 | -0.0649 | 0.059 |
| demo | B | ECG - base | absd | joint (4 predictors) | pct_echo | 18 | 0.0057 | 0.0792 | 0.009 |
| demo | B | ECG - base | absd | joint (4 predictors) | log_density | 18 | -0.1515 | -0.0604 | 0.052 |
| demo | B | ECG - base | absd | joint (4 predictors) | physiology | 18 | -0.1335 | -0.0663 | 0.037 |
| demo | B | ECG - base | z2 | univariable | conf | 18 | -12.5867 | -4.0185 | 0.056 |
| demo | B | ECG - base | z2 | univariable | pct_echo | 18 | -0.1162 | -1.6209 | 0.490 |
| demo | B | ECG - base | z2 | univariable | log_density | 18 | -5.5574 | -2.2146 | 0.345 |
| demo | B | ECG - base | z2 | univariable | physiology | 18 | -6.8786 | -3.4180 | 0.115 |
| demo | B | ECG - base | z2 | joint (4 predictors) | conf | 18 | -11.1485 | -3.5593 | 0.117 |
| demo | B | ECG - base | z2 | joint (4 predictors) | pct_echo | 18 | 0.2796 | 3.9010 | 0.078 |
| demo | B | ECG - base | z2 | joint (4 predictors) | log_density | 18 | -8.7735 | -3.4963 | 0.128 |
| demo | B | ECG - base | z2 | joint (4 predictors) | physiology | 18 | -6.3854 | -3.1730 | 0.207 |
| demo | B | ECG - base | mean_smd | univariable | conf | 18 | -0.0078 | -0.0025 | 0.694 |
| demo | B | ECG - base | mean_smd | univariable | pct_echo | 18 | -0.0009 | -0.0119 | 0.012 |
| demo | B | ECG - base | mean_smd | univariable | log_density | 18 | -0.0304 | -0.0121 | 0.012 |
| demo | B | ECG - base | mean_smd | univariable | physiology | 18 | -0.0218 | -0.0108 | 0.030 |
| demo | B | ECG - base | mean_smd | joint (4 predictors) | conf | 18 | -0.0118 | -0.0038 | 0.320 |
| demo | B | ECG - base | mean_smd | joint (4 predictors) | pct_echo | 18 | 0.0002 | 0.0027 | 0.418 |
| demo | B | ECG - base | mean_smd | joint (4 predictors) | log_density | 18 | -0.0418 | -0.0167 | <0.001 |
| demo | B | ECG - base | mean_smd | joint (4 predictors) | physiology | 18 | 0.0061 | 0.0030 | 0.376 |
| demo | B | ECG - base | cstat | univariable | conf | 18 | -0.0050 | -0.0016 | 0.824 |
| demo | B | ECG - base | cstat | univariable | pct_echo | 18 | -0.0009 | -0.0131 | 0.127 |
| demo | B | ECG - base | cstat | univariable | log_density | 18 | -0.0379 | -0.0151 | 0.068 |
| demo | B | ECG - base | cstat | univariable | physiology | 18 | -0.0362 | -0.0180 | 0.016 |
| demo | B | ECG - base | cstat | joint (4 predictors) | conf | 18 | -0.0016 | -0.0005 | 0.953 |
| demo | B | ECG - base | cstat | joint (4 predictors) | pct_echo | 18 | 0.0012 | 0.0170 | 0.008 |
| demo | B | ECG - base | cstat | joint (4 predictors) | log_density | 18 | -0.0574 | -0.0229 | <0.001 |
| demo | B | ECG - base | cstat | joint (4 predictors) | physiology | 18 | -0.0199 | -0.0099 | 0.159 |
| sparse | A | ECG - base | absd | univariable | conf | 18 | -0.0557 | -0.0178 | 0.278 |
| sparse | A | ECG - base | absd | univariable | pct_echo | 18 | 0.0016 | 0.0217 | 0.193 |
| sparse | A | ECG - base | absd | univariable | log_density | 18 | 0.0235 | 0.0094 | 0.583 |
| sparse | A | ECG - base | absd | univariable | physiology | 18 | 0.0042 | 0.0021 | 0.899 |
| sparse | A | ECG - base | absd | joint (4 predictors) | conf | 18 | -0.0199 | -0.0063 | 0.785 |
| sparse | A | ECG - base | absd | joint (4 predictors) | pct_echo | 18 | 0.0062 | 0.0864 | <0.001 |
| sparse | A | ECG - base | absd | joint (4 predictors) | log_density | 18 | -0.1323 | -0.0527 | 0.004 |
| sparse | A | ECG - base | absd | joint (4 predictors) | physiology | 18 | -0.0327 | -0.0162 | 0.429 |
| sparse | A | ECG - base | z2 | univariable | conf | 18 | -7.0988 | -2.2664 | 0.015 |
| sparse | A | ECG - base | z2 | univariable | pct_echo | 18 | 0.0778 | 1.0852 | 0.427 |
| sparse | A | ECG - base | z2 | univariable | log_density | 18 | 2.2048 | 0.8786 | 0.579 |
| sparse | A | ECG - base | z2 | univariable | physiology | 18 | 1.0327 | 0.5132 | 0.901 |
| sparse | A | ECG - base | z2 | joint (4 predictors) | conf | 18 | -6.3881 | -2.0395 | 0.074 |
| sparse | A | ECG - base | z2 | joint (4 predictors) | pct_echo | 18 | 0.0506 | 0.7062 | 0.629 |
| sparse | A | ECG - base | z2 | joint (4 predictors) | log_density | 18 | 1.8416 | 0.7339 | 0.640 |
| sparse | A | ECG - base | z2 | joint (4 predictors) | physiology | 18 | -1.4674 | -0.7292 | 0.680 |
| sparse | A | ECG - base | mean_smd | univariable | conf | 18 | -0.0057 | -0.0018 | 0.617 |
| sparse | A | ECG - base | mean_smd | univariable | pct_echo | 18 | -0.0003 | -0.0040 | 0.267 |
| sparse | A | ECG - base | mean_smd | univariable | log_density | 18 | -0.0096 | -0.0038 | 0.289 |
| sparse | A | ECG - base | mean_smd | univariable | physiology | 18 | -0.0071 | -0.0035 | 0.317 |
| sparse | A | ECG - base | mean_smd | joint (4 predictors) | conf | 18 | -0.0077 | -0.0025 | 0.574 |
| sparse | A | ECG - base | mean_smd | joint (4 predictors) | pct_echo | 18 | -0.0001 | -0.0018 | 0.676 |
| sparse | A | ECG - base | mean_smd | joint (4 predictors) | log_density | 18 | -0.0077 | -0.0031 | 0.463 |
| sparse | A | ECG - base | mean_smd | joint (4 predictors) | physiology | 18 | 0.0020 | 0.0010 | 0.835 |
| sparse | A | ECG - base | cstat | univariable | conf | 18 | -0.0165 | -0.0053 | 0.403 |
| sparse | A | ECG - base | cstat | univariable | pct_echo | 18 | -0.0006 | -0.0080 | 0.231 |
| sparse | A | ECG - base | cstat | univariable | log_density | 18 | -0.0237 | -0.0094 | 0.150 |
| sparse | A | ECG - base | cstat | univariable | physiology | 18 | -0.0313 | -0.0156 | 0.004 |
| sparse | A | ECG - base | cstat | joint (4 predictors) | conf | 18 | -0.0094 | -0.0030 | 0.578 |
| sparse | A | ECG - base | cstat | joint (4 predictors) | pct_echo | 18 | 0.0007 | 0.0093 | 0.059 |
| sparse | A | ECG - base | cstat | joint (4 predictors) | log_density | 18 | -0.0098 | -0.0039 | 0.440 |
| sparse | A | ECG - base | cstat | joint (4 predictors) | physiology | 18 | -0.0387 | -0.0192 | <0.001 |
| sparse | B | ECG - base | absd | univariable | conf | 18 | -0.0835 | -0.0267 | 0.188 |
| sparse | B | ECG - base | absd | univariable | pct_echo | 18 | -0.0016 | -0.0228 | 0.136 |
| sparse | B | ECG - base | absd | univariable | log_density | 18 | -0.0455 | -0.0181 | 0.224 |
| sparse | B | ECG - base | absd | univariable | physiology | 18 | -0.0332 | -0.0165 | 0.267 |
| sparse | B | ECG - base | absd | joint (4 predictors) | conf | 18 | -0.1008 | -0.0322 | 0.175 |
| sparse | B | ECG - base | absd | joint (4 predictors) | pct_echo | 18 | -0.0029 | -0.0405 | 0.024 |
| sparse | B | ECG - base | absd | joint (4 predictors) | log_density | 18 | 0.0285 | 0.0114 | 0.497 |
| sparse | B | ECG - base | absd | joint (4 predictors) | physiology | 18 | 0.0122 | 0.0061 | 0.723 |
| sparse | B | ECG - base | z2 | univariable | conf | 18 | -5.0446 | -1.6105 | 0.014 |
| sparse | B | ECG - base | z2 | univariable | pct_echo | 18 | -0.0215 | -0.2994 | 0.450 |
| sparse | B | ECG - base | z2 | univariable | log_density | 18 | -0.6950 | -0.2770 | 0.478 |
| sparse | B | ECG - base | z2 | univariable | physiology | 18 | -0.6521 | -0.3241 | 0.406 |
| sparse | B | ECG - base | z2 | joint (4 predictors) | conf | 18 | -5.2942 | -1.6902 | 0.019 |
| sparse | B | ECG - base | z2 | joint (4 predictors) | pct_echo | 18 | -0.0411 | -0.5732 | 0.238 |
| sparse | B | ECG - base | z2 | joint (4 predictors) | log_density | 18 | 0.3035 | 0.1209 | 0.819 |
| sparse | B | ECG - base | z2 | joint (4 predictors) | physiology | 18 | 0.1421 | 0.0706 | 0.898 |
| sparse | B | ECG - base | mean_smd | univariable | conf | 18 | 0.0071 | 0.0023 | 0.465 |
| sparse | B | ECG - base | mean_smd | univariable | pct_echo | 18 | -0.0004 | -0.0054 | 0.130 |
| sparse | B | ECG - base | mean_smd | univariable | log_density | 18 | -0.0111 | -0.0044 | 0.224 |
| sparse | B | ECG - base | mean_smd | univariable | physiology | 18 | -0.0122 | -0.0061 | 0.045 |
| sparse | B | ECG - base | mean_smd | joint (4 predictors) | conf | 18 | 0.0064 | 0.0021 | 0.531 |
| sparse | B | ECG - base | mean_smd | joint (4 predictors) | pct_echo | 18 | -0.0005 | -0.0072 | 0.067 |
| sparse | B | ECG - base | mean_smd | joint (4 predictors) | log_density | 18 | 0.0152 | 0.0061 | 0.112 |
| sparse | B | ECG - base | mean_smd | joint (4 predictors) | physiology | 18 | -0.0125 | -0.0062 | 0.092 |
| sparse | B | ECG - base | cstat | univariable | conf | 18 | -0.0075 | -0.0024 | 0.692 |
| sparse | B | ECG - base | cstat | univariable | pct_echo | 18 | -0.0006 | -0.0077 | 0.277 |
| sparse | B | ECG - base | cstat | univariable | log_density | 18 | -0.0215 | -0.0086 | 0.221 |
| sparse | B | ECG - base | cstat | univariable | physiology | 18 | -0.0286 | -0.0142 | 0.004 |
| sparse | B | ECG - base | cstat | joint (4 predictors) | conf | 18 | -0.0016 | -0.0005 | 0.918 |
| sparse | B | ECG - base | cstat | joint (4 predictors) | pct_echo | 18 | 0.0004 | 0.0060 | 0.353 |
| sparse | B | ECG - base | cstat | joint (4 predictors) | log_density | 18 | -0.0039 | -0.0016 | 0.819 |
| sparse | B | ECG - base | cstat | joint (4 predictors) | physiology | 18 | -0.0353 | -0.0175 | 0.007 |

## Stratum coverage per trial (% of trial cohort in each stratum)

| trial | n | pct_lag_known | pct_inpatient | pct_echo | median_density | pct:lag<=365 (all) | pct:lag<=90 | pct:lag<=30 | pct:echo=yes | pct:echo=no | pct:density=T1 (low) | pct:density=T2 | pct:density=T3 (high) | pct:age<65 | pct:age>=65 | pct:sex=female | pct:sex=male | pct:setting=outpatient | pct:setting=inpatient | confounding |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| east-afnet4 | 16109 | 100.0 | 55.7 | 49.2 | 106.0 | 100.0 | 86.5 | 76.5 | 49.2 | 50.8 | 33.8 | 33.0 | 33.2 | 25.2 | 74.8 | 46.9 | 53.1 | 44.3 | 55.7 | 0.3 |
| allhat | 26592 | 100.0 | 32.4 | 19.4 | 40.0 | 100.0 | 78.8 | 69.3 | 19.4 | 80.6 | 33.9 | 33.3 | 32.8 | 31.2 | 68.8 | 53.0 | 47.0 | 67.6 | 32.4 | 0.3 |
| aristotle | 18771 | 100.0 | 51.3 | 42.3 | 72.0 | 100.0 | 87.9 | 81.1 | 42.3 | 57.7 | 33.3 | 33.8 | 32.9 | 21.3 | 78.7 | 43.9 | 56.1 | 48.7 | 51.3 | 0.3 |
| ascot | 26021 | 100.0 | 31.9 | 17.7 | 37.0 | 100.0 | 80.2 | 70.9 | 17.7 | 82.3 | 33.5 | 33.4 | 33.1 | 56.8 | 43.2 | 50.3 | 49.7 | 68.1 | 31.9 | 0.1 |
| value | 26657 | 100.0 | 26.3 | 17.6 | 36.0 | 100.0 | 76.5 | 66.9 | 17.6 | 82.4 | 33.6 | 33.2 | 33.2 | 40.4 | 59.6 | 52.3 | 47.7 | 73.7 | 26.3 | 0.4 |
| transform-hf | 15657 | 100.0 | 75.5 | 39.9 | 87.0 | 100.0 | 93.9 | 90.5 | 39.9 | 60.1 | 33.8 | 33.0 | 33.2 | 25.1 | 74.9 | 49.1 | 50.9 | 24.5 | 75.5 | 0.1 |
| cabana-v2 | 13133 | 100.0 | 64.0 | 50.0 | 97.0 | 100.0 | 90.7 | 83.6 | 50.0 | 50.0 | 33.9 | 33.0 | 33.1 | 28.6 | 71.4 | 40.3 | 59.7 | 36.0 | 64.0 | 1.4 |
| ontarget | 14853 | 100.0 | 33.5 | 21.7 | 37.0 | 100.0 | 78.1 | 69.3 | 21.7 | 78.3 | 33.7 | 33.3 | 33.0 | 32.0 | 68.0 | 45.9 | 54.1 | 66.5 | 33.5 | 0.2 |
| comet | 6381 | 100.0 | 61.0 | 59.8 | 112.0 | 100.0 | 90.0 | 81.0 | 59.8 | 40.2 | 33.4 | 33.6 | 32.9 | 40.2 | 59.8 | 38.5 | 61.5 | 39.0 | 61.0 | 0.1 |
| rocket-af | 7055 | 100.0 | 48.5 | 29.8 | 63.0 | 100.0 | 85.4 | 77.5 | 29.8 | 70.2 | 33.5 | 33.4 | 33.1 | 25.1 | 74.9 | 42.0 | 58.0 | 51.5 | 48.5 | 0.6 |
| plato | 6759 | 100.0 | 86.4 | 34.1 | 66.0 | 100.0 | 97.0 | 95.7 | 34.1 | 65.9 | 33.8 | 33.3 | 32.9 | 42.3 | 57.7 | 37.1 | 62.9 | 13.6 | 86.4 | 0.2 |
| paradigm-hf-seq | 5129 | 100.0 | 38.0 | 37.8 | 98.0 | 100.0 | 75.6 | 62.3 | 37.8 | 62.2 | 33.4 | 33.5 | 33.1 | 36.8 | 63.2 | 38.6 | 61.4 | 62.0 | 38.0 | 0.4 |
| empa-reg | 5649 | 100.0 | 27.0 | 40.4 | 83.0 | 100.0 | 65.6 | 51.0 | 40.4 | 59.6 | 33.5 | 33.7 | 32.8 | 35.7 | 64.3 | 39.8 | 60.2 | 73.0 | 27.0 | 0.1 |
| rely | 4172 | 100.0 | 57.9 | 26.6 | 80.0 | 100.0 | 86.7 | 79.4 | 26.6 | 73.4 | 33.3 | 33.4 | 33.2 | 22.1 | 77.9 | 42.8 | 57.2 | 42.1 | 57.9 | 0.0 |
| elite-ii | 3222 | 100.0 | 57.4 | 27.6 | 75.0 | 100.0 | 87.4 | 80.0 | 27.6 | 72.4 | 33.8 | 32.9 | 33.3 | 14.4 | 85.6 | 43.7 | 56.3 | 42.6 | 57.4 | 0.2 |
| emperor-preserved-v2 | 2417 | 100.0 | 42.5 | 63.8 | 119.0 | 100.0 | 76.0 | 61.2 | 63.8 | 36.2 | 33.6 | 33.4 | 33.0 | 29.3 | 70.7 | 47.4 | 52.6 | 57.5 | 42.5 | 0.1 |
| life | 3131 | 100.0 | 32.1 | 24.2 | 47.0 | 100.0 | 81.9 | 71.2 | 24.2 | 75.8 | 33.8 | 33.0 | 33.3 | 42.3 | 57.7 | 56.3 | 43.7 | 67.9 | 32.1 | 0.2 |
| carolina | 1794 | 100.0 | 23.1 | 19.8 | 42.0 | 100.0 | 70.1 | 57.1 | 19.8 | 80.2 | 33.9 | 32.8 | 33.3 | 37.4 | 62.6 | 47.9 | 52.1 | 76.9 | 23.1 | 0.0 |

Skipped trial × stratum × half (either arm below the minimum size):

| stratum | half | n_trials_skipped |
|---|---|---|
| density=T3 (high) | A | 1 |
| density=T3 (high) | B | 1 |
| density=T3 (high) | full | 1 |

<!-- AUDIT -->
## Audit

- **Two-trial pre-run** (COMET, LIFE; `results_audit.csv`), stratum 'all', full cohort. The engine output reproduces `claude-v16-engine/validation_estimates.csv` exactly for:
  - sparse: |Δlog HR| = 0, |Δmean SMD| = 0, |ΔC| = 0; matched pairs 2423 / 1239, identical to validation.
  - sparse+ECG: all differences 0; pairs 2114 / 1207.
  - unmatched: all differences 0.
- **Placebo sanity.**
  - Two-trial pre-run, per trial × base × stratum: shufECG and noise32 beat the base on mean |SMD| in 46% of cells each, versus 89% for ECG.
  - Full run: 48% / 48% for mean |SMD| versus 79% for ECG; C-statistic 42% / 47% versus 76%. The placebos do not systematically beat the base.
  - In the summaries, the ECG-vs-placebo differences are close to the ECG-vs-base differences.
- **Pair counts.** The minimum matched pairs in any analysed set is 105 (full) and 30 / 36 (half A / B). The medians in the pre-run were 848 (full) and about 415 (halves). No run errors; no missing log HR or C-statistic (7,530 result rows).
- **Size rule.** The only trial × stratum skipped is RELY density T3 (one arm < 100). That stratum therefore uses 17 trials; every other row stratum uses 18.
- **Trial counts for the trial-level strata** (exact sign-flip; the minimum attainable p with 6 trials is 0.031):
  - physiology 8, control 10;
  - close emulation yes 5 (not tested, < 6), no 13;
  - confounding and size tertiles 6 each.
- **ECG lag.** Taken from each trial's `claude-<trial>-bcl*/input/restricted_selection.parquet` (`lag_days`, from `select_cohort_ecgs.py`). It is available for 100% of analysed patients (the selection window is [index − 365, index], so 'lag ≤ 365' = all). Across trials, the share with lag ≤ 30 d is 51–96% and ≤ 90 d is 66–97%.
- **Care setting.** Existing outpatient subsets (`*-baseline-op-v11`, `*-outpt`) cover only some trials and a different roster. The flag was therefore re-derived for all 18 trials with the same rule as `scripts/make_outpatient_subset.py`: inpatient if the index date falls inside an OMOP gold 9201 visit. Inpatient share among analysed patients ranges from 23% (CAROLINA) to 86% (PLATO).
- **Echo.** Echo = `T.echo_any & T.post2016`; the share is 18–64% per trial. Density tertiles are rank-based within trial; age and sex come from the completed demo covariates.
- **Halves.** Each patient split is seeded (16060 + trial index) and stratified by treatment. Strata are defined on the full cohort and then intersected with the half. The half minimum is 50 per arm.
- **Arm construction.** PCs are computed on the full trial cohort, not re-estimated within strata. shufECG is taken from the full-cohort permutation (`T.shuffle_perm`) and then subset. noise32 is `T.noise32`.
- **Multiple testing.** q is BH over the 46 tested full-cohort cells per metric. The trial-level strata re-use the 'all' runs, so they are not independent of the row strata.
<!-- /AUDIT -->
