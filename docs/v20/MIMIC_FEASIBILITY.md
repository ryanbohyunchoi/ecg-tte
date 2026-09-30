# v2.0 MIMIC-IV feasibility: inventory, prior work, candidate emulations and plan (discovery only)

- **Date:** 2026-09-30. Discovery and feasibility only. No PS model, balance, HR or RCT comparison was run.
- **Access:** read-only throughout. I used bounded `ls`/`find` (depth ≤ 6, with timeouts), header/schema
  reads, and DuckDB aggregate queries. Nothing outside `/mnt/raid0/rbc58` was written.
- **Outputs:** intermediates are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-mimic-feasibility/`
  (umask 077, restricted, not committed):
  - `stage_icu.py` and `feasibility_screen.py`: the screen code;
  - `panel_coverage.py`: held-out panel coverage;
  - `screen_results.{json,md}` and `panel_coverage.json`: aggregate results;
  - `stage/`: restricted per-trial cohort parquet and ICU subsets.
- **Reporting:** aggregates only; counts of 1–10 are shown as `<11`. No subject IDs, dates or note text
  appear here. Note text was never opened.
- **Relation to v1.5:** MIMIC-IV was already used in v1.5 for 5 in-hospital emulations
  (`docs/PROTOCOL_V1_5_EXTERNAL.md`, `docs/V15_EXTERNAL_SUMMARY.md`, `scripts/v15/v15_mimic_*.py`). This
  document inventories all MIMIC assets on our mounts, records what was run, screens about 25 further
  candidate trials against the v2.0 feasibility rules, and proposes the MIMIC arm of v2.0.

## 0. Bottom line

1. **All the MIMIC data we need is already on disk.** The copies are:
   - **MIMIC-IV 3.1** (hosp and icu), in two byte-identical copies:
     - bb2238's copy, which v1.5 used;
     - Ryan's own copy under `/mnt/raid0/rbc58`.
   - **MIMIC-IV-ECG 1.0:** 800,035 12-lead ECGs from 161,352 subjects. About 130.6k of those subjects
     also have MIMIC-IV admissions.
   - **On NFS:** MIMIC-IV 2.2, MIMIC-IV-Note 2.2, MIMIC-IV-ED 2.2 and MIMIC-CXR.
   - **MIMIC-IV-ECHO 0.1:** study lists and DICOMs. The DICOMs cover about 4.6k subjects.
   - **A MIMIC-IV-Echo structured-measurement table** in another user's folder: 206,488 echo studies from
     91,372 subjects, with LVEF, dimensions, diastolic grade, RV function and valves. Its release version
     and DUA status are unverified (§1, §6.3).
2. **Our BCL MIMIC pipeline already exists and has run end to end.**
   - v1.5 (2026-09-26) converted 18,034 MIMIC ECGs to the Yale npy layout. It fixed the aVL/aVF lead order
     and converted units to mV.
   - It embedded them with the Yale BCL checkpoint (µV ×1000 fix).
   - It built 5 complete trial directories, all with `READY_COHORT`, `READY_ECG` and `READY_OUTCOMES`
     markers, each with a death co-primary and NCOs: PLATO, ARISTOTLE, ROCKET AF, TRANSFORM-HF and COMET.
   - It ran the v1.5 engine on them: estimates, RCT panel, plasmode and capture.
   - **These trials have not been re-analysed with the v1.6+ held-out-balance machinery.** The v1.6
     documents list "external MIMIC/UKB confirmation deferred".
   - No MIMIC-wide BCL embedding exists. Other groups' MIMIC ECG models were run on case-control cohorts
     for VHD prediction, which does not transfer to our trials.
3. **Feasibility screen.** I screened 30 trial/variant definitions with a simplified version of the v1.5
   cohort logic. Rules: ≥300 with an ECG in the smaller arm, and ≥50 primary-outcome events among
   ECG-linked patients.
   - **Pass, already built in v1.5:** PLATO, ARISTOTLE, ROCKET AF, TRANSFORM-HF and COMET. The screen
     reproduces the built v1.5 arm sizes to within about 5%.
   - **Pass, new:**
     - **SOAP II:** dopamine vs norepinephrine, 28-day death; 927 vs 5,245 with an ECG; 1,996 events.
     - **PEPTIC:** PPI vs H2RA in ventilated ICU patients, in-hospital death; 2,149 vs 5,283; 1,364
       events.
     - **ELITE II:** ARB vs ACEi in HF, death; 1,847 vs 5,951, or losartan vs captopril 1,166 vs 997.
     - **RE-LY:** dabigatran vs warfarin; 439 vs 6,116. It is imprecise: dabigatran stroke/SE events
       are 11.
     - **DOREMI proxy:** milrinone vs dobutamine in HF; 603 vs 540; 315 in-hospital deaths.
     - **Statin intensity after ACS** (PROVE-IT proxy): 3,862 vs 1,343.
     - **AFFIRM proxy:** rhythm vs rate agents in AF; 2,656 vs 3,459.
   - **Fail:** TRITON (prasugrel 131), ENGAGE (edoxaban <11), PARADIGM-HF in both new-user and switcher
     forms (sac/val ≤103 with an ECG), SYNERGY, OASIS-5, HORIZONS-AMI, strict PROVE-IT (pravastatin
     207), MENDS2/SPICE III (dexmedetomidine ≤172), PROTECT (enoxaparin 150), SOAP II cardiogenic
     subgroup, strict DOREMI (cardiogenic-shock code; milrinone 223), and AMPLIFY/EINSTEIN (recurrent-VTE
     events 14–35).
4. **Structural limit.** MIMIC-IV-ECG effectively ends in about 2019 (estimated real year), while
   admissions run to 2022. Drugs adopted late therefore have almost no pre-index ECGs. This rules out
   sac/val, SGLT2i, edoxaban and tenecteplase.
5. **Held-out balance panel: MIMIC is richer than expected.** Among ECG-linked patients, coverage before
   t0 is:
   - creatinine, CBC and bicarbonate: 92–100%;
   - NT-proBNP: 12–55%;
   - troponin T: 24–79%;
   - lactate: 37–95%;
   - ICU vitals in the prior 24 h: 18–95%;
   - structured TTE in the prior 365 d: 26–78%.

   This makes MIMIC a strong external test of the v1.6 held-out balance result, which is our most robust
   finding.
6. **Compliance.**
   - Every module except MIMIC-IV-ECG is under the PhysioNet Credentialed Health Data License 1.5.0.
     MIMIC-IV-ECG is open access under ODbL.
   - The PhysioNet responsible-use rule forbids sending credentialed data to online AI services. This
     workflow is agent-driven, so agents must only ever see aggregates, and the set-up should be
     confirmed with Ryan/PI (§6.3).
   - Only one download credential is visible on disk: PhysioNet user `[PI PhysioNet account]`, in an NFS MIMIC-CXR-JPG
     download script.

## 1. Data inventory (paths, versions, contents at schema level)

The raid0 copies below are owned by the named users; I read them in place.

| # | Path | Module / version | Contents (schema level) | Size | Licence |
|---|---|---|---|---|---|
| D1 | `/mnt/raid0/bb2238/physionet/physionet.org/files/mimiciv/3.1/{hosp,icu}` | MIMIC-IV 3.1 (Oct 2024) | **hosp:** admissions, patients (anchor_age/year/group, dod), diagnoses_icd, procedures_icd, prescriptions, pharmacy, poe(+detail), emar(+detail), labevents, microbiologyevents, omr, transfers, services, drgcodes, hcpcsevents, d_* dictionaries. **icu:** icustays, chartevents, inputevents, ingredientevents, outputevents, procedureevents, datetimeevents, d_items, caregiver | hosp ≈ 6.2 GB, icu ≈ 4.3 GB (csv.gz) | PhysioNet Credentialed 1.5.0 |
| D2 | `/mnt/raid0/rbc58/physionet.org/files/mimiciv/3.1/{hosp,icu}` (owner rbc58, 2026-07-17) | MIMIC-IV 3.1 | Identical to D1: same SHA256SUMS manifest and identical file sizes | same | same |
| D3 | `/mnt/raid0/bb2238/physionet/physionet.org/files/mimic-iv-ecg/1.0` | MIMIC-IV-ECG 1.0 | `record_list.csv` (subject_id, study_id, file_name, ecg_time, path), `machine_measurements.csv` (machine intervals/axes plus report lines), `waveform_note_links.csv`, WFDB `files/p10xx…` (1,000 dirs). 800,035 records / 161,352 subjects | ≈ 90 GB (PhysioNet listing; not du'd) | **ODbL 1.0 (open access)** |
| D4 | `/mnt/raid0/pp675/phd/data/raw_ecg/mimic4ecg12l` | MIMIC-IV-ECG 1.0 | Second copy; `record_list.csv` byte-identical to D3 | ≈ 90 GB | ODbL |
| D5 | `/mnt/raid0/bb2238/physionet/physionet.org/files/mimic-iv-fhir/2.1`, `…/mimic-iv-demo/2.2` | MIMIC-IV FHIR 2.1; demo 2.2 | FHIR ndjson (Patient, Encounter, Condition, Medication*, Observation*, Procedure…); 100-patient demo | 30 GB; 16 MB | Credentialed / open (demo) |
| D6 | `/mnt/nfs_yale_ecg/mimic/physionet.org/files/mimiciv/2.2` | MIMIC-IV 2.2 | Same tables as D1, older release | hosp ≈ 4.5 GB, icu ≈ 3.2 GB | Credentialed |
| D7 | `/mnt/nfs_yale_ecg/mimic/physionet.org/files/mimic-iv-note/2.2/note` | MIMIC-IV-Note 2.2 | `discharge.csv` (3.5 GB; about 332k discharge summaries), `discharge_detail.csv`, `radiology.csv` (2.9 GB), `radiology_detail.csv` | 6.7 GB | Credentialed; **free text, never read by agents** |
| D8 | `/mnt/nfs_yale_ecg/mimic/physionet.org/files/mimic-iv-ed/2.2/ed` | MIMIC-IV-ED 2.2 | edstays, triage (vitals, acuity), vitalsign, diagnosis, medrecon (home medications), pyxis | ≈ 120 MB | Credentialed |
| D9 | `/mnt/nfs_yale_ecg/mimic/physionet.org/files/{mimic-iv-ecg/1.0, mimic-cxr/2.1.0, mimic-cxr-jpg/2.1.0}` | ECG (third copy), CXR, CXR-JPG | CXR reports zip plus images; `download_chunks.sh` (wget, `--user [PI PhysioNet account] --ask-password`) | large | ODbL / Credentialed |
| D10 | `/mnt/raid0/ak3398/physionet.org/files/mimic-iv-echo/` (0.1, plus newer top-level `echo-study-list.csv` and `echo-record-list.csv`) | MIMIC-IV-ECHO 0.1 | 7,243 studies. The newer study list adds `measurement_id` and `measurement_datetime` (link to structured measurements) and `note_id`. DICOMs are not here | 45 MB | Credentialed |
| D11 | S3 `spinup-002216-ynhh-echo-backup` (s3fs `~/mnt/backup_echo`): `mimic-iv-echo/p10…p19`, `mimic-iv-echo_2/…/0.1`, `mimic_echo_intermediate_avi`, `mimic_echo_doppler_intermediate_avi`, `021124_mimic-echo_view_preds.csv` | MIMIC-IV-ECHO 0.1 DICOMs and derived AVIs | Echo videos (about 4.6k subjects) | large (not sized) | Credentialed |
| D12 | `/mnt/nfs_yale_echo/{011425_mimic-echo_preprocessed, 012526_…panecho_preprocessed, 012626_…echoprime_preprocessed, 021224_…, mimic-echo_97209294, panecho_mimic_preds.csv}` | Derived from D10/D11 | PanEcho/EchoPrime preprocessing and study-level AI predictions (Khera lab) | large | Derived, credentialed |
| D13 | `/mnt/raid0/gih5/A100_mnt_data_gih5/mv-mt-echo/echobench/structured-measurement.csv` (+ `structured-measurement-subset.csv`, `echo_study_structured_labels.csv`, `mimic_structured_labels.csv`, `linked_echo_studies_cleaned.csv`, `echo_study_reports_labels_qwen*.csv`) | "MIMIC-IV-Echo structured measurements". The source release and version are **not recorded on disk** | Long format: subject_id, measurement_id, measurement_datetime, test_type (tte 179,928 / stress 16,389 / tee 10,171 studies), measurement (302 fields, e.g. lvef, lvedd, lvesd, septal_thickness, diastolic_grade, rv_function, tr_mmhg, aortic_stenosis, mitral/tricuspid regurgitation, ra_size, pericardial_effusion), result, unit. 28.1M rows; **91,372 subjects**. The Qwen label files are local-LLM extractions from echo report text; `report_text` is a column in them, so do not open | 2.6 GB | Credentialed (confirm the release) |
| D14 | `/mnt/raid0/eo287/clmbr/processed_data/mimic_*` | CLMBR-T-base applied to MIMIC-IV (E. Oikonomou) | MEDS-style mapped events: `mimic_labs_clmbr_mapped.csv` (subject_id, hadm_id, event_code, event_time, valuenum), `mimic_meds_clmbr.csv`, `mimic_procedures_clmbrt.csv`, `mimic_iv_diagnoses_with_snomed(_clmbr).parquet`, `mimic_admissions/demos/anchor.csv` (with an anchor-delta "original year" reconstruction); `mimic_clmbrt_last_embeddings.parquet` (5,231 subjects × embedding at an ECG time); `mimic_ecg_clmbrt_embeddings_with_labels.parquet` (5,231 rows; echo labels plus embedding) | ≈ 400 MB | Derived, credentialed |
| D15 | `/mnt/raid0/rbc58/mimic_ehr/` (Ryan, 2026-08-19; MOSAIC VHD project) | Derived | `cohort_{AS,AR,MR,LVSD}.parquet` (echo-labelled case-control cohorts: 265 / 782 / 1,889 / 3,351), `notes.parquet` (discharge-note text for these cohorts; **restricted, never open**), Qwen3-Embedding-8B note embeddings `mimic_emb_*_masked_w360b{0,30}.parquet` (4,096-d, computed locally), `mimic_preds_*` (note/ECG/fusion scores), `fusion_*.joblib`, logs | 390 MB | Derived, credentialed |
| D16 | `/mnt/raid0/rbc58/mosaic/mimic_linkage/` | Derived | `mimic_linkage.parquet` (per subject: n_adm, n_ecg, n_echo, first/last dates), `mimic_coverage.{md,json}`: 223,452 with EHR admissions; 161,352 with ≥1 ECG; 4,555 with ≥1 DICOM echo; 3,842 with all three | 11 MB | Derived, credentialed |
| D17 | `/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-*`, `claude-v15d-mimic-*-death`, `shared/claude-v15-mimic-ecg-npy` | Ours (v1.5) | See §2 | npy 4.1 GB | Derived, credentialed |

Not found:
- MIMIC-III or eICU on any mount searched;
- ECG reports (these are in `machine_measurements.csv`; `waveform_note_links` points to notes that were not
  released);
- a GEMs ICD-9↔10 mapping table.

The code that generated D15/D16 (`scripts/build_mimic_linkage.py`, `mosaic5.agent.build_embeddings`) is
named in their logs but is **not on disk** under `/home/rbc58/github` or `/mnt/raid0/rbc58`. `mosaic/mosaic5`
contains no MIMIC code. No other `/home/rbc58/github` repo has MIMIC code, except one `rhd_echo` commit that
adds an S3 prefix for MIMIC-IV-ECHO controls (`237b05b`, `scripts/preprocess_yale.py`).

## 2. What was run before

### 2.1 ecg-tte v1.5 (2026-09-26; tag `protocol-v1.5`)

Commits: `fef7a48` (protocol), `309185b` (deviation log), `d7fc084` (first pass) and `20a9fbe` (post-audit
corrections).

| Script (`scripts/v15/`) | What it does |
|---|---|
| `v15_mimic_stage.py` | Stages 12 MIMIC-IV 3.1 tables into `audits/claude-v15-mimic-shared/stage/*.parquet` (D1 source): patients, admissions, diagnoses/procedures, prescriptions, emar, labevents, omr, transfers, a subset of ICU vitals, and ECG `record_list` |
| `v15_mimic_common.py` | Concept map with ICD-10 and hand-mapped ICD-9 prefixes, lab item IDs, oral routes, gates, endpoints, hashed pid (`sha256("v15-mimic:<subject_id>")`) |
| `v15_mimic_cohort.py` | In-hospital new-user active-comparator cohort per trial. Time zero = first enteral order before discharge. Washout covers earlier admissions and the index admission before t0. Also applies the calendar gate, disease gate and trial exclusions, and builds the baseline (labs, vitals, dx, meds), hdPS panel, `rct.json` and `summary.json` |
| `v15_mimic_ecg_convert.py` | WFDB → Yale npy: (5000, 12) float32 mV at 500 Hz; leads reordered by header name (MIMIC stores aVF before aVL); NaN interpolation or failure rules |
| `v15_mimic_ecg_pipeline.py` | Per trial: prepare (latest ECG in [t0−365 d, t0], with fallback) → embed (`bcl_embed_uv.py`, BCL checkpoint `…/12Lead_BCL_training/…_08_26_2026/trained_12lead_30.pt`, ×1000 µV fix, GPUs 2/3) → link (`ecg_embedding.parquet`, `READY_ECG`) |
| `v15_mimic_ecg_validate.py` | Conversion validation (`audits/claude-v15-mimic-ecg-driver/validation.json`) |
| `v15_mimic_outcomes.py`, `v15_mimic_auditfix.py`, `v15_mimic_death_dirs.py`, `v15_mimic_nco_v2{,b}.py` | Outcomes, post-audit baseline fix (prior admissions only; 28-day primary-position rule for MI/stroke), death co-primary dirs, 8 extra NCOs |
| `v15_analyze.py`, `v15_summarize.py` | Engine (M0–M4, ECG only, clinical; 1:1 caliper 0.2; Cox with pair-clustered SE; RCT-DUPLICATE panel; plasmode; capture) and summaries |

**State.** All 5 trial directories are complete, with markers `READY_*`, `AUDITFIX_DONE` and
`NCO_V2(B)_DONE`, plus `analysis/` and `analysis_v1_preaudit/`. So are the 5 `claude-v15d-*-death`
directories.

ECG linkage, from `claude-v15-mimic-bcl-<trial>/ecg_summary.json`:
- About 99.5% of candidate records converted.
- The median ECG lag was 1–2 days.
- 16–46% of linked ECGs were recorded on the index day.
- Embedding statistics were non-degenerate: mean pairwise cosine about 0.11–0.13.

Analysed arms (ECG-linked) and results, from `docs/V15_EXTERNAL_SUMMARY.md`:

| Trial | Arms (n with ECG) | Primary events (arm 1 / arm 2) | RCT | Sparse | Sparse + ECG | hdPS200 + ECG |
|---|---|---|---|---|---|---|
| PLATO | ticagrelor 441 / clopidogrel 2,433 | 63 / 571 | 0.84 | 0.77 | 0.71 | 0.89 |
| ARISTOTLE | apixaban 1,556 / warfarin 3,576 | 16 / 69 (imprecise) | 0.79 | 0.49 | 0.55 | 0.58 |
| ROCKET AF | rivaroxaban 905 / warfarin 5,591 | 11 / 99 (imprecise) | 0.88 | 0.44 | 0.89 | 0.90 |
| TRANSFORM-HF | torsemide 940 / furosemide 3,466 | 251 / 764 | 1.02 | 1.10 | 1.23 | 1.13 |
| COMET | metoprolol 4,101 / carvedilol 743 | 981 / 130 | 1.21 (inverted orientation) | 1.35 | 1.24 | 1.04 |

- **Pooled results.** External-only (MIMIC + UKB, 8 trials): sparse + ECG vs sparse, C1, was closer in
  5/8 (p = 0.39). Plasmode bias reduction for C1 was +0.013 (MC CI 0.005–0.025).
- **Held-out balance ("capture").** In v1.5 this was computed only on the 8 labs/vitals that were also in
  the clinical PS, so it was **not held out**. Sparse → sparse + ECG median capture was 20 → 31%.
- **Implication for v2.0.** The MIMIC half of the v1.6 headline, held-out balance on a panel never used in
  any PS, has never been tested.

### 2.2 Other MIMIC analyses on our mounts (not trial emulations)

- **D15 / D16: Ryan's MOSAIC-VHD MIMIC external validation (August 2026).**
  - Echo-labelled case-control cohorts for AS, AR, MR and LVSD.
  - Frozen Yale EHR probes applied to locally computed Qwen3 note embeddings, fused with an ECG score.
  - Example: LVSD with no blackout had ECG AUROC 0.84, EHR 0.85 and fusion 0.88.
  - Not reusable for TTE: the cohorts are case-control and the ECG model is not BCL. The linkage table is
    reusable.
- **D14: CLMBR-T on MIMIC (eo287, Oct 2025).** Mapped event tables plus embeddings at ECG times for the
  5,231 ECG/echo-linked subjects.
  - The mapped tables are the cheapest route to a **MIMIC CLMBR arm at trial t0**: re-run CLMBR-T with
    each trial's time zero as the censor date.
  - They are another user's derived files. Read them in place, or copy only into `/mnt/raid0/rbc58`, and
    only if Ryan holds MIMIC-IV access (§6.3).
- **D12 / D13: Khera-lab MIMIC-ECHO benchmarking (gih5).** PanEcho/EchoPrime predictions, plus a
  structured-measurement → label conversion. D13 is the candidate **held-out echo panel**.

## 3. Feasibility screen

### 3.1 Method

The screen is `feasibility_screen.py` in the audit directory. It follows the v1.5 design, simplified:
- **Time zero.** t0 = first qualifying order of either arm, starting before discharge. The source is
  hosp `prescriptions` (route-filtered) or ICU `inputevents` (vasopressors, inotropes, sedatives).
- **Ties.** Patients with both arms at t0 are excluded.
- **Washout.** No order of either arm (any route) in an earlier admission, or earlier in the index
  admission. Class-wide washout is used where appropriate (ACEi/ARB/ARNI; statins).
- **Other criteria:** age ≥ 18; alive at t0; estimated real year ≥ drug availability.
- **Disease gate:** ICD-10/9 codes in the index admission, the index admission plus the 30 d before, or
  any earlier admission.
- **Trial-specific extras:** PCI in the index admission; t0 within the first 48 h of an ICU stay;
  invasive ventilation spanning t0; no other vasopressor at or before t0.
- **ECG** = any MIMIC-IV-ECG record in [t0 − 365 d, t0], index day included (Ryan's Yale rule).
- **Outcomes** among ECG-linked patients:
  - death from `patients.dod`, which is complete to 1 year after the last discharge;
  - in-hospital death (`hospital_expire_flag`);
  - readmission with a primary-position ICD code (any position for stroke/SE, as in v1.5).

**Validation against the built v1.5 cohorts** (ECG-linked, screen vs built):

| Trial | Screen | Built |
|---|---|---|
| PLATO | 450 / 2,579 | 441 / 2,433 |
| ARISTOTLE | 1,631 / 3,672 | 1,556 / 3,576 |
| ROCKET AF | 955 / 5,751 | 905 / 5,591 |
| TRANSFORM-HF | 1,015 / 3,535 | 940 / 3,466 |
| COMET | 4,107 / 747 | 4,101 / 743 |

The screen lacks the OAC, ICH, DOAC-365 and eGFR exclusions, so it runs about 0–8% high. Expect built
cohorts to be about 5% smaller than the screened ones.

**Near-duplicate check.** For each pair of cohorts I computed the share of the smaller ECG-linked cohort
that also appears in the other.
- Pairs with the same contrast share ≥ 0.9: the ENGAGE, DOAC-pooled and ARISTOTLE/ROCKET/RE-LY variants.
- Pairs with a shared warfarin arm share 0.72–0.89: ARISTOTLE, ROCKET and RE-LY.
- Pairs with different contrasts in the same disease share 0.3–0.7: e.g. PLATO vs statin intensity 0.69;
  COMET vs ELITE II 0.49; SOAP II vs PEPTIC < 0.3.

### 3.2 Feasibility table

- **Benchmarks** marked (reg.) are the verified entries in `scripts/trial_specs.PUBLISHED`. The others are
  from memory and must be verified before registration.
- **Counts** are from the screen, among patients with an ECG in [t0−365 d, t0].
- **Events** are for the listed outcome, given as total (arm 1 / arm 2).
- **Feasible:** Y = both rules pass and there is an ascertainable primary (or accepted substitute)
  endpoint; P = passes with a substitution or design caveat; N = fails.

| # | Trial (benchmark) | Design in MIMIC | Comparator | Outcome (horizon) | Data needed | n with ECG, arm 1 / arm 2 (all) | Events, ECG-linked | Feasible | Reason |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **PLATO** (0.84, reg.) | ACS (index/30 d), first oral P2Y12 | clopidogrel | death or MI/stroke readmission (12 m) | hosp | 450 / 2,579 (943 / 3,977) | 625 (61 / 564) | **Y (built)** | v1.5 dir complete |
| 2 | **ARISTOTLE** (0.79, reg.) | AF, first OAC | warfarin | stroke/SE readmission (12 m; death co-primary) | hosp | 1,631 / 3,672 | 101 (19 / 82); death 1,002 | **Y (built)** | apixaban-arm events < 30 for stroke/SE (use death co-primary); shares warfarin with 2/3/9 |
| 3 | **ROCKET AF** (0.88, reg.) | as 2 | warfarin | as 2 | hosp | 955 / 5,751 | 134 (11 / 123); death 1,173 | **Y (built)** | imprecise; 72% shared with ARISTOTLE |
| 4 | **TRANSFORM-HF** (1.02, reg.) | HF admission (index/30 d), first oral loop; prior IV loop allowed | furosemide | death (12 m) | hosp | 1,015 / 3,535 | 1,045 (270 / 775) | **Y (built)** | — |
| 5 | **COMET** (0.83, reg.) | HF, first oral BB | carvedilol | death (12 m) | hosp | 4,107 / 747 | 1,115 (983 / 132) | **Y (built)** | metoprolol arm mostly tartrate (in-hospital) |
| 6 | **SOAP II** (28-d death OR 1.17, 0.97–1.42) | ICU, first vasopressor infusion; no epi/phenylephrine/vasopressin at or before t0 | norepinephrine | death (28 d) | icu inputevents | **927 / 5,245** (1,133 / 8,631) | **1,996** (283 / 1,713) | **Y** | short horizon avoids dod truncation; confounding by indication is strongly cardiac (HR, rhythm, post-cardiotomy), which is attractive for ECG. Cardiogenic-shock subgroup fails (dopamine 238) |
| 7 | **PEPTIC** (in-hospital death RR 1.05, 1.00–1.10) | ICU (t0 ≤ 48 h), ventilated, first PPI vs H2RA (IV/enteral) | H2RA | in-hospital death | hosp + icu | **2,149 / 5,283** (3,727 / 8,722) | **1,364** (507 / 857) | **Y** | non-cardiac question in which ECG should not matter. Useful as a **negative-control trial** for the ECG gain (§5). The RCT was cluster-crossover |
| 8 | **ELITE II** (1.13, 0.95–1.35, reg.) | HF, first ARB vs ACEi (class; ARNI excluded; class-wide washout) | ACEi | death (12 m; RCT median ~1.5 y) | hosp | **1,847 / 5,951** (3,426 / 9,241) | **1,437** (297 / 1,140) | **Y (class proxy)** | Strict losartan vs captopril: 1,166 / 997, 417 deaths, which also passes. In hospital, captopril is often a short-acting titration agent (strategy mismatch); prefer class as primary and strict as sensitivity |
| 9 | **RE-LY** (0.66, 0.53–0.82, reg.) | AF, first OAC | warfarin | stroke/SE (12 m; death co-primary) | hosp | **439** / 6,116 (581 / 8,235) | 138 (11 / 127); death 1,166 (44 / 1,122) | **P** | passes the counts, but dabigatran stroke/SE events are 11 (imprecise) and the warfarin arm overlaps with ARISTOTLE/ROCKET (89% of the RE-LY cohort is also in ROCKET). Use as secondary |
| 10 | **DOREMI** proxy (in-hospital death RR 0.85, 0.60–1.21; primary composite RR 0.90, 0.69–1.19) | ICU, first inotrope infusion, HF code in the index admission | dobutamine | in-hospital death (DOREMI secondary) | icu inputevents | **603 / 540** (749 / 797) | **315** (94 / 221) | **P** | population proxy (HF + inotrope, not coded cardiogenic shock). The strict cardiogenic-shock gate fails (milrinone 223). The primary composite is only partly ascertainable: death, RRT and MCS are timed; arrest and MI are not |
| 11 | **PROVE-IT** proxy: statin intensity after ACS (0.84, 0.74–0.95 for atorva 80 vs prava 40) | ACS (index/30 d), first statin; high (atorva 40–80, rosuva 20–40) vs moderate/low | moderate/low statin | death or MI/stroke readmission (12 m; RCT 2 y) | hosp (strength from `prod_strength`) | **3,862 / 1,343** (7,348 / 2,450) | **1,016** (743 / 273) | **P** | Strict atorva 80 vs pravastatin fails (pravastatin 207). The class proxy needs Ryan's accepted-proxy decision. Different contrast from PLATO but 69% population overlap |
| 12 | **AFFIRM** proxy (death HR 1.15, 0.99–1.34) | AF coded in the index admission; first oral AAD vs first diltiazem/verapamil/digoxin | rate agents | death (12 m; RCT ~3.5 y) | hosp | **2,656 / 3,459** (4,372 / 5,866) | **1,239** (377 / 862) | **P (design-heavy)** | strategy trial, emulated by the first agent only. Amiodarone use is dominated by post-cardiotomy AF, and rhythm patients also get rate agents. Exploratory only |
| 13 | TRITON-TIMI 38 (0.81, reg.) | ACS + PCI in the index admission | clopidogrel | death/MI/stroke (12 m) | hosp | 131 / 2,162 | 301 (<11 / 296) | **N** | prasugrel < 300 |
| 14 | ENGAGE AF (0.79 / ITT 0.87) | AF | warfarin | stroke/SE | hosp | <11 / 3,273 | — | **N** | edoxaban essentially absent |
| 15 | DOAC (any) vs warfarin, AF | AF | warfarin | stroke/SE | hosp | 2,820 / 5,575 | 152 | N (duplicate) | ≥ 98% overlap with 2/3/9; no single RCT |
| 16 | PARADIGM-HF (0.80, reg.) | HF; sac/val vs ACEi, new users | ACEi | death/HF readmission | hosp | **27** / 2,407 | — | **N** | sac/val new users 218 (27 with an ECG). **Switcher design:** 581 sac/val initiators with HF and prior ACEi/ARB, but only 103 have an ECG in 365 d, because the ECG data end around 2019 |
| 17 | ELITE II strict | see 8 | captopril | death | hosp | 1,166 / 997 | 417 | Y (sensitivity for 8) | — |
| 18 | PROVE-IT strict | ACS, atorva 80 vs pravastatin | pravastatin | death/MI/stroke | hosp | 3,270 / **207** | 674 | **N** | pravastatin < 300 |
| 19 | AMPLIFY (0.84, 0.60–1.18) | VTE in the index admission, first oral anticoagulant | warfarin (proxy for LMWH→VKA) | recurrent VTE readmission (6 m) | hosp | 324 / 773 | **14** | **N** | < 50 events (death 155 is not the primary) |
| 20 | EINSTEIN-DVT/PE (0.68 / 1.12) | as 19 | warfarin | recurrent VTE (12 m) | hosp | 267 / 1,397 | 35 | **N** | arm < 300 and < 50 events; the pooled DOAC version (575 / 1,374) still has only 31 events |
| 21 | SYNERGY (30-d death/MI 0.96, 0.86–1.06) | NSTE-ACS; therapeutic enoxaparin (≥ 60 mg) vs IV UFH | IV UFH | 30-d death (+ MI readmission) | hosp | **86** / 4,015 | 353 | **N** | enoxaparin-arm size; in-hospital MI after t0 is not timed |
| 22 | OASIS-5 | NSTE-ACS; fondaparinux vs enoxaparin | enoxaparin | 30-d death | hosp | 23 / 416 | 43 | **N** | size and events |
| 23 | HORIZONS-AMI | ACS + PCI; bivalirudin vs UFH | UFH | 30-d death | hosp | 15 / 1,348 | 72 | **N** | cath-lab drugs are largely not in the pharmacy data |
| 24 | MENDS2 (90-d death HR 1.06, 0.74–1.52) | sepsis, ventilated, first sedative infusion | propofol | 90-d death | icu | **135** / 2,236 | 1,047 | **N** | dexmedetomidine is rarely first-line |
| 25 | SPICE III (90-d death OR ~1.0) | ventilated, dexmedetomidine vs propofol/midazolam | usual sedation | 90-d death | icu | **172** / 16,760 | 3,512 | **N** | as 24 |
| 26 | PROTECT (dalteparin vs UFH; proxy enoxaparin) | ICU (≤ 48 h), SC prophylaxis | UFH SC | in-hospital death (PROTECT primary = proximal DVT, not ascertainable) | hosp + icu | **150** / 10,226 | 893 | **N** | enoxaparin rare in the ICU; primary not ascertainable |
| 27 | SOAP II cardiogenic subgroup | card. shock code | NE | 28-d death | icu | 238 / 468 | 333 | **N** | dopamine < 300 |
| 28 | DOREMI strict | cardiogenic-shock code | dobutamine | in-hospital death | icu | 223 / 391 | 243 | **N** | milrinone < 300 |
| 29 | AcT / tenecteplase vs alteplase | ischemic stroke | alteplase | mRS (not ascertainable) | hosp | 0 tenecteplase orders | — | **N** | drug absent; primary not ascertainable |
| 30 | POINT/CHANCE (DAPT vs aspirin after minor stroke/TIA; 0.75, 0.59–0.95) | stroke/TIA; clopidogrel within 24 h of first aspirin | aspirin alone | ischemic stroke readmission / death (90 d) | hosp | not computed | — | **unknown** | arms need a 24-h grace-period definition and aspirin is often a home medication (ED `medrecon`). Estimated cost: about 1 h to add to the screen |

**Rules applied as in Yale:**
- active comparator or accepted proxy;
- ascertainable primary endpoint, with death as the co-primary external outcome (as registered in v1.5);
- treatment identifiable from orders;
- ≥ 300 with an ECG in the smaller arm;
- ≥ 50 events;
- no near-duplicate cohort.

The ≥ 300 rule is stricter than v1.5's ≥ 200 per arm; every v1.5 MIMIC trial passes both.

## 4. Held-out balance panel available in MIMIC

These percentages are from `panel_coverage.json`. Each is the share of ECG-linked patients with a
measurement before t0: in [t0−365 d, t0) for labs, OMR and TTE, and in [t0−24 h, t0) for ICU vitals.

| Trial | n with ECG | Creat | NT-proBNP | TnT | Lactate | Albumin | INR | LDL | HbA1c | TTE ≤ 365 d | TTE ≤ t0 + 3 d | OMR BP/BMI | ICU vitals 24 h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PLATO | 3,029 | 97 | 20 | 79 | 38 | 41 | 88 | 32 | 38 | 37 | 80 | 53 | 32 |
| ARISTOTLE | 5,303 | 98 | 32 | 30 | 65 | 65 | 94 | 24 | 43 | 48 | 59 | 72 | 28 |
| ROCKET AF | 6,706 | 98 | 27 | 30 | 63 | 62 | 96 | 22 | 42 | 47 | 57 | 60 | 30 |
| TRANSFORM-HF | 4,550 | 99 | 55 | 40 | 62 | 65 | 91 | 23 | 36 | 58 | 69 | 72 | 18 |
| COMET | 4,854 | 97 | 48 | 42 | 56 | 57 | 87 | 20 | 31 | 39 | 68 | 58 | 28 |
| RE-LY | 6,555 | 98 | 26 | 30 | 64 | 63 | 97 | 24 | 43 | 47 | 56 | 57 | 31 |
| ELITE II (class) | 7,798 | 97 | 42 | 44 | 51 | 54 | 87 | 29 | 33 | 45 | 67 | 46 | 22 |
| Statin intensity | 5,205 | 93 | 17 | 69 | 37 | 42 | 84 | 28 | 33 | 27 | 73 | 31 | 32 |
| AFFIRM proxy | 6,115 | 96 | 24 | 24 | 45 | 48 | 90 | 22 | 28 | 27 | 47 | 47 | 20 |
| SOAP II | 6,172 | 99 | 32 | 48 | 93 | 77 | 94 | 19 | 27 | 43 | 70 | 52 | 84 |
| DOREMI (HF) | 1,143 | 100 | 51 | 66 | 95 | 88 | 99 | 28 | 57 | 78 | 90 | 56 | 89 |
| PEPTIC | 7,432 | 99 | 12 | 30 | 91 | 70 | 97 | 14 | 39 | 26 | 49 | 34 | 95 |

The proposed held-out panel is never used in any PS. It follows the v1.6/covars2b logic.

**A. Labs:**
- NT-proBNP, troponin T;
- lactate, albumin, bilirubin, ALT;
- INR, platelets, WBC, bicarbonate;
- LDL, HbA1c.

Creatinine, K, Na and Hb stay in the clinical PS, as in v1.5.

**B. Vitals:**
- ICU HR, SBP/DBP and MAP (last value in the 24 h before t0);
- also SpO2, RR and temperature, which need an extra `chartevents` item stage;
- OMR BMI/weight;
- ED triage vitals (D8, MIMIC-IV 2.2 ID space; subject_id is stable across releases).

**C. Echo (D13):**
- LVEF, LVEDD/LVESD, septal/posterior wall thickness, diastolic grade and E/e′;
- RV function, TR gradient/PASP, LA/RA size;
- AS/MR/TR grade, pericardial effusion.

The latest TTE in [t0−365 d, t0) gives 26–78% coverage. This is the same physiology class as the Yale LV
panel, so it gives a direct external replication of "ECG captures LV structure and function, not valves".

**D. ICU severity** (ICU trials only):
- ventilation at t0;
- lactate, vasopressor count/dose at t0 (SOAP II excluded by design);
- a SOFA-like score from labs and vitals.

**E. Coded-record features that are not diagnoses:**
- prior-admission count and LOS;
- ED visit count (D8);
- `drgcodes`.

These are the analogue of the Yale utilisation block and can stay as a non-ECG-proximal block.

**Not used as held-out variables:**
- ECG `machine_measurements` (QRS/QTc/HR/axis), because they are derived from the same ECG. They are
  better as an "interpretable ECG" comparator arm (S3 representation sweep).
- Note-derived variables, unless extracted **locally** (never by an online model; §6.3).

## 5. Recommended analysis plan (MIMIC arm of v2.0; register before any outcome is touched)

**Trials.**
- **Core set (8 trials):**
  - the 5 built v1.5 trials: PLATO, ARISTOTLE, ROCKET AF, TRANSFORM-HF and COMET;
  - SOAP II, ELITE II (class) and DOREMI-HF proxy.
- **Secondary:**
  - RE-LY (imprecise, shared warfarin arm);
  - statin intensity (PROVE-IT proxy, pending Ryan's accepted-proxy decision);
  - AFFIRM proxy (exploratory).
- **PEPTIC as a pre-specified negative-control trial.** Non-cardiac question; ECG physiology is not
  expected to be a strong confounder. The v1.6 claim predicts that ECG adds held-out balance mainly for
  cardiac physiology; it should add little here beyond shrinkage.
- Follow v1.7 blinded-selection practice: freeze the list, definitions and benchmarks (verified from
  primary papers into `trial_specs.PUBLISHED`) in a dated amendment **before** building outcomes for the
  new trials.

**Build.**
1. **Generalise the v1.5 cohort builder** (new script, e.g. `scripts/v20/v20_mimic_cohort.py`):
   - an ICU `inputevents` exposure source (vasopressor/inotrope start);
   - an ICU window and ventilation gates;
   - class washout sets;
   - strength-based arms;
   - the prior-admission-only baseline (v1.5 audit fix), with the gate allowed from the index admission.
   - Reuse `v15_mimic_common` concepts and add the new ones: VTE, card_shock, sepsis, nste_acs.
2. **Point staging at D2** (Ryan's own MIMIC-IV 3.1 copy, byte-identical to D1) for a clean chain of
   custody. Stage `chartevents` for the extra vitals and `drgcodes`. Stage D13 as a restricted parquet
   (latest TTE per patient before t0).
3. **ECG:** reuse `v15_mimic_ecg_pipeline.py` unchanged (prepare → convert → BCL embed → link).
   - Use the same checkpoint and the same Yale PCA to 32 PCs.
   - The new trials need up to about 39.5k (subject, t0) ECG selections (27.8k subjects), some of them
     already converted in `shared/claude-v15-mimic-ecg-npy`.
   - Conversion takes about 30 min on 48 CPUs and adds about 10 GB of npy. BCL embedding takes about
     1 h on 1 GPU; check `nvidia-smi` first.
4. **Optional CLMBR arm:** CLMBR-T at t0 from D14's mapped MEDS tables, mirroring Yale P1 (CLMBR vs
   CLMBR + ECG).

**Analyses.** Reuse the Yale v1.6+ engine where possible:
- **Primary (replicates the v1.6 headline).** Demo PS (age, sex, estimated year) vs demo + ECG PCs,
  caliper 0.2. Report the percentage of held-out panel variables with |SMD| < 0.1, plus mean |SMD|, the
  C-statistic of the held-out panel, and Mahalanobis distance. Test with an exact sign-flip across the
  MIMIC trials; pool with Yale by RCT.
- **Placebo guardrails:** shuffled-ECG and noise-32 arms, and split-half confirmation, as in v1.6.
- **PS-richness ladder (S1):**
  - demo → minimal-7 (age, sex, race, T2D, CAD, HTN, HLD);
  - → sparse dx;
  - → hdPS k (365-d prior-admission panel);
  - → clinical (PS labs and vitals).
  - MIMIC's thin coded record (hospital episodes only) is the natural test of "ECG gains grow as coded
    data thin".
- **Echo-specific result:** capture of LVEF, LV size and diastolic function vs valves on D13, compared
  with the Yale LV panel.
- **RCT agreement.** Death co-primary and trial primary, with the RCT-DUPLICATE panel and z². These are
  reported as secondary, whatever the result, as fixed in the v1.5 amendment.
- **Plasmode:** 80% subsampling with MIMIC phys = the held-out panel.
- **NCOs:** the v1.5 set of 11.

## 6. Effort, risks and compliance

### 6.1 Effort (agent time; compute is small)

| Step | Estimate |
|---|---|
| Amendment (trial list, verified benchmarks, definitions) | 0.5 d |
| Generalised cohort builder (ICU source, gates) + baseline/panel/held-out panel incl. echo | 1–1.5 d |
| ECG prepare/convert/embed/link for 6–10 new trials | 2–3 h wall-clock |
| Re-run v1.6-style balance/ladder/placebo on 5 built + new trials; summaries; audit | 1 d |
| Optional CLMBR-T at t0 (D14 tables) | 0.5–1 d |

### 6.2 Risks

1. **ECG coverage ends around 2019.**
   - Late drugs are infeasible.
   - In every trial, the ECG-linked subset is skewed to earlier years.
   - Remedy: report calendar balance, and keep `index_year` in every PS.
2. **ECG timing.** 16–46% of linked ECGs are recorded on the index day, and in ICU trials they may follow
   shock onset. The ECG can then partly reflect the indication, or a treatment given before t0 (e.g. an
   earlier vasopressor).
   - Sensitivity: ECG ≥ 1 d before t0.
   - Sensitivity: exclude ECGs after ICU admission.
3. **Dates are shifted and years are coarse.** The anchor-year group gives ±1–2 y of uncertainty in the
   calendar year. This affects drug-availability gates and calendar confounding.
4. **Hospital-only record.** There are no outpatient prescriptions; ED `medrecon` gives only partial home
   medications. Prior use cannot be ruled out, so these are "hospital new users".
   - Death is complete to 1 y after the last discharge. Readmissions count only within BIDMC.
   - Keep horizons ≤ 12 months, and prefer the short-horizon ICU trials (SOAP II, PEPTIC, DOREMI).
5. **Index-admission diagnoses are dated at admission.** The v1.5 audit found post-t0 leakage from them,
   so keep the prior-admission-only baseline.
6. **In-hospital treatment choice.** Protocol-driven prescribing (e.g. captopril titration, metoprolol
   tartrate in hospital) differs from the RCT strategies. Emulation-quality ratings are needed.
7. **Shared arms and populations.**
   - The warfarin arm is shared across ARISTOTLE, ROCKET AF and RE-LY.
   - PLATO and statin intensity overlap (ACS).
   - Cluster by comparator when pooling (v1.7 practice).
8. **D13 provenance is unverified**, so its release and DUA need confirming before use (§6.3). If it
   cannot be used, fall back to D10–D12, which cover only about 4.6k subjects, too few for a panel.
9. **Credibility.** MIMIC TTEs are viewed sceptically (paper-mill signatures;
   `docs/LITERATURE_TTE_UKB_MIMIC.md`). Pre-registration, blinded selection and reporting every result
   are essential.

### 6.3 Compliance (conservative; confirm with Ryan/PI before any new build)

1. **Licences.**
   - **Credentialed:** MIMIC-IV (2.2, 3.1), MIMIC-IV-Note, MIMIC-IV-ED, MIMIC-IV-ECHO, MIMIC-CXR and FHIR
     are all under the PhysioNet Credentialed Health Data License 1.5.0 (`LICENSE.txt` in each copy).
   - **Open:** MIMIC-IV-ECG 1.0 is open access under ODbL 1.0. However, linking it to MIMIC-IV (as we do)
     makes the linked data credentialed.
   - **ODbL share-alike:** any *public* derived database of the waveforms alone (e.g. released
     embeddings) must be under ODbL.
2. **Licence terms that matter here.**
   - No attempt to re-identify, and reasonable care to avoid disclosure (items 1–2).
   - **Do not share access with anyone else** (item 3). Every analyst, and Ryan, must hold their own
     credentialed PhysioNet account, with current CITI training (item 7) and a signed DUA **for each
     project used**. MIMIC-IV, -Note, -ED and -ECHO are separate projects.
   - Using another user's download (bb2238, ak3398, gih5, eo287) does **not** transfer access. It is
     acceptable only if the reader holds their own access to that project.
   - Research use only (item 6).
   - Contribute code associated with publications to an open repository (item 8). The `scripts/v15`
     and v2.0 MIMIC code should be releasable; no restricted data may be in the repository.
3. **Online AI services.**
   - PhysioNet's responsible-use guidance for credentialed data prohibits sending the data to third-party
     online services such as ChatGPT or similar APIs, unless the service has contractual no-retention
     and no-human-review terms. Local models are fine.
   - This project is run by Claude agents, which are an online AI service. Therefore:
     - agents must **never** display or read row-level MIMIC data, IDs, shifted dates or note text;
     - scripts must print aggregates only, with 1–10 suppressed. v1.5 and this screen comply.
   - Existing note-derived artefacts were produced locally: the Qwen3 embeddings (D15) and the Qwen3-235B
     report labels (D13 side files). Their inputs (`notes.parquet`, `report_text` columns) must never be
     opened by an agent.
   - **Open question for Ryan/PI:** whether agent-orchestrated local execution with aggregate-only
     returns is acceptable under our DUAs and Yale policy. If in doubt, a credentialed human runs the
     MIMIC build scripts and agents see only the aggregate summaries.
4. **Which account the copies came from.**
   - Visible on disk: only PhysioNet user `[PI PhysioNet account]` (Rohan Khera). It appears in
     `/mnt/nfs_yale_ecg/mimic/physionet.org/files/download_chunks.sh`, the MIMIC-CXR-JPG download (wget
     `--user [PI PhysioNet account] --ask-password`). The other NFS modules (MIMIC-IV 2.2, Note, ED, ECG) were
     probably obtained the same way (unverified).
   - The raid0 copies record no credential:
     - bb2238, 2026-07 to 09;
     - rbc58, 2026-07-17;
     - ak3398, echo lists;
     - pp675, ECG, which is open access;
     - gih5, D13.
   - Ryan's own MIMIC-IV 3.1 copy (D2) suggests he holds MIMIC-IV access. Confirm his access to **Note,
     ED and ECHO** before using D7, D8 or D13.
5. **Outputs.**
   - Restricted outputs stay under `/mnt/raid0/rbc58/ecg-tte/audits/claude-v*-mimic-*` (umask 077).
   - Only aggregate markdown is committed.
   - No shifted dates, `subject_id`/`hadm_id` or small cells go into docs or the paper. The v1.5 pid is
     a salted hash, but that does not make it shareable.

## Appendix: reproducibility

```bash
AUD=/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-mimic-feasibility
PY=/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python
umask 077
$PY $AUD/stage_icu.py            # ICU subsets: inputevents (vaso/inotrope/sedative items), icustays, ventilation
$PY $AUD/feasibility_screen.py   # 30 definitions -> screen_results.{json,md}; ~3 min
$PY $AUD/panel_coverage.py       # held-out panel coverage -> panel_coverage.json
```

Inputs:
- the v1.5 stage `audits/claude-v15-mimic-shared/stage/*.parquet`;
- D1 `icu/*.csv.gz`;
- the D13 index, as `stage/echo_meas_index.parquet`: study-level subject, id, datetime and test type only.
