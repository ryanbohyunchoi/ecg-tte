# Literature covariate inventory for the held-out balance panel (v1.6)

Compiled 2026-09-26. Sources: PubMed / Europe PMC (REST API and PMC full text where open access), ClinicalTrials.gov
registrations with attached protocol PDFs, journal pages, OHDSI GitHub source. No patient-level data was read or
written for this document. Local availability comes from `docs/DATA_SOURCES.md`, `docs/v16/COVARIATES.md`,
`docs/COMET_COVARIATE_DICTIONARY.md`, `scripts/trial_specs.py`, `scripts/build_core_baseline.py` and
`scripts/build_physiology_panel_v2.py`, plus an aggregate list of OMOP gold `measurement_concept_id`s (2022 partition,
counts only) and the column names (schema only) of the Epic snapshot tables.

Machine-readable candidate list: [`lit_covariates.json`](lit_covariates.json). It has 150 entries, each with `{id, name, domain,
definition, codes, lookback_days, priority, source_refs, yale_availability, current_panel}`.

Items marked **[unverified]** were not checked against a primary source in this session.

---

## 1. Typical covariate domains and how often they appear

Legend: **x** = included in the PS / adjustment set. **e** = covered only empirically (large-scale or hdPS code
features, with no curated definition). **b** = measured for balance checking only, not in the PS. **-** = not
reported or not checked.

Source columns:
- **KH-COVID**: Khera 2021, ACEi/ARB claims PS [KH1]
- **LEGEND**: LEGEND-T2DM/HTN large-scale PS [KH2, KH3, KH4, OH1]
- **KH-TOPCAT**: Thangaraj 2025, TOPCAT mapped to YNHHS EHR [KH8]
- **DISCO**: Biswas 2025, AI-ECG digital twins [KH7]
- **KH-AIECG**: Dhingra/Croon AI-ECG prognostic adjustment [KH10–KH12]
- **RD-PARADIGM**: RCT-DUPLICATE PARADIGM-HF protocol, NCT04736433 [RD3]
- **EMPRISE**: Patorno/Htoo [RD4, RD5]
- **ARISTOPH**: ARISTOPHANES DOAC [AF1]
- **Sentinel**: Sentinel PS tool [SE1]
- **hdPS**: Schneeweiss [HD1, HD2]
- **CPRD-HF**: Fan 2026, HFrEF TTE in CPRD [UK1]
- **OHDSI-FE**: FeatureExtraction defaults [OH2]

| Domain | KH-COVID | LEGEND | KH-TOPCAT | DISCO | KH-AIECG | RD-PARADIGM | EMPRISE | ARISTOPH | Sentinel | hdPS | CPRD-HF | OHDSI-FE | n / 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Age, sex | x | x | x | x | x | x | x | x | x | x | x | x | 12 |
| CV comorbidities (HF, IHD/MI, AF, HTN, stroke, PAD, valve) | x | e | x | x | x | x | x | x | x | e | x | e | 12 |
| Non-CV comorbidities (CKD, COPD, liver, psych, cancer, thyroid) | x | e | x | - | x | x | x | x | - | e | x | e | 10 |
| CV medications | x | e | x | - | - | x | x | x | x | e | x | e | 10 |
| Race / ethnicity | x | x | x | - | x | - | x | - | - | - | x | x | 7 |
| Comorbidity index (Charlson / combined score / Elixhauser) | x | x | - | - | - | x | x | x | x | - | - | x | 7 |
| Laboratory values | - | e (status only) | x | - | x | b | b | - | - | - | x | e | 7 |
| Lifestyle (smoking, obesity, alcohol/drug use) | - | e | - | - | x | x | x | - | - | e | x | e | 7 |
| Calendar time | - | x | - | - | - | x | x | - | - | - | x | x | 5 |
| Non-CV medications (CNS drugs, opioids, steroids, PPI, NSAID) | - | e | - | - | - | x | x | - | x (NSAID) | e | - | e | 6 |
| Health-care utilisation counts (admissions, ED, office visits) | - | x | - | - | - | x | x | - | x | - | - | - | 4 |
| Empirical high-dimensional codes | - | x | - | - | - | - | x (hdPS sens.) | - | - | x | - | x | 4 |
| Diabetes complications / DCSI | - | x | - | - | - | x | x | - | - | - | - | x | 4 |
| Region / site | - | - | x (by campus) | - | - | x | x | - | - | - | x | - | 4 |
| Insurance / SES proxy (payer, copay, dual, low income) | x | - | - | - | - | x | x (OOP cost) | - | - | - | x (IMD) | - | 4 |
| Vitals (SBP, BMI, HR) | - | - | x | - | x | - | - | - | - | - | x | - | 3 |
| Polypharmacy (number of distinct drugs) | - | - | - | - | - | x | x | - | x | - | - | - | 3 |
| Stroke/bleeding risk scores (CHADS2, CHA2DS2-VASc, HAS-BLED) | - | x | - | - | - | - | - | x (reported) | - | - | - | x | 3 |
| Diagnostic-testing intensity (ECG, echo, labs counts) | - | e | - | - | - | x | - | - | - | e | - | e | 3 |
| Healthy-user markers (flu vaccine, colonoscopy, mammogram, BMD) | - | e | - | - | - | x | - | - | - | e | - | e | 3 |
| Frailty index (Kim CFI / empirical frailty score) | - | - | - | - | - | x | x | - | - | - | - | - | 2 |
| Specialist visits (cardiology, endocrinology, IM/FM) | - | - | - | - | - | x | x | - | - | - | - | - | 2 |
| Learned representation (AI-ECG embeddings, EHR transformer) | - | - | - | x | - | - | - | - | - | - | x (DL arm) | - | 2 |
| Area deprivation (ADI/IMD/SVI) | - | - | - | - | - | - | - | - | - | - | x | - | 1 |
| LVEF / echo | - | - | x | eligibility (EF<40) | - | - | - | - | - | - | - | - | 1 |
| NYHA / functional status | - | - | - | - | - | - | - | - | - | - | - | - | 0 (Khera-lab NLP [KH13] extracts it but has not used it in a PS) |

Main patterns:
1. **What every study includes.** All 12 sources adjust for age, sex and curated CV comorbidities, and almost all
   adjust for the major non-CV comorbidities and CV drugs. Everything else varies.
2. **The Schneeweiss/RCT-DUPLICATE template is the densest investigator-specified set.** It uses more than 120
   covariates over a 180-day look-back (365 days for the frailty score). The PARADIGM-HF replication protocol
   NCT04736433 (the balance table in its Appendix B) lists:
   - demographics, region and year
   - the combined comorbidity score (180 days)
   - about 18 CV comorbidities, including ICD/CRT, pulmonary hypertension, hypotension and HF hospitalisation
   - 16 CV drug classes
   - about 25 other comorbidities: dementia, thyroid disease, hyperkalemia, depression, pneumonia, AKI, CKD stage,
     dialysis, OSA, cancer, anemia and others
   - lifestyle factors: obesity, smoking, alcohol or drug use
   - about 20 non-CV drug classes: antipsychotics, dementia drugs, antiparkinsonians, hypnotics, anticonvulsants,
     antidepressants, lithium, benzodiazepines, opioids, COPD drugs and others
   - healthy-user markers: bone densitometry, colonoscopy, flu vaccine, mammogram
   - frailty score (365 days)
   - utilisation: hospitalisations, ED visits, IM/FM visits, number of distinct drugs, cardiology visits, and
     counts of ECGs and echos
   - SES proxies: copay, low-income indicator, business type, plan type, Medicaid dual status

   Labs (HbA1c, BNP/NT-proBNP, BUN, creatinine, lipids, hemoglobin, sodium, albumin, glucose, potassium) are
   tabulated for balance but kept **out of the PS**. The ARISTOTLE protocol NCT04593030 does this explicitly: "not
   adding to PS". This is the direct precedent for our held-out-physiology design.
3. **OHDSI/LEGEND (the Khera-lab federated work) uses no curated list.** It fits an L1-regularised PS on thousands of
   features:
   - condition/drug group eras (SNOMED/ATC roll-up), procedures, devices, measurements and observations, in 365-,
     180- and 30-day windows (older-adult LEGEND: index, 6 months, 1 year and any time prior)
   - Charlson, DCSI, CHADS2 and CHA2DS2-VASc
   - demographics, including race, ethnicity, index year and index month

   Measurements enter as *status* (was the lab measured), not values [KH4]. Note that the FeatureExtraction default
   `endDays = 0` includes the index day, whereas our convention excludes it.
4. **Two gaps remain even in the literature.** SES and functional status are the domains most often flagged as
   residual confounders (CPRD HFrEF TTE [UK1]; npj Digit Med 2026 operational-TTE review). Only claims studies
   with payer data (RCT-DUPLICATE) or UK data (IMD) adjust for SES, and no reviewed PS study adjusts for NYHA class
   from EHR data.

---

## 2. Khera lab (Yale CarDS Lab): papers and covariate sets

| Paper | Data / design | Covariates used for adjustment, matching or description | Relevance to us |
|---|---|---|---|
| **[KH7] Biswas D, Dhingra LS, Aminorroaya A, Croon PM, Oikonomou EK, Khera R. "High-dimensional phenotypic matching with AI-enhanced ECG to replicate heart failure trial outcomes in real-world data" (DISCO). *Eur Heart J* 2025;46(Suppl 1):ehaf784.4614** | 4,705 HFrEF (EF<40%) patients in a US health network; ARNi vs ACEi against the PARADIGM-HF HR of 0.84 | Traditional Cox adjustment used only **age, sex, hypertension, diabetes, MI, IHD and stroke**. The DISCO arm used embeddings of a CNN AI-ECG model tuned to LVEF, grouped by K-means with K=10, to form "digital-twin" matched clusters. It reported improved "balance of prognostic factors between arms" | **Closest precedent to our study.** Its adjustment set was very thin (7 covariates), and our 150-candidate held-out panel is the stronger test of the same idea. Abstract only; the held-out variables were not specified |
| [KH8] Thangaraj PM, ... Khera R. "Computational Phenomapping of RCT Participants ..." *Circ Cardiovasc Qual Outcomes* 2025 (PMID 40261065) | TOPCAT participants mapped to HFpEF inpatients at 5 YNHHS hospitals (York St, St Raphael, Bridgeport, Greenwich, L+M) | 65 of 1,143 TOPCAT variables could be mapped to the EHR, and 63 covariates were used. They covered demographics, race/ethnicity, LVEF (echo within 6 months), vitals (SBP, BMI, HR), conditions (AF, MI, ...), procedures (PCI), medications (beta-blocker, ...), labs (median missingness 24%) and echo variables. Rule-based ICD-10-CM and name-string maps. Results reported by hospital campus | Shows which trial variables are computable in YNHHS EHR. Supports adding site/campus as a covariate. Lab missingness ranged from 7% to 67% |
| [KH9] Thangaraj PM, ... Khera R. RCT-Twin-GAN. *npj Digit Med* 2026 (PMID 41794982) | SPRINT/ACCORD digital twins | Conditioning covariates: age, Black race, BMI, family history of CVD, female sex, GFR, heart rate, LVH, MI and statin use | Prognostic covariate set for BP trials (ALLHAT/VALUE/ASCOT analogues) |
| [KH1] Khera R, Clark C, Lu Y, ... Krumholz HM. ACEi/ARB and COVID-19. *JAHA* 2021 (PMID 33624516) | Optum Medicare Advantage + commercial claims; PS matching; negative controls | Age, sex, race, **insurance type**, indications (DM, MI, HF, CKD), **every Charlson component**, and number of antihypertensive agents. Balance target: SMD <10%. Also checked equipoise, negative control outcomes and 100 PS-matching iterations | Minimal curated claims set from the Khera lab. Includes insurance, which we lack |
| [KH2] Khera R, Schuemie MJ, ... Suchard MA. LEGEND-T2DM protocol. *BMJ Open* 2022 (PMID 35680274) | OHDSI network, new-user active comparator | Large-scale PS on conditions, drugs, procedures and observations in 365/180/30-day windows, rolled up at SNOMED and ingredient/ATC levels. Charlson, DCSI, CHADS2 and CHA2DS2-VASc. Age, gender, race, index month/year, labs and utilisation. Needle/device codes excluded. "1000s–10 000s" features | Template for an empirical held-out family |
| [KH3] Khera R, Aminorroaya A, Dhingra LS, Thangaraj PM, ... *JACC* 2024 (PMID 39197980); [KH6] *BMJ Med* 2023 (PMID 37829182) | 10 databases; 4 second-line classes | Regularised large-scale PS on demographics, comorbidities, concomitant drugs and utilisation. Pass rule: max SMD <0.15. 100 empirically chosen negative controls | Balance diagnostic threshold of 0.15 across all covariates |
| [KH4] Kim C, ... Khera R (LEGEND-T2DM, older adults). *Nat Commun* 2026 (PMID 41935054) | 9 databases (5 claims, 4 EHR) | L1 PS over demographics, conditions, drugs, procedures, measurements, devices and observations. Windows: index day, 6 months, 1 year, any time prior. "Measurements were included as only the measurement status ... not the value." Max-SMD rule | Supports *lab-measured flags* as a covariate family |
| [KH5] Bu F, ... Suchard MA (Khera co-author). GLP-1RA vs SGLT2i. *JACC* 2026 (PMID 41984016) | 10 databases; 10 individual drugs | Large-scale PS with often more than 10,000 baseline features (demographics, conditions, drugs, procedures, labs). L1 with 10-fold CV; 5 strata or variable-ratio matching, caliper 0.2 | Same as above |
| [KH10] Dhingra LS, ... Khera R. AI-ECG HF risk. *Eur Heart J* 2025 (PMID 39804243); [KH11] PRESENT-SHD. *JACC* 2025 (PMID 40139886); [KH12] Croon PM. *Circulation* 2025 (PMID 40888124) | YNHHS + ELSA-Brasil + UKB; AI-ECG prognosis | Adjustment for demographics and baseline comorbidities (hypertension, diabetes, HF, etc., from pre-ECG encounters) and the competing risk of death. PCP-HF comparator: age, sex, race, SBP, treated HTN, smoking, glucose/DM, BMI, cholesterol, HDL, QRS. Croon ran a PheWAS over **989 phecodes** | AI-ECG outputs track a broad phenome, so held-out balance over a *phecode-wide* panel is a natural extension |
| [KH13] Adejumo P, Thangaraj PM, ... Khera R. NLP functional status in HF. *JAMA Netw Open* 2024 (PMID 39509128) | YNHHS notes | NYHA class and activity/rest symptoms extracted by deep-learning NLP. About 1% of notes mention NYHA explicitly, and about 11% of encounters had symptoms that could be classified | Shows NYHA is recoverable from notes. Our notes cover 2021+ only (partial) |
| [KH14] Aminorroaya A, ... Khera R. ARISE Lp(a) screening in health systems. *Circ Genom Precis Med* 2025 (PMID 39846171) | YNHHS + VUMC EHR | ASCVD history, statin use, antihypertensive use, LDL-C, HDL-C, TG | Shows lipid and ASCVD features are computable in YNHHS |
| [KH15] Dhingra LS, ... Khera R. T2D/CVD registry expenses. *Am J Prev Cardiol* 2026 (PMID 41767452) | YNHHS registry | **ZIP-code median household income** (Census), CCSR principal-dx grouping, age, sex, race | Precedent for ZIP-level SES from YNHHS addresses |
| [KH16] Lu Y, ... Khera R (co-author). Semaglutide and CV risk factors. *JAMA Netw Open* 2025 (PMID 40779264) | YNHHS + Houston Methodist EHR, difference-in-differences | Age, sex, race/ethnicity, calendar and individual fixed effects; baseline = 12-month means | Notes that the payer mix (commercial, Medicare, Medicaid) exists in the EHR |
| [KH17] Dhingra LS, ... Khera R. HCM therapies and AI-ECG markers. *Am J Cardiol* 2025 (PMID 39581517) | Multicenter HCM | Therapy (mavacamten, myectomy, ASA) effect on AI-ECG scores | AI-ECG is treatment-responsive, so it must stay strictly pre-index (already enforced) |
| TARGET-AI (Oikonomou EK, ... Khera R; medRxiv 2025, PMID 40909833) | EHR deployment framework | Not read; the server returned 403 **[unverified]** | - |

Summary of the Khera-lab pattern:
- **Federated OMOP work** (LEGEND, with Suchard/Schuemie) uses *empirical large-scale* PS. It adds four scores
  (Charlson, DCSI, CHADS2, CHA2DS2-VASc), judges balance by max SMD <0.15 and calibrates with negative controls.
- **Single-system YNHHS work** uses *curated clinical* sets: demographics, race/ethnicity, a handful of
  comorbidities, vitals, labs, LVEF and site. It adds AI-ECG as a high-dimensional phenotype (DISCO,
  phenomapping).

I found no Khera-lab paper that puts insurance, ADI, frailty indices or NYHA into a PS on YNHHS data. The
closest are insurance in the Optum claims paper [KH1] and ZIP income used descriptively [KH15]. No CLMBR / EHR
foundation-model PS paper from the lab was found. The EHR-side ML work is schema mapping [Zhou X, AMIA 2025, PMID
40417570] and NLP.

---

## 3. What is available locally (from the docs; aggregate schema only)

| Source | Availability for covariates |
|---|---|
| OMOP gold `condition_occurrence` + `observation` | ICD-10-CM source values, all years. Z/R/W codes often sit in `observation`. All dx-based phenotypes are **yes** |
| OMOP gold `drug_exposure` | Orders only, and only the first word of the order name is kept, so dose, route and adherence are unavailable. Drug classes: **yes**. OTC drugs (aspirin, NSAIDs) are under-recorded: **partial** |
| OMOP gold `procedure_occurrence` | 88% have concept_id 0, so use the CPT source value (PCI, CABG, devices, ECG, echo, stress tests, screening, dialysis). **yes**. DME HCPCS is sparse: **partial** |
| OMOP gold `measurement` (83 concepts) | Vitals (SBP, DBP, HR, SpO2, temperature, RR, weight, height, BMI); CBC with differential; CMP/BMP; LFTs; lipids (TC, HDL, LDL, TG, non-HDL); HbA1c; TSH/T4; INR/PTT; NT-proBNP/BNP; hs-TnT/TnI/TnT; CRP/hs-CRP; uric acid; Lp(a)/ApoB (very sparse). **Missing: UACR / urine protein, magnesium, ferritin/iron** |
| OMOP gold `visit_occurrence` | 9201/9202/9203 counts, inpatient days, index-day setting: **yes**. `observation_period` is unusable, so derive prior observation time from the first visit |
| Epic `Patients` | Race (all listed), ethnicity, sex, DOB, **current ZIP only**. No payer, language, marital status or address history |
| Epic `hosp_enc` / `outpatient_enc` | Hospital area, department, provider type, discharge disposition, means of arrival, LOS. Site, specialty visits and discharge to facility: **partial**, because department-to-specialty mapping is needed |
| Echo metadata (2015+) | LVEF and full structured echo panel: **yes** (already held out) |
| ECG metadata (MUSE) | Intervals and text. These are ECG-proximal and not a fair held-out test for an ECG embedding |
| Notes (2021+) | NYHA/functional status via NLP: **partial** (index ≥2021 only) |
| External, not on raid0 | ADI / SVI / ACS income. ZIP is available, so these are **partial** once a ZIP/ZCTA file is supplied |

**Current panel.** The following sets exist today:
- **PS core** (`build_core_baseline.py`): age, male, index year; LVEF, SBP, DBP, HR, BMI, creatinine, K, Na, Hb
  (withheld from the claims-like PS); 9 DX_CORE comorbidities; trial-specific 90-day drug classes and extra dx;
  3 visit counts.
- **v16 held-out extras**: race/ethnicity, hyperlipidemia, statin, T2D, CAD, tobacco, obesity, the 13-domain
  frailty count, inpatient days, prior HF hospitalisation.
- **Held-out physiology v2**: echo structure/function/valves, NT-proBNP, hs-TnT, eGFR, albumin, BUN, glucose,
  HbA1c, WBC, platelets, LDL.

---

## 4. Consolidated candidate list

The **Current panel** column values mean:
- **PS-core**: in every trial's core PS.
- **PS-trial**: in some trials' PS (`drugs_90d` / `extra_dx`). Held out only in the trials that do not use it.
- **core (withheld...)**: in the core set but excluded from the claims-like PS.
- **held-out v16 / held-out phys**: already on the held-out balance panel.
- **none**: not built.

Default windows follow our convention (index day excluded): diagnoses [index-365, index-1], drugs [index-90,
index-1], labs and vitals latest value in the window, "any prior" = all history before index. Priority tags:
- **core**: appears in most sources or is trial-critical.
- **common**: appears in 2 or more major templates (RCT-DUPLICATE, EMPRISE, OHDSI, Charlson/Elixhauser, frailty).
- **occasional**: appears in single studies.

Reference keys are listed in Section 6.

| # | Covariate | Domain | Definition / codes | Look-back (d) | Priority | Sources | Yale OMOP/Epic | Current panel |
|---|---|---|---|---|---|---|---|---|
| 1 | `age_at_index` | demographics | Age in years at index (exact DOB). *person.birth_datetime* | 0 | core | KH1, KH3, KH7, KH8, RD3, RD4, SE1, OH2, UK1 | yes | PS-core |
| 2 | `sex` | demographics | Recorded sex. *person.gender_concept_id 8507/8532* | 0 | core | KH1, KH3, KH7, KH8, RD3, RD4, SE1, OH2, UK1 | yes | PS-core |
| 3 | `race` | demographics | Race categories (White/Black/Asian/other/unknown). *Epic PATIENT_RACE_ALL* | 0 | core | KH1, KH3, KH8, RD4, OH2, UK1 | yes | held-out v16 |
| 4 | `ethnicity_hispanic` | demographics | Hispanic ethnicity, with explicit unknown. *Epic PATIENT_ETHNICITY* | 0 | core | KH3, KH8, RD4, OH2 | yes | held-out v16 |
| 5 | `index_year` | calendar | Calendar year (or quarter) of index. *index_date* | 0 | core | KH3, RD3, RD4, OH2, UK1 | yes | PS-core |
| 6 | `prior_observation_days` | administrative | Days from first recorded YNHHS visit to index (length of health-system engagement). OMOP observation_period is unusable, so derive it from the first visit. *visit_occurrence min(visit_start_date)* | - | common | OH2, KH2 | yes | none |
| 7 | `care_site_campus` | administrative | Site of the most recent pre-index encounter (YNHH York St/St Raphael, Bridgeport, Greenwich, L+M, community practice). Analogue of claims 'region'. *Epic hosp_enc HOSPITAL_AREA_NAME / outpatient DEPARTMENT_NAME* | 365 | common | KH8, RD3, RD4, OH2, UK1 | partial | none |
| 8 | `index_setting_inpatient` | administrative | Drug initiated during or at discharge from an inpatient stay vs outpatient (index-day visit type). *visit_occurrence 9201/9203/9202 on index date* | 0 | common | RD3, KH8 | yes | none |
| 9 | `insurance_type` | SES | Primary payer: Medicare / Medicaid / commercial / dual / self-pay. *payer/coverage table (not in extract)* | 365 | common | KH1, RD3, KH15 | no | none |
| 10 | `low_income_or_dual` | SES | Medicaid, dual eligibility or low-income subsidy indicator. *payer table (not in extract)* | 365 | common | RD3 | no | none |
| 11 | `area_deprivation_index` | SES | ADI national percentile / state decile of residence (Neighborhood Atlas). Only the current ZIP is available, so use a ZIP/ZCTA-level approximation. *Epic Patients.ZIP + external ADI file* | 0 | common | IX9, UK1 | partial | none |
| 12 | `area_ses_other` | SES | CDC SVI or ZIP median household income (ACS). Khera-lab T2D registry used ZIP income. *Epic Patients.ZIP + CDC SVI* | 0 | occasional | KH15 | partial | none |
| 13 | `preferred_language_non_english` | SES | Preferred language not English / interpreter needed. *Epic PATIENT.LANGUAGE_C (not in extract)* | 0 | occasional | - | no | none |
| 14 | `smoking` | lifestyle | Current tobacco use (dx proxy); ever-use adds history-of-dependence code. *current F17, Z72.0; ever adds Z87.891* | 365 | core | RD3, RD4, KH10, UK1, IX10 | partial | held-out v16 |
| 15 | `alcohol_use_disorder` | lifestyle | Alcohol abuse/dependence or alcohol-related organ disease. *F10, K70, G62.1, I42.6, Z71.41* | 365 | common | RD3, RD4, IX1 | yes | none |
| 16 | `drug_use_disorder` | lifestyle | Non-alcohol substance use disorder. *F11-F16, F18, F19* | 365 | common | RD3, IX1 | yes | none |
| 17 | `obesity_dx` | lifestyle | Obesity diagnosis or BMI-code >= 30. *E66.0/.1/.2/.8/.9, Z68.3x, Z68.4x* | 365 | core | RD3, RD4, IX1 | yes | held-out v16 |
| 18 | `bmi` | vitals | Latest BMI kg/m2. *measurement 4245997* | 365 | core | KH8, KH9, KH10, UK1, IX10 | yes | core (withheld from claims-like PS) |
| 19 | `heart_failure` | CV history | Any HF diagnosis. *I50, I11.0, I13.0, I13.2, I09.81* | 365 | core | KH1, RD3, RD4, SE1, AF1 | yes | PS-trial (extra_dx in AF/ACS/DM trials) |
| 20 | `prior_hf_hospitalization` | CV history | Inpatient stay ending before index with I50 (principal or any position); also the count of such stays. *9201 visit + I50 in stay* | 365 | core | RD3, RD4 | yes | held-out v16 |
| 21 | `ischemic_heart_disease` | CV history | Any IHD (stable/unstable angina, ACS, chronic IHD, old MI). *I20-I25* | 365 | core | KH7, RD3, RD4, UK1 | yes | PS-core |
| 22 | `prior_mi` | CV history | Acute or old MI. *I21, I22, I23, I25.2* | any prior | core | KH1, KH7, KH8, KH9, RD3, RD4 | yes | none (inside IHD) |
| 23 | `prior_pci` | CV history | History of PCI (status code or procedure). *Z95.5, Z98.61; CPT 92920-92944, C9600-C9608* | any prior | core | KH8, RD3, RD4 | yes | PS-trial (Z codes, some trials) |
| 24 | `prior_cabg` | CV history | History of CABG. *Z95.1; CPT 33510-33536* | any prior | core | RD3, RD4 | yes | PS-trial (Z codes, some trials) |
| 25 | `atrial_fibrillation_flutter` | CV history | AF or atrial flutter. *I48* | 365 | core | KH8, RD3, SE1 | yes | PS-core |
| 26 | `other_arrhythmia` | CV history | SVT / other arrhythmia; separately VT/VF or cardiac arrest (any prior). *I47.1, I49.1-I49.9; VT/VF/arrest I47.2, I49.0, I46* | 365 | common | RD3 | yes | none |
| 27 | `conduction_disorder` | CV history | AV block / bundle branch block. ECG-proximal: expect the embedding to capture it. *I44, I45* | 365 | common | RD3 | yes | none |
| 28 | `cardiac_device` | CV history | PPM / ICD / CRT present or implanted. *Z95.0, Z95.81x, Z45.0x; CPT 33206-33249, 33224-33226* | any prior | common | RD3 | yes | none |
| 29 | `valve_disease` | CV history | Valvular heart disease. *I05-I08, I34-I37* | 365 | common | RD3, KH11 | yes | PS-core |
| 30 | `prior_valve_procedure` | CV history | Prosthetic valve / TAVR / surgical valve. *Z95.2-Z95.4; CPT 33361-33369, 33405-33430* | any prior | common | RD3 | yes | exclusion only (AF trials) |
| 31 | `cardiomyopathy` | CV history | Cardiomyopathy (dilated, hypertrophic, other). *I42, I43* | 365 | common | KH12, KH17 | yes | none |
| 32 | `hypertension` | CV history | Hypertension. *I10-I16* | 365 | core | KH7, RD3, RD4, UK1 | yes | PS-core |
| 33 | `pulmonary_hypertension` | CV history | Pulmonary hypertension / pulmonary heart disease. *I27* | 365 | common | RD3 | yes | none |
| 34 | `hyperlipidemia` | CV history | Hyperlipidemia. *E78.0-E78.5* | 365 | core | RD3, RD4, KH14 | yes | held-out v16 |
| 35 | `ischemic_stroke` | CV history | Ischemic stroke or sequelae. *I63, I69.3* | any prior | core | KH7, RD3, RD4, IX3 | yes | PS-core (pooled stroke_history) |
| 36 | `intracranial_hemorrhage` | CV history | Hemorrhagic stroke / ICH. *I60-I62, I69.0-I69.2* | any prior | core | RD3, IX4 | yes | PS-core (pooled) / exclusion PLATO |
| 37 | `tia` | CV history | Transient ischemic attack. *G45 (excl G45.4)* | any prior | core | RD3, IX3 | yes | PS-trial (AF trials) |
| 38 | `peripheral_arterial_disease` | CV history | PAD / atherosclerosis of extremities / PAD procedures. *I70.2-I70.7, I73.9, I74.2-I74.4, Z89.4-Z89.6; CPT 37220-37235* | 365 | core | RD3, RD4, IX3 | yes | PS-core (narrow: I702, I739) |
| 39 | `vte_history` | CV history | DVT/PE history. *I26, I80.1-I80.2, I82.4, Z86.71* | any prior | common | RD3 | yes | none |
| 40 | `cha2ds2_vasc` | risk score | CHA2DS2-VASc (and CHADS2) computed from age, sex, HF, HTN, DM, stroke/TIA/embolism, vascular disease. *components above* | 365 | core | OH2, KH2, AF1, IX3 | yes | none |
| 41 | `has_bled_modified` | risk score | Claims-modified HAS-BLED (HTN, renal/liver disease, stroke, bleeding, age>65, antiplatelet/NSAID, alcohol; labile INR from INR variability if on warfarin). *components above + INR 3022217* | 365 | core | AF1, IX4 | partial | none |
| 42 | `diabetes_any` | metabolic | Diabetes mellitus (any type); T1D (E10) as sub-flag. *E08-E11, E13* | 365 | core | KH1, KH7, RD3, RD4, UK1 | yes | PS-core |
| 43 | `t2d` | metabolic | Type 2 diabetes. *E11* | 365 | common | RD3, RD4 | yes | held-out v16 |
| 44 | `diabetes_complications_dcsi` | metabolic | Diabetes complications: retinopathy, nephropathy, neuropathy, PVD, metabolic (DKA/HHS); DCSI score. *E08-E13 .2/.3/.4/.5/.0/.1, H36, G63.2, E11.51; DCSI map* | any prior | common | OH2, KH2, RD4, IX8 | yes | none |
| 45 | `hypoglycemia` | metabolic | Hypoglycemia events. *E16.0-E16.2, E11.64x, E13.64x* | 365 | common | RD4 | yes | none |
| 46 | `ckd_any` | renal | Chronic kidney disease. *N18, I12, I13* | 365 | core | KH1, RD3, RD4 | yes | PS-core (N18 only) |
| 47 | `ckd_stage` | renal | CKD stage 1-2 / 3 / 4 / 5 (N18.1-N18.5; N18.30-32). *N18.1-N18.5* | 365 | common | RD3, RD4 | yes | none |
| 48 | `eskd_dialysis_transplant` | renal | ESKD, chronic dialysis or kidney transplant. *N18.6, Z99.2, Z49, Z94.0; CPT 90935-90999* | any prior | core | RD3 | yes | none |
| 49 | `acute_kidney_injury` | renal | AKI. *N17* | 365 | common | RD3, RD4 | yes | none |
| 50 | `hyperkalemia` | renal | Hyperkalemia diagnosis. *E87.5* | 365 | common | RD3 | yes | none |
| 51 | `fluid_electrolyte_disorder` | renal | Fluid/electrolyte/acid-base disorders (Elixhauser). *E86, E87* | 365 | common | RD4, IX1 | yes | none |
| 52 | `thyroid_disease` | endocrine | Hypothyroidism or hyperthyroidism. *E00-E03, E89.0; E05* | 365 | common | RD3, UK1 | yes | none |
| 53 | `obstructive_sleep_apnea` | pulmonary | OSA. *G47.33* | 365 | common | RD3, RD4 | yes | none |
| 54 | `copd` | pulmonary | COPD / emphysema / chronic bronchitis. *J41-J44* | 365 | core | RD3, RD4, UK1 | yes | PS-core (pooled with asthma) |
| 55 | `asthma` | pulmonary | Asthma. *J45* | 365 | common | RD3 | yes | PS-core (pooled) |
| 56 | `pneumonia_recent` | pulmonary | Pneumonia (acute illness marker). *J12-J18* | 180 | common | RD3 | yes | none |
| 57 | `liver_disease` | hepatic | Chronic liver disease incl. cirrhosis (Charlson mild/severe). *K70-K77, I85, B18* | 365 | common | RD3, RD4, IX1 | yes | PS-trial (AF, some HF) |
| 58 | `gi_bleed` | bleeding | GI hemorrhage / bleeding peptic ulcer; peptic ulcer disease (Charlson) as a sub-flag. *K92.0-K92.2, K25-K28, K62.5, K55.21* | 365 | core | RD3, AF1, IX4 | yes | PS-trial (ACS) |
| 59 | `major_bleed_other` | bleeding | Other major bleeding: hemorrhage NOS, hematuria, acute posthemorrhagic anemia, hemoptysis, hemarthrosis. *R58, R31, D62, R04.2, M25.0, N93* | 365 | core | AF1, IX4 | yes | PS-trial (AF) |
| 60 | `anemia` | hematologic | Anemia diagnosis. *D50-D64* | 365 | common | RD3, IX1 | yes | none |
| 61 | `coagulopathy_thrombocytopenia` | hematologic | Coagulation defects / thrombocytopenia (Elixhauser). *D65-D69* | 365 | common | IX1 | yes | none |
| 62 | `dementia` | neuro-psych | Dementia / Alzheimer disease. *F01-F03, G30, G31.0, G31.1, G31.83* | 365 | common | RD3, RD4, IX1, IX5 | yes | frailty_count component only |
| 63 | `depression` | neuro-psych | Depressive disorder. *F32, F33, F34.1* | 365 | common | RD3, IX1 | yes | frailty_count component only |
| 64 | `anxiety` | neuro-psych | Anxiety disorders. *F40, F41* | 365 | common | RD3 | yes | none |
| 65 | `serious_mental_illness` | neuro-psych | Psychosis / schizophrenia / bipolar. *F20-F29, F30, F31* | 365 | common | RD3, IX1 | yes | none |
| 66 | `falls` | frailty | Falls. *W00-W19, R29.6, Z91.81* | 365 | common | RD3, IX5 | yes | frailty_count component only |
| 67 | `gait_mobility_weakness` | frailty | Gait abnormality, weakness, debility. *R26, R53, M62.81* | 365 | common | IX5, IX6 | yes | frailty_count component only |
| 68 | `malnutrition_weight_loss` | frailty | Malnutrition / abnormal weight loss / cachexia. *E40-E46, R63.4, R63.6, R64* | 365 | common | IX1, IX5 | yes | frailty_count component only |
| 69 | `osteoporosis_fracture` | frailty | Osteoporosis or fragility fracture. *M80, M81, S72, S22, S32* | 365 | common | RD3, RD4, IX5 | yes | frailty_count component only |
| 70 | `cancer_any` | oncology | Any malignancy excluding non-melanoma skin. *C00-C43, C45-C97, Z85 (history), D00-D09 excluded* | 365 | common | RD3, IX1 | yes | none |
| 71 | `metastatic_cancer` | oncology | Metastatic solid tumor (Charlson). *C77-C80* | 365 | common | IX1, IX2 | yes | none |
| 72 | `rheumatologic_disease` | systemic | Connective tissue / inflammatory arthritis (Charlson). *M05, M06, M32-M35, M45* | 365 | common | IX1 | yes | none |
| 73 | `charlson_index` | index | Charlson comorbidity index (Quan ICD-10 coding, 17 conditions). *Quan 2005 ICD-10 map* | 365 | core | KH1, OH2, KH2, AF1, IX1 | yes | none |
| 74 | `elixhauser_index` | index | Elixhauser comorbidities (AHRQ refined, 31-38 categories) or van Walraven score. *AHRQ Elixhauser ICD-10 map* | 365 | common | IX1 | yes | none |
| 75 | `combined_comorbidity_score` | index | Gagne combined Charlson-Elixhauser score (standard in RCT-DUPLICATE and Sentinel). *Gagne 2011 map* | 180 | core | RD3, RD4, RD5, SE1, IX2 | yes | none |
| 76 | `claims_frailty_index_kim` | index | Kim claims-based frailty index (93 items: 52 ICD, 25 CPT, 16 HCPCS). Segal indicator as an alternative. *Kim 2018 / Segal 2017 code lists* | 365 | common | RD3, RD4, RD5, IX5, IX6 | partial | approximated by v16 frailty_count (dx-only, 13 domains) |
| 77 | `hospital_frailty_risk_score` | index | Gilbert Hospital Frailty Risk Score (109 ICD-10 codes). OHDSI FeatureExtraction analysis 926. *Gilbert 2018 map* | 730 | occasional | IX7, OH2 | yes | none |
| 78 | `cardiovascular_risk_equation` | index | PREVENT / PCE / PCP-HF 10-y risk from age, sex, SBP, BP treatment, DM, smoking, lipids, eGFR, BMI. *component labs/vitals/dx* | 365 | occasional | KH10, KH14, IX10 | partial | none |
| 79 | `acei` | medication | Any order of ACE inhibitor in window (drug_exposure token match (first word of order), orders only). *captopril, enalapril, lisinopril, ramipril, benazepril, fosinopril, quinapril, perindopril, trandolapril, moexipril + brands* | 90 | core | RD3, RD4, KH1 | yes | PS-trial |
| 80 | `arb` | medication | Any order of ARB in window (drug_exposure token match (first word of order), orders only). *losartan, valsartan, candesartan, irbesartan, olmesartan, telmisartan, eprosartan, azilsartan* | 90 | core | RD3, RD4, KH1 | yes | PS-trial |
| 81 | `arni` | medication | Any order of ARNI in window (drug_exposure token match (first word of order), orders only). *sacubitril, entresto* | 90 | core | RD3 | yes | PS-trial (HF) |
| 82 | `beta_blocker` | medication | Any order of beta-blocker in window (drug_exposure token match (first word of order), orders only). *carvedilol, metoprolol, bisoprolol, atenolol, nebivolol, propranolol, labetalol, nadolol* | 90 | core | RD3, RD4, KH8 | yes | PS-trial |
| 83 | `mra` | medication | Any order of MRA in window (drug_exposure token match (first word of order), orders only). *spironolactone, eplerenone, finerenone* | 90 | core | RD3, RD4 | yes | PS-trial (HF) |
| 84 | `loop_diuretic` | medication | Any order of loop diuretic in window (drug_exposure token match (first word of order), orders only). *furosemide, bumetanide, torsemide, ethacrynic* | 90 | core | RD3, RD4 | yes | PS-trial |
| 85 | `thiazide` | medication | Any order of thiazide/thiazide-like in window (drug_exposure token match (first word of order), orders only). *hydrochlorothiazide, chlorthalidone, indapamide, metolazone* | 90 | common | RD3, RD4 | yes | PS-trial (some) |
| 86 | `ccb_dhp` | medication | Any order of dihydropyridine CCB in window (drug_exposure token match (first word of order), orders only). *amlodipine, nifedipine, felodipine, isradipine, nicardipine* | 90 | common | RD3 | yes | PS-trial (some) |
| 87 | `ccb_nondhp` | medication | Any order of non-DHP CCB in window (drug_exposure token match (first word of order), orders only). *diltiazem, verapamil* | 90 | common | RD3 | yes | PS-trial (AF) |
| 88 | `other_antihypertensive` | medication | Any order of other antihypertensive in window (drug_exposure token match (first word of order), orders only). *hydralazine, clonidine, minoxidil, doxazosin, terazosin, prazosin, methyldopa, aliskiren* | 90 | common | RD3 | yes | none |
| 89 | `nitrate` | medication | Any order of nitrate in window (drug_exposure token match (first word of order), orders only). *nitroglycerin, isosorbide* | 90 | common | RD3 | yes | none |
| 90 | `digoxin` | medication | Any order of digoxin in window (drug_exposure token match (first word of order), orders only). *digoxin, lanoxin* | 90 | common | RD3 | yes | PS-trial (HF) |
| 91 | `antiarrhythmic` | medication | Any order of antiarrhythmic in window (drug_exposure token match (first word of order), orders only). *amiodarone, dronedarone, sotalol, flecainide, propafenone, dofetilide* | 90 | common | RD3 | yes | PS-trial (AF, HF amiodarone) |
| 92 | `statin` | medication | Any order of statin in window (drug_exposure token match (first word of order), orders only). *atorvastatin, rosuvastatin, simvastatin, pravastatin, lovastatin, pitavastatin, fluvastatin + brands* | 90 | core | RD3, RD4, KH9, KH14 | yes | PS-trial (some) / held-out v16 |
| 93 | `nonstatin_lipid` | medication | Any order of non-statin lipid-lowering in window (drug_exposure token match (first word of order), orders only). *ezetimibe, evolocumab, alirocumab, inclisiran, fenofibrate, gemfibrozil, icosapent, bempedoic* | 90 | common | RD3, RD4 | yes | none |
| 94 | `aspirin` | medication | Any order of aspirin in window (drug_exposure token match (first word of order), orders only). *aspirin (OTC under-recorded)* | 90 | core | RD3, SE1 | partial | PS-trial (some) |
| 95 | `p2y12` | medication | Any order of P2Y12 inhibitor in window (drug_exposure token match (first word of order), orders only). *clopidogrel, prasugrel, ticagrelor* | 90 | core | RD3 | yes | PS-trial (AF) |
| 96 | `oral_anticoagulant` | medication | Any order of oral anticoagulant in window (drug_exposure token match (first word of order), orders only). *warfarin, apixaban, rivaroxaban, dabigatran, edoxaban* | 90 | core | RD3, RD4 | yes | PS-trial (some) |
| 97 | `metformin` | medication | Any order of metformin in window (drug_exposure token match (first word of order), orders only). *metformin* | 90 | core | RD3, RD4, KH3 | yes | PS-trial (DM) |
| 98 | `sulfonylurea` | medication | Any order of sulfonylurea in window (drug_exposure token match (first word of order), orders only). *glipizide, glimepiride, glyburide* | 90 | common | RD3, RD4 | yes | PS-trial (DM) |
| 99 | `dpp4i` | medication | Any order of DPP-4 inhibitor in window (drug_exposure token match (first word of order), orders only). *sitagliptin, linagliptin, saxagliptin, alogliptin* | 90 | common | RD3, RD4 | yes | arm in some trials |
| 100 | `glp1ra` | medication | Any order of GLP-1 RA / GIP-GLP-1 in window (drug_exposure token match (first word of order), orders only). *semaglutide, liraglutide, dulaglutide, exenatide, tirzepatide* | 90 | core | RD3, RD4, KH3, KH5 | yes | none |
| 101 | `sglt2i` | medication | Any order of SGLT2 inhibitor in window (drug_exposure token match (first word of order), orders only). *empagliflozin, dapagliflozin, canagliflozin, ertugliflozin, sotagliflozin* | 90 | core | RD3, RD4, KH3 | yes | PS-trial (HF) |
| 102 | `insulin` | medication | Any order of insulin in window (drug_exposure token match (first word of order), orders only). *insulin + brands* | 90 | core | RD3, RD4 | yes | PS-trial (ACS, DM) |
| 103 | `nsaid` | medication | Any order of NSAID in window (drug_exposure token match (first word of order), orders only). *ibuprofen, naproxen, meloxicam, diclofenac, celecoxib, ketorolac, indomethacin* | 90 | common | RD3, SE1, IX4 | partial | PS-trial (AF) |
| 104 | `ppi` | medication | Any order of proton-pump inhibitor in window (drug_exposure token match (first word of order), orders only). *omeprazole, pantoprazole, esomeprazole, lansoprazole, rabeprazole* | 90 | common | RD3 | yes | PS-trial (ACS) |
| 105 | `oral_corticosteroid` | medication | Any order of systemic corticosteroid in window (drug_exposure token match (first word of order), orders only). *prednisone, methylprednisolone, dexamethasone, hydrocortisone* | 90 | common | RD3, RD4 | yes | none |
| 106 | `opioid` | medication | Any order of opioid in window (drug_exposure token match (first word of order), orders only). *oxycodone, hydrocodone, morphine, tramadol, hydromorphone, fentanyl, methadone* | 90 | common | RD3, RD4 | yes | none |
| 107 | `antidepressant` | medication | Any order of antidepressant in window (drug_exposure token match (first word of order), orders only). *sertraline, citalopram, escitalopram, fluoxetine, paroxetine, venlafaxine, duloxetine, bupropion, mirtazapine, trazodone* | 90 | common | RD3 | yes | none |
| 108 | `antipsychotic_or_hypnotic` | medication | Any order of antipsychotic, benzodiazepine or hypnotic in window (drug_exposure token match (first word of order), orders only). *quetiapine, olanzapine, risperidone, haloperidol, aripiprazole, lorazepam, alprazolam, clonazepam, diazepam, zolpidem* | 90 | common | RD3 | yes | none |
| 109 | `copd_asthma_inhaler` | medication | Any order of inhaled bronchodilator / ICS in window (drug_exposure token match (first word of order), orders only). *albuterol, tiotropium, fluticasone, budesonide, salmeterol, formoterol, umeclidinium* | 90 | common | RD3 | yes | none |
| 110 | `n_distinct_drug_ingredients` | polypharmacy | Number of distinct drug ingredients (tokens) ordered. *drug_exposure token match (first word of order), orders only* | 365 | core | RD3, RD4, SE1 | yes | none |
| 111 | `n_inpatient_admissions` | utilisation | Number of inpatient admissions. *visit 9201* | 365 | core | RD3, RD4, SE1, KH2 | yes | PS-core |
| 112 | `inpatient_days` | utilisation | Inpatient days / LOS. *visit 9201 stays* | 365 | common | RD3, RD4 | yes | held-out v16 |
| 113 | `recent_hospitalization_30d` | utilisation | Any hospitalization in the 30 days before index (vs 31-180). *visit 9201* | 30 | common | RD3 | yes | none |
| 114 | `n_ed_visits` | utilisation | Number of ED visits. *visit 9203* | 365 | core | RD3, RD4, SE1 | yes | PS-core |
| 115 | `n_outpatient_visits` | utilisation | Number of outpatient visits. *visit 9202* | 365 | core | RD3, SE1 | yes | PS-core |
| 116 | `n_cardiology_visits` | utilisation | Cardiology visits (specialist engagement). *Epic outpatient_enc DEPARTMENT_NAME / VISIT_PROV_TYPE* | 365 | common | RD3, RD4 | partial | none |
| 117 | `n_pcp_visits` | utilisation | Internal/family medicine visits. *Epic outpatient_enc DEPARTMENT_NAME* | 365 | common | RD3, RD4 | partial | none |
| 118 | `n_ecgs` | diagnostic testing | Number of ECGs (ECG-proximal). *MUSE ECG metadata; CPT 93000-93010* | 365 | common | RD3 | yes | none |
| 119 | `n_echos` | diagnostic testing | Number of echocardiograms. *echo metadata; CPT 93303-93356* | 365 | common | RD3 | yes | held-out phys (echo_done only) |
| 120 | `ischemia_testing_or_cath` | diagnostic testing | Stress test, nuclear MPI, coronary CTA, diagnostic cath. *CPT 93015-93018, 78451-78454, 75574, 93454-93461* | 365 | common | RD3 | yes | none |
| 121 | `lab_test_intensity` | diagnostic testing | Number of distinct lab tests / HbA1c or lipid panel ordered (surveillance intensity). *measurement concept counts* | 365 | common | OH2, RD4 | yes | none |
| 122 | `influenza_vaccination` | healthy user | Influenza vaccine (healthy-adherer proxy). *CPT 90653-90689, 90756; Z23; drug token influenza/fluzone* | 365 | common | RD3, RD5 | partial | none |
| 123 | `cancer_screening` | healthy user | Colonoscopy, mammography, PSA, bone densitometry. *CPT 45378-45398, 77065-77067, 84152-84154, 77080* | 730 | common | RD3 | yes | none |
| 124 | `discharge_to_facility_or_home_health` | utilisation | Most recent discharge to SNF / rehab / home health (functional dependence proxy). *Epic hosp_enc DISCH_DISP* | 365 | occasional | - | partial | none |
| 125 | `durable_medical_equipment` | frailty | Wheelchair, hospital bed, walker, home oxygen (Kim CFI HCPCS items). *HCPCS E0100-E0159, E0250-E0304, E1130-E1161, E1390* | 365 | occasional | IX5 | partial | none (DME HCPCS sparse in gold) |
| 126 | `sbp` | vitals | Latest systolic BP. *measurement 4152194* | 90 | core | KH8, KH9, KH10, UK1, IX10 | yes | core (withheld from claims-like PS) |
| 127 | `dbp` | vitals | Latest diastolic BP. *measurement 3012888* | 90 | common | KH8 | yes | core (withheld from claims-like PS) |
| 128 | `heart_rate` | vitals | Latest heart rate (ECG-proximal). *measurement 3027018* | 90 | common | KH8, KH9 | yes | core (withheld from claims-like PS) |
| 129 | `creatinine` | laboratory | Serum creatinine (latest value in window, index day excluded; OMOP measurement concept). *3016723* | 90 | core | RD3, RD4, UK1 | yes | core (withheld from claims-like PS) |
| 130 | `egfr` | laboratory | eGFR CKD-EPI (latest value in window, index day excluded; OMOP measurement concept). *40764999* | 90 | core | KH8, KH9, RD4, UK1, IX10 | yes | held-out phys |
| 131 | `potassium` | laboratory | Potassium (latest value in window, index day excluded; OMOP measurement concept). *3023103* | 90 | common | RD3 | yes | core (withheld from claims-like PS) |
| 132 | `sodium` | laboratory | Sodium (latest value in window, index day excluded; OMOP measurement concept). *3019550* | 90 | common | RD3 | yes | core (withheld from claims-like PS) |
| 133 | `bun` | laboratory | BUN (latest value in window, index day excluded; OMOP measurement concept). *3013682* | 90 | common | RD3 | yes | held-out phys |
| 134 | `hemoglobin` | laboratory | Hemoglobin (latest value in window, index day excluded; OMOP measurement concept). *3000963* | 90 | common | RD3, KH8 | yes | core (withheld from claims-like PS) |
| 135 | `hba1c` | laboratory | HbA1c (latest value in window, index day excluded; OMOP measurement concept). *3004410* | 365 | core | RD3, RD4, RD6, IX10 | yes | held-out phys |
| 136 | `glucose` | laboratory | Glucose (latest value in window, index day excluded; OMOP measurement concept). *3004501* | 90 | occasional | RD3, KH10 | yes | held-out phys |
| 137 | `ldl_c` | laboratory | LDL-C (latest value in window, index day excluded; OMOP measurement concept). *3028288* | 365 | common | RD3, RD4, KH14 | yes | held-out phys |
| 138 | `hdl_tc_tg` | laboratory | HDL-C, total cholesterol, triglycerides (latest value in window, index day excluded; OMOP measurement concept). *3007070, 3027114, 3022192* | 365 | common | RD3, RD4, KH14, UK1 | yes | none |
| 139 | `natriuretic_peptide` | laboratory | NT-proBNP (BNP separately, do not pool) (latest value in window, index day excluded; OMOP measurement concept). *3029187; BNP 3011960* | 365 | core | RD3, KH8 | yes | held-out phys (NT-proBNP) |
| 140 | `troponin` | laboratory | hs-TnT / TnI (latest value in window, index day excluded; OMOP measurement concept). *40769783, 3021337, 3019800* | 90 | occasional | KH8 | yes | held-out phys (hs-TnT) |
| 141 | `albumin` | laboratory | Serum albumin (latest value in window, index day excluded; OMOP measurement concept). *3024561* | 90 | common | RD3 | yes | held-out phys |
| 142 | `liver_panel` | laboratory | ALT, AST, total bilirubin, alkaline phosphatase (latest value in window, index day excluded; OMOP measurement concept). *3006923, 3013721, 3024128, 3035995* | 180 | occasional | KH8 | yes | none |
| 143 | `platelets_wbc` | laboratory | Platelets, WBC (latest value in window, index day excluded; OMOP measurement concept). *3024929, 3000905* | 90 | occasional | KH8 | yes | held-out phys |
| 144 | `inr` | laboratory | INR (arm-leaking for warfarin comparisons; use only as a pre-exposure value or as HAS-BLED labile INR) (latest value in window, index day excluded; OMOP measurement concept). *3022217* | 90 | common | AF1, IX4 | yes | none |
| 145 | `uacr` | laboratory | Urine albumin-creatinine ratio (latest value in window, index day excluded; OMOP measurement concept). *not in the 83 gold measurement concepts* | 365 | common | RD4, IX10 | no | none |
| 146 | `lab_measured_flags` | laboratory | Indicator that each key lab (NT-proBNP, HbA1c, lipids, TSH, INR, troponin) was measured in the window. LEGEND-T2DM enters measurements as status, not value. *measurement concept presence* | 365 | common | KH4, OH2, RD3 | yes | none |
| 147 | `lvef` | cardiac structure | Latest echo LVEF. *echo metadata EF 5-90* | 365 | core | KH7, KH8, RD3 | yes | core (withheld from claims-like PS) |
| 148 | `echo_structure_panel` | cardiac structure | LV wall thickness/mass, LA volume, diastolic grade, RVSP, TAPSE, valve grades. *echo_metadata_2026_06_12 structured columns* | 365 | occasional | KH8 | yes | held-out phys |
| 149 | `nyha_class` | functional status | NYHA class from notes (NLP). *clinical notes (NLP; notes 2021+ only)* | 365 | core | KH13, RD3 | partial | none |
| 150 | `empirical_hdps_codes` | empirical | Top-k empirical codes per data dimension (dx, procedures, drugs, labs) ranked by Bross bias. Not a single covariate; a balance-panel family. *hdPS dimensions* | 365 | common | HD1, HD2, OH2, KH2, RD4, RD7 | yes | PS (hdPS arms) |

Summary: 150 candidates. By priority: 56 core, 83 common, 11 occasional. By Yale availability: 131 yes, 15 partial,
4 no.

---

## 5. Gaps vs the current panel, and cautions

**Top gaps.** These are core or common, computable now, and not yet built. The list is ordered by how often the
literature uses them.
1. **Comorbidity indices.** Charlson (Quan ICD-10), Gagne combined comorbidity score and Elixhauser. They are
   standard in RCT-DUPLICATE, Sentinel, EMPRISE, ARISTOPHANES, OHDSI and Khera 2021. None is built, and all can be
   computed from ICD-10.
2. **AF-trial risk scores.** CHA2DS2-VASc (plus CHADS2) and claims-modified HAS-BLED. These are OHDSI defaults and
   standard in DOAC studies. We have the components but not the scores. HAS-BLED labile INR needs INR history.
3. **Validated frailty index.** Kim CFI or Segal, instead of the 13-domain dx count. The CFI's HCPCS DME items are
   sparse in gold, so it is partial. The HFRS (109 ICD-10 codes) is a fully dx-based alternative.
4. **The RCT-DUPLICATE "other comorbidity" block.** Dementia, depression, anxiety, SMI, cancer (incl.
   metastatic), liver disease (only in AF trials now), anemia, coagulopathy, AKI, CKD stage, ESKD/dialysis,
   hyperkalemia, fluid/electrolyte disorders, thyroid disease, OSA, recent pneumonia, alcohol/drug use disorder,
   osteoporosis/fracture, falls.
5. **CV-history detail.** Prior MI (currently pooled into IHD), prior PCI/CABG in all trials, cardiac devices,
   cardiomyopathy, pulmonary hypertension, prior valve procedure, VTE history, other arrhythmias, and the
   HFrEF/HFpEF code split.
6. **Non-CV drug classes and polypharmacy.** Opioids, oral steroids, antidepressants, antipsychotics/hypnotics,
   inhalers, nitrates, non-statin lipid drugs, other antihypertensives, and the **number of distinct drug
   ingredients**. The count is standard in Sentinel and RCT-DUPLICATE and is one of the strongest surveillance
   proxies.
7. **Care-intensity and healthy-user markers.**
   - hospitalisation in the last 30 days
   - cardiology and PCP visit counts (Epic department)
   - ECG, echo and ischemia-testing counts
   - lab-test intensity and lab-measured flags (LEGEND style)
   - flu vaccination, colonoscopy/mammogram/BMD
   - discharge to SNF or home health
8. **Administrative context.** Site/campus (Khera TOPCAT used YNHHS campuses; claims studies use region),
   index-day setting (inpatient vs outpatient initiation) and prior observation time.
9. **Labs not yet on the panel.** HDL/TC/TG, INR, liver panel, TSH, CRP. UACR is **not available** in gold.
10. **SES.**
    - ADI/SVI/ZIP income is partial: a ZIP/ZCTA file needs to be supplied, and only the current address is known.
    - Insurance/payer, dual status, language and marital status are **not available** in the current extract.
    - These are the most-cited residual-confounding domains, so a JDAT pull of Epic coverage/payer and
      language fields is worth requesting.

**Cautions for using these as *held-out* balance variables:**
- **Design-relative held-out status.**
  - In hdPS / sparse-code PS designs, the empirical code features may already contain the dx codes behind
    dementia, cancer, CKD stage and similar variables. For each design, report which held-out variables share
    codes with that design's PS feature set. A variable is "held out" only if none of its defining codes (or its
    parent roll-ups) entered that PS.
  - PS-trial variables are held out only in the trials that do not use them.
- **ECG-proximal variables.** Heart rate, AF/flutter, conduction disorders, LVH, cardiomyopathy and ECG counts are
  partly visible to the embedding. Improved balance on them is expected and does not show recovery of unmeasured
  confounding. Report them as a separate block from "ECG-distal" variables (SES, frailty, psych, cancer,
  healthy-user, labs such as HbA1c, lipids and albumin).
- **Arm-leaking variables.**
  - INR in warfarin-comparator trials.
  - Aspirin/NSAID orders (OTC under-capture).
  - Statin in trials where it is part of the PS.
  - Prior use of a class in its own arm's washout.

  Exclude these per trial, as `exposure_features` in `roles.json` already does for drug tokens.
- **Window alignment.** OHDSI FeatureExtraction defaults (`endDays = 0`) include the index day. RCT-DUPLICATE uses
  180 days, 30 days vs 31–180 days, and 365 days for frailty. Keep our index-day exclusion, and record the
  alternative windows when comparing with the literature.
- **Missingness as information.** For labs, add the "measured" flag next to the value (the LEGEND approach [KH4]),
  so that balance on testing intensity is assessed separately from balance on values.

---

## 6. References

Khera lab
- [KH1] Khera R, Clark C, Lu Y, et al. *J Am Heart Assoc* 2021;10:e018086. PMID 33624516. https://pmc.ncbi.nlm.nih.gov/articles/PMC8403305/
- [KH2] Khera R, Schuemie MJ, Lu Y, et al. LEGEND-T2DM protocol. *BMJ Open* 2022. PMID 35680274. https://pmc.ncbi.nlm.nih.gov/articles/PMC9185490/ ; protocol site https://ohdsi-studies.github.io/LegendT2dm/Protocol.html
- [KH3] Khera R, Aminorroaya A, Dhingra LS, et al. *J Am Coll Cardiol* 2024. PMID 39197980. https://pmc.ncbi.nlm.nih.gov/articles/PMC12045554/
- [KH4] Kim C, et al. (LEGEND-T2DM older adults). *Nat Commun* 2026. PMID 41935054. https://www.nature.com/articles/s41467-026-71307-0
- [KH5] Bu F, et al. GLP-1RA vs SGLT2i. *J Am Coll Cardiol* 2026. PMID 41984016. https://www.jacc.org/doi/10.1016/j.jacc.2026.02.5123 ; preprint https://www.medrxiv.org/content/10.64898/2026.02.23.26346890v1.full
- [KH6] Khera R, et al. Multinational patterns of second-line initiation (LEGEND-T2DM). *BMJ Med* 2023. PMID 37829182
- [KH7] Biswas D, Dhingra LS, Aminorroaya A, Croon PM, Oikonomou EK, Khera R. DISCO. *Eur Heart J* 2025;46(Suppl 1):ehaf784.4614. https://academic.oup.com/eurheartj/article/46/Supplement_1/ehaf784.4614/8308217
- [KH8] Thangaraj PM, et al. *Circ Cardiovasc Qual Outcomes* 2025. PMID 40261065. https://pmc.ncbi.nlm.nih.gov/articles/PMC12203226/
- [KH9] Thangaraj PM, Shankar SV, Huang S, Nadkarni GN, Mortazavi BJ, Oikonomou EK, Khera R. *npj Digit Med* 2026. PMID 41794982
- [KH10] Dhingra LS, et al. *Eur Heart J* 2025. PMID 39804243. https://doi.org/10.1093/eurheartj/ehae914
- [KH11] Dhingra LS, et al. PRESENT-SHD. *J Am Coll Cardiol* 2025. PMID 40139886. https://doi.org/10.1016/j.jacc.2025.01.030
- [KH12] Croon PM, Dhingra LS, Biswas D, Oikonomou EK, Khera R. *Circulation* 2025. PMID 40888124
- [KH13] Adejumo P, Thangaraj PM, et al. *JAMA Netw Open* 2024. PMID 39509128
- [KH14] Aminorroaya A, et al. *Circ Genom Precis Med* 2025. PMID 39846171
- [KH15] Dhingra LS, et al. *Am J Prev Cardiol* 2026. PMID 41767452
- [KH16] Lu Y, et al. *JAMA Netw Open* 2025. PMID 40779264
- [KH17] Dhingra LS, et al. *Am J Cardiol* 2025. PMID 39581517

RCT-DUPLICATE / Schneeweiss group
- [RD1] Franklin JM, Patorno E, Desai RJ, et al. *Circulation* 2021;143:1002. PMID 33327727. https://pmc.ncbi.nlm.nih.gov/articles/PMC7940583/
- [RD2] Wang SV, Schneeweiss S, et al. *JAMA* 2023;329:1376. PMID 37097356. https://pmc.ncbi.nlm.nih.gov/articles/PMC10130954/
- [RD3] RCT-DUPLICATE registered protocols with covariate/balance appendices. PARADIGM-HF NCT04736433 (main source for the covariate list). Also ARISTOTLE NCT04593030, PLATO NCT04237935, ONTARGET NCT04354350, EMPA-REG NCT04215536, ROCKET-AF NCT04593056, RE-LY NCT04593043, TRITON NCT04237922. PDFs at https://cdn.clinicaltrials.gov/large-docs/<last2>/<NCT>/Prot_SAP_00x.pdf
- [RD4] Htoo PT, Tesfaye H, Schneeweiss S, et al. EMPRISE final results. *Cardiovasc Diabetol* 2024. PMID 38331813. https://pmc.ncbi.nlm.nih.gov/articles/PMC10854040/
- [RD5] Patorno E, et al. EMPRISE HHF. *Circulation* 2019. PMID 30955357. https://pmc.ncbi.nlm.nih.gov/articles/PMC6594384/
- [RD6] Patorno E, et al. *Diabetes Obes Metab* 2018. PMID 29206336 (claims PS balances EHR-only HbA1c/BMI/eGFR/BP/smoking)
- [RD7] Weckstein AR, Wang SV, Wyss R, Schneeweiss S. Data-adaptive vs investigator-specified adjustment, 15 emulations. *JAMIA* 2026. PMID 41338229

OHDSI / Sentinel / hdPS
- [OH1] Suchard MA, et al. LEGEND-HTN. *Lancet* 2019. PMID 31668726
- [OH2] OHDSI FeatureExtraction, `createDefaultCovariateSettings` and `inst/csv/PrespecAnalyses.csv` (analyses 901–904 Charlson/DCSI/CHADS2/CHA2DS2-VASc, 926 HFRS, 905–925 distinct/visit counts). https://github.com/OHDSI/FeatureExtraction
- [SE1] Sentinel propensity-score tools: Mini-Sentinel PSM tool report https://www.sentinelinitiative.org/sites/default/files/Methods/Mini-Sentinel_Methods_Propensity-Score-Matching-Tool-Enhancements-Report_0.pdf ; routine querying documentation https://www.sentinelinitiative.org/sites/default/files/surveillance-tools/routine-querying/Sentinel-Routine_Querying_System-Documentation_7.0.0.pdf. Default covariates per the search summary: age, sex, combined comorbidity score, inpatient/institutional/ED/ambulatory visit counts, dispensings, unique generics, unique classes **[unverified against the PDF text]**
- [HD1] Schneeweiss S, et al. *Epidemiology* 2009. PMID 19487948
- [HD2] Rassen JA, et al. hdPS planning/reporting. *Pharmacoepidemiol Drug Saf* 2023. https://pmc.ncbi.nlm.nih.gov/articles/PMC10099872/

Other emulations
- [AF1] Lip GYH, et al. ARISTOPHANES. *Stroke* 2018. PMID 30571400. https://pmc.ncbi.nlm.nih.gov/articles/PMC6257512/
- [UK1] Fan Z, Yang Q, Hu Y, Danaei G, Davey Smith G, Rao S, Rahimi K. Bias in HF TTE across statistical and DL methods (CPRD Aurum, 39 prespecified covariates including IMD, smoking, BMI, SBP, eGFR, cholesterol). *Nat Commun* 2026. PMID 42443168. https://pmc.ncbi.nlm.nih.gov/articles/PMC13486677/

Indices / SDOH
- [IX1] Quan H, et al. Charlson/Elixhauser ICD-10 coding. *Med Care* 2005. PMID 16224307
- [IX2] Gagne JJ, Glynn RJ, Avorn J, Levin R, Schneeweiss S. Combined comorbidity score. *J Clin Epidemiol* 2011. PMID 21208778
- [IX3] Lip GY, et al. CHA2DS2-VASc. *Chest* 2010. PMID 19762550
- [IX4] Pisters R, et al. HAS-BLED. *Chest* 2010. PMID 20299623
- [IX5] Kim DH, et al. Claims-based frailty index. *J Gerontol A* 2018. PMID 29244057
- [IX6] Segal JB, et al. Claims-based frailty indicator. *Med Care* 2017. PMID 28437320
- [IX7] Gilbert T, et al. Hospital Frailty Risk Score. *Lancet* 2018. PMID 29706364
- [IX8] Young BA, et al. DCSI. *Am J Manag Care* 2008. PMID 18197741
- [IX9] Kind AJH, Buckingham WR. Neighborhood Atlas / ADI. *N Engl J Med* 2018. PMID 29949490
- [IX10] Khan SS, et al. PREVENT equations. *Circulation* 2024. PMID 37947085 (the model also offers an optional SDI term **[unverified]**)
- Operational TTE framework in EHR (confounders commonly missing from structured EHR: severity, functional status, frailty, SDOH). *npj Digit Med* 2026. https://www.nature.com/articles/s41746-026-02563-z
