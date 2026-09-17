# First H100 run: JDAT filenames only

Ryan runs this script on the H100. The assistant does not connect to the cluster.
This is a file inventory, not a schema profiler or clinical-data analysis.

## Run

After transferring the current code to your cluster checkout, run from its root:

```bash
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte-audits
python scripts/inventory_jdat.py \
  --root t2dm=/home/rbc58/mnt/t2dm-jdat-data \
  --root cmp=/home/rbc58/mnt/cmp-jdat-data \
  --root implementation=/home/rbc58/mnt/implementation \
  --root ascvd=/home/rbc58/mnt/ascvd \
  --output-dir "/mnt/raid0/rbc58/ecg-tte-audits/jdat-inventory-$(date +%Y%m%d-%H%M%S)"
```

These four locations are **unverified leads from the old project**, not confirmed
source roots. Replace paths as needed, or repeat `--root LABEL=/absolute/path` for
additional directories. Missing roots are reported while other roots are still
scanned. Roots must not overlap; do not provide both a parent and its subdirectory.

Requires Python 3.9 or later; no additional packages, GPU, or network connection.
The script does not pull code, access S3, mount drives, or open source file contents.
It only enumerates directories and reads filesystem metadata. Mounts must already
be available to your cluster session. It lists all file extensions and hidden files
inside the supplied roots, so derived files may appear alongside raw deliveries.

## Review

The new output directory contains:

- `inventory.md`: full file list grouped by source root, with relative paths,
  byte sizes, filename-based domain hints, and missing/unreadable entries.
- `inventory.jsonl`: the same entries in a machine-readable form.
- `summary.json`: completion status, counts, total bytes, category counts, and
  resolved source roots.

Review `inventory.md` on the H100 first. Filenames can contain identifiers, so
these reports are restricted until you review them. Return only the non-identifying
extract/table filenames and summary sections you consider appropriate to share.
We can then identify likely demographics, diagnoses, encounters, medications,
labs, vitals, notes, mortality, and imaging metadata sources together.

Category labels are guesses from filenames. An `ECG` label could describe a
general extract with ECG in its name; it does not establish that the file contains
waveforms. `unclassified` is retained for manual review. Paths under familiar
derived directories are flagged but not omitted.

## Completeness and reruns

- Exit `0`: all supplied roots traversed without reported filesystem errors.
  An empty readable root can still complete; inspect its count.
- Exit `2`: invalid arguments/output, missing/unreadable root, or another reported
  filesystem error. An incomplete report may still contain useful file listings.
- Descendant symlinks are listed but never followed. An explicitly supplied root
  alias is resolved before scanning. Special files are listed without opening.
- Compressed files and archives are listed as files; members are not extracted.
- File contents, headers, record counts, clinical dates, and checksums of source
  files are not read. This is not an immutable snapshot of a changing filesystem;
  run against a stable delivery if available.
- Existing output directories are refused. Use a new output name for every run,
  including reruns after interruption. Check `summary.json`; `running`, `failed`,
  or `incomplete` is not a complete inventory.
- Output must be separate from all source trees. Reports are created in a private
  directory (mode `0700`, subject to filesystem support).

No complete cluster-wide discovery is claimed: the inventory covers only the roots
you supply. Other mounts/deliveries can be added after reviewing the first report.

## Local verification

```bash
python -m unittest discover -s tests -p 'test_inventory_jdat.py' -v
```

Seven synthetic tests verify metadata-only scanning, nested/hidden files,
symlink/special-file handling, missing/unreadable roots, overwrite/root-overlap
protection, and separation of detailed filenames from console output. No actual
JDAT sources have been inspected during development.
