# v1.7: fixed confirmatory analysis applied to the blinded-rule subsets of the existing 18 trials (2026-09-27)

**Provenance**
- The rule is `docs/v17/TRIAL_SELECTION_RULE.md` and `trial_selection.json` (commit 68a13a5). It was made by a rater that saw no results; its attestation is in the file.
- The analysis is fixed by `docs/v16/V17_CONFIRMATION_PLAN.md` (commit 0e66e3c):
  - P1 = demographics PS; P2 = demographics + HTN/T2D/CAD/AF/obesity/HF;
  - 1:1 caliper 0.2, ±ECG32, with shufECG and noise32 placebos;
  - one-sided exact sign-flip test.
- The numbers reuse the S1 (`r1_demo`) and S10 per-trial estimates, with no re-fitting.

**Caveat.** The rule is blind, but the per-trial results for these 18 trials had already been seen by the analyst, so this is not an out-of-sample confirmation. Only new trials (v1.7 B) provide that.

## Subsets among the 18 analysed trials
- **S_fid (9):** ARISTOTLE, EAST-AFNET 4, CABANA, ROCKET-AF, PLATO, PARADIGM-HF (sequential), RE-LY, ELITE II, CAROLINA.
- **S_both** (fidelity and ECG relevance ≥ medium; 8): S_fid without CAROLINA.
- **S_fid_strict (4):** ARISTOTLE, ROCKET-AF, RE-LY, ELITE II.
- **S_ecg (15)** and **S_ecg_high (6):** listed in `claude-v16-s10-demo6/v17_subsets_existing18.csv`.
- **Not in the 18 analysed trials** (DCP, INVEST, TRITON, PARTNER, ENGAGE-AF): these are pending v1.7 B.

## Results (one-sided p; "better" = ECG improves)

| PS | Subset | n | % held-out \|SMD\| < 0.1 | p | vs shuf / noise | \|Δlog HR\| vs RCT | p | vs shuf / noise |
|---|---|---|---|---|---|---|---|---|
| P1 demographics | all 18 | 18 | 53.8 → 60.2 (14/18) | 0.0001 | 0.0005 / 0.001 | 0.265 → 0.208 (14/18) | 0.017 | 0.041 / 0.060 |
| P1 demographics | **S_both** | 8 | **52.4 → 61.1 (7/8)** | **0.008** | 0.004 / 0.023 | **0.413 → 0.295 (8/8)** | **0.004** | **0.016 / 0.020** |
| P1 demographics | S_fid | 9 | 51.4 → 59.1 (7/9) | 0.008 | 0.004 / 0.012 | 0.368 → 0.270 (8/9) | 0.014 | 0.022 / 0.029 |
| P1 demographics | S_fid_strict | 4 | 45.4 → 53.6 (4/4) | 0.063 (minimum possible) | — | 0.337 → 0.239 (4/4) | 0.063 | — |
| P2 demo+6dx | all 18 | 18 | 60.4 → 64.0 (14/18) | 0.008 | 0.012 / 0.003 | 0.233 → 0.201 | 0.006 | 0.48 / 0.35 (placebo fails) |
| P2 demo+6dx | S_both | 8 | 61.7 → 65.6 (6/8) | 0.086 | — | 0.327 → 0.291 | 0.070 | 0.52 / 0.35 |

**P1 / S_both robustness checks for |Δlog HR|**
- **Benchmark shuffle:** observed −0.119; the null mean is −0.061 with benchmarks shuffled within the 8 trials (p = 0.009) and −0.065 with benchmarks drawn from all 18 (p = 0.004). About half of the gain is trial-specific.
- **Comparator clustering:** p = 0.031 over 5 clusters.
- **Leave-one-out:** max p = 0.008 for |Δ| and 0.016 for % < 0.1.
- **Halves:** for |Δ|, A p = 0.14 and B p = 0.039; for % < 0.1, A p = 0.039 and B p = 0.051.
- **Per trial:** every trial moves closer to its RCT. CABANA contributes the largest single change (1.23 → 0.99). Excluding it, all 7 others still improve (LOO).

## Reading
In the trials that a blinded rater judged high-fidelity and ECG-relevant, adding ECG to a demographics-only PS:
- raised held-out balance by about 9 points of covariates below 0.1;
- moved all 8 emulated HRs closer to their RCTs;
- beat both placebos, and about half the gain is trial-specific.

With the 6-diagnosis PS, the subset gain is not significant, and the |Δ| gain fails the placebo test.

This is the most favourable defensible trial-emulation result so far. Out-of-sample confirmation in the new v1.7 trials is required before it can be called confirmatory.
