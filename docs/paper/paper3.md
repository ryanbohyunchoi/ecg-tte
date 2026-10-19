# LATENT-RCT: Foundation-Model Representations of the Electrocardiogram and the Electronic Health Record for Confounding Control in Target Trial Emulation

*Working draft (paper 3); first draft 2026-10-19. It supersedes paper.md (ECG only, PS-Demo primary, 38 trials) and paper2.md (TRACE-ECG, 32 trials, PS-Flags framing) for the current design (*`pipeline.md`*, updates to 2026-10-19). Target journal: to be decided. Reporting follows the TARGET guideline for target trial emulation and STROBE.*

*Markers:*

- *[CHECK]: a number or statement not yet verified against its source, or a value whose basis differs from the primary design.*
- *[PRELIMINARY]: a result from an incomplete run, to be replaced.*
- *[PENDING]: an analysis not yet run.*
- *[USER]: a decision awaiting the user.*

*Draft notes, marked as such, must be removed before submission.*

*Number sources:*

- *Yale (31 trials):* `docs/s31/S31_RESULTS.md`, `audits/claude-s31-20261014/summary_v1/` and `docs/queue/figure4.md` (audited).
- *MIMIC-IV:* `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md` and `docs/mimic/MIMIC_HDPS_WINDOW.md`.
- *CHS and SPRINT:* `audits/bdc-fig5/RESULTS_LOCAL.md` (aggregates relayed from BioData Catalyst; see the draft note on the public repository at the end).



## Abstract (UNEDITED)

**Importance.** Target trial emulations in electronic health records (EHRs) adjust for investigator-chosen covariates. Measured physiology is often missing, and building covariates from codes differs across health systems. Foundation models compress routine data into reusable patient representations, but whether these representations improve confounding control is not known.

**Objective.** To evaluate whether representations from an EHR foundation model (AI-EHR) and an electrocardiogram (ECG) foundation model (AI-ECG) improve covariate balance and agreement with randomized clinical trial (RCT) results in emulations of cardiovascular RCTs, and whether they can replace investigator-built propensity score (PS) covariates.

**Design, Setting and Participants.** The development cohort was the Yale New Haven Health System (YNHHS) EHR. Of 99 candidate cardiovascular RCTs, 37 were feasible and 31 passed emulation-quality grading; each was emulated as a new-user, active-comparator study. External validation used:

- MIMIC-IV, with 7 cardiovascular trials and 1 negative-control trial;
- the Cardiovascular Health Study (CHS), with 5 cohort emulations, on BioData Catalyst.

A hidden-confounder benchmark inside the SPRINT trial is preliminary.

**Exposures.** Each PS specification was fitted with and without AI-EHR (CLMBR-T, 64 principal components of the coded pre-index history) and AI-ECG (32 principal components of the pre-index 12-lead ECG), alone and together, and with permuted placebos. The primary PS (PS-CVD5) contained demographics and 5 cardiovascular diagnoses.

**Main Outcomes and Measures.**

- **Primary:** relative reduction in mean absolute standardized mean difference (|SMD|) on 54 held-out vital-sign, laboratory and echocardiographic characteristics after 1:1 PS matching.
- **Secondary:** the absolute difference between emulated and RCT log hazard ratios (|Δ log HR|), tested against a benchmark-permutation null.

**Results.** In 31 trials (211,054 patients), held-out imbalance fell when the representations were added to PS-CVD5:

- by 12.9% (95% CI, 7.6%–18.3%) with AI-EHR;
- by 8.7% (95% CI, 4.2%–13.5%) with AI-ECG;
- by 14.6% (95% CI, 7.7%–21.1%) with both.

Permuted placebos had no effect.

Without any investigator-chosen diagnoses, a PS of demographics plus both representations balanced held-out characteristics:

- 17.8% (95% CI, 11.8%–23.6%) better than PS-CVD5;
- 8.0% (95% CI, 1.9%–13.6%) better than a high-dimensional PS (hdPS);
- 7.0% (95% CI, 1.1%–12.7%) better than a clinical PS with measured vitals and laboratory values.

The two representations were complementary:

- AI-ECG gains were concentrated in echocardiographic measures of left ventricular (LV) structure and function and in trials whose treatment choice depends on cardiac physiology.
- AI-EHR gains were concentrated in laboratory values and vital signs.
- AI-EHR added nothing to an hdPS built from the same coded record (0.6%), whereas AI-ECG still added 7.1%.

Emulated hazard ratios moved closer to RCT results on average (|Δ log HR| 0.232 with PS-CVD5 vs 0.164 with demographics plus both representations), but not toward each trial's own result (benchmark-permutation P ≥ .26).

In MIMIC-IV, both representations together reduced imbalance by 18.6%, and AI-ECG added 10.8% on top of an hdPS built from the same coded window. In CHS, AI-ECG reduced held-out imbalance by 9.5% on average across 5 emulations, which was not statistically distinguishable from no effect with 4 comparator clusters. [CHS AI-EHR: PENDING.]

**Conclusions and Relevance.** Foundation-model representations of routine EHR and ECG data improved held-out covariate balance in trial emulations and, together, matched or exceeded investigator-built PS specifications without feature engineering. The EHR representation recovered information contained in the coded record, and the ECG added physiological information that codes do not capture. Neither produced trial-specific agreement with RCT results. Better balance on measured characteristics does not establish that unmeasured confounding is removed.

## Introduction

Randomization is the gold standard for causal inference in medicine. Treatment is assigned by chance, so measured and unmeasured characteristics are, on average, balanced between arms. Differences in outcomes can then be attributed to the treatment itself.^1^ Randomized controlled trials (RCTs) are, however, expensive and time-consuming. They are also often infeasible or unrepresentative for important populations, such as older, multimorbid or underrepresented patients who receive these therapies in practice.^2^

Inferring causal effects from the data already generated in routine care therefore remains an unmet need. Target trial emulation (TTE), in which the protocol of a hypothetical RCT is specified and then emulated in observational data, is a leading candidate approach.^3^ Confounding is traditionally addressed with propensity scores (PS) estimated from structured variables chosen by investigators. This strategy balances measured characteristics well, and benchmarking against completed RCTs has shown that well-designed emulations can reproduce trial results.^4,5^ However, its guarantee extends only to what is measured. Most emulations rely on claims data, which record diagnoses, procedures and prescriptions consistently.^6^ Electronic health records (EHRs) capture clinical measurements at the point of care and are available within individual health systems, making them actionable for site-specific evidence generation.^7^ However, laboratory values, vital signs and imaging are missing for many patients, and not at random. These measurements therefore cannot be relied on for adjustment.^8^

This gap is particularly consequential in cardiovascular medicine. Many determinants of both treatment choice and prognosis are physiological: ventricular function, chamber size, atrial substrate, congestion and conduction. These are the characteristics most likely to confound comparisons and least likely to be captured in structured data. The 12-lead electrocardiogram (ECG) offers a potential solution. It is inexpensive and acquired routinely across the health system.^9^ Artificial intelligence applied to the ECG (AI-ECG) detects left ventricular dysfunction, structural heart disease and other latent phenotypes.^9–12^ Foundation-model embeddings compress this information into general-purpose representations of cardiac physiology.^13^ Because the ECG records current cardiac physiology and is available for most patients, AI-ECG representations may capture confounding that structured data miss and partly compensate for physiological measurements that are missing from routine-care data.

The structured data themselves pose a second challenge. Conventional PS covariates, from a short list of diagnoses to the hundreds of code features selected by high-dimensional PS algorithms,^16^ must be specified, coded and validated for each study, and coding practices differ across health systems. Foundation models of the EHR offer an alternative. Models such as CLMBR-T are pretrained on sequences of diagnosis, medication, procedure, measurement and visit codes from millions of patients, and summarize each patient's coded history, including the order of events, in a general-purpose representation (AI-EHR) that requires no study-specific feature engineering.^22,23^ The two representations differ in what they can see. The ECG records current cardiac physiology that is rarely coded, whereas the EHR representation reflects which conditions were diagnosed and which tests and treatments were ordered, but not their measured values. Whether either representation improves confounding control beyond investigator-chosen covariates, and whether together they could replace them, is not known.

Here, we designed LATENT-RCT [USER: expansion of the acronym], in which we evaluated whether AI-ECG and AI-EHR representations improve confounding control in 31 emulations of cardiovascular RCTs in a large health system, with external validation in a second health system and in an epidemiological cohort study. We assessed (i) balance on held-out clinical, laboratory and echocardiographic characteristics when each representation was added to conventional PS specifications, (ii) whether a PS of demographics and the two representations could replace investigator-chosen covariates, (iii) agreement with RCT results, and (iv) bias removal in simulations with a known treatment effect.

## Methods



### Data sources

**Development cohort.**

- **Data:** structured EHR data of the Yale New Haven Health System (YNHHS), a large academic health system in the American northeast, mapped to the Observational Medical Outcomes Partnership (OMOP) common data model.
- **Linked data:** structured echocardiography reports, raw 12-lead ECG signals and state vital statistics records (eMethods 1).
- **Index dates:** from the later of January 1, 2013, or the drug's US approval, through June 30, 2024. [CHECK: pipeline.md §1 states 2011–2024; reconcile with the per-trial index windows in eTable 1.]
- **Ethics:** the Yale Institutional Review Board approved the study and waived informed consent for this secondary analysis of existing data.

**External validation cohorts.**

1. **MIMIC-IV (version 3.1)** with MIMIC-IV-ECG (version 1.0): deidentified EHR and 12-lead ECG data from Beth Israel Deaconess Medical Center, Boston, Massachusetts (eMethods 11).^14,21^
2. **The Cardiovascular Health Study (CHS):** a community cohort of adults aged 65 years or older with annual clinic visits, medication inventories, echocardiography, laboratory measures and adjudicated cardiovascular events. Its phenotype data (phs000287) and ECG files (phs003639) were accessed on the NHLBI BioData Catalyst under an approved data access request.
3. **SPRINT,** for the hidden-confounder benchmark: BioLINCC phs003483, with the SPRINT-Imaging baseline ECGs (phs003566) on BioData Catalyst.

Analyses on BioData Catalyst were run by the investigators within the platform, and only aggregate results were exported. [USER: confirm data-use and IRB statements for MIMIC-IV, CHS and SPRINT.]

### Trial selection and target trial specification

Trials were selected in two stages (eMethods 3).

**Stage 1: feasibility.** Of 99 candidate cardiovascular RCTs, 37 met all 5 feasibility criteria:

1. an active comparator, or an accepted proxy for a placebo comparator;
2. a primary end point ascertainable in the EHR;
3. identifiable intervention and comparator strategies;
4. at least 350 patients with an ECG in the smaller treatment group and at least 50 outcome events;
5. no near-duplicate cohort (≥80% overlap of patient–index records with another emulation).

**Stage 2: emulation quality.** Emulation quality was graded from design information, using a points-based adaptation of the RCT-DUPLICATE design-emulation criteria:^5^

- 1 point each for design flags (in-hospital initiation not reproduced, a responder or tolerability run-in, a baseline-therapy switch not mirrored, follow-up of 48 months or more, and other time-zero misalignment);
- 0, 1 or 2 points each for comparator and outcome fidelity.

Emulations were rated excellent (0 points), good, moderate or limited (≥4 points). Limited emulations were excluded.

**The analysed set** comprised 31 trials: 3 excellent, 11 good and 17 moderate (Table 1; Figure 1).

**Target trial protocols.** For each trial, we specified the target trial protocol and its emulation following the TARGET guideline, summarized using the population, intervention, comparator, outcome and time (PICOT) elements (Table 1; eMethods 2).^15^ Each emulation used a new-user, active-comparator design and estimated the effect of treatment initiation, analogous to the intention-to-treat effect.

**Post hoc change.** The size threshold was raised from 300 to 350 after near-separation of the richest PS models was observed in the smallest trial, PROTECT AF (314 patients in the smaller group). This removed only PROTECT AF. Results for the previous 32-trial set are reported as a sensitivity analysis (eTable [CHECK]).

### Learned representations

**AI-EHR.** We used CLMBR-T-base, a 141-million-parameter transformer foundation model of the coded EHR. It was pretrained at Stanford on the structured records of 2.57 million patients.^22,23^

- **Input:** each patient's coded history (diagnoses, drug orders, procedures, measurement codes without their values, and visits), up to the day before the index date, with the most recent 4,096 tokens used. It reads codes, never measured values.
- **Use:** the model was applied frozen, without fine-tuning.
- **Output:** its 768-dimensional representation was reduced to 64 principal components within each trial, with 32 components as a sensitivity analysis.

**AI-ECG.** We used the most recent 12-lead ECG within 365 days before or on the index date.

- **Encoder:** an AI-ECG signal model adapted from a biometric contrastive learning (BCL) model. This self-supervised approach learns patient-specific representations of cardiac structure and function without diagnostic labels.^13^
- **Output:** a 256-dimensional embedding per ECG, reduced to 32 principal components within each trial (eMethods 4).
- **Index-day ECGs:** included. Analyses excluding them are reported as a sensitivity analysis.

**Placebos.** Each representation was permuted between patients within each trial. This preserves its dimension and distribution but removes its information about the patient.

### Propensity score specifications

**Estimation.** Within each trial, the PS was estimated by L2-penalized (ridge) logistic regression on standardized covariates. The same penalty (inverse regularization strength 1) was used for every specification, so that only the covariates differed between comparisons (eMethods 5).

**Conventional specifications,** ordered by the number of inputs:

- **PS-Demo:** age, sex and calendar year of index.
- **PS-CVD5 (primary):** PS-Demo plus hypertension, type 2 diabetes, coronary artery disease, atrial fibrillation (AF) and heart failure.
- **PS-CVD10:** PS-CVD5 plus chronic kidney disease, chronic obstructive pulmonary disease or asthma, peripheral artery disease, stroke or transient ischaemic attack, and valvular heart disease.
- **PS-Clinical:** further included measured vital signs and laboratory values, diagnoses, medication orders and healthcare use.
  - No PS included left ventricular ejection fraction (LVEF) or any other echocardiographic measure.
  - Missing values were handled by multiple imputation (5 draws). Per-item |SMD| values were averaged across draws, and hazard ratios were combined by Rubin's rules.
- **High-dimensional PS (hdPS):** demographics, 9 to 13 investigator-selected diagnoses, and 200 empirically selected yes/no code features.^16^
  - Candidates were diagnosis, drug, procedure and laboratory-measured codes in the year before index.
  - They were ranked by their association with treatment within a random half of code features, with exposure drugs excluded.

**Arms.** Each specification was fitted alone and with AI-EHR, AI-ECG, both, or a permuted placebo, denoted, for example, PS-CVD5 + AI-EHR.

**Demographics plus AI representations.** To ask whether the representations can replace investigator-chosen covariates, we compared PS-Demo + AI-ECG, PS-Demo + AI-EHR and PS-Demo + AI-ECG + AI-EHR with PS-CVD5, the hdPS and PS-Clinical. These PS models contain no hand-picked diagnoses, laboratory values or code features.

**A diagnosis-flag PS (PS-Flags)** gives AI-EHR an equal-information comparator: PS-Demo plus a yes/no flag for every 3-character ICD-10-CM code recorded before index with at least 1% prevalence. It is reported in the supplement.

**Matching.** In the primary configuration, patients were matched 1:1 without replacement by greedy nearest-neighbour matching on the PS logit, with a caliper of 0.2 standard deviations of the logit. Cells with fewer than 11 matched pairs were treated as failed.

**Other configurations:**

- a caliper of 0.1;
- 1:3 matching;
- inverse probability of treatment weighting (IPTW);
- overlap weighting;^25^
- a gradient-boosted PS with 5-fold cross-fitting.



### Covariate balance

**Primary outcome.** The primary outcome was balance after matching on characteristics not included in the PS under evaluation, summarized as the absolute standardized mean difference (|SMD|).^17^

**The primary panel** comprised 54 non-coded characteristics (eTable 2):

- 9 vital signs and core laboratory values, including observed LVEF;
- 10 other laboratory values, including N-terminal pro–B-type natriuretic peptide (NT-proBNP) and estimated glomerular filtration rate (eGFR);
- 35 echocardiographic measures: LV structure (7), LV function (4), diastolic function and left atrium (8), right ventricle (RV) and pulmonary circulation (7), and valves and aorta (9).

A secondary panel added 4 coded-record summaries: medications, healthcare use, held-out codes and a prognostic score.

**Leakage control.** A characteristic was masked (not evaluated) for a PS if it was the same quantity as a PS input, was derived from one, or correlated with one at |ρ| ≥ 0.80.

- For PS-Clinical, its 8 measured vitals and laboratory inputs and eGFR (derived from creatinine, age and sex) were masked.
- For the hdPS and AI-EHR, the 4 coded-record summaries were masked.
- A cell's mask was the union of the PS's and the added representation's masks.
- Each comparison used only characteristics observed and unmasked in both compared cells.



### Trial emulation analysis

**Estimates.** Emulated hazard ratios (HRs) were estimated with Cox proportional hazards models in the matched cohort, with robust variance clustered on matched pairs.

**Agreement metrics.** Following the RCT-DUPLICATE initiative,^5,18^ agreement with each RCT was assessed as:

- the Pearson correlation of emulated and RCT log HRs across trials;
- estimate agreement: the emulated HR within the RCT 95% CI;
- standardized difference agreement: the difference between emulated and RCT log HRs within 1.96 times its combined standard error;
- the absolute difference between emulated and RCT log HRs (|Δ log HR|).

**Benchmark-permutation test.** These metrics improve whenever estimates move toward the null. So every agreement result was accompanied by a benchmark-permutation test: RCT results were reassigned at random across trials 20,000 times, to assess whether a reduction in |Δ log HR| was specific to each trial's own RCT result (eMethods 6).

### Plasmode simulation

We used plasmode simulations,^19^ which retain each trial's real covariates, ECGs, coded histories and follow-up while simulating treatment and outcome with a known HR (0.80).

- **The confounder:** a measured physiological variable (LVEF, NT-proBNP, body mass index or eGFR) alone drove treatment and also affected the hazard.
- **Orientation:** LVEF and eGFR were oriented clinically (lower values increasing treatment and hazard), a post hoc choice disclosed in our previous report.
- **Withholding:** the confounder was withheld from every PS except an oracle PS that included it.
- **Design:** 107 trial–confounder combinations, 50 replicates of 80% subsamples, and the 9 non-null scenarios plus the null (eMethods 7).
- **Outcome:** the share of the confounder's bias removed by each arm.

[CHECK: the plasmode cells span 31 trials of the 38 emulated trials, not the 31-trial analysed set: they include ALLHAT, ASCOT-BPLA, DECLARE-TIMI 58, ONTARGET, REWIND and VALUE, and omit CANVAS, INSIGHT, LEADER, PROVE IT-TIMI 22, RE-LY and VALIANT. The re-run on the analysed set is PENDING (`pipeline.md` §8).]

### External validation

**MIMIC-IV.** We emulated 7 cardiovascular trials (PLATO, ARISTOTLE, ROCKET AF, TRANSFORM-HF, COMET, SOAP II and ELITE II), plus PEPTIC as a negative-control trial (RCT relative risk, 1.05). Each was an in-hospital-initiation, new-user, active-comparator design, with time zero at the first inpatient order of either study drug (eMethods 11).

- **The PS-CVD5 analog:** demographics plus the 5 diagnoses coded in earlier admissions.
- **AI-ECG:** as at Yale.
- **AI-EHR:** the same frozen CLMBR-T checkpoint applied to MIMIC-IV converted to its input format.
  - Its input was the history before the index admission time. Events of the index emergency department stay before admission were kept.
  - A first-run input that also read the index admission's laboratory and order stream before time zero was moved to a sensitivity analysis, because that stream overlaps in time with the held-out laboratory values. This decision was made after both results were seen and is disclosed.
- **hdPS:** rebuilt on the same pre-admission window. The original hdPS, which read the index stay, is a sensitivity analysis.
- **Held-out panel:** 26 laboratory, vital sign, ventilation and utilization characteristics. Utilization was masked for arms with AI-EHR or the hdPS, leaving 22.
- **CIs:** from 4,000 bootstrap resamples of trials.

**CHS.** Treatment initiation was emulated at the annual clinic visits (protocol locked before analysis; `docs/bdc/CHS_PROTOCOL.md`).

- **Time zero:** the first visit at which the new drug class was recorded (visit *k*). Neither class could be recorded at any earlier visit.
- **Baseline:** every PS covariate, held-out characteristic and the ECG was taken from the previous visit (*k*−1) or earlier.
- **Feasible emulations:** 5 met the ≥350 rule. Two planned emulations were infeasible under the same rule: a dihydropyridine-only sensitivity of emulation 1, and thiazide vs β-blocker with no RCT benchmark.


| #   | Emulation                                                          | Benchmark                                                         |
| --- | ------------------------------------------------------------------ | ----------------------------------------------------------------- |
| 1   | calcium-channel blocker vs thiazide                                | ALLHAT                                                            |
| 2   | angiotensin-converting enzyme inhibitor vs thiazide                | ALLHAT                                                            |
| 3   | angiotensin-converting enzyme inhibitor vs calcium-channel blocker | STOP-2; balance only, until the head-to-head estimate is verified |
| 5   | statin vs no statin                                                | PROSPER                                                           |
| 6   | aspirin vs no aspirin                                              | ASPREE                                                            |


Emulations 5 and 6 were sequential trials at each visit.

- **PS specifications:**
  - **PS-Base** (the PS-CVD5 analog): age, sex, Black race, hypertension, diabetes, coronary artery disease, AF, heart failure and visit.
  - **PS-Clinical:** adds blood pressure, body mass index, smoking and laboratory values.
  - **PS-Codes** (hdPS-like): the top 200 hospital diagnosis, procedure and medication-class codes.
- **ECG:** the visit *k*−1 ECG, encoded with the same BCL encoder, gave 32 principal components per emulation.
- **Held-out panel:** echocardiography (LV mass, wall thickness, LV function, left atrial dimension, E/A ratio), laboratory values, vital signs and functional measures.
- **Tests:** sign-flip tests across 4 comparator clusters.
- **Deviation:** after the first locked run, an independent code audit led to a corrected re-run. Eligibility exclusions were also evaluated with history up to time zero rather than visit *k*−1. That design change was made after results were seen and is disclosed (`pipeline.md` §9).
- **AI-EHR in CHS:** CLMBR-T was applied to pseudo-timelines built from CHS events, visits, medication classes mapped to representative RxNorm products, and hospital ICD-9 codes mapped to SNOMED. This was added after the locked results were seen and is exploratory. [PENDING: results.]

**Hidden-confounder benchmark in SPRINT (preliminary).** Inside the SPRINT trial (n = 8,815 with a baseline ECG), we induced confounding by RCT rejection sampling, following Keith et al.:^26^

- Participants were subsampled so that the probability of intensive treatment depended on a withheld baseline characteristic C (odds ratio 3 per SD in the primary scenario).
- The characteristics were eGFR, NT-proBNP, high-sensitivity troponin I, body mass index, urine albumin-to-creatinine ratio, Cornell voltage (positive control) and LDL cholesterol (negative control).
- We then estimated the effect with PS-Base (the PS-CVD5 analog), PS-Base + AI-ECG, PS-Base + permuted AI-ECG, a rich PS without C (± AI-ECG), and an oracle PS including C, using the same estimator.
- **Primary metric:** the share of the confounding gap between PS-Base and the oracle closed by adding AI-ECG, over 300 draws per scenario.

The protocol was locked before any ECG-adjusted estimate (`docs/bdc/FIG5_SPRINT_PROTOCOL.md`). [PRELIMINARY: 3 of 7 characteristics, 50 draws; the full run is PENDING. AI-EHR is not available in SPRINT.]

### Statistical analysis

**Unit and measures.** Trials were the unit of analysis. For each trial, balance was summarized as:

- the mean |SMD| over the characteristics observed in both compared arms;
- the proportion of characteristics with |SMD| < 0.1.

The primary measure was the relative reduction in mean |SMD|: 1 minus the ratio of the across-trial means with and without the added representation. Its 95% CIs came from 4,000 bootstrap resamples of trials (seed 20261001).

**Tests.** Paired differences were tested with exact sign-flip permutation tests across trials:

- one-sided for a representation against its base or its placebo;
- two-sided for head-to-head comparisons between PS specifications and for placebos against base.

**Robustness:**

- clustering of trials that shared a comparator (14 clusters);
- leave-one-trial-out analysis.

**Multiple testing.** The false discovery rate was controlled by the Benjamini–Hochberg method within families (balance, agreement), across contrasts and configurations.^24^ Domain-level results are exploratory.

**Descriptive grouping.** Trials were grouped by type of treatment decision:

- **Cardiac-physiology decisions:** rhythm control (AF-CHF, AFFIRM, EAST-AFNET 4, CABANA and RAFT-AF), and heart-failure and renin–angiotensin drug choice (PARADIGM-HF, ELITE II, TRANSFORM-HF, COMET, EMPEROR-Preserved and VALIANT).
- **Other decisions:** all remaining trials.

This grouping, and a blinded physiologic label (eMethods [CHECK]), were used descriptively, without tests of group differences.

**Sensitivity analyses:**

- the 32-trial set including PROTECT AF;
- all 37 feasible trials;
- framework v2.0 quality tiers and corrected cohort specifications;
- AI-EHR with 32 components;
- exclusion of index-day ECGs;
- a cross-validated PS penalty.

**Exploratory nature.** This study was exploratory, and several design choices were made after earlier results were known; they are listed in eTable [CHECK] (deviations log). All analyses are reported. Analyses were performed in Python 3.11 (eMethods 10).

## Results



### Trial selection and study population

**The 31 analysed trials** covered AF (11), diabetes (7), heart failure (5), hypertension (2), acute coronary syndromes or myocardial infarction (2) and other indications (4) (Table 1; Figure 1).

**Cohorts:**

- 211,054 patients with both an ECG and an AI-EHR representation, aggregated across trials (median, 5,080 per trial; range, 1,546–22,277);
- with PS-CVD5, 43,644 matched pairs (median, 1,062 per trial; range, 397–4,100), with 88.2% of the smaller treatment group matched on average;
- PS models including AI-EHR matched 80.2% (AI-EHR) and 78.8% (both) of the smaller group, vs 87.2% with AI-ECG.



### Held-out balance with the representations added to PS-CVD5

Adding either representation to PS-CVD5 improved balance on the 54 held-out characteristics, and adding both improved it most (Figure 2A–B). The mean |SMD| decreased from 0.129:


| Added to PS-CVD5 | Mean |SMD| | Relative reduction (95% CI) | Trials improved | q      |
| ---------------- | ---------- | --------------------------- | --------------- | ------ |
| AI-EHR           | 0.112      | 12.9% (7.6%–18.3%)          | 23 of 31        | < .001 |
| AI-ECG           | 0.117      | 8.7% (4.2%–13.5%)           | 20 of 31        | .004   |
| Both             | 0.110      | 14.6% (7.7%–21.1%)          | 23 of 31        | .002   |


- **Proportion balanced:** the share of characteristics with |SMD| < 0.1 increased from 53.9% to 59.4%, 57.3% and 60.9%, respectively.
- **Robustness:** each gain held when trials sharing a comparator were clustered (P ≤ .004).
- **Placebos:** permuted placebos did not improve balance (AI-EHR, 2.2%; 95% CI, −2.5% to 6.7%; AI-ECG, 0.4%; 95% CI, −3.5% to 4.3%). Each real representation beat its placebo (AI-EHR, 11.0%; 95% CI, 4.6%–16.7%; AI-ECG, 8.3%; 95% CI, 4.0%–12.7%).
- **Direct comparison:** AI-EHR and AI-ECG did not differ clearly in overall balance (4.7%; 95% CI, −1.2% to 9.6%; two-sided P = .13).
- **Adding one to the other:**
  - adding AI-EHR to PS-CVD5 + AI-ECG reduced imbalance by a further 6.6% (95% CI, −0.0% to 12.6%; P = .028);
  - adding AI-ECG to PS-CVD5 + AI-EHR reduced it by a further 2.0% (95% CI, −3.5% to 6.9%; P = .24).
- **AI-EHR with 32 rather than 64 components:** 11.3% (95% CI, 6.4%–16.3%).

**The two representations improved balance in different domains** (Figure 2B; exploratory).

- **AI-EHR:** gains were largest in vital signs and core laboratory values (23.1%; 95% CI, 15.2%–29.9%), other laboratory values (25.7%; 95% CI, 14.1%–34.7%), LV structure (16.9%) and valves and aorta (15.6%). Little changed in LV function (0.2%) or diastolic function (4.2%).
- **AI-ECG:** gains were concentrated in LV function (16.1%; 95% CI, 2.5%–28.6%), diastolic function and left atrial size (16.0%; 95% CI, 5.5%–24.7%) and LV structure (15.0%; 95% CI, 3.5%–25.3%).
- **Head to head:** AI-ECG balanced LV function (difference, −19.0%; 95% CI, −36.1% to −4.1%) and diastolic function (−14.1%; 95% CI, −25.8% to −2.2%) better than AI-EHR. AI-EHR balanced other laboratory values (20.5%; 95% CI, 8.2%–31.1%) and vital signs and core laboratory values (15.9%; 95% CI, 5.5%–24.3%) better than AI-ECG.
- **Together:** both reduced imbalance in vital signs and core laboratory values by 32.5% and in LV structure by 23.9%.
- **RV and pulmonary measures:** neither representation improved them.

**Gains with AI-ECG were concentrated in cardiac-physiology decisions** (Figure 2D; descriptive).

- In the 11 rhythm-control and heart-failure or renin–angiotensin drug-choice trials, the proportion of balanced characteristics increased in 10, by a mean of 9.9 percentage points.
- In the 20 other trials it increased in 9, by a mean of −0.3 points.
- Overall, 19 of 31 trials improved (mean, +3.3 points; P = .015).

[CHECK: add the same per-trial view for AI-EHR, which Figure 2D does not show.]

**Replication across configurations.** The gains replicated with a caliper of 0.1, 1:3 matching and overlap weighting, but not uniformly with IPTW or the gradient-boosted PS (eFigure [CHECK]). The relative reductions with AI-EHR, AI-ECG and both were:


| Configuration       | AI-EHR                        | AI-ECG                        | Both                          |
| ------------------- | ----------------------------- | ----------------------------- | ----------------------------- |
| Caliper 0.1         | 11.1%                         | 7.6%                          | 16.1%                         |
| 1:3 matching        | 14.1%                         | 6.2%                          | 13.6%                         |
| Overlap weighting   | 14.1%                         | 7.5%                          | 16.7%                         |
| IPTW                | 2.4% (95% CI, −8.8% to 10.8%) | 5.1% (95% CI, 1.6%–8.8%)      | 6.2% (95% CI, −0.6% to 13.0%) |
| Gradient-boosted PS | 6.8% (95% CI, 0.6%–13.0%)     | −1.5% (95% CI, −8.0% to 4.2%) | 12.6% (95% CI, 7.9%–17.5%)    |




### Balance across the propensity score ladder

The added value of both representations was largest with the sparsest PS and diminished as conventional covariates became richer (Figure 2C). Mean |SMD| with each PS alone was 0.141 (PS-Demo), 0.129 (PS-CVD5), 0.118 (PS-CVD10), 0.118 (PS-Clinical) and 0.114 (hdPS).


| PS          | + AI-EHR | + AI-ECG        | + both |
| ----------- | -------- | --------------- | ------ |
| PS-Demo     | 20.6%    | 10.6%           | 25.4%  |
| PS-CVD5     | 12.9%    | 8.7%            | 14.6%  |
| PS-CVD10    | 7.0%     | 3.8% (P = .095) | 6.9%   |
| PS-Clinical | 4.4%     | 3.3% (P = .079) | 3.4%   |
| hdPS        | 0.6%     | 7.1% (P = .015) | 8.5%   |


**On the hdPS**, which is built from the same coded record that AI-EHR reads:

- AI-EHR added nothing (0.6%; 95% CI, −7.0% to 7.4%), and it balanced worse than AI-ECG at that rung (−6.9%; 95% CI, −12.4% to −2.1%).
- AI-ECG still improved balance (7.1%; 95% CI, 0.7%–12.8%), although its gain at that rung was not clearly larger than that of the permuted AI-ECG (3.1%; 95% CI, −4.0% to 10.2%).

**PS-Flags.** Against PS-Flags, a PS of yes/no flags for every recorded diagnosis, PS-Demo + AI-EHR showed no detectable difference (0.7%; 95% CI, −5.5% to 6.8%; two-sided P = .81) (eFigure [CHECK]).

### Demographics plus AI representations vs investigator-built PS

A PS of demographics and the two representations, with no investigator-chosen diagnoses, laboratory values or code features, balanced the held-out characteristics better than any conventional PS (Figure 4). Mean |SMD| was:

- 0.143 unmatched;
- 0.129 with PS-CVD5, 0.118 with PS-Clinical (on the characteristics that are not its inputs) and 0.114 with the hdPS;
- 0.126 with PS-Demo + AI-ECG, 0.112 with PS-Demo + AI-EHR and 0.106 with PS-Demo + AI-ECG + AI-EHR.

**Demographics + AI-ECG + AI-EHR vs each conventional PS:**


| Compared with | Relative reduction (95% CI) | Trials   | Two-sided P |
| ------------- | --------------------------- | -------- | ----------- |
| PS-CVD5       | 17.8% (11.8%–23.6%)         | 27 of 31 | < .001      |
| hdPS          | 8.0% (1.9%–13.6%)           | 25 of 31 | .012        |
| PS-Clinical   | 7.0% (1.1%–12.7%)           |          | .033        |


**Each representation alone, on demographics:**

- **Demographics + AI-EHR** was 12.5% better than PS-CVD5 (95% CI, 6.3%–18.4%; P = .001) and comparable to the hdPS (2.0%; 95% CI, −4.4% to 8.0%; P = .53).
- **Demographics + AI-ECG** was comparable to PS-CVD5 (1.5%; 95% CI, −4.0% to 7.4%; P = .61) and worse than the hdPS (−10.2%; 95% CI, −19.7% to −1.5%; P = .03).

**Robustness of demographics + both vs PS-CVD5.** The advantage was robust under:

- a caliper of 0.1 (15.5%);
- 1:3 matching (17.3%);
- overlap weighting (16.4%);
- the 32- and 38-trial sets (about 17.7%).

It was weaker with the gradient-boosted PS (9.0%) and not significant with IPTW (5.8%; P = .086).

**Input count and retention.**

- **Input count did not explain the advantage:** demographics plus a permuted AI-EHR, with the same number of inputs, was 11.8% worse than PS-CVD5.
- **Retention:** the AI-EHR arms matched 79% to 81% of the smaller group, vs 88% for PS-CVD5. In the 12 trials with a retention loss of 5 percentage points or less, the advantage held (13.8%; 95% CI, 5.5%–22.9%; P = .006).
- **Fragility:** the advantages over the hdPS and PS-Clinical were sensitive to the configuration and to single trials, for example P = .067 vs the hdPS with a caliper of 0.1.



### Agreement with RCT results

The representations moved estimates closer to RCT results on average, but not toward each trial's own result (Figure 3).


| PS                             | Mean |Δ log HR| | Trials closer than PS-CVD5 | P                | Benchmark-permutation P |
| ------------------------------ | --------------- | -------------------------- | ---------------- | ----------------------- |
| PS-CVD5                        | 0.232           |                            |                  |                         |
| PS-CVD5 + AI-ECG               | 0.198           | 20 of 31                   | .035             | .56                     |
| PS-CVD5 + AI-EHR               | 0.169           | 18 of 31                   | .025             | .93                     |
| PS-CVD5 + both                 | 0.161           | 18 of 31                   | .018             | .97                     |
| Demographics + AI-ECG + AI-EHR | 0.164           |                            | .037 (two-sided) | .26 (two-sided)         |


- **Comparison with PS-Clinical:** demographics + AI-ECG + AI-EHR came about as close as PS-Clinical (0.171).
- **Placebos:** the permuted placebos did not change agreement (0.230 and 0.226).
- **Statistical agreement:** standardized-difference agreement rose from 74% of trials with PS-CVD5 (and with the hdPS) to 84% with demographics + AI-ECG + AI-EHR (PS-Clinical, 87%).
- **Correlation:** the correlation with RCT log HRs did not improve (0.55 vs 0.49).
- **Interpretation:** estimates with demographics + AI-ECG + AI-EHR were less dispersed than with PS-CVD5 (SD of log HRs, 0.22 vs 0.37) and less biased toward benefit (mean bias, −0.01 vs −0.07). Together with the benchmark-permutation results, this indicates that the gains reflect attenuation of extreme estimates rather than trial-specific correction.

**Two isolated trial-specific signals with AI-ECG**, both identified post hoc and treated as exploratory:

- with PS-CVD10 (|Δ log HR| 0.213 to 0.173; benchmark-permutation P < .001);
- with PS-Clinical (0.171 to 0.151; P = .003).

**By emulation quality (descriptive):**

- In the 14 excellent or good emulations, |Δ log HR| was 0.230 with PS-CVD5, 0.176 with AI-ECG, 0.149 with AI-EHR and 0.152 with both.
- In the 17 moderate emulations, it was 0.235, 0.217, 0.185 and 0.168.

[CHECK: false discovery rate control for the agreement family on the 31-trial set.]

### Plasmode simulation

Both representations removed part of the bias from a withheld physiological confounder when added to PS-CVD5, and neither approached adjustment for the confounder itself (eFigure [CHECK]).

**Overall.** PS-CVD5 alone removed 18.6% of the bias, compared with 2.4% for PS-Demo. Of the bias remaining after PS-CVD5:

- AI-EHR removed a further 22.6% (Monte Carlo SE, 0.3);
- AI-ECG removed 11.3% (0.3);
- both removed 29.5% (0.4);
- permuted AI-EHR removed 1.0% (0.4).

**By confounder,** the pattern followed what each representation can see:

- AI-ECG removed more of the bias from LVEF than AI-EHR (15.2% vs 8.4%).
- AI-EHR removed more for eGFR (35.5% vs 2.5%) and NT-proBNP (28.4% vs 15.1%).
- This matched how well each predicted the confounder in the real data. Cross-fitted R² for eGFR was 0.34 with AI-EHR vs 0.05 with AI-ECG; for LVEF, it was 0.19 vs 0.22.

**Best arm and coverage.** The best arm, PS-CVD5 + AI-ECG + AI-EHR, removed 42.6% of the bias, vs 93.7% for the oracle. Its CI coverage of the true effect was 76.9%, vs 94.4% for the oracle.

[CHECK: plasmode trial set; see Methods.]

### External validation in MIMIC-IV

**Population.** The 7 cardiovascular trials comprised 37,694 patient–index records (Figure 6A).

**Balance, PS-CVD5 analog** (relative reductions over 22 characteristics with AI-EHR, 26 otherwise):


| Added to PS-CVD5 | Relative reduction (95% CI) | Trials lower | P    |
| ---------------- | --------------------------- | ------------ | ---- |
| AI-EHR           | 7.7% (3.0%–14.0%)           | 6 of 7       | .023 |
| AI-ECG           | 6.6% (2.4%–13.1%)           | 6 of 7       | .016 |
| Both             | 18.6% (12.5%–26.7%)         | 7 of 7       | .008 |


- **AI-ECG on top of AI-EHR:** a further 11.9% (95% CI, 6.9%–16.8%; 7 of 7).
- **Placebos:** the permuted placebos did not improve balance (AI-ECG, −3.1%; AI-EHR, −1.3%).
- **Why AI-EHR gained less than at Yale:** MIMIC-IV has no outpatient diagnoses or prescriptions, so the coded history before admission is thin (median, 59 in-vocabulary events per patient).

**On the hdPS built from the same pre-admission window:**

- the hdPS improved on PS-CVD5 by 11.7% (95% CI, 7.1%–16.8%);
- AI-ECG still added 10.8% (95% CI, 7.2%–15.7%; 7 of 7; P = .008);
- AI-EHR added nothing (−1.2%; 95% CI, −7.8% to 5.8%);
- on demographics, either representation brought balance to about the level of this hdPS (AI-ECG, −5.4%; AI-EHR, −5.6%), and both together were slightly better (5.8%; 95% CI, 0.2%–10.9%).

**Agreement:** estimates moved closer to RCT results (|Δ log HR| 0.344 with PS-CVD5, 0.326 with AI-ECG, 0.278 with AI-EHR and 0.240 with both), but no change was trial-specific (benchmark-permutation P ≥ .57).

**Negative control (PEPTIC):** both representations moved the PS-CVD5 estimate toward the null, from HR 1.51 (95% CI, 1.35–1.69) to:

- 1.39 (95% CI, 1.24–1.55) with AI-ECG;
- 1.28 (95% CI, 1.14–1.43) with AI-EHR;
- 1.21 (95% CI, 1.08–1.35) with both.

The permuted placebos did not move it (1.60 and 1.61).

### External validation in the Cardiovascular Health Study

**Population.** Five emulations were feasible (smaller group with an ECG at the prior visit, 404 to 1,143 in the first locked build) (Figure 6B). [CHECK: sizes after the audit re-run; emulation 2 lost ACE-inhibitor starters with heart failure in the gap year (498 → 382 starters).] The ECG encoder transferred to CHS ECGs (linear probe for sex, AUC 0.899; echocardiographic LV mass, R² 0.33).

**Balance with AI-ECG added to PS-Base.** Mean held-out |SMD| fell by 9.5% on average across emulations, but the direction varied:


| Emulation                                   | Relative reduction |
| ------------------------------------------- | ------------------ |
| 1. Calcium-channel blocker vs thiazide      | 20.3%              |
| 3. ACE inhibitor vs calcium-channel blocker | 16.0%              |
| 5. Statin initiation                        | 12.2%              |
| 2. ACE inhibitor vs thiazide                | 1.1%               |
| 6. Aspirin initiation                       | −15.5%             |


- **Test:** with 4 comparator clusters, the smallest attainable sign-flip P was .0625, and the observed P was .25.
- **Placebo:** the permuted AI-ECG gave −0.6%.
- **Echocardiography:** mean echocardiographic |SMD| fell from 0.081 to 0.058, and imbalance was lower in 20 of 30 echocardiographic item–emulation cells. The matched |SMD| values of about 0.03 to 0.09 are close to the chance level for about 400 pairs.
- **Richer PS:** with PS-Clinical and PS-Codes, AI-ECG added 4.0% and 1.6%.

**AI-EHR:** [PENDING: CLMBR-T on CHS pseudo-timelines; exploratory.] An exploratory, unsupervised code representation fitted in CHS reduced imbalance by 13.1% but did not improve on PS-Codes built from the same codes (1.2%) (eTable [CHECK]).

**Hazard ratios** (PS-Base, then + AI-ECG) were:

- emulation 1: 1.05 and 1.11 (ALLHAT, 0.98);
- emulation 2: 1.25 and 1.06 (ALLHAT, 0.99);
- emulation 5: 0.76 and 1.01 (PROSPER, 0.85);
- emulation 6: 0.96 and 0.97 (ASPREE, 0.95).



### Hidden-confounder benchmark in SPRINT [PRELIMINARY]

[PRELIMINARY: 50 draws, odds ratio 3, primary outcome, 3 of the 7 withheld characteristics; full run PENDING.]

With confounding induced inside SPRINT by a withheld characteristic (Figure 5), adding AI-ECG to PS-Base closed:

- 19.0% (95% CI, 14.1%–23.6%) of the confounding gap for NT-proBNP;
- 25.5% (95% CI, 11.6%–38.4%) for eGFR;
- 10.6% (95% CI, −9.9% to 28.1%) for Cornell voltage, the positive control.

The permuted AI-ECG closed 2.4%, 4.6% and 0.8%.

- **Prediction of C:** AI-ECG predicted NT-proBNP beyond PS-Base (partial R², 0.12) but barely predicted eGFR (0.01). So the eGFR result is not explained by balance on eGFR, and needs the full run.
- **Positive control:** for Cornell voltage, balance on the withheld characteristic improved by 55%, but the induced bias was small and the estimate imprecise.



## Tables and Figures

**Table 1. Target trial specification (PICOT) and emulation quality for the 38 emulated trials**


| Area         | Trial             | Population                                                  | Intervention              | Comparator                    | Outcome (RCT primary endpoint)                                       | Time (mo) | RCT estimate (CI)                                     | Emulation quality (points) | Analysed (31)                                     | Cardiac-physiology decision |
| ------------ | ----------------- | ----------------------------------------------------------- | ------------------------- | ----------------------------- | -------------------------------------------------------------------- | --------- | ----------------------------------------------------- | -------------------------- | ------------------------------------------------- | --------------------------- |
| AF           | ARISTOTLE         | AF                                                          | apixaban                  | warfarin                      | stroke or systemic embolism                                          | 22        | 0.79 (0.66–0.95)                                      | Excellent (0)              | Yes                                               | No                          |
| AF           | ROCKET-AF         | AF                                                          | rivaroxaban               | warfarin                      | stroke or systemic embolism                                          | 23        | 0.88 (0.74–1.03)                                      | Excellent (0)              | Yes                                               | No                          |
| AF           | RE-LY             | AF                                                          | dabigatran                | warfarin                      | stroke or systemic embolism                                          | 24        | 0.66 (0.53–0.82) [RR]                                 | Excellent (0)              | Yes                                               | No                          |
| AF           | EAST-AFNET 4      | Early AF (diagnosis ≤1 y) on rate control                   | rhythm-control drug added | continued rate control        | CV death, stroke, HF or ACS hospitalisation                          | 61        | 0.79 (0.66–0.94) [96% CI]                             | Moderate (3)               | Yes                                               | Yes                         |
| AF           | CABANA            | AF                                                          | catheter ablation         | antiarrhythmic drug           | death, disabling stroke, serious bleeding or cardiac arrest          | 49        | 0.86 (0.65–1.15)                                      | Moderate (3)               | Yes                                               | Yes                         |
| AF           | AFFIRM            | AF on rate control, age ≥65                                 | rhythm-control drug added | continued rate control        | all-cause death                                                      | 42        | 1.15 (0.99–1.34)                                      | Good (1)                   | Yes                                               | Yes                         |
| AF           | AF-CHF            | AF with HF on rate control                                  | rhythm-control drug added | continued rate control        | CV death                                                             | 37        | 1.06 (0.86–1.30)                                      | Good (2)                   | Yes                                               | Yes                         |
| AF           | FRAIL-AF          | AF on warfarin, age ≥75                                     | switch to DOAC            | warfarin                      | major or clinically relevant non-major bleeding                      | 12        | 1.69 (1.23–2.32) [cause-specific HR]                  | Moderate (2)               | Yes                                               | No                          |
| AF           | LAAOS III         | AF undergoing cardiac surgery                               | surgical LAA occlusion    | surgery without LAA occlusion | ischaemic stroke or systemic embolism                                | 46        | 0.67 (0.53–0.85)                                      | Good (2)                   | Yes                                               | No                          |
| AF           | PROTECT AF        | AF on warfarin with ≥1 stroke risk factor                   | percutaneous LAA closure  | warfarin                      | stroke, CV death or systemic embolism                                | 18        | 0.62 (0.35–1.25) [rate ratio] [95% credible interval] | Good (1)                   | No: excluded at feasibility (smaller group < 350) | No                          |
| AF           | RAFT-AF           | AF with HF on rate control                                  | catheter ablation         | continued rate control        | all-cause death or HF event                                          | 36        | 0.71 (0.49–1.03)                                      | Good (2)                   | Yes                                               | Yes                         |
| AF           | ACTIVE W          | AF with ≥1 stroke risk factor, age ≥55                      | clopidogrel               | warfarin                      | stroke, non-CNS systemic embolism, MI or vascular death              | 15        | 1.44 (1.18–1.76) [RR]                                 | Moderate (3)               | Yes                                               | No                          |
| HF           | COMET             | HF                                                          | carvedilol                | metoprolol                    | all-cause mortality                                                  | 58        | 0.83 (0.74–0.93)                                      | Good (1)                   | Yes                                               | Yes                         |
| HF           | PARADIGM-HF       | HF on ACEi/ARB (switch at time zero)                        | sacubitril-valsartan      | ACEi                          | CV death or first HF hospitalisation                                 | 27        | 0.80 (0.73–0.87)                                      | Moderate (3)               | Yes                                               | Yes                         |
| HF           | TRANSFORM-HF      | HF hospitalisation (discharge within 30 d)                  | torsemide                 | furosemide                    | all-cause mortality                                                  | 12        | 1.02 (0.89–1.18)                                      | Moderate (2)               | Yes                                               | Yes                         |
| HF           | ELITE II          | HF, age ≥60                                                 | ARB                       | ACEi                          | all-cause mortality                                                  | 18        | 1.13 (0.95–1.35) [95.7% CI]                           | Good (1)                   | Yes                                               | Yes                         |
| HF           | EMPEROR-Preserved | HF with T2D                                                 | SGLT2i                    | DPP-4i (placebo proxy)        | CV death or HF hospitalisation                                       | 26        | 0.79 (0.69–0.90)                                      | Moderate (3)               | Yes                                               | Yes                         |
| Hypertension | LIFE              | Hypertension with ECG-LVH, age 55–80                        | ARB                       | β-blocker                     | CV death, MI or stroke                                               | 58        | 0.87 (0.77–0.98)                                      | Moderate (3)               | Yes                                               | No                          |
| Hypertension | ALLHAT            | Hypertension, age ≥55                                       | amlodipine                | thiazide                      | fatal CHD or nonfatal MI                                             | 59        | 0.98 (0.90–1.07) [RR]                                 | Limited (4)                | No: limited                                       | No                          |
| Hypertension | VALUE             | Hypertension, age ≥50                                       | ARB                       | amlodipine                    | cardiac morbidity and mortality composite                            | 50        | 1.04 (0.94–1.15)                                      | Limited (4)                | No: limited                                       | No                          |
| Hypertension | ASCOT-BPLA        | Hypertension, age 40–79                                     | amlodipine                | β-blocker                     | nonfatal MI and fatal CHD                                            | 66        | 0.90 (0.79–1.02)                                      | Limited (4)                | No: limited                                       | No                          |
| Hypertension | INSIGHT           | High-risk hypertension, age ≥55                             | nifedipine                | thiazide                      | CV death, MI, HF or stroke                                           | 42        | 1.10 (0.91–1.34) [RR]                                 | Good (2)                   | Yes                                               | No                          |
| ACS / MI     | PLATO             | ACS within 30 d                                             | ticagrelor                | clopidogrel                   | vascular death, MI or stroke                                         | 12        | 0.84 (0.77–0.92)                                      | Good (2)                   | Yes                                               | No                          |
| ACS / MI     | VALIANT           | MI within 30 d                                              | ARB                       | ACEi                          | all-cause death                                                      | 25        | 1.00 (0.90–1.11) [97.5% CI]                           | Good (2)                   | Yes                                               | Yes                         |
| Diabetes     | EMPA-REG OUTCOME  | T2D with established CVD                                    | SGLT2i                    | DPP-4i (placebo proxy)        | 3-point MACE                                                         | 37        | 0.86 (0.74–0.99) [95.02% CI]                          | Moderate (3)               | Yes                                               | No                          |
| Diabetes     | CAROLINA          | T2D                                                         | linagliptin               | glimepiride                   | 3-point MACE                                                         | 76        | 0.98 (0.84–1.14) [95.47% CI]                          | Good (2)                   | Yes                                               | No                          |
| Diabetes     | LEADER            | T2D with CVD, age ≥50                                       | liraglutide               | DPP-4i (placebo proxy)        | CV death, nonfatal MI or nonfatal stroke                             | 46        | 0.87 (0.78–0.97)                                      | Moderate (3)               | Yes                                               | No                          |
| Diabetes     | SUSTAIN-6         | T2D with CVD, age ≥50                                       | semaglutide               | DPP-4i (placebo proxy)        | CV death, nonfatal MI or nonfatal stroke                             | 25        | 0.74 (0.58–0.95)                                      | Moderate (3)               | Yes                                               | No                          |
| Diabetes     | REWIND            | T2D, age ≥50                                                | dulaglutide               | DPP-4i (placebo proxy)        | nonfatal MI, nonfatal stroke or CV death (incl. unknown causes)      | 65        | 0.88 (0.79–0.99)                                      | Limited (4)                | No: limited                                       | No                          |
| Diabetes     | DECLARE-TIMI 58   | T2D, age ≥40                                                | dapagliflozin             | DPP-4i (placebo proxy)        | CV death or HF hospitalisation                                       | 50        | 0.83 (0.73–0.95)                                      | Limited (4)                | No: limited                                       | No                          |
| Diabetes     | CANVAS Program    | T2D, age ≥30                                                | canagliflozin             | DPP-4i (placebo proxy)        | CV death, nonfatal MI or nonfatal stroke                             | 43        | 0.86 (0.75–0.97)                                      | Moderate (3)               | Yes                                               | No                          |
| Diabetes     | TECOS             | T2D with CVD, age ≥50                                       | sitagliptin               | sulfonylurea (placebo proxy)  | CV death, nonfatal MI, nonfatal stroke or UA hospitalisation         | 36        | 0.98 (0.88–1.09)                                      | Moderate (3)               | Yes                                               | No                          |
| Diabetes     | CARMELINA         | T2D with kidney disease                                     | linagliptin               | sulfonylurea (placebo proxy)  | CV death, nonfatal MI or nonfatal stroke                             | 26        | 1.02 (0.89–1.17)                                      | Moderate (3)               | Yes                                               | No                          |
| Other        | ONTARGET          | Established vascular disease or high-risk diabetes, age ≥55 | ARB                       | ACEi                          | CV death, MI, stroke or HF hospitalisation                           | 56        | 1.01 (0.94–1.09) [RR]                                 | Limited (4)                | No: limited                                       | No                          |
| Other        | PRECISION         | Arthritis with CV risk                                      | celecoxib                 | naproxen                      | CV death (incl. haemorrhagic), nonfatal MI or nonfatal stroke (APTC) | 34        | 0.93 (0.76–1.13)                                      | Good (2)                   | Yes                                               | No                          |
| Other        | AMPLIFY           | Acute VTE                                                   | apixaban                  | warfarin                      | recurrent symptomatic VTE or VTE-related death                       | 6         | 0.84 (0.60–1.18) [RR]                                 | Moderate (2)               | Yes                                               | No                          |
| Other        | LODESTAR          | Coronary artery disease                                     | rosuvastatin              | atorvastatin                  | 3-y death, MI, stroke or any coronary revascularisation              | 36        | 1.06 (0.86–1.30)                                      | Moderate (2)               | Yes                                               | No                          |
| Other        | PROVE IT-TIMI 22  | ACS within 30 d                                             | atorvastatin              | pravastatin                   | death, MI, UA rehospitalisation, revascularisation >= 30 d or stroke | 24        | 0.84 (0.74–0.95)                                      | Moderate (3)               | Yes                                               | No                          |


*Abbreviations:*

- ACEi, angiotensin-converting enzyme inhibitor; ARB, angiotensin receptor blocker;
- ACS, acute coronary syndrome; AF, atrial fibrillation; CHD, coronary heart disease; CV, cardiovascular; CVD, cardiovascular disease; HF, heart failure; MI, myocardial infarction; MACE, major adverse cardiovascular events; UA, unstable angina; VTE, venous thromboembolism;
- DOAC, direct oral anticoagulant; DPP-4i, dipeptidyl peptidase-4 inhibitor; SGLT2i, sodium-glucose cotransporter-2 inhibitor; LAA, left atrial appendage; LVH, left ventricular hypertrophy; T2D, type 2 diabetes.

*Notes:*

- RCT estimates are hazard ratios unless indicated; intervals are 95% CIs unless indicated (PROTECT AF, Bayesian 95% credible interval). ROCKET-AF is the intention-to-treat estimate.
- Time is the trial-matched follow-up horizon.
- "Placebo proxy" marks placebo-controlled trials emulated with an active comparator.
- **Emulation quality** is the adjudicated four-tier rating from design information, with total design points in parentheses (eMethods 3). Limited emulations were excluded.
- **PROTECT AF** met the original feasibility rule (≥300) but not the revised rule (≥350); it is in the 32-trial sensitivity set.
- **Cardiac-physiology decision** is the descriptive grouping used in Figure 2D (rhythm control; heart-failure and renin–angiotensin drug choice). The blinded physiologic labels are in eTable [CHECK].
- The emulated outcome omitted components that could not be ascertained from EHR data in LODESTAR and PROVE IT-TIMI 22 (coronary revascularization), AMPLIFY (VTE-related death), FRAIL-AF (clinically relevant non-major bleeding) and CABANA (disabling stroke) (eTable 1).



[CHECK: Table 1 is copied from paper2.md, which follows the committed `docs/paper/table1_picot.md`. The user has uncommitted edits to `table1_picot.md`; merge them before submission.]

**Figure 1. Study design (LATENT-RCT).** Trial flow: 99 candidate RCTs → 37 feasible → 31 analysed. Representations: AI-EHR (CLMBR-T, coded history, 64 principal components) and AI-ECG (BCL ECG encoder, 32 principal components), added to a ladder of conventional PS specifications. Endpoints: balance on 54 held-out characteristics, and agreement with RCT results. Validation cohorts: MIMIC-IV, CHS and SPRINT. *(docs/presentation/figures/latent_rct_overview.png)* [CHECK: update the validation cohorts to MIMIC-IV, CHS and SPRINT. The current figure shows All of Us and UK Biobank as planned.]

**Figure 2. Held-out covariate balance (31 trials).**

- A, Love plot of the 54 held-out characteristics (median |SMD| across trials): unmatched, PS-CVD5, PS-CVD5 + AI-ECG.
- B, Mean |SMD| by domain for the same arms.
- C, The PS ladder (PS-Demo, PS-CVD5, PS-CVD10, PS-Clinical, hdPS) with AI-ECG, AI-EHR or both added.
- D, Per-trial change in the proportion of characteristics with |SMD| < 0.1 with AI-ECG added to PS-CVD5, coloured by cardiac-physiology decision (descriptive grouping).

*(docs/paper/figures_latent/figure2_covariate_balance.png)* [CHECK: with AI-EHR in the headline, panels A and B should add PS-CVD5 + AI-EHR and PS-CVD5 + both; figure update PENDING.]

**Figure 3. Agreement of emulated and RCT results (31 trials).**

- A, Emulated vs RCT hazard ratios with PS-CVD5 and PS-CVD5 + AI-ECG.
- B, Mean |Δ log HR| across the PS ladder with AI-ECG, AI-EHR or both added.
- C, Mean |Δ log HR| by emulation quality (PS-CVD5).

Lower values are closer to the RCT. *(docs/paper/figures_latent/figure3_rct_agreement.png)* [CHECK: consider PS-CVD5 + AI-EHR / + both in panel A.]

**Figure 4. Demographics plus AI representations vs investigator-built PS (31 trials).**

- A, Love plot (unmatched, PS-CVD5, demographics + AI-ECG, demographics + AI-ECG + AI-EHR).
- B, Mean |SMD| for unmatched, PS-CVD5, hdPS, PS-Clinical and the demographics + AI arms, with paired contrasts vs PS-CVD5 and vs hdPS.
- C, Mean |Δ log HR|.
- D, Standardized-difference agreement.

*(draft: audits/claude-fig4-standalone-20261014/figure4_draft_v4.png; spec: docs/queue/figure4.md; deck version: lab deck slide 9 panel D)* [PENDING: build `scripts/figures/make_figure4_standalone.py`; consider adding demographics + AI-EHR as its own bar.]

**Figure 5. Hidden-confounder benchmark in SPRINT [PRELIMINARY].** Share of the confounding gap between PS-Base and the oracle closed by adding AI-ECG (and by the permuted AI-ECG), for each withheld characteristic. [PENDING: full run, 7 characteristics × 3 odds ratios × 300 draws.]

**Figure 6. External validation.**

- A, MIMIC-IV: balance by domain (PS-CVD5, hdPS on the AI-EHR window, and the AI arms on each), and agreement. *(docs/paper/figures_latent/figure_mimic_main.png)*
- B, CHS: balance per emulation with AI-ECG (and AI-EHR, PENDING).

[PENDING: CHS panel.]

**Supplementary materials** [CHECK: the paper 3 supplement is not yet assembled; eMethods 1–11 are currently in supplement.md]:

- **eFigures:**
  - plasmode;
  - every contrast in every configuration;
  - PS-Flags and retention sensitivity analyses;
  - the 58-item panel;
  - Figure 2D's other groupings (clinical area, decision type, blinded physiologic label).
- **eTables:**
  - 32-trial and 37-trial sensitivity sets;
  - framework v2.0 tiers and corrected cohorts;
  - index-day ECGs;
  - cross-validated penalty;
  - MIMIC-IV first-run AI-EHR input and v20 hdPS;
  - CHS per-emulation results and the code audit;
  - the deviations log.



## Discussion

In LATENT-RCT, foundation-model representations of routine EHR and ECG data improved confounding control in 31 emulations of cardiovascular RCTs.

- Added to a PS of demographics and five diagnoses, the EHR representation reduced held-out imbalance by 13% and the ECG representation by 9%, with no gain from permuted placebos.
- Together, on demographics alone, they balanced vital signs, laboratory values and echocardiographic measures better than PS-CVD5, and modestly better than a high-dimensional PS and a clinical PS with measured covariates.
- These results replicated in a second health system.

The practical implication is that a reusable, pretrained summary of the record can stand in for much of the study-specific covariate engineering that trial emulations currently require.

The two representations captured different information, and the comparisons that equalize information show where each one's value lies.

**AI-EHR captures the coded record.** It reads only codes, and its gains were in laboratory values and vital signs. Its plasmode advantage was for eGFR and NT-proBNP, quantities that diagnoses of kidney and heart disease and the tests ordered can stand in for. When the comparator PS was built from the same coded record, it added nothing:

- the hdPS at Yale;
- the hdPS on the same pre-admission window in MIMIC-IV;
- the code-based PS in CHS;
- the diagnosis-flag PS.

Its contribution is therefore efficiency rather than new information: the coded record's content without feature engineering, code selection or study-specific validation, from a model applied unchanged across health systems.

**AI-ECG adds physiology that codes do not record.** Its gains were in echocardiographic LV function, diastolic function and LV structure, and in trials in which treatment choice depends on cardiac physiology, such as rhythm control and heart-failure drug choice. Its plasmode advantage was for LVEF. It was the only representation that still improved balance on top of a code-based hdPS: 7.1% at Yale, where the gain was not clearly larger than its placebo's, and 10.8% in MIMIC-IV.

The representations were complementary, and they were most useful together and when conventional adjustment was sparse.

**Agreement with RCT results did not distinguish the representations from attenuation.** Every arm with a representation moved estimates closer to RCT results on average, but reassigning RCT results across trials gave reductions as large. The estimates became less dispersed rather than more correlated with each trial's result. Balance on measured characteristics and agreement with RCTs are distinct targets, and improving the first does not establish that the second will follow. The differences that remain between emulations and their RCTs more likely reflect design, populations and outcome definitions than residual confounding that a representation could fix.

**External validation supported the balance findings, with limits:**

- **MIMIC-IV:** the combined gain was larger than at Yale, and the ECG added on top of the coded-record PS in every trial. The EHR representation's gain was smaller, consistent with the thinner prior record of an inpatient database.
- **CHS:** a community cohort with systematic echocardiography. The ECG improved echocardiographic balance on average, but its effect varied between emulations, and five emulations cannot establish it.
- **SPRINT [PRELIMINARY]:** the hidden-confounder benchmark inside a randomized trial suggests that the ECG closes part of the gap from withheld NT-proBNP, consistent with the plasmode results. The full run will establish its size and its limits.

**Limitations.**

- **Exploratory study.** Several design choices were made after earlier results were known, and they are disclosed: the primary PS, the revised feasibility size rule, the trial set and cohort version, and the MIMIC-IV AI-EHR input window.
- **Balance and exchangeability.** Better balance on observed characteristics does not establish exchangeability, particularly when those characteristics are measured selectively. Several held-out characteristics have coded proxies that AI-EHR and the hdPS can see.
- **Retention.** PS models with AI-EHR matched about 8 percentage points less of the smaller treatment group, so balance was assessed in somewhat different populations. The gains held in trials with little loss of retention and with overlap weighting.
- **IPTW and the gradient-boosted PS.** The gains were weaker or lost under IPTW, plausibly reflecting extreme weights from near-separation of rich PS models. AI-ECG's gain was lost with the gradient-boosted PS.
- **Benchmarks.** RCT estimates are imperfect benchmarks when populations, treatment implementation, follow-up or outcomes differ, and several emulations used placebo-proxy comparators.
- **Simulations.** The plasmode imposed selected mechanisms with a post hoc orientation, and coverage was below nominal for every arm without the confounder.
- **Model input.** AI-EHR was truncated to the most recent 4,096 tokens and applied without fine-tuning. In CHS, it was applied to pseudo-timelines unlike its training data.
- **Validation cohorts.** The validation cohorts were small: 7 trials in MIMIC-IV and 5 emulations in CHS.
- **Cardiac-physiology grouping.** It was defined descriptively after the per-trial results were seen.

**Conclusion.** Foundation-model representations of the EHR and the ECG improved held-out covariate balance in target trial emulations and, together, matched or exceeded investigator-built PS specifications without feature engineering. The EHR representation recovered information contained in the coded record; the ECG added physiological information the record lacks. Neither produced trial-specific agreement with RCT results. Learned representations are most useful as a reusable foundation for adjustment, especially where measured physiology is sparse. They do not substitute for measuring key confounders or for careful emulation design.

## References

*References 1–25 follow paper2.md, including the [PI] placeholders of paper.md. New references are marked [NEW]. Renumber in order of first citation before submission.*

1. Hernán MA, Robins JM. *Causal Inference: What If.* Boca Raton: Chapman & Hall/CRC; 2020.
2. Sherman RE, Anderson SA, Dal Pan GJ, et al. Real-world evidence — what is it and what can it tell us? *N Engl J Med.* 2016;375:2293–2297.
3. Hernán MA, Robins JM. Using big data to emulate a target trial when a randomized trial is not available. *Am J Epidemiol.* 2016;183:758–764.
4. Franklin JM, Patorno E, Desai RJ, et al. Emulating randomized clinical trials with nonrandomized real-world evidence studies: first results from the RCT DUPLICATE initiative. *Circulation.* 2021;143:1002–1013.
5. Wang SV, Schneeweiss S; RCT-DUPLICATE Initiative. Emulation of randomized clinical trials with nonrandomized database analyses: results of 32 clinical trials. *JAMA.* 2023;329:1376–1385.
6. [PI: reference cited for claims data recording diagnoses, procedures and prescriptions consistently]
7. [PI: reference cited for EHR data being actionable for site-specific evidence generation]
8. Haneuse S, Arterburn D, Daniels MJ. Assessing missing data assumptions in EHR-based studies: a complex and underappreciated task. *JAMA Netw Open.* 2021;4:e210184.
9. [PI: reference cited for the ECG being inexpensive and routinely acquired]
10. Attia ZI, Kapa S, Lopez-Jimenez F, et al. Screening for cardiac contractile dysfunction using an artificial intelligence–enabled electrocardiogram. *Nat Med.* 2019;25:70–74.
11. Dhingra LS, Aminorroaya A, Sangha V, et al. Ensemble deep learning algorithm for structural heart disease screening using electrocardiographic images: PRESENT SHD. *J Am Coll Cardiol.* 2025;85:1302–1313.
12. Dhingra LS, Aminorroaya A, Sangha V, et al. Heart failure risk stratification using artificial intelligence applied to electrocardiogram images: a multinational study. *Eur Heart J.* 2025;46(11):1044–1053.
13. Sangha V, Khunte A, Holste G, Mortazavi BJ, Wang Z, Oikonomou EK, Khera R. Biometric contrastive learning for data-efficient deep learning from electrocardiographic images. *J Am Med Inform Assoc.* 2024;31(4):855–865.
14. Johnson AEW, Bulgarelli L, Shen L, et al. MIMIC-IV, a freely accessible electronic health record dataset. *Sci Data.* 2023;10:1.
15. Cashin AG, Hansford HJ, Hernán MA, et al. Transparent reporting of observational studies emulating a target trial: the TARGET statement. *JAMA.* 2025;334(12):1084–1093.
16. Schneeweiss S, Rassen JA, Glynn RJ, Avorn J, Mogun H, Brookhart MA. High-dimensional propensity score adjustment in studies of treatment effects using health care claims data. *Epidemiology.* 2009;20:512–522.
17. Austin PC. Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples. *Stat Med.* 2009;28:3083–3107.
18. Heyard R, Held L, Schneeweiss S, Wang SV. Design differences and variation in results between randomised trials and non-randomised emulations: meta-analysis of RCT-DUPLICATE data. *BMJ Med.* 2024;3:e000709.
19. Franklin JM, Schneeweiss S, Polinski JM, Rassen JA. Plasmode simulation for the evaluation of pharmacoepidemiologic methods in complex healthcare databases. *Comput Stat Data Anal.* 2014;72:219–226.
20. Morris TP, White IR, Crowther MJ. Using simulation studies to evaluate statistical methods. *Stat Med.* 2019;38:2074–2102.
21. Gow B, Pollard T, Nathanson LA, et al. MIMIC-IV-ECG: diagnostic electrocardiogram matched subset (version 1.0). PhysioNet. 2023.
22. Wornow M, Thapa R, Steinberg E, Fries JA, Shah NH. EHRSHOT: an EHR benchmark for few-shot evaluation of foundation models. *Adv Neural Inf Process Syst.* 2023;36.
23. Steinberg E, Jung K, Fries JA, Corbin CK, Pfohl SR, Shah NH. Language models are an effective representation learning technique for electronic health record data. *J Biomed Inform.* 2021;113:103637.
24. Benjamini Y, Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *J R Stat Soc Series B Stat Methodol.* 1995;57:289–300. [CHECK]
25. Li F, Morgan KL, Zaslavsky AM. Balancing covariates via propensity score weighting. *J Am Stat Assoc.* 2018;113:390–400. [CHECK]
26. [NEW] Keith K, et al. RCT rejection sampling for causal estimation evaluation. *Trans Mach Learn Res.* 2023. [CHECK: full citation]
27. [NEW] Fried LP, Borhani NO, Enright P, et al. The Cardiovascular Health Study: design and rationale. *Ann Epidemiol.* 1991;1:263–276. [CHECK]
28. [NEW] SPRINT Research Group. A randomized trial of intensive versus standard blood-pressure control. *N Engl J Med.* 2015;373:2103–2116. [CHECK]



## Draft notes (remove before submission)



### What changed from [paper2.md](http://paper2.md)

- **Framing.** The paper is now about foundation-model representations as a replacement for, and supplement to, investigator-built covariates. AI-EHR and the combination are in the headline (user decision, 2026-10-19). The ECG is presented as the source of the physiological information that codes lack. paper2.md's central PS-Flags head-to-head moves to the supplement and is cited as an equal-information comparison.
- **Wording.** "AI-EHR" means CLMBR-T, which reads coded (structured) data. It is never called "unstructured". The waveform ECG is the unstructured input.
- **Trial set:** 31 trials (≥350 rule; PROTECT AF removed), version 1 cohorts, v19 tiers. The 32-trial set is a sensitivity.
- **PS ladder:** PS-Demo → PS-CVD5 → PS-CVD10 → PS-Clinical (no LVEF, 5-draw MI) → hdPS. PS-Flags is supplement only.
- **Masking:** the leakage-corrected masks of `pipeline.md` §6.
- **Cohorts:** YNHHS (development), MIMIC-IV (AI-EHR added; hdPS on the AI-EHR window), CHS (locked protocol; AI-EHR PENDING) and SPRINT (Figure 5, PRELIMINARY). All of Us and UK Biobank are not in this paper.
- **Figure 2D:** cardiac-physiology grouping (descriptive). The blinded labels move to the supplement.
- **Label analyses:** the tested label analyses of paper2 (label-permutation P values) are not carried over. They were on 32 trials and did not survive FDR control.



- **Order of the representations (user decision, 2026-10-19):** the ECG comes first and the EHR second, in the title and in every section. Apply this when each section is revised (the Abstract, Methods, Results, Figures and Discussion still list AI-EHR first in places).

### Still to do before the paper is complete

1. `pipeline.md` **rewrite.** Its header, §2 and §3 still say "ECG only", "29 trials" and "38 emulated". Rewrite it as one clean lock that matches this file: CLMBR-T in the headline, 31 trials, the cohorts above.
2. **Figures:**
  - add the AI-EHR arms to Figure 2A–B;
  - build Figure 4;
  - finish Figure 5 after the full SPRINT run;
  - build Figure 6B for CHS;
  - update Figure 1 (cohorts).
3. **Analyses:**
  - plasmode re-run on the 31-trial analysed set;
  - FDR for the agreement family on 31 trials;
  - per-trial AI-EHR view (Figure 2D analogue);
  - CHS CLMBR-T;
  - SPRINT full run;
  - verify the STOP-2 head-to-head estimate (CHS emulation 3).
4. **Deck consistency:**
  - slide 4 says "bring unstructured information into trial emulation", which conflicts with the CLMBR-T wording rule;
  - take-home claim 3 says "Trial replication", which should be "closer on average, not trial-specific".
5. **Public repository.** `audits/bdc-fig5/RESULTS_LOCAL.md` says the BDC aggregates are not committed while the repository is public. This file contains CHS and SPRINT aggregates and is committed on local `main` only. Do not push `main` until that is cleared.
6. **Claim-by-claim audit** of this file against its sources, once the figures are final.

