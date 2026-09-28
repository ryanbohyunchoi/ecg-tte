# v1.9 G3: AI-ECG prognostic and predictive enrichment for trial design (38 trials; exploratory)

Plan: `docs/v18/V19_GERMAN_STYLE_PLAN.md` §G3 (fixed in `661cf67` before results). Code: `scripts/v19/g3_enrichment.py`
(`run` → `summarize` → `tables` → `figures`). Aggregates: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v19-g3-enrichment/`
(umask 077; counts 1–10 suppressed; none occurred: min cell n = 586, min events = 67). **Everything here is exploratory. Every cell is reported, either below or in the appendix.**

## Plain-language verdict

1. **The AI-ECG risk score is prognostic in every trial, but it is the weakest of the scores.**
   - It is fitted on 32 ECG-embedding PCs only and cross-fitted, so it never sees the patient it scores.
   - In the emulated (sparse-PS matched) trial populations, its pooled HR per SD is **1.52 (1.45–1.59)** and its mean C-index is **0.62**.
   - Comparators: clinical demographics + diagnoses score **1.76 (1.69–1.83)**, C 0.67; CLMBR-T **1.93 (1.82–2.04)**, C 0.68.
   - The shuffled-ECG placebo is null: 1.00 (0.98–1.02), C 0.50.
   - The ECG score is below the clinical score in 36/38 trials (ΔC −0.047, 95% CI −0.058 to −0.036).
2. **The ECG adds a little on top of clinical data.** ECG + clinical vs clinical alone gives ΔC **+0.014 (+0.009 to +0.018)**, with C higher in 33/38 trials.
3. **Top-quartile enrichment reduces the number of patients who must be enrolled** (at the cost of screening 4×). The pooled reductions in the matched population are:

   | Score | Top 25% | Top 50% |
   |---|---|---|
   | AI-ECG | **34%** (30–37%) | 22% |
   | Clinical | 44% (41–46%) | 29% |
   | CLMBR | 44% | 30% |
   | ECG + clinical | 45% (42–48%) | 31% |

   The ECG's added enrichment over clinical data is about 1 percentage point. German et al.'s PGS gave 8.6–26%, so an ECG-only score enriches more than a PGS. Routine EHR data enrich more still.
4. **A score's prognostic strength is the same in the emulated trial population and in all initiators.** For the ECG, the matched/unmatched ratio of HR per SD is 1.01 (16/38 trials lower when matched, p = 0.37). German et al. found a difference for AF; there is no such difference here: AF-12 ECG gives 1.45 matched vs 1.40 unmatched.
5. **There is no convincing predictive enrichment.**
   - The pooled treatment × ECG-score interaction is a ratio of 1.037 (1.000–1.075) per SD, p = 0.052. On the HR scale, the drug looks slightly *less* favourable in higher-risk patients.
   - The clinical, CLMBR and combined scores show the same small positive interaction (1.04–1.05), and the placebo does not (0.99). This points to a generic risk-scale artefact (e.g. depletion of susceptibles or residual confounding correlated with risk), not to ECG-specific effect modification.
   - In the primary matched population, 2/38 per-trial ECG interactions pass within-score BH q < 0.10: VALUE (q = 0.007) and PROVE-IT (q = 0.063).
   - **AF and HF trials:** no ECG interaction reaches q < 0.19. The fixed-effect ratio is 1.04 for AF-12 and 0.94 for HF-5.

**Bottom line.** As in German et al., the new data type is useful for trial *design* (prognostic enrichment), not as an effect modifier. In our system, however, an ECG-only score is clearly weaker than scores built from routine demographics and diagnoses (or from CLMBR). Its incremental value over them is small and consistent, but not large.

## Methods (as run)

**Trials and loading.** The trials are the 38 of v1.8 (`v18_embed_compare.ALL`: v1.6 18 + v1.7 15 + v1.8 AF 5). Each is loaded with `v16_engine.load_trial`: imputation 1; follow-up capped at the trial horizon; primary outcome; rows with `T.y_ok`.

**Risk scores.** All scores are fitted in each trial's full cohort of initiators, with no treatment term:
- **Model:** 5-fold cross-fitted L2-penalised Cox (lifelines, penalizer 0.01, l1_ratio 0; features standardised within the training fold).
- **Folds:** `StratifiedKFold` on the event indicator, seed 19030 + trial index. One row is one patient, so the folds are by patient.
- **Score:** the out-of-fold linear predictor.

| Score | Features |
|---|---|
| **ECG** (primary) | 32 ECG-embedding PCs (`T.ecg_pc`). 32 was chosen to match the PS arms of v1.6–v1.8. |
| ECG64 | 64 PCs (sensitivity analysis) |
| **CLIN** | `T.X_dx`: demographics + sparse diagnosis flags (= the `sparse` PS design). This is the cross-fitted "demo + dx" clinical comparator. |
| **CLMBR** | 64 CLMBR-T PCs |
| **ECG+CLIN** | ECG32 + X_dx |
| shufECG | ECG32 rows permuted with `T.shuffle_perm` (placebo) |
| PROG | The prognostic reference already built for `smd_prog_full`. See the definition below. |

PROG = `claude-<trial>-progref-v1/scores-v3` `prog_full`:
- It is an L2 logistic model fitted on 30,000 external reference patients outside the cohort, with about 900 panel features.
- Its outcome is generic and 1-year, not the trial outcome, and it is not cross-fitted.
- Its linear predictor is extremely heavy-tailed in a few trials (naive HR per SD blew up in ALLHAT, VALUE, CANVAS and ONTARGET). Its HR per SD and interaction therefore use a rank-based inverse-normal transform (see deviation 2).

**Populations.**

| Label | Population |
|---|---|
| `unm` | All initiators in the trial cohort (unmatched) |
| `m_sparse` (**primary** matched) | The sparse-PS (`T.X_dx`, L2 C = 1) 1:1 caliper-0.2 matched sample |
| `m_P1` (secondary) | Demographics-PS matched sample |
| `m_clin` (secondary) | Clinical-PS (`T.X_core`) matched sample |

Scores are fitted once in the full cohort and evaluated in each population. Every patient's score is out-of-fold.

**Prognostic metrics.**
- **HR per SD:** Cox on the score standardised within the population. Matched samples use a pair-clustered robust SE; unmatched uses a robust SE.
- **Harrell's C.**
- **Uncertainty:** bootstrap, B = 200, resampling pairs (matched) or patients (unmatched) with the score held fixed. It gives SEs for C and for paired ΔC, and percentile CIs for the reductions.
- **Pooling:** DerSimonian–Laird random effects; I² is reported. Paired across-trial contrasts also get an exact / Monte-Carlo sign-flip p (`v13_summarize.sign_flip`, two-sided).

**Sample size (German et al. approach).** German et al. hold the relative treatment effect fixed at the RCT HR, so the required number of events is the same with or without enrichment. Enrichment helps only by raising the event rate, which reduces the number of patients who must be enrolled to accrue those events.
- **Required events:** D = 4(z₀.₉₇₅ + z₀.₈₀)² / (log HR_RCT)² (Schoenfeld; 1:1; two-sided α 0.05; power 80%).
- **Enrolled patients:** N = D / p, where p is the Kaplan–Meier cumulative incidence at the trial horizon (arms pooled). p is computed in the full population and in its top 25% / 50% by score (quantile threshold within the population).
- **Reduction:** 1 − p_full / p_top. It does not depend on the HR. N depends on the HR and is undefined for VALIANT (RCT HR = 1.00).
- **Screening:** screening burden = N_top / fraction.
- **Pooling:** random effects on log(p_full / p_top).

**Predictive metrics.**
- **Model:** Cox in the matched sample with treatment, z (the score standardised in the matched sample) and treatment × z, with a pair-clustered robust SE.
- **Reported quantity:** exp(β_int) is the ratio of treatment HRs per SD of the score. A value > 1 means relative benefit is smaller (or harm larger) at higher risk.
- **Reporting:** per trial and DL-pooled, with BH-FDR within each score × population over 38 trials (`q_within`) and over all 798 cells (`q_all`).

## Audit / sanity checks

- **Reproduction of a known cell.** The sparse-PS matched log HR was rebuilt inside this script with `E.ps_logit` / `E.match` / `E.cox`. It reproduces `claude-v18-embed-compare/results.csv` (full half, sparse, base) in all 38 trials, with identical pair counts. The max |Δ| is 1e-16, except ALLHAT at 4.0e-5: this is the documented greedy-matching near-tie in `docs/v16/ENGINE_VALIDATION.md`, and its pair count is identical.
- **Placebo (shufECG).** The pooled HR per SD is 0.997 (0.978–1.016), mean C 0.495, and the enrichment reduction is 1.9% (−0.2 to 3.8%).
  - The interaction ratio is 0.993 (p = 0.58).
  - Per-trial placebo C ranged 0.37–0.54. The low tail is PROTECT AF matched, with 79 events.
  - A pre-run null diagnostic was done because of this tail. With 8 random permutations or N(0,1) noise, cross-fitted null C-indices average 0.48–0.51, with SD 0.025–0.04 in the small trials. The extreme single draws are therefore sampling noise, not leakage.
  - The penalty (0.01 / 0.1 / 1) and 1% winsorisation changed the ECG C by ≤ 0.004.
- **Uncertainty is understated.** The bootstrap holds the score fixed, so the CIs ignore model-refit and fold-split variability. For the ECG score that variability is ~0.01–0.02 C in the small trials (3 fold seeds, pre-run diagnostic).

## Deviations from the plan (logged)

1. **Additions to the plan.** These go beyond what was written:
   - enrichment at 50% (in addition to 25%);
   - C-index;
   - an ECG64 sensitivity score;
   - a shuffled-ECG placebo;
   - an ECG + clinical combined score;
   - the external PROG score;
   - secondary matched populations P1 and clinical-PS.
2. **PROG HR per SD and interaction use a rank-based inverse-normal transform.** This is post hoc, adopted after the first run showed extreme values caused by the heavy tail. C and quantile enrichment are unchanged by it.
3. **Choice of clinical comparator.** The plan names "the demographics + dx prognostic score". The cross-fitted demo + dx Cox (CLIN) is used as the primary clinical comparator because it is outcome-specific and cross-fitted, like the ECG score. The external `prog_full` score is reported alongside it.
4. **The primary matched population is the sparse-PS sample.** The plan said "trial-eligible matched population" without fixing the PS.
5. **No other deviations.**

## Results

### Prognostic, pooled (random effects over 38 trials)

**HR per SD of score:**

| Score | Matched (sparse) | Unmatched |
|---|---|---|
| **AI-ECG (32)** | **1.52 (1.45–1.59)** | **1.50 (1.45–1.57)** |
| ECG64 | 1.55 (1.47–1.62) | 1.53 (1.47–1.60) |
| Clinical (demo + dx) | 1.76 (1.69–1.83) | 1.79 (1.72–1.86) |
| CLMBR-T | 1.93 (1.82–2.04) | 1.93 (1.83–2.04) |
| ECG + clinical | 1.86 (1.79–1.94) | 1.88 (1.81–1.95) |
| PROG (external, rank-normal) | 2.03 (1.94–2.14) | 2.04 (1.96–2.13) |
| shufECG (placebo) | 1.00 (0.98–1.02) | 1.00 (0.98–1.01) |

**C-index, pooled (95% CI) [range over trials]:**

| Score | Matched (sparse) | Unmatched |
|---|---|---|
| **AI-ECG (32)** | 0.620 (0.607–0.634) [0.53–0.74] | 0.619 [0.55–0.73] |
| ECG64 | 0.628 | 0.625 |
| Clinical (demo + dx) | 0.670 (0.657–0.682) [0.59–0.79] | 0.677 |
| CLMBR-T | 0.680 [0.55–0.83] | 0.681 |
| ECG + clinical | 0.683 | 0.687 |
| PROG (external, rank-normal) | 0.691 | 0.694 |
| shufECG (placebo) | 0.499 | 0.499 |

I² for HR per SD is 0.91–0.95 for every real score; placebo I² is 0.48 (matched) and 0.41 (unmatched). The ECG HR per SD is significant (p < 0.05) in 36/38 trials matched and 38/38 unmatched.

Secondary matched populations: P1-matched ECG 1.53 (1.46–1.59) and clinical-PS-matched ECG 1.52 (1.46–1.59). Their CLIN and CLMBR values are 1.79 / 1.94 (P1) and 1.75 / 1.92 (clinical PS). Full table: `prognostic_pooled.csv`.

**By category, sparse-matched ECG HR per SD** (clinical and CLMBR for comparison):

| Category | ECG | Clinical | CLMBR |
|---|---|---|---|
| **AF (12)** | 1.45 (1.33–1.58) | 1.84 | 2.07 |
| **HF (5)** | 1.36 (1.29–1.43) | 1.61 | 1.80 |
| DM (9) | 1.57 | 1.76 | 1.78 |
| HTN (5) | 1.66 | 1.70 | 1.89 |
| ACS (2) | 1.59 | 1.92 | 2.06 |
| Other (5) | 1.59 | 1.72 | 2.00 |

The ECG is relatively weakest in AF and HF: there the disease-defining information is already in the diagnosis codes, and the cohort is homogeneous in the ECG's strongest signal (rhythm / LV dysfunction). The ECG comes closest to clinical in HTN (e.g. LIFE C 0.596 vs 0.592; VALUE 0.679 vs 0.696).

**Paired ΔC across 38 trials** (bootstrap-SE DL pooled; k = trials with a > b; sign-flip p):

| a − b | Matched (sparse) | Unmatched |
|---|---|---|
| ECG − clinical | −0.047 (−0.058, −0.036); 2/38; p < 1e-4 | −0.056 (−0.065, −0.047); 0/38 |
| ECG+clinical − clinical | **+0.014 (+0.009, +0.018); 33/38; p < 1e-4** | +0.011 (+0.007, +0.015); 29/38 |
| ECG+clinical − ECG | +0.059; 38/38 | +0.066; 38/38 |
| CLMBR − ECG | +0.060 (+0.048, +0.072); 37/38 | +0.063; 37/38 |
| CLMBR − clinical | +0.011 (+0.002, +0.021); 23/38; p = 0.14 | +0.006 (−0.003, +0.014); 20/38; p = 0.48 |
| ECG64 − ECG | +0.008 (+0.005, +0.011); 29/38 | +0.007; 33/38 |
| ECG − placebo | +0.125; 37/38 | +0.120; 38/38 |
| ECG − PROG (mean) | −0.071; 0/38 | −0.076; 0/38 |

**Emulated trial population vs all initiators** (log HR per SD, matched minus unmatched, across trials):

| Score | Ratio | Trials lower when matched | Sign-flip p |
|---|---|---|---|
| ECG | 1.007 | 16/38 | 0.37 |
| Clinical | 0.978 | 26/38 | 0.002 |
| CLMBR | 0.994 | — | 0.49 |
| ECG + clinical | 0.988 | — | 0.035 |
| Placebo | 0.983 | — | 0.10 |

Matching on the sparse PS (which contains the clinical score's inputs) slightly attenuates the clinical score's gradient, as expected. It does not attenuate the ECG's.

### Enrichment (sparse-matched population; `G3_sample_size.png`)

**Pooled reduction in enrolled patients (random effects on log event-rate ratio; per-trial range in brackets):**

| Score | Top 25% | Top 50% |
|---|---|---|
| **AI-ECG** | **33.5% (30.1–36.8)** [14–51] | **22.4% (20.2–24.5)** [2–35] |
| ECG64 | 34.7% (31.1–38.0) | 23.2% |
| Clinical | 43.6% (40.8–46.3) [23–59] | 28.9% (27.2–30.6) |
| CLMBR | 43.7% (40.8–46.6) [18–62] | 30.3% (28.6–32.1) |
| ECG + clinical | 44.7% (41.8–47.5) [26–59] | 30.5% (28.8–32.2) |
| PROG | 45.2% (42.5–47.8) | 31.4% |
| Placebo | 1.9% (−0.2–3.8) | 0.3% |

Unmatched (all initiators) values are nearly identical: ECG 32.9%, clinical 44.2%, CLMBR 43.2%, combined 44.8% (top 25%).

Median ECG top-25% reduction by category:

| Category | ECG | Clinical |
|---|---|---|
| AF | 27% | 43% |
| HF | 24% | 37% |
| DM | 38% | 47% |
| HTN | 41% | 43% |
| ACS | 38% | 51% |
| Other | 38% | 41% |

Paired enrichment contrasts (log event-rate ratio of a vs b, top 25%, matched):

| Contrast | Trials where a is better | DL difference |
|---|---|---|
| ECG vs clinical | 1/38 | −0.147 (−0.180, −0.113) |
| ECG + clinical vs clinical | 29/38 (p = 0.035) | +0.026 (+0.013, +0.039), i.e. ≈ +1.1 pp reduction |
| CLMBR vs ECG | 34/38 | — |

For top 50%, ECG + clinical vs clinical is 28/38 trials, +0.025.

**Worked examples (ECG top 25%, matched, RCT HR):**
- **ARISTOTLE** (HR 0.79): p rises from 0.087 to 0.120. Enrolment falls from 6,513 to 4,698 patients (−28%), but 18,793 must be screened. With the clinical score it is −59%.
- **DECLARE** (HR 0.83): p rises from 0.32 to 0.66, giving 2,802 → 1,366 (−51%).
- **Near-null RCT HRs** (ALLHAT, ONTARGET, CAROLINA, CARMELINA, TECOS, TRANSFORM-HF) need 10⁵–10⁶ patients regardless of enrichment.

### Predictive (treatment × score; sparse-matched primary)

**Pooled ratio of treatment HR per SD** (DL; q = within-score BH over 38 trials):

| Score | Pooled ratio | p | I² | Trials p < 0.05 | Trials q < 0.10 |
|---|---|---|---|---|---|
| **AI-ECG** | **1.037 (1.000–1.075)** | 0.052 | 0.44 | 9 | 2 (VALUE q = 0.007; PROVE-IT q = 0.063) |
| ECG64 | 1.027 (0.996–1.059) | 0.094 | — | 6 | 0 |
| Clinical | 1.037 (1.008–1.067) | 0.013 | — | 3 | 2 (VALUE, LIFE) |
| CLMBR | 1.049 (1.010–1.090) | 0.014 | — | 6 | 2 (AFFIRM, EMPEROR-Preserved) |
| ECG + clinical | 1.046 (1.021–1.072) | < 0.001 | 0.04 | 3 | 2 |
| PROG | 1.015 (0.978–1.053) | 0.45 | — | 3 | 1 |
| Placebo | 0.993 (0.967–1.019) | 0.58 | — | 2 | 0 |

In the secondary matched samples, the ECG pooled ratio is 1.036 (P1; p = 0.08) and 1.025 (clinical PS; p = 0.15). Over all 798 interaction cells, 19 have q_all < 0.05. They are concentrated in VALUE (9 cells, every score), AFFIRM (5, mostly CLMBR / clinical-PS matched), LODESTAR P1 (2), LIFE, EMPEROR-Preserved and PROVE-IT (1 each).

A trial whose interaction appears for every score, including clinical ones (VALUE), reflects the risk scale of that emulation, not ECG-specific modification.

**AF and HF trials (ECG score, sparse matched):**

| Trial | Interaction ratio | p | q |
|---|---|---|---|
| ARISTOTLE | 1.04 | 0.66 | |
| ROCKET AF | 0.92 | 0.48 | |
| RE-LY | 1.17 | 0.39 | |
| EAST-AFNET 4 | 0.99 | 0.75 | |
| CABANA | 1.05 | 0.58 | |
| AFFIRM | 1.09 | 0.041 | 0.19 |
| AF-CHF | 1.13 | 0.20 | |
| FRAIL-AF | 0.95 | 0.78 | |
| LAAOS III | 0.92 | 0.66 | |
| PROTECT AF | 1.30 | 0.24 | |
| RAFT-AF | 1.18 | 0.046 | 0.19 |
| ACTIVE W | 0.80 | 0.086 | |
| COMET | 0.92 | 0.15 | |
| PARADIGM-HF (seq) | 0.87 | 0.024 | 0.19 |
| TRANSFORM-HF | 1.15 | 0.27 | |
| ELITE II | 1.01 | 0.95 | |
| EMPEROR-Preserved | 1.00 | 0.98 | |

Fixed-effect: AF-12 1.04 and HF-5 0.94. The CLMBR interactions in AFFIRM (q = 0.001) and EMPEROR-Preserved (q = 0.02) are the only AF/HF cells with q < 0.10 in the primary population. Neither is ECG.

## Figures

- `docs/v19/G3_prognostic_forest.png`: HR per SD of the ECG, clinical and CLMBR scores, per trial (grouped by category) and pooled. Left panel: sparse-matched population; right panel: all initiators.
- `docs/v19/G3_sample_size.png`: % reduction in enrolled patients from enrolling the top 25% (left) or top 50% (right) of each score (ECG, clinical, CLMBR, ECG + clinical), per trial with bootstrap CI, and pooled.

## Files (`/mnt/raid0/rbc58/ecg-tte/audits/claude-v19-g3-enrichment/`)

| Content | Files |
|---|---|
| Per-trial cells | `prognostic_per_trial.csv`, `enrichment_per_trial.csv`, `predictive_per_trial.csv` |
| Pooled results | `prognostic_pooled.csv`, `prognostic_by_category.csv`, `enrichment_pooled.csv`, `predictive_pooled.csv` |
| Paired contrasts | `cindex_paired.csv`, `enrichment_paired.csv`, `matched_vs_unmatched.csv` |
| Bootstrap replicates | `bootstrap.csv` (aggregate statistics per replicate) |
| Run log and checks | `log.json`, `log_check.csv` (reproduction check) |
| Tables | `tables.md` (appended below) |

## Appendix: every per-trial cell

### Prognostic, sparse-PS matched

| trial | cat | n | events | HR/SD ECG | HR/SD CLIN | HR/SD CLMBR | HR/SD ECG+CLIN | HR/SD PROG | HR/SD shufECG | C ECG | C CLIN | C CLMBR | C ECG+CLIN | C PROG | C shufECG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 5602 | 450 | 1.37 (1.26-1.50) | 2.17 (2.02-2.34) | 2.41 (2.19-2.66) | 2.23 (2.07-2.40) | 2.01 (1.82-2.22) | 0.92 (0.83-1.01) | 0.591 | 0.736 | 0.733 | 0.743 | 0.689 | 0.477 |
| rocket-af | AF | 4355 | 331 | 1.31 (1.16-1.47) | 1.98 (1.84-2.14) | 2.19 (1.97-2.43) | 2.06 (1.90-2.23) | 1.89 (1.68-2.12) | 1.07 (0.96-1.19) | 0.577 | 0.711 | 0.717 | 0.721 | 0.673 | 0.513 |
| rely | AF | 1403 | 113 | 1.20 (1.00-1.42) | 1.85 (1.63-2.10) | 2.06 (1.71-2.48) | 1.87 (1.64-2.13) | 1.92 (1.59-2.32) | 0.94 (0.77-1.13) | 0.551 | 0.702 | 0.694 | 0.706 | 0.684 | 0.486 |
| east-afnet4 | AF | 6913 | 3219 | 1.67 (1.61-1.73) | 2.13 (2.06-2.21) | 2.26 (2.16-2.36) | 2.22 (2.13-2.31) | 2.20 (2.09-2.30) | 1.00 (0.97-1.04) | 0.648 | 0.712 | 0.713 | 0.720 | 0.723 | 0.500 |
| cabana-v2 | AF | 3146 | 504 | 2.06 (1.90-2.24) | 1.84 (1.72-1.97) | 3.34 (3.01-3.70) | 2.27 (2.12-2.43) | 3.81 (3.35-4.33) | 0.99 (0.91-1.08) | 0.715 | 0.681 | 0.826 | 0.749 | 0.806 | 0.494 |
| affirm | AF | 8198 | 2353 | 1.65 (1.59-1.72) | 1.82 (1.75-1.90) | 2.61 (2.48-2.76) | 2.00 (1.92-2.09) | 2.33 (2.23-2.44) | 1.03 (0.99-1.07) | 0.648 | 0.673 | 0.741 | 0.699 | 0.742 | 0.508 |
| af-chf | AF | 2532 | 552 | 1.64 (1.50-1.80) | 1.96 (1.78-2.16) | 2.00 (1.82-2.19) | 2.13 (1.93-2.34) | 1.93 (1.77-2.10) | 1.03 (0.95-1.12) | 0.632 | 0.678 | 0.687 | 0.695 | 0.693 | 0.509 |
| frail-af | AF | 1593 | 124 | 1.11 (0.93-1.33) | 1.58 (1.34-1.86) | 1.49 (1.21-1.84) | 1.51 (1.28-1.78) | 1.86 (1.56-2.22) | 1.14 (0.97-1.33) | 0.529 | 0.639 | 0.619 | 0.626 | 0.667 | 0.542 |
| laaos3 | AF | 1022 | 79 | 1.15 (0.93-1.43) | 1.73 (1.45-2.06) | 1.35 (1.08-1.70) | 1.77 (1.42-2.19) | 1.42 (1.11-1.81) | 0.93 (0.75-1.17) | 0.532 | 0.644 | 0.576 | 0.636 | 0.590 | 0.480 |
| protect-af | AF | 620 | 79 | 1.56 (1.29-1.89) | 1.48 (1.23-1.78) | 1.63 (1.36-1.94) | 1.68 (1.38-2.05) | 1.79 (1.46-2.19) | 0.62 (0.50-0.78) | 0.634 | 0.646 | 0.651 | 0.668 | 0.665 | 0.371 |
| raft-af | AF | 1228 | 630 | 1.34 (1.24-1.46) | 1.71 (1.57-1.87) | 2.09 (1.90-2.29) | 1.73 (1.59-1.89) | 2.19 (1.99-2.42) | 1.04 (0.96-1.12) | 0.588 | 0.654 | 0.697 | 0.658 | 0.718 | 0.514 |
| active-w | AF | 1643 | 258 | 1.30 (1.16-1.46) | 1.63 (1.46-1.81) | 1.69 (1.50-1.91) | 1.72 (1.53-1.93) | 1.77 (1.58-1.98) | 0.98 (0.86-1.12) | 0.577 | 0.650 | 0.647 | 0.656 | 0.664 | 0.501 |
| comet | HF | 4844 | 1258 | 1.36 (1.29-1.44) | 1.79 (1.69-1.90) | 1.84 (1.74-1.96) | 1.80 (1.70-1.91) | 2.00 (1.88-2.12) | 0.96 (0.91-1.02) | 0.587 | 0.666 | 0.674 | 0.668 | 0.700 | 0.490 |
| paradigm-hf-seq | HF | 2443 | 1269 | 1.33 (1.26-1.41) | 1.54 (1.46-1.63) | 1.78 (1.67-1.90) | 1.62 (1.53-1.72) | 1.79 (1.67-1.91) | 1.06 (1.00-1.12) | 0.587 | 0.629 | 0.653 | 0.642 | 0.662 | 0.516 |
| transform-hf | HF | 1392 | 241 | 1.52 (1.35-1.71) | 1.65 (1.43-1.91) | 1.88 (1.64-2.16) | 1.84 (1.62-2.09) | 1.99 (1.76-2.26) | 1.03 (0.91-1.17) | 0.612 | 0.633 | 0.672 | 0.658 | 0.688 | 0.513 |
| elite-ii | HF | 2294 | 381 | 1.42 (1.28-1.57) | 1.62 (1.47-1.79) | 1.63 (1.45-1.83) | 1.73 (1.55-1.92) | 1.85 (1.65-2.06) | 0.99 (0.89-1.10) | 0.604 | 0.633 | 0.634 | 0.649 | 0.657 | 0.503 |
| emperor-preserved-v2 | HF | 1054 | 509 | 1.24 (1.15-1.35) | 1.46 (1.33-1.59) | 1.82 (1.65-2.00) | 1.51 (1.38-1.66) | 1.99 (1.81-2.20) | 0.96 (0.89-1.05) | 0.568 | 0.619 | 0.663 | 0.627 | 0.690 | 0.496 |
| empa-reg | DM | 3269 | 566 | 1.54 (1.43-1.67) | 1.78 (1.65-1.92) | 1.83 (1.68-1.99) | 1.78 (1.65-1.92) | 1.96 (1.79-2.16) | 0.99 (0.91-1.08) | 0.634 | 0.672 | 0.666 | 0.673 | 0.676 | 0.496 |
| carolina | DM | 1470 | 293 | 1.37 (1.23-1.52) | 1.80 (1.62-2.01) | 1.61 (1.45-1.80) | 1.76 (1.58-1.96) | 1.85 (1.64-2.08) | 1.05 (0.94-1.18) | 0.596 | 0.661 | 0.629 | 0.656 | 0.652 | 0.506 |
| leader | DM | 906 | 145 | 1.46 (1.25-1.70) | 1.54 (1.34-1.77) | 1.68 (1.41-2.01) | 1.65 (1.43-1.89) | 1.82 (1.52-2.18) | 0.87 (0.73-1.04) | 0.601 | 0.640 | 0.641 | 0.654 | 0.666 | 0.468 |
| sustain6 | DM | 2112 | 197 | 1.59 (1.39-1.82) | 1.72 (1.52-1.94) | 1.75 (1.51-2.04) | 1.82 (1.61-2.05) | 2.37 (2.00-2.81) | 0.90 (0.79-1.02) | 0.632 | 0.658 | 0.652 | 0.674 | 0.712 | 0.471 |
| rewind | DM | 2660 | 366 | 1.65 (1.49-1.81) | 1.70 (1.56-1.85) | 1.86 (1.68-2.06) | 1.83 (1.68-2.00) | 1.93 (1.72-2.16) | 0.97 (0.88-1.07) | 0.636 | 0.672 | 0.670 | 0.691 | 0.671 | 0.495 |
| declare | DM | 2585 | 635 | 2.22 (2.07-2.39) | 2.61 (2.43-2.79) | 3.06 (2.82-3.32) | 2.73 (2.53-2.93) | 3.31 (3.00-3.65) | 0.95 (0.88-1.03) | 0.742 | 0.785 | 0.792 | 0.798 | 0.798 | 0.483 |
| canvas | DM | 970 | 138 | 1.72 (1.47-2.01) | 1.78 (1.55-2.05) | 1.85 (1.54-2.21) | 1.89 (1.62-2.21) | 1.95 (1.56-2.43) | 0.91 (0.78-1.07) | 0.663 | 0.678 | 0.668 | 0.684 | 0.666 | 0.470 |
| tecos | DM | 2743 | 585 | 1.39 (1.28-1.51) | 1.64 (1.52-1.76) | 1.65 (1.51-1.80) | 1.70 (1.57-1.84) | 1.81 (1.65-1.98) | 1.08 (0.99-1.17) | 0.596 | 0.645 | 0.643 | 0.651 | 0.660 | 0.519 |
| carmelina | DM | 1138 | 233 | 1.32 (1.16-1.51) | 1.47 (1.31-1.65) | 1.18 (1.03-1.34) | 1.50 (1.33-1.69) | 1.70 (1.48-1.94) | 0.94 (0.82-1.08) | 0.575 | 0.624 | 0.550 | 0.626 | 0.646 | 0.485 |
| life | HTN | 2474 | 280 | 1.44 (1.28-1.61) | 1.44 (1.31-1.58) | 1.93 (1.72-2.17) | 1.57 (1.41-1.75) | 2.08 (1.80-2.41) | 1.00 (0.89-1.12) | 0.596 | 0.592 | 0.691 | 0.619 | 0.683 | 0.499 |
| allhat | HTN | 16969 | 790 | 1.62 (1.52-1.74) | 1.79 (1.70-1.89) | 1.83 (1.70-1.96) | 1.95 (1.84-2.06) | 1.82 (1.70-1.95) | 0.97 (0.91-1.04) | 0.638 | 0.685 | 0.671 | 0.703 | 0.666 | 0.494 |
| value | HTN | 20379 | 2471 | 1.84 (1.77-1.91) | 1.95 (1.88-2.02) | 2.08 (2.00-2.17) | 2.16 (2.08-2.24) | 2.23 (2.14-2.33) | 0.95 (0.91-0.99) | 0.679 | 0.696 | 0.703 | 0.729 | 0.717 | 0.485 |
| ascot | HTN | 22338 | 804 | 1.64 (1.54-1.76) | 1.61 (1.53-1.71) | 1.67 (1.56-1.78) | 1.85 (1.75-1.96) | 1.80 (1.67-1.94) | 1.10 (1.03-1.18) | 0.645 | 0.653 | 0.651 | 0.686 | 0.656 | 0.527 |
| insight | HTN | 791 | 151 | 1.79 (1.52-2.10) | 1.72 (1.49-1.97) | 1.98 (1.70-2.32) | 2.03 (1.74-2.38) | 1.82 (1.53-2.17) | 0.96 (0.83-1.13) | 0.650 | 0.667 | 0.690 | 0.706 | 0.673 | 0.492 |
| plato | ACS/post-MI | 4726 | 740 | 1.72 (1.60-1.85) | 1.90 (1.79-2.03) | 2.06 (1.92-2.22) | 2.04 (1.91-2.18) | 2.11 (1.95-2.27) | 1.07 (0.99-1.15) | 0.656 | 0.700 | 0.705 | 0.712 | 0.701 | 0.515 |
| valiant | ACS/post-MI | 1204 | 144 | 1.43 (1.22-1.68) | 1.99 (1.74-2.26) | 2.07 (1.73-2.47) | 1.83 (1.59-2.10) | 2.50 (2.13-2.92) | 0.98 (0.83-1.16) | 0.610 | 0.728 | 0.698 | 0.692 | 0.768 | 0.495 |
| ontarget | Other | 12945 | 3058 | 1.63 (1.57-1.68) | 1.65 (1.59-1.70) | 1.69 (1.63-1.76) | 1.87 (1.81-1.93) | 1.78 (1.72-1.85) | 1.01 (0.98-1.05) | 0.643 | 0.648 | 0.651 | 0.684 | 0.663 | 0.503 |
| precision | Other | 4172 | 397 | 1.88 (1.72-2.06) | 2.01 (1.86-2.17) | 2.36 (2.12-2.63) | 2.09 (1.93-2.27) | 2.59 (2.32-2.89) | 1.09 (0.98-1.21) | 0.687 | 0.717 | 0.728 | 0.732 | 0.748 | 0.525 |
| amplify | Other | 1462 | 273 | 1.24 (1.11-1.39) | 1.36 (1.23-1.50) | 1.96 (1.71-2.24) | 1.39 (1.26-1.54) | 1.79 (1.58-2.02) | 0.98 (0.87-1.10) | 0.559 | 0.604 | 0.673 | 0.610 | 0.659 | 0.496 |
| lodestar | Other | 8247 | 1743 | 1.73 (1.65-1.81) | 1.85 (1.77-1.92) | 2.20 (2.09-2.32) | 2.02 (1.93-2.11) | 2.30 (2.18-2.42) | 0.96 (0.92-1.01) | 0.653 | 0.695 | 0.712 | 0.714 | 0.715 | 0.491 |
| prove-it | Other | 1053 | 304 | 1.46 (1.31-1.63) | 1.78 (1.60-1.98) | 1.84 (1.63-2.08) | 1.82 (1.62-2.04) | 1.98 (1.75-2.24) | 0.97 (0.87-1.09) | 0.608 | 0.669 | 0.678 | 0.668 | 0.682 | 0.498 |

### Prognostic, all initiators (unmatched)

| trial | cat | n | events | HR/SD ECG | HR/SD CLIN | HR/SD CLMBR | HR/SD ECG+CLIN | HR/SD PROG | HR/SD shufECG | C ECG | C CLIN | C CLMBR | C ECG+CLIN | C PROG | C shufECG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 18764 | 1194 | 1.44 (1.36-1.52) | 2.12 (2.04-2.21) | 2.39 (2.26-2.53) | 2.18 (2.09-2.27) | 2.12 (2.00-2.24) | 0.91 (0.86-0.97) | 0.603 | 0.746 | 0.735 | 0.749 | 0.706 | 0.475 |
| rocket-af | AF | 7049 | 528 | 1.29 (1.18-1.41) | 2.05 (1.93-2.17) | 2.23 (2.06-2.42) | 2.09 (1.97-2.23) | 2.06 (1.89-2.25) | 1.05 (0.97-1.14) | 0.574 | 0.734 | 0.726 | 0.732 | 0.696 | 0.513 |
| rely | AF | 4166 | 406 | 1.21 (1.10-1.33) | 2.04 (1.90-2.19) | 2.05 (1.87-2.25) | 2.08 (1.92-2.25) | 1.95 (1.76-2.15) | 1.01 (0.91-1.12) | 0.560 | 0.730 | 0.706 | 0.723 | 0.683 | 0.508 |
| east-afnet4 | AF | 16083 | 7387 | 1.62 (1.58-1.66) | 2.12 (2.06-2.17) | 2.20 (2.14-2.26) | 2.17 (2.11-2.23) | 2.20 (2.12-2.27) | 1.00 (0.97-1.02) | 0.644 | 0.716 | 0.712 | 0.723 | 0.726 | 0.499 |
| cabana-v2 | AF | 13131 | 4458 | 1.80 (1.74-1.85) | 1.99 (1.93-2.05) | 2.86 (2.76-2.98) | 2.22 (2.15-2.29) | 2.61 (2.50-2.73) | 1.01 (0.98-1.04) | 0.671 | 0.702 | 0.769 | 0.728 | 0.761 | 0.503 |
| affirm | AF | 17627 | 4874 | 1.57 (1.53-1.62) | 1.86 (1.81-1.91) | 2.45 (2.36-2.53) | 1.99 (1.93-2.04) | 2.25 (2.18-2.32) | 1.00 (0.97-1.03) | 0.635 | 0.681 | 0.731 | 0.700 | 0.734 | 0.501 |
| af-chf | AF | 5550 | 1130 | 1.60 (1.51-1.71) | 1.95 (1.82-2.08) | 1.93 (1.81-2.06) | 2.12 (1.99-2.27) | 1.93 (1.82-2.05) | 1.01 (0.96-1.07) | 0.629 | 0.681 | 0.679 | 0.700 | 0.692 | 0.505 |
| frail-af | AF | 3713 | 285 | 1.18 (1.05-1.32) | 1.70 (1.53-1.90) | 1.56 (1.37-1.77) | 1.65 (1.48-1.84) | 1.77 (1.57-1.99) | 1.15 (1.02-1.29) | 0.551 | 0.658 | 0.627 | 0.648 | 0.659 | 0.538 |
| laaos3 | AF | 2621 | 205 | 1.18 (1.03-1.35) | 1.82 (1.64-2.02) | 1.57 (1.36-1.81) | 1.87 (1.65-2.12) | 1.57 (1.37-1.81) | 1.06 (0.92-1.22) | 0.549 | 0.674 | 0.614 | 0.671 | 0.618 | 0.519 |
| protect-af | AF | 1439 | 221 | 1.36 (1.19-1.56) | 1.76 (1.56-1.99) | 1.70 (1.51-1.92) | 1.81 (1.59-2.05) | 2.01 (1.77-2.29) | 0.88 (0.77-1.01) | 0.589 | 0.679 | 0.652 | 0.672 | 0.699 | 0.465 |
| raft-af | AF | 3003 | 1839 | 1.29 (1.23-1.35) | 1.65 (1.57-1.73) | 1.87 (1.78-1.98) | 1.68 (1.60-1.77) | 1.99 (1.88-2.10) | 1.04 (1.00-1.10) | 0.582 | 0.641 | 0.673 | 0.651 | 0.698 | 0.514 |
| active-w | AF | 3134 | 446 | 1.28 (1.17-1.41) | 1.73 (1.59-1.87) | 1.73 (1.58-1.90) | 1.74 (1.60-1.89) | 1.89 (1.72-2.07) | 0.96 (0.88-1.06) | 0.574 | 0.675 | 0.653 | 0.668 | 0.677 | 0.494 |
| comet | HF | 6378 | 1573 | 1.43 (1.36-1.51) | 1.84 (1.74-1.93) | 1.91 (1.81-2.01) | 1.86 (1.76-1.96) | 2.06 (1.95-2.17) | 0.98 (0.93-1.03) | 0.604 | 0.672 | 0.680 | 0.677 | 0.708 | 0.495 |
| paradigm-hf-seq | HF | 5126 | 2460 | 1.39 (1.33-1.45) | 1.58 (1.52-1.64) | 1.88 (1.80-1.97) | 1.67 (1.60-1.74) | 1.88 (1.80-1.98) | 1.02 (0.98-1.06) | 0.597 | 0.636 | 0.671 | 0.648 | 0.676 | 0.504 |
| transform-hf | HF | 15650 | 2798 | 1.53 (1.47-1.59) | 1.59 (1.53-1.66) | 1.98 (1.90-2.06) | 1.82 (1.75-1.89) | 1.93 (1.86-2.00) | 0.98 (0.94-1.01) | 0.615 | 0.623 | 0.682 | 0.659 | 0.679 | 0.493 |
| elite-ii | HF | 3222 | 549 | 1.39 (1.28-1.52) | 1.59 (1.46-1.72) | 1.72 (1.57-1.88) | 1.68 (1.54-1.84) | 1.91 (1.75-2.09) | 0.97 (0.89-1.05) | 0.597 | 0.630 | 0.649 | 0.644 | 0.672 | 0.493 |
| emperor-preserved-v2 | HF | 2407 | 1125 | 1.26 (1.18-1.33) | 1.51 (1.42-1.60) | 1.76 (1.65-1.89) | 1.54 (1.45-1.64) | 1.93 (1.81-2.05) | 0.97 (0.92-1.03) | 0.567 | 0.625 | 0.655 | 0.629 | 0.681 | 0.494 |
| empa-reg | DM | 5635 | 949 | 1.47 (1.38-1.56) | 1.79 (1.69-1.90) | 1.86 (1.74-1.99) | 1.79 (1.69-1.90) | 1.97 (1.83-2.11) | 0.99 (0.93-1.05) | 0.618 | 0.677 | 0.672 | 0.677 | 0.682 | 0.497 |
| carolina | DM | 1792 | 355 | 1.42 (1.28-1.56) | 1.75 (1.59-1.93) | 1.63 (1.48-1.80) | 1.73 (1.57-1.91) | 1.82 (1.63-2.04) | 1.03 (0.93-1.14) | 0.609 | 0.657 | 0.632 | 0.663 | 0.655 | 0.500 |
| leader | DM | 3778 | 794 | 1.43 (1.34-1.53) | 1.64 (1.54-1.74) | 1.68 (1.56-1.81) | 1.68 (1.58-1.79) | 1.87 (1.73-2.03) | 0.96 (0.89-1.03) | 0.602 | 0.654 | 0.648 | 0.658 | 0.672 | 0.493 |
| sustain6 | DM | 3710 | 410 | 1.58 (1.44-1.73) | 1.74 (1.60-1.89) | 1.78 (1.61-1.97) | 1.83 (1.68-2.00) | 2.16 (1.93-2.41) | 0.93 (0.85-1.02) | 0.635 | 0.671 | 0.662 | 0.680 | 0.705 | 0.480 |
| rewind | DM | 6040 | 1158 | 1.62 (1.53-1.71) | 1.79 (1.71-1.89) | 1.88 (1.77-1.99) | 1.85 (1.76-1.94) | 1.97 (1.85-2.11) | 1.00 (0.94-1.05) | 0.643 | 0.687 | 0.676 | 0.697 | 0.684 | 0.503 |
| declare | DM | 6959 | 1811 | 2.18 (2.09-2.28) | 2.65 (2.53-2.76) | 3.06 (2.91-3.22) | 2.75 (2.63-2.89) | 3.28 (3.10-3.48) | 0.99 (0.95-1.04) | 0.730 | 0.782 | 0.786 | 0.794 | 0.787 | 0.500 |
| canvas | DM | 6032 | 928 | 1.66 (1.56-1.76) | 1.89 (1.79-1.99) | 1.91 (1.78-2.04) | 1.92 (1.82-2.03) | 2.13 (1.98-2.30) | 0.93 (0.87-0.99) | 0.652 | 0.698 | 0.679 | 0.706 | 0.695 | 0.475 |
| tecos | DM | 2922 | 630 | 1.39 (1.28-1.50) | 1.60 (1.50-1.72) | 1.62 (1.49-1.76) | 1.68 (1.56-1.81) | 1.78 (1.63-1.95) | 1.05 (0.97-1.14) | 0.595 | 0.642 | 0.640 | 0.649 | 0.658 | 0.513 |
| carmelina | DM | 1546 | 313 | 1.29 (1.15-1.45) | 1.50 (1.36-1.65) | 1.17 (1.05-1.31) | 1.50 (1.36-1.66) | 1.66 (1.47-1.86) | 0.93 (0.83-1.04) | 0.566 | 0.630 | 0.547 | 0.625 | 0.637 | 0.481 |
| life | HTN | 3126 | 403 | 1.42 (1.29-1.56) | 1.52 (1.40-1.64) | 1.91 (1.74-2.11) | 1.61 (1.47-1.76) | 2.11 (1.88-2.37) | 0.98 (0.89-1.08) | 0.598 | 0.619 | 0.689 | 0.637 | 0.694 | 0.495 |
| allhat | HTN | 26559 | 1333 | 1.64 (1.56-1.73) | 1.85 (1.77-1.93) | 1.87 (1.77-1.97) | 2.00 (1.91-2.10) | 1.80 (1.71-1.90) | 0.98 (0.92-1.03) | 0.643 | 0.692 | 0.675 | 0.711 | 0.663 | 0.495 |
| value | HTN | 26616 | 3652 | 1.79 (1.74-1.85) | 1.96 (1.90-2.01) | 2.11 (2.04-2.18) | 2.15 (2.08-2.21) | 2.20 (2.13-2.28) | 0.96 (0.93-1.00) | 0.672 | 0.700 | 0.706 | 0.728 | 0.714 | 0.490 |
| ascot | HTN | 25988 | 905 | 1.60 (1.51-1.71) | 1.61 (1.53-1.70) | 1.67 (1.57-1.78) | 1.82 (1.72-1.93) | 1.82 (1.69-1.95) | 1.07 (1.01-1.14) | 0.635 | 0.650 | 0.650 | 0.679 | 0.658 | 0.521 |
| insight | HTN | 8835 | 1211 | 1.68 (1.59-1.77) | 1.69 (1.61-1.77) | 2.04 (1.93-2.16) | 1.93 (1.84-2.03) | 2.11 (1.98-2.24) | 0.97 (0.91-1.02) | 0.645 | 0.657 | 0.697 | 0.697 | 0.691 | 0.491 |
| plato | ACS/post-MI | 6752 | 1063 | 1.77 (1.66-1.88) | 1.86 (1.77-1.96) | 2.00 (1.88-2.12) | 2.03 (1.92-2.15) | 2.12 (1.99-2.26) | 1.05 (0.99-1.11) | 0.665 | 0.697 | 0.698 | 0.713 | 0.703 | 0.513 |
| valiant | ACS/post-MI | 2096 | 253 | 1.55 (1.38-1.74) | 1.92 (1.73-2.13) | 2.19 (1.92-2.50) | 1.83 (1.65-2.04) | 2.65 (2.33-3.02) | 1.07 (0.95-1.21) | 0.630 | 0.708 | 0.711 | 0.693 | 0.770 | 0.521 |
| ontarget | Other | 14823 | 3599 | 1.64 (1.59-1.69) | 1.66 (1.61-1.71) | 1.71 (1.65-1.77) | 1.87 (1.82-1.93) | 1.81 (1.74-1.87) | 1.00 (0.97-1.04) | 0.644 | 0.649 | 0.653 | 0.686 | 0.666 | 0.500 |
| precision | Other | 5302 | 511 | 1.85 (1.71-2.00) | 2.01 (1.87-2.15) | 2.28 (2.08-2.51) | 2.09 (1.95-2.25) | 2.55 (2.32-2.81) | 1.10 (1.00-1.20) | 0.680 | 0.718 | 0.724 | 0.729 | 0.746 | 0.527 |
| amplify | Other | 5080 | 980 | 1.24 (1.17-1.32) | 1.48 (1.40-1.56) | 1.82 (1.70-1.95) | 1.48 (1.40-1.57) | 1.89 (1.78-2.02) | 0.97 (0.91-1.03) | 0.562 | 0.622 | 0.659 | 0.621 | 0.676 | 0.493 |
| lodestar | Other | 22271 | 5103 | 1.71 (1.66-1.76) | 1.86 (1.81-1.91) | 2.25 (2.18-2.32) | 2.02 (1.97-2.08) | 2.26 (2.19-2.33) | 0.99 (0.96-1.02) | 0.651 | 0.691 | 0.716 | 0.708 | 0.715 | 0.497 |
| prove-it | Other | 4378 | 1116 | 1.63 (1.53-1.73) | 1.83 (1.73-1.93) | 2.05 (1.92-2.19) | 1.93 (1.83-2.04) | 2.17 (2.03-2.32) | 1.02 (0.96-1.08) | 0.638 | 0.690 | 0.699 | 0.696 | 0.710 | 0.507 |

### Prognostic, P1-matched

| trial | cat | n | events | HR/SD ECG | HR/SD CLIN | HR/SD CLMBR | HR/SD ECG+CLIN | HR/SD PROG | HR/SD shufECG | C ECG | C CLIN | C CLMBR | C ECG+CLIN | C PROG | C shufECG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 5562 | 437 | 1.38 (1.26-1.51) | 2.19 (2.04-2.35) | 2.44 (2.21-2.69) | 2.24 (2.08-2.41) | 2.04 (1.86-2.25) | 0.92 (0.83-1.01) | 0.592 | 0.746 | 0.738 | 0.748 | 0.695 | 0.476 |
| rocket-af | AF | 5209 | 392 | 1.28 (1.16-1.43) | 2.05 (1.91-2.19) | 2.24 (2.03-2.47) | 2.09 (1.94-2.25) | 2.02 (1.81-2.25) | 1.04 (0.94-1.15) | 0.571 | 0.725 | 0.725 | 0.723 | 0.690 | 0.508 |
| rely | AF | 1404 | 117 | 1.27 (1.05-1.53) | 1.93 (1.69-2.20) | 2.01 (1.68-2.41) | 1.97 (1.70-2.28) | 1.89 (1.59-2.26) | 0.97 (0.82-1.16) | 0.563 | 0.719 | 0.700 | 0.707 | 0.680 | 0.498 |
| east-afnet4 | AF | 6913 | 3103 | 1.67 (1.61-1.74) | 2.12 (2.04-2.20) | 2.25 (2.15-2.35) | 2.20 (2.11-2.28) | 2.25 (2.14-2.36) | 1.01 (0.98-1.05) | 0.648 | 0.716 | 0.717 | 0.724 | 0.730 | 0.504 |
| cabana-v2 | AF | 3146 | 615 | 2.16 (2.00-2.33) | 2.19 (2.05-2.35) | 3.63 (3.30-4.00) | 2.56 (2.38-2.76) | 3.76 (3.36-4.21) | 1.03 (0.96-1.11) | 0.723 | 0.736 | 0.827 | 0.778 | 0.814 | 0.508 |
| affirm | AF | 8198 | 2242 | 1.66 (1.60-1.73) | 1.88 (1.81-1.96) | 2.79 (2.63-2.95) | 2.07 (1.98-2.16) | 2.41 (2.30-2.53) | 1.02 (0.97-1.06) | 0.651 | 0.682 | 0.751 | 0.708 | 0.749 | 0.506 |
| af-chf | AF | 2537 | 527 | 1.64 (1.49-1.80) | 1.98 (1.80-2.19) | 2.02 (1.82-2.23) | 2.16 (1.96-2.39) | 1.97 (1.80-2.16) | 1.02 (0.94-1.11) | 0.630 | 0.683 | 0.685 | 0.697 | 0.699 | 0.504 |
| frail-af | AF | 1594 | 119 | 1.15 (0.96-1.38) | 1.52 (1.28-1.80) | 1.45 (1.16-1.81) | 1.48 (1.25-1.75) | 1.82 (1.49-2.21) | 1.15 (0.96-1.37) | 0.544 | 0.621 | 0.597 | 0.615 | 0.661 | 0.537 |
| laaos3 | AF | 1022 | 67 | 1.16 (0.92-1.45) | 1.86 (1.56-2.21) | 1.46 (1.12-1.89) | 1.91 (1.53-2.38) | 1.52 (1.20-1.92) | 0.80 (0.63-1.02) | 0.530 | 0.694 | 0.595 | 0.664 | 0.609 | 0.446 |
| protect-af | AF | 626 | 89 | 1.34 (1.06-1.69) | 1.70 (1.41-2.05) | 1.50 (1.26-1.78) | 1.79 (1.45-2.20) | 1.92 (1.56-2.36) | 0.82 (0.65-1.03) | 0.577 | 0.676 | 0.630 | 0.665 | 0.690 | 0.444 |
| raft-af | AF | 1228 | 657 | 1.44 (1.32-1.56) | 1.76 (1.61-1.92) | 2.03 (1.86-2.22) | 1.83 (1.68-1.99) | 2.28 (2.07-2.51) | 1.03 (0.95-1.12) | 0.603 | 0.662 | 0.693 | 0.670 | 0.720 | 0.514 |
| active-w | AF | 1788 | 263 | 1.24 (1.10-1.40) | 1.78 (1.60-1.98) | 1.73 (1.53-1.96) | 1.79 (1.60-2.01) | 1.92 (1.71-2.17) | 0.97 (0.86-1.09) | 0.570 | 0.683 | 0.654 | 0.679 | 0.685 | 0.495 |
| comet | HF | 5263 | 1398 | 1.40 (1.32-1.47) | 1.80 (1.70-1.90) | 1.85 (1.75-1.96) | 1.81 (1.71-1.91) | 2.01 (1.90-2.12) | 0.99 (0.94-1.04) | 0.595 | 0.666 | 0.674 | 0.669 | 0.703 | 0.499 |
| paradigm-hf-seq | HF | 2443 | 1221 | 1.35 (1.28-1.43) | 1.59 (1.50-1.68) | 1.83 (1.71-1.95) | 1.65 (1.56-1.75) | 1.84 (1.73-1.97) | 1.02 (0.97-1.08) | 0.585 | 0.632 | 0.661 | 0.641 | 0.670 | 0.506 |
| transform-hf | HF | 1392 | 243 | 1.55 (1.37-1.76) | 1.57 (1.38-1.80) | 2.07 (1.81-2.36) | 1.81 (1.59-2.06) | 2.04 (1.79-2.32) | 1.00 (0.88-1.14) | 0.614 | 0.629 | 0.689 | 0.661 | 0.690 | 0.507 |
| elite-ii | HF | 2152 | 346 | 1.41 (1.27-1.56) | 1.59 (1.43-1.77) | 1.63 (1.45-1.82) | 1.70 (1.52-1.90) | 1.88 (1.69-2.11) | 0.98 (0.88-1.09) | 0.601 | 0.628 | 0.634 | 0.645 | 0.666 | 0.493 |
| emperor-preserved-v2 | HF | 1060 | 504 | 1.26 (1.15-1.37) | 1.52 (1.39-1.66) | 1.72 (1.55-1.91) | 1.53 (1.40-1.68) | 1.99 (1.80-2.19) | 0.96 (0.88-1.06) | 0.571 | 0.626 | 0.652 | 0.629 | 0.690 | 0.493 |
| empa-reg | DM | 3340 | 594 | 1.47 (1.36-1.58) | 1.77 (1.65-1.91) | 1.88 (1.73-2.05) | 1.77 (1.65-1.91) | 1.98 (1.81-2.17) | 0.98 (0.91-1.06) | 0.618 | 0.673 | 0.672 | 0.675 | 0.680 | 0.493 |
| carolina | DM | 1537 | 312 | 1.43 (1.29-1.58) | 1.76 (1.59-1.95) | 1.68 (1.52-1.86) | 1.76 (1.59-1.95) | 1.89 (1.69-2.12) | 1.02 (0.91-1.13) | 0.613 | 0.659 | 0.641 | 0.669 | 0.666 | 0.498 |
| leader | DM | 906 | 147 | 1.51 (1.29-1.75) | 1.60 (1.40-1.84) | 1.72 (1.43-2.06) | 1.77 (1.54-2.04) | 1.79 (1.47-2.18) | 0.90 (0.76-1.06) | 0.621 | 0.646 | 0.652 | 0.670 | 0.649 | 0.471 |
| sustain6 | DM | 2127 | 215 | 1.57 (1.38-1.79) | 1.67 (1.48-1.87) | 1.80 (1.55-2.10) | 1.80 (1.60-2.03) | 2.12 (1.82-2.47) | 0.93 (0.82-1.06) | 0.629 | 0.648 | 0.653 | 0.672 | 0.694 | 0.482 |
| rewind | DM | 2661 | 350 | 1.69 (1.53-1.86) | 1.68 (1.54-1.84) | 1.79 (1.61-2.00) | 1.84 (1.68-2.01) | 1.86 (1.65-2.09) | 0.97 (0.88-1.08) | 0.651 | 0.661 | 0.657 | 0.693 | 0.668 | 0.498 |
| declare | DM | 2634 | 589 | 2.25 (2.08-2.43) | 2.84 (2.63-3.06) | 3.25 (2.97-3.55) | 2.94 (2.71-3.19) | 3.32 (3.02-3.65) | 0.99 (0.91-1.08) | 0.740 | 0.798 | 0.801 | 0.806 | 0.802 | 0.496 |
| canvas | DM | 970 | 145 | 1.50 (1.30-1.73) | 1.72 (1.50-1.97) | 1.68 (1.39-2.03) | 1.72 (1.49-1.99) | 1.65 (1.34-2.04) | 0.89 (0.74-1.05) | 0.623 | 0.660 | 0.633 | 0.650 | 0.627 | 0.458 |
| tecos | DM | 2772 | 594 | 1.39 (1.28-1.51) | 1.60 (1.49-1.72) | 1.61 (1.47-1.75) | 1.68 (1.55-1.81) | 1.79 (1.64-1.96) | 1.04 (0.96-1.13) | 0.597 | 0.641 | 0.637 | 0.648 | 0.660 | 0.510 |
| carmelina | DM | 1188 | 238 | 1.29 (1.13-1.47) | 1.53 (1.36-1.72) | 1.18 (1.04-1.35) | 1.50 (1.34-1.69) | 1.72 (1.50-1.97) | 0.94 (0.83-1.07) | 0.570 | 0.632 | 0.549 | 0.627 | 0.645 | 0.484 |
| life | HTN | 2473 | 310 | 1.44 (1.30-1.60) | 1.56 (1.43-1.70) | 1.96 (1.76-2.19) | 1.66 (1.50-1.84) | 2.16 (1.89-2.48) | 0.99 (0.89-1.11) | 0.605 | 0.626 | 0.694 | 0.645 | 0.696 | 0.495 |
| allhat | HTN | 16969 | 841 | 1.63 (1.53-1.75) | 1.82 (1.72-1.92) | 1.87 (1.75-2.00) | 1.95 (1.85-2.07) | 1.87 (1.75-2.00) | 0.98 (0.91-1.05) | 0.641 | 0.689 | 0.680 | 0.708 | 0.669 | 0.491 |
| value | HTN | 20382 | 2539 | 1.80 (1.74-1.87) | 1.95 (1.88-2.01) | 2.10 (2.01-2.18) | 2.15 (2.07-2.23) | 2.24 (2.15-2.33) | 0.95 (0.91-0.99) | 0.674 | 0.698 | 0.705 | 0.728 | 0.716 | 0.486 |
| ascot | HTN | 25535 | 899 | 1.60 (1.50-1.70) | 1.61 (1.53-1.69) | 1.66 (1.56-1.77) | 1.82 (1.72-1.92) | 1.82 (1.69-1.95) | 1.08 (1.01-1.15) | 0.635 | 0.649 | 0.649 | 0.678 | 0.659 | 0.522 |
| insight | HTN | 791 | 151 | 1.88 (1.60-2.20) | 1.72 (1.50-1.97) | 2.03 (1.75-2.36) | 2.13 (1.83-2.47) | 1.85 (1.56-2.20) | 0.95 (0.82-1.11) | 0.670 | 0.672 | 0.695 | 0.727 | 0.669 | 0.487 |
| plato | ACS/post-MI | 5065 | 838 | 1.68 (1.57-1.80) | 1.82 (1.72-1.93) | 1.94 (1.81-2.07) | 1.96 (1.84-2.09) | 2.06 (1.92-2.21) | 1.05 (0.98-1.12) | 0.651 | 0.691 | 0.692 | 0.704 | 0.699 | 0.511 |
| valiant | ACS/post-MI | 1190 | 139 | 1.57 (1.35-1.83) | 2.04 (1.77-2.35) | 2.07 (1.74-2.46) | 1.95 (1.68-2.26) | 2.70 (2.28-3.20) | 1.00 (0.84-1.18) | 0.632 | 0.719 | 0.693 | 0.697 | 0.775 | 0.503 |
| ontarget | Other | 12720 | 3060 | 1.65 (1.59-1.70) | 1.64 (1.59-1.70) | 1.71 (1.65-1.77) | 1.87 (1.81-1.94) | 1.80 (1.73-1.87) | 1.01 (0.97-1.04) | 0.644 | 0.648 | 0.653 | 0.686 | 0.664 | 0.501 |
| precision | Other | 4301 | 429 | 1.84 (1.69-2.01) | 2.02 (1.87-2.18) | 2.32 (2.09-2.58) | 2.09 (1.93-2.27) | 2.60 (2.33-2.90) | 1.07 (0.97-1.19) | 0.678 | 0.720 | 0.726 | 0.730 | 0.746 | 0.520 |
| amplify | Other | 1366 | 246 | 1.24 (1.10-1.41) | 1.38 (1.24-1.54) | 1.95 (1.68-2.27) | 1.39 (1.25-1.55) | 1.85 (1.62-2.11) | 0.91 (0.80-1.03) | 0.565 | 0.602 | 0.675 | 0.607 | 0.664 | 0.478 |
| lodestar | Other | 7758 | 1729 | 1.81 (1.72-1.90) | 1.94 (1.86-2.03) | 2.31 (2.19-2.43) | 2.12 (2.03-2.22) | 2.28 (2.16-2.40) | 0.99 (0.95-1.04) | 0.667 | 0.709 | 0.725 | 0.726 | 0.722 | 0.497 |
| prove-it | Other | 1061 | 316 | 1.52 (1.36-1.69) | 1.74 (1.56-1.93) | 1.88 (1.67-2.11) | 1.82 (1.62-2.03) | 2.04 (1.80-2.30) | 1.02 (0.90-1.14) | 0.621 | 0.673 | 0.678 | 0.677 | 0.698 | 0.506 |

### Prognostic, clinical-PS matched

| trial | cat | n | events | HR/SD ECG | HR/SD CLIN | HR/SD CLMBR | HR/SD ECG+CLIN | HR/SD PROG | HR/SD shufECG | C ECG | C CLIN | C CLMBR | C ECG+CLIN | C PROG | C shufECG |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 5595 | 456 | 1.33 (1.22-1.45) | 2.16 (2.02-2.32) | 2.33 (2.12-2.56) | 2.19 (2.03-2.35) | 2.02 (1.82-2.23) | 0.92 (0.83-1.01) | 0.583 | 0.737 | 0.728 | 0.737 | 0.684 | 0.473 |
| rocket-af | AF | 4097 | 309 | 1.26 (1.12-1.42) | 1.88 (1.74-2.03) | 2.15 (1.92-2.40) | 1.94 (1.80-2.11) | 1.78 (1.58-2.00) | 1.08 (0.97-1.19) | 0.569 | 0.702 | 0.708 | 0.713 | 0.662 | 0.517 |
| rely | AF | 1397 | 122 | 1.30 (1.07-1.57) | 1.91 (1.69-2.15) | 2.19 (1.84-2.59) | 2.01 (1.75-2.30) | 2.17 (1.80-2.61) | 1.06 (0.89-1.27) | 0.575 | 0.706 | 0.725 | 0.706 | 0.714 | 0.518 |
| east-afnet4 | AF | 6914 | 3241 | 1.62 (1.57-1.68) | 2.11 (2.03-2.19) | 2.22 (2.13-2.31) | 2.17 (2.09-2.26) | 2.20 (2.09-2.31) | 1.01 (0.98-1.05) | 0.641 | 0.709 | 0.709 | 0.717 | 0.724 | 0.503 |
| cabana-v2 | AF | 3122 | 399 | 1.92 (1.75-2.11) | 2.02 (1.86-2.19) | 3.08 (2.77-3.41) | 2.26 (2.08-2.46) | 3.16 (2.76-3.61) | 1.03 (0.94-1.13) | 0.693 | 0.721 | 0.797 | 0.749 | 0.766 | 0.505 |
| affirm | AF | 8174 | 2436 | 1.60 (1.53-1.66) | 1.81 (1.74-1.88) | 2.57 (2.44-2.71) | 1.97 (1.90-2.06) | 2.23 (2.13-2.33) | 1.01 (0.97-1.05) | 0.637 | 0.669 | 0.736 | 0.693 | 0.732 | 0.506 |
| af-chf | AF | 2520 | 560 | 1.64 (1.49-1.79) | 1.87 (1.71-2.06) | 1.91 (1.74-2.10) | 2.08 (1.89-2.29) | 1.90 (1.75-2.07) | 1.00 (0.92-1.08) | 0.631 | 0.673 | 0.682 | 0.693 | 0.691 | 0.497 |
| frail-af | AF | 1594 | 130 | 1.20 (1.03-1.41) | 1.54 (1.31-1.82) | 1.37 (1.13-1.66) | 1.53 (1.30-1.80) | 1.64 (1.39-1.93) | 1.09 (0.93-1.28) | 0.560 | 0.636 | 0.595 | 0.629 | 0.650 | 0.520 |
| laaos3 | AF | 1008 | 72 | 1.05 (0.84-1.31) | 1.66 (1.39-1.99) | 1.70 (1.28-2.25) | 1.66 (1.32-2.09) | 1.37 (1.09-1.73) | 0.84 (0.67-1.06) | 0.498 | 0.634 | 0.619 | 0.610 | 0.587 | 0.457 |
| protect-af | AF | 586 | 77 | 1.48 (1.21-1.81) | 1.63 (1.33-2.00) | 1.74 (1.42-2.13) | 1.77 (1.45-2.17) | 2.13 (1.68-2.69) | 0.65 (0.50-0.84) | 0.617 | 0.656 | 0.658 | 0.674 | 0.697 | 0.386 |
| raft-af | AF | 1052 | 528 | 1.39 (1.28-1.52) | 1.67 (1.52-1.83) | 1.98 (1.80-2.19) | 1.72 (1.57-1.90) | 2.11 (1.91-2.34) | 1.02 (0.93-1.11) | 0.598 | 0.649 | 0.690 | 0.660 | 0.709 | 0.516 |
| active-w | AF | 1558 | 249 | 1.28 (1.14-1.45) | 1.66 (1.49-1.85) | 1.69 (1.50-1.91) | 1.77 (1.57-1.99) | 1.86 (1.65-2.09) | 0.98 (0.87-1.11) | 0.571 | 0.658 | 0.648 | 0.664 | 0.679 | 0.503 |
| comet | HF | 4196 | 1058 | 1.36 (1.28-1.45) | 1.79 (1.67-1.91) | 1.85 (1.74-1.97) | 1.82 (1.70-1.94) | 2.08 (1.94-2.22) | 0.98 (0.92-1.05) | 0.590 | 0.662 | 0.674 | 0.668 | 0.710 | 0.496 |
| paradigm-hf-seq | HF | 2364 | 1235 | 1.32 (1.24-1.40) | 1.51 (1.43-1.60) | 1.79 (1.68-1.92) | 1.58 (1.49-1.67) | 1.74 (1.63-1.86) | 1.02 (0.96-1.07) | 0.580 | 0.622 | 0.656 | 0.631 | 0.659 | 0.500 |
| transform-hf | HF | 1392 | 236 | 1.67 (1.48-1.90) | 1.65 (1.41-1.94) | 2.03 (1.76-2.34) | 1.96 (1.70-2.24) | 2.07 (1.83-2.34) | 0.87 (0.77-0.98) | 0.636 | 0.632 | 0.689 | 0.674 | 0.695 | 0.461 |
| elite-ii | HF | 2324 | 377 | 1.39 (1.25-1.54) | 1.63 (1.47-1.81) | 1.71 (1.53-1.92) | 1.71 (1.54-1.91) | 1.88 (1.69-2.10) | 0.98 (0.89-1.08) | 0.595 | 0.632 | 0.648 | 0.646 | 0.666 | 0.501 |
| emperor-preserved-v2 | HF | 963 | 459 | 1.29 (1.18-1.41) | 1.46 (1.33-1.60) | 1.77 (1.59-1.96) | 1.51 (1.38-1.65) | 1.92 (1.74-2.13) | 0.97 (0.88-1.06) | 0.575 | 0.618 | 0.662 | 0.631 | 0.683 | 0.496 |
| empa-reg | DM | 2975 | 523 | 1.50 (1.38-1.62) | 1.73 (1.61-1.87) | 1.85 (1.68-2.02) | 1.74 (1.61-1.88) | 1.89 (1.72-2.08) | 0.98 (0.90-1.07) | 0.627 | 0.665 | 0.666 | 0.669 | 0.667 | 0.497 |
| carolina | DM | 1473 | 294 | 1.39 (1.25-1.56) | 1.75 (1.57-1.95) | 1.58 (1.42-1.76) | 1.71 (1.53-1.91) | 1.78 (1.58-2.00) | 1.03 (0.92-1.15) | 0.608 | 0.653 | 0.622 | 0.654 | 0.650 | 0.498 |
| leader | DM | 900 | 144 | 1.57 (1.34-1.83) | 1.49 (1.28-1.73) | 1.68 (1.40-2.03) | 1.69 (1.45-1.98) | 1.78 (1.47-2.17) | 0.89 (0.75-1.06) | 0.629 | 0.616 | 0.640 | 0.646 | 0.651 | 0.471 |
| sustain6 | DM | 1776 | 172 | 1.55 (1.35-1.79) | 1.72 (1.51-1.97) | 1.73 (1.47-2.03) | 1.83 (1.60-2.10) | 2.23 (1.86-2.66) | 0.91 (0.79-1.05) | 0.632 | 0.661 | 0.647 | 0.678 | 0.710 | 0.479 |
| rewind | DM | 2600 | 353 | 1.74 (1.58-1.91) | 1.78 (1.63-1.94) | 1.90 (1.71-2.11) | 1.95 (1.78-2.14) | 2.14 (1.91-2.41) | 0.96 (0.87-1.07) | 0.659 | 0.686 | 0.680 | 0.707 | 0.697 | 0.491 |
| declare | DM | 2410 | 588 | 2.17 (2.02-2.33) | 2.62 (2.43-2.82) | 3.17 (2.90-3.46) | 2.71 (2.50-2.94) | 3.46 (3.12-3.84) | 1.00 (0.93-1.09) | 0.739 | 0.789 | 0.797 | 0.802 | 0.801 | 0.503 |
| canvas | DM | 964 | 136 | 1.58 (1.36-1.84) | 1.70 (1.48-1.95) | 1.65 (1.37-1.99) | 1.86 (1.60-2.17) | 1.80 (1.44-2.26) | 0.81 (0.69-0.95) | 0.642 | 0.648 | 0.633 | 0.662 | 0.631 | 0.439 |
| tecos | DM | 2675 | 578 | 1.40 (1.29-1.53) | 1.61 (1.49-1.73) | 1.59 (1.46-1.74) | 1.70 (1.57-1.83) | 1.78 (1.62-1.95) | 1.05 (0.97-1.14) | 0.597 | 0.638 | 0.634 | 0.649 | 0.657 | 0.512 |
| carmelina | DM | 1108 | 216 | 1.26 (1.09-1.46) | 1.43 (1.27-1.61) | 1.11 (0.97-1.27) | 1.43 (1.26-1.62) | 1.55 (1.35-1.78) | 0.99 (0.86-1.14) | 0.558 | 0.612 | 0.533 | 0.612 | 0.620 | 0.505 |
| life | HTN | 2471 | 277 | 1.52 (1.36-1.71) | 1.58 (1.44-1.73) | 1.96 (1.75-2.20) | 1.73 (1.56-1.93) | 2.02 (1.77-2.31) | 0.94 (0.83-1.05) | 0.618 | 0.621 | 0.693 | 0.654 | 0.685 | 0.485 |
| allhat | HTN | 16963 | 806 | 1.61 (1.50-1.72) | 1.81 (1.71-1.91) | 1.82 (1.70-1.95) | 1.95 (1.84-2.06) | 1.82 (1.70-1.95) | 0.95 (0.89-1.02) | 0.635 | 0.684 | 0.672 | 0.703 | 0.665 | 0.488 |
| value | HTN | 20365 | 2395 | 1.88 (1.81-1.95) | 1.96 (1.89-2.04) | 2.11 (2.02-2.20) | 2.19 (2.10-2.27) | 2.23 (2.14-2.33) | 0.96 (0.92-0.99) | 0.685 | 0.700 | 0.706 | 0.733 | 0.716 | 0.487 |
| ascot | HTN | 20432 | 734 | 1.63 (1.52-1.75) | 1.59 (1.51-1.69) | 1.68 (1.57-1.80) | 1.82 (1.71-1.94) | 1.86 (1.72-2.01) | 1.07 (1.00-1.15) | 0.639 | 0.647 | 0.653 | 0.680 | 0.664 | 0.518 |
| insight | HTN | 786 | 158 | 1.82 (1.58-2.09) | 1.52 (1.34-1.74) | 1.90 (1.64-2.21) | 1.87 (1.65-2.13) | 1.81 (1.54-2.13) | 1.05 (0.89-1.24) | 0.670 | 0.622 | 0.675 | 0.687 | 0.662 | 0.514 |
| plato | ACS/post-MI | 4037 | 679 | 1.75 (1.62-1.89) | 1.89 (1.76-2.02) | 2.03 (1.88-2.19) | 2.05 (1.91-2.19) | 2.18 (2.01-2.37) | 1.07 (0.99-1.16) | 0.658 | 0.696 | 0.701 | 0.710 | 0.707 | 0.516 |
| valiant | ACS/post-MI | 1200 | 143 | 1.45 (1.24-1.71) | 1.96 (1.70-2.27) | 2.12 (1.77-2.55) | 1.88 (1.63-2.17) | 2.54 (2.15-3.00) | 1.03 (0.87-1.22) | 0.611 | 0.715 | 0.703 | 0.694 | 0.764 | 0.511 |
| ontarget | Other | 12328 | 2900 | 1.65 (1.59-1.71) | 1.63 (1.57-1.68) | 1.70 (1.64-1.76) | 1.86 (1.80-1.92) | 1.77 (1.70-1.84) | 1.00 (0.97-1.04) | 0.647 | 0.644 | 0.652 | 0.685 | 0.660 | 0.500 |
| precision | Other | 3970 | 368 | 1.85 (1.69-2.03) | 2.00 (1.84-2.16) | 2.30 (2.06-2.58) | 2.07 (1.90-2.25) | 2.61 (2.33-2.93) | 1.09 (0.98-1.22) | 0.684 | 0.717 | 0.726 | 0.730 | 0.750 | 0.525 |
| amplify | Other | 1454 | 266 | 1.22 (1.08-1.37) | 1.41 (1.27-1.56) | 1.94 (1.68-2.24) | 1.42 (1.28-1.58) | 1.83 (1.63-2.06) | 0.94 (0.83-1.07) | 0.560 | 0.614 | 0.667 | 0.612 | 0.665 | 0.488 |
| lodestar | Other | 8613 | 1782 | 1.75 (1.67-1.83) | 1.86 (1.78-1.94) | 2.32 (2.20-2.44) | 2.03 (1.93-2.12) | 2.32 (2.20-2.44) | 0.99 (0.94-1.03) | 0.657 | 0.695 | 0.724 | 0.714 | 0.724 | 0.495 |
| prove-it | Other | 1043 | 304 | 1.47 (1.32-1.64) | 1.79 (1.61-2.00) | 1.80 (1.59-2.04) | 1.85 (1.65-2.08) | 2.06 (1.81-2.33) | 0.97 (0.86-1.10) | 0.611 | 0.674 | 0.665 | 0.673 | 0.694 | 0.496 |

### Enrichment, m_sparse

| trial | cat | rct_hr | p_full | N_full | ECG top25 p | ECG red25 % | ECG red50 % | CLIN top25 p | CLIN red25 % | CLIN red50 % | CLMBR top25 p | CLMBR red25 % | CLMBR red50 % | ECG+CLIN top25 p | ECG+CLIN red25 % | ECG+CLIN red50 % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 0.790 | 0.087 | 6,513 | 0.120 | 28 (20, 37) | 19 | 0.210 | 59 (56, 62) | 38 | 0.202 | 57 (54, 60) | 38 | 0.212 | 59 (56, 62) | 39 |
| rocket-af | AF | 0.880 | 0.081 | 23,666 | 0.116 | 30 (19, 40) | 18 | 0.187 | 57 (52, 60) | 32 | 0.177 | 54 (50, 58) | 37 | 0.191 | 57 (52, 60) | 34 |
| rely | AF | 0.660 | 0.086 | 2,113 | 0.101 | 15 (-13, 34) | 11 | 0.198 | 56 (48, 62) | 35 | 0.201 | 57 (50, 63) | 33 | 0.192 | 55 (47, 61) | 34 |
| east-afnet4 | AF | 0.790 | 0.541 | 1,045 | 0.741 | 27 (25, 29) | 21 | 0.831 | 35 (33, 37) | 28 | 0.833 | 35 (33, 37) | 28 | 0.842 | 36 (34, 37) | 29 |
| cabana-v2 | AF | 0.860 | 0.187 | 7,373 | 0.359 | 48 (44, 52) | 34 | 0.377 | 50 (45, 55) | 31 | 0.498 | 62 (60, 65) | 40 | 0.422 | 56 (52, 59) | 37 |
| affirm | AF | 1.150 | 0.303 | 5,305 | 0.462 | 34 (32, 37) | 25 | 0.504 | 40 (37, 42) | 30 | 0.569 | 47 (45, 48) | 35 | 0.537 | 44 (41, 45) | 31 |
| af-chf | AF | 1.060 | 0.249 | 37,116 | 0.394 | 37 (31, 42) | 23 | 0.465 | 46 (42, 50) | 33 | 0.408 | 39 (33, 44) | 31 | 0.503 | 50 (46, 53) | 32 |
| frail-af | AF | 1.690 | 0.084 | 1,361 | 0.102 | 18 (-9, 35) | 2 | 0.138 | 39 (22, 49) | 30 | 0.151 | 44 (30, 54) | 24 | 0.122 | 31 (11, 45) | 27 |
| laaos3 | AF | 0.670 | 0.098 | 1,995 | 0.121 | 19 (-28, 40) | 7 | 0.194 | 49 (37, 60) | 27 | 0.139 | 29 (3, 46) | 27 | 0.213 | 54 (40, 63) | 24 |
| protect-af | AF | 0.620 | 0.147 | 933 | 0.213 | 31 (9, 47) | 28 | 0.244 | 40 (22, 52) | 25 | 0.235 | 37 (19, 48) | 28 | 0.273 | 46 (33, 55) | 30 |
| raft-af | AF | 0.710 | 0.546 | 491 | 0.665 | 18 (10, 24) | 13 | 0.777 | 30 (24, 34) | 21 | 0.850 | 36 (32, 40) | 25 | 0.778 | 30 (24, 33) | 21 |
| active-w | AF | 1.440 | 0.165 | 1,434 | 0.210 | 22 (10, 35) | 18 | 0.252 | 35 (21, 42) | 31 | 0.277 | 40 (31, 47) | 27 | 0.268 | 39 (28, 45) | 29 |
| comet | HF | 1.210 | 0.281 | 3,214 | 0.368 | 24 (19, 29) | 18 | 0.459 | 39 (36, 42) | 28 | 0.460 | 39 (36, 42) | 29 | 0.458 | 39 (35, 42) | 28 |
| paradigm-hf-seq | HF | 0.800 | 0.541 | 1,165 | 0.653 | 17 (11, 21) | 12 | 0.724 | 25 (22, 29) | 19 | 0.755 | 28 (25, 31) | 20 | 0.734 | 26 (23, 30) | 20 |
| transform-hf | HF | 1.020 | 0.175 | 458,702 | 0.252 | 31 (16, 38) | 22 | 0.278 | 37 (27, 44) | 25 | 0.320 | 46 (37, 51) | 30 | 0.295 | 41 (32, 47) | 26 |
| elite-ii | HF | 1.130 | 0.168 | 12,515 | 0.232 | 28 (20, 37) | 21 | 0.281 | 40 (35, 46) | 24 | 0.281 | 40 (33, 46) | 28 | 0.283 | 41 (33, 46) | 27 |
| emperor-preserved-v2 | HF | 0.790 | 0.515 | 1,096 | 0.599 | 14 (5, 21) | 11 | 0.670 | 23 (16, 29) | 18 | 0.748 | 31 (26, 36) | 23 | 0.702 | 27 (21, 32) | 20 |
| empa-reg | DM | 0.860 | 0.197 | 6,998 | 0.308 | 36 (29, 41) | 26 | 0.372 | 47 (41, 51) | 28 | 0.337 | 41 (36, 46) | 29 | 0.361 | 45 (39, 48) | 30 |
| carolina | DM | 0.980 | 0.263 | 292,584 | 0.347 | 24 (12, 35) | 20 | 0.493 | 47 (40, 52) | 31 | 0.386 | 32 (23, 41) | 27 | 0.457 | 43 (36, 49) | 29 |
| leader | DM | 0.870 | 0.176 | 9,208 | 0.283 | 38 (22, 44) | 18 | 0.285 | 38 (25, 48) | 28 | 0.297 | 41 (29, 50) | 26 | 0.300 | 41 (30, 50) | 26 |
| sustain6 | DM | 0.740 | 0.115 | 3,009 | 0.200 | 43 (32, 50) | 27 | 0.225 | 49 (41, 55) | 26 | 0.204 | 44 (35, 50) | 28 | 0.223 | 48 (39, 55) | 30 |
| rewind | DM | 0.880 | 0.204 | 9,418 | 0.336 | 39 (33, 47) | 27 | 0.347 | 41 (35, 48) | 31 | 0.332 | 38 (28, 45) | 33 | 0.356 | 43 (35, 48) | 33 |
| declare | DM | 0.830 | 0.323 | 2,802 | 0.662 | 51 (48, 54) | 35 | 0.721 | 55 (52, 58) | 41 | 0.707 | 54 (51, 57) | 40 | 0.744 | 57 (54, 59) | 42 |
| canvas | DM | 0.860 | 0.148 | 9,319 | 0.261 | 43 (30, 51) | 29 | 0.291 | 49 (41, 57) | 29 | 0.275 | 46 (36, 53) | 30 | 0.300 | 51 (41, 57) | 29 |
| tecos | DM | 0.980 | 0.236 | 326,206 | 0.339 | 30 (23, 36) | 19 | 0.386 | 39 (34, 44) | 24 | 0.385 | 39 (32, 43) | 26 | 0.379 | 38 (32, 42) | 27 |
| carmelina | DM | 1.020 | 0.227 | 353,110 | 0.289 | 22 (5, 32) | 13 | 0.361 | 37 (27, 45) | 21 | 0.275 | 18 (-0, 28) | 7 | 0.328 | 31 (20, 40) | 23 |
| life | HTN | 0.870 | 0.145 | 11,200 | 0.223 | 35 (25, 44) | 20 | 0.224 | 35 (26, 43) | 18 | 0.259 | 44 (35, 49) | 34 | 0.232 | 38 (30, 44) | 26 |
| allhat | HTN | 0.980 | 0.058 | 1,318,466 | 0.099 | 41 (36, 46) | 24 | 0.111 | 47 (44, 51) | 31 | 0.110 | 47 (42, 50) | 31 | 0.115 | 49 (46, 52) | 34 |
| value | HTN | 1.040 | 0.149 | 137,263 | 0.280 | 47 (45, 49) | 30 | 0.293 | 49 (47, 51) | 31 | 0.284 | 48 (45, 50) | 35 | 0.313 | 52 (51, 54) | 36 |
| ascot | HTN | 0.900 | 0.048 | 58,559 | 0.082 | 41 (36, 45) | 26 | 0.085 | 43 (40, 47) | 27 | 0.080 | 40 (34, 44) | 28 | 0.088 | 45 (41, 49) | 31 |
| insight | HTN | 1.100 | 0.223 | 15,503 | 0.409 | 45 (36, 53) | 25 | 0.387 | 42 (33, 50) | 28 | 0.435 | 49 (39, 55) | 31 | 0.429 | 48 (41, 55) | 36 |
| plato | ACS/post-MI | 0.840 | 0.161 | 6,411 | 0.277 | 42 (37, 46) | 28 | 0.327 | 51 (47, 54) | 35 | 0.329 | 51 (48, 54) | 36 | 0.328 | 51 (47, 54) | 36 |
| valiant | ACS/post-MI | 1.000 | 0.124 | n/a (RCT HR = 1) | 0.185 | 33 (14, 44) | 25 | 0.258 | 52 (43, 57) | 39 | 0.234 | 47 (37, 53) | 33 | 0.231 | 46 (37, 54) | 34 |
| ontarget | Other | 1.010 | 0.281 | 1,130,387 | 0.452 | 38 (35, 40) | 25 | 0.456 | 39 (36, 40) | 24 | 0.439 | 36 (34, 38) | 27 | 0.488 | 42 (41, 44) | 29 |
| precision | Other | 0.930 | 0.108 | 55,077 | 0.207 | 48 (43, 53) | 32 | 0.230 | 53 (49, 56) | 34 | 0.235 | 54 (49, 57) | 36 | 0.230 | 53 (49, 57) | 38 |
| amplify | Other | 0.840 | 0.191 | 5,397 | 0.245 | 22 (5, 32) | 13 | 0.271 | 29 (17, 39) | 25 | 0.328 | 42 (36, 50) | 31 | 0.272 | 30 (16, 37) | 24 |
| lodestar | Other | 1.060 | 0.227 | 40,657 | 0.366 | 38 (35, 40) | 28 | 0.430 | 47 (45, 49) | 33 | 0.443 | 49 (47, 50) | 34 | 0.451 | 50 (47, 52) | 35 |
| prove-it | Other | 0.840 | 0.290 | 3,567 | 0.371 | 22 (14, 32) | 20 | 0.489 | 41 (34, 46) | 28 | 0.505 | 43 (37, 47) | 29 | 0.497 | 42 (35, 47) | 26 |

### Enrichment, unm

| trial | cat | rct_hr | p_full | N_full | ECG top25 p | ECG red25 % | ECG red50 % | CLIN top25 p | CLIN red25 % | CLIN red50 % | CLMBR top25 p | CLMBR red25 % | CLMBR red50 % | ECG+CLIN top25 p | ECG+CLIN red25 % | ECG+CLIN red50 % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 0.790 | 0.070 | 8,035 | 0.108 | 35 (29, 39) | 20 | 0.170 | 59 (57, 60) | 39 | 0.163 | 57 (54, 59) | 40 | 0.174 | 60 (58, 61) | 38 |
| rocket-af | AF | 0.880 | 0.081 | 23,771 | 0.116 | 30 (23, 38) | 17 | 0.196 | 59 (55, 61) | 36 | 0.179 | 55 (52, 58) | 37 | 0.195 | 59 (55, 61) | 36 |
| rely | AF | 0.660 | 0.105 | 1,726 | 0.141 | 25 (10, 34) | 16 | 0.247 | 57 (54, 60) | 37 | 0.228 | 54 (49, 57) | 36 | 0.247 | 57 (54, 60) | 36 |
| east-afnet4 | AF | 0.790 | 0.533 | 1,059 | 0.733 | 27 (25, 29) | 20 | 0.832 | 36 (35, 37) | 28 | 0.816 | 35 (34, 36) | 28 | 0.839 | 36 (35, 38) | 29 |
| cabana-v2 | AF | 0.860 | 0.366 | 3,776 | 0.569 | 36 (34, 37) | 26 | 0.644 | 43 (41, 44) | 32 | 0.696 | 47 (46, 48) | 36 | 0.653 | 44 (43, 45) | 33 |
| affirm | AF | 1.150 | 0.295 | 5,441 | 0.438 | 33 (31, 34) | 22 | 0.502 | 41 (40, 43) | 31 | 0.538 | 45 (43, 46) | 34 | 0.517 | 43 (41, 44) | 32 |
| af-chf | AF | 1.060 | 0.233 | 39,684 | 0.352 | 34 (29, 37) | 22 | 0.415 | 44 (41, 47) | 32 | 0.388 | 40 (36, 44) | 29 | 0.443 | 47 (44, 50) | 33 |
| frail-af | AF | 1.690 | 0.083 | 1,373 | 0.108 | 23 (7, 34) | 11 | 0.156 | 47 (39, 53) | 31 | 0.137 | 40 (32, 47) | 27 | 0.142 | 41 (33, 50) | 30 |
| laaos3 | AF | 0.670 | 0.098 | 2,007 | 0.107 | 9 (-9, 29) | 8 | 0.209 | 53 (44, 59) | 31 | 0.146 | 33 (16, 44) | 25 | 0.206 | 53 (47, 59) | 31 |
| protect-af | AF | 0.620 | 0.180 | 765 | 0.237 | 24 (11, 36) | 21 | 0.307 | 41 (34, 49) | 30 | 0.268 | 33 (18, 41) | 28 | 0.292 | 38 (26, 46) | 32 |
| raft-af | AF | 0.710 | 0.648 | 413 | 0.733 | 12 (8, 15) | 10 | 0.825 | 21 (19, 24) | 18 | 0.837 | 23 (21, 26) | 21 | 0.845 | 23 (21, 26) | 18 |
| active-w | AF | 1.440 | 0.149 | 1,581 | 0.203 | 26 (17, 34) | 16 | 0.267 | 44 (39, 49) | 33 | 0.257 | 42 (36, 47) | 28 | 0.264 | 43 (37, 48) | 30 |
| comet | HF | 1.210 | 0.270 | 3,338 | 0.376 | 28 (24, 32) | 21 | 0.458 | 41 (38, 43) | 29 | 0.455 | 41 (38, 43) | 29 | 0.453 | 40 (38, 43) | 29 |
| paradigm-hf-seq | HF | 0.800 | 0.499 | 1,264 | 0.622 | 20 (17, 23) | 15 | 0.692 | 28 (25, 30) | 20 | 0.733 | 32 (30, 34) | 23 | 0.698 | 28 (26, 31) | 22 |
| transform-hf | HF | 1.020 | 0.180 | 445,391 | 0.265 | 32 (30, 35) | 22 | 0.287 | 37 (35, 40) | 24 | 0.334 | 46 (44, 48) | 31 | 0.308 | 42 (40, 44) | 29 |
| elite-ii | HF | 1.130 | 0.173 | 12,151 | 0.242 | 28 (22, 36) | 18 | 0.281 | 38 (34, 43) | 24 | 0.298 | 42 (37, 46) | 30 | 0.285 | 39 (33, 43) | 27 |
| emperor-preserved-v2 | HF | 0.790 | 0.542 | 1,043 | 0.623 | 13 (7, 18) | 11 | 0.716 | 24 (21, 28) | 18 | 0.770 | 30 (26, 33) | 21 | 0.723 | 25 (21, 29) | 20 |
| empa-reg | DM | 0.860 | 0.210 | 6,559 | 0.316 | 34 (27, 39) | 24 | 0.387 | 46 (42, 49) | 31 | 0.363 | 42 (38, 45) | 30 | 0.378 | 44 (41, 48) | 31 |
| carolina | DM | 0.980 | 0.266 | 289,515 | 0.374 | 29 (19, 38) | 21 | 0.483 | 45 (38, 51) | 32 | 0.389 | 32 (23, 40) | 25 | 0.456 | 42 (35, 48) | 31 |
| leader | DM | 0.870 | 0.239 | 6,769 | 0.349 | 32 (25, 37) | 18 | 0.389 | 39 (34, 43) | 27 | 0.382 | 37 (32, 42) | 26 | 0.390 | 39 (34, 43) | 26 |
| sustain6 | DM | 0.740 | 0.139 | 2,491 | 0.232 | 40 (32, 46) | 25 | 0.250 | 44 (40, 49) | 29 | 0.246 | 43 (37, 48) | 26 | 0.259 | 46 (41, 51) | 29 |
| rewind | DM | 0.880 | 0.241 | 7,981 | 0.388 | 38 (33, 42) | 26 | 0.428 | 44 (40, 47) | 30 | 0.405 | 41 (37, 44) | 32 | 0.442 | 46 (43, 49) | 31 |
| declare | DM | 0.830 | 0.304 | 2,977 | 0.625 | 51 (49, 53) | 35 | 0.727 | 58 (57, 60) | 40 | 0.700 | 57 (55, 58) | 40 | 0.738 | 59 (57, 60) | 41 |
| canvas | DM | 0.860 | 0.170 | 8,114 | 0.287 | 41 (36, 45) | 29 | 0.337 | 49 (46, 52) | 34 | 0.316 | 46 (42, 49) | 32 | 0.345 | 51 (48, 54) | 35 |
| tecos | DM | 0.980 | 0.238 | 323,761 | 0.339 | 30 (23, 35) | 19 | 0.383 | 38 (33, 42) | 24 | 0.386 | 38 (32, 43) | 25 | 0.376 | 37 (31, 42) | 27 |
| carmelina | DM | 1.020 | 0.229 | 350,089 | 0.311 | 26 (15, 34) | 11 | 0.359 | 36 (28, 43) | 24 | 0.265 | 14 (-1, 25) | 4 | 0.330 | 31 (22, 38) | 22 |
| life | HTN | 0.870 | 0.162 | 10,017 | 0.243 | 34 (23, 41) | 20 | 0.261 | 38 (31, 43) | 23 | 0.302 | 47 (41, 51) | 34 | 0.264 | 39 (32, 44) | 28 |
| allhat | HTN | 0.980 | 0.065 | 1,180,460 | 0.112 | 42 (38, 45) | 25 | 0.129 | 50 (47, 52) | 31 | 0.122 | 47 (44, 49) | 32 | 0.134 | 51 (49, 54) | 34 |
| value | HTN | 1.040 | 0.166 | 122,595 | 0.300 | 45 (43, 46) | 29 | 0.326 | 49 (47, 50) | 32 | 0.321 | 48 (46, 49) | 35 | 0.346 | 52 (50, 53) | 35 |
| ascot | HTN | 0.900 | 0.048 | 58,934 | 0.079 | 39 (34, 44) | 25 | 0.084 | 43 (39, 47) | 26 | 0.081 | 41 (36, 46) | 29 | 0.088 | 45 (41, 48) | 30 |
| insight | HTN | 1.100 | 0.154 | 22,470 | 0.268 | 43 (39, 46) | 27 | 0.275 | 44 (41, 47) | 27 | 0.309 | 50 (48, 53) | 34 | 0.300 | 49 (46, 51) | 34 |
| plato | ACS/post-MI | 0.840 | 0.163 | 6,340 | 0.286 | 43 (39, 46) | 30 | 0.324 | 50 (47, 53) | 35 | 0.324 | 50 (46, 52) | 35 | 0.335 | 51 (49, 54) | 36 |
| valiant | ACS/post-MI | 1.000 | 0.123 | n/a (RCT HR = 1) | 0.187 | 34 (23, 42) | 27 | 0.257 | 52 (47, 56) | 36 | 0.249 | 50 (44, 54) | 36 | 0.240 | 49 (41, 53) | 35 |
| ontarget | Other | 1.010 | 0.290 | 1,092,288 | 0.469 | 38 (36, 40) | 25 | 0.467 | 38 (36, 39) | 24 | 0.457 | 36 (35, 38) | 26 | 0.501 | 42 (40, 44) | 29 |
| precision | Other | 0.930 | 0.111 | 53,881 | 0.207 | 47 (42, 51) | 32 | 0.235 | 53 (49, 56) | 35 | 0.237 | 53 (49, 57) | 35 | 0.238 | 54 (49, 56) | 37 |
| amplify | Other | 0.840 | 0.199 | 5,188 | 0.241 | 17 (10, 24) | 14 | 0.312 | 36 (32, 40) | 25 | 0.345 | 42 (39, 46) | 30 | 0.312 | 36 (32, 40) | 25 |
| lodestar | Other | 1.060 | 0.249 | 37,068 | 0.400 | 38 (36, 39) | 27 | 0.465 | 46 (45, 47) | 32 | 0.478 | 48 (47, 49) | 34 | 0.477 | 48 (46, 49) | 33 |
| prove-it | Other | 0.840 | 0.256 | 4,042 | 0.392 | 35 (32, 39) | 25 | 0.464 | 45 (42, 48) | 33 | 0.504 | 49 (47, 51) | 33 | 0.463 | 45 (42, 48) | 33 |

### Predictive (treatment x score, ratio of HR per SD treated vs comparator), m_sparse

| trial | cat | ECG ratio | ECG p (q) | CLIN ratio | CLIN p (q) | CLMBR ratio | CLMBR p (q) | ECG+CLIN ratio | ECG+CLIN p (q) | PROG ratio | PROG p (q) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 1.04 (0.87-1.25) | 0.660 (0.95) | 1.12 (0.97-1.30) | 0.116 (0.63) | 1.23 (1.01-1.50) | 0.041 (0.26) | 1.12 (0.96-1.30) | 0.143 (0.61) | 1.23 (1.02-1.48) | 0.034 (0.44) |
| rocket-af | AF | 0.92 (0.73-1.16) | 0.481 (0.83) | 0.96 (0.83-1.12) | 0.625 (0.83) | 0.94 (0.76-1.17) | 0.604 (0.82) | 0.97 (0.82-1.14) | 0.673 (0.85) | 0.92 (0.72-1.16) | 0.478 (0.79) |
| rely | AF | 1.17 (0.81-1.69) | 0.392 (0.75) | 1.15 (0.89-1.49) | 0.291 (0.74) | 1.16 (0.79-1.72) | 0.451 (0.73) | 1.19 (0.90-1.57) | 0.232 (0.61) | 1.09 (0.73-1.64) | 0.670 (0.91) |
| east-afnet4 | AF | 0.99 (0.92-1.06) | 0.751 (0.96) | 0.98 (0.91-1.06) | 0.644 (0.83) | 1.00 (0.92-1.09) | 0.958 (0.96) | 0.99 (0.91-1.07) | 0.730 (0.85) | 0.96 (0.87-1.05) | 0.378 (0.74) |
| cabana-v2 | AF | 1.05 (0.88-1.26) | 0.577 (0.95) | 1.20 (1.02-1.40) | 0.024 (0.30) | 1.09 (0.87-1.38) | 0.443 (0.73) | 1.10 (0.93-1.29) | 0.265 (0.61) | 1.03 (0.75-1.41) | 0.870 (0.98) |
| affirm | AF | 1.09 (1.00-1.18) | 0.041 (0.19) | 1.03 (0.95-1.11) | 0.500 (0.74) | 1.25 (1.12-1.39) | 0.000 (0.00) | 1.09 (1.00-1.18) | 0.052 (0.50) | 1.08 (0.98-1.18) | 0.110 (0.67) |
| af-chf | AF | 1.13 (0.94-1.35) | 0.195 (0.53) | 0.95 (0.79-1.15) | 0.597 (0.83) | 1.06 (0.87-1.29) | 0.576 (0.81) | 1.04 (0.86-1.24) | 0.702 (0.85) | 0.94 (0.79-1.11) | 0.454 (0.78) |
| frail-af | AF | 0.95 (0.67-1.35) | 0.782 (0.96) | 0.75 (0.55-1.03) | 0.075 (0.48) | 0.80 (0.52-1.23) | 0.311 (0.73) | 0.75 (0.54-1.04) | 0.083 (0.53) | 0.70 (0.48-1.01) | 0.058 (0.55) |
| laaos3 | AF | 0.91 (0.61-1.37) | 0.663 (0.95) | 1.01 (0.74-1.37) | 0.969 (0.99) | 1.11 (0.68-1.82) | 0.667 (0.82) | 1.03 (0.69-1.55) | 0.868 (0.97) | 1.18 (0.80-1.73) | 0.410 (0.74) |
| protect-af | AF | 1.30 (0.84-1.99) | 0.235 (0.57) | 0.96 (0.66-1.40) | 0.831 (0.95) | 0.96 (0.65-1.40) | 0.819 (0.84) | 1.10 (0.72-1.68) | 0.654 (0.85) | 0.90 (0.57-1.41) | 0.650 (0.91) |
| raft-af | AF | 1.18 (1.00-1.38) | 0.046 (0.19) | 0.94 (0.80-1.12) | 0.503 (0.74) | 1.08 (0.89-1.31) | 0.407 (0.73) | 1.10 (0.92-1.30) | 0.291 (0.61) | 1.14 (0.93-1.40) | 0.194 (0.67) |
| active-w | AF | 0.80 (0.63-1.03) | 0.086 (0.27) | 0.92 (0.75-1.14) | 0.452 (0.74) | 0.89 (0.71-1.13) | 0.345 (0.73) | 0.88 (0.70-1.11) | 0.272 (0.61) | 0.91 (0.73-1.13) | 0.393 (0.74) |
| comet | HF | 0.92 (0.82-1.03) | 0.147 (0.43) | 1.06 (0.94-1.19) | 0.332 (0.74) | 1.11 (0.99-1.25) | 0.077 (0.33) | 1.03 (0.92-1.16) | 0.567 (0.85) | 1.08 (0.96-1.22) | 0.216 (0.67) |
| paradigm-hf-seq | HF | 0.87 (0.78-0.98) | 0.024 (0.19) | 0.95 (0.85-1.06) | 0.329 (0.74) | 0.89 (0.78-1.01) | 0.077 (0.33) | 0.94 (0.84-1.05) | 0.277 (0.61) | 1.02 (0.90-1.15) | 0.753 (0.95) |
| transform-hf | HF | 1.15 (0.89-1.49) | 0.270 (0.57) | 0.91 (0.69-1.19) | 0.484 (0.74) | 0.89 (0.68-1.17) | 0.408 (0.73) | 0.93 (0.72-1.20) | 0.559 (0.85) | 0.93 (0.72-1.20) | 0.576 (0.84) |
| elite-ii | HF | 1.01 (0.82-1.23) | 0.952 (0.99) | 1.21 (0.99-1.48) | 0.066 (0.48) | 1.13 (0.90-1.42) | 0.288 (0.73) | 1.13 (0.91-1.40) | 0.267 (0.61) | 1.00 (0.81-1.23) | 0.990 (0.99) |
| emperor-preserved-v2 | HF | 1.00 (0.84-1.19) | 0.976 (0.99) | 1.13 (0.95-1.35) | 0.160 (0.72) | 1.37 (1.13-1.67) | 0.001 (0.02) | 1.10 (0.92-1.31) | 0.305 (0.61) | 1.15 (0.94-1.41) | 0.168 (0.67) |
| empa-reg | DM | 1.06 (0.91-1.23) | 0.463 (0.83) | 1.07 (0.92-1.25) | 0.366 (0.74) | 1.04 (0.87-1.24) | 0.680 (0.82) | 1.10 (0.94-1.28) | 0.246 (0.61) | 1.01 (0.84-1.22) | 0.901 (0.98) |
| carolina | DM | 1.00 (0.80-1.25) | 0.994 (0.99) | 1.10 (0.88-1.36) | 0.397 (0.74) | 1.22 (0.98-1.51) | 0.072 (0.33) | 1.11 (0.89-1.39) | 0.348 (0.63) | 1.20 (0.94-1.53) | 0.134 (0.67) |
| leader | DM | 1.05 (0.76-1.45) | 0.756 (0.96) | 0.94 (0.71-1.24) | 0.659 (0.83) | 1.06 (0.72-1.55) | 0.774 (0.82) | 1.07 (0.80-1.43) | 0.655 (0.85) | 0.81 (0.55-1.20) | 0.299 (0.67) |
| sustain6 | DM | 0.89 (0.67-1.17) | 0.393 (0.75) | 1.16 (0.90-1.49) | 0.244 (0.74) | 1.48 (1.07-2.04) | 0.017 (0.16) | 1.00 (0.78-1.28) | 0.980 (0.99) | 1.04 (0.71-1.53) | 0.838 (0.98) |
| rewind | DM | 1.05 (0.87-1.26) | 0.618 (0.95) | 1.03 (0.86-1.23) | 0.785 (0.95) | 1.04 (0.84-1.29) | 0.712 (0.82) | 1.06 (0.89-1.26) | 0.533 (0.85) | 1.00 (0.79-1.27) | 0.970 (0.99) |
| declare | DM | 1.02 (0.88-1.18) | 0.832 (0.97) | 1.00 (0.87-1.15) | 0.986 (0.99) | 0.97 (0.82-1.15) | 0.741 (0.82) | 1.00 (0.86-1.15) | 0.953 (0.99) | 0.80 (0.66-0.97) | 0.021 (0.40) |
| canvas | DM | 0.71 (0.52-0.98) | 0.037 (0.19) | 0.90 (0.66-1.21) | 0.477 (0.74) | 0.87 (0.60-1.26) | 0.455 (0.73) | 0.84 (0.60-1.16) | 0.288 (0.61) | 0.73 (0.47-1.12) | 0.149 (0.67) |
| tecos | DM | 1.01 (0.85-1.19) | 0.915 (0.99) | 1.06 (0.92-1.23) | 0.434 (0.74) | 1.15 (0.97-1.37) | 0.115 (0.40) | 1.10 (0.94-1.28) | 0.245 (0.61) | 1.04 (0.86-1.25) | 0.713 (0.93) |
| carmelina | DM | 0.74 (0.57-0.97) | 0.026 (0.19) | 0.87 (0.69-1.10) | 0.245 (0.74) | 0.77 (0.60-0.99) | 0.041 (0.26) | 0.85 (0.68-1.07) | 0.160 (0.61) | 0.81 (0.62-1.07) | 0.140 (0.67) |
| life | HTN | 1.16 (0.91-1.48) | 0.243 (0.57) | 1.41 (1.16-1.71) | 0.001 (0.01) | 1.09 (0.87-1.36) | 0.462 (0.73) | 1.37 (1.10-1.71) | 0.005 (0.09) | 1.15 (0.87-1.53) | 0.325 (0.69) |
| allhat | HTN | 0.97 (0.85-1.11) | 0.673 (0.95) | 1.00 (0.90-1.12) | 0.994 (0.99) | 0.94 (0.82-1.07) | 0.345 (0.73) | 0.98 (0.87-1.10) | 0.737 (0.85) | 0.92 (0.80-1.06) | 0.243 (0.67) |
| value | HTN | 1.15 (1.07-1.24) | 0.000 (0.01) | 1.14 (1.07-1.23) | 0.000 (0.01) | 1.11 (1.02-1.20) | 0.015 (0.16) | 1.13 (1.04-1.22) | 0.003 (0.09) | 1.21 (1.11-1.32) | 0.000 (0.00) |
| ascot | HTN | 1.01 (0.89-1.16) | 0.851 (0.97) | 1.05 (0.94-1.17) | 0.405 (0.74) | 0.97 (0.85-1.11) | 0.701 (0.82) | 1.00 (0.89-1.13) | 0.985 (0.99) | 0.99 (0.85-1.16) | 0.929 (0.98) |
| insight | HTN | 1.22 (0.87-1.73) | 0.254 (0.57) | 0.76 (0.56-1.02) | 0.064 (0.48) | 0.90 (0.64-1.27) | 0.536 (0.78) | 0.95 (0.68-1.31) | 0.738 (0.85) | 0.78 (0.54-1.14) | 0.197 (0.67) |
| plato | ACS/post-MI | 1.21 (1.04-1.40) | 0.014 (0.17) | 1.09 (0.96-1.25) | 0.172 (0.72) | 1.11 (0.95-1.29) | 0.179 (0.57) | 1.14 (0.99-1.30) | 0.070 (0.53) | 1.10 (0.94-1.28) | 0.248 (0.67) |
| valiant | ACS/post-MI | 1.32 (0.97-1.80) | 0.082 (0.27) | 1.01 (0.78-1.31) | 0.944 (0.99) | 0.87 (0.60-1.26) | 0.458 (0.73) | 1.14 (0.87-1.50) | 0.345 (0.63) | 0.91 (0.66-1.25) | 0.565 (0.84) |
| ontarget | Other | 1.07 (1.00-1.14) | 0.064 (0.24) | 1.04 (0.97-1.11) | 0.264 (0.74) | 1.01 (0.94-1.09) | 0.777 (0.82) | 1.07 (1.00-1.14) | 0.049 (0.50) | 1.04 (0.97-1.13) | 0.267 (0.67) |
| precision | Other | 1.03 (0.86-1.24) | 0.745 (0.96) | 1.02 (0.87-1.19) | 0.848 (0.95) | 1.10 (0.88-1.37) | 0.409 (0.73) | 1.00 (0.85-1.19) | 0.967 (0.99) | 0.88 (0.71-1.11) | 0.286 (0.67) |
| amplify | Other | 0.98 (0.77-1.25) | 0.864 (0.97) | 1.08 (0.88-1.33) | 0.459 (0.74) | 0.91 (0.69-1.20) | 0.494 (0.75) | 1.07 (0.87-1.31) | 0.513 (0.85) | 1.08 (0.86-1.37) | 0.516 (0.82) |
| lodestar | Other | 1.11 (1.01-1.22) | 0.035 (0.19) | 1.01 (0.93-1.10) | 0.822 (0.95) | 1.09 (0.98-1.21) | 0.103 (0.39) | 1.02 (0.94-1.12) | 0.596 (0.85) | 0.99 (0.90-1.10) | 0.901 (0.98) |
| prove-it | Other | 1.37 (1.11-1.70) | 0.003 (0.06) | 1.11 (0.90-1.37) | 0.325 (0.74) | 1.03 (0.82-1.31) | 0.778 (0.82) | 1.15 (0.92-1.43) | 0.213 (0.61) | 1.01 (0.79-1.29) | 0.920 (0.98) |

### Predictive (treatment x score, ratio of HR per SD treated vs comparator), m_P1

| trial | cat | ECG ratio | ECG p (q) | CLIN ratio | CLIN p (q) | CLMBR ratio | CLMBR p (q) | ECG+CLIN ratio | ECG+CLIN p (q) | PROG ratio | PROG p (q) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 1.12 (0.93-1.34) | 0.225 (0.57) | 1.05 (0.90-1.21) | 0.546 (0.84) | 1.03 (0.84-1.26) | 0.772 (0.84) | 1.05 (0.90-1.22) | 0.541 (0.85) | 1.21 (0.99-1.47) | 0.059 (0.48) |
| rocket-af | AF | 0.96 (0.77-1.19) | 0.685 (0.88) | 1.00 (0.85-1.17) | 0.988 (1.00) | 0.90 (0.73-1.10) | 0.302 (0.72) | 0.99 (0.83-1.17) | 0.866 (0.92) | 0.95 (0.75-1.20) | 0.662 (0.87) |
| rely | AF | 1.08 (0.74-1.58) | 0.695 (0.88) | 1.15 (0.87-1.51) | 0.334 (0.75) | 1.26 (0.88-1.83) | 0.210 (0.57) | 1.16 (0.86-1.58) | 0.326 (0.79) | 1.21 (0.81-1.81) | 0.358 (0.80) |
| east-afnet4 | AF | 0.98 (0.91-1.05) | 0.565 (0.88) | 1.00 (0.93-1.08) | 0.999 (1.00) | 1.03 (0.94-1.12) | 0.536 (0.72) | 1.01 (0.93-1.09) | 0.885 (0.92) | 0.93 (0.85-1.03) | 0.165 (0.70) |
| cabana-v2 | AF | 1.12 (0.93-1.35) | 0.248 (0.59) | 1.30 (1.10-1.53) | 0.002 (0.04) | 1.06 (0.84-1.34) | 0.621 (0.77) | 1.22 (1.02-1.46) | 0.027 (0.15) | 1.17 (0.86-1.59) | 0.330 (0.80) |
| affirm | AF | 1.09 (1.00-1.18) | 0.046 (0.22) | 0.98 (0.90-1.06) | 0.551 (0.84) | 1.16 (1.04-1.30) | 0.008 (0.10) | 1.03 (0.95-1.12) | 0.466 (0.85) | 1.05 (0.96-1.16) | 0.258 (0.80) |
| af-chf | AF | 1.19 (0.99-1.42) | 0.066 (0.28) | 0.94 (0.77-1.14) | 0.535 (0.84) | 1.09 (0.89-1.32) | 0.402 (0.72) | 1.02 (0.84-1.24) | 0.827 (0.92) | 0.93 (0.78-1.12) | 0.451 (0.84) |
| frail-af | AF | 0.89 (0.62-1.26) | 0.502 (0.88) | 0.81 (0.57-1.15) | 0.232 (0.68) | 0.84 (0.54-1.28) | 0.409 (0.72) | 0.79 (0.55-1.14) | 0.210 (0.73) | 0.74 (0.49-1.11) | 0.145 (0.70) |
| laaos3 | AF | 0.89 (0.57-1.39) | 0.604 (0.88) | 0.87 (0.61-1.24) | 0.436 (0.79) | 0.98 (0.58-1.64) | 0.932 (0.93) | 0.88 (0.56-1.37) | 0.564 (0.85) | 1.06 (0.69-1.63) | 0.797 (0.92) |
| protect-af | AF | 1.70 (1.10-2.63) | 0.017 (0.13) | 0.76 (0.52-1.10) | 0.146 (0.50) | 1.13 (0.81-1.57) | 0.463 (0.72) | 1.04 (0.70-1.55) | 0.858 (0.92) | 0.83 (0.56-1.22) | 0.340 (0.80) |
| raft-af | AF | 1.05 (0.90-1.23) | 0.524 (0.88) | 1.08 (0.91-1.29) | 0.360 (0.76) | 1.20 (0.99-1.45) | 0.059 (0.32) | 1.12 (0.94-1.34) | 0.188 (0.71) | 1.15 (0.96-1.39) | 0.137 (0.70) |
| active-w | AF | 0.85 (0.67-1.08) | 0.178 (0.52) | 0.78 (0.64-0.95) | 0.013 (0.11) | 0.82 (0.64-1.06) | 0.126 (0.48) | 0.75 (0.61-0.93) | 0.009 (0.11) | 0.79 (0.62-1.00) | 0.046 (0.48) |
| comet | HF | 0.89 (0.80-0.99) | 0.031 (0.20) | 1.05 (0.94-1.17) | 0.413 (0.79) | 1.12 (1.00-1.26) | 0.049 (0.31) | 1.01 (0.91-1.13) | 0.838 (0.92) | 1.04 (0.93-1.16) | 0.534 (0.84) |
| paradigm-hf-seq | HF | 0.88 (0.78-0.99) | 0.037 (0.20) | 0.87 (0.78-0.97) | 0.015 (0.11) | 0.89 (0.77-1.01) | 0.080 (0.35) | 0.90 (0.80-1.01) | 0.074 (0.35) | 0.98 (0.86-1.12) | 0.753 (0.92) |
| transform-hf | HF | 1.10 (0.87-1.40) | 0.422 (0.84) | 0.99 (0.75-1.31) | 0.955 (1.00) | 0.78 (0.59-1.03) | 0.083 (0.35) | 0.97 (0.76-1.24) | 0.799 (0.92) | 0.87 (0.67-1.12) | 0.280 (0.80) |
| elite-ii | HF | 1.02 (0.83-1.26) | 0.843 (0.94) | 1.11 (0.92-1.35) | 0.287 (0.73) | 1.08 (0.86-1.37) | 0.506 (0.72) | 1.11 (0.89-1.37) | 0.347 (0.79) | 0.97 (0.78-1.21) | 0.791 (0.92) |
| emperor-preserved-v2 | HF | 0.99 (0.84-1.19) | 0.955 (0.99) | 1.20 (1.01-1.44) | 0.041 (0.20) | 1.45 (1.19-1.75) | 0.000 (0.01) | 1.14 (0.96-1.35) | 0.136 (0.57) | 1.20 (0.99-1.45) | 0.063 (0.48) |
| empa-reg | DM | 1.04 (0.89-1.21) | 0.657 (0.88) | 1.08 (0.93-1.25) | 0.306 (0.73) | 1.05 (0.89-1.25) | 0.549 (0.72) | 1.05 (0.91-1.22) | 0.508 (0.85) | 0.99 (0.82-1.19) | 0.878 (0.93) |
| carolina | DM | 0.96 (0.78-1.19) | 0.716 (0.88) | 0.99 (0.80-1.22) | 0.909 (1.00) | 1.16 (0.95-1.43) | 0.146 (0.48) | 0.99 (0.80-1.22) | 0.922 (0.92) | 1.06 (0.85-1.33) | 0.602 (0.85) |
| leader | DM | 0.99 (0.73-1.34) | 0.960 (0.99) | 0.92 (0.70-1.22) | 0.575 (0.84) | 1.04 (0.71-1.53) | 0.825 (0.87) | 0.98 (0.73-1.31) | 0.880 (0.92) | 0.89 (0.59-1.34) | 0.573 (0.85) |
| sustain6 | DM | 0.94 (0.71-1.25) | 0.669 (0.88) | 1.12 (0.87-1.43) | 0.379 (0.76) | 1.43 (1.02-2.02) | 0.039 (0.30) | 1.02 (0.79-1.30) | 0.898 (0.92) | 1.04 (0.72-1.51) | 0.842 (0.92) |
| rewind | DM | 1.00 (0.82-1.22) | 0.987 (0.99) | 1.00 (0.84-1.19) | 0.990 (1.00) | 1.10 (0.89-1.36) | 0.369 (0.72) | 1.03 (0.86-1.22) | 0.766 (0.92) | 1.02 (0.82-1.28) | 0.844 (0.92) |
| declare | DM | 0.80 (0.68-0.93) | 0.005 (0.05) | 0.98 (0.84-1.14) | 0.782 (1.00) | 0.87 (0.73-1.05) | 0.152 (0.48) | 0.93 (0.79-1.09) | 0.352 (0.79) | 0.86 (0.70-1.05) | 0.148 (0.70) |
| canvas | DM | 0.96 (0.70-1.33) | 0.821 (0.94) | 1.04 (0.79-1.35) | 0.800 (1.00) | 1.06 (0.73-1.53) | 0.757 (0.84) | 1.07 (0.79-1.45) | 0.675 (0.92) | 0.99 (0.66-1.50) | 0.979 (0.98) |
| tecos | DM | 1.00 (0.85-1.18) | 0.993 (0.99) | 1.05 (0.91-1.21) | 0.515 (0.84) | 1.12 (0.94-1.33) | 0.198 (0.57) | 1.08 (0.93-1.25) | 0.321 (0.79) | 1.02 (0.85-1.22) | 0.832 (0.92) |
| carmelina | DM | 0.95 (0.73-1.24) | 0.697 (0.88) | 0.87 (0.68-1.11) | 0.255 (0.69) | 0.92 (0.70-1.21) | 0.548 (0.72) | 0.93 (0.73-1.19) | 0.559 (0.85) | 0.82 (0.62-1.10) | 0.186 (0.71) |
| life | HTN | 1.15 (0.92-1.44) | 0.208 (0.56) | 1.24 (1.05-1.47) | 0.012 (0.11) | 1.08 (0.86-1.35) | 0.505 (0.72) | 1.27 (1.03-1.55) | 0.023 (0.15) | 1.11 (0.84-1.46) | 0.478 (0.84) |
| allhat | HTN | 0.98 (0.86-1.12) | 0.757 (0.90) | 0.97 (0.87-1.09) | 0.637 (0.90) | 0.96 (0.84-1.09) | 0.509 (0.72) | 0.95 (0.85-1.06) | 0.336 (0.79) | 0.93 (0.81-1.07) | 0.340 (0.80) |
| value | HTN | 1.18 (1.09-1.26) | 0.000 (0.00) | 1.21 (1.12-1.30) | 0.000 (0.00) | 1.12 (1.03-1.22) | 0.006 (0.10) | 1.19 (1.10-1.28) | 0.000 (0.00) | 1.24 (1.13-1.35) | 0.000 (0.00) |
| ascot | HTN | 1.03 (0.91-1.17) | 0.670 (0.88) | 1.08 (0.97-1.19) | 0.170 (0.54) | 1.02 (0.90-1.16) | 0.738 (0.84) | 1.03 (0.92-1.16) | 0.572 (0.85) | 1.00 (0.87-1.16) | 0.967 (0.98) |
| insight | HTN | 1.10 (0.78-1.55) | 0.594 (0.88) | 0.78 (0.59-1.03) | 0.081 (0.31) | 0.90 (0.66-1.22) | 0.491 (0.72) | 0.86 (0.63-1.18) | 0.345 (0.79) | 0.83 (0.58-1.18) | 0.298 (0.80) |
| plato | ACS/post-MI | 1.12 (0.97-1.28) | 0.121 (0.42) | 1.13 (1.01-1.27) | 0.039 (0.20) | 1.06 (0.92-1.22) | 0.416 (0.72) | 1.16 (1.02-1.31) | 0.025 (0.15) | 1.15 (0.99-1.33) | 0.063 (0.48) |
| valiant | ACS/post-MI | 1.19 (0.87-1.63) | 0.286 (0.64) | 1.03 (0.77-1.39) | 0.829 (1.00) | 0.97 (0.67-1.42) | 0.893 (0.92) | 1.08 (0.80-1.47) | 0.607 (0.85) | 0.93 (0.65-1.31) | 0.664 (0.87) |
| ontarget | Other | 1.06 (0.99-1.13) | 0.114 (0.42) | 1.06 (1.00-1.14) | 0.066 (0.28) | 1.01 (0.94-1.09) | 0.749 (0.84) | 1.08 (1.01-1.15) | 0.025 (0.15) | 1.02 (0.95-1.11) | 0.532 (0.84) |
| precision | Other | 1.14 (0.95-1.37) | 0.162 (0.51) | 1.02 (0.87-1.19) | 0.804 (1.00) | 1.09 (0.89-1.35) | 0.404 (0.72) | 1.05 (0.89-1.23) | 0.595 (0.85) | 0.94 (0.76-1.17) | 0.593 (0.85) |
| amplify | Other | 0.90 (0.70-1.15) | 0.390 (0.82) | 1.00 (0.80-1.25) | 0.983 (1.00) | 0.91 (0.68-1.21) | 0.499 (0.72) | 0.94 (0.75-1.18) | 0.575 (0.85) | 1.11 (0.86-1.42) | 0.437 (0.84) |
| lodestar | Other | 1.20 (1.09-1.32) | 0.000 (0.00) | 1.11 (1.02-1.21) | 0.021 (0.13) | 1.14 (1.02-1.26) | 0.016 (0.15) | 1.14 (1.04-1.26) | 0.006 (0.11) | 1.04 (0.94-1.17) | 0.432 (0.84) |
| prove-it | Other | 1.45 (1.17-1.79) | 0.001 (0.01) | 1.02 (0.82-1.27) | 0.838 (1.00) | 1.06 (0.83-1.35) | 0.629 (0.77) | 1.10 (0.88-1.38) | 0.398 (0.84) | 1.09 (0.84-1.41) | 0.504 (0.84) |

### Predictive (treatment x score, ratio of HR per SD treated vs comparator), m_clin

| trial | cat | ECG ratio | ECG p (q) | CLIN ratio | CLIN p (q) | CLMBR ratio | CLMBR p (q) | ECG+CLIN ratio | ECG+CLIN p (q) | PROG ratio | PROG p (q) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aristotle | AF | 1.07 (0.90-1.28) | 0.458 (0.79) | 1.12 (0.97-1.30) | 0.114 (0.57) | 1.13 (0.93-1.36) | 0.211 (0.62) | 1.10 (0.95-1.28) | 0.206 (0.63) | 1.21 (0.99-1.47) | 0.062 (0.59) |
| rocket-af | AF | 0.95 (0.76-1.21) | 0.698 (0.88) | 1.05 (0.90-1.23) | 0.510 (0.80) | 0.92 (0.73-1.16) | 0.473 (0.86) | 1.06 (0.90-1.25) | 0.507 (0.77) | 1.05 (0.83-1.32) | 0.713 (0.77) |
| rely | AF | 0.99 (0.67-1.45) | 0.945 (0.97) | 1.11 (0.86-1.43) | 0.427 (0.80) | 1.03 (0.73-1.46) | 0.864 (0.91) | 1.07 (0.81-1.42) | 0.645 (0.82) | 0.89 (0.62-1.28) | 0.523 (0.74) |
| east-afnet4 | AF | 1.03 (0.96-1.11) | 0.339 (0.68) | 0.99 (0.92-1.07) | 0.823 (0.92) | 1.03 (0.94-1.12) | 0.545 (0.86) | 1.01 (0.93-1.09) | 0.815 (0.89) | 0.95 (0.87-1.05) | 0.311 (0.69) |
| cabana-v2 | AF | 1.13 (0.93-1.37) | 0.205 (0.61) | 1.10 (0.93-1.30) | 0.255 (0.74) | 1.03 (0.83-1.28) | 0.812 (0.91) | 1.11 (0.94-1.32) | 0.214 (0.63) | 1.04 (0.78-1.39) | 0.773 (0.82) |
| affirm | AF | 1.16 (1.07-1.25) | 0.000 (0.02) | 1.04 (0.97-1.13) | 0.287 (0.76) | 1.26 (1.14-1.40) | 0.000 (0.00) | 1.11 (1.02-1.21) | 0.013 (0.24) | 1.17 (1.07-1.28) | 0.001 (0.02) |
| af-chf | AF | 1.13 (0.95-1.36) | 0.176 (0.61) | 1.03 (0.85-1.25) | 0.767 (0.92) | 1.13 (0.94-1.37) | 0.188 (0.62) | 1.06 (0.88-1.28) | 0.539 (0.79) | 0.96 (0.81-1.14) | 0.634 (0.77) |
| frail-af | AF | 0.82 (0.59-1.16) | 0.264 (0.68) | 0.81 (0.60-1.09) | 0.164 (0.62) | 0.97 (0.65-1.44) | 0.877 (0.91) | 0.77 (0.56-1.06) | 0.111 (0.53) | 0.92 (0.65-1.29) | 0.616 (0.77) |
| laaos3 | AF | 1.12 (0.73-1.70) | 0.606 (0.88) | 1.04 (0.74-1.46) | 0.827 (0.92) | 0.85 (0.50-1.45) | 0.550 (0.86) | 1.12 (0.73-1.72) | 0.592 (0.81) | 1.22 (0.80-1.86) | 0.356 (0.74) |
| protect-af | AF | 1.51 (0.96-2.38) | 0.074 (0.40) | 0.82 (0.56-1.21) | 0.320 (0.76) | 0.87 (0.57-1.33) | 0.519 (0.86) | 1.08 (0.70-1.65) | 0.740 (0.85) | 0.77 (0.48-1.21) | 0.253 (0.69) |
| raft-af | AF | 1.08 (0.91-1.29) | 0.386 (0.70) | 1.06 (0.88-1.28) | 0.527 (0.80) | 1.14 (0.93-1.40) | 0.213 (0.62) | 1.15 (0.96-1.38) | 0.134 (0.57) | 1.18 (0.96-1.45) | 0.111 (0.69) |
| active-w | AF | 0.73 (0.57-0.94) | 0.016 (0.15) | 0.89 (0.71-1.12) | 0.315 (0.76) | 0.75 (0.58-0.96) | 0.024 (0.19) | 0.80 (0.63-1.02) | 0.076 (0.53) | 0.78 (0.61-1.00) | 0.052 (0.59) |
| comet | HF | 0.94 (0.83-1.06) | 0.320 (0.68) | 1.11 (0.98-1.27) | 0.106 (0.57) | 1.15 (1.00-1.31) | 0.042 (0.27) | 1.06 (0.94-1.21) | 0.340 (0.76) | 1.09 (0.95-1.24) | 0.206 (0.69) |
| paradigm-hf-seq | HF | 0.88 (0.79-0.99) | 0.041 (0.31) | 0.96 (0.86-1.08) | 0.546 (0.80) | 0.87 (0.76-1.00) | 0.052 (0.27) | 0.97 (0.86-1.09) | 0.607 (0.81) | 1.04 (0.91-1.18) | 0.615 (0.77) |
| transform-hf | HF | 0.98 (0.76-1.27) | 0.893 (0.96) | 0.91 (0.68-1.23) | 0.547 (0.80) | 0.77 (0.59-1.01) | 0.057 (0.27) | 0.88 (0.67-1.16) | 0.357 (0.76) | 0.83 (0.64-1.09) | 0.184 (0.69) |
| elite-ii | HF | 1.00 (0.82-1.22) | 0.990 (0.99) | 1.18 (0.96-1.44) | 0.112 (0.57) | 1.12 (0.90-1.39) | 0.307 (0.73) | 1.09 (0.89-1.34) | 0.398 (0.76) | 1.04 (0.85-1.28) | 0.694 (0.77) |
| emperor-preserved-v2 | HF | 0.97 (0.80-1.16) | 0.713 (0.88) | 1.12 (0.93-1.33) | 0.227 (0.74) | 1.37 (1.11-1.70) | 0.003 (0.06) | 1.10 (0.92-1.33) | 0.304 (0.76) | 1.13 (0.91-1.40) | 0.256 (0.69) |
| empa-reg | DM | 1.08 (0.93-1.27) | 0.317 (0.68) | 1.13 (0.96-1.32) | 0.137 (0.58) | 1.01 (0.85-1.22) | 0.878 (0.91) | 1.15 (0.98-1.35) | 0.082 (0.53) | 1.04 (0.86-1.26) | 0.697 (0.77) |
| carolina | DM | 0.95 (0.78-1.17) | 0.657 (0.88) | 1.03 (0.84-1.27) | 0.772 (0.92) | 1.17 (0.95-1.44) | 0.145 (0.60) | 1.01 (0.83-1.24) | 0.893 (0.92) | 1.08 (0.86-1.37) | 0.506 (0.74) |
| leader | DM | 0.90 (0.66-1.22) | 0.502 (0.79) | 1.00 (0.75-1.33) | 0.984 (0.98) | 1.04 (0.73-1.47) | 0.834 (0.91) | 1.03 (0.76-1.40) | 0.848 (0.89) | 0.86 (0.58-1.28) | 0.453 (0.74) |
| sustain6 | DM | 0.85 (0.62-1.18) | 0.335 (0.68) | 1.11 (0.85-1.44) | 0.439 (0.80) | 1.47 (1.05-2.06) | 0.025 (0.19) | 0.95 (0.72-1.25) | 0.694 (0.82) | 0.93 (0.65-1.35) | 0.706 (0.77) |
| rewind | DM | 0.97 (0.80-1.17) | 0.721 (0.88) | 0.97 (0.81-1.16) | 0.746 (0.92) | 0.99 (0.81-1.21) | 0.911 (0.91) | 0.96 (0.81-1.15) | 0.673 (0.82) | 0.86 (0.69-1.09) | 0.211 (0.69) |
| declare | DM | 0.99 (0.85-1.15) | 0.876 (0.96) | 1.13 (0.98-1.30) | 0.104 (0.57) | 1.05 (0.88-1.26) | 0.566 (0.86) | 1.14 (0.98-1.33) | 0.083 (0.53) | 0.93 (0.76-1.13) | 0.458 (0.74) |
| canvas | DM | 0.84 (0.61-1.17) | 0.305 (0.68) | 1.00 (0.75-1.32) | 0.975 (0.98) | 1.02 (0.71-1.48) | 0.904 (0.91) | 0.83 (0.59-1.17) | 0.290 (0.76) | 0.85 (0.56-1.31) | 0.465 (0.74) |
| tecos | DM | 0.97 (0.82-1.14) | 0.704 (0.88) | 1.05 (0.91-1.22) | 0.489 (0.80) | 1.10 (0.92-1.31) | 0.279 (0.71) | 1.07 (0.91-1.25) | 0.410 (0.76) | 1.00 (0.83-1.20) | 0.998 (1.00) |
| carmelina | DM | 0.85 (0.65-1.10) | 0.209 (0.61) | 0.95 (0.74-1.21) | 0.665 (0.92) | 0.93 (0.71-1.20) | 0.557 (0.86) | 0.91 (0.72-1.16) | 0.450 (0.76) | 0.79 (0.60-1.04) | 0.088 (0.67) |
| life | HTN | 1.03 (0.82-1.31) | 0.787 (0.93) | 1.18 (0.98-1.43) | 0.075 (0.57) | 1.03 (0.82-1.29) | 0.810 (0.91) | 1.15 (0.93-1.43) | 0.200 (0.63) | 1.11 (0.85-1.45) | 0.446 (0.74) |
| allhat | HTN | 0.95 (0.83-1.09) | 0.491 (0.79) | 1.02 (0.91-1.14) | 0.708 (0.92) | 0.94 (0.82-1.08) | 0.368 (0.82) | 0.98 (0.88-1.10) | 0.761 (0.85) | 0.94 (0.82-1.08) | 0.396 (0.74) |
| value | HTN | 1.10 (1.02-1.19) | 0.011 (0.14) | 1.13 (1.05-1.22) | 0.001 (0.03) | 1.06 (0.98-1.15) | 0.158 (0.60) | 1.11 (1.02-1.20) | 0.012 (0.24) | 1.14 (1.05-1.25) | 0.002 (0.05) |
| ascot | HTN | 1.01 (0.88-1.16) | 0.911 (0.96) | 1.11 (0.99-1.24) | 0.083 (0.57) | 1.01 (0.88-1.16) | 0.835 (0.91) | 1.04 (0.92-1.18) | 0.483 (0.76) | 1.09 (0.93-1.28) | 0.270 (0.69) |
| insight | HTN | 1.14 (0.85-1.52) | 0.379 (0.70) | 1.02 (0.77-1.36) | 0.876 (0.93) | 0.96 (0.70-1.32) | 0.804 (0.91) | 1.15 (0.85-1.54) | 0.364 (0.76) | 0.80 (0.57-1.12) | 0.194 (0.69) |
| plato | ACS/post-MI | 1.16 (0.99-1.35) | 0.063 (0.40) | 1.08 (0.95-1.24) | 0.248 (0.74) | 1.05 (0.90-1.23) | 0.529 (0.86) | 1.12 (0.97-1.29) | 0.111 (0.53) | 1.11 (0.94-1.32) | 0.202 (0.69) |
| valiant | ACS/post-MI | 1.25 (0.92-1.72) | 0.156 (0.61) | 1.13 (0.86-1.48) | 0.367 (0.77) | 1.13 (0.79-1.61) | 0.499 (0.86) | 1.11 (0.84-1.47) | 0.450 (0.76) | 1.03 (0.75-1.42) | 0.848 (0.87) |
| ontarget | Other | 1.05 (0.98-1.12) | 0.204 (0.61) | 1.06 (0.99-1.13) | 0.121 (0.57) | 1.01 (0.94-1.09) | 0.752 (0.91) | 1.07 (1.00-1.15) | 0.047 (0.53) | 1.03 (0.95-1.11) | 0.489 (0.74) |
| precision | Other | 1.13 (0.94-1.37) | 0.200 (0.61) | 1.02 (0.87-1.21) | 0.773 (0.92) | 1.15 (0.91-1.45) | 0.250 (0.68) | 1.05 (0.88-1.24) | 0.616 (0.81) | 0.93 (0.74-1.18) | 0.554 (0.75) |
| amplify | Other | 0.93 (0.74-1.17) | 0.539 (0.82) | 1.02 (0.83-1.26) | 0.856 (0.93) | 0.94 (0.71-1.25) | 0.664 (0.91) | 1.01 (0.81-1.25) | 0.941 (0.94) | 1.13 (0.90-1.43) | 0.293 (0.69) |
| lodestar | Other | 1.01 (0.92-1.11) | 0.848 (0.96) | 1.03 (0.95-1.12) | 0.466 (0.80) | 1.12 (1.02-1.25) | 0.024 (0.19) | 1.03 (0.95-1.13) | 0.460 (0.76) | 1.06 (0.95-1.18) | 0.299 (0.69) |
| prove-it | Other | 1.36 (1.10-1.69) | 0.005 (0.10) | 1.11 (0.90-1.36) | 0.346 (0.77) | 0.97 (0.76-1.25) | 0.844 (0.91) | 1.15 (0.92-1.45) | 0.216 (0.63) | 1.12 (0.87-1.44) | 0.397 (0.74) |
