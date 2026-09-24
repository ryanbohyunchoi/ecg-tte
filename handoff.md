# Handoff: adapted COMET cohort, adjustment, and representation benchmark

Last updated: **2026-09-23**. This current-state brief supersedes pending-state
claims in the chronological history below. Cluster results here are from Ryan's
supplied aggregate reports; the assistant did not access H100. No patient records
or embeddings belong in this repository.

## Current result and next action (updated end of 2026-09-23 session)

Read `docs/STRATEGY.md` first; it holds every result table. Everything below is
**exploratory, COMET only**: designs were chosen during the session after earlier results.
No outcomes have been used.

### Overnight 2026-09-24: 13-trial expansion — read `report.md` first
12 adapted trials analysed (TRITON failed feasibility).
- Headline: with a demographics + diagnoses PS, raw ECG PCs cut the residual measured-LVEF
  imbalance by a median of 62% in the 5 trials that had any; all 5 are physiology trials.
- hdPS stays the high-dimensional workhorse.
- Open decisions (report §7): care setting at initiation, HR verification, overlap/weighting,
  primary hdPS k, protocol freeze.

### Replication update (later 2026-09-23; see `docs/STRATEGY.md` "Replication")
- **PARADIGM-HF (adapted) is built** under the new multi-trial contract.
  - Cohort: 2,885 ARNI / 2,746 ACEi; 4,203 have ECG + CLMBR.
  - Pipeline: `docs/RUN_LONGTAIL_REPLICATION.md`. Decisions: `docs/DECISIONS.md`.
- **Evaluator v2** is generic across trials.
  - hdPS gets frequency levels at k = 100/200/500.
  - New diagnostics: prognostic-score balance (external HF reference set), post-matching
    C-statistic, and a chance floor.
- **Correction to item 5 below.** The COMET v1 hdPS picked prior study-drug orders
  (near-instruments). With them removed, hdPS100 ≈ CLMBR in COMET, and hdPS200 ≈ CLMBR in
  PARADIGM. hdPS500 is better on long-tail balance, at lower retention.
- **What replicates:** CLMBR's large gain and ECG's modest gain over the clinical PS. Stacking
  hdPS + ECG + CLMBR is best in both trials.
- **PLATO and ARISTOTLE done (same pipeline).** hdPS beats CLMBR clearly in both, and ECG adds nothing
  to long-tail balance. CLMBR worsens prognostic-score balance in PARADIGM and ARISTOTLE.
  Stacking hdPS + ECG + CLMBR is best in all four trials, at a 12–36% retention cost.
  See the four-trial summary in STRATEGY.
- Next decisions for Ryan:
  - Is hdPS (plus embeddings) the primary high-dimensional arm?
  - Should CABG/index-procedure features become PLATO core covariates? That would be a new
    spec version, decided before any outcome.
  - Negative-control outcomes.

### What was established
1. **The BCL ECG collapse was an input bug.** Checkpoints expect µV, but `all_ecgs` is mV,
   and 250 Hz-flagged files were stretched. Fixed with `scripts/bcl_embed_uv.py` and
   re-embedded (`audits/claude-bcl-uv-fix`). Earlier BCL comparison results are invalid;
   they are preserved as history.
2. **The fixed BCL is clinically informative.** Out-of-cohort linear heads on 40K ECG–echo
   pairs (COMET excluded) give held-out LVEF≤40 AUC 0.90, AF 0.95. No retraining is needed
   for now (`docs/ECG_MODEL.md`).
3. **Cosine matching on any embedding does not balance confounders.** It has been dropped as
   a primary method.
4. **Native-numeric CLMBR is no better than code-only.**
5. **Core result: long-tail balance.** Evaluated on 1,208 held-out pre-index OMOP features
   (`scripts/build_preindex_panel.py`, `scripts/eval_longtail_balance.py`), with a noise
   placebo and an exposure-only hdPS benchmark.
   - The rich clinical PS leaves 18% of features at SMD > 0.1; the placebo also gives 18%.
   - +ECG gives 14.7% (information orthogonal to codes).
   - +CLMBR gives 4.2%; hdPS100 gives 9.1%.
   - At every base (demo / claims / clinical), ECG+CLMBR beats hdPS on long-tail balance,
     LVEF balance and retention.
   - Embeddings do NOT replace the core clinical confounders: a demographics-only base
     leaves LVEF/AF imbalanced.
6. **Held-out LVEF:** under a claims-only PS, unstructured features reduce observed LVEF SMD
   0.52 → 0.22.
7. **Trial feasibility screen** (`docs/TRIAL_FEASIBILITY_2026_09_23.md`): PLATO, TRITON,
   COMET and PARADIGM-HF lead.

### Ryan's decisions (2026-09-23)
- ECG window: 365 d before index. An index-day ECG counts as pre-treatment.
- Container is the primary workspace (`master.md`); `main` is the trunk; push regularly.
- Don't scale to 10 trials until the covariate-balance story is coherent. It must be more
  than "an EF imputer".

### Proposed story (not frozen)
Structured PSM balances what it is given but leaves the rest of the record imbalanced.
- EHR foundation-model embeddings are a better high-dimensional complement than hdPS.
- ECG embeddings add physiologic information that no code set contains.
- The question for the multi-trial study: does this better balance bring estimates closer to
  the RCT?

### Next actions
1. **Replicate the long-tail analysis in 2–3 other trials** (PLATO, PARADIGM-HF, ARISTOTLE).
   This needs:
   - a cohort + clinical baseline for each, under the new contract;
   - the fixed BCL embedding with a 365 d window;
   - CLMBR code-only encoding (MEDS build per cohort, see `docs/RUN_COMET_MEDS_AND_CLMBR.md`);
   - the pre-index panel.
2. **Strengthen hdPS as a comparator:** add frequency levels (once/sporadic/frequent) and
   k = 200/500. An outcome-ranked hdPS waits until outcome use is allowed by protocol.
3. **Negative-control outcomes** (balance ≠ bias): pre-specify a set, then check whether
   embedding-augmented PS moves NCO HRs toward 1.
4. **Stronger balance diagnostics:** prognostic-score balance, and
   C-statistic-of-treatment-after-matching.
5. **Freeze the protocol** (base covariates, embedding k, hdPS spec, evaluation panel)
   before any trial outcome.

## Cohort and adjustment state

- Adapted COMET exploratory baseline: **7,499** people, **4,539 carvedilol** and
  **2,960 metoprolol tartrate**, after the adopted calendar/quality restrictions.
  The medication anchor is an outpatient order proxy, not verified dispensing or
  ingestion; this is not a strict replication of COMET trial eligibility.
- Saved 32-variable baseline and five completed MICE datasets are reused.
  Ordered-BP pilot: five imputations, 50 iterations; recorded invalid completed
  BP pairs zero. Computational checks do not prove MAR or convergence sufficiency.
- Original clinical PSM is the primary comparator; the previously refined PSM is
  explicitly secondary and was developed after observing diagnostics. Preserve
  original results. PSM uses 1:1 greedy matching without replacement and a
  0.2 pooled within-arm SD caliper on propensity-score logits.
- Representation comparisons subset existing imputations to their common input
  population and rerun both PSM versions. They do not refit MICE or change the
  evaluated clinical feature set. Balance includes missingness indicators;
  undefined SMDs are not zero. Observed-only balance is also saved.
- The earlier source snapshots and candidate event cache are complete. Do not
  rescan huge raw files for each analysis. Damaged hospital lab file 3 was not
  silently repaired or included; verified limited lab sources remain documented.

## CLMBR findings to preserve

Frozen CLMBR-T, 768 dimensions, code-only, last 4,096 retained tokens, latest
retained-token representation. **7,498 encoded: C 4,538 / T 2,960**; one carvedilol
patient had no clinical events. 102 histories truncated. Numeric values were
omitted and explicit sex/race tokens were not included. Mapping/token acceptance
is not a clinical validity test. These input limitations may matter but have not
been shown to explain the balance results.

The first greedy matching version consumed the entire smaller arm from a fixed
majority-arm prefix: retained-set comparisons were embedding-independent. Preserve
that flawed result as history, not evidence of encoder inferiority. Corrected
smaller-arm greedy and global-optimal versions followed explicitly.

| On the 7,498-person CLMBR population | Pairs | Mean absolute SMD across imputations |
|---|---:|---:|
| Original PSM | 2,382–2,426 | 0.03055–0.03476 |
| Previously refined PSM | 2,368–2,400 | 0.01820–0.02322 |
| Global optimal CLMBR cosine, no caliper | 2,960 | 0.09465–0.10076 |
| CLMBR cosine caliper 0.20 | 1,430 | 0.07672–0.08151 |
| CLMBR cosine caliper 0.30 | 2,352 | 0.08656–0.09256 |
| CLMBR cosine caliper 0.40 | 2,874 | 0.09473–0.10040 |

All three cutoffs were user-selected exploratory sensitivities and are retained;
none is a validated optimal threshold. Global assignment reduced total cosine
distance by about 6.4% versus greedy but did not improve average clinical balance.
Observed-only EF/AF imbalance persisted; the gap was not confined to imputed
values. This supports a conclusion about these method/input combinations, not
general encoder quality or treatment-effect accuracy.

## ECG BCL: completed (as-run vectors superseded by the µV fix above)

Upstream: `CarDS-Yale/ECG-signal-pipeline`, pinned commit
`d359c04d1f5e6c810f76751777535918870704b7`.
Checkpoint SHA256:
`3a5df9efa95bab0db99f419cfb85ad7a8d4b63f6bb765e10021d636ae8b64d4a`.
Saved configuration: BCL, 12 leads, 10 seconds, 500 Hz, lead_time_transformer.
**Output is the 256-dimensional backbone BEFORE the projection head**, not the
legacy archived Net1D representation. No weights were trained or fine-tuned.

Metadata is `/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet`.
Waveforms are under `/mnt/raid0/bb2238/signals/preprocessed/all_ecgs`.
The lowercase `fileID` contains subdirectories and an optional `.npy` suffix.
Initial flat-path/ID checks rejected these paths and misleadingly selected zero.
Fixed v2 preserves relative paths, canonicalizes the suffix and sampling IDs,
rejects traversal/symlinks, and retains global identity/timing collision checks.
No basename guessing or older-date fallback was introduced.

Selection: latest strictly prior calendar day 1–365 before the existing index;
lexical canonical ID on that day; required unambiguous sampling label.

| Selection status | Carvedilol | Metoprolol tartrate |
|---|---:|---:|
| Selected and subsequently encoded | 3,561 | 2,542 |
| No prior-365-day ECG | 868 | 359 |
| Sampling label unresolved | 110 | 59 |

Selected **6,103 / 7,499 (81.4%)**; 583 have the catalog's 250 Hz flag. Private
normalized catalogs reproduce the upstream `5_0` test; they do not independently
validate sampling frequency or lead order. Smoke included 8 per arm/sampling
stratum. All 32 passed in 16.299 seconds. Full run passed all 6,103 in
660.588 seconds, with zero load errors, nonfinite rows or zero vectors.
Inference used one H100, fp32, batch 8, workers 2, no augmentation/filtering;
full shards contain up to 512 rows. Finite/nonzero checks do not establish useful
representation geometry. Full-run v1 did not save vector-content checksums;
the subsequent linkage adapter recorded current hashes and repeated output QC,
which cannot retrospectively prove original vector byte identity.

## ECG BCL comparison result (invalid: mV input bug)

Report: `/mnt/raid0/rbc58/ecg-tte/audits/comet-bcl-comparison-FZIo043w/report`.
Starting population: **6,103 (C 3,561 / T 2,542)** for all methods below.

| Method | Pairs retained | Mean absolute SMD | Features with absolute SMD >= 0.1 |
|---|---:|---:|---:|
| Original PSM | 1,980–2,050 | 0.02735–0.03948 | 2–4 |
| Previously refined PSM | 1,977–2,036 | 0.01852–0.02388 | 0–2 |
| ECG BCL global optimal cosine | 2,542 | 0.10360–0.10856 | 19–24 |

Ranges are across the five saved imputations. BCL pairs are fixed; clinical
measurements differ across imputations. Cosine matches all 2,542 metoprolol
patients to 2,542 distinct carvedilol patients (71.38% of carvedilol), without a
cosine caliper. Clinical PSM retains its caliper. BCL had worse measured balance
and higher retention. Do not claim isolated metric superiority or inferior
causal accuracy from these results. BCL maximum SMD is 0.542–0.596.
Matched cosine median 3.106e-7, p95 1.232e-6, maximum 0.000389883;
these warrant the geometry investigation above.

Original PDF: `comparison_love_plots.pdf` inside that report. Its old CLMBR
legend refers to ECG BCL. Correct it with the representation-aware plotting
script into a fresh directory, preserving the original report manifest.
A combined CLMBR-versus-BCL analysis has **not** run; a verified shared population
is needed before comparing them directly.

## Exact reusable H100 artifacts

All paths below are under `/mnt/raid0/rbc58/ecg-tte/` unless shown otherwise.

| Artifact | Relative path |
|---|---|
| Clean MICE input | `audits/comet-mice-prep-M9F28Lk2/report` |
| Five ordered-BP imputations | `audits/comet-mice-pilot-v2-w5ZRCHzh/report` |
| CLMBR MEDS | `shared/comet-meds-v1-3hgAkgoB/meds` |
| CLMBR full embeddings | `audits/comet-clmbr-full-NAyb4G2x/report` |
| CLMBR optimal no-caliper comparison | `audits/comet-cosine-comparison-v3-HKXiJR7g/report` |
| CLMBR caliper grid | `audits/comet-cosine-caliper-grid-XhRUMLhu` |
| CLMBR observed-only review | `audits/comet-observed-review-CLXuw3X7/report` |
| BCL v2 selection | `audits/comet-bcl-input-v2-C9ftzPbQ/report` |
| BCL smoke inputs | `audits/comet-bcl-smoke-prep-SWznZWZE/report` |
| BCL smoke outputs | `audits/comet-bcl-smoke-Ik5VklyT/report` |
| BCL full run | `audits/comet-bcl-full-lMQtaSyg` (input/ and report/) |
| BCL linked vectors | `audits/comet-bcl-comparison-FZIo043w/linked` |
| BCL comparison (invalid, mV input) | `audits/comet-bcl-comparison-FZIo043w/report` |
| **BCL re-embedding, µV fix** | `audits/claude-bcl-uv-fix` |
| Strategy diagnostic (as-run / fixed ECG) | `audits/claude-matching-diagnostic`, `audits/claude-matching-diagnostic-uvfix` |
| BCL working environment | `software/bcl-smoke-runtime-zZ5FVVsd/env` |
| Pinned BCL source checkout | `software/bcl-smoke-runtime-zZ5FVVsd/upstream` |
| R environment | `software/mice-r-v2-tyXlJyw1/env` |

Python for cohort/matching on core-hpcws2: `/home/rbc58/miniconda3/envs/mosaic/bin/python`.
Inside the HIPAA Claude Code container that path does not exist. Use
`/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python` (pandas/pyarrow/sklearn/lifelines).
Use existing launchers for its SciPy C++ runtime workaround and R isolation.
BCL working versions: torch 2.5.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6.
No need to reinstall or repeat successful inference.

## Proposed research direction, not implemented

Ryan asked whether to develop a TTE-specific encoder. Discussed frozen embeddings
in regularized propensity models, clinical-plus-embedding propensity models,
small learned projections, and eventual encoder fine-tuning. No training objective,
loss weights, training cohort, checkpoint, or evaluation split has been frozen.
Do not present any as implemented. Preserve unsupervised/frozen results as baseline.
Any new learned method needs separate development patients/trials, patient-overlap
control across trials, and held-out evaluation. Keep evaluation outcomes and
published RCT effects out of design tuning; keep post-index events out of inputs.
Balance, overlap/retention and effect recovery are distinct evaluation dimensions.
User specifically rejects gaming balance or selecting a method to recover the
published effect. A constant representation would appear balanced in embedding
space without preserving clinical confounding information.

## Validation and handoff boundaries

Implemented code through `45bde0e` is on `psm-mice-imputation`. Local verification
included 12 BCL tests, 11 cosine tests, R original/refined/external-pair and
observed-balance integration, and synthetic corrected-PDF generation. These are
synthetic checks; H100 results above came from user reports up to 2026-09-23. From
2026-09-23, Claude Code runs in an approved HIPAA environment with direct read access
and write access to `/mnt/raid0/rbc58` only (see AGENTS.md). The audit results in the
top section were produced there as aggregate outputs. No endpoint estimation was
performed.

Next session should read this brief, `master.md`, `docs/DECISIONS.md`,
`docs/COMET_BALANCE_EVALUATION_PLAN.md`, `docs/COMET_BCL_COMPARISON_PLAN.md`, and
`docs/RUN_COMET_BCL_COMPARISON.md`. Continue from saved artifacts. Do not rerun old
launchers blindly or overwrite old outputs. Outcomes/follow-up remain a separate
track; verify its current branch/handoff rather than inferring completion here.

Chronological history before 2026-09-23 moved verbatim to `docs/HANDOFF_HISTORY.md`.
