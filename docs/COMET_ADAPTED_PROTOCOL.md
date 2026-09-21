# Adapted COMET study — selected direction

Decision date: 2026-09-21. The user selected an explicitly adapted observational COMET study. This is the current design direction; it does not freeze all eligibility rules or establish a validated analysis cohort. Earlier draft requirements that conflict with this document are superseded. No new patient exclusions are applied by this document.

## Selected scope

Compare carvedilol with immediate-release metoprolol tartrate using validated prescribing evidence. This is a COMET-inspired prescribing-strategy comparison, not an exact replication of randomized treatment or verified dispensing/adherence.

Retain the selected exploratory starting phenotype:

**(Prior general HF code OR latest strictly prior EF <40) AND no strictly prior diastolic/HFpEF exclusion evidence.**

The current implementation uses DX_DATE, a latest prior echo within 365 days, candidate numeric EF >1 and <40, and whole-patient exclusion for any-diastolic/combined codes or lexical diastolic/HFpEF mentions. The lexical exclusion is not negation-aware. These mechanics reproduce the selected roster but still require clinical validation. General HF codes do not establish HFrEF; describe the population as broadly defined HF/low-EF candidates until phenotype validation supports stronger language. Any change to this rule requires a separately versioned definition and counts.

The starting roster is 6,530 (4,017 carvedilol; 2,513 metoprolol tartrate). It is not a target sample size or a final eligible denominator. No restriction is selected to recover the original trial effect or preserve a desired N.

## Eligibility and index decisions

| Item | Current decision or remaining work |
|---|---|
| Drug identity | Validate ingredient, formulation, route, order class and cancellation/reconciliation handling. Unknown treatment assignment cannot silently pass. |
| Index date | First qualifying study-drug prescription under the eventual common rules; current earliest-order dates remain exploratory. Eligibility, assignment and follow-up must share time zero. |
| Prior beta-blockers | Audit route-specific dated/undated history and baseline observation before choosing a washout. Neither 365 days nor the original trial's two-week rule is adopted automatically. |
| HF definition | Retain the selected broader rule above as an explicit adaptation. Do not substitute imputed EF for eligibility evidence. |
| Age/calendar/observation | Adult restriction is proposed; validate DOB and source coverage, then freeze common rules for both arms. No required future encounter or refill. |
| Contraindications and acute instability | Map measurable diagnoses, vitals, procedures and medications; determine which are mandatory and specify lookbacks. Do not automatically remove everyone with a broad proxy code. |
| NYHA, background therapy and stability | Assess capture and report unknowns. Decide explicitly whether to require, adapt or omit each original criterion; absence of documentation is not normality or eligibility. |
| Other original exclusions | Review each individually, including source availability and clinical meaning. This document is not blanket authorization to ignore exclusions. |
| Unknown mandatory criterion | Stop clinical eligibility for that criterion unless a versioned adaptation is explicitly agreed. Do not silently treat unknown as pass. |

The original design lists adult symptomatic HF, ventricular-function criteria, prior cardiovascular admission, stable background therapy and detailed exclusions. Its rules are the reference for an explicit adaptation register, not automatically executable filters. See the [COMET design, sections 2.1–2.2](https://onlinelibrary.wiley.com/doi/full/10.1016/S1388-9842%2802%2900025-9).

A later refill must not become an initiation merely because HF or eligibility is documented later. If a switching or prevalent-user question is needed, define it separately. Prescriptions do not establish continuous use, fills or an exposure-free period.

## Next evidence gate: criterion-level feasibility

Produce a versioned eligibility register with one row per original criterion: source definition, adapted rule, source fields, time window, validation status and missing-data policy. For each candidate and criterion, retain pass/fail/unknown with provenance on H100. Report aggregate counts by arm and criterion, overlaps and sequential attrition under an explicitly stated ordering. Audit criteria before freezing the executable protocol; never use outcomes for this selection.

The completed beta-history screen is one input: 3,787 candidates have no named generic lead in prior365 days; 3,269 also have no undated generic or unresolved prior/undated lead, retaining same-day flags. These are not validated new users. Review the 598 medication catalog combinations locally for route/formulation mapping. The failed lab extension remains unavailable as a complete snapshot; neither silently bypass its status nor assume missing lab values are normal.

## Analysis sequence

1. Validate medication/phenotype mappings and audit eligibility/observation feasibility.
2. Freeze the adapted eligibility, index, outcome, follow-up and estimand contracts; materialize and verify per-arm attrition.
3. Extract traceable pre-index covariates, assess units/missingness and finalize the imputation plan.
4. Fit propensity scores, match and assess overlap/balance before estimating effects. PSM does not substitute for eligibility or resolve unknown treatment timing.

A stricter COMET-aligned sensitivity cohort can be specified separately where data support its requirements. Do not call it an exact emulation if mandatory criteria remain unmeasured. The current main direction remains adapted; no switching between definitions based on results.
