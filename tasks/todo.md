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

- [x] Pull latest cards-misc main and trace source patterns, retained fields and feature-branch differences.
- [x] Document 24 candidate ETL inputs within the latest 64-file source audit and PSM limitations.
- [x] Build read-only existing-OMOP manifest/schema inspector; four synthetic tests pass (33 total).
- [ ] Ryan returns reviewed existing-bb2238 manifest/schema evidence; establish producing run/version and mapping resolution without changing the dataset.
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
