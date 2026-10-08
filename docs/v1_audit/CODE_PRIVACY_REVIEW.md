# Version 1 (TRACE-ECG, tag `trace-v1`, commit 5c98301): code and privacy review

Written 2026-10-08 by an audit agent. Read-only review: no existing file was modified, and nothing was committed. Test scripts are in `scripts/v1_audit/code/`. Their outputs are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/code/` (umask 077; `restricted_*` files stay on raid0). This document contains aggregates only: no identifiers, and no counts of 1–10 patients.

## 1. Summary

- **The PS-CVD5 headline numbers in paper2 are correct.**
  - I re-derived them independently from `core/restricted_cells.parquet`, and they match to the last digit: ECG 8.8% (4.4–13.3), CLMBR-T 12.4% (7.1–17.7), both 13.5% (6.6–20.4), and the PS-Demo + CLMBR-T vs PS-Flags contrast.
  - I re-ran the engine on two real trials (RE-LY and PROTECT AF). It reproduces the saved cells exactly. Matching, caliper, SMD, PS fitting, determinism and convergence invariants all hold (§3).
- **No BLOCKING code bug was found.**
- **Three SHOULD-FIX analysis issues change secondary paper2 numbers:**
  - **F1 (new): cells with 1–10 matched pairs still enter the balance contrasts.**
    - Where: PROTECT AF, hdPS200 + ECG + CLMBR-T in the main, caliper 0.1 and 1:3 configurations, and hdPS200 + CLMBR-T with caliper 0.1.
    - In the main configuration, the published hdPS200 + both result is −1.4% (−22.5 to 13.3). With those cells treated as failed, it is +8.5% (2.0 to 14.7), q = .032.
    - The S32 count of q < .05 balance rows goes from 98 to 104: main 18 → 20, 1:3 18 → 20, gradient-boosted PS 18 → 19, overlap 23 → 24.
  - **F2 (known, now quantified): near-duplicate held-out items are not masked for PS-Clinical.** Over the 54 items, PS-CVD5 + CLMBR-T vs PS-Clinical moves from −4.9% to −3.8% (strict mask) or −2.5% (broad mask). The gradient-boosted PS row moves from −11.9% to −10.4% or −8.2%.
  - **F3: 37% of YNHHS ECGs are recorded on the index day (mean across trials; 15–62% per trial), and paper2 has no YNHHS sensitivity analysis that excludes them.** In the patients whose ECG was at least 1 day before index, the PS-CVD5 + ECG gain is 6.9% (0.4–13.4), compared with 8.8% in the full cohort. CLMBR-T is unchanged (11.3%).
- **SHOULD-FIX (reporting): the plasmode "% bias removed" figures are null-corrected, and paper2 Methods do not say so** (from the subagent review). Raw vs published: ECG 9.8% vs 11.3%; CLMBR-T 22.2% vs 22.6%.
- **Privacy.**
  - The paper2 manuscript, its supplement, Table 1, the figures and the gallery are clean.
  - No patient-level or restricted file is tracked in git, now or anywhere in main's history.
  - Older internal docs that are tracked publish two counts of 1–10 patients (BLOCKING for a public push) and several counts that can be recovered by subtraction.
  - `.gitignore` does not cover `*.docx`, `*.pkl`, `*.log`, `*.err` and similar patterns (§5).

## 2. Findings table (code)

Severity scale: **BLOCKING** changes a headline number or the primary conclusion. **SHOULD-FIX** changes a secondary number or claim, or is a methodological error with real impact. **MINOR** is cosmetic, has negligible impact, or concerns wording.

| # | Severity | File:line | Description | Verified how | Impact on paper2 |
|---|---|---|---|---|---|
| F1 | SHOULD-FIX | `scripts/v21/paper2_grid.py:357-363` (`load_F`); cells written at `:152-169`; per-trial SMDs in `scripts/v20/sens_primary32.py:183-195` | Cells with 1–10 matched pairs are masked only in the **retention** means (`RET … .mask(small_pairs(g))`). Their held-out SMDs remain in `SM` and enter every balance contrast. In PROTECT AF, 4 such hdPS200 cells carry 48–51 of the 54 items. Their per-trial mean \|SMD\| is 0.50–0.75, against a median of 0.08–0.10 across the other trials. log HR is NaN in all of them, so agreement is unaffected. Paper2 treats the PS-Flags cells for this trial as dropped, but these were not. | `check_tiny_cells.py` lists the cells and recomputes the 12 affected S32 contrasts without them. `recount_q_tiny.py` sets the SMDs of cells with 1–10 pairs to NaN, recomputes the affected rows (54- and 58-item p-values) and re-runs the BH balance family for S32 and S38. | **hdPS200: ECG+CLMBR vs base:** main −1.4% (−22.5, 13.3), q .65 → **+8.5% (2.0, 14.7), q .032**; 1:3 −1.4% → +6.5%, q .034. **hdPS200: ECG+CLMBR vs CLMBR:** main 1.8% → 7.9%, q .020. **Caliper 0.1, CLMBR vs ECG:** −12.0% → −3.9%. **q<.05 counts** (Results "Replication across configurations"): S32 98 → 104, main 18 → 20; S38 114 → 120. Figure 2B and eFigure 3 show the hdPS200 "both" bars with the contaminated values. All PS-CVD5 numbers are unchanged. |
| F2 | SHOULD-FIX (known: `docs/v2_planning/LESSONS_FROM_V1.md` §1) | `scripts/v21/paper2_grid.py:140`, `scripts/v20/sens_primary32.py:89` (`clin_ex`) | PS-Clinical masks only `mean_meds`, `mean_util` and `smd_obs_<T.phys>`. It does not mask near-duplicates of variables in its own PS: `pp_LVFUNC__ef` (echo EF ≈ LVEF) and `pp_LAB__egfr` (computed from creatinine, age and sex); also, more loosely, `pp_LAB__bun` and `pp_LVFUNC__lv_sys_grade`. This flatters PS-Clinical's balance. The paired masking carries this into the cross-rung contrasts. | `remask_heldout.py` re-masks from the saved per-trial SMDs, with no refitting. It also reproduces the published rows exactly before re-masking. | **P5+CLMBR vs clinical**, main: −4.9% (−11.2, 0.9) → −3.8% (−10.2, 2.1) strict, −2.5% (−8.7, 3.4) broad. GBM: −11.9%, P = .0013 → −10.4%, P = .0047 strict; −8.2%, P = .018 broad. With 1:3 matching, P = .047 → .18 or .42. **P5+ECG+CLMBR vs clinical**, main: −5.4% → −5.0% or −3.9%. **clinical: ECG / CLMBR vs base** (both arms share the leak): almost no change (−1.3 → −1.5 / −2.0; 0.8 → 0.8 / 1.3). The "nominally worse than PS-Clinical" wording survives but weakens, and the GBM q would need recomputation. The 58-item hdPS `mean_meds` leak (LESSONS §1) does not affect the 54-item primary endpoint. |
| F3 | SHOULD-FIX (design disclosure / sensitivity) | `scripts/select_cohort_ecgs.py:54-55` (`lag >= 0`; PI decision of 2026-09-23 in `docs/DECISIONS.md:2214`) | The ECG is the latest one in [index − 365 d, index], **index day included**. Index dates have no time of day, so an index-day ECG can come after the initiating order. Index-day share among analysed patients: mean 0.37, range 0.15–0.62 (PLATO 0.62, LAAOS III 0.61). CLMBR-T and every held-out item exclude the index day (`encode_comet_clmbr.py:75-77`, `build_physiology_panel_v2.py`, `build_core_baseline.py`), so the ECG is the only PS input that can contain post-initiation data. Paper2 states the window but reports the index-day exclusion only for MIMIC-IV. | `check_inputs.py` (index-day share per trial). `sens_no_index_day_ecg.py` re-runs the P5 main cells on the patients with an ECG ≥ 1 day before index (median 63% of each cohort kept; all cells ≥ 11 pairs). | On that subset: ECG 6.9% (0.4–13.4), 19/32, one-sided P = .033 (published 8.8%); CLMBR-T 11.3% (6.0–16.5); both 11.8% (3.5–19.2); permuted ECG −2.6% (−7.0 to 1.8). The ECG gain is smaller but persists. Report this as a sensitivity analysis, next to the MIMIC-IV one. |
| F4 | SHOULD-FIX (reporting) | `scripts/v20/g2b_simulation_ext.py:265-272` (used by `scripts/v21/paper2_plasmode.py`) | The plasmode "% bias removed" subtracts each arm's null-scenario error before taking the ratio. That is a reasonable choice, but paper2 Methods "Simulation" do not mention it; it is described only in paper 1's supplement. | Subagent: synthetic unit test of `pooled()`; re-ran the unmodified `paper2_plasmode.one()` for 4 cells × 2 replicates (480/480 rows identical). | Raw → published: P5 18.9 → 18.6; ECG over P5 9.8 → 11.3; CLMBR-T 22.2 → 22.6; both 28.3 → 29.5; permuted CLMBR-T −0.1 → 1.0; best arm 41.9 → 42.6; oracle 93.1 → 93.7; LVEF ECG vs CLMBR-T 15.8 vs 10.5 (published 15.2 vs 8.4). Conclusions unchanged. Fix: add one sentence to Methods. |
| F5 | MINOR | `scripts/v21/paper2_plasmode.py:95` | The R² loop does not apply the `excluded_cells.csv` filter: 108 cells (including ROCKET AF × LVEF) instead of 107. | Subagent recomputation. | LVEF R² CLMBR-T / ECG 0.192 / 0.219 vs 0.191 / 0.216 on the 107 cells. Rounded values unchanged. |
| F6 | MINOR | `scripts/v20/mimic_summary.py` (`boot_rr`) | The MIMIC-IV bootstrap CI depends on trial order (seed 0, 2,000 resamples, alphabetical pivot order). Separately, the window-fix CIs quoted in the paper2 Discussion use the 4,000-resample `relred_ci`, while Methods say 2,000 resamples. | Subagent. | 2.3–12.8 vs 2.3–12.6; hdPS window-fix CI −0.1 to 17.3 (4,000) vs −0.5 to 17.3 (2,000). Monte Carlo error only. |
| F7 | MINOR | `scripts/v18/v18_clmbr.py:231` | The HF term of PS-CVD5 is `hf_any_365` (I50, I11.0, I13.0, I13.2) except in 6 trials that lack it, which use `elx_chf`. In S32 these are LIFE and INSIGHT. Paper2 describes a single "heart failure" definition. | `check_inputs.py` (`hf_col`). | Definition differs by trial; not quantified. Disclose in eMethods. |
| F8 | MINOR | `scripts/v21/make_paper2_figures.py:352,374,760,1141-1166,452,283,291` | Figure labels: Figure 2 says "32 trials" where the PS-Flags rows use 31. The Figure 5D note "6 trial points beyond ±0.3" double counts (there are 3). eFigure 5 uses filled markers with different meanings in panels A and B. The Figure 3A title, and the Figure 1 hdPS box and "6 arms", are imprecise. | Subagent: rebuilt all 228 `check_values.json` entries identically and viewed the PNGs. | Display only. |
| F9 | MINOR | `scripts/v13_common.py:28` | `warnings.filterwarnings("ignore")` silences lbfgs non-convergence. | `check_engine.py`: n_iter ≤ 54 of 5,000 for every rung × arm design in RE-LY and PROTECT AF (including 625 to 689 columns for PS-Flags). | None found. Keep a convergence assertion. |

### Proposed fixes (text only; nothing applied)

F1. Treat cells with 1–10 matched pairs as failed for balance, as the PS-Flags cells already are:

```diff
 def load_F(R):
     F, SM, RET = {}, {}, {}
+    R = R.copy()
+    R.loc[small_pairs(R), [f"smd:{c}" for c in VN]] = np.nan  # 1-10 pairs: no balance information (v1 audit F1)
     for (rg, cfg, a), g in R.groupby(["rung", "config", "arm"]):
```

Then re-run `summarize`, `headline`, `labels`, `flagscv --stage summarize`, `retsens` and the figure script. Update the paper2 q-count sentence and Figure 2B / eFigure 3. Also state in Methods that cells with fewer than 11 pairs are excluded (it currently says this for PS-Flags only).

F2. Add near-duplicate masking for the clinical rung in `paper2_grid.task` (and `sens_primary32.task`), or apply it at summary time from the saved SMDs:

```diff
-    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
+    clin_ex = ({"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
+               | ({"pp_LVFUNC__ef"} if "lvef" in T.phys else set())
+               | ({"pp_LAB__egfr"} if "creatinine" in T.phys else set()))
```

Then report the strict mask as primary and the broad mask (adding BUN and the LV systolic grade) as a sensitivity analysis.

F3. Add the subset analysis (`sens_no_index_day_ecg.py`, or an equivalent row in `paper2_grid`) as a sensitivity analysis. In Methods, state the index-day share (15–62% per trial).

F4. Add one sentence to Methods "Simulation": "Bias was null-corrected by subtracting each arm's error in the corresponding null scenario (eMethods 7)."

## 3. What was checked and found correct

**PS fitting** (`v13_common.ps_logit`)
- Covariates are standardised (StandardScaler on the full design), fitted by L2 logistic regression with C = 1 for every rung, and predicted in-sample. The gradient-boosted PS uses 5-fold cross-fitting with fixed seeds.
- lbfgs converged in every design tested.
- The PS-CVD5 inputs (`hypertension_v11`, `t2d`, `cad_ihd`, AF, `hf_any_365`/`elx_chf`) use the window [index − 365, index − 1].
- No key was missing and no value was NaN in any of the 38 trials, so `nan_to_num` never zeroed real missing data (`check_inputs.py`).

**Matching** (`eval_longtail_balance.ps_greedy`, `v13_common.match`)
- Greedy 1:1 without replacement, anchored on the smaller arm, in descending order of the anchor-arm propensity.
- Caliper 0.2 × sqrt((var_t + var_c) / 2) of the PS logit. Ties are broken deterministically (stable sort).
- 1:3 matching runs 3 passes, with controls weighted 1/m per anchor.
- Verified on real data: no unit reused; max |Δlogit| / width ≤ 1.000; control weights sum to 1 per anchor.

**SMD** (`v16_engine.smd_components`)
- NaN-aware (weighted) means in the matched or weighted sample, divided by the pre-match pooled SD sqrt((s1² + s0²) / 2) with ddof 1.
- Matches an independent pandas implementation to 3e-14 across all 546 and 692 held-out components.
- Binary items use the same formula (equivalent to the pooled-proportion SD).

**Held-out items**
- Every item's window ends at index − 1: physiology panel [index − 365, index − 1]; observed labs and vitals [index − 90, index − 1] (365 days for BMI and LVEF).
- Echo items are masked before 2016-07-31.
- Items are paired within trial (observed in both arms).
- The 54 non-coded items are as described.

**Embeddings**
- The ECG and CLMBR-T PCs come from an unsupervised SVD within each trial cohort, with no outcome data.
- 0 duplicate ECG keys; 0 duplicate CLMBR-T rows; CLMBR-T index dates equal the cohort index dates in all 38 trials.
- The CLMBR-T cutoff is midnight of the index day.

**Permuted placebos**
- One fixed permutation (seed 424242) across the whole trial cohort, not within arm, which is correct for a placebo. The same permutation is used for the ECG and CLMBR-T.

**PS-Flags**
- Index day excluded; full history.
- Every pre-index condition source value is ICD-10-formatted, including before October 2015 (`check_flags_icd9.py`), so no ICD-9 history is mixed in or lost.

**Statistics**
- **Relative reduction:** a ratio of across-trial means, with a 4,000-resample percentile trial bootstrap (fixed seed). Reproduced exactly.
- **Sign-flip tests:** exact meet-in-the-middle; one- and two-sided versions are correct; reproduced.
- **BH-FDR:** 1,348 balance and 1,011 agreement p-values per set, recomputed exactly (subagent).
- **Benchmark permutation:** one-sided and two-sided versions are correct.
- **Label analyses:** permutation tests, families and paired masking are all reproduced (subagent).

**Cox model**
- lifelines with Efron ties, robust SE clustered on matched pairs or anchors. Weighted analyses use a robust sandwich SE.
- Follow-up starts the day after index; events during the index stay are excluded.
- Excluded outcome rows: ≤ 0.5% per trial.
- RCT benchmarks: orientation and CI level verified for all 56 `PUBLISHED` entries. PROTECT AF has an asymmetric credible interval, so the SE is approximate.

**Determinism**
- Two runs of each cell were identical.
- The engine reproduces `restricted_cells.parquet` exactly for RE-LY and PROTECT AF.

**MIMIC-IV and plasmode** (subagent)
- Every paper2 number re-derived.
- PS-CVD5 analog flags use prior admissions only.
- The 26 held-out items are all pre-index and none is in the PS.
- PEPTIC: pair-clustered Cox.
- Plasmode: complete-case confounder handling is identical across arms; seeds are independent of arm; no outcome leakage into the PCs; R² is cross-fitted without leakage.

**Figures and Results text** (subagent)
- About 120 numbers in paper2 Results match the CSVs. All 228 figure check values are reproduced.

## 4. Privacy findings (git-tracked files on main and the figure gallery)

The cell sizes themselves are not reproduced here. "1–10" stands in for each one.

| # | Severity | Location | Category | Description | Suggested fix |
|---|---|---|---|---|---|
| P1 | BLOCKING (before any public push) | `docs/COMET_OUTCOMES_HANDOFF.md:56`; `docs/COMET_OUTCOME_PROPOSAL_V1.json:19` | Small count | Number of COMET patients with a death date before index (1–10), stated directly and also recoverable from the line's other two counts. | Write "<11 (suppressed)" and drop the complementary exact counts. |
| P2 | BLOCKING (before any public push) | `docs/DECISIONS.md:1718-1719, 1819`; `docs/HANDOFF_HISTORY.md:2252-2253, 2353`; `tasks/todo.md:719`; `docs/REVIEW_COMET_REPRESENTATION_BALANCE.md:32` | Small count, and derivable from the x/y fractions | Number of carvedilol patients with only a birth record (1–10). | Replace with "<11", and drop the x/y pairs whose difference is 1–10. |
| P3 | SHOULD-FIX | `docs/v18/EMBEDDING_COMPARISON.md:205-206` | Derivable count | The minimum common-anchor percentages for hdPS200 + CLMBR-T and hdPS200 + CLMBR-T + ECG belong to PROTECT AF. Combined with its published smaller-arm size, they give a matched count of 1–10. These are the same cells as F1. | Show "<4% (suppressed)", or leave PROTECT AF out of the minimum. |
| P4 | SHOULD-FIX | `docs/v19/G3_ENRICHMENT.md:332-358` | Derivable count | For 24 trials, the per-trial n is 1–10 below the published cohort size. The gap is the patients excluded for having no usable outcome. | Round n, or add a note that exclusions are <11. |
| P5 | SHOULD-FIX | `docs/AUDIT_V15_2026_09_26.md:166` | Derivable count | The MIMIC-IV fallback-ECG fraction implies 1–10 patients. | "all but <11". |
| P6 | SHOULD-FIX | `docs/PROTOCOL_V1_1_AMENDMENT.md:30, 52` | Small count | Changes in cohort-builder membership of 1–10 patients. | "<11 patients". |
| P7 | SHOULD-FIX | `docs/PROTOCOL_V1_5_EXTERNAL.md:218` | Derivable count | The UKB ECG-file linkage fraction implies a gap of 1–10 files. UKB is out of scope. | ">99.9%". |
| P8 | SHOULD-FIX | `archive/2026-09-09-legacy-v1/handoff.md:86` | Identifier | An "example" MRN written as a placeholder that matches one real MRN in the OMOP person table (no attributes attached). | Replace with `MR#######`. |
| P9 | SHOULD-FIX | `.gitignore` | gitignore gap | `*.docx`, `*.pkl`, `*.tsv`, `*.feather`, `*.h5`, `*.xlsx`, `*.err`, `*.log`, `*.out`, `*.ipynb` and `audits/` are not ignored. A `git add -A` would commit the untracked PI Word draft `docs/paper/trial_emulate_manuscript_v2_RC.docx` and 8 empty `.err` files. `*.csv`, `*.parquet`, `*.npy`, `*.npz`, `restricted_*` and `*.pt` are ignored. | Add these patterns. |
| P10 | MINOR | `scripts/v15/v15_ukb_cvd.py:27, 160` | Exact date | The latest death date in the UKB extract (one person's date, used as a coverage cut-off). | Round to the month. |
| P11 | MINOR | `docs/v21/PAPER2_RESULTS.md:282`; eFigure 4B | Borderline | PS-Flags minimum ESS fraction 0.002. ESS is weighted, not a head count. | Optional: "<0.01". |
| P12 | MINOR | `docs/v19/G1_DESIGN_STEPS.md:346, 394, 412, 448, 460, 538`; `docs/v21/MIMIC_PAPER2.md:141` | Version or configuration differences of 1–10 | n differences between data versions or configurations; not a patient attribute. | Optional rounding. |

**Privacy coverage (clean)**
- 806 tracked files. No tabular, pickle, log, notebook, docx or `restricted_*` file is tracked now or anywhere in main's history.
- No cohort patient_key or person_id, and no MIMIC subject, hadm, stay or study ID, appears in any tracked file.
- No note or echo-report free text: section headers and keyword hits are schema or policy mentions only.
- paper2.md, supplement.md and table1_picot.md: every patient, pair and event count is ≥ 11; PROTECT AF is shown as "fewer than 11 matched pairs".
- The 0.3–5.7% truncation range and the "at most 5.9%" figure were checked against each trial's size: no implied count is 1–10.
- `docs/paper/figures_paper2/` and the gallery `claude-v21-paper2/figures_paper2.html` show trial-level aggregates only: no per-patient points and no KM at-risk tables. PDFs were not text-scanned because `pdftotext` is not installed.
- Not scanned: paper.md, the `.docx` files and the `r2` branch.

## 5. Files written by this audit

- `docs/v1_audit/CODE_PRIVACY_REVIEW.md` (this file).
- In `scripts/v1_audit/code/`:
  - core checks: `check_inputs.py`, `check_engine.py`, `check_flags_icd9.py`, `remask_heldout.py`, `check_tiny_cells.py`, `recount_q_tiny.py`, `sens_no_index_day_ecg.py`;
  - figure and label checks (subagent): `figs_*.py`, `labels_*.py`;
  - plasmode and MIMIC-IV checks (subagent): `plasmode_rerun_newarms.py`, `mimic_flags_demo_check.py`.
- In `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/code/`:
  - `inputs.csv`, `remask.csv`, `tiny_cells.csv`, `sensitivity_tinyfix.csv`;
  - `sens_no_index_day_ecg.csv` and `restricted_sens_no_index_day_ecg.parquet`;
  - `check_engine_protect-af.txt`, `plasmode_rerun_newarms.csv`, `mimic_flags_demo_check.csv`;
  - `privacy/` (scratch hit lists).
