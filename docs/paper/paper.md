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

### Study design and data source
We conducted a series of target trial emulations using electronic health records (EHR) from the Yale New Haven Health System. The system is a large academic network of hospitals and outpatient practices in Connecticut. Structured data were obtained from an Observational Medical Outcomes Partnership (OMOP) common data model extract, supplemented by the Epic source tables. The extract included diagnoses (ICD-10-CM), medication orders, procedures, laboratory measurements, vital signs and encounters. Echocardiographic measurements were taken from structured echocardiography reports. Deaths and causes of death came from the EHR and linked Connecticut vital statistics records. Twelve-lead ECGs were obtained from the institutional ECG archive as raw 10-second, 500 Hz waveforms. Index dates spanned 2011–2024, and follow-up extended to the end of available data (December 2024 for all-cause death; June 2024 for cause-specific death). The study was approved by the Yale Institutional Review Board with a waiver of informed consent [confirm protocol number]. Only aggregate results are reported.

### Selection of target trials
We emulated 38 randomized trials of cardiovascular therapies with an active comparator (or an active-comparator adaptation), spanning five areas:
- atrial fibrillation (12 trials);
- diabetes (9);
- heart failure (5);
- hypertension (5);
- acute coronary syndrome or myocardial infarction (2);
- other indications (5).

The trials were selected in three sequential sets (Supplementary Table 1):
- **Development set (18 trials):** the 18 trials in which the analytic approach was developed.
- **General confirmation set (15 trials):** drawn largely from trials emulated by the RCT-DUPLICATE initiative.^4,5^
- **Atrial fibrillation confirmation set (5 trials).**

Each confirmation set was fixed before any of its results were computed. For every new trial, the specification and the published primary hazard ratio (HR) were registered in the project repository before outcome extraction. Feasibility screens used only pooled counts. Trials were required to have at least 300 patients with an ECG in the smaller arm and at least 50 pooled primary-outcome events. Candidate cohorts were excluded as near-duplicates if more than 80% of their patient–index date records coincided with an existing cohort.

An independent rater, blinded to all emulation results, classified each trial's emulation fidelity using criteria adapted from RCT-DUPLICATE.^5^ These criteria covered:
- time-zero alignment;
- run-in periods;
- switching of baseline therapy;
- long follow-up with delayed effects;
- comparator and outcome fidelity.

The rater also graded each trial's a-priori relevance of ECG-reflected physiology to treatment choice and prognosis.

### Emulation design
Each emulation followed a new-user, active-comparator design mirroring the corresponding trial protocol (Supplementary Table 1).
- **Eligibility:** trial-specific inclusion and exclusion criteria were operationalized from structured data. Patients were aged 18 years or older (or the trial minimum) and had at least 365 days of prior EHR activity.
- **Time zero:** the date of the first qualifying order for the study drug or procedure, with no order for the comparator in the preceding 365 days. Switch and procedure designs were specified where the trial required them.
- **Follow-up:** from the day after time zero to the earliest of the outcome, death, end of data or the trial-matched follow-up horizon.
- **Outcomes:** each trial's primary endpoint, mapped to EHR events. Hospitalization endpoints required a qualifying ICD-10 code during an inpatient stay. Cardiovascular death was defined from listed causes of death.
- **Estimand:** the initiator (intention-to-treat–like) effect.

### AI-ECG embeddings
For each patient we used the most recent 12-lead ECG within 365 days before or on the index date. ECGs were encoded with a transformer encoder pretrained with biometric contrastive learning (BCL).^10^ This self-supervised model learns patient-specific ECG representations without diagnostic labels. It was applied frozen to raw waveforms. The resulting embeddings were reduced to their first 32 principal components within each trial. Two placebo representations of the same dimension were constructed:
- a **permuted-ECG placebo**, in which each patient was assigned the embedding of another randomly selected patient in the same cohort;
- a **noise placebo** of independent Gaussian variables.

As a comparator representation derived from the structured record, we used a code-based EHR foundation model (CLMBR-T; 64 principal components) applied to each patient's coded history before the index date.^11^

### Propensity score specifications
The primary propensity score (PS) included demographics only: age, sex and calendar year of index. This mimics settings in which few structured covariates are reliably available. We also evaluated a ladder of progressively richer PS specifications:
- demographics plus five cardiometabolic diagnoses (hypertension, type 2 diabetes, coronary disease, atrial fibrillation and heart failure);
- the same plus obesity;
- a sparse PS of demographics plus 9 to 13 investigator-selected cardiovascular diagnoses;
- a high-dimensional PS adding the 200 empirically selected codes most associated with treatment;^6^
- a clinical PS adding vital signs, laboratory values, left ventricular ejection fraction, medications and healthcare use.

Each specification was fitted with and without the ECG embedding and with each placebo. PS were estimated by L2-penalized logistic regression on standardized covariates. Patients were matched 1:1 by greedy nearest-neighbour matching on the logit of the PS without replacement, with a caliper of 0.2 standard deviations. In sensitivity analyses we varied the caliper, the matching ratio (1:3), the weighting (inverse probability and overlap weights) and the number of ECG components.

### Outcomes of the evaluation

**Covariate balance.** Balance was assessed on 58 characteristics that were not included in the PS under evaluation (Supplementary Table 2), in six groups:
- coded-record summaries: medication classes, healthcare use, held-out diagnosis and procedure codes, and an external prognostic score;
- vital signs and core laboratory values;
- other laboratory values including NT-proBNP;
- echocardiographic measures of left ventricular structure;
- echocardiographic measures of left ventricular function, diastolic and left atrial function, and right ventricular and pulmonary haemodynamics;
- valves.

Standardized mean differences (SMD) were computed in the matched sample, using the pooled standard deviation of the unmatched cohort and only observed values. The primary balance endpoint was the proportion of held-out characteristics with an absolute SMD below 0.1, computed per trial. In sensitivity analyses we used an expanded panel of about 400 additional pre-index characteristics. This panel included comorbidity indices, frailty, medications, healthcare use and further laboratory values. It excluded variables in or derived from the PS, variables that could reveal the assigned treatment, and ECG-proximal variables. We also assessed distributional and multivariate balance and balance on measurement patterns.

**Agreement with RCT results.** For each emulation we computed the absolute difference between the emulated and RCT log HR. We also computed a precision-standardized difference, which accounts for the standard errors of both estimates, and whether the emulated estimate was statistically consistent with the RCT.

To distinguish movement toward each trial's own result from generic attenuation of extreme estimates, we used a benchmark-shuffle test. The observed improvement was compared with the improvement obtained when RCT benchmarks were permuted across trials.

### Simulation with a known treatment effect
To quantify bias removal directly, we performed plasmode simulations in 31 trials. Each simulation retained real patient covariates, ECGs and censoring and used repeated 80% subsamples.
- **Hidden confounder:** one measured physiological variable (echocardiographic LVEF, NT-proBNP, body mass index or estimated glomerular filtration rate) was designated as a confounder.
- **Treatment and outcomes:** treatment assignment and outcomes were simulated to depend on the hidden confounder across a grid of strengths, with a true HR of 0.80.
- **Estimation:** the confounder was excluded from every PS.
- **Bias removal:** calculated as the proportion of the demographic-PS bias eliminated by adding the ECG, the placebos or the confounder itself, which served as an oracle. We related it to the cross-validated proportion of variance in the confounder explained by the ECG.

### ECG imbalance across design steps and trial enrichment
To evaluate AI-ECG as a diagnostic of residual confounding, we measured imbalance in ECG-derived phenotypes and the ability of the ECG embedding to predict treatment at successive design steps:
1. a crude comparison without trial eligibility criteria;
2. the emulated trial cohort;
3. sparse PS matching;
4. high-dimensional PS matching;
5. clinical PS matching.

To evaluate trial-design utility, we derived a cross-fitted AI-ECG risk score for each trial's primary outcome. We compared its prognostic performance with clinical and EHR-embedding scores and estimated the reduction in required sample size from enrolling patients in the top quartile of predicted risk.

### Statistical analysis
Because trials are the unit of replication, comparisons between PS specifications used exact one-sided sign-flip permutation tests across trials on per-trial paired differences. One-sided tests were used where the direction was prespecified, and two-sided tests otherwise.

Robustness was assessed in four ways:
- **Clustering:** tests were clustered by comparator class, because some trials share comparator populations.
- **Leave-one-trial-out:** each trial was omitted in turn.
- **Split halves:** the analysis was replicated in two random, treatment-stratified halves of each cohort.
- **Multiple comparisons:** the false discovery rate was controlled with the Benjamini–Hochberg procedure within analysis families.

Analyses were designated prospectively as confirmatory (the prespecified confirmation sets) or exploratory (all others). All results are reported regardless of direction. Three rounds of independent audit re-derived all headline estimates from aggregate outputs. The audits also verified that pre-registration and blinding commitments preceded the corresponding results. Analyses used Python 3.11 (scikit-learn, lifelines [confirm]).

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
11. Steinberg E, Jung K, Fries JA, Corbin CK, Pfohl SR, Shah NH. Language models are an effective representation learning technique for electronic health record data. *J Biomed Inform.* 2021;113:103637. [verify]

---

### Draft notes (remove before submission)
- **Methods v1 (2026-09-28). Items to confirm:**
  - IRB protocol number;
  - the index period (2011–2024, from the cohort index dates);
  - the BCL architecture wording (the transformer BCL checkpoint; the published BCL used a CNN on ECG images, so check which reference applies);
  - the embedding dimension before PCA;
  - software versions;
  - the CLMBR reference (ref 11, to verify).
- **Supplementary tables referenced:**
  - S1: 38 trial specifications with RCT HRs and the blinded rating;
  - S2: the 58 held-out variables and the expanded panel.
- **Introduction v3 (2026-09-28):**
  - It follows the PI outline: randomization, then RCT limits, then the unmet need, then TTE with a PS on structured data (strengths and limits), then EHR missingness vs claims, then CV physiology and AI-ECG, then "Here, we".
  - References 1–10 are checked against PubMed/publisher pages. Still to confirm: the ref 9 full author list and the ref 10 page range.
- **Optional closing sentence for the Introduction**, consistent with the v1.6–v1.9 results and the round-4 audit: "We find that AI-ECG embeddings improve balance on unmeasured physiology and remove confounding bias in proportion to how well they encode the confounder, but do not by themselves reproduce trial-specific RCT results."
- **Possible additional citation:** DISCO (Biswas D, Dhingra LS, Aminorroaya A, Croon PM, Oikonomou EK, Khera R. *Eur Heart J* 2025;46(Suppl 1):ehaf784.4614), the closest precedent. Cite it in the Introduction or the Discussion.
