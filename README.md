# Multimodal target trial emulation benchmark

We are restarting this project to test whether representations learned from ECGs,
structured EHR, clinical notes, and echocardiography improve recovery of published
randomized-trial effects compared with a strong propensity-score matching baseline.
Improvement is a research hypothesis, not a required outcome of the analysis.

**Current phase: research design and raw JDAT source investigation.** There is no
active replacement analysis pipeline yet. No new patient data have been inspected
and no new treatment effects have been estimated during this restart.

The first tool is ready: [run the JDAT file inventory on the H100](docs/RUN_JDAT_INVENTORY.md).
It lists filenames and sizes only. Ryan runs it and reviews the report before sharing.

Next: [inspect selected JDAT column headers](docs/RUN_JDAT_HEADERS.md), using the
T2DM filenames Ryan supplied. This reads only a bounded first line per candidate.

Next record-level step: [run bounded mapping reconnaissance](docs/RUN_JDAT_MAPPING_AUDIT.md).
This checks field presence and code counts; standard mappings and CLMBR-T inputs
are not yet validated.

## Start here

- [Detailed restart plan](docs/RESTART_PLAN.md): questions, experimental design,
  statistical comparison, implementation sequence, and completion gates.
- [Raw JDAT investigation](docs/RAW_JDAT_INVESTIGATION.md): source inventory,
  profiling specification, temporal semantics, and normalized data contracts.
- [Component audit matrix](docs/COMPONENT_AUDIT.md): what must be investigated and
  the evidence required before each component is trusted.
- [Decision register](docs/DECISIONS.md): accepted directions, proposed defaults,
  open questions, and decisions required before effect estimation.
- [Research references](docs/REFERENCES.md): source-checked context and remaining
  literature/protocol verification work.
- [Current task list](tasks/todo.md).

## Legacy archive

All 74 previously tracked files were preserved in
[archive/2026-09-09-legacy-v1](archive/2026-09-09-legacy-v1/ARCHIVE.md), with a
SHA-256 inventory of their exact contents. The source revision is
`dd723066e3c6c2e3be9ce61c7503a95dc82e5f5b` (2026-08-05).

The old scripts, configurations, results described in notes, and methodological
assumptions are **reference only**. New code must not import or execute the archive.
The previous 32 configs are candidate ideas, not validated new protocols.
Git history remains available. Cluster datasets and outputs were not moved.

## Working principles

Raw JDAT extracts are the intended source of truth. Derived OMOP data may help
reconcile records, but are not the default source for the new analysis. Model
adapters may still need standard clinical vocabularies.

Establish reliable exposure, eligibility, time zero, follow-up, endpoints, and a
competitive conventional baseline before testing representations. Compare methods
on declared populations and estimands. Freeze the evaluation before examining
new benchmark treatment effects, and retain failed and inconclusive analyses.

Patient records, notes, signals, images, embeddings, linkage keys, and granular
profiling outputs remain in the approved research environment. The repository
contains code, protocols, synthetic test fixtures, and reviewed aggregate reports.

## Change log

- **2026-09-09:** Added explicit T2DM header inspection, per-file progress, conservative
  header validation, and H100 commands. All 15 synthetic tests pass; no real headers
  have been inspected by the assistant. Recorded the user-provided inventory findings.
- **2026-09-09:** Added a standalone metadata-only inventory and H100 run instructions;
  seven synthetic tests passed. Cluster execution and source verification are pending.
- **2026-09-09:** Archived legacy v1 without changing its tracked file contents;
  created the new multimodal benchmark plan, raw-source investigation specification,
  component audit, and decision register. Implementation and raw-data validation
  remain pending.
