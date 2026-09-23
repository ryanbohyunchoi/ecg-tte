# Diagnose zero BCL waveform selections

The H100 input report comet-bcl-input-0aseLinb found pre-index ECG metadata for
6,272 of 7,499 patients, but selected zero waveforms. This does not establish
that waveforms are absent: the exact nonempty, nonsymlink .npy lookup failed.

Run this aggregate-only diagnostic before inference. It samples the first 64
missing-waveform patients per arm, caps IDs at 256 per alias, and probes the four
known roots. It checks literal names, appended .npy/.npz, symlinks and sampling
catalog membership. Directory inventories stop at 500 entries; metadata is read
once with four projected columns. These samples are not population estimates.
No waveform contents, identifiers or filenames are emitted. No parser, cohort,
checkpoint, preprocessing or selection policy is changed.

```bash
(
set -e
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
BCL_PATH_CHECK=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-path-check-XXXXXXXX)
/home/rbc58/miniconda3/envs/mosaic/bin/python scripts/diagnose_comet_bcl_waveforms.py \
  --report /mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-input-0aseLinb/report \
  --metadata /mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet \
  --output-dir "$BCL_PATH_CHECK/report"
cat "$BCL_PATH_CHECK/report/summary.json"
)
```

Review the summary before choosing a corrected root or linkage rule. A successful
path probe is not waveform/preprocessing validation or permission to substitute
a different checkpoint. All private input artifacts remain on H100.
