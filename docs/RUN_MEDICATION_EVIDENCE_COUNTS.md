# Count medication evidence before claiming verified fills

## Verification gate

A completed outpatient fill needs source documentation establishing a pharmacy
dispensing event (rather than a prescription, authorization, reconciliation or
hospital administration), a valid dispensing timestamp, patient/drug identity,
and a defensible transaction deduplication and cancellation/reversal policy. Check
whether fulfillment/pickup is distinguishable from preparation or claim submission.
Days supply is additionally needed for supply-based coverage; its presence alone
does not establish dispensing. Even verified dispensing does not prove ingestion.

OMOP distinguishes prescriptions written, dispensed and administered through record
provenance; its `refills` field represents intended refills on prescriptions, not
completed dispensing events. Quantity and days supply can originate from either
prescribing or dispensing. See [CDM documentation](https://ohdsi.github.io/CommonDataModel/cdm54.html).
The local RBC transformation does not implement a verified source-specific drug-type
classification; do not apply a generic OMOP dispensing filter to it uncritically.

First obtain the dictionary and actual raw schema, then trace source events and
their status history on H100. A pharmacist/source analyst should review a restricted
sample there, including ambiguous, reversed and hospital-source cases. Do not return
examples, identifiers or dates. Return reviewed aggregate validation results only.

## What this new audit can count now

### Combined quality audit (version 4)

Use `--detail-audit` to add the next checks in the same scan. No dependencies beyond
standard Python are required. It keeps the version 3 literal-tab contract explicit.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
MED_QUALITY_OUT=$(mktemp -d "/mnt/raid0/rbc58/ecg-tte/audits/medication-quality-XXXXXXXX")
python scripts/count_medication_evidence.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Meds.txt \
  --output-dir "$MED_QUALITY_OUT/report" \
  --record-format literal-tabs \
  --expected-schema-sha256 61f9556c4f054c3346d46f78e63d65a467e022f800fb0b388e5dbcf622903da8 \
  --detail-audit --full-scan
cat "$MED_QUALITY_OUT/report/summary.json"
```

New `quality_audit` summary includes:

- Separate blank and case-insensitive candidate markers NULL, NONE, N/A, NA, NAN,
  NAT, UNKNOWN and backslash-N. These are profiling hypotheses, not frozen clinical
  missingness definitions. The earlier raw-key denominator remains unchanged;
  separate quality counts flag marker/quoted identifiers for review.
- Calendar parsing under explicit ISO and month-first slash-date hypotheses for
  order/start/end/discontinuation fields. Unsupported formats and invalid dates
  remain explicit; no dates/examples, ranges or patient histories are exported.
  Parsing establishes neither clinically plausible time nor information availability.
- Quantity and refill numeric categories: blank/marker, zero, positive, negative,
  noninteger refill values, or unrecognized notation. No supply is inferred from
  quantity, dose, frequency or end dates.
- Distinct nonmarker order keys, repeated keys, excess rows per key, changed audit
  projections, and keys associated with multiple nonmarker patient keys. Fingerprints
  use only the listed audit fields, including medication ID/dose/route where present,
  not all source columns. Different fingerprints may be updates, not errors. Equal
  fingerprints are not proof of identical full records. No deduplication is applied.

The separate restricted report now cross-tabulates available ORDERING_MODE,
ORDER_MODE, ORDER_SOURCE, ORDER_CLASS, ORDER_STATUS, DISPENSED_UNIT, REORDERED_YN and
MODIFIED_YN, with records and distinct raw patient keys per combination. The 1,000
combination limit and omitted records are explicit; patients overlap across groups.
Mode/source labels are not interpreted as validated setting. Review this file on
the cluster and share only approved labels/counts. Do not paste it wholesale.

This full scan does more work and uses more cluster-local scratch space than the
previous count: temporary SQLite storage now also tracks order keys. Source files
remain unchanged; no GPU or cluster network access is used by the script. Temporary
storage is restricted and removed on handled completion/failure; interruption may
leave it behind. A failed scan exports no partial quality statistics or denominator.
The quality audit does not establish valid fills, an exposure index, cohort
eligibility or patient-level adherence. No clinical rule is frozen by its output.

`scripts/count_medication_evidence.py` reads one explicit raw JDAT text file without
changing it. Standard-library Python only; no GPU or third-party packages needed.
It reports:

- Total parsed records and distinct nonempty patient keys within that source.
- Missing patient keys and candidate field availability/nonempty counts.
- Distinct patient keys with any candidate fill-date or supply field populated.
  These are field-presence counts only, not valid-date/supply or verified-fill counts.
- Order class × order status record and distinct-patient counts in a separate
  restricted report. These categories do not themselves establish exposure type.

The audited candidate names are explicit in the script. Absence of those names does
not rule out differently named equivalents. No clinical source classifier, drug-arm
filter, washout, event deduplication, adherence calculation or eligible cohort is
implemented. Thus verified outpatient-fill N and eligible-initiator N are always
`null` with a structured reason. They are never falsely reported as zero.

Counts are across all drugs in the selected file. Keys are trimmed only; identity
linkage and literal null markers remain unvalidated. A row containing `NULL` is a
nonempty value under this audit. Distinct keys are a preliminary patient-count
measure, not a validated cohort denominator. Source files and category groups may
overlap in patients; never add their distinct counts together.

## Ryan runs on H100

After obtaining the local code changes, run from the cluster checkout. The source
is the 2026 RBC implementation medication-list file from reviewed lineage. A missing
file fails rather than substituting another cohort. Keep report and scratch storage
under `/mnt/raid0/rbc58/ecg-tte/audits` on the cluster, outside the source dataset.

```bash
cd "$HOME/github/ecg-tte"
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
MED_COUNT_OUT=$(mktemp -d "/mnt/raid0/rbc58/ecg-tte/audits/medication-evidence-counts-XXXXXXXX")
python scripts/count_medication_evidence.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Meds.txt \
  --output-dir "$MED_COUNT_OUT/report" \
  --full-scan
```

This full-file scan is needed for source-level N and may take substantial CPU/I/O
time and local scratch space. Progress contains record counts only. For a smoke
check, replace `--full-scan` with `--max-rows 100000` in a fresh output directory;
that yields prefix counts, never population N. No broad file discovery or source
union occurs. Use separate runs for selected administration sources only if needed;
their counts remain separate source denominators, not outpatient fill denominators.

Review `summary.json` and `restricted_categories.json` on the cluster. Return only
the reviewed summary and approved aggregate category counts, applying the project's
aggregate-release rules; do not paste the restricted report wholesale. Temporary
SQLite storage contains patient keys with restrictive directory permissions and is
removed on normal completion or handled failure. An interrupted process can leave
restricted scratch files: keep them on the cluster and remove them there when no
process is using them. A remaining `running` report is not a completed audit.

Malformed records stop the run and invalidate counts rather than skipping rows.
Version 2 sets an explicit 1 MiB character limit per CSV field and a separate
1 MiB byte limit per logical record, avoiding Python's smaller implicit field limit.
Strict quote parsing is unchanged. Reports include parser settings and safe failure
codes, the failing processing stage, and diagnostic records processed; progress is
not a usable cohort count. No exception message or source text is exported.
Do not change quoting or skip malformed rows to force completion. Optional
`--max-field-chars` and `--max-record-bytes` are bounded at 16 MiB, with field limit
no greater than record limit; change only after reviewing the reported reason.
Source-change detection checks size/mtime before and after the record scan. A prefix
that exactly reaches its cap is conservatively labeled bounded, even if EOF might
immediately follow. Category catalog limits disclose omitted records; overall
distinct counts are not capped. The raw parser necessarily reads each selected row
but only retains the specified fields; free text and record examples are not emitted.

## Next N after source validation

### If strict parsing fails

The version 2 H100 run stopped with `csv_parse_error` after 413,839 records;
the field-size hypothesis was not confirmed. No valid N resulted. Run the structural
diagnostic below instead of repeating the full count or changing quote handling.
It performs two bounded passes (at most 500,000 logical records for strict parsing,
and 500,000 physical lines for literal-delimiter width checks). No database of
patient keys is built, and no source values or exception messages are exported.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
MED_FORMAT_OUT=$(mktemp -d "/mnt/raid0/rbc58/ecg-tte/audits/medication-format-XXXXXXXX")
python scripts/diagnose_medication_format.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Meds.txt \
  --output-dir "$MED_FORMAT_OUT/report" \
  --max-records 500000
cat "$MED_FORMAT_OUT/report/summary.json"
```

`diagnostic_complete` means the format check finished, not that parsing succeeded
or a parser is approved. Review both pass statuses, limits and reasons. Stable
physical-line widths may support a literal-quote hypothesis but cannot prove source
semantics or validate the entire file. Legitimate quoted multiline fields or tabs
inside fields can also produce width differences. Resolve the extraction format
before changing the counting parser. No rows are skipped, repaired or used to build
a replacement denominator by this diagnostic.

### Trial-specific denominator sequence

### Reviewed quote conflict and provisional literal-tab scan

The subsequent diagnostic reproduced an unexpected character after closing quote
at 413,839 parsed records (413,840 physical lines consumed). All 500,000 inspected
physical lines had the expected 42 columns; 2,337 contained quotes, only one had
a quote at field start, and no source change was detected. This supports testing
literal quotes in a tab-separated extract; it does not prove full-file validity
or the source's documented quoting convention.

Version 3 supports an explicit `literal-tabs` reconnaissance mode, pinned to the
reviewed header schema. It treats each physical line as one record, splits tabs,
preserves quotes and empty trailing fields, and invalidates all counts at any width
mismatch. Strict CSV remains the default. No rows are skipped or combined, and
clinical exposure definitions are unchanged. Results remain provisional raw-key
counts pending extract-format and identity review. Quoted patient keys are counted
separately as a warning metric; quotes are never silently stripped to merge keys.

Run this in a fresh directory to assess full-file structure and preliminary N:

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
MED_COUNT_OUT=$(mktemp -d "/mnt/raid0/rbc58/ecg-tte/audits/medication-literal-counts-XXXXXXXX")
python scripts/count_medication_evidence.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --file CarDS_2435227_Meds.txt \
  --output-dir "$MED_COUNT_OUT/report" \
  --record-format literal-tabs \
  --expected-schema-sha256 61f9556c4f054c3346d46f78e63d65a467e022f800fb0b388e5dbcf622903da8 \
  --full-scan
cat "$MED_COUNT_OUT/report/summary.json"
```

Even successful structural checks do not certify that every tab/newline is a true
delimiter or that patient keys require no normalization. Confirm the extraction
specification before freezing an ingestion contract. Verified-fill N remains not
assessable until dispensing semantics are validated.

### Trial-specific denominator sequence (after source validation)

For each prespecified treatment/comparator arm, report sequentially:

1. Patients with candidate medication evidence and classifiable care setting.
2. Patients with verified outpatient dispensing after deduplication/reversal handling.
3. Patients with valid dispensing dates and supply information, separately.
4. Eligible new initiators with the required captured pre-index history.
5. Descriptive repeat-fill counts over prespecified windows, with observation
   coverage and early death/loss to follow-up accounted for; no future-fill filter
   on the primary cohort.

Steps 2–5 require verified source semantics and a trial contract and are not outputs
of this preliminary audit. If verified dispensing is unsupported, report that
limitation and separately assess prescribing-based feasibility.
