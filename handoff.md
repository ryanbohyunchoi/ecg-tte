# Handoff: adapted COMET cohort, adjustment, and outcomes

Last updated: **2026-09-22**. Read this current-session brief first. The older
roadmap and chronological evidence below are retained for history; their pending
items and population counts may be superseded by this brief.

## Two concurrent sessions — current ownership

Ryan approved splitting work into two independent tracks. This session owns
**Track 1: cohort and baseline adjustment**. A new session should own
**Track 2: outcomes and follow-up**. Use a separate worktree and a `codex/` branch
for Track 2, based on the latest `psm-mice-imputation` branch including this handoff.
Do not start from an older default branch that lacks the restart scripts.

| Track | Owns | Deliverable |
|---|---|---|
| 1 — existing session | Expanded diagnosis cohort reassessment; lab recovery/mapping; baseline covariates; MICE and PSM | Versioned cohort, baseline table, tested adjustment pipeline |
| 2 — new session | Outcome sources and definitions; death-date coverage/consistency; hospitalization-event definitions; follow-up and censoring | Source audit scripts, synthetic tests, proposed endpoint/follow-up contract |

Track 2 can investigate source coverage and develop synthetic-tested code without
waiting for final cohort membership. Any candidate-roster feasibility counts are
provisional. Final outcome attachment requires Track 1's finalized patient/index
manifest. Final MICE specifications may depend on outcome/follow-up variables;
coordinate that interface before analysis-stage imputation.

### Instructions for the new outcomes session

1. Read `master.md`, `README.md`, `docs/RESTART_PLAN.md`, `docs/DECISIONS.md`, this
   brief, `docs/COMET_ADAPTED_PROTOCOL.md`, `docs/COMET_COHORT_DRAFT.md` (historical
   proposals), and `docs/COMET_MISSING_DATA_PLAN.md`.
2. Prepare a versioned outcome/follow-up proposal. All-cause mortality is a
   candidate endpoint, **not a frozen decision**. Verify primary trial sources
   before claiming alignment. Do not silently choose endpoint, horizon, estimand,
   administrative cutoff, or censoring rules.
3. Prepare H100 audits for death-date presence, conflicts, source freshness,
   linkage and temporal consistency; inspect coverage independently of treatment
   effects. Missing death dates do not prove survival through an arbitrary end
   date. Delivery dates do not automatically establish follow-up coverage.
4. Assess hospitalization event definitions if proposed as an outcome: setting,
   encounter/episode deduplication, transfers, dates and capture. Our use of
   all-cause inpatient encounters as a **baseline covariate** does not select
   all-cause hospitalization as a study endpoint.
5. Define a proposed patient/index-to-outcome interface with event time, censor
   time/reason, coverage and provenance. Keep outcome data out of baseline
   representations and design-stage tuning. Do not require a future encounter
   or refill for entry; avoid immortal-time selection.
6. Work in new outcome-specific scripts/tests/docs. Do not change cohort
   eligibility, original medication anchors, the32-variable specification,
   baseline extraction, or MICE/PSM code. Do not edit the shared source engine
   dependencies casually: their hashes are part of snapshot compatibility.
7. No treatment-effect estimation, treatment-stratified outcome comparisons,
   protocol freezing, source rewriting or cluster execution by the assistant.
   Flag decisions for coordination with Ryan and Track 1; do not freeze them
   unilaterally.
8. Return the branch/commit, tested changes, exact H100 commands, proposed
   decisions and unresolved evidence. Put progress in a new
   `docs/COMET_OUTCOMES_HANDOFF.md` to avoid concurrent edits to this handoff and
   shared decision/task registers. Track 1 will integrate agreed updates.

### Execution and data boundaries — both sessions

- **Never SSH into or directly access H100**, even for listings. Ryan pulls and
  executes code. Local work is code, documentation and synthetic tests.
- Patient records, identifiers, clinical text and patient-specific dates stay on
  H100. Only reviewed aggregate reports return to chat/repository.
- Immutable raw data and completed snapshots are shared read-only. Each job
  writes a fresh private directory, with `umask 077`, beneath
  `/mnt/raid0/rbc58/ecg-tte/audits/` or `/mnt/raid0/rbc58/ecg-tte/shared/`.
  Track 2 should use `comet-outcome-*` audit directories.
- Preserve the legacy archive and existing OMOP datasets. Do not import legacy
  analysis code as an active protocol. Avoid simultaneous heavy cluster scans
  if storage becomes a bottleneck; concurrent local development is independent.

## Current scientific and execution state

- Explicitly adapted COMET: carvedilol versus metoprolol tartrate prescribing
  comparison, not verified dispensing/adherence or strict RCT replication.
- Current anchor: earliest qualifying observed outpatient Normal/Print study-drug
  order across arms, using ORDER_INST. Not first-ever beta-blocker use. Same-day
  competing-arm ties excluded. New-user/washout, observation, other eligibility,
  endpoint, follow-up and estimand contracts remain unfinished.
- Selected phenotype: prior general HF code **OR** latest strictly prior numeric
  EF>1 and<40 within365days, with whole-patient prior diastolic/combined/HFpEF
  code or lexical exclusion signals. Lexical exclusions are not negation-aware.
- Previous cohort:6,530 (4,017carvedilol/2,513tartrate), **provisional**.
  Staging v4 has32covariates; utilization recorded zeros established. All-cause
  inpatient encounters retained; HF-specific hospitalization predictor removed.
- 2025DXlinked9,361/9,373baseline inpatient keys (99.87%), versus212using2026DX.
  It revealed1,619prior exclusion signals in the existing roster.4,911would
  remain after those removals alone, but **this is not a rebuilt cohort count**:
  expanded HF evidence may also admit previously unselected candidates.
- 2025outpatient labs alone covered446/6,530patients with any prior90result-dated
  record, not four-analyte availability. Hospital labs1/2are completed stages in
  a globally failed snapshot. Shard3is damaged; no replacement established.
- No vital unit documentation is available yet. BP/pulse/BMI numeric candidates
  do not establish units, BP ordering or clinical validity. No MICE, PSM or
  treatment-effect estimation has run.

### Pending Track 1 jobs — do not mistake readiness for completion

Latest implementation commit before this handoff: `439badd`;208synthetic tests
passed. `docs/RUN_COMET_REASSESSMENT.md` contains the complete run block for:

- `scripts/reassess_comet_diagnoses.py`: original candidate roster, both diagnosis
  deliveries, fixed medication anchors; report retained/entered/removed patients
  and write a separately versioned cohort and transition table.
- `scripts/reuse_comet_hospital_labs.py`: independently copy and verify2025hospital
  lab shards1/2, including raw and Parquet checksums, into a new limited snapshot.
  Parent stays failed/untouched; damaged shard3is not accessed.

Ryan's latest saved-report check found **no summaries** under
`audits/comet-expanded-dx-*/report/summary.json` or
`shared/hospital-labs-limited-*/snapshot/summary.json`. Commands were supplied
again; execution/completion is not yet established. Do not repeat the completed
2025source builds. Old cohort adapters intentionally reject the reassessment's
new version until downstream extraction is updated by Track 1.

### Known H100 paths

All paths below are user-reported; no assistant remote inspection.

| Artifact | Absolute path |
|---|---|
| Repository | `/home/rbc58/github/ecg-tte` |
| Raw delivery parent | `/home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG` |
| Core medication/2026DX/echo snapshot | `/mnt/raid0/rbc58/ecg-tte/shared/source-v1-9Ka1kA0i/snapshot` |
| Clinical demographics/encounters/vitals snapshot | `/mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-t9ZGomLT/snapshot` |
|2025diagnosis snapshot | `/mnt/raid0/rbc58/ecg-tte/shared/diagnoses-2025-nauv2IgF/snapshot` |
|2025outpatient lab snapshot | `/mnt/raid0/rbc58/ecg-tte/shared/outpatient-labs-2025-fOMEo0i1/snapshot` |
| Original broader medication candidates | `/mnt/raid0/rbc58/ecg-tte/audits/comet-candidates-c2FSBqdW/report` |
| Previous6,530cohort | `/mnt/raid0/rbc58/ecg-tte/audits/comet-broad-excluded-cnG52aaY/report` |
| Baseline v3 parent of v4 | `/mnt/raid0/rbc58/ecg-tte/audits/comet-baseline-v3-XhcifvB2/report` |
| Failed lab extension, read only | `/mnt/raid0/rbc58/ecg-tte/shared/psm-sources-v1-0815146D/snapshot` |

The clinical snapshot includes2025Patients with BIRTH_DATE/DEATH_DATE, both
2025and2026encounter deliveries, and selected vitals. A2026Patients file was not
available in the earlier source inventory. Mortality ascertainment and freshness
remain unvalidated; a2025patient file must not silently imply complete2026death
follow-up. Inspect source contracts/manifests through H100 tools Ryan runs.

## Historical roadmap and evidence log

The following sections preserve earlier work. The current-session brief above
controls ownership and current status where older entries conflict.

## Pipeline checklist — stages, deliverables and completion gates

Status as of 2026-09-16. Checked items have evidence; unchecked items are planned.
This is the working roadmap, not a frozen analysis protocol. Target-trial emulation
covers the entire design and analysis, not only arm assignment. Stages 1–3 can be
separate software modules but must share one prespecified index-time contract.

### Stage 0 — Find, inventory and qualify available data

- [x] Locate full RBC OMOP at `/mnt/raid0/rbc58/omop/gold` and compare documented
  inputs, mapping resolution and table schemas with bb2238.
- [x] Locate supplemental medication tables and mosaic/gold_rbc; record limits of
  their inspection and preserve all existing datasets.
- [x] Record latest available per-step manifest counts and unresolved provenance.
- [ ] Freeze an explicit source snapshot/table manifest for the first trial.
- [ ] Verify patient linkage, code coverage, units, source overlap, event/availability
  timestamps and the trial's required fields using read-only aggregate checks.
- [ ] Establish usable baseline history and outcome capture; do not treat birth-based
  observation periods as continuous observation.

**Gate:** discovery is complete enough to start trial-specific feasibility. Clinical
source validation remains open; finding tables does not complete all of Stage 0.

### Stage 1 — Prespecify the target trial and build candidate cohorts

- [ ] Select trial(s) based on clinical relevance and source feasibility, not favorable
  agreement with known effects. Obtain protocol, supplements and verified RCT results.
- [ ] Freeze target population, treatment/comparator strategies, eligibility,
  candidate index, baseline window, endpoint, follow-up, censoring and estimand.
- [ ] Define the unit: patient versus patient–trial episode, repeated eligibility,
  re-entry rules, and handling of multiple encounters or candidate treatment starts.
- [ ] Prespecify the reference effect scale/horizon, comparison metrics, development
  versus evaluation split, and primary method comparison before new effect estimates.

#### Stage 1a — Conventional cohort implementation (active first priority)

- [ ] Translate the protocol into clinician-reviewed, versioned rules and code sets.
- [ ] Define basic candidate eligibility: age, indication, prior treatment, available
  history, required clinical evidence and observable contraindications.
- [ ] Define medication evidence precisely: order, dispensing, administration or
  reconciliation; dose/formulation/route, new use, washout, canceled/held records,
  combination products and same-day ambiguities.
- [ ] Assess pre-index treatment history/adherence only when the source supports it.
  Do not infer adherence from prescription presence, refills ordered or ingestion
  from a recorded prescription. Record unobservable requirements explicitly.
- [ ] Test positive/negative/boundary cases with synthetic fixtures, including nulls,
  absent fields, dates, OR/AND logic, duplicate records and conflicting evidence.

#### Stage 1b — CIPHER-EHR cohort-construction comparator (deferred)

Ryan selected the conventional, non-CIPHER-EHR workflow for the first baseline.
Retain this track for later investigation; it is not part of the first implementation.

- [x] Clone and review CIPHER-EHR v2 documentation and mapping-review/query code.
- [ ] Freeze version, model/checkpoint, prompts, terminology, clinician-review budget
  and the same protocol/source snapshot/index-time evidence used for Stage 1a.
- [ ] Adapt the RBC parquet/OMOP data contract and patient–episode cutoffs to the tool;
  direct compatibility and large-dataset scalability have not been demonstrated.
- [ ] Generate reviewable criteria, mappings and SQL; retain evidence for each rule
  and complete required human mapping/code-set reviews before execution.
- [ ] Validate protocol extraction/code logic separately from patient eligibility.
  Establish an independently clinician-adjudicated held-out reference sample with
  eligible, ineligible, ambiguous and discordant cases; reviewers are blinded to
  method identity and downstream outcomes/effect estimates where feasible.
- [ ] Compare criterion-level and final eligibility sensitivity, specificity, PPV,
  NPV, agreement, abstentions/unassessable cases, error types and review time with
  uncertainty. Account for stratified sampling when estimating population metrics.
- [ ] Prespecify whether this tests structured cohort generation or patient-level
  note adjudication. If notes add information, include a same-information comparator
  so the effect of extra data is not attributed solely to the LLM.
- [ ] Keep all patient-data processing and any LLM inference in the approved research
  environment. Cloning does not authorize cloud PHI transfer or a live run.

**Gate:** CIPHER-EHR is an optional cohort-method comparison, not a prerequisite for
establishing conventional PSM. Do not define “better cohort” by being closer to the
RCT effect. First establish clinical eligibility accuracy independently.

### Stage 2 — Final eligibility, exclusions and cohort validation

- [ ] Apply the complete inclusion/exclusion logic at each candidate index using only
  evidence available then; distinguish missing, absent, conflicting and unmeasurable.
- [ ] Verify required criterion implementation and stopping rules. Unsupported
  mandatory criteria stop or explicitly reclassify the trial; never silently omit.
- [ ] Produce criterion-level evidence and an attrition table, including reasons for
  exclusions, missing modality data and any unassessable patients/episodes.
- [ ] Clinically review sample decisions and check counts, duplicates, eligibility
  contradictions. Compare overlap with CIPHER-EHR only if that deferred track resumes.
- [ ] Freeze the eligible cohort definition. Stage 2 validates/finalizes Stage 1;
  it must not add post-treatment exclusions after examining outcomes.

**Gate:** a reproducible eligible patient–episode population with traceable criteria.

### Stage 3 — Treatment strategies, time zero, baseline features and adjustment

#### Stage 3a — Treatment/comparator classification and follow-up contract

- [ ] Classify observed treatment strategy at the eligible index; use “treated and
  comparator arms,” not outcome-defined “cases and controls.” No random assignment
  is created by observational matching.
- [ ] Align eligibility, treatment classification and follow-up start at time zero;
  resolve prevalent users, simultaneous therapies and ambiguous start times.
- [ ] Separate an initiation/ITT-analogue strategy from an adherence/per-protocol
  strategy. Future adherence is not a baseline eligibility filter. If per-protocol
  effects are pursued, prespecify deviations, censoring and appropriate adjustment
  for time-varying confounding; do not simply drop later nonadherent patients.
- [ ] Freeze outcome phenotype, time at risk, death/competing-event handling and
  censoring. Keep outcome extraction isolated from matching/representation tuning.

#### Agreed analysis direction — initiation plus sustained treatment

Ryan agreed to this direction on 2026-09-16:

- **Primary initiation-based PSM:** retain eligible patients irrespective of later
  treatment discontinuation, subject to the protocol's ordinary follow-up rules.
- **Secondary sustained-treatment/per-protocol analysis:** patients contribute
  follow-up until a prespecified treatment deviation. Censor at that point rather
  than retroactively excluding them. Outcomes before censoring count; outcomes
  afterward are outside their uncensored follow-up in this secondary analysis.
  Death before censoring counts as an outcome when death is the endpoint; for
  other endpoints, follow the prespecified competing-event/estimand definition.
- Plan inverse-probability-of-censoring weighting using appropriately timed measured
  predictors of deviation and outcome. Baseline PSM alone does not resolve selection
  from treatment-related censoring. Evaluate measured-confounding assumptions,
  positivity, weight stability/truncation and uncertainty; weighting is not a
  guarantee against bias from unmeasured reasons for discontinuation.

**Agreed direction, not implemented or validated:** the drug/comparator, exposure
start, verified fill/supply source, grace period, allowable gaps/switches, adherence
threshold, censoring timestamp, within-day event ordering and weighting model remain
unfrozen. Apply comparable strategy-specific rules to both arms. Landmark analysis
remains an alternative only if separately selected; it is not the current secondary
analysis choice. Do not infer a 180-day censoring rule from the earlier refill proposal.

#### Medication exposure and adherence plan — conventional baseline first

**User-requested proposal:** require evidence of repeated medication use, such as
**2–3 refills within 180 days or the first year**, to avoid equating a single order
with sustained treatment. This is a proposed persistence criterion, not a frozen
threshold or an implemented filter.

- [ ] Verify whether the sources contain actual dispensing/fill events, their dates,
  days supplied and links to the original prescription. Refill authorizations,
  repeated orders, reconciliation entries and administration rows must not be
  counted as pharmacy refills. Deduplicate the same event across source deliveries.
- [ ] Determine whether the selected therapy is a chronic outpatient medication for
  which refill-based persistence is appropriate. Account for 30- versus 90-day
  supplies; refill counts alone do not establish medication coverage or ingestion.
- [ ] Freeze whether “2–3 refills” means additional fills after the initial fill or
  total fills, the 180- versus 365-day window, drug/ingredient switching rules,
  permissible gaps and observation requirements. Apply clinically comparable
  definitions to both active-treatment arms. Prespecify sensitivity alternatives
  before seeing effect estimates; do not select the best RCT agreement.
- [ ] Validate initial exposure using evidence available at time zero. If only
  prescriptions are observable, label the strategy as prescribing rather than
  verified dispensing/use. Unsupported mandatory exposure requirements stop the
  trial rather than silently treating an order as proof of use.
- [ ] Keep the primary initiation-based analysis separate from sustained-use
  analyses: do not retrospectively remove patients with early outcomes, death or
  discontinuation because they failed to accumulate future refills.
- [ ] Implement the agreed secondary per-protocol design only after prespecification:
  an analysis
  from initiation with explicit grace periods, deviations, censoring and suitable
  adjustment for time-varying confounding. Establish data support and assumptions
  before implementation; simply excluding later nonadherent patients is inadequate.
- [ ] If a simpler refill-defined cohort is desired, consider a separate landmark
  analysis: assess refill evidence through day 180 or 365, require survival and
  observability to that landmark in both arms, and start outcome follow-up there.
  This targets a selected survivor population and a different estimand; it is not
  directly interchangeable with the initiation-based RCT comparison and still
  requires confounding/selection assessment.

**Current feasibility:** the inspected RBC gold schema does not establish actual
pharmacy fills or days supply. The supplemental medication tables retain richer
order/status/date fields, but verified dispensing and adherence remain unresolved.
Use read-only source checks on the H100 before choosing a computable criterion.
Calculate coverage measures such as PDC/MPR only if fill and supply semantics support
it; an unmeasurable adherence criterion must be reported as unmeasurable.

Requiring future refills while beginning follow-up at the first prescription can
introduce immortal-time and selection bias. Align eligibility, treatment strategy
and follow-up for each analysis ([methodological reference](https://pubmed.ncbi.nlm.nih.gov/27237061/)).

#### Care setting and medication evidence — bounded audit available

Run instructions: [medication setting audit](docs/RUN_MEDICATION_SETTINGS_AUDIT.md).
The first pass reports bounded record-level categories and field presence; actual
H100 results, semantic validation and patient-level persistence remain pending.

For a chronic outpatient medication trial, prioritize outpatient maintenance
exposure for persistence/refill assessment. This is conditional on the selected
trial, not a universal eligibility rule. An inpatient-initiation or discharge trial
requires its own index and treatment contract. Prior hospitalization alone does not
exclude a patient from an outpatient trial; inpatient history can inform baseline
covariates and hospital events can remain endpoints.

Keep two independent classifications: **care setting** (inpatient, outpatient,
emergency, discharge/transition, unknown) and **evidence type** (order, actual
administration, dispensing, medication history). Outpatient administration is not
an outpatient pharmacy refill; repeated inpatient doses are not refills. Discharge
prescribing does not prove post-discharge filling or continued use.

- [ ] On the H100, inspect distinct values, missingness and counts for the preserved
  setting, order class/status and source fields in `/home/rbc58/mnt/ecg-tte/drugs`.
  Review source dictionaries and transformation code before assigning meanings.
- [ ] Cross-tabulate setting × evidence type × source, with aggregate record and
  unique-patient counts, duplicates and unknown/conflicting classifications. Patients
  can appear in several settings, so patient counts across categories are not additive.
- [ ] Check raw encounter type, administration action and order/encounter identifiers
  where available; quantify linkage success and disagreements. Date overlap alone
  is insufficient to assert that an order belongs to a hospital encounter.
- [ ] Assess the selected treatment and comparator separately: canceled/held orders,
  actual administrations, verified fills, supply completeness and distinct fill
  dates. Keep identifiers, record examples and raw value catalogs on the cluster;
  return only reviewed aggregate summaries.
- [ ] Freeze the applicable setting/evidence rule only after this audit. The current
  gold samples omit encounter IDs and administration action; existing metadata
  cannot establish a reliable setting filter or actual refill availability.

OMOP distinguishes record provenance with `drug_type_concept_id` and encounter
setting through linked visits, when those fields are populated correctly. Their
presence and correct mapping in this dataset must be verified, not assumed from
OMOP naming ([OMOP conventions](https://ohdsi.github.io/CommonDataModel/cdm54.html)).

#### Medication setting report reviewed — 2026-09-16

Ryan supplied the restricted category report for 13 medication files. Reviewed
setting/status/class aggregates are summarized here; the raw catalog is not copied
into the repository. Each file's setting counts total 100,000 records, consistent
with the configured first-row prefix. These are not unique-patient counts or
population estimates. The companion summary was not supplied, so file coverage,
failures, truncation and fill/supply-field presence cannot be assessed from this
artifact alone.

| Source family | Observed setting label | Selected prefix findings |
|---|---|---|
| Four home-medication files | `home_meds` | `Historical Med` comprises 27.202% of CMP, 58.467% of implementation, 27.202% of merged and 25.217% of T2DM prefixes. Orders also have Normal/Print/No Print and other classes. |
| Six inpatient files | `inpatient` | Order class is null throughout each prefix; Discontinued is 79.576–88.059% of records. Completed, Dispensed, Verified and Sent also occur. |
| Three outpatient-administration files | `outpatient_admin` | Order class is null throughout each prefix; Completed is 79.962–89.102%. Discontinued and other order statuses also occur. |

**Interpretation:** these derived tables separate source-setting labels, but the
report does not independently validate encounter setting. Home-medication files
mix historical-medication entries and prescription-related classes; they cannot
all be treated as incident outpatient prescriptions. `Sent` is not proof of a fill,
`Dispensed` in an inpatient source is not proof of an outpatient pharmacy refill,
and `Completed` is not sufficient evidence of an administered dose. Validate source
semantics and administration-action timestamps before making those inferences.

Do not discard every `Discontinued` record: a recorded end status does not establish
that treatment never began. Establish when status was recorded relative to index;
a later discontinuation must not become a retrospective baseline exclusion.
Likewise, `Normal` alone is not a validated new-use rule and `Historical Med` does
not establish when medication was first started.

CMP and merged home-medication prefixes have identical class/status distributions.
This flags possible source overlap, not proven duplicate records. Do not concatenate
merged and component tables without lineage and event-level deduplication checks.

**Next gate:** obtain the companion summary from this same run to establish
fill-date/days-supply presence and coverage. Trace the source-preserving builder's
setting/status derivation, choose the trial/drug/comparator, and validate initial
prescription versus history and actual dispensing. For chronic outpatient therapy,
home-medication sources are the candidate starting point; no setting/status filter
or 2–3-refill adherence rule is validated yet. If actual fills are unavailable,
repeated prescriptions can only be evaluated as a documented-prescribing persistence
proxy, with a distinct definition and estimand—not asserted medication adherence.

#### Companion medication summary reviewed — 2026-09-16

The subsequent summary resolves the preceding coverage uncertainty: all 13 direct
parquet files completed, no file limit was reached, no source changes were detected,
and each file read a 100,000-record prefix. All files reached the row limit. The
reported category/cross-tab omitted-record counts are zero.

All 13 schemas lack the audited names for fill/dispensing date, days supply,
quantity, refills/refills remaining, administration action, order ID and encounter
ID. This establishes absence of those exact case-insensitive names in these derived
files, not absence of equivalent differently named fields or upstream raw sources.
Order date is populated in every sampled record. Home-medication end_date is
nonempty in 85.902–90.520% of sampled records, but its meaning is unverified; all
inpatient/outpatient-admin sampled end dates are null. Do not infer supply duration
from order_date-to-end_date without validating source semantics.

**Adherence assessment:** actual outpatient dispensing events after a validated
initial fill can support refill/persistence measures; verified days supply is also
needed for supply-based coverage such as proportion of days covered (PDC). Deduplicate
fills, handle reversals, overlaps/stockpiling, switches, hospitalization and follow-up
capture explicitly. Pharmacy supply is a proxy for medication availability, not proof
of ingestion. A missing refill outside known pharmacy capture is unknown, not proven
nonadherence. The current derived-file report does not establish these inputs.

Next inspect upstream raw JDAT medication headers/dictionaries and builder lineage
for discarded or differently named pharmacy fill/supply fields. A broader scan of
these same derived rows cannot recover absent columns. If only repeat orders exist,
report distinct post-index prescribing events as a documented-prescribing persistence
proxy, not verified refills/PDC/adherence. Do not infer actual initiation from the
first recorded order or historical-medication entry alone.

Post-index measurement is appropriate for describing persistence or a prespecified
per-protocol analysis; future refill achievement must not retrospectively define
eligibility at the initial index. Keep early outcomes/deaths in the initiation-based
analysis, and use the separate Stage 3a adherence design if estimating sustained-use
effects. No adherence threshold or drug-specific filter is frozen by this report.

#### Stage 3b — PSM, representations, clustering and cosine matching

- [ ] Build prespecified clinical covariates and an expanded structured baseline;
  define missingness/imputation and fit preprocessing within development partitions.
- [ ] Enforce traceable pre-index cutoffs for every measurement, code, note, ECG and
  representation; assess pretrained model overlap and future-information leakage.
- [ ] Fit the clinical PSM baseline and expanded structured/regularized PS comparator;
  prespecify overlap rules, caliper, ratio, replacement, seeds and failure behavior.
- [ ] Specify clustering and cosine methods independently: input representations,
  scaling/normalization, training population, cluster selection, distance thresholds,
  how treatment arms are matched, and zero/missing-vector handling.
- [ ] Use the same eligible starting population and estimand for paired adjustment
  comparisons; define common treated anchors/retention rules and modality subsets.
  Keep the separate cohort-construction experiment distinguishable from matching.
- [ ] Assess pre/post-match balance, overlap, retention, effective sample size and
  sensitivity to matching choices before seeing treatment-effect comparisons.
- [ ] Freeze methods and evaluation cohorts. Unsupervised learning is not inherently
  protected against leakage or outcome-guided choice of clusters/hyperparameters.

**Gate:** validated baseline and comparison designs with acceptable prespecified
balance/overlap, or a documented failure. High treatment AUC is not the gate.

### Stage 4 — Effect estimation and comparison with the randomized trial

- [ ] Run a common, estimand-compatible outcome estimator across adjustment methods;
  account for matching/weights and repeated patients, and verify variance behavior.
- [ ] Estimate effects with uncertainty, event counts and follow-up summaries. Check
  model assumptions; handle competing risks according to the frozen estimand.
- [ ] Compare against the verified published RCT effect on the same orientation,
  endpoint, scale and follow-up horizon—not against an unspecified “model.”
- [ ] Report prespecified effect-error/directional metrics and paired method
  differences with uncertainty; distinguish a single-trial pilot from evidence
  of general improvement across independent trial families.
- [ ] Account for multiple methods/trials, shared patients and reference uncertainty;
  keep failed, null and inconclusive runs in the registered results.
- [ ] Run prespecified sensitivity analyses/controls; do not tune cohort rules,
  mappings or similarity settings to obtain the desired RCT agreement.

### Stage 5 — Robustness, reproducibility and ACC abstract

- [ ] Complete source/clinical/statistical review and preplanned sensitivity checks.
- [ ] Preserve protocol, cohort, data/model versions, seeds, code revision, execution
  manifests and aggregate result lineage without committing patient-level artifacts.
- [ ] Report cohort attrition, baseline balance, mapping limitations, retention,
  effect estimates and uncertainty, computational cost and failure rates.
- [ ] Present cohort-construction accuracy and causal-effect recovery as distinct
  claims; state the evaluation scope and any unresolved limitations.
- [ ] Prepare ACC abstract/tables/figures with conclusions supported by the actual
  results. Submission deadline/format and final trial roster remain to be confirmed.

### CIPHER-EHR review and design references

Cloned locally at `/Users/ryanchoi/Desktop/Research/github/reference/cipher-ehr`,
revision `7fd54c71d47c4b9a7c8cec7b0fecaec533ca2b6a`. The repo contains v1 and v2;
v2's README calls it **TrialMap v2**. Its documented workflow is protocol PDF →
LLM-drafted atomic eligibility/mappings → human approval → validated SQL → cohort
and attrition. This supports a cohort-generation comparison; it does not establish
superior patient-level clinical adjudication. The documented inputs are CSV/TXT
or SQLite, not a proven direct adapter to our partitioned OMOP parquet. It supports
local model providers, but no dependencies were installed, app run, or data supplied.

- [CIPHER-EHR repository](https://github.com/CarDS-Yale/cipher-ehr)
- [Reviewed v2 workflow](https://github.com/CarDS-Yale/cipher-ehr/blob/7fd54c71d47c4b9a7c8cec7b0fecaec533ca2b6a/cipher-ehr-v2/README.md)
- [Alignment of eligibility, treatment assignment and follow-up](https://pubmed.ncbi.nlm.nih.gov/27237061/)

## Current dataset to assess first

**Full RBC OMOP root: `/mnt/raid0/rbc58/omop`**  
**Gold tables: `/mnt/raid0/rbc58/omop/gold`**  
**Recorded run manifests: `/mnt/raid0/rbc58/omop/audit/runs/`**

This is the most complete existing mapping identified in this investigation and
the preferred candidate foundation for the first PSM feasibility assessment.
It is the expanded RBC rebuild, not merely the supplemental `mosaic/gold_rbc`
output. It is not yet validated for a specific target trial or certified as a
complete, standard-tool-compatible OMOP CDM database.

All ten inspected table directories contain parquet files: `person`, `death`,
`cohort`, `observation_period`, `condition_occurrence`, `observation`,
`drug_exposure`, `measurement`, `visit_occurrence`, `procedure_occurrence`.
The report read parquet footer schemas only, sampling three files per table;
whole-table schema consistency, current row totals and patient linkage were not tested.

## Research objective and immediate priority

Prepare an ACC abstract evaluating whether unsupervised clustering and cosine
similarity improve target-trial emulation compared with strong propensity-score
matching. Improvement is a hypothesis, not a required result or tuning target.

Start with a clinically specified PSM baseline and, where feasible, an expanded
structured/regularized propensity model. Compare representation methods on
prespecified populations, outcomes, estimands and pre-index cutoffs. The objective
is good balance and valid comparisons, not a high propensity score or treatment AUC.
CLMBR-T and further OMOP remapping are not prerequisites for beginning feasibility.

## What the existing runs produced

The RBC report contains all **12 discovered manifests**, spanning July 17–19, 2026
UTC. Counts below use the latest recorded output for each step, never the sum of
repeated runs. They are historical manifest counts, not independently recomputed
current-table totals. Person footer metadata confirms the reported person row count.

| Domain | Full RBC mapping | Older bb2238 mapping |
|---|---:|---:|
| Person | 879,547 | 879,547 |
| Death | 103,111 | 103,111 |
| Medication records | 125,488,272 | 85,767,598 |
| Laboratory measurements | 321,428,791 | 15,519,308 |
| Vital measurements | 88,240,830 | 19,349,129 |
| Hospital visits | 18,426,882 | No visit parquet found |
| Outpatient visits | 14,070,092 | No visit parquet found |
| Procedures | 469,011,381 | No procedure parquet found |

RBC condition contributions: **138,979,018** from encounter diagnoses,
**9,278,210** from problem lists, and **6,667,568** from medical history.
These are output records, not distinct diseases or unique clinical events.
Equal person counts between datasets do not establish identical membership.

### Medication mapping

- Latest recorded RxNorm mapping: **115,605,653 mapped**, **9,882,619 unmapped**,
  **92.12%** of the 125,488,272 retained medication records.
- Sampled current schemas contain `drug_concept_id`; the reviewed expanded code
  maps to RxNorm ingredients. A nonzero ID does not prove a clinically correct match.
- RBC retains the **39,720,674** cleaned medication records that bb2238 rejected
  as unmapped to ATC. It does not mean every raw source row was retained: structural
  rejects still occurred before gold.
- Earlier discussion that an RBC enrichment cannot recover upstream rejects applies
  to the standalone `enrich_drug_rxnorm.py` add-on, **not this full rebuild**.
- Gold samples still lack dose, route, administration action, order IDs and encounter
  IDs. The reviewed implementation uses order time for orders/administrations and
  sets end equal to start. Do not interpret these as verified initiation or duration.
- `drug_source_concept_code` is typed `double` in sampled RBC files. Check nullness
  and type consistency before using that field; metadata alone cannot prove it is
  entirely null. Do not confuse it with standard `drug_concept_id`.

### Measurements, visits and procedures

- RBC expands the narrow five-lab/BMI/systolic-BP selection with broader lab and
  vital definitions. Blood pressure can emit separate systolic/diastolic records,
  so vital output exceeding input is not itself proof of duplication.
- Recorded lab mapping rate is **97.52%**, but its denominator is output measurements
  plus counted unmapped base names in the reviewed code. It is not full raw-data
  retention, clinical accuracy, or the same denominator as bb2238's 4.48% lab retention.
- Sampled measurement schemas omit units and result-availability timestamps. They
  sample early vital partitions; the report does not enumerate current lab concepts.
- Visits and procedures now exist, enabling richer candidate utilization/procedure
  features. Their mappings and linkage still need validation. Procedure count and
  zero reported rejects do not mean all procedure concepts mapped; ID 0 is allowed.
- Encounter-diagnosis `unmapped_snomed` rejects increased to **19,785,221**, versus
  15,187,034 in bb2238. Review vocabulary/domain differences and trial code coverage;
  more data overall is not proof of better mapping for every phenotype.

## Input lineage and versions

Study family: **2435227-CarDS-ECG**, described in the registry as adults at Yale
with at least one ECG. Recorded RBC raw input paths are under:

`/home/rbc58/mnt/implementation/cardsjdat-CC1022-MEDINT/2435227-CarDS-ECG/`

Two deliveries: **`Data-2025-04-03`** and **`Data-2026-04-15`**.
This is not the separate `2380791` DM2 extract previously profiled; do not assume
identical source semantics or populations.

Recorded RBC source groups:

| Group | Recorded inputs |
|---|---|
| Person/death | 2025 `CarDS_2435227_Patients.txt` only |
| Diagnoses | Hospital and outpatient `*_Enc_DX.txt` from both deliveries: 4 files |
| Labs | 2025 hospital shards 1–3 plus outpatient Labs; 2026 hospital shards 1–4 plus outpatient shards 1–3: 11 files |
| Drugs | 2025 outpatient administration; 2026 Meds, hospital administration shards 1–2 and outpatient administration: 5 files |
| Vitals | 2025 outpatient; 2026 hospital and outpatient: 3 files |
| Visits | Hospital and outpatient base encounter tables from both deliveries: 4 files |
| Additional history | Problem_List and Medical_Hx from both deliveries: 4 files |
| Procedures | Gold-stage runs are recorded, but their source-file lists are absent from the supplied manifests; the reviewed code targets CPT/ICD procedure extracts |

RBC includes 2026 hospital Labs_4, absent from the bb2238 run's ten lab inputs.
Patient/death data still originate from the 2025 patient extract despite newer
clinical event deliveries; check mortality freshness and event-to-person linkage.

The output was assembled across multiple runs:

- `5480ae5b-d8ef-4a75-af72-9384dcd83bc5`: July 19 UTC, successful steps **1 and 6**.
- `2fbb3f83-582b-4119-9c26-2f07418da66f`: preceding run completed **2, 7, 8, 9, 10**
  but recorded errors for **1 and 6**, subsequently rerun above.
- `556037d5-81d2-4352-92a1-29e066bd0b97`: latest recorded lab gold remapping.
- `585eb21a-c648-4192-a91f-8bfb8a927fc5`: latest recorded drug gold remapping.
- `1a0d3104-9045-42d7-9acf-633a282a2383`: recorded expanded vitals run.
- `52f8d557-2836-4817-9cb9-079bcf38b77d`: latest recorded procedure gold run.

There is no demonstrated single successful full eleven-step run in this report.
Exact producing Git revision and current partition-to-run lineage remain unproven.

Local reference repository: `/Users/ryanchoi/Desktop/Research/github/reference/cards-misc`.
Its `main` was pulled to **33532e6** on September 16; the preserved July feature
branch `feat/omop-procedures-visits` is **9e9fbc9**. Main is newer by date but has
narrower transforms. Do not run main over the RBC output assuming it reproduces it.

## Other locations: keep distinct

| Location | Evidence / role |
|---|---|
| `/mnt/raid0/bb2238/omop/gold` | Older narrow mapping; latest supplied full-run manifest June 22, 23 staged inputs. Preserve unchanged. |
| `/mnt/raid0/rbc58/mosaic/gold_rbc` | Four discovered supplemental table directories: conditions, observations, procedures, drugs. Broad discovery hit limits before sampling their schemas. |
| `/mnt/raid0/bb2238/omop/gold_rbc` | Reported missing or not a directory. |
| `/home/rbc58/mnt/ecg-tte/drugs` | Sampled CMP medication files preserve status/class, dose/unit, route/frequency, end date, setting, cohort and source_file. Potential exposure-validation source. |
| `/mnt/raid0/rbc58/mm_vhd/drug/drug_master.parquet` | Sampled footer: 135,879,464 records; preserves order/start/end/discontinuation dates and medication details. Not a complete OMOP dataset. |
| `/mnt/raid0/bb2238/ecg_ascvd/omop_database` and `/home/rbc58/mnt/ascvd/omop_database` | Older ASCVD mapping, person files report 1,113,002 rows. Possible overlap/mirroring is unverified; do not combine counts. |

The broad search does not establish whether `drug_master_v2` exists: its sampling
was limited by filename family. Source-preserving drug columns are promising but
have not been checked for missingness, validity or compatible patient identifiers.

## Next work: trial-specific feasibility, not another broad discovery pass

**Output-location update (2026-09-17):** new audit reports and per-run temporary
databases go under `/mnt/raid0/rbc58/ecg-tte/audits/`, with fresh private run folders.
This supersedes earlier home-directory destinations. Source datasets and checkout
paths are unchanged. Ryan handles any relocation of completed historical reports.

**Next H100 command (2026-09-17):** RUN_HF_MEDICATION_SCREEN.md provides the new
COMET/PARADIGM-HF lexical medication screen. Seven synthetic tests pass. It counts
candidate drug/formulation patients, exploratory outpatient Normal/Print/date strata,
recorded-history evidence and arm overlap. Brand-only, ambiguous and conflicting
names stay in review buckets. Actual drug mapping, HF eligibility, new use and fills
remain unvalidated; full-source H100 counts are pending.

**Initial trial focus selected:** Ryan wants heart-failure/GDMT trials, naming COMET
and PARADIGM-HF. See HF_TRIAL_FEASIBILITY.md. Next screen both exact drug contrasts;
COMET is a proposed first pilot, pending tartrate/formulation and HF/EF feasibility.
PARADIGM-HF requires enalapril-specific counts and explicit run-in/endpoint handling.
No protocol or drug-specific cohort is frozen or implemented.

**Full date audit now confirmed complete:** companion summary matches the group
report and all 30,929,792 records, with EOF reached and zero shape/group omissions.
All non-null ORDER_INST/START_DATE values parse. Structural date investigation is
complete for this file; remaining work is source semantics and trial-specific
prescribing/index/eligibility rules, not repeated generic date scans. Actual fills
and adherence are still unverified. Earlier companion-summary requests below are
resolved by this update.

**Latest full date groups:** supplied mode/class groups sum to 30,929,792 records,
with no omissions; all are ORDERING_MODE=Outpatient. Companion summary was not
included, so confirm run status/source checks. Normal records (18,309,003) have
100% parseable START_DATE and 96.85% same-day agreement among pairs with order
timestamps. Print agreement is 95.86%; Historical Med only 11.04%, with 5,691,895
NULL start dates. Missingness and discordance are class-dependent; the earlier
prefix must not characterize the Normal population. Preserve both date fields,
separate history from candidate prescriptions, and define a trial-specific index
before patient selection. Mode is not independently validated encounter setting
or dispensing. No new eligibility rule is frozen.

**Latest date finding:** first 500,000 records confirm ORDER_INST uses ISO minute
precision (495,563 parseable, 4,437 NULL), which the old audit omitted. START_DATE
has 223,476 parseable dates and 276,524 NULLs. Of 219,039 comparable pairs, 153,688
are same-day, 63,328 start before order and 2,023 after. No format/group omissions.
Prefix proportions cannot be extrapolated. Next obtain full-file comparisons and
review mode/class groups; no automatic switch to START_DATE or fallback is justified.

**Order versus start date:** a focused audit is ready in
RUN_MEDICATION_DATE_AUDIT.md, initially a 500,000-record prefix. It reports expanded
format recognition, masked shapes and calendar-day agreement/direction, with
restricted ordering-mode/class groups. Six synthetic tests pass; H100 results
pending. It does not select START_DATE or silently replace the order timestamp.

**Latest version 4 results:** full scan complete, same 30,929,792 records and 752,215
patient keys. All order IDs distinct within this source; no repeated-key conflicts.
Quantity positive on 22,392,680 records, but actual dispensing still unverified.
ORDER_INST has 30,001,013 unrecognized-format values and 928,779 literal NULLs;
resolve timestamp format before choosing index. Other date fields have parseable
ISO values plus literal NULLs, not complete date capture. The broad category
cross-tab omitted 5,859,926 records (18.95%); setting counts are incomplete although
whole-file quality/order-key diagnostics completed. Next use safe timestamp-format
diagnostics and focused category summaries, not another unchanged scan. See the
latest decision entry for details. Earlier readiness notes below are historical.

**Next executable audit:** version 4 `--detail-audit` adds mode/source × class/status
counts, quantity/date/refill validity and candidate null markers, plus repeated and
conflicting order-key checks. See the combined-quality command at the top of
RUN_MEDICATION_EVIDENCE_COUNTS.md. Seven quality tests and fifteen count regressions
pass locally; this combined H100 run has not occurred. No automatic fill/setting
classification or deduplication is implemented.

**Latest medication evidence (full-file report received):** version 3 literal-tab
scan completed with **30,929,792 records and 752,215 distinct nonempty patient keys**
in the 2026 RBC implementation Meds source. No empty/quoted patient keys or omitted
category records. This is all-drug source coverage, not outpatient-dispensing or
eligible-cohort N. Audited fill-date/days-supply names are absent; ORDER_MED_ID,
order/start/end/discontinuation dates and refill fields exist. Almost universal
nonempty values require null-marker and date/numeric validity checks, not an
assumption of complete clinical data. Verified fills and eligible initiators remain
not assessable. Next review approved order class/status counts and all 42 header
names for alternatives, validate identity/event deduplication and obtain source
semantics. Historical failure/tool-readiness notes below are superseded by this
completed structural scan, but no clinical source contract is yet frozen.

**Subsequent complete-header review:** QUANTITY_DISPENSED and DISPENSED_UNIT are
present but were not in the earlier audit allowlist; quantity availability must
not be described as universally absent. ORDERING_MODE, ORDER_MODE and ORDER_SOURCE
also exist and need category/semantic review. No explicit fill-date or days-supply
column is evident. Normal/Sent contains 16,446,649 records and 624,183 distinct
patient keys; Print/Sent 2,709,416 and 407,130. These overlapping source groups are
candidate prescribing strata, not verified dispensing or eligible initiator N.
All supplied class/status counts sum to the full-file total. Literal NULL is
confirmed in status values; date/refill null-marker checks remain pending.

**Medication N audit ready (2026-09-16):**
[RUN_MEDICATION_EVIDENCE_COUNTS.md](docs/RUN_MEDICATION_EVIDENCE_COUNTS.md) provides
a standard-library, read-only raw medication scan for Ryan. It counts records,
distinct nonempty patient keys, candidate fill/supply field presence, and restricted
order class/status categories. Six synthetic tests pass; no H100 run yet. Verified
outpatient-fill and eligible-initiator N are explicitly not assessable, not zero.
Those require documented dispensing semantics and trial-specific validation.

Subsequent H100 attempt failed after 400,000-record progress with a generic Error;
no valid N resulted. Version 2 now sets bounded CSV field/record limits and safe
failure reasons; 11 synthetic tests pass. An inherited CSV field limit is a plausible
cause, not confirmed. Rerun in a fresh output directory; do not skip malformed rows.

Version 2 rerun reports `csv_parse_error` after 413,839 records, not a field-size
error. Next run the bounded structural diagnostic in the same run document;
strict replay and physical-line widths are reported separately. No N or new parsing
contract has been established. Seventeen count/format synthetic tests pass.

Latest diagnostic: unexpected character after closing quote; all 500,000 inspected
physical lines have 42 columns (2,337 contain quotes; one field-start quote).
Version 3 offers explicit, schema-pinned literal-tabs reconnaissance to test the
full file without skipping rows; 21 count/format tests pass. This is provisional
format testing and raw-key counting, not a frozen ingestion contract or verified-fill
N. The latest command is in RUN_MEDICATION_EVIDENCE_COUNTS.md.

**Medication setting trace (2026-09-16):** see
[MEDICATION_SETTING_TRACE.md](docs/MEDICATION_SETTING_TRACE.md). Supplemental
`setting` values are confirmed in reviewed reports; compatible historical builder
code assigns them by source family, not encounter linkage. Reviewed OMOP code loses
drug-to-visit linkage and uses a constant drug type across medication sources.
Hospital visit code can distinguish inpatient/outpatient/emergency classes, while
outpatient-source visits are mapped broadly and need encounter-type review.
Exact producing versions remain unproven. The trace includes a targeted RBC raw
header command and proposed cohort/follow-up rules: select qualifying index events,
retain subsequent care in all settings, and do not require a future visit for entry.

1. Specify one treatment/comparator trial, target population, estimand, index rule,
   baseline window, follow-up and endpoint before examining new treatment effects.
2. Use read-only aggregates on the full RBC dataset to assess eligible arm counts,
   required covariates/missingness, pre-index history, mapping coverage and endpoints.
3. Validate order versus administration semantics and ingredient/formulation/dose
   requirements; consult the richer existing medication tables where necessary.
4. Do not use birth-based observation periods as proof of captured baseline history.
   RBC still has **20,597** people without an inferred end date. Check actual history,
   mortality freshness, chronological plausibility and follow-up ascertainment.
5. Check numerical units, result availability, repeated measurements, source-version
   overlap, zero concepts and event-to-person/visit linkage for the chosen protocol.
6. After those gates, build clinical and expanded structured PSM baselines, assess
   overlap/retention/balance, and compare clustering/cosine methods fairly. No trial
   effect or superiority result has been established in this restarted project.

## Access and preservation rules

- **Never SSH or directly access the cluster**, even for listings. Ryan pulls code
  onto the H100 and runs it. Local work is code, documentation and synthetic tests.
- **Do not modify bb2238 or the existing RBC datasets.** Current authorization is
  read-only assessment, not ETL, remapping, overwrite, repair or cache clearing.
- New reports belong in a fresh directory under Ryan's home, outside source trees.
  Patient rows, identifiers, notes, granular outputs and embeddings stay on cluster.
- `archive/2026-09-09-legacy-v1/` is historical reference only; preserve it and do not
  import its modules or treat old configurations/results as validated protocols.
- All findings here derive from reviewed aggregate/metadata reports and code review.
  Tool tests validate synthetic behavior, not clinical or statistical correctness.

## Supporting files

- [Detailed mapping audit](docs/CARDS_MISC_OMOP_PSM_AUDIT.md)
- [Read-only manifest/schema inspector instructions](docs/RUN_EXISTING_OMOP_AUDIT.md)
- [RBC output discovery instructions](docs/RUN_RBC_OMOP_DISCOVERY.md)
- [Decision register](docs/DECISIONS.md)
- [Work tracker](tasks/todo.md)
- [Operating instructions](master.md)
# Latest evidence: full HF medication screen (2026-09-17)

Confirmed complete_file/EOF, unchanged source and 30,929,792 records in
`/mnt/raid0/rbc58/ecg-tte/audits/hf-medication-screen-trqwmXRj/report/summary.json`.
All lexical bucket/date totals reconcile. Dated outpatient Normal/Print candidate
keys: carvedilol not marked extended 30,611; metoprolol tartrate 45,584;
sacubitril/valsartan 5,909; enalapril 3,126. These are not eligible HF or new-user
counts. Mapping catalog has no reported omissions but has not been clinically
validated. Next review mappings locally on H100, then assess common calendar
coverage, linked pre-index HF/EF and baseline history before freezing a trial.
All new outputs belong under `/mnt/raid0/rbc58/ecg-tte/audits/`; older home-output
instructions below are superseded. No cluster access by the assistant.
# Latest source schema evidence (2026-09-17)

Ryan confirms echo_accession_number.parquet footer: 661,062 rows, MRN/string,
EchoDate/string, EF/double, AccessionNumber/string. No report-availability timestamp
is exposed. Both 2026 hospital/outpatient encounter DX files have matching 17-column
headers with PAT_MRN_ID, PAT_ENC_CSN_ID, CURRENT_ICD9_LIST, CURRENT_ICD10_LIST,
CALC_DX_DATE, DX_DTTM and DX_DATE. Source existence/schema gate is confirmed;
EF provenance/units, exact identity linkage, diagnosis parsing and temporal meaning
remain open. Next audit those properties before declaring pre-index HF eligibility.
# Latest HF source audit results (2026-09-17)

H100 completed full medication/echo scans and 500,000-row prefixes of each DX
source. Echo: 661,062 rows/unique accessions, 314,428 MRN keys, all ISO dates;
644,905 EF values in >1–100, 16,087 null, 70 zero/scale-ambiguous/outside range.
Any pre-anchor candidate-range EF keys: carvedilol 12,574/30,611; tartrate
14,078/45,584; ARNI 4,813/5,909; enalapril 347/3,126. Not trial eligibility or
windowed/nearest EF counts. ARNI/enalapril asymmetry needs calendar/history review.
Outpatient DX prefix lacks DX_DATE/DX_DTTM on 133,279/500,000 rows despite complete
CALC_DX_DATE; its lineage must be resolved before fallback. No HF phenotype yet.
# Latest blocker: hospital diagnosis format

HF source version 2 failed_counts_invalid with row_width_mismatch in hospital DX
after progress at 42,700,000 records. Exact line/cause unknown; calendar/recency and
full DX results were invalidated. Next run docs/RUN_HF_DX_FORMAT.md, which scans only
hospital DX in two structural passes; do not rerun the full HF audit unchanged.
Previously completed version 1 reports remain separate evidence.
# Hospital DX format fix ready

Ryan confirms the single terminal hospital DX line has zero payload bytes.
Version 3 HF source audit adds --allow-hospital-terminal-empty-line, hospital-only,
EOF-only and counted separately. Other malformed rows still fail; no source edits.
18 HF tests pass. Next run updated RUN_HF_SOURCE_AUDIT.md in a fresh RAID directory.
# Both DX terminal empty lines confirmed; version 4 ready

Outpatient full diagnostic confirms 9,633,590 width-17 data lines plus exactly one
empty terminal line. Hospital has 42,763,152 data lines plus one empty terminal
line. Version 4 requires independent --allow-hospital-terminal-empty-line and
--allow-outpatient-terminal-empty-line flags. Updated run instructions include both.
19 HF synthetic tests pass; full version 4 aggregate results remain pending.
# Latest: HF version 4 completed successfully

All four sources reached EOF with unchanged-source checks; both DX terminal blanks
counted separately. Candidate EF 1–365 days before exploratory first-order anchor:
carvedilol 10,322; tartrate 12,180; ARNI 4,281; enalapril 242. Latest prior echo EF
(1,35], without a recency window: 2,227 / 831 / 2,541 / 12 respectively. These are
separate marginal summaries, not HF/new-user cohort counts. Enalapril is a major
feasibility concern. Resolve common calendar coverage and DX semantics, then joint
latest-echo recency/EF plus pre-index HF. Do not rerun structural diagnostics.
# Latest reviewed evidence: version 5 joint audit (2026-09-21)

Full source scans completed with valid accounting. DX_DATE-based prior I50 HF
plus latest strictly prior EF (1,35] within 365 days: carvedilol 704, tartrate 235.
Systolic code with no prior echo/recent null: 211/64; stale echo: 56/26. Low EF
without prior I50: 1,446/574. These are provisional phenotype groups, not eligible
new users. CALC_DX_DATE changes only one carvedilol prior-HF/no-echo key. Next
validate diagnosis coverage and index contract, then covariate availability.
No PSM, MI or treatment effect estimated. See latest decision entry for caveats.
# Shared source-table layer ready (2026-09-21)

User authorized reusable tables. scripts/build_shared_tables.py now writes all
reviewed medication, hospital/outpatient DX and echo source values to private
Parquet under `/mnt/raid0/rbc58/ecg-tte/shared/`, with typed day/key helpers and
provenance/QC. Per-source completed manifests enable integrity-checked resume.
121 active tests pass, including 12 real-Parquet tests. No H100 shared build yet;
run docs/RUN_SHARED_TABLES.md and return reviewed summary.json. Existing raw audits
are not automatically redirected. Labs/vitals/encounters/mortality and clinical
identity/timing/eligibility contracts remain separate unimplemented/unvalidated
work; no PSM or imputation has run.
# Shared snapshot now built on H100 (2026-09-21)

Ryan reports shared_sources_v1 complete in 1,114.242 seconds (~18.6 minutes),
83,987,596 data rows, 158 parts and 4,119,797,883 Parquet bytes. All four source
counts and date QC match prior audits; terminal DX blanks separately counted.
The actual snapshot directory is absent from the pasted summary; retain it from
SHARED_RUN/the printed run path. Clinical semantics remain unvalidated. Next add
verified demographics/labs/vitals/encounters as separate extensions and adapt
downstream tools to read the shared snapshot. No PSM or MICE has run.
# PSM extension header evidence received (2026-09-21)

19 candidate files exist; only 2026 Patients missing. Use 2025 demographics as a
source lead with freshness limitations. Hospital/outpatient encounters have care
setting/identity/time fields; vitals have MEAS_VALUE, UNIT and RECORDED_TIME. Labs
have component IDs/names and values/result/specimen times but no explicit units
column. 2025 labs: 51 columns; 2026: 49 (department ID/name absent). Keep versions
separate pending overlap review. Next bounded profiling and unit/source mapping,
then new shared extensions without rewriting the completed core snapshot.

# PSM prefix profile reviewed (2026-09-21)

All 19 requested 10,000-row prefixes passed with unchanged sources and reconciled
date/numeric/unit counters; 190,000 records total, no EOF and no catalog omissions.
This is bounded structural evidence, not full-file validation or cohort missingness.
Lab units absent from schemas; vital units often literal NULL. ORD_VALUE versus
ORD_NUM_VALUE needs joint/component-level interpretation before numeric features.
Next: raw-preserving shared extensions with separate delivery/source lineage and
full-file accounting, then clinical component/unit mapping and pre-index covariate
coverage. Existing four-table snapshot remains intact; extensions are not built.

# PSM raw extension ready for H100 (2026-09-21)

Run docs/RUN_PSM_SHARED_TABLES.md for all 19 new source tables under RAID shared/.
Core snapshot is untouched. Unknown counts discovered at EOF; explicit terminal
empty-line option counts at most one exact final blank per file. All original
lab/vital values retained; clinical mapping and delivery deduplication pending.
133 local tests pass. H100 full-source build/runtime/compressed size unmeasured.
Completed older snapshots remain readable; engine hash changed, so do not resume
old interrupted builds with this release.

# COMET design work while extension runs (2026-09-21)

Review docs/COMET_COHORT_DRAFT.md and docs/COMET_COVARIATE_DICTIONARY.md. Clinical
criteria/windows are proposals with explicit unresolved gates; not a cohort run.
select_preindex_measurements.py implements only the mapped-event selection
primitive (date-only, strict pre-index, latest observation, no older fallback,
unit/availability/conflict flags, source lineage). No patient data or cluster job.
146 tests pass including 13 new selection tests. Builder and all hash dependencies
are unchanged from c5ba178, so this preparation does not alter the running build.
Next needs completed extension summary and reviewed component/unit/timing maps;
then raw-to-feature adapters, baseline coverage, imputation and matching in order.

# COMET candidates can run before labs finish

User wants actual candidate cohort preparation while conversion runs. New
RUN_COMET_CANDIDATES.md is runnable in a second tmux window, using the uniquely
discovered completed core snapshot only. New output is restricted patient-level
Parquet plus retained family-order SQLite and aggregate summary. Joint first
lexical arm anchor changes denominators relative to prior per-arm audits; no
clinical eligibility/new-use claim. Keeps competing-arm ties, prior history and
HF/EF groups for review, without future-event exclusions. 152 tests pass; running
builder hash dependencies unchanged. Return reviewed candidate summary next;
lab completion is not a prerequisite for this job.

# 2026-09-21: PSM extension failed on third 2025 hospital lab shard

Ryan supplied status=failed after 8,420.996 s, failure stage
Data_2025_04_03_hosp_enc_labs_3, BuildError/line_exceeds_limit. Six completed
stages are retained, including labs1 115,899,065 rows (2,621.968 s) and labs2
116,360,130 rows (2,701.132 s); one separately counted terminal blank each. The
whole extension remains incomplete and cannot feed the shared reader. Error
proves >1 MiB physical record only, not corruption or the actual maximum size.
Prepared constant-memory, value-free full byte-structure diagnostic of this one
source. No raw edits, row skips, parser relaxation or builder hash changes.
Recovery must explicitly verify/reuse existing stages under any changed parser
contract; unchanged resume would repeat failure. COMET candidate job remains
independent on the complete core snapshot. See RUN_LAB_LONG_LINE_DIAGNOSTIC.md.

# 2026-09-21: Lab shard 3 has a structurally invalid terminal record

Full diagnostic reached EOF with unchanged source: 87,246,327 width-51 lines,
then one final unterminated 15,529,283,887-byte record with only five columns and
NUL bytes. No exact empty line. Source is 66,081,132,812 bytes; diagnostic took
900.682 s. This is not resolved by raising the parser limit. Root cause remains
unknown; no raw truncation, skip, parser relaxation or partial-cohort substitution.
Obtain a verified intact source copy or corrected export with lineage/completeness
evidence. Preserve six completed extension stages and the failed run; recovery
requires integrity-checked reuse and an explicit corrected-source contract.
Independent COMET core-snapshot candidate work can continue. Details and reviewed
post-header data checksum recorded in docs/LAB_SOURCE_RECOVERY.md.

# 2026-09-21: COMET status recovery and bounded lab-tail sampling

User requested checking previous COMET completion and inspecting/possibly ignoring
the malformed lab region. Added read-only check_comet_runs.py: find saved runs,
verify completed candidate hash/footer/counts and manifest references; never infer
process liveness from saved building status. Added inspect_lab_tail_bytes.py: five
4 KiB windows, byte-category counts only, no clinical text or source edits. Samples
cannot justify discarding 15.53 GB or establish upstream completeness. Full suite
164 tests passes, including seven new status/sampling tests. H100 checks await
Ryan; no cluster access performed and no new candidate job automatically started.

# COMET candidate roster completed: reviewed H100 summary

comet_candidates_v1 complete_provisional_candidates/counts_valid=true after
348.81 seconds (5.81 minutes); 30,929,792 medication records scanned. Candidate
patient keys 71,814 = carvedilol 27,458 + tartrate 44,330 + 26 competing-arm ties.
All evidence groups reconcile separately within each arm and diagnosis-date view.
DX_DATE prior provisional HF plus recent latest echo EF (1,35): 577/154; EF=35
adds 19/8, giving (1,35] totals 596/162. Systolic code with no prior echo/recent
missing EF: 193/50; stale echo: 45/18. These remain evidence strata, not final
eligibility or validated percent EF. Compared with previous per-arm anchors, this
roster uses a joint earliest arm anchor; denominator/selection changed explicitly.
Prior365-day carvedilol/metoprolol family order flags: 9,502/15,766. Undated family
order flags: 4,619/7,252. Flags overlap, are not a full-class washout, and cannot
be subtracted from HF/EF group marginals to obtain eligible new-user counts.
Completed core snapshot now explicitly known:
/mnt/raid0/rbc58/ecg-tte/shared/source-v1-9Ka1kA0i/snapshot.
Candidate run directory absent from this summary; retain via status checker.
This confirms reported candidate completion; no independent cluster artifact
verification performed here. Next intersect prior-history/uncertainty flags with
HF/EF groups and calendar coverage using the saved roster; validate drug/identity/
observation/index semantics before final cohort. No MICE/PSM or effect estimation.

# User supports broader systolic-code OR EF<40 adaptation

User expressed comfort with pre-index HFrEF-oriented codes OR EF<40 rather than
requiring general HF plus EF<=35. Treat as an authorized direction for a separately
named COMET-inspired adaptation, not a silent redefinition of strict COMET or a
validated phenotype. Preserve requested strict <40 boundary; EF=40 should be counted
separately (guideline HFrEF uses <=40). Existing broad I50 counts include general
HF and are not HFrEF-specific. Existing systolic search includes I50.2/I50.4 parents
and their 0-3 children; current DX_DATE roster counts are 661 carvedilol and 213
tartrate with any prior systolic/combined code, not confirmed current reduced EF.
Official CMS labels support systolic and combined systolic/diastolic code meanings;
ACC/AHA guideline distinguishes reduced EF from improved EF. Coding alone cannot
guarantee contemporary EF, and EF alone can represent asymptomatic LV dysfunction.
Next count code-only, EF-only, both, and code with latest EF>=40 separately using
validated percent EF and prior dates; latest>35 bins cannot yield <40 counts.
Retain proposed365-day latest-echo rule and no fallback; code recency/validation,
clinical HF evidence, drug/new-use and identity remain unresolved. No new cohort
counts, eligibility changes in code, imputation or PSM performed this turn.
References: CMS A56952 code table; ACC/AHA/HFSA 2022 guideline (JACC DOI
10.1016/j.jacc.2021.12.011).

# Count-only general-HF/diastolic-exclusion sensitivity prepared

User requests numbers for systolic-code OR EF<40 and a general HF-code alternative
excluding explicit diastolic/HFpEF evidence. Implemented count_comet_hf_variants.py
on the fixed completed candidate roster, re-reading only projected echo/DX tables.
Report six scenarios: systolic OR EF baseline; general OR EF; isolated-diastolic/
HFpEF exclusion versus any-diastolic (including combined) exclusion, each either
on the code branch or the entire patient. This resolves ambiguity by reporting
both, not silently choosing a cohort. Name flags use DX_NAME lexical matching,
not negation-aware NLP; no raw names exported. Strict prior dates, independent DX
views, latest365-day EF >1 and <40, EF=40 separate, no older fallback. No eligibility
change, washout, MI or PSM. Source maps/units/availability remain unvalidated.
Six synthetic tests including complete Parquet integration pass. H100 counts
pending; do not infer N by adding overlapping prior summaries.

# Broader COMET HF/EF count variants completed

Reviewed comet_hf_variants_v1 complete_count_only/counts_valid=true, 225.127 s.
All evidence strata reconcile with fixed arm denominators and all scenario deltas
recompute correctly. DX_DATE counts (carvedilol/tartrate; unresolved arm ties
excluded from these totals): systolic/combined OR EF<40 2,859/1,112 (3,971); general
HF OR EF<40 4,454/2,922 (7,376); isolated-diastolic/HFpEF exclusion on code branch
4,161/2,563 (6,724), entire patient 4,109/2,554 (6,663); any-diastolic/HFpEF
exclusion on code branch 4,104/2,530 (6,634), entire patient 4,017/2,513 (6,530).
CALC_DX_DATE adds one carvedilol to each general-code scenario; systolic baseline
unchanged. 26 denominator arm ties yield one baseline/two general-rule candidates
and remain separate. Broad literal entire-patient rule adds 2,559 versus systolic
OR EF baseline, but is not a validated HFrEF phenotype. Code-branch low-EF rescue
adds 104 over any-diastolic entire-patient exclusion. Name exclusion is lexical
(any prior DX_NAME signal), not adjudicated/negation-aware. No prior-history
exclusion, new-use verification, endpoint validation, MICE or PSM. Next cross-tab
phenotype evidence with prior/undated medication history and observation/calendar
coverage; do not choose a phenotype solely for N. Candidate report now known:
/mnt/raid0/rbc58/ecg-tte/audits/comet-candidates-c2FSBqdW/report.

# User-selected first analysis population: broadest HF OR EF<40

Remember user preference to start with the largest cohort: DX_DATE general prior
I50 HF OR latest prior EF<40 (numeric >1), 365-day echo window, NO diastolic/HFpEF
exclusion, no competing-arm ties: 4,454 carvedilol +2,922 tartrate =7,376. This is
the first exploratory COMET-inspired population, not a validated HFrEF/new-user
cohort or frozen statistical protocol. Preserve stricter variants for sensitivity
analyses; do not select based on later effect fit. Added dedicated selected-cohort
document and audit_comet_broad_cohort.py to materialize this roster and report
prior/undated family-order combinations, calendar strata and code/EF evidence.
Reads only candidate artifact plus echo, no labs or repeated DX scan. No history
exclusion applied, no MICE/PSM/effects. Three new synthetic tests pass.

# CURRENT USER DECISION — supersedes no-exclusion 7,376 selection

User explicitly confirmed (general HF code OR EF<40) with entire-patient prior
diastolic/HFpEF exclusions, including combined systolic/diastolic signals. This
is the first of the clarified alternatives, NOT requiring both HF and EF<40.
Expected DX_DATE counts 4,017 carvedilol +2,513 tartrate =6,530. Prior 7,376
no-exclusion interpretation was mistaken and is superseded; retain only as a
named sensitivity. Corrected dedicated selected-cohort doc and README.
audit_comet_broad_cohort.py version2 applies the exact audited exclusion helper
to strictly prior DX_DATE rows, including low-EF candidates; reports 437/409
expected removals and history/calendar strata. Reads core DX projections again,
no labs. Tests verify prior exclusions beat low EF and same/future diagnoses do
not exclude. Fresh output required; no overwrite/reuse of version1 selection.
No final phenotype/identity/new-use/endpoint validation or PSM implied.

# Selected excluded COMET exploratory cohort materialized successfully

Reviewed comet_broad_exploratory_v2 complete_exploratory_cohort_audit/counts_valid,
149.834 seconds. Exactly 6,530 =4,017 carvedilol +2,513 tartrate; removals437/409
from prior4,454/2,922. Arm totals, history/evidence/calendar totals and history by
calendar intersections reconcile. Prior365 family order found1,364/982; no prior
found but undated352/183; neither found2,301/1,348. No prior365 found inclusive of
undated is2,653/1,531 (4,184); neither prior nor undated totals3,649. These are
flags, not final new-user counts: class coverage/observation unvalidated, no history
exclusion applied. Evidence basis code-only1,639/1,572, EF-only1,723/756, both655/185.
Code-only and EF-only composition differs across arms; not all candidates have
confirmed HFrEF. Most anchors2013–2024; 2012four total and2025–2026five total.
Do not freeze calendar exclusions based solely on these counts. Core remains
independent of damaged lab source. Selected materialization output path absent
from this summary; preserve run path on H100. Next validate class-wide drug history
and baseline observation, then covariate availability and missingness before PSM.
No MI/matching/effect estimate has run.

### 2026-09-21: next index/eligibility evidence check

Added scripts/audit_comet_beta_history.py and docs/RUN_COMET_BETA_HISTORY.md. Uses selected v2 report discovery, preserves 6,530 roster/dates, scans broader named beta-blocker history and creates restricted mapping catalog. No clinical new-user N or PSM; medication-ID/route/observation validation remains pending. No lab extension dependency; no source recovery or raw edits. H100 execution pending.


2026-09-21 reviewed beta history: complete_history_screen, 202.146 seconds; groups reconcile to 4,017/2,513. No named-generic prior365 lead: 2,428/1,359 (3,787 total). Additionally no undated generic or unresolved prior/undated lead: 2,089/1,180 (3,269), retaining same-day flags. These are lexical screens across all routes/classes, not eligible new-user counts. 7,071 index source rows verified; 598 private mapping combinations. Exact selected report: /mnt/raid0/rbc58/ecg-tte/audits/comet-broad-excluded-cnG52aaY/report. No exclusions or washout policy changed. User raises concern about excessive restriction; criterion-level pass/fail/unknown feasibility and explicit adapted versus closer-trial definitions remain needed before PSM.


### 2026-09-21 — Explicitly adapted COMET selected

User confirms an explicitly adapted COMET study. docs/COMET_ADAPTED_PROTOCOL.md is the current design direction: preserve the selected broader HF/low-EF starting rule with whole-patient diastolic/HFpEF exclusions; audit each original criterion as pass/fail/unknown before freezing adapted eligibility. No washout length or blanket omission of unavailable criteria approved. No roster, index or PSM changes. Older conflicting draft phenotype proposals are superseded.


### 2026-09-21 — Core eligibility feasibility implementation

Added audit_comet_eligibility.py and RUN_COMET_ELIGIBILITY_FEASIBILITY.md. Fixed selected roster, complete core sources only. Reports 32 original criteria with clinical ascertainment unknown, EF35/40 numeric screens, 14/30/90/180/365 lexical beta windows, selected background/prohibited medication names and two-calendar-month MI/cerebrovascular code leads. No false pass from absent evidence, no clinical exclusions, no new index or PSM. Restricted representative provenance on H100. Failed extension not bypassed; remaining source and mapping requirements explicit. H100 run pending.


### 2026-09-21 — Core eligibility feasibility results reviewed

Completed in206.323s; 6,530 roster unchanged. Numeric screens and overlapping groups reconcile by arm; signal complements reconcile. EF≤35:1,832/663=2,495; EF<40:2,378/941=3,319; numeric EF≥40:612/728=1,340; unknown recent usable EF:1,027/844=1,871. This explicitly shows the selected OR phenotype includes measured EF≥40; it cannot be labeled uniformly HFrEF. No-prior named-beta screen totals14/30/90/180/365days:5,768/5,366/4,732/4,303/3,787; not validated washout. Recent MI signals131/106; cerebrovascular110/94; overlap prevents summing exclusions. All32 clinical criteria are unknown by design in the script, not an empirical finding that every measurement is missing. No clinical eligibility or attrition established. Next unblock complete demographics/encounters/vitals source availability and medication mapping, rather than repeat core scans.


### 2026-09-21 — Independent clinical source build

Implemented build_clinical_shared_tables.py: eight explicitly selected demographic/encounter/vital sources across 2025/2026, no labs or unavailable2026 Patients probe. Fresh independent snapshot under RAID; no failed-snapshot bypass/promotion. Existing shared builder and implementation hashes unchanged; new driver hash in source specs protects resume. Clinical semantics, delivery overlap and identity unvalidated; next audit DOB, observation and vital mappings after H100 completion. Run instructions in RUN_CLINICAL_SHARED_TABLES.md.


### 2026-09-21 — Declared PSM baseline extraction target

Specified33 variables in docs/COMET_PSM_TABLE_V1.md/.json:3 demographic/calendar,5 physiology,4labs,9comorbidities,8prior-order classes,4utilization. Three metadata fields separate; QC/provenance/eligibility/outcomes not PS predictors. Source maps/availability/clinical validity and model encoding remain pending; no silent feature dropping, no unavailable-source imputation. Fixed extraction target, not a fitted or final-ready model.


### 2026-09-21 — Independent clinical snapshot complete

Reviewed eight-table summary: complete,1024.926seconds (~17.1min),108521653rows,208parts,3425046652output bytes. Physical-line/terminal-empty accounting, patient-key and all date-QC sums reconcile. 2025patient/encounter/vital source hashes match earlier successfully built stages. Clinical semantics/identity still unvalidated; neither unique-patient coverage nor clinical missingness inferred from row counts. No labs included; no new cohort exclusions or MICE/PSM. Actual clinical snapshot run path not supplied in pasted summary. Next audit cohort linkage/DOB, pre-index encounters and vital IDs/units against complete clinical snapshot, preserving delivery separation.


### 2026-09-21 — Cohort-specific clinical baseline QC prepared

Implemented audit_comet_clinical_baseline.py and RUN_COMET_CLINICAL_BASELINE_QC.md: discovery of one exact eight-table completed clinical snapshot, candidate DOB/sex agreement, prior365 encounter key coverage and cross-source/date/patient conflicts, prior vital component/unit/value-shape catalog with90-day split. Restricted catalogs/patient QC remain on H100. No clinical setting assumptions, numeric vital extraction, cohort changes or MICE/PSM. Synthetic integration verified; cluster run pending.


### 2026-09-22 — Clinical baseline QC completed

Reviewed complete_clinical_baseline_qc/counts_valid,347.168seconds (~5.8min). All6,530 have adult_numeric age and a single raw sex code/label pair (4,017carvedilol/2,513tartrate); labels and identity remain unvalidated. Each source encounter-coverage pair reconciles. Prior365 2025hospital-source keys:3,922/2,482; outpatient-source:2,237/1,522. Only5 encounter rows in2026hospital sources and no2026vital pre-index rows reported; temporal/source coverage requires interpretation, not automatic data-loss diagnosis. No overlapping patient/CSN across sources, conflicting key dates or cross-patient CSNs in this selected dated window; no global uniqueness claim. 88,841 prior365 vital rows from2025outpatient source;32catalog combinations. Clinical snapshot path /mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-t9ZGomLT/snapshot. Next review restricted component/unit/sex/setting catalog locally; no vital patient-level availability or usable baseline values established yet. Cohort unchanged; noMICE/PSM.


### 2026-09-22 — Clinical mapping catalog reviewed

32vital catalog rows reconcile to88,841 prior365 records. Observed component labels:5 BLOOD PRESSURE/BP slash pairs;8 PULSE;301070 R BMI/BMI(Calculated); all three UNIT=NULL. Height11/Inches, weight14/Ounces, SpO2 10/% are explicit; do not assume weight pounds or temperature scale. Prior90 candidate patient counts BP1,300/884=2,184; pulse1,292/875=2,167; BMI1,121/703=1,824. These are any-record counts, not latest valid feature completeness;365-day BMI union unavailable from overlapping bins. Sex1/Female2,522;2/Male4,008, total6,530; raw observed mapping established, historical availability unvalidated. ED_YN/INP_YN include00/01/10/11; preserve overlapping flags,00 not automatically outpatient. Units, BP pair orientation and timestamp semantics need source metadata or an explicit validated component contract before canonical vital extraction. No eligibility/PSM changes.


### 2026-09-22 — Latest prior vital staging extractor

Implemented extract_comet_vital_candidates.py with known clinical snapshot path and RUN_COMET_VITAL_CANDIDATES.md. One row per existing candidate, paired raw BP components, pulse and365-day BMI; separate no-record/latest-unusable/tie/undated/mapping-change statuses and restricted raw lineage. Units/BP orientation/availability/ranges unvalidated; ready_for_mice false. Asked user about flowsheet dictionary/source confirmation; no confirmation received at implementation time. No canonical-unit assumption or cohort exclusions introduced.


### 2026-09-22 — Vital candidate extraction completed

Reviewed complete_candidate_extraction,301.034s,6,530 unchanged. Joint and feature marginals reconcile by arm. Numeric raw-scale candidate totals:BP1,937(1,143/794),pulse2,060(1,235/825),BMI2,853(1,720/1,133). Latest-day disagreements247/107/13; no-record-in-window4,346/4,363/3,664 respectively. Allthree numeric1,694; no records for allthree3,437. BP/pulse numeric+disagreement equal earlier90-day catalog unique counts2,184/2,167. Disagreements can represent repeat readings at different times on one day under conservative day-level selector, not necessarily source errors; exact-time alternative requires explicit versioned timing policy. Units/orientation/availability/range checks remain unresolved and ready_for_mice false. Next resolve component metadata, assess timestamp handling, then finalize missingness before MICE; do not use complete-case requirement as implicit eligibility.


### 2026-09-22 — Vital v2 repeat-reading and auxiliary rules

User agreed to continue after averaging BP/pulse and latest BMI discussion. Implemented latest-day, latest-encounter BP/pulse mean with exact-duplicate weighting; paired BP values retained. BMI latest exact timestamp with conflicting ties unresolved. Additional older91–365-day BP/pulse candidate columns are auxiliaries only, not baseline fallback. Arm/year and primary-versus-older coverage added for imputation readiness. No claim that MAR or predictive support is established, no MICE yet; units/ranges/availability still unresolved. Fresh version2 outputs required.


### 2026-09-22 — Vital v2 result reviewed

Complete_candidate_extraction,362.935s. All6,530 retained; primary/older feature totals, arm/year marginals and primary joint counts reconcile. BP2,184,pulse2,167,BMI2,866 raw numeric candidates; all prior247/107/13 latest-day disagreements resolved under explicit v2 rules. No-record counts4,346/4,363/3,664 (66.6/66.8/56.1%). Older91–365day evidence available for1,033patients lacking90-dayBP and1,011lacking90-daypulse (~23.8/23.2% of respective missing groups). These are potential auxiliaries, not replacements or demonstrated predictive support. Missing both recent/older:BP3,313,pulse3,352. Units/orientation/availability/ranges remain unvalidated; ready_for_mice false. Next resolve measurement contract and finish broader baseline covariate extraction before MICE diagnostic pilot; no further cohort changes.


### 2026-09-22 — Unified baseline staging assembly

Implemented build_comet_baseline_staging.py and RUN_COMET_BASELINE_STAGING.md: fixed33-column target plus3metadata, separate patient/feature statuses, exact vital-v2 hash/roster alignment, demographic/EF candidates, explicit positive diagnosis/name leads and encounter-key/flag count proxies. Four labs blocked; absent code/drug evidence and zero utilization remain null with negative-ascertainment/coverage blocks, not normal MICE missingness. Vocabulary and clinical roles unvalidated; no eligibility/PSM changes. This is a unified review artifact, not ready-for-MICE. H100 run pending.


### 2026-09-22 — Baseline staging result reviewed

Complete_baseline_staging,283.876seconds;6,530rows/33covariates. All66arm-feature totals reconcile. Age/sex/year complete; EF4,659;BP2,184;pulse2,167;BMI2,866 candidates;4lab slots entirely source-blocked. Diagnosis/drug slots intentionally contain positive leads or blocked nulls, not validated0/1 predictors and cannot be directly imputed with only observed1s. HF-admission candidate linkage only16patients versus5,361with hospital-flag count; requires date/code/encounter-join investigation, not acceptance as clinical HF admission prevalence. Low recorded diagnosis leads (diabetes401,hypertension983) also warrant source/date/ICD9 coverage check before negative coding. QC190patients with unparsed priorDX,3,613with any undated medication orders,0encounter-key problems. Vital v2 report path /mnt/raid0/rbc58/ecg-tte/audits/comet-vital-v2-fh8lNqlw/report. No MICE/PSM or cohort change. Next prioritize diagnosis date/key coverage and HF admission linkage, then explicit recorded-evidence zero policy; lab recovery and units remain blocked.


### 2026-09-22 — Recorded evidence policy accepted; HF linkage diagnostic prepared

User approved practical diagnosis/order binary coding:1 qualifying recorded lead,
0 no qualifying record in declared available source/window, null technical
uncertainty. Zero is not true clinical absence and is not imputed. Implemented
baseline staging v2 with positive precedence, feature-specific undated leads and
missing/unparsed data blocks; no new eligibility/observation restriction. Existing
33 slots and cohort/index retained. HF feature remains same-patient/CSN INP_YN=1
plus strictly prior365 I50 DX_DATE, described as inpatient encounters with HF,
not HF-caused admissions. Added separate aggregate linkage stages by diagnosis
source and date bucket, with index-year code/date/key coverage and ICD9 presence.
Alternative/future dates remain diagnostic-only, never baseline fallback. Utilization
zero handling unchanged pending this audit. H100 v2 execution/results pending;
MICE/PSM remain unrun. See RUN_COMET_BASELINE_STAGING.md for fresh RAID command.


### 2026-09-22 — Baseline v2 and HF linkage results reviewed

Completed baseline staging v2 in439.167s (7.3min);6,530patients,33features.
All66arm-feature denominators reconcile to4,017/2,513. Recorded binary zeros
implemented; diagnosis technical-null counts293–1,501 (4.5–23.0%) and medication
44–451 (0.7–6.9%) per feature. Positive counts unchanged. Vitals/EF/labs unchanged;
no MICE/PSM. Missing diagnosis timing contributes beyond190patients with malformed
prior code cells; unassessable is not solely malformed coding.

HF diagnostic:9,373 inpatient encounter keys (5,048/4,325),5,361patients.
Only212keys(128/84),195patients(113/82),match ANY hospital diagnosis at any date;
no outpatient diagnosis matches. Same-key HF any date19keys/18patients; prior365
DX_DATE17keys/16patients. CALC_DX_DATE gives identical counts; two HF keys are older.
Thus dominant loss is same-key diagnosis linkage/capture, not HF specificity or
DX_DATE window. Do not relax dates or interpret unmatched encounters as HF-free.
Cause unproven: check diagnosis/encounter delivery alignment, source coverage and
key conventions. Current core diagnoses are2026 delivery; nearly all baseline
encounters come from2025 delivery. This is a hypothesis to investigate, not proof
of incompatible identities or permission for fuzzy matching.

Diagnosis coverage: hospital prior365141,578rows (141,267parseable ICD10),
outpatient prior365201rows (200parseable), versus37,282outpatient rows without
DX_DATE and110,430future rows. ICD9 presence overlaps ICD10; cannot sum as extra
patients or claim ICD9 explains linkage loss. Next source/delivery/key coverage
check before promoting recorded zeros into a final model; no cohort change.


### 2026-09-22 — User approves all-cause hospitalization adjustment

Removed HF-specific hospitalization predictor from current PSM target, explicitly versioned as COMET_PSM_TABLE_V2.json:32covariates. Baseline staging v3 emits35columns including3metadata; all-cause prior365 inpatient-flagged encounter counts retained unchanged. HF linkage diagnostic remains separate QC only. No cohort/index/endpoint changes; utilization zero handling unchanged. H100 v3 run pending; no MICE/PSM.


### 2026-09-22 — Baseline v3 result verified

Reviewed complete_baseline_staging/counts_valid v3,364.364s (~6.1min),6530rows/32covariates. All64arm-feature denominators reconcile to4017/2513. HF-specific predictor absent; all remaining feature-status counts exactly equal v2. All-cause inpatient positive counts5361;1169remain null under unchanged utilization-zero policy (not measurement missingness). No encounter-key problems. Four labs entirely source-blocked; vital units/orientation unresolved; diagnosis source alignment remains relevant to comorbidity capture despite HF-feature removal. No MICE/PSM. Do not repeat this unchanged staging run; next resolve utilization recorded-zero policy, measurement contract and usable lab source coverage, and diagnosis delivery alignment.


### 2026-09-22 — Recorded utilization zeros approved and prepared

User approves continuing with0 for no recorded baseline encounter. Added hash-checked finalize_comet_utilization.py to convert completed v3 to v4 without raw rescans. Exactly three utilization zero_coverage_unvalidated states become0/no_qualifying_record; positive counts, technical nulls, all other32feature slots, cohort/index and endpoints preserved. This counts qualifying dated records only; no complete-observation claim, no undated timing imputation. Expected inpatient1169/ED1692/outpatient2771conversions (overlapping). H100 execution pending. Labs still unavailable and vital contract unresolved; no MICE/PSM. RUN_COMET_UTILIZATION_ZEROS.md provides fresh RAID command.


### 2026-09-22 — Baseline v4 conversion verified

Reviewed complete_baseline_staging v4/counts_valid,0.86s,6530patients/32covariates. All64arm-feature denominators reconcile; exact comparison with v3 confirms only expected utilization null-to-recorded-zero changes. Hospital5361positive/1169zero,ED4838/1692,outpatient3759/2771; no utilization nulls remain in this run. Other feature/status counts identical. Source v3 report path /mnt/raid0/rbc58/ecg-tte/audits/comet-baseline-v3-XhcifvB2/report; v4 destination not supplied. No MICE/PSM; next resolve vital measurement contract, lab availability and diagnosis capture. No further unchanged staging reruns needed.


### 2026-09-22 — Remaining source dependency check prepared

User confirms no source documentation for BP/pulse/BMI units or intact replacement lab3currently available. Prepared check_comet_source_dependencies.py: bounded diagnosis headers in both deliveries,11lab-file metadata probes, dictionary-like filenames and saved lab-stage/catalog locations. No patient rows/labcontents, no source substitution or promotion of failed snapshots. Two synthetic tests pass,204total. H100 run pending; RUN_COMET_SOURCE_DEPENDENCIES.md. Keep progressing source recovery/measurement contract without rerunning unchanged baseline.


### 2026-09-22 — Source dependencies result reviewed

Metadata check completed2.503s,no warnings. Both2025DXsources exist with same17-column hash as2026: hospital32,958,318,913bytes andoutpatient10,409,771,048bytes versus2026hospital7,232,195,120/outpatient1,607,545,803. Larger size is not proof of historical coverage, overlap or integrity. This provides concrete candidates for matched-delivery linkage and comorbidity audits; do not silently replace/union sources or change current cohort. Expanded DXmay also change HF/diastolic eligibility evidence; assess separately on fixed cohort first and preserve potential attrition/entry accounting.

All11labpaths present_metadata_only. Known damaged2025hospital shard3still66,081,132,812bytes; no intact replacement established. Failed snapshot retains reported lab1/2stages115,899,065/116,360,130rows; not authorized as globally complete.2025outpatient lab source9,301,880,219bytes provides an independent candidate for baseline lab feasibility. Saved catalog /mnt/raid0/rbc58/ecg-tte/audits/psm-source-profile-Nbo4yhXs/report/restricted_measurement_catalog.json. No dictionary-like filenames in bounded searched directories; not proof none exists elsewhere. Next same-delivery2025DXbuild/linkage audit and explicit limited lab-source feasibility with integrity checks; no claimed units or MICE readiness.


### 2026-09-22 — Independent2025DX and limited outpatient-lab phase prepared

User approved separate2025DXbuild and available-source lab feasibility. Implemented build_comet_2025_sources.py with separate diagnoses/outpatient-labs domains and strict existing shared-source engine; no engine fingerprint edits. Select exactly2025hospital/outpatientDX and separate2025outpatientlabs, no damaged shard or failed-snapshot bypass. Added fixed-cohort audit for same-delivery inpatient-key linkage, prior365DXsignals and any-prior exclusion signals without roster changes; prior90RESULT_DATElab presence plus restricted component catalog. Lab count is not four-analyte completeness. Two synthetic tests added,206total pass. RUN_COMET_2025_SOURCES.md complete chained H100 block; build/audit results pending. No eligibility/endpoint/MICE/PSM changes.


### 2026-09-22 — 2025 source audit reveals material diagnosis coverage gap

Reviewed complete_fixed_cohort_feasibility/counts_valid with unchanged4017/2513denominators and same cohort SHA.2025hospitalDXmatches9361/9373baselineinpatientkeys(99.87%;5042/5048C,4319/4325T), versus212/9373using2026DX. Strong evidence source-delivery coverage caused prior low linkage; not global identity validation. All per-arm patient counts within denominator.2025prior365hospitalDXpatients3939/2486, outpatient2393/1540.

Newly observed any-prior diastolic/combined/HFpEF code or lexical exclusion signals947C/672T=1619(24.8%); prior365833/578=1411. If unchanged exclusion algorithm applied only to fixed current roster,4911wouldremain(3070/1841), NOT a final rebuilt cohort N: original broader candidate set may gain HF evidence and need reassessment. Signals lexical/not adjudicated. No exclusion or HFpredictor reinstatement performed. Source gap affects comorbidity and cohort ascertainment; v4not finalmodelready.

Outpatientlabs prior90RESULT_DATEcoverage259C/187T=446(6.83%), anylabnotfour-analyte completeness.279catalogcombinations,0omitted. Lab buildcompleted; progresslast15,624,429is not asserted finalrowcount. Independent sources successfully opened by audit. Paths: diagnoses-2025-nauv2IgF/snapshot(hashb713a94e17640b3795981d4d808f8a9bdbfd18bd8fdf2c128e5d81cfab601b8a), outpatient-labs-2025-fOMEo0i1/snapshot(hash93b23938a89ec2269152c76374b86cb6cf7cb302a6db7ef7e1343cfd4082ab9b), under sharedroot. Need expanded diagnosis-source cohort reassessment before imputation, and integrity-verified limited hospital lab recovery forcoverage. No MICE/PSM.


### 2026-09-22 — Expanded diagnosis reassessment and limited lab reuse prepared

User approves reassessing original medication candidates with both diagnosis deliveries under unchanged HF/EF/exclusion rule. Added reassess_comet_diagnoses.py: newversion, originalanchors, Boolean evidence union, retained/entered/removed/not-selected summaries and restricted transition table. Old roster/baseline preserved; downstream oldversionreadersrejectnewversion. Separate reuse_comet_hospital_labs.py copies completed2025lab1/2stages into fresh explicitlylimitedsnapshot with Parquet+rawsourcechecksums through unchangedengine; failedparent untouched, shard3notread, no integritybypass. Synthetic entry/removal/futurecutoff and alteredrawsource failure tests pass;208total. H100 RUN_COMET_REASSESSMENT.md pending. No MICE/PSM or endpoint change.


2026-09-22: Latest attachment repeats prior comet_2025_source_audit_v1 output with identical cohort/source hashes and counts; no expanded-diagnosis reassessment or limited-hospital-lab reuse result present. Do not infer those jobs ran or repeat source builds. Next inspect saved comet-expanded-dx/hospital-labs-limited run summaries.
