# Where does ECG help? Per-trial patterns across 33 trials (exploratory, 2026-09-27)

**Data.** The per-trial table is `claude-v17-confirm/per_trial_patterns.csv`: 33 trials × P1/P2, full cohort, 58-panel.

**Metrics.**
- **Balance gain** = ECG − base in % of held-out covariates with |SMD| < 0.1.
- **ECG-specific gain** = ECG − shufECG, which removes the dimension/placebo artefact.
- **Gap change** = ECG − base in |Δlog HR| vs RCT.

**Tests.** Group comparisons use permutation tests (20,000 draws, one-sided), without multiplicity correction. Groups are:
- blinded ECG relevance, from `trial_selection.json` (pre-specified by a rater who saw no results);
- AF trials, a post-hoc label.

| PS | Group | n | Balance gain diff (p) | ECG-specific gain diff (p) | Gap change diff (p) |
|---|---|---|---|---|---|
| P1 demo | blinded ECG relevance = high | 8 | +0.4 (0.46) | +2.9 (0.15) | **−0.085 (0.022)** |
| P1 demo | AF trials | 7 | +5.6 (0.070) | **+6.6 (0.012)** | **−0.089 (0.021)** |
| P2 demo+6dx | blinded ECG relevance = high | 8 | +4.0 (0.065) | **+7.0 (0.009)** | −0.039 (0.074) |
| P2 demo+6dx | AF trials | 7 | +2.7 (0.16) | +4.8 (0.063) | −0.013 (0.33) |

**Mean ECG-specific balance gain by domain**
- **P1:**
  - highest: ACS 13.8, AF-OAC 12.1, AF-rhythm 12.1, post-MI 12.1, HF 8.6;
  - lowest: DM 4.4, statin 4.3, HTN 1.3, NSAID 1.7.
- **P2:** AF-rhythm 10.8, HF 5.5, HTN 3.9; everything else ≤ 1.7 (post-MI −13.8, n = 1).

**Other observations**
- **Large placebo-matched gains are not ECG-specific:** REWIND (+25.9 vs shuf +20.7), LODESTAR (+20.7 vs +15.5), AMPLIFY (+20.7 vs +13.8) and VALUE (+8.6 vs +8.6).
- **ECG-specific large gains:**
  - EAST-AFNET 4: +20.7 vs 0
  - ROCKET-AF: +19.0 vs +1.7
  - AFFIRM: +13.8 vs −1.7
  - TRANSFORM-HF: +13.8 vs +1.7
  - PLATO: +8.6 vs −5.2
  - CANVAS: +8.8 vs −5.3
- **Trial size.** Larger trials show larger balance gains (Spearman ρ = 0.38 with log n, p = 0.028), consistent with less noise in the SMDs.
- **Gap change.** Larger baseline gaps shrink more (ρ = −0.65, p < 0.001), consistent with the shrinkage-toward-null mechanism documented in V17_CONFIRMATION_RESULTS.

**Reading**
- ECG's balance and gap gains concentrate in cardiac-substrate questions: AF (rhythm control and anticoagulation), ACS/post-MI and HF.
- The gains are smallest in diabetes, hypertension, statin and NSAID comparisons. There, treatment choice is driven by non-cardiac factors.
- The blinded, pre-specified "high ECG relevance" class shows significantly larger gap reduction (P1) and ECG-specific balance gain (P2).
- This is effect-modification analysis with ~12 tests and no correction, so it is hypothesis-generating.

## Trial emulation by clinical category (exploratory)

**Source.** `claude-v17-confirm/emulation_by_category.csv`.

**Tests.** All tests are one-sided exact sign-flip across the trials in each category.
- The shuffled-RCT test draws benchmarks from all 33 RCTs, 10,000 draws.
- "Consistent" means |z| < 1.96 vs the RCT, using both SEs.

| PS | Category | n | Gap −ECG → +ECG | Closer | p | vs shufECG p | Shuffled-RCT p | z² p | Consistent −→+ |
|---|---|---|---|---|---|---|---|---|---|
| P1 | **AF** (5 old + AFFIRM, AF-CHF) | 7 | **0.437 → 0.317** | **7/7** | **0.008** | **0.016** | **0.035** | **0.008** | **2 → 5** |
| P1 | HTN | 5 | 0.288 → 0.183 | 5/5 | 0.031 | 0.031 | 0.24 | 0.031 | 2 → 3 |
| P1 | HF | 5 | 0.157 → 0.114 | 3/5 | 0.22 | 0.31 | 0.10 | 0.22 | 4 → 4 |
| P1 | Diabetes | 9 | 0.213 → 0.215 | 2/9 | 0.51 | 0.32 | 0.90 | 0.43 | 6 → 6 |
| P1 | ACS/post-MI | 2 | 0.115 → 0.122 | 1/2 | 0.75 | — | 0.70 | — | 2 → 2 |
| P1 | Other (statin, NSAID, VTE, vascular) | 5 | 0.218 → 0.196 | 4/5 | 0.28 | 0.062 | 0.81 | 0.16 | 2 → 4 |
| P1 | Blinded ECG relevance high | 8 | 0.329 → 0.215 | 7/8 | 0.012 | 0.012 | 0.43 | 0.012 | 4 → 6 |
| P2 | AF | 7 | 0.344 → 0.317 | 4/7 | 0.17 | 0.63 | 0.71 | 0.16 | 4 → 5 |
| P2 | HF | 5 | 0.138 → 0.107 | 5/5 | 0.031 | 0.34 | 0.002 | 0.031 | 4 → 4 |
| P2 | Blinded ECG relevance high | 8 | 0.225 → 0.179 | 7/8 | 0.027 | 0.027 | 0.38 | 0.035 | 5 → 6 |

**Reading**
- **AF with a demographics PS.** This is the only category that passes all four checks: significant gap reduction, beats shuffled ECG, trial-specific, and significant z². Every AF emulation moves closer to its RCT, including both new AF trials (AFFIRM 0.16 → 0.04, AF-CHF 0.29 → 0.17). Consistency with the RCT rises from 2/7 to 5/7.
- **Caveats for AF:**
  - The AF grouping is post hoc.
  - There are 7 trials in 2 comparator clusters (anticoagulation, rhythm control).
  - AFFIRM overlaps EAST-AFNET 4.
  - With the 6-diagnosis PS, which includes an AF flag, the AF gain disappears.
- **HTN (P1) and blinded high relevance.** The gains are significant and beat placebo, but they are not trial-specific, i.e. generic shrinkage.
- **HF (P2).** The gain is trial-specific but not placebo-specific.
- **Diabetes and ACS.** No emulation gain.


## Round-4 audit corrections (2026-09-28; docs/v18/AUDIT_ROUND4.md §7)
- **The AF pattern did not replicate in the prespecified v1.8 confirmation** (docs/v18/AF_CONFIRMATION_RESULTS.md: 3/5 closer, p = 0.19; worse with P5).
- The AF-7 shuffled-RCT p depends on the benchmark pool:
  - 0.096 within the 7 trials;
  - 0.032 with 33 RCTs;
  - 0.063 with 38 RCTs.
- The "high ECG relevance" class was prespecified, but the test comparing it was not. Its shuffled-RCT p = 0.43 (generic).
- Code for these tables: `scripts/v17/v17_patterns.py`.
