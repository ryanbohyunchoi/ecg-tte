# v2.0 echo-subset analysis: real-data bias removal by the ECG (plan; committed before any result)

Exploratory. Code: `scripts/v20/echo_subset.py`. Outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-echo-subset/` (umask 077; aggregates only; counts 1–10 suppressed). Results: `docs/v20/ECHO_SUBSET.md`.

## Question
This is the real-data counterpart of the plasmode (docs/v19/G2_SIMULATION.md, docs/v20/G2_EXTENSION.md). Among patients with a measured physiological confounder, how much of the change in the emulated log HR produced by adjusting for that measured physiology is reproduced by adjusting for the ECG embedding instead?

## Subsets (per trial, before matching)
- **E (echo):** usable outcome (`T.y_ok`) and a valid pre-index echo LVEF (`T.H["pp_LVFUNC__ef"]`, 5–90%). This is the value used in the 58-variable held-out panel; echo is masked for index dates before 2016-07-31.
- **N (NT-proBNP):** usable outcome and a valid NT-proBNP (`pp_BNP__ntprobnp`, 5–100,000 pg/mL, log scale).
- **Eligibility:** a trial × subset combination is analysed only if the smaller arm has ≥ 300 patients and the subset has ≥ 50 primary-outcome events.

## Physiology sets (fixed now)
- **Single (primary):** for E, echo LVEF; for N, log NT-proBNP. Each is fully observed within its subset.
- **Extended (secondary):** {echo LVEF, log NT-proBNP, BMI (`obs_bmi`, 12–80), eGFR (`pp_LAB__egfr`, 1–200)}. Values missing within the subset are median-imputed and get a missingness indicator. Cleaning is the same as G2 (`g2_simulation.clean_c`).

## Base PS and arms (full engine: L2 logistic C = 1 on standardized covariates, 1:1 greedy caliper 0.2 SD of the logit, pair-clustered Cox; `v16_engine.run_cell`)
- **Base PS:**
  - P1 demographics (primary);
  - P5 (demographics + 5 dx);
  - hdPS200 (demographics + sparse dx + top-200 hdPS levels, re-ranked within the subset);
  - clinical minus physiology: `T.core` without the analogue of the physiology set. That is lvef for single-E; nothing for single-N, since NT-proBNP is not in the clinical PS; and lvef, bmi and creatinine for the extended set.
- **Arms per base:**
  - base;
  - base + ECG32 (`T.ecg_pc`);
  - base + permuted ECG32 (`T.ecg_pc[T.shuffle_perm]`);
  - base + noise32 (`T.noise32`);
  - base + phys (single);
  - base + phys (extended).
  - All arms are fitted on the same subset rows.

## Estimand and pooling
- **Per trial i:**
  - num_i = logHR_base − logHR_base+ECG;
  - den_i = logHR_base − logHR_base+phys;
  - these are the same for each placebo, with the ECG replaced by the placebo.
- **Primary pooled estimate:** F = Σ num_i·den_i / Σ den_i², the least-squares slope through the origin, i.e. the share of the physiology-driven shift that the ECG reproduces. It handles shifts of either sign and down-weights trials in which physiology moves the estimate little.
- **Co-primary:** placebo-corrected F − F_permutedECG. This is needed because num and den share the base-arm estimate, so matching noise alone makes F positive.
- **Secondary:**
  - the aligned ratio of sums Σ num_i·sign(den_i) / Σ|den_i|;
  - the correlation of num and den;
  - mean |den| and |num|;
  - |SMD| of the physiology variable after matching in each arm;
  - mean |logHR − RCT log HR| per arm (descriptive).
- **CI:** percentile 95% from 2,000 bootstrap resamples of trials (paired within trial for differences).
- **Trial sets:** primary is the 32 trials of the paper (quality tier not "Limited", `docs/v19/quality_tiers.json`); the 38 emulated trials are a sensitivity analysis. If fewer than 10 trials are eligible in a set, results are descriptive only.

## Plasmode comparison
For the single physiology variable, compute in each subset the 5-fold cross-fitted ridge partial R² of the standardized confounder on the ECG32 given the base covariates, as in G2 `cv_r2`. The prediction is 100·F ≈ 100 × partial R². It is summarized as the den²-weighted mean partial R², matching the slope weights.

## Gates and exclusions
- **Reproduction gate:** the full-cohort P1 base log HR must equal `claude-v17-confirm/results_all.csv` / `claude-v18-af-confirm/results_af5.csv` (|Δ| ≤ 1e-9) in all 38 trials before any subset result is used.
- **Excluded:** trial × subset combinations failing eligibility, and cells whose Cox fit fails (logged).
- **Deviations** are logged in ECHO_SUBSET.md.

## Caveats (stated in advance)
- The physiology shift is not the true bias. It is only what adjustment for measured physiology changes, and confounding that remains unmeasured is unknown.
- The subset estimand is conditional on having the measurement, e.g. patients referred for echo.
- Measured LVEF may also be affected by later care. It is pre-index, but its timing relative to prescribing differs between patients.
