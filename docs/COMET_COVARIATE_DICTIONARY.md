# COMET clinical covariate dictionary — proposed v0

The primary extraction target is now the [declared 33-variable table](COMET_PSM_TABLE_V1.md). The broader inventory below remains mapping/auxiliary context; it is not the active predictor list.

2026-09-21. A reviewable feature specification, not a finalized PSM model. Windows
below are proposed design choices; none were selected using treatment effects.
One row may expand into several model terms. Variable count is not a quality
criterion. Confirm causal roles, measurement quality, overlap and sample support
before freezing the actual set. No automated treatment-prediction screening.

All baseline windows exclude the index calendar day. Lags 1 through W include
exactly index minus W through index minus 1. Date-only source helpers cannot
prove report availability. Include source/measurement recency in QC, but adding
missingness/recency to the propensity model requires a variable-role decision.

| Variable/domain | Candidate source/fields | Proposed selection/window | Unit, missingness and role review |
|---|---|---|---|
| Age | 2025 Patients.BIRTH_DATE | Completed age at index | Validate DOB and identity; never use future echo age. Proposed confounder; mandatory demographic failures are not silently imputed. |
| Recorded sex | 2025 Patients.SEX_C / SEX | Source attribute, with provenance | Check label conflicts and update semantics. Missing is distinct from any category. Do not equate recorded sex with gender identity. |
| Calendar time | Declared index date | Index year; finer periods only if supported | Secular prescribing/capture confounder; common support required. |
| Site/care setting | Encounter IDs, department/facility and care-class fields | Most recent appropriate prior encounter within 365 days; otherwise unknown | Hospital file does not mean inpatient. Pre-index site can encode instrument/selection effects; inclusion requires role review. No inferred site from future visits. |
| LVEF | Echo EF, EchoDate | Latest prior echo within 365 days, with no fallback from unusable latest echo | Verified percent only; EF=35 separate until boundary resolved. Eligibility versus adjustment roles separate; cannot impute qualification. Availability timestamp/proxy unresolved. |
| HF history/severity | Hospital/outpatient diagnosis codes; encounter context | HF phenotype before index; 365-day recency/counts, CV admission in proposed 730-day trial-alignment audit | Versioned ICD9/10 map and date lineage required. Prior diagnosis absence is not proof of no HF. NYHA not established in structured sources. |
| Systolic and diastolic BP | FLO_MEAS_ID/name, MEAS_VALUE, UNIT, RECORDED_TIME | Latest prior mapped measurement within 90 days | Candidate canonical mmHg; mapping/units not validated. Split slash pairs only after component review; retain both components from the same reading. No generic string split. |
| Heart rate | Same vital source | Latest prior within 90 days | Candidate beats/min; exact component and unit mapping required. |
| BMI | Mapped vital component | Latest prior within 365 days | Candidate kg/m²; no unreviewed BMI calculation from unrelated height/weight dates. Weight/height can be audit auxiliaries with their own units/times. |
| Creatinine | COMPONENT_ID/name, ORD_VALUE, ORD_NUM_VALUE; specimen/result times | Latest prior within 90 days | Candidate mg/dL after verified conversion; never infer units from plausible values. Keep inequality results separate; do not treat numeric sentinels as measurements. |
| eGFR | Mapped lab component and equation provenance | Latest prior within 90 days | Candidate mL/min/1.73m². Equation changes and censored values need review; do not combine indexed/nonindexed units. Decide creatinine versus eGFR redundancy before PSM; no formula invented from missing inputs. |
| Potassium and sodium | Mapped lab components | Latest prior each within 90 days | Candidate mmol/L; verify component-specific units and specimen context. |
| Hemoglobin | Mapped lab component | Latest prior within 90 days | Candidate g/dL; conversion only through approved mapping. |
| BNP / NT-proBNP | Distinct mapped lab components | Latest prior within 90 days; optional severity auxiliaries | Keep assays separate, candidate pg/mL subject to verification. Do not pool or substitute them. Availability may be too selective for primary PSM. |
| Comorbidities | Hospital/outpatient DX with validated timing | Proposed 365-day code history; lifetime/history phenotypes require separate coverage policy | Candidate ischemic disease/MI, AF, hypertension, diabetes, CKD, stroke, COPD/asthma, peripheral arterial disease and valve disease. Versioned phenotypes, not code-prefix guesses. Contraindication versus confounder role must be explicit. |
| Baseline medications | Mapped medication orders plus original timing/status fields | Proposed orders in previous 90 days; 365-day history audit | ACEI, ARB, ARNI, MRA, loop diuretics, SGLT2i, digoxin and relevant rhythm/BP drugs. Presence means prior order evidence, not active use or adherence. Historical calendar availability matters. No future refill requirement. |
| Baseline healthcare use | Encounter identifiers and validated setting/time | Distinct outpatient visits, ED encounters and hospital admissions in prior 365 days | Deduplicate via reviewed event keys across deliveries, not row counts. Missing coverage is not zero utilization. HF-specific admissions need validated phenotype. |

These are candidate clinical domains, not a requirement to include every listed
variable. Race/ethnicity, geography and socioeconomic proxies require a separate
causal/measurement review; raw ZIP and provider IDs are not default PSM features.
Do not include assigned-drug dose, post-index treatment, discontinuation, outcomes,
future visits or representations built with future data in baseline adjustment.

## Mapping and timing contract required per measurement

Record component IDs, source delivery, assay/specimen restrictions, raw value
precedence, marker/sentinel handling, canonical units/conversion, clinical range
checks, timestamp meaning and availability rule under a versioned mapping. The
current lab schema has no explicit unit field: authoritative component/source
metadata is needed before canonical numeric features can be emitted. MICE cannot
supply missing unit provenance. The two lab value columns remain raw until a
joint component-level review decides how each can be used.

A numeric event adapter must provide both observation and availability dates.
Specimen collection and result availability are different concepts. If no valid
availability source exists, mark unknown. A documented proxy can be considered
under an explicitly adapted contract, not silently set equal to observation date.
The selector currently blocks that measurement. For patient attributes and code
histories, separate adapters must address historical availability as well.

Provenance for each selected value includes snapshot/version, source table and
source row; event date, lag, original component/value/unit and conversion decisions
remain restricted on H100. No patient-specific dates or values in Git or logs.

## Missingness and imputation handoff

Produce arm/year QC with the full declared cohort denominator and separate states:
source unavailable, source coverage unknown, event date unresolved, no record in
window, latest observation unusable (with overlapping reasons), and observed.
A missing numeric covariate is not a missing schema column or unknown unit.
Report these states before offering any values to an imputation routine.

The selector returns one exclusive status and zero or more issue flags. Sum the
exclusive statuses for denominator checks; do not sum overlapping flags. Audits
should additionally retain measurement lag and cross-source disagreement rates.
Cell-release review stays on H100; do not export small or unreviewed strata.

Use the proposed MICE plan only after mapping/timing and cohort definitions pass.
Suitable numeric covariates may be candidates for PMM. Entirely unavailable or
uninterpretable fields, eligibility, exposure and missing modalities are not
imputed to manufacture a cohort. See COMET_MISSING_DATA_PLAN.md. No MICE model,
matching parameters or variable list is frozen by this dictionary.

## Implemented selector and remaining adapters

`select_preindex_measurements.py` is an in-memory, date-level measurement selector
that consumes one patient's mapped feature stream, including original lineage.
It never opens the cluster or raw JDAT. It requires an explicit rule (feature,
window, unit, mapping version, validity version) and ingestion/coverage status.
No clinical map or clinical range is supplied by the generic engine.

It selects the latest observation day in the baseline window before assessing
values. An unusable latest measurement blocks the value rather than triggering
an older-value fallback. Latest-day disagreement blocks selection; equal values
retain all source lineages without claiming that delivery duplicates are resolved.
Repeated identical input rows are idempotent. Unknown event dates block selection;
same-day and future observations are excluded. Unknown availability or known
availability on/after index makes the latest observation unusable. This deliberately
conservative behavior is a proposed extraction contract, not a validated clinical
missing-data strategy. Any alternative requires a new explicit policy and tests.

The current code does not scan Parquet, build indexes, map raw components, split BP,
reconcile patients/deliveries, derive comorbidities/medications, build a cohort, or
run imputation/PSM. Those are the next adapters after the full-source manifests and
restricted component/unit maps are reviewed. The running builder and its hash
inputs are unchanged by this design work.
