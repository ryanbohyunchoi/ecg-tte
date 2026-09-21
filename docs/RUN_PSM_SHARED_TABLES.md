# Build the PSM source extensions on H100

This converts the 19 reviewed demographics, encounter, vital and lab files into
separate raw-preserving Parquet tables. The existing medication/DX/echo snapshot
is not an input and is not rewritten. Output stays under the RAID project root.
Requires Python 3.9+ and PyArrow; use the same environment as the successful core
build. No GPU or new package installation is needed.

## Run once in a new directory

Run inside your existing tmux session. The raw sources total approximately 245.83
GB, mostly labs. Full-build time and compressed size have not been measured. The
23-second prefix profile cannot predict the full conversion time. Check available
space; do not delete existing runs automatically to make room.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/shared
PSM_SHARED_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/shared/psm-sources-v1-XXXXXXXX)
echo "Extension directory: $PSM_SHARED_RUN/snapshot"
df -h /mnt/raid0/rbc58/ecg-tte/shared
PYTHONDONTWRITEBYTECODE=1 python scripts/build_psm_shared_tables.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG \
  --output-dir "$PSM_SHARED_RUN/snapshot" \
  --allow-terminal-empty-line
cat "$PSM_SHARED_RUN/snapshot/summary.json"
```

The explicit terminal-line flag permits at most one zero-payload LF/CRLF line at
verified EOF per file and counts it separately. This is a declared parser policy,
not a claim that these 19 files contain such lines. Interior or multiple blanks,
whitespace-only payloads, wrong widths, NUL bytes, invalid UTF-8 and lines over
1 MiB still fail. Omit the flag to use strict no-blank behavior. No rows are
repaired or silently skipped. Unknown full row counts are discovered at EOF;
physical lines must equal data rows plus separately counted terminal blanks.
This verifies ingestion accounting, not completeness of the upstream extract.
An empty source fails. All source schemas are checked before large scans start.

## Tables and interpretation

Each file has its own table directory, e.g.
`Data_2025_04_03_hosp_enc_labs_1`. Source specs record delivery, domain, original
relative path and `psm_raw_sources_v1` extension contract. Every row has source ID
and ordinal. 2025 and 2026 files/shards are not merged or deduplicated. The missing
2026 Patients file is not substituted silently: demographics is explicitly 2025.

All original columns remain strings, including identifiers, free text, literal
null markers, UNIT, ORD_VALUE and ORD_NUM_VALUE. No numeric sentinel is assumed
valid, no inequality is converted to an exact measurement, and no units are
inferred. Trimmed patient-key helpers and date-only parsing helpers follow the
core staging contract; original timestamps remain unchanged. Result/specimen
fields are retained separately. Calendar-day helpers do not establish clinical
availability or same-day pre-index ordering. Hospital-file provenance is not an
inpatient classification. No missing lab or missing unit is imputed.

Manifests include source/output hashes, schema, row counts, source stability and
date/key QC. Aggregate summary.json contains no source values. Keep Parquet and
manifests on H100; return only the reviewed summary. This extension does not yet
produce a COMET baseline feature matrix, MICE results or PSM estimates.

## Resume the same extension

Retain the exact printed directory, code version, Python/PyArrow environment and
parser options. Use the same command with `--resume` added; do not create another
PSM_SHARED_RUN first. Completed tables are hash-verified and reused. Hash checks
still read source bytes. Interrupted tables are retained and rebuilt; they are
not appended. Only one build may hold a snapshot lock. The reader rejects a
snapshot until all 19 stages complete.

This release extends the shared engine for unknown row counts and therefore
changes its implementation hash. Completed older core snapshots remain readable
and need no rebuilding; resuming an older interrupted build requires its original
code/runtime. Do not try to resume an old core snapshot with this release.

Downstream tools can use `build_shared_tables.open_table(snapshot, source_id)`
with projected columns and filters. Global manifest format remains
`shared_sources_v1`; each extension source spec carries its additional contract.
The next clinical step is component/unit mapping, delivery overlap review and
pre-index covariate coverage by arm, with a declared cohort/index contract.
