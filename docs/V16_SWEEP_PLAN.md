# v1.6 exploratory sweep: where and when do AI-ECG embeddings add value? (2026-09-26)

**Status: exploratory methods analysis, NOT protocol-frozen.** Specifications are chosen after seeing
the v1.3–v1.5 results. Every finding is hypothesis-generating. This file is written before any v1.6
results exist and lists the full grid. **All** cells are reported, including null and harmful ones.

## Question
Across 18 Yale target-trial emulations, under which set points does adding the BCL AI-ECG embedding to
a propensity score (PS) significantly (a) improve balance on characteristics NOT in the PS and
(b) move emulated HRs closer to the RCT?

## Fixed pieces (reuse)
- Trials: the 18 in `scripts/make_acc_figure.py::trials` (PRIMARY + EXTRA with bootstrap outputs).
- Engine: `scripts/v13_common.py` (Trial, ps_logit, match, cox, outcomes, bench). Imputation 1, pool
  split seed 0. The primary outcome is taken at the trial horizon.
- RCT benchmark: `bench(key)`.

## Sweep axes (each run with vs without ECG, plus placebo ECG: `shufECG` and `noise32`)
- **S1. Baseline PS richness ladder:** unadjusted → demo (age, sex, index year) → demo + race →
  minimal-7 (age, sex, race, T2D, CAD/IHD, HTN, hyperlipidemia) → sparse (current) → hdPS k ∈
  {25, 50, 100, 200} → clinical.
- **S2. Code sparsity (real data):** dropout p ∈ {0, 0.25, 0.5, 0.75, 0.9, 1.0} applied to sparse and hdPS.
- **S3. ECG representation and PS model:**
  - ECG: PCs {4, 8, 16, 32, 64, 128}, full 256-d, ECG phenotype scores, phenotypes + PCs;
  - PS model: L2 C ∈ {0.1, 1, 100}, GBM;
  - estimator: match caliper {0.05, 0.1, 0.2}, IPTW, overlap weights.
- **S4. Population / effect modifiers:**
  - ECG recency (lag ≤ 30 / 90 / 365 d);
  - echo available vs not;
  - code-density tertile;
  - age group;
  - outpatient vs inpatient index;
  - trial role (physiology vs control);
  - confounding magnitude (|unadjusted − RCT| tertile).

## Outcomes per cell
- **Balance (held-out, never in that PS):**
  - per-variable |SMD| on the 58-variable panel (as in `make_acc_figure.VARS`);
  - per-trial mean |SMD|;
  - a multivariate balance test: cross-fitted C-statistic of held-out variables predicting treatment in
    the matched set;
  - prognostic-score SMD.
- **RCT agreement:**
  - |Δlog HR| vs RCT;
  - precision-standardized z² = Δ² / (se² + se_RCT²);
  - statistical consistency (|z| < 1.96);
  - dispersion φ.
- **Paired inference across trials:** exact sign-flip on per-trial (ECG − no-ECG) differences.
  Benjamini–Hochberg FDR within each sweep family and across the whole grid (both reported).

## Guardrails
1. **Placebo rule:** a gain counts as ECG-specific only if ECG also beats `shufECG` and `noise32` in
   the same cell. Otherwise it is dimension or regularisation, not ECG information.
2. **Full reporting:** every cell appears in the results tables and heat maps, significant or not.
3. **Split confirmation:** cells flagged in discovery (patient half A, seeded) are re-estimated in
   half B. Both halves are reported.
4. **Consistency check:** the engine reproduces the saved v1.3 point estimates
   (`check_against_saved`) and the saved `summary_pooled.csv` SMDs before any sweep runs.
5. **Aggregate outputs only:**
   - CSV and parquet go under `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-<name>/`;
   - markdown goes in `docs/v16/`;
   - counts of 1–10 are suppressed.
6. External confirmation of any headline cell in MIMIC/UKB is deferred; it is noted as a limitation.
