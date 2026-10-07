# paper2 plasmode: PS-CVD5, the ECG and CLMBR-T (2026-10-07)

**Supplement analysis, exploratory.** This is step C of `HANDOFF_PAPER2.md` (§3.5). It extends the v2.0 G2 plasmode (`docs/v20/G2_EXTENSION.md`, `scripts/v20/g2b_simulation_ext.py`) with PS-CVD5 and CLMBR-T arms.
- Code: `scripts/v21/paper2_plasmode.py` (imports g2b; g2b is not modified).
- Aggregates: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/plasmode/` (umask 077).
- Log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/logs/plasmode.log`.

## Verdict (plain language)

1. **Gate passed.** The existing arms, recomputed with the new code, match `claude-v20-g2-ext` replicate outputs exactly: 1,080 rows, max |Δ| = 0 for log HR, SE, truth, n, n treated and events. The new arms therefore share subsamples, treatments and outcomes with the published plasmode.
2. **PS-CVD5 by itself removes about a fifth of the hidden-confounder bias.** The design has treatment driven by the withheld confounder only and is clinically oriented. PS-CVD5 removes 18.6% of the bias overall, vs 2.4% for PS-Demo. The five diagnoses act as proxies for the confounder: LVEF 24.0%, NT-proBNP 25.8%, BMI 6.2%, eGFR 18.0%.
3. **The ECG still adds on top of PS-CVD5.** It removes a further **11.3%** (MCSE 0.3) of the bias that PS-CVD5 leaves. By confounder: LVEF 15.2%, NT-proBNP 15.1%, BMI 19.2%, but only 2.5% for eGFR. PS-CVD5 + ECG removes 27.8% of the bias vs unmatched.
4. **CLMBR-T adds more than the ECG overall, but the gain comes mostly from the renal and natriuretic confounders.**
   - Over PS-CVD5, CLMBR-T removes a further **22.6%** (MCSE 0.3) of the remaining bias.
   - By confounder: eGFR 35.5%, NT-proBNP 28.4%, BMI 10.2%, LVEF 8.4%.
   - So for **LVEF the ECG adds more than CLMBR-T** (15.2% vs 8.4%). For eGFR and NT-proBNP, CLMBR-T adds far more.
   - This matches the real-data cross-fitted R² for the confounder: CLMBR-T 0.34 for eGFR vs 0.05 for the ECG, and 0.19 for LVEF vs 0.22 for the ECG (cell means).
5. **The two representations are partly complementary.**
   - PS-CVD5 + ECG + CLMBR-T removes **42.6%** of the bias vs unmatched, and 29.5% of what PS-CVD5 leaves.
   - Added on top of PS-CVD5 + CLMBR-T, the ECG still removes 8.9% overall and 9.7% for LVEF.
   - Added on top of PS-CVD5 + ECG, CLMBR-T removes 20.5% overall but only 2.5% for LVEF.
6. **The placebo shows the gains are not a dimension artefact.** Adding 64 permuted CLMBR-T PCs to PS-CVD5 removes 1.0% (MCSE 0.4). The permuted ECG alone removes −0.1%.
7. **No representation substitutes for measuring the confounder.**
   - The best arm (PS-CVD5 + ECG + CLMBR-T) removes 43% of the bias; the oracle removes 94%.
   - CI coverage of the true effect is 77% for the best arm vs 94% for the oracle. Every non-oracle arm is between 51% and 77%.

The doc rounds MCSEs to 0.1; the CSVs carry the unrounded values.

## Design (unchanged from the paper's primary plasmode)

**Cells, seeds and replicates.** The cells are the 107 analysed trial × confounder cells in 31 trials: LVEF 25, NT-proBNP 21, BMI 31, eGFR 30. The design is identical to `docs/v20/G2_EXTENSION.md`:
- ROCKET-AF × LVEF is excluded, as in v1.9 and v2.0;
- 50 replicates per cell, each an 80% subsample without replacement;
- the 9 non-null OR_T × HR_Y scenarios plus the null;
- true HR 0.80;
- the same seeds, keyed by replicate, trial, confounder and scenario, never by arm.

**Treatment** depends on the withheld confounder C only ("trtC"), with the intercept recalibrated to the real treated share.
- **Clinically oriented:** LVEF and eGFR are sign-flipped, so a higher Cz means lower LVEF / eGFR, more treatment and higher hazard. These cells come from g2b `trtC_adv`.
- NT-proBNP and BMI come from g2b `trtC` (as designed; identical by construction).
- This is the combination behind g2b `pooled_trtC_cliniorient.csv`, the source of the paper's "ECG alone removes 18.0%" result.

**Matching and estimation** are as before: L2 logistic PS refitted in every replicate, 1:1 greedy matching with caliper 0.2 SD, and a pair-clustered Cox model. The truth is the marginal log HR in each arm's matched population. C is in no PS except the oracle.

**Arms**

| Arm | PS covariates | Source |
|---|---|---|
| Unmatched | none | g2b `reps_trtC*` |
| PS-Demo (`base`) | age, sex, index year | g2b |
| PS-Demo + ECG | + 32 ECG PCs (`T.ecg_pc`) | g2b |
| ECG only / permuted ECG only | 32 ECG PCs / permuted | g2b |
| Oracle | PS-Demo + Cz | g2b |
| **PS-CVD5** (`P5`) | PS-Demo + hypertension, T2D, CAD, AF, HF (`v18_clmbr.designs(T, n, P5DX)`, 8 columns; HF = `hf_any_365` in 26 trials, `elx_chf` in 5), as `sens_primary32` | new |
| **PS-CVD5 + ECG** | + 32 ECG PCs | new |
| **PS-CVD5 + CLMBR-T** | + 64 CLMBR-T PCs (`T.clm_pc`) | new |
| **PS-CVD5 + ECG + CLMBR-T** | + both | new |
| **CLMBR-T only** | 64 CLMBR-T PCs | new |
| **PS-CVD5 + permuted CLMBR-T** (placebo; added) | + `T.clm_pc[T.shuffle_perm]` | new |

**Endpoints** are as in g2b `pooled()`:
- **% of bias removed** = 100 × (1 − Σ cell-mean error of the arm / Σ cell-mean error of the reference), over trial × C × the 9 non-null scenarios.
- **Null-corrected:** the error in each scenario minus the null-scenario error for the same arm and subsample.
- **Added share over a PS** = the % of that PS's remaining bias removed by adding the representation.
- **MCSE:** 1,000 resamples of replicates within cells. It reflects simulation error only, not uncertainty over trials.
- **Bias, empirical SE, RMSE and coverage**, with MCSE (Morris et al. 2019).

## 1. Gate

**Gate 1: replicate outputs.** `paper2_plasmode.py` re-implements g2b's replicate function. It is identical code, with the arm list passed as an argument and the P5 / CLMBR-T blocks added. The existing six trtC arms were recomputed on 6 cells × 3 replicates × 10 scenarios and compared with g2b's reps after the same CSV round trip (`gate.csv`):

| g2b variant | Cells | Rows | Matched to reference | Max \|Δ\| (log HR, SE, truth, n, n_t, events) | NaN pattern | Result |
|---|---|---|---|---|---|---|
| `trtC_adv` | comet × LVEF, aristotle × LVEF, plato × eGFR | 540 | 540 / 540 | 0 | equal | **PASS** |
| `trtC` | aristotle × BMI, affirm × NT-proBNP, comet × NT-proBNP | 540 | 540 / 540 | 0 | equal | **PASS** |

**Gate 2: pooled results.** After the full run, the existing arms' pooled results, recomputed together with the new arms, reproduce g2b `pooled_trtC_cliniorient.csv`: 60/60 rows, max |Δ| 1.4e-14 in % removed, i.e. floating-point summation order (`summary_check.csv`).

**Cache identity.** For all 31 trials, the reloaded `T.cov[T.demo]`, `T.ecg_pc`, permuted ECG and `T.X_dx` equal the v1.9 / v2.0 cache arrays exactly. The P5 and CLMBR-T matrices are finite with the expected shapes (`prep_p5.csv`).

## 2. % of C-induced bias removed vs unmatched (null-corrected; clinically oriented, treatment from C)

Source: `pooled_trtC_cliniorient_p5.csv`, `analysis == "null-corrected"`. MCSE: ≤ 0.28 for "All" (≤ 0.40 for the oracle) and ≤ 0.70 per confounder (≤ 1.03 for the oracle).

| Arm | LVEF | NT-proBNP | BMI | eGFR | All |
|---|---|---|---|---|---|
| PS-Demo | 1.3 | 9.0 | −9.6 | 6.0 | 2.4 |
| PS-Demo + ECG | 28.2 | 27.0 | 11.8 | 12.7 | 18.9 |
| ECG only | 27.6 | 22.3 | 15.7 | 9.0 | 17.2 |
| Permuted ECG only | −0.0 | 0.3 | 0.7 | −0.8 | −0.1 |
| **PS-CVD5** | 24.0 | 25.8 | 6.2 | 18.0 | **18.6** |
| **PS-CVD5 + ECG** | 35.5 | 37.0 | 24.2 | 20.0 | **27.8** |
| **PS-CVD5 + CLMBR-T** | 30.4 | 46.9 | 15.8 | 47.1 | **37.0** |
| **PS-CVD5 + ECG + CLMBR-T** | **37.1** | **53.8** | **29.0** | **47.2** | **42.6** |
| **CLMBR-T only** | 27.0 | 38.6 | 15.6 | 45.2 | **33.8** |
| PS-CVD5 + permuted CLMBR-T | 23.7 | 27.7 | 7.2 | 18.7 | 19.4 |
| Oracle (PS-Demo + C) | 92.9 | 91.9 | 90.0 | 97.2 | 93.7 |

**Raw results (not null-corrected),** "All" column: PS-CVD5 18.9, + ECG 26.9, + CLMBR-T 36.9, + both 41.9, CLMBR-T only 33.8, + permuted CLMBR-T 18.9; MCSE ≤ 0.20.
- By confounder: PS-CVD5 + ECG + CLMBR-T removes 37.9 / 51.1 / 27.0 / 47.2 for LVEF / NT-proBNP / BMI / eGFR, and CLMBR-T only removes 27.5 / 38.4 / 15.2 / 44.8.
- The existing arms reproduce the paper exactly: ECG only 18.0 overall (27.9 / 22.2 / 17.5 / 9.7), oracle 93.1, permuted ECG −0.2.

## 3. Added share over PS-CVD5 (null-corrected; % of the remaining bias; MCSE in brackets)

Source: `added_value_p5.csv`.

| Contrast | LVEF | NT-proBNP | BMI | eGFR | All |
|---|---|---|---|---|---|
| **ECG over PS-CVD5** | 15.2 (0.8) | 15.1 (0.8) | 19.2 (0.8) | 2.5 (0.5) | **11.3 (0.3)** |
| **CLMBR-T over PS-CVD5** | 8.4 (0.8) | 28.4 (0.9) | 10.2 (0.8) | 35.5 (0.5) | **22.6 (0.3)** |
| **ECG + CLMBR-T over PS-CVD5** | 17.3 (0.8) | 37.8 (0.9) | 24.3 (0.8) | 35.7 (0.5) | **29.5 (0.4)** |
| ECG over PS-CVD5 + CLMBR-T | 9.7 (0.9) | 13.1 (1.2) | 15.7 (0.9) | 0.2 (0.8) | 8.9 (0.5) |
| CLMBR-T over PS-CVD5 + ECG | 2.5 (0.9) | 26.7 (1.0) | 6.3 (1.0) | 34.0 (0.5) | 20.5 (0.4) |
| Permuted CLMBR-T over PS-CVD5 (placebo) | −0.3 (0.8) | 2.5 (0.9) | 1.0 (0.9) | 0.9 (0.5) | 1.0 (0.4) |
| CVD5 diagnoses over PS-Demo | 23.0 (0.6) | 18.4 (0.7) | 14.4 (0.7) | 12.8 (0.4) | 16.6 (0.3) |
| ECG over PS-Demo (same design, for reference) | 27.3 (0.6) | 19.7 (0.7) | 19.5 (0.7) | 7.1 (0.4) | 16.9 (0.3) |

**Raw (not null-corrected), All column:**

| Contrast | Raw value |
|---|---|
| ECG over PS-CVD5 | 9.8 |
| CLMBR-T over PS-CVD5 | 22.2 |
| Both over PS-CVD5 | 28.3 |
| ECG over PS-CVD5 + CLMBR-T | 7.9 |
| CLMBR-T over PS-CVD5 + ECG | 20.5 |
| Placebo | −0.1 |

For LVEF the raw values are 15.8 (ECG over PS-CVD5) and 10.5 (CLMBR-T over PS-CVD5).

**Relation to the paper's added-share numbers.** The paper's 14.9% (PS-Demo), 8.6% (hdPS) and 11.7% (PS-Clinical) come from the g2b *main* treatment design (demographic PS logit + C, clinically oriented), not from trtC. In trtC the ECG adds 16.9% over PS-Demo. hdPS and PS-Clinical rungs were not run in trtC, so the new CLMBR-T arms cannot be compared directly with hdPS or PS-Clinical here.

## 4. Real-data predictiveness of C (context)

Mean cross-fitted ridge R² of Cz in S over the 107 cells (source: `r2_p5.csv`; same estimator as v1.9 `cv_r2`):

| Representation | LVEF | NT-proBNP | BMI | eGFR | All |
|---|---|---|---|---|---|
| PS-CVD5 covariates | 0.13 | 0.18 | 0.13 | 0.08 | 0.13 |
| ECG | 0.22 | 0.20 | 0.22 | 0.05 | 0.17 |
| CLMBR-T | 0.19 | 0.27 | 0.25 | 0.34 | 0.27 |
| PS-CVD5 + ECG + CLMBR-T | 0.29 | 0.37 | 0.39 | 0.35 | 0.35 |
| Permuted CLMBR-T | −0.00 | −0.00 | −0.00 | −0.00 | −0.00 |

The ordering of bias removed follows the R² ordering, as in v1.9 (bias removed ≈ 100 × R²).

CLMBR-T's high eGFR and NT-proBNP R² plausibly come from codes that track kidney and heart-failure care, for example CKD diagnoses, nephrology or heart-failure drugs, and *which* labs were ordered (measurement codes without values; see `docs/v18/CLMBR_LEAKAGE.md`). CLMBR-T never sees the confounder's value, so this is legitimate proxy information. It is, however, coded-record information rather than physiology.

## 5. Performance (non-null scenarios; clinically oriented, treatment from C)

Source: `performance_trtC_cliniorient_p5.csv`. All confounders: 963 trial × C × scenario cells, 50 replicates each. MCSE of bias is 0.001 and of coverage ≤ 0.17 points. Bias is on the log-HR scale (log HR − truth).

| Arm | Bias | Empirical SE | RMSE | Coverage |
|---|---|---|---|---|
| Unmatched | 0.228 | 0.118 | 0.269 | 51.2% |
| PS-Demo | 0.222 | 0.135 | 0.272 | 57.7% |
| PS-Demo + ECG | 0.184 | 0.136 | 0.243 | 65.4% |
| ECG only | 0.187 | 0.137 | 0.246 | 64.7% |
| PS-CVD5 | 0.185 | 0.133 | 0.240 | 64.8% |
| PS-CVD5 + ECG | 0.166 | 0.135 | 0.228 | 69.2% |
| PS-CVD5 + CLMBR-T | 0.144 | 0.136 | 0.209 | 74.2% |
| PS-CVD5 + ECG + CLMBR-T | 0.132 | 0.137 | 0.202 | 76.9% |
| CLMBR-T only | 0.151 | 0.136 | 0.215 | 72.4% |
| PS-CVD5 + permuted CLMBR-T | 0.185 | 0.137 | 0.243 | 65.6% |
| Oracle | 0.016 | 0.135 | 0.138 | 94.4% |

**By confounder,** shown as bias / coverage (coverage MCSE ≤ 0.39 points):

| Arm | LVEF (225 cells) | NT-proBNP (189) | BMI (279) | eGFR (270) |
|---|---|---|---|---|
| Unmatched | 0.226 / 52% | 0.236 / 47% | 0.152 / 68% | 0.301 / 36% |
| PS-CVD5 | 0.173 / 68% | 0.173 / 66% | 0.141 / 74% | 0.247 / 51% |
| PS-CVD5 + ECG | 0.146 / 75% | 0.154 / 71% | 0.119 / 79% | 0.242 / 53% |
| PS-CVD5 + CLMBR-T | 0.155 / 73% | 0.130 / 77% | 0.128 / 78% | 0.160 / 69% |
| PS-CVD5 + ECG + CLMBR-T | 0.140 / 77% | 0.116 / 81% | 0.111 / 81% | 0.159 / 70% |
| CLMBR-T only | 0.164 / 71% | 0.145 / 73% | 0.129 / 78% | 0.166 / 67% |
| Oracle | 0.017 / 95% | 0.027 / 94% | 0.012 / 95% | 0.010 / 94% |

**Null scenario check** (OR_T = 1, HR_Y = 1, i.e. random treatment; `null_check_p5.csv`): mean bias is within ±0.003 for every arm, and coverage is 94.8–95.8%.

**Retention** (`retention_p5.csv`) is the mean matched share of the replicate subsample:

| Arm | Retention |
|---|---|
| PS-Demo | 66.6% |
| PS-CVD5 | 66.2% |
| PS-CVD5 + ECG | 64.7% |
| PS-CVD5 + CLMBR-T | 63.1% |
| PS-CVD5 + ECG + CLMBR-T | 61.5% |
| CLMBR-T only | 63.6% |
| Oracle | 63.8% |

The richer PS lose slightly more pairs. Because the truth is defined in each arm's own matched population, retention differences do not bias the % removed.

## 6. Deviations and notes (logged)

1. **Existing arms reused.** Unmatched, PS-Demo, PS-Demo + ECG, ECG only, permuted ECG only and the oracle are taken from g2b `reps_trtC.csv` / `reps_trtC_adv.csv` rather than recomputed, as g2b did with the v1.9 arms. This is justified by the exact gate (§1). Only the new arms were simulated: 324,000 estimates (trtC_adv LVEF/eGFR 168,000; trtC NT-proBNP/BMI 156,000), 15 min on 24 workers.
2. **Only the primary design was run.** That is clinically oriented trtC: `trtC_adv` for LVEF/eGFR and `trtC` for NT-proBNP/BMI. The as-designed orientation and the g2b main design (demographic logit + C) were not run with the new arms, and there are no hdPS, PS-Clinical, PS-Flags or CLMBR-T 32-PC arms in the plasmode.
3. **Added placebo arm.** PS-CVD5 + permuted CLMBR-T was not in the §3.5 arm list. It was added because CLMBR-T has 64 dimensions vs the ECG's 32.
4. **PCs from the full trial cohort.** P5 and the CLMBR-T PCs are computed on the full trial cohort (`v18_clmbr.designs`, `T.clm_pc`), then subset to each replicate's rows, as for the ECG PCs. The PS is refitted in every replicate.
5. **Clinical orientation is post hoc** (inherited from v1.9/v2.0; see `docs/v20/G2_EXTENSION.md` §7).
6. **Cell exclusion.** ROCKET-AF × LVEF is excluded via v1.9 `excluded_cells.csv`, as in g2b.
7. **Suppression.** In `reps_*_p5.csv`, counts 1–10 are set to missing (flag `suppressed_lt11`). This affects only the event counts in 939 rows, all in the excluded ROCKET-AF × LVEF cell. The summaries use no counts below 11.
8. **MCSE scope.** MCSEs reflect simulation error only (replicate resampling within cells), not trial-selection uncertainty.
9. **No commit.** Code and docs are left for the coordinator.

## Files

All in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/plasmode/`:

| File | Content |
|---|---|
| `gate.csv` | reproduction gate |
| `summary_check.csv` | pooled consistency check |
| `prep_p5.csv` | P5 columns per trial |
| `r2_p5.csv` | real-data R² per cell |
| `reps_trtC_adv_p5.csv`, `reps_trtC_p5.csv` | replicate-level aggregates, new arms, suppressed |
| `pooled_trtC_cliniorient_p5.csv` | % removed vs unmatched / PS-Demo / P5 / P5 + ECG / P5 + CLMBR-T, raw and null-corrected, with MCSE |
| `added_value_p5.csv` | added shares |
| `performance_trtC_cliniorient_p5.csv` | bias, empirical SE, RMSE, coverage, with MCSE |
| `null_check_p5.csv` | null scenario check |
| `retention_p5.csv` | matched share |
| `cache/restricted_p5_*.npz` | restricted design matrices, not for export |
