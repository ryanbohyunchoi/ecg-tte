# paper2 step D: PS-CVD5 analog in the MIMIC-IV replication (2026-10-07)

This implements `HANDOFF_PAPER2.md` §3.6: a supplementary analysis, ECG only, with no CLMBR-T in MIMIC.
- **Code:** `scripts/v21/mimic_cvd5.py`. It imports `scripts/v20/mimic_replication.py` and `mimic_summary.py` and does not modify them.
- **Outputs:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/mimic/` (umask 077):
  - `gate/` holds the gate result;
  - `flags/flag_check.csv` holds aggregate checks;
  - the generated tables are in `summary/tables.md` and `summary/summary.json`;
  - the restricted per-trial files are `flags/*.parquet` and `results/*.csv`.
- **Data handling:** MIMIC was read in place from the v1.5 staged tables. Aggregates only; no count of 1–10 is reported, no patient rows were printed and no note text was opened.
- **Runtime:** about 10 s for the analysis (8 workers). It was run in tmux window `paper2:mimic`, with the log in `audits/claude-v21-paper2/logs/mimic.log`.

## Verdict

1. **The existing `sparse` base is not PS-CVD5.**
   - `sparse` is demographics plus 9–13 diagnosis flags per trial: CKD, stroke, COPD/asthma, PAD, valve disease and trial extras on top of the cardiovascular ones.
   - In the AF and HF trials it lacks AF or HF, because that is the gate condition.
   - In PLATO it lacks CAD.
   - Its `diabetes` is any diabetes, not T2D.

   So a new base was built: **PS-CVD5** = v1.5 demographics (age, sex, estimated index year) plus HTN, T2D, CAD/IHD, AF and HF, coded in **earlier admissions only**.
2. **Gate: PASS.** All `demo` and `sparse` cells (8 trials × 3 arms × 2 populations, arms and per-variable tables) reproduce the v20 results **exactly**, with max |Δ| = 0. The published v20 summary numbers (% balanced, relative reduction and bootstrap CI) also reproduce with max |Δ| = 0.
3. **Balance: adding the ECG to PS-CVD5 improves held-out balance in MIMIC, by a similar amount to Yale.**
   - **Result (7 cardiovascular trials):**
     - mean |SMD| fell by **6.6% (95% CI 2.3–12.8)**, lower in 6/7 trials (exact sign-flip p = 0.016);
     - % |SMD| < 0.1 went from 45.6 to 51.6, i.e. +6.0 points, but only 3/7 trials improved (p = 0.125).
   - **Placebo:** the permuted ECG gave −3.1% and +1.1 points.
   - **Comparison with Yale:** the Yale PS-CVD5 result is 9.0% (4.8–13.3) in 32 trials.
   - **Comparison with the v20 MIMIC demographic PS:** that gain was 10.3%, so it is smaller here, as expected for a richer base.
4. **The size of the gain depends on design details.**
   - **Same five flags, two small changes:**
     - with any diabetes in place of T2D, which shifts prevalence by at most 0.8 points, the gain is 11.8% (7.2–16.7; 7/7);
     - with index-admission codes included, it is 11.5% (7.1–17.4; 7/7).
   - **Excluding index-day ECGs**, the primary analysis gives 6.5% (−0.2 to 13.6; 5/7; p = 0.094).
   - **Reading:** the direction is stable, but with 7 trials and greedy 1:1 matching, the point estimate moves by about ±5 percentage points between near-identical specifications. The trial-bootstrap CI does not capture this.
5. **RCT agreement: no ECG-specific improvement (same as v20 and Yale).**
   - **ECG vs PS-CVD5 alone:** mean |Δ log HR| went from 0.344 to 0.326 (4/7 closer; p = 0.27).
   - **Placebo:** the permuted ECG gave 0.323, as close as the real ECG.
6. **Negative-control trial (PEPTIC; RCT RR 1.05).**
   - **Result:** PS-CVD5 gives HR 1.51 (1.35–1.69). Adding the ECG moves it to 1.39 (1.24–1.55), and balance improves (30.8% → 42.3% of characteristics balanced).
   - **Placebo:** the permuted ECG gives 1.60.
   - **Comparison with v20:** this is the same pattern as with the demographic PS.
7. **Side finding: an inconsistency in v20, not caused by this analysis.**
   - **What differs:** in the v20 new trials (SOAP II, ELITE II and PEPTIC), the `dx` covariates and the hdPS panel `dx_` codes include **index-admission** discharge diagnoses (`mimic_build_new.py`: `admittime <= index admittime`). The 5 v1.5 trials were audit-fixed to **earlier admissions only** (`v15_mimic_auditfix.py`, AUDIT_V15 M2). The flag rebuild here reproduces each convention exactly (0 discordant patients).
   - **What it affects:** the v20 `sparse`, `hdPS200` and `clinical` results for those 3 trials. The primary v20 demographic analysis is unaffected.
   - **What it does not affect:** PS-CVD5 here uses earlier admissions for all 8 trials.
   - **Action taken:** a window-fixed sensitivity re-run is in §6. Paper1's MIMIC numbers do not change materially.

## 1. Definitions

**PS-CVD5 (primary):** v1.5 `demo` (with missingness indicators, as in v20) plus five flags.

| Flag | ICD-10 prefixes | ICD-9 prefixes | Source |
|---|---|---|---|
| Hypertension | I10–I13, I15 | 401–405 | v1.5 `CONCEPTS` |
| Type 2 diabetes | E11 | 250.x0, 250.x2 | new (Yale P5 `t2d` = E11) |
| CAD/IHD | I20–I25 | 410–414 | v1.5 `CONCEPTS` |
| Atrial fibrillation | I48 | 427.31 | v1.5 `CONCEPTS` |
| Heart failure | I50 | 428 | v1.5 `CONCEPTS` |

- **Window:** any diagnosis code in an admission that started before the index admission, with the index admission itself excluded. This is the v1.5 audit-fixed, leakage-safe convention, closest to Yale's pre-index codes.
- **Check:** for the 5 v1.5 trials it reproduces the existing baseline flags exactly (0 discordant).
- **Gate condition:** under this window it is a prior-history flag, not a constant. For example, prior AF is 15–16% in the AF trials.
- **Constant flags** are dropped from the PS automatically. Only `cvd5_incl` loses any, one per trial where the gate condition is coded in the index admission (4 flags remain):
  - CAD in PLATO;
  - AF in ARISTOTLE and ROCKET AF;
  - HF in TRANSFORM-HF, COMET and ELITE II.

  PS-CVD5 and `cvd5_anydm` keep all 5 in every trial.

| Base | Difference from PS-CVD5 |
|---|---|
| `cvd5_anydm` (sensitivity) | any diabetes (v1.5 `diabetes`, E08–E13 / 250) instead of T2D |
| `cvd5_incl` (sensitivity) | index-admission codes included (the v20 new-trial window) |

**Unchanged from v20:**
- arms: base, +ECG (32 PCs) and +permuted ECG (seed 20261001);
- PS: L2 logistic; matching 1:1 greedy with caliper 0.2;
- outcome model: Cox with robust SE clustered on pairs;
- held-out panel of **26 items** (A core labs and vitals 8, B additional labs 13, C ventilation at t0 1, D utilisation 4);
- populations: all, and excluding index-day ECGs;
- relative reduction in mean |SMD| with a 2,000-resample trial bootstrap (seed 0), via `mimic_summary.boot_rr`; exact one-sided sign-flip test; agreement metrics via `mimic_summary.agreement`.

**Prevalence of the flags** (earlier admissions, %; range over the 8 trials):
- HTN 10–37;
- T2D 5–19;
- CAD 5–19;
- AF 3–16;
- HF 4–18.

With index-admission codes included, the corresponding ranges are 62–84, 26–42, 37–100, 20–100 and 22–100.

## 2. Gate

| Check | Result |
|---|---|
| `demo` and `sparse` arms tables, 8 trials (12 rows each) vs v20 `results/<k>_arms.csv` | same rows; max \|Δ\| 0.0; NaN pattern and text equal |
| `demo` and `sparse` per-variable tables (312 rows each) vs v20 `_vars.csv` | same rows; max \|Δ\| 0.0 |
| v20 `summary.json` balance metrics (demo and sparse; all sets and populations) recomputed | max \|Δ\| 0.0 |
| **Gate** | **PASS** |

## 3. Balance (26-item held-out panel; mean over trials)

| Set | Base PS | Population | % \|SMD\|<0.1: base → +ECG | Δ pts (better; p) | Rel. reduction in mean \|SMD\| [95% CI] (lower; p) | Permuted ECG: Δ pts / rel. red. |
|---|---|---|---|---|---|---|
| (v20) primary 7 | demographic | all | 41.2 → 51.6 | +10.4 (7/7; 0.008) | 10.3 [6.4, 14.5] (7/7; 0.008) | +0.5 / −2.5 |
| **primary 7** | **PS-CVD5** | **all** | **45.6 → 51.6** | **+6.0 (3/7; 0.125)** | **6.6 [2.3, 12.8] (6/7; 0.016)** | +1.1 / −3.1 |
| primary 7 | PS-CVD5 | no index-day ECG | 47.3 → 51.1 | +3.8 (4/7; 0.062) | 6.5 [−0.2, 13.6] (5/7; 0.094) | −3.8 / −6.1 |
| primary 7 | CVD5, any DM | all | 44.5 → 52.2 | +7.7 (5/7; 0.031) | 11.8 [7.2, 16.7] (7/7; 0.008) | +3.3 / −0.6 |
| primary 7 | CVD5, any DM | no index-day ECG | 44.5 → 48.9 | +4.4 (4/7; 0.19) | 10.5 [4.9, 15.9] (6/7; 0.016) | −1.6 / −5.6 |
| primary 7 | CVD5, incl. index adm. | all | 42.9 → 50.0 | +7.1 (5/7; 0.031) | 11.5 [7.1, 17.4] (7/7; 0.008) | +2.2 / +2.0 |
| primary 7 | CVD5, incl. index adm. | no index-day ECG | 42.3 → 48.9 | +6.6 (5/7; 0.047) | 8.7 [2.2, 15.1] (6/7; 0.023) | 0.0 / +1.0 |
| all 8 | PS-CVD5 | all | 43.8 → 50.5 | +6.7 (4/8; 0.062) | 7.6 [3.3, 12.8] (7/8; 0.008) | +1.0 / −2.7 |
| all 8 | PS-CVD5 | no index-day ECG | 46.6 → 51.4 | +4.8 (5/8; 0.031) | 7.5 [0.8, 13.8] (6/8; 0.047) | −4.3 / −6.1 |

**By block** (PS-CVD5, primary 7, all patients; relative reduction with the ECG):
- core labs and vitals 4.3%;
- additional labs 9.2%;
- utilisation 4.0%.

With any diabetes, the same blocks give 12.0%, 13.1% and 7.5%.

**Cross-base contrasts** (primary 7, all patients):

| Contrast | % balanced | Rel. reduction in mean \|SMD\| [95% CI] (lower; p) | Mean \|Δ log HR\| |
|---|---|---|---|
| PS-CVD5 vs demographic PS | 41.2 → 45.6 | 6.3 [1.9, 11.8] (6/7; 0.023) | 0.337 → 0.344 |
| PS-CVD5 vs v20 `sparse` | 47.3 → 45.6 | −3.4 [−9.2, 1.9] (3/7) | — |
| **PS-CVD5 + ECG vs v20 `sparse`** | 47.3 → 51.6 | 3.4 [0.1, 6.8] (5/7; 0.055) | 0.303 → 0.326 |
| PS-CVD5 + ECG vs demographic PS + ECG | 51.6 → 51.6 | 2.5 [−0.4, 5.8] (4/7; 0.11) | 0.315 → 0.326 |

Once the ECG is in the PS, the five diagnoses add little.

### Per trial (PS-CVD5, all patients)

| Trial | % balanced: base → +ECG | Mean \|SMD\|: base → +ECG (rel. red. %) | HR base | HR +ECG (95% CI) | HR permuted | RCT | Pairs (base / +ECG) |
|---|---|---|---|---|---|---|---|
| PLATO | 42.3 → 38.5 | 0.163 → 0.166 (−2.0) | 0.76 | 0.77 (0.55–1.07) | 0.75 | 0.84 | 441 / 431 |
| ARISTOTLE | 38.5 → 38.5 | 0.197 → 0.188 (4.6) | 0.45 | 0.43 (0.23–0.84) | 0.49 | 0.79 | 1,490 / 1,488 |
| ROCKET AF | 38.5 → 38.5 | 0.214 → 0.205 (4.0) | 0.50 | 0.49 (0.24–1.01) | 0.48 | 0.88 | 904 / 902 |
| TRANSFORM-HF | 46.2 → 69.2 | 0.138 → 0.131 (4.8) | 1.32 | 1.30 (1.08–1.57) | 1.30 | 1.02 | 939 / 940 |
| COMET | 46.2 → 46.2 | 0.135 → 0.129 (4.4) | 1.37 | 1.16 (0.92–1.46) | 1.32 | 1.20 | 743 / 742 |
| SOAP II (OR benchmark) | 50.0 → 65.4 | 0.141 → 0.128 (9.4) | 0.80 | 0.76 (0.65–0.88) | 0.77 | 1.17 | 926 / 926 |
| ELITE II | 57.7 → 65.4 | 0.129 → 0.096 (26.0) | 0.74 | 0.85 (0.72–0.99) | 0.84 | 1.13 | 1,841 / 1,838 |
| PEPTIC (negative control; RR benchmark) | 30.8 → 42.3 | 0.179 → 0.155 (13.5) | 1.51 | 1.39 (1.24–1.55) | 1.60 | 1.05 | 2,137 / 2,133 |

Every event count is ≥ 18 per analysed cell, so nothing needed suppression.

## 4. RCT agreement (trial primary outcome; primary 7, all patients)

| Base PS | Arm | r | Estimate agreement | Std-diff agreement | Mean \|Δ log HR\| | ECG closer (p) |
|---|---|---|---|---|---|---|
| (v20) demographic | PS alone / + ECG | 0.71 / 0.67 | 0/7 / 1/7 | 5/7 / 4/7 | 0.337 / 0.315 | 4/7 (0.27) |
| **PS-CVD5** | PS alone | 0.69 | 0/7 | 4/7 | 0.344 | |
| **PS-CVD5** | + ECG | 0.69 | 1/7 | 4/7 | 0.326 | **4/7 (0.27)** |
| **PS-CVD5** | + permuted ECG | 0.70 | 1/7 | 4/7 | 0.323 | |
| PS-CVD5, no index-day ECG | PS alone / + ECG / + permuted | 0.34 / 0.38 / 0.31 | 2/7 / 0/7 / 1/7 | 6/7 / 6/7 / 5/7 | 0.291 / 0.235 / 0.205 | 4/7 (0.20) |
| CVD5, any DM | PS alone / + ECG / + permuted | 0.70 / 0.68 / 0.65 | 1/7 / 1/7 / 2/7 | 4/7 / 5/7 / 4/7 | 0.340 / 0.286 / 0.296 | 3/7 (0.36) |
| CVD5, incl. index adm. | PS alone / + ECG / + permuted | 0.45 / 0.70 / 0.75 | 1/7 / 2/7 / 2/7 | 4/7 / 5/7 / 5/7 | 0.292 / 0.233 / 0.246 | 4/7 (0.13) |

In every variant the permuted ECG moves |Δ log HR| about as much as the real ECG does. Any agreement change is therefore generic attenuation, not ECG-specific. This matches the Yale benchmark-permutation result.

## 5. Deviations and notes

1. **New base, not `sparse`.** `sparse` is not CVD5 (see Verdict 1), so PS-CVD5 was built from the staged `diagnoses_icd` table, read in place.
   - T2D (ICD-10 E11; ICD-9 250 with fifth digit 0 or 2) is a new concept, matching Yale `t2d`.
   - The other four flags use the v1.5 concept prefixes unchanged.
2. **Window.** Earlier admissions only, for all 8 trials. For SOAP II, ELITE II and PEPTIC this differs from their v20 `dx` covariates, which include the index admission (Verdict 7). `cvd5_incl` reproduces that convention as a sensitivity analysis.
3. **No race variable.** As in v20, MIMIC PS-CVD5 uses v1.5 `demo` (age, sex, estimated index year). The index year is estimated from the de-identified anchor year group.
4. **Gate condition in the PS.** AF in the AF trials and HF in the HF trials enter as *prior-admission* history flags. They are not constant under the earlier-admission window.
5. **Bootstrap.** 2,000 resamples, seed 0 (the v20 `mimic_summary.boot_rr` convention), not the 4,000 used for the Yale paper2 grid. This keeps the gate on the v20 summary numbers exact. With 7–8 trials the CI is crude; the per-trial direction and the exact sign-flip p carry the inference.
6. **Echocardiography is not in the held-out panel** (as in v20: its provenance is unverified). The Yale primary 54-item non-coded panel has no MIMIC equivalent; the 26-item panel is used.
7. **Multiplicity.** No FDR is applied here. This is a supplementary, single-family analysis, and the p values are nominal.
8. **Scope.** Nothing in `paper.md`, `table1_picot.md` or the .docx was edited. Nothing was committed or pushed.

## 6. Window-fix sensitivity for paper1's MIMIC numbers (reviewer item S5; added 2026-10-07)

**Verdict: paper1's MIMIC numbers do not change materially.**
- **Unchanged:** every PS-Demo number in `paper.md` line 91 is unaffected, because the demographic PS uses no diagnoses. That covers 10.3% (6.4–14.5), 7/7, P = .008, 41.2% → 51.6%, permuted −2.5%, the index-day exclusion 14.5% (9.5–19.8) and the 441–1,841 pairs.
- **Changed:** the hdPS and PS-Clinical-lite gains move slightly upward. Both CIs still include 0, so the reading "smaller with the hdPS and PS-Clinical-lite" holds.
- **Gate:** the 5 unchanged v1.5 trials reproduce v20 exactly in all four bases. The new trials' PS-Demo cells also reproduce exactly.

**What was done.** `scripts/v21/mimic_window_fix.py` imports the v20 and v1.5 modules without modifying them. Outputs are in `audits/claude-v21-paper2/mimic/windowfix/`.
- **Rebuilt for SOAP II, ELITE II and PEPTIC**, with the v1.5 audit-fix rules (`v15_mimic_auditfix.py`):
  - the baseline `dx` flags, from earlier admissions only;
  - the hdPS panel `dx_` codes, from earlier admissions with admittime in [t0 − 365 d, index admittime);
  - the panel `px_` codes, with chartdate in [t0 − 365 d, index day) and the index admission excluded;
  - ≥1% prevalence; `rx_` and `lab_` columns unchanged; no baseline column became constant.
- **Re-run:** sparse, hdPS200 and clinical-lite ± ECG ± permuted ECG, in both populations.
- **Recomputed:** the paper's CIs with `sens_primary32.relred_ci` (4,000 resamples, seed 20261001, the `paper.md` convention), and the v20 summary metrics with `mimic_summary`.
  - Before any fix, both reproduce the v20 inputs exactly. For example, hdPS 7.5 (−0.4 to 16.2) and clinical-lite 1.2 (−9.1 to 11.8), as cited.
- **Also:** `mimic_cvd5.py` was refactored, moving the analysis loop into `run_trial`. Its outputs are byte-identical (md5) to the first run.

**Effect of the fix on the new trials' covariates** (prevalence, v20 → fixed):
- HTN: SOAP II 70 → 37%, ELITE II 84 → 20%, PEPTIC 62 → 10%;
- panel `dx_` codes: 419 → 207, 278 → 63 and 326 → 22;
- panel `px_` codes: 37 → 24, 35 → 3 and 12 → 2.

### `paper.md` line 91: exact replacement numbers (7 cardiovascular trials; 4,000-resample CI)

| Quantity in line 91 | v20 (as published) | Window-fixed |
|---|---|---|
| PS-Demo + ECG, relative reduction in mean \|SMD\| | 10.3% (6.4%–14.5%), 7/7, P = .008 | **unchanged** |
| % balanced, PS-Demo → + ECG | 41.2% → 51.6% | **unchanged** |
| Permuted ECG (PS-Demo) | −2.5% | **unchanged** |
| PS-Demo, excluding index-day ECGs | 14.5% (9.5%–19.8%) | **unchanged** |
| Matched pairs, PS-Demo | 441 to 1,841 | **unchanged** |
| **hdPS** + ECG | 7.5% (−0.4% to 16.2%) | **8.1% (−0.1% to 17.3%)** |
| **PS-Clinical-lite** + ECG | 1.2% (−9.1% to 11.8%) | **3.0% (−8.6% to 15.2%)** |

### Supplement eTable 6B, affected rows (old vs new)

eTable 6B uses the v20 2,000-resample CI, so the table gives the CI under both conventions. Part A of eTable 6 is PS-Demo only, so it is unchanged.

| PS | Population | Version | Rel. red. % (4,000-resample CI) | (v20 2,000-resample CI) | Trials lower | Permuted % | % bal base → +ECG | Mean \|Δ log HR\| base → +ECG | Closer | P | + permuted | r | Std-diff agreement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PS-Sparse | All | v20 | 10.2 (7.6 to 14.6) | (7.6 to 14.4) | 7/7 | −3.6 | 47.3 → 50.0 | 0.303 → 0.209 | 4/7 | .27 | 0.255 | 0.75 → 0.64 | 6/7 → 5/7 |
| PS-Sparse | All | **fixed** | **10.9 (8.3 to 14.1)** | (8.3 to 13.9) | 7/7 | −2.3 | 46.2 → 48.9 | 0.322 → 0.200 | 5/7 | .12 | 0.280 | 0.71 → 0.67 | 5/7 → 5/7 |
| PS-Sparse | No index-day ECG | v20 | 9.6 (2.7 to 15.2) | (3.2 to 15.0) | 6/7 | −4.3 | 46.7 → 53.8 | 0.229 → 0.208 | 2/7 | .42 | 0.258 | 0.65 → 0.41 | 6/7 → 6/7 |
| PS-Sparse | No index-day ECG | **fixed** | **9.3 (2.6 to 14.5)** | (3.6 to 14.6) | 6/7 | −7.2 | 47.8 → 51.6 | 0.278 → 0.245 | 2/7 | .33 | 0.268 | 0.52 → 0.27 | 6/7 → 6/7 |
| hdPS | All | v20 | 7.5 (−0.4 to 16.2) | (−0.5 to 15.9) | 4/7 | −0.3 | 65.9 → 68.1 | 0.220 → 0.179 | 4/7 | .22 | 0.165 | 0.68 → 0.54 | 5/7 → 5/7 |
| hdPS | All | **fixed** | **8.1 (−0.1 to 17.3)** | (−0.5 to 17.3) | 4/7 | +0.4 | 65.9 → 68.1 | 0.215 → 0.179 | 5/7 | .26 | 0.173 | 0.70 → 0.53 | 6/7 → 5/7 |
| hdPS | No index-day ECG | v20 | 3.4 (−5.5 to 12.7) | (−5.9 to 12.2) | 5/7 | −1.4 | 66.5 → 63.7 | 0.272 → 0.207 | 5/7 | .16 | 0.243 | 0.15 → 0.27 | 6/7 → 7/7 |
| hdPS | No index-day ECG | **fixed** | **3.5 (−4.6 to 8.4)** | (−3.8 to 8.5) | 6/7 | +0.4 | 67.6 → 62.6 | 0.266 → 0.240 | 3/7 | .44 | 0.270 | 0.17 → 0.12 | 6/7 → 6/7 |
| PS-Clinical-lite | All | v20 | 1.2 (−9.1 to 11.8) | (−9.6 to 10.8) | 3/7 | +0.5 | 68.4 → 69.4 | 0.297 → 0.175 | 5/7 | .078 | 0.231 | 0.74 → 0.82 | 4/7 → 6/7 |
| PS-Clinical-lite | All | **fixed** | **3.0 (−8.6 to 15.2)** | (−9.1 to 14.5) | 3/7 | +1.9 | 69.4 → 71.4 | 0.284 → 0.172 | 4/7 | .11 | 0.244 | 0.77 → 0.81 | 5/7 → 6/7 |
| PS-Clinical-lite | No index-day ECG | v20 | −1.5 (−13.5 to 5.9) | (−12.7 to 6.0) | 4/7 | +1.3 | 64.3 → 66.3 | 0.159 → 0.313 | 4/7 | .85 | 0.198 | 0.63 → −0.06 | 6/7 → 7/7 |
| PS-Clinical-lite | No index-day ECG | **fixed** | **3.0 (−2.2 to 7.8)** | (−2.1 to 8.1) | 5/7 | +1.3 | 58.2 → 62.2 | 0.169 → 0.315 | 3/7 | .83 | 0.192 | 0.61 → −0.06 | 6/7 → 6/7 |

**Notes:**
- **RCT agreement is qualitatively unchanged.** The clinical-lite PS + ECG is still the closest, at 0.172, and the permuted ECG is close behind (0.244 vs v20 0.231). The P for the ECG being closer goes from .078 to .11.
- **PEPTIC (negative control, RR 1.05):**
  - The v20 `sparse` PS gave 1.16 (1.03–1.30). That was partly because index-admission (post-t0) discharge diagnoses were in the PS. With the fix it gives 1.51 (1.34–1.69), close to PS-Demo's 1.53.
  - The clinical-lite PS still recovers the null: 1.03 (0.92–1.14), and 1.01 with the ECG (v20: 0.98 and 0.96).
  - The v20 narrative is unchanged: measured physiology removes the PEPTIC confounding, and the ECG partly does.
- **eTable 6B source.** The supplement's eTable 6B 2,000-resample CIs predate the paper's 4,000-resample CIs, as the paper's change log records. If eTable 6B is updated, use the 4,000-resample column for consistency with `paper.md`.
- **Source files:** `windowfix/summary/balance.csv`, `agreement.csv` and `per_trial_new.csv` (aggregates); `windowfix/gate/gate.csv`.
