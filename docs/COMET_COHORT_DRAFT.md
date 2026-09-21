# COMET cohort specification — design draft

Current design direction: [explicitly adapted COMET study](COMET_ADAPTED_PROTOCOL.md), selected 2026-09-21. Conflicting earlier proposals below are superseded; no additional eligibility filters are frozen.

2026-09-21. Proposed, not frozen; no eligible cohort, matching or effect estimate
is produced by this document. The existing first-order anchors are feasibility
anchors only. Source semantics, phenotype, observation and endpoint gates remain
open. Keep the running source-conversion implementation unchanged.

## Trial reference and emulation scope

The original trial compared carvedilol with immediate-release metoprolol tartrate,
with target doses 25 mg twice daily and 50 mg twice daily respectively. It enrolled
symptomatic chronic HF patients (NYHA II–IV) with previous cardiovascular admission
and reduced EF, on background diuretics and ACE inhibition unless not tolerated.
These are trial criteria, not facts established in our extracts. The main report
abstract says EF <35%; the design/later trial reports describe <=35%. Resolve the
exact protocol boundary before freezing; retain a separate EF=35 count meanwhile.
Do not infer eligibility from the exploratory (1,35] band.

Primary trial sources:
- Main report: https://pubmed.ncbi.nlm.nih.gov/12853193/
- Design: https://onlinelibrary.wiley.com/doi/full/10.1016/S1388-9842%2802%2900025-9
- Trial investigators' later description of eligibility:
  https://www.jacc.org/doi/10.1016/j.jacc.2005.11.069

The design extraction must reconcile the full inclusion/exclusion criteria,
including prior cardiovascular admission window, treatment stability, NYHA,
contraindications and prohibited drugs. This document is not an exhaustive RCT
protocol transcription. Published treatment-effect numbers are deliberately not
inputs to cohort or feature code.

## Two separately named candidate populations

| Candidate | Proposed evidence before index | Interpretation and gate |
|---|---|---|
| `comet_ef_defined_draft` | Clinically supported HF plus latest prior measured, validated percent EF below the reconciled trial boundary, within proposed 365 days | Candidate for closer alignment. Unsupported mandatory RCT requirements stop a close-emulation claim; any relaxation needs an explicit adapted protocol. |
| `comet_diagnosis_adapted_draft` | A separately validated systolic/combined HF phenotype when recent EF is unavailable; retain EF-observed and EF-unavailable strata | Explicit adaptation, not equivalent to numeric EF eligibility. A generic I50 code alone is insufficient to establish HFrEF. |

Do not union either population with all patients having low EF or any HF code to
increase sample size. Define handling of a recent EF above threshold, stale EF,
ambiguous units and disagreement before running the cohort. Latest invalid or
missing EF must not trigger a search for an older qualifying EF. Same-day evidence
is separate. No imputed EF or future diagnosis can establish eligibility. ICD9,
historical ICD mappings and non-I50 HF families still need phenotype review.

## Proposed exposure and index rules

1. Map medication IDs, ingredient, formulation, route and order classes on H100.
   Carvedilol must have the intended formulation; metoprolol succinate and unclear
   metoprolol formulations are not tartrate. Lexical buckets are discovery only.
2. Use outpatient prescribing as the observable strategy if source review supports
   it. ORDER_INST is a candidate order timestamp, not confirmed dispensing or
   treatment start. START_DATE is retained independently; no fallback is frozen.
   Reconciliation, cancelled orders, print/normal classes and discharge prescriptions
   require explicit rules. ORDERING_MODE does not establish encounter setting.
3. Proposed new-prescribing lookback: 365 days for any beta-blocker prescription,
   not just the two trial drugs. This is an emulation proposal, not COMET's original
   washout criterion. Its implementation is blocked on the complete drug map and
   adequate historical source coverage. Absence of records is not continuous
   enrollment, adherence or lifetime treatment-naivety.
4. Evaluate candidate orders chronologically against the same pre-index eligibility
   and history rules in both arms. Select at most one first qualifying index per
   patient across both arms; do not use separate first-ever arm anchors as two trial
   entries. Reject unresolved same-day competing-arm orders with an explicit reason.
   Later switching never retroactively excludes someone at baseline.
5. Proposed adult restriction (>=18) and common calendar period require source
   coverage review. Compute age using DOB at index, not age recorded at a later echo.
   Common calendar boundaries must use coverage/clinical rationale, not effect fit.
6. Freeze a baseline observation rule after auditing encounter history and source
   coverage. Report prior encounter counts and first/last observed dates over 365
   days. Do not claim one encounter proves a full observable year, or require a
   future encounter to qualify. No numerical visit threshold is frozen here.

Eligibility, assignment and follow-up start must share time zero. All baseline
measurements use strict prior days in the first implementation; source-validated
within-day ordering can be a separately versioned extension. Hospital/ED history
can inform baseline risk without requiring inpatient treatment assignment.

## Estimand, follow-up and endpoint gates

Proposed observational contrast: initiation of the two prescribing strategies,
following patients regardless of subsequent recorded discontinuation/switching.
This is an analogue of a treatment-policy strategy, not randomized assignment or
verified medication consumption. For 1:1 matching, the candidate target is the
matchable carvedilol-initiator population; report selection/overlap losses and
resolve how matching across imputations affects that target before freezing.
Matching ratio, replacement, caliper and model are still proposed, not defaults
in executable code.

All-cause mortality is a candidate aligned endpoint. The available 2025 Patients
file's DEATH_DATE does not establish complete death capture, observation end or
2026 refresh. Do not classify absent death dates as known survival to extraction.
Follow-up horizon, administrative end, loss-to-follow-up, death linkage and event
validation are blocking decisions. A required future visit creates selection and
must not be used as a shortcut. An on-treatment analysis would need separately
validated exposure deviations and censoring methods; orders cannot establish PDC.

## Required design outputs before PSM

- Versioned drug/phenotype/unit maps, source dates and exact snapshot identifiers.
- Per-arm sequential attrition with overlapping QC flags kept separate from
  mutually exclusive exclusion reasons; patient-level reasons remain on H100.
- Calendar overlap, baseline observation, eligible patient counts and exposure ties.
- Covariate availability, invalidity and timing by arm/year; no arm-specific outcome
  exploration or published-effect optimization during design.
- Clinical variable-role review and explicit decision for each mandatory unavailable
  criterion: stop or name an adaptation, never silently omit it.
- Frozen cohort/endpoint/estimand/missing-data contracts before effect estimation.

The synthetic measurement selector in `scripts/select_preindex_measurements.py`
is only a baseline-selection component. It does not implement the phenotype,
new-user index, mortality follow-up, imputation or matching.
