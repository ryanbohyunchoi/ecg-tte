# PS-Clinical (no LVEF) with 5-draw multiple imputation on the version 1 cohorts

Written 2026-10-13. Version 1 cohorts are the primary cohorts again (user decision 2026-10-13, `pipeline.md`). This is the version 1 counterpart of `docs/v2_psclin_mi/PS_CLINICAL_MI.md` (spec-v2 fixed cohorts).

- **Code:** `scripts/v2_psclin_mi/psclin_mi_v1.py`. It is a mode of `psclin_mi.py`, which it imports unchanged: the cell task, the gate, the masks, the summary endpoints. It re-points the output paths and adds a 5-draw imputation on the version 1 population.
- **Outputs** (umask 077, not committed): `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-psclin-mi/`. This document reports aggregates only: trial counts, means, CIs and P values.

## Plain-language summary

- **What was done.** PS-Clinical without LVEF was re-imputed with 5 independent draws. The imputation used the **same population as version 1's no-LVEF re-imputation**: the full pre-ECG baseline roster of each trial. LVEF was neither imputed nor used as a predictor. The `clinical_nolvef` rung was then run on the version 1 cohorts:
  - 6 PS methods × 38 trials × 5 draws;
  - arms PS alone, + ECG, + permuted ECG, and the CLMBR-T arms for the record;
  - 7,030 cells in total.

  The draws were combined in the usual way: per-item |SMD| averaged over draws, and log HRs by Rubin's rules.
- **Gates passed (exact).**
  - **Imputation:** draw 1 equals the version 1 re-imputed table (`claude-v1-psclin-nolvef/imputation/`) in 38/38 trials (asserted).
  - **Cells:** the draw-1 cells reproduce all 1,406 existing version 1 PS-Clinical-no-LVEF cells (6 methods × 7 arms × 38 trials). 98,420 values were compared: maximum deviation 0, 0 NaN mismatches, 0 string mismatches.
- **Headline** (paper 1's 32 trials, main configuration = 1:1 caliper 0.2, 54 leakage-corrected items, 45 held out for this rung). Adding the ECG to PS-Clinical (no LVEF, MI) lowers mean |SMD| from 0.119 to 0.115:
  - **3.2% (95% CI −1.0 to 7.2)**, 19/32 trials better, P = .075 (q .22);
  - single-draw version 1 value, for comparison: 4.5% (−2.9 to 10.9), P = .11.
- **All 38 trials:** 3.6% (−0.3 to 7.3), 24/38, P = .037.
- **Against the permuted ECG:**
  - the ECG gives 4.4% (−0.0 to 8.5) on 32 trials (P = .031) and 4.8% (0.9 to 8.6) on 38 (P = .011);
  - the permuted ECG itself: −1.2% (−3.2 to 0.8), P = .27 (two-sided).
- **Draw-to-draw range** of the main contrast (+ ECG vs PS alone, 32 trials): 4.5 / 3.2 / 6.0 / −1.8 / 4.4 (range −1.8 to 6.0). The MI estimate sits inside it.
- **Where it helps** (32 trials, main):
  - observed LVEF, the only vitals/labs item not masked: 24.8% (15.3 to 32.7), P < .001;
  - LV structure: 7.0% (0.3 to 12.6), P = .028;
  - all 35 echo items: 2.7% (−2.2 to 7.2), P = .14.
- **Other PS methods** (32 trials): the gain is larger and significant with 1:3 matching (5.1%), overlap weighting (5.5%) and gbm (5.1%), all P ≤ .002. It is smallest with IPTW (1.5%, P = .23).
- **RCT agreement.** With the Rubin-combined log HR, |Δ log HR| goes from 0.166 to 0.149: 22/32 trials closer, sign-flip P = .025, benchmark-permutation P = .002. **Read this with caution.**
  - In the single draw it was 0.150 → 0.153 (P = .63).
  - The MI result is driven mainly by the PS-alone arm's HR being farther from the RCTs in draws 4 and 5 (0.176 and 0.194, against 0.150 in draw 1). The + ECG arm is steadier (0.141–0.160).
  - So it reflects the instability of the PS-alone HRs across draws as much as a gain from the ECG.
  - Caliper 0.1 matching shows the same pattern (0.166 → 0.150, P = .047, permutation P = .028). The other PS methods show no such gain (1:3, overlap, IPTW, gbm: P ≥ .052).
- **Bottom line.**
  - On the primary (version 1) cohorts and paper 1's 32 trials, proper MI moves the ECG gain at the richest PS level from 4.5% (single draw) to **3.2%, still not significant** (P = .075).
  - It is significant on all 38 trials and under 1:3, overlap and gbm.
  - It is clearly better than the permuted ECG, and it is concentrated in observed LVEF and LV structure.
  - The draws differ by about 8 points (−1.8 to 6.0), so a single-draw estimate should not be reported.

## 1. Design

As `docs/v2_psclin_mi/PS_CLINICAL_MI.md` §1. The differences:

| Element | Choice |
|---|---|
| Cohorts | version 1 analysed rows (all rows; version 1 outcomes); PCs computed within the cohort rows, which here equal the version 1 PCs (confirmed by the gate) |
| Imputation population | the full pre-ECG baseline roster (`claude-<trial>-baseline-v11/restricted_baseline_observed.parquet`), as version 1's no-LVEF re-imputation; the analysed cohort is a subset |
| Imputation model | `build_core_baseline.impute(observed without lvef, treated, m = 5)`, IterativeImputer(`sample_posterior=True`, `max_iter=10`, `random_state=20260923 + k − 1`); observed values kept (asserted, 38 × 5 tables); draws asserted to differ from each other where values were imputed |
| Arms, configurations, masks, F1 rule, combination | unchanged. Masks for this rung: the 8 observed vitals/labs that are PS inputs (not LVEF), eGFR and the 4 coded items, so 45 of the 54 items are held out and the 54- and 58-item endpoints coincide. **No MI cell failed** (0/1,406) |
| Other rungs in the summaries | the version 1 cells (`grid.reference()`: claude-v21-paper2 core, claude-v1-ps10, claude-v1-psclin-nolvef) |
| Sets | S32 = paper 1's 32 trials (v19 tiers, `docs/v19/quality_tiers.json`, Limited excluded: ALLHAT, ASCOT-BPLA, DECLARE-TIMI 58, ONTARGET, REWIND, VALUE); S38. S29, Snew (30) and SEG (12) are also in `summary/contrasts.csv` for the record |

## 2. Gate

| Check | Result |
|---|---|
| Imputation, draw 1 vs `claude-v1-psclin-nolvef/imputation/restricted_completed_nolvef_01_*` | equal, 38/38 trials (asserted in `impute`; `imputation/imputation_log_v1.json`) |
| Cells, draw 1 vs `claude-v1-psclin-nolvef/cells/restricted_cells.parquet` (rung `clinical_nolvef`) | 6 configurations × 7 arms (incl. CLMBR-T 32 PCs, main) × 38 trials = 1,406 cells; 98,420 values; **PASS: maximum deviation 0, 0 NaN mismatches, 0 string mismatches** (`cells/gate_status.json`) |
| Summary, draw 1 as a rung vs the version 1 single-draw rung | identical contrasts (S32 main: 4.5% and 8.7% for ECG vs PS alone and vs the permuted ECG; the version 1 values) |

## 3. Results, main configuration

Leakage-corrected masks; 45 items held out. Relative reduction = 100 × (1 − mean over trials of the arm's mean |SMD| / same for the comparator). 54 items = 58 items for this rung. P = exact sign-flip across trials: one-sided for a representation vs its base or placebo, two-sided for placebo vs base. q = BH within the rung's family (within-rung contrasts × 6 configurations × 4 balance endpoints, per set).

| Set | Contrast | mean \|SMD\| | rel. reduction (95% CI) | better | P | q | % \|SMD\| < 0.1 (P) | \|Δ log HR\| (closer; P; perm. P) |
|---|---|---|---|---|---|---|---|---|
| S32 | **+ ECG vs PS alone** | 0.119 → 0.115 | **3.2% (−1.0 to 7.2)** | 19/32 | .075 | .22 | 57.0 → 59.1 (.064) | 0.166 → 0.149 (22/32; .025; .002) |
| S32 | + permuted ECG vs PS alone | 0.119 → 0.121 | −1.2% (−3.2 to 0.8) | 11/32 | .27 | .43 | 57.0 → 58.8 (.038) | 0.166 → 0.160 (18/32; .32; .11) |
| S32 | ECG vs permuted ECG | 0.121 → 0.115 | 4.4% (0.0 to 8.5) | 22/32 | .031 | .13 | | 0.160 → 0.149 (17/32; .067; .051) |
| S38 | **+ ECG vs PS alone** | 0.113 → 0.109 | **3.6% (−0.3 to 7.3)** | 24/38 | .037 | .11 | 59.5 → 61.5 (.036) | 0.166 → 0.150 (25/38; .024; .002) |
| S38 | + permuted ECG vs PS alone | 0.113 → 0.114 | −1.3% (−3.1 to 0.5) | 14/38 | .20 | .32 | 59.5 → 60.8 (.061) | 0.166 → 0.162 (19/38; .54; .15) |
| S38 | ECG vs permuted ECG | 0.114 → 0.109 | 4.8% (0.9 to 8.6) | 26/38 | .011 | .050 | | 0.162 → 0.150 (22/38; .036; .034) |

(The S32 CI lower bounds of ECG vs permuted ECG are −0.02 (main) and −0.01 (cal01), shown rounded as 0.0.)

**CLMBR-T rows (record only; not in the paper), main:**

| Contrast | S32 | S38 |
|---|---|---|
| + CLMBR-T vs PS alone | 2.2% (−3.9 to 7.4), P .24 | 2.5% (−3.1 to 7.4), P .19 |
| + CLMBR-T + ECG vs PS alone | 2.7% (−2.6 to 8.0), P .16 | 3.6% (−1.3 to 8.5), P .076 |
| + CLMBR-T + ECG vs + CLMBR-T | 0.5% (−3.0 to 4.5), P .42 | 1.1% (−2.0 to 4.6), P .29 |
| CLMBR-T vs permuted CLMBR-T | 3.8% (−2.5 to 9.6), P .12 | 3.9% (−1.9 to 9.2), P .089 |
| + CLMBR-T 32 PCs vs PS alone | 2.9% (−0.5 to 6.2), P .060 | 2.8% (−0.3 to 5.8), P .046 |

## 4. All configurations (54 items; S32 | S38)

**+ ECG vs PS alone** (rel. reduction; better; P | |Δ log HR| PS alone → + ECG; closer; P; perm. P):

| config | S32 | S38 |
|---|---|---|
| main | 3.2% (−1.0 to 7.2); 19/32; .075 \| 0.166 → 0.149; 22/32; .025; .002 | 3.6% (−0.3 to 7.3); 24/38; .037 \| 0.166 → 0.150; 25/38; .024; .002 |
| cal01 | 3.0% (−1.2 to 7.0); 21/32; .090 \| 0.166 → 0.150; 18/32; .047; .028 | 3.5% (−0.5 to 7.2); 25/38; .044 \| 0.165 → 0.149; 23/38; .027; .013 |
| m13 | 5.1% (1.9 to 8.7); 22/32; .002 \| 0.163 → 0.156; 17/32; .15; .19 | 5.6% (2.7 to 8.8); 27/38; < .001 \| 0.163 → 0.158; 21/38; .19; .21 |
| iptw | 1.5% (−2.2 to 5.4); 20/32; .23 \| 0.199 → 0.212; 13/32; .89; .79 | 1.9% (−1.4 to 5.3); 25/38; .15 \| 0.189 → 0.198; 18/38; .84; .72 |
| overlap | 5.5% (2.2 to 9.3); 22/32; < .001 \| 0.165 → 0.159; 17/32; .17; .26 | 6.0% (3.0 to 9.3); 27/38; < .001 \| 0.162 → 0.156; 22/38; .10; .16 |
| gbm | 5.1% (2.2 to 8.0); 22/32; .002 \| 0.167 → 0.152; 17/32; .060; .10 | 5.1% (2.2 to 7.8); 26/38; < .001 \| 0.174 → 0.160; 21/38; .052; .073 |

**ECG vs permuted ECG:**

| config | S32 | S38 |
|---|---|---|
| main | 4.4% (0.0 to 8.5); .031 | 4.8% (0.9 to 8.6); .011 |
| cal01 | 4.3% (0.0 to 8.5); .030 | 4.9% (0.9 to 8.6); .010 |
| m13 | 4.7% (1.7 to 8.2); .002 | 5.4% (2.5 to 8.4); < .001 |
| iptw | 3.4% (−0.6 to 7.4); .062 | 3.4% (−0.1 to 7.1); .040 |
| overlap | 6.3% (3.1 to 10.0); < .001 | 6.7% (3.8 to 9.9); < .001 |
| gbm | 4.3% (1.1 to 7.5); .006 | 4.6% (1.9 to 7.5); .001 |

**+ permuted ECG vs PS alone** (two-sided) ranges from −1.9% to 0.8% (S32) and from −1.6% to 0.5% (S38). It is nominally significant only for overlap weighting (−0.8%, P .008 / .004).

## 5. Domains (main; PS alone → + ECG; relative reduction; better; P)

| Domain (items) | S32 + ECG vs PS alone | S32 ECG vs permuted ECG | S38 + ECG vs PS alone |
|---|---|---|---|
| Vitals & core labs (9; only observed LVEF held out) | 0.119 → 0.090; 24.8% (15.3 to 32.7); 22/32; < .001 | 32.2% (22.6 to 39.9); < .001 | 22.1% (14.3 to 29.4); 26/38; < .001 |
| Other labs (10) | 2.9% (−2.2 to 7.7); .14 | 0.1% (−7.3 to 7.0); .49 | 2.9% (−1.8 to 7.3); .12 |
| Echo: LV structure (7) | 7.0% (0.3 to 12.6); 21/32; .028 | 8.9% (2.6 to 14.9); .007 | 7.6% (1.8 to 12.8); 26/38; .011 |
| Echo: LV function (4) | 3.0% (−5.4 to 11.0); .25 | 8.1% (−1.5 to 16.5); .063 | 4.5% (−3.0 to 11.5); .12 |
| Echo: diastolic / LA (8) | 6.8% (−1.8 to 15.1); .078 | 5.6% (−2.4 to 13.5); .11 | 7.2% (−0.8 to 14.5); .049 |
| Echo: RV / pulmonary (7) | 4.1% (−2.4 to 10.0); .13 | 4.1% (−2.1 to 9.7); .11 | 4.3% (−1.7 to 9.7); .095 |
| Echo: valves / aorta (9) | −3.8% (−9.8 to 1.9); .88 | −1.4% (−6.8 to 3.4); .67 | −3.8% (−9.5 to 1.4); .90 |
| Echo, all 35 items | 0.130 → 0.127; 2.7% (−2.2 to 7.2); 18/32; .14 | 4.2% (−0.3 to 8.4); .039 | 3.2% (−1.4 to 7.4); 22/38; .085 |

Other configurations and sets: `summary/domains.csv`.

## 6. Draws and Rubin's rules

**Main contrast by draw (main configuration, 54 items):**

| Set | Contrast | draw 1 / 2 / 3 / 4 / 5 | MI |
|---|---|---|---|
| S32 | + ECG vs PS alone | 4.5 / 3.2 / 6.0 / −1.8 / 4.4 | 3.2 (−1.0 to 7.2) |
| S32 | ECG vs permuted ECG | 8.7 / 6.6 / 3.2 / −0.3 / 3.8 | 4.4 (0.0 to 8.5) |
| S32 | + permuted ECG vs PS alone | −4.6 / −3.6 / 2.8 / −1.5 / 0.7 | −1.2 |
| S38 | + ECG vs PS alone | 5.3 / 3.5 / 5.9 / −0.4 / 4.0 | 3.6 (−0.3 to 7.3) |
| S38 | ECG vs permuted ECG | 8.5 / 8.0 / 3.0 / 0.8 / 4.0 | 4.8 (0.9 to 8.6) |

Draw 1 equals the version 1 single-draw value (4.5% / 8.7% on S32; 5.3% / 8.5% on S38).

**|Δ log HR| by draw** (main, S32; PS alone → + ECG; closer; sign-flip P; permutation P):

| Draw | Result |
|---|---|
| 1 | 0.150 → 0.153; 14/32; .63; .15 |
| 2 | 0.167 → 0.154; 20/32; .16; .03 |
| 3 | 0.168 → 0.160; 18/32; .28; .08 |
| 4 | 0.176 → 0.141; 19/32; .04; .33 |
| 5 | 0.194 → 0.154; 24/32; .001; < .001 |

The PS-alone arm's agreement varies more across draws (0.150–0.194) than the + ECG arm's (0.141–0.160). The MI improvement in |Δ log HR| (0.166 → 0.149) therefore comes partly from the PS-alone arm's instability.

**Between-draw share of the Rubin total variance** (median over 38 trials; `summary/rubin_diagnostics.csv`):

| Method | Between-draw share | Combined SE vs mean within-draw SE |
|---|---|---|
| main matching | 0.16–0.21 | about 9–12% larger (maximum 1.7×) |
| cal01 | 0.17–0.25 | |
| gbm | 0.16–0.21 | |
| 1:3 matching | about 0.07–0.09 | |
| IPTW | about 0.04 | |
| overlap weighting | under 0.01 | |

As on the fixed cohorts, most of the imputation noise enters through which patients get matched.

## 7. Ladder on the version 1 cohorts (main; + ECG vs PS alone, 54 items)

The other rungs are the version 1 cells, unchanged.

| PS base | S32: PS alone → + ECG | S32: rel. reduction (95% CI); better; P | S38: PS alone → + ECG | S38: rel. reduction (95% CI); better; P |
|---|---|---|---|---|
| PS-Demo | 0.143 → 0.127 | 11.3% (6.0 to 16.1); 26/32; < .001 | 0.139 → 0.121 | 12.6% (7.7 to 16.8); 32/38; < .001 |
| **PS-CVD5 (primary)** | 0.130 → 0.118 | **8.8% (4.4 to 13.3)**; 21/32; < .001 | 0.124 → 0.112 | 9.0% (5.0 to 13.5); 26/38; < .001 |
| PS-CVD10 | 0.121 → 0.115 | 5.0% (−0.8 to 10.3); 23/32; .051 | 0.115 → 0.109 | 4.8% (−0.5 to 9.8); 27/38; .042 |
| hdPS | 0.118 → 0.109 | 7.6% (1.7 to 13.0); 22/32; .008 | 0.112 → 0.103 | 7.6% (2.2 to 12.6); 27/38; .004 |
| **PS-Clinical (no LVEF), MI** | **0.119 → 0.115** | **3.2% (−1.0 to 7.2); 19/32; .075** | 0.113 → 0.109 | 3.6% (−0.3 to 7.3); 24/38; .037 |

Means are per-rung (each rung's own mask). On the 35 echo items (S32), PS alone → + ECG:

| PS base | S32, 35 echo items |
|---|---|
| PS-Demo | 0.157 → 0.136 |
| PS-CVD5 | 0.140 → 0.127 |
| CVD10 | 0.134 → 0.128 |
| hdPS | 0.133 → 0.122 |
| PS-Clinical (no LVEF, MI) | 0.130 → 0.127 |

**Ladder comparisons (PS alone, main, S32 | S38):**

| Comparison | S32 | S38 |
|---|---|---|
| PS-Clinical (no LVEF, MI) vs PS-CVD5 | 7.5% (2.3 to 12.4); 24/32; P .006 | 7.2% (2.6 to 11.9); P .004 |
| PS-Clinical (no LVEF, MI) vs hdPS | 2.8% (−5.4 to 10.0); P .50 | 2.2% (−5.4 to 9.2); P .57 |
| PS-CVD5 + ECG vs PS-Clinical (no LVEF, MI) alone | 1.6% (−2.7 to 6.1); 15/32; P .48 | 2.0% (−2.0 to 6.0); P .34 |

The ECG on top of PS-CVD5 roughly matches the clinical PS.

## 8. Notes

- **Same imputation population as version 1.** The roster-wide imputation (pre-ECG baseline roster, analysed cohort a subset) is what makes draw 1 identical to version 1. The spec-v2 run imputed within the fixed cohort instead (see `docs/v2_psclin_mi/PS_CLINICAL_MI.md` §6).
- **Averaging |SMD| across draws** is mildly conservative for balance: the mean of |SMD| is at least |mean SMD|. Treatment is an imputation predictor, as in version 1.
- **The "Vitals & core labs" domain** for this rung contains only one held-out item, observed LVEF. The other 8 are masked as PS inputs.
- **Failed cells:** none in the MI rung. `summary/failed_cells.csv` lists only the version 1 PS-Flags and hdPS failures, which were already known.

## 9. Files

- **Repository:** `scripts/v2_psclin_mi/psclin_mi_v1.py`, this document. `scripts/v2_psclin_mi/psclin_mi.py` was not changed.
- **Audits** (`/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-psclin-mi/`):
  - `imputation/`: `restricted_completed_nolvef_v1_<trial>.parquet` (5 draws, full roster) and `imputation_log_v1.json`;
  - `cells/`:
    - `restricted_cells_v1.parquet`: 7,030 per-draw cells;
    - `restricted_cells_v1_mi.parquet`: 1,406 MI cells, rung `clinical_nolvef_mi`, the column layout of `claude-v2-psclin-mi/cells/restricted_cells_v2_mi.parquet` (asserted), for `scripts/build_balance_explorer.py`;
    - `restricted_cells_v1_mi_v1layout.parquet`: the same cells in the exact columns, dtypes and row order of `claude-v1-psclin-nolvef/cells/restricted_cells.parquet`, rung `clinical_nolvef`, as a drop-in for the version 1 explorer loader;
    - `cells_v1_mi.csv`: suppressed;
    - `gate.csv`, `gate_status.json`;
  - `summary/`: `contrasts.csv`, `domains.csv`, `ladder.csv`, `per_trial.csv`, `rubin_diagnostics.csv`, `failed_cells.csv`;
  - `privacy_scan.json`: clean;
  - `logs/`;
  - `DONE`.
