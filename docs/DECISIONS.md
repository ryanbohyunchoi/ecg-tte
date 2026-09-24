# Decision register

Created 2026-09-09. This separates user direction from defaults proposed for review.
Open choices do not block archiving or planning; they do block dependent execution.

## Accepted user direction

| ID | Decision | Basis |
|---|---|---|
| D01 | Start a new implementation; old code is reference only. | User request, 2026-09-09. |
| D02 | Evaluate multiple representations and combinations against PSM across trials. | User request. |
| D03 | Investigate raw JDAT structured data as the preferred source. | User request. |
| D04 | Include AI-ECG, AI-EHR, AI-ECHO, and multimodal/hybrid hypotheses. | User request. |
| D05 | Structured CLMBR-T and Qwen-based note embeddings remain candidates; no EHR encoder is selected. | User explicitly undecided. |
| D06 | No assistant SSH or direct cluster access, including file listings. Ryan pulls code onto the H100 and runs it; only reviewed non-identifying inventories/aggregates return. | Explicit user correction, 2026-09-09; see `../master.md`. |

## Proposed defaults for the plan — not frozen analysis choices

| ID | Proposal | Why / when finalized |
|---|---|---|
| P01 | Select a clinically diverse benchmark by source observability and outcome-blind feasibility, not by favorable effects. | Confirm scope after user preference and source inventory. |
| P02 | Treat previously inspected legacy trial analyses as development evidence. Use separate locked evaluation families where feasible. | Avoid claiming genuine blinding for already-known results. |
| P03 | Start with an audited structured PSM baseline and one ECG add-on before expanding the method matrix. | Establish data and causal-design validity before costly embeddings. |
| P04 | Use published HR agreement as the primary metric family only for appropriately aligned time-to-event comparisons. | Handle different outcome scales separately. |
| P05 | Compare each candidate against PSM rerun on the same declared modality cohort and treated target population. | Separate modality selection from adjustment gains. |
| P06 | Explore several candidates; nominate one primary comparison before protected evaluation, or use a fixed multiplicity-controlled family. | Avoid picking the winner after viewing trial effects. |
| P07 | Keep model training/inference and raw data on the approved cluster. | Matches existing project environment; no cloud transfer is assumed. |
| P08 | Treat active-comparator substitutions and weak endpoint proxies as a separate exploratory tier. | They can change the causal question relative to the RCT. |

## Questions raised with the user

| ID | Missing information | Dependent work |
|---|---|---|
| Q01 | Execution resolved: Ryan runs code on the H100; no assistant SSH. Raw JDAT roots, extract versions, and output destination still need confirmation through user-run discovery. | All real-source probing. |
| Q02 | Diverse trials from the beginning versus cardiovascular/HF-first development. | Candidate roster and development split. |
| Q03 | Availability of raw structured sources, notes, ECGs, echo studies, and encoder checkpoints; whether AI-ECHO means imaging, reports, or both. | Modality feasibility and compute plan. |

## Decisions needed after profiling

1. Which medication evidence can define time zero: prescribing, dispensing, or
   administration? Which historical/reconciliation entries must be excluded?
2. What observation history and endpoint capture can the extracts establish?
3. Which trial contrasts and endpoint definitions are close enough for the primary
   benchmark? Who will review the clinical phenotype mappings?
4. Is echo video available, still imaging only, report text only, or a mixture?
5. Which exact pretrained checkpoints and training cohorts can be audited for overlap?
6. Which target estimand, matching design, follow-up strategy, and effect scale are
   justified for each trial? Which comparisons share a common estimand?
7. How many independent trial families and events are feasible, and what improvement
   can the benchmark detect under a prospective simulation?
8. Which primary method family, missing-data strategy, evaluation split, and
   multiplicity correction will be frozen?
9. What cluster resources, storage limits, reviewed-aggregate release rules, and
   analyst/clinical reviewer responsibilities apply?

## Decision log format

Each finalized decision records: date, responsible reviewer, evidence artifact,
alternatives considered, exact version/config hash, affected trials, and whether
new emulation effects had already been inspected. Later changes require a new
version and an explicit impact statement; do not silently revise the benchmark.

## Evidence update — metadata inventory, 2026-09-09

Implemented `scripts/inventory_jdat.py` as a standalone standard-library tool;
no archive code is imported. It inventories explicit roots without reading source
contents, retains unclassified files, records traversal errors, skips descendant
symlinks, and creates a new restricted report directory. Seven synthetic tests
passed. Ryan must execute it on the H100; all source locations remain unverified.
This completes file-inventory tooling only, not schema profiling or source validation.

## Evidence update — first H100 inventory excerpt, 2026-09-09

Ryan provided a completed T2DM-root summary (4,309 files, approximately 1.07 TB)
and selected non-identifying filenames. Raw medication, lab, vital, encounter,
patient, and history tables are candidates; clinical semantics remain unverified.
Multiple versions, nested deliveries, and `.partial` artifacts require provenance
review before ingestion. Filename category counts contain known heuristic errors.
See `JDAT_SOURCE_FINDINGS.md`; this is not completion of all-root discovery.

## Evidence update — header inspection tooling, 2026-09-09

Added `scripts/inspect_jdat_headers.py` with an explicit 38-file preset from Ryan's
excerpt. It reads only a bounded first physical line, rejects unrecognized header
candidates without echoing raw values, and records per-file progress/status.
Copy/date variants are inspected separately; no authoritative version is selected.
All 15 synthetic tests pass. Actual headers and clinical semantics remain unverified.

## Evidence update — CLMBR-T mapping readiness, 2026-09-16

Ryan supplied 36 successful header candidates and two rejected dated lab variants.
Headers establish candidate identity/time/code/value fields, not record completeness
or standard-vocabulary mappings. Prioritize a mapping-feasibility audit: local drug,
lab and flowsheet dictionaries; ICD/procedure mapping; lab units; timestamp semantics;
and exact tokenizer coverage. A full OMOP CDM build versus direct standardized-event
adapter remains an implementation choice. No encoder input or model has been validated.

## Implementation update — bounded mapping reconnaissance, 2026-09-16

Added per-file record parsing, presence counts and restricted raw code-cell catalogs.
Explicit file selection and row bounds prevent implicit delivery pooling; failures
stop a file and invalidate its catalog/counts. Nine new synthetic tests pass (29
total). No source rows accessed locally. Standard mappings, timestamp validation,
per-patient coverage and tokenizer evaluation remain pending source dictionaries
and explicit contracts. See `RUN_JDAT_MAPPING_AUDIT.md`.

## Evidence update — first bounded record audit, 2026-09-16

Ryan returned successful 100,000-record prefix scans for seven selected files.
All audited fields were nonempty under the whitespace-only definition; this is
not evidence of complete capture. Next distinguish candidate null markers and
invalid date/numeric formats before estimating usable-field coverage. Continue
source dictionary discovery; do not infer standard mappings from local code IDs.
See `JDAT_SOURCE_FINDINGS.md` for reviewed counts and limitations.

## ACC priority and existing OMOP audit — 2026-09-16

Ryan clarified the immediate ACC abstract goal: test unsupervised clustering and
cosine similarity against a robust PSM target-trial baseline. Prioritize existing
OMOP feasibility and conventional baseline design; CLMBR-T remapping is not the
immediate prerequisite. Improvement remains a hypothesis, not a tuning target.

Reviewed cards-misc main `33532e6` and feature branch `9e9fbc9`. Main is newer but
narrower; the producing version of Ryan's gold is unresolved. The latest 64-file
source inventory matches 24 main ETL input candidates, not a verified gold run.
Medication semantics, observation history and missing visits/procedures prevent
assuming readiness. See `CARDS_MISC_OMOP_PSM_AUDIT.md` for exact filenames and findings.

## Existing bb2238 data are read-only — 2026-09-16

Ryan explicitly wants inspection of the existing bb2238 OMOP output only: identify
inputs and mapping resolution, with no changes to that dataset. Do not run ETL or
remap/overwrite it. Added `audit_existing_omop.py` to read existing manifests and
parquet footer schemas on the H100, writing reports only to a fresh directory in
Ryan's home. Four synthetic tests pass (33 total). Actual report remains pending.

## Existing bb2238 evidence received — 2026-09-16

Read-only report identifies seven manifests; latest recorded full run is June 22,
029e6e60, 23 staged inputs, six steps and no recorded step errors. Current metadata
is consistent with the narrow pipeline: no visit/procedure parquet found, sampled
drugs have no standard drug_concept_id. Recorded silver-to-gold retention is 4.48%
for labs, 68.35% for medications, 26.04% for vitals; do not interpret these as patient
coverage or mapping correctness. Exact code revision/current partition lineage
remain unproven. Next evaluate trial-specific exposure/covariate/outcome feasibility
read-only; do not modify bb2238. Detailed input list and counts recorded in
CARDS_MISC_OMOP_PSM_AUDIT.md.

## RBC comparison requested — 2026-09-16

Ryan wants to locate the existing RBC remapping, possibly in mosaic or target-trial
outputs, and compare it with bb2238. Added bounded read-only directory/schema
inspection for documented candidate roots and Ryan's RAID directory. No historical
mapper is executed and no source is changed. Three new synthetic tests pass (36
total). Actual RBC location, schema and mapping coverage remain unverified until
Ryan returns the reviewed report. See RUN_RBC_OMOP_DISCOVERY.md.

## RBC outputs located — 2026-09-16

Reviewed discovery identifies a full-table directory candidate at rbc58/omop/gold
and the four discovered supplemental table directories at mosaic/gold_rbc.
Broad searches exhausted limits before their schemas; no mapping-quality verdict
yet. Separate ecg-tte/drugs and mm_vhd/drug schemas preserve additional medication
fields. Next use exact-root read-only inspections, not broader repeated searches.

## Full RBC mapping assessed — 2026-09-16

User report confirms expanded rbc58/omop gold, twelve manifests and ten populated
table directories. Latest recorded drugs retain 125.49M cleaned rows with 92.12%
RxNorm mapping, labs 321.43M, vitals 88.24M; visits/procedures/history are present.
This full rebuild differs from the standalone enrichment: upstream ATC rejects
were retained. Prefer RBC as candidate PSM foundation, pending trial-specific
exposure, history, covariate/endpoint and mapping checks. No automatic remapping
or changes to existing datasets. See detailed audit for denominators and run lineage.

## Pipeline checklist and CIPHER-EHR comparison — 2026-09-16

Added Stage 0–5 checklist to handoff.md, with conventional 1a and optional CIPHER-EHR
1b cohort-generation tracks. Target-trial design precedes cohort execution; eligibility,
treatment classification and follow-up share time zero. Future adherence is not a
baseline filter. Adjustment/representations are explicit Stage 3b; clinical cohort
accuracy is assessed separately from RCT effect recovery. CIPHER-EHR cloned/reviewed
at 7fd54c7; no app execution, integration, inference or clinical validation performed.

## Conventional cohort first; medication persistence proposal — 2026-09-16

Ryan selected non-CIPHER-EHR cohort construction for the initial PSM baseline;
CIPHER-EHR integration is deferred. Record 2–3 refills within 180 or 365 days as a
proposed sustained-use criterion, with exact count/window and data semantics still
open. Actual fills must be distinguished from refill authorizations/repeated orders.
Future refill attainment cannot be a retrospective eligibility filter at initiation.
Plan baseline exposure validation and a separately specified per-protocol or landmark
analysis if supported; neither adherence nor dispensing is yet verified in RBC data.
See handoff.md for checklist, estimand distinctions and evidence gates.

## Care-setting assessment — 2026-09-16

Propose outpatient maintenance exposure for refill assessment only when aligned
with the chosen chronic-treatment trial. Setting and medication evidence type are
separate axes; neither outpatient administration nor inpatient doses establish
pharmacy refills. No setting rule is frozen. Audit preserved setting/order/source
fields and raw encounter/action linkage before implementing a filter. Existing gold
metadata cannot resolve this; Ryan runs read-only aggregate checks on H100.

## Medication setting audit implementation — 2026-09-16

Added a read-only, allowlisted parquet-prefix audit for the source-preserving
medication directory. Reports setting/status/source categories locally and exports
only metadata/missingness in summary. Does not read patient identifiers, infer
actual fills, classify evidence semantics or compute patient-level adherence.
Six synthetic tests verify bounds, null/blank handling, raw-value separation,
source preservation, output refusal, symlink handling and failed-file status.
Cluster execution and clinical validation remain pending. See run instructions.

## Medication setting category evidence — 2026-09-16

Reviewed 13 supplied file category summaries, each with 100,000 setting records.
Home medication prefixes mix historical and prescription classes; inpatient and
outpatient-admin prefixes have null order class. Source-setting labels alone do
not validate actual fills or administration. Do not exclude all Discontinued
records or treat Sent/Dispensed status as proof of outpatient use. Status timing
must be checked. CMP/merged identical category distributions flag potential overlap,
not proven duplicates. Companion summary (fill/supply presence, coverage/failures)
is still needed. Only reviewed aggregates recorded in handoff; raw catalog excluded.

## Medication supply feasibility evidence — 2026-09-16

Companion summary confirms all 13 bounded file audits completed with no file cap,
source-change flag or category omission. All queried fill/dispensing-date, supply,
quantity and refill column names are absent in these derived schemas. Order dates
are populated in prefixes; end dates are not validated supply durations. Actual
refill/PDC assessment remains unsupported by these files. Inspect raw JDAT headers,
dictionaries and builder lineage for upstream equivalents before abandoning that
possibility. Repeated orders can support only a separately labeled prescribing
persistence proxy; post-index attainment is not baseline eligibility.

## Agreed sustained-treatment analysis direction — 2026-09-16

Ryan accepted a primary initiation-based analysis retaining later discontinuers,
plus a secondary sustained-treatment analysis that censors at a prespecified
strategy deviation, retaining follow-up and outcomes before censoring. Plan IPCW
for measured selection into continued adherence; baseline PSM is insufficient on
its own. No survivor-only retrospective exclusion. Death handling depends on the
endpoint/estimand. Data feasibility, gap/grace rules, censoring timing and weighting
specification remain open; this agreement is not implementation or validation.

## Local medication and encounter setting trace — 2026-09-16

Inspected historical medication builder as reference only, separate CardioMap
builder, and cards-misc main/feature medication and visit code. Compatible legacy
builder assigns `setting` by filename family and conflates selected administration
or order dates in `order_date`; it omits refill/supply/action/linkage fields. Reviewed
OMOP code uses constant drug provenance and does not emit medication-to-visit links.
Hospital visit mapping distinguishes three encounter classes; outpatient mapping
assigns all source records to outpatient, preserving encounter type for later review.
These are verified code behaviors, not proof of current cluster producing versions.
Propose setting/evidence fields with explicit unknowns and selection at the index
event, retaining later inpatient/outpatient follow-up without future-visit eligibility.
No trial-specific rule frozen. See MEDICATION_SETTING_TRACE.md for evidence and
targeted read-only RBC header instructions; cluster checks remain pending.

## Medication evidence denominators tooling — 2026-09-16

Ryan requested N for dispensing feasibility. Added a read-only one-file raw JDAT
audit with explicit full-scan versus prefix scope, distinct nonempty patient keys,
candidate field presence and restricted order class/status counts. Missing candidate
fields are not zero verified fills. Verified outpatient-fill N and eligible-initiator
N remain null/not assessable until source and trial contracts are validated. Raw
REFILLS and order status labels never classify actual fills. No cohort criterion
was changed. Six synthetic tests pass, covering distinct counts, absent-field versus
zero distinction, no dispensing inference, malformed-input invalidation, privacy,
output preservation, symlinks and explicit prefix/category limits. Actual source N
and clinical validation remain pending Ryan's H100 run. See RUN_MEDICATION_EVIDENCE_COUNTS.md.

## First medication N run failed; parser diagnostics strengthened — 2026-09-16

Ryan returned a full-scan attempt on the specified RBC raw Meds source. Progress
passed 400,000 records, then status was failed_counts_invalid with generic Error.
No valid patient denominator or fill count resulted. A CSV field-limit failure is
plausible but not established by that report. Version 2 replaces the inherited
128 KiB CSV field limit with an explicit bounded 1 MiB character limit, retaining
the separate 1 MiB logical-record byte limit and strict parsing. Added safe reason
codes, processing stage and diagnostic progress; no raw exceptions or patient data
are exposed. Eleven synthetic tests pass, including long fields, malformed quotes,
multiline records, bounded failure and privacy. H100 rerun and cause confirmation
remain pending; malformed records are not skipped or silently reinterpreted.

## Medication parsing failure localized — 2026-09-16

Ryan's version 2 rerun reports csv_parse_error during record_parse after 413,839
processed records. This is not a field-size diagnostic and yields no valid N.
Added a bounded structural diagnostic: strict logical-record replay and an
independent physical-line delimiter-width check with aggregate-only reports.
Literal-quote parsing is a hypothesis, not an adopted source contract. The counting
parser remains strict. Six diagnostic tests plus eleven count-audit tests pass;
the older parquet audit suite could not import locally because pyarrow is absent.
New H100 diagnostic results and extraction-format verification remain pending.

## Medication quote-format evidence and provisional counts — 2026-09-16

Ryan returned the bounded diagnostic: strict CSV stops with unexpected character
after closing quote after 413,839 records; all 500,000 physical lines have 42
tab-separated columns, with 2,337 quote-containing lines and one field-start quote.
Source unchanged. This supports a literal-quote hypothesis, not a frozen extraction
contract. Added explicit version 3 literal-tabs reconnaissance, requiring a matching
header schema hash, full width checks, bounded fields/records and no row skipping.
Strict CSV remains default. Quotes in patient keys are retained and counted for
review. Fifteen count tests and six format tests pass; full-file counts, extraction
specification and verified dispensing N remain pending. No cohort rule changed.

## Full raw medication count report received — 2026-09-16

Ryan returned version 3 complete_file/reached_eof for the 2026 RBC implementation
CarDS_2435227_Meds.txt with the reviewed schema hash
61f9556c4f054c3346d46f78e63d65a467e022f800fb0b388e5dbcf622903da8.
The explicit literal-tab scan accepted 30,929,792 records and counted 752,215
distinct trimmed nonempty PAT_MRN_ID keys, with no empty or quote-containing keys
and no omitted category records. This is the source-wide, all-drug raw-key
denominator, not verified outpatient users, eligible initiators or actual fills.
Identity/null-marker and extract-format semantics remain unvalidated.

Present audited fields: ORDER_MED_ID, ORDER_INST, START_DATE, END_DATE,
DISCONTINUE_TIME, REFILLS and REFILLS_REMAINING. Every field is nonempty on every
row except REFILLS (one empty). Whitespace-only presence cannot establish valid
dates/numbers; literal null markers may explain apparent completeness and require
explicit audit. Do not infer all records were discontinued or had refills.

Queried fill/dispensing-date, days-supply, quantity, administration-action/time and
encounter-ID names are absent. Differently named equivalents/other pharmacy sources
are not excluded. Verified-fill N and eligible-initiator N remain not assessable,
not zero. Next review approved class/status aggregates and all 42 header names,
then audit null markers/date-numeric validity and medication event identity with a
source dictionary. Confirm actual dispensing semantics before longitudinal refill
or sustained-treatment analyses; no new eligibility or adherence rule is frozen.

## Complete medication header and class/status review — 2026-09-16

Ryan supplied all 42 column names and class/status aggregate groups. Their record
counts sum to 30,929,792, matching the full-file report. Selected reviewed groups:
Normal/Sent has 16,446,649 records and 624,183 distinct patient keys; Print/Sent
has 2,709,416 records and 407,130 keys; Historical Med/NULL has 5,350,259 records
and 603,346 keys. These patient groups overlap and cannot be summed. Normal across
statuses has 18,309,003 records; Historical Med has 8,418,627; Print has 3,012,580.
Status totals include 21,049,695 Sent, 6,898,003 literal NULL and 2,981,531 Suspend.
Literal NULL is confirmed in status values, not yet in date/refill fields.

Correction/expansion of the candidate-field audit: QUANTITY_DISPENSED and
DISPENSED_UNIT exist in the header but were outside the audit's name allowlist.
Previous absence findings apply only to the queried names, not all quantity fields.
No explicit dispensing-date or days-supply column appears among the 42 names.
ORDERING_MODE/_C, ORDER_MODE, ORDER_SOURCE/_C, REORDERED_YN and MODIFIED_YN are
available leads for source classification and repeated-order interpretation.
Presence does not validate encounter setting, actual fills, or discontinuation.

Epic's public ORDER_MED specification describes prescription orders, user-entered
quantity, allowed refills, order timestamps and planned end dates. Its ORDER_MED_2
specification describes remaining authorized quantity. This supports caution about
interpreting order fields as completed fills; exact JDAT aliases and derivations
remain unverified. Sources checked 2026-09-16:
https://open.epic.com/EHITables/GetTable/ORDER_MED.htm and
https://open.epic.com/EHITables/GetTable/ORDER_MED_2.htm.

Next targeted audit should combine ordering mode/source × class/status, candidate
null-marker and date/numeric validity, quantity/unit presence, and order-ID
deduplication. Do not repeat the same full scan without adding these checks.
Normal/Sent is a candidate prescribing stratum, not a frozen eligibility rule,
verified outpatient start, or proof of dispensing. No verified-fill N is available.

## Combined medication quality audit implementation — 2026-09-16

Added opt-in version 4 detail audit for the source's actual quantity fields,
explicit candidate markers, ISO/month-first date-format hypotheses, numeric
validity and repeated/conflicting order keys. Restricted category cross-counts
include mode/source, class/status, quantity unit and reorder/modified flags.
Records remain unchanged; no event deduplication, dispensing classifier or new
cohort definition is applied. Seven new quality tests and fifteen count regressions
pass. User-run H100 results, date/source dictionary confirmation and exposure
selection remain pending. See RUN_MEDICATION_EVIDENCE_COUNTS.md for exact command,
denominators, category limits, scratch-storage requirements and interpretation.

## Version 4 full-file quality results — 2026-09-16

Ryan returned complete_file/reached_eof for the same source/schema: 30,929,792
records, 752,215 nonempty patient keys. Every field-quality category total reconciles
to the record denominator. All 30,929,792 order keys are distinct, with no repeated
keys or cross-patient key conflicts within this file. This does not rule out
clinically duplicate/reordered events under different IDs or overlap across files.

QUANTITY_DISPENSED: 22,392,680 positive numeric values (72.40%), 8,537,103 literal
NULL values and nine zeros. These are record counts, not patient counts, and do not
verify completed dispensing. REFILLS has 15,777 unrecognized numeric values, four
nonintegers and one negative, alongside zero/positive and marker categories; do not
interpret unusual values before source review. No days-supply or fill-date evidence
has been established.

ORDER_INST: 30,001,013 unrecognized-format values and 928,779 literal NULL values.
All non-null order timestamps fail the current limited format hypotheses; this
suggests a systematic format mismatch, not demonstrated invalid clinical dates.
START_DATE has 25,234,145 parseable ISO values, END_DATE 27,249,053 and
DISCONTINUE_TIME 23,226,111; remaining entries are literal NULL. Parseability is
not proof of initiation, supply duration, time of information availability or
reliable discontinuation. No silent fallback from ORDER_INST to START_DATE.

The eight-field restricted category cross-tab omitted 5,859,926 records (18.95%)
after its combination limit. Whole-file numeric/date/order-key summaries remain
usable as structural diagnostics, but retained cross-tab groups cannot establish
complete setting coverage. Replace the overly broad cross-tab with separate
mode/source marginals and focused mode × class/status counts, with explicit limits.
Next add aggregate-only timestamp-format diagnostics without exposing dates, and
obtain source semantics. Outpatient/inpatient eligibility, verified-fill N and
adherence criteria remain unresolved. Do not rerun the unchanged audit.

## Focused date comparison audit — 2026-09-16

Added aggregate-only date format diagnostics and calendar-day comparisons of
ORDER_INST and START_DATE, stratified in a restricted report by ordering mode/class.
Expanded format hypotheses cover ISO minute precision, fractional seconds and AM/PM;
ambiguous slash dates and timezone-bearing dates are excluded from comparisons.
All letters/digits are removed from reported structural format patterns; no raw
dates or exact patient intervals are exported. Six synthetic tests pass. Initial
500,000-record user-run prefix check remains pending and is not population evidence.
No index rule or source-semantic claim changed. See RUN_MEDICATION_DATE_AUDIT.md.

## Order timestamp format resolved in prefix — 2026-09-16

Ryan returned 500,000 records with no shape/group omissions: ORDER_INST 495,563
ISO minute-precision timestamps and 4,437 NULL; START_DATE 223,476 ISO dates and
276,524 NULL. All non-null values parsed. There are 219,039 comparable pairs:
153,688 same calendar day (70.16% of comparable pairs), 63,328 start before order,
2,023 start after order. 280,961 pairs are not comparable. This is a nonrandom
prefix, not the source-wide distribution. The original parser omitted minute
precision; that implementation limitation is corrected with regression assertions.
Do not call the source dates invalid or automatically switch to START_DATE.
Full-file date comparison and mode/class review remain pending, as do semantics
and new-user validation. ORDER_INST remains a candidate prescribing timestamp,
not a verified dispensing date; neither index rule nor fallback is frozen.

## Full date mode/class aggregate review — 2026-09-16

Ryan supplied the restricted mode/class aggregate report, not its companion summary.
All 14 groups are labeled ORDERING_MODE=Outpatient, with zero omitted records.
Comparison, order-format and start-format counts reconcile within each group and
sum to the previous full-file total of 30,929,792. This supports complete record
coverage in the supplied group artifact; companion run status/source-change checks
still need confirmation. The label describes ordering mode, not verified linked
encounter setting or dispensing. No inpatient-mode records occur in this source
report; this does not assess the separate hospital medication-administration source.

Across groups: ORDER_INST 30,001,013 ISO minute-precision values and 928,779 NULLs;
START_DATE 25,234,145 ISO dates and 5,695,647 NULLs. No other format categories are
reported. 24,305,379 pairs are comparable; 21,095,949 same-day. Normal has
18,309,003 records, all with parseable START_DATE, and 17,391,308 parseable order
timestamps; same-day agreement is 96.85% among comparable Normal records. Print has
3,012,580 records and 95.86% same-day agreement among its 3,005,520 comparable pairs.
Historical Med has 8,418,627 records, 5,691,895 NULL start dates, and only 11.04%
same-day agreement among 2,726,318 comparable pairs. Thus the earlier prefix's
44.70% overall START_DATE availability must not characterize the prescription class.

Interpretation: evidence supports separating historical medication documentation
from candidate prescription initiation. Preserve ORDER_INST and START_DATE as
different fields. For a prescribing-at-order-time strategy, ORDER_INST is the
candidate index; a scheduled-start strategy or handling missing order timestamps
requires a separate justified rule. Do not automatically drop all discordant dates,
infer fills, or backdate eligibility with history entries. Normal/Print are candidate
classes pending source/clinical validation, not frozen eligibility. Next confirm
companion summary and define the first treatment/comparator trial, washout/history
and index contract; additional source-wide counting alone will not establish use.

## Full date audit completion confirmed — 2026-09-16

Ryan supplied the companion summary: complete_file, reached_eof=true, 30,929,792
records, matching reviewed schema, zero shape/group omissions. ORDER_INST consists
of 30,001,013 minute-precision ISO values and 928,779 NULLs; START_DATE consists of
25,234,145 ISO dates and 5,695,647 NULLs. All non-null date values in these two fields
parsed under the documented format checks. Comparison totals match the previously
reviewed mode/class groups. The tool's completion path includes its source size/mtime
consistency check; no failure was reported. This closes this file's structural date
format/comparison audit, not source-semantic validation or cohort eligibility.
Next specify a treatment/comparator trial and its prescribing index, class/history,
washout and missing-date rules. Verified dispensing/adherence remain unsupported by
the evidence reviewed; no protocol is frozen by accepting this summary.

## Initial HF trial focus — user direction, 2026-09-16

Ryan selected heart-failure/GDMT candidates, specifically COMET and PARADIGM-HF.
Recorded a feasibility screen with primary-source anchors in HF_TRIAL_FEASIBILITY.md.
Screen both exact contrasts before selecting a first implemented protocol. COMET
as the initial engineering pilot is a proposal, conditional on formulation-specific
arm counts and HF/EF/outcome feasibility. Do not silently substitute succinate for
tartrate or pooled ACEI/ARB for enalapril. PARADIGM-HF run-in, eligibility amendments
and cardiovascular-death/HF-hospitalization ascertainment require explicit handling.
No trial-specific cohort, washout, endpoint, estimand or reference effect is frozen;
drug-specific counts and clinical validation remain pending.

## Initial HF medication screen implementation — 2026-09-17

Added schema-bound read-only lexical feasibility screen for COMET/PARADIGM-HF
candidates. It separates metoprolol salts/unspecified names, carvedilol extended
release flags, combinations, brand-only matches and cross-name conflicts. Normal/
Print outpatient labels form an exploratory stratum, not frozen eligibility. It
counts distinct nonmarker patient keys, date availability/comparison, limited
earlier recorded same-bucket medication evidence and cross-arm/same-day overlap.
Restricted name/ID/route catalogs require H100 clinician/source review. No trial
cohort, mapping, washout, route/dose/status exclusion, dispensing or effect estimate
is validated. Seven synthetic tests pass; H100 execution and exact arm Ns pending.
See RUN_HF_MEDICATION_SCREEN.md. All earlier data-preservation boundaries remain.

## Audit output root changed — user direction, 2026-09-17

Ryan requests audit outputs under RAID rather than cluttering his home directory.
Use `/mnt/raid0/rbc58/ecg-tte/audits/` with private, fresh per-run directories for
all new audit reports and their temporary databases. Updated master.md and active
run instructions. Existing home output locations were produced by our explicit
commands, not source-data discovery. Ryan may move only completed project audit
folders, skipping active jobs, symlinks and existing destinations; raw datasets and
unrelated home directories remain untouched. Actual cluster relocation is not
performed or verified by the assistant. No assistant SSH authorization is implied.

## Exact RAID project destination clarified — 2026-09-17

Ryan specifies `/mnt/raid0/rbc58/ecg-tte/` as the output project root. Use its
`audits/` subdirectory for reports and run-specific scratch storage, replacing the
assistant-proposed sibling ecg-tte-audits. Updated all active run commands and master
instructions. Narrowed discovery examples to explicit data roots so their output
does not overlap a scanned parent. Existing cluster folders have not been moved by
the assistant; Ryan runs migration after active jobs finish.
# 2026-09-17: Partial HF medication screen report received

Reviewed user-supplied report tail shows dated outpatient Normal/Print candidate
patient keys: metoprolol tartrate 45,584; succinate 68,535; sacubitril/valsartan
5,909; enalapril 3,126. COMET pair overlap is 4,381 keys (64 with any same-day
candidate orders); PARADIGM-HF overlap is 87 (zero same-day). These are lexical
prescribing candidates, not eligible HF patients, initiators, fills or adherence.
The pasted report omits run status, EOF, row count and the carvedilol candidate
denominator; full-file completion and COMET arm coverage remain unconfirmed.
Obtain the complete reviewed summary without rerunning the scan. Then review
restricted mappings on H100 and assess pre-index HF/EF and contemporaneous arm
coverage before freezing eligibility or index rules. No clinical rule changed.
# 2026-09-17: Complete HF medication screen confirmed

The companion summary for hf-medication-screen-trqwmXRj confirms complete_file,
EOF, unchanged source, matching schema and 30,929,792 rows. Lexical candidate
records total 910,036; bucket totals, date comparison and format totals reconcile.
Catalog omissions are empty. Dated outpatient Normal/Print candidate patient keys:
carvedilol not marked extended 30,611; metoprolol tartrate 45,584;
sacubitril/valsartan 5,909; enalapril 3,126. Earlier recorded same-bucket orders
occur for 9,809, 15,877, 738 and 2,036 of those respective candidate groups.
This closes the missing-report/completion check above, not clinical validation.
No route or HF filter, validated drug mapping, baseline observability or new-use
definition has been applied. No index rule is frozen. Next review the restricted
mapping catalog on H100 and measure contemporaneous arm coverage and linked
pre-index HF/EF, history and required covariates. Do not subtract the history
counts to claim new users or exclude all eventual cross-arm patients.
# 2026-09-17: Echo and diagnosis source trace

Ryan requested pre-index EF and diagnosis evidence, mentioning "imio" fields.
Historical handoff/CLAUDE notes identify the EF candidate as
`/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet`, explicitly
distinguishing it from echo.parquet. This is a legacy lead, not a verified current
schema. The archived loader expected MRN/EF, guessed a date column and stripped
alphabetic MRN prefixes; do not inherit those transformations without identity
collision and timestamp-semantic validation. Existing reviewed RBC lineage lists
CarDS_2435227_Hosp_Enc_DX.txt and CarDS_2435227_Outpatient_Enc_DX.txt in the 2026
delivery. Prior T2DM headers establish CURRENT_ICD10_LIST as a candidate elsewhere,
not proof of its presence or meaning in the RBC files. No literal imio field has
been located in active local documentation. Next inspect the exact echo footer
schema and RBC diagnosis headers on H100, then implement source-bound pre-index
coverage checks. No EF threshold, HF code set or clinical eligibility rule frozen.
# 2026-09-17: Echo and RBC diagnosis schemas confirmed by Ryan

Reviewed footer report confirms echo_accession_number.parquet has 661,062 rows,
MRN/string, EchoDate/string, AccessionNumber/string, EF/double, ProcedureType/string
and valve/demographic fields. Rows are not unique patients or necessarily unique
studies. No report-finalization/availability timestamp is present in this schema;
EchoDate semantics, EF units/provenance/validity and key linkage remain unverified.
Both 2026 RBC hospital/outpatient encounter diagnosis files have the same reviewed
17-column tab header and schema hash
eee6c9922b68b8f5c95022eff2a9c7b827478195d07167c62343060cb7e75cb4.
Fields include PAT_MRN_ID, PAT_ENC_CSN_ID, CALC_DX_DATE, DX_DTTM, DX_DATE,
CURRENT_ICD9_LIST, CURRENT_ICD10_LIST, DX_SOURCE, PRIMARY_YN and POA_YN.
Header evidence does not verify row parsing, code-list structure or diagnosis
availability time. No field literally named imio appears in these schemas.
Next audit exact-string MRN linkage, missingness, EF units/distribution and
date-format agreement before a source-bound pre-index coverage audit. Do not
strip MRN prefixes, select a diagnosis timestamp by name alone, treat current
ICD mappings as historically available, or substitute diagnosis for numeric EF.
# 2026-09-17: HF source audit implementation

`audit_hf_sources.py` recreates four lexical arm anchors from full medication
orders and audits full echo metadata for quality/exact MRN coverage. Echo timing
uses calendar days before/same/after earliest candidate order, without baseline
eligibility claims, unit conversion or nearest-study selection. DX is initially
bounded to 500,000 rows per file, with code-structure checks and all three date
fields compared independently. DX overlaps are any-diagnosis/any-time in prefix,
not HF coverage. Temporary patient/date storage stays in the RAID run directory.
Source changes and schema/width failures invalidate results. Local tests are
synthetic; PyArrow is unavailable locally, so real Parquet I/O awaits H100.
# 2026-09-17: HF source QC returned; baseline echo asymmetry

Ryan's report confirms complete_requested_scope/counts_valid, full medication
30,929,792-row and echo 661,062-row scans; each DX source is a 500,000-row prefix.
All EF categories and DX format/structure totals reconcile. Echo has 314,428 exact
nonmarker MRN keys and 661,062 distinct accessions; no missing key/accession or
repeated accession rows reported. All EchoDate values parse as ISO calendar dates.
EF: 16,087 null; 14 outside 0–100; 54 zero; 2 positive <=1; remaining 644,905 in
>1–100. Units, report availability and identity semantics remain unvalidated.
Pre-anchor >1–100 EF patient keys: carvedilol 12,574/30,611 (41.1%); tartrate
14,078/45,584 (30.9%); sacubitril/valsartan 4,813/5,909 (81.5%); enalapril
347/3,126 (11.1%). These use any earlier echo, not a baseline window, nearest
measurement, trial EF threshold, HF phenotype or new-use definition. Flags overlap.
Enalapril/ARNI baseline echo asymmetry warrants calendar coverage and observation
history checks; it does not justify moving index or accepting post-index EF.
DX prefix CALC_DX_DATE complete; DX_DATE/DX_DTTM missing in 13 hospital rows and
133,279 outpatient rows (26.7%). Where comparable, dates agree on calendar day.
Do not adopt CALC_DX_DATE as a fallback until its derivation is established.
Comma-containing ICD cells and other structures require tokenization review;
no HF counts obtained. Next resolve those structures/date lineage, inspect arm
calendar coverage and prespecified baseline-window/nearest-echo feasibility.
# HF source audit version 2: calendar and recency diagnostics

Implemented per-arm first-candidate anchor years and any-candidate order years,
nearest strictly prior candidate-range EF recency, and latest strictly prior echo
EF-band distributions including missingness and same-day band disagreements.
Recency bins are exploratory, not frozen eligibility windows. Added full DX scan
option, lexical tokenization diagnostics and CALC_DX_DATE-year/DX_DATE availability
counts. No local definition of CALC_DX_DATE found; source documentation requested.
No HF phenotype, fallback date, index change or common calendar window selected.
Sixteen HF synthetic tests pass; version 2 cluster results pending.
# HF source version 2 failed during full hospital DX scan

Ryan reports failed_counts_invalid/row_width_mismatch in the hospital DX source
after progress at 42,700,000 records. Exact failing physical line and cause are
unknown. No new calendar/recency or full DX counts are accepted from this run;
earlier successful version 1 evidence remains separate. Added a full-file,
schema-pinned structural diagnostic using strict CSV and literal-line passes,
with capped structural mismatch samples and no raw cell output. Do not rerun
medications/echo or skip/repair records until the DX format issue is understood.
Eight synthetic format tests pass, including late mismatches and schema rejection.
# Hospital DX diagnostic: sole width mismatch at final physical line

Ryan's full structural report reached EOF with unchanged source: 42,763,153 data
physical lines, 42,763,152 matching 17 fields, and exactly one short line at the
final ordinal (one field, no quotes, newline terminated). Strict CSV fails after
211,904 accepted records on unexpected character after closing quote, so changing
to strict CSV does not resolve ingestion. The one-field terminal line may be blank,
whitespace, or nonblank content; its classification is not established. Next read
only a bounded tail and report structural/whitespace flags without source text.
No line exclusion or parser change is approved by this evidence alone, and the
42,763,152 structurally matching lines are not a validated clinical denominator.
# Hospital DX terminal line confirmed empty; explicit parser exception

Ryan's bounded tail report confirms final_line_payload_bytes=0, empty=true,
columns=1 and unchanged source. Combined with the full structure audit, this
supports a narrow explicit terminal-empty-line option for hospital DX only.
Version 3 records one accepted empty LF/CRLF line at verified EOF separately from
data rows. Interior/multiple blank lines, whitespace/BOM payloads and other width
errors still fail. No source edits, clinical eligibility changes or generic row
skipping. Eighteen HF synthetic tests pass; full version 3 H100 run pending.
# HF version 3 now blocked by outpatient DX width mismatch

Ryan reports hospital-terminal-empty-line option enabled; failure stage advanced
to CarDS_2435227_Outpatient_Enc_DX.txt after progress at 9,600,000 rows. Counts remain
invalid; neither exact failing ordinal nor terminal-blank cause is established.
Diagnostic version 3 adds exact empty/whitespace payload and verified EOF position
to structural samples, eliminating the separate tail-check step. Run outpatient
DX only next. No outpatient parser relaxation or new clinical counts accepted.
Eleven synthetic format tests pass, including BOM and bounded-prefix safeguards.
# Outpatient DX terminal empty line confirmed; version 4 parser option

Ryan's full outpatient diagnostic reached EOF with 9,633,590 width-17 physical
data lines and exactly one short final line, zero payload bytes, exact_empty_line
true, and unchanged source. This supports the same narrowly counted EOF-only rule
as hospital DX. Version 4 adds a separate outpatient opt-in, retaining independent
hospital control, strict defaults and no medication parser changes. Nineteen HF
synthetic tests pass; full version 4 calendar/recency results remain pending.
# HF source version 4 completed: calendar/recency feasibility evidence

Ryan supplied complete_requested_scope/counts_valid with EOF and unchanged sources:
30,929,792 medication rows, 661,062 echoes, hospital DX 42,763,152 data rows and
outpatient DX 9,633,590 data rows. Each DX file has exactly one separately counted
terminal blank. Date/code totals and per-arm/year recency/latest-echo counts
reconcile. This completes structural scans, not source-semantic validation.
Candidate-range EF within 1–365 days before first candidate order: carvedilol
10,322/30,611; tartrate 12,180/45,584; ARNI 4,281/5,909; enalapril 242/3,126.
Latest strictly prior echo EF in (1,35], with no recency restriction: carvedilol
2,227; tartrate 831; ARNI 2,541; enalapril 12. These are different marginal
summaries, not their intersection, not HF eligibility or new-user counts. Same-day
echoes excluded; units and availability remain unvalidated. Enalapril feasibility
is markedly limited under this exploratory anchor; not sufficient to declare all
possible prespecified enalapril designs infeasible or change comparator/index.
No arm has 1–365-day EF coverage for anchor years before 2015; this suggests a
temporal source-coverage issue, not proof of absence of earlier echoes. Candidate
orders drop sharply in 2025/2026; administrative coverage cannot be inferred.
Hospital DX_DATE/DX_DTTM missing 10,454,872/42,763,152; outpatient missing
2,181,764/9,633,590. Comparable dates agree with CALC_DX_DATE but its derivation
remains unresolved. Lexically unresolved ICD10 cells: hospital 66,781; outpatient
2,055. No HF-specific code counts or pre-index HF phenotype yet.
Next assess joint latest-echo recency/EF bands and pre-index HF evidence after
code/date-source validation, within a justified common calendar period. No trial
window, threshold, comparator substitution or protocol is frozen by this report.
# 2026-09-20: Joint diagnosis/EF feasibility and proposed missing-data strategy

User authorized investigating broader diagnosis-based HF evidence alongside
measured EF. Version 5 adds optional joint cross-counts by arm/year, separate
DX_DATE/CALC_DX_DATE views, latest-prior echo recency/EF bands and provisional I50
code evidence. No phenotype/date fallback or clinical cohort is frozen. See
RUN_HF_JOINT_EVIDENCE.md for code-set omissions and temporal limitations. Twenty-two
synthetic HF/joint tests pass; cluster run pending. Missing PSM covariates: propose
MICE with PMM for suitable numeric variables, not mean/cluster single imputation;
see COMET_MISSING_DATA_PLAN.md. Eligibility is not imputed. Matching/MI uncertainty
and outcome/design separation require validation before implementation.
# 2026-09-21: Joint HF/EF version 5 completed

Reviewed report confirms full-source completion/counts_valid, expected data counts
and one terminal blank per DX source. Joint totals reconcile per arm/year/date
view with candidate denominators and prior-HF flag counts. Using DX_DATE and latest
strictly prior echo within 365 days, provisional I50 HF evidence plus numeric EF
(1,35] yields carvedilol 704 (445 other HF +259 systolic) and tartrate 235 (143+92).
Systolic code with no prior echo/recent null EF: 211/64; with stale echo: 56/26.
Low recent EF without prior I50 evidence: 1,446/574. Systolic code with latest
recent EF >35–100: 284/135, a review pattern, not necessarily diagnostic error.
Broad prior I50 counts are 3,309/2,492; broad I50 OR recent low EF would be
4,755/3,066 under this anchor, a different population not accepted as COMET.
CALC_DX_DATE adds only one carvedilol prior-HF key (no prior echo), with otherwise
identical COMET joint groups; date agreement does not validate source semantics.
PARADIGM candidate HF-plus-recent-low-EF counts are 982 ARNI and 4 enalapril.
Counts remain exploratory: one ICD10 I50 code suffices, ICD9 and other HF families
unassessed; medication mapping/identity/availability/new-use/clinical eligibility
not validated, calendar window not frozen. Next source/date/code completeness and
trial-index contract, then covariate availability for the declared population;
do not start PSM or choose broader criteria just to enlarge N.
# 2026-09-21: Audit performance without changing clinical rules

No measured version 5 wall time is available. Version 6 adds stage-labelled
progress/elapsed throughput and bounded in-memory caching of repeated DX dates
and HF-code strings; cached/uncached semantics tested (24 HF/joint tests pass).
No clinical criteria, row exclusion or parser changes. No end-to-end speedup claim.
Do not rerun successful version 5 merely for performance measurement. Persistent
validated intermediate tables/checkpoints are planned, not implemented; see
HF_AUDIT_PERFORMANCE.md. Next necessary run can provide measured throughput.
# 2026-09-21: First reusable source-table builder implemented

User authorized a shared layer for subsequent trials. build_shared_tables.py
converts all rows/columns of the reviewed medication, hospital DX, outpatient DX
and echo sources into Zstandard Parquet; no HF/drug/cohort filtering. Raw values
remain alongside source-row lineage, trimmed unvalidated keys and typed calendar
days plus parsing/missing-marker statuses. Clinical semantics/identity remain
unvalidated. Other domains are not yet implemented. Shared outputs use a new
private `/mnt/raid0/rbc58/ecg-tte/shared/` snapshot directory.
Per-source atomic publication preserves completed stages after later failures.
Explicit resume checks code/runtime/source contracts, full source/output hashes,
source fingerprints, schemas and row counts. Incomplete stages are preserved and
rebuilt, not silently appended or reused. A manifest-aware PyArrow dataset reader
rejects incomplete snapshots and supports projected/filterable downstream reads.
Existing raw audit entry points have not been redirected. Sources/OMOP/archive
unchanged. Full active suite: 121 tests pass including 12 synthetic real-Parquet
builder/reader/restart tests in an isolated local PyArrow 23.0.1 environment.
H100 build, actual compressed size and speedup remain unmeasured. Run instructions:
docs/RUN_SHARED_TABLES.md. MICE/PSM/cohort definitions remain separate future work.
# 2026-09-21: First H100 shared snapshot completed

Ryan supplied shared_sources_v1 status=complete, elapsed 1,114.242 s (18.57 min).
All 83,987,596 data rows reconcile with reviewed audits: medication 30,929,792;
hospital DX 42,763,152; outpatient DX 9,633,590; echo 661,062. DX terminal blanks
are separately accounted (one each). Date QC totals agree with prior full scans.
158 Parquet parts total 4,119,797,883 bytes (4.12 GB / 3.84 GiB). Per-table build
times: 637.526 s medication, 382.907 s hospital DX, 89.112 s outpatient DX,
4.333 s echo. Source hashes are present in Ryan's restricted summary/manifest.
This confirms structural ingestion under the versioned contract, not clinical
semantics or identity validation. Exact snapshot directory was not in this pasted
summary and must be retained from the run path. Do not rebuild these four sources
to add other domains; verify new schemas and create compatible extension snapshots.
Next domains for clinical PSM: demographics, labs, vitals and encounters. No shared
query speedup, imputation or matching has yet been measured/run.
# 2026-09-21: Next shared domains, header-only preflight

Prepared inspect_psm_source_headers.py for 20 explicit RBC demographic, lab, vital
and encounter paths from recorded 2025/2026 lineage, including an explicitly
unverified 2026 patient-file probe. It groups reviewed header candidates and reports
missing sources, without reading patient rows, combining deliveries or modifying
the completed shared snapshot. Fifteen header tests pass (two new selection/report
tests). Exact schemas, units, source overlap and date semantics remain to be
reviewed before an extension build. Run docs/RUN_PSM_SOURCE_HEADERS.md next.
# 2026-09-21: RBC PSM extension schemas received

Ryan reports 19/20 header candidates across six schemas; only the probed 2026
Patients file is missing. 2025 demographics exists with BIRTH_DATE, DEATH_DATE,
SEX and race/ethnicity. Hospital encounter schema (55 fields) exposes encounter
IDs, care-class flags and admission/discharge timestamps. Outpatient schema has
17 fields with CONTACT_DATE/ENC_TYPE and encounter IDs. Three vital files share
10 fields including FLO_MEAS_ID/name, MEAS_VALUE, UNIT and RECORDED_TIME.
2025 labs have 51 fields; 2026 labs 49, lacking PAT_DEPARTMENT_ID/NAME present in
2025. Both have COMPONENT_ID/name, ORD_VALUE/ORD_NUM_VALUE and specimen/result
dates/times; neither exposes an explicit units column. Do not infer units solely
from analyte names or silently pool values. Schema evidence does not establish
delivery overlap or lab-component mapping validity. Keep deliveries/shards separate.
Lab files dominate the next extension's raw volume; full-size timing cannot be
extrapolated from the earlier small header check. Next bounded row-structure,
numeric/date/marker and measurement-catalog/unit-source audit before promoting
these new domains. Do not rebuild the completed first snapshot or impute missing
units/absent coverage. Demographic/death freshness remains tied to the 2025 file.
# Bounded PSM extension profiler prepared

profile_psm_sources.py profiles 10,000-record prefixes of the 19 schema-confirmed
PSM extension files. Reports are per-source, schema-pinned and separated into
aggregate format/QC and restricted measurement catalogs. No clinical-value
normalization, units inference, delivery union or snapshot rebuild. No row skipping;
failed files expose no valid partial QC/catalog. Four synthetic tests pass.
Next Ryan runs RUN_PSM_SOURCE_PROFILE.md and reviews summary/catalog locally.

# 2026-09-21: Bounded PSM source profile reviewed

Ryan supplied complete_requested_scope: all 19 sources completed their requested
10,000-row prefixes (190,000 records, not unique patients); none reached EOF. All
counts_valid flags are true, sources unchanged, and date/numeric/unit counters
reconcile with each prefix denominator. No catalog records omitted. Summed reported
per-source time is 23.092 seconds; this is not a full-build runtime estimate.
Lab schemas have no explicit unit field. Vitals UNIT is NULL in 61.23% of the
2025 outpatient prefix, 73.76% of the 2026 hospital prefix and 53.84% of the 2026
outpatient prefix. These prefixes are not representative missingness estimates.
Slash-separated vital values require component-specific interpretation. Lab
ORD_VALUE and ORD_NUM_VALUE format distributions differ, particularly in 2025;
marginal counts cannot establish rowwise equivalence or numeric sentinel safety.
Preserve both raw fields. Do not select ORD_NUM_VALUE merely for higher numeric
completeness. Hospital-file provenance alone does not establish inpatient setting.
Next define separate raw-preserving extension contracts for demographics,
encounters, vitals and labs with full-file accounting and delivery provenance.
Unit mapping is a gate for clinical normalization/PSM features, not for lossless
raw storage. Do not merge/deduplicate deliveries or rebuild the completed core
snapshot. Full-source parsing, component/unit mapping, identity and baseline
availability remain unvalidated; no PSM or MICE has run.

# 2026-09-21: PSM raw source extension implemented

Added build_psm_shared_tables.py for the 19 schema-pinned sources, with delivery/
domain/source lineage and all original strings preserved. Shared engine now
accepts unknown expected counts only with discover_at_eof policy, rejects empty
sources, and reconciles physical/data/terminal-line counts. Explicit CLI opt-in
permits one exact empty LF/CRLF line only at verified EOF per source; no inference
that such lines exist, no interior blanks, generic skipping or source edits.
No unit conversion, clinical normalization, delivery union or numeric lab-field
selection. Existing core snapshot is not rewritten. Implementation hash changed: old
complete snapshots remain readable; old interrupted builds need their original
code to resume. Full active suite 133 tests passed, including six new extension
tests and twelve core builder tests. H100 conversion remains pending.

# 2026-09-21: COMET design and baseline selection prepared during conversion

Added COMET_COHORT_DRAFT.md and COMET_COVARIATE_DICTIONARY.md. These are proposed
contracts, not frozen eligibility or a finalized PSM variable set. Keep measured-EF
and diagnosis-adapted populations separate, reconcile EF boundary, verify exposure
formulation, baseline observation and endpoint capture before clinical execution.
Proposed windows: numeric vitals/labs 90 days, EF/BMI/history 365 days, all strict
prior days. New-prescribing 365-day class washout is a proposal, not the RCT rule.
No drug/ICD/unit map, mortality endpoint or matching parameters silently frozen.
Added generic select_preindex_measurements.py for mapped in-memory events only:
versioned unit/validity contracts, latest-day selection, lineage, no older-value
fallback, explicit date/availability/unit/invalidity/tie states. Unknown availability
blocks the latest measurement. No raw/Parquet adapter, clinical normalization,
cohort engine, MICE or PSM implemented. Thirteen synthetic selection tests pass;
full active suite 146 tests passes. All nine builder implementation-hash input
files are byte-identical to c5ba178, preserving the running conversion contract.
Next review H100 extension completion and restricted component/unit provenance,
then implement clinical adapters and cohort-specific pre-index availability QC.

# 2026-09-21: Parallel core-snapshot COMET candidate job

User clarified that candidate cohort work should proceed during lab conversion.
Implemented build_comet_candidates.py using only the complete core snapshot, with
projected single-thread scans and private RAID outputs. It creates a patient-key
roster with a joint earliest lexical anchor across both arms, unresolved same-day
competing arms, prior365/undated carvedilol-metoprolol family order flags and
latest-prior EF plus independent DX_DATE/CALC_DX_DATE provisional I50 evidence.
This is a change from per-arm first-order audit anchors, explicitly labelled in
output/docs, not a frozen trial index or eligible cohort. No history/route/status/
dose/HF filter or full-class washout; no future-event eligibility. EF=35 separate;
no fallback from latest missing/invalid echo. Same/later HF flags are temporal QC
only, not model features. No MICE/PSM. All 152 tests pass including six synthetic
core-Parquet candidate tests. Builder hash inputs remain byte-identical to c5ba178.
H100 candidate execution/runtime pending; it may contend with conversion for IO.

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

### 2026-09-21 — Expanded beta-blocker history before index qualification

Implemented a lexical history and restricted medication mapping review for the selected excluded v2 cohort. No roster/date/eligibility changes: named generic leads extend beyond carvedilol/metoprolol, while brand-only/unknown suffix leads remain unresolved. All routes/classes are retained for review, not automatically excluded. Prior365, undated and same-day evidence are separate; no match does not establish class washout. The proposed 365-day new-prescribing design still needs mapped medication IDs, route policy and baseline observation evidence. H100 results pending. See RUN_COMET_BETA_HISTORY.md.


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


### 2026-09-23 — Consolidated handoff published
Current-state summary is at the top of handoff.md and supersedes historical
pending claims. Both full encoders and separate same-population PSM comparisons
are complete per supplied H100 reports. No effects or encoder fine-tuning.
BCL geometry/preprocessing audit is next; combined CLMBR/BCL common-population
comparison remains pending. Plot legend fix45bde0e is published; corrected H100
PDF regeneration not confirmed. Preserve all original runs and restrictions.


### 2026-09-23 — Execution mode: HIPAA Claude Code with direct cluster access
User authorized a HIPAA-compliant Claude Code session to read all mounted data and
run analyses directly, writing only under /mnt/raid0/rbc58 and /home/rbc58/github.
AGENTS.md updated. Aggregates-only rule for chat/logs/repo unchanged.

### 2026-09-23 — BCL geometry audit: mV/µV input bug (observed)
Audit requested by the consolidated handoff. As-run BCL vectors are near-identical
in direction (||mean unit|| 0.999995). Root cause: checkpoint BatchNorm running
variance ~1.5e4 implies µV training input; all_ecgs is mV. Same checkpoint with
input x1000 is non-degenerate (||mean unit|| 0.35). COMET linear probes: sex 0.81,
age>=65 0.80, AF 0.75, LVEF<=40 0.69 (as-run: 0.69/0.64/0.62/0.59). Also observed:
`5_0`-flagged files are already 500 Hz in all_ecgs, so they were stretched 5 s→10 s.
Fixing units and sampling to match training preprocessing is a correction, not
tuning to balance. The checkpoint and representation layer are unchanged. As-run BCL
comparison results are invalid as ECG evidence and are preserved as history.
Script: scripts/bcl_embed_uv.py. Output: audits/claude-bcl-uv-fix.

### 2026-09-23 — Exploratory strategy diagnostic (proposed, not frozen)
scripts/diag_matching_strategies.py over five saved imputations. Findings:
- Cosine NN on any embedding leaves max SMD 0.54–0.59.
- Embedding PCs in PS: with the full clinical PS, balance is already <0.1. With a PS
  that withholds EF/labs/vitals, held-out LVEF SMD falls 0.56→0.37 (ECG fixed + CLMBR).
The held-out design, PCA k (32/64) and whitening were chosen during this session after
viewing balance, so these results are exploratory. The proposed protocol is in
docs/STRATEGY.md and must be frozen before any outcome analysis.

### 2026-09-23 — Branch consolidation
`consolidate-2026-09-23` = `psm-mice-imputation` + `codex/comet-outcomes` + this
session's audit. `main` fast-forwarded to it. **`bio-embed-lvsd` is not merged:** it
modifies legacy v1 scripts (stage3/stage4, PARADIGM config) that the restart
archived, and merging it would breach the archive boundary. The branch stays on the
remote as reference. Its `bio_embed.py` loads all_ecgs without µV scaling, so
treat any outputs from it as affected by the same input-unit bug. The container
is now the primary workspace (master.md).

### 2026-09-23 — Phenotype heads, native CLMBR, observed-LVEF evaluation (exploratory)
- Out-of-cohort ECG phenotype heads: 40K ECG–echo pairs, COMET patients excluded,
  seeded patient split. Held-out LVEF≤40 AUC 0.90, AF 0.95.
- Native-numeric CLMBR full run: 7,498 encoded, 81% of numeric measurements accepted.
  Env is an Aug-9 mosaic snapshot with transformers 4.44.2; the code-only run used 5.15.0.
- COMET held-out design, observed-only LVEF SMD: claims 0.52 → +ECG+CLMBR+MUSE+phenotypes
  0.22. Native CLMBR is not better than code-only (0.38 vs 0.36).
- Still exploratory. Feature families were chosen after seeing COMET balance, so any
  claim needs the frozen protocol and the other trials.
- Feasibility screen (OMOP gold, aggregate): see docs/TRIAL_FEASIBILITY_2026_09_23.md.
  Index-day ECG handling and the ECG coverage criterion need a decision.

### 2026-09-23 — User decisions: ECG window and index-day ECG
Ryan: relax the ECG availability window to 365 days before index. An index-day ECG counts
as pre-treatment. Ryan also asked to hold off on scaling to more trials until the
covariate-balance story is coherent ("not just an EF imputer").

### 2026-09-23 — Long-tail balance result (exploratory)
New evaluation: balance on 1,208 held-out pre-index OMOP features never in the PS, with a
noise placebo and an exposure-only hdPS benchmark. Pool-B features with SMD>0.1:
clinical 18.2%, placebo 18.0%, +ECG 14.7%, +CLMBR 4.2%, hdPS100 9.1%.
Defined during this session after the earlier results, so exploratory. Replication on
other trials is proposed before any freeze. See docs/STRATEGY.md.

### 2026-09-23 — Low-dimensional PS + embeddings vs hdPS (exploratory)
At every base (demo/claims/clinical), ECG+CLMBR beats exposure-ranked hdPS100 on long-tail
balance (~half the residual), LVEF balance and retention. A demographics-only base plus
embeddings does not balance the core confounders (LVEF 0.39, AF 0.28). Proposed framing:
embeddings complement or replace hdPS; they do not replace investigator-specified confounders.

### 2026-09-23 — Multi-trial replication contract v1 (PARADIGM-HF adapted; proposed, not frozen)
Ryan asked to check whether the COMET long-tail result replicates before scaling to 10 trials.
Everything below is new code under an explicit contract (no archived code). Specs live in
`scripts/trial_specs.py`; a change to any item is a new `spec_version`.

**Cohort (`scripts/build_trial_cohort.py`, OMOP gold, spec `paradigm_hf_adapted_v1`).**
- Arms: sacubitril/valsartan (tokens `sacubitril`, `entresto`) vs any oral ACEi (10 ingredients
  plus brands; IV enalaprilat is a separate token and is excluded). Orders, not dispensing.
  The screen's enalapril/lisinopril-only arm was widened to all ACEi: the RCT comparator was
  enalapril, but single-ingredient ACEi arms would be small and a class comparator is the usual
  active-comparator adaptation.
- New user: first-ever order of the arm class with index in [2015-07-07, 2024-06-30]
  (US approval date); no order of the other arm in [index-365, index] (index day included).
  This removes ARNI starters with ACEi use in the prior year (the usual clinical switch path).
  That is a deliberate new-user choice: the cohort compares naive/ARB-switched ARNI starters with
  ACEi starters, which differs from the RCT's run-in design.
- Age >= 18 at index; earliest visit <= index-365 (prior activity); a person eligible in both arms
  is kept once at the earliest index.
- Gate: ICD-10 I50 on or before index.
- HFrEF adaptation: exclude a latest echo EF (365 d, index day excluded) > 40. If EF is unknown,
  exclude I50.3x (diastolic) without any I50.2x/I50.4x. Unknown EF otherwise passes.
- RCT safety exclusions, on the latest value in 90 d (unknown passes): eGFR < 30 (concept
  40764999), potassium > 5.2, SBP < 100; angioedema history (T78.3) before index.
- Result: 2,885 ARNI / 2,746 ACEi (attrition in `audits/claude-paradigm-cohort-v1/attrition.csv`).
  The ECG-available analysis population is 4,203 (2,182 / 2,021).

**Core baseline (`scripts/build_core_baseline.py`).** COMET 32-variable table analogue on OMOP gold.
- Age (exact DOB), sex (gender concept), index year.
- LVEF: echo EF, 365 d.
- SBP/DBP/HR/labs: 90 d, latest value per concept. BMI: 365 d. Implausible values -> missing,
  no older fallback. SBP and DBP are taken independently, not from one reading (a gold limitation).
- Nine comorbidities: 365 d ICD-10 prefixes as in COMET staging v3.
- Medications: order in 90 d. For PARADIGM, ACEi/ARNI (arm-defining) are replaced by
  beta-blocker; ARB, MRA, loop, SGLT2i, digoxin and amiodarone are kept.
- Visit counts by concept, 365 d. The index day is excluded throughout.
- Imputation: five datasets from sklearn IterativeImputer(sample_posterior=True) with treatment
  as a predictor. This is not the COMET R MICE pipeline; it is a lighter chained-equation
  substitute chosen for speed across trials.

**Representations.**
- ECG: latest ECG with an existing waveform in [index-365, index], index day allowed (Ryan's
  decision). Ties go to the lexically last fileID. Fixed BCL, `scripts/bcl_embed_uv.py`
  (x1000, no 250 Hz flags). 34% of selected ECGs are index-day.
- Phenotype heads: the COMET-era 40K phenotype set, with every ECG of a cohort patient removed
  from train and test before fitting (`--exclude-cohort`; 1,066 ECGs for PARADIGM).
- CLMBR: code-only, frozen, per-cohort MEDS. `build_comet_meds.py` now also accepts a trial
  cohort report (hash-verified `restricted_cohort.parquet`); its final integrity check no longer
  hard-codes the COMET baseline file.
- Probe gate (PARADIGM): ECG sex 0.81 (below the 0.85 gate, as in COMET), age>=65 0.80, AF 0.76;
  CLMBR AF 0.93. LVEF<=40 is not probeable: the cohort excludes EF>40.

**Panel v2 (`build_preindex_panel.py`).** Code features now hold distinct-day counts in the window
(v1: 1.0 for any), so hdPS can form frequency levels. The evaluator binarises codes, so pool-B
SMDs are unchanged. `--dictionary` rebuilds exactly a given feature set (reference cohorts).
The A/B split is seeded over the dictionary file order. COMET therefore uses its v1 dictionary,
which reproduces v1 pool assignments exactly (verified: identical pairs and pool-B fractions).

**hdPS v2 (`eval_longtail_balance.py`).** Exposure-only ranking, as instructed.
- Candidates: pool-A dx/rx/px codes with once / sporadic (>= median user count) / frequent
  (>= 75th percentile) levels, with duplicates dropped; pool-A lab-measured flags at the once
  level only. Ranked by |log prevalence ratio|; k = 100/200/500. The v1 any-use hdPS100 is kept.
- **Exposure-defining features removed.** Prior orders of either arm's study drug (`rx_<arm keyword>`)
  are dropped from hdPS candidates, pool B and the C-statistic. They are part of the treatment
  definition (standard hdPS excludes exposure codes). In COMET v1 they were present
  (`rx_carvedilol`, `rx_metoprolol`) and were selected by hdPS as near-instruments. That cut
  retention and inflated residual imbalance, so **the COMET v1 hdPS comparator was handicapped**.
  PARADIGM's panel contains no such features: first-ever use and the washout remove them.

**New diagnostics.**
- Prognostic-score balance (`build_prognostic_reference.py`, `fit_prognostic_score.py`): Ryan
  chose 1-year death or HF hospitalisation.
  - Reference set: 30,000 HF patients never in the cohort. The pseudo-index is a seeded random
    visit after their first I50 code, in [index_start, 2023-12-31], with age, prior-activity and
    alive rules.
  - Outcome: death, or an inpatient visit with an I50 code dated within the stay, in (0, 365] d.
    This is a binary outcome with loss to follow-up unmodelled.
  - Features: the same OMOP core builder (median fill plus missing indicators) and the cohort's
    panel dictionary.
  - Two L2 logistic scores. prog_core (core only): reference test AUC 0.73 (PARADIGM) / 0.71
    (COMET). prog_full (core + full panel, CV-chosen C = 3e-4): 0.75 / 0.73.
  - No cohort outcome is extracted. COMET uses the same builder on its roster (spec `comet`, used
    only for prognostic features), so the score is defined the same way in both trials.
- Post-matching C-statistic: 5-fold CV AUC of an L2 logistic model of treatment in the matched
  sample. (a) Core covariates, C=1. (b) Core + pool B, C=0.01; lab NaN is filled with the median.
  A label-permutation check gives 0.50. Franklin et al. (2014) caution that the PS-model version
  of this is uninformative; this one includes covariates never in the PS.
- Chance floor (`summarize_longtail.py`): the expected share of |SMD| > 0.1 in a randomised sample
  with the same number of pairs, 2(1 - Φ(0.1·√(pairs/2))). Methods that trim more have a
  higher floor.
- Grid: 5 imputations × 5 splits (v1: 3 splits).

All thresholds, k values, PCA dimensions and the method ladder were carried over from the COMET
exploratory analysis before PARADIGM results were seen. The exposure-feature removal was found
by inspecting the COMET C-statistic, and was applied to both trials before any pooled results
were read. Still exploratory; nothing is frozen.

### 2026-09-23 — PLATO and ARISTOTLE adapted specs (proposed, not frozen)
Same contract and evaluator as PARADIGM-HF, with specs in `scripts/trial_specs.py`.

**PLATO (`plato_adapted_v1`): ticagrelor vs clopidogrel.**
- Index window 2011-07-20 (US approval) to 2024-06-30. New-user and washout rules as for PARADIGM.
- Gate: I21, I24 or I20.0 in [index-30, index] (unstable angina added to the screen's MI gate;
  PLATO enrolled UA).
- Exclusions: any oral anticoagulant order in [index-30, index]; ICH history (I61/I62) before index.
- Index-event characteristics, an **exception to the index-day exclusion**, because ACS
  management happens on the index day:
  - `stemi_30d`: I21.0–I21.3 in [index-30, index];
  - `pci_index_30d`: PCI CPT/HCPCS/ICD-10-PCS in [index-30, index].
- Extra history: HF, prior PCI/CABG status Z-codes, GI bleeding.
- Medications (90 d): aspirin, statin, beta-blocker, ACEi/ARB, PPI, insulin.
- Prognostic outcome: 1-year death, or an inpatient stay with I21/I22/I63/I64. The reference set
  is ACS patients never in the cohort, with a pseudo-index visit within 30 d after an ACS code.
- CABG is not in the core set (not pre-declared). It turned out to be the dominant residual
  confounder; see STRATEGY.
- Result: 4,503 ticagrelor / 3,477 clopidogrel; 6,759 with ECG + CLMBR (62% index-day ECGs).

**ARISTOTLE (`aristotle_adapted_v1`): apixaban vs warfarin.**
- Index window 2013-01-01 to 2024-06-30. Gate: I48 on or before index.
- Exclusions: mitral stenosis (I05.0, I05.2, I34.2) or mechanical valve (Z95.2) before index;
  any other DOAC order in [index-365, index].
- Extra history: HF, prior bleeding, TIA, liver disease.
- Medications (90 d): aspirin, P2Y12, statin, beta-blocker, ACEi/ARB, antiarrhythmic,
  rate-control CCB, NSAID.
- Prognostic outcome: 1-year death, or an inpatient stay with I63/I64/I61.
- Result: 20,579 apixaban / 5,283 warfarin; 18,771 with ECG + CLMBR.
- ECG AF probe AUC is 0.58, because AF is near-universal in an AF cohort; it is not a gate failure
  in the clinical sense.

### 2026-09-24 — Overnight expansion to 13 trials (assistant discretion, per Ryan's instruction)
Ryan: include as many trials as possible, pivot toward trials where physiology matters, and use
discretion for basic decisions. Full rationale and open questions are in `report.md`.
- **Trial roles, fixed before any results.**
  - Physiology (main test): COMET, PARADIGM-HF, PARAGON-HF, TRANSFORM-HF, ELITE II, LIFE,
    DIONYSOS.
  - Control (no ECG benefit expected): PLATO, TRITON, ARISTOTLE, ROCKET-AF, RE-LY, ALLHAT.
- **Feasibility rule, fixed before building:** the smaller arm must have >= 300 patients with a
  selected ECG. TRITON failed (278 prasugrel users) and is reported, not analysed.
- **LIFE v1** (losartan vs atenolol) failed at 226 atenolol users. v2 widened it to ARB vs
  cardioselective beta-blocker before any LIFE balance was computed.
- **Class adaptations:**
  - ELITE II: any ARB vs any ACEi (trial: losartan vs captopril).
  - ALLHAT: amlodipine vs any thiazide (trial: chlorthalidone).
  - LIFE v2: as above.
- **Eligibility adaptations:**
  - PARAGON-HF: EF >= 45 if measured; if EF is unknown, an I50.3x code is required.
  - TRANSFORM-HF: an I50 code within 30 d stands in for the index HF hospitalisation.
  - LIFE: hypertension plus ECG-text LVH within 365 d, age 55–80, no HF, no MI/stroke in 180 d.
  - DIONYSOS: AF only.
  - The DOAC trials reuse the ARISTOTLE rules.
- **Published HRs** are entered from memory and must be verified before any RCT-agreement use.
- **Pipeline:** unattended `scripts/run_trial_pipeline.sh`, identical to the four-trial analysis.
  The only new diagnostic tables come from `scripts/summarize_all_trials.py`.
- **Observed, not acted on:** the share of index orders written during an inpatient stay differs
  strongly between arms in several trials (e.g. DIONYSOS 17% vs 70%). Setting and route are not
  in any PS; whether to restrict or adjust is an open decision for Ryan.

### 2026-09-24 — Ryan's decisions on report.md §7 and resulting v3 contract
- **Primary population: outpatient initiators** (index order not during an inpatient stay),
  "when possible". Exception, by trial design: PLATO (ACS) and TRANSFORM-HF (HF discharge)
  started treatment in hospital, so all initiators are primary there. The other population is the
  secondary analysis in every trial. `scripts/make_outpatient_cohort.py`.
- **One imputation method for all trials:** sklearn chained equations (IterativeImputer,
  sample_posterior, 5 datasets), re-fitted within each analysis population. COMET now uses the
  same OMOP core-baseline builder as the others (`claude-comet-baseline-omop`, `-op`); the
  earlier R-MICE COMET inputs are kept as history.
- **COMET ECG re-selected under the common rule** (365 d, index day allowed; previously 1–365 d):
  `claude-comet-bcl-v2`, 6,381 ECGs.
- **Published HRs verified** against the source papers and stored in `trial_specs.PUBLISHED`,
  with endpoint and orientation. ROCKET-AF's benchmark is changed to the ITT HR 0.88: our
  initiator emulation is ITT-like, and the per-protocol 0.79 was entered before.
- **Emulation-quality rating** (RCT-DUPLICATE style) instead of dropping low-overlap trials.
  Rubric in report.md, proposed before any outcome.
- **Balance first, then pre-register.** No outcomes until the balance story and protocol are frozen.
- **New evaluation (assistant):**
  - Held-out physiology panel: 10 labs from OMOP gold, plus 26 PanEcho echo-report measurements
    (curated 2015–2022 subset; 1–5% of patients). `scripts/build_physiology_panel.py`.
  - Chance-level SMD per variable, given the measured counts in each matched arm; results are
    reported as excess over chance (validated on a simulated null).
  - A `dxall` sparse base (demographics + every 3-char ICD-10 code with ≥ 2% prevalence).
  - hdPS comparators inside the sparse set.
  - Methods with < 20 matched pairs record retention only (PARAGON-HF outpatient).
