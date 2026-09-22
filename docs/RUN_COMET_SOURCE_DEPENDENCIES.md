# Check remaining COMET source dependencies

Current staging v4 is complete for6,530patients/32slots. User confirms no vital
unit documentation or intact replacement for the damaged2025lab shard3 is
currently available. Do not repeat cohort construction or infer units from
numeric values alone.

This lightweight check inspects the exact diagnosis headers in both deliveries,
metadata for11known lab paths, filenames that might be dictionaries in the raw
root/delivery directories, and saved summary/catalog locations. It reads no
patient rows or lab contents. It does not establish integrity from file presence,
recover a failed snapshot, or substitute a source. Diagnosis2025availability is
an unverified lead to investigate the poor2025encounter/2026diagnosis linkage.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
COMET_DEP_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-source-dependencies-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/check_comet_source_dependencies.py \
  --root /home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG \
  --shared-root /mnt/raid0/rbc58/ecg-tte/shared \
  --audit-root /mnt/raid0/rbc58/ecg-tte/audits \
  --output-dir "$COMET_DEP_RUN/report"
cat "$COMET_DEP_RUN/report/summary.json"
```

Review locally before sharing. Only exact headers, filenames and saved aggregate
stage metadata are included; dictionary and catalog contents remain unread.
Inventory is bounded to10,000entries per directory; warnings identify limits or
unavailable locations. No recursive discovery. `metadata_check_complete` means
this bounded check ended, not that clinical dependencies are resolved. Missing
files and failed snapshot statuses remain explicit.

Expected runtime: seconds to a few minutes depending on mount latency. Next
select a separately specified usable lab source set or obtain a corrected source;
do not read the failed snapshot as complete. If no dictionary appears, obtain
source confirmation or explicitly agree a provisional measurement contract with
plausibility checks; neither has occurred. Cohort, predictors and outcomes stay
unchanged; no MICE/PSM runs.
