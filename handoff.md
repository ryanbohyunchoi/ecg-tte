# Handoff: adapted COMET cohort, adjustment, and representation benchmark

Last updated: **2026-09-23**. This current-state brief supersedes pending-state
claims in the chronological history below. Cluster results here are from Ryan's
supplied aggregate reports; the assistant did not access H100. No patient records
or embeddings belong in this repository.

## Current result and next action

**The BCL geometry/preprocessing audit requested below has run (2026-09-23, direct
cluster access, aggregate outputs only). The near-zero BCL cosine distances came from
an input-unit bug, not from the model.** The BCL checkpoints were trained on µV input,
but `all_ecgs` stores mV. The eval-mode network therefore saw ~1000x-too-small inputs,
and every ECG mapped to nearly the same vector. The earlier ECG BCL cosine and BCL
comparison results below are **invalid as evidence about ECG information**. Preserve
them as history.

Observed facts (COMET n=6,103; details in `docs/ECG_MODEL.md`, `docs/STRATEGY.md`):
- As-run vectors: ||mean unit vector|| = 0.999995. Random-pair cosine distance median
  1.9e-6. First-BatchNorm stored input variance ~1.5e4 vs ~0.013 observed at input.
- Re-embedded with the same checkpoint, input x1000 and no 250 Hz stretching
  (`scripts/bcl_embed_uv.py`; output `audits/claude-bcl-uv-fix/`): ||mean unit|| 0.35.
  5-fold linear-probe AUC sex 0.69→0.81, age≥65 0.64→0.80, AF 0.62→0.75,
  LVEF≤40 0.59→0.69.
- Second bug: catalog `5_0` (250 Hz) files are already 500 Hz in `all_ecgs`, so
  `process_ecg` stretched 5 s to 10 s for 583/6,103 COMET ECGs.
- Exploratory strategy comparison (`scripts/diag_matching_strategies.py`, 5 imputations,
  outputs `audits/claude-matching-diagnostic{,-uvfix}/`):
  - Cosine matching on any embedding, with any preprocessing, leaves max SMD 0.54–0.59
    (LVEF, AF).
  - Adding centred embedding PCs to a PS that withholds EF/labs/vitals reduces held-out
    LVEF SMD: 0.56 (claims-only) → 0.42 (+ECG) / 0.45 (+CLMBR) / 0.37 (+both).
  - This held-out design and the PCA settings were chosen after seeing data. They are
    **exploratory, not frozen**. No outcomes were used.

**Later on 2026-09-23 (details in `docs/STRATEGY.md` "Update" section):**
- Out-of-cohort ECG phenotype heads work: LVEF≤40 AUC 0.90, AF 0.95.
- Native CLMBR is encoded; it is no better than code-only.
- Unstructured features cut observed-LVEF SMD under a claims-only PS from 0.52 to 0.22.
- Trial screen done: PLATO, TRITON, COMET and PARADIGM-HF lead.

**Core result so far (long-tail balance, `docs/STRATEGY.md`):**
- The clinical PS leaves 18% of 636 held-out pre-index features imbalanced; the noise
  placebo gives 18%.
- +ECG gives 14.7% (orthogonal to codes); +CLMBR gives 4.2%; hdPS gives 9.1%.
- Ryan's decisions: ECG window 365 d; index-day ECG counts as pre-treatment.
- Ryan wants a coherent balance story before scaling.

**Next action (proposed, not frozen):**
1. Replicate the long-tail test on PLATO, PARADIGM-HF and ARISTOTLE.
2. Add negative-control outcomes.
1. Freeze the evaluation protocol: method ladder, held-out covariate set, PCA k.
2. Re-embed any further cohorts only through the fixed wrapper, and gate them with
   `scripts/embedding_utils.py`.
3. Decide whether to add supervised ECG phenotype probabilities, or to train a supervised
   multi-task ECG model (`docs/ECG_MODEL.md`).
4. Rerun CLMBR with numeric values.

The Love-plot relabel item from the previous brief is moot for BCL: the BCL
vectors themselves are superseded.

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
