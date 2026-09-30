# v2.0 G2 extension: ECG alone, and the ECG on top of richer propensity scores (plasmode; 2026-09-30)

**Exploratory.** This extends the v1.9 G2 plasmode (`docs/v19/G2_SIMULATION.md`) on the same 107 trial × confounder cells (31 trials) and the same grid, seeds and replicates.
- Code: `scripts/v20/g2b_simulation_ext.py`.
- Aggregates: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-g2-ext/` (umask 077).
- Figure: `docs/v20/G2_EXT_bias_by_rung.png`.

## Verdict (plain language)

1. **The ECG by itself removes about a quarter of the bias from a hidden LVEF confounder, and about a sixth across the four confounders.**
   - With a propensity score built only from the 32 ECG PCs, 28% of the LVEF-induced bias is removed relative to no adjustment. This uses the clean design with treatment driven by C only, in the clinical orientation (lower LVEF = more treatment and higher risk).
   - The same ECG-only PS removes 22% for NT-proBNP, 18% for BMI and 10% for eGFR, 18% overall.
   - A PS on the permuted ECG removes 0%, and adjusting for the confounder itself (oracle) removes 92–93%.
   - This matches the v1.9 rule that bias removed ≈ 100 × the ECG's R² for the confounder (LVEF R² ≈ 0.26).
2. **The ECG still adds on top of richer propensity scores, but less.**
   - It removes a further 9–15% of whatever bias each PS leaves (null-corrected, all confounders):
     - demographic PS 15%;
     - sparse 10%;
     - hdPS200 9%;
     - clinical PS without the confounder 12%.
   - For LVEF the added share is 13–22%; for eGFR it is about 0–6%.
   - Richer PS remove much more bias on their own: codes are good proxies for eGFR (CKD) and NT-proBNP (HF), and poor ones for LVEF and BMI.
3. **Nothing makes the ECG a substitute for measuring the confounder.**
   - The best arm (hdPS + ECG) removes 45% of the C-induced bias overall and 37% for LVEF. The oracle removes about 94%.
   - CI coverage of the true effect stays at 68–83% for every ECG-containing arm, vs 95% for the oracle.
4. **The result does not depend on the true HR of 0.80.** The % of bias removed by adding the ECG is 14.2% at true HRs of 0.6, 0.8 and 1.0 (MCSE 0.5).

## Why the "clinical orientation" is the primary lens here

In the v1.9 as-designed simulation, a higher value of every confounder raises both treatment and hazard. For LVEF and eGFR that is the clinically reverse direction.
- The real covariates in the outcome model (heart failure, CKD, creatinine and so on) are associated with LVEF and eGFR in the clinically adverse direction. Their paths therefore partly cancel C's bias when patients are unmatched.
- Any PS that balances those proxies removes the cancellation and can increase the error relative to unmatched. In the as-designed run, sparse, hdPS and clinical PS all look worse than unmatched for LVEF and eGFR (table in section 5).
- This was already the caveat in v1.9. There, the "adverse" variant (LVEF and eGFR sign-flipped, i.e. clinically oriented) was post hoc.

Here the **clinically oriented set** combines LVEF and eGFR from the adverse runs with NT-proBNP and BMI from the as-designed runs, which are identical by construction. It is the primary lens for interpretation. The as-designed results are reported in full, and the orientation choice is logged as a deviation.

## 1. Arms and designs

| Arm | PS covariates |
|---|---|
| unmatched | none |
| Demographic PS (v1.9 "base") | age, sex, index year |
| Demographic PS + ECG | + 32 ECG PCs |
| **ECG only** (new) | 32 ECG PCs only |
| **Permuted ECG only** (new, placebo) | 32 permuted ECG PCs only |
| **Sparse PS** / **+ ECG** (new) | `T.X_dx`: demographics + 9–13 trial diagnoses (12–16 columns) |
| **hdPS200** / **+ ECG** (new) | sparse + the top 200 hdPS recurrence levels (422–1,153 candidates per trial), re-ranked on the simulated treatment in each replicate (\|log prevalence ratio\|, as `v13_common.Trial.hd`) |
| **Clinical PS (minus C)** / **+ ECG** (new) | `T.X_core` (28–37 columns) with C's own analogue removed: `lvef` for LVEF, `bmi` for BMI, `creatinine` for eGFR. Nothing is removed for NT-proBNP, which is not in the clinical PS |
| Demographic PS + C (oracle) | demographics + the standardized confounder |

**Designs:**
- **main:** the v1.9 design. Treatment = demographic PS logit + log(OR)·C.
- **trtC** (new): treatment depends on C only, with the intercept recalibrated to the real treated share. There is no demographic confounding, so "ECG only vs unmatched" is clean.
- **adv / trtC_adv:** the same two designs, clinically oriented for LVEF and eGFR.
- **hr1.0 / hr0.6:** the main design with true HR 1.0 or 0.6. Common random numbers are used (same subsamples, treatments and uniforms). The arms are unmatched, demographic, + ECG, ECG only and oracle, in the null, (1.5, 1.5) and (2, 2) scenarios.

**Endpoints** follow v1.9:
- **% of bias removed** = 100 × (1 − Σ cell-mean error of the arm / Σ cell-mean error of the reference), over trial × C × the 9 non-null scenarios.
- **Null-corrected:** the error in each scenario minus the error in the null scenario for the same arm and subsample. This removes each arm's non-C (demographic or design) bias.
- **Monte Carlo SE (MCSE):** from 1,000 resamples of replicates within cells.
- **Other measures:** bias, empirical SE, RMSE and coverage, each with MCSE, following Morris, White & Crowther (Stat Med 2019).

## 2. Question 1: how much bias does the ECG remove by itself?

**% of C-induced bias removed vs unmatched, clinically oriented** (MCSE ≤ 0.3 for "all" and ≤ 0.6 per confounder):

| Arm | Design | LVEF | NT-proBNP | BMI | eGFR | All |
|---|---|---|---|---|---|---|
| **ECG only** | **trtC (clean), raw** | **27.9** | 22.2 | 17.5 | 9.7 | **18.0** |
| ECG only | trtC, null-corrected | 27.6 | 22.3 | 15.7 | 9.0 | 17.2 |
| Permuted ECG only | trtC, raw | 0.3 | 0.4 | −0.7 | −0.5 | −0.2 |
| Demographic PS | trtC, raw | 1.4 | 10.3 | −9.9 | 5.8 | 2.7 |
| Demographic PS + ECG | trtC, raw | 27.5 | 27.7 | 12.6 | 12.2 | 19.0 |
| Oracle | trtC, raw | 92.3 | 88.7 | 92.3 | 96.6 | 93.1 |
| **ECG only** | **main, null-corrected** | **26.3** | 19.2 | 17.7 | 7.3 | **16.3** |
| Permuted ECG only | main, null-corrected | 1.6 | 2.0 | −1.4 | −0.1 | 0.4 |
| Demographic PS + ECG | main, null-corrected | 24.2 | 17.4 | 8.8 | 5.7 | 13.0 |
| Oracle | main, null-corrected | 92.5 | 94.0 | 88.4 | 97.7 | 93.8 |

**Reading:**
- A PS on the ECG alone removes about as much C-induced bias as the demographic PS + ECG: 28% vs 28% for LVEF in the clean design. The demographic part contributes little to removing C's bias.
- LVEF is the confounder the ECG encodes best.

**Performance, LVEF, clean design (trtC, clinically oriented):**

| Arm | Bias | RMSE | Coverage |
|---|---|---|---|
| Unmatched | 0.226 | 0.266 | 52% |
| ECG only | 0.163 | 0.224 | 71% |
| Oracle | 0.017 | 0.140 | 95% |

Bias is on the log-HR scale.

## 3. Question 2: the ECG on top of richer PS

**% of C-induced bias removed vs unmatched (null-corrected, clinically oriented).** Each cell is PS alone → PS + ECG.

| PS | LVEF | NT-proBNP | BMI | eGFR | All |
|---|---|---|---|---|---|
| Demographic | 2.4 → **24.2** | −0.4 → 17.4 | −13.0 → 8.8 | 0.1 → 5.7 | −2.2 → **13.0** |
| Sparse | 19.7 → **32.7** | 34.5 → 38.4 | 0.6 → 16.8 | 49.4 → 48.3 | 29.2 → **36.1** |
| hdPS200 | 27.9 → **37.3** | 47.1 → 51.7 | 16.5 → 25.8 | 57.0 → 57.4 | 39.6 → **44.8** |
| Clinical (minus C) | 23.5 → **33.9** | 44.8 → 51.4 | −1.2 → 14.1 | 50.0 → 52.7 | 31.9 → **39.8** |
| ECG only | 26.3 | 19.2 | 17.7 | 7.3 | 16.3 |
| Oracle (demographic + C) | 92.5 | 94.0 | 88.4 | 97.7 | 93.8 |

**ECG's added share: % of the bias remaining after each PS that adding the ECG removes** (null-corrected, clinically oriented; MCSE in brackets):

| PS | LVEF | NT-proBNP | BMI | eGFR | All |
|---|---|---|---|---|---|
| Demographic | 22.4 (0.7) | 17.7 (0.7) | 19.3 (0.7) | 5.6 (0.5) | **14.9 (0.3)** |
| Sparse | 16.2 (0.8) | 6.0 (1.2) | 16.3 (0.8) | −2.3 (1.0) | **9.7 (0.4)** |
| hdPS200 | 13.0 (1.2) | 8.6 (1.8) | 11.1 (1.2) | 0.9 (1.2) | **8.6 (0.6)** |
| Clinical (minus C) | 13.7 (0.9) | 12.0 (1.3) | 15.1 (0.8) | 5.3 (0.9) | **11.7 (0.5)** |

The same measure without null correction (raw) is 17.1, 10.7, 10.1 and 11.0 for the four PS (all confounders); for LVEF it is 26.5, 14.7, 12.4 and 13.2.

**Performance, all confounders, clinically oriented** (963 trial × C × scenario cells; 50 replicates each; MCSE of bias 0.001 and of coverage ≤ 0.17 points):

| Arm | Bias | Empirical SE | RMSE | Coverage |
|---|---|---|---|---|
| Unmatched | 0.200 | 0.118 | 0.256 | 55.9% |
| Demographic | 0.223 | 0.145 | 0.280 | 60.2% |
| Demographic + ECG | 0.185 | 0.144 | 0.248 | 67.7% |
| ECG only | 0.167 | 0.137 | 0.238 | 67.8% |
| Permuted ECG only | 0.200 | 0.137 | 0.268 | 60.8% |
| Sparse | 0.154 | 0.141 | 0.220 | 73.9% |
| Sparse + ECG | 0.137 | 0.141 | 0.208 | 77.5% |
| hdPS200 | 0.132 | 0.161 | 0.221 | 80.6% |
| hdPS200 + ECG | 0.118 | 0.166 | 0.216 | 82.9% |
| Clinical (minus C) | 0.146 | 0.139 | 0.213 | 75.9% |
| Clinical + ECG | 0.130 | 0.141 | 0.203 | 79.2% |
| Oracle | 0.014 | 0.143 | 0.146 | 94.8% |

Bias is the mean of (log HR − truth) over cells. The demographic PS has a larger raw bias than unmatched because real demographic confounding partly offsets the simulated C bias in the unmatched comparison (see v1.9).

**LVEF alone** (225 cells), shown as bias / RMSE / coverage:

| Arm | Bias | RMSE | Coverage |
|---|---|---|---|
| Unmatched | 0.209 | 0.260 | 56% |
| Demographic | 0.226 | 0.281 | 61% |
| + ECG | 0.166 | 0.232 | 73% |
| ECG only | 0.158 | 0.229 | 70% |
| Sparse | 0.177 | 0.238 | 71% |
| Sparse + ECG | 0.151 | 0.220 | 76% |
| hdPS | 0.166 | 0.250 | 75% |
| hdPS + ECG | 0.146 | 0.240 | 79% |
| Clinical | 0.169 | 0.231 | 72% |
| Clinical + ECG | 0.146 | 0.215 | 77% |
| Oracle | 0.016 | 0.148 | 95% |

## 4. True-HR check

Main design, as designed; null, (1.5, 1.5) and (2, 2) scenarios; all 107 cells; 50 replicates; common random numbers. % of the demographic-PS bias removed (raw; MCSE 0.3–0.7):

| True HR | + ECG | ECG only | Oracle | Coverage (demographic / + ECG / oracle) |
|---|---|---|---|---|
| 0.6 | 14.2 | 24.9 | 94.3 | 61 / 66 / 95% |
| 0.8 | 14.2 | 24.8 | 93.7 | 59 / 65 / 95% |
| 1.0 | 14.2 | 24.7 | 93.4 | 57 / 63 / 95% |

The % removed and the bias itself (demographic PS 0.228–0.229 log HR) do not depend on the true effect.

## 5. As-designed results (full; for completeness)

**% vs unmatched, null-corrected, as designed** (higher = more treatment and higher hazard for every C):

| Arm | LVEF | NT-proBNP | BMI | eGFR | All |
|---|---|---|---|---|---|
| Demographic | −8.4 | −0.4 | −13.0 | −8.8 | −7.5 |
| + ECG | −8.7 | 17.4 | 8.8 | −24.1 | 3.8 |
| ECG only | 10.0 | 19.2 | 17.7 | −14.9 | 12.3 |
| Sparse → + ECG | −34.1 → −10.8 | 34.5 → 38.4 | 0.6 → 16.8 | −32.2 → −34.6 | 0.6 → 11.6 |
| hdPS → + ECG | −15.0 → −2.8 | 47.1 → 51.7 | 16.5 → 25.8 | −35.0 → −38.3 | 13.5 → 20.1 |
| Clinical → + ECG | −26.8 → −9.3 | 44.8 → 51.4 | −1.2 → 14.1 | −42.3 → −28.9 | 3.2 → 15.9 |
| Oracle | 92.4 | 94.0 | 88.4 | 106.8 | 93.4 |

The ECG's added share over each PS, as designed (null-corrected, all confounders): demographic 10.6, sparse 11.1, hdPS 7.6, clinical 13.1. The negative LVEF and eGFR entries for richer PS are the orientation artefact described above. The v1.9 headline numbers are reproduced exactly by this code: +ECG 14.2% raw, 10.6% null-corrected; LVEF 9.1, NT-proBNP 20.6, BMI 20.1, eGFR −4.8.

## 6. Audit checks

- **Reproduction gate:** the v1.9 arms (base, ECG, oracle) were recomputed with this code on 3 cells × 3 replicates × 10 scenarios (270 rows) for the as-designed runs (comet × LVEF, aristotle × BMI, plato × eGFR) and for the adverse runs (comet × LVEF, aristotle × LVEF, plato × eGFR). Every row matched v19 `reps.csv` / `reps_adverse.csv` exactly (max |Δ| = 0 for log HR, SE, truth, n, n_t and events) after the same CSV round trip. The first comparison, with pandas' default float parser, differed by ≤ 1e-16. That is a parser artefact, fixed with `float_precision="round_trip"`.
- **Cache identity:** for every trial, the reloaded `T.cov[T.demo]` and `T.ecg_pc` equal the v1.9 cache arrays exactly, so the patients and their order are the same. The hdPS levels are binary in all 31 trials.
- **Placebos:** the permuted-ECG-only PS removes −0.2% to 2.0% in every design.
- **Oracle:** removes 88–98% with 95% coverage in every design.
- **Summary code:** checked against the v1.9 summary.
- **Run log:** main (432,000 estimates, 13 min), trtC (324,000), hr1.0 / hr0.6 (each 81,000 estimates), adv (224,000) and trtC_adv (168,000; LVEF and eGFR cells). All ran on 40 workers of 192 cores; the machine was shared at a load of about 130.

## 7. Deviations and notes (logged)

1. **v1.9 arms reused.** They were not recomputed in the main and adverse runs: they are taken from v19 `reps.csv` / `reps_adverse.csv`, which is justified by the exact reproduction gate. The new arms use identical random streams, so all arms share subsamples, treatments and outcomes within each replicate.
2. **Clinical orientation as the primary lens (post hoc).** The adverse orientation of LVEF and eGFR was chosen after seeing the as-designed extension results, as in v1.9. Both are reported.
3. **The clinical PS uses the singly imputed baseline** (`T.X_core`, as in the real-data analyses). Only C's own analogue is removed. Correlated covariates that stay in (e.g. heart failure for LVEF, CKD for eGFR) are legitimate proxies, and part of what the clinical PS removes comes from them.
4. **hdPS ranking** uses a numpy reimplementation of `eval_longtail_balance.hdps_rank` (|log((p1 + 0.001)/(p0 + 0.001))|, stable descending sort) on the simulated treatment. Tie order may differ from pandas' stable descending sort. It is not gated, because the hdPS arms are new.
5. **trtC intercept:** recalibrated to the real treated share on the full analysis set S for each OR, like v1.9's calibration.
6. **Monte Carlo SE** of the pooled % removed comes from resampling replicates within cells (1,000 resamples). It reflects simulation error only, not uncertainty about the choice of trials.
7. **50 replicates per cell,** as in v1.9. The pooled MCSEs are ≤ 0.6 points, so more replicates were not needed for the pooled conclusions. Per-cell results are noisier; see `pooled_*.csv` for per-confounder values.
