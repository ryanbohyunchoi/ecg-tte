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
   - **Result:** PS-CVD5 gives HR 1.51 (1.35–1.69). Adding the ECG moves it to 1.39 (1.24–1.56), and balance improves (30.8% → 42.3% of characteristics balanced).
   - **Placebo:** the permuted ECG gives 1.60.
   - **Comparison with v20:** this is the same pattern as with the demographic PS.
7. **Side finding: an inconsistency in v20, not caused by this analysis.**
   - **What differs:** in the v20 new trials (SOAP II, ELITE II and PEPTIC), the `dx` covariates and the hdPS panel `dx_` codes include **index-admission** discharge diagnoses (`mimic_build_new.py`: `admittime <= index admittime`). The 5 v1.5 trials were audit-fixed to **earlier admissions only** (`v15_mimic_auditfix.py`, AUDIT_V15 M2). The flag rebuild here reproduces each convention exactly (0 discordant patients).
   - **What it affects:** the v20 `sparse`, `hdPS200` and `clinical` results for those 3 trials. The primary v20 demographic analysis is unaffected.
   - **What it does not affect:** PS-CVD5 here uses earlier admissions for all 8 trials.
   - **Action:** flag this to the user before the v20 ladder results for those trials are reused.

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
