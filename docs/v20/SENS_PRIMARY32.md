# v2.0 sensitivity and robustness analyses for the primary 32-trial set (2026-10-01)

**Exploratory.**
- Plan: [SENS_PRIMARY32_PLAN.md](SENS_PRIMARY32_PLAN.md) (commit d262e91, before results).
- Code: `scripts/v20/sens_primary32.py`.
- Aggregates: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-sens-primary32/`. Files: `sensitivity.csv`, `pcsweep.csv`, `outpatient.csv`, `ci.csv`, `gate.csv`, `cells.csv` (counts 1–10 suppressed), `restricted_cells.parquet`.
- Sets: S32 = 38 emulated minus 6 Limited (primary); S38 = all 38.
- Full cohort only. Split-sample halves were dropped per PI decision.

## Verdict (plain language)

1. **The balance finding is robust.** With the demographic PS, adding the ECG improves held-out balance under every matching or weighting choice: caliper 0.1, 1:3 matching, IPTW and overlap weighting.
   - The relative reduction in mean |SMD| is 11.2–14.4%, all with CIs above 0. The permuted ECG gives about 0 in every configuration.
   - It also survives comparator clustering (P = .033), leave-one-trial-out (max P = .004) and FDR (q = .007).
   - **Exception:** with a gradient-boosted PS the gain is smaller (+1.3 points, P = .21; relative reduction 6.6%, 1.5–11.2). The tree-based PS seems to use the 32 continuous PCs less effectively.
2. **The gain needs about 16 or more ECG components.** It rises from 6.8% with 4 PCs to 11–15% with 32–256 PCs and plateaus beyond 32. The permuted ECG stays near 0 at every dimension.
3. **Closer agreement with the RCTs is robust to matching choices but is not trial-specific.**
   - |Δ log HR| falls with the ECG in every configuration except the gradient-boosted PS (P = .09). It survives comparator clustering (P = .026) and leave-one-out (max P = .016), and is borderline after FDR (q = .051).
   - The benchmark shuffle is never significant (P = .26–.85). So the gain is generic attenuation, not a correction specific to each trial, as before.
4. **Outpatient initiators, primary set (23 trials):** the balance gain is +2.2 points (12/23 trials; P = .083; relative reduction 7.7%, 2.6–12.5). It is smaller than for all initiators in the same trials (+4.9 points, P = .008), and the change in percentage points is not significant.
5. **Regenerated CIs mostly confirm the paper.** Two need correcting:
   - **LV systolic function:** 14.6% with CI **−0.5% to 27.3%**, which crosses 0. The paper has 0.1–27.2.
   - **High-dimensional PS:** **7.6% (1.9–12.8)** with paired variable sets. The paper has 8.1% (2.3–12.9).

## Reproduction gate

All main-config cells reproduce `claude-v18-embed-compare` (half = full) **exactly**, with maximum |Δ| = 0 across loghr, se, n, n_pairs and all 58 SMDs. This covers P1, P5, hdPS200 and clinical × base, ECG and shufECG, in 38 trials (`gate.csv`). See deviation 2 for one first-pass fix.

## 1. Matching and estimation sensitivity (demographic PS)

Endpoints: % of the 58 held-out characteristics with |SMD| < 0.1, and the relative reduction in mean |SMD| (95% CI). P values are one-sided exact sign-flip.

**S32 (primary):**

| Configuration | % \|SMD\|<0.1: PS → + ECG | Trials better | P | Rel. reduction (95% CI) | Permuted ECG rel. red. | \|Δ log HR\|: PS → + ECG | Closer | P | Bench. shuffle P | Std-diff agr.: PS → + ECG |
|---|---|---|---|---|---|---|---|---|---|---|
| Main (1:1, caliper 0.2) | 49.8 → 55.0 | 22/32 | .002 | 11.4 (6.3–16.0) | −0.7 | 0.251 → 0.205 | 20/32 | .008 | .26 | 62.5 → 84.4% |
| Caliper 0.1 | 50.4 → 55.6 | 20/32 | .003 | 12.2 (6.9–17.1) | −0.8 | 0.250 → 0.208 | 21/32 | .016 | .31 | 65.6 → 84.4% |
| 1:3 matching | 51.0 → 57.8 | 23/32 | <.001 | 13.6 (9.8–17.5) | −0.4 | 0.242 → 0.205 | 19/32 | .016 | .53 | 62.5 → 68.8% |
| IPTW (stabilised, trimmed) | 51.3 → 55.9 | 20/32 | <.001 | 11.2 (7.2–15.2) | −0.7 | 0.250 → 0.218 | 21/32 | .043 | .85 | 62.5 → 75.0% |
| Overlap weighting | 51.6 → 59.0 | 28/32 | <.001 | 14.4 (10.6–18.2) | −0.7 | 0.246 → 0.204 | 24/32 | .002 | .39 | 65.6 → 75.0% |
| Gradient-boosted PS (1:1) | 50.1 → 51.4 | 17/32 | .21 | 6.6 (1.5–11.2) | −1.3 | 0.261 → 0.238 | 20/32 | .09 | .62 | 68.8 → 78.1% |

**S38 (sensitivity):** relative reductions are 12.6% (main), 13.6% (caliper 0.1), 14.0% (1:3), 11.5% (IPTW), 15.0% (overlap) and 7.3% (gradient-boosted); all CIs exclude 0. |Δ| P values are .001–.015, except .09 for the gradient-boosted PS.

**PS ladder, main configuration** (S32; relative reduction, then |Δ log HR|):

| PS | % \|SMD\|<0.1 | P | Rel. reduction (95% CI) | Permuted | \|Δ\| PS → + ECG | P |
|---|---|---|---|---|---|---|
| Demographic | 49.8 → 55.0 | .002 | 11.4 (6.3–16.0) | −0.7 | 0.251 → 0.205 | .008 |
| Five-diagnosis | 53.6 → 57.6 | .003 | 9.0 (4.8–13.3) | 1.1 | 0.226 → 0.196 | .049 |
| High-dimensional | 58.9 → 63.8 | <.001 | 7.6 (1.9–12.8) | 2.8 | 0.181 → 0.167 | .20 |
| Clinical | 61.9 → 62.2 | .41 | −1.2 (−6.5 to 3.9) | −3.4 | 0.158 → 0.155 | .42 |

## 2. ECG dimension (demographic PS, main configuration)

| PCs | S32 % \|SMD\|<0.1 (PS 49.8) | Trials better | P | Rel. reduction (95% CI) | Permuted rel. red. | \|Δ\| (PS 0.251) | P |
|---|---|---|---|---|---|---|---|
| 4 | 52.6 | 18/32 | .030 | 6.8 (2.7–10.7) | 0.8 | 0.238 | .24 |
| 8 | 53.6 | 20/32 | .011 | 8.8 (4.3–13.0) | −3.2 | 0.243 | .34 |
| 16 | 53.2 | 20/32 | .027 | 10.5 (5.6–15.0) | −1.6 | 0.218 | .030 |
| **32** | **55.0** | 22/32 | .002 | **11.4 (6.3–16.0)** | −0.7 | 0.205 | .008 |
| 64 | 56.7 | 25/32 | <.001 | 12.0 (4.9–18.0) | −2.2 | 0.190 | .002 |
| 128 | 57.2 | 27/32 | <.001 | 15.3 (10.2–19.9) | −1.7 | 0.201 | .008 |
| 256 | 57.7 | 23/32 | <.001 | 13.8 (7.3–19.5) | −3.3 | 0.200 | .022 |

The S38 pattern is the same: 6.6% at 4 PCs and 16.5% at 128 PCs.

## 3. Robustness of the primary analyses (main configuration)

ECG vs PS alone. Columns are sign-flip P, comparator-cluster P (14 clusters), leave-one-out max P, and BH q within the family (main configuration: set × rung × contrast).

| Set | PS | Balance % \|SMD\|<0.1: P / cluster / LOO / q | Mean \|SMD\|: P / cluster / LOO / q | \|Δ log HR\|: P / cluster / LOO / q | Bench. shuffle P (q) |
|---|---|---|---|---|---|
| S32 | Demographic | .002 / .033 / .004 / .007 | <.001 / .004 / <.001 / <.001 | .008 / .026 / .016 / .051 | .26 (.40) |
| S32 | Five-diagnosis | .003 / .016 / .006 / .009 | <.001 / .002 / <.001 / <.001 | .049 / .20 / .087 / .14 | .70 (.70) |
| S32 | High-dimensional | <.001 / .001 / <.001 / .003 | .007 / <.001 / .014 / .017 | .20 / .27 / .29 / .39 | .11 (.40) |
| S32 | Clinical | .41 / .33 / .62 / .50 | .67 / .52 / .78 / .77 | .42 / .25 / .57 / .55 | .62 (.70) |
| S38 | Demographic | <.001 / .017 / <.001 / .003 | <.001 / .001 / <.001 / <.001 | .002 / .021 / .004 / .017 | .22 (.40) |

- **ECG vs permuted ECG (S32, demographic PS):** balance P = .001 (cluster .002, LOO .002); |Δ| P = .002 (cluster .011, LOO .003); benchmark shuffle P = .047. That shuffle p-value isn't significant after FDR (q = .38).
- **Permuted ECG vs PS alone (two-sided):** balance P = .98. For |Δ| the P is .054, because the placebo moves estimates slightly *away* from the RCTs (0.251 → 0.280).

## 4. Outpatient initiators

Source: v19 `SENS_OUTPATIENT` cells. OUT-29 is the a priori outpatient-RCT set.

| Set | PS | Population | % \|SMD\|<0.1: PS → + ECG | Trials better | P (cluster / LOO) | Rel. reduction (95% CI) |
|---|---|---|---|---|---|---|
| OUT-29 ∩ S32 (23) | Demographic | Outpatient | 47.1 → 49.3 (+2.2) | 12/23 | .083 (.049 / .16) | 7.7 (2.6–12.5) |
| OUT-29 ∩ S32 (23) | Demographic | All initiators, same trials | 52.1 → 57.0 (+4.9) | 16/23 | .008 | 10.1 (3.5–15.8) |
| OUT-29 ∩ S32 (23) | Five-diagnosis | Outpatient | 49.6 → 51.7 (+2.1) | 12/23 | .12 | 6.4 (−0.5 to 12.5) |
| OUT-29 (29) | Demographic | Outpatient | 51.7 → 54.0 (+2.3) | 17/29 | .035 (.008 / .068) | 7.9 (3.4–11.9) |
| OUT-29 (29) | Demographic | All initiators, same trials | 53.7 → 59.4 (+5.7) | 22/29 | .001 | 12.0 (6.2–16.9) |

The permuted ECG gives about 0 in every row.

## 5. Regenerated bootstrap CIs vs the current paper

Method: percentile CI, 4,000 resamples of trials, ratio of across-trial means, fresh `default_rng(20261001)` for each CI. Balance is computed on the variables observed in **both** arms of each trial (paired).

| Quantity (S32, demographic PS unless stated) | Paper | Regenerated | Note |
|---|---|---|---|
| All 58 characteristics | 11.4 (6.3–15.9) | 11.4 (6.3–16.0) | |
| LV structure | 24.6 (14.6–32.5) | 24.6 (15.0–32.1) | |
| Diastolic / LA | 17.7 (8.1–26.2) | 17.7 (8.0–26.4) | |
| **LV systolic function** | 14.6 (0.1–27.2) | **14.6 (−0.5 to 27.3)** | **CI crosses 0; correct the paper** |
| Vitals & core labs | 13.9 | 13.9 (6.8–20.2) | |
| RV / pulmonary | 13.0 | 13.0 (3.0–22.1) | |
| Valves / aorta | 1.3 | 1.3 (−12.5 to 12.7) | |
| Other labs | −0.9 | −0.9 (−10.5 to 7.0) | |
| Coded record | 12.8 | 12.8 (7.3–17.7) | |
| Five-diagnosis PS | 9.0 (4.9–13.2) | 9.0 (4.8–13.3) | |
| **High-dimensional PS** | 8.1 (2.3–12.9) | **7.6 (1.9–12.8)** | The paper's value masked only variables missing under PS alone. The paired mask is the correct comparison |
| Clinical PS | −1.1 | −1.2 (−6.5 to 3.9) | Same reason |
| S38 all 58 | 12.6 (8.0–16.7) | 12.6 (7.8–16.6) | |
| MIMIC-IV, demographic PS (7 trials) | 10.3 (6.4–14.5) | 10.3 (6.4–14.5) | |
| MIMIC-IV, excluding index-day ECGs | 14.5 (9.7–19.7) | 14.5 (9.5–19.8) | |
| MIMIC-IV, high-dimensional PS | 7.5 | 7.5 (−0.4 to 16.2) | |
| MIMIC-IV, clinical-lite PS | 1.2 | 1.2 (−9.1 to 11.8) | |

## Deviations (logged)

1. **Split-sample halves dropped** per PI decision, 2026-10-01. Robustness is comparator clustering, leave-one-out and BH-FDR only.
2. **Gate fix.**
   - In the first pass, P5 base cells differed from v18 in ALLHAT and VALUE: |Δ log HR| 0.0024, with the same number of pairs.
   - Cause: the PS design matrices were passed as non-row-indexed arrays. v18 uses `b5[r]`, `T.X_dx[r]` and `T.X_core[r]`, so BLAS summation order differed and flipped greedy-matching ties.
   - Fix: the indexing was made identical to v18 and the **whole grid was rerun**. The gate then reproduced exactly (max |Δ| = 0).
3. **Paired variable sets.** Balance comparisons use, per trial, the 58-panel variables observed in both arms of the comparison. Earlier deck and figure code masked only variables missing under PS alone. This moves the high-dimensional PS estimate from 8.1% to 7.6%; the demographic PS values are unchanged.
4. **Family definitions.** BH-FDR families follow the plan: balance-primary (lt01), balance-secondary (mean |SMD|), emulation (|Δ|; consistency) and trial-specific (benchmark shuffle). They are taken within the main configuration (`q_*_main`) and across all configurations (`q_*_all`). The audit helper's q = .084 for |Δ| used a different family; here q = .051.
5. **Not computed:** the treatment-classifier C-statistic (cstat = None, which saves time), and agreement metrics for the weighting estimators, where pairs are undefined.
6. **MIMIC-IV CIs** are computed from the per-trial arm files (`results/<trial>_arms.csv`), not the rounded summary JSON.
