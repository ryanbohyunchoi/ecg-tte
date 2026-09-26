# v1.6 sweep audit (S1, S3, S4; S2 pending) — 2026-09-26

This is an independent, skeptical audit of the exploratory v1.6 sweeps (`docs/V16_SWEEP_PLAN.md`). Code is in `scripts/v16/audit_v16.py`
(modes `a`, `b`, `c`, `d`). It uses its own sign-flip, BH and pairing code and does not call the sweep summary functions.
Aggregates are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-audit/` (`check*.csv`, `partb_*.csv`).
The audit reports aggregates only; it contains no patient-level rows and no patient counts of 1–10.
Trial counts (k of 18) are not patient counts.

Terms used below:
- **d**: the mean over trials of (ECG arm − comparator). Negative means ECG is better.
- **p**: exact two-sided sign-flip p over trials.

**S2 (`docs/v16/S2_DROPOUT.md`) had not been written when this audit finished.** Its `results.csv` exists. It enters only the
global-FDR sensitivity analysis (seed 0), so S2 is marked pending.

## Verdict table

| # | Check | Verdict | Fix / consequence |
|---|---|---|---|
| 1 | Independent recomputation of d, k/n, p | **PASS** | S1, S3 and S4 recompute exactly (max \|Δd\| 2e-16, max \|Δp\| 6e-17, k/n identical in all 104 cell × metric checks). Minor: the demo-base arm differs slightly between S4 and S1/S3 (max \|Δlog HR\| 0.006, same pair counts; floating-point tie-breaking in greedy matching on a 3-covariate PS). No correction needed. |
| 2 | Held-out leakage / prognostic score | **PASS with minor concerns** | prog_full is fitted outside the cohort (PASS). Pool-B "held-out" codes include dx_E11/E78/I10/I25/I48, which are near-copies of PS flags in sparse/min-7/hdPS. Clinical keeps echo EF and eGFR/BUN in `mean_smd_ho` although lvef and creatinine are in its PS, and obesity is in the new-covariate set although BMI is in its PS. Say so in the synthesis. The effect is expected to be negligible (B_mean is 1 of 58 variables and averages several hundred features) and it applies equally to the base and ECG arms. |
| 3 | Placebo validity | **PASS** | shufECG is a permutation of ECG rows, same dimension, independent of treatment. noise is seeded and of equal dimension. Pair counts are equal to base (median ratio ≥ 0.997). The placebo − base null is centred near 0, slightly on the worse side. |
| 4 | Split halves | **PASS** (with caveat) | The halves are disjoint, cover the cohort and are stratified on treatment. The seed (16060 + trial index) does not depend on outcomes, and pairs(A)+pairs(B) ≈ full. Caveat: across cells, half-level d correlates only weakly between A and B for \|Δlog HR\| (r = 0.39) and C-statistic (r = 0.26). "Replicated in both halves" is a low-power, noisy criterion, and the halves come from the same 18 trials. |
| 5 | Regression to the benchmark in the S4 confounding meta-regression | **FAIL** (for the claim) | With RCT HRs shuffled across trials, the slope is just as negative as observed (demo \|Δ\|: observed −0.062/SD, null median −0.057, p = 0.33; sparse z²: −2.6 vs −5.0, p = 0.89). Using a no-RCT moderator \|unadj − clinical PS\| also gives no benchmark-specific slope (p_one-sided 0.68–0.94). **Remove S4 finding 3 as an effect modifier.** Its slope is fully explained by the moderator and the outcome sharing the RCT benchmark and by generic shrinkage toward the null (see check 11). |
| 6 | Global multiplicity | **CONCERN** | Global within-metric BH over 85 de-duplicated S1+S3+S4 cells: \|Δlog HR\| **1/85** (S3 demo 64 PCs, q = 0.049); z² 36/85; mean \|SMD\| 62/85; C-statistic 65/85. A single BH pooled over all metrics is misleadingly lenient (12 \|Δ\| cells pass only because hundreds of tiny balance p-values are pooled in). The effective number of independent cells is ≤ 15–21 per metric (bounded by the 17–18 trials; median pairwise r 0.36–0.68). |
| 7 | Trial-level dependence | **CONCERN** | Rosters overlap heavily (person_id, % of the smaller roster): ARISTOTLE–RELY 82%, ROCKET-AF–RELY 82%, EMPEROR–EMPA-REG 66%, ALLHAT–VALUE 63%, and cross-question overlaps up to 49%. Leave-one-trial-out: demo \|Δ\| p ranges 0.007–0.066 and 7/18 drops lose p < 0.05. With 10 comparator clusters: demo \|Δ\| p = 0.24, demo z² p = 0.084, sparse mean \|SMD\| p = 0.105 (all lost). Sparse z² p = 0.025, sparse C-statistic p = 0.031, and demo/min-7/hdPS200 mean \|SMD\| (p ≤ 0.004) survive. |
| 8 | SMD definition and C-statistic sample-size artifact | **PASS** | The SMD denominator is the pooled SD of the analysed pre-match rows (confirmed in `smd_components`). ECG does not shrink the matched set (median pairs ratio 0.9998). Thinning base matched sets to the ECG pair count changes the C-statistic by −0.0003 (sparse) and +0.0009 (demo), p = 0.78/0.39. Against the thinned base, the ECG C-statistic gains remain (−0.013, p = 0.011; −0.019, p = 0.0008). |
| 9 | Markdown claims | **CONCERN** | Several "agreement with RCT", "replicates" and "effect modifier" statements overstate the evidence; see the list below. |
| 10 | Privacy | **PASS** | No counts of 1–10 in docs/v16/*.md (regex scan of "n (x%)" cells and complements; COVARIATES.md uses `<11`). The S4 coverage table holds percentages of cohorts ≥ 1,794 patients with no stratum < 13%. Its last column, headed "confounding", is the trial-level \|unadj − RCT\|, not a percentage; relabel it. The PNGs are drawn from trial-level summaries. |
| 11 | *(added)* Benchmark specificity of the RCT-agreement gain | **FAIL** (for "closer to the RCT") | With RCT benchmarks shuffled across trials, ECG "improves" z² about as much as with the true benchmarks. Examples: S1 demo z² −3.66 vs null median −3.64 (p = 0.49); sparse −1.40 vs −1.83 (p = 0.79); none −6.4 vs −9.2. ECG mainly moves log HRs toward the null: mean \|log HR\| goes from 0.317 to 0.277 for demo and from 0.224 to 0.193 for sparse, and RCT \|log HR\| averages 0.145. **\|Δlog HR\| is benchmark-specific only in a few post-hoc cells** (S1 demo p = 0.046; S3 demo 64 PCs p = 0.003; sparse overlap p = 0.011; sparse 1:3 matching p = 0.006). |

## Details

### 1. Recomputation (`check1_recompute.csv`, `check1_cross_sweep.csv`)
The audit recomputed per-trial ECG − base differences directly from each `results.csv` for these cells:
- S1: none, demo, minimal-7, sparse, hdPS200 and clinical, on \|Δ\|, z², mean \|SMD\|, C-statistic and common-4.
- S3: demo/sparse 32 PCs, sparse and demo 64 PCs, sparse overlap, sparse match 0.2×3 and sparse L2 C = 0.01.
- S4: the demo and sparse top-confounding tertiles, demo/sparse echo = no, demo echo = yes, sparse 'all' and demo lag ≤ 30.

Every d, k/n and p equals the sweep summary CSVs and the markdown tables. Spot checks of the markdown numbers also match:
- S1 demo \|Δ\|: −0.057, 14/18, p = 0.033.
- S1 sparse z²: −1.403, p = 0.024.
- S3 sparse overlap mean \|SMD\|: −0.011, p < 0.001.
- S4 demo T3 z²: −8.55, p = 0.031.

S1 and S3 default cells are identical to one another. The S4 demo arms differ slightly, as noted in the verdict table.

### 2. Held-out leakage
- **PS designs vs the 58-panel.**
  - demo, demo+race, min-7, sparse and hdPS contain no meds, util or observed-vitals components.
  - hdPS uses pool-A codes only, and the pool-B split is the same seed as the held-out matrix.
  - Clinical (`X_core`) contains the meds, util and 9 phys columns. S1 removes them in `mean_smd_ho`/`cstat_ho`. S3 and S4 never use clinical.
- **Residual overlaps (minor).**
  - Pool-B features contain the ICD roots behind sparse flags (for example comet: dx_E11, dx_I10, dx_I25, dx_I48; aristotle and allhat: dx_E78). So the S1 sentence "Race/HLD/T2D/CAD/HTN are not in the 58-panel" is not strictly true for B_mean.
  - The clinical held-out subset still contains echo EF (vs lvef in the PS) and eGFR/BUN (vs creatinine).
- **New covariates.** t2d is excluded wherever sparse `diabetes` or min-7 t2d is in the PS. hyperlipidemia and race are excluded in the min-7 and sparse+race+HLD rungs. inpatient_days_365 is excluded for clinical. Kept despite proxies:
  - prior_hf_hosp_365 where heart_failure is in the PS (documented);
  - obesity for clinical (BMI in the PS; not documented).
  - Clinical's common-4 gain (−0.007) may therefore be slightly inflated or deflated. This is immaterial to the conclusions.
- **prog_full.** It is fitted by `fit_prognostic_score.py` on an external reference set built by `build_prognostic_reference.py`, which excludes all cohort person_ids. For all 18 trials, the excluded count equals the roster size. No cohort outcome is read.

### 3. Placebos (`partb_trials.csv`, `check3_*.csv`)
**Permutation.**
- `T.shuffle_perm` is a true permutation for all 18 trials (fixed points ≤ 0.06%).
- Treatment concordance under the permutation equals its chance expectation (for example 0.519 vs 0.515).
- Max \|corr(PC, treatment)\|: shuffled PCs 0.013–0.066, noise 0.010–0.063, real PCs 0.043–0.209.
- S3 shuffles each representation (4 to 256 dims, phenotypes) with the same permutation. Noise has the same dimension and is seeded (32-d = `T.noise32`, else 3000 + 1000·d).

Placebo − base across all 91 S1+S3+S4 cells (full cohort):

| contrast | metric | mean d | median d | % cells d<0 | % p<0.05 better | % p<0.05 worse |
|---|---|---|---|---|---|---|
| ECG − base | \|Δlog HR\| | −0.032 | −0.031 | 90 | 34 | 0 |
| ECG − base | z² | −2.14 | −1.65 | 97 | 62 | 0 |
| ECG − base | mean \|SMD\| | −0.0146 | −0.0120 | 100 | 77 | 0 |
| ECG − base | C-statistic | −0.0156 | −0.0168 | 100 | 81 | 0 |
| shufECG − base | \|Δlog HR\| | +0.001 | +0.001 | 48 | 0 | 2 |
| shufECG − base | z² | +0.12 | −0.00 | 51 | 2 | 1 |
| shufECG − base | mean \|SMD\| | +0.0007 | +0.0003 | 44 | 0 | 2 |
| shufECG − base | C-statistic | +0.0023 | +0.0022 | 30 | 0 | 13 |
| noise − base | \|Δlog HR\| | +0.005 | +0.003 | 42 | 0 | 2 |
| noise − base | z² | +0.27 | +0.20 | 30 | 2 | 3 |
| noise − base | mean \|SMD\| | +0.0007 | +0.0005 | 41 | 0 | 2 |
| noise − base | C-statistic | +0.0019 | +0.0024 | 32 | 2 | 8 |

**Reading.**
- The placebo null is centred at or slightly above 0: adding 32 uninformative columns slightly worsens the held-out C-statistic.
- "ECG beats placebo" contrasts are therefore marginally easier to pass than "ECG beats base".
- Pair counts barely differ from base: median ECG/base ratio 0.997–0.999 (placebos 0.999–1.000), minimum 0.79.

### 4. Halves (`check4_halves.csv`, `partb_trials.csv`)
**Validity.**
- S1, S3 and S4 use the same split (`default_rng(16060 + i)`, per-arm permutation).
- A∩B = ∅ and A∪B = the cohort in all 18 trials.
- \|treated share A − B\| ≤ 0.0004.
- n(A)+n(B) = n(full) exactly; pairs(A)+pairs(B) / pairs(full) has median 0.997–0.999 (range 0.85–1.08).
- Event-rate differences between halves are chance-sized (≤ 0.047, largest in the smallest trials).

**Agreement of cell-level d across cells:**

| metric | corr(full, mean of halves) | corr(A, B) |
|---|---|---|
| \|Δlog HR\| | 0.40 | 0.39 |
| z² | 0.94 | 0.90 |
| mean \|SMD\| | 0.89 | 0.80 |
| C-statistic | 0.78 | 0.26 |

- \|Δlog HR\| is essentially unreplicable at half size.
- For the C-statistic, A and B agree across cells much less than the full-cohort values imply (the cross-fitted AUC is noisy at half size).

### 5. Regression to the benchmark (`check5_*.csv`, `check5b_*.csv`)
The analysis is a univariable WLS of the per-trial ECG gain on the moderator, with weights 1/(se_base² + se_RCT²) as in S4 (k = 18).

| base | moderator | metric | slope/SD | perm p | shufECG slope/SD |
|---|---|---|---|---|---|
| demo | \|unadj − RCT\| (S4) | \|Δ\| | −0.062 | 0.003 | +0.030 |
| demo | \|unadj − RCT\| (S4) | z² | −5.31 | 0.001 | +2.67 |
| demo | \|unadj − clinical PS\| (no RCT) | \|Δ\| | −0.040 | 0.084 | +0.029 |
| demo | \|unadj − clinical PS\| (no RCT) | z² | −3.66 | 0.011 | +2.44 |
| sparse | \|unadj − RCT\| (S4) | \|Δ\| | −0.038 | 0.003 | −0.023 |
| sparse | \|unadj − RCT\| (S4) | z² | −2.59 | <0.001 | −1.26 |
| sparse | \|unadj − clinical PS\| (no RCT) | \|Δ\| | −0.036 | 0.005 | −0.022 |
| sparse | \|unadj − clinical PS\| (no RCT) | z² | −2.07 | 0.002 | −1.26 |

The permutation p above permutes the moderator. That tests association, not benchmark specificity. Two null distributions test specificity.

**Null (b): RCT HRs (and SEs) shuffled across trials, with the moderator and outcome recomputed.**

| base | metric | observed slope | null median | null 5th–95th pct | P(null ≤ observed) |
|---|---|---|---|---|---|
| demo | \|Δ\| | −0.062 | −0.057 | −0.077 to −0.036 | 0.33 |
| demo | z² | −5.31 | −8.29 | −12.1 to −3.8 | 0.86 |
| sparse | \|Δ\| | −0.038 | −0.041 | −0.047 to −0.032 | 0.74 |
| sparse | z² | −2.59 | −4.97 | −7.7 to −1.9 | 0.89 |

**Null (a'): no-RCT moderator \|unadj − clinical PS\|, RCTs shuffled in the outcome only.** The ECG slopes are *less* negative than
the null (P(null ≤ observed) = 0.93/0.94 demo, 0.68/0.91 sparse).

**Conclusion.**
- A negative slope arises for any benchmark, because the ECG arm moves log HRs toward the null (check 11), and trials with large confounding have more room to move.
- The confounding-magnitude "effect modifier" is not evidence of ECG information.
- The tertile cells (demo/sparse T3, p = 0.031, 6 trials) inherit the same problem.

### 6. Global multiplicity (`check6_global_fdr*.csv`, `check6_effective_number.csv`)
**Scope.**
- All full-cohort ECG vs base cells of S1 (13), S3 (44) and S4 (46 incl. confounding tertiles).
- Exact duplicate designs are dropped: the S3 duplicate default cells, and the S3/S4 copies of S1 demo/sparse when numerically identical. That leaves 85 cells per core metric.
- Also included: the S1-only metrics (held-out-from-base \|SMD\| and C-statistic, new covariates, common-4; 13 each).

BH within metric over all sweeps; cells with q < 0.05 and d < 0:

| metric | S1 | S3 | S4 | total |
|---|---|---|---|---|
| \|Δlog HR\| | 0/13 | 1/39 (demo 64 PCs, q = 0.049) | 0/33 | **1/85** |
| z² | 4/13 (none, demo, demo+race, min-7+year) | 27/39 | 5/33 | 36/85 |
| mean \|SMD\| | 10/13 | 32/39 | 20/33 | 62/85 |
| C-statistic | 11/13 | 31/39 | 23/33 | 65/85 |

- A single BH over all 392 cell × metric tests gives 12 \|Δ\| "survivors" (for example S1 demo+race). That is an artifact of mixing a weak family with hundreds of p ≈ 1e-5 balance tests; do not report it.
- With S2 (seed 0) added, the counts barely change (S2: \|Δ\| 1/10, z² 6/11, SMD 9/10, C 10/11 under the pooled BH).

**Effective number.** Per-trial ECG gains are strongly correlated across cells:

| metric | median r | IQR | Li–Ji M_eff | variance share of first eigenvector |
|---|---|---|---|---|
| \|Δlog HR\| | 0.36 | 0.07–0.59 | 20 | 44% |
| z² | 0.67 | 0.36–0.83 | 16 | 64% |
| mean \|SMD\| | 0.48 | 0.28–0.66 | 18 | 51% |
| C-statistic | 0.64 | 0.50–0.76 | 17 | 64% |

M_eff is bounded by the number of trials (17 complete). The sweeps amount to one experiment on 18 (overlapping) trials viewed ~80 ways.
"Consistent across cells" is not independent confirmation.

### 7. Trial dependence (`check7_loo_cluster.csv`, `partb_roster_overlap.csv`)
The 10 clusters group trials that share a question or comparator: DOAC-vs-warfarin (3); SGLT2-vs-DPP4 (2); ARB-vs-ACEi (2); AF rhythm (2); hypertension (ALLHAT, VALUE, ASCOT, LIFE); plus 5 singletons. Each cluster's p is the sign-flip over cluster means.

| S1 cell / metric | d (k) | p | LOO p range | LOO drops with p ≥ 0.05 | cluster p (k better) | max p dropping one cluster |
|---|---|---|---|---|---|---|
| demo \|Δ\| | −0.057 (14/18) | 0.033 | 0.007–0.066 | 7/18 | 0.24 (6/10) | 0.14 |
| demo z² | −3.66 (14/18) | 0.006 | 0.001–0.012 | 0 | 0.084 (6/10) | 0.042 |
| sparse z² | −1.40 (14/18) | 0.024 | 0.001–0.048 | 0 | 0.025 (8/10) | 0.080 |
| sparse mean \|SMD\| | −0.0067 (14/18) | 0.026 | 0.004–0.053 | 3/18 | 0.105 (7/10) | 0.065 |
| demo mean \|SMD\| | −0.023 (17/18) | <0.001 | <0.001 | 0 | 0.004 (9/10) | <0.001 |
| sparse C-statistic | −0.013 (15/18) | 0.023 | 0.002–0.046 | 0 | 0.031 (7/10) | 0.10 |
| demo C-statistic | −0.018 (15/18) | 0.003 | <0.001–0.006 | 0 | 0.006 (9/10) | 0.018 |
| min-7 mean \|SMD\| | −0.016 (16/18) | <0.001 | <0.001–0.001 | 0 | 0.002 (10/10) | 0.002 |
| hdPS200 mean \|SMD\| | −0.0097 (15/18) | 0.003 | <0.001–0.006 | 0 | 0.002 (10/10) | 0.008 |
| none z² | −6.40 (14/18) | 0.001 | <0.001–0.003 | 0 | 0.023 (7/10) | 0.010 |

- The roster overlap is large even across clusters (for example ARISTOTLE–CABANA 49%, ONTARGET–VALUE 47%). So the trial-level sign-flip treats as exchangeable units that partly share patients and comparator arms.

### 8. SMD definition and the C-statistic artifact (`partb_trials.csv`)
**SMD definition.**
- `smd_components` divides by sqrt((var_t + var_c)/2) over all analysed rows (pre-match, ddof 1). The numerator is the NaN-aware weighted difference in the matched sample, which is the same as eval_longtail_balance.
- A smaller matched set would inflate the \|SMD\| noise floor, which works *against* ECG. It is therefore not an artifact in ECG's favour.

**C-statistic thinning test.** The test re-matched the sparse and demo bases and their +ECG arms in all 18 trials. Base matched pairs were thinned at random to the ECG pair count (5 reps).

| base | ECG/base pairs (median) | ECG − base C | thinned base − base C | ECG − thinned base C | fold-seed SD of C (median) |
|---|---|---|---|---|---|
| sparse | 0.9998 | −0.0133 (p = 0.023) | −0.0003 (p = 0.78) | −0.0130 (p = 0.011) | 0.0029 |
| demo | 0.9996 | −0.0176 (p = 0.003) | +0.0009 (p = 0.39) | −0.0185 (p = 0.0008) | 0.0026 |

The per-trial fold-seed SD of the C-statistic (~0.003) is of the same order as the hdPS-rung gains (0.007–0.012). Those gains are only detectable when averaged over trials.

### 9. Markdown statements that overstate (recommended edits)
**S1_LADDER.md**
1. *"Agreement with the RCT"* (findings 4–5, bottom line) should say "\|Δlog HR\|/z² vs RCT decreases". Check 11 shows the z² gain is not specific to each trial's own RCT (for example demo z² −3.66 vs −3.64 with shuffled benchmarks). It is consistent with generic shrinkage toward the null.
2. *"Only 'none' meets every criterion"* (z²): 'none' compares an ECG-only PS against the crude estimate, so it is not an ECG add-on effect. Its z² gain is also benchmark-nonspecific (−6.4 vs null −9.2).
3. *"placebo-beating"* in the automatic flags means direction only. Say so, and note that the placebo null is slightly positive.
4. *"Race/HLD/T2D/CAD/HTN are not in the 58-panel"*: pool-B codes include the ICD roots E11/E78/I10/I25 in some trials.
5. *"Dispersion φ is lower with ECG at every rung"*: this is descriptive and untested, and it is equally explained by shrinkage toward the null.
6. *Replicated* (p < 0.05 in both halves) for hdPS25 and similar cells should be phrased as "significant in both halves of the same trials", not replication.

**S3_REPR.md**
1. Finding 1 heading: *"robust … survives FDR and replicates"* is true for the demo base only. On sparse, mean \|SMD\| replicates at p < 0.05 in both halves in only 2/22 cells, and z² in 7/22.
2. Finding 6: *"for balance and z² these gains are ECG-specific, FDR-significant and replicated in both halves"*. Replace z² with a qualified statement: global within-metric BH passes 27/39 S3 cells, but the gain is benchmark-nonspecific.
3. Findings 2/4: 64 PCs, overlap weights, 1:3 matching and C = 0.01 are post-hoc picks among 44 cells. Under the global BH only demo 64 PCs survives for \|Δ\| (q = 0.049), and it fails half replication (half A p = 0.52).

**S4_SUBGROUPS.md**
1. **Finding 3 should be withdrawn or rewritten.** The "effect modifier: confounding magnitude" is reproduced exactly by shuffled benchmarks (check 5). *"The placebo slopes have the opposite sign, so this is ECG-specific"* is not a valid inference. Placebos do not shift estimates, so they cannot show the shrinkage artifact.
2. Finding 4 (*"populations that do not modify the ECG gain"*) rests on overlapping intervals without an interaction test. Say "no evidence of modification (not tested formally)".
3. The echo comparison of balance gains compares \|SMD\| over different variable sets: echo components are all NaN in echo = no. That caveat is there; also apply it to the C-statistic.
4. The coverage table's last column is headed `confounding`, but the table is labelled "% of trial cohort". Relabel it.

### 10. Privacy
- docs/v16/*.md: no "n (x%)" cells with n in 1–10 and no complements in 1–10 (COVARIATES.md uses `<11` 21 times).
- S1/S3/S4 hold only trial-level means, medians of pair counts and p-values.
- The S4 audit mentions per-analysis minima of 105 / 30 / 36 matched pairs (> 10).
- The PNGs are drawn from `summary*.csv` (trial-level aggregates).
- This audit's outputs hold trial-level aggregates and roster-overlap percentages only; overlaps < 11 persons are dropped.

## Headline claims that survive the audit
1. **Held-out balance.** Adding 32 BCL ECG PCs to a thin PS (demo, demo+race, minimal-7) lowers held-out mean \|SMD\| (about −0.016 to −0.023) and the held-out C-statistic (about −0.014 to −0.021). This holds with the true 18 trials:
   - ECG-specific against placebos;
   - under global BH;
   - under leave-one-trial-out and comparator clustering (cluster p ≤ 0.006);
   - not a pair-count artifact.
2. **Richer baselines.** With sparse/hdPS the balance gain is small (about −0.006 to −0.013). It is globally FDR-significant in most cells but fragile: sparse mean \|SMD\| cluster p = 0.105; hdPS200 mean \|SMD\| survives, cluster p = 0.002. With clinical it is null.
3. **\|Δlog HR\| vs RCT.** No robust improvement: 1/85 cells passes global within-metric BH, and none replicates. The smaller z² with ECG is real in the data, but it is not specific to each trial's RCT. It is equivalent to shrinking estimates toward the null, so it should not be presented as "closer to the RCT".
4. **Effect modifiers.** No subgroup or trial-level effect modifier survives. The confounding-magnitude result is a benchmark artifact.

## Recommended corrections for the synthesis
1. Lead with balance on held-out variables (demo/minimal-7 bases) as the finding, and state that it is small on sparse/hdPS and null on clinical.
2. Report the global within-metric BH (this audit) next to the within-sweep FDR. Drop "significant" wherever only within-sweep q < 0.05 holds and the global q ≥ 0.05, including all \|Δlog HR\| cells except S3 demo 64 PCs.
3. Replace "moves HRs closer to the RCT" with "shrinks HRs toward the null; the reduction in \|Δ\|/z² is not specific to the trial's own RCT benchmark (shuffled-benchmark null)". Add the shuffled-benchmark test as a standard guardrail.
4. Withdraw S4 finding 3 (the confounding-magnitude modifier) and the statements about the T3 tertile.
5. State the trial dependence explicitly. Rosters overlap by up to 82%, and there are 10 comparator clusters. Give cluster-level p-values for headline cells, and call halves "within-trial split halves", not replication.
6. Note the minor held-out residual overlaps (pool-B ICD roots; clinical EF/eGFR/BMI proxies) and the demo-PS tie-breaking nondeterminism (\|Δlog HR\| ≤ 0.006).
7. Audit S2 once `docs/v16/S2_DROPOUT.md` exists. It needs the same checks: its placebos, halves and seeds, plus the shuffled-benchmark and cluster tests.
