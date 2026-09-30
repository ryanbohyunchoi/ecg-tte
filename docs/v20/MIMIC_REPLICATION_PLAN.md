# v2.0 MIMIC-IV external replication: plan (committed before any result; 2026-09-30)

**Purpose.** Test in MIMIC-IV the project's headline finding: adding AI-ECG embeddings (BCL encoder, 32 PCs) to a propensity score (PS) improves balance on held-out characteristics. Secondary: agreement with RCT results.
- **Basis:** `docs/v20/MIMIC_FEASIBILITY.md` and `audits/claude-v20-mimic-feasibility/`.
- **Status:** exploratory external replication.
- **Access:** the PI authorised agent access to MIMIC on 2026-09-30.
- **Privacy:** aggregates only, with counts 1–10 suppressed. Note text is never opened, and no patient rows are printed.
- **Where things are written:** outputs in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-mimic-replication/` (umask 077); code in `scripts/v20/`.

## 1. Trials

**A. Built in v1.5** (reused unchanged: cohort, baseline, panel, ECG embeddings, outcomes, `rct.json`):
- PLATO (ticagrelor vs clopidogrel);
- ARISTOTLE (apixaban vs warfarin);
- ROCKET AF (rivaroxaban vs warfarin);
- TRANSFORM-HF (torsemide vs furosemide);
- COMET (metoprolol vs carvedilol).

**B. New.** Cohorts follow the frozen definitions of `claude-v20-mimic-feasibility/feasibility_screen.py`: in-hospital new user, active comparator; time zero = first qualifying order or infusion; ties excluded; washout; age ≥ 18; calendar gate; disease or ICU gates as listed. Treated = the first-listed arm.

| Trial | Treated vs comparator | Gate | Primary outcome (MIMIC) | RCT benchmark (verified from the PubMed abstract) |
|---|---|---|---|---|
| SOAP II | dopamine vs norepinephrine; first ICU infusion; no other vasopressor at or before t0 | none | all-cause death ≤ 28 d | OR 1.17 (0.97–1.42), death at 28 d; De Backer, NEJM 2010;362:779 (PMID 20200382). Odds ratio, flagged |
| ELITE II (class) | ARB vs ACE inhibitor, enteral; washout of ACEi/ARB/ARNI | heart failure (any) | all-cause death ≤ 365 d | HR 1.13 (95.7% CI 0.95–1.35); Pitt, Lancet 2000 (trial_specs PUBLISHED) |
| PEPTIC (**negative-control trial**) | PPI vs H2RA, enteral or IV, within the first 48 h of ICU | invasive ventilation spanning t0 | all-cause death ≤ 90 d | RR 1.05 (1.00–1.10), in-hospital death by day 90; Young, JAMA 2020;323:616 (PMID 31950977). Risk ratio, flagged |

**Deviations in the new cohorts:**
- SOAP II and PEPTIC ascertain death from MIMIC `dod`, which covers out-of-hospital deaths up to 1 year after discharge; every horizon here is ≤ 365 d from an in-hospital t0.
- PEPTIC uses all-cause death at 90 d rather than in-hospital death by day 90, which avoids censoring at discharge.
- Trial exclusion criteria beyond the gates are not applied.

**Summary sets:**
- **Primary:** the 7 cardiovascular trials (A plus SOAP II and ELITE II).
- **PEPTIC:** reported separately as the negative-control trial.
- **All 8 trials:** sensitivity analysis.

The new trials are built with a v20 builder that mirrors `v15_mimic_cohort.py` for baseline, panel and outcomes, using the same covariate definitions. The medication covariates are a fixed generic set: aspirin, statin, beta-blocker, ACEi/ARB, loop diuretic, anticoagulant, PPI and insulin, with any of the trial's own exposure classes removed. Their ECGs are selected, converted and embedded with the unchanged v1.5 pipeline (`v15_mimic_ecg_pipeline.py`): the latest 12-lead ECG in [t0 − 365 d, t0], the same BCL checkpoint and ×1000 µV fix, and 256-d embeddings.

## 2. Held-out balance panel (never in the PS under evaluation)

The latest value in [t0 − 365 d, t0) for labs; the other blocks use the windows below. Observed values only, never imputed.

| Block | Characteristics | Held out for |
|---|---|---|
| A. Core labs and vitals (v1.5 `labs_vitals`) | creatinine, potassium, sodium, hemoglobin, SBP, DBP, heart rate, BMI | demographic, sparse and hdPS (they are in the clinical PS) |
| B. Additional labs | NT-proBNP, troponin T, lactate, albumin, BUN, WBC, platelets, INR, LDL, HbA1c, total bilirubin, ALT, bicarbonate (itemids as in `panel_coverage.py`; plausibility ranges fixed in code) | every PS |
| C. ICU state | invasive ventilation spanning t0 | every PS (constant in PEPTIC, so dropped there) |
| D. Utilisation (v1.5 `util`) | prior admissions in 365 d, ED visits in 365 d, days from admission to t0, ICU before t0 | demographic, sparse and hdPS (they are in the clinical PS) |

- **Primary panel:** A + B + C + D (26 characteristics) for the demographic PS; B + C (14) for the clinical PS.
- **Secondary panel:** missingness indicators of A and B.
- **Echocardiography is excluded.** The structured echo-measurement table on disk (another user's folder) has an unrecorded release version and data-use status (feasibility report §6.3). It will be added only after the PI confirms its provenance, as a labelled post-plan addition.
- **Also excluded:** ECG `machine_measurements`, which are derived from the same ECG, and all note-derived variables.

## 3. PS ladder and arms

| Base PS | Covariates (v1.5 definitions) |
|---|---|
| **Demographic (primary)** | age, sex, estimated index year |
| Sparse | demographic + diagnoses |
| hdPS200 | sparse + top-200 hdPS levels (v1.5 `TrialData.hd`) |
| Clinical-lite | v1.5 `clinical`: demo + dx + meds + labs/vitals (single iterative imputation, as v1.5) + utilisation |

For each base PS, three arms: **PS alone**, **PS + ECG** (32 PCs of the 256-d embedding, computed within each trial as in v1.5), and **PS + permuted ECG** (the same 32 PCs shuffled between patients within the trial; fixed seed 20261001).
- **Estimation:** PS by L2-penalised logistic regression (C = 1, standardised).
- **Matching:** 1:1 greedy nearest neighbour on the PS logit, caliper 0.2 SD, anchored on the smaller arm (`v13_common.match`).
- **Outcome model:** Cox with robust SE clustered on pairs (`v13_common.cox`).

## 4. Metrics and tests

- **SMD:** `smd_vector`, i.e. NaN-aware arm means in the matched sample over the pooled SD of the analysed, unmatched rows.
- **Per trial and arm:**
  - % of panel characteristics with |SMD| < 0.1;
  - mean |SMD|.
- **Primary contrast:** demographic PS + ECG vs demographic PS alone.
  - Δ in % of characteristics with |SMD| < 0.1;
  - trials improved;
  - exact one-sided sign-flip test across trials (7 trials, minimum attainable p = 1/128);
  - relative reduction in mean |SMD| = 1 − mean_t(m_ECG) / mean_t(m_base), with a percentile bootstrap CI over trials (2,000 resamples; crude with 7 trials, so per-trial values are also shown).
- **Placebo:** the same statistics for permuted ECG vs PS alone.
- **Ladder:** the same statistics for sparse, hdPS200 and clinical-lite.
- **By block:** A, B and D separately (descriptive).
- **RCT agreement (secondary; trial primary outcome):**
  - per trial: log HR and 95% CI per arm, and |Δ log HR| vs the RCT;
  - across the 7 trials: Pearson r of log HRs, estimate agreement (HR within the RCT 95% CI), standardised-difference agreement (|z| < 1.96) and mean |Δ log HR|;
  - ECG vs PS alone: trials closer, and the sign-flip p.

  OR and RR benchmarks are used as given, and flagged.
- **Negative control (PEPTIC):**
  - HR per arm vs the benchmark RR 1.05;
  - whether the 95% CI covers 1.05;
  - whether the ECG changes the estimate;
  - the balance statistics.
- **ECG timing sensitivity:** all of the above repeated after excluding patients whose linked ECG is on the index day (`lag_days` < 1).

## 5. Gates and order of work

1. **Reproduction gate:** before any new analysis, the v1.5 primary-outcome estimates (arms unmatched, sparse, sparse+ECG, hdPS200, hdPS200+ECG, ECGonly and clinical) are recomputed for the 5 built trials with the v1.5 engine (`v15_analyze.TrialData`, `fit_matches`, `estimates`). They must equal `analysis/estimates.csv` (|Δ log HR| < 1e-9).
2. Run the balance and agreement analyses on the 5 built trials.
3. Build SOAP II, ELITE II and PEPTIC (cohort, baseline, panel and outcomes; then ECG selection, conversion and embedding). Before embedding, check the GPUs with `nvidia-smi` and use a free one. Run long jobs detached with `setsid nohup`.
4. Re-run the analyses for all 8 trials.
5. Write `docs/v20/MIMIC_REPLICATION.md`, with the verdict first and every deviation logged.
