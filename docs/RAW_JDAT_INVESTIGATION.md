# Raw JDAT investigation and data contract plan

**Status:** investigation specification, 2026-09-09. Source names and locations
below come from legacy code/notes; they have not been verified during the restart.
No raw patient data have been accessed by this task.

## 1. Establish the source universe

Inventory all authorized extracts, not only medication files and not only patients
who already have ECGs or echoes. Determine how each extract's patient population
was selected: diabetes, cardiomyopathy, ECG availability, implementation cohort,
other disease criteria, dates, or later clinical events. Selection of the extract
itself can constrain the emulation population or condition on future information.

| Legacy lead | Previously recorded location | What remains unknown |
|---|---|---|
| T2DM JDAT | `/home/rbc58/mnt/t2dm-jdat-data` | Current versions, all domains, extract inclusion rules, full dates. |
| CMP JDAT | `/home/rbc58/mnt/cmp-jdat-data` | Same questions; overlap with other extracts. |
| Implementation JDAT | Previously under `/home/rbc58/mnt/implementation/.../2435227-CarDS-ECG/Data-2026-04-15` | Exact current path, refresh/versioning, available notes and imaging links. |
| ASCVD source | `/home/rbc58/mnt/ascvd` | Whether original JDAT tables exist beyond derived OMOP. |
| ECG waveforms | `/mnt/raid0/bb2238/signals/preprocessed/all_ecgs` | Raw signals versus derived arrays, preprocessing provenance, other signal collections. |
| ECG/echo metadata | `/mnt/raid0/rbc58/mm_vhd/metadata` | Source lineage, study identifiers, timestamp precision, completeness. |
| Echo media | No verified path | Videos/images, view labels, storage format, access, checkpoints. |
| Clinical notes | No verified path | Text availability, note/version timestamps, included types, source restrictions. |

Examples of historical medication filename stems are `2380791_CarDS_Outcomes_DM2`,
`2356781_CarDS_Aim_1`, and `CarDS_2435227`, with `_Meds.txt`,
`_Outpatient_Enc_Med_Admin.txt`, and `_Hosp_Enc_Med_Admin_*.txt` suffixes. These
patterns are discovery leads, not a fixed source specification.

Request the JDAT extraction request/specification, data dictionary, code lists,
delivery dates, correction history, and known missing domains. Record expected
versus delivered files and whether extracts are cumulative or incremental.

## 2. New profiler: bounded, read-only, aggregate-only

Implement the profiler from scratch after access and source roots are established.
The old explorers may inform questions but are not safe active tools: some emit
raw examples on errors, sample only leading rows, or silently skip malformed rows.

### Pass A — inventory and schema

- Enumerate explicitly configured roots with deterministic file ordering. Avoid
  following arbitrary symlinks outside those roots. Separate source from output paths.
- Record source ID, delivery/version, file type, compression, byte size, metadata,
  schema fingerprint, header names, delimiter/encoding candidates, and shard membership.
- Use metadata-only inspection where possible. Mark row counts as exact, estimated,
  or unknown; a line count is not a record count for multiline quoted text.
- Do not assume UTF-8/Latin-1, delimiter, quoting, or date-column semantics merely
  because a parser returns rows. Make parsing decisions explicit and reproducible.
- Define snapshot identities using immutable delivery manifests/object versions
  where available. Distinguish a cheap metadata fingerprint from a content hash;
  decide full hashing costs before scanning multi-terabyte sources.

### Pass B — representative profiling

- Sample deterministically across files, shards, delivery cohorts, and time coverage;
  do not use only the first N records. Use bounded-memory streaming/reservoir sampling
  where needed and label sample statistics as sampled.
- Measure missingness, parse success, key uniqueness/duplication, date precision,
  candidate linkage coverage, source vocabulary distribution, and units.
- Output aggregate summaries only. Never output patient rows, identifiers, note
  snippets, free-text frequency lists, raw failing lines, or raw exception payloads.
- Categorical output is opt-in for clinically reviewed code/unit/status fields;
  arbitrary strings can contain identifiers. Aggregate dates to approved coarse
  periods. Apply the institution's aggregate/small-cell rules; do not invent an
  unsanctioned universal cutoff.
- Keep detailed source filenames/paths and lineage reports in the restricted
  environment if their contents might identify patients or reveal sensitive context.

### Pass C — full-scan validation for promoted sources

- Validate parsers over every shard before a source enters a scientific cohort.
- Account for all input records as accepted, rejected, or quarantined by reason.
  Parsing failures must be counted, localized to a source version, and reviewed.
- A malformed row is not silently discarded. Do not replace undecodable bytes or
  truncate fields without counts, explicit policy, and clinical impact assessment.
- Use restricted row-level lineage internally for audit, with no record examples
  exported to logs/chat. Missing mandatory keys or unresolved encoding changes stop
  source promotion; optional-domain failures remain explicit statuses.
- Store progress checkpoints only when source identity and parsing configuration
  match. Return nonzero status for incomplete/failed required profiling.

### Intended report bundle

| Artifact | Purpose |
|---|---|
| `source_manifest.json` | Source versions, scan scope, fingerprints, profiler/config version, completion state. |
| `schema_catalog.json` | Column types, semantic candidates, unresolved parsing/date decisions. |
| `parse_quality` | Exact/sample counts, rejected records, missing mandatory fields, encoding/format changes. |
| `identity_overlap` | Aggregate within/across-source linkage, collisions, unmapped fractions, patient overlap. |
| `domain_coverage` | Domain coverage by cohort/year and observation-history duration. |
| `medication_semantics` | Order/admin/history/dispense evidence and record-class distributions. |
| `measurement_catalog` | Raw codes, reviewed labels, units, numeric/qualifier handling, coverage. |
| `encounter_outcome_coverage` | Encounter linkage, care settings, death/event capture, known ascertainment gaps. |
| `modality_coverage` | Pre-index availability by proposed windows, input validity, timestamp/version coverage. |
| `source_decisions.md` | Evidence-backed mapping choices, unresolved items, domain reviewer, promotion status. |

Machine-readable tables stay outside the repository by default. Only reviewed
aggregate summaries are candidates for repository inclusion.

## 3. Domain investigations

### Identity, demographics, and extract overlap

Establish a source-namespace-aware patient identity map and stable internal key.
Preserve raw IDs in a restricted linkage table. Keep identifiers as strings;
leading zeros and alphabetic prefixes may be meaningful. Do not apply blanket
prefix removal without demonstrating one-to-one mapping and collision behavior.

Quantify one-to-many MRN/person relationships, reused identifiers, merges/splits,
missing keys, and disagreement in demographics. Define a reviewed authority and
temporal policy for conflicting demographic fields. Keep date-of-birth-derived
age internal; report only approved aggregates. Multiple extracts containing the
same patient are not independent datasets.

### Observation and follow-up

Determine delivery cutoff, domain-specific start/end coverage, encounter visibility,
outside-system care, and mortality capture. A patient's last encounter is not proof
of complete event-free observation up to that date, and first recorded contact is
not proof that earlier medication exposure did not occur. Evaluate baseline
lookback/continuity rules and alternative observation proxies per trial.

Distinguish event time from entered/recorded time and extract time. Identify delayed
coding, retroactive problem-list entries, and historical events imported later.
Do not use the maximum observed death date as the database's administrative end.

### Medication evidence

Separate at minimum: written prescription, dispensing evidence, administration,
historical medication entry, reconciliation, inpatient discharge prescription,
cancellation, discontinuation, and reorder/correction.

For each record class determine the meaning of order/start/end/admin/contact dates,
status history, original prescription/order ID, ingredient/product identifiers,
dose, formulation, route, quantity, days supply, frequency, and linkage to encounters.
Current final status may reflect a future discontinuation and should not
retroactively determine whether a prescription existed at baseline.

Investigate whether true pharmacy fills exist. If only prescribing data exist,
define prescribing strategies and describe that departure from dispensing-based
trials. Historical entries can document prior use without establishing initiation.
Repeated entries or different order dates do not automatically establish refills
or adherence. Deduplicate repeated deliveries and amended/reordered events using
source identifiers and a documented fallback key.

Build treatment definitions from reviewed ingredient/product mappings, with
explicit formulations, combinations, dose, route, and ambiguous matches. A
substring that assigns combination products to both arms needs an explicit rule,
not a first-arm-wins tie break. Decide same-day competing starts before outcomes.

### Diagnoses, encounters, and procedures

Identify billing versus problem-list versus encounter diagnoses, primary versus
secondary position, rule-out/history flags, ICD versions, onset versus service
versus coding date, and encounter linkage. Distinguish inpatient, ED, observation,
outpatient, and telehealth settings from actual source semantics.

Reconcile admission/discharge chronology, transfers, overlapping encounters, and
the same episode appearing in multiple files. Verify procedure/code systems and
whether completed versus ordered procedures can be distinguished. Disease history
and incident endpoints require different definitions and lookbacks.

An HF diagnosis without a qualifying encounter is not silently converted into HF
hospitalization. Source constraints lead to an explicit alternative phenotype/tier
or to infeasibility, not an automatic endpoint fallback.

### Labs, vitals, and structured echo measurements

Inventory all available measures; do not inherit the old five-lab/two-vital limit.
For trial candidates investigate renal function, electrolytes, hemoglobin,
glycemia, lipids, BNP/NT-proBNP, troponin, blood pressure, height/weight/BMI, and
relevant echo measurements if present. Availability is unknown until profiled.

Resolve local analyte codes/labels, specimen type, result versus order/collection
time, final/corrected versions, units, assay changes, duplicate panels, reference
ranges, qualitative results, and values such as `<x` or `>x`. Retain original
values/units/qualifiers alongside reviewed normalized values. Incompatible units
or specimens do not get pooled because labels match.

Define clinically justified range checks and test conversions. Do not silently
clip real extreme values to cohort minima/maxima. Corrected values available
after index are not automatically valid baseline measurements. Derived eGFR/BMI
must record the formula and required inputs. Select last/nearest/summary measures
using a prespecified baseline window rather than the value that best matches an RCT.

### Mortality and nonfatal outcomes

Inventory death sources, linkage, date precision, completeness, updates, and
cause availability. Distinguish verified death, uncertain death, and no recorded
death. Review capture differences by source/year. Cause-specific mortality cannot
be inferred from a date-only field without an explicit proxy designation.

For each endpoint, establish incident status, event dates, inpatient specificity,
recurrent episodes, competing death, adjudication availability, and censoring.
For composites preserve all components and select the first qualifying event only
under the registered definition. Test equality at index/censor dates and prohibit
negative follow-up or events after censoring from silently entering estimates.

### Notes and imaging

For notes inventory authored/service/signed/amended timestamps, historical versions,
note types, templates, copied-forward content, extract filters, and linkage. A note
about a pre-index visit may contain facts added after treatment initiation. If
availability timing cannot be established, flag/exclude it from the primary baseline
representation according to a frozen rule.

For ECGs inventory original and preprocessed signals, sampling/lead/unit metadata,
quality flags, study times, file identity, and model preprocessing lineage.
For echoes determine available video/still/report assets, views, frame counts,
study dates, acquisition devices, and image/report linkage. Count patients and
studies separately; more frames or repeated tests must not become more subjects.

## 4. Proposed normalized contracts

Preserve native source details; normalization is an auditable representation,
not a claim that every source has the same clinical semantics.

| Entity | Minimum contract |
|---|---|
| Source asset | Source namespace, extract/version, schema/parser fingerprint, file/shard identity, counts, QC status. |
| Patient identity | Stable internal patient ID, namespaced source key, validity/merge evidence, collision status. |
| Event | Patient ID, event ID/type, clinical time/precision, availability time/quality, source record/version, code system/code, encounter ID when supported. |
| Medication event | Event class, ingredient/product, dose/route/formulation, original order/dispense/admin times, status/version, encounter, confidence. |
| Measurement | Raw/normalized value and unit, qualifier, analyte/specimen, collection/result/availability times, correction/version, validity. |
| Encounter | Patient, encounter ID, care setting, admission/discharge, transfer linkage, source provenance. |
| Modality study | Patient/study ID, modality, acquired/available times, asset references, quality/preprocessing, report linkage. |
| Trial episode | Trial/protocol, patient/episode ID, treatment, index, eligibility evidence, observation boundaries, attrition reasons. |
| Baseline snapshot | Trial episode, cutoff policy, selected event/study IDs, feature definitions, missingness states, snapshot hash. |
| Outcome | Trial episode, definition/version, component/event time, censor time/reason, effect horizon, validity status. |

Absent required timestamps, identities, or source evidence remain explicit unknowns.
They are not filled with dates or IDs from a loosely related table.

## 5. First milestone acceptance criteria

1. Every expected source is catalogued as present, absent, or unresolved.
2. Promoted-source parsers have exact accounting and no unexplained row loss.
3. Identity transformations and joins have measured collision/multiplication checks.
4. Medication initiation evidence is separated from history/admin/reconciliation.
5. Observation, encounter setting, endpoint dates, and availability-time limitations
   are documented well enough to screen candidate trials.
6. Measurement and modality coverage is measured beyond the old OMOP selection.
7. Each source has a named decision/evidence record; unsupported assumptions remain
   blocked from clinical analysis.
8. The profiler passes synthetic malformed-row, embedded-delimiter, date/unit,
   duplicate-key, privacy-output, bounded-memory, and restart/failure tests.

Deliver a source report and candidate feasibility questions before choosing final
feature sets or writing treatment-effect code.
