# Protocol v1.3 amendment (2026-09-25): exploratory robustness and design-fidelity program

This amends `docs/PROTOCOL_V1.md` (tags `protocol-v1`, `protocol-v1.1`, `protocol-v1.2`).

**Status of these analyses.** Phase 2 has already run (commit 043740e), and its primary results are
final and unchanged. Everything below is **exploratory**. It was registered on 2026-09-25, after the
phase-2 results were seen, and before any of these analyses was run. It is tagged `protocol-v1.3`
before the first run. Deviations found necessary during implementation are logged at the end of
this file, with dates, before the results are summarised.

**Motivation.** H5 was not supported: ECG arms did not agree with the RCTs better than sparse. Three
explanations are possible:
- the design is equivalent;
- low power (10 trials);
- design error that affects every arm equally.

The program separates these. Parts I–II use the existing cohorts. Part III adds trials. CIPHER-EHR
is deferred (Ryan, 2026-09-25).

## Common definitions

- **Arms.** M0 unadjusted, M1 sparse, M2 sparse + ECG (32 BCL PCs), M3 hdPS200, M4 hdPS200 + ECG,
  and R clinical reference, exactly as in v1.1.
- **R+ physiology reference.** R plus the measured physiology panel (every echo domain, NT-proBNP,
  labs). Missing values are median-filled with a missing indicator. Echo values from before
  2016-07-31 are treated as missing (option A).
- **Primary population and outcome.** All initiators; the primary outcome at the trial horizon.
- **Trial sets.** The 10-trial primary set, with each RCT counted once.
- **Contrasts of interest.** C1 = M2 vs M1 and C2 = M4 vs M3.

### Pre-specified decision rules (exploratory)

"ECG improves" is claimed for a contrast only if all of the following hold:
1. **Plasmode (I1).** The pooled bias reduction has a 95% CI that excludes 0 in the base
   physiology-confounding scenario.
2. **Paired bootstrap (I3).** Against the RCT or R+, the cross-trial mean difference in squared
   error has a 95% CI below 0. This is reported for all three targets; RCT and R+ are co-primary for
   this part.
3. **Placebo and dose response.** M2 beats both placebo arms (I4).
4. **Robustness.** The direction holds in ≥ 80% of multiverse specifications (I6) and in every
   leave-one-trial-out set (I7).

If only some rules hold, the claim is reported as partial.

## Part I: tests specific to the ECG (existing 10 trials)

### I1. Plasmode simulation

For each trial, in the primary population with imputation 1:
- Fit a Cox model of the real primary outcome on treatment plus all clinical core covariates
  (demographics, diagnoses, medications, utilisation and the imputed core-9 physiology).
- Keep the real treatment assignment and covariates.
- Simulate event times from the fitted linear predictor and the Breslow baseline hazard, with the
  treatment log-HR set to log(0.8). Censoring is administrative only: the trial horizon and the end
  of data.

Scenarios (physiology multiplier κ, applied to the core-9 coefficients):
- **base:** κ = 1;
- **no physiology confounding:** κ = 0;
- **strong:** κ = 2;
- **null effect:** κ = 1 with HR 1.0.

Design details:
- **Truth.** For each arm, the truth is the marginal HR in that arm's matched population. It is
  computed from counterfactual outcomes under both treatments, which removes non-collapsibility.
- **Replicates.** 200 per scenario. The matched sets are those saved in phase 2 (imputation 1,
  split seed 0); they do not depend on the outcome.
- **Metrics.** Bias, empirical SD, RMSE and 95% CI coverage per arm. The bias reduction of C1 and
  C2 is computed as |bias(M1)| − |bias(M2)|, per trial and pooled; its Monte Carlo 95% CI is
  obtained by resampling replicates.

### I2. Internal physiology reference (R+)

- R+ is an extra matched arm, built with the same matcher.
- Each arm's |log HR − log HR(R+)| is reported alongside the value against R and against the RCT.
- R+ removes design error, because every arm uses the same data.

### I3. Within-trial paired bootstrap

- **Resampling.** 200 bootstrap resamples of each trial cohort (imputation 1). In each resample,
  hdPS ranking, PS fitting and matching are refitted for every arm, and the pair-clustered Cox model
  is refitted. ECG PCs come from the full cohort (unsupervised). The pool split is fixed at seed 0.
- **Targets.**
  - The RCT: drawn as N(log HR, SE²) in each replicate, so its uncertainty is propagated.
  - R and R+: refitted in the same resample.
- **Statistics.**
  - Per trial: the distribution of err(M2)² − err(M1)² and of log HR(M2) − log HR(M1).
  - Across trials: the mean over trials of these differences, with a percentile 95% CI. Trials are
    resampled independently.
  - The same statistics for C2.

### I4. Placebo ECG arms

These run inside I3 and I6:
- sparse + noise32 and hdPS200 + noise32 (Gaussian noise);
- sparse + shuffled ECG and hdPS200 + shuffled ECG (the real ECG PCs, permuted between patients,
  seeded).

Any gain from M2 must exceed the gain from these arms.

### I5. Dose response and a second ECG representation

- ECG PCs: 8, 16, 32 (base) and 64.
- 32 PCs + 5 ECG phenotype scores.
- The 6 PRESENT-SHD logits.
- The second encoder: 32 PCs of the penultimate layer of the PRESENT-SHD LVEF < 40 CNN (TF, CPU).

Each is added to both sparse and hdPS200. Point estimates are computed on the full data (I6
machinery) and the bootstrap distribution in I3.

### I6. Multiverse of analysis choices

Point estimates on the full data. The full factorial of:
- **caliper:** 0.05, 0.1, 0.2 or 0.5 SD;
- **ratio:** 1:1 or 1:3 (greedy, without replacement);
- **estimator:** matching, stabilised IPTW (ATE, trimmed at the 1st/99th PS percentiles), or
  overlap weights;
- **PS model:** L2 logistic with C = 1 (base), C = 0.1 or C = 100, or gradient boosting
  (HistGradientBoosting, default settings, 5-fold cross-fitted);
- **hdPS split seed:** 0–4;
- **imputation:** 1 (base) and 1–5 Rubin-pooled for the base PS model.

Summaries:
- per specification, the cross-trial mean |Δlog HR| vs the RCT and vs R+ for each arm;
- the share of specifications in which C1 and C2 favour the ECG;
- a specification curve.

### I7. Leave-one-trial-out and permutation

- Every cross-trial statistic is recomputed with each trial left out in turn.
- An exact sign-flip permutation test (2¹⁰ = 1,024 flips) of the mean paired difference in squared
  error vs the RCT, for C1 and C2.

### I8. Empirical calibration with expanded negative controls

- The negative-control outcomes are expanded to about 20 (the list is in `trial_specs.NCO_EXT`).
  They are chosen to have no plausible effect of any study drug class.
- Excluded on pharmacological grounds: bleeding outcomes (because of anticoagulants and
  antiplatelets), gout (diuretics), angioedema (ACEi/ARNI), hypoglycaemia, genital infection and
  ketoacidosis (SGLT2i), falls/syncope/hypotension (antihypertensives), and hyperkalaemia.
- Outcomes are extracted with the v1.2 rules: the event must be new after index, with no event in
  the prior 365 days.
- For each arm and trial, the systematic-error model is b_i ~ N(μ, σ² + se_i²), fitted by maximum
  likelihood. If fewer than 8 negative controls have ≥ 11 events, it is pooled across trials.
- The primary estimates are then calibrated (shift by μ, SE √(se² + σ²)), and every agreement
  metric (including the SE-aware metrics) is recomputed.

### I9. E-values

For each arm and trial, the E-value for the ratio HR_emulated / HR_RCT: how much unmeasured
confounding would be needed to explain the disagreement.

## Part II: closer to the trial design (existing trials)

### II1. Transport to the RCT's Table 1

- In each arm's matched cohort, entropy-balancing weights make the matched sample's means equal
  the RCT's published baseline means.
- Variables are used when available in both sources: age, female, diabetes, hypertension, AF,
  prior MI, HF, prior stroke, LVEF (imputed), SBP, creatinine (converted from eGFR only if needed:
  none) and BMI.
- The Table-1 values are taken from the primary publications (sources recorded in
  `trial_specs.RCT_TABLE1`).
- Estimated with a weighted, pair-clustered Cox model.
- If entropy balancing fails to converge, the variable with the largest standardised gap is
  dropped (logged).

### II2. Per-protocol (on-treatment) analysis with IPCW

- **Censoring events.** Follow-up is censored at the first order of the other arm's study drug
  (switch), or at discontinuation.
- **Discontinuation.** No further order of the assigned drug within the grace period G after the
  last order; the date is last order + G. G = 365 days (base) and 180 days (sensitivity), chosen
  from the observed distribution of gaps between orders (75th percentile 143–335 days across study
  drugs). Orders have no days-supply.
- **IPCW.** A pooled-logistic model of protocol deviation per 90-day interval, using treatment,
  interval and the arm's own PS covariates. Stabilised, truncated at the 99th percentile. Estimated
  with a weighted start–stop Cox model, clustered on pair.
- **Not applicable to PARTNER** (procedure design).
- **Switch designs (PARADIGM-HF):** switching means an ARNI order in the comparator arm.

### II3. Run-in emulation (landmark)

- Landmark at 90 days. Keep pairs in which both members are alive, event-free and uncensored at
  day 90, and both have at least one repeat order of their assigned drug in (0, 90] days. The clock
  restarts at day 90.
- Primary interest is PARADIGM-HF, which had an active run-in; the analysis is reported for all
  drug trials.

### II4. Stricter outcome definitions

Hospitalisation components count only when the qualifying code is a primary billing diagnosis of
the stay (`condition_status_source_value` = 'HOSPITAL_BILLING_DX Y'). Death components are
unchanged.

### II5. Dose and time zero

- **Dose:** not feasible. Order records carry the ingredient only, with no strength or
  days-supply (checked 2026-09-25). Recorded as a limitation.
- **Time zero:** unchanged. The index order date is already in-hospital for ACS/HF-discharge
  trials.

## Part III: more physiology trials

- **Candidates** are screened in the order listed, with benchmarks and Table 1 verified from the
  primary papers:
  - Diuretic Comparison Project;
  - ONTARGET (ARB vs ACEi);
  - VALUE (ARB vs amlodipine);
  - ASCOT-BPLA (amlodipine vs atenolol);
  - EMPA-REG OUTCOME and EMPEROR-Preserved (SGLT2i vs DPP-4i proxy, as in RCT-DUPLICATE);
  - EAST-AFNET 4 (antiarrhythmic drug vs rate-control initiation in recent AF);
  - CABANA (ablation vs antiarrhythmic drug, procedure design).
- **Controls, if time allows:** CAROLINA, CARES and ENGAGE AF.
- **Analysis.** Each trial runs through the same frozen v1.1/v1.2 pipeline: phase 1, then phase 2,
  with no change to code or rules. The primary-set rule (≥ 400 clinical-PS pairs) is applied before
  outcomes are extracted.
- **Reporting.** Results are reported as an **extension set** and as a combined set (primary +
  extension). The frozen 10-trial primary results are never replaced.

## Outputs

- Restricted outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v13-*`.
- Aggregate tables: `docs/v13/`.
- A report section: "Exploratory robustness program (v1.3)".

## Deviation log

(filled in during implementation, dated, before summaries)

- **2026-09-25, deviation 1 (II2).** In LIFE, the median time to "discontinuation" with G = 365 d
  is exactly 365 d: more than half of initiators have no repeat order within a year. Refills
  probably run on the original prescription, which has refills but no days-supply. G = 730 d is
  added as a further sensitivity. This was seen before any per-protocol estimate was computed.
- **2026-09-25, deviation 2 (II2).** Added a switch-only variant, which censors only at the first
  order of the other arm's drug. Switching is observable in order data; discontinuation is not.
- **2026-09-25, deviation 3 (I1).** Added the plasmode scenario "phys_only": κ = 1, and the
  medication and utilisation coefficients set to 0. It isolates confounding by physiology, which
  the ECG could capture, from confounding by medication and utilisation, which it cannot. Added
  before any plasmode result was seen.
- **2026-09-25, deviation 4 (I1).** The truth is computed from 20 counterfactual copies with common
  random numbers, instead of 5 independent copies. This reduces Monte Carlo error in the truth.
  Changed after a 3-replicate smoke test on LIFE, before the full run.
- **2026-09-25, deviation 5 (II1).** In the LIFE smoke test (sparse arm, imputation 1), balancing to
  the RCT's Table 1 converged but left an effective sample size of 183 out of about 2,400. The
  driver is the trial's mean SBP of 174 mmHg; our cohort's is much lower. A second variant,
  `transport_ess20`, keeps dropping the variable with the largest standardised gap until the
  effective sample size is at least 20% of the matched sample. Both variants are reported. Only
  the effective sample size was inspected; the estimates were not compared.
- **2026-09-25, deviation 6 (I1), made after seeing the plasmode results.**
  - **The problem.** The registered plasmode kept each arm's matched set fixed across replicates.
    So the per-trial "bias" includes the chance covariate imbalance of that single matched sample,
    and the Monte Carlo CIs do not reflect it. The clinical reference R contains every
    outcome-model covariate, yet it showed |bias| up to 0.08 (RE-LY) in the null scenario, where
    the true effect is zero in every arm. In the extension trials, the sign of C1/C2 reversed
    relative to the primary trials.
  - **The fix.** A resampled plasmode (Franklin et al. 2014): in each replicate, resample the
    cohort with replacement, refit hdPS, PS and matching for every arm, then simulate all
    scenarios on that resample. 200 replicates per trial; truths as before.
  - **Reporting.** Both versions are reported. The resampled version is treated as the correct
    implementation of I1, and it decides rule 1. The fixed-set version is labelled as registered
    and flawed.
