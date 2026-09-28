# S10: demographics + HTN, T2D, CAD, AF, obesity and HF, with vs without ECG (post hoc, PI request, 2026-09-27)

**Design**
- **PS covariates:** age, sex, index year, hypertension, T2D (E11), CAD/IHD (I20–I25), AF (I48), obesity, and HF.
  - HF is `hf_any_365`: I50, I11.0, I13.0, I13.2 in 365 d.
  - In LIFE, ALLHAT, ONTARGET, VALUE and ASCOT, `hf_any_365` was dropped for prevalence below 1%, so Elixhauser CHF is used there.
- **Arms:** +ECG32 vs base, with shufECG and noise32 placebos.
- **Matching:** 1:1, caliper 0.2 and caliper 0.1.
- **Scope:** 18 trials; halves full/A/B, as in S1.
- **Held-out balance:** the 58-variable panel. It is also reported without BMI, because obesity is in the PS.

Code: `scripts/v16/s10_demo6.py` and `s10_summarize.py`. Aggregates are in `claude-v16-s10-demo6/`.

## Results (caliper 0.2, 58-panel, full cohort unless stated)

| Metric | Base | +ECG | Trials better | p | vs shufECG | vs noise | Cluster p | LOO max | Half A | Half B | BH q |
|---|---|---|---|---|---|---|---|---|---|---|---|
| % held-out \|SMD\| < 0.1 | 60.4% | 64.0% | 14/18 | 0.017 | 0.023 | 0.006 | 0.016 | 0.033 | 0.035 | 0.001 | 0.031 |
| Love count < 0.1 (of 58) | 42 | 47 | — | descriptive | | | | | | | |
| Mean \|SMD\| | 0.114 | 0.103 | 14/18 | 0.006 | 0.009 | <0.001 | 0.022 | 0.011 | 0.032 | 0.001 | 0.027 |
| Balance C-statistic | 0.679 | 0.664 | 16/18 | 0.001 | 0.002 | <0.001 | 0.006 | 0.002 | 0.008 | 0.014 | 0.011 |
| % \|SMD\| > 0.2 | 15.2% | 12.8% | 9/18 | 0.088 | | | | | 0.12 | 0.001 | 0.10 |
| \|Δlog HR\| vs RCT | 0.233 | 0.201 | 13/18 | 0.012 | **0.96** | **0.70** | 0.008 | 0.025 | 0.17 | 0.78 | 0.027 |
| z² | 6.55 | 5.24 | 13/18 | 0.029 | 0.14 | 0.34 | 0.027 | 0.057 | 0.010 | 0.15 | 0.042 |

**Notes**
- **Benchmark shuffle.** For \|Δ\| the shuffled-benchmark null mean is −0.014 (p = 0.002, trial-specific); for z² it is −1.21 (p = 0.42, generic).
- **Without BMI.** Results are essentially unchanged: % < 0.1 is 60.5 → 63.8, p = 0.029.
- **Caliper 0.1.** It gives the same pattern: % < 0.1 is 59.8 → 63.7, p = 0.014, both halves; the love count is 41 → 49.
- **Retention.** ECG matched slightly fewer patients: 89.1% → 88.2% of the smaller arm at caliper 0.2.

## Reading
- **Balance.** With this 6-diagnosis PS, ECG significantly increases the share of held-out covariates below 0.1 (+3.6 pp; love plot 42 → 47). It is robust to placebos, clustering and leave-one-out, and significant in both halves. The gain is smaller than with demographics alone (+6.4 pp) and larger than with the full sparse PS (+0.7 pp, null).
- **RCT agreement.** \|Δlog HR\| falls from 0.233 to 0.201. This is significant, benchmark-specific, and survives clustering and leave-one-out. However, **shuffled ECG gives the same improvement** (d_shufECG −0.030; ECG vs shufECG p = 0.96), and the gain is not significant in either half. It is therefore not attributable to ECG information. Adding 32 extra PS dimensions of any kind changes the matched sets in a way that happens to help. It must not be reported as an ECG effect.

## Per-trial balance and emulation (caliper 0.2, full cohort)

**Emulation quality** comes from the blinded RCT-DUPLICATE-style rating (`docs/v14/closeness_rating.json`), which was made without viewing results:
- **Flags:** in-hospital start, responder run-in, baseline-therapy switch, and delayed effect.
- **Comparator and outcome:** each rated for how faithfully the emulation reproduces the trial's.

**Balance** is the % of the 58 held-out covariates with |SMD| < 0.1.

**Consistent** means |z| < 1.96 vs the RCT, using both SEs.

| Trial | Close emulation | Design flags | Comparator | Outcome | Balance −ECG → +ECG | RCT HR (95% CI) | HR −ECG | HR +ECG | \|Δlog HR\| −ECG → +ECG | Consistent −/+ |
|---|---|---|---|---|---|---|---|---|---|---|
| EAST-AFNET 4 | no | 1 | moderate | moderate | 75.9 → 87.9 | 0.79 (0.67–0.94) | 0.96 | 0.87 | 0.19 → 0.10 | N → Y |
| VALUE | no | 1 | moderate | moderate | 65.5 → 75.9 | 1.04 (0.94–1.15) | 0.74 | 0.77 | 0.35 → 0.31 | N → N |
| PARADIGM-HF | no | 1 | moderate | moderate | 65.5 → 74.1 | 0.80 (0.73–0.87) | 0.99 | 0.95 | 0.22 → 0.17 | N → N |
| TRANSFORM-HF | no | 2 | good | good | 39.7 → 48.3 | 1.02 (0.89–1.17) | 0.89 | 0.91 | 0.13 → 0.12 | Y → Y |
| ROCKET-AF | yes | 0 | good | good | 50.0 → 56.9 | 0.88 (0.75–1.04) | 0.58 | 0.54 | 0.41 → 0.48 | N → N |
| CAROLINA | yes | 0 | good | moderate | 43.1 → 50.0 | 0.98 (0.84–1.14) | 0.89 | 0.92 | 0.09 → 0.06 | Y → Y |
| ELITE II | yes | 0 | moderate | good | 67.2 → 74.1 | 1.13 (0.95–1.34) | 0.90 | 0.95 | 0.23 → 0.18 | Y → Y |
| LIFE | no | 2 | moderate | moderate | 51.7 → 56.9 | 0.87 (0.77–0.98) | 0.78 | 0.88 | 0.10 → 0.01 | Y → Y |
| PLATO | no | 1 | good | moderate | 79.3 → 84.5 | 0.84 (0.77–0.92) | 0.84 | 0.85 | 0.00 → 0.01 | Y → Y |
| ASCOT-BPLA | no | 1 | moderate | moderate | 70.7 → 74.1 | 0.90 (0.79–1.02) | 0.79 | 0.78 | 0.13 → 0.14 | Y → Y |
| ALLHAT | no | 1 | moderate | moderate | 87.9 → 89.7 | 0.98 (0.90–1.07) | 1.20 | 1.23 | 0.20 → 0.23 | N → N |
| ONTARGET | no | 2 | moderate | moderate | 70.7 → 72.4 | 1.01 (0.94–1.09) | 0.84 | 0.85 | 0.19 → 0.17 | N → N |
| CABANA | no | 0 | moderate | moderate | 50.0 → 51.7 | 0.86 (0.65–1.14) | 0.34 | 0.37 | 0.94 → 0.84 | N → N |
| EMPA-REG OUTCOME | no | 0 | moderate | moderate | 46.6 → 48.3 | 0.86 (0.74–0.99) | 0.66 | 0.72 | 0.26 → 0.17 | N → Y |
| RE-LY | yes | 0 | moderate | good | 42.1 → 42.1 | 0.66 (0.53–0.82) | 0.97 | 0.98 | 0.38 → 0.39 | Y → Y |
| COMET | no | 1 | poor | good | 55.2 → 55.2 | 1.21 (1.07–1.35) | 1.18 | 1.21 | 0.02 → 0.00 | Y → Y |
| EMPEROR-Preserved | no | 0 | moderate | moderate | 62.1 → 56.9 | 0.79 (0.69–0.90) | 0.72 | 0.73 | 0.09 → 0.07 | Y → Y |
| ARISTOTLE | yes | 0 | good | good | 63.8 → 53.4 | 0.79 (0.66–0.95) | 0.62 | 0.67 | 0.24 → 0.16 | Y → Y |

**Summary**
- **Closer to the RCT with ECG:** 13 of 18 trials.
- **Consistency with the RCT:** 11/18 without ECG → 13/18 with ECG. EAST-AFNET 4 and EMPA-REG become consistent; none is lost.
- **Balance gain by emulation quality:** mean +2.1 pp in the 5 "close" emulations and +4.2 pp in the 13 not close.
- **Balance gain vs gain in |Δ|:** not correlated across trials (Spearman ρ = 0.12, p = 0.63).
- **Reminder (placebo):** the |Δ| improvement is reproduced by shuffled ECG (ECG vs shufECG p = 0.96), so the per-trial movement toward the RCT is not attributable to ECG information.


## Round-4 audit corrections (2026-09-28; docs/v18/AUDIT_ROUND4.md §7)
- Per-trial table summary: consistency with the RCT is **10/18 → 12/18**, not 11 → 13.
- The p-values in this file are two-sided unless stated otherwise.
