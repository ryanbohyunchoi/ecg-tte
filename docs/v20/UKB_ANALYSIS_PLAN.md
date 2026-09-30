# v2.0 UK Biobank analysis plan: CMR plasmode, PGS vs ECG, CMR held-out balance (registered before any result)

Date 2026-09-30. Exploratory. This plan is committed before any simulation result or CMR balance statistic is computed.
Code: `scripts/v20/ukb_cmr_plasmode.py`. Aggregates: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-ukb-analysis/`
(umask 077). Write-up: `docs/v20/UKB_ANALYSIS.md`. Inputs are read in place (read-only):
- the v1.5 UKB trial directories (`claude-v15-ukb-{ontarget,ascot,allhat}`: cohort, baseline, outcomes, ECG BCL
  embeddings);
- the CMR imaging-derived phenotype basket, streamed column-filtered from the read-only object store. Only the
  needed columns are cached, restricted, in the output directory;
- the local PGS Catalog scores (AF, AS, CAD, DCM, HCM, HF).

No participant-level rows or identifiers are reported; counts 1–10 are suppressed.

## Base populations
The three v1.5 prevalent-user cohorts anchored at the imaging visit: ONTARGET (ARB vs ACEi), ASCOT (amlodipine vs
beta-blocker) and ALLHAT (amlodipine vs thiazide). They supply realistic covariate structure, a real treatment for
the demographic PS logit, a real outcome for the baseline hazard, and real administrative censoring.
- ASCOT and ALLHAT share the amlodipine arm, so their cells are not independent. We report per cohort, and pooled
  results are labelled accordingly.
- Analysis set S per cohort × confounder: an imaging-visit ECG embedding, the confounder observed at the imaging
  visit in its valid range, and all six PGS present (the same S for every arm, so ECG and PGS are compared on
  identical people).
- A cell is simulated if both real arms in S have ≥300 people.

## Hidden confounders (CMR, same visit as the ECG), clinical orientation
Higher standardized Cz means more treatment and higher hazard:
- **LVEF**, field 22420 (fallback: Bai IDP LVEF). Valid 10–90%. Sign −1, i.e. lower LVEF is worse. This is the
  primary confounder.
- **LV end-diastolic volume indexed** to body surface area (22421/22427). Valid 20–300 mL/m². Sign +1.
- **LV myocardial mass indexed** (Bai IDP LV mass / BSA). Valid 15–200 g/m². Sign +1.

  The field mapping is checked empirically: LVEF from the two sources must correlate strongly, and ranges must be
  plausible. If a field fails the check, that confounder is dropped and the failure logged.
- NT-proBNP is not available locally (it is in Olink only), so it is not used.

## Simulation design (as v1.9 G2 / v2.0 G2 extension, clinical orientation)
- **Treatment, main design:** logit P(T) = α + η_demo + log(OR)·Cz.
  - η_demo is the L2 PS logit of the real treatment on demographics (age, sex, index year) in S.
  - α is calibrated to the real treated share.
  - OR ∈ {1.25, 1.5, 2}, plus the null OR = 1.
- **Treatment, trtC design:** logit P(T) = α + log(OR)·Cz, with no demographic term. This gives a clean
  "proxy-only vs unmatched" comparison.
- **Outcome:** Weibull PH, lp = Zcore·β + log(HR_Y)·Cz + log(0.8)·T.
  - β comes from a ridge Cox fit (penalizer 0.01) of the real outcome on the real treatment and the standardized
    baseline covariates. These are demographics, 9 diagnoses, medication classes, labs/vitals median-imputed with
    missingness indicators, and utilisation. The baseline covariates contain no CMR variable.
  - The baseline is a Weibull fit to the Breslow cumulative hazard.
  - HR_Y ∈ {1.25, 1.5, 2}; with OR = 1, only HR_Y = 1.
- **Event rate (deviation from pure plasmode, prespecified):** the UKB real event rates are 3–5%, which gives
  imprecise matched Cox estimates. λ is therefore scaled so that the simulated null-scenario event rate is ≈20%,
  close to the Yale G2 median of 21%. A sensitivity run on the ONTARGET × LVEF cell keeps the real event rate.
- **Censoring:** administrative, min(trial horizon, 2022-10-31 − index).
- **Replicates:** 50 per cell, each an 80% subsample without replacement. In each, treatment is redrawn, every PS
  refitted (L2 logistic, C = 1), 1:1 greedy caliper-0.2 matching applied, and a Cox model with pair-clustered SE fitted.
- **Truth:** the marginal log HR in each arm's matched population, from counterfactual outcomes (5 copies, common
  random numbers).
- **Arms:**
  - main design: unmatched; demographic PS; demo + ECG (32 PCs of the BCL embedding, computed within cohort);
    demo + permuted ECG; demo + PGS (6 scores); demo + PGS + ECG; ECG only; permuted ECG only; PGS only;
    oracle (demo + Cz);
  - trtC design: unmatched; ECG only; permuted ECG only; PGS only; PGS + ECG; oracle (Cz only).
- **Endpoints:**
  - % of bias removed (ratio of summed cell-mean errors over non-null scenarios), raw and null-corrected, vs
    unmatched and vs the demographic PS, each with MCSE (1,000 replicate resamples within cells);
  - bias, empirical SE, RMSE and coverage, each with MCSE (ADEMP);
  - the ECG's and the PGS's added share over the demographic PS.
- **Real-data proxy strength:** 5-fold cross-fitted ridge R² of Cz on ECG32, PGS6, PGS6 + ECG32, demographics, and
  demographics + ECG, plus the partial R²(ECG | demo), in S.
- **Primary summaries:**
  - % of LVEF-induced bias removed by ECG only vs PGS only (trtC, vs unmatched);
  - demo + ECG vs demo + PGS (main design, null-corrected, vs the demographic PS);
  - relation to R² (expect ≈100 × R², as in Yale G2).

## Held-out CMR balance (descriptive)
In ONTARGET, ASCOT and ALLHAT, with the **real** exposure, we match with the demographic PS, demo + ECG, demo +
permuted ECG and demo + PGS. We then report |SMD| (pooled SD of the unmatched analysed cohort) on a CMR panel:
- LVEF, LVEDVi, LVESVi, LV mass index, LV stroke volume index, cardiac index;
- RV EF/EDVi, and LA maximum volume index, if the fields are present.

The balance set is people with an ECG and CMR.

**Caveat, stated with every result:** exposure is prevalent use at the imaging visit and the CMR is measured on
treatment. Balance therefore mixes confounding with treatment effects. With three overlapping cohorts, no
significance test is performed.

## Reporting
The plain-language verdict comes first. Every deviation from this plan is logged in `docs/v20/UKB_ANALYSIS.md`.
Nothing is pushed; commits are local only, pending the PI's review of UKB-related material.
