# Figure 5 protocol: hidden-confounder benchmark inside SPRINT (RCT rejection sampling)

**LOCKED 2026-10-15** (user approval of BDC_FEASIBILITY.md §4 and the defaults below, 2026-10-15), before any ECG-adjusted estimate exists.
- Changes after this point are deviations: log them in `pipeline.md` §9.
- Feasibility facts may change counts, never the design.

## Data
- **Source:** SPRINT, BioLINCC on BDC (phs003483), and SPRINT-Imaging raw ECG XML (phs003566). Built by `scripts/bdc/sprint_cohort.py` (git ad3f99d).
- **Analysis population:** randomized participants with an assigned baseline ECG XML (ECGDAYS in [−90, 30]), n = 8,815.
- **Complete case:** each C is analysed only among participants with that C observed.
- **Treatment T:** RANDASSIGN (1 = intensive SBP target).
- **Primary outcome:** SPRINT-POP primary composite (`EVENT_PRIMARY`, `T_PRIMARY`).
- **Secondary outcome:** primary composite or death (`EVENT_PRIMARYORDEATH`).

## Hidden confounders C (z-scored within the analysis population)

| C | Role |
|---|---|
| `EGFR` | physiology (as in the paper's plasmode) |
| `LOG_NTPROBNP` | physiology (as in the paper's plasmode) |
| `LOG_HSTNI` | physiology |
| `BMI` | physiology (as in the paper's plasmode) |
| `LOG_UMALCR` | physiology |
| `ECG_CV`: Cornell voltage from the reading centre, measured on the same baseline ECG | **positive control**: the ECG should recover it |
| `LDL_CALC` (Friedewald) | **negative control**: expected to be invisible to the ECG |

## Inducing confounding (Keith et al., TMLR 2023, rejection sampling)
1. **Selection model:** logit P\*(T=1|C) = α + β·z(C), with β = log(OR) and OR ∈ {2, 3, 5}.
   - OR 3 is the primary strength. OR 5 is a stress test.
   - α is solved so that mean P\* equals the randomized share P̂(T=1).
   - P\* is clipped to [0.05, 0.95].
2. **Acceptance:** keep participant i with probability P\*(T=tᵢ|Cᵢ) / (P̂(T=tᵢ)·M), where M = maxᵢ P\*(T=tᵢ|Cᵢ)/P̂(T=tᵢ).
3. **Draws:** 300 per (C, OR), with seeds 20261015 + draw.
   - The same seeds are used for every adjustment arm, so the arms are paired within each draw.

## Adjustment arms
All arms use the paper's estimator:
- L2 logistic PS with C = 1 on standardised covariates;
- 1:1 greedy nearest-neighbour matching on the PS logit, caliper 0.2 SD, without replacement;
- Cox model in the matched cohort with robust SE clustered on pairs.

Missing PS inputs get median imputation plus a missingness indicator.

1. **Crude:** no adjustment (all accepted participants, unmatched Cox).
2. **PS-Base**, the PS-CVD5 analogue for this trial. Hypertension is universal in SPRINT and diabetes is an exclusion, so the variables are:
   - AGE, FEMALE, RACE4 (dummies);
   - SUB_CLINICALCVD, SUB_SUBCLINICALCVD;
   - ATRIALFIB, CONHEARTFAIL;
   - current smoking (SMOKE_3CAT = 3).
3. **PS-Base + ECG:** BCL encoder, 256-d → 32 PCs. The PCs are fitted once on the 8,815 baseline ECGs.
4. **PS-Base + permuted ECG:** the ECG rows shuffled once, with seed 424242. This is the placebo.
5. **PS-Rich (−C):** PS-Base plus the inputs below, minus C and anything derived from it.
   - **Added inputs:**
     - SBP, DBP, N_AGENTS, ASPIRIN, STATIN, HEARTATT;
     - EGFR, SCREAT, SUB_CKD;
     - LOG_UMALCR, BMI, CHR, HDL, log TRR, GLUR;
     - LOG_NTPROBNP, LOG_HSTNI, HRAVG, EDUCATION.
   - **Removed for each C:**
     - EGFR: EGFR, SCREAT, SUB_CKD;
     - LDL_CALC: CHR, HDL, log TRR;
     - every C: any other input with |ρ| ≥ 0.80 with C in the analysis population (the paper's leakage rule).
   - No ECG reading-centre measure is ever a PS input.
6. **PS-Rich (−C) + ECG.**
7. **Oracle:** PS-Base + C.

## Truth and metrics
**Per draw:**
- the log HR for each arm;
- post-match |SMD| of C and of the other baseline measures;
- the number of matched pairs and events.

**Primary metric: share of the confounding gap closed** by adding the ECG.
- Formula: G = Σ(b_base − b_arm) / Σ(b_base − b_oracle), summed over draws. This is a ratio of means. b is the log HR of the named arm.
- Reported for PS-Base + ECG and PS-Base + permuted ECG.
- The same ratio is reported for PS-Rich (−C) + ECG against PS-Rich (−C).
- 95% CI from bootstrapping draws: 2,000 resamples, seed 20261001.

**Balance metric:** relative reduction in post-match |SMD| of C, i.e. 1 − mean(arm) / mean(PS-Base).

**Absolute-bias reference:**
- **Truth:** the full-trial Cox HR (all 8,815, original randomization) weighted by P\*(T=1|C). That is the randomized HR in the population the matching targets.
- **Reported against it:** bias, RMSE and 95% CI coverage for every arm.

**Gate:** a (C, OR) cell counts as having induced bias only if mean(b_base − b_oracle) > 2 × its Monte Carlo SE. Other cells are reported as "no material induced bias" and are not used for G.

**Also reported:**
- the cross-validated R² of C from the ECG PCs alone, and the partial R² beyond PS-Base. This is the Figure 4A analogue;
- the confounding-vs-error plot.

## Runs
- **Preliminary (label it as such everywhere):** C ∈ {EGFR, LOG_NTPROBNP, ECG_CV}, OR 3, 50 draws, primary outcome.
- **Full:** all 7 C × 3 OR × 300 draws × both outcomes.
- **Later trials:** ACCORD and WHI use this protocol with trial-specific PS-Base/Rich lists, fixed before their ECG arms run.
