# Full BCL encoding after successful smoke

H100 report comet-bcl-smoke-Ik5VklyT completed 32/32, 256 dimensions, no load
errors, nonfinite or zero vectors in16.299seconds. Saved checkpoint matched
BCL,12leads,10seconds,500Hz,lead_time_transformer. Runtime torch2.5.0,
numpy2.4.6,scipy1.17.1,pandas3.0.6, H100. These are user-reported observations.

With an allocated GPU, pull the branch and run:

```bash
bash scripts/run_comet_bcl_full_h100.sh
```

Reuses /mnt/raid0/rbc58/ecg-tte/software/bcl-smoke-runtime-zZ5FVVsd/env
and its pinned upstream checkout; no reinstall. Full preparation covers all6,103
selected records (C3,561/T2,542) from comet-bcl-input-v2-C9ftzPbQ. It creates a
new full normalized sampling catalog: do not reuse the32-record smoke catalog.
Checks linkage continuity with the successful smoke, checkpoint content hash,
source commit, saved configuration, and four runtime package versions. Records
an explicit environment listing. Single GPU, batch8/workers2/fp32 unchanged;
512-record shards instead of32. No matching, cohort changes or model retraining.

Outputs are fresh under RAID. Raw logs/index errors stay restricted. A completed
run requires all selected IDs exactly once in order across the expected shards,
256-dimensional finite nonzero float32 vectors and no load errors. Failure reports
retain aggregate vector QC when available; do not silently remove failed records.
The aggregate summary stays ready_for_matching=false pending linkage and common
population comparison setup. Clinical semantics and training overlap remain
separate limitations. No claim that ECG availability or technical validity proves
causal validity. Local tests use synthetic vectors only.
