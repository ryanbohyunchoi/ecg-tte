# Expanded COMET baseline from the completed candidate cache

## Scope

One command verifies and uses the completed expanded diagnosis cohort and candidate
cache. It refreshes vital candidates, constructs the declared 32 baseline columns
using both diagnosis deliveries, and saves a smaller pre-index lab extract. All
output is a new private directory; existing cohorts, caches and source tables stay
unchanged. The reported cohort has 9,735 candidates; the script validates the saved
cohort rather than hardcoding that count or selecting a new population.

The run is **staging, not MICE or effect estimation**. In particular, creatinine,
potassium, sodium and hemoglobin remain null with `pending_lab_component_unit_mapping`
until the lab catalog is mapped. No lab value is inferred from a plausible number,
component substring or numeric sentinel. The source header reviewed for 2025 labs
has no explicit unit field; the report lists any unit fields actually available.
Vital raw-scale candidates retain their existing unverified-unit status.

## Run on H100

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_BASELINE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-cached-baseline-XXXXXXXX)
python scripts/build_comet_cached_baseline.py \
  --project-root /mnt/raid0/rbc58/ecg-tte \
  --output-dir "$COMET_BASELINE_RUN/report"
cat "$COMET_BASELINE_RUN/report/summary.json"
```

Discovery requires exactly one completed `comet-expanded-dx-*/report` and one
completed `comet-event-cache-*/cache`. It never chooses the newest arbitrarily.
If multiple exist, use explicit `--cohort-report` and `--candidate-cache` paths.
The supplied cache summary did not contain its destination, so discovery avoids
inventing that path. Input manifests bind the five source snapshots automatically.

There is no need to rerun source builds, cache construction, or cohort reassessment.
Runtime is not yet measured on H100. Progress prints the current source/stage.
This version does not resume a failed run; completed child artifacts stay available
but only the root `complete_cached_baseline_staging` status means this full run passed.

## Outputs

- `summary.json`: aggregate feature-status counts by arm, lab coverage and elapsed time.
- `manifest.json`: input and implementation hashes and output integrity checks.
- `baseline/restricted_baseline_staging.parquet`: 32 candidate covariates plus patient,
  treatment and index fields, on the verified expanded roster.
- `baseline/restricted_feature_status.parquet`: separate missing/technical/recorded
  evidence status for each patient-feature pair.
- `vitals/`: refreshed measurements, raw-scale status and restricted lineage.
- `labs/*.parquet`: projected lab fields for days 1–90 before each patient's index,
  including raw values, source row, component and specimen labels. No notes/comments
  are projected. Sources remain separate; overlapping rows are not counted as unique tests.
- `labs/restricted_lab_catalog.json`: component/specimen/unit signatures and raw-value
  format counts. Review locally before sharing any labels or aggregates.

## Preserved clinical rules and limitations

Original medication-order anchors and cohort exclusions are unchanged. Diagnoses
from both deliveries contribute Boolean recorded comorbidity evidence within 365
prior days. Duplicate positive records cannot increase a binary feature. Missing or
unparseable evidence retains the existing technical-null rules; positive evidence
wins. ICD9 mapping remains absent and visible in the diagnosis coverage diagnostic.

Prior orders use 90 days, EF/encounters/BMI 365, BP/pulse 90. Index-day observations
are excluded. The pre-index lab extract uses RESULT_DATE, a calendar-day proxy, not
proof of historical result availability; undated results are excluded from it.
Lab component/unit mappings and same-time duplicate/conflict resolution are still
required before producing clinical lab features. Missing results are not zero.

Recorded encounter zeros follow the already accepted v4 policy: no qualifying dated
record, not continuous observation. Ambiguous encounter keys/settings remain null.
Both clinical deliveries are considered, and the existing tuple deduplication and
conflict handling are preserved. No HF hospitalization feature is reintroduced.
The HF linkage diagnostic pools source-type evidence across diagnosis deliveries;
the separate coverage report identifies each source snapshot.

Lab coverage is limited to the completed 2025 outpatient snapshot and hospital
shards 1 and 2. Damaged shard 3 stays excluded. This limitation must remain visible
in later missingness and analysis reports. No outcome data are used as baseline
features or to tune the extraction.

After this run, mapping work should read the saved pre-index lab extracts, not the
original large sources. Freeze the final clinical/analysis contracts and review
cohort-specific missingness before MICE and PSM.
