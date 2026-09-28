# AI-enhanced electrocardiography as a phenotypic probe of confounding in target trial emulation: an evaluation across 38 cardiovascular trials

*Working draft; last updated 2026-09-28. Sections are added in order. Draft notes are marked and must be removed before submission.*

## Abstract

*(to be written last)*

## Introduction

Randomization is the foundation of causal inference in medicine. Treatment is assigned by chance, so measured and unmeasured characteristics are, on average, balanced between arms. Differences in outcomes can then be attributed to the treatment itself.^1^ Randomized controlled trials (RCTs) are, however, expensive and time-consuming. They are also often infeasible or unrepresentative for important populations, such as older, multimorbid or underrepresented patients who receive these therapies in practice.^2^

Inferring causal effects from the data already generated in routine care therefore remains an unmet need. Target trial emulation is a leading candidate approach.^3^ The protocol of a hypothetical randomized trial is specified explicitly and then emulated in observational data. Confounding is typically addressed with propensity scores (PS) estimated from structured variables. This strategy balances measured characteristics well, and benchmarking against completed RCTs has shown that well-designed emulations can reproduce trial results.^4,5^ Its guarantee extends only to what is measured, however. Most emulations rely on claims data, which record diagnoses, procedures and prescriptions consistently. Electronic health records (EHRs) contain richer clinical information, but laboratory values, vital signs and imaging are missing for many patients, and not at random. These measurements therefore cannot be relied on for adjustment.^6^

This gap is particularly consequential in cardiovascular medicine. Many determinants of both treatment choice and prognosis are physiological: ventricular function, chamber size, atrial substrate, congestion and conduction. These are the characteristics most likely to confound comparisons and least likely to be captured in structured data. The 12-lead electrocardiogram (ECG) offers a potential solution. It is inexpensive and acquired routinely across the health system. Artificial intelligence applied to the ECG (AI-ECG) detects left ventricular dysfunction, structural heart disease and other latent phenotypes.^7–9^ Foundation-model embeddings compress this information into general-purpose representations of cardiac physiology.^10^ Because the ECG measures current physiology and is available for most patients, AI-ECG may capture confounding that structured data miss.

Here, we evaluated whether AI-ECG embeddings capture confounding missed by structured data in 38 emulations of cardiovascular RCTs. We assessed (i) balance on held-out clinical, laboratory and echocardiographic characteristics, (ii) agreement with RCT results, (iii) bias removal in simulations with a known treatment effect, and (iv) utility for trial enrichment.

## Methods

### Data sources
We used data from the Yale New Haven Health System (YNHHS), a large academic health system with multiple hospitals and an extensive outpatient network across Connecticut and Rhode Island. Structured EHR data were obtained from an Observational Medical Outcomes Partnership (OMOP) common data model extract and the source Epic tables. They included diagnoses (ICD-10-CM), medication orders, procedures, laboratory measurements, vital signs and encounters. Echocardiographic measurements were obtained from structured echocardiography reports. Deaths were identified from the EHR and linked Connecticut vital statistics records, which also provided causes of death. Twelve-lead ECGs were obtained from the institutional ECG archive as raw 10-second, 500 Hz signals. The study included patients with an index date between 2011 and 2024, with follow-up through December 2024.

The Yale Institutional Review Board approved the study protocol (protocol number [ ]) and waived the need for informed consent, as the study represents secondary analysis of existing data.

### Target trial specification
We emulated 38 randomized controlled trials (RCTs) of cardiovascular therapies. Each used an active comparator or an established active-comparator adaptation of a placebo-controlled design. The trials spanned atrial fibrillation (AF; 12 trials), diabetes (9), heart failure (HF; 5), hypertension (5), acute coronary syndrome or myocardial infarction (2) and other indications (5) (Supplementary Table 1).

Each emulation followed a new-user, active-comparator design that mirrored the corresponding trial protocol:
- **Eligibility:** trial inclusion and exclusion criteria were operationalized from structured data. All patients were aged ≥18 years (or the trial minimum) and had ≥365 days of prior EHR activity.
- **Time zero:** the first order for the study drug or procedure, with no order for the comparator in the preceding 365 days. Sequential switch designs were used where the trial compared a new therapy against continuation of an existing one.
- **Follow-up:** from the day after time zero until the outcome, death, the end of available data or the trial-matched follow-up horizon, whichever came first.
- **Outcome:** each trial's primary endpoint, mapped to EHR events. Hospitalization endpoints required a qualifying diagnosis during an inpatient stay. Cardiovascular death was defined from listed causes of death.
- **Estimand:** the effect of treatment initiation, analogous to the intention-to-treat effect.

### Trial selection and prespecification
Trials were assembled in three sets:
1. **Development set (18 trials),** in which the analytic approach was developed.
2. **General confirmation set (15 trials),** drawn largely from trials emulated in the RCT-DUPLICATE initiative.^4,5^
3. **AF confirmation set (5 trials).**

The analysis plan for each confirmation set was fixed before any of its results were computed. For each new trial, the trial specification and the published primary hazard ratio (HR) were registered in a version-controlled repository before outcome extraction.

Feasibility required ≥300 patients with an ECG in the smaller treatment arm and ≥50 primary-outcome events. It was assessed using pooled counts only. Candidate cohorts sharing >80% of patient–index date records with an existing cohort were excluded as duplicates.

An independent rater, blinded to all emulation results, classified the emulation fidelity of each trial using criteria adapted from RCT-DUPLICATE.^5^ These criteria cover time-zero alignment, run-in periods, switching of baseline therapy, delayed effects with long follow-up, and comparator and outcome fidelity. The rater also classified, a priori, the relevance of ECG-reflected physiology to treatment choice and prognosis in each trial.

### Study exposure: AI-ECG representations
For each patient, we used the most recent 12-lead ECG obtained within 365 days before or on the index date. ECGs were encoded with an in-house signal model: a transformer encoder adapted from our previously developed image-based biometric contrastive learning (BCL) model and trained with the same self-supervised objective on 12-lead ECG signals (Supplementary Methods).^10^ The objective learns patient-specific representations of the ECG without diagnostic labels. The frozen encoder produced a 256-dimensional embedding per ECG. Within each trial, embeddings were reduced to their first 32 principal components, which entered the propensity score (PS) as covariates.

We constructed two placebo representations of the same dimension:
- a **permuted-ECG placebo,** in which embeddings were randomly reassigned between patients within each cohort;
- a **noise placebo** of independent standard Gaussian variables.

As a comparator representation derived from the structured record, we used CLMBR-T-base, a 141-million-parameter foundation model developed at Stanford and pretrained on the structured EHR data of 2.57 million patients.^11^ The frozen model was applied to each patient's coded history before the index date. The resulting 768-dimensional representations were reduced to 64 principal components.

### Propensity score specifications and matching
The primary PS included demographics only (age, sex and calendar year of index). This represents settings in which few structured covariates are reliably captured. We also evaluated progressively richer specifications:
- demographics plus five cardiometabolic diagnoses (hypertension, type 2 diabetes, coronary artery disease, AF and HF);
- the same with obesity;
- a sparse PS of demographics and 9–13 investigator-selected cardiovascular diagnoses;
- a high-dimensional PS adding the 200 codes most strongly associated with treatment;^6^
- a clinical PS adding vital signs, laboratory values, left ventricular ejection fraction (LVEF), medications and healthcare use.

Each specification was fitted alone, with the ECG embedding, with CLMBR-T, with both, and with each placebo. PS were estimated using L2-penalized logistic regression on standardized covariates. Patients were matched 1:1 on the logit of the PS using greedy nearest-neighbour matching without replacement and a caliper of 0.2 standard deviations. Sensitivity analyses varied the caliper, the matching ratio and the number of ECG components, and used inverse probability and overlap weighting.

### Study outcomes
**Covariate balance.** Balance was assessed on 58 characteristics that were not included in the PS under evaluation (Supplementary Table 2). They comprised:
- summaries of medications, healthcare use and held-out diagnosis and procedure codes;
- an external prognostic score;
- vital signs and laboratory values, including NT-proBNP;
- 35 echocardiographic measures of left ventricular structure and function, diastolic and left atrial function, right ventricular and pulmonary haemodynamics, and valvular disease.

Standardized mean differences (SMD) were calculated in the matched sample using observed values and the pooled standard deviation before matching. The primary balance outcome was the proportion of held-out characteristics with an absolute SMD <0.1 in each trial. We further evaluated an expanded panel of about 400 pre-index characteristics:
- comorbidity and frailty indices, medication classes, healthcare use and additional laboratory values;
- excluding variables included in or derived from the PS, variables that could reveal treatment assignment, and characteristics directly reflected in the ECG.

**Agreement with RCT results.** For each emulation, we calculated:
- the absolute difference between the emulated and RCT log HR;
- a precision-standardized difference incorporating the standard errors of both estimates;
- whether the emulated estimate was statistically consistent with the RCT.

HRs were estimated using Cox proportional hazards models with robust standard errors clustered on matched pairs.

To distinguish movement toward each trial's own result from generic attenuation of extreme estimates, we compared the observed improvement with that obtained after permuting RCT benchmarks across trials.

### Simulation with a known treatment effect
To quantify bias reduction directly, we performed plasmode simulations in 31 trials. Real covariates, ECGs and censoring patterns were retained, and repeated 80% subsamples were drawn.
- **Hidden confounder:** one measured physiological variable (LVEF, NT-proBNP, body mass index or estimated glomerular filtration rate) was designated as an unmeasured confounder and excluded from every PS.
- **Simulated treatment and outcomes:** treatment assignment and time-to-event outcomes were simulated to depend on this variable across a range of confounding strengths, with a true HR of 0.80.
- **Bias removed:** the proportion of the demographic-PS bias eliminated by adding the ECG embedding, the placebos, or the confounder itself (oracle). We related this proportion to the cross-validated variance in the confounder explained by the ECG embedding.

### ECG-based diagnostics and trial enrichment
To evaluate AI-ECG as a diagnostic of residual confounding, we measured imbalance in AI-ECG-derived phenotypes, and the ability of the ECG embedding to discriminate treatment groups, at successive design steps:
1. a comparison of initiators without trial eligibility criteria;
2. the emulated trial population;
3. matching on the sparse PS;
4. matching on the high-dimensional PS;
5. matching on the clinical PS.

To evaluate utility for trial design, we derived a cross-fitted AI-ECG risk score for each trial's primary outcome. We compared its prognostic performance with that of clinical and EHR-embedding scores. We also estimated the reduction in required sample size from enrolling patients in the highest quartile of predicted risk.

### Statistical analysis
Trials were treated as the unit of replication. Differences between PS specifications were tested with exact sign-flip permutation tests on per-trial paired differences. The tests were one-sided where the direction was prespecified and two-sided otherwise. Robustness was assessed by:
- clustering trials that share comparator populations;
- leave-one-trial-out analyses;
- replication in two random, treatment-stratified halves of each cohort.

The false discovery rate was controlled with the Benjamini–Hochberg procedure within analysis families. Analyses were designated prospectively as confirmatory or exploratory, and all results are reported regardless of direction. Three rounds of independent audit re-derived headline estimates from aggregate outputs and confirmed that each prespecification preceded the corresponding results.

**Software.** All analyses were performed in Python 3.11.16, using:
- pandas 2.3.3 and NumPy 2.4.6 for data processing;
- DuckDB 1.5.5 for database queries;
- scikit-learn 1.9.1 for PS models and imputation;
- lifelines 0.30.3 for survival analysis;
- SciPy 1.17.1 and statsmodels 0.15.0 for statistical testing;
- matplotlib 3.11.2 for figures.

ECG embeddings were generated with PyTorch 2.5.0. CLMBR-T representations were generated with PyTorch 2.13.0 and FEMR 0.2.3.

## Results

*(pending)*

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

---

### Draft notes (remove before submission)
- **Methods v2 (2026-09-28), written in the style of Khera-lab methods sections** (headings such as "Data sources" and "Study exposure"; the standard IRB and software sentences):
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
