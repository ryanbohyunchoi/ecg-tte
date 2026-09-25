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
- **2026-09-25, deviation 1 (summaries).** In the small CAROLINA echo subgroups, the hdPS200 + ECG
  Cox model failed in most replicates, because there were fewer than 5 events or no events in one
  arm. The NaNs from that single trial made the cross-trial means undefined. Plasmode summaries
  now exclude any trial–arm cell with fewer than 80% successful replicates, and the table reports
  the number of trials each contrast used. Pool-vs-pool differences use only the trials valid in
  both pools. This was decided before looking at the affected contrasts, which were blank.
- **2026-09-25, post-hoc addition F (Ryan's question, "ECG alone?").** Added after the v1.4
  results; exploratory.
  - **Arms:**
    - ECG only (the 32 PCs, no other covariate);
    - demographics only (age, sex, index year);
    - demographics + ECG.
  - **Comparators:** unadjusted, sparse, sparse + ECG, clinical PS and R+.
  - **Analyses, all 18 trials:** real-data paired bootstrap (200 replicates; targets the RCT and
    R+) and resampled plasmode (200 replicates, v1.3 scenarios).
  - **Question:** how much confounding does the ECG capture on its own, compared with
    demographics and coded diagnoses?
- **2026-09-25, post-hoc addition G (Ryan).** Directional consistency and closeness metrics in the
  style of RCT-DUPLICATE. Exploratory.
  - **Metrics, per arm:**
    - direction: the same side of HR = 1 as the RCT, over all trials and over RCTs whose CI
      excludes 1;
    - regulatory agreement;
    - share of trials with an emulated HR within 0.8–1.25× the RCT HR;
    - Pearson and Spearman correlation of log HRs;
    - calibration slope.
  - **Subsets:** all trials, closely emulated trials, physiology trials, and trials whose RCT
    result was significant.
  - **Uncertainty:** 95% CIs from the paired bootstrap. Point estimates are from the full cohort,
    imputation 1.
  - **Caution:** metrics based on counts give discrete bootstrap distributions. Their percentile
    CIs can exclude the point estimate, so they are descriptive.
  - Script: `scripts/v14_direction.py`; output: `docs/V14_DIRECTION.md`.

## Independent audit, 2026-09-25: corrections

The audit report is kept in the session scratchpad; its findings are summarised here. Every
correction below was made before the affected results were re-summarised.

1. **Inference.**
   - **The problem.** The within-trial paired bootstrap re-matches on resamples that contain
     duplicate patients. That is not valid for matching estimators (Abadie & Imbens 2008). Its
     distributions were off-centre: the SD of the shift in the paired C1 difference across
     trials was about 0.06, comparable to the effect.
   - **The fix.** Every real-data claim now uses the exact sign-flip test across trials, with
     leave-one-out and without-CABANA ranges. Binary agreement metrics use exact McNemar tests.
     Bootstrap intervals are reported as descriptive only.
   - **Consequence.** These claims are withdrawn pending re-analysis:
     - the precision-weighted analysis (p = 0.02), because its per-trial variances came from the
       bootstrap;
     - the "physiology-trial CI excludes 0" result;
     - "significantly closer" under dropout.
2. **Plasmode.**
   - Resampling with replacement shares the problem in item 1. The primary plasmode is now an
     80% subsample without replacement in each replicate, with PS and matching refitted. It is
     run for v1.3 (`claude-v13-plasmode-ss`), v1.4 dropout (`claude-v14-ss`) and the ECG-only
     arms (`claude-v14-ecgonly/pl-ss`).
   - The earlier versions are reported for comparison.
   - By construction, outcomes are simulated from the clinical-PS covariates. The clinical PS is
     therefore correctly specified in the plasmode; this is now stated explicitly.
3. **EMPEROR-Preserved.** v1 had no type 2 diabetes gate, although its DPP-4i comparator implies
   T2D. Coded diabetes was 51% on SGLT2i vs 81% on DPP-4i, and mean index years were 2022 vs 2018.
   v2 requires E11, is rebuilt through the whole frozen pipeline, and replaces v1 everywhere.
4. **CABANA.** In v1:
   - the ablation arm was restricted to patients with no antiarrhythmic use in the prior year,
     which is a selected group;
   - "serious bleeding" included D62 and R58 in any position, giving a 39% composite event rate
     against about 9% in the RCT.

   v2:
   - applies the comparator washout to the antiarrhythmic arm only (`washout_arms`);
   - defines bleeding as GI or non-traumatic intracranial hospitalisation (K920–K922, I62).

   It is rebuilt through the whole pipeline and replaces v1.
5. **Per-protocol.**
   - Not applicable to the procedure-vs-drug design (CABANA), because the ablation arm has no
     drug orders.
   - For the add-on design (EAST-AFNET 4), rate-control orders in the rhythm-control arm are no
     longer counted as switching (`add_on`). EAST-AFNET 4's v1.3 outcomes and design analyses are
     re-extracted.
6. **Reporting corrections.**
   - "About 20% in physiology trials" should read about 14%.
   - C2 in the plasmode is a slight increase in bias, not "no gain".
   - For C1, the 200 multiverse specifications are 40 distinct ones for the seed-independent
     arms (GBM is seed-dependent). They are reported as such.
   - Dropout also deletes hdPS lab-order flags. These are coded orders, so this is consistent
     with "codes"; stated.
   - Under dropout, R+ is itself degraded, and a single random deletion is used; stated.
   - v1.4 E did not add prior HF hospitalisation to R+; logged as a deviation.
   - The entropy-balancing docstring was wrong, and CABANA's Table-1 values are medians used as
     means; noted.
