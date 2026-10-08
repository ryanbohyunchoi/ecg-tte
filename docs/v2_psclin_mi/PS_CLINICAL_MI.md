# PS-Clinical (no LVEF) with 5-draw multiple imputation on the spec-v2 fixed cohorts

Written 2026-10-08 (queue `docs/queue/QUEUE_2026_10_08.md`, step B; pipeline.md §4 and §9 deviation "5-draw multiple imputation instead of a single draw").

- **Code:** `scripts/v2_psclin_mi/psclin_mi.py` (impute / run / gate / combine / summarize / privacy).
- **Reused unchanged:**
  - `build_core_baseline.impute` (IterativeImputer, `sample_posterior=True`, seeds 20260923 + k − 1 for draws k = 1–5, as `scripts/v1_psclin_nolvef/imputation_draws.py`);
  - the `clinical_nolvef` design and masks of `scripts/v1_psclin_nolvef/psclin_nolvef.py`;
  - the spec-v2 rows, outcome re-definitions, within-cohort PCs and placebo permutation of `scripts/v2_cohorts/grid.py`;
  - the endpoint code of `scripts/v21/paper2_grid.py` / `scripts/v20/sens_primary32.py` (through `scripts/v2_cohorts/summarize.py`).
- **Outputs** (umask 077, not committed): `/mnt/raid0/rbc58/ecg-tte/audits/claude-v2-psclin-mi/`. This document reports aggregates only: trial counts, means, CIs and P values.

## Plain-language summary

- **What was done.** PS-Clinical without LVEF was re-imputed **within each spec-v2 fixed cohort** with 5 independent imputation draws, and LVEF was removed from the imputation model. The full rung was then run for all 6 PS methods × 38 trials × 5 draws (7,030 cells). The draws were combined:
  - **balance:** per-item |SMD| averaged over the 5 draws, then the usual endpoints;
  - **HRs:** Rubin's rules.
- **Gate passed.** With the version 1 cohorts and draw 1, the code reproduces every existing PS-Clinical-no-LVEF cell exactly: 1,406 cells (6 methods × 7 arms, incl. CLMBR-T 32 PCs, × 38 trials), 98,420 values, maximum deviation 0.
- **Headline (spec-v2 cohorts, 1:1 caliper 0.2, 54 leakage-corrected items, 45 held out for this rung).** The ECG on top of PS-Clinical (no LVEF):
  - **provisional v2 set (29 trials): 4.4% (95% CI 0.9 to 8.0)**, 19/29 trials better, P = .009;
  - paper 1's 32 trials: 2.4% (−1.8 to 6.5), 20/32, P = .13;
  - all 38: 3.0% (−0.8 to 6.9), 25/38, P = .06.
- **Against the permuted ECG,** the ECG gives 6.0% (2.9 to 9.3) on the 29 trials (P < .001) and 5.9% on all 38. The permuted ECG itself makes balance slightly worse: −1.7% (29 trials) to −3.4% (32 trials).
- **Draw-to-draw range of the main contrast** (ECG vs PS alone, 54 items):
  - 29 trials: 4.4 / 4.9 / 1.7 / 5.6 / 5.4 (range 1.7 to 5.6);
  - 32 trials: 0.0 to 4.4;
  - all 38: 0.7 to 4.6.

  The MI estimate sits inside each range.
- **Where it helps (29 trials):**
  - observed LVEF, the only vitals/labs item not masked: 16.0% (4.1 to 27.9), P = .008;
  - all 35 echo items: 4.8% (1.2 to 8.5), P = .008;
  - LV structure: 8.1% (1.0 to 15.6).
- **RCT agreement:** no change. |Δ log HR| (Rubin-combined log HR) goes from 0.155 to 0.153, 17/29 trials closer, sign-flip P = .43, benchmark-permutation P = .44.
- **The ladder on the spec-v2 cohorts** (+ ECG vs PS alone, main, 54 items):

  | PS base | 29 trials | 32 trials | 38 trials |
  |---|---|---|---|
  | PS-Demo | 9.5% (5.2 to 13.9) | 11.8% | 12.5% |
  | **PS-CVD5 (primary)** | **6.5% (2.2 to 11.4)**, 21/29, P .004 | 6.6% (2.0 to 11.4) | 6.7% (2.5 to 10.8) |
  | PS-CVD10 | 4.7% (−1.0 to 10.6), P .07 | 3.2% | 4.1% |
  | hdPS | −0.9% (−5.3 to 4.3) | −0.3% | −0.2% |
  | PS-Clinical (no LVEF), MI | 4.4% (0.9 to 8.0), P .009 | 2.4% | 3.0% |

- **Bottom line.** Even with proper MI on the fixed cohorts, the ECG still gives a small gain at the richest PS level on the provisional 29-trial set. It is concentrated in observed LVEF and the echo domain, and it is clearly better than its permuted placebo. The gain is smaller and not significant on paper 1's 32 trials. The draws differ by about 4 points, so single-draw estimates should not be reported.

## 1. Design

| Element | Choice |
|---|---|
| Cohorts | spec-v2 fixed cohorts: rows = version 1 analysed rows not flagged `drop_v2` (`scripts/v2_cohorts/specs_v2.py`, `audits/claude-v2-cohorts/flags/restricted_drop_*.parquet`); AMPLIFY, LODESTAR and PROVE IT outcomes re-defined (`restricted_outcome_*.parquet`), exactly as `grid.py` |
| Imputation population | **the fixed cohort only**: observed baseline rows (`claude-<trial>-baseline-v11/restricted_baseline_observed.parquet`) of the fixed cohort's patients. Version 1 imputed on the full baseline roster (pre-ECG; the analysed cohort is 38–100% of it). See §6 |
| Imputation model | `build_core_baseline.impute(observed without lvef, treated, m = 5)`: IterativeImputer(`sample_posterior=True`, `max_iter=10`, `random_state=20260923 + k − 1`, `skip_complete=True`); all other covariates + treatment as predictors; clipped to plausible ranges; observed values kept (asserted in all 38 × 5 tables). LVEF is neither imputed nor a predictor |
| PS | the version 1 `clinical_nolvef` design (core covariates minus `lvef`), L2 C = 1, `E.run_cell(..., cstat=None)` |
| Arms | base, + ECG (32 PCs), + permuted ECG; also + CLMBR-T (64 PCs), + CLMBR-T + ECG, + permuted CLMBR-T and + CLMBR-T 32 PCs (main only). CLMBR-T arms are kept in the record but are **not in the paper** |
| Representations | PCs within the fixed cohort (`pcs(ecg_raw[rows], 64)[:, :32]`; CLMBR-T 64), placebo = `default_rng(424242).permutation(len(rows))` (pipeline.md §3) |
| Configurations | main (1:1, caliper 0.2), cal01, m13 (1:3), iptw, overlap, gbm |
| Masks | pipeline.md §6 leakage-corrected: PS-Clinical (no LVEF) masks the 8 observed vitals/labs that are PS inputs (`smd_obs_*`, not LVEF), eGFR and the 4 coded items; + CLMBR-T arms: the 4 coded items. 45 of the 54 items stay held out (incl. observed LVEF and all 35 echo items). Other rungs: as `scripts/v2_cohorts/summarize.py` |
| F1 | a cell with < 11 matched pairs or a failed fit is failed. An MI cell is failed if any of its 5 draws failed. **No PS-Clinical (no LVEF) cell failed** in any draw |

**Combination (per trial × configuration × arm).**
- **Balance:** |SMD| of each item averaged over the 5 draws (an item unobserved in a draw contributes from the other draws), then the endpoints of pipeline.md §6: relative reduction in mean |SMD| with a 4,000-resample trial bootstrap (seed 20261001), exact sign-flip P (one-sided for a representation vs its base or placebo; two-sided for placebos vs base and head-to-heads), % |SMD| < 0.1, per-domain relative reductions.
- **HRs:** Rubin's rules: log HR = mean of the 5 log HRs; total variance T = W̄ + (1 + 1/5) B, with W̄ the mean squared robust SE and B the between-draw variance. |Δ log HR| vs the RCT, sign-flip P and the benchmark-permutation P (20,000 draws) use the combined log HR; estimate agreement and the standardised-difference agreement use √T.

## 2. Gate (version 1 cohorts, draw 1)

`psclin_mi.py impute --cohort v1` re-ran the imputation on the full baseline roster: draw 1 equals the version 1 re-imputed table (`claude-v1-psclin-nolvef/imputation/`) in 38/38 trials (asserted, exact).

`psclin_mi.py run --cohort v1` + `gate` compared every `clinical_nolvef` cell with `audits/claude-v1-psclin-nolvef/cells/restricted_cells.parquet`:

| Check | Result |
|---|---|
| Scope | 6 configurations × 7 arms (incl. CLMBR-T 32 PCs, main) × 38 trials = 1,406 cells |
| Columns | log HR, SE, n, n_t, n_c, n_pairs, ESS, retention, PS dimension, RCT benchmark, 58 SMDs; key / ex58 / cell_failed |
| Values compared | 98,420 |
| Result | **PASS: maximum deviation 0, 0 NaN mismatches, 0 string mismatches** (`cells/gate_status.json`, 14:13) |

**First attempt failed, and why (kept for the record: `logs/gate.log`).**
- Only the PS-alone arm differed: gbm up to 0.040 on one SMD and 2e-3 on one log HR (AMPLIFY); iptw and overlap at round-off (2e-11). Every arm with PCs matched exactly, so the imputed values were identical.
- **Cause: memory layout.** Version 1 passed a row-indexed copy `Xre[r]` (C-ordered). This code passed the Fortran-ordered block that pandas returns. Without an `hstack` partner, the base-arm design keeps that layout. The gradient-boosted PS (tie-breaking) and lbfgs (round-off) are sensitive to it.
- Fixed by indexing the same way as version 1.
- **Lesson for any re-implementation:** gbm cells are reproducible only when the design matrix has the same memory layout.

## 3. Results, main configuration

Leakage-corrected masks; 45 items held out for this rung. Relative reduction = 100 × (1 − mean over trials of the arm's mean |SMD| / same for PS alone).

| Set | Contrast | mean \|SMD\| | rel. reduction (95% CI) | better | P | q (rung family) | % \|SMD\| < 0.1 (P) | \|Δ log HR\| (closer; P; perm. P) |
|---|---|---|---|---|---|---|---|---|
| S29 | + ECG vs PS alone | 0.115 → 0.110 | **4.4% (0.9 to 8.0)** | 19/29 | .009 | .07 | 59.4 → 63.1 (.011) | 0.155 → 0.153 (17/29; .43; .44) |
| S29 | + permuted ECG vs PS alone | 0.115 → 0.117 | −1.7% (−3.1 to −0.3) | 9/29 | .026 (two-sided) | .10 | 59.4 → 59.0 | |
| S29 | ECG vs permuted ECG | 0.117 → 0.110 | 6.0% (2.9 to 9.3) | 22/29 | <.001 | .02 | | |
| S32 | + ECG vs PS alone | 0.126 → 0.123 | 2.4% (−1.8 to 6.5) | 20/32 | .13 | .29 | 54.9 → 57.5 (.07) | 0.176 → 0.176 (18/32; .50; .32) |
| S32 | + permuted ECG vs PS alone | 0.126 → 0.131 | −3.4% (−6.8 to −0.9) | 8/32 | .005 (two-sided) | .06 | | |
| S32 | ECG vs permuted ECG | | 5.7% (2.9 to 8.6) | 24/32 | <.001 | .02 | | |
| S38 | + ECG vs PS alone | 0.119 → 0.115 | 3.0% (−0.8 to 6.9) | 25/38 | .06 | .15 | 57.6 → 60.3 (.03) | 0.178 → 0.177 (23/38; .45; .28) |
| S38 | + permuted ECG vs PS alone | | −3.1% (−6.1 to −0.8) | 11/38 | .006 (two-sided) | .04 | | |
| S38 | ECG vs permuted ECG | | 5.9% (3.3 to 8.7) | 29/38 | <.001 | .003 | | |

**CLMBR-T rows (record only; not in the paper), S29 main:**
- + CLMBR-T: 1.7% (−3.4 to 6.6), P .28;
- + CLMBR-T + ECG: 5.5% (0.6 to 11.1), P .02;
- + CLMBR-T + ECG vs + CLMBR-T: 3.9% (0.9 to 6.9), P .009;
- + CLMBR-T vs permuted CLMBR-T: 4.6% (0.1 to 8.9).

**Ladder comparisons (PS alone, S29, main):**
- PS-Clinical (no LVEF, MI) vs PS-CVD5: 6.3% (3.1 to 9.9), 22/29, two-sided P < .001;
- vs hdPS: 2.1% (−7.9 to 10.8), P .70.
- PS-CVD5 + ECG vs PS-Clinical (no LVEF, MI) alone: 1.0% (−2.5 to 5.0), P .61. The ECG on top of PS-CVD5 roughly matches the clinical PS.

**Rescored sets** (added after step D, `docs/emulation_quality_v2/RESCORE_V2_COHORTS.md`; `summarize` re-run, sets `Snew` and `SEG`), main configuration:

| Set | + ECG vs PS alone | ECG vs permuted ECG | draws 1–5 range |
|---|---|---|---|
| New analysed set (30) | 4.5% (1.2 to 7.9); 20/30; P = .006 | 5.9% (3.0 to 9.0); P < .001 | 2.4 to 5.7 |
| Excellent + Good (12) | 4.1% (−1.5 to 9.7); 7/12; P = .09 | 4.7% (0.4 to 9.3); P = .03 | 0.7 to 8.6 |

## 4. All configurations (+ ECG vs PS alone; 54 items)

| config | S29 | S32 | S38 |
|---|---|---|---|
| main | 4.4% (0.9 to 8.0); 19/29; .009 | 2.4% (−1.8 to 6.5); 20/32; .13 | 3.0% (−0.8 to 6.9); 25/38; .06 |
| cal01 | 4.7% (0.9 to 8.5); 18/29; .011 | 3.1% (−1.5 to 7.5); 19/32; .09 | 3.3% (−0.9 to 7.3); 24/38; .06 |
| m13 | 3.8% (0.4 to 7.5); 21/29; .018 | 3.2% (0.3 to 6.4); 22/32; .020 | 3.5% (0.8 to 6.4); 28/38; .006 |
| iptw | 2.8% (−0.9 to 6.8); 16/29; .08 | −0.6% (−5.1 to 3.8); 16/32; .59 | 0.3% (−3.9 to 4.3); 21/38; .45 |
| overlap | 4.6% (1.0 to 8.9); 20/29; .012 | 3.6% (0.2 to 7.6); 21/32; .029 | 4.2% (1.0 to 7.6); 26/38; .008 |
| gbm | 1.3% (−0.6 to 3.2); 18/29; .09 | 0.9% (−1.5 to 3.0); 21/32; .24 | 1.1% (−1.5 to 3.5); 24/38; .20 |

ECG vs permuted ECG is positive in every configuration and set: 1.1% to 6.0%, P ≤ .05 in 14 of 18 cells. On observed LVEF (the one unmasked vitals/labs item), the gain is 5.9–26.4% across methods and sets. It reaches P < .01 under 1:3 matching and overlap weighting in all three sets (`summary/domains.csv`).

## 5. Draws and Rubin's rules

| Set | main contrast (+ ECG vs PS alone, 54 items) by draw 1 / 2 / 3 / 4 / 5 | MI (averaged \|SMD\|) |
|---|---|---|
| S29 | 4.4 / 4.9 / 1.7 / 5.6 / 5.4 | 4.4 (0.9 to 8.0) |
| S32 | 0.0 / 1.1 / 2.8 / 3.8 / 4.4 | 2.4 (−1.8 to 6.5) |
| S38 | 0.7 / 2.7 / 3.3 / 3.8 / 4.6 | 3.0 (−0.8 to 6.9) |

**Between-draw share of the Rubin total variance** (median over 38 trials; `summary/rubin_diagnostics.csv`):
- matching (main 0.15–0.23; cal01 0.19–0.27): the combined SE is about 8–17% larger than the mean within-draw SE (maximum 1.5×);
- 1:3 matching about 0.08;
- IPTW about 0.04;
- overlap weighting under 0.01.

So most of the imputation noise enters through which patients get matched.

**Single-draw comparisons (S29, main, ECG vs PS alone):**
- draw 1 within the fixed cohort: 4.4%;
- version 1 imputation reused on the spec-v2 rows (the `scripts/v2_cohorts` `clinical_nolvef` cells): 1.7% (−5.8 to 8.7).

The difference is of the same size as the draw-to-draw spread.

## 6. Notes and limitations

- **Imputation population.** The queue asked for re-imputation "within the fixed cohort". This code imputes on the fixed analysed cohort only. Version 1 imputed on the larger pre-ECG baseline roster. So even for the 6 trials whose spec-v2 cohort equals the version 1 cohort, draw 1 differs from the version 1 cells. A roster-wide imputation, with the dropped patients removed afterwards, would be the alternative. Listed as a decision for the user.
- **Averaging |SMD| across draws** is the queue's specification. It is not Rubin's rules for the SMD. The mean of |SMD| over draws is slightly larger than |mean SMD| when draws disagree in sign, so it is mildly conservative for balance.
- **Treatment as an imputation predictor** (as version 1): it is kept for compatibility. It makes imputed values depend on arm, which is standard for PS analyses but should be stated.
- **Residual LVEF information** via HF diagnoses, MRA/loop-diuretic orders and use is intended (not echo measurements).
- **Not changed:** C = 1 (pipeline.md §8). No "was measured" flags were added (pipeline.md §10.3, open).

## 7. Files

- **Repository:** `scripts/v2_psclin_mi/psclin_mi.py`, this document.
- **Audits** (`/mnt/raid0/rbc58/ecg-tte/audits/claude-v2-psclin-mi/`):
  - `imputation/`: restricted completed tables (v1 draw 1; v2 draws 1–5) and `imputation_log_*.json`;
  - `cells/`:
    - `restricted_cells_v1.parquet` (gate);
    - `restricted_cells_v2.parquet` (7,030 per-draw cells);
    - `restricted_cells_v2_mi.parquet` (1,406 MI cells) and the suppressed `cells_v2_mi.csv`;
    - `gate.csv`, `gate_status.json`;
  - `summary/`: `contrasts.csv`, `domains.csv`, `ladder.csv`, `per_trial.csv`, `rubin_diagnostics.csv`, `failed_cells.csv`;
  - `privacy_scan.json`: clean (no count 1–10 in any count column; no identifier columns or keys);
  - `logs/`.
