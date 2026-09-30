# v2.0 UK Biobank feasibility: inventory, candidate emulations and plan (discovery only)

- **Date:** 2026-09-30. Discovery and feasibility only; no emulation, PS model, balance or HR was run.
- **Access:** read-only throughout (S3 `ls` and header or schema streaming; bounded `find`/`ls` on `/mnt/raid0`).
- **Outputs:** intermediates (listings, `feasibility_counts.py`, `feasibility_counts.json`) are in
  `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-ukb-feasibility/` (umask 077, restricted, not committed).
- **Reporting:** aggregates only; counts 1–10 are shown as `<11`. No participant rows or eids appear here.
- **Relation to v1.5:** UKB was already used in v1.5, with 3 prevalent-user emulations at the imaging visit
  (`docs/V15_EXTERNAL_SUMMARY.md`, `docs/PROTOCOL_V1_5_EXTERNAL.md`, `scripts/v15/v15_ukb_*.py`). This document
  inventories everything available, checks designs better than prevalent use, and proposes the v2.0 UKB arm.

## 0. Bottom line

1. **Everything needed for an ECG × CMR × PGS UKB arm is already on disk except GP prescriptions.**
   - 12-lead resting ECGs at the imaging visit: 93,262 ECGs from 84,107 participants, already converted
     and already embedded with our BCL encoder.
   - CMR LV phenotypes for 40,302 participants at instance 2; 35,053 of them also have an instance-2 ECG.
   - PGS for 6 cardiac traits in 58,034 genotyped participants, 56,756 of whom have an instance-2 ECG.
   - HES first occurrences to 2022-10-31 and death registrations to 2024-07.
2. **GP prescription records (`gp_scripts`) are not anywhere on disk or in either bucket.** In the current
   UKB release they cover only about 45% of participants and end in 2016–2017. Only about 12.7k
   imaging visits (2014–2016) predate that end date. As a result, **a GP-defined new-user design
   with the ECG before initiation is not feasible today** (§3.3).
   - This changes if UKB releases the England-wide GP data. The UK Government's February 2026 data
     provision notice paves the way for that, on a restricted cloud platform. Release status is
     unverified as of this audit.
3. **Feasible now, from self-reported medication (field 20003, UKB coding 4):**
   - **Five antihypertensive emulations meet ≥300 ECG in the smaller arm and ≥50 events in both designs:**
     ONTARGET, ALLHAT, ASCOT-BPLA, LIFE and VALUE.
     - The **prevalent-user** design (D1) is the v1.5 design.
     - The new **"incident between baseline and imaging"** design (D2) excludes users at the 2006–10
       baseline visit.
   - **CAPRIE (clopidogrel vs aspirin) passes only in D1.**
   - **In every design, the ECG is recorded on treatment.** It is taken at the same visit that defines
     exposure, so it is a post-initiation covariate. This is the dominant validity threat.
4. **Infeasible:**
   - **No DOAC, SGLT2i, DPP-4i, GLP-1RA, ticagrelor/prasugrel, ARNI or ivabradine entries exist in coding 4:**
     DOAC vs warfarin, SGLT2i vs DPP-4i/SU, ARNI and ticagrelor comparisons are therefore impossible
     without GP data.
   - **No dose data:** statin intensity cannot be defined.
   - **Too few participants or events:** INVEST, AFFIRM, IDEAL, metformin vs SU and TRANSFORM-HF.
5. **UKB's unique value is not RCT agreement, which is weak here. It is:**
   - **CMR-anchored held-out balance and plasmode.** CMR LVEF, volumes and mass are measured at the same
     visit as the ECG, in about 35k people.
   - **A direct PGS vs ECG comparison** of orthogonal diagnostics, as in German et al., Nat Genet 2025.
   - Recommended: run these as a **physiology benchmark** that does not depend on an RCT, plus D2
     emulations as secondary external replication.

## 1. Data inventory

### 1.1 S3 bucket A: `spinup-001718-ukbiobank-src` (profile `ukb_s3`; read-only)

The name the task used, "ukb-s3", is the local profile name. That bucket name does not exist, and
the IAM user cannot call ListBuckets.

| Path | Content | Size | Notes |
|---|---|---|---|
| `ukb47034.{enc,enc_ukb,csv,tab,sd2,r,html}`, `my_ukb_data*.{rds,tsv}`, `biobanksrc.rds` | Main dataset: application 71033, basket 2011112, run 47034 (created 2021-05-20; 14,492 data columns; 2,192 fields in `fields.ukb`) | csv 30.3 GB, tab 29.2 GB, tsv 32.1 GB, enc_ukb 14.3 GB | **Present:** 20205, 6025, 12336/12338/12340, 22330–22338, 20002/20003, 41270/41280 (and 41271/41272/41282), 40000–40002, 42000/42026, biochemistry 30690–30780, BP 4079/4080, BMI 21001, 22420/22421. **Absent:** GP record counts 42038–42040, first occurrences 130000+, genetic PCs 22009, PGS 26200+, CMR IDPs 24100+ |
| `filtered_ukb47034.csv` | Named-column subset of run 47034 (2,125 columns; biochemistry, death, HES dates, etc.) | 1.86 GB (2024-04) | Same file copied to `/mnt/raid0/lsd26/deid_safe/ARISE_data_model/` |
| `ecg/` | **Field 20205 resting 12-lead ECG XML (CardioSoft)** | 45,416 objects, 37.9 GB (2021-06): 42,386 instance-2 XML, 3,016 instance-3 XML; 42,766 unique participants | Plus `ukb47034.bulk` (20205_2 = 42,390; 20205_3 = 3,016), `ukbfetch`, import logs. Superseded by the May 2025 extract (§1.3) |
| `first1kecgs/` | First 1,000 of the above XMLs | 0.85 GB | Test copy |
| `ukb/omop_database/`, `ukb/omop_csv_database/` | OMOP CDM (person, death, observation_period, condition_occurrence, measurement, drug_exposure; 52 parts each) built by bb2238 (`ukb_sparse_omop.py`) | 0.11 GB / 0.54 GB | `drug_exposure.source` = "UKB", i.e. **self-reported 20003 at visits, not GP scripts**. Conditions come from 41270, 40001, 42000/42006 and 20002 |
| `ukb/cohorts/ukb_250429.parquet` (+ `_vit_embeddings.npy`) | 7,021-row ECG-image mortality cohort with ViT embeddings (bb2238, 2025-04) | 1 MB + 14 MB | Different task |
| `ukb/metadata/ukb_ecg_metadata.parquet` | ECG metadata for 45,415 XMLs (HR, PR, QRS, QT, QTc, diagnoses, ECGDate) | 4 MB | |
| `ukbconv`, `ukbfetch`, `ukbmd5`, `ukblink`, `gfetch`, `encoding.ukb`, `*.key`, `.ukbkey` | UKB legacy tools and access keys | small | **Key files were not opened** |
| `rohan_explore/`, `.ipynb_checkpoints/`, `.vscode/`, `.Trash-1000/` | Scratch | small | |

### 1.2 S3 bucket B: `spinup-001a89-biobankmri-1` (profile `biobank-mri-1`; read-only)

| Path | Content | Size | Notes |
|---|---|---|---|
| `scout/` (20207) | CMR scout DICOM zip | 49,295 objects, 333 GB (i2 45,618; i3 3,668) | 2021-10 download |
| `longheart/` (20208) | CMR long-axis cine | 49,197 objects, 438 GB (i2 45,520; i3 3,666) | |
| `aorticdisten/` (20210) | Aortic distensibility | 46,755 objects, 281 GB | |
| `cinetag/` (20211) | Cine tagging | 46,572 objects, 183 GB | |
| `lvoutflow/` (20212) | LVOT cine | 46,696 objects, 173 GB | |
| `bloodflow/` (20213) | Phase-contrast flow | 46,443 objects, 252 GB | |
| (absent) 20209 | **Short-axis cine not downloaded** | – | Not needed: derived LV/RV IDPs exist (next row) |
| `structured_measurements/ukb674780.*` | **CMR-derived phenotypes basket**: application 71033, basket 2018229, run 674780 (2023-09-13; 367 columns) | csv 0.70 GB | Fields 22420–22427 (Siemens inline LV function: LVEF, LVEDV, LVESV, SV, CO, CI, BSA, HR); **24100–24181** (Bai et al. IDPs: LV/RV/LA/RA volumes and EF, LV mass, wall thickness, strain, aortic distensibility); 12671–12702 (pulse-wave analysis at imaging); 25931 |
| `ukb47034.{csv,enc,enc_ukb}` | Second copy of the 2021 main basket | 30.3 GB | |
| `preprocessed/{longheart,longheart_may2025,a3c_mri2echo*}` | CMR long-axis → AVI (MRI-to-echo work) | 11–26 GB each | eo287/bb2238 projects |
| `unzipped/` | Partial DICOM unzip | ~4 GB | |
| `clmbr/ukb_ecg_image_embeddings_with_labels*.parquet` | ECG-**image** embeddings with labels (2025-01) | 5 × 125 MB | Not our signal encoder |
| `evan_workspace/` | `47034_mri.csv`, `ukb47034_mri_ids.csv` (2.2 GB), AVR/AS matching tables, models (`.pt`), dictionary | 3.4 GB | eo287; AS/AVR work |
| `old_server_backup/{assist,ecgage,hcm,ukb_exclude}` | Old project code and outputs | <0.1 GB | Includes a withdrawal/exclusion list (`ukb_exclude`) |

### 1.3 Local disk (read-only unless under `/mnt/raid0/rbc58`)

| Path | Content | Size / N | Already computed? |
|---|---|---|---|
| `/mnt/nfs_yale_ecg/biobank/raw_data/` | 2021 20205 XMLs | 45,417 files | – |
| `/mnt/nfs_yale_ecg/biobank/numpy_may_2025_extract/` and **`/mnt/raid0/bb2238/signals/preprocessed/ukb_2025/`** | **May 2025 ECG extract as npy**, float32 (12, 5000), 500 Hz 10 s, mV (raw/200 minus a 500-sample median filter); leads I, II, III, aVR, aVL, aVF, V1–V6 | 93,262 ECGs; 84,107 participants; i2 82,300, i3 10,962, both 9,155 | Yes (bb2238 `setup_ukb_signals.ipynb`) |
| `/mnt/nfs_yale_ecg/biobank/ukbb_may_2025_extract_ecg_metadata.csv` | Per-ECG device and filter metadata; one device type, 0.01–100 Hz, 50 Hz filter on, no pacemakers | 93,262 rows | – |
| **`/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-ukb-bcl/restricted_ukb_bcl_embeddings.parquet`** | **Our BCL 256-d embeddings of all 93,262 UKB ECGs** (µV fix applied; 0 failures; embedding geometry matches Yale, `validation.json`) | 97 MB | **Yes (v1.5)** |
| `/mnt/nfs_yale_ecg/biobank/signal/`, `bb2238/signals/preprocessed/ukb/` | 2021 npy (older naming) | ~42–45k | Superseded |
| `/mnt/raid0/bb2238/local_image_saves/ukb/ukb_may_2025/` | ECG PNG renders | 93,267 | Image-model inputs |
| `/mnt/raid0/bb2238/ecg_ascvd/backup/data/ukb/` | 1- and 12-lead ASCVD model predictions on the 2025 ECGs | 2 × 373 KB | Yes |
| **`/mnt/raid0/rbc58/prs/ukb/data.csv`** | **RAP-style participant export** (p-field names; 2026-03; 547 columns, 28 fields): 31, 34, 52, 53 (i0–i3), 1239, 2966, 4080, **20003 (i0–i3 × 48)**, 20160, 21000, 21022, 22001, 22006, **22009 (40 PCs)**, 22019/22020, 23104, 30690/30700/30750/30760/30780, 40000, **41270/41280**, 42000, 42006 | 830 MB | Used by v1.5 |
| `/mnt/nfs_yale_ecg/biobank/ukb_working_file.csv` | Derived outcomes incl. CV death primary/secondary (deaths to 2020) | 140 MB | Used by v1.5 (Ryan-approved) |
| `/mnt/raid0/rbc58/prs/bfile/ecg/ukb_allchr.QC.final.{bed,bim,fam}` | QC'd imputed genotypes, 58,034 participants, ~6.09 M variants | 84 GB bed | – |
| **`/mnt/raid0/rbc58/prs/prs_output/ukb/{af,as,cad,dcm,hcm,hf}/`** | **PGS Catalog scores** (AF PGS005168, AS PGS005252, CAD PGS003725, DCM PGS004862, HCM PGS004910, HF PGS005097), 58,034 each; 56,756 also have an i2 ECG | small | **Yes** (plus HERMES HF-partitioned scores, cardsbio) |
| `/mnt/raid0/rbc58/prs/ukb/{ukb_features*.parquet, ukb_cohort/, ecg_ascvd_preds.parquet, *_results_raw.csv}` | ECG/CMR/carotid/fundus "biological age" outputs and ECG-ASCVD features for the PRS project | ≤ 30 MB each | Yes |
| `/mnt/raid0/eo287/clmbr/processed_data/ukb/` | MEDS-like tables (`ukb_events_pooled` 2.04 M rows, `ukb_snomed_events`, `ukb_lab_events`, `ukb_meds` = self-report), **CLMBR embeddings** for 41,902 people, censored at the i2 date | ~0.4 GB | Yes; our re-censored copy is `/mnt/raid0/rbc58/clmbr/ukb/ukb_clmbr_embeddings_censored_v2.parquet` |
| `/mnt/raid0/rbc58/ecg-tte/audits/claude-v15{,s,d}-ukb-*` | v1.5 trial directories (ONTARGET, ALLHAT, ASCOT; eligibility, CV-death and death-only sensitivities; ARISTOTLE marked infeasible) | – | Yes |
| `/mnt/raid0/lsd26/deid_safe/ARISE_data_model/` | `filtered_ukb47034.csv`, PCE-risk working file, ID key spreadsheet (not opened) | – | Other project |
| `/mnt/raid0/rbc58/ecg-tte/reference/ukb/coding4.tsv` | Public coding-4 table (self-report drugs) | – | Yes |

**Not found anywhere:** `gp_scripts`, `gp_clinical`, `gp_registrations`, `hesin*` record-level tables (HES
episodes, OPCS procedures, admission dates), `death_cause` record-level, Olink proteomics and NMR
metabolomics.
- **Where record-level tables live:** bb2238's RAP notebooks (`/mnt/raid0/bb2238/ecg_ascvd/backup/src/ukb/backup/
  pyspark_ukbrap_extraction.ipynb`, `omop_test.ipynb`) list these tables in the application's RAP (DNAnexus)
  dataset. They are therefore accessible **on the RAP** (application 71033) but were never exported.
- **Procedures:** OPCS procedure codes (41272) exist only in the S3 2021 basket, not in `data.csv`.

## 2. Coverage (aggregates)

| Quantity | N |
|---|---|
| Imaging visit (instance 2) attenders in `data.csv` | 91,979 (2014-04 to 2024-10) |
| Repeat imaging (instance 3) attenders | 13,769 (2019-05 to 2024-10) |
| Instance-2 attenders with an instance-2 12-lead ECG | 82,255 |
| Instance-2 ECG and CMR LV phenotype at instance 2 (22420 or 24100/24103) | **35,053** (35,025 among `data.csv` i2 attenders) |
| CMR LV phenotypes at i2, any (22420: 39,615; Bai IDPs: 39,286) | 40,302 (2023 basket; later imaging not yet included) |
| Instance-3 ECG and instance-3 CMR | 1,731 |
| i3 attenders with an earlier i2 ECG | 11,263 |
| i2 attenders with 20003 medications reported | 55,778 (i0 60,346 among these people; i3 6,820) |
| Genetic PCs present (i2 attenders) | 89,829 |
| Local genotypes/PGS with an i2 ECG | 56,756 |
| CLMBR embeddings (censored at i2) | 41,902 |
| HES first-occurrence data end | 2022-10-31 (i2 visits on or before this date: 60,163) |
| Death registry max date | 2024-07-07 (censor at 2024-06-30, v1.5 rule) |

**Imaging-visit (instance 2) attendances by year (`data.csv`):**

| Year | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Visits | 1,962 | 5,365 | 5,421 | 8,090 | 12,091 | 13,846 | 2,159 | 1,578 | 11,768 | 18,078 | 11,621 |

- 45% of instance-2 visits (41,467, in 2022–24) have almost no HES follow-up before the 2022-10 data end.
- Death-only outcomes follow them to 2024-06.

**GP linkage:** not measurable locally (fields 42038–42040 are not in any basket on disk).
- Per UKB documentation, primary-care data exist for about 230,000 participants (≈45%), with extracts
  ending in 2016 or 2017 depending on the supplier ([UKB Primary Care Linked Data v2](https://biobank.ndph.ox.ac.uk/showcase/showcase/docs/primary_care_data.pdf);
  [UKB GP data](https://www.ukbiobank.ac.uk/about-our-data/types-of-data/healthcare-records/access-to-our-participants-gp-data/)).
- 12,748 instance-2 visits (about 11k with an ECG) took place before 2017. Assuming 45% are linked, that gives
  **≈5k GP-linked people with any GP follow-up after their ECG, and a median of ≈1 year** of it.
- The February 2026 UK Government data provision notice allows coded GP data (diagnoses, prescriptions,
  referrals, labs) for all England participants. These data will be accessible only on a restricted cloud platform, after a
  data-sharing agreement and DHSC security approval
  ([UKB news](https://www.ukbiobank.ac.uk/news/major-milestone-for-health-research-as-uk-government-decision-enables-access-to-uk-biobank-volunteers-gp-patient-data/);
  [Digital Health, 2026-02](https://www.digitalhealth.net/2026/02/uk-biobank-granted-access-to-gp-patient-data-for-research/)).
- **This is the one change that would make GP-defined new-user emulations with a pre-initiation imaging
  ECG feasible.** Check its release status on the RAP before planning around it.

## 3. Candidate emulations

### 3.1 Designs checked

- **D1, prevalent user at imaging (v1.5 design).**
  - Arms: 20003 at i2. Time zero: i2 date. ECG: i2, lag 0.
  - Exposure: the ECG is on treatment; duration of use is unknown.
- **D2, incident between baseline and imaging (new).**
  - Arms: on the arm drug at i2 but on neither arm drug at i0 (or i1, if attended). Time zero: i2.
  - Exposure: initiated within 4–10 years before time zero, which reduces depletion of susceptibles
    but not by much.
  - The ECG is still on treatment.
  - Baseline biomarkers (i0) precede initiation.
- **D3, initiation between i2 and i3 (true new user; the ECG precedes initiation).**
  - Arms: on neither arm drug at i0–i2 and on exactly one at i3. Time zero: i3 date.
  - ECG: i2, recorded before initiation (lag = i3 − i2).
- **D4, GP new user after the ECG (the requested design).** New use from `gp_scripts` within 365 days
  after the i2 ECG, or with the ECG within 365 days before the first prescription. Time zero: first
  prescription. Needs GP data (§2).

**Common elements:**
- Arm definitions: exactly one arm (users of both removed); class exclusions as in `scripts/v15/v15_ukb_common.py`.
- Hypertension trials: hypertension gate, and no prior I50.
- Outcomes: HES 41270/41280 first occurrence strictly after time zero, plus 42000/42006 and death (40000).
- Censoring: HES end 2022-10-31 for composites; 2024-06-30 for death-only.
- Horizon: trial duration.
- Counts: arm N, N with an ECG, N with ECG + CMR, and events among ECG holders.
- Cohort overlap: the share of one cohort's ECG holders who appear in another cohort.

Limitation of the outcome definition: 41280 holds only the first date per ICD-10 code, so recurrent
events and events in people with an earlier code are not observable.

### 3.2 Feasibility table

Criteria: ≥300 with an ECG in the smaller arm and ≥50 primary-outcome events among ECG holders.

Counts are A / B; "ECG+CMR" is the subset of the ECG counts that also has instance-2 CMR.

| Trial (benchmark) | Comparator (A vs B) | Primary outcome (UKB proxy) | Data needed | D1 N with ECG (ECG+CMR); events | D2 N with ECG (ECG+CMR); events | D3 N with ECG; events | Feasible | Reason |
|---|---|---|---|---|---|---|---|---|
| **ONTARGET** (HR 1.01) | ARB vs ACEi | death/MI/stroke/HF | 20003, HES, death | 2,569 / 4,937 (1,606 / 3,154); 124 / 243 | 1,108 / 2,398 (646 / 1,413); 43 / 87 | 30 / 84; 0 | **Y (D1, D2)** | Active comparator; ELITE II as secondary |
| **ALLHAT** (HR 0.98) | amlodipine vs thiazide | death/MI (fatal CHD + MI proxy) | same | 3,449 / 1,374 (1,991 / 929); 85 / 45 | 2,348 / 536 (1,268 / 352); 47 / 19 | 107 / 22; <11 | **Y (D1, D2)**, near-duplicate flag | 69–75% of its records are also in ASCOT/VALUE |
| **ASCOT-BPLA** (HR 0.90) | amlodipine vs atenolol-type BB | death/MI | same | 3,456 / 1,912 (2,030 / 1,193); 88 / 99 | 2,486 / 1,020 (1,364 / 583); 48 / 42 | 113 / 49; <11 | **Y (D1, D2)** | Largest event count among CCB comparisons |
| **LIFE** (HR 0.87) | ARB vs atenolol-type BB | death/MI/stroke | same | 2,142 / 2,055 (1,364 / 1,264); 68 / 102 | 1,162 / 1,052 (690 / 588); 34 / 38 | 30 / 48; <11 | **Y (D1, D2)**, near-duplicate flag | 72% (D1) / 55% (D2) of its records are also in ONTARGET (shared ARB arm). LVH eligibility (ECG-LVH) could be applied, but the ECG is on treatment |
| **VALUE** (HR 1.04) | ARB vs amlodipine | death/MI/HF (cardiac composite) | same | 1,846 / 3,350 (1,184 / 1,957); 77 / 96 | 993 / 2,406 (599 / 1,303); 37 / 57 | 29 / 108; <11 | **Y (D1, D2)**, near-duplicate flag | 63–66% of its records are also in ALLHAT/ASCOT |
| **CAPRIE** (RRR 8.7%) | clopidogrel vs aspirin (prior CAD/stroke/PAD) | death/MI/ischaemic stroke | 20003, HES, 42000/42006 | 344 / 1,690 (202 / 1,074); 12 / 53 | 197 / 680; <11 / 14 | <11 / 19; 0 | **Y (D1 only, marginal)** | D2 smaller arm is 197; 23-month horizon |
| INVEST (HR 0.98) | verapamil vs atenolol (HTN + CAD) | death/MI/stroke | same | 14 / 1,089; <11 / 52 | <11 / 567 | 0 / 25 | N | Verapamil rarely used |
| IDEAL (HR 0.89) | atorvastatin vs simvastatin post-MI (dose unknown) | death/MI | same | 688 / 187; 35 / 11 | 322 / 48 | <11 | N | Simvastatin arm 187; no dose, so no intensity contrast |
| Statin intensity (e.g. TNT, SEARCH) | high vs moderate | MACE | GP scripts with dose | – | – | – | N | Coding 4 has no dose |
| AFFIRM (HR 1.15) | rhythm (antiarrhythmic) vs rate control, AF | death | 20003, HES I48 | 72 / 986; 21 events | 48 / 646 | <11 / 33 | N | Antiarrhythmic arm too small |
| Metformin vs SU (SPREAD-DIMCAD) | metformin vs sulfonylurea | death/MI/stroke | 20003 | 1,149 / 52; 45 / <11 | 739 / 28 | 31 / <11 | N | SU arm tiny (SU monotherapy is rare) |
| TRANSFORM-HF (HR 1.02) | torasemide vs furosemide, HF | death | 20003 | 0 / 77 | 0 / 58 | – | N | No torasemide users |
| ARISTOTLE / ROCKET (DOAC vs warfarin) | DOAC vs warfarin, AF | stroke/SE | GP scripts | – | – | – | **N (now); unknown with new GP data** | Coding 4 has no DOACs |
| SGLT2i vs DPP-4i / SU (e.g. CVOT-type) | SGLT2i vs DPP-4i or SU | MACE / HF | GP scripts | – | – | – | **N (now); unknown** | Not in coding 4; 2016–17 GP data predate uptake |
| ACEi vs ARB, BB vs CCB, thiazide vs CCB with GP new use (D4) | as above | as above | `gp_scripts` (RAP), HES | – | – | – | **N with current GP data (estimated); unknown with new GP data** | ≈5k GP-linked ECG holders before the GP data end, ≈1 year window; estimated <300 per arm for any class pair |

**D3 is infeasible for every comparison:** at most 113 people with an ECG in the larger arm, 49 in the
smaller arm, and 0 to <11 events. Only 5,302 instance-3 visits precede the HES data end.

**Near-duplicates:**
- ALLHAT, ASCOT and VALUE share the amlodipine arm; 60–75% of each cohort's records appear in another.
- LIFE shares the ARB arm with ONTARGET.
- Project precedents: ACCOMPLISH was excluded at 96% overlap; ACTIVE W was flagged at 69%.
- **Recommendation:** prespecify ONTARGET, ASCOT and CAPRIE as the core. Report ALLHAT, VALUE and LIFE
  as flagged cluster members, with comparator-cluster inference (as in v1.7).

### 3.3 Why D4 (GP new user after the ECG) is not feasible today

- The imaging ECG programme started in 2014, and only about 14% of i2 visits (12,748) predate 2017.
- Current GP extracts end in 2016–2017 and cover about 45% of participants.
- Requiring GP initiation within 365 days after an ECG before about mid-2017 leaves roughly 5k eligible
  people. Among 60–75-year-olds, antihypertensive initiation incidence is a few percent per year, so
  any class pair would have far fewer than 300 initiators.
- If the new England-wide GP data reach the RAP with coverage past 2022, D4 becomes the primary UKB
  design. In that case:
  - use the 2014–2022 ECGs (≈45k with HES follow-up);
  - include the DOAC and SGLT2i comparisons;
  - use HES dates to 2022+ as outcomes.

## 4. Proposed held-out physiology panel (never used in any PS)

1. **CMR, instance 2, same visit as the ECG** (22420–22427; 24100–24181):
   - LVEF, LVEDV/LVESV indexed, SV, CO/CI, LV mass and mass/volume;
   - RV EDV/ESV/EF;
   - LA/RA maximum volume and EF;
   - regional wall thickness (mean, maximum);
   - global circumferential/radial/longitudinal strain;
   - aortic distensibility (ascending, descending).

   About 35k people have these, and 55–65% of ECG holders in each D1/D2 cohort have CMR. Derived flags:
   LVEF < 50%, LVH by mass index, LA enlargement.
2. **Vascular:** pulse-wave analysis at imaging (12671–12702: central SBP, augmentation index, PWV-type
   indices, cardiac output).
3. **Vitals at i2:** SBP/DBP (4080 automated; mean of 2), heart rate, BMI (23104/21001).
   - Heart rate and SBP are partly treatment-affected (β-blocker), so report them separately.
4. **Biomarkers (i0/i1, pre-imaging):** total/LDL/HDL cholesterol, creatinine/eGFR, HbA1c; add CRP and
   cystatin C from the 2021 basket.
   - These are 4–10 years old at time zero. **They are pre-initiation in D2**, which is useful.
   - NT-proBNP is not in UKB core biochemistry. It exists only in Olink proteomics for a subset, which is
     not on disk, so it is listed as unknown.
5. **Genetics (orthogonal diagnostic, not a physiology target):** the 6 local PGS (AF, AS, CAD, DCM, HCM,
   HF), with the option to add UKB standard PRS (field 26200+) from the RAP.

**Caveat for every panel item:** it is measured on treatment at the same visit, except biomarkers in D2.
Balance on these variables therefore mixes confounding and treatment effects. The one exception is
the plasmode below, where treatment is simulated and this caveat does not apply.

## 5. ECG embedding plan

**Status: done.** No new compute is required for the existing extract.
- **Input format:** UKB 20205 is a GE CardioSoft XML with 10 s × 12 leads at 500 Hz.
- **Conversion (bb2238):** `raw[:, :5000] / 200` → mV, minus a 500-sample median-filter baseline.
- **Leads:** order I, II, III, aVR, aVL, aVF, V1–V6, which matches the Yale layout. Hardware is uniform:
  one device, 0.01–100 Hz, 50 Hz notch.
- **Embedding:** BCL via `scripts/v15/v15_ukb_ecg_embed.py` → `scripts/bcl_embed_uv.py` (×1000 → µV,
  no 250 Hz flags). 93,262 of 93,262 embedded (about 80 ECG/s on one GPU, i.e. about 20 min);
  `claude-v15-ukb-bcl/validation.json`.
- **Reduction:** 32 PCs. Fit the PCA on the Yale reference, as in the main analysis, and project UKB onto
  it. Also compare UKB-fitted PCs, because UKB PC1 variance differs slightly from Yale.

**To do:**
1. **QC.** Reuse the Yale QC. Also flag flat or noisy leads, and pacing (none recorded in the metadata).
2. **Domain shift.** Report embedding–phenotype R² in UKB for age, sex, HR, QRS, QTc and CMR LVEF/mass,
   compared with Yale echo. The plasmode needs this R² (v1.9 G2 showed bias removal ≈ 100 × R²).
3. **Newer ECGs.** If UKB releases imaging after May 2025, fetch the new 20205 files on the RAP or via
   the approved route, then convert and embed them with the same code.
4. **Optional.** AI-ECG phenotype heads (LVEF < 40%, LVH, AF) on UKB, for German-style SMD diagnostics.

## 6. Recommended analysis plan (UKB arm of v2.0; to be registered before any outcome is used)

**A. Physiology benchmark (primary UKB contribution; independent of any RCT).**
1. **Population:** i2 attenders with an ECG and CMR (≈35k). Covariates: demographics, i0–i2 self-report,
   HES first occurrences before i2, and the PS ladder (demo → minimal-7 → sparse → hdPS → clinical),
   exactly as at Yale.
2. **Plasmode with CMR-LVEF as the hidden confounder:**
   - simulate treatment from the observed covariates plus LVEF (and, separately, LV mass and LA volume);
   - simulate the outcome from the observed covariates plus LVEF, with true HR = 1.0 and 0.6;
   - vary the confounding strength over the grid used in v1.9 G2;
   - estimate with and without the ECG PCs at each rung;
   - report bias removed as a percentage, RMSE, coverage and MCSE;
   - add placebo ECGs (shuffled, noise-32).

   CMR is measured at the same visit as the ECG, which removes the echo timing mismatch present in Yale.
   It is the cleanest test of "ECG recovers hidden cardiac physiology".
3. **PGS vs ECG:** in the same simulation, substitute the PGS (HF, CAD, AF, DCM, HCM) for the ECG.
   - Following German et al., we expect PGS R² with LVEF to be low, so PGS should remove little bias.
   - Report ECG, PGS and ECG + PGS side by side, as a function of R².

**B. Emulations (secondary external replication).**
1. **Designs:** D2 as primary UKB design (ONTARGET, ASCOT, CAPRIE-D1 core; ALLHAT, VALUE, LIFE flagged),
   D1 as sensitivity (v1.5 continuity).
2. **Arms per trial:** unadjusted, sparse, sparse + ECG, hdPS200, hdPS200 + ECG, clinical (+ i0
   biomarkers), CLMBR subset, and PGS arms (sparse + PGS, sparse + ECG + PGS).
3. **Primary estimand:** held-out balance on the §4 panel, reporting |SMD| < 0.1 % and C-statistic
   (a CMR-specific block).
   - Report German-style Fig-2 diagnostics: SMDs of the ECG phenotype and the PGS across design steps.
4. **RCT agreement** is reported descriptively with v1.5 metrics (|Δlog HR|, z², φ), because of the
   on-treatment ECG and prevalent/incident-at-visit exposure. It is pooled with Yale and MIMIC by RCT
   only in sensitivity analyses.
5. **Negative controls:** cataract, inguinal hernia, cholelithiasis (v1.5 NCO set).

**C. Conditional on new GP data (D4).** Re-register GP new-user emulations with time zero at the first
prescription and the ECG within 365 days before it. Candidates: ACEi vs ARB, BB vs CCB, thiazide vs
CCB, DOAC vs warfarin, SGLT2i vs DPP-4i/SU. This becomes the headline UKB emulation set if feasible.

## 7. Effort, risks and compliance

### Effort
| Step | Estimate |
|---|---|
| D2 cohort builder: extend `scripts/v15/v15_ukb_build.py` with a `--design d2` flag and LIFE/VALUE/CAPRIE specs | 0.5–1 day |
| CMR panel extraction to `/mnt/raid0/rbc58` (a copy of `ukb674780.csv` is needed; aggregate outputs only) | 0.5 day |
| Plasmode (reuse v1.9 G2/v2.0 G2 engine) + PGS arms | 1–2 days |
| Emulation runs (v15 engine) | < 1 day compute |
| D4, if GP data are released on the RAP | 1–2 weeks (RAP-side Spark extraction, re-registration) |

### Risks
1. **On-treatment ECG and CMR (D1/D2).**
   - β-blockers alter HR/PR, and RAS blockers alter LV mass. The held-out balance and RCT comparisons are
     therefore confounded by treatment effects.
   - Mitigation: prefer the plasmode, report HR/PR-sensitive items separately, and restrict to D2 with
     older initiation.
2. **Short HES follow-up** (2022-10) for the 2022–24 imaging waves. About 45% of ECGs contribute
   death-only follow-up.
   - Events are modest: 65–370 per emulation in D1, 66–130 in D2. CI widths will match the weak v1.5
     results.
3. **Healthy-volunteer imaging cohort.** Low event rates, low confounding by indication, and a narrow
   LVEF distribution (few LVEF < 40%). The plasmode confounding range is therefore limited by the
   realised LVEF variance.
4. **First-occurrence outcomes** miss recurrent events. Exposure from self-report has no dates or doses.
5. **Overlap across the antihypertensive cohorts** (§3.2) inflates apparent replication.
6. **CMR basket from 2023** covers ≈40k people. A later IDP release would add more.

### Compliance (conservative; confirm with the application PI before use)
- **Application:**
  - Local material belongs to **UK Biobank application 71033**. This is visible in the ukbconv logs and
    key-file names; the key files were not opened, and no secrets were printed.
  - **Baskets:** 2011112 (run 47034, 2021) and 2018229 (run 674780, CMR IDPs, 2023).
  - `data.csv` is a RAP-style export (2026-03). The RAP notebooks reference `app71033`; that it belongs to the
    same application is assumed, not verified.
- **Scope.**
  - The approved scope of application 71033 was not visible on disk. The confirmed uses are: prior
    ECG-ASCVD, ECG-age, HCM/AS, PRS and HF-subphenotype projects, and v1.5 of this project.
  - **Confirm that pharmacoepidemiological target-trial emulation and methods for confounding control
    are covered.** If not, file a scope change.
- **Access model.**
  - UKB now provides data through its RAP. New GP data will be released only on a restricted cloud
    platform.
  - **Do not extract GP or HES record-level tables from the RAP to local disk** unless the application
    terms allow it. Run D4 cohort building on the RAP and export aggregates only.
  - Whether the local copies (the 2021/2023 baskets, `data.csv`, the ECG and CMR bulk files) are still
    permitted under current terms needs PI confirmation.
- **Third parties and AI services.**
  - The UKB MTA/Access Agreement forbids passing participant data to anyone outside the approved
    application.
  - Participant-level UKB data must not be sent to external services. That includes cloud LLM or AI
    APIs, and also external collaborators not on the application.
  - Agents working on this project may only produce aggregate outputs and code. This audit printed no
    rows or eids; S3 listings containing eids stayed in the restricted audits directory.
  - The Yale-trained BCL encoder is applied locally, and the UKB embeddings are derived data. They stay
    under `/mnt/raid0/rbc58` and are never committed or shared.
- **Returns and reporting.**
  - UKB requires return of derived variables and results (e.g. embedding-derived phenotypes) after
    publication. Plan a return dataset.
  - Report aggregates only, with small cells suppressed. Our rule (1–10) is at least as strict as
    NHS-derived HES/death output rules.
  - Honour participant withdrawals: apply the latest UKB withdrawal list before every analysis. A
    `ukb_exclude` list exists in the MRI bucket, but its date is unknown.
- **Other users' data.** bb2238, eo287 and lsd26 folders and both buckets were read in place only.
  - The CMR IDP CSV was streamed through memory for counts and never written to disk.
  - Any future local copy goes under `/mnt/raid0/rbc58/ecg-tte/`.

## Appendix: reproducibility

- **Counts:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-ukb-feasibility/feasibility_counts.py` →
  `feasibility_counts.json`.
  - Arm classes come from `scripts/v15/v15_ukb_common.py`, plus drug-level regexes for atorvastatin,
    simvastatin, clopidogrel, verapamil, torasemide and furosemide.
  - D1 ONTARGET reproduces the v1.5 cohort: 2,567 / 4,931 people with an ECG and 124 / 243 events, vs
    2,569 / 4,937 here after re-deriving ECG availability from the file list.
- **S3 listings:** `s3_*_l1.txt` and `s3_*_full.txt` in the same directory. These are restricted
  because the file names contain eids.
