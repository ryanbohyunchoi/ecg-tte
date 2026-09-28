# v1.9 plan: analyses modelled on German et al. (Nat Genet 2025), fixed before results (2026-09-28)

These analyses are exploratory. Every cell is reported. Tests are two-sided unless stated otherwise.

## G1: ECG imbalance as an orthogonal diagnostic across design steps (their Fig 2)
**Design steps** (per trial, where buildable):
- **S0:** crude contrast, i.e. drug initiators vs comparator initiators without trial eligibility gates (and, if feasible, initiators vs non-initiators);
- **S1:** trial cohort (eligibility + active comparator + new user);
- **S2:** sparse-PS matched;
- **S3:** hdPS200 matched;
- **S4:** clinical-PS matched.

**Diagnostics**, none of which is in any PS:
- SMDs of AI-ECG-derived phenotypes (`T.ph` scores);
- the cross-fitted C-statistic of the ECG embedding for treatment.

For comparison, the same diagnostics are computed on echo LVEF and NT-proBNP where measured.

**Questions**
- Does ECG imbalance shrink with design quality?
- Across trials × steps, does residual ECG imbalance correlate with |Δlog HR| vs RCT? (Spearman, with the trial as a cluster.)
- Does it agree with residual echo/lab imbalance?

## G2: simulation, i.e. how much confounding the ECG embedding removes
This is plasmode-style (the valid 80%-subsampling version) with a known true HR.
- The outcome is simulated to depend on treatment and on one held-out physiological confounder C: echo LVEF, NT-proBNP, BMI or eGFR. Confounding strength is set on a grid.
- C is excluded from every PS. Arms are base P1, +ECG, +shufECG, +noise, and base + C itself (oracle).
- **Estimand:** % of the bias removed, as a function of the ECG's cross-fitted R² for C (measured in real data).

**Question:** does ECG remove bias in proportion to how well it predicts the confounder? (Their result: an imperfect proxy removes only part.)

## G3: AI-ECG prognostic and predictive enrichment for trial design (their Fig 5)
**AI-ECG risk score.** Cross-fitted (5-fold, by patient), from ECG embedding PCs alone, predicting the trial primary outcome at the horizon. It is fitted in the pooled trial cohort with no treatment term.

**Prognostic analysis**
- Report the HR per SD of the score in the emulated trial-eligible matched population vs in all initiators in the health system.
- Report the sample-size reduction from enrolling the top 25% of the score (Schoenfeld events-based, using the RCT HR).

**Predictive analysis**
- Treatment × score interaction on the matched sample (Cox, pair-clustered). Report per trial and meta-analysed with random effects.

**Comparison.** Repeat with a clinical risk score (the demographics + dx prognostic score) and with CLMBR, to show whether the ECG adds enrichment value.
