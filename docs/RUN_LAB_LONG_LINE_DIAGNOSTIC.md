# Diagnose the PSM lab record-size failure

Ryan's extension snapshot `psm-sources-v1-0815146D/snapshot` failed after
8,420.996 seconds at `Data_2025_04_03_hosp_enc_labs_3` with `line_exceeds_limit`.
Six stages completed: demographics, hospital/outpatient encounters, outpatient
vitals, and hospital lab shards 1 and 2. The completed stages remain on disk;
the incomplete lab shard must not be used. Overall snapshot remains incomplete.

The builder reads physical lines with a 1 MiB limit. This error establishes only
that a physical record exceeded that cap, not its actual length or whether its
51 fields are intact. Large narrative fields are a possibility, not a diagnosis.
Do not truncate, skip the record, edit raw data or simply retry the same command.
Do not delete the existing snapshot or rebuild completed stages into a new one.

Run this byte-structure scan of the failing source only. It uses fixed-size chunks
and does not retain whole long records. All outputs are structural aggregates:
widths, sizes, record ordinals, null-byte flags and terminal-line metadata. Source
values are never printed. UTF-8 correctness and clinical semantics are not checked.
It scans the entire ~66 GB source once; runtime is not measured. The core-snapshot
COMET candidate job is independent of this failed extension.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
LAB_FORMAT_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/lab-long-lines-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/diagnose_long_source_lines.py \
  --source /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/Data-2025-04-03/CarDS_2435227_Hosp_Enc_Labs_3.txt \
  --expected-schema-sha256 cdb32a17c00ec93b8d6b7a9d294c3c249c7c8274f6340381c020153763ed85ab \
  --output-dir "$LAB_FORMAT_RUN/report"
cat "$LAB_FORMAT_RUN/report/summary.json"
```

The diagnostic does not change the builder or its implementation-hash dependencies.
Return the reviewed summary. Once the maximum length and widths are known, define
an explicit bounded parser contract and integrity-checked recovery path. A change
to builder code makes its old resume contract incompatible unless that migration
is explicitly implemented; do not promise an unchanged --resume will fix this.
The existing completed stage manifests/hashes are the evidence needed for reuse.
