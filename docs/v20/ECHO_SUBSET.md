# v2.0 echo-subset analysis: real-data bias removal by the ECG (results)

Plan `docs/v20/ECHO_SUBSET_PLAN.md` (committed e098888 before any result). Code `scripts/v20/echo_subset.py`. Outputs `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-echo-subset/` (`per_trial.csv`, `pooled.csv`, `eligibility.csv`, `gate.csv`, `summary.json`; umask 077; counts 1–10 suppressed). Figure `docs/v20/ECHO_SUBSET_F.png`. Exploratory.

## Verdict (plain language)

- **Balance: clear.** In patients with a measured LVEF, adding the ECG to the demographic PS closes **about 60% of the LVEF imbalance** that adjusting for LVEF itself closes. After matching, |SMD| for LVEF goes from 0.187 to 0.097; with LVEF in the PS it is 0.036; with the permuted ECG, 0.182 (about 3% closed). For NT-proBNP, the ECG closes about 39% (0.230 → 0.149; with NT-proBNP itself, 0.022).
- **HR shift: too noisy to pin down.** The ECG moves the log HR in the same direction as adjustment for measured physiology: slope F = 0.69 for LVEF (95% CI 0.19–1.00), with a correlation of 0.63 across trials. But the permuted-ECG placebo gives F = 0.42. The two F values share the same base estimate, and re-matching alone moves log HR by about as much as physiology adjustment does (mean |shift| about 0.1). The placebo-corrected F is **0.27 (−0.31 to 0.72)** for LVEF and 0.11 (−0.19 to 0.52) for NT-proBNP. Both are consistent with the plasmode prediction (partial R² 0.23 and 0.19), but neither can be distinguished from 0 with 20 and 16 trials.
- **Adjusting for measured physiology did not bring estimates closer to the RCTs.** Mean |Δ log HR vs RCT| in the LVEF subset with the demographic PS was 0.228 for the base PS, 0.219 with the ECG and 0.272 with LVEF. In real data, the physiology shift therefore mixes confounding correction with matching noise and subset effects.
- **Bottom line for the paper:**
  - Real data confirm the mechanism: the ECG recovers a large share of the imbalance in measured LVEF and NT-proBNP.
  - They cannot precisely estimate the share of the resulting HR bias removed, because estimation noise dominates.
  - The plasmode remains the only precise estimate of bias removed. The echo subset is its consistency check: point estimates are of similar magnitude (placebo-corrected 0.27 vs predicted 0.23 for LVEF), with wide CIs.

## Reproduction gate
Full-cohort P1 base log HR matched `claude-v17-confirm/results_all.csv` / `claude-v18-af-confirm/results_af5.csv` in 38/38 trials (max |Δ| 8.3e-17). There were 1,316 subset cells and no fit errors.

## Eligibility (smaller arm ≥ 300 and ≥ 50 events within the subset)

| Subset | 38 trials | 32-trial primary set |
|---|---|---|
| E (echo LVEF) | 26 | 20 |
| N (NT-proBNP) | 21 | 16 |

## Balance on the defining variable after matching (mean |SMD| across trials; 32-trial set)

| Subset, base PS | PS alone | + ECG | + permuted ECG | + measured physiology | Share of the imbalance closed by the ECG* |
|---|---|---|---|---|---|
| E, demographic | 0.187 | 0.097 | 0.182 | 0.036 | **60%** (placebo 3%) |
| E, five-diagnosis | 0.121 | 0.096 | 0.132 | 0.037 | 30% |
| E, hdPS200 | 0.130 | 0.088 | 0.122 | 0.040 | 47% |
| E, clinical minus LVEF | 0.118 | 0.089 | 0.114 | 0.041 | 38% |
| N, demographic | 0.230 | 0.149 | 0.238 | 0.022 | **39%** (placebo −4%) |
| N, five-diagnosis | 0.191 | 0.136 | 0.171 | 0.046 | 38% |
| N, hdPS200 | 0.127 | 0.090 | 0.108 | 0.044 | 45% |
| N, clinical | 0.096 | 0.078 | 0.093 | 0.025 | 25% |

\*(PS alone − + ECG) / (PS alone − + physiology). This column was computed descriptively and is not in the plan; see deviation 1.

## Pooled F: share of the physiology-driven log-HR shift reproduced by the ECG (slope through the origin, trial bootstrap 95% CI)

Primary set, 32 trials; single physiology variable.

| Subset | Base PS | k | F, ECG | F, permuted ECG | F, noise | Placebo-corrected F (ECG − permuted) | Plasmode prediction (weighted partial R²) |
|---|---|---|---|---|---|---|---|
| E | demographic | 20 | **0.69 (0.19 to 1.00)** | 0.42 | 0.31 | **0.27 (−0.31 to 0.72)** | 0.23 |
| E | five-diagnosis | 20 | 0.31 (−0.13 to 0.69) | 0.54 | 0.14 | −0.23 (−1.13 to 0.35) | 0.17 |
| E | hdPS200 | 20 | 0.58 (−0.10 to 1.12) | 0.79 | 1.02 | −0.21 (−1.01 to 0.79) | 0.15 |
| E | clinical minus LVEF | 20 | −0.01 (−0.52 to 0.72) | −0.28 | 0.80 | 0.27 (−0.41 to 1.24) | 0.15 |
| N | demographic | 16 | 0.29 (−0.32 to 0.64) | 0.18 | 0.45 | 0.11 (−0.19 to 0.52) | 0.19 |
| N | five-diagnosis | 16 | 0.21 (−0.21 to 0.96) | 0.43 | 0.23 | −0.22 (−0.62 to 0.71) | 0.15 |
| N | hdPS200 | 16 | 0.21 (−0.62 to 0.68) | −0.01 | 0.91 | 0.22 (−0.64 to 0.62) | 0.09 |
| N | clinical | 16 | 0.65 (0.41 to 1.00) | 0.54 | 0.50 | 0.11 (−0.22 to 0.48) | 0.11 |

With the extended physiology set (LVEF, NT-proBNP, BMI and eGFR, with missing values imputed and flagged), the demographic PS in subset E gives F = 0.60 (0.24 to 0.79), permuted ECG 0.10, and placebo-corrected 0.51 (−0.10 to 0.83). For the 38-trial set, subset E with the demographic PS gives F = 0.64 (0.25 to 0.93) and placebo-corrected 0.26 (−0.31 to 0.64). All cells are in `pooled.csv`.

Why the placebos are large: num and den share logHR_base, so any re-matching noise in the base arm creates a positive correlation between them. The corrected F removes that shared component on average, but not its variance.

## Distance to the RCT (descriptive; mean |log HR − RCT log HR|; 32-trial set, subset E)

| Base PS | PS alone | + ECG | + LVEF |
|---|---|---|---|
| demographic | 0.228 | 0.219 | 0.272 |
| five-diagnosis | 0.219 | 0.202 | 0.203 |
| hdPS200 | 0.189 | 0.170 | 0.171 |
| clinical minus LVEF | 0.162 | 0.156 | 0.186 |

## Deviations (logged)
1. **Balance-based share closed.** Computed from the planned |SMD| outputs, but the ratio itself was not a prespecified summary. It is reported because the HR-based F proved too imprecise to interpret.
2. None other. The plan's fewer-than-10-trials rule did not trigger (k = 16–26).

## Caveats
- **The physiology shift is not the true bias:** in real data it includes matching noise and the effect of restricting to patients with the measurement.
- **The subset is not representative:** patients with echo or NT-proBNP are more often inpatients or referred.
- **These are exploratory post-hoc style analyses:** 32 cells per metric with overlapping bases; no multiplicity adjustment.
