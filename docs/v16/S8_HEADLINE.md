# v1.6 S8 headline (selection stage; confirmation pending)

This file records the HALF-A-ONLY selection before any half-B or full-cohort result of the S8 grid was computed. At the time of this commit, `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s8-headline/` contains only half-A results (`results_A.csv`) plus a 2-trial full-cohort engine-reproduction check on 8 cells (`audit_check_results.csv`, used only to verify the code reproduces ENGINE_VALIDATION; not summarised).

## Selection

Rule: Half A only; panel p58; metric = trial-level % of held-out variables with |SMD| < 0.1 (ECG − base, dropout cells averaged over 3 seeds). Eligible scenario = (cell, trial subset) with ECG − base gain > 0, exact sign-flip p < 0.05, and ECG − shufECG > 0 and ECG − noise > 0. Base 'none' (ECG only vs unmatched) excluded from the headline pool (it measures matching vs no matching, not ECG added to a PS); reported descriptively. Rank by gain (descending); take the top 3 with at most one scenario per base (the base's modifier variants and trial subsets compete for its slot).

Selection timestamp: **2026-09-26 23:42:00 EDT**; halves in the results: ['A']; 23 of 68 scenarios eligible.

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
