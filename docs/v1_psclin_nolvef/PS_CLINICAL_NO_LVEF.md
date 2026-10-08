# PS-Clinical without LVEF (TRACE-ECG version 1 grid)

Written 2026-10-08. This follows the user decision of 2026-10-08: no propensity score (PS) may use an echocardiographic measurement. All 35 echo items and the observed-LVEF item are therefore held out for every PS.

- Code: `scripts/v1_psclin_nolvef/` (`psclin_nolvef.py`, `imputation_draws.py`, `make_tables.py`, `explorer_headless_check.py`). Version 1 code is imported unchanged.
- Outputs (restricted folder, umask 077): `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-psclin-nolvef/`. The full tables are in `summary/tables.md`.
- This document reports aggregates only: trial counts, means, CIs and P values. It contains no patient counts.

## Plain-language summary

- **What changed.** The richest PS, "PS-Clinical", used to include the patient's last LVEF. We removed LVEF and re-imputed the other clinical covariates without it, so the imputation model never saw LVEF. The new PS ("PS-Clinical (no LVEF)") still has demographics, the 8 other vital signs and labs, diagnoses, medications and healthcare use. Every echo measurement and the observed LVEF are now outcomes of balance, not inputs.
- **Gate.** The code reproduces every existing PS-Clinical cell of the paper 2 grid exactly: 1,368 cells, 95,760 values, maximum deviation 0.
- **The ECG on top of the no-LVEF PS** (paper 1 trial set, primary 1:1 matching).
  - The ECG lowers mean imbalance by **4.5% (95% CI −2.9 to 10.9)**: 19 of 32 trials better, P = .11.
  - The 45 held-out characteristics left after masking are the same on the 58-item and the 54-item panels, so both give 4.5%. With paper 1's own masking rule, the 58-item figure is 4.2% (−3.1 to 10.5).
  - This compares with **−1.2% (−6.5 to 3.9)** for the old PS-Clinical with LVEF (paper 1 eTable 3, reproduced exactly).
  - Across all 38 trials: 5.3% (−1.3 to 11.2), P = .06.
  - The ECG clearly beats a permuted ECG: 8.7% (3.2 to 14.0), P = .003.
  - The gain is clearer with overlap weighting (5.5%, P = .001) and the gradient-boosted PS (11.3%, P < .001).
- **Where the ECG helps.** The gains are in the characteristics that the no-LVEF PS can no longer see:
  - observed LVEF 13.6%;
  - echo EF 12.1%;
  - LV systolic grade 14.1%;
  - diastolic/LA domain 12.2% (0.3 to 23.2);
  - all 35 echo items 4.7%.

  None of these CIs excludes 0 in the main configuration, except diastolic/LA.
- **CLMBR-T adds little:** 1.5% (−6.8 to 9.0). CLMBR-T + ECG gives 4.0% (−4.1 to 11.4).
- **What LVEF itself bought.** On the 42 characteristics held out under both PSs, adding LVEF to the PS improved balance by 3.1% (−3.3 to 9.4; P = .35). The improvement was clearer under 1:3 matching, overlap weighting and the boosted PS (4.0–8.1%).
- **Imputation caveat.** The covariates are imputed once, with a random draw. Across 5 imputation draws, the ECG gain ranges from −1.8% to 6.0% without LVEF (average-draw analysis 3.3%, −0.9 to 7.3), and from −1.7% to 2.1% with LVEF (1.1%). The old −1.2% / −1.7% came from the least favourable of the 5 draws.
- **Bottom line.** Without LVEF in the PS, the ECG recovers a small, imprecise gain at the richest PS level, concentrated in the LVEF and echo characteristics the PS no longer contains. It does not reach significance in the primary configuration. The "nothing adds to PS-Clinical" finding of paper 1 and paper 2 was partly an artefact of LVEF being in the PS.

## 1. What changed and why

**Before (version 1).** PS-Clinical (rung `clinical`) = `T.X_core`, all core covariates of the trial's `roles.json` after single imputation (imputation 1). It included `lvef`, the latest echo EF in [index − 365, index − 1] (`scripts/build_core_baseline.py`). Its held-out masking was `{mean_meds, mean_util} | {smd_obs_<c> for c in T.phys}`, which includes `smd_obs_lvef`.

**Two problems with that design:**
- **A PS input that is itself an echo measurement.** Echo EF (ρ = 1.00 with LVEF) and LV systolic grade (median |ρ| 0.91–0.93) were held-out "outcomes" that the PS controlled directly. DEFECT_IMPACT §1 masked them as leakage; the R2 pooled correlations (`audits/claude-r2/leakage/r4_pooled.csv`, scenario S3) agree.
- **Through the imputation.** LVEF was missing in 25–90% of patients (median 76% across the 38 trials). The imputed LVEF and the imputed values of the other 8 vitals and labs came from a model that used LVEF as a predictor.

**After (user decision 2026-10-08).** The new rung `clinical_nolvef` drops LVEF from the PS and re-imputes without it. The echo panel (35 items) and observed LVEF become ordinary held-out characteristics.

**Without LVEF, the largest remaining R2 pooled correlation** of any echo item with any PS-Clinical input is:
- aortic root ~ male, 0.55;
- the next is GLS ~ heart failure, 0.42.

Both are below the ρ ≥ 0.80 R2 masking rule, so no echo item is masked.

**Everything else is identical to the v21 grid:**
- arms: base, + ECG (32 PCs), + CLMBR-T (64 PCs), + CLMBR-T + ECG, + permuted ECG, + permuted CLMBR-T, plus + CLMBR-T 32 PCs in the main configuration;
- configurations: main (1:1, caliper 0.2), cal01, m13 (1:3), iptw, overlap, gbm;
- the 38 trials;
- `E.run_cell(..., cstat=None)`;
- L2 penalty C = 1.

## 2. Imputation (choice: re-imputation, primary; column drop, sensitivity)

**Baseline imputation step.** `scripts/build_core_baseline.impute`, run once per trial when the baseline was built (`audits/claude-<trial>-baseline-v11/`, 5 imputations; the grid uses imputation 1):
- `IterativeImputer(sample_posterior=True, max_iter=10, random_state=20260923 + i, skip_complete=True)`;
- **all covariates, including LVEF, plus the treatment indicator** are predictors;
- imputed values are clipped to plausible ranges, and observed values are kept.

So LVEF was both imputed and a predictor of every other imputed covariate.

**Feasibility check (in `psclin_nolvef.py impute`).** I re-ran the same function on `restricted_baseline_observed.parquet` with LVEF included:
- it reproduced `restricted_completed_01.parquet` exactly in 30 trials;
- in the 8 largest it matched to ≤ 4.1e-12, which is float round-off;
- there were 0 missingness mismatches.

The whole step took 84 CPU-seconds, so re-imputation was clearly feasible.

**Primary (`clinical_nolvef`).**
- Ran `impute(observed without the lvef column, treated, m = 1)`: same seed (20260923), same settings, imputation 1.
- LVEF is neither imputed nor used as a predictor.
- Observed values are preserved in all 38 trials.
- The medication and utilisation columns have no missing values, so they are unchanged (asserted); the held-out medication and use components are untouched.

**Sensitivity (`clinical_nolvef_drop`).** The `lvef` column was dropped from the existing completed table. The other imputed values still carry LVEF as a predictor: this is the residual indirect channel.

**How much the imputed values moved.** Among imputed cells, the re-imputed values differ from the original by about 1 observed SD on average (median 0.85–1.12 SD by covariate; `imputation/imputation_change.csv`). This is mostly a new posterior draw (`sample_posterior=True`): changing the column set changes the random stream. It is not a systematic shift. Section 7 therefore adds a 5-draw check.

## 3. Masks (final list)

A cell's mask is rung mask ∪ arm mask; permuted arms take the real arm's mask. Two variants were computed throughout.

**Primary: "clean"** (DEFECT_IMPACT §1 rules, minus the LVEF-derived items). For PS-Clinical (no LVEF) the masked items are:

| Item | Why masked |
|---|---|
| `mean_meds`, `mean_util` | PS inputs (medication-order flags, utilisation counts) |
| `smd_obs_sbp`, `smd_obs_dbp`, `smd_obs_heart_rate`, `smd_obs_bmi`, `smd_obs_creatinine`, `smd_obs_potassium`, `smd_obs_sodium`, `smd_obs_hemoglobin` | PS inputs (8 observed vitals and labs) |
| `pp_LAB__egfr` | derived from PS creatinine, age and sex (CKD-EPI; median ρ 0.83) |
| `B_mean`, `smd_prog_full` | DEFECT_IMPACT lists all 4 coded-record items for PS-Clinical: held-out codes overlap the PS diagnoses, and the prognostic score is a linear predictor of the core covariates |

- **Held out (no longer masked):** `smd_obs_lvef`, `pp_LVFUNC__ef`, `pp_LVFUNC__lv_sys_grade`, and all 35 echo items.
- **Held-out set:** 45 items. They are the same on the 58-item and the 54-item panels, because all 4 coded items are masked. "58-item" and "54-item" results for this rung are therefore identical.
- **CLMBR-T arm mask:** the 4 coded items, already inside the rung mask.
- **Other rungs (clean):**
  - PS-Demo: none;
  - PS-CVD5 and PS-Flags: `B_mean`, `smd_prog_full`;
  - hdPS: the 4 coded items;
  - PS-Clinical (with LVEF): the 4 coded items + 9 `smd_obs_*` + eGFR + echo EF + LV systolic grade (42 items remain).

**Secondary: "v1"** (paper 1 / paper 2 rule: only items that are themselves PS inputs). For the new rung this masks `mean_meds`, `mean_util` and the 8 `smd_obs_*`, leaving 48 items on the 58 panel and 46 on the 54 panel. This is the cells' `ex58` and the explorer's "leakage-corrected masking: off".

**F1 rule.** A cell with fewer than 11 matched pairs, or a failed fit, is treated as failed: all items and the log HR are missing. No PS-Clinical cell, with or without LVEF, failed. The failed cells are 18 PS-Flags cells (one trial) and 4 hdPS cells (`summary/failed_cells.csv`).

## 4. Gate

`psclin_nolvef.py gate` compared the `clinical` rung (with LVEF) recomputed by this code with `audits/claude-v21-paper2/core/restricted_cells.parquet`.

| Check | Result |
|---|---|
| Scope | 6 arms × 6 configurations × 38 trials = 1,368 cells |
| Columns compared | log HR, SE, n, n_t, n_c, n_pairs, ESS, retention, PS dimension, RCT benchmark, 58 SMDs, plus key / ex58 / cell_failed |
| Values compared | 95,760 |
| Result | **PASS: max deviation 0, 0 NaN mismatches, 0 string mismatches** (`cells/gate_status.json`) |

**Further checks:**
- **Summary pipeline.** The paper 1 eTable 3 value for PS-Clinical + ECG (58 items, v1 masking, S32, main) came out at −1.2% (−6.5 to 3.9). The leakage-clean DEFECT_IMPACT values came out at −1.7% (+ ECG) and +1.5% (+ CLMBR-T), and the ladder rungs at 11.3 / 8.8 / 7.6%, as published.
- **Imputation-draw check.** Draw 1 equals the main cells (max deviation 0).

## 5. Results (paper 1 set S32 unless stated; leakage-clean masking; 54 items = 58 items for this rung)

Reading the tables:
- Relative reduction = 100 × (1 − mean over trials of the arm's mean |SMD| / same for PS alone). The CI comes from 4,000 trial bootstrap resamples, seed 20261001.
- "Better" = trials with lower mean |SMD|.
- P = exact sign-flip test: one-sided for real arms, two-sided for permuted arms.
- |Δ log HR| = mean absolute difference from the RCT log HR. Permutation P = within-set benchmark permutation, 20,000 draws.
- q = BH within this rung's family: 10 within-rung contrasts × 6 configurations × 4 balance endpoints, per set.

### 5.1 Headline (main configuration)

**S32 (32 trials):**

| Arm vs PS alone | mean \|SMD\| | rel. reduction (95% CI) | better | P | q | % \|SMD\| < 0.1 (P) | \|Δ log HR\| (closer; P; perm. P) |
|---|---|---|---|---|---|---|---|
| + ECG | 0.117 → 0.112 | **4.5% (−2.9 to 10.9)** | 19/32 | .11 | .31 | 59.0 → 60.0 (.30) | 0.150 → 0.153 (14/32; .63; .15) |
| + permuted ECG | 0.117 → 0.123 | −4.6% (−11.1 to 1.2) | 13/32 | .15 | .35 | 59.0 → 56.1 (.05) | 0.150 → 0.167 (14/32; .18; .24) |
| + CLMBR-T | 0.117 → 0.115 | 1.5% (−6.8 to 9.0) | 20/32 | .36 | .52 | 59.0 → 60.1 (.28) | 0.150 → 0.144 (20/32; .37; .77) |
| + CLMBR-T + ECG | 0.117 → 0.112 | 4.0% (−4.1 to 11.4) | 20/32 | .16 | .35 | 58.9 → 59.7 (.33) | 0.150 → 0.142 (21/32; .37; .85) |
| + permuted CLMBR-T | 0.117 → 0.118 | −1.6% (−6.1 to 2.8) | 14/32 | .48 | .62 | 59.0 → 57.8 (.38) | 0.150 → 0.158 (13/32; .53; .53) |
| ECG vs permuted ECG | | 8.7% (3.2 to 14.0) | 23/32 | .003 | .049 | | |
| CLMBR-T vs permuted CLMBR-T | | 2.9% (−4.0 to 9.1) | 22/32 | .20 | .41 | | |
| CLMBR-T vs ECG (two-sided) | | −3.1% (−10.4 to 3.9) | 12/32 | .41 | | | |
| + CLMBR-T (32 PCs) | 0.117 → 0.119 | −1.3% (−9.6 to 5.6) | 16/32 | .61 | | | |

**S38 (all 38 trials):**

| Arm vs PS alone | rel. reduction (95% CI) | better | P | q | \|Δ log HR\| (closer; P; perm. P) |
|---|---|---|---|---|---|
| + ECG | 5.3% (−1.3 to 11.2) | 24/38 | .06 | .17 | 0.150 → 0.149 (18/38; .46; .10) |
| + permuted ECG | −3.5% (−9.3 to 1.7) | 18/38 | .23 | .37 | 0.150 → 0.169 |
| + CLMBR-T | 2.2% (−5.0 to 8.9) | 25/38 | .28 | .42 | 0.150 → 0.144 (24/38; .35; .78) |
| + CLMBR-T + ECG | 5.6% (−1.5 to 12.7) | 25/38 | .07 | .19 | 0.150 → 0.140 (25/38; .30; .84) |
| + permuted CLMBR-T | −0.9% (−5.1 to 2.9) | 17/38 | .65 | .75 | |
| ECG vs permuted ECG | 8.5% (3.3 to 13.2) | 27/38 | .002 | .021 | |
| + CLMBR-T (32 PCs) | −0.7% (−8.1 to 5.5) | 19/38 | .57 | | |

**Against the old PS-Clinical (with LVEF), same trials and configuration:**

| PS base | Masking | + ECG | + CLMBR-T | + both |
|---|---|---|---|---|
| with LVEF | v1, 58 items (paper 1 eTable 3) | −1.2% (−6.5 to 3.9), P .67 | 1.0% | 0.1% |
| with LVEF | clean, 54 items (DEFECT_IMPACT) | −1.7% (−7.6 to 3.9), P .71 | 1.5% (−2.9 to 6.3) | −0.5% |
| **no LVEF** | **clean, 45 items** | **4.5% (−2.9 to 10.9), P .11** | 1.5% (−6.8 to 9.0) | 4.0% (−4.1 to 11.4) |
| no LVEF | v1, 58 items (48 held out) | 4.2% (−3.1 to 10.5), P .12 | 1.6% (−6.3 to 9.0) | 4.2% (−3.7 to 11.2) |
| no LVEF | v1, 54 items (46 held out) | 4.4% (−3.1 to 10.8) | 1.5% | 4.0% |

### 5.2 All six configurations (relative reduction vs PS alone; better; P)

**S32:**

| config | + ECG | + permuted ECG | + CLMBR-T | + CLMBR-T + ECG | + permuted CLMBR-T |
|---|---|---|---|---|---|
| main | 4.5% (−2.9 to 10.9); 19/32; .11 | −4.6% (−11.1 to 1.2); 13/32; .15 | 1.5% (−6.8 to 9.0); 20/32; .36 | 4.0% (−4.1 to 11.4); 20/32; .16 | −1.6% (−6.1 to 2.8); 14/32; .48 |
| cal01 | 5.8% (−1.2 to 12.1); 21/32; .05 | −1.9% (−8.2 to 3.9); 17/32; .55 | 2.5% (−5.0 to 9.3); 19/32; .25 | 4.1% (−3.8 to 11.7); 20/32; .16 | −0.0% (−4.6 to 4.5); 16/32; 1.00 |
| m13 | 5.1% (0.7 to 9.4); 19/32; .02 | 1.2% (−1.2 to 3.5); 17/32; .34 | 2.7% (−3.9 to 8.5); 20/32; .22 | 6.8% (1.2 to 12.2); 19/32; .01 | −0.1% (−3.0 to 2.5); 17/32; .95 |
| iptw | 0.6% (−5.4 to 6.3); 20/32; .43 | −1.9% (−5.2 to 1.0); 12/32; .29 | −8.0% (−28.5 to 4.4); 16/32; .71 | −11.5% (−39.9 to 7.3); 17/32; .75 | −2.4% (−4.9 to −0.1); 14/32; .07 |
| overlap | 5.5% (2.1 to 9.3); 23/32; .001 (q .028) | −0.8% (−1.4 to −0.2); 12/32; .02 | 4.2% (−0.5 to 8.8); 19/32; .04 | 6.2% (1.1 to 12.1); 21/32; .01 | −0.7% (−1.6 to 0.3); 11/32; .21 |
| gbm | 11.3% (6.4 to 16.3); 24/32; <.001 (q .004) | −0.1% (−4.7 to 4.2); 17/32; .98 | 2.5% (−2.1 to 7.2); 19/32; .15 | 6.3% (0.6 to 12.0); 23/32; .02 | −0.8% (−4.7 to 3.7); 14/32; .71 |

**S38:**

| config | + ECG | + permuted ECG | + CLMBR-T | + CLMBR-T + ECG | + permuted CLMBR-T |
|---|---|---|---|---|---|
| main | 5.3% (−1.3 to 11.2); 24/38; .06 | −3.5% (−9.3 to 1.7); 18/38; .23 | 2.2% (−5.0 to 8.9); 25/38; .28 | 5.6% (−1.5 to 12.7); 25/38; .07 | −0.9% (−5.1 to 2.9); 17/38; .65 |
| cal01 | 7.0% (0.7 to 12.9); 27/38; .02 | −1.1% (−6.7 to 4.3); 22/38; .71 | 3.1% (−3.3 to 9.4); 22/38; .18 | 5.1% (−2.0 to 12.0); 25/38; .09 | −0.3% (−4.2 to 3.8); 18/38; .90 |
| m13 | 5.6% (1.6 to 9.5); 24/38; .005 (q .030) | 1.2% (−0.9 to 3.3); 20/38; .28 | 3.0% (−3.0 to 8.3); 25/38; .16 | 7.8% (2.8 to 12.8); 24/38; .003 (q .025) | 0.0% (−2.7 to 2.5); 19/38; 1.00 |
| iptw | 1.1% (−4.3 to 6.2); 25/38; .35 | −1.6% (−4.6 to 1.1); 15/38; .33 | −7.2% (−25.4 to 3.8); 19/38; .71 | −9.8% (−35.0 to 6.9); 22/38; .72 | −2.2% (−4.5 to −0.1); 17/38; .06 |
| overlap | 6.0% (2.9 to 9.3); 28/38; <.001 (q .003) | −0.8% (−1.3 to −0.2); 13/38; .008 | 4.4% (0.3 to 8.5); 24/38; .02 | 7.0% (2.2 to 12.1); 26/38; .003 (q .025) | −0.5% (−1.4 to 0.4); 14/38; .29 |
| gbm | 11.3% (6.9 to 15.5); 29/38; <.001 (q .001) | 0.5% (−3.9 to 4.3); 21/38; .84 | 3.4% (−1.0 to 7.7); 23/38; .07 | 7.3% (2.1 to 12.2); 29/38; .005 (q .030) | 0.2% (−3.8 to 4.6); 17/38; .92 |

**Reading:**
- **With LVEF** (old rung, clean, S32), + ECG ranged from −4.4% (IPTW) to 2.1% (overlap); main −1.7%, gbm −3.8%. Without LVEF it ranges from 0.6% to 11.3%.
- **IPTW.** CLMBR-T loses under IPTW here too. This is the same weight instability as in the v1 audit, defect 4.
- **Rows reaching q < .05 in this rung's family:**
  - S32: 6 rows (overlap and gbm ECG vs base, ECG vs permuted ECG in main / overlap / gbm, gbm CLMBR-T vs ECG);
  - S38: 13 rows.

### 5.3 RCT agreement (|Δ log HR| vs RCT, S32; base → arm; trials closer; P; permutation P)

| config | + ECG | + permuted ECG | + CLMBR-T | + CLMBR-T + ECG |
|---|---|---|---|---|
| main | 0.150 → 0.153; 14/32; .63; .15 | 0.150 → 0.167; 14/32; .18; .24 | 0.150 → 0.144; 20/32; .37; .77 | 0.150 → 0.142; 21/32; .37; .85 |
| cal01 | 0.157 → 0.160; 16/32; .61; .59 | 0.157 → 0.156; .98 | 0.157 → 0.139; 15/32; .17; .59 | 0.157 → 0.146; 18/32; .33; .89 |
| m13 | 0.159 → 0.157; 17/32; .44; .81 | 0.159 → 0.170; .04 | 0.159 → 0.152; 18/32; .32; .91 | 0.159 → 0.145; 16/32; .21; .86 |
| iptw | 0.209 → 0.212; 15/32; .63; .53 | 0.209 → 0.205; .48 | 0.209 → 0.247; 16/32; .69; .46 | 0.209 → 0.278; 19/32; .68; .58 |
| overlap | 0.162 → 0.157; 19/32; .20; .34 | 0.162 → 0.161; .70 | 0.162 → 0.152; 17/32; .29; .77 | 0.162 → 0.145; 17/32; .16; .57 |
| gbm | 0.181 → 0.156; 20/32; .04; .05 | 0.181 → 0.163; .23 | 0.181 → 0.171; 16/32; .29; .83 | 0.181 → 0.179; 15/32; .46; .85 |

- No arm moves the estimates closer to the RCTs in a trial-specific way: every permutation P is ≥ .05. The lowest is ECG with the gbm PS (.05), which is also the only nominal |Δ log HR| gain (P .04).
- Dropping LVEF from PS-Clinical did not itself worsen agreement: PS alone 0.158 with LVEF vs 0.150 without (main, S32; P .56).

### 5.4 Domains (main configuration; PS alone → + arm; relative reduction; better; P)

**S32:**

| Domain (items held out) | + ECG | + CLMBR-T | + CLMBR-T + ECG | + permuted ECG |
|---|---|---|---|---|
| Observed LVEF (1; the only unmasked "vitals & core labs" item) | 0.109 → 0.094; 13.6% (−11.9 to 30.8); 18/32; .13 | 8.8% (−16.8 to 30.4); .26 | 2.6%; .43 | −24.8% (−56.1 to −3.5); .04 |
| Echo EF (1) | 0.108 → 0.095; 12.1% (−13.8 to 29.1); 17/32; .16 | 8.5%; .28 | 1.3%; .47 | −24.9%; .04 |
| LV systolic grade (1) | 0.148 → 0.127; 14.1% (−11.4 to 35.2); 20/32; .14 | 2.8%; .39 | 7.8%; .22 | −8.6%; .46 |
| LVEF-derived, 3 items | 0.121 → 0.105; 13.3% (−10.2 to 29.8); 18/32; .13 | 6.3%; .28 | 4.4%; .36 | −18.3%; .11 |
| Echo: LV structure (7) | 0.108 → 0.101; 6.2% (−6.7 to 15.8); .16 | 6.6% (−5.4 to 16.5); .15 | 8.3%; .12 | −3.8%; .47 |
| Echo: LV function (4) | 0.171 → 0.159; 6.9% (−16.4 to 25.3); .28 | −5.8%; .68 | 5.0%; .34 | −11.8%; .29 |
| Echo: diastolic / LA (8) | 0.117 → 0.102; **12.2% (0.3 to 23.2)**; 18/32; .03 | 5.1%; .15 | 10.0% (−1.4 to 20.2); .05 | −1.5%; .73 |
| Echo: RV / pulmonary (7) | 2.8% (−4.5 to 10.2); .24 | −0.6%; .54 | 2.4%; .34 | −7.4%; .26 |
| Echo: valves / aorta (9) | −1.3% (−12.9 to 7.8); .59 | 1.9%; .39 | −0.3%; .52 | −1.4%; .75 |
| **All 35 echo items** | 0.128 → 0.122; 4.7% (−3.7 to 11.9); 20/32; .13 | 1.7% (−7.6 to 9.5); .36 | 4.5% (−4.2 to 12.4); .15 | −4.5% (−11.2 to 1.5); .18 |
| Other labs (9; eGFR masked) | 1.6% (−8.3 to 10.1); .38 | −0.6%; .51 | 1.2%; .43 | −2.0%; .70 |

**S38:**
- observed LVEF 14.6% (−3.6 to 28.4), P .06;
- echo EF 13.3%;
- LV systolic grade 14.8%;
- diastolic/LA 12.8% (1.7 to 22.9), P .02;
- all 35 echo items 5.6% (−2.1 to 12.2), P .08;
- CLMBR-T + ECG on diastolic/LA 11.0% (0.9 to 20.4).

**Other configurations** (S32, ECG, LVEF-derived 3 items):
- cal01 18.6% (−2.3 to 34.6);
- 1:3 matching (m13) 17.9% on observed LVEF (6.9 to 28.0; P .004).

For comparison, with LVEF in the PS (clean, S32), ECG on all 35 echo items was −1.3% (−7.3 to 4.9). The full per-configuration domain tables are in `summary/tables.md`.

### 5.5 What LVEF bought (PS-Clinical with LVEF vs without, PS alone)

**Paired on the 42 items held out under both PSs** (clean masking: the union of the masks, so the LVEF-derived items are excluded). Relative reduction > 0 means better balance with LVEF; two-sided P.

| config | mean \|SMD\| no LVEF → with LVEF | S32 rel. reduction (95% CI); better; P | S38 rel. reduction (95% CI); better; P |
|---|---|---|---|
| main | 0.117 → 0.113 | 3.1% (−3.3 to 9.4); 17/32; .35 | 4.0% (−2.1 to 10.0); 22/38; .22 |
| cal01 | 0.119 → 0.114 | 4.0% (−1.7 to 9.4); 21/32; .17 | 5.0% (−0.3 to 10.3); 24/38; .09 |
| m13 | 0.112 → 0.105 | 6.0% (2.6 to 9.7); 22/32; .002 | 6.4% (2.8 to 10.3); 25/38; .001 |
| iptw | 0.126 → 0.121 | 4.4% (−0.9 to 10.6); 19/32; .17 | 5.2% (0.4 to 10.8); 23/38; .07 |
| overlap | 0.108 → 0.104 | 4.0% (0.9 to 7.8); 19/32; .02 | 5.5% (2.0 to 9.6); 25/38; .003 |
| gbm | 0.122 → 0.112 | 8.1% (1.6 to 15.4); 23/32; .03 | 9.3% (2.8 to 15.6); 28/38; .009 |

- **Can the ECG replace LVEF?** In the main configuration (S32), the no-LVEF PS + ECG against the with-LVEF PS alone gives 0.113 → 0.112, 0.7% (−5.3 to 6.5), P .81. That is, the ECG makes up for the loss of LVEF on these 42 items.
- **Across 5 imputation draws** (§7), LVEF bought between −1.4% and 5.9% in the main configuration. On per-trial |SMD| averaged over the draws it bought 2.9% (−1.0 to 7.4) in S32 and 3.9% (−0.3 to 8.6) in S38.
- **On the LVEF-derived items themselves** (v1 masking, where the with-LVEF PS was not masked for them, so this effect is mechanical):
  - echo EF 0.108 → 0.077 (28.8%) and LV systolic grade 0.148 → 0.091 (38.6%) in S32;
  - all 35 echo items 0.128 → 0.122 (4.6%; P .28).

  So LVEF in the PS mostly balanced the copies of itself.

### 5.6 Information ladder (main; mean over trials of each trial's mean |SMD|; S32 then S38)

**Common item set:** the 45 items held out at every one of the four default ladder levels (= the no-LVEF rung's held-out set). The last column is + ECG vs PS alone, paired, on the rung's own leakage-clean 54-item set.

| PS base | PS alone | + ECG | + CLMBR-T | + CLMBR-T + ECG | + ECG vs PS alone (95% CI) |
|---|---|---|---|---|---|
| PS-Demo | 0.143 / 0.139 | 0.127 / 0.120 | 0.117 / 0.111 | 0.111 / 0.105 | 11.3% (6.0 to 16.1) / 12.6% (7.7 to 16.8) |
| PS-CVD5 | 0.129 / 0.122 | 0.117 / 0.111 | 0.117 / 0.110 | 0.118 / 0.110 | 8.8% (4.4 to 13.3) / 9.0% (5.0 to 13.5) |
| hdPS | 0.122 / 0.115 | 0.113 / 0.107 | 0.127 / 0.119 | 0.107 / 0.101 | 7.6% (1.7 to 13.0) / 7.6% (2.2 to 12.6) |
| **PS-Clinical (no LVEF)** | **0.117 / 0.111** | **0.112 / 0.106** | 0.115 / 0.109 | 0.112 / 0.105 | **4.5% (−2.9 to 10.9) / 5.3% (−1.3 to 11.2)** |
| (PS-Flags) | 0.117 / 0.110 | 0.122 / 0.114 | 0.120 / 0.113 | 0.124 / 0.115 | −3.0% / −1.8% |
| (PS-Clinical with LVEF, 42 items) | 0.113 / 0.105 | 0.115 / 0.106 | 0.111 / 0.102 | 0.113 / 0.104 | −1.7% / −0.9% |

**On the 35 echo items alone** (S32):
- PS alone: PS-Demo 0.157, PS-CVD5 0.140, hdPS 0.133, PS-Clinical (no LVEF) 0.128;
- + ECG: 0.136, 0.127, 0.122, 0.122.

**PS-Clinical (no LVEF) against the other rungs** (PS alone, S32, main):
- vs PS-CVD5: 9.0% (2.9 to 14.6), 25/32, P .003;
- vs hdPS: 5.0% (−4.8 to 13.5), P .31.

So even without LVEF the ladder still descends. The ECG gain shrinks up the ladder (11.3 → 8.8 → 7.6 → 4.5%) but no longer turns negative at the top.

### 5.7 CLMBR-T rows (main, S32, clean)

| Contrast | Rel. reduction (95% CI) | Better | P |
|---|---|---|---|
| PS-Clinical (no LVEF) + CLMBR-T vs PS alone | 1.5% (−6.8 to 9.0) | 20/32 | .36 |
| + CLMBR-T + ECG vs PS alone | 4.0% (−4.1 to 11.4) | 20/32 | .16 |
| + CLMBR-T + ECG vs + CLMBR-T | 1.9% (−2.7 to 6.4) | 18/32 | .22 |
| + CLMBR-T vs + permuted CLMBR-T | 2.9% (−4.0 to 9.1) | 22/32 | .20 |
| + CLMBR-T (32 PCs) vs PS alone | −1.3% (−9.6 to 5.6) | 16/32 | .61 |
| PS-CVD5 + CLMBR-T vs PS-Clinical (no LVEF) alone (two-sided) | −0.1% (−6.2 to 5.5) | 17/32 | .98 |
| PS-CVD5 + CLMBR-T + ECG vs PS-Clinical (no LVEF) alone | −0.3% (−9.5 to 7.8) | 17/32 | .94 |
| PS-CVD5 + ECG vs PS-Clinical (no LVEF) alone | −0.2% (−6.9 to 6.2) | 15/32 | .96 |

**PS-CVD5 + CLMBR-T vs PS-Clinical (no LVEF)** was −2.6% (clean) against the with-LVEF PS-Clinical in DEFECT_IMPACT; it is now −0.1%. In other configurations:
- gbm: −0.3% (−6.4 to 6.2);
- PS-CVD5 + CLMBR-T + ECG with gbm: 7.7% (1.9 to 13.9), P .02;
- overlap: 6.4% (1.7 to 11.6).

## 6. Sensitivity: LVEF column dropped from the existing imputation

These analyses keep the indirect channel: the other covariates were imputed using LVEF.

| S32, main, clean | + ECG | + CLMBR-T | + CLMBR-T + ECG | ECG vs permuted ECG | LVEF bought |
|---|---|---|---|---|---|
| re-imputed (primary) | 4.5% (−2.9 to 10.9) | 1.5% (−6.8 to 9.0) | 4.0% (−4.1 to 11.4) | 8.7% (3.2 to 14.0) | 3.1% (−3.3 to 9.4) |
| column dropped | 1.9% (−3.8 to 7.5), 19/32, P .25 | −2.7% (−11.2 to 4.1) | 2.3% (−5.6 to 9.6) | 3.1% (−2.2 to 8.6) | 2.2% (−3.7 to 7.6) |

**S38, column dropped:** ECG 2.2% (−2.8 to 7.4); CLMBR-T −2.0%; both 2.9%.

**Other configurations, column dropped** (S32, ECG):
- m13: 7.0% (3.0 to 11.1), P < .001;
- overlap: 5.6% (2.2 to 9.5), P .001;
- gbm: 1.8%.

The two variants differ by roughly the size of single-imputation draw noise (§7), so the difference cannot be attributed to the indirect channel.

## 7. Sensitivity: imputation draws (main configuration; `imputation_draws.py`)

**Setup:**
- Imputations 1–5 use seeds 20260923 + 0..4.
- With LVEF, draws 1–5 are the existing `restricted_completed_0k` tables. Without LVEF, the same `impute` call is used with m = 5; draw 1 = primary, asserted identical.
- Draw 1 reproduces the main cells exactly (max deviation 0).
- Relative reduction is on 54 items, clean masks.

| Set | PS base | Arm | Draws 1 / 2 / 3 / 4 / 5 | Per-trial \|SMD\| averaged over draws (95% CI); better; P |
|---|---|---|---|---|
| S32 | with LVEF | + ECG | **−1.7** / 0.3 / 1.9 / 1.9 / 2.1 | 1.1% (−2.1 to 4.5); 17/32; .26 |
| S32 | no LVEF | + ECG | **4.5** / 3.2 / 6.0 / −1.8 / 4.4 | 3.3% (−0.9 to 7.3); 19/32; .07 |
| S32 | with LVEF | + CLMBR-T | 1.5 / −3.0 / 2.4 / 3.2 / 2.9 | 2.3% (−2.3 to 6.6) |
| S32 | no LVEF | + CLMBR-T | 1.5 / −1.8 / 5.2 / 1.7 / 4.0 | 2.3% (−3.9 to 7.5) |
| S32 | with LVEF | + CLMBR-T + ECG | −0.5 / −2.7 / 2.3 / 0.9 / 0.2 | 0.6% (−5.4 to 6.4) |
| S32 | no LVEF | + CLMBR-T + ECG | 4.0 / 0.8 / 3.0 / 0.1 / 6.2 | 3.1% (−2.1 to 8.1) |
| S32 | with / no LVEF | + permuted ECG | median −1.7 / −1.5 | −0.7% / −1.0% |
| S38 | with LVEF | + ECG | −0.9 / 1.2 / 2.4 / 1.8 / 3.0 | 1.6% (−1.3 to 4.8); 22/38; .15 |
| S38 | no LVEF | + ECG | 5.3 / 3.5 / 5.9 / −0.4 / 4.0 | 3.7% (−0.2 to 7.3); 24/38; .03 |
| S38 | no LVEF | + CLMBR-T + ECG | 5.6 / 0.7 / 3.4 / 2.2 / 6.6 | 3.9% (−0.9 to 8.6) |

**Reading:**
- **Spread.** The ECG gain at PS-Clinical varies by about 4–8 points between imputation draws.
- **Old draw.** The draw used by version 1 (draw 1) was the least favourable of the 5 for the with-LVEF ECG contrast.
- **Average-draw estimates.** Averaged over draws, the ECG gain is 1.1% with LVEF and 3.3% without (S32). Removing LVEF shifts the ECG gain up by about 2 points; the draw-1 headline overstates the shift (−1.7 → 4.5).
- **Status.** None of these is a formal multiple-imputation analysis. The grid itself still uses a single imputation.

## 8. Balance explorer

`scripts/build_balance_explorer.py` (edited) rebuilds `docs/presentation/ecg_tte_balance_explorer_2026_10_08.html`.

**Changes:**
- New information level "PS-Clinical (no LVEF)", read from `audits/claude-v1-psclin-nolvef/cells/` (re-imputed primary).
- The old level is renamed "PS-Clinical (with LVEF, v1)".
- New "Ladder levels" checkboxes. The default ladder is PS-Demo → PS-CVD5 → hdPS → PS-Clinical (no LVEF); PS-Flags and the with-LVEF PS-Clinical can still be ticked.
- Leakage-corrected masking for the new level masks eGFR and the 4 coded items.
- `TRACE.level` was added for headless checks. Header and caption text were updated.

**Validation (`--check`, Python, full precision):**
- 141/141 published values still match (paper 1 eTables 3A/7A, paper 2, DEFECT_IMPACT).
- Paper 2 `sensitivity.csv`: 600 rows, max deviation 4.5e-14.
- Leakage-clean sweep: 600 rows, 4.5e-14.
- The same 28 F1-affected rows as before.
- New rung vs `summary/contrasts.csv`: 240 rows (6 configurations × S32/S38 × 5 arms × 54/58 × masking off/on).
  - Max deviations: relative reduction 3.3e-14, CI 8.5e-14, mean |SMD| 1e-16, % < 0.1 7e-15, P 1.1e-16;
  - trials-better counts are all equal.
- Ladder levels vs `summary/ladder.csv`: 1,728 values, max deviation 1e-16, trial counts all equal.

**Headless (Chromium; `explorer_headless_check.py`, outputs in `audits/claude-v1-psclin-nolvef/explorer/`):**
- 0 page or console errors.
- 498 control actions, including the new ladder checkboxes. The default view still shows paper 1's primary numbers (11.4%, 6.3 to 16.0; 49.8 → 55.0; 22/32; P .002) and is restored after toggling.
- The default ladder shows PS-Demo, PS-CVD5, hdPS, PS-Clinical (no LVEF).
- JS vs Python on the embedded data: 72 combinations (12 for the new rung), 936 values, 0 mismatches (max deviation 9e-14).
- JS vs the full-precision summaries for the new rung: 240/240 relative reductions equal at 1 decimal (max deviation 2.4e-4, from the 1e-5 integer encoding); 1,728/1,728 ladder levels equal at 3 decimals.
- Privacy scan of the HTML: pass (no forbidden keys or strings, no 6+ digit identifiers, no small counts in text).

## 9. Limitations

- **Single imputation.** The covariates are imputed once. Draw-to-draw noise (§7) is of the same order as the effects. The re-imputation includes the treatment indicator as a predictor, as in version 1.
- **Residual LVEF information.** Not in the PS, but present through correlates: the diagnoses (heart failure), medications (e.g., MRA, loop diuretic) and utilisation are still in the PS, and they are correlated with LVEF. That is intended: they are not echo measurements. The largest remaining pooled correlation of an echo item with a PS input is 0.55 (aortic root ~ male).
- **Column-dropped variant.** It keeps the indirect channel through the imputation model; it is reported only as a sensitivity.
- **Masking choice.** The 4 coded items are masked for this rung under the clean rule, so the "58-item" result equals the 54-item result. With paper 1's rule (only PS inputs masked), the 58-item figure is 4.2% (−3.1 to 10.5).
- **Unchanged version 1 issues.** The open cohort issues of the version 1 audit (handoff §4) and the fixed C = 1 penalty (a CV penalty shrinks the ECG gain at PS-CVD5) are not addressed here.

## 10. Files

**Repository (code and this document; nothing restricted):**
- `scripts/v1_psclin_nolvef/psclin_nolvef.py`: impute / run / gate / summarize / privacy;
- `scripts/v1_psclin_nolvef/imputation_draws.py`;
- `scripts/v1_psclin_nolvef/make_tables.py`;
- `scripts/v1_psclin_nolvef/explorer_headless_check.py`;
- `scripts/build_balance_explorer.py` (edited) and `docs/presentation/ecg_tte_balance_explorer_2026_10_08.html` (rebuilt).

**Audits** (`/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-psclin-nolvef/`, umask 077, not committed):
- `imputation/`: restricted re-imputed tables, `imputation_status.json`, aggregate change tables;
- `cells/`: `restricted_cells.parquet`, suppressed `cells.csv`, `gate.csv`, `gate_status.json`;
- `summary/`: `contrasts.csv`, `domains.csv`, `ladder.csv`, `failed_cells.csv`, `tables.md`;
- `impdraws/`: restricted cells, `imputation_draws.csv`, `imputation_draws_range.csv`;
- `explorer/`: headless results, screenshots, explorer privacy scan;
- `privacy_scan.json`: clean; no count of 1–10 in any csv;
- `logs/`.
