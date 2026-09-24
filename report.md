# ECG-TTE balance study: report (v3, 2026-09-24)

For Ryan. **Balance only; no outcome has been extracted or estimated.** Aggregates only.
- Decision log: `docs/DECISIONS.md`.
- Full v3 tables: `docs/V3_TABLES_2026_09_24.md`.
- The overnight report (all initiators, pre-v3) is kept at `docs/REPORT_OVERNIGHT_2026_09_24.md`.

## A. Answers to your questions

**1. What is in the sparse PS, and how does the ECG enter it?**
- The sparse ("dx") PS contains:
  - **Demographics:** age, sex, index year.
  - **Recorded diagnoses:** binary, any ICD-10 code in the 365 days before index (index day
    excluded), using an investigator-selected cardiology list:

    | Covariate | ICD-10 prefixes |
    |---|---|
    | Ischemic heart disease/MI | I20–I25 |
    | Atrial fibrillation | I48 |
    | Hypertension | I10–I13, I15 |
    | Diabetes | E08–E11, E13 |
    | CKD | N18 |
    | Stroke | I60–I64, I69 |
    | COPD/asthma | J44–J46 |
    | PAD | I70.2, I73.9 |
    | Valve disease | I05–I08, I34–I37 |

  - **Trial-specific extras:**
    - PLATO: HF (I50), prior PCI/CABG status (Z95.1/Z95.5/Z98.61), GI bleeding, STEMI in 30 days.
    - AF trials: HF, prior bleeding, TIA, liver disease.
    - DIONYSOS and LIFE: HF.
- **Excluded:** medications, visit counts, procedures, EF, labs and vitals.
- **The ECG enters as covariates, not as a distance.** It is the first 32 principal components of
  the 256-dimensional BCL embedding, added to the logistic PS alongside the diagnoses. Matching
  is then 1:1 greedy nearest-neighbour on the PS logit (caliper 0.2 SD). **No cosine distance
  is used anywhere.** Cosine matching was dropped earlier because it never balanced confounders.

**2. Balance beyond diagnosis codes: labs, echo features, and deltas vs hdPS.** Yes. Every trial
now has a held-out physiology panel that never enters any PS:
- **Core 9:** EF, SBP, DBP, HR, BMI, creatinine, K, Na, Hb.
- **Labs 10:** NT-proBNP, hs-troponin T, eGFR, albumin, BUN, glucose, HbA1c, WBC, platelets, LDL.
- **Echo 26:** wall thickness (IVSd, LVPWd, increased-wall-thickness flag); LV dimensions and
  volumes; LA size and volume; E/e′; diastolic grade; RVSP; TAPSE; RV size and function; aortic
  root; valve grades and velocities.
  - These come from the **PanEcho echo-report labels**, which cover a curated 2015–2022 set of
    34K studies, i.e. only **1–5% of each cohort**.
  - The full echo report extract you mention is not reachable from this container: the JDAT
    root is not mounted, and OMOP gold has no echo measurements. **Please point me to the
    newest echo report file** (§E1).

Scoring is by excess over chance. Small matched sets produce imbalance by chance alone, so each
variable is scored as its |SMD| minus the |SMD| expected under randomisation given how many
patients were measured in each matched arm (§C). Results (§C.1–C.3):

- **Core-9 physiology.** In the physiology trials, raw ECG PCs and hdPS200 each remove about
  0.04 of excess SMD from the sparse PS. The ECG does better than hdPS200 in **5 of 7** physiology
  trials, and in only **1 of 5** controls. The combination (dx + hdPS200 + ECG) is best.
- **Measured LVEF** (8 trials where the sparse PS leaves SMD ≥ 0.1):
  - The ECG beats hdPS200 in **6 of 8** (COMET 0.34 vs 0.46; DIONYSOS 0.18 vs 0.33;
    TRANSFORM-HF 0.01 vs 0.07; PARAGON-HF 0.73 vs 0.81).
  - hdPS beats the ECG in ELITE II and ROCKET-AF.
- **Labs 10.** Already at the chance level under every PS, including the sparse one: there is
  no residual lab imbalance for any method to fix. One exception is NT-proBNP in DIONYSOS, where
  the ECG halves it (0.30 → 0.15).
- **Echo measurements.** The chance level is 0.14–0.53, because so few patients are measured.
  The direction favours adding the ECG (median excess: dx 0.040, dx + ECG 0.015, dx + hdPS200
  0.012, both 0.009), but **this is not interpretable at this coverage**.

**3. All diagnosis codes or a cardiology subset?** Both were run (`dx` vs `dxall`; dxall =
demographics + every 3-character ICD-10 code with ≥ 2% prevalence in the prior year).
- All codes balance core physiology better in 10 of 12 trials and reduce non-diagnosis long-tail
  imbalance by a median of about 40%.
- The ECG still adds on top: dxall + ECG improves core physiology over dxall in 10 of 12 trials.
- The cost is retention: pairs fall by a median of about 7% (COMET −23%, PARAGON-HF −51%).
- **Recommendation:** use investigator-selected cardiology diagnoses as the named core, as in
  RCT-DUPLICATE, and **let hdPS carry "all codes"**. This is equivalent in spirit to dxall, but
  prioritised and capped at k. Report dxall as a sensitivity analysis.

**"It never reaches the full clinical PS" — does that mean it's worse than high-dimensional PSM?**
No. That sentence compared sparse + ECG with the clinical PS that *contains* the measured EF,
labs and vitals. Neither sparse + ECG nor sparse + hdPS reaches that PS on physiology, and that
gap is the price of missing measurements. Against hdPS:
- On **physiology**, the ECG ties or beats hdPS in the physiology trials.
- On the **coded record** (long-tail), hdPS is better.
- They are complementary, and the combination is best on both.

**What is "claims"?** A *claims-like* covariate set, not insurance data: demographics +
diagnoses + medication orders + visit counts, without EF, labs or vitals. It mimics what a claims
database would contain. All data here are Yale EHR (OMOP gold); medications are orders, not
dispensings.

**hdPS200 vs hdPS500.** hdPS (Schneeweiss 2009):
- For each pre-index code, it creates binary "once / sporadic / frequent" indicators.
- It ranks them by how differently prevalent they are between arms. This is exposure-only; no
  outcome is used.
- It adds the top **k** to the PS. **hdPS200 = the top 200; hdPS500 = the top 500.**

More k balances more of the record but trims more pairs. **Recommendation: hdPS200 as primary**,
with k = 100 and 500 as sensitivity analyses.

## B. Your decisions and how they were applied

| # | Decision | Applied |
|---|---|---|
| 1 | Outpatient initiation primary "when possible"; all initiators secondary | Done. PLATO and TRANSFORM-HF keep all initiators as primary because the RCTs started treatment in hospital (ACS; HF discharge); outpatient is secondary for them |
| 2 | Verify HRs | Done (§D). One change: **ROCKET-AF benchmark → ITT HR 0.88** (0.74–1.03); 0.79 was the per-protocol estimate. COMET's 0.83 is carvedilol vs metoprolol; our arm order gives 1.20 |
| 4 | Rank emulation quality instead of dropping trials | Proposed rubric and ranking in §D |
| 9 | One imputation method | **sklearn chained equations for all 12 trials**, COMET included. COMET's covariates are now rebuilt with the same OMOP builder, refitted within each population. The R-MICE inputs are kept as history |
| 10 | Best balance story before any outcome, then pre-register | No outcome touched; §F lists what to freeze |
| 3, 5, 8 | Fine as is | Unchanged: LIFE ECG use, primary hdPS arm, cross-trial overlap |

Also for consistency: COMET's ECGs were re-selected under the common rule (365 days, index day
allowed) and re-embedded (6,381 ECGs).

## C. v3 results (primary population)

### C.1 Core-9 physiology, excess |SMD| over chance (0 = as balanced as a randomised sample)

| Trial | Role | Pairs (dx) | dx | dx + ECG | dx + hdPS200 | dx + hdPS200 + ECG | Clinical PS (EF/labs in PS) |
|---|---|---|---|---|---|---|---|
| COMET | physiology | 797 | 0.079 | 0.042 | 0.054 | **0.028** | −0.018 |
| PARADIGM-HF | physiology | 629 | 0.048 | **0.021** | 0.048 | 0.053 | −0.028 |
| PARAGON-HF ⚠ | physiology | 297 | 0.125 | 0.058 | 0.087 | **0.022** | 0.000 |
| TRANSFORM-HF | physiology | 697 | 0.086 | 0.029 | 0.036 | **0.018** | −0.011 |
| ELITE II | physiology | 563 | −0.029 | −0.025 | −0.028 | −0.038 | −0.005 |
| LIFE | physiology | 960 | 0.068 | 0.062 | 0.018 | **0.006** | 0.029 |
| DIONYSOS | physiology | 599 | 0.110 | **0.029** | 0.060 | 0.044 | 0.001 |
| PLATO | control | 2223 | 0.016 | 0.016 | −0.006 | −0.003 | −0.011 |
| ARISTOTLE | control | 906 | 0.075 | 0.056 | **0.022** | 0.035 | −0.001 |
| ROCKET-AF | control | 896 | 0.096 | 0.082 | 0.035 | **0.022** | 0.019 |
| RE-LY | control | 420 | 0.021 | 0.050 | −0.020 | −0.014 | 0.009 |
| ALLHAT | control | 6262 | 0.056 | 0.045 | 0.052 | **0.045** | −0.002 |

Median change from dx:
- Physiology trials: ECG −0.037, hdPS200 −0.038, ECG added on top of hdPS200 −0.016.
- Controls: ECG −0.011, hdPS200 −0.041.

**In the physiology trials the ECG matches hdPS on physiology, and the ECG's gain is specific to
them.** In the secondary population (all initiators; larger samples) the ECG and hdPS again tie
on physiology trials (−0.032 vs −0.039). Measured LVEF there: in 5 trials, dx 0.47 → dx + ECG 0.18
vs dx + hdPS200 0.39.

### C.2 Measured LVEF SMD, primary population (trials with dx ≥ 0.1)

| Trial | dx | dx + ECG | dx + hdPS200 | dx + hdPS200 + ECG |
|---|---|---|---|---|
| COMET | 0.61 | **0.34** | 0.46 | **0.24** |
| PARAGON-HF ⚠ | 0.91 | 0.73 | 0.81 | **0.57** |
| TRANSFORM-HF | 0.11 | **0.01** | 0.07 | 0.07 |
| ELITE II | 0.17 | 0.14 | **0.06** | 0.12 |
| DIONYSOS | 0.35 | **0.18** | 0.33 | 0.19 |
| ARISTOTLE | 0.20 | **0.07** | 0.08 | 0.07 |
| ROCKET-AF | 0.28 | 0.23 | 0.13 | **0.09** |
| RE-LY | 0.13 | **0.04** | 0.09 | 0.09 |

PARADIGM-HF is the one physiology trial where the ECG *worsened* LVEF (0.05 → 0.20, outpatient).
Its baseline LVEF imbalance was small, and its outpatient sample is small (629 pairs, about 40%
with measured EF).

### C.3 Long-tail balance of the coded record (full design; pool-B share > 0.1, excess over chance in brackets)

| Trial | Pairs (clinical PS) | Clinical | + ECG | + CLMBR | + hdPS200 | + hdPS200 + ECG + CLMBR |
|---|---|---|---|---|---|---|
| COMET | 710 | 18.9% (13.0) | 16.3% (9.0) | 11.9% (4.8) | 10.2% (1.1) | 10.8% (−0.8) |
| PARADIGM-HF | 520 | 28.8% (18.1) | 23.0% (6.1) | 20.1% (3.6) | 17.5% (0.2) | 22.0% (−3.9) |
| PARAGON-HF ⚠ | 228 | 33.4% (4.8) | 37.1% (3.2) | 38.3% (1.7) | 39.1% (−8.5) | 53.9% (−19.6) |
| TRANSFORM-HF | 696 | 29.6% (23.3) | 27.1% (20.8) | 15.3% (8.9) | 14.5% (8.0) | 8.6% (1.9) |
| ELITE II | 554 | 16.6% (7.0) | 18.4% (8.1) | 14.0% (3.4) | 11.7% (−2.6) | 11.9% (−6.1) |
| LIFE | 916 | 6.9% (3.7) | 7.3% (3.6) | 7.3% (3.2) | 11.2% (6.0) | 9.4% (2.6) |
| DIONYSOS | 588 | 11.4% (2.7) | 12.6% (3.8) | 6.9% (−2.6) | 8.7% (−0.3) | 6.7% (−4.3) |
| PLATO | 1883 | 14.9% (14.7) | 14.3% (14.1) | 10.1% (9.8) | 2.5% (2.2) | 2.1% (1.7) |
| ARISTOTLE | 911 | 19.9% (16.6) | 20.2% (16.9) | 13.0% (9.2) | 8.1% (3.9) | 7.1% (2.0) |
| ROCKET-AF | 870 | 20.5% (16.8) | 18.9% (14.9) | 13.6% (9.0) | 7.5% (2.0) | 5.9% (−0.9) |
| RE-LY | 419 | 20.4% (5.6) | 20.7% (5.5) | 16.5% (0.6) | 19.0% (2.4) | 16.9% (−2.2) |
| ALLHAT | 6208 | 0.3% (0.3) | 0.2% (0.2) | 0.0% (0.0) | 0.1% (0.1) | 0.0% (0.0) |

With the outpatient restriction, several trials fall to 400–700 pairs, where most residual
long-tail imbalance is within chance once hdPS is added.

## D. Trials: verified benchmarks and emulation-quality rating (proposed)

The rubric was fixed before any outcome. Each item is scored 0–2:
- **(a) Comparator:** exact agents = 2; class or formulation/dose unknown = 1.
- **(b) Key eligibility:** implementable = 2; partial (e.g. EF only when measured) = 1.
- **(c) Time zero/setting:** matches the trial = 2; proxy = 1.
- **(d) Endpoint in the EHR:** all-cause death or stroke/SE = 2; needs cause of death or recurrent
  events = 1; rhythm-based = 0.
- **(e) Data:** ≥ 800 clinical-PS pairs in the primary population = 2; 400–799 = 1; < 400 = 0.

**Close ≥ 8, moderate 6–7, limited ≤ 5.** This is RCT-DUPLICATE in spirit, not their exact
criteria.

| Trial | Published primary result (verified) | a | b | c | d | e | Rating | Main limitation |
|---|---|---|---|---|---|---|---|---|
| PLATO | HR 0.84 (0.77–0.92), vascular death/MI/stroke | 2 | 2 | 2 | 1 | 2 | **close (9)** | no cause of death |
| ARISTOTLE | HR 0.79 (0.66–0.95), stroke/SE | 2 | 1 | 2 | 2 | 2 | **close (9)** | CHADS risk factor not required |
| ROCKET-AF | HR 0.88 (0.74–1.03) ITT, stroke/SE | 2 | 1 | 2 | 2 | 2 | **close (9)** | trial required CHADS2 ≥ 2 |
| LIFE (v2) | HR 0.87 (0.77–0.98), CV death/MI/stroke | 1 | 2 | 2 | 1 | 2 | **close (8)** | class comparator |
| COMET | HR 0.83 (0.74–0.93) carvedilol vs metoprolol, all-cause death | 1 | 1 | 2 | 2 | 1 | moderate (7) | metoprolol formulation unknown |
| TRANSFORM-HF | HR 1.02 (0.89–1.18), all-cause death | 2 | 1 | 1 | 2 | 1 | moderate (7) | HF-discharge time zero is a proxy |
| ELITE II | HR 1.13 (95.7% CI 0.95–1.35), all-cause death | 1 | 1 | 2 | 2 | 1 | moderate (7) | ARB vs ACEi class |
| RE-LY | RR 0.66 (0.53–0.82), stroke/SE (150 mg) | 1 | 1 | 2 | 2 | 1 | moderate (7) | dose unknown |
| ALLHAT | RR 0.98 (0.90–1.07), fatal CHD/nonfatal MI | 1 | 1 | 2 | 1 | 2 | moderate (7) | any thiazide; already balanced |
| DIONYSOS | HR 1.59 (1.28–1.98), AF recurrence or discontinuation | 2 | 1 | 2 | 0 | 1 | moderate (6) | endpoint needs rhythm follow-up |
| PARADIGM-HF | HR 0.80 (0.73–0.87), CV death/first HF hospitalisation | 1 | 1 | 1 | 1 | 1 | **limited (5)** | trial required prior ACEi/ARB; our washout excludes ACEi switchers |
| PARAGON-HF | RR 0.87 (0.75–1.01), total HF hospitalisations + CV death | 2 | 1 | 1 | 1 | 0 | **limited (5)** | 228 pairs; recurrent-event endpoint |
| TRITON | HR 0.81 (0.73–0.90) | – | – | – | – | – | not analysed | failed feasibility (278 prasugrel) |

Sources: COMET [Lancet 2003](https://pubmed.ncbi.nlm.nih.gov/12853193/);
PARADIGM-HF [NEJM 2014](https://www.nejm.org/doi/full/10.1056/NEJMoa1409077);
PARAGON-HF [NEJM 2019](https://www.nejm.org/doi/full/10.1056/NEJMoa1908655);
TRANSFORM-HF [JAMA 2023](https://jamanetwork.com/journals/jama/fullarticle/2800428);
ELITE II [Lancet 2000](https://www.thelancet.com/journals/lancet/article/PIIS0140673600022133/fulltext);
LIFE [Lancet 2002](https://pubmed.ncbi.nlm.nih.gov/11937178/);
DIONYSOS [J Cardiovasc Electrophysiol 2010](https://pubmed.ncbi.nlm.nih.gov/20384650/);
PLATO [NEJM 2009](https://www.nejm.org/doi/full/10.1056/NEJMoa0904327);
TRITON [NEJM 2007](https://www.nejm.org/doi/full/10.1056/NEJMoa0706482);
ARISTOTLE [NEJM 2011](https://www.nejm.org/doi/full/10.1056/NEJMoa1107039);
ROCKET-AF [NEJM 2011](https://www.nejm.org/doi/full/10.1056/NEJMoa1009638);
RE-LY [NEJM 2009](https://www.nejm.org/doi/full/10.1056/NEJMoa0905561);
ALLHAT [JAMA 2002](https://jamanetwork.com/journals/jama/fullarticle/195626).

## E. Open questions and uncertainties

1. **Where is the newest echo report?** I need the full structured extract with wall thickness
   etc. for all echoes; PanEcho covers only 1–5%. With full coverage, the echo panel would
   become the best independent test of whether the ECG captures physiology. It is currently too
   sparse to read.
2. **PARADIGM-HF and PARAGON-HF new-user rule.** Both trials enrolled patients already on an
   ACEi/ARB. Our comparator washout removes ARNI starters who switched from an ACEi, which is the
   usual clinical path. Should they get a v2 "switcher" design (ARNI initiators with prior
   ACEi/ARB vs continuing ACEi/ARB users)? That could move both from "limited" toward "moderate".
3. **The outpatient restriction halves some trials** (COMET 797 pairs, RE-LY 420, PARAGON-HF 297).
   Keep outpatient as primary everywhere, or apply it only where the RCT was clearly an
   outpatient chronic-therapy trial? My recommendation is the latter, which is what I applied for
   PLATO and TRANSFORM-HF.
4. **Should the labs panel stay as an evaluation target?** It shows no residual imbalance under
   any method, so it can't discriminate. Should NT-proBNP (43% measured in HF cohorts) be shown
   alone as the key severity marker?
5. **The rating rubric** (§D) is my proposal. Do you want different weights, or RCT-DUPLICATE's
   exact categories?
6. **For the pre-registration:**
   - Primary sparse base: dx (investigator-selected) with dxall as a sensitivity analysis, or
     the reverse?
   - Primary high-dimensional arm: hdPS200.
   - ECG input: 32 raw PCs.

## F. Suggested next steps

1. You decide E1–E3 and E6. I obtain the full echo extract, and possibly add the ARNI switcher
   variant.
2. Freeze **Protocol v1** (a draft can be written next):
   - trial list with emulation ratings;
   - analysis populations;
   - PS arms (sparse ± ECG, ± hdPS200; clinical as reference);
   - balance metrics and chance correction;
   - the estimate comparison (full-data vs sparse vs sparse + ECG, then RCT agreement);
   - negative-control outcomes.
3. Only then extract outcomes.

## G. Files

- Code: `scripts/`
  - specs and verified benchmarks: `trial_specs.py`;
  - `make_outpatient_cohort.py`, `build_physiology_panel.py`, `run_v3_trial.sh`, `summarize_v3.py`.
- Outputs (restricted, RAID) in `/mnt/raid0/rbc58/ecg-tte/audits/`:
  - `claude-<trial>-{cohort-op, baseline-op, physpanel-v1}`
  - `claude-v3-full[-all]-<trial>`, `claude-v3b-sparse[-all]-<trial>`
