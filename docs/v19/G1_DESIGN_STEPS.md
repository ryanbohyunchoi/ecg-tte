# G1: ECG imbalance as an orthogonal diagnostic across design steps (v1.9, exploratory)

Plan: `docs/v18/V19_GERMAN_STYLE_PLAN.md` section G1 (analogue of German et al. 2025, Fig 2). Code: `scripts/v19/g1_design_steps.py`.
Outputs (aggregates only): `audits/claude-v19-g1-design-steps/` (`steps.csv`, `step_tests.csv`, `correlations.csv`, `tables.md`, `log.json`).
Figure: `docs/v19/G1_design_steps.png`. All analyses are exploratory, and every cell is reported (full tables in the appendix).

## Verdict (plain language)

- **ECG imbalance shrinks with design quality.** This mirrors German et al.'s PGS result.
  - Mean |SMD| of the 5 AI-ECG phenotype scores goes 0.206 (S0, ungated initiators) → 0.144 (S1, trial cohort; same data source) → 0.088 (S2 sparse PS) → 0.079 (S3 hdPS200) → 0.075 (S4 clinical PS). The S1 → S4 means are over 38 trials.
  - The ECG-embedding C-statistic for treatment goes 0.629 → 0.591 → 0.558 → 0.541 → 0.550.
  - The largest drops are gating (S0 → S1) and the first PS (S1 → S2):
    - S0 → S1: phenotypes 27/37 trials, p = 0.0001; C-statistic 30/37, p < 0.0001.
    - S1 → S2: 38/38 trials for both.
  - Beyond S2 the gains are small:
    - S2 → S3: C-statistic 30/38, p = 0.0001; phenotypes not significant.
    - S3 → S4: phenotypes not significant, and the C-statistic gets *worse* (16/38 improve, p = 0.015). The clinical PS leaves more ECG signal than hdPS200.
  - The per-trial monotone trend over S1 → S4 is clear for phenotypes (36/38) and the C-statistic (34/38), both p < 0.0001.
  - The shuffled-ECG placebo C-statistic is 0.50 at every step, and no step contrast is significant for it.
- **Residual ECG imbalance does NOT track RCT disagreement.** Across 38 trials × matched steps S2–S4 (114 points), the Spearman correlation of residual ECG imbalance with |Δlog HR| vs the RCT is about 0:
  - phenotype mean ρ = −0.03, p = 0.85;
  - ECG C-statistic ρ = −0.03, p = 0.81;
  - p values are from a trial-block permutation.
  - Within-trial correlations are also null.
  - Held-out echo LVEF and NT-proBNP imbalance do not track |Δlog HR| either (ρ ≈ 0). So none of these balance diagnostics predicts closeness to the RCT.
  - Only at S1 (unmatched) does the ECG C-statistic correlate with |Δlog HR| (ρ = 0.38, p = 0.019). That reflects crude confounding and is not residual imbalance.
- **Agreement with echo/lab imbalance is partial.**
  - LVEF: within a trial, the steps with more ECG-phenotype imbalance also have more held-out LVEF imbalance (ρ_within = 0.38, p = 0.0005, S2–S4). Across trials the correlation is weak (ρ = 0.10, p = 0.36 over S2–S4; restricted to S2–S3, where LVEF is truly held out, ρ = 0.27, p = 0.055). At S1 it is 0.47 (p = 0.004).
  - NT-proBNP: essentially no agreement with ECG imbalance at any step.
  - Caveat: LVEF is a clinical-PS covariate (T.core `lvef`), so at S4 it is not held out. Its sharp S3 → S4 fall (0.149 → 0.069) is by construction.
- **Bottom line (German-style).** The ECG behaves as an orthogonal balance diagnostic: design steps visibly remove ECG-measured physiology imbalance, and a placebo ECG shows nothing. However, the size of the residual ECG imbalance after matching carries no information about how far an emulation lands from its RCT.

## Design

| step | definition | trials |
|---|---|---|
| S0 | drug vs comparator initiators **without trial eligibility gates**. `build_trial_cohort.py` stages s1–s4 are unchanged (first use in window, 365-d comparator washout, age ≥ 18 + 365-d prior activity, dedupe; switch_seq: same candidate records and sequential sampling). Removed: the disease gate (s5 := s4), all other gates (require_all, first_dx_within, ecg_text, pci, procedure_1d, require_drugs) and every declared exclusion; trial min/max age replaced by ≥ 18. Then ECG selection (latest ECG in [index − 365, index]), BCL embeddings, phenotype heads re-trained excluding the S0 roster, physiology panel v2. | 37 (all except COMET, whose cohort comes from a different roster pipeline) |
| S1 | trial cohort = v16 engine analysis set (`T.keys`), unmatched | 38 |
| S2 | sparse PS (`T.X_dx`: demographics + dx flags), L2 C = 1, 1:1 greedy caliper 0.2 SD of the logit | 38 |
| S3 | hdPS200 (`T.X_dx` + top-200 hdPS levels) | 38 |
| S4 | clinical PS (`T.X_core`) | 38 |

**Diagnostics.** None of these is in any PS, except LVEF at S4 (see the caveat above).
- **Phenotypes.** |SMD| of the 5 AI-ECG phenotype scores `T.ph`: `ph_lvef_le_40_logit`, `ph_afib_logit`, `ph_male_logit`, `ph_lvef_pred`, `ph_age_pred`.
  - `ph_mean` is the mean over the 5 and is the primary diagnostic.
  - `ph3_mean` is the mean over the 3 non-demographic scores (LVEF ≤ 40, AF, LVEF). Sex and age are themselves in every PS.
- **ECG C-statistic.** `ecg_c`: 5-fold cross-fitted L2 (C = 1) logistic AUC of treatment from the 32 ECG PCs, within the (matched) sample (`v16_engine.balance_cstat`).
- **Placebo.** `shuf_c`: the same C-statistic after permuting the PCs across patients.
- **Echo/lab comparators.** Held-out echo LVEF (`pp_LVFUNC__ef`) and NT-proBNP (`pp_BNP__ntprobnp`), raw as in the engine plus log NT-proBNP.
  - Echo is masked for index < 2016-07-31.
  - An SMD is reported only if ≥ 20 patients per arm have a measurement.
- **SMD denominator.** The pooled SD of the step's unmatched rows (S0: S0 rows; S1–S4: S1 rows), exactly as `v16_engine.smd_components`.
- **Emulation.** |Δlog HR| = |log HR − RCT log HR|, using the engine Cox model (pair-clustered SE for matched steps).

**Tests.**
- Step contrasts: two-sided sign-flip across trials (`v13_summarize.sign_flip`: exact for ≤ 20 trials, otherwise 20,000 Monte Carlo draws, seed 0; "p = 0.0000" means < 1/20,000).
- Monotone trend: per-trial Spearman of the metric vs step index S1..S4, then a sign-flip of the per-trial values.
- Correlations: Spearman over trial × step points, with a cluster-robust permutation that permutes the y blocks between trials of equal block size (20,000 draws). "Within" = ranks centred within trial, with within-trial permutation.

## Audits

- **Engine reproduction.** S1–S4 log HR and matched-pair counts reproduce `claude-v18-embed-compare/results.csv` exactly (rungs none/sparse/hdPS200/clinical, arm base, full half; checked for ARISTOTLE, EMPA-REG and LEADER). The engine's 58-panel `smd:pp_LVFUNC__ef` / `smd:pp_BNP__ntprobnp` agree to < 1e-14.
- **S0 cohort build.** The gate-free build reproduces the original attrition counts at stages s1–s4 exactly (e.g. EMPA-REG 16,951 / 14,919; ARISTOTLE 38,910 / 13,962).
- **S0 embeddings.**
  - To save GPU time, ECGs already embedded (same checkpoint and settings) in a registry trial's BCL run were copied rather than re-embedded (`bcl/reuse.json`). The rest were embedded on idle GPUs (0, 3–7).
  - The 4 focus trials were fully re-embedded. For S1 patients with the same record, their embeddings are identical to the engine's (max |Δ| = 0.0).
  - Trials with newly embedded ECGs show max |Δ| ≤ 0.001 (GPU nondeterminism).
  - S0-trained vs S1-trained phenotype heads: correlation ≥ 0.99 for every score in every trial. Echo LVEF agrees 100%.
- **Nesting.**
  - For 30 trials, ≥ 99% of S1 records (same patient, arm and index date) are in S0. The remaining 1% comes from dropping the trial minimum age, which changes the earliest-index dedupe.
  - The 7 switch_seq trials re-sample comparators sequentially from the ungated pool, so S1 is **not** nested in S0: only 21–33% of S1 records reappear (PARADIGM-HF-seq, EAST-AFNET 4, AFFIRM, AF-CHF, FRAIL-AF, PROTECT AF, RAFT-AF).
  - The "S1 (S0 data)" row uses only those shared records. A nested-only test (30 trials) is reported.
- **Shared S0 cohorts.** Trials with the same drug contrast share one S0 cohort:
  - EAST-AFNET 4 = AFFIRM = AF-CHF;
  - EMPA-REG = EMPEROR-Preserved;
  - ELITE II = VALIANT.
  - A test averaging within shared S0 cohorts (33 units) is reported.
- **Placebo.** The shuffled-ECG C-statistic averages 0.497–0.502 at every step, and no step contrast is significant (all p ≥ 0.17).

## Results

### Step means (mean over trials; medians in `step_means.csv`)

| data | step | trials | ph_mean | ph3_mean | ecg_c | shuf_c | LVEF | log NT-proBNP | NT-proBNP | abs Δ log HR |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 build | S0 | 37 | 0.206 | 0.239 | 0.629 | 0.502 | 0.263 | 0.186 | 0.172 | – |
| S0 build | S1 | 37 | 0.144 | 0.171 | 0.591 | 0.502 | 0.167 | 0.228 | 0.227 | – |
| engine | S1 | 38 | 0.148 | 0.175 | 0.597 | 0.501 | 0.181 | 0.207 | 0.199 | 0.261 |
| engine | S2 | 38 | 0.088 | 0.111 | 0.558 | 0.501 | 0.134 | 0.103 | 0.077 | 0.188 |
| engine | S3 | 38 | 0.079 | 0.099 | 0.541 | 0.497 | 0.149 | 0.105 | 0.079 | 0.181 |
| engine | S4 | 38 | 0.075 | 0.092 | 0.550 | 0.500 | 0.069* | 0.071 | 0.066 | 0.159 |

\* LVEF is in the clinical PS.

Per phenotype, the scores ordered by S1 imbalance are LVEF ≤ 40 > LVEF > age > AF > sex. Each falls from S0 to S4:
- LVEF ≤ 40: 0.268 → 0.207 → 0.134 → 0.116 → 0.105;
- AF: 0.199 → 0.131 → 0.077 → 0.070 → 0.074.

At S4, 29/38 trials have ph_mean < 0.1, and 15/38 still have an ECG C-statistic > 0.55.

### Focus trials

| trial | step | n | pairs | ph_mean | ecg_c | shuf_c | LVEF | log NT-proBNP | abs Δ log HR |
|---|---|---|---|---|---|---|---|---|---|
| EMPA-REG | S0 | 14,954 | – | 0.263 | 0.631 | 0.512 | 0.720 | 0.117 | – |
| | S1 | 5,649 | – | 0.138 | 0.573 | 0.510 | 0.563 | 0.144 | 0.069 |
| | S2 | 3,272 | 1,636 | 0.029 | 0.534 | 0.511 | 0.349 | 0.065 | 0.069 |
| | S3 | 3,042 | 1,521 | 0.026 | 0.520 | 0.488 | 0.190 | 0.074 | 0.037 |
| | S4 | 2,980 | 1,490 | 0.023 | 0.512 | 0.497 | 0.087* | 0.019 | 0.087 |
| ARISTOTLE | S0 | 35,430 | – | 0.107 | 0.575 | 0.499 | 0.110 | 0.460 | – |
| | S1 | 18,771 | – | 0.129 | 0.595 | 0.506 | 0.123 | 0.661 | 0.332 |
| | S2 | 5,604 | 2,802 | 0.080 | 0.558 | 0.498 | 0.049 | 0.089 | 0.053 |
| | S3 | 4,638 | 2,319 | 0.054 | 0.523 | 0.505 | 0.066 | 0.124 | 0.101 |
| | S4 | 5,598 | 2,799 | 0.086 | 0.545 | 0.511 | 0.009* | 0.025 | 0.147 |
| EAST-AFNET 4 | S0 | 27,854 | – | 0.398 | 0.703 | 0.510 | 0.301 | 0.271 | – |
| | S1 | 16,109 | – | 0.176 | 0.628 | 0.505 | 0.232 | 0.139 | 0.254 |
| | S2 | 6,924 | 3,462 | 0.115 | 0.599 | 0.492 | 0.132 | 0.101 | 0.201 |
| | S3 | 6,446 | 3,223 | 0.109 | 0.579 | 0.502 | 0.158 | 0.073 | 0.266 |
| | S4 | 6,924 | 3,462 | 0.085 | 0.588 | 0.506 | 0.021* | 0.061 | 0.173 |
| PARADIGM-HF (seq) | S0 | 7,959 | – | 0.887 | 0.891 | 0.503 | 2.210 | 0.320 | – |
| | S1 | 5,129 | – | 0.392 | 0.722 | 0.505 | 0.307 | 0.157 | 0.408 |
| | S2 | 2,444 | 1,222 | 0.318 | 0.679 | 0.491 | 0.229 | 0.093 | 0.244 |
| | S3 | 2,268 | 1,134 | 0.185 | 0.598 | 0.503 | 0.220 | 0.105 | 0.191 |
| | S4 | 2,366 | 1,183 | 0.259 | 0.653 | 0.492 | 0.040* | 0.025 | 0.206 |

Notes on the focus trials:
- **PARADIGM-HF.** In S0 (sacubitril/valsartan vs ACEi without the HFrEF gates), ECG phenotypes and echo LVEF are grossly imbalanced (LVEF |SMD| 2.2). The trial gates remove most of this. Even after the best PS, the ECG C-statistic stays at 0.60–0.68, which is the clearest case of residual ECG-visible physiology.
- **EMPA-REG and EAST-AFNET 4** follow the German pattern: a large drop at gating and at the first PS, then a plateau.
- **ARISTOTLE.** Gating does not reduce ECG imbalance (S0 0.107 vs S1 0.129), and log NT-proBNP imbalance *rises* with gating (0.46 → 0.66). The S1 SMD denominator is smaller within the gated AF population, so the same absolute difference counts for more.

### (ii) Monotone decline: paired sign-flip across trials

Sign convention: a − b > 0 means lower imbalance at b. The full list, including ph3_mean and raw NT-proBNP, is in the appendix.

| contrast | ph_mean | ecg_c | shuf_c (placebo) | LVEF | log NT-proBNP | abs Δ log HR |
|---|---|---|---|---|---|---|
| S0 → S1 (37 trials, S0 data) | +0.061, 27/37, p = 0.0001 | +0.038, 30/37, p < 0.0001 | +0.000, p = 0.94 | +0.096, 21/37, p = 0.029 | −0.042, 15/37, p = 0.027 | – |
| S0 → S1 (33 shared-S0 units) | +0.054, 24/33, p = 0.0006 | +0.036, 26/33, p = 0.0001 | −0.001, p = 0.88 | +0.095, p = 0.062 | −0.041, p = 0.029 | – |
| S0 → S1 (30 nested trials) | +0.042, 21/30, p = 0.0008 | +0.029, 24/30, p = 0.0001 | – | +0.047, p = 0.063 | −0.047, p = 0.021 | – |
| S1 → S2 | +0.061, 38/38, p < 0.0001 | +0.039, 38/38, p < 0.0001 | −0.000, p = 0.97 | +0.047, 28/38, p = 0.004 | +0.104, 31/38, p = 0.0001 | +0.073, 27/38, p = 0.008 |
| S2 → S3 | +0.008, 24/38, p = 0.15 | +0.017, 30/38, p = 0.0001 | +0.004, p = 0.27 | −0.014, 13/38, p = 0.43 | −0.002, p = 0.87 | +0.007, 14/38, p = 0.84 |
| S3 → S4 | +0.004, 24/38, p = 0.25 | −0.008, 16/38, p = 0.015 | −0.003, p = 0.37 | +0.080*, 29/38, p = 0.0001 | +0.034, p = 0.092 | +0.022, 24/38, p = 0.34 |
| S1 → S4 | +0.074, 37/38, p < 0.0001 | +0.048, 36/38, p < 0.0001 | +0.001, p = 0.86 | +0.112*, p = 0.0001 | +0.135, p < 0.0001 | +0.102, 27/38, p = 0.001 |
| trend S1..S4 (−Spearman) | 0.69, 36/38, p < 0.0001 | 0.64, 34/38, p < 0.0001 | – | 0.39, 29/38, p = 0.0002 | 0.44, 30/38, p = 0.0001 | – |

Gating reduces ECG imbalance but *raises* the NT-proBNP SMD in most trials (15/37 decline). This is partly the denominator effect described under ARISTOTLE: the SMD is scaled by the SD within the step's sample.

### (iii) Residual imbalance vs RCT disagreement and vs echo/lab imbalance

Spearman over trial × step points. p is the trial-block permutation p; "within" = within-trial ranks.

| x | y | steps | ρ | p | ρ within | p within |
|---|---|---|---|---|---|---|
| ph_mean | abs Δ log HR | S2–S4 (114 points) | −0.025 | 0.85 | 0.053 | 0.63 |
| ph3_mean | abs Δ log HR | S2–S4 | 0.003 | 0.98 | 0.139 | 0.21 |
| ecg_c | abs Δ log HR | S2–S4 | −0.033 | 0.81 | −0.097 | 0.52 |
| shuf_c (placebo) | abs Δ log HR | S2–S4 | −0.003 | 0.98 | −0.076 | 0.55 |
| LVEF | abs Δ log HR | S2–S4 | −0.028 | 0.79 | 0.057 | 0.58 |
| log NT-proBNP | abs Δ log HR | S2–S4 | 0.021 | 0.85 | 0.004 | 0.98 |
| ph_mean | LVEF | S2–S4 | 0.100 | 0.36 | 0.382 | 0.0005 |
| ph_mean | LVEF | S2–S3 (LVEF held out) | 0.268 | 0.055 | 0.287 | 0.16 |
| ph3_mean | LVEF | S2–S4 | 0.098 | 0.37 | 0.304 | 0.004 |
| ecg_c | LVEF | S2–S4 | 0.023 | 0.83 | 0.096 | 0.36 |
| ph_mean | log NT-proBNP | S2–S4 | 0.068 | 0.57 | 0.058 | 0.66 |
| ecg_c | log NT-proBNP | S2–S4 | 0.015 | 0.90 | 0.016 | 0.91 |
| ecg_c | NT-proBNP (raw) | S2–S4 | −0.313 | 0.008 | −0.083 | 0.49 |
| ecg_c | abs Δ log HR | S1 only (38 trials) | 0.376 | 0.019 | – | – |
| ph_mean | LVEF | S1 only | 0.467 | 0.004 | – | – |

Notes:
- The raw NT-proBNP correlation is negative and would not survive multiplicity correction; the log-scale version is null.
- Per-step correlations (S1, S2, S3, S4 separately) are in the appendix. The only other nominal hits are ph_mean vs LVEF at S3 (ρ = 0.36, p = 0.025) and ecg_c vs LVEF at S4 (ρ = −0.37, p = 0.025, where LVEF is a PS covariate).
- No multiplicity correction is applied; about 40 correlation cells are reported.

## Deviations and limitations (logged)

1. **S0 age.** Trial-specific age limits were dropped (age ≥ 18 kept). S0 is defined per drug contrast, so trials sharing a contrast share one S0 (see the audits).
2. **Initiators vs non-initiators** (the plan's "if feasible" part of S0) was not done. No non-initiator roster or index-date rule exists in the pipeline.
3. **S0 embeddings were reused rather than re-embedded.** Determinism was verified: |Δ| = 0 for the same ECG in the same run configuration, ≤ 0.001 across runs.
4. **S0 phenotype heads were re-trained excluding the S0 roster** (`train_ecg_phenotype_heads.py`, the pipeline's leakage rule). The S0 vs S1 comparison therefore uses the "S0 data" rows for both steps (same heads, PCs of the S0 embeddings, S1 = shared records). The engine rows use the original heads and PCs.
5. **S0 is not restricted by other data sources.** It requires only an ECG embedding. The engine S1 additionally intersects with CLMBR, panel and covariate availability (the S0-data S1 row equals the engine S1 for nested trials).
6. **LVEF is not held out at S4** (it is in `T.core`). NT-proBNP is held out at every step.
7. **Choices not fixed in the plan:**
   - log NT-proBNP added next to raw;
   - ECG C-statistic L2 with C = 1 (the engine held-out C-statistic uses C = 0.01 over many components);
   - an SMD is suppressed when < 20 patients per arm are measured.
8. **COMET has no S0** (its roster is built by a different pipeline).
9. **|Δlog HR| is a noisy target.** Previous rounds found RCT agreement to be dominated by benchmark noise and shrinkage (AUDIT_ROUND4). A null correlation is therefore weak evidence of "no relation", and a positive correlation would have needed the benchmark-shuffle check.

## Appendix: full tables (`audits/claude-v19-g1-design-steps/tables.md`)

## step means (mean over trials)

| variant | step | n_trials | ph_mean | ph3_mean | ecg_c | shuf_c | smd_lvef | smd_logbnp | smd_bnp | absd |
|---|---|---|---|---|---|---|---|---|---|---|
| engine | S1 | 38 | 0.148 | 0.175 | 0.597 | 0.501 | 0.181 | 0.207 | 0.199 | 0.261 |
| engine | S2 | 38 | 0.088 | 0.111 | 0.558 | 0.501 | 0.134 | 0.103 | 0.077 | 0.188 |
| engine | S3 | 38 | 0.079 | 0.099 | 0.541 | 0.497 | 0.149 | 0.105 | 0.079 | 0.181 |
| engine | S4 | 38 | 0.075 | 0.092 | 0.550 | 0.500 | 0.069 | 0.071 | 0.066 | 0.159 |
| s0data | S0 | 37 | 0.206 | 0.239 | 0.629 | 0.502 | 0.263 | 0.186 | 0.172 | – |
| s0data | S1 | 37 | 0.144 | 0.171 | 0.591 | 0.502 | 0.167 | 0.228 | 0.227 | – |

## per-phenotype |SMD| means

| variant | step | smd:ph_lvef_le_40_logit | smd:ph_afib_logit | smd:ph_male_logit | smd:ph_lvef_pred | smd:ph_age_pred |
|---|---|---|---|---|---|---|
| engine | S1 | 0.207 | 0.131 | 0.082 | 0.187 | 0.135 |
| engine | S2 | 0.134 | 0.077 | 0.047 | 0.123 | 0.056 |
| engine | S3 | 0.116 | 0.070 | 0.042 | 0.112 | 0.056 |
| engine | S4 | 0.105 | 0.074 | 0.043 | 0.098 | 0.053 |
| s0data | S0 | 0.268 | 0.199 | 0.111 | 0.250 | 0.199 |
| s0data | S1 | 0.205 | 0.123 | 0.078 | 0.185 | 0.130 |

## step tests (two-sided sign-flip, v13_summarize.sign_flip; > 0 = lower imbalance at b)

| set | metric | a | b | n_trials | mean_a_minus_b | k_decline | p_signflip |
|---|---|---|---|---|---|---|---|
| 38 trials (engine) | ph_mean | S1 | S2 | 38 | 0.0608 | 38/38 | 0.0000 |
| 38 trials (engine) | ph_mean | S2 | S3 | 38 | 0.0083 | 24/38 | 0.1532 |
| 38 trials (engine) | ph_mean | S3 | S4 | 38 | 0.0045 | 24/38 | 0.2479 |
| 38 trials (engine) | ph_mean | S1 | S3 | 38 | 0.0691 | 36/38 | 0.0000 |
| 38 trials (engine) | ph_mean | S1 | S4 | 38 | 0.0736 | 37/38 | 0.0000 |
| 38 trials (engine) | ph_mean | S2 | S4 | 38 | 0.0128 | 26/38 | 0.0010 |
| 38 trials (engine) | ph3_mean | S1 | S2 | 38 | 0.0633 | 35/38 | 0.0000 |
| 38 trials (engine) | ph3_mean | S2 | S3 | 38 | 0.0122 | 23/38 | 0.1321 |
| 38 trials (engine) | ph3_mean | S3 | S4 | 38 | 0.0069 | 22/38 | 0.2513 |
| 38 trials (engine) | ph3_mean | S1 | S3 | 38 | 0.0755 | 34/38 | 0.0000 |
| 38 trials (engine) | ph3_mean | S1 | S4 | 38 | 0.0824 | 38/38 | 0.0000 |
| 38 trials (engine) | ph3_mean | S2 | S4 | 38 | 0.0191 | 26/38 | 0.0008 |
| 38 trials (engine) | ecg_c | S1 | S2 | 38 | 0.0389 | 38/38 | 0.0000 |
| 38 trials (engine) | ecg_c | S2 | S3 | 38 | 0.0170 | 30/38 | 0.0001 |
| 38 trials (engine) | ecg_c | S3 | S4 | 38 | -0.0083 | 16/38 | 0.0145 |
| 38 trials (engine) | ecg_c | S1 | S3 | 38 | 0.0559 | 35/38 | 0.0000 |
| 38 trials (engine) | ecg_c | S1 | S4 | 38 | 0.0476 | 36/38 | 0.0000 |
| 38 trials (engine) | ecg_c | S2 | S4 | 38 | 0.0086 | 25/38 | 0.0195 |
| 38 trials (engine) | shuf_c | S1 | S2 | 38 | -0.0001 | 22/38 | 0.9735 |
| 38 trials (engine) | shuf_c | S2 | S3 | 38 | 0.0040 | 21/38 | 0.2735 |
| 38 trials (engine) | shuf_c | S3 | S4 | 38 | -0.0033 | 14/38 | 0.3665 |
| 38 trials (engine) | shuf_c | S1 | S3 | 38 | 0.0039 | 23/38 | 0.1774 |
| 38 trials (engine) | shuf_c | S1 | S4 | 38 | 0.0005 | 21/38 | 0.8569 |
| 38 trials (engine) | shuf_c | S2 | S4 | 38 | 0.0006 | 17/38 | 0.8517 |
| 38 trials (engine) | smd_lvef | S1 | S2 | 38 | 0.0470 | 28/38 | 0.0036 |
| 38 trials (engine) | smd_lvef | S2 | S3 | 38 | -0.0144 | 13/38 | 0.4290 |
| 38 trials (engine) | smd_lvef | S3 | S4 | 38 | 0.0797 | 29/38 | 0.0001 |
| 38 trials (engine) | smd_lvef | S1 | S3 | 38 | 0.0326 | 24/38 | 0.0866 |
| 38 trials (engine) | smd_lvef | S1 | S4 | 38 | 0.1124 | 31/38 | 0.0001 |
| 38 trials (engine) | smd_lvef | S2 | S4 | 38 | 0.0653 | 27/38 | 0.0034 |
| 38 trials (engine) | smd_logbnp | S1 | S2 | 38 | 0.1039 | 31/38 | 0.0001 |
| 38 trials (engine) | smd_logbnp | S2 | S3 | 38 | -0.0025 | 17/38 | 0.8740 |
| 38 trials (engine) | smd_logbnp | S3 | S4 | 38 | 0.0338 | 25/38 | 0.0917 |
| 38 trials (engine) | smd_logbnp | S1 | S3 | 38 | 0.1014 | 27/38 | 0.0009 |
| 38 trials (engine) | smd_logbnp | S1 | S4 | 38 | 0.1352 | 30/38 | 0.0000 |
| 38 trials (engine) | smd_logbnp | S2 | S4 | 38 | 0.0313 | 28/38 | 0.0077 |
| 38 trials (engine) | smd_bnp | S1 | S2 | 38 | 0.1223 | 32/38 | 0.0000 |
| 38 trials (engine) | smd_bnp | S2 | S3 | 38 | -0.0020 | 19/38 | 0.8719 |
| 38 trials (engine) | smd_bnp | S3 | S4 | 38 | 0.0124 | 20/38 | 0.4350 |
| 38 trials (engine) | smd_bnp | S1 | S3 | 38 | 0.1203 | 31/38 | 0.0000 |
| 38 trials (engine) | smd_bnp | S1 | S4 | 38 | 0.1327 | 31/38 | 0.0000 |
| 38 trials (engine) | smd_bnp | S2 | S4 | 38 | 0.0104 | 25/38 | 0.3819 |
| 38 trials (engine) | absd | S1 | S2 | 38 | 0.0732 | 27/38 | 0.0077 |
| 38 trials (engine) | absd | S2 | S3 | 38 | 0.0068 | 14/38 | 0.8368 |
| 38 trials (engine) | absd | S3 | S4 | 38 | 0.0221 | 24/38 | 0.3419 |
| 38 trials (engine) | absd | S1 | S3 | 38 | 0.0800 | 21/38 | 0.0811 |
| 38 trials (engine) | absd | S1 | S4 | 38 | 0.1021 | 27/38 | 0.0011 |
| 38 trials (engine) | absd | S2 | S4 | 38 | 0.0289 | 26/38 | 0.0268 |
| S0 trials (S0 data) | ph_mean | S0 | S1 | 37 | 0.0614 | 27/37 | 0.0001 |
| S0 trials (S0 data) | ph3_mean | S0 | S1 | 37 | 0.0679 | 23/37 | 0.0030 |
| S0 trials (S0 data) | ecg_c | S0 | S1 | 37 | 0.0379 | 30/37 | 0.0000 |
| S0 trials (S0 data) | shuf_c | S0 | S1 | 37 | 0.0002 | 13/37 | 0.9431 |
| S0 trials (S0 data) | smd_lvef | S0 | S1 | 37 | 0.0961 | 21/37 | 0.0289 |
| S0 trials (S0 data) | smd_logbnp | S0 | S1 | 37 | -0.0416 | 15/37 | 0.0267 |
| S0 trials (S0 data) | smd_bnp | S0 | S1 | 37 | -0.0553 | 10/37 | 0.0018 |
| S0 cohorts (shared S0 averaged) | ph_mean | S0 | S1 | 33 | 0.0538 | 24/33 | 0.0006 |
| S0 cohorts (shared S0 averaged) | ph3_mean | S0 | S1 | 33 | 0.0538 | 20/33 | 0.0181 |
| S0 cohorts (shared S0 averaged) | ecg_c | S0 | S1 | 33 | 0.0358 | 26/33 | 0.0001 |
| S0 cohorts (shared S0 averaged) | shuf_c | S0 | S1 | 33 | -0.0005 | 12/33 | 0.8804 |
| S0 cohorts (shared S0 averaged) | smd_lvef | S0 | S1 | 33 | 0.0947 | 18/33 | 0.0621 |
| S0 cohorts (shared S0 averaged) | smd_logbnp | S0 | S1 | 33 | -0.0413 | 13/33 | 0.0286 |
| S0 cohorts (shared S0 averaged) | smd_bnp | S0 | S1 | 33 | -0.0528 | 9/33 | 0.0058 |
| S0 trials, S1 nested in S0 (>=99%) | ph_mean | S0 | S1 | 30 | 0.0419 | 21/30 | 0.0008 |
| S0 trials, S1 nested in S0 (>=99%) | ecg_c | S0 | S1 | 30 | 0.0293 | 24/30 | 0.0001 |
| S0 trials, S1 nested in S0 (>=99%) | smd_lvef | S0 | S1 | 30 | 0.0472 | 16/30 | 0.0625 |
| S0 trials, S1 nested in S0 (>=99%) | smd_logbnp | S0 | S1 | 30 | -0.0469 | 11/30 | 0.0214 |
| 38 trials (engine) | ph_mean | trend | S1..S4 (-Spearman) | 38 | 0.6895 | 36/38 | 0.0000 |
| 38 trials (engine) | ecg_c | trend | S1..S4 (-Spearman) | 38 | 0.6421 | 34/38 | 0.0000 |
| 38 trials (engine) | smd_lvef | trend | S1..S4 (-Spearman) | 38 | 0.3947 | 29/38 | 0.0002 |
| 38 trials (engine) | smd_logbnp | trend | S1..S4 (-Spearman) | 38 | 0.4368 | 30/38 | 0.0001 |

## correlations (Spearman; p = cluster (trial-block) permutation)

| x | y | rho | p | n_pts | n_trials | rho_within | p_within | step |
|---|---|---|---|---|---|---|---|---|
| ph_mean | absd | -0.025 | 0.853 | 114 | 38 | 0.053 | 0.634 | S2-S4 |
| ph_mean | smd_lvef | 0.100 | 0.362 | 114 | 38 | 0.382 | 0.001 | S2-S4 |
| ph_mean | smd_logbnp | 0.068 | 0.567 | 114 | 38 | 0.058 | 0.659 | S2-S4 |
| ph_mean | smd_bnp | -0.199 | 0.094 | 114 | 38 | 0.131 | 0.282 | S2-S4 |
| ph3_mean | absd | 0.003 | 0.981 | 114 | 38 | 0.139 | 0.214 | S2-S4 |
| ph3_mean | smd_lvef | 0.098 | 0.370 | 114 | 38 | 0.304 | 0.003 | S2-S4 |
| ph3_mean | smd_logbnp | 0.013 | 0.913 | 114 | 38 | -0.015 | 0.906 | S2-S4 |
| ph3_mean | smd_bnp | -0.197 | 0.097 | 114 | 38 | 0.216 | 0.072 | S2-S4 |
| ecg_c | absd | -0.033 | 0.808 | 114 | 38 | -0.097 | 0.524 | S2-S4 |
| ecg_c | smd_lvef | 0.023 | 0.832 | 114 | 38 | 0.096 | 0.360 | S2-S4 |
| ecg_c | smd_logbnp | 0.015 | 0.901 | 114 | 38 | 0.016 | 0.912 | S2-S4 |
| ecg_c | smd_bnp | -0.313 | 0.008 | 114 | 38 | -0.083 | 0.485 | S2-S4 |
| smd_lvef | absd | -0.028 | 0.789 | 114 | 38 | 0.057 | 0.576 | S2-S4 |
| smd_logbnp | absd | 0.021 | 0.847 | 114 | 38 | 0.004 | 0.976 | S2-S4 |
| shuf_c | absd | -0.003 | 0.979 | 114 | 38 | -0.076 | 0.547 | S2-S4 |
| ph_mean | smd_lvef | 0.268 | 0.055 | 76 | 38 | 0.287 | 0.162 | S2-S3 |
| ph_mean | absd | -0.010 | 0.943 | 76 | 38 | -0.019 | 0.918 | S2-S3 |
| ecg_c | smd_lvef | 0.195 | 0.176 | 76 | 38 | 0.142 | 0.463 | S2-S3 |
| ecg_c | absd | -0.037 | 0.789 | 76 | 38 | -0.047 | 0.858 | S2-S3 |
| ph_mean | absd | 0.199 | 0.229 | 38 | 38 | – | – | S1 |
| ecg_c | absd | 0.376 | 0.019 | 38 | 38 | – | – | S1 |
| ph_mean | smd_lvef | 0.467 | 0.004 | 38 | 38 | – | – | S1 |
| ph_mean | smd_logbnp | 0.017 | 0.918 | 38 | 38 | – | – | S1 |
| ecg_c | smd_lvef | 0.349 | 0.033 | 38 | 38 | – | – | S1 |
| ecg_c | smd_logbnp | 0.020 | 0.904 | 38 | 38 | – | – | S1 |
| ph_mean | absd | -0.120 | 0.465 | 38 | 38 | – | – | S2 |
| ecg_c | absd | 0.007 | 0.967 | 38 | 38 | – | – | S2 |
| ph_mean | smd_lvef | 0.203 | 0.218 | 38 | 38 | – | – | S2 |
| ph_mean | smd_logbnp | 0.048 | 0.770 | 38 | 38 | – | – | S2 |
| ecg_c | smd_lvef | 0.174 | 0.300 | 38 | 38 | – | – | S2 |
| ecg_c | smd_logbnp | -0.007 | 0.966 | 38 | 38 | – | – | S2 |
| ph_mean | absd | 0.096 | 0.569 | 38 | 38 | – | – | S3 |
| ecg_c | absd | -0.084 | 0.618 | 38 | 38 | – | – | S3 |
| ph_mean | smd_lvef | 0.364 | 0.025 | 38 | 38 | – | – | S3 |
| ph_mean | smd_logbnp | 0.077 | 0.648 | 38 | 38 | – | – | S3 |
| ecg_c | smd_lvef | 0.257 | 0.118 | 38 | 38 | – | – | S3 |
| ecg_c | smd_logbnp | 0.151 | 0.364 | 38 | 38 | – | – | S3 |
| ph_mean | absd | -0.131 | 0.435 | 38 | 38 | – | – | S4 |
| ecg_c | absd | -0.043 | 0.799 | 38 | 38 | – | – | S4 |
| ph_mean | smd_lvef | -0.304 | 0.062 | 38 | 38 | – | – | S4 |
| ph_mean | smd_logbnp | -0.029 | 0.864 | 38 | 38 | – | – | S4 |
| ecg_c | smd_lvef | -0.365 | 0.025 | 38 | 38 | – | – | S4 |
| ecg_c | smd_logbnp | -0.148 | 0.377 | 38 | 38 | – | – | S4 |

## trials with S0: every step

| trial | variant | step | n | n_t | n_c | ph_mean | ph3_mean | ecg_c | shuf_c | smd_lvef | smd_logbnp | absd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| active-w | engine | S1 | 3139.000 | 1076.000 | 2063.000 | 0.163 | 0.233 | 0.627 | 0.506 | 0.034 | 0.544 | 0.073 |
| active-w | engine | S2 | 1646.000 | 823.000 | 823.000 | 0.144 | 0.220 | 0.587 | 0.502 | 0.083 | 0.086 | 0.060 |
| active-w | engine | S3 | 1204.000 | 602.000 | 602.000 | 0.150 | 0.202 | 0.614 | 0.492 | 0.184 | 0.138 | 0.102 |
| active-w | engine | S4 | 1562.000 | 781.000 | 781.000 | 0.129 | 0.197 | 0.603 | 0.474 | 0.010 | 0.092 | 0.056 |
| active-w | s0data | S0 | 22566.000 | 14602.000 | 7964.000 | 0.182 | 0.255 | 0.659 | 0.500 | 0.063 | 0.302 | – |
| active-w | s0data | S1 | 3134.000 | 1075.000 | 2059.000 | 0.164 | 0.235 | 0.628 | 0.499 | 0.038 | 0.544 | – |
| af-chf | engine | S1 | 5558.000 | 1272.000 | 4286.000 | 0.271 | 0.325 | 0.664 | 0.494 | 0.242 | 0.187 | 0.210 |
| af-chf | engine | S2 | 2538.000 | 1269.000 | 1269.000 | 0.153 | 0.203 | 0.612 | 0.497 | 0.211 | 0.120 | 0.163 |
| af-chf | engine | S3 | 2230.000 | 1115.000 | 1115.000 | 0.130 | 0.193 | 0.592 | 0.519 | 0.236 | 0.129 | 0.285 |
| af-chf | engine | S4 | 2526.000 | 1263.000 | 1263.000 | 0.127 | 0.168 | 0.594 | 0.521 | 0.054 | 0.078 | 0.133 |
| af-chf | s0data | S0 | 27854.000 | 7333.000 | 20521.000 | 0.398 | 0.529 | 0.703 | 0.510 | 0.301 | 0.271 | – |
| af-chf | s0data | S1 | 1349.000 | 1063.000 | 286.000 | 0.322 | 0.373 | 0.654 | 0.512 | 0.228 | 0.238 | – |
| affirm | engine | S1 | 17634.000 | 4100.000 | 13534.000 | 0.176 | 0.183 | 0.652 | 0.499 | 0.219 | 0.148 | 0.043 |
| affirm | engine | S2 | 8200.000 | 4100.000 | 4100.000 | 0.116 | 0.116 | 0.637 | 0.489 | 0.145 | 0.059 | 0.036 |
| affirm | engine | S3 | 7488.000 | 3744.000 | 3744.000 | 0.089 | 0.092 | 0.597 | 0.496 | 0.137 | 0.068 | 0.007 |
| affirm | engine | S4 | 8176.000 | 4088.000 | 4088.000 | 0.095 | 0.081 | 0.610 | 0.510 | 0.010 | 0.031 | 0.061 |
| affirm | s0data | S0 | 27854.000 | 7333.000 | 20521.000 | 0.398 | 0.529 | 0.703 | 0.510 | 0.301 | 0.271 | – |
| affirm | s0data | S1 | 4600.000 | 3532.000 | 1068.000 | 0.168 | 0.179 | 0.644 | 0.497 | 0.189 | 0.162 | – |
| allhat | engine | S1 | 26592.000 | 18098.000 | 8494.000 | 0.053 | 0.055 | 0.567 | 0.496 | 0.003 | 0.076 | 0.294 |
| allhat | engine | S2 | 16988.000 | 8494.000 | 8494.000 | 0.026 | 0.026 | 0.565 | 0.500 | 0.004 | 0.076 | 0.169 |
| allhat | engine | S3 | 16980.000 | 8490.000 | 8490.000 | 0.020 | 0.018 | 0.547 | 0.501 | 0.014 | 0.087 | 0.205 |
| allhat | engine | S4 | 16984.000 | 8492.000 | 8492.000 | 0.017 | 0.017 | 0.546 | 0.498 | 0.014 | 0.089 | 0.193 |
| allhat | s0data | S0 | 44459.000 | 30350.000 | 14109.000 | 0.094 | 0.094 | 0.574 | 0.501 | 0.047 | 0.094 | – |
| allhat | s0data | S1 | 26460.000 | 18014.000 | 8446.000 | 0.053 | 0.054 | 0.568 | 0.491 | 0.000 | 0.068 | – |
| amplify | engine | S1 | 5080.000 | 4068.000 | 1012.000 | 0.080 | 0.114 | 0.547 | 0.514 | 0.127 | 0.332 | 0.060 |
| amplify | engine | S2 | 1462.000 | 731.000 | 731.000 | 0.038 | 0.050 | 0.532 | 0.522 | 0.105 | 0.122 | 0.168 |
| amplify | engine | S3 | 1280.000 | 640.000 | 640.000 | 0.030 | 0.030 | 0.514 | 0.494 | 0.075 | 0.034 | 0.039 |
| amplify | engine | S4 | 1454.000 | 727.000 | 727.000 | 0.026 | 0.023 | 0.500 | 0.494 | 0.105 | 0.089 | 0.122 |
| amplify | s0data | S0 | 33805.000 | 27481.000 | 6324.000 | 0.110 | 0.135 | 0.585 | 0.501 | 0.110 | 0.394 | – |
| amplify | s0data | S1 | 5080.000 | 4068.000 | 1012.000 | 0.080 | 0.115 | 0.547 | 0.519 | 0.127 | 0.332 | – |
| aristotle | engine | S1 | 18771.000 | 15419.000 | 3352.000 | 0.129 | 0.167 | 0.595 | 0.506 | 0.123 | 0.661 | 0.332 |
| aristotle | engine | S2 | 5604.000 | 2802.000 | 2802.000 | 0.080 | 0.088 | 0.558 | 0.498 | 0.049 | 0.089 | 0.053 |
| aristotle | engine | S3 | 4638.000 | 2319.000 | 2319.000 | 0.054 | 0.055 | 0.523 | 0.505 | 0.066 | 0.124 | 0.101 |
| aristotle | engine | S4 | 5598.000 | 2799.000 | 2799.000 | 0.086 | 0.091 | 0.545 | 0.511 | 0.009 | 0.025 | 0.147 |
| aristotle | s0data | S0 | 35430.000 | 27360.000 | 8070.000 | 0.107 | 0.139 | 0.575 | 0.499 | 0.110 | 0.460 | – |
| aristotle | s0data | S1 | 18771.000 | 15419.000 | 3352.000 | 0.131 | 0.168 | 0.595 | 0.503 | 0.123 | 0.661 | – |
| ascot | engine | S1 | 26021.000 | 13238.000 | 12783.000 | 0.187 | 0.239 | 0.625 | 0.511 | 0.167 | 0.001 | 0.130 |
| ascot | engine | S2 | 22364.000 | 11182.000 | 11182.000 | 0.130 | 0.185 | 0.605 | 0.508 | 0.127 | 0.016 | 0.191 |
| ascot | engine | S3 | 21332.000 | 10666.000 | 10666.000 | 0.134 | 0.190 | 0.601 | 0.504 | 0.149 | 0.024 | 0.243 |
| ascot | engine | S4 | 20460.000 | 10230.000 | 10230.000 | 0.124 | 0.176 | 0.599 | 0.507 | 0.004 | 0.025 | 0.129 |
| ascot | s0data | S0 | 60732.000 | 24442.000 | 36290.000 | 0.206 | 0.308 | 0.650 | 0.501 | 0.428 | 0.168 | – |
| ascot | s0data | S1 | 25977.000 | 13220.000 | 12757.000 | 0.186 | 0.236 | 0.625 | 0.502 | 0.167 | 0.001 | – |
| cabana-v2 | engine | S1 | 13133.000 | 1573.000 | 11560.000 | 0.347 | 0.398 | 0.708 | 0.513 | 0.185 | 0.442 | 1.439 |
| cabana-v2 | engine | S2 | 3146.000 | 1573.000 | 1573.000 | 0.143 | 0.168 | 0.625 | 0.506 | 0.033 | 0.125 | 0.914 |
| cabana-v2 | engine | S3 | 3146.000 | 1573.000 | 1573.000 | 0.080 | 0.077 | 0.578 | 0.519 | 0.085 | 0.079 | 0.114 |
| cabana-v2 | engine | S4 | 3122.000 | 1561.000 | 1561.000 | 0.089 | 0.109 | 0.585 | 0.495 | 0.031 | 0.084 | 0.526 |
| cabana-v2 | s0data | S0 | 15516.000 | 1640.000 | 13876.000 | 0.344 | 0.405 | 0.707 | 0.505 | 0.223 | 0.438 | – |
| cabana-v2 | s0data | S1 | 13133.000 | 1573.000 | 11560.000 | 0.350 | 0.401 | 0.708 | 0.507 | 0.185 | 0.442 | – |
| canvas | engine | S1 | 6037.000 | 485.000 | 5552.000 | 0.115 | 0.077 | 0.590 | 0.510 | 0.270 | 0.276 | 0.080 |
| canvas | engine | S2 | 970.000 | 485.000 | 485.000 | 0.048 | 0.026 | 0.542 | 0.503 | 0.399 | 0.235 | 0.046 |
| canvas | engine | S3 | 956.000 | 478.000 | 478.000 | 0.055 | 0.075 | 0.522 | 0.489 | 0.111 | 0.260 | 0.261 |
| canvas | engine | S4 | 964.000 | 482.000 | 482.000 | 0.037 | 0.027 | 0.543 | 0.514 | 0.254 | 0.092 | 0.052 |
| canvas | s0data | S0 | 7838.000 | 603.000 | 7235.000 | 0.131 | 0.104 | 0.600 | 0.534 | 0.200 | 0.412 | – |
| canvas | s0data | S1 | 6036.000 | 485.000 | 5551.000 | 0.115 | 0.076 | 0.588 | 0.496 | 0.270 | 0.276 | – |
| carmelina | engine | S1 | 1546.000 | 803.000 | 743.000 | 0.050 | 0.026 | 0.507 | 0.493 | 0.028 | 0.142 | 0.013 |
| carmelina | engine | S2 | 1138.000 | 569.000 | 569.000 | 0.011 | 0.009 | 0.485 | 0.516 | 0.104 | 0.017 | 0.014 |
| carmelina | engine | S3 | 966.000 | 483.000 | 483.000 | 0.031 | 0.032 | 0.459 | 0.443 | 0.081 | 0.142 | 0.133 |
| carmelina | engine | S4 | 1108.000 | 554.000 | 554.000 | 0.024 | 0.011 | 0.497 | 0.525 | 0.071 | 0.055 | 0.075 |
| carmelina | s0data | S0 | 7910.000 | 3284.000 | 4626.000 | 0.129 | 0.138 | 0.559 | 0.502 | 0.093 | 0.005 | – |
| carmelina | s0data | S1 | 1546.000 | 803.000 | 743.000 | 0.050 | 0.025 | 0.507 | 0.516 | 0.028 | 0.142 | – |
| carolina | engine | S1 | 1794.000 | 962.000 | 832.000 | 0.061 | 0.085 | 0.529 | 0.510 | 0.217 | 0.031 | 0.002 |
| carolina | engine | S2 | 1470.000 | 735.000 | 735.000 | 0.043 | 0.050 | 0.509 | 0.500 | 0.122 | 0.100 | 0.124 |
| carolina | engine | S3 | 1338.000 | 669.000 | 669.000 | 0.036 | 0.030 | 0.530 | 0.499 | 0.210 | 0.062 | 0.174 |
| carolina | engine | S4 | 1474.000 | 737.000 | 737.000 | 0.052 | 0.060 | 0.517 | 0.503 | 0.093 | 0.021 | 0.141 |
| carolina | s0data | S0 | 5994.000 | 4032.000 | 1962.000 | 0.088 | 0.118 | 0.542 | 0.496 | 0.108 | 0.054 | – |
| carolina | s0data | S1 | 1794.000 | 962.000 | 832.000 | 0.062 | 0.086 | 0.530 | 0.500 | 0.217 | 0.031 | – |
| declare | engine | S1 | 6967.000 | 2102.000 | 4865.000 | 0.289 | 0.383 | 0.637 | 0.507 | 0.667 | 0.138 | 0.809 |
| declare | engine | S2 | 2588.000 | 1294.000 | 1294.000 | 0.060 | 0.072 | 0.543 | 0.474 | 0.358 | 0.086 | 0.180 |
| declare | engine | S3 | 2380.000 | 1190.000 | 1190.000 | 0.070 | 0.097 | 0.527 | 0.480 | 0.387 | 0.173 | 0.261 |
| declare | engine | S4 | 2414.000 | 1207.000 | 1207.000 | 0.024 | 0.022 | 0.521 | 0.485 | 0.019 | 0.079 | 0.214 |
| declare | s0data | S0 | 11896.000 | 4885.000 | 7011.000 | 0.397 | 0.531 | 0.689 | 0.507 | 0.867 | 0.096 | – |
| declare | s0data | S1 | 6959.000 | 2094.000 | 4865.000 | 0.292 | 0.385 | 0.635 | 0.509 | 0.667 | 0.138 | – |
| east-afnet4 | engine | S1 | 16109.000 | 3462.000 | 12647.000 | 0.176 | 0.229 | 0.628 | 0.505 | 0.232 | 0.139 | 0.254 |
| east-afnet4 | engine | S2 | 6924.000 | 3462.000 | 3462.000 | 0.115 | 0.183 | 0.599 | 0.492 | 0.132 | 0.101 | 0.201 |
| east-afnet4 | engine | S3 | 6446.000 | 3223.000 | 3223.000 | 0.109 | 0.158 | 0.579 | 0.502 | 0.158 | 0.073 | 0.266 |
| east-afnet4 | engine | S4 | 6924.000 | 3462.000 | 3462.000 | 0.085 | 0.119 | 0.588 | 0.506 | 0.021 | 0.061 | 0.173 |
| east-afnet4 | s0data | S0 | 27854.000 | 7333.000 | 20521.000 | 0.398 | 0.529 | 0.703 | 0.510 | 0.301 | 0.271 | – |
| east-afnet4 | s0data | S1 | 4074.000 | 3035.000 | 1039.000 | 0.166 | 0.215 | 0.623 | 0.487 | 0.169 | 0.210 | – |
| elite-ii | engine | S1 | 3222.000 | 1469.000 | 1753.000 | 0.079 | 0.107 | 0.508 | 0.498 | 0.112 | 0.355 | 0.177 |
| elite-ii | engine | S2 | 2294.000 | 1147.000 | 1147.000 | 0.045 | 0.064 | 0.506 | 0.513 | 0.074 | 0.053 | 0.163 |
| elite-ii | engine | S3 | 2222.000 | 1111.000 | 1111.000 | 0.064 | 0.093 | 0.493 | 0.521 | 0.133 | 0.018 | 0.114 |
| elite-ii | engine | S4 | 2324.000 | 1162.000 | 1162.000 | 0.031 | 0.041 | 0.522 | 0.482 | 0.103 | 0.013 | 0.112 |
| elite-ii | s0data | S0 | 42157.000 | 20071.000 | 22086.000 | 0.078 | 0.076 | 0.559 | 0.501 | 0.081 | 0.135 | – |
| elite-ii | s0data | S1 | 3195.000 | 1444.000 | 1751.000 | 0.082 | 0.114 | 0.517 | 0.494 | 0.124 | 0.357 | – |
| empa-reg | engine | S1 | 5649.000 | 3159.000 | 2490.000 | 0.138 | 0.189 | 0.573 | 0.510 | 0.563 | 0.144 | 0.069 |
| empa-reg | engine | S2 | 3272.000 | 1636.000 | 1636.000 | 0.029 | 0.034 | 0.534 | 0.511 | 0.349 | 0.065 | 0.069 |
| empa-reg | engine | S3 | 3042.000 | 1521.000 | 1521.000 | 0.026 | 0.037 | 0.520 | 0.488 | 0.190 | 0.074 | 0.037 |
| empa-reg | engine | S4 | 2980.000 | 1490.000 | 1490.000 | 0.023 | 0.028 | 0.512 | 0.497 | 0.087 | 0.019 | 0.087 |
| empa-reg | s0data | S0 | 14954.000 | 8506.000 | 6448.000 | 0.263 | 0.347 | 0.631 | 0.512 | 0.720 | 0.117 | – |
| empa-reg | s0data | S1 | 5649.000 | 3159.000 | 2490.000 | 0.139 | 0.190 | 0.573 | 0.516 | 0.563 | 0.144 | – |
| emperor-preserved-v2 | engine | S1 | 2417.000 | 1477.000 | 940.000 | 0.075 | 0.062 | 0.550 | 0.501 | 0.300 | 0.335 | 0.057 |
| emperor-preserved-v2 | engine | S2 | 1056.000 | 528.000 | 528.000 | 0.071 | 0.094 | 0.509 | 0.464 | 0.168 | 0.027 | 0.049 |
| emperor-preserved-v2 | engine | S3 | 896.000 | 448.000 | 448.000 | 0.038 | 0.026 | 0.464 | 0.485 | 0.174 | 0.016 | 0.106 |
| emperor-preserved-v2 | engine | S4 | 964.000 | 482.000 | 482.000 | 0.039 | 0.031 | 0.503 | 0.504 | 0.105 | 0.013 | 0.041 |
| emperor-preserved-v2 | s0data | S0 | 14954.000 | 8506.000 | 6448.000 | 0.263 | 0.347 | 0.631 | 0.512 | 0.720 | 0.117 | – |
| emperor-preserved-v2 | s0data | S1 | 2417.000 | 1477.000 | 940.000 | 0.073 | 0.060 | 0.551 | 0.503 | 0.300 | 0.335 | – |
| frail-af | engine | S1 | 3714.000 | 797.000 | 2917.000 | 0.071 | 0.084 | 0.546 | 0.492 | 0.049 | 0.038 | 0.599 |
| frail-af | engine | S2 | 1594.000 | 797.000 | 797.000 | 0.049 | 0.055 | 0.521 | 0.505 | 0.000 | 0.008 | 0.660 |
| frail-af | engine | S3 | 1546.000 | 773.000 | 773.000 | 0.046 | 0.058 | 0.499 | 0.501 | 0.071 | 0.058 | 0.668 |
| frail-af | engine | S4 | 1594.000 | 797.000 | 797.000 | 0.058 | 0.067 | 0.507 | 0.485 | 0.033 | 0.089 | 0.747 |
| frail-af | s0data | S0 | 8609.000 | 1880.000 | 6729.000 | 0.085 | 0.090 | 0.556 | 0.498 | 0.015 | 0.054 | – |
| frail-af | s0data | S1 | 1199.000 | 560.000 | 639.000 | 0.080 | 0.091 | 0.570 | 0.518 | 0.049 | 0.301 | – |
| insight | engine | S1 | 8847.000 | 397.000 | 8450.000 | 0.046 | 0.063 | 0.551 | 0.503 | 0.110 | 0.182 | 0.595 |
| insight | engine | S2 | 794.000 | 397.000 | 397.000 | 0.032 | 0.030 | 0.506 | 0.507 | 0.045 | 0.211 | 0.426 |
| insight | engine | S3 | 770.000 | 385.000 | 385.000 | 0.057 | 0.043 | 0.529 | 0.495 | 0.306 | 0.361 | 0.139 |
| insight | engine | S4 | 788.000 | 394.000 | 394.000 | 0.039 | 0.043 | 0.545 | 0.452 | 0.243 | 0.006 | 0.222 |
| insight | s0data | S0 | 24068.000 | 2440.000 | 21628.000 | 0.211 | 0.043 | 0.688 | 0.490 | 0.066 | 0.162 | – |
| insight | s0data | S1 | 8842.000 | 394.000 | 8448.000 | 0.046 | 0.062 | 0.561 | 0.513 | 0.119 | 0.182 | – |
| laaos3 | engine | S1 | 2621.000 | 511.000 | 2110.000 | 0.174 | 0.166 | 0.655 | 0.494 | 0.014 | 0.141 | 0.165 |
| laaos3 | engine | S2 | 1022.000 | 511.000 | 511.000 | 0.157 | 0.168 | 0.563 | 0.487 | 0.024 | 0.126 | 0.061 |
| laaos3 | engine | S3 | 956.000 | 478.000 | 478.000 | 0.139 | 0.139 | 0.588 | 0.519 | 0.105 | 0.000 | 0.189 |
| laaos3 | engine | S4 | 1008.000 | 504.000 | 504.000 | 0.142 | 0.153 | 0.603 | 0.524 | 0.008 | 0.074 | 0.170 |
| laaos3 | s0data | S0 | 5333.000 | 638.000 | 4695.000 | 0.273 | 0.288 | 0.694 | 0.508 | 0.051 | 0.152 | – |
| laaos3 | s0data | S1 | 2621.000 | 511.000 | 2110.000 | 0.175 | 0.167 | 0.655 | 0.509 | 0.014 | 0.141 | – |
| leader | engine | S1 | 3782.000 | 453.000 | 3329.000 | 0.134 | 0.078 | 0.628 | 0.500 | 0.063 | 0.218 | 0.588 |
| leader | engine | S2 | 906.000 | 453.000 | 453.000 | 0.043 | 0.023 | 0.571 | 0.491 | 0.022 | 0.137 | 0.398 |
| leader | engine | S3 | 848.000 | 424.000 | 424.000 | 0.074 | 0.088 | 0.559 | 0.481 | 0.127 | 0.002 | 0.535 |
| leader | engine | S4 | 900.000 | 450.000 | 450.000 | 0.061 | 0.077 | 0.545 | 0.500 | 0.072 | 0.106 | 0.359 |
| leader | s0data | S0 | 8758.000 | 1466.000 | 7292.000 | 0.267 | 0.232 | 0.676 | 0.499 | 0.199 | 0.246 | – |
| leader | s0data | S1 | 3777.000 | 450.000 | 3327.000 | 0.130 | 0.074 | 0.623 | 0.471 | 0.064 | 0.218 | – |
| life | engine | S1 | 3131.000 | 1239.000 | 1892.000 | 0.196 | 0.280 | 0.597 | 0.500 | 0.041 | 0.128 | 0.185 |
| life | engine | S2 | 2478.000 | 1239.000 | 1239.000 | 0.105 | 0.151 | 0.575 | 0.507 | 0.003 | 0.091 | 0.016 |
| life | engine | S3 | 2462.000 | 1231.000 | 1231.000 | 0.131 | 0.191 | 0.543 | 0.508 | 0.089 | 0.049 | 0.010 |
| life | engine | S4 | 2476.000 | 1238.000 | 1238.000 | 0.118 | 0.176 | 0.553 | 0.524 | 0.107 | 0.034 | 0.014 |
| life | s0data | S0 | 54854.000 | 16782.000 | 38072.000 | 0.160 | 0.250 | 0.631 | 0.500 | 0.004 | 0.055 | – |
| life | s0data | S1 | 3101.000 | 1223.000 | 1878.000 | 0.192 | 0.271 | 0.590 | 0.503 | 0.041 | 0.107 | – |
| lodestar | engine | S1 | 22277.000 | 10954.000 | 11323.000 | 0.066 | 0.068 | 0.550 | 0.501 | 0.051 | 0.237 | 0.079 |
| lodestar | engine | S2 | 8250.000 | 4125.000 | 4125.000 | 0.043 | 0.046 | 0.509 | 0.504 | 0.013 | 0.141 | 0.102 |
| lodestar | engine | S3 | 8390.000 | 4195.000 | 4195.000 | 0.057 | 0.078 | 0.508 | 0.502 | 0.041 | 0.086 | 0.108 |
| lodestar | engine | S4 | 8616.000 | 4308.000 | 4308.000 | 0.045 | 0.056 | 0.525 | 0.500 | 0.041 | 0.108 | 0.112 |
| lodestar | s0data | S0 | 62619.000 | 27655.000 | 34964.000 | 0.055 | 0.053 | 0.547 | 0.497 | 0.032 | 0.155 | – |
| lodestar | s0data | S1 | 22277.000 | 10954.000 | 11323.000 | 0.065 | 0.068 | 0.550 | 0.504 | 0.051 | 0.237 | – |
| ontarget | engine | S1 | 14853.000 | 7102.000 | 7751.000 | 0.082 | 0.107 | 0.552 | 0.499 | 0.186 | 0.057 | 0.246 |
| ontarget | engine | S2 | 12968.000 | 6484.000 | 6484.000 | 0.056 | 0.075 | 0.543 | 0.493 | 0.202 | 0.029 | 0.171 |
| ontarget | engine | S3 | 12274.000 | 6137.000 | 6137.000 | 0.035 | 0.046 | 0.530 | 0.505 | 0.081 | 0.070 | 0.121 |
| ontarget | engine | S4 | 12352.000 | 6176.000 | 6176.000 | 0.035 | 0.046 | 0.526 | 0.495 | 0.019 | 0.023 | 0.129 |
| ontarget | s0data | S0 | 42118.000 | 20032.000 | 22086.000 | 0.078 | 0.076 | 0.558 | 0.492 | 0.081 | 0.134 | – |
| ontarget | s0data | S1 | 14777.000 | 7038.000 | 7739.000 | 0.084 | 0.108 | 0.554 | 0.492 | 0.185 | 0.065 | – |
| paradigm-hf-seq | engine | S1 | 5129.000 | 1223.000 | 3906.000 | 0.392 | 0.579 | 0.722 | 0.505 | 0.307 | 0.157 | 0.408 |
| paradigm-hf-seq | engine | S2 | 2444.000 | 1222.000 | 1222.000 | 0.318 | 0.481 | 0.679 | 0.491 | 0.229 | 0.093 | 0.244 |
| paradigm-hf-seq | engine | S3 | 2268.000 | 1134.000 | 1134.000 | 0.185 | 0.281 | 0.598 | 0.503 | 0.220 | 0.105 | 0.191 |
| paradigm-hf-seq | engine | S4 | 2366.000 | 1183.000 | 1183.000 | 0.259 | 0.387 | 0.653 | 0.492 | 0.040 | 0.025 | 0.206 |
| paradigm-hf-seq | s0data | S0 | 7959.000 | 2377.000 | 5582.000 | 0.887 | 1.282 | 0.891 | 0.503 | 2.210 | 0.320 | – |
| paradigm-hf-seq | s0data | S1 | 1411.000 | 1189.000 | 222.000 | 0.381 | 0.567 | 0.718 | 0.529 | 0.194 | 0.328 | – |
| plato | engine | S1 | 6759.000 | 4011.000 | 2748.000 | 0.132 | 0.113 | 0.603 | 0.506 | 0.118 | 0.271 | 0.176 |
| plato | engine | S2 | 4730.000 | 2365.000 | 2365.000 | 0.050 | 0.068 | 0.514 | 0.502 | 0.084 | 0.178 | 0.063 |
| plato | engine | S3 | 4074.000 | 2037.000 | 2037.000 | 0.031 | 0.040 | 0.509 | 0.518 | 0.108 | 0.104 | 0.067 |
| plato | engine | S4 | 4040.000 | 2020.000 | 2020.000 | 0.028 | 0.038 | 0.503 | 0.491 | 0.066 | 0.133 | 0.029 |
| plato | s0data | S0 | 19020.000 | 5584.000 | 13436.000 | 0.185 | 0.171 | 0.644 | 0.494 | 0.164 | 0.144 | – |
| plato | s0data | S1 | 6759.000 | 4011.000 | 2748.000 | 0.133 | 0.115 | 0.603 | 0.510 | 0.118 | 0.271 | – |
| precision | engine | S1 | 5310.000 | 2440.000 | 2870.000 | 0.088 | 0.085 | 0.557 | 0.508 | 0.072 | 0.018 | 0.224 |
| precision | engine | S2 | 4178.000 | 2089.000 | 2089.000 | 0.053 | 0.061 | 0.528 | 0.516 | 0.003 | 0.005 | 0.237 |
| precision | engine | S3 | 3072.000 | 1536.000 | 1536.000 | 0.041 | 0.037 | 0.507 | 0.504 | 0.009 | 0.015 | 0.196 |
| precision | engine | S4 | 3976.000 | 1988.000 | 1988.000 | 0.040 | 0.045 | 0.520 | 0.521 | 0.022 | 0.032 | 0.165 |
| precision | s0data | S0 | 26563.000 | 8107.000 | 18456.000 | 0.163 | 0.078 | 0.666 | 0.499 | 0.027 | 0.049 | – |
| precision | s0data | S1 | 5310.000 | 2440.000 | 2870.000 | 0.089 | 0.087 | 0.557 | 0.495 | 0.072 | 0.018 | – |
| protect-af | engine | S1 | 1442.000 | 314.000 | 1128.000 | 0.185 | 0.277 | 0.593 | 0.457 | 0.357 | 0.018 | 0.062 |
| protect-af | engine | S2 | 620.000 | 310.000 | 310.000 | 0.164 | 0.249 | 0.581 | 0.495 | 0.190 | 0.083 | 0.090 |
| protect-af | engine | S3 | 210.000 | 105.000 | 105.000 | 0.266 | 0.351 | 0.594 | 0.449 | 0.526 | 0.429 | 0.173 |
| protect-af | engine | S4 | 586.000 | 293.000 | 293.000 | 0.197 | 0.238 | 0.598 | 0.452 | 0.114 | 0.014 | 0.044 |
| protect-af | s0data | S0 | 1391.000 | 324.000 | 1067.000 | 0.219 | 0.249 | 0.610 | 0.546 | 0.279 | 0.005 | – |
| protect-af | s0data | S1 | 471.000 | 313.000 | 158.000 | 0.174 | 0.271 | 0.566 | 0.478 | 0.259 | 0.133 | – |
| prove-it | engine | S1 | 4379.000 | 3848.000 | 531.000 | 0.133 | 0.149 | 0.534 | 0.498 | 0.120 | 0.314 | 0.058 |
| prove-it | engine | S2 | 1054.000 | 527.000 | 527.000 | 0.058 | 0.056 | 0.482 | 0.479 | 0.362 | 0.132 | 0.296 |
| prove-it | engine | S3 | 1008.000 | 504.000 | 504.000 | 0.069 | 0.081 | 0.435 | 0.523 | 0.196 | 0.014 | 0.357 |
| prove-it | engine | S4 | 1044.000 | 522.000 | 522.000 | 0.036 | 0.043 | 0.442 | 0.505 | 0.043 | 0.341 | 0.283 |
| prove-it | s0data | S0 | 44170.000 | 34401.000 | 9769.000 | 0.076 | 0.037 | 0.558 | 0.495 | 0.112 | 0.171 | – |
| prove-it | s0data | S1 | 4379.000 | 3848.000 | 531.000 | 0.133 | 0.149 | 0.532 | 0.504 | 0.120 | 0.314 | – |
| raft-af | engine | S1 | 3003.000 | 614.000 | 2389.000 | 0.189 | 0.094 | 0.659 | 0.509 | 0.144 | 0.221 | 0.295 |
| raft-af | engine | S2 | 1228.000 | 614.000 | 614.000 | 0.088 | 0.081 | 0.579 | 0.524 | 0.021 | 0.192 | 0.105 |
| raft-af | engine | S3 | 684.000 | 342.000 | 342.000 | 0.045 | 0.056 | 0.498 | 0.483 | 0.099 | 0.038 | 0.323 |
| raft-af | engine | S4 | 1052.000 | 526.000 | 526.000 | 0.059 | 0.067 | 0.562 | 0.510 | 0.003 | 0.167 | 0.068 |
| raft-af | s0data | S0 | 6929.000 | 1719.000 | 5210.000 | 0.134 | 0.078 | 0.694 | 0.493 | 0.078 | 0.165 | – |
| raft-af | s0data | S1 | 618.000 | 577.000 | 41.000 | 0.215 | 0.230 | 0.564 | 0.479 | 0.257 | 0.116 | – |
| rely | engine | S1 | 4172.000 | 702.000 | 3470.000 | 0.151 | 0.228 | 0.598 | 0.487 | 0.277 | 0.484 | 0.041 |
| rely | engine | S2 | 1404.000 | 702.000 | 702.000 | 0.065 | 0.094 | 0.520 | 0.511 | 0.054 | 0.244 | 0.217 |
| rely | engine | S3 | 1396.000 | 698.000 | 698.000 | 0.047 | 0.061 | 0.522 | 0.491 | 0.036 | 0.163 | 0.450 |
| rely | engine | S4 | 1398.000 | 699.000 | 699.000 | 0.071 | 0.102 | 0.538 | 0.499 | 0.212 | 0.090 | 0.059 |
| rely | s0data | S0 | 10234.000 | 1255.000 | 8979.000 | 0.162 | 0.191 | 0.602 | 0.493 | 0.247 | 0.373 | – |
| rely | s0data | S1 | 4172.000 | 702.000 | 3470.000 | 0.153 | 0.229 | 0.598 | 0.496 | 0.277 | 0.484 | – |
| rewind | engine | S1 | 6049.000 | 1335.000 | 4714.000 | 0.080 | 0.082 | 0.604 | 0.502 | 0.127 | 0.251 | 0.285 |
| rewind | engine | S2 | 2668.000 | 1334.000 | 1334.000 | 0.058 | 0.057 | 0.575 | 0.490 | 0.108 | 0.178 | 0.145 |
| rewind | engine | S3 | 2472.000 | 1236.000 | 1236.000 | 0.050 | 0.057 | 0.584 | 0.473 | 0.137 | 0.243 | 0.036 |
| rewind | engine | S4 | 2608.000 | 1304.000 | 1304.000 | 0.050 | 0.030 | 0.575 | 0.496 | 0.048 | 0.218 | 0.104 |
| rewind | s0data | S0 | 9012.000 | 2066.000 | 6946.000 | 0.123 | 0.126 | 0.613 | 0.497 | 0.148 | 0.226 | – |
| rewind | s0data | S1 | 6034.000 | 1321.000 | 4713.000 | 0.079 | 0.084 | 0.603 | 0.496 | 0.138 | 0.262 | – |
| rocket-af | engine | S1 | 7055.000 | 3633.000 | 3422.000 | 0.194 | 0.260 | 0.630 | 0.517 | 0.178 | 0.569 | 0.601 |
| rocket-af | engine | S2 | 4360.000 | 2180.000 | 2180.000 | 0.105 | 0.152 | 0.571 | 0.513 | 0.111 | 0.181 | 0.243 |
| rocket-af | engine | S3 | 3724.000 | 1862.000 | 1862.000 | 0.099 | 0.123 | 0.544 | 0.527 | 0.142 | 0.260 | 0.297 |
| rocket-af | engine | S4 | 4100.000 | 2050.000 | 2050.000 | 0.078 | 0.100 | 0.562 | 0.511 | 0.073 | 0.071 | 0.196 |
| rocket-af | s0data | S0 | 18411.000 | 9944.000 | 8467.000 | 0.208 | 0.264 | 0.616 | 0.494 | 0.207 | 0.444 | – |
| rocket-af | s0data | S1 | 7055.000 | 3633.000 | 3422.000 | 0.197 | 0.264 | 0.632 | 0.502 | 0.178 | 0.569 | – |
| sustain6 | engine | S1 | 3727.000 | 1701.000 | 2026.000 | 0.166 | 0.181 | 0.621 | 0.519 | 0.123 | 0.086 | 0.518 |
| sustain6 | engine | S2 | 2122.000 | 1061.000 | 1061.000 | 0.068 | 0.070 | 0.587 | 0.515 | 0.157 | 0.186 | 0.428 |
| sustain6 | engine | S3 | 1604.000 | 802.000 | 802.000 | 0.054 | 0.059 | 0.570 | 0.510 | 0.092 | 0.146 | 0.011 |
| sustain6 | engine | S4 | 1782.000 | 891.000 | 891.000 | 0.062 | 0.085 | 0.548 | 0.519 | 0.151 | 0.016 | 0.385 |
| sustain6 | s0data | S0 | 9674.000 | 5358.000 | 4316.000 | 0.284 | 0.277 | 0.667 | 0.500 | 0.167 | 0.063 | – |
| sustain6 | s0data | S1 | 3725.000 | 1700.000 | 2025.000 | 0.163 | 0.179 | 0.623 | 0.516 | 0.123 | 0.086 | – |
| tecos | engine | S1 | 2925.000 | 1513.000 | 1412.000 | 0.073 | 0.052 | 0.510 | 0.507 | 0.053 | 0.103 | 0.111 |
| tecos | engine | S2 | 2746.000 | 1373.000 | 1373.000 | 0.050 | 0.035 | 0.492 | 0.503 | 0.036 | 0.121 | 0.105 |
| tecos | engine | S3 | 2266.000 | 1133.000 | 1133.000 | 0.060 | 0.037 | 0.513 | 0.492 | 0.157 | 0.152 | 0.132 |
| tecos | engine | S4 | 2678.000 | 1339.000 | 1339.000 | 0.052 | 0.034 | 0.498 | 0.496 | 0.023 | 0.128 | 0.085 |
| tecos | s0data | S0 | 8062.000 | 4117.000 | 3945.000 | 0.064 | 0.061 | 0.513 | 0.489 | 0.034 | 0.022 | – |
| tecos | s0data | S1 | 2913.000 | 1508.000 | 1405.000 | 0.073 | 0.051 | 0.521 | 0.495 | 0.050 | 0.115 | – |
| transform-hf | engine | S1 | 15657.000 | 697.000 | 14960.000 | 0.175 | 0.189 | 0.654 | 0.492 | 0.140 | 0.066 | 0.102 |
| transform-hf | engine | S2 | 1394.000 | 697.000 | 697.000 | 0.161 | 0.189 | 0.622 | 0.503 | 0.120 | 0.050 | 0.086 |
| transform-hf | engine | S3 | 1372.000 | 686.000 | 686.000 | 0.128 | 0.141 | 0.602 | 0.478 | 0.011 | 0.040 | 0.112 |
| transform-hf | engine | S4 | 1394.000 | 697.000 | 697.000 | 0.143 | 0.163 | 0.588 | 0.520 | 0.034 | 0.077 | 0.037 |
| transform-hf | s0data | S0 | 45256.000 | 1376.000 | 43880.000 | 0.235 | 0.256 | 0.651 | 0.504 | 0.268 | 0.146 | – |
| transform-hf | s0data | S1 | 15657.000 | 697.000 | 14960.000 | 0.175 | 0.190 | 0.653 | 0.514 | 0.140 | 0.066 | – |
| valiant | engine | S1 | 2096.000 | 669.000 | 1427.000 | 0.114 | 0.092 | 0.553 | 0.465 | 0.174 | 0.291 | 0.026 |
| valiant | engine | S2 | 1204.000 | 602.000 | 602.000 | 0.018 | 0.022 | 0.502 | 0.516 | 0.183 | 0.052 | 0.147 |
| valiant | engine | S3 | 1086.000 | 543.000 | 543.000 | 0.026 | 0.021 | 0.479 | 0.497 | 0.152 | 0.063 | 0.013 |
| valiant | engine | S4 | 1200.000 | 600.000 | 600.000 | 0.032 | 0.026 | 0.527 | 0.499 | 0.213 | 0.034 | 0.112 |
| valiant | s0data | S0 | 42157.000 | 20071.000 | 22086.000 | 0.078 | 0.076 | 0.559 | 0.501 | 0.081 | 0.135 | – |
| valiant | s0data | S1 | 2096.000 | 669.000 | 1427.000 | 0.117 | 0.098 | 0.553 | 0.507 | 0.174 | 0.291 | – |
| value | engine | S1 | 26657.000 | 10208.000 | 16449.000 | 0.045 | 0.061 | 0.565 | 0.500 | 0.150 | 0.045 | 0.420 |
| value | engine | S2 | 20414.000 | 10207.000 | 10207.000 | 0.035 | 0.039 | 0.561 | 0.493 | 0.121 | 0.014 | 0.276 |
| value | engine | S3 | 20412.000 | 10206.000 | 10206.000 | 0.017 | 0.019 | 0.548 | 0.500 | 0.155 | 0.029 | 0.210 |
| value | engine | S4 | 20400.000 | 10200.000 | 10200.000 | 0.024 | 0.026 | 0.548 | 0.497 | 0.065 | 0.011 | 0.207 |
| value | s0data | S0 | 46443.000 | 18227.000 | 28216.000 | 0.069 | 0.085 | 0.580 | 0.500 | 0.580 | 0.069 | – |
| value | s0data | S1 | 26572.000 | 10157.000 | 16415.000 | 0.046 | 0.063 | 0.566 | 0.499 | 0.147 | 0.048 | – |

## per trial (engine): ph_mean, ecg_c and |Δlog HR| by step

| trial | S1_ph | S2_ph | S3_ph | S4_ph | S1_c | S2_c | S3_c | S4_c | S1_absd | S2_absd | S3_absd | S4_absd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| active-w | 0.163 | 0.144 | 0.150 | 0.129 | 0.627 | 0.587 | 0.614 | 0.603 | 0.073 | 0.060 | 0.102 | 0.056 |
| af-chf | 0.271 | 0.153 | 0.130 | 0.127 | 0.664 | 0.612 | 0.592 | 0.594 | 0.210 | 0.163 | 0.285 | 0.133 |
| affirm | 0.176 | 0.116 | 0.089 | 0.095 | 0.652 | 0.637 | 0.597 | 0.610 | 0.043 | 0.036 | 0.007 | 0.061 |
| allhat | 0.053 | 0.026 | 0.020 | 0.017 | 0.567 | 0.565 | 0.547 | 0.546 | 0.294 | 0.169 | 0.205 | 0.193 |
| amplify | 0.080 | 0.038 | 0.030 | 0.026 | 0.547 | 0.532 | 0.514 | 0.500 | 0.060 | 0.168 | 0.039 | 0.122 |
| aristotle | 0.129 | 0.080 | 0.054 | 0.086 | 0.595 | 0.558 | 0.523 | 0.545 | 0.332 | 0.053 | 0.101 | 0.147 |
| ascot | 0.187 | 0.130 | 0.134 | 0.124 | 0.625 | 0.605 | 0.601 | 0.599 | 0.130 | 0.191 | 0.243 | 0.129 |
| cabana-v2 | 0.347 | 0.143 | 0.080 | 0.089 | 0.708 | 0.625 | 0.578 | 0.585 | 1.439 | 0.914 | 0.114 | 0.526 |
| canvas | 0.115 | 0.048 | 0.055 | 0.037 | 0.590 | 0.542 | 0.522 | 0.543 | 0.080 | 0.046 | 0.261 | 0.052 |
| carmelina | 0.050 | 0.011 | 0.031 | 0.024 | 0.507 | 0.485 | 0.459 | 0.497 | 0.013 | 0.014 | 0.133 | 0.075 |
| carolina | 0.061 | 0.043 | 0.036 | 0.052 | 0.529 | 0.509 | 0.530 | 0.517 | 0.002 | 0.124 | 0.174 | 0.141 |
| comet | 0.362 | 0.294 | 0.237 | 0.204 | 0.701 | 0.681 | 0.646 | 0.632 | 0.096 | 0.020 | 0.092 | 0.048 |
| declare | 0.289 | 0.060 | 0.070 | 0.024 | 0.637 | 0.543 | 0.527 | 0.521 | 0.809 | 0.180 | 0.261 | 0.214 |
| east-afnet4 | 0.176 | 0.115 | 0.109 | 0.085 | 0.628 | 0.599 | 0.579 | 0.588 | 0.254 | 0.201 | 0.266 | 0.173 |
| elite-ii | 0.079 | 0.045 | 0.064 | 0.031 | 0.508 | 0.506 | 0.493 | 0.522 | 0.177 | 0.163 | 0.114 | 0.112 |
| empa-reg | 0.138 | 0.029 | 0.026 | 0.023 | 0.573 | 0.534 | 0.520 | 0.512 | 0.069 | 0.069 | 0.037 | 0.087 |
| emperor-preserved-v2 | 0.075 | 0.071 | 0.038 | 0.039 | 0.550 | 0.509 | 0.464 | 0.503 | 0.057 | 0.049 | 0.106 | 0.041 |
| frail-af | 0.071 | 0.049 | 0.046 | 0.058 | 0.546 | 0.521 | 0.499 | 0.507 | 0.599 | 0.660 | 0.668 | 0.747 |
| insight | 0.046 | 0.032 | 0.057 | 0.039 | 0.551 | 0.506 | 0.529 | 0.545 | 0.595 | 0.426 | 0.139 | 0.222 |
| laaos3 | 0.174 | 0.157 | 0.139 | 0.142 | 0.655 | 0.563 | 0.588 | 0.603 | 0.165 | 0.061 | 0.189 | 0.170 |
| leader | 0.134 | 0.043 | 0.074 | 0.061 | 0.628 | 0.571 | 0.559 | 0.545 | 0.588 | 0.398 | 0.535 | 0.359 |
| life | 0.196 | 0.105 | 0.131 | 0.118 | 0.597 | 0.575 | 0.543 | 0.553 | 0.185 | 0.016 | 0.010 | 0.014 |
| lodestar | 0.066 | 0.043 | 0.057 | 0.045 | 0.550 | 0.509 | 0.508 | 0.525 | 0.079 | 0.102 | 0.108 | 0.112 |
| ontarget | 0.082 | 0.056 | 0.035 | 0.035 | 0.552 | 0.543 | 0.530 | 0.526 | 0.246 | 0.171 | 0.121 | 0.129 |
| paradigm-hf-seq | 0.392 | 0.318 | 0.185 | 0.259 | 0.722 | 0.679 | 0.598 | 0.653 | 0.408 | 0.244 | 0.191 | 0.206 |
| plato | 0.132 | 0.050 | 0.031 | 0.028 | 0.603 | 0.514 | 0.509 | 0.503 | 0.176 | 0.063 | 0.067 | 0.029 |
| precision | 0.088 | 0.053 | 0.041 | 0.040 | 0.557 | 0.528 | 0.507 | 0.520 | 0.224 | 0.237 | 0.196 | 0.165 |
| protect-af | 0.185 | 0.164 | 0.266 | 0.197 | 0.593 | 0.581 | 0.594 | 0.598 | 0.062 | 0.090 | 0.173 | 0.044 |
| prove-it | 0.133 | 0.058 | 0.069 | 0.036 | 0.534 | 0.482 | 0.435 | 0.442 | 0.058 | 0.296 | 0.357 | 0.283 |
| raft-af | 0.189 | 0.088 | 0.045 | 0.059 | 0.659 | 0.579 | 0.498 | 0.562 | 0.295 | 0.105 | 0.323 | 0.068 |
| rely | 0.151 | 0.065 | 0.047 | 0.071 | 0.598 | 0.520 | 0.522 | 0.538 | 0.041 | 0.217 | 0.450 | 0.059 |
| rewind | 0.080 | 0.058 | 0.050 | 0.050 | 0.604 | 0.575 | 0.584 | 0.575 | 0.285 | 0.145 | 0.036 | 0.104 |
| rocket-af | 0.194 | 0.105 | 0.099 | 0.078 | 0.630 | 0.571 | 0.544 | 0.562 | 0.601 | 0.243 | 0.297 | 0.196 |
| sustain6 | 0.166 | 0.068 | 0.054 | 0.062 | 0.621 | 0.587 | 0.570 | 0.548 | 0.518 | 0.428 | 0.011 | 0.385 |
| tecos | 0.073 | 0.050 | 0.060 | 0.052 | 0.510 | 0.492 | 0.513 | 0.498 | 0.111 | 0.105 | 0.132 | 0.085 |
| transform-hf | 0.175 | 0.161 | 0.128 | 0.143 | 0.654 | 0.622 | 0.602 | 0.588 | 0.102 | 0.086 | 0.112 | 0.037 |
| valiant | 0.114 | 0.018 | 0.026 | 0.032 | 0.553 | 0.502 | 0.479 | 0.527 | 0.026 | 0.147 | 0.013 | 0.112 |
| value | 0.045 | 0.035 | 0.017 | 0.024 | 0.565 | 0.561 | 0.548 | 0.548 | 0.420 | 0.276 | 0.210 | 0.207 |
