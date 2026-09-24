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

## Core result: long-tail balance (2026-09-23; answers "is it more than an EF imputer?")
Question: a PS balances what it is given. Does adding representations improve balance on the
**rest of the pre-treatment record** that the PS leaves out?

Design:
- Evaluation panel: 1,208 pre-index OMOP features (365 d to 1 d before index): 232 dx,
  187 drugs, 722 procedures, 61 labs (value + measured flag) and visit counts
  (`scripts/build_preindex_panel.py`).
- The panel is split per domain into pool A (hdPS may select from it) and pool B
  (evaluation only; never in any PS).
- hdPS uses exposure-only prioritisation (no outcome).
- Placebo arm: the same number of pure-noise features, to control for caliper
  trimming/retention.
- 5 imputations × 3 random splits (`scripts/eval_longtail_balance.py`). Output:
  `audits/claude-longtail-balance/summary_pooled.csv`.

| PS | Pairs | Pool-B features SMD > 0.1 (range over 15 runs) | Mean abs SMD | PS covariates max SMD |
|---|---|---|---|---|
| Unmatched | 2542 | 37.5% (36.5–39.5) | 0.094 | 0.61 |
| Clinical (32 covs) | 1871 | 18.2% (16.8–20.9) | 0.060 | 0.05 |
| Clinical + noise (placebo, 101 dims) | 1821 | 18.0% (15.1–21.1) | 0.060 | 0.05 |
| **Clinical + ECG** (5 phenotype + 32 PCs) | 1712 | **14.7%** (13.5–16.2) | 0.055 | 0.05 |
| **Clinical + CLMBR** (64 PCs) | 1661 | **4.2%** (3.5–5.0) | 0.039 | 0.05 |
| Clinical + ECG + CLMBR | 1585 | 4.1% (2.5–5.3) | 0.038 | 0.04 |
| Clinical + hdPS (100 codes from pool A) | 1402 | 9.1% (4.1–12.9) | 0.047 | 0.05 |
| Clinical + hdPS + ECG + CLMBR | 1210 | 4.1% (1.6–7.2) | 0.038 | 0.06 |

Reading (exploratory, COMET only):
1. A rich structured PS still leaves ~18% of the broader pre-treatment record imbalanced.
   The noise placebo changes nothing, so the gains below are not a trimming artefact.
2. **CLMBR works like a learned hdPS.** It cuts residual long-tail imbalance ~77%. It beats
   empirical hdPS on balance (4.2% vs 9.1%) and on retention (1661 vs 1402 pairs), with no
   code selection. It is also far more stable across splits.
3. **ECG adds information orthogonal to codes.** It never sees codes yet cuts long-tail
   imbalance ~20%, with non-overlapping ranges vs clinical-only. It also specifically
   recovers physiologic confounders that codes miss (held-out observed LVEF, section below).
   On a code-heavy panel it adds little beyond CLMBR.
4. Caveats:
   - CLMBR's input includes coded history (a superset of the panel window), so its gain on
     coded features is partly by construction. hdPS has the same property, and CLMBR still
     beats it.
   - Balance is not bias. The link to effect accuracy must be shown with negative-control
     outcomes and RCT agreement.

**Proposed story.** Structured PSM balances what it is given but not the rest of the record.
- EHR foundation-model embeddings balance the coded record better than hdPS.
- ECG embeddings add physiologic information that no code set contains.
- Across trials, does this better balance translate into estimates closer to the RCT?
- Before scaling: replicate this long-tail test on 2–3 more trials (PLATO, PARADIGM-HF,
  ARISTOTLE) and add negative-control outcomes.

## Replication: PARADIGM-HF + COMET under the v2 evaluator (2026-09-23, later)
Contract: `docs/DECISIONS.md` ("Multi-trial replication contract v1"). Commands:
`docs/RUN_LONGTAIL_REPLICATION.md`. Outputs: `audits/claude-longtail-v2-{comet,paradigm}/summary_pooled.csv`.
Setup:
- 5 imputations × 5 splits.
- hdPS v2 uses once/sporadic/frequent levels with k = 100/200/500, exposure-only ranking.
- Exposure-defining features (prior orders of the study drugs) are removed from hdPS candidates,
  pool B and the C-statistic.
- Chance = the expected share of |SMD| > 0.1 in a randomised sample of the same size.
- Prog = |SMD| of the external prognostic score (core + full panel; 1-y death/HF hospitalisation;
  fit on 30K HF patients outside each cohort).
- C = post-matching CV C-statistic of treatment on core + pool-B features (0.5 = indistinguishable).

PARADIGM-HF (adapted): ARNI vs ACEi, n = 4,203 with ECG + CLMBR (2,182 / 2,021). The arms differ
mostly by calendar year (SMD 0.91), so retention is about 50%.

| PS (PARADIGM) | Pairs | Pool-B > 0.1 (range) | Excess over chance | Prog | C |
|---|---|---|---|---|---|
| Unmatched | 2182 | 31.8% | 31.7% | 0.017 | 0.85 |
| Clinical + noise101 (placebo) | 1061 | 25.8% (21.2–34.0) | 23.7% | 0.026 | 0.68 |
| Clinical | 1096 | 25.9% (23.2–28.8) | 24.0% | 0.019 | 0.69 |
| Clinical + ECG | 916 | 21.4% (16.4–25.3) | 18.2% | 0.030 | 0.65 |
| Clinical + CLMBR | 894 | 10.1% (6.6–13.3) | 6.6% | 0.080 | 0.59 |
| Clinical + ECG + CLMBR | 806 | 10.3% (7.5–14.9) | 5.9% | 0.067 | 0.58 |
| Clinical + hdPS100 (v1 any-use) | 920 | 11.4% (7.9–15.8) | 8.2% | 0.024 | 0.62 |
| Clinical + hdPS100 (v2 levels) | 948 | 13.7% (10.6–17.6) | 10.7% | 0.019 | 0.63 |
| Clinical + hdPS200 | 875 | 10.7% (7.7–14.1) | 7.0% | 0.027 | 0.61 |
| Clinical + hdPS500 | 734 | 7.0% (4.8–9.8) | 1.5% | 0.018 | 0.55 |
| Clinical + hdPS200 + ECG + CLMBR | 699 | 8.0% (5.2–12.2) | 1.8% | 0.042 | 0.53 |
| Claims + ECG + CLMBR | 821 | 14.0% | 9.7% | 0.041 | 0.60 |
| Claims + hdPS200 | 898 | 10.7% | 7.3% | 0.019 | 0.63 |
| Demo + CLMBR / Demo + hdPS200 | 968 / 942 | 9.5% / 9.7% | 6.7% / 6.7% | 0.107 / 0.044 | 0.66 / 0.67 |

COMET rerun under v2 (same cohort and embeddings as the v1 table above; the v1 dictionary keeps
the v1 splits):

| PS (COMET) | Pairs | Pool-B > 0.1 (range) | Excess over chance | Prog | C |
|---|---|---|---|---|---|
| Clinical | 1871 | 17.9% (15.4–22.5) | 17.7% | 0.067 | 0.64 |
| Clinical + ECG | 1712 | 14.5% (13.2–17.3) | 14.2% | 0.067 | 0.61 |
| Clinical + CLMBR | 1661 | 3.8% (3.0–4.7) | 3.4% | 0.031 | 0.58 |
| Clinical + ECG + CLMBR | 1585 | 3.7% (2.2–5.0) | 3.2% | 0.021 | 0.57 |
| Clinical + hdPS100 (v1 any-use, exposure codes removed) | 1663 | 4.4% (1.9–6.1) | 4.0% | 0.038 | 0.59 |
| Clinical + hdPS200 | 1616 | 3.9% (1.6–6.1) | 3.4% | 0.028 | 0.58 |
| Clinical + hdPS500 | 1444 | 2.1% (0.9–4.6) | 1.3% | 0.033 | 0.55 |
| Clinical + hdPS200 + ECG + CLMBR | 1457 | 1.4% (0.6–2.2) | 0.7% | 0.018 | 0.53 |
| Claims + ECG + CLMBR | 1652 | 3.8% | 3.4% | 0.027 | 0.61 |
| Claims + hdPS200 | 1752 | 3.6% | 3.3% | 0.057 | 0.64 |

Reading (exploratory):
1. **Replicates.**
   - A rich clinical PS leaves a large share of the pre-index record imbalanced (18% COMET, 26%
     PARADIGM), and the noise placebo reproduces it.
   - CLMBR removes most of it (−79% / −61%). ECG alone gives a smaller, consistent gain
     (−19% / −17%).
   - The C-statistic and pool-B share rank methods the same way in both trials.
2. **Does not replicate: "CLMBR beats hdPS".**
   - The v1 COMET hdPS100 (9.1% at 1,402 pairs) was handicapped: it selected prior orders of
     the study drugs themselves (`rx_carvedilol`, `rx_metoprolol`), which are near-instruments.
   - With those removed, hdPS100 gives 4.4% at 1,663 pairs, the same as CLMBR (3.8% at 1,661).
   - In PARADIGM, CLMBR ≈ hdPS200 (10.1% vs 10.7%, similar retention). hdPS500 is better on
     long-tail balance in both trials, at lower retention.
   - The earlier claim "ECG + CLMBR beats hdPS at every base" is withdrawn.
3. **The combination is best in both trials.** hdPS + ECG + CLMBR comes close to the chance
   floor (excess about 1–2%), at 30–40% lower retention than the clinical PS.
4. **Prognostic-score balance does not separate the methods.** Every adjusted PS gives
   |SMD| < 0.1. In PARADIGM, adding CLMBR slightly worsens it (0.019 → 0.080). In COMET it
   improves it (0.067 → 0.031).
5. **LVEF recovery is not testable in PARADIGM.** EF > 40 is excluded and unmatched LVEF SMD is
   only 0.08. The ECG-for-physiology finding rests on COMET alone: claims + ECG takes held-out
   LVEF from 0.56 to 0.41, while hdPS does not recover it (claims + hdPS200: 0.48).

PLATO (adapted): ticagrelor vs clopidogrel, n = 6,759 with ECG + CLMBR (4,011 / 2,748).
Source: `audits/claude-longtail-v2-plato/summary_pooled.csv`.

| PS (PLATO) | Pairs | Pool-B > 0.1 (range) | Excess over chance | Prog | C |
|---|---|---|---|---|---|
| Unmatched | 2748 | 58.0% | 58.0% | 0.127 | 0.79 |
| Clinical + noise101 (placebo) | 1851 | 14.2% | 14.0% | 0.032 | 0.61 |
| Clinical | 1883 | 14.9% (11.8–17.9) | 14.7% | 0.021 | 0.61 |
| Clinical + ECG | 1896 | 14.3% (12.1–16.5) | 14.1% | 0.028 | 0.61 |
| Clinical + CLMBR | 1809 | 10.1% (7.4–12.1) | 9.8% | 0.019 | 0.59 |
| Clinical + ECG + CLMBR | 1813 | 10.0% (8.4–11.1) | 9.8% | 0.015 | 0.59 |
| Clinical + hdPS100 | 1779 | 3.8% (2.3–5.1) | 3.5% | 0.032 | 0.56 |
| Clinical + hdPS200 | 1728 | 2.5% (1.4–4.2) | 2.2% | 0.029 | 0.55 |
| Clinical + hdPS500 | 1556 | 1.4% (0.5–2.6) | 0.9% | 0.028 | 0.52 |
| Clinical + hdPS200 + ECG + CLMBR | 1660 | 2.1% (1.2–3.0) | 1.7% | 0.017 | 0.53 |
| Demo + CLMBR / Demo + hdPS200 | 2130 / 1941 | 15.7% / 3.0% | 15.6% / 2.8% | 0.133 / 0.131 | 0.70 / 0.69 |

In PLATO the result reverses:
- hdPS beats CLMBR clearly at the same retention.
- ECG adds nothing to long-tail balance.
- The residual imbalance after clinical + CLMBR is dominated by index-admission CABG markers:
  CABG CPT/PCS codes, cardiopulmonary bypass, anesthesia for CABG, protamine, blood crossmatch.
  Clopidogrel is preferred around CABG. Recent, procedure-driven confounding is what the
  last-token CLMBR representation does not capture and exposure-ranked hdPS does.

ARISTOTLE (adapted): apixaban vs warfarin, n = 18,771 with ECG + CLMBR (15,419 / 3,352).
Source: `audits/claude-longtail-v2-aristotle/summary_pooled.csv`.

| PS (ARISTOTLE) | Pairs | Pool-B > 0.1 (range) | Excess over chance | Prog | C |
|---|---|---|---|---|---|
| Unmatched | 3352 | 41.3% | 41.3% | 0.213 | 0.88 |
| Clinical + noise101 (placebo) | 2577 | 19.9% | 19.8% | 0.148 | 0.71 |
| Clinical | 2575 | 20.6% (17.5–23.5) | 20.6% | 0.132 | 0.71 |
| Clinical + ECG | 2589 | 20.3% (17.2–22.8) | 20.2% | 0.141 | 0.70 |
| Clinical + CLMBR | 2282 | 12.6% (9.7–16.4) | 12.5% | 0.182 | 0.64 |
| Clinical + ECG + CLMBR | 2257 | 13.0% (10.1–16.6) | 12.9% | 0.191 | 0.64 |
| Clinical + hdPS100 | 2211 | 4.4% (2.2–5.8) | 4.3% | 0.026 | 0.60 |
| Clinical + hdPS200 | 2163 | 3.7% (1.9–6.9) | 3.6% | 0.024 | 0.58 |
| Clinical + hdPS500 | 2072 | 2.3% (1.1–4.7) | 2.1% | 0.016 | 0.55 |
| Clinical + hdPS200 + ECG + CLMBR | 2011 | 1.0% (0.2–2.2) | 0.9% | 0.027 | 0.53 |
| Demo + CLMBR / Demo + hdPS200 | 2337 / 2201 | 18.4% / 4.3% | 18.4% / 4.2% | 0.137 / 0.079 | 0.66 / 0.61 |

### Four-trial summary (exploratory)
Relative change in the pool-B share with |SMD| > 0.1 versus the clinical PS:

| Arm vs clinical PS | COMET | PARADIGM-HF | PLATO | ARISTOTLE |
|---|---|---|---|---|
| + ECG | −19% | −17% | −3% | −2% |
| + CLMBR | −79% | −61% | −32% | −39% |
| + hdPS100 (v2) | −73% | −47% | −75% | −79% |
| + hdPS200 | −78% | −59% | −83% | −82% |
| + hdPS200 + ECG + CLMBR | −92% | −69% | −86% | −95% |
| Pairs retained, hdPS200 + ECG + CLMBR vs clinical | −22% | −36% | −12% | −22% |

Where it contradicts the COMET story:
1. **CLMBR is not a better high-dimensional adjuster than hdPS.**
   - They tie in the two HF trials, which are chronic, code-rich histories.
   - hdPS wins clearly in ACS and AF.
   - In PLATO the gap is procedural confounding at the index admission (CABG). The frozen
     last-token CLMBR vector does not isolate it.
2. **ECG helps long-tail balance only in the HF trials.** The ECG's value is specific to
   physiologic, LVEF-driven confounding; it is not a general record summary.
3. **CLMBR can worsen prognostic balance.**
   - It worsens it in PARADIGM (0.019 → 0.080) and ARISTOTLE (0.132 → 0.182) while improving
     long-tail balance.
   - In ARISTOTLE the clinical PS leaves the prognostic score imbalanced (0.13); hdPS fixes it
     (0.02–0.03).
   - Long-tail balance and prognostic balance can disagree, so both must be reported.

What holds in all four trials:
- A rich clinical PS leaves 15–26% of the pre-index record imbalanced, and a noise placebo shows
  this is not a trimming artefact.
- Adding ECG + CLMBR to hdPS reduces the residual further, to near the chance floor, at a
  12–36% cost in retained pairs.
- The post-matching C-statistic ranks methods the same way as the pool-B share.

### Sparse PS: demographics + diagnoses ± ECG (2026-09-23, later; exploratory)
Ryan's proposal: a sparse PS of demographics + recorded diagnoses (`dx`), with no medications,
utilisation, procedures, EF, labs or vitals, plus ECG. `ECGpc` = 32 centred BCL principal
components only, with no supervised phenotype predictions. `--method-set sparse`; outputs in
`audits/claude-sparse-dx-<trial>/summary_pooled.csv`.

"Phys" = the 9 withheld physiology variables (EF, SBP, DBP, HR, BMI, creatinine, K, Na, Hb),
scored on measured values only.

| Trial | PS | Pairs | Pool-B > 0.1 | Meds > 0.1 (of 6–8) | Phys > 0.1 (of 9) | Phys mean |SMD| | Measured LVEF SMD |
|---|---|---|---|---|---|---|---|
| COMET | dx | 2193 | 27.3% | 4.0 | 3.4 | 0.129 | 0.56 |
| COMET | dx + noise32 (placebo) | 2173 | 27.6% | 4.0 | 3.0 | 0.122 | 0.54 |
| COMET | **dx + ECGpc** | 1929 | 21.6% | 3.4 | 2.4 | 0.092 | **0.34** |
| COMET | dx + hdPS200 + ECGpc | 1654 | 2.6% | 2.4 | 2.2 | 0.076 | 0.22 |
| COMET | full clinical PS | 1871 | 17.9% | 0 | 0 | 0.031 | 0.02 |
| PARADIGM-HF | dx → dx + ECGpc | 1266 → 1015 | 38.4% → 31.1% | 3 → 2 | 4 → 4 | 0.103 → 0.073 | 0.13 → 0.04 |
| PLATO | dx → dx + ECGpc | 2223 → 2240 | 19.5% → 20.2% | 3 → 3 | 2 → 1 | 0.056 → 0.056 | 0.06 → 0.05 |
| ARISTOTLE | dx → dx + ECGpc | 2621 → 2629 | 23.8% → 24.0% | 0 → 0 | 3 → 2 | 0.095 → 0.075 | 0.05 → 0.05 |

Reading:
- **In HF, the ECG recovers part of the physiology that the sparse PS omits.** In COMET,
  measured-LVEF imbalance falls from 0.56 to 0.34 (−40%), and mean physiology imbalance falls
  about 30%. The placebo changes nothing.
- **Raw ECG PCs do almost as well as PCs + phenotype predictions** (COMET LVEF 0.34 vs 0.32), so
  the ECG effect does not depend on supervised predicted values.
- **ECG does not substitute for medications or utilisation.** It is also not a general sickness
  summary in ACS/AF, where it changes nothing.
- In PLATO and ARISTOTLE there is little physiologic imbalance to recover (unmatched phys mean
  0.09–0.11). They cannot test the ECG's value, only its lack of harm.
- The full clinical PS remains far better on physiology (LVEF 0.02). Sparse + ECG narrows the gap
  but does not close it.

Implication (four trials): the story "embeddings are a better high-dimensional complement than
hdPS" is not supported against a properly specified hdPS. What survives: the representations are a
code-selection-free alternative that is about as good as a tuned hdPS. ECG adds physiologic
balance that codes don't, where the key confounder is physiologic. Stacking hdPS with the
embeddings balances best, at a cost in retention.

## Low-dimensional PS + embeddings vs hdPS (2026-09-23)
Same long-tail design, 5 imputations × 3 splits (`audits/claude-longtail-lowdim/summary_pooled.csv`).
- demo = age, sex, index year.
- claims = the clinical set minus EF/labs/vitals.
- "Clin32 >0.1" = how many of the 32 hand-picked clinical covariates stay imbalanced.

| PS | Pairs | Pool-B SMD > 0.1 | Clin32 > 0.1 (of 32) | LVEF SMD | AF SMD |
|---|---|---|---|---|---|
| demo | 2448 | 37.4% | 14.4 | 0.58 | 0.47 |
| demo + hdPS100 | 1635 | 11.3% | 10.1 | 0.47 | 0.29 |
| demo + CLMBR | 1883 | 5.4% | 6.4 | 0.48 | 0.37 |
| **demo + ECG + CLMBR** | 1721 | **5.5%** | 8.0 | **0.39** | **0.28** |
| claims + hdPS100 | 1514 | 8.9% | 3.5 | 0.48 | 0.04 |
| **claims + ECG + CLMBR** | 1652 | **4.3%** | 3.0 | **0.36** | 0.02 |
| clinical + hdPS100 | 1402 | 9.1% | 0 | 0.03 | 0.03 |
| **clinical + ECG + CLMBR** | 1585 | **4.1%** | 0 | 0.04 | 0.02 |

Reading:
- **At every base level, ECG+CLMBR beats hdPS.** It gives better long-tail balance (about half the
  residual), better LVEF balance and higher retention.
- **With a demographics-only base, CLMBR matches the long-tail balance of a rich base.** But
  6–8 of the 32 key confounders stay imbalanced, and LVEF/AF don't reach < 0.1.
- Embeddings are therefore **a better high-dimensional complement than hdPS, not a substitute
  for investigator-specified core confounders.** Proposed design: core clinical confounders +
  embeddings (in place of, or on top of, hdPS).

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

Decided by Ryan (2026-09-23): relax the ECG window to 365 d; index-day ECG counts as pre-treatment.
Previously open:
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
