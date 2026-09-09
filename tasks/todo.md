# Restart work tracker

Status as of 2026-09-09. Checked means completed with evidence, not merely planned.

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
- [x] Resolve execution boundary: no assistant SSH; Ryan pulls and runs code on the H100 (see `master.md`).
- [ ] Confirm raw source roots, extract versions, and output destination through user-run discovery.
- [ ] Establish what notes, ECGs, echo images/videos, and checkpoints are available.
- [ ] Inventory source files and obtain source dictionaries/extract specifications.
- [ ] Implement a new aggregate-only, bounded-memory JDAT profiler with synthetic tests.
- [ ] Run metadata/schema profiling on the cluster; return reviewed aggregate reports.
- [ ] Resolve parse rules, linkage, duplicates, and source date semantics.
- [ ] Validate medication event classes and ascertainment windows.
- [ ] Validate encounters, mortality, labs/vitals, and modality timestamps.
- [ ] Produce a signed-off source map and initial trial-feasibility table.

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

No raw-data inspection, replacement clinical analysis, or superiority result has
been completed during this restart.
