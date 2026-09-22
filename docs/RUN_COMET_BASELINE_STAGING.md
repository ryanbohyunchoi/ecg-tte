# Assemble the declared COMET baseline staging table

This joins the fixed cohort, completed core/clinical snapshots and version2 vital candidates into one36-column table:33 declared feature slots plus patient key, treatment arm and index date. It is an explicit staging artifact, not a validated analysis table. `ready_for_mice` remains false.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_BASELINE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-baseline-staging-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/build_comet_baseline_staging.py \
  --cohort-report /mnt/raid0/rbc58/ecg-tte/audits/comet-broad-excluded-cnG52aaY/report \
  --clinical-snapshot /mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-t9ZGomLT/snapshot \
  --audit-root /mnt/raid0/rbc58/ecg-tte/audits \
  --output-dir "$COMET_BASELINE_RUN/report"
cat "$COMET_BASELINE_RUN/report/summary.json"
```

Discovery requires exactly one complete version2 vital report. If several exist, use `--vital-report` with the intended absolute report path instead of `--audit-root`. Hashes, cohort patient/arm/index alignment and clinical snapshot lineage must match. Fresh output only; no overwrite or resume. Several projected tables are scanned; H100 runtime is not yet measured. All outputs stay on RAID.

## Outputs

- `restricted_baseline_staging.parquet`: one row per candidate, the33 feature slots in COMET_PSM_TABLE_V1.json, and three metadata columns.
- `restricted_feature_status.parquet`: one row per patient/feature giving its candidate or blocking state. Must accompany the numeric table; do not send all nulls directly to MICE.
- `manifest.json`: binds the candidate cohort, core/clinical snapshots, vital output, feature specification, script and outputs. Explicit discovery code prefixes and medication-name lists are recorded. Selection rules and source snapshots support reproducing this stage; complete event-level provenance adapters remain required for clinical promotion.
- `summary.json`: per-arm feature/status/non-null counts and source-quality flags. Return only reviewed aggregates; all patient tables remain on H100.

## What is actually extracted

Demographics use exact patient keys, consistent DOBs and the observed raw sex pairs1/Female and2/Male. Index year is derived. These do not validate identity or demographic availability at index. Echo uses the latest strictly prior day within365 days, accepts only a single candidate value in(1,100], and never falls back from a missing/conflicting latest value.

The vital columns copy version2 candidates. `sbp` and `dbp` are the declared first/second BP target slots, with explicit unit/orientation-unverified status; their names do not certify the interpretation. Older BP/pulse auxiliaries remain in the linked vital artifact, outside the33 predictor slots.

Diagnosis slots are positive ICD10-family discovery leads in the prior365 days. Exact candidate prefixes are in the script/manifest. They are not validated year-specific ICD10-CM phenotypes, do not interpret ICD9, and do not establish lifetime history. For example,I48 includes flutter;I60–I64/I69 includes broader cerebrovascular history;the PAD vocabulary is incomplete;valve codes do not establish severity. The mappings are for feasibility review only. Every absent lead remains null with `negative_ascertainment_unvalidated`, not0 and not an ordinary imputation target. Malformed prior code cells are counted.

Medication slots are positive generic-name leads in the prior90 days, all source routes/classes. They do not establish active use, indication, dose or complete class coverage; brand-only records are not mapped. Sacubitril+valsartan is an ARNI lead and does not also mark the ARB slot from that same record. Other separate ARB orders can still mark that slot. This is a provisional discovery vocabulary, not the approved medication-ID/formulation map.

Utilization uses unique patient/CSN keys in the prior365 days. Exact duplicate tuples collapse; conflicting dates/settings or cross-patient CSNs block that patient's counts. Outpatient-source membership, ED_YN=1 and INP_YN=1 are explicit unvalidated setting proxies. ED and inpatient counts may overlap. HF admission candidates additionally require a matching patient/CSN with prior I50 evidence; this is not principal-diagnosis adjudication. Zero counts remain null because observation coverage is not established. No future diagnoses, medications or encounters contribute.

The four lab columns remain null with `blocked_lab_source`; the failed lab extension is not read. A source-level absence cannot be repaired by MICE.

## What this does not establish

This is the complete declared column layout, not completed clinical validation. Eligibility/index, diagnosis/drug maps, source capture/negative ascertainment, encounter-setting definitions, units/ranges/availability and lab recovery remain unresolved. The status summary distinguishes these problems from genuinely missing measured covariates. No patients are excluded and no imputation, matching or effects are run.

Next review the unified feature-status counts and freeze validated mappings/coverage policies, including how to encode recorded negative evidence. Only then produce a separately versioned model-ready baseline table. Do not quietly interpret all absent codes as disease-free, all absent orders as no treatment, or all source-blocked nulls as imputable. Clinical missingness diagnostics, predictive support and a MICE pilot follow that gate.

Synthetic integration checks exact36-column layout,2-patient/66-status-row reconciliation, matched vital lineage, pre-index dates, duplicate encounter handling, HF-key linkage, missing labs and absent evidence remaining null, no overwrite, and rejection of altered vital artifacts.
