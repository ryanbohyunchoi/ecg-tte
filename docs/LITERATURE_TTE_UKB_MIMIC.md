# Target trial emulation (TTE) and RCT benchmarking in UK Biobank and MIMIC/eICU: literature scan

Compiled 2026-09-26. Sources: Europe PMC REST API (title/abstract search), PubMed/PMC, publisher pages, arXiv, medRxiv.
Search strings: `"UK Biobank" AND ("target trial" OR "trial emulation" OR "emulated trial" OR "emulate")` returned 12 title/abstract hits. The same filter with `MIMIC-IV/MIMIC-III/"Medical Information Mart"/eICU` returned 46 hits, nearly all from 2023 to 2026. Other searches covered new-user/active-comparator designs, RCT replication/benchmarking, text/embedding/foundation-model confounding, and UKB/MIMIC data-limitation papers.

Legend: **[V]** = the abstract was read (Europe PMC or publisher) and the details were checked. **[U]** = not verified: details come from search snippets, secondary descriptions, or my own knowledge, so check them before citing. "Benchmark" means the authors themselves compared their estimate to an RCT. "Implicit RCT" means a relevant RCT exists but the authors did not formally benchmark against it; any agreement statement in those cases is **my reading**, not the authors'.

---

## 0. Bottom line

1. **UK Biobank.** There are about 10 explicit TTE papers (2024–2026), and a handful involve cardiovascular drugs: atorvastatin vs rosuvastatin, ACEi vs ARB, anticholinergic antidepressants → CVD, statins → dementia, and losartan → urate. None of them used ECG, imaging or learned representations for confounding adjustment. Only one did any formal RCT benchmarking: the losartan urate paper, which set a meta-analysis of placebo-controlled trials against n=23 treated participants. Every drug TTE I found uses **linked GP prescribing** (about 45% of the cohort, extract ends around 2016–17) to define new users. **I found no UKB TTE that uses prevalent users at the imaging visit**, which is our design.
2. **MIMIC/eICU.** About 45 TTEs, almost all from 2023–2026. Almost all are ICU-timing strategies (intubation, vasopressin, RRT, transfusion, fluids), plus a few in-hospital cardiovascular drug comparisons: diltiazem vs metoprolol for AF with RVR, early antiplatelet after CABG, high- vs moderate-intensity statin in ACS, and sertraline vs (es)citalopram with QTc measured from MIMIC-IV-ECG. Formal RCT benchmarking is rare. The only MIMIC paper whose stated goal is recovering an RCT result is Doutreligne 2025 (albumin in sepsis vs ALBIOS-type RCTs), plus an arXiv preprint that "aligned with" external RCTs after adding LLM-extracted note covariates. A 2026 iScience paper showed that a MIMIC balanced-crystalloid-vs-saline TTE **flips sign** depending on how exposure is defined, even though propensity-score diagnostics looked fine.
3. **Learned representations for confounding in these datasets.** Precedent is **almost nil**. The nearest items are:
   - MIMIC-IV clinical-note covariates (LLM-extracted, compared with BioClinicalBERT embeddings; arXiv 2026)
   - text matching on MIMIC-type notes (Mozer et al., arXiv 2023)
   - generic theory for pre-trained image/text representations as confounders (Schulte et al., ICML 2025; chest X-ray features, semi-synthetic)
   - a CPRD transformer TTE by Rahimi's group (Nat Commun 2026) that **failed** to reproduce beta-blocker and digoxin RCT benchmarks in HFrEF.

   **I found no paper that uses ECG waveform embeddings (or UKB CMR/retinal embeddings) as confounders in a drug-comparison TTE, in any dataset.** In MIMIC-IV-ECG and UKB, the ECG shows up only as an outcome (QTc) or as a predictor.
4. **Main meta-research backdrop.** Wang et al., BMJ 2026 (107 TTE–RCT pairs): r=0.59 overall and 0.83 for close emulations. Poorer concordance was associated with **treatment started in hospital**, imbalanced baseline populations, and low outcome-emulation quality. Emulations systematically **underestimated MACE effects** (ratio of ratios 0.91). All of these bear on our external validation.
5. **Credibility climate.** MIMIC and UK Biobank are both named among open datasets showing "paper-mill" signatures (Spick et al., J Clin Epidemiol 2026). Reviewers will treat a new MIMIC/UKB TTE sceptically by default.

---

## 1. UK Biobank TTE / trial-emulation papers

| # | Citation | Question / comparison | Design (new-user? time zero) | Outcome & ascertainment | RCT benchmark / agreement | Limitations noted |
|---|---|---|---|---|---|---|
| U1 | Zhou S, Chen R, …, Nie S. *Comparative effectiveness and safety of atorvastatin versus rosuvastatin: a multi-database cohort study.* Ann Intern Med 2024;177. doi:10.7326/M24-0178. PMID 39467290 **[V]** | Rosuvastatin vs atorvastatin (active comparator), UKB plus China Renal Data System | Active-comparator **new-user** TTE; UKB new users are almost certainly from GP prescribing [U: data source detail]; 1:1 multilevel PS matching | 6-y all-cause mortality (primary), MACE, liver outcomes, T2DM, CKD; linked HES/death registry | No formal benchmark. **Implicit RCT:** LODESTAR (Lee YJ et al., BMJ 2023) found no difference in the death/MI/stroke/revascularisation composite and more new-onset diabetes with rosuvastatin [U: from memory]. UKB/CRDS showed lower mortality and MACE with rosuvastatin (UKB RD −1.38%) → **mortality/MACE direction differs from the RCT; the diabetes signal agrees** (my reading) | Authors: "possible residual confounding"; many differences not significant |
| U2 | Xie C, Chen R, Zhou S, …, Nie S. *Comparative effectiveness of ACE inhibitors versus ARBs: multidatabase target trial emulation studies.* Hypertension 2025;82. doi:10.1161/HYPERTENSIONAHA.125.25549. PMID 40905143 **[V]** | ACEi vs ARB new users, UKB (n=72,534) plus CRDS | New-user active comparator; PS matching | 5-y all-cause mortality (UKB HR 1.13, 1.07–1.19), MACE | No formal benchmark. **Implicit RCT:** ONTARGET (ramipril vs telmisartan; equivalent CV outcomes) → **UKB estimate disagrees with the head-to-head RCT** (my reading). A cautionary analogue for our work | Residual confounding (abstract) |
| U3 | Xu Y, Xu H, Guo J, …, Zhan S. *Long-term cardiovascular risks of anticholinergic versus non-anticholinergic antidepressants: a TTE with negative control correction.* Pharmacoepidemiol Drug Saf 2026;35:e70434. doi:10.1002/pds.70434. PMID 42449494 **[V]** | Anticholinergic vs non-anticholinergic antidepressant initiators | **New-user active comparator, restricted to participants with linked primary-care records**; 2006–2021 | CV hospitalisation/death (HES + death registry); median follow-up 9.1 y | None. Uses PS matching plus **proximal causal inference and negative-control-outcome calibration** for unmeasured confounding | Shows that a UKB drug TTE requires the GP-linked subset; strong example of a negative-control toolkit |
| U4 | Lai Y, Her QL, …, Stürmer T, Wang T, Xu Y. *Heterogeneous treatment effects of statins on dementia: TTE with causal ML using integrated genetic and real-world data.* Alzheimers Dement 2026;22. doi:10.1002/alz.71178. PMID 41748529 **[V]** | Statin initiators vs non-initiators, age ≥55 (n=18,366) | Initiator vs non-initiator (GP data implied [U]); MSM; causal forest for HTE by PRS | 5-y dementia (HES/death-based) | Overall aRD −1.0‰ (null), consistent in direction with null statin cognition RCTs (my reading) | Same group as U3 (Stürmer co-author) |
| U5 | Xu X, Naeem A, …, Kontopantelis E, Tomaszewski M. *Urate-lowering effects of losartan: meta-analysis of RCTs and target trial emulation.* Hypertens Res 2026;49. doi:10.1038/s41440-026-02719-0. PMID 42458015 **[V]** | Losartan vs matched controls → serum urate | TTE as a "replication experiment" | Serum urate (UKB biochemistry) | **Explicit benchmark:** RCT meta-analysis −0.29 mg/dL vs TTE −0.35 mg/dL (n=23 treated vs 92 controls) → agreement, but tiny n | Tiny exposed sample, which is itself informative about how rarely UKB captures drug initiation near a measurement visit |
| U6 | Zhuo L, …, Zhan S, Zhao H. *Influenza vaccination and AKI: prospective TTE.* Am J Kidney Dis 2026;87. doi:10.1053/j.ajkd.2025.09.005. PMID 41110628 **[V]** | Vaccination vs none, age ≥65 | **Sequential trials** (50 monthly trials, 2007–2017) in the GP-data subset | 1-y AKI (HES) | None | Residual confounding, selection bias (abstract cut off) |
| U7 | (Hearing aids → dementia) *A hypothetical intervention on the use of hearing aids for the risk of dementia in people with hearing loss in UK Biobank.* Am J Epidemiol 2025. PMID 39676318 (correction PMID 42603279). Code: github.com/JuM24/HA-and-dementia-in-UKBB **[V title / U details]** | Hearing-aid use | TTE framework using UKB assessment waves [U] | Dementia | None | Non-drug; illustrates the use of repeat-visit exposure |
| U8 | Ahmadi M, …, Stamatakis E. *TTE of physical activity and CVD risk: impact of exposure assessment method.* medRxiv 2025. doi:10.1101/2025.11.02.25339322 **[V]** | Adopting ≥150 MVPA min/week vs remaining inactive, between baseline and **re-examination** | Time zero = repeat-assessment visit; PS-matched | Incident CVD (HES) | None | **Closest design analogue to our "time zero at a UKB visit" choice**. Shows how few participants have repeat visits (wearables n=490) |
| U9 | German J, …, Patorno E, Kutalik Z, Philippakis A, Ganna A. *Incorporating genetic data improves target trial emulations.* Nat Genet 2025. doi:10.1038/s41588-025-02229-8. PMID 40533517 **[V]** | Four cardiometabolic RCTs emulated | **FinnGen, not UKB** (often mis-cited as UKB) | Registry | Benchmarks against RCTs. PGS imbalance between arms tracks design quality; **PGS alone cannot adjust for unmeasured confounding** | Relevant as a precedent for using a non-tabular or biological signal to *diagnose* confounding (their PGS ≈ our ECG) |
| U10 | Ann Intern Med / Hypertension group (Nie S) reuse the same UKB+CRDS pipeline; also Zhan S group (U3, U6). Other UKB "TTE" hits are nutrition/behaviour/genetics (alcohol & steatosis, sleep/circadian & dementia) **[V titles]** | — | — | — | — | — |

Related UKB drug cohorts (not labelled TTE; prevalent use at baseline from self-report) **[V titles]**: statins and liver disease (Vell MS, JAMA Netw Open 2023, PMID 37358849); aspirin and ICH (Wang Z, Int J Stroke 2025, PMID 39297449); aspirin and MRI liver fat (Feng Q, Diabetes Obes Metab 2026, PMID 41705647); RAS blockers and PTSD (Kang S, BMC Med 2024, PMID 39443947). This is the genre reviewers will lump us with if the design looks like "baseline self-reported medication vs non-use."

### UKB-specific methodological / data-quality papers (for limitations)
- **Healthy-volunteer / participation bias:** Fry A et al., Am J Epidemiol 2017;186:1026, PMID 28641372 (5.5% response rate; healthier, less deprived) **[V]**. Batty GD et al., BMJ 2020;368:m131, PMID 32051121 (risk-factor associations still generalise) **[V]**. Schoeler T et al., Nat Hum Behav 2023, PMID 37106081 (participation bias distorts genetic associations) **[V]**. Munafò MR et al., Int J Epidemiol 2018, PMID 29040562 (collider bias) **[V]**.
- **Imaging sub-sample is even more selected:** Lyall DM et al., Brain Commun 2022, PMID 35651593 (imaging attendees healthier than the full cohort) **[V]**.
- **Primary-care prescribing:** Darke P et al., JAMIA 2022, PMID 34897458 (curation of GP data; about 45% of participants; multiple suppliers; ends around 2016–17) **[V title; coverage figures U]**. Domingues A et al., PDS 2025, PMID 41355709 (self-reported vs GP-prescribed opioids agree only moderately, κ≤0.66; self-report is collected once at baseline) **[V]**.
- UKB itself lists "pharmacoepidemiological research in the UK Biobank" as an approved-research theme (ukbiobank.ac.uk). **Not a methods paper.**
- **First-occurrence fields (Category 1712):** they collapse primary care, HES, self-report and death into the first date of each 3-character ICD-10 code. The source differs by participant (GP-linked or not), and self-report dates are approximate. I found **no peer-reviewed validation paper for first-occurrence fields as TTE outcomes** [U: UKB resource documentation only].

---

## 2. MIMIC-III / MIMIC-IV / eICU TTE and RCT-benchmarking papers

### 2a. Cardiovascular-drug or ECG-relevant emulations (closest to our in-hospital emulations)

| # | Citation | Comparison | Design / time zero | Outcome | RCT benchmark | Notes |
|---|---|---|---|---|---|---|
| M1 | Deng J, …, Lyu J. *Diltiazem versus metoprolol for AF with rapid ventricular rate in ICU patients using TTE.* Sci Rep 2026. doi:10.1038/s41598-026-61755-5. PMID 42469382 **[V]** | IV diltiazem vs metoprolol initiation (n=1,492) | T0 = first administration; overlap/PS weighting | HR<110 within 1 h; in-hospital death | None; small RCTs exist (e.g., Fromm 2015 in the ED) [U] | Authors: "hypothesis-generating… residual confounding and limitations of structured EHR" |
| M2 | Jiang Y, Ding H, Su J, Li X. *Early antiplatelet therapy and 30-day mortality after CABG: TTE using MIMIC-IV.* BMJ Open 2026;16. doi:10.1136/bmjopen-2025-113901. PMID 42014148 **[V]** | Antiplatelet ≤24 h post-CABG vs not (n=6,887) | Clone-censor-weight for grace period | 30-d mortality (uses MIMIC-IV state death linkage), AKI | None | Explicitly flags "single academic medical centre" |
| M3 | Huang K, …, Sun H. *Renal safety checkpoint for early high-intensity statin in critically ill ACS: multidatabase TTE.* medRxiv 2026. doi:10.64898/2026.08.05.26359828 **[V]** | High vs moderate intensity statin ≤24 h, MIMIC-IV + eICU + MIMIC-III (n=5,178) | Active comparator; database-specific PS, overlap weights | 7-d KDIGO 2–3 AKI / RRT | None | **Pooling MIMIC-III and MIMIC-IV risks double-counting overlapping 2008–2012 BIDMC patients** (a reviewer point applicable to anyone combining them) |
| M4 | Lin J, Zhang T. *Short-term ECG safety after inpatient initiation of sertraline vs citalopram/escitalopram: TTE using MIMIC-IV-ECG.* Gen Hosp Psychiatry 2026;102. doi:10.1016/j.genhosppsych.2026.06.012. PMID 42401115 **[V]** | New-user active comparator (n=4,921); baseline 12-lead ECG within 48 h required | IPTW | 7-d ECG deterioration, QTcF events | None | **Only MIMIC TTE found that uses MIMIC-IV-ECG**, and it uses the ECG as eligibility and outcome, not as a confounder. Limitations: clinically driven follow-up ECGs, machine-measured intervals |
| M5 | Wang S et al. *Early dexmedetomidine in ventilated AMI: TTE using MIMIC-IV.* 2025 preprint (ResearchGate) **[U]** | Early dex vs none (n=2,056) | — | Mortality | None | — |
| M6 | Wang Z et al. *Early albumin infusion and mortality in ICU patients with HFpEF: TTE.* Eur J Clin Pharmacol 2026. PMID 41649576 **[V title]** | — | — | — | — | — |

### 2b. RCT-benchmarking / methods-oriented MIMIC work

| # | Citation | What was done | Agreement / lesson |
|---|---|---|---|
| B1 | Doutreligne M, Struja T, Abecassis J, Morgand C, Celi LA, Varoquaux G. *Step-by-step causal analysis of EHRs to ground decision-making.* PLOS Digit Health 2025;4:e0000721. PMID 39899627 **[V]** | Albumin + crystalloid vs crystalloid alone in sepsis (MIMIC-IV), **compared explicitly with RCTs as gold standard** | Recovering the RCT result needed (i) short treatment-initiation windows (**longer windows → immortal-time bias**) and (ii) expert-chosen confounders; AIPW + random forest most reliable. **Best MIMIC methodological template/precedent for RCT benchmarking** |
| B2 | Dai Q, Hao Y, Shen J, Ren X, Jin C. *Exposure definition sensitivity unmasks hidden confounding in crystalloid TTE.* iScience 2026;29:116584. PMID 42436975 **[V]** | Balanced crystalloid vs saline (SMART/BaSICS-type question), MIMIC-IV n=42,883, eICU external | Two prespecified exposure definitions gave **OR 0.49 vs 2.51** for MAKE-30 despite max SMD 0.048. Switching 89% in MIMIC vs 1.2% in eICU. **Standard PS diagnostics missed confounding from institutional practice.** Directly relevant: "balance ≠ validity" in MIMIC |
| B3 | Wanis KN, Madenci AL, …, Young JG, Celi LA. *Emulating target trials comparing early and delayed intubation strategies.* Chest 2023;164. PMID 37150505 **[V]** | Three nested TTEs in MIMIC-IV | RD went from +7.1 pp to ≈0 as strategies/eligibility became realistic. Shows design choices dominate |
| B4 | Yarnell CJ, …, Celi L, Elbers P, …, Tomlinson G. *Oxygenation thresholds for invasive ventilation: TTE in two cohorts.* Crit Care 2023;27:67. PMID 36814287 **[V]** | MIMIC-IV primary, AmsterdamUMCdb secondary | **Opposite directions in the two databases.** External-validation heterogeneity is expected |
| B5 | Li H, Zang C, Xu Z, Pan W, Rajendran S, Chen Y, Wang F. *Federated target trial emulation.* npj Digit Med 2025;8. PMID 40593099 **[V]** | Sepsis (corticosteroid [U]) trials across eICU + MIMIC-IV (192 hospitals) | Benchmark is the pooled-data estimate, not an RCT (28-d mortality HR 1.08 federated vs 1.10 pooled) |
| B6 | Rajendran S, …, Schenck EJ, Wang F. *Corticosteroids for infectious critical illness: multicenter TTE stratified by predicted organ-dysfunction trajectory.* medRxiv 2024. doi:10.1101/2024.03.07.24303926 **[V]** | eICU+MIMIC-IV development; CEDAR validation | Harm estimates (HR 1.24–1.40) contrast with corticosteroid RCT meta-analyses showing modest benefit/neutral (my reading) |
| B7 | Liu L, Chen J, Macropol K. *LLM-extracted covariates for clinical causal inference: rethinking integration strategies.* arXiv:2604.16763 (2026) **[V abstract]** | Early vasopressor → 28-d mortality, MIMIC-IV sepsis n=21,859; 7 integration strategies incl. **BioClinicalBERT note embeddings** | LLM-extracted structured covariates added to PS beat embeddings (semi-synthetic bias 0.0003 vs 0.0082). Real-data estimate shrank 0.055→0.027, "aligning with external RCT findings." **The closest "representations for confounding in MIMIC" paper; it found raw embeddings inferior to targeted covariates** |
| B8 | Mozer R, Kaufman AR, Celi LA, Miratrix L. *Leveraging text data for causal inference using electronic health records.* arXiv:2307.03687 (2023, rev. 2024) **[V abstract; dataset U, likely MIMIC notes]** | Text-augmented matching on progress notes | Text improves matching/HTE; no RCT benchmark |
| B9 | *Text rationalization for robust causal effect estimation (CATR).* arXiv:2512.05373 **[U]** | Token selection for confounding; MIMIC-III real-data example | Method paper |
| B10 | van den Boom W et al. *The search for optimal oxygen saturation targets in critically ill patients: observational data from large ICU databases.* Chest 2020;157:566. PMID 31589844 **[V snippet]** | eICU + MIMIC-III "replicate" analyses; SpO2 94–98% optimal | Not TTE. Later RCTs (e.g., PILOT, NEJM 2022) found no difference between targets [U]. Classic example of MIMIC association not borne out by RCT |
| B11 | Struja T et al. *Causal inference template for equity in ICU* (Heart Lung 2025, PMID 40163946); *Ideal glucose range in sepsis, MIMIC-IV* (BMJ Open 2026, PMID 41605594) **[V titles]** | MIT-LCP templates | — |
| B12 | THESEUS: *From study design to executable code: automating TTE with LLMs.* JAMIA Open 2026;9:ooag131. PMID 42428529 **[V snippet]** | OHDSI/Strategus-based automation | Not MIMIC-specific |

Other 2025–2026 MIMIC/eICU TTEs (timing strategies; no RCT benchmark) **[V titles]**:
- vasopressin timing (Nakashima, Intensive Care Med 2026, PMID 42578996)
- vasopressor escalation (Zhang, Front Pharmacol 2026, PMID 42565049)
- ROX-guided intubation (Yamamoto, J Intensive Care 2026, PMID 42698089)
- immediate invasive ventilation (Mellado-Artigas, Crit Care 2024, PMID 38730306)
- RBC transfusion and SA-AKI (Liu, J Adv Res 2026, PMID 42571852)
- prophylactic anticoagulation in sepsis thrombocytopenia (Chen, J Thromb Thrombolysis 2026, PMID 42489962)
- acetaminophen in stroke (Wang, Sci Rep 2026, PMID 41965385)
- fentanyl and delirium after cardiac surgery (Qu, J Evid Based Med 2026, PMID 41755357)
- in-hospital influenza vaccination (Feng, Chest 2026, PMID 42061701)
- sepsis bundle timing (Li, Clin Epidemiol 2026, PMID 41883561)
- contrast CT and AKI (Orso, Emerg Radiol 2026, PMID 42671734)

### Critical-care TTE guidance
- Reep CAT, Wils EJ, Heunks L. *Opportunities, challenges and future perspectives for TTE in critical care clinical research.* Crit Care 2025;29:484. PMID 41225646 **[V]**. Covers the need for confounders measured just before treatment, the difficulty of defining time zero in ICU data, same-interval recording of treatment and outcome, and the need for high-resolution longitudinal data. It cites **no** MIMIC TTE with formal RCT agreement.
- MIMIC-IV data paper: Johnson AEW et al., Sci Data 2023;10:1, PMID 36596836 **[V]**. Single centre (BIDMC); dates shifted per patient; out-of-hospital death from state records up to 1 year after last discharge [U: details from MIMIC docs].
- eICU-CRD: Pollard TJ et al., Sci Data 2018;5:180178, PMID 30204154 **[V]**. Multicentre (208 US hospitals, 2014–15); ICU-stay only; no post-discharge follow-up.

---

## 3. Learned representations / imaging / ECG for confounding: general precedent (any dataset)

| Citation | Data | Relevance |
|---|---|---|
| Schulte R, Rügamer D, Nagler T. *Adjustment for confounding using pre-trained representations.* ICML 2025, PMLR 267:53557–53580; arXiv:2506.14329 **[V]** | Chest X-ray DenseNet-121 features (TorchXRayVision), IMDb text; semi-synthetic | Theory: when pre-trained latent features are sufficient for adjustment (DML). Cite as justification for embedding-based adjustment |
| Fan Z, Yang Q, Hu Y, Danaei G, Davey Smith G, Rao S, Rahimi K. *Evaluating bias in TTE for heart failure across statistical and deep learning methods.* Nat Commun 2026;17. PMID 42443168 **[V]** | CPRD Aurum; beta-blockers (positive control) and digoxin (negative control) vs usual care in HFrEF | **No method, including a Transformer, reproduced the RCTs.** All recovered truth in semi-synthetic data. **The most important "negative" analogue: prevalent/usual-care comparators in HF defeat learned EHR representations** |
| German J et al., Nat Genet 2025 (U9) | FinnGen | Biological signal (PGS) as a *balance diagnostic*, not a sufficient adjuster |
| Lee J, Ma S, Serban N, Yang S. JAMIA Open 2025;8:ooaf032. PMID 40290454 **[V]** | Claims, synthetic/semi-synthetic | Transformer PS for IPTW |
| Plasek JM, Wyss R, Weberpals J, et al. Comput Biol Med 2025, PMID 39965395; Weberpals J et al. Am J Epidemiol 2026, PMID 39844590 **[V titles]** | Claims + notes (Mass General Brigham) | NLP-derived features vs structured features in hdPS-style pharmacoepi |
| MIMIC: B7, B8, B9 above | MIMIC notes | Text only; no waveform/imaging |

**Gap statement (supportable):** across UKB, MIMIC and eICU, I found no published TTE or RCT-benchmarking study that uses ECG waveforms, ECG embeddings, CMR/echo/retinal imaging, or EHR foundation-model embeddings as confounders for a drug comparison. MIMIC-IV-ECG appears only as an outcome/eligibility source (M4). UKB ECG/CMR appear only in prediction and association work. Confidence: moderate. Search engines index preprints and ML venues unevenly.

---

## 4. Meta-research on TTE–RCT concordance (context for reviewers)
- Wang C, Tang D, von Dadelszen P, …, Magee LA. *Concordance between TTE and RCTs: systematic review and meta-analysis.* BMJ 2026;393. doi:10.1136/bmj-2025-086810. PMID 42156120 **[V]**. 107 pairs: r=0.59, standardised-difference agreement 79%, ratio of ratios 0.96. Close emulations (n=63): r=0.83. **Poorer concordance with in-hospital treatment start, imbalanced baseline populations, low outcome-emulation quality. MACE effects underestimated** (RoR 0.91).
- A Eur J Public Health 2025 abstract (82 pairs; r=0.55, 0.86 in closer emulations) looks like an earlier version of the same work **[U]**.
- Wang SV, Schneeweiss S, RCT-DUPLICATE. JAMA 2023;329:1376. PMID 37097356 **[V]**. Franklin JM et al., Circulation 2021, PMID 33327727 **[V]**. These are claims-based and use no UKB/MIMIC.
- Reporting: TARGET Statement (Cashin AG, Hansford HJ, Hernán MA, et al.), JAMA 2025, PMID 40899949 and BMJ 2025, PMID 40903028 **[V]**. Hernán MA et al., J Clin Epidemiol 2016, PMID 27237061 (immortal time, prevalent users) **[V]**.
- Credibility: Spick M, Onoja A, Harrison C, Stender S, et al. *Quantifying new threats to health and biomedical literature integrity from rapidly scaled publications.* J Clin Epidemiol 2026, PMID 41740900 **[V]**. Names MIMIC and UK Biobank among 9 datasets with paper-mill hallmarks; 11,577 excess 2025 papers. Suchak T et al., PLoS Biol 2025, PMID 40338847 (NHANES) **[V]**.

---

## 5. Limitations that reviewers will raise, mapped to our v1.5 external validation

The design as recorded in project memory: MIMIC-IV has 5 in-hospital emulations with baseline from prior admissions only; UKB has 3 prevalent-user emulations at the imaging visit, with the ECG on treatment, no GP prescribing on disk, no DOAC coding, and deaths to about 2020.

**UKB**
1. **Prevalent-user design at the imaging visit.** This is the biggest critique, and I found no UKB TTE precedent for it. Every drug TTE in UKB (U1–U4, U6) uses GP-record **new users**. Expect citations to Hernán 2016 / Ray 2003 (depletion of susceptibles, healthy adherer). They will argue the design emulates "continue vs never start" rather than the RCT's "initiate vs control," so RCT agreement is not an appropriate benchmark.
2. **ECG recorded on treatment = a post-treatment covariate.** Adjusting for an ECG measured after drug exposure can remove part of the drug's effect (mediator adjustment: e.g., beta-blocker → heart rate/QRS; MRA/ARNI → LV remodelling) and can introduce collider bias. Reviewers will say this biases toward the null by design, and some will say it invalidates the UKB arm as a test of "ECG as a baseline confounder."
3. **Healthy volunteer and imaging-sub-sample selection** (Fry 2017; Lyall 2022). Event rates are low, which gives low power and wide CIs, and generalisation to RCT populations (HF, ACS, AF patients) is poor.
4. **No primary-care prescribing on disk / self-report medication only at visits.** Exposure misclassification, no dose, no discontinuation, so no per-protocol analysis. DOACs are absent in coding 4, which is a known limitation for AF-trial emulation.
5. **Outcome ascertainment.** HES/first-occurrence fields mix sources, carry approximate self-report dates, and are right-censored (deaths to about 2020). The outcomes are not adjudicated trial endpoints, and there is no outpatient HF worsening.
6. **Paper-mill scepticism.** A UKB drug paper without GP-based new-user design will be read against this backdrop.

**MIMIC-IV**
1. **Single centre (BIDMC), in-hospital initiation.** The BMJ 2026 meta-analysis ties in-hospital treatment start to poorer concordance. Trials such as PARADIGM-HF, ARISTOTLE and EMPEROR randomised mostly stable outpatients, so the target population differs.
2. **Follow-up.** Post-discharge outcomes are limited: death comes from state records to about 1 year, and there is no out-of-system HF hospitalisation or MI/stroke capture. Expect questions about "28-day MI/stroke rule" validity and competing risks.
3. **Baseline from prior admissions only.** Confounder capture is sparse and informative (sicker, repeat patients). Reviewers may argue that ECG gains in MIMIC reflect the data poverty of the setting rather than a general property, though this is consistent with our own v1.4 deletion finding.
4. **Institutional practice/switching confounding** (B2) and design sensitivity (B3, B4). Expect requests for alternative exposure definitions and grace periods.
5. **Date shifting.** Calendar-time trends (e.g., drug availability, guideline changes like sacubitril/valsartan after 2015 or SGLT2i after 2019–2020) cannot be aligned exactly. This matters for any emulation whose drug entered practice during 2008–2022.
6. **ECG as confounder.** Reviewers will ask whether the ECG was acquired before treatment (time-ordering in the 365-day window), because a same-day index ECG may be acquired after or because of the treatment decision.

**Positive framing available**
- **Novelty is real.** No prior study uses ECG or learned physiological embeddings as confounders in UKB/MIMIC TTEs.
- **External validation across two very different data-generating mechanisms** is rarer than single-database MIMIC TTEs, and B4/B2 show that heterogeneity across databases is expected, not a failure.
- **Honest negative/nuanced results align with the literature.** Fan 2026 (transformer fails in HF), B7 (embeddings < targeted covariates), and German 2025 (PGS diagnoses but does not fix confounding) all support framing the ECG as a *physiology-balance diagnostic and partial adjuster*, not a replacement for design.
- **Recommendation:** present UKB as a design-limited sensitivity/transportability check (prevalent-user, on-treatment ECG) rather than as RCT-benchmark evidence, or restrict it to balance/negative-control analyses. Follow TARGET reporting.

---

## 6. Items to verify before citing
- LODESTAR and ONTARGET effect sizes (from memory).
- PILOT oxygen RCT result (from memory).
- UKB GP coverage (~45%, ~230k) and extract end dates (Darke 2022 and UKB docs).
- MIMIC-IV death-linkage window (MIMIC docs).
- FL-TTE sepsis treatment identity.
- Mozer 2023 dataset.
- CATR details.
- Hearing-aid AJE 2025 authors.
- Dexmedetomidine AMI preprint.
