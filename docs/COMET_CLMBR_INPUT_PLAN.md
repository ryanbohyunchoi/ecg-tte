# COMET CLMBR-first representation plan

User direction, 2026-09-23: proceed with frozen CLMBR-T using newly mapped OMOP
gold while the user locates the general BCL ECG weights. This document specifies
the next implementation, not a completed embedding run or validated data source.

## Population and time zero

Start with all 7,499 patients in the verified cleaned COMET preparation:
`/mnt/raid0/rbc58/ecg-tte/audits/comet-mice-prep-M9F28Lk2/report`.
Preserve treatment arms, index dates, eligibility, existing MICE and PSM versions.
Do not require ECG coverage or membership in a historical CLMBR cache.

Resolve trimmed exact patient_key to OMOP person_source_value/person_id, with
explicit missing and one-to-many/many-to-one checks. Do not strip prefixes or
leading zeros. Conflicts must remain separate from no-history exclusions.

Every clinical event must be strictly before index-date midnight under the source
clock convention. Exclude same-calendar-day and future events; report unparseable
and missing timestamps. Event date and record availability are separate concepts:
record any inability to verify availability at index. No future visit discharge
information or future-derived features. Include available prior history without
silently imposing the ECG 365-day window; record actual model truncation and token
selection. Birth/sex encoding must follow the verified tokenizer/input contract.

## Sources and model

Candidate source: `/mnt/raid0/rbc58/omop/gold`; confirm whether the user's newly
mapped gold is this snapshot or a newer one. Previously reviewed mapping coverage
is historical evidence, not proof of current partition lineage or tokenizer coverage.
Candidate vocabulary reference: `/mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv`.
Candidate frozen model directory: `/mnt/raid0/eo287/clmbr` (existence confirmed,
checkpoint/tokenizer identity not yet verified).

Read only the cohort's relevant projected person/event columns from the gold
snapshot. Reuse a compatible standardized-event cache if provenance can be
verified; otherwise create a cohort-specific cache. Do not rebuild JDAT or OMOP.
Do not import archive code or use historical prognostic disease heads.

OMOP concept IDs are inputs to vocabulary resolution, not automatically valid
CLMBR tokens. Verify concept-to-code conversion and actual tokenizer acceptance.
Report concept-zero/unmapped and unsupported events by domain and treatment arm,
patients with no retained events, history length, and model truncation. Numeric
values, units, birth/sex tokens and timestamp rules need explicit handling under
the actual tokenizer version; do not silently copy old values-dropped defaults.
Prior HF and medication evidence are legitimate baseline history; do not inherit
prognostic disease-code masking from unrelated archived experiments.

## Execution and artifacts

1. Confirm source snapshot, required column schemas, MRN/person mapping and the
   local CLMBR checkpoint/tokenizer/runtime identity.
2. Build a reusable cohort-specific pre-index event cache and aggregate coverage
   report. Save source lineage, mapping policy and cutoff for each subject locally.
3. Run a small inference smoke test, then all supported cohort members. Save
   immutable checkpoint/tokenizer hashes, code/config version, finite vector QC,
   vector dimension and explicit per-patient failure reasons on the cluster.
4. Preserve raw vectors. Apply a declared normalization only for matching and
   cache it separately. Clinical PSM and CLMBR matching use the same eligible
   CLMBR-covered cohort for the primary paired comparison; report coverage losses.

All new data/cache/model/run artifacts belong under `/mnt/raid0/rbc58/ecg-tte/`,
with fresh private outputs and compatible resumability checks. No cluster access
by the assistant. No GPU run, embedding generation, or matching has occurred yet.

## Comparison remains independent of observed balance

Primary next method is direct matching by CLMBR vector similarity/distance,
not adding CLMBR to a propensity model. Specify matching ratio, replacement,
ordering/ties, normalization and support rules before examining balance results.
Do not tune PSM or CLMBR to remove residual EF/AF imbalance or recover trial effects.
Preserve both clinical PSM versions and disclose the prior refinement history.
Use fixed clinical/missingness evaluation variables and common pre-match SMD
scales, and report balance together with retention. Any method may perform worse.


## MEDS bridge clarified — 2026-09-23

The intended route is OMOP gold -> versioned MEDS events -> tokenizer/processor ->
frozen CLMBR-T embeddings. MEDS is an event serialization layer, not another
clinical label mapping or the MICE-imputed patient table. Preserve observed
measurements/units in the conversion; explicitly verify how this checkpoint
consumes numeric values instead of silently discarding them. Do not fabricate
longitudinal events from imputed baseline covariates.

Archive reference points to /mnt/raid0/rbc58/mosaic/meds_extract_rbc_v2 as a
possible existing remapped-gold MEDS extract. Its current existence, lineage,
COMET subject coverage and timestamps are unverified. Historical builders were
cohort-scoped, so an existing directory may omit COMET patients. Reuse requires
compatible lineage, event domains, vocabulary, coverage and cutoff handling;
otherwise build a new COMET-cohort MEDS extract directly from existing gold.
Do not rerun the old archive builder or remake OMOP.

Core event fields are subject_id, time and code, with numeric_value for numeric
measurements; pin the MEDS version compatible with the selected FEMR runtime and
validate complete dataset metadata/sharding, not merely these column names.
Clinical events with missing time cannot bypass the pre-index filter. Declared
static demographic handling is separate. Model vocabulary acceptance still needs
checking even if the MEDS schema is valid.

References: https://huggingface.co/StanfordShahLab/clmbr-t-base and
https://github.com/Medical-Event-Data-Standard/meds (reviewed 2026-09-23).
