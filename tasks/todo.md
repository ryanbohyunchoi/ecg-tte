# Restart work tracker

Status as of 2026-09-16. Checked means completed with evidence, not merely planned.

## Restart delivered

- [x] Inspect legacy implementation and commit history.
- [x] Read the linked JAMA study and primary model documentation.
- [x] Preserve all 74 previously tracked files in a reference-only archive.
- [x] Verify archived file contents against pre-move SHA-256 hashes.
- [x] Write detailed research plan, source investigation, component audit, and decisions.
- [x] Replace root project guidance so future work starts from the new plan.

## First implementation milestone: raw-source evidence

- [x] Build and synthetically verify a metadata-only JDAT file inventory for Ryan to run (7 tests passed; `docs/RUN_JDAT_INVENTORY.md`).
- [ ] Ryan runs the inventory on the H100 and returns reviewed non-identifying filenames.
- [x] Record Ryan's first T2DM summary and filename excerpt; identify version/partial-file issues and category-label errors (`docs/JDAT_SOURCE_FINDINGS.md`).
- [x] Build bounded header-only inspection for 38 explicit T2DM candidates; 8 new tests pass (15 total).
- [x] Ryan runs header inspection and returns reviewed table/column names (`docs/RUN_JDAT_HEADERS.md`).
- [x] Review supplied header report: 36 candidates, two dated lab variants rejected (2026-09-16).
- [ ] Audit standard-code crosswalks and CLMBR-T tokenizer coverage; resolve lab units and event-time semantics.
- [x] Resolve execution boundary: no assistant SSH; Ryan pulls and runs code on the H100 (see `master.md`).
- [ ] Confirm raw source roots, extract versions, and output destination through user-run discovery.
- [ ] Establish what notes, ECGs, echo images/videos, and checkpoints are available.
- [ ] Inventory source files and obtain source dictionaries/extract specifications.
- [x] Implement bounded per-file mapping reconnaissance with aggregate summaries and a restricted on-cluster code catalog; nine synthetic tests pass (29 total).
- [ ] Complete dictionary/crosswalk audit and broader source profiling; current tool checks presence and raw code-cell counts only.
- [x] Receive first bounded record audit: seven 100,000-record prefixes, no reported parsing failures (2026-09-16).
- [ ] Audit candidate null markers and date/numeric validity; all fields were nonempty under the initial whitespace-only rule.
- [ ] Complete broader metadata/schema profiling and review aggregate reports.
- [ ] Resolve parse rules, linkage, duplicates, and source date semantics.
- [ ] Validate medication event classes and ascertainment windows.
- [ ] Validate encounters, mortality, labs/vitals, and modality timestamps.
- [ ] Produce a signed-off source map and initial trial-feasibility table.

## ACC baseline priority — 2026-09-16

- [x] Record conventional cohort construction as first priority; defer CIPHER-EHR.
- [x] Record proposed 2–3 refills over 180/365 days and distinguish baseline exposure from sustained-use analyses in handoff.md.
- [ ] Verify actual fills/days supply versus orders and refill authorizations in read-only medication source checks.
- [ ] Freeze feasible exposure/persistence rules for both arms and the estimand; do not condition initiation eligibility on future refill attainment.

- [x] Add Stage 0–5 pipeline checklist with 1a/1b cohort tracks and explicit matching/evaluation gates to handoff.md.
- [x] Clone/review CIPHER-EHR v2 workflow; integration and independent eligibility validation are deferred for the first baseline.

- [x] Consolidate current RBC mapping, run lineage, comparison and remaining gates in root handoff.md.

- [x] Build bounded read-only RBC output discovery from local path references; three new tests pass (36 total).
- [x] Locate RBC candidates: rbc58/omop/gold and mosaic/gold_rbc; review medication supplement schemas.
- [x] Review full rbc58/omop report: expanded tables, latest per-step counts and RxNorm coverage; prefer as candidate baseline source.
- [ ] Complete trial-specific read-only feasibility on RBC; resolve exposure/history and code/measurement validity before fitting.

- [x] Pull latest cards-misc main and trace source patterns, retained fields and feature-branch differences.
- [x] Document 24 candidate ETL inputs within the latest 64-file source audit and PSM limitations.
- [x] Build read-only existing-OMOP manifest/schema inspector; four synthetic tests pass (33 total).
- [x] Review existing-bb2238 metadata: latest recorded full run June 22, 23 staged inputs, narrow gold schema; exact producing commit remains unverified.
- [ ] Audit chosen treatment/comparator coverage, missingness, prior history and endpoints using read-only aggregates; bb2238 remains unchanged.
- [ ] Define one feasible treatment/comparator protocol and required baseline covariates.
- [ ] Validate exposure/index and observation history; add required raw fields before fitting PSM.
- [ ] Establish clinical and expanded structured PSM baselines before clustering/cosine comparisons.

## Subsequent evidence gates

- [ ] Freeze normalized event contracts and build tested raw adapters.
- [ ] Independently re-extract candidate RCT protocols and reference endpoints.
- [ ] Choose development trials and protected evaluation families.
- [ ] Freeze benchmark estimands, denominators, metrics, failure rules, and power plan.
- [ ] Implement and validate conventional PSM and complementary baselines.
- [ ] Validate encoders and build temporally correct patient-index embeddings.
- [ ] Develop representation/fusion methods using development data only.
- [ ] Freeze candidates and statistical analysis plan before held-out effects.
- [ ] Run the registered benchmark including failure and sensitivity reports.
- [ ] Generate a reproducible evidence package and manuscript tables.

Ryan supplied reviewed header candidates. Seven bounded record scans were also reviewed; broader source validation,
replacement clinical analysis, and superiority results remain pending.

- [ ] Audit medication setting × evidence type × source and trial-specific exposure counts on H100; distinguish outpatient maintenance, inpatient administration and discharge prescribing (handoff.md).

- [x] Implement bounded medication setting/status/source audit with restricted local category report; six synthetic tests pass.
- [x] Receive and review medication setting/status/class categories for 13 file prefixes; companion summary remains outstanding.
- [x] Review companion summary: 13 completed bounded audits; queried fill/supply/refill column names absent.
- [ ] Verify setting/status derivation and status timing; inspect raw JDAT headers and builder lineage for upstream dispensing/supply equivalents.
- [ ] Resolve possible home_meds_cmp/home_meds_merged overlap before any union.

- [x] Record Ryan's agreement: primary initiation-based PSM plus secondary sustained-treatment censoring/weighting analysis.
- [ ] After exposure-data validation, prespecify deviations, grace/gap/switch rules, censoring timing and endpoint handling for both arms.
- [ ] Specify and validate censoring weights, longitudinal covariate cutoffs, positivity/stability diagnostics and uncertainty for the secondary analysis.

- [x] Trace local medication/visit builders: source-derived setting, mixed date semantics, constant OMOP drug provenance, missing exact drug–visit links; document code evidence separately from unproven run lineage (`docs/MEDICATION_SETTING_TRACE.md`).
- [ ] Ryan runs targeted RBC medication/encounter header inspection from the trace document; review source dictionaries and confirm supplemental producing code/version.
- [ ] Validate encounter-linked setting and medication evidence separately; preserve unknowns and assess trial-specific candidate starts in both arms before selecting outpatient/inpatient strategies.
- [ ] Implement index-based cohort eligibility with follow-up across required care settings; test that future visits/refills and later hospitalization do not retrospectively determine primary eligibility.

- [x] Implement raw-source medication evidence counts (full-file or explicit prefix), distinct nonempty patient keys, candidate fill/supply presence and restricted class/status counts; six synthetic tests pass. Verified-fill/eligible N stays not assessable (`docs/RUN_MEDICATION_EVIDENCE_COUNTS.md`).
- [x] Receive completed raw RBC medication evidence scan: 30,929,792 records and 752,215 distinct nonempty patient keys; verified-fill and eligible N remain not assessable.
- [ ] Validate dispensing transaction semantics, dates, reversals/deduplication and patient identity before reporting verified-fill N.
- [x] Review first full-scan failure after 400,000-record progress; no valid N. Add bounded explicit CSV field limit and safe failure diagnostics; 11 synthetic tests pass.
- [x] Receive version 2 rerun and inspect safe failure reason before changing parsing assumptions.
- [x] Review version 2 failure: csv_parse_error after 413,839 processed records; no valid N. Add bounded aggregate-only format diagnostic; 17 relevant synthetic tests pass.
- [x] Receive reviewed format diagnostic; use its structural evidence for explicit provisional literal-tab reconnaissance.
- [x] Review format diagnostic: 500,000/500,000 physical lines have 42 columns; strict parser hits closing-quote conflict. Add explicit schema-pinned literal-tab reconnaissance mode; 21 relevant tests pass.
- [x] Receive successful full-file literal-tab reconnaissance; no empty/quoted patient keys, no category omissions, queried fill/supply names absent.
- [ ] Confirm extraction format and identity semantics before treating preliminary raw-key counts as a validated patient denominator.
- [x] Review all 42 raw column names and approved class/status aggregates; group record counts reconcile to 30,929,792. Normal/Sent contains 624,183 distinct keys; groups overlap.
- [x] Identify previously unaudited QUANTITY_DISPENSED/DISPENSED_UNIT and ordering-mode/source fields; correct quantity-absence interpretation in handoff/decisions.
- [ ] Audit ordering mode/source × class/status, literal null markers, date/numeric validity, quantity/unit availability and repeated order IDs together; verify JDAT aliases against source specifications before defining exposure.
- [x] Implement version 4 combined quality audit with restricted mode/source cross-counts, candidate null/date/numeric categories and order-key conflict diagnostics; 7 new quality tests and 15 count regressions pass.
- [ ] Ryan runs version 4 with --detail-audit on H100 and returns reviewed summary and approved category counts; actual classifications and deduplication decisions remain open.
- [x] Review version 4 full-file summary: 30,929,792 unique order keys; 22,392,680 positive quantity records; literal NULLs confirmed in dates/refills. All field-quality totals reconcile.
- [ ] Resolve ORDER_INST format with aggregate-only structural diagnostics: 30,001,013 non-null values unrecognized by current formats; do not replace index date silently.
- [ ] Replace eight-field category cross-tab (18.95% records omitted) with focused setting/source summaries and explicit completeness; obtain reviewed values before setting classification.
- [x] Implement date-focused format and calendar comparison audit with masked shapes, focused mode/class groups and no exported date values; six synthetic tests pass.
- [ ] Ryan runs the 500,000-record date audit and returns reviewed summary; then assess full-file format/comparison feasibility before deciding between ORDER_INST and START_DATE.
- [x] Review date prefix: all non-null timestamps parse; ORDER_INST uses minute precision. Comparable pairs 219,039, same-day 153,688. Correct the general quality parser's missing minute-precision format.
- [ ] Obtain full-file date comparison and approved mode/class groups; distinguish historical/backdated entries and scheduled starts before freezing index or fallback rules.
- [x] Review full mode/class groups: totals reconcile to 30,929,792; zero omissions; all labeled outpatient ordering mode. Normal START_DATE completeness 100%, same-day agreement 96.85% of comparable Normal pairs; historical class has much lower agreement.
- [ ] Confirm companion full-date summary/run status, then specify first trial's prescription class, index, missing-order-date, scheduled-start and history/washout rules; source labels do not establish actual fills.
- [x] Confirm full-date companion summary: complete_file, EOF, matching 30,929,792 records/schema and no shape/group omissions. Structural date parsing/comparison gate closed for this source.
- [ ] Select first treatment/comparator trial and specify prescribing evidence, index, class/history, washout, scheduled-start and missing-order-date rules; independently validate source meanings. Actual dispensing/adherence remains unverified.
- [x] Record Ryan's HF/GDMT focus: COMET and PARADIGM-HF candidate screen with primary-source anchors (`docs/HF_TRIAL_FEASIBILITY.md`).
- [ ] Screen exact drug/formulation contrasts for both candidates; separate metoprolol tartrate, succinate and unspecified, and count enalapril specifically.
- [ ] Validate pre-index HF/EF, background treatment, clinical covariates and endpoint capture; choose and freeze first trial contract based on feasibility before estimating effects.
- [x] Implement preliminary HF medication-name screen, separate formulation/ambiguity buckets, outpatient Normal/Print/date strata, exact patient overlap and limited recorded-history diagnostics; seven synthetic tests pass (2026-09-17).
- [ ] Ryan runs HF medication screen and returns reviewed summary; review restricted candidate drug-ID/name/route catalog on H100 before freezing mappings or reporting eligible HF arm N.
- [x] Update master and active run instructions to put reports/scratch databases beneath `/mnt/raid0/rbc58/ecg-tte/audits/` (2026-09-17 user direction).
- [ ] Ryan relocates completed home audit folders to the RAID audit root; skip active jobs and destination collisions. No assistant cluster access.
- [x] Replace fragile pasted relocation loop with relocate_audit_reports.py: explicit project prefixes, finished-status checks, no overwrite, symlink skips and progress; four synthetic tests pass.
- [x] Review partial HF screen tail: dated candidate keys tartrate 45,584, sacubitril/valsartan 5,909, enalapril 3,126; overlap reported, not eligible cohort N.
- [ ] Recover full HF summary from RAID: confirm status/EOF/row count and carvedilol denominator missing from pasted tail; review mappings and contemporaneous HF/EF feasibility next.
- [x] Confirm full HF screen summary (hf-medication-screen-trqwmXRj): complete_file/EOF, unchanged source, 30,929,792 rows, 910,036 lexical candidate records; all bucket/date totals reconcile. Dated carvedilol candidate keys 30,611. Clinical mapping and HF eligibility remain open.
- [x] Trace historical EF metadata to echo_accession_number.parquet and RBC hospital/outpatient encounter DX files; flag legacy MRN stripping and date guessing as unvalidated.
- [ ] Ryan returns reviewed echo footer schema and exact RBC DX headers; resolve "imio" field and event/availability dates, then implement pre-index EF/HF linkage coverage.
- [x] Review echo/DX schemas: 661,062 echo rows with MRN/EchoDate/EF; both RBC DX files have matching 17-column schemas and CURRENT_ICD10_LIST. Availability-time and identity semantics remain unverified.
- [ ] Audit echo EF validity/units/date formats and exact MRN linkage; audit DX date fields and code-list format, then quantify pre-index HF/EF coverage with explicit timing limitations.
- [x] Implement HF source QC and exploratory exact-key echo coverage audit with full medication/echo scans and bounded DX date/code-structure checks; no HF eligibility or numeric EF units presumed.
- [ ] Ryan runs RUN_HF_SOURCE_AUDIT.md; inspect pre/same/post echo availability, exact-key overlap, EF scale, accession conflicts and DX formats before defining clinical extraction rules.
- [x] Review HF source QC: full echo/medication scans, bounded DX; pre-anchor candidate EF coverage 41.1% carvedilol, 30.9% tartrate, 81.5% ARNI, 11.1% enalapril. EF/DX totals reconcile.
- [ ] Investigate common calendar coverage and enalapril baseline echo shortfall; review DX list structures and CALC_DX_DATE lineage (26.7% outpatient prefix lacks DX_DATE/DX_DTTM) before full HF phenotype/pre-index extraction.
- [x] Add version 2 first/any prescription-year counts, nearest prior EF recency and latest-echo missingness/conflicts, full DX scan and tokenization diagnostics; 16 HF tests pass.
- [ ] Ryan runs HF source audit version 2 with --dx-full-scan; obtain CALC_DX_DATE source definition and review common years/recency before choosing trial-specific windows.
- [x] Investigate reported full hospital DX width failure; add schema-pinned full structural diagnostic and safe mismatch positions (eight tests pass).
- [ ] Ryan runs RUN_HF_DX_FORMAT.md on hospital DX only; determine supported parser/source correction before rerunning HF source version 2. No clinical counts accepted from failed run.
- [x] Review full hospital DX format diagnostic: all but final physical line have 17 fields; sole last line has one field and newline. Strict CSV also fails earlier on quotes.
- [ ] Classify terminal line as empty/ASCII whitespace/nonblank using bounded tail metadata before specifying any explicit terminal-blank parser policy; no arbitrary row skipping.
- [x] Confirm hospital DX tail is exactly empty; implement opt-in hospital-only terminal empty line with separate physical/data accounting and rejection tests (18 HF tests pass).
- [ ] Ryan reruns HF source audit version 3 with --dx-full-scan --allow-hospital-terminal-empty-line in a fresh RAID directory; verify EOF and exactly one terminal empty line before interpreting results.
- [x] Review HF version 3 outpatient width failure; extend diagnostic to classify exact-empty payload and EOF position in one scan (11 tests pass).
- [ ] Ryan runs outpatient-only diagnostic in RUN_HF_DX_FORMAT.md; no full HF rerun or outpatient blank-line policy until structural evidence arrives.
- [x] Confirm outpatient DX sole mismatch is a zero-byte-payload terminal line; add independent outpatient EOF-empty-line flag (19 HF tests pass).
- [ ] Ryan reruns HF source audit version 4 with both explicit terminal-line flags; expect hospital 42,763,152 and outpatient 9,633,590 data rows, each plus one counted terminal blank.
- [x] Review complete HF version 4: full source EOF, expected terminal blanks, reconciled year/recency/DX totals; enalapril latest prior EF (1,35] only 12 under exploratory first-order anchor.
- [ ] Resolve echo/calendar coverage, DX date semantics and unresolved code cells; assess joint latest-prior-EF recency/threshold and pre-index HF before selecting trial cohort. Do not combine marginal counts as eligibility.
- [x] Implement optional joint HF-code/latest-EF feasibility cross-counts with separate diagnosis dates; document provisional code search and MICE/PMM proposal (22 HF/joint tests pass).
- [ ] Ryan runs RUN_HF_JOINT_EVIDENCE.md; review diagnosis-plus-EF, missing/stale EF and other patterns without promoting them to eligibility. Audit covariate missingness before freezing MI/PSM.
- [x] Review successful version 5 joint report: COMET prior I50 plus latest EF (1,35] within 365 days 704/235; systolic with missing recent EF 211/64 plus stale 56/26; all arm/year totals reconcile.
- [ ] Resolve trial index/prior treatment and diagnosis-source completeness (including ICD9) before freezing strict versus adapted COMET populations; then audit baseline covariates/missingness. PSM/MI not yet run.
- [x] Add elapsed/stage throughput and bounded date/code memoization without changing audit semantics; 24 HF/joint tests pass, H100 speedup unmeasured.
- [ ] Design private RAID intermediate tables with source/parser manifests and independent completed-stage validation to avoid repeated raw scans; do not reuse incompatible caches.
- [x] Build first shared source-table converter/manifest reader for all medication/DX/echo rows with typed helpers, QC, source/output hashes and per-source resume. Full active suite 121 tests passes, including 12 real-Parquet synthetic tests.
- [ ] Ryan runs RUN_SHARED_TABLES.md and returns reviewed summary; verify expected row accounting and QC before downstream use. Add verified remaining domains and explicitly adapt trial audits to the snapshot.
- [x] Review first H100 shared snapshot: complete, 83,987,596 rows / 158 parts / 4.12 GB, 18.57 minutes, reconciled terminal-blank and date QC accounting.
- [ ] Preserve exact completed snapshot path; verify demographics/labs/vitals/encounter schemas and plan extensions without rewriting the completed four source tables.
- [x] Prepare 20-file RBC PSM header preflight for demographics/labs/vitals/encounters, with compact schema groups and no shared snapshot changes; 15 header tests pass.
- [ ] Ryan returns reviewed PSM schema groups/unavailable statuses; then specify extension contracts and delivery overlap handling before converting new domains.
- [x] Review RBC PSM headers: 19 files / six schemas; 2026 Patients missing; vital UNIT available, lab units not explicit; lab schemas differ by two department columns.
- [ ] Prepare bounded extension profiling/source contracts, preserve delivery separation, resolve lab units and measured-variable catalogs before full lab conversion or PSM feature extraction.
- [x] Implement bounded 19-source PSM profiler with pinned schemas, date/numeric/unit QC and separate restricted catalogs (four synthetic tests pass).
- [ ] Ryan returns reviewed profile summary and approved measurement/unit mapping findings; define extension contracts before full conversion.

- [x] Review 19-source PSM prefix summary: 190,000 rows, all counter totals reconcile, unchanged sources, no catalog omissions; no full-file or clinical validation inferred.
- [ ] Implement separate raw-preserving PSM extensions with full-file accounting; retain both lab value fields and source/delivery provenance. Resolve units/component mapping before clinical normalization, then audit pre-index covariate coverage.

- [x] Implement 19-file raw-preserving PSM extension with explicit EOF count discovery and optional counted terminal blank, separate source/delivery provenance, compatible complete-snapshot reader; 133 active tests pass.
- [ ] Ryan runs RUN_PSM_SHARED_TABLES.md on H100 and returns reviewed summary; verify full-source accounting before component/unit mapping and baseline feature extraction.

- [x] Prepare proposed COMET cohort contract and clinical covariate dictionary with separate EF-defined/adapted populations and explicit timing/unit/observation/endpoint gates.
- [x] Implement mapped-event pre-index measurement selector with lineage and no older-value fallback; 13 synthetic tests, 146 full-suite tests pass. Running-builder hash inputs unchanged.
- [ ] Review component/unit/availability mappings and full extension completion, then implement Parquet-to-clinical adapters and declared-cohort arm/year covariate QC. No MICE/PSM before these gates.

- [x] Implement core-snapshot-only COMET candidate roster, joint arm anchors, prior family order history and HF/EF groups; six new synthetic tests, 152 full-suite tests pass.
- [ ] Ryan runs RUN_COMET_CANDIDATES.md in second tmux window while extension runs; review new joint-anchor denominators and unresolved exposure/HF evidence before freezing cohort eligibility.

- [x] Diagnose extension failure as >1 MiB physical line in 2025 hospital labs3; prepare bounded-memory byte-structure diagnostic (five synthetic tests). No builder changes.
- [ ] Ryan runs RUN_LAB_LONG_LINE_DIAGNOSTIC.md; use actual lengths/widths to define explicit parser recovery with verified reuse of six completed stages.

- [x] Review full long-line diagnostic: final 15.53 GB/NUL-bearing/five-column unterminated record invalidates lab shard 3; do not increase limit or skip tail.
- [ ] Obtain verified intact copy or corrected lab shard 3 export; preserve original and six completed stages, then define explicit integrity-checked recovery. COMET core-snapshot candidates remain runnable.

- [x] Add read-only COMET artifact verification and bounded lab-tail byte-pattern sampling; 164 tests pass.
- [ ] Ryan returns COMET status check and reviewed tail sample counts; select existing completed candidate run or diagnose unfinished job before launching another.

- [x] Review completed COMET roster: 71,814 candidate keys, all arm/date-view totals reconcile, 5.81-minute run; provisional HF plus recent EF (1,35] 596/162 under joint anchors.
- [ ] Cross-tab saved roster HF/EF evidence with prior/undated history and calendar coverage; validate exposure and baseline observation before eligible new-user counts.

- [ ] Quantify user-supported separate COMET-inspired systolic/combined-code OR latest prior EF<40 adaptation; report code-only/EF-only/both/EF>=40 discordance and EF=40 separately. Do not reuse broad I50 totals as HFrEF or silently change strict COMET.

- [x] Implement fixed-roster count comparison for code OR EF<40 and general HF with isolated/any-diastolic exclusions, both code-branch and entire-patient interpretations; six synthetic tests pass.
- [ ] Ryan runs RUN_COMET_HF_VARIANTS.md and returns reviewed scenario counts/deltas before selecting an adapted phenotype.

- [x] Review broader HF/EF sensitivity counts: baseline 3,971, literal any-diastolic entire-patient exclusion 6,530, code-branch exclusion 6,634; all totals/deltas reconcile.
- [ ] Review clinical meaning of broader general-HF variants and intersect with prior prescribing/observation before final cohort selection; do not select by N alone.

- [x] Record user selection of broadest 7,376-person exploratory population, without diastolic exclusions; implement materialization and history/calendar audit.
- [ ] Ryan runs COMET_SELECTED_EXPLORATORY_COHORT.md; verify 4,454/2,922 reproduction and review prior/undated prescribing combinations before clinical feature/PSM progression.

- [x] Correct selected population to user-confirmed HF OR EF<40 WITH entire-patient diastolic/HFpEF exclusions (6,530); v2 materializer and current decision docs replace mistaken no-exclusion selection.
- [ ] Run version2 selected-cohort audit in fresh directory; verify 4,017/2,513 and removals 437/409, then review history/calendar before matching.

- [x] Verify selected excluded cohort materialization: 6,530; all exclusions/history/evidence/calendar totals reconcile; 3,649 have neither recorded prior365 family orders nor undated family orders (not validated new users).
- [ ] Validate full beta-blocker history and baseline observation; review arm differences in code-only/EF-only evidence and calendar capture before clinical feature extraction/PSM.

- [x] Implement expanded beta-blocker lexical history and restricted ID/name/route/class catalog, preserving selected v2 roster and indices; synthetic lineage/failure/time tests pass.
- [ ] Run RUN_COMET_BETA_HISTORY.md on H100; review aggregate history counts and locally review medication mapping before freezing class washout and qualifying index/eligibility rules.

- [x] Reconcile expanded beta history: 6,530 total, 3,787 without named prior365 leads; 3,269 additionally without undated/unresolved leads (not new-user N).
- [ ] Audit eligibility criterion-level pass/fail/unknown and medication route mapping before choosing adapted restrictions; preserve current cohort pending decisions.

- [x] Record user-selected explicitly adapted COMET direction in COMET_ADAPTED_PROTOCOL.md and link older cohort drafts to it.
- [ ] Build original-to-adapted eligibility register and criterion-level feasibility audit; resolve source dependencies and missingness policies before cohort freeze/PSM.

- [x] Implement fixed-roster core eligibility feasibility screens and 32-criterion unknown-status register with synthetic pre-index and failure tests.
- [ ] Ryan runs RUN_COMET_ELIGIBILITY_FEASIBILITY.md; review numeric/lexical counts, then map drugs and restore demographic/encounter/vital availability before clinical eligibility decisions.

- [x] Reconcile complete core eligibility feasibility results (206.323s), including EF≥40 subgroup1,340 and unknown EF1,871; no eligibility exclusions applied.
- [ ] Unblock independently complete demographics/encounters/vitals sources and medication mapping; clarify measured-EF≥40 subgroup role before final adapted phenotype freeze.

- [x] Implement separate eight-source clinical snapshot build so corrupted labs no longer block demographics/encounters/vitals conversion.
- [ ] Ryan runs RUN_CLINICAL_SHARED_TABLES.md and returns completed summary; audit DOB/linkage, pre-index encounter coverage and vital units before feature extraction.

- [x] Specify33-variable primary PSM extraction target and clean baseline-table field list.
- [ ] Implement validated adapters for declared fields, audit missingness/support and resolve laboratory sources before model readiness.

- [x] Review successful eight-source clinical snapshot:17.1min; all reported line/key/date-QC counts reconcile.
- [ ] Discover exact completed clinical snapshot path and implement cohort-specific DOB/encounter/vital mapping audit before33-variable baseline extraction/MICE.

- [x] Implement cohort-specific demographic/encounter/vital mapping QC with exact completed-snapshot discovery and synthetic integration checks.
- [ ] Run RUN_COMET_CLINICAL_BASELINE_QC.md; review counts and restricted unit/component/setting maps before building33-variable baseline table.

- [x] Reconcile clinical baseline QC:6,530adult numeric/single raw sex pairs, all source coverage totals;32restricted mapping combinations.
- [ ] Review approved vital component/unit and sex/setting labels from restricted catalog before baseline feature extraction.

- [x] Review32-row clinical mapping catalog:BP5,pulse8,BMI301070; observed sex codes; overlapping ED/inpatient flags.
- [ ] Resolve component-level units/BP pair semantics and availability rule; extract latest prior values with statuses, derive365-day BMI coverage without summing overlapping bins.

- [x] Implement latest prior vital candidate staging with full cohort, raw paired BP,365-day BMI, status counts and lineage; synthetic tests pass.
- [ ] Run RUN_COMET_VITAL_CANDIDATES.md and resolve source unit/orientation/availability metadata before canonical baseline promotion and MICE.

- [x] Reconcile vital candidate extraction:1,937BP,2,060pulse,2,853BMI raw numeric candidates;1,694allthree; cohort unchanged.
- [ ] Resolve units/availability and assess exact-time repeated-reading selection versus current latest-day disagreement before canonical vital promotion.

- [x] Implement vital v2 repeat-reading policy and separate older-measurement auxiliary availability plus arm/year QC.
- [ ] Run fresh vital v2; review updated missingness and older support, resolve units, and finish baseline covariates before diagnostic MICE pilot.

- [x] Reconcile completed vital v2:all repeat-reading conflicts resolved; older BP/pulse available for1,033/1,011 with missing recent values.
- [ ] Resolve measurement contract and complete baseline covariate extraction before MICE; auxiliary availability is not validated predictive performance.

- [x] Implement unified33-column baseline staging with separate status table and synthetic integration checks.
- [ ] Run RUN_COMET_BASELINE_STAGING.md; resolve remaining mapping/coverage/unit/lab blockers before model-ready baseline and MICE diagnostic pilot.

- [x] Reconcile complete baseline staging:6,530x33,all arm-feature denominators;4labs blocked.
- [ ] Investigate sparse HF-admission linkage (16) and diagnosis-date/ICD coverage before zero-coding recorded evidence or MICE. Positive-only binary staging columns are not valid imputation inputs.


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


### 2026-09-23 — Embedding comparison next steps
- [x] Review compact asset schemas and refined clinical balance: missingness balanced; EF remains >=0.1 in all five imputations, AF in one.
- [ ] Audit embedding availability across all 7,499 candidates using exact patient/file linkage and strictly pre-index ECG dates; reconcile FileID versus fileID explicitly.
- [ ] Verify cached CLMBR history cutoff and model provenance; locate ECG encoder checkpoint/provenance. Directory existence and 768 columns do not establish readiness.
- [ ] Establish common available cohort and rerun clinical comparator before comparing clinical+ECG, clinical+CLMBR and combined representations. Preserve original/refined full-cohort PSM results.

- [x] Record corrected objective: stop balance-driven PSM refinements; retain residual imbalance as benchmark evidence.
- [ ] Specify and implement direct embedding cosine/distance matching versus the preserved clinical PSM comparators, with common-population balance and retention reporting. This supersedes treating embedding-augmented PSM as the primary next comparison.

- [x] Implement aggregate embedding linkage feasibility audit with synthetic collision/timing checks.
- [ ] Ryan runs RUN_COMET_EMBEDDING_COVERAGE.md on H100; review arm-level coverage before specifying direct embedding matching.

- [x] Review H100 embedding linkage: 6,272 pre-index ECG metadata patients; zero matching legacy ECG vector files at inspected path; CLMBR train cache 368 patients, allcomers 14 (overlap unknown).
- [ ] Resolve ECG storage/encoder provenance and verify raw waveform availability; establish cohort-specific CLMBR input/cutoff before broader generation. Preserve full candidate cohort rather than choosing cohort by existing cache availability.

- [x] Trace archived ECG checkpoint references: biometric path consistently specified; echo-sim checkpoint explicitly distinguished.
- [ ] Locate original weights on H100 using project-directory checkpoint search, then verify identity and training provenance.

- [x] Review initial checkpoint search: original COMET encoder not found; variant biocontrastive weights are a different architecture.
- [ ] Check cardiomap root/link and experiment archive layout; original search did not follow symlinks.

- [x] Confirm old cardiomap experiments directory absent, not a broken symlink.
- [ ] Expand BCL weight search beyond cardiomap to relocated experiment folders/backups.

- [x] Record CLMBR-first direction and explicit cohort/input plan; user handles BCL checkpoint search.
- [ ] Confirm new OMOP snapshot path and checkpoint/tokenizer identity; prepare exact person linkage and pre-index event adapter for all 7,499 candidates.
- [ ] Generate fresh frozen CLMBR vectors and compare direct distance matching with preserved PSM on common eligible patients.

- [ ] Verify meds_extract_rbc_v2 lineage/COMET coverage; reuse only if compatible, otherwise build versioned cohort MEDS from existing gold before CLMBR inference.

- [x] Implement/test COMET person-to-MEDS input coverage check.
- [ ] Run RUN_COMET_CLMBR_INPUTS.md on H100; assess existing MEDS coverage and lineage before generation.

- [x] Review MEDS coverage: all 7,499 link to gold person; old MEDS covers 1,386 (18.5%). Local model config/dictionary/safetensors present.
- [ ] Build fresh cohort-specific pre-index MEDS from gold; obtain current event schemas/vocabulary configuration before implementing the adapter. Do not use old cache membership as eligibility.

- [x] Implement cohort-specific gold-to-MEDS builder and frozen CLMBR runner with synthetic verification.
- [ ] Execute MEDS build on H100, review coverage/mapping; run 32-patient CUDA smoke with pinned compatible FEMR runtime before full inference.

- [x] Receive completed cohort MEDS: 7,498 with clinical events, all 7,499 exact birth, 6.83M rows, 3.8 minutes.
- [ ] Run explicitly code-only 32-patient CLMBR runtime smoke; final numeric representation remains unfrozen.
- [ ] Inspect unit_concept_id metadata and unmapped procedure concept provenance; missing raw unit label is not proof of absent unit information.

- [ ] Verify archived mosaic conda environment for FEMR0.2.3/MEDS0.1.3/CUDA; base lacks FEMR. Rerun fresh smoke only after runtime check.

- [ ] Retry CLMBR with libstdc++ derived from active interpreter sys.prefix, not CONDA_PREFIX; preflight before smoke. Current blocker is system CXXABI, not missing FEMR.

- [x] Fix raw-config false rejection by resolving FEMR defaults; test explicit non-768/null values remain unchanged.
- [ ] Rerun fresh CLMBR smoke after config fix; runtime imports/H100 now pass.

- [x] Replace HF5 loading lifecycle with exact safetensors state loading; add safe stage/stack diagnostics and nine focused tests.
- [ ] Rerun CLMBR smoke after loader revision; actual GPU forward remains unverified.

- [x] H100 CLMBR smoke passed:32/32 valid768D vectors,65strictly matched tensors,1truncated history.
- [ ] Run full codes-only CLMBR extraction with identical checkpoint/MEDS/4096-token policy, then review coverage and freeze direct matching settings.

- [x] Full CLMBR extraction completed:7,498 valid768D vectors in114.545s;102truncated;one no-clinical-history patient.
- [ ] Implement prespecified direct CLMBR cosine matching and common7,498-patient clinical PSM comparison, retaining saved imputation values and original/refined PSM versions. No further balance-driven tuning.


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


### 2026-09-23 — Consolidated handoff published
Current-state summary is at the top of handoff.md and supersedes historical
pending claims. Both full encoders and separate same-population PSM comparisons
are complete per supplied H100 reports. No effects or encoder fine-tuning.
BCL geometry/preprocessing audit is next; combined CLMBR/BCL common-population
comparison remains pending. Plot legend fix45bde0e is published; corrected H100
PDF regeneration not confirmed. Preserve all original runs and restrictions.

## 2026-09-23 — BCL audit, strategy, consolidation (HIPAA Claude Code session)

- [x] Consolidate `psm-mice-imputation` + `codex/comet-outcomes` on `consolidate-2026-09-23`.
- [x] BCL geometry/preprocessing audit: mV/µV input bug and 250 Hz stretching found (DECISIONS.md).
- [x] Re-embed COMET 6,103 ECGs with the fix (`scripts/bcl_embed_uv.py`, `audits/claude-bcl-uv-fix`).
- [x] Embedding gate + preprocessing utilities; 5 synthetic tests (`tests/test_embedding_utils.py`).
- [x] Exploratory strategy diagnostic over 5 imputations (`scripts/diag_matching_strategies.py`).
- [x] OMOP gold / notes / echo / ECG-text inventory (`docs/DATA_SOURCES.md`).
- [x] Split handoff: current brief in `handoff.md`, history in `docs/HANDOFF_HISTORY.md`.
- [ ] Ryan: review and freeze the evaluation protocol in `docs/STRATEGY.md` (method ladder, held-out set, PCA k).
- [x] Gate the fixed BCL on echo-linked LVEF: out-of-cohort heads, AUC 0.90.
- [ ] Decide: supervised ECG phenotype probabilities vs. multi-task ECG training (`docs/ECG_MODEL.md`).
- [x] Rerun CLMBR with numeric values: done, no better than code-only.
- [ ] Review `bio-embed-lvsd` for merge.
- [x] Feasibility screen and proposed ten (docs/TRIAL_FEASIBILITY_2026_09_23.md).
- [ ] Ryan: decide the ECG coverage criterion and index-day ECG handling.
- [x] Long-tail balance + low-dim vs hdPS analysis (COMET).
- [ ] Replicate long-tail analysis on PLATO, PARADIGM-HF, ARISTOTLE.
- [ ] Stronger hdPS comparator; negative-control outcomes; prognostic-score balance.

## Multi-trial long-tail replication (2026-09-23)

- [x] Generic trial pipeline: specs, cohort, core baseline + imputation, panel v2, ECG select/link, phenotype-head cohort exclusion, MEDS roster contract.
- [x] PARADIGM-HF adapted cohort, BCL, phenotype scores, CLMBR code-only, panel; long-tail v2 grid.
- [x] hdPS v2 (once/sporadic/frequent, k 100/200/500, exposure-only); exposure-defining features removed.
- [x] Prognostic-score balance (external reference, 1-y death/HF hosp) and post-matching C-statistic.
- [x] COMET rerun under v2 (v1 splits preserved).
- [x] PLATO adapted cohort and grid.
- [x] ARISTOTLE adapted cohort and grid.
- [ ] Negative-control outcomes; protocol freeze before any trial outcome.
- [x] Overnight 13-trial expansion (12 analysed; TRITON failed feasibility); report.md.
- [x] Ryan decisions; published HRs verified; protocol v1 frozen (tag protocol-v1).
- [x] Phase 2: outcome extraction code reviewed (v1.2), run once; results in report.md.
- [ ] Ryan: framing decision and follow-ups (report.md §7).
