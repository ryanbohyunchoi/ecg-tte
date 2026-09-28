# v1.9 G2: how much confounding by a held-out physiological variable does the ECG embedding remove? (2026-09-28)

**Exploratory.** This implements section G2 of `docs/v18/V19_GERMAN_STYLE_PLAN.md`. The code is `scripts/v19/g2_simulation.py`. Aggregates are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v19-g2-simulation/`. The figure is `docs/v19/G2_bias_vs_R2.png`; the two post-hoc sensitivity variants are in `G2_bias_vs_R2_adverse.png` and `G2_bias_vs_R2_conly.png`. Every cell is reported, here and in `docs/v19/G2_SIMULATION_TABLES.md`.

## Verdict (plain language)

**The ECG removes only a small part of the bias from an unmeasured physiological confounder, roughly in proportion to how well it predicts that confounder.**

- **Scale.** Pooled over 107 trial × confounder cells (31 trials), adding the 32 ECG PCs to the P1 demographic PS removes **14% of the bias** in the as-designed simulation. The two sensitivity variants give 17% and 15%.
  - The same PS with the confounder itself (the oracle) removes **93–94%**.
  - The placebos, shuffled ECG and 32 noise columns, remove **0–1.5%**.
- **Coverage.** Nominal 95% CI coverage of the truth rises only from 75% to 80% with the ECG (oracle: 95%). At the strongest confounding (OR 2 and HR 2 per SD), 95% CIs cover the truth in 39% of replicates for base matching, 45% with the ECG and 95% for the oracle.
- **Prediction sets the ceiling.**
  - The ECG's cross-fitted R² for the confounder in real data is modest. Medians: echo LVEF 0.26, BMI 0.22, NT-proBNP 0.20, eGFR 0.04. The largest value in any trial is 0.35.
  - The share of bias removed tracks R².
    - **Clinically oriented variant** (higher Cz = lower LVEF / lower eGFR): across cells, Spearman ρ = 0.84 between % removed and the partial R² given demographics. The weighted slope through the origin is 1.16, i.e. about 100 × R² %.
    - **C-only-outcome variant:** ρ = 0.86, slope 0.91.
    - **As-designed variant:** ρ = 0.51, slope 0.88.
  - So the ECG behaves like an imperfect linear proxy. It removes about as much bias as the fraction of the confounder's variance it explains, and no more. This is German et al.'s PGS conclusion transposed to the ECG.
- **Caveat on the as-designed orientation.** Here a higher value of every confounder raises both treatment and hazard. For LVEF (9%) and eGFR (−5%) the ECG removes less than R² predicts, or slightly increases bias.
  - The reason is that the real covariates kept in the outcome model are associated with LVEF / eGFR in the clinically adverse direction, for example heart failure with low LVEF. The C-driven confounding therefore has partly cancelling paths.
  - The ECG proxies mostly the part of C that shares those paths, so removing it can leave the net bias unchanged or larger.
  - With C oriented clinically (post hoc), or with the outcome depending on C alone (post hoc), the relationship is clean for LVEF (26% / 20% removed) and eGFR (7% / 4%).
- **Bottom line for the paper.** Adding the ECG to a PS cannot substitute for measuring a confounder such as LVEF, NT-proBNP or BMI. It removes roughly 10–25% of such bias when R² ≈ 0.2, and almost none for eGFR. This agrees with the real-data finding that the ECG improves balance but does not reliably move emulations toward the RCTs.

## Design (as implemented)

**Trials and confounders.** All 38 trials of `v18_af_confirm.ALL` were used. The confounders, taken from the engine's held-out matrix `T.H`, were:

| confounder | source | valid range | scale |
|---|---|---|---|
| echo LVEF | `pp_LVFUNC__ef` (echo masked before 2016-07-31) | 5–90 | as recorded |
| NT-proBNP | `pp_BNP__ntprobnp` | 5–100,000; a 9,999,999 sentinel exists | log |
| BMI | `obs_bmi` | 12–80 | as recorded |
| eGFR | `pp_LAB__egfr` | 1–200; reported values are capped at 90 in the source | as recorded |

**Analysis set S.**
- S = patients with a usable outcome and C observed. Cz is C standardised within S.
- A trial × C cell was simulated if both REAL arms in S had ≥ 300 patients. This gave **108 of 152 cells in 31 trials** (BMI 31, eGFR 30, LVEF 26, NT-proBNP 21).
- One cell, ROCKET-AF × LVEF, was excluded from every summary as an outcome-model calibration failure: the simulated null event rate was 0.9% vs 9.7% real (rule: < half the real rate). **107 cells** remain.

**Treatment (re-simulated).**
- logit P(T) = α + η_demo + log(OR_T)·Cz.
- η_demo is the real P1 PS logit, fitted on the real treatment on age, sex and index year.
- α is calibrated to the real treated share in S.
- OR_T per SD ∈ {1.25, 1.5, 2}, plus a null OR_T = 1.

**Outcome (Weibull proportional hazards).**
- lp = Zcore·β + log(HR_Y)·Cz + log(0.8)·T.
- β comes from a ridge Cox fit (penalizer 0.01) of the real outcome on the real treatment and standardised `T.X_core`. C's own analogue (lvef / bmi / creatinine) is dropped from `T.X_core`.
- The baseline is a Weibull smoothing of the Breslow hazard, as in `scripts/v13_plasmode.py`.
- λ is divided by mean(exp(log(HR_Y)·Cz)).
- HR_Y per SD ∈ {1.25, 1.5, 2}; the null scenario is OR_T = 1 with HR_Y = 1.
- Censoring is administrative: min(horizon, end of death / cause-of-death data − index). This is the v1.3 plasmode convention.
- Real ECG PCs, real covariates and real index dates are kept.
- Simulated null event rates match the real rates (median 21.0% vs 20.4%).

**Replicates.**
- 80% subsampling of S without replacement, 50 replicates per cell. This is the valid plasmode (`docs/AUDIT_2026_09_25.md`); the with-replacement bootstrap with re-matching was not used.
- In each replicate the treatment is re-drawn, every PS is refitted (L2 logistic C = 1) and every arm is re-matched: 1:1 greedy, caliper 0.2 SD of the logit, `v13_common.match`.
- The estimate is a pair-clustered robust Cox model (`v13_common.cox`).
- Total: 324,000 replicate × scenario × arm estimates per variant.

**Arms (C is in no PS except the oracle).** unmatched, P1 base, +ECG32 (`T.ecg_pc`), +shufECG32, +noise32, and the oracle (base + Cz).

**Truth and endpoints.**
- **Truth** per replicate × arm × scenario is the marginal log HR in that arm's analysed (matched) population. It is computed from counterfactual outcomes under both treatments (5 copies, common random numbers). This handles non-collapsibility.
- **bias** = mean(log HR − truth).
- **% bias removed** = 100 × (1 − Σbias_arm / Σbias_ref), with ref = base or unmatched. Per trial × C it is pooled over the 9 non-null grid cells. The replicate-resampling intervals reflect Monte Carlo error only.
- **coverage** = % of replicates with |log HR − truth| ≤ 1.96 SE.
- **Real-data R².** A 5-fold cross-fitted ridge R² of Cz on ECG32 in S, for all 152 cells. Also reported: demographics alone, demographics + ECG, and the partial R²(ECG | demo) = (R²(demo+ECG) − R²(demo)) / (1 − R²(demo)).

## Deviations and post-hoc additions (logged)

1. **Censoring.** It is administrative (v1.3 plasmode convention) rather than the real loss-to-follow-up censoring times, which are unobservable for patients with events.
2. **Eligibility.** The ≥ 300-per-arm rule uses the real arms. Simulated arms are calibrated to the same treated share.
3. **Treatment model.** It also contains the real demographic PS (η_demo), so that the P1 base arm has real demographic confounding to remove. Other real covariates enter the outcome only. Conditional on (demographics, C) there is therefore no confounding, and the oracle is correctly specified.
4. **Excluded cell.** ROCKET-AF × LVEF (calibration failure, rule above) is excluded from all summaries. Its replicates remain in `reps*.csv`.
5. **Post hoc, after seeing the as-designed results.**
   - The two sensitivity variants: "adverse" (LVEF and eGFR sign-flipped so that a higher Cz is clinically worse; the same seeds) and "conly" (Zcore·β = 0, so the outcome depends on C and treatment only).
   - The null-corrected excess bias: per arm and replicate, the scenario error minus the null-scenario error on the same subsample. This removes each arm's non-C design bias.
   - Leave-LODESTAR-out. LODESTAR's P1 base and oracle arms are biased by +0.08 to +0.13 even under the null in 3 of 4 confounders. This is a demographic-PS matching artefact; any 32 added columns remove it.
   - All of these are reported below. None changes the conclusion. The null-corrected pooled % removed by ECG is 10.6% (as designed), 14.9% (adverse) and 12.1% (C-only).

## Audit checks

- **Engine reproduction.** Before new work, the P1 base cell (full cohort, 1:1 caliper 0.2) was recomputed with `v16_engine.run_cell` and compared with `claude-v17-confirm/results_all.csv` / `claude-v18-af-confirm/results_af5.csv`. It was **identical in 38/38 trials** (max |Δlog HR| 8e-17).
- **Truth estimator.** The single-covariate Newton Cox used for the truth agrees with lifelines to 1e-8.
- **Null scenario.** With treatment depending on demographics only and no C effect, pooled bias is essentially zero and coverage is 94–95% in every matched arm:
  - as designed: base +0.002, ECG −0.003, shufECG −0.001, noise32 +0.001, oracle +0.001;
  - conly: all within ±0.005.
- **Oracle.** It removes 93–94% of the C bias with 95% coverage in every variant. The residual (about 0.004–0.03 log HR) is within-caliper imbalance.
- **Placebos.** shufECG32 and noise32 remove −1% to +1.5% overall and have R² ≤ 0.006 for every confounder.
- **Reproducibility across variants.** The NT-proBNP and BMI cells are identical in the as-designed and "adverse" variants (same sign, same seeds).

## Key results

### Pooled % of P1-base bias removed (107 cells; the 9-cell grid; ratio of summed biases)

| variant | ECG32 | shufECG32 | noise32 | oracle | coverage base → ECG (oracle) | ρ(% removed, partial R²) | slope vs 100 × R² |
|---|---|---|---|---|---|---|---|
| as designed (all C "higher = more treatment and hazard") | **14.2** | 1.5 | 0.4 | 93.5 | 75 → 80 (95) | 0.51 | 0.88 |
| adverse orientation (post hoc) | **17.1** | 0.4 | 0.3 | 93.7 | 60 → 68 (95) | 0.84 | 1.16 |
| C-only outcome (post hoc) | **14.8** | 0.1 | −0.8 | 92.9 | 74 → 79 (95) | 0.86 | 0.91 |
| as designed, null-corrected | 10.6 | −1.0 | −0.7 | 93.9 | | 0.40 | 0.71 |
| as designed, no LODESTAR | 12.0 | −0.8 | −1.9 | 93.8 | | | |

### By confounder (as designed / adverse / C-only; % of base bias removed by +ECG32)

| confounder | cells | median R²(ECG) | mean partial R² | as designed | adverse | C-only | oracle |
|---|---|---|---|---|---|---|---|
| Echo LVEF | 25 | 0.26 | 0.20 | 9.1 | 26.5 | 20.1 | 92.8–93.9 |
| NT-proBNP (log) | 21 | 0.20 | 0.18 | 20.6 | 20.6 | 17.3 | 92.9–93.0 |
| BMI | 31 | 0.22 | 0.21 | 20.1 | 20.1 | 17.1 | 91.2–92.6 |
| eGFR | 30 | 0.04 | 0.03 | −4.8 | 7.5 | 3.5 | 95.3–96.2 |

The median R² column is over all 38 trials; the mean partial R² is over the simulated cells.

- In the adverse variant, 50% of cells remove 9–25% of the base bias. The maximum is 54% (LODESTAR NT-proBNP). The ECG's R² never exceeds 0.35 in any cell.
- **% of unmatched bias removed** (requested) is reported in the tables but is hard to interpret. Real demographic confounding partly offsets the simulated C bias (mean unmatched bias 0.11 vs P1 base 0.14 as designed), so even base matching "removes" a negative share of the unmatched bias. The ECG's value vs unmatched is −8% (as designed), +7% (adverse) and +13% (C-only).

### Figure

`docs/v19/G2_bias_vs_R2.png` is analogous to German et al. Fig 3:
- **(a)** bias after P1 base matching over the OR_T × HR_Y grid;
- **(b)** % of that bias removed by +ECG32;
- **(c)** per trial × confounder % removed vs the real-data partial R², with the y = 100 × R² line, the oracle median and the shufECG placebo.

The adverse and C-only versions have the `_adverse` / `_conly` suffixes.

---

# Generated tables: as-designed variant (every cell)

## A. Audit checks

* Engine reproduction (P1 base, full cohort, 1:1 caliper 0.2) vs `claude-v17-confirm/results_all.csv` and `claude-v18-af-confirm/results_af5.csv`: 38/38 trials identical (max |Δlog HR| 8.3e-17).
* Null scenario (OR_T = 1, HR_Y = 1: treatment depends on demographics only), mean bias across trial × confounder cells: unmatched -0.016 (coverage 86%), base +0.002 (coverage 94%), ECG -0.003 (coverage 95%), shufECG -0.001 (coverage 95%), noise32 +0.001 (coverage 95%), oracle +0.001 (coverage 95%).

## B. Pooled over all trial × confounder cells (equal weight per cell)

bias = mean(log HR − truth); pooled % removed = 100 × (1 − Σ bias_arm / Σ bias_ref) over cells; median % = median of per-cell ratios; coverage = mean over cells of the 95% CI coverage of the replicate truth.

**Bias (log HR)**

| OR_T / HR_Y | unmatched | base | ECG | shufECG | noise32 | oracle |
|---|---|---|---|---|---|---|
| 1 / 1 | -0.016 | 0.002 | -0.003 | -0.001 | 0.001 | 0.001 |
| 1.25 / 1.25 | 0.014 | 0.037 | 0.027 | 0.032 | 0.034 | 0.002 |
| 1.25 / 1.5 | 0.048 | 0.072 | 0.060 | 0.070 | 0.069 | 0.006 |
| 1.25 / 2 | 0.094 | 0.117 | 0.097 | 0.115 | 0.116 | 0.008 |
| 1.5 / 1.25 | 0.035 | 0.063 | 0.056 | 0.062 | 0.062 | 0.005 |
| 1.5 / 1.5 | 0.096 | 0.124 | 0.104 | 0.121 | 0.123 | 0.008 |
| 1.5 / 2 | 0.179 | 0.207 | 0.179 | 0.205 | 0.208 | 0.012 |
| 2 / 1.25 | 0.066 | 0.098 | 0.087 | 0.096 | 0.098 | 0.005 |
| 2 / 1.5 | 0.164 | 0.196 | 0.169 | 0.196 | 0.198 | 0.014 |
| 2 / 2 | 0.298 | 0.332 | 0.287 | 0.330 | 0.334 | 0.020 |

**% of base bias removed (pooled)**

| OR_T / HR_Y | unmatched | base | ECG | shufECG | noise32 | oracle |
|---|---|---|---|---|---|---|
| 1.25 / 1.25 | 61.7 | 0.0 | 24.9 | 12.1 | 6.7 | 94.1 |
| 1.25 / 1.5 | 33.0 | 0.0 | 16.1 | 2.3 | 4.5 | 91.0 |
| 1.25 / 2 | 20.1 | 0.0 | 17.3 | 2.2 | 1.0 | 93.1 |
| 1.5 / 1.25 | 43.6 | 0.0 | 10.3 | 1.6 | 1.2 | 91.8 |
| 1.5 / 1.5 | 23.2 | 0.0 | 16.0 | 2.6 | 1.5 | 93.2 |
| 1.5 / 2 | 13.6 | 0.0 | 13.5 | 1.3 | -0.3 | 94.0 |
| 2 / 1.25 | 32.1 | 0.0 | 10.6 | 1.2 | -0.1 | 95.3 |
| 2 / 1.5 | 16.5 | 0.0 | 13.6 | -0.2 | -0.9 | 93.1 |
| 2 / 2 | 10.4 | 0.0 | 13.6 | 0.7 | -0.6 | 93.9 |

**% of unmatched bias removed (pooled)**

| OR_T / HR_Y | unmatched | base | ECG | shufECG | noise32 | oracle |
|---|---|---|---|---|---|---|
| 1.25 / 1.25 | 0.0 | -160.8 | -95.8 | -129.3 | -143.2 | 84.7 |
| 1.25 / 1.5 | 0.0 | -49.3 | -25.2 | -45.8 | -42.7 | 86.6 |
| 1.25 / 2 | 0.0 | -25.2 | -3.5 | -22.4 | -24.0 | 91.4 |
| 1.5 / 1.25 | 0.0 | -77.4 | -59.1 | -74.6 | -75.3 | 85.5 |
| 1.5 / 1.5 | 0.0 | -30.2 | -9.4 | -26.8 | -28.3 | 91.2 |
| 1.5 / 2 | 0.0 | -15.7 | -0.1 | -14.1 | -16.0 | 93.1 |
| 2 / 1.25 | 0.0 | -47.2 | -31.6 | -45.5 | -47.3 | 93.0 |
| 2 / 1.5 | 0.0 | -19.8 | -3.5 | -20.0 | -20.8 | 91.7 |
| 2 / 2 | 0.0 | -11.6 | 3.5 | -10.9 | -12.3 | 93.2 |

**Coverage of 95% CI (%)**

| OR_T / HR_Y | unmatched | base | ECG | shufECG | noise32 | oracle |
|---|---|---|---|---|---|---|
| 1 / 1 | 86.4 | 94.1 | 95.2 | 95.3 | 95.3 | 94.6 |
| 1.25 / 1.25 | 85.6 | 92.4 | 94.4 | 94.0 | 93.6 | 95.0 |
| 1.25 / 1.5 | 84.6 | 88.8 | 91.6 | 90.3 | 90.3 | 94.9 |
| 1.25 / 2 | 78.3 | 82.1 | 87.1 | 83.1 | 83.5 | 95.1 |
| 1.5 / 1.25 | 81.9 | 87.7 | 91.3 | 89.3 | 89.0 | 94.6 |
| 1.5 / 1.5 | 77.0 | 78.5 | 84.2 | 80.7 | 80.3 | 95.1 |
| 1.5 / 2 | 59.6 | 62.6 | 69.0 | 63.6 | 62.3 | 94.9 |
| 2 / 1.25 | 76.3 | 80.4 | 85.3 | 81.6 | 81.4 | 94.8 |
| 2 / 1.5 | 62.1 | 64.3 | 70.1 | 64.4 | 64.1 | 94.7 |
| 2 / 2 | 36.5 | 38.6 | 45.3 | 38.8 | 37.8 | 94.6 |

## C. By confounder (pooled over the 9 non-null grid cells; % = pooled ratio of summed biases)

| confounder | k_trials | mean_r2_ecg | mean_partial_r2 | bias_unm | bias_base | %rm_ECG | %rm_shufECG | %rm_noise32 | %rm_oracle | %rm_ECG_vs_unm | cov_base | cov_ECG | cov_oracle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Echo LVEF | 25 | 0.216 | 0.202 | 0.086 | 0.116 | 9.097 | 3.549 | 1.724 | 93.906 | -23.535 | 78.338 | 81.947 | 94.978 |
| NT-proBNP (log) | 21 | 0.203 | 0.177 | 0.191 | 0.208 | 20.558 | 0.805 | -0.365 | 92.920 | 13.572 | 62.307 | 71.386 | 94.921 |
| BMI | 31 | 0.222 | 0.207 | 0.138 | 0.170 | 20.076 | 0.280 | -0.077 | 92.562 | 1.462 | 70.588 | 77.470 | 95.068 |
| eGFR | 30 | 0.046 | 0.032 | 0.046 | 0.076 | -4.759 | 3.051 | 1.315 | 96.179 | -71.629 | 85.807 | 86.393 | 94.467 |
| all | 31 | 0.167 | 0.151 | 0.110 | 0.138 | 14.247 | 1.502 | 0.405 | 93.487 | -7.546 | 75.040 | 79.823 | 94.849 |

## D. % bias removed by +ECG32 vs the ECG's real-data R² for C (one point per trial × confounder)

y = % of base bias removed by +ECG32 (ratio of grid-summed biases); x = cross-fitted R² (r2_ecg: ECG32 alone; r2_partial: ECG32 given demographics). WLS weights = mean base bias; slope_origin = WLS slope through 0 (1.0 = removes 100 × R² %).

| conf | x | k | spearman | p | wls_intercept | wls_slope | slope_origin | mean_x | mean_prb | median_prb |
|---|---|---|---|---|---|---|---|---|---|---|
| lvef | r2_partial | 25 | -0.152 | 0.470 | 4.931 | 22.319 | 43.755 | 0.202 | 9.097 | 4.445 |
| lvef | r2_ecg | 25 | -0.112 | 0.593 | 5.378 | 18.530 | 40.707 | 0.216 | 9.097 | 4.445 |
| ntprobnp | r2_partial | 21 | 0.735 | 0.000 | -7.319 | 155.614 | 117.666 | 0.177 | 20.558 | 19.403 |
| ntprobnp | r2_ecg | 21 | 0.762 | 0.000 | -11.073 | 154.621 | 103.301 | 0.203 | 20.558 | 19.403 |
| bmi | r2_partial | 31 | 0.159 | 0.392 | 12.533 | 36.269 | 95.272 | 0.207 | 20.076 | 20.385 |
| bmi | r2_ecg | 31 | 0.193 | 0.298 | 10.289 | 44.021 | 89.584 | 0.222 | 20.076 | 20.385 |
| egfr | r2_partial | 30 | -0.415 | 0.022 | -4.308 | -15.016 | -118.385 | 0.032 | -4.759 | -6.219 |
| egfr | r2_ecg | 30 | -0.432 | 0.017 | -3.582 | -26.007 | -88.850 | 0.046 | -4.759 | -6.219 |
| all | r2_partial | 107 | 0.505 | 0.000 | -3.021 | 102.820 | 88.115 | 0.151 | 14.247 | 12.745 |
| all | r2_ecg | 107 | 0.514 | 0.000 | -4.820 | 102.718 | 80.786 | 0.167 | 14.247 | 12.745 |

## E. Every simulated trial × confounder cell

prb_* = % of base bias removed (9-cell grid; 95% replicate-resampling interval = Monte Carlo error only); pru_ECG = % of unmatched bias removed; *_strong = OR_T 2 / HR_Y 2 cell.

| trial | conf | n_obs | r2_ecg | r2_partial | r2_shuf | base_bias_grid_mean | prb_ECG | prb_ECG_lo | prb_ECG_hi | prb_shufECG | prb_noise32 | prb_oracle | pru_ECG | base_bias_strong | prb_ECG_strong |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| active-w | bmi | 1394.00 | 0.23 | 0.21 | -0.00 | 0.18 | 25.46 | 17.49 | 33.21 | -0.90 | -0.07 | 92.95 | -381.85 | 0.49 | 23.45 |
| active-w | egfr | 1199.00 | 0.02 | 0.02 | -0.00 | 0.06 | -10.65 | -44.31 | 13.38 | 18.19 | 5.81 | 130.66 | 287.26 | 0.26 | 6.89 |
| active-w | lvef | 908.00 | 0.29 | 0.28 | -0.01 | 0.08 | 9.28 | -9.26 | 28.09 | 10.01 | -7.88 | 96.35 | -368.04 | 0.22 | 17.18 |
| af-chf | bmi | 2880.00 | 0.24 | 0.22 | -0.00 | 0.15 | 10.11 | 2.22 | 17.84 | 0.62 | -7.93 | 93.83 | -272.71 | 0.42 | 14.14 |
| af-chf | egfr | 2813.00 | 0.03 | 0.03 | -0.00 | 0.07 | 12.74 | -1.51 | 26.00 | 19.45 | 5.25 | 95.79 | 377.12 | 0.23 | 3.29 |
| af-chf | lvef | 1295.00 | 0.04 | 0.03 | -0.00 | 0.12 | 0.05 | -8.45 | 8.12 | 7.65 | -1.44 | 104.27 | -88.59 | 0.29 | 0.86 |
| af-chf | ntprobnp | 2305.00 | 0.21 | 0.20 | -0.00 | 0.20 | 21.63 | 14.98 | 27.71 | 3.50 | 3.37 | 100.31 | -25.78 | 0.41 | 22.44 |
| affirm | bmi | 9178.00 | 0.23 | 0.22 | -0.00 | 0.21 | 23.82 | 20.67 | 26.64 | 2.77 | 4.10 | 94.21 | -25.10 | 0.50 | 23.40 |
| affirm | egfr | 8868.00 | 0.06 | 0.06 | -0.00 | 0.07 | -2.47 | -11.08 | 4.70 | 5.26 | 1.05 | 101.27 | -281.30 | 0.19 | 1.62 |
| affirm | lvef | 7842.00 | 0.27 | 0.25 | 0.00 | 0.09 | 4.77 | -0.67 | 9.97 | 2.31 | 1.97 | 106.59 | -110.64 | 0.23 | 12.35 |
| affirm | ntprobnp | 5525.00 | 0.21 | 0.20 | -0.00 | 0.20 | 19.73 | 17.38 | 22.10 | -2.59 | -1.08 | 96.39 | 9.84 | 0.42 | 21.07 |
| allhat | bmi | 10212.00 | 0.25 | 0.24 | -0.00 | 0.19 | 26.82 | 23.33 | 30.67 | -0.58 | -0.87 | 98.87 | 24.79 | 0.45 | 26.87 |
| allhat | egfr | 9611.00 | 0.02 | 0.01 | -0.00 | 0.09 | -1.30 | -15.40 | 10.13 | -4.81 | 1.98 | 104.92 | 35.07 | 0.24 | -1.77 |
| allhat | lvef | 5084.00 | 0.08 | 0.06 | -0.00 | 0.15 | -2.39 | -13.67 | 8.32 | -7.89 | -4.20 | 95.10 | 20.84 | 0.35 | -5.98 |
| allhat | ntprobnp | 2169.00 | 0.13 | 0.10 | -0.00 | 0.24 | 14.73 | 5.57 | 23.37 | 6.55 | -6.00 | 94.98 | 33.33 | 0.50 | 10.98 |
| amplify | bmi | 2314.00 | 0.24 | 0.22 | -0.00 | 0.15 | 20.79 | 12.06 | 28.75 | 1.58 | 1.99 | 85.48 | -78.40 | 0.37 | 25.40 |
| amplify | egfr | 3096.00 | 0.06 | 0.04 | -0.00 | 0.12 | -11.40 | -28.80 | 3.85 | -9.48 | -7.84 | 85.69 | 44.50 | 0.31 | 1.23 |
| amplify | ntprobnp | 2167.00 | 0.19 | 0.17 | -0.00 | 0.21 | 14.94 | 8.66 | 21.19 | -4.40 | -5.56 | 92.04 | 44.99 | 0.47 | 12.05 |
| aristotle | bmi | 8405.00 | 0.24 | 0.23 | -0.00 | 0.17 | 20.94 | 13.55 | 28.26 | -3.11 | -5.73 | 91.48 | 20.35 | 0.46 | 21.93 |
| aristotle | egfr | 8675.00 | 0.07 | 0.07 | 0.00 | 0.08 | -25.17 | -42.48 | -10.65 | 0.80 | -3.04 | 97.77 | -11.88 | 0.29 | -5.95 |
| aristotle | lvef | 7793.00 | 0.27 | 0.26 | -0.00 | 0.14 | 15.64 | 5.74 | 24.36 | 3.94 | -0.12 | 104.60 | 27.66 | 0.34 | 16.50 |
| aristotle | ntprobnp | 5183.00 | 0.21 | 0.20 | -0.00 | 0.24 | 24.54 | 19.01 | 29.64 | -3.06 | -1.51 | 106.90 | 6.23 | 0.53 | 20.75 |
| ascot | bmi | 9936.00 | 0.26 | 0.26 | -0.00 | 0.21 | 15.30 | 13.17 | 17.46 | 0.87 | -1.15 | 73.24 | 8.31 | 0.52 | 14.73 |
| ascot | egfr | 9231.00 | 0.02 | 0.02 | -0.00 | 0.05 | -0.39 | -6.39 | 6.00 | 3.26 | 0.31 | 111.86 | -134.31 | 0.16 | -3.58 |
| ascot | lvef | 4550.00 | 0.07 | 0.06 | -0.00 | 0.13 | 4.44 | -3.83 | 12.43 | -0.58 | 3.37 | 94.39 | -9.07 | 0.38 | 10.81 |
| ascot | ntprobnp | 1887.00 | 0.11 | 0.09 | -0.00 | 0.21 | 6.42 | 2.46 | 10.32 | -0.31 | -2.81 | 82.89 | 6.33 | 0.49 | 8.82 |
| cabana-v2 | bmi | 7068.00 | 0.21 | 0.21 | -0.00 | 0.19 | 25.52 | 21.32 | 29.38 | -2.01 | -2.77 | 96.65 | -113.81 | 0.48 | 23.53 |
| cabana-v2 | egfr | 6357.00 | 0.08 | 0.08 | -0.00 | 0.03 | -65.25 | -154.93 | -21.65 | -1.94 | -1.36 | 119.10 | 150.42 | 0.15 | -16.29 |
| cabana-v2 | lvef | 6440.00 | 0.28 | 0.27 | -0.00 | 0.09 | -8.18 | -21.62 | 3.55 | -1.04 | 6.11 | 94.90 | 238.52 | 0.22 | 9.38 |
| carmelina | bmi | 743.00 | 0.23 | 0.19 | -0.00 | 0.17 | 23.96 | 16.15 | 31.99 | -0.97 | 2.78 | 93.47 | 23.13 | 0.38 | 22.70 |
| carmelina | egfr | 816.00 | 0.05 | 0.02 | -0.01 | 0.15 | 3.95 | -4.54 | 11.95 | 2.68 | 2.84 | 92.43 | -3.33 | 0.33 | 5.36 |
| carolina | bmi | 754.00 | 0.22 | 0.18 | -0.01 | 0.15 | 17.69 | 10.18 | 25.59 | 5.64 | 2.72 | 72.06 | 25.58 | 0.32 | 19.65 |
| comet | bmi | 2535.00 | 0.21 | 0.21 | -0.00 | 0.15 | 15.81 | 12.60 | 19.10 | -2.22 | -2.55 | 81.07 | 34.24 | 0.37 | 14.42 |
| comet | egfr | 3358.00 | 0.04 | 0.03 | -0.00 | 0.09 | 0.82 | -4.06 | 5.45 | -2.56 | 1.69 | 48.46 | 43.65 | 0.22 | 1.46 |
| comet | lvef | 3765.00 | 0.26 | 0.24 | -0.00 | 0.22 | 13.24 | 11.34 | 15.02 | -0.70 | 0.07 | 74.70 | 48.65 | 0.46 | 13.34 |
| comet | ntprobnp | 3096.00 | 0.18 | 0.18 | 0.00 | 0.18 | 8.52 | 6.59 | 10.49 | -1.38 | -1.20 | 67.44 | 54.81 | 0.37 | 10.69 |
| declare | bmi | 3382.00 | 0.20 | 0.18 | -0.00 | 0.15 | 6.54 | 1.07 | 11.71 | -13.31 | -13.12 | 78.55 | 64.12 | 0.37 | 13.73 |
| declare | egfr | 2666.00 | 0.05 | 0.01 | -0.00 | 0.06 | -43.66 | -71.35 | -24.00 | -23.12 | -24.46 | 135.86 | 65.59 | 0.18 | -12.60 |
| declare | lvef | 1895.00 | 0.34 | 0.31 | -0.00 | 0.00 | -4597.42 | -12410.63 | 11088.66 | -3778.64 | -3788.80 | -49.79 | 49.88 | 0.15 | -32.27 |
| declare | ntprobnp | 1466.00 | 0.30 | 0.24 | -0.00 | 0.19 | 22.70 | 15.07 | 29.75 | -18.84 | -17.85 | 92.64 | 53.40 | 0.40 | 23.59 |
| east-afnet4 | bmi | 8144.00 | 0.24 | 0.24 | -0.00 | 0.18 | 19.68 | 16.63 | 22.68 | -0.06 | 2.26 | 98.08 | 0.62 | 0.39 | 19.31 |
| east-afnet4 | egfr | 8368.00 | 0.07 | 0.07 | -0.00 | 0.03 | -62.92 | -89.71 | -43.97 | -7.02 | -19.95 | 119.87 | -388.31 | 0.15 | -5.54 |
| east-afnet4 | lvef | 7772.00 | 0.29 | 0.27 | -0.00 | 0.07 | -15.42 | -24.56 | -6.89 | -1.72 | -0.26 | 97.92 | -60.45 | 0.21 | 4.68 |
| east-afnet4 | ntprobnp | 5369.00 | 0.21 | 0.20 | -0.00 | 0.21 | 26.30 | 24.03 | 28.58 | 0.72 | 0.21 | 100.11 | 24.87 | 0.42 | 24.06 |
| elite-ii | bmi | 1174.00 | 0.20 | 0.20 | 0.00 | 0.17 | 16.68 | 9.10 | 23.31 | 1.90 | 4.19 | 71.65 | 44.21 | 0.38 | 27.11 |
| elite-ii | egfr | 1332.00 | 0.02 | 0.02 | -0.00 | 0.10 | -20.09 | -38.90 | -5.05 | -11.90 | -24.56 | 92.31 | 28.87 | 0.29 | -0.41 |
| elite-ii | lvef | 868.00 | 0.07 | 0.07 | 0.00 | 0.18 | 13.73 | 0.53 | 25.46 | 1.40 | -2.87 | 70.25 | 63.92 | 0.32 | 12.11 |
| elite-ii | ntprobnp | 1160.00 | 0.21 | 0.22 | -0.00 | 0.18 | 18.95 | 11.83 | 25.89 | -1.91 | -0.85 | 77.89 | 51.40 | 0.36 | 14.90 |
| empa-reg | bmi | 3289.00 | 0.18 | 0.16 | -0.00 | 0.15 | 20.39 | 15.57 | 25.56 | 1.16 | 1.61 | 89.08 | -13.97 | 0.38 | 12.82 |
| empa-reg | egfr | 2688.00 | 0.08 | 0.04 | -0.00 | 0.07 | -14.47 | -26.11 | -5.28 | -2.56 | 3.27 | 103.93 | -1488.43 | 0.23 | -2.76 |
| empa-reg | lvef | 2242.00 | 0.35 | 0.35 | -0.00 | 0.05 | -13.52 | -37.41 | 3.73 | -18.84 | -10.84 | 122.34 | -130.50 | 0.18 | 11.56 |
| empa-reg | ntprobnp | 1720.00 | 0.28 | 0.24 | -0.00 | 0.25 | 30.00 | 25.11 | 34.71 | 2.38 | -0.50 | 91.17 | 33.25 | 0.45 | 25.26 |
| emperor-preserved-v2 | bmi | 1457.00 | 0.22 | 0.17 | -0.00 | 0.11 | 28.85 | 20.59 | 36.76 | 1.83 | 10.10 | 103.31 | -47.74 | 0.28 | 30.00 |
| emperor-preserved-v2 | egfr | 1430.00 | 0.04 | 0.01 | -0.00 | 0.08 | -5.87 | -16.45 | 4.33 | -6.69 | -6.84 | 101.10 | -519.84 | 0.26 | 6.55 |
| emperor-preserved-v2 | lvef | 1517.00 | 0.10 | 0.09 | -0.00 | 0.12 | 2.27 | -4.64 | 8.70 | -3.15 | -8.78 | 106.15 | -171.14 | 0.30 | 4.59 |
| emperor-preserved-v2 | ntprobnp | 1307.00 | 0.20 | 0.15 | -0.00 | 0.17 | 14.25 | 8.41 | 19.91 | -4.29 | -2.95 | 100.46 | -169.88 | 0.35 | 7.12 |
| frail-af | bmi | 2062.00 | 0.19 | 0.17 | -0.00 | 0.23 | 13.91 | 3.92 | 23.08 | -6.97 | -5.31 | 105.79 | 28.90 | 0.55 | 9.95 |
| frail-af | egfr | 1658.00 | 0.01 | 0.02 | -0.00 | 0.09 | -0.50 | -29.36 | 20.41 | -6.32 | -6.00 | 89.63 | 9.38 | 0.21 | 0.97 |
| laaos3 | bmi | 1830.00 | 0.18 | 0.18 | -0.00 | 0.20 | 17.73 | 7.91 | 26.83 | 0.21 | -3.33 | 109.96 | 19.88 | 0.48 | 22.68 |
| laaos3 | egfr | 1554.00 | 0.04 | 0.05 | -0.00 | 0.02 | -61.34 | -838.63 | 521.13 | 9.22 | 0.95 | 202.72 | -416.85 | 0.10 | -27.51 |
| laaos3 | lvef | 1879.00 | 0.26 | 0.25 | -0.00 | 0.10 | 22.11 | 1.57 | 40.11 | 20.57 | -3.72 | 106.27 | 12.62 | 0.27 | 8.99 |
| life | bmi | 1332.00 | 0.26 | 0.24 | -0.00 | 0.18 | 15.70 | 6.47 | 23.80 | -4.28 | -2.47 | 88.63 | 11.26 | 0.45 | 14.23 |
| life | egfr | 1156.00 | 0.01 | 0.01 | -0.00 | 0.07 | 9.77 | -14.52 | 31.55 | 9.57 | 12.88 | 118.49 | -74.16 | 0.15 | 10.23 |
| lodestar | bmi | 9345.00 | 0.24 | 0.24 | -0.00 | 0.18 | 29.83 | 26.28 | 33.27 | 9.35 | 8.41 | 98.76 | -117.23 | 0.36 | 14.49 |
| lodestar | egfr | 8908.00 | 0.08 | 0.06 | 0.00 | 0.17 | 47.22 | 43.18 | 51.23 | 48.45 | 48.43 | 57.97 | -325.75 | 0.28 | 15.11 |
| lodestar | lvef | 6780.00 | 0.29 | 0.28 | -0.00 | 0.25 | 61.18 | 58.06 | 64.36 | 57.33 | 56.33 | 92.39 | -71.12 | 0.44 | 52.53 |
| lodestar | ntprobnp | 3981.00 | 0.28 | 0.26 | -0.00 | 0.27 | 53.70 | 50.91 | 56.73 | 31.34 | 31.22 | 96.69 | -7.79 | 0.44 | 35.68 |
| ontarget | bmi | 5205.00 | 0.24 | 0.22 | -0.00 | 0.12 | 15.65 | 12.83 | 18.79 | -0.51 | 0.58 | 95.72 | -36.02 | 0.33 | 14.76 |
| ontarget | egfr | 4934.00 | 0.02 | 0.01 | -0.00 | 0.08 | -1.03 | -7.73 | 4.72 | 2.49 | 1.91 | 98.92 | -56.91 | 0.18 | 0.02 |
| ontarget | lvef | 3184.00 | 0.20 | 0.18 | -0.00 | 0.15 | 18.39 | 14.24 | 22.22 | 4.76 | 4.16 | 89.42 | 4.24 | 0.34 | 16.80 |
| ontarget | ntprobnp | 1166.00 | 0.14 | 0.10 | -0.00 | 0.21 | 12.37 | 9.49 | 15.53 | -0.70 | 4.08 | 78.45 | 14.97 | 0.43 | 9.81 |
| paradigm-hf-seq | bmi | 2716.00 | 0.22 | 0.20 | 0.00 | 0.17 | 15.93 | 11.29 | 20.44 | 6.70 | -2.19 | 100.05 | 12.50 | 0.39 | 15.77 |
| paradigm-hf-seq | egfr | 2806.00 | 0.02 | 0.02 | -0.00 | 0.07 | -7.84 | -19.83 | 2.60 | -2.45 | -0.06 | 109.67 | -46.53 | 0.20 | 2.35 |
| paradigm-hf-seq | lvef | 1895.00 | 0.09 | 0.08 | -0.00 | 0.14 | 3.60 | 0.53 | 6.44 | -2.46 | -2.89 | 86.05 | 9.07 | 0.32 | 4.45 |
| paradigm-hf-seq | ntprobnp | 2243.00 | 0.18 | 0.17 | -0.00 | 0.18 | 20.95 | 18.10 | 23.69 | -2.71 | -0.12 | 94.04 | 7.07 | 0.36 | 18.07 |
| plato | bmi | 2432.00 | 0.18 | 0.17 | -0.00 | 0.16 | 18.59 | 14.52 | 22.67 | 1.24 | 0.52 | 93.42 | 3.83 | 0.39 | 17.56 |
| plato | egfr | 2689.00 | 0.09 | 0.06 | -0.00 | 0.03 | -39.04 | -84.70 | -17.67 | 8.83 | 3.38 | 82.25 | 188.04 | 0.19 | -5.38 |
| plato | lvef | 2274.00 | 0.22 | 0.21 | -0.00 | 0.09 | -4.01 | -8.97 | 0.76 | -0.43 | -0.30 | 91.92 | -345.65 | 0.27 | 2.26 |
| plato | ntprobnp | 1334.00 | 0.25 | 0.22 | -0.00 | 0.25 | 19.40 | 16.84 | 22.23 | -1.24 | -2.09 | 79.41 | 11.08 | 0.51 | 17.42 |
| precision | bmi | 2955.00 | 0.25 | 0.23 | -0.00 | 0.16 | 21.98 | 17.76 | 26.29 | 0.64 | 0.82 | 87.09 | 3.63 | 0.41 | 19.09 |
| precision | egfr | 2246.00 | 0.03 | 0.01 | -0.00 | 0.08 | -2.56 | -10.73 | 5.54 | 4.36 | 1.82 | 63.51 | 19.08 | 0.25 | 1.62 |
| precision | lvef | 1084.00 | 0.20 | 0.17 | -0.01 | 0.12 | 12.45 | 0.44 | 24.36 | 6.18 | 11.64 | 86.64 | -30.58 | 0.28 | 2.94 |
| raft-af | bmi | 1857.00 | 0.25 | 0.23 | -0.00 | 0.16 | 22.49 | 17.23 | 27.18 | 4.30 | 4.34 | 93.49 | 1.62 | 0.36 | 19.00 |
| raft-af | egfr | 1810.00 | 0.02 | 0.02 | -0.00 | 0.07 | -6.57 | -19.28 | 4.98 | -11.78 | -1.79 | 99.15 | -1876.90 | 0.22 | 11.74 |
| raft-af | lvef | 1733.00 | 0.23 | 0.20 | -0.00 | 0.10 | 14.86 | 6.31 | 23.04 | -3.67 | -3.10 | 112.99 | 297.67 | 0.25 | 16.53 |
| raft-af | ntprobnp | 1532.00 | 0.17 | 0.16 | -0.00 | 0.19 | 18.26 | 13.35 | 22.99 | 4.03 | -2.59 | 98.44 | -334.37 | 0.41 | 21.05 |
| rewind | bmi | 2829.00 | 0.19 | 0.18 | 0.00 | 0.19 | 19.87 | 13.55 | 25.69 | -3.45 | -2.72 | 90.87 | -356.63 | 0.47 | 19.53 |
| rewind | egfr | 2557.00 | 0.09 | 0.04 | -0.00 | 0.06 | -22.81 | -50.97 | -4.23 | -7.43 | -3.40 | 92.27 | 171.72 | 0.16 | -2.28 |
| rewind | lvef | 1378.00 | 0.28 | 0.26 | -0.00 | 0.10 | 2.44 | -13.47 | 16.32 | -4.22 | -12.72 | 89.83 | 345.79 | 0.22 | -1.26 |
| rocket-af | bmi | 3109.00 | 0.25 | 0.24 | -0.00 | 0.15 | 24.66 | 18.75 | 30.70 | 5.51 | 6.77 | 97.23 | -11.02 | 0.39 | 25.11 |
| rocket-af | egfr | 2486.00 | 0.05 | 0.04 | -0.00 | 0.05 | -14.21 | -39.66 | 2.68 | -14.08 | -11.92 | 106.86 | -35.19 | 0.21 | -5.29 |
| rocket-af | ntprobnp | 1417.00 | 0.19 | 0.19 | -0.00 | 0.20 | 19.94 | 14.88 | 24.66 | -0.65 | -3.33 | 87.46 | 3.69 | 0.40 | 11.56 |
| sustain6 | bmi | 2224.00 | 0.16 | 0.14 | -0.00 | 0.16 | 25.74 | 17.79 | 33.87 | 7.62 | 6.69 | 99.68 | -111.12 | 0.50 | 23.56 |
| sustain6 | egfr | 2024.00 | 0.06 | 0.03 | -0.00 | 0.07 | 1.66 | -16.29 | 18.42 | 19.72 | 10.24 | 133.29 | 137.80 | 0.22 | 13.67 |
| sustain6 | lvef | 1427.00 | 0.26 | 0.25 | -0.00 | 0.07 | 0.05 | -21.85 | 18.68 | -3.01 | 3.14 | 97.91 | 139.27 | 0.20 | 12.70 |
| sustain6 | ntprobnp | 905.00 | 0.23 | 0.18 | 0.01 | 0.21 | 27.55 | 17.46 | 36.78 | 1.49 | 3.53 | 115.38 | 186.01 | 0.45 | 23.00 |
| tecos | bmi | 1365.00 | 0.18 | 0.16 | -0.01 | 0.14 | 11.04 | 6.19 | 15.93 | 0.30 | -2.44 | 88.39 | 12.60 | 0.38 | 11.73 |
| tecos | egfr | 1073.00 | 0.07 | 0.03 | -0.00 | 0.10 | -4.98 | -13.42 | 2.70 | -10.09 | -6.95 | 84.73 | 15.42 | 0.26 | 3.78 |
| tecos | lvef | 734.00 | 0.28 | 0.26 | -0.01 | 0.10 | -0.23 | -12.25 | 10.56 | 1.26 | -4.55 | 89.53 | 25.13 | 0.25 | 8.77 |
| transform-hf | bmi | 6370.00 | 0.24 | 0.22 | -0.00 | 0.17 | 23.89 | 14.86 | 33.20 | -3.74 | -3.63 | 105.85 | 5.38 | 0.54 | 13.24 |
| transform-hf | egfr | 7257.00 | 0.03 | 0.02 | -0.00 | 0.10 | 1.16 | -20.23 | 18.00 | 9.57 | -6.15 | 92.24 | -48.95 | 0.20 | -17.43 |
| transform-hf | lvef | 6141.00 | 0.29 | 0.26 | -0.00 | 0.11 | 22.91 | 9.45 | 35.83 | -2.07 | -1.31 | 112.61 | 18.81 | 0.26 | 34.76 |
| transform-hf | ntprobnp | 5917.00 | 0.20 | 0.17 | -0.00 | 0.18 | 9.70 | -0.15 | 18.45 | -0.70 | -6.95 | 99.24 | 24.99 | 0.38 | 8.84 |
| value | bmi | 10152.00 | 0.26 | 0.25 | -0.00 | 0.19 | 24.64 | 22.49 | 26.91 | 1.51 | 0.35 | 93.57 | -45.42 | 0.44 | 19.44 |
| value | egfr | 9310.00 | 0.03 | 0.02 | -0.00 | 0.06 | -8.15 | -18.00 | 0.60 | 5.40 | 2.31 | 109.99 | 456.66 | 0.15 | -7.71 |
| value | lvef | 4628.00 | 0.11 | 0.09 | -0.00 | 0.14 | 5.49 | 1.97 | 9.04 | 1.00 | 0.04 | 89.27 | -66.89 | 0.31 | -1.27 |
| value | ntprobnp | 2084.00 | 0.16 | 0.09 | -0.00 | 0.20 | 10.65 | 5.80 | 15.28 | -3.13 | -6.04 | 96.81 | 18.66 | 0.44 | 15.14 |

## F. Real-data R² of the ECG for each confounder, all 38 trials × 4 confounders (incl. skipped cells)

Cross-fitted (5-fold) ridge R² in patients with C observed (and a usable outcome); n_obs_t / n_obs_c = real arms. eligible = both real arms ≥ 300 (simulated). smd_real = real-data standardised difference in C (treated − control).

| trial | conf | n_obs_t | n_obs_c | eligible | r2_ecg | r2_demo | r2_demo_ecg | r2_partial | r2_shuf | r2_noise | smd_real |
|---|---|---|---|---|---|---|---|---|---|---|---|
| comet | lvef | 1491.000 | 2274.000 | True | 0.264 | 0.047 | 0.273 | 0.238 | -0.001 | -0.002 | 0.536 |
| comet | ntprobnp | 1236.000 | 1860.000 | True | 0.180 | 0.054 | 0.220 | 0.175 | 0.000 | -0.002 | -0.124 |
| comet | bmi | 1079.000 | 1456.000 | True | 0.213 | 0.057 | 0.259 | 0.214 | -0.003 | -0.003 | -0.031 |
| comet | egfr | 1394.000 | 1964.000 | True | 0.036 | 0.015 | 0.044 | 0.029 | -0.001 | -0.002 | 0.121 |
| paradigm-hf-seq | lvef | 851.000 | 1044.000 | True | 0.090 | 0.017 | 0.100 | 0.084 | -0.003 | -0.000 | -0.303 |
| paradigm-hf-seq | ntprobnp | 751.000 | 1492.000 | True | 0.184 | 0.065 | 0.222 | 0.168 | -0.003 | -0.004 | 0.317 |
| paradigm-hf-seq | bmi | 634.000 | 2082.000 | True | 0.215 | 0.078 | 0.262 | 0.199 | 0.002 | -0.002 | 0.062 |
| paradigm-hf-seq | egfr | 695.000 | 2111.000 | True | 0.023 | 0.021 | 0.036 | 0.015 | -0.002 | 0.001 | -0.002 |
| transform-hf | lvef | 378.000 | 5763.000 | True | 0.285 | 0.041 | 0.293 | 0.263 | -0.000 | -0.001 | -0.144 |
| transform-hf | ntprobnp | 356.000 | 5561.000 | True | 0.199 | 0.080 | 0.241 | 0.175 | -0.002 | -0.000 | 0.156 |
| transform-hf | bmi | 391.000 | 5979.000 | True | 0.243 | 0.124 | 0.314 | 0.218 | -0.001 | -0.001 | 0.434 |
| transform-hf | egfr | 337.000 | 6920.000 | True | 0.033 | 0.028 | 0.048 | 0.021 | -0.002 | -0.001 | -0.559 |
| elite-ii | lvef | 453.000 | 415.000 | True | 0.074 | -0.002 | 0.071 | 0.073 | 0.004 | -0.001 | -0.112 |
| elite-ii | ntprobnp | 549.000 | 611.000 | True | 0.215 | 0.037 | 0.250 | 0.221 | -0.005 | -0.004 | -0.047 |
| elite-ii | bmi | 560.000 | 614.000 | True | 0.202 | 0.057 | 0.246 | 0.200 | 0.003 | -0.000 | 0.059 |
| elite-ii | egfr | 658.000 | 674.000 | True | 0.023 | 0.007 | 0.031 | 0.024 | -0.003 | -0.002 | -0.154 |
| life | lvef | 255.000 | 488.000 | False | 0.052 | 0.023 | 0.058 | 0.036 | -0.001 | -0.003 | -0.040 |
| life | ntprobnp | 110.000 | 218.000 | False | 0.049 | 0.023 | 0.074 | 0.052 | -0.013 | -0.012 | -0.198 |
| life | bmi | 494.000 | 838.000 | True | 0.257 | 0.068 | 0.296 | 0.245 | -0.001 | -0.004 | 0.103 |
| life | egfr | 444.000 | 712.000 | True | 0.013 | -0.001 | 0.011 | 0.012 | -0.004 | -0.002 | -0.096 |
| plato | lvef | 1247.000 | 1027.000 | True | 0.215 | 0.009 | 0.219 | 0.211 | -0.002 | -0.003 | 0.119 |
| plato | ntprobnp | 642.000 | 692.000 | True | 0.251 | 0.063 | 0.267 | 0.218 | -0.001 | -0.001 | -0.310 |
| plato | bmi | 1374.000 | 1058.000 | True | 0.184 | 0.085 | 0.242 | 0.172 | -0.003 | -0.003 | 0.052 |
| plato | egfr | 1524.000 | 1165.000 | True | 0.089 | 0.042 | 0.102 | 0.063 | -0.002 | -0.003 | 0.185 |
| aristotle | lvef | 6872.000 | 921.000 | True | 0.270 | 0.030 | 0.277 | 0.255 | -0.001 | -0.002 | 0.128 |
| aristotle | ntprobnp | 4481.000 | 702.000 | True | 0.207 | 0.045 | 0.233 | 0.197 | -0.002 | -0.000 | -0.141 |
| aristotle | bmi | 6985.000 | 1420.000 | True | 0.238 | 0.085 | 0.297 | 0.232 | -0.002 | -0.001 | 0.006 |
| aristotle | egfr | 7542.000 | 1133.000 | True | 0.073 | 0.012 | 0.081 | 0.070 | 0.001 | -0.001 | 0.187 |
| rocket-af | lvef | 1120.000 | 942.000 | True | 0.288 | 0.029 | 0.300 | 0.279 | -0.003 | -0.005 | 0.179 |
| rocket-af | ntprobnp | 694.000 | 723.000 | True | 0.194 | 0.041 | 0.219 | 0.185 | -0.001 | -0.003 | -0.438 |
| rocket-af | bmi | 1664.000 | 1445.000 | True | 0.248 | 0.084 | 0.299 | 0.235 | -0.002 | -0.003 | 0.110 |
| rocket-af | egfr | 1333.000 | 1153.000 | True | 0.049 | 0.017 | 0.056 | 0.040 | -0.003 | -0.004 | 0.467 |
| rely | lvef | 115.000 | 966.000 | False | 0.330 | 0.035 | 0.335 | 0.311 | -0.002 | 0.006 | 0.248 |
| rely | ntprobnp | 117.000 | 734.000 | False | 0.120 | 0.042 | 0.152 | 0.115 | -0.001 | -0.003 | -0.326 |
| rely | bmi | 195.000 | 1473.000 | False | 0.216 | 0.048 | 0.253 | 0.215 | -0.003 | -0.001 | -0.101 |
| rely | egfr | 268.000 | 1184.000 | False | 0.060 | 0.000 | 0.060 | 0.060 | -0.001 | -0.001 | 0.433 |
| allhat | lvef | 3684.000 | 1400.000 | True | 0.078 | 0.033 | 0.089 | 0.058 | -0.001 | -0.003 | -0.002 |
| allhat | ntprobnp | 1663.000 | 506.000 | True | 0.133 | 0.088 | 0.179 | 0.100 | -0.002 | -0.003 | 0.363 |
| allhat | bmi | 6729.000 | 3483.000 | True | 0.250 | 0.074 | 0.297 | 0.241 | -0.001 | -0.000 | -0.286 |
| allhat | egfr | 7006.000 | 2605.000 | True | 0.020 | 0.018 | 0.030 | 0.012 | -0.001 | -0.001 | -0.191 |
| emperor-preserved-v2 | lvef | 1057.000 | 460.000 | True | 0.100 | 0.050 | 0.132 | 0.086 | -0.002 | -0.001 | -0.304 |
| emperor-preserved-v2 | ntprobnp | 868.000 | 439.000 | True | 0.197 | 0.107 | 0.243 | 0.152 | -0.002 | -0.005 | -0.066 |
| emperor-preserved-v2 | bmi | 983.000 | 474.000 | True | 0.215 | 0.167 | 0.310 | 0.171 | -0.002 | -0.004 | 0.154 |
| emperor-preserved-v2 | egfr | 929.000 | 501.000 | True | 0.041 | 0.080 | 0.093 | 0.014 | -0.002 | -0.003 | 0.194 |
| east-afnet4 | lvef | 1835.000 | 5937.000 | True | 0.287 | 0.034 | 0.296 | 0.272 | -0.000 | -0.001 | -0.243 |
| east-afnet4 | ntprobnp | 1238.000 | 4131.000 | True | 0.214 | 0.063 | 0.249 | 0.198 | -0.001 | -0.002 | 0.216 |
| east-afnet4 | bmi | 1871.000 | 6273.000 | True | 0.242 | 0.088 | 0.303 | 0.236 | -0.002 | -0.002 | 0.023 |
| east-afnet4 | egfr | 1840.000 | 6528.000 | True | 0.073 | 0.017 | 0.085 | 0.069 | -0.001 | -0.001 | -0.006 |
| cabana-v2 | lvef | 760.000 | 5680.000 | True | 0.285 | 0.028 | 0.293 | 0.273 | -0.002 | 0.000 | 0.173 |
| cabana-v2 | ntprobnp | 283.000 | 3899.000 | False | 0.184 | 0.048 | 0.216 | 0.177 | -0.002 | -0.000 | -0.543 |
| cabana-v2 | bmi | 1048.000 | 6020.000 | True | 0.209 | 0.080 | 0.270 | 0.206 | -0.001 | -0.001 | 0.120 |
| cabana-v2 | egfr | 610.000 | 5747.000 | True | 0.083 | 0.023 | 0.099 | 0.077 | -0.001 | -0.001 | 0.419 |
| ontarget | lvef | 1563.000 | 1621.000 | True | 0.198 | 0.021 | 0.202 | 0.185 | -0.000 | -0.002 | 0.185 |
| ontarget | ntprobnp | 524.000 | 642.000 | True | 0.138 | 0.083 | 0.175 | 0.101 | -0.004 | -0.001 | -0.012 |
| ontarget | bmi | 2744.000 | 2461.000 | True | 0.241 | 0.093 | 0.292 | 0.219 | -0.003 | -0.001 | 0.047 |
| ontarget | egfr | 2437.000 | 2497.000 | True | 0.024 | 0.023 | 0.036 | 0.013 | -0.002 | -0.001 | -0.143 |
| value | lvef | 1833.000 | 2795.000 | True | 0.106 | 0.035 | 0.119 | 0.086 | -0.000 | -0.002 | -0.155 |
| value | ntprobnp | 554.000 | 1530.000 | True | 0.160 | 0.143 | 0.218 | 0.088 | -0.000 | -0.003 | -0.247 |
| value | bmi | 3981.000 | 6171.000 | True | 0.260 | 0.079 | 0.308 | 0.249 | -0.002 | -0.002 | 0.130 |
| value | egfr | 3077.000 | 6233.000 | True | 0.032 | 0.024 | 0.042 | 0.018 | -0.000 | -0.001 | 0.231 |
| ascot | lvef | 1889.000 | 2661.000 | True | 0.071 | 0.024 | 0.079 | 0.056 | -0.002 | -0.001 | 0.164 |
| ascot | ntprobnp | 966.000 | 921.000 | True | 0.115 | 0.057 | 0.146 | 0.095 | -0.002 | -0.002 | -0.144 |
| ascot | bmi | 4943.000 | 4993.000 | True | 0.264 | 0.057 | 0.300 | 0.258 | -0.000 | -0.001 | -0.011 |
| ascot | egfr | 4877.000 | 4354.000 | True | 0.023 | 0.010 | 0.027 | 0.018 | -0.002 | 0.000 | -0.155 |
| empa-reg | lvef | 1566.000 | 676.000 | True | 0.354 | 0.031 | 0.366 | 0.345 | -0.002 | -0.003 | -0.526 |
| empa-reg | ntprobnp | 1143.000 | 577.000 | True | 0.279 | 0.115 | 0.331 | 0.243 | -0.003 | -0.002 | 0.257 |
| empa-reg | bmi | 1986.000 | 1303.000 | True | 0.178 | 0.121 | 0.261 | 0.159 | -0.002 | -0.002 | 0.094 |
| empa-reg | egfr | 1647.000 | 1041.000 | True | 0.082 | 0.092 | 0.127 | 0.039 | -0.002 | -0.002 | 0.137 |
| carolina | lvef | 231.000 | 119.000 | False | 0.232 | 0.012 | 0.251 | 0.242 | -0.005 | -0.006 | -0.213 |
| carolina | ntprobnp | 158.000 | 71.000 | False | 0.188 | 0.015 | 0.207 | 0.195 | -0.067 | -0.044 | 0.187 |
| carolina | bmi | 406.000 | 348.000 | True | 0.223 | 0.165 | 0.318 | 0.183 | -0.006 | -0.008 | -0.206 |
| carolina | egfr | 407.000 | 266.000 | False | 0.035 | 0.055 | 0.060 | 0.005 | -0.002 | 0.001 | -0.461 |
| leader | lvef | 127.000 | 901.000 | False | 0.278 | 0.012 | 0.279 | 0.270 | -0.004 | -0.005 | 0.059 |
| leader | ntprobnp | 80.000 | 791.000 | False | 0.250 | 0.099 | 0.287 | 0.209 | -0.010 | -0.007 | -0.628 |
| leader | bmi | 258.000 | 1636.000 | False | 0.210 | 0.136 | 0.294 | 0.183 | -0.002 | -0.001 | 0.774 |
| leader | egfr | 170.000 | 1440.000 | False | 0.044 | 0.034 | 0.054 | 0.021 | -0.003 | -0.002 | 0.374 |
| sustain6 | lvef | 683.000 | 744.000 | True | 0.255 | 0.017 | 0.259 | 0.246 | -0.003 | -0.002 | 0.124 |
| sustain6 | ntprobnp | 346.000 | 559.000 | True | 0.227 | 0.084 | 0.247 | 0.178 | 0.006 | -0.001 | -0.587 |
| sustain6 | bmi | 1230.000 | 994.000 | True | 0.160 | 0.125 | 0.244 | 0.136 | -0.004 | -0.002 | 0.685 |
| sustain6 | egfr | 885.000 | 1139.000 | True | 0.056 | 0.046 | 0.075 | 0.030 | -0.001 | -0.000 | 0.348 |
| rewind | lvef | 345.000 | 1033.000 | True | 0.281 | 0.029 | 0.284 | 0.263 | -0.003 | 0.002 | 0.123 |
| rewind | ntprobnp | 199.000 | 850.000 | False | 0.271 | 0.119 | 0.306 | 0.213 | -0.002 | -0.005 | -0.515 |
| rewind | bmi | 752.000 | 2077.000 | True | 0.193 | 0.098 | 0.259 | 0.179 | 0.000 | -0.002 | 0.441 |
| rewind | egfr | 638.000 | 1919.000 | True | 0.090 | 0.082 | 0.121 | 0.042 | -0.001 | -0.001 | 0.131 |
| declare | lvef | 1026.000 | 869.000 | True | 0.336 | 0.061 | 0.356 | 0.314 | -0.002 | -0.004 | -0.630 |
| declare | ntprobnp | 761.000 | 705.000 | True | 0.303 | 0.187 | 0.379 | 0.237 | -0.001 | -0.002 | 0.460 |
| declare | bmi | 1233.000 | 2149.000 | True | 0.201 | 0.124 | 0.279 | 0.177 | -0.003 | -0.000 | 0.133 |
| declare | egfr | 1000.000 | 1666.000 | True | 0.050 | 0.066 | 0.074 | 0.009 | -0.001 | -0.001 | -0.060 |
| canvas | lvef | 58.000 | 1080.000 | False | 0.301 | 0.023 | 0.308 | 0.291 | -0.002 | -0.001 | -0.280 |
| canvas | ntprobnp | 57.000 | 906.000 | False | 0.291 | 0.151 | 0.342 | 0.225 | -0.006 | -0.006 | -0.301 |
| canvas | bmi | 249.000 | 2451.000 | False | 0.224 | 0.145 | 0.308 | 0.190 | -0.001 | -0.003 | 0.368 |
| canvas | egfr | 162.000 | 2132.000 | False | 0.117 | 0.104 | 0.143 | 0.044 | -0.004 | -0.002 | 0.198 |
| tecos | lvef | 399.000 | 335.000 | True | 0.277 | 0.024 | 0.282 | 0.265 | -0.006 | -0.004 | 0.053 |
| tecos | ntprobnp | 304.000 | 246.000 | False | 0.317 | 0.102 | 0.354 | 0.281 | 0.000 | -0.003 | -0.065 |
| tecos | bmi | 736.000 | 629.000 | True | 0.180 | 0.121 | 0.265 | 0.163 | -0.005 | -0.003 | 0.003 |
| tecos | egfr | 563.000 | 510.000 | True | 0.069 | 0.065 | 0.089 | 0.027 | -0.002 | -0.001 | 0.009 |
| carmelina | lvef | 316.000 | 196.000 | False | 0.299 | 0.037 | 0.309 | 0.282 | -0.006 | -0.006 | -0.028 |
| carmelina | ntprobnp | 278.000 | 186.000 | False | 0.205 | 0.060 | 0.219 | 0.169 | -0.005 | -0.005 | 0.226 |
| carmelina | bmi | 402.000 | 341.000 | True | 0.226 | 0.135 | 0.298 | 0.188 | -0.003 | -0.004 | -0.146 |
| carmelina | egfr | 491.000 | 325.000 | True | 0.045 | 0.065 | 0.080 | 0.016 | -0.006 | -0.008 | -0.132 |
| valiant | lvef | 157.000 | 226.000 | False | 0.067 | -0.002 | 0.065 | 0.066 | -0.002 | 0.001 | -0.174 |
| valiant | ntprobnp | 148.000 | 226.000 | False | 0.203 | 0.073 | 0.262 | 0.204 | -0.015 | -0.013 | 0.137 |
| valiant | bmi | 153.000 | 346.000 | False | 0.181 | 0.079 | 0.239 | 0.173 | 0.006 | -0.004 | -0.065 |
| valiant | egfr | 260.000 | 423.000 | False | 0.033 | 0.090 | 0.079 | -0.012 | -0.003 | -0.002 | -0.318 |
| insight | lvef | 86.000 | 1609.000 | False | 0.079 | 0.019 | 0.081 | 0.064 | 0.003 | 0.000 | 0.114 |
| insight | ntprobnp | 37.000 | 597.000 | False | 0.070 | 0.023 | 0.089 | 0.068 | -0.002 | -0.003 | 0.378 |
| insight | bmi | 181.000 | 3850.000 | False | 0.210 | 0.049 | 0.244 | 0.205 | 0.000 | -0.002 | -0.014 |
| insight | egfr | 188.000 | 2888.000 | False | 0.014 | 0.003 | 0.017 | 0.014 | -0.002 | -0.003 | -0.757 |
| affirm | lvef | 2178.000 | 5664.000 | True | 0.270 | 0.038 | 0.277 | 0.249 | 0.001 | -0.001 | -0.227 |
| affirm | ntprobnp | 1520.000 | 4005.000 | True | 0.212 | 0.046 | 0.237 | 0.200 | -0.001 | -0.000 | 0.171 |
| affirm | bmi | 2211.000 | 6967.000 | True | 0.225 | 0.082 | 0.284 | 0.220 | -0.000 | -0.000 | 0.013 |
| affirm | egfr | 2200.000 | 6668.000 | True | 0.057 | 0.013 | 0.070 | 0.058 | -0.000 | -0.001 | -0.007 |
| af-chf | lvef | 511.000 | 784.000 | True | 0.038 | 0.011 | 0.046 | 0.035 | -0.003 | -0.002 | -0.245 |
| af-chf | ntprobnp | 603.000 | 1702.000 | True | 0.207 | 0.069 | 0.255 | 0.200 | -0.001 | -0.000 | 0.298 |
| af-chf | bmi | 663.000 | 2217.000 | True | 0.237 | 0.125 | 0.316 | 0.218 | -0.000 | -0.003 | -0.030 |
| af-chf | egfr | 651.000 | 2162.000 | True | 0.029 | 0.009 | 0.037 | 0.029 | -0.002 | -0.003 | -0.008 |
| precision | lvef | 534.000 | 550.000 | True | 0.195 | 0.043 | 0.204 | 0.168 | -0.006 | -0.001 | 0.069 |
| precision | ntprobnp | 228.000 | 378.000 | False | 0.319 | 0.209 | 0.371 | 0.205 | -0.008 | -0.033 | 0.092 |
| precision | bmi | 1404.000 | 1551.000 | True | 0.255 | 0.113 | 0.321 | 0.234 | -0.001 | -0.000 | -0.055 |
| precision | egfr | 1123.000 | 1123.000 | True | 0.031 | 0.046 | 0.054 | 0.008 | -0.003 | -0.002 | 0.019 |
| amplify | lvef | 2064.000 | 239.000 | False | 0.211 | 0.022 | 0.217 | 0.199 | -0.001 | -0.001 | 0.142 |
| amplify | ntprobnp | 1828.000 | 339.000 | True | 0.192 | 0.058 | 0.218 | 0.170 | -0.002 | -0.002 | 0.071 |
| amplify | bmi | 1841.000 | 473.000 | True | 0.235 | 0.073 | 0.275 | 0.219 | -0.005 | -0.004 | -0.181 |
| amplify | egfr | 2726.000 | 370.000 | True | 0.062 | 0.036 | 0.078 | 0.043 | -0.002 | -0.002 | 0.331 |
| lodestar | lvef | 3789.000 | 2991.000 | True | 0.290 | 0.021 | 0.296 | 0.281 | -0.002 | -0.002 | 0.051 |
| lodestar | ntprobnp | 2005.000 | 1976.000 | True | 0.275 | 0.069 | 0.313 | 0.262 | -0.001 | -0.002 | -0.045 |
| lodestar | bmi | 5101.000 | 4244.000 | True | 0.241 | 0.073 | 0.295 | 0.240 | -0.001 | -0.001 | -0.060 |
| lodestar | egfr | 4788.000 | 4120.000 | True | 0.079 | 0.029 | 0.089 | 0.062 | 0.000 | -0.001 | -0.081 |
| prove-it | lvef | 1063.000 | 82.000 | False | 0.218 | 0.011 | 0.216 | 0.207 | -0.007 | -0.005 | -0.123 |
| prove-it | ntprobnp | 732.000 | 87.000 | False | 0.246 | 0.097 | 0.296 | 0.220 | -0.008 | -0.002 | -0.007 |
| prove-it | bmi | 1014.000 | 165.000 | False | 0.206 | 0.088 | 0.263 | 0.192 | 0.002 | -0.000 | -0.006 |
| prove-it | egfr | 1401.000 | 131.000 | False | 0.063 | 0.041 | 0.075 | 0.035 | -0.004 | -0.001 | 0.130 |
| frail-af | lvef | 259.000 | 841.000 | False | 0.285 | 0.039 | 0.293 | 0.264 | -0.009 | -0.007 | 0.048 |
| frail-af | ntprobnp | 203.000 | 819.000 | False | 0.139 | 0.033 | 0.162 | 0.133 | -0.007 | -0.004 | 0.026 |
| frail-af | bmi | 439.000 | 1623.000 | True | 0.186 | 0.074 | 0.235 | 0.173 | -0.004 | -0.004 | -0.066 |
| frail-af | egfr | 347.000 | 1311.000 | True | 0.013 | -0.003 | 0.013 | 0.016 | -0.000 | -0.002 | 0.100 |
| laaos3 | lvef | 386.000 | 1493.000 | True | 0.257 | 0.008 | 0.259 | 0.253 | -0.004 | -0.003 | -0.014 |
| laaos3 | ntprobnp | 167.000 | 676.000 | False | 0.151 | 0.014 | 0.156 | 0.144 | -0.002 | -0.004 | 0.029 |
| laaos3 | bmi | 389.000 | 1441.000 | True | 0.185 | 0.029 | 0.207 | 0.183 | -0.001 | -0.000 | -0.064 |
| laaos3 | egfr | 321.000 | 1233.000 | True | 0.043 | 0.005 | 0.053 | 0.048 | -0.002 | -0.000 | 0.117 |
| protect-af | lvef | 180.000 | 674.000 | False | 0.330 | 0.062 | 0.341 | 0.297 | -0.003 | -0.005 | 0.321 |
| protect-af | ntprobnp | 113.000 | 520.000 | False | 0.150 | -0.000 | 0.148 | 0.148 | -0.007 | -0.008 | -0.009 |
| protect-af | bmi | 234.000 | 725.000 | False | 0.251 | 0.088 | 0.299 | 0.231 | -0.005 | -0.004 | -0.129 |
| protect-af | egfr | 225.000 | 779.000 | False | 0.029 | 0.000 | 0.038 | 0.038 | -0.003 | -0.007 | 0.038 |
| raft-af | lvef | 396.000 | 1337.000 | True | 0.232 | 0.059 | 0.249 | 0.202 | -0.001 | -0.003 | -0.144 |
| raft-af | ntprobnp | 310.000 | 1222.000 | True | 0.171 | 0.074 | 0.218 | 0.155 | -0.001 | -0.003 | -0.351 |
| raft-af | bmi | 438.000 | 1419.000 | True | 0.249 | 0.121 | 0.321 | 0.228 | -0.001 | -0.002 | 0.342 |
| raft-af | egfr | 328.000 | 1482.000 | True | 0.023 | 0.025 | 0.046 | 0.021 | -0.003 | -0.002 | 0.321 |
| active-w | lvef | 418.000 | 490.000 | True | 0.290 | 0.016 | 0.296 | 0.285 | -0.005 | -0.007 | 0.034 |
| active-w | ntprobnp | 202.000 | 382.000 | False | 0.162 | 0.012 | 0.178 | 0.168 | -0.007 | -0.006 | -0.333 |
| active-w | bmi | 546.000 | 848.000 | True | 0.225 | 0.075 | 0.272 | 0.213 | -0.001 | -0.001 | -0.031 |
| active-w | egfr | 511.000 | 688.000 | True | 0.019 | -0.000 | 0.023 | 0.023 | -0.000 | -0.002 | 0.090 |

Summary by confounder (all 38 trials):

| conf | r2_ecg_median | r2_ecg_min | r2_ecg_max | r2_partial_median | r2_partial_min | r2_partial_max | r2_shuf_median | r2_shuf_min | r2_shuf_max | r2_noise_median | r2_noise_min | r2_noise_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bmi | 0.224 | 0.160 | 0.264 | 0.210 | 0.136 | 0.258 | -0.002 | -0.006 | 0.006 | -0.002 | -0.008 | -0.000 |
| egfr | 0.042 | 0.013 | 0.117 | 0.025 | -0.012 | 0.077 | -0.002 | -0.006 | 0.001 | -0.002 | -0.008 | 0.001 |
| lvef | 0.260 | 0.038 | 0.354 | 0.248 | 0.035 | 0.345 | -0.002 | -0.009 | 0.004 | -0.002 | -0.007 | 0.006 |
| ntprobnp | 0.198 | 0.049 | 0.319 | 0.178 | 0.052 | 0.281 | -0.002 | -0.067 | 0.006 | -0.003 | -0.044 | -0.000 |
