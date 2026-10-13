# Exploratory trial-search candidates (LATENT-RCT)

Written 2026-10-13. **Exploratory only.**
- Nothing here changes the analysed set, pipeline.md §2 or any registered specification.
- No patient data were read and no count screen was run.
- Feasibility is a design-level expectation. Every trial must still pass the registered count-only screen (≥300 patients with an ECG in the smaller arm, ≥50 pooled events, <80% record overlap).

Related files:
- [SEARCH_PROTOCOL.md](SEARCH_PROTOCOL.md): eligibility and sources.
- [SEARCH_LOG.md](SEARCH_LOG.md): queries, counts, PRISMA flow and coverage.
- [candidates.json](candidates.json): the same content, machine-readable.

Published effects:
- Transcribed from the PubMed abstract of the primary paper (retrieved 2026-10-13), with the PMID and DOI given in each entry.
- Where the abstract reports no HR, the entry says so.
- Quality-item codes follow `docs/emulation_quality_v2/QUALITY_FRAMEWORK.md` (EL, TZ, TS, CO, OU, FU, ES, BM, DA, SI). Scores are anticipated, not rated.

## Summary

- **New candidates (not in the current pool):**
  - Group A: 11;
  - Group B: 13;
  - Group C: 14;
  - Group D: 126 entries covering 210 trials.
- **Legacy archive:** 4 of the A–C trials (EINSTEIN-DVT, EINSTEIN-PE, RE-COVER II, DAPA-CKD) exist only in the legacy v1 archive (RCT-DUPLICATE configs), not in the current pool.
- **Coverage:** 68 of the 70 eligible pool trials were retrieved by the search. Coverage of all eligible trials identified is **42%** (45% counting the legacy archive). See SEARCH_LOG.md §5.

## Top picks (15)

These are the strongest additions.
- The first ten are positive or high-information benchmarks (Group C, with their A/B tag).
- The last five are Group A trials that need no proxy.

| # | Trial (year) | Group | Contrast | Published effect (primary) | Citation | Why |
|---|---|---|---|---|---|---|
| 1 | RAFT (2010) | C (tag A) | ICD + CRT (CRT-D) vs ICD alone | HR 0.75 (95% CI 0.64-0.87); death HR 0.75 | Tang ASL, et al. N Engl J Med 2010;363:2385-95; PMID 21073365 | Positive device benchmark in which the ECG defines eligibility and modifies the effect (QRS/LBBB), a direct test of whether ECG embeddings carry treatment-relevant physiology |
| 2 | BEST-CLI (cohort 1) (2022) | C (tag A) | Surgical bypass vs endovascular therapy | Cohort 1 HR 0.68 (95% CI 0.59-0.79); cohort 2 HR 0.79 (0.58-1.06) | Farber A, et al. N Engl J Med 2022;387:2305-16; PMID 36342173 | Strongly positive procedure-vs-procedure benchmark with procedure-coded endpoints |
| 3 | DAPA-CKD (2020) | C (tag B) | Dapagliflozin vs placebo | HR 0.61 (95% CI 0.51-0.72) | Heerspink HJL, et al. N Engl J Med 2020;383:1436-46; PMID 32970396 | Very strong positive benchmark with lab-defined population and endpoint (an EHR strength) |
| 4 | SOUL (2025) | C (tag B) | Oral semaglutide 14 mg vs placebo | HR 0.86 (95% CI 0.77-0.96) | McGuire DK, et al. N Engl J Med 2025;392:2001-12; PMID 40162642 | Recent positive proxy CVOT |
| 5 | FREEDOM (2012) | C (tag B) | PCI with drug-eluting stents vs CABG | 5-year rate 26.6% PCI vs 18.7% CABG, P=0.005 (CABG better); no HR reported in the abstract | Farkouh ME, et al. N Engl J Med 2012;367:2375-84; PMID 23121323 | Landmark positive procedural benchmark (CABG superior) with heavy confounding by anatomy and frailty |
| 6 | BETAMI-DANBLOCK (2025) | C (tag B) | Beta-blocker vs no beta-blocker (open-label) | HR 0.85 (95% CI 0.75-0.98) | Munkhaugen J, et al. N Engl J Med 2025;393:1901-11; PMID 40888716 | Contemporary, guideline-changing, ECG-relevant (heart rate, arrhythmia) |
| 7 | TALOS-AMI (2021) | C (tag B) | Switch to clopidogrel + aspirin vs continue ticagrelor + aspirin | HR 0.55 (95% CI 0.40-0.76), superiority P=0.0001 | Kim CJ, et al. Lancet 2021;398:1305-16; PMID 34627490 | Positive switch-design benchmark in ACS, parallel to FRAIL-AF in AF |
| 8 | VOYAGER PAD (2020) | C (tag B) | Rivaroxaban 2.5 mg bid + aspirin vs aspirin + placebo | HR 0.85 (95% CI 0.76-0.96) | Bonaca MP, et al. N Engl J Med 2020;382:1994-2004; PMID 32222135 | Positive benchmark anchored at a procedure |
| 9 | REDUCE-IT (2019) | C (tag B) | Icosapent ethyl 2 g bid vs mineral-oil placebo | HR 0.75 (95% CI 0.68-0.83) | Bhatt DL, et al. N Engl J Med 2019;380:11-22; PMID 30415628 | Strong positive benchmark with lab-defined eligibility |
| 10 | DapaTAVI (2025) | C (tag B) | Dapagliflozin + standard care vs standard care (open-label) | HR 0.72 (95% CI 0.55-0.95); death HR 0.87 | Raposeiras-Roubin S, et al. N Engl J Med 2025;392:1396-405; PMID 40162639 | Recent positive trial anchored at a procedure |
| 11 | SURPASS-CVOT (2025) | A | Tirzepatide (up to 15 mg weekly) vs dulaglutide 1.5 mg weekly | HR 0.92 (95.3% CI 0.83-1.01); P=0.003 noninferiority, P=0.09 superiority | Nicholls SJ, et al. N Engl J Med 2025;393:2409-20; PMID 41406444 | The only large incretin head-to-head CVOT with a hard endpoint |
| 12 | TASTE (2013) | A | Manual thrombus aspiration + PCI vs PCI alone | HR 0.94 (95% CI 0.72-1.22) | Frobert O, et al. N Engl J Med 2013;369:1587-97; PMID 23991656 | Registry-embedded RCT (the closest RCT design to EHR emulation) with an all-cause-death endpoint |
| 13 | INVESTED (2021) | A | High-dose trivalent inactivated influenza vaccine vs standard-dose quadrivalent vaccine | HR 1.06 (95% CI 0.97-1.17) | Vardeny O, et al. JAMA 2021;325:39-49; PMID 33275134 | EHR-native exposure with an active comparator, all-cause outcomes and a high-risk CV population |
| 14 | PRoFESS (2008) | A | Aspirin + extended-release dipyridamole vs clopidogrel | HR 1.01 (95% CI 0.92-1.11) | Sacco RL, et al. N Engl J Med 2008;359:1238-51; PMID 18753638 | Large active-comparator secondary-stroke trial |
| 15 | EVAR trial 1 (2010) | A | Endovascular repair (EVAR) vs open repair | All-cause death adjusted HR 1.03 (0.86-1.23); 30-day operative mortality adjusted OR 0.39 (0.18-0.87); 4-year all-cause death HR 0.90 (0.69-1.18) (Lancet 2005, PMID 15978925) | EVAR trial investigators (Greenhalgh RM, et al.). N Engl J Med 2010;362:1863-71; 4-year report Lancet 2005;365:2179-86; PMID 20382983 | Procedure-vs-procedure trial with an all-cause-death endpoint and strong confounding by frailty, a demanding test of ECG-augmented balance |

### A coherent prespecified exploratory confirmation set

If the user wants a third prespecified stage (like v1.7/v1.8), a natural set is **'procedure and device contrasts plus decision-point designs'**:
- **Positive anchors (directional tests):**
  - RAFT (CRT-D vs ICD);
  - BEST-CLI (bypass vs endovascular);
  - FREEDOM (PCI vs CABG in diabetes);
  - DapaTAVI (SGLT2i after TAVR);
  - BETAMI-DANBLOCK (β-blocker after MI);
  - TALOS-AMI (switch design).
- **Null anchors:**
  - TASTE (thrombectomy add-on);
  - EVAR-1 (EVAR vs open);
  - CTOPP (dual vs single-chamber pacing);
  - SCOT (switch design);
  - INVESTED (vaccine formulation).

Why this set holds together:
- **Mostly active or procedural comparators.** No placebo proxy is needed; the proxy-based positives (SOUL, DAPA-CKD, REDUCE-IT) could form a separate proxy arm.
- **ECG physiology plausibly matters.** QRS and conduction for RAFT/CTOPP; STEMI ECG for TASTE; heart rate and arrhythmia for BETAMI.
- **The project's existing designs largely suffice:**
  - procedure vs procedure at a common time zero (LAAOS III-type);
  - switch_seq;
  - new-user.

New methodology would be needed for:
- **DapaTAVI and BETAMI-DANBLOCK:** a grace-period (clone-censor-weight) design for initiation vs non-initiation.
- **VOYAGER PAD and COMPASS:** dose-level drug tokens.

Before registration, check record overlap for:
- the PAD group (BEST-CLI, SWEDEPAD 1, VOYAGER PAD share index procedures);
- DapaTAVI against the analysed PARTNER cohort.

## Group A: likely feasible as is

### HF

#### CIBIS III (2005)

- **Citation:** Willenheimer R, et al. Circulation 2005;112:2426-35; PMID 16143696; DOI 10.1161/CIRCULATIONAHA.105.582320.
- **PICOT:**
  - Population: Mild-to-moderate HF (NYHA II-III), LVEF <=35%, age >=65, not on ACEi/ARB/beta-blocker.
  - Intervention: Bisoprolol first (6 months), then bisoprolol + enalapril.
  - Comparator: Enalapril first (6 months), then combination.
  - Primary outcome: All-cause death or all-cause hospitalisation.
  - Follow-up: 6-24 months (combination phase).
  - N randomised: 1,010.
- **Published effect (abstract):** HR 0.94 (95% CI 0.77-1.16); noninferior.
- **Emulation sketch:** New-user, initial-strategy contrast: first neurohormonal agent in HF patients naive to both classes; no order of the other class in a 30-day grace window (added later in both arms, as in the trial). Time zero = first order of bisoprolol (or cardioselective beta-blocker class) or ACEi.
- **EHR codes / drug tokens:** I50.x; echo LVEF <=35%; drug tokens bisoprolol (class: cardioselective beta-blocker) and enalapril (class: ACEi); outcomes all-cause death + any inpatient admission.
- **Anticipated quality items:** TS 1 (beta-blocker or ACEi class adaptation; a sequence strategy approximated by first-agent choice); CO 1 (ACEi class for enalapril); EL 1 (LVEF from echo, DA if under 50% measured); OU 0 (all-cause death/hospitalisation); FU 0; BM 0.
- **Feasibility risk:** US practice often co-initiates both classes, so the single-agent-first arms may be small.
- **Why add:** HF active-comparator trial with all-cause endpoints, complementary to COMET/ELITE II; first-agent choice is plausibly ECG-driven (heart rate, conduction).

### Hypertension

#### NORDIL (2000)

- **Citation:** Hansson L, et al. Lancet 2000;356:359-65; PMID 10972367; DOI 10.1016/S0140-6736(00)02526-5.
- **PICOT:**
  - Population: Hypertension (DBP >=100 mm Hg), age 50-74.
  - Intervention: Diltiazem.
  - Comparator: Diuretics, beta-blockers or both.
  - Primary outcome: Fatal/non-fatal stroke, MI, or other CV death.
  - Follow-up: not stated in the abstract (about 4.5 years per secondary sources; unverified).
  - N randomised: 10,881.
- **Published effect (abstract):** RR 1.00 (95% CI 0.87-1.15).
- **Emulation sketch:** New-user: diltiazem vs thiazide or beta-blocker as the first antihypertensive. Exclude AF/flutter/SVT (diltiazem is used for rate control). Time zero = first order.
- **EHR codes / drug tokens:** I10; diltiazem token; thiazide and beta-blocker class tokens; exclude I47-I48; outcomes stroke/MI hospitalisation + CV death.
- **Anticipated quality items:** CO 1 (mixed comparator); OU 1 (CV death); BM 1 (RR); FU 1 if horizon >=48 mo (set 47); TZ.c possible (previously treated patients).
- **Feasibility risk:** Confounding by indication for diltiazem (arrhythmia, angina); ECG may help.
- **Why add:** Non-dihydropyridine CCB vs conventional therapy; large null benchmark, and diltiazem initiators are common.

#### ANBP2 (2003)

- **Citation:** Wing LMH, et al. N Engl J Med 2003;348:583-92; PMID 12584366; DOI 10.1056/NEJMoa021716.
- **PICOT:**
  - Population: Hypertension, age 65-84, Australian family practice.
  - Intervention: ACE inhibitor (enalapril recommended).
  - Comparator: Thiazide diuretic (HCTZ recommended).
  - Primary outcome: First cardiovascular event or death from any cause.
  - Follow-up: median 4.1 years.
  - N randomised: 6,083.
- **Published effect (abstract):** HR 0.89 (95% CI 0.79-1.00).
- **Emulation sketch:** New-user active comparator: first antihypertensive order (ACEi vs thiazide), none in the prior 365 days. Time zero = first order.
- **EHR codes / drug tokens:** I10-I15; ACEi class and thiazide-class tokens; outcomes all-cause death + first CV-coded inpatient stay (I20-I25, I50, I60-I66, I70-I74).
- **Anticipated quality items:** TS 1, CO 1 (class adaptations); OU 1 (the broad 'any CV event' composite is approximated by CV hospitalisations; outpatient events are missed); FU 0 if horizon <48 mo (use 47); TZ.c to be checked (proportion previously treated); BM 0.
- **Feasibility risk:** The thiazide arm overlaps the ALLHAT and INSIGHT cohorts; run the record-overlap check.
- **Why add:** Pragmatic primary-care trial of first-line class with a tight near-null CI; ACEi vs thiazide is not in the analysed set (ALLHAT's lisinopril arm was never built).

### Diabetes/cardiometabolic

#### SURPASS-CVOT (2025) [tag recent]

- **Citation:** Nicholls SJ, et al. N Engl J Med 2025;393:2409-20; PMID 41406444; DOI 10.1056/NEJMoa2505928.
- **PICOT:**
  - Population: T2D with established ASCVD, BMI >=25.
  - Intervention: Tirzepatide (up to 15 mg weekly).
  - Comparator: Dulaglutide 1.5 mg weekly.
  - Primary outcome: CV death, MI or stroke.
  - Follow-up: event-driven (median not stated in abstract).
  - N randomised: 13,299.
- **Published effect (abstract):** HR 0.92 (95.3% CI 0.83-1.01); P=0.003 noninferiority, P=0.09 superiority.
- **Emulation sketch:** New-user active comparator in T2D + ASCVD: tirzepatide (approved May 2022) vs dulaglutide initiators, with no GLP-1RA in the prior 365 days. Index window 2022-06 to 2024. Time zero = first order.
- **EHR codes / drug tokens:** E11 + ASCVD codes; tokens tirzepatide (exclude obesity-only Zepbound without T2D), dulaglutide; 3-point MACE.
- **Anticipated quality items:** FU 1 (FU.b: the available horizon of at most ~2.5 y is much shorter than the trial's); OU 1 (CV death); BM 0 (noninferiority HR, 95.3% CI); DA risk (event count in a short window).
- **Feasibility risk:** Short follow-up; calendar-time confounding (supply shortages 2022-2024).
- **Why add:** The only large incretin head-to-head CVOT with a hard endpoint; true active comparator; very high use late in the window.

### ACS/CAD/antiplatelet

#### PRoFESS (2008)

- **Citation:** Sacco RL, et al. N Engl J Med 2008;359:1238-51; PMID 18753638; DOI 10.1056/NEJMoa0805002.
- **PICOT:**
  - Population: Recent non-cardioembolic ischaemic stroke (<90 days).
  - Intervention: Aspirin + extended-release dipyridamole.
  - Comparator: Clopidogrel.
  - Primary outcome: Recurrent stroke.
  - Follow-up: mean 2.5 years.
  - N randomised: 20,332.
- **Published effect (abstract):** HR 1.01 (95% CI 0.92-1.11).
- **Emulation sketch:** New-user active comparator after ischaemic stroke: first order of the aspirin/dipyridamole combination product vs clopidogrel within 90 days of the index stroke. Exclude AF and anticoagulant users. Time zero = first order (inpatient or discharge).
- **EHR codes / drug tokens:** I63; combination token aspirin-dipyridamole (Aggrenox), clopidogrel; exclude I48 and OAC; outcome stroke hospitalisation (I60-I64) after the index stay.
- **Anticipated quality items:** TS 0, CO 0; TZ 0 (both arms start at the same point; inpatient orders are visible); OU 0-1 (recurrent vs index stroke separated by excluding the index stay); ES risk (higher discontinuation of ASA-ERDP); DA risk (ASA-ERDP use declined).
- **Why add:** Large active-comparator secondary-stroke trial; adds the cerebrovascular domain, which the pool lacks.

#### TASTE (2013) [tag registry-RCT]

- **Citation:** Frobert O, et al. N Engl J Med 2013;369:1587-97; PMID 23991656; DOI 10.1056/NEJMoa1308789.
- **PICOT:**
  - Population: STEMI undergoing primary PCI (registry-based, Scandinavia).
  - Intervention: Manual thrombus aspiration + PCI.
  - Comparator: PCI alone.
  - Primary outcome: All-cause death at 30 days.
  - Follow-up: 30 days (1-year follow-up published).
  - N randomised: 7,244.
- **Published effect (abstract):** HR 0.94 (95% CI 0.72-1.22).
- **Emulation sketch:** Procedure add-on within a common procedure (as LAAOS III): primary PCI for STEMI with vs without a same-session aspiration thrombectomy code. Time zero = PCI date.
- **EHR codes / drug tokens:** I21.0-I21.3; PCI CPT 92941 / ICD-10-PCS 027-; thrombectomy CPT 92973 / ICD-10-PCS 02C-; outcome all-cause death (death records, including in-hospital deaths).
- **Anticipated quality items:** TZ 0 (common time zero); TS 0; CO 0; OU 0 (all-cause death); FU 0; DA risk (thrombectomy use fell after 2015).
- **Feasibility risk:** Strong confounding by thrombus burden (angiographic, not coded). TOTAL is an alternative benchmark (Group D, near-duplicate).
- **Why add:** Registry-embedded RCT (the closest RCT design to EHR emulation) with an all-cause-death endpoint; STEMI ECG physiology is central to both thrombus burden and prognosis.

### Other

#### CTOPP (2000) [tag device]

- **Citation:** Connolly SJ, et al. N Engl J Med 2000;342:1385-91; PMID 10805823; DOI 10.1056/NEJM200005113421902.
- **PICOT:**
  - Population: First pacemaker for symptomatic bradycardia, no chronic AF.
  - Intervention: Physiologic pacing (dual-chamber or atrial).
  - Comparator: Ventricular (single-chamber) pacing.
  - Primary outcome: Stroke or CV death.
  - Follow-up: mean 3 years.
  - N randomised: 2,568.
- **Published effect (abstract):** RRR 9.4% (95% CI -10.5 to 25.7), i.e. RR ~0.91 (0.74-1.11).
- **Emulation sketch:** Device vs device at first implant: dual-chamber vs single-chamber ventricular pacemaker (leadless VVI included) in patients without AF. Time zero = implant date.
- **EHR codes / drug tokens:** Bradycardia/AV block/SND codes (I44.1-I44.2, I49.5, R00.1); CPT 33208 vs 33207 (and leadless 33274); exclude I48; outcome stroke hospitalisation + CV death.
- **Anticipated quality items:** EL 1 (exclude AF); TS 0; CO 0; OU 1 (CV death); BM 1 (RRR, not HR); confounding by frailty (single-chamber devices go to frail patients), where ECG conduction features are directly relevant.
- **Why add:** Device-vs-device contrast in which the ECG is the indication; UKPACE and MOST are alternative benchmarks (Group D).

#### EVAR trial 1 (2010)

- **Citation:** EVAR trial investigators (Greenhalgh RM, et al.). N Engl J Med 2010;362:1863-71; 4-year report Lancet 2005;365:2179-86; PMID 20382983; DOI 10.1056/NEJMoa0909305.
- **PICOT:**
  - Population: AAA >=5.5 cm, age >=60, fit for open repair.
  - Intervention: Endovascular repair (EVAR).
  - Comparator: Open repair.
  - Primary outcome: All-cause death (long term); aneurysm-related death.
  - Follow-up: 1999-2009 (mean ~6 years).
  - N randomised: 1,252.
- **Published effect (abstract):** All-cause death adjusted HR 1.03 (0.86-1.23); 30-day operative mortality adjusted OR 0.39 (0.18-0.87); 4-year all-cause death HR 0.90 (0.69-1.18) (Lancet 2005, PMID 15978925).
- **Emulation sketch:** Procedure vs procedure: first elective repair of non-ruptured AAA, EVAR vs open. Time zero = repair date. A 4-year all-cause-death horizon matches the 2005 report.
- **EHR codes / drug tokens:** I71.4; EVAR CPT 34701-34708 / ICD-10-PCS 04V03DZ etc.; open CPT 35081/35102 / 04R0-, 04V00-; outcome all-cause death.
- **Anticipated quality items:** EL 1-2 ('fit for open repair' cannot be identified, so EVAR includes unfit patients); TS 0, CO 0, OU 0; BM 1 for the 2010 adjusted HR (use the 2005 4-year HR); FU 0 with a 48-month horizon.
- **Why add:** Procedure-vs-procedure trial with an all-cause-death endpoint and strong confounding by frailty, a demanding test of ECG-augmented balance.

#### SCOT (2017) [tag switch-design]

- **Citation:** MacDonald TM, et al. Eur Heart J 2017;38:1843-50; PMID 27705888; DOI 10.1093/eurheartj/ehw387.
- **PICOT:**
  - Population: Age >=60, OA/RA on chronic prescribed non-selective NSAID, no CVD.
  - Intervention: Switch to celecoxib.
  - Comparator: Continue prescribed nsNSAID.
  - Primary outcome: Hospitalisation for non-fatal MI/ACS, non-fatal stroke, or CV death.
  - Follow-up: median 3 years.
  - N randomised: 7,297.
- **Published effect (abstract):** ITT HR 1.04 (0.81-1.33); on-treatment HR 1.12 (0.81-1.55).
- **Emulation sketch:** Sequential switch (switch_seq, as FRAIL-AF): established prescribed-nsNSAID users who switch to celecoxib vs continuers sampled within +/-30 days. Time zero = switch date.
- **EHR codes / drug tokens:** M05-M06, M15-M19; tokens diclofenac, ibuprofen, naproxen, meloxicam, etc. (prescribed); celecoxib; exclude CVD; outcome MI/stroke hospitalisation + CV death.
- **Anticipated quality items:** CO 0 (continuation); TS 0; OU 1 (CV death); ES 0 using the ITT benchmark (the trial's primary was on-treatment); DA risk (low event rate, ~1.1/100 PY).
- **Why add:** Tests the switch design in a second drug class; complements PRECISION (new users) without reusing its cohort.

#### INVESTED (2021) [tag pragmatic, vaccine]

- **Citation:** Vardeny O, et al. JAMA 2021;325:39-49; PMID 33275134.
- **PICOT:**
  - Population: Recent MI or HF hospitalisation plus >=1 risk factor.
  - Intervention: High-dose trivalent inactivated influenza vaccine.
  - Comparator: Standard-dose quadrivalent vaccine.
  - Primary outcome: All-cause death or cardiopulmonary hospitalisation (per season).
  - Follow-up: up to 3 seasons (2016-2019).
  - N randomised: 5,260.
- **Published effect (abstract):** HR 1.06 (95% CI 0.97-1.17).
- **Emulation sketch:** Season-specific new-user: patients with an MI or HF hospitalisation in the prior 12 months vaccinated Sep-Jan; arm by vaccine formulation. Time zero = vaccination date; follow-up to the season end. First season only.
- **EHR codes / drug tokens:** CVX/CPT vaccine codes (high-dose CVX 135/197, CPT 90662; standard-dose quadrivalent CVX 150/158/161/171); I21/I50 hospitalisation; outcome death or principal-diagnosis cardiopulmonary admission.
- **Anticipated quality items:** TS 0 (formulation coded); EL 1 (risk-factor enrichment; high-dose licensed >=65, so restrict to >=65); OU 1 (cardiopulmonary definition); vaccination capture outside the system (pharmacies) is incomplete.
- **Why add:** EHR-native exposure with an active comparator, all-cause outcomes and a high-risk CV population; a very common exposure.

#### SWEDEPAD 1 (2025) [tag registry-RCT, recent]

- **Citation:** Falkenberg M, et al. Lancet 2025;406:1103-14; PMID 40902617; DOI 10.1016/S0140-6736(25)01585-5.
- **PICOT:**
  - Population: Chronic limb-threatening ischaemia (Rutherford 4-6) undergoing infrainguinal endovascular treatment.
  - Intervention: Paclitaxel-coated balloons/stents.
  - Comparator: Uncoated devices.
  - Primary outcome: Ipsilateral major (above-ankle) amputation.
  - Follow-up: multi-year (enrolment 2014-2023).
  - N randomised: 2,400.
- **Published effect (abstract):** HR 1.05 (95% CI 0.87-1.27); all-cause death HR 1.04 (0.92-1.17).
- **Emulation sketch:** Device contrast within a common procedure: CLTI endovascular revascularisation with vs without a drug-coated device. Time zero = procedure date.
- **EHR codes / drug tokens:** I70.22-I70.26 / I70.23x-I70.26x; endovascular CPT 37224-37235; drug-coated device from ICD-10-PCS device qualifiers (drug-coated balloon / drug-eluting intraluminal device) or HCPCS C2623; outcome amputation CPT 27590-27598, 27880-27889 / ICD-10-PCS 0Y6-.
- **Anticipated quality items:** TS 1 (device identification depends on PCS qualifiers or HCPCS; laterality is needed for 'ipsilateral'); OU 1 (laterality); CO 0; EL 0; calendar confounding (paclitaxel mortality signal 2018-2019).
- **Feasibility risk:** Index dates are shared with BEST-CLI and VOYAGER PAD cohorts; check overlap.
- **Why add:** Registry-based RCT with a procedure-coded endpoint; a device-safety question that matters in the current window.

## Group B: feasible with an accepted proxy or a stated adaptation

### HF

#### STICH (hypothesis 1) (2011) [tag procedure, strategy]

- **Citation:** Velazquez EJ, et al. N Engl J Med 2011;364:1607-16; extended (STICHES) N Engl J Med 2016;374:1511-20 (PMID 27040723); PMID 21463150; DOI 10.1056/NEJMoa1100356.
- **PICOT:**
  - Population: CAD amenable to CABG with LVEF <=35%.
  - Intervention: CABG + medical therapy.
  - Comparator: Medical therapy alone.
  - Primary outcome: All-cause death.
  - Follow-up: median 56 months (STICHES 9.8 years).
  - N randomised: 1,212.
- **Published effect (abstract):** HR 0.86 (0.72-1.04); 10-year STICHES HR 0.84 (0.73-0.97).
- **Emulation sketch:** Strategy at a common decision point: diagnostic angiography in ischaemic cardiomyopathy (LVEF <=35%), CABG within a 30-60 day grace period vs no CABG. Needs clone-censor-weighting, which is not yet in the pipeline.
- **EHR codes / drug tokens:** Cath CPT 93454-93461; CABG CPT 33510-33536; echo LVEF; outcome all-cause death.
- **Anticipated quality items:** TZ.d (grace period/immortal time must be handled); EL 1 ('amenable to CABG'); CO 1 (non-surgical arm includes surgical non-candidates); FU 1 (>=48 mo); ES (crossover).
- **Why add:** Landmark HFrEF revascularisation trial with an all-cause-death endpoint; LV physiology is central.

#### IRONMAN (2022) [tag lab-defined]

- **Citation:** Kalra PR, et al. Lancet 2022;400:2199-209; PMID 36347265; DOI 10.1016/S0140-6736(22)02083-9.
- **PICOT:**
  - Population: HF with LVEF <=45% and iron deficiency (TSAT <20% or ferritin <100).
  - Intervention: IV ferric derisomaltose.
  - Comparator: Usual care (open-label).
  - Primary outcome: Recurrent HF hospitalisation and CV death.
  - Follow-up: median 2.7 years.
  - N randomised: 1,137.
- **Published effect (abstract):** RR 0.82 (95% CI 0.66-1.02).
- **Emulation sketch:** Initiation vs non-initiation after a qualifying iron panel: HF patient with qualifying labs; IV iron within a 30-day grace period vs none. Time zero = lab date; clone-censor-weight.
- **EHR codes / drug tokens:** I50; ferritin/TSAT labs; IV iron HCPCS J1437/J1439/J1756/J2916 or infusion orders; outcome HF hospitalisation + CV death.
- **Anticipated quality items:** CO 1 (usual-care comparator, matching the open-label trial); TZ.d (grace period); OU 1 (first-event analysis changes the estimand from recurrent events); BM 1 (rate ratio); EL 0 (lab-defined).
- **Why add:** Eligibility is defined by labs, which is an EHR strength; AFFIRM-AHF and HEART-FID are placebo-controlled alternative benchmarks.

### Diabetes/cardiometabolic

#### EXSCEL (2017) [tag placebo-proxy]

- **Citation:** Holman RR, et al. N Engl J Med 2017;377:1228-39; PMID 28910237; DOI 10.1056/NEJMoa1612917.
- **PICOT:**
  - Population: T2D with or without CVD (73% with CVD).
  - Intervention: Exenatide extended-release weekly.
  - Comparator: Placebo.
  - Primary outcome: CV death, non-fatal MI or non-fatal stroke.
  - Follow-up: median 3.2 years.
  - N randomised: 14,752.
- **Published effect (abstract):** HR 0.91 (95% CI 0.83-1.00).
- **Emulation sketch:** RCT-DUPLICATE placebo proxy: exenatide ER vs DPP-4i new users (as LEADER). Time zero = first order.
- **EHR codes / drug tokens:** E11; tokens exenatide (weekly formulation) vs DPP-4i; 3-point MACE.
- **Anticipated quality items:** CO 2 (proxy); OU 1 (CV death); FU 0 (38 mo); DA risk (exenatide ER use is modest; the LEADER liraglutide arm had 453 with an ECG).
- **Why add:** Completes the GLP-1RA CVOT family under the accepted proxy; benchmark at the null boundary.

### ACS/CAD/antiplatelet

#### COURAGE (2007) [tag procedure, strategy]

- **Citation:** Boden WE, et al. N Engl J Med 2007;356:1503-16; PMID 17387127; DOI 10.1056/NEJMoa070829.
- **PICOT:**
  - Population: Stable CAD with objective ischaemia and >=70% stenosis.
  - Intervention: PCI + optimal medical therapy.
  - Comparator: Optimal medical therapy.
  - Primary outcome: All-cause death or non-fatal MI.
  - Follow-up: median 4.6 years.
  - N randomised: 2,287.
- **Published effect (abstract):** HR 1.05 (95% CI 0.87-1.27).
- **Emulation sketch:** Decision point = elective diagnostic angiography with obstructive CAD in stable patients (no ACS in 30 days). PCI within a 30-day grace period vs no revascularisation (CABG excluded). Clone-censor-weight.
- **EHR codes / drug tokens:** Cath CPT 93454-93461; I25.x without I20.0/I21-I24 in 30 days; PCI CPT 92928-92944; outcome death + MI hospitalisation.
- **Anticipated quality items:** TZ.d (grace period); EL 1 (ischaemia and anatomy not coded); CO 1; ES (33% crossover to PCI in the trial); FU 1 if horizon >=48 (use a 36-mo landmark).
- **Why add:** Landmark stable-CAD strategy trial with a null benchmark; ISCHEMIA is the alternative (Group D).

#### VALIDATE-SWEDEHEART (2017) [tag registry-RCT, in-hospital]

- **Citation:** Erlinge D, et al. N Engl J Med 2017;377:1132-42; PMID 28844201; DOI 10.1056/NEJMoa1706443.
- **PICOT:**
  - Population: STEMI or NSTEMI undergoing PCI on a potent P2Y12 inhibitor, no planned GPI.
  - Intervention: Bivalirudin.
  - Comparator: Heparin monotherapy.
  - Primary outcome: Death, MI or major bleeding at 180 days.
  - Follow-up: 180 days.
  - N randomised: 6,006.
- **Published effect (abstract):** HR 0.96 (95% CI 0.83-1.10).
- **Emulation sketch:** In-hospital procedural anticoagulant contrast at PCI for MI: bivalirudin vs UFH-only. Time zero = PCI date.
- **EHR codes / drug tokens:** I21; PCI codes; bivalirudin/heparin administrations (cath-lab MAR); outcome all-cause death + post-discharge MI/major-bleeding hospitalisation.
- **Anticipated quality items:** OU 1-2 (index-stay MI/bleeding excluded by the current rule); TS/SI risk (cath-lab drugs may be documented outside order tables); CO 0.
- **Why add:** Registry-based RCT with a null benchmark; tests in-hospital drug exposure. BRIGHT-4, HEAT-PPCI, EUROMAX, HORIZONS-AMI and MATRIX are alternatives (Group D).

#### EMPACT-MI (2024) [tag placebo-proxy, in-hospital]

- **Citation:** Butler J, et al. N Engl J Med 2024;390:1455-66; PMID 38587237; DOI 10.1056/NEJMoa2314051.
- **PICOT:**
  - Population: Acute MI with new LVEF <45% and/or congestion, within 14 days.
  - Intervention: Empagliflozin.
  - Comparator: Placebo.
  - Primary outcome: First HF hospitalisation or all-cause death.
  - Follow-up: median 17.9 months.
  - N randomised: 6,522.
- **Published effect (abstract):** HR 0.90 (95% CI 0.76-1.06).
- **Emulation sketch:** Placebo proxy restricted to T2D: SGLT2i vs DPP-4i initiation within 14 days of the MI admission (inpatient orders visible). Time zero = first order.
- **EHR codes / drug tokens:** I21; LVEF from echo; E11; SGLT2i/DPP-4i tokens; outcome HF hospitalisation + all-cause death.
- **Anticipated quality items:** CO 2 (DPP-4i proxy); EL 2 (T2D restriction; only a minority of trial patients had diabetes); TZ 0 (in-hospital orders visible, as for the PLATO exemption); OU 0.
- **Why add:** Post-MI SGLT2i null benchmark; complements PARADISE-MI.

#### TACSI (2025) [tag registry-RCT, recent]

- **Citation:** Jeppsson A, et al. N Engl J Med 2025;393:2313-23; PMID 40888737; DOI 10.1056/NEJMoa2508026.
- **PICOT:**
  - Population: ACS treated with isolated CABG.
  - Intervention: Ticagrelor + aspirin for 12 months.
  - Comparator: Aspirin alone.
  - Primary outcome: Death, MI, stroke or repeat revascularisation at 1 year.
  - Follow-up: 12 months.
  - N randomised: 2,201.
- **Published effect (abstract):** HR 1.06 (95% CI 0.72-1.56); net adverse clinical events HR 1.45.
- **Emulation sketch:** Common decision point = CABG for ACS: ticagrelor initiation within 14 days of surgery (discharge) vs no P2Y12 inhibitor (aspirin background assumed). Time zero = CABG date + grace period.
- **EHR codes / drug tokens:** I21-I24 index; CABG CPT 33510-33536; ticagrelor token; outcomes death, MI/stroke hospitalisation, repeat revascularisation procedures.
- **Anticipated quality items:** CO 1 (non-initiator comparator, matching the open-label trial; aspirin not identifiable); TZ.d (grace period); OU 1 (needs repeat-revascularisation procedure outcome); FU 0.
- **Why add:** Recent registry-based pragmatic RCT anchored at a common decision point.

### VTE

#### EINSTEIN-DVT (2010) [tag legacy-archive, RCT-DUPLICATE]

- **Citation:** EINSTEIN Investigators (Bauersachs R, et al.). N Engl J Med 2010;363:2499-510; PMID 21128814; DOI 10.1056/NEJMoa1007903.
- **PICOT:**
  - Population: Acute symptomatic proximal DVT without PE.
  - Intervention: Rivaroxaban.
  - Comparator: Enoxaparin then VKA.
  - Primary outcome: Recurrent VTE.
  - Follow-up: 3, 6 or 12 months.
  - N randomised: 3,449.
- **Published effect (abstract):** HR 0.68 (95% CI 0.44-1.04).
- **Emulation sketch:** New-user active comparator after acute DVT (as AMPLIFY): rivaroxaban vs warfarin (with parenteral lead-in). Exclude PE. Time zero = first anticoagulant order.
- **EHR codes / drug tokens:** I82.4x acute (no I26); rivaroxaban, warfarin, enoxaparin; outcome recurrent VTE as a new inpatient stay with a VTE code.
- **Anticipated quality items:** OU 2 (inpatient-only recurrent VTE, as AMPLIFY); TS 0, CO 0 (VKA); FU 0; BM 0.
- **Feasibility risk:** Warfarin arm overlaps AMPLIFY's comparator; check the record share.
- **Why add:** RCT-DUPLICATE trial (legacy v1 config exists) that is missing from the current pool; uses a common DOAC.

#### EINSTEIN-PE (2012) [tag legacy-archive, RCT-DUPLICATE]

- **Citation:** EINSTEIN-PE Investigators (Buller HR, et al.). N Engl J Med 2012;366:1287-97; PMID 22449293; DOI 10.1056/NEJMoa1113572.
- **PICOT:**
  - Population: Acute symptomatic PE with or without DVT.
  - Intervention: Rivaroxaban.
  - Comparator: Enoxaparin then VKA.
  - Primary outcome: Recurrent VTE.
  - Follow-up: 3, 6 or 12 months.
  - N randomised: 4,832.
- **Published effect (abstract):** HR 1.12 (95% CI 0.75-1.68).
- **Emulation sketch:** As EINSTEIN-DVT, in PE (I26), which gives a cohort disjoint from EINSTEIN-DVT.
- **EHR codes / drug tokens:** I26.x; rivaroxaban, warfarin, enoxaparin; recurrent VTE hospitalisation.
- **Anticipated quality items:** OU 2 (as AMPLIFY); TS 0; CO 0; FU 0.
- **Why add:** RCT-DUPLICATE trial missing from the current pool; together with EINSTEIN-DVT it gives a DVT/PE pair.

#### RE-MEDY (active-control study) (2013) [tag switch-design]

- **Citation:** Schulman S, et al. N Engl J Med 2013;368:709-18; PMID 23425163; DOI 10.1056/NEJMoa1113697.
- **PICOT:**
  - Population: VTE treated for 3-12 months, at elevated recurrence risk.
  - Intervention: Dabigatran (extended).
  - Comparator: Warfarin (extended).
  - Primary outcome: Recurrent or fatal VTE.
  - Follow-up: 6-36 months.
  - N randomised: 2,856.
- **Published effect (abstract):** HR 1.44 (95% CI 0.78-2.64); major bleeding HR 0.52.
- **Emulation sketch:** Sequential switch (switch_seq): established warfarin users >=3 months after VTE who switch to dabigatran vs continuers sampled within +/-30 days.
- **EHR codes / drug tokens:** VTE codes; warfarin then dabigatran orders; recurrent VTE hospitalisation.
- **Anticipated quality items:** OU 2; EL 1; DA risk; CO 0.
- **Why add:** Switch design in VTE, parallel to FRAIL-AF in AF.

#### RE-COVER II (2014) [tag legacy-archive, RCT-DUPLICATE]

- **Citation:** Schulman S, et al. Circulation 2014;129:764-72; PMID 24344086; DOI 10.1161/CIRCULATIONAHA.113.004450.
- **PICOT:**
  - Population: Acute VTE after 5-11 days of parenteral anticoagulation.
  - Intervention: Dabigatran 150 mg bid.
  - Comparator: Warfarin.
  - Primary outcome: Recurrent symptomatic VTE or related death at 6 months.
  - Follow-up: 6 months.
  - N randomised: 2,589.
- **Published effect (abstract):** HR 1.08 (95% CI 0.64-1.80).
- **Emulation sketch:** Sequential: first oral anticoagulant after >=5 days of parenteral heparin/LMWH, dabigatran vs warfarin. Time zero = first oral order.
- **EHR codes / drug tokens:** I26/I82; heparin/enoxaparin; dabigatran, warfarin; recurrent VTE hospitalisation.
- **Anticipated quality items:** OU 2; DA risk (low dabigatran use for VTE); CO 0.
- **Why add:** RCT-DUPLICATE trial missing from the current pool; RE-COVER is its twin (Group D, near-duplicate).

#### CARAVAGGIO (2020) [tag class-adaptation]

- **Citation:** Agnelli G, et al. N Engl J Med 2020;382:1599-607; PMID 32223112; DOI 10.1056/NEJMoa1915103.
- **PICOT:**
  - Population: Cancer-associated acute VTE.
  - Intervention: Apixaban.
  - Comparator: Dalteparin.
  - Primary outcome: Recurrent VTE at 6 months.
  - Follow-up: 6 months.
  - N randomised: 1,170.
- **Published effect (abstract):** HR 0.63 (95% CI 0.37-1.07); major bleeding HR 0.82.
- **Emulation sketch:** New-user: apixaban vs LMWH (enoxaparin/dalteparin class adaptation) in active cancer with acute VTE. Time zero = first order.
- **EHR codes / drug tokens:** C00-C96 with recent oncology treatment; I26/I82; apixaban; enoxaparin/dalteparin; recurrent VTE hospitalisation.
- **Anticipated quality items:** CO 1 (LMWH class); OU 2; EL 1 (active cancer from codes and chemotherapy orders); FU 0.
- **Why add:** Guideline-defining cancer-VTE trial, DOAC vs LMWH.

### Other

#### CREST (2010) [tag procedure]

- **Citation:** Brott TG, et al. N Engl J Med 2010;363:11-23; PMID 20505173; DOI 10.1056/NEJMoa0912321.
- **PICOT:**
  - Population: Symptomatic or asymptomatic carotid stenosis.
  - Intervention: Carotid stenting.
  - Comparator: Carotid endarterectomy.
  - Primary outcome: Periprocedural stroke, MI or death, or ipsilateral stroke within 4 years.
  - Follow-up: median 2.5 years.
  - N randomised: 2,502.
- **Published effect (abstract):** HR 1.11 (95% CI 0.81-1.51).
- **Emulation sketch:** Procedure vs procedure: first carotid revascularisation, CAS (including TCAR) vs CEA. Time zero = procedure date.
- **EHR codes / drug tokens:** I65.2x (+ I63/G45 history for 'symptomatic'); CAS CPT 37215/37216 / ICD-10-PCS 037K3-/037L3-; CEA CPT 35301 / 03CK0ZZ, 03CL0ZZ.
- **Anticipated quality items:** Adaptation needed: OU 2 under the current rule, because periprocedural events happen in the index stay; count in-stay post-procedure events (POA = N) or accept OU 2. EL 1 (stenosis degree not coded); TS 0, CO 0.
- **Why add:** High-impact US carotid trial (procedure vs procedure); ICSS, ACST-2, ACT-1 and SPACE give stratum-specific alternative benchmarks.

## Group C: positive (non-null) benchmarks for directional tests

### HF

#### RAFT (2010) [tag A, device, ECG-defined eligibility]

- **Citation:** Tang ASL, et al. N Engl J Med 2010;363:2385-95; PMID 21073365; DOI 10.1056/NEJMoa1009540.
- **PICOT:**
  - Population: NYHA II-III HF, LVEF <=30%, QRS >=120 ms (or paced >=200 ms).
  - Intervention: ICD + CRT (CRT-D).
  - Comparator: ICD alone.
  - Primary outcome: All-cause death or HF hospitalisation.
  - Follow-up: mean 40 months.
  - N randomised: 1,798.
- **Published effect (abstract):** HR 0.75 (95% CI 0.64-0.87); death HR 0.75.
- **Emulation sketch:** Device vs device at first implant: CRT-D vs ICD-only in HFrEF with a wide QRS. Time zero = implant date. QRS duration/morphology from the raw pre-implant ECG.
- **EHR codes / drug tokens:** I50; LVEF <=30%; ECG QRS >=120 ms; CPT 33249 with vs without 33225 (LV lead) / ICD-10-PCS generator device values; outcome death + HF hospitalisation.
- **Anticipated quality items:** EL 0-1 (QRS and LVEF measured); TS 0, CO 0; OU 0-1 (HF hospitalisation coding position); FU 0; DA (count of CRT-D vs ICD-only implants to be checked).
- **Why add:** Positive device benchmark in which the ECG defines eligibility and modifies the effect (QRS/LBBB), a direct test of whether ECG embeddings carry treatment-relevant physiology. MADIT-CRT is an alternative benchmark (Group D, near-duplicate).

### Diabetes/cardiometabolic

#### DAPA-CKD (2020) [tag B, placebo-proxy, lab-defined, legacy-archive, RCT-DUPLICATE]

- **Citation:** Heerspink HJL, et al. N Engl J Med 2020;383:1436-46; PMID 32970396; DOI 10.1056/NEJMoa2024816.
- **PICOT:**
  - Population: CKD (eGFR 25-75, UACR 200-5000), with or without T2D (two-thirds with T2D).
  - Intervention: Dapagliflozin.
  - Comparator: Placebo.
  - Primary outcome: Sustained eGFR decline >=50%, ESKD, or renal or CV death.
  - Follow-up: median 2.4 years.
  - N randomised: 4,304.
- **Published effect (abstract):** HR 0.61 (95% CI 0.51-0.72).
- **Emulation sketch:** Placebo proxy in the T2D stratum: SGLT2i vs DPP-4i new users with qualifying eGFR/UACR labs. Lab-based endpoint: confirmed (>=28 d) eGFR decline >=50%, dialysis/transplant codes, renal or CV death.
- **EHR codes / drug tokens:** eGFR/UACR labs; E11; SGLT2i/DPP-4i tokens; N18.6, Z99.2, dialysis CPT 90935-90999; outcome per above.
- **Anticipated quality items:** CO 2 (proxy); EL 1 (T2D restriction; UACR measured in a subset, so DA); OU 1 (lab-based composite, renal death by cause); FU 0.
- **Why add:** Very strong positive benchmark with lab-defined population and endpoint (an EHR strength); emulated in RCT-DUPLICATE; legacy v1 config exists.

#### SOUL (2025) [tag B, placebo-proxy, recent]

- **Citation:** McGuire DK, et al. N Engl J Med 2025;392:2001-12; PMID 40162642; DOI 10.1056/NEJMoa2501006.
- **PICOT:**
  - Population: T2D, age >=50, with ASCVD and/or CKD.
  - Intervention: Oral semaglutide 14 mg.
  - Comparator: Placebo.
  - Primary outcome: CV death, MI or stroke.
  - Follow-up: median 49.5 months.
  - N randomised: 9,650.
- **Published effect (abstract):** HR 0.86 (95% CI 0.77-0.96).
- **Emulation sketch:** Placebo proxy: oral semaglutide (tablet formulation; marketed Sep 2019+) vs DPP-4i new users. Time zero = first order.
- **EHR codes / drug tokens:** E11 + ASCVD/CKD; semaglutide TABLET formulation token (must be separable from injectable); DPP-4i; 3-point MACE.
- **Anticipated quality items:** CO 2 (proxy); TS 1 (formulation must be distinguishable, or the cohort merges with SUSTAIN-6); FU 1 (horizon >=48 mo unless truncated); DA risk.
- **Why add:** Recent positive proxy CVOT; PIONEER 6 is an alternative benchmark (Group D, near-duplicate).

### ACS/CAD/antiplatelet

#### TACTICS-TIMI 18 (2001) [tag B, strategy, ECG-defined eligibility]

- **Citation:** Cannon CP, et al. N Engl J Med 2001;344:1879-87; PMID 11419424; DOI 10.1056/NEJM200106213442501.
- **PICOT:**
  - Population: UA/NSTEMI with ST/T changes, raised markers or CAD history.
  - Intervention: Early invasive strategy (angiography 4-48 h).
  - Comparator: Conservative (selectively invasive).
  - Primary outcome: Death, non-fatal MI or ACS rehospitalisation at 6 months.
  - Follow-up: 6 months.
  - N randomised: 2,220.
- **Published effect (abstract):** OR 0.78 (95% CI 0.62-0.97).
- **Emulation sketch:** Decision point = NSTE-ACS admission: coronary angiography within 48 h vs not within 48 h (clone-censor). ST/T changes can be read from the admission ECG.
- **EHR codes / drug tokens:** I21.4/I24.9/I20.0; angiography CPT 93454-93461 timing; outcome death, MI and ACS readmissions.
- **Anticipated quality items:** TZ.d (grace period); CO 1; ES (about half of conservative-arm patients had angiography in hospital); BM 1 (OR); era differs (1997-2000 tirofiban use); FU 0.
- **Why add:** Positive strategy benchmark with ECG-defined eligibility. FRISC II, RITA-3, ICTUS and SENIOR-RITA are alternatives (Group D).

#### FREEDOM (2012) [tag B, procedure]

- **Citation:** Farkouh ME, et al. N Engl J Med 2012;367:2375-84; PMID 23121323; DOI 10.1056/NEJMoa1211585.
- **PICOT:**
  - Population: Diabetes with multivessel CAD (83% three-vessel), no left main.
  - Intervention: PCI with drug-eluting stents.
  - Comparator: CABG.
  - Primary outcome: All-cause death, non-fatal MI or non-fatal stroke.
  - Follow-up: median 3.8 years (5-year rates).
  - N randomised: 1,900.
- **Published effect (abstract):** 5-year rate 26.6% PCI vs 18.7% CABG, P=0.005 (CABG better); no HR reported in the abstract.
- **Emulation sketch:** Procedure vs procedure in diabetes: multivessel PCI (>=2 vessels by CPT add-on codes) vs CABG with >=2 grafts. Time zero = revascularisation date.
- **EHR codes / drug tokens:** E10/E11; PCI CPT 92928 + 92929/92934/92938/92944 (or C9600-C9608); CABG CPT 33510-33536 (graft counts); outcome death + MI/stroke hospitalisation.
- **Anticipated quality items:** EL 1-2 (anatomy approximated by vessel/graft counts; left main not excluded); OU 1 (periprocedural index-stay MI excluded); BM 1 (rates/P only in the abstract; extract an HR from the full text); FU 1 if horizon >=48.
- **Why add:** Landmark positive procedural benchmark (CABG superior) with heavy confounding by anatomy and frailty. SYNTAX, EXCEL, NOBLE and FAME 3 are alternatives (Group D).

#### COMPASS (2017) [tag B, add-on, dose-identification]

- **Citation:** Eikelboom JW, et al. N Engl J Med 2017;377:1319-30; PMID 28844192; DOI 10.1056/NEJMoa1709118.
- **PICOT:**
  - Population: Stable CAD or PAD.
  - Intervention: Rivaroxaban 2.5 mg bid + aspirin.
  - Comparator: Aspirin alone.
  - Primary outcome: CV death, stroke or MI.
  - Follow-up: mean 23 months.
  - N randomised: 27,395.
- **Published effect (abstract):** HR 0.76 (95% CI 0.66-0.86); major bleeding HR 1.70.
- **Emulation sketch:** Sequential add-on vs continuation in CAD/PAD without an anticoagulation indication: rivaroxaban 2.5 mg initiation vs established antiplatelet-only users sampled within +/-30 days.
- **EHR codes / drug tokens:** I25/I70.2; rivaroxaban 2.5 mg STRENGTH (needs dose-level tokens); exclude I48, I26, I82; 3-point MACE.
- **Anticipated quality items:** TS 1-2 (strength identification); CO 2 (placebo-controlled; non-initiator comparator); OU 1 (CV death); DA risk (vascular-dose uptake); FU 0.
- **Why add:** Very large positive benchmark. VOYAGER PAD gives the same drug a cleaner time zero.

#### POINT (2018) [tag B, in-hospital]

- **Citation:** Johnston SC, et al. N Engl J Med 2018;379:215-25; PMID 29766750; DOI 10.1056/NEJMoa1800410.
- **PICOT:**
  - Population: Minor ischaemic stroke (NIHSS <=3) or high-risk TIA, within 12 h.
  - Intervention: Clopidogrel + aspirin for 90 days.
  - Comparator: Aspirin + placebo.
  - Primary outcome: Ischaemic stroke, MI or ischaemic vascular death at 90 days.
  - Follow-up: 90 days.
  - N randomised: 4,881.
- **Published effect (abstract):** HR 0.75 (95% CI 0.59-0.95); major haemorrhage HR 2.32.
- **Emulation sketch:** ED/admission decision point: clopidogrel order within 24 h vs none (aspirin ordered in both; inpatient orders visible). Time zero = presentation.
- **EHR codes / drug tokens:** I63/G45 with an NIHSS flowsheet value if available; clopidogrel/aspirin inpatient orders; outcome ischaemic stroke/MI hospitalisation + vascular death.
- **Anticipated quality items:** OU 2 risk (most recurrences fall in the first days, inside the index stay; adaptation: count in-stay events after day 1 with POA = N); EL 1 (NIHSS/ABCD2); CO 2 (placebo add-on; non-initiator); FU 0.
- **Why add:** Positive, guideline-defining stroke trial; CHANCE is an alternative (Group D).

#### TALOS-AMI (2021) [tag B, switch-design]

- **Citation:** Kim CJ, et al. Lancet 2021;398:1305-16; PMID 34627490; DOI 10.1016/S0140-6736(21)01445-8.
- **PICOT:**
  - Population: AMI after PCI, event-free on ticagrelor + aspirin for 1 month (Korea).
  - Intervention: Switch to clopidogrel + aspirin.
  - Comparator: Continue ticagrelor + aspirin.
  - Primary outcome: CV death, MI, stroke or BARC 2/3/5 bleeding at 12 months.
  - Follow-up: 12 months.
  - N randomised: 2,697.
- **Published effect (abstract):** HR 0.55 (95% CI 0.40-0.76), superiority P=0.0001.
- **Emulation sketch:** Sequential switch (switch_seq): about 1 month after MI-PCI, ticagrelor users who switch to clopidogrel vs continuers sampled within +/-30 days.
- **EHR codes / drug tokens:** I21 + PCI; ticagrelor, then clopidogrel orders; outcomes CV death, MI/stroke hospitalisation, bleeding hospitalisation.
- **Anticipated quality items:** OU 2 (BARC 2 bleeding, the dominant component, is not ascertainable, as for FRAIL-AF); EL 1 (East Asian population; event-free at 1 month); CO 0; FU 0.
- **Why add:** Positive switch-design benchmark in ACS, parallel to FRAIL-AF in AF.

#### BETAMI-DANBLOCK (2025) [tag B, in-hospital, recent]

- **Citation:** Munkhaugen J, et al. N Engl J Med 2025;393:1901-11; PMID 40888716; DOI 10.1056/NEJMoa2505985.
- **PICOT:**
  - Population: MI within 14 days with LVEF >=40% (Norway/Denmark).
  - Intervention: Beta-blocker.
  - Comparator: No beta-blocker (open-label).
  - Primary outcome: All-cause death, MI, unplanned revascularisation, ischaemic stroke, HF or malignant ventricular arrhythmia.
  - Follow-up: median 3.5 years.
  - N randomised: 5,574.
- **Published effect (abstract):** HR 0.85 (95% CI 0.75-0.98).
- **Emulation sketch:** MI admission with LVEF >=40%: beta-blocker initiated in hospital or within 14 days vs not (grace period; prior beta-blocker users excluded). Time zero = MI admission.
- **EHR codes / drug tokens:** I21; echo LVEF >=40%; beta-blocker tokens (inpatient + discharge); outcomes death, MI/stroke/HF hospitalisations, revascularisation procedures, I47.2/I49.0 events.
- **Anticipated quality items:** CO 1 (no-treatment comparator, matching the open-label trial); TZ 0 (in-hospital orders visible); TZ.d (grace period); OU 1 (composite with revascularisation and arrhythmia); FU 0 (42 mo); strong confounding (non-use is selective).
- **Why add:** Contemporary, guideline-changing, ECG-relevant (heart rate, arrhythmia). REDUCE-AMI (0.96) and REBOOT (1.04) are same-question benchmarks on an overlapping cohort (Group D), a natural test of benchmark heterogeneity.

### Lipids

#### IMPROVE-IT (2015) [tag B, add-on]

- **Citation:** Cannon CP, et al. N Engl J Med 2015;372:2387-97; PMID 26039521; DOI 10.1056/NEJMoa1410489.
- **PICOT:**
  - Population: ACS within 10 days, LDL 50-125 mg/dL.
  - Intervention: Ezetimibe + simvastatin 40 mg.
  - Comparator: Simvastatin 40 mg.
  - Primary outcome: CV death, MI, UA hospitalisation, coronary revascularisation >=30 days, or stroke.
  - Follow-up: median 6 years (7-year KM).
  - N randomised: 18,144.
- **Published effect (abstract):** HR 0.936 (95% CI 0.89-0.99); 7-year KM 32.7% vs 34.7%.
- **Emulation sketch:** Decision point = ACS admission: statin + ezetimibe initiation within 10 days vs statin alone (non-initiator of ezetimibe).
- **EHR codes / drug tokens:** I21-I24 + LDL lab; statin and ezetimibe tokens; outcome needs coronary revascularisation procedures >=30 days plus UA hospitalisation.
- **Anticipated quality items:** CO 2 (placebo add-on; non-initiator comparator); OU 1-2 (revascularisation component needs a procedure-based outcome; LODESTAR lacked it); FU 1 (>=48 mo unless truncated); small effect, so low directional power.
- **Why add:** Canonical lipid add-on benchmark; its small positive effect tests the resolution of the agreement metrics.

#### REDUCE-IT (2019) [tag B, stated-proxy, lab-defined]

- **Citation:** Bhatt DL, et al. N Engl J Med 2019;380:11-22; PMID 30415628; DOI 10.1056/NEJMoa1812792.
- **PICOT:**
  - Population: Established CVD or diabetes + risk factors, on statin, triglycerides 135-499 mg/dL.
  - Intervention: Icosapent ethyl 2 g bid.
  - Comparator: Mineral-oil placebo.
  - Primary outcome: CV death, MI, stroke, coronary revascularisation or UA.
  - Follow-up: median 4.9 years.
  - N randomised: 8,179.
- **Published effect (abstract):** HR 0.75 (95% CI 0.68-0.83).
- **Emulation sketch:** Stated active-comparator proxy (not an RCT-DUPLICATE convention): icosapent ethyl vs omega-3-acid ethyl esters (EPA+DHA) new users among statin users with a qualifying TG lab. The proxy rests on null hard-outcome trials of EPA+DHA products (STRENGTH, VITAL, ASCEND).
- **EHR codes / drug tokens:** TG lab; statin tokens; icosapent ethyl vs omega-3-acid ethyl esters (prescription); outcome MACE + revascularisation procedures + UA hospitalisation.
- **Anticipated quality items:** CO 2 (proxy; mineral-oil placebo may have inflated the benchmark); OU 1 (revascularisation and UA components); FU 1 if horizon >=48; EL 0.
- **Why add:** Strong positive benchmark with lab-defined eligibility; it would explicitly test a new, prespecified proxy. JELIS and RESPECT-EPA are alternatives (Group D).

### Valve/structural

#### DapaTAVI (2025) [tag B, decision-point, recent]

- **Citation:** Raposeiras-Roubin S, et al. N Engl J Med 2025;392:1396-405; PMID 40162639; DOI 10.1056/NEJMoa2500366.
- **PICOT:**
  - Population: Severe AS undergoing TAVI with HF history, LVEF <=40%, diabetes or CKD; not on SGLT2i.
  - Intervention: Dapagliflozin + standard care.
  - Comparator: Standard care (open-label).
  - Primary outcome: All-cause death or worsening HF (hospitalisation or urgent visit) at 1 year.
  - Follow-up: 1 year.
  - N randomised: 1,257.
- **Published effect (abstract):** HR 0.72 (95% CI 0.55-0.95); death HR 0.87.
- **Emulation sketch:** Common decision point = TAVR: SGLT2i initiation within 14-30 days of TAVR vs none (grace period, clone-censor). Excludes prior SGLT2i users.
- **EHR codes / drug tokens:** TAVR CPT 33361-33366 / ICD-10-PCS 02RF3-; SGLT2i tokens; I50/LVEF/E11/N18; outcome death + HF hospitalisation.
- **Anticipated quality items:** CO 1 (no-treatment comparator, matching the open-label trial); TZ.d (grace period); OU 1 (urgent outpatient HF visits missed); FU 0.
- **Feasibility risk:** TAVR index dates overlap the previously analysed PARTNER cohort; the 80% rule may need an interpretation (different contrast, same records).
- **Why add:** Recent positive trial anchored at a procedure.

### Other

#### VOYAGER PAD (2020) [tag B, decision-point, dose-identification]

- **Citation:** Bonaca MP, et al. N Engl J Med 2020;382:1994-2004; PMID 32222135; DOI 10.1056/NEJMoa2000052.
- **PICOT:**
  - Population: Symptomatic PAD after lower-extremity revascularisation (within 10 days).
  - Intervention: Rivaroxaban 2.5 mg bid + aspirin.
  - Comparator: Aspirin + placebo.
  - Primary outcome: Acute limb ischaemia, major vascular amputation, MI, ischaemic stroke or CV death.
  - Follow-up: median 28 months (3-year KM).
  - N randomised: 6,564.
- **Published effect (abstract):** HR 0.85 (95% CI 0.76-0.96).
- **Emulation sketch:** Common decision point = lower-extremity revascularisation: rivaroxaban 2.5 mg initiation within 10 days vs none. Time zero = procedure date + grace period.
- **EHR codes / drug tokens:** I70.2x; revascularisation CPT 37224-37235/35556-35671; rivaroxaban 2.5 mg strength; outcomes ALI (I74.3/I74.4), amputation procedures, MI/stroke, CV death.
- **Anticipated quality items:** TS 1-2 (strength); CO 2 (placebo; non-initiator comparator); TZ.d (10-day grace period); OU 1 (CV death; ALI coding); FU 0.
- **Why add:** Positive benchmark anchored at a procedure; complements BEST-CLI/SWEDEPAD 1 in a vascular area that is new to the project.

#### BEST-CLI (cohort 1) (2022) [tag A, procedure]

- **Citation:** Farber A, et al. N Engl J Med 2022;387:2305-16; PMID 36342173; DOI 10.1056/NEJMoa2207899.
- **PICOT:**
  - Population: CLTI eligible for either revascularisation with an adequate great saphenous vein.
  - Intervention: Surgical bypass.
  - Comparator: Endovascular therapy.
  - Primary outcome: Major adverse limb event (above-ankle amputation or major reintervention) or death.
  - Follow-up: median 2.7 years.
  - N randomised: 1,830.
- **Published effect (abstract):** Cohort 1 HR 0.68 (95% CI 0.59-0.79); cohort 2 HR 0.79 (0.58-1.06).
- **Emulation sketch:** Procedure vs procedure: first revascularisation for CLTI, open bypass vs endovascular. Time zero = procedure date.
- **EHR codes / drug tokens:** I70.22-I70.26; bypass CPT 35556-35671 / ICD-10-PCS 041-; endovascular CPT 37224-37235; outcome amputation and reintervention procedures + all-cause death.
- **Anticipated quality items:** EL 1 (vein adequacy not identifiable, so cohorts 1 and 2 mix); TS 0; CO 0; OU 0-1 (reintervention definition); FU 0.
- **Feasibility risk:** Shares endovascular index dates with SWEDEPAD 1 and VOYAGER PAD; select or check overlap.
- **Why add:** Strongly positive procedure-vs-procedure benchmark with procedure-coded endpoints; heavy confounding by frailty.

## Group D: considered but likely infeasible or ineligible (kept for transparency)

The 'Eligible' column refers to protocol criteria E1–E7. 'Yes' means the trial meets them but is expected to fail on feasibility, for one of three reasons:
- the drug is rare in the window;
- the cohort near-duplicates an existing or proposed one;
- there are too few events.

Reason codes: P, X, O, N, S, D and R as in the protocol §2; *near-dup* = near-duplicate cohort; *rare* = too rare; *date* = outside the 1995–2025 window.

Grouped rows count each trial separately (n trials).

| Area | Trial(s) | Year | n trials | Eligible | Reason | Representative PMID | Published effect (if noted) |
|---|---|---|---|---|---|---|---|
| AF/anticoagulation | ACTIVE A | 2009 | 1 | no | P: clopidogrel added to aspirin vs placebo; aspirin background not identifiable | 19336502 |  |
| AF/anticoagulation | AMADEUS | 2008 | 1 | no | X: idraparinux never marketed | 18294998 |  |
| AF/anticoagulation | Amulet IDE | 2021 | 1 | no | X: device brand not identifiable (Amulet vs Watchman share the LAAO code) | 34459659 |  |
| AF/anticoagulation | EPIC-CAD | 2024 | 1 | no | X: edoxaban de-escalation (Korea); edoxaban ~150 users at the site | 39225258 |  |
| AF/anticoagulation | NAVIGATE ESUS | 2018 | 1 | no | N: ESUS not identifiable; aspirin comparator | 29766772 |  |
| AF/anticoagulation | OCEAN (post-ablation rivaroxaban vs aspirin) | 2026 | 1 | no | date: published after the window; aspirin comparator; covert MRI infarcts | 41211931 |  |
| AF/anticoagulation | OCEANIC-AF / AZALEA-TIMI 71 | 2025 | 2 | no | X: asundexian/abelacimab not marketed | 39225267 |  |
| AF/anticoagulation | RE-SPECT ESUS | 2019 | 1 | no | N: ESUS not identifiable; aspirin comparator | 31091372 |  |
| AF/anticoagulation | SPORTIF V | 2005 | 1 | no | X: ximelagatran never marketed | 15701910 |  |
| AF/anticoagulation | WARSS | 2001 | 1 | no | X: aspirin comparator | 11794192 |  |
| AF/anticoagulation | X-VeRT | 2014 | 1 | yes | rare: too rare: very few events within 30-42 days of cardioversion | 25182247 |  |
| HF | AFFIRM-AHF | 2020 | 1 | no | P: placebo-controlled; same cohort as IRONMAN (alternative benchmark) | 33197395 | RR 0.79 (0.62-1.01) |
| HF | ATMOSPHERE | 2016 | 1 | yes | rare: aliskiren rarely used | 27043774 |  |
| HF | AVID | 1997 | 1 | no | X: ICD vs antiarrhythmic in arrest survivors; the antiarrhythmic-only arm is now a contraindication-selected group | 9411221 |  |
| HF | COMPANION | 2004 | 1 | no | D: comparator is optimal medical therapy (no device) | 15152059 |  |
| HF | DANISH | 2016 | 1 | no | D: ICD vs no ICD (no-device comparator) | 27571011 | HR 0.87 (0.68-1.12) |
| HF | DIGIT-HF | 2025 | 1 | no | X: digitoxin not marketed in the US | 40879434 |  |
| HF | HEART-FID | 2023 | 1 | no | P: placebo-controlled; hierarchical primary endpoint | 37632463 |  |
| HF | MADIT-CRT | 2009 | 1 | yes | near-dup: near-duplicate of the RAFT cohort (CRT-D vs ICD); keep as an alternative benchmark | 19723701 | HR 0.66 (0.52-0.84) |
| HF | MADIT-II | 2002 | 1 | no | D: ICD vs conventional therapy (no-device comparator; no common decision point) | 11907286 | HR 0.69 (0.51-0.93) |
| HF | Placebo-only HF trials without a proxy (DIG, RALES, EMPHASIS-HF, CHARM, Val-HeFT, SHIFT, VICTORIA, GALACTIC-HF, FINEARTS-HF, MERIT-HF, COPERNICUS) |  | 11 | no | P: placebo-only; no accepted active-comparator proxy (11 trials) |  |  |
| HF | SCD-HeFT | 2005 | 1 | no | P: amiodarone vs placebo; ICD vs no device has no common decision point | 15659722 |  |
| HF | WARCEF | 2012 | 1 | no | X: aspirin comparator (OTC) | 22551105 |  |
| HF | WATCH | 2009 | 1 | yes | rare: warfarin in sinus-rhythm HF not used after 2012; aspirin arm | 19289640 |  |
| Hypertension | BP-target trials (SPRINT, ACCORD-BP, STEP, BPROAD, HOT) |  | 5 | no | X: treat-to-target strategies not identifiable (5 trials) |  |  |
| Hypertension | BedMed | 2025 | 1 | no | X: dosing time not identifiable | 40354045 |  |
| Hypertension | CAMELOT | 2004 | 1 | no | P: primary contrast vs placebo | 15536108 |  |
| Hypertension | CAPPP | 1999 | 1 | yes | near-dup: ACEi arm near-duplicates ANBP2 and the comparator NORDIL; prior-therapy switch (TZ.c) and >=48-month horizon make it likely Limited | 10030325 | RR 1.05 (0.90-1.22) |
| Hypertension | CASE-J | 2008 | 1 | yes | near-dup: near-duplicate of VALUE (ARB vs amlodipine); primary paper not retrieved (Hypertension journal, outside the journal filter) |  |  |
| Hypertension | CONVINCE | 2003 | 1 | yes | rare: too rare: verapamil (INVEST verapamil arm had 316 initiators in total) | 12709465 | HR 1.02 (0.88-1.18) |
| Hypertension | HYVET | 2008 | 1 | no | P: placebo-controlled | 18378519 |  |
| Hypertension | JMIC-B | 2004 | 1 | yes | rare: primary paper not retrieved (Hypertens Res); the nifedipine-in-CAD arm is likely too small |  |  |
| Hypertension | Jikei Heart / KYOTO HEART | 2007 | 2 | no | R: retracted | 17467513 |  |
| Hypertension | STOP-Hypertension-2 | 1999 | 1 | yes | near-dup: three-arm old-vs-new drugs in age 70-84; near-duplicate of ANBP2/NORDIL | 10577635 | RR 0.99 (0.84-1.16) |
| Hypertension | TIME | 2022 | 1 | no | X: evening vs morning dosing not identifiable | 36240838 | HR 0.95 (0.83-1.10) |
| Diabetes/cardiometabolic | AMPLITUDE-O | 2021 | 1 | no | X: efpeglenatide not marketed | 34215025 |  |
| Diabetes/cardiometabolic | ELIXA | 2015 | 1 | yes | rare: lixisenatide rarely used | 26630143 | HR 1.02 (0.89-1.17) |
| Diabetes/cardiometabolic | EMPA-KIDNEY | 2023 | 1 | yes | near-dup: near-duplicate class cohort of DAPA-CKD (SGLT2i in CKD) | 36331190 | HR 0.72 (0.64-0.82) |
| Diabetes/cardiometabolic | EXAMINE | 2013 | 1 | yes | rare: alogliptin rarely used (sulfonylurea proxy) | 23992602 | HR 0.96 |
| Diabetes/cardiometabolic | FIDELIO-DKD / FIGARO-DKD | 2020 | 2 | no | P: finerenone (2021+) vs placebo; no proxy | 33264825 |  |
| Diabetes/cardiometabolic | FLOW | 2024 | 1 | no | near-dup: kidney primary endpoint; near-duplicate of the SUSTAIN-6 cohort | 38785209 |  |
| Diabetes/cardiometabolic | GRADE | 2022 | 1 | no | O: glycaemic primary outcome | 36129997 |  |
| Diabetes/cardiometabolic | Glycaemic-strategy trials (ACCORD, ADVANCE, VADT, UKPDS 33/34, Look AHEAD, BARI 2D) |  | 6 | no | X: intensity/lifestyle/strategy targets not identifiable (6 trials) |  |  |
| Diabetes/cardiometabolic | HARMONY Outcomes | 2018 | 1 | no | X: albiglutide withdrawn 2018 | 30291013 |  |
| Diabetes/cardiometabolic | IRIS | 2016 | 1 | no | N: insulin resistance without diabetes not identifiable; pioglitazone rare | 26886418 |  |
| Diabetes/cardiometabolic | ORIGIN | 2012 | 1 | no | X: glargine not identifiable (generic 'insulin' token; DEVOTE precedent) |  |  |
| Diabetes/cardiometabolic | PIONEER 6 | 2019 | 1 | yes | near-dup: near-duplicate of the SOUL cohort (oral semaglutide vs DPP-4i); alternative benchmark | 31185157 | HR 0.79 (0.57-1.11) |
| Diabetes/cardiometabolic | PROactive | 2005 | 1 | yes | rare: too rare: pioglitazone (TOSCA.IT pioglitazone arm had 96 with an ECG) | 16214598 | HR 0.90 (0.80-1.02) |
| Diabetes/cardiometabolic | RECORD | 2009 | 1 | no | X: rosiglitazone restricted 2010-2013, rarely used in the window | 19501900 |  |
| Diabetes/cardiometabolic | SCORED / SOLOIST | 2021 | 2 | no | X: sotagliflozin rarely used | 33200891 |  |
| Diabetes/cardiometabolic | SELECT | 2023 | 1 | no | P: placebo-controlled in obesity without diabetes; no accepted proxy (would be high priority if a proxy were accepted) | 37952131 | HR 0.80 (0.72-0.90) |
| Diabetes/cardiometabolic | VERTIS CV | 2020 | 1 | yes | rare: ertugliflozin rarely used | 32966714 | HR 0.97 |
| ACS/CAD/antiplatelet | ABYSS | 2024 | 1 | no | X: beta-blocker interruption not reliably identifiable | 39213187 | HR 1.16 (1.01-1.33) |
| ACS/CAD/antiplatelet | ALL-HEART | 2022 | 1 | no | N: allopurinol initiation in IHD without gout is not a routine-care decision | 36216006 | HR 1.04 (0.89-1.21) |
| ACS/CAD/antiplatelet | Aspirin-comparator trials (CAPRIE, SOCRATES, HOST-EXAM, SMART-CHOICE 3, TiCAB) |  | 5 | no | X: aspirin arm not identifiable (OTC); HOST-EXAM HR 0.73 (0.59-0.90) (5 trials) | 34010616 |  |
| ACS/CAD/antiplatelet | Aspirin-withdrawal/short-DAPT trials (TWILIGHT, TICO, STOPDAPT-2, GLOBAL LEADERS, MASTER DAPT) |  | 5 | no | X: aspirin discontinuation not identifiable (5 trials) | 31556978 |  |
| ACS/CAD/antiplatelet | Bivalirudin trials (BRIGHT-4, HEAT-PPCI, EUROMAX, MATRIX-antithrombin, HORIZONS-AMI) |  | 5 | yes | near-dup: near-duplicates of VALIDATE-SWEDEHEART; 30-day endpoints dominated by index-stay events; HEAT-PPCI RR 1.52 (1.09-2.13) is a harm benchmark (5 trials) | 25002178 |  |
| ACS/CAD/antiplatelet | CHAMPION PHOENIX | 2013 | 1 | no | O: 48-hour periprocedural endpoint | 23473369 |  |
| ACS/CAD/antiplatelet | CHANCE | 2013 | 1 | yes | near-dup: near-duplicate of POINT (China) | 23803136 |  |
| ACS/CAD/antiplatelet | COMPLETE | 2019 | 1 | no | N: multivessel disease is angiographic (not coded); staged-PCI timing | 31475795 | HR 0.74 (0.60-0.91) |
| ACS/CAD/antiplatelet | CORONARY / ROOBY / GOPCABE | 2012 | 3 | no | O: 30-day index-stay composites; pump status coding uncertain (3 trials) | 22449296 |  |
| ACS/CAD/antiplatelet | CURE | 2001 | 1 | no | P: placebo add-on; P2Y12 non-use in ACS is now selective | 11519503 |  |
| ACS/CAD/antiplatelet | Colchicine trials (COLCOT, LoDoCo2, CLEAR SYNERGY, CONVINCE-stroke) |  | 4 | no | P: placebo-controlled; no proxy (4 trials) |  |  |
| ACS/CAD/antiplatelet | DETO2X-AMI | 2017 | 1 | no | X: oxygen therapy not identifiable | 28844200 |  |
| ACS/CAD/antiplatelet | EXCEL | 2016 | 1 | no | N: left main not reliably identifiable | 27797291 | HR 1.00 (0.79-1.26) |
| ACS/CAD/antiplatelet | FAME 3 | 2022 | 1 | yes | near-dup: near-duplicate of the FREEDOM/SYNTAX cohort; repeat revascularisation in the endpoint | 34735046 | HR 1.5 (1.1-2.2) |
| ACS/CAD/antiplatelet | FIRE | 2023 | 1 | no | N: as COMPLETE | 37634150 | HR 0.73 (0.57-0.93) |
| ACS/CAD/antiplatelet | FRISC II / RITA-3 / ICTUS / SENIOR-RITA |  | 4 | yes | near-dup: near-duplicates of the TACTICS-TIMI 18 cohort; alternative benchmarks (FRISC II RR 0.78 (0.62-0.98); RITA-3 RR 0.66 (0.51-0.85); SENIOR-RITA HR 0.94 (0.77-1.14)) (4 trials) | 10475181 |  |
| ACS/CAD/antiplatelet | FULL REVASC | 2024 | 1 | no | N: as COMPLETE | 38587995 | HR 0.93 (0.74-1.17) |
| ACS/CAD/antiplatelet | ISCHEMIA | 2020 | 1 | yes | near-dup: near-duplicate of COURAGE; time zero before angiography; risk-difference benchmark | 32227755 |  |
| ACS/CAD/antiplatelet | MINT | 2023 | 1 | no | X: transfusion threshold strategy | 37952133 |  |
| ACS/CAD/antiplatelet | NOBLE | 2016 | 1 | no | N: left main not reliably identifiable; MACCE with repeat revascularisation | 27810312 | HR 1.48 (1.11-1.96) |
| ACS/CAD/antiplatelet | NORSTENT | 2016 | 1 | no | X: BMS rare after 2015; stent type | 27572953 |  |
| ACS/CAD/antiplatelet | OASIS-5 / ExTRACT / SYNERGY | 2006 | 3 | no | O: index-stay endpoints; fondaparinux rare (3 trials) | 16537663 |  |
| ACS/CAD/antiplatelet | OPTIMAAL | 2002 | 1 | yes | near-dup: near-duplicate of VALIANT (ARB vs ACEi after MI) | 12241832 | RR 1.13 (0.99-1.28) |
| ACS/CAD/antiplatelet | POPular AGE | 2020 | 1 | yes | near-dup: subset (age >=70) of the PLATO cohort | 32334703 |  |
| ACS/CAD/antiplatelet | PRAGUE-18 | 2016 | 1 | yes | near-dup: near-duplicate of ISAR-REACT 5 (which failed the size gate) | 27576777 |  |
| ACS/CAD/antiplatelet | REBOOT | 2025 | 1 | yes | near-dup: near-duplicate of the BETAMI-DANBLOCK cohort (EF >40%); alternative benchmark | 40888702 | HR 1.04 (0.89-1.22) |
| ACS/CAD/antiplatelet | REDUCE-AMI | 2024 | 1 | yes | near-dup: subset (EF >=50%) of the BETAMI-DANBLOCK cohort; alternative benchmark | 38587241 | HR 0.96 (0.79-1.16) |
| ACS/CAD/antiplatelet | RIVAL / MATRIX (access) | 2011 | 2 | no | X: radial vs femoral access not coded (2 trials) | 21470671 |  |
| ACS/CAD/antiplatelet | SYNTAX | 2009 | 1 | yes | near-dup: superset of the FREEDOM PCI-vs-CABG cohort; repeat revascularisation dominant | 19228612 | 12-mo MACCE 17.8% vs 12.4%, P=0.002 |
| ACS/CAD/antiplatelet | THALES | 2020 | 1 | no | P: placebo add-on of ticagrelor in stroke (not a US use before 2020) | 32668111 |  |
| ACS/CAD/antiplatelet | TOTAL | 2015 | 1 | yes | near-dup: near-duplicate of the TASTE cohort; composite includes index-stay shock; alternative benchmark | 25853743 | HR 0.99 (0.85-1.15) |
| ACS/CAD/antiplatelet | TRILOGY ACS | 2012 | 1 | yes | rare: prasugrel without PCI rare (TRITON failed size) | 22920930 |  |
| Lipids | ALLHAT-LLT | 2002 | 1 | no | D: usual-care comparator; pre-window | 12479764 |  |
| Lipids | CLEAR Outcomes | 2023 | 1 | no | P: placebo; bempedoic acid approved 2020 (low uptake) | 36876740 | HR 0.87 (0.79-0.96) |
| Lipids | EWTOPIA 75 | 2019 | 1 | no | D: ezetimibe vs diet in Japanese primary prevention; no decision point | 31434507 | HR 0.66 (0.50-0.86) |
| Lipids | FOURIER / ODYSSEY OUTCOMES | 2017 | 2 | no | P: placebo; no accepted proxy (2 trials) | 28304224 |  |
| Lipids | JELIS / RESPECT-EPA | 2007 | 2 | yes | near-dup: near-duplicates of REDUCE-IT (EPA; Japan) (2 trials) | 17398308 |  |
| Lipids | Niacin/fibrate add-on trials (AIM-HIGH, HPS2-THRIVE, ACCORD-Lipid, FIELD, PROMINENT) |  | 5 | no | P: placebo-controlled (5 trials) |  |  |
| Lipids | RACING | 2022 | 1 | no | X: intensity contrast (dose); risk-difference benchmark | 35863366 |  |
| Lipids | STRENGTH | 2020 | 1 | no | X: omega-3 carboxylic acids never marketed | 33190147 |  |
| Lipids | Statin-dose trials (TNT, SEARCH, A to Z) |  | 3 | no | X: dose not encoded (3 trials) | 15755765 |  |
| VTE | API-CAT / RENOVE | 2025 | 2 | no | X: DOAC dose contrast (2 trials) | 40023651 |  |
| VTE | COBRRA | 2026 | 1 | no | date: WATCH LIST: apixaban vs rivaroxaban bleeding in acute VTE, but published 2026 (outside 1995-2025). Would be Group A/C | 42269161 |  |
| VTE | CRISTAL | 2022 | 1 | no | D: cluster-crossover | 35997730 |  |
| VTE | EINSTEIN-CHOICE | 2017 | 1 | no | X: aspirin comparator | 28316279 |  |
| VTE | EPCAT II | 2018 | 1 | yes | rare: too few events (<1% VTE) | 29466159 |  |
| VTE | Hokusai-VTE / Hokusai VTE Cancer | 2013 | 2 | yes | rare: edoxaban rarely used at the site (2 trials) | 23991658 |  |
| VTE | PEITHO | 2014 | 1 | no | O: haemodynamic decompensation endpoint | 24716681 |  |
| VTE | PEPPER (NCT02810704) / EPCAT III |  | 2 | no | date: unpublished in the window (PEPPER) or published 2026 (EPCAT III) |  |  |
| VTE | PREVENT CLOT | 2023 | 1 | yes | rare: too rare (0.75% 90-day death); risk-difference benchmark | 36652352 |  |
| VTE | RE-COVER | 2009 | 1 | yes | near-dup: twin of RE-COVER II (near-duplicate) | 19966341 | HR 1.10 (0.65-1.84) |
| VTE | Thromboprophylaxis trials with venography/placebo (MARINER, MAGELLAN, APEX, ADOPT, RECORD1-4, ADVANCE-1-3, RE-NOVATE) |  | 13 | no | O: asymptomatic/venographic endpoints or placebo (13 trials) |  |  |
| Valve/structural | ATLANTIS | 2022 | 1 | yes | rare: apixaban after TAVI mixes AF and non-AF strata; rare | 35583186 |  |
| Valve/structural | COAPT / EARLY TAVR / POPular TAVI |  | 3 | no | S: size <1,000 or no-procedure comparator (3 trials) |  |  |
| Valve/structural | GALILEO | 2020 | 1 | yes | rare: rivaroxaban after TAVR without AF rare in US practice | 31733180 | HR 1.35 (1.01-1.81) |
| Valve/structural | PFO closure trials (RESPECT, CLOSE, REDUCE) |  | 3 | no | S: size <1,000; PFO-attributable stroke not identifiable (3 trials) |  |  |
| Valve/structural | PROTECTED TAVR / BHF PROTECT-TAVI | 2022 | 2 | no | O: stroke within 72 h / index stay (2 trials) | 36121045 |  |
| Valve/structural | TAVI vs SAVR trials (DEDICATE, SURTAVI, Evolut Low Risk, UK TAVI) |  | 4 | yes | near-dup: near-duplicates of the previously analysed PARTNER cohort (results seen); DEDICATE HR 0.53 (0.35-0.79) (4 trials) | 38588025 |  |
| Other | ACST-1 | 2004 | 1 | no | D: deferral comparator; pre-window medical therapy | 15135594 |  |
| Other | ADAPTABLE | 2021 | 1 | no | X: aspirin dose (OTC) not identifiable | 33999548 | HR 1.02 (0.91-1.14) |
| Other | CAMELLIA-TIMI 61 | 2018 | 1 | no | P: placebo; lorcaserin withdrawn 2020 | 30145941 |  |
| Other | CREST-2 | 2025 | 1 | no | N: stenosis severity not coded; medical-therapy (no-procedure) comparator; risk-difference benchmark | 41269206 |  |
| Other | DANFLU-2 | 2025 | 1 | no | E2: non-CV primary endpoint | 40888694 |  |
| Other | DANPACE | 2011 | 1 | yes | rare: AAIR single-lead atrial pacemakers rare in US practice | 21300730 |  |
| Other | ENTRACTE | 2020 | 1 | yes | rare: too rare: biologic arm (ORAL Surveillance precedent: 87 with ECG) | 31469238 | HR 1.05 (0.77-1.43) |
| Other | IAMI | 2021 | 1 | no | P: placebo-controlled | 34459211 |  |
| Other | ICSS / ACST-2 / ACT-1 / SPACE |  | 4 | yes | near-dup: stratum-specific near-duplicates of the CREST cohort; alternative benchmarks (ICSS 120-day stroke/death/procedural MI HR 1.69 (1.16-2.45); ACST-2 RR 1.16 (0.86-1.57)) (4 trials) | 20189239 |  |
| Other | MOST | 2002 | 1 | no | X: same dual-chamber device programmed DDDR vs VVIR; mode not identifiable | 12063369 |  |
| Other | OVER / CORAL / ASTRAL |  | 3 | no | S: size <1,000 or no-procedure comparator (3 trials) | 19826022 |  |
| Other | POISE / POISE-2 / POISE-3 | 2008 | 3 | no | O: perioperative index-stay endpoints; placebo (3 trials) |  |  |
| Other | SAVE | 2016 | 1 | no | X: CPAP vs usual care; adherence/no decision point | 27571048 |  |
| Other | TRAVERSE | 2023 | 1 | no | P: placebo-controlled testosterone | 37326322 |  |
| Other | UKPACE | 2005 | 1 | yes | near-dup: near-duplicate of the CTOPP cohort; alternative benchmark | 16014884 | HR 0.96 (death) |
| Other | WRAP-IT | 2019 | 1 | no | X: antibacterial envelope not coded | 30883056 | HR 0.60 (0.36-0.98) |

## Unbuilt design variants of pool trials (not new trials; noted for completeness)

These are counted once in the 99, as their parent trials:
- ALLHAT lisinopril vs chlorthalidone;
- ALLHAT doxazosin vs chlorthalidone.

ALLHAT lisinopril would give an ACEi-vs-thiazide contrast inside an existing cohort (near-duplicate by construction).
