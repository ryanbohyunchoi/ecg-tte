# The 31-trial primary set (s31): headline numbers next to the 32-trial values

Queue 2026-10-14, Step 2 (`docs/queue/QUEUE_2026_10_14_S31.md`; `pipeline.md` update 2026-10-14). Built by `scripts/s31/s31_numbers.py` from the existing cells and the s31 Python summaries (`scripts/s31/s31_summaries.py`).

- **s31 (primary):** paper 1's 32 trials (v19 tiers, Limited excluded) minus **PROTECT AF**, now excluded at feasibility (smaller arm < 350 patients with an ECG). Trial flow: 99 → 37 feasible → 31 analysed (tiers of the 37: 3 / 11 / 17 / 6).
- **32 (sensitivity):** paper 1's 32 with PROTECT AF, the previous primary. The size-rule change is post hoc: it was made after near-separation of the rich PS models was seen in PROTECT AF.
- **Design (unchanged):** version 1 cohorts; PS-CVD5 primary; fixed C = 1; 1:1 nearest neighbour, caliper 0.2; 54 held-out items with the leakage-corrected masks; PS-Clinical without LVEF, 5-draw MI.
- **Endpoint:** relative reduction in the across-trial mean |SMD| (95% CI from 4,000 trial resamples); P = exact sign-flip across trials on the per-trial mean |SMD| (one-sided for a representation vs its base or placebo, two-sided otherwise).
- **Checks:** the S32 rows of every summary equal the committed runs (to ≤ 1.5e-14); every summary value is re-derived from the cells (max deviation: 4.5e-14 percentage points, 9.7e-17 in P; 0 mismatches in trial counts); the index-day and CV-penalty rows reproduce their published 32-trial values before the s31 value is taken.

## 1. Primary: PS-CVD5 + ECG vs PS-CVD5

| Quantity | s31 (primary) | 32 trials (sensitivity) |
|---|---|---|
| Relative reduction in mean \|SMD\| | **8.7% (4.2 to 13.5)** | 8.8% (4.4 to 13.3) |
| One-sided sign-flip P (mean \|SMD\|) | <.001 | <.001 |
| Trials with lower mean \|SMD\| | 20/31 | 21/32 |
| Mean \|SMD\|, PS-CVD5 → + ECG | 0.129 → 0.117 | 0.130 → 0.118 |
| Items with \|SMD\| < 0.1 | 53.9% → 57.3% (+3.3 points; 19/31 trials improved; P = .015) | 53.4% → 57.0% (+3.6 points; 20/32; P = .009) |
| BH-FDR q (within-set balance family) | .004 | .003 |
| Permuted ECG vs PS-CVD5 (two-sided P) | 0.4% (-3.5 to 4.3), P = .83 | 1.0% (-2.8 to 4.8), P = .63 |
| ECG vs permuted ECG | 8.3% (4.0 to 12.7), P < .001 | 8.0% (3.6 to 12.2), P < .001 |
| \|Δ log HR\| vs RCT, PS-CVD5 → + ECG | 0.232 → 0.198 (20/31 closer; sign-flip P = .035) | 0.226 → 0.196 (20/32; P = .049) |
| Benchmark-permutation P (trial-specificity) | 0.56 | 0.70 |

### Domains (PS-CVD5 + ECG vs PS-CVD5)

| Domain (items) | s31 | 32 trials |
|---|---|---|
| Vitals & core labs (9) | 8.5% (2.8 to 14.0) | 8.7% (3.4 to 13.8) |
| Other labs (10) | 6.5% (-1.7 to 15.1) | 6.9% (-0.8 to 14.8) |
| Echo: LV structure (7) | 15.0% (3.5 to 25.3) | 14.9% (3.5 to 25.3) |
| Echo: LV function (4) | 16.1% (2.5 to 28.6) | 16.4% (2.5 to 28.5) |
| Echo: diastolic / LA (8) | 16.0% (5.5 to 24.7) | 16.1% (6.1 to 24.3) |
| Echo: RV / pulmonary (7) | -2.2% (-14.8 to 8.6) | -1.8% (-13.6 to 8.2) |
| Echo: valves / aorta (9) | 3.7% (-4.5 to 11.5) | 4.2% (-3.6 to 11.9) |
| Echo, all 35 items (35) | 9.1% (3.1 to 15.3) | 9.2% (3.3 to 15.2) |

## 2. PS ladder (main configuration)

Mean \|SMD\| over the 54 items (mean across trials of each trial's mean); relative reduction vs PS alone (paired by trial).

| Level | Unmatched | PS alone | + ECG | + CLMBR-T | + CLMBR-T + ECG | + ECG (s31) | + ECG (32) | + CLMBR-T (s31 / 32) | + CLMBR-T + ECG (s31 / 32) |
|---|---|---|---|---|---|---|---|---|---|
| PS-Demo | 0.143 (0.144) | 0.141 (0.143) | 0.126 (0.127) | 0.112 (0.114) | 0.106 (0.107) | 10.6% (5.3 to 15.6), P < .001 | 11.3% (6.0 to 16.1), P < .001 | 20.6% / 20.7% | 25.4% / 25.8% |
| PS-CVD5 | 0.143 (0.144) | 0.129 (0.130) | 0.117 (0.118) | 0.112 (0.114) | 0.110 (0.112) | 8.7% (4.2 to 13.5), P < .001 | 8.8% (4.4 to 13.3), P < .001 | 12.9% / 12.4% | 14.6% / 13.5% |
| PS-CVD10 | 0.143 (0.144) | 0.118 (0.121) | 0.114 (0.115) | 0.110 (0.112) | 0.110 (0.112) | 3.8% (-1.6 to 9.0), P = .095 | 5.0% (-0.8 to 10.3), P = .051 | 7.0% / 7.4% | 6.9% / 7.0% |
| PS-Clinical (no LVEF, MI) | 0.142 (0.143) | 0.118 (0.119) | 0.114 (0.115) | 0.113 (0.117) | 0.114 (0.116) | 3.3% (-1.1 to 7.5), P = .079 | 3.2% (-1.0 to 7.2), P = .075 | 4.4% / 2.2% | 3.4% / 2.7% |
| hdPS | 0.143 (0.144) | 0.114 (0.118) | 0.106 (0.109) | 0.113 (0.122) | 0.104 (0.104) | 7.1% (0.7 to 12.8), P = .015 | 7.6% (1.7 to 13.0), P = .008 | 0.6% / -3.5% | 8.5% / 8.5% |

Levels: s31 value, with the 32-trial value in brackets. Trials behind each s31 point: PS-Demo 31/31/31/31; PS-CVD5 31/31/31/31; PS-CVD10 31/31/31/31; PS-Clinical (no LVEF, MI) 31/31/31/31; hdPS 31/31/31/31 (PS alone / + ECG / + CLMBR-T / + both). Every arm has all 31 trials.

|Δ log HR| and benchmark-permutation P for + ECG at each level:

| Level | s31 | 32 trials |
|---|---|---|
| PS-Demo | 0.255 → 0.207; permutation P = .11 | 0.251 → 0.205; P = .26 |
| PS-CVD5 | 0.232 → 0.198; permutation P = .56 | 0.226 → 0.196; P = .70 |
| PS-CVD10 | 0.213 → 0.173; permutation P < .001 | 0.208 → 0.171; P = .003 |
| PS-Clinical (no LVEF, MI) | 0.171 → 0.151; permutation P = .003 | 0.166 → 0.149; P = .002 |
| hdPS | 0.182 → 0.172; permutation P = .089 | 0.181 → 0.167; P = .11 |

## 3. Six PS methods (PS-CVD5 + ECG vs PS-CVD5)

| Method | s31 | 32 trials |
|---|---|---|
| 1:1, caliper 0.2 | 8.7% (4.2 to 13.5), P < .001, 20/31 | 8.8% (4.4 to 13.3), P < .001, 21/32 |
| 1:1, caliper 0.1 | 7.6% (3.1 to 12.5), P = .002, 21/31 | 7.8% (3.2 to 12.6), P = .001, 22/32 |
| 1:3 | 6.2% (2.8 to 9.9), P < .001, 24/31 | 6.4% (2.8 to 9.9), P < .001, 25/32 |
| IPTW | 5.1% (1.6 to 8.8), P = .002, 25/31 | 4.8% (1.5 to 8.5), P = .003, 25/32 |
| Overlap weights | 7.5% (4.4 to 11.0), P < .001, 28/31 | 7.4% (4.3 to 10.9), P < .001, 29/32 |
| Gradient-boosted PS | -1.5% (-8.0 to 4.2), P = .67, 16/31 | -1.1% (-7.3 to 4.3), P = .63, 17/32 |

CIs excluding 0: s31 5 of 6; 32 trials 5 of 6.

## 4. Agreement with the RCTs by emulation quality (PS-CVD5, main configuration)

Tiers are the v19 tiers of the 37 feasible trials (s31 column) or of the 38 (32-trial column). Agreement metrics: r = Pearson r with the RCT log HRs; estimate agreement = emulated HR inside the RCT 95% CI; standardized-difference agreement = |z| < 1.96. Benchmark-permutation P: one-sided for + ECG.

| Group (trials, s31 / 32) | Arm | r | Estimate agr. | Std-diff agr. | Mean \|Δ log HR\| | Closer vs PS alone | Benchmark-perm. P |
|---|---|---|---|---|---|---|---|
| Excellent + Good (14 / 15) | PS-CVD5 | 0.63 (0.65) | 43% (47%) | 71% (73%) | 0.230 (0.216) |  |  |
|  | + ECG | 0.69 (0.70) | 79% (80%) | 86% (87%) | 0.176 (0.171) | 9/14 (9/15) | 0.48 (0.65) |
| Moderate (17 / 17) | PS-CVD5 | 0.50 (0.50) | 47% (47%) | 76% (76%) | 0.235 (0.235) |  |  |
|  | + ECG | 0.48 (0.48) | 59% (59%) | 71% (71%) | 0.217 (0.217) | 11/17 (11/17) | 0.63 (0.63) |
| Limited (6 / 6) | PS-CVD5 | -0.05 (-0.05) | 0% (0%) | 33% (33%) | 0.211 (0.211) |  |  |
|  | + ECG | -0.12 (-0.12) | 17% (17%) | 33% (33%) | 0.192 (0.192) | 3/6 (3/6) | 0.87 (0.87) |

s31 value first, the 32-trial (38-trial tier) value in brackets.

Benchmark-permutation P for PS-CVD5 + ECG: s31 0.56, all 37 feasible 0.53, framework v2.0 provisional 29 0.90 (32-trial: 0.70; all 38 0.68). PS-CVD10 + ECG: s31 P < .001 (32-trial P = .003; post hoc, exploratory).

## 5. Robustness rows of the lab deck (PS-CVD5 + ECG vs PS-CVD5, 54 items)

| Check | s31 | 32 trials |
|---|---|---|
| ECG vs permuted, range over five trial sets | 8.3 to 9.4% (s31; Excellent + Good of the 37; all 37; v2.0 29; v2.0 30) | 8.0 to 9.4% (32; Excellent + Good; all 38; 29; 30) |
| Comparator-cluster sign-flip P; largest leave-one-trial-out P | .002 (14 clusters); .001 | .002 (14 clusters); <.001 |
| PS-Clinical (no LVEF), 5-draw MI, + ECG | 3.3% (-1.1 to 7.5), P = .079; single draws -2.9 to 6.5% | 3.2% (-1.0 to 7.2), P = .075; draws -1.8 to 6.0% |
| Spec-v2 cohort fixes (point estimate; version 1 → fixed cohorts) | 8.7% → 7.0%; random removal median 6.7 (2.6 to 9.0) | 8.8% → 6.6%; 6.9 (2.8 to 9.3) |
| Framework v2.0 sets (version 1 cohorts; unchanged, both include PROTECT AF) | provisional 29: 9.4% (4.5 to 14.4); rescored 30: 9.9% (5.2 to 14.7) | same |
| CV log-loss penalty (R2 cells, scenario S1) | 5.2% (-1.0 to 11.3), 21/31 | 5.7% (-0.5 to 11.4), 22/32 |
| Index-day ECGs excluded (ECG ≥ 1 day before index) | 7.8% (0.7 to 14.6), P = .021, 19/31 | 6.9% (0.4 to 13.4), P = .033, 19/32 |

R2's own CV-tuned primary (35-trial R2 set, 56 R2 leakage-clean items: 4.7%) is a different design and is not re-derived here.
