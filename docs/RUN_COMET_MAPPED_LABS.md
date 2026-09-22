# Reviewed lab identity mapping and resolution candidate

The 374-group catalog supplied on 2026-09-22 supports the following exact
component/name/base-name identity candidates in the selected 2025 hospital1/2 and
outpatient lab sources. No canonical unit metadata were supplied.

| Target | Component IDs |
|---|---|
| Creatinine | 795, 1526296 |
| Potassium | 894, 1534081 |
| Sodium | 893, 1534098 |
| Hemoglobin (routine-name candidates) | 1256, 17187, 1534435, 812, 24868 |

Exact signatures are encoded in `scripts/comet_reviewed_lab_map.py`, and copied
into each mapping report. Primary selection requires SPECIMEN_TYPE exactly Blood
and no explicit contradictory urine/CSF/stool/swab specimen-source signal. Missing
or contradictory specimen labels remain unresolved. This conservative source rule
is explicit: the reviewed catalog includes a few routine-labelled components with
urine/catheter or unrelated specimen labels. It does not establish that those
metadata are always accurate.

Exclude BUN/creatinine ratio, eGFR, urine creatinine, HbA1c, hemoglobin fractions,
electrophoresis, free plasma hemoglobin, urine hemoglobin, blood-gas and POC
hemoglobin from these primary identity candidates. They are not interchangeable
measurements. No silent substitution or imputed mapping.

## Run once on H100

This combines the age/dated-diagnosis resolution step with lab mapping in a fresh
output. It does not require a prior resolution run, nor rebuild the source cache.
The small saved lab extracts are reused.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_MAPPED_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-mapped-baseline-XXXXXXXX)
python scripts/resolve_comet_baseline_gaps.py \
  --project-root /mnt/raid0/rbc58/ecg-tte \
  --map-reviewed-labs \
  --output-dir "$COMET_MAPPED_RUN/report"
cat "$COMET_MAPPED_RUN/report/summary.json"
```

Exactly one completed mapping-gap audit is discovered, or specify
`--mapping-report /absolute/path/to/report`. Fresh output version is
`comet_baseline_resolution_v2_mapped_labs`.

## Interpretation and outputs

`restricted_baseline_resolution.parquet` now includes raw-scale numeric lab
candidates, with `mapped_numeric_units_unverified` status. These are **not verified
mg/dL, mmol/L or g/dL values**, and `ready_for_mice` remains false. There is no unit
conversion or plausible-value unit inference. New explicit unit fields trigger
review rather than changing the source contract automatically.

Use RESULT_DATE days1-90 strictly before each original index, then latest RESULT_TIME.
Index day and future results are excluded. Latest-day unparseable times or date/time
conflicts block selection; tied numeric disagreements are null. No older fallback
or averaging of conflicting lab results. Identical latest values across source rows
coalesce into one candidate while all selected rows are retained in restricted
lineage. Specimen/label/value failures at the selected latest timestamp do not cause
fallback to older values. This is conservative candidate extraction, not final
clinical validity or result-availability validation.

Parse complete ordinary numeric ORD_VALUE strings only. Inequality, text, missing
and nonfinite values stay unresolved. ORD_NUM_VALUE is checked for disagreement
but never substituted as a result. Clinical range and sentinel validation are still
needed before using raw-scale candidates for MICE.

`lab_mapping_report.json` contains per-arm availability/status counts and source
record QC. `restricted_lab_selected_lineage.parquet` retains selected source rows,
times and raw values on H100 only. The legacy label-only draft, if present, is
superseded by the explicit identity map in the mapping report.

Age/diagnosis changes are exactly those in RUN_COMET_BASELINE_RESOLUTION.md:
adult-range selection with invalid-age quarantine, dated recorded diagnosis
features, separate undated auxiliaries, no ICD9 translation or date fallback.
This preserves the original baseline and is still a resolution candidate, not a
frozen full COMET protocol. No MICE, matching or effect estimation is run here.
