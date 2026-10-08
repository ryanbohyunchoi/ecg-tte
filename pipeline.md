# pipeline.md: the settled TRACE-ECG analysis pipeline (covariate balance and trial emulation)

Written **2026-10-08**. This is the single reference for the design we settled on. Every element is marked **LOCKED** or **PENDING** (open decision or running analysis).
- **Changing a LOCKED item:** it becomes a logged deviation (§9).
- **When everything is LOCKED:** commit this file as the methods lock. From then on, figures and the manuscript are generated only from it.

**Manuscript:** this design extends paper2 (PS-CVD5 primary, ECG + CLMBR-T, PS-Flags as the CLMBR-T check). Paper 1 (`docs/paper/paper.md`, PS-Demo primary, ECG only) is the earlier version.

**Disclosure:** PS-CVD5 as primary was first proposed on 2026-10-07 (paper2), before the R2 and PS-10 results. The switch from paper 1's PS-Demo is still a post hoc change and must be stated in the Methods.

---

## 1. Data

| Element | Choice | Status |
|---|---|---|
| Source | YNHHS EHR mapped to OMOP (gold), structured echo reports, raw 12-lead ECGs, state death records; index dates 2011–2024 | LOCKED |
| External replication | MIMIC-IV 3.1 (ECG only; no CLMBR-T, no echo) | LOCKED |
| Clinical notes | Not used in this paper (R2 only, branch `r2`) | LOCKED |

## 2. Trials

| Step | Choice | Status | Source |
|---|---|---|---|
| Stage 1: feasibility | 99 candidates → 38 emulated (comparator, ascertainable endpoint, identifiable strategies, sample size) | LOCKED (unchanged) | eMethods 3 |
| Stage 2: emulation quality | **Framework v2.0**: 10 items, points and tiers; Limited is excluded | **PENDING:** audit running; framework-design decisions open | `docs/emulation_quality_v2/` |
| Analysed set | **29 trials** (adjudicated). Leaving vs paper 1: CABANA, ACTIVE W, AMPLIFY, EMPEROR-Preserved, LEADER, SUSTAIN-6, CANVAS. Entering: ALLHAT, ASCOT-BPLA, VALUE, ONTARGET | **PENDING** (audit; 10 tier-changing provisional scores; the 5 major-problem trials that stay at Moderate) | `ADJUDICATION.md`, `quality_v2_final.json` |
| Sensitivity sets | Excellent + Good (8); all 38; paper 1's 32 | LOCKED | |
| Cohort fixes | Exclusion-type fixes from the criteria check: washouts, age bound, etc. Primary as built or with fixes? | **PENDING** | `docs/v1_criteria_check/TRIAL_CRITERIA_CHECK.md` |
| Trial labels | Physiologic yes/no and domains (two blind LLM runs); descriptive only | LOCKED (clinician review pending) | `docs/v21/TRIAL_LABELS.json` |

## 3. Representations

| Representation | Definition | Status |
|---|---|---|
| **ECG** | BCL self-supervised signal encoder, 256-d → **32 PCs within each trial**. Latest 12-lead ECG in [index − 365 d, index], **index day included** (user decision 2026-10-08; share of index-day ECGs disclosed per trial) | LOCKED |
| **CLMBR-T** | CLMBR-T-base (frozen), code-only coded EHR (diagnoses, drugs, procedures, measurement codes without values, visits), last 4,096 tokens, **index day excluded** → 768-d → **64 PCs within each trial**; 32 PCs as a sensitivity. **Never call it "unstructured."** | LOCKED |
| **Placebos** | Permuted ECG and permuted CLMBR-T (embeddings shuffled between patients within each trial; same dimension) | LOCKED |

## 4. Propensity scores

**Model:** L2-penalised logistic regression on standardised covariates, **fixed C = 1 for every specification** (user decision 2026-10-08; rationale in §8).

| Level | Covariates | Role | Status |
|---|---|---|---|
| PS-Demo | age, sex, index year | ladder | LOCKED |
| **PS-CVD5** | PS-Demo + hypertension, T2D, CAD, AF, HF | **PRIMARY** | LOCKED |
| hdPS | PS-Demo + 9–13 investigator diagnoses + top 200 hdPS code levels (treatment-only ranking, random half of code features, exposure drugs excluded) | ladder | LOCKED |
| **PS-Clinical (no LVEF)** | the clinical PS **without LVEF**: vitals, core labs, diagnoses, medication orders, utilisation. **No PS contains any echo measurement**. Missing values: **5-draw multiple imputation** (re-imputed without LVEF); per-item \|SMD\| averaged across draws, HRs combined by Rubin's rules | ladder (richest) | LOCKED (MI run pending on spec-v2 cohorts). "Was measured" flags: not added |
| CVD10 (PS-10) | PS-Demo + 10 fixed diagnoses: HTN, T2D, CAD/MI, AF, HF, CKD, COPD/asthma, PAD, stroke/TIA, valve disease (no obesity) | **main ladder, as a comparison** (between PS-CVD5 and hdPS); not the main love plot | LOCKED |
| PS-Flags | PS-Demo + yes/no ICD-10 3-character diagnosis flags, full pre-index history, ≥1% prevalence | **supplement** (the CLMBR-T vs diagnosis-flag test) | LOCKED |

**Added to each level:** none (base), + ECG, + CLMBR-T, + ECG + CLMBR-T, + permuted ECG, + permuted CLMBR-T.

**Supplement PS variants:**
- cross-validated penalty (R2 result for PS-CVD5 + ECG: 4.7%);
- gradient-boosted PS;
- LEGEND-style large-scale L1 PS (R2, branch `r2`).

## 5. Matching / weighting

| Method | Role |
|---|---|
| **1:1 greedy nearest neighbour on the PS logit, caliper 0.2 SD, without replacement** | **PRIMARY** |
| Caliper 0.1; 1:3 matching; overlap weighting; IPTW; gradient-boosted PS (1:1, caliper 0.2) | sensitivity |
| Cells with <11 matched pairs | treated as failed (dropped) |

Status: LOCKED.

## 6. Covariate balance (held-out characteristics)

**Held-out** means the characteristic is not an input of the PS being evaluated. Balance is measured after matching as |SMD|. Panels:

| Panel | Content | Role | Status |
|---|---|---|---|
| **54 non-coded items, leakage-corrected** | 9 vitals and core labs (incl. observed LVEF), 10 other labs (incl. NT-proBNP, eGFR), **35 echo measures** (LV structure 7, LV function 4, diastolic/LA 8, RV/pulmonary 7, valves/aorta 9) | **PRIMARY** (main love plot) | LOCKED |
| 58 items | the 54 + 4 coded-record summaries (medications, healthcare use, held-out codes, prognostic score) | secondary (supplement love plot). The coded items are masked for CLMBR-T, hdPS and others by the leakage map | LOCKED |
| Expanded panel (~330 items per trial; 245–336 by PS) | broad pre-index characteristics from published PS / TTE covariate sets; mostly code features; **not leakage-masked** (CLMBR-T looks inflated there) | **supplement only** | LOCKED |

**Leakage-corrected masking.** A cell's mask = the PS level's mask ∪ the added representation's mask (placebos take the real arm's mask):

| PS level / arm | Masked on the 54 items | Masked on the 58 items (additionally) |
|---|---|---|
| PS-Demo, CVD10 | none | `B_mean`, prognostic score |
| PS-CVD5, PS-Flags | none | `B_mean`, prognostic score |
| hdPS | none | all 4 coded items |
| **PS-Clinical (no LVEF)** | observed vitals/labs that are PS inputs (8 `smd_obs_*`; **not** LVEF) + **eGFR** (derived from creatinine, age, sex) | all 4 coded items |
| + CLMBR-T (any level) | none | all 4 coded items |

**Rules:**
- mask any held-out item that is the same quantity as, derived from, or the same code family as a PS input;
- also mask any item with pooled |ρ| ≥ 0.80 with a PS input;
- soft proxies (0.50 ≤ |ρ| < 0.80, e.g. BUN, LVESVi, GLS vs LVEF) are not masked; a "clean + soft" sensitivity masks them.

Sources: `docs/v1_audit/DEFECT_IMPACT.md` §1; `docs/v1_ps10/PS10.md`; `docs/v2_planning/LESSONS_FROM_V1.md`.

**Endpoints:**
- **Primary:** relative reduction in mean |SMD| = 1 − (across-trial mean with the representation / without), with a 95% CI from 4,000 bootstrap resamples of trials (seed 20261001).
- **Secondary:** % of items with |SMD| < 0.1; trials improved; per-domain relative reductions.
- Items are used only where observed in both compared cells.

**Tests:**
- exact sign-flip permutation across trials: one-sided for a representation vs its base or placebo; two-sided for head-to-heads (e.g. CLMBR-T vs ECG, PS-Demo + CLMBR-T vs PS-Flags) and for placebos vs base;
- robustness: comparator-cluster sign-flip and leave-one-trial-out;
- BH-FDR within families (balance and agreement), across contrasts × configurations.

**Love plots:**
- **Main figure:** the 54 leakage-corrected items, PS-CVD5 base vs + ECG vs + CLMBR-T vs + both (median across analysed trials), grouped by domain. The ladder figure includes CVD10 as a comparison.
- **Supplement:** the 58-item love plot (with permuted placebos) and the expanded-panel figure.
- PS-Flags appears only in supplement figures; CVD10 appears in the ladder, not the main love plot.

## 7. Trial emulation (agreement with RCTs)

| Element | Choice | Status |
|---|---|---|
| Effect estimate | Cox model in the matched cohort, robust variance clustered on matched pairs; trial-matched horizon | LOCKED |
| Metrics | \|Δ log HR\| vs RCT (paired, trials closer, sign-flip P); Pearson r; estimate agreement; standardized-difference agreement (RCT-DUPLICATE) | LOCKED |
| **Trial-specificity test** | **Benchmark-permutation test** (RCT results reassigned across trials, 20,000 draws). It must accompany every agreement claim, because estimates shrinking toward the null improve the other metrics without trial-specific correction | LOCKED |
| Framing | Agreement is secondary; balance is primary. No agreement claim without the permutation result | LOCKED |
| Exploratory note | CVD10 + ECG showed a trial-specific signal (permutation P = .003). Post hoc; report as exploratory only | LOCKED |

## 8. Supporting analyses

| Analysis | Design | Status |
|---|---|---|
| Plasmode | Withheld physiological confounder (LVEF, NT-proBNP, BMI, eGFR), clinically oriented, treatment driven by the confounder; arms PS-CVD5 ± ECG ± CLMBR-T, CLMBR-T alone, permuted CLMBR-T | exists (v21, `docs/v21/PLASMODE_PAPER2.md`); **re-check on the final trial set: PENDING** |
| MIMIC-IV | PS-CVD5 analog (prior-admission diagnoses) ± ECG ± permuted ECG; 7 cardiovascular trials + PEPTIC negative control | exists (`docs/v21/MIMIC_PAPER2.md`); LOCKED |
| Representation alone | CLMBR-T-only or ECG-only PS vs PS-CVD5 / hdPS / PS-Flags / PS-Clinical | exists (R2 X1, branch `r2`); supplement; LOCKED |
| Domain / label / quality subsets | Descriptive | LOCKED |

**Why a fixed penalty:**
- C = 1 was the original design;
- it keeps comparisons covariate-only;
- the PS goal is balance, not prediction;
- cross-validated log loss, when ECG columns are added, also shrinks the base covariates (median C 0.032 → 0.010);
- the cross-validated result and the placebo contrast (~8% under both) are reported as sensitivities.

## 9. Deviations log (append only)

| Date | Change | Reason |
|---|---|---|
| 2026-10-08 | Primary PS-Demo → PS-CVD5; CLMBR-T added | User decision; PS-CVD5 first proposed 2026-10-07 (paper2) |
| 2026-10-08 | LVEF removed from PS-Clinical | Echo is the test domain; no PS uses echo (user decision) |
| 2026-10-08 | Leakage-corrected masking primary | v1 audit found near-duplicate leaks (echo EF ≈ LVEF; eGFR from creatinine) |
| 2026-10-08 | Emulation-quality framework v2.0 replaces the v19 tiers | Blind re-audit and data check found cohort-specification defects not covered by v19 |
| 2026-10-08 | PS-Flags to the supplement; CVD10 in the main ladder as a comparison (not the main love plot) | User decision |
| 2026-10-08 | PS-Clinical: 5-draw multiple imputation instead of a single draw | Single-draw noise of a few points found in the no-LVEF re-run (user decision) |
| 2026-10-08 | Spec-v2 cohorts: apply exclusion-type fixes (numeric entry bounds, age bounds, class washouts, LAAOS III AF before admission, LIFE definite LVH, COMET EF ≤35%, VALIANT LV dysfunction/HF) and outcome fixes (AMPLIFY, LODESTAR, PROVE IT) instead of penalising them in the quality scores; PCs recomputed within fixed cohorts. Rebuild-only defects (CABANA, TRANSFORM-HF) stay scored | User decision after the quality audit (AUDIT_QUALITY_V2.md B1); run in progress (`docs/v2_cohorts/`) |

## 10. Open decisions (needed before the lock)

1. **Trial set:**
   - the audit result;
   - whether the 5 major-problem trials (LAAOS III, LIFE, COMET, TRANSFORM-HF, VALIANT) stay at Moderate or a tier rule is tightened;
   - whether ALLHAT, ASCOT-BPLA, VALUE and ONTARGET re-enter;
   - the framework clarifications C1–C10.
2. **Cohort fixes:** use exclusion-type fixes in the primary analysis, or only as a sensitivity.
3. **PS-Clinical (no LVEF):** review the results; decide whether to add the "was measured" flags.
4. ~~C = 100 sensitivity~~: not run (user decision 2026-10-08).
5. **Manuscript file:** update `paper2.md`, or start a new file.
6. **Clinician review** of the quality adjudication and the trial labels.

## 11. After the lock

1. Re-run all summaries on the locked design (from existing cells and the new rungs).
2. Regenerate the figures (adapt `scripts/v21/make_paper2_figures.py`) and the balance explorer.
3. Update the manuscript, including the 23 paper2 text fixes from `docs/v1_audit/CLAIMS_RECHECK.md`.
4. Run a claim-by-claim audit of the manuscript and figures.
