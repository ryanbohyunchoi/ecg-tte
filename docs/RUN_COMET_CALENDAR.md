# COMET calendar restriction

User approved index dates on or after January 1, 2015 for the primary analysis.
Preserve the full-period roster for sensitivity analysis. Expected candidate count
from reviewed aggregates: 7,499 (4,539 carvedilol; 2,960 metoprolol tartrate).
This is not a requirement for observed EF, a new HF rule or final outcome eligibility.
Upper index-date and follow-up limits remain to be specified.

Run on H100 after pulling the branch:

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
COMET_CALENDAR_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-calendar-XXXXXXXX)
python scripts/restrict_comet_calendar.py \
  --source-report /mnt/raid0/rbc58/ecg-tte/audits/comet-mapped-baseline-sK5bQzbm/report \
  --output-dir "$COMET_CALENDAR_RUN/report"
cat "$COMET_CALENDAR_RUN/report/summary.json"
```

Uses only small saved artifacts; no warehouse rescan. New versioned output includes
filtered baseline, feature statuses and lab lineage, private exclusions, checksums
and per-arm numeric availability/distributions. Original artifacts remain unchanged.
Keep patient artifacts on the cluster; share only reviewed aggregate summary.

This output is not accepted as the old mapped resolution version. Downstream MICE
must explicitly support this new contract. No automatic value cleaning is applied.
Next review numeric missingness within this cohort, then freeze measurement cleaning
and primary/sensitivity imputation specifications. MICE and PSM are not yet run.
