# BCL upstream source review — 2026-09-23

Inspected https://github.com/CarDS-Yale/ECG-signal-pipeline at commit
`d359c04d1f5e6c810f76751777535918870704b7`, read-only local clone.
No model weights, waveforms, or training data loaded. This supersedes the prior
source-location uncertainty; cluster asset availability remains unknown.

## Confirmed implementation

- `bcl_embed_torch.py` and `torch_env.yml` exist at repository root.
- Input CSV requires lowercase `fileID`. The script does not choose pre-index
  ECGs or validate a clinical baseline date. Construct a private linkage table
  separately; pass a fileID-only CSV so optional filter columns cannot silently
  remove patients. Every exclusion still needs explicit recording.
- Default checkpoint is `/mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/CNN0_lead_time_transformer_10s_500Hz_BCL_LR0.0001_Dropout0.5_08_26_2026/trained_12lead_30.pt`.
  Actual contents/epoch/configuration and training overlap remain unverified.
- This is CNN0SignalBackbone with checkpoint-specified representation, default
  checkpoint advertised as12-lead lead_time_transformer. Output is BEFORE the
  BCL projection head, not the archived Net1D512D projected representation.
  Actual dimension follows checkpoint config; transformer code default256 is
  not evidence of the saved model's dimension. Use this source explicitly; no
  silent reuse of the old archive contract.
- Non-projection weights must match backbone keys. Runs eval/inference mode,
  defaults fp32. No training or fine-tuning requested.
- Outputs float32 shard arrays and row/fileID/error index CSVs. Failed loads
  become NaN rows with raw error strings; those files/logs stay restricted.
  Adapter must reject/non-count nonfinite or zero vectors and validate every
  selected fileID exactly once. Successful file writing is not coverage success.
- Whole output shards, not batches, are assigned to ranks. Default shard_size50,000
  means a~6K cohort uses only one rank. Use explicit shard_size512 for a later
  two-GPU full run; smoke can use one GPU. No GPU allocation has been checked.
- Resume identity tracks paths/settings/fileID hash, but not checkpoint content
  hash and not every preprocessing input. Our wrapper should use fresh output
  and pin source, weights, sampling metadata and explicit roots. No overwrite.

## Preprocessing dependencies

`modules/utils_torch.py` reads `<root>/<fileID>.npy` in ordered roots, infers sample
axis and uses first12 channels. Assumes canonical lead order and10seconds; these
are source assumptions to verify, not facts established by shape. Uses
`formats_rerun.csv` (columns fileID,format_new) to identify250Hz recordings,
resamples them to500Hz, subtracts a500-sample median-filter baseline, then resamples
and truncates to checkpoint frequency/duration. No default inference augmentation.
Sampling-format input therefore must not be replaced by an empty file or guessed
from absent metadata. Default format path `/mnt/nfs_yale_ecg/preprocessing/formats_rerun.csv`.
Historical H100 waveform root `/mnt/raid0/bb2238/signals/preprocessed/all_ecgs`
is a candidate explicit override, not proven equivalent to upstream default roots.

Environment YAML declares Python3.11,PyTorch2.5.0,CUDA12.4 plus scientific packages;
several versions are ranges, so save the solved environment. Install only to a
fresh explicit RAID prefix, with RAID package cache/temp when ready.

## Next H100 step (read-only paths/header)

```bash
(
set -e
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
BCL_CHECK=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/bcl-assets-XXXXXXXX)
python scripts/check_comet_bcl_assets.py --output-dir "$BCL_CHECK/report"
cat "$BCL_CHECK/report/summary.json"
)
```

Then resolve missing assets, freeze the ECG selection/input/checkpoint contract,
build fileID-only input with private dated linkage, inspect checkpoint metadata,
and perform a small frozen inference smoke test. No cohort/output placeholders
should be passed to the upstream extraction command. Compare with unchanged
clinical PSM on the same ECG-available patients; ECG metadata availability alone
does not establish usable vectors. Do not silently convert this into an
embedding-derived propensity model without its separate specification.
