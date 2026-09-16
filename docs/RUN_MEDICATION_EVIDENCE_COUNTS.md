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
in your home on the cluster, outside the source dataset.

```bash
cd "$HOME/github/ecg-tte"
MED_COUNT_OUT=$(mktemp -d "$HOME/medication-evidence-counts-XXXXXXXX")
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
