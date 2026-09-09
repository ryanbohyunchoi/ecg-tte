# Restart plan: multimodal representations for target trial emulation

**Date:** 2026-09-09
**Status:** proposed research and engineering plan; not a frozen statistical analysis plan.
**Completed now:** legacy archive, initial source/code review, and this planning package.
**Not completed:** raw JDAT inspection, validated new protocols, replacement estimators,
encoder selection, or a new benchmark run.

## 1. Research question and scope

Can pre-treatment representations learned from ECGs, structured EHR events,
clinical notes, and echocardiography improve agreement between observational
target-trial emulations and corresponding randomized-trial effects, compared with
a strong conventional PSM baseline?

The scientific result may be improvement, no improvement, or deterioration. The
goal is a defensible benchmark that can distinguish those outcomes. Recovering a
published effect is evidence about agreement; it is not by itself proof that an
estimator has removed confounding. Differences in populations, treatment versions,
follow-up, outcome measurement, and sampling uncertainty also matter.

The linked RCT-DUPLICATE study provides a useful design reference: feasibility-led
trial selection, prespecified emulations, PSM, and multiple agreement measures.
It does not establish that embeddings improve adjustment. Our contribution will
be a paired comparison of representation strategies within carefully aligned
emulations. [JAMA study](https://jamanetwork.com/journals/jama/fullarticle/2804067)

The old 32 configs are not a mandated roster. In particular, the paper includes
PRONOUNCE, while the legacy repository includes COMET and lacks PRONOUNCE. Rebuild
the candidate list from primary trial materials and raw-data feasibility.

## 2. Research hypotheses

Keep information source and adjustment algorithm as separate experimental axes.
An ECG vector can be used in a propensity model, direct matching distance, or
outcome model; those are different methods and must have separate identifiers.

| Representation | Questions to test | Important comparison |
|---|---|---|
| AI-ECG | Does waveform information improve balance/effect recovery beyond structured clinical covariates? | PSM plus waveform features versus the same PSM; also compare conventional ECG intervals. |
| AI-EHR structured | Does a longitudinal encoder such as CLMBR-T improve on clinical features and code-history summaries? | Clinical PSM, expanded/high-dimensional structured baseline, then encoder augmentation. |
| AI-EHR notes | Do pre-index notes add information not present in structured records? | Notes-based representation versus a simple text baseline and structured PSM on the same note-available cohort. |
| AI-ECHO imaging | Do pre-index images/videos contribute beyond measured EF and other structured echo variables? | Imaging representation versus structured echo covariates in the same echo-available cohort. |
| AI-ECHO reports | Does report text add value? | Separate from imaging and account for overlap with the general note corpus. |
| Multimodal | Are the information sources complementary? | ECG+EHR, ECG+echo, EHR+echo, then all available modalities. |
| Hybrid adjustment | Does combining structured PS constraints and representation similarity outperform either alone? | Identical starting cohort, treated target population, endpoint, and outcome estimator. |

Do not run every combination immediately. The method registry will label each
entry as proposed, development, frozen confirmatory, or exploratory. The first
embedding comparison should be the simplest available addition to a validated
PSM baseline; ECG is a candidate because legacy infrastructure exists, not because
its benefit is established.

## 3. Data foundation: raw JDAT first

The detailed investigation is in [RAW_JDAT_INVESTIGATION.md](RAW_JDAT_INVESTIGATION.md).

Build a lineage-preserving data layer:

```text
Immutable raw JDAT extracts + source specifications
    -> versioned source adapters, parsing/QC and identity reconciliation
    -> normalized events with clinical time, availability time, and provenance
    -> trial eligibility, treatment index, follow-up, and endpoint tables
    -> pre-index clinical features and modality-specific input snapshots
    -> frozen representations and registered adjustment methods
    -> per-trial estimates/diagnostics -> paired benchmark evaluation
```

Raw data may be richer than the old extract, but that must be measured. Compare
raw-versus-OMOP coverage in a restricted reconciliation study and explain losses,
duplicates, and mapping differences. Do not silently union the two systems.

CLMBR-T expects standardized coded events, with a MEDS input representation in its
current model documentation. Raw-source priority is compatible with a dedicated
JDAT-to-standard-vocabulary adapter; it does not require reusing old OMOP tables.
Measure unmapped and out-of-vocabulary events before treating its output as a
complete EHR representation. [CLMBR-T model card](https://huggingface.co/StanfordShahLab/clmbr-t-base)

**Gate:** no trial engine may consume a source until its schema, identity,
timestamp semantics, record classes, and QC accounting are documented.

## 4. Trial selection and protocol registry

### Candidate selection

Screen a broad candidate roster across therapeutic areas, treatment effect
directions, and null/noninferiority settings. Record every candidate considered
and the reason it enters or leaves the benchmark. Selection must be based on
measurability, confounder coverage, overlap, independent clinical considerations,
and statistical feasibility, not the new estimated effect.

Use three protocol tiers, assigned before effects:

- **Tier A: close emulation.** Treatment/comparator, population, endpoint,
  ascertainment, follow-up, and effect interpretation are sufficiently aligned.
  This is the candidate primary benchmark.
- **Tier B: explicit adaptation.** Comparator substitution, endpoint proxy,
  unavailable run-in, or substantial transport difference changes interpretation.
  Report separately; do not use Tier B success to claim exact RCT recovery.
- **Tier C: infeasible.** Required information, overlap, or event precision is
  insufficient. Preserve the failure reason; do not manufacture a substitute.

A smaller credible benchmark is preferable to forcing all legacy trials into the
analysis. Cohort counts alone are insufficient: feasibility includes events,
follow-up, matched retention/effective sample size, and modality coverage. Use
pooled outcome information for design-stage power work, keeping treatment-stratified
new outcomes hidden until protocol freeze.

### Per-trial protocol contract

Each versioned protocol must explicitly specify:

1. RCT identifier, primary publications/protocols, arm orientation, dose/formulation,
   superiority/noninferiority hypothesis, and reference analysis population.
2. Trial and emulation eligibility side by side, including unavailable criteria.
3. Source evidence for each treatment strategy, setting, index rule, washout,
   prior observation requirement, switching, same-day exposure ties, and re-entry.
4. Target population and causal estimand; explain how the matched treated
   population relates to the original RCT population.
5. Exact alignment of eligibility, treatment assignment, and follow-up start.
6. Endpoint phenotype, incident/recurrent handling, composite components,
   competing events, adjudication/proxy limitations, and code-set version.
7. Follow-up horizon, censoring, death capture, treatment discontinuation, and
   the intended analogue of ITT or on-treatment analysis.
8. Clinical confounder set, windows, missing-data rules, modality availability,
   and same-day timing policy.
9. Estimator, effect scale, variance calculation, diagnostics, and failure rules.
10. Published reference estimate, interval, scale, endpoint, horizon, and direction,
    verified independently from the phenotype specification.
11. Sensitivity analyses, control outcomes, feasibility thresholds, and reviewer.

Reference estimates belong in an evaluation registry unavailable to the
representation/matching selection code. Protocol design necessarily reads RCT
materials, so this is separation of computation and tuning, not a claim that
researchers are unaware of published findings.

### Time-zero safeguards

The default design uses only information available by treatment assignment for
eligibility and baseline adjustment. Do not require future refills, exclude early
adverse discontinuation, or put post-index adherence into baseline propensity
models. A grace-period strategy requires an explicit alternative design and
appropriate analysis; it cannot be implemented as retrospective cohort filtering.
Synchronizing eligibility, treatment assignment, and follow-up is central to
avoiding self-inflicted time-zero bias. [Hernán et al.](https://pubmed.ncbi.nlm.nih.gov/27237061/)

Do not assume the first observed medication entry is lifetime initiation. Distinguish
new prescribing from new dispensing and historical medication reconciliation.
Observation through a health system is not equivalent to continuous insurance
enrollment. Establish what the source can support and label the target accordingly.

## 5. A strong conventional baseline

Build and verify the clinical PSM baseline before representations. Include
prespecified confounders that matter clinically, calendar time, care utilization,
and reliable available labs/vitals. Do not discard important confounders merely
because a treatment-prediction model assigns them zero coefficients.

Create a trial-specific causal diagram or equivalent variable-role review before
selecting features. Pre-treatment does not automatically mean safe to adjust for:
review colliders, strong treatment instruments, indication proxies, and variables
that effectively encode the assigned therapy. Rich embeddings can contain these
signals too. Predictive quality and embedding similarity do not establish the
exchangeability assumptions needed for causal interpretation.

Proposed conventional comparisons:

- Crude outcome comparison on the full declared cohort, without arbitrary arm
  downsampling; descriptive context only.
- A clinical structured PSM baseline with an explicit PS model, scaling,
  matching ratio/replacement/order, overlap policy, and caliper units.
- An expanded structured/code-history or high-dimensional PSM baseline, to test
  whether gains reflect richer inputs rather than representation learning.
- Weighting and a suitable doubly robust estimator as complementary analyses
  after estimand alignment and independent validation. IPTW is not PSM and need
  not target the same population as matching.

Select PS hyperparameters with prespecified, outcome-blind balance and retention
criteria on development data. Treatment AUC alone is not the objective. Fix the
selection budget across comparable representation variants. Do not retain the old
raw threshold or LASSO selection procedure simply because it is already coded.

Use clinically meaningful missingness categories: not measured, not captured,
invalid, explicitly absent, and observed present. A missing feature column is an
adapter/schema failure when mandatory; an individual missing value is a data state.
Zero-coded absence of a diagnosis is not automatically proof of disease absence.

Multiple imputation is a candidate, not a default inherited from v1. Validate
distributions, bounds, categorical handling, convergence, and pooled uncertainty.
Choose the number of imputations using missing-information and Monte Carlo error
diagnostics. Never impute treatment assignment, eligibility facts, clinical
outcomes, or an entirely unavailable waveform/image modality to qualify a patient.

If an analysis-stage imputation model uses outcomes for valid effect estimation,
separate it from outcome-blind cohort/method development and pre-index embedding
construction. Apply the same frozen imputation procedure to paired methods; retain
an outcome-free sensitivity. Review match-within-imputation and pooling behavior
specifically for the chosen estimator.

**Gate:** synthetic known-answer tests, source-grounded pilot validation,
reasonable overlap/balance, reproducible estimates, and verified uncertainty.
Matching fails explicitly when support is inadequate.

## 6. Representation and fusion study

### Shared representation contract

Every vector is keyed by patient, trial-episode/index, modality, source snapshot,
pre-index cutoff, preprocessing version, checkpoint hash, and pooling policy.
It also records input availability, failure reason, shape, dtype, and finite-value
checks. A reusable ECG-study vector may be cached by study hash; the choice of
which study enters a trial episode remains index-specific and separately versioned.

No post-index records, treatment-start documents, future amended reports, or
outcome labels enter baseline encoders. Default to strictly pre-index events;
include same-day data only when ordering is established. Restrict inference inputs
by both clinical event time and when the information was available. When historical
versions are unavailable, document the limitation and use conservative exclusions.

Audit each model's training objective, training population/dates, and possible
patient/outcome overlap. A frozen encoder trained on overlapping patients' future
records is still potentially contaminated. Use an independent evaluation population
where possible; otherwise disclose the overlap and restrict the claim.

### Modality-specific work

| Modality | First investigations | Required validation |
|---|---|---|
| ECG | Available raw/preprocessed waveforms, lead order, units, sample rate, duration, device/site, checkpoint objective. | Shape and signal QA, stable inference, study-to-patient mapping, duplicate/collapsed vector checks, no random missing checkpoint components. |
| Structured EHR | Source code dictionaries, numeric values, event timing, mapping to encoder vocabulary, sequence length. | Coverage by domain/year/cohort, unknown-token rates, ordering/tie handling, truncation and patient-index representation tests. |
| Notes | Note types, encounter/authored/signed/amended times, copied text, storage and model access. | Local inference, no identifiers in model inputs where unnecessary, cutoff leakage tests, deduplication, chunking/pooling reproducibility. |
| Echo imaging | Videos versus stills, views, frame timing, quality, paired reports, study dates, encoder availability. | Study-level aggregation without image-count weighting of patients, view QA, burned-in text/device effects, pre-index selection and identity joins. |
| Echo reports | Report versions and timestamps, structured measurements, overlap with other notes. | Distinct method IDs from imaging; remove duplicated evidence in multimodal analyses. |

Qwen-based note embeddings are a hypothesis. The official Qwen embedding release
documents text-embedding models and inference conventions, not validated causal
adjustment on these clinical notes. Pin the exact encoder/tokenizer and evaluate
chunking, truncation, instruction, and pooling on development data.
[Official implementation](https://github.com/QwenLM/Qwen3-Embedding)

### Controlled method expansion

For each validated representation `Z`, start with:

1. Clinical PSM plus `Z` in a prespecified regularized propensity model.
2. Clinical PS caliper followed by matching on distance in `Z`.
3. Representation-only matching as a mechanistic ablation, with explicit reporting
   of any loss of clinical balance.

Then test combinations, beginning with separately scaled/normalized blocks and a
fixed development-selected fusion policy. A raw concatenation can be dominated
by vector dimension or scale. Fit dimensionality reduction and learned fusion only
inside the declared development/training partition. More complex joint learning
comes after simple fusion, with its own contamination and compute audit.

Useful ablations include structured ECG intervals, structured echo measurements,
code counts/time bins, simple note representations, dimension-matched random
features, modality removal, and missingness/utilization-only controls. Report
runtime, storage, retained sample size, and inference failure as well as agreement.

## 7. Fair method comparisons

### Modality availability

Define before adjustment:

- `D_base`: eligible patients with adequate source/outcome observability.
- `D_ECG`, `D_structured`, `D_notes`, `D_echo`: corresponding valid pre-index input
  cohorts, with explicit coverage requirements.
- Named pairwise and multimodal intersections for each registered comparison.

For each candidate, rerun the PSM baseline on that exact starting population.
Report baseline performance in both `D_base` and the restricted cohort. This
distinguishes changes due to selecting patients with a modality from changes due
to using its information. Do not force every comparison onto a tiny all-modality
intersection; reserve it for the relevant multimodal questions.

### Matched target population and effect scale

Equal starting denominators are necessary but insufficient: different matchers
may retain different treated patients. For a confirmatory matching comparison,
freeze a common treated anchor population using baseline-only support rules and
require compared methods to retain those anchors with their declared weights.
If a prespecified common retained subset is necessary, define and freeze the rule
before outcomes, rerun methods on it, and report the narrowed target explicitly.
Method-specific retained populations are a secondary operational analysis.

Do not treat ATT, ATE, overlap-weighted populations, conditional matched-set Cox
coefficients, and marginal HRs as interchangeable. Define the target outcome
contrast and variance approach per trial. Use a common outcome estimator across
the matching comparisons where justified. Inspect proportional hazards and use
prespecified risk or restricted-mean contrasts when suitable published references
exist; do not change scale after seeing agreement.

## 8. Demonstrating directional and statistical improvement

### Define the claim before testing

For eligible HR trials, let `theta_R,j = log(HR_RCT,j)` and
`theta_m,j = log(HR_method_m,j)` with a verified common treatment direction.

Proposed primary loss and paired improvement:

```text
L_m,j     = abs(theta_m,j - theta_R,j)
Delta_m,j = L_PSM,j - L_m,j
```

Positive `Delta` means the candidate is closer to the RCT on that trial. The
primary aggregate is the equally weighted mean paired improvement across the
prespecified evaluable trial set; report its interval and the number of independent
trial families. Family-weighted and median/win-rate summaries are sensitivities.
No universal raw-effect aggregation across HRs, risk ratios, and continuous mean
differences. Define separate effect-scale strata or a separately justified
standardized metric before including non-HR trials.

Directional improvement has two distinct summaries: the proportion of trials
with positive `Delta`, and agreement with the RCT effect's side of the null.
Neither alone establishes statistical superiority. Null and noninferiority
trials require their own margin-aware interpretation.

### Uncertainty and multiplicity

- Nominate one primary candidate versus PSM using development data, then freeze
  it. If several candidates remain confirmatory, freeze the family and use a
  prespecified familywise procedure such as Holm for the superiority tests.
- A superiority claim requires a positive aggregate improvement with appropriate
  interval/test evidence after multiplicity adjustment, plus acceptable retention,
  balance, precision, and prespecified sensitivity results. Define any minimum
  useful improvement during power planning, not after the results.
- Methods share patients and trial references. Treat their errors as paired, not
  independent. Repeated seeds, imputations, endpoints, and databases are not new
  independent trials.
- Group related trials sharing drugs, indications, and substantial patient overlap.
  Assess dependence using cluster-resident overlap summaries and simulations.
  Use family-level inference only when enough independent families exist; otherwise
  state the limitation and keep results descriptive.
- Finalize a variance strategy appropriate to the actual matching/weighting and
  survival estimator. Validate coverage in simulations. Do not blindly bootstrap
  patients through fixed-neighbor matching; bootstrap validity depends on the
  estimator and replacement scheme. Distinguish trial-level resampling of benchmark
  metrics from patient-level variance estimation.
  [Matching variance study](https://pmc.ncbi.nlm.nih.gov/articles/PMC4260115/)
- Report both fixed-published-reference agreement and a sensitivity propagating
  published RCT uncertainty. The observed RCT point estimate is not noiseless truth.

### Secondary metrics

Report absolute/squared log-effect error, mean signed discrepancy, calibration,
Bland–Altman plots, Pearson/Spearman association, and paired win rates. Correlation
alone can look favorable despite systematic error.

Reproduce the paper's agreement definitions in a distinct module: estimate
agreement means the emulation point estimate falls inside the RCT interval;
significance/noninferiority agreement and standardized-difference agreement need
exact original rules. Generic CI overlap is an additional metric, not a substitute
for estimate agreement. Verify formulas and noninferiority margins against the
supplement/protocols before freezing this module.
[Agreement definitions](https://jamanetwork.com/journals/jama/fullarticle/2804067)

Do not reward artificially wide intervals: report interval width, effective sample
size, failed estimation, and retention alongside agreement. Cross-trial aggregation
summarizes method performance; it is not a pooled drug treatment effect.

### Failures and robustness

Predeclare trial-level eligibility for each method comparison and publish the full
trial-by-method status matrix. Distinguish source-infeasible, no overlap, encoder
failure, insufficient events, estimator failure, and valid null results. A failed
candidate is not silently removed to improve its mean score. Report conditional
paired accuracy on valid common comparisons alongside success/coverage rates and
a conservative failure sensitivity; material differential failure precludes a
general superiority claim.

Plan negative/positive control outcomes with clinical justification, known-answer
simulations with hidden confounding, temporal/site/cohort sensitivity, missingness
and modality-selection sensitivity, index/window changes, alternate censoring,
calendar-time balance, treatment versions, and matching order/seed sensitivity.
Diagnostics are evidence about failure mechanisms, not guarantees of no bias.

### Power and protected evaluation

Use development data and plausible effect-discrepancy simulations to estimate
benchmark power over the number of independent trial families, within-trial events,
modality attrition, and candidate multiplicity. Do not promise significance from
32 configured trials. If too few informative comparisons remain, present a pilot
benchmark and seek additional data/trials before a confirmatory claim.

Freeze trial families, method IDs, hyperparameters, source/model versions,
denominators, failure rules, and analysis code before protected evaluation. A
prospective or external benchmark is strongest; when unavailable, use clearly
labeled held-out families and acknowledge prior knowledge of published results.
Legacy analyses already viewed cannot become untouched validation by renaming them.

## 9. Engineering architecture and reproducibility

Proposed layout once implementation begins; these directories are not implemented yet:

```text
src/ecg_tte/
  sources/          raw adapters, schema/QC, identity, normalization
  protocols/        typed trial definitions and executable eligibility rules
  cohorts/          index episodes, observation, exclusions, attrition
  outcomes/         endpoints, censoring, time-to-event contracts
  features/         clinical covariates and missing-data processing
  representations/  ECG, structured EHR, notes, echo, fusion adapters
  methods/          PSM, weighting, hybrid matching, outcome estimation
  evaluation/       reference registry, agreement metrics, paired comparisons
  reporting/        stable result schemas and aggregate diagnostics
  orchestration/    CLI, manifests, cache validation, run status
configs/            separate source, trial, method, and benchmark configuration
tests/              synthetic unit, integration, property, simulation checks
```

Use stable machine-readable IDs, never plot labels as join keys. Every result row
includes trial/protocol, method/version, source snapshot, cohort hash, estimand,
effect scale/orientation, outcome, follow-up, denominator, n/events/ESS, estimate,
uncertainty, diagnostics, and status/reason. Missing or failed results remain rows.

Use immutable run directories, atomic output writes, content-aware cache keys,
explicit seeds, dependency locks, checkpoint hashes, and run manifests. Successful
status requires validated outputs from the current invocation; file existence from
an earlier run is insufficient. Do not auto-pull changing code during a scientific
run. Keep the archive outside imports, packaging, test discovery, and job loops.

CI initially uses synthetic data and known-answer cases. Add tests for nested
config execution, unknown keys, date boundaries, treatment ties, unit conversions,
identity collisions, duplicate joins, no future information, empty arms, censoring,
matching/weight semantics, failed encoders, reproducibility, and stale cache rejection.
Every clinical criterion needs an executable test plus a source-mapping review.

## 10. Phases and concrete completion gates

| Phase | Work and artifacts | Gate to proceed |
|---|---|---|
| 0 — Reset | Legacy archive, manifest, new scope, decisions, work tracker. | All previous tracked files preserved; active docs identify the new project. Completed. |
| 1 — Source reconnaissance | New raw profiler; file/schema manifest; source dictionaries; quality, identity, coverage, and modality reports. | Raw roots accessible; source semantics evidenced; unresolved issues assigned. |
| 2 — Data contracts | Normalized tables, tested adapters, reconciliation report, restricted provenance mapping. | Row accounting, identity and time invariants pass; no silent parse loss or unexplained joins. |
| 3 — Trial design | Candidate screen, clinical protocol/reference cards, feasibility and power model, development/evaluation split. | Required elements observable; targets aligned; exclusion/benchmark rules frozen before effects. |
| 4 — Baselines | Clinical and expanded structured PSM, diagnostics, appropriate variance, synthetic/pilot verification. | Credible strong comparator; all criteria executed; overlap and uncertainty validated. |
| 5 — Representations | Checkpoint/input audits; cutoff-aware ECG/EHR/notes/echo adapters; coverage and compute report. | No known temporal leakage; identity/shape/determinism tests pass; training overlap disclosed. |
| 6 — Development | Restricted method matrix, ablations, fusion/tuning, matching-population checks. | Candidate list and statistical analysis plan frozen; no evaluation effects used in tuning. |
| 7 — Evaluation | Protected trial-family run, paired accuracy/inference, failure matrix, robustness analyses. | Complete registered report; no selective omissions; limitations and inconclusive results retained. |
| 8 — Evidence package | Source-to-result lineage, protocol supplements, flow/balance/calibration plots, methods and result tables. | Reproducible from pinned inputs; clinical/statistical/code review complete. |

Phase 1 is the immediate next work. Plan wall-clock estimates only after raw file
sizes, access, model assets, and resource limits are known. Archive creation does
not constitute completion of the component investigation.

## 11. Questions and immediate next step

The three questions sent to the user concern raw-source access, initial trial
breadth, and available modalities/checkpoints. Until resolved, the plan assumes
raw profiling will run on the cluster, a diverse feasibility-led roster is the
desired eventual benchmark, and imaging/text echo remain separate candidates.
These assumptions permit planning, not patient-data access or final model selection.

Next deliverable: a new JDAT inventory/profiling tool and its reviewed aggregate
source report, followed by a clinical source-mapping review. Do not start fitting
new treatment-effect models while foundational source semantics remain unknown.
