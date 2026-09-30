# v2.0 UK Biobank: CMR plasmode (ECG vs polygenic scores as confounding proxies) and CMR held-out balance

Date 2026-09-30. **Exploratory.**
- Plan: `docs/v20/UKB_ANALYSIS_PLAN.md`, committed before results (43de534).
- Code: `scripts/v20/ukb_cmr_plasmode.py`.
- Aggregates: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-ukb-analysis/`. Files named `restricted_*` hold participant-level matrices and stay there.
- Figure: `docs/v20/UKB_CMR_plasmode.png`.

Aggregates only; counts 1–10 suppressed. Local commits only, pending PI review.

## Verdict (plain language)

1. **In UK Biobank, the ECG embedding removes a sizeable part of the bias from hidden cardiac MRI physiology. Polygenic scores remove almost none.**
   - The cleanest version has treatment driven only by the hidden CMR variable, and uses the ECG alone as the PS. It removes:
     - **24%** of the bias from hidden **LVEF**;
     - **40%** from LV end-diastolic volume index;
     - **45%** from LV mass index;
     - **36%** overall.
   - Six cardiovascular polygenic scores (AF, AS, CAD, DCM, HCM, HF) remove **2%** overall, and **3%** for LVEF.
   - Adding the PGS to the ECG adds nothing (36%).
   - Adjusting for the CMR variable itself removes **97%**, and the permuted-ECG placebo removes **0%**.
   - Monte Carlo SE ≤ 2.6 percentage points.
2. **Added to a demographic PS, the ECG removes a further 19% of the remaining confounder-induced bias.** This is the design where treatment depends on demographics and C, null-corrected.
   - By confounder: LVEF 14%, LVEDVi 25%, LV mass index 20%.
   - The PGS add **1%**, and PGS + ECG gives 22%.
   - Oracle 92%; MCSE ≤ 4.3.
3. **Bias removed tracks how well each proxy predicts the confounder**, as it did at Yale:
   - The ECG's cross-fitted R² is 0.10–0.15 for LVEF, 0.27–0.32 for LVEDVi and 0.41–0.43 for LV mass index.
   - The PGS R² is ≤ 0.02.
   - Across the 9 cohort × confounder cells, bias removed by ECG only ≈ **1.2 × 100 × R²** (slope through the origin; Spearman ρ = 0.77).
   - So the UKB replicates the Yale finding (≈100 × R²) in an independent population. Here the confounder was measured by CMR at the same visit as the ECG.
4. **ECG vs genetics:**
   - The ECG measures current physiology, and so proxies it far better than germline scores do.
   - This is the ECG counterpart of German et al. (Nat Genet 2025): PGS are weak proxies for confounders.
   - It also reproduces their caution. A DCM score whose weights were trained partly on UK Biobank CMR traits (HERMES MTAG, PGS004862) looks misleadingly strong in UKB, with LVEF R² 0.12–0.18 against 0.01–0.02 for the non-MTAG score. See deviation 2.
5. **Held-out CMR balance with the real exposure is uninformative.**
   - Exposure is prevalent use at the imaging visit, and the CMR is measured on treatment, so arm differences in LVEF and LA volume partly reflect drug effects rather than confounding. For example, beta-blocker vs amlodipine in ASCOT: LA volume |SMD| 0.40.
   - Adding the ECG changed mean |SMD| little: ONTARGET 0.038 → 0.038, ASCOT 0.262 → 0.246, ALLHAT 0.164 → 0.167.
   - No test was performed. The plasmode, where treatment is simulated, is the valid UKB contribution.

## Data and populations

| Cohort (v1.5, prevalent user at imaging visit) | Cohort N | With ECG | ECG + CMR | ECG + CMR + PGS (analysis set, LVEF) | Real arms in S (T / C) | Real event rate |
|---|---|---|---|---|---|---|
| ONTARGET (ARB vs ACEi) | 8,535 | 7,498 | 4,673 | 3,226 | 1,055 / 2,171 | 4.9% |
| ASCOT (amlodipine vs β-blocker) | 6,082 | 5,362 | 3,171 | 2,278 | 1,428 / 850 | 3.5% |
| ALLHAT (amlodipine vs thiazide) | 5,432 | 4,820 | 2,873 | 2,020 | 1,401 / 619 | 2.7% |

- ASCOT and ALLHAT share the amlodipine arm, so cells are not independent.
- **Confounders:** Bai et al. CMR imaging-derived phenotypes at the imaging visit, in the clinical orientation. They are LVEF (lower = more treatment and hazard), LVEDV/BSA and LV mass/BSA (higher = worse). All 9 cohort × confounder cells were eligible (≥300 per real arm).
- **ECG:** our BCL embeddings (v1.5), reduced to 32 PCs within each cohort. The permuted-ECG placebo shuffles the PCs between participants.
- **PGS:** PGS Catalog scores on the local QC'd genotypes, standardised:
  - AF (PGS005168), AS (PGS005252), CAD (PGS003725), HCM (PGS004910, GWAMA), HF (PGS005097);
  - DCM (**PGS004861, GWAMA**; see deviation 2).

## Proxy strength (real data; 5-fold cross-fitted ridge R²)

| Cohort | Confounder | n | R² ECG | partial R² ECG (given demographics) | R² PGS (6) | partial R² PGS | R² DCM-MTAG (diagnostic; overlap) |
|---|---|---|---|---|---|---|---|
| ONTARGET | LVEF | 3,226 | 0.148 | 0.099 | 0.018 | 0.021 | 0.138 |
| ONTARGET | LVEDVi | 3,112 | 0.300 | 0.252 | 0.005 | 0.007 | 0.091 |
| ONTARGET | LV mass index | 3,112 | 0.425 | 0.294 | 0.000 | 0.003 | 0.025 |
| ASCOT | LVEF | 2,278 | 0.137 | 0.078 | 0.021 | 0.027 | 0.117 |
| ASCOT | LVEDVi | 2,214 | 0.266 | 0.221 | 0.005 | 0.007 | 0.081 |
| ASCOT | LV mass index | 2,214 | 0.407 | 0.253 | 0.000 | 0.005 | 0.018 |
| ALLHAT | LVEF | 2,020 | 0.105 | 0.054 | 0.021 | 0.025 | 0.177 |
| ALLHAT | LVEDVi | 1,953 | 0.319 | 0.267 | 0.005 | 0.008 | 0.105 |
| ALLHAT | LV mass index | 1,953 | 0.429 | 0.238 | 0.001 | 0.002 | 0.026 |

The ECG's LVEF R² in UKB (0.10–0.15) is lower than at Yale (median 0.26 for echo LVEF). UKB is a healthy volunteer population with a narrow LVEF range and few reduced-EF participants.

## Simulation results

All pooled over the 3 cohorts × 3 confounders × 9 non-null scenarios, with 50 replicates each; the ratio of summed cell-mean errors; MCSE from 1,000 replicate resamples within cells.

### A. Treatment driven by C only (trtC): each proxy alone vs unmatched (raw)

| PS | LVEF | LVEDVi | LV mass index | All |
|---|---|---|---|---|
| ECG only | **24.0** | 40.0 | 44.5 | **35.9** |
| PGS only | 2.7 | 3.6 | −0.3 | **1.9** |
| PGS + ECG | 25.4 | 39.4 | 45.3 | 36.4 |
| Permuted ECG only | −0.4 | 1.1 | 0.6 | 0.4 |
| C only (oracle) | 95.8 | 97.8 | 97.0 | 96.8 |

The null-corrected values are similar (ECG only: 23.5 / 37.7 / 47.4 / 36.2), and the maximum MCSE is 2.6.

**Performance, LVEF, trtC:**

| Arm | Bias (log HR) | RMSE | Coverage |
|---|---|---|---|
| Unmatched | 0.208 | 0.241 | 55% |
| ECG only | 0.158 | 0.211 | 72% |
| PGS only | 0.203 | 0.248 | 61% |
| Oracle | 0.009 | 0.129 | 95% |

Bias MCSE is 0.003–0.004 and coverage MCSE about 1 point.

### B. Treatment driven by demographics + C (main design): % of the demographic-PS bias removed, null-corrected

| Added to the demographic PS | LVEF | LVEDVi | LV mass index | All |
|---|---|---|---|---|
| + ECG | 14.0 | 24.6 | 19.9 | **19.2** |
| + PGS | 1.2 | 5.6 | −5.5 | **0.9** |
| + PGS + ECG | 12.6 | 23.3 | 33.3 | 21.9 |
| + permuted ECG | −0.3 | −0.1 | −6.6 | −1.9 |
| + C (oracle) | 91.3 | 96.4 | 87.3 | 91.9 |

- **Vs unmatched (null-corrected, all confounders):**
  - demographic PS 24%;
  - + ECG 39%;
  - + PGS 25%;
  - ECG only 39%;
  - PGS only 1%;
  - oracle 94%.
- The raw values are similar (+ ECG 19.0% of the demographic-PS bias).
- Maximum MCSE 4.3.

**Coverage, all confounders:**

| Arm | Coverage |
|---|---|
| Unmatched | 56% |
| Demographic PS | 74% |
| + ECG | 81% |
| + PGS | 74% |
| + PGS + ECG | 82% |
| Oracle | 96% |

### C. Real event rate (sensitivity; ONTARGET × LVEF; simulated null event rate 5.8% vs 20% in the primary run)
- Null-corrected, vs the demographic PS: + ECG 25.6%, + PGS 7.0%, oracle 87.8%.
- ECG only vs unmatched: 24.5%.
- The raw values are noisier (+ ECG 13.7%; MCSE up to 4.4).
- The direction and ordering are unchanged, and the ECG > PGS pattern does not depend on the event-rate rescaling.

### D. Relation to R² (trtC, 9 cells)

| Proxy | Slope through origin (% removed = slope × 100 × R²) | Spearman ρ |
|---|---|---|
| ECG only | 1.21 | 0.77 |
| PGS + ECG | 1.15 | 0.92 |

- For PGS only, R² ≤ 0.02 and % removed ranges from −8 to 6. It is indistinguishable from zero.

## Held-out CMR balance with the real exposure (descriptive; prevalent users; CMR on treatment)

Mean |SMD| over 11 CMR measures:
- **Measures:** LVEF, LVEDVi, LVESVi, LVSVi, LV cardiac index, LV mass index, RVEDVi, RVEF, LAVi max, LA EF, RAVi max.
- **Set:** participants with ECG, CMR and PGS.

| Cohort | Unmatched | Demographic PS | + ECG | + permuted ECG | + PGS | + PGS + ECG |
|---|---|---|---|---|---|---|
| ONTARGET | 0.065 | 0.038 | 0.038 | 0.048 | 0.037 | 0.033 |
| ASCOT | 0.281 | 0.262 | 0.246 | 0.269 | 0.276 | 0.243 |
| ALLHAT | 0.264 | 0.164 | 0.167 | 0.162 | 0.179 | 0.147 |

- The large ASCOT imbalances (LVEF 0.25, LA volume 0.40) are consistent with on-treatment effects of β-blockade vs amlodipine on heart rate, stroke volume and atrial size, not with pre-treatment confounding.
- This analysis cannot separate the two, which is why the plasmode is the UKB result.
- Per-variable SMDs are in `balance_cmr.csv`.

## Deviations from the plan (logged)

1. **LVEF source.**
   - The plan named field 22420 (inline scanner analysis) as primary, with the Bai IDP as fallback. The prespecified empirical check found only moderate agreement between the two sources: r = 0.60 for LVEF, and r = 0.32 for LVEDV (22421 vs 24100).
   - The Bai deep-learning IDPs are the validated pipeline. All CMR confounders and panel measures therefore use the Bai IDPs (24100–24115) indexed to BSA (22427). Field 22420 is not used.
2. **DCM PGS.**
   - The locally computed DCM score was HERMES **MTAG** (PGS004862, Zheng et al. Nat Genet 2024). It borrows strength from LV imaging traits that include UK Biobank CMR, so it overlaps with our confounders.
   - Its R² for LVEF was 0.12–0.18, against 0.01–0.02 for all other scores. This is implausible for germline prediction and consistent with overlap.
   - We scored the **non-MTAG GWAMA** DCM score (PGS004861) on the same genotypes, with the same plink2 settings as the existing pipeline (534,900 variants matched), and used it in all PGS arms. The MTAG score is reported only as a diagnostic R².
   - With the MTAG score, the "PGS" arms would have been inflated.
3. **NT-proBNP** was not available locally, as anticipated in the plan. No NT-proBNP confounder was used.
4. **CAPRIE** (named in the task) is not among the built v1.5 cohorts. The balance analysis used ONTARGET, ASCOT and ALLHAT.
5. **A summarize bug** (a per-cell summary divided by zero for empty confounder subsets) was fixed and the summary re-run. Simulation outputs were unaffected.

## Reproducibility
- The CMR columns (eid; fields 22420–22427 and 24100–24115 at instance 2) were streamed, column-filtered, from the CMR imaging-derived phenotype basket in the read-only object store into `restricted_cmr_i2.parquet` (40,459 participants with any instance-2 CMR). The streaming command is not committed, because it names storage locations.
- The DCM GWAMA score was produced with plink2 `--score … 1 2 3 header` on the QC'd genotypes (output `restricted_DCM_PGS004861.sscore`).
- `ukb_cmr_plasmode.py prep` builds the analysis sets and the real-data R², and writes the restricted cache.
- `run --design main|trtC|realrate --reps 50 --workers 24` produces 45,000, 27,000 and 3,500 replicate-arm rows.
- `summarize` writes `pooled_*.csv`, `performance_*.csv` and `cells_*.csv`.
- `balance` writes `balance_cmr.csv`, and `figure` writes the figure.
- Null-scenario bias is ≈0 in every arm: |mean error| ≤ 0.012 log HR in the main design.
