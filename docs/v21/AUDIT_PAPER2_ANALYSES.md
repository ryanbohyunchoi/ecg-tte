# Adversarial review of the paper2 analyses (step E)

Written 2026-10-07 by the step-E reviewer. Scope: `docs/v21/PAPER2_RESULTS.md`, `PS_FLAGS.md`, `TRIAL_LABELS.md`, `PLASMODE_PAPER2.md`, `MIMIC_PAPER2.md`, `scripts/v21/*.py` and the outputs in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/{core,plasmode,mimic,labels}/`.

I changed no analysis code and no other doc. My scratch code and aggregate outputs are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/review/` (umask 077; trial-level aggregates only):
- `recompute.py`, `recompute_labels.py`: independent recomputation;
- `retention.py`, `fair_flags.py`, `fair_flags_summary.py`, `flag_proxies.py`: new sensitivity checks;
- the CSV and restricted parquet outputs of those scripts.

## Summary

| Severity | # | Items |
|---|---|---|
| **BLOCKING** | 1 | B1 small-count disclosure (PROTECT AF matched pairs) in a committed doc and in the "suppressed" CSVs |
| **SHOULD-FIX** | 7 | S1 PS-Flags fairness / "equivalent" wording; S2 "ECG uniquely improves echo" overstated; S3 CLMBR-T vs ECG reported for main only; S4 label analysis (multiplicity, statistic, κ from one model); S5 MIMIC side finding also affects published paper1 numbers; S6 unpaired agreement means in the PI head-to-head; S7 retention sensitivity not reported |
| NOTE | 11 | gate genuine; spec compliance; leakage; plasmode/MIMIC checks; minor numeric slips |

**Bottom line.**
- **The core computations are correct.** Every headline number I recomputed from `restricted_cells.parquet` with my own code matches the reported value to the printed precision (§R below). The gate is genuine.
- **The PS-Demo + CLMBR-T vs PS-Flags result can be reported** as "no evidence that CLMBR-T beats the flags". It cannot be reported as "equivalent". It should be reported together with a regularisation-tuned PS-Flags sensitivity (S1). That sensitivity moves the point estimate to −1.5% (CI −7.5 to 4.4), so the qualitative conclusion holds.
- **One privacy item (B1)** must be fixed before anything is pushed.

---

## BLOCKING

### B1. Small-count disclosure: PROTECT AF matched pairs (docs and "suppressed" CSVs)

**Evidence.**
- **Affected cells.** 13 cells in `core/restricted_cells.parquet` have `n_pairs` between 1 and 10, all in PROTECT AF:
  - Flags × {base, shufECG, shufCLMBR} × {main, cal01, m13};
  - hdPS200 × CLMBR (cal01) and hdPS200 × ECG+CLMBR (main, cal01, m13).
- **The CSVs.** `core/cells.csv` and `core/per_trial.csv` blank `n_pairs` for these cells (`suppressed_lt11 = True`) but keep the following:
  - `ess_t` / `ess_c`, which equal `n_pairs` exactly under 1:1 matching (integer-valued in all 13 rows);
  - `retain` = n_pairs / min(n_t, n_c), together with unsuppressed `n_t` and `n_c`.

  So the exact count can be recovered in **13/13** suppressed rows. These are the files the figures agent is told to read.
- **The docs.**
  - `docs/v21/PS_FLAGS.md` (committed in 115a4dc) lists the exact `retain_Flags_base_main` for PROTECT AF (value redacted here; it implied fewer than 11 matched pairs).
  - `PAPER2_RESULTS.md` §4 gave the retention as a rounded percentage of the smaller arm (now replaced).
  - With the PROTECT AF arm sizes, this bounds the matched-pair count to a small range inside 1–10. The 1,442-patient cohort is stated in the same docs and in `supplement.md`.

**Fix.**
1. In `paper2_grid.py`, add a wrapper around `SP.suppress` that also blanks `ess_t`, `ess_c` and `retain` (and `p_ps`-independent derived ratios) whenever `n_pairs` is suppressed. Regenerate `cells.csv` and `per_trial.csv`. Restricted parquet stays as is.
2. In `PS_FLAGS.md`, replace the exact value with `<0.02 (fewer than 11 matched pairs; suppressed)`. In `PAPER2_RESULTS.md` §4, write "keeps fewer than 11 matched pairs". Amend the local commit before the user pushes.
3. Tell the figures agent not to plot per-trial retention or ESS for suppressed cells.

---

## SHOULD-FIX

### S1. PS-Flags fairness: the C = 1 L2 PS overfits; report a tuned PS-Flags, and drop "equivalent"

**Evidence that the specified PS-Flags is under-regularised.** L2 C = 1 on standardised flags, with 426–622 binary columns.
- **In-sample PS AUC** (`review/restricted_flag_proxies.csv`):
  - 1.000 in PROTECT AF (622 flags, 1,442 patients);
  - ≥ 0.90 in 7/32 trials;
  - lower for P1 + CLMBR-T in the same trials (0.96 in PROTECT AF).
- **PROTECT AF is pure overfitting, not an exposure proxy.** No flag has |SMD| > 0.5 between arms there.
- **Retention of the smaller arm, S32 main:**
  - PS-Flags base: median 0.72 (mean 0.713), and 13/32 trials < 0.70;
  - P1 + CLMBR-T: median 0.83;
  - P5 base: median 0.99.

  `PS_FLAGS.md`'s "median 0.78" is the S38 median. The S32 value is 0.72.
- **Cross-validated C** (5-fold, log-loss, grid 1e-4 to 10): 3e-4 to 3e-3 for PS-Flags, i.e. 300–3,000× stronger regularisation than specified. It is 3e-3 to 0.1 for P1 + CLMBR-T, so C = 1 is also loose for CLMBR-T, but it matters far less there.

**Reviewer sensitivity: PS-Flags re-run with stronger or tuned regularisation.**
- Design: main configuration, S32, 54 items, paired, 4,000-resample bootstrap with seed 20261001.
- Script: `review/fair_flags.py`. The C = 1 arm reproduces the grid's Flags base cells exactly in all 32 trials (max |Δ| 0).
- Output: `review/restricted_fair_flags_h2h.csv`.

| a vs b (two-sided) | Trials | Relative reduction, 54 items (95% CI) | a better | P | Retention a / b | \|Δ log HR\| b → a (P) |
|---|---|---|---|---|---|---|
| P1 + CLMBR-T vs PS-Flags C = 1 (as reported) | 31 | 0.7 (−5.5 to 6.8) | 13/31 | .81 | 0.80 / 0.71 | 0.186 → 0.170 (.50) |
| P1 + CLMBR-T vs PS-Flags C = 0.1 | 32 | 7.7 (−0.1 to 15.8) | 20/32 | .085 | 0.80 / 0.72 | 0.218 → 0.170 (.44) |
| P1 + CLMBR-T vs PS-Flags C = 0.01 | 32 | 1.0 (−5.1 to 6.8) | 14/32 | .76 | 0.80 / 0.73 | 0.202 → 0.170 (.25) |
| **P1 + CLMBR-T vs PS-Flags CV-tuned** | 32 | **−1.5 (−7.5 to 4.4)** | 13/32 | .63 | 0.80 / 0.77 | 0.216 → 0.170 (.069) |
| P1 + CLMBR-T CV-tuned vs PS-Flags CV-tuned | 32 | −0.3 (−5.6 to 4.1) | 17/32 | .91 | 0.80 / 0.77 | 0.216 → 0.182 (.15) |

Under CV tuning, PS-Flags keeps PROTECT AF: retention 0.50 (vs < 0.02), median 0.79, minimum 0.41.

**Restricting the reported (C = 1) head-to-head to trials where PS-Flags retains well** (`review/restricted_h2h_by_flags_retention.csv`):

| PS-Flags retention | Trials | Relative reduction, 54 items (95% CI) |
|---|---|---|
| ≥ 0.5 | 27 | −1.1 (−7.2 to 5.1) |
| ≥ 0.7 | 19 | −2.6 (−9.2 to 4.6) |
| ≥ 0.9 | 11 | −5.1 (−13.1 to 5.8) |

The per-trial CLMBR-T advantage does not track PS-Flags retention: Spearman ρ = −0.29, P = .11.

**Judgement.**
- **What holds.** The qualitative conclusion, that there is no evidence PS-Demo + CLMBR-T balances better than PS-Flags, survives every fairer specification. Where PS-Flags behaves well, the flags are nominally *better*.
- **What does not hold.**
  - "*Equivalent*" is not supported: there is no margin, the CI is ±6%, and the point estimate moves from −5% to +8% with the regularisation choice or trial set.
  - The C = 1 arm silently drops PROTECT AF and trims 29% of the smaller arm on average.
  - Tuned PS-Flags agrees *less* well with the RCTs than P1 + CLMBR-T (0.216 vs 0.170, 21/32 closer, two-sided P = .069). That nominal agreement difference should be mentioned, not hidden. Like the other agreement gains, it is probably attenuation: the benchmark-permutation P for the C = 1 row is .97.
- **Is a fairer PS-Flags needed before reporting?** Not for the direction of the conclusion. It is needed for the write-up: paper2 should report the tuned PS-Flags as a prespecified-style sensitivity next to the C = 1 primary.

**Fix.**
1. Add a `Flags-CV` arm to `paper2_grid.py`: L2 with C chosen by 5-fold CV log-loss per trial, on `Cs = logspace(-4, 1, 11)`, with the chosen C logged. Run it at least for the main configuration, ideally for all 6, with the head-to-head and `Flags-CV + CLMBR` rows. Alternatively, cite `review/restricted_fair_flags_h2h.csv` as the sensitivity.
2. Report the retention-restricted rows above.
3. Replace "equivalent" (Verdict 2, §4) with "no detectable difference (0.7%, 95% CI −5.5 to 6.8; P = .81)".
4. State that the C = 1 PS-Flags overfits small trials: PROTECT AF has in-sample AUC 1.00 and fewer than 11 pairs.
5. In paper2.md, present PS-Flags C = 1 as the "same PS model for every rung" analysis, and CV-tuned as the fairness check.

### S2. "The ECG uniquely improves the echo domains" is overstated

**Evidence** (`headline_domains.csv`, `domains.csv`; P5, S32).
- **ECG domain gains vs base.** In the main configuration:
  - LV function 16.4%, q = .09;
  - LV structure 14.9%, q = .07;
  - only diastolic/LA reaches q < .05 (16.1%, q = .03).

  CLMBR-T improves LV structure by about as much (14.7%).
- **Direct domain contrast, CLMBR-T vs ECG.** In the main configuration:
  - LV function −18.4% (P = .027, q = .14);
  - diastolic/LA −18.4% (P = .016, q = .09).

  Neither survives FDR, and the ECG advantage does not replicate across configurations:
  - m13: LV function −4.6% (q = .78), diastolic/LA −6.1% (q = .54);
  - overlap: −4.6% (q = .66) and −4.6% (q = .38).

**Fix.**
- Reword Verdict 1 and the bottom line: "in the main configuration, the ECG's gains were concentrated in the echo domains (nominal; only diastolic/LA q < .05), and the direct ECG-vs-CLMBR-T domain differences were nominal and did not replicate under 1:3 matching or overlap weights".
- Add the `P5: CLMBR vs ECG` domain row (all configurations) to the Figure 3 heatmap source.

### S3. CLMBR-T vs ECG overall balance is reported for the main configuration only, which is the least favourable to CLMBR-T

**Evidence** (`sensitivity.csv`, P5, S32, 54 items, two-sided):

| Configuration | CLMBR-T vs ECG | q |
|---|---|---|
| main | 3.9% (P = .20) | .36 |
| m13 | 7.4% | .022 |
| overlap | 6.7% (2.9–10.6) | .012 |
| gbm | 8.1% | .036 |

HANDOFF §1.7 says to report every configuration and not to lead with one.

**Fix.** Add `P5: CLMBR vs ECG` (and `P5: ECG+CLMBR vs ECG`, which has q < .05 in cal01, m13, overlap and gbm) to the §5 all-configuration table and to Verdict 1: "CLMBR-T improved overall balance more than the ECG in 3 of 6 configurations (q < .05); in the main configuration the difference was not significant."

### S4. Label-stratified analysis: multiplicity, test statistic, and what κ = 1.0 means

**Evidence.**
- **(a) Multiplicity.** §3.4 runs, per set × configuration:
  - 5 arms × 3 endpoints of physiologic tests;
  - about 20 tested domain rows.

  None is FDR-adjusted. ECG P = .048 (S32) and .081 (S38) would not survive any correction. CLMBR-T .025 and both .004 might.
- **(b) Test statistic.** The permutation statistic is the difference in the *absolute* mean-|SMD| gain (`labels_physiologic.csv`, `diff_yes_minus_no`). The table, however, shows *relative* reductions (16.3% vs 5.7%) next to that P value.
- **(c) What κ = 1.0 means.** The two "independent" labellers were two runs of the same model on the same prompt and table (`TRIAL_LABELS.md`: "separate Claude agents"). κ = 1.0 is therefore expected and is not evidence of inter-rater reliability. The circularity is acknowledged; this shared-model point is not.

**My recomputation matches the reported values** (`review/restricted_recompute_labels.csv`, own permutation code, different seed):
- ECG: 16.3 (7.8–25.7) vs 5.7 (1.0–10.2), P = .048;
- CLMBR-T: P = .026;
- both: P = .005 (reported .004; Monte Carlo error);
- LV-systolic-function labels, ECG: 0.097 vs 0.011, P = .004 (reported .003).

**Fix.**
- Label §3.4 P values as nominal, or apply BH within a label family per set × configuration.
- State that the test is on the absolute gain.
- Describe the labellers as two runs of one LLM. Do not present κ = 1.0 as reliability in paper2.md.
- Optionally, have a clinician confirm the 11 "yes" labels.

### S5. The MIMIC side finding is correct but understated: it touches published paper1 numbers

**Evidence.** I verified the finding in the code:
- `scripts/v20/mimic_build_new.py` L119 joins diagnoses with `ad.admittime <= c2.admittime`, which includes the index admission;
- the hdPS panel uses L192–193 (`ad.hadm_id = pc.hadm_id OR ...`);
- the v1.5 audit fix (`v15/v15_mimic_auditfix.py` L58, L88) uses `ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id`;
- `mimic/flags/flag_check.csv` confirms 0 discordant patients for each convention.

The v20 `clinical` base also contains `dx` (`v15_analyze.GROUPS = [demo, dx, meds, labs_vitals, util]`). The MIMIC doc says to flag the issue "before the v20 ladder results for those trials are reused". However, `docs/paper/paper.md` line 91 already reports MIMIC hdPS 7.5% (−0.4 to 16.2) and PS-Clinical-lite 1.2% (−9.1 to 11.8) over the 7 cardiovascular trials, which include SOAP II and ELITE II. Index-admission discharge diagnoses can be post-treatment.

**Fix.**
- Tell the user explicitly that paper1's MIMIC hdPS and PS-Clinical-lite results (and the `meds` group, if it uses the same window: check) include index-admission codes for SOAP II and ELITE II.
- Re-run the v20 sparse, hdPS200 and clinical cells for SOAP II, ELITE II and PEPTIC with the earlier-admission window as a v21 sensitivity, importing v20 without editing it, before any of these numbers are reused in paper2.

### S6. The PI head-to-head agreement row uses unpaired means

**Evidence.** In the `P1+CLMBR vs Flags base` row, |Δ| 0.186 → 0.170 compares PS-Flags over 31 trials (PROTECT AF has no estimate) with P1 + CLMBR-T over 32. Paired over the same 31 trials, it is 0.186 → 0.174. `PAPER2_RESULTS` §7.6 discloses this, but the headline table does not.

**Fix.** Report paired means in §4 (or footnote the 31 vs 32), and apply the same to any Flags row used in paper2.md.

### S7. The retention difference (CLMBR-T trims about 10 points more) needs the available sensitivity in the doc

**Evidence** (`review/retention.py`; P5, S32, main).
- **Retention:** base 0.886, ECG 0.876, CLMBR-T 0.791, both 0.775. Balance is evaluated in different matched populations.
- **My checks suggest this is not an artefact:**
  - the CLMBR-T gain does not track its retention loss (Spearman ρ = 0.21, P = .24);
  - in the 15 trials where CLMBR-T loses ≤ 5 points of retention, CLMBR-T still gives 9.3% (2.0–16.5) and the ECG 6.9% (1.2–12.7);
  - overlap weights, which trim no one, keep the CLMBR-T gain (13.6%, q < .001).
- **IPTW.** The IPTW losses are weight-driven, not "retention" (IPTW does not trim). Median ESS fraction under IPTW, S32:
  - P5 base 0.72 and P5 + CLMBR-T 0.44;
  - PS-Flags base 0.18 (minimum 0.002) and hdPS200 0.34.

  So the claim in §5 that the IPTW "CLMBR-T beats Flags/hdPS" rows are a rich-PS weighting failure is **supported**. Verdict 4's "retention/weight-driven" should read "weight-driven (low ESS)".

**Fix.** Add these three numbers to §3 (Retention) and §7.9, and reword Verdict 4.

---

## NOTES

**N1. The gate is genuine.**
- **No self-comparison.** `gate()` reads `claude-v20-sens-primary32/restricted_cells.parquet` (mtime 2026-10-01) and `claude-v18-embed-compare/restricted_results_unsuppressed.parquet` (2026-09-28). These are separate directories from the v21 output, so the file is not compared with itself.
- **Matching.** It matches on trial within rung × configuration × arm, filtering k_pcs ∈ {0, 32} so that the sp32 ECG-dimension sweep is excluded.
- **Coverage.** It compares 66 columns (log HR, SE, n, n_t, n_c, n_pairs, ESS and 58 SMDs), and it requires all 38 trials to be present and the NaN patterns to agree.
- **Results.** sp32: 2,736 cells, max |Δ| 0. v18 CLMBR-T: 912 cells, max |Δ| 0, `ex58` strings identical.
- **The new Flags rung has no external reference.** I therefore re-executed PS-Flags base × main for all 32 S32 trials in a separate process (`review/fair_flags.py`). Max |Δ| was 0 for log HR and all 58 SMDs.

**N2. Spec compliance (HANDOFF §1, §3).** Everything specified is present:
- 5 rungs, 7 arms (CLMBR32 main-only, P1/P5), 6 configurations;
- all §3.2 within-rung and cross-rung contrasts (337 per set = 55 × 5 + 62);
- 54-item primary with the 4,000-resample bootstrap, the 58-item secondary and per-domain rows;
- the agreement endpoints, the 20,000-draw benchmark permutation, and BH across all configurations × contrasts within set (balance family = {m54, lt01_54, m58, lt01_58}; agreement = {absd, cons, bshuf});
- the labels analysis with 10,000 permutations and the Spearman check with placebo control;
- S32 primary and S38 sensitivity.

The logged deviations (§7) are reasonable:
- cross-rung rows are two-sided, as is the two-sided benchmark permutation;
- the Flags+CLMBR and clinical+CLMBR rows are deduplicated;
- the extra CLMBR32 rows were added;
- PROTECT AF cells that failed are recorded as NaN.

Placebo rows sit inside the FDR family, which is mildly conservative.

**N3. Leakage.**
- **Window.** The PS-Flags window (`condition_start_date < index`, observed minimum 1 day before index in every trial) matches CLMBR-T's (events before index midnight; `CLMBR_LEAKAGE.md` §a).
- **Exposure features.** `roles["exposure_features"]` contains only `rx_` features, so no dx flag was removed.
- **Exposure proxies.** I looked for dx-level exposure proxies (`review/restricted_flag_proxies.csv`: top 6 flags by arm SMD per trial). None appear. There are no pre-procedural Z01 codes in the LAAO or ablation trials. The separating codes are clinical (for example, acute-illness codes in CABANA and RAFT-AF, obesity/OSA in SUSTAIN-6, COVID/era codes U07).
- **Proxies of held-out values.** Some flags proxy held-out *values*: E66 for BMI; N18/N17 for creatinine/eGFR; I42/I50/R94 for the echo items. CLMBR-T (the same condition rows), hdPS200 and P5 (HF) see these too, so the head-to-head is symmetric, but "held-out" means "values not in the PS", not "unrelated to the PS". SMDs are computed on observed values only (`smd_components`, no missingness indicators), so CLMBR-T's measurement codes do not balance missingness directly.
- **Clinical masking.** The `ex58` masking for clinical carries into cross-rung contrasts through item pairing.

**N4. Permutation P values** use count/B, not (count+1)/(B+1). No zero P exists in any output, so this is cosmetic.

**N5. Minor numeric slips.**
- **LV_structure, "both".** PAPER2_RESULTS §6 says the LV_structure difference for "both" is −0.005. The CSV value is −0.0045, which prints as −0.004.
- **PEPTIC + ECG CI.** The MIMIC doc verdict gives 1.24–1.56; its table and the CSV give 1.24–1.55 (upper limit 1.5549).
- **Retention medians.** `PS_FLAGS.md` "median 0.78" is S38. PAPER2_RESULTS quotes the S32 mean, 0.713. State the set each time.

**N6. Plasmode.**
- **Gate.** `gate.csv` shows 1,080 rows with max |Δ| 0 for log HR, SE, truth, n, n_t and events. `summary_check.csv` shows 60/60 pooled rows with max |Δ| 1.4e-14.
- **Headline numbers match the CSVs.** I checked every number in §2–§5 against `pooled_*`, `added_value_p5`, `performance_*`, `null_check_p5`, `retention_p5` and `r2_p5`. Examples:
  - null-corrected % removed: P5 18.6, + ECG 27.8, + CLMBR-T 37.0, + both 42.6, CLMBR-T only 33.8, oracle 93.7;
  - added over P5: ECG 11.3 (MCSE 0.3), CLMBR-T 22.6, both 29.5, placebo 1.0;
  - coverage 51.2–76.9% (non-oracle) vs 94.4% (oracle).
- **R² cell count.** `r2_p5.csv` has 108 rows, including the excluded ROCKET-AF × LVEF cell; the doc says 107. The means are identical to 2 dp after excluding that cell.
- **Interpretation.** CLMBR-T's eGFR advantage (R² 0.34 vs ECG 0.05) is plausibly coded-record proxy information (CKD codes, nephrology care, lab orders). The doc already says so.

**N7. MIMIC.**
- **Gate.** `gate/gate.csv` shows 16 tables with max |Δ| 0, and `PASS` records a summary max difference of 0.
- **Headline numbers.** They follow from the per-trial rows: 6.6% [2.3, 12.8], 6/7; % balanced 45.6 → 51.6, 3/7; |Δ| 0.344 → 0.326, 4/7; permuted ECG 0.323; PEPTIC 1.51 → 1.39, permuted 1.60.
- **Small counts.** Minimum events 18 and minimum pairs 132, so there are no 1–10 counts.
- **Scope.** There are only 7 trials, and no FDR is applied; this is disclosed. The "Yale 9.0%" comparison is the 58-item value. The paper2 54-item value is 8.8%.

**N8. Dimension (64 vs 32 PCs).** Dimension does not drive the CLMBR-T gain:
- CLMBR-T 32 PCs gives 11.2% (6.5–16.0) vs 12.4% with 64;
- the 64-dimensional shuffled CLMBR-T gives 2.4% (−2.1 to 6.8).

P1 + CLMBR32 vs PS-Flags is −2.9% (−10.1 to 4.4), the same conclusion as with 64 PCs.

**N9. Agreement.** No S32 agreement q < .05 in any configuration (minimum q: absd .16, bshuf .10, cons .43). The three S38 GBM rows are correctly described as isolated. The paper1 pattern (m13 P = .007, permutation P = .037; GBM permutation P = .005) reproduces exactly under P5.

**N10. Privacy, other checks.**
- `git ls-files` has no CSV, parquet or other data files. Tracked extensions are py, md, png, pdf, yaml, sh, json, R, html, gitignore and svg.
- All files in `docs/v21` and `scripts/v21` are tracked; there are no untracked files there.
- `TRIAL_LABELS.json` is trial-level.
- `PS_FLAGS.md` patient counts are all ≥ 1,442, except the derived retention in B1. The `n_keys_not_in_roster` and `n_expo_removed` columns are 0.
- `mimic/flags/*.parquet` holds patient-level data without the `restricted_` prefix. It stays on raid0, but should be renamed for consistency.

**N11. Interpretive notes for paper2.md.**
- **PS-Clinical.** "CLMBR-T is somewhat worse than PS-Clinical" rests on −4.9% (−11.2 to 0.9) in main. It is significant only under GBM (−11.9%, q = .007). Say so.
- **The PI's timing hypothesis is not directly tested.** PS-Flags lacks timing, but CLMBR-T also differs by including drugs, procedures, measurement codes and visits. A null head-to-head therefore says that CLMBR-T's *total* extra content does not improve balance over the flags. It does not isolate timing.
- **Exposure-drug tokens.** CLMBR-T sees exposure-drug tokens for ≤ 5.9% of patients; PS-Flags sees no drugs.

---

## R. Independent recomputation (own code from `core/restricted_cells.parquet`)

**Method.** `review/recompute.py` does not import `paper2_grid` or the `sens_primary32` summary helpers. It uses its own versions of:
- the `ex58` masking and within-trial item pairing;
- an exact meet-in-the-middle sign-flip test;
- the trial bootstrap (4,000 resamples, seed 20261001);
- the comparator-cluster map read from `docs/v17/trial_selection.json`;
- the benchmark permutation (20,000 draws).

Output: `review/restricted_recompute_headline.csv`. All values match the reported ones.

| Quantity (S32, main unless stated) | Reported | Recomputed |
|---|---|---|
| P5 + ECG, 54-item relative reduction (CI); better; P; cluster P | 8.8 (4.4–13.3); 21/32; < .001; .002 | 8.85 (4.37–13.30); 21/32; .0003; .0022 |
| P5 + CLMBR-T | 12.4 (7.1–17.7); 23/32; cluster .002 | 12.37 (7.09–17.73); 23/32; .0023 |
| P5 + both | 13.5 (6.6–20.4); 23/32; cluster .004 | 13.54 (6.56–20.42); 23/32; .0042 |
| P5 % \|SMD\| < 0.1, base → ECG / CLMBR-T / both | 53.4 → 57.0 / 58.7 / 59.9 | 53.40 → 57.04 / 58.65 / 59.93 |
| P5 + ECG, 58-item (paper1 check) | 9.0 (4.8–13.3) | 9.02 (4.78–13.28) |
| P5 shuffled CLMBR-T | 2.4 (−2.1 to 6.8); 18/32; P .33 | 2.40 (−2.13 to 6.77); 18/32; .325 |
| **P1 + CLMBR-T vs PS-Flags**: balance; better; P | 0.7 (−5.5 to 6.8); 13/31; .81 | 0.75 (−5.47 to 6.82); 13/31; .814 |
| **P1 + CLMBR-T vs PS-Flags**: \|Δ\|; closer; P; permutation P | 0.186 → 0.170; 19/31; .50; .97 | 0.1858 → 0.1705; 19/31; .495; .974 |
| P1 + CLMBR-T vs PS-Flags, S38 | 0.2 (−5.4 to 5.5); 0.183 → 0.168, 23/37, .49, perm .82 | 0.16 (−5.39 to 5.54); 0.1826 → 0.1682, 23/37, .485, .822 |
| P1 + CLMBR-T vs PS-Flags, IPTW | 28.0 (14.0–39.2); 0.375 → 0.186, P .006, perm .97 | 28.04 (14.01–39.15); 0.3753 → 0.1857, .006, .965 |
| P5 + CLMBR-T vs clinical (S32 / S38) | −4.9 (−11.2 to 0.9) / −5.7 (−11.7 to −0.4) | −4.87 (−11.24 to 0.91) / −5.75 (−11.67 to −0.44) |
| hdPS200 + ECG | 7.6 (1.7–13.0); 22/32; .008 | 7.60 (1.75–13.03); 22/32; .0082 |
| **Agreement row: P5 + ECG**: \|Δ\|; closer; P; cluster; LOO; permutation P | 0.226 → 0.196; 20/32; .049; .20; .087; .70 | 0.2261 → 0.1956; 20/32; .0486; .197; .0873; .698 |
| P5 + CLMBR-T agreement | 0.166; 18/32; .030; .046; .059; perm .93 | 0.1663; 18/32; .0296; .0461; .0592; .934 |
| P5 + both agreement | 0.158; 18/32; .019; .10; .039; perm .94 | 0.1577; 18/32; .0193; .0995; .0386; .944 |
| P5 + ECG, m13 / gbm: P and permutation P | .007, .037 / .32, .005 | .0070, .0374 / .318, .0048 |
| S38 P5 + ECG / CLMBR-T / both | 9.0 (5.0–13.5) / 12.7 (8.0–17.6) / 14.5 (8.1–20.6) | 9.04 (4.97–13.47) / 12.73 (8.01–17.56) / 14.45 (8.07–20.63) |
| **Label: physiologic vs not, ECG** (relative reduction; P) | 16.3 (7.8–25.7) vs 5.7 (1.0–10.2); .048 | 16.30 (7.78–25.69) vs 5.66 (0.95–10.20); .048 |
| Label: LV-systolic-function domain, ECG / CLMBR-T | 0.097 vs 0.011, .003 / 0.079 vs −0.018, .002 | 0.097 vs 0.011, .004 / 0.079 vs −0.018, .005 |

## T. Traceability of PAPER2_RESULTS.md

I checked about 150 numbers against `headline.csv`, `sensitivity.csv`, `headline_domains.csv`, `domains.csv`, `q_counts.csv`, `labels_*.csv`, `per_trial.csv` and `gate_status.json`:
- all of the Verdict;
- §1 (gate, the paper1 spot check, lt01 53.4 → 59.9);
- the §3 balance, retention, domain and agreement tables;
- all eleven §4 rows;
- the §5 balance and agreement tables for all 6 configurations, q_counts, the S38 GBM rows and the S38 table;
- the §6 physiologic, domain and Spearman tables.

All match to the printed precision, with three exceptions:
- the LV_structure "both" difference (N5);
- the PS-Flags retention median, which mixes sets (N5);
- the paired-means issue in the PI agreement row (S6).

The count statement "55 contrasts per configuration, 62 for main, 337 per set" is correct.

## Files

| File | Content |
|---|---|
| `review/recompute.py`, `recompute_headline.csv` | independent headline recomputation |
| `review/recompute_labels.py`, `recompute_labels.csv` | independent label-stratified recomputation |
| `review/retention.py`, `h2h_by_flags_retention.csv` | retention, IPTW ESS, retention-restricted head-to-head |
| `review/fair_flags.py`, `fair_flags_summary.py`, `fair_flags_h2h.csv`, `restricted_fair_flags.parquet` | PS-Flags with C ∈ {1, 0.1, 0.01, CV} and CV-tuned P1 + CLMBR-T (restricted: trial-level SMDs, log HR) |
| `review/flag_proxies.py`, `flag_proxies.csv` | in-sample PS AUCs and top separating flags per trial (code-level SMDs only) |
