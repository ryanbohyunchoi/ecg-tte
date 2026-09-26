# Protocol v1.5 (2026-09-26): external first pass in MIMIC-IV and UK Biobank (exploratory)

This protocol was registered before any outcome was extracted in either cohort, and is tagged
`protocol-v1.5`. It is a **first pass**: its aims are feasibility and direction of effect, not
confirmation. Deviations are logged, with dates, at the end of this file.

## Question

Does the pattern found at Yale replicate in two structurally different data sources?
- Sparse + ECG closer to the RCT than sparse.
- A small bias reduction in the plasmode.
- A larger gain when the coded record is thin.

In both cohorts the coded record is thinner than at Yale. MIMIC-IV has hospital episodes only.
UK Biobank has mainly hospital ICD-10 codes, with GP prescribing data for a subset.

## Cohorts and designs

### MIMIC-IV 3.1 + MIMIC-IV-ECG 1.0 (+ echo study list)

**Design.** In-hospital-initiation, new-user, active-comparator.
- Time zero is the first inpatient order (prescriptions/eMAR) of either study drug during an
  admission.
- There must be no order of either drug in any earlier admission, which is the washout.
- The disease gate is an ICD diagnosis during the index admission or any earlier one.
- Covariates are defined from the index admission up to time zero, and from all earlier admissions.

**Candidate trials** (the benchmarks are the same verified entries as in `trial_specs.PUBLISHED`):

| Trial | Comparison | Gate | Outcome | Horizon |
|---|---|---|---|---|
| PLATO | ticagrelor vs clopidogrel | ACS admission | death, readmission for MI or stroke | 12 months |
| ARISTOTLE | apixaban vs warfarin | AF | readmission for stroke or systemic embolism | 12 months (shortened) |
| ROCKET AF | rivaroxaban vs warfarin | AF | readmission for stroke or systemic embolism | 12 months (shortened) |
| TRANSFORM-HF | torsemide vs furosemide | HF admission | all-cause death | 12 months |
| COMET | metoprolol vs carvedilol | HF | all-cause death | 12 months (shortened) |

Horizons are capped at 12 months because death after discharge is captured only to about 1 year.
The truncation is a limitation.

**Death and follow-up.**
- Death uses `patients.dod`.
- Patients are censored at 365 days after their last recorded contact, or at the horizon if
  earlier.
- Readmission outcomes use `diagnoses_icd` of later admissions within MIMIC only.

**ECG.** The latest ECG in the 365 days before time zero, time zero included. Waveforms are
converted to the Yale npy layout and embedded with the same BCL checkpoint and PCs as at Yale.

### UK Biobank

**Design.** Prevalent-user, active-comparator, anchored at the imaging visit (instance 2), which
is when the ECG (field 20205) was recorded.
- Arms are defined by self-reported current medication at that visit (field 20003, UKB coding 4).
- A new-user design is possible only in the GP-prescribing subset (about 31k people). It is
  screened for feasibility and used where arms are large enough.
- Prevalent-user designs weaken the comparison with RCTs; this is a stated limitation.

**Candidate comparisons:**

| Comparison | Emulates | Outcome |
|---|---|---|
| ARB vs ACEi | ONTARGET / ELITE II-type | CV death, MI, stroke or HF |
| amlodipine vs thiazide | ALLHAT | CHD death or MI; here death or MI |
| amlodipine vs beta-blocker | ASCOT-BPLA | CHD death or MI; here death or MI |
| DOAC vs warfarin | AF anticoagulation | stroke |

Outcomes come from first-occurrence ICD-10 dates (41270/41280), algorithmic MI and stroke dates
(42000/42006) and death (40000). Horizon: the trial's own, capped by data availability. Cause of
death (field 40001) is not in the current extract, so all-cause death is used wherever CV death
would be; stated.

**Covariates.**
- Demographics.
- ICD-10 history before the visit.
- Visit measurements: SBP, BMI, smoking.
- Biomarkers from instance 0; stated.

## Arms

These match the Yale arms as closely as each data source allows.
- **M0** unadjusted.
- **M1** sparse: age, sex, calendar year (for MIMIC, the shifted year group), plus the selected
  diagnoses.
- **M2** sparse + ECG: 32 PCs.
- **M3** hdPS200: sparse + the top 200 coded levels, from a 365-day pre-index panel.
- **M4** hdPS200 + ECG.
- **ECG only.**
- **R clinical:** sparse + medications + labs and vitals.
- **CLMBR arms:** UK Biobank only, where embeddings exist and their censoring is at or before
  index.

Matching and estimation:
- 1:1 greedy caliper matching (0.2 SD of the logit).
- Cox model with SE clustered on pair.
- Missing covariates: single chained-equation imputation in this first pass, plus
  missing-indicator flags.

## Metrics and inference

- **Per arm, the RCT-DUPLICATE panel:**
  - significance agreement, estimate agreement and standardised-difference agreement;
  - Pearson r (with so few trials, reported only as descriptive);
  - ratio of ratios, Heyard dispersion φ and mean |Δlog HR|.
- **Paired contrasts, C1 = M2 vs M1 and C2 = M4 vs M3:**
  - per trial: Δ|log HR − RCT|;
  - per trial: precision-standardised z²;
  - across trials: exact sign-flip test, reported as descriptive with 3–5 trials.
- **Plasmode:** 80% subsampling, 200 replicates, base and phys_only scenarios, true HR 0.8.
  Report the bias reduction for C1 and C2.
- **Balance:** capture % on the physiology available, which is labs and vitals.
- **Feasibility rule, applied before outcomes are extracted:**
  - at least 200 per arm with an ECG;
  - at least 150 clinical-PS pairs.

  Trials failing the rule are reported as infeasible.

## Outputs

- Restricted outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-{mimic,ukb}-*`.
- Code: `scripts/v15/`.
- Aggregate summary: `docs/V15_EXTERNAL_SUMMARY.md`.

## Deviation log

(dated entries)
