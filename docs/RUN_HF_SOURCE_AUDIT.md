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
  --dx-max-rows 500000
cat "$HF_SOURCE_OUT/report/summary.json"
```

The medication scan is full-file to recreate each of the four lexical arm's earliest
dated outpatient Normal/Print orders. Echo is full-file; each diagnosis file is
limited to 500,000 rows initially. `complete_requested_scope` does NOT mean full
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
