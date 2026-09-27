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
