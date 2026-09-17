# JDAT mapping reconnaissance on the H100

This is the first record-level readiness check, not an OMOP converter or CLMBR-T
validator. Ryan runs it on the cluster; no assistant cluster access. Standard-library
Python 3.9+ is sufficient. No GPU, model download, or new dependency is needed.

## Run

Use the `summary.json` from the successful header inspection. Replace the example
path below with that actual directory. File indices are the 1-based positions in
that report, not identifiers guessed from filenames. Confirm them in `headers.md`.
For the supplied 38-file report, these select inclusion diagnoses (2), medication
orders (5), encounters (6), CPT procedures (7), vitals (9), outpatient administration
(10), and the first hospital laboratory shard (13):

```bash
git switch psm-mice-imputation
git pull --ff-only origin psm-mice-imputation

JDAT_HEADER_REPORT="/mnt/raid0/rbc58/ecg-tte-audits/jdat-headers-REPLACE_WITH_ACTUAL_TIMESTAMP/summary.json"
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte-audits
JDAT_MAPPING_OUT="/mnt/raid0/rbc58/ecg-tte-audits/jdat-mapping-$(date +%Y%m%d-%H%M%S)"
python scripts/profile_jdat_mapping.py \
  --headers "$JDAT_HEADER_REPORT" \
  --file-index 2 --file-index 5 --file-index 6 --file-index 7 \
  --file-index 9 --file-index 10 --file-index 13 \
  --max-rows 100000 \
  --output-dir "$JDAT_MAPPING_OUT"
```

The source root, exact relative paths, delimiter and encoding come from the header
report. No recursive search or automatic version selection occurs. Files remain
separate; selecting a file does not designate it as the authoritative delivery.
Start with this bounded pass before attempting whole-file profiling. A prefix is
not a random or representative sample and cannot estimate cohort-wide coverage.
Progress prints every 10,000 accepted records and on file completion. Shared mount
latency can still block a filesystem call. A killed run remains incomplete; rerun
in a fresh directory. No source data are changed.

## Outputs: both remain restricted on the cluster

- `summary.json`: per-field empty/nonempty counts, distinct raw code-cell counts,
  per-file row accounting and status, limits, source size/mtime and schema/report
  hashes. No raw source values, dates or identifiers are included. Review even
  aggregates and paths before sharing; this is not an automatic deidentification
  or small-cell suppression system.
- `restricted_code_counts.sqlite`: exact values and frequencies for an explicit
  allowlist of code-bearing fields. **Do not upload, commit or paste this database.**
  Unexpected PHI can occur even in a nominal code column. Patient identifiers,
  timestamps, notes, values, medication names and other free text are not cataloged.

Empty means blank/whitespace only. Literal `NULL`, `NA`, sentinel dates and invalid
values remain nonempty until source rules are established. Dates are assessed for
presence only. ICD list fields remain opaque cells: their delimiter/meaning is not
assumed. Distinct raw cells are not counts of mapped concepts or patients.

The parser supports quoted multiline records but stops on row-width, decoding,
quoting, NUL-byte or record-size failures. Default record bound is 1 MiB; code cells
are capped at 4,096 characters. No raw error text is emitted. Failed-file catalog
entries and field counts are discarded, rather than silently skipping bad rows.
A failure may indicate an incorrect CSV dialect assumption, not corrupt JDAT data.

`complete_file` means EOF was encountered; `bounded_prefix` means the row cap was
reached without testing an additional row. `audit_complete` means selected scans
finished, not that source coverage, mappings or clinical semantics are validated.
Exit 2 means failure. A report still marked `running` is incomplete. Source size and
mtime changes are checked, but are not a cryptographic verification of all file bytes.

## Evidence needed before the next adapter

1. Review this first report for parse success, field availability and code cardinality.
2. Locate JDAT/Epic dictionaries or validated institutional crosswalks for
   `MEDICATION_ID`, `COMPONENT_ID`, and `FLO_MEAS_ID`, plus visit/action/status codes.
   Establish lab units and vocabulary versions. Dictionary inspection stays local
   to the cluster; return only reviewed schemas and aggregate findings.
3. Freeze source code normalization and code-system rules, list expansion,
   standard concept crosswalk versions and handling of ambiguous/missing mappings.
   Do not infer mappings from numeric local IDs or silently match drug names.
4. Establish event and availability times, clinical record classes and source
   completeness. Neither populated date fields nor a visit table proves this.
5. Implement/test the standardized-event adapter and measure distinct-code and
   event-weighted mapping coverage. Separately audit the exact CLMBR-T tokenizer
   and checkpoint. Per-patient/year coverage and index-cutoff validation follow
   once identity and time semantics are settled.

The current profiler implements step 1 tooling only. It does not evaluate standard
mapping, numerical units, patient linkage, timestamps, pre-index eligibility,
model vocabulary coverage, treatment effects or clinical/statistical adequacy.
