# S9 covariate-set plan: fixed before any S9 results (2026-09-26)

This plan responds to the PI's request to show where ECG improves balance to |SMD| < 0.1. Selecting covariates by the size of the observed ECG gain would inflate the result, so no set is chosen that way without out-of-sample confirmation. The full held-out panel is always reported next to every subset. Each set is labelled with how it was chosen.

## Set 1: clinically defined ECG-relevant confounders
These are fixed now from mechanism: characteristics a 12-lead ECG plausibly reflects that also drive treatment choice and prognosis. They are included when held out from the PS and available.
- **LV function:** LVEF (obs and echo EF), LV systolic grade, GLS, LV stroke volume index.
- **LV structure:** LVIDd, LVEDVi, LVESVi, IVSd, LVPWd, wall-thickness grade, LV mass (if available).
- **Diastolic and atrial:** LA volume index, LA size grade, E/e', diastolic grade.
- **RV and pulmonary:** RVSP, TAPSE, RV S', RV systolic grade, pulmonary hypertension dx.
- **Neurohormonal and renal:** NT-proBNP, eGFR, creatinine, BUN, hemoglobin.
- **Clinical HF burden:** prior HF hospitalisation (strict pre-index), cardiomyopathy dx, loop diuretic use (if not in the PS or the exposure).

## Set 2: literature-standard held-out set
This set is taken from docs/v16/lit_covariates.json, using priority core + common items that are available and not in the cell's PS. Exposure leaks are excluded.

## Set 3: data-driven, split-sample
1. In half A only, rank held-out variables by the ECG − base gain in trial-averaged |SMD|. Candidates are the full expanded non-proximal panel plus the 58-panel.
2. Take the top 25 and write them to selection_S9.json.
3. Commit the selection before any half-B computation.
4. Report balance on this fixed set in half B and in the full cohort.

## Evaluation
Evaluation uses the S8-selected headline scenarios plus sparse and demo as references. For every set, it reports:
- % of covariates with |SMD| < 0.1 per trial;
- the love-plot count below 0.1;
- mean |SMD|.

Each metric is tested with placebos (shufECG, noise), comparator clustering, leave-one-out and BH-FDR. Love plots are produced per set, plus a domain-level love plot over all domains.
