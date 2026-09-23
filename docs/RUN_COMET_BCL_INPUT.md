# Prepare private BCL ECG input

H100 user confirmed ECG metadata, waveform directory, upstream default BCL
checkpoint and sampling-format CSV exist. That verifies presence, not contents.
This stage constructs the cohort CSV; it does not load waveforms or the model.

Select the most recent ECG calendar day strictly1–365days before each existing
COMET index. On that day, resolve FileID/fileID against nonempty regular waveform
files. If both aliases in a row match distinct files, exclude with explicit reason.
Check selected-day IDs against all metadata for patient/date collisions. Among
multiple resolved ECGs on the same day choose lexical fileID. Do not fall back to
an older day after missing waveform or sampling metadata. Keep excluded patients
in the private linkage report; do not change the source cohort.

Sampling-format labels must be present and unambiguous for the chosen ID. The
upstream rule identifies250Hz via `5_0` substring. Requiring a known label is an
explicit stricter availability rule than upstream's implicit500Hz for unlisted IDs.
This stage does not prove sampling-label accuracy or canonical waveform lead order.

Only run after the prepared code is available on H100:

```bash
(
set -e
cd "$HOME/github/ecg-tte"
umask 077
BCL_INPUT=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-input-XXXXXXXX)
/home/rbc58/miniconda3/envs/mosaic/bin/python scripts/prepare_comet_bcl_input.py --relative-npy \
  --source-report /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-prep-M9F28Lk2/report \
  --metadata /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \
  --waveform-root /mnt/raid0/bb2238/signals/preprocessed/all_ecgs \
  --formats /mnt/nfs_yale_ecg/preprocessing/formats_rerun.csv \
  --output-dir "$BCL_INPUT/report"
cat "$BCL_INPUT/report/summary.json"
echo "Report directory: $BCL_INPUT/report"
)
```

Outputs: fileID-only `restricted_bcl_input.csv`, patient/date/index/reason
`restricted_ecg_linkage.csv`, source manifest and aggregate summary. All patient
artifacts remain on H100. This is not an inference launch or matching-ready
population. Review exclusions/aliases, then inspect checkpoint configuration and
perform a small frozen inference smoke test. No reconstruction of a training
cohort or tuning of encoder weights is authorized.

## Relative-path contract v2

User confirmed metadata IDs contain subdirectories and a terminal .npy suffix.
Use --relative-npy for comet_bcl_input_v2_relative_npy. This preserves all directory
components and strips exactly one optional terminal .npy to produce the canonical
stem. Lookup appends .npy once. Absolute paths, empty/dot/traversal components,
backslashes, control characters, and symlinked files/directories below the root
are rejected. Both aliases and sampling-catalog IDs use the same canonicalization;
conflicting labels and global identity collisions remain exclusions. No basename
fallback or date-derived directory is used. Original default v1 remains available.

The private input contains relative stems, compatible with the upstream loader's
suffix-appending lookup. Before GPU inference, the sampling catalog supplied to
the encoder must use these same canonical stems; feeding the original catalog
without checking this could silently misclassify 250Hz records. Selection still
sets ready_for_inference=false. No raw filename example is needed in chat.
