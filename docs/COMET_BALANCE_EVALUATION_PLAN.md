# Required covariate balance evaluation

User requirement, 2026-09-22: improvement in covariate balance is a primary
methodological benchmark objective. Superiority of proposed methods is a hypothesis
to test, not an expected result to engineer. RCT effect agreement remains a separate
evaluation objective; measured balance alone cannot establish causal accuracy.
This document records a required analysis stage. The balance implementation and
matched results do not yet exist; matching/imputation details remain to be frozen.

## Deliverables before effect estimation

- Baseline table by treatment before and after matching, with available sample
  sizes, missingness, means/SDs or appropriate distribution summaries and proportions.
- Absolute standardized mean differences (SMDs) for every prespecified clinical
  covariate, all categorical levels and original missingness indicators. Include
  prespecified nonlinear terms/interactions when used in the propensity model.
- Love plot of before/after SMDs. Proposed review threshold: absolute SMD <0.10 for
  each designated covariate; report every violation. This is a diagnostic threshold,
  not proof of unconfoundedness or an automatic guarantee of acceptable design.
- Continuous-variable variance ratios and distribution checks for skewed variables;
  mean balance alone is insufficient. Explicitly handle constant variables and
  undefined standardized differences rather than silently returning zero.
- Propensity-score overlap and support plots by arm, matched/unmatched counts,
  retention by arm and effective sample size if weights are used. Report which
  patients the matched estimate represents; matching can change the target population.

Use a specified pre-match standardization denominator consistently for before/after
SMDs. For proposed continuous covariates, the pooled pre-match SD is a candidate
convention; binary indicators need an explicit proportion-based convention.
Categorical coding, weights, replacement and matching ratio must be specified before
implementation. Do not substitute independent-sample p-values for balance diagnostics.

## Multiple imputation and model selection

Fit propensity scores and match separately within each imputed dataset under the
frozen plan. Assess balance and retention separately in every dataset; summarize
median and worst absolute SMD, and the fraction exceeding the review threshold.
An average alone must not hide a poorly balanced imputation. Do not apply Rubin's
rules to SMDs. Original missingness indicators stay fixed across imputations.

Model/matching refinements may use prespecified design diagnostics, never outcomes,
trial-effect agreement or a desired effect. Preserve all attempted specifications
and report unresolved balance limitations. Outcome estimation follows the balance
review; passing it cannot rule out unmeasured confounding.

The same reporting interface should later compare clinical PSM, CLMBR-T-assisted
PSM, ECG-assisted PSM and combinations. Where populations differ, report both their
own-population diagnostics and feasible paired common-population comparisons.

## Methodological references

Austin (2009), [Balance diagnostics for comparing the distribution of baseline
covariates between treatment groups in propensity-score matched samples](https://pmc.ncbi.nlm.nih.gov/articles/PMC3472075/).

Austin (2011), [An Introduction to Propensity Score Methods for Reducing the Effects
of Confounding in Observational Studies](https://pmc.ncbi.nlm.nih.gov/articles/PMC3144483/).
These support SMD/distribution diagnostics and caution against balance decisions
based solely on significance tests. The project-specific imputation summaries and
review workflow above remain our proposed analysis specification.

## Fair comparisons across methods

Freeze a common clinical evaluation set before comparing unadjusted groups, clinical
PSM, CLMBR-T, ECG representations and combinations. Report mean and maximum absolute
SMD, fraction below the review threshold, distributional diagnostics and retention
together. A method must not appear superior solely by discarding more patients.
Use common eligible populations and the same matching/estimation settings for
controlled method comparisons; report modality-specific available populations
separately. Keep pre-match standardization denominators fixed within each comparison.

Prespecified additional clinical variables outside model fitting may provide a
secondary representation evaluation. Do not remove essential confounders from the
primary clinical comparator just to create a held-out test. Assess original observed
values and missingness alongside completed-data balance: imputation must not create
an appearance of balance that depends entirely on modeled values.
