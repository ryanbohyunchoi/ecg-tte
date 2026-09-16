# cards-misc OMOP input and PSM readiness audit

Reviewed 2026-09-16. This is a code and committed aggregate-metadata audit, not a
validation of the H100 gold tables. No cluster connection or patient-row inspection.

## Existing bb2238 report received — 2026-09-16

The user-run inspector found seven manifests and selected all seven. The newest
recorded full ETL is June 22, 2026, run
`029e6e60-35ce-4a77-b491-0dfc3b1df071`, stage all/local true, steps 1–6, no recorded
step errors. This is newer-run evidence within the supplied manifest history,
not proof that no unrecorded later writes occurred. No Git revision is supplied.

Current metadata: person has one file with 879,547 rows; no regular parquet files
were found for visit_occurrence or procedure_occurrence. All three sampled drug
schemas lack drug_concept_id, dose, route, administration action and encounter ID.
Sampled measurement schemas omit units and availability times. The measurement
samples are early vital partitions only; they do not enumerate the lab concepts.
Together with the manifests, this is consistent with the narrow mapping, not the
expanded feature branch; it does not identify an exact producing commit.

Latest full-run counts (historical manifest, not recomputed current table totals):

| Domain | Recorded gold output | Relevant losses |
|---|---:|---|
| Person | 879,547 | 49 source rows rejected as invalid_sex |
| Death | 103,111 | Completeness and temporal plausibility remain unvalidated |
| Condition | 132,775,140 | 15,187,034 unmapped_snomed rejects in diagnosis processing |
| Observation | 34,538,453 | Derived diagnosis domain; not evidence of mapped history/visit tables |
| Labs | 15,519,308 | 330,969,813 unmatched_lab, 226,993 range, 63,103 numeric rejects |
| Drugs | 85,767,598 | 39,720,674 unmapped_atc rejects |
| Vitals | 19,349,129 | 54,952,951 unmatched_vital rejects |

Using cleaned silver rows as denominators: lab retention 4.48% of 346,779,217;
drug retention 68.35% of 125,488,272; vital retention 26.04% of 74,302,080.
These are row retention rates, NOT mapping accuracy, patient coverage or causal
adequacy. Most lab/vital loss reflects the explicitly restricted feature definitions.
Diagnosis mapping explodes lists and can produce multiple target concepts, so no
simple output/input mapping percentage is asserted for that domain.

Observation_period was inferred; 35,915 people (4.08%) lacked an inferred end date.
The reviewed code falls back to birth in this situation and uses birth as the start
for all people. This cannot establish valid baseline/washout or follow-up coverage.
Early death partition labels also warrant aggregate temporal-plausibility review,
without inferring patient-specific dates or the cause from metadata alone.

The full run records **23 staged input files**, not the 24 candidates in today's
raw inventory: 1 person + 4 diagnoses + 10 labs + 5 medications + 3 vitals.
`Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_4` is absent from that run's source list.
Its later inventory presence does not prove it existed at run time or should be
concatenated without delivery review. Person/death still originate from the 2025
patient extract, while the event inputs span 2025 and 2026 deliveries. Mortality
refresh and event-to-person linkage need verification.

Verdict: usable foundation for trial-specific baseline feasibility; insufficient
evidence to declare a robust target-trial PSM baseline ready. First assess one
chosen treatment/comparator's exposure ascertainment, covariate availability,
prior-history and endpoint requirements using read-only aggregates. No remapping
or modifications of bb2238 are authorized or performed.

### Input paths recorded in the latest full-run manifest

Paths below are relative to the common study segment within staging; these are
parquet inputs actually recorded by the run, not raw files read directly in that run.

**Step 1: 1 files**

- `Data-2025-04-03/CarDS_2435227_Patients.parquet`

**Step 2: 4 files**

- `Data-2025-04-03/CarDS_2435227_Hosp_Enc_DX.parquet`
- `Data-2025-04-03/CarDS_2435227_Outpatient_Enc_DX.parquet`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_DX.parquet`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_DX.parquet`

**Step 3: 10 files**

- `Data-2025-04-03/CarDS_2435227_Hosp_Enc_Labs_1.parquet`
- `Data-2025-04-03/CarDS_2435227_Hosp_Enc_Labs_2.parquet`
- `Data-2025-04-03/CarDS_2435227_Hosp_Enc_Labs_3.parquet`
- `Data-2025-04-03/CarDS_2435227_Outpatient_Enc_Labs.parquet`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_1.parquet`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_2.parquet`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_3.parquet`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Labs_1.parquet`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Labs_2.parquet`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Labs_3.parquet`

**Step 4: 5 files**

- `Data-2025-04-03/CarDS_2435227_Outpatient_Enc_Med_Admin.parquet`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Med_Admin_1.parquet`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Med_Admin_2.parquet`
- `Data-2026-04-15/CarDS_2435227_Meds.parquet`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Med_Admin.parquet`

**Step 5: 3 files**

- `Data-2025-04-03/CarDS_2435227_Outpatient_Enc_Flo_Vitals.parquet`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Flo_Vitals.parquet`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Flo_Vitals.parquet`

## Original code-level assessment (before output report)

The documented raw source families are promising for a strong propensity-score
baseline. The current `main` gold transforms are too limited to assume they support
a defensible medication-based target trial out of the box. Start feasibility work
with the existing outputs, establish their producing revision, then augment the
specific exposure/visit/measurement fields needed for the first trial. A complete
OMOP remap or CLMBR-T deployment is not a prerequisite for this baseline.

The immediate ACC objective is to compare unsupervised clustering and cosine-based
matching with a strong conventional PSM comparator. Improvement remains a hypothesis.
Keep the source cohort, index, outcome, estimand and baseline cutoff identical in
paired comparisons, and audit retention/overlap as well as covariate balance.

## Versions and what was actually pulled

Repository: `https://github.com/brunombatinica/cards-misc`.
Local path: `/Users/ryanchoi/Desktop/Research/github/reference/cards-misc`.

- Initially checked out: `feat/omop-procedures-visits`, `9e9fbc9`, July 18.
  Pulling that branch reported up to date. It contains eleven steps, broader
  lab/vital definitions, RxNorm ingredient mapping, visits/history/procedures,
  and separate `rbc_scripts`.
- Fetched and fast-forwarded local `main` to `33532e6`, September 16. The feature
  branch remains preserved. Main has six registered steps and does NOT contain
  the feature branch's expanded transforms. Calendar recency does not identify
  which implementation produced Ryan's existing gold output.
- Today's committed `schema_audit_all/REPORT.md` describes a schema-discovery run
  at 12:58:36, sampling the first 10,000 rows per file, with `ignore_errors=true`.
  It is not a successful gold ETL manifest, a complete row-accounting report or
  proof that these files reached the output being used for this project.

Both branch implementations were inspected as text; neither pipeline was executed.

## Source coverage

The registered cohort is `2435227-CarDS-ECG`, described as adults at Yale with at
least one ECG, under:

`s3://spinup-002c89-implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG`

The latest inventory includes 64 files in `Data-2025-04-03` and `Data-2026-04-15`.
This is a different extract family from the `2380791` DM2 files previously profiled.
Do not assume equivalent populations, identifiers or delivery completeness.

Matching main's five raw-input step patterns against the committed 64-file inventory
selects **24 files**: one patient, four diagnosis, eleven lab, five medication and
three vital files. These are resolved candidate inputs, NOT a reconstructed list
of files consumed by an unprovided gold run manifest. The older targeted inventory
lists only ten lab files, further supporting the need to identify the actual run.

| Raw family | Main gold use | Additional raw data available |
|---|---|---|
| Patients | Person, death, cohort | Only a 2025 Patients file in latest inventory; assess linkage of newer event patients and mortality freshness. |
| Inpatient/outpatient encounter DX | ICD10-to-SNOMED conditions/observations | ICD9 and encounter/source detail exist upstream but are not fully retained. |
| Labs | Five categories: total cholesterol, HDL, eGFR, creatinine, HbA1c | Many other analytes, specimen/result times and component IDs exist upstream. |
| Medication orders and administrations | First-name-token to ATC; unmatched rows rejected | IDs, order class/status, dose/route, administration action and timing available upstream. |
| Vitals | BMI and systolic BP | Other measurements and units exist upstream. |
| Hospital/outpatient encounter tables | Staged/profiled only | Admission/discharge, ED/inpatient flags, encounter IDs, disposition. |
| Problem list and medical history | Staged/profiled only | Additional longitudinal history, with timing semantics requiring review. |
| CPT and ICD procedure extracts | Not mapped by main | Eight files across hospital/outpatient and both deliveries. |
| Imaging, family history, allergies, genetics, notes | Not mapped by main | Available in the inventory; necessity depends on trial. Notes are not required for the initial structured PSM baseline. |

## Findings that affect target-trial validity

### 1. Medication exposure is the primary blocker

`steps/step4_medications.py` uses `ORDER_INST` for both orders and administration
files. Silver retains only medication name, simple generic and pharmacologic class
besides derived patient/time/year. It discards source-file identity, order IDs,
encounter IDs, administration actions, start/end/discontinuation, dose and route
from the event output. Gold sets both start and end to the order timestamp,
uses first-token ATC matching and rejects unmapped drugs. Main has no standard
`drug_concept_id` column.

Consequences: gold alone cannot reliably distinguish prescribing from receiving a
dose, determine exposure duration, reject held/canceled administration records,
or establish a dose/formulation-specific treatment strategy. Drug presence may
be useful as a baseline feature after mapping validation, but the index event needs
a separate source-grounded contract. Neither an ATC code nor RxNorm alone repairs
missing event semantics. The feature branch keeps unmapped rows and adds RxNorm,
but still uses order time and can collapse combinations to a first ingredient;
it is not automatically a validated exposure layer.

### 2. Observation history starts at birth

`steps/step6_observation_period.py` starts every observation period at birth,
ending at the last selected gold event or a hand-entered extraction date. This is
not evidence of longitudinal capture since birth or continuous follow-up. Do not
use it directly to declare a 365-day washout or baseline observation period.
Build evidence-based history rules and state the limits of EHR follow-up.

### 3. Encounter and procedure information is available but not mapped on main

Main registers steps 1–6 only. `definitions/raw_sources.py` explicitly treats
encounters and histories as staging-only. Hospital outcomes, encounter-linked
phenotypes, prior utilization and procedural confounders therefore cannot simply
be assumed available in main's gold. Feature-branch code provides reusable ideas,
but the actual gold table schema and run version must be checked first.

### 4. The measurement selection is narrow and contains transformations needing review

Main retains five laboratory categories and BMI/systolic BP only. It does not
retain many potential trial-specific severity measures. eGFR values such as `>60`
are replaced with 90; inequality operators are not preserved as quantitative
semantics. Lab dedup keys use patient, specimen date, procedure name and component
name, omitting the order/result ID and value. Different same-day results can thus
collapse. Source-path ordering favors an earlier lexicographic delivery for matching
keys. Gold measurement output omits units and result-availability timestamps.

Revisit only the measurements required for the first protocol initially, with
validated units, source-specific missing values and strict pre-index rules. Do not
use the narrow PREVENT-oriented selection as a universally adequate baseline.

### 5. Linkage, chronology and completeness still need output-level checks

Silver drops source provenance and encounter IDs for the mapped events. Medications
and vitals have no deduplication, so overlap between dated deliveries can inflate
counts. Diagnosis dedup omits encounter identity, and mapping can fall back to an
ICD10 stem. Missing/unmapped codes can reduce confounder and endpoint capture.
The demographic step excludes sex values outside Male/Female and defaults unknown
ethnicity to non-Hispanic; these need explicit review rather than treating them as
validated demographic encoding. Only the 2025 Patients file is inventoried, while
2026 event files exist: test event-to-person linkage and mortality update coverage.
None of these checks can be resolved by filename presence alone.

## Evidence in today's raw schema report

The raw schemas contain useful medication class/status/action and temporal fields,
plus hospital encounter and lab-result detail. Under the report's explicit
`nullstr=['NULL','']` handling, the 10,000-row 2026 medication-order prefix has
48.30% missing START_DATE, 47.85% missing ORDER_STATUS and 66.93% missing ORDER_SOURCE.
The first hospital administration prefix has 93.86% missing INFUSION_END_TIME.
Outpatient vitals have 53.84% missing UNIT. These are start-biased samples, not
cohort-wide rates. They demonstrate why nonempty strings are not sufficient QC;
they do not establish the null conventions for the separate DM2 source.

## User clarification: existing bb2238 output is read-only

Ryan confirmed that the immediate task is to assess the existing bb2238 dataset,
not change or rerun it. Use `RUN_EXISTING_OMOP_AUDIT.md` to collect manifests and
footer/schema metadata with no patient-row access and no writes under bb2238.
Any later augmentation discussed below is a proposal, not authorization to modify
that dataset. No remapping or data processing was run during this audit.

## Minimal next milestone for the ACC baseline

1. Identify the exact gold root(s), producing revision/run manifest, completed
   steps, schemas and source-file list. Do not pool `gold` and `gold_rbc` blindly
   or rerun main over the existing output. Review aggregates only outside the cluster.
2. Choose one target/comparator trial protocol on clinical/source feasibility,
   without selecting for agreement with an already-viewed estimate. Establish the
   treatment evidence, eligibility, time zero, baseline window and endpoint first.
3. Audit existing gold for candidate counts, patient linkage, mapping completeness,
   missingness, prior history, encounter/outcome availability and duplicate effects.
4. Add a narrow source-derived exposure table and any required visit/lab fields.
   Reuse gold where verified; preserve the existing output as a versioned snapshot.
5. Fit a clinical PSM baseline, then a prespecified expanded structured/regularized
   PS baseline if feasible. Include demographics, calendar time, clinical history,
   co-medications, measured severity and utilization as justified by the protocol.
   Evaluate overlap, retention and pre/post-match balance. A high propensity-score
   value or treatment-prediction AUC is not the success criterion.
6. Compare clustering/cosine methods on declared common populations and estimands,
   using pre-index representations and outcome-blind tuning. CLMBR-T mapping can
   proceed later if the selected representation requires it.

OHDSI's CohortMethod provides a reference implementation of large-scale regularized
PS models using diagnoses, drugs, procedures and demographics, with matching and
balance diagnostics: https://ohdsi.github.io/CohortMethod/ . This does not establish
that the current parquet output is complete OMOP or compatible without an adapter.

## Exact candidate inputs from the latest inventory

These paths are relative to the registered root above. Generated by matching the
source patterns in main `33532e6` against the committed inventory; no source access.

### step1_demographics — 1 files

- `Data-2025-04-03/CarDS_2435227_Patients.txt`

### step2_diagnoses — 4 files

- `Data-2025-04-03/CarDS_2435227_Hosp_Enc_DX.txt`
- `Data-2025-04-03/CarDS_2435227_Outpatient_Enc_DX.txt`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_DX.txt`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_DX.txt`

### step3_labs — 11 files

- `Data-2025-04-03/CarDS_2435227_Hosp_Enc_Labs_1.txt`
- `Data-2025-04-03/CarDS_2435227_Hosp_Enc_Labs_2.txt`
- `Data-2025-04-03/CarDS_2435227_Hosp_Enc_Labs_3.txt`
- `Data-2025-04-03/CarDS_2435227_Outpatient_Enc_Labs.txt`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_1.txt`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_2.txt`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_3.txt`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Labs_4.txt`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Labs_1.txt`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Labs_2.txt`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Labs_3.txt`

### step4_medications — 5 files

- `Data-2025-04-03/CarDS_2435227_Outpatient_Enc_Med_Admin.txt`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Med_Admin_1.txt`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Med_Admin_2.txt`
- `Data-2026-04-15/CarDS_2435227_Meds.txt`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Med_Admin.txt`

### step5_vitals — 3 files

- `Data-2025-04-03/CarDS_2435227_Outpatient_Enc_Flo_Vitals.txt`
- `Data-2026-04-15/CarDS_2435227_Hosp_Enc_Flo_Vitals.txt`
- `Data-2026-04-15/CarDS_2435227_Outpatient_Enc_Flo_Vitals.txt`
