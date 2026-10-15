# MIMIC-IV external validation: ECG and CLMBR-T (consolidated, 2026-10-14)

This document supersedes the scattered MIMIC notes (v1.5, v20, v21; §10) for the current design. It covers the PS-CVD5 analog ± ECG (the existing analysis, re-run and gated) and the CLMBR-T arms added on 2026-10-14 (queue `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR.md`).

> **Decision, 2026-10-15 (the user's):** the primary CLMBR-T input in MIMIC is **history before the index admission only**. Its gain had been driven by the index admission's own pre-t0 lab and order stream, which overlaps in time with the held-out lab values (§8). The first-run input (index-admission labs and orders before t0 included) is now a sensitivity analysis. This was decided after both results were seen and is disclosed as such. The ECG, PS-CVD5 and permuted-ECG cells are identical under both inputs.
>
> **What "history before the index admission" includes (audit 2026-10-15, `docs/mimic/AUDIT_MIMIC_PRIMARY_SWITCH.md`):** every event before the index *admission time*. That keeps the **index ED stay before admission**: 8.7% of input events, in 72% of patients; for 32.3% of patients it is the whole clinical input; 21.6% of the held-out lab values were measured in that ED window. Only 57.7% of patients have any input from before the index episode. The input is therefore "history before the index admission (index ED stay kept)", not "prior history only". It removes the inpatient pre-t0 stream but not all of the index episode.

- **Code:** `scripts/mimic/` (entry point `run_mimic_external.py`). It imports `scripts/v20/mimic_replication.py`, `mimic_summary.py`, `scripts/v21/mimic_cvd5.py` and the Yale CLMBR-T encoder functions without modifying them.
- **Outputs:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014/` (umask 077). The restricted files (MEDS, embeddings, per-trial cells) stay there and are not committed.
- **Data handling:** MIMIC was read in place (the v1.5 staged tables; raw MIMIC-IV 3.1 `prescriptions` for NDC codes). Aggregates only; counts of 1–10 are suppressed; pair counts, retention and ESS are not given per trial; no note text was opened.

## Verdict

1. **Gate (Step 0): PASS.** The existing analysis, re-run from scratch, reproduces `docs/v21/MIMIC_PAPER2.md` exactly: 24 flag / cell / item tables with max |Δ| = 0, and the headline 6.6% (2.3–12.8), 6/7 trials lower, sign-flip P = .016, % |SMD| < 0.1 45.6 → 51.6, permuted ECG −3.1% (v20 bootstrap convention). The new analysis code reproduces every v21 base / ECG / permuted-ECG cell with max |Δ| = 0.
2. **CLMBR-T is usable in MIMIC (coverage gate GO; gate run on the first-run input).** 82.1% of the analysed patients' coded events are in the CLMBR-T dictionary (Yale s31: 78.5%). The median is 211 (93–490) in-vocabulary events per patient (Yale 308 (104–757)), and 0.2% of patients have no prior coded history (Yale: < 11 of 313,867). The model and runtime hashes equal Yale's. Primary input: 83.4% in the dictionary, median 59 in-vocabulary events, 10.6% birth only, 42.3% with no input from before the index episode.
3. **Balance (7 cardiovascular trials, PS-CVD5 analog; utilisation masked for the CLMBR-T arms; CLMBR-T input = history before the index admission):**
   - **+ ECG:** 6.6% (2.4 to 13.1), 6/7 trials lower, P = .016 (the v21 point estimate; 4,000-resample CI). Yale s31: 8.7% (4.2 to 13.5).
   - **+ CLMBR-T:** 7.7% (3.0 to 14.0), 6/7, P = .023. Yale: 12.9% (7.6 to 18.3).
   - **+ ECG + CLMBR-T:** 18.6% (12.5 to 26.7), 7/7, P = .008. Yale: 14.6% (7.7 to 21.1).
   - **CLMBR-T vs ECG:** 0.6% (−2.4 to 3.3), 3/7, two-sided P = .734: about the same size.
   - **Placebos:** permuted ECG −3.1% (−5.6 to −0.3); permuted CLMBR-T −1.3% (−5.5 to 3.9). Each real arm beats its placebo: ECG 9.4% (6.2 to 14.0), 7/7; CLMBR-T 8.9% (5.6 to 11.9), 6/7.
4. **Does the ECG still add once CLMBR-T is in? In MIMIC, yes, in every variant of the primary input; not in one first-run variant.** + ECG + CLMBR-T vs + CLMBR-T: **11.9% (6.9 to 16.8), 7/7 trials lower, P = .008**. Across the design-detail variants it is 6.3–11.5% (any diabetes 6.3% (1.0 to 11.7); 6/7; §8). With the first-run input and the any-diabetes base it is 0.6% (−5.9 to 8.9; 3/7). At Yale it is 2.0% (−3.5 to 6.9), P = .24.
5. **RCT agreement: closer, but not trial-specific.** Mean |Δ log HR| 0.344 (PS-CVD5) → 0.326 (+ ECG) → 0.278 (+ CLMBR-T; 4/7 closer) → 0.240 (+ both; 6/7 closer). The permuted placebos also move it (0.323 and 0.314). The benchmark-permutation P is .84 for + ECG, .95 for + CLMBR-T and .57 for + both, so the improvement is not trial-specific (attenuation, not agreement). This is the same reading as at Yale.
6. **PEPTIC (negative control, RCT RR 1.05):** PS-CVD5 HR 1.51 (1.35–1.69); + ECG 1.39 (1.24–1.55); + CLMBR-T 1.28 (1.14–1.43); + both 1.21 (1.08–1.35); permuted ECG 1.60 (1.42–1.81); permuted CLMBR-T 1.61 (1.43–1.81). Both representations remove part of the confounding by illness severity in this non-cardiac comparison; neither reaches the null. The measured-physiology (clinical-lite) PS did in v20 (0.98), and so does CLMBR-T when it reads the index admission's pre-t0 stream (1.00 (0.90–1.11); sensitivity, §8).
7. **Cell validity:** 0 failed cells (< 11 pairs) and 0 cells failing the overlap rule, in every base and population. 1 of 8 + CLMBR-T cells and 1 of 8 + ECG + CLMBR-T cells retain 50–90% of the smaller arm; all other cells retain ≥ 90%. Median in-sample C: PS-CVD5 0.662, + ECG 0.704, + CLMBR-T 0.724, + both 0.755.
8. **Reading.** With history before the index admission, CLMBR-T improves balance about as much as the ECG (7.7% vs 6.6%), less than at Yale (12.9%). That is expected: MIMIC has no outpatient diagnoses or prescriptions, so the prior record is thin (median 59 in-vocabulary events; 10.6% of patients birth only). The two representations are complementary (18.6% together), and the ECG adds 11.9% on top of CLMBR-T in 7/7 trials. When CLMBR-T also reads the index admission's pre-t0 lab and order stream (the first-run input), its gain rises to 23.1%. That stream overlaps in time with the held-out lab values, so this larger number is reported as a sensitivity analysis only (§8). As at Yale, CLMBR-T stays a comparison arm, not a take-home claim.

## 1. Results (primary: 7 cardiovascular trials, PS-CVD5 analog, all analysed patients; CLMBR-T input = history before the index admission)

Rel. red. = relative reduction in the across-trial mean |SMD|. Items: 26, or 22 when a CLMBR-T arm is in either cell (utilisation masked). P: exact sign-flip across trials (one-sided unless marked two-sided). Yale s31: 54 items, 31 trials (`docs/s31/S31_RESULTS.md`; `audits/claude-s31-20261014/summary_v1/contrasts.csv`).

| Contrast | MIMIC rel. red. (95% CI) | Trials lower; P | % \|SMD\| < 0.1 | Mean \|Δ log HR\| (closer) | Yale s31 rel. red. (95% CI) | Yale trials lower; P |
|---|---|---|---|---|---|---|
| + ECG vs PS-CVD5 | 6.6% (2.4 to 13.1) | 6/7; .016 | 45.6 → 51.6 | 0.344 → 0.326 (4/7) | 8.7% (4.2 to 13.5) | 20/31; <.001 |
| + CLMBR-T vs PS-CVD5 | 7.7% (3.0 to 14.0) | 6/7; .023 | 44.2 → 51.3 | 0.344 → 0.278 (4/7) | 12.9% (7.6 to 18.3) | 23/31; <.001 |
| + ECG + CLMBR-T vs PS-CVD5 | 18.6% (12.5 to 26.7) | 7/7; .008 | 44.2 → 51.9 | 0.344 → 0.240 (6/7) | 14.6% (7.7 to 21.1) | 23/31; <.001 |
| **+ ECG + CLMBR-T vs + CLMBR-T** | **11.9% (6.9 to 16.8)** | **7/7; .008** | 51.3 → 51.9 | 0.278 → 0.240 (3/7) | 2.0% (−3.5 to 6.9) | 18/31; .238 |
| + ECG + CLMBR-T vs + ECG | 12.4% (8.8 to 16.2) | 7/7; .008 | 51.9 → 51.9 | 0.326 → 0.240 (5/7) | 6.6% (−0.0 to 12.6) | 18/31; .028 |
| + CLMBR-T vs + ECG (two-sided) | 0.6% (−2.4 to 3.3) | 3/7; .734 | 51.9 → 51.3 | 0.326 → 0.278 (4/7) | 4.7% (−1.2 to 9.6) | 23/31; .126 |
| + ECG vs + permuted ECG | 9.4% (6.2 to 14.0) | 7/7; .008 | 46.7 → 51.6 | 0.323 → 0.326 (4/7) | 8.3% (4.0 to 12.7) | 24/31; <.001 |
| + CLMBR-T vs + permuted CLMBR-T | 8.9% (5.6 to 11.9) | 6/7; .016 | 42.2 → 51.3 | 0.314 → 0.278 (5/7) | 11.0% (4.6 to 16.7) | 26/31; <.001 |
| + permuted ECG vs PS-CVD5 (two-sided) | −3.1% (−5.6 to −0.3) | 2/7; .094 | 45.6 → 46.7 | 0.344 → 0.323 (4/7) | 0.4% (−3.5 to 4.3) | 14/31; .834 |
| + permuted CLMBR-T vs PS-CVD5 (two-sided) | −1.3% (−5.5 to 3.9) | 2/7; .609 | 44.2 → 42.2 | 0.344 → 0.314 (4/7) | 2.2% (−2.5 to 6.7) | 17/31; .394 |

The % |SMD| < 0.1 of the base differs between rows (45.6 vs 44.2) only because CLMBR-T contrasts use the 22 unmasked items.

**RCT agreement by arm** (7 trials):

| Arm | r | Estimate agreement | Std-diff agreement | Mean \|Δ log HR\| | Benchmark-permutation P vs PS-CVD5 |
|---|---|---|---|---|---|
| PS-CVD5 | 0.69 | 0/7 | 4/7 | 0.344 | |
| + ECG | 0.69 | 1/7 | 4/7 | 0.326 | .84 |
| + CLMBR-T | 0.65 | 1/7 | 5/7 | 0.278 | .95 |
| + ECG + CLMBR-T | 0.65 | 3/7 | 6/7 | 0.240 | .57 |
| + permuted ECG | 0.70 | 1/7 | 4/7 | 0.323 | |
| + permuted CLMBR-T | 0.63 | 1/7 | 4/7 | 0.314 | |

**PEPTIC** (negative control; RCT RR 1.05; balance on 26 items, 22 for the CLMBR-T arms):

| Arm | HR (95% CI) | % \|SMD\| < 0.1 | Mean \|SMD\| |
|---|---|---|---|
| PS-CVD5 | 1.51 (1.35–1.69) | 30.8 | 0.179 |
| + ECG | 1.39 (1.24–1.55) | 42.3 | 0.155 |
| + CLMBR-T | 1.28 (1.14–1.43) | 40.9 | 0.158 |
| + ECG + CLMBR-T | 1.21 (1.08–1.35) | 31.8 | 0.149 |
| + permuted ECG | 1.60 (1.42–1.81) | 30.8 | 0.180 |
| + permuted CLMBR-T | 1.61 (1.43–1.81) | 22.7 | 0.191 |

Generated tables (every base, population and set; aggregates only): `audits/claude-mimic-clmbr-20261014/summary_prior/tables.md` and `summary.json` (primary). The first-run input (index-admission pre-t0 stream included; sensitivity) is in `summary/`.

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
| `prescriptions` (raw 3.1; the staged copy has no `ndc`) | NDC → RxNorm / RxNorm Extension through "Maps to" (OHDSI vocabulary with NDC 20240825, read in place: `/mnt/raid0/bb2238/agents/ohdsi/omop_vocabularies`; the project vocabulary has no NDC) | **primary:** order start before the index admission time; sensitivity: order start < t0, any admission |
| `labevents` | LOINC from a curated itemid → LOINC map (96 items), otherwise `MIMIC_LAB/<itemid>` | **primary:** chart time before the index admission time (earlier admissions or outpatient draws); sensitivity: chart time < t0 |
| `admissions` / `transfers` | `Visit/IP` (admission), `Visit/ER` (ED stay) | **primary:** before the index admission time; sensitivity: admit / ED in-time < t0 |
| `patients` | `MEDS_BIRTH` at 1 July of (anchor_year − anchor_age) | static |

**Rules and deviations from Yale, each forced by MIMIC:**
1. **No leakage past time zero.** Only events strictly before t0 enter. MIMIC diagnosis and procedure codes carry no reliable timestamp, so they are placed at their admission's discharge time and **every code of the index admission is excluded** (the PS-CVD5 analog uses earlier admissions only, too). **Primary input (2026-10-15): every event at or after the index admission time is removed** (`build_meds_prior_only.py`), so no lab, order or visit of the index admission enters. In the sensitivity input, labs and medication orders from the index admission count if timestamped before t0. **Checks (aggregate, over all 43.8 million events):** 0 events at or after t0; 0 index-admission diagnosis or procedure codes; 0 events before birth.
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
| **Primary input (history before the index admission):** birth only | 10.6% | < 11 patients |
| **Primary input:** in-vocabulary events per patient, median | 59 | 308 |

- **By domain (all 78,183 MEDS subjects):** diagnoses 88.1% in the dictionary, drug orders 60.5%, labs 83.4%, procedures 34.8%, visits 100%. Labs are 86% of all events.
- **Stop rule** (< 50% in the dictionary, or > 50% of patients with no prior coded history): **not fired**. Under the literal lab rule (no LOINC), about 9% of events would be in the dictionary and the rule would fire.
- The builder's in-vocabulary counts equal the tokenizer's accepted counts for every subject (78,183/78,183; verification report).
- The coverage gate was run on the first-run input. The primary input (history before the index admission) is thinner, as the last two rows show; it would also pass the stop rule (10.6% < 50% with no prior history).

### 5.4 CLMBR-T inference (Step 2; `encode_mimic_clmbr.py`)

- Same checkpoint (`/mnt/raid0/eo287/clmbr`), femr 0.2.3 / meds 0.1.3, FEMR tokenizer and batch processor, torch seed 20260923, latest retained token representation (768-d), raw vectors. The model files and runtime versions **equal the Yale `manifest.json`** (sha256 of `config.json`, `dictionary.msgpack`, `model.safetensors`; femr, meds, torch, transformers, xformers, numpy, pyarrow).
- Two differences, both forced by MIMIC: (1) the cutoff is the exact t0 timestamp, not index-date midnight; (2) a subject with no tokenizer-supported clinical event is encoded from its birth event alone (a demographics-only embedding) and kept, not skipped.
- **CLMBR-T PCs:** 64 within each trial (`eval_longtail_balance.pcs` on the trial's analysed patients, as `v13_common.clm_pc`). Placebo: the PCs permuted between patients with the same within-trial permutation as the permuted ECG (seed 20261001).
- **Reproducibility:** BLAS runs single-threaded (`mimic_common` sets `OMP/OPENBLAS/MKL_NUM_THREADS=1`). Birth-only subjects with the same birth year share an embedding, so PS ties are broken by floating-point order. With multi-threaded BLAS the prior-only CLMBR-T cells move slightly (about 1e-3 in mean |SMD|).
- A 100-subject smoke test ran first. The first-run (sensitivity) inference ran on GPU 6 (shared; GPU 3 was taken by another job when the run started), the primary (history before the index admission) on GPU 3. GPU 7 is never used.

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

Relative reduction in mean |SMD| (95% CI; trials lower). CLMBR-T input = history before the index admission in every row except the last. The design-detail rows are the existing v21 sensitivities, now with the CLMBR-T arms.

| Variant | + ECG vs PS-CVD5 | + CLMBR-T vs PS-CVD5 | + ECG + CLMBR-T vs PS-CVD5 | + ECG + CLMBR-T vs + CLMBR-T |
|---|---|---|---|---|
| **Primary** | 6.6% (2.4 to 13.1); 6/7 | 7.7% (3.0 to 14.0); 6/7 | 18.6% (12.5 to 26.7); 7/7 | 11.9% (6.9 to 16.8); 7/7 |
| Any diabetes instead of T2D (`cvd5_anydm`) | 11.8% (7.4 to 16.9); 7/7 | 11.0% (6.2 to 16.1); 7/7 | 16.6% (11.6 to 22.8); 7/7 | 6.3% (1.0 to 11.7); 6/7 |
| Index-admission codes in the base (`cvd5_incl`) | 11.5% (7.0 to 17.7); 7/7 | 11.4% (7.0 to 15.3); 7/7 | 18.6% (13.7 to 23.0); 7/7 | 8.0% (5.5 to 11.2); 7/7 |
| No index-day ECG | 6.5% (−0.4 to 13.6); 5/7 | 0.1% (−11.7 to 12.0); 4/7 | 11.6% (3.9 to 21.1); 6/7 | 11.5% (4.5 to 17.1); 5/7 |
| All 8 trials (with PEPTIC) | 7.6% (3.2 to 13.1); 7/8 | 9.5% (4.0 to 15.2); 7/8 | 19.4% (13.6 to 26.0); 8/8 | 11.0% (7.0 to 15.6); 8/8 |
| Utilisation not masked (26 items) | 6.6% (2.4 to 13.1); 6/7 | 8.9% (4.1 to 14.9); 6/7 | 19.6% (13.2 to 27.1); 7/7 | 11.7% (6.8 to 16.7); 7/7 |
| **CLMBR-T input includes the index admission's pre-t0 labs and orders** (first-run input; `meds`) | 6.6% (2.4 to 13.1); 6/7 | 23.1% (16.0 to 28.9); 7/7 | 29.0% (21.6 to 37.1); 7/7 | 7.7% (3.0 to 14.1); 6/7 |

- **The ECG's added value on top of CLMBR-T holds in every variant of the primary input** (6.3–11.9%; 5/7 to 8/8 trials lower) and in the first-run primary configuration (7.7%). It does **not** hold with the first-run input and the any-diabetes base (0.6%, −5.9 to 8.9; 3/7).
- **CLMBR-T alone is less stable:** 7.7–11.4% in most variants, but 0.1% (−11.7 to 12.0) in the population without index-day ECGs.
- The ECG rows equal the v21 point estimates exactly (`summary.json` gates). The CIs differ from the v21 table only by the bootstrap convention (§7). As in v21, the ECG estimate moves by about ±5 points between near-identical bases.
- Excluding overlap-invalid cells changes nothing (no cell fails the rule).

**Why the CLMBR-T input changed** (decision 2026-10-15, after both results were seen).
- **The first-run input** followed the queue rule: labs and orders of the index admission count if timestamped before t0. That pre-t0 stream is close in time to the held-out lab values (latest value before t0, mostly from the same admission). The model does not see values, but ordering intensity is a soft proxy for them, and such proxies are not masked under the `pipeline.md` §6 rules.
- **With that stream, CLMBR-T gave 23.1%**, about twice Yale's 12.9%. About two-thirds of it came from the index admission's own pre-t0 stream rather than prior history.
- **The primary input** (`build_meds_prior_only.py`, `run_mimic_external.py prior`) removes every event at or after the index admission time; 0 remaining events were checked. **It keeps the index ED stay before admission** (audit: 8.7% of events, in 72% of patients; the whole clinical input for 32.3%; 21.6% of held-out lab values measured in that window; index-episode events a median of 24 h before t0). In 2.8% of subjects t0 falls before the admission time, so for them the input equals the first-run input.
- **Comparison with Yale.** At Yale the held-out labs are the latest values in [index − 365 d, index − 1 d], all inside the CLMBR-T input window, so the order codes of essentially every held-out lab are visible to CLMBR-T. The primary MIMIC input is **stricter** than Yale on this structural overlap (about 31.5% of held-out values have visible order codes: 21.6% from the index ED stay, 9.9% earlier). What set the first-run input apart from Yale was closeness in time (hours, within the same acute episode), not the structure. Under the `pipeline.md` §6 rules nothing needs masking in either cohort.
- **The primary input is thinner:** 83.4% of its events are in the dictionary, 10.6% of patients are left with birth only, the median is 59 in-vocabulary events, and 42.3% of patients have no input from before the index episode (birth only, or the index ED stay only). It uses the same checkpoint and hashes and the same analysis code (v21 cells reproduced, max |Δ| 0; 0 failed or overlap-invalid cells).
- **With the first-run input:**
  - mean |Δ log HR| 0.344 → 0.260 (+ CLMBR-T) → 0.249 (+ both), with benchmark-permutation P .70 and .43;
  - PEPTIC: + CLMBR-T HR 1.00 (0.90–1.11), + both 0.95 (0.85–1.06), permuted CLMBR-T 1.43 (1.28–1.61);
  - median in-sample C: + CLMBR-T 0.793, + both 0.807.

## 9. Limitations

- **Hospital-only history.** MIMIC records only BIDMC hospital episodes (and outpatient labs drawn there): no outpatient diagnoses or prescriptions. The CLMBR-T input is therefore thinner and differently composed than Yale's: 86% of its events are labs (in the first-run input, 30.2% of the analysed patients' lab events came from the index admission before t0). With the primary input (history before the index admission), 10.6% of patients have birth only and the median is 59 in-vocabulary events.
- **12-month horizon** (death after discharge is captured only to about 1 year); several trials are shortened.
- **7 trials.** The bootstrap CI over 7 trials is crude; the per-trial direction and the exact sign-flip P (minimum one-sided P 1/128) carry the inference. Near-identical design variants move the ECG estimate by about ±5 points (§8).
- **Mapping choices made for MIMIC:** a curated lab LOINC map; NDC → RxNorm from a second OHDSI vocabulary; year-only birth; no vitals; prescriptions orders only (no administrations); about 14% of pre-t0 prescription rows have no NDC and are dropped.
- **Timing of the CLMBR-T input.** The primary input is history before the index admission only, chosen on 2026-10-15 after both inputs had been analysed (§8). The first-run input, which also read the index admission's pre-t0 labs and orders, gave a much larger CLMBR-T gain (23.1%), driven by a stream that overlaps in time with the held-out lab values. The primary input is a conservative external test of CLMBR-T: MIMIC's prior record is hospital-only and thin. It still keeps the index ED stay before admission (21.6% of held-out lab values were measured there; order codes visible, values not); a stricter input that also drops the ED stay would leave 42.3% of patients without input from before the index episode.
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
