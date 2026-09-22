# COMET outcomes and follow-up: Track 2 handoff

2026-09-22. **Proposal and source-audit implementation, not a frozen endpoint or completed H100 validation.** This outcome track uses the adapted prescribing comparison and fixed candidate anchors supplied by Track 1. It does not change medication evidence, eligibility, the 32 covariates, MICE, or PSM.

## Verified trial reference and proposed endpoint candidates

The [COMET design paper](https://onlinelibrary.wiley.com/doi/full/10.1016/S1388-9842%2802%2900025-9), sections 3 and 5, and [main trial report](https://pubmed.ncbi.nlm.nih.gov/12853193/) identify **all-cause mortality** and **time to all-cause death or all-cause admission** as co-primary endpoints. The trial followed participants after treatment discontinuation; its loss-to-follow-up rule was last follow-up. Those trial rules do not supply an administrative end or a loss-to-follow-up rule for our JDAT data. All-cause mortality is a proposed first candidate because it avoids admission episode classification, conditional on verified death ascertainment. The composite is a separate candidate that needs validated inpatient capture and episode definitions. Neither is selected or estimable yet.

The existing baseline covariate counting inpatient-flagged encounters in the *prior* 365 days does not validate a *post-index* hospitalization endpoint. Its recorded-zero policy is not a mortality ascertainment policy.

## What is known locally and what the audit checks

The complete clinical snapshot is reported to contain a 2025 Patients source with `DEATH_DATE`, 2025 and 2026 hospital and outpatient encounter deliveries, and no 2026 Patients source. A delivery name is not an event-capture end date. The source audit reads the preserved tables and a supplied roster's patient key/index day, with no treatment arm column. It writes a private per-patient QC file on H100 plus a pooled aggregate summary marked restricted until reviewed.

`audit_comet_outcome_sources.py` checks:

- Patient row presence, missing/unparseable/conflicting death dates, death dates before/on/after index, death before birth, and death-date calendar distribution. **No recorded death date remains unknown survival status.**
- Encounter date parseability and calendar distribution separately by delivery; pre/index/post-index rows; dated encounters after a recorded death; discharge before admission or after a recorded death for review.
- Post-index inpatient-flagged, dated, keyed rows as **candidates only**, duplicate rows across deliveries, encounter keys with conflicting admission dates, missing inpatient keys, and adjacent episodes that could represent transfers.
- Snapshot/roster fingerprints and a fresh private output directory. Input changes invalidate counts; failures leave `counts_valid=false`.

It cannot verify death registry linkage, completeness of deaths outside this health system, update lag, coverage start/end, true admission setting, capture outside participating facilities, transfers, discharge disposition, same-day event ordering, or whether repeated rows represent one stay. Aggregate maxima show recorded source dates only. The current roster may be provisional while Track 1 rebuilds it; rerun after its final patient/index manifest is agreed.

## Proposed patient/index-to-outcome interface

A later, separately versioned attachment should consume an immutable, hash-checked `patient_key`, `index_day`, and cohort-version manifest from Track 1. One row per eligible patient/index should include:

| Field | Proposed meaning / required state |
|---|---|
| `outcome_contract_version`, source hashes | Exact phenotype, source snapshots, mapping and code version. |
| `time_zero`, `index_day`, `same_day_policy` | Eligibility, assignment and follow-up align. Same-day chronology requires source validation; otherwise unresolved. |
| `event_type`, `event_day`, `event_source`, `event_provenance` | First qualifying event after time zero, with death/admission components separate for a composite. Null is allowed only with an explicit ascertainment status. |
| `coverage_start`, `coverage_end`, `coverage_basis`, `coverage_status` | Externally justified observable interval and its evidence. Last encounter is not automatically a coverage end. |
| `censor_day`, `censor_reason`, `administrative_end`, `horizon_day` | Computed only after coverage and horizon are frozen; no silent end based on file delivery or missing death date. |
| `event_status`, `unassessable_reason` | Event, observed event-free to a defensible censor point, or unassessable; never convert missing `DEATH_DATE` into survival. |
| `quality_flags` | Date conflict, post-death encounter, duplicate/transfer ambiguity, source inconsistency and same-day uncertainty. |

The attachment must reject duplicate patient/index keys, event before time zero, event after censor, an index after justified coverage end, unresolved mandatory source status, and missing coverage support for purported event-free follow-up. It must preserve all candidate entrants; it cannot require a future visit, later refill, or recorded survival to enter the cohort. For a sustained-treatment analysis, deviation censoring and IPCW would be a distinct contract, after validated medication-supply evidence and time-varying covariates.

## Decisions for Ryan and Track 1 before attachment

1. Confirm whether death date is registry-linked or health-system-only, its data cutoff/update lag, and whether an independently documented coverage end exists. Audit date conflicts and post-death records before accepting all-cause mortality.
2. Choose an emulation endpoint, risk horizon, calendar administrative end, estimand and effect scale with source feasibility in hand. COMET's event-driven trial follow-up is not automatically the observational horizon.
3. If considering the composite, review `INP_YN`, admission/discharge fields, key uniqueness, cross-delivery duplicates, transfers and capture. Specify first admission versus recurrent events, observation boundaries, death ordering and same-day rules.
4. Provide the final versioned cohort/index manifest from Track 1. Any feasibility counts from the old 6,530 roster are provisional; no outcome-based cohort changes.
5. Coordinate any outcome variables for **analysis-stage** MICE only after the outcome contract is frozen. Keep design-stage imputation selection and every baseline representation outcome-free, and retain an outcome-free sensitivity.

No treatment-stratified outcome results, treatment effect, endpoint freeze, patient data or cluster execution were produced by this local work. The shared decision register and task list remain for Track 1 integration as requested in `handoff.md`.

## 2026-09-22 source-audit evidence returned

Ryan ran commit `e7d82a2` against the provisional 6,530-person roster and clinical snapshot. The audit completed in 130.774 seconds with valid counts at `/mnt/raid0/rbc58/ecg-tte/audits/comet-outcome-source-tHnSeYRl/report`. Roster SHA-256 was `8a48b28ca008dd0c15cb32e475ccb2569b6d5b01cde4b59849a7629b4ab3d8a2`; clinical manifest SHA-256 was `d95690d6ce554eeca90628d3a95f285b09c4be7da8c108237aaba80ff5c93117`.

Observed pooled facts:

- 2,261/6,530 (34.6%) had one recorded post-index death date, 4,268 (65.4%) had no recorded death date, and one had a death date before index. The latter is a blocking temporal inconsistency for that patient/index, not an automatic exclusion or corrected date.
- The only patient table was the 2025 delivery: 103,111 rows had a parsed death date and 776,485 did not. Recorded death years include implausibly early values beginning in 1913 and end in 2025. Calendar validity alone does not establish clinical validity, linkage provenance or complete ascertainment.
- Encounter sources include 2026 records, but there is no 2026 Patients source in the completed clinical snapshot. The 2026 encounter deliveries are concentrated in 2025–2026, whereas recorded deaths end in 2025. This demonstrates asynchronous source freshness; it does not identify the death-source cutoff within 2025.
- 4,572/6,530 (70.0%) had at least one post-index, dated, keyed `INP_YN=1` candidate. There were no missing keys, conflicting admission dates by key, invalid discharge-before-admission rows, or exact duplicate encounter identities under this audit's definitions.
- 669 patients had 881 adjacent distinct-key episode pairs within one day of discharge, so transfer/episode collapse can materially affect a hospitalization endpoint.
- Nineteen patients had 28 encounter rows after a recorded death, and 65 had 75 hospital discharges after a recorded death. These may include source errors, administrative discharge timing, linkage problems or death-date problems; they require review and do not justify rewriting dates.

Consequences: a missing death date cannot be converted to survival, and encounter data through 2026 cannot extend mortality follow-up beyond the independently verified death-source coverage end. All-cause mortality remains a candidate but is blocked on death provenance and cutoff. The admission composite remains separately blocked on episode semantics. These pooled results must be rerun on Track 1's final roster; no outcome-based eligibility change is authorized.

A second pooled audit, `audit_comet_followup_feasibility.py`, now reports index-year counts, death-time bins, first/last inpatient candidate-time bins, last-any-encounter landmarks, and recent month-level source density. Future encounters are explicitly audit signals and never become eligibility, survival proof, censoring or a complete-observation claim.
