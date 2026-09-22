# Versioned age and diagnosis resolution, with lab mapping draft

This step writes a new **resolution candidate**. It does not overwrite the previous
9,735-person baseline or produce an analysis-ready cohort. The user requested
resolution after reviewing the mapping-gap findings.

## Explicit changes

- Keep ages 18–120. Exclude under18; quarantine null, invalid, negative or over120
  ages rather than imputing eligibility. Based on the supplied counts, 9,732 rows
  are expected, subject to the verified input. This is not full COMET eligibility.
- Diagnose recorded evidence only from DX_DATE days1–365 before the original index.
  Undated evidence is saved separately as an auxiliary and no longer blocks every
  otherwise-negative feature. Thus zero means no qualifying **dated** record,
  not absence of disease. This changes the missingness policy explicitly.
- Parse complete ICD10 token lists separated by commas, semicolons, pipes or
  whitespace. Do not extract codes from free text or accept partial lists. Remaining
  dated parse failures/missing ICD10 continue to block otherwise-negative features;
  positive evidence takes precedence. ICD9 and alternative dates are not silently
  substituted. Index-day/future diagnoses do not enter baseline values.
- Produce a restricted lab mapping draft from the actual catalog on H100. Exact
  generic labels are tentative identity candidates; urine/fluid/CSF signals and
  other names require review. Nothing is approved, no units are assumed, and no
  lab values are inserted into the baseline. Finalization requires reviewed
  component/specimen evidence and units. The 374-group catalog has not yet been
  provided to this task.

## Run on H100

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_RESOLUTION_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-resolution-XXXXXXXX)
python scripts/resolve_comet_baseline_gaps.py \
  --project-root /mnt/raid0/rbc58/ecg-tte \
  --output-dir "$COMET_RESOLUTION_RUN/report"
cat "$COMET_RESOLUTION_RUN/report/summary.json"
```

Requires exactly one completed `comet-mapping-gaps-*/report`, or use explicit
`--mapping-report`. Source and output hashes are checked. Each run has a fresh
output directory; no existing table is modified. Review the output and before/after
diagnosis counts before adopting this version for the study. No MICE is run.

## Locate the lab catalog requested for review

```bash
find /mnt/raid0/rbc58/ecg-tte/audits -maxdepth 3 -type f \
  -path '*/comet-mapping-gaps-*/report/restricted_target_lab_catalog.json' -print
```

If its shell variable remains set:

```bash
less "$COMET_MAPPING_RUN/report/restricted_target_lab_catalog.json"
```

It contains component IDs/names/specimen labels and aggregate counts, not patient
identifiers or raw result values. Review locally before sharing. The new
`restricted_lab_mapping_draft.json` provides label triage but does not replace
this review or provide evidence for units absent from the source.

The new baseline includes the same 32 slots and unchanged medication-order anchors.
Four lab slots remain pending mapping; vital unit/availability assumptions and the
final analysis/outcome contract still require resolution. The new undated-diagnosis
auxiliaries describe ascertainment uncertainty and are not automatically added as
propensity-score predictors.
