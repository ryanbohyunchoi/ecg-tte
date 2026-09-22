# Efficiency audit: reusable multi-trial, multi-method TTE benchmark

2026-09-22. Scope: local code review, user-supplied aggregate run reports, restart
plan and RCT-DUPLICATE publication. No cluster access or performance experiment.
Recommendations below are proposed implementation priorities, not measured speedups
or frozen statistical choices. No source engine, eligibility or estimator changed.

## Finding and immediate status

The main bottleneck is repeated data extraction and fragmented decisions, not
proven MICE compute cost. The current scripts provide useful safety checks but
remain trial-specific reconnaissance rather than a reusable benchmark runner.

Latest returned report confirms limited hospital lab reuse COMPLETE:232,259,195
rows across two shards,411parts,5,658,061,845compressed output bytes. Reported
elapsed1441.904seconds is the engine verification interval, not necessarily total
wall time including initial verification/copy. Preserve this snapshot; do not
repeat the132GBraw checksum pass per analysis. Damaged shard3remains excluded.
Expanded diagnosis cohort:9,735=5,867carvedilol+3,868tartrate, still exploratory.
Existing6,530-patient baseline/vitals must not be relabelled as this new cohort.

## Prioritized findings

| Priority | Evidence | Change | Acceptance criterion |
|---|---|---|---|
| P0 |2026diagnoses matched212/9373prior inpatient keys;2025diagnoses matched9361. Original medication anchors still derive from the existing medication snapshot. | Source registry by domain/delivery, calendar range, key convention, role and approved overlap policy. Audit medication-source completeness before declaring initiators. | Missing/mismatched domains reported before cohort build; no assumption newer delivery replaces historical records. |
| P0 | `build_comet_candidates.records` scans projected columns, converts batches to Python dictionaries, emits every row; cohort/date filtering occurs downstream. | Filter patient keys and necessary date windows in Arrow batches before Python mapping; materialize reusable candidate event extracts. | Same patient/source-row identities and clinical decisions on synthetic boundaries and H100 aggregate reconciliation; record scanned/emitted rows and time. |
| P0 | Reassessment, clinical QC, vital extraction and baseline assembly rescan overlapping source tables. | One extraction per source/spec; compute component catalog, unit/numeric/date QC and availability together. | Re-running an unchanged feature specification does not rescan source tables. |
| P0 | Each script requires manual paths/environment variables; users repeatedly lost variables or supplied earlier reports. | Persistent run manifest, dependency graph, one runner/status command and compact review report. | Fresh shell can resume/check the intended run; source paths/statuses explicit; failed dependencies stop consumers. |
| P1 | Many adapters import a COMET-specific `verify` that accepts only `comet_broad_exploratory_v2`; new version intentionally rejected. | Versioned common cohort interface and explicit migration adapters. | Patient/index/source lineage preserved; old artifacts rejected unless migration is declared, not by weakening hash checks. |
| P1 | `open_table` verifies footers on each open; reuse verifies saved parts, copied parts and raw checksums; downstream defaults do NOT rehash raw files. | Cache validated manifest/schema metadata within an invocation. Keep expensive raw verification at ingestion/recovery or after an integrity concern. Add byte-progress heartbeats during hash/copy work. | Checksums/failure behavior retained; observable progress; no claim of immutability without enforcing/documenting storage policy. |
| P1 | Scanner uses `use_threads=False`; Parquet parts follow ingestion order, not a patient/date partition contract. | Benchmark bounded Arrow filtering/thread settings; consider patient-hash buckets or useful sort order only after measurement. | Wall time, CPU time, peak RSS and I/O recorded on representative sources; stop if more threads worsen shared-storage load. |
| P1 | Reassessment largely duplicates broad-cohort code; phenotype parsing and transition logic are repeated across scripts. | Shared pure phenotype/window functions plus trial configuration. | Known entry/removal/tie/future-data tests unchanged; one definition per clinical rule. |
| P1 | Source, cohort, feature, imputation, method and outcome versions are not orchestrated together. | Dependency-specific cache keys and a standard result contract. | A phenotype change invalidates dependent cohort/features but not raw snapshots; a method change reuses unchanged cohort/features/outcomes. |

## Reuse architecture, without a wholesale rewrite

Immutable raw sources -> versioned per-delivery source tables -> projected event
extracts -> trial cohort/index + baseline table and separate outcome attachment ->
imputation sets -> method variants -> locked evaluation report.

Two reuse levels are necessary:

1. Trial-independent normalized source/event layer, preserving source identity,
   raw values, event dates, availability-date status, unit and mapping versions.
   This is reusable across future HF and non-HF trials.
2. Trial-family candidate extracts. For COMET start with the original broader
   medication-candidate population, not just the currently eligible9,735. Preserve
   the pre-index history needed for any-prior exclusions; a365-day filter would
   silently change that rule. A later trial with new drugs/anchors expands or
   rebuilds its extract; the COMET subset is not a universal data source.

Keep post-index outcome data separate from baseline/representation extracts.
Labs need specimen/result times, numeric qualification and units; do not discard
unusable/unmapped records without explicit QC accounting. Duplicate deliveries
need source-aware deduplication. Boolean phenotype union is not a safe general
rule for encounter counts or lab averaging.

Cache identity should include selected source manifest hashes, patient/index hash,
field projection, date/availability windows, mapping version, extractor code and
relevant runtime/dependency versions. Representation caches also require modality,
checkpoint, input/preprocessing and cutoff. MICE caches require predictor roles,
model/seed/config and any analysis-stage outcome contract. Artifact existence or
file modification time alone is not a compatibility rule.

Arrow supports projection, filtering and threaded scanning; performance depends
on physical layout and selectivity. Patient predicates may reduce Python work
without reducing disk reads if row-group statistics cannot prune. Do not promise
a10xgain or allocate GPUs to an I/O/Python-row bottleneck without measurement.
[Arrow dataset documentation](https://arrow.apache.org/docs/python/dataset.html).

## What RCT-DUPLICATE means for this benchmark

RCT-DUPLICATE used feasibility-selected trials, prespecified protocols, new-user
PS-matched designs and predefined agreement measures. More closely emulated
trial designs showed greater agreement. These support prioritizing design/source
alignment before adding methods; they do not justify altering cohorts to recover
an RCT estimate. Its claims-based exposure/censoring approach is not automatically
supported by our prescribing data. [JAMA paper](https://jamanetwork.com/journals/jama/fullarticle/2804067).

Our proposed extension compares multiple frameworks within each trial. Separate:

- **Representation/adjustment comparison:** hold eligible cohort, index, endpoint,
  horizon and target estimand constant; vary clinical/structured/ECG/echo/note
  features or a declared adjustment method.
- **Phenotype/cohort-construction comparison:** changes entry/eligibility and thus
  may change target population. Evaluate as a distinct axis with overlaps and
  attrition, not as a clean representation improvement.

A minimal method registry starts with clinical PSM, expanded structured PSM, and
clinical PSM plus one specified representation. Weighting/doubly robust methods
are optional subsequent estimators requiring aligned estimands; do not implement
every combination before one end-to-end validated trial works. The32clinical
variables are a COMET extraction target, not the complete universal baseline for
all trials. A richer structured comparator helps distinguish modality benefit
from simply adding more information.

Compare modality methods on identical starting populations and matched target
populations where feasible; separately report full-cohort clinical results and
modality-subset results. Matching attrition across methods/imputations must be
visible, not silently ignored. Keep imputation inputs/outcomes and uncertainty
pooling consistent with the declared estimand. MICE does not repair unobserved
confounding, absent lab sources or missing death ascertainment.

Register each trial's source/eligibility/endpoint/estimand/horizon, medication
version, feasible precision and emulation tier before estimates. Adapted365-day
COMET mortality is not directly equivalent to a long-follow-up RCT effect. Match
reference horizon/scale or report the adaptation separately; do not attribute
that mismatch to method performance.

Evaluation registry: trial/protocol/source/cohort/method/imputation/outcome hashes,
arm orientation, effect scale/estimand, N/events/retention/ESS as applicable,
balance/overlap diagnostics, effect/uncertainty, runtime/resource use and failure
reason. Preserve failed runs. Published RCT references stay outside method tuning.
Use paper-defined agreement metrics plus prespecified paired continuous error
metrics, not correlation or significance agreement alone. Group related trial
families for development/held-out evaluation and account for dependencies and
multiple comparisons. A closer estimate is not proof of less causal bias; include
controls/sensitivity and simulations to assess failure modes.

## Concrete next implementation sequence

1. Register completed snapshots and the9,735reassessment; obtain exact output
   paths/hashes. No repeat source builds or completed lab recovery.
2. Implement common cohort adapter and one source-projected candidate extraction
   pass. Include consolidated diagnosis/medication coverage and lab/vital catalog,
   timing, units, numeric validity and per-arm missingness report. Retain staging
   values/technical uncertainty; clinical normalization follows explicit maps.
3. Outcomes session completes source provenance/censoring proposal in parallel;
   agree a single small set of pending clinical decisions, not one question per
   sequential scan. No automatic freeze on unanswered questions.
4. Implement/test MICE+PSM and effect-estimation interfaces on synthetic data while
   extracts run. Validate meaningful estimator behavior, not just successful code.
5. Attach the frozen cohort/baseline/outcome contracts and run one COMET analysis.
6. Add a second trial using configuration and shared adapters; only then expand
   the method matrix and expensive representation extraction.

Track1owns extraction/cohort/MICE/PSM; Track2owns outcomes. Keep separate worktrees
and output directories. Use one shared integration point for schemas/protocol
choices. Limit concurrent heavy scans until I/O measurements support more.

## Measurement plan and checks before promotion

Benchmark old versus proposed extraction on a representative source/snapshot;
report wall time, CPU, peak memory, bytes/rows scanned, rows retained, cache hits
and time spent hashing versus processing. Repeat a cached run and show no full
scan. Reconcile cohort membership, dates, positive/zero/null states, duplicate
handling and lab selection with baseline implementation; test boundary/future
rows, invalid units, stale caches, corrupted parts and failed dependencies.

No performance patch or clinical change is implemented by this audit. Preserve
current raw/shared-table contracts until a new implementation passes those checks.
