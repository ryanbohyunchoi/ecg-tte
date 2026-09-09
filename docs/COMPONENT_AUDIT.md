# Component investigation and validation matrix

**Status:** initial code-grounded risk inventory and investigation plan, 2026-09-09.
This is not a completed clinical/statistical audit. No legacy cluster results have
been independently reproduced. The new implementation does not yet exist.

## 1. Findings to carry forward from v1

Paths below point into the immutable snapshot. Findings marked code-confirmed mean
the behavior is present in source, not that its empirical impact has been measured.

| Finding | Evidence | Required replacement behavior |
|---|---|---|
| Future adherence used in design/adjustment — code-confirmed. | [Adherence builder](../archive/2026-09-09-legacy-v1/scripts/cohort_utils.py), `compute_adherence_metrics_generic`; [Stage 3](../archive/2026-09-09-legacy-v1/scripts/stage3_filter.py) filters future refill counts and early discontinuation; [Stage 4](../archive/2026-09-09-legacy-v1/scripts/stage4_analyze.py) includes 90/180-day post-index counts in PS candidates. | Baseline-only design/adjustment; explicit longitudinal strategy if future adherence is relevant. |
| Medication-list history treated as initiation evidence — code-confirmed; validity unverified. | [Drug builder](../archive/2026-09-09-legacy-v1/scripts/build_drug_master.py) describes historical entries as usable; generic arm assignment uses first observed record. | Validate event classes and prior observation; distinguish first recorded use from initiation. |
| Malformed raw rows can disappear — code-confirmed. | [Drug builder](../archive/2026-09-09-legacy-v1/scripts/build_drug_master.py), `_BAD_LINES_KWARG` skips bad rows. | Exact parse accounting, restricted quarantine, explicit failure/promotion policy. |
| Identifier normalization strips leading letters — code-confirmed; collisions not established. | [Shared utilities](../archive/2026-09-09-legacy-v1/scripts/cohort_utils.py), person/ECG/echo loaders. | Namespaced identity map with tested one-to-one transformations and collision reports. |
| Configured criteria can be informational or skipped — code-confirmed. | [Stage 1](../archive/2026-09-09-legacy-v1/scripts/stage1_build_pool.py) constructs exclusion flags; Stage 3 has a flat merge and a fixed cardiac exclusion list. | Typed executable criteria; unknown/unsupported required criteria stop the trial. |
| Config/runtime endpoint and window mismatch — code-confirmed. | [PARADIGM config](../archive/2026-09-09-legacy-v1/configs/paradigm_hf.yaml) versus [wrapper](../archive/2026-09-09-legacy-v1/trials/paradigm/run_stage4.sh), Stage 1 death horizon, Stage 3 ECG default. | One resolved protocol drives execution and reference selection; test every effective value. |
| Administrative censoring is not fully source-grounded — code-confirmed. | Stage 1 infers an end date from death records; legacy death columns do not consistently apply an explicit earlier censor date to observed deaths. | Source/domain cutoff contract; event and follow-up censoring tested together. |
| Denominator audit need not equal analytic denominator — code-confirmed. | Stage 4 computes strict masks but runs the main ladder on full/imputed frames and falls back when the strict mask is empty. | Declared/hashed analytic cohort and estimand per result; no empty-mask fallback. |
| Matching can miss available controls — code-confirmed. | Stage 4 `_greedy_match` searches only `2*k` nearest controls before considering whether they have been used. | Algorithm specification and adversarial tests for support, replacement, ties, order, ratio, and exhaustion. |
| Propensity variable selection optimizes treatment AUC — code-confirmed. | Stage 4 `LogisticRegressionCV(scoring='roc_auc')`. | Mandatory clinical confounders plus outcome-blind balance/retention-based development policy. |
| Absent checkpoint projector can become random — code-confirmed. | [ECG loader](../archive/2026-09-09-legacy-v1/scripts/stage2_embed.py), `load_bcl_encoder`. | Mandatory component checks; fail instead of producing plausible random representations. |
| ECG caches depend mainly on existing file names — code-confirmed. | Stage 2 skips existing fileID outputs. | Input/preprocessing/checkpoint-aware cache identity and validated atomic outputs. |
| Current Stage 4 no longer executes the original ECG/hybrid hypotheses — code-confirmed. | Stage 4 `main` invokes conventional methods; ECG functions remain unused. | Registry-driven method execution with expected result/status rows. |
| Meta-analysis joins obsolete labels — code-confirmed. | [Stage 5](../archive/2026-09-09-legacy-v1/scripts/stage5_meta.py), `_match_method`. | Stable method IDs and schema validation; plot titles are presentation only. |
| Run wrappers can mistake stale output for success — code-confirmed. | [Full PARADIGM wrapper](../archive/2026-09-09-legacy-v1/trials/paradigm/run_paradigm_full.sh) checks existence after some commands and auto-pulls code. | Immutable source revision/run directory; exit status plus invocation-bound manifest and output validation. |
| Historical benchmark results require revalidation — documented, not independently verified. | [Old task log](../archive/2026-09-09-legacy-v1/tasks/todo.md) describes 27/32 runs and a missing required-ICD gate. | Treat historical outcomes as development evidence; rebuild all new protocols from source. |

The old binary flags, simple imputation bounds, matched-set Cox choices, and
reported balance need methodological review. A historical note saying a behavior
was fixed is not sufficient evidence of validity in the restarted benchmark.

## 2. Full component acceptance matrix

Each audit record should include owner/reviewer, source/code version, evidence
artifact, unresolved issues, severity, status, and date. Every row below starts as
**pending**; root syntax validation is not a substitute for these gates.

| Component | Questions to answer | Required evidence/test before promotion |
|---|---|---|
| Extract population | Who was selected into each JDAT delivery, and using which dates/events? | Extract specification; cohort overlap and selection diagram; transport limitations. |
| Parsing and source versions | Can records be read without silent loss or changing semantics across shards? | Full row accounting, encoding/delimiter fixtures, schema drift report. |
| Identity and joins | Are keys stable and joins clinically valid? | Collision, duplicate, orphan and row-multiplication tests; reviewed mapping authority. |
| Observation history | What baseline and outcome capture is defensible? | Source coverage by domain/time; tested observation boundaries and sensitivity plan. |
| Exposure | What evidence defines initiation/strategy adherence? | Reviewed order/history/admin/dispense classes, drug mapping tests, time-zero examples using synthetic records. |
| Eligibility | Is every criterion truly executed? | Criterion-to-source matrix; positive/negative/boundary cases and attrition totals. |
| Outcomes | Does the phenotype correspond to the reference endpoint? | Clinical review, source linkage/QC, incident/recurrent/composite and competing-event tests. |
| Time zero and censoring | Are selection/assignment/follow-up synchronized? | Timeline fixtures including same-day events, early death, grace periods, loss of capture, administrative cutoff. |
| Clinical covariates | Are values pre-index, correctly mapped, and retained end to end? | Feature dictionary with provenance; unit/window tests; no missing-column fallback. |
| Missing data | Are absence, missingness, and structural nonavailability distinguished? | Missingness report; imputation diagnostics, distribution checks, simulation of interval coverage. |
| ECG input/encoder | Do vectors represent the intended signals and frozen model? | Lead/unit/shape QA; strict checkpoint load, identity, determinism, collapse and overlap tests. |
| Structured EHR encoder | Do mapped sequences retain clinically relevant information? | Vocabulary/unknown-token coverage, numeric-event handling, cutoff/order/truncation tests. |
| Notes encoder | Are text and model outputs temporally valid and stable? | Version cutoff, copied-note, chunk/pooling, forbidden-input and local-output tests. |
| Echo encoder | What imaging/report information is actually represented? | Asset/view/QC inventory, study-level aggregation, pre-index timing and text-overlap audit. |
| Fusion | Is any modality dominating due to scale, size, or duplication? | Normalization/dimension ablations; fit-partition provenance; missing-modality behavior. |
| PSM and distances | Are target, caliper, replacement, constraints, and candidate search correct? | Known-match/adversarial fixtures, treated retention, balance, overlap, order sensitivity. |
| Weighting | What population do weights target, and is positivity plausible? | Weight derivation tests, normalization/extreme tails, ESS, weighted balance, valid variance. |
| Outcome estimation | Is the model estimating the declared contrast? | Known-answer/simulation checks; PH diagnostics, marginal/conditional distinction, cluster handling. |
| Denominators and estimands | Are methods compared on the same target rather than differently selected patients? | Cohort hashes, common-anchor audit, modality/retention flow and population characteristics. |
| Reference extraction | Is every published number aligned and correctly oriented? | Independently reviewed reference cards including endpoint, time, effect scale, and CI. |
| Trial comparison | Are agreement metrics and paired uncertainty correct? | Analytic toy examples, zero/null/noninferiority cases, family-dependence and multiplicity simulations. |
| Failure handling | Can missingness/failure masquerade as success or an omitted unfavorable trial? | Injected failures, mandatory status rows, source-infeasible versus estimator-failed distinction. |
| Orchestration and caching | Can interrupted/stale/mixed-version runs contaminate output? | Atomic-write, resume, hash-invalidation, explicit-exit and output-schema tests. |
| Privacy/output boundary | Can logs/reports disclose patient information? | Synthetic identifier/text canaries, sanitized error tests, aggregate release review. |
| Reproducibility | Can an independent analyst reproduce the same cohort and results? | Pinned dependencies/configs/assets; clean-environment synthetic run and controlled cluster rerun. |

## 3. Review sequence

Work from source parsing/identity through timing and clinical definitions, then
covariates and baselines, then representations and multimodal methods, then
cross-trial inference. Do not address only software correctness: a deterministic
pipeline can deterministically answer the wrong causal question.

Use synthetic data to prove mechanics, aggregate real-data profiling to establish
source behavior, and clinical/statistical review to justify definitions. Patient-level
spot checks, when necessary, occur inside the approved environment with qualified
reviewers; only conclusions and approved aggregates leave that environment.

Define explicit failure thresholds during each component's development, record
their basis, and freeze them before evaluation. The plan intentionally avoids
inventing universal acceptable missingness/event-count/overlap cutoffs without
knowing the sources, estimators, and trial targets.
