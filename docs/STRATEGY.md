# Study strategy — unstructured information for confounding control in TTE

Last updated: 2026-09-23. Status: **proposed, not frozen.** Requires Ryan's sign-off
before any outcome analysis (AGENTS.md: no tuning toward RCT effects). Evidence below
is exploratory: the held-out design and PCA settings were chosen after viewing balance.

## Aim
Show that adding unstructured information (ECG waveform embeddings, EHR foundation-model
embeddings, ECG/echo/note text) to confounding adjustment moves observational estimates
closer to published RCT results, across ~10 cardiovascular trials (RCT-DUPLICATE style,
Wang et al. JAMA 2023). Each trial need not replicate on its own. The claim is statistical,
across trials: directional and numerical agreement improves.

## What COMET has taught us (2026-09-23)
Population: carvedilol vs metoprolol tartrate. n = 6,103 have both ECG and CLMBR embeddings.
Script: `scripts/diag_matching_strategies.py`.

All numbers are means over 5 MICE imputations. "ECG" = BCL lead_time_transformer after the µV
input-scale fix (`scripts/bcl_embed_uv.py`). Pre-fix numbers are in brackets.
Source: `/mnt/raid0/rbc58/ecg-tte/audits/claude-matching-diagnostic-uvfix/summary_pooled_5imp.csv`.

| Method | Pairs | Max SMD (32 covs) | LVEF SMD | AF SMD |
|---|---|---|---|---|
| Unmatched | 2542 | 0.61 | 0.61 | 0.53 |
| Cosine NN on ECG / CLMBR / concat (any preprocessing) | 2542 | 0.54–0.59 | 0.54–0.59 | 0.48–0.52 |
| PS on ECG PCs only | 2065 | 0.42 [0.54] | 0.42 | 0.38 |
| PS on ECG+CLMBR PCs only | 1721 | 0.38 [0.43] | 0.38 | 0.30 |
| PS: all clinical covariates | 1861 | 0.050 | 0.046 | 0.015 |
| PS: clinical + ECG + CLMBR PCs | 1591 | 0.046 | 0.024 | 0.032 |
| PS-caliper → ECG cosine (hybrid) | 2009 | 0.060 | 0.058 | 0.055 |
| **PS: claims-only (EF/labs/vitals withheld)** | 2117 | 0.56 | 0.56 | 0.05 |
| **PS: claims + ECG PCs** | 1825 | 0.42 [0.50] | 0.42 | 0.02 |
| **PS: claims + CLMBR PCs** | 1791 | 0.45 | 0.45 | 0.02 |
| **PS: claims + ECG + CLMBR PCs** | 1668 | 0.37 [0.42] | 0.37 | 0.01 |

Findings:
1. **Matching on embedding distance alone does not balance confounders**, whatever the
   preprocessing. Nearest neighbours in a 256–768-D space are close on "everything a
   little", not on the few variables that drive treatment choice. Drop it as a primary
   method.
2. **When covariates are rich, PSM already reaches SMD < 0.1.** Embeddings cannot show a
   gain on measured covariates that are already balanced. SMD < 0.1 on measured
   covariates is necessary but cannot by itself show value.
3. **The informative test is held-out covariate balance.** Withhold a strong confounder
   (LVEF, labs) from the PS, as a claims database would, and check whether the
   unstructured features recover it. CLMBR + fixed-ECG PCs cut held-out LVEF SMD
   0.56 → 0.37 (~35%), and the CLMBR run saw no numeric values.
4. **The ECG embeddings used before 2026-09-23 were broken by an input-scale bug.**
   BCL checkpoints were trained on µV input, but `all_ecgs` is stored in mV. In eval mode
   BatchNorm therefore saw ~1000x-too-small inputs and every ECG collapsed to the same
   vector. Fixed by `scripts/bcl_embed_uv.py` (x1000). Also pass a formats CSV with
   no 250 Hz flags, because all_ecgs is already 500 Hz. Post-fix COMET probes: sex 0.81,
   age≥65 0.80, AF 0.75, LVEF≤40 0.69. Pre-fix symptoms, for the record:
   - BCL `lead_time_transformer_08_26_2026`: all vectors point the same way
     (‖mean unit vector‖ = 0.999995). Even centred, linear-probe AUCs are sex 0.69,
     AF 0.62, LVEF ≤ 40 0.59.
   - June stage2 embeddings used an `ecg_biometric` checkpoint, which learns
     person-identity features that are invariant to clinical state.
   - 24 MUSE interval + diagnosis-text features beat the BCL embedding on AF (0.77).
   The fixed ECG embedding now beats CLMBR on held-out LVEF, but LVEF recovery is still
   partial (0.56 → 0.42). A supervised EF-aware ECG model is the obvious next lever
   (see `docs/ECG_MODEL.md`).
   → Every embedding must pass `scripts/embedding_utils.py::probe_gate` before use.

## Update: phenotype heads, MUSE text, native CLMBR, observed-only LVEF (2026-09-23, later)
Held-out design, means over 5 imputations. The PS withholds EF/labs/vitals. "Observed" LVEF SMD
uses only measured (non-imputed) LVEF; imputation dilutes the signal. Source:
`audits/claude-matching-diagnostic-v3-{codeonly,native}/summary_pooled_5imp.csv`.

| PS covariates (claims-like base) | Pairs | LVEF SMD (MICE) | **LVEF SMD (observed)** | AF SMD |
|---|---|---|---|---|
| Unmatched | 2542 | 0.61 | 0.57 | 0.53 |
| Claims only | 2117 | 0.56 | 0.52 | 0.05 |
| + MUSE intervals/text (24) | 1921 | 0.51 | 0.43 | 0.03 |
| + ECG phenotype scores (5; out-of-cohort heads) | 1877 | 0.42 | 0.30 | 0.03 |
| + ECG PCs (32) | 1825 | 0.42 | 0.31 | 0.02 |
| + CLMBR code-only PCs (64) | 1791 | 0.45 | 0.36 | 0.02 |
| + CLMBR native-numeric PCs (64) | 1820 | 0.46 | 0.38 | 0.03 |
| + ECG PCs + CLMBR code-only | 1668 | 0.37 | 0.25 | 0.01 |
| **+ ECG + CLMBR code-only + MUSE + phenotypes** | 1610 | 0.35 | **0.22** | 0.01 |
| Reference: full clinical PS (EF/labs/vitals included) | 1861 | 0.05 | 0.02 | 0.02 |

Reading:
- Unstructured features recover about 60% of the observed-LVEF imbalance that claims
  covariates miss (0.52 → 0.22). They don't reach < 0.1. Measured EF remains the
  gold-standard adjuster where it's available.
- Five supervised ECG phenotype scores (out-of-cohort heads: LVEF≤40 AUC 0.90, AF 0.95) do as
  well as 32 PCs, so they're a compact, interpretable PS input.
- Native-numeric CLMBR is **not** better than code-only here (0.38 vs 0.36). There's no
  evidence that numeric tokens help this model.
- More PS dimensions lower retention (2117 → 1610 pairs). Report retention alongside
  balance.
- Implication for the multi-trial study: the value of unstructured data should be largest
  in trials where key confounders are poorly measured. For example, echo EF within 365 d is
  available for only 11–42% in AF and T2D trials, vs ~50% in HF/ACS trials
  (`docs/TRIAL_FEASIBILITY_2026_09_23.md`). That is a testable, pre-specifiable prediction.

## Final method ladder (identical for every trial)
| # | Arm | Covariates in PS | Role |
|---|---|---|---|
| M0 | Unadjusted | — | floor |
| M1 | Claims-like PSM | demographics, dx, meds, utilisation | RCT-DUPLICATE analogue |
| M2 | Rich PSM | M1 + EF, labs, vitals (MICE) | best structured |
| M3 | M1 + unstructured | M1 + ECG PCs + EHR-embedding PCs (+ ECG text flags) | main test A |
| M4 | M2 + unstructured | M2 + same | main test B |
| S1 | PS-caliper → embedding cosine hybrid | M2 PS caliper, then cosine | sensitivity |
| S2 | IPTW (stabilised, trimmed) versions of M1–M4 | — | sensitivity |

Embedding inputs to the PS: centred PCA scores (k = 32 ECG, 64 EHR), fixed in advance. Optional
extension: supervised reduction (cross-fitted embedding → treatment/outcome score), reported
separately.

## Pre-specified evaluation
Per trial:
- Balance: max and mean |SMD| over all covariates, target < 0.1 (0.15 tolerated).
- Held-out balance: SMD on EF/labs/vitals under M1 vs M3.
- Effect: HR with 95% CI.

Across trials (the headline), for each method vs published RCT HR, following RCT-DUPLICATE:
- Pearson r of log-HRs.
- Estimate agreement (emulated HR inside the RCT CI).
- Regulatory agreement (same direction and significance).
- Standardised difference.
- Mean |log-HR difference|.

Paired comparison M3 vs M1 and M4 vs M2 across trials (Wilcoxon on |log-HR diff|).

Guardrails:
- No outcome data before balance is locked.
- Caliper, k and covariate sets are fixed before looking at any HR.
- Report every trial attempted, not only the ones that look good.

## Trial selection (~10)
Criteria:
- ≥ 300 per arm after I/E.
- ≥ 70% ECG coverage within 90 d before index.
- An active-comparator design feasible in Yale data.
- A published HR exists.

Screen run 2026-09-23 on OMOP gold (`docs/TRIAL_FEASIBILITY_2026_09_23.md`). All 15
candidates have ≥ 300 per arm. Only the ACS and HF trials approach 70% ECG coverage within
90 d. Proposed ten (active-comparator RCTs first):
1. PLATO
2. TRITON
3. COMET
4. PARADIGM-HF
5. ARISTOTLE
6. ROCKET-AF
7. RE-LY
8. CAROLINA
9. EMPA-REG
10. DECLARE or TECOS

Open decisions:
- **ECG criterion.** Either relax it to 365 d, or analyse the ECG-available subpopulation
  with all methods on the same denominator.
- **Index-day ECGs.** Is an index-day ECG pre-treatment? Excluding the index day drops
  PLATO's coverage from 0.83 to 0.54.
- **Placebo-controlled trials** need an active comparator, so their published HRs are
  only an indirect benchmark.

## Workstreams
1. **ECG representation.** Scale fix done. Next, add supervised disease-probability
   features and/or train a multi-task model. See `docs/ECG_MODEL.md`.
2. **EHR representation.** Rerun CLMBR with numeric values (currently code-only). Consider
   motor/other FEMR models.
3. **Code consolidation.** Done on `consolidate-2026-09-23`: `psm-mice-imputation` plus
   `codex/comet-outcomes`. `bio-embed-lvsd` (July, 5 commits) has not been merged yet.
4. **Generalise to ~10 trials.** Implement M0–M4 behind an explicit new contract. Do not
   revive the archived stage4/stage5 scripts (AGENTS.md archive boundary).
