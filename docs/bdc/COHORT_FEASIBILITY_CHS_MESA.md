# CHS and MESA: desk feasibility for running the LATENT-RCT pipeline in NHLBI cohorts

Written 2026-10-16 from **public sources only**: the dbGaP FTP data dictionaries and variable reports (phs000287.v7.p1, phs000209.v13.p3), the public BDC Gen3 index, cohort websites and published papers. No controlled data were opened.
- Counts here are public aggregates (dbGaP variable reports or papers), or estimates marked as such.
- Raw notes stay in the session scratchpad and are not committed.

**Goal (user decision 2026-10-16):** replicate the pipeline in cohorts:
1. new-user active-comparator emulation;
2. PS ± AI-ECG from the latest ECG before initiation;
3. 1:1 matching;
4. balance on held-out physiology;
5. HR versus an era-matched RCT.

The plan is CHS with the full pipeline and MESA for the balance endpoint only. The next step is the count script `scripts/bdc/cohort_count.py`, which runs in BDC and outputs aggregates only.

## 1. CHS (phs000287.v7.p1; ECG XML phs003639)

**Population.** 5,531 subjects in the release; `PERSTAT` = 1 for the original cohort (4,903, entry 1989–90) and 2 for the African-American cohort (628, entry 1992–93).
- Consent groups: c1 HMB-MDS 5,353; c2 HMB-NPU-MDS 171; c3 and c4 (DS-CVD) 1–10 each.
- Subject key: `dbGaP_Subject_ID` / `Individual_ID`.
- On BDC the tables are named `phs000287.v7.<pht>.p1.c<k>.<TABLE>.<consent>.txt.gz`. Older v6 copies are also present; the script takes the latest version per consent group.

**Visits and medications.** There is an annual clinic visit each year from 2 to 11 (1989–99).

| Year | Table |
|---|---|
| Year 2 (baseline) | `BASE1` (history, meds, BP) + `BASE2` (echo, ECG, labs) |
| Years 3 and 4 | `YR3`, `YR4` |
| Year 5 | `YR5OLD` (original cohort) + `YR5NEW` (new-cohort baseline) |
| Years 6–11 | `YR6`–`YR11` |

- **Timing:** `STDYTIME` = days since entry. Do **not** use the `YEAR` variable: every value is 1960.
- **Class flags:** identical 0/1 flags (0 = no, 1 = yes) in every visit table, with no raw drug names:
  - ACE inhibitor: `ACE06`, with `ACED06` for ACE + diuretic;
  - ARB: `A2A06`, non-zero only from Year 8;
  - CCB: `CCB06`, with sub-types `AMLOD06`, `NIFSR06`/`NIFIR06`, `DLTSR06`, `VERSR06`;
  - thiazide: `HCTZ06`, `HCTZK06`; loop diuretic: `LOOP06`;
  - beta-blocker: `BETA06`, `BETAD06`;
  - statin: `STTN06`;
  - aspirin: `ASPIRIN` (asked yearly; `ASA06` undercounts);
  - also `WARF06`, `DIG06`, `NSAID06`, `ESTRGN06`.
- **Prevalent users, baseline → Year 11** (public variable reports):
  - ACE inhibitor 303 → 613;
  - CCB 568 → about 950;
  - thiazide 545 → 331;
  - beta-blocker about 600;
  - statin 90 → 511.
- **Initiation rate:** Psaty (JAMA 1993) found 144 new antihypertensive starters from baseline to Year 3, preferring CCB and ACE inhibitors.

**ECG.** 39,227 XML files at visits `VISIT01`–`VISIT10`, where VISITnn = CHS year nn+1.
- Files per visit: 4,841 → 2,830.
- Per-visit zips are also provided. The linkage key is the Gen3 PFB (`imaging_file` → `subject`) and `Documentation/DD_CHS_Imaging_c1.csv`.
- **Design consequence:** a drug start is only known to fall between two annual visits, so the pre-initiation ECG is the one from the **previous visit**, about 1 year earlier.

**Held-out physiology** (on everyone at fixed visits):
- **Echo** at baseline (`BASE2`; original cohort only) and Year 7 (both cohorts):
  - LV mass: `NEWLVM43` at baseline, `MMLVMS43` at Year 7;
  - EF: `LVEF43` at baseline, `LVFNCT43` grade at Year 7;
  - LA size: `MMLAD43`;
  - wall thickness: `MMVSTD43`, `MMLVWD43`;
  - E/A: `DPMEP43`/`DPMAP43` (units differ between the two visits).
- **Labs** at Years 2 and 5 (partly Year 9): creatinine `CRE44`, LDL `LDLADJ`, HDL, triglycerides, glucose, insulin, albumin, uric acid, fibrinogen; CRP (`CRPBLADJ`, `CRPYR5`); cystatin C (`CYSTATC`, Year 5). No NT-proBNP.
- **BP:** `AVZMSYS` (Years 2–3), `AVESYS` (Years 4–11). Weight; gait (`TIME27`).
- **Vascular:** carotid IMT (`ULTRABL`, `ULTRAYR5`, `ULTRAY11`, `IMT_POLACK`); ABI `AAI` at Years 2, 5 and 11.
- **Spirometry:** Years 2, 6 and 9.
- **Never in a held-out panel (ECG-derived):** the `*42`/`*21` variables, `ECGLVH`, `MAJABN`, `MINABN`, `LVM42`.

**Outcomes.**
- `EVENT_SUMMARY`: incident MI, CHF, stroke, TIA, claudication, angina, CHD and death, with days to each from entry. Follow-up runs to about 2003: 2,807 deaths, 1,254 HF, 790 strokes, 697 MIs.
- `CHS_Event16`: one row per event, to about 2015.
- `ICD9`: hospital codes, usable for bleeding.

**Candidate emulations** (era 1989–99, age 65 or older). Benchmark HRs below are from memory and must be verified before use.

| # | Comparison (new users at a visit; ECG from the previous visit) | RCT benchmark | Estimated new users per arm (not a count) |
|---|---|---|---|
| 1 | CCB (dihydropyridine) vs thiazide | ALLHAT amlodipine vs chlorthalidone: CHD RR 0.98; HF 1.38 | CCB 800–1,200; thiazide 400–700 |
| 2 | ACE inhibitor vs thiazide | ALLHAT lisinopril vs chlorthalidone (CHD 0.99; HF 1.19); ANBP2 (0.89) | ACE inhibitor 700–1,000 |
| 3 | ACE inhibitor vs CCB | STOP-2, age 70–84 | as above |
| 4 | Thiazide vs beta-blocker | MRC trial in older adults (1992; no head-to-head HR) | beta-blocker 400–600 |
| 5 | Statin start vs none | PROSPER, age 70–82: HR 0.85 | statin 550–750 |
| 6 | (optional) aspirin start vs none | ASPREE (CVD 0.95; major bleeding 1.38); a known CHS confounding example (Kronmal 1998) | large |

Not feasible: BAFTA (too few warfarin starters aged 75 or older with AF), DIG (needs HF with known EF), SHEP (placebo).

## 2. MESA (phs000209.v13.p3; BioLINCC phs003288; ECG XML phs003703)

**Population and exams.** The dbGaP release has 6,429 of 6,814 participants (key `sidno`).
- Tables: `MESA_Exam1Main` to `MESA_Exam4Main` and `MESA_Exam5Main` (pht001116–20, pht003091).
- Exam timing in days since exam 1: `E12DyC` (mean 598), `E13DyC` (1,167), `e14dyc` (1,767), `e15dyc` (3,458).

**Medication flags** (0/1, `<class><exam>c`):
- ACE inhibitor: `ace`, `aced`;
- ARB: `a2a`, `a2ad`;
- CCB: `ccb`;
- thiazide: `hctz`;
- beta-blocker: `beta`, `betad`;
- statin: `sttn`;
- any antihypertensive: `htnmed`;
- also `asa`, `warf`.
- Statin users at exams 1–5: 945 / 1,159 / 1,377 / 1,450 / 1,662.

**ECG.** XML at exam 1 (6,783) and exam 5 (4,611) only.
- The trailing file number is **not** a participant ID; linkage goes through the Gen3 PFB.
- **Design consequence:** the pre-initiation ECG is the exam-1 ECG, 1.5–3 years before an exam-2 or exam-3 start.

**Held-out physiology at exam 1.**
- **Cardiac MRI** (n = 4,740): LV mass `olvedm1`, `olvedv1`, `olvesv1`, `olvef1`, `olvsv1`, segmental wall thickness.
- **CAC:** `agatpm1c`. **IMT:** `ccafwm1`. **ABI:** `abi1c`.
- **Labs:** creatinine/eGFR (`cepgfr1c`), cystatin C, lipids, glucose, CRP, IL-6, fibrinogen, D-dimer, UACR.
- **NT-proBNP:** `ntprbnp1` (n = 5,486; pht002140).
- **Never in a held-out panel (ECG-derived):** 118 variables (`ecglvh1c`, Minnesota, Novacode, intervals) and pht002195.

**Outcomes.**
- dbGaP `MESA_ThruYear2011Events` (pht001123):

| Outcome | Events |
|---|---|
| MI | 196 |
| Stroke | 170 |
| HF | 224 |
| Hard CHD | 268 |
| Hard CVD | 426 |
| All CVD | 604 |
| Death | 694 |

- BioLINCC (phs003288) has events through 2020. **HRs need the BioLINCC events**; with events only to 2011 they would be underpowered.

**Candidate comparisons (balance endpoint):**

| Comparison | Size | Notes |
|---|---|---|
| **Statin start vs none at exam 2 or 3** | about 850–900 starters, about 600–650 with exam-1 CMR (estimate) | Published: 517 starters by exam 2 (Carr 2010) and 872 at exams 2–5 among 3,113 statin-naive people with CMR (Strand 2018). Clearly feasible |
| ACE inhibitor/ARB vs CCB starters at exams 2–3 | about 200–250 per arm (estimate) | Borderline |
| Any first antihypertensive vs none | about 600 with CMR | |

## 3. Next steps
1. **Import into the BDC project** with Gen3 "Export to Seven Bridges":
   - **CHS:** project `CHS_HMB-MDS_` (phs000287 c1, plus c2 if approved) txt.gz tables. All of them are fine (about 30 MB); the needed ones are `BASE1`, `BASE2`, `YR3`–`YR11`, `YR5OLD`/`YR5NEW`, `EVENT_SUMMARY`, `CHS_Event16`, `ICD9`. Also the ECG imaging project for phs003639, **XML format**. The `tsv/imaging_file.tsv` it produces is the ECG-to-participant key (about 5 GB).
   - **MESA:** phs000209 c1/c2 txt.gz tables, plus the phs003703 XML (about 2.3 GB).
2. **Run** `python scripts/bdc/cohort_count.py --cohort CHS`, and then `--cohort MESA`. They report new users per comparison and arm, how many have an ECG at the previous visit (CHS) or at exam 1 (MESA), and how many also have held-out echo or CMR. Counts of 1–10 are suppressed.
3. **Fix the cohort trial list from those counts**, using the ≥ 350 smaller-arm rule. Then write the cohort protocol (eligibility, time zero, outcomes, held-out panel) **before** any ECG-adjusted estimate, as for Figure 5.
