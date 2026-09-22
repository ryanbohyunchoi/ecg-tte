# Latest pre-index vital candidates — version2

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

The observed component signatures are5/BLOOD PRESSURE/BP,8/PULSE/Pulse,301070/R BMI/BMI(Calculated), with literal NULL units. Primary windows remain90days for BP/pulse and365days for BMI. No index-day or future readings are used.

Version2 replaces the previous same-day-disagreement policy. On the latest prior measurement day, BP/pulse select the encounter associated with the latest recorded timestamp, then average its parseable readings on that day. Exact duplicates (encounter, timestamp, numeric value) receive one weight. BP components use the same paired readings. Other encounters on that day are not mixed. Missing encounter keys or competing encounters at the latest timestamp block selection. This is a latest-day-within-encounter mean, not a multi-day hospital-stay mean. An unparseable selected reading blocks the mean; no silent skipping.

BMI uses the latest recorded timestamp on the latest day. Differing values at that exact timestamp remain unresolved. Missing/invalid clock times block time-based selection. The raw timestamp must agree with the parsed calendar day; timezones and ambiguous formats are not guessed. No older-value fallback is introduced.

BP/pulse from days91–365 are extracted separately as `bp_older`/`pulse_older` potential imputation auxiliaries using the same rule. They never populate primary baseline columns. Undated matched components block both primary and older selection. Clinical units/availability still require validation.

BP slash-separated values are parsed into `bp_first_candidate` and `bp_second_candidate`; these are not yet labeled systolic/diastolic in the output. Pulse/BMI are raw-scale numeric candidates. No unit conversion, clinical-range validation or availability timestamp validation is claimed. Zero, negative and extreme parseable numbers are not certified as clinically valid. A `candidate_numeric_units_unverified` status is not a clinical observed-value acceptance decision.

`summary.json` gives mutually exclusive feature and primary joint status counts by arm, arm/year missingness patterns, and primary-versus-older availability counts. These counts do not measure predictive accuracy or prove the missing-at-random assumption. These establish unique latest-record availability, including365-day BMI, without summing overlapping catalog bins. `restricted_vital_candidates.parquet` contains all cohort rows, numeric candidates, observation dates and status columns. `restricted_lineage.json` contains original selected-day values, source rows and undated blocking records; it must stay on H100 and must never be pasted into chat. The manifest binds the cohort, clinical snapshot, output hashes, driver and candidate map. Immutable snapshot metadata is checked before/after; clinical parts are not fully rehashed.

## Gate to canonical baseline values

Request the JDAT flowsheet dictionary/source confirmation of BP pair order and units (mmHg), pulse units (beats/min), BMI definition/units (kg/m²), plus RECORDED_TIME meaning. These are currently unresolved; plausible values alone cannot verify units. An explicit availability-time proxy and clinical validity rules also need documentation before promotion to the main baseline table. Do not turn unit-unverified records into missing cells and let MICE hide a source-definition problem.

After those decisions, the staged lineage allows a versioned conversion/validation step without another full-source scan, followed by cohort-specific numeric missingness review. Neither MICE nor eligibility thresholds are applied by this script.

## Version2 validation and scope

Synthetic tests verify within-encounter means, paired BP, duplicate weighting, exclusion of other encounters, latest-timestamp BMI and unresolved ties, date/time/key failures, older auxiliary separation and unchanged cohort. A full MICE pilot still requires the remaining covariates and validated units; this run assesses availability and repeat-reading handling only. Use a fresh run directory and retain the version1 outputs.
