# Figure captions (first draft, 2026-10-01)

All figures are built by `scripts/v20/make_paper_figures.py` from aggregate audit outputs. Files are in `main/` (Figures 1–4) and `supplementary/` (eFigures 1–8), each as PNG (300 dpi) and PDF.

- **Primary set:** 32 trials (emulation-quality tiers other than limited). The primary PS is the demographic PS.
- **Abbreviations:** PS, propensity score; SMD, standardized mean difference; HR, hazard ratio; LVEF, left ventricular ejection fraction; NT-proBNP, N-terminal pro–B-type natriuretic peptide; BMI, body mass index; eGFR, estimated glomerular filtration rate; YNHHS, Yale New Haven Health System.

## Main figures

**Figure 1. Study Design, Trial Selection and Analyses**
Of 99 candidate cardiovascular RCTs, 38 met the feasibility criteria and were emulated in YNHHS electronic health record data, and 32 were retained after emulation-quality grading (6 limited emulations excluded). ECGs were encoded with a self-supervised AI-ECG model, and the resulting 32 principal components were added to each PS specification. Three analyses followed:
1. balance on held-out characteristics;
2. agreement with the published RCT results;
3. plasmode simulations with a known treatment effect.

An external validation in MIMIC-IV used 7 cardiovascular trials meeting the same feasibility criteria, plus PEPTIC as a negative-control trial.

**Figure 2. Balance on Held-Out Characteristics With and Without the ECG Embedding**
- A, Relative reduction in mean |SMD| of held-out characteristics when the ECG embedding (red circles) or a permuted-ECG placebo (gold triangles) was added to the demographic PS, overall (58 characteristics; 11.4%; 95% CI, 6.3%–16.0%) and by domain, across 32 trials. The left ventricular systolic function estimate (14.6%) has a 95% CI that includes 0 (−0.5% to 27.3%).
- B, The same measure by PS specification: demographic (11.4%), five-diagnosis (9.0%), high-dimensional (7.6%; 1.9%–12.8%) and clinical (−1.2%). For the clinical PS, characteristics included in that PS are excluded.
- C, External replication in MIMIC-IV across 7 trials. The demographic PS gave 10.3% (6.4%–14.5%). Clinical-lite denotes the PS available in MIMIC-IV.

Relative reduction is 1 minus the ratio of the across-trial mean of the mean |SMD| with the added components to that without them. The 95% CIs are percentile intervals from 4,000 bootstrap resamples of trials with a fixed seed. Within each trial, only characteristics observed in both compared arms are used.

**Figure 3. Agreement of Emulated and RCT Hazard Ratios**
- A, Emulated vs RCT HRs for 32 trials with the demographic PS alone (open circles) and with the ECG embedding (red). Grey segments join the two estimates for each trial; the dashed line is the line of identity.
- B, Mean absolute difference between emulated and RCT log HRs by PS specification. Labels give:
  - the number of trials in which the ECG moved the estimate closer to the RCT;
  - the one-sided exact sign-flip P value;
  - the benchmark-permutation P value, in which RCT results were reassigned across trials 20,000 times.
- C, RCT-DUPLICATE agreement metrics by emulation quality (excellent or good, n = 15; moderate, n = 17) for the demographic and clinical PS with and without the ECG:
  - Pearson correlation of log HRs;
  - estimate agreement (emulated HR within the RCT 95% CI);
  - standardized difference agreement (|z| < 1.96).

  Comparisons by emulation quality are post hoc.

**Figure 4. Plasmode Simulation: Bias From an Unmeasured Physiological Confounder Removed by the ECG**
- A, Percentage of the demographic-PS bias removed by adding the ECG embedding, against the ECG's cross-fitted partial R² for the withheld confounder in the real data, for 107 trial–confounder combinations in 31 trials. The dashed line is 100 × R². Dotted lines give the median for the oracle (adjustment for the confounder itself) and for the permuted-ECG placebo.
- B, Percentage of confounder-induced bias removed, by confounder:
  - by a PS built from the ECG embedding alone (LVEF, 27.9%; all confounders, 18.0%);
  - by adding the ECG to the demographic, high-dimensional and clinical PS, as a share of the bias remaining after each PS (14.9%, 8.6% and 11.7%);
  - by the oracle (93.1%).

  Error bars are ±1.96 Monte Carlo SEs.

In both panels, LVEF and eGFR are oriented so that lower values increase treatment probability and hazard (clinical orientation; adopted after the initial design, see eMethods 7). NT-proBNP and BMI are identical in both orientations. In panel B:
- the ECG-only and oracle values come from the design in which treatment depends on the confounder only;
- the added-value bars use bias corrected for each arm's error in the no-confounding scenario.

The true HR was 0.80.

## Supplementary figures

**eFigure 1. Trial Selection Flow**
Selection of the 38 emulated and 32 analysed trials from 99 candidate RCTs, with reasons for exclusion and the 6 trials excluded for limited emulation quality. *Draft: counts by exclusion reason are placeholders to be filled from the screening log (docs/v17/candidates.json, docs/v18/af_candidates.json, scripts/trial_specs.py).*

**eFigure 2. Balance on the 58 Held-Out Characteristics**
Median |SMD| after matching across 32 trials with the demographic PS alone (open circles), with the ECG embedding (red) and with the permuted-ECG placebo (gold triangles), grouped by domain. The dashed line marks |SMD| = 0.1.

**eFigure 3. Balance on the Expanded Panel by Domain**
Relative reduction in mean |SMD| with the ECG embedding (red) and the permuted-ECG placebo (gold) across about 330 additional pre-index characteristics per trial (344 with data in the primary set), by domain, for the demographic PS in 32 trials. Overall reduction: 9.8% (95% CI, 6.3%–13.2%). The 95% CIs are from bootstrap resampling of trials.

**eFigure 4. Emulated and RCT Hazard Ratios for All 38 Emulated Trials**
Emulated HRs (95% CI) with the demographic PS alone (open circles) and with the ECG embedding (red), against the RCT estimate (bar) and 95% CI (grey band). Trials are ordered by emulation-quality tier. The 6 limited-quality emulations (grey labels) are excluded from the primary analyses.

**eFigure 5. Sensitivity Analyses**
- A, Proportion of held-out characteristics with |SMD| < 0.1 in 29 trials whose RCTs enrolled outpatients, among all initiators and among patients initiating treatment outside an inpatient stay. Bars show the demographic PS alone, with the ECG and with the permuted ECG. Labels give the gain with the ECG, the number of trials improved and the sign-flip P value.
- B, Mean absolute difference from the RCT log HR, with and without the ECG (demographic PS), for:
  - the initiation (primary) estimand;
  - outpatient initiators;
  - per-protocol and switch-only estimands with inverse-probability-of-censoring weights;
  - a 90-day landmark;
  - a 90-day run-in.

  Each estimand is shown for the trials of the primary set in which it was estimable (n shown).

**eFigure 6. Echocardiography Subset: Real-Data Counterpart of the Simulation**
- A, Among patients with a pre-index LVEF (or NT-proBNP) measurement, the proportion of the imbalance in that measure closed by adding the ECG embedding (solid bars) or the permuted-ECG placebo (hatched), relative to the imbalance closed by adjusting for the measure itself, by PS specification. Demographic PS: 60% for LVEF and 39% for NT-proBNP; placebo about 3% and −4%.
- B, Placebo-corrected share of the HR shift produced by adjusting for the measure that the ECG reproduces (F, 95% CI), against the plasmode prediction (partial R² of the ECG). The dashed line is the line of identity.

Primary set of 32 trials; 20 trials in the LVEF subset and 16 in the NT-proBNP subset met the size criteria.

**eFigure 7. MIMIC-IV External Validation by Trial**
- A, Proportion of 26 held-out characteristics (laboratory values, vital signs, ventilation and utilisation) with |SMD| < 0.1 with the demographic PS alone, with the ECG embedding and with the permuted ECG.
- B, Emulated HRs vs the RCT estimate (bar) and 95% CI (grey band). [OR] and [RR] mark RCT benchmarks reported as odds ratio (SOAP II) or risk ratio (PEPTIC).

PEPTIC (proton pump inhibitor vs histamine-2 receptor antagonist) is a negative-control trial with an expected null effect.

**eFigure 8. Robustness of the Plasmode Simulation**
- A, Percentage of demographic-PS bias removed (all confounders) by adding the ECG embedding, by a PS of the ECG alone and by the oracle, at true HRs of 0.6, 0.8 and 1.0 (common random numbers; ±1.96 Monte Carlo SEs). Adding the ECG removed 14.2% at each true HR.
- B, Coverage of the true effect by nominal 95% CIs for each PS specification, with and without the ECG (clinical orientation, all confounders). The dashed line marks 95%.
