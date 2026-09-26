# RCT-DUPLICATE in depth, and where ECG-augmented PS fits in the literature

Compiled 2026-09-25. Sources: PubMed/Europe PMC abstracts (via the Europe PMC REST API), PMC full text where open access, and journal/arXiv pages. Anything marked **[unverified]** was not checked against a primary source in this session; it is cited from memory or from a search snippet only. Numbers without that tag were read from the abstract or full text at the URL given.

---

## PART 1: RCT-DUPLICATE

### 1.1 Core papers

| Paper | Link | Scope |
|---|---|---|
| Franklin JM, Pawar A, ... Temple R, Schneeweiss S. *Clin Pharmacol Ther* 2020;107:817. Process paper | PMID 31541454, https://doi.org/10.1002/cpt.1633 | Picked 40 RCTs and expected about 30 replications to be completed. Lays out the structured, registered process. |
| Franklin JM, Glynn RJ, Suissa S, Schneeweiss S. "Emulation differences vs. biases when calibrating RWE findings against RCTs." *CPT* 2020 | PMID 32052415, https://pmc.ncbi.nlm.nih.gov/articles/PMC7233792/ | Conceptual paper on why RCT and RWE results differ. |
| Franklin JM, Patorno E, Desai RJ, et al. *Circulation* 2021;143:1002-13. First 10 trials | PMID 33327727, https://pmc.ncbi.nlm.nih.gov/articles/PMC7940583/ | 3 active-controlled and 7 placebo-controlled cardiometabolic/antiplatelet trials. |
| Wang SV, Schneeweiss S, RCT-DUPLICATE Initiative. *JAMA* 2023;329:1376-85. 32 trials | PMID 37097356, https://pmc.ncbi.nlm.nih.gov/articles/PMC10130954/ | 30 completed and 2 ongoing trials. Main results paper. |
| Heyard R, Held L, Schneeweiss S, Wang SV. *BMJ Med* 2024;3:e000709. Meta-regression | PMID 38348308, https://pmc.ncbi.nlm.nih.gov/articles/PMC10860009/ (a correction for an EINSTEIN-PE data error is at PMID 40519359) | Explains why RCT and RWE estimates differ. |
| Köppe J, Micheloud C, Erdmann S, Heyard R, Held L. *BMC Med Res Methodol* 2025. Sceptical p-value | PMID 40413382, https://pmc.ncbi.nlm.nih.gov/articles/PMC12103786/ | Alternative measure of replication success. |
| Weckstein AR, Wang SV, Wyss R, Schneeweiss S. *JAMIA* 2026;33:573. Data-adaptive vs investigator-specified adjustment | PMID 41338229, https://doi.org/10.1093/jamia/ocaf204 | 15 RCT-DUPLICATE emulations. **Closest methodological precedent for us.** |
| Htoo PT, Patorno E, Schneeweiss S, Wang SV. *CPT* 2026. Post hoc population standardization | PMID 41733244, https://doi.org/10.1002/cpt.70241 | 4 cardiovascular outcome trials. Negative result. |
| Wang SV, Russo M, Glynn RJ, ... Concato J, Schneeweiss S. *CPT* 2025. BenchExCal | PMID 40067205, https://pmc.ncbi.nlm.nih.gov/articles/PMC12087693/ | Calibration framework. |
| Wang SV, Lin KJ, Schneeweiss S. *PDS* 2024. The 8 DOAC emulations | PMID 38720425, https://pmc.ncbi.nlm.nih.gov/articles/PMC11086666/ | The one discordant trial "was aligned with a meta-analysis of six trials", so the trial itself may have been the outlier. |
| Suissa S, et al. *AJE* 2025. COPD/asthma emulations | PMID 39191649 | Results were "mainly discordant". IMPACT: RWE HR 1.08 vs RCT 0.84. Blamed on forced discontinuation of treatment before randomization. |
| D'Andrea E, et al. *Arthritis Rheumatol* 2025. HORIZON-PFT | PMID 39129266 | RWE HR 0.72 vs RCT 0.59. Interpolating the RCT to 18 months gives HR 0.74, so the gap is explained by the delayed effect combined with short persistence. |
| Wang SV, Sreedhara SK, Schneeweiss S (REPEAT). *Nat Commun* 2022 | PMID 36045130 | Reproduced 150 RWE studies. Pearson r = 0.85; median HR ratio 1.0 (IQR 0.9-1.1). A useful ceiling: two analyses of the *same* data only correlate at about 0.85. |

### 1.2 Agreement metrics (exact definitions)

- **Regulatory agreement.** Franklin 2021 called it regulatory agreement; Wang 2023 renamed it "statistical significance agreement". Definition: "the ability of the RWE study to replicate the direction and statistical significance of the RCT finding", i.e., "estimates and CIs on the same side of the null". Wang 2023 adds **partial significance agreement**: for non-inferiority trials, the RWE meets the prespecified NI criterion even if it shows superiority. Wang reports "full or partial" as the headline number.
- **Estimate agreement.** The RWE HR point estimate lies inside the RCT's 95% CI.
- **Standardized difference agreement.** z = (θ̂_RCT − θ̂_RWE) / sqrt(σ̂²_RCT + σ̂²_RWE) on the log-HR scale. Agreement means |z| < 1.96.
- **Continuous metrics.** Pearson r of log HRs across pairs; Cohen κ for significance agreement (Wang 2023); a Bland-Altman plot of log-HR differences.
- **Heyard 2024.** Outcome is the difference in log HR. Uses an inverse-variance weighted regression against a constant, with multiplicative heterogeneity as in Mawdsley et al. A value of 1 means no excess heterogeneity.
- **Weckstein 2026** adds a **difference-in-differences** metric for comparing adjustment strategies against the RCT benchmark.
- **Wider TTE literature** (BMJ 2026 meta-analysis, below): **ratio of ratios** (HR_TTE / HR_RCT), pooled with I². Hemkens 2016 used the relative odds ratio.

### 1.3 Results

**Franklin 2021 (10 trials).**
- Significance ("regulatory") agreement in 6/10.
- Estimate agreement in 8/10.
- Either metric met in 9/10.
- |standardized difference| < 2 in 9/10.
- Pairs (RCT HR vs RWE HR):

| Trial | RCT HR | RWE HR | Comparator in RWE |
|---|---|---|---|
| LEADER | 0.88 | 0.83 | DPP-4i as placebo proxy |
| DECLARE | 0.83 | 0.68 | DPP-4i as placebo proxy |
| EMPA-REG | 0.86 | 0.80 | DPP-4i as placebo proxy |
| CANVAS | 0.86 | 0.83 | DPP-4i as placebo proxy |
| CARMELINA | 0.98 | 0.89 | Sulfonylurea as placebo proxy |
| TECOS | 0.98 | 0.89 | Sulfonylurea as placebo proxy |
| SAVOR | 1.00 | 0.80 | Sulfonylurea as placebo proxy |
| CAROLINA | 0.98 | 0.92 | Glimepiride (active comparator) |
| TRITON | 0.81 | 0.87 | Clopidogrel |
| PLATO | 0.84 | 0.92 | Clopidogrel |

- The largest deviations were in the trials that used a sulfonylurea as the placebo proxy. The authors attribute this to residual confounding (frailer or poorer patients get older, cheaper drugs).
- Design: 1:1 nearest-neighbour PS matching, caliper 0.01, on more than 120 covariates from a 6-month baseline.
- Lab data were **left out of the PS and checked for balance after matching.** This is the direct analog of our echo-balance check.
- Analysis was on-treatment with a 30-day grace period. The authors note this is one reason RWE effects came out larger than RCT effects, since trials are ITT with long follow-up.

**Wang 2023 (32 trials; 29 completed trials with HRs plus the 2 predicted trials).**
- Overall: Pearson r 0.82 (95% CI 0.64-0.91). Full or partial significance agreement 75% (56% full + 19% partial). Estimate agreement 66%. Standardized difference agreement 75%. κ = 0.57 (0.34-0.81).
- Post hoc subset of 16 **closely emulated** trials: r 0.93 (0.79-0.97). Full or partial significance agreement 94% (75% full). Estimate agreement 88%. Standardized difference agreement 88%. κ 0.89 (0.69-1.00).
- The 16 **not closely emulated** trials: r 0.53 (0.00-0.83). Significance agreement 56% (38% full). Estimate agreement 50%. Standardized difference agreement 69%. κ 0.31.
- Mean difference in log HR 0.01 (limits −0.38 to 0.39). Removing 1-2 outliers changed r to anywhere between 0.44 and 0.86, so a correlation over about 30 pairs is fragile.
- 83% of 35 control outcomes gave the expected result.
- Both prospectively predicted trials (CAROLINA, PRONOUNCE) agreed on all 3 binary metrics.
- Design: all 32 protocols were registered on ClinicalTrials.gov before any inferential analysis. Three US claims databases (Optum, MarketScan, Medicare). 1:1 PS matching with a 1% caliper on more than 100 covariates. On-treatment primary analysis, ITT in eTable 4.
- **Trials were chosen for feasibility**, meaning adequate power, measurable key confounders, and emulatable endpoints.

**Heyard 2024 (29 pairs).**
- Mean difference in log HR 0.002 (95% CI −0.066 to 0.071).
- Multiplicative heterogeneity was 1.95, meaning pairs disagree about twice as much as sampling error alone would predict.
- Adding the close-emulation indicator: coefficient −0.167 (−0.288 to −0.045), heterogeneity down to 1.76.
- Univariate coefficients (difference in log HR):

| Emulation difference | Coefficient (95% CI) | R² |
|---|---|---|
| Discontinuation of maintenance treatment without washout | 0.286 (0.189 to 0.383) | 0.56 |
| Run-in period | 0.253 (0.130 to 0.376) | 0.38 |
| Placebo control | −0.167 (−0.286 to −0.049) | 0.23 |
| Good comparator emulation | 0.111 (ns) | — |
| Dose titration | −0.079 (ns) | — |
| In-hospital start (univariate) | 0.098 (ns) | — |
| Delayed effect (univariate) | 0.257 (ns) | — |

- The final model, chosen by leave-one-out MSE with the one-SE rule, kept in-hospital start (0.207), discontinuation (0.323) and delayed effect (0.374). Residual heterogeneity was **1.061**, i.e., close to none.
- Conclusion: most of the RCT-RWE variation is explained by **design emulation differences, not confounding**.

**Htoo 2026.** Standardizing the PS-matched claims cohorts to the RCTs' age, sex and risk-factor mix "produced minimal changes in HRs" and widened the CIs.

**Weckstein 2026 (15 emulations, Optum 2004-2023).**
- Outcome-adaptive LASSO beat investigator-specified adjustment for RCT agreement in 73% of full data-adaptive and 87% of hybrid emulations.
- Other methods that use associations with both treatment and outcome did similarly well. **PS models tuned only for treatment prediction did poorly.**
- The result depended on the trial. Hybrid data-adaptive plus investigator-specified adjustment was "most reliable".

### 1.4 How "close emulation" was defined (post hoc)

The criteria come from Wang 2023, repeated verbatim in Heyard 2024. A pair counts as closely emulated if **none** of the following applies:

1. Therapy starts in hospital. Claims do not see inpatient initiation, e.g., antiplatelets during an ACS admission (3 trials, 9%).
2. A run-in that selectively enrolls responders to one arm (13 trials, 41%).
3. Randomization effects mixed with discontinuation of baseline therapy (9 trials, 28%). For example, COPD trials stopped maintenance inhalers at randomization.
4. Delayed effect combined with long trial follow-up (3 trials, 9%). Real-world median on-treatment follow-up was 4-18 months vs 24-36 months in trials.

It also requires comparator and outcome emulation to be at least "moderate", with at least one rated "good".

Two further design issues were recorded but are **not** in the closeness rule: dose titration (11 trials, 34%) and placebo emulated with an active comparator expected to have no effect (10 trials, 31%). Overall ratings: comparator emulation good 66%, moderate 25%, poor 9%; outcome emulation good 59%, moderate 41%.

The indicator was **post hoc, set by the study team, and not blinded to results.** Heyard's data-driven selection later confirmed three of the four items.

### 1.5 How RCT-DUPLICATE framed its conclusions

- **Wang 2023 headline:** "RWE studies can reach similar conclusions as RCTs when design and measurements can be closely emulated, but this may be difficult to achieve. Concordance varied depending on the agreement metric. Emulation differences, chance, and residual confounding can contribute to divergence ... and are difficult to disentangle."
  - The message is positive but conditional. It leads with the post hoc closely-emulated subset (r 0.93), is openly caveated, and reports **several metrics** rather than one test. There was **no formal hypothesis test** of agreement.
- **Franklin 2021:** the positive message was a *design lesson* ("selection of active comparator therapies with similar indications and use patterns enhances the validity of RWE"), plus the caveat that concordance "is not guaranteed".
- **Heyard 2024:** reframed disagreement as a mismatch of *estimands* rather than bias, i.e., the RCT and the RWE study answer different questions.
- **DOAC paper 2024:** when an emulation disagreed, the trial itself may be the outlier; it was compared against a meta-analysis of similar trials.

### 1.6 Methodological lessons

- Protocols were registered on ClinicalTrials.gov before any outcome analysis. Success criteria were prespecified per trial (Franklin 2021).
- New users vs active comparator; 1:1 nearest-neighbour matching, caliper 0.01; more than 100-120 investigator-specified covariates from a 6-month look-back. Standard hdPS was not used in the main analyses; Weckstein 2026 later tested data-adaptive methods.
- On-treatment was primary because real-world persistence is short; this makes delayed-effect trials hard to emulate. ITT was a sensitivity analysis.
- Placebo proxies work only with a comparator believed to have no effect and a similar indication. DPP-4i worked; sulfonylureas did not.
- Balance was checked on variables not used in the PS (labs in the linked subset). The Patorno 2018 precedent is in 2.1.
- Trials were chosen for feasibility. The authors say this limits generalizability and that "multiple factors ... cancel each other out".

---

## PART 2: The research landscape

### 2.1 Adding richer or unstructured data to claims PS (closest analogs to ECG-in-PS)

- **Patorno E, ... Schneeweiss S. *Diabetes Obes Metab* 2018.** PMID 29206336, https://pmc.ncbi.nlm.nih.gov/articles/PMC6207375/
  - 1:1 PS matching on more than 100 claims covariates balanced EHR-only variables (HbA1c, BMI, eGFR, BP, smoking); most SMDs were below 0.1 and residual SMDs below 0.2.
  - They used a Bross-type bias analysis: RR 1.50 moved only to 1.52-1.53.
  - **Precedent for using held-out physiology balance as a validity check.** Their conclusion was that claims PS was *sufficient*. Our finding is the reverse: echo LV structure stays imbalanced without the ECG. That contrast is a selling point.
- **Schneeweiss S, et al. *BMC Med Res Methodol* 2012.** Lab supplement for statins; PMID 23181419.
  - Lab testing is selective: claims predict *who gets* a test (AUC 0.89-0.93) but explain only 14% of variation in the values.
  - The authors concluded the added value of labs is limited. This is a good foil for ECG: ECGs are near-ubiquitous in CV patients, so missingness matters less.
- **Wyss R, Plasek JM, ... Lin KJ. *CPT* 2023.** Bag-of-words from free-text notes (PMID 36528788).
  - NLP features **improved prediction of treatment** but gave "little to no improvement" in predicting outcomes.
  - This mirrors what we would expect if ECG mainly predicts treatment choice. Checking ECG's association with the outcome is a necessary diagnostic.
- **Wyss R, Yang J, Schneeweiss S, ... Lin KJ. *J Biomed Inform* 2025.** Ultra-high-dimensional NLP proxy adjustment (PMID 40691893; https://pmc.ncbi.nlm.nih.gov/articles/PMC11838641/).
  - Claims-only PS left large imbalances in the NLP features.
  - HR changes from adding NLP were small: PPI 1.40 → 1.38; HTN 0.96 → 1.01; analgesics 0.76 → 0.81.
  - Framed as "improved overall covariate balance and **may provide a modest benefit**". **This is the most direct precedent for how to frame a modest effect-estimate gain.**
- **Plasek JM, et al. *Comput Biol Med* 2025** (PMID 39965395). Bross ranking of NLP-derived features (including BERT/BioBERT/GloVe embeddings) vs structured features. The top 25 confounders were mostly expert/structured features; embeddings mattered at ranks 25-100.
- **Zeng J, Gensheimer MF, Rubin DL, Athey S, Shachter RD. *Nat Commun* 2022** (PMID 35197467). Confounders mined from Stanford oncology notes "shift the HR estimate towards the RCT results" in 4 cohorts. A precedent for showing movement toward the RCT.
- **Han L, ... Aghaeepour N. medRxiv 2026** (doi 10.64898/2026.08.22.26361065; not peer reviewed).
  - Sentence embeddings of surgical procedure names, reduced **with PCA** and added to entropy balancing, across 3 perioperative RCT replications.
  - In GA-CARES, adding embeddings moved a spurious benefit to OR 0.84 (0.62-1.14), consistent with the RCT.
  - Methodologically almost identical to our embedding → PCs → PS pipeline.
- **Veitch V, Sridhar D, Blei D. "Adapting Text Embeddings for Causal Inference." UAI 2020** (https://proceedings.mlr.press/v124/veitch20a.html). Argues for "causally sufficient embeddings": **reduce dimension with supervision, keeping only what predicts treatment and outcome.** Our 32 unsupervised PCs may discard the confounding-relevant signal.
- Keith, Jensen, O'Connor. "Text and causal inference: a review of using text to remove confounding." ACL 2020. **[unverified]**
- **Weberpals J, et al. *Epidemiology* 2021** (PMID 33591049). An autoencoder representation of Flatiron EHR used as the PS "did not perform better than ... LASSO". Negative or neutral result.
- **Fan Z, ... Rahimi K. *Nat Commun* 2026** (PMID 42443168; https://pmc.ncbi.nlm.nih.gov/articles/PMC13486677/).
  - CPRD HFrEF emulations: beta-blockers (positive control) and digoxin (negative control).
  - PSM, IPTW, TMLE and a Transformer (T-BEHRT-type) **all failed** to reproduce the RCTs, although they recovered the truth in semi-synthetic simulations.
  - Strong negative precedent. It shows that plasmode success does not by itself validate a method, and it motivates adding information *beyond* coded EHR, which is our case.
- **Ma F, et al. "Foundation Models to Unlock RWE from Nationwide Medical Claims" (ReClaim). arXiv 2605.02740, 2026** (not peer reviewed).
  - A claims foundation-model embedding added to the PS.
  - **Residual systematic error on negative control outcomes** fell (a "72% reduction in systematic bias on average" vs Delphi embeddings) across GLP-1RA/SGLT2i/DPP-4i comparisons.
  - Precedent for using negative controls to measure the value of embeddings in a PS.
- EHR foundation models:
  - CLMBR: Steinberg E, et al. *J Biomed Inform* 2021 (PMID 33290879).
  - MOTOR: Steinberg E, et al. ICLR 2024 (arXiv 2301.03150). **[unverified]**
  - Targeted-BEHRT: Rao S, et al. *IEEE TNNLS* 2024 (PMID 35737602).
  - I found no peer-reviewed RCT-benchmarked PS study using CLMBR/MOTOR.
- ECG encoders: PCLR, Diamant N, et al. *PLoS Comput Biol* 2022 (PMID 35157695).
  - **I found no published study that uses ECG waveform or AI-ECG embeddings for confounding adjustment or PS in pharmacoepidemiology.** Searches of Europe PMC, the web and arXiv returned only AI-ECG diagnosis, TARGET-AI deployment, and ECG-age biomarker papers. Our work appears to be the first on this, but a search absence does not prove novelty.
- Theory for "proxy of unmeasured physiology":
  - Miao W, Geng Z, Tchetgen Tchetgen EJ. *Biometrika* 2018. Proxy variables of an unmeasured confounder (PMID 33343006).
  - Ogburn EL, VanderWeele TJ. *Epidemiology* 2012 (PMID 22450692). Adjusting for a nondifferentially mismeasured confounder gives *partial* bias removal. This is exactly the "ECG removes ~20%" pattern.

### 2.2 hdPS and data-adaptive PS benchmarked against RCTs

- **Schneeweiss S, et al. *Epidemiology* 2009** (PMID 19487948). The original hdPS. Benchmarked against "results expected from RCTs": for COX-2 inhibitors vs NSAIDs, RR 1.09 crude → 0.94 with 15 predefined covariates → 0.88 with +500 hdPS covariates.
- **Toh S, García Rodríguez LA, Hernán MA. *PDS* 2011** (PMID 21717528). hdPS in THIN EMR: OR 0.81 with known confounders, 0.81 with smoking/BMI/alcohol added, 0.78 with hdPS added. **Little gain when major confounders are already captured**, which is relevant to our "full PS" arm.
- **Tian Y, Schuemie MJ, Suchard MA. *IJE* 2018** (PMID 29939268). Large-scale L1-regularized PS beat hdPS on balance and on negative-control bias. The framework combines plasmode and negative controls.
- **Karim ME, Pang M, Platt RW. *Epidemiology* 2018** (PMID 29166301). Machine learning is about as good as hdPS; hybrids are slightly better in plasmode.
- **Wyss R, et al. *Epidemiology* 2018** (PMID 28991001). Super Learner plus hdPS in plasmode; overfitted PS models hurt.
- **Wyss R, et al. *PDS* 2022** (PMID 35729705). Review: machine-learning proxy adjustment can supplement investigator-specified variables. Feature generation and diagnostics are underdeveloped.
- **Weckstein 2026** (see 1.3). The first systematic RCT-benchmarked comparison.

### 2.3 Benchmarking frameworks for RWE vs RCT

- **OHDSI empirical calibration.** Schuemie MJ, et al. *PNAS* 2018 (PMID 29531023). Negative controls plus synthetic positive controls; calibrated CIs restore 95% coverage.
- **OHDSI Methods Benchmark.** Schuemie MJ, et al. *Harv Data Sci Rev* 2020 (PMID 33367288; https://pmc.ncbi.nlm.nih.gov/articles/PMC7755157/). "In most contexts, only half of the 95% CIs" covered the truth.
- **LEGEND-HTN.** Suchard MA, et al. *Lancet* 2019 (PMID 31668726). 22,000 calibrated HRs across 9 databases; large-scale PS plus control outcomes.
- Hwang H, et al. *BMC Med Res Methodol* 2022 (PMID 35896966). Calibration works best when the bias comes from unmeasured confounding. Choosing suitable negative controls matters.
- **BenchExCal** (Wang 2025, PMC12087693).
  - Stage 1 is a benchmark emulation. Its divergence ξ₁ (difference in log HR) is scaled by the variance ratio and used as a normal prior on the stage-2 bias.
  - Includes a tipping-point analysis.
  - Uses the same three binary metrics.
  - 5 planned examples: RECORD1 → knee surgery; RECORD → EINSTEIN-DVT; SUSTAIN-6 → PIONEER-6/SOUL; EMPEROR-Reduced → EMPEROR-Preserved; SOUL prediction.
- **Dahabreh IJ, Robins JM, Hernán MA. *Epidemiology* 2020.** "Benchmarking observational methods by comparing randomized trials and their emulations" (PMID 32740470). A conceptual framework: agreement tests the joint validity of the data, the design and the analysis.
- Matthews AA, ... Hernán MA. *JAHA* 2021 (PMID 33998290). VALIDATE was emulated in SWEDEHEART, the same registry. 180-day death: RR 1.21 (0.88-1.54) vs trial HR 1.05. Even rich registry data could not capture minor bleeding or 14-day effects.
- **OPERAND.** Crown W, Dahabreh IJ, et al. *Value Health* 2023 (PMID 35970705). Two teams emulated the same trials (ROCKET-AF, LEAD-2) and made different design choices; analyst decisions are a source of variability.
- Hernán MA, et al. *Epidemiology* 2008 (PMID 18854702). WHI vs Nurses' Health Study reanalysis.
- **Meta-epidemiology.**
  - **Wang C, ... Magee LA. *BMJ* 2026** (PMID 42156120; https://pmc.ncbi.nlm.nih.gov/articles/PMC13184834/).
    - 107 TTE-RCT pairs: r 0.59 (0.45-0.70); standardized difference agreement 79%; ratio of ratios 0.96 (0.92-1.01; I² 36%).
    - 63 closer emulations: r 0.83; standardized difference agreement 87%.
    - MACE ratio of ratios 0.91 (0.86-0.96), i.e., TTEs underestimate CV effects. Claims-based emulations: ratio of ratios 0.90.
    - Poorer concordance was associated with imbalanced baseline characteristics, in-hospital start and poor outcome emulation.
    - They recommend "leveraging multisource linked databases".
  - Hemkens LG, et al. *BMJ* 2016 (PMID 26858277). 16 PS-based routinely-collected-data studies vs later RCTs: direction differed in 31%; mortality estimates 31% more favourable (ROR 1.31, 1.03-1.65).
  - Hong YD, et al. *BMC Med* 2021 (PMID 34865623). 74 pooled pairs: 79.7% not significantly different; 17.6% significantly different and in opposite directions.
  - Bartlett VL, ... Ross JS. *JAMA Netw Open* 2019 (PMID 31596493). Only 15% of 220 high-impact US trials could be replicated with claims or EHR data.
- **Replicability statistics.** Köppe/Held 2025: the sceptical p-value has the two-trials-rule type I error with more power.
- On the "ratio of HRs within 0.8-1.25" metric: **no RCT-DUPLICATE precedent found.** The nearest precedents are ratio of ratios (Wang C 2026), relative OR (Hemkens 2016), and REPEAT's HR ratio IQR 0.9-1.1. A 0.8-1.25 band would be an invented threshold.
- Merola D, ... Wang S. *JAMA Netw Open* 2024 (PMID 39348118). KEYNOTE-189 in a multi-system EHR: HR 0.95 vs RCT 0.49. An EHR failure case.

### 2.4 Information-poor data, look-back and EHR continuity (precedent for the dropout experiment)

- **Lin KJ, et al. *CPT* 2018** (PMID 28865143).
  - EHR continuity, measured as mean proportion of encounters captured. The top 20% by predicted continuity had **3.5-5.8-fold less misclassification** of 40 CER variables.
  - Directly relevant: a single-health-system EHR misses out-of-system care.
  - Follow-ups: Merola/Lin *Clin Epidemiol* 2022 (PMID 36387928); *JAMIA* 2022 (PMID 35357470); *CPT* 2023 (PMID 37597260, 37026443).
- **Nakasian SS, Rassen JA, Franklin JM. *PDS* 2017** (PMID 28397352). Using all available look-back raised covariate prevalence by at least 15% but barely changed HRs.
- **Conover MM, et al. *PDS* 2018** (PMID 29655187). For statins and a 6-month cancer negative control: HR 0.79 with 1-year look-back, 0.90 with all available, 1.05 with 3-year. **A negative-control outcome used to grade how information-poor a design is.**
- Claims vs EHR-linked: Franklin 2021 and Patorno 2018 used linked EHR subsets. Wyss 2023 and 2025 compare claims-only PS with claims plus EHR text.

---

## PART 3: Concrete additions or reframings for our paper

Each item is tied to a precedent and ordered roughly by value for effort.

1. **Report the full RCT-DUPLICATE metric panel per PS specification** (sparse, sparse+ECG, full, full+ECG, ECG-only).
   - Metrics: significance agreement (full/partial), estimate agreement, standardized difference agreement (|z| < 1.96), Pearson r of log HRs with CI, Cohen κ, and mean difference in log HR with Bland-Altman limits.
   - Also report ratio of ratios with I², as in Wang C 2026.
   - Precedent: Wang 2023 and Franklin 2021 report agreement descriptively and do not test it. Presenting ours as a descriptive panel, with the registered test as one element, matches their norm.
   - Caveat: Wang 2023 showed r moves between 0.44 and 0.86 when 1-2 pairs are dropped. Report leave-one-out ranges.

2. **Apply the published closeness rubric instead of our own, ideally with a rater blinded to results.**
   - Code each of our 18 trials on the Wang/Heyard items: in-hospital start, responder run-in, discontinuation of baseline therapy without washout, delayed effect with long follow-up, comparator quality, outcome quality.
   - Have a clinician blinded to our HRs rate them. Report the subset results as a *replication of RCT-DUPLICATE's post hoc finding*: r 0.93 vs 0.53 for them.
   - This turns our "closely-emulated trials agree best, and sparse+ECG has the lowest error there" into an externally anchored result rather than our own post hoc cut.

3. **Rebuild the paired-error meta-analysis as a Heyard-style meta-regression.**
   - Regress the difference in log HR (RWE − RCT) with inverse-variance weights and multiplicative heterogeneity. Terms: emulation-difference covariates, PS specification, and specification × closeness.
   - Report how much ECG lowers residual heterogeneity: Heyard started at 1.95 and reached 1.06 with 3 design terms.
   - Our p = 0.02 precision-weighted analysis is the same machinery as Heyard 2024 (Mawdsley weighting). Citing it makes the method look standard rather than ad hoc. It stays post hoc, so it should be labeled exploratory.

4. **Separate emulation differences from confounding, and bound what ECG can achieve.**
   - Franklin, Glynn, Suissa, Schneeweiss (*CPT* 2020) and Heyard 2024 show most RCT-RWE disagreement is design and estimand mismatch, which no PS can fix.
   - Add a variance-decomposition or power paragraph. With between-pair heterogeneity near 2 and n = 18, a correctly specified PS gain of about 8-20% of the confounding bias cannot be detected against RCT benchmarks.
   - This explains the non-significant registered tests without special pleading. Weckstein 2026 also found gains "varied by emulation".

5. **Add negative control outcomes and empirical calibration per PS specification.** This is the biggest power gain.
   - Take 20-50 negative control outcomes per trial cohort, following OHDSI (Schuemie 2018 *PNAS*; LEGEND-HTN 2019). Compare the empirical null (mean bias, SD, coverage) for sparse vs sparse+ECG.
   - Hundreds of cohort-by-outcome estimates give far more power than 18 RCT pairs.
   - Closest precedent: ReClaim 2026, which used NCO residual systematic error as the metric for foundation-model embeddings in a PS. Tian 2018 used NCO bias to compare PS methods.
   - Pick NCOs plausibly confounded by cardiac physiology (e.g., falls, pneumonia admission, cataract surgery) so ECG has something to fix. Hwang 2022 shows NCO choice matters.

6. **Strengthen the held-out physiology balance result and translate it into bias.**
   - Patorno 2018 is the template: claims PS, EHR-only lab balance, then a Bross-formula bias analysis. They found claims were sufficient; our echo LV findings say not for cardiac structure. Say this contrast explicitly.
   - Translate residual echo SMDs into expected bias using literature associations between echo variables and outcomes. Plasek 2025 used Bross ranking; Franklin 2021 kept labs out of the PS for exactly this purpose.

7. **Make the data-poor setting central, using standard pharmacoepidemiology levers.**
   - (a) Stratify or restrict by predicted EHR continuity (Lin 2018 *CPT*; Merola 2022). Hypothesis: ECG gains are larger in low-continuity patients, whose coded history is incomplete.
   - (b) Vary look-back (6 months, 1 year, all available), following Nakasian 2017 and Conover 2018.
   - (c) Recast the code-deletion dropout experiment as emulating "claims-thin" or new-to-system patients.
   - All three have precedent and support a credible framing: "ECG substitutes for missing history."

8. **Replace or add to the 32 unsupervised PCs with outcome-aware selection, and compare head-to-head with hdPS/LASSO.**
   - Veitch 2020 argues embeddings must be reduced with supervision on treatment and outcome to be causally sufficient.
   - Weckstein 2026 found outcome-adaptive LASSO and hybrid methods beat investigator-specified adjustment in 73-87% of emulations, while treatment-only PS models did poorly.
   - Wyss 2023 found text features predict treatment, not outcome. A PS-only ECG may therefore act partly like an instrument.
   - Add outcome-adaptive LASSO over (codes + ECG PCs + full embedding) and report whether ECG features survive selection.
   - Report "ECG on top of hdPS" as well as "ECG on top of sparse". Our memory notes hdPS ≥ CLMBR in the long-tail replication, so ECG vs hdPS is the obvious reviewer question.

9. **Frame plasmode as necessary but not sufficient, and cite the precedents.**
   - Plasmode is the standard method (Franklin 2014 *CSDA*, PMID 24587587; Tian 2018; Wyss 2018; Karim 2018).
   - Fan 2026 *Nat Commun* shows methods can pass semi-synthetic tests and still fail against RCTs. This justifies our three-legged evidence: plasmode, held-out physiology balance, and RCT agreement.
   - Also cite Ogburn & VanderWeele 2012 on partial bias removal by imperfect proxies, and Miao 2018 for the formal proxy framing. Both support "~8% overall, more under dropout" as the theoretically expected size.

10. **Calibrate the headline language to the literature's norms.**
    - Use Wyss 2025's "improved balance and may provide a modest benefit" and Wang 2023's conditional "can reach similar conclusions when ... closely emulated".
    - Candidate headline: "ECG embeddings consistently improved balance on unmeasured cardiac structure and reduced simulated bias, most in information-poor settings. Agreement with RCTs improved directionally (14/18 trials) and was best in closely emulated trials, where confounding rather than design mismatch dominates error."
    - Optionally add the sceptical p-value (Köppe/Held 2025) as a secondary replication metric.

11. **Optional prospective component.** Pre-register a prediction for an ongoing CV trial, as in RCT-DUPLICATE's CAROLINA/PRONOUNCE predictions or Wang's COBRRA 2026 prediction (PMID 42389777). Alternatively, apply BenchExCal: calibrate a stage-2 question using the stage-1 divergence under each PS specification, and show that ECG shrinks the calibration prior.

12. **Things not to do.** Htoo 2026 found post hoc population standardization to RCT age/sex/risk factors did not bring estimates closer and widened CIs, so it is low value. Do not present a "0.8-1.25 HR ratio" band as an established metric; no precedent was found.

---

### Unverified or partially verified items
- MOTOR (Steinberg et al., ICLR 2024) and Keith et al. (ACL 2020) are cited from memory and were not checked.
- ReClaim (arXiv 2605.02740) and Han 2026 (medRxiv) are preprints. The ReClaim "72%" figure comes from the abstract page, and its NCO details come from a search snippet.
- The ITT vs on-treatment numbers in Wang 2023 eTable 4 were not accessed.
- The names of the 16 closely emulated trials are not listed in Wang 2023's main text; they are in the supplement, which was not accessed.
- Heyard's coefficients come from the PMC full text of the original article. The later correction (EINSTEIN-PE point estimate) may change the numbers slightly.
