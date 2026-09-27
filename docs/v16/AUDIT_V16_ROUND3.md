# v1.6 sweep audit, round 3 (final): S8 headline, S9 covariate sets, round-2 fixes, global multiplicity (2026-09-27)

This is an independent, skeptical third-round audit. It covers S8 (|SMD| < 0.1 headline), S9 (covariate sets), the round-2 fixes (covars2b, S6 v2b) and the global multiplicity across S1–S9.

The audit code is its own:
- `scripts/v16/audit3/`: `a3_common.py` (exact sign-flip, BH, love count, arm-swap permutation), `a3_s8.py`, `a3_retention.py`, `a3_s9.py`, `a3_global.py`.
- It recomputes everything from raw per-trial arm rows (`results_v2.csv`, `var_*.parquet`, `results_x2np.csv`) and never calls a sweep's summary functions.
- `a3_retention.py` re-fits the demo PS and re-matches with the engine's `ps_logit` / `match`, reproducing S8 exactly (pair counts Δ = 0, % < 0.1 Δ < 1e-14).

Aggregate outputs are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-audit3/` (umask 077):
- `s8_recompute.csv`, `retention_demo.csv`, `s9_recompute.csv`;
- `global_cells_all18.csv`, `global_cells_withphys.csv`, `pooled_balance_bh.csv`.

There are no patient-level rows. "k/18" are trial counts, and love counts are variable counts.

## Verdict table

| # | Check | Verdict | Consequence |
|---|---|---|---|
| 1 | Independent recomputation | **PASS** | Every S8 and S9 number checked reproduces (max \|Δd\| 4e-15, \|Δp\| 6e-17). S8 demo / caliper 0.1 / 18 trials: 54.2 → 61.0% (+6.8 pp, 13/18, p = 0.0008, cluster p = 0.023, LOO max p = 0.0016; half A p = 0.0011, half B p = 0.0045); love count 29 → 43 of 58. S9 and S6-v2b also reproduce (below). |
| 2 | Love-count test validity | **PASS with caveat** | The within-trial arm-swap permutation is a valid randomisation test of the same exchangeability null as the sign-flip. The love count is coarse, and the test has less power than the per-trial sign-flip: 17 vs 26 of 36 S9 family rows reach p < 0.05, with 10 discordant rows (per-trial significant, love count not) and 1 the other way. A per-trial count sign-flip gives the per-trial % p. Report the love count as descriptive, with the per-trial metric as the test. |
| 3 | Selection integrity (S8, S9) | **PASS** | S8: half-A run ends 23:41:38, `selection.json` 23:42:00, commit 42f1758 23:42:16, full/B run 23:42:27–23:47:30 (303 s). S9: mapping commit 5c0a94d 00:09:53, half-A run 00:10:07–00:10:24, selection 00:11:39, commit 60ed1c6 00:11:45, full/B run 00:11:55–00:13:03. Code review confirms both selections read half-A rows only. Set 3 re-derives exactly from half A (12/12 scenarios). |
| 4 | Forking paths in the 18-trial S8 headline | **CONCERN (minor)** | demo / caliper 0.1 / 18 trials ranks 8/33 by gain and 16/33 by p among the 18-trial PS cells; BH q = 0.0015 (33 cells), 0.0032 (132 S8 tests), 0.0032 (143 unique S1–S9 cells). In half A it ranked 1st among 18-trial cells and 3rd among eligible scenarios. It was excluded only by the "one scenario per base" rule. Caliper is **not** material: at caliper 0.2 it is +6.4 pp, p = 0.0002, love 32 → 43. **Recommend caliper 0.2 as the headline** (see below). |
| 5 | Leakage (covars2b; S8 expanded panel) | **PASS (S8 minor)** | No covars2b-excluded (trial, variable) pair and no non-pre-index variable appears in S9, or, by code path, in S6 v2b. S8's expanded panel used covars2: it has `hfrs_ge5` in 18 trials and 8 utilisation variables built with the old index-stay visit rule. Recomputed on covars2b non-proximal, the S8 expanded rows change by ≤ 0.1 pp (table below). The conclusions stand. |
| 6 | Caliper 0.1 retention / population | **PASS with caveat** | ECG matches slightly fewer anchor-arm patients. At caliper 0.1: 89.1% (base) vs 87.2% (ECG), −1.9 pp, lower in 13/18 trials, p = 0.092. At caliper 0.2: −1.3 pp, p = 0.30. Every S8 matching cell loses 1–2.5 pp with ECG. On the common-anchor intersection (82% of anchors, identical population in both arms) the gain is 83% of the full gain: +5.7 pp, 15/18, p = 0.0017, cluster p = 0.016, love 30 → 40. The retained population is barely shifted (anchor-vs-all 58-panel \|SMD\| +0.003, p = 0.20). |
| 7 | Trial-emulation claims | **PASS** | S8 finding 5 and S9 finding 8 claim no benchmark-specific gain, and the S8 bottom line says not to frame it as RCT agreement. Global BH (below) confirms 0 \|Δlog HR\| cells and 0 benchmark-specific cells. Three wording edits follow (§7). |
| 8 | Global multiplicity S1–S9 | **Claims unchanged** | 143 unique 18-trial full-cohort cells (round 2: 129; S8 adds 15; S9 and S6 v2b add 0). \|Δlog HR\| 0/143 (min q 0.064); benchmark-shuffle 0/143 (min q 0.057); significant AND benchmark-specific 0/143; z² 88/143 but 0 benchmark-specific; mean \|SMD\| 123/143; C 122/143; % < 0.1 88/143. Across 573 pooled balance tests (cells × 3 metrics + S9 family × 4 metrics): 430 survive, 0 significantly worse. |
| 9 | Privacy and permissions | **PASS** | Every file and directory under claude-v16-s8-headline, s9-covsets, covars2b, s6-balance-v2b and s5-nco-v2b is 600/700 (`find -perm /077` is empty). Committed S8/S9/fix markdown has no patient or event counts of 1–10; the only "pairs" figures are ratios. `selection_S9.json` holds variable names, \|SMD\| gains and trial counts only. |

## Details

### 1. Recomputation

**S8** (`a3_s8.py` on `results_v2.csv`).
- `results.csv` equals `results_v2.csv`.
- The half-A rows in `results_v2.csv` equal the pre-selection `prev_v1_expanded/results_A.csv` exactly (log HR and % < 0.1 Δ = 0). The selection therefore stands on the rows that exist today.
- % < 0.1 was recomputed from the 58 `smd:` columns, not from `p58_pct_lt10` (Δ < 1e-14).

| cell (18 trials) | half | base → ECG % < 0.1 | d (k) | p | cluster p | love base → ECG (arm-swap p) |
|---|---|---|---|---|---|---|
| demo / caliper 0.1 | full | 54.2 → 61.0 | +6.81 (13/18) | 0.0008 | 0.023 | 29 → 43 (0.001) |
| | A | 47.6 → 55.8 | +8.14 (16/18) | 0.0011 | 0.004 | 20 → 38 (<0.001) |
| | B | 47.5 → 53.4 | +5.87 (12/18) | 0.0045 | 0.008 | 24 → 33 (0.042) |
| demo / caliper 0.2 | full | 53.8 → 60.2 | +6.42 (14/18) | 0.0002 | 0.016 | 32 → 43 (0.005) |
| | A | 48.9 → 56.5 | +7.66 (16/18) | 0.0012 | 0.004 | 24 → 38 (0.008) |
| | B | 47.3 → 54.0 | +6.73 (12/18) | 0.0038 | 0.012 | 24 → 34 (0.029) |
| minimal-7 | full | 53.1 → 59.8 | +6.71 (15/18) | 0.0008 | 0.051 | 27 → 40 (0.001) |
| common-10 | full | 58.4 → 65.3 | +6.90 (15/18) | 0.0008 | 0.023 | 42 → 48 (0.24) |
| sparse | full | 63.4 → 64.0 | +0.66 (8/18) | 0.69 | 0.36 | 48 → 47 (0.87) |
| hdPS200 | full | 67.2 → 71.7 | +4.50 (12/18) | 0.012 | 0.020 | 46 → 53 (0.052) |

- The demo caliper 0.1 LOO max p is 0.0016.
- The S8 love counts were descriptive; the arm-swap p values in the table are new.

**S9** (`a3_s9.py` on `var_A` / `var_full_B`). All 108 recomputed rows (9 scenarios × 4 sets × 3 halves) equal `set_summary.csv` (max \|Δd\| 4e-15). The love-count arm-swap p agrees within Monte-Carlo error.

Headline rows (demo / caliper 0.1, 18 trials):

| set | full: % < 0.1 (d, p, q) | love (p; LOO max p) | half B d (p, q) | half B love (p) |
|---|---|---|---|---|
| Set 1 (28) | 43.6 → 55.1 (+11.6, p = 0.0015, q = 0.004) | 8 → 16 (0.021; **0.15**) | +9.2 (0.0025, 0.010) | 6 → 11 (0.14) |
| Set 2 (273) | 55.8 → 61.9 (+6.1, p = 0.0002) | 160 → 193 (0.0005) | +5.7 (<0.001) | 146 → 176 (0.005) |
| Set 3 (25) | 28.5 → 39.4 (+10.9, p = 0.0006) | 2 → 7 (0.098) | +7.4 (0.012, 0.031) | 2 → 4 (0.31) |
| FULL (405) | 59.9 → 65.3 (+5.4, p < 0.001) | 266 → 309 (<0.001) | +4.4 (0.0005) | 244 → 277 (0.006) |

**S6 v2b** (own sign-flip on `results_x2np.csv` `xsmd_other`).
- sparse x2np: 0.0758 → 0.0689 (−0.0069, 14/18, p = 0.0009, cluster p = 0.0078). This matches AUDIT_V16_ROUND2_FIXES.
- Halves: A p = 0.0078, **B p = 0.135** (12/18).
- Other rows: demo −0.0133 (17/18); minimal-7 −0.0087 (18/18); sparse-drop50 −0.0053 (p = 0.022); clinical −0.0026 (p = 0.0049, cluster p = 0.049); hdPS200 −0.0004 (p = 0.51). All match.

### 2. Love-count test
**Validity.** Under H0 the two arms' per-trial \|SMD\| vectors are exchangeable within trial. Swapping them is the same randomisation group as the sign-flip, applied to a non-additive statistic (a count of per-variable medians across trials). It is exact for ≤ 12 units and Monte-Carlo otherwise. The test is valid:
- the arms share patients, but that affects only power;
- the statistic is two-sided;
- NaN handling is consistent.

**Power.** It has less power than the per-trial test:
- S9 family, full cohort: 17 love vs 26 per-trial rows at p < 0.05; rank correlation of p 0.82.
- The 10 discordant rows are all "per-trial significant, love not" (for example Set 3 half B 2 → 4, p = 0.31, while the per-trial p = 0.012).
- A per-trial sign-flip on the *count* of variables below 0.1 reproduces the per-trial % p (for example Set 1 full 0.0016).

**Recommendation.** Use the per-trial % < 0.1 (or count) sign-flip as the inferential test. Show the love-plot count descriptively, or with the arm-swap p labelled as such. The Set 1 love count is not LOO-robust (max p 0.15), so do not headline "8 → 16" as a tested result.

### 3. Selection integrity
**S8.**
- `select()` calls `load_results(["A"])` and `grid_summary(df, ["A"])`. It globs `results_*.csv`; at selection time the only such file was `results_A.csv`. The 2-trial full-cohort engine check is `audit_check_results.csv`, which the glob does not match, and it does not contain the demo caliper 0.1 cell.
- `selection.json` equals `prev_v1_expanded/selection_original.json`.
- The `select()` code is unchanged between 42f1758 and HEAD. The later diff touches only the expanded-panel exclusions, the worker cap and the reporting.
- The full/B start (≈ 23:42:27, from the 303-s runtime) is 11 s after the commit.

**S9.**
- The plan (f533f16, 23:45:55) predates every S9 output. The earliest is the 2-trial half-A test at 00:08:33.
- `run()` asserts that `selection_S9.json` exists before any non-A half. `select()` asserts `set(V.half) == {"A"}`.
- The committed JSON equals the output copy.
- The Set 1 / Set 2 mapping code is unchanged between 5c0a94d and HEAD (the diff touches plots and the seed column only).
- COVARIATES2.md changed at 631bd8c, after the mapping commit. Re-deriving Set 2 from the 5c0a94d version of COVARIATES2.md gives the identical 275 variables (0 differences).

**Set 1 vs plan.** All 29 plan items are mapped. LV mass is unavailable, as logged. All 28 variables are observed. "IVSd > 15 mm" is correctly not added.

**Set 2 by rule.** 139 core + common items: 129 map to ≥ 1 variable, and 10 are excluded with logged reasons (age/sex/index year are in every PS, index-day, not in extract, ADI, NLP-only, PS-only).

**Minor deviations (not logged).**
- The Set 3 / FULL pool excludes the claude-v16-covars (`v1:`) variables (race, tobacco, obesity and others). The plan says "full expanded non-proximal panel plus the 58-panel". The effect is small, but log it.
- **Scenario choice.** The S9 18-trial headline scenarios were fixed at 5c0a94d (00:09:53), after the S8 full/B results (commit 86d6ef3, 23:58). 24 of Set 1's 28 variables are 58-panel echo/lab variables already seen in S8. Set 1 is therefore mechanism-defined but *not* blind to S8's full-cohort result for these cells. Only Set 3 half B is truly out of sample.

### 4. Forking paths in the S8 18-trial headline
**How much was examined.** The S8 grid has:
- 34 cells (33 with a PS base) × 2 trial subsets × 2 panels × 3 halves × 5 threshold metrics;
- plus 4 engine metrics.

For the primary metric in the full cohort there are 66 tests on the 58-panel (132 with the expanded panel).

**Where demo / caliper 0.1 / 18 trials sits.**

| family | position | q |
|---|---|---|
| 33 18-trial cells, full | rank 8 by d, 16 by p | 0.0015 |
| 132 full-cohort S8 tests | | 0.0032 |
| 143 unique S1–S9 cells (this design is S3 `3c|demo|match0.1x1`) | rank 34 by p | 0.0032 |
| half B, 33 cells | rank 7 by d | 0.016 |

- In half A it ranked 1st among the 18-trial cells (+8.1 pp).
- It sat 3rd in the eligible list, behind its own physiology-subset twin, which took the demo slot under the one-per-base rule.

**The headline is a family-wide pattern.**
- 28/33 18-trial cells are p < 0.05 in the full cohort (27 BH).
- 15/33 are p < 0.05 in **both** halves: demo × {0.2, 0.1, 1:3, overlap}, minimal-7 × {0.2, 0.1, 1:3, overlap, 64 PCs}, sparse-50% × 5 estimators, sparse-75%.

The forking-path inflation for "ECG raises % < 0.1 at thin PS bases" is therefore small. The specific cell/wording choice matters little.

**The selection rule is biased toward the 8-trial subsets.** Ranking by raw gain favours 8-trial subsets (higher variance), which is why the pre-selected scenarios were physiology subsets and then shrank. That is a design weakness of the rule, not a violation.

**Caliper 0.1 vs 0.2 is not material.**
- % < 0.1: +6.8 vs +6.4 pp. Both halves are significant at each caliper.
- Love count: 29 → 43 vs 32 → 43. The larger contrast at 0.1 comes from a *lower base* love count (29 vs 32), not a better ECG arm.
- ECG at 0.1 minus ECG at 0.2: +0.9 pp (p = 0.41). Base at 0.1 minus base at 0.2: +0.5 pp (p = 0.52).

**Most defensible headline cell.** Demo PS (age, sex, index year) with the standard 1:1 caliper-0.2 match, 18 trials:
- this is the S1 ladder rung `r1_demo`, planned in V16_SWEEP_PLAN before any result;
- it is the engine's default estimator;
- q = 0.0013 over the 143 global cells.

Caliper 0.1 is a sensitivity.

### 5. Leakage
**covars2b.**
- The builder's visit query now requires `v.s < idx AND v.e < idx`.
- Spot check of `recent_hosp_30d` among index-inpatient patients (covars2 → covars2b; the third figure is the rate in non-inpatient patients):

  | trial | covars2 | covars2b | non-inpatient |
  |---|---|---|---|
  | TRANSFORM-HF | 61% | 8% | 12% |
  | PARADIGM-seq | 73% | 9% | 6% |
  | PLATO | 59% | 6% | 11% |

- `days_since_last_visit` changes in 23–47% of rows. The index-inpatient median goes from 5–6 d to 36–76 d.
- **S9:** 0 excluded (trial, variable) pairs, 0 non-pre-index variables, and no `hfrs_ge5`.
- **S6 v2b:** `load_extra` drops status ≠ kept*, leak and timing ≠ pre_index, the same filter S9 uses. S6 stores no variable lists, so this is verified by code path.

**S8 expanded panel (covars2 plus ad-hoc exclusions).**
- It still contains `hfrs_ge5` (18 trials; uncalibrated, not leaky).
- It contains 8 visit-utilisation variables built with the v2 rule, which counts a stay in progress: `days_since_last_visit`, `ehr_history_days`, and the outpatient, office, ED, telemedicine, infusion and anticoagulation-clinic counts.
- It also lacks the deterministic-lab fix.

Recomputed on the covars2b non-proximal panel (same matched sets, from S9's per-variable file; 347 variables):

| scenario | S8 (covars2) d, p | covars2b d, p |
|---|---|---|
| demo / cal 0.1, 18 | +5.06, 0.0003 | +5.14, 0.0002 |
| demo / cal 0.2, 18 | +5.29, 0.0001 | +5.34, 0.0001 |
| minimal-7, 18 | +3.32, 0.0002 | +3.38, 0.0001 |
| common-10, 18 | +3.12, 0.007 | +3.14, 0.007 |
| sparse, 18 | +3.05, 0.020 | +3.05, 0.023 (half B p = 0.15) |
| hdPS200, 18 | −0.07, 0.87 | −0.11, 0.82 |
| demo / cal 0.1, phys | +6.6, 0.016 | +6.58, 0.016 |
| minimal-7, phys | +4.7, 0.023 | +4.77, 0.023 |
| common-10, phys | +6.4, 0.008 | +6.43, 0.008 |

All differences are ≤ 0.1 pp. S8 finding 4 should cite the covars2b values or note the equivalence.

### 6. Retention (anchor = smaller arm; demo PS, full cohort, 18 trials)

| caliper | anchors matched, base → ECG | Δ (k lower, p) | common-anchor share | intersection % < 0.1 base → ECG (d, p, cluster p) | love (intersection) |
|---|---|---|---|---|---|
| 0.1 | 89.1% → 87.2% | −1.9 pp (13/18, 0.092) | 82.4% | 53.4 → 59.0 (+5.66, 15/18, p = 0.0017, cluster p = 0.016) | 30 → 40 |
| 0.2 | 90.6% → 89.3% | −1.3 pp (10/18, 0.30) | 84.9% | 52.8 → 57.9 (+5.08, 14/18, p = 0.0032, cluster p = 0.023) | 32 → 42 |

- The ECG arm's retention loss is generic. In S8's own n_pairs/n_t, every matching cell loses 0.9–2.5 pp with ECG, including sparse and hdPS200 where there is no balance gain.
- About 15–20% of the headline gain may reflect the ECG arm dropping hard-to-match anchors. The rest holds on an identical population.
- Report the retention by arm next to the headline.

### 7. Trial emulation and wording
No overstatement of RCT agreement was found. Global results (18-trial, 143 cells):
- \|Δlog HR\| 0/143 (best q 0.064: S3 demo 4 / 64 PCs, sparse 1:3);
- shuffle 0/143 (best q 0.057: S6 sparse-drop50, S4 age < 65);
- z² benchmark-specific 0/143.

Including the 33 S8 physiology-subset cells (176):
- \|Δ\| 0/176;
- 10/176 cells have shuffle q < 0.05 (mostly S8 physiology subsets), but none is also sign-flip significant (intersection-union 0/176).

**Edits.**
1. S8 finding 3: "The 18-trial analogues replicate robustly" → "The 18-trial analogues (post hoc; demo / caliper 0.1 was half-A-eligible, rank 3, and excluded only by the one-per-base rule) are significant in both halves".
2. S8 bottom line / finding 1: prefer caliper 0.2, "32 → 43". Add retention: "ECG matched 1–2 pp fewer patients; on the common matched population the gain is +5.1–5.7 pp".
3. S8 finding 4: note that on covars2b the values are unchanged (≤ 0.1 pp).
4. S9 finding 1:
   - "BH-FDR (36 tests per metric)" → "BH-FDR over 144 tests (36 scenario × set rows × 4 metrics) within half".
   - "replicates in both halves" → "is significant in half B on % < 0.1 (for Set 3, half A is the selection half). The love count is not significant in half B for Set 1 (p = 0.14) or Set 3 (p = 0.31), and the Set 1 love count is not LOO-robust (max p 0.15)".
5. S9 deviations: log that the Set 3 / FULL pool excludes the `v1:` variables, and that the 18-trial scenarios were fixed after the S8 full-cohort results.
6. S6 v2b: add "sparse x2np is not significant in half B (p = 0.14)" wherever the sparse v2b number is quoted.

### 8. Global multiplicity (`global_cells_all18.csv`)
**Method.** Same method as round 2: dedupe by per-trial log HR signature (trials sorted), seed-averaged dropout cells, and joint RCT (log HR, SE) shuffle with 5,000 draws.

**New unique 18-trial cells from S8.**
- demo × {0.1, 1:3, overlap, 64 PCs} are S3 copies. common-10 is S7 `common10`, and sparse minus AF is S7 `cum_k1`.
- The new cells are minimal-7 × {0.1, 1:3, overlap, 64 PCs}, sparse × {0.1, 1:3, 64 PCs}, hdPS200 × 4 estimators and the sparse-p25/50/75 seed-averaged cells, among others.
- S9's 6 cells are all copies. S6 v2b p58 is identical to v1.

| metric | survivors / 143 | best q |
|---|---|---|
| \|Δlog HR\| | 0 | 0.064 |
| \|Δ\| benchmark-shuffle | 0 | 0.057 |
| \|Δ\| significant AND shuffle | 0 | 0.124 |
| z² | 88 | 0.022 |
| z² shuffle | 0 | 0.47 |
| mean \|SMD\| | 123 | <0.001 |
| C-statistic | 122 | <0.001 |
| % \|SMD\| < 0.1 (58-panel) | 88 | <0.001 |

Headline q values (% < 0.1): demo caliper 0.2 = 0.0013; demo caliper 0.1 = 0.0032; minimal-7 = 0.0032; common-10 = 0.0032.

**Pooled balance family (573 tests).** 143 cells × {mean \|SMD\|, C, % < 0.1}, plus the S9 36 family rows × 4 metrics. 430 survive, and 0 are significantly worse.

| test | q |
|---|---|
| S9 Set 1 (demo caliper 0.1) % < 0.1 | 0.0038 |
| S9 Set 1 love count | 0.031 |
| S9 Set 3 full % < 0.1 | 0.0019 |
| S9 Set 3 love count | 0.11 |
| sparse FULL % < 0.1 | 0.041 |

### 9. Privacy and permissions
- All output directories are 700 and all files 600.
- The audit3 scripts are chmod 600.
- A scan of S8_HEADLINE, S9_COVSETS, S9 plan, the round-2 fixes, S6 and COVARIATES2 for "1–10 patients/events/pairs" and "n = 1–10" finds nothing.

## Recommended final headline wording

**Balance.**
> "In 18 Yale target-trial emulations, adding the AI-ECG embedding to a demographics-only propensity score (age, sex, index year; 1:1 caliper-0.2 matching) raised the share of 58 held-out covariates with |SMD| < 0.1 from 54% to 60% per trial (+6.4 percentage points; 14/18 trials; exact sign-flip p = 0.0002; significant in both random patient halves; no change with shuffled or random-noise embeddings), and the number of covariates with median |SMD| < 0.1 from 32 to 43. The gain was similar with minimal clinical PSs, but negligible when the PS already included the full coded diagnosis set (+0.7 points) and small or not replicated with high-dimensional PSs. ECG-adjusted matching retained 1–2% fewer patients; on the common matched population the gain was +5.1 points."

For the ECG-relevant physiology set (S9 Set 1, 28 echo/lab/HF variables), use this wording, labelled exploratory:
> "44% → 55% below 0.1 per trial (p = 0.0015), confirmed in half B".

**Trial emulation.**
> "Adding the embedding did not measurably bring emulated hazard ratios closer to the RCT results. The |Δlog HR| gain was significant in no design after correction for 143 designs, and apparent z² improvements were equally large against shuffled (wrong-trial) benchmarks, i.e. generic shrinkage rather than trial-specific agreement."

State that all of v1.6 is exploratory and post hoc, and that external (MIMIC/UKB) confirmation of the balance result is pending.
