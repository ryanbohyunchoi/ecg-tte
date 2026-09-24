# Protocol v1 (DRAFT, not frozen): unstructured ECG information for confounding control in EHR-based target trial emulation

Status: **draft for Ryan's review, 2026-09-24.** No outcome has been extracted for any trial.
Everything below is to be frozen *before* outcome extraction. Items marked **[OPEN]** need a
decision. Every choice made after viewing balance results is labelled as such (§12).

## 1. Objective and hypotheses

In EHR data, key clinical measurements (echo, labs, vitals) are often missing. We ask whether a
routinely acquired 12-lead ECG, used as a representation in the propensity score, recovers
confounding information that codes miss, and whether this improves target trial emulation.

Balance hypotheses (phase 1, balance only):
- **H1 Complementarity.** ECG embeddings capture cardiac structural and functional confounding.
  Empirical code selection (hdPS) captures the coded record. The combination captures both.
- **H2 Specificity.** The ECG's balance gain is larger in trials where cardiac physiology drives
  treatment choice (pre-specified "physiology" role) than in control trials.
- **H3 Substitution.** Adding the ECG to a sparse (codes-only) PS closes part of the gap to a PS
  that contains the measured values.
- **H4 Mechanism.** The ECG's gain is concentrated in LV structure, LV function, diastolic and RV
  physiology, and is absent for valve disease and the aortic root.

Effect hypothesis (phase 2, after freeze):
- **H5.** Estimates from sparse + ECG and hdPS + ECG lie closer than the sparse and hdPS
  estimates to (a) the full-data (clinical PS) emulation and (b) the published RCT result.

## 2. Data sources

| Source | Content | Use |
|---|---|---|
| Yale OMOP gold (`/mnt/raid0/rbc58/omop/gold`) | persons, conditions (ICD-10), drug orders, procedures, measurements, visits, deaths | cohorts, covariates, hdPS panel, outcomes (phase 2) |
| Echo EF (`mm_vhd/metadata/echo_accession_number.parquet`) | EF per echo | LVEF covariate (clinical PS), EF eligibility |
| Structured echo reports (`bb2238/metadata/echo_metadata_2026_06_12.parquet`) | ~797K reports, 2015–2026 | **evaluation only** (never in any PS) |
| ECG metadata and waveforms (`mm_vhd/metadata/ecg_metadata.parquet`, `bb2238/signals/preprocessed/all_ecgs`) | 12-lead, 500 Hz | ECG representation |
| BCL encoder (lead_time_transformer, 08/26/2026, epoch 30) | frozen, 256-d, µV input | primary ECG representation |
| CLMBR-T (code-only) | frozen EHR foundation model | sensitivity |

## 3. Trials

**Inclusion rule** (fixed before building):
- an active-comparator emulation is feasible in OMOP gold;
- a published primary result exists;
- the smaller arm has ≥ 300 patients with a selected ECG.

**Roles** were fixed before any balance result was viewed:
- *physiology*: cardiac function plausibly drives treatment choice;
- *control*: no ECG-specific benefit is expected.

**Emulation rating rubric** (0–2 per item; close ≥ 8, moderate 6–7, limited ≤ 5; a placebo-controlled RCT emulated with a proxy comparator scores 0 on comparator fidelity):
- comparator fidelity;
- key eligibility;
- time zero/setting;
- endpoint measurability in the EHR;
- data sufficiency (clinical-PS pairs ≥ 800 = 2; 400–799 = 1; < 400 = 0).

| Trial (adapted) | Role | Comparison | Benchmark (verified) | Rating |
|---|---|---|---|---|
| COMET | physiology | metoprolol vs carvedilol | HR 0.83 (0.74–0.93), carvedilol vs metoprolol; all-cause death | moderate |
| PARADIGM-HF | physiology | ARNI vs ACEi (new users) | HR 0.80 (0.73–0.87); CV death / HF hospitalisation | limited |
| PARADIGM-HF switcher | physiology | ARNI switchers vs ACEi continuers | same | moderate (7) |
| PARAGON-HF | physiology | ARNI vs valsartan | RR 0.87 (0.75–1.01) | limited |
| TRANSFORM-HF | physiology | torsemide vs furosemide | HR 1.02 (0.89–1.18); all-cause death | moderate |
| ELITE II | physiology | ARB vs ACEi | HR 1.13 (0.95–1.35); all-cause death | moderate |
| LIFE | physiology | ARB vs cardioselective β-blocker, ECG-LVH | HR 0.87 (0.77–0.98); CV death/MI/stroke | close |
| DIONYSOS | physiology | dronedarone vs amiodarone | HR 1.59 (1.28–1.98); AF recurrence/discontinuation | moderate |
| DAPA-HF / EMPEROR-Reduced | physiology | SGLT2i vs DPP-4i (T2D, HFrEF) | HR 0.74 (0.65–0.85) vs placebo | limited (4): placebo trial, proxy comparator, 375 pairs |
| PARTNER 2A/3 | physiology | TAVR vs surgical AVR | HR 0.89 (0.73–1.09); death/disabling stroke at 2 y | moderate (7): 342 pairs, strong risk-based selection |
| PLATO | control | ticagrelor vs clopidogrel | HR 0.84 (0.77–0.92) | close |
| ARISTOTLE | control | apixaban vs warfarin | HR 0.79 (0.66–0.95) | close |
| ROCKET-AF | control | rivaroxaban vs warfarin | HR 0.88 (0.74–1.03), ITT | close |
| RE-LY | control | dabigatran vs warfarin | RR 0.66 (0.53–0.82) | moderate |
| ALLHAT | control | amlodipine vs thiazide | RR 0.98 (0.90–1.07) | moderate |

Not analysed:
- TRITON (278 prasugrel users with an ECG);
- PARAGON-HF switcher (251);
- LIFE v1 (226 atenolol users; replaced by the class adaptation v2 before any balance was
  viewed).

Specs are in `scripts/trial_specs.py`; decisions are in `docs/DECISIONS.md`.

## 4. Target-trial elements (common to all trials unless the spec says otherwise)

| Element | Specification |
|---|---|
| Eligibility | Trial-specific gate and exclusions (specs). Age ≥ 18 (or the trial minimum). ≥ 365 d prior EHR activity. An unknown value passes the safety exclusions (documented adaptation) |
| Treatment strategies | Initiation of arm drug A vs arm drug B (first-ever order; no order of the other arm in [index−365, index]). Switch design and procedure designs as specified |
| Assignment | Observational; adjustment by PS matching (§6) |
| Time zero | First qualifying order/procedure date |
| Follow-up (phase 2) | From the day after index until the earliest of: outcome, death, end of data (2024-12-31 for death), 365 d/730 d (trial-matched horizon **[OPEN]**) |
| Outcome (phase 2) | Trial primary endpoint mapped to EHR events (§9) |
| Estimand | Initiator (ITT-like) effect; per-protocol as sensitivity **[OPEN]** |
| Population | **Primary: all initiators. Sensitivity: outpatient initiators** (index order not during an inpatient stay) |

## 5. Covariates and representations

- **Sparse base ("sparse"):** age, sex, index year, plus investigator-selected cardiology
  diagnoses in the prior 365 d (IHD/MI, AF, HTN, DM, CKD, stroke, COPD/asthma, PAD, valve
  disease) and trial extras.
- **Clinical PS (reference):** sparse + LVEF (echo, 365 d), SBP, DBP, HR, BMI, creatinine, K, Na,
  Hb (latest; 90 d for labs and vitals, 365 d for BMI), trial-relevant medication orders (90 d)
  and visit counts (365 d).
  - Missing values: 5 chained-equation imputations (sklearn IterativeImputer, sample_posterior,
    treatment as predictor), fitted within each analysis population.
- **ECG:** latest ECG in [index−365, index] (index day allowed). Frozen BCL with µV input; the first
  32 centred principal components enter the PS as covariates.
- **hdPS (exposure-only):** pool-A codes (half of the pre-index panel), once/sporadic/frequent
  levels, ranked by |log prevalence ratio|, top k = 200 (primary); 100 and 500 as sensitivity.
  Prior orders of the study drugs are excluded.

## 6. PS arms (frozen list)

| Arm | Covariates |
|---|---|
| M0 | unadjusted |
| M1 sparse | sparse base |
| **M2 sparse + ECG** | M1 + 32 ECG PCs |
| **M3 hdPS200** | M1 + 200 hdPS flags |
| **M4 hdPS200 + ECG** | M3 + 32 ECG PCs |
| R clinical (reference) | clinical PS |

Sensitivity arms:
- hdPS100 and hdPS500 (± ECG);
- all 3-character diagnosis codes instead of the selected list;
- claims-like (M1 + medications + visits);
- CLMBR code-only 64 PCs;
- clinical + ECG;
- noise placebo (M1 + 32 N(0,1) columns);
- **[OPEN]** a supervised structural-heart-disease ECG encoder (PRESENT-SHD or out-of-cohort
  heads), with its leakage handling in §12.

**Matching:** 1:1 greedy nearest-neighbour on the PS logit (L2 logistic, standardised
covariates), caliper 0.2 × pooled SD, anchored on the smaller arm, without replacement.
Secondary: overlap weighting **[OPEN]**.

## 7. Balance evaluation (phase 1)

Domains (none enters any PS except those listed as covariates in §5):
- medications;
- healthcare use;
- rest of the coded record (pool B: the other half of the pre-index panel);
- core-9 physiology (measured values only);
- echo domains from the structured echo report, latest in [index−365, index−1]:
  - LV structure (IVSd, LVPWd, LVIDd, LVEDVi, LVESVi, wall-thickness grade, IVSd > 15 mm)
  - LV function (EF, SVi, GLS, systolic grade)
  - diastolic/LA (E/A, E/e′, e′, LAVi, LA size, diastolic grade, LVDD)
  - RV/pulmonary (TAPSE, RV S′, RVSP, RVIDd, RAP, RV size and function)
  - valves (AV Vmax/mean gradient, TV gradient, AS/AR/MR/TR grades, moderate/severe flags)
  - aortic root
  - echo performed (yes/no);
- NT-proBNP and 9 other labs;
- an external prognostic risk score (fit on patients outside each cohort; 1-y death or a
  trial-type composite).

Metrics:
- **Excess |SMD| over chance**, per variable, averaged within each domain. Chance is the
  expected |SMD| under randomisation given the measured counts in each matched arm.
- **Capture %** = 1 − excess(arm)/excess(unmatched), where unmatched excess ≥ 0.02.
- Pool-B share of |SMD| > 0.1 with chance floor.
- Post-matching C-statistic.
- Retention (pairs).
- Grid: 5 imputations × 5 panel splits.

Pre-specified tests (medians across trials, with counts of trials improved):
- H1: M2 vs M1 and M4 vs M3 capture, per domain.
- H2: the (M2 − M1) change in excess on LV structure, LV function and core-9, physiology vs
  control (one-sided Mann-Whitney; exploratory given n ≈ 7–10 per group).
- H3: share of the (M1 − R) gap closed by M2, M3, M4.
- H4: ranking of per-domain M2 gains.

## 8. Phase-2 effect estimation (only after this protocol is frozen)

- For each trial, arm and imputation: Cox model of the trial-mapped outcome in the matched cohort
  (robust SE clustered on pair), pooled by Rubin's rules.
- Outcome definitions per trial: `trial_specs.PUBLISHED` endpoint. The EHR mapping is
  **[OPEN]**, because there is no cause of death, so CV death is replaced by all-cause death as a
  documented deviation.
- **Agreement metrics:**
  - (a) versus the full-data reference estimate R: difference in log-HR and CI overlap;
  - (b) versus the RCT, per RCT-DUPLICATE: estimate agreement (point estimate in the RCT CI),
    regulatory agreement (same direction and significance), standardised difference.
- Across trials: paired comparison of |log-HR − log-HR_R| and |log-HR − log-HR_RCT| for M2 vs M1
  and M4 vs M3 (Wilcoxon signed-rank), stratified by role and emulation rating.
- **Negative-control outcomes** **[OPEN]**: candidates are cataract surgery, inguinal hernia repair,
  hip/wrist fracture and influenza vaccination. Expected HR ≈ 1 for every comparison.

## 9. Reporting

Report every trial attempted, including failures and "limited" ratings. Report the primary and
sensitivity populations, all arms, retention, and all balance domains, whatever the direction of
the result.

## 10. Code and reproducibility

- Pipeline: `scripts/run_trial_pipeline.sh`, `run_v3_trial.sh`, the capture queue and
  `summarize_capture.py`.
- Every run writes a fresh private directory with a manifest. Aggregate outputs only in Git.

## 11. Timeline

1. Ryan resolves the [OPEN] items.
2. Freeze v1 (tag the commit).
3. Extract outcomes.
4. Run phase 2 once.

## 12. Choices made after viewing balance results (disclosure)

- Exposure-defining drug features were removed after inspecting the COMET C-statistic.
- The chance correction was added after the small-sample outpatient results.
- The switcher design was added after seeing that PARADIGM/PARAGON excluded the usual switch path.
- The primary population was changed from outpatient back to all initiators (Ryan: broader
  inclusion).
- The echo evaluation source was changed from PanEcho labels to the full echo report.
- **Supervised SHD encoder (proposed after seeing the valve result).** 35–42% of each cohort
  (23% in ALLHAT) is in the PRESENT-SHD training set. Its echo-based balance must therefore be
  assessed only in patients not in that training set, or heads must be retrained out-of-cohort.
