# Structured literature search for emulable cardiovascular RCTs: protocol

Written 2026-10-13, **before any search was run**. Study: LATENT-RCT (formerly TRACE-ECG).

The execution record (queries as run, dates, hit counts, screening tallies, deviations) is in [SEARCH_LOG.md](SEARCH_LOG.md). The results are in [CANDIDATES.md](CANDIDATES.md) and [candidates.json](candidates.json).

## 1. Purpose and scope

The search has two aims:
1. **Coverage check.** Estimate how much of the eligible trial literature the project's existing candidate pool already covers. The pool is the 99 candidates of eMethods 3.
2. **New candidates.** List eligible trials that are not yet in the pool, as a separate **exploratory set** that the user may add later.

The search does **not** change the current analysed set (pipeline.md §2), the 38 emulated trials, or any registered specification.

Constraints:
- **Literature only.** No patient data is read. No count, feasibility or data screen is run. Any feasibility judgement here is a design-level expectation, to be tested later by the project's count-only screen (eMethods 3: ≥300 patients with an ECG in the smaller arm, ≥50 pooled events, <80% record overlap with an existing cohort).
- **Web privacy.** Requests go only to public pages and public APIs that need no key and no e-mail:
  - PubMed E-utilities without the optional `email`/`api_key` parameters;
  - the ClinicalTrials.gov API v2;
  - journal and PubMed abstract pages;
  - public web search.

  No user name, e-mail or other identifier is placed in any URL, header or parameter.

## 2. Eligibility criteria

The criteria are derived from the project's feasibility criteria (eMethods 2–3; quality framework v2.0, `docs/emulation_quality_v2/QUALITY_FRAMEWORK.md`).

| # | Criterion | Eligible when |
|---|---|---|
| E1 | Design | Randomized controlled trial; parallel-group, factorial or pragmatic/registry-based. Cluster and crossover designs are eligible only if individual treatment assignment is identifiable (otherwise recorded as ineligible). |
| E2 | Population | Adults (≥18 y) with a cardiovascular condition, or a cardiometabolic or other condition (e.g. T2D, arthritis, gout) where the trial's primary endpoint is a hard CV endpoint. |
| E3 | Comparator | One of: (a) an **active comparator** (drug vs drug, procedure vs procedure); (b) a **strategy comparison** implementable with the project's existing designs: new-user, sequential add-on/switch vs continuation (`switch_seq`, as EAST-AFNET 4, FRAIL-AF, PROTECT AF), or a procedure add-on vs none within a common procedure (LAAOS III); (c) **placebo-controlled with an accepted proxy**, i.e. the RCT-DUPLICATE convention of a DPP-4 inhibitor or sulfonylurea for glucose-lowering drugs, or another active comparator with no expected effect on the outcome that is stated explicitly (scored CO = 2). Placebo-only trials with no defensible proxy are **ineligible** (reason P). |
| E4 | Strategies identifiable | Drug, device or procedure identifiable from EHR orders, CPT/HCPCS or ICD-10-PCS codes, **and** in use in US practice during 2011–2024 (the YNHHS index window). Excluded if the hypothesis depends on a feature that cannot be identified (reason X):<br>- OTC aspirin as an arm-defining therapy;<br>- dose or intensity contrasts where dose is not encoded in the drug token;<br>- device brand;<br>- treat-to-target strategies;<br>- vascular access site. |
| E5 | Endpoint ascertainable | Primary endpoint mapped to EHR events:<br>- all-cause or cause-specific death (state death records with causes);<br>- MI, stroke, systemic embolism, HF, VTE or major bleeding hospitalisation;<br>- coded procedures (revascularisation, amputation, reintervention).<br>Excluded (reason O) when the dominant component needs one of:<br>- rhythm monitoring (AF recurrence);<br>- imaging surveillance (venography, MRI-covert infarcts);<br>- functional scales (mRS, NYHA, KCCQ, 6MWD);<br>- surrogate biomarkers (HbA1c, BP, NT-proBNP, LDL, eGFR slope);<br>- in-hospital or peri-procedural events within the index stay only.<br>Endpoints that are ascertainable with a stated loss (e.g. CRNM bleeding, outpatient VTE) are eligible with an OU flag. |
| E6 | Size | Randomized N ≥ 1,000, **or** a high-impact landmark trial: cited as a class I/IIa evidence source in a current ACC/AHA or ESC guideline, or published in NEJM/Lancet/JAMA with a hard primary endpoint (reason S if neither). |
| E7 | Publication | Primary results published in a peer-reviewed journal 1995-01-01 to 2025-12-31, with a reported primary effect estimate. An HR is preferred; an RR, OR, sHR or risk difference is eligible with a BM flag. |
| E8 | Benchmark direction (not an eligibility criterion) | Recorded for Group C: superiority shown (95% CI excluding 1) or harm shown. |

Exclusion reasons, one primary reason per record at full-text stage:
- **P:** placebo without proxy;
- **X:** strategy not identifiable, or not used in 2011–2024 US practice;
- **O:** endpoint not ascertainable;
- **N:** population not identifiable from structured data (e.g. genotype, device-detected subclinical AF, ESUS, frailty scales, CYP2C19 carriers);
- **S:** size or impact;
- **D:** design (crossover/cluster without individual assignment; de-escalation without an identifiable decision point; non-randomized);
- **Q:** secondary or duplicate publication of a trial already counted;
- **R:** retracted or under expression of concern.

## 3. Information sources

1. **PubMed** (E-utilities `esearch`/`esummary`), area-specific queries (§4). Each query is restricted to:
   - publication type Randomized Controlled Trial;
   - six journals (NEJM, Lancet, JAMA, J Am Coll Cardiol, Circulation, Eur Heart J);
   - 1995–2025;
   - a hard-endpoint term;
   - exclusion of common secondary-analysis title terms.

   This makes the journal-restricted search and the PubMed search one step. Trials in other journals are reached through sources 2–4.
2. **ClinicalTrials.gov** API v2: interventional, randomized, Phase 3/4, enrollment ≥1,000, CV conditions, start date 1995–2022. This source identifies registered large trials by acronym and title, and is used to find trials missed by the journal restriction.
3. **RCT-DUPLICATE** trial list: the 32 trials of Wang et al. JAMA 2023 (PMID 37097356) and the 10 of Franklin et al. Circulation 2021 (PMID 33327727). Read from the PMC full text or abstract.
4. **Guideline-cited landmark trials.** A hand search of trials cited as the evidence basis of class I/IIa recommendations. Guidelines:
   - 2023 ACC/AHA/ACCP/HRS AF;
   - 2024 ESC AF;
   - 2022 AHA/ACC/HFSA HF and 2021/2023 ESC HF;
   - 2023 ESC ACS and 2025 ACC/AHA ACS;
   - 2023 AHA/ACC chronic coronary disease;
   - 2017 ACC/AHA and 2024 ESC hypertension;
   - 2018 AHA/ACC cholesterol;
   - 2020 ACC/AHA and 2021 ESC valvular heart disease;
   - 2019 ESC PE and 2021 CHEST VTE;
   - 2024 ACC/AHA PAD;
   - 2021 AHA/ASA secondary stroke prevention;
   - ADA Standards of Care 2025 (CV section).

   Hand-searched trials are verified individually on PubMed.
5. **Snowballing.** Trials named in the project's own screening lists that point to sibling trials (e.g. design-variant arms, same-question trials) are checked.

Not used: Embase and CENTRAL (no institution-free access), and any API that needs an e-mail or key.

## 4. PubMed query strings (as planned; the log records the strings as executed)

Common blocks:
- `RCT` = `"Randomized Controlled Trial"[pt]`
- `JRN` = `("N Engl J Med"[ta] OR "Lancet"[ta] OR "JAMA"[ta] OR "J Am Coll Cardiol"[ta] OR "Circulation"[ta] OR "Eur Heart J"[ta])`
- `DT` = `("1995/01/01"[dp] : "2025/12/31"[dp])`
- `HARD` = `(mortality[tiab] OR death[tiab] OR "myocardial infarction"[tiab] OR stroke[tiab] OR hospitalization[tiab] OR hospitalisation[tiab] OR bleeding[tiab] OR embolism[tiab] OR "cardiovascular events"[tiab] OR "cardiovascular outcomes"[tiab] OR "major adverse"[tiab])`
- `NOTSEC` = `NOT ("post hoc"[ti] OR "secondary analysis"[ti] OR subgroup*[ti] OR substudy[ti] OR "sub-study"[ti] OR "insights from"[ti] OR rationale[ti] OR "design and"[ti] OR "baseline characteristics"[ti] OR "cost-effectiveness"[ti] OR "quality of life"[ti] OR "pharmacokinetic*"[ti] OR "meta-analysis"[ti] OR "patient-level"[ti] OR "pooled analysis"[ti])`

Area queries: `RCT AND JRN AND DT AND HARD AND <AREA> NOTSEC`

| ID | Area | `<AREA>` |
|---|---|---|
| Q1 | AF / anticoagulation | `("atrial fibrillation"[ti] OR anticoagula*[ti] OR warfarin[ti] OR apixaban[ti] OR rivaroxaban[ti] OR dabigatran[ti] OR edoxaban[ti] OR "left atrial appendage"[ti])` |
| Q2 | HF and devices | `("heart failure"[ti] OR "ventricular dysfunction"[ti] OR "ejection fraction"[ti] OR cardiomyopathy[ti] OR resynchronization[ti] OR defibrillator*[ti] OR pacing[ti] OR pacemaker*[ti])` |
| Q3 | Hypertension | `(hypertension[ti] OR hypertensive[ti] OR "blood pressure"[ti] OR antihypertensive[ti])` |
| Q4 | Diabetes / cardiometabolic | `(diabetes[ti] OR diabetic[ti] OR glucose-lowering[ti] OR liraglutide[ti] OR semaglutide[ti] OR dulaglutide[ti] OR exenatide[ti] OR tirzepatide[ti] OR empagliflozin[ti] OR dapagliflozin[ti] OR canagliflozin[ti] OR ertugliflozin[ti] OR pioglitazone[ti] OR rosiglitazone[ti] OR sitagliptin[ti] OR saxagliptin[ti] OR linagliptin[ti] OR alogliptin[ti] OR obesity[ti] OR "kidney disease"[ti])` |
| Q5 | ACS / CAD / antiplatelet / revascularisation | `("coronary"[ti] OR "myocardial infarction"[ti] OR "acute coronary"[ti] OR angioplasty[ti] OR stent*[ti] OR bypass[ti] OR antiplatelet[ti] OR clopidogrel[ti] OR ticagrelor[ti] OR prasugrel[ti] OR bivalirudin[ti] OR revasculari*[ti] OR "beta-blocker*"[ti])` |
| Q6 | Lipids | `(statin*[ti] OR cholesterol[ti] OR lipid*[ti] OR atorvastatin[ti] OR rosuvastatin[ti] OR simvastatin[ti] OR pravastatin[ti] OR ezetimibe[ti] OR PCSK9[ti] OR evolocumab[ti] OR alirocumab[ti] OR icosapent[ti] OR "omega-3"[ti] OR "fatty acids"[ti] OR fenofibrate[ti] OR niacin[ti] OR "bempedoic"[ti])` |
| Q7 | VTE | `("venous thromboembolism"[ti] OR "venous thrombosis"[ti] OR "deep vein thrombosis"[ti] OR "deep-vein thrombosis"[ti] OR "pulmonary embolism"[ti] OR thromboprophylaxis[ti])` |
| Q8 | Valve / structural | `("aortic stenosis"[ti] OR "aortic valve"[ti] OR "aortic-valve"[ti] OR transcatheter[ti] OR mitral[ti] OR tricuspid[ti] OR "patent foramen ovale"[ti])` |
| Q9 | Stroke / carotid / peripheral / aortic | `(stroke[ti] OR "ischemic attack"[ti] OR carotid[ti] OR "peripheral artery"[ti] OR "peripheral arterial"[ti] OR "limb ischemia"[ti] OR "limb-threatening"[ti] OR aneurysm[ti])` |
| Q10 | Other CV safety / vaccines | `("cardiovascular safety"[ti] OR celecoxib[ti] OR NSAID*[ti] OR "anti-inflammatory"[ti] OR febuxostat[ti] OR testosterone[ti] OR influenza[ti] OR vaccin*[ti] OR colchicine[ti] OR "sleep apnea"[ti])` |

Deduplication is by PMID across queries.

## 5. ClinicalTrials.gov query (API v2)

- **Endpoint:** `https://clinicaltrials.gov/api/v2/studies`.
- **Parameters:**
  - `query.cond` = `cardiovascular OR "atrial fibrillation" OR "heart failure" OR hypertension OR "coronary artery disease" OR "myocardial infarction" OR "acute coronary syndrome" OR stroke OR "venous thromboembolism" OR "pulmonary embolism" OR "aortic stenosis" OR "peripheral arterial disease" OR "type 2 diabetes"`
  - `filter.advanced` = `AREA[StudyType]INTERVENTIONAL AND AREA[DesignAllocation]RANDOMIZED AND (AREA[Phase]PHASE3 OR AREA[Phase]PHASE4) AND AREA[EnrollmentCount]RANGE[1000, MAX] AND AREA[StartDate]RANGE[1995-01-01, 2022-12-31]`
  - `filter.overallStatus` = `COMPLETED|TERMINATED`
- **Fields:** NCT ID, acronym, brief title, enrollment, start date, conditions, interventions, primary outcome.
- **Screening:** records are screened on title/acronym/intervention/primary outcome. A record that passes is linked to its primary publication on PubMed. Records without a primary publication found are not carried forward.

## 6. Screening procedure

1. **Identification.** All records from §4 (PubMed) and §5 (CT.gov), plus records from sources 3–5. Duplicates are removed: within PubMed by PMID; across sources by trial name (acronym) and primary PMID.
2. **Title/abstract screening** against E1–E7, by one reviewer (an LLM agent, under this protocol). Records are excluded at this stage only when ineligibility is evident from the title or registry entry (non-RCT, secondary paper, pediatric, non-CV, surrogate primary, placebo-only class with no proxy, drug never marketed in the US, N clearly <1,000 and not a landmark). Uncertain records go forward.
3. **Full-text / abstract-level eligibility.** For each retained trial, the primary-publication abstract (PubMed or publisher page) is read to record:
   - PICOT and N;
   - the primary effect and its 95% CI;
   - one exclusion reason (§2) if ineligible.

   If a full text is paywalled, the abstract is used.
4. **Coverage check.** Each eligible trial is matched by name against the project pool:
   - `scripts/trial_specs.py` (all specified trials);
   - `docs/v17/candidates.md` and `docs/v18/af_candidates.md`, including the "screened, not built" and "not screened" tables;
   - Table 1 of `docs/paper/paper.md` (the 38).

   The legacy archive configs (`archive/2026-09-09-legacy-v1/configs/`, the RCT-DUPLICATE set) are recorded separately as "considered in legacy v1".

   **Coverage = eligible trials already in the pool / all eligible trials**, reported with and without the legacy archive.
5. **Grouping of new eligible trials** (each trial in exactly one primary group; tags allowed):
   - **A:** likely feasible as is (active comparator or existing design; drugs/procedures common in 2011–2024 US practice; EHR-ascertainable endpoint);
   - **B:** feasible with an accepted proxy or a stated adaptation (placebo proxy, class adaptation, non-initiator sequential comparator, endpoint adaptation, population adaptation);
   - **C:** positive (non-null) benchmark suitable for directional tests, regardless of A/B status (tagged A or B);
   - **D:** considered but likely infeasible (drug not used in the window, endpoint not ascertainable, population not identifiable, too rare, near-duplicate of an existing cohort), kept for transparency.

   Group C takes precedence over A/B. A trial is placed in C when its primary 95% CI excludes 1 **and** it would otherwise be A or B. Within groups, trials are ordered by clinical area: AF/anticoagulation, HF, hypertension, diabetes/cardiometabolic, ACS/CAD/antiplatelet, lipids, VTE, valve/structural, other.
6. **Per-trial record**:
   - name and year;
   - journal plus PMID or DOI;
   - PICOT and N;
   - published effect with its source;
   - emulation design sketch (new-user or sequential; time zero);
   - EHR codes and drug tokens needed;
   - anticipated quality-framework items (EL, TZ, TS, CO, OU, FU, ES, BM, DA);
   - a one-line "why add".
7. **Effect verification.** Each benchmark is verified against the PubMed abstract (or the publisher abstract). Where the abstract could not be retrieved, the record says so and the estimate is marked unverified.

## 7. Limitations anticipated

The following limits are fixed in advance:
- a single screener;
- a journal restriction for the main PubMed stream;
- no Embase or CENTRAL;
- registry-only for non-indexed trials;
- design-level feasibility only, with no counts.

Results do not imply that any trial meets the project's size gates. Every candidate must pass the registered count-only screen before it is built. If the exploratory set is adopted as a prespecified confirmation set, its specs and benchmarks must be committed **before** that screen, following the v1.7/v1.8 conventions.
