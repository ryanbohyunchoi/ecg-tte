# COMET embedding linkage feasibility

This audit does not match patients or fit models. It checks the existing cleaned
7,499-patient roster against projected ECG metadata and existing cache file IDs.
It uses two projected metadata passes to detect file-ID collisions outside the
cohort too. No waveforms, free-text diagnoses, vectors or models are loaded.

The exploratory availability window is strictly prior calendar days 1–365. This
is an audit window, not a frozen representation selection rule. Same-day records
and unparsed/timezone-bearing dates are not counted as pre-index evidence.
FileID and fileID are reported separately, without silently selecting an alias.
Ambiguous patient/date mappings and duplicated cache IDs cannot count as usable
links. ECG file presence means only a nonempty regular .npy file at the historical
path, not a validated vector. CLMBR cache linkage does not prove its history cutoff.
Directory contents may change during the audit; file presence is an observation,
not an immutable embedding manifest. Counts overlap across aliases/caches.

Run on H100 after pulling the code:

```bash
(
set -e
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
COMET_EMBED_COVERAGE=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-embedding-coverage-XXXXXXXX)
python scripts/audit_comet_embedding_coverage.py \
  --source-report /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-prep-M9F28Lk2/report \
  --output-dir "$COMET_EMBED_COVERAGE/report"
cat "$COMET_EMBED_COVERAGE/report/summary.json"
echo "Report directory: $COMET_EMBED_COVERAGE/report"
)
```

Review aggregate coverage by arm and alias before choosing the common comparison
population. Do not restrict to previously matched patients. No additional MICE or
source rebuild. Next verify representation cutoff/checkpoint provenance and freeze
direct cosine/distance matching settings before looking at embedding balance.
