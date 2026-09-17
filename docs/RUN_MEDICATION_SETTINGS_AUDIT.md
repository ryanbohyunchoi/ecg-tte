# Check medication setting and evidence fields

Ryan runs this on the H100; no assistant cluster access. This reads the first
100,000 rows of each of at most 40 flat parquet files in the medication directory,
projecting only allowlisted setting/status/source and presence-check columns.
It does not read identifiers, notes, medication names or entire patient histories.
No GPU is used. Existing data remain unchanged; outputs must be a fresh directory
outside the source tree. Use an existing environment with `pyarrow` installed.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation

umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
MED_SETTING_OUT="/mnt/raid0/rbc58/ecg-tte/audits/medication-settings-$(date +%Y%m%d-%H%M%S)"
python scripts/audit_medication_settings.py \
  --root "$HOME/mnt/ecg-tte/drugs" \
  --output-dir "$MED_SETTING_OUT"

cat "$MED_SETTING_OUT/summary.json"
cursor "$MED_SETTING_OUT/restricted_values.json"
```

The root is based on the previously reviewed discovery, which found
`home_meds_cmp.parquet`, `inpatient_cmp_1.parquet` and
`outpatient_admin_cmp.parquet`. The audit includes any other direct parquet files
present there and reports file limits; it does not recurse or follow file symlinks.

Expect a lightweight first pass compared with a full scan, but shared-mount I/O
can block. Progress prints once per file; `summary.json` updates after each file.
A killed process can leave status `running`. Check exit status/report for failed
files. `inspection_complete` means the bounded audit finished, not that all rows
were read or clinical semantics validated. `row_limit_reached` and
`file_limit_reached` disclose truncation. Prefixes are not random samples and must
not be used as population prevalence estimates. Counts are records, not patients.

## Reports and interpretation

- `summary.json`: file metadata, fields present/absent, sampled null/blank/value
  counts, category/cross-tab truncation and failures. No raw category or date values.
  Review paths/metadata before sharing.
- `restricted_values.json`: actual setting, order-class/status, source and selected
  coded-type/action categories, plus setting × class × status × source-file counts.
  Keep this on the cluster. Fields may contain unexpected sensitive strings even
  though identifiers/notes are excluded. Review locally and return only approved
  category labels and aggregate counts; do not paste this file wholesale.

Null and whitespace-only strings are counted separately. Literal strings such as
`NULL`, `unknown` or `N/A` remain values pending semantic review. Category catalogs
retain at most 1,000 distinct entries per field/cross-tab per file; uncatalogued
record counts are explicit, so these are not guaranteed global top categories.

The report checks candidate supply/fill/date/quantity fields for presence and
nonempty cells without exporting their values. A present fill-date column is not
proof of a pharmacy dispense, and a refill field may mean authorized repeats.
No evidence-type classifier is applied yet. Source filename and setting labels
must be reconciled with the transformation code and data dictionary.

## What to review next

1. Which setting and order-class/status labels actually occur, and which are missing?
2. Do source labels agree with settings, or are home medication histories mixed
   with prescriptions/administrations?
3. Are fill/dispensing dates and days supply present and populated? What do they mean?
4. Are encounter/action fields available to verify inpatient versus outpatient
   evidence? Do not infer visit linkage just from date overlap.

Return the reviewed summary and a short description of approved category labels.
Then define the setting/evidence mapping and a second, trial-specific audit of
unique patients, deduplication, linkage and longitudinal persistence. Those are
not implemented here: no drug/comparator or verified fill contract is frozen.
Do not sum counts across overlapping source products as independent events.
