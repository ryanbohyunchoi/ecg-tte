# Version 1 defect-impact audit of paper2.md (TRACE-ECG manuscript 2)

Written 2026-10-08. Audited state: `main` at tag `trace-v1` (5c98301). Code: `scripts/v1_audit/defect_impact.py`, `defect_extras.py`, `claim_table.py`. They import `scripts/v21/paper2_grid.py` and `scripts/v20/sens_primary32.py` without changing them. Outputs (aggregates, restricted folder): `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/defects/`. This document contains aggregates only: trial counts, means, CIs and P values. No patient count of 1 to 10 appears.

## Summary

1. **Gate: PASS.** Four paper2 cells (PROTECT AF: PS-CVD5 base and + ECG; PS-Flags C = 1; cross-validated PS-Flags) were refitted from scratch. All 66 values per cell matched exactly (max deviation 0). The S32 summary row "PS-CVD5 + ECG vs base" matched `core/sensitivity.csv` to 1.8e-15 (8.846%, 95% CI 4.366 to 13.295). The label tests matched exactly.
2. **The primary PS-CVD5 balance claims are unaffected by held-out leakage** (8.8%, 12.4%, 13.5%). The leakage-clean sweep reproduces every 54-item row that does not involve PS-Clinical to 0.0.
3. **The one conclusion leakage changes is CLMBR-T vs PS-Clinical.** PS-CVD5 + CLMBR-T vs PS-Clinical moves from −4.9% (−11.2 to 0.9) to **−2.6% (−8.4 to 3.2)**, with 14/32 trials better rather than 9/32. The gradient-boosted row moves from −11.9% (q = .007) to **−8.5% (q = .058)** in S32; it stays at q < .05 in S35 and S38. Echo EF (ρ = 1.00 with LVEF), LV systolic grade (|ρ| = 0.91) and eGFR (ρ = 0.83 with CKD-EPI recomputed from the PS inputs) had flattered PS-Clinical's balance.
4. **The 58-item numbers for CLMBR-T are partly mechanical.** They fall from 14.0% / 15.3% to 12.4% / 13.5% once the coded-record items that CLMBR-T sees are masked. The hdPS `rx_` / E&M overlap with `mean_meds` / `mean_util` is real (`rx_` levels in the hdPS top 200 in 38/38 trials; E&M levels in 35/38), but it touches no paper2 headline.
5. **RCT agreement.** Pure shrinkage of the PS-CVD5 estimates toward the null reproduces 79% of the ECG's |Δ log HR| reduction and 100–110% of the reductions with CLMBR-T and with both. In the primary configuration, random benchmarks give larger mean reductions than the true ones (1.2–1.4×). paper2's agreement wording is consistent with this. Two sentences need tightening: the conclusion "neither … produced trial-specific agreement" and the PEPTIC sentence.
6. **Penalty C = 1.** The cross-validated PS-Flags is verified: the cell matches exactly, the chosen C reproduces in 3/3 trials, the penalties are 316–3,162× stronger, and the in-sample C statistic in PROTECT AF is 1.00 at C = 1. The head-to-head conclusion holds: −1.5% (S32) and −2.2% (S35). Caveat: a CV penalty also shrinks the ECG gain, to 5.7% (−0.5 to 11.4) in S32 and 4.7% in R2's primary set (R2 result).
7. **IPTW.** Only the IPTW sentences depend on IPTW configurations. The CLMBR-T "loss" under IPTW is an ESS artefact: in the 11 trials with an ESS fraction ≥ 0.5, the gain is 7.9% (1.2 to 16.7). The PS-Flags IPTW contrast cannot be estimated with adequate ESS (4 trials).
8. **Trial set.** On R2's results-blind 35-trial set and on all 38 trials, every primary balance conclusion holds: 8.6% / 12.0% / 12.8% (S35). The physiologic-label ECG contrast loses even nominal significance (P = .048 → .095). The quality-stratum agreement pattern reverses under the blind tiers.
9. **FDR.** paper2's BH families are applied as declared. Under Benjamini–Yekutieli (valid under arbitrary dependence), the primary gains survive (q ≤ .02), but 3 of the 18 primary-configuration rows with BH q < .05 do not: CLMBR-T vs ECG at PS-Demo, hdPS + ECG, and CLMBR-T vs ECG at hdPS (q .16–.25). Across all configurations, 98 → 65 rows survive.
10. **MIMIC.** The window-fix numbers in `MIMIC_PAPER2.md` §6 are confirmed from source. They change only paper.md line 91 (hdPS 7.5% → 8.1%; PS-Clinical-lite 1.2% → 3.0%) and supplement eTable 6B. paper2's MIMIC Results are unaffected, and its Limitations sentence is already correct.

## Gate

| Check | Result |
|---|---|
| PROTECT AF, PS-CVD5 × main × base, refit vs `core/restricted_cells.parquet` (log HR, SE, n, pairs, ESS, 58 SMDs) | max dev 0, 0 NaN mismatches |
| PROTECT AF, PS-CVD5 × main × + ECG | max dev 0 |
| PROTECT AF, PS-Flags (C = 1) × main × base | max dev 0 |
| PROTECT AF, PS-Flags CV × main × base vs `restricted_flagscv_cells.parquet` | max dev 0 |
| S32 main "P5: ECG vs base" summary row (65 numeric fields) vs `core/sensitivity.csv` | max dev 1.8e-15 |
| Label tests, S32 main (P and q, physiologic and domain families) vs `core/labels_*.csv` | max dev 0 / 8e-17 |
| Leakage-clean sweep, every 54-item row not involving PS-Clinical (S32, S38) | identical to paper2 (max dev 0) |
| Cross-check with R2 `h1_ecg_decomposition.csv` (C = 1, primary35, 54 items: 8.6, 4.5–13.2) | this audit: 8.6 (4.5–13.2) |

## Headline claims of paper2.md

paper2.md has no abstract yet. Its headline claims are taken from Results, Discussion and Conclusion.

| # | Claim (paper2.md) | Number in paper2 |
|---|---|---|
| C1 | ECG improves balance with PS-CVD5 | 8.8% (4.4–13.3), 21/32, q = .002 |
| C2 | CLMBR-T improves balance with PS-CVD5 | 12.4% (7.1–17.7), q < .001 |
| C3 | Both improve it most | 13.5% (6.6–20.4), q = .003 |
| C4 | Permuted placebos do not | 1.0% (−2.8 to 4.8); 2.4% (−2.1 to 6.8) |
| C5 | 58-item panel | 9.0%, 14.0%, 15.3% |
| C6 | CLMBR-T vs ECG not clearly different (main); CLMBR-T ahead in 3 of 6 configurations | 3.9% (−1.8 to 8.9), q = .36 |
| C7 | Ladder: gains largest with PS-Demo; CLMBR-T > ECG there | 11.3 / 20.7 / 25.8%; 10.5%, q = .022 |
| C8 | hdPS: ECG still helps (not distinct from placebo); CLMBR-T does not, and is worse than the ECG | 7.6% (1.7–13.0), q = .033; vs permuted 4.8%, q = .26; −3.5%; −12.1%, q = .021 |
| C9 | Nothing adds to PS-Flags or PS-Clinical | Flags −3.0 / −2.9%; Clinical −1.3 / +0.8% |
| C10 | PS-Demo + CLMBR-T vs PS-Flags: no detectable difference | 0.7% (−5.5 to 6.8), 13/31, P = .81; agreement P = .50, permutation P = .97 |
| C11 | Holds against a fairer PS-Flags | CV −1.5% (−7.5 to 4.4); range −5 to +8%; CV penalty 300–3,000× stronger; in-sample C = 1.00 |
| C12 | CV PS-Flags agrees less well (nominal) | 0.216 vs 0.170, P = .069, permutation P = .001 |
| C13 | CLMBR-T not better than hdPS | 3.8% (−3.0 to 10.0); 3.8% (−2.7 to 9.6) |
| C14 | CLMBR-T nominally worse than PS-Clinical; significant only with the GBM PS (Conclusion: "nominally less well balanced than a PS with measured clinical covariates") | −4.9% (−11.2 to 0.9), q = .25; GBM −11.9%, q = .007 |
| C15 | IPTW "advantage" over PS-Flags and hdPS is an artefact | 28.0%, q = .009; 17.9%, q = .004; ESS 0.18 / 0.34 vs 0.72 |
| C16 | Agreement: closer on average, not trial-specific, nothing survives FDR | 0.226 → 0.196 / 0.166 / 0.158; q .58 / .51 / .43; permutation .70 / .93 / .94; EA 15 → 22 / 20 / 20; SDA 24 → 25 / 26 / 30 |
| C17 | Replication across configurations; IPTW and GBM exceptions | cal01, m13, overlap all q ≤ .010; IPTW: ECG 4.8%, CLMBR-T −2.0%; GBM: ECG −1.1% |
| C18 | Rows reaching q < .05 | 98 / 337 balance rows; 0 agreement rows |
| C19 | Larger gains in physiologic trials, none surviving FDR | ECG 16.3 vs 5.7% (P = .048, q = .16); CLMBR-T 22.6 vs 8.0% (P = .025, q = .13); both 29.6 vs 6.7% (P = .004, q = .060) |
| C20 | LV-systolic domain label survives FDR (domain family) | q = .021 ×3 |
| C21 | Domains: ECG in echo (nominal), CLMBR-T in labs | ECG LV function 16.4%, diastolic 16.1% (q = .03); CLMBR-T vitals 22.7%, labs 24.1%; CLMBR-T vs ECG other labs 18.4%, q = .045 |
| C22 | Agreement by quality (descriptive) | ECG: excellent/good 0.216 → 0.171 vs moderate 0.235 → 0.217 |
| C23 | Same in all 38 trials | 9.0 / 12.7 / 14.5%; vs PS-Flags 0.2% |
| C24 | Gain not explained by retention | 15 trials: 9.3% / 6.9%; overlap 13.6% |
| C25 | Plasmode | ECG 11.3%, CLMBR-T 22.6%, both 29.5% of remaining bias |
| C26 | MIMIC-IV PS-CVD5 analog; PEPTIC; window-fix sentence | 6.6% (2.3–12.8); 1.51 → 1.39; hdPS 7.5 → 8.1%, PS-Clinical-lite 1.2 → 3.0% |

## Claim × defect table

S32 = paper2 primary set; S35 = R2 blind primary set (`QUALITY_R2.json`, tiers A–C); S38 = all 38. "Clean" = leakage-clean masks (defect 1).

Verdicts:
- **U**: unaffected;
- **N**: changes the number, conclusion unchanged;
- **C**: changes the conclusion;
- **D**: descriptive only.

Defects without a row for a claim are U, or not applicable, for that claim.

| Claim | Defect | Number in paper2 | Number after correcting the defect (95% CI) | Verdict |
|---|---|---|---|---|
| C1–C3 | 1 leakage | 8.8 / 12.4 / 13.5% | identical (54-item rows unchanged, max dev 0) | U |
| C1 | 3 penalty (R2 result) | 8.8% (4.4–13.3) | CV log-loss penalty: 5.7% (−0.5 to 11.4) S32; 4.7% (−0.4 to 9.9) S35, 56 items; vs permuted ECG 7.9% (3.1–12.5) | N (robustness caveat: CI crosses 0 vs base) |
| C1–C3 | 6 trial set | 8.8 / 12.4 / 13.5% | S35: 8.6 (4.5–13.2) / 12.0 (7.4–17.0) / 12.8 (6.8–19.2), all q ≤ .002; S38: 9.0 / 12.7 / 14.5 | N |
| C1–C3 | 7 FDR | q .002 / <.001 / .003 (BH) | BY: .016 / .004 / .020 | U |
| C4 | 6 | 1.0 / 2.4% | S35: 1.7 (−1.6 to 4.9) / 2.7 (−1.8 to 6.8) | U |
| C5 | 1 leakage | 9.0 / 14.0 / 15.3% | clean (P5 − `B_mean`, prognostic score; CLMBR-T − 4 coded items): 8.8 / 12.4 / 13.5% | N (CLMBR-T's 58-item excess is mechanical) |
| C6 | 6 | 3.9% (−1.8 to 8.9), q .36; ahead in m13 / overlap / GBM | S35: 3.7% (−1.8 to 8.6), q .36; m13 7.2% q .016, overlap 6.5% q .013, GBM 5.9% q .12 | N (2 of 6 configurations in S35) |
| C6 | 7 | m13 q .022, overlap .012, GBM .036 | BY: .17, .09, .28 | N (none survives BY) |
| C7 | 6 | 11.3 / 20.7 / 25.8%; CLMBR-T > ECG 10.5%, q .022 | S35: 12.0 / 21.4 / 26.5%; 10.6%, q .023 | U |
| C7 | 7 | q .022 | BY q .17 | N (BY-fragile) |
| C8 | 6 | hdPS + ECG 7.6% (1.7–13.0), q .033; CLMBR-T vs ECG −12.1%, q .021 | S35: 6.5% (1.2–11.4), q .041; −10.3%, q .052 | N |
| C8 | 7 | q .033; .021 | BY q .25; .16 | N (BY-fragile; already "not distinguishable from permuted ECG") |
| C9 | 1 | Clinical: ECG −1.3%, CLMBR-T +0.8% | clean: −1.7% (−7.6 to 3.9), +1.5% (−2.9 to 6.3); + soft correlates: −1.9%, +2.2% | N |
| C9 | 6 | Flags: −3.0 / −2.9% | S35: −1.7 / −2.6%; clinical (clean) −0.8 / +3.4% | N |
| C10 | 1 | 0.7% (−5.5 to 6.8) | identical (no 54-item overlap between flags and the panel; coded items only on the 58 panel) | U |
| C10 | 3 | C = 1; 31 trials (PROTECT AF dropped) | CV PS-Flags (32 trials): −1.5% (−7.5 to 4.4), verified | U (verified) |
| C10 | 6 | 0.7%, 31 trials | S35: 0.4% (−5.3 to 6.2), 34 trials; S38: 0.2% | U |
| C11 | 3 | CV −1.5% (−7.5 to 4.4); 300–3,000×; C = 1.00 | reproduced: cell exact; chosen C 3/3 trials exact; C ratio 316–3,162; in-sample C 1.00 (PS-CVD5: 0.66) | U (verified) |
| C11 | 6 | −1.5% | S35: −2.2% (−8.2 to 3.9); C = 0.1: 5.8% (−2.7 to 14.3) | U |
| C12 | 2 / 6 | permutation P = .001 | S35: 0.198 vs 0.162, P = .12, permutation P = .029 | N (weaker; remains a single nominal sensitivity) |
| C13 | 1 / 6 | 3.8 / 3.8% | clean identical; S35 2.9% (−3.5 to 9.0) / 3.6% (−2.2 to 8.9) | U |
| **C14** | **1 leakage** | **−4.9% (−11.2 to 0.9), 9/32, q .25; GBM −11.9%, q .007** | **clean: −2.6% (−8.4 to 3.2), 14/32, q .56; GBM −8.5% (−16.2 to −2.1), q .058. Clean + BUN / LVESVi / GLS: −1.5% (−7.3 to 4.3); GBM −5.4% (−12.7 to 0.5)** | **C** |
| C14 | 1 × 6 | (not reported for S35) | S35: orig −6.3% (−12.4 to −0.6) → clean −3.3% (−8.8 to 2.2); GBM orig −14.6% (q .001) → clean −10.6% (−18.3 to −4.1, q .013). S38: −5.7% → −2.9%; GBM −13.5% → −10.0% (q .015) | C (main row); GBM q < .05 is set-dependent |
| C14 | 7 | GBM q .007 | BY q .054 | N |
| C15 | 4 IPTW | 28.0% / 17.9% (artefact) | trials with ESS fraction ≥ 0.5 in both cells: Flags 4 trials (not estimable); hdPS 7 trials, 9.2% (6.0–12.1) | U (already called an artefact) |
| C15 | 7 | q .009 / .004 | BY .074 / .028 | N |
| C16 | 2 shrinkage | 0.226 → 0.196 / 0.166 / 0.158; permutation .70 / .93 / .94 | pure-shrinkage counterfactual: 0.202 / 0.161 / 0.158 (79% / 110% / 100% of the gain); random-benchmark mean gain 1.19 / 1.40 / 1.36 × observed | U (wording consistent; see §2) |
| C16 | 2 | EA 15 → 22 / 20 / 20; SDA 24 → 25 / 26 / 30 | pure shrinkage: EA 17 / 20 / 20; SDA 25 / 28 / 28 | U (ECG's EA gain exceeds pure shrinkage; SDA does not) |
| C16 | 6 | as above, 32 trials | S35: 0.230 → 0.192 / 0.152 / 0.147; P .009 / .001 / .002; q .17 / .13 / .14; permutation .36 / .58 / .64 | N (still no FDR survivor, not trial-specific) |
| C17 | 4 IPTW | IPTW: ECG 4.8% (q .013); CLMBR-T −2.0%, both −0.9% "lost"; ESS 0.72 → 0.44 | ESS ≥ 0.5 trials: ECG 4.8% (0.1–10.0), 21 trials; CLMBR-T 7.9% (1.2–16.7), 11 trials; both 8.3% (−3.5 to 22.7), 10 trials | C (the IPTW "loss" of the CLMBR-T gain is weight instability) |
| C17 | 6 | as above | S35: cal01 / m13 / overlap ECG 8.1 / 5.8 / 7.0%, CLMBR-T 8.9 / 12.6 / 13.1%, all q ≤ .01; GBM ECG 1.0% | U |
| C18 | 1 | 98 balance rows, 0 agreement | clean S32: 96 (overlap 22, GBM 17), 0 agreement | N |
| C18 | 6 | 98 | S35: 98 clean (105 orig); S38: 109 clean (114 orig), 3 agreement rows | N |
| C18 | 7 | 98 (BH) | BY: 65 (primary configuration 13 of 18) | N |
| C19 | 6 | ECG P .048 (q .16); CLMBR-T .025 (.13); both .004 (.060) | S35: ECG 15.2 vs 6.2%, P .095 (q .28); CLMBR-T 21.3 vs 8.5%, P .030 (q .23); both 25.6 vs 8.0%, P .016 (q .23). S38: P .081 / .027 / .007 | N (ECG loses nominal P < .05; conclusion "none survived FDR" holds) |
| C20 | 6 | q .021 ×3 (7 labelled trials) | S35 (8 labelled): q .019 / .047 / .019; S38: .042 / .046 / .026; union labels S35 q ≥ .16 | U |
| C21 | 1 / 6 | as listed | clean S32 identical; S35: ECG LV function 11.5% (q .23), LV structure 14.9% (q .039), diastolic 18.6% (q .004); CLMBR-T vs ECG other labs 19.7% (q .007), diastolic −22.9% (q .013) | N |
| C22 | 6 quality | ECG: good+ 0.216 → 0.171 (9/15) vs moderate 0.235 → 0.217 (11/17); CLMBR-T gain larger in good+ | R2 blind tiers (S35): ECG A/B 0.220 → 0.187 (12/19) vs C 0.241 → 0.198 (10/16); CLMBR-T A/B 0.056 vs C 0.103 (reversed) | C (direction depends on post hoc tiers; paper2 already calls it noise) |
| C23 | 1 / 6 | 9.0 / 12.7 / 14.5%; Flags 0.2% | clean identical; S38 vs clinical −5.7% → −2.9% | U |
| C24 | 1 / 6 | 9.3% / 6.9%; overlap 13.6% | unaffected (P5 rows); S35 overlap 13.1% | U |
| C25 | 3 | plasmode arms | not re-run (PS also L2 C = 1; ladder rungs other than PS-CVD5 not simulated) | not quantified |
| C26 | 9 MIMIC | 6.6% (2.3–12.8); PEPTIC 1.51 → 1.39; window fix 7.5 → 8.1%, 1.2 → 3.0% | confirmed from `windowfix/summary/balance.csv`: hdPS 8.12 (−0.09 to 17.29); clinical-lite 2.98 (−8.59 to 15.23); PS-Demo identical. PS-CVD5 analog used earlier admissions in all 8 trials | U for paper2; paper.md line 91 needs the change |
| all | 5, 8 | — | descriptive (§5, §8) | D |

## 1. Held-out balance leakage

**Method.**
- **Masks derived independently** from the variable definitions: `v16_engine.VARS`, `v13_common.Trial` (PS-Clinical = `roles.json` core: demographics, 9 imputed vitals/labs including LVEF and creatinine, diagnoses, utilisation counts, medication-order flags) and `heldout_matrix`.
- **Data-driven check** (`leakcheck`, 38 trials): within-trial Spearman between each of the 54 held-out items (observed values) and every PS-Clinical input. eGFR was also compared with CKD-EPI 2021 recomputed from the PS creatinine, age and sex. hdPS top-200 code families were counted.
- **Re-analysis:** the full paper2 sweep (337 rows × S32 / S35 / S38) was recomputed from the saved per-item SMDs with the clean masks, plus the original masks on S35. BH used exactly paper2's families. No refitting was needed.

**Leakage map used ("clean"; a cell's mask is rung ∪ arm block; placebos take the real arm's mask):**

| Source | 54-item panel | 58-item panel only | Basis |
|---|---|---|---|
| PS-Clinical | 9 `smd_obs_*` (as in v1) + **echo EF, LV systolic grade, eGFR** (42 items remain) | all 4 coded items | EF ρ = 1.00 with LVEF (38/38 trials); LV systolic grade median \|ρ\| 0.91; eGFR vs CKD-EPI(PS creatinine, age, sex) median ρ 0.83 (max 0.97), i.e. derived |
| Sensitivity "clean + soft" | + BUN, LVESVi, GLS | | strongest measured-value correlates: BUN ~ creatinine 0.49; LVESVi ~ LVEF 0.75 (max 0.85); GLS ~ LVEF 0.61 |
| hdPS | none | all 4 coded | `rx_` levels in top 200 in 38/38 trials (median 32) → `mean_meds`; E&M `px_992–994` in 35/38 → `mean_util`; investigator diagnoses → `B_mean`, prognostic score |
| PS-CVD5 | none | `B_mean`, prognostic score | pool-B dx in the families of the 5 diagnoses; prognostic score is a linear predictor of core covariates |
| PS-Flags | none | `B_mean`, prognostic score | pool-B dx components are themselves flags |
| CLMBR-T (and permuted, 32-PC) | none | all 4 coded | coded-record summaries of the codes CLMBR-T embeds. CLMBR-T is code-only (`docs/v18/CLMBR_LEAKAGE.md`: numeric values dropped), so on the 54 items only soft proxies remain (R2: max within-trial \|ρ\| of any PC with any item 0.45) |
| ECG | none | none | |

**Agreement with R2** (`git show r2:docs/r2/LEAKAGE_MAP.md`, `leakage_map.json`):
- **Same 54-item masks:** S3 (PS-Clinical) masks echo EF, LV systolic grade and eGFR, and leaves BUN unmasked. R2 also reports BUN \|ρ\| = 0.48.
- **Same 58-item masks** for S1, S2b, S3 and CLMBR-T.

**Disagreements:**
- **(a) PS-Flags and `mean_meds` / `mean_util`.** R2 masks them for PS-Flags (S2a) as "coded-record representation". Flags are diagnosis codes only, so I treat meds and utilisation as soft for PS-Flags. This affects only 58-item PS-Flags rows, none of them headline.
- **(b) LVESVi and GLS.** I add them, with BUN, as a sensitivity (clean + soft). R2's pooled ρ ≥ 0.80 rule did not fire, but LVESVi reaches \|ρ\| 0.85 within some trials and is a component of EF.

**Result.**
- **54-item rows not involving PS-Clinical:** unchanged to 0.0 in S32 and S38.
- **PS-Clinical rows (72 of 337):** all change.
- **Head-to-head that matters (C14):** −4.9% → −2.6%, and 9/32 → 14/32 trials better. GBM −11.9% (q .007) → −8.5% (q .058); with soft correlates also masked, −5.4% (q .25).
- **Other configurations:**
  - cal01 −6.4% → −3.6%;
  - m13 −4.9% → −2.1%;
  - overlap −3.5% → −0.4%;
  - IPTW −11.2% → −7.5%.
- **PS-CVD5 + ECG + CLMBR-T vs PS-Clinical:** −5.4% → −4.3%.
- **S35 and S38:** the original masking would have given CIs excluding 0 (S35 −6.3% [−12.4 to −0.6]; S38 −5.7% [−11.7 to −0.4]). Clean values are −3.3% and −2.9%. The GBM row stays significant there (q .013 / .015).
- **Within-rung PS-Clinical rows** share the leak and move by < 1 point (C9).
- **58-item panel:** CLMBR-T 14.0 → 12.4% and both 15.3 → 13.5%. The extra gain on 58 items came entirely from the coded-record items CLMBR-T sees.

**Recommended wording for paper2.md:**
- **Methods (Covariate balance):** after "At PS-Clinical, the characteristics included in that PS were also removed", add: "as were echocardiographic EF and LV systolic grade, which measure LVEF, and eGFR, which is derived from creatinine, age and sex (42 characteristics)".
- **Results:** replace the PS-Clinical sentence with: "Compared with PS-Clinical, PS-CVD5 + CLMBR-T did not differ detectably (−2.6%; 95% CI, −8.4% to 3.2%; q = .56); with the gradient-boosted PS it was worse (−8.5%; 95% CI, −16.2% to −2.1%; q = .058)."
- **Conclusion:** replace "and was nominally less well balanced than a PS with measured clinical covariates" with "and did not differ detectably from a PS with measured clinical covariates on characteristics that PS did not itself include".
- **58-item sentence:** add "of which the additional gain with CLMBR-T reflects coded-record summaries that CLMBR-T itself sees (leakage-clean: 8.8%, 12.4% and 13.5%)".
- **Count:** "98 reached q < .05" → 96 (clean).

## 2. RCT agreement driven by shrinkage to the null

**Method.** All six configurations, P5 arms, S32 and S35 (`d2_shrinkage.csv`):
- mean |log HR| and SE, base vs arm;
- trials moved toward the null;
- a pure-shrinkage counterfactual (PS-CVD5 log HRs × s, where s = mean |arm| / mean |base|);
- the benchmark-permutation null mean of the |Δ| reduction (20,000 draws).

**Result (main, S32).**

| Arm | Mean \|log HR\| | Trials toward null | Pure-shrinkage \|Δ\| (observed) | Random-benchmark gain / observed gain |
|---|---|---|---|---|
| ECG | 0.302 → 0.268 (s = 0.89) | 20/32 | 0.202 (0.196) | 1.19 |
| CLMBR-T | 0.302 → 0.191 (s = 0.63) | 26/32 | 0.161 (0.166) | 1.40 |
| Both | 0.302 → 0.183 (s = 0.60) | 24/32 | 0.158 (0.158) | 1.36 |

- **Mean SE** rises with CLMBR-T, from 0.118 to 0.123–0.129. This and shrinkage drive SDA: pure shrinkage plus base SEs already gives 28/32.
- **The one place the ECG beats pure shrinkage** is m13: shrinkage explains 18% of the gain, and the random-benchmark gain is 0.5× observed (permutation P = .037).
- **Every sentence in paper2 that claims agreement** was checked against these results:

| Sentence | Verdict |
|---|---|
| Results "Agreement": "closer … on average, but not toward each trial's own result … attenuation … accounts for the gains" | consistent; could add "scaling the PS-CVD5 estimates toward the null by the same factor reproduced the reduction (0.202, 0.161, 0.158)" |
| EA 15 → 22 / 20 / 20 and SDA 24 → 30 | consistent (caveat present). Note SDA also rises with the larger SE of CLMBR-T models |
| PS-Flags agreement (P = .50; permutation .97) | consistent |
| CV PS-Flags "agreed less well … permutation P = .001" | consistent as "nominal sensitivity"; S35 permutation P = .029, P = .12 |
| "For the ECG, the agreement pattern of our previous report reproduced …" | consistent; under GBM the ECG moves estimates away from the null (s = 1.06), so that signal is not attenuation, but it is a single nominal row |
| Quality strata (C22) | descriptive; reverses under blind tiers (§6). Recommend dropping or marking as uninformative |
| MIMIC "permuted ECG moved it as much" | consistent |
| MIMIC PEPTIC "adding the ECG moved the estimate toward the null … permuted did not" | **tighten**: one trial; movement toward the null is the generic attenuation mechanism. Add "in a single negative-control trial, not separable from attenuation" |
| Discussion "in most configurations reassigning RCT results … gave reductions as large" | consistent by the permutation P (ECG ≥ .20 in 4 of 6 configurations; CLMBR-T and both ≥ .78 in all 6). By mean random-benchmark gain: ≥ observed for CLMBR-T and both in all 6 configurations (1.2–2.8×), but for the ECG only in main and cal01. Elsewhere the ECG's gain was larger than random (m13 0.50×, overlap 0.78×) or absent (IPTW) |
| Conclusion "Neither representation produced trial-specific agreement" | **tighten**: "… trial-specific agreement gains over its base PS"; the only trial-specific signal (vs CV PS-Flags) was a nominal sensitivity result |

## 3. Fixed L2 penalty C = 1

**Verification of the cross-validated PS-Flags:**
- the refitted PROTECT AF FlagsCV cell matches exactly;
- `cv_C` re-run on PROTECT AF, RAFT-AF and VALIANT reproduces the logged C exactly (0.00316, 0.00316, 0.001);
- over S32, the chosen C is in {3.2e-4, 1e-3, 3.2e-3}, i.e. 316–3,162× stronger than C = 1, which confirms "300 to 3,000";
- the in-sample C statistic of PS-Flags at C = 1 in PROTECT AF is 1.00 (PS-CVD5 0.66);
- with CV, PROTECT AF re-enters (32 trials).

**Head-to-head:**
- C = 1: 0.7% (31 trials); CV: −1.5% (−7.5 to 4.4; 32 trials); S35 CV −2.2% (−8.2 to 3.9).
- **Conclusion (no detectable difference; never in CLMBR-T's favour): unaffected.**

**ECG caveat (R2, not re-derived; `audits/claude-r2/followup/h1_ecg_decomposition.csv`).** With a CV log-loss penalty for every PS:
- PS-CVD5 + ECG vs base falls from 8.8% (4.4–13.3) to 5.7% (−0.5 to 11.4) in S32;
- in R2's primary 35 on 56 leakage-clean items it is 4.7% (−0.4 to 9.9);
- vs permuted ECG it remains 7.9% (3.1–12.5).

Recommended addition to Limitations: "With a cross-validated penalty, the ECG gain with PS-CVD5 was smaller (5.7%; 95% CI, −0.5% to 11.4%), although it remained larger than that of the permuted ECG."

Not quantified here: the CV-penalty effect on the CLMBR-T arms and on the plasmode arms.

## 4. IPTW instability

**Claims resting on IPTW:**
- C15, PS-Demo + CLMBR-T "better" than PS-Flags and hdPS under IPTW (already labelled an artefact);
- C17, ECG persists and CLMBR-T is lost under IPTW;
- 7 of the 98 q < .05 rows (C18).

No primary, PS-Flags or PS-Clinical conclusion rests on IPTW.

**Effective sample size.** Median ESS fraction (min over arms) under IPTW, S32:

| Base PS | base | + ECG | + CLMBR-T | + both |
|---|---|---|---|---|
| PS-Demo | 0.87 | 0.72 | 0.44 | 0.39 |
| PS-CVD5 | 0.72 | 0.67 | 0.44 | 0.38 |
| PS-Flags | 0.18 | 0.16 | 0.14 | 0.12 |
| hdPS | 0.34 | 0.27 | 0.24 | 0.21 |
| PS-Clinical | 0.54 | 0.44 | 0.40 | 0.35 |

**Restriction to adequate ESS.** Restricting to trials with an ESS fraction ≥ 0.5 in both cells gives:
- PS-CVD5 + ECG 4.8% (0.1–10.0; 21 trials);
- PS-CVD5 + CLMBR-T **7.9% (1.2–16.7; 11 trials)**;
- PS-Demo + CLMBR-T vs hdPS 9.2% (6.0–12.1; 7 trials);
- vs PS-Flags only 4 trials, so not estimable.

**Recommended wording:** "With IPTW, the CLMBR-T gains were lost overall (−2.0%), but not in the 11 trials with adequate effective sample size (7.9%; 95% CI, 1.2%–16.7%), indicating weight instability rather than absence of a gain."

## 5. Ad hoc PS ladder (descriptive)

The rungs are not ordered by data availability:
- PS-Flags (all ICD-10 3-character codes, full history) and hdPS (one-year codes + labs-measured flags + investigator diagnoses) draw on the same coded record with different windows;
- PS-Clinical adds measured values, which are missing not at random.

"Diminished as hand-built covariates became richer" is therefore an ordering by covariate count rather than by information source. PS-CVD5 was chosen as primary after paper 1's results were seen. No number changes.

**Recommended wording:** state that the ladder was defined post hoc and is not a data-availability hierarchy.

## 6. Quality tiers and trial set finalised after results

**Method.**
- Every headline row was recomputed on S38 and on R2's blind, results-free primary set (S35; excludes FRAIL-AF, ACTIVE W and TRANSFORM-HF, and keeps the 6 v1 "limited" trials).
- S35 used both original and clean masks.
- The physiologic and domain label tests, the CV PS-Flags head-to-heads and the quality strata (by R2 blind tier) were also recomputed.

**Result.** Every primary balance conclusion holds on S35 and S38 (table above):
- C1–C3: 8.6 / 12.0 / 12.8%;
- C10: 0.4%;
- C11: −2.2%;
- C16: no agreement row survives FDR in S35; permutation P .36–.64.

What changes:
- **Physiologic-label contrast:** the ECG loses nominal significance (P .095; q .28).
- **CLMBR-T vs ECG** is ahead at q < .05 in 2 of 6 configurations on S35, not 3.
- **CLMBR-T vs PS-Clinical:** without the leakage fix, the CI would exclude 0 on S35 and S38 (§1).
- **Quality-stratified agreement (C22):** under blind tiers, ECG gains are similar in A/B and C, and the CLMBR-T gain is larger in C (0.103 vs 0.056), reversing paper2's direction.
- **TRANSFORM-HF,** one of the 10 physiologic trials, is excluded from S35; the LV-systolic domain result survives (q .019 / .047 / .019).

**Recommended wording:**
- report S35 as the results-blind sensitivity set alongside S38;
- delete the quality-stratum sentence, or state that its direction depends on the tiering.

## 7. Many contrasts

**FDR family per headline claim:**

| Claim | Family |
|---|---|
| C1–C3, C6–C10, C13–C18 | paper2 sweep BH (balance: 4 endpoints × 337 rows; agreement: 3 endpoints × 337), as declared |
| C19 | label family |
| C20–C21 | domain family |
| C11–C12 (flagscv), C24 (retention), C25 (plasmode), C26 (MIMIC) | outside FDR, nominal; paper2 says so for flagscv, retention and MIMIC; it should say so for plasmode (Monte Carlo SEs only) |

All quoted q values match `core/sensitivity.csv`.

**Checks.**
- **(a) Global pooling.** Pooling all families (5,006 P values) into one BH lowers q: 13 agreement rows reach q < .05, because many small balance P values make BH more lenient. Pooling is therefore not a stricter test, and paper2's separate agreement family is the conservative choice.
- **(b) Benjamini–Yekutieli** within paper2's families, valid under the strong dependence between these rows:
  - **Survive:** the primary gains (q .016 / .004 / .020), the placebo contrasts (ECG vs permuted .023; CLMBR-T vs permuted .048) and the PS-Demo rows.
  - **Do not survive:** CLMBR-T vs ECG at PS-Demo (.17), hdPS + ECG (.25), CLMBR-T worse than ECG at hdPS (.16), CLMBR-T > ECG in m13 / overlap / GBM (.17 / .09 / .28), the GBM PS-Clinical row (.054) and the IPTW PS-Flags row (.074).
  - **Counts:** 98 → 65 balance rows; primary configuration 18 → 13.

**Recommended wording.** Describe the cross-representation and hdPS results (C6–C8) as surviving BH but not a dependence-robust correction.

## 8. The substitution question (descriptive)

paper2 never asks whether a representation recovers what measuring physiology buys. The nearest contrasts are PS-CVD5 (+ representation) vs PS-Clinical. On leakage-clean items, the gap between PS-CVD5 and PS-Clinical is −12.9% (−18.7 to −7.6; S32). With the ECG, CLMBR-T or both added, the remaining gap is −3.0% / −2.6% / −4.3%. Roughly 70–80% of the gap on these 42 items closes; each contrast is paired on its own item set, so this is an approximation (`d8_substitution_gap.csv`).

This cannot answer the substitution question, because the items PS-Clinical measures (vitals, core labs, LVEF and their duplicates) are exactly those excluded from the comparison.

**Recommended wording:** state in Limitations that the design cannot assess substitution for measured physiology.

## 9. MIMIC v20 window defect

**Confirmed from source** (`audits/claude-v21-paper2/mimic/windowfix/summary/balance.csv`, `agreement.csv`; 4,000-resample CI):

| | v20 | Fixed |
|---|---|---|
| hdPS + ECG | 7.54% (−0.40 to 16.23) | **8.12% (−0.09 to 17.29)** |
| PS-Clinical-lite + ECG | 1.15% (−9.12 to 11.82) | **2.98% (−8.59 to 15.23)** |
| PS-Sparse | 10.2% | 10.9% (8.3–14.1) |

- **PS-Demo:** 10.3% (6.4–14.5), 41.2 → 51.6%, permuted −2.5% and 14.5% (index-day excluded) are identical.

**Sentences affected:**
- **paper.md line 91:** "smaller with the hdPS (7.5%; 95% CI, −0.4% to 16.2%) and PS-Clinical-lite (1.2%; 95% CI, −9.1% to 11.8%)" → "(8.1%; 95% CI, −0.1% to 17.3%) and PS-Clinical-lite (3.0%; 95% CI, −8.6% to 15.2%)".
- **paper.md line 92:** "it decreased with the ECG for each of the 4 PS specifications, with the ECG outperforming the permuted-ECG placebo for 3 of 4" still holds with the fixed values: sparse 0.322 → 0.200 (permuted 0.280); hdPS 0.215 → 0.179 (permuted 0.173); clinical-lite 0.284 → 0.172 (permuted 0.244).
- **supplement eTable 6B:** the PS-Sparse, hdPS and PS-Clinical-lite rows need replacing (`MIMIC_PAPER2.md` §6 gives both CI conventions).

**paper2.md:**
- **Results MIMIC paragraph: unaffected.** The PS-CVD5 analog uses earlier admissions in all 8 trials.
- The "with index-admission codes included, 11.5%" sensitivity deliberately uses the defective window. Suggest labelling it as such.
- The Limitations sentence and the change-log note already state the corrected numbers correctly.

## Files

Code (new; not committed):
- `scripts/v1_audit/defect_impact.py`: gate, leakcheck, sweep, extras;
- `scripts/v1_audit/defect_extras.py`: defects 2, 3, 4, 6, 7, 8;
- `scripts/v1_audit/claim_table.py`.

Restricted outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/defects/`.

| Defect | Files |
|---|---|
| Gate | `gate.csv` |
| 1 | `leak_rho_summary.csv`, `leak_rho_top_per_item.csv`, `restricted_leak_rho_per_trial.parquet`, `hdps_code_families.csv` |
| 1, 6 | `sweep_sensitivity.csv`, `sweep_domains.csv`, `claim_rows.csv`, `q_counts_by_variant.csv` |
| 2 | `d2_shrinkage.csv` |
| 3 | `d3_flagscv_s35.csv`, `d3_flags_penalty.json` |
| 4 | `d4_iptw.csv` |
| 6 | `d6_labels*.csv`, `d6_labels_gate.json`, `d6_quality_strata.csv` |
| 7 | `d7_by_families.csv`, `d7_global_fdr.csv` |
| 8 | `d8_substitution_gap.csv` |

Re-run (CPU, ≤ 16 workers; about 12 minutes in total, of which the sweep is about 10):

```
cd scripts/v1_audit
python defect_impact.py gate
python defect_impact.py leakcheck
python defect_impact.py sweep
python defect_impact.py extras
python defect_extras.py
python claim_table.py
```
