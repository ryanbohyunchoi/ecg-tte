# HF source quality and exact-key coverage audit

Ryan runs this on H100. Source files are read only. Outputs and temporary SQLite
patient/date tables stay in a fresh private RAID directory. Requires PyArrow (the
schema check already succeeded with it on H100). No GPU is needed.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
HF_SOURCE_OUT=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/hf-source-audit-XXXXXXXX)
python scripts/audit_hf_sources.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2026-04-15 \
  --echo /mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet \
  --output-dir "$HF_SOURCE_OUT/report" \
  --dx-full-scan \
  --allow-hospital-terminal-empty-line \
  --allow-outpatient-terminal-empty-line
cat "$HF_SOURCE_OUT/report/summary.json"
```

The medication scan is full-file to recreate each of the four lexical arm's earliest
dated outpatient Normal/Print orders. Echo is full-file; each diagnosis file is
scanned to EOF with the command above. Use `--dx-max-rows 500000` instead for an explicitly bounded run. `complete_requested_scope` does NOT mean full
DX coverage. Per-file status and reached_eof distinguish prefix versus full reads.
Prefix overlaps are descriptive only, not representative HF prevalence estimates.

Reports include EF descriptive bands (not validated percentage units or eligibility
thresholds), date formats, masked echo-date shapes, repeated accession rows and
rows disagreeing with the first accession record. Only MRN, EchoDate, EF and
AccessionNumber are read from echo. Exact trimmed MRN overlap preserves letters
and leading zeros. Null markers are excluded. Successful equality does not prove
that patient namespaces/identities agree; unmatched records are not normalized.

Arm-level echo flags count distinct patient keys with any study before, on or after
the exploratory medication anchor. Flags overlap: a patient may have studies in
all three periods. The >1 to 100 range excludes obvious scale ambiguity but does
not validate clinical EF. These are not nearest-echo selections, EF-threshold
eligibility, HF counts or new users. EchoDate is not known report-availability time.
No dates or identifiers are exported. Source dictionaries and provenance remain
required before clinical interpretation; post-index and same-day echoes do not
qualify as verified baseline evidence.

DX code cells are classified by structure only (single code-shaped token,
delimiter presence, other); no codes/text are emitted, no lists are interpreted and
no HF phenotype is applied. All three diagnosis dates are compared separately.
DX overlap counts ignore diagnosis meaning/timing and are not pre-index HF counts.
Do not assign a preferred date from its name or treat CURRENT_ICD10_LIST as proof
of a historically available code. Malformed width, source changes and schema errors
invalidate counts, with no silent skipping. Literal-tabs remains a provisional
format hypothesis for each source.

Review summary.json on H100 and return only approved aggregates. Temporary SQLite
files normally disappear on exit; interrupted jobs can leave restricted scratch
files. No source data or outputs are written to the home directory.

Local validation: synthetic tests cover EF bands, exact keys, duplicate accession
conflicts, pre/same/post-day distinctions, ambiguous dates, row-width/schema and
source-change failures, privacy and output overlap. Local Python lacks PyArrow;
real Parquet I/O remains to be exercised on H100.

## Version 2: calendar coverage, recency and DX structure

The next run deliberately rescans medications/echo and now both complete DX files;
version 1 scratch keys were removed, so its aggregate report cannot answer these
new questions. All prior scope, format and clinical limitations still apply.

`calendar_and_recency` reports each arm's first candidate anchor counts by year,
plus distinct patient keys with any candidate order in each year. The latter
patients overlap across years; counts are not new initiators. First-anchor cohorts
can differ from treatment decisions in a chosen later common calendar window.
No contemporaneous window is selected automatically.

Within anchor year, mutually exclusive nearest-prior candidate-range EF recency
bins are 1–90, 91–180, 181–365, 366–730, >730 days and no prior candidate EF.
These are feasibility bands, not accepted baseline windows. A separate distribution
uses the latest prior echo day regardless of EF missingness. Different EF bands
on that same latest day are explicitly unresolved; agreement within one band does
not establish identical measurements. Neither same-day nor later echoes enter
these prior summaries. No last-valid-value fallback is adopted for eligibility.

DX tokenization tests a comma/semicolon/pipe split hypothesis and reports only
structure counts, including empty tokens and unresolved cells. Code-shaped tokens
are not validated ICD codes or HF diagnoses. CALC_DX_DATE-year strata show where
DX_DATE is usable; this cannot establish the derivation or availability time of
CALC_DX_DATE. No definition was found in the available local source code. A JDAT
source specification/extraction SQL is needed before choosing any date fallback.

Sixteen HF synthetic tests pass after version 2 additions, including exact recency
boundaries, latest-day band disagreements and preservation of missing latest EF.
H100 exercised real Parquet reading in version 1; version 2 awaits a cluster run.

## Version 3: observed terminal empty line

Ryan's full hospital DX diagnostic found exactly one short physical line, at EOF,
following 42,763,152 lines of width 17. A bounded byte-level tail check confirmed
zero payload bytes, not whitespace or nonblank content. The explicit
`--allow-hospital-terminal-empty-line` option accepts one empty LF/CRLF physical
line only at EOF of hospital DX. It counts that line separately from data rows;
interior/multiple blanks, whitespace, BOM payloads and other malformed widths
still fail. The medication and outpatient DX parsers retain their existing rules.
Source bytes are never modified. The summary is now version 3 and exposes
physical_lines_read, rows_read, terminal_empty_lines_accepted and the per-file
policy. A bounded scan stopping before EOF cannot claim the terminal line accepted.

Eighteen HF synthetic tests pass. Rerun in a fresh directory with the flag above;
there is no recoverable patient-level cache from the failed version 2 run.

## Version 4: outpatient terminal empty line confirmed

The full outpatient structural diagnostic confirms 9,633,590 width-17 data lines
plus exactly one zero-payload empty final line, with EOF and unchanged source.
Use both explicit flags in the current command. Each file's option applies only
to that named DX source; medication parsing is unchanged. Expect one separately
counted terminal empty line per DX file and no change to source bytes. Default
behavior remains strict rejection. Nineteen HF synthetic tests pass, including
independent source-specific policy controls. Full version 4 results remain pending.
