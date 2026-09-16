# Handoff: current OMOP mapping and ACC PSM baseline

Last updated: **2026-09-16**. Evidence: Ryan's reviewed H100 directory/schema and
run-manifest reports. No assistant cluster access or patient-row inspection.

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
- [ ] If sustained use is the target, prespecify a secondary per-protocol analysis
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
