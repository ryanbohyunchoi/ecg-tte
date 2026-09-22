# Latest pre-index vital candidates

Creates a restricted one-row-per-candidate staging table for BP components, pulse and BMI. This advances beyond catalog counts to actual selected records and missingness/quality states. It is not the final33-variable PSM table and is marked `ready_for_mice: false`.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_VITAL_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-vital-candidates-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/extract_comet_vital_candidates.py \
  --cohort-report /mnt/raid0/rbc58/ecg-tte/audits/comet-broad-excluded-cnG52aaY/report \
  --clinical-snapshot /mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-t9ZGomLT/snapshot \
  --output-dir "$COMET_VITAL_RUN/report"
cat "$COMET_VITAL_RUN/report/summary.json"
```

Reads only the three vital tables from the completed clinical snapshot. All candidates remain; no new exclusions or model changes. Runtime is unmeasured. Keep all output under RAID and return only the reviewed summary.

## Selection and meaning

The observed component signatures are5/BLOOD PRESSURE/BP,8/PULSE/Pulse,301070/R BMI/BMI(Calculated), with literal NULL units. The last signature is an observed source label, not a verified calculation. Latest strictly prior calendar day within90 days is selected for BP/pulse; BMI uses365 days. Same-day/future records are excluded. Several identical numeric observations on the latest day agree; differing observations block selection. A missing/unparseable latest value blocks selection without falling back. Undated records for the matched patient/component block that feature because ordering cannot be established. Changed selected-day labels or units are reported rather than silently accepted.

BP slash-separated values are parsed into `bp_first_candidate` and `bp_second_candidate`; these are not yet labeled systolic/diastolic in the output. Pulse/BMI are raw-scale numeric candidates. No unit conversion, clinical-range validation or availability timestamp validation is claimed. Zero, negative and extreme parseable numbers are not certified as clinically valid. A `candidate_numeric_units_unverified` status is not a clinical observed-value acceptance decision.

`summary.json` gives mutually exclusive feature and joint status counts by arm. These establish unique latest-record availability, including365-day BMI, without summing overlapping catalog bins. `restricted_vital_candidates.parquet` contains all cohort rows, numeric candidates, observation dates and status columns. `restricted_lineage.json` contains original selected-day values, source rows and undated blocking records; it must stay on H100 and must never be pasted into chat. The manifest binds the cohort, clinical snapshot, output hashes, driver and candidate map. Immutable snapshot metadata is checked before/after; clinical parts are not fully rehashed.

## Gate to canonical baseline values

Request the JDAT flowsheet dictionary/source confirmation of BP pair order and units (mmHg), pulse units (beats/min), BMI definition/units (kg/m²), plus RECORDED_TIME meaning. These are currently unresolved; plausible values alone cannot verify units. An explicit availability-time proxy and clinical validity rules also need documentation before promotion to the main baseline table. Do not turn unit-unverified records into missing cells and let MICE hide a source-definition problem.

After those decisions, the staged lineage allows a versioned conversion/validation step without another full-source scan, followed by cohort-specific numeric missingness review. Neither MICE nor eligibility thresholds are applied by this script.
