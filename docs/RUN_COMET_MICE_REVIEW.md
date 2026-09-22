# Review the saved COMET MICE pilot

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
COMET_MICE_REVIEW=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-review-XXXXXXXX)
python scripts/review_comet_mice_pilot.py \
  --report /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-ss4GJlP5/report \
  --output-dir "$COMET_MICE_REVIEW/report"
cat "$COMET_MICE_REVIEW/report/summary.json"
```

No R installation, source scans, or repeated imputation needed. Keep all patient
artifacts on cluster; share only reviewed aggregate summary. Existing chain_traces.pdf
still needs visual review for drift/mixing. Autocorrelation summaries do not establish
convergence; observed/imputed distribution differences are not balance metrics and
need not be zero. BP counts distinguish unique people from repeated imputation rows;
no automatic swapping, clipping, exclusion or value replacement occurs.

The lme4/Matrix startup warning is separately detected in the saved engine log.
Environment repair and verification remains separate; this review does not modify
packages or claim that the ABI mismatch is fixed. PSM readiness remains false.
