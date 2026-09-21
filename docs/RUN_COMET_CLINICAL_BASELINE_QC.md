# COMET demographic, encounter and vital mapping audit

Uses the completed independent clinical snapshot and fixed selected6,530 candidate roster. Does not alter eligibility or index dates, generate the33-variable baseline table, or run MICE/PSM. This resolves linkage and mapping questions before extraction.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_CLINICAL_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-clinical-baseline-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_comet_clinical_baseline.py \
  --cohort-report /mnt/raid0/rbc58/ecg-tte/audits/comet-broad-excluded-cnG52aaY/report \
  --shared-root /mnt/raid0/rbc58/ecg-tte/shared \
  --output-dir "$COMET_CLINICAL_RUN/report"
cat "$COMET_CLINICAL_RUN/report/summary.json"
```

Discovery requires exactly one completed `clinical-sources-v1-*/snapshot` with the expected eight tables. If multiple exist, use `--clinical-snapshot` with the intended absolute snapshot path instead of `--shared-root`; no automatic newest-run selection. All outputs are fresh and on RAID. Runtime is not measured on H100; this scans projected columns from108.5million rows, so allow several minutes.

## Report contents

- `demographic_groups`: exact trimmed patient-key linkage, DOB agreement/unusability and candidate completed age at index; raw sex code/label agreement. The audit flags ages outside0–120 without treating that range as a clinical inclusion rule. Missing values mixed with valid DOBs remain conflicts. Raw label agreement is not a validated sex category map. Demographic history/availability at index remains unverified.
- `encounter_key_coverage`: patients with a dated source encounter key within prior365 days and per-source distinct patient/CSN counts. A missing key is separately counted. These are not clinically classified visit/admission counts. No record is not proof of no utilization or continuous observation.
- `encounter_key_overlap`: shared patient/CSN keys across sources, differing dates for the same patient/CSN and CSNs attached to multiple patient keys. These are review flags, not automatic deduplication or patient reconciliation. Overlap includes hospital/outpatient tables as well as deliveries.
- `record_qc`: selected-cohort prior365 and undated record counts by arm/source. These are records, not unique patients. Encounter dates use CONTACT_DATE or HOSP_ADMSN_DATE according to source; no interpretation of source filename as actual care setting.
- `vital_catalog_combinations`: number of restricted mapping rows; not the number of usable BP, pulse or BMI features.

Only prior days1–365 are eligible for the vital catalog; days1–90 are separated from91–365. Same-day/future measurements are omitted. The catalog classifies value format only: missing marker, numeric, slash pair or other. No numeric value is exported and no slash pair is automatically interpreted as BP. Units and component mappings must be reviewed before values enter baseline extraction/MICE. Unknown availability timestamps remain a separate feature-adapter issue.

## Restricted outputs and next step

Keep `restricted_mapping_catalog.json`, `restricted_demographic_qc.parquet` and `restricted_encounter_qc.sqlite` on H100. They contain raw labels or patient-linked information and must not be pasted wholesale. The catalog contains component IDs/names/units with record and patient counts, raw sex code/label combinations and ED_YN/INP_YN combinations. Counts overlap across mapping rows. It provides the material needed for reviewed measurement/setting maps, not automatic approval of those maps.

Return the reviewed summary. Next review relevant catalog entries locally to freeze BP/pulse/BMI component IDs and units, sex labels and encounter-setting/deduplication rules. Then emit the declared baseline columns plus separate provenance/missingness tables. Entirely unavailable lab variables remain unresolved; no no-lab PSM model is silently substituted.

The script requires completed exact-inventory clinical tables, verifies cohort hash and manifest consistency, checks source part metadata, rejects oversized catalogs/labels, and writes a manifest with output hashes. It does not rehash every clinical part during reading. Synthetic tests cover duplicate/conflicting DOBs, age boundaries, encounter duplication/date/key conflicts, same-day/future vital exclusion, private value non-export, unchanged roster and failed/wrong-snapshot discovery.
