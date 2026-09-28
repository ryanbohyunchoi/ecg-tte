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

*Working draft; last updated 2026-09-28. Draft notes are marked and must be removed before submission.*

## Key Points

**Question:** *(to write)*

**Findings:** *(to write)*

**Meaning:** *(to write)*

## Abstract

*(to be written last; JAMA structure: Importance; Objective; Design, Setting, and Participants; Exposures; Main Outcomes and Measures; Results; Conclusions and Relevance; ≤350 words)*

## Introduction

Randomization is the foundation of causal inference in medicine. Treatment is assigned by chance, so measured and unmeasured characteristics are, on average, balanced between arms. Differences in outcomes can then be attributed to the treatment itself.^1^ Randomized controlled trials (RCTs) are, however, expensive and time-consuming. They are also often infeasible or unrepresentative for important populations, such as older, multimorbid or underrepresented patients who receive these therapies in practice.^2^

Inferring causal effects from the data already generated in routine care therefore remains an unmet need. Target trial emulation is a leading candidate approach.^3^ The protocol of a hypothetical randomized trial is specified explicitly and then emulated in observational data. Confounding is typically addressed with propensity scores (PS) estimated from structured variables. This strategy balances measured characteristics well, and benchmarking against completed RCTs has shown that well-designed emulations can reproduce trial results.^4,5^ Its guarantee extends only to what is measured, however. Most emulations rely on claims data, which record diagnoses, procedures and prescriptions consistently. Electronic health records (EHRs) contain richer clinical information, but laboratory values, vital signs and imaging are missing for many patients, and not at random. These measurements therefore cannot be relied on for adjustment.^6^

This gap is particularly consequential in cardiovascular medicine. Many determinants of both treatment choice and prognosis are physiological: ventricular function, chamber size, atrial substrate, congestion and conduction. These are the characteristics most likely to confound comparisons and least likely to be captured in structured data. The 12-lead electrocardiogram (ECG) offers a potential solution. It is inexpensive and acquired routinely across the health system. Artificial intelligence applied to the ECG (AI-ECG) detects left ventricular dysfunction, structural heart disease and other latent phenotypes.^7–9^ Foundation-model embeddings compress this information into general-purpose representations of cardiac physiology.^10^ Because the ECG measures current physiology and is available for most patients, AI-ECG may capture confounding that structured data miss.

Here, we evaluated whether AI-ECG embeddings capture confounding missed by structured data in 38 emulations of cardiovascular RCTs. We assessed (i) balance on held-out clinical, laboratory and echocardiographic characteristics, (ii) agreement with RCT results, (iii) bias removal in simulations with a known treatment effect, and (iv) utility for trial enrichment.

## Methods

### Data sources
We used electronic health record (EHR) data from the Yale New Haven Health System (YNHHS), a large academic health system in Connecticut and Rhode Island. We mapped the structured EHR data to the Observational Medical Outcomes Partnership (OMOP) common data model ourselves. We linked these data to structured echocardiography reports, raw 12-lead ECG signals and state vital statistics records (eMethods 1). We included patients with index dates from 2011 through 2024. The Yale Institutional Review Board approved the study (protocol number [ ]) and waived informed consent for this secondary analysis of existing data.

### Target trial specification
We emulated 38 randomized controlled trials (RCTs) of cardiovascular therapies with active comparators. The trials covered atrial fibrillation (AF; 12 trials), diabetes (9), heart failure (5), hypertension (5), acute coronary syndromes (2) and other indications (5) (eTable 1). Each emulation used a new-user, active-comparator design that mirrored the trial protocol:
- trial eligibility criteria;
- time zero at the first order of the study drug or procedure, with a 365-day washout for the comparator;
- follow-up to the trial-matched horizon;
- the trial's primary endpoint;
- an initiator (intention-to-treat–like) estimand.

Operational definitions are given in eMethods 2.

### Trial selection and prespecification
Trials were assembled in three sets:
1. a development set (18 trials);
2. a general confirmation set (15 trials), drawn largely from RCT-DUPLICATE;^4,5^
3. an AF confirmation set (5 trials).

For each confirmation set, the analysis plan, trial specifications and published hazard ratios (HRs) were fixed in a version-controlled repository before any results were computed. An independent rater, blinded to all results, graded emulation fidelity and the a priori relevance of ECG-reflected physiology to each trial (eMethods 3).

### AI-ECG and EHR representations
We used the most recent 12-lead ECG within 365 days before or on the index date. ECGs were encoded with an in-house signal model adapted from our image-based biometric contrastive learning (BCL) model.^10^ This self-supervised model produced a 256-dimensional embedding per ECG, which was reduced to 32 principal components within each trial (eMethods 4). To test whether any gains reflected ECG information rather than added dimensions, we used a permuted-ECG placebo, in which embeddings were shuffled between patients.

For comparison, we used CLMBR-T-base, a structured-EHR foundation model.^11^ We applied it to each patient's coded history before the index date and reduced its output to 64 principal components.

### Propensity scores and matching
The primary propensity score (PS) included demographics only (age, sex and calendar year). We also evaluated progressively richer specifications:
- demographics plus five cardiometabolic diagnoses;
- a sparse diagnosis-based PS;
- a high-dimensional PS;^6^
- a clinical PS including vital signs, laboratory values and ejection fraction.

Each specification was fitted with and without the ECG and CLMBR-T representations and the placebo. Patients were matched 1:1 on the PS logit using nearest-neighbour matching with a caliper of 0.2 SD (eMethods 5).

### Outcomes
The primary balance outcome was the proportion of 58 held-out characteristics with an absolute standardized mean difference (SMD) <0.1. None of these characteristics were included in the PS under evaluation. They comprised medication, utilization and coded-record summaries; vital signs; laboratory values including NT-proBNP; and 35 echocardiographic measures (eTable 2). An expanded panel of about 400 characteristics was used in sensitivity analyses.

Agreement with RCTs was measured as:
- the absolute difference between emulated and RCT log HRs;
- statistical consistency with the RCT estimate.

Emulated HRs were estimated with Cox models with robust variance clustered on matched pairs. A benchmark-permutation test distinguished trial-specific agreement from generic attenuation of extreme estimates (eMethods 6).

### Simulation and ECG-based diagnostics
In plasmode simulations with a true HR of 0.80, a measured physiological variable was withheld from every PS to act as an unmeasured confounder. The variables were ejection fraction, NT-proBNP, body mass index and estimated glomerular filtration rate. We quantified the proportion of the resulting bias removed by adding the ECG embedding (eMethods 7). We also examined ECG-phenotype imbalance across successive design steps, and the prognostic value of an AI-ECG risk score for trial enrichment (eMethods 8).

### Statistical analysis
Trials were the unit of replication. Paired differences between PS specifications were tested with exact sign-flip permutation tests across trials. We assessed robustness to clustering of related trials, leave-one-trial-out analysis and split-sample replication. The false discovery rate was controlled within analysis families. Analyses were designated as confirmatory or exploratory in advance, and all results are reported. Headline estimates were re-derived in three independent audits. Analyses were performed in Python 3.11 (eMethods 9).

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

## Supplementary Methods (eMethods)

### eMethods 1. Data sources
- **YNHHS** comprises multiple hospitals and an extensive outpatient network across Connecticut and Rhode Island.
- **EHR data:** our team mapped the structured Epic data to the OMOP common data model. The domains were diagnoses (ICD-10-CM), medication orders, procedures, laboratory measurements, vital signs and encounters. Source Epic tables supplemented the mapped data for race and ethnicity.
- **Echocardiography:** echocardiographic measurements were taken from structured echocardiography reports. Free text was not used.
- **Deaths:** deaths were identified from the EHR and from linked Connecticut vital statistics records, which also provided the listed causes.
- **ECGs:** ECGs were retrieved from the institutional archive as raw 10-second, 500 Hz 12-lead signals.
- **Follow-up:** follow-up extended through December 2024 for all-cause death and June 2024 for cause-specific death.

### eMethods 2. Emulation design
- **Eligibility:** patients were aged ≥18 years (or the trial minimum), had ≥365 days of prior EHR activity and met trial-specific inclusion and exclusion criteria operationalized from structured data.
- **Time zero:** the first qualifying order or procedure, with no comparator order in the preceding 365 days. Sequential switch designs were used where the trial compared a new therapy with continuation of an existing one.
- **Follow-up:** from the day after time zero until the outcome, death, end of data or the trial-matched horizon, whichever occurred first.
- **Outcomes:** hospitalization endpoints required a qualifying ICD-10 code during an inpatient stay. Cardiovascular death was defined from listed causes of death.

### eMethods 3. Prespecification, feasibility and blinded rating
- **Feasibility:** ≥300 patients with an ECG in the smaller arm and ≥50 pooled primary events. Feasibility was assessed using pooled counts only.
- **Near-duplicates:** cohorts sharing >80% of patient–index date records with an existing cohort were excluded.
- **Blinded rating:** the rater followed RCT-DUPLICATE-adapted criteria. These covered time-zero alignment, run-in periods, switching of baseline therapy, delayed effects with long follow-up, and comparator and outcome fidelity.

### eMethods 4. ECG and EHR representations
- **ECG model:** a transformer encoder applied to 12-lead signals and trained in-house with the BCL objective of the published image-based model.^10^ [Add architecture and training-data details.]
- **Embeddings:** the frozen encoder produced 256-dimensional embeddings, from which the first 32 principal components were computed within each trial.
- **Placebos:** a permuted-ECG placebo (embeddings reassigned at random between patients within each cohort) and a noise placebo of independent Gaussian variables of the same dimension.
- **CLMBR-T-base:** a 141-million-parameter model pretrained on the structured EHR data of 2.57 million patients at Stanford.^11^ It was applied frozen to pre-index coded history, producing 768-dimensional representations reduced to 64 principal components.

### eMethods 5. Propensity score specifications
- **Five-diagnosis PS:** hypertension, type 2 diabetes, coronary artery disease, AF and heart failure.
- **Sparse PS:** 9–13 investigator-selected cardiovascular diagnoses.
- **High-dimensional PS:** the 200 empirically selected codes most associated with treatment.
- **Clinical PS:** added vital signs, laboratory values, LVEF, medications and healthcare use.
- **Estimation:** PS were estimated with L2-penalized logistic regression on standardized covariates.
- **Matching:** greedy nearest-neighbour, without replacement.
- **Sensitivity analyses:** caliper 0.1, 1:3 matching, inverse probability and overlap weighting, and 4–256 ECG components.

### eMethods 6. Balance and agreement metrics
- **SMDs:** computed from observed values using the pooled SD before matching.
- **Expanded panel:** comorbidity and frailty indices, medication classes, healthcare use and additional laboratory values. It excluded variables in or derived from the PS, variables revealing treatment, and ECG-proximal characteristics.
- **Additional balance measures:** distributional and multivariate balance, and balance in measurement patterns.
- **Agreement metrics:**
  - a precision-standardized difference incorporating both standard errors;
  - statistical consistency, defined as |z| <1.96.
- **Benchmark-permutation test:** compared the observed improvement with that obtained after permuting RCT benchmarks across trials.

### eMethods 7. Plasmode simulation
- **Setting:** 31 trials, using repeated 80% subsamples that retained real covariates, ECGs and censoring.
- **Simulated data:** treatment and time-to-event outcomes were simulated to depend on the withheld confounder across a grid of confounding strengths.
- **Bias removed:** the proportion of the demographic-PS bias eliminated by adding the ECG embedding, the placebos or the confounder itself (oracle). It was related to the cross-validated variance in the confounder explained by the ECG.

### eMethods 8. Design-step diagnostics and enrichment
- **Design steps:**
  1. initiators without trial eligibility criteria;
  2. the emulated trial population;
  3. sparse PS matching;
  4. high-dimensional PS matching;
  5. clinical PS matching.
- **Enrichment:** the cross-fitted AI-ECG risk score for each trial's primary outcome was compared with clinical and CLMBR-T scores. Sample-size reduction was estimated from enrolment of patients in the top quartile of predicted risk.

### eMethods 9. Statistical software
- **Core analyses:** Python 3.11.16, with pandas 2.3.3, NumPy 2.4.6, DuckDB 1.5.5, scikit-learn 1.9.1, lifelines 0.30.3, SciPy 1.17.1, statsmodels 0.15.0 and matplotlib 3.11.2.
- **ECG embeddings:** PyTorch 2.5.0.
- **CLMBR-T representations:** PyTorch 2.13.0 and FEMR 0.2.3.
- **Tests:** one-sided where the direction was prespecified; two-sided otherwise.

---

### Draft notes (remove before submission)
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
