# Assemble the declared COMET baseline staging table

This joins the fixed cohort, completed core/clinical snapshots and version2 vital candidates into one36-column table:33 declared feature slots plus patient key, treatment arm and index date. It is an explicit staging artifact, not a validated analysis table. `ready_for_mice` remains false.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/audits
COMET_BASELINE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-baseline-v2-XXXXXXXX)
PYTHONDONTWRITEBYTECODE=1 python scripts/build_comet_baseline_staging.py \
  --cohort-report /mnt/raid0/rbc58/ecg-tte/audits/comet-broad-excluded-cnG52aaY/report \
  --clinical-snapshot /mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-t9ZGomLT/snapshot \
  --vital-report /mnt/raid0/rbc58/ecg-tte/audits/comet-vital-v2-fh8lNqlw/report \
  --output-dir "$COMET_BASELINE_RUN/report"
cat "$COMET_BASELINE_RUN/report/summary.json"
cat "$COMET_BASELINE_RUN/report/hf_linkage_diagnostic.json"
```

Discovery requires exactly one complete version2 vital report. If several exist, use `--vital-report` with the intended absolute report path instead of `--audit-root`. Hashes, cohort patient/arm/index alignment and clinical snapshot lineage must match. Fresh output only; no overwrite or resume. Several projected tables are scanned; The preceding version took about 4.7 minutes on H100; allow roughly 5–10 minutes for this expanded scan, subject to I/O load. All outputs stay on RAID.

## Outputs

- `restricted_baseline_staging.parquet`: one row per candidate, the33 feature slots in COMET_PSM_TABLE_V1.json, and three metadata columns.
- `restricted_feature_status.parquet`: one row per patient/feature giving its candidate or blocking state. Must accompany the numeric table; do not send all nulls directly to MICE.
- `manifest.json`: binds the candidate cohort, core/clinical snapshots, vital output, feature specification, script and outputs. Explicit discovery code prefixes and medication-name lists are recorded. Selection rules and source snapshots support reproducing this stage; complete event-level provenance adapters remain required for clinical promotion.
- `summary.json`: per-arm feature/status/non-null counts and source-quality flags. Return only reviewed aggregates; all patient tables remain on H100.

## What is actually extracted

Demographics use exact patient keys, consistent DOBs and the observed raw sex pairs1/Female and2/Male. Index year is derived. These do not validate identity or demographic availability at index. Echo uses the latest strictly prior day within365 days, accepts only a single candidate value in(1,100], and never falls back from a missing/conflicting latest value.

The vital columns copy version2 candidates. `sbp` and `dbp` are the declared first/second BP target slots, with explicit unit/orientation-unverified status; their names do not certify the interpretation. Older BP/pulse auxiliaries remain in the linked vital artifact, outside the33 predictor slots.

Diagnosis slots are positive ICD10-family discovery leads in the prior365 days. Exact candidate prefixes are in the script/manifest. They are not validated year-specific ICD10-CM phenotypes, do not interpret ICD9, and do not establish lifetime history. For example,I48 includes flutter;I60–I64/I69 includes broader cerebrovascular history;the PAD vocabulary is incomplete;valve codes do not establish severity. The mappings are for feasibility review only. Version2 uses the user-approved recorded-evidence policy: 1 for a qualifying prior lead; 0 for no qualifying record under this vocabulary/window; null for technical uncertainty. A missing/unparseable ICD10 cell within365 days blocks otherwise negative diagnosis slots. Undated parseable codes block only their matching features; undated unparseable cells block all diagnosis slots. An observed qualifying positive wins over uncertainty. Zero does not establish disease absence, requires no gold-standard adjudication or continuous-enrollment proof, and is not imputed. No observation-based cohort exclusions are added. ICD9 presence is reported separately and is not silently mapped.

Medication slots are positive generic-name leads in the prior90 days, all source routes/classes. They do not establish active use, indication, dose or complete class coverage; brand-only records are not mapped. Sacubitril+valsartan is an ARNI lead and does not also mark the ARB slot from that same record. Other separate ARB orders can still mark that slot. This is a provisional discovery vocabulary, not the approved medication-ID/formulation map. The same 1/0/null recorded-evidence policy applies. An undated matching name blocks that class if no dated positive exists; a prior90 or undated row with all three name fields missing blocks otherwise negative classes. Unmatched nonempty names are no match under the declared lexical vocabulary, not technical missingness. Brand coverage remains a limitation. The presence of an unrelated undated order does not block every medication variable.

Utilization uses unique patient/CSN keys in the prior365 days. Exact duplicate tuples collapse; conflicting dates/settings or cross-patient CSNs block that patient's counts. Outpatient-source membership, ED_YN=1 and INP_YN=1 are explicit unvalidated setting proxies. ED and inpatient counts may overlap. HF admission candidates additionally require a matching patient/CSN with prior I50 evidence; this is not principal-diagnosis adjudication. Zero counts remain null because observation coverage is not established. No future diagnoses, medications or encounters contribute to baseline features. The separate linkage diagnostic classifies diagnosis dates outside baseline solely to explain failed joins; these never rescue baseline counts.

The four lab columns remain null with `blocked_lab_source`; the failed lab extension is not read. A source-level absence cannot be repaired by MICE.

## What this does not establish

This is the complete declared column layout, not completed clinical validation. Eligibility/index, diagnosis/drug maps, source capture/negative ascertainment, encounter-setting definitions, units/ranges/availability and lab recovery remain unresolved. The status summary distinguishes these problems from genuinely missing measured covariates. No patients are excluded and no imputation, matching or effects are run.

The recorded-evidence binary encoding is now accepted; review the resulting technical-null counts and linkage diagnostic, then resolve the remaining mappings and measurement contracts. Only then produce a separately versioned model-ready baseline table. Do not quietly interpret all absent codes as disease-free, all absent orders as no treatment, or all source-blocked nulls as imputable. Clinical missingness diagnostics, predictive support and a MICE pilot follow that gate.

Synthetic integration checks exact36-column layout,2-patient/66-status-row reconciliation, matched vital lineage, pre-index dates, duplicate encounter handling, HF-key linkage, missing labs and recorded zeros, technical-null precedence, no overwrite, and rejection of altered vital artifacts.

## Version2 HF linkage diagnostic

`hf_linkage_diagnostic.json` reports unique inpatient encounter keys and patients by arm and diagnosis source. The denominator requires an unambiguous prior365 encounter with INP_YN=1 and valid ED flag. Stages show any same-key diagnosis, any same-key I50 code, and I50 DX_DATE and CALC_DX_DATE buckets (prior365, older, missing, same-day, future). Diagnosis-source and stage counts overlap. Missing stages mean zero, not unavailable. Both sources are inspected separately, while the existing baseline feature uses their union.

Row-level coverage aggregates by arm/index year/source show ICD10 parsing, ICD9 presence, missing encounter keys and DX_DATE timing. They help distinguish limited historical coding from encounter-key/date mismatch. Exact trimmed patient/CSN matching is preserved; no identifier transformations or alternate-date fallback are applied. The diagnostic and its checksum are bound to the run manifest. No raw codes, identifiers or patient-specific dates are printed. Review aggregates locally before sharing.

The legacy feature name `hf_hospital_admissions` now has the explicit description **inpatient encounters with an HF diagnosis**. It does not establish HF as the cause of admission or merge encounters into hospitalization episodes. This version does not change its values or null/zero policy; investigate linkage before that separate change. All existing snapshots and v1 reports remain untouched.
