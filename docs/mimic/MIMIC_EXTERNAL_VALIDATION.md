# MIMIC-IV external validation: ECG and CLMBR-T (consolidated, 2026-10-14)

This document supersedes the scattered MIMIC notes (v1.5, v20, v21; §10) for the current design. It covers the PS-CVD5 analog ± ECG (the existing analysis, re-run and gated) and the CLMBR-T arms added on 2026-10-14 (queue `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR.md`).

- **Code:** `scripts/mimic/` (entry point `run_mimic_external.py`). It imports `scripts/v20/mimic_replication.py`, `mimic_summary.py`, `scripts/v21/mimic_cvd5.py` and the Yale CLMBR-T encoder functions without modifying them.
- **Outputs:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014/` (umask 077). The restricted files (MEDS, embeddings, per-trial cells) stay there and are not committed.
- **Data handling:** MIMIC was read in place (the v1.5 staged tables; raw MIMIC-IV 3.1 `prescriptions` for NDC codes). Aggregates only; counts of 1–10 are suppressed; pair counts, retention and ESS are not given per trial; no note text was opened.

## Verdict

1. **Gate (Step 0): PASS.** The existing analysis, re-run from scratch, reproduces `docs/v21/MIMIC_PAPER2.md` exactly: 24 flag / cell / item tables with max |Δ| = 0, and the headline 6.6% (2.3–12.8), 6/7 trials lower, sign-flip P = .016, % |SMD| < 0.1 45.6 → 51.6, permuted ECG −3.1% (v20 bootstrap convention). The new analysis code reproduces every v21 base / ECG / permuted-ECG cell with max |Δ| = 0.
2. **CLMBR-T is usable in MIMIC (coverage gate GO).** 82.1% of the analysed patients' coded events are in the CLMBR-T dictionary (Yale s31: 78.5%). The median is 211 (93–490) in-vocabulary events per patient (Yale 308 (104–757)), and 0.2% of patients have no prior coded history (Yale: < 11 of 313,867). The model and runtime hashes equal Yale's.
3. **Balance (7 cardiovascular trials, PS-CVD5 analog; utilisation masked for the CLMBR-T arms):**
   - **+ ECG:** 6.6% (2.4 to 13.1), 6/7 trials lower, P = .016 (the v21 point estimate; 4,000-resample CI). Yale s31: 8.7% (4.2 to 13.5).
   - **+ CLMBR-T:** 23.1% (16.0 to 28.9), 7/7, P = .008. Yale: 12.9% (7.6 to 18.3).
   - **+ ECG + CLMBR-T:** 29.0% (21.6 to 37.1), 7/7, P = .008. Yale: 14.6% (7.7 to 21.1).
   - **Placebos:** permuted ECG −3.1% (−5.6 to −0.3); permuted CLMBR-T −0.6% (−4.6 to 4.5). Each real arm beats its placebo: ECG 9.4% (6.2 to 14.0), 7/7; CLMBR-T 23.6% (14.0 to 30.4), 6/7.
4. **Does the ECG still add once CLMBR-T is in? In MIMIC, yes in the primary analysis; not in every variant.** + ECG + CLMBR-T vs + CLMBR-T: 7.7% (3.0 to 14.1), 6/7 trials lower, P = .016. It holds without index-day ECGs, with index-admission codes in the base and in all 8 trials (7.2–9.8%), and it is larger when CLMBR-T reads only history before the index admission (11.9%, 6.9 to 16.8; 7/7). It does not hold with any diabetes in place of T2D (0.6%, −5.9 to 8.9; 3/7). At Yale it is 2.0% (−3.5 to 6.9), P = .24.
5. **RCT agreement: closer with CLMBR-T, but not trial-specific.** Mean |Δ log HR| 0.344 (PS-CVD5) → 0.326 (+ ECG) → 0.260 (+ CLMBR-T; 6/7 closer, P = .023) → 0.249 (+ both). The permuted placebos also move it (0.323 and 0.317). The benchmark-permutation P is .70 for + CLMBR-T and .43 for + both, so the improvement is not trial-specific (attenuation, not agreement). This is the same reading as at Yale.
6. **PEPTIC (negative control, RCT RR 1.05):** PS-CVD5 HR 1.51 (1.35–1.69); + ECG 1.39 (1.24–1.55); **+ CLMBR-T 1.00 (0.90–1.11)**; + both 0.95 (0.85–1.06); permuted ECG 1.60; permuted CLMBR-T 1.43 (1.28–1.61). CLMBR-T removes the confounding by illness severity in this non-cardiac comparison, as the measured-physiology (clinical-lite) PS did in v20 (0.98); the ECG removes part of it. With history before the index admission only, CLMBR-T gives 1.28 (1.14–1.43): the null is recovered only by the in-hospital pre-t0 stream.
7. **Cell validity:** 0 failed cells (< 11 pairs) and 0 cells failing the overlap rule, in every base and population. 1 of 8 + CLMBR-T cells and 3 of 8 + ECG + CLMBR-T cells retain 50–90% of the smaller arm; all other cells retain ≥ 90%. Median in-sample C: PS-CVD5 0.662, + ECG 0.704, + CLMBR-T 0.793, + both 0.807.
8. **Reading.** CLMBR-T's gain in MIMIC is about twice Yale's. The MIMIC PS-CVD5 analog is thin (hospital-only, earlier-admission diagnoses; prevalences 3–37%), while CLMBR-T reads the index admission's pre-t0 lab and order stream, which carries acuity and is close in time to the held-out lab values. **Restricted to history before the index admission, CLMBR-T gives 7.7% (3.0 to 14.0), about the ECG's 6.6%, and the ECG then adds 11.9% (6.9 to 16.8; 7/7)** (§8). The large primary CLMBR-T gain should therefore be read as "the in-hospital record before t0", not "prior history". As at Yale, CLMBR-T stays a comparison arm, not a take-home claim.

## 1. Results (primary: 7 cardiovascular trials, PS-CVD5 analog, all analysed patients)

Rel. red. = relative reduction in the across-trial mean |SMD|. Items: 26, or 22 when a CLMBR-T arm is in either cell (utilisation masked). P: exact sign-flip across trials (one-sided unless marked two-sided). Yale s31: 54 items, 31 trials (`docs/s31/S31_RESULTS.md`; `audits/claude-s31-20261014/summary_v1/contrasts.csv`).

| Contrast | MIMIC rel. red. (95% CI) | Trials lower; P | % \|SMD\| < 0.1 | Mean \|Δ log HR\| (closer) | Yale s31 rel. red. (95% CI) | Yale trials lower; P |
|---|---|---|---|---|---|---|
| + ECG vs PS-CVD5 | 6.6% (2.4 to 13.1) | 6/7; .016 | 45.6 → 51.6 | 0.344 → 0.326 (4/7) | 8.7% (4.2 to 13.5) | 20/31; <.001 |
| + CLMBR-T vs PS-CVD5 | 23.1% (16.0 to 28.9) | 7/7; .008 | 44.2 → 57.8 | 0.344 → 0.260 (6/7) | 12.9% (7.6 to 18.3) | 23/31; <.001 |
| + ECG + CLMBR-T vs PS-CVD5 | 29.0% (21.6 to 37.1) | 7/7; .008 | 44.2 → 64.3 | 0.344 → 0.249 (6/7) | 14.6% (7.7 to 21.1) | 23/31; <.001 |
| **+ ECG + CLMBR-T vs + CLMBR-T** | **7.7% (3.0 to 14.1)** | **6/7; .016** | 57.8 → 64.3 | 0.260 → 0.249 (3/7) | 2.0% (−3.5 to 6.9) | 18/31; .238 |
| + ECG + CLMBR-T vs + ECG | 23.6% (18.5 to 27.7) | 7/7; .008 | 51.9 → 64.3 | 0.326 → 0.249 (7/7) | 6.6% (−0.0 to 12.6) | 18/31; .028 |
| + CLMBR-T vs + ECG (two-sided) | 17.2% (9.4 to 23.1) | 7/7; .016 | 51.9 → 57.8 | 0.326 → 0.260 (5/7) | 4.7% (−1.2 to 9.6) | 23/31; .126 |
| + ECG vs + permuted ECG | 9.4% (6.2 to 14.0) | 7/7; .008 | 46.7 → 51.6 | 0.323 → 0.326 (4/7) | 8.3% (4.0 to 12.7) | 24/31; <.001 |
| + CLMBR-T vs + permuted CLMBR-T | 23.6% (14.0 to 30.4) | 6/7; .016 | 45.5 → 57.8 | 0.317 → 0.260 (5/7) | 11.0% (4.6 to 16.7) | 26/31; <.001 |
| + permuted ECG vs PS-CVD5 (two-sided) | −3.1% (−5.6 to −0.3) | 2/7; .094 | 45.6 → 46.7 | 0.344 → 0.323 (4/7) | 0.4% (−3.5 to 4.3) | 14/31; .834 |
| + permuted CLMBR-T vs PS-CVD5 (two-sided) | −0.6% (−4.6 to 4.5) | 3/7; .812 | 44.2 → 45.5 | 0.344 → 0.317 (2/7) | 2.2% (−2.5 to 6.7) | 17/31; .394 |

The % |SMD| < 0.1 of the base differs between rows (45.6 vs 44.2) only because CLMBR-T contrasts use the 22 unmasked items.

**RCT agreement by arm** (7 trials):

| Arm | r | Estimate agreement | Std-diff agreement | Mean \|Δ log HR\| | Benchmark-permutation P vs PS-CVD5 |
|---|---|---|---|---|---|
| PS-CVD5 | 0.69 | 0/7 | 4/7 | 0.344 | |
| + ECG | 0.69 | 1/7 | 4/7 | 0.326 | .84 |
| + CLMBR-T | 0.75 | 1/7 | 5/7 | 0.260 | .70 |
| + ECG + CLMBR-T | 0.76 | 4/7 | 6/7 | 0.249 | .43 |
| + permuted ECG | 0.70 | 1/7 | 4/7 | 0.323 | |
| + permuted CLMBR-T | 0.61 | 0/7 | 4/7 | 0.317 | |

**PEPTIC** (negative control; RCT RR 1.05; balance on 26 items, 22 for the CLMBR-T arms):

| Arm | HR (95% CI) | % \|SMD\| < 0.1 | Mean \|SMD\| |
|---|---|---|---|
| PS-CVD5 | 1.51 (1.35–1.69) | 30.8 | 0.179 |
| + ECG | 1.39 (1.24–1.55) | 42.3 | 0.155 |
| + CLMBR-T | 1.00 (0.90–1.11) | 40.9 | 0.129 |
| + ECG + CLMBR-T | 0.95 (0.85–1.06) | 54.5 | 0.116 |
| + permuted ECG | 1.60 (1.42–1.81) | 30.8 | 0.180 |
| + permuted CLMBR-T | 1.43 (1.28–1.61) | 31.8 | 0.183 |

Generated tables (every base, population and set; aggregates only): `audits/claude-mimic-clmbr-20261014/summary/tables.md` and `summary.json`.

## 2. Cohorts and time zero

MIMIC-IV 3.1 (hosp, ICU) with MIMIC-IV-ECG 1.0. Each emulation is an **in-hospital-initiation, new-user, active-comparator** design (protocol v1.5; v20 plan):
- **Time zero (t0):** the start time of the first inpatient order of either study drug (enteral, for the oral drugs); SOAP II: the first ICU vasopressor infusion; PEPTIC: the first PPI or H2RA order in the first 48 h of ICU.
- **Washout:** no order of either drug in any earlier admission, and none before t0 in the index admission (TRANSFORM-HF allows IV loop diuretic before t0). Ties at t0 are excluded.
- **Gates:** the disease concept coded in the index admission or an earlier one (ACS in PLATO and HF in TRANSFORM-HF: index admission or an admission discharged within 30 d); age ≥ 18; estimated calendar year ≥ the drug's availability year; PEPTIC: invasive ventilation spanning t0.
- **Treated** = the first-listed arm. **Analysed patients** = cohort ∩ baseline ∩ panel ∩ linked ECG ∩ outcome (`v15_analyze.TrialData`): 45,107 patient–index rows over the 8 trials (37,694 in the 7 cardiovascular trials).

## 3. Trials and benchmarks

| Trial | Treated vs comparator | Gate | MIMIC outcome | Horizon | RCT benchmark |
|---|---|---|---|---|---|
| PLATO | ticagrelor vs clopidogrel | ACS | death, or readmission with MI or stroke | 12 months | HR 0.84 (0.77–0.92) |
| ARISTOTLE | apixaban vs warfarin | AF | readmission with stroke or systemic embolism | 12 months (shortened) | HR 0.79 (0.66–0.95) |
| ROCKET AF | rivaroxaban vs warfarin | AF | readmission with stroke or systemic embolism | 12 months (shortened) | HR 0.88 (0.74–1.03) |
| TRANSFORM-HF | torsemide vs furosemide | HF admission | all-cause death | 12 months | HR 1.02 (0.89–1.18) |
| COMET | metoprolol (tartrate or succinate) vs carvedilol | HF | all-cause death | 12 months (shortened) | HR 1.205 (1.075–1.351) |
| SOAP II | dopamine vs norepinephrine | none (first ICU infusion; no other vasopressor at or before t0) | all-cause death | 28 d | OR 1.17 (0.97–1.42) (flagged: odds ratio) |
| ELITE II (class) | ARB vs ACE inhibitor | HF | all-cause death | 365 d | HR 1.13 (95.7% CI 0.95–1.35) |
| PEPTIC (negative-control trial) | PPI vs H2RA | ventilated ICU | all-cause death | 90 d | RR 1.05 (1.00–1.10) (flagged: risk ratio) |

- **Primary set:** the 7 cardiovascular trials. **PEPTIC** is reported alone as the negative-control trial; **all 8** is a sensitivity analysis.
- Death uses `patients.dod` (complete to about 1 year after discharge), hence the ≤ 12-month horizons. Readmission outcomes use later MIMIC admissions only.

## 4. Covariates: the PS-CVD5 analog

- **PS-CVD5 (MIMIC)** = v1.5 demographics (age, sex, estimated index year, with missingness indicators) + hypertension, type 2 diabetes, CAD/IHD, AF and HF flags, from **earlier admissions only** (admittime before the index admission; index admission excluded). Constant flags are dropped (the gate condition in some trials).
- **PS model:** L2 (ridge) logistic regression on standardised inputs, **fixed C = 1** for every arm.
- **Matching:** 1:1 greedy nearest neighbour on the PS logit, caliper 0.2 SD, without replacement, anchored on the smaller arm. Cells with < 11 pairs are failed.
- **Outcome model:** Cox, robust SE clustered on pairs.
- No race variable (as in v20). The index year is estimated from the de-identified anchor year group.

## 5. The ECG and CLMBR-T inputs

### 5.1 ECG (unchanged)

The latest 12-lead ECG in [t0 − 365 d, t0], **index day included**; the Yale BCL checkpoint (×1000 µV fix); 256-d embedding → **32 PCs within each trial**. Placebo: the PCs permuted between patients within the trial (seed 20261001).

### 5.2 CLMBR-T: MEDS build (Step 1; `build_mimic_meds.py`)

One MEDS subject per trial–patient–index (78,183 subjects; the same MIMIC patient in two trials is two subjects with two time zeros), built to match the Yale input (`scripts/build_comet_meds.py`):

| Source | Code strings | Timing |
|---|---|---|
| `diagnoses_icd` | ICD9CM / ICD10CM (dotted) mapped to standard concepts (SNOMED) through `CONCEPT_RELATIONSHIP` "Maps to", as in an OMOP condition table (Yale's codes are standard concepts; the CLMBR-T dictionary has no ICD-CM codes) | **earlier admissions only**, at that admission's discharge time |
| `procedures_icd` | ICD9Proc (dotted) / ICD10PCS (standard vocabularies, used directly) | earlier admissions only, at discharge |
| `prescriptions` (raw 3.1; the staged copy has no `ndc`) | NDC → RxNorm / RxNorm Extension through "Maps to" (OHDSI vocabulary with NDC 20240825, read in place: `/mnt/raid0/bb2238/agents/ohdsi/omop_vocabularies`; the project vocabulary has no NDC) | order start time < t0, any admission |
| `labevents` | LOINC from a curated itemid → LOINC map (96 items), otherwise `MIMIC_LAB/<itemid>` | chart time < t0, any admission or outpatient |
| `admissions` / `transfers` | `Visit/IP` (admission), `Visit/ER` (ED stay) | admit / ED in-time < t0 |
| `patients` | `MEDS_BIRTH` at 1 July of (anchor_year − anchor_age) | static |

**Rules and deviations from Yale, each forced by MIMIC:**
1. **No leakage past time zero.** Only events strictly before t0 enter. MIMIC diagnosis and procedure codes carry no reliable timestamp, so they are placed at their admission's discharge time and **every code of the index admission is excluded** (the PS-CVD5 analog uses earlier admissions only, too). Labs and medication orders from the index admission count only if timestamped before t0. **Checks (aggregate, over all 43.8 million events):** 0 events at or after t0; 0 index-admission diagnosis or procedure codes; 0 events before birth.
2. **Exposure drugs and the gate code are excluded** (queue rule): prescriptions matching the trial's exposure-drug tokens (the cohort builders' own drug strings) and diagnosis codes with the trial's gate prefixes. Yale's MEDS build applies no explicit filter (its new-user washout and index-day exclusion do this implicitly), so this is slightly stricter than Yale. The filter works on the order's drug string, as the cohort builders' washout does, so a few products whose string lacks the token pass (verification: 28 events of IV enalaprilat in ELITE II, and < 11 events each of a few others, including IV furosemide in TRANSFORM-HF, which that design allows before t0).
3. **Labs.** MIMIC-IV 3.1 `d_labitems` has no LOINC column (removed after v1.0) and no MIMIC lab → LOINC table exists on disk. Under the literal rule ("LOINC where `d_labitems` has it, otherwise the MIMIC itemid") every lab would be out of the CLMBR-T vocabulary, and only about 9% of events would be in the dictionary (the stop rule would fire on labs alone). A **curated map** (`scripts/mimic/lab_loinc_map.py`) covers the 96 most frequent test itemids. Each LOINC was checked against the OMOP CONCEPT table (all valid and standard; the label next to the LOINC long name is in `vocab/lab_loinc_verified.csv`). Where the first-choice code is not in the dictionary, an equivalent in-dictionary code was taken (for example bicarbonate → total CO2 2028-9; blood-gas pH, pO2 and total CO2 → the arterial codes). 95 of the 96 are in the dictionary (pCO2 is not); non-test items (hemolysis indices, hold tubes, specimen type, smear morphology) stay MIMIC itemid codes.
4. **Birth.** MIMIC has no birth date. Birth is placed at 1 July of (anchor_year − anchor_age); it agrees with the v1.5 age to the year in every subject. **Sex is not a token**, as at Yale (`build_comet_meds` v1 has no static sex or race tokens).
5. **emar** is not used: it carries no drug code (its rows repeat the `prescriptions` order through `pharmacy_id`). **Vitals** (chartevents, `omr`) are not coded, as the queue lists hosp sources only.
6. **Code-only:** no numeric values are written (`--numeric-mode code-only`, last **4,096** tokens), as at Yale.

### 5.3 Vocabulary coverage gate (Step 1.5; `coverage.py`)

| Statistic | MIMIC, analysed patients (8 trials; n = 45,107) | Yale, s31 trials (all cohort patients; n = 313,867) |
|---|---|---|
| Share of coded events in the CLMBR-T dictionary | 82.1% | 78.5% |
| In-vocabulary events per patient, median (IQR) | 211 (93–490) | 308 (104–757) |
| No prior coded history (birth only) | 0.2% | < 11 patients |
| More than 4,096 tokens (truncated) | 1.0% | 1.3% |
| No coded history outside the index admission | 14.9% | — (index day excluded at Yale) |

- **By domain (all 78,183 MEDS subjects):** diagnoses 88.1% in the dictionary, drug orders 60.5%, labs 83.4%, procedures 34.8%, visits 100%. Labs are 86% of all events.
- **Stop rule** (< 50% in the dictionary, or > 50% of patients with no prior coded history): **not fired**. Under the literal lab rule (no LOINC), about 9% of events would be in the dictionary and the rule would fire.
- The builder's in-vocabulary counts equal the tokenizer's accepted counts for every subject (78,183/78,183; verification report).

### 5.4 CLMBR-T inference (Step 2; `encode_mimic_clmbr.py`)

- Same checkpoint (`/mnt/raid0/eo287/clmbr`), femr 0.2.3 / meds 0.1.3, FEMR tokenizer and batch processor, torch seed 20260923, latest retained token representation (768-d), raw vectors. The model files and runtime versions **equal the Yale `manifest.json`** (sha256 of `config.json`, `dictionary.msgpack`, `model.safetensors`; femr, meds, torch, transformers, xformers, numpy, pyarrow).
- Two differences, both forced by MIMIC: (1) the cutoff is the exact t0 timestamp, not index-date midnight; (2) a subject with no tokenizer-supported clinical event is encoded from its birth event alone (a demographics-only embedding) and kept, not skipped.
- **CLMBR-T PCs:** 64 within each trial (`eval_longtail_balance.pcs` on the trial's analysed patients, as `v13_common.clm_pc`). Placebo: the PCs permuted between patients with the same within-trial permutation as the permuted ECG (seed 20261001).
- **Reproducibility:** BLAS runs single-threaded (`mimic_common` sets `OMP/OPENBLAS/MKL_NUM_THREADS=1`). Birth-only subjects with the same birth year share an embedding, so PS ties are broken by floating-point order. With multi-threaded BLAS the prior-only CLMBR-T cells move slightly (about 1e-3 in mean |SMD|).
- A 100-subject smoke test ran first. Inference ran on GPU 6 (shared; GPU 3 was taken by another job when the run started and GPU 7 is never used).

## 6. Held-out panel and leakage masks

**Panel:** 26 items, never PS inputs (unchanged from v20/v21): A core labs and vitals (8: creatinine, potassium, sodium, hemoglobin, SBP, DBP, heart rate, BMI), B additional labs (13: NT-proBNP, troponin T, lactate, albumin, BUN, WBC, platelets, INR, LDL, HbA1c, total bilirubin, ALT, bicarbonate), C ventilation at t0 (1), D utilisation (4). Observed values only; latest value in [t0 − 365 d, t0) for labs. **No echo** (provenance of the MIMIC echo table unverified). Balance = |SMD| after matching (pooled SD of the unmatched analysed rows).

**Mask for the CLMBR-T arms** (`pipeline.md` §6: mask any held-out item that is the same quantity as, derived from or the same code family as a model input):

| Item | Derivable from the CLMBR-T input? | Masked for CLMBR-T arms |
|---|---|---|
| D: admissions in the prior 365 d | yes (`Visit/IP` events with their times) | **yes** |
| D: ED visits in the prior 365 d | yes (`Visit/ER` events) | **yes** |
| D: days from admission to t0 | yes (the index `Visit/IP` time relative to the last pre-t0 event) | **yes** |
| D: ICU before t0 | partly (ICU-only lab patterns; no ICU transfer token) | **yes** (same family, masked with D) |
| A, B: lab and vital **values** | no (code-only: the model sees that a lab was ordered, not its value) | no (as at Yale, where the 54 items are not masked for CLMBR-T) |
| C: ventilation at t0 | no direct token (the blood-gas "intubated" and ventilator items are not in the dictionary); soft proxy: arterial blood-gas codes in the 24 h before t0 (phi 0.45 pooled, verification report), below the 0.80 masking threshold | no |
| Lab missingness indicators (secondary panel) | yes (which labs were ordered) | not used here |

A mask applies whenever a CLMBR-T arm (real or permuted) is in either compared cell, so CLMBR-T contrasts use 22 items. Items enter a contrast only where observed in both cells. The unmasked 26-item results are a sensitivity analysis.

## 7. Endpoints and tests

- **Primary:** relative reduction in mean |SMD| = 1 − mean_t(m_a) / mean_t(m_b), 95% CI from **4,000 trial-bootstrap resamples (seed 20261001)**; trials lower; **exact sign-flip P** (one-sided for a representation vs its base or its placebo; two-sided for a placebo vs base and for CLMBR-T vs ECG).
- **Secondary:** % of items with |SMD| < 0.1; mean |Δ log HR| vs the RCT, trials closer, sign-flip P and the **benchmark-permutation P** (RCT results reassigned across trials, 20,000 draws); Pearson r, estimate agreement and standardized-difference agreement; PEPTIC HR.
- **Cell validity:** the overlap rule (≥ 30% of the smaller arm matched or ≥ 50 pairs) as in the PROTECT AF audit; failed cells (< 11 pairs) are counted.
- **Note on the published v21 CIs:** `docs/v21/MIMIC_PAPER2.md` used the v20 bootstrap (2,000 resamples, seed 0). This document uses the paper convention (4,000, seed 20261001), so the ECG point estimates are identical and the CIs differ slightly.

## 8. Sensitivity analyses (7 cardiovascular trials unless stated)

Relative reduction in mean |SMD| (95% CI; trials lower). The first three rows are the existing design-detail sensitivities of v21, now with the CLMBR-T arms.

| Variant | + ECG vs PS-CVD5 | + CLMBR-T vs PS-CVD5 | + ECG + CLMBR-T vs PS-CVD5 | + ECG + CLMBR-T vs + CLMBR-T |
|---|---|---|---|---|
| **Primary** | 6.6% (2.4 to 13.1); 6/7 | 23.1% (16.0 to 28.9); 7/7 | 29.0% (21.6 to 37.1); 7/7 | 7.7% (3.0 to 14.1); 6/7 |
| Any diabetes instead of T2D (`cvd5_anydm`) | 11.8% (7.4 to 16.9); 7/7 | 29.0% (22.2 to 33.6); 7/7 | 29.4% (22.6 to 35.9); 7/7 | 0.6% (−5.9 to 8.9); 3/7 |
| Index-admission codes in the base (`cvd5_incl`) | 11.5% (7.0 to 17.7); 7/7 | 24.5% (18.9 to 29.4); 7/7 | 29.9% (22.4 to 36.3); 7/7 | 7.2% (4.0 to 11.3); 7/7 |
| No index-day ECG | 6.5% (−0.4 to 13.6); 5/7 | 17.4% (9.0 to 26.8); 7/7 | 25.5% (20.9 to 30.1); 7/7 | 9.8% (3.3 to 14.9); 6/7 |
| All 8 trials (with PEPTIC) | 7.6% (3.2 to 13.1); 7/8 | 24.8% (17.8 to 30.2); 8/8 | 30.8% (23.4 to 38.1); 8/8 | 8.0% (3.7 to 13.5); 7/8 |
| Utilisation not masked (26 items) | 6.6% (2.4 to 13.1); 6/7 | 29.1% (20.8 to 35.4); 7/7 | 34.7% (27.1 to 42.7); 7/7 | 7.8% (2.4 to 14.7); 6/7 |
| **CLMBR-T input = history before the index admission only** (`meds_prior`; see below) | 6.6% (2.4 to 13.1); 6/7 | 7.7% (3.0 to 14.0); 6/7 | 18.6% (12.5 to 26.7); 7/7 | 11.9% (6.9 to 16.8); 7/7 |

**History-before-the-index-admission sensitivity** (`build_meds_prior_only.py`, `run_mimic_external.py prior`; added after the primary CLMBR-T results were seen). The primary input follows the queue rule: labs and orders of the index admission count if timestamped before t0. That pre-t0 stream is close in time to the held-out lab values (latest value before t0, mostly from the same admission). The model does not see values, but ordering intensity is a soft proxy for them; such proxies are not masked under the `pipeline.md` §6 rules. Yale's input stops at the index day. Here every event at or after the index admission time is removed (analysed patients; 0 remaining events checked). This is approximate: labs and orders of the index ED stay before the admission time are kept (verification report: in most patients). 10.6% of patients are left with birth only; the median is 59 in-vocabulary events. Same checkpoint and hashes; same analysis code (v21 cells reproduced, max |Δ| 0; 0 failed or overlap-invalid cells).
- + CLMBR-T falls from 23.1% to **7.7% (3.0 to 14.0)**, about the ECG's size (CLMBR-T vs ECG 0.6%, −2.4 to 3.3) and smaller than Yale's 12.9%.
- The ECG adds **11.9% (6.9 to 16.8), 7/7**, on top of this CLMBR-T.
- Mean |Δ log HR| 0.344 → 0.278 (+ CLMBR-T) → 0.240 (+ both); benchmark-permutation P .95 and .57.
- PEPTIC: + CLMBR-T HR 1.28 (1.14–1.43), + both 1.21 (1.08–1.35): the null is no longer recovered.
- **Reading:** about two-thirds of CLMBR-T's MIMIC gain comes from the index admission's own pre-t0 stream, not from prior history.

- The ECG rows equal the v21 point estimates exactly (`summary.json` gates). The CIs differ from the v21 table only by the bootstrap convention (§7).
- As in v21, the ECG estimate moves by about ±5 points between near-identical bases. Across the five design-detail variants (any diabetes, index-admission codes, no index-day ECG, all 8 trials, unmasked), the CLMBR-T estimate moves less (17–29%) and is lower in every trial, and the ECG's added value on top of CLMBR-T ranges from 0.6% to 9.8%. The input-timing variant (history before the index admission) is the exception: CLMBR-T 7.7% (6/7), and the ECG adds 11.9%.
- Excluding overlap-invalid cells changes nothing (no cell fails the rule).

## 9. Limitations

- **Hospital-only history.** MIMIC records only BIDMC hospital episodes (and outpatient labs drawn there): no outpatient diagnoses or prescriptions. The CLMBR-T input is therefore thinner and differently composed than Yale's: 86% of its events are labs (30.2% of the analysed patients' lab events come from the index admission before t0, the rest from earlier admissions and outpatient draws), and 14.9% of analysed patients have no coded history outside the index admission.
- **12-month horizon** (death after discharge is captured only to about 1 year); several trials are shortened.
- **7 trials.** The bootstrap CI over 7 trials is crude; the per-trial direction and the exact sign-flip P (minimum one-sided P 1/128) carry the inference. Near-identical design variants move the ECG estimate by about ±5 points (§8).
- **Mapping choices made for MIMIC:** a curated lab LOINC map; NDC → RxNorm from a second OHDSI vocabulary; year-only birth; no vitals; prescriptions orders only (no administrations); about 14% of pre-t0 prescription rows have no NDC and are dropped.
- **Timing of the CLMBR-T input.** The primary input includes index-admission lab and order codes before t0, close in time to the held-out lab values; lab-ordering intensity is a soft proxy for the values and is not masked under the `pipeline.md` rules. Most of the primary CLMBR-T gain depends on it (§8: 23.1% → 7.7% with history before the index admission only). That sensitivity was added after the primary results were seen.
- **CLMBR-T was added after the Yale results** and after the MIMIC ECG results were known; it is reported as a comparison arm, as at Yale.
- **No echo** in the held-out panel; the Yale echo result is not replicated here.

## 10. History (older MIMIC documents; kept unchanged)

| Document | What it holds |
|---|---|
| [`docs/PROTOCOL_V1_5_EXTERNAL.md`](../PROTOCOL_V1_5_EXTERNAL.md) | v1.5 protocol (MIMIC and UK Biobank): the 5 built trials, cohort design, deviation log |
| [`docs/V15_EXTERNAL_SUMMARY.md`](../V15_EXTERNAL_SUMMARY.md) | v1.5 first-pass results |
| [`docs/v20/MIMIC_FEASIBILITY.md`](../v20/MIMIC_FEASIBILITY.md) | v20 feasibility screen (new trials, data inventory) |
| [`docs/v20/MIMIC_REPLICATION_PLAN.md`](../v20/MIMIC_REPLICATION_PLAN.md) | v20 plan (committed before results): trials, panel, PS ladder |
| [`docs/v20/MIMIC_REPLICATION.md`](../v20/MIMIC_REPLICATION.md) | v20 results: demographic PS ± ECG, ladder, PEPTIC |
| [`docs/v21/MIMIC_PAPER2.md`](../v21/MIMIC_PAPER2.md) | v21 PS-CVD5 analog ± ECG; design-detail sensitivities; window fix for paper 1 |
| [`docs/mimic/VERIFY_MIMIC_CLMBR.md`](VERIFY_MIMIC_CLMBR.md) | independent verification of this document |
