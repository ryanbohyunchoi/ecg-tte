# v1.9 sensitivity: adherence / on-treatment and run-in estimands (38 trials, P1 / P5)

Exploratory sensitivity analysis. Plan `docs/v19/SENS_ADHERENCE_PLAN.md` (committed c1f22c3 before any result; one
logged deviation). Code `scripts/v19/sens_adherence.py`; outputs (umask 077)
`/mnt/raid0/rbc58/ecg-tte/audits/claude-v19-sens-adherence/` (`summary.csv`, `per_trial.csv`, `retention.csv`,
`deviation.csv`, `verify.csv`, `tables.md`). Aggregates only; counts 1–10 suppressed.

## Setting and reproduction

- Current analysis setting: the 38 trials of v1.8 (`v18_af_confirm` / `v18_embed_compare`), PS P1 (demographics) and
  P5 (+ HTN, T2D, CAD, AF, HF), arms base / +ECG32 / +permuted ECG32 / unmatched, 1:1 caliper-0.2 matching via
  `E.run_cell`. Every sensitivity estimand is computed on the **same matched set** as the primary ITT estimate.
- **Reproduction gate passed:** the recomputed ITT log HR, SE, n, n_t, n_c and n_pairs equal
  `claude-v18-embed-compare` for all 798 cells (38 trials × full/A/B × 7 cells), max |deviation| = 0.
- Estimands (v1.3 II2 / II3; deviation times from `v13_extract`, IPCW = `v13_design.ipcw`): per-protocol with
  stabilised IPCW, G = 365 (base) / 180 / 730; switch-only with IPCW; the same without weights (naive); 90-day
  run-in landmark (both pair members followed > 90 d and ≥ 1 repeat order of the assigned drug in (0, 90]); and
  (deviation 1) a 90-day landmark without the repeat-order rule.

## Not applicable (logged)

- **Per-protocol and run-in not applicable (one-time procedure arm): CABANA (ablation vs AAD), LAAOS III (surgical
  LAA occlusion), PROTECT AF (LAAO vs warfarin), RAFT-AF (ablation vs rate control).** They enter only the ITT
  column, so the sensitivity sets have 34 trials.
- **Registered run-in not estimable (≤ 50 patients kept):** P1: CANVAS, CARMELINA, CAROLINA, EMPEROR-Preserved,
  INSIGHT, LEADER, SUSTAIN-6 (k = 27); P5: the same + DECLARE (k = 26). All other estimands were estimable in all 34.
- Sequential designs, v1.3 rules, flagged in the per-trial table: PARADIGM-HF-seq and FRAIL-AF (sequential switch:
  an other-arm order after index censors), EAST-AFNET 4, AFFIRM and AF-CHF (add-on: only an AAD order censors the
  rate-control arm).

## Adherence in the matched samples

- Share of matched patients censored by protocol deviation before their event or end of follow-up (median over
  trials, base arm): G = 180 87%, G = 365 70%, G = 730 44%, switch-only 8%. Orders carry no days-supply, so
  "discontinuation" is mostly a refill artefact; switch-only is the cleanest on-treatment estimand.
- IPCW weights are well behaved (median of the per-cell maximum after truncation 1.1–1.5; max 2.0), so IPCW and
  naive estimates are nearly identical.
- Landmark retention (aggregate % of analysed matched patients kept at day 90, 34 trials): **registered run-in 10.3%**
  (P1 base; median 9.3%, range 2–25%; unmatched 32%), because only a minority have a repeat order within 90 days
  and both pair members must qualify. The plain 90-day landmark keeps 86% (unmatched 92%).

## Main results

|Δ| = mean |log HR − RCT log HR|; closer = trials with ECG |Δ| < base |Δ|; cons = % |z| < 1.96; p = exact one-sided sign-flip (ECG better); bs = within-set benchmark shuffle (20,000); cl = comparator-cluster sign-flip. Full cohort; A/B = split halves.


## P1

| estimand | set | k | \|Δ\| unmatched | \|Δ\| base | \|Δ\| +ECG | \|Δ\| +perm ECG | closer | cons base→ECG (perm) | p ECG vs base | p ECG vs perm | bs p | cl p (n cl) | p A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ITT (primary) | all38 | 38 | 0.261 | 0.258 | 0.207 | 0.285 | 25/38 | 58→76 (58) | 0.002 | 3e-04 | 0.220 | 0.021 (14) | 0.171 / 0.026 |
| ITT (primary) | applicable34 | 34 | 0.234 | 0.232 | 0.188 | 0.256 | 22/34 | 56→76 (56) | 0.008 | 9e-04 | 0.198 | 0.039 (13) | 0.403 / 0.055 |
| PP IPCW G=365 (base) | applicable34 | 34 | 0.329 | 0.315 | 0.251 | 0.330 | 25/34 | 53→65 (47) | 0.002 | 4e-04 | 0.040 | 0.003 (13) | 0.030 / 0.020 |
| PP IPCW G=180 | applicable34 | 34 | 0.388 | 0.363 | 0.305 | 0.404 | 23/34 | 53→59 (41) | 0.008 | 0.002 | 0.029 | 0.002 (13) | 0.149 / 0.002 |
| PP IPCW G=730 | applicable34 | 34 | 0.292 | 0.278 | 0.218 | 0.300 | 25/34 | 50→68 (50) | 7e-04 | 8e-05 | 0.098 | 1e-03 (13) | 0.287 / 0.004 |
| switch-only IPCW | applicable34 | 34 | 0.276 | 0.270 | 0.210 | 0.289 | 26/34 | 47→71 (53) | 4e-04 | 8e-05 | 0.121 | 6e-04 (13) | 0.403 / 0.014 |
| PP naive G=365 | applicable34 | 34 | 0.328 | 0.312 | 0.252 | 0.332 | 25/34 | 50→62 (44) | 0.004 | 4e-04 | 0.054 | 0.005 (13) | 0.047 / 0.024 |
| PP naive G=180 | applicable34 | 34 | 0.387 | 0.363 | 0.303 | 0.406 | 22/34 | 53→59 (41) | 0.006 | 0.002 | 0.023 | 0.002 (13) | 0.159 / 0.002 |
| PP naive G=730 | applicable34 | 34 | 0.291 | 0.278 | 0.220 | 0.301 | 26/34 | 47→62 (47) | 8e-04 | 9e-05 | 0.094 | 0.001 (13) | 0.264 / 0.007 |
| switch-only naive | applicable34 | 34 | 0.275 | 0.270 | 0.211 | 0.289 | 25/34 | 47→65 (53) | 4e-04 | 9e-05 | 0.125 | 9e-04 (13) | 0.439 / 0.011 |
| 90-d run-in landmark | applicable34 | 27 | 0.278 | 0.488 | 0.287 | 0.376 | 19/27 | 81→96 (74) | 0.015 | 0.054 | 0.721 | 0.010 (13) | 0.872 / 0.344 |
| 90-d landmark, no repeat-order rule (dev. 1) | applicable34 | 34 | 0.240 | 0.232 | 0.222 | 0.265 | 22/34 | 68→74 (62) | 0.340 | 0.030 | 0.803 | 0.530 (13) | 0.913 / 0.289 |

## P5

| estimand | set | k | \|Δ\| unmatched | \|Δ\| base | \|Δ\| +ECG | \|Δ\| +perm ECG | closer | cons base→ECG (perm) | p ECG vs base | p ECG vs perm | bs p | cl p (n cl) | p A / B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ITT (primary) | all38 | 38 | 0.261 | 0.224 | 0.195 | 0.224 | 23/38 | 68→71 (71) | 0.033 | 0.045 | 0.684 | 0.248 (14) | 0.135 / 0.517 |
| ITT (primary) | applicable34 | 34 | 0.234 | 0.213 | 0.180 | 0.205 | 22/34 | 68→71 (71) | 0.016 | 0.076 | 0.260 | 0.044 (13) | 0.258 / 0.852 |
| PP IPCW G=365 (base) | applicable34 | 34 | 0.329 | 0.292 | 0.237 | 0.258 | 23/34 | 62→62 (56) | 0.008 | 0.184 | 0.202 | 0.026 (13) | 0.250 / 0.801 |
| PP IPCW G=180 | applicable34 | 34 | 0.388 | 0.332 | 0.282 | 0.336 | 23/34 | 56→62 (53) | 0.083 | 0.017 | 0.182 | 0.127 (13) | 0.312 / 0.528 |
| PP IPCW G=730 | applicable34 | 34 | 0.292 | 0.255 | 0.213 | 0.234 | 24/34 | 62→76 (65) | 0.006 | 0.155 | 0.058 | 0.028 (13) | 0.005 / 0.691 |
| switch-only IPCW | applicable34 | 34 | 0.276 | 0.247 | 0.208 | 0.227 | 22/34 | 62→68 (65) | 0.006 | 0.163 | 0.091 | 0.025 (13) | 0.072 / 0.718 |
| PP naive G=365 | applicable34 | 34 | 0.328 | 0.289 | 0.234 | 0.260 | 23/34 | 53→62 (53) | 0.009 | 0.134 | 0.185 | 0.034 (13) | 0.285 / 0.824 |
| PP naive G=180 | applicable34 | 34 | 0.387 | 0.332 | 0.283 | 0.336 | 23/34 | 56→59 (47) | 0.082 | 0.018 | 0.225 | 0.139 (13) | 0.299 / 0.518 |
| PP naive G=730 | applicable34 | 34 | 0.291 | 0.254 | 0.211 | 0.235 | 24/34 | 62→71 (59) | 0.005 | 0.126 | 0.052 | 0.023 (13) | 0.004 / 0.729 |
| switch-only naive | applicable34 | 34 | 0.275 | 0.246 | 0.208 | 0.226 | 22/34 | 59→68 (62) | 0.006 | 0.169 | 0.082 | 0.026 (13) | 0.078 / 0.704 |
| 90-d run-in landmark | applicable34 | 26 | 0.254 | 0.430 | 0.271 | 0.285 | 18/26 | 77→92 (88) | 0.060 | 0.433 | 0.567 | 0.021 (13) | 0.824 / 0.656 |
| 90-d landmark, no repeat-order rule (dev. 1) | applicable34 | 34 | 0.240 | 0.248 | 0.209 | 0.232 | 21/34 | 68→68 (74) | 0.040 | 0.206 | 0.449 | 0.008 (13) | 0.448 / 0.545 |

## Landmark retention (% of analysed matched patients kept at day 90; applicable trials)

| estimand | PS | arm | trials | aggregate % | median % | min % | max % |
|---|---|---|---|---|---|---|---|
| landmark90 | P1 | ECG | 34 | 86.0 | 87.2 | 56.8 | 95.7 |
| landmark90 | P1 | base | 34 | 86.2 | 86.6 | 59.0 | 97.3 |
| landmark90 | P1 | shufECG | 34 | 86.2 | 86.8 | 59.6 | 96.1 |
| landmark90 | P5 | ECG | 34 | 86.0 | 86.7 | 57.4 | 95.1 |
| landmark90 | P5 | base | 34 | 86.2 | 86.6 | 57.5 | 95.7 |
| landmark90 | P5 | shufECG | 34 | 86.1 | 86.6 | 56.3 | 96.7 |
| landmark90 | none | unmatched | 34 | 91.9 | 92.7 | 73.6 | 95.8 |
| runin90 | P1 | ECG | 34 | 10.2 | 8.9 | 1.4 | 24.6 |
| runin90 | P1 | base | 34 | 10.3 | 9.3 | 2.3 | 24.6 |
| runin90 | P1 | shufECG | 34 | 10.3 | 9.0 | 1.7 | 24.1 |
| runin90 | P5 | ECG | 34 | 10.3 | 8.9 | 2.0 | 25.3 |
| runin90 | P5 | base | 34 | 10.3 | 9.1 | 1.6 | 25.8 |
| runin90 | P5 | shufECG | 34 | 10.4 | 8.5 | 1.6 | 25.5 |
| runin90 | none | unmatched | 34 | 32.3 | 30.2 | 13.3 | 52.5 |

## Per-trial (P1; HR base → +ECG, RCT HR; — = not applicable / not estimable)

| trial | design | RCT | ITT | PP IPCW 365 | switch IPCW | run-in 90 | retained % (base) | deviating % G365 (base) |
|---|---|---|---|---|---|---|---|---|
| comet | parallel drug | 1.21 | 1.20→1.25 | 1.55→1.63 | 1.37→1.41 | 1.04→1.08 | 18 | 82 |
| paradigm-hf-seq | sequential switch | 0.80 | 1.16→0.99 | 1.16→0.99 | 1.19→1.01 | 0.91→0.95 | 11 | 47 |
| transform-hf | parallel drug | 1.02 | 0.92→1.23 | 0.84→1.09 | 0.83→1.09 | 1.80→2.00 | 17 | 11 |
| elite-ii | parallel drug | 1.13 | 0.86→1.01 | 0.82→0.98 | 0.83→0.96 | 1.06→1.07 | 14 | 66 |
| life | parallel drug | 0.87 | 0.68→0.81 | 0.54→0.64 | 0.65→0.76 | 1.63→0.95 | 9 | 81 |
| plato | parallel drug | 0.84 | 0.80→0.82 | 0.74→0.76 | 0.74→0.76 | 0.46→0.54 | 17 | 17 |
| aristotle | parallel drug | 0.79 | 0.55→0.65 | 0.52→0.61 | 0.54→0.65 | 0.80→1.16 | 21 | 67 |
| rocket-af | parallel drug | 0.88 | 0.51→0.51 | 0.48→0.47 | 0.49→0.51 | 0.51→0.76 | 19 | 68 |
| rely | parallel drug | 0.66 | 0.77→0.73 | 0.71→0.69 | 0.73→0.70 | 0.71→0.99 | 16 | 71 |
| allhat | parallel drug | 0.98 | 1.31→1.22 | 1.41→1.45 | 1.47→1.32 | 1.67→1.39 | 6 | 87 |
| emperor-preserved-v2 | parallel drug | 0.79 | 0.76→0.81 | 0.70→0.77 | 0.75→0.80 | — | 4 | 50 |
| east-afnet4 | sequential add-on | 0.79 | 1.07→0.94 | 1.16→0.99 | 1.09→0.95 | 0.92→0.81 | 17 | 56 |
| cabana-v2 | NA: procedure arm | 0.86 | 0.25→0.32 | — | — | — | — | — |
| ontarget | parallel drug | 1.01 | 0.81→0.84 | 0.68→0.73 | 0.78→0.80 | 0.71→0.79 | 7 | 76 |
| value | parallel drug | 1.04 | 0.74→0.76 | 0.72→0.73 | 0.72→0.74 | 0.74→0.94 | 7 | 81 |
| ascot | parallel drug | 0.90 | 0.80→0.89 | 0.69→0.82 | 0.74→0.82 | 0.71→0.75 | 10 | 86 |
| empa-reg | parallel drug | 0.86 | 0.77→0.66 | 0.76→0.65 | 0.78→0.66 | 1.68→1.52 | 4 | 76 |
| carolina | parallel drug | 0.98 | 0.99→0.91 | 1.09→1.06 | 1.03→0.97 | — | 2 | 84 |
| leader | parallel drug | 0.87 | 0.57→0.54 | 0.69→0.47 | 0.51→0.47 | — | 5 | 85 |
| sustain6 | parallel drug | 0.74 | 0.49→0.54 | 0.47→0.51 | 0.49→0.54 | 0.51→0.25 | 4 | 65 |
| rewind | parallel drug | 0.88 | 0.86→0.82 | 0.81→0.79 | 0.81→0.78 | 1.15→0.64 | 4 | 78 |
| declare | parallel drug | 0.83 | 1.81→1.36 | 1.83→1.40 | 1.81→1.37 | 1.83→1.98 | 2 | 64 |
| canvas | parallel drug | 0.86 | 0.82→0.95 | 0.63→0.75 | 0.77→0.90 | — | 2 | 89 |
| tecos | parallel drug | 0.98 | 0.88→0.88 | 0.82→0.80 | 0.89→0.89 | 0.39→0.51 | 4 | 76 |
| carmelina | parallel drug | 1.02 | 1.01→0.98 | 1.18→1.10 | 1.01→0.99 | — | 4 | 70 |
| valiant | parallel drug | 1.00 | 0.84→0.80 | 0.70→0.74 | 0.85→0.84 | 0.34→1.25 | 16 | 80 |
| insight | parallel drug | 1.10 | 1.74→1.49 | 1.88→1.74 | 1.91→1.68 | — | 7 | 80 |
| affirm | sequential add-on | 1.15 | 1.35→1.11 | 1.80→1.45 | 1.44→1.20 | 0.93→0.62 | 21 | 69 |
| af-chf | sequential add-on | 1.06 | 1.42→1.26 | 1.92→1.54 | 1.64→1.43 | 0.70→0.89 | 24 | 60 |
| precision | parallel drug | 0.93 | 0.70→0.73 | 0.71→0.69 | 0.67→0.70 | 0.10→0.95 | 2 | 85 |
| amplify | parallel drug | 0.84 | 0.67→0.72 | 0.66→0.70 | 0.66→0.70 | 0.26→0.59 | 25 | 5 |
| lodestar | parallel drug | 1.06 | 1.09→0.91 | 1.19→0.99 | 1.11→0.91 | 0.79→1.11 | 5 | 77 |
| prove-it | parallel drug | 0.84 | 1.17→1.07 | 1.30→1.10 | 1.26→1.11 | 1.26→0.83 | 11 | 70 |
| frail-af | sequential switch | 1.69 | 0.96→1.08 | 1.06→1.03 | 1.06→1.03 | 2.27→1.43 | 17 | 11 |
| laaos3 | NA: procedure arm | 0.67 | 0.94→0.77 | — | — | — | — | — |
| protect-af | NA: procedure arm | 0.62 | 0.55→0.72 | — | — | — | — | — |
| raft-af | NA: procedure arm | 0.71 | 0.57→0.60 | — | — | — | — | — |
| active-w | parallel drug | 1.44 | 1.47→1.57 | 1.33→1.44 | 1.38→1.49 | 1.48→1.02 | 15 | 61 |

## Verdict (plain language)

- **Emulations are further from the RCTs under on-treatment estimands.** On the same 34 trials, the P1 base
  |Δlog HR| is 0.23 (ITT), 0.27 (switch-only), 0.32 (G = 365) and 0.36 (G = 180). Most benchmark RCTs report ITT,
  and order-based discontinuation is noisy.
- **The ECG result is qualitatively the same as under ITT.** Adding ECG32 to P1 shrinks |Δ| under every
  on-treatment estimand: G = 365 IPCW 0.315 → 0.251, 25/34 closer, p = 0.002; vs permuted ECG p = 0.0004;
  cluster p = 0.003. ITT on the same 34 trials: 0.232 → 0.188, 22/34, p = 0.008. With P5 the gain persists
  (p 0.005–0.08) but does not beat permuted ECG (p 0.13–0.18, except G = 180), as in ITT.
- **The one change is borderline and not robust.** With P1, the within-set benchmark shuffle reaches p = 0.023–0.054
  for G = 180 / 365 (ITT on the same trials 0.20). So part of the on-treatment gain looks trial-specific, not generic
  shrinkage. By the plan's rule this counts as a "change" in 3 of 20 estimand × PS shuffle cells. But:
  - the G = 730 (0.094–0.098) and switch-only (0.12) estimands, which are closer to ITT, do not show it;
  - P5 does not show it (0.18–0.23);
  - none survives correction for the 20 shuffle tests (Bonferroni threshold 0.0025; min p 0.023).
  Read it as a hint to report, not a finding.
- **Run-in is uninformative.** The registered run-in keeps about 10% of patients. Its apparent large gain (P1
  0.488 → 0.287, p = 0.015) is noise in tiny samples: vs permuted ECG p = 0.054, shuffle p = 0.72, halves p = 0.87 /
  0.34. The plain 90-day landmark gives ITT-like results with a weaker ECG effect (P1 p = 0.34; P5 p = 0.040,
  shuffle p = 0.45).
- **Bottom line:** the conclusions do not change. ECG added to a thin PS moves emulated HRs toward the RCTs, and
  the movement is largely generic shrinkage, under ITT and under every on-treatment and run-in estimand. At most
  there is a weak, P1-only, multiplicity-fragile hint of trial-specific agreement with short-grace per-protocol
  censoring.
