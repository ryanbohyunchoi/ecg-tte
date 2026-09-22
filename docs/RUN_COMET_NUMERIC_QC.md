# Numeric QC of the mapped resolution candidate

Uses only the small saved mapped baseline, selected lab lineage and manifests.
No original sources, full candidate cache or diagnosis extraction is rerun.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_NUMERIC_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-numeric-qc-XXXXXXXX)
python scripts/audit_comet_numeric_candidates.py \
  --project-root /mnt/raid0/rbc58/ecg-tte \
  --output-dir "$COMET_NUMERIC_RUN/report"
cat "$COMET_NUMERIC_RUN/report/summary.json"
```

Requires exactly one completed `comet-mapped-baseline-*/report`, or specify an
absolute `--source-report`. It verifies hashes, roster counts and selected-lab
value/date lineage. Failure writes invalid-count status where output exists.

The summary describes:

- Arm-specific raw-scale quantiles and magnitude bins for age, EF, BP, pulse, BMI
  and four labs. No min/max or individual raw examples are printed. Quantiles are
  suppressed for fewer than20 finite values; all reports still require local review.
- Selected lab distributions by source/component, counting a patient once per group.
  A patient can belong to several source/component groups; do not sum those counts.
- Null/nonfinite counts and selected extreme repeated-number flags. These are
  possible sentinels only, not an exhaustive or validated list. No values are removed.
- Joint missingness and calendar/arm availability, to help assess whether imputation
  would rely heavily on extrapolation into poorly observed groups.
- Paired BP ordering flags as QC, not proof of component orientation or units.

All values remain in their raw scale. Plausible quantiles do not verify units.
There is no cleaning, winsorization, imputation or effect estimation. Unit, numeric
validity, final feature and imputation contracts remain open for review.

Later matching must include the required balance stage in
[COMET_BALANCE_EVALUATION_PLAN.md](COMET_BALANCE_EVALUATION_PLAN.md). That stage is
specified, not yet implemented or run.
