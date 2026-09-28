# v1.8 Plan A results: prespecified AF confirmation (5 new AF trials; confirmatory)

**Plan.** This is `docs/v17/V18_PLANS.md` Plan A, fixed in commit `760981a` before any v1.8 result. The five trials (FRAIL-AF, LAAOS III, PROTECT AF, RAFT-AF, ACTIVE W) were registered (`91cc8a3`), built blind (`c6724bd`) and rated blind (`79ffb98`) before this analysis.

**Code.** `scripts/v18/v18_af_confirm.py` imports `scripts/v17/v17_confirm.py` unchanged. It changes only three things: the trial list, the covariate paths, and the P5 diagnosis list, which is set exactly as in `s11_p5.py`.

**Outputs.** `/mnt/raid0/rbc58/ecg-tte/audits/claude-v18-af-confirm/`:
- `results_af5.csv`;
- `summary.csv`;
- `per_trial_af5.csv`, `per_trial_af12.csv`;
- `verify_verify.csv`.

## Verdict in plain language

**The prespecified AF confirmation does not confirm.** It fails on both the primary and the co-primary endpoint.

- **Primary: |Δlog HR| vs the RCT in the 5 new AF trials, demographics PS (P1).** This is the plan's hypothesis.
  - Adding the ECG moves the mean gap from 0.254 to 0.199.
  - Only 3 of the 5 trials move closer: FRAIL-AF, LAAOS III and RAFT-AF. PROTECT AF and ACTIVE W move away.
  - One-sided exact sign-flip **p = 0.19**. The smallest attainable p is 1/32 = 0.031.
- **Co-primary: benchmark shuffle, P1.** **p = 0.28**, so the gap reduction is no larger than with randomly assigned RCT benchmarks.
- **With the 5-diagnosis PS (P5), the ECG makes emulation worse.**
  - The mean gap goes from 0.135 to 0.212, with 1/5 trials closer.
  - Sign-flip p = 0.97; benchmark shuffle p = 1.00.
  - Without the ECG, the P5 emulations were already close to the RCTs, and all 5 were consistent with them.
- **Placebo contrasts, P1.** ECG vs shufECG p = 0.19. ECG vs noise32 p = 0.75: noise32 has a smaller mean gap (0.178) than the ECG.
- **Secondary endpoints, new 5.**
  - Consistency under P1 rises from 4/5 to 5/5: FRAIL-AF becomes consistent (p = 0.50). Under P5 it is 5/5 → 5/5.
  - z² falls under P1 (1.63 → 0.92, p = 0.13) and rises under P5 (0.56 → 1.15).
  - Held-out balance:
    - 58-panel % |SMD| < 0.1: P1 39.7 → 43.1 (p = 0.34); P5 43.4 → 46.9 (p = 0.19).
    - covars2b non-proximal: P1 61.3 → 59.9 (p = 0.78); P5 58.7 → 59.9 (p = 0.28).
    - None of these changes is significant.
- **Blinded subsets of the new 5.** S_fid and S_both are the same 4 trials (all but FRAIL-AF), and neither is significant (P1 |Δ| p = 0.38; P5 p = 0.94).
- **Combined AF-12 (7 existing + 5 new).**
  - Under P1 the sign-flip is significant: 0.361 → 0.268, 10/12 closer, p = 0.004, vs shufECG p = 0.004, LOO max p = 0.007.
  - This is driven by the 7 trials that generated the hypothesis.
  - The co-primary benchmark shuffle still fails (p = 0.14), and so does the test vs noise32 (p = 0.055).
  - The cluster p = 0.125 is the floor attainable with 3 clusters.
  - Under P5: p = 0.18, benchmark shuffle p = 0.98.
- **Interpretation.** The v1.7 AF pattern (ECG narrows the RCT gap with a demographics PS) did not replicate in new AF trials. In AF-12 it looks significant only because it includes the exploratory 7, and even there it does not pass the trial-specificity (benchmark shuffle) test. The one robust signal in AF-12 is held-out balance: the ECG improves 58-panel and covars2b balance under P1 beyond shufECG and noise32. It does not do so in the new 5 alone.

## Implementation (no analysis choice changed)

- **Trial list.** `V.ALL` = the 18 v1.6 trials (i = 0–17), then `v13_common.V17` (i = 18–32), then `v13_common.V18` in registry order:
  - frail-af i = 33;
  - laaos3 34;
  - protect-af 35;
  - raft-af 36;
  - active-w 37.

  Halves use `s1_ladder.halves(T, i)`, with seed = 16060 + i (16093–16097). The index continues after the 33 trials, and the existing 33 keep their seeds.
- **Paths.** `cdirs()` returns `claude-v18-covars` / `claude-v18-covars2b` for V18 trials; all other trials are unchanged. Readiness is checked against `claude-v18-trials/<trial>.READY`. All V18 trials load with `E.load_trial(n, cache=False)`, as V17 trials do.
- **PS.** P1 = `T.demo`. P5 = `T.demo` + hypertension_v11, t2d, cad_ihd (covars v1) + atrial_fibrillation (`T.cov`) + HF. This is `V.P2DX` monkeypatched exactly as `s11_p5.py`; the engine's "P2" label is renamed "P5" on output.
  - HF is covars2b `hf_any_365` if present, else `elx_chf`. `hf_any_365` was present in all 5 trials.
  - AF is constant in AF trials.
- **Arms.** base, +ECG32, +shufECG, +noise32, plus unmatched. `E.run_cell(..., estimator=("match", 0.2, 1))`, PS L2 C = 1.
- **The existing 33 trials.** They are read from `claude-v17-confirm/results_all.csv` (P1) and `results_p5.csv` (P5, label P2 there). They are not recomputed.
- **Metrics and tests.** These are `v17_confirm.trial_metrics` and `signflip_1s`:
  - clusters come from `docs/v17/trial_selection.json` and are cluster-mean sign-flips;
  - LOO is the max p;
  - halves are A and B.
- **Benchmark shuffle (co-primary).** For each of 20,000 draws (`numpy.random.default_rng(0)`):
  - the k analysed trials are given k RCT benchmarks drawn **jointly as (log HR, SE) pairs, without replacement, from all 38 RCT benchmarks** (33 + 5);
  - the statistic is mean(|le − q| − |lb − q|) for |Δ|, or the SE-weighted analogue for z²;
  - p = P(null ≤ observed).

  This is the `v18_clmbr.py` construction with 38 benchmarks and 20,000 draws. The v1.7 `analyse()` permuted benchmarks within the analysed set, and the v1.7 category table drew from 33 RCTs with 10,000 draws.
- **PROTECT AF benchmark.** The benchmark is a Bayesian rate ratio, 0.62 (95% credible interval 0.35–1.25). As registered in `trial_specs.PUBLISHED` and converted by `v13_common.bench`:
  - rb = log(0.62) = −0.478;
  - rs = (log 1.25 − log 0.35) / (2 × 1.96) = 0.325.

  The credible interval is treated as a 95% CI.

**Reproduction check.** ARISTOTLE (i = 6) and AFFIRM (i = 27) were rerun through the v1.8 runner. The comparison covers:
- P1, P5 and unmatched rows;
- halves full/A/B;
- all 5 arms;
- 54 cells × 84 numeric columns (HR, SE, pairs, all 58 SMDs, covars2b x-panel, C-stat, ...).

These were compared with `claude-v17-confirm/results_all.csv` and `results_p5.csv`. **Max deviation = 0.0.** The wall-clock `secs` column was excluded from the comparison.

**AF-7 reference.** Recomputed from the same files, the AF-7 P1 result reproduces `V17_PATTERNS.md`: 0.437 → 0.317, 7/7, p = 0.008, vs shufECG p = 0.016, consistency 2 → 5. Its benchmark-shuffle p is 0.062 here (38 RCTs, 20,000 draws) vs 0.035 in v1.7 (33 RCTs, 10,000 draws).

## Per-trial table, new 5 trials (full cohort)

**Column definitions.**
- HR is in our orientation (arm 0 vs arm 1), with SE of log HR.
- |Δ| = |log HR − log RCT|.
- "Consistent" means |z| < 1.96, with z computed using both SEs.
- Balance is the % with |SMD| < 0.1 on the 58-variable held-out panel and on the covars2b non-proximal panel.
- The rating comes from `trial_selection.json`: fidelity include; strict; ECG relevance; comparator cluster.

### P1 (demographics)

| trial | RCT HR (SE log) | HR −ECG (SE) | HR +ECG (SE) | \|Δ\| −ECG | \|Δ\| +ECG | consistent −/+ | 58-panel %<0.1 −/+ | covars2b %<0.1 −/+ | \|Δ\| shufECG / noise32 | rating (fidelity; strict; ECG relevance; cluster) |
|---|---|---|---|---|---|---|---|---|---|---|
| frail-af | 1.69 (0.162) | 0.956 (0.186) | 1.083 (0.187) | 0.569 | 0.445 | no / yes | 41.4 / 56.9 | 88.0 / 85.8 | 0.539 / 0.510 | out; out; medium; C_AF_OAC_VS_WARFARIN |
| laaos3 | 0.67 (0.121) | 0.939 (0.248) | 0.773 (0.228) | 0.337 | 0.143 | yes / yes | 60.3 / 44.8 | 67.1 / 61.9 | 0.470 / 0.004 | in; in; high; C_SINGLE_laaos3 |
| protect-af | 0.62 (0.325) | 0.552 (0.223) | 0.722 (0.229) | 0.115 | 0.153 | yes / yes | 22.4 / 39.7 | 53.9 / 50.6 | 0.104 / 0.066 | in; in; medium; C_AF_OAC_VS_WARFARIN |
| raft-af | 0.71 (0.190) | 0.566 (0.077) | 0.600 (0.082) | 0.227 | 0.169 | yes / yes | 34.5 / 31.0 | 31.8 / 32.0 | 0.198 / 0.236 | in; in; high; C_AF_RHYTHM_AAD |
| active-w | 1.44 (0.102) | 1.468 (0.123) | 1.568 (0.131) | 0.019 | 0.085 | yes / yes | 39.7 / 43.1 | 65.7 / 69.2 | 0.079 / 0.075 | in; out; medium; C_AF_OAC_VS_WARFARIN |

### P5 (demographics + HTN, T2D, CAD, AF, HF)

| trial | RCT HR (SE log) | HR −ECG (SE) | HR +ECG (SE) | \|Δ\| −ECG | \|Δ\| +ECG | consistent −/+ | 58-panel %<0.1 −/+ | covars2b %<0.1 −/+ | \|Δ\| shufECG / noise32 | rating (fidelity; strict; ECG relevance; cluster) |
|---|---|---|---|---|---|---|---|---|---|---|
| frail-af | 1.69 (0.162) | 1.205 (0.200) | 1.056 (0.184) | 0.338 | 0.470 | yes / yes | 58.6 / 51.7 | 84.5 / 85.5 | 0.633 / 0.608 | out; out; medium; C_AF_OAC_VS_WARFARIN |
| laaos3 | 0.67 (0.121) | 0.706 (0.230) | 0.803 (0.229) | 0.053 | 0.180 | yes / yes | 39.7 / 43.1 | 50.3 / 57.3 | 0.209 / 0.084 | in; in; high; C_SINGLE_laaos3 |
| protect-af | 0.62 (0.325) | 0.639 (0.218) | 0.690 (0.237) | 0.031 | 0.107 | yes / yes | 36.2 / 48.3 | 54.2 / 52.1 | 0.120 / 0.039 | in; in; medium; C_AF_OAC_VS_WARFARIN |
| raft-af | 0.71 (0.190) | 0.585 (0.080) | 0.557 (0.082) | 0.194 | 0.242 | yes / yes | 37.9 / 43.1 | 32.9 / 31.2 | 0.183 / 0.201 | in; in; high; C_AF_RHYTHM_AAD |
| active-w | 1.44 (0.102) | 1.528 (0.131) | 1.527 (0.132) | 0.059 | 0.059 | yes / yes | 44.8 / 48.3 | 71.3 / 73.5 | 0.066 / 0.134 | in; out; medium; C_AF_OAC_VS_WARFARIN |

### |Δlog HR| per trial, AF-12

| trial | set | P1 \|Δ\| −/+ECG | P5 \|Δ\| −/+ECG |
|---|---|---|---|
| aristotle | v1.7 AF-7 | 0.367 → 0.198 | 0.369 → 0.181 |
| rocket-af | v1.7 AF-7 | 0.555 → 0.550 | 0.416 → 0.373 |
| rely | v1.7 AF-7 | 0.155 → 0.099 | 0.349 → 0.168 |
| east-afnet4 | v1.7 AF-7 | 0.305 → 0.170 | 0.158 → 0.156 |
| cabana-v2 | v1.7 AF-7 | 1.230 → 0.989 | 0.975 → 0.758 |
| affirm | v1.7 AF-7 | 0.159 → 0.039 | 0.066 → 0.095 |
| af-chf | v1.7 AF-7 | 0.289 → 0.173 | 0.302 → 0.094 |
| frail-af | v1.8 new | 0.569 → 0.445 | 0.338 → 0.470 |
| laaos3 | v1.8 new | 0.337 → 0.143 | 0.053 → 0.180 |
| protect-af | v1.8 new | 0.115 → 0.153 | 0.031 → 0.107 |
| raft-af | v1.8 new | 0.227 → 0.169 | 0.194 → 0.242 |
| active-w | v1.8 new | 0.019 → 0.085 | 0.059 → 0.059 |

## Full tables

**Column definitions.**
- Metrics:
  - absd = |Δlog HR| (primary);
  - z2 = z²;
  - cons = % consistent;
  - lt01 = % of 58 held-out |SMD| < 0.1;
  - x_lt01 = % covars2b non-proximal |SMD| < 0.1;
  - mean_smd = mean held-out |SMD|;
  - cstat = PS C-statistic, shown for reference (lower = better).
- All p values are one-sided exact sign-flips for "ECG better", except "bench-shuffle p", which is shown for absd/z2 only.
- "better" = trials in which +ECG is better than base.
- Clusters are comparator clusters:
  - new 5: C_AF_OAC_VS_WARFARIN (FRAIL-AF, PROTECT AF, ACTIVE W), C_AF_RHYTHM_AAD (RAFT-AF), C_SINGLE_laaos3;
  - AF-12: the same 3 clusters;
  - with 3 clusters the smallest attainable cluster p is 0.125.

### New 5 AF trials (primary set)

| PS | metric | n | base | +ECG | +shufECG | +noise32 | better | p | p vs shuf | p vs noise | clusters | cluster p | cl. p vs shuf | cl. p vs noise | LOO max p | p half A | p half B | bench-shuffle p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | lt01 | 5 | 39.7 | 43.1 | 50.2 | 42.1 | 3/5 | 0.344 | 1.000 | 0.281 | 3 | 0.750 | 1.000 | 0.500 | 0.625 | 0.188 | 0.188 | — |
| P1 | x_lt01 | 5 | 61.3 | 59.9 | 61.1 | 60.1 | 2/5 | 0.781 | 0.938 | 0.594 | 3 | 0.875 | 0.875 | 0.750 | 0.938 | 0.188 | 0.375 | — |
| P1 | mean_smd | 5 | 0.160 | 0.143 | 0.136 | 0.151 | 3/5 | 0.125 | 1.000 | 0.031 | 3 | 0.500 | 1.000 | 0.125 | 0.250 | 0.125 | 0.156 | — |
| P1 | cstat | 5 | 0.765 | 0.763 | 0.779 | 0.779 | 4/5 | 0.406 | 0.062 | 0.125 | 3 | 0.625 | 0.250 | 0.375 | 0.562 | 0.062 | 0.062 | — |
| P1 | absd | 5 | 0.254 | 0.199 | 0.278 | 0.178 | 3/5 | 0.188 | 0.188 | 0.750 | 3 | 0.125 | 0.125 | 0.750 | 0.375 | 0.562 | 0.094 | 0.285 |
| P1 | z2 | 5 | 1.632 | 0.923 | 1.792 | 1.175 | 3/5 | 0.125 | 0.125 | 0.250 | 3 | 0.125 | 0.125 | 0.375 | 0.250 | 0.656 | 0.219 | 0.756 |
| P1 | cons | 5 | 80.0 | 100.0 | 80.0 | 80.0 | 1/5 | 0.500 | 0.500 | 0.500 | 3 | 0.500 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 | — |
| P5 | lt01 | 5 | 43.4 | 46.9 | 43.4 | 46.2 | 4/5 | 0.188 | 0.188 | 0.438 | 3 | 0.125 | 0.375 | 0.625 | 0.375 | 0.938 | 0.906 | — |
| P5 | x_lt01 | 5 | 58.7 | 59.9 | 60.2 | 60.3 | 3/5 | 0.281 | 0.562 | 0.625 | 3 | 0.375 | 0.500 | 0.750 | 0.562 | 0.188 | 0.938 | — |
| P5 | mean_smd | 5 | 0.143 | 0.129 | 0.142 | 0.141 | 4/5 | 0.094 | 0.125 | 0.062 | 3 | 0.250 | 0.250 | 0.250 | 0.188 | 0.531 | 0.969 | — |
| P5 | cstat | 5 | 0.751 | 0.742 | 0.765 | 0.759 | 3/5 | 0.344 | 0.031 | 0.125 | 3 | 0.500 | 0.125 | 0.250 | 0.688 | 0.125 | 0.656 | — |
| P5 | absd | 5 | 0.135 | 0.212 | 0.242 | 0.213 | 1/5 | 0.969 | 0.281 | 0.469 | 3 | 1.000 | 0.375 | 0.750 | 1.000 | 0.469 | 0.438 | 1.000 |
| P5 | z2 | 5 | 0.558 | 1.149 | 1.744 | 1.588 | 1/5 | 0.969 | 0.281 | 0.312 | 3 | 1.000 | 0.375 | 0.500 | 1.000 | 0.375 | 0.344 | 0.930 |
| P5 | cons | 5 | 100.0 | 100.0 | 80.0 | 80.0 | 0/5 | 1.000 | 0.500 | 0.500 | 3 | 1.000 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 | — |

### New 5, blinded subsets S_fid = S_both (laaos3, protect-af, raft-af, active-w)

S_fid and S_both are identical within the new 5. The S_both table is therefore identical to this one, and both are written to `summary.csv`.

| PS | metric | n | base | +ECG | +shufECG | +noise32 | better | p | p vs shuf | p vs noise | clusters | cluster p | cl. p vs shuf | cl. p vs noise | LOO max p | p half A | p half B | bench-shuffle p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | lt01 | 4 | 39.2 | 39.7 | 44.8 | 39.2 | 2/4 | 0.500 | 1.000 | 0.500 | 3 | 0.750 | 1.000 | 0.500 | 0.875 | 0.125 | 0.312 | — |
| P1 | x_lt01 | 4 | 54.6 | 53.4 | 54.3 | 53.9 | 2/4 | 0.688 | 0.875 | 0.688 | 3 | 0.625 | 0.750 | 0.875 | 0.875 | 0.062 | 0.312 | — |
| P1 | mean_smd | 4 | 0.170 | 0.151 | 0.148 | 0.160 | 2/4 | 0.250 | 1.000 | 0.062 | 3 | 0.500 | 1.000 | 0.125 | 0.500 | 0.062 | 0.250 | — |
| P1 | cstat | 4 | 0.814 | 0.815 | 0.832 | 0.826 | 3/4 | 0.562 | 0.125 | 0.250 | 3 | 0.625 | 0.250 | 0.375 | 0.625 | 0.062 | 0.125 | — |
| P1 | absd | 4 | 0.175 | 0.137 | 0.213 | 0.095 | 2/4 | 0.375 | 0.375 | 0.875 | 3 | 0.250 | 0.250 | 0.750 | 0.750 | 0.250 | 0.188 | 0.536 |
| P1 | z2 | 4 | 0.706 | 0.345 | 1.028 | 0.393 | 2/4 | 0.250 | 0.250 | 0.500 | 3 | 0.250 | 0.250 | 0.500 | 0.500 | 0.312 | 0.438 | 0.920 |
| P1 | cons | 4 | 100.0 | 100.0 | 100.0 | 100.0 | 0/4 | 1.000 | 1.000 | 1.000 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — |
| P5 | lt01 | 4 | 39.7 | 45.7 | 41.4 | 45.3 | 4/4 | 0.062 | 0.188 | 0.500 | 3 | 0.125 | 0.250 | 0.625 | 0.125 | 0.875 | 0.812 | — |
| P5 | x_lt01 | 4 | 52.2 | 53.5 | 53.2 | 53.6 | 2/4 | 0.312 | 0.375 | 0.562 | 3 | 0.375 | 0.500 | 0.625 | 0.625 | 0.250 | 0.875 | — |
| P5 | mean_smd | 4 | 0.153 | 0.135 | 0.147 | 0.144 | 3/4 | 0.125 | 0.250 | 0.125 | 3 | 0.250 | 0.250 | 0.250 | 0.250 | 0.312 | 0.938 | — |
| P5 | cstat | 4 | 0.805 | 0.788 | 0.811 | 0.804 | 3/4 | 0.188 | 0.062 | 0.250 | 3 | 0.250 | 0.125 | 0.250 | 0.375 | 0.125 | 0.562 | — |
| P5 | absd | 4 | 0.084 | 0.147 | 0.145 | 0.115 | 1/4 | 0.938 | 0.562 | 0.812 | 3 | 1.000 | 0.625 | 0.875 | 1.000 | 0.688 | 0.500 | 1.000 |
| P5 | z2 | 4 | 0.266 | 0.514 | 0.422 | 0.432 | 1/4 | 0.938 | 0.562 | 0.625 | 3 | 1.000 | 0.625 | 0.875 | 1.000 | 0.750 | 0.500 | 0.475 |
| P5 | cons | 4 | 100.0 | 100.0 | 100.0 | 100.0 | 0/4 | 1.000 | 1.000 | 1.000 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | — |

### Combined AF-12 (aristotle, rocket-af, rely, east-afnet4, cabana-v2, affirm, af-chf + the 5 new)

| PS | metric | n | base | +ECG | +shufECG | +noise32 | better | p | p vs shuf | p vs noise | clusters | cluster p | cl. p vs shuf | cl. p vs noise | LOO max p | p half A | p half B | bench-shuffle p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | lt01 | 12 | 44.0 | 51.6 | 47.5 | 46.6 | 10/12 | 0.016 | 0.112 | 0.014 | 3 | 0.500 | 0.375 | 0.125 | 0.033 | 0.013 | 0.010 | — |
| P1 | x_lt01 | 12 | 56.8 | 60.3 | 56.7 | 57.1 | 9/12 | 0.018 | 0.014 | 0.005 | 3 | 0.375 | 0.250 | 0.125 | 0.035 | 0.002 | 0.007 | — |
| P1 | mean_smd | 12 | 0.159 | 0.134 | 0.155 | 0.154 | 10/12 | 0.001 | 0.018 | 0.000 | 3 | 0.250 | 0.250 | 0.125 | 0.002 | 0.016 | 0.003 | — |
| P1 | cstat | 12 | 0.760 | 0.750 | 0.771 | 0.772 | 10/12 | 0.022 | 0.000 | 0.001 | 3 | 0.125 | 0.125 | 0.125 | 0.045 | 0.007 | 0.001 | — |
| P1 | absd | 12 | 0.361 | 0.268 | 0.385 | 0.332 | 10/12 | 0.004 | 0.004 | 0.055 | 3 | 0.125 | 0.125 | 0.375 | 0.007 | 0.238 | 0.011 | 0.137 |
| P1 | z2 | 12 | 8.419 | 4.963 | 9.476 | 9.106 | 10/12 | 0.001 | 0.002 | 0.004 | 3 | 0.125 | 0.125 | 0.250 | 0.002 | 0.159 | 0.033 | 0.964 |
| P1 | cons | 12 | 50.0 | 83.3 | 50.0 | 50.0 | 4/12 | 0.062 | 0.062 | 0.062 | 3 | 0.250 | 0.250 | 0.250 | 0.125 | 0.500 | 0.250 | — |
| P5 | lt01 | 12 | 51.5 | 57.2 | 52.9 | 51.9 | 9/12 | 0.021 | 0.035 | 0.025 | 3 | 0.125 | 0.375 | 0.375 | 0.041 | 0.791 | 0.282 | — |
| P5 | x_lt01 | 12 | 63.7 | 65.2 | 64.6 | 64.1 | 9/12 | 0.063 | 0.278 | 0.087 | 3 | 0.125 | 0.250 | 0.125 | 0.125 | 0.059 | 0.158 | — |
| P5 | mean_smd | 12 | 0.134 | 0.117 | 0.130 | 0.131 | 10/12 | 0.002 | 0.001 | 0.002 | 3 | 0.125 | 0.125 | 0.125 | 0.005 | 0.229 | 0.181 | — |
| P5 | cstat | 12 | 0.744 | 0.732 | 0.752 | 0.747 | 10/12 | 0.022 | 0.000 | 0.003 | 3 | 0.125 | 0.125 | 0.125 | 0.043 | 0.006 | 0.575 | — |
| P5 | absd | 12 | 0.276 | 0.240 | 0.300 | 0.289 | 7/12 | 0.177 | 0.041 | 0.100 | 3 | 0.625 | 0.125 | 0.500 | 0.304 | 0.066 | 0.159 | 0.977 |
| P5 | z2 | 12 | 5.110 | 3.192 | 5.483 | 5.586 | 7/12 | 0.061 | 0.020 | 0.031 | 3 | 0.250 | 0.125 | 0.250 | 0.122 | 0.039 | 0.148 | 0.985 |
| P5 | cons | 12 | 66.7 | 83.3 | 66.7 | 66.7 | 2/12 | 0.250 | 0.250 | 0.250 | 3 | 0.250 | 0.250 | 0.250 | 0.500 | 1.000 | 0.500 | — |

### AF-12, blinded subsets S_fid = S_both (11 trials; all except FRAIL-AF)

S_fid and S_both are also identical within AF-12.

| PS | metric | n | base | +ECG | +shufECG | +noise32 | better | p | p vs shuf | p vs noise | clusters | cluster p | cl. p vs shuf | cl. p vs noise | LOO max p | p half A | p half B | bench-shuffle p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | lt01 | 11 | 44.2 | 51.1 | 45.3 | 46.0 | 9/11 | 0.031 | 0.043 | 0.024 | 3 | 0.500 | 0.375 | 0.125 | 0.062 | 0.006 | 0.016 | — |
| P1 | x_lt01 | 11 | 54.0 | 58.0 | 53.8 | 54.5 | 9/11 | 0.012 | 0.011 | 0.006 | 3 | 0.375 | 0.250 | 0.125 | 0.024 | 0.000 | 0.005 | — |
| P1 | mean_smd | 11 | 0.163 | 0.136 | 0.161 | 0.157 | 9/11 | 0.002 | 0.008 | 0.000 | 3 | 0.250 | 0.250 | 0.125 | 0.004 | 0.009 | 0.005 | — |
| P1 | cstat | 11 | 0.777 | 0.767 | 0.790 | 0.788 | 9/11 | 0.034 | 0.001 | 0.003 | 3 | 0.125 | 0.125 | 0.125 | 0.068 | 0.001 | 0.002 | — |
| P1 | absd | 11 | 0.342 | 0.252 | 0.371 | 0.316 | 9/11 | 0.007 | 0.007 | 0.073 | 3 | 0.125 | 0.125 | 0.375 | 0.015 | 0.039 | 0.021 | 0.311 |
| P1 | z2 | 11 | 8.700 | 5.121 | 9.896 | 9.543 | 9/11 | 0.002 | 0.004 | 0.008 | 3 | 0.125 | 0.125 | 0.250 | 0.005 | 0.017 | 0.040 | 0.974 |
| P1 | cons | 11 | 54.5 | 81.8 | 54.5 | 54.5 | 3/11 | 0.125 | 0.125 | 0.125 | 3 | 0.250 | 0.250 | 0.250 | 0.250 | 0.500 | 0.250 | — |
| P5 | lt01 | 11 | 50.9 | 57.7 | 53.1 | 52.1 | 9/11 | 0.010 | 0.035 | 0.029 | 3 | 0.125 | 0.375 | 0.375 | 0.020 | 0.670 | 0.214 | — |
| P5 | x_lt01 | 11 | 61.8 | 63.4 | 62.5 | 62.1 | 8/11 | 0.075 | 0.210 | 0.063 | 3 | 0.125 | 0.250 | 0.125 | 0.148 | 0.063 | 0.134 | — |
| P5 | mean_smd | 11 | 0.136 | 0.118 | 0.131 | 0.131 | 9/11 | 0.003 | 0.002 | 0.004 | 3 | 0.125 | 0.125 | 0.125 | 0.006 | 0.094 | 0.138 | — |
| P5 | cstat | 11 | 0.764 | 0.748 | 0.767 | 0.762 | 10/11 | 0.002 | 0.000 | 0.006 | 3 | 0.125 | 0.125 | 0.125 | 0.004 | 0.004 | 0.476 | — |
| P5 | absd | 11 | 0.270 | 0.219 | 0.270 | 0.260 | 7/11 | 0.104 | 0.082 | 0.164 | 3 | 0.500 | 0.125 | 0.500 | 0.193 | 0.097 | 0.181 | 0.874 |
| P5 | z2 | 11 | 5.417 | 3.146 | 5.342 | 5.529 | 7/11 | 0.029 | 0.040 | 0.062 | 3 | 0.250 | 0.125 | 0.250 | 0.058 | 0.074 | 0.166 | 0.976 |
| P5 | cons | 11 | 63.6 | 81.8 | 72.7 | 72.7 | 2/11 | 0.250 | 0.500 | 0.500 | 3 | 0.250 | 0.500 | 0.500 | 0.500 | 1.000 | 0.500 | — |

### Reference: the 7 existing AF trials (hypothesis-generating; same code, 38-benchmark shuffle)

| PS | metric | n | base | +ECG | +shufECG | +noise32 | better | p | p vs shuf | p vs noise | clusters | cluster p | cl. p vs shuf | cl. p vs noise | LOO max p | p half A | p half B | bench-shuffle p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | lt01 | 7 | 47.1 | 57.7 | 45.6 | 49.8 | 7/7 | 0.008 | 0.008 | 0.031 | 2 | 0.250 | 0.250 | 0.250 | 0.016 | 0.031 | 0.023 | — |
| P1 | x_lt01 | 7 | 53.6 | 60.6 | 53.5 | 54.9 | 7/7 | 0.008 | 0.008 | 0.008 | 2 | 0.250 | 0.250 | 0.250 | 0.016 | 0.008 | 0.008 | — |
| P1 | mean_smd | 7 | 0.159 | 0.127 | 0.168 | 0.156 | 7/7 | 0.008 | 0.008 | 0.008 | 2 | 0.250 | 0.250 | 0.250 | 0.016 | 0.070 | 0.008 | — |
| P1 | cstat | 7 | 0.756 | 0.740 | 0.765 | 0.767 | 6/7 | 0.023 | 0.008 | 0.008 | 2 | 0.250 | 0.250 | 0.250 | 0.047 | 0.016 | 0.016 | — |
| P1 | absd | 7 | 0.437 | 0.317 | 0.462 | 0.443 | 7/7 | 0.008 | 0.016 | 0.023 | 2 | 0.250 | 0.250 | 0.250 | 0.016 | 0.086 | 0.047 | 0.062 |
| P1 | z2 | 7 | 13.268 | 7.850 | 14.964 | 14.772 | 7/7 | 0.008 | 0.016 | 0.016 | 2 | 0.250 | 0.250 | 0.250 | 0.016 | 0.031 | 0.047 | 0.954 |
| P1 | cons | 7 | 28.6 | 71.4 | 28.6 | 28.6 | 3/7 | 0.125 | 0.125 | 0.125 | 2 | 0.250 | 0.250 | 0.250 | 0.250 | 0.500 | 0.250 | — |
| P5 | lt01 | 7 | 57.3 | 64.6 | 59.7 | 56.0 | 5/7 | 0.055 | 0.102 | 0.023 | 2 | 0.500 | 0.500 | 0.250 | 0.109 | 0.438 | 0.133 | — |
| P5 | x_lt01 | 7 | 67.3 | 69.0 | 67.8 | 66.9 | 6/7 | 0.094 | 0.203 | 0.023 | 2 | 0.250 | 0.500 | 0.250 | 0.188 | 0.125 | 0.016 | — |
| P5 | mean_smd | 7 | 0.127 | 0.108 | 0.121 | 0.123 | 6/7 | 0.016 | 0.008 | 0.031 | 2 | 0.250 | 0.250 | 0.250 | 0.031 | 0.148 | 0.047 | — |
| P5 | cstat | 7 | 0.740 | 0.726 | 0.743 | 0.738 | 7/7 | 0.008 | 0.008 | 0.008 | 2 | 0.250 | 0.250 | 0.250 | 0.016 | 0.008 | 0.398 | — |
| P5 | absd | 7 | 0.376 | 0.261 | 0.342 | 0.343 | 6/7 | 0.023 | 0.070 | 0.078 | 2 | 0.250 | 0.250 | 0.250 | 0.047 | 0.039 | 0.219 | 0.278 |
| P5 | z2 | 7 | 8.361 | 4.651 | 8.154 | 8.441 | 6/7 | 0.023 | 0.039 | 0.055 | 2 | 0.250 | 0.250 | 0.250 | 0.047 | 0.039 | 0.195 | 0.977 |
| P5 | cons | 7 | 42.9 | 71.4 | 57.1 | 57.1 | 2/7 | 0.250 | 0.500 | 0.500 | 2 | 0.250 | 0.500 | 0.500 | 0.500 | 1.000 | 0.500 | — |

## Deviations from the plan

There are no deviations in analysis choices. The implementation notes below are documented for completeness:
1. The trial index for the new trials continues at 33–37, which gives halves seeds 16093–16097.
2. The existing 33 trials are read from the v1.7 result files rather than recomputed. Reproduction on ARISTOTLE and AFFIRM is exact.
3. The benchmark-shuffle draws (rb, rs) jointly from the 38 benchmarks, as specified ("33 + new").
4. The PROTECT AF credible interval is treated as a 95% CI, as registered.

## Caveats

- **Power.** With 5 trials, the smallest attainable one-sided sign-flip p is 1/32 = 0.031. That requires all 5 trials to move closer; with 3 comparator clusters the floor is 1/8. A 5-trial confirmation can only detect a large, uniform effect. The observed pattern (3/5 under P1, 1/5 under P5) is not that.
- **ACTIVE W overlaps RE-LY.** 69% of its (patient, index) records are identical to the RE-LY cohort (its warfarin arm), so it is not fully independent of an AF-7 trial. The overlap was flagged, not excluded. Without the ECG it already matched the RCT closely (P1 |Δ| 0.019), and the ECG moved it away (0.085).
- **FRAIL-AF is outcome-poor.** The RCT's primary endpoint includes clinically relevant non-major bleeding, which major-bleeding hospitalisation cannot capture. The blinded rater set outcome fidelity to "poor", and the trial is outside S_fid. It had the largest P1 gain (0.569 → 0.445, becoming consistent) but worsened under P5 (0.338 → 0.470). Excluding it (S_fid) does not change the verdict.
- **PROTECT AF.**
  - The benchmark is a Bayesian rate ratio with a wide credible interval (SE 0.325), so consistency is easy to achieve.
  - Real-world LAAO is channelled to OAC-unsuitable patients.
- **LAAOS III.** It is the only trial where the ECG gave a large P1 gain (0.337 → 0.143). Under P5 it was already close (0.053) and the ECG moved it away (0.180). noise32 gave an even smaller P1 gap (0.004), which shows how noisy the per-trial |Δ| is at these sample sizes.
- **Combined AF-12.**
  - It contains the 7 hypothesis-generating trials, so its significant P1 sign-flip is not independent confirmation.
  - Its benchmark shuffle (p = 0.14) and its test vs noise32 (p = 0.055) fail.
- **Consistency with the RCT is high even without the ECG** (P1 4/5, P5 5/5). The new trials' RCT benchmarks have wide intervals, which leaves little room to improve consistency.
- **Multiplicity.** The secondary endpoints are reported without correction, per the plan.
- **Privacy.** Aggregates only; no counts are shown. The analysed matched-pair counts all exceed 10.
