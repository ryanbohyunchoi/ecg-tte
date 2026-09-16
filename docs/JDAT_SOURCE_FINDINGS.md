# JDAT source findings

## 2026-09-09 — user-provided T2DM inventory excerpt

Evidence: Ryan supplied a completed T2DM root summary and an excerpt of the file
inventory produced on the H100. The assistant has not accessed the cluster or
opened source records. This is a partial filename review, not a complete source
inventory, schema review, or validated data dictionary.

The supplied summary reports 4,309 files totaling 1,069,923,851,277 bytes under
`/home/rbc58/mnt/t2dm-jdat-data`. These totals include all inventoried files, not
necessarily unique raw data. Other roots had not completed in the supplied status.

### Candidate source families

| Filename suffix in the `2380791_CarDS_Outcomes_DM2_` delivery | Candidate role; contents unverified |
|---|---|
| `Patients.txt` | Patient linkage and demographics. |
| `Inclusion_Dx.txt` | Diagnoses related to extract inclusion; investigate cohort-selection rules. |
| `Medical_Hx.txt`, `Problem_List.txt` | Medical history and recorded problem list; date/status semantics unresolved. |
| `Meds.txt` | Medication records; prescribing, history, reconciliation, and dispensing semantics unresolved. |
| `Hosp_Enc_Med_Admin_1.txt`, `_2.txt` | Hospital medication administration candidates. |
| `Outpatient_Enc_Med_Admin.txt` | Outpatient medication administration candidate. |
| `Outpatient_Enc.txt` | Outpatient encounter candidate. |
| `Outpatient_Enc_CPT.txt`, `Outpatient_Enc_ICD_PX.txt` | Procedure-code candidates; code versions and completed/ordered status unresolved. |
| `Outpatient_Enc_Flo_Vitals.txt` | Vitals/flowsheet candidate. |
| `Hosp_Enc_Labs_1.txt` through `_6.txt` | Hospital lab shard candidates. |
| `Outpatient_Enc_Labs_1.txt`, `_2.txt` | Outpatient lab shard candidates. |

### Delivery and completeness issues

- `Hosp_Enc_Labs_1 copy.txt`, `Hosp_Enc_Labs_1.txt`, and
  `Hosp_Enc_Labs_1_2023_09_15.txt` have different byte sizes. They are not
  byte-identical files; overlapping clinical records, replacement deliveries,
  or incomplete copies remain possible. Do not concatenate or select by size/date alone.
- An outpatient lab shard also has an undated and a `_2023_09_15` variant.
  Resolve the entire delivery/shard set rather than mixing versions independently.
- The T2DM tree also contains a nested `Data-2024-03-12` delivery with
  `2435227_CarDS_ECG_Labs_1.txt` through `_12.txt` and medication administration
  shards. Different extract identifiers and the containing directory suggest
  separate provenance; shared patients/events are not yet known.
- Several nested lab files have companion names ending `.partial`, including
  one zero-byte file. Keep these out of candidate ingestion pending delivery
  verification. A corresponding `.txt` filename does not itself prove completion.
- `output.log` is an operational artifact, not a clinical source table candidate.
- Do not delete, merge, or rename any original files during this investigation.

### Inventory-label corrections

The current filename heuristic mislabeled `Outpatient_Enc.txt` as demographics
because `patient` matches within `outpatient`. It also labeled
`CarDS_ECG_Labs_*.txt` as ECG because the extract prefix was matched before `Labs`.
Treat those entries as encounter and lab candidates respectively. Existing
category counts are unreliable domain summaries and should not drive feasibility.
The underlying filenames and byte sizes remain the evidence supplied by the user.

### Next evidence needed

Review remaining delivery-level filenames and source dictionaries/manifests. Then
build a bounded header-only inspector for explicitly selected complete candidate
files, with PHI-safe failure behavior and no patient-row output. Use schemas and
delivery documentation to establish patient/encounter linkage, timestamp columns,
medication record classes, lab codes/units, and version/shard relationships before
any row-level profiling or merging. Mortality, hospital encounter linkage, notes,
and actual imaging assets have not been established by this excerpt.

## 2026-09-16 — user-provided successful header report

The attached report supersedes the earlier missing-file report: 36 files have
tab-delimited header candidates; two dated lab variants were rejected as
`unrecognized_or_ambiguous_header`. The cause of the earlier path failure remains
unknown. No source records have been inspected by the assistant.

Observed column evidence:

- Patient table: `PAT_ID`, `PAT_MRN_ID`, `BIRTH_DATE`, `DEATH_DATE`, sex/race/ethnicity.
  Linkage, completeness, and historical demographic availability remain untested.
- Diagnosis/history tables: ICD9/ICD10 lists, local diagnosis IDs and several
  event/entry dates. These do not establish comprehensive encounter diagnosis coverage.
- Medication orders: local medication IDs/names, order class/source/status, dose,
  route, order/start/end dates, and refill/quantity fields. No explicit RxNorm/NDC
  field in the supplied header; pharmacy dispensing semantics remain unverified.
- Administration: order and encounter IDs, `TAKEN_TIME`, `MAR_ACTION`, dose/route.
- Procedures: CPT codes and ICD procedure billing codes with code-set fields/dates.
- Vitals: local flowsheet IDs/names, recorded time, value and `UNIT`.
- Labs: local component IDs/names, specimen metadata, values, collection and result
  times. No explicit LOINC or lab-unit field in the supplied lab headers. T2DM labs
  have 60 columns; the nested delivery has 55. Same column count is not a sufficient
  schema match: the two administration families have 39 columns but different hashes.

Assessment: adequate structural evidence to begin an OMOP-vocabulary mapping pilot,
not yet evidence that a complete or faithful CLMBR-T input can be produced.
Next investigate local-to-standard code crosswalks, event-time semantics, lab units,
patient linkage and vocabulary coverage in the exact pretrained tokenizer. A full
OMOP database is optional for the model adapter; standardized, temporally correct
events must satisfy the pinned CLMBR-T/FEMR input contract.

## 2026-09-16 — first bounded record audit returned by Ryan

Header report SHA-256: `d22097606fd67c1410886c1ee9a8089cc297f33ec31a56285f4ca30996698972`.
Seven files (indices 2, 5, 6, 7, 9, 10, 13) each accepted the first 100,000
records, with status `bounded_prefix`, valid counts and no reported parse failures.
This is 700,000 records across separate files, not unique patients or a random sample.

Distinct raw cells: ICD9 list 362; ICD10 list 550; medication order IDs 6,112;
administration medication IDs 1,063; encounter types 25; CPT cells 2,136;
flowsheet IDs 7; lab component IDs 274; MAR action codes 14. These are not verified
standard concepts, unique ingredients, individual diagnoses, or mapped events.

Every audited field had zero empty/whitespace cells, including discontinuation,
infusion-end and hospital dates. Literal null markers are counted as nonempty by
version 1. Therefore these results do not establish completeness: next audit
candidate missing-value markers and date/numeric validity without emitting source
values. Placeholder use is a hypothesis, not an observed fact. Do not silently
reclassify source-specific sentinel codes without evidence.

Standard mapping and tokenizer coverage remain explicitly unassessed. Source
dictionaries, lab units, time semantics and longitudinal diagnosis coverage remain
unresolved. No patient-level records or restricted code catalog were received.
