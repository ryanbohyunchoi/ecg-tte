# Initial heart-failure trial feasibility screen

2026-09-16. Ryan selected heart-failure/GDMT trials as the initial focus, naming
COMET and PARADIGM-HF. These are candidates, not frozen protocols or implemented
cohorts. No drug-specific patient N or emulated treatment effect is available.

## Candidate contrasts and primary-source anchors

| Candidate | Actual trial contrast | Immediate feasibility gates |
|---|---|---|
| COMET | Carvedilol versus metoprolol **tartrate**, target doses 25 mg twice daily and 50 mg twice daily respectively | Distinguish salt/release formulation and route, establish pre-index systolic HF and EF, baseline history and prior beta-blocker exposure, and comparable prescribing indications. Do not substitute succinate or unspecified metoprolol. |
| PARADIGM-HF | Sacubitril/valsartan versus **enalapril**, on background recommended therapy | Count enalapril specifically; verify pre-index EF, symptoms, natriuretic peptides, renal function, potassium and BP. The sequential active-drug run-in creates a tolerability-selected randomized population that a routine prescribing cohort does not automatically reproduce. |

Primary publications/design sources checked:

- [COMET main report](https://pubmed.ncbi.nlm.nih.gov/12853193/).
- [COMET design](https://onlinelibrary.wiley.com/doi/full/10.1016/S1388-9842%2802%2900025-9).
- [PARADIGM-HF main report](https://www.nejm.org/doi/abstract/10.1056/NEJMoa1409077).
- [PARADIGM-HF investigators' natriuretic-peptide analysis](https://www.jacc.org/doi/10.1016/j.jacc.2019.01.018).

Extract exact eligibility, amendment versions, baseline treatment requirements,
run-in, endpoint definitions and timing from full protocols/supplements before
freezing either emulation. Do not inherit archived trial configs. COMET's main
abstract and design descriptions require reconciliation of the precise EF boundary
before coding. PARADIGM-HF's EF threshold changed by amendment; do not silently pick
one. No published treatment-effect estimates are recorded in this feasibility screen.

## Proposed order of work

Screen both contrasts in one medication feasibility pass. COMET is a proposed
first engineering pilot because it avoids PARADIGM-HF's dual active-drug run-in,
but this is an implementation judgment, not evidence it is clinically feasible.
Select the first implemented protocol after seeing arm counts, formulation
resolution, pre-index HF/EF coverage and endpoint observability, never effect agreement.

The exact comparator is a gate: carvedilol versus metoprolol succinate is a different
contrast from COMET; sacubitril/valsartan versus pooled ACEI/ARB is different from
PARADIGM-HF. If either adaptation is chosen, register it separately and do not claim
close emulation of the named RCT.

## Next count contract (planned, not implemented)

Update 2026-09-17: preliminary lexical medication screen now implemented and
synthetically tested; see RUN_HF_MEDICATION_SCREEN.md. It has not run on H100.
Reviewed terminology mappings, HF eligibility and new-user counts below remain
planned. Screening counts must not be represented as these validated cohorts.

Use the reviewed source snapshot and retain full medication-name/formulation
information for a clinician-reviewed mapping on H100. Ingredient-only RBC mappings
cannot by themselves distinguish tartrate and succinate. Screen medication-ID/name
mapping first; brand/generic, route, combination products, ambiguous names and
conflicting mappings must be explicit. No raw names or row examples enter chat.

For carvedilol, metoprolol tartrate, metoprolol succinate, unspecified metoprolol,
sacubitril/valsartan and enalapril, report:

1. Records and distinct patient keys per reviewed ingredient/formulation bucket.
2. Counts by ordering mode and medication class, separating history and candidate
   prescriptions; status labels must not be used as a retrospective exclusion.
3. Order/start date availability and disagreement for each arm.
4. Patient overlap between arms, same-day competing therapies and available
   medication history; repeated orders are not fills or verified new initiations.
5. Subsequently, linked pre-index HF diagnosis/EF, clinical covariates and usable
   observation history, with criterion-level attrition and unknowns. Medication
   counts alone are not HF-cohort N. Source identity linkage must be validated.

Use a common contemporaneous calendar window and comparable eligibility in both
arms; drug availability and prescribing patterns must not define incompatible eras.
Index, washout length, baseline window, mandatory criteria, missing-date handling
and scheduled-start policy remain open and require trial-specific prespecification.

COMET includes mortality and mortality/admission endpoints. PARADIGM-HF's primary
endpoint is cardiovascular death or HF hospitalization. Current general death-table
presence does not validate cardiovascular cause or hospitalization phenotypes;
do not substitute all-cause mortality for a primary composite without declaring a
different endpoint and selecting its matching published reference. Mortality freshness
and follow-up capture remain gates for both candidates.

The current source supports candidate outpatient **prescribing** records, not
verified pharmacy fills. Retain the agreed primary initiation-based direction and
later discontinuers, subject to ordinary follow-up rules. Sustained-treatment
analysis remains conditional on observable treatment deviations; never require
future refill attainment for baseline entry.
