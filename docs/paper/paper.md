# AI-enhanced electrocardiography as a phenotypic probe of confounding in target trial emulation: an evaluation across 38 cardiovascular trials

**Subtitle (JAMA requirement):** *A Comparative Effectiveness Study Using Target Trial Emulation* [confirm the study-type label with the editorial office]

**Target journal:** JAMA Cardiology, Original Investigation.
- **Limits:**
  - main text ≤3,000 words;
  - structured abstract ≤350 words;
  - ≤5 tables and figures combined;
  - 50–75 references;
  - Key Points (Question / Findings / Meaning, ≤100 words);
  - a data sharing statement;
  - EQUATOR reporting (STROBE; the TARGET guideline for target trial emulation).
- **Supplement:** eMethods, eTables and eFigures.

*Working draft; last updated 2026-09-30. Draft notes are marked and must be removed before submission.*

## Key Points

**Question:** *(to write)*

**Findings:** *(to write)*

**Meaning:** *(to write)*

## Abstract

*(to be written last; JAMA structure: Importance; Objective; Design, Setting, and Participants; Exposures; Main Outcomes and Measures; Results; Conclusions and Relevance; ≤350 words)*

## Introduction

Randomization is the gold standard for causal inference in medicine. Treatment is assigned by chance, so measured and unmeasured characteristics are, on average, balanced between arms. Differences in outcomes can then be attributed to the treatment itself.^1^ Randomized controlled trials (RCTs) are, however, expensive and time-consuming. They are also often infeasible or unrepresentative for important populations, such as older, multimorbid or underrepresented patients who receive these therapies in practice.^2^

Inferring causal effects from the data already generated in routine care therefore remains an unmet need. Target trial emulation (TTE) is a leading candidate approach.^3^ The protocol of a hypothetical randomized trial is specified explicitly and then emulated in observational, real world data. Confounding is typically addressed with propensity scores (PS) estimated from structured variables. This strategy balances measured characteristics well, and benchmarking against completed RCTs has shown that well-designed emulations can reproduce trial results.^4,5^ However, its guarantee extends only to what is measured. Most emulations rely on claims data, which record diagnoses, procedures and prescriptions consistently. Electronic health records (EHRs) contain richer clinical information[can we change richer clinical infromation to something where EHR information is more actionable and availablility for site specific ], but laboratory values, vital signs and imaging are missing for many patients, and not at random. These measurements therefore cannot be relied on for adjustment.^6^

This gap is particularly consequential in cardiovascular medicine. Many determinants of both treatment choice and prognosis are physiological: ventricular function, chamber size, atrial substrate, congestion and conduction. These are the characteristics most likely to confound comparisons and least likely to be captured in structured data. The 12-lead electrocardiogram (ECG) offers a potential solution. It is inexpensive and acquired routinely across the health system. Artificial intelligence applied to the ECG (AI-ECG) detects left ventricular dysfunction, structural heart disease and other latent phenotypes.^7–9^ Foundation-model embeddings compress this information into general-purpose representations of cardiac physiology.^10^ Because the ECG measures current physiology and is available for most patients, AI-ECG may capture confounding that structured data miss.

Here, we evaluated whether AI-ECG embeddings capture confounding missed by structured data in 38 emulations of cardiovascular RCTs. We assessed (i) balance on held-out clinical, laboratory and echocardiographic characteristics, (ii) agreement with RCT results, (iii) bias removal in simulations with a known treatment effect, and (iv) utility for trial enrichment.

## Methods

### Data sources
We used electronic health record (EHR) data from the Yale New Haven Health System (YNHHS), a large academic health system in Connecticut. We mapped the structured EHR data to the Observational Medical Outcomes Partnership (OMOP) common data model. We linked these data to structured echocardiography reports, raw 12-lead ECG signals and state vital statistics records (eMethods 1). We included patients with index dates from 2011 through 2024. The Yale Institutional Review Board approved the study (protocol number [ ]) and waived informed consent for this secondary analysis of existing data.

### Trial selection and target trial specification
We identified candidate cardiovascular randomized controlled trials (RCTs) from landmark trials and from prior trial emulation initiatives.^4,5^ Trials were eligible if they had an active comparator, or a comparator that could be emulated with an accepted active proxy; a primary endpoint ascertainable from EHR data; and treatment strategies identifiable from medication orders or procedure codes. YNHHS also had to provide at least 300 patients with an ECG in the smaller treatment group and at least 50 primary-outcome events, and cohorts that largely duplicated an existing emulation were excluded. Of 99 candidate trials, 38 met these criteria and were emulated (eFigure 1). They covered atrial fibrillation (AF; 12 trials), diabetes (9), heart failure (5), hypertension (5), acute coronary syndromes (2) and other indications (5).

For each trial, we specified the target trial protocol and its emulation following the TARGET guideline, summarized using the population, intervention, comparator, outcome and time (PICOT) elements (Table 1; eMethods 2; eTable 1).^12^ The specification and the published primary hazard ratio (HR) were recorded before outcomes were extracted. Each emulation used a new-user, active-comparator design and estimated the effect of treatment initiation, analogous to the intention-to-treat effect (eMethods 2).

We graded how closely each emulation reproduced its trial using design information only. Five design deviations described by the RCT-DUPLICATE initiative (in-hospital initiation not mirrored, selective run-in, discontinuation of baseline therapy at randomization, delayed effect with long follow-up, and other time-zero misalignment) each scored 1 point, and comparator and outcome fidelity each scored 0 (good), 1 (moderate) or 2 (poor).^5^ Trials were classified as excellent (0 points), good (1–2), moderate (3) or limited (≥4) emulations (eMethods 3).

### AI-ECG and EHR representations
We used the most recent 12-lead ECG within 365 days before or on the index date. ECGs were encoded with an AI-ECG signal model adapted from an image-based biometric contrastive learning (BCL) model.^10^ This self-supervised model produced a 256-dimensional embedding per ECG, which was reduced to 32 principal components within each trial (eMethods 4). To test whether any gains reflected ECG information rather than added dimensions, we used a permuted-ECG placebo, in which embeddings were shuffled between patients.

For comparison, we used CLMBR-T-base, a structured-EHR foundation model.^11^ We applied it to each patient's coded history before the index date and reduced its output to 64 principal components.

### Propensity scores and matching
Within each trial, we estimated the propensity score (PS), the probability of receiving the intervention rather than the comparator, using L2-penalized (ridge) logistic regression on standardized covariates. The primary PS included only age, sex and calendar year of index, and represents settings in which few structured covariates are reliably captured. To examine how the value of ECG information depends on the richness of structured data, we fitted progressively richer specifications. These added five cardiometabolic diagnoses (hypertension, type 2 diabetes, coronary artery disease, AF and heart failure), with or without obesity; a sparse set of 9 to 13 cardiovascular diagnoses recorded in the prior year; a high-dimensional PS, which added to the sparse PS the 200 recurrence-weighted code features most imbalanced between treatment groups;^13^ and a clinical PS (median 32 covariates per trial) that additionally included vital signs, laboratory values, left ventricular ejection fraction (LVEF), medication orders and healthcare use (eMethods 5).

For every specification, we compared the PS alone with the same PS augmented with the 32 ECG principal components, the CLMBR-T components, both, or the permuted-ECG placebo, holding all other modelling choices constant. Patients were matched 1:1 without replacement by greedy nearest-neighbour matching on the logit of the PS, with a caliper of 0.2 standard deviations of the logit, starting from the smaller treatment group. Unmatched patients were excluded.

### Outcomes
The primary balance outcome was covariate balance, after matching, on characteristics that were not included in the PS under evaluation. Balance was summarized as the absolute standardized mean difference (SMD), with |SMD| <0.1 regarded as balanced.^14^ The primary panel comprised 58 characteristics fixed before analysis: 35 echocardiographic measures, vital signs, laboratory values including N-terminal pro–B-type natriuretic peptide (NT-proBNP), and summaries of medications, healthcare use and the coded record (eTable 2). We chose these because they are directly measured cardiac physiology, the confounders most relevant to cardiovascular comparisons and most plausibly reflected in the ECG. In a sensitivity analysis, we assembled an expanded panel of about 330 additional pre-index characteristics per trial from a review of covariates used in published PS and trial emulation studies. It covered comorbidities, medication classes, healthcare use, additional laboratory values, devices and procedures, risk and frailty scores, and preventive care. Characteristics in or derived from the PS under evaluation, characteristics that revealed treatment, and characteristics that an ECG encodes directly, such as arrhythmias, conduction disease and cardiac devices, were excluded (eMethods 6).

Emulated HRs were estimated with Cox proportional hazards models with robust variance clustered on matched pairs. Following the RCT-DUPLICATE initiative, agreement with each RCT was assessed as the Pearson correlation of emulated and RCT log HRs across trials; estimate agreement, defined as an emulated HR within the RCT 95% CI; and standardized difference agreement, defined as a difference between emulated and RCT log HRs within 1.96 times its combined standard error.^4,5^ We also used the absolute difference between emulated and RCT log HRs, and assessed whether reductions in that difference were specific to each trial or reflected generic attenuation of extreme estimates, by comparing them with reductions obtained after reassigning RCT results at random across trials (eMethods 6).

### Simulation
The true effect is unknown in real data. We therefore used plasmode simulations,^15^ which retain each trial's real covariates, ECGs and follow-up while simulating treatment and outcome with a known HR of 0.80. A measured physiological variable, LVEF, NT-proBNP, body mass index or estimated glomerular filtration rate, was made to drive both treatment and outcome and was withheld from every PS, so that it acted as an unmeasured confounder. We quantified the proportion of the resulting bias removed when the ECG embedding was added to the demographic PS, relative to adding the confounder itself, and related it to how well the ECG predicted the confounder in the real data (eMethods 7). We also examined residual ECG-phenotype imbalance across successive design steps and the prognostic value of an AI-ECG risk score for trial enrichment (eMethods 8).

### Statistical analysis
Trials were the unit of analysis. For each trial, we computed the proportion of held-out characteristics with |SMD| <0.1 and the mean |SMD|, and summarized each PS specification across trials. The effect of adding the ECG was expressed as the change in the proportion of balanced characteristics and as the relative reduction in mean |SMD|, with 95% CIs from bootstrap resampling of trials. Paired differences between specifications were tested with exact one-sided sign-flip permutation tests across trials. We assessed robustness to clustering of trials that shared a comparator, with leave-one-trial-out analyses and in split-sample halves, and controlled the false discovery rate within analysis families. Agreement with RCTs was described by emulation quality. Sensitivity analyses varied the caliper, matching ratio and weighting approach, the number of ECG components, the variable panel, and the estimand (per-protocol and switch-only estimands with inverse-probability-of-censoring weights, 90-day landmark and run-in analyses), and restricted cohorts to patients initiating treatment as outpatients (eMethods 5, 6 and 9). This study was exploratory, and all analyses are reported. Headline estimates were re-derived in independent audits. Analyses were performed in Python 3.11 (eMethods 10).

## Results

*(pending)*

## Tables and Figures

**Table 1. Target trial specification (PICOT) and emulation quality for the 38 emulated trials**

| Area | Trial | Population | Intervention | Comparator | Outcome (RCT primary endpoint) | Time (mo) | RCT HR (95% CI) | Emulation quality |
|---|---|---|---|---|---|---|---|---|
| AF | ARISTOTLE | AF | apixaban | warfarin | stroke or systemic embolism | 22 | 0.79 (0.66–0.95) | High (strict) |
| AF | ROCKET-AF | AF | rivaroxaban | warfarin | stroke or systemic embolism | 23 | 0.88 (0.74–1.03) | High (strict) |
| AF | RE-LY | AF | dabigatran | warfarin | stroke or systemic embolism | 24 | 0.66 (0.53–0.82) [RR] | High (strict) |
| AF | EAST-AFNET 4 | Early AF (diagnosis ≤1 y) on rate control | rhythm-control drug added | continued rate control | CV death, stroke, HF or ACS hospitalisation | 61 | 0.79 (0.66–0.94) | High |
| AF | CABANA | AF | catheter ablation | antiarrhythmic drug | death, disabling stroke, serious bleeding or cardiac arrest | 49 | 0.86 (0.65–1.15) | High |
| AF | AFFIRM | AF on rate control, age ≥65 | rhythm-control drug added | continued rate control | all-cause death | 42 | 1.15 (0.99–1.34) | High (strict) |
| AF | AF-CHF | AF with HF on rate control | rhythm-control drug added | continued rate control | CV death | 37 | 1.06 (0.86–1.30) | High (strict) |
| AF | FRAIL-AF | AF on warfarin, age ≥75 | switch to DOAC | warfarin | major or clinically relevant non-major bleeding | 12 | 1.69 (1.23–2.32) [cause-specific HR] | Lower |
| AF | LAAOS III | AF undergoing cardiac surgery | surgical LAA occlusion | surgery without LAA occlusion | ischaemic stroke or systemic embolism | 46 | 0.67 (0.53–0.85) | High (strict) |
| AF | PROTECT AF | AF on warfarin with ≥1 stroke risk factor | percutaneous LAA closure | warfarin | stroke, CV death or systemic embolism | 18 | 0.62 (0.35–1.25) [rate ratio] | High (strict) |
| AF | RAFT-AF | AF with HF on rate control | catheter ablation | continued rate control | all-cause death or HF event | 36 | 0.71 (0.49–1.03) | High (strict) |
| AF | ACTIVE W | AF with ≥1 stroke risk factor, age ≥55 | clopidogrel | warfarin | stroke, non-CNS systemic embolism, MI or vascular death | 15 | 1.44 (1.18–1.76) [RR] | High |
| HF | COMET | HF | carvedilol | metoprolol | all-cause mortality | 58 | 0.83 (0.74–0.93) | Lower |
| HF | PARADIGM-HF | HF on ACEi/ARB (switch at time zero) | sacubitril-valsartan | ACEi | CV death or first HF hospitalisation | 27 | 0.80 (0.73–0.87) | High |
| HF | TRANSFORM-HF | HF hospitalisation (discharge within 30 d) | torsemide | furosemide | all-cause mortality | 12 | 1.02 (0.89–1.18) | Lower |
| HF | ELITE II | HF, age ≥60 | ARB | ACEi | all-cause mortality | 18 | 1.13 (0.95–1.35) | High (strict) |
| HF | EMPEROR-Preserved | HF with T2D | SGLT2i | DPP-4i (placebo proxy) | CV death or HF hospitalisation | 26 | 0.79 (0.69–0.90) | Lower |
| Hypertension | LIFE | Hypertension with ECG-LVH, age 55–80 | ARB | β-blocker | CV death, MI or stroke | 58 | 0.87 (0.77–0.98) | Lower |
| Hypertension | ALLHAT | Hypertension, age ≥55 | amlodipine | thiazide | fatal CHD or nonfatal MI | 59 | 0.98 (0.90–1.07) [RR] | Lower |
| Hypertension | VALUE | Hypertension, age ≥50 | ARB | amlodipine | cardiac morbidity and mortality composite | 50 | 1.04 (0.94–1.15) | Lower |
| Hypertension | ASCOT-BPLA | Hypertension, age 40–79 | amlodipine | β-blocker | nonfatal MI and fatal CHD | 66 | 0.90 (0.79–1.02) | Lower |
| Hypertension | INSIGHT | High-risk hypertension, age ≥55 | nifedipine | thiazide | CV death, MI, HF or stroke | 42 | 1.10 (0.91–1.34) [RR] | High |
| ACS / MI | PLATO | ACS within 30 d | ticagrelor | clopidogrel | vascular death, MI or stroke | 12 | 0.84 (0.77–0.92) | High |
| ACS / MI | VALIANT | MI within 30 d | ARB | ACEi | all-cause death | 25 | 1.00 (0.90–1.11) | High |
| Diabetes | EMPA-REG OUTCOME | T2D with established CVD | SGLT2i | DPP-4i (placebo proxy) | 3-point MACE | 37 | 0.86 (0.74–0.99) | Lower |
| Diabetes | CAROLINA | T2D | linagliptin | glimepiride | 3-point MACE | 76 | 0.98 (0.84–1.14) | High |
| Diabetes | LEADER | T2D with CVD, age ≥50 | liraglutide | DPP-4i (placebo proxy) | CV death, nonfatal MI or nonfatal stroke | 46 | 0.87 (0.78–0.97) | Lower |
| Diabetes | SUSTAIN-6 | T2D with CVD, age ≥50 | semaglutide | DPP-4i (placebo proxy) | CV death, nonfatal MI or nonfatal stroke | 25 | 0.74 (0.58–0.95) | Lower |
| Diabetes | REWIND | T2D, age ≥50 | dulaglutide | DPP-4i (placebo proxy) | nonfatal MI, nonfatal stroke or CV death (incl. unknown causes) | 65 | 0.88 (0.79–0.99) | Lower |
| Diabetes | DECLARE-TIMI 58 | T2D, age ≥40 | dapagliflozin | DPP-4i (placebo proxy) | CV death or HF hospitalisation | 50 | 0.83 (0.73–0.95) | Lower |
| Diabetes | CANVAS Program | T2D, age ≥30 | canagliflozin | DPP-4i (placebo proxy) | CV death, nonfatal MI or nonfatal stroke | 43 | 0.86 (0.75–0.97) | Lower |
| Diabetes | TECOS | T2D with CVD, age ≥50 | sitagliptin | sulfonylurea (placebo proxy) | CV death, nonfatal MI, nonfatal stroke or UA hospitalisation | 36 | 0.98 (0.88–1.09) | Lower |
| Diabetes | CARMELINA | T2D with kidney disease | linagliptin | sulfonylurea (placebo proxy) | CV death, nonfatal MI or nonfatal stroke | 26 | 1.02 (0.89–1.17) | Lower |
| Other | ONTARGET | Established vascular disease or high-risk diabetes, age ≥55 | ARB | ACEi | CV death, MI, stroke or HF hospitalisation | 56 | 1.01 (0.94–1.09) [RR] | Lower |
| Other | PRECISION | Arthritis with CV risk | celecoxib | naproxen | CV death (incl. haemorrhagic), nonfatal MI or nonfatal stroke (APTC) | 34 | 0.93 (0.76–1.13) | High |
| Other | AMPLIFY | Acute VTE | apixaban | warfarin | recurrent symptomatic VTE or VTE-related death | 6 | 0.84 (0.60–1.18) [RR] | Lower |
| Other | LODESTAR | Coronary artery disease | rosuvastatin | atorvastatin | 3-y death, MI, stroke or any coronary revascularisation | 36 | 1.06 (0.86–1.30) | Lower |
| Other | PROVE IT-TIMI 22 | ACS within 30 d | atorvastatin | pravastatin | death, MI, UA rehospitalisation, revascularisation >= 30 d or stroke | 24 | 0.84 (0.74–0.95) | Lower |

*Abbreviations:*
- ACEi, angiotensin-converting enzyme inhibitor; ARB, angiotensin receptor blocker;
- ACS, acute coronary syndrome; AF, atrial fibrillation; CAD, coronary artery disease; CHD, coronary heart disease; CV, cardiovascular; CVD, cardiovascular disease; HF, heart failure; MI, myocardial infarction; MACE, major adverse cardiovascular events; UA, unstable angina; VTE, venous thromboembolism;
- DOAC, direct oral anticoagulant; DPP-4i, dipeptidyl peptidase-4 inhibitor; SGLT2i, sodium-glucose cotransporter-2 inhibitor; LAA, left atrial appendage;
- LVH, left ventricular hypertrophy; T2D, type 2 diabetes.

*Notes:*
- RCT estimates are hazard ratios unless indicated.
- Time is the trial-matched follow-up horizon.
- "Placebo proxy" marks placebo-controlled trials emulated with an active comparator.
- Emulation quality is from a blinded rating made before results were examined. High (strict) means no design flag; high means one flag with at least moderate comparator and outcome fidelity; lower means all others.
- Full eligibility criteria, code lists and adaptations are given in eTable 1.

**Figure 1.** Balance on held-out characteristics by domain (docs/abstract/ACC_2027/fig_A_loveplot) *(placeholder; final figure plan pending)*

**Figure 2.** Distance from the RCT result by trial type (fig_B_hr_gap) *(placeholder)*

**Figure 3.** Simulation: bias removed vs ECG R² (fig_C_simulation) *(placeholder)*

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
9. Dhingra LS, et al. Heart failure risk stratification using artificial intelligence applied to electrocardiogram images: a multinational study. *Eur Heart J.* 2025;46:1044–1053.
10. Sangha V, Khunte A, Holste G, Mortazavi BJ, Wang Z, Oikonomou EK, Khera R. Biometric contrastive learning for data-efficient deep learning from electrocardiographic images. *J Am Med Inform Assoc.* 2024;31(4):855.
11. Wornow M, Thapa R, Steinberg E, Fries JA, Shah NH. EHRSHOT: an EHR benchmark for few-shot evaluation of foundation models. *Adv Neural Inf Process Syst.* 2023;36.
12. Cashin AG, Hansford HJ, Hernán MA, et al. Transparent reporting of observational studies emulating a target trial: the TARGET statement. *JAMA.* 2025. doi:10.1001/jama.2025.13350 [verify author list and pages]
13. Schneeweiss S, Rassen JA, Glynn RJ, Avorn J, Mogun H, Brookhart MA. High-dimensional propensity score adjustment in studies of treatment effects using health care claims data. *Epidemiology.* 2009;20:512–522.
14. Austin PC. Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples. *Stat Med.* 2009;28:3083–3107.
15. Franklin JM, Schneeweiss S, Polinski JM, Rassen JA. Plasmode simulation for the evaluation of pharmacoepidemiologic methods in complex healthcare databases. *Comput Stat Data Anal.* 2014;72:219–226. [verify]

## Supplementary Methods (eMethods)

### eMethods 1. Data sources
YNHHS comprises multiple hospitals and an extensive outpatient network across Connecticut and Rhode Island. Our team mapped the structured Epic data to the OMOP common data model, covering diagnoses (ICD-10-CM), medication orders, procedures, laboratory measurements, vital signs and encounters; source Epic tables supplemented the mapped data for race, ethnicity and hospital encounters. Echocardiographic measurements were taken from structured echocardiography reports; free text was not used. Deaths were identified from the EHR and from linked Connecticut vital statistics records, which also provided the listed causes of death. ECGs were retrieved from the institutional archive as raw 10-second, 500 Hz 12-lead signals. Follow-up extended through December 2024 for all-cause death and June 2024 for cause-specific death.

### eMethods 2. Emulation design (PICOT)
The population comprised patients meeting the trial's key eligibility criteria as operationalized from structured data. All were aged 18 years or older (or the trial minimum) and had at least 365 days of prior EHR activity, and exclusion criteria that could be ascertained were applied. New users of the intervention were compared with new users of the comparator. Time zero was the first order of the study drug or procedure, with no order for the comparator in the preceding 365 days. Where the trial tested adding or switching therapy against continuing existing treatment, for example rhythm control added to rate control or switching from warfarin, a sequential design was used. For placebo-controlled trials, an active comparator without an expected effect on the outcome served as a placebo proxy, for example dipeptidyl peptidase-4 inhibitors in trials of glucose-lowering drugs. The outcome was the trial's primary endpoint, mapped to EHR events; hospitalization components required a qualifying ICD-10 code during an inpatient stay, and cardiovascular death was defined from listed causes of death. Follow-up began the day after time zero and continued to the primary endpoint, death, end of data or a trial-matched horizon, whichever came first. eTable 1 lists, for each trial, the PICOT elements and the TARGET protocol components (eligibility, treatment strategies, assignment, time zero, follow-up, outcome, causal contrast and analysis), each with its emulated counterpart and any adaptation.

### eMethods 3. Trial selection and emulation quality
Trials were assembled in three stages: 18 trials in which the analytic approach was developed; 15 trials, drawn largely from RCT-DUPLICATE, analysed under a prespecified plan; and 5 AF trials analysed under a separate prespecified plan. For the second and third stages, trial specifications, benchmarks and the analysis plan were committed before any results were computed, and results for these prespecified sets are reported separately in the supplement. Of 99 candidate RCTs, 38 were emulated (eFigure 1). Reasons for exclusion were a placebo-only design without an accepted proxy, an endpoint not ascertainable from EHR data, an exposure that could not be identified, insufficient size, or a near-duplicate cohort. Size was assessed from pooled counts only, as at least 300 patients with an ECG in the smaller arm and at least 50 pooled primary events. Cohorts sharing more than 80% of patient–index date records with an existing cohort were considered near-duplicates.

Emulation quality was rated from design information only, without reference to emulation results. Five design deviations were scored, following the RCT-DUPLICATE classification of emulation differences:^5^ in-hospital initiation not mirrored in the emulation (F1), a selective run-in period (F2), discontinuation or replacement of an ongoing same-purpose therapy at randomization that the emulation did not reproduce (F3), a horizon of 48 months or longer with a delayed treatment effect (F4), and other misalignment of time zero (F5). Comparator and outcome fidelity were each graded good, moderate or poor. A poor comparator denoted a placebo proxy or a substitution that changed the trial hypothesis, and a poor outcome a primary endpoint that could not be validly ascertained. Each flag scored 1 point, and comparator and outcome fidelity scored 0, 1 or 2 points for good, moderate or poor, giving a total of 0 to 9. Trials were classified as excellent (0 points), good (1–2 points, with no poor item and at most one flag), moderate (3 points, or 1–2 points with a poor item or two flags) or limited (≥4 points). The points were additive because design differences contribute approximately additively to disagreement between RCTs and their emulations (Heyard et al., BMJ Med 2024 [verify]), and poor proxies were weighted double because they agreed worst in RCT-DUPLICATE.^4^ The ratings were first made as a three-class classification and then independently re-rated by a second reviewer, blind to the first ratings and to all results. Agreement on the three-class result was 82% (Cohen κ, 0.71) and disagreements were adjudicated against the written rules. The graded scale was defined after the primary analyses had been run but from design items only, and analyses by emulation quality are therefore post hoc. Of the 38 trials, 3 were rated excellent, 12 good, 17 moderate and 6 limited. The relevance of ECG-reflected physiology to each trial was graded high, medium or low according to whether treatment choice and prognosis plausibly depend on it.

### eMethods 4. ECG and EHR representations
The ECG model is a transformer encoder applied to 12-lead signals and trained in-house with the BCL objective of the published image-based model.^10^ [Add architecture and training-data details.] The frozen encoder produced 256-dimensional embeddings, from which the first 32 principal components were computed within each trial. Two placebos were used: a permuted-ECG placebo, in which embeddings were reassigned at random between patients within each cohort, and a noise placebo of independent Gaussian variables of the same dimension. CLMBR-T-base is a 141-million-parameter model pretrained on the structured EHR data of 2.57 million patients at Stanford.^11^ It was applied frozen to pre-index coded history, and its 768-dimensional representations were reduced to 64 principal components.

### eMethods 5. Propensity score specifications and matching
Six PS specifications were fitted. The demographic PS included age, sex and calendar year of index. The five-diagnosis PS added hypertension, type 2 diabetes, coronary artery disease, AF and heart failure, and a variant also added obesity. The sparse PS included demographics and 9 to 13 investigator-selected cardiovascular diagnoses recorded in the prior 365 days. The high-dimensional PS followed the approach of Schneeweiss et al.^13^ Pre-index diagnosis, medication, procedure and laboratory-order codes were converted into indicators of any, sporadic (at least the median count among patients with the code) and frequent (at least the 75th percentile) recurrence. These were ranked by the absolute log ratio of their prevalence in the two treatment groups, and the top 200 were added to the sparse PS. Unlike the original algorithm, codes were ranked on their association with treatment only, not with the outcome, so that selection never used outcome data; candidates were drawn from a random half of the code features, the other half being reserved for balance assessment, and the trial's exposure drugs were excluded. The clinical PS comprised a median of 32 covariates per trial (range, 28–37). The 24 covariates common to all trials were age, sex, index year; AF, hypertension, diabetes, ischemic heart disease or myocardial infarction, chronic kidney disease, chronic obstructive pulmonary disease or asthma, peripheral artery disease, stroke and valve disease; LVEF, systolic and diastolic blood pressure, heart rate, body mass index, creatinine, potassium, sodium and hemoglobin; and outpatient, emergency department and inpatient encounter counts. Trial-specific covariates comprised 3 to 10 medication orders relevant to the clinical area and additional diagnoses such as heart failure, transient ischemic attack, liver disease and prior bleeding. Diagnoses were ascertained in the prior 365 days, medication orders in the prior 90 days and the latest plausible laboratory and vital sign values in the prior 365 days. Missing values in the clinical PS were completed with a single imputation by chained equations (posterior sampling, with all covariates and treatment as predictors and no outcome information).

All PS were estimated by L2-penalized logistic regression on standardized covariates with an inverse regularization strength of 1 (scikit-learn), which stabilizes estimates when covariates are numerous, correlated or sparse. The same specification was used for every covariate set, so that only the covariates differed between comparisons. Matching was greedy 1:1 nearest-neighbour matching without replacement on the PS logit. Patients in the smaller treatment group were processed in descending order of the PS and matched to the nearest available patient within a caliper of 0.2 standard deviations of the logit. In sensitivity analyses, we used a caliper of 0.1, 1:3 matching, inverse probability and overlap weighting, a gradient-boosted PS with 5-fold cross-fitting, and 4 to 256 ECG principal components.

### eMethods 6. Balance and agreement metrics
For each characteristic, the SMD was the difference in means between treatment groups in the matched sample divided by the pooled standard deviation of the unmatched analysed cohort, so that the denominator did not change between PS specifications. Held-out characteristics were not imputed. Diagnoses, procedures and medications were coded as present or absent in the look-back window, laboratory and vital sign values were compared among patients with an observed value, and each laboratory value had a separate indicator of missingness included as its own characteristic. The primary panel of 58 characteristics excluded every variable in the demographic and diagnosis-based PS; at the clinical PS, the characteristics included in that PS were also removed.

The expanded panel was built from a review of 12 sources describing covariates in PS and trial emulation studies, including studies from our group, RCT-DUPLICATE protocols, the Sentinel PS tool, the high-dimensional PS and the OHDSI FeatureExtraction defaults. The review yielded 150 candidate covariates, which were implemented as 431 variables from the OMOP and Epic data, with all look-back windows ending the day before index. Within each trial, we excluded variables defining the exposure, variables with prevalence below 1% or above 99% or observed in fewer than 1% of patients, variables not strictly measured before index, and 67 ECG-proximal variables that an ECG encodes directly. The last group comprised rhythm and conduction disorders, devices and pacing, ablation and cardioversion, ventricular arrhythmias, cardiomyopathy and heart failure, myocardial infarction, natriuretic peptide, rate- and rhythm-control drugs, prior ECG counts and composite scores with such components. For each PS, we also excluded variables that overlapped with that PS, including composite scores with PS components, and, for the high-dimensional PS, variables whose codes could enter its selection. This left about 300 to 345 characteristics per trial depending on the PS. Variables were grouped into seven domains for display: comorbidities, medications, healthcare use and testing, additional laboratory values and vital signs, devices and procedures, risk and frailty scores, and preventive care.

For each trial and specification, we computed the proportion of characteristics with |SMD| <0.1 and the mean |SMD|. The relative reduction in mean |SMD| with the ECG was 1 minus the ratio of the mean |SMD| with and without the ECG, averaged across trials, with a percentile 95% CI from 2,000 bootstrap resamples of trials; it does not depend on a threshold. As an additional multivariate measure, a treatment classifier was cross-fitted (5-fold) on all held-out characteristics in the matched sample, with median imputation and missingness indicators; an area under the curve of 0.5 indicates groups that cannot be distinguished. Changes in balance by characteristic and domain were examined descriptively.

For agreement with RCTs, let θ~E~ and θ~R~ be the emulated and RCT log HRs with standard errors s~E~ and s~R~. Estimate agreement was |θ~E~ − θ~R~| ≤1.96 s~R~, standardized difference agreement was |θ~E~ − θ~R~| / (s~E~^2^ + s~R~^2^)^1/2^ <1.96, and the Pearson correlation was computed between θ~E~ and θ~R~ across trials.^4,5^ The absolute difference |θ~E~ − θ~R~| was compared between specifications within each trial. In the benchmark-permutation test, RCT results were reassigned at random across trials 20,000 times, and the reduction in the mean absolute difference with the ECG was recomputed each time. A reduction larger than under reassignment indicates movement toward each trial's own result rather than a general shrinkage of extreme estimates.

### eMethods 7. Plasmode simulation
Simulations were run in 31 trials and 107 trial–confounder combinations. These were trials in which at least 300 patients per treatment group had the confounder recorded, after exclusion of one combination whose simulated event rate was less than half the observed rate. The confounders were echocardiographic LVEF, NT-proBNP (log-transformed), body mass index and estimated glomerular filtration rate, standardized within the analysis set. Treatment was simulated from a logistic model including the observed demographic PS logit and the confounder, with an odds ratio of 1.25, 1.5 or 2 per standard deviation, and calibrated to the observed proportion treated. Event times were simulated from a Weibull proportional hazards model including the observed clinical covariates, with coefficients estimated in the real data, the confounder, with an HR of 1.25, 1.5 or 2 per standard deviation, and treatment, with a true HR of 0.80. A null scenario had no confounding. Censoring was administrative at the trial horizon or end of data. Real covariates, ECGs and index dates were retained, and simulated event rates were close to observed rates (median, 21.0% vs 20.4%). In each of 50 replicates per scenario, 80% of patients were sampled without replacement, treatment and outcome were redrawn, and every PS was refitted and rematched. The compared arms were the demographic PS alone and with the ECG components, the permuted-ECG placebo, 32 noise columns, or the confounder itself (oracle). The true marginal log HR in each matched population was computed from simulated potential outcomes under both treatments, which accounts for non-collapsibility. Bias was the mean difference between the estimated and true log HR, and the proportion of bias removed was 1 minus the ratio of bias with and without the added components, pooled over the nine confounding scenarios. We also report CI coverage of the true value. The ECG's ability to encode each confounder was estimated in the real data as the cross-fitted R^2^ of the confounder on the ECG components, and as the partial R^2^ given demographics. The confounders were oriented so that higher values increased both treatment and hazard. Two sensitivity variants were added after the primary simulation had been examined: one with LVEF and estimated glomerular filtration rate oriented in their clinically adverse direction, and one in which the outcome depended on the confounder and treatment only.

### eMethods 8. Design-step diagnostics and enrichment
Residual imbalance in ECG phenotypes was examined across five successive design steps: initiators without trial eligibility criteria; the emulated trial population; sparse PS matching; high-dimensional PS matching; and clinical PS matching. For enrichment, the cross-fitted AI-ECG risk score for each trial's primary outcome was compared with clinical and CLMBR-T scores, and the reduction in sample size was estimated for enrolment of patients in the top quartile of predicted risk.

### eMethods 9. Sensitivity analyses
All sensitivity estimands were computed in the same matched samples as the primary estimate. Per-protocol effects censored patients at deviation from the assigned strategy, with grace periods of 180, 365 and 730 days and stabilized inverse-probability-of-censoring weights; a switch-only estimand censored only at initiation of the comparator strategy. Because orders carry no days' supply, the switch-only estimand was considered the most reliable on-treatment estimand. We also estimated effects in a 90-day landmark analysis and in a 90-day run-in analysis requiring at least one repeat order of the assigned drug within 90 days, analogous to an active run-in. These estimands were not applicable to the four trials with a one-time procedure arm, and the run-in analysis was not estimable in trials with 50 or fewer patients retained. In a separate analysis, cohorts were restricted to patients initiating treatment outside an inpatient stay, using an a priori classification of each RCT's setting. Analyses by emulation quality, including the analysis excluding the six trials with limited emulation quality, were post hoc.

### eMethods 10. Statistical software
Core analyses used Python 3.11.16, with pandas 2.3.3, NumPy 2.4.6, DuckDB 1.5.5, scikit-learn 1.9.1, lifelines 0.30.3, SciPy 1.17.1, statsmodels 0.15.0 and matplotlib 3.11.2. ECG embeddings were computed with PyTorch 2.5.0, and CLMBR-T representations with PyTorch 2.13.0 and FEMR 0.2.3. Tests were one-sided where the direction was prespecified and two-sided otherwise.

---

### Draft notes (remove before submission)
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
  - The PI's bracketed request in Introduction paragraph 2 ("richer clinical information") is still open.
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
