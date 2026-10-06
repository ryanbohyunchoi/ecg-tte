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

*Concise legends; these match docs/paper/supplement.md.*

### eFigure 1. Trial Selection

File: `supplementary/efigure1_trial_flow.png`

Flow from 99 candidate RCTs to 38 emulated and 32 analysed trials, with reasons for exclusion and the 6 limited-quality emulations excluded after quality grading. [PI: add counts by exclusion reason from the screening log.]

### eFigure 2. Balance on the 58 Held-Out Characteristics With the Permuted-ECG Placebo

File: `supplementary/efigure2_loveplot_58.png`

Median absolute standardized mean difference (|SMD|) across 32 trials after matching on PS-Demo (open circles), PS-Demo + ECG (red) and PS-Demo + permuted ECG (gold triangles), grouped by domain. The dashed line marks |SMD| = 0.1.

### eFigure 3. Balance on the Expanded Panel

File: `supplementary/efigure3_expanded_panel.png`

Relative reduction in mean |SMD| with the ECG (red) and the permuted-ECG placebo (gold), overall and by domain, for PS-Demo in 32 trials. Error bars are 95% CIs from bootstrap resampling of trials.

### eFigure 4. Emulated and RCT Hazard Ratios for the 38 Emulated Trials

File: `supplementary/efigure4_forest_38.png`

Emulated HRs (95% CI) with PS-Demo (open circles) and PS-Demo + ECG (red) against the RCT estimate (bar) and 95% CI (grey band), ordered by emulation quality. Limited-quality emulations (grey labels) are excluded from the primary analyses.

### eFigure 5. Robustness of the Plasmode Simulation

File: `supplementary/efigure5_simulation_robustness.png`

A, Percentage of bias removed (all confounders) by adding the ECG to PS-Demo, by a PS of the ECG alone and by adjustment for the confounder itself, at true HRs of 0.6, 0.8 and 1.0; error bars are ±1.96 Monte Carlo SEs. B, Coverage of nominal 95% CIs for each PS specification without and with the ECG; the dashed line marks 95%.

### eFigure 6. External Validation in MIMIC-IV by Trial

File: `supplementary/efigure6_mimic_per_trial.png`

A, Percentage of 26 held-out characteristics with |SMD| <0.1 after matching on PS-Demo, PS-Demo + ECG and PS-Demo + permuted ECG. B, Emulated HRs (95% CI) against the RCT estimate (bar) and 95% CI (grey band). PEPTIC is a negative-control trial; [OR] and [RR] mark benchmarks reported as an odds ratio or relative risk.

### eFigure 7. Alternative Estimands

File: `supplementary/efigure7_estimands.png`

Mean absolute difference between emulated and RCT log HRs with PS-Demo (open) and PS-Demo + ECG (red) for the initiation (primary), per-protocol, switch-only, 90-day landmark and 90-day run-in estimands, in the primary-set trials in which each was estimable (n shown).

### eFigure 8. Comparison With Measured Physiology in Patients With Echocardiography

File: `supplementary/efigure8_echo_subset.png`

A, Share of the imbalance in LVEF or NT-proBNP closed by adding the ECG (solid bars) or the permuted ECG (hatched), relative to adjustment for the measured value itself, by PS specification. B, Placebo-corrected share of the HR shift reproduced by the ECG (95% CI) against the simulation prediction; the dashed line is the line of identity.

*Abbreviations for eFigures:* ECG, electrocardiogram; hdPS, high-dimensional propensity score; HR, hazard ratio; LVEF, left ventricular ejection fraction; NT-proBNP, N-terminal pro–B-type natriuretic peptide; PS, propensity score; RCT, randomized controlled trial; SMD, standardized mean difference.
