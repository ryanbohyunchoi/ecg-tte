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
- **2026-09-26 (MIMIC cohorts), recorded before any outcome was analysed.**
  - **Cohort rebuild.** The cohorts were rebuilt once to exclude orders dated after discharge. The
    new cohorts are strict subsets of the old ones, with identical time zero and arm for every
    retained patient. Outcomes were extracted after the rebuild.
  - **Time zero:** the first oral or enteral order that starts before discharge.
  - **TRANSFORM-HF:** IV loop diuretic before time zero in the index admission is allowed and
    recorded as a covariate (`iv_loop_before_index`).
  - **Calendar and age:** `index_year` = anchor-year-group midpoint plus the within-patient year
    offset; age uses the same offset.
  - **Gates:**
    - ACS and HF (TRANSFORM-HF): in the index admission, or in an admission discharged within
      30 days.
    - AF, and HF for COMET: in the index admission or any earlier one.
  - **ICD-9 codes** are kept as separate panel features, because no GEMs mapping table is on disk.
  - **Negative controls** (appendicitis, inguinal hernia, cholelithiasis) have very few events and
    are uninformative; this is noted.
- **2026-09-26 (UK Biobank cohorts), recorded before any outcome was analysed.**
  - **Infeasible parts.**
    - DOAC vs warfarin: UKB coding 4 (field 20003) has no DOAC entries.
    - The GP new-user variant: the processed "meds" table is self-report mapped to RxNorm, not GP
      prescribing, and no GP-scripts file is on disk.
  - **Feasible comparisons:** ontarget (ARB vs ACEi, with ELITE II as a secondary benchmark on
    all-cause death), allhat (amlodipine vs thiazide) and ascot (amlodipine vs beta-blocker).
  - **Data end:** 2022-10-31, the latest hospital first-occurrence date. Visits after it are
    excluded.
  - **Outcomes.** All-cause death replaces CV/CHD death, because cause of death is not in the
    extract. The trials' age and high-risk eligibility criteria are not applied; the looser cohorts
    are counted only.
  - **Code panel.** The dx panel uses all history before index, because the source records only
    first occurrences.
  - **Biomarkers** come from instance 1 or 0, 4–10 years before index.
  - **CLMBR embeddings** are usable: the ID is the eid and the censor date is the imaging visit.
    They cover about 67% of each cohort, so CLMBR arms are analysed within the covered subset, and
    the main arms are re-run in that same subset for like-for-like comparison.
- **2026-09-26 (MIMIC negative controls v2), recorded before any NCO result was analysed.**
  Approved by Ryan via the coordinator. Eight hospital-coded negative-control outcomes are added
  alongside the original three, because those three have very few events:
  UTI (N39.0 / 599.0), osteoarthritis (M15–M19 / 715), diverticular disease (K57 / 562),
  hypothyroidism (E03 / 244), cataract (H25–H26 / 366), benign prostatic hyperplasia (N40 / 600;
  men only), glaucoma (H40 / 365) and dorsalgia/back pain (M54 / 724).
  - **Definition:** same as the original three. Any-position diagnosis in a later admission,
    dated to the admission start. Death censors. Truncated at `horizon_days`. NaN if the code
    occurred in the index admission or in an admission in the prior 365 days.
  - **Files:** the columns are added to `outcomes.parquet`; the primary `t` and `e` are
    unchanged. The previous file is kept as `outcomes_preNCO.parquet`.
  - **Diverticular disease made bleeding-free (same day, coordinator decision, before any NCO
    analysis).** The with-bleeding codes, checked against `d_icd_diagnoses`, no longer count as
    events: K57.01, K57.11, K57.13, K57.21, K57.31, K57.33, K57.41, K57.51, K57.53, K57.81, K57.91,
    K57.93 and ICD-9 562.02, 562.03, 562.12, 562.13. Any K57 or 562 code, bleeding ones included,
    still sets the prior/index exclusion to NaN. Only `t_nco_diverticular` and
    `e_nco_diverticular` were overwritten. The previous file is kept as
    `outcomes_preDIVfix.parquet`.

## Independent audit of v1.5, 2026-09-26: corrections

The audit report is in `docs/AUDIT_V15_2026_09_26.md`. Each correction below was decided before
the corrected results were seen.

1. **Pooled inference.**
   - **Headline:** pool per RCT (average within each RCT across cohorts, 18 RCTs), then run an
     exactly enumerated sign-flip test.
   - **Reported descriptively only:** the 26-emulation count, which treats emulations as
     independent although they share RCT benchmarks.
   - **Mechanics:** `sign_flip` now enumerates exactly up to 20 units. Before, it used a
     20,000-draw Monte Carlo above 16.
2. **MIMIC baseline.**
   - **The problem:** index-admission discharge diagnoses were included in the baseline and in
     the hdPS panel. Some are consequences of treatment or post-time-zero events: E93x
     anticoagulant adverse effects, abnormal INR 790.9x, long-term anticoagulant use V58.6x,
     cardiac arrest I46, shock R57, palliative care Z51.
   - **New primary:** diagnoses from earlier admissions only. The gate diagnosis is still allowed
     from the index admission, to define eligibility.
   - **Sensitivity:** the original specification.
3. **MIMIC outcomes.** An MI or stroke readmission within 28 days of the index discharge counts
   only if it is a new event: I22, or the primary diagnosis position (`seq_num` = 1). This
   mirrors the Yale v1.2 rule. It stops the index event's codes, which are carried forward for
   4 weeks, being counted again.
4. **UK Biobank ECG and exposure.**
   - The ECG is recorded at the same visit that defines prevalent exposure, so it partly reflects
     the drug's effect (e.g. beta-blockers). This is labelled as an on-treatment covariate.
   - **Sensitivity:** the trials' own eligibility criteria (ASCOT: no prior CHD or MI; ALLHAT:
     age 55 or older; ONTARGET: age 55 or older with CVD or diabetes). This also reduces the
     problem that MI can be detected only once per person.
5. **Engine validation.** The LIFE validation reproduces the unmatched estimate exactly. The
   matched arms differ by up to 0.55 SE, which is design-related. The claim is reworded and
   re-validated with Yale's exact design.
6. **Yale implication.** Yale in-hospital-initiation trials may share the problem in item 2:
   inpatient billing diagnoses are dated at admission, before the order. This is flagged for a
   Yale sensitivity analysis.
