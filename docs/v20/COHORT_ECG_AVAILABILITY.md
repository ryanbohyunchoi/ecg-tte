# Raw 12-lead ECG availability in NHLBI cohorts and trials on BioData Catalyst (BDC)

Compiled 2026-09-30 from public web sources only: dbGaP study pages and public FTP metadata, the public BDC Gen3 metadata and index services, NCPI catalog, BioLINCC, cohort websites, PubMed. No controlled-access data were opened. Anything marked **[unverified]** is from background knowledge or a single weak source and needs checking before use.

## Headline finding

In 2024-2026 NHLBI and the EPICARE ECG Reading Center (Wake Forest; PI Elsayed Soliman) deposited raw digital 12-lead ECG XML files on BDC. Most were deposited as separate "-Imaging" dbGaP accessions, largely under the HeartShare/AMP-HF program. Every file is registered in BDC's Gen3 index (`https://gen3.biodatacatalyst.nhlbi.nih.gov/index/index?authz=/programs/imaging/projects/<code>`). The **file-level metadata** (object URL, file name, size) is publicly listable, but the file contents need dbGaP authorization. The counts below come from enumerating that index on 2026-09-30. File names follow the pattern `<STUDY>_ECG_[cohort_]VISITnn_<YYYY>0101_<n>.xml`. Dates are coarsened to 1 January of the year; WHI dates are redacted entirely to 1900-01-01.

**Of the seven studies you named, five have raw waveforms on BDC: SPRINT, ACCORD, WHI, CHS and FHS. So do MESA, HCHS/SOL, and JHS (exam 3 only). ARIC and CARDIA do not have waveforms on BDC.**

## Summary table

| Study | Accession(s) (bold = ECG files) | On BDC? | ECG form | Exams with ECG (approximate file counts on BDC) | Echo / CMR | Meds | Outcomes | How to get waveforms | Fit for our project |
|---|---|---|---|---|---|---|---|---|---|
| **SPRINT** | phs003483 (SPRINT-BioLINCC clinical); **phs003566 (SPRINT-Imaging, ECG)**; BioLINCC HLB02021925a | y (both) | **Waveform**: 24,269 XML files, 2010-2016 (about 2.6 per participant, N=9,361); GE MAC 1200 / 12SL, read at EPICARE | Baseline, year 2, year 4, close-out (protocol 5.3.4). All files are labelled VISIT01, so assign the visit from the file year plus the BioLINCC visit dates | None (brain MRI in the SPRINT MIND subset only) | BP meds recorded and adjusted at every visit (monthly early, then quarterly); other meds [unverified] | Blinded adjudication: MI, non-MI ACS, stroke, HF, CVD death | dbGaP DAR for phs003566 + phs003483 (GRU), then analyse on BDC | **Medium-high.** Serial ECGs, adjudicated events, and randomized arms that give a built-in benchmark. But drug choice was protocolized, so there are few "natural" new-user contrasts (add-on class choice is possible) |
| **ACCORD** | phs003551 (ACCORD-BioLINCC); **phs003562 (ACCORD-Imaging, ECG)**; phs001411 (genomics) | y (both) | **Waveform**: 41,054 XML files, 2001-2014 (N=10,251) | Baseline, every 2 years, close-out (protocol 2.4.c.2). All files labelled VISIT01; use the year | None (MIND brain MRI n=632; EYE fundus photos) | Concomitant meds collected at follow-up visits [unverified frequency] | Adjudicated MI (including silent MI from ECG), stroke, CV death, HF | DAR phs003562 + phs003551 (GRU) | **High.** Diabetes drug classes were chosen by clinicians within a target-driven protocol, giving many new-user contrasts (e.g., TZD vs SU vs insulin add-on). About 4 ECGs per person; randomized arms as a benchmark |
| **WHI** | phs000200 (WHI main, dbGaP); phs004266 (WHI-BioLINCC, on BDC); **phs003824 (WHI CT+OS Imaging, ECG)** | y (Gen3 projects `img_WHI_HMB` / `img_WHI_HMB-NPU`; NCPI lists the platform as "dbGaP") | **Waveform**: GE MUSE XML, 12-lead, 10 s, 500 Hz, base64 waveforms (dbGaP description). 184,361 XML files | Clinical Trial (CT) participants only: baseline (66,900), year 3 (57,502), year 6 (48,407), year 9 (11,552) | None known in the parent study [unverified] | Medication inventory at baseline and some follow-up visits (CT years 1, 3, 6, 9 [unverified]) | Centrally adjudicated MI, CHD death, stroke, hospitalized HF, and others | DAR phs003824 (HMB / HMB-NPU) + phs004266 or phs000200 | **High.** Very large N, women only, 4 ECG waves aligned to medication-inventory visits. Caveat: acquisition dates are redacted (1900-01-01), so ECG timing is known only by visit label |
| **CHS** | phs000287 (cohort); phs001368 (TOPMed); **phs003639 (CHS-Imaging, ECG)**; BioLINCC CHS | y | **Waveform**: 39,165 XML files; derived Minnesota / Novacode / intervals (EPICARE) also in phs000287 (78 "QRS" variables) | Annual visits 1-10, 1989-1999: about 4,835 at visit 1, falling to about 2,823 at visit 10 | Echo at baseline and again later (1994-95 [unverified]) | **Annual medication inventory** (dbGaP description) | Adjudicated MI, angina, HF, stroke, TIA, claudication, death | DAR phs003639 (HMB-MDS etc.) + phs000287 | **High (best fit).** Annual ECG matched to annual med inventory, so there is an ECG shortly before nearly every initiation. Older adults, high event rates. Already used on BDC by HeartShare (JACC 2026) |
| **FHS** | phs000007 (cohort); phs000974 (TOPMed); phs000061 (SHARe Digital ECG: **derived intervals only**); **phs003593 (FHS-Cohort Imaging)**; phs003594 (FHS-BioLINCC) | y | **Waveform**: about 38,500 XML files, 1984-2022, across 6 sub-cohorts; derived intervals and Minnesota code also in phs000007/phs000061 | Original exams 18-32 (about 7.2k); Offspring exams 3-10 (about 18.3k); Gen3 exams 1-3 (about 10.4k); Omni1 exams 1-5 (about 1.5k); Omni2 exams 1-3 (about 1.0k); NOS exams 1-3 (about 0.2k) | Echo at many exams (phs003593 text lists echo "images" at these same exams; see note); cardiac CT on 4,427 people (CT zips on BDC) | Medication list at every exam [unverified detail] | Physician-panel adjudicated CHD, stroke, HF, death | DAR phs003593 (HMB-IRB-MDS / NPU) + phs000007. Local IRB approval required by consent | **High.** Longest serial ECG record, meds at each exam, adjudicated outcomes. Exams are 2-8 years apart, so the ECG-to-initiation gap is longer than in CHS |
| **ARIC** | phs000280 (cohort); phs001211 (TOPMed); phs003738 (ARIC-BioLINCC on BDC) | y (phenotypes only) | **Derived only** on dbGaP/BDC (Minnesota / Novacode / intervals; 240 "QRS" variables in phs000280). No ARIC ECG waveform accession exists in dbGaP (all study titles checked through phs004xxx) | Every visit (V1 1987-89 through V5 2011-13 and later) [unverified exact list]. Waveforms exist (CNN on raw V1 ECGs, n=14,613; CNN on V3 and V5) | Echo at visit 5 and later [unverified] | Meds at each visit and at annual/semiannual calls [unverified] | Adjudicated MI, CHD death, HF (from 2005), stroke | ARIC-approved manuscript or ancillary study proposal, then DMDA and data request to the ARIC Coordinating Center (aricdata@unc.edu). Waveforms held by EPICARE [unverified route]. Off BDC, with fees | **Medium.** Excellent cohort, but waveforms need ARIC approval and a separate transfer |
| **MESA** | phs000209 (cohort); phs001416 (TOPMed); phs003288 (MESA-BioLINCC); **phs003703 (ECG Tracing Repository)**; phs003702 (Echo image repository); phs004423 (cardiac CT images) | y | **Waveform**: 11,394 XML files | Exam 1, 2000-02 (6,783); Exam 5, 2010-12 (4,611) | CMR at exam 1 (and exam 5 [unverified]); **raw echo DICOM at exam 6** (phs003702) | Medication inventory at every exam | Adjudicated CVD events | DAR phs003703 + phs000209 or phs003288 | **Medium.** Excellent imaging companions, but only 2 ECG waves 10 years apart, so few initiations have a recent ECG |
| **JHS** | phs000286 (cohort); phs000964 (TOPMed); phs003740 (JHS-BioLINCC); **phs003747 (JHS-Images)** | y | Exam 1: **JPG images** of ECGs (3,521; not waveforms). Exam 3: **XML waveforms** (2,608) | Exams 1 (2000-04) and 3 (2009-13) | Echo exam 1; CMR exam 2 or 3 [unverified which] | Meds at each exam [unverified] | Adjudicated CHD, stroke, HF | DAR phs003747 + phs000286 or phs003740 | **Low-medium.** Waveforms only at exam 3; exam 1 would need image digitization |
| **CARDIA** | phs000285 (cohort); phs003739 (CARDIA-BioLINCC on BDC) | y (phenotypes only) | Derived only [unverified variable content]; no waveform accession found | Years 0, 7, 20, 25, 30 [unverified] | Echo years 5, 25, 30 [unverified] | Meds each exam [unverified] | Adjudicated events (few, young cohort) | CARDIA ancillary study / coordinating center [unverified] | **Low.** Young cohort, few events, no waveforms on BDC |
| **HCHS/SOL** | phs000810 (cohort); phs001395 (TOPMed); **phs003963 (Imaging: HCHS/SOL, ECG)**; phs003543 (NSRR sleep) | y | **Waveform**: 13,157 XML files (larger files, about 395 KB median) | Visit 1 only (2008-11); visit 2 ECGs not in the index | ECHO-SOL ancillary echo [unverified] | Meds at visits [unverified] | Adjudicated CVD via annual follow-up [unverified] | DAR phs003963 + phs000810 | **Low.** Single ECG, younger cohort, few events |
| *REGARDS* (extra) | **phs004265 (REGARDS ECG)** | y | **JPG images only** (37,072; not waveforms) | Visit 1 2003-07 (24,976); visit 2 2013-16 (12,096) | None | Pill-bottle review at the in-home visit [unverified] | Adjudicated stroke, CHD | DAR phs004265 | **Low** for waveform work (needs digitization) |

Counts are ECG files, not participants. Some participants have more than one file per visit, and each consent group is a separate Gen3 project; the counts above sum all consent groups.

## Per-study notes

### SPRINT
- phs003566 is described as "provides access to ECG signals data from the SPRINT clinical trial. The clinical phenotyping and outcomes data from the trial are associated with SPRINT-BioLINCC, phs003483". The DOI creator is Soliman (EPICARE); the DOI is 10.60645/BDC-8JS3-T2T3.
- Gen3 project `img_SPRINT_GRU` holds 24,269 `SPRINT_ECG_VISIT01_<year>0101_<n>.xml` files (median about 198 KB).
  - Every file carries the label VISIT01, so the ECG wave has to be recovered from the file year and the BioLINCC visit/ECG datasets.
  - The project also includes a data dictionary (xlsx), a readme (txt), and the Gen3 PFB (avro) files that map files to subjects.
- Protocol v5.0, section 5.3.4: "A 12-lead ECG is obtained at baseline and at the 2 and 4 year follow-up visits and close-out visit". ECGs were read by the ECG reading center. The SPRINT LVH paper describes GE MAC 1200 recording, reading at EPICARE, and GE 12-SL 2001 processing.
- Events were adjudicated by adjudicators blinded to arm. There is no echo or CMR.
- Fit: in-trial non-randomized drug-class contrasts are possible, and the randomized comparison offers a ground-truth check. But treatment was algorithmic, so few prescribing decisions are "confounded" in the usual sense.

### ACCORD
- phs003562 (ACCORD-Imaging) likewise "provides access to ECG signals data", linked to ACCORD-BioLINCC phs003551. It contains 41,054 XML files dated 2001-2014, all labelled VISIT01.
- Supporting documents in the project: "Review Process for ACCORD ECG XML files.pdf", "HeartShare-ECG-DE-ID-QC.pdf", and a data dictionary.
- Protocol 2.4.c.2: 12-lead ECG "at baseline ..., at the biennial follow-up visits (i.e., every 2 years) and close-out visit". Silent MI was ascertained by the ECG Reading Center.
- There is no echo or CMR. The MIND brain MRI substudy had 632 participants; the EYE substudy has fundus photos.
- Fit: the best trial for new-user contrasts, because glucose-lowering (and BP- and lipid-lowering) drug choice within arms was clinician-driven.

### WHI
- The phs003824 description states: ECGs "were given to all clinical trial participants at baseline and in years 3, 6, and 9". The ECGs are "12 lead 10 seconds ECGS sampled at 500Hz via GE ECG machines and process via GE MUSE system ... exported from GE MUSE ... in XML format"; the waveforms are base64. "All acquisition dates within files and in file names have been set to January 1, 1900".
- The Gen3 file names carry VISIT01/03/06/09. Counts per visit are in the table (184,361 XML files in total).
- 67,979 consented subjects (HMB 59,668; HMB-NPU 8,311). Observational Study (OS) participants had no study ECGs; only CT participants did.
- WHI-BioLINCC (phs004266, 136,270 subjects) is on BDC; the parent phs000200 is also on dbGaP. Outcomes are centrally adjudicated.
- Fit: very strong statistically. The main design constraint is timing: without ECG dates, "ECG before initiation" has to be defined as the ECG from the visit at or before the medication inventory that shows the initiation.

### CHS
- phs003639 (CHS-Imaging, 5,539 subjects). The dbGaP text does not say "ECG files", but the Gen3 index lists 39,165 `CHS_ECG_VISITnn_*.xml` files across annual visits 1-10 (1989-1999).
  - The years on visit 4/5 files start at 1984, so a few file dates are odd; check against the phenotype data.
  - Per-visit zip bundles are also provided.
- The parent phs000287 states that annual exams included "medication inventory, ECG, ..." and less often echocardiography. Adjudicated events: MI, angina, HF, stroke, TIA, claudication, mortality.
- Derived Minnesota / Novacode / intervals are in the phenotype data (EPICARE).
- Fit: best match to the new-user design, because an ECG and a medication inventory were taken at the same annual visit for 10 years.

### FHS
- phs000061 ("Framingham SHARe Digital ECG") holds **derived measurements only**. These are Bonner-program intervals from Original exams 16-18 and Offspring exam 2, plus scanned-paper intervals (QT, QTpeak, RR, PR, QRS) from Original exam 11, Offspring exam 1 and Gen3 exam 1.
- phs003593 (FHS-Cohort Imaging, v2) text says "Echocardiogram images, available from ... Original Cohort: exams 18-32; Offspring cohort: exams 3-10; Third Generation, NOS and OMNI-2 cohorts: exams 1-3; OMNI-1 cohort: exams 1-5", plus CT for 4,427 participants.
- **What the Gen3 index actually shows is different:** about 38,500 `FHS_ECG_<cohort>_VISITnn_*.xml` files at exactly those exams, plus about 4,400 `CT*.zip` files. No echo files are listed.
  - Either the dbGaP description mislabels electrocardiograms as echocardiograms, or echo will be added later [unverified]. Confirm with BDC help or FHS.
  - The cohort codes in the file names (00, 01, 02, 03, 07, 72) read as Original, Offspring, NOS, Gen3, Omni1, Omni2; this is the standard FHS idtype convention (inferred).
- FHS began recording digital ECGs in 1986 (Marquette MAC/PC, later MAC 5000) and manages them in MUSE 8 (EHJ Digital Health 2026, ECG-age paper).
- The HeartShare JACC 2026 paper used "raw 12-lead ECG waveform data ... from XML files at baseline" for 4,102 FHS Gen3, 4,062 CHS and 5,962 MESA participants. The analysis ran entirely on BDC.
- FHS data not in repositories require an FHS Research Application, possibly with fees.

### ARIC
- There is no ECG waveform accession on dbGaP or BDC. ARIC-BioLINCC phs003738 (15,277 subjects) is on BDC with phenotypes. phs000280 carries derived ECG variables (about 240 variables match "QRS"; "Minnesota" matches are inflated by the Minnesota field center).
- ARIC waveforms clearly exist and have been used for deep learning:
  - Akbilgic et al., EHJ Digital Health 2021: CNN on raw 12-lead baseline ECGs, 14,613 participants.
  - Butler et al., CVDHJ 2023: the same model validated in MESA.
  - Yao et al., EHJ Digital Health 2025: CNN ECG score at visits 3 and 5.
  - These were Wake Forest / EPICARE-affiliated groups.
- Access: an ARIC-approved manuscript proposal or ancillary study, then a DMDA and data request to the ARIC Coordinating Center, with fees. Waveforms would presumably come via EPICARE [unverified].

### MESA
- phs003703 ("Electrocardiogram Tracing Repository includes ECG tracings performed during MESA Exam 1 ... and during MESA Exam 5") is on BDC. It holds 11,394 XML files.
- phs003702 holds echo DICOMs from Exam 6 (2016-18; Early HF ancillary). phs004423 holds cardiac CT images.
- Baseline CMR measured "ventricular mass and function" (BioLINCC).
- Medications were collected at every exam, and events are adjudicated.
- The two ECG waves are 10 years apart, which limits ECG-at-initiation designs. MESA is better suited as an ECG-to-CMR/echo validation cohort.

### JHS
- phs003747 ("Jackson Heart Study - Images", 3,883 subjects) is on BDC.
  - Exam 1: 2 MB JPG images of ECGs (3,521).
  - Exam 3: XML waveforms (2,608).
  - An image-to-subject ID mapping file is included.
- JHS phenotyping includes echo (exam 1) and cardiac MRI, with adjudicated events (dbGaP phs003747 text).

### CARDIA
- CARDIA-BioLINCC phs003739 is on BDC. No ECG waveform accession was found. Exam, echo and ECG schedules above are [unverified].

### HCHS/SOL
- phs003963 (13,175 subjects) holds visit-1 XML only (2008-2011). The description does not mention ECG, but the file names do.

### Other BDC resources seen while searching
- HeartShare harmonized HF-trial collection: phs003989 and phs004460. These are clinical data; the constituent trials (TOPCAT, SOLVD, SCD-HeFT, HF-ACTION, etc.) are BioLINCC-on-BDC.
- The ALLHAT-BioLINCC phenotype data (phs004021, 42,418 subjects) is on BDC, but no ALLHAT ECG waveform accession was found.
- BioLINCC-on-BDC accessions show no variables in the dbGaP variable browser; their data are distributed as files on BDC.

## Practical access notes
1. One DAR per accession: request the ECG ("-Imaging" / "Tracing Repository") accession **and** the matching phenotype accession (BioLINCC or cohort). BDC documentation says BioLINCC data on BDC need dbGaP authorization even if you already have BioLINCC approval.
2. Files are Gen3 DRS objects in `/programs/imaging/projects/img_<STUDY>_<consent>`. Each project ships a data dictionary, a de-identification QC document, and PFB (avro) subject/sample files for linking files to subject IDs.
   - Moving files into a BDC Seven Bridges workspace goes through the Gen3 export/DRS import [unverified exact steps].
3. Dates in file names are coarsened to the year (WHI fully redacted). Take visit dates from the phenotype data.
4. The format is XML with base64 waveforms (WHI is explicitly GE MUSE XML, 500 Hz). Other studies are probably also MUSE XML exported by EPICARE [unverified]. The HCHS/SOL files are about twice the size, so check the lead and length layout.
5. Consent constraints: FHS requires IRB approval (HMB-IRB). Several cohorts have NPU (not-for-profit only) or DS-CVD consent groups; each group is a separate project.

## References
- BDC BioLINCC datasets and dbGaP requirement: https://bdcatalyst.gitbook.io/biodata-catalyst-documentation/written-documentation/explore-available-data/pic-sure-for-biodata-catalyst-user-guide/data-in-bdc-pic-sure/available-data-and-managing-data-access/biolincc-datasets
- BDC release notes 2025-01-15 (SPRINT-BioLINCC phs003483, etc.): https://bdcatalyst.gitbook.io/biodata-catalyst-documentation/written-documentation/release-notes/2025-01-15-nhlbi-biodata-catalyst-ecosystem-release-notes
- BDC Gen3 imaging collections (ECG, echo, CT, DICOM): https://bdcatalyst.gitbook.io/biodata-catalyst-documentation/written-documentation/explore-available-data/gen3-discovering-data
- BDC Gen3 metadata (per study): https://gen3.biodatacatalyst.nhlbi.nih.gov/mds/metadata/phs003566.v1.p1.c1 (swap in other accession.consent values)
- BDC Gen3 index (file listing): https://gen3.biodatacatalyst.nhlbi.nih.gov/index/index?authz=/programs/imaging/projects/img_SPRINT_GRU
- dbGaP public study metadata: https://ftp.ncbi.nlm.nih.gov/dbgap/studies/ (GapExchange XML per study)
- SPRINT-Imaging: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003566.v1.p1 ; NCPI https://ncpi-data.org/studies/phs003566 ; SPRINT-BioLINCC https://ncpi-data.org/studies/phs003483
- SPRINT BioLINCC: https://biolincc.nhlbi.nih.gov/studies/sprint/ ; Protocol v5.0: https://www.sprinttrial.org/public/Protocol_Current.pdf
- SPRINT ECG methods (MAC 1200, EPICARE): https://pmc.ncbi.nlm.nih.gov/articles/PMC11215828
- ACCORD-Imaging: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003562.v1.p1 ; NCPI https://ncpi-data.org/studies/phs003562 ; ACCORD-BioLINCC https://ega-archive.org/studies/phs003551
- ACCORD BioLINCC and protocol: https://biolincc.nhlbi.nih.gov/studies/accord/ ; https://biolincc.nhlbi.nih.gov/media/studies/accord/Protocol.pdf
- WHI Imaging: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003824.v1.p1 ; NCPI https://ncpi-data.org/studies/phs003824
- CHS Imaging: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003639.v1.p1 ; NCPI https://ncpi-data.org/studies/phs003639 ; CHS cohort https://ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000287 ; https://chs-nhlbi.org/
- FHS Digital ECG (derived): https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000061.v9.p4
- FHS Imaging: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003593.v2.p1 ; NCPI https://ncpi-data.org/studies/phs003593
- FHS data access: https://www.framinghamheartstudy.org/fhs-for-researchers/data-available-overview/
- FHS digital ECG history (ECG-age and cognition): https://pmc.ncbi.nlm.nih.gov/articles/PMC12966501/
- MESA ECG Tracing Repository: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003703.v1.p1 ; NCPI https://ncpi-data.org/studies/phs003703 ; Echo repository https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003702.v1.p1 ; exam components https://www.mesa-nhlbi.org/about/components ; BioLINCC https://biolincc.nhlbi.nih.gov/studies/mesa/
- JHS Images: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003747.v1.p1 ; NCPI https://ncpi-data.org/studies/phs003747
- HCHS/SOL Imaging: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs003963.v1.p1 ; NCPI https://ncpi-data.org/studies/phs003963
- REGARDS ECG: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs004265.v1.p1
- ARIC data access: https://aric.cscc.unc.edu/aric9/researchers/Obtain_Submit_Data ; ARIC-BioLINCC https://ega-archive.org/studies/phs003738
- HeartShare data sharing: https://amphf.org/for-scientists/data-sharing/
- Desai AS et al. Predicting HF from 12-lead ECGs using AI: HeartShare/AMP-HF pooled cohort (FHS, CHS, MESA on BDC). JACC 2026;87:990-1005. https://doi.org/10.1016/j.jacc.2025.10.065 (PMID 41493294)
- Akbilgic O et al. ECG-AI for HF prediction (ARIC raw ECGs). EHJ Digital Health 2021. https://doi.org/10.1093/ehjdh/ztab080
- Butler L et al. Generalizable ECG-AI for 10-year HF risk (ARIC-trained, MESA-validated). CVDHJ 2023. https://doi.org/10.1016/j.cvdhj.2023.11.003
- Yao Y et al. Multimodal AF prediction (ARIC V3/V5 CNN ECG score). EHJ Digital Health 2025. https://doi.org/10.1093/ehjdh/ztae081
- Brant LCC et al. ECG deep learning for AF (FHS, UKB, ELSA-Brasil). Circ Arrhythm Electrophysiol 2025. https://doi.org/10.1161/CIRCEP.125.013734
