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
