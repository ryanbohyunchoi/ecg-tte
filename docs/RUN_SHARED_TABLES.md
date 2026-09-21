# Build reusable source tables on H100

The first shared snapshot covers all rows of the four verified medication, hospital
DX, outpatient DX and echo sources. It is a trial-independent **source staging
layer**, not a validated clinical event model or a COMET cohort. Labs, vitals,
encounters, demographics and mortality are not yet converted. No archived code is
imported. Existing OMOP and all source files remain untouched.

Requires Python and PyArrow. PyArrow already worked in Ryan's H100 echo audits.
No GPU, database server or new cluster package installation is required. Local
integration tests used Python 3.10 and PyArrow 23.0.1. Each build records the actual
runtime versions; resume requires matching versions and implementation hash.

## First build

This intentionally scans the sources once and writes a new snapshot. Budget time
and storage for raw reading, date parsing, compressed Parquet output and integrity
hashes. No measured H100 runtime or final compressed size is available. Check free
space first; do not overwrite or remove old audit outputs to make room automatically.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/shared
SHARED_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/shared/source-v1-XXXXXXXX)
echo "Build directory: $SHARED_RUN/snapshot"
df -h /mnt/raid0/rbc58/ecg-tte/shared
PYTHONDONTWRITEBYTECODE=1 python scripts/build_shared_tables.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --echo /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \
  --output-dir "$SHARED_RUN/snapshot"
cat "$SHARED_RUN/snapshot/summary.json"
```

The CLI pins the reviewed ordered schemas and expected row counts for this exact
source delivery. Future deliveries require a new reviewed contract, not a silent
replacement. Expected data rows: medication_orders 30,929,792; hospital_diagnoses
42,763,152; outpatient_diagnoses 9,633,590; echo_studies 661,062. Both DX sources
permit one explicitly counted zero-payload LF/CRLF final line; no other row skips.

Only reviewed aggregate summary.json should be shared. Parquet files, manifests
and any source values stay on H100. Full manifests contain paths and schema details
and should remain restricted unless individually reviewed.

## Output layout

```
snapshot/
  manifest.json                # global status, exact contract and stage manifests
  summary.json                 # aggregate counts, timing and QC
  medication_orders/
    manifest.json
    part-00000.parquet ...
  hospital_diagnoses/ ...
  outpatient_diagnoses/ ...
  echo_studies/ ...
```

All original source columns are retained. Text-source columns remain strings,
including spaces, identifiers, literal null markers, code lists and free text.
Line endings delimit records; the original source bytes remain authoritative.
Echo columns retain their Arrow types and values; Parquet container metadata is
not copied as a claim of clinical provenance. No patient filter, HF filter,
medication selection, deduplication, clipping or imputation is performed.

Added fields:

- `__source_id`, `__source_row`: source identity and one-based data-row ordinal.
  Together with the snapshot/source hash they form a lineage key, not a global
  clinical event identifier. Terminal blanks do not increment the data ordinal.
- `__patient_key`: trimmed source MRN, retaining prefixes and zeros; candidate null
  markers become null in this helper only. `__patient_key_status` labels the rule.
  Original identifiers remain intact. This does not establish cross-source identity.
- `__day_<field>` and `__date_status_<field>`: typed calendar date plus format/quality
  status for selected clinical date fields. Ambiguous/offset-bearing formats are
  not compared; original date/time strings remain. These helpers are NOT event
  availability timestamps and cannot establish within-day pre-index ordering.

Code sets, true dispensing semantics, diagnosis-date lineage, echo EF units,
patient reconciliation and clinical eligibility are still unresolved. A complete
snapshot certifies ingestion accounting/integrity under the provisional parser,
not those clinical facts. Omitted source domains must stop mandatory downstream
requirements; their absence is not zero comorbidity or a normal lab.

## Restart after interruption or failure

Use the SAME output directory with `--resume`, and the SAME code/runtime/source
contract. Do not git-pull a new implementation in the middle of a build and expect
it to resume. Example while SHARED_RUN is still set correctly:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/build_shared_tables.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --echo /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \
  --output-dir "$SHARED_RUN/snapshot" \
  --resume
```

If the shell variable is lost, set SHARED_RUN to the exact printed run directory
before issuing that command; do not guess from whichever directory is newest.

Each stage is published by an atomic directory rename only after row accounting,
source stability, footer checks and hashes pass. A completed stage survives later
failures. Resume verifies source SHA-256, source metadata, output hashes, schemas
and counts before reuse. This still reads bytes for hashing but avoids reparsing
and rewriting verified stages. A failed/incomplete stage is preserved under an
`.incomplete-*` name and rebuilt; partial-shard resume is not implemented. Concurrent
builds into the same directory are refused using an OS file lock. Killed jobs
release the lock automatically. Do not delete source files or partial artifacts
while any build is running.

## Reuse in later trial tools

Import `open_table` from scripts/build_shared_tables.py. It refuses a globally
incomplete snapshot, validates stage manifests and Parquet footers, and reads only
requested columns. `verify_hashes=True` additionally hashes all parts; normal
queries avoid that extra full read. Complete snapshots must remain immutable.

Example inside a cluster-side analysis script:

```python
from build_shared_tables import open_table
import pyarrow.dataset as ds

meds = open_table(snapshot_path, 'medication_orders')
# Process batches; do not print patient data or collect the full dataset in RAM.
for batch in meds.scanner(
    columns=['__patient_key', 'ORDER_MED_ID', 'MEDICATION_NAME',
             '__day_ORDER_INST', '__source_row'],
    filter=ds.field('__day_ORDER_INST').is_valid(),
    batch_size=65536,
).to_batches():
    pass  # trial-specific extraction, with its own frozen rules and manifest
```

The existing raw audit scripts have NOT been silently redirected to these tables.
New/updated trial tools must explicitly consume the snapshot and document their
column/date semantics. Projection and parsed typed columns should reduce repeat
work, but no end-to-end speedup is claimed before an H100 comparison. Filtering on
EF or medications is downstream and does not remove other trials' source rows.

Local verification: real synthetic Parquet integration tests cover raw-value
preservation, typed dates, terminal blanks, failures, hashes, same-stat source
changes, incompatible resumes, completed-stage reuse, output boundaries and
manifest-reader rejection of partial snapshots.
