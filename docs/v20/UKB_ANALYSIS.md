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

## Part 2. Held-out covariate balance and trial emulation in UK Biobank

### Verdict (plain language)
1. **With a held-out panel measured before initiation, adding the ECG barely changed balance, and the change was not ECG-specific.**
   - **Setting:** the primary design (new use since baseline; 5 trials). Panel A holds baseline (2006–10) SBP, BMI, smoking, lipids, creatinine and HbA1c, all measured before drug initiation.
   - **Result:** mean |SMD| went from 0.093 to 0.089, a relative reduction of 3.9% (95% CI −7.2 to 18.5; 3/5 trials better; sign-flip p = 0.31). The permuted ECG gave −1.9%.
   - **Richer PS:** 0.060 → 0.057 (4.8%, −7.8 to 15.5).
2. **Balance on cardiac MRI measured at the same visit as the ECG did improve, but this is on-treatment physiology.**
   - **Prevalent-user design (6 trials):** the ECG reduced CMR imbalance by **22.0% (14.8–31.2; 5/6 trials; p = 0.031)**; the permuted ECG gave 0.1%.
   - **Primary design:** 10.7% (−11.7 to 25.2) with the demographic PS, and 17.6% (10.7–22.2) with the richer PS. In the richer PS the permuted ECG also gave 12.9%, so that gain is partly non-specific.
   - **Why this is weak evidence:** the ECG and CMR are recorded on treatment at the same visit. Both reflect current physiology, including drug effects. This is not evidence of pre-treatment confounding control.
3. **Agreement with the RCTs did not improve consistently with the ECG.**
   - **Primary design:** mean |Δ log HR| was 0.378 with the demographic PS and 0.313 with + ECG (3/5 trials closer). The permuted ECG did better (0.242, 4/5 closer), so the change is noise from re-matching, not ECG information. With the richer PS, adding the ECG made agreement worse (0.231 → 0.350).
   - **Prevalent-user design:** the ECG moved estimates closer (0.279 → 0.165; 5/6 trials; p = 0.031; permuted ECG 0.310).
   - **Fragility:** that result rests on six overlapping cohorts with 65–367 events.
   - **Absolute agreement is poor in both designs:** ASCOT HR ≈ 0.5–0.7 vs 0.90, and VALUE ≈ 1.3–1.8 vs 1.04. Design problems dominate: prevalent or long-standing users, indication (β-blockers for coronary disease) and self-reported medication.
4. **Bottom line.** In UK Biobank the ECG cannot serve as a pre-treatment covariate, because it is recorded after initiation. The informative UKB result is the plasmode (Part 1), where treatment is simulated. The real-exposure balance and emulation analyses are descriptive and should be reported as a limitation-bounded external check, not as replication.

### Key limitation: ECG timing
In both designs the ECG is taken at the imaging visit (time zero), after the drug was started: 4–10 years after in the primary design, and at an unknown time in the prevalent-user design.
- The ECG therefore partly reflects drug effects, for example β-blocker heart rate and PR interval.
- Adjusting for it is adjustment for a post-treatment variable. It can remove part of the treatment effect or induce bias, and it cannot be interpreted as confounding control.
- The same applies to the CMR panel and the imaging-visit SBP and BMI.
- Only panel A (baseline i0 measures) precedes initiation, and only in the primary design.

### Design
- **Trials:** ONTARGET (ARB vs ACEi), ASCOT (amlodipine vs atenolol-type β-blocker), ALLHAT (amlodipine vs thiazide), LIFE (ARB vs atenolol-type β-blocker) and VALUE (ARB vs amlodipine), all with a hypertension gate and no prior HF. CAPRIE (clopidogrel vs aspirin, prior CAD/stroke/PAD) is included in the prevalent-user design only. Its new-use design had 197 in the smaller arm, below the ≥300 requirement.
- **Designs:**
  - **Primary, new use since baseline:** on exactly one arm class at the imaging visit and on neither at baseline or the first repeat visit.
  - **Secondary, prevalent use at the imaging visit:** the v1.5 design.

  Time zero is the imaging-visit date in both.
- **Other elements:** outcomes (HES first occurrence and algorithmic MI/stroke after time zero, plus all-cause death as the CV-death proxy), horizons and censoring follow v1.5.
- **PS arms:** L2 logistic, 1:1 greedy caliper 0.2, pair-clustered Cox.
  - Demographic (age, sex, index year); + ECG (32 PCs); + permuted ECG.
  - **Richer PS:** demographics + 9 comorbidities + non-exposure medication classes at i2 + 3 utilisation counts; with ECG; with permuted ECG. It lost overlap in two trials (primary design: ASCOT 515 of 1,019 pairs; LIFE 326 of 1,051).
- **Held-out panels (never in any PS):**
  - **A:** 9 baseline measures, before initiation in the primary design; 5–15% missing.
  - **C:** 9 comorbidities + 3 utilisation counts, demographic arms only. Measured before time zero, but not necessarily before initiation.
  - **B:** 11 CMR measures + imaging-visit SBP and BMI. On treatment; CMR available for 55–62%.
- **Reproduction gate (passed):** the prevalent-user ONTARGET, ASCOT and ALLHAT cohorts, outcomes, baseline covariates and ECG sets are identical to v1.5. The unmatched, sparse and sparse + ECG log HRs reproduce v1.5 exactly (max |Δ| 8e-17).

### Cohorts (with ECG)

| Trial | Primary: T / C | Primary: events | Prevalent: T / C | Prevalent: events | RCT HR |
|---|---|---|---|---|---|
| ONTARGET | 1,106 / 2,393 | 130 | 2,567 / 4,931 | 367 | 1.01 |
| ASCOT | 2,483 / 1,019 | 90 | 3,452 / 1,910 | 187 | 0.90 |
| ALLHAT | 2,345 / 536 | 66 | 3,446 / 1,374 | 130 | 0.98 |
| LIFE | 1,160 / 1,051 | 72 | 2,140 / 2,053 | 170 | 0.87 |
| VALUE | 992 / 2,404 | 94 | 1,845 / 3,347 | 173 | 1.04 |
| CAPRIE | infeasible (197 in smaller arm) | – | 343 / 1,690 | 65 | 0.913 |

**Record overlap:** the share of one trial's ECG holders who are also in another trial. ALLHAT, ASCOT and VALUE share 62–75% (the amlodipine arm); LIFE shares 48–55% with ONTARGET and ASCOT (primary design). Trials were kept, but pooled statistics treat them as if independent, which they are not.

### Balance, primary design (new use since baseline): mean |SMD| per trial

| Panel | Trial | Unmatched | Demo PS | + ECG | + permuted ECG | Richer PS | + ECG | + permuted ECG |
|---|---|---|---|---|---|---|---|---|
| A (baseline, pre-initiation) | ONTARGET | 0.054 | 0.057 | 0.048 | 0.062 | 0.042 | 0.037 | 0.057 |
| | ASCOT | 0.120 | 0.115 | 0.124 | 0.112 | 0.080 | 0.073 | 0.071 |
| | ALLHAT | 0.079 | 0.099 | 0.090 | 0.084 | 0.048 | 0.046 | 0.076 |
| | LIFE | 0.131 | 0.108 | 0.121 | 0.116 | 0.068 | 0.079 | 0.067 |
| | VALUE | 0.082 | 0.084 | 0.063 | 0.097 | 0.063 | 0.050 | 0.073 |
| B (CMR + i2 vitals, on treatment) | ONTARGET | 0.092 | 0.060 | 0.067 | 0.053 | 0.048 | 0.046 | 0.045 |
| | ASCOT | 0.278 | 0.281 | 0.246 | 0.268 | 0.195 | 0.154 | 0.141 |
| | ALLHAT | 0.200 | 0.155 | 0.184 | 0.209 | 0.178 | 0.134 | 0.133 |
| | LIFE | 0.313 | 0.284 | 0.193 | 0.287 | 0.198 | 0.165 | 0.200 |
| | VALUE | 0.156 | 0.128 | 0.121 | 0.145 | 0.121 | 0.111 | 0.127 |

Panel C (comorbidities/utilisation, demographic arms), mean |SMD|, demo PS → + ECG:

| ONTARGET | ASCOT | ALLHAT | LIFE | VALUE |
|---|---|---|---|---|
| 0.051 → 0.046 | 0.419 → 0.395 | 0.090 → 0.092 | 0.329 → 0.333 | 0.135 → 0.121 |

### Balance, pooled across trials (relative reduction in mean |SMD| vs the same PS without ECG; trial-level bootstrap CI)

| Design | Panel | + ECG (demo) | + permuted ECG (demo) | + ECG (richer PS) | + permuted ECG (richer PS) |
|---|---|---|---|---|---|
| Primary (5 trials) | A: baseline, pre-initiation | 3.9% (−7.2 to 18.5); 3/5; p = 0.31 | −1.9% | 4.8% (−7.8 to 15.5); 4/5; p = 0.22 | −14.4% |
| Primary | C: comorbidity/utilisation | 3.6% (−0.8 to 8.3); 3/5; p = 0.16 | 1.2% | – | – |
| Primary | B: CMR + i2 vitals (on treatment) | 10.7% (−11.7 to 25.2); 3/5; p = 0.25 | −5.9% | 17.6% (10.7–22.2); 5/5; p = 0.031 | 12.9% |
| Prevalent (6 trials) | A: baseline | 23.6% (6.2–40.1); 4/6; p = 0.06 | 13.5% | 0.7% (−6.5 to 8.0) | 2.2% |
| Prevalent | C: comorbidity/utilisation | 3.7% (2.1–4.8); 5/6; p = 0.031 | −1.5% | – | – |
| Prevalent | B: CMR + i2 vitals (on treatment) | **22.0% (14.8–31.2); 5/6; p = 0.031** | 0.1% | 13.9% (−6.8 to 24.2); 4/6 | 1.7% |

- The prevalent-design panel A result depends on CAPRIE (0.137 → 0.058 with ECG, 0.065 with permuted ECG), a small cohort in which the placebo improves balance as much as the ECG.
- p values are one-sided exact sign-flip tests across trials (minimum possible 1/32 or 1/64). They are descriptive, given the overlap.

### Trial emulation: HR (95% CI) vs RCT

**Primary design (new use since baseline):**

| Trial (RCT HR) | Demo PS | + ECG | + permuted ECG | Richer PS | + ECG |
|---|---|---|---|---|---|
| ONTARGET (1.01) | 1.07 (0.70–1.63) | 1.13 (0.73–1.74) | 1.06 | 1.06 (0.69–1.62) | 0.94 (0.62–1.42) |
| ASCOT (0.90) | 0.47 (0.27–0.80) | 0.47 (0.28–0.80) | 0.58 | 0.51 (0.24–1.12) | 0.52 (0.24–1.13) |
| ALLHAT (0.98) | 0.53 (0.24–1.15) | 0.68 (0.33–1.39) | 0.77 | 0.68 (0.32–1.47) | 0.61 (0.28–1.34) |
| LIFE (0.87) | 0.88 (0.54–1.42) | 0.86 (0.49–1.49) | 0.93 | 0.88 (0.42–1.86) | 1.29 (0.60–2.78) |
| VALUE (1.04) | 1.80 (1.07–3.04) | 1.60 (0.95–2.69) | 1.58 | 1.23 (0.73–2.08) | 1.34 (0.78–2.29) |

**Prevalent-user design:**

| Trial (RCT HR) | Demo PS | + ECG | + permuted ECG | Richer PS | + ECG |
|---|---|---|---|---|---|
| ONTARGET (1.01) | 1.05 (0.82–1.35) | 0.99 (0.77–1.28) | 0.98 | 0.97 (0.76–1.24) | 0.91 (0.71–1.16) |
| ASCOT (0.90) | 0.62 (0.45–0.84) | 0.61 (0.44–0.85) | 0.65 | 0.65 (0.43–0.99) | 0.69 (0.44–1.08) |
| ALLHAT (0.98) | 0.73 (0.47–1.15) | 0.98 (0.64–1.52) | 0.66 | 0.85 (0.53–1.35) | 1.04 (0.66–1.64) |
| LIFE (0.87) | 0.64 (0.47–0.88) | 0.75 (0.53–1.05) | 0.70 | 0.91 (0.57–1.46) | 0.80 (0.49–1.30) |
| VALUE (1.04) | 1.53 (1.08–2.19) | 1.34 (0.96–1.88) | 1.50 | 1.30 (0.90–1.89) | 1.36 (0.93–2.00) |
| CAPRIE (0.913) | 1.21 (0.51–2.84) | 1.10 (0.48–2.53) | 1.54 | 1.36 (0.53–3.49) | 1.18 (0.50–2.81) |

**RCT-DUPLICATE agreement metrics across trials:**

| Design | Arm | Mean \|Δ log HR\| | Estimate agreement | Standardized-difference agreement | Closer vs PS alone (sign-flip p) |
|---|---|---|---|---|---|
| Primary (5) | Unmatched | 0.315 | 1/5 | 4/5 | – |
| | Demo PS | 0.378 | 2/5 | 3/5 | – |
| | + ECG | 0.313 | 1/5 | 4/5 | 3/5 (0.22) |
| | + permuted ECG | 0.242 | 2/5 | 5/5 | 4/5 (0.09) |
| | Richer PS | 0.231 | 2/5 | 5/5 | – |
| | + ECG | 0.350 | 1/5 | 5/5 | 1/5 (0.97) |
| Prevalent (6) | Unmatched | 0.255 | 1/6 | 5/6 | – |
| | Demo PS | 0.279 | 1/6 | 4/6 | – |
| | + ECG | 0.165 | 2/6 | 5/6 | 5/6 (0.031) |
| | + permuted ECG | 0.310 | 1/6 | 6/6 | 4/6 (0.67) |
| | Richer PS | 0.197 | 2/6 | 6/6 | – |
| | + ECG | 0.174 | 2/6 | 6/6 | 3/6 (0.28) |

- Pearson r across 5–6 trials is reported in `emu_pooled_emulation.csv` but is not interpretable with so few points.
- The CIs are wide (66–130 events per trial in the primary design). Standardized-difference agreement is therefore high for every arm and does not discriminate between them.

### Deviations and notes (balance and emulation)
1. **CAPRIE** uses the p2y12 class (clopidogrel; prasugrel and ticagrelor are absent from coding 4) vs aspirin, with dipyridamole users excluded. The outcome is death, MI or ischaemic stroke (codes I63/I64 only). The published benchmark (RR 0.913, 0.835–0.997) was added, because it is not in `trial_specs.PUBLISHED`. CAPRIE is prevalent-user design only.
2. **Richer PS** lost overlap in ASCOT and LIFE (primary design), which widens their CIs. It excludes laboratory and vital-sign covariates, so that those measures could be held out.
3. **Event counts** of 1–10 in matched arms are suppressed in `emu_estimates.csv`.
4. **Outputs:**
   - `emu_estimates.csv`, `emu_balance.csv`, `emu_balance_by_var.csv`;
   - `emu_pooled_balance.csv`, `emu_pooled_emulation.csv`;
   - `emu_overlap.csv`, `emu_meta.csv`;
   - the reproduction gates `emu_gate_build.csv` and `emu_gate_estimates.csv`.
