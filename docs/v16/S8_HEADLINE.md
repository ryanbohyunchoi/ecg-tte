# v1.6 S8 headline: where adding AI-ECG moves held-out covariates below |SMD| 0.1 (2026-09-26)

Exploratory, post-hoc. Script `scripts/v16/s8_headline.py`; outputs `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s8-headline/` (`results.csv`, `grid_summary.csv`, `part2_*.csv`, `selection.json`). Aggregates only; no patient-level rows.

## Key findings

Units: "pp" = percentage points of held-out variables with |SMD| < 0.1. "Love count" = how many of the 58 variables have a median |SMD| across trials below 0.1.

1. **Where ECG moves covariates below 0.1: PS bases with thin coded data.** Full cohort, 18 trials:
   - ECG raises the per-trial % of the 58 held-out variables with |SMD| < 0.1 by about 5–9 pp in 29 of 34 cells (p < 0.05). This holds for demo, demo+race, minimal-7, common-10, sparse with 25–75% code dropout, and for every estimator and ECG-dimension variant of those bases.
   - It never gets worse at p < 0.05.
   - The placebos do nothing: shufECG − base averages +0.15 pp and noise − base +0.08 pp across the 34 cells.
   - Examples (love counts are unmatched 33 of 58):

     | base | % < 0.1, base → ECG | love count, base → ECG |
     |---|---|---|
     | demo | 53.8 → 60.2 | 32 → 43 |
     | demo, overlap weights (18/18 trials improved) | 53.8 → 61.8 | 35 → 45 |
     | minimal-7 | 53.1 → 59.8 | 27 → 40 |
     | sparse, 75% dropout | 54.3 → 61.5 | 36 → 40 |

   - With the full sparse PS, the gain is null: +0.7 pp, p = 0.69, love count 48 → 47. This is the result the PI saw.
   - With hdPS the gain is small and does not replicate across halves: hdPS200 +4.5 pp, p = 0.012, love count 46 → 53, but half A p = 0.60.

2. **Pre-specified selection (half A only, committed before half B / full were computed).**
   - The rule picked three physiology-trial (k = 8) scenarios:
     - demo with caliper 0.1: +10.1 pp, 7/8, p = 0.031
     - minimal-7: +7.8 pp, p = 0.016
     - common-10: +7.8 pp, p = 0.016
   - Half-B confirmation:
     - **common-10 confirmed**: +8.0 pp, 7/8, p = 0.016; beats shufECG (p = 0.031) and noise in direction; cluster p = 0.031, LOO max p = 0.031.
     - demo caliper 0.1 is borderline: +7.8 pp, p = 0.047, but the placebo contrasts are not significant.
     - minimal-7 is **not confirmed**: +3.7 pp, p = 0.25.
   - In the full cohort (k = 8) all three are positive but not significant: p = 0.14, 0.062, 0.078. Their love counts are 25 → 38, 34 → 36 and 32 → 45 of 58.
   - This is winner's-curse shrinkage in 8-trial subsets.

3. **The 18-trial analogues replicate robustly (sensitivity; NOT the pre-selected scenarios).**
   - demo with caliper 0.1: +6.8 pp, 13/18, p < 0.001, grid q = 0.001, cluster p = 0.023, LOO max p = 0.002; half A p = 0.001, half B p = 0.004; love count 29 → 43.
   - minimal-7: +6.7 pp, p < 0.001; half B p = 0.028.
   - common-10: +6.9 pp, p < 0.001; half B p = 0.065.

   These, and demo with overlap weights / 1:3 matching and sparse at 50% dropout (significant in both halves), are the most defensible reviewer-facing headline. They are chosen post hoc from the full grid, so say so.

4. **Expanded non-ECG-proximal panel** (covars2, with the round-2 audit exclusions): the same pattern at smaller size.
   - Selected scenarios, full cohort: +4.7 to +6.6 pp, p = 0.008–0.023.
   - Sparse: +3.0 pp, p = 0.020.
   - hdPS200: null.

5. **Trial emulation: no benchmark-specific RCT gain.**
   - In the three selected scenarios, ECG lowers |Δlog HR| (0.316 → 0.233, 0.286 → 0.200, 0.229 → 0.213) and z²/φ (φ 13.3 → 6.7, 10.9 → 5.0, 8.1 → 4.9).
   - Only minimal-7 reaches p < 0.05 on |Δ| (p = 0.031), and it fails the shuffled-RCT test (p = 0.058), clustering (p = 0.062) and half-replication (A p = 0.23, B p = 0.39).
   - The z² gains are not specific to each trial's own RCT (shuffled-RCT p = 0.46–0.85): this is generic shrinkage toward the null.
   - Sparse reference: |Δ| p = 0.26; z² p = 0.024 but shuffled-RCT p = 0.80.

**Bottom line for the PI.** A defensible |SMD| < 0.1 headline is: "with a demographic or minimal PS, adding the ECG embedding moved about 10 more of 58 held-out covariates below 0.1 (for example 29 → 43, or 32 → 43 with standard caliper 0.2), replicated in both random halves, with no change from placebo embeddings." It should not be framed as closer agreement with the RCTs.

## Selection (half A only; written and committed before half-B / full confirmation)

Rule: Half A only; panel p58; metric = trial-level % of held-out variables with |SMD| < 0.1 (ECG − base, dropout cells averaged over 3 seeds). Eligible scenario = (cell, trial subset) with ECG − base gain > 0, exact sign-flip p < 0.05, and ECG − shufECG > 0 and ECG − noise > 0. Base 'none' (ECG only vs unmatched) excluded from the headline pool (it measures matching vs no matching, not ECG added to a PS); reported descriptively. Rank by gain (descending); take the top 3 with at most one scenario per base (the base's modifier variants and trial subsets compete for its slot).

Selection timestamp: **2026-09-26 23:42:00 EDT**; halves present in the results at selection: ['A']. 23 of 68 scenarios (cells × trial subsets) were eligible.

```json
[
 {
  "cell": "demo|cal0.1",
  "subset": "phys",
  "label": "demo / caliper 0.1 (physiology trials)",
  "halfA_d": 10.129310344827587,
  "halfA_k": "7/8",
  "halfA_p": 0.03125,
  "halfA_d_shuf": 10.99137931034483,
  "halfA_d_noise": 9.267241379310345,
  "halfA_base": 45.47413793103448,
  "halfA_ecg": 55.603448275862064
 },
 {
  "cell": "min7|default",
  "subset": "phys",
  "label": "minimal-7 (physiology trials)",
  "halfA_d": 7.758620689655173,
  "halfA_k": "7/8",
  "halfA_p": 0.015625,
  "halfA_d_shuf": 7.974137931034485,
  "halfA_d_noise": 4.956896551724139,
  "halfA_base": 45.04310344827586,
  "halfA_ecg": 52.80172413793103
 },
 {
  "cell": "common10|default",
  "subset": "phys",
  "label": "common-10 (physiology trials)",
  "halfA_d": 7.75862068965517,
  "halfA_k": "7/8",
  "halfA_p": 0.015625,
  "halfA_d_shuf": 5.172413793103445,
  "halfA_d_noise": 4.741379310344824,
  "halfA_base": 50.862068965517246,
  "halfA_ecg": 58.62068965517241
 }
]
```

Top eligible scenarios in half A:

| cell | subset | d_p58_pct_lt10 | k_p58_pct_lt10 | p_p58_pct_lt10 | d_shuf_p58_pct_lt10 | d_noise_p58_pct_lt10 |
|---|---|---|---|---|---|---|
| demo|cal0.1 | phys | 10.129 | 7/8 | 0.031 | 10.991 | 9.267 |
| demo|default | phys | 9.483 | 7/8 | 0.023 | 14.009 | 11.422 |
| demo|cal0.1 | all | 8.137 | 16/18 | 0.001 | 8.905 | 7.760 |
| min7|default | phys | 7.759 | 7/8 | 0.016 | 7.974 | 4.957 |
| common10|default | phys | 7.759 | 7/8 | 0.016 | 5.172 | 4.741 |
| demo|default | all | 7.658 | 16/18 | 0.001 | 10.054 | 9.006 |
| min7|cal0.1 | all | 6.508 | 13/18 | 0.007 | 7.666 | 6.129 |
| min7|pc64 | phys | 6.466 | 7/8 | 0.031 | 5.172 | 4.741 |
| demo|overlap | all | 6.130 | 15/18 | 0.001 | 6.515 | 6.418 |
| min7|default | all | 6.029 | 14/18 | 0.002 | 7.762 | 6.606 |
| demo|m1to3 | all | 5.458 | 13/18 | 0.004 | 8.043 | 6.513 |
| sparse_p75|default | all | 5.371 | 16/18 | 0.000 | 6.109 | 4.733 |
| min7|pc64 | all | 5.083 | 14/18 | 0.005 | 5.063 | 4.112 |
| common10|default | all | 4.502 | 11/18 | 0.010 | 4.500 | 2.388 |
| sparse_p50|overlap | all | 3.991 | 13/18 | 0.030 | 5.142 | 3.767 |

## Confirmation of the selected scenarios (58-panel % of variables with |SMD| < 0.1)

d = ECG − base in percentage points (mean over trials; positive = more variables below 0.1); k = trials improved; p = exact sign-flip; q = BH over the 34 cells within half × subset; cluster = sign-flip over 10 comparator clusters (k = clusters improved); LOO = max p leaving one trial out. Love = number of the 58 variables whose median |SMD| across trials is < 0.1 (unmatched / base → ECG). Expanded = claude-v16-covars2 non-ECG-proximal panel.

| scenario | half | base %<0.1 | ECG %<0.1 | d (k) | p | q (grid) | vs shuf d (p) | vs noise d (p) | cluster p (k) | LOO max p | love <0.1 unm/base→ECG | love shuf/noise | expanded d (p) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo / caliper 0.1 (physiology trials) | A | 45.5 | 55.6 | +10.1 (7/8) | 0.031 | 0.212 | +11.0 (0.016) | +9.3 (0.055) | 0.062 (6/7+) | 0.062 | 26/20→35 of 58 | 19/23 | +6.1 (0.023) |
| demo / caliper 0.1 (physiology trials) | B | 42.9 | 50.6 | +7.8 (6/8) | 0.047 | 0.133 | +5.2 (0.234) | +3.9 (0.469) | 0.094 (5/7+) | 0.094 | 23/20→31 of 58 | 24/22 | +3.8 (0.055) |
| demo / caliper 0.1 (physiology trials) | full | 55.0 | 60.3 | +5.4 (5/8) | 0.141 | 0.165 | +10.1 (0.031) | +9.3 (0.031) | 0.250 (4/7+) | 0.281 | 35/25→38 of 58 | 28/27 | +6.6 (0.016) |
| minimal-7 (physiology trials) | A | 45.0 | 52.8 | +7.8 (7/8) | 0.016 | 0.212 | +8.0 (0.023) | +5.0 (0.234) | 0.016 (7/7+) | 0.031 | 26/19→34 of 58 | 21/25 | +2.5 (0.156) |
| minimal-7 (physiology trials) | B | 46.8 | 50.4 | +3.7 (6/8) | 0.250 | 0.386 | +3.2 (0.352) | +4.5 (0.219) | 0.375 (5/7+) | 0.484 | 23/27→29 of 58 | 30/25 | +5.8 (0.016) |
| minimal-7 (physiology trials) | full | 52.6 | 59.1 | +6.5 (7/8) | 0.062 | 0.101 | +5.6 (0.172) | +5.2 (0.078) | 0.125 (6/7+) | 0.125 | 35/34→36 of 58 | 31/37 | +4.7 (0.023) |
| common-10 (physiology trials) | A | 50.9 | 58.6 | +7.8 (7/8) | 0.016 | 0.212 | +5.2 (0.047) | +4.7 (0.031) | 0.031 (6/7+) | 0.031 | 26/28→37 of 58 | 31/32 | +4.9 (0.008) |
| common-10 (physiology trials) | B | 44.8 | 52.8 | +8.0 (7/8) | 0.016 | 0.089 | +3.4 (0.031) | +4.7 (0.141) | 0.031 (6/7+) | 0.031 | 23/23→32 of 58 | 29/27 | +7.7 (0.008) |
| common-10 (physiology trials) | full | 56.7 | 64.7 | +8.0 (6/8) | 0.078 | 0.115 | +9.3 (0.031) | +5.4 (0.234) | 0.156 (5/7+) | 0.156 | 35/32→45 of 58 | 32/37 | +6.4 (0.008) |
| sparse (reference) | A | 56.6 | 59.0 | +2.4 (12/18) | 0.110 | 0.170 | +2.5 (0.148) | +1.8 (0.367) | 0.230 (8/10+) | 0.214 | 26/39→46 of 58 | 38/41 | +2.9 (0.005) |
| sparse (reference) | B | 56.4 | 58.1 | +1.7 (10/18) | 0.355 | 0.394 | +4.4 (0.028) | +4.5 (0.007) | 0.359 (6/10+) | 0.558 | 27/36→37 of 58 | 35/31 | +1.9 (0.192) |
| sparse (reference) | full | 63.4 | 64.0 | +0.7 (8/18) | 0.688 | 0.688 | +2.2 (0.158) | +0.5 (0.813) | 0.363 (6/10+) | 1.000 | 33/48→47 of 58 | 45/45 | +3.0 (0.020) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | A | 47.6 | 55.8 | +8.1 (16/18) | 0.001 | 0.008 | +8.9 (<0.001) | +7.8 (<0.001) | 0.004 (9/10+) | 0.002 | 26/20→38 of 58 | 22/22 | +6.1 (<0.001) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | B | 47.5 | 53.4 | +5.9 (12/18) | 0.004 | 0.017 | +5.7 (0.012) | +4.8 (0.047) | 0.008 (8/10+) | 0.009 | 27/24→33 of 58 | 24/27 | +4.1 (0.001) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | full | 54.2 | 61.0 | +6.8 (13/18) | <0.001 | 0.001 | +9.1 (<0.001) | +6.9 (<0.001) | 0.023 (8/10+) | 0.002 | 33/29→43 of 58 | 33/34 | +5.1 (<0.001) |
| minimal-7 (18 trials; sensitivity, not selected) | A | 49.2 | 55.2 | +6.0 (14/18) | 0.002 | 0.009 | +7.8 (<0.001) | +6.6 (0.007) | 0.021 (8/10+) | 0.003 | 26/23→39 of 58 | 22/24 | +1.7 (0.071) |
| minimal-7 (18 trials; sensitivity, not selected) | B | 50.6 | 54.8 | +4.1 (11/18) | 0.028 | 0.057 | +5.5 (0.005) | +6.1 (0.005) | 0.023 (8/10+) | 0.055 | 27/30→38 of 58 | 29/29 | +3.0 (0.006) |
| minimal-7 (18 trials; sensitivity, not selected) | full | 53.1 | 59.8 | +6.7 (15/18) | <0.001 | 0.001 | +5.6 (0.014) | +4.5 (0.020) | 0.051 (8/10+) | 0.002 | 33/27→40 of 58 | 35/38 | +3.3 (<0.001) |
| common-10 (18 trials; sensitivity, not selected) | A | 54.6 | 59.1 | +4.5 (11/18) | 0.010 | 0.026 | +4.5 (0.015) | +2.4 (0.145) | 0.010 (9/10+) | 0.020 | 26/37→44 of 58 | 36/39 | +4.5 (<0.001) |
| common-10 (18 trials; sensitivity, not selected) | B | 52.6 | 56.4 | +3.8 (14/18) | 0.065 | 0.096 | +2.4 (0.079) | +3.6 (0.013) | 0.035 (8/10+) | 0.125 | 27/31→39 of 58 | 32/30 | +4.2 (<0.001) |
| common-10 (18 trials; sensitivity, not selected) | full | 58.4 | 65.3 | +6.9 (15/18) | <0.001 | 0.001 | +5.3 (0.003) | +5.1 (0.009) | 0.023 (7/10+) | 0.002 | 33/42→48 of 58 | 41/43 | +3.1 (0.007) |

## Other threshold metrics for the selected scenarios (base → ECG, sign-flip p)

pct_lt05 / pct_gt20: % of variables with |SMD| < 0.05 / > 0.2; max = largest |SMD|; keyphys_all = % of trials in which all available key physiology variables (LVEF, NT-proBNP, eGFR, Hb, LVIDd, LVESVi, LAVI, E/e', RVSP) are < 0.1.

| scenario | half | p58_pct_lt05 | p58_pct_gt20 | p58_max_smd | p58_keyphys_all | xo_pct_lt05 | xo_pct_gt20 | xo_max_smd | mean_smd |
|---|---|---|---|---|---|---|---|---|---|
| demo / caliper 0.1 (physiology trials) | A | 27.4→31.2 (0.312) | 26.7→21.3 (0.117) | 0.676→0.666 (0.922) | 0.0→0.0 (1.000) | 32.7→35.7 (0.289) | 17.0→12.6 (0.016) | 0.672→0.644 (0.688) | 0.155→0.129 (0.031) |
| demo / caliper 0.1 (physiology trials) | B | 23.7→27.8 (0.086) | 26.5→19.2 (0.047) | 0.778→0.613 (0.117) | 0.0→0.0 (1.000) | 31.5→33.7 (0.008) | 18.0→14.1 (0.055) | 0.602→0.520 (0.047) | 0.163→0.131 (0.016) |
| demo / caliper 0.1 (physiology trials) | full | 27.6→34.1 (0.031) | 22.4→15.9 (0.008) | 0.616→0.525 (0.133) | 12.5→0.0 (1.000) | 34.8→39.1 (0.016) | 16.1→11.6 (0.016) | 0.554→0.440 (0.023) | 0.138→0.110 (0.008) |
| minimal-7 (physiology trials) | A | 23.3→30.0 (0.094) | 25.9→19.8 (0.031) | 0.628→0.642 (0.906) | 0.0→0.0 (1.000) | 37.0→39.8 (0.109) | 12.7→10.5 (0.047) | 0.746→0.682 (0.180) | 0.150→0.127 (0.008) |
| minimal-7 (physiology trials) | B | 22.8→27.4 (0.203) | 27.6→19.6 (0.078) | 0.724→0.626 (0.273) | 0.0→0.0 (1.000) | 33.2→37.3 (0.195) | 13.8→10.5 (0.023) | 0.628→0.577 (0.289) | 0.153→0.129 (0.102) |
| minimal-7 (physiology trials) | full | 26.1→33.4 (0.078) | 21.8→14.9 (0.008) | 0.627→0.569 (0.406) | 0.0→0.0 (1.000) | 37.6→42.3 (0.031) | 11.8→8.5 (0.070) | 0.636→0.551 (0.062) | 0.129→0.109 (0.016) |
| common-10 (physiology trials) | A | 26.9→31.5 (0.102) | 21.1→16.4 (0.062) | 0.679→0.630 (0.211) | 0.0→0.0 (1.000) | 35.5→39.9 (0.008) | 10.6→8.1 (0.047) | 0.635→0.616 (0.859) | 0.135→0.117 (0.008) |
| common-10 (physiology trials) | B | 24.4→25.2 (0.781) | 22.0→17.9 (0.016) | 0.697→0.536 (0.031) | 0.0→0.0 (1.000) | 32.3→38.9 (0.008) | 12.3→9.1 (0.023) | 0.516→0.462 (0.344) | 0.143→0.121 (0.008) |
| common-10 (physiology trials) | full | 32.5→37.7 (0.203) | 18.3→11.2 (0.062) | 0.678→0.545 (0.094) | 0.0→0.0 (1.000) | 39.8→45.2 (0.078) | 9.5→6.6 (0.016) | 0.452→0.409 (0.117) | 0.121→0.098 (0.031) |
| sparse (reference) | A | 34.1→33.3 (0.626) | 17.4→16.3 (0.554) | 0.640→0.646 (0.860) | 0.0→0.0 (1.000) | 44.2→45.7 (0.033) | 6.3→5.5 (0.118) | 0.582→0.581 (0.994) | 0.121→0.118 (0.504) |
| sparse (reference) | B | 30.0→31.7 (0.467) | 16.9→15.7 (0.338) | 0.572→0.516 (0.183) | 0.0→0.0 (1.000) | 42.7→44.1 (0.306) | 6.6→6.1 (0.459) | 0.522→0.473 (0.222) | 0.122→0.114 (0.033) |
| sparse (reference) | full | 36.9→37.6 (0.587) | 15.0→11.9 (0.006) | 0.540→0.531 (0.849) | 0.0→0.0 (1.000) | 45.5→48.7 (0.004) | 5.9→4.3 (0.022) | 0.459→0.441 (0.438) | 0.107→0.101 (0.026) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | A | 27.9→31.9 (0.048) | 25.9→20.5 (0.016) | 0.650→0.678 (0.510) | 0.0→0.0 (1.000) | 33.1→35.3 (0.120) | 15.9→12.2 (<0.001) | 0.627→0.577 (0.134) | 0.149→0.129 (0.002) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | B | 27.5→29.3 (0.263) | 24.8→18.6 (<0.001) | 0.663→0.550 (0.022) | 0.0→0.0 (1.000) | 31.5→34.3 (<0.001) | 17.0→13.4 (0.001) | 0.622→0.627 (0.893) | 0.150→0.128 (<0.001) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | full | 30.5→36.1 (<0.001) | 22.4→15.4 (<0.001) | 0.560→0.519 (0.230) | 5.6→0.0 (1.000) | 34.8→37.9 (0.002) | 15.1→11.7 (<0.001) | 0.548→0.468 (<0.001) | 0.136→0.111 (<0.001) |
| minimal-7 (18 trials; sensitivity, not selected) | A | 27.5→30.7 (0.139) | 24.7→20.2 (0.013) | 0.610→0.645 (0.386) | 0.0→0.0 (1.000) | 39.9→41.8 (0.043) | 10.4→8.6 (0.001) | 0.670→0.617 (0.061) | 0.144→0.129 (0.002) |
| minimal-7 (18 trials; sensitivity, not selected) | B | 27.1→31.8 (0.009) | 23.3→18.2 (0.013) | 0.640→0.564 (0.065) | 0.0→0.0 (1.000) | 37.7→40.3 (0.054) | 11.0→9.4 (0.025) | 0.588→0.573 (0.621) | 0.143→0.124 (0.003) |
| minimal-7 (18 trials; sensitivity, not selected) | full | 29.5→34.1 (0.020) | 20.3→15.0 (<0.001) | 0.540→0.520 (0.558) | 0.0→0.0 (1.000) | 41.0→44.4 (<0.001) | 9.9→7.5 (<0.001) | 0.570→0.534 (0.078) | 0.128→0.112 (<0.001) |
| common-10 (18 trials; sensitivity, not selected) | A | 30.0→31.8 (0.270) | 19.8→16.6 (0.014) | 0.641→0.626 (0.507) | 0.0→0.0 (1.000) | 40.5→44.2 (<0.001) | 7.7→5.9 (0.007) | 0.563→0.676 (0.434) | 0.131→0.118 (0.002) |
| common-10 (18 trials; sensitivity, not selected) | B | 28.8→30.1 (0.318) | 17.5→16.8 (0.734) | 0.597→0.516 (0.021) | 5.6→0.0 (1.000) | 39.6→43.1 (0.005) | 8.5→6.9 (0.017) | 0.476→0.516 (0.541) | 0.127→0.115 (0.031) |
| common-10 (18 trials; sensitivity, not selected) | full | 35.0→38.8 (0.045) | 15.3→12.4 (0.106) | 0.562→0.525 (0.425) | 0.0→0.0 (1.000) | 44.1→47.9 (0.003) | 6.3→5.1 (0.081) | 0.464→0.463 (0.933) | 0.112→0.099 (0.014) |

## Part 2: trial emulation in the selected scenarios (+ sparse reference)

|Δ| = |log HR − RCT log HR| (mean over trials); z² = Δ²/(SE² + SE_RCT²); consistency = % trials with |z| < 1.96; estimate agreement = % trials whose point estimate lies in the RCT 95% CI; φ = Q/(k−1). Shuffled-RCT null: RCT log HR and SE permuted jointly across trials (5,000 draws), median null d and one-sided p = P(null d ≤ observed d). Dropout cells: seed-averaged.

| scenario | half | |Δ| base→ECG | d |Δ| (k, p) | shuffled-RCT null d (p) | cluster p / LOO | vs shuf / noise p | z² base→ECG | d z² (p) | z² shuffled-RCT p | z² cluster p | consistency % | estimate agreement % | φ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| demo / caliper 0.1 (physiology trials) | full | 0.316→0.233 | -0.083 (5/8, 0.078) | -0.038 (0.172) | 0.156 (4/7+) / 0.156 | -0.113 (0.078) / -0.100 (0.062) | 11.82→6.03 | -5.79 (0.062) | 0.569 | 0.125 | 62→75 (shuf 50) | 38→50 (shuf 38) | 13.31→6.71 (shuf 16.61) |
| demo / caliper 0.1 (physiology trials) | A | 0.349→0.278 | -0.072 (6/8, 0.211) | -0.038 (0.169) | 0.344 (5/7+) / 0.406 | -0.112 (0.055) / -0.096 (0.188) | 10.28→5.91 | -4.37 (0.234) | 0.429 | 0.391 | 62→62 (shuf 50) | 38→50 (shuf 12) | 11.61→6.73 (shuf 12.54) |
| demo / caliper 0.1 (physiology trials) | B | 0.359→0.228 | -0.131 (6/8, 0.062) | -0.065 (0.012) | 0.125 (5/7+) / 0.125 | -0.064 (0.266) / -0.090 (0.156) | 10.94→3.96 | -6.98 (0.070) | 0.381 | 0.141 | 62→88 (shuf 62) | 38→50 (shuf 50) | 12.02→4.53 (shuf 9.40) |
| minimal-7 (physiology trials) | full | 0.286→0.200 | -0.087 (6/8, 0.031) | -0.056 (0.058) | 0.062 (5/7+) / 0.062 | -0.070 (0.109) / -0.061 (0.102) | 9.98→4.58 | -5.40 (0.039) | 0.458 | 0.078 | 62→62 (shuf 62) | 38→62 (shuf 50) | 10.89→5.04 (shuf 10.47) |
| minimal-7 (physiology trials) | A | 0.281→0.239 | -0.042 (5/8, 0.227) | -0.031 (0.209) | 0.219 (5/7+) / 0.453 | -0.117 (0.062) / -0.036 (0.398) | 7.73→4.92 | -2.81 (0.312) | 0.296 | 0.219 | 62→62 (shuf 50) | 50→50 (shuf 25) | 8.37→5.32 (shuf 11.18) |
| minimal-7 (physiology trials) | B | 0.250→0.198 | -0.052 (5/8, 0.391) | -0.066 (0.696) | 0.672 (4/7+) / 0.781 | -0.046 (0.453) / -0.087 (0.117) | 6.01→2.44 | -3.56 (0.164) | 0.619 | 0.328 | 62→88 (shuf 62) | 50→50 (shuf 62) | 6.25→2.77 (shuf 6.32) |
| common-10 (physiology trials) | full | 0.229→0.213 | -0.016 (4/8, 0.758) | -0.044 (0.839) | 0.906 (3/7+) / 0.938 | -0.015 (0.594) / -0.037 (0.180) | 7.39→4.40 | -2.99 (0.266) | 0.847 | 0.469 | 62→75 (shuf 62) | 62→38 (shuf 50) | 8.11→4.93 (shuf 6.55) |
| common-10 (physiology trials) | A | 0.270→0.228 | -0.042 (6/8, 0.320) | -0.015 (0.205) | 0.438 (5/7+) / 0.578 | -0.073 (0.156) / -0.013 (0.664) | 5.65→3.86 | -1.79 (0.133) | 0.216 | 0.203 | 50→75 (shuf 62) | 38→50 (shuf 38) | 6.45→4.30 (shuf 7.73) |
| common-10 (physiology trials) | B | 0.225→0.162 | -0.063 (6/8, 0.055) | -0.013 (0.265) | 0.109 (5/7+) / 0.109 | -0.102 (0.016) / -0.039 (0.219) | 4.01→2.24 | -1.77 (0.070) | 0.529 | 0.141 | 62→88 (shuf 62) | 50→75 (shuf 38) | 4.50→2.48 (shuf 5.63) |
| sparse (reference) | full | 0.182→0.162 | -0.020 (14/18, 0.264) | -0.017 (0.417) | 0.061 (8/10+) / 0.517 | -0.023 (0.088) / -0.034 (0.053) | 4.90→3.50 | -1.40 (0.024) | 0.804 | 0.025 | 61→78 (shuf 67) | 56→56 (shuf 50) | 4.70→3.41 (shuf 4.59) |
| sparse (reference) | A | 0.245→0.186 | -0.059 (14/18, 0.042) | -0.011 (0.013) | 0.043 (9/10+) / 0.083 | -0.019 (0.349) / -0.019 (0.551) | 4.70→3.23 | -1.47 (0.013) | 0.163 | 0.033 | 67→72 (shuf 72) | 22→39 (shuf 44) | 4.50→3.13 (shuf 4.08) |
| sparse (reference) | B | 0.203→0.169 | -0.034 (13/18, 0.231) | -0.032 (0.463) | 0.320 (7/10+) / 0.417 | -0.052 (0.001) / -0.037 (<0.001) | 3.54→2.31 | -1.22 (0.030) | 0.787 | 0.055 | 61→78 (shuf 67) | 39→44 (shuf 22) | 3.52→2.17 (shuf 3.65) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | full | 0.259→0.213 | -0.046 (12/18, 0.087) | -0.024 (0.104) | 0.354 (5/10+) / 0.167 | -0.059 (0.082) / -0.050 (0.094) | 9.89→6.38 | -3.51 (0.007) | 0.516 | 0.113 | 56→61 (shuf 50) | 44→44 (shuf 44) | 9.86→6.16 (shuf 11.00) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | A | 0.254→0.201 | -0.052 (14/18, 0.045) | -0.047 (0.384) | 0.031 (8/10+) / 0.090 | -0.086 (0.002) / -0.083 (0.011) | 7.51→4.77 | -2.74 (0.026) | 0.424 | 0.025 | 67→67 (shuf 56) | 44→56 (shuf 33) | 7.32→4.68 (shuf 7.68) |
| demo / caliper 0.1 (18 trials; sensitivity, not selected) | B | 0.284→0.231 | -0.053 (11/18, 0.152) | -0.040 (0.249) | 0.434 (6/10+) / 0.292 | -0.041 (0.162) / -0.059 (0.091) | 7.76→4.40 | -3.35 (0.069) | 0.477 | 0.225 | 56→72 (shuf 56) | 44→39 (shuf 39) | 7.82→3.91 (shuf 6.75) |
| minimal-7 (18 trials; sensitivity, not selected) | full | 0.238→0.200 | -0.038 (11/18, 0.058) | -0.027 (0.102) | 0.068 (7/10+) / 0.116 | -0.036 (0.101) / -0.043 (0.007) | 8.37→5.63 | -2.73 (0.033) | 0.324 | 0.094 | 56→61 (shuf 56) | 44→50 (shuf 44) | 8.17→5.13 (shuf 8.43) |
| minimal-7 (18 trials; sensitivity, not selected) | A | 0.217→0.197 | -0.020 (11/18, 0.269) | -0.015 (0.287) | 0.047 (7/10+) / 0.517 | -0.084 (0.006) / -0.038 (0.046) | 6.42→4.74 | -1.69 (0.073) | 0.067 | 0.025 | 67→67 (shuf 56) | 56→50 (shuf 39) | 6.32→4.62 (shuf 7.69) |
| minimal-7 (18 trials; sensitivity, not selected) | B | 0.235→0.228 | -0.008 (9/18, 0.805) | -0.022 (0.839) | 0.957 (5/10+) / 0.979 | -0.016 (0.596) / -0.036 (0.244) | 5.58→3.99 | -1.59 (0.188) | 0.437 | 0.281 | 61→67 (shuf 61) | 33→33 (shuf 44) | 5.38→3.42 (shuf 5.75) |
| common-10 (18 trials; sensitivity, not selected) | full | 0.215→0.200 | -0.016 (10/18, 0.520) | -0.030 (0.839) | 0.594 (5/10+) / 0.958 | -0.002 (0.928) / -0.015 (0.422) | 6.62→4.37 | -2.25 (0.035) | 0.742 | 0.117 | 61→72 (shuf 61) | 44→33 (shuf 44) | 6.52→4.04 (shuf 5.33) |
| common-10 (18 trials; sensitivity, not selected) | A | 0.214→0.183 | -0.031 (11/18, 0.177) | -0.020 (0.256) | 0.312 (7/10+) / 0.322 | -0.056 (0.131) / -0.031 (0.151) | 4.82→3.65 | -1.17 (0.029) | 0.148 | 0.068 | 61→78 (shuf 67) | 44→50 (shuf 39) | 4.52→3.43 (shuf 5.02) |
| common-10 (18 trials; sensitivity, not selected) | B | 0.232→0.195 | -0.037 (14/18, 0.081) | -0.015 (0.130) | 0.297 (7/10+) / 0.149 | -0.044 (0.073) / -0.011 (0.708) | 4.01→2.73 | -1.28 (0.021) | 0.442 | 0.137 | 61→72 (shuf 67) | 28→44 (shuf 28) | 3.76→2.50 (shuf 4.29) |

### Per-trial estimates: demo / caliper 0.1 (physiology trials) (full cohort)

| trial | RCT HR | base HR | +ECG HR | +shufECG HR | |Δ| base | |Δ| ECG | ECG closer |
|---|---|---|---|---|---|---|---|
| comet | 1.21 | 1.20 | 1.23 | 1.17 | 0.007 | 0.022 | no |
| paradigm-hf-seq | 0.80 | 1.16 | 0.99 | 1.27 | 0.375 | 0.218 | yes |
| transform-hf | 1.02 | 0.92 | 1.23 | 0.91 | 0.103 | 0.187 | no |
| elite-ii | 1.13 | 0.86 | 0.96 | 0.91 | 0.268 | 0.168 | yes |
| life | 0.87 | 0.68 | 0.80 | 0.67 | 0.241 | 0.083 | yes |
| emperor-preserved-v2 | 0.79 | 0.79 | 0.81 | 0.81 | 0.001 | 0.031 | no |
| east-afnet4 | 0.79 | 1.07 | 0.94 | 1.08 | 0.305 | 0.170 | yes |
| cabana-v2 | 0.86 | 0.25 | 0.32 | 0.22 | 1.230 | 0.990 | yes |

### Per-trial estimates: minimal-7 (physiology trials) (full cohort)

| trial | RCT HR | base HR | +ECG HR | +shufECG HR | |Δ| base | |Δ| ECG | ECG closer |
|---|---|---|---|---|---|---|---|
| comet | 1.21 | 1.21 | 1.22 | 1.21 | 0.001 | 0.013 | no |
| paradigm-hf-seq | 0.80 | 1.20 | 0.99 | 1.18 | 0.403 | 0.212 | yes |
| transform-hf | 1.02 | 0.94 | 0.96 | 1.02 | 0.079 | 0.056 | yes |
| elite-ii | 1.13 | 0.89 | 0.97 | 0.95 | 0.234 | 0.157 | yes |
| life | 0.87 | 0.71 | 0.80 | 0.71 | 0.204 | 0.090 | yes |
| emperor-preserved-v2 | 0.79 | 0.86 | 0.87 | 0.86 | 0.083 | 0.091 | no |
| east-afnet4 | 0.79 | 1.04 | 0.95 | 1.04 | 0.273 | 0.184 | yes |
| cabana-v2 | 0.86 | 0.31 | 0.39 | 0.31 | 1.013 | 0.795 | yes |

### Per-trial estimates: common-10 (physiology trials) (full cohort)

| trial | RCT HR | base HR | +ECG HR | +shufECG HR | |Δ| base | |Δ| ECG | ECG closer |
|---|---|---|---|---|---|---|---|
| comet | 1.21 | 1.16 | 1.21 | 1.18 | 0.042 | 0.001 | yes |
| paradigm-hf-seq | 0.80 | 1.09 | 0.99 | 1.04 | 0.310 | 0.211 | yes |
| transform-hf | 1.02 | 0.97 | 0.86 | 0.85 | 0.048 | 0.173 | no |
| elite-ii | 1.13 | 1.01 | 0.89 | 0.96 | 0.115 | 0.236 | no |
| life | 0.87 | 0.83 | 0.81 | 0.84 | 0.045 | 0.070 | no |
| emperor-preserved-v2 | 0.79 | 0.82 | 0.89 | 0.84 | 0.032 | 0.122 | no |
| east-afnet4 | 0.79 | 1.02 | 0.94 | 1.00 | 0.258 | 0.174 | yes |
| cabana-v2 | 0.86 | 0.32 | 0.42 | 0.36 | 0.981 | 0.715 | yes |

### Per-trial estimates: sparse (reference) (full cohort)

| trial | RCT HR | base HR | +ECG HR | +shufECG HR | |Δ| base | |Δ| ECG | ECG closer |
|---|---|---|---|---|---|---|---|
| comet | 1.21 | 1.18 | 1.19 | 1.13 | 0.020 | 0.017 | yes |
| paradigm-hf-seq | 0.80 | 1.02 | 0.96 | 1.05 | 0.244 | 0.184 | yes |
| transform-hf | 1.02 | 0.94 | 0.93 | 0.97 | 0.086 | 0.092 | no |
| elite-ii | 1.13 | 0.96 | 0.99 | 1.00 | 0.163 | 0.127 | yes |
| life | 0.87 | 0.86 | 0.79 | 0.82 | 0.016 | 0.091 | no |
| plato | 0.84 | 0.79 | 0.85 | 0.86 | 0.063 | 0.009 | yes |
| aristotle | 0.79 | 0.75 | 0.79 | 0.72 | 0.053 | 0.003 | yes |
| rocket-af | 0.88 | 0.69 | 0.72 | 0.69 | 0.243 | 0.199 | yes |
| rely | 0.66 | 0.82 | 0.99 | 0.87 | 0.217 | 0.401 | no |
| allhat | 0.98 | 1.16 | 1.15 | 1.16 | 0.169 | 0.161 | yes |
| emperor-preserved-v2 | 0.79 | 0.83 | 0.81 | 0.86 | 0.049 | 0.030 | yes |
| east-afnet4 | 0.79 | 0.97 | 0.93 | 0.99 | 0.201 | 0.166 | yes |
| cabana-v2 | 0.86 | 0.34 | 0.41 | 0.38 | 0.914 | 0.735 | yes |
| ontarget | 1.01 | 0.85 | 0.87 | 0.85 | 0.171 | 0.149 | yes |
| value | 1.04 | 0.79 | 0.82 | 0.82 | 0.276 | 0.239 | yes |
| ascot | 0.90 | 0.74 | 0.77 | 0.78 | 0.191 | 0.160 | yes |
| empa-reg | 0.86 | 0.80 | 0.80 | 0.76 | 0.069 | 0.078 | no |
| carolina | 0.98 | 0.87 | 0.92 | 0.86 | 0.124 | 0.067 | yes |

### Per-trial estimates: demo / caliper 0.1 (18 trials; sensitivity, not selected) (full cohort)

| trial | RCT HR | base HR | +ECG HR | +shufECG HR | |Δ| base | |Δ| ECG | ECG closer |
|---|---|---|---|---|---|---|---|
| comet | 1.21 | 1.20 | 1.23 | 1.17 | 0.007 | 0.022 | no |
| paradigm-hf-seq | 0.80 | 1.16 | 0.99 | 1.27 | 0.375 | 0.218 | yes |
| transform-hf | 1.02 | 0.92 | 1.23 | 0.91 | 0.103 | 0.187 | no |
| elite-ii | 1.13 | 0.86 | 0.96 | 0.91 | 0.268 | 0.168 | yes |
| life | 0.87 | 0.68 | 0.80 | 0.67 | 0.241 | 0.083 | yes |
| plato | 0.84 | 0.81 | 0.81 | 0.79 | 0.031 | 0.033 | no |
| aristotle | 0.79 | 0.55 | 0.65 | 0.51 | 0.355 | 0.197 | yes |
| rocket-af | 0.88 | 0.48 | 0.49 | 0.53 | 0.609 | 0.582 | yes |
| rely | 0.66 | 0.77 | 0.73 | 0.80 | 0.155 | 0.099 | yes |
| allhat | 0.98 | 1.31 | 1.22 | 1.28 | 0.289 | 0.218 | yes |
| emperor-preserved-v2 | 0.79 | 0.79 | 0.81 | 0.81 | 0.001 | 0.031 | no |
| east-afnet4 | 0.79 | 1.07 | 0.94 | 1.08 | 0.305 | 0.170 | yes |
| cabana-v2 | 0.86 | 0.25 | 0.32 | 0.22 | 1.230 | 0.990 | yes |
| ontarget | 1.01 | 0.82 | 0.84 | 0.82 | 0.212 | 0.186 | yes |
| value | 1.04 | 0.74 | 0.76 | 0.75 | 0.334 | 0.313 | yes |
| ascot | 0.90 | 0.82 | 0.92 | 0.83 | 0.090 | 0.027 | yes |
| empa-reg | 0.86 | 0.84 | 0.67 | 0.85 | 0.020 | 0.247 | no |
| carolina | 0.98 | 1.02 | 0.92 | 1.02 | 0.042 | 0.067 | no |

### Per-trial estimates: minimal-7 (18 trials; sensitivity, not selected) (full cohort)

| trial | RCT HR | base HR | +ECG HR | +shufECG HR | |Δ| base | |Δ| ECG | ECG closer |
|---|---|---|---|---|---|---|---|
| comet | 1.21 | 1.21 | 1.22 | 1.21 | 0.001 | 0.013 | no |
| paradigm-hf-seq | 0.80 | 1.20 | 0.99 | 1.18 | 0.403 | 0.212 | yes |
| transform-hf | 1.02 | 0.94 | 0.96 | 1.02 | 0.079 | 0.056 | yes |
| elite-ii | 1.13 | 0.89 | 0.97 | 0.95 | 0.234 | 0.157 | yes |
| life | 0.87 | 0.71 | 0.80 | 0.71 | 0.204 | 0.090 | yes |
| plato | 0.84 | 0.78 | 0.82 | 0.79 | 0.075 | 0.021 | yes |
| aristotle | 0.79 | 0.61 | 0.56 | 0.54 | 0.256 | 0.349 | no |
| rocket-af | 0.88 | 0.56 | 0.57 | 0.56 | 0.449 | 0.443 | yes |
| rely | 0.66 | 0.82 | 0.88 | 0.75 | 0.213 | 0.283 | no |
| allhat | 0.98 | 1.20 | 1.12 | 1.22 | 0.201 | 0.134 | yes |
| emperor-preserved-v2 | 0.79 | 0.86 | 0.87 | 0.86 | 0.083 | 0.091 | no |
| east-afnet4 | 0.79 | 1.04 | 0.95 | 1.04 | 0.273 | 0.184 | yes |
| cabana-v2 | 0.86 | 0.31 | 0.39 | 0.31 | 1.013 | 0.795 | yes |
| ontarget | 1.01 | 0.79 | 0.82 | 0.79 | 0.249 | 0.214 | yes |
| value | 1.04 | 0.77 | 0.77 | 0.76 | 0.301 | 0.301 | no |
| ascot | 0.90 | 0.80 | 0.80 | 0.78 | 0.112 | 0.119 | no |
| empa-reg | 0.86 | 0.80 | 0.77 | 0.79 | 0.078 | 0.110 | no |
| carolina | 0.98 | 0.92 | 0.96 | 0.93 | 0.058 | 0.019 | yes |

### Per-trial estimates: common-10 (18 trials; sensitivity, not selected) (full cohort)

| trial | RCT HR | base HR | +ECG HR | +shufECG HR | |Δ| base | |Δ| ECG | ECG closer |
|---|---|---|---|---|---|---|---|
| comet | 1.21 | 1.16 | 1.21 | 1.18 | 0.042 | 0.001 | yes |
| paradigm-hf-seq | 0.80 | 1.09 | 0.99 | 1.04 | 0.310 | 0.211 | yes |
| transform-hf | 1.02 | 0.97 | 0.86 | 0.85 | 0.048 | 0.173 | no |
| elite-ii | 1.13 | 1.01 | 0.89 | 0.96 | 0.115 | 0.236 | no |
| life | 0.87 | 0.83 | 0.81 | 0.84 | 0.045 | 0.070 | no |
| plato | 0.84 | 0.86 | 0.86 | 0.84 | 0.023 | 0.024 | no |
| aristotle | 0.79 | 0.70 | 0.66 | 0.64 | 0.123 | 0.179 | no |
| rocket-af | 0.88 | 0.60 | 0.64 | 0.58 | 0.384 | 0.320 | yes |
| rely | 0.66 | 0.88 | 0.97 | 0.82 | 0.287 | 0.385 | no |
| allhat | 0.98 | 1.22 | 1.08 | 1.18 | 0.222 | 0.096 | yes |
| emperor-preserved-v2 | 0.79 | 0.82 | 0.89 | 0.84 | 0.032 | 0.122 | no |
| east-afnet4 | 0.79 | 1.02 | 0.94 | 1.00 | 0.258 | 0.174 | yes |
| cabana-v2 | 0.86 | 0.32 | 0.42 | 0.36 | 0.981 | 0.715 | yes |
| ontarget | 1.01 | 0.82 | 0.84 | 0.82 | 0.211 | 0.180 | yes |
| value | 1.04 | 0.78 | 0.81 | 0.81 | 0.286 | 0.247 | yes |
| ascot | 0.90 | 0.75 | 0.77 | 0.76 | 0.185 | 0.160 | yes |
| empa-reg | 0.86 | 0.75 | 0.72 | 0.81 | 0.131 | 0.173 | no |
| carolina | 0.98 | 0.81 | 0.86 | 0.90 | 0.193 | 0.129 | yes |

## Grid: % of held-out variables with |SMD| < 0.1, 58-panel, all 18 trials

q = BH over cells within half × subset × panel; q global = BH over cells × both panels (within half, subset).

| cell | full base→ECG | full d (k, p) | A base→ECG | A d (k, p) | B base→ECG | B d (k, p) | full q | full q global | shuf−base / noise−base d | ECG−shuf / ECG−noise p | love unm/base→ECG | cluster p / LOO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none (ECG only) | 51.5→59.9 | +8.4 (16/18, <0.001) | 49.6→51.8 | +2.3 (9/18, 0.265) | 47.0→52.8 | +5.9 (14/18, 0.015) | <0.001 | <0.001 | -1.5 / -0.2 | <0.001 / <0.001 | 33/33→43 | 0.004 / <0.001 |
| demo | 53.8→60.2 | +6.4 (14/18, <0.001) | 48.9→56.5 | +7.7 (16/18, 0.001) | 47.3→54.0 | +6.7 (12/18, 0.004) | <0.001 | 0.001 | -1.0 / +0.5 | 0.001 / 0.003 | 33/32→43 | 0.016 / <0.001 |
| demo+race | 51.9→60.1 | +8.2 (16/18, <0.001) | 49.4→54.0 | +4.6 (12/18, 0.097) | 48.0→51.9 | +3.8 (13/18, 0.148) | <0.001 | <0.001 | +1.8 / +0.1 | <0.001 / <0.001 | 33/30→42 | 0.002 / <0.001 |
| minimal-7 | 53.1→59.8 | +6.7 (15/18, <0.001) | 49.2→55.2 | +6.0 (14/18, 0.002) | 50.6→54.8 | +4.1 (11/18, 0.028) | 0.001 | 0.003 | +1.2 / +2.2 | 0.014 / 0.020 | 33/27→40 | 0.051 / 0.002 |
| min-7+AF+HF | 58.1→63.2 | +5.1 (12/18, 0.013) | 52.4→55.4 | +3.0 (11/18, 0.067) | 51.3→55.0 | +3.7 (13/18, 0.135) | 0.018 | 0.026 | +1.2 / +0.1 | 0.070 / 0.017 | 33/38→45 | 0.020 / 0.025 |
| common-10 | 58.4→65.3 | +6.9 (15/18, <0.001) | 54.6→59.1 | +4.5 (11/18, 0.010) | 52.6→56.4 | +3.8 (14/18, 0.065) | 0.001 | 0.003 | +1.6 / +1.8 | 0.003 / 0.009 | 33/42→48 | 0.023 / 0.002 |
| sparse | 63.4→64.0 | +0.7 (8/18, 0.688) | 56.6→59.0 | +2.4 (12/18, 0.110) | 56.4→58.1 | +1.7 (10/18, 0.355) | 0.688 | 0.693 | -1.5 / +0.2 | 0.158 / 0.813 | 33/48→47 | 0.363 / 1.000 |
| sparse, 25% dropout | 59.9→64.4 | +4.5 (16/18, <0.001) | 54.6→57.2 | +2.5 (13/18, 0.038) | 53.1→55.4 | +2.3 (12/18, 0.105) | <0.001 | 0.001 | -0.3 / +0.0 | <0.001 / 0.001 | 33/40→49 | 0.004 / <0.001 |
| sparse, 50% dropout | 57.8→63.1 | +5.2 (15/18, <0.001) | 52.7→56.4 | +3.7 (13/18, 0.007) | 50.8→55.6 | +4.8 (11/18, 0.008) | <0.001 | 0.001 | -0.0 / -0.1 | <0.001 / <0.001 | 33/39→45 | 0.006 / <0.001 |
| sparse, 75% dropout | 54.3→61.5 | +7.2 (17/18, <0.001) | 49.2→54.6 | +5.4 (16/18, <0.001) | 49.1→54.1 | +5.0 (14/18, 0.009) | <0.001 | <0.001 | +1.6 / -0.2 | <0.001 / <0.001 | 33/36→40 | 0.006 / <0.001 |
| sparse minus AF | 62.6→66.2 | +3.6 (13/18, 0.017) | 56.6→58.4 | +1.7 (10/18, 0.226) | 53.4→58.1 | +4.7 (13/18, 0.057) | 0.021 | 0.028 | -1.5 / +1.0 | 0.014 / 0.231 | 33/46→48 | 0.014 / 0.034 |
| hdPS25 | 65.8→69.6 | +3.7 (13/18, 0.009) | 61.3→62.8 | +1.5 (9/18, 0.265) | 59.1→61.2 | +2.1 (10/18, 0.301) | 0.014 | 0.020 | +2.1 / -0.8 | 0.281 / 0.021 | 33/48→53 | 0.047 / 0.019 |
| hdPS50 | 69.4→70.4 | +1.0 (9/18, 0.499) | 61.5→62.5 | +1.0 (10/18, 0.493) | 59.3→60.8 | +1.5 (9/18, 0.359) | 0.514 | 0.506 | -1.0 / -1.5 | 0.271 / 0.220 | 33/51→53 | 0.715 / 0.817 |
| hdPS200 | 67.2→71.7 | +4.5 (12/18, 0.012) | 60.0→60.9 | +0.9 (8/18, 0.604) | 61.5→64.8 | +3.3 (12/18, 0.045) | 0.017 | 0.025 | +2.2 / +0.4 | 0.224 / 0.005 | 33/46→53 | 0.020 / 0.023 |
| demo / 64 PCs | 53.8→59.6 | +5.9 (14/18, 0.008) | 48.9→53.0 | +4.1 (12/18, 0.085) | 47.3→52.0 | +4.7 (11/18, 0.027) | 0.013 | 0.018 | -3.0 / -3.8 | <0.001 / <0.001 | 33/32→40 | 0.059 / 0.016 |
| demo / caliper 0.1 | 54.2→61.0 | +6.8 (13/18, <0.001) | 47.6→55.8 | +8.1 (16/18, 0.001) | 47.5→53.4 | +5.9 (12/18, 0.004) | 0.001 | 0.003 | -2.3 / -0.1 | <0.001 / <0.001 | 33/29→43 | 0.023 / 0.002 |
| demo / 1:3 matching | 53.2→61.8 | +8.6 (14/18, <0.001) | 51.0→56.4 | +5.5 (13/18, 0.004) | 47.4→54.4 | +7.0 (16/18, <0.001) | <0.001 | 0.001 | +0.7 / +0.6 | <0.001 / <0.001 | 33/31→44 | 0.004 / <0.001 |
| demo / overlap weights | 53.8→61.8 | +8.0 (18/18, <0.001) | 50.0→56.2 | +6.1 (15/18, <0.001) | 48.2→55.9 | +7.7 (14/18, <0.001) | <0.001 | <0.001 | -0.0 / -0.8 | <0.001 / <0.001 | 33/35→45 | 0.002 / <0.001 |
| minimal-7 / 64 PCs | 53.1→60.5 | +7.4 (15/18, <0.001) | 49.2→54.3 | +5.1 (14/18, 0.005) | 50.6→54.2 | +3.5 (12/18, 0.044) | <0.001 | 0.002 | +2.7 / +0.8 | 0.020 / <0.001 | 33/27→41 | 0.008 / <0.001 |
| minimal-7 / caliper 0.1 | 55.1→61.0 | +5.9 (16/18, <0.001) | 48.7→55.2 | +6.5 (13/18, 0.007) | 50.6→54.5 | +3.8 (13/18, 0.031) | <0.001 | 0.001 | -0.9 / +1.2 | 0.001 / 0.012 | 33/32→41 | 0.010 / <0.001 |
| minimal-7 / 1:3 matching | 55.0→61.7 | +6.7 (16/18, <0.001) | 53.0→56.8 | +3.8 (13/18, 0.016) | 49.6→54.7 | +5.0 (13/18, 0.020) | <0.001 | <0.001 | +0.3 / +0.8 | <0.001 / <0.001 | 33/32→44 | 0.004 / <0.001 |
| minimal-7 / overlap weights | 56.5→63.5 | +7.0 (16/18, <0.001) | 52.2→56.1 | +3.8 (11/18, 0.021) | 51.1→57.3 | +6.2 (15/18, <0.001) | <0.001 | <0.001 | -1.2 / +0.2 | <0.001 / <0.001 | 33/37→47 | 0.002 / <0.001 |
| sparse / 64 PCs | 63.4→66.4 | +3.1 (13/18, 0.056) | 56.6→58.6 | +1.9 (11/18, 0.188) | 56.4→59.4 | +2.9 (12/18, 0.147) | 0.063 | 0.073 | +1.6 / -1.7 | 0.318 / <0.001 | 33/48→53 | 0.070 / 0.112 |
| sparse / caliper 0.1 | 62.9→64.5 | +1.6 (10/18, 0.309) | 56.3→59.0 | +2.8 (13/18, 0.148) | 57.3→58.1 | +0.8 (11/18, 0.706) | 0.328 | 0.321 | -0.8 / +0.9 | 0.194 / 0.706 | 33/43→44 | 0.115 / 0.496 |
| sparse / 1:3 matching | 63.3→65.2 | +1.9 (10/18, 0.194) | 59.9→62.0 | +2.1 (9/18, 0.201) | 55.9→59.1 | +3.2 (12/18, 0.048) | 0.213 | 0.206 | -0.4 / +0.7 | 0.017 / 0.254 | 33/47→50 | 0.543 / 0.345 |
| sparse / overlap weights | 64.2→67.0 | +2.8 (11/18, 0.044) | 59.7→61.9 | +2.2 (11/18, 0.138) | 56.1→62.8 | +6.7 (17/18, <0.001) | 0.051 | 0.063 | -0.0 / -0.5 | 0.020 / 0.018 | 33/48→51 | 0.125 / 0.087 |
| sparse, 50% dropout / 64 PCs | 57.8→63.3 | +5.5 (14/18, <0.001) | 52.7→55.9 | +3.2 (16/18, 0.003) | 50.8→55.1 | +4.2 (14/18, 0.011) | <0.001 | 0.002 | -1.0 / -1.6 | <0.001 / <0.001 | 33/39→46 | 0.004 / <0.001 |
| sparse, 50% dropout / caliper 0.1 | 57.8→63.6 | +5.8 (15/18, <0.001) | 52.8→56.6 | +3.9 (15/18, <0.001) | 50.9→56.2 | +5.4 (14/18, 0.004) | <0.001 | 0.001 | -0.2 / -0.4 | <0.001 / <0.001 | 33/40→48 | 0.004 / <0.001 |
| sparse, 50% dropout / 1:3 matching | 57.8→63.3 | +5.5 (18/18, <0.001) | 53.7→57.7 | +3.9 (13/18, 0.014) | 51.6→56.4 | +4.8 (17/18, <0.001) | <0.001 | <0.001 | +0.1 / -0.2 | <0.001 / <0.001 | 33/38→43 | 0.002 / <0.001 |
| sparse, 50% dropout / overlap weights | 58.5→64.8 | +6.3 (16/18, <0.001) | 54.9→58.9 | +4.0 (13/18, 0.030) | 52.2→58.5 | +6.3 (17/18, <0.001) | <0.001 | <0.001 | -0.2 / -0.4 | <0.001 / <0.001 | 33/39→47 | 0.004 / <0.001 |
| hdPS200 / 64 PCs | 67.2→72.6 | +5.4 (13/18, 0.001) | 60.0→62.2 | +2.1 (11/18, 0.213) | 61.5→63.1 | +1.6 (10/18, 0.322) | 0.002 | 0.006 | +1.9 / +1.6 | 0.022 / 0.048 | 33/46→53 | 0.004 / 0.003 |
| hdPS200 / caliper 0.1 | 67.3→70.6 | +3.4 (10/18, 0.030) | 60.0→60.9 | +0.9 (9/18, 0.609) | 61.7→63.6 | +1.9 (9/18, 0.407) | 0.036 | 0.045 | +2.1 / +0.6 | 0.530 / 0.083 | 33/49→53 | 0.172 / 0.059 |
| hdPS200 / 1:3 matching | 68.3→72.1 | +3.7 (12/18, 0.014) | 61.2→64.5 | +3.3 (16/18, 0.007) | 63.9→63.7 | -0.2 (8/18, 0.864) | 0.019 | 0.026 | +1.2 / +1.4 | 0.048 / 0.178 | 33/46→50 | 0.039 / 0.028 |
| hdPS200 / overlap weights | 71.3→74.4 | +3.1 (11/18, 0.016) | 63.2→64.9 | +1.7 (9/18, 0.155) | 64.3→66.5 | +2.2 (13/18, 0.013) | 0.020 | 0.026 | -0.6 / +0.2 | 0.009 / 0.021 | 33/51→56 | 0.059 / 0.031 |

## Grid: % of held-out variables with |SMD| < 0.1, 58-panel, 8 physiology trials

q = BH over cells within half × subset × panel; q global = BH over cells × both panels (within half, subset).

| cell | full base→ECG | full d (k, p) | A base→ECG | A d (k, p) | B base→ECG | B d (k, p) | full q | full q global | shuf−base / noise−base d | ECG−shuf / ECG−noise p | love unm/base→ECG | cluster p / LOO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none (ECG only) | 52.4→59.9 | +7.5 (7/8, 0.016) | 50.0→50.6 | +0.6 (2/8, 0.875) | 45.7→50.9 | +5.2 (5/8, 0.164) | 0.041 | 0.026 | -1.9 / +0.4 | 0.008 / 0.008 | 35/35→36 | 0.031 / 0.031 |
| demo | 54.7→61.2 | +6.5 (6/8, 0.047) | 47.6→57.1 | +9.5 (7/8, 0.023) | 44.0→52.8 | +8.8 (6/8, 0.062) | 0.089 | 0.064 | -2.8 / -2.6 | 0.031 / 0.016 | 35/24→38 | 0.094 / 0.094 |
| demo+race | 50.2→60.6 | +10.3 (8/8, 0.008) | 48.3→51.3 | +3.0 (4/8, 0.539) | 44.8→48.7 | +3.9 (6/8, 0.422) | 0.038 | 0.018 | +2.8 / +1.1 | 0.047 / 0.008 | 35/28→39 | 0.016 / 0.016 |
| minimal-7 | 52.6→59.1 | +6.5 (7/8, 0.062) | 45.0→52.8 | +7.8 (7/8, 0.016) | 46.8→50.4 | +3.7 (6/8, 0.250) | 0.101 | 0.079 | +0.9 / +1.3 | 0.172 / 0.078 | 35/34→36 | 0.125 / 0.125 |
| min-7+AF+HF | 56.2→62.5 | +6.3 (5/8, 0.188) | 50.2→53.4 | +3.2 (6/8, 0.141) | 49.1→50.6 | +1.5 (4/8, 0.789) | 0.199 | 0.201 | +1.9 / -1.3 | 0.398 / 0.125 | 35/37→41 | 0.156 / 0.359 |
| common-10 | 56.7→64.7 | +8.0 (6/8, 0.078) | 50.9→58.6 | +7.8 (7/8, 0.016) | 44.8→52.8 | +8.0 (7/8, 0.016) | 0.115 | 0.096 | -1.3 / +2.6 | 0.031 / 0.234 | 35/32→45 | 0.156 / 0.156 |
| sparse | 61.6→64.2 | +2.6 (5/8, 0.172) | 52.4→55.4 | +3.0 (5/8, 0.141) | 51.7→56.2 | +4.5 (6/8, 0.047) | 0.195 | 0.187 | -1.3 / -0.6 | 0.312 / 0.273 | 35/42→42 | 0.156 / 0.344 |
| sparse, 25% dropout | 57.7→63.4 | +5.7 (8/8, 0.008) | 52.5→54.3 | +1.8 (5/8, 0.312) | 47.2→52.5 | +5.3 (6/8, 0.031) | 0.038 | 0.018 | -0.3 / +0.4 | 0.008 / 0.070 | 35/39→43 | 0.016 / 0.016 |
| sparse, 50% dropout | 55.5→61.9 | +6.4 (7/8, 0.016) | 51.7→52.9 | +1.1 (4/8, 0.531) | 46.1→52.8 | +6.7 (7/8, 0.047) | 0.041 | 0.026 | -0.5 / +0.1 | 0.023 / 0.023 | 35/34→40 | 0.031 / 0.031 |
| sparse, 75% dropout | 51.7→60.9 | +9.3 (8/8, 0.008) | 48.2→51.7 | +3.4 (6/8, 0.164) | 44.7→50.4 | +5.7 (6/8, 0.156) | 0.038 | 0.018 | +1.9 / -0.3 | 0.008 / 0.008 | 35/30→39 | 0.016 / 0.016 |
| sparse minus AF | 60.6→65.3 | +4.7 (6/8, 0.094) | 54.5→54.3 | -0.2 (4/8, 1.000) | 50.2→51.5 | +1.3 (5/8, 0.875) | 0.128 | 0.111 | -2.6 / +3.0 | 0.062 / 0.719 | 35/46→45 | 0.078 / 0.188 |
| hdPS25 | 63.8→67.7 | +3.9 (5/8, 0.234) | 59.5→60.1 | +0.6 (4/8, 0.812) | 54.5→57.3 | +2.8 (5/8, 0.422) | 0.234 | 0.245 | +2.4 / -1.1 | 0.594 / 0.234 | 35/40→47 | 0.453 / 0.469 |
| hdPS50 | 66.6→70.0 | +3.4 (6/8, 0.141) | 57.5→59.5 | +1.9 (5/8, 0.445) | 54.5→58.8 | +4.3 (5/8, 0.125) | 0.165 | 0.155 | -0.0 / -1.1 | 0.188 / 0.125 | 35/45→50 | 0.234 / 0.281 |
| hdPS200 | 65.5→72.8 | +7.3 (7/8, 0.016) | 56.9→58.6 | +1.7 (4/8, 0.578) | 59.1→61.4 | +2.4 (5/8, 0.422) | 0.041 | 0.026 | +5.6 / +3.0 | 0.555 / 0.039 | 35/44→50 | 0.031 / 0.031 |
| demo / 64 PCs | 54.7→59.7 | +5.0 (5/8, 0.234) | 47.6→50.9 | +3.2 (6/8, 0.469) | 44.0→46.3 | +2.4 (4/8, 0.562) | 0.234 | 0.245 | -5.4 / -7.1 | 0.016 / 0.008 | 35/24→36 | 0.375 / 0.469 |
| demo / caliper 0.1 | 55.0→60.3 | +5.4 (5/8, 0.141) | 45.5→55.6 | +10.1 (7/8, 0.031) | 42.9→50.6 | +7.8 (6/8, 0.047) | 0.165 | 0.155 | -4.7 / -3.9 | 0.031 / 0.031 | 35/25→38 | 0.250 / 0.281 |
| demo / 1:3 matching | 52.6→63.6 | +11.0 (7/8, 0.016) | 51.3→55.8 | +4.5 (5/8, 0.125) | 43.5→52.2 | +8.6 (8/8, 0.008) | 0.041 | 0.026 | +1.1 / +0.9 | 0.008 / 0.031 | 35/32→39 | 0.031 / 0.031 |
| demo / overlap weights | 52.6→61.9 | +9.3 (8/8, 0.008) | 49.1→55.2 | +6.0 (7/8, 0.055) | 43.8→54.7 | +11.0 (7/8, 0.016) | 0.038 | 0.018 | -0.0 / -0.9 | 0.008 / 0.008 | 35/29→40 | 0.016 / 0.016 |
| minimal-7 / 64 PCs | 52.6→61.0 | +8.4 (6/8, 0.062) | 45.0→51.5 | +6.5 (7/8, 0.031) | 46.8→53.7 | +6.9 (7/8, 0.023) | 0.101 | 0.079 | +2.2 / +0.4 | 0.109 / 0.023 | 35/34→45 | 0.125 / 0.125 |
| minimal-7 / caliper 0.1 | 52.6→59.1 | +6.5 (7/8, 0.031) | 45.7→52.2 | +6.5 (6/8, 0.125) | 46.8→49.4 | +2.6 (6/8, 0.352) | 0.066 | 0.046 | -0.2 / +1.9 | 0.062 / 0.172 | 35/32→38 | 0.062 / 0.062 |
| minimal-7 / 1:3 matching | 55.4→61.2 | +5.8 (6/8, 0.047) | 52.8→54.7 | +1.9 (4/8, 0.586) | 47.6→51.5 | +3.9 (4/8, 0.359) | 0.089 | 0.064 | +1.1 / +0.4 | 0.047 / 0.023 | 35/36→39 | 0.094 / 0.094 |
| minimal-7 / overlap weights | 57.1→63.4 | +6.2 (6/8, 0.031) | 51.7→53.9 | +2.2 (3/8, 0.562) | 47.6→55.8 | +8.2 (6/8, 0.031) | 0.066 | 0.046 | -1.9 / +0.4 | 0.008 / 0.055 | 35/37→42 | 0.062 / 0.062 |
| sparse / 64 PCs | 61.6→66.2 | +4.5 (8/8, 0.008) | 52.4→54.5 | +2.2 (5/8, 0.484) | 51.7→55.6 | +3.9 (7/8, 0.164) | 0.038 | 0.018 | -0.6 / -2.2 | 0.016 / 0.008 | 35/42→45 | 0.016 / 0.016 |
| sparse / caliper 0.1 | 59.1→63.6 | +4.5 (6/8, 0.055) | 51.7→54.1 | +2.4 (6/8, 0.273) | 51.9→56.0 | +4.1 (7/8, 0.273) | 0.098 | 0.072 | +1.7 / +1.9 | 0.500 / 0.414 | 35/41→41 | 0.047 / 0.109 |
| sparse / 1:3 matching | 61.6→65.3 | +3.7 (5/8, 0.180) | 56.9→59.1 | +2.2 (4/8, 0.500) | 52.4→57.3 | +5.0 (6/8, 0.062) | 0.197 | 0.194 | -0.6 / +2.4 | 0.016 / 0.602 | 35/43→45 | 0.203 / 0.359 |
| sparse / overlap weights | 62.3→67.2 | +5.0 (6/8, 0.133) | 58.4→59.7 | +1.3 (5/8, 0.672) | 51.7→60.8 | +9.1 (8/8, 0.008) | 0.165 | 0.149 | +0.0 / -1.1 | 0.062 / 0.062 | 35/41→47 | 0.203 / 0.266 |
| sparse, 50% dropout / 64 PCs | 55.5→63.1 | +7.6 (7/8, 0.023) | 51.7→53.9 | +2.2 (7/8, 0.133) | 46.1→52.0 | +5.9 (6/8, 0.094) | 0.057 | 0.037 | -1.2 / -0.4 | 0.008 / 0.016 | 35/34→44 | 0.047 / 0.047 |
| sparse, 50% dropout / caliper 0.1 | 55.1→62.3 | +7.2 (7/8, 0.016) | 51.6→53.1 | +1.5 (6/8, 0.172) | 46.0→52.1 | +6.1 (7/8, 0.055) | 0.041 | 0.026 | -1.2 / -0.6 | 0.016 / 0.023 | 35/34→41 | 0.031 / 0.031 |
| sparse, 50% dropout / 1:3 matching | 55.9→62.6 | +6.7 (8/8, 0.008) | 52.5→55.4 | +2.9 (6/8, 0.320) | 47.8→53.4 | +5.6 (7/8, 0.055) | 0.038 | 0.018 | -0.3 / -0.6 | 0.008 / 0.016 | 35/34→40 | 0.016 / 0.016 |
| sparse, 50% dropout / overlap weights | 56.3→64.7 | +8.4 (8/8, 0.008) | 54.2→57.6 | +3.4 (6/8, 0.336) | 47.6→56.4 | +8.8 (8/8, 0.008) | 0.038 | 0.018 | -0.6 / -0.1 | 0.008 / 0.008 | 35/36→44 | 0.016 / 0.016 |
| hdPS200 / 64 PCs | 65.5→71.6 | +6.0 (7/8, 0.016) | 56.9→57.5 | +0.6 (3/8, 0.875) | 59.1→60.1 | +1.1 (4/8, 0.672) | 0.041 | 0.026 | +1.9 / +5.8 | 0.062 / 1.000 | 35/44→47 | 0.031 / 0.031 |
| hdPS200 / caliper 0.1 | 64.7→70.3 | +5.6 (6/8, 0.078) | 56.0→57.5 | +1.5 (4/8, 0.727) | 58.6→59.3 | +0.6 (3/8, 0.922) | 0.115 | 0.096 | +5.0 / +3.0 | 0.859 / 0.297 | 35/47→49 | 0.141 / 0.156 |
| hdPS200 / 1:3 matching | 68.3→72.6 | +4.3 (6/8, 0.109) | 58.4→61.6 | +3.2 (7/8, 0.086) | 61.2→62.7 | +1.5 (5/8, 0.312) | 0.143 | 0.127 | +1.1 / +0.9 | 0.203 / 0.312 | 35/47→49 | 0.156 / 0.219 |
| hdPS200 / overlap weights | 70.3→74.8 | +4.5 (5/8, 0.094) | 59.5→61.2 | +1.7 (4/8, 0.375) | 61.2→64.9 | +3.7 (7/8, 0.016) | 0.128 | 0.111 | -1.1 / +0.4 | 0.062 / 0.125 | 35/50→51 | 0.188 / 0.188 |

## Grid: % of held-out variables with |SMD| < 0.1, expanded non-ECG-proximal panel, all 18 trials

q = BH over cells within half × subset × panel; q global = BH over cells × both panels (within half, subset).

| cell | full base→ECG | full d (k, p) | A base→ECG | A d (k, p) | B base→ECG | B d (k, p) | full q | full q global | shuf−base / noise−base d | ECG−shuf / ECG−noise p | cluster p / LOO |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none (ECG only) | 61.4→66.1 | +4.7 (16/18, <0.001) | 59.7→62.4 | +2.7 (13/18, 0.035) | 59.0→62.0 | +3.0 (13/18, 0.023) | <0.001 | 0.001 | -1.0 / +0.1 | <0.001 / <0.001 | 0.010 / <0.001 |
| demo | 60.0→65.3 | +5.3 (15/18, <0.001) | 58.3→63.6 | +5.3 (17/18, <0.001) | 56.8→60.9 | +4.0 (16/18, <0.001) | <0.001 | <0.001 | -0.3 / +0.5 | <0.001 / <0.001 | 0.004 / <0.001 |
| demo+race | 60.7→66.2 | +5.5 (15/18, <0.001) | 59.6→64.8 | +5.3 (14/18, 0.002) | 57.9→60.6 | +2.8 (14/18, 0.029) | <0.001 | <0.001 | -0.2 / +0.1 | <0.001 / <0.001 | 0.016 / <0.001 |
| minimal-7 | 68.6→72.0 | +3.3 (16/18, <0.001) | 67.0→68.7 | +1.7 (11/18, 0.071) | 64.5→67.5 | +3.0 (14/18, 0.006) | <0.001 | 0.001 | -0.0 / +0.4 | <0.001 / 0.001 | 0.002 / <0.001 |
| min-7+AF+HF | 69.1→73.5 | +4.4 (15/18, <0.001) | 68.7→71.1 | +2.4 (12/18, 0.008) | 67.0→67.4 | +0.4 (10/18, 0.771) | <0.001 | 0.001 | +1.0 / +0.6 | <0.001 / <0.001 | 0.002 / <0.001 |
| common-10 | 71.9→75.0 | +3.1 (14/18, 0.007) | 69.1→73.6 | +4.5 (17/18, <0.001) | 67.2→71.4 | +4.2 (16/18, <0.001) | 0.012 | 0.018 | +0.9 / +0.7 | 0.069 / 0.051 | 0.037 / 0.015 |
| sparse | 74.5→77.6 | +3.0 (13/18, 0.020) | 71.9→74.8 | +2.9 (15/18, 0.005) | 70.4→72.4 | +1.9 (10/18, 0.192) | 0.026 | 0.032 | +0.1 / -0.0 | 0.008 / 0.004 | 0.039 / 0.039 |
| sparse, 25% dropout | 72.8→75.9 | +3.1 (15/18, 0.004) | 69.6→72.5 | +3.0 (17/18, 0.003) | 67.6→71.0 | +3.4 (15/18, 0.003) | 0.007 | 0.014 | -0.1 / -0.2 | 0.001 / <0.001 | 0.027 / 0.008 |
| sparse, 50% dropout | 70.4→73.4 | +3.0 (14/18, 0.028) | 67.4→70.4 | +2.9 (15/18, 0.002) | 65.3→68.5 | +3.2 (13/18, 0.005) | 0.034 | 0.043 | -0.3 / -0.4 | 0.001 / <0.001 | 0.033 / 0.056 |
| sparse, 75% dropout | 66.5→70.5 | +4.0 (16/18, 0.003) | 63.9→68.3 | +4.4 (18/18, <0.001) | 61.5→65.8 | +4.3 (16/18, 0.002) | 0.006 | 0.011 | +0.0 / -0.1 | <0.001 / <0.001 | 0.016 / 0.006 |
| sparse minus AF | 74.4→78.2 | +3.8 (16/18, 0.010) | 71.0→74.1 | +3.1 (14/18, 0.009) | 70.2→72.3 | +2.1 (13/18, 0.216) | 0.015 | 0.022 | -0.6 / +0.4 | <0.001 / <0.001 | 0.029 / 0.020 |
| hdPS25 | 85.5→87.2 | +1.7 (12/18, 0.072) | 81.8→82.4 | +0.6 (10/18, 0.408) | 81.8→83.6 | +1.8 (14/18, 0.035) | 0.082 | 0.090 | +0.6 / +0.6 | 0.222 / 0.208 | 0.064 / 0.140 |
| hdPS50 | 87.0→89.0 | +1.9 (12/18, 0.012) | 82.9→84.1 | +1.1 (13/18, 0.141) | 84.4→84.7 | +0.2 (11/18, 0.694) | 0.017 | 0.025 | +0.3 / +0.1 | 0.031 / 0.046 | 0.045 / 0.024 |
| hdPS200 | 90.6→90.5 | -0.1 (7/18, 0.869) | 86.4→85.9 | -0.4 (10/18, 0.480) | 86.4→86.9 | +0.5 (8/18, 0.509) | 0.869 | 0.869 | -0.3 / +0.4 | 0.592 / 0.358 | 0.906 / 0.939 |
| demo / 64 PCs | 60.0→65.3 | +5.3 (15/18, <0.001) | 58.3→64.6 | +6.4 (17/18, <0.001) | 56.8→61.1 | +4.3 (14/18, 0.002) | <0.001 | 0.001 | -0.6 / -0.7 | <0.001 / <0.001 | 0.004 / <0.001 |
| demo / caliper 0.1 | 60.2→65.2 | +5.1 (15/18, <0.001) | 57.1→63.1 | +6.1 (16/18, <0.001) | 56.2→60.4 | +4.1 (14/18, 0.001) | <0.001 | 0.002 | -0.7 / +0.1 | <0.001 / <0.001 | 0.008 / <0.001 |
| demo / 1:3 matching | 60.3→65.5 | +5.2 (16/18, <0.001) | 59.0→63.5 | +4.5 (16/18, 0.003) | 57.1→61.1 | +4.0 (14/18, <0.001) | <0.001 | <0.001 | -0.9 / -0.0 | <0.001 / <0.001 | 0.002 / <0.001 |
| demo / overlap weights | 60.3→65.2 | +4.9 (17/18, <0.001) | 58.5→63.2 | +4.7 (16/18, <0.001) | 57.7→61.7 | +4.1 (14/18, <0.001) | <0.001 | <0.001 | +0.0 / -0.2 | <0.001 / <0.001 | 0.002 / <0.001 |
| minimal-7 / 64 PCs | 68.6→73.4 | +4.7 (16/18, <0.001) | 67.0→70.0 | +3.0 (12/18, 0.024) | 64.5→68.6 | +4.1 (15/18, 0.012) | <0.001 | 0.002 | -1.0 / -0.5 | <0.001 / <0.001 | 0.010 / <0.001 |
| minimal-7 / caliper 0.1 | 69.0→72.3 | +3.3 (16/18, <0.001) | 67.8→69.4 | +1.6 (12/18, 0.086) | 64.7→68.0 | +3.3 (13/18, 0.004) | 0.001 | 0.002 | +0.0 / +0.4 | 0.003 / 0.002 | 0.004 / <0.001 |
| minimal-7 / 1:3 matching | 68.4→72.3 | +3.9 (18/18, <0.001) | 66.2→69.7 | +3.4 (16/18, <0.001) | 65.3→67.9 | +2.6 (13/18, 0.021) | <0.001 | <0.001 | +0.3 / +0.3 | <0.001 / <0.001 | 0.002 / <0.001 |
| minimal-7 / overlap weights | 69.5→73.2 | +3.6 (17/18, <0.001) | 67.8→70.7 | +2.9 (16/18, <0.001) | 66.1→68.8 | +2.7 (14/18, 0.003) | <0.001 | <0.001 | +0.3 / +0.1 | <0.001 / <0.001 | 0.002 / <0.001 |
| sparse / 64 PCs | 74.5→78.6 | +4.1 (14/18, 0.006) | 71.9→75.3 | +3.4 (16/18, <0.001) | 70.4→73.3 | +2.9 (13/18, 0.057) | 0.010 | 0.018 | -0.0 / +0.8 | 0.008 / 0.004 | 0.020 / 0.012 |
| sparse / caliper 0.1 | 75.2→78.1 | +2.9 (14/18, 0.034) | 72.4→75.2 | +2.8 (15/18, 0.019) | 71.0→73.2 | +2.2 (10/18, 0.177) | 0.040 | 0.050 | -1.0 / -0.7 | <0.001 / <0.001 | 0.047 / 0.068 |
| sparse / 1:3 matching | 74.6→77.9 | +3.3 (16/18, <0.001) | 72.4→75.4 | +3.0 (14/18, 0.003) | 70.8→73.1 | +2.3 (14/18, 0.030) | <0.001 | 0.001 | +0.4 / +0.1 | 0.004 / <0.001 | 0.010 / <0.001 |
| sparse / overlap weights | 75.6→79.2 | +3.6 (17/18, <0.001) | 73.5→76.4 | +2.9 (16/18, <0.001) | 71.5→74.5 | +3.0 (16/18, <0.001) | <0.001 | <0.001 | +0.0 / +0.1 | <0.001 / <0.001 | 0.004 / <0.001 |
| sparse, 50% dropout / 64 PCs | 70.4→74.3 | +4.0 (15/18, 0.005) | 67.4→72.2 | +4.8 (17/18, <0.001) | 65.3→68.5 | +3.2 (15/18, 0.002) | 0.009 | 0.018 | -0.7 / -0.9 | <0.001 / <0.001 | 0.016 / 0.010 |
| sparse, 50% dropout / caliper 0.1 | 70.6→73.8 | +3.2 (13/18, 0.026) | 67.4→70.7 | +3.3 (15/18, <0.001) | 65.2→68.5 | +3.3 (15/18, 0.002) | 0.033 | 0.040 | -0.2 / -0.6 | 0.002 / <0.001 | 0.035 / 0.052 |
| sparse, 50% dropout / 1:3 matching | 70.7→73.6 | +2.9 (16/18, 0.005) | 68.5→71.5 | +3.0 (17/18, <0.001) | 65.8→69.1 | +3.3 (14/18, 0.001) | 0.009 | 0.018 | -0.3 / -0.4 | <0.001 / <0.001 | 0.031 / 0.011 |
| sparse, 50% dropout / overlap weights | 70.6→74.4 | +3.8 (18/18, <0.001) | 69.2→72.5 | +3.4 (17/18, <0.001) | 66.4→70.0 | +3.6 (17/18, <0.001) | <0.001 | <0.001 | -0.0 / +0.1 | <0.001 / <0.001 | 0.002 / <0.001 |
| hdPS200 / 64 PCs | 90.6→91.6 | +1.0 (10/18, 0.130) | 86.4→86.7 | +0.4 (11/18, 0.574) | 86.4→86.2 | -0.2 (8/18, 0.761) | 0.134 | 0.148 | +0.2 / -0.1 | 0.078 / 0.077 | 0.061 / 0.255 |
| hdPS200 / caliper 0.1 | 91.1→90.0 | -1.0 (5/18, 0.086) | 86.0→84.9 | -1.1 (7/18, 0.189) | 86.0→86.7 | +0.8 (8/18, 0.394) | 0.092 | 0.104 | -0.7 / -0.6 | 0.576 / 0.408 | 0.070 / 0.170 |
| hdPS200 / 1:3 matching | 90.4→91.7 | +1.3 (12/18, 0.016) | 86.5→87.8 | +1.3 (12/18, 0.057) | 87.0→87.8 | +0.8 (9/18, 0.222) | 0.021 | 0.026 | +0.7 / +0.8 | 0.224 / 0.451 | 0.002 / 0.031 |
| hdPS200 / overlap weights | 92.0→92.8 | +0.8 (12/18, 0.079) | 88.5→88.9 | +0.4 (8/18, 0.455) | 89.1→89.3 | +0.2 (9/18, 0.372) | 0.087 | 0.096 | -0.1 / -0.1 | 0.008 / 0.044 | 0.236 / 0.158 |

## Grid: % of held-out variables with |SMD| < 0.1, expanded non-ECG-proximal panel, 8 physiology trials

q = BH over cells within half × subset × panel; q global = BH over cells × both panels (within half, subset).

| cell | full base→ECG | full d (k, p) | A base→ECG | A d (k, p) | B base→ECG | B d (k, p) | full q | full q global | shuf−base / noise−base d | ECG−shuf / ECG−noise p | cluster p / LOO |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none (ECG only) | 60.3→66.5 | +6.2 (6/8, 0.047) | 57.9→60.4 | +2.6 (6/8, 0.305) | 56.8→61.9 | +5.1 (5/8, 0.094) | 0.069 | 0.064 | -1.8 / +0.2 | 0.016 / 0.016 | 0.094 / 0.094 |
| demo | 60.0→66.6 | +6.6 (7/8, 0.016) | 56.8→63.2 | +6.3 (7/8, 0.023) | 56.2→59.0 | +2.8 (7/8, 0.086) | 0.031 | 0.026 | -0.0 / +1.2 | 0.023 / 0.031 | 0.031 / 0.031 |
| demo+race | 59.5→66.7 | +7.1 (7/8, 0.016) | 58.2→63.6 | +5.4 (6/8, 0.094) | 55.6→59.0 | +3.4 (6/8, 0.156) | 0.031 | 0.026 | +0.8 / +0.9 | 0.023 / 0.031 | 0.031 / 0.031 |
| minimal-7 | 65.8→70.5 | +4.7 (7/8, 0.023) | 63.8→66.3 | +2.5 (6/8, 0.156) | 58.9→64.7 | +5.8 (7/8, 0.016) | 0.040 | 0.037 | -0.4 / -0.1 | 0.008 / 0.031 | 0.031 / 0.047 |
| min-7+AF+HF | 65.4→71.7 | +6.3 (7/8, 0.023) | 65.3→69.3 | +4.0 (7/8, 0.039) | 60.6→64.2 | +3.5 (6/8, 0.031) | 0.040 | 0.037 | +0.9 / +0.7 | 0.016 / 0.008 | 0.031 / 0.047 |
| common-10 | 65.8→72.1 | +6.4 (8/8, 0.008) | 64.2→69.1 | +4.9 (8/8, 0.008) | 59.1→66.8 | +7.7 (8/8, 0.008) | 0.024 | 0.018 | +2.2 / +1.4 | 0.117 / 0.055 | 0.016 / 0.016 |
| sparse | 67.4→72.8 | +5.4 (7/8, 0.055) | 65.7→70.9 | +5.1 (8/8, 0.008) | 63.2→67.0 | +3.8 (5/8, 0.219) | 0.072 | 0.072 | +0.2 / +0.2 | 0.008 / 0.039 | 0.078 / 0.109 |
| sparse, 25% dropout | 67.4→72.4 | +5.0 (6/8, 0.062) | 63.6→68.8 | +5.2 (8/8, 0.008) | 59.4→65.4 | +6.0 (6/8, 0.031) | 0.076 | 0.079 | -0.6 / -1.1 | 0.016 / 0.016 | 0.094 / 0.125 |
| sparse, 50% dropout | 65.8→70.7 | +4.9 (6/8, 0.133) | 62.1→67.2 | +5.1 (7/8, 0.023) | 58.6→64.2 | +5.6 (6/8, 0.047) | 0.146 | 0.149 | -0.7 / -0.8 | 0.023 / 0.016 | 0.141 / 0.266 |
| sparse, 75% dropout | 63.2→69.3 | +6.1 (7/8, 0.047) | 59.9→66.8 | +6.8 (8/8, 0.008) | 56.2→62.6 | +6.4 (8/8, 0.008) | 0.069 | 0.064 | -0.7 / -0.3 | 0.016 / 0.008 | 0.078 / 0.094 |
| sparse minus AF | 68.3→73.4 | +5.1 (7/8, 0.117) | 64.3→70.9 | +6.6 (8/8, 0.008) | 62.9→65.6 | +2.7 (5/8, 0.430) | 0.133 | 0.135 | -1.5 / -0.9 | 0.008 / 0.016 | 0.172 / 0.234 |
| hdPS25 | 80.8→84.3 | +3.5 (7/8, 0.062) | 76.5→78.4 | +1.9 (6/8, 0.055) | 75.7→78.5 | +2.8 (6/8, 0.102) | 0.076 | 0.079 | +0.7 / +0.9 | 0.062 / 0.070 | 0.094 / 0.125 |
| hdPS50 | 81.7→85.6 | +3.9 (8/8, 0.008) | 77.8→80.0 | +2.3 (6/8, 0.102) | 79.3→80.0 | +0.7 (5/8, 0.625) | 0.024 | 0.018 | +0.7 / +0.5 | 0.047 / 0.047 | 0.016 / 0.016 |
| hdPS200 | 86.5→87.2 | +0.7 (4/8, 0.344) | 82.2→82.4 | +0.2 (5/8, 0.734) | 82.4→82.2 | -0.2 (3/8, 0.859) | 0.354 | 0.354 | +0.6 / +1.0 | 0.953 / 0.727 | 0.438 / 0.688 |
| demo / 64 PCs | 60.0→66.8 | +6.8 (7/8, 0.016) | 56.8→64.7 | +7.9 (7/8, 0.047) | 56.2→59.4 | +3.2 (6/8, 0.109) | 0.031 | 0.026 | -1.2 / -1.0 | 0.016 / 0.031 | 0.031 / 0.031 |
| demo / caliper 0.1 | 59.7→66.3 | +6.6 (7/8, 0.016) | 56.6→62.7 | +6.1 (7/8, 0.023) | 55.4→59.2 | +3.8 (6/8, 0.055) | 0.031 | 0.026 | +0.2 / +1.3 | 0.023 / 0.016 | 0.031 / 0.031 |
| demo / 1:3 matching | 60.4→66.5 | +6.2 (7/8, 0.016) | 57.2→63.1 | +5.9 (7/8, 0.055) | 56.4→61.6 | +5.2 (6/8, 0.031) | 0.031 | 0.026 | -1.4 / -0.4 | 0.008 / 0.008 | 0.031 / 0.031 |
| demo / overlap weights | 59.7→66.9 | +7.1 (8/8, 0.008) | 57.9→63.0 | +5.2 (7/8, 0.031) | 55.7→62.0 | +6.4 (7/8, 0.016) | 0.024 | 0.018 | +0.3 / +0.0 | 0.008 / 0.008 | 0.016 / 0.016 |
| minimal-7 / 64 PCs | 65.8→72.9 | +7.0 (8/8, 0.008) | 63.8→66.7 | +2.9 (5/8, 0.219) | 58.9→67.5 | +8.6 (8/8, 0.008) | 0.024 | 0.018 | -0.5 / -1.0 | 0.008 / 0.008 | 0.016 / 0.016 |
| minimal-7 / caliper 0.1 | 65.7→71.3 | +5.6 (8/8, 0.008) | 64.0→66.6 | +2.6 (6/8, 0.148) | 58.8→64.3 | +5.6 (6/8, 0.039) | 0.024 | 0.018 | -0.5 / +0.1 | 0.008 / 0.016 | 0.016 / 0.016 |
| minimal-7 / 1:3 matching | 65.6→71.3 | +5.8 (8/8, 0.008) | 63.3→67.7 | +4.5 (7/8, 0.023) | 60.7→65.6 | +4.9 (7/8, 0.062) | 0.024 | 0.018 | +0.3 / +0.7 | 0.008 / 0.008 | 0.016 / 0.016 |
| minimal-7 / overlap weights | 66.1→71.5 | +5.4 (8/8, 0.008) | 63.9→67.8 | +3.9 (8/8, 0.008) | 60.9→65.4 | +4.5 (7/8, 0.047) | 0.024 | 0.018 | +0.2 / +0.1 | 0.016 / 0.008 | 0.016 / 0.016 |
| sparse / 64 PCs | 67.4→74.8 | +7.4 (7/8, 0.023) | 65.7→70.3 | +4.6 (7/8, 0.016) | 63.2→68.5 | +5.3 (6/8, 0.094) | 0.040 | 0.037 | -1.6 / +1.6 | 0.008 / 0.023 | 0.031 / 0.047 |
| sparse / caliper 0.1 | 68.1→72.8 | +4.7 (7/8, 0.102) | 66.4→70.4 | +4.0 (7/8, 0.039) | 62.5→67.4 | +4.9 (5/8, 0.172) | 0.119 | 0.119 | -1.3 / -1.0 | 0.008 / 0.031 | 0.141 / 0.203 |
| sparse / 1:3 matching | 68.4→73.8 | +5.4 (8/8, 0.008) | 66.6→72.1 | +5.4 (8/8, 0.008) | 62.8→67.3 | +4.5 (6/8, 0.047) | 0.024 | 0.018 | +0.2 / -0.0 | 0.016 / 0.016 | 0.016 / 0.016 |
| sparse / overlap weights | 68.5→74.6 | +6.1 (8/8, 0.008) | 67.1→71.6 | +4.5 (8/8, 0.008) | 62.9→68.2 | +5.3 (8/8, 0.008) | 0.024 | 0.018 | -0.2 / -0.2 | 0.008 / 0.008 | 0.016 / 0.016 |
| sparse, 50% dropout / 64 PCs | 65.8→71.4 | +5.6 (7/8, 0.055) | 62.1→68.7 | +6.6 (8/8, 0.008) | 58.6→64.4 | +5.9 (8/8, 0.008) | 0.072 | 0.072 | -1.1 / -1.3 | 0.008 / 0.008 | 0.094 / 0.109 |
| sparse, 50% dropout / caliper 0.1 | 65.6→70.7 | +5.0 (6/8, 0.148) | 62.0→67.9 | +5.9 (7/8, 0.016) | 57.7→63.7 | +6.1 (7/8, 0.016) | 0.158 | 0.163 | -0.9 / -1.0 | 0.016 / 0.016 | 0.156 / 0.297 |
| sparse, 50% dropout / 1:3 matching | 66.4→71.2 | +4.8 (7/8, 0.039) | 63.8→68.3 | +4.5 (8/8, 0.008) | 59.3→65.1 | +5.8 (7/8, 0.016) | 0.063 | 0.057 | -0.8 / -1.0 | 0.016 / 0.008 | 0.062 / 0.078 |
| sparse, 50% dropout / overlap weights | 65.8→71.5 | +5.7 (8/8, 0.008) | 64.5→69.8 | +5.3 (8/8, 0.008) | 59.2→65.5 | +6.3 (8/8, 0.008) | 0.024 | 0.018 | +0.0 / +0.2 | 0.008 / 0.008 | 0.016 / 0.016 |
| hdPS200 / 64 PCs | 86.5→89.1 | +2.5 (7/8, 0.055) | 82.2→84.1 | +1.9 (7/8, 0.016) | 82.4→81.6 | -0.8 (3/8, 0.547) | 0.072 | 0.072 | +1.0 / +0.6 | 0.117 / 0.094 | 0.078 / 0.109 |
| hdPS200 / caliper 0.1 | 87.5→86.7 | -0.8 (3/8, 0.477) | 81.7→81.7 | +0.0 (4/8, 1.000) | 81.4→82.5 | +1.1 (4/8, 0.641) | 0.477 | 0.487 | -0.9 / -0.9 | 0.938 / 1.000 | 0.422 / 0.938 |
| hdPS200 / 1:3 matching | 86.9→89.7 | +2.8 (8/8, 0.008) | 82.9→85.3 | +2.4 (7/8, 0.055) | 83.3→83.9 | +0.6 (6/8, 0.484) | 0.024 | 0.018 | +1.6 / +1.4 | 0.242 / 0.234 | 0.016 / 0.016 |
| hdPS200 / overlap weights | 88.9→90.4 | +1.5 (7/8, 0.016) | 85.0→86.1 | +1.1 (4/8, 0.312) | 85.5→85.6 | +0.2 (4/8, 0.688) | 0.031 | 0.026 | -0.0 / +0.1 | 0.008 / 0.062 | 0.031 / 0.031 |

## Grid: other threshold metrics (full cohort, 18 trials; base → ECG, sign-flip p)

| cell | p58_pct_lt05 | p58_pct_gt20 | p58_max_smd | p58_keyphys_all | xo_pct_gt20 | xo_max_smd |
|---|---|---|---|---|---|---|
| none (ECG only) | 31.2→35.9 (0.003) | 23.4→17.1 (<0.001) | 0.588→0.560 (0.118) | 0.0→0.0 (1.000) | 14.8→12.3 (0.002) | 0.608→0.570 (0.052) |
| demo | 31.0→36.5 (0.001) | 22.5→15.5 (<0.001) | 0.567→0.515 (0.182) | 0.0→0.0 (1.000) | 14.8→11.5 (<0.001) | 0.547→0.473 (0.002) |
| demo+race | 30.8→34.2 (0.064) | 23.2→15.7 (<0.001) | 0.596→0.512 (0.053) | 0.0→0.0 (1.000) | 14.2→11.0 (<0.001) | 0.533→0.475 (0.015) |
| minimal-7 | 29.5→34.1 (0.020) | 20.3→15.0 (<0.001) | 0.540→0.520 (0.558) | 0.0→0.0 (1.000) | 9.9→7.5 (<0.001) | 0.570→0.534 (0.078) |
| min-7+AF+HF | 34.2→39.8 (0.002) | 16.5→13.3 (0.010) | 0.579→0.484 (<0.001) | 0.0→0.0 (1.000) | 8.5→6.8 (0.008) | 0.587→0.548 (0.323) |
| common-10 | 35.0→38.8 (0.045) | 15.3→12.4 (0.106) | 0.562→0.525 (0.425) | 0.0→0.0 (1.000) | 6.3→5.1 (0.081) | 0.464→0.463 (0.933) |
| sparse | 36.9→37.6 (0.587) | 15.0→11.9 (0.006) | 0.540→0.531 (0.849) | 0.0→0.0 (1.000) | 5.9→4.3 (0.022) | 0.459→0.441 (0.438) |
| sparse, 25% dropout | 35.6→40.1 (0.002) | 16.1→12.6 (<0.001) | 0.567→0.524 (0.109) | 0.0→0.0 (1.000) | 6.6→4.9 (<0.001) | 0.484→0.482 (0.970) |
| sparse, 50% dropout | 34.0→38.6 (<0.001) | 17.8→14.1 (<0.001) | 0.561→0.533 (0.249) | 0.0→0.0 (1.000) | 7.9→6.1 (0.007) | 0.499→0.457 (<0.001) |
| sparse, 75% dropout | 32.2→37.6 (<0.001) | 19.7→14.4 (<0.001) | 0.550→0.528 (0.364) | 0.0→0.0 (1.000) | 10.2→7.8 (<0.001) | 0.501→0.501 (0.986) |
| sparse minus AF | 37.3→39.3 (0.097) | 14.4→11.1 (0.004) | 0.519→0.521 (0.970) | 0.0→5.6 (1.000) | 5.9→4.1 (<0.001) | 0.499→0.450 (0.072) |
| hdPS25 | 39.8→45.0 (<0.001) | 11.7→9.3 (0.028) | 0.526→0.482 (0.085) | 5.6→11.1 (1.000) | 2.7→2.2 (0.127) | 0.415→0.386 (0.069) |
| hdPS50 | 44.0→46.1 (0.362) | 11.2→9.5 (0.107) | 0.463→0.461 (0.965) | 5.6→11.1 (1.000) | 2.3→1.4 (0.001) | 0.438→0.396 (0.290) |
| hdPS200 | 43.4→46.6 (0.098) | 10.1→8.6 (0.141) | 0.424→0.427 (0.933) | 0.0→16.7 (0.250) | 1.2→1.1 (0.420) | 0.418→0.442 (0.303) |
| demo / 64 PCs | 31.0→36.9 (0.006) | 22.5→14.8 (<0.001) | 0.567→0.582 (0.810) | 0.0→0.0 (1.000) | 14.8→10.8 (<0.001) | 0.547→0.477 (<0.001) |
| demo / caliper 0.1 | 30.5→36.1 (<0.001) | 22.4→15.4 (<0.001) | 0.560→0.519 (0.230) | 5.6→0.0 (1.000) | 15.1→11.7 (<0.001) | 0.548→0.468 (<0.001) |
| demo / 1:3 matching | 30.9→38.4 (0.001) | 21.8→14.5 (<0.001) | 0.560→0.515 (0.174) | 0.0→0.0 (1.000) | 14.8→11.5 (<0.001) | 0.534→0.488 (0.027) |
| demo / overlap weights | 32.2→38.4 (0.003) | 21.7→14.9 (<0.001) | 0.550→0.511 (0.015) | 0.0→0.0 (1.000) | 14.2→11.6 (<0.001) | 0.528→0.489 (0.006) |
| minimal-7 / 64 PCs | 29.5→37.0 (<0.001) | 20.3→14.3 (<0.001) | 0.540→0.590 (0.497) | 0.0→0.0 (1.000) | 9.9→7.2 (<0.001) | 0.570→0.562 (0.860) |
| minimal-7 / caliper 0.1 | 29.8→34.7 (0.013) | 20.2→14.5 (<0.001) | 0.540→0.514 (0.468) | 0.0→0.0 (1.000) | 9.8→7.3 (<0.001) | 0.570→0.542 (0.216) |
| minimal-7 / 1:3 matching | 30.1→36.5 (<0.001) | 20.2→14.5 (<0.001) | 0.539→0.514 (0.175) | 0.0→0.0 (1.000) | 9.5→7.6 (0.001) | 0.565→0.548 (0.336) |
| minimal-7 / overlap weights | 31.4→39.4 (<0.001) | 18.9→14.2 (0.002) | 0.538→0.507 (0.042) | 0.0→0.0 (1.000) | 9.1→7.2 (<0.001) | 0.567→0.536 (0.002) |
| sparse / 64 PCs | 36.9→39.2 (0.250) | 15.0→10.7 (<0.001) | 0.540→0.483 (0.093) | 0.0→5.6 (1.000) | 5.9→3.9 (0.002) | 0.459→0.455 (0.849) |
| sparse / caliper 0.1 | 37.0→37.0 (1.000) | 14.4→11.1 (0.006) | 0.534→0.509 (0.427) | 0.0→0.0 (1.000) | 5.9→4.4 (0.023) | 0.439→0.439 (0.996) |
| sparse / 1:3 matching | 37.1→40.7 (0.054) | 13.5→11.8 (0.049) | 0.533→0.511 (0.265) | 0.0→0.0 (1.000) | 5.4→4.4 (0.077) | 0.468→0.420 (0.019) |
| sparse / overlap weights | 36.6→41.3 (<0.001) | 12.6→10.2 (0.004) | 0.507→0.485 (0.087) | 0.0→0.0 (1.000) | 5.4→4.3 (0.002) | 0.446→0.427 (0.023) |
| sparse, 50% dropout / 64 PCs | 34.0→38.8 (0.001) | 17.8→13.4 (<0.001) | 0.561→0.537 (0.511) | 0.0→0.0 (1.000) | 7.9→5.7 (<0.001) | 0.499→0.453 (0.040) |
| sparse, 50% dropout / caliper 0.1 | 34.9→38.8 (0.020) | 17.4→13.7 (<0.001) | 0.565→0.539 (0.312) | 0.0→0.0 (1.000) | 8.1→6.0 (0.003) | 0.505→0.464 (0.002) |
| sparse, 50% dropout / 1:3 matching | 35.0→39.3 (<0.001) | 17.3→13.4 (<0.001) | 0.534→0.510 (0.311) | 0.0→0.0 (1.000) | 7.9→6.2 (<0.001) | 0.479→0.449 (0.010) |
| sparse, 50% dropout / overlap weights | 35.0→39.7 (0.002) | 16.6→12.5 (<0.001) | 0.526→0.497 (0.040) | 0.0→0.0 (1.000) | 7.6→5.8 (<0.001) | 0.481→0.459 (0.028) |
| hdPS200 / 64 PCs | 43.4→47.8 (0.055) | 10.1→8.6 (0.277) | 0.424→0.428 (0.928) | 0.0→22.2 (0.125) | 1.2→1.2 (0.839) | 0.418→0.420 (0.942) |
| hdPS200 / caliper 0.1 | 44.1→48.1 (0.018) | 10.3→8.3 (0.148) | 0.416→0.429 (0.774) | 5.6→16.7 (0.500) | 1.2→1.1 (0.352) | 0.411→0.444 (0.223) |
| hdPS200 / 1:3 matching | 45.7→49.4 (0.005) | 8.9→7.6 (0.029) | 0.434→0.427 (0.767) | 5.6→16.7 (0.500) | 1.2→1.1 (0.409) | 0.400→0.387 (0.351) |
| hdPS200 / overlap weights | 46.3→49.8 (0.007) | 8.9→7.2 (0.019) | 0.416→0.401 (0.335) | 16.7→22.2 (1.000) | 1.1→1.0 (0.641) | 0.390→0.382 (0.349) |

## Grid: engine metrics (ECG − base, 18 trials; standard sweep summary)

Heat map: `docs/v16/S8_HEADLINE_heatmap.png`.

| cell | absd full d (p) | absd A/B p | z2 full d (p) | z2 A/B p | mean_smd full d (p) | mean_smd A/B p | cstat full d (p) | cstat A/B p | |Δ| q | |Δ| vs shuf/noise p | consistency % base→ECG | φ base→ECG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none (ECG only) | -0.057 (0.032) | <0.001/0.016 | -6.40 (0.001) | <0.001/0.001 | -0.022 (<0.001) | 0.003/<0.001 | -0.024 (<0.001) | <0.001/<0.001 | 0.081 | 0.014/0.013 | 50→67 | 13.84→6.89 |
| demo | -0.057 (0.033) | 0.106/0.125 | -3.66 (0.006) | 0.032/0.083 | -0.023 (<0.001) | 0.003/<0.001 | -0.018 (0.003) | 0.091/<0.001 | 0.081 | 0.083/0.120 | 56→61 | 9.76→6.08 |
| demo+race | -0.054 (0.022) | 0.240/0.013 | -3.71 (0.002) | 0.055/0.010 | -0.023 (<0.001) | 0.032/<0.001 | -0.021 (<0.001) | <0.001/0.011 | 0.081 | 0.179/0.159 | 61→67 | 9.63→5.63 |
| minimal-7 | -0.038 (0.058) | 0.269/0.805 | -2.73 (0.033) | 0.073/0.188 | -0.016 (<0.001) | 0.002/0.003 | -0.016 (<0.001) | 0.017/<0.001 | 0.103 | 0.101/0.007 | 56→61 | 8.17→5.13 |
| min-7+AF+HF | -0.033 (0.071) | 0.959/0.329 | -1.97 (0.039) | 0.201/0.085 | -0.016 (<0.001) | 0.021/0.060 | -0.018 (<0.001) | 0.002/0.047 | 0.121 | 0.013/<0.001 | 61→67 | 7.13→5.14 |
| common-10 | -0.016 (0.520) | 0.177/0.081 | -2.25 (0.035) | 0.029/0.021 | -0.013 (0.014) | 0.002/0.031 | -0.014 (0.049) | 0.125/0.047 | 0.570 | 0.928/0.422 | 61→72 | 6.52→4.04 |
| sparse | -0.020 (0.264) | 0.042/0.231 | -1.40 (0.024) | 0.013/0.030 | -0.007 (0.026) | 0.504/0.033 | -0.013 (0.023) | <0.001/0.055 | 0.346 | 0.088/0.053 | 61→78 | 4.70→3.41 |
| sparse, 25% dropout | -0.038 (0.013) | 0.474/0.094 | -2.20 (0.003) | 0.113/0.037 | -0.014 (<0.001) | 0.002/0.001 | -0.018 (<0.001) | <0.001/0.019 | 0.072 | 0.098/0.038 | 61→76 | 6.20→3.93 |
| sparse, 50% dropout | -0.036 (0.033) | 0.004/0.351 | -2.46 (0.021) | 0.016/0.071 | -0.014 (<0.001) | 0.007/<0.001 | -0.015 (<0.001) | 0.012/<0.001 | 0.081 | 0.033/0.084 | 63→67 | 7.25→4.68 |
| sparse, 75% dropout | -0.047 (0.030) | 0.103/0.081 | -3.25 (0.009) | 0.012/0.025 | -0.019 (<0.001) | <0.001/<0.001 | -0.018 (0.001) | <0.001/<0.001 | 0.081 | 0.058/0.030 | 57→67 | 8.72→5.10 |
| sparse minus AF | -0.054 (0.006) | 0.517/0.101 | -1.68 (0.002) | 0.394/0.059 | -0.009 (<0.001) | 0.075/0.020 | -0.015 (0.006) | 0.016/0.018 | 0.051 | 0.339/0.011 | 61→78 | 5.47→3.76 |
| hdPS25 | +0.004 (0.830) | 0.489/0.091 | -0.55 (0.316) | 0.575/0.068 | -0.010 (<0.001) | 0.013/0.001 | -0.010 (0.020) | 0.083/0.004 | 0.882 | 0.541/0.794 | 61→78 | 3.69→3.13 |
| hdPS50 | -0.025 (0.126) | 0.095/0.002 | -0.94 (0.027) | 0.012/<0.001 | -0.005 (0.161) | 0.030/0.188 | -0.008 (0.029) | 0.041/0.223 | 0.172 | 0.324/0.162 | 61→67 | 3.88→2.80 |
| hdPS200 | -0.002 (0.918) | 0.159/0.079 | -0.56 (0.242) | 0.120/0.067 | -0.010 (0.003) | 0.032/0.285 | -0.007 (0.048) | 0.954/0.028 | 0.918 | 0.678/0.493 | 56→72 | 3.28→2.71 |
| demo / 64 PCs | -0.080 (<0.001) | 0.525/0.108 | -4.61 (<0.001) | 0.067/0.050 | -0.024 (<0.001) | 0.026/<0.001 | -0.019 (0.003) | 0.004/<0.001 | 0.020 | 0.002/0.002 | 56→61 | 9.76→4.91 |
| demo / caliper 0.1 | -0.046 (0.087) | 0.045/0.152 | -3.51 (0.007) | 0.026/0.069 | -0.025 (<0.001) | 0.002/<0.001 | -0.022 (<0.001) | 0.009/0.001 | 0.138 | 0.082/0.094 | 56→61 | 9.86→6.16 |
| demo / 1:3 matching | -0.052 (0.057) | 0.161/0.100 | -4.99 (0.005) | 0.025/0.033 | -0.025 (<0.001) | <0.001/<0.001 | -0.019 (<0.001) | 0.009/<0.001 | 0.103 | 0.101/0.124 | 50→56 | 12.21→6.92 |
| demo / overlap weights | -0.050 (0.037) | 0.013/0.113 | -4.94 (0.002) | <0.001/0.008 | -0.025 (<0.001) | <0.001/<0.001 | -0.023 (<0.001) | <0.001/<0.001 | 0.085 | 0.044/0.031 | 56→61 | 11.64→6.33 |
| minimal-7 / 64 PCs | -0.037 (0.100) | 0.329/0.244 | -2.96 (0.017) | 0.028/0.092 | -0.016 (0.002) | 0.016/<0.001 | -0.023 (<0.001) | 0.001/<0.001 | 0.141 | 0.087/0.007 | 56→61 | 8.17→5.00 |
| minimal-7 / caliper 0.1 | -0.041 (0.043) | 0.301/0.741 | -2.93 (0.021) | 0.062/0.171 | -0.017 (<0.001) | <0.001/0.004 | -0.018 (<0.001) | 0.034/0.007 | 0.090 | 0.084/0.021 | 50→61 | 8.27→5.16 |
| minimal-7 / 1:3 matching | -0.036 (0.033) | 0.021/0.216 | -2.62 (0.013) | 0.002/0.044 | -0.018 (<0.001) | <0.001/<0.001 | -0.015 (<0.001) | <0.001/<0.001 | 0.081 | 0.091/0.009 | 56→56 | 9.21→6.21 |
| minimal-7 / overlap weights | -0.033 (0.050) | 0.006/0.105 | -3.27 (0.005) | 0.002/0.028 | -0.019 (<0.001) | <0.001/<0.001 | -0.017 (<0.001) | <0.001/<0.001 | 0.100 | 0.052/0.045 | 56→61 | 9.05→5.51 |
| sparse / 64 PCs | -0.023 (0.318) | 0.075/0.408 | -1.61 (0.081) | 0.021/0.037 | -0.012 (0.002) | 0.779/0.048 | -0.019 (<0.001) | 0.017/0.029 | 0.398 | 0.142/0.145 | 61→67 | 4.70→3.23 |
| sparse / caliper 0.1 | -0.015 (0.457) | 0.056/0.354 | -1.53 (0.028) | 0.038/0.080 | -0.008 (0.032) | 0.196/0.176 | -0.019 (<0.001) | 0.026/0.022 | 0.517 | 0.110/0.013 | 61→78 | 4.61→3.25 |
| sparse / 1:3 matching | -0.032 (0.003) | 0.221/0.063 | -1.82 (<0.001) | 0.022/0.010 | -0.009 (0.002) | 0.082/0.007 | -0.011 (0.044) | 0.009/0.026 | 0.047 | 0.004/0.053 | 67→72 | 6.01→4.13 |
| sparse / overlap weights | -0.024 (0.011) | 0.091/0.090 | -1.65 (0.005) | 0.023/0.017 | -0.011 (<0.001) | <0.001/<0.001 | -0.017 (<0.001) | <0.001/<0.001 | 0.072 | 0.017/0.004 | 67→78 | 5.29→3.55 |
| sparse, 50% dropout / 64 PCs | -0.055 (0.004) | 0.076/0.243 | -3.35 (0.001) | 0.023/0.020 | -0.017 (<0.001) | 0.002/<0.001 | -0.018 (<0.001) | <0.001/<0.001 | 0.049 | 0.001/<0.001 | 63→72 | 7.25→3.71 |
| sparse, 50% dropout / caliper 0.1 | -0.038 (0.030) | 0.034/0.719 | -2.55 (0.008) | 0.093/0.165 | -0.014 (<0.001) | 0.011/0.003 | -0.018 (<0.001) | 0.002/0.001 | 0.081 | 0.030/0.040 | 63→69 | 7.22→4.55 |
| sparse, 50% dropout / 1:3 matching | -0.030 (0.093) | 0.013/0.153 | -2.66 (0.022) | 0.005/0.016 | -0.015 (<0.001) | <0.001/<0.001 | -0.014 (<0.001) | <0.001/<0.001 | 0.138 | 0.079/0.028 | 61→67 | 8.29→5.33 |
| sparse, 50% dropout / overlap weights | -0.035 (0.024) | 0.074/0.111 | -2.89 (0.004) | 0.010/0.016 | -0.016 (<0.001) | <0.001/<0.001 | -0.019 (<0.001) | <0.001/<0.001 | 0.081 | 0.027/0.016 | 61→69 | 7.84→4.72 |
| hdPS200 / 64 PCs | -0.017 (0.328) | 0.022/0.736 | -0.88 (0.034) | 0.004/0.516 | -0.010 (0.005) | 0.173/0.307 | -0.010 (0.037) | 0.327/0.075 | 0.398 | 0.044/0.463 | 56→78 | 3.28→2.37 |
| hdPS200 / caliper 0.1 | -0.003 (0.868) | 0.436/0.074 | -0.59 (0.205) | 0.265/0.052 | -0.007 (0.012) | 0.321/0.261 | -0.005 (0.345) | 0.289/0.011 | 0.895 | 0.905/0.720 | 61→78 | 3.11→2.49 |
| hdPS200 / 1:3 matching | -0.012 (0.356) | 0.031/0.471 | -0.80 (0.052) | 0.009/0.595 | -0.007 (<0.001) | 0.009/0.215 | -0.009 (<0.001) | 0.077/0.214 | 0.417 | 0.708/0.678 | 56→67 | 3.90→3.07 |
| hdPS200 / overlap weights | -0.013 (0.090) | 0.092/0.946 | -0.73 (0.021) | 0.006/0.187 | -0.006 (<0.001) | 0.011/0.025 | -0.010 (<0.001) | <0.001/<0.001 | 0.138 | 0.170/0.050 | 72→78 | 3.06→2.30 |

## Figures

- `docs/v16/S8_THRESHOLD_grid.png`: ECG gain in % < 0.1 across the grid.

- `docs/v16/S8_HEADLINE_heatmap.png`: engine metrics.

- `docs/v16/S8_LOVEPLOT_demo_cal01_phys.png`

- `docs/v16/S8_LOVEPLOT_min7_phys.png`

- `docs/v16/S8_LOVEPLOT_common10_phys.png`

- `docs/v16/S8_LOVEPLOT_sparse.png`

- `docs/v16/S8_LOVEPLOT_demo_cal01_all18_sens.png`

- `docs/v16/S8_LOVEPLOT_min7_all18_sens.png`

- `docs/v16/S8_LOVEPLOT_common10_all18_sens.png`

## Audit

**(1) Reproduction of engine validation** (full cohort, 18 trials; max |S8 − ENGINE_VALIDATION| over trials; the only non-zero row, sparse, is ALLHAT, the known floating-point near-tie in greedy matching documented in ENGINE_VALIDATION.md):

| arm | d_loghr | d_mean_smd | d_pairs | d_cstat |
|---|---|---|---|---|
| hdPS200 | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |
| hdPS200+ECG | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |
| sparse | 0.00003983 | 0.00020563 | 0.00000000 | 0.00013741 |
| sparse+ECG | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |
| unmatched | 0.00000000 | 0.00000000 | 0.00000000 | 0.00000000 |

**(2) Pair counts** (matching cells, full cohort; arm pairs / base pairs): ECG median 0.999 (5th–95th pct 0.892–1.018); shufECG median 1.000 (5th–95th pct 0.967–1.015); noise median 1.000 (5th–95th pct 0.967–1.014).

**(4) Pre-run check (2 trials, full cohort; `audit_check_results.csv`).** carolina and emperor-preserved-v2, 8 cells (none, demo, sparse, sparse p=0.5, hdPS200, hdPS200 overlap, min-7 64 PCs, sparse 1:3). The sparse / sparse+ECG / hdPS200 / hdPS200+ECG / unmatched log HR, SE, pair counts, mean |SMD| and C-statistic equal ENGINE_VALIDATION exactly. Placebo arms did not systematically beat base, and pair counts were within a few % of base. The 58-panel threshold metrics recompute from the engine's per-variable |SMD|. The expanded-panel |SMD| uses the matched set captured from the same `run_cell` call (the `v13_common.match` / `weights` wrappers record the call's own output, so no re-matching).

**(5) Selection guardrail.**
- Half A was run alone first (`run --halves A`; the only other outputs then were the 2-trial check in (4)).
- `select` wrote `selection.json` at the timestamp shown, and it was committed (git 42f1758, "half-A-only selection") before the full-cohort and half-B runs were launched.
- Selection used only the 58-panel. The round-2 rerun (6) reproduces every 58-panel value exactly (max |Δ| = 0 for log HR, SE, mean |SMD|, C, % < 0.1), so the committed selection stands unchanged. `selection.json` was not regenerated; its copy is in `prev_v1_expanded/`.

**(6) Round-2 audit change to the expanded panel (docs/v16/AUDIT_V16_ROUND2.md §2).** After the first full run, the expanded (xo) panel was rebuilt and ALL halves were re-run (32 workers). The changes:
- Excluded `index_setting_*` (domain index_context) and `zip_*` (current address).
- Excluded `recent_hosp_30d` and `n_inpatient_stays_365` (both count the index admission).
- Moved to the ECG-proximal block, so no longer in the panel: MI/ACS flags (prior_mi_ever, acute_mi_365, acs_365, cci_mi), lab_bnp(+missing) and HF drugs (ARNI, MRA, loop diuretic, digoxin, other HF drug).
- Composite scores are treated as PS-overlapping, and dropped per cell, when the cell's PS contains any of their components (`COMPOSITE` in the script). These are CHA2DS2-VASc(≥2), CHADS2, HAS-BLED(no-drug), Charlson (and age-Charlson), Elixhauser count/vw, Gagne and DCSI. HFRS is dropped whenever the PS has any diagnosis flag.
- Median panel size (full cohort): unmatched 355 → 340 variables, demo 354 → 337, min-7 338 → 318, sparse/hdPS 312 → 294.5.
- Per trial × arm, % < 0.1 changed by up to 4.0 pp. All tables and figures in this document use the corrected (v2) panel. The v1 results are kept in `prev_v1_expanded/`.

**(7) Design notes.**
- 'none' has no PS base. Its base arm is the unmatched cohort, and its placebos are shufECG-only and noise-only matching.
- Dropout cells use `Trial.degraded(p, seed)` for the PS only. Balance is always on the TRUE (undegraded) 58-panel and expanded panel. Every dropout metric is first averaged over seeds 0–2 within each trial.
- 64-PC cells use the same shuffle permutation and 64-d seeded noise (as in S3).
- The physiology subset is 8 trials (comet, paradigm-hf-seq, transform-hf, elite-ii, life, emperor-preserved-v2, east-afnet4, cabana-v2). With k = 8 the smallest attainable exact sign-flip p is 0.0078.
- "keyphys_all" (all available key physiology variables < 0.1) is almost never met in any arm, so it is uninformative.

**(3) Placebo − base across the 34 cells** (full, 18 trials, % < 0.1, 58-panel): shufECG − base mean +0.15 pp (p<0.05 better in 1, worse in 2); noise − base mean +0.08 pp (better 0, worse 1); ECG − base mean +5.19 pp (better 29, worse 0).
