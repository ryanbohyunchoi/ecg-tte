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
