# v1.7 confirmatory analysis: 15 new trials (2026-09-27)

Fixed analysis of `docs/v16/V17_CONFIRMATION_PLAN.md` section C (commit 0e66e3c, fixed before any v1.7 result), blinded subsets and comparator clusters from `docs/v17/trial_selection.json` (commits 68a13a5 / f66e7a0). Script `scripts/v17/v17_confirm.py`; outputs (aggregates only) in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v17-confirm/` (`summary.csv`, `per_trial_new15.csv`, `results_*.csv`, `verify_*.csv`, `log_*.json`). All p-values are one-sided exact sign-flip tests (direction: ECG better), computed by full enumeration of all 2^k sign vectors.

## Verdict (plain language)

**Confirmation set = the 15 new trials, whose results nobody had seen.**

| Question | P1: demographics PS | P2: demographics + 6 diagnoses PS |
|---|---|---|
| **Balance** (primary: % of the 58 held-out covariates with \|SMD\| < 0.1) | **Confirmed at the pre-specified trial-level test, but not robust.** 52.4 → 58.3 %, 11/15 trials better, p = 0.033. | **Not confirmed.** 57.2 → 59.0 %, 9/15 trials better, p = 0.17. |
| Balance, secondary endpoints | Held-out covars2b non-proximal panel 67.5 → 72.2 %, p = 0.0005 (clustered p = 0.020). Balance C-statistic p = 0.006. Mean \|SMD\| p = 0.064. | Covars2b panel 72.6 → 75.4 %, p = 0.006 (clustered p = 0.043). Mean \|SMD\| and C-statistic show no gain (p = 0.66 and 0.26). |
| **Placebo-specific?** (primary balance) | Yes. ECG beats shufECG (p = 0.0003) and noise32 (p = 0.039); both placebos change balance by < 1 point. | No. ECG does not beat shufECG (p = 0.37). |
| **Clustered / leave-one-out** (primary balance) | Not significant. Clustered p = 0.078 (8 comparator clusters); leave-one-out max p = 0.064. By half: A p = 0.089, B p = 0.006. | Not significant (clustered p = 0.55). |
| **Emulation** (primary: \|Δlog HR\| vs RCT) | **Not confirmed.** 0.250 → 0.208, 8/15 trials closer, p = 0.074 (clustered p = 0.059; halves 0.44 / 0.25). Among the secondaries, z² (p = 0.032) and consistency (53 → 87 %, p = 0.031) improve. But the **benchmark shuffle fails** (p = 0.97): swapping the RCT benchmarks between trials gives an even larger mean gain (−0.068 against the observed −0.042). The HR shift is therefore not trial-specific. ECG pulls extreme HRs (e.g. DECLARE 1.81 → 1.36, AFFIRM 1.35 → 1.11) toward the typical benchmark. The "beats placebo" results (p = 0.0005 / 0.008) come mostly from shufECG making HRs *worse*. | **Null.** 0.192 → 0.193, 7/15 trials closer, p = 0.52. z², consistency and benchmark shuffle are all null. |

**Bottom line.**
- The confirmation set partly replicates the v1.6 **balance** finding. Adding ECG to a demographics-only PS improves held-out covariate balance, and does so more than the placebos. The gain is about 6 points, the same size as in v1.6 (6.4).
- The balance gain does not survive comparator clustering or leave-one-out at 0.05. It also does not replicate for the richer 6-diagnosis PS on the primary 58-variable panel, although it does on the secondary covars2b panel.
- The v1.6 **emulation** finding (HRs move closer to the RCT) is **not confirmed**. The primary \|Δ\| test is not significant for either PS, and the benchmark shuffle shows the P1 improvement is not specific to each trial's own RCT.
- The blinded high-fidelity / ECG-relevant subsets of the new trials are too small to test: S_both has 3 trials and S_both_high / S_fid_strict have 2 (AFFIRM and AF-CHF). The smallest attainable p is 0.125 with 3 trials and 0.25 with 2. Their directions favour ECG for P1 (S_both: balance 3/3 better, \|Δ\| 2/3 closer), but nothing is significant.
- No multiplicity adjustment was pre-specified. With 2 PSs × 2 primary endpoints, a Bonferroni threshold of 0.0125 would be met by none of the four confirmation-set primary tests.

**All 33 trials (18 v1.6 + 15 new; not out-of-sample for the 18):**
- P1 balance: 53.1 → 59.3 %, 25/33, p = 0.0001, clustered p = 0.0005 (13 clusters).
- P1 \|Δ\|: 0.258 → 0.208, 22/33, p = 0.004, clustered p = 0.034, but the benchmark-shuffle p = 0.37.
- P2 balance: p = 0.0075 (clustered p = 0.074).
- P2 \|Δ\|: p = 0.078 (ECG does not beat shufECG, p = 0.44).

## Provenance and reproduction check
- **Design.** The design is exactly S1 `r1_demo` (P1) and S10 caliper 0.2 (P2):
  - arms base, +ECG32, +shufECG, +noise32, plus unmatched;
  - `E.run_cell(..., estimator=("match", 0.2, 1))`, L2 C = 1;
  - halves full / A / B from `s1_ladder.halves`.
- **Half-split seed.** The seed is 16060 + i, where i is the trial's position in `E.TRIALS + list(v13_common.V17)`:
  - the v1.6 trials keep i = 0–17 (their v1.6 seeds);
  - the new trials get i = 18–32 (leader 18, sustain6 19, rewind 20, declare 21, canvas 22, tecos 23, carmelina 24, valiant 25, insight 26, affirm 27, af-chf 28, precision 29, amplify 30, lodestar 31, prove-it 32).
- **Reproduction check.** The script was run first on COMET and ARISTOTLE, then on all 18 v1.6 trials. It reproduces `claude-v16-s1-ladder/results.csv` (r1_demo and unmatched) and `claude-v16-s10-demo6/results.csv` (caliper 0.2) **exactly**, with max deviation 0.0. The check covered log HR, SE, pairs, mean \|SMD\|, C-statistic and all 58 per-variable \|SMD\|, for every arm and half (`verify_verify2.csv`, `verify_all.csv`).
- **Summary checks.** The v1.6 18-trial summaries recomputed with the new test code match `V17_BLINDED_SUBSET_EXISTING18.md`:
  - P1 balance 53.8 → 60.2, p = 0.0001;
  - P1 \|Δ\| 0.265 → 0.208, p = 0.017 (vs shuf 0.041, vs noise 0.060);
  - P2 \|Δ\| p = 0.006 (vs shuf 0.48).
- **Data sources.** For the v1.6 trials, 58-panel, HR and C-statistic numbers come from the v1.6 results files. The covars2b secondary panel is new for all 33 trials, computed with the same code.

## Deviations
None in the analysis design. Implementation choices the plan did not spell out are listed below; each was fixed in the script before any new-trial result was viewed.
1. **HF column.** hf_any_365 is absent from `claude-v17-covars2b/insight.parquet`, so INSIGHT uses elx_chf. This is the S10 rule, which v1.6 already applied to LIFE, ALLHAT, ONTARGET, VALUE and ASCOT. Every other P2 column (hypertension_v11, t2d, cad_ihd, obesity, atrial_fibrillation) was present in all 15 new trials. No P2 cell was NaN-filled in any new trial.
2. **Secondary balance panel.** The covars2b non-proximal panel follows the S8/S9 rules:
   - `S6.load_extra`: status kept*, no exposure leak, timing pre_index;
   - minus the ecg_proximal block, `S8.EXTRA_PROX`, `S8.NOT_PREINDEX`, zip_* and index_context;
   - per PS, `S6.excluded_extra` and `S8.composite_overlap` using the PS column names. For P1 these are T.demo; for P2, T.demo + the six columns.

   There are 318–340 panel variables per trial before the per-PS drops. v1.6 had no P2 run on this panel.
3. **Benchmark shuffle.** (rb, rs) are permuted jointly within each analysed set, 20,000 draws with `default_rng(0)`. p = P(null mean ≤ observed mean) for ECG − base. S10 used 5,000 draws.
4. **Consistency test.** Consistency is a per-trial indicator (\|z\| < 1.96). The test is a one-sided sign-flip on the ECG − base indicator differences.
5. **Clustering.** Clustered tests use the `trial_selection.json` comparator clusters (not `audit_v16.CLUSTER`), with cluster means of the per-trial differences. Clustered p is also reported for ECG vs each placebo.
6. **Subsets within (ii).** These are `subsets.all_trials` restricted to the 33 analysed trials. Within (i), they are `subsets.v17_new_15`.

## Caveats
- **Correlated DPP-4i-comparator trials.**
  - 5 of the 15 new trials (LEADER, SUSTAIN-6, REWIND, DECLARE, CANVAS) share the DPP-4i comparator pool with each other and with EMPA-REG and EMPEROR-Preserved (cluster C_DPP4I_PROXY).
  - TECOS and CARMELINA share sulfonylurea and DPP-4i arms with CAROLINA.
  - The trial-level sign-flip treats these trials as independent. The clustered test (8 clusters in the confirmation set) is the conservative reading, and it is not significant for either primary endpoint.
- **AFFIRM ⊃ EAST-AFNET 4.** AFFIRM contains most EAST-AFNET 4 records, and AF-CHF uses the same sequential add-on design. In set (ii) these three are effectively one piece of evidence counted up to three times; they share one cluster (C_AF_RHYTHM_AAD).
  - AFFIRM and AF-CHF are the only S_fid_strict / S_both_high new trials. The high-fidelity new-trial evidence is therefore essentially one design replicated twice.
- **Outcome-poor or imprecise trials.**
  - Base SE of log HR is ≥ 0.14 in LEADER, SUSTAIN-6, CANVAS, VALIANT, INSIGHT and CARMELINA (0.13).
  - \|Δlog HR\| changes of 0.03–0.10 in these trials are well inside sampling noise.
  - AMPLIFY's VTE outcome has low specificity (6-month horizon).
  - LODESTAR and PROVE IT omit revascularisation from the composite.
- **Emulation-fidelity caveats.** Placebo-proxy trials (7 of 15) have poor comparator fidelity by the blinded rule; only 5 of 15 new trials pass S_fid. The confirmation set is therefore weighted toward low-fidelity emulations, where the v1.6 emulation signal was already weakest.
- **Record overlap.** LEADER–EMPA-REG 0.58, VALIANT–ONTARGET 0.61 and INSIGHT–ALLHAT 0.63 (same-record share) weaken the independence of set (ii) from the v1.6 trials.
- **Exploratory v1.6 origin.** The endpoints and PSs were chosen after v1.6 results were seen. Only set (i) is out-of-sample.

## Full tables
Set = new15 (confirmation), all33, or old18 (v1.6 reference). Arm columns are across-trial means. "k better" = trials where ECG improves on base. "Cluster p" = sign-flip over comparator-cluster means (number of clusters in parentheses). The minimum attainable p is 2^-n.

#### P1 — % 58-panel |SMD|<0.1 (primary)

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 52.4 | 58.3 | 52.0 | 53.2 | 11/15 | 0.033 | 0.0003 | 0.039 | 0.078 (8) | 0.012 / 0.055 | 0.064 | 0.089 / 0.006 |
| new15 | S_fid | 5 | 58.6 | 61.4 | 55.2 | 57.6 | 4/5 | 0.281 | 0.094 | 0.250 | 0.438 (4) | 0.188 / 0.312 | 0.562 | 0.062 / 0.031 |
| new15 | S_fid_strict | 2 | 62.1 | 69.8 | 59.5 | 60.3 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.500 / 0.250 |
| new15 | S_ecg | 8 | 57.4 | 61.5 | 54.8 | 59.3 | 5/8 | 0.156 | 0.008 | 0.273 | 0.219 (5) | 0.062 / 0.281 | 0.312 | 0.156 / 0.012 |
| new15 | S_both | 3 | 59.8 | 67.2 | 56.3 | 58.6 | 3/3 | 0.125 | 0.125 | 0.125 | 0.250 (2) | 0.250 / 0.250 | 0.250 | 0.250 / 0.125 |
| new15 | S_both_high | 2 | 62.1 | 69.8 | 59.5 | 60.3 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.500 / 0.250 |
| all33 | all | 33 | 53.1 | 59.3 | 52.5 | 53.8 | 25/33 | 0.0001 | <0.0001 | 0.0004 | 0.0005 (13) | 0.0001 / 0.0006 | 0.0002 | 0.0002 / <0.0001 |
| all33 | S_fid | 14 | 54.0 | 59.9 | 50.0 | 53.6 | 11/14 | 0.010 | 0.0005 | 0.005 | 0.109 (8) | 0.027 / 0.035 | 0.020 | 0.006 / 0.005 |
| all33 | S_fid_strict | 6 | 50.9 | 59.0 | 47.8 | 53.3 | 6/6 | 0.016 | 0.016 | 0.125 | 0.125 (3) | 0.125 / 0.250 | 0.031 | 0.188 / 0.094 |
| all33 | S_ecg | 23 | 54.0 | 59.8 | 51.7 | 55.0 | 17/23 | 0.001 | <0.0001 | 0.007 | 0.012 (11) | 0.0010 / 0.011 | 0.002 | 0.001 / 0.0001 |
| all33 | S_both | 11 | 54.4 | 62.7 | 49.9 | 54.8 | 10/11 | 0.0010 | 0.0005 | 0.004 | 0.062 (5) | 0.031 / 0.031 | 0.002 | 0.018 / 0.011 |
| all33 | S_both_high | 5 | 58.3 | 66.9 | 53.1 | 55.5 | 4/5 | 0.062 | 0.031 | 0.031 | 0.500 (2) | 0.250 / 0.250 | 0.125 | 0.062 / 0.031 |
| old18 | all | 18 | 53.8 | 60.2 | 52.8 | 54.2 | 14/18 | 0.0001 | 0.0005 | 0.001 | 0.008 (10) | 0.008 / 0.003 | 0.0002 | 0.0006 / 0.002 |

#### P1 — % covars2b non-prox <0.1

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 67.5 | 72.2 | 68.0 | 67.8 | 13/15 | 0.0005 | 0.0010 | 0.0005 | 0.020 (8) | 0.016 / 0.027 | 0.0010 | 0.014 / 0.112 |
| new15 | S_fid | 5 | 68.2 | 72.6 | 67.9 | 69.0 | 4/5 | 0.094 | 0.062 | 0.125 | 0.188 (4) | 0.125 / 0.250 | 0.188 | 0.062 / 0.125 |
| new15 | S_fid_strict | 2 | 69.5 | 75.9 | 68.6 | 68.9 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 |
| new15 | S_ecg | 8 | 69.1 | 75.7 | 71.0 | 70.2 | 8/8 | 0.004 | 0.008 | 0.004 | 0.031 (5) | 0.031 / 0.031 | 0.008 | 0.031 / 0.062 |
| new15 | S_both | 3 | 69.8 | 77.4 | 70.3 | 70.7 | 3/3 | 0.125 | 0.125 | 0.125 | 0.250 (2) | 0.250 / 0.250 | 0.250 | 0.125 / 0.375 |
| new15 | S_both_high | 2 | 69.5 | 75.9 | 68.6 | 68.9 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 |
| all33 | all | 33 | 64.0 | 69.0 | 64.0 | 64.4 | 28/33 | <0.0001 | <0.0001 | <0.0001 | 0.0002 (13) | 0.0007 / 0.0005 | <0.0001 | <0.0001 / 0.0004 |
| all33 | S_fid | 14 | 59.6 | 65.3 | 59.0 | 60.2 | 13/14 | 0.0002 | 0.0001 | 0.0002 | 0.016 (8) | 0.008 / 0.016 | 0.0005 | 0.0001 / 0.002 |
| all33 | S_fid_strict | 6 | 58.8 | 65.6 | 57.8 | 59.8 | 6/6 | 0.016 | 0.016 | 0.016 | 0.125 (3) | 0.125 / 0.125 | 0.031 | 0.016 / 0.047 |
| all33 | S_ecg | 23 | 63.7 | 69.7 | 64.1 | 64.7 | 20/23 | <0.0001 | <0.0001 | <0.0001 | 0.0010 (11) | 0.001 / 0.0010 | <0.0001 | <0.0001 / 0.0002 |
| all33 | S_both | 11 | 58.4 | 65.5 | 57.8 | 59.5 | 11/11 | 0.0005 | 0.0005 | 0.0005 | 0.031 (5) | 0.031 / 0.031 | 0.0010 | 0.0005 / 0.008 |
| all33 | S_both_high | 5 | 62.3 | 69.0 | 61.8 | 62.5 | 5/5 | 0.031 | 0.031 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.062 | 0.031 / 0.031 |
| old18 | all | 18 | 61.0 | 66.3 | 60.7 | 61.6 | 15/18 | <0.0001 | <0.0001 | <0.0001 | 0.002 (10) | 0.002 / 0.003 | 0.0001 | <0.0001 / 0.0001 |

#### P1 — mean |SMD| (58)

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 0.133 | 0.123 | 0.135 | 0.136 | 12/15 | 0.064 | 0.006 | 0.039 | 0.277 (8) | 0.047 / 0.090 | 0.118 | 0.021 / 0.004 |
| new15 | S_fid | 5 | 0.108 | 0.111 | 0.121 | 0.112 | 4/5 | 0.531 | 0.125 | 0.438 | 0.562 (4) | 0.250 / 0.625 | 0.562 | 0.125 / 0.062 |
| new15 | S_fid_strict | 2 | 0.093 | 0.081 | 0.101 | 0.094 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.500 / 0.250 |
| new15 | S_ecg | 8 | 0.116 | 0.111 | 0.119 | 0.121 | 6/8 | 0.172 | 0.059 | 0.164 | 0.250 (5) | 0.094 / 0.188 | 0.273 | 0.203 / 0.023 |
| new15 | S_both | 3 | 0.100 | 0.091 | 0.111 | 0.103 | 3/3 | 0.125 | 0.125 | 0.125 | 0.250 (2) | 0.250 / 0.250 | 0.250 | 0.250 / 0.125 |
| new15 | S_both_high | 2 | 0.093 | 0.081 | 0.101 | 0.094 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.500 / 0.250 |
| all33 | all | 33 | 0.134 | 0.117 | 0.137 | 0.135 | 29/33 | <0.0001 | <0.0001 | <0.0001 | 0.0006 (13) | 0.0007 / 0.0004 | 0.0001 | 0.0001 / <0.0001 |
| all33 | S_fid | 14 | 0.134 | 0.119 | 0.145 | 0.137 | 12/14 | 0.024 | 0.0005 | 0.003 | 0.270 (8) | 0.031 / 0.055 | 0.048 | 0.017 / 0.001 |
| all33 | S_fid_strict | 6 | 0.146 | 0.121 | 0.155 | 0.142 | 6/6 | 0.016 | 0.016 | 0.016 | 0.125 (3) | 0.125 / 0.125 | 0.031 | 0.328 / 0.094 |
| all33 | S_ecg | 23 | 0.133 | 0.114 | 0.138 | 0.134 | 21/23 | <0.0001 | <0.0001 | 0.0001 | 0.002 (11) | 0.001 / 0.0010 | 0.0001 | 0.004 / <0.0001 |
| all33 | S_both | 11 | 0.136 | 0.113 | 0.147 | 0.137 | 11/11 | 0.0005 | 0.0005 | 0.0005 | 0.031 (5) | 0.031 / 0.031 | 0.0010 | 0.042 / 0.003 |
| all33 | S_both_high | 5 | 0.123 | 0.100 | 0.132 | 0.128 | 5/5 | 0.031 | 0.031 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.062 | 0.062 / 0.031 |
| old18 | all | 18 | 0.135 | 0.111 | 0.140 | 0.134 | 17/18 | <0.0001 | <0.0001 | <0.0001 | 0.002 (10) | 0.002 / 0.0010 | <0.0001 | 0.002 / 0.0003 |

#### P1 — balance C-stat

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 0.666 | 0.648 | 0.653 | 0.661 | 11/15 | 0.006 | 0.209 | 0.070 | 0.145 (8) | 0.730 / 0.387 | 0.012 | 0.365 / 0.231 |
| new15 | S_fid | 5 | 0.689 | 0.686 | 0.687 | 0.686 | 3/5 | 0.406 | 0.500 | 0.531 | 0.625 (4) | 0.688 / 0.562 | 0.625 | 0.188 / 0.344 |
| new15 | S_fid_strict | 2 | 0.746 | 0.732 | 0.751 | 0.757 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.500 |
| new15 | S_ecg | 8 | 0.666 | 0.640 | 0.651 | 0.667 | 8/8 | 0.004 | 0.051 | 0.004 | 0.031 (5) | 0.156 / 0.031 | 0.008 | 0.547 / 0.531 |
| new15 | S_both | 3 | 0.691 | 0.678 | 0.686 | 0.704 | 3/3 | 0.125 | 0.375 | 0.125 | 0.250 (2) | 0.500 / 0.250 | 0.250 | 0.125 / 0.750 |
| new15 | S_both_high | 2 | 0.746 | 0.732 | 0.751 | 0.757 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.500 |
| all33 | all | 33 | 0.682 | 0.664 | 0.680 | 0.683 | 26/33 | <0.0001 | 0.0002 | 0.0002 | 0.002 (13) | 0.028 / 0.0002 | 0.0001 | 0.056 / 0.0008 |
| all33 | S_fid | 14 | 0.704 | 0.695 | 0.711 | 0.711 | 10/14 | 0.066 | 0.014 | 0.056 | 0.219 (8) | 0.121 / 0.238 | 0.132 | 0.086 / 0.015 |
| all33 | S_fid_strict | 6 | 0.712 | 0.708 | 0.724 | 0.727 | 4/6 | 0.266 | 0.031 | 0.031 | 0.625 (3) | 0.250 / 0.250 | 0.438 | 0.281 / 0.031 |
| all33 | S_ecg | 23 | 0.696 | 0.675 | 0.696 | 0.700 | 20/23 | 0.0001 | <0.0001 | <0.0001 | 0.0010 (11) | 0.002 / 0.0005 | 0.0001 | 0.100 / 0.004 |
| all33 | S_both | 11 | 0.719 | 0.705 | 0.727 | 0.731 | 9/11 | 0.028 | 0.005 | 0.001 | 0.094 (5) | 0.094 / 0.031 | 0.057 | 0.032 / 0.035 |
| all33 | S_both_high | 5 | 0.770 | 0.742 | 0.779 | 0.781 | 5/5 | 0.031 | 0.031 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.062 | 0.031 / 0.062 |
| old18 | all | 18 | 0.696 | 0.678 | 0.702 | 0.701 | 15/18 | 0.002 | <0.0001 | <0.0001 | 0.003 (10) | 0.0010 / 0.003 | 0.003 | 0.045 / 0.0001 |

#### P1 — |Δlog HR| vs RCT (primary)

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B | bench-shuffle null mean / p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 0.250 | 0.208 | 0.305 | 0.264 | 8/15 | 0.074 | 0.0005 | 0.008 | 0.059 (8) | 0.008 / 0.027 | 0.146 | 0.441 / 0.253 | -0.068 (obs -0.042) / 0.971 |
| new15 | S_fid | 5 | 0.274 | 0.196 | 0.355 | 0.254 | 4/5 | 0.062 | 0.031 | 0.125 | 0.125 (4) | 0.062 / 0.250 | 0.125 | 0.500 / 0.156 | -0.091 (obs -0.078) / 1.000 |
| new15 | S_fid_strict | 2 | 0.224 | 0.106 | 0.205 | 0.228 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 | -0.137 (obs -0.118) / 1.000 |
| new15 | S_ecg | 8 | 0.241 | 0.215 | 0.280 | 0.265 | 4/8 | 0.223 | 0.016 | 0.031 | 0.375 (5) | 0.094 / 0.188 | 0.359 | 0.910 / 0.336 | -0.052 (obs -0.026) / 0.969 |
| new15 | S_both | 3 | 0.209 | 0.143 | 0.245 | 0.216 | 2/3 | 0.250 | 0.125 | 0.250 | 0.500 (2) | 0.250 / 0.500 | 0.500 | 0.625 / 0.250 | -0.083 (obs -0.066) / 1.000 |
| new15 | S_both_high | 2 | 0.224 | 0.106 | 0.205 | 0.228 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 | -0.137 (obs -0.118) / 1.000 |
| all33 | all | 33 | 0.258 | 0.208 | 0.286 | 0.261 | 22/33 | 0.004 | 0.0007 | 0.005 | 0.034 (13) | 0.012 / 0.038 | 0.009 | 0.116 / 0.056 | -0.047 (obs -0.050) / 0.374 |
| all33 | S_fid | 14 | 0.335 | 0.244 | 0.376 | 0.329 | 12/14 | 0.002 | 0.0009 | 0.009 | 0.023 (8) | 0.016 / 0.039 | 0.004 | 0.158 / 0.049 | -0.070 (obs -0.091) / 0.128 |
| all33 | S_fid_strict | 6 | 0.299 | 0.195 | 0.289 | 0.283 | 6/6 | 0.016 | 0.031 | 0.062 | 0.125 (3) | 0.125 / 0.125 | 0.031 | 0.562 / 0.156 | -0.073 (obs -0.105) / 0.102 |
| all33 | S_ecg | 23 | 0.264 | 0.211 | 0.281 | 0.269 | 16/23 | 0.012 | 0.007 | 0.014 | 0.067 (11) | 0.050 / 0.059 | 0.023 | 0.281 / 0.030 | -0.037 (obs -0.053) / 0.154 |
| all33 | S_both | 11 | 0.358 | 0.253 | 0.382 | 0.361 | 10/11 | 0.002 | 0.002 | 0.008 | 0.031 (5) | 0.062 / 0.031 | 0.005 | 0.169 / 0.021 | -0.070 (obs -0.104) / 0.054 |
| all33 | S_both_high | 5 | 0.471 | 0.317 | 0.507 | 0.501 | 5/5 | 0.031 | 0.031 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.062 | 0.031 / 0.031 | -0.129 (obs -0.154) / 0.301 |
| old18 | all | 18 | 0.265 | 0.208 | 0.269 | 0.259 | 14/18 | 0.017 | 0.041 | 0.060 | 0.119 (10) | 0.147 / 0.163 | 0.033 | 0.053 / 0.063 | -0.027 (obs -0.057) / 0.041 |

#### P1 — z² vs RCT

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B | bench-shuffle null mean / p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 5.99 | 3.28 | 7.43 | 6.31 | 8/15 | 0.032 | 0.0006 | 0.005 | 0.023 (8) | 0.008 / 0.039 | 0.065 | 0.361 / 0.072 | -3.72 (obs -2.711) / 0.877 |
| new15 | S_fid | 5 | 3.67 | 1.81 | 5.43 | 3.21 | 4/5 | 0.062 | 0.031 | 0.125 | 0.125 (4) | 0.062 / 0.250 | 0.125 | 0.250 / 0.156 | -3.33 (obs -1.863) / 0.992 |
| new15 | S_fid_strict | 2 | 3.94 | 0.93 | 3.25 | 4.00 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 | -3.25 (obs -3.007) / 1.000 |
| new15 | S_ecg | 8 | 3.39 | 2.48 | 4.23 | 3.82 | 4/8 | 0.141 | 0.016 | 0.031 | 0.219 (5) | 0.062 / 0.125 | 0.250 | 0.848 / 0.188 | -3.36 (obs -0.911) / 0.990 |
| new15 | S_both | 3 | 2.96 | 1.15 | 3.32 | 3.10 | 2/3 | 0.250 | 0.125 | 0.250 | 0.500 (2) | 0.250 / 0.500 | 0.500 | 0.375 / 0.250 | -4.29 (obs -1.810) / 1.000 |
| new15 | S_both_high | 2 | 3.94 | 0.93 | 3.25 | 4.00 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 | -3.25 (obs -3.007) / 1.000 |
| all33 | all | 33 | 8.16 | 4.93 | 9.36 | 8.76 | 22/33 | 0.0003 | 0.0002 | 0.0005 | 0.003 (13) | 0.004 / 0.006 | 0.0007 | 0.017 / 0.010 | -3.76 (obs -3.228) / 0.797 |
| all33 | S_fid | 14 | 9.57 | 5.17 | 11.90 | 11.04 | 12/14 | 0.0007 | 0.0005 | 0.002 | 0.012 (8) | 0.016 / 0.027 | 0.001 | 0.043 / 0.029 | -5.72 (obs -4.399) / 0.851 |
| all33 | S_fid_strict | 6 | 6.06 | 3.38 | 5.78 | 6.79 | 6/6 | 0.016 | 0.031 | 0.031 | 0.125 (3) | 0.125 / 0.125 | 0.031 | 0.312 / 0.156 | -4.02 (obs -2.678) / 0.784 |
| all33 | S_ecg | 23 | 7.27 | 4.50 | 8.52 | 8.27 | 16/23 | 0.004 | 0.003 | 0.003 | 0.024 (11) | 0.021 / 0.023 | 0.009 | 0.078 / 0.011 | -3.87 (obs -2.776) / 0.883 |
| all33 | S_both | 11 | 11.32 | 6.05 | 13.57 | 13.44 | 10/11 | 0.002 | 0.002 | 0.003 | 0.031 (5) | 0.062 / 0.031 | 0.005 | 0.047 / 0.024 | -7.12 (obs -5.272) / 0.856 |
| all33 | S_both_high | 5 | 18.94 | 9.28 | 23.52 | 22.73 | 5/5 | 0.031 | 0.031 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.062 | 0.031 / 0.031 | -12.84 (obs -9.654) / 0.866 |
| old18 | all | 18 | 9.97 | 6.31 | 10.98 | 10.81 | 14/18 | 0.003 | 0.010 | 0.008 | 0.042 (10) | 0.071 / 0.062 | 0.006 | 0.016 / 0.041 | -3.59 (obs -3.658) / 0.479 |

#### P1 — % consistent (|z|<1.96)

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 53.3 | 86.7 | 60.0 | 60.0 | 5/15 | 0.031 | 0.062 | 0.062 | 0.031 (8) | 0.062 / 0.125 | 0.062 | 1.000 / 0.125 |
| new15 | S_fid | 5 | 40.0 | 100.0 | 40.0 | 60.0 | 3/5 | 0.125 | 0.125 | 0.250 | 0.125 (4) | 0.125 / 0.250 | 0.250 | 1.000 / 0.250 |
| new15 | S_fid_strict | 2 | 50.0 | 100.0 | 50.0 | 50.0 | 1/2 | 0.500 | 0.500 | 0.500 | 0.500 (1) | 0.500 / 0.500 | 1.000 | 1.000 / 0.500 |
| new15 | S_ecg | 8 | 50.0 | 87.5 | 62.5 | 50.0 | 3/8 | 0.125 | 0.250 | 0.125 | 0.125 (5) | 0.250 / 0.250 | 0.250 | 1.000 / 0.250 |
| new15 | S_both | 3 | 66.7 | 100.0 | 66.7 | 66.7 | 1/3 | 0.500 | 0.500 | 0.500 | 0.500 (2) | 0.500 / 0.500 | 1.000 | 1.000 / 0.500 |
| new15 | S_both_high | 2 | 50.0 | 100.0 | 50.0 | 50.0 | 1/2 | 0.500 | 0.500 | 0.500 | 0.500 (1) | 0.500 / 0.500 | 1.000 | 1.000 / 0.500 |
| all33 | all | 33 | 54.5 | 72.7 | 54.5 | 57.6 | 7/33 | 0.035 | 0.035 | 0.062 | 0.031 (13) | 0.031 / 0.062 | 0.062 | 0.500 / 0.031 |
| all33 | S_fid | 14 | 42.9 | 78.6 | 42.9 | 50.0 | 5/14 | 0.031 | 0.031 | 0.062 | 0.062 (8) | 0.062 / 0.125 | 0.062 | 0.500 / 0.125 |
| all33 | S_fid_strict | 6 | 50.0 | 83.3 | 50.0 | 50.0 | 2/6 | 0.250 | 0.250 | 0.250 | 0.250 (3) | 0.250 / 0.250 | 0.500 | 1.000 / 0.500 |
| all33 | S_ecg | 23 | 56.5 | 73.9 | 56.5 | 56.5 | 5/23 | 0.109 | 0.109 | 0.109 | 0.125 (11) | 0.062 / 0.125 | 0.188 | 0.500 / 0.125 |
| all33 | S_both | 11 | 45.5 | 72.7 | 45.5 | 45.5 | 3/11 | 0.125 | 0.125 | 0.125 | 0.250 (5) | 0.250 / 0.250 | 0.250 | 0.500 / 0.250 |
| all33 | S_both_high | 5 | 20.0 | 60.0 | 20.0 | 20.0 | 2/5 | 0.250 | 0.250 | 0.250 | 0.500 (2) | 0.500 / 0.500 | 0.500 | 0.500 / 0.250 |
| old18 | all | 18 | 55.6 | 61.1 | 50.0 | 55.6 | 2/18 | 0.500 | 0.312 | 0.500 | 0.500 (10) | 0.312 / 0.500 | 0.750 | 0.500 / 0.250 |

#### P2 — % 58-panel |SMD|<0.1 (primary)

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 57.2 | 59.0 | 58.3 | 54.3 | 9/15 | 0.172 | 0.372 | 0.020 | 0.555 (8) | 0.594 / 0.293 | 0.316 | 0.087 / 0.193 |
| new15 | S_fid | 5 | 63.8 | 65.9 | 64.1 | 59.0 | 2/5 | 0.375 | 0.500 | 0.219 | 0.562 (4) | 0.750 / 0.438 | 0.750 | 0.750 / 0.125 |
| new15 | S_fid_strict | 2 | 65.5 | 77.6 | 66.4 | 57.8 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.500 / 0.500 |
| new15 | S_ecg | 8 | 60.8 | 63.6 | 63.8 | 57.0 | 5/8 | 0.172 | 0.555 | 0.039 | 0.375 (5) | 0.688 / 0.188 | 0.344 | 0.102 / 0.430 |
| new15 | S_both | 3 | 62.6 | 69.5 | 66.7 | 57.5 | 2/3 | 0.250 | 0.500 | 0.250 | 0.500 (2) | 0.750 / 0.500 | 0.500 | 0.625 / 0.375 |
| new15 | S_both_high | 2 | 65.5 | 77.6 | 66.4 | 57.8 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.500 / 0.500 |
| all33 | all | 33 | 58.9 | 61.7 | 59.1 | 57.4 | 23/33 | 0.007 | 0.025 | 0.0003 | 0.074 (13) | 0.048 / 0.102 | 0.014 | 0.005 / 0.003 |
| all33 | S_fid | 14 | 61.1 | 64.6 | 61.2 | 58.9 | 9/14 | 0.059 | 0.109 | 0.019 | 0.129 (8) | 0.219 / 0.082 | 0.114 | 0.094 / 0.003 |
| all33 | S_fid_strict | 6 | 59.0 | 63.6 | 59.6 | 55.6 | 4/6 | 0.156 | 0.156 | 0.078 | 0.250 (3) | 0.250 / 0.125 | 0.312 | 0.094 / 0.078 |
| all33 | S_ecg | 23 | 59.9 | 62.9 | 60.0 | 58.1 | 16/23 | 0.014 | 0.061 | 0.001 | 0.014 (11) | 0.061 / 0.0010 | 0.027 | 0.015 / 0.006 |
| all33 | S_both | 11 | 62.0 | 66.7 | 62.1 | 60.1 | 8/11 | 0.035 | 0.090 | 0.025 | 0.062 (5) | 0.188 / 0.031 | 0.070 | 0.111 / 0.006 |
| all33 | S_both_high | 5 | 64.5 | 73.8 | 61.4 | 60.7 | 5/5 | 0.031 | 0.031 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.062 | 0.312 / 0.062 |
| old18 | all | 18 | 60.4 | 64.0 | 59.7 | 60.0 | 14/18 | 0.008 | 0.012 | 0.003 | 0.008 (10) | 0.018 / 0.0010 | 0.017 | 0.018 / 0.0007 |

#### P2 — % covars2b non-prox <0.1

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 72.6 | 75.4 | 72.8 | 72.8 | 12/15 | 0.006 | 0.029 | 0.0006 | 0.043 (8) | 0.039 / 0.016 | 0.011 | 0.120 / 0.306 |
| new15 | S_fid | 5 | 75.0 | 78.4 | 73.8 | 74.9 | 5/5 | 0.031 | 0.031 | 0.031 | 0.062 (4) | 0.062 / 0.062 | 0.062 | 0.156 / 0.188 |
| new15 | S_fid_strict | 2 | 76.8 | 80.0 | 77.1 | 77.4 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 |
| new15 | S_ecg | 8 | 74.0 | 77.2 | 73.4 | 75.0 | 6/8 | 0.027 | 0.031 | 0.004 | 0.062 (5) | 0.062 / 0.031 | 0.055 | 0.164 / 0.016 |
| new15 | S_both | 3 | 78.0 | 81.1 | 76.6 | 77.7 | 3/3 | 0.125 | 0.125 | 0.125 | 0.250 (2) | 0.250 / 0.250 | 0.250 | 0.500 / 0.125 |
| new15 | S_both_high | 2 | 76.8 | 80.0 | 77.1 | 77.4 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 |
| all33 | all | 33 | 71.4 | 74.2 | 71.2 | 71.5 | 24/33 | <0.0001 | 0.0003 | <0.0001 | 0.005 (13) | 0.003 / 0.002 | 0.0001 | 0.0009 / 0.013 |
| all33 | S_fid | 14 | 71.6 | 73.4 | 70.6 | 71.7 | 10/14 | 0.007 | 0.010 | 0.033 | 0.043 (8) | 0.008 / 0.055 | 0.013 | 0.008 / 0.039 |
| all33 | S_fid_strict | 6 | 72.1 | 73.6 | 73.5 | 73.7 | 4/6 | 0.062 | 0.484 | 0.547 | 0.250 (3) | 0.750 / 0.750 | 0.125 | 0.031 / 0.062 |
| all33 | S_ecg | 23 | 71.4 | 74.6 | 71.1 | 71.9 | 16/23 | 0.0001 | 0.0007 | 0.0004 | 0.0010 (11) | 0.003 / 0.0010 | 0.0002 | 0.0004 / 0.001 |
| all33 | S_both | 11 | 71.4 | 73.4 | 70.7 | 71.8 | 8/11 | 0.004 | 0.031 | 0.061 | 0.031 (5) | 0.062 / 0.062 | 0.008 | 0.012 / 0.019 |
| all33 | S_both_high | 5 | 69.8 | 72.6 | 68.4 | 69.2 | 4/5 | 0.062 | 0.031 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.125 | 0.031 / 0.062 |
| old18 | all | 18 | 70.4 | 73.3 | 70.0 | 70.5 | 12/18 | 0.002 | 0.002 | 0.004 | 0.011 (10) | 0.008 / 0.014 | 0.003 | 0.0003 / 0.009 |

#### P2 — mean |SMD| (58)

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 0.119 | 0.121 | 0.122 | 0.120 | 9/15 | 0.664 | 0.460 | 0.525 | 0.793 (8) | 0.297 / 0.637 | 0.802 | 0.156 / 0.260 |
| new15 | S_fid | 5 | 0.105 | 0.102 | 0.112 | 0.107 | 3/5 | 0.344 | 0.188 | 0.281 | 0.500 (4) | 0.312 / 0.438 | 0.562 | 0.812 / 0.375 |
| new15 | S_fid_strict | 2 | 0.088 | 0.075 | 0.092 | 0.096 | 2/2 | 0.250 | 0.500 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 |
| new15 | S_ecg | 8 | 0.107 | 0.110 | 0.109 | 0.116 | 5/8 | 0.645 | 0.547 | 0.148 | 0.719 (5) | 0.688 / 0.250 | 0.781 | 0.160 / 0.379 |
| new15 | S_both | 3 | 0.096 | 0.093 | 0.094 | 0.104 | 2/3 | 0.500 | 0.500 | 0.250 | 0.750 (2) | 0.750 / 0.500 | 0.750 | 0.625 / 0.375 |
| new15 | S_both_high | 2 | 0.088 | 0.075 | 0.092 | 0.096 | 2/2 | 0.250 | 0.500 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.250 |
| all33 | all | 33 | 0.116 | 0.111 | 0.117 | 0.117 | 23/33 | 0.066 | 0.065 | 0.042 | 0.058 (13) | 0.008 / 0.015 | 0.112 | 0.019 / 0.011 |
| all33 | S_fid | 14 | 0.114 | 0.107 | 0.116 | 0.117 | 9/14 | 0.020 | 0.046 | 0.007 | 0.059 (8) | 0.059 / 0.055 | 0.039 | 0.275 / 0.073 |
| all33 | S_fid_strict | 6 | 0.121 | 0.113 | 0.120 | 0.126 | 4/6 | 0.062 | 0.188 | 0.047 | 0.125 (3) | 0.125 / 0.125 | 0.125 | 0.156 / 0.062 |
| all33 | S_ecg | 23 | 0.114 | 0.107 | 0.114 | 0.118 | 17/23 | 0.022 | 0.030 | 0.0005 | 0.017 (11) | 0.014 / 0.006 | 0.042 | 0.013 / 0.005 |
| all33 | S_both | 11 | 0.112 | 0.102 | 0.111 | 0.115 | 8/11 | 0.018 | 0.090 | 0.006 | 0.062 (5) | 0.156 / 0.062 | 0.034 | 0.123 / 0.018 |
| all33 | S_both_high | 5 | 0.100 | 0.083 | 0.104 | 0.105 | 5/5 | 0.031 | 0.062 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.062 | 0.062 / 0.031 |
| old18 | all | 18 | 0.114 | 0.103 | 0.112 | 0.115 | 14/18 | 0.003 | 0.005 | <0.0001 | 0.011 (10) | 0.005 / 0.0010 | 0.006 | 0.016 / 0.0004 |

#### P2 — balance C-stat

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 0.648 | 0.644 | 0.649 | 0.650 | 8/15 | 0.255 | 0.198 | 0.136 | 0.395 (8) | 0.180 / 0.406 | 0.437 | 0.102 / 0.829 |
| new15 | S_fid | 5 | 0.677 | 0.672 | 0.689 | 0.673 | 3/5 | 0.312 | 0.062 | 0.469 | 0.625 (4) | 0.125 / 0.688 | 0.625 | 0.438 / 0.688 |
| new15 | S_fid_strict | 2 | 0.738 | 0.708 | 0.741 | 0.730 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.500 |
| new15 | S_ecg | 8 | 0.650 | 0.646 | 0.652 | 0.652 | 4/8 | 0.359 | 0.266 | 0.219 | 0.469 (5) | 0.344 / 0.375 | 0.609 | 0.461 / 0.965 |
| new15 | S_both | 3 | 0.675 | 0.667 | 0.690 | 0.677 | 2/3 | 0.375 | 0.125 | 0.250 | 0.750 (2) | 0.250 / 0.500 | 0.750 | 0.625 / 0.750 |
| new15 | S_both_high | 2 | 0.738 | 0.708 | 0.741 | 0.730 | 2/2 | 0.250 | 0.250 | 0.250 | 0.500 (1) | 0.500 / 0.500 | 0.500 | 0.250 / 0.500 |
| all33 | all | 33 | 0.665 | 0.655 | 0.665 | 0.666 | 24/33 | 0.008 | 0.003 | 0.0009 | 0.020 (13) | 0.017 / 0.008 | 0.016 | 0.005 / 0.103 |
| all33 | S_fid | 14 | 0.692 | 0.682 | 0.696 | 0.691 | 11/14 | 0.055 | 0.005 | 0.046 | 0.074 (8) | 0.023 / 0.141 | 0.109 | 0.051 / 0.213 |
| all33 | S_fid_strict | 6 | 0.708 | 0.696 | 0.705 | 0.705 | 5/6 | 0.125 | 0.188 | 0.125 | 0.125 (3) | 0.250 / 0.375 | 0.250 | 0.062 / 0.594 |
| all33 | S_ecg | 23 | 0.679 | 0.667 | 0.678 | 0.680 | 17/23 | 0.024 | 0.008 | 0.005 | 0.031 (11) | 0.032 / 0.023 | 0.046 | 0.061 / 0.155 |
| all33 | S_both | 11 | 0.705 | 0.693 | 0.707 | 0.704 | 9/11 | 0.084 | 0.018 | 0.024 | 0.156 (5) | 0.094 / 0.094 | 0.169 | 0.111 / 0.224 |
| all33 | S_both_high | 5 | 0.752 | 0.723 | 0.754 | 0.747 | 5/5 | 0.031 | 0.031 | 0.031 | 0.250 (2) | 0.250 / 0.250 | 0.062 | 0.062 / 0.094 |
| old18 | all | 18 | 0.678 | 0.664 | 0.678 | 0.680 | 16/18 | 0.0005 | 0.0008 | 0.0003 | 0.003 (10) | 0.003 / 0.002 | 0.0009 | 0.004 / 0.007 |

#### P2 — |Δlog HR| vs RCT (primary)

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B | bench-shuffle null mean / p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 0.192 | 0.193 | 0.197 | 0.222 | 7/15 | 0.522 | 0.425 | 0.024 | 0.570 (8) | 0.562 / 0.031 | 0.737 | 0.468 / 0.136 | 0.006 (obs 0.001) / 0.355 |
| new15 | S_fid | 5 | 0.226 | 0.240 | 0.256 | 0.276 | 2/5 | 0.688 | 0.250 | 0.156 | 0.750 (4) | 0.250 / 0.188 | 0.875 | 0.344 / 0.062 | -0.010 (obs 0.014) / 1.000 |
| new15 | S_fid_strict | 2 | 0.121 | 0.121 | 0.134 | 0.137 | 1/2 | 0.750 | 0.500 | 0.500 | 1.000 (1) | 0.500 / 0.500 | 1.000 | 0.750 / 0.500 | -0.040 (obs 0.000) / 1.000 |
| new15 | S_ecg | 8 | 0.205 | 0.211 | 0.213 | 0.242 | 4/8 | 0.598 | 0.445 | 0.074 | 0.438 (5) | 0.312 / 0.031 | 0.781 | 0.465 / 0.266 | -0.008 (obs 0.006) / 0.882 |
| new15 | S_both | 3 | 0.164 | 0.136 | 0.146 | 0.181 | 2/3 | 0.375 | 0.375 | 0.250 | 0.500 (2) | 0.250 / 0.250 | 0.750 | 0.375 / 0.250 | -0.065 (obs -0.027) / 1.000 |
| new15 | S_both_high | 2 | 0.121 | 0.121 | 0.134 | 0.137 | 1/2 | 0.750 | 0.500 | 0.500 | 1.000 (1) | 0.500 / 0.500 | 1.000 | 0.750 / 0.500 | -0.040 (obs 0.000) / 1.000 |
| all33 | all | 33 | 0.214 | 0.197 | 0.200 | 0.214 | 20/33 | 0.078 | 0.439 | 0.064 | 0.007 (13) | 0.501 / 0.085 | 0.135 | 0.202 / 0.133 | -0.006 (obs -0.017) / 0.088 |
| all33 | S_fid | 14 | 0.274 | 0.257 | 0.264 | 0.283 | 8/14 | 0.191 | 0.429 | 0.140 | 0.469 (8) | 0.227 / 0.102 | 0.294 | 0.183 / 0.0004 | -0.011 (obs -0.017) / 0.294 |
| all33 | S_fid_strict | 6 | 0.251 | 0.243 | 0.185 | 0.217 | 3/6 | 0.422 | 0.797 | 0.812 | 0.500 (3) | 0.625 / 0.625 | 0.688 | 0.703 / 0.094 | -0.021 (obs -0.008) / 0.778 |
| all33 | S_ecg | 23 | 0.225 | 0.205 | 0.204 | 0.218 | 15/23 | 0.055 | 0.507 | 0.185 | 0.011 (11) | 0.411 / 0.236 | 0.091 | 0.129 / 0.323 | -0.013 (obs -0.021) / 0.167 |
| all33 | S_both | 11 | 0.282 | 0.249 | 0.249 | 0.274 | 7/11 | 0.054 | 0.500 | 0.205 | 0.125 (5) | 0.375 / 0.250 | 0.102 | 0.087 / 0.003 | -0.028 (obs -0.033) / 0.354 |
| all33 | S_both_high | 5 | 0.318 | 0.270 | 0.338 | 0.341 | 4/5 | 0.125 | 0.062 | 0.062 | 0.250 (2) | 0.250 / 0.250 | 0.250 | 0.094 / 0.062 | -0.053 (obs -0.048) / 0.551 |
| old18 | all | 18 | 0.233 | 0.201 | 0.202 | 0.208 | 13/18 | 0.006 | 0.478 | 0.348 | 0.004 (10) | 0.325 / 0.272 | 0.012 | 0.087 / 0.392 | -0.014 (obs -0.032) / 0.001 |

#### P2 — z² vs RCT

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B | bench-shuffle null mean / p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 2.21 | 2.20 | 2.41 | 2.80 | 7/15 | 0.494 | 0.247 | 0.055 | 0.508 (8) | 0.238 / 0.051 | 0.721 | 0.498 / 0.180 | -0.03 (obs -0.008) / 0.520 |
| new15 | S_fid | 5 | 2.37 | 2.88 | 3.24 | 3.41 | 2/5 | 0.625 | 0.219 | 0.188 | 0.625 (4) | 0.188 / 0.188 | 0.750 | 0.344 / 0.062 | -0.05 (obs 0.510) / 0.830 |
| new15 | S_fid_strict | 2 | 1.31 | 1.16 | 1.50 | 1.45 | 1/2 | 0.500 | 0.500 | 0.500 | 0.500 (1) | 0.500 / 0.500 | 1.000 | 0.750 / 0.500 | -0.54 (obs -0.142) / 1.000 |
| new15 | S_ecg | 8 | 2.54 | 2.40 | 2.64 | 3.19 | 4/8 | 0.402 | 0.301 | 0.109 | 0.281 (5) | 0.219 / 0.062 | 0.633 | 0.488 / 0.520 | -0.77 (obs -0.139) / 0.835 |
| new15 | S_both | 3 | 1.60 | 1.11 | 1.33 | 1.74 | 2/3 | 0.250 | 0.375 | 0.250 | 0.250 (2) | 0.250 / 0.250 | 0.500 | 0.375 / 0.250 | -1.78 (obs -0.495) / 1.000 |
| new15 | S_both_high | 2 | 1.31 | 1.16 | 1.50 | 1.45 | 1/2 | 0.500 | 0.500 | 0.500 | 0.500 (1) | 0.500 / 0.500 | 1.000 | 0.750 / 0.500 | -0.54 (obs -0.142) / 1.000 |
| all33 | all | 33 | 4.58 | 3.86 | 4.62 | 4.64 | 20/33 | 0.034 | 0.052 | 0.048 | 0.007 (13) | 0.092 / 0.053 | 0.065 | 0.013 / 0.042 | -0.71 (obs -0.720) / 0.482 |
| all33 | S_fid | 14 | 5.21 | 4.47 | 5.65 | 5.65 | 8/14 | 0.147 | 0.121 | 0.178 | 0.359 (8) | 0.117 / 0.121 | 0.285 | 0.026 / 0.0005 | -1.25 (obs -0.745) / 0.785 |
| all33 | S_fid_strict | 6 | 3.43 | 3.39 | 2.74 | 2.58 | 3/6 | 0.469 | 0.812 | 0.766 | 0.375 (3) | 0.625 / 0.625 | 0.625 | 0.484 / 0.125 | -1.04 (obs -0.039) / 0.867 |
| all33 | S_ecg | 23 | 4.50 | 3.64 | 4.50 | 4.56 | 15/23 | 0.022 | 0.085 | 0.102 | 0.013 (11) | 0.120 / 0.086 | 0.044 | 0.019 / 0.154 | -1.22 (obs -0.854) / 0.807 |
| all33 | S_both | 11 | 5.95 | 4.66 | 6.03 | 6.06 | 7/11 | 0.049 | 0.152 | 0.205 | 0.125 (5) | 0.156 / 0.156 | 0.098 | 0.027 / 0.004 | -2.24 (obs -1.290) / 0.868 |
| all33 | S_both_high | 5 | 9.05 | 6.44 | 10.35 | 10.35 | 4/5 | 0.062 | 0.062 | 0.062 | 0.250 (2) | 0.250 / 0.250 | 0.125 | 0.094 / 0.062 | -4.47 (obs -2.610) / 0.924 |
| old18 | all | 18 | 6.55 | 5.24 | 6.45 | 6.18 | 13/18 | 0.014 | 0.071 | 0.169 | 0.014 (10) | 0.081 / 0.142 | 0.029 | 0.005 / 0.077 | -1.20 (obs -1.314) / 0.414 |

#### P2 — % consistent (|z|<1.96)

| set | subset | n | base | +ECG | +shuf | +noise | k better | p | p vs shuf | p vs noise | cluster p (k cl.) | cl. p vs shuf / noise | LOO max p | p half A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| new15 | all | 15 | 73.3 | 80.0 | 86.7 | 80.0 | 1/15 | 0.500 | 1.000 | 1.000 | 0.500 (8) | 1.000 / 1.000 | 1.000 | 1.000 / 0.500 |
| new15 | S_fid | 5 | 80.0 | 80.0 | 80.0 | 80.0 | 0/5 | 1.000 | 1.000 | 1.000 | 1.000 (4) | 1.000 / 1.000 | 1.000 | 1.000 / 0.500 |
| new15 | S_fid_strict | 2 | 100.0 | 100.0 | 100.0 | 100.0 | 0/2 | 1.000 | 1.000 | 1.000 | 1.000 (1) | 1.000 / 1.000 | 1.000 | 1.000 / 1.000 |
| new15 | S_ecg | 8 | 75.0 | 75.0 | 87.5 | 75.0 | 0/8 | 1.000 | 1.000 | 1.000 | 1.000 (5) | 1.000 / 1.000 | 1.000 | 1.000 / 1.000 |
| new15 | S_both | 3 | 100.0 | 100.0 | 100.0 | 100.0 | 0/3 | 1.000 | 1.000 | 1.000 | 1.000 (2) | 1.000 / 1.000 | 1.000 | 1.000 / 1.000 |
| new15 | S_both_high | 2 | 100.0 | 100.0 | 100.0 | 100.0 | 0/2 | 1.000 | 1.000 | 1.000 | 1.000 (1) | 1.000 / 1.000 | 1.000 | 1.000 / 1.000 |
| all33 | all | 33 | 63.6 | 72.7 | 75.8 | 72.7 | 3/33 | 0.125 | 1.000 | 1.000 | 0.250 (13) | 1.000 / 1.000 | 0.250 | 0.250 / 0.125 |
| all33 | S_fid | 14 | 64.3 | 71.4 | 71.4 | 71.4 | 1/14 | 0.500 | 1.000 | 1.000 | 0.500 (8) | 1.000 / 1.000 | 1.000 | 0.250 / 0.125 |
| all33 | S_fid_strict | 6 | 83.3 | 83.3 | 83.3 | 83.3 | 0/6 | 1.000 | 1.000 | 1.000 | 1.000 (3) | 1.000 / 1.000 | 1.000 | 0.500 / 0.500 |
| all33 | S_ecg | 23 | 65.2 | 73.9 | 78.3 | 73.9 | 2/23 | 0.250 | 1.000 | 1.000 | 0.250 (11) | 1.000 / 1.000 | 0.500 | 0.250 / 0.250 |
| all33 | S_both | 11 | 63.6 | 72.7 | 72.7 | 72.7 | 1/11 | 0.500 | 1.000 | 1.000 | 0.500 (5) | 1.000 / 1.000 | 1.000 | 0.250 / 0.250 |
| all33 | S_both_high | 5 | 40.0 | 60.0 | 60.0 | 60.0 | 1/5 | 0.500 | 1.000 | 1.000 | 0.500 (2) | 1.000 / 1.000 | 1.000 | 0.500 / 0.500 |
| old18 | all | 18 | 55.6 | 66.7 | 66.7 | 66.7 | 2/18 | 0.250 | 1.000 | 1.000 | 0.250 (10) | 1.000 / 1.000 | 0.500 | 0.250 / 0.250 |

### Per-trial, confirmation set

| trial | RCT HR | fidelity (strict) | ECG relevance | cluster | P1 HR −/+ECG (SE) | P1 \|Δ\| −/+ | P1 %<0.1 −/+ | P2 HR −/+ECG (SE) | P2 \|Δ\| −/+ | P2 %<0.1 −/+ |
|---|---|---|---|---|---|---|---|---|---|---|
| leader | 0.87 | no | medium | C_DPP4I_PROXY | 0.57 / 0.54 (0.17) | 0.423 / 0.478 | 50.0 / 37.9 | 0.59 / 0.55 (0.16) | 0.385 / 0.465 | 51.7 / 46.6 |
| sustain6 | 0.74 | no | medium | C_DPP4I_PROXY | 0.49 / 0.54 (0.14) | 0.407 / 0.307 | 39.7 / 48.3 | 0.61 / 0.56 (0.14) | 0.186 / 0.280 | 43.1 / 44.8 |
| rewind | 0.88 | no | low | C_DPP4I_PROXY | 0.86 / 0.82 (0.11) | 0.019 / 0.073 | 46.6 / 72.4 | 0.78 / 0.75 (0.11) | 0.125 / 0.166 | 53.4 / 56.9 |
| declare | 0.83 | no | low | C_DPP4I_PROXY | 1.81 / 1.36 (0.08) | 0.779 / 0.492 | 37.9 / 39.7 | 1.02 / 0.87 (0.08) | 0.203 / 0.045 | 37.9 / 53.4 |
| canvas | 0.86 | no | low | C_DPP4I_PROXY | 0.82 / 0.95 (0.16) | 0.050 / 0.095 | 33.3 / 42.1 | 0.98 / 0.84 (0.17) | 0.128 / 0.026 | 28.1 / 29.8 |
| tecos | 0.98 | no | medium | C_DPP4I_VS_SU | 0.88 / 0.88 (0.08) | 0.105 / 0.106 | 74.1 / 67.2 | 0.86 / 0.89 (0.08) | 0.133 / 0.091 | 70.7 / 70.7 |
| carmelina | 1.02 | no | low | C_DPP4I_VS_SU | 1.01 / 0.98 (0.13) | 0.011 / 0.039 | 58.6 / 65.5 | 0.98 / 0.93 (0.13) | 0.038 / 0.092 | 63.8 / 67.2 |
| valiant | 1.00 | yes | medium | C_ARB_VS_ACEI | 0.84 / 0.80 (0.17) | 0.180 / 0.218 | 55.2 / 62.1 | 0.78 / 0.85 (0.16) | 0.250 / 0.166 | 56.9 / 53.4 |
| insight | 1.10 | yes | low | C_HTN_ANTIHYPERTENSIVE | 1.74 / 1.49 (0.17) | 0.459 / 0.305 | 48.3 / 37.9 | 1.80 / 2.09 (0.17) | 0.493 / 0.641 | 51.7 / 46.6 |
| affirm | 1.15 | yes (strict) | high | C_AF_RHYTHM_AAD | 1.35 / 1.11 (0.04) | 0.159 / 0.039 | 63.8 / 77.6 | 1.18 / 1.05 (0.04) | 0.027 / 0.088 | 74.1 / 82.8 |
| af-chf | 1.06 | yes (strict) | high | C_AF_RHYTHM_AAD | 1.42 / 1.26 (0.08) | 0.289 / 0.173 | 60.3 / 62.1 | 1.31 / 1.24 (0.08) | 0.215 / 0.155 | 56.9 / 72.4 |
| precision | 0.93 | yes | low | C_SINGLE_precision | 0.70 / 0.73 (0.10) | 0.283 / 0.243 | 65.5 / 67.2 | 0.80 / 0.80 (0.10) | 0.145 / 0.150 | 79.3 / 74.1 |
| amplify | 0.84 | no | low | C_SINGLE_amplify | 0.67 / 0.72 (0.13) | 0.220 / 0.153 | 36.2 / 56.9 | 0.75 / 0.77 (0.12) | 0.107 / 0.087 | 56.9 / 48.3 |
| lodestar | 1.06 | no | medium | C_STATIN_CAD | 1.09 / 0.91 (0.05) | 0.030 / 0.157 | 72.4 / 93.1 | 0.93 / 0.90 (0.05) | 0.133 / 0.164 | 89.7 / 91.4 |
| prove-it | 0.84 | no | medium | C_STATIN_CAD | 1.17 / 1.07 (0.11) | 0.335 / 0.240 | 43.9 / 43.9 | 1.15 / 1.11 (0.10) | 0.310 / 0.277 | 43.1 / 46.6 |


## Round-4 audit corrections (2026-09-28; docs/v18/AUDIT_ROUND4.md §7)
- AFFIRM/EAST-AFNET 4 overlap: 48% of AFFIRM persons are in the EAST-AFNET 4 cohort (25% with the same index date). It is not "most records".
- Patient-level overlap beyond the identical-record rule: ACTIVE W–ARISTOTLE 78% and INSIGHT–ALLHAT 79%.
- The v1.7 count-only feasibility screen (pooled events) ran before the registration commit. No effect information was involved.
