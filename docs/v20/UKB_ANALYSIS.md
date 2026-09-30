# v2.0 UK Biobank: CMR plasmode, held-out covariate balance and trial emulation

Date 2026-09-30. **Exploratory.**
- Plan: `docs/v20/UKB_ANALYSIS_PLAN.md`, registered before results (43de534); amendments 1–2 were added before the balance and emulation results.
- Code: `scripts/v20/ukb_cmr_plasmode.py` (plasmode) and `scripts/v20/ukb_emulations.py` (balance and emulation).
- Aggregates: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-ukb-analysis/`. Files named `restricted_*` hold participant-level data and stay there.
- Figure: `docs/v20/UKB_CMR_plasmode.png`.

Aggregates only; counts 1–10 suppressed. The project does not use polygenic scores or genetics (PI decision, 2026-09-30).

## Part 1. CMR plasmode: how much hidden cardiac-MRI confounding does the ECG remove?

### Verdict (plain language)
1. **The ECG embedding removes a sizeable share of the bias from hidden cardiac MRI physiology.** In the cleanest version, treatment is driven only by the hidden CMR variable and the ECG alone is the PS. It removes:
   - **24%** of the bias from hidden **LVEF**;
   - **40%** from LV end-diastolic volume index;
   - **45%** from LV mass index;
   - **36%** overall.

   Adjusting for the CMR variable itself removes 97%, and a permuted-ECG placebo removes 0%. Monte Carlo SE ≤ 2.6 points.
2. **Added to a demographic PS, the ECG removes a further 19% of the remaining confounder-induced bias**: LVEF 14%, LVEDVi 25%, LV mass index 20% (oracle 92%, permuted ECG −2%).
3. **Bias removed tracks how well the ECG predicts the confounder, as at Yale.**
   - The ECG's cross-fitted R² is 0.10–0.15 for LVEF, 0.27–0.32 for LVEDVi and 0.41–0.43 for LV mass index.
   - Across the 9 cohort × confounder cells, % removed ≈ 1.2 × 100 × R² (slope through the origin; Spearman ρ 0.77).
   - UK Biobank therefore reproduces the Yale relationship (≈100 × R²) in an independent population, with the confounder measured by CMR at the same visit as the ECG.

### Design
- **Base populations:** the v1.5 prevalent-user cohorts at the imaging visit:
  - ONTARGET, ARB vs ACEi (analysis set 3,226);
  - ASCOT, amlodipine vs β-blocker (2,278);
  - ALLHAT, amlodipine vs thiazide (2,020).

  ASCOT and ALLHAT share the amlodipine arm, so their cells are not independent.
- **Hidden confounders:** Bai et al. CMR imaging-derived phenotypes at the imaging visit, in the clinical orientation. LVEF (lower = more treatment and hazard), LVEDV/BSA and LV mass/BSA (higher = worse).
- **Simulation:** the design of the Yale G2 plasmode.
  - A Weibull outcome from the real covariates plus C, with a true HR of 0.80.
  - 9 confounding scenarios plus a null.
  - 50 replicates per scenario, each an 80% subsample.
  - Refit PS, 1:1 caliper matching, and a pair-clustered Cox model.
  - The truth is the marginal HR from counterfactual outcomes.
  - The UKB event rate was rescaled to about 20% (prespecified). A real-event-rate sensitivity run was also done.
- **ECG:** our BCL embeddings, reduced to 32 PCs within each cohort.

### Results

**A. Treatment driven by C only: the ECG as the only PS (bias removed vs unmatched; raw)**

| PS | LVEF | LVEDVi | LV mass index | All |
|---|---|---|---|---|
| ECG only | **24.0** | 40.0 | 44.5 | **35.9** |
| Permuted ECG only | −0.4 | 1.1 | 0.6 | 0.4 |
| C only (oracle) | 95.8 | 97.8 | 97.0 | 96.8 |

- The null-corrected values are similar: ECG only 23.5 / 37.7 / 47.4 / 36.2.
- For LVEF, the ECG alone reduced bias from 0.208 to 0.158 log HR, and coverage rose from 55% to 72% (oracle 95%).

**B. Treatment driven by demographics + C: % of the demographic-PS bias removed (null-corrected)**

| Added to the demographic PS | LVEF | LVEDVi | LV mass index | All |
|---|---|---|---|---|
| + ECG | 14.0 | 24.6 | 19.9 | **19.2** |
| + permuted ECG | −0.3 | −0.1 | −6.6 | −1.9 |
| + C (oracle) | 91.3 | 96.4 | 87.3 | 91.9 |

- **Relative to unmatched (all confounders):** the demographic PS removed 24%, + ECG 39%, ECG only 39% and the oracle 94%.
- **Coverage:** unmatched 56%, demographic PS 74%, + ECG 81%, oracle 96%.
- **Real-event-rate sensitivity** (ONTARGET × LVEF): + ECG 25.6% of the demographic-PS bias; ECG only 24.5% vs unmatched; oracle 88%.

**C. ECG proxy strength (5-fold cross-fitted ridge R²)**

| Cohort | LVEF | LVEDVi | LV mass index |
|---|---|---|---|
| ONTARGET | 0.148 | 0.300 | 0.425 |
| ASCOT | 0.137 | 0.266 | 0.407 |
| ALLHAT | 0.105 | 0.319 | 0.429 |

The LVEF R² is lower than at Yale (median 0.26 with echo LVEF). UK Biobank participants are healthy volunteers with a narrow LVEF range.

### Deviations (plasmode)
1. **CMR source.** The planned LVEF field (22420, inline scanner analysis) agreed only moderately with the Bai IDPs (r 0.60; LVEDV r 0.32). The validated Bai IDPs indexed to BSA were used throughout.
2. **Dropped arms.** Arms using polygenic scores were run and then dropped per PI decision (amendment 1). They are not reported, and their outputs stay in the audit folder. The analysis set was restricted to participants with genotype data, as run.
3. **NT-proBNP** is not available locally, so it was not used as a confounder.
4. **Summary fix.** A divide-by-zero in a per-cell summary was fixed and the summaries re-run. Simulation outputs were unaffected.
