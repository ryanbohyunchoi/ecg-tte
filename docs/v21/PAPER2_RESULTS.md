# paper2 core results: learned representations vs hand-built PS covariates (step B)

Written 2026-10-07 by the step-B agent. Spec: `HANDOFF_PAPER2.md` §3.1–3.4. Code: `scripts/v21/ps_flags.py`, `scripts/v21/paper2_grid.py`. All files named below are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/` and hold trial-level aggregates. None of them is committed. `restricted_*` files hold unsuppressed counts and never leave raid0; every CSV has counts of 1–10 suppressed. Primary trial set: S32 (32 analysed trials). Sensitivity set: S38 (all 38 trials).

## Verdict in plain language

1. **Balance: both learned representations help a PS-CVD5 propensity score, in different places.**
   - With PS-CVD5 (main configuration, 1:1, caliper 0.2), on the 54 non-coded held-out characteristics, adding a representation reduces mean |SMD| by:
     - ECG: 8.8% (95% CI 4.4–13.3);
     - CLMBR-T: 12.4% (7.1–17.7);
     - both: 13.5% (6.6–20.4).
   - All three reach q < .01.
   - Both placebos (shuffled ECG and shuffled CLMBR-T) give ≈ 0.
   - **Per domain, the two representations look different, but only nominally:**
     - in the main configuration, the ECG's gains are concentrated in the echo domains: LV function 16.4%, LV structure 14.9%, diastolic/LA 16.1%. Only diastolic/LA reaches q < .05 (q = .03);
     - across configurations, LV structure reaches q < .05 under 1:3 matching, overlap weights and IPTW, and diastolic/LA under 1:3 matching;
     - CLMBR-T improves the labs and vitals (24% and 23%, q < .01) and the valves;
     - the direct CLMBR-T vs ECG domain differences in the echo domains are nominal and do not replicate: in the main configuration, LV function −18.4% (q = .14) and diastolic/LA −18.4% (q = .09); under 1:3 matching −4.6% and −6.1%; under overlap −4.6% and −4.6%; all q ≥ .38 there.
   - **CLMBR-T vs ECG overall** (54 items, two-sided): CLMBR-T improves balance more than the ECG in 3 of 6 configurations at q < .05:
     - 1:3 matching 7.4%, q = .022;
     - overlap 6.7%, q = .012;
     - GBM 8.1%, q = .036.

     In the main configuration the difference is not significant (3.9%, q = .36).
   - **Adding the ECG on top of CLMBR-T** gives +1.3% in the main configuration (q = .49). It gives more in other configurations: overlap 3.0%, q = .005; GBM 6.7%, q = .009.
2. **Against stronger hand-built PS models, CLMBR-T adds nothing; the ECG still adds something at hdPS only.**
   - **PS-Flags.** There is no detectable difference between PS-Demo + CLMBR-T and PS-Flags (demographics + ~530 yes/no diagnosis flags):
     - balance +0.7% (95% CI −5.5 to 6.8), 13/31 trials better, two-sided P = .81;
     - agreement, paired over 31 trials, |Δ| 0.186 → 0.174, P = .50.

     This is not equivalence: there is no margin, and the CI is ±6%. Adding CLMBR-T to PS-Flags does nothing (−2.9%).
   - **Regularisation caveat.** The specified PS-Flags (L2, C = 1, the same PS model for every rung) overfits small trials. In PROTECT AF it keeps fewer than 11 matched pairs.
     - **CV-tuned penalty** (fairness sensitivity, `flagscv.csv`): −1.5% (−7.5 to 4.4), P = .63.
     - **Restricted to trials where PS-Flags keeps ≥ 0.7 of the smaller arm** (19 trials): −2.6% (−9.2 to 4.6).
     - **C = 0.1:** +7.7% (−0.1 to 15.8), P = .085.

     The point estimate moves between about −5% and +8% with the regularisation choice or trial set. None of these specifications shows CLMBR-T beating the flags.
   - **Tuned PS-Flags agreement.** CV-tuned PS-Flags agrees *less* well with the RCTs than PS-Demo + CLMBR-T: |Δ| 0.216 vs 0.170, 21/32 closer, two-sided P = .069, benchmark-permutation P = .001. The C = 1 primary shows no such difference (benchmark-permutation P = .97). This is a sensitivity result, outside the FDR sweep.
   - **PI hypothesis.** The PI's timing hypothesis predicts that CLMBR-T should beat the flags. Within this design, there is no evidence that it does. The test is also not specific to timing: CLMBR-T additionally sees drugs, procedures, measurement codes and visits.
   - **hdPS200.** CLMBR-T is not better than the hdPS200 base: P1 + CLMBR-T +3.8% (−3.0 to 10.0); P5 + CLMBR-T +3.8% (−2.7 to 9.6). Added to hdPS200, CLMBR-T gives −3.5%, while the ECG still gives +7.6% (1.7–13.0), q = .03.
   - **PS-Clinical.** CLMBR-T is nominally *worse* than the PS-Clinical base, which uses measured vitals and labs: P5 + CLMBR-T −4.9% (−11.2 to 0.9), q = .25 in the main configuration. This is significant only under the gradient-boosted PS (−11.9%, q = .007). Nothing adds to PS-Clinical (ECG −1.3%, CLMBR-T +0.8%).
3. **Agreement with the RCTs: nothing survives FDR, and nothing is trial-specific.**
   - The PS-CVD5 |Δ log HR| falls from 0.226 to:
     - 0.196 with the ECG (20/32 closer, P = .049);
     - 0.166 with CLMBR-T (18/32, P = .030);
     - 0.158 with both (18/32, P = .019).
   - All three q values are ≥ .43, and every benchmark-permutation P is ≥ .70 (0.70 ECG, 0.93 CLMBR-T, 0.94 both).
   - So the "improvement" is attenuation toward the null, not trial-specific agreement.
   - In S32, no agreement contrast in any configuration reaches q < .05. In S38, only two GBM-PS rows do; see §5.
4. **Robust across configurations for balance; IPTW and GBM are the exceptions.**
   - The PS-CVD5 balance gains replicate under caliper 0.1, 1:3 matching and overlap weights (all q < .02).
   - They are attenuated or lost under IPTW (CLMBR-T −2.0%, both −0.9%). This is weight-driven (low ESS), not trimming. The median ESS fraction under IPTW is 0.72 for the P5 base and 0.44 for P5 + CLMBR-T (`retention_sens.csv`).
   - **Retention does not explain the matched-sample gains** (`retention_sens.csv`). CLMBR-T trims about 10 points more of the smaller arm, but:
     - the per-trial CLMBR-T gain does not track its retention loss (Spearman ρ = 0.21, P = .24);
     - in the 15 trials where CLMBR-T loses ≤ 5 points of retention, CLMBR-T still gives 9.3% (2.0–16.5) and the ECG 6.9% (1.2–12.7);
     - overlap weights, which trim no one, keep the gain (13.6%, q < .001).
   - They are attenuated or lost for the ECG under the gradient-boosted PS (−1.1%).
5. **Which trials benefit (labels, `docs/v21/TRIAL_LABELS.json`).** The labels come from two runs of the same LLM, blind to results; see §6. In trials labelled "physiologic" (10 of the S32 trials), the PS-CVD5 balance gains are nominally larger than in the other 22 trials, for the ECG and for CLMBR-T alike:
   - relative reductions: ECG 16.3% vs 5.7%; CLMBR-T 22.6% vs 8.0%; both 29.6% vs 6.7%;
   - label-permutation P on the absolute gain: .048, .025 and .004;
   - BH q within the label family: .16, .13 and .060, so none reaches q < .05;
   - placebos P ≥ .69.
   - Because CLMBR-T, which is not a physiological signal, shows the same pattern, this more likely reflects more confounding in those trials ("room to improve") than ECG-specific content.
   - Agreement gains do not differ by label (P ≥ .87 for the real arms).
   - In the per-domain analysis, trials labelled LV-systolic-function show a larger gain in the LV-function items: ECG P = .003, CLMBR-T P = .002, both P = .001. All three have q = .021 within the domain family.

**Bottom line for paper2.**
- Learned representations improve balance over a sparse PS (PS-Demo/PS-CVD5).
- In the main configuration, the ECG's gains are concentrated in the echo-measured domains. This is nominal (only diastolic/LA q < .05), and the direct ECG-vs-CLMBR-T domain differences do not replicate under 1:3 matching or overlap weights.
- Overall, CLMBR-T improves balance at least as much as the ECG (more, at q < .05, in 3 of 6 configurations).
- CLMBR-T shows no detectable advantage over yes/no diagnosis flags or hdPS, and is nominally worse than measured vitals and labs.
- Neither representation produces trial-specific agreement with RCTs.

## 1. Gate

`gate_status.json`, `gate_sp32.csv`, `gate_v18.csv`.

| Gate | Cells compared | Max abs deviation | NaN mismatches | Result |
|---|---|---|---|---|
| P1/P5/hdPS200/clinical × base/ECG/shufECG × 6 configurations vs `claude-v20-sens-primary32/restricted_cells.parquet` (log HR, SE, n, n_t, n_c, n_pairs, ESS, 58 SMDs) | 2,736 (38 trials × 72) | 0.0 | 0 | **PASS** (≤ 1e-12) |
| CLMBR-T cells (P1/P5/hdPS200/clinical × base/ECG/CLMBR/ECG+CLMBR/shufECG/shufCLMBR, main) vs `claude-v18-embed-compare/restricted_results_unsuppressed.parquet` (full cohort) | 912 (38 × 24) | 0.0 | 0 | identical; `ex58` strings identical too |

**Why the CLMBR-T numbers differ from the v1.8 reports although the cells are identical.** The cells reproduce v1.8 exactly, because the same design columns are built in the same order. The differences from `docs/v18/CLMBR_RESULTS.md` and `EMBEDDING_COMPARISON.md` are all in the summary layer:
1. **Trial sets.** v1.8 used 33 or 38 trials; paper2 uses S32, with S38 as sensitivity.
2. **Endpoint.** v1.8's primary was `nc_lt01`, the % of non-coded items with |SMD| < 0.1. Paper2's primary is the relative reduction in mean |SMD| over the same 54 non-coded items.
3. **Item pairing.** Paper2 pairs items within trial: an item counts only if observed in both arms (`sens_primary32.paired_balance`). The clinical `ex58` masking therefore carries into cross-rung contrasts.
4. **Benchmark permutation.** Paper2 permutes within the analysed set (`sens_primary32.bshuf`).

For reference, the v1.8-style `% < 0.1` on the 54 items is in `sensitivity.csv` as `lt01_54_*`. At P5, ECG+CLMBR-T moves it from 53.4 to 59.9 (+6.5 pp; v1.8 reported +7.5 pp on 33 trials).

**Spot check against the published paper1 numbers** (P5 + ECG, S32, main, 58 items): relative reduction 9.0% (4.8–13.3); |Δ| 0.226 → 0.196, 20/32 closer, P = .049, cluster P = .20, permutation P = .70; estimate agreement 15 → 22/32; standardized-difference agreement 24 → 25/32. These match HANDOFF §2 / supplement eTables 3–5 (`sensitivity.csv`: `relred58`, `absd_*`, `b_ea`/`a_ea`, `b_cons`/`a_cons`).

## 2. What was run

**Rungs**

| Rung | Design |
|---|---|
| P1 | PS-Demo |
| P5 | PS-CVD5 (primary) |
| Flags | PS-Demo + 426–622 binary ICD-10 3-character flags; full history, index day excluded, ≥ 1% prevalence; see `docs/v21/PS_FLAGS.md` |
| hdPS200 | as sens_primary32 |
| clinical | as sens_primary32, with its `ex58` masking |

**Arms:** base, +ECG (32 PCs), +CLMBR-T (64 PCs), +ECG+CLMBR-T, +shuffled ECG, +shuffled CLMBR-T, and +CLMBR-T 32 PCs (main configuration, P1 and P5 only).

**Configurations:** main (1:1, caliper 0.2), cal01, m13 (1:3), iptw, overlap, gbm. The grid has 182 cells per trial, 6,916 cells in total (`restricted_cells.parquet`; suppressed copy `cells.csv`).

**Contrasts** (`sensitivity.csv`, 337 per set):
- 10 within each rung × 5 rungs × 6 configurations;
- 5 cross-rung head-to-heads × 6 configurations;
- 7 CLMBR-T-32 rows (main).

`Flags+CLMBR vs Flags` and `clinical+CLMBR vs clinical` are the within-rung rows `Flags: CLMBR vs base` and `clinical: CLMBR vs base`. They are not duplicated.

**Endpoints**
- **Balance:**
  - `relred54` = 100 × (1 − mean_a/mean_b) of per-trial mean |SMD| over the 54 non-coded items, with a 4,000-resample trial bootstrap CI (seed 20261001); this is the primary endpoint;
  - its exact sign-flip P (`m54_p`);
  - `lt01_54`;
  - the 58-item `relred58` and `lt01_58`;
  - per-domain rows (`domains.csv`).
- **Agreement:**
  - |Δ log HR| (`absd_*`), with exact sign-flip, comparator-cluster and leave-one-out P;
  - `bshuf_p`, the within-set benchmark permutation (20,000 draws);
  - r (`b_r`/`a_r`), estimate agreement (`*_ea`) and standardized-difference agreement (`*_cons`).

**Sidedness:** one-sided for "arm better than base" and "embedding better than placebo"; two-sided for the head-to-heads (CLMBR-T vs ECG, all cross-rung rows, CLMBR vs CLMBR32) and for placebo vs base.

**FDR:** Benjamini–Hochberg within set, across all 6 configurations × all contrasts.
- Balance family: {m54, lt01_54, m58, lt01_58} P values; columns `q_*_fam`.
- Agreement family: {absd, cons, bshuf}.
- Single-endpoint sweep q values (`q_*_sweep`) are also given.
- Domain P values form their own exploratory family (`q_domain_fam`).

## 3. PS-CVD5 (P5), S32, main configuration

Source: `headline.csv` (rows `set = S32`, `config = main`).

### Balance

| PS-CVD5 + | mean \|SMD\| 54 (base → arm) | Relative reduction, 54 items (95% CI) | Trials better | P | Cluster P | q (balance family) | % \|SMD\|<0.1, 54 items | Relative reduction, 58 items |
|---|---|---|---|---|---|---|---|---|
| ECG | 0.130 → 0.118 | 8.8 (4.4 to 13.3) | 21/32 | < .001 | .002 | .002 | 53.4 → 57.0 | 9.0 (4.8 to 13.3) |
| CLMBR-T (64) | 0.130 → 0.114 | 12.4 (7.1 to 17.7) | 23/32 | < .001 | .002 | < .001 | 53.4 → 58.7 | 14.0 (8.9 to 19.2) |
| ECG + CLMBR-T | 0.130 → 0.112 | 13.5 (6.6 to 20.4) | 23/32 | < .001 | .004 | .003 | 53.4 → 59.9 | 15.3 (8.7 to 21.8) |
| CLMBR-T (32) | 0.129 → 0.115 | 11.2 (6.5 to 16.0) | 23/32 | < .001 | .002 | < .001 | 53.4 → 59.2 | 13.0 (8.5 to 17.6) |
| shuffled ECG | 0.130 → 0.129 | 1.0 (−2.8 to 4.8) | 15/32 | .63 (2-sided) | .85 | .74 | 53.4 → 54.0 | 1.1 |
| shuffled CLMBR-T | 0.130 → 0.127 | 2.4 (−2.1 to 6.8) | 18/32 | .33 (2-sided) | .42 | .50 | 53.4 → 56.1 | 2.4 |
| ECG+CLMBR-T vs CLMBR-T | 0.114 → 0.112 | 1.3 (−4.2 to 6.6) | 18/32 | .31 | .11 | .49 | | |
| ECG+CLMBR-T vs ECG | 0.118 → 0.112 | 5.2 (−1.5 to 11.6) | 18/32 | .07 | .11 | .18 | | |
| CLMBR-T vs ECG (2-sided) | 0.118 → 0.114 | 3.9 (−1.8 to 8.9) | 23/32 | .20 | .61 | .36 | | |

**Retention** (matched anchors / smaller arm, mean over trials; cells with 1–10 pairs excluded from every retention mean): base 0.886, ECG 0.876, CLMBR-T 0.791, both 0.775, shuffled CLMBR-T 0.879. CLMBR-T trims about 10 points more of the smaller arm. The shuffled CLMBR-T arm, which has the same dimension and trims almost nothing, gives no gain, so the gain is not a dimension artefact.

**Is the gain a restriction effect?** Source: `retention_sens.csv`.
- The per-trial CLMBR-T gain does not track its retention loss: Spearman ρ = 0.21, P = .24 (ECG+CLMBR-T ρ = 0.12).
- **15 trials where CLMBR-T loses ≤ 5 points of retention:** CLMBR-T 9.3% (2.0 to 16.5), ECG 6.9% (1.2 to 12.7), both 11.7% (1.5 to 22.0).
- **The other 17 trials:** CLMBR-T 15.3% (8.3 to 22.6), ECG 10.7% (4.4 to 17.2).
- **Overlap weights, which trim no one:** CLMBR-T 13.6% (8.8 to 18.6), q < .001.

Restriction may contribute, but it does not explain the gain.

### Per domain

PS-CVD5, S32, main. Relative reduction in mean |SMD| (95% CI), with q from the domain family. Source: `headline_domains.csv` / `domains.csv`.

| Domain | + ECG | + CLMBR-T | + both | shuffled ECG | shuffled CLMBR-T |
|---|---|---|---|---|---|
| Vitals & core labs | 8.7 (3.4 to 13.8), q .02 | 22.7 (15.5 to 29.4), q < .01 | 32.1 (25.2 to 37.1), q < .01 | 2.2 | 2.3 |
| Other labs | 6.9 (−0.8 to 14.8), q .23 | 24.1 (13.0 to 33.2), q < .01 | 21.7 (12.0 to 30.7), q < .01 | 1.7 | 1.5 |
| Echo: LV structure | 14.9 (3.5 to 25.3), q .07 | 14.7 (1.3 to 26.4), q .12 | 21.7 (8.7 to 33.3), q .01 | −2.4 | −2.0 |
| Echo: LV function | 16.4 (2.5 to 28.5), q .09 | 1.0 (−17.4 to 16.7), q .78 | 7.6 (−13.0 to 24.7), q .54 | 9.2 | 7.0 |
| Echo: diastolic / LA | 16.1 (6.1 to 24.3), q .03 | 0.7 (−13.1 to 11.9), q .78 | 10.4 (−5.4 to 24.4), q .33 | 1.3 | 1.4 |
| Echo: RV / pulmonary | −1.8 (−13.6 to 8.2), q .86 | 0.2 (−12.8 to 11.2), q .79 | −1.3 (−14.9 to 11.0), q .84 | −5.0 | 2.8 |
| Echo: valves / aorta | 4.2 (−3.6 to 11.9), q .44 | 15.9 (4.5 to 25.0), q .04 | 3.1 (−12.4 to 14.9), q .68 | 0.6 | 3.7 |

### Agreement with the RCT

Source: `headline.csv`.

| PS-CVD5 + | \|Δ log HR\| (base → arm) | Trials closer | P | Cluster P | LOO max P | Benchmark-permutation P | q (agreement family) | r (base → arm) | Estimate agreement % | Standardized-difference agreement % |
|---|---|---|---|---|---|---|---|---|---|---|
| ECG | 0.226 → 0.196 | 20/32 | .049 | .20 | .087 | .70 | .58 | 0.56 → 0.57 | 46.9 → 68.8 | 75.0 → 78.1 |
| CLMBR-T | 0.226 → 0.166 | 18/32 | .030 | .046 | .059 | .93 | .51 | 0.56 → 0.50 | 46.9 → 62.5 | 75.0 → 81.3 |
| ECG + CLMBR-T | 0.226 → 0.158 | 18/32 | .019 | .10 | .039 | .94 | .43 | 0.56 → 0.59 | 46.9 → 62.5 | 75.0 → 93.8 |
| CLMBR-T (32) | 0.226 → 0.164 | 19/32 | .040 | .099 | .079 | .97 | .52 | 0.56 → 0.51 | 46.9 → 65.6 | 75.0 → 87.5 |
| shuffled ECG | 0.226 → 0.226 | 16/32 | .995 (2-sided) | .63 | | .16 | 1.00 | | | |
| shuffled CLMBR-T | 0.226 → 0.227 | 19/32 | .97 (2-sided) | .39 | | .29 | 1.00 | | | |

Percentages are % of 32 trials. For example, standardized-difference agreement with both representations = 30/32.

## 4. Head-to-heads (S32, main; two-sided)

Source: `headline.csv`. Positive relative reduction means the learned-representation PS (a) is better balanced than the hand-built reference (b).

| Contrast (a vs b) | mean \|SMD\| 54 (b → a) | Relative reduction, 54 items (95% CI) | a better | P | q | \|Δ\| (b → a) | a closer | P | Permutation P |
|---|---|---|---|---|---|---|---|---|---|
| **PS-Demo + CLMBR-T vs PS-Flags** | 0.113 → 0.112 | 0.7 (−5.5 to 6.8) | 13/31 | .81 | .86 | 0.186 → 0.174ᵃ | 19/31 | .50 | .97 |
| PS-Demo + CLMBR-T(32) vs PS-Flags | 0.113 → 0.116 | −2.9 (−10.1 to 4.4) | 13/31 | .44 | .60 | 0.186 → 0.181ᵃ | 14/31 | .81 | .999 |
| PS-Flags + CLMBR-T vs PS-Flags (1-sided) | 0.112 → 0.115 | −2.9 (−8.7 to 3.0) | 15/31 | .82 | .87 | 0.186 → 0.189 | 17/31 | .55 | .90 |
| PS-Demo + CLMBR-T vs hdPS200 | 0.118 → 0.114 | 3.8 (−3.0 to 10.0) | 17/32 | .29 | .47 | 0.181 → 0.170 | 20/32 | .59 | .095 |
| PS-CVD5 + CLMBR-T vs hdPS200 | 0.118 → 0.114 | 3.8 (−2.7 to 9.6) | 19/32 | .26 | .43 | 0.181 → 0.166 | 20/32 | .36 | .15 |
| hdPS200 + CLMBR-T vs hdPS200 (1-sided) | 0.118 → 0.122 | −3.5 (−14.0 to 6.0) | 18/32 | .71 | .80 | 0.181 → 0.184 | 15/31 | .55 | .67 |
| hdPS200 + ECG vs hdPS200 (1-sided) | 0.117 → 0.109 | 7.6 (1.7 to 13.0) | 22/32 | .008 | .033 | 0.181 → 0.167 | 18/32 | .20 | .11 |
| PS-CVD5 + CLMBR-T vs PS-Clinical | 0.111 → 0.117 | −4.9 (−11.2 to 0.9) | 9/32 | .12 | .25 | 0.158 → 0.166 | 16/32 | .69 | .19 |
| PS-CVD5 + ECG + CLMBR-T vs PS-Clinical | 0.111 → 0.117 | −5.4 (−11.9 to 1.1) | 13/32 | .13 | .27 | 0.158 → 0.158 | 13/32 | .98 | .17 |
| PS-Clinical + CLMBR-T vs PS-Clinical (1-sided) | 0.111 → 0.110 | 0.8 (−3.9 to 5.9) | 16/32 | .38 | .54 | 0.158 → 0.157 | 17/32 | .48 | .66 |
| PS-Clinical + ECG vs PS-Clinical (1-sided) | 0.111 → 0.113 | −1.3 (−6.8 to 3.9) | 17/32 | .68 | .78 | 0.158 → 0.155 | 18/32 | .42 | .62 |

ᵃ Paired over the 31 trials with an estimate in both arms (`absd_b_pair` / `absd_a_pair` in `headline.csv`). The unpaired arm means (32 trials for PS-Demo + CLMBR-T) are 0.170 and 0.183.

**Notes on the Flags rows.**
- The Flags rows have 31 trials. In PROTECT AF, PS-Flags keeps fewer than 11 matched pairs, so its estimate is missing and its 54-item SMDs are unobserved.
- The PS-Flags-base retention mean is 0.735 over the 31 trials with ≥ 11 pairs (S32 median 0.72 including PROTECT AF; 13/32 trials < 0.70), vs 0.796 for PS-Demo + CLMBR-T (`retention_sens.csv`, `docs/v21/PS_FLAGS.md`).
- The specified C = 1 penalty is 300–3,000× looser than the cross-validated optimum for PS-Flags (`flagscv_log.csv`).

### Fairness sensitivity: CV-tuned PS-Flags and retention-restricted head-to-head

Source: `flagscv.csv` (`paper2_grid.py flagscv`).
- PS-Flags is refitted with L2 C chosen per trial by 5-fold CV log-loss (C grid 1e-4 to 10; the chosen C per trial × design is in `flagscv_log.csv`).
- The C = 0.1 and C = 0.01 rows use a fixed C.
- `P1CV` = PS-Demo + CLMBR-T with its own CV-tuned C.
- Agreement means are paired. All rows are S32 and two-sided unless marked. Rows run for main, m13 and overlap.
- These rows are outside the main FDR sweep (sensitivity analyses).

They reproduce the reviewer's `review/restricted_fair_flags_h2h.csv` to the printed precision, e.g. P1+CLMBR vs Flags-CV −1.516 (−7.451 to 4.381), P = .628.

| Contrast (configuration) | Trials | Relative reduction, 54 items (95% CI) | a better | P | \|Δ\| b → a (paired) | a closer | P | Permutation P | Retention a / b |
|---|---|---|---|---|---|---|---|---|---|
| P1 + CLMBR-T vs PS-Flags C = 1 (main; primary, as above) | 31 | 0.7 (−5.5 to 6.8) | 13/31 | .81 | 0.186 → 0.174 | 19/31 | .50 | .97 | 0.80 / 0.735 |
| P1 + CLMBR-T vs PS-Flags C = 0.1 (main) | 32 | 7.7 (−0.1 to 15.8) | 20/32 | .085 | 0.218 → 0.170 | 19/32 | .44 | .32 | 0.80 / 0.72 |
| P1 + CLMBR-T vs PS-Flags C = 0.01 (main) | 32 | 1.0 (−5.1 to 6.8) | 14/32 | .76 | 0.202 → 0.170 | 17/32 | .25 | .14 | 0.80 / 0.73 |
| **P1 + CLMBR-T vs PS-Flags CV (main)** | 32 | **−1.5 (−7.5 to 4.4)** | 13/32 | .63 | 0.216 → 0.170 | 21/32 | .069 | .001 | 0.80 / 0.77 |
| P1 + CLMBR-T vs PS-Flags CV (m13) | 32 | 1.6 (−4.0 to 6.7) | 18/32 | .60 | 0.223 → 0.166 | 23/32 | .038 | .001 | 0.80 / 0.77 |
| P1 + CLMBR-T vs PS-Flags CV (overlap) | 32 | 1.9 (−1.4 to 5.1) | 18/32 | .27 | 0.184 → 0.176 | 18/32 | .64 | .70 | — |
| P1CV + CLMBR-T vs PS-Flags CV (main) | 32 | −0.3 (−5.6 to 4.1) | 17/32 | .91 | 0.216 → 0.182 | 18/32 | .15 | .007 | 0.80 / 0.77 |
| PS-Flags CV + CLMBR-T vs PS-Flags CV (main, 1-sided) | 32 | −4.3 (−17.1 to 5.4) | 16/32 | .71 | 0.216 → 0.218 | 16/32 | .55 | .17 | 0.69 / 0.77 |
| PS-Flags CV + CLMBR-T vs PS-Flags CV (overlap, 1-sided) | 32 | 4.6 (2.7 to 6.7) | 28/32 | < .001 | 0.184 → 0.171 | 22/32 | .037 | .39 | — |
| PS-Flags CV + ECG vs PS-Flags CV (main, 1-sided) | 32 | 0.7 (−3.6 to 4.9) | 12/32 | .38 | 0.216 → 0.212 | 20/32 | .43 | .052 | 0.76 / 0.77 |
| PS-Flags CV + ECG vs PS-Flags CV (overlap, 1-sided) | 32 | 2.9 (1.7 to 4.4) | 27/32 | < .001 | 0.184 → 0.175 | 21/32 | .002 | .037 | — |
| P1 + CLMBR-T vs PS-Flags C = 1, PS-Flags retention ≥ 0.5 (main) | 27 | −1.1 (−7.2 to 5.1) | 10/27 | .74 | 0.206 → 0.182 | 17/27 | .20 | .82 | |
| same, PS-Flags retention ≥ 0.7 | 19 | −2.6 (−9.2 to 4.6) | 6/19 | .50 | 0.222 → 0.211 | 11/19 | .64 | .89 | |
| same, PS-Flags retention ≥ 0.9 | 11 | −5.1 (−13.1 to 5.8) | 3/11 | .37 | 0.305 → 0.280 | 7/11 | .50 | .77 | |

S38 gives the same picture: P1 + CLMBR-T vs PS-Flags CV −2.2% (−7.7 to 3.4) in main.

**Reading.**
- No specification shows CLMBR-T beating the flags on balance. Where PS-Flags behaves well (CV-tuned, or high retention), the flags are nominally *better*.
- **Agreement against the tuned flags:** under CV tuning, PS-Flags agrees less well with the RCTs than P1 + CLMBR-T in the matched configurations, and the benchmark permutation says this difference is trial-specific (P = .001).
  - The CV-tuned PS-Flags agrees well with *permuted* benchmarks: its estimates are shrunk toward a common value.
  - It is not overlap-robust (P = .64, permutation P = .70).
  - It contrasts with the C = 1 primary (permutation P = .97).
  - Treat it as a nominal sensitivity finding.
- **Embeddings added to tuned flags under overlap weights:** both embeddings give small but consistent gains (CLMBR-T 4.6%, ECG 2.9%), unlike under matching.

**PS-Flags vs PS-Demo + CLMBR-T, per domain** (`headline_domains.csv`). No domain differs (all q ≥ .57):
- LV function −7.2%;
- diastolic/LA +6.3%;
- other labs +6.8%;
- vitals −4.7%.

## 5. All configurations

### S32, PS-CVD5 balance

Relative reduction in mean |SMD|, 54 items (95% CI), with q from the balance family. Source: `headline.csv`.

| Contrast | main | cal01 | m13 | iptw | overlap | gbm |
|---|---|---|---|---|---|---|
| P5 + ECG vs base | 8.8 (4.4 to 13.3); q .002 | 7.8 (3.2 to 12.6); q .007 | 6.4 (2.8 to 9.9); q .003 | 4.8 (1.5 to 8.5); q .013 | 7.4 (4.3 to 10.9); q < .001 | −1.1 (−7.3 to 4.3); q .74 |
| P5 + CLMBR-T vs base | 12.4 (7.1 to 17.7); q < .001 | 10.1 (4.0 to 16.2); q .010 | 13.3 (8.3 to 18.5); q < .001 | −2.0 (−15.2 to 9.4); q .73 | 13.6 (8.8 to 18.6); q < .001 | 6.9 (1.1 to 12.7); q .058 |
| P5 + both vs base | 13.5 (6.6 to 20.4); q .003 | 15.8 (8.6 to 22.9); q .001 | 13.6 (8.4 to 19.0); q < .001 | −0.9 (−18.2 to 11.4); q .66 | 16.2 (10.6 to 22.1); q < .001 | 13.2 (8.8 to 17.9); q < .001 |
| P5 CLMBR-T vs ECG (2-sided) | 3.9 (−1.8 to 8.9); q .36 | 2.5 (−4.0 to 8.2); q .61 | 7.4 (2.8 to 12.0); q .022 | −7.2 (−20.6 to 3.9); q .54 | 6.7 (2.9 to 10.6); q .012 | 8.1 (2.6 to 13.2); q .036 |
| P5 ECG+CLMBR-T vs ECG | 5.2 (−1.5 to 11.6); q .18 | 8.7 (2.4 to 15.0); q .031 | 7.8 (3.8 to 11.7); q .003 | −6.1 (−22.7 to 5.1); q .77 | 9.5 (5.6 to 13.7); q < .001 | 13.9 (8.1 to 19.8); q < .001 |
| P5 ECG+CLMBR-T vs CLMBR-T | 1.3 (−4.2 to 6.6); q .49 | 6.3 (0.5 to 11.8); q .067 | 0.3 (−2.9 to 3.7); q .57 | 1.0 (−6.7 to 8.6); q .55 | 3.0 (1.3 to 5.0); q .005 | 6.7 (2.6 to 10.6); q .009 |
| P1 + CLMBR-T vs Flags | 0.7 (−5.5 to 6.8); q .86 | 4.3 (−2.6 to 10.7); q .41 | 5.1 (1.0 to 9.4); q .093 | 28.0 (14.0 to 39.2); q .009 | 1.6 (−2.2 to 4.9); q .57 | −3.1 (−7.4 to 1.8); q .37 |
| P1 + CLMBR-T vs hdPS200 | 3.8 (−3.0 to 10.0); q .47 | 5.0 (−1.5 to 11.4); q .33 | 4.5 (−1.7 to 10.4); q .36 | 17.9 (8.6 to 26.9); q .004 | 2.8 (−2.8 to 8.0); q .53 | 0.9 (−3.8 to 5.4); q .80 |
| P5 + CLMBR-T vs clinical | −4.9 (−11.2 to 0.9); q .25 | −6.4 (−13.1 to −0.2); q .16 | −4.9 (−9.9 to −0.5); q .13 | −11.2 (−26.1 to 0.3); q .24 | −3.5 (−9.1 to 1.2); q .34 | −11.9 (−19.7 to −5.2); q .007 |

**IPTW.** Under IPTW, the PS-Flags and hdPS200 bases have extreme weights from near-separation.
- Median ESS fraction (`retention_sens.csv`): PS-Flags base 0.18 (minimum 0.002), hdPS200 0.34, vs 0.72 for P5 base.
- Their |Δ| is 0.375 and 0.253, vs 0.186 and 0.181 under matching.

That is why "CLMBR-T beats Flags/hdPS" appears only under IPTW. It is weight-driven (a failure of the rich-PS weighting), not a CLMBR-T effect.

**CLMBR-T vs ECG** (rows added per audit S3). CLMBR-T beats the ECG overall at q < .05 in m13, overlap and gbm, but not in main, cal01 or iptw. The per-domain CLMBR-T vs ECG rows for all configurations, the Figure 3 heatmap source, are in `headline_domains.csv` (contrast `P5: CLMBR vs ECG`):
- the ECG is nominally ahead in LV function and diastolic/LA in main and cal01 (all q ≥ .06), not in m13 or overlap;
- CLMBR-T is ahead in vitals and other labs in main, cal01, m13 and overlap (q ≤ .07), and in vitals under GBM (q < .01); not under IPTW.

### S32, PS-CVD5 agreement

Columns: |Δ| (base → arm), trials closer, sign-flip P, benchmark-permutation P; q from the agreement family. Source: `headline.csv`.

| Contrast | main | cal01 | m13 | iptw | overlap | gbm |
|---|---|---|---|---|---|---|
| P5 + ECG | 0.226→0.196, 20/32, P .049, perm .70; q .58 | 0.227→0.204, 16/32, P .11, perm .85; q .70 | 0.212→0.187, 21/32, P .007, perm .037; q .43 | 0.221→0.227, 15/32, P .69, perm .96; q 1.00 | 0.208→0.189, 20/32, P .011, perm .20; q .43 | 0.203→0.196, 17/32, P .32, perm .005; q .89 |
| P5 + CLMBR-T | 0.226→0.166, 18/32, P .030, perm .93; q .51 | 0.227→0.186, 16/32, P .13, perm .99; q .71 | 0.212→0.163, 19/32, P .036, perm .89; q .51 | 0.221→0.206, 17/32, P .37, perm .94; q .95 | 0.208→0.171, 16/32, P .14, perm .98; q .74 | 0.203→0.182, 17/32, P .25, perm .99; q .81 |
| P5 + both | 0.226→0.158, 18/32, P .019, perm .94; q .43 | 0.227→0.164, 20/32, P .037, perm .99; q .51 | 0.212→0.153, 20/32, P .020, perm .78; q .43 | 0.221→0.206, 17/32, P .38, perm .91; q .95 | 0.208→0.163, 19/32, P .087, perm .96; q .69 | 0.203→0.172, 19/32, P .15, perm .84; q .75 |
| P1 + CLMBR-T vs Flags (2-sided) | 0.186→0.170, 19/31, P .50, perm .97; q .97 | 0.201→0.180, 19/31, P .19, perm .68; q .78 | 0.174→0.166, 18/31, P .85, perm .73; q 1.00 | 0.375→0.186, 20/32, P .006, perm .97; q .43 | 0.189→0.176, 17/32, P .33, perm .70; q .92 | 0.191→0.184, 18/32, P .67, perm .57; q 1.00 |

The ECG's paper1 pattern reproduces under PS-CVD5: 1:3 matching gives P .007 and permutation P .037; GBM gives permutation P .005. CLMBR-T never shows a trial-specific signal (permutation P ≥ .78 in every configuration).

### Which configurations reach q < .05

Source: `q_counts.csv`. Counts of contrast rows per configuration (55 per configuration; 62 for main).

| Set | Configuration | Balance m54 q<.05 | Balance lt01_54 q<.05 | Agreement absd q<.05 | Benchmark-permutation q<.05 | Standardized-difference agreement q<.05 |
|---|---|---|---|---|---|---|
| S32 | main | 18 | 13 | 0 | 0 | 0 |
| S32 | cal01 | 14 | 8 | 0 | 0 | 0 |
| S32 | m13 | 18 | 11 | 0 | 0 | 0 |
| S32 | iptw | 7 | 10 | 0 | 0 | 0 |
| S32 | overlap | 23 | 19 | 0 | 0 | 0 |
| S32 | gbm | 18 | 12 | 0 | 0 | 0 |
| S38 | main / cal01 / m13 / iptw / overlap / gbm | 18 / 17 / 19 / 9 / 27 / 24 | 16 / 11 / 14 / 9 / 22 / 14 | 0 / 0 / 0 / 0 / 0 / **2** | 0 / 0 / 0 / 0 / 0 / **1** | 0 |

**The S38 GBM agreement rows** (`sensitivity.csv`):
- P1: ECG+CLMBR-T vs base, absd P = .0001, q = .034;
- P1: ECG+CLMBR-T vs ECG, absd P = .0001, q = .034;
- P5: CLMBR-T vs ECG (two-sided) benchmark permutation, P = .0001, q = .034.

These are isolated rows in a sensitivity set and a sensitivity configuration.

**Balance rows with q < .05 in S32 main** are the embedding-vs-base and embedding-vs-placebo rows at P1 and P5, plus hdPS200 + ECG. They are never Flags or clinical rows. They include the combination rows at P1. The two head-to-heads between the representations go in opposite directions: CLMBR-T is better than the ECG at P1 (10.5%, q = .022) but worse at hdPS200 (−12.1%, q = .021).

### S38 (sensitivity), main

Source: `headline.csv`, `set = S38`.

| Contrast | Balance: relative reduction, 54 items | q | Agreement: \|Δ\| | Closer | P | Permutation P |
|---|---|---|---|---|---|---|
| P5 + ECG | 9.0 (5.0 to 13.5) | < .001 | 0.224→0.195 | 23/38 | .033 | .68 |
| P5 + CLMBR-T | 12.7 (8.0 to 17.6) | < .001 | 0.224→0.162 | 22/38 | .011 | .90 |
| P5 + both | 14.5 (8.1 to 20.6) | < .001 | 0.224→0.154 | 22/38 | .006 | .91 |
| P1 + CLMBR-T vs Flags (2-sided) | 0.2 (−5.4 to 5.5) | .97 | 0.183→0.168 | 23/37 | .49 | .82 |
| P5 + CLMBR-T vs hdPS200 (2-sided) | 3.5 (−2.1 to 8.8) | .39 | 0.181→0.162 | 26/38 | .18 | .089 |
| P5 + CLMBR-T vs clinical (2-sided) | −5.7 (−11.7 to −0.4) | .11 | 0.159→0.162 | 20/38 | .85 | .21 |

## 6. Trial-type analysis (§3.4; PS-CVD5, main)

**Labels.** `docs/v21/TRIAL_LABELS.json`, 11/38 physiologic (10/32 in S32).
- **Who labelled.** The two "independent" labellers were two runs of the same LLM (Claude), each blind to results and to the other's labels, working from the same results-free PICOT table.
- **What κ means here.** Their κ = 1.0 is therefore expected and is **not** evidence of inter-rater reliability. Moreover, the labeller knows the published trials (accepted circularity, HANDOFF §1.6).
- **Clinician check.** A clinician check of the 11 "yes" labels would strengthen this. It has not been done.

**Sources:** `labels_physiologic.csv`, `labels_domain.csv`, `labels_spearman.csv`, `labels_per_trial.csv`.

**Tests.** P values come from 10,000 label permutations, two-sided. **The test statistic is the difference in mean absolute gain** (base − arm mean |SMD|), labelled minus not labelled.

**FDR.** BH q is computed within label families per set × configuration:
- physiologic family: 5 arms × 3 endpoints;
- domain family: tested rows per label source.

All P values here are nominal except where q is shown. All six configurations are in the CSVs.

### Physiologic vs not

S32. The test uses the absolute gain (mean |SMD| base − arm, 54 items). Relative reductions within each group (95% CI) are shown alongside as descriptive values.

| Arm (vs PS-CVD5 base) | Absolute gain: physiologic (n = 10) vs not (n = 22) | Difference | P | q | Relative reduction: physiologic | Relative reduction: not physiologic | Agreement gain difference: P (q) |
|---|---|---|---|---|---|---|---|
| ECG | 0.0203 vs 0.0075 (8/10 vs 13/22 better) | 0.0128 | .048 | .16 | 16.3 (7.8 to 25.7) | 5.7 (1.0 to 10.2) | .98 (.98) |
| CLMBR-T | 0.0282 vs 0.0106 (9/10 vs 14/22) | 0.0176 | .025 | .13 | 22.6 (14.1 to 31.0) | 8.0 (2.5 to 13.6) | .87 (.98) |
| ECG + CLMBR-T | 0.0369 vs 0.0088 (10/10 vs 13/22) | 0.0280 | .004 | .060 | 29.6 (20.8 to 38.3) | 6.7 (−0.5 to 13.7) | .93 (.98) |
| shuffled ECG | 0.0025 vs 0.0007 | 0.0018 | .74 | .98 | 2.0 (−5.1 to 8.9) | 0.5 (−4.0 to 4.9) | .25 (.53) |
| shuffled CLMBR-T | 0.0051 vs 0.0022 | 0.0028 | .69 | .98 | 4.1 (−1.1 to 10.0) | 1.7 (−4.4 to 7.5) | .76 (.98) |

In S38 (11 vs 27) the pattern is the same: ECG P = .081 (q = .30), CLMBR-T P = .027 (q = .20), both P = .007 (q = .10).

### Per domain

**Label-domain → held-out item mapping** (`paper2_grid.DOMAIN_ITEMS`):

| Label domain | Held-out items |
|---|---|
| LV_systolic_function | "Echo: LV function" group (EF, LV stroke volume index, GLS, LV systolic grade) + observed LVEF |
| diastolic_LA | "Echo: diastolic / LA" group |
| RV_pulmonary_congestion | "Echo: RV / pulmonary" group + NT-proBNP |
| LV_structure | "Echo: LV structure" group. Only 1 labelled trial (LIFE), so it is reported descriptively and not tested |
| rhythm_conduction | No held-out balance domain exists (the 58-item panel has no ECG-interval or rhythm items). Heart rate (1 item) is used as a descriptive proxy only |

**Results:** gain in mean |SMD| over the mapped items, labelled vs not; S32, `domains` (intersection) labels.

Absolute gain in mean |SMD| over the mapped items, labelled vs not; P (q within the domain family).

| Label domain (n labelled) | ECG: labelled vs not, P (q) | CLMBR-T: labelled vs not, P (q) | Both, P (q) | shuffled ECG, P (q) |
|---|---|---|---|---|
| LV_systolic_function (7) | 0.097 vs 0.011, .003 (.021) | 0.079 vs −0.018, .002 (.021) | 0.122 vs −0.011, .001 (.021) | .32 (.67) |
| diastolic_LA (6) | 0.035 vs 0.015, .23 (.66) | 0.031 vs −0.006, .045 (.22) | 0.044 vs 0.005, .090 (.36) | .57 (.80) |
| RV_pulmonary_congestion (3) | 0.004 vs −0.003, .71 (.84) | 0.000 vs 0.005, .84 (.89) | .46 (.78) | .89 (.89) |
| rhythm_conduction, heart-rate proxy (8) | 0.028 vs 0.004, .28 (.67) | .51 (.78) | .61 (.80) | .16 (.54) |
| LV_structure (1, descriptive) | 0.034 vs 0.017 (difference +0.017) | difference −0.003 | difference −0.004 | difference −0.015 |

The `domains_union` sensitivity labels give the same direction but weaker results: LV_systolic_function ECG P = .005 (q = .056), CLMBR-T P = .037 (q = .25).

### Data-driven check

Spearman correlation, over S32 trials, between each arm's gain and the residual echo imbalance under the PS-CVD5 base (`labels_spearman.csv`):

| Arm | 54-item gain: rho, P | Echo gain: rho, P |
|---|---|---|
| ECG | 0.36, .045 | 0.33, .067 |
| CLMBR-T | 0.41, .021 | 0.34, .054 |
| shuffled ECG | 0.19, .31 | 0.08, .68 |
| shuffled CLMBR-T | 0.46, .008 | 0.54, .001 |

The shuffled CLMBR-T placebo correlates at least as strongly as the real arms. In trials with large residual echo imbalance (sparse, noisy echo items), any change in the matched sample lowers the imbalance, i.e. regression to the mean. So this check cannot attribute the gain to ECG content. The ECG exceeds its own placebo (0.36 vs 0.19), but not the CLMBR-T placebo.

**Interpretation.** Learned representations help most where there is the most physiological confounding to remove. The ECG is no more physiology-specific than CLMBR-T at the level of the overall gain. The domain heatmap in §3 is where they differ: the ECG covers the echo domains, CLMBR-T the labs.

## 7. Deviations from the spec and decisions taken

1. **Empty matched sets.** In PROTECT AF, Flags × m13 × {ECG, CLMBR, ECG+CLMBR} has no pair within the caliper: L2 PS on 622 flags + embeddings, 1,442 patients, near-separation. `v16_engine.run_cell` crashes on an empty 1:k match. Those 3 cells are recorded as all-NaN (`cell_failed`), and the trial drops out of those contrasts. No other cell failed.
2. **Two-sided contrasts.** All cross-rung "learned representation vs another hand-built PS" contrasts (vs Flags, hdPS200, clinical) are treated as head-to-heads, so they are two-sided. So are CLMBR vs ECG, CLMBR vs CLMBR32 and placebo vs base (as in sens_primary32). For two-sided rows the benchmark permutation is the two-sided analogue of `sens_primary32.bshuf`: the same draws, 2 × the smaller tail.
3. **Duplicate cross-rung rows.** `Flags+CLMBR vs Flags` and `clinical+CLMBR vs clinical` are the same cells as the within-rung "CLMBR vs base" rows, so they are entered once in the FDR sweep.
4. **CLMBR32 contrasts.** Added: CLMBR32 vs base, CLMBR32 vs ECG, CLMBR vs CLMBR32 (P1 and P5) and P1+CLMBR32 vs Flags, all main configuration. CLMBR32 = the first 32 of the 64 CLMBR-T PCs (the same SVD).
5. **FDR families** are defined within set (S32 and S38 separately). The definitions are in §2. Domain P values have no cluster/LOO P and form a separate exploratory family.
6. **Paired and unpaired agreement means.** `absd_a`/`absd_b`, r, ea and cons are means over trials with a finite estimate in that arm. They are not strictly paired when a cell has NaN, which affects only rows involving Flags (PROTECT AF). Paired means (`absd_a_pair`, `absd_b_pair`, `n_agree_pair`) were added after the audit and are used for all Flags rows in this document. The tests (`*_p`, `*_better`) are always paired.
7. **Flags prevalence and window.** The PS-Flags prevalence threshold is applied in `T.keys`, the analysed cohort, not in the roster. Flags come from `scripts/v21/ps_flags.py`, which copies the dx query of `build_preindex_panel.py` because that query cannot be imported (see `docs/v21/PS_FLAGS.md`). The window matches CLMBR-T's: index day excluded, full history. CLMBR-T is additionally truncated to its last 4,096 tokens for 0.3–5.7% of patients.
8. **Labels.** The labels analysis was run for all 6 configurations; main is primary. Agreement gain by label uses |Δ log HR|. "Per-domain gain" uses the item mapping above, not the E.VARS groups alone (LVEF and NT-proBNP were added to the LV-function and RV/congestion sets).
9. **Retention.** CLMBR-T arms retain about 9–10 percentage points fewer anchors than base or ECG arms. Retention sensitivity (`retention_sens.csv`, `paper2_grid.py retsens`):
   - the CLMBR-T gain does not track the retention loss (ρ = 0.21, P = .24);
   - in the 15-trial small-loss subset the gain persists (CLMBR-T 9.3%, ECG 6.9%);
   - overlap weights (no trimming) keep it (13.6%).

   The IPTW losses are weight-driven (low ESS), not trimming. No anchor-level common-support re-analysis was run. v1.8's `common_support.csv` exists for the main-configuration cells.
10. **Privacy (audit B1).** Cells with 1–10 matched pairs (13 cells, all PROTECT AF) have `n_pairs`, `ess_t`, `ess_c` and `retain` blanked in every CSV. Retention means exclude them. `paper2_grid.py privacy` re-applies all blanks and scans `core/` (`privacy_scan.json`: clean).

## 8. Files

| File | Content |
|---|---|
| `core/restricted_cells.parquet` | all 6,916 cells (restricted; aggregates per trial × cell, unsuppressed counts) |
| `core/cells.csv` | same, counts 1–10 suppressed |
| `core/log.json` | per-trial flag counts, runtime |
| `core/gate_status.json`, `gate_sp32.csv`, `gate_v18.csv` | gate |
| `core/sensitivity.csv` | every contrast × configuration × set (674 rows), all endpoints and q values |
| `core/domains.csv` | per-domain rows (4,718) |
| `core/headline.csv`, `headline_domains.csv`, `q_counts.csv` | subsets used in this document |
| `core/per_trial.csv` | trial-level aggregates per rung × configuration × arm (m54, lt01_54, m58, absd, retention, domain means; counts suppressed) |
| `core/labels_physiologic.csv`, `labels_domain.csv`, `labels_spearman.csv`, `labels_per_trial.csv` | §3.4 |
| `core/tables.md` | markdown dump of `sensitivity.csv` by set × configuration |
| `core/flagscv.csv`, `flagscv_domains.csv`, `flagscv_log.csv`, `flagscv_cells.csv`, `restricted_flagscv_cells.parquet` | CV-tuned / fixed-C PS-Flags sensitivity (audit S1) |
| `core/retention_sens.csv` | retention / ESS sensitivity (audit S7) |
| `core/privacy_scan.json` | B1 privacy scan result |
| `core/flags/flags_build.csv` | PS-Flags source panel facts (roster level) |

Re-run: `cd scripts/v21; python paper2_grid.py run --workers 24; python paper2_grid.py gate; python paper2_grid.py summarize; python paper2_grid.py labels` (the labels step is standalone; it needs `restricted_cells.parquet` and `docs/v21/TRIAL_LABELS.json`).

## 9. Response to audit (`docs/v21/AUDIT_PAPER2_ANALYSES.md`)

| Item | Fix |
|---|---|
| **B1** small-count disclosure | **Code.** `paper2_grid.suppress` wraps `sens_primary32.suppress` and also blanks `ess_t`, `ess_c` and `retain` wherever `n_pairs` is 1–10. `load_F` excludes those cells from every retention mean, so they cannot be recovered by differencing. `flags_matrix` and `ps_flags.py` now suppress `flag_prev_max` / `pct_with_any_dx` when the complement is 1–10 patients. A new `privacy` subcommand re-applies all blanks to `cells.csv`, `flagscv_cells.csv`, `log.json` and `flags/flags_build.csv`, and scans every CSV in `core/`. **Result:** `privacy_scan.json` is clean. **Regenerated:** `cells.csv`, `per_trial.csv`, `sensitivity.csv`, `headline*.csv`, `tables.md`. **Docs:** in `PS_FLAGS.md`, PROTECT AF retention is now "<0.02 (fewer than 11 matched pairs)", and its `flag_prev_max`, whose complement was < 11 patients, is now "> 0.99 (complement suppressed)". This document now says "fewer than 11 matched pairs". The Flags retention mean is now 0.735 over 31 trials. |
| **S1** PS-Flags fairness | `paper2_grid.py flagscv` adds CV-tuned PS-Flags (`FlagsCV`), plus its + CLMBR-T and + ECG arms and a CV-tuned P1 + CLMBR-T (main, m13 and overlap), and fixed C = 0.1 / 0.01 (main). Outputs: `flagscv.csv`, `flagscv_log.csv`. It reproduces `review/restricted_fair_flags_h2h.csv` exactly (−1.5%, −7.5 to 4.4, P = .63; C = 0.1 +7.7%, P = .085). Retention-restricted head-to-heads (≥ 0.5 / 0.7 / 0.9) are in `flagscv.csv`. "Equivalent" is replaced by "no detectable difference". The C-sensitivity caveat and the tuned-Flags agreement result (benchmark-permutation P = .001, nominal, not overlap-robust) are in Verdict 2 and §4. |
| **S2** echo-domain claim | Verdict 1 and the bottom line now say the ECG's echo-domain gains are nominal in the main configuration (only diastolic/LA q < .05), with the cross-configuration detail. The CLMBR-T vs ECG domain differences are described as nominal and non-replicating. `headline_domains.csv` now holds all configurations for the key contrasts, including `P5: CLMBR vs ECG` (the Figure 3 heatmap source). |
| **S3** CLMBR-T vs ECG overall | Added to §5 (all configurations, with ECG+CLMBR-T vs ECG and vs CLMBR-T) and to Verdict 1: CLMBR-T beats the ECG at q < .05 in 3 of 6 configurations (m13, overlap, gbm), but not in main. |
| **S4** label analysis | BH-FDR within label families: physiologic = 5 arms × 3 endpoints per set × configuration; domain = tested rows per set × configuration × label source. The `q_family` column is in `labels_physiologic.csv` and `labels_domain.csv`. The table now shows the absolute gain, which is the test statistic, next to the descriptive relative reduction. No physiologic-vs-not test reaches q < .05 (both: q = .060). The LV-systolic-function domain rows do (q = .021). The labellers are described as two runs of one LLM; κ is not presented as reliability. |
| **S5** MIMIC side finding | Not in step B's scope; the step-D / MIMIC doc is the coordinator's to update. |
| **S6** paired agreement | Paired columns were added to `sensitivity.csv` / `headline.csv`. The PI head-to-head now reports 0.186 → 0.174 (31 paired trials), with a footnote giving the unpaired values. |
| **S7** retention sensitivity | `paper2_grid.py retsens` writes `retention_sens.csv` (ρ, the 15-trial small-loss subset, ESS fractions, retention by set). This is in §3, §7.9 and Verdict 4. The IPTW wording is now "weight-driven (low ESS)". |
| **N5** slips | LV_structure "both" is now −0.004. The PS-Flags retention medians now state the set (S32 0.72, S38 0.78). The PEPTIC + ECG CI in `MIMIC_PAPER2.md` is now 1.24–1.55. |
| **N11** wording | PS-Clinical: "nominally worse; significant only under GBM". The PI timing hypothesis is not isolated, because CLMBR-T also sees drugs, procedures, measurement codes and visits (Verdict 2). |

