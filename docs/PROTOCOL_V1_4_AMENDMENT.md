# Protocol v1.4 amendment (2026-09-25): where does the ECG add information? (exploratory)

This amends `docs/PROTOCOL_V1_3_AMENDMENT.md`. Ryan approved it on 2026-09-25. It was registered
before any of these analyses ran and is tagged `protocol-v1.4`. Everything here is **exploratory**.

**Question.** v1.3 showed that the ECG improves balance on measured physiology. It showed only a
small bias reduction with a known truth, and no demonstrable gain in agreement with the RCTs.
v1.4 asks whether the ECG's contribution grows in the settings where it should matter:
- the coded record is thin;
- no echo is available;
- the outcome is driven by physiology;
- the hidden confounder is measured cardiac structure itself.

## Common definitions (unchanged from v1.3 unless stated)

- **Trials.** The 18 trials of the v1.3 combined set: 10 primary and 8 extension.
- **Population.** All initiators, imputation 1, pool split seed 0.
- **Arms.** M1 sparse, M2 sparse + ECG (32 PCs), M3 hdPS200, M4 hdPS200 + ECG, R clinical, R+
  physiology reference.
- **Contrasts.** C1 = M2 vs M1; C2 = M4 vs M3.
- **Tools, both as in v1.3.**
  - Real-data paired bootstrap: 200 replicates; targets the RCT and R+.
  - Resampled plasmode (v1.3 deviation 6): 200 replicates; scenarios `base` and `phys_only`
    unless stated.

## A. Data-poor patients (stratification)

- **Code density.** The number of distinct code features (diagnoses, drugs, procedures) with any
  occurrence in the 365-day pre-index panel.
- **Strata.** Trial-specific tertiles: low, mid and high.
- **Within each stratum.** PS, hdPS ranking and matching are refitted for every arm. The bootstrap
  and the plasmode resample within the stratum. The plasmode outcome model is the full-cohort
  model from v1.3.
- **Hypothesis A.** The ECG's gain (C1, C2) is larger in the low-density tertile than in the high
  one:
  - plasmode bias reduction, low minus high, has a 95% CI above 0; and
  - the bootstrap Δ squared error vs R+, low minus high, has a 95% CI below 0.

## B. Degraded coded data (dropout experiment, same patients)

- **Dropout.** Each patient's recorded diagnosis, drug and procedure codes are deleted at random
  (seeded), each with probability p ∈ {0.5, 0.75, 0.9}. Deletion applies to every code-derived
  input: the sparse diagnosis covariates, the hdPS candidate levels, and the diagnosis covariates
  inside R and R+.
- **Kept as recorded.** Demographics, labs, vitals, echo and the ECG.
- **Plasmode outcomes** are still generated from the true, undegraded covariates.
- **p = 0** is the v1.3 result.
- **Hypothesis B.** The ECG's gain increases with p: plasmode C1/C2 bias reduction at p = 0.75
  minus p = 0 has a 95% CI above 0.

## C. Patients without an echo

- **Scope.** Patients indexed on or after 2016-07-31, when echo coverage is complete.
- **Strata.**
  - *No echo*: no echo measure in the 365 days before index.
  - *Echo*: at least one echo measure in that window.
- **Analysis.** Same as A, within each stratum.
- **Hypothesis C.** The ECG's gain is larger in the no-echo stratum. The criteria are those of A.

## D. Plasmode with echo-measured physiology as the hidden confounder

- **Subcohort.** Patients indexed on or after 2016-07-31 who have at least one measure in the
  LVSTRUCT, LVFUNC, DIAST or RVPULM domains in the 365 days before index.
- **Outcome model.** A Cox model of the real primary outcome on the core covariates plus the
  standardised echo measures of those domains. Missing individual measures are filled with the
  median. Ridge penalty 0.01.
- **Scenarios.**
  - `echo_base`: fitted coefficients.
  - `echo_strong`: echo coefficients × 2.
  - `echo_only`: medications, utilisation and core-9 coefficients set to 0; echo coefficients × 1.
- **Replicates.** 200 resampled replicates. R+ contains the echo measures, so it should be
  approximately unbiased.
- **Hypothesis D.** In `echo_only`, the ECG reduces bias: C1 and C2 bias reduction with 95% CI
  above 0.

## E. A physiology-driven outcome: hospitalisation for heart failure

- **Outcome.** Time to the first inpatient stay after index with an I50 code. Same stay rules as
  v1.2. Censoring at death, the trial horizon and the end of data (2024-12-31). Patients with an
  I50 hospitalisation in the 365 days before index are kept, and that history is part of R+.
- **Why no RCT benchmark.** Most trials do not report this outcome as primary.
- **Targets.**
  - Real data: R+, via the bootstrap.
  - Truth: a plasmode whose outcome model is fitted on this outcome.
- **Hypothesis E.** C1 and C2 plasmode bias reduction has a 95% CI above 0, and the bootstrap Δ
  squared error vs R+ has a 95% CI below 0.

## Reporting

- For each of hypotheses A–E, report whether it is supported. There are 5 hypotheses × 2
  contrasts; no multiplicity adjustment is made, and this is stated.
- Outputs: `audits/claude-v14-*` (restricted) and `docs/V14_SUMMARY.md`.
- The interactive results page (`docs/presentation/ecg_tte_results.html`, aggregate only) is
  updated with these results.

## Deviation log

(dated entries, before summaries)
