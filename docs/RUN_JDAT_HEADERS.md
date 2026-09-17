# Inspect candidate JDAT headers on the H100

Ryan runs this locally on the H100. No assistant SSH or patient-data transfer.
Python 3.9+ and the standard library are sufficient; no GPU or pandas is needed.

From the cluster repository checkout:

```bash
git pull --ff-only origin psm-mice-imputation

umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte-audits
JDAT_HEADERS="/mnt/raid0/rbc58/ecg-tte-audits/jdat-headers-$(date +%Y%m%d-%H%M%S)"
python scripts/inspect_jdat_headers.py \
  --root /home/rbc58/mnt/t2dm-jdat-data \
  --preset t2dm \
  --output-dir "$JDAT_HEADERS"

less "$JDAT_HEADERS/headers.md"
```

The preset explicitly selects 38 `.txt` candidates from the user-provided excerpt:
patient/history/diagnosis tables, medication tables, outpatient encounters and
procedures/vitals, hospital/outpatient lab shards and their copy/date variants,
plus the nested 2024 delivery's lab and medication-administration shards.
It does not recursively scan directories or read every file in the inventory.
No `.partial` companions or operational logs are included.

For other tables, use explicit relative filenames instead of the preset:

```bash
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte-audits
python scripts/inspect_jdat_headers.py \
  --root /home/rbc58/mnt/t2dm-jdat-data \
  --file 2380791_CarDS_Outcomes_DM2_Meds.txt \
  --file 2380791_CarDS_Outcomes_DM2_Patients.txt \
  --output-dir "/mnt/raid0/rbc58/ecg-tte-audits/jdat-selected-headers-$(date +%Y%m%d-%H%M%S)"
```

## What it does

- Requests only the first physical line with unbuffered binary reading, capped
  at 64 KiB plus one sentinel byte. It never proceeds to a second line. If a file
  is headerless, its first line is still inspected internally but must pass
  conservative header checks before any column candidates are reported.
- Strictly decodes UTF-8 with optional BOM. There is no silent encoding fallback.
  Use `--encoding latin-1` only when supported by source evidence.
- Detects tab, pipe, or comma delimiters using the candidate header only. Use
  `--delimiter tab`, `pipe`, or `comma` to specify a known delimiter.
- Requires at least two unique identifier-like column names and a recognized
  patient/encounter identifier column. Unexpected, multiline, binary, oversized,
  duplicate-column, or unrecognized headers are rejected without raw text output.
  A rejection is a review item, not evidence that the source itself is invalid.
- Records header columns, delimiter, encoding policy, bytes read, file size,
  and an ordered-column schema hash. The hash does not validate row equivalence,
  duplicate deliveries, file completeness, or clinical meanings.
- Refuses partial files, non-`.txt` formats, relative-path escapes, descendant
  symlinks, existing output directories, and output overlapping the source tree.
- Shows file ordinal and status on the console, never filenames, column names,
  raw lines, or raw filesystem exception messages. On a slow mount, a filesystem
  operation may still block; the last ordinal identifies the preset entry.

## Reports and review

`headers.md` contains the readable column lists. `summary.json` records per-file
status/results and is updated after each file. Both stay on the cluster until
reviewed: even a header candidate or filename can contain unexpected sensitive text.
Share only reviewed table names and column lists, never patient rows.

Exit `0` means every selected file produced a header candidate. Exit `2` means
some were missing/rejected or setup failed; review the available results rather
than assuming the whole report is unusable. A killed/interrupted run is not complete.
Use a fresh output directory for reruns. No source files are changed.

Matching headers across versions can identify schema differences, but choosing
an authoritative delivery still requires manifests/source documentation and later
restricted validation. This step does not establish column types, value ranges,
row counts, record overlap, or medication/timestamp semantics.

Verification: eight new synthetic header tests and seven existing inventory tests
passed locally. Real JDAT execution remains Ryan's next step.

## Optional saved-inventory path resolution

If files are nested beneath the original root, supply `--inventory-dir` with the
completed inventory directory and `--inventory-source t2dm` instead of `--root`.
The scanner uses exact recorded paths, or a unique basename match. Ambiguous
basenames are reported without selecting a delivery. An explicit `--root` may
override the recorded mount root. Five additional synthetic tests cover this mode
and distinguish missing roots, missing files and nonregular paths.
