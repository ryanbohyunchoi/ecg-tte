# Explain diagnosis nulls and narrow lab mapping candidates

Uses the completed cached baseline, its small pre-index lab extracts, and the
existing diagnosis/demographic cache. Does not rebuild or overwrite any artifact,
change clinical criteria, infer units, run MICE, or estimate effects.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_MAPPING_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-mapping-gaps-XXXXXXXX)
python scripts/audit_comet_mapping_gaps.py \
  --project-root /mnt/raid0/rbc58/ecg-tte \
  --output-dir "$COMET_MAPPING_RUN/report"
cat "$COMET_MAPPING_RUN/report/summary.json"
```

Discovery requires exactly one complete `comet-cached-baseline-*/report`. If there
are multiple, pass its absolute path with `--baseline-report`. No destination for
that earlier run was supplied in the reviewed summary, so none is assumed here.

## What to review

`summary.json` provides:

- Unique patients with any pre-index lab across all three sources, without adding
  overlapping per-source counts. A separate union counts broad name leads for
  creatinine, potassium, sodium and hemoglobin. These are not approved analytes or
  usable numeric measurement counts.
- Reasons for each final diagnosis technical null: missing versus unparsed ICD10,
  prior-year versus undated records, and presence of unmapped ICD9 evidence. Reasons
  overlap. Counts explicitly reproduce the existing saved diagnosis feature values;
  a mismatch fails the audit instead of silently changing the parser or values.
- Non-identifying age categories, separating negative age, over120, under18, adult
  review range, and missing/conflicting birth dates. This is an integrity check,
  not a new eligibility exclusion.

`restricted_target_lab_catalog.json` narrows the 5,261 source catalog combinations
using broad target-name discovery. It contains component IDs, names, specimen
labels, any explicit units, counts and raw-value format categories. It contains no
patient identifiers, patient dates or raw result values. Still review it on H100
before sharing any labels/counts:

```bash
less "$COMET_MAPPING_RUN/report/restricted_target_lab_catalog.json"
```

Broad name leads can include urine creatinine, ratios, HbA1c or other non-target
measurements. They must not be promoted directly into PSM covariates. Unit fields
were absent in the reviewed sources; this script does not supply default units
from the magnitude of a measurement. The small saved extracts allow subsequent
approved mapping and numeric QC without full-source scans.

The current baseline rule marks otherwise-negative features technically unresolved
when a relevant prior/undated row has missing or wholly unparseable ICD10. A single
such row can block multiple features, while positive evidence wins. The audit
quantifies this behavior and potential ICD9 coverage gaps. It does not automatically
convert nulls to zeros or treat parsing failures as ordinary imputation targets.

All patient-level artifacts remain on the cluster. This audit uses the existing
code contract and rejects an altered parent, changed source, or baseline parser
version. No source re-export or large-table rebuild is needed for this step.
