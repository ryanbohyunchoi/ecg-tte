# ECG-TTE: final results — balance (phase 1) and effect estimates (phase 2)

**Date:** 2026-09-25 (overnight run). For Ryan. Aggregates only.

**Protocol:** `docs/PROTOCOL_V1.md` (tag `protocol-v1`), amended before any outcome extraction by
`docs/PROTOCOL_V1_1_AMENDMENT.md` (tag `protocol-v1.1`) and `docs/PROTOCOL_V1_2_AMENDMENT.md`
(tag `protocol-v1.2`). Phase 2 ran once, from commit `043740e` (= `protocol-v1.2`).

**Earlier reports:** `docs/REPORT_V3_2026_09_24.md`, `docs/REPORT_OVERNIGHT_2026_09_24.md`.

---

## 1. Bottom line

1. **Balance: the ECG captures cardiac structure and function that codes miss.**
   - In the physiology trials (primary set, all initiators; echo scored from 2016-07-31), raw ECG
     embeddings added to a codes-only PS raised capture of echo LV structure from 47% to 81% and
     of measured core physiology from 19% to 48%.
   - That is at or above what hdPS achieves for LV structure (63%). hdPS remains far better for
     the coded record (medications 83%, rest of record 87%).
   - Combining hdPS and the ECG gives the best capture of LV structure (87%). It even exceeds the
     full-data clinical PS (70%), which contains measured EF.
   - The ECG does **not** capture valve disease (20% → 5%).
2. **The specificity hypothesis (H2) is only partly supported after the audit fixes.**
   - The ECG's gain on core physiology is larger in physiology trials than in controls (p = 0.026).
   - For LV structure the difference is borderline (p = 0.089; p = 0.015 in the post-2016
     sensitivity cohort).
   - For LV function it is not supported (p = 0.33).
3. **Effect estimates: better balance did not produce estimates closer to the RCTs (H5 not
   supported).** Across the 10 primary-set trials:

   | Arm | Mean \|log HR − RCT\| | Estimate agreement |
   |---|---|---|
   | Sparse PS | 0.127 | 7/10 |
   | Sparse + ECG | 0.128 | 6/10 |
   | hdPS200 | 0.164 | 6/10 |
   | hdPS200 + ECG | 0.147 | 6/10 |
   | Full-data clinical PS | 0.122 | 7/10 |
   | Unadjusted | 0.241 | 3/10 |

   - No paired comparison is significant (p = 0.23–0.92).
   - Any PS adjustment roughly halves the error of the unadjusted estimate. Beyond that, adding
     the ECG, hdPS or even measured EF/labs does not move estimates closer to the RCT on average.
   - The only favourable signal is small and exploratory: in the six "close" emulations, sparse +
     ECG has the lowest error (0.074 vs 0.093 for sparse).
4. **Negative controls show no systematic residual confounding in any arm:** 1–4 of 30 CIs exclude
   1 per arm, as expected by chance. The estimates are imprecise, though (mean |log HR| ≈ 0.3).
5. **For the paper,** a defensible framing is:
   - *mechanism and balance:* what a routine ECG adds to a code-based PS, and which confounders it
     captures (LV structure/function) and misses (valves);
   - *a negative effect finding:* in 10 emulations, these balance improvements did not measurably
     improve agreement with RCT estimates.

   The effect comparison is likely underpowered and limited by outcome measurement in the EHR
   (§6.4).

---

## 2. What was done since the last report

1. **Audit** of the whole pipeline, run as parallel reviews:
   - code correctness;
   - reporting consistency;
   - data-level checks (tests, time windows, reproducibility, leakage).

   It found no critical errors, 5 major and 12 minor code issues, and several reporting errors.
2. **Protocol v1.1** (before outcomes) fixed them. Main items:
   - exact PS matcher (the old ±60 window missed matches);
   - switcher exposure features;
   - SHD LVEF leakage mask;
   - echo-data QC;
   - PCI codes;
   - deterministic tie-breaks.

   Your decisions also went in: a **sequential switcher design** for PARADIGM-HF (removes the use
   of future information) and **echo evaluation restricted to index ≥ 2016-07-31 (option A)**,
   plus a sensitivity analysis dropping pre-2016 patients.
3. **Phase 1 re-run:** all 15 trials × 4 populations (primary; outpatient; SHD arms; post-2016).
   That is 59 grids of 25 runs each, all complete.
4. **Pre-run review of the phase-2 code** against the protocol found three bias-relevant issues:
   - index-day deaths;
   - I21 re-coding for 28 days after an MI;
   - index-stay leakage.

   They were fixed as **Protocol v1.2**, and the reviewer's synthetic test cases were re-run and
   behave correctly.
5. **Phase 2:** outcome extraction and Cox estimation (matched, pair-clustered; Rubin's rules over 5
   imputations; overlap weighting as secondary), run once for 14 trials × 4 populations.

---

## 3. Trials and emulation ratings (v1.1, all initiators)

Rubric items: (a) comparator, (b) eligibility, (c) time zero, (d) endpoint, (e) data sufficiency
(clinical-PS pairs). Close ≥ 8, moderate 6–7, limited ≤ 5.

| Trial (adapted) | Role | Comparison (arm 1 vs arm 2) | RCT benchmark (our orientation) | Clinical-PS pairs | Rating | Set |
|---|---|---|---|---|---|---|
| COMET | physiology | metoprolol vs carvedilol | 1.21 (1.08–1.35), death | 2,104 | close (8) | primary |
| PARADIGM-HF, sequential switcher | physiology | ARNI switchers vs ACEi continuers | 0.80 (0.73–0.87), CV death/HF hosp | 1,176 | moderate (7) | primary |
| PARADIGM-HF, new-user | physiology | ARNI vs ACEi | same | 1,159 | moderate (6) | sensitivity (one design per RCT) |
| TRANSFORM-HF | physiology | torsemide vs furosemide | 1.02 (0.89–1.18), death | 697 | moderate (7) | primary |
| ELITE II | physiology | ARB vs ACEi | 1.13 (0.95–1.35), death | 1,174 | close (8) | primary |
| LIFE | physiology | ARB vs cardioselective β-blocker (ECG-LVH) | 0.87 (0.77–0.98), CV death/MI/stroke | 1,232 | close (8) | primary |
| DIONYSOS | physiology | dronedarone vs amiodarone | 1.59 (1.28–1.98) | 751 | moderate (6) | balance only (endpoint not emulable) |
| PLATO | control | ticagrelor vs clopidogrel | 0.84 (0.77–0.92), CV death/MI/stroke | 2,026 | close (9) | primary |
| ARISTOTLE | control | apixaban vs warfarin | 0.79 (0.66–0.95), stroke/SE | 2,791 | close (9) | primary |
| ROCKET-AF | control | rivaroxaban vs warfarin | 0.88 (0.74–1.03) ITT, stroke/SE | 2,062 | close (9) | primary |
| RE-LY | control | dabigatran vs warfarin | 0.66 (0.53–0.82), stroke/SE | 699 | moderate (7) | primary |
| ALLHAT | control | amlodipine vs thiazide | 0.98 (0.90–1.07), CHD death/MI | 8,487 | moderate (7) | primary |
| PARAGON-HF | physiology | ARNI vs valsartan | 0.87 (0.75–1.01) | 310 | limited (5) | supplement |
| DAPA-HF / EMPEROR-R | physiology | SGLT2i vs DPP-4i (placebo proxy) | 0.74 (0.65–0.85) | 376 | limited (4) | supplement |
| PARTNER 2A | physiology | TAVR vs surgical AVR | 0.89 (0.73–1.09), death/stroke | 343 | moderate (7) | supplement |

Not analysed:
- TRITON (feasibility, 278 prasugrel users);
- PARAGON-HF switcher (feasibility);
- the v1 PARADIGM-HF switcher (replaced by the sequential design).

Balance sets: the primary balance set is 11 trials (6 physiology, 5 control). DIONYSOS is in it for
balance; the new-user PARADIGM-HF is excluded under one-design-per-RCT. The primary phase-2 set is
10 trials (without DIONYSOS).

---

## 4. Phase 1: what each PS arm captures (primary, all initiators)

Cells: median % of the pre-matching excess imbalance removed, over the trials with that
imbalance. 100% = balanced to the level of a randomised sample. Echo domains and measured LVEF are
scored for index ≥ 2016-07-31. Full tables: `docs/V11_CAPTURE_MAP_ALL_PRIMARY.md`.

**Physiology trials (n = 6)**

| Domain | Sparse | Sparse + ECG | hdPS200 | hdPS200 + ECG | Clinical PS (reference) |
|---|---|---|---|---|---|
| Medications | 42% | 47% | 83% | 85% | 110% |
| Healthcare use | 45% | 53% | 83% | 92% | 111% |
| Rest of coded record | 35% | 48% | 87% | 91% | 61% |
| Core-9 physiology (EF, vitals, basic labs; measured) | 19% | 48% | 61% | 65% | 98% |
| Echo: LV function | 26% | 49% | 39% | 56% | 83% |
| **Echo: LV structure / wall thickness** | 47% | **81%** | 63% | **87%** | 70% |
| Echo: diastolic / LA | 68% | 76% | 60% | 77% | 72% |
| Echo: RV / pulmonary pressure | 48% | 63% | 75% | 91% | 49% |
| Echo: valves | 20% | 5% | 52% | 55% | 37% |
| NT-proBNP | 102% | 110% | 107% | 104% | 110% |
| Prognostic risk score | 72% | 73% | 91% | 102% | 88% |
| Median pairs | 1,184 | 1,184 | 1,115 | 1,086 | 1,175 |

**Control trials (n = 5):** the ECG adds little.
- Core-9: 41% → 52%.
- LV structure: 29% → 35%.
- hdPS captures valves (77%) and the coded record (93%).

**Hypothesis tests (pre-specified; one-sided Mann-Whitney on the change in excess from adding the
ECG, physiology vs control):**

| Domain | Physiology (trials improved) | Control (trials improved) | p (primary) | p (post-2016 cohort) |
|---|---|---|---|---|
| Core-9 physiology | −0.029 (6/6) | −0.014 (4/5) | **0.026** | 0.063 |
| LV structure | −0.033 (5/6) | −0.001 (3/5) | 0.089 | **0.015** |
| LV function | −0.004 (3/6) | +0.037 (1/5) | 0.33 | 0.089 |

**Share of the sparse → clinical-PS gap closed (H3; medians pooled over both roles):**

| Domain | + ECG | + hdPS200 | + both |
|---|---|---|---|
| LV structure | 69% | 76% | 108% |
| Core-9 | 24% | 50% | 64% |
| Medications | 7% | 58% | 60% |

**Sensitivities:**
- **Post-2016 cohort:** the same pattern, stronger for LV structure (27% → 94% with the ECG).
- **Outpatient initiators:** the same direction but noisier (about half the pairs).
- **SHD encoder** (PRESENT-SHD signal models; echo and measured LVEF scored outside its training
  set):
  - helps diastolic function (85% vs 28% for the ECG) and RV/pulmonary pressure (88% vs 5%);
  - does not help LV structure (54% vs 79%);
  - improves valves only combined with the ECG (77%), which is noisy.

  Tables: `docs/V11_CAPTURE_MAP_*`.

---

## 5. Phase 2: effect estimates (primary: all initiators, trial horizon, matched)

HR (95% CI), arm 1 vs arm 2. Full per-trial tables: `docs/PHASE2_SUMMARY_ALL.md` and
`docs/phase2_tables/`.

| Trial | RCT | Unadjusted | Sparse | Sparse + ECG | hdPS200 | hdPS200 + ECG | Clinical PS |
|---|---|---|---|---|---|---|---|
| COMET | 1.21 (1.08–1.35) | 1.33 (1.20–1.46) | 1.18 (1.06–1.32) | 1.19 (1.05–1.33) | 1.10 (0.98–1.24) | 1.15 (1.02–1.31) | 1.14 (1.00–1.30) |
| PARADIGM-HF (sequential) | 0.80 (0.73–0.87) | 1.20 (1.10–1.32) | 1.02 (0.91–1.14) | 0.96 (0.86–1.07) | 0.97 (0.87–1.08) | 0.94 (0.84–1.06) | 0.99 (0.86–1.15) |
| TRANSFORM-HF | 1.02 (0.89–1.18) | 0.92 (0.77–1.10) | 0.94 (0.73–1.19) | 0.93 (0.73–1.19) | 1.14 (0.87–1.49) | 1.14 (0.87–1.48) | 0.92 (0.70–1.23) |
| ELITE II | 1.13 (0.95–1.35) | 0.95 (0.80–1.12) | 0.96 (0.79–1.17) | 0.99 (0.82–1.21) | 1.01 (0.82–1.24) | 0.99 (0.81–1.22) | 0.99 (0.81–1.22) |
| LIFE | 0.87 (0.77–0.98) | 0.72 (0.59–0.89) | 0.86 (0.68–1.08) | 0.79 (0.63–1.00) | 0.86 (0.68–1.09) | 0.91 (0.72–1.14) | 0.89 (0.70–1.12) |
| PLATO | 0.84 (0.77–0.92) | 0.70 (0.62–0.79) | 0.79 (0.68–0.91) | 0.85 (0.74–0.98) | 0.90 (0.77–1.05) | 0.93 (0.79–1.09) | 0.91 (0.77–1.08) |
| ARISTOTLE | 0.79 (0.66–0.95) | 0.57 (0.50–0.64) | 0.75 (0.62–0.90) | 0.79 (0.66–0.94) | 0.71 (0.58–0.88) | 0.75 (0.62–0.92) | 0.73 (0.58–0.91) |
| ROCKET-AF | 0.88 (0.74–1.03) | 0.48 (0.40–0.58) | 0.69 (0.56–0.86) | 0.72 (0.58–0.89) | 0.65 (0.52–0.83) | 0.76 (0.60–0.96) | 0.73 (0.57–0.94) |
| RE-LY | 0.66 (0.53–0.82) | 0.69 (0.51–0.92) | 0.82 (0.57–1.18) | 0.99 (0.68–1.43) | 1.04 (0.70–1.53) | 1.20 (0.79–1.81) | 0.82 (0.53–1.25) |
| ALLHAT | 0.98 (0.90–1.07) | 1.32 (1.17–1.48) | 1.16 (1.01–1.33) | 1.15 (1.00–1.32) | 1.20 (1.05–1.38) | 1.07 (0.93–1.23) | 1.14 (0.98–1.32) |
| *Supplement: PARAGON-HF* | 0.87 (0.75–1.01) | 1.63 | 1.65 | 1.38 | 1.22 | 1.01 | 1.37 |
| *Supplement: DAPA-HF proxy* | 0.74 (0.65–0.85) | 0.90 | 0.85 | 0.81 | 0.78 | 0.86 | 0.79 |
| *Supplement: PARTNER 2A* | 0.89 (0.73–1.09) | 1.90 | 1.03 | 1.29 | 0.62 | 0.61 | 0.98 |

**Agreement across the 10 primary-set trials:**

| Arm | Estimate agreement (HR in RCT CI) | Regulatory agreement | Std-difference agreement | Mean \|Δlog HR\| vs RCT | vs full-data reference | Pearson r |
|---|---|---|---|---|---|---|
| Unadjusted | 3/10 | 7/10 | 5/10 | 0.241 | 0.185 | 0.54 |
| Sparse | 7/10 | 5/10 | 8/10 | 0.127 | 0.039 | 0.60 |
| Sparse + ECG | 6/10 | 5/10 | 9/10 | 0.128 | 0.055 | 0.46 |
| hdPS200 | 6/10 | 3/10 | 6/10 | 0.164 | 0.076 | 0.38 |
| hdPS200 + ECG | 6/10 | 5/10 | 8/10 | 0.147 | 0.082 | 0.25 |
| Clinical PS (reference) | 7/10 | 5/10 | 9/10 | 0.122 | 0 | 0.64 |

Paired Wilcoxon tests:
- |Δ vs RCT|, sparse + ECG vs sparse: 7/10 trials closer, p = 0.56.
- |Δ vs RCT|, hdPS200 + ECG vs hdPS200: 6/10 closer, p = 0.56.
- vs the full-data reference: p ≥ 0.43 for every comparison.

**Stratified (mean |Δlog HR| vs RCT):**

| Stratum | Sparse | Sparse + ECG | hdPS + ECG | Clinical |
|---|---|---|---|---|
| Physiology trials | 0.106 | 0.102 | 0.097 | 0.104 |
| Controls | 0.149 | 0.155 | 0.198 | 0.141 |
| Close emulations | 0.093 | 0.074 | 0.086 | 0.090 |

The hdPS arms do worse mainly in the anticoagulation controls (RE-LY, ROCKET-AF).

**Sensitivities:** the conclusions are unchanged. For each analysis, the range of mean |Δlog HR| vs
RCT across the adjusted arms:

| Analysis | Range | Note |
|---|---|---|
| Overlap weighting | 0.10–0.14 | hdPS200 + ECG lowest, 0.104 |
| 12-month horizon | 0.13–0.19 | |
| 60-month horizon | 0.11–0.14 | |
| No-cause deaths as non-CV | 0.12–0.17 | |
| Post-2016 cohort | 0.10–0.15 | sparse 0.104; sparse + ECG 0.105 |
| Outpatient-only | 0.19–0.27 | poor for every arm, including the clinical PS; restricting ACS/HF-discharge trials to outpatients departs from those trials |
| SHD arms | – | sparse + SHD 0.110, r = 0.71, the best r of any arm; not significant |

**Negative controls** (cataract surgery, hernia repair, non-melanoma skin cancer; 30 estimates per
arm): CIs exclude 1 in 1–4 per arm, which is chance level. No arm shows systematic residual
confounding.

**Exploratory, post hoc (added 2026-09-25): comparison that accounts for standard errors.** This
summary uses each trial's emulated and RCT standard errors. For each trial,
z = (log HR_emulated − log HR_RCT) / √(SE²_emulated + SE²_RCT). The differences are then pooled
across trials with a DerSimonian–Laird random-effects model.
- **τ** is the between-trial spread of the error that sampling error cannot explain. Smaller is
  better.
- **Coverage** is how often the emulated 95% CI contains the RCT point estimate.

Primary set, all initiators:

| Arm | Mean \|z\| | \|z\| < 1.96 | Pooled bias (log HR) | τ | I² | Coverage | Median SE |
|---|---|---|---|---|---|---|---|
| M0 unadjusted | 2.56 | 5/10 | −0.066 | 0.301 | 91% | 4/10 | 0.075 |
| M1 sparse | 1.15 | 8/10 | +0.008 | 0.123 | 57% | 7/10 | 0.098 |
| M2 sparse + ECG | 1.04 | 9/10 | +0.025 | 0.094 | 43% | 7/10 | 0.096 |
| M3 hdPS200 | 1.33 | 6/10 | +0.036 | 0.131 | 59% | 6/10 | 0.105 |
| M4 hdPS200 + ECG | 1.07 | 8/10 | +0.052 | 0.078 | 33% | 8/10 | 0.103 |
| R clinical | 1.00 | 9/10 | +0.032 | 0.075 | 29% | 9/10 | 0.110 |

Adding the ECG lowers the unexplained heterogeneity for both base PSs: τ goes from 0.123 to 0.094
for sparse and from 0.131 to 0.078 for hdPS200. The post-2016 cohort shows the same pattern (sparse
0.109 → 0.076). The ECG arms move toward the clinical PS (0.075), and precision is unchanged
(median SE is essentially the same).

None of these differences is significant:
- paired Wilcoxon of |z| against sparse: sparse + ECG p = 0.38 (smaller |z| in 7/10 trials);
  hdPS200 + ECG p = 0.85;
- every pooled-bias CI includes 0.

In the SHD population, sparse + SHD has the lowest τ of any arm (0.055, 10/10 with |z| < 1.96),
also not significant. The results are consistent with the |Δlog HR| comparison. With 10 trials
there is little power. Script: `scripts/summarize_phase2_se.py`. Tables:
`docs/PHASE2_SE_EXPLORATORY_{ALL,2016,SHD}.md`.

---

## 5b. Exploratory robustness program (protocol v1.3, 2026-09-25)

**Status.** Registered in `docs/PROTOCOL_V1_3_AMENDMENT.md` (tag `protocol-v1.3`) after phase 2 and
before any of these analyses ran. Seven deviations are dated and logged in that file. The frozen
phase-2 results in §5 are unchanged. Everything here is exploratory. CIPHER-EHR was deferred (Ryan).

- **Full tables:**
  - `docs/V13_SUMMARY_PRIMARY.md` (10 frozen primary trials)
  - `docs/V13_SUMMARY_EXTENSION.md` (8 new trials)
  - `docs/V13_SUMMARY_COMBINED.md` (18 trials)
- **Scripts:** `scripts/v13_*.py`.
- **Code check:** the v1.3 loader reproduces the saved phase-2 PS logits exactly (max difference
  about 1e-11). Its phase-2 re-estimates match the frozen estimates to within 4e-16.

**Contrasts.**
- C1 = sparse + ECG vs sparse.
- C2 = hdPS200 + ECG vs hdPS200.

**What was run.**
- **I1 Plasmode.** Known true effect, 5 scenarios, 200 replicates per trial.
- **I2–I3 Paired bootstrap.** 200 replicates per trial; hdPS, PS and matching refitted in each.
  Three targets:
  - the RCT, with its sampling error propagated;
  - the clinical reference R;
  - a new physiology reference R+ (R plus every echo domain, NT-proBNP and labs).
- **I4 Placebos.** 32 noise columns, and the real ECG shuffled between patients.
- **I5 Dose response and alternative ECG inputs.**
  - 8, 16, 32 or 64 PCs, and 32 PCs + phenotypes.
  - The PRESENT-SHD logits.
  - A second encoder: the penultimate layer (3,840 dimensions → 32 PCs) of the PRESENT-SHD
    LVEF < 40 CNN.
- **I6 Multiverse.** 200 specifications: 4 PS models × 5 hdPS splits × 10 estimators.
- **I7 Tests across trials.** Exact sign-flip permutation and leave-one-trial-out.
- **I8 Empirical calibration.** 25 negative-control outcomes.
- **I9 E-values.**
- **Part II Closer to the trial.**
  - Transport to the RCT's published Table 1 (entropy balancing; sources in `docs/v13/rct_facts.json`).
  - Per-protocol analysis with IPCW. Deviations defined three ways: a grace period of 365, 180 or
    730 days, or switching only.
  - A 90-day run-in landmark.
  - Primary-billing-diagnosis hospitalisations only.
  - Dose: not feasible, because orders record the ingredient only.
- **Part III New trials.** 13 new RCT emulations were specified; benchmarks were checked against
  the primary papers.
  - **8 passed every gate:**
    - physiology: EMPEROR-Preserved, EAST-AFNET 4, CABANA;
    - control: ONTARGET, VALUE, ASCOT-BPLA, EMPA-REG OUTCOME, CAROLINA.
  - **5 were too small:** CASTLE-AF, ENGAGE AF, DCP, INVEST, PARADISE-MI.

**Correction found during the run (deviation 6).** The registered plasmode kept each arm's matched
set fixed across replicates, so chance imbalance in that one sample showed up as "bias". Even the
correctly specified clinical PS showed |bias| up to 0.08 when the true effect was null. The fixed
version made the ECG look 20–30% better. The corrected version resamples the cohort and refits
the PS and matching in every replicate (Franklin 2014). Only the corrected version is used below.

### Results (18 trials unless stated)

| Question | C1: sparse + ECG vs sparse | C2: hdPS200 + ECG vs hdPS200 |
|---|---|---|
| **Plasmode, known truth, base scenario:** reduction in \|bias\| (log HR), 95% CI | **+0.004 (0.002 to 0.006)**, about 8% of sparse's bias; beats the shuffled-ECG placebo (+0.007) | −0.002 (−0.005 to 0.000); no gain |
| Plasmode, physiology trials only (n = 8) | **+0.009 (0.004 to 0.011)** | −0.008 (−0.011 to −0.004); slight harm |
| Plasmode, only physiology confounds (the phys_only scenario) | 0.000 (−0.002 to 0.002) | +0.003 (0.000 to 0.005) |
| **Real data, paired bootstrap vs RCT:** mean Δ squared error | −0.001 (−0.044 to 0.005) | −0.002 (−0.030 to 0.028) |
| Paired bootstrap vs RCT, physiology trials only | **−0.007 (−0.079 to −0.002)** | −0.004 (−0.031 to 0.012) |
| Paired bootstrap vs R+ (no RCT design error) | −0.001 (−0.016 to 0.008) | +0.002 (−0.019 to 0.013) |
| Trials in which the ECG arm is closer to the RCT | **14/18** (supplementary sign test p = 0.03; registered sign-flip p = 0.99) | 11/18 (p = 0.48) |
| Multiverse: specifications favouring the ECG, vs RCT (mean \|Δ\|) | **100%** | 86% |
| Multiverse: specifications favouring the ECG, vs R+ (mean \|Δ\|) | 83% | 59% |
| Trials needed to detect the plasmode-sized gain with RCT benchmarks | about 1,450 (base) / 540 (strong) | not detectable (no gain) |

**Other findings.**

- **Placebos.**
  - Adding pure noise or shuffled ECG to sparse did not help, and in the plasmode it slightly
    increased bias.
  - Real ECG beat shuffled ECG in the plasmode, but not in the real-data bootstrap.
- **Dose response and alternative ECG inputs, vs the RCT.**
  - PRESENT-SHD logits added to sparse: −0.017 (−0.048 to 0.002).
  - The second encoder added to sparse: −0.010 (−0.045 to 0.001).
  - Both point estimates favour the ECG, but neither is significant, and neither holds against R+.
  - Dose response for sparse vs the RCT: the effect grows with the amount of ECG information.

    | ECG input added to sparse | Mean Δ squared error vs RCT (95% CI) |
    |---|---|
    | 8 PCs | +0.005 |
    | 16 PCs | +0.008 |
    | 32 PCs | −0.001 |
    | 64 PCs | −0.013 (−0.050 to 0.001) |
    | 32 PCs + phenotypes | −0.014 (−0.046 to −0.001) |

    This pattern does not appear against R+, or on top of hdPS.
- **Negative-control calibration.**
  - Adding the ECG did not reduce systematic error in the negative controls. Change in σ: C1
    −0.006, C2 +0.006; both p > 0.6.
  - Calibration widened the intervals but did not improve any arm's agreement with the RCT.
- **E-values.** The median E-value for the disagreement between the emulation and the RCT is
  about 1.5 in every arm. Modest unmeasured confounding, or design error, could explain the gaps.
- **Part II: closer to the trial design.**
  - No design refinement improved overall agreement.
  - Transport to the RCT's Table 1, strict primary diagnoses and the 90-day run-in all made
    agreement worse. They lose events and effective sample size, and SBP targets such as LIFE's
    mean of 174 mmHg cannot be reached.
  - One consistent pattern: in the on-treatment analyses (IPCW, switch-only or 730-day grace
    periods), hdPS200 + ECG had the smallest error of all arms, including the clinical PS.

    | Arm | Mean \|Δlog HR\| | τ |
    |---|---|---|
    | hdPS200 + ECG | 0.138–0.149 | 0.118–0.126 |
    | hdPS200 | 0.167–0.176 | – |
    | Clinical PS | 0.149–0.154 | – |

  - Per-protocol here rests on order records without days-supply. More than half of initiators
    have no re-order within a year.

**Bottom line of v1.3.**
1. **Measurable, but small.** Where the truth is known, adding the ECG to a sparse PS removes a
   small but real amount of bias, about 8% overall and about 20% in physiology trials. It does
   nothing on top of hdPS.
2. **Consistent in direction, not significant on the registered tests.** Against the RCTs, sparse
   + ECG moves estimates in the right direction consistently:
   - 14 of 18 trials;
   - every one of the 200 analysis specifications;
   - bootstrap CI excluding 0 in the physiology trials.

   The registered magnitude-based tests are not significant, and nothing holds against the
   within-data physiology reference R+.
3. **RCT benchmarking can't adjudicate a gain this size.** A gain of this size (≈ 0.004–0.009
   log HR) is far below what benchmarking against RCTs can detect. Differences in design between
   the RCTs and the emulations, about 0.12–0.15 log HR even for the best PS, swamp it.
4. **None of the pre-specified decision rules for "ECG improves" was fully met.** C1 met rules 1
   (plasmode), 3 (placebo, plasmode) and 4a (multiverse). It failed rule 2 (bootstrap), rule 3 on
   real data, and rule 4b (leave-one-out). The correct claim is **partial**. The ECG's
   demonstrable value is in balancing measured physiology (phase 1) and a small reduction in bias
   for sparse PSs. Improved agreement with RCTs is not demonstrated.
5. **The mechanism is not what we assumed.** In the plasmode, the ECG's gain disappears when only
   the core-9 physiology confounds (the phys_only scenario). So the gain there does not come
   from proxying the core-9 values, many of which are imputed. The mechanism behind the small
   gain is unresolved.

## 6. Interpretation and limitations

1. **What the paper can claim.**
   - A routine ECG, entered as raw embedding PCs, recovers physiologic confounding that a
     code-based PS leaves. This is LV structure and function, the cardiac information codes
     don't carry.
   - The ECG complements hdPS: hdPS covers the coded record, the ECG covers physiology.
   - The ECG does not see valve disease.
   - These are balance results, with a mechanism the echo data make interpretable.
2. **What it cannot claim.** Better balance on these domains did not translate into estimates
   closer to the RCTs, and neither did measured EF/labs (the clinical PS). With 10 trials the
   comparison has little power. The between-arm differences (≈ 0.01–0.04 in log HR) are small
   relative to the residual trial-to-emulation gap (≈ 0.12). That gap is dominated by factors no
   PS arm addresses.
3. **Why the residual gap is large** (likely contributors, not tested):
   - outcome measurement: the EHR composites are broad;
   - comparator and population differences from the trials;
   - initiation of orders rather than dispensing;
   - differences in follow-up.

   For example, PARADIGM-HF's composite occurs in about 52% of both arms over 27 months (the
   trial: 22–27%). HF hospitalisation defined by any I50 code during a stay behaves close to
   all-cause hospitalisation, which pulls toward the null.
4. **Other limitations:**
   - EHR orders, not dispensings.
   - CT Vital Statistics causes are listed causes without an underlying-cause flag (CV death may
     be over-counted).
   - Conditions are linked to stays by date only.
   - Index-admission events (periprocedural stroke, in-hospital reinfarction) are not captured.
   - The primary set has 10 trials, so tests have low power.
   - Several design choices were made after viewing balance, all disclosed (protocol §12,
     amendments).
   - Phase 2 ran after two amendments, both registered before outcome extraction.

---

## 7. Questions for you

1. **Framing.** Do you agree with a "balance/mechanism positive, effect-agreement null" framing?
   The alternative is a methods paper on the capture map, with the effect comparison as a
   secondary aim.
2. **Outcome refinement.** A pre-specified v1.3 would use a stricter HF-hospitalisation
   definition. It would have to be declared as post-hoc because outcomes have now been seen, so
   I'd present it only as exploratory. Do you want it?
3. **More trials to raise power for H5.** This is only possible with new, pre-specified
   emulations. Also, TRITON might become feasible with a broader window.
4. **SHD encoder.** Report it as a secondary arm (current), or develop it further (e.g. more valve
   targets)?

---

## 8. Audit trail and files

- **Audit findings and fixes:** `docs/DECISIONS.md` (2026-09-24 entries);
  `docs/PROTOCOL_V1_1_AMENDMENT.md`; `docs/PROTOCOL_V1_2_AMENDMENT.md`.
- **Checks that passed:**
  - 302 unit tests (the 2 torch-dependent ones pass in the torch environment);
  - all ECGs 0–365 d before index;
  - CLMBR index alignment 100%;
  - exact reproducibility of a re-run;
  - reference-set and phenotype-training disjointness;
  - the matcher equals brute force;
  - Cox/Rubin recover a known HR in simulation.
- **Phase 1:** `docs/V11_CAPTURE_MAP_{ALL,OP,SHD,2016}_{PRIMARY,ALLTRIALS}.md`.
- **Phase 2:** `docs/PHASE2_SUMMARY_{ALL,OP,SHD,2016}.md` and `docs/phase2_tables/*.csv` (events
  1–10 suppressed).
- **Restricted outputs on RAID** (`/mnt/raid0/rbc58/ecg-tte/audits/`):
  - `claude-cap4-{all,op,shd,2016}-<trial>` (grids and matched sets);
  - `claude-<trial>-outcomes-v1`;
  - `claude-phase2-<pop>-<trial>.csv`.
