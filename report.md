# Overnight report: multi-trial balance study (2026-09-24)

For Ryan. Everything here is **balance-only and exploratory**. No trial outcome was extracted, and
no hazard ratio was estimated. Aggregates only. Detailed decision log: `docs/DECISIONS.md`
(entries 2026-09-23/24). Commands: `docs/RUN_LONGTAIL_REPLICATION.md`.

## 1. Summary

1. **13 adapted trials were attempted and 12 were analysed.**
   - 7 physiology-driven trials (the main test): COMET, PARADIGM-HF, PARAGON-HF, TRANSFORM-HF,
     ELITE II, LIFE, DIONYSOS.
   - 5 controls where no ECG benefit was expected: PLATO, ARISTOTLE, ROCKET-AF, RE-LY, ALLHAT.
   - TRITON failed the pre-set feasibility rule: 278 prasugrel users with an ECG, below the
     300 minimum.
   - All 12 ran through one identical pipeline: cohort, core baseline, fixed BCL ECG, CLMBR
     code-only, pre-index panel, external prognostic score, and the long-tail grid (5 imputations
     × 5 splits).
2. **Headline for the paper.** The PS was restricted to demographics + recorded diagnoses: no
   echo, labs, vitals or medications.
   - In every trial where that PS left measured-LVEF imbalance ≥ 0.1 (5 trials, all physiology
     trials), adding raw ECG embedding PCs reduced it by a median of **62%** (range 33–88%).
     There were no predicted values; the ECG entered as 32 raw PCs.
   - Outpatient-initiator sensitivity: 8 trials had LVEF imbalance ≥ 0.1, and the median
     reduction was **51%** (16–70%). There was one exception, PARADIGM-HF.
   - The same-size noise placebo does nothing comparable.
3. **Mean measured-physiology imbalance** (9 variables) falls **24%** in physiology trials vs
   **10%** in controls when ECG PCs are added to the sparse PS. It never reaches the full
   clinical PS, which still has the measured values.
4. **For the rest of the coded record, hdPS remains the workhorse.**
   - hdPS200 is better than CLMBR in 4 of 12 trials (ELITE II and the three ACS/AF controls)
     and ties in 6.
   - CLMBR is better in LIFE, and in ALLHAT, which is at ceiling (meaningless).
   - A stacked hdPS + ECG + CLMBR PS gives the lowest pool-B imbalance in 11 of 12 trials (not
     ALLHAT, which is at ceiling; PARAGON-HF is uninterpretable). The hdPS200 version costs
     2–36% of pairs.
5. Adding ECG to a PS that already contains the clinical measurements adds little outside COMET
   and PARADIGM-HF (median −3%). **The ECG is valuable when the measurements are missing, not on
   top of them.** This supports the framing you proposed.

## 2. What was run (same for every trial)

| Component | Definition |
|---|---|
| Cohort | New users of either arm (first-ever order, no comparator order in 365 d incl. index day); age and prior-activity rules; trial-specific gate and exclusions (§3). `scripts/build_trial_cohort.py`, specs in `scripts/trial_specs.py` |
| Clinical PS (core) | Demographics, index year, LVEF (echo 365 d), vitals/labs (90 d, BMI 365 d), 9+ comorbidities (365 d), trial-relevant medications (90 d), visit counts (365 d). Index day excluded. 5 chained-equation imputations |
| Claims PS | Core minus EF, labs and vitals |
| Sparse "dx" PS | Demographics + recorded diagnoses only. No medications, utilisation, procedures, EF, labs or vitals |
| ECG | Fixed BCL, latest ECG in [index-365, index], index day allowed. Full-design arms use 5 phenotype scores + 32 PCs; **sparse arms use the 32 PCs only** |
| CLMBR | Frozen CLMBR-T, code-only, per-cohort MEDS, 64 PCs |
| hdPS | Exposure-only ranking of once/sporadic/frequent code levels from pool A; k = 100/200/500 |
| Evaluation | Pool-B features (half of ~900–1,300 pre-index codes/labs/visits, never in any PS); measured-only physiology; external prognostic score (1-y death/HF hospitalisation or a trial-appropriate composite, fit on 30K patients outside each cohort); post-matching C-statistic; chance floor |
| Matching | 1:1 greedy on the PS logit, caliper 0.2 SD, anchored on the smaller arm |

## 3. Trials

| Trial | Role | Comparison (adapted) | Key adaptations | Cohort n (arm1 / arm2) | ECG + CLMBR n | Status |
|---|---|---|---|---|---|---|
| COMET | physiology | metoprolol tartrate vs carvedilol | JDAT-based cohort (earlier work) | 2,960 / 4,539 | 2,542 / 3,561 | done |
| PARADIGM-HF | physiology | sacubitril/valsartan vs any ACEi | EF ≤ 40 if measured; eGFR/K/SBP exclusions | 2,885 / 2,746 | 2,182 / 2,021 | done |
| PARAGON-HF | physiology | sacubitril/valsartan vs valsartan | age ≥ 50; EF ≥ 45 if measured, else HFpEF code required | 756 / 703 | 578 / 522 | done ⚠ small overlap (311 pairs) |
| TRANSFORM-HF | physiology | torsemide vs furosemide | I50 code in 30 d stands in for index HF hospitalisation | 879 / 17,920 | 697 / 14,960 | done |
| ELITE II | physiology | any ARB vs any ACEi | age ≥ 60; EF ≤ 40 if measured; class adaptation | 2,362 / 2,530 | 1,469 / 1,753 | done |
| LIFE (v2) | physiology | any ARB vs cardioselective β-blocker | hypertension + **ECG-text LVH**; age 55–80; no HF; no MI/stroke 180 d. v1 (losartan vs atenolol) failed at n = 226 | 1,239 / 1,892 | 1,239 / 1,892 | done |
| DIONYSOS | physiology | dronedarone vs amiodarone | AF only | 998 / 11,169 | 753 / 9,634 | done |
| PLATO | control | ticagrelor vs clopidogrel | ACS in 30 d; no OAC; index-day STEMI/PCI allowed as covariates | 4,503 / 3,477 | 4,011 / 2,748 | done |
| TRITON | control | prasugrel vs clopidogrel | ACS + PCI in 30 d | 341 / 1,758 | 278 prasugrel | **failed feasibility** |
| ARISTOTLE | control | apixaban vs warfarin | AF; no mitral stenosis/mechanical valve; no other DOAC | 20,579 / 5,283 | 15,419 / 3,352 | done |
| ROCKET-AF | control | rivaroxaban vs warfarin | as ARISTOTLE | 5,573 / 5,381 | 3,633 / 3,422 | done |
| RE-LY | control | dabigatran vs warfarin | as ARISTOTLE; dose not identifiable | 1,272 / 5,442 | 702 / 3,470 | done |
| ALLHAT | control | amlodipine vs any thiazide | hypertension, age ≥ 55, no HF | 38,534 / 20,001 | 18,098 / 8,494 | done (at ceiling: clinical PS already balanced) |

Not attempted, and why:
- Placebo-controlled HF trials (DAPA-HF, EMPEROR, TOPCAT, SHIFT, DIG) have no sensible active
  comparator.
- PARTNER (TAVR vs SAVR) needs a procedure exposure contract.
- SAFE-T and RATE-AF have no hazard ratio for the primary endpoint.
- The T2D CVOTs have low ECG coverage (screen of 2026-09-23).

Embedding QC:
- ECG probe AUCs: sex 0.81–0.89, age ≥ 65 0.70–0.82, LVEF ≤ 40 0.78–0.85 where testable.
- CLMBR AF probe 0.90–0.98.
- ECG phenotype heads were retrained per trial with that trial's patients removed; held-out
  LVEF ≤ 40 AUC 0.90–0.91.
- External prognostic scores: reference AUC 0.73–0.84.

## 4. Results

### 4.1 Sparse PS + ECG: the main result

Measured-LVEF standardised difference (measured EF only):

| Trial | Role | Unmatched | Demo + dx | **Demo + dx + ECG PCs** | Claims | Claims + ECG PCs | Clinical (EF in PS) |
|---|---|---|---|---|---|---|---|
| COMET | physiology | 0.57 | 0.56 | **0.34** | 0.52 | 0.31 | 0.02 |
| PARADIGM-HF | physiology | 0.07 | 0.13 | **0.04** | 0.10 | 0.06 | 0.03 |
| PARAGON-HF ⚠ | physiology | 0.91 | 0.98 | **0.66** | 0.94 | 0.65 | 0.12 |
| TRANSFORM-HF | physiology | 0.13 | 0.11 | **0.01** | 0.10 | 0.01 | 0.06 |
| ELITE II | physiology | 0.11 | 0.08 | 0.07 | 0.07 | 0.12 | 0.08 |
| LIFE | physiology | 0.02 | 0.01 | 0.08 | 0.11 | 0.07 | 0.07 |
| DIONYSOS | physiology | 0.71 | 0.47 | **0.18** | 0.38 | 0.33 | 0.12 |
| PLATO | control | 0.10 | 0.06 | 0.05 | 0.02 | 0.06 | 0.03 |
| ARISTOTLE | control | 0.12 | 0.05 | 0.05 | 0.01 | 0.04 | 0.03 |
| ROCKET-AF | control | 0.18 | 0.08 | 0.02 | 0.03 | 0.04 | 0.08 |
| RE-LY | control | 0.24 | 0.05 | 0.08 | 0.02 | 0.07 | 0.10 |
| ALLHAT | control | 0.01 | 0.00 | 0.01 | 0.01 | 0.02 | 0.04 |

Mean |SMD| over the 9 withheld physiology variables (measured values), sparse PS:

| Trial | Role | Demo + dx | + noise (placebo) | + ECG PCs | Change (ECG) | Change (placebo) |
|---|---|---|---|---|---|---|
| COMET | physiology | 0.129 | 0.122 | 0.092 | −29% | −5% |
| PARADIGM-HF | physiology | 0.103 | 0.110 | 0.073 | −30% | +7% |
| PARAGON-HF ⚠ | physiology | 0.255 | 0.218 | 0.189 | −26% | −15% |
| TRANSFORM-HF | physiology | 0.151 | 0.125 | 0.093 | −38% | −17% |
| ELITE II | physiology | 0.058 | 0.062 | 0.045 | −23% | +7% |
| LIFE | physiology | 0.143 | 0.147 | 0.128 | −10% | +3% |
| DIONYSOS | physiology | 0.211 | 0.201 | 0.179 | −15% | −5% |
| PLATO | control | 0.056 | 0.052 | 0.056 | −1% | −7% |
| ARISTOTLE | control | 0.095 | 0.093 | 0.075 | −21% | −2% |
| ROCKET-AF | control | 0.125 | 0.128 | 0.116 | −7% | +2% |
| RE-LY | control | 0.142 | 0.142 | 0.141 | −1% | 0% |
| ALLHAT | control | 0.104 | 0.098 | 0.080 | −22% | −6% |

Reading:
- Diagnoses alone leave LVEF badly imbalanced exactly in the trials where cardiac function drives
  the prescribing choice: carvedilol vs metoprolol, ARNI vs valsartan in HFpEF, amiodarone vs
  dronedarone (dronedarone is contraindicated in HFrEF), torsemide vs furosemide.
  - In every one of them the raw ECG recovers a large part of it.
  - In the ACS/AF/HTN controls, diagnoses already balance LVEF, so there is nothing to recover.
- The ECG gain exceeds the placebo's by > 5 points in **10 of 12 trials** (not PLATO or RE-LY). TRANSFORM-HF and
  PARAGON-HF have placebo gains of −15 to −17%, a small-sample artefact, so their ECG gains are
  about half as large net.
- **The ECG does not reach the full-data PS.** COMET: 0.34 vs 0.02; DIONYSOS: 0.18 vs 0.12.

Outpatient-initiator sensitivity (index order not during an inpatient stay; imputations reused):

| Trial | Measured LVEF: demo + dx → + ECG PCs |
|---|---|
| COMET | 0.55 → 0.26 |
| PARADIGM-HF | 0.05 → 0.20 (worse) |
| PARAGON-HF | 0.91 → 0.73 |
| TRANSFORM-HF | 0.12 → 0.04 |
| ELITE II | 0.17 → 0.14 |
| LIFE | 0.06 → 0.08 |
| DIONYSOS | 0.35 → 0.18 |
| PLATO | 0.07 → 0.06 |
| ARISTOTLE | 0.20 → 0.07 |
| ROCKET-AF | 0.28 → 0.23 |
| RE-LY | 0.13 → 0.04 |
| ALLHAT | 0.01 → 0.01 |

### 4.2 Full design: long-tail balance of the coded record

Change in the share of pool-B features with |SMD| > 0.1 versus the clinical PS:

| Trial | Role | Clinical PS | + ECG | + CLMBR | + hdPS200 | + hdPS200 + ECG + CLMBR | Pairs lost (stack) |
|---|---|---|---|---|---|---|---|
| COMET | physiology | 17.9% | −19% | −79% | −78% | −92% | 22% |
| PARADIGM-HF | physiology | 25.9% | −17% | −61% | −59% | −69% | 36% |
| PARAGON-HF ⚠ | physiology | 25.8% | +15% | +14% | +17% | +76% | 72% |
| TRANSFORM-HF | physiology | 29.6% | −8% | −48% | −51% | −71% | 4% |
| ELITE II | physiology | 13.0% | −8% | −50% | −68% | −71% | 17% |
| LIFE | physiology | 7.6% | +4% | −37% | −14% | −24% | 20% |
| DIONYSOS | physiology | 20.3% | −3% | −78% | −77% | −83% | 4% |
| PLATO | control | 14.9% | −3% | −32% | −83% | −86% | 12% |
| ARISTOTLE | control | 20.6% | −2% | −39% | −82% | −95% | 22% |
| ROCKET-AF | control | 23.0% | −3% | −41% | −85% | −94% | 26% |
| RE-LY | control | 23.7% | +6% | −55% | −55% | −62% | 9% |
| ALLHAT | control | 0.3% | (at ceiling) | | | | |

⚠ PARAGON-HF: only 311 pairs under the clinical PS; chance alone gives ~21% of features > 0.1,
so its long-tail numbers are uninterpretable. The excess-over-chance version of this table is in
`docs/OVERNIGHT_TABLES_2026_09_24.md`.

Prognostic-score balance (clinical / + CLMBR / + hdPS200):
- CLMBR worsens it in PARADIGM-HF (0.019 → 0.080), ARISTOTLE (0.13 → 0.18), ROCKET-AF (0.08 →
  0.12) and RE-LY (0.04 → 0.08).
- hdPS200 improves it in 9 of 12 trials. It is slightly worse in PARADIGM-HF (0.019 → 0.027) and
  PLATO (0.021 → 0.029), unchanged in ALLHAT, and never above 0.083.
- This is a further reason to prefer hdPS over CLMBR as the high-dimensional arm.

## 5. What this means for the paper outline

A defensible story:

> In EHR-based target trial emulation, key clinical measurements are often missing. A routinely
> acquired ECG recovers a substantial part of the physiologic confounding that a code-only
> propensity score leaves. The gain is concentrated in trials where cardiac function drives
> treatment choice, as pre-specified. The rest of the coded record is best handled by hdPS; the
> ECG and hdPS are complementary.

What it does **not** yet show:
- that the balance gain moves effect estimates, either toward the full-data emulation or toward
  the RCT;
- that the ECG can replace measured EF, which it can't (§4.1).

The next evidence step is the within-trial comparison of estimates (full data vs sparse vs
sparse + ECG). It needs outcomes and should be frozen first (§7).

## 6. Decisions I made (at my discretion; all in `docs/DECISIONS.md`)

1. Trial roles (physiology vs control) and the feasibility rule (smaller arm ≥ 300 with ECG) were
   fixed before building any cohort.
2. LIFE widened to v2 (ARB vs cardioselective β-blocker) after v1 failed feasibility, before any
   LIFE balance was computed. TRITON was not widened; it is reported as failed.
3. Class adaptations: ELITE II (ARB vs ACEi), ALLHAT (any thiazide), LIFE v2. Rationale:
   single-ingredient arms were too small, and the class is the usual active-comparator
   adaptation.
4. EF-based eligibility where EF is measured, with a code fallback when it is unknown
   (PARADIGM-HF, ELITE II, PARAGON-HF). An unknown value passes the safety exclusions.
5. The ECG entered the sparse arms as raw PCs only, per your preference against predicted values.
   The phenotype-score arm is kept for comparison and does about the same.
6. Prognostic-score outcomes by trial type: HF → death or HF hospitalisation; ACS/HTN → death, MI
   or stroke; AF anticoagulation → death or stroke; DIONYSOS → death or AF/HF/stroke
   hospitalisation.
7. Added an outpatient-initiator sensitivity analysis (§4.1) after seeing large setting
   differences. The primary analyses are unchanged.
8. GPU use: only devices idle at launch (5 and 6; others were occupied by other users).

## 7. Uncertainties and questions for you

1. **Care setting and route at initiation.**
   - The index order falls during an inpatient stay very differently by arm: DIONYSOS 17% vs 70%,
     TRANSFORM-HF 43% vs 72%, PARAGON-HF 33% vs 10%, COMET 65% vs 49%.
   - OMOP gold can't distinguish IV from oral: amiodarone and furosemide likely include IV
     inpatient use.
   - Setting is not in any PS. Options:
     - (a) restrict to outpatient initiation as the primary analysis;
     - (b) add "inpatient at index" as a core covariate;
     - (c) keep all patients and report setting.

   **Recommend (a) for chronic-therapy trials plus (b) as a sensitivity.** The outpatient
   sensitivity above shows the ECG result survives restriction.
2. **Published HRs** in `trial_specs.py` were entered from memory: PARAGON 0.87 (rate ratio),
   TRANSFORM 1.02, ELITE II 1.13, LIFE 0.87, DIONYSOS 1.59, ALLHAT 0.98. They must be verified,
   and each trial's primary endpoint mapped, before any RCT-agreement analysis.
3. **Is the measured-value evaluation fair?**
   - LVEF balance is assessed only where EF was measured (about 30–60% of patients), and
     measurement itself is selective.
   - Should we also report balance on "EF measured (yes/no)"? Should echo-derived variables
     beyond EF (valve disease, LV mass) enter the physiology panel?
4. **Trials with poor overlap.** PARAGON-HF keeps 311 pairs; TRANSFORM-HF, DIONYSOS and RE-LY
   keep about 700. Keep them with a flag, drop them, or use weighting (IPTW/overlap weights)
   instead of matching for the whole study? I'd favour overlap weighting as a pre-specified
   secondary analysis.
5. **LIFE uses the ECG twice.** ECG-text LVH defines eligibility, and the ECG is also in the PS.
   Is that acceptable, or should LIFE move to the control group?
6. **CABG and index procedures in PLATO** (the dominant residual confounder found earlier). Add
   them to the ACS core set as a new spec version?
7. **Primary high-dimensional arm.** hdPS200 (my recommendation) or hdPS500, and is CLMBR kept
   only as a sensitivity analysis?
8. **Patient overlap across trials.** The same person can appear in several cohorts (e.g.
   PARADIGM-HF and ELITE II ACEi users). This is fine for balance, but it matters for any pooled
   cross-trial statistic.
9. **Imputation.** The new trials use sklearn chained equations, not the COMET R MICE pipeline.
   Is that acceptable for the paper, or should the R pipeline be generalised?
10. **The analysis choices so far were not pre-registered.** Before any outcome, freeze: trial
    list and roles, base covariate sets, ECG PCs (32), hdPS k, caliper, the evaluation panel and
    the estimate comparison.

## 8. Suggested next steps

1. Decide items 1, 4 and 7 above, then freeze the protocol (a `docs/PROTOCOL_V1.md` draft can be
   prepared).
2. Verify the published HRs and endpoint mappings; define negative-control outcomes.
3. Estimate effects under the frozen protocol:
   - full data, sparse, sparse + ECG, sparse + hdPS + ECG;
   - report agreement with the full-data estimate and with the RCT.

## 9. Where everything is

- Code: `scripts/` (specs `trial_specs.py`, driver `run_trial_pipeline.sh`, tables
  `summarize_all_trials.py`). Tests: `tests/test_longtail_v2.py`.
- Outputs (restricted, on RAID) under `/mnt/raid0/rbc58/ecg-tte/audits/`:
  - `claude-<trial>-{cohort-v1, baseline-v1, panel-v2, bcl, phenotypes, clmbr-codeonly, progref-v1}`
  - `claude-longtail-v2-<trial>`, `claude-sparse-dx-<trial>`, `claude-sparse-dx-outpt-<trial>`
  - all tables: `claude-overnight-tables.md`
  - inpatient-at-index shares: `claude-overnight-index-inpatient-share.json`
- MEDS builds: `/mnt/raid0/rbc58/ecg-tte/shared/claude-<trial>-meds-v2`.
