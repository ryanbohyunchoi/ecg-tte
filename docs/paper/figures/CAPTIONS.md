# Figure captions (first draft, 2026-10-01)

All figures are built by `scripts/v20/make_paper_figures.py` from aggregate audit outputs. Files are in `main/` (Figures 1–4) and `supplementary/` (eFigures 1–8), each as PNG (300 dpi) and PDF.

- **Primary set:** 32 trials (emulation-quality tiers other than limited). The primary PS is PS-Demo.
- **Abbreviations:** PS, propensity score; SMD, standardized mean difference; HR, hazard ratio; LVEF, left ventricular ejection fraction; NT-proBNP, N-terminal pro–B-type natriuretic peptide; BMI, body mass index; eGFR, estimated glomerular filtration rate; YNHHS, Yale New Haven Health System.

## Main figures

**Figure 1. Study Design, Trial Selection and Analyses**
Of 99 candidate cardiovascular RCTs, 38 met the feasibility criteria and were emulated in YNHHS electronic health record data, and 32 were retained after emulation-quality grading (6 limited emulations excluded). ECGs were encoded with a self-supervised AI-ECG model, and the resulting 32 principal components were added to each PS specification. Three analyses followed:
1. balance on held-out characteristics;
2. agreement with the published RCT results;
3. plasmode simulations with a known treatment effect.

An external validation in MIMIC-IV used 7 cardiovascular trials meeting the same feasibility criteria, plus PEPTIC as a negative-control trial.

**Figure 2. Balance on Held-Out Characteristics With and Without the ECG Embedding**

A, Median absolute standardized mean difference (|SMD|) across 32 trials for each of 58 held-out characteristics before matching (crosses), after matching on PS-Demo (open circles) and after matching on PS-Demo + ECG (filled circles); the dashed line marks |SMD| = 0.1. B, Mean |SMD| by characteristic domain. C, Mean |SMD| before matching and after matching on each PS specification without and with the ECG; labels give the relative change with the ECG. D, Change in the percentage of characteristics with |SMD| <0.1 after adding the ECG to PS-Demo in each trial (22 of 32 trials improved; P = .002).

**Figure 3. Agreement of Emulated and RCT Hazard Ratios**

A, Emulated vs RCT HRs for 32 trials with PS-Demo (open circles) and PS-Demo + ECG (filled circles); the dashed line is the line of identity. B, Mean absolute difference between emulated and RCT log HRs by PS specification; labels give the number of trials closer to the RCT with the ECG, the sign-flip P value and the benchmark-permutation P value. C, Standardized difference agreement by emulation quality (excellent or good, n = 15; moderate, n = 17) for each PS specification without (open) and with (filled) the ECG. D, Pearson correlation, estimate agreement and standardized difference agreement for each PS specification without and with the ECG.

**Figure 4. Bias From an Unmeasured Physiological Confounder Removed by the ECG in Plasmode Simulations**

A, Percentage of bias removed by adding the ECG to PS-Demo vs the ECG's partial R² for the withheld confounder in the real data, for 107 trial–confounder combinations in 31 trials; the dashed line is 100 × R², and dotted lines give the medians for adjustment for the confounder itself and for the permuted-ECG placebo. B, Percentage of confounder-induced bias removed by a PS of the ECG alone and by adding the ECG to PS-Demo, the hdPS and PS-Clinical, by confounder; error bars are ±1.96 Monte Carlo SEs. Adjustment for the confounder itself removed 93.1% of the bias (not shown).

*Abbreviations for Figures 2–4:* BMI, body mass index; ECG, electrocardiogram; eGFR, estimated glomerular filtration rate; hdPS, high-dimensional propensity score; HR, hazard ratio; LVEF, left ventricular ejection fraction; NT-proBNP, N-terminal pro–B-type natriuretic peptide; PS, propensity score; RCT, randomized controlled trial; SMD, standardized mean difference.

## Supplementary figures

**eFigure 1. Trial Selection Flow**
Selection of the 38 emulated and 32 analysed trials from 99 candidate RCTs, with reasons for exclusion and the 6 trials excluded for limited emulation quality. *Draft: counts by exclusion reason are placeholders to be filled from the screening log (docs/v17/candidates.json, docs/v18/af_candidates.json, scripts/trial_specs.py).*

**eFigure 2. Balance on the 58 Held-Out Characteristics**
Median |SMD| after matching across 32 trials with PS-Demo alone (open circles), with the ECG embedding (red) and with the permuted-ECG placebo (gold triangles), grouped by domain. The dashed line marks |SMD| = 0.1.

**eFigure 3. Balance on the Expanded Panel by Domain**
Relative reduction in mean |SMD| with the ECG embedding (red) and the permuted-ECG placebo (gold) across about 330 additional pre-index characteristics per trial (344 with data in the primary set), by domain, for PS-Demo in 32 trials. Overall reduction: 9.8% (95% CI, 6.3%–13.2%). The 95% CIs are from bootstrap resampling of trials.

**eFigure 4. Emulated and RCT Hazard Ratios for All 38 Emulated Trials**
Emulated HRs (95% CI) with PS-Demo alone (open circles) and with the ECG embedding (red), against the RCT estimate (bar) and 95% CI (grey band). Trials are ordered by emulation-quality tier. The 6 limited-quality emulations (grey labels) are excluded from the primary analyses.

**eFigure 5. Robustness of the Plasmode Simulation**
- A, Percentage of PS-Demo bias removed (all confounders) by adding the ECG embedding, by a PS of the ECG alone and by the oracle, at true HRs of 0.6, 0.8 and 1.0 (common random numbers; ±1.96 Monte Carlo SEs). Adding the ECG removed 14.2% at each true HR.
- B, Coverage of the true effect by nominal 95% CIs for each PS specification, with and without the ECG (clinical orientation, all confounders). The dashed line marks 95%.

**eFigure 6. Echocardiography Subset: Real-Data Counterpart of the Simulation**
- A, Among patients with a pre-index LVEF (or NT-proBNP) measurement, the proportion of the imbalance in that measure closed by adding the ECG embedding (solid bars) or the permuted-ECG placebo (hatched), relative to the imbalance closed by adjusting for the measure itself, by PS specification. PS-Demo: 60% for LVEF and 39% for NT-proBNP; placebo about 3% and −4%.
- B, Placebo-corrected share of the HR shift produced by adjusting for the measure that the ECG reproduces (F, 95% CI), against the plasmode prediction (partial R² of the ECG). The dashed line is the line of identity.

Primary set of 32 trials; 20 trials in the LVEF subset and 16 in the NT-proBNP subset met the size criteria.

**eFigure 7. MIMIC-IV External Validation by Trial**
- A, Proportion of 26 held-out characteristics (laboratory values, vital signs, ventilation and utilisation) with |SMD| < 0.1 with PS-Demo alone, with the ECG embedding and with the permuted ECG.
- B, Emulated HRs vs the RCT estimate (bar) and 95% CI (grey band). [OR] and [RR] mark RCT benchmarks reported as odds ratio (SOAP II) or risk ratio (PEPTIC).

PEPTIC (proton pump inhibitor vs histamine-2 receptor antagonist) is a negative-control trial with an expected null effect.

**eFigure 8. Alternative Estimands**
- Mean absolute difference from the RCT log HR, with and without the ECG (PS-Demo), for:
  - the initiation (primary) estimand;
  - per-protocol and switch-only estimands with inverse-probability-of-censoring weights;
  - a 90-day landmark;
  - a 90-day run-in.

  Each estimand is shown for the trials of the primary set in which it was estimable (n shown).
