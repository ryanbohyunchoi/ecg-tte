# Run the frozen BCL GPU smoke test

On H100, with a GPU allocated, pull psm-mice-imputation then run:

```bash
bash scripts/run_comet_bcl_smoke_h100.sh
```

This creates a fresh upstream checkout and environment on RAID, pins source to
d359c04d1f5e6c810f76751777535918870704b7, installs torch_env.yml to an explicit
prefix, and saves the solved environment. Setup time is separate from inference.
No modification of mosaic or existing environments. The scheduler's GPU visibility
is preserved. Existing prepared report is comet-bcl-smoke-prep-SWznZWZE/report.

The wrapper verifies input digests and sampling-catalog alignment, checks local
CUDA, hashes the user-confirmed checkpoint, and requires its advertised saved
BCL/12lead/10second/500Hz/lead_time_transformer configuration without overriding
it. A mismatch stops with checkpoint_contract_mismatch for further review.
The trusted local checkpoint is loaded using the upstream weights_only=False
contract; do not substitute checkpoints. No patient values enter the summary.

Run one GPU, batch8, workers2, one32-record shard, fp32/eval, no augmentation,
quality filtering, deduplication, partial mode, or overwrite. Use the paired
canonical sampling catalog, never the original unnormalized IDs. Checkpoint
weights produce backbone vectors before the projection head, as explicitly
reviewed in COMET_BCL_UPSTREAM_REVIEW.md.

Raw logs and index/error records remain restricted on H100. A successful smoke
requires every input exactly once in order, float32 2D arrays with the configured
dimension, no load errors, and finite nonzero vectors. Checkpoint/input hashes
and waveform sizes/mtimes are rechecked. These tests do not validate clinical
sampling semantics, lead order, training overlap, or full-cohort availability.
The result remains ready_for_matching=false. Share only reviewed summary.json.
