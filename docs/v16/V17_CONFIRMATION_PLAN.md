# v1.7 confirmation plan: new trials plus a blinded trial-selection rule (fixed 2026-09-27, before any v1.7 result)

## Purpose
The v1.6 findings are exploratory and post hoc. v1.7 tests them in trials whose results have never been seen, using a trial-selection rule made blind to all results.

## A. Blinded trial-selection rule (route 2)
An independent rater agent sees only design-level facts:
- `scripts/trial_specs.py` specs: arms, gates, exclusions, outcomes, horizon, notes;
- `docs/v14/rct_facts.json` / rct_facts where present;
- general knowledge of the published protocols.

It must not read any audits directory, any `docs/v1*`/`docs/v16` result file, `report.md`, or the presentation. It writes `docs/v17/TRIAL_SELECTION_RULE.md` and `docs/v17/trial_selection.json`, which are committed before any metric is computed on the selected subset. The rule has two layers:
1. **Emulation fidelity.** This is mechanical: RCT-DUPLICATE design flags, comparator and outcome fidelity, and feasibility or precision thresholds based on design-stage quantities only.
2. **ECG-mechanism relevance.** This is an a-priori classification: whether treatment choice and prognosis in that clinical question plausibly depend on cardiac structure, function or rhythm that a 12-lead ECG reflects.

The rule is applied to the existing 18 trials and to every new trial.

## B. New trials
- **Candidates:** further active-comparator cardiovascular RCTs, especially from RCT-DUPLICATE, plus the already-built but unused PARADISE-MI, DCP and INVEST. They are screened for feasibility in the Yale data using counts only.
- **Builds:** new trials are built with the existing pipeline. The pipeline is `trial_specs` → `build_trial_cohort` → `build_core_baseline` → `build_preindex_panel` → ECG selection + BCL → physiology panel → outcomes.
- **Registration:** each new trial's spec, RCT benchmark HR (verified from the publication) and outcome definition are committed before outcome extraction.

## C. Fixed confirmatory analysis (identical code to v1.6; no changes allowed)
- **PS:** P1 = demographics only (age, sex, index year); P2 = demographics + HTN, T2D, CAD, AF, obesity, HF (S10 definition). Each is run ± ECG32, with shufECG and noise32 placebos. Matching is 1:1, caliper 0.2, L2 C = 1.
- **Primary balance endpoint:** per-trial % of held-out covariates with |SMD| < 0.1, on the 58-variable panel.
- **Secondary balance endpoints:** % < 0.1 on the covars2b non-proximal panel, mean |SMD|, and the balance C-statistic.
- **Primary emulation endpoint:** |Δlog HR| vs RCT.
- **Secondary emulation endpoints:** z², consistency, and the benchmark-shuffle permutation.
- **Tests:** exact sign-flip across trials, one-sided in the direction found in v1.6 (ECG better). ECG must beat both placebos. Comparator clustering and leave-one-out are also run.
- **Sets analysed:**
  - (i) new trials only (the confirmation set);
  - (ii) all trials;
  - (iii) the blinded-rule subset of (i) and (ii).
- **Reporting:** results are reported regardless of direction.
