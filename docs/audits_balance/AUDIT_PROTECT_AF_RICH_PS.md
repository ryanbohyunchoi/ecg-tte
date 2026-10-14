# Audit: PROTECT AF and the rich-PS arms (hdPS + CLMBR-T) in the Figure 2C ladder

**Date:** 2026-10-14. **Auditor:** Claude (adversarial audit, read-only on code, figures and deck).

**Scope.** The suspected artefact on paper 1's 32 trials (version 1 cohorts; main configuration: 1:1 greedy matching on the PS logit, caliper 0.2, L2 logistic C = 1; 54 leakage-corrected held-out items):
- hdPS + CLMBR-T shows **−3.5%** relative change vs hdPS alone;
- that becomes **+0.6%** without PROTECT AF;
- PROTECT AF's hdPS mean |SMD| is 0.240, against 0.114 in the other 31 trials;
- its hdPS + CLMBR-T + ECG cell fails (<11 pairs).

**Sources (read only):**
- `audits/claude-v21-paper2/core/restricted_cells.parquet`;
- `audits/claude-v1-ps10/cells/restricted_cells.parquet`;
- `audits/claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet`;
- the grid, engine and figure code named in each section.

**Audit scripts and outputs:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-audit-protectaf/` (umask 077):
- `a1_protect.py`: PROTECT AF re-run, PS diagnostics, construction checks, noise floor;
- `a1b_hdps_top.py`, `a1c_zerocell.py`: hdPS level mechanism checks;
- `a2_loo_common.py`: leave-one-out and like-for-like levels;
- `a3b_panelC.py`: Panel C on a common trial set;
- `a5_scan.py`: all 38 trials;
- `a6_rules.py`: handling rules.

Files named `restricted_*` hold exact counts and stay on the cluster.

**Privacy.** This document gives aggregates only. Matched-pair counts are not reported: retention is banded, and cells with fewer than 11 pairs are shown as "<11".

**Context.** pipeline.md was updated on 2026-10-14, while this audit was running. It raises the feasibility size rule to ≥350 in the smaller arm, which removes PROTECT AF and makes 31 trials the primary set. Section 7 assesses that rule.

---

## Verdict

1. **Not a bug.**
   - All 38 PROTECT AF main-configuration cells reproduce exactly when re-run with `E.run_cell` on the trial object (max |deviation| 0.0 over the log HR, SE, counts and 58 |SMD| values; no NaN mismatches).
   - The grid also equals `claude-v18-embed-compare` exactly (912 cells; this audit and `gate_status.json`).
   - Every construction check passes (section 4).
2. **It is a genuine overlap and small-sample artefact with two layers.**
   - **(a) Poor overlap under coded-history PS models, in the trial with the smallest smaller arm (~310).**
     - CLMBR-T alone separates the arms: cross-fitted C 0.93–0.94 even on top of PS-Demo or PS-CVD5. The permuted CLMBR-T gives 0.53–0.62.
     - The hdPS alone reaches cross-fitted C 0.89 and keeps 30–50% of the smaller arm.
     - hdPS + CLMBR-T (280 inputs, 0.89 inputs per smaller-arm patient): in-sample C 0.999, cross-fitted C 0.956, 74% of patients with PS < 0.01 or > 0.99, <5% of the smaller arm retained (11–20 pairs).
     - Adding ECG (312 inputs) gives <11 pairs, so the cell fails.
     - This is real separation plus overfitting. The CLMBR-T C-statistic barely drops under cross-fitting. The hdPS and PS-Flags models overfit: in-sample vs cross-fitted C 0.98 vs 0.89, and 1.00 vs 0.72.
   - **(b) Mean |SMD| in a small matched sample is dominated by sampling noise.**
     - The expected |SMD| with *no* confounding at the realised matched size (the "noise floor", section 6) is 0.51 for the hdPS + CLMBR-T cell. The observed value is 0.40.
     - For the hdPS base cell, the floor is 0.19 against 0.24 observed.
     - So the cell's "worse balance" is unmeasurable, not worse.
3. **PROTECT AF is the dominant influential trial, but not the only one.**
   - Leave-one-trial-out changes larger than 1.5 points, in paired relative change vs PS alone:

     | Trial | Changes > 1.5 points |
     |---|---|
     | PROTECT AF | hdPS + CLMBR-T +4.2; PS-Clinical + CLMBR-T +2.2; the plotted (unpaired) hdPS + both level −3.0 |
     | CABANA | PS-Demo + CLMBR-T −2.4; PS-Demo + both −2.0 |
     | CANVAS | hdPS + ECG +2.0; hdPS + CLMBR-T +2.0; PS-CVD10 + both +1.6 |
     | LEADER | hdPS + CLMBR-T −1.6 |
     | RAFT-AF | plotted hdPS + both level only, +1.5 |
   - EMPA-REG is not influential: at most 1.0.
   - The headline PS-CVD5 + ECG changes by at most 1.1 (AF-CHF), and by 0.2 for PROTECT AF.
4. **Figure 2C mixes trial sets.**
   - Each plotted point is an unpaired mean over the trials where that cell did not fail. The labels are paired.
   - The only affected point is hdPS + CLMBR-T + ECG: 31 trials, against 32 for hdPS alone. Its visual gap (−12.1%) overstates the paired change (−8.5%) by 3.6 points, because PROTECT AF is in the denominator but not the numerator.
   - Item-set differences are negligible (≤ 0.0007 |SMD|).
5. **Recommendation** (section 7):
   - plot every ladder level on one common trial set;
   - keep the paired labels;
   - apply any exclusion as a uniform, cell-level overlap rule (minimum retention, or minimum matched pairs) rather than a size threshold set just above one trial;
   - report overlap weighting alongside, because it is nearly insensitive to PROTECT AF.
   - The headline PS-CVD5 + ECG barely moves: 8.8% → 8.7% (31 trials) → 7.4% (overlap weighting, 32 trials).
   - All these handling rules are post hoc.

---

## 1. PROTECT AF: diagnostics by PS level × arm (main configuration)

PROTECT AF is the trial with the smallest smaller arm among all 38: about 1,440 patients, about 310 in the smaller (LAAO) arm. The next smallest is INSIGHT, at about 400.

**Columns:**
- *Inputs / smaller arm* = PS columns ÷ smaller-arm size.
- *C in-sample* = AUC of the fitted PS (L2, C = 1, standardised, as `v13_common.ps_logit`).
- *C cross-fitted* = the same model, 5-fold stratified, scaler fitted within folds.
- *Mean abs SMD (54)* = mean |SMD| over the 54 items (45 for PS-Clinical, where the ex58 mask applies).
- *Noise floor* = expected mean |SMD| at the cell's realised matched size with random labels (section 6).

| PS | arm | inputs | inputs / smaller arm | retention (smaller arm) | C in-sample | C cross-fitted | PS <0.01 or >0.99 | mean abs SMD (54) | noise floor |
|---|---|---|---|---|---|---|---|---|---|
| PS-Demo | base | 3 | 0.01 | ≥90% | 0.541 | 0.522 | 0% | 0.221 | 0.11 |
| PS-Demo | ECG | 35 | 0.11 | ≥90% | 0.664 | 0.595 | 0% | 0.166 | 0.11 |
| PS-Demo | CLMBR | 67 | 0.21 | 30–50% | 0.960 | 0.934 | 37% | 0.171 | 0.17 |
| PS-Demo | ECG+CLMBR | 99 | 0.32 | 30–50% | 0.966 | 0.928 | 40% | 0.147 | 0.17 |
| PS-Demo | shufECG | 35 | 0.11 | ≥90% | 0.604 | 0.473 | 0% | 0.162 | 0.11 |
| PS-Demo | shufCLMBR | 67 | 0.21 | ≥90% | 0.654 | 0.528 | 0% | 0.209 | 0.11 |
| PS-CVD5 | base | 8 | 0.03 | ≥90% | 0.657 | 0.648 | 2% | 0.172 | 0.11 |
| PS-CVD5 | ECG | 40 | 0.13 | ≥90% | 0.713 | 0.654 | 3% | 0.149 | 0.11 |
| PS-CVD5 | CLMBR | 72 | 0.23 | 30–50% | 0.964 | 0.937 | 39% | 0.172 | 0.17 |
| PS-CVD5 | ECG+CLMBR | 104 | 0.33 | 30–50% | 0.969 | 0.932 | 43% | 0.193 | 0.18 |
| PS-CVD5 | shufECG | 40 | 0.13 | ≥90% | 0.679 | 0.597 | 2% | 0.149 | 0.11 |
| PS-CVD5 | shufCLMBR | 72 | 0.23 | ≥90% | 0.717 | 0.616 | 2% | 0.158 | 0.11 |
| PS-CVD10 | base | 13 | 0.04 | ≥90% | 0.667 | 0.648 | 2% | 0.204 | 0.11 |
| PS-CVD10 | ECG | 45 | 0.14 | ≥90% | 0.721 | 0.658 | 3% | 0.149 | 0.11 |
| PS-CVD10 | CLMBR | 77 | 0.25 | 30–50% | 0.965 | 0.934 | 40% | 0.177 | 0.17 |
| PS-CVD10 | ECG+CLMBR | 109 | 0.35 | 30–50% | 0.970 | 0.929 | 44% | 0.172 | 0.18 |
| PS-Flags | base | 625 | 1.99 | <11 pairs (failed) | 1.000 | 0.723 | 60% | – | – |
| PS-Flags | ECG / CLMBR / both / placebos | 657–721 | 2.1–2.3 | <11 pairs (all failed) | 1.000 | 0.73–0.88 | 60–75% | – | – |
| hdPS | base | 216 | 0.69 | 30–50% | 0.978 | 0.892 | 52% | 0.240 | 0.19 |
| hdPS | ECG | 248 | 0.79 | 20–30% | 0.984 | 0.890 | 56% | 0.205 | 0.21 |
| **hdPS** | **CLMBR** | 280 | 0.89 | **<5% (11–20 pairs)** | 0.999 | 0.956 | 74% | **0.403** | **0.51** |
| **hdPS** | **ECG+CLMBR** | 312 | 0.99 | **<11 pairs (failed)** | 1.000 | 0.953 | 75% | – | – |
| hdPS | shufECG | 248 | 0.79 | 30–50% | 0.982 | 0.888 | 54% | 0.275 | 0.20 |
| hdPS | shufCLMBR | 280 | 0.89 | 20–30% | 0.986 | 0.884 | 56% | 0.218 | 0.22 |
| PS-Clinical (with LVEF, v1) | base | 36 | 0.11 | ≥90% | 0.786 | 0.750 | 3% | 0.155 | 0.12 |
| PS-Clinical (with LVEF, v1) | CLMBR | 100 | 0.32 | 30–50% | 0.973 | 0.936 | 46% | 0.168 | 0.18 |

PS-Clinical (no LVEF, 5-draw MI) is the ladder rung; it was not re-fitted here. Its stored retention is:
- base: ≥90%;
- + ECG: 70–90%;
- + CLMBR-T and + both: 30–50%.

No cell in that rung failed.

**Reproduction (item 1).**
- PROTECT AF has 38 main-configuration cells: 5 v21 rungs plus PS-CVD10, × 6 or 7 arms.
- Each was rebuilt exactly as `paper2_grid.task` / `ps10.task` and re-run with `E.run_cell`.
- Max |deviation| from the stored cells was 0.0 over n, n_t, n_c, n_pairs, log HR, SE, ESS and the 58 |SMD| values, with no NaN mismatches. This includes the hdPS and hdPS + CLMBR-T cells, and the failed hdPS + CLMBR-T + ECG cell, which fails identically.

**Is this near-separation or overfitting? Both, for different inputs.**
- **CLMBR-T: genuine separation.**
  - Even with only 3 demographic covariates, the 64 CLMBR-T PCs give a cross-fitted C of 0.934 (in-sample 0.960).
  - The permuted CLMBR-T gives 0.53. The largest single-PC correlation with treatment is |r| = 0.33; for ECG it is 0.11.
  - The coded record strongly identifies who receives LAAO vs warfarin. This is not overfitting.
- **hdPS and PS-Flags: overfitting at C = 1 in a small trial.**
  - In-sample vs cross-fitted C is 0.978 vs 0.892 for the hdPS (across trials, median gap 0.055; PROTECT AF 0.086), and 1.000 vs 0.723 for PS-Flags.
  - PROTECT AF has the most inputs per smaller-arm patient of all 38 trials in every rung: hdPS 0.69 (median 0.16); PS-Flags 1.99 (median 0.41).
- **The combination tips the cell over.** In hdPS + CLMBR-T, three-quarters of patients have PS outside [0.01, 0.99]. The caliper (0.2 × pooled SD of the arm's own logit, logit SD ~7) cannot bridge the two piles.

**Which items drive the high |SMD|** (item names only; per-item values over ~a dozen pairs are mostly noise):
- hdPS + CLMBR-T: NT-proBNP, E/A, LVEDD, RV S′, LV systolic grade, LV posterior wall.
- hdPS + CLMBR-T + ECG, before the F1 rule blanks it: NT-proBNP, AV Vmax, AV mean gradient, E/A, aortic root, RVSP.
- hdPS base: RV systolic grade, RVIDd, RV S′, observed SBP, echo EF, observed LVEF.
- PS-Demo base: hs-troponin T, albumin, WBC, observed LVEF, echo EF, LAVI.

These are scattered echo and lab items from different domains, with a different set in every arm. That is the signature of noise, not of one systematically unbalanced confounder.

**Mechanism checks (hdPS):**
- The top-ranked hdPS levels in PROTECT AF are mostly codes nearly absent in the LAAO arm: mannitol, milrinone and papaverine orders, several local procedure codes and malnutrition (E43). This suggests post-cardiac-surgery patients in the warfarin arm, who are structurally not LAAO candidates.
- One code is enriched in the LAAO arm: CPT 93662, intracardiac echocardiography.
- Hypothesis tested: the hdPS ranking (|log prevalence ratio| with a 1e-3 offset) favours levels absent in one arm, and these cause the separation. **Refuted.**
  - 13 of the top 200 levels are absent in one arm.
  - Refitting without them leaves retention in the same band (hdPS: 30–50%; hdPS + CLMBR-T: <5%) and the C-statistics essentially unchanged (cross-fitted 0.888 and 0.954).
  - The separation is spread over many codes. It is not caused by a few zero-cell levels.

## 2. Leave-one-trial-out influence on the ladder

**Method.**
- Paired relative change vs PS alone, `BE.pair_stats` on the Figure 2 grid (S32, main, 54 items, leakage-corrected masks, F1 rule).
- Recomputed without each of the 32 trials, for every rung × arm: PS-Demo, PS-CVD5, PS-CVD10, PS-Clinical (no LVEF, MI) and hdPS, each × {ECG, CLMBR-T, both, permuted ECG, permuted CLMBR-T}.
- The figure's unpaired level ratio was also recomputed.
- Full table: `a2_loo.csv`.

**Changes > 1.5 points:**

| Comparison (vs PS alone) | All 32 | Trial removed | Without it | Δ |
|---|---|---|---|---|
| hdPS + CLMBR-T | −3.5 | **PROTECT AF** | +0.6 | **+4.2** |
| hdPS + CLMBR-T | −3.5 | CANVAS | −1.6 | +2.0 |
| hdPS + CLMBR-T | −3.5 | LEADER | −5.1 | −1.6 |
| hdPS + ECG | 7.6 | CANVAS | 9.6 | +2.0 |
| PS-Clinical (no LVEF) + CLMBR-T | 2.2 | **PROTECT AF** | 4.4 | +2.2 |
| PS-Demo + CLMBR-T | 20.7 | CABANA | 18.3 | −2.4 |
| PS-Demo + CLMBR-T + ECG | 25.8 | CABANA | 23.8 | −2.0 |
| PS-CVD10 + CLMBR-T + ECG | 7.0 | CANVAS | 8.6 | +1.6 |
| *plotted level ratio* hdPS + both | 12.1 | **PROTECT AF** | 9.1 | −3.0 |
| *plotted level ratio* hdPS + both | 12.1 | RAFT-AF | 13.6 | +1.5 |

- **Below threshold:**
  - PS-CVD5 + ECG (headline): at most 1.1 (AF-CHF; PROTECT AF −0.2).
  - PS-Demo + ECG: 1.5 (INSIGHT).
  - PS-CVD10 + ECG: 1.4 (INSIGHT; PROTECT AF −1.2).
  - PS-Clinical + ECG: 1.2.
  - EMPA-REG: at most 1.0 anywhere.
  - RAFT-AF: at most 1.4 on paired values.
- **Removing PROTECT AF lowers every ECG gain except PS-Clinical's:** PS-Demo −0.7, PS-CVD5 −0.2, PS-CVD10 −1.2, hdPS −0.5. Excluding it is therefore *not* favourable to the ECG claim.
- **Why the others move:**
  - **CANVAS** keeps ≥90% retention in every arm, with cross-fitted C ≈ 0.67. Its influence is pure noise: few patients with echo, so a high noise floor (0.135, among the highest), and mean |SMD| moves 0.21 → 0.27 → 0.29 across arms with near-identical PS models.
  - **CABANA** is a genuine CLMBR-T effect: cross-fitted C 0.93 with CLMBR-T; PS-Demo mean |SMD| 0.231 → 0.080. CLMBR-T captures the selection to ablation.
  - **LEADER** is noise (floor 0.123).

## 3. Like-for-like trial and item sets in Figure 2C

**How Figure 2C computes each value** (`make_figure2_latent.level()` = the explorer's `levels()`):
- **Plotted point:** the mean across trials of each trial's mean |SMD| over *that arm's* observed items. Failed cells (<11 pairs) are all-NaN, so the trial drops out of that point only.
- **Label:** the paired relative change (`pair_stats`), using items observed in both arms and trials present in both.

**Decomposition of each plotted gap vs PS alone (`a3_common.csv`):**
- *Total* = the plotted gap.
- *Trial-set part* = total minus the gap on the rung's common trials.
- *Item-set part* = the further change when items are restricted to those observed in every plotted arm.

| Rung | Arm | Plotted level ratio | Paired label | Total gap | Trial-set part | Item-set part |
|---|---|---|---|---|---|---|
| hdPS | + ECG | 8.0% | 7.6% | −0.0094 | −0.0008 | −0.0005 |
| hdPS | + CLMBR-T | −3.2% | −3.5% | +0.0038 | **+0.0051** (PROTECT AF in both) | −0.0007 |
| hdPS | + both | **12.1%** | 8.5% | −0.0143 | **−0.0039** (PROTECT AF only in base) | −0.0007 |
| PS-CVD10 | + both | 7.6% | 7.0% | −0.0092 | 0 | −0.0007 |
| PS-Demo | + both | 25.4% | 25.8% | −0.0364 | 0 | +0.0006 |
| all other cells | | equal to the label within 0.4 points | | | 0 | ≤ 0.0005 |

- **The trial-set mismatch matters only at the hdPS rung, and only through PROTECT AF.** There it inflates the visual hdPS + both gain from 8.5% to 12.1%.
- **Items:** a cell with few pairs can lose items (zero-variance or unobserved in one matched arm). hdPS + CLMBR-T in PROTECT AF has 51 of 54 items. The effect on the plotted means is ≤ 0.0007.

**Recommendation for the figure.** Use one common trial set for the whole panel: the trials where every plotted cell is non-failed. Within each rung, use the items observed in every plotted arm. Keep the paired labels.
- Within a rung, leakage masks legitimately differ (PS-Clinical masks 8 observed vitals and labs plus eGFR). Applying common items *across* rungs would impose PS-Clinical's 45-item panel on every rung, so common items should be per rung.
- On the version 1 S32 grid with CLMBR-T arms, the common set is **31 trials** (PROTECT AF out).
- With ECG-only arms it is all 32: no ECG-only cell fails.

**Panel C under that rule** (31 trials; within-rung common items; labels = paired change on the same 31; `a3b_panelC.csv`):

| Level | Unmatched | PS alone | + ECG | + CLMBR-T | + both | + ECG label (32-trial figure) | + CLMBR-T vs PS | + both vs PS |
|---|---|---|---|---|---|---|---|---|
| PS-Demo | 0.143 | 0.141 | 0.126 | 0.112 | 0.105 | **−10.6%** (−11.3%) | −20.6% | −25.4% |
| PS-CVD5 | 0.143 | 0.129 | 0.117 | 0.112 | 0.110 | **−8.7%** (−8.8%) | −12.9% | −14.6% |
| PS-CVD10 | 0.143 | 0.118 | 0.114 | 0.110 | 0.110 | **−3.8%** (−5.0%) | −7.0% | −6.9% |
| PS-Clinical (no LVEF, MI) | 0.142 | 0.118 | 0.114 | 0.113 | 0.114 | **−3.3%** (−3.2%) | −4.4% | −3.4% |
| hdPS | 0.143 | 0.114 | 0.105 | 0.113 | 0.104 | **−7.1%** (−7.6%) | **+0.6%** (CI −7.0 to 7.4) | −8.5% |

Paired 95% bootstrap CIs on the 31 trials:

| Level | + ECG |
|---|---|
| PS-Demo | 5.3–15.6 |
| PS-CVD5 | 4.2–13.5 |
| PS-CVD10 | −1.6 to 9.0 |
| PS-Clinical | −1.1 to 7.5 |
| hdPS | 0.7–12.8 |

These values should equal the s31 recomputation queued on 2026-10-14 (`docs/queue/QUEUE_2026_10_14_S31.md`). They are an independent check on it.

## 4. Construction checks of the rich-PS arms (PROTECT AF; the duplicate-column check over all 38)

| Check | Result |
|---|---|
| CLMBR-T 64 PCs computed within the trial | Recomputed independently from the 768-d embedding files, de-duplicated and re-indexed to `T.keys`; `pcs(·, 64)` equals `T.clm_pc` exactly (max dev 0). No duplicate or missing keys. PCs centred (\|mean\| < 1e-15) and uncorrelated (off-diagonal \|r\| < 1e-14). |
| ECG 32 PCs within the trial | Recomputed from the BCL embeddings on `T.keys`: equals `T.ecg_pc` exactly. |
| Row alignment of appended blocks | Blocks are in `T.keys` order (grid rows `r = arange(n)`). The PS logit is invariant to a random row permutation of design and treatment (max dev 1.7e-11). |
| Column construction | hdPS + CLMBR-T = 216 + 64 = 280 (`p_ps` agrees for every cell); hdPS + CLMBR-T + ECG = 312. CLMBR-T and ECG blocks add no duplicated or constant columns. |
| Duplicated columns | **Minor finding, not CLMBR-specific:** the hdPS design has 1–5 duplicated columns in 16 of 38 trials (1 in PROTECT AF). These are two hdPS levels of different codes with identical patterns (e.g. two co-recorded procedure codes); `hdps_levels` de-duplicates within a code only. Under L2 this doubles the effective weight of that feature. It affects base and all arms of the rung equally and is immaterial here. |
| Standardisation | Every design goes through `StandardScaler` in `ps_logit`, identical for every rung and arm. Each PC gets unit variance and the same penalty. |
| hdPS ranking vector | `hdps_rank(T.lv, T.t)[:200]` reproduces the grid's hdPS columns exactly; the same `T.t` is used by `run_cell` (rows = all). |
| Caliper | `ps_greedy` uses 0.2 × sqrt((var(logit \| t=1) + var(logit \| t=0))/2) of the logit passed in, i.e. the arm's own PS. Largest matched-pair logit gap in hdPS + CLMBR-T = 0.9998 × width. |
| vs `claude-v18-embed-compare` | 4 rungs × 6 arms × 38 trials (912 cells): max \|dev\| 0.0, 0 NaN mismatches. The PROTECT AF hdPS + CLMBR-T cell has the same pair count in both (≥11). hdPS + CLMBR-T + ECG is <11 in both. v18 already flagged this: `docs/v18/EMBEDDING_COMPARISON.md`, "PROTECT AF at hdPS200 … the PS nearly separates the arms". |

## 5. Other near-separation cases (all 38 trials × rungs × arms, main configuration)

Source: `a5_scan.py`. PS C-statistics were refitted for P1, P5, PS10, Flags, hdPS200 and PS-Clinical (v1); retention was read from the stored cells, including the PS-Clinical (no LVEF, MI) rung.

**Cells retaining < 30% of the smaller arm** (all in S32; none in the 6 Limited trials):

| Trial | Cells (retention band) |
|---|---|
| PROTECT AF | PS-Flags, all 6 arms (<11 pairs, failed); hdPS + ECG (20–30%); hdPS + CLMBR-T (<5%); hdPS + CLMBR-T + ECG (<11 pairs, failed); hdPS + permuted CLMBR-T (20–30%) |
| RAFT-AF | PS-Flags + CLMBR-T (10–20%); PS-Flags + both (<10%) |
| EMPEROR-Preserved | PS-Flags + CLMBR-T and + both (20–30%) |

No ladder cell (PS-Demo, PS-CVD5, PS-CVD10, PS-Clinical no-LVEF MI, hdPS) outside PROTECT AF retains < 30%.

Ladder cells at 30–50% retention:
- **LODESTAR:** every ladder cell, including PS-CVD5 alone. This is a trial-level overlap feature, not specific to rich PS models.
- **EMPEROR-Preserved and SUSTAIN-6:** the CLMBR-T arms at every rung, and the hdPS arms.
- **PROTECT AF:** the CLMBR-T arms and hdPS alone.
- **RAFT-AF, ROCKET-AF and ACTIVE W:** hdPS + CLMBR-T (RAFT-AF also PS-Clinical + both).

**Extreme C-statistics:**
- **In-sample C ≥ 0.99:** only PROTECT AF (all PS-Flags arms; hdPS + CLMBR-T; hdPS + both) and RAFT-AF (PS-Flags + CLMBR-T, + both).
- **Cross-fitted C ≥ 0.90:** only the three procedure-vs-drug AF trials (**CABANA, PROTECT AF, RAFT-AF**), in every CLMBR-T arm at every rung. CABANA reaches it also with PS-Flags + CLMBR-T. CLMBR-T strongly encodes selection to ablation or LAAO.
  - CABANA (ablation) and RAFT-AF keep 50–90% retention at PS-Demo / PS-CVD5 + CLMBR-T.
  - Only PROTECT AF, the smallest, collapses.
  - Index-day exclusion was verified in `docs/v18/CLMBR_LEAKAGE.md`. Pre-procedural work-up or channelling codes in the days before index are a plausible source, but this was not tested here.

**Effect on reported numbers.** Excluding all three CLMBR-separating trials is not justified by any rule considered here. Only PROTECT AF fails any retention or pair threshold at the ladder rungs. Its effects are in sections 2 and 7.

## 6. Cross-cutting finding: the noise floor of mean |SMD|

**Definition.**
- For a cell with m matched pairs, the expected per-item |SMD| under *no* confounding was estimated by drawing 2m patients at random from the trial cohort and splitting them at random.
- The engine's own SMD code was used: the pooled pre-match SD as denominator, and items observed only in a subset.
- 40–200 draws per m, averaged over the 54 items.
- The result is approximate. Matching on a PS correlated with the items can lower the true floor a little.

**Across S32** (mean across trials; `a5_scan` floors):

| Level | Arm | Mean \|SMD\| | Noise floor | Excess |
|---|---|---|---|---|
| PS-CVD5 | base | 0.130 | 0.082 | 0.048 |
| PS-CVD5 | + ECG | 0.118 | 0.083 | 0.035 |
| hdPS | base | 0.118 | 0.090 | 0.029 |
| hdPS | + CLMBR-T | 0.122 | 0.103 | 0.019 |
| hdPS | + both (31) | 0.104 | 0.092 | 0.012 |

- **Most of every ladder level is sampling noise:** the floor is 57–89% of the level (PS-Demo alone 57%, PS-CVD5 alone 63%, hdPS + both 89%).
- **Arms that discard patients carry a higher floor and look worse even when equally balanced.** The hdPS + CLMBR-T "worsening" is entirely floor: the floor rises 0.0136 while the level rises 0.0038.
- **The ECG gains are not a retention artefact:** the floor is essentially unchanged with + ECG (0.082 → 0.083).
- **Size alone does not explain the floor.** At PS-CVD5, PROTECT AF's floor is 0.108, only the 8th highest of 32. INSIGHT (0.158), PROVE IT, CANVAS, VALIANT, LEADER, CAROLINA and RE-LY are noisier, because they have few patients with echo. PROTECT AF is anomalous only where rich PS models destroy overlap.

## 7. Recommendation (principled, uniform rules; all post hoc)

**Effect of uniform rules** (paired relative change vs PS alone, 54 items; `a6_rules.csv`).

*Per comparison* = a trial enters a comparison only if both cells pass. *Global* = a trial enters every comparison only if all 20 ladder cells (5 rungs × base / ECG / CLMBR-T / both) pass.

| Rule | PS-CVD5 + ECG (headline) | PS-Demo + ECG | PS-CVD10 + ECG | PS-Clin + ECG | hdPS + ECG | hdPS + CLMBR-T | Trials affected |
|---|---|---|---|---|---|---|---|
| Current (F1: ≥ 11 pairs) | **8.8** [4.4, 13.3] | 11.3 | 5.0 | 3.2 | 7.6 | −3.5 [−14.0, 6.0] | – |
| Per comparison: retention ≥ 30% | 8.8 | 11.3 | 5.0 | 3.2 | 7.1 | 0.6 | PROTECT AF (hdPS rows only) |
| Per comparison: ≥ 50 pairs | 8.8 | 11.3 | 5.0 | 3.2 | 7.6 | 0.6 | PROTECT AF (hdPS + CLMBR-T rows) |
| Per comparison: retention ≥ 50% | 9.0 | 11.1 | 5.3 | 3.3 | 6.8 | 0.5 | LODESTAR (all); EMPEROR-Pres., PROTECT AF, SUSTAIN-6 (CLMBR-T / hdPS); ACTIVE W, RAFT-AF, ROCKET-AF (hdPS + CLMBR-T) |
| **Global: every ladder cell ≥ 11 pairs, or ≥ 30% retention, or ≥ 50 pairs** (identical) | **8.7** [4.2, 13.5] | 10.6 | 3.8 | 3.3 | 7.1 | **0.6** [−7.0, 7.4] | PROTECT AF |
| Overlap weighting, all 32 (no exclusion) | **7.4** [4.3, 10.9] | 14.5 | 6.9 | 5.5 | 4.6 | 2.1 [−0.5, 5.4] | none; without PROTECT AF: 7.4 / 14.4 / 6.9 / 5.4 / 5.1 / 2.6 |
| *Feasibility size rule ≥ 350 (pipeline.md, 2026-10-14)* | *8.7* | *10.6* | *3.8* | *3.3* | *7.1* | *0.6* | *PROTECT AF (all analyses)* |

**Assessment of the ≥ 350 size rule** (user decision 2026-10-14; already disclosed as post hoc):
- In this grid it gives the same balance numbers as the global overlap rule, because PROTECT AF is the only trial removed.
- As a rule it is weakly principled:
  - **It is set just above one trial** (~310 smaller arm). Any threshold from about 315 to 400 does the same, because the next smallest is INSIGHT, at about 400.
  - **It targets cohort size, but the problem is overlap.** PROTECT AF's PS-CVD5 cells retain ≥ 90%, with a noise floor below 7 other trials.
  - **It removes PROTECT AF from every analysis**, including the agreement analyses, where it is not pathological.
- A cell-level overlap rule addresses the actual mechanism and generalises to future trials and arms.

**Recommended handling.** All items are post hoc and must be disclosed as decided after the PROTECT AF behaviour was seen.

1. **Keep the primary contrast unchanged.** PS-CVD5 + ECG vs PS-CVD5 is paired, and PROTECT AF's PS-CVD5 cells are well behaved. Every rule gives 8.7–9.0% (overlap weighting 7.4%), so the headline does not depend on the handling.
2. **Prespecify one uniform cell-validity rule for all trials, arms and PS levels**, in addition to the existing F1 (< 11 pairs). Retention ≥ 30% of the smaller arm, or ≥ 50 matched pairs, both work.
   - Apply it **globally for figures and ladders** (one common trial set) and **per comparison for paired tests**.
   - On the version 1 S32 grid either threshold removes only PROTECT AF. The ladder labels become 10.6 / 8.7 / 3.8 / 3.3 / 7.1% for + ECG, and hdPS + CLMBR-T becomes +0.6%.
   - If the user keeps the ≥ 350 size rule, state in the Methods that it coincides with this overlap rule on this grid, and give the overlap rationale.
3. **Draw Figure 2C on a common trial set,** with within-rung common items and paired labels (section 3 table).
   - This is a display rule, not an analysis change. It removes the 3.6-point visual exaggeration of hdPS + both.
   - With the s31 primary set it is automatically satisfied: no cell fails among the 31.
4. **Report overlap weighting alongside matching** for the ladder. It does not discard patients, so it is nearly insensitive to PROTECT AF (all changes ≤ 0.6 points except PS-Clinical + CLMBR-T, 1.2, and + both, 0.8). Note that PROTECT AF's ESS fraction is low under it for hdPS (10–20%) and hdPS + CLMBR-T (5–10%).
5. **Footnote text.** "near-separation" is accurate but incomplete. A fuller version: "hdPS + CLMBR-T retains < 5% of PROTECT AF's smaller arm; at that size mean |SMD| is dominated by sampling noise (expected ≈ 0.5 with no confounding)." With s31 the footnote is removed anyway.
6. **Optional diagnostic (supplement):** report each level's noise floor, or a noise-corrected balance metric, so that arms with different retention are compared fairly. This is exploratory; do not replace the locked endpoint.

**What is post hoc:**
- every rule in the table except the current F1 rule;
- the ≥ 350 size rule;
- the common-trial-set display rule;
- the noise-floor diagnostic.

The F1 rule (< 11 pairs = failed) predates this audit (v1 audit F1).
