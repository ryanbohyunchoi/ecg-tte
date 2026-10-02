# AI-enhanced electrocardiography as a phenotypic probe of confounding in target trial emulation: an evaluation across 38 cardiovascular trials

*Working draft; last updated 2026-10-01. Target journal: to be decided. Reporting follows the TARGET guideline for target trial emulation and STROBE. Draft notes are marked and must be removed before submission.*

## Abstract

*(to be written last; structured as Background, Methods, Results and Conclusions)*

## Introduction

Randomization is the gold standard for causal inference in medicine. Treatment is assigned by chance, so measured and unmeasured characteristics are, on average, balanced between arms. Differences in outcomes can then be attributed to the treatment itself.^1^ Randomized controlled trials (RCTs) are, however, expensive and time-consuming. They are also often infeasible or unrepresentative for important populations, such as older, multimorbid or underrepresented patients who receive these therapies in practice.^2^

Inferring causal effects from the data already generated in routine care therefore remains an unmet need. Target trial emulation (TTE), in which the protocol of a hypothetical randomized trial is specified and then emulated in observational data, is a leading candidate approach.^3^ Confounding is traditionally addressed with propensity scores (PS) estimated from structured variables. This strategy balances measured characteristics well, and benchmarking against completed RCTs has shown that well-designed emulations can reproduce trial results.^4,5^ However, its guarantee extends only to what is measured. Most emulations rely on claims data, which record diagnoses, procedures and prescriptions consistently. Electronic health records (EHRs) capture clinical measurements at the point of care and are available within individual health systems, making them actionable for site-specific evidence generation. However, laboratory values, vital signs and imaging are missing for many patients, and not at random. These measurements therefore cannot be relied on for adjustment.^6^

This gap is particularly consequential in cardiovascular medicine. Many determinants of both treatment choice and prognosis are physiological: ventricular function, chamber size, atrial substrate, congestion and conduction. These are the characteristics most likely to confound comparisons and least likely to be captured in structured data. The 12-lead electrocardiogram (ECG) offers a potential solution. It is inexpensive and acquired routinely across the health system. Artificial intelligence applied to the ECG (AI-ECG) detects left ventricular dysfunction, structural heart disease and other latent phenotypes.^7–9^ Foundation-model embeddings compress this information into general-purpose representations of cardiac physiology.^10^ Because the ECG records current cardiac physiology and is available for most patients, AI-ECG representations may capture confounding that structured data miss and partly compensate for physiological measurements that are missing from routine-care data.

Here, we evaluated whether AI-ECG embeddings capture confounding missed by structured data in 38 emulations of cardiovascular RCTs. We assessed (i) balance on held-out clinical, laboratory and echocardiographic characteristics, (ii) agreement with RCT results, and (iii) bias removal in simulations with a known treatment effect.

## Methods



### Data sources

We used electronic health record (EHR) data from the Yale New Haven Health System (YNHHS), a large academic health system in the American northeast. We mapped the structured EHR data to the Observational Medical Outcomes Partnership (OMOP) common data model. We linked these data to structured echocardiography reports, raw 12-lead ECG signals and state vital statistics records (eMethods 1). We included patients with index dates from 2011 through 2024. The Yale Institutional Review Board approved the study (protocol number [PI: IRB protocol number]) and waived informed consent for this secondary analysis of existing data. For external validation, we used MIMIC-IV (version 3.1) and MIMIC-IV-ECG (version 1.0), deidentified EHR and 12-lead ECG data from patients treated at Beth Israel Deaconess Medical Center, Boston, Massachusetts (eMethods 11).^11,12^

### Trial selection and target trial specification

We identified candidate cardiovascular randomized controlled trials (RCTs) from landmark trials and investigator review of the cardiovascular literature. Trials were selected in two stages. First, *feasibility criteria* assessed whether each trial could be replicated in YNHHS data, based on the comparator, the ascertainability of the primary endpoint, the identifiability of the treatment strategies and the available sample size. Second, *emulation-quality criteria* assessed how closely each feasible emulation reproduced the design of the trial, including its eligibility, time zero, treatment strategies, comparator and outcome, and emulations with limited fidelity were excluded. Of 99 candidate trials, 38 met the feasibility criteria and were emulated, and 32 were retained after the quality assessment (eFigure 1). Both sets of criteria are detailed in eMethods 3. The 32 trials covered atrial fibrillation (AF; 12 trials), diabetes (7), heart failure (5), hypertension (2), acute coronary syndromes or myocardial infarction (2) and other indications (4).

For each trial, we specified the target trial protocol and its emulation following the TARGET guideline, summarized using the population, intervention, comparator, outcome and time (PICOT) elements (Table 1; eMethods 2; eTable 1).^13^ Each emulation used a new-user, active-comparator design and estimated the effect of treatment initiation, analogous to the intention-to-treat effect (eMethods 2).

Emulation quality was graded from design information alone, using a points-based adaptation of the RCT-DUPLICATE design-emulation criteria that scores in-hospital initiation not mirrored in the emulation, other misalignment of time zero, selective run-in, discontinuation of baseline therapy at randomization and long follow-up with a delayed treatment effect, together with comparator and outcome fidelity.^5^ Emulations were classified as excellent, good, moderate or limited (eMethods 3). 

### AI-ECG representation

We used the most recent 12-lead ECG within 365 days before or on the index date. ECGs were encoded with an AI-ECG signal model adapted from an image-based biometric contrastive learning (BCL) model, a self-supervised approach that learns patient-specific representations of cardiac structure and function without diagnostic labels.^10^ The model produced a 256-dimensional embedding per ECG, which was reduced to 32 principal components within each trial (eMethods 4).

*In a sensitivity analysis reported in the supplement, we also applied CLMBR-T-base, a structured-EHR foundation model, to each patient's coded history before the index date and reduced its output to 64 principal components, to explore whether foundation-model embeddings of other routinely collected data could serve a similar role in target trial emulation.^14^*

### Propensity scores and matching

Within each trial, we estimated the propensity score (PS) using L2-penalized logistic regression on standardized covariates. The primary specification, the demographic PS (PS-Demo), included only age, sex and calendar year of index, and represents settings in which few structured covariates are reliably captured. To examine whether the contribution of the ECG diminishes as structured covariates become richer, we fitted three further specifications of increasing richness: PS-CVD5, which added five cardiovascular and metabolic diagnoses (hypertension, type 2 diabetes, coronary artery disease, AF and heart failure); a high-dimensional PS (hdPS), which added 200 empirically selected code features to demographics and 9 to 13 investigator-selected prior diagnoses;^15^ and the clinical PS (PS-Clinical), which further included vital signs, laboratory values, left ventricular ejection fraction (LVEF), medications and healthcare use (eMethods 5). Each specification was fitted with and without the 32 ECG principal components (denoted, for example, PS-Demo + ECG), holding all other modelling choices constant, and patients were matched 1:1 without replacement by nearest-neighbour matching on the PS logit with a caliper of 0.2 standard deviations of the logit. In sensitivity analyses reported in the supplement, the PS was instead augmented with a permuted-ECG placebo, in which embeddings were shuffled between patients to test whether gains reflected ECG information rather than added dimensions, with the CLMBR-T components, or with both representations.

### Covariate balance

The primary outcome was balance, after matching, on characteristics not included in the PS under evaluation, summarized as the absolute standardized mean difference (SMD); an |SMD| <0.1 was considered balanced.^16^ The primary panel comprised 58 characteristics: 35 echocardiographic measures, vital signs, laboratory values including N-terminal pro–B-type natriuretic peptide (NT-proBNP), and summaries of medications, healthcare use and the coded record, including a prognostic score for the trial's primary outcome (eTable 2). These direct measures of cardiac structure and function are principal determinants of treatment selection and prognosis and are incompletely captured by diagnosis codes. To assess balance across a broader range of characteristics, we also examined an expanded panel of approximately 330 pre-index characteristics per trial with PS-Demo (245 to 336 across PS specifications), derived from covariates used in published PS and trial emulation studies (eMethods 6).

### Trial emulation analysis

Emulated HRs were estimated with Cox proportional hazards models with robust variance clustered on matched pairs. Following the RCT-DUPLICATE initiative, agreement with each RCT was assessed as the Pearson correlation of emulated and RCT log HRs across trials; estimate agreement, defined as an emulated HR within the RCT 95% CI; and standardized difference agreement, defined as a difference between emulated and RCT log HRs within 1.96 times its combined standard error.^4,5^ We also used the absolute difference between emulated and RCT log HRs, and assessed whether reductions in that difference were specific to each trial or reflected generic attenuation of extreme estimates, by comparing them with reductions obtained after reassigning RCT results at random across trials (eMethods 6).

### Simulation

The true effect is unknown in real data. We therefore used plasmode simulations,^17^ which retain each trial's real covariates, ECGs and follow-up while simulating treatment and outcome with a known HR. A measured physiological variable, LVEF, NT-proBNP, body mass index or estimated glomerular filtration rate, was made to drive both treatment and outcome and was withheld from every PS, so that it acted as an unmeasured confounder. We quantified the proportion of the resulting bias removed by a PS built from the ECG embedding alone, and by adding the ECG to PS-Demo, the hdPS and PS-Clinical, relative to adjusting for the confounder itself, and related it to how well the ECG predicted the confounder in the real data (eMethods 7).

### External validation

To assess generalizability, we reimplemented the analyses in MIMIC-IV. Using the same feasibility criteria, we selected trials whose treatment strategies are typically initiated in hospital, reflecting the inpatient population of MIMIC-IV: 7 cardiovascular trials (PLATO, ARISTOTLE, ROCKET AF, TRANSFORM-HF, COMET, SOAP II and ELITE II) and, as a negative control, PEPTIC, which found no significant difference in mortality between proton pump inhibitors and histamine-2 receptor antagonists in mechanically ventilated patients. ECG encoding, PS specification, matching, balance assessment and outcome analyses followed the primary analysis, with adaptations to the available data, including a held-out panel of 26 laboratory, vital sign and utilization characteristics and the absence of LVEF (eMethods 11).

### Statistical analysis

Trials were the unit of analysis. For each trial, balance was summarized as the proportion of held-out characteristics with an |SMD| <0.1, the measure prespecified for the confirmation analyses (eMethods 3), and as the mean |SMD|, using the characteristics observed in both compared arms. We also expressed the effect of the ECG as the relative reduction in mean |SMD|, defined as 1 minus the ratio of the across-trial means with and without the ECG; this threshold-free summary was added post hoc, and its 95% CIs were obtained from 4,000 bootstrap resamples of trials. Paired differences between PS specifications were tested with exact one-sided sign-flip permutation tests across trials. Robustness was assessed by clustering trials that shared a comparator and by leave-one-trial-out analysis, and the false discovery rate was controlled within analysis families. Agreement with RCTs was also described by emulation quality. Sensitivity analyses, reported in the supplement, included all 38 emulated trials, the expanded panel, alternative matching and weighting approaches, PS models and numbers of ECG components, per-protocol, switch-only, landmark and run-in estimands, restriction to patients initiating treatment as outpatients, and a comparison with measured physiology in patients with echocardiography (eMethods 5, 9 and 12). This study was exploratory, and all analyses are reported. Analyses were performed in Python 3.11 (eMethods 10).

## Results

### Trial selection and study population

Of 99 candidate RCTs, 38 met the feasibility criteria in YNHHS data and were emulated (eFigure 1). After grading of emulation quality, 6 limited-quality emulations were excluded, and the remaining 32 trials (3 excellent, 12 good and 17 moderate emulations) formed the primary analysis set (Table 1). The 32 trial cohorts comprised 212,496 patients with an ECG (median, 4,729 per trial; range, 1,442–22,277). With PS-Demo, 88,460 patients (41.6%) were retained in 44,230 matched pairs (median, 981 pairs per trial; range, 314–4,100) (Figure 1; eTable 3).

### Covariate balance

Adding the ECG embedding to PS-Demo improved balance on the 58 held-out characteristics (Figure 2A and 2D). The mean |SMD| decreased from 0.142 to 0.126, a relative reduction of 11.4% (95% CI, 6.3%–16.0%), and the proportion of characteristics with an |SMD| <0.1 increased from 49.8% to 55.0% (22 of 32 trials improved; P = .002). This improvement was robust to clustering of trials by comparator (P = .033) and to omission of any single trial (maximum P = .004), and it remained significant after false discovery rate control (q = .007). The permuted-ECG placebo did not improve balance (relative reduction, −0.7%).

The improvement was concentrated in measures of cardiac structure and function. The largest relative reductions in mean |SMD| were in left ventricular structure (24.6%; 95% CI, 15.0%–32.1%) and in diastolic function and left atrial size (17.7%; 95% CI, 8.0%–26.4%), followed by vital signs and core laboratory values (13.9%; 95% CI, 6.8%–20.2%) and right ventricular and pulmonary measures (13.0%; 95% CI, 3.0%–22.1%). The estimate for left ventricular systolic function was similar but imprecise (14.6%; 95% CI, −0.5% to 27.3%). Balance did not improve for valvular and aortic measures (1.3%; 95% CI, −12.5% to 12.7%) or for other laboratory values (−0.9%; 95% CI, −10.5% to 7.0%) (Figure 2B; eFigure 2).

The added value of the ECG decreased as the structured PS became richer (Figure 2C). The relative reduction was 9.0% (95% CI, 4.8%–13.3%) with PS-CVD5 and 7.6% (95% CI, 1.9%–12.8%) with the hdPS, and there was no improvement with PS-Clinical (−1.2%; 95% CI, −6.5% to 3.9%), which already includes LVEF and core physiology. Findings were similar in the expanded panel of approximately 330 characteristics (relative reduction, 9.8%; 95% CI, 6.3%–13.2%) and across all 38 emulated trials (12.6%; 95% CI, 7.8%–16.6%) (eTable 5; eFigure 3).

### Agreement with RCT results

With PS-Demo, adding the ECG moved emulated estimates closer to RCT results (Figure 3A; eFigure 4). The mean absolute difference between emulated and RCT log HRs decreased from 0.251 to 0.205 (20 of 32 trials closer; P = .008), the correlation with RCT estimates increased from 0.51 to 0.59, and standardized difference agreement increased from 20 to 27 of 32 trials. The reduction remained nominally significant with clustering by comparator (P = .026) and after omission of any single trial (maximum P = .016), and it was borderline after false discovery rate control (q = .051). However, it was not specific to each trial's own RCT result (benchmark-permutation P = .27), indicating that the ECG largely attenuated extreme estimates rather than correcting each emulation toward its trial.

The gain in agreement was smaller with richer PS specifications (Figure 3B and 3D). The mean absolute difference decreased from 0.226 to 0.196 with PS-CVD5 (P = .049), from 0.181 to 0.167 with the hdPS (P = .20) and from 0.158 to 0.155 with PS-Clinical (P = .42). Agreement metrics for each specification, including all 38 emulated trials, are shown in eTable 7.

Agreement with RCT results was closer for emulations rated excellent or good (n = 15) than for those rated moderate (n = 17) (Figure 3C; eTable 8). With PS-Clinical, the correlation with RCT estimates was 0.83 vs 0.39 and standardized difference agreement was 100% vs 71%, respectively. Among excellent or good emulations, adding the ECG to PS-Demo increased standardized difference agreement from 67% to 93% and reduced the mean absolute difference in 11 of 15 trials (P = .009), whereas the change among moderate emulations was smaller (9 of 17 trials; P = .13). These comparisons were post hoc.

### Plasmode simulation

In plasmode simulations across 107 trial–confounder combinations in 31 trials, the ECG embedding removed part, but not most, of the bias from an unmeasured physiological confounder (Figure 4). In the post hoc design in which the withheld confounder alone determined treatment and LVEF and estimated glomerular filtration rate were oriented clinically, a PS built from the ECG embedding alone removed 18.0% of the bias overall: 27.9% for LVEF, 22.2% for NT-proBNP, 17.5% for body mass index and 9.7% for estimated glomerular filtration rate. Adjustment for the confounder itself removed 93.1% of the bias, and the permuted-ECG placebo removed none (−0.2%).

Added to an existing PS, the ECG removed a further 14.9% of the remaining bias with PS-Demo, 8.6% with the hdPS and 11.7% with PS-Clinical from which the confounder was withheld (22.4%, 13.0% and 13.7%, respectively, for LVEF). The proportion of bias removed tracked how well the ECG predicted the confounder in the real data, at approximately 100 × the partial R² given demographics (Figure 4A); the median R² across the 38 trials was 0.26 for LVEF, 0.22 for body mass index, 0.20 for NT-proBNP and 0.04 for estimated glomerular filtration rate. Coverage of the true effect remained below nominal for every PS that included the ECG (68%–83%; oracle, 95%). In the initial design, in which higher values of every confounder increased treatment and hazard, adding the ECG to PS-Demo removed 14.2% of the bias (LVEF, 9.1%; estimated glomerular filtration rate, −4.8%), and this proportion was unchanged at true HRs of 0.6, 0.8 and 1.0 (eFigure 5).

### Comparison with measured physiology

Among patients with a pre-index echocardiogram (20 trials) or NT-proBNP measurement (16 trials), adding the ECG to PS-Demo closed 60% of the LVEF imbalance and 39% of the NT-proBNP imbalance that was closed by adjustment for the measured value itself (permuted ECG, 3% and −4%, respectively). The placebo-corrected share of the corresponding HR shift reproduced by the ECG was 0.27 (95% CI, −0.31 to 0.72) for LVEF, consistent with the simulation prediction of 0.23 but imprecise (eFigure 6).

### External validation in MIMIC-IV

In MIMIC-IV, 7 cardiovascular trials and 1 negative-control trial met the feasibility criteria, with 441 to 1,841 matched pairs per cardiovascular trial with PS-Demo (eTable 4). Adding the ECG embedding to PS-Demo reduced the mean |SMD| across the 26 held-out characteristics by 10.3% (95% CI, 6.4%–14.5%), with improvement in all 7 cardiovascular trials (P = .008), and increased the proportion of balanced characteristics from 41.2% to 51.6% (eFigure 7). The permuted-ECG placebo did not improve balance (−2.5%). The reduction was 14.5% (95% CI, 9.5%–19.8%) after exclusion of patients whose ECG was recorded on the index day and, as in the primary analysis, was smaller with the hdPS (7.5%; 95% CI, −0.4% to 16.2%) and PS-Clinical-lite (1.2%; 95% CI, −9.1% to 11.8%).

Agreement with RCT results improved directionally but not significantly. With PS-Demo, the mean absolute difference from RCT log HRs decreased from 0.337 to 0.315 (4 of 7 trials closer; P = .27), and it decreased with the ECG for each of the 4 PS specifications, with the ECG outperforming the permuted-ECG placebo for 3 of 4. The correlation with RCT estimates and standardized difference agreement did not improve with PS-Demo (0.71 to 0.67; 5 to 4 of 7 trials) (eTable 9). In the negative-control trial, for which the RCT relative risk was 1.05, PS-Demo yielded an HR of 1.53 (95% CI, 1.36–1.71); adding the ECG moved the estimate toward the null (HR, 1.39; 95% CI, 1.24–1.56), whereas the permuted-ECG placebo did not (HR, 1.61).

### Sensitivity analyses

The balance gain was consistent across alternative matching and weighting approaches, with relative reductions of 11.2% to 14.4% with a caliper of 0.1, 1:3 matching, inverse probability weighting and overlap weighting, and it was smaller with a gradient-boosted PS (6.6%; 95% CI, 1.5%–11.2%). The gain increased with the number of ECG components, from 6.8% with 4 components to a plateau of 11% to 15% with 32 to 256 components. The mean absolute difference from RCT results decreased with every approach except the gradient-boosted PS (P = .09), and the benchmark-permutation test was not significant for any approach (P = .26 to .85) (eTable 6).

Restriction to patients who initiated treatment as outpatients was possible in 29 of the 38 emulated trials, including all 6 limited-quality emulations. In these trials, the balance gain with PS-Demo was smaller than among all initiators (+2.3 vs +5.7 percentage points; 17 of 29 trials; P = .035), suggesting that part of the gain reflects differences in care setting captured by the ECG. In the 23 of these trials in the primary set, the gain was +2.2 percentage points (12 of 23 trials; P = .083; relative reduction, 7.7%; 95% CI, 2.6%–12.5%), compared with +4.9 points (P = .008) among all initiators in the same trials. After restriction, the ECG no longer reduced the distance from RCT results (0.213 to 0.196; 14 of 29 trials closer; P = .24), and the standard error of the log HR increased by a median factor of 1.37 (eFigure 8).

Among the 28 primary-set trials with an applicable on-treatment estimand, adding the ECG reduced the mean absolute difference from RCT results with the switch-only estimand (0.253 to 0.199; 21 of 28 trials closer; P = .002) and with the per-protocol estimand with a 365-day grace period (0.302 to 0.241; 21 of 28 trials; P = .008), but not in the 90-day landmark analysis (0.225 to 0.229; 16 of 28 trials; P = .56). In the 22 trials in which the 90-day run-in analysis was estimable, the difference decreased from 0.502 to 0.307 (15 of 22 trials; P = .065) (eTable 11).

In the prespecified confirmation analysis of 15 trials, adding the ECG increased the proportion of balanced characteristics from 52.4% to 58.3% (11 of 15 trials; P = .033) and reduced the mean absolute difference from RCT results from 0.250 to 0.208 (P = .074; benchmark-permutation P = .97). The prespecified confirmation in 5 AF trials did not replicate the agreement finding: the mean absolute difference decreased from 0.254 to 0.199 (3 of 5 trials closer; P = .19; benchmark-permutation P = .28), and with PS-CVD5 the ECG worsened agreement (0.135 to 0.212) (eTable 10). *In the CLMBR-T sensitivity analysis, structured-EHR embeddings also improved balance, and adding the ECG to them improved it further (eTable 12).*

## Tables and Figures

**Table 1. Target trial specification (PICOT) and emulation quality for the 38 emulated trials**


| Area         | Trial             | Population                                                  | Intervention              | Comparator                    | Outcome (RCT primary endpoint)                                       | Time (mo) | RCT estimate (CI)                                     | Emulation quality (points) |
| ------------ | ----------------- | ----------------------------------------------------------- | ------------------------- | ----------------------------- | -------------------------------------------------------------------- | --------- | ----------------------------------------------------- | -------------------------- |
| AF           | ARISTOTLE         | AF                                                          | apixaban                  | warfarin                      | stroke or systemic embolism                                          | 22        | 0.79 (0.66–0.95)                                      | Excellent (0)              |
| AF           | ROCKET-AF         | AF                                                          | rivaroxaban               | warfarin                      | stroke or systemic embolism                                          | 23        | 0.88 (0.74–1.03)                                      | Excellent (0)              |
| AF           | RE-LY             | AF                                                          | dabigatran                | warfarin                      | stroke or systemic embolism                                          | 24        | 0.66 (0.53–0.82) [RR]                                 | Excellent (0)              |
| AF           | EAST-AFNET 4      | Early AF (diagnosis ≤1 y) on rate control                   | rhythm-control drug added | continued rate control        | CV death, stroke, HF or ACS hospitalisation                          | 61        | 0.79 (0.66–0.94) [96% CI]                             | Moderate (3)               |
| AF           | CABANA            | AF                                                          | catheter ablation         | antiarrhythmic drug           | death, disabling stroke, serious bleeding or cardiac arrest          | 49        | 0.86 (0.65–1.15)                                      | Moderate (3)               |
| AF           | AFFIRM            | AF on rate control, age ≥65                                 | rhythm-control drug added | continued rate control        | all-cause death                                                      | 42        | 1.15 (0.99–1.34)                                      | Good (1)                   |
| AF           | AF-CHF            | AF with HF on rate control                                  | rhythm-control drug added | continued rate control        | CV death                                                             | 37        | 1.06 (0.86–1.30)                                      | Good (2)                   |
| AF           | FRAIL-AF          | AF on warfarin, age ≥75                                     | switch to DOAC            | warfarin                      | major or clinically relevant non-major bleeding                      | 12        | 1.69 (1.23–2.32) [cause-specific HR]                  | Moderate (2)               |
| AF           | LAAOS III         | AF undergoing cardiac surgery                               | surgical LAA occlusion    | surgery without LAA occlusion | ischaemic stroke or systemic embolism                                | 46        | 0.67 (0.53–0.85)                                      | Good (2)                   |
| AF           | PROTECT AF        | AF on warfarin with ≥1 stroke risk factor                   | percutaneous LAA closure  | warfarin                      | stroke, CV death or systemic embolism                                | 18        | 0.62 (0.35–1.25) [rate ratio] [95% credible interval] | Good (1)                   |
| AF           | RAFT-AF           | AF with HF on rate control                                  | catheter ablation         | continued rate control        | all-cause death or HF event                                          | 36        | 0.71 (0.49–1.03)                                      | Good (2)                   |
| AF           | ACTIVE W          | AF with ≥1 stroke risk factor, age ≥55                      | clopidogrel               | warfarin                      | stroke, non-CNS systemic embolism, MI or vascular death              | 15        | 1.44 (1.18–1.76) [RR]                                 | Moderate (3)               |
| HF           | COMET             | HF                                                          | carvedilol                | metoprolol                    | all-cause mortality                                                  | 58        | 0.83 (0.74–0.93)                                      | Good (1)                   |
| HF           | PARADIGM-HF       | HF on ACEi/ARB (switch at time zero)                        | sacubitril-valsartan      | ACEi                          | CV death or first HF hospitalisation                                 | 27        | 0.80 (0.73–0.87)                                      | Moderate (3)               |
| HF           | TRANSFORM-HF      | HF hospitalisation (discharge within 30 d)                  | torsemide                 | furosemide                    | all-cause mortality                                                  | 12        | 1.02 (0.89–1.18)                                      | Moderate (2)               |
| HF           | ELITE II          | HF, age ≥60                                                 | ARB                       | ACEi                          | all-cause mortality                                                  | 18        | 1.13 (0.95–1.35) [95.7% CI]                           | Good (1)                   |
| HF           | EMPEROR-Preserved | HF with T2D                                                 | SGLT2i                    | DPP-4i (placebo proxy)        | CV death or HF hospitalisation                                       | 26        | 0.79 (0.69–0.90)                                      | Moderate (3)               |
| Hypertension | LIFE              | Hypertension with ECG-LVH, age 55–80                        | ARB                       | β-blocker                     | CV death, MI or stroke                                               | 58        | 0.87 (0.77–0.98)                                      | Moderate (3)               |
| Hypertension | ALLHAT            | Hypertension, age ≥55                                       | amlodipine                | thiazide                      | fatal CHD or nonfatal MI                                             | 59        | 0.98 (0.90–1.07) [RR]                                 | Limited (4)                |
| Hypertension | VALUE             | Hypertension, age ≥50                                       | ARB                       | amlodipine                    | cardiac morbidity and mortality composite                            | 50        | 1.04 (0.94–1.15)                                      | Limited (4)                |
| Hypertension | ASCOT-BPLA        | Hypertension, age 40–79                                     | amlodipine                | β-blocker                     | nonfatal MI and fatal CHD                                            | 66        | 0.90 (0.79–1.02)                                      | Limited (4)                |
| Hypertension | INSIGHT           | High-risk hypertension, age ≥55                             | nifedipine                | thiazide                      | CV death, MI, HF or stroke                                           | 42        | 1.10 (0.91–1.34) [RR]                                 | Good (2)                   |
| ACS / MI     | PLATO             | ACS within 30 d                                             | ticagrelor                | clopidogrel                   | vascular death, MI or stroke                                         | 12        | 0.84 (0.77–0.92)                                      | Good (2)                   |
| ACS / MI     | VALIANT           | MI within 30 d                                              | ARB                       | ACEi                          | all-cause death                                                      | 25        | 1.00 (0.90–1.11) [97.5% CI]                           | Good (2)                   |
| Diabetes     | EMPA-REG OUTCOME  | T2D with established CVD                                    | SGLT2i                    | DPP-4i (placebo proxy)        | 3-point MACE                                                         | 37        | 0.86 (0.74–0.99) [95.02% CI]                          | Moderate (3)               |
| Diabetes     | CAROLINA          | T2D                                                         | linagliptin               | glimepiride                   | 3-point MACE                                                         | 76        | 0.98 (0.84–1.14) [95.47% CI]                          | Good (2)                   |
| Diabetes     | LEADER            | T2D with CVD, age ≥50                                       | liraglutide               | DPP-4i (placebo proxy)        | CV death, nonfatal MI or nonfatal stroke                             | 46        | 0.87 (0.78–0.97)                                      | Moderate (3)               |
| Diabetes     | SUSTAIN-6         | T2D with CVD, age ≥50                                       | semaglutide               | DPP-4i (placebo proxy)        | CV death, nonfatal MI or nonfatal stroke                             | 25        | 0.74 (0.58–0.95)                                      | Moderate (3)               |
| Diabetes     | REWIND            | T2D, age ≥50                                                | dulaglutide               | DPP-4i (placebo proxy)        | nonfatal MI, nonfatal stroke or CV death (incl. unknown causes)      | 65        | 0.88 (0.79–0.99)                                      | Limited (4)                |
| Diabetes     | DECLARE-TIMI 58   | T2D, age ≥40                                                | dapagliflozin             | DPP-4i (placebo proxy)        | CV death or HF hospitalisation                                       | 50        | 0.83 (0.73–0.95)                                      | Limited (4)                |
| Diabetes     | CANVAS Program    | T2D, age ≥30                                                | canagliflozin             | DPP-4i (placebo proxy)        | CV death, nonfatal MI or nonfatal stroke                             | 43        | 0.86 (0.75–0.97)                                      | Moderate (3)               |
| Diabetes     | TECOS             | T2D with CVD, age ≥50                                       | sitagliptin               | sulfonylurea (placebo proxy)  | CV death, nonfatal MI, nonfatal stroke or UA hospitalisation         | 36        | 0.98 (0.88–1.09)                                      | Moderate (3)               |
| Diabetes     | CARMELINA         | T2D with kidney disease                                     | linagliptin               | sulfonylurea (placebo proxy)  | CV death, nonfatal MI or nonfatal stroke                             | 26        | 1.02 (0.89–1.17)                                      | Moderate (3)               |
| Other        | ONTARGET          | Established vascular disease or high-risk diabetes, age ≥55 | ARB                       | ACEi                          | CV death, MI, stroke or HF hospitalisation                           | 56        | 1.01 (0.94–1.09) [RR]                                 | Limited (4)                |
| Other        | PRECISION         | Arthritis with CV risk                                      | celecoxib                 | naproxen                      | CV death (incl. haemorrhagic), nonfatal MI or nonfatal stroke (APTC) | 34        | 0.93 (0.76–1.13)                                      | Good (2)                   |
| Other        | AMPLIFY           | Acute VTE                                                   | apixaban                  | warfarin                      | recurrent symptomatic VTE or VTE-related death                       | 6         | 0.84 (0.60–1.18) [RR]                                 | Moderate (2)               |
| Other        | LODESTAR          | Coronary artery disease                                     | rosuvastatin              | atorvastatin                  | 3-y death, MI, stroke or any coronary revascularisation              | 36        | 1.06 (0.86–1.30)                                      | Moderate (2)               |
| Other        | PROVE IT-TIMI 22  | ACS within 30 d                                             | atorvastatin              | pravastatin                   | death, MI, UA rehospitalisation, revascularisation >= 30 d or stroke | 24        | 0.84 (0.74–0.95)                                      | Moderate (3)               |




*Abbreviations:*

- ACEi, angiotensin-converting enzyme inhibitor; ARB, angiotensin receptor blocker;
- ACS, acute coronary syndrome; AF, atrial fibrillation; CAD, coronary artery disease; CHD, coronary heart disease; CV, cardiovascular; CVD, cardiovascular disease; HF, heart failure; MI, myocardial infarction; MACE, major adverse cardiovascular events; UA, unstable angina; VTE, venous thromboembolism;
- DOAC, direct oral anticoagulant; DPP-4i, dipeptidyl peptidase-4 inhibitor; SGLT2i, sodium-glucose cotransporter-2 inhibitor; LAA, left atrial appendage;
- LVH, left ventricular hypertrophy; T2D, type 2 diabetes.

*Notes:*

- RCT estimates are hazard ratios unless indicated; intervals are 95% CIs unless indicated (PROTECT AF, Bayesian 95% credible interval). ROCKET-AF is the intention-to-treat estimate; the published primary analysis was per-protocol (HR 0.79; 95% CI, 0.66–0.96).
- Time is the trial-matched follow-up horizon.
- "Placebo proxy" marks placebo-controlled trials emulated with an active comparator.
- Emulation quality is the adjudicated four-tier rating, made from design information and blind to emulation results, with total design points in parentheses: excellent, 0 points; good, 1–2 points with no poor item and at most one flag; moderate, 3 points, or 1–2 points with a poor item or two flags; limited, ≥4 points (eMethods 3). Limited emulations were excluded from the primary analysis set.
- The emulated outcome omitted components that could not be ascertained from EHR data in LODESTAR and PROVE IT-TIMI 22 (coronary revascularization), AMPLIFY (VTE-related death), FRAIL-AF (clinically relevant non-major bleeding) and CABANA (disabling stroke) (eTable 1).
- Full eligibility criteria, code lists and adaptations are given in eTable 1.

**Figure 1. Study design and trial selection.** Data sources, the two-stage selection of trials (99 candidates, 38 emulated, 32 analysed) and the MIMIC-IV external validation cohort. *(Draft: docs/paper/figures/main/)*

**Figure 2. Balance on held-out characteristics.** A, Love plot of the 58 held-out characteristics before matching and after matching on PS-Demo and PS-Demo + ECG (median across 32 trials). B, Mean |SMD| by domain. C, Mean |SMD| before matching and with each PS specification, with and without the ECG. D, Per-trial change in the proportion of balanced characteristics with the ECG. *(Draft: docs/paper/figures/main/)*

**Figure 3. Agreement of emulated and RCT results.** A, Emulated vs RCT log HRs with the PS alone and with the ECG embedding. B, Mean absolute difference from RCT log HRs by PS specification, with the benchmark-permutation null. C, Standardized difference agreement by emulation quality for each PS specification. D, RCT-DUPLICATE agreement metrics for each PS specification. *(Draft: docs/paper/figures/main/)*

**Figure 4. Plasmode simulation.** A, Proportion of bias removed by the ECG embedding vs the ECG's R² for the withheld confounder, by trial–confounder combination. B, Bias removed by the ECG alone and when added to each PS, by confounder (adjustment for the confounder itself removed 93.1% and is not shown). *(Draft: docs/paper/figures/main/)*

**Supplementary figures** (docs/paper/figures/supplementary/):

- eFigure 1, trial selection flow with exclusion reasons;
- eFigure 2, per-characteristic balance (58 characteristics);
- eFigure 3, expanded-panel balance by domain;
- eFigure 4, per-trial emulated vs RCT HRs;
- eFigure 5, simulation robustness (true HRs of 0.6, 0.8 and 1.0; Monte Carlo standard errors);
- eFigure 6, echocardiography-subset analysis;
- eFigure 7, MIMIC-IV per-trial balance and HRs;
- eFigure 8, sensitivity analyses (outpatient initiators and alternative estimands).

**Supplementary tables** (to be built): eTable 1, target trial specifications and emulation adaptations; eTable 2, held-out characteristics and expanded-panel sources; eTable 3, trial cohorts; eTable 4, MIMIC-IV cohorts; eTable 5, expanded panel and 38-trial balance; eTable 6, matching, weighting, PS-model and ECG-component sensitivity analyses; eTable 7, agreement metrics by PS specification and trial set; eTable 8, agreement by emulation quality; eTable 9, MIMIC-IV agreement; eTable 10, prespecified confirmation analyses; eTable 11, on-treatment, landmark and run-in estimands; eTable 12, CLMBR-T comparisons.

## Discussion

*(pending)*

## References

1. Hernán MA, Robins JM. *Causal Inference: What If.* Boca Raton: Chapman & Hall/CRC; 2020.
2. Sherman RE, Anderson SA, Dal Pan GJ, et al. Real-world evidence — what is it and what can it tell us? *N Engl J Med.* 2016;375:2293–2297.
3. Hernán MA, Robins JM. Using big data to emulate a target trial when a randomized trial is not available. *Am J Epidemiol.* 2016;183:758–764.
4. Franklin JM, Patorno E, Desai RJ, et al. Emulating randomized clinical trials with nonrandomized real-world evidence studies: first results from the RCT DUPLICATE initiative. *Circulation.* 2021;143:1002–1013.
5. Wang SV, Schneeweiss S; RCT-DUPLICATE Initiative. Emulation of randomized clinical trials with nonrandomized database analyses: results of 32 clinical trials. *JAMA.* 2023;329:1376–1385.
6. Haneuse S, Arterburn D, Daniels MJ. Assessing missing data assumptions in EHR-based studies: a complex and underappreciated task. *JAMA Netw Open.* 2021;4:e210184.
7. Attia ZI, Kapa S, Lopez-Jimenez F, et al. Screening for cardiac contractile dysfunction using an artificial intelligence–enabled electrocardiogram. *Nat Med.* 2019;25:70–74.
8. Dhingra LS, Aminorroaya A, Sangha V, et al. Ensemble deep learning algorithm for structural heart disease screening using electrocardiographic images: PRESENT SHD. *J Am Coll Cardiol.* 2025;85:1302–1313.
9. Dhingra LS, Aminorroaya A, Sangha V, Pedroso AF, Asselbergs FW, Brant LCC, Barreto SM, Ribeiro ALP, Krumholz HM, Oikonomou EK, Khera R. Heart failure risk stratification using artificial intelligence applied to electrocardiogram images: a multinational study. *Eur Heart J.* 2025;46(11):1044–1053. doi:10.1093/eurheartj/ehae914
10. Sangha V, Khunte A, Holste G, Mortazavi BJ, Wang Z, Oikonomou EK, Khera R. Biometric contrastive learning for data-efficient deep learning from electrocardiographic images. *J Am Med Inform Assoc.* 2024;31(4):855–865.
11. Johnson AEW, Bulgarelli L, Shen L, et al. MIMIC-IV, a freely accessible electronic health record dataset. *Sci Data.* 2023;10:1. doi:10.1038/s41597-022-01899-x
12. Gow B, Pollard T, Nathanson LA, et al. MIMIC-IV-ECG: diagnostic electrocardiogram matched subset (version 1.0). PhysioNet. 2023. doi:10.13026/4nqg-sb35
13. Cashin AG, Hansford HJ, Hernán MA, et al. Transparent reporting of observational studies emulating a target trial: the TARGET statement. *JAMA.* 2025;334(12):1084–1093. doi:10.1001/jama.2025.13350
14. Wornow M, Thapa R, Steinberg E, Fries JA, Shah NH. EHRSHOT: an EHR benchmark for few-shot evaluation of foundation models. *Adv Neural Inf Process Syst.* 2023;36.
15. Schneeweiss S, Rassen JA, Glynn RJ, Avorn J, Mogun H, Brookhart MA. High-dimensional propensity score adjustment in studies of treatment effects using health care claims data. *Epidemiology.* 2009;20:512–522.
16. Austin PC. Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples. *Stat Med.* 2009;28:3083–3107.
17. Franklin JM, Schneeweiss S, Polinski JM, Rassen JA. Plasmode simulation for the evaluation of pharmacoepidemiologic methods in complex healthcare databases. *Comput Stat Data Anal.* 2014;72:219–226.
18. Heyard R, Held L, Schneeweiss S, Wang SV. Design differences and variation in results between randomised trials and non-randomised emulations: meta-analysis of RCT-DUPLICATE data. *BMJ Med.* 2024;3:e000709.
19. Morris TP, White IR, Crowther MJ. Using simulation studies to evaluate statistical methods. *Stat Med.* 2019;38:2074–2102.



## Supplementary Methods (eMethods)



### eMethods 1. Data sources

YNHHS comprises multiple hospitals and an extensive outpatient network across Connecticut and Rhode Island. Our team mapped the structured Epic data to the OMOP common data model, covering diagnoses (ICD-10-CM), medication orders, procedures, laboratory measurements, vital signs and encounters; source Epic tables supplemented the mapped data for race, ethnicity and hospital encounters. Echocardiographic measurements were taken from structured echocardiography reports; free text was not used. Echocardiographic held-out values were set to missing for index dates before July 31, 2016, the start of the structured echocardiography source. Deaths were identified from the EHR and from linked Connecticut vital statistics records, which also provided the listed causes of death. ECGs were retrieved from the institutional archive as raw 10-second, 500 Hz 12-lead signals. Follow-up extended through December 2024 for all-cause death and June 2024 for cause-specific death.

### eMethods 2. Emulation design (PICOT)

The population comprised patients meeting the trial's key eligibility criteria as operationalized from structured data. All were aged 18 years or older (or the trial minimum) and had a first recorded encounter at least 365 days before the index date, and exclusion criteria that could be ascertained were applied. New users of the intervention were compared with new users of the comparator. Time zero was the first order of the study drug or procedure, with no order for the comparator in the preceding 365 days. Where the trial tested adding or switching therapy against continuing existing treatment, for example rhythm control added to rate control or switching from warfarin, a sequential design was used. For placebo-controlled trials, an active comparator without an expected effect on the outcome served as a placebo proxy, for example dipeptidyl peptidase-4 inhibitors in trials of glucose-lowering drugs. The outcome was the trial's primary endpoint, mapped to EHR events; hospitalization components required a qualifying ICD-10 code during an inpatient stay, and cardiovascular death was defined from listed causes of death. Follow-up began the day after time zero and continued to the primary endpoint, death, end of data or a trial-matched horizon, whichever came first. eTable 1 lists, for each trial, the PICOT elements and the TARGET protocol components (eligibility, treatment strategies, assignment, time zero, follow-up, outcome, causal contrast and analysis), each with its emulated counterpart and any adaptation.

### eMethods 3. Trial selection and emulation quality

Trials were assembled in three stages: 18 trials in which the analytic approach was developed; 15 trials, drawn largely from RCT-DUPLICATE, analysed under a prespecified plan; and 5 AF trials analysed under a separate prespecified plan. For the second and third stages, trial specifications, benchmarks and the analysis plan were committed before any results were computed, and results for these prespecified sets are reported in eTable 10. A count-only screen of pooled event numbers preceded registration of the second stage, and the AF hypothesis tested in the third stage arose from a post hoc pattern in second-stage results. Four further trials were built during early development but are not among the 38: PARAGON-HF, DAPA-HF/EMPEROR-Reduced and PARTNER had fewer than 400 matched pairs with PS-Clinical, the data-sufficiency threshold of the development protocol, and the primary outcome of DIONYSOS (recurrence of AF) could not be ascertained. Because their results had been examined, none was eligible for the prespecified confirmation stages. Of 99 candidate RCTs, 38 were emulated (eFigure 1). Candidates were counted as individual RCTs: design variants of the same trial were counted once, and grouped entries in screening lists were counted separately. Reasons for exclusion were a placebo-only design without an accepted proxy, an endpoint not ascertainable from EHR data, an exposure that could not be identified, insufficient size, or a near-duplicate cohort. Size was assessed from pooled counts only, as at least 300 patients with an ECG in the smaller arm and at least 50 pooled primary events. Cohorts sharing 80% or more of patient–index date records with an existing cohort were considered near-duplicates. This rule was added after the initial count-only screen; overlap of 50% to 80% was permitted (for example, 69% between ACTIVE W and RE-LY), and the 18 development cohorts were not compared with one another.

Emulation quality was rated from design information only, without reference to emulation results. Five design deviations were scored, following the RCT-DUPLICATE classification of emulation differences:^5^ in-hospital initiation not mirrored in the emulation (F1), a selective run-in period (F2), discontinuation or replacement of an ongoing same-purpose therapy at randomization that the emulation did not reproduce (F3), a horizon of 48 months or longer with a delayed treatment effect (F4), and other misalignment of time zero (F5). Comparator and outcome fidelity were each graded good, moderate or poor. A poor comparator denoted a placebo proxy or a substitution that changed the trial hypothesis, and a poor outcome a primary endpoint that could not be validly ascertained. Each flag scored 1 point, and comparator and outcome fidelity scored 0, 1 or 2 points for good, moderate or poor, giving a total of 0 to 9. Trials were classified as excellent (0 points), good (1–2 points, with no poor item and at most one flag), moderate (3 points, or 1–2 points with a poor item or two flags) or limited (≥4 points). The points were additive because design differences contribute approximately additively to disagreement between RCTs and their emulations,^18^ and poor proxies were weighted double because they agreed worst in RCT-DUPLICATE.^4^ The ratings were first made as a three-class classification and then independently re-rated by a second reviewer from design information, blind to all emulation results. The second reviewer was inadvertently exposed to the first three-class labels, so the agreement may be overstated; both ratings were made with large-language-model assistance [PI: confirm the wording of this disclosure]. Agreement on the three-class result was 82% (Cohen κ, 0.71) and disagreements were adjudicated against the written rules. The graded scale was defined after the primary analyses had been run but from design items only, and analyses by emulation quality are therefore post hoc. Of the 38 emulated trials, 3 were rated excellent, 12 good, 17 moderate and 6 limited; the 6 limited emulations (ALLHAT, ASCOT-BPLA, DECLARE-TIMI 58, ONTARGET, REWIND and VALUE) were excluded from the primary analysis set. The relevance of ECG-reflected physiology to each trial was graded high, medium or low according to whether treatment choice and prognosis plausibly depend on it.

### eMethods 4. ECG and EHR representations

The ECG model is a convolutional encoder followed by a transformer over leads and time, applied to 10-second, 500 Hz 12-lead signals in microvolts and trained in-house with the BCL objective of the published image-based model.^10^ [PI: add the training data (number of ECGs and patients, years, and whether trial cohorts were excluded) and training details.] In echocardiography-linked ECGs from 8,127 held-out patients outside the COMET cohort, linear probes on the embedding detected LVEF ≤40% with an area under the curve of 0.90 and AF with an area under the curve of 0.95, and explained 32% of the variance in LVEF. The frozen encoder produced 256-dimensional embeddings, from which the first 32 principal components were computed within each trial. Two placebos were used: a permuted-ECG placebo, in which embeddings were reassigned at random between patients within each cohort, and a noise placebo of independent Gaussian variables (96 columns, matching the combined CLMBR-T and ECG representation, in the real-data analyses; 32 columns in the simulation). CLMBR-T-base is a 141-million-parameter model pretrained on the structured EHR data of 2.57 million patients at Stanford.^14^ It was applied frozen to coded history strictly before the index day (codes only; the most recent 4,096 tokens), and its 768-dimensional representations were reduced to 64 principal components.

### eMethods 5. Propensity score specifications and matching

Four PS specifications are reported. PS-Demo included age, sex and calendar year of index. PS-CVD5 added hypertension, type 2 diabetes, coronary artery disease, AF and heart failure. The hdPS followed the approach of Schneeweiss et al.^15^ Its base covariates were demographics and 9 to 13 investigator-selected diagnoses recorded in the prior 365 days, including cardiovascular conditions and conditions such as diabetes, chronic kidney disease and chronic lung disease. Pre-index diagnosis, medication and procedure codes with a prevalence of at least 2% were converted into indicators of any, sporadic (at least the median count among patients with the code) and frequent (at least the 75th percentile) recurrence, and laboratory tests into indicators of having been measured. Indicators were ranked by the absolute log ratio of their prevalence in the two treatment groups (with an offset of 0.001), and the top 200 indicators were added to the base covariates. Unlike the original algorithm, codes were ranked on their association with treatment only, not with the outcome, so that selection never used outcome data; candidates were drawn from a random half of the code features, the other half being reserved for balance assessment, and the trial's exposure drugs were excluded. PS-Clinical comprised a median of 32 covariates per trial (range, 28–37). The 24 covariates common to all trials were age, sex, index year; AF, hypertension, diabetes, ischemic heart disease or myocardial infarction, chronic kidney disease, chronic obstructive pulmonary disease or asthma, peripheral artery disease, stroke and valve disease; LVEF, systolic and diastolic blood pressure, heart rate, body mass index, creatinine, potassium, sodium and hemoglobin; and outpatient, emergency department and inpatient encounter counts. Trial-specific covariates comprised 3 to 10 medication orders relevant to the clinical area and additional diagnoses such as heart failure, transient ischemic attack, liver disease and prior bleeding. Diagnoses were ascertained in the prior 365 days and medication orders in the prior 90 days. For laboratory values and vital signs, the latest value in the prior 90 days (365 days for body mass index and LVEF) was used and set to missing if implausible. Items describing the index event in acute coronary syndrome trials (ST-elevation myocardial infarction and percutaneous coronary intervention within 30 days) used a window that included the index day. Missing values in PS-Clinical were completed with a single imputation by chained equations (posterior sampling, with all covariates and treatment as predictors and no outcome information).

All PS were estimated by L2-penalized logistic regression on standardized covariates with an inverse regularization strength of 1 (scikit-learn), which stabilizes estimates when covariates are numerous, correlated or sparse. The same specification was used for every covariate set, so that only the covariates differed between comparisons. Matching was greedy 1:1 nearest-neighbour matching without replacement on the PS logit. Patients in the smaller treatment group were processed in descending order of their predicted probability of membership in that group and matched to the nearest available patient within a caliper of 0.2 pooled within-group standard deviations of the logit in the analysed cohort. In sensitivity analyses in the 32 and 38 trials (eTable 6), we used a caliper of 0.1, 1:3 matching, inverse probability and overlap weighting, a gradient-boosted PS with 5-fold cross-fitting, and 4 to 256 ECG principal components.

### eMethods 6. Balance and agreement metrics

For each characteristic, the SMD was the difference in means between treatment groups in the matched sample divided by the pooled standard deviation of the unmatched analysed cohort, so that the denominator did not change between PS specifications. Held-out characteristics were not imputed. Diagnoses, procedures and medications were coded as present or absent in the look-back window, and laboratory and vital sign values were compared among patients with an observed value. The primary panel of 58 characteristics excluded every variable in the demographic and diagnosis-based PS; at PS-Clinical, the characteristics included in that PS were also removed. Its coded-record summaries include a prognostic score for the trial's primary outcome, which has demographic and diagnostic components and is retained at every PS specification, and summaries of held-out code features that can include diagnoses also present in the diagnosis-based PS.

The expanded panel was built from a review of 12 sources describing covariates in PS and trial emulation studies, including studies from our group, RCT-DUPLICATE protocols, the Sentinel PS tool, the hdPS and the OHDSI FeatureExtraction defaults; the sources and their citations are listed in eTable 2. The review yielded 150 candidate covariates, which were implemented as 431 variables from the OMOP and Epic data, with all look-back windows ending the day before index. Within each trial, we excluded variables defining the exposure, variables with prevalence below 1% or above 99% or observed in fewer than 1% of patients, variables not strictly measured before index, and 67 ECG-proximal variables that an ECG encodes directly. The last group comprised rhythm and conduction disorders, devices and pacing, ablation and cardioversion, ventricular arrhythmias, cardiomyopathy and heart failure, myocardial infarction, natriuretic peptide, rate- and rhythm-control drugs, prior ECG counts and composite scores with such components. For each PS, we also excluded variables that overlapped with that PS, including composite scores with PS components, and, for the hdPS, variables whose codes could enter its selection. This left about 245 to 336 characteristics per trial depending on the PS (median, about 330 with PS-Demo). Expanded-panel results are reported for PS-Demo only. In the expanded panel, each laboratory value also had an indicator of missingness included as its own characteristic. Variables were grouped into seven domains for display: comorbidities, medications, healthcare use and testing, additional laboratory values and vital signs, devices and procedures, risk and frailty scores, and preventive care.

For each trial and specification, we computed the proportion of characteristics with |SMD| <0.1 and the mean |SMD|. The relative reduction in mean |SMD| with the ECG was 1 minus the ratio of the across-trial mean of the mean |SMD| with the ECG to that without the ECG, with a percentile 95% CI from 4,000 bootstrap resamples of trials; it does not depend on a threshold. It was added post hoc to the prespecified proportion of characteristics with |SMD| <0.1. Changes in balance by characteristic and domain were examined descriptively.

For agreement with RCTs, let θ~E~ and θ~R~ be the emulated and RCT log HRs with standard errors s~E~ and s~R~. Estimate agreement was |θ~E~ − θ~R~| ≤1.96 s~R~, standardized difference agreement was |θ~E~ − θ~R~| / (s~E~^2^ + s~R~^2^)^1/2^ <1.96, and the Pearson correlation was computed between θ~E~ and θ~R~ across trials.^4,5^ The absolute difference |θ~E~ − θ~R~| was compared between specifications within each trial. In the benchmark-permutation test, RCT results were reassigned at random across trials 20,000 times, and the reduction in the mean absolute difference with the ECG was recomputed each time. A reduction larger than under reassignment indicates movement toward each trial's own result rather than a general shrinkage of extreme estimates.

### eMethods 7. Plasmode simulation

Simulations were run in 31 trials and 107 trial–confounder combinations. These were trials in which at least 300 patients per treatment group had the confounder recorded, after exclusion of one combination whose simulated event rate was less than half the observed rate. The confounders were echocardiographic LVEF, NT-proBNP (log-transformed), body mass index and estimated glomerular filtration rate, standardized within the analysis set. Treatment was simulated from a logistic model including the observed PS-Demo logit and the confounder, with an odds ratio of 1.25, 1.5 or 2 per standard deviation, and calibrated to the observed proportion treated. Event times were simulated from a Weibull proportional hazards model including the observed clinical covariates, with coefficients estimated in the real data, the confounder, with an HR of 1.25, 1.5 or 2 per standard deviation, and treatment, with a true HR of 0.80. A null scenario had no confounding. Censoring was administrative at the trial horizon or end of data. Real covariates, ECGs and index dates were retained, and simulated event rates were close to observed rates (median, 21.0% vs 20.4%). In each of 50 replicates per scenario, 80% of patients were sampled without replacement, treatment and outcome were redrawn, and every PS was refitted and rematched. The compared arms were PS-Demo alone and with the ECG components, the permuted-ECG placebo, 32 noise columns, or the confounder itself (oracle). The true marginal log HR in each matched population was computed from simulated potential outcomes under both treatments, which accounts for non-collapsibility. Bias was the mean difference between the estimated and true log HR, and the proportion of bias removed was 1 minus the ratio of bias with and without the added components, pooled over the nine confounding scenarios. We also report CI coverage of the true value. The ECG's ability to encode each confounder was estimated in the real data as the cross-fitted R^2^ of the confounder on the ECG components, and as the partial R^2^ given demographics. In the initial design, every confounder was oriented so that higher values increased both treatment and hazard. After this design had been examined, LVEF and estimated glomerular filtration rate were reoriented so that lower values increased treatment and hazard, as in clinical practice, because in the initial orientation their effects partly cancelled against those of the real covariates; a variant in which the outcome depended on the confounder and treatment only was also added. The main-text results combine the reoriented LVEF and estimated glomerular filtration rate scenarios with the unchanged NT-proBNP and body mass index scenarios; results of the initial design are reported in the supplement.

The compared PS were PS-Demo alone and with the ECG components; a PS on the ECG components alone and on the permuted ECG components alone; the hdPS, with codes re-ranked on the simulated treatment in each replicate, with and without the ECG; PS-Clinical with the confounder's own analogue removed (LVEF for LVEF, body mass index for body mass index, creatinine for estimated glomerular filtration rate), with and without the ECG; and the oracle. To isolate the bias induced by the confounder from demographic confounding and design artefacts, we subtracted, for each arm and subsample, the error in the scenario without confounding (null-corrected bias). The proportion of bias removed by the ECG-only PS was estimated in an additional post hoc design in which treatment depended on the confounder only. The added value of the ECG over each PS was 1 minus the ratio of the null-corrected bias with and without the ECG. We report Monte Carlo SEs from 1,000 resamples of replicates within cells, together with empirical SE, root mean squared error and coverage, following the ADEMP framework.^19^ To assess dependence on the true effect, the principal arms were re-run with true HRs of 1.0 and 0.6 using common random numbers.

### eMethods 8. Design-step diagnostics

Residual imbalance in ECG phenotypes was examined in the 38 trials across five successive design steps: initiators without trial eligibility criteria; the emulated trial population; matching on demographics and prior diagnoses; hdPS matching; and PS-Clinical matching. The mean |SMD| of ECG phenotypes fell from 0.206 to 0.144, 0.088, 0.079 and 0.075 across these steps, but residual imbalance after matching was not associated with the absolute difference from RCT results (Spearman ρ = −0.03; P = .85).

### eMethods 9. Sensitivity analyses

The on-treatment, landmark and run-in estimands were computed in the same matched samples as the primary estimate. Per-protocol effects censored patients at deviation from the assigned strategy, with grace periods of 180, 365 and 730 days and stabilized inverse-probability-of-censoring weights truncated at the 99th percentile; a switch-only estimand censored only at initiation of the comparator strategy. Because orders carry no days' supply, the switch-only estimand was considered the most reliable on-treatment estimand. We also estimated effects in a 90-day landmark analysis, which was added after the analysis plan, and in a 90-day run-in analysis requiring at least one repeat order of the assigned drug within 90 days, analogous to an active run-in. These estimands were not applicable to the four trials with a one-time procedure arm, and the run-in analysis was not estimable in trials with 50 or fewer patients retained. In a separate analysis, in which the PS was refitted and patients rematched, cohorts were restricted to patients initiating treatment outside an inpatient stay, using an a priori classification of each RCT's setting; this restriction was applicable in 29 of the 38 trials. Exclusion of the six limited-quality emulations from the primary analysis set, and analyses by emulation quality, were post hoc; all analyses are therefore also reported for the 38 emulated trials.

### eMethods 10. Statistical software

Core analyses used Python 3.11.16, with pandas 2.3.3, NumPy 2.4.6, DuckDB 1.5.5, scikit-learn 1.9.1, lifelines 0.30.3, SciPy 1.17.1 and matplotlib 3.11.2. ECG embeddings were computed with PyTorch 2.5.0, and CLMBR-T representations with PyTorch 2.13.0 and FEMR 0.2.3; principal components of both representations were computed in the core analysis environment. Tests were one-sided where the direction was prespecified and two-sided otherwise.

---



### eMethods 11. External validation in MIMIC-IV

MIMIC-IV contains deidentified EHR data for patients admitted to the emergency department or hospital at Beth Israel Deaconess Medical Center, and MIMIC-IV-ECG contains the matched diagnostic 12-lead ECG signals, which extend to approximately 2019.^11,12^ Candidate trials were screened against the feasibility criteria of the primary analysis, using the same thresholds: at least 300 patients with an ECG in the smaller treatment group and at least 50 primary-outcome events. Outcomes were restricted to those ascertainable in hospital data or from linked dates of death, which are complete for 1 year after discharge. Five trials (PLATO, ARISTOTLE, ROCKET AF, TRANSFORM-HF and COMET) had been built previously, and SOAP II (dopamine vs norepinephrine), ELITE II (angiotensin receptor blocker vs angiotensin-converting enzyme inhibitor in heart failure) and PEPTIC (proton pump inhibitor vs histamine-2 receptor antagonist in ventilated patients; negative control) were added from prespecified screen definitions. Before the new analyses, the previous estimates for the five existing trials were reproduced exactly. The ECG nearest before time zero was encoded with the same model and reduced to 32 principal components within each trial. The held-out panel comprised 26 characteristics: core laboratory values and vital signs (8), additional laboratory values (13; NT-proBNP, troponin T, lactate, albumin and others), mechanical ventilation at time zero (1) and healthcare use (4). The four PS specifications were PS-Demo; a sparse PS (PS-Sparse) of demographics and prior diagnoses; the hdPS; and a PS-Clinical-lite of core laboratory values, vital signs and healthcare use (LVEF was not available), whose components were removed from its held-out panel. The plan was committed before the new analyses, although estimates for the five previously built trials already existed. RE-LY and three trials requiring a proxy comparator also met the count thresholds but were not analysed. Laboratory values were compared among patients with an observed value, with indicators of missingness. Structured echocardiographic measurements were not used because their provenance could not be verified. Two RCT benchmarks were not HRs (SOAP II, odds ratio; PEPTIC, relative risk). Because 16% to 53% of ECGs were recorded on the index day, a sensitivity analysis excluded these patients.

### eMethods 12. Echocardiography subset

Within each trial, we analysed patients with a pre-index echocardiographic LVEF and, separately, patients with a pre-index NT-proBNP value, in trials with at least 300 patients in the smaller treatment group and at least 50 events within the subset (20 and 16 of the 32 trials). In each subset, we matched on PS-Demo alone, with the ECG components, with the permuted-ECG placebo, and with the measured value itself. The share of the imbalance closed by the ECG was the reduction in |SMD| for the measured value with the ECG divided by the reduction with the measured value itself; this measure was not in the analysis plan and is descriptive. The share of the HR shift reproduced by the ECG was the slope through the origin of the log HR change with the ECG on the log HR change with the measured value, pooled across trials, with a trial-level bootstrap 95% CI, and was corrected by subtracting the corresponding slope for the permuted-ECG placebo. The analysis plan was committed before results were computed.

### Draft notes (remove before submission)
- **PI comments, 2026-10-01 (third round):**
  - **Strikethrough:** the struck post hoc sentence in the Methods Simulation paragraph is removed. The post hoc status stays disclosed in the Results ("in the post hoc design") and in eMethods 7.
  - **External validation (Methods):** condensed to "analyses reimplemented in MIMIC-IV". Adaptations are in eMethods 11.
  - **Statistical analysis:** condensed. The audit-process sentence is dropped.
  - **Results:** restructured in the style of RCT-DUPLICATE and the LEGEND studies.
    - Each paragraph opens with its finding, followed by the supporting estimates.
    - There are panel-level figure references.
    - The MIMIC-IV cohort counts moved to the external-validation subsection.
    - The matching, weighting and component sensitivity analyses moved to Sensitivity analyses.
    - Echocardiography has its own subsection ("Comparison with measured physiology").
    - No numbers were changed.

- **PI bracket comments, 2026-10-01 (Introduction and Methods), and how each was handled:**
  - **Introduction:** TTE defined in a modifier clause; the final sentence of the physiology paragraph rewritten (the undefined "RWD" is removed).
  - **Trial selection:**
    - the RCT-DUPLICATE sourcing phrase is removed;
    - the two stages are now named *feasibility criteria* (can the trial be replicated in YNHHS) and *emulation-quality criteria* (how closely the emulation reproduces the trial design), with details in eMethods 3.
  - **BCL:** reduced to a modifier clause.
  - **CLMBR-T:**
    - the purpose clause is added. CLMBR-T embeds the *structured* EHR, so the text says "embeddings of other routinely collected data" rather than "unstructured";
    - the subsection is retitled "AI-ECG representation";
    - CLMBR-T is framed as a supplement-only sensitivity analysis in Methods and Results.
  - **PS names, used throughout the main text, eMethods, captions and figure labels:**
    - PS-Demo (demographics only);
    - PS-CVD5 (+5 cardiovascular/metabolic diagnoses);
    - hdPS (high-dimensional);
    - PS-Clinical;
    - in MIMIC-IV, PS-Sparse and PS-Clinical-lite;
    - arms are written e.g. "PS-Demo + ECG".
  - **Figures** regenerated with the new labels.
- **[PI: …] items to decide or supply (2026-10-01):**
  1. IRB protocol number (Data sources).
  2. Wording of the disclosure that the second quality rater was exposed to the first labels and that both ratings used large-language-model assistance (eMethods 3).
  3. ECG model training data and details (eMethods 4).
  4. Exclusion counts by reason for eFigure 1, from the screening log; the figure is still a placeholder.
  5. Target journal; this sets the abstract structure, the Key Points and the reference style.
  6. Whether to cite the 38 RCT publications (Table 1) and the 12 expanded-panel sources in the reference list, rather than only in eTable 2.
- **Final post-audit pass (2026-10-01).** Every MISMATCH, UNSUPPORTED and NOT CHECKED row of `docs/paper/AUDIT_MANUSCRIPT_2026-10-01.md` is closed or mapped to a [PI: …] item in `docs/paper/AUDIT_CLOSURE_2026-10-01.md`. Backup: `…/paper/backup/paper_pre_final_audit_2026-10-01.md`.
  - The paper is now journal-neutral: JAMA-specific limits, subtitle and abstract headings removed.
  - eTables are renumbered in order of first citation (old → new: 12→6, 6→7, 7→8, 8→9, 11→10, 9→11, 10→12). eFigures 5 and 8 are swapped (simulation robustness is now 5, sensitivity analyses 8), with the files, the figure script and CAPTIONS.md renamed to match. Older draft notes below keep the old numbers.
  - New numbers, all from aggregate outputs: cohort sizes (claude-v18-embed-compare, full cohort, demographic PS); on-treatment, landmark and run-in estimands in the primary set (claude-v19-sens-adherence, recomputed with v17 signflip_1s); outpatient distance and SE inflation (docs/v19/SENS_OUTPATIENT.md).
  - References 9, 11 and 18 were verified against Crossref (author lists and DOIs). The ref 12 DOI was verified against DataCite.
- **SENS_PRIMARY32 integration (2026-10-01).** Source: `docs/v20/SENS_PRIMARY32.md` (commits d262e91, 8b742ca). Backup: `…/paper/backup/paper_pre_sens32_2026-10-01.md`.
  - **Numbers changed (old → new):**
    - overall relative reduction CI 6.3–15.9 → 6.3–16.0;
    - leave-one-out max P .005 → .004, and balance FDR q = .007 added;
    - permuted ECG −0.6% → −0.7%;
    - LV structure CI 14.6–32.5 → 15.0–32.1;
    - diastolic/LA CI 8.1–26.2 → 8.0–26.4;
    - LV systolic function CI [pending] → −0.5 to 27.3, reworded as imprecise;
    - vital signs CI added (6.8–20.2), RV/pulmonary CI added (3.0–22.1);
    - valves CI −12.2 to 13.0 → −12.5 to 12.7; other labs CI added (−10.5 to 7.0);
    - five-diagnosis CI 4.9–13.2 → 4.8–13.3;
    - high-dimensional 8.1% (2.3–13.4) → 7.6% (1.9–12.8), using paired variable sets;
    - clinical −1.1% (−6.2 to 4.0) → −1.2% (−6.5 to 3.9);
    - 38-trial CI 8.0–16.7 → 7.8–16.6;
    - RCT distance: leave-one-out max P .016 added, FDR q .084 → .051 (borderline);
    - outpatient 23-trial result confirmed (+2.2 points, P = .083; 7.7%, 2.6–12.5) vs +4.9 points (P = .008) for all initiators;
    - switch-only confirmed for 28 primary-set trials (0.253 → 0.199; P = .002);
    - CLMBR-T distance 0.171 → 0.170 (balance 60.7% / 62.6%, P = .025, confirmed);
    - MIMIC excluding index-day ECGs CI 9.7–19.7 → 9.5–19.8; MIMIC hdPS CI −0.5 to 15.9 → −0.4 to 16.2; MIMIC clinical-lite CI −9.6 to 10.8 → −9.1 to 11.8.
  - **Added:**
    - matching and weighting sensitivity results (11.2%–14.4%; gradient-boosted PS 6.6%, 1.5–11.2);
    - the ECG-component sweep (6.8% at 4 PCs, plateau 11%–15% at 32–256);
    - RCT distance under alternative specifications (benchmark-permutation P = .26 to .85);
    - all of the above in eTable 12 (provisional number);
    - a Statistical analysis sentence on paired variable sets and the fixed-seed bootstrap.
  - **Figures:** Figure 2 now reads the SENS_PRIMARY32 CIs (`claude-v20-sens-primary32/ci.csv`). Figure 4A has a y-axis from −20 and a moved label. CAPTIONS.md is updated.
  - **Known discrepancy:** the lab deck's balance explorer still masks only variables missing under PS alone, so its high-dimensional PS shows 8.1%, not 7.6%. The deck builder was updated only to accept the new Table 1 tier labels.
- **Audit fixes (2026-10-01), from** `docs/paper/AUDIT_MANUSCRIPT_2026-10-01.md`**.** Backup: `…/paper/backup/paper_pre_audit_fix_2026-10-01.md`.
  - **PI decisions:**
    - Enrichment dropped (Introduction aim iv, Methods, eMethods 8).
    - Design-step diagnostics kept in eMethods 8 only, with their result.
    - Matching and weighting sensitivity analyses kept for the 32/38 trials; their results are pending (SENS_PRIMARY32). The 18-trial values are not cited.
    - Robustness results are reported with "[to be confirmed by SENS_PRIMARY32]".
  - Split-half replication removed from the manuscript per PI decision (2026-10-01); results remain in the audit record (half A P = .30 for |Δ|).
  - **P1 items:**
    - #54: sensitivity analyses marked pending for the 32/38 trials.
    - #96/97: robustness limited to comparator clustering, leave-one-out and FDR, marked to be confirmed; "re-derived in independent audits" replaced by the internal consistency audit.
    - #67/84/76: relative-reduction definition corrected (ratio of across-trial means; 4,000 resamples) in Statistical analysis and eMethods 6. The LV systolic-function CI is marked "[CI to be regenerated]".
    - #110: outpatient analysis stated as 29 of 38 trials, plus the 23-trial primary-set result (to be confirmed).
    - Post hoc disclosure in the main text: the 32-trial set (Trial selection), relative reduction (Statistical analysis), the 58-panel timing (Covariate balance), and the simulation orientation and ECG-only design (Simulation Methods and Results). eMethods 7 now gives a single orientation statement (#105/106).
    - Table 1 regenerated with the four adjudicated tiers and design points (`scripts/make_picot_table.py`; 3/12/17/6). Non-95% intervals, the PROTECT AF credible interval, the ROCKET-AF ITT estimate and omitted outcome components are footnoted (#19–24).
  - **P2 items:**
    - lab and vital look-back (#49);
    - 58-panel missingness indicators removed and the prognostic score disclosed (#57/58/61);
    - expanded panel 245–336 (#64);
    - noise placebo 96 columns (#34);
    - hdPS details (#41–43);
    - matching order and caliper SD (#52/53);
    - echo masking before 2016-07-31 (#28);
    - treatment-classifier AUC removed (#68);
    - statsmodels removed (S2);
    - references renumbered in first-citation order, Heyard (18) and Morris (19) added, refs 10 and 13 pages completed (R1–R3).
  - **P3 items:**
    - adherence (switch-only) and CLMBR-T results added and marked to be confirmed (#113/115);
    - echo-subset sentence plus eMethods 12 (X3);
    - AF confirmation failure stated, and 15-trial prespecified results added (eTable 11) (#11/114);
    - MIMIC wording: clinical-lite, four specifications including sparse, "decreased" limited to the mean absolute difference, "without substitution", pair range for the demographic PS (#117/118);
    - re-rater exposure and LLM assistance disclosed [PI to confirm wording] (#16);
    - F1 in the main-text list (#14);
    - "cardiovascular and metabolic" (#39);
    - candidate sourcing (#6);
    - ACS/MI naming (#5);
    - the 4 previously built trials noted for eFigure 1 (#2);
    - the P = .009 attribution (#93);
    - "first recorded encounter ≥365 days" (#29);
    - CLMBR-T input window (#35);
    - near-duplicate rule details and the screen-before-registration caveat (#8/10);
    - partial R² and the 38-trial median (#103);
    - the 14.2% design label (#104);
    - truncated weights, the landmark deviation and outpatient rematching (#112/113).
  - **Open items:**
    - All relative-reduction CIs are to be regenerated from the committed `scripts/v20/make_paper_figures.py` with fixed seeds. The hdPS CI shows the audit's common-variable estimate (2.3–13.4).
    - The expanded-panel P5/P2 overlap-exclusion naming bug (#63) must be fixed before any P5 expanded result is reported.
    - eTable numbering (3–11) is provisional.
    - ECG model architecture (eMethods 4) is still a placeholder.
    - eFigure 1 needs exclusion counts and the reason for the 4 previously built trials.
    - The CLMBR-T PC environment (mosaic-env, Python 3.11.15, scikit-learn 1.9.0) is to be stated if confirmed (S3).
    - Only 19 references against the 50–75 target; the 38 trial publications are uncited.
    - UK Biobank and polygenic scores remain excluded.
- **PI bracketed comments addressed (2026-10-01).** Backup: `…/paper/backup/paper_worktree_2026-10-01.md`.
  1. **Data sources, "mention MIMIC-IV":** added an external-validation sentence and refs 16–17 (both [verify]).
  2. **Methods, "external cohort validation":** new subsection "External validation" plus eMethods 11, from `docs/v20/MIMIC_REPLICATION.md` and `MIMIC_FEASIBILITY.md`.
  3. **Results, "figures folder":** the folder is `docs/paper/figures/main` and `/supplementary`, being created by the figure agent. The figure plan moved to Tables and Figures (Figures 1–4, eFigures 1–8), and the bracket was removed from Results.
  4. **Cohorts, "mention MIMIC-IV trials":** added the MIMIC-IV trial count and matched-pair range (eTable 4). The Yale [n] placeholders remain.
  5. **Balance, "is 11.4% across all 58?":** rephrased as "Across the 58 held-out characteristics … reduced the mean |SMD| … a relative reduction of 11.4%".
  6. **Results, "no bullet points; final-version prose":** all of Results is now prose (balance, agreement, quality, simulation, external validation, sensitivity). Secondary detail is referenced to eTables 5–11 and eFigures 2–8.
  7. **Balance, "reference the supplements":** the expanded panel and 38-trial results point to eTable 5 and eFigure 3, the domain detail to eFigure 2.
  8. **Agreement, "move clinical-PS info to supplement":** the clinical PS-alone agreement metrics and the 38-trial numbers moved to eTable 6. The clinical-PS comparison by quality tier is kept, as it carries the quality finding.
  9. **Simulation, "simplify and clarify":** shortened to the ECG-alone result, the added value over each PS, the R² relationship and coverage. Robustness moved to eFigure 8.
  10. **Sensitivity, "add MIMIC validation":** new "External validation" Results subsection with balance, agreement and the negative control. Sensitivity analyses are in prose; missing items carry "[results to be added]".
  - **eTable numbering is provisional (3–11).** Build the eTables to match.
  - **UK Biobank:** excluded from the manuscript entirely (PI decision, 2026-10-01).
- **Simulation results (2026-09-30):** from `docs/v20/G2_EXTENSION.md` (commit 625542c; aggregates in `audits/claude-v20-g2-ext/`).
  - The ECG-only numbers use the clean design (treatment driven by C only) in the clinical orientation. The added-share numbers are null-corrected.
  - The sparse-PS arms (added share 9.7% overall, 16.2% for LVEF) were run but are omitted from the manuscript, consistent with the simplified PS ladder.
  - The as-designed v1.9 numbers (14.2% with the demographic PS; LVEF 9.1%, eGFR −4.8%) go to the supplement. Orientation is a logged post hoc choice. NT-proBNP and BMI are orientation-independent.
- **Methods v5 and Results draft (2026-09-30), from the PI's bracketed comments:**
  - **Selection:** two-stage selection (feasibility, then quality); the primary set is now 32 trials, with 38 as a sensitivity set. The main text states that the grading was finalized after the primary analyses.
  - **Representations:** a BCL description has been added. CLMBR-T is framed as a sensitivity analysis and kept in italics.
  - **PS section:** the obesity (P2) and sparse PS were removed from the manuscript for simplicity. Their results remain in the record (deck, audits) and can be restored; the sparse diagnosis set survives only as the hdPS base. PS text is condensed, and the permuted ECG, CLMBR-T and both are listed as sensitivity augmentations.
  - **Outcomes:** split into "Covariate balance" and "Trial emulation analysis".
  - **Backups:** pre-edit backups are at `…/paper/backup/paper_worktree_2026-09-30*.md`.
  - **Results numbers:** from the deck data, the same sources as the audits. Relative-reduction CIs are a bootstrap over trials (4,000 resamples).
- **Methods v4 (2026-09-30): updated to the analyses conducted through v1.9.**
  - Main-text Methods are back in prose (no bullets), keeping the PI's wording edits to the Introduction and Data sources. The previous working version is backed up at `/mnt/raid0/rbc58/ecg-tte/audits/claude-acc2027-abstract/paper/backup/paper_worktree_2026-09-30.md`.
  - New or changed:
    - four-tier emulation-quality scale;
    - full PS ladder, including the obesity variant, the hdPS algorithm (ref 13, replacing the incorrect ref 6 citation) and the clinical PS count;
    - rationale for the primary 58 panel and the construction of the expanded panel;
    - missing-data handling (held-out: observed values plus missingness indicators; clinical PS: single chained-equation imputation);
    - relative reduction in mean |SMD| with bootstrap CI;
    - RCT-DUPLICATE agreement metrics;
    - the plasmode in detail (eMethods 7);
    - a new eMethods 9 on sensitivity estimands and the outpatient restriction; software is now eMethods 10.
  - The expanded panel is now "about 300–345 per trial", not "about 400".
  - **Inconsistency to resolve:** Table 1 and its footnote still show the v1.7 three-class rating (high strict / high / lower). The Methods now describe the four-tier scale (3 excellent / 12 good / 17 moderate / 6 limited). Regenerate Table 1 (`scripts/make_picot_table.py`) with the tiers, or keep both.
  - **To verify:** refs 14–15 and the Heyard BMJ Med 2024 citation in eMethods 3. The sensitivity analyses listed from earlier versions (caliper 0.1, 1:3 matching, IPTW/overlap weighting, gradient-boosted PS, 4–256 PCs) must be confirmed as reported in Results/eTables.
  - The balance effect-size script (relative reduction with bootstrap CI) should move from the session scratchpad into `scripts/v19/` before Results cite it.
  - Introduction paragraph 2: "richer clinical information" replaced per the PI's bracketed request (actionable, site-specific EHR data).
- **Candidate count (2026-09-28): 99 individual RCTs.**
  - These are the unique trials across `trial_specs.py`, `docs/v17/candidates.json` and `docs/v18/af_candidates.json`.
  - Design variants of the same RCT are collapsed.
  - Grouped not-screened entries are expanded: PALLAS/ELDERCARE-AF/NOAH; RAAFT-2/MANTRA-PAF/EARLY-AF/STOP AF First/Cryo-FIRST/AATAC; ENTRUST-AF PCI/ENVISAGE-TAVI AF; ELAN/TIMING/OPTIMAS; INVICTUS/RIVER; AVERROES/BAFTA; EMPEROR-Reduced/DELIVER; BRUISE CONTROL.
  - The eFigure 1 flow must list these with reasons.
  - The time-zero, follow-up and estimand sentences moved to eMethods 2.
- **Trial selection v3 (2026-09-28):**
  - Selection and specification are merged into one subsection.
  - The main text now simply says 38 trials met the criteria; the staged and prespecified assembly is described only in eMethods 3.
  - **Caution for Results and Discussion:** when citing results from the prespecified subsets (e.g., the 15-trial and 5-trial AF confirmation analyses), reference eMethods 3 so that their status is clear.
- **Trial selection v2 (2026-09-28):**
  - The three sets are aggregated into one bucket of 38 trials in the main text.
  - The selection criteria and screening count (~90 candidates) are described.
  - One sentence on the 20 prespecified trials is kept for transparency; the staged detail is in eMethods 3.
  - **The PI mentioned 36 trials; the analysed total is 38 (18 + 15 + 5). Confirm.**
  - An eFigure 1 flow diagram is still to be built.
  - The rater paragraph is shortened.
- **PICOT v2 (2026-09-28):**
  - The RCT-DUPLICATE framing of PICOT is removed; the TARGET statement (ref 12) is cited as the standardization reference.
  - The per-element PICOT detail is moved to eMethods 2.
  - The emulation-quality rating is added to the main text and as a Table 1 column: 9 high (strict), 9 high, 20 lower.
- **PICOT in the main text (earlier):**
  - PICOT is now part of the main Methods, with a 38-row Table 1 generated by `scripts/make_picot_table.py`.
  - For JAMA's 5-display-item limit, a condensed Table 1 may later be needed, with the full table moved to eTable 1.
  - The population descriptions in the script are concise summaries of the spec gates; verify them against trial_specs before submission.
- **PICOT (earlier):**
  - Added to the main Methods and eMethods 2.
  - eTable 1 must be built from `scripts/trial_specs.py` and PROTOCOL_V1 §4b in PICOT plus TARGET format.
  - The TARGET checklist goes in the supplement.
- **Methods v3 (2026-09-28):**
  - The main text is shortened; detail has moved to eMethods 1–9.
  - The text now states that the OMOP mapping was generated in-house.
- **Methods v2 notes, retained for reference:** (headings such as "Data sources" and "Study exposure"; the standard IRB and software sentences):
  - The IRB number is left blank for the PI.
  - BCL is described as an in-house signal model adapted from the image-based BCL (ref 10). Details go in the Supplementary Methods.
  - The embedding dimension is verified as 256, with 32 PCs.
  - CLMBR-T-base is cited as Wornow 2023 (EHRSHOT).
  - Software versions are taken from the analysis environments.
- **Supplementary tables referenced:**
  - S1: 38 trial specifications with RCT HRs and the blinded rating;
  - S2: the 58 held-out variables and the expanded panel.
- **Introduction v3 (2026-09-28):**
  - It follows the PI outline: randomization, then RCT limits, then the unmet need, then TTE with a PS on structured data (strengths and limits), then EHR missingness vs claims, then CV physiology and AI-ECG, then "Here, we".
  - References 1–10 are checked against PubMed/publisher pages. Still to confirm: the ref 9 full author list and the ref 10 page range.
- **Optional closing sentence for the Introduction**, consistent with the v1.6–v1.9 results and the round-4 audit: "We find that AI-ECG embeddings improve balance on unmeasured physiology and remove confounding bias in proportion to how well they encode the confounder, but do not by themselves reproduce trial-specific RCT results."
- **Possible additional citation:** DISCO (Biswas D, Dhingra LS, Aminorroaya A, Croon PM, Oikonomou EK, Khera R. *Eur Heart J* 2025;46(Suppl 1):ehaf784.4614), the closest precedent. Cite it in the Introduction or the Discussion.

