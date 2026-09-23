# Handoff history (moved verbatim from handoff.md on 2026-09-23)

Superseded where the current brief in `handoff.md` says so. Kept for provenance.

## Historical brief and chronological evidence (superseded where noted above)

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


2026-09-22 latest execution update: expanded DX reassessment COMPLETE/counts_valid,793.135s. Selected9735=5867carvedilol+3868tartrate; retained4911,entered4824,removed1619 versus prior6530. Arm/history/calendar/evidence totals reconcile. Still exploratory, not final eligibility. Lab reuse log has started shard1verification; completion and current live process status not established. This supersedes earlier statement that reassessment had no saved result.


### 2026-09-22 — Efficiency audit and hospital lab reuse completion

Reviewed limited lab snapshot COMPLETE:232259195rows,411parts,5658061845compressed bytes,engine verification elapsed1441.904s(not full copy+verification walltime). No need repeat recovery. Added PIPELINE_EFFICIENCY_AUDIT_2026_09_22.md based on code, aggregate evidence and JAMA RCT-DUPLICATE. Priorities: source/delivery registry; shared cohort interface; Arrow-filtered reusable broader-candidate extracts; consolidated mapping/QC/features; persistent runner/status and dependency-aware caches; outcome work in parallel. Preservechecksums/clinicaldecisions. Multi-trial/method registry fixes cohort/estimand/outcome for representation comparisons; cohort-construction methods separateaxis. No performance gains measured or methods implemented by audit; no new clinical rule frozen.


### 2026-09-22 — Benchmark direction and candidate-cache implementation

User confirms the goal is consistency of agreement with published randomized trial effects across unadjusted, clinical PSM, EHR representations, ECG representations and combinations. Population differences across frameworks are permitted but must be reported; retain paired common-population comparisons where feasible to distinguish population from adjustment effects. Agreement does not establish unbiasedness; no tuning to published treatment effects. PSM is the first working analysis. CLMBR-T is the selected EHR model direction; checkpoint/input contract remain unselected. ECG model and fusion specification remain open. No statistical analysis plan or endpoint is frozen by this choice.

Implemented native Arrow patient filtering in diagnosis reassessment, vital extraction, baseline staging and the 2025 source audit. Added all-date/all-column broader-candidate event cache with explicit source identities, population coverage checks and verified cached parts; diagnosis reassessment accepts it. Preserves source engine and clinical cutoffs. Synthetic direct/cache cohort parity and integrity tests added. H100 cache build/performance unmeasured. Next: refreshed expanded-cohort baseline consuming cache and both diagnosis deliveries plus limited labs; old baseline readers remain version-restricted. See docs/RUN_CANDIDATE_EVENT_CACHE.md. No MICE/PSM run yet.


### 2026-09-22 — Candidate event cache completed on H100

Reviewed user-provided candidate_event_cache_v1 summary: status complete, 71,814 broader candidate keys, 17 tables from five source snapshots, 327.723 seconds. Source rows 702,126,702; retained rows 144,424,880; 79.43% fewer rows; compressed output 4,665,534,348 bytes. This is reduction in input rows, not a measured downstream runtime speedup. All dates/columns retained; downstream pre-index filters remain mandatory. Current exploratory COMET roster remains 9,735, not 71,814. Cache destination path was not included in supplied summary; do not invent it. Limited lab source contains only verified shards 1 and 2; damaged shard 3 remains excluded. No MICE or PSM result. Next: consolidated refreshed baseline using this cache and both diagnosis deliveries; do not rebuild the completed cache.


### 2026-09-22 — Expanded cohort cache-backed baseline runner prepared

Added build_comet_cached_baseline.py with strict expanded-cohort/cache/source/anchor lineage checks. One command discovers exactly one completed compatible cohort/cache (or accepts explicit paths), verifies cached parts once per run, regenerates vital candidates, and stages 32 columns using both diagnosis deliveries. Previously accepted recorded utilization zeros preserved; no cohort/index/endpoint changes. Old-version entry points remain restricted. Saves projected RESULT_DATE days1-90 lab rows from outpatient and verified hospital1/2 to smaller restricted Parquet plus component/specimen/unit catalog. Four clinical lab slots remain null/pending mapping rather than assigning unverified analytes or units. Vital unit uncertainty remains visible. Saved lab extracts support subsequent mapping without large-source rescans. No MICE or effect estimation. 213 synthetic tests passed, including end-to-end cohort/diagnosis/vital/zero-policy checks, individual date boundaries and altered-source rejection. H100 execution pending; see docs/RUN_COMET_CACHED_BASELINE.md.


### 2026-09-22 — Cached expanded baseline completed on H100

Reviewed comet_cached_baseline_v1 complete_cached_baseline_staging/counts_valid; ready_for_mice false. Runtime150.837s; unchanged9735=5867C+3868T,32features; all64arm-feature status totals reconcile. Actual cohortpath audits/comet-expanded-dx-OBLjqscQ/report and cachepath shared/comet-event-cache-k8bicpaM/cache under RAIDprojectroot now confirmed. Baseline output destination not supplied. Candidate availability: EF4624(52.5%null),BP2936(69.8%null),pulse2903(70.2%null),BMI3813(60.8%null). Sex/indexyear complete; one age_out_of_review_range, not ordinary missingage. Diagnosis technical nulls substantial: AF3466,CKD4239,diabetes3544; inspect parsing/date/missing-ICD10 and unmapped ICD9 causes before treating as imputation targets. No zero-policy change.

Lab extracts1307588rows,35593944bytes (~35.6MB) across outpatient17339/590patients,hospital1 629793/2561patients,hospital2 660456/2603patients. Patient counts overlap; union and analyte coverage not yet known. Allthreeunit_fields empty;5261catalogcombinations. Four lab target slots are pending mapping, not established100%clinical missingness. Next use only small saved extracts/catalog for component/specimen mapping and coverage, while tracing diagnosis technical-null reasons. Existing unit/availability and analysis-contract gates remain. No new source builds, MICE or PSM effects.


### 2026-09-22 — Mapping-gap audit prepared from completed cached baseline

User authorizes lab mapping review and diagnosis technical-null investigation. Added audit_comet_mapping_gaps.py: verifies completed parent artifacts and parser contract, computes unique any-lab and broad target-name patient unions from 35.6MB saved extracts, and writes a restricted narrowed component/specimen/unit/format catalog. Lexical leads explicitly include possible non-target assays; no clinical map or units inferred. Diagnosis scan reconstructs current values exactly and explains final nulls by prior365/undated, missing/unparsed ICD10 and ICD9 presence; positive evidence overrides blockers. A single bad/missing ICD10 row can block multiple otherwise-negative features under current policy. Added aggregate age sanity categories. No table mutations, imputation or source rebuild. 216 synthetic tests pass, including source tamper rejection, positive override, future-code exclusion, saved-value mismatch rejection and cross-source patient union. H100 execution pending; docs/RUN_COMET_MAPPING_GAPS.md provides one command.


### 2026-09-22 — Mapping-gap results reviewed

User report complete_mapping_gap_audit/counts_valid,70.909s; diagnosis reconstruction matches saved values; baseline unchanged and not MICE-ready. All18arm/diagnosis-feature totals reconcile. Any prior90 lab union5412/9735(55.6%):3074C/2338T; target name leads creatinine3437,potassium3434,sodium3434,hemoglobin5197. Name leads are not usable analyte counts; potential urine/ratios/HbA1c remain unreviewed. Narrowed catalog374groups not supplied yet, so no approved lab mapping/unit assumptions.

Diagnosis reasons show4,095,430undated rows vs1,075,699prior365rows;3,493,173undated rows have parseableICD10 withoutICD9 and594,672withICD9. Missing/unparsed/datelost rows overlap across patient-feature reasons; do not sum patient causes. Current policy uses undated records as technical blockers on otherwise-negative features; this is substantial constructed missingness, not proof of absent clinical information. Need date-field/encounter-date provenance and malformed-list analysis before policy change or MICE; no automatic undated positive or zero conversion.

Age review5865adult-rangeC plus2under18;3867adult-rangeT plus1over120. Cohort unchanged9735; adult requirement and anomalous-age handling must be explicit before eligibility freeze. No age values/dates/identifiers shared. Baseline report path now confirmed audits/comet-cached-baseline-PYwwyapr/report under RAIDroot. Next review restricted_target_lab_catalog locally and investigate diagnosis time/parsing with existing cache.


### 2026-09-22 — Explicit age/dated-diagnosis resolution candidate prepared

User requests resolution and mapping. Actual374-group lab catalog absent from attachments; asked for reviewed labels, user asked location, supplied RAID find/less instructions. Lab clinical mapping remains unresolved; no canonical units inferred. New resolve_comet_baseline_gaps.py writes separate resolution candidate: adult18-120, under18 excluded, invalid/null age quarantined; expected9732from reviewed counts. Dated DX_DATEprior365 recorded-evidence policy; undated diagnoses retained as separate auxiliaries rather than technical blockers. This is an explicit missingness-policy change, not proof of disease absence or full eligibility freeze. Complete-token whitespace ICD10 lists accepted; remaining dated parse failures/missingICD10 remain technical null, positive evidence wins; no future/index-day evidence, ICD9 translation or date fallback. Preserves oldtable/index/otherfeatures. Writes unapproved lab identity draft from cluster catalog; no labs inserted.220tests pass including revised undated policy, future exclusion, complete-token parsing, age quarantine and immutable parent. H100 run pending; docs/RUN_COMET_BASELINE_RESOLUTION.md. No MICE/effect run.


### 2026-09-22 — Actual lab catalog reviewed; explicit identity extraction implemented

Received374-group restricted target catalog with no unit fields. Encoded exact reviewed2025source component/name/base-name candidates: creatinine795/1526296;potassium894/1534081;sodium893/1534098;routine-namehemoglobin1256/17187/1534435/812/24868. Reject ratios,eGFR,urine,HbA1c,fractions/electrophoresis,freeHb,bloodgas/POC from primary identity map. Some routine IDs carry contradictory urine/catheter or unrelated specimen labels; primary requires exactBlood and no explicit contradictory source signal, flagsothers. Not metadata gold-standard validation.

Added comet_reviewed_lab_map.py and --map-reviewed-labs to resolve_comet_baseline_gaps.py, newoutputversioncomet_baseline_resolution_v2_mapped_labs. Uses smallsavedpreindexextracts, latestday/time, exactsignatures, rawORD_VALUE numericparser, tiesagreeorNULL,noolderfallback. ORD_NUM_VALUE discrepancies QC-only/no fallback. Populates four baseline slots as mapped_numeric_units_unverified; no canonicalunits/conversion,ready_for_micefalse. Preserves restricted lineage, previous tables, explicitadult/datedDXcandidatepolicy.224tests pass incl integrated lab insertion, timestampconflicts,specimengates,sourceboundaries,futureresultexclusion,sentinelcompanionnotused. H100pending;docs/RUN_COMET_MAPPED_LABS.md singlecombinedrun. Unit/sentinel/clinicalvalidity and finalanalysiscontract remain unresolved; no MICE/PSM.


### 2026-09-22 — Mapped resolution candidate completed on H100

Reviewed comet_baseline_resolution_v2_mapped_labs complete_resolution_candidate/counts_valid,56.15s;ready_for_micefalse. Adult-range roster9732=5865C+3867T after2under18excluded/1agequarantined. All64feature-arm totals and18diagnosis-transition totals reconcile. Lab numeric raw-scale candidates:creatinine3366(65.4%null),potassium3331(65.8%),sodium3366(65.4%),hemoglobin5069(47.9%). Mostly no mapped component in prior90 window (6298chemistry,4595hemoglobin); specimenblocks67eachchemistry/68hemoglobin, latestnonnumeric1creatinine/36potassium/1sodium. No timestamp/signature disagreement status reported. Units/clinical ranges remain unvalidated; no effect/MICE.

Diagnosis policy transitions across patient-feature cells:25912null->recorded0,7003nullremain,31394zeroand23279positiveunchanged. This is explicit dated-record policy change, not recovered disease-negative labels; no positive diagnoses added by whitespace parser (no recovery counter present). Remainingdiagnosisnull rates3.5–10.9% (AF791/8.1%,CKD829/8.5%,diabetes664/6.8%).3713datedmissing/unparsedrows persist, previously includingICD9leads. Vital missingness unchanged:BP69.8%,pulse70.2%,BMI60.8%,EF52.5%. Mapping reportactualpath audits/comet-mapping-gaps-LHK8x3Sn/report now confirmed; mappedoutputpathnotprovided. Next numeric range/sentinel/scaleQC from saved candidate/lineage data, unit/measurement contract and PSM feature/missingness decisions, in parallel outcome contract. No rebuild needed.


### 2026-09-22 — Numeric candidate QC and required balance evaluation

User requests continuing preparation and later covariate-balance evaluation. Added audit_comet_numeric_candidates.py to read only small mapped baseline/selected lab lineage with hash/roster/value/date checks. Reports raw-scale quantiles by arm and source/component, magnitude/possible-sentinel flags, joint/calendar missingness and paired-BP ordering. No automatic cleaning, unit inference, imputation or clinical-range approval;226synthetic tests pass. H100 pending;docs/RUN_COMET_NUMERIC_QC.md.

Recorded required future balance stage in docs/COMET_BALANCE_EVALUATION_PLAN.md: pre/postmatching Table1,SMDs/Loveplot,variance/distribution diagnostics,PSoverlap,retention and weightedESS whereapplicable. Proposed absSMD<0.10reviewthreshold,notcausalvalidityproof;no pvalue-only balance decision. Evaluate each imputation separately;reportmedian/worstSMDandfailurefraction,notpooledSMDoraveragealone. Prespecify denominator/coding/matching details; do not use outcomes orRCTeffectagreement for design tuning. Required userdirection;balanceimplementation/matchedresults notyetexist.


### 2026-09-22 — Numeric QC completed; missingness requires calendar-aware planning

Supplied comet_numeric_qc_v1 report: complete_numeric_candidate_qc, counts_valid
true, ready_for_mice false; 9,732 candidates (5,865 carvedilol, 3,867 metoprolol
tartrate), 0.184 seconds. Source mapped report confirmed at
/mnt/raid0/rbc58/ecg-tte/audits/comet-mapped-baseline-sK5bQzbm/report.
Two carvedilol BMI candidates occupy 0.1–<1 and 1000–<10000 magnitude bins; seven
carvedilol DBP candidates are zero. No automatic correction or removal performed.
Only 473 have all nine non-age numeric candidates (279/194); 1,378 have all nine
missing (854/524). These are numeric completeness counts, not completeness of all
32 PSM covariates. EF availability is zero in every pre-2015 arm/year stratum
(2,233 candidates combined). This demonstrates calendar-associated absence, not
its cause; do not silently extrapolate EF with routine MICE across these years.
Next: explicit candidate cleaning and measurement assumptions, separate sporadic
from calendar/source absence, then freeze primary vs sensitivity feature/imputation
contracts. Preserve cohort and raw values; no eligibility/date restriction adopted
from this QC alone. No MICE, matching, balance results or treatment effects yet.
User clarified covariate-balance improvement as a primary benchmark objective;
updated COMET_BALANCE_EVALUATION_PLAN.md with common clinical evaluation set,
retention tradeoffs and controlled comparisons, without presuming superiority.


### 2026-09-22 — Approved 2015-onward primary candidate population
User approved index >=2015-01-01; retain full-period sensitivity roster. Implemented restrict_comet_calendar.py with immutable parent verification and synchronized baseline/status/lineage filtering. Expected7499=4539C+2960T pending H100 run. No observed-EF requirement, value cleaning or other eligibility change. Three synthetic tests pass including boundary, duplicate/date failures, tamper rejection, no overwrite and artifact consistency. Run docs/RUN_COMET_CALENDAR.md; next review within-cohort missingness then measurement/MICE contract.


### 2026-09-22 — 2015-onward candidate cohort confirmed on H100
Reviewed comet_calendar_candidates_v1 complete_calendar_candidates, counts_valid
true, ready_for_mice false. 7,499 candidates: 4,539 carvedilol and 2,960 metoprolol
tartrate; excluded before2015:1,326/907. All20 numeric profile totals reconcile.
Combined missingness: EF2875(38.3%), SBP/DBP5322(71.0%), pulse5348(71.3%),
BMI4605(61.4%), creatinine4789(63.9%), potassium4819(64.3%), sodium4789(63.9%),
hemoglobin3577(47.7%); age complete. EF coverage improves from52.5% missing;
vital missingness does not improve. Three zero DBP values and two extreme-scale
BMI values remain, all in carvedilol. No cleaning performed. Proposed next step:
explicit measurement/cleaning contract, preserving people and raw measurements;
then cohort-specific imputation plan with original-missingness diagnostics and
sensitivity analyses. No additional complete-case exclusion, no PSM or effects.
Outcome-follow-up upper index date remains unfrozen; avoid labeling7499 the final
analysis denominator. New run output path not supplied; source_report identifies
the parent mapped report, not the calendar output.


### 2026-09-22 — Approved minimal cleaning before MICE pilot
Implemented prepare_comet_mice.py: verified calendar parent, preserve roster/raw data, set DBP==0 and BMI<1 or>1000 missing with private reason log, report all32-feature missingness. Expected5 changed cells,7499 retained. Two synthetic cleaning tests passed. H100 pending; docs/RUN_COMET_MICE_PREPARATION.md. Diagnostic MICE pilot proposed, not implemented/run; types/predictor design, source measurement assumptions and final follow-up eligibility remain unresolved. No final effect inference authorized by pilot status.


### 2026-09-22 — MICE preparation completed on H100
Reviewed comet_mice_preparation_v1 complete_mice_preparation/counts_valid true;
ready_for_mice false. Roster unchanged7499=4539C+2960T. Exactly2 BMI and3 DBP
cells set missing as authorized. All64 feature-arm missingness counts reconcile
across32 covariates:6 complete(age,sex,indexyear,3utilization);26 incomplete
(9continuous,9diagnosis,8medication indicators). Complete numeric coverage does
not establish recorded-sex coding or clinical utilization semantics. Missing
diagnosis indicators remain unknown recorded evidence, not confirmed absence.
Confirmed calendar path audits/comet-calendar-g6NLpUzH/report; preparation output
path not supplied. Next implement explicit cohort-specific diagnostic MICE with
PMM continuous and binary categorical models, fixed treatment predictor, no IDs or
endpoints; runtime validation must check category domains, unsupported/constant
targets, source integrity and logged predictor changes. Pilot5 datasets/20
iterations remains proposed, not implemented/run. Measurement units and final
outcome eligibility remain unresolved; no effect-ready declaration.


### 2026-09-22 — Diagnostic MICE pilot implemented
Added run_comet_mice_pilot.py and comet_mice_engine.R, explicit32-feature+fixedtreatment model, PMM continuous/logreg binary,5datasets20iterationsseed20260922. Verified preparation manifests, immutable observations/roster, no ID/endpoints as predictors, private missingness mask and row keys, actual/requested models, warnings/events, chain traces/plots, lag1 autocorrelation and arm-specific distributions/BP-order diagnostics. No automatic PSM/effect readiness; package/model changes flagged. Synthetic actual R4.4.3/mice3.19.0 run160rows completed11seconds with no warnings/events/model changes and convergence output; no H100 pilot yet. Minimal1e-14 CSV roundtrip tolerance restores exact source/donor values in final Parquet. docs/RUN_COMET_MICE_PILOT.md contains cluster commands and limitations.


### 2026-09-22 — First H100 MICE pilot failed at engine startup
User supplied failed_pilot,7499rows,0.301s,mice_engine_failed_check_restricted_log. Prepared source confirmed audits/comet-mice-prep-M9F28Lk2/report. Specific cause unknown; duration suggests early engine/runtime failure, not proof of missing package. Added read-only diagnose_comet_mice_failure.py with allowlisted fixed log categories and no raw text exposure;2synthetic tests pass. Next Ryan runs diagnostic on failed output; no cohort/imputation method changes and no successful H100 imputation claimed.


### 2026-09-22 — H100 diagnostic MICE pilot completed
Reviewed comet_mice_pilot_v1 complete_pilot_requires_review/counts_valid true at
/mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-ss4GJlP5/report.
7499patients(4539C/2960T),5imputations20iterations,214.749seconds; R4.4.3,mice3.19.0.
No warnings captured inside mice(), no logged events or method/predictor changes;
convergence output exists but has not been reviewed. External package-load warning
reports lme4 built Matrix ABI1 vs runtimeABI2. Engine warning_count0 does NOT cover
requireNamespace startup warnings, so do not describe the entire run as warning-free.
Current pilot uses pmm/logreg, not multilevel lme4 imputers; warning does not by
itself prove pilot failure, but environment compatibility needs repair/verification.
SBP<DBP counts:carvedilol imputation1=1,imputation5=2,allothers0. Three completed
patient-imputation rows, not necessarily3uniquepeople. No automatic swapping,
clipping,removal or rerun. Next review chain traces/AC and observed-vs-imputed
distributions, inspect private BP provenance, and resolve library mismatch before
final reproducible run. No PSM/effect readiness or convergence claim.


### 2026-09-22 — Saved MICE review implementation
Added review_comet_mice_pilot.py: verifies pilot output and original baseline
checksums/row order, rechecks observed preservation/PMM donor support; produces
26target lag1 autocorrelation summaries, per-arm numeric observed/imputed median
differences/tails and BP provenance with unique-person vs person-imputation counts.
Startup ABI warning checked separately from engine warning_count. No automatic
convergence/MAR approval, value changes,matching or MICE rerun. Two synthetic unit
tests and end-to-end review of actual synthetic R pilot passed. H100pending.


### 2026-09-22 — Saved MICE diagnostic review received
complete_diagnostic_review/counts_valid true for7499patients5imputations.26targets
have19finite AC iterations. Largest last5mean|AC|:DBP0.613,SBP0.530,valve0.381,
CKD0.310. These indicate persistence warranting trace review/longer pilot, not
a formal convergence failure. Numeric observed/imputed median differences modest
on reported raw scales; metoprolol EF imputed median42.05–47.40 vs observed44.05.
Marginal agreement does not validate MAR,units,joint relationships or causal use.
All3inconsistent BP rows are3unique carvedilol patients with both BP components
imputed (1inimputation1,2inimputation5); no observed pair changed. No automatic
swap/clipping/exclusion approved. Startup ABI warning remains. Next proposed:
trace review; compatible R environment; explicitly versioned BP-constrained
imputation specification and longer diagnostic pilot before final MICE/PSM.
No cohort change and no matching/effect results.


### 2026-09-22 — Ordered BP/50iteration diagnostic pilot v2 implemented
User approved next pilot and environment repair. Added --ordered-bp versioncomet_mice_pilot_v2_ordered_bp,50iterations5imputations. New custom PMM retains ordered ordinary draws; invalid draws refit on eligible observed donors for recipient current counterpart (>=5required), no clipping/swapping/observed changes. Reject invalid observed/finalpairs. ABIstartup warning nowstops engine; freshisolated Conda repair instructions include warning-as-error preflight, exactenvironment export. Review supports bothversions. Actual160row synthetic50iteration run completed; dedicatedRtests preserveobservations andstop when eligible donors unavailable. H100pending; docs/RUN_COMET_ORDERED_BP_PILOT.md. No readiness claim.


### 2026-09-22 — Ordered-BP H100 pilot v2 completed
User supplied comet_mice_pilot_v2_ordered_bp complete_pilot_requires_review,
counts_valid true,7499patients(4539C/2960T),5imputations50iterations,533.645seconds.
Run:/mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-v2-w5ZRCHzh/report.
R environment:/mnt/raid0/rbc58/ecg-tte/software/mice-r-v2-tyXlJyw1/env;
R4.4.3,mice3.19.0. Startup warnings0,imputation warnings0,logged events0,
no predictor/method changes. All10arm/imputation BP-order counts zero; ordering
is now enforced by construction, not independent evidence of imputation validity.
Convergence output exists but its traces/AC/distributions have not been reviewed.
Next run existing review_comet_mice_pilot.py against this saved output and compare
with v1 diagnostics. Both BP model and iteration count changed, so any difference
cannot be attributed solely to longer chains. No additional MICE rerun required
for this review. No PSM/effect readiness claimed.


### 2026-09-22 — Ordered-BP pilot v2 review received
Reviewed complete_diagnostic_review/counts_valid true,7499patients5imputations;
ABI warning absent,zero BPviolations,zero engine/startup warnings/modelchanges.
Last5mean|AC|SBP0.409vs0.530v1,DBP0.412vs0.613;CKD0.127vs0.310,
valve0.033vs0.381. All26targets49finiteiteration diagnostics. Numeric marginal
distributions broadly similar to previous report; metoprolol EF imputed medians
45–46 vs44.05observed. No claim of convergence/MAR validation from aggregates.
Both iterations and BP model changed, so improvement attribution is unresolved.
Review report remaining_review list is static/stale: ABI repair and constraint
implementation already completed; actual remaining step is trace drift/mixing
review before exploratory PSM design. No additional automatic imputation run
recommended solely to reduce AC. Five datasets still diagnostic, not final MI
precision selection;32covariate PSM specification/estimand/follow-up remain tofreeze.


### 2026-09-22 — Exploratory PSM and trace summaries implemented
User asked to continue. Added run_comet_exploratory_psm.py + Rengine: verified orderedBPpilot,32clinical covariate main-effects logistic PS,carvediloltreated,1:1greedy descendinglogit no replacement,0.2pooledwithin-armSDlogitcaliper. Explicit design experiment, not final estimand freeze or imputation convergence approval. Perimputation balanceclinical+originalmissingness,SMDfixedpreSD,binaryBernoulliSD,undefinedzeros,varratios,ECDF,retention,Love/overlapplots. Trace midpoint10vsfinal10 summaries; manualreviewremains. Actualsynthetic5imputation matching ran; unitcaliper/reuse andRbalanceinvariants pass. No H100matching/effects yet. docs/RUN_COMET_EXPLORATORY_PSM.md.


### 2026-09-22 — PSM caliper serialization precision fix
H100 exploratory run audits/comet-exploratory-psm-xulOVF3T/report stopped at
caliper_violation. Found reproducible code defect: jsonlite default digits4 rounds
reported caliper, while Rmatching uses full precision and Python compares saved
scores against rounded threshold. Synthetic0.23454321 becomes0.2345, falsely
rejecting0.23453. Fixed summary digits=NA and score CSV17significantdigits.
Caliper/matching/model unchanged; no increased validation tolerance. Regression
test confirms original falsefailure and continued rejection beyond truecaliper;
full synthetic5imputation matching passed. H100cause likely this defect but raw
pairs not inspected remotely; newrunmuststillvalidate. Preserve failedrun; rerun
matching only from savedv2imputations, no MICE/source rebuild.


### 2026-09-22 — First successful H100 exploratory PSM
Precision-fixed run audits/comet-exploratory-psm-BMy8F09e/report completed in3.924s,
counts_valid true,ready_for_effects false. Five imputation paircounts2382,2384,
2402,2387,2427 (4764–4854matched people per dataset; not summable acrossdatasets).
Carvedilolretention52.5–53.5%,metoprolol80.5–82.0%; roughly64–65%total.
MeanpostabsSMD0.0296–0.0345,max0.1232–0.1605;3,3,3,5,3evaluatedfeatures
>=0.1. SixundefinedSMDs eachdataset, no constantpredictors orPSwarnings. Likely
constant missingness flags given6completefeatures, but feature-levelreport needed
to confirm. Summarydoesnotcontain pre-matchSMDs or failingfeaturenames, so no
quantifiedimprovement orclinicalbalanceapproval yet. Need saved
balance_across_imputations.csv and trace_drift_summary.csv/chainplots review.
No rerun or effectestimate. Current shellvariableCOMET_PSM_RUN assignedinsubshell
willnotpersist; use explicit successfulrunpath in subsequentcommands.


### 2026-09-22 — Feature-level first PSM balance reviewed
User supplied balance_across_imputations.csv for successful exploratory run
BMy8F09e. EF medianabsSMD0.11483,worst0.13859,>=0.1in5/5;AFmedian0.08280,
worst0.10031,1/5. Other clinicalfeature/sexlevelSMDs<0.1inall5.
Missingness residuals:Hbmedian0.13320,worst0.16051,5/5;MRAmedian0.11440,
worst0.12867,4/5;ARNImedian0.09640,worst0.13609,2/5. Sixundefinedfeatures
are missingness indicators for fully observed age,sex,indexyear,3utilization
variables; expected zero variance,notfailedimputation.
Do not interpret imputed meanbalance as confirmedbalance of true unobserved values.
CurrentPSmodelexcludedmissingnessindicators. Proposedexplicit exploratoryv2:keep
samecohort/imputations/matchingcaliper;add original nonconstantmissingnessflags
andflexibleEFterm,compare fullperimputationbalance+retentionagainstpreservedv1.
Notimplemented/frozenyet;outcome-blinddesignrefinement only,norefitMICEneeded.
Trace review remainspending;noeffectreadinessclaim.


### 2026-09-23 — Clinical v2 and embedding archive discovery
User approved refinedclinical+embeddingpreparation, directed ECGarchive and
../mosaic/archive search. Readonlysearchfound ECGmetadata/signals,biometric and
ecg_sim checkpoints,legacyCOMETvectors undercardiomap; CLMBRweightslead
/mnt/raid0/eo287/clmbr and mosaicprog_clmbr caches/MEDSlead. No H100existence
orpreindexcoverageverified; archivesuntouched/unimported.
Implemented --refined explicitcomet_exploratory_psm_v2_refined: EF natural spline
knots30,50 boundaries1,100; original nonconstantmissingnessflags; QRdependent
columns explicitlyreported, all originalclinical/missingnessvariables evaluated.
Sameimputations/cohort/matchingrule asv1. ActualRsynthetic5imputationrunpassed;
common evaluationfeatures and preSMDs identical tov1. No clinicalsuperiorityclaim.
Added inspect_embedding_assets.py exactleadexistence/footerchecks, no patientrows
or directorylisting/modelunpickling; syntheticprivacytestpasses. Next Ryan runs
refinedPSM and assetscheck; schemaevidence neededfor cohort-specific temporal
coverage. docs/EMBEDDING_ARCHIVE_LEADS.md. No GPUinference or embeddings adopted.


### 2026-09-23 — Refined PSM H100 results received
Reviewed complete_exploratory_design_requires_review/counts_valid true7499inputs,
4.292s at audits/comet-refined-psm-0COf8sBN/report. Pairs2368,2375,2400,2383,2401
vs2382,2384,2402,2387,2427v1 (loss14,9,2,4,26pairs). MeanabsSMD0.0176–0.0241
vs0.0296–0.0345;max0.1110–0.1272vs0.1232–0.1605. Features>=0.1:1,1,1,2,1.
Sixconstantmissingnessflags explicitlyomittedfromfitting;noaliases or warnings.
Remainingfeaturenamesneeded; near0/1propensities warrant overlapreview, not
automaticpositivityapproval. No final model freeze or effects.
Assetreport at audits/embedding-assets-DPrRshKo/report but pastedtextstarts at
emb_553; onlytailthrough emb_767 andlegacyMEDSdirectoryexistence visible. Cannot
confirm ECGmetadata/checkpointstatus orwholeembedding dimension from truncated
paste. Next compact fullassetsummaryexcludingindividualembcolumns and refined
balancefeaturetable, without rerunning scans/models.


### 2026-09-23 — Compact embedding assets and refined balance confirmed
User supplied compact output for embedding-assets-DPrRshKo and refined PSM
comet-refined-psm-0COf8sBN. All nonconstant missingness indicators have absolute
SMD <0.1 in every imputation. Hemoglobin missingness median/worst 0.04442/0.06883,
MRA 0.01341/0.02153, ARNI 0.01608/0.02915. EF remains >=0.1 in all five:
median 0.12269, worst 0.12722 (original median 0.11483, worst 0.13859).
Thus EF median worsened slightly despite improved worst imbalance. AF exceeds
0.1 in one imputation (worst 0.10766); all other clinical features stay below
0.1 in all five. Preserve both comparators; no final balance/effect approval.

ECG metadata footer confirms 5,078,917 rows with MRN, ECGDate and BOTH FileID
and fileID; these aliases require explicit reconciliation. Signal and legacy
COMET biometric vector directories exist, but both historical ECG checkpoint
paths are missing. CLMBR checkpoint directory exists; contents not inspected.
CLMBR allcomers cache has 5,744 rows and v2_train cache 64,535 rows. Each has
768 emb_ columns and only file_id besides embeddings: no explicit patient or
history cutoff. These are vector-row counts, not COMET patient coverage.
No patient rows or vectors were read locally; archive remains unchanged.

Next: outcome-blind coverage audit across all 7,499 candidates, exact-key
file_id-to-ECG-to-patient linkage with ambiguity checks and strict pre-index
timing, then independent CLMBR history-cutoff/checkpoint provenance verification.
Do not select only the previously matched patients. Compare methods on common
available patients with the same clinical evaluation set; rerun clinical PSM
on that common population. Existing cache existence is not leakage clearance.
No new MICE or source-table rebuild is needed for this coverage step.


### 2026-09-23 — User corrects benchmark objective
User explicitly clarified: do not keep adjusting methods to make every covariate
balanced. Test whether direct ECG/CLMBR-T embedding cosine-similarity or distance
matching improves clinical balance compared with PSM. Stop further EF/AF-driven
PSM refinement; residual imbalance is an evaluation result. Preserve original and
already-refined PSM and disclose their development history. Embedding-augmented
PSM is a separate optional method, not the primary requested comparison. Freeze
comparison settings before examining embedding results; no selective reporting or
tuning to desired balance/RCT effects. Common population, fixed evaluation features
and denominators, retention and pre-index provenance remain required.


### 2026-09-23 — Embedding linkage feasibility audit implemented
Added audit_comet_embedding_coverage.py and RUN_COMET_EMBEDDING_COVERAGE.md.
Verifies cleaned roster hash and denominators; two projected ECG metadata passes
check strictly prior days 1–365 and global cross-alias patient/date collisions.
Aliases stay separate. CLMBR duplicate IDs excluded; ECG .npy presence only, no
vectors or notes read. Aggregate output, private fresh destination, no matching.
Synthetic timing/collision/duplicate/alias/privacy and date tests pass (2 tests).
H100 coverage and representation history/model provenance remain unverified.
Archive CLMBR cache builder supports configurable index-date column, so cache
file_id linkage alone cannot establish the historical run's actual cutoff.


### 2026-09-23 — H100 embedding coverage received
Run comet-embedding-coverage-l5h8nn2Y/report completed in 24.562 seconds,
counts_valid true, ready_for_matching false. Of 4,539 carvedilol and 2,960
metoprolol candidates, 3,671 and 2,601 respectively have ECG metadata strictly
1–365 days before index: 6,272/7,499 total. These are metadata coverage counts,
not verified waveform or embedding availability. No ambiguous candidate file IDs.
All 30,424 prior-window metadata rows had differing FileID/fileID values.
Only fileID matched CLMBR cache keys: allcomers 7/7 patients by arm; v2_train
190/178. Cache overlap across the two files was not measured: do not sum them.
No nonempty nonsymlink {fileID}.npy vectors matched either alias in the inspected
legacy ECG embedding directory. This does not establish absence in other paths,
formats or nested layouts. Zero same-record ECG-vector/CLMBR intersections.

Next investigate ECG directory layout/manifest and raw waveform coverage, locate
encoder provenance, and verify CLMBR model plus historical event input/cutoff.
Do not shrink the primary benchmark to the 368 cache-covered patients merely
because those vectors already exist. Cohort-specific generation may be needed
for broader coverage; not yet implemented or executed. No PSM tuning or matching.


### 2026-09-23 — Original ECG checkpoint search
Read-only searches of ecg-tte and mosaic archives found only the same biometric
checkpoint path, /mnt/raid0/rbc58/cardiomap/experiments/ecg_biometric/best.pt.
Local sibling ecgbio text search found no alternate path. Archived stage2_embed.py
explicitly warns that ecg_sim_from_biometric is an echo-sim fine-tune and directs
COMET use to the biometric checkpoint; mosaic4/M0_5_EMBEDDINGS.md agrees.
No checkpoint located or loaded, no archive changes, no cluster access. Next Ryan
runs a depth-limited checkpoint filename search in H100 project directories;
results stay in a private RAID audit folder pending review. Negative results from
a depth-limited search do not establish that weights are absent from the cluster.


### 2026-09-23 — Checkpoint search did not locate COMET encoder
User supplied ecg-checkpoint-search-7TmOCbNj output; no original biometric or
ecg_sim checkpoint was listed. Search errors were empty, but the search skipped
missing roots, did not follow symbolic links and was depth-limited. It is not
proof of deletion. Found variant biocontrastive checkpoints are a different
model family: local variant documentation describes an EfficientNet-B3 ECG-image
encoder (300x300x3, 1536 output), not the archived Net1D waveform/projector
COMET encoder. Do not substitute by similar filename. Environment .pth files
are not model checkpoints. Next inspect cardiomap/experiment root links and
archive layout before deciding original weights cannot be recovered.


### 2026-09-23 — BCL old experiments directory absent
User confirmed cardiomap exists as a real directory with cohort, dcm_cache,
embeddings, eval and trialemulation subdirectories; experiments and its
ecg_biometric child are absent, not symlinks.
The pasted GitHub checkout result was truncated and is not interpretable.
Further local searches in mosaic and cardioaging yielded no alternative Net1D
BCL checkpoint path. ecgbio references a separate TensorFlow B3 image model;
this does not identify the requested archived waveform BCL weights. Broaden
H100 search to moved experiments/checkpoints and backup locations; no model
substitution or inference authorized by missing-path evidence alone.


### 2026-09-23 — User prioritizes CLMBR on newly mapped OMOP gold
User will locate BCL weights independently. Proceed with frozen CLMBR first on
newly mapped gold, not the limited old ECG-keyed caches. Candidate gold root is
/mnt/raid0/rbc58/omop/gold; asynchronous question asks whether the new snapshot
is at this path. Existing root/model references found in local mosaic config
and archive; no current source or checkpoint contents read on H100.
Added docs/COMET_CLMBR_INPUT_PLAN.md: all 7,499 candidates, no ECG requirement;
exact person linkage; strictly pre-index EHR history; verified vocabulary/tokenizer
acceptance; cohort cache then frozen inference then direct distance comparison.
No imported archived modules, full OMOP rebuild, further PSM tuning, or new
embeddings yet. Gold mapping labels alone do not prove model vocabulary coverage.


### 2026-09-23 — MEDS bridge explicitly required
User correctly identified MEDS conversion before CLMBR. Confirmed historical
OMOP-to-flat-MEDS builder and model input examples; no archived code imported.
Potential reusable extract: mosaic/meds_extract_rbc_v2, cohort-scoped and not
verified for COMET. Plan now explicitly includes MEDS version/schema/metadata,
lineage/coverage checks, numeric handling and strict time cutoff. Imputed PSM
values must not be fabricated as observed MEDS events. No conversion/inference
run yet; next verify existing extract versus new gold before reuse or cohort build.


### 2026-09-23 — CLMBR MEDS input coverage implemented
Added audit_comet_clmbr_inputs.py and RUN_COMET_CLMBR_INPUTS.md. Uses explicit
source-report/gold/MEDS/model/output paths. Verifies roster hash/denominators,
checks global person identity collisions, projects three MEDS columns in bounded
Arrow batches and filters cohort IDs before Python conversion. Reports dated-code
coverage strictly before index midnight; undated and future rows separate. Saves
restricted linkage on cluster. Fixed model-file metadata only, no model loading.
Three synthetic tests pass: identity collisions/cutoff/privacy, no history and
symlink refusal. Numeric processing, clinical-code eligibility, model identity,
tokenizer compatibility and MEDS-to-gold lineage remain unverified; no inference.
User has approved proceeding with MEDS/CLMBR, historical paths explicit in runbook;
no proof yet that those paths contain the newly referenced mapping snapshot.


### 2026-09-23 — MEDS coverage results require cohort-specific extract
H100 comet-clmbr-inputs-AwA2BnNg/report completed in 23.421s. All 7,499
candidates link uniquely to current OMOP person: 4,539 carvedilol and 2,960
metoprolol. Existing meds_extract_rbc_v2 has 188,908,961 rows but contains
only 780 carvedilol and 606 metoprolol cohort members (1,386 total, 18.48%).
All 1,386 have dated pre-index codes; 6,113 linked candidates have no rows in
this MEDS extract. Absence from this cohort-scoped cache is not evidence of
absence of EHR history in OMOP. Pre-index rows total 1,963,206; same-day/future
rows 2,893,968 were not counted as prior history. Clinical-code sufficiency per
patient and tokenizer acceptance not yet assessed.
Model directory has config.json (2,002 bytes), dictionary.msgpack (6,839,410)
and model.safetensors (566,608,776). This is promising local model availability,
not verified model identity; missing alternate filenames do not imply a broken
model. MEDS uses timestamp[ms], large_string and double values with a saved pandas
index; explicit versioned schema conversion is required for a new MEDS contract.
Next build cohort-specific pre-index MEDS from gold, preserving all 7,499 in
coverage denominators rather than restricting to old cache membership. Need
current event table schemas and vocabulary/model configuration for the adapter.
No source rebuilt, no MICE rerun, no model inference yet.


### 2026-09-23 — Cohort MEDS builder and frozen CLMBR adapter implemented
User explicitly requested new cohort-specific MEDS and encoder pipeline. Added
build_comet_meds.py: verified roster; exact person linkage; five mandatory gold
domains; projected Arrow filtering; private SQLite staging; relevant concept
mapping; subject-disjoint sorted MEDS Parquet; exact-birth handling and numeric
values/units retained. No MICE features manufactured as events. Only pre-index
events retained, no same-day/future rows. New outputs and source inventories.
Added encode_comet_clmbr.py: verify output hashes, local checkpoint SHA256 and
strict state loading; frozen 768D model, latest4096 token positions, explicit
native vs code-only numerical policy, per-patient statuses and arm-level acceptance.
Uses pinned FEMR0.2.3/MEDS0.1.3 APIs verified by inspecting downloaded official
package wheels, not importing archive code. Flat MEDS_BIRTH maps explicitly to
pinned nested MEDS birth code SNOMED/184099003. Native mode passes numerical
values; old archived runner had omitted them. No unit-conversion claim.
Initial contract omits static sex/race tokens, observation domain and drug doses;
these are explicit in the runbook. Missing exact birth remains in denominator but
cannot be encoded. Model layout/state or unexpected inference failure stops.
Four new synthetic tests pass (complete staged build, temporal/identity/finiteness
checks, required-domain failure, cache mutation); three prior input tests also
pass. No GPU inference or real H100 MEDS build tested locally. Runbook:
docs/RUN_COMET_MEDS_AND_CLMBR.md. Ryan builds MEDS, then runs 32-subject smoke
in compatible GPU environment, then full fresh encoder output after review.
Partial outputs are not automatically resumable; completed MEDS cache is reusable.


### 2026-09-23 — Fresh COMET MEDS completed on H100
User report for shared/comet-meds-v1-3hgAkgoB/meds: complete_cohort_meds,
counts_valid true, 6,829,970 rows across 32 shards in 227.151s. Exact birth
for all 7,499 candidates; clinical MEDS coverage 4,538/4,539 carvedilol and
2,960/2,960 metoprolol (7,498 total). One birth-only carvedilol patient remains
in cohort denominator and must receive an explicit no-clinical-events status.
The old MEDS cache covered only 1,386 candidates.
Two source limitations: 3,580,966 measurement rows have numerical values but
no raw unit label, among 3,592,432 pre-index measurement candidates; unit concept
fields were not inspected by this builder, so do not infer units absent in gold.
Procedure candidates 565,410, of which 520,701 fail vocabulary resolution;
44,709 survive. Another 3,694,738 pre-index procedure rows have no standard
concept. Drug rows without standard concept:116,490. These are not tokenizer
coverage results. Counts cannot be called full clinical domain coverage.
Next:32-patient explicitly code-only runtime smoke to validate actual CUDA/FEMR
execution without assuming numerical unit compatibility. This is a technical
test, not the final benchmark representation and not a substitute for resolving
unit concept metadata/procedure vocabulary coverage. Native inference remains
pending numerical input validation. No MEDS rebuild needed for runtime smoke.


### 2026-09-23 — CLMBR smoke stopped on missing FEMR in base
User smoke comet-clmbr-smoke-QgGy4qEK/report failed after0.169s with
PackageNotFoundError/femr. No inference occurred; MEDS remains complete.
Archive run_prognostic_hfref_v2.sh and mosaic1/mosaic1.md explicitly use the
mosaic conda environment; prior handoff records FEMR0.2.3 and xformers there.
Next activate mosaic and verify exact FEMR/MEDS versions, imports and CUDA
before rerunning the same32-patient code-only smoke in a fresh output directory.
Do not install into base or rebuild MEDS based on this environment failure.
Current mosaic environment compatibility is not yet verified on H100.


### 2026-09-23 — Mosaic CLMBR runtime CXXABI failure
User environment has FEMR0.2.3, MEDS0.1.3, torch2.13.0, xformers0.0.35,
transformers5.15.0. Imports stop when scipy.optimize HiGHS resolves system
/lib/x86_64-linux-gnu/libstdc++.so.6 lacking CXXABI_1.3.15. No CLMBR run
launched. Do not downgrade/reinstall packages based on this evidence.
Read local mosaic/paper.md current runtime investigation: identical failure
resolved there by deriving libstdc++.so.6 from sys.prefix and preloading it for
a new process. CONDA_PREFIX had differed from interpreter prefix, so relying
on CONDA_PREFIX was specifically unreliable. This is related-project evidence,
not proof the current run is repaired. Next explicit mosaic interpreter plus
process-scoped LD_PRELOAD, then scipy.optimize/FEMR/CUDA preflight and fresh
32-patient code-only smoke. No model, MEDS, scientific contract or package changes.


### 2026-09-23 — CLMBR config default handling fixed
Interpreter-derived libstdc++ preload passed runtime imports and detected H100.
Smoke comet-clmbr-smoke-dS7xNUcE stopped at expected_clmbr_t_768_dimensions:
raw config report hidden_size null, n_layers12, vocab_size65536. This does not
prove wrong checkpoint width: raw lookup conflated omitted defaults with null.
Adapter now resolves through pinned FEMRModelConfig.from_pretrained, records raw
versus resolved fields and omitted/defaulted fields, and passes the same resolved
config to strict model loading. No hardcoded override of explicit wrong/null
dimensions; 768 output and strict checkpoint state checks retained.
Six focused synthetic tests passed. Independently loaded the official downloaded
FEMR0.2.3 config module locally and verified omitted hidden_size resolves to768
while explicit n_layers12 is preserved. No local weights or GPU execution.
Next pull patch, reuse exact MEDS/model, fresh32-person code-only smoke with the
same successful interpreter-derived runtime preload. Full checkpoint compatibility
and inference remain unverified; source unit/procedure limitations unchanged.


### 2026-09-23 — Strict safetensors loader replaces incompatible HF lifecycle
H100 smoke comet-clmbr-smoke-3YE3VjSg resolved768D/12layers and read65weight
tensors, then AttributeError; original report lacked stage/trace details, so
precise H100 failing line is not confirmed. Inspected official Transformers5.15
wheel and FEMR0.2.3: HF finalize loader uses all_tied_weights_keys set by post_init,
which FEMR constructor does not call. This establishes a relevant loader API
incompatibility, not complete diagnosis of all possible inference errors.
Adapter now constructs the same FEMR model from resolved config, loads local
safetensors via strict PyTorch state dict with exact key/shape/dtype validation.
No renaming, missing/random replacement, dtype casting, architecture/weight
changes, or package downgrade. Loader revision recorded. Execution stages and
allowlisted traceback module/function/line metadata added, without exception
messages, locals, source text or patient values. Nine focused tests pass,
including actual synthetic tensor/output equality and mismatch rejection.
No H100 model run verified yet. Reuse MEDS/checkpoint/runtime preload; rerun
fresh32patient smoke. Broader torch/xformers/FEMR compatibility still unverified.


### 2026-09-23 — CLMBR H100 smoke succeeded
User supplied comet-clmbr-smoke-LyvcBwss/report: complete_smoke_requires_review,
counts_valid true, ready_for_matching false, 24.483s. All32 targets encoded
(16 per arm), 768D; direct strict loader matched65 tensors. Code-only mode,
latest4096 token positions, one truncated history. Tokenizer accepts15,836/19,299
carvedilol and25,284/30,055 metoprolol measurements (41,120/49,354 total).
These are deterministic smoke-sample event acceptance counts, not full-cohort
clinical coverage or balance. No inference failures in this sample.
Model hashes: config9c8b9835ed5628a9b6d9498577a93ac4d9e6e269beecfbd69ca3b5dcab915e2a;
dictionary481ddac70a37e79bbfadde1411ad674544a161e3c1948149989cd159a34203ee;
weightsf56e2ece082b9daf87767c7de93419db1b6c0eaf21311e06c8f329b7ab4b81a2.
Next full cohort codes-only extraction (--limit0), same MEDS/model/runtime/4096
policy in fresh output. This is the first exploratory codes-only representation,
not approval of native numeric handling or final benchmark specification.
At most7,498 have mapped clinical events; tokenizer/no-history checks may further
reduce availability. Numeric unit/procedure mapping and static sex/race omissions
remain disclosed; no MICE rebuild or PSM refinement. Match only after full
coverage/truncation review and outcome-blind matching specification.


### 2026-09-23 — Full codes-only CLMBR embeddings completed
User report comet-clmbr-full-NAyb4G2x/report: complete_embeddings_requires_review,
counts_valid true, ready_for_matching false,114.545s. Targets7,499; encoded7,498
(4,538 carvedilol,2,960 metoprolol). One carvedilol patient no_clinical_events;
no other recorded exclusions/failures. Output768D; strict65tensor load; same
config/dictionary/weight hashes as successful smoke. Latest4096 tokens;102
patients truncated (1.36% of encoded cohort). Acceptance2,909,561/3,640,359
carvedilol and2,527,474/3,182,112 metoprolol, overall5,437,035/6,822,471
(79.69%). These are event-token acceptance counts, not independent patient or
clinical phenotype accuracy. Representation is codes-only, not numeric-inclusive.

No additional inference or MEDS/MICE rebuild is needed for this representation.
Next compare unchanged clinical PSM specifications and direct CLMBR cosine
matching on the same7,498 candidates. Clinical PSM needs rerunning on that
common population, using saved imputations with no refitting MICE. Preserve
full7,499 original/refined results. Freeze direct matching assignment, ratio,
replacement/support/tie rules before inspecting embedding balance; no tuning
to remove residual imbalance or reproduce RCT effects. Report retention jointly
with fixed clinical/missingness SMD and distribution metrics. Numeric unit and
procedure mapping limitations, static demographics omission remain unchanged.
Full embeddings remain restricted on H100; no matching or effect results yet.


### 2026-09-23 — Common-population CLMBR cosine comparison implemented
User authorized continuing from full 7,498 embeddings. New outcome-blind
`compare_comet_clmbr.py` preserves saved MICE and reruns unchanged original and
previously refined PSM on exactly the embedding-available cohort. Original PSM
is primary; refinement history disclosed. Cosine: L2 vectors, 1-dot, 1:1 greedy
without replacement, SHA256(comet_cosine_v1|key) treated order, lexical control
ties, no cutoff. No clinical/outcome tuning. Assignment/support rules differ
from PSM, so this is a method-bundle comparison, not isolated metric superiority.
Retentions, distance quantiles, common-denominator clinical/missingness balance,
observed-only SMD/counts, distribution metrics and comparative Love plots emitted.
Source manifests, cohort/arm/index identity and fixed checkpoint hash checked.
Local synthetic tests cover cosine direction/ties/row-order invariance, invalid
vectors, original/refined/external-pair R evaluation, observed-only denominators,
full orchestration (input MICE review mocked there), and manifest tamper rejection.
Existing PSM pair/caliper and fixed-SMD tests pass. No H100 comparison executed.
Next Ryan runs docs/RUN_COMET_COSINE_COMPARISON.md; review summary and plots.
Trace/source limitations and effect readiness unchanged. No MICE or GPU rerun.


### 2026-09-23 — Comparison missingness-mask contract repair
H100 comet-cosine-comparison-eJEnmZKn failed with AttributeError at3.231s;
no balance results valid. Inspected MICE writer: mask is an array of row objects,
whereas comparison incorrectly called mask.get/items as if column-oriented.
This reproduces an AttributeError path; original H100 report has no traceback
to independently confirm the exact line. Fixed consumer to validate boolean
row masks against original measurements and subset rows unchanged. Added safe
stage/module/function/line diagnostics (no exception text, locals or records).
Previous synthetic integration used a column-shaped mask and missed this defect;
updated to the actual producer format. Six Python tests and synthetic R
original/refined/external-pair balance integration pass. Matching contract,
cohort, checkpoint and imputations unchanged. Fresh H100 rerun pending.


### 2026-09-23 — First cosine result complete; selection flaw identified
User supplied comet-cosine-comparison-wOVBLUxm/report: complete, counts_valid
true, 13.095 seconds; common7498 (4538 carvedilol,2960 metoprolol). Original
PSM2382–2426 pairs, meanabsSMD.03055–.03476, max.12319–.16051,3–4 features
>=.1. Previously refined2368–2400 pairs, mean.01820–.02322, max.11494–.13257,
1 feature>=.1. Cosine2960 pairs, mean.10684–.11102, max.60178–.64184,25–27
features>=.1. All include original missingness and six undefined constant flags.

Code review identified structural benchmark limitation: v1 iterates majority
carvedilol in fixed hash order without caliper until all2960 controls are used.
Retained treated patients are therefore the first2960 hash-ordered keys and all
controls are retained, independently of embeddings. Cosine affects pair identity
but cannot affect marginal SMD/ECDF/variance balance. Synthetic check with ten
different embedding matrices confirmed identical retained sets. Computational
completion is valid but this is not a meaningful representation-dependent
selection comparison; do not infer CLMBR inferiority from this result. Preserve
v1 and disclose flaw. Proposed explicit v2: iterate smaller metoprolol arm in
fixed order, select nearest unused carvedilol using cosine; keep all other input
and evaluation rules. No new v2 implementation/run yet; no outcome use or tuning
of clinical variables/checkpoint. Effect readiness remains false.


### 2026-09-23 — User-approved metoprolol-anchor cosine v2 implemented
Explicit --metoprolol-anchor selects comet_cosine_comparison_v2_metoprolol_anchor.
All metoprolol patients queried in fixed hash order; closest unused carvedilol
selected with lexical exact-distance ties. Same normalization, cutoff-none,
checkpoint, common cohort, saved MICE and original/refined PSM formulas. Stop if
metoprolol exceeds carvedilol pool. Pair arm labels/SMD direction unchanged.
V1 code path and saved output preserved; historical doc now cautions against
interpreting v1 as representation-dependent marginal-balance evaluation.
New synthetic test changes vectors and verifies selected carvedilol membership
changes in v2 but not v1; verifies distance, labels, row-order invariance, ties,
no replacement and arm-size failure. Orchestration test uses unequal120/80 arms
and explicit v2 metadata. H100 execution pending; use
docs/RUN_COMET_COSINE_V2.md or scripts/run_comet_cosine_v2_h100.sh.
No result-driven changes of clinical features/checkpoint or new effects approval.


### 2026-09-23 — Corrected CLMBR cosine v2 H100 result
User supplied comet-cosine-comparison-v2-wiph2eZH/report: complete exploratory
comparison, counts_valid true,15.298s, common7498 (4538 carvedilol,2960
metoprolol); one carvedilol unavailable. Explicit metoprolol-anchor v2.
Cosine2960 pairs in all5 imputations (65.23% carvedilol,100% metoprolol),
meanabsSMD.09289–.09918, maxabsSMD.60957–.65820,19–21 evaluated features>=.1.
Original PSM2382–2426 pairs, mean.03055–.03476, max.12319–.16051,3–4>=.1;
refined2368–2400 pairs, mean.01820–.02322, max.11494–.13257,1>=.1.
PSM results unchanged from v1 common-population rerun. Metrics include clinical
features and original missingness; six constant/undefined indicators excluded
from means. Cosine median distance.22959,p95.43088,max.57923.
Interpretation: this codes-only direct-cosine/no-caliper method retains more
patients but has worse measured marginal balance than both clinical PSM methods.
Do not generalize to all CLMBR methods or causal effect accuracy: support, ordering
and retention differ; representation lacks numeric input and has source limits.
Freeze/report this result without tuning to force improvement. Next inspect
feature-level completed/observed balance and Love plots; feature responsible for
max SMD is not identifiable from this summary alone. Effects readiness remains
false; trace review pending. No new methods or changes authorized by this result.


### 2026-09-23 — Global optimal cosine v3 implemented; no cosine caliper
User authorized global minimization and asked about calipers. Explicit
--global-optimal selects v3: scipy rectangular linear_sum_assignment minimizing
total float64 L2 cosine distance, all metoprolol assigned without replacement
to selected carvedilol. No cosine cutoff; PSM still0.2 pooled within-arm SD(logit).
No validated cosine threshold chosen; adding a cutoff would require separate
explicit support/cardinality rules and rationale, not tuning this balance table.
Lexical axes, solver tie choice without perturbation, numpy/scipy versions logged.
Recompute v2 greedy reference objective and require optimal total <= greedy with
same cardinality. Original/refined PSM, MICE, checkpoint and cohort unchanged.
Tests compare with exhaustive assignments on20 synthetic rectangular examples,
confirm strict improvement examples, no reuse, arm labels and order invariance.
Full synthetic pipeline exercised v3. H100 run pending via
scripts/run_comet_cosine_v3_h100.sh; runtime preload addresses prior SciPy C++ ABI
issue. Keep v1/v2 results; lower total distance does not guarantee lower SMD or
smaller worst individual distance. No effects readiness or convergence approval.


### 2026-09-23 — Global cosine v3 H100 result completed
User report comet-cosine-comparison-v3-HKXiJR7g/report: complete, counts_valid
true,16.411s. scipy1.17.1,numpy1.26.4. Same7498 common patients,2960 pairs.
Global total cosine distance681.60320 versus greedy728.24589:6.40479% lower.
Global median distance.21237,p95.41141,max.57819. No cosine caliper.
Clinical/missingness meanabsSMD.09465–.10076 versus v2.09289–.09918; higher
in every imputation. Global maxabsSMD.61086–.65602;19–22 features>=.1.
Original PSM mean.03055–.03476,2382–2426 pairs,3–4>=.1; refined
mean.01820–.02322,2368–2400 pairs,1>=.1; PSM results unchanged.
Interpretation: optimizer improves its distance objective but not average
clinical balance in this experiment. Preserve all results; do not tune cosine
cutoff against these same balance outputs. This does not establish causal
effect superiority or general CLMBR inferiority. Next inspect saved feature-level
and observed-only balance to locate residual differences; no new inference or
imputation needed. Outcome readiness false; trace review remains pending.


### 2026-09-23 — User-approved cosine caliper grid v4
User supplied v3 feature table: medianabsSMD LVEF.62285, AF.47444, age.25747,
ARNI.24926, hemoglobin.21741, sex.18037; notable missingness imbalances include
BP/pulse/BMI/MRA. These are absolute SMDs, not directions or observed-only
values. Cursor IPC socket failure affects editor launch, not completed analysis.
User explicitly chose exploratory calipers0.20,0.30,0.40 after prior result review.
Implemented --global-optimal --cosine-caliper as distinct v4. Inclusive distance
threshold, maximum feasible cardinality first then minimum total distance.
Dummy columns with penalty2*n_metoprolol+1 exceed all possible real cosine cost
differences; forbidden edges infinite. Both groups can lose patients. Not
post-hoc pruning. Same original common cohort/SMD denominator/MICE/checkpoint/PSM.
Diagnostics include no-eligible-partner counts, edge count, unmatched counts,
matched cardinality and total distance. Fewer than2 matches stops balance with
structured diagnostics. All three cutoffs preserved/reported, not winner-selected.
Launcher creates fresh RAID grid, continues after individual failures and emits
combined summary.11 cosine tests plus2 grid tests pass, including exhaustive
partial assignment enumeration over40 matrices, threshold-boundary/rematching
example, no-feasible-edge case, invalid cutoff checks, actual synthetic partial
cohort/R balance integration and all-cutoff failure reporting. Existing R checks
pass. H100 run pending: scripts/run_comet_caliper_grid_h100.sh. No automatic
clinical, convergence or effects approval; no validated cosine cutoff claimed.


### 2026-09-23 — Cosine caliper grid H100 result complete
User supplied comet-cosine-caliper-grid-XhRUMLhu/grid_summary.json: all three
cutoffs completed, original/refined PSM unchanged, same7498 pre-match cohort.
0.20:1430 pairs,31.51% carvedilol/48.31% metoprolol retained; meanabsSMD
.07672–.08151,max.55540–.59089,16–18 features>=.1.
0.30:2352 pairs,51.83%/79.46%; mean.08656–.09256,max.57716–.61665,16–20>=.1.
0.40:2874 pairs,63.33%/97.09%; mean.09473–.10040,max.61432–.65928,20–23>=.1.
Original PSM2382–2426 pairs,mean.03055–.03476,3–4>=.1; refined2368–2400
pairs,mean.01820–.02322,1>=.1. Clinical and original missingness evaluated,
six constant/undefined flags. All three cosine calipers retain poorer measured
balance than PSM here. At0.30 retention is close to PSM, though selected people
can differ; retention count alone does not explain the gap.0.20 improves mean
balance versus no-caliper but loses1530/2960 metoprolol and3108/4538 carvedilol.
No cutoff chosen as winner; retain/report grid as exploratory sensitivity.
Do not generalize to all representations or treatment-effect validity. Next
review observed-only diagnostics and input/source limitations, preserve current
method results before any explicitly defined new representation or hybrid test.
No further threshold search or clinical/effect readiness inferred.


### 2026-09-23 — Observed-only/representation review prepared
User authorized review after caliper grid. Inspected MEDS/encoder and R balance
implementation: codes-only drops numeric values at inference, no explicit sex/race
tokens, exact birth/time retained; accepted event proportions are not diagnosis-
specific coverage. These differences plausibly limit balance but are not causal
explanations proved by current outputs. Observed-only evaluator masks imputed
values, uses available-case pre-SD; this differs from completed-data denominator.
New aggregate-only review verifies saved CSV hashes and summarizes all methods/
features across calipers, observed counts/fractions and signed SMDs, without
patient reads or rematching. Printed focus reflects already-reviewed variables;
all-feature artifact preserved. Undefined SMDs not zero. Synthetic tests cover
signed/absolute distinction, available counts and invalid count rejection. H100
review pending: scripts/run_comet_observed_review_h100.sh. No new representation,
caliper tuning, clinical unit approval or effects readiness inferred.


### 2026-09-23 — Observed review received; BCL encoder lead supplied
User supplied comet-observed-review-CLXuw3X7: original PSM observed EFabsSMD.058,
AF.086 versus cosine0.20 EF.519/AF.384;0.30 EF.555/AF.423;0.40 EF.603/AF.464.
Thus major differences persist among observed values; imputation alone does not
explain them. Observed-only denominators/available populations differ from
completed-data measures; no missingness assumption is validated.
User supplied filenames torch_env.yml and bcl_embed_torch.py with two-GPU torchrun
and placeholder cohort/output paths. Requested BCL comparison. Exact scripts
not located in local filename search. Asked for actual H100 directory/repository.
A separate local variant BCL training script is not confirmed as this encoder;
do not substitute. Added COMET_BCL_COMPARISON_PLAN.md with required source/weights/
input review and proposed pre-index ECG/common-population comparison. No training,
new environment, inference or BCL matching launched; no cluster direct access.


### 2026-09-23 — Exact BCL upstream located and inspected
User identified CarDS-Yale/ECG-signal-pipeline. Read-only local clone commit
d359c04d1f5e6c810f76751777535918870704b7 contains bcl_embed_torch.py/torch_env.yml.
Confirmed fileID-only input, backbone-before-projector output, default CNN0
lead_time_transformer12lead epoch30 checkpoint under /mnt/nfs_model_saves; not
the old archived Net1D projection. Actual checkpoint contents unavailable locally.
Preprocessing depends on formats_rerun.csv250Hz labels,10s first12canonical
channels,median baseline filter. Whole-shard rank distribution means50K default
uses only one GPU for cohort; proposed512 full-run shards. New read-only asset
checker reports fixed H100 paths/header only; no file rows/weights/waveforms or
directory listings. Synthetic header/missing-path checks passed. Docs
COMET_BCL_UPSTREAM_REVIEW.md pins review and next H100 commands. Need cluster
asset evidence before environment/input build/smoke. No training/inference run.


### 2026-09-23 — BCL asset presence confirmed; ECG input builder prepared locally
User confirmed metadata/checkpoint/formats files exist and historical waveform
root is a directory. Contents/weights/shape/lead semantics remain unverified.
Prepared prepare_comet_bcl_input.py with hash-checked existing cohort,latest prior
calendar day1–365,explicit alias resolution,global identity collision checks,
lexical same-day tie rule,no older fallback,and required unambiguous sampling
label. Output fileID-only CSV plus private selected/excluded dated linkage.
No waveform contents/model or cluster access. Synthetic tests cover temporal
cutoff,no older fallback,both-alias conflict,global identity conflict,format
conflict and unsafe paths. H100 input run pending. Earlier auto-review blocked
publishing internal-path BCL docs/code; user has not explicitly approved push
since that block. Prepared changes remain local, not claimed remotely available.


### 2026-09-23 — BCL publication explicitly authorized
User explicitly approved pushing BCL scripts/docs including internal cluster paths.
Committed d4b23d6; focused selection tests passed. H100 next step is the private
input builder in docs/RUN_COMET_BCL_INPUT.md. No patient processing or GPU run
performed locally. Existing unrelated documentation edits preserved.


### 2026-09-23 — BCL zero-selection path diagnosis
H100 comet-bcl-input-0aseLinb completed: 7,499 candidates; 6,272 with prior365
metadata (C 3,671; T 2,601), zero matching waveform selections. The remaining
1,227 had no prior365 ECG. This is an unresolved path/filename availability gate,
not evidence that all ECGs are absent. Added bounded aggregate-only diagnostic
for four known roots, both aliases, suffixes and symlinks; no waveform reads or
selection changes. Synthetic probe tests pass. Await H100 diagnostic output;
GPU inference and BCL matching remain pending. Run instructions:
docs/RUN_COMET_BCL_PATH_DIAGNOSTIC.md. Embedding-augmented PSM remains deferred.


### 2026-09-23 — Nested ECG root confirmed by user
User listing shows month and other subdirectories under the RAID waveform root.
Extended BCL path diagnostic with explicit bounded nested-root walk, exact
basename matching and duplicate/limit/error counts. No date-derived paths,
symlink traversal, waveform reads, or automatic inference approval. Five focused
synthetic tests pass. Await aggregate nested diagnostic; production input builder
and upstream encoder still require nested-path integration before inference.


### 2026-09-23 — BCL metadata IDs are relative .npy paths
H100 nested diagnostic tested zero IDs: both aliases rejected in all 156 sampled
rows. User confirms IDs contain subdirectories and .npy. Prior result did not test
waveform absence. Added explicit v2 --relative-npy selection contract preserving
subdirectories, canonicalizing suffix in aliases/catalog, rejecting traversal and
symlinks, and retaining existing timing/identity checks. Six tests pass. Await
new full selection summary. Encoder sampling catalog normalization must be checked
before GPU launch. No raw examples requested or patient data accessed locally.


### 2026-09-23 — BCL v2 selection recovered 6,103 patients
H100 comet-bcl-input-v2-C9ftzPbQ selected C3,561/T2,542; no prior365 ECG
C868/T359; sampling unresolved C110/T59. Lowercase fileID resolved all selected
records; 583 selected sampling flags indicate250Hz. Total6,103/7,499=81.4%.
Added smoke-input preparation: up to8 per arm/sampling stratum, canonical derived
sampling catalog, linkage digest and waveform size/mtime checks. No waveform
contents/checkpoint read locally; eight focused tests pass. Checkpoint/runtime
inspection and GPU smoke execution remain pending; no matching approval.


### 2026-09-23 — BCL 32-record smoke inputs completed
User report comet-bcl-smoke-prep-SWznZWZE confirms32: eight per arm/sampling
stratum. Added pinned-source isolated-RAID launcher and frozen checkpoint/GPU
runner with private logs, digest checks and finite/nonzero exact-output coverage
validation. Nine synthetic tests pass; actual checkpoint/runtime/GPU execution
remains on H100 and unverified locally. Run docs/RUN_COMET_BCL_SMOKE.md.
No full-cohort embeddings, matching or effects claimed.


### 2026-09-23 — BCL smoke succeeded; full runner prepared
User report comet-bcl-smoke-Ik5VklyT:32/32,256D,zero load/nonfinite/zero-vector
errors;16.299seconds; saved BCL12lead10s500Hz lead_time_transformer verified.
Environment bcl-smoke-runtime-zZ5FVVsd is reusable. Added explicit --full input
contract and reference-smoke-bound full inference using same checkpoint hash,
pinned source and runtime versions;512-record shards with unchanged batch8.
Ten synthetic tests pass. H100 full6,103 run remains pending; no matching yet.
Instructions docs/RUN_COMET_BCL_FULL.md. All existing outputs preserved.


### 2026-09-23 — Full BCL complete; comparison authorized
User full report comet-bcl-full-lMQtaSyg:6,103x256,zero load/nonfinite/zero-vector
errors,660.588seconds. User authorized trying comparison. Implemented private
fileID-to-baseline adapter with pre-index checks and explicit BCL input branch
in existing comparator; no CLMBR impersonation. Same-cohort original/refined PSM
versus no-caliper global optimal cosine, unchanged five saved imputations. New
RAID launcher reuses existing Python/R environments. Twelve BCL tests, eleven
cosine tests and R original/refined/external-pair observed-balance integration
passed synthetically. Actual H100 matching remains pending. Prior full vectors
lacked saved content hashes: adapter records current hashes after repeated QC,
not retrospective byte-integrity proof. See docs/RUN_COMET_BCL_COMPARISON.md.


### 2026-09-23 — BCL comparison complete; plot legend bug
H100 comet-bcl-comparison-FZIo043w confirms BCL256D on6,103 patients.
Cosine2,542pairs; originalPSM1,980–2,050; refined1,977–2,036. BCL meanabsSMD
0.1036–0.1086 vs original0.0274–0.0395 and refined0.0185–0.0239. Existing
plot legend incorrectly hard-coded CLMBR; fixed to read representation from
contract.json. Optional fresh plot destination avoids modifying manifested old
outputs. No matching/data changes. Matched cosine median3.106e-7 needs geometry
and preprocessing investigation; no collapse diagnosis from matched pairs alone.
