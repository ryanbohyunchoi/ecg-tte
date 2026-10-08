# Spec-v2 cohorts: exclusion-type and outcome fixes to the 38 TRACE-ECG emulations, with the analysis grid re-run

Date: 2026-10-08. User decision (2026-10-08): fix the cohorts rather than penalise them in the emulation-quality scores.

- **Code:** `scripts/v2_cohorts/`.
- **Outputs:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-v2-cohorts/` (umask 077).
- **Nothing existing was edited.** That includes `scripts/trial_specs.py`, the cohort builders, the version 1 scripts, the docs and the explorer. The spec-v2 changes are declared only in `scripts/v2_cohorts/specs_v2.py`.
- Not committed.
- Aggregates only. Counts of 1–10 are suppressed, including counts that could be derived by differencing.

## Plain-language summary

**What was fixed.** Every fix removes patients from the version 1 analysed cohorts, or re-defines an outcome. No index date moves, nobody new is admitted, and no new ECG or CLMBR-T encoding was needed. There are five kinds of fix:

1. **Published numeric entry bounds** (31 trials with at least one patient removed). Each is evaluated on the latest value in the builder's lookback before index (90 days for labs and vitals, 365 days for BMI, 365 days for echo EF; index day excluded). An unknown value passes. The bounds are:
   - HbA1c windows (9 diabetes trials);
   - blood-pressure entry bounds (LIFE, INSIGHT, ASCOT-BPLA, ALLHAT, VALUE) and "uncontrolled BP" exclusions (COMET, ONTARGET, the DOAC trials, DECLARE, EMPEROR-Preserved, PRECISION);
   - natriuretic-peptide thresholds (PARADIGM-HF, EMPEROR-Preserved, RAFT-AF);
   - a total-cholesterol cap (PROVE IT);
   - renal, haemoglobin, platelet, ALT, BMI, heart-rate and LVEF bounds wherever the published criteria state a number.
2. **Age bounds**, checked against the publication for all 38 trials. Only CAROLINA (40–85) removed patients. LODESTAR's ≥19 removed none. In the other 36, the version 1 spec already applies the published hard bound, or a stricter documented one (AFFIRM ≥65, ACTIVE W ≥55; their published routes are risk-factor based).
3. **Class washouts.**
   - Other GLP-1RA: LEADER, SUSTAIN-6, REWIND.
   - Other SGLT2i: DECLARE, CANVAS. Not applicable to EMPA-REG and EMPEROR-Preserved, whose SGLT2i arm is already a first-ever-in-class order.
   - Saxagliptin/alogliptin: EMPEROR-Preserved, DECLARE.
   - Prior ARNI: ELITE II, VALIANT.
   - Metoprolol succinate: COMET.
4. **Gate and population fixes.**
   - LAAOS III: AF must be coded before the index admission.
   - LIFE: a definite ECG-LVH statement is required.
   - COMET: LVEF ≤35%; unknown passes.
   - VALIANT: LV dysfunction or HF is required.
5. **Outcome re-definitions.**
   - AMPLIFY: recurrent VTE now requires a primary-billing VTE stay starting ≥7 days after the index stay. Events fall from 980 to 64.
   - LODESTAR: coronary revascularisation added. Events rise from 5,103 to 5,825.
   - PROVE IT: revascularisation at ≥30 days added. Events rise from 1,116 to 1,193.

**How many patients were removed.** The median across the 38 trials is about 15%.
- Six trials lost nobody: TRANSFORM-HF, PLATO, EAST-AFNET 4, CABANA, AFFIRM and FRAIL-AF. Their version 1 cells are reused.
- Three lost under 1%: AF-CHF, ACTIVE W and LODESTAR (LODESTAR also has the outcome change).
- **The trials that changed most:**

| Trial | Removed | Driven by |
|---|---|---|
| VALIANT | 60.2% | LV dysfunction / HF requirement |
| LAAOS III | 56.6% | AF before admission |
| COMET | 48.9% | LVEF ≤35% and succinate washout |
| LIFE | 42.4% | definite LVH and the BP 160–200 / 95–115 window |
| EMPEROR-Preserved | 24.2% | |
| RE-LY | 24.1% | mostly haemoglobin <10 g/dL |
| CAROLINA | 22.9% | |
| PROTECT AF | 22.9% | |
| INSIGHT | 22.6% | |
| AMPLIFY | 20.1% | |

**Headline: PS-CVD5 + representation vs PS-CVD5.** Main configuration; relative reduction in mean |SMD| over the 54 leakage-corrected items. The version 1 cohort numbers reproduce paper2 exactly.

| Set | + ECG, v1 → v2 | + CLMBR-T, v1 → v2 | + both, v1 → v2 |
|---|---|---|---|
| 32 (paper 1) | 8.8% (4.4–13.3) → **6.6% (2.0–11.4)**, P .004 | 12.4% → **11.4% (4.8–17.5)**, P .001 | 13.5% → **11.6% (4.9–18.8)**, P .001 |
| 29 (provisional) | 9.4% → **6.5% (2.2–11.4)**, P .004 | 11.2% → **10.6% (4.9–16.8)**, P <.001 | 12.6% → **12.7% (6.3–19.6)**, P <.001 |
| 38 | 9.0% → **6.7% (2.5–10.8)**, P .002 | 12.7% → **11.8% (5.7–17.4)**, P <.001 | 14.5% → **12.3% (6.2–18.5)**, P <.001 |

- **Balance holds.** All three gains stay positive and significant in every set (BH q ≤ .025). Against its permuted placebo, the ECG is unchanged: 8.0% → 8.1% (32 trials).
- **The ECG gain shrinks by about a quarter.** Removing the same number of patients per arm at random, 20 times, gives a median ECG gain of 6.9% (5th–95th percentile 2.9–9.3%) in the 32-trial set. That is the same as the spec-v2 value of 6.6%. So the shrinkage reflects re-fitting on smaller cohorts, not anything specific to the fixes. The CLMBR-T and combined gains also stay inside the random-removal range.
- **The agreement gain disappears.** |Δ log HR| vs the RCT, 32 trials:
  - Version 1: + ECG 0.226 → 0.196 (P .049); + CLMBR-T → 0.166 (P .030); + both → 0.158 (P .019).
  - Spec-v2: + ECG 0.213 → 0.222 (P .71); + CLMBR-T → 0.195 (P .31); + both → 0.191 (P .28).
  - The base PS-CVD5 agreement improved with the fixes, from 0.226 to 0.213.
  - Random removal also shrinks the agreement gain. ECG median gain 0.010 (−0.015 to 0.043), vs 0.030 in version 1.
  - The benchmark-permutation P is ≥.68 for every primary contrast in both cohort versions (≥.86 in spec-v2), so there was never a trial-specific agreement signal.
- **Ladder (main configuration, 32 trials).**
  - PS-Demo + ECG: 11.3 → 11.8%.
  - PS-CVD5 + ECG: 8.8 → 6.6%.
  - **hdPS + ECG: 7.6 → −0.3%** (+ CLMBR-T −3.5 → 4.2; + both 8.5 → 3.7).
  - PS-Clinical (no LVEF) + ECG: 4.5 → −3.3%.
  - On hdPS and PS-Clinical (no LVEF), no arm adds significant balance on the spec-v2 cohorts. In the supplement rung CVD10, + both still does (8.0%, P .005).
- **PS-Flags is unstable on the smaller cohorts** (supplement).
  - The ≥1% prevalence filter is re-applied within each fixed cohort. With fixed C = 1, this produces 460–600 flags for cohorts of 800–1,100 patients.
  - PS-Flags base balance degrades: mean |SMD| 0.113 → 0.140; VALIANT 0.13 → 0.39.
  - As a result, "PS-Demo + CLMBR-T vs PS-Flags" moves from 0.7% to 17.7% (P .008).
  - Treat this as an artefact until a sensitivity with the version 1 flag set has been run (see "Caveats").
- **Requiring entry values to be measured** (sensitivity) removes 73–95% of patients in the trials with HbA1c, BP or NT-proBNP entry bounds. In the 32-trial set the gains then shrink:
  - + ECG 4.4% (−2.7 to 10.6), P .13;
  - + CLMBR-T 5.9% (−3.0 to 14.2);
  - + both 7.3% (1.0 to 14.3), P .018.
  - Many PS-Flags and hdPS cells fail (<11 pairs).
- **ECG and CLMBR-T PCs.** The primary analysis refits the PCs within each fixed cohort. With the version 1 PCs instead, the gains are: ECG 4.2%, CLMBR-T 8.6%, both 13.4% (32 trials).

## Gates

| Gate | What it compares | Result |
|---|---|---|
| **Gate A** | The spec-v2 pipeline with no fix applied (every row of each analysed cohort; PCs refit within the cohort; within-cohort placebo permutation; hdPS re-ranking; within-cohort PS-Flags filter) vs the version 1 cells: `claude-v21-paper2/core/restricted_cells.parquet` (P1, P5, Flags, hdPS200, clinical, including CLMBR32 for P1/P5), `claude-v1-ps10/cells` (PS10) and `claude-v1-psclin-nolvef/cells` (clinical_nolvef; clinical CLMBR32). Coverage: 38 trials × 7 rungs × 6 arms × 6 configurations, plus CLMBR32 main. | **Passed exactly.** 9,728 of 9,728 cells; maximum \|deviation\| 0 over rb, rs, p_ps, n, n_t, n_c, n_pairs, log HR, SE, ESS, retention and all 58 SMDs; 0 NaN mismatches; ex58, key and cell_failed identical (`cells/gate_status.json`). |
| Gate A, first attempt | Same comparison | **Failed** (max \|deviation\| 0.079, ARISTOTLE hdPS200 + both). Cause: raw CLMBR-T arrays sliced by row were C-ordered, while version 1 fitted the PCs on pandas' Fortran-ordered array, so the SVD differed in the last bits. Fixed by keeping the memory layout (`grid.subset`); the re-run is exact. **A last-bit perturbation of the PCs moved one matched log HR by 0.08**: matching is that fragile in high-dimensional PS designs. |
| v1 summary | `summarize.py` on the version 1 cells | Reproduces paper2: PS-CVD5 + ECG 8.8% (4.4–13.3), + CLMBR-T 12.4%, + both 13.5% |
| Data-check reproduction | Spec-v2 flags vs `TRIAL_CRITERIA_CHECK.md` | Same shares for every reused flag: COMET succinate 15.1% and LVEF 38.7%; VALIANT 58.7%; LIFE 21.7%; LAAOS III 56.6%; CAROLINA age 11.6%; washouts 2.1 / 8.7 / 5.1 / 7.9 / 8.8%; saxagliptin/alogliptin 1.3 / 3.6%. LODESTAR and PROVE IT event counts are also identical. |

## Methods

**Cohorts.** The version 1 analysed cohort is: completed covariates ∩ ECG embedding ∩ CLMBR-T embedding ∩ phenotypes ∩ panel, with the keys from `audits/claude-v1-criteria/keys`. Equality with `T.keys` is asserted for every trial.

**Spec-v2 cohort** = the version 1 cohort minus the patients flagged by any rule in `specs_v2.rules(n)`:

| Rule type | Definition |
|---|---|
| age | Exact age at index (builder formula) outside the published hard bound. Age routes that belong to risk-factor enrichment are not hard bounds and are not applied. |
| num | Latest plausible value in [index − lookback, index − 1] (`flags.MEASURE`; plausibility ranges as `trial_specs.NUMERIC_CORE`) violates the published bound. **An unknown value passes**, as in the builder. "Treated hypertension" (ASCOT, ALLHAT, VALUE) = an antihypertensive order in [index − 365, index − 1]. AF for the NT-proBNP threshold = an I48 code on or before index. HF hospitalisation = an I50 code inside a merged inpatient stay in the prior 365 days (274 days for RAFT-AF). "On glucose-lowering therapy" / "on a sulfonylurea or glinide" = an order in the prior 12 weeks. |
| flag | Data-check flags (`scripts/v1_criteria_check/s2_flags.py`, reused). Drug windows are [index − 365, index], index day included, as the builder's `other_drugs_365d`. |

**Outcomes.** These are restricted files on `T.keys`; the follow-up horizons are unchanged.
- AMPLIFY: first inpatient stay starting ≥7 days after the end of the index stay with a primary hospital-billing VTE code (I26, I80.1, I80.2, I82.4). Death and data end censor. This is the data check's definition with the 7-day gap.
- LODESTAR and PROVE IT: `s3_reanalysis.outcome_fix` (PCI/CABG codes; after the index stay for LODESTAR, ≥30 days after index for PROVE IT).

**Grid** (`grid.py`; version 1 code imported unchanged).
- Rungs: P1, P5, PS10, Flags, hdPS200, clinical (with LVEF, version 1) and clinical_nolvef.
- Arms: base, ECG, CLMBR, ECG+CLMBR, shufECG and shufCLMBR, in 6 configurations, plus CLMBR32 in the main configuration for P1, P5, clinical and clinical_nolvef. That is 256 cells per trial.
- Each rung's design is built on the full cohort exactly as in version 1, then row-subset.
- **PCs (primary):** ECG 32 PCs and CLMBR-T 64 PCs refit within the fixed cohort from the raw embeddings (pipeline.md §3). Sensitivity: the version 1 PCs restricted to the rows.
- **Placebos:** the arm's PCs permuted within the rows (`default_rng(424242)`, the same as `T.shuffle_perm` when nothing is removed).
- **hdPS:** `T.hd(200, t[rows], rows)` re-ranks the levels within the cohort.
- **PS-Flags:** the ≥1% prevalence filter is computed within the cohort.
- **PS-Clinical (no LVEF):** reuses the re-imputed completed covariates; no re-imputation.
- 32 trials were re-run in each variant. The 6 unchanged trials reuse their version 1 cells.
- Cells: `cells/restricted_cells_{v2,v2old,v2meas}_all.parquet`. They keep the v21 column layout and rung names, with `cohort_spec = 'v2'`, `variant` and `refit` added, so the explorer and figures can switch to them.

**Summaries** (`summarize.py`).
- Endpoints, tests and masks are those of pipeline.md §6, computed through the unchanged `paper2_grid._row`.
- Masks (leakage-corrected): a cell's mask = rung mask ∪ arm mask; placebos take the real arm's mask.
- Primary panel: the 54 non-coded items; the 58-item panel is secondary.
- Cells with <11 matched pairs, or a failed fit, are failed.
- Relative reduction: 4,000-resample trial bootstrap, seed 20261001.
- Exact sign-flip test: one-sided for a representation vs its base or placebo; two-sided for head-to-heads, base-to-base contrasts and placebo vs base.
- |Δ log HR| vs RCT: sign-flip P and benchmark-permutation P (20,000 draws).
- BH-FDR within cohort × set, over the within-rung contrasts × configurations.
- Sets:
  - S32 = paper 1;
  - S29 = the `analysed_set` in `docs/emulation_quality_v2/quality_v2_final.json`;
  - S38 = all 38.
- The sets are defined on the version 1 tiers. The fixes may change some quality scores; re-scoring is not part of this task.

**Random-removal calibration** (`random_removal.py`). For each trial with exclusions, the same number of patients per arm is removed at random, 20 draws per trial. PS-CVD5 base, + ECG, + CLMBR-T and + both are refit in the main configuration, with PCs within the reduced cohort. The pooled values are then compared with spec-v2.

## Sensitivity variants

| Variant | Rows | PCs | Purpose |
|---|---|---|---|
| **v2** (primary) | spec-v2 rules, unknown passes | refit within the cohort | |
| v2old | as v2 | version 1 PCs | effect of refitting the PCs |
| v2meas | as v2, plus the **entry** bounds must be measured: HbA1c windows, the BP entry windows of LIFE / INSIGHT / ASCOT-BPLA / ALLHAT / VALUE, NT-proBNP / BNP thresholds, PARADIGM-HF LVEF ≤35%, PROVE IT cholesterol cap, COMET LVEF | refit within the cohort | "require the value to be measured". Safety-type exclusions (renal, Hb, platelets, ALT, BMI, heart rate, EF exclusions, "uncontrolled BP") keep "unknown passes": requiring all of them as well removed 75–98% of most cohorts. |

## Per-trial rule sets and sources

The full rule table, with every rule's definition, source and share removed, is in the appendix ("Per rule").

**Source key.** Criteria were read in the primary source (paper, design paper, protocol, registry or FDA review) unless marked "secondary" (ACC summary, review, or a document reproducing the criteria). Many NEJM/Lancet full texts and supplements were not accessible; the protocols posted on ClinicalTrials.gov, FDA medical reviews, EudraCT, BioLINCC and PMC were used instead.

### Heart failure / post-MI

| Trial | Spec-v2 rules (beyond the version 1 spec) | Source |
|---|---|---|
| **COMET** | Succinate washout (JDAT succinate-named order in [index − 365, index]). LVEF ≤35% (latest echo EF >35% excluded). SBP >170 or DBP >105, SBP <85, heart rate <60 excluded. | Poole-Wilson, Lancet 2003;362:7 (Methods, full text) |
| **PARADIGM-HF** | Latest EF >35% excluded (amended LVEF ≤35%). NT-proBNP ≥600 or BNP ≥150 required (≥400 / ≥100 with an HF hospitalisation in the prior 12 months). ALT >2× ULN excluded. Already in the spec: SBP <100, eGFR <30, K >5.2. | design paper, Eur J Heart Fail 2013 (PMC3746839), Table 2; NCT01035255 |
| **TRANSFORM-HF** | None: there is no numeric NT-proBNP cut-off in the protocol. | protocol v2.0 (NCT03296813) |
| **ELITE II** | Prior ARNI excluded. DBP >95 and creatinine >2.5 mg/dL excluded. | Pitt, Lancet 2000; ACC summary (secondary, for DBP and creatinine) |
| **EMPEROR-Preserved** | Saxagliptin/alogliptin excluded. NT-proBNP >300 (>900 with an AF code) required. BMI ≥45, SBP ≥180, heart rate >110 with AF, Hb <9 and ALT >3× ULN excluded. Already in the spec: EF >40, eGFR <20, SBP <100. | protocol §3.3 (NCT03057951) |
| **VALIANT** | Prior ARNI excluded. LV dysfunction or HF required: latest EF >40% in [index − 365, index] excluded, and EF unknown without an I50 code excluded (data-check definition; index-day echo included). Creatinine ≥2.5 mg/dL excluded. | NEJM 2003 abstract and Methods excerpts; ACC summary |
| **AF-CHF** | Heart rate <50 excluded (pacemaker not identifiable). | NCT00597077 |
| **RAFT-AF** | NT-proBNP ≥400 with an HF hospitalisation in the prior 9 months, otherwise ≥600. These are the sinus-rhythm thresholds: rhythm at sampling is unknown, so the lower thresholds are used. | Circulation 2022 supplement, Table S1 |

### Hypertension

BP is the latest SBP and DBP on prior treatment; the trials' placebo run-in values cannot be reproduced.

| Trial | Spec-v2 rules | Source |
|---|---|---|
| **LIFE** | Definite ECG-LVH statement required (data-check A ∪ B hedged list). SBP 160–200 and/or DBP 95–115 required. EF ≤40% excluded. | Dahlöf, Lancet 2002 (full text) |
| **INSIGHT** | BP ≥150/95 or SBP ≥160 required. EF <40% excluded. | Lancet 2000 abstract; ACC summary (secondary) |
| **ASCOT-BPLA** | Untreated: SBP ≥160 or DBP ≥100 required. Treated: SBP ≥140 or DBP ≥90 required. | Sever, J Hypertens 2001; Lancet 2005 |
| **ALLHAT** | Untreated: SBP ≥140 or DBP ≥90, and ≤180/110, required. Treated: ≤160/100 (visit 1) required. EF <35% and creatinine ≥2.0 excluded. | ALLHAT protocol (BioLINCC); JAMA 2002 |
| **VALUE** | Untreated: SBP 160–210 and DBP <115 required. Treated: SBP ≤210 and DBP <115 required. Creatinine >3.0 mg/dL excluded. | Julius, Lancet 2004 (full text) |
| **ONTARGET** | BP >160/100, creatinine >3.0 mg/dL and ALT >4× ULN excluded. Already in the spec: K >5.5. | NCT00153101 |

### Anticoagulation / AF / devices

Creatinine clearance is approximated by eGFR, as in the version 1 specs.

| Trial | Spec-v2 rules | Source |
|---|---|---|
| **ARISTOTLE** | SBP >180 or DBP >100, creatinine >2.5, eGFR <25, platelets ≤100, Hb <9 and ALT >2× ULN excluded. | FDA medical review NDA 202155 |
| **ROCKET AF** | SBP ≥180 or DBP ≥100, platelets <90, Hb <10, eGFR <30 and ALT >3× ULN excluded. | FDA medical review NDA 202439 |
| **RE-LY** | SBP >180 or DBP >100, eGFR <30, Hb <10, platelets <100 and ALT >2× ULN excluded. | FDA medical review NDA 22-512 |
| **AMPLIFY** | SBP >180 or DBP >100 (secondary source), Hb <9, platelets <100, creatinine >2.5, eGFR <25 and ALT >2× ULN excluded. Outcome re-defined. | JAHA 2015 (PMC4845271) |
| **PROTECT AF** | EF <30%, platelets <100 and Hb <10 excluded. | NCT00129545; FDA SSED P130013 |
| **ACTIVE W** | Platelets <50 excluded. | NCT00243178 |
| **LAAOS III** | AF coded before the index admission required (data-check flag). | data check; NCT01561651 |
| **PLATO, EAST-AFNET 4, CABANA, AFFIRM, FRAIL-AF** | No hard numeric bound beyond age (risk-factor routes only). FRAIL-AF's eGFR <30 is already in the spec. | as listed in the appendix |

### Diabetes CVOTs

HbA1c is the latest value within 90 days.

| Trial | Spec-v2 rules | Source |
|---|---|---|
| **EMPA-REG** | HbA1c 7.0–10.0% required (7.0–9.0% if no glucose-lowering order in the prior 12 weeks). BMI >45 and ALT >3× ULN excluded. | design paper (PMC4072621) |
| **CAROLINA** | Age 40–85 required. HbA1c 6.5–8.5% required (6.5–7.5% on a sulfonylurea or glinide). BMI >45 and ALT >3× ULN excluded. | protocol rev. 6 (NCT01243424) |
| **LEADER** | Other-GLP-1RA washout. HbA1c ≥7.0% required. | NEJM 2016; EudraCT 2009-012201-19 |
| **SUSTAIN-6** | Other-GLP-1RA washout (oral semaglutide counted as the same molecule). HbA1c ≥7.0% required. | NCT01720446 |
| **REWIND** | Other-GLP-1RA washout. HbA1c ≤9.5% required. BMI <23 and ALT ≥3× ULN excluded. | protocol (NCT01394952) |
| **DECLARE-TIMI 58** | Saxagliptin/alogliptin and other-SGLT2i washouts. HbA1c <6.5% or ≥12% excluded. SBP >180 or DBP >100 and ALT >3× ULN excluded. Already in the spec: eGFR <60. | protocol v5.0 (NCT01730534) |
| **CANVAS** | Other-SGLT2i washout. HbA1c 7.0–10.5% required. ALT >2× ULN excluded. | protocols DIA3008 / DIA4003 |
| **TECOS** | HbA1c 6.5–8.0% required. | EudraCT 2008-006719-20 |
| **CARMELINA** | HbA1c 6.5–10.0% required. BMI >45 and ALT ≥3× ULN excluded. | protocol 1218.22; design paper (PMC5870815) |

### Other

| Trial | Spec-v2 rules | Source |
|---|---|---|
| **PRECISION** | SBP >140 or DBP >90 excluded. **Secondary source:** a document reproducing the design paper's Table I. A threshold of about 150/95 is also recalled; this is unverified. Creatinine >1.7 (men) / >1.5 (women), EF ≤35% and ALT >2× ULN excluded. | Becker, Am Heart J 2009, as reproduced in a secondary document |
| **LODESTAR** | Age ≥19 (no patient removed). ALT >3× ULN excluded. Outcome adds revascularisation. | Hong, **JAMA** 2023;329:1078, Table S1 |
| **PROVE IT-TIMI 22** | Total cholesterol ≤240 mg/dL required (secondary source; the ClinicalTrials.gov text inverts this rule). Creatinine >2.0 excluded. Outcome adds revascularisation ≥30 days. | NEJM 2004; PMC3097284 |

**Assumption.** For the "× ULN" rules, ULN = 40 U/L for ALT. The laboratory-specific ULN is not in OMOP gold.

## Could not apply, or approximated (and why)

- **Risk-factor enrichment routes** (code-defined, EL-type), for example:
  - LEADER ≥60 route; SUSTAIN-6, REWIND, DECLARE and CANVAS risk-factor routes; the CAROLINA risk route;
  - CHADS-type requirements (ROCKET AF, RE-LY, ACTIVE W, PROTECT AF);
  - EAST-AFNET 4, CABANA and AFFIRM risk routes;
  - the risk-factor counts in ALLHAT, ASCOT, VALUE and INSIGHT.
  - These are criteria, not numeric bounds, and are out of scope.
- **Measurement timing cannot be reproduced.** Affected criteria:
  - BP after a placebo run-in (LIFE, INSIGHT) or at randomisation (EMPEROR SBP ≥180);
  - run-in thresholds (PARADIGM-HF SBP <95, K >5.4, eGFR decline);
  - PROVE IT total cholesterol within 24 hours of ACS;
  - natriuretic peptide by rhythm at sampling (RAFT-AF; EMPEROR via an AF code).
  - Each is approximated by the latest value before index.
- **Not extractable or not identifiable:**
  - fasting status (fasting glucose in EMPA-REG and CAROLINA; fasting triglycerides in ASCOT);
  - bilirubin, calcitonin, CK and UACR / proteinuria;
  - LA diameter (RAFT-AF >55 mm) and the EMPEROR structural-heart-disease criteria;
  - NYHA class, HF duration, diuretic or ACEi dose (COMET, PARADIGM-HF) and drug counts (EMPEROR: SBP 150–180 requires ≥3 antihypertensives);
  - pacemaker status (AF-CHF heart rate <50);
  - ECG voltage criteria (LIFE Cornell / Sokolow-Lyon), so the text gate is used;
  - "LVEF never ≤40%" (EMPEROR history);
  - the DECLARE HbA1c 6.5–7% quota;
  - the alternatives to LVEF (COMET LVEDD/FS, VALIANT wall-motion index), which matter only when EF is unknown, and unknown passes anyway.
- **Approximations:**
  - creatinine clearance → CKD-EPI eGFR;
  - ALT ULN 40 U/L;
  - HF hospitalisation = an I50 code within an inpatient stay;
  - "treated" hypertension = any antihypertensive order in the prior year;
  - "on therapy" = an order in the prior 12 weeks.
- **COMET** uses echo-metadata EF; the JDAT roster used the JDAT echo table. The COMET roster itself was not rebuilt.
- **Data-check items confirmed "not present" and not changed:** COMET succinate in the metoprolol arm, and ARNI entering the ELITE II / VALIANT ARB arms via 'valsartan'.

## Out of scope (needs a full rebuild; left as is)

1. **CABANA:** earliest-index dedupe and arm assignment. Needs a sequential design.
2. **TRANSFORM-HF:** time zero and the discharge anchor.
3. **Any fix that would admit patients at a later index date.** Examples:
   - a later sitagliptin start after saxagliptin;
   - a later first GLP-1RA or SGLT2i after a washout failure;
   - a later definite-LVH ECG (LIFE) or a later qualifying HbA1c / BP / NT-proBNP;
   - a VALIANT or LAAOS III re-entry at a later qualifying event;
   - COMET re-built from JDAT with EF ≤35% at roster stage.
4. **Sequential designs not resampled.** PARADIGM-HF (seq), EAST-AFNET 4, AFFIRM, AF-CHF, FRAIL-AF, PROTECT AF and RAFT-AF had their comparators sampled before the exclusions. Removing patients leaves the remaining sampled sets, and does not re-sample comparators for retained switchers.
5. **New ECG or CLMBR-T encodings:** none were needed, because no patient was added.

## Caveats

- **The fixed cohorts are smaller, so every refit is noisier.**
  - Random removal of the same number of patients shrinks the PS-CVD5 + ECG gain as much as the actual fixes do. So the v1 → v2 change in the ECG gain is not evidence that the fixes removed ECG-favourable patients.
  - A more plausible reading is that version 1's full-cohort point estimate sat in the upper part of what near-equivalent cohorts produce.
- **High-dimensional PS rungs degrade in small cohorts at fixed C = 1.** This affects hdPS and especially PS-Flags; for PS-Flags, the within-cohort ≥1% filter admits more flags as n falls.
  - The spec-v2 head-to-heads that involve PS-Flags or hdPS should not be read as substantive until a sensitivity is run with the version 1 flag columns (or a prevalence floor in patients rather than per cent).
  - That sensitivity has not been run.
- **The quality-tier sets (S32, S29) were not re-scored after the fixes.** The SI defects that the fixes remove may change tiers.
- **"Unknown passes" keeps most patients without a measured entry value.** In the hypertension and diabetes trials, the share meeting the published entry window when it is measured is often low (for example ASCOT-BPLA). The v2meas sensitivity, which requires the value, removes most patients and widens every CI.

## Files

- **Code (`scripts/v2_cohorts/`):**
  - `v2common.py`: paths, sets, suppression.
  - `specs_v2.py`: rules.
  - `flags.py`: inputs, outcomes and rules applied.
  - `grid.py`: cells, gate A and assembly.
  - `summarize.py`: contrasts, domains, ladder, per trial.
  - `random_removal.py`.
  - `tables.py`.
  - `privacy_scan.py`.
  - `run_all.sh`.
- **Aggregate outputs:**
  - `flags/exclusions_by_trial.csv`, `exclusions_by_rule.csv`, `measured_share.csv`, `outcome_events.csv`;
  - `cells/gate.csv`, `gate_status.json`, `cells_*_all.csv` (suppressed; count columns blanked for AF-CHF and ACTIVE W, where an arm lost fewer than 11 patients);
  - `summary/contrasts.csv`, `domains.csv`, `ladder.csv`, `per_trial.csv`, `failed_cells.csv`, `random_removal*.csv`, `tables.md`;
  - `privacy_scan.json`.
- **Restricted (never commit):**
  - `flags/restricted_meas_*.parquet`, `restricted_drop_*.parquet`, `restricted_outcome_*.parquet`;
  - `cells/restricted_cells_*.parquet`;
  - `summary/restricted_random_removal_cells.parquet`.

## Appendix: tables

Generated by `scripts/v2_cohorts/tables.py` from the aggregate CSVs. "m54" = mean |SMD| over the 54 items; "Rel. red." in %; P values one-sided for a representation vs its base or placebo, two-sided where marked. Percentages shown as "<x" hide counts of 1–10.

### Random-removal calibration (PS-CVD5, main configuration; 20 draws removing the same number of patients per arm at random)

| Set | Arm | Rel. red. 54, v1 | spec-v2 | random removal: median (5th–95th pct) | share of draws ≤ spec-v2 | \|dlog HR\| gain v1 | spec-v2 | random: median (5th–95th) |
|---|---|---|---|---|---|---|---|---|
| S32 | + ECG | 8.8 | 6.6 | 6.9 (2.8 to 9.3) | 0.45 | 0.030 | -0.010 | 0.010 (-0.015 to 0.043) |
| S32 | + CLMBR-T | 12.4 | 11.4 | 10.4 (7.3 to 14.3) | 0.60 | 0.060 | 0.018 | 0.014 (-0.009 to 0.037) |
| S32 | + both | 13.5 | 11.6 | 12.3 (10.0 to 15.5) | 0.40 | 0.068 | 0.021 | 0.026 (-0.009 to 0.047) |
| S29 | + ECG | 9.4 | 6.5 | 6.9 (4.0 to 8.4) | 0.35 | 0.023 | -0.011 | 0.004 (-0.016 to 0.027) |
| S29 | + CLMBR-T | 11.2 | 10.6 | 10.4 (6.7 to 14.7) | 0.55 | 0.043 | 0.015 | 0.010 (-0.009 to 0.035) |
| S29 | + both | 12.6 | 12.7 | 13.7 (11.2 to 16.0) | 0.35 | 0.054 | 0.014 | 0.020 (0.002 to 0.044) |
| S38 | + ECG | 9.0 | 6.7 | 7.0 (3.2 to 9.6) | 0.40 | 0.029 | -0.007 | 0.008 (-0.013 to 0.039) |
| S38 | + CLMBR-T | 12.7 | 11.8 | 10.9 (7.8 to 14.2) | 0.60 | 0.061 | 0.022 | 0.018 (0.002 to 0.038) |
| S38 | + both | 14.5 | 12.3 | 12.8 (10.9 to 15.4) | 0.35 | 0.070 | 0.022 | 0.032 (0.002 to 0.047) |

### Per trial: fixes and share removed

| Trial | S32 | S29 | Fix types applied | Rules removing patients | % removed (v2) | treated / comparator | % removed (entry values measured) |
|---|---|---|---|---|---|---|---|
| COMET | yes | yes | numeric, washout/class, gate/population | comet_succinate_365; comet_lvef_le35; bp_le170_105; sbp_ge85; hr_ge60 | 48.9 | 57.2 / 43.2 | 75.9 |
| PARADIGM-HF | yes | yes | numeric | lvef_le35; natriuretic_peptide; alt_gt2uln | 17.3 | 22.7 / 15.5 | 85.9 |
| TRANSFORM-HF | yes | yes | none (no patient removed) | - | 0.0 | 0.0 / 0.0 | 0.0 |
| ELITE II | yes | yes | numeric, washout/class | arni_365; dbp_le95; creat_le2_5 | 7.1 | 9.0 / 5.5 | 7.1 |
| LIFE | yes | yes | numeric, gate/population | definite_lvh; bp_life; lvef_gt40 | 42.4 | 43.6 / 41.7 | 95.0 |
| PLATO | yes | yes | none (no patient removed) | - | 0.0 | 0.0 / 0.0 | 0.0 |
| ARISTOTLE | yes | yes | numeric | bp_le180_100; creat_le2_5; egfr_ge25; plt_gt100; hb_ge9; alt_gt2uln | 12.8 | 11.3 / 19.7 | 12.8 |
| ROCKET-AF | yes | yes | numeric | bp_lt180_100; plt_ge90; hb_ge10; egfr_ge30; alt_gt3uln | 16.8 | 8.6 / 25.5 | 16.8 |
| RE-LY | yes | yes | numeric | bp_le180_100; egfr_ge30; hb_ge10; plt_ge100; alt_gt2uln | 24.1 | 8.5 / 27.2 | 24.1 |
| ALLHAT |  | yes | numeric | bp_allhat; lvef_ge35; creat_lt2 | 9.2 | 9.9 / 7.6 | 83.5 |
| EMPEROR-Preserved | yes |  | numeric, washout/class | saxa_alo_365; ntprobnp_300_900; bmi_lt45; sbp_lt180; hr_le110_af; hb_ge9; alt_gt3uln | 24.2 | 25.2 / 22.6 | 80.2 |
| EAST-AFNET 4 | yes | yes | none (no patient removed) | - | 0.0 | 0.0 / 0.0 | 0.0 |
| CABANA | yes |  | none (no patient removed) | - | 0.0 | 0.0 / 0.0 | 0.0 |
| ONTARGET |  | yes | numeric | bp_le160_100; creat_le3; alt_gt4uln | 4.3 | 4.9 / 3.8 | 4.3 |
| VALUE |  | yes | numeric | bp_value; creat_le3 | 9.0 | 8.9 / 9.1 | 84.6 |
| ASCOT-BPLA |  | yes | numeric | bp_ascot | 16.6 | 13.3 / 20.1 | 90.7 |
| EMPA-REG OUTCOME | yes | yes | numeric | hba1c_empareg; bmi_le45; alt_gt3uln | 17.8 | 18.8 / 16.4 | 86.3 |
| CAROLINA | yes | yes | numeric, age | age_40_85; hba1c_carolina; bmi_le45; alt_gt3uln | 22.9 | 24.7 / 20.7 | 91.2 |
| LEADER | yes |  | numeric, washout/class | other_glp1_365; hba1c_7.0_None | 9.4 | 12.1 / 9.0 | 77.8 |
| SUSTAIN-6 | yes |  | numeric, washout/class | other_glp1_365; hba1c_7.0_None | 17.4 | 26.0 / 10.3 | 81.8 |
| REWIND |  |  | numeric, washout/class | other_glp1_365; hba1c_None_9.5; bmi_ge23; alt_lt3uln | 15.0 | 21.8 / 13.1 | 82.2 |
| DECLARE-TIMI 58 |  |  | numeric, washout/class | saxa_alo_365; other_sglt2_365; hba1c_6.5_12.0; bp_le180_100; alt_gt3uln | 18.9 | 22.2 / 17.5 | 83.2 |
| CANVAS Program | yes |  | numeric, washout/class | other_sglt2_365; hba1c_7.0_10.5; alt_gt2uln | 19.5 | 21.4 / 19.4 | 85.3 |
| TECOS | yes | yes | numeric | hba1c_6.5_8.0 | 17.3 | 17.8 / 16.8 | 88.9 |
| CARMELINA | yes | yes | numeric | hba1c_6.5_10.0; bmi_le45; alt_lt3uln | 14.8 | 14.3 / 15.3 | 76.0 |
| VALIANT | yes | yes | numeric, washout/class, gate/population | arni_365; valiant_lvd_or_hf; creat_lt2_5 | 60.2 | 58.6 / 60.9 | 60.2 |
| INSIGHT | yes | yes | numeric | bp_insight; lvef_ge40 | 22.6 | 15.9 / 22.9 | 93.9 |
| AFFIRM | yes | yes | none (no patient removed) | - | 0.0 | 0.0 / 0.0 | 0.0 |
| AF-CHF | yes | yes | numeric | hr_ge50 | 0.3 | <0.9 / 0.3 | 0.3 |
| PRECISION | yes | yes | numeric | bp_le140_90; creat_sex; lvef_gt35; alt_gt2uln | 13.2 | 13.4 / 13.0 | 13.2 |
| AMPLIFY | yes |  | numeric, outcome | bp_le180_100; hb_ge9; plt_ge100; creat_le2_5; egfr_ge25; alt_gt2uln | 20.1 | 19.5 / 22.1 | 20.1 |
| LODESTAR | yes | yes | numeric, outcome | alt_gt3uln | 0.6 | 0.6 / 0.6 | 0.6 |
| PROVE IT-TIMI 22 | yes | yes | numeric, outcome | tc_le240; creat_le2 | 6.2 | 6.3 / 5.8 | 75.2 |
| FRAIL-AF | yes | yes | none (no patient removed) | - | 0.0 | 0.0 / 0.0 | 0.0 |
| LAAOS III | yes | yes | gate/population | af_before_admission | 56.6 | 23.1 / 64.7 | 56.6 |
| PROTECT AF | yes | yes | numeric | lvef_ge30; plt_ge100; hb_ge10 | 22.9 | 15.0 / 25.1 | 22.9 |
| RAFT-AF | yes | yes | numeric | ntprobnp_raft | 4.4 | 6.2 / 3.9 | 73.2 |
| ACTIVE W | yes |  | numeric | plt_ge50 | <0.4 | 0.0 / <0.5 | <0.4 |

### Per rule

| Trial | Rule | Fix | Definition | Source | % removed | treated / comparator | % removed, measured required |
|---|---|---|---|---|---|---|---|
| COMET | age_18_None | 2 | exclude if age 18- not met (age at index) | COMET (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| COMET | comet_succinate_365 | 3 | exclude metoprolol succinate-named JDAT order in [index-365, index] (prior/concurrent succinate; both arms) | TRIAL_CRITERIA_CHECK; COMET | 15.1 | 19.5 / 12.0 | 15.1 |
| COMET | comet_lvef_le35 | 4 | exclude latest echo EF > 35% in [index-365, index-1] (unknown passes; v2meas: EF must be measured) | COMET (LVEF <= 35%) | 38.7 | 45.8 / 33.7 | 71.4 |
| COMET | bp_le170_105 | 1 | exclude SBP > 170 or DBP > 105 mmHg | COMET | 1.5 | 1.3 / 1.7 | 1.5 |
| COMET | sbp_ge85 | 1 | exclude SBP < 85 mmHg | COMET | 0.2 | <0.4 / <0.3 | 0.2 |
| COMET | hr_ge60 | 1 | exclude resting heart rate < 60 bpm | COMET | 2.1 | 2.5 / 1.9 | 2.1 |
| PARADIGM-HF | age_18_None | 2 | exclude if age 18- not met (age at index) | PARADIGM-HF (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| PARADIGM-HF | lvef_le35 | 1 | exclude latest echo EF > 35% | PARADIGM-HF (amended LVEF <= 35%) | 11.3 | 16.7 / 9.6 | 71.3 |
| PARADIGM-HF | natriuretic_peptide | 1 | require NT-proBNP >= 600 or BNP >= 150 pg/mL (>= 400 / >= 100 if an HF hospitalisation in the prior 12 months); exclude if measured and neither qualifies | PARADIGM-HF | 4.4 | 3.5 / 4.6 | 72.6 |
| PARADIGM-HF | alt_gt2uln | 1 | exclude ALT > 2 x ULN (ULN assumed 40 U/L, i.e. > 80 U/L) | PARADIGM-HF | 2.8 | 4.2 / 2.4 | 2.8 |
| TRANSFORM-HF | age_18_None | 2 | exclude if age 18- not met (age at index) | TRANSFORM-HF (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ELITE II | age_60_None | 2 | exclude if age 60- not met (age at index) | ELITE II (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ELITE II | arni_365 | 3 | exclude ARNI (sacubitril/entresto) order in [index-365, index], both arms | TRIAL_CRITERIA_CHECK; ELITE II (ACEi-naive) | 4.0 | 6.6 / 1.9 | 4.0 |
| ELITE II | dbp_le95 | 1 | exclude DBP > 95 mmHg | ELITE II | 0.7 | 0.7 / 0.7 | 0.7 |
| ELITE II | creat_le2_5 | 1 | exclude creatinine > 2.5 mg/dL (220 umol/L) | ELITE II | 2.6 | 2.1 / 3.1 | 2.6 |
| LIFE | age_55_80 | 2 | exclude if age 55-80 not met (age at index) | LIFE (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| LIFE | definite_lvh | 4 | require a definite ECG-LVH statement: exclude patients whose only LVH statements are minimal-voltage / normal-variant, possible / cannot-rule-out or negated | TRIAL_CRITERIA_CHECK; LIFE (ECG-LVH) | 21.7 | 25.7 / 19.1 | 21.7 |
| LIFE | bp_life | 1 | require SBP 160-200 and/or DBP 95-115 mmHg (SBP >= 160 or DBP >= 95, and SBP <= 200 and DBP <= 115) | LIFE | 23.2 | 20.0 / 25.3 | 94.3 |
| LIFE | lvef_gt40 | 1 | exclude latest echo EF <= 40% | LIFE | 0.5 | <0.9 / <0.6 | 0.5 |
| PLATO | age_18_None | 2 | exclude if age 18- not met (age at index) | PLATO (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ARISTOTLE | age_18_None | 2 | exclude if age 18- not met (age at index) | ARISTOTLE (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ARISTOTLE | bp_le180_100 | 1 | exclude SBP > 180 or DBP > 100 mmHg | ARISTOTLE | 0.7 | 0.6 / 0.8 | 0.7 |
| ARISTOTLE | creat_le2_5 | 1 | exclude creatinine > 2.5 mg/dL | ARISTOTLE | 3.3 | 2.7 / 6.0 | 3.3 |
| ARISTOTLE | egfr_ge25 | 1 | exclude eGFR < 25 (CrCl < 25 mL/min approximated by eGFR) | ARISTOTLE | 2.7 | 2.5 / 3.9 | 2.7 |
| ARISTOTLE | plt_gt100 | 1 | exclude platelets <= 100 x 10^9/L | ARISTOTLE | 2.2 | 1.8 / 4.1 | 2.2 |
| ARISTOTLE | hb_ge9 | 1 | exclude haemoglobin < 9 g/dL | ARISTOTLE | 6.5 | 5.8 / 10.0 | 6.5 |
| ARISTOTLE | alt_gt2uln | 1 | exclude ALT > 2 x ULN (ULN assumed 40 U/L, i.e. > 80 U/L) | ARISTOTLE | 2.6 | 2.5 / 3.2 | 2.6 |
| ROCKET-AF | age_18_None | 2 | exclude if age 18- not met (age at index) | ROCKET-AF (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ROCKET-AF | bp_lt180_100 | 1 | exclude SBP >= 180 or DBP >= 100 mmHg | ROCKET AF | 0.9 | 0.9 / 1.0 | 0.9 |
| ROCKET-AF | plt_ge90 | 1 | exclude platelets < 90 x 10^9/L | ROCKET AF | 1.6 | 0.7 / 2.6 | 1.6 |
| ROCKET-AF | hb_ge10 | 1 | exclude haemoglobin < 10 g/dL | ROCKET AF | 13.4 | 6.3 / 20.9 | 13.4 |
| ROCKET-AF | egfr_ge30 | 1 | exclude eGFR < 30 (CrCl < 30 approximated) | ROCKET AF | 2.6 | 0.7 / 4.7 | 2.6 |
| ROCKET-AF | alt_gt3uln | 1 | exclude ALT > 3 x ULN (ULN assumed 40 U/L, i.e. > 120 U/L) | ROCKET AF | 1.4 | 1.0 / 1.8 | 1.4 |
| RE-LY | age_18_None | 2 | exclude if age 18- not met (age at index) | RE-LY (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| RE-LY | bp_le180_100 | 1 | exclude SBP > 180 or DBP > 100 mmHg | RE-LY | 0.7 | <1.6 / 0.8 | 0.7 |
| RE-LY | egfr_ge30 | 1 | exclude eGFR < 30 (CrCl < 30 approximated) | RE-LY | 4.1 | <1.6 / 4.8 | 4.1 |
| RE-LY | hb_ge10 | 1 | exclude haemoglobin < 10 g/dL | RE-LY | 18.4 | 5.3 / 21.0 | 18.4 |
| RE-LY | plt_ge100 | 1 | exclude platelets < 100 x 10^9/L | RE-LY | 3.5 | 1.7 / 3.9 | 3.5 |
| RE-LY | alt_gt2uln | 1 | exclude ALT > 2 x ULN (ULN assumed 40 U/L, i.e. > 80 U/L) | RE-LY | 3.0 | 2.0 / 3.2 | 3.0 |
| ALLHAT | age_55_None | 2 | exclude if age 55- not met (age at index) | ALLHAT (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ALLHAT | bp_allhat | 1 | require SBP >= 140 or DBP >= 90 and <= 180/110 mmHg if untreated; <= 160/100 if treated (visit 1) | ALLHAT | 7.2 | 7.5 / 6.6 | 83.0 |
| ALLHAT | lvef_ge35 | 1 | exclude latest echo EF < 35% | ALLHAT | 0.1 | 0.1 / 0.2 | 0.1 |
| ALLHAT | creat_lt2 | 1 | exclude creatinine >= 2.0 mg/dL | ALLHAT | 2.1 | 2.7 / 0.9 | 2.1 |
| EMPEROR-Preserved | age_18_None | 2 | exclude if age 18- not met (age at index) | EMPEROR-Preserved (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| EMPEROR-Preserved | saxa_alo_365 | 3 | exclude saxagliptin/alogliptin order in [index-365, index] (removes them from the DPP-4i comparator) | TRIAL_CRITERIA_CHECK; R2 must-fix | 1.3 | 0.0 / 3.4 | 1.3 |
| EMPEROR-Preserved | ntprobnp_300_900 | 1 | require NT-proBNP > 300 pg/mL (> 900 with an AF code on/before index); exclude if measured and below | EMPEROR-Preserved | 9.8 | 11.1 / 7.9 | 74.1 |
| EMPEROR-Preserved | bmi_lt45 | 1 | exclude BMI >= 45 kg/m2 (365 d) | EMPEROR-Preserved | 6.4 | 8.1 / 3.8 | 6.4 |
| EMPEROR-Preserved | sbp_lt180 | 1 | exclude SBP >= 180 mmHg | EMPEROR-Preserved | 1.1 | 1.2 / <1.2 | 1.1 |
| EMPEROR-Preserved | hr_le110_af | 1 | exclude heart rate > 110 bpm in patients with an AF code | EMPEROR-Preserved | <0.5 | <0.7 / <1.2 | <0.5 |
| EMPEROR-Preserved | hb_ge9 | 1 | exclude haemoglobin < 9 g/dL | EMPEROR-Preserved | 7.6 | 6.5 / 9.3 | 7.6 |
| EMPEROR-Preserved | alt_gt3uln | 1 | exclude ALT > 3 x ULN (ULN assumed 40 U/L, i.e. > 120 U/L) | EMPEROR-Preserved | 0.5 | <0.7 / <1.2 | 0.5 |
| EAST-AFNET 4 | age_18_None | 2 | exclude if age 18- not met (age at index) | EAST-AFNET 4 (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| CABANA | age_18_None | 2 | exclude if age 18- not met (age at index) | CABANA (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ONTARGET | age_55_None | 2 | exclude if age 55- not met (age at index) | ONTARGET (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ONTARGET | bp_le160_100 | 1 | exclude BP > 160/100 mmHg | ONTARGET | 3.5 | 4.1 / 3.0 | 3.5 |
| ONTARGET | creat_le3 | 1 | exclude creatinine > 265 umol/L (3.0 mg/dL) | ONTARGET | 0.6 | 0.6 / 0.5 | 0.6 |
| ONTARGET | alt_gt4uln | 1 | exclude ALT > 4 x ULN (ULN assumed 40 U/L, i.e. > 160 U/L) | ONTARGET | 0.3 | 0.3 / 0.3 | 0.3 |
| VALUE | age_50_None | 2 | exclude if age 50- not met (age at index) | VALUE (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| VALUE | bp_value | 1 | require SBP 160-210 and DBP < 115 mmHg if untreated; SBP <= 210 and DBP < 115 if treated | VALUE | 8.1 | 8.7 / 7.7 | 84.4 |
| VALUE | creat_le3 | 1 | exclude creatinine > 265 umol/L (3.0 mg/dL) | VALUE | 1.0 | 0.3 / 1.5 | 1.0 |
| ASCOT-BPLA | age_40_79 | 2 | exclude if age 40-79 not met (age at index) | ASCOT-BPLA (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ASCOT-BPLA | bp_ascot | 1 | require SBP >= 160 or DBP >= 100 mmHg if untreated, SBP >= 140 or DBP >= 90 if treated | ASCOT-BPLA | 16.6 | 13.3 / 20.1 | 90.7 |
| EMPA-REG OUTCOME | age_18_None | 2 | exclude if age 18- not met (age at index) | EMPA-REG OUTCOME (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| EMPA-REG OUTCOME | hba1c_empareg | 1 | require HbA1c 7.0-10.0% if on glucose-lowering therapy in the prior 12 weeks, 7.0-9.0% if drug-naive | EMPA-REG OUTCOME | 14.2 | 15.0 / 13.3 | 85.4 |
| EMPA-REG OUTCOME | bmi_le45 | 1 | exclude BMI > 45 kg/m2 | EMPA-REG OUTCOME | 3.6 | 4.1 / 2.9 | 3.6 |
| EMPA-REG OUTCOME | alt_gt3uln | 1 | exclude ALT > 3 x ULN (ULN assumed 40 U/L, i.e. > 120 U/L) | EMPA-REG OUTCOME | 0.7 | 0.7 / 0.8 | 0.7 |
| CAROLINA | age_40_85 | 2 | exclude if age 40-85 not met (age at index) | CAROLINA (published age bound) | 11.6 | 12.1 / 11.1 | 11.6 |
| CAROLINA | hba1c_carolina | 1 | require HbA1c 6.5-8.5% (6.5-7.5% if on a sulfonylurea or glinide in the prior 12 weeks) | CAROLINA | 10.2 | 12.9 / 7.1 | 89.3 |
| CAROLINA | bmi_le45 | 1 | exclude BMI > 45 kg/m2 | CAROLINA | 2.1 | 1.7 / 2.6 | 2.1 |
| CAROLINA | alt_gt3uln | 1 | exclude ALT > 3 x ULN (ULN assumed 40 U/L, i.e. > 120 U/L) | CAROLINA | <0.6 | <1.1 / <1.3 | <0.6 |
| LEADER | age_50_None | 2 | exclude if age 50- not met (age at index) | LEADER (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| LEADER | other_glp1_365 | 3 | exclude other-GLP-1RA order in [index-365, index] | TRIAL_CRITERIA_CHECK; LEADER | 2.1 | 6.2 / 1.6 | 2.1 |
| LEADER | hba1c_7.0_None | 1 | require HbA1c >= 7.0% | LEADER | 7.3 | 6.2 / 7.4 | 77.2 |
| SUSTAIN-6 | age_50_None | 2 | exclude if age 50- not met (age at index) | SUSTAIN-6 (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| SUSTAIN-6 | other_glp1_365 | 3 | exclude other-GLP-1RA order in [index-365, index] | TRIAL_CRITERIA_CHECK; SUSTAIN-6 | 8.7 | 16.5 / 2.1 | 8.7 |
| SUSTAIN-6 | hba1c_7.0_None | 1 | require HbA1c >= 7.0% | SUSTAIN-6 | 9.1 | 10.2 / 8.2 | 80.3 |
| REWIND | age_50_None | 2 | exclude if age 50- not met (age at index) | REWIND (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| REWIND | other_glp1_365 | 3 | exclude other-GLP-1RA order in [index-365, index] | TRIAL_CRITERIA_CHECK; REWIND | 5.1 | 15.2 / 2.2 | 5.1 |
| REWIND | hba1c_None_9.5 | 1 | require HbA1c <= 9.5% | REWIND | 7.3 | 6.7 / 7.4 | 80.2 |
| REWIND | bmi_ge23 | 1 | exclude BMI < 23 kg/m2 | REWIND | 2.7 | 1.0 / 3.2 | 2.7 |
| REWIND | alt_lt3uln | 1 | exclude ALT >= 3 x ULN (ULN assumed 40 U/L) | REWIND | 0.7 | <0.8 / 0.8 | 0.7 |
| DECLARE-TIMI 58 | age_40_None | 2 | exclude if age 40- not met (age at index) | DECLARE-TIMI 58 (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| DECLARE-TIMI 58 | saxa_alo_365 | 3 | exclude saxagliptin/alogliptin order in [index-365, index] | TRIAL_CRITERIA_CHECK; R2 must-fix | 3.6 | 0.0 / 5.1 | 3.6 |
| DECLARE-TIMI 58 | other_sglt2_365 | 3 | exclude other-SGLT2i order in [index-365, index] | TRIAL_CRITERIA_CHECK; DECLARE | 8.8 | 13.2 / 6.9 | 8.8 |
| DECLARE-TIMI 58 | hba1c_6.5_12.0 | 1 | exclude HbA1c < 6.5% or >= 12.0% | DECLARE-TIMI 58 | 6.1 | 8.3 / 5.2 | 80.7 |
| DECLARE-TIMI 58 | bp_le180_100 | 1 | exclude SBP > 180 or DBP > 100 mmHg | DECLARE-TIMI 58 | 0.7 | 0.8 / 0.7 | 0.7 |
| DECLARE-TIMI 58 | alt_gt3uln | 1 | exclude ALT > 3 x ULN (ULN assumed 40 U/L, i.e. > 120 U/L) | DECLARE-TIMI 58 | 0.8 | 0.8 / 0.9 | 0.8 |
| CANVAS Program | age_30_None | 2 | exclude if age 30- not met (age at index) | CANVAS Program (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| CANVAS Program | other_sglt2_365 | 3 | exclude other-SGLT2i order in [index-365, index] | TRIAL_CRITERIA_CHECK; CANVAS | 7.9 | 14.4 / 7.3 | 7.9 |
| CANVAS Program | hba1c_7.0_10.5 | 1 | require HbA1c 7.0-10.5% | CANVAS / CANVAS-R | 10.8 | 8.2 / 11.0 | 83.3 |
| CANVAS Program | alt_gt2uln | 1 | exclude ALT > 2 x ULN (ULN assumed 40 U/L, i.e. > 80 U/L) | CANVAS / CANVAS-R | 2.1 | <2.3 / 2.2 | 2.1 |
| TECOS | age_50_None | 2 | exclude if age 50- not met (age at index) | TECOS (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| TECOS | hba1c_6.5_8.0 | 1 | require HbA1c 6.5-8.0% | TECOS | 17.3 | 17.8 / 16.8 | 88.9 |
| CARMELINA | age_18_None | 2 | exclude if age 18- not met (age at index) | CARMELINA (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| CARMELINA | hba1c_6.5_10.0 | 1 | require HbA1c 6.5-10.0% | CARMELINA | 11.8 | 12.2 / 11.3 | 74.8 |
| CARMELINA | bmi_le45 | 1 | exclude BMI > 45 kg/m2 | CARMELINA | 3.2 | 2.5 / 3.9 | 3.2 |
| CARMELINA | alt_lt3uln | 1 | exclude ALT >= 3 x ULN (ULN assumed 40 U/L) | CARMELINA | 0.8 | <1.4 / <1.5 | 0.8 |
| VALIANT | age_18_None | 2 | exclude if age 18- not met (age at index) | VALIANT (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| VALIANT | arni_365 | 3 | exclude ARNI order in [index-365, index], both arms | TRIAL_CRITERIA_CHECK; VALIANT | 1.0 | 2.1 / <0.8 | 1.0 |
| VALIANT | valiant_lvd_or_hf | 4 | require LV dysfunction or HF: exclude latest echo EF > 40% in [index-365, index] (index-day echo included) and exclude EF unknown without an I50 code on/before index | VALIANT (LVEF <= 40% and/or HF) | 58.7 | 56.4 / 59.8 | 58.7 |
| VALIANT | creat_lt2_5 | 1 | exclude creatinine >= 2.5 mg/dL | VALIANT | 0.6 | <1.6 / 0.8 | 0.6 |
| INSIGHT | age_55_80 | 2 | exclude if age 55-80 not met (age at index) | INSIGHT (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| INSIGHT | bp_insight | 1 | require BP >= 150/95 mmHg or SBP >= 160 mmHg | INSIGHT | 22.4 | 15.9 / 22.8 | 93.8 |
| INSIGHT | lvef_ge40 | 1 | exclude latest echo EF < 40% | INSIGHT | 0.2 | <2.8 / 0.2 | 0.2 |
| AFFIRM | age_18_None | 2 | exclude if age 18- not met (age at index) | AFFIRM (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| AF-CHF | age_18_None | 2 | exclude if age 18- not met (age at index) | AF-CHF (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| AF-CHF | hr_ge50 | 1 | exclude heart rate < 50 bpm (pacemaker not identifiable) | AF-CHF | 0.3 | <0.9 / 0.3 | 0.3 |
| PRECISION | age_18_None | 2 | exclude if age 18- not met (age at index) | PRECISION (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| PRECISION | bp_le140_90 | 1 | exclude uncontrolled BP: SBP > 140 or DBP > 90 mmHg | PRECISION (design paper Table I, secondary source) | 10.9 | 12.0 / 10.0 | 10.9 |
| PRECISION | creat_sex | 1 | exclude creatinine > 1.7 (men) / > 1.5 (women) mg/dL | PRECISION | 1.3 | 0.9 / 1.6 | 1.3 |
| PRECISION | lvef_gt35 | 1 | exclude latest echo EF <= 35% | PRECISION | 0.5 | <0.5 / 0.8 | 0.5 |
| PRECISION | alt_gt2uln | 1 | exclude ALT > 2 x ULN (ULN assumed 40 U/L, i.e. > 80 U/L) | PRECISION | 0.8 | 0.5 / 1.0 | 0.8 |
| AMPLIFY | age_18_None | 2 | exclude if age 18- not met (age at index) | AMPLIFY (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| AMPLIFY | bp_le180_100 | 1 | exclude SBP > 180 or DBP > 100 mmHg | AMPLIFY | 0.8 | 0.8 / <1.1 | 0.8 |
| AMPLIFY | hb_ge9 | 1 | exclude haemoglobin < 9 g/dL | AMPLIFY | 13.2 | 12.9 / 14.4 | 13.2 |
| AMPLIFY | plt_ge100 | 1 | exclude platelets < 100 x 10^9/L | AMPLIFY | 1.9 | 1.8 / 2.6 | 1.9 |
| AMPLIFY | creat_le2_5 | 1 | exclude creatinine > 2.5 mg/dL | AMPLIFY | 3.3 | 2.6 / 6.5 | 3.3 |
| AMPLIFY | egfr_ge25 | 1 | exclude eGFR < 25 (CrCl < 25 approximated) | AMPLIFY | 2.5 | 2.2 / 3.6 | 2.5 |
| AMPLIFY | alt_gt2uln | 1 | exclude ALT > 2 x ULN (ULN assumed 40 U/L, i.e. > 80 U/L) | AMPLIFY | 4.2 | 4.3 / 3.8 | 4.2 |
| LODESTAR | age_19_None | 2 | exclude if age 19- not met (age at index) | LODESTAR (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| LODESTAR | alt_gt3uln | 1 | exclude ALT > 3 x ULN (ULN assumed 40 U/L, i.e. > 120 U/L) | LODESTAR | 0.6 | 0.6 / 0.6 | 0.6 |
| PROVE IT-TIMI 22 | age_18_None | 2 | exclude if age 18- not met (age at index) | PROVE IT-TIMI 22 (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| PROVE IT-TIMI 22 | tc_le240 | 1 | require total cholesterol <= 240 mg/dL (not on statin: other-statin washout in the spec; window 90 d before index, not the trial's 24 h after ACS) | PROVE IT-TIMI 22 | 2.7 | 2.7 / 2.8 | 74.1 |
| PROVE IT-TIMI 22 | creat_le2 | 1 | exclude creatinine > 2.0 mg/dL | PROVE IT-TIMI 22 | 3.7 | 3.7 / 3.0 | 3.7 |
| FRAIL-AF | age_75_None | 2 | exclude if age 75- not met (age at index) | FRAIL-AF (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| LAAOS III | age_18_None | 2 | exclude if age 18- not met (age at index) | LAAOS III (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| LAAOS III | af_before_admission | 4 | require AF coded before the index admission: exclude first-ever I48 dated within the index inpatient stay (or on the index day without a stay) | TRIAL_CRITERIA_CHECK; LAAOS III (pre-existing AF) | 56.6 | 23.1 / 64.7 | 56.6 |
| PROTECT AF | age_18_None | 2 | exclude if age 18- not met (age at index) | PROTECT AF (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| PROTECT AF | lvef_ge30 | 1 | exclude latest echo EF < 30% | PROTECT AF | 6.2 | <3.5 / 7.4 | 6.2 |
| PROTECT AF | plt_ge100 | 1 | exclude platelets < 100 x 10^9/L | PROTECT AF | 2.4 | <3.5 / 2.4 | 2.4 |
| PROTECT AF | hb_ge10 | 1 | exclude haemoglobin < 10 g/dL | PROTECT AF | 17.1 | 12.1 / 18.5 | 17.1 |
| RAFT-AF | age_18_None | 2 | exclude if age 18- not met (age at index) | RAFT-AF (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| RAFT-AF | ntprobnp_raft | 1 | require NT-proBNP >= 400 pg/mL with an HF hospitalisation in the prior 9 months, else >= 600 (the sinus-rhythm thresholds; rhythm at sampling not identifiable, so the lower thresholds are used) | RAFT-AF | 4.4 | 6.2 / 3.9 | 73.2 |
| ACTIVE W | age_18_None | 2 | exclude if age 18- not met (age at index) | ACTIVE W (published age bound) | 0.0 | 0.0 / 0.0 | 0.0 |
| ACTIVE W | plt_ge50 | 1 | exclude platelets < 50 x 10^9/L | ACTIVE W | <0.4 | 0.0 / <0.5 | <0.4 |

### Headline: PS-CVD5 + representation vs PS-CVD5, main configuration

| Set | Contrast | Cohorts | m54 base -> arm | Rel. red. 54 (95% CI) | Trials better | P | q | Rel. red. 58 (95% CI) | abs dlogHR base -> arm | Closer | P (sign-flip) | P (benchmark perm.) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S32 | PS-CVD5 + ECG vs PS-CVD5 | v1 cohorts | 0.130 -> 0.118 | 8.8 (4.4 to 13.3) | 21/32 | <.001 | 0.003 | 8.8 (4.5 to 13.2) | 0.226 -> 0.196 | 20/32 | 0.049 | 0.698 |
| S32 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2 (primary) | 0.134 -> 0.125 | 6.6 (2.0 to 11.4) | 22/32 | 0.004 | 0.025 | 6.6 (2.1 to 11.3) | 0.213 -> 0.222 | 14/32 | 0.712 | 0.952 |
| S32 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2, v1 PCs | 0.134 -> 0.129 | 4.2 (-0.5 to 9.0) | 22/32 | 0.043 | 0.159 | 4.2 (-0.4 to 8.9) | 0.213 -> 0.219 | 20/32 | 0.621 | 0.501 |
| S32 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2, entry values measured | 0.187 -> 0.179 | 4.4 (-2.7 to 10.6) | 20/32 | 0.131 | 0.359 | 4.2 (-2.8 to 10.2) | 0.297 -> 0.253 | 15/32 | 0.194 | 0.379 |
| S32 | PS-CVD5 + CLMBR-T vs PS-CVD5 | v1 cohorts | 0.130 -> 0.114 | 12.4 (7.1 to 17.7) | 23/32 | <.001 | <.001 | 12.4 (7.1 to 17.7) | 0.226 -> 0.166 | 18/32 | 0.030 | 0.934 |
| S32 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2 (primary) | 0.134 -> 0.119 | 11.4 (4.8 to 17.5) | 25/32 | 0.001 | 0.009 | 11.4 (4.8 to 17.5) | 0.213 -> 0.195 | 17/32 | 0.307 | 0.921 |
| S32 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2, v1 PCs | 0.134 -> 0.123 | 8.6 (2.3 to 15.3) | 22/32 | 0.007 | 0.044 | 8.6 (2.3 to 15.3) | 0.213 -> 0.169 | 17/32 | 0.111 | 0.837 |
| S32 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2, entry values measured | 0.186 -> 0.175 | 5.9 (-3.0 to 14.2) | 21/32 | 0.114 | 0.328 | 5.9 (-3.0 to 14.2) | 0.297 -> 0.225 | 17/31 | 0.086 | 0.593 |
| S32 | PS-CVD5 + both vs PS-CVD5 | v1 cohorts | 0.130 -> 0.112 | 13.5 (6.6 to 20.4) | 23/32 | <.001 | 0.003 | 13.5 (6.6 to 20.4) | 0.226 -> 0.158 | 18/32 | 0.019 | 0.944 |
| S32 | PS-CVD5 + both vs PS-CVD5 | spec-v2 (primary) | 0.134 -> 0.119 | 11.6 (4.9 to 18.8) | 25/32 | 0.001 | 0.009 | 11.6 (4.9 to 18.8) | 0.213 -> 0.191 | 19/32 | 0.280 | 0.947 |
| S32 | PS-CVD5 + both vs PS-CVD5 | spec-v2, v1 PCs | 0.134 -> 0.116 | 13.4 (6.2 to 20.4) | 23/32 | <.001 | 0.005 | 13.4 (6.2 to 20.4) | 0.213 -> 0.178 | 20/32 | 0.168 | 0.941 |
| S32 | PS-CVD5 + both vs PS-CVD5 | spec-v2, entry values measured | 0.178 -> 0.165 | 7.3 (1.0 to 14.3) | 23/30 | 0.018 | 0.101 | 7.3 (1.0 to 14.3) | 0.297 -> 0.290 | 15/30 | 0.546 | 0.945 |
| S29 | PS-CVD5 + ECG vs PS-CVD5 | v1 cohorts | 0.116 -> 0.105 | 9.4 (4.5 to 14.4) | 20/29 | <.001 | 0.004 | 9.3 (4.5 to 14.3) | 0.202 -> 0.179 | 17/29 | 0.097 | 0.902 |
| S29 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2 (primary) | 0.120 -> 0.112 | 6.5 (2.2 to 11.4) | 21/29 | 0.004 | 0.021 | 6.5 (2.2 to 11.3) | 0.176 -> 0.188 | 15/29 | 0.802 | 0.955 |
| S29 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2, v1 PCs | 0.120 -> 0.114 | 5.2 (0.8 to 9.6) | 22/29 | 0.012 | 0.058 | 5.2 (0.8 to 9.6) | 0.176 -> 0.187 | 19/29 | 0.686 | 0.466 |
| S29 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2, entry values measured | 0.158 -> 0.153 | 3.0 (-4.1 to 10.0) | 19/29 | 0.229 | 0.439 | 2.9 (-4.2 to 9.8) | 0.248 -> 0.249 | 12/29 | 0.505 | 0.712 |
| S29 | PS-CVD5 + CLMBR-T vs PS-CVD5 | v1 cohorts | 0.116 -> 0.103 | 11.2 (5.8 to 16.7) | 22/29 | <.001 | 0.001 | 11.2 (5.8 to 16.7) | 0.202 -> 0.160 | 16/29 | 0.057 | 0.926 |
| S29 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2 (primary) | 0.120 -> 0.107 | 10.6 (4.9 to 16.8) | 22/29 | <.001 | 0.005 | 10.6 (4.9 to 16.8) | 0.176 -> 0.161 | 17/29 | 0.279 | 0.859 |
| S29 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2, v1 PCs | 0.120 -> 0.112 | 6.3 (0.3 to 12.6) | 20/29 | 0.023 | 0.092 | 6.3 (0.3 to 12.6) | 0.176 -> 0.169 | 15/29 | 0.399 | 0.878 |
| S29 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2, entry values measured | 0.157 -> 0.154 | 1.5 (-6.8 to 10.2) | 19/29 | 0.370 | 0.591 | 1.5 (-6.8 to 10.2) | 0.248 -> 0.191 | 17/28 | 0.107 | 0.544 |
| S29 | PS-CVD5 + both vs PS-CVD5 | v1 cohorts | 0.116 -> 0.101 | 12.6 (4.8 to 20.8) | 20/29 | 0.002 | 0.014 | 12.6 (4.8 to 20.8) | 0.202 -> 0.148 | 18/29 | 0.014 | 0.838 |
| S29 | PS-CVD5 + both vs PS-CVD5 | spec-v2 (primary) | 0.120 -> 0.105 | 12.7 (6.3 to 19.6) | 24/29 | <.001 | 0.003 | 12.7 (6.3 to 19.6) | 0.176 -> 0.163 | 19/29 | 0.295 | 0.877 |
| S29 | PS-CVD5 + both vs PS-CVD5 | spec-v2, v1 PCs | 0.120 -> 0.104 | 12.9 (6.8 to 19.4) | 21/29 | <.001 | 0.002 | 12.9 (6.8 to 19.4) | 0.176 -> 0.161 | 19/29 | 0.282 | 0.844 |
| S29 | PS-CVD5 + both vs PS-CVD5 | spec-v2, entry values measured | 0.146 -> 0.135 | 8.1 (1.7 to 15.9) | 21/27 | 0.010 | 0.057 | 8.1 (1.7 to 15.9) | 0.248 -> 0.259 | 14/27 | 0.751 | 0.917 |
| S38 | PS-CVD5 + ECG vs PS-CVD5 | v1 cohorts | 0.124 -> 0.112 | 9.0 (5.0 to 13.5) | 26/38 | <.001 | <.001 | 9.0 (5.1 to 13.3) | 0.224 -> 0.195 | 23/38 | 0.033 | 0.684 |
| S38 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2 (primary) | 0.127 -> 0.118 | 6.7 (2.5 to 10.8) | 27/38 | 0.002 | 0.009 | 6.7 (2.5 to 10.7) | 0.212 -> 0.219 | 19/38 | 0.691 | 0.964 |
| S38 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2, v1 PCs | 0.127 -> 0.121 | 4.9 (0.7 to 9.0) | 28/38 | 0.014 | 0.060 | 4.9 (0.8 to 9.0) | 0.212 -> 0.211 | 26/38 | 0.491 | 0.356 |
| S38 | PS-CVD5 + ECG vs PS-CVD5 | spec-v2, entry values measured | 0.177 -> 0.170 | 4.1 (-2.3 to 9.9) | 24/38 | 0.118 | 0.297 | 3.9 (-2.3 to 9.6) | 0.292 -> 0.260 | 18/38 | 0.233 | 0.400 |
| S38 | PS-CVD5 + CLMBR-T vs PS-CVD5 | v1 cohorts | 0.124 -> 0.108 | 12.7 (8.0 to 17.6) | 29/38 | <.001 | <.001 | 12.7 (8.0 to 17.6) | 0.224 -> 0.162 | 22/38 | 0.011 | 0.902 |
| S38 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2 (primary) | 0.127 -> 0.112 | 11.8 (5.7 to 17.4) | 30/38 | <.001 | 0.002 | 11.8 (5.7 to 17.4) | 0.212 -> 0.190 | 21/38 | 0.231 | 0.919 |
| S38 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2, v1 PCs | 0.127 -> 0.115 | 9.3 (3.1 to 15.2) | 28/38 | 0.002 | 0.011 | 9.3 (3.1 to 15.2) | 0.212 -> 0.170 | 21/38 | 0.080 | 0.836 |
| S38 | PS-CVD5 + CLMBR-T vs PS-CVD5 | spec-v2, entry values measured | 0.176 -> 0.166 | 5.9 (-2.4 to 13.6) | 26/38 | 0.085 | 0.238 | 5.9 (-2.4 to 13.6) | 0.292 -> 0.223 | 21/37 | 0.056 | 0.619 |
| S38 | PS-CVD5 + both vs PS-CVD5 | v1 cohorts | 0.124 -> 0.106 | 14.5 (8.1 to 20.6) | 29/38 | <.001 | <.001 | 14.5 (8.1 to 20.6) | 0.224 -> 0.154 | 22/38 | 0.006 | 0.912 |
| S38 | PS-CVD5 + both vs PS-CVD5 | spec-v2 (primary) | 0.127 -> 0.111 | 12.3 (6.2 to 18.5) | 31/38 | <.001 | 0.001 | 12.3 (6.2 to 18.5) | 0.212 -> 0.189 | 23/38 | 0.236 | 0.949 |
| S38 | PS-CVD5 + both vs PS-CVD5 | spec-v2, v1 PCs | 0.127 -> 0.110 | 13.6 (7.4 to 19.8) | 28/38 | <.001 | <.001 | 13.6 (7.4 to 19.8) | 0.212 -> 0.175 | 24/38 | 0.110 | 0.916 |
| S38 | PS-CVD5 + both vs PS-CVD5 | spec-v2, entry values measured | 0.169 -> 0.157 | 7.4 (1.6 to 13.9) | 27/36 | 0.008 | 0.048 | 7.4 (1.6 to 13.9) | 0.292 -> 0.274 | 19/36 | 0.438 | 0.920 |

### All six configurations (relative reduction 54 items, %; P balance; P |dlog HR|)

| Set | Config | + ECG v1 | + ECG v2 | + CLMBR-T v1 | + CLMBR-T v2 | + both v1 | + both v2 |
|---|---|---|---|---|---|---|---|
| S32 | main | 8.8 (P <.001; dHR P 0.049) | 6.6 (P 0.004; dHR P 0.712) | 12.4 (P <.001; dHR P 0.030) | 11.4 (P 0.001; dHR P 0.307) | 13.5 (P <.001; dHR P 0.019) | 11.6 (P 0.001; dHR P 0.280) |
| S32 | cal01 | 7.8 (P 0.001; dHR P 0.113) | 6.4 (P 0.004; dHR P 0.392) | 10.1 (P 0.002; dHR P 0.129) | 13.5 (P <.001; dHR P 0.315) | 15.8 (P <.001; dHR P 0.037) | 12.9 (P <.001; dHR P 0.309) |
| S32 | m13 | 6.4 (P <.001; dHR P 0.007) | 5.2 (P <.001; dHR P 0.273) | 13.3 (P <.001; dHR P 0.036) | 9.8 (P 0.004; dHR P 0.016) | 13.6 (P <.001; dHR P 0.020) | 11.9 (P <.001; dHR P 0.079) |
| S32 | iptw | 4.8 (P 0.003; dHR P 0.690) | 2.4 (P 0.120; dHR P 0.538) | -2.0 (P 0.622; dHR P 0.366) | -1.1 (P 0.581; dHR P 0.388) | -0.9 (P 0.517; dHR P 0.377) | 0.9 (P 0.422; dHR P 0.329) |
| S32 | overlap | 7.4 (P <.001; dHR P 0.011) | 5.3 (P <.001; dHR P 0.056) | 13.6 (P <.001; dHR P 0.135) | 11.4 (P <.001; dHR P 0.047) | 16.2 (P <.001; dHR P 0.087) | 13.2 (P <.001; dHR P 0.029) |
| S32 | gbm | -1.1 (P 0.629; dHR P 0.318) | 7.3 (P 0.004; dHR P 0.715) | 6.9 (P 0.017; dHR P 0.249) | 11.7 (P <.001; dHR P 0.386) | 13.2 (P <.001; dHR P 0.152) | 11.3 (P 0.001; dHR P 0.221) |
| S29 | main | 9.4 (P <.001; dHR P 0.097) | 6.5 (P 0.004; dHR P 0.802) | 11.2 (P <.001; dHR P 0.057) | 10.6 (P <.001; dHR P 0.279) | 12.6 (P 0.002; dHR P 0.014) | 12.7 (P <.001; dHR P 0.295) |
| S29 | cal01 | 8.8 (P 0.001; dHR P 0.163) | 5.9 (P 0.006; dHR P 0.515) | 8.9 (P 0.004; dHR P 0.165) | 12.4 (P <.001; dHR P 0.312) | 14.0 (P 0.001; dHR P 0.037) | 11.8 (P <.001; dHR P 0.477) |
| S29 | m13 | 7.4 (P <.001; dHR P 0.017) | 6.1 (P <.001; dHR P 0.059) | 13.1 (P <.001; dHR P 0.031) | 9.3 (P 0.006; dHR P 0.058) | 14.9 (P <.001; dHR P 0.004) | 13.9 (P <.001; dHR P 0.114) |
| S29 | iptw | 6.9 (P <.001; dHR P 0.559) | 4.9 (P 0.002; dHR P 0.445) | 4.2 (P 0.319; dHR P 0.708) | 3.0 (P 0.277; dHR P 0.580) | 1.9 (P 0.482; dHR P 0.676) | 3.9 (P 0.236; dHR P 0.549) |
| S29 | overlap | 7.9 (P <.001; dHR P 0.003) | 5.4 (P 0.001; dHR P 0.037) | 14.2 (P <.001; dHR P 0.184) | 11.4 (P <.001; dHR P 0.108) | 17.0 (P <.001; dHR P 0.094) | 13.4 (P <.001; dHR P 0.053) |
| S29 | gbm | 3.0 (P 0.077; dHR P 0.288) | 8.2 (P 0.004; dHR P 0.269) | 8.8 (P 0.002; dHR P 0.577) | 13.9 (P <.001; dHR P 0.662) | 13.5 (P <.001; dHR P 0.166) | 11.7 (P 0.001; dHR P 0.212) |
| S38 | main | 9.0 (P <.001; dHR P 0.033) | 6.7 (P 0.002; dHR P 0.691) | 12.7 (P <.001; dHR P 0.011) | 11.8 (P <.001; dHR P 0.231) | 14.5 (P <.001; dHR P 0.006) | 12.3 (P <.001; dHR P 0.236) |
| S38 | cal01 | 8.3 (P <.001; dHR P 0.080) | 6.5 (P 0.002; dHR P 0.286) | 10.1 (P <.001; dHR P 0.070) | 13.3 (P <.001; dHR P 0.237) | 16.5 (P <.001; dHR P 0.014) | 12.6 (P <.001; dHR P 0.255) |
| S38 | m13 | 6.5 (P <.001; dHR P 0.008) | 5.5 (P <.001; dHR P 0.232) | 13.5 (P <.001; dHR P 0.013) | 9.8 (P 0.001; dHR P 0.007) | 14.1 (P <.001; dHR P 0.006) | 12.5 (P <.001; dHR P 0.040) |
| S38 | iptw | 5.1 (P <.001; dHR P 0.572) | 2.9 (P 0.059; dHR P 0.448) | -0.7 (P 0.547; dHR P 0.296) | -0.4 (P 0.530; dHR P 0.305) | 0.8 (P 0.482; dHR P 0.307) | 2.1 (P 0.307; dHR P 0.256) |
| S38 | overlap | 7.8 (P <.001; dHR P 0.004) | 5.7 (P <.001; dHR P 0.031) | 13.8 (P <.001; dHR P 0.075) | 11.7 (P <.001; dHR P 0.022) | 17.0 (P <.001; dHR P 0.044) | 14.0 (P <.001; dHR P 0.012) |
| S38 | gbm | -0.2 (P 0.534; dHR P 0.508) | 6.5 (P 0.004; dHR P 0.637) | 6.8 (P 0.010; dHR P 0.260) | 11.4 (P <.001; dHR P 0.218) | 13.2 (P <.001; dHR P 0.091) | 10.9 (P <.001; dHR P 0.099) |

### Ladder, S32, main configuration (relative reduction 54 items, %)

| PS level | base mean SMD54 v1 | base mean SMD54 v2 | + ECG v1 | + ECG v2 | + CLMBR-T v1 | + CLMBR-T v2 | + both v1 | + both v2 |
|---|---|---|---|---|---|---|---|---|
| PS-Demo | 0.143 | 0.146 | 11.3 (P <.001) | 11.8 (P <.001) | 20.7 (P <.001) | 18.8 (P <.001) | 25.8 (P <.001) | 20.1 (P <.001) |
| PS-CVD5 | 0.130 | 0.134 | 8.8 (P <.001) | 6.6 (P 0.004) | 12.4 (P <.001) | 11.4 (P 0.001) | 13.5 (P <.001) | 11.6 (P 0.001) |
| hdPS | 0.118 | 0.126 | 7.6 (P 0.008) | -0.3 (P 0.553) | -3.5 (P 0.714) | 4.2 (P 0.092) | 8.5 (P 0.008) | 3.7 (P 0.119) |
| PS-Clinical (no LVEF) | 0.117 | 0.122 | 4.5 (P 0.114) | -3.3 (P 0.755) | 1.5 (P 0.359) | -0.1 (P 0.509) | 4.0 (P 0.160) | -1.7 (P 0.662) |
| CVD10 (supplement) | 0.121 | 0.124 | 5.0 (P 0.051) | 3.2 (P 0.162) | 7.4 (P 0.009) | 3.6 (P 0.083) | 7.0 (P 0.018) | 8.0 (P 0.005) |
| PS-Flags (supplement) | 0.113 | 0.140 | -3.0 (P 0.902) | -2.4 (P 0.729) | -2.9 (P 0.821) | -12.4 (P 0.971) | -6.3 (P 0.854) | -6.6 (P 0.789) |
| PS-Clinical (with LVEF, v1) (v1 reference) | 0.113 | 0.122 | -1.7 (P 0.712) | -4.8 (P 0.892) | 1.5 (P 0.258) | -3.0 (P 0.825) | -0.5 (P 0.554) | 1.5 (P 0.383) |

### Base-to-base and head-to-heads, S32, main

| Contrast (two-sided) | v1 | v2 |
|---|---|---|
| P1 base vs P5 base | -10.9 (-18.5 to -3.8), P 0.005; dHR 0.226->0.251 P 0.276 | -8.3 (-15.0 to -2.1), P 0.013; dHR 0.213->0.276 P 0.008 |
| hdPS200 base vs P5 base | 8.6 (1.1 to 15.1), P 0.027; dHR 0.226->0.181 P 0.269 | 6.2 (-3.3 to 14.8), P 0.204; dHR 0.213->0.206 P 0.899 |
| clinical_nolvef base vs P5 base | 9.0 (2.9 to 14.6), P 0.006; dHR 0.226->0.150 P 0.014 | 10.5 (4.7 to 17.1), P <.001; dHR 0.213->0.167 P 0.176 |
| PS10 base vs P5 base | 6.8 (2.4 to 11.2), P 0.005; dHR 0.226->0.208 P 0.412 | 7.6 (3.1 to 12.3), P 0.005; dHR 0.213->0.242 P 0.225 |
| Flags base vs P5 base | 12.3 (5.9 to 18.3), P 0.001; dHR 0.226->0.186 P 0.149 | -4.8 (-22.7 to 8.1), P 0.634; dHR 0.213->0.259 P 0.507 |
| P1+CLMBR vs Flags base | 0.7 (-5.5 to 6.8), P 0.814; dHR 0.186->0.170 P 0.495 | 17.7 (6.2 to 28.8), P 0.008; dHR 0.259->0.197 P 0.098 |
| P5+CLMBR vs hdPS200 base | 3.8 (-2.7 to 9.6), P 0.260; dHR 0.181->0.166 P 0.357 | 5.7 (-1.3 to 12.3), P 0.148; dHR 0.206->0.195 P 0.767 |
| P5+ECG+CLMBR vs hdPS200 base | 5.5 (-1.5 to 11.6), P 0.115; dHR 0.181->0.158 P 0.263 | 5.6 (-0.6 to 11.6), P 0.105; dHR 0.206->0.191 P 0.627 |
| P5+CLMBR vs clinical_nolvef base | -0.1 (-6.2 to 5.5), P 0.977; dHR 0.150->0.166 P 0.288 | -1.7 (-10.5 to 6.0), P 0.707; dHR 0.167->0.195 P 0.194 |
| P5+ECG+CLMBR vs clinical_nolvef base | -0.3 (-9.5 to 7.8), P 0.942; dHR 0.150->0.158 P 0.590 | -1.6 (-10.0 to 6.3), P 0.708; dHR 0.167->0.191 P 0.275 |
| P5+ECG vs clinical_nolvef base | -0.2 (-6.9 to 6.2), P 0.964; dHR 0.150->0.196 P 0.047 | -3.8 (-10.8 to 2.2), P 0.263; dHR 0.167->0.222 P 0.041 |

### Placebos and head-to-heads within rung, S32, main

| PS level | Contrast | sided | v1 | v2 |
|---|---|---|---|---|
| PS-CVD5 | shufECG vs base | two | 1.0 (-2.8 to 4.8), P 0.628; dHR P 0.995 | -1.7 (-6.6 to 3.3), P 0.507; dHR P 0.531 |
| PS-CVD5 | shufCLMBR vs base | two | 2.4 (-2.1 to 6.8), P 0.325; dHR P 0.967 | 0.2 (-5.2 to 5.6), P 0.938; dHR P 0.449 |
| PS-CVD5 | ECG vs shufECG | one | 8.0 (3.6 to 12.2), P <.001; dHR P 0.062 | 8.1 (3.2 to 12.9), P 0.001; dHR P 0.441 |
| PS-CVD5 | CLMBR vs shufCLMBR | one | 10.2 (4.1 to 15.6), P 0.001; dHR P 0.030 | 11.2 (4.7 to 17.7), P 0.002; dHR P 0.137 |
| PS-CVD5 | CLMBR vs ECG | two | 3.9 (-1.8 to 8.9), P 0.198; dHR P 0.286 | 5.1 (-0.4 to 10.2), P 0.077; dHR P 0.256 |
| PS-CVD5 | ECG+CLMBR vs CLMBR | one | 1.3 (-4.2 to 6.6), P 0.312; dHR P 0.296 | -0.4 (-6.0 to 5.0), P 0.551; dHR P 0.390 |
| PS-CVD5 | ECG+CLMBR vs ECG | one | 5.2 (-1.5 to 11.6), P 0.073; dHR P 0.099 | 4.9 (0.1 to 10.0), P 0.031; dHR P 0.107 |
| PS-Demo | shufECG vs base | two | -0.6 (-5.4 to 4.4), P 0.829; dHR P 0.054 | -0.4 (-4.6 to 3.8), P 0.855; dHR P 0.423 |
| PS-Demo | shufCLMBR vs base | two | -1.5 (-5.1 to 2.1), P 0.414; dHR P 0.646 | -2.4 (-7.5 to 2.4), P 0.358; dHR P 0.827 |
| PS-Demo | ECG vs shufECG | one | 11.9 (6.8 to 16.7), P <.001; dHR P 0.002 | 12.0 (7.2 to 16.6), P <.001; dHR P 0.101 |
| PS-Demo | CLMBR vs shufCLMBR | one | 22.1 (15.5 to 28.8), P <.001; dHR P 0.023 | 19.7 (11.5 to 27.5), P <.001; dHR P 0.018 |
| PS-Demo | CLMBR vs ECG | two | 10.5 (3.8 to 17.0), P 0.005; dHR P 0.256 | 8.2 (2.3 to 14.1), P 0.014; dHR P 0.566 |
| PS-Demo | ECG+CLMBR vs CLMBR | one | 6.4 (2.4 to 10.2), P 0.003; dHR P 0.442 | 1.8 (-3.7 to 6.5), P 0.262; dHR P 0.028 |
| PS-Demo | ECG+CLMBR vs ECG | one | 16.3 (11.0 to 21.6), P <.001; dHR P 0.136 | 9.4 (3.5 to 15.4), P 0.003; dHR P 0.012 |
| hdPS | shufECG vs base | two | 3.0 (-1.4 to 7.3), P 0.197; dHR P 0.684 | 2.4 (-3.1 to 7.3), P 0.413; dHR P 0.314 |
| hdPS | shufCLMBR vs base | two | 2.0 (-2.3 to 6.2), P 0.374; dHR P 0.978 | -2.8 (-7.6 to 1.8), P 0.284; dHR P 0.017 |
| hdPS | ECG vs shufECG | one | 4.8 (-2.4 to 12.0), P 0.120; dHR P 0.317 | -2.3 (-7.7 to 2.5), P 0.798; dHR P 0.196 |
| hdPS | CLMBR vs shufCLMBR | one | -5.6 (-16.4 to 3.1), P 0.807; dHR P 0.449 | 4.4 (-2.9 to 11.8), P 0.143; dHR P 0.192 |
| hdPS | CLMBR vs ECG | two | -12.1 (-23.7 to -3.2), P 0.005; dHR P 0.622 | 3.3 (-3.3 to 9.5), P 0.358; dHR P 0.905 |
| hdPS | ECG+CLMBR vs CLMBR | one | 7.9 (2.5 to 13.6), P 0.005; dHR P 0.228 | -0.5 (-6.5 to 5.3), P 0.571; dHR P 0.004 |
| hdPS | ECG+CLMBR vs ECG | one | 1.7 (-4.7 to 8.1), P 0.317; dHR P 0.436 | 2.7 (-3.8 to 9.4), P 0.224; dHR P 0.080 |
| PS-Clinical (no LVEF) | shufECG vs base | two | -4.6 (-11.1 to 1.2), P 0.153; dHR P 0.183 | -5.5 (-13.2 to 1.7), P 0.171; dHR P 0.698 |
| PS-Clinical (no LVEF) | shufCLMBR vs base | two | -1.6 (-6.1 to 2.8), P 0.477; dHR P 0.526 | -5.0 (-11.0 to 0.2), P 0.090; dHR P 0.077 |
| PS-Clinical (no LVEF) | ECG vs shufECG | one | 8.7 (3.2 to 14.0), P 0.003; dHR P 0.116 | 2.1 (-3.0 to 7.3), P 0.221; dHR P 0.561 |
| PS-Clinical (no LVEF) | CLMBR vs shufCLMBR | one | 2.9 (-4.0 to 9.1), P 0.202; dHR P 0.269 | 4.5 (-1.9 to 10.5), P 0.086; dHR P 0.037 |
| PS-Clinical (no LVEF) | CLMBR vs ECG | two | -3.1 (-10.4 to 3.9), P 0.412; dHR P 0.643 | 3.1 (-3.4 to 9.6), P 0.393; dHR P 0.170 |
| PS-Clinical (no LVEF) | ECG+CLMBR vs CLMBR | one | 1.9 (-2.7 to 6.4), P 0.219; dHR P 0.449 | -1.8 (-8.7 to 4.8), P 0.697; dHR P 0.575 |
| PS-Clinical (no LVEF) | ECG+CLMBR vs ECG | one | -0.6 (-6.6 to 4.8), P 0.584; dHR P 0.325 | 1.4 (-6.6 to 8.4), P 0.364; dHR P 0.164 |

### Per domain, PS-CVD5, S32, main

| Domain | + ECG v1 | + ECG v2 | + CLMBR-T v1 | + CLMBR-T v2 | + both v1 | + both v2 |
|---|---|---|---|---|---|---|
| Vitals & core labs | 8.7 (P 0.002) | 7.6 (P 0.015) | 22.7 (P <.001) | 22.2 (P <.001) | 32.1 (P <.001) | 21.8 (P <.001) |
| Other labs | 6.9 (P 0.056) | 7.0 (P 0.133) | 24.1 (P <.001) | 29.8 (P <.001) | 21.7 (P <.001) | 18.9 (P <.001) |
| Echo: LV structure | 14.9 (P 0.010) | 14.1 (P 0.013) | 14.7 (P 0.022) | 16.3 (P 0.009) | 21.7 (P 0.001) | 13.4 (P 0.026) |
| Echo: LV function | 16.4 (P 0.017) | 8.1 (P 0.189) | 1.0 (P 0.453) | -3.4 (P 0.635) | 7.6 (P 0.226) | 8.0 (P 0.187) |
| Echo: diastolic / LA | 16.1 (P 0.003) | 4.9 (P 0.238) | 0.7 (P 0.459) | 5.9 (P 0.210) | 10.4 (P 0.095) | 9.5 (P 0.083) |
| Echo: RV / pulmonary | -1.8 (P 0.624) | 6.4 (P 0.087) | 0.2 (P 0.490) | 4.4 (P 0.260) | -1.3 (P 0.581) | 2.9 (P 0.311) |
| Echo: valves / aorta | 4.2 (P 0.152) | 1.3 (P 0.373) | 15.9 (P 0.005) | 3.7 (P 0.225) | 3.1 (P 0.341) | 6.6 (P 0.175) |
| Echo, all 35 items | 9.2 (P 0.003) | 6.4 (P 0.014) | 7.6 (P 0.018) | 5.4 (P 0.112) | 7.5 (P 0.069) | 7.9 (P 0.035) |

### Ladder, S29, main configuration (relative reduction 54 items, %)

| PS level | base mean SMD54 v1 | base mean SMD54 v2 | + ECG v1 | + ECG v2 | + CLMBR-T v1 | + CLMBR-T v2 | + both v1 | + both v2 |
|---|---|---|---|---|---|---|---|---|
| PS-Demo | 0.129 | 0.128 | 11.3 (P <.001) | 9.5 (P <.001) | 20.4 (P <.001) | 15.5 (P <.001) | 25.9 (P <.001) | 18.4 (P <.001) |
| PS-CVD5 | 0.116 | 0.120 | 9.4 (P <.001) | 6.5 (P 0.004) | 11.2 (P <.001) | 10.6 (P <.001) | 12.6 (P 0.002) | 12.7 (P <.001) |
| hdPS | 0.105 | 0.112 | 7.4 (P 0.003) | -0.9 (P 0.643) | -3.8 (P 0.670) | 2.4 (P 0.227) | 7.7 (P 0.033) | 2.7 (P 0.215) |
| PS-Clinical (no LVEF) | 0.106 | 0.113 | 3.6 (P 0.191) | 1.7 (P 0.330) | 2.6 (P 0.302) | 4.5 (P 0.104) | 7.2 (P 0.058) | 2.9 (P 0.216) |
| CVD10 (supplement) | 0.109 | 0.113 | 5.7 (P 0.052) | 4.7 (P 0.074) | 7.9 (P 0.003) | 5.0 (P 0.022) | 10.0 (P 0.001) | 10.8 (P <.001) |
| PS-Flags (supplement) | 0.099 | 0.128 | -1.6 (P 0.773) | -2.0 (P 0.658) | -4.2 (P 0.916) | -13.0 (P 0.945) | -6.9 (P 0.854) | -4.8 (P 0.670) |
| PS-Clinical (with LVEF, v1) (v1 reference) | 0.101 | 0.107 | -2.4 (P 0.753) | -6.0 (P 0.903) | 2.9 (P 0.139) | -4.3 (P 0.928) | -0.7 (P 0.566) | -0.5 (P 0.542) |

### Base-to-base and head-to-heads, S29, main

| Contrast (two-sided) | v1 | v2 |
|---|---|---|
| P1 base vs P5 base | -11.9 (-19.1 to -5.0), P 0.002; dHR 0.202->0.228 P 0.242 | -6.6 (-11.3 to -2.0), P 0.012; dHR 0.176->0.237 P 0.007 |
| hdPS200 base vs P5 base | 8.6 (0.6 to 15.9), P 0.044; dHR 0.202->0.187 P 0.607 | 6.7 (-3.2 to 16.0), P 0.201; dHR 0.176->0.177 P 0.976 |
| clinical_nolvef base vs P5 base | 7.2 (0.4 to 13.4), P 0.043; dHR 0.202->0.147 P 0.042 | 7.4 (3.5 to 11.7), P <.001; dHR 0.176->0.156 P 0.476 |
| PS10 base vs P5 base | 6.0 (1.0 to 11.2), P 0.027; dHR 0.202->0.179 P 0.302 | 5.5 (1.3 to 10.0), P 0.019; dHR 0.176->0.194 P 0.419 |
| Flags base vs P5 base | 12.8 (6.1 to 19.0), P 0.001; dHR 0.202->0.185 P 0.294 | -7.6 (-27.6 to 8.6), P 0.530; dHR 0.176->0.232 P 0.429 |
| P1+CLMBR vs Flags base | -0.9 (-7.5 to 5.4), P 0.787; dHR 0.185->0.161 P 0.203 | 17.9 (4.2 to 30.4), P 0.030; dHR 0.232->0.168 P 0.117 |
| P5+CLMBR vs hdPS200 base | 2.4 (-5.2 to 9.0), P 0.549; dHR 0.187->0.160 P 0.048 | 4.3 (-4.2 to 11.8), P 0.341; dHR 0.177->0.161 P 0.237 |
| P5+ECG+CLMBR vs hdPS200 base | 4.4 (-3.2 to 10.8), P 0.242; dHR 0.187->0.148 P 0.014 | 6.1 (-1.9 to 13.2), P 0.150; dHR 0.177->0.163 P 0.342 |
| P5+CLMBR vs clinical_nolvef base | 1.1 (-5.5 to 7.0), P 0.732; dHR 0.147->0.160 P 0.408 | 1.0 (-5.4 to 7.4), P 0.764; dHR 0.156->0.161 P 0.792 |
| P5+ECG+CLMBR vs clinical_nolvef base | 1.0 (-10.0 to 10.7), P 0.852; dHR 0.147->0.148 P 0.927 | 3.8 (-3.5 to 11.2), P 0.335; dHR 0.156->0.163 P 0.766 |
| P5+ECG vs clinical_nolvef base | 2.2 (-4.6 to 7.8), P 0.517; dHR 0.147->0.179 P 0.090 | -0.3 (-6.2 to 5.3), P 0.912; dHR 0.156->0.188 P 0.167 |

### Placebos and head-to-heads within rung, S29, main

| PS level | Contrast | sided | v1 | v2 |
|---|---|---|---|---|
| PS-CVD5 | shufECG vs base | two | 0.1 (-4.2 to 4.3), P 0.959; dHR P 0.965 | 0.1 (-4.7 to 5.3), P 0.960; dHR P 0.372 |
| PS-CVD5 | shufCLMBR vs base | two | 0.7 (-4.1 to 5.6), P 0.784; dHR P 0.777 | -0.9 (-5.6 to 3.8), P 0.729; dHR P 0.384 |
| PS-CVD5 | ECG vs shufECG | one | 9.3 (5.2 to 13.5), P <.001; dHR P 0.058 | 6.3 (0.9 to 11.7), P 0.016; dHR P 0.378 |
| PS-CVD5 | CLMBR vs shufCLMBR | one | 10.6 (4.3 to 16.1), P <.001; dHR P 0.036 | 11.3 (5.2 to 17.9), P <.001; dHR P 0.077 |
| PS-CVD5 | CLMBR vs ECG | two | 2.0 (-3.9 to 7.3), P 0.502; dHR P 0.405 | 4.3 (-0.7 to 9.2), P 0.113; dHR P 0.191 |
| PS-CVD5 | ECG+CLMBR vs CLMBR | one | 1.5 (-4.3 to 7.3), P 0.308; dHR P 0.198 | 1.6 (-3.0 to 6.4), P 0.259; dHR P 0.550 |
| PS-CVD5 | ECG+CLMBR vs ECG | one | 3.5 (-3.5 to 10.9), P 0.178; dHR P 0.049 | 6.0 (0.7 to 11.6), P 0.024; dHR P 0.095 |
| PS-Demo | shufECG vs base | two | -1.2 (-6.4 to 4.5), P 0.694; dHR P 0.265 | -1.8 (-6.9 to 3.0), P 0.480; dHR P 0.672 |
| PS-Demo | shufCLMBR vs base | two | -0.8 (-4.7 to 2.9), P 0.706; dHR P 0.724 | -4.1 (-10.0 to 1.5), P 0.179; dHR P 0.692 |
| PS-Demo | ECG vs shufECG | one | 12.5 (6.5 to 17.9), P <.001; dHR P 0.005 | 11.1 (6.2 to 16.2), P <.001; dHR P 0.004 |
| PS-Demo | CLMBR vs shufCLMBR | one | 21.3 (15.1 to 26.5), P <.001; dHR P 0.018 | 18.0 (11.0 to 23.9), P <.001; dHR P 0.009 |
| PS-Demo | CLMBR vs ECG | two | 10.2 (4.6 to 15.4), P 0.001; dHR P 0.477 | 6.7 (2.3 to 10.8), P 0.008; dHR P 0.741 |
| PS-Demo | ECG+CLMBR vs CLMBR | one | 6.9 (2.7 to 10.5), P 0.001; dHR P 0.586 | 3.9 (-0.6 to 7.9), P 0.043; dHR P 0.146 |
| PS-Demo | ECG+CLMBR vs ECG | one | 16.3 (11.2 to 21.0), P <.001; dHR P 0.296 | 9.9 (4.8 to 14.9), P <.001; dHR P 0.129 |
| hdPS | shufECG vs base | two | 3.9 (-0.9 to 8.7), P 0.129; dHR P 0.205 | 1.5 (-4.7 to 7.7), P 0.678; dHR P 0.116 |
| hdPS | shufCLMBR vs base | two | 2.2 (-2.3 to 6.7), P 0.367; dHR P 0.453 | -1.8 (-6.8 to 3.2), P 0.574; dHR P 0.055 |
| hdPS | ECG vs shufECG | one | 3.6 (-3.3 to 9.9), P 0.175; dHR P 0.237 | -1.9 (-7.0 to 2.8), P 0.759; dHR P 0.038 |
| hdPS | CLMBR vs shufCLMBR | one | -6.1 (-19.0 to 3.8), P 0.758; dHR P 0.455 | 0.7 (-5.4 to 6.6), P 0.411; dHR P 0.440 |
| hdPS | CLMBR vs ECG | two | -12.1 (-25.8 to -1.0), P 0.037; dHR P 0.549 | 1.7 (-4.0 to 7.2), P 0.599; dHR P 0.084 |
| hdPS | ECG+CLMBR vs CLMBR | one | 6.5 (1.6 to 11.3), P 0.007; dHR P 0.154 | 0.3 (-5.4 to 6.0), P 0.463; dHR P 0.007 |
| hdPS | ECG+CLMBR vs ECG | one | 1.3 (-4.9 to 6.9), P 0.339; dHR P 0.394 | 2.0 (-3.0 to 6.7), P 0.231; dHR P 0.212 |
| PS-Clinical (no LVEF) | shufECG vs base | two | -3.2 (-8.4 to 1.5), P 0.219; dHR P 0.141 | -1.5 (-8.6 to 4.9), P 0.688; dHR P 0.318 |
| PS-Clinical (no LVEF) | shufCLMBR vs base | two | -0.9 (-5.7 to 3.5), P 0.704; dHR P 0.912 | -2.5 (-7.7 to 2.6), P 0.356; dHR P 0.733 |
| PS-Clinical (no LVEF) | ECG vs shufECG | one | 6.6 (0.9 to 12.3), P 0.019; dHR P 0.050 | 3.1 (-2.4 to 8.9), P 0.146; dHR P 0.109 |
| PS-Clinical (no LVEF) | CLMBR vs shufCLMBR | one | 3.2 (-4.0 to 10.1), P 0.201; dHR P 0.461 | 6.8 (0.6 to 12.6), P 0.026; dHR P 0.124 |
| PS-Clinical (no LVEF) | CLMBR vs ECG | two | -1.0 (-8.3 to 5.8), P 0.785; dHR P 0.876 | 3.0 (-3.1 to 9.1), P 0.389; dHR P 0.362 |
| PS-Clinical (no LVEF) | ECG+CLMBR vs CLMBR | one | 4.0 (-1.3 to 8.7), P 0.073; dHR P 0.495 | -2.0 (-9.4 to 4.8), P 0.689; dHR P 0.853 |
| PS-Clinical (no LVEF) | ECG+CLMBR vs ECG | one | 3.5 (-1.4 to 8.5), P 0.102; dHR P 0.441 | 1.0 (-7.0 to 8.1), P 0.404; dHR P 0.501 |

### Per domain, PS-CVD5, S29, main

| Domain | + ECG v1 | + ECG v2 | + CLMBR-T v1 | + CLMBR-T v2 | + both v1 | + both v2 |
|---|---|---|---|---|---|---|
| Vitals & core labs | 10.2 (P 0.002) | 6.1 (P 0.052) | 19.4 (P <.001) | 19.9 (P <.001) | 28.6 (P <.001) | 19.6 (P 0.001) |
| Other labs | 1.8 (P 0.287) | 12.9 (P <.001) | 18.4 (P 0.003) | 25.5 (P 0.001) | 23.3 (P <.001) | 21.8 (P <.001) |
| Echo: LV structure | 22.2 (P <.001) | 14.7 (P 0.020) | 17.2 (P 0.015) | 17.8 (P 0.003) | 23.1 (P 0.002) | 17.6 (P 0.009) |
| Echo: LV function | 18.7 (P 0.011) | 7.1 (P 0.233) | 7.7 (P 0.185) | -3.6 (P 0.632) | 5.8 (P 0.266) | 16.0 (P 0.029) |
| Echo: diastolic / LA | 14.6 (P 0.013) | 1.2 (P 0.435) | 2.8 (P 0.352) | 7.0 (P 0.152) | 12.8 (P 0.082) | 11.9 (P 0.062) |
| Echo: RV / pulmonary | -3.6 (P 0.746) | 3.0 (P 0.279) | -4.9 (P 0.749) | 5.4 (P 0.226) | -4.3 (P 0.722) | 0.4 (P 0.476) |
| Echo: valves / aorta | 4.0 (P 0.163) | 2.5 (P 0.288) | 13.3 (P 0.023) | 3.4 (P 0.250) | -0.0 (P 0.500) | 4.9 (P 0.260) |
| Echo, all 35 items | 10.6 (P 0.002) | 5.4 (P 0.035) | 8.0 (P 0.012) | 5.8 (P 0.073) | 6.9 (P 0.120) | 9.5 (P 0.015) |

### Ladder, S38, main configuration (relative reduction 54 items, %)

| PS level | base mean SMD54 v1 | base mean SMD54 v2 | + ECG v1 | + ECG v2 | + CLMBR-T v1 | + CLMBR-T v2 | + both v1 | + both v2 |
|---|---|---|---|---|---|---|---|---|
| PS-Demo | 0.139 | 0.139 | 12.6 (P <.001) | 12.5 (P <.001) | 21.8 (P <.001) | 19.5 (P <.001) | 27.2 (P <.001) | 21.5 (P <.001) |
| PS-CVD5 | 0.124 | 0.127 | 9.0 (P <.001) | 6.7 (P 0.002) | 12.7 (P <.001) | 11.8 (P <.001) | 14.5 (P <.001) | 12.3 (P <.001) |
| hdPS | 0.112 | 0.118 | 7.6 (P 0.004) | -0.2 (P 0.534) | -2.5 (P 0.668) | 3.6 (P 0.111) | 8.4 (P 0.004) | 3.4 (P 0.114) |
| PS-Clinical (no LVEF) | 0.111 | 0.115 | 5.3 (P 0.057) | -2.3 (P 0.704) | 2.2 (P 0.283) | 0.3 (P 0.471) | 5.6 (P 0.072) | -0.2 (P 0.519) |
| CVD10 (supplement) | 0.115 | 0.118 | 4.8 (P 0.042) | 4.1 (P 0.077) | 7.4 (P 0.004) | 5.3 (P 0.018) | 8.2 (P 0.004) | 9.3 (P <.001) |
| PS-Flags (supplement) | 0.107 | 0.130 | -1.8 (P 0.786) | -1.0 (P 0.606) | -2.5 (P 0.809) | -11.0 (P 0.966) | -4.1 (P 0.771) | -4.8 (P 0.738) |
| PS-Clinical (with LVEF, v1) (v1 reference) | 0.105 | 0.112 | -0.9 (P 0.625) | -3.8 (P 0.855) | 2.7 (P 0.119) | -1.5 (P 0.684) | 0.9 (P 0.401) | 1.7 (P 0.349) |

### Base-to-base and head-to-heads, S38, main

| Contrast (two-sided) | v1 | v2 |
|---|---|---|
| P1 base vs P5 base | -12.9 (-20.3 to -6.2), P <.001; dHR 0.224->0.258 P 0.175 | -9.8 (-16.1 to -3.8), P 0.003; dHR 0.212->0.281 P 0.005 |
| hdPS200 base vs P5 base | 9.2 (2.6 to 15.3), P 0.008; dHR 0.224->0.181 P 0.210 | 7.4 (-1.7 to 15.1), P 0.089; dHR 0.212->0.205 P 0.875 |
| clinical_nolvef base vs P5 base | 8.4 (2.8 to 13.6), P 0.006; dHR 0.224->0.150 P 0.005 | 10.2 (4.8 to 16.1), P <.001; dHR 0.212->0.168 P 0.128 |
| PS10 base vs P5 base | 7.1 (3.1 to 11.0), P 0.001; dHR 0.224->0.202 P 0.259 | 6.8 (2.0 to 11.1), P 0.007; dHR 0.212->0.238 P 0.207 |
| Flags base vs P5 base | 12.4 (6.8 to 17.7), P <.001; dHR 0.224->0.183 P 0.091 | -3.1 (-19.1 to 8.6), P 0.743; dHR 0.212->0.248 P 0.542 |
| P1+CLMBR vs Flags base | 0.2 (-5.4 to 5.5), P 0.956; dHR 0.183->0.168 P 0.485 | 15.7 (5.0 to 26.1), P 0.011; dHR 0.248->0.198 P 0.138 |
| P5+CLMBR vs hdPS200 base | 3.5 (-2.1 to 8.8), P 0.238; dHR 0.181->0.162 P 0.182 | 4.8 (-1.8 to 10.9), P 0.187; dHR 0.205->0.190 P 0.606 |
| P5+ECG+CLMBR vs hdPS200 base | 5.8 (-0.3 to 11.5), P 0.067; dHR 0.181->0.154 P 0.126 | 5.1 (-0.6 to 10.6), P 0.105; dHR 0.205->0.189 P 0.532 |
| P5+CLMBR vs clinical_nolvef base | 1.0 (-4.7 to 6.3), P 0.732; dHR 0.150->0.162 P 0.373 | -0.9 (-8.6 to 6.1), P 0.831; dHR 0.168->0.190 P 0.244 |
| P5+ECG+CLMBR vs clinical_nolvef base | 1.4 (-6.8 to 8.7), P 0.739; dHR 0.150->0.154 P 0.784 | -0.5 (-7.8 to 6.6), P 0.901; dHR 0.168->0.189 P 0.271 |
| P5+ECG vs clinical_nolvef base | 0.7 (-5.5 to 6.4), P 0.824; dHR 0.150->0.195 P 0.024 | -3.4 (-9.6 to 2.1), P 0.270; dHR 0.168->0.219 P 0.026 |

### Placebos and head-to-heads within rung, S38, main

| PS level | Contrast | sided | v1 | v2 |
|---|---|---|---|---|
| PS-CVD5 | shufECG vs base | two | 0.5 (-3.1 to 4.0), P 0.804; dHR P 0.995 | -1.0 (-5.5 to 3.4), P 0.677; dHR P 0.433 |
| PS-CVD5 | shufCLMBR vs base | two | 2.3 (-1.8 to 6.3), P 0.286; dHR P 0.914 | 0.0 (-4.9 to 5.0), P 0.987; dHR P 0.476 |
| PS-CVD5 | ECG vs shufECG | one | 8.6 (4.9 to 12.7), P <.001; dHR P 0.045 | 7.5 (3.1 to 11.7), P <.001; dHR P 0.351 |
| PS-CVD5 | CLMBR vs shufCLMBR | one | 10.6 (5.1 to 15.7), P <.001; dHR P 0.014 | 11.7 (5.7 to 17.9), P <.001; dHR P 0.081 |
| PS-CVD5 | CLMBR vs ECG | two | 4.1 (-1.4 to 8.7), P 0.132; dHR P 0.168 | 5.4 (0.4 to 10.1), P 0.043; dHR P 0.150 |
| PS-CVD5 | ECG+CLMBR vs CLMBR | one | 2.0 (-2.8 to 6.7), P 0.215; dHR P 0.266 | 0.1 (-5.0 to 4.9), P 0.488; dHR P 0.487 |
| PS-CVD5 | ECG+CLMBR vs ECG | one | 6.0 (-0.3 to 11.8), P 0.031; dHR P 0.050 | 5.6 (1.2 to 10.1), P 0.009; dHR P 0.080 |
| PS-Demo | shufECG vs base | two | 0.3 (-4.0 to 5.0), P 0.902; dHR P 0.039 | -0.3 (-4.3 to 3.6), P 0.883; dHR P 0.420 |
| PS-Demo | shufCLMBR vs base | two | -0.2 (-3.6 to 3.1), P 0.887; dHR P 0.876 | -2.8 (-7.6 to 1.7), P 0.249; dHR P 0.709 |
| PS-Demo | ECG vs shufECG | one | 12.4 (7.8 to 16.8), P <.001; dHR P <.001 | 12.7 (7.9 to 17.3), P <.001; dHR P 0.060 |
| PS-Demo | CLMBR vs shufCLMBR | one | 22.3 (16.4 to 28.3), P <.001; dHR P 0.004 | 20.8 (13.0 to 28.2), P <.001; dHR P 0.006 |
| PS-Demo | CLMBR vs ECG | two | 10.5 (4.4 to 16.5), P 0.002; dHR P 0.146 | 8.2 (2.9 to 13.6), P 0.005; dHR P 0.361 |
| PS-Demo | ECG+CLMBR vs CLMBR | one | 6.8 (3.3 to 10.4), P <.001; dHR P 0.457 | 2.7 (-2.2 to 7.2), P 0.146; dHR P 0.014 |
| PS-Demo | ECG+CLMBR vs ECG | one | 16.6 (12.1 to 21.6), P <.001; dHR P 0.087 | 10.3 (5.0 to 15.7), P <.001; dHR P 0.003 |
| hdPS | shufECG vs base | two | 2.7 (-1.3 to 6.8), P 0.194; dHR P 0.520 | 1.7 (-3.5 to 6.3), P 0.541; dHR P 0.322 |
| hdPS | shufCLMBR vs base | two | 2.2 (-1.6 to 6.0), P 0.282; dHR P 0.906 | -3.7 (-8.0 to 0.6), P 0.124; dHR P 0.033 |
| hdPS | ECG vs shufECG | one | 5.0 (-1.7 to 11.4), P 0.088; dHR P 0.321 | -1.4 (-6.3 to 3.1), P 0.715; dHR P 0.179 |
| hdPS | CLMBR vs shufCLMBR | one | -4.7 (-15.0 to 3.2), P 0.782; dHR P 0.449 | 4.9 (-1.8 to 11.5), P 0.091; dHR P 0.180 |
| hdPS | CLMBR vs ECG | two | -11.0 (-21.9 to -2.9), P 0.005; dHR P 0.572 | 2.6 (-3.5 to 8.1), P 0.428; dHR P 0.995 |
| hdPS | ECG+CLMBR vs CLMBR | one | 7.2 (2.1 to 12.0), P 0.004; dHR P 0.125 | -0.1 (-5.4 to 4.7), P 0.516; dHR P 0.005 |
| hdPS | ECG+CLMBR vs ECG | one | 1.5 (-4.7 to 7.2), P 0.327; dHR P 0.346 | 2.5 (-3.2 to 8.1), P 0.228; dHR P 0.061 |
| PS-Clinical (no LVEF) | shufECG vs base | two | -3.5 (-9.3 to 1.7), P 0.233; dHR P 0.088 | -5.7 (-12.4 to 1.0), P 0.113; dHR P 0.680 |
| PS-Clinical (no LVEF) | shufCLMBR vs base | two | -0.9 (-5.1 to 2.9), P 0.646; dHR P 0.495 | -4.6 (-9.9 to 0.3), P 0.087; dHR P 0.067 |
| PS-Clinical (no LVEF) | ECG vs shufECG | one | 8.5 (3.3 to 13.2), P 0.002; dHR P 0.029 | 3.2 (-1.8 to 8.2), P 0.106; dHR P 0.539 |
| PS-Clinical (no LVEF) | CLMBR vs shufCLMBR | one | 2.9 (-3.1 to 8.5), P 0.174; dHR P 0.242 | 4.6 (-1.1 to 9.9), P 0.064; dHR P 0.036 |
| PS-Clinical (no LVEF) | CLMBR vs ECG | two | -3.4 (-9.7 to 3.0), P 0.322; dHR P 0.764 | 2.6 (-3.6 to 8.4), P 0.429; dHR P 0.223 |
| PS-Clinical (no LVEF) | ECG+CLMBR vs CLMBR | one | 2.9 (-1.4 to 7.2), P 0.107; dHR P 0.376 | -0.7 (-6.9 to 4.9), P 0.590; dHR P 0.469 |
| PS-Clinical (no LVEF) | ECG+CLMBR vs ECG | one | 0.1 (-5.1 to 5.2), P 0.490; dHR P 0.328 | 2.0 (-5.2 to 8.0), P 0.294; dHR P 0.150 |

### Per domain, PS-CVD5, S38, main

| Domain | + ECG v1 | + ECG v2 | + CLMBR-T v1 | + CLMBR-T v2 | + both v1 | + both v2 |
|---|---|---|---|---|---|---|
| Vitals & core labs | 9.4 (P <.001) | 7.8 (P 0.005) | 22.9 (P <.001) | 21.3 (P <.001) | 32.5 (P <.001) | 22.3 (P <.001) |
| Other labs | 6.2 (P 0.064) | 6.3 (P 0.140) | 23.5 (P <.001) | 27.9 (P <.001) | 21.5 (P <.001) | 17.5 (P <.001) |
| Echo: LV structure | 14.4 (P 0.006) | 13.2 (P 0.010) | 13.7 (P 0.019) | 16.6 (P 0.004) | 21.8 (P <.001) | 13.9 (P 0.013) |
| Echo: LV function | 14.9 (P 0.014) | 9.6 (P 0.121) | 4.2 (P 0.294) | -0.4 (P 0.516) | 11.0 (P 0.111) | 10.0 (P 0.108) |
| Echo: diastolic / LA | 17.2 (P <.001) | 6.5 (P 0.149) | 1.9 (P 0.374) | 7.5 (P 0.139) | 11.3 (P 0.058) | 10.1 (P 0.054) |
| Echo: RV / pulmonary | -0.9 (P 0.565) | 6.3 (P 0.068) | 0.1 (P 0.489) | 4.2 (P 0.245) | 0.5 (P 0.468) | 3.7 (P 0.246) |
| Echo: valves / aorta | 4.8 (P 0.105) | 0.7 (P 0.428) | 15.9 (P 0.002) | 4.7 (P 0.150) | 3.2 (P 0.320) | 8.1 (P 0.106) |
| Echo, all 35 items | 9.5 (P <.001) | 6.6 (P 0.006) | 8.1 (P 0.006) | 6.4 (P 0.053) | 8.6 (P 0.030) | 9.0 (P 0.011) |

### Per trial, PS-CVD5, main configuration (trial-level aggregates)

| Trial | m54 base v1 | m54 +ECG v1 | m54 +CLMBR-T v1 | absd base v1 | m54 base v2 | m54 +ECG v2 | m54 +CLMBR-T v2 | absd base v2 |
|---|---|---|---|---|---|---|---|---|
| COMET | 0.147 | 0.116 | 0.108 | 0.000 | 0.140 | 0.119 | 0.106 | 0.108 |
| PARADIGM-HF | 0.107 | 0.075 | 0.095 | 0.229 | 0.111 | 0.085 | 0.108 | 0.255 |
| TRANSFORM-HF | 0.156 | 0.133 | 0.115 | 0.058 | 0.156 | 0.133 | 0.115 | 0.058 |
| ELITE II | 0.096 | 0.083 | 0.079 | 0.244 | 0.086 | 0.086 | 0.070 | 0.210 |
| LIFE | 0.127 | 0.115 | 0.114 | 0.023 | 0.141 | 0.148 | 0.148 | 0.108 |
| PLATO | 0.060 | 0.058 | 0.055 | 0.054 | 0.060 | 0.058 | 0.055 | 0.054 |
| ARISTOTLE | 0.132 | 0.114 | 0.105 | 0.369 | 0.139 | 0.137 | 0.127 | 0.172 |
| ROCKET-AF | 0.148 | 0.134 | 0.132 | 0.416 | 0.134 | 0.140 | 0.116 | 0.327 |
| RE-LY | 0.179 | 0.192 | 0.171 | 0.349 | 0.191 | 0.214 | 0.194 | 0.197 |
| ALLHAT | 0.054 | 0.050 | 0.049 | 0.245 | 0.051 | 0.041 | 0.048 | 0.222 |
| EMPEROR-Preserved | 0.103 | 0.107 | 0.103 | 0.058 | 0.130 | 0.097 | 0.109 | 0.258 |
| EAST-AFNET 4 | 0.087 | 0.061 | 0.054 | 0.158 | 0.087 | 0.061 | 0.054 | 0.158 |
| CABANA | 0.142 | 0.123 | 0.083 | 0.975 | 0.142 | 0.123 | 0.083 | 0.975 |
| ONTARGET | 0.073 | 0.063 | 0.056 | 0.185 | 0.076 | 0.070 | 0.054 | 0.229 |
| VALUE | 0.079 | 0.069 | 0.062 | 0.307 | 0.078 | 0.071 | 0.068 | 0.313 |
| ASCOT-BPLA | 0.087 | 0.089 | 0.077 | 0.135 | 0.080 | 0.076 | 0.080 | 0.193 |
| EMPA-REG OUTCOME | 0.121 | 0.119 | 0.133 | 0.204 | 0.138 | 0.123 | 0.123 | 0.210 |
| CAROLINA | 0.141 | 0.117 | 0.135 | 0.104 | 0.161 | 0.164 | 0.127 | 0.045 |
| LEADER | 0.162 | 0.177 | 0.160 | 0.568 | 0.215 | 0.176 | 0.190 | 0.263 |
| SUSTAIN-6 | 0.153 | 0.153 | 0.122 | 0.318 | 0.159 | 0.155 | 0.128 | 0.406 |
| REWIND | 0.112 | 0.082 | 0.092 | 0.186 | 0.103 | 0.105 | 0.079 | 0.164 |
| DECLARE-TIMI 58 | 0.135 | 0.129 | 0.122 | 0.208 | 0.137 | 0.124 | 0.120 | 0.124 |
| CANVAS Program | 0.263 | 0.246 | 0.213 | 0.173 | 0.219 | 0.225 | 0.181 | 0.004 |
| TECOS | 0.084 | 0.089 | 0.078 | 0.111 | 0.100 | 0.095 | 0.093 | 0.124 |
| CARMELINA | 0.112 | 0.117 | 0.107 | 0.024 | 0.130 | 0.144 | 0.145 | 0.006 |
| VALIANT | 0.110 | 0.110 | 0.129 | 0.220 | 0.138 | 0.154 | 0.151 | 0.076 |
| INSIGHT | 0.171 | 0.181 | 0.148 | 0.643 | 0.205 | 0.199 | 0.178 | 0.566 |
| AFFIRM | 0.082 | 0.068 | 0.066 | 0.066 | 0.082 | 0.068 | 0.066 | 0.066 |
| AF-CHF | 0.130 | 0.073 | 0.076 | 0.302 | 0.110 | 0.067 | 0.081 | 0.172 |
| PRECISION | 0.064 | 0.078 | 0.067 | 0.203 | 0.083 | 0.061 | 0.062 | 0.126 |
| AMPLIFY | 0.124 | 0.095 | 0.125 | 0.090 | 0.090 | 0.121 | 0.154 | 0.702 |
| LODESTAR | 0.052 | 0.055 | 0.052 | 0.154 | 0.056 | 0.043 | 0.045 | 0.120 |
| PROVE IT-TIMI 22 | 0.184 | 0.149 | 0.196 | 0.446 | 0.181 | 0.156 | 0.165 | 0.243 |
| FRAIL-AF | 0.107 | 0.105 | 0.115 | 0.338 | 0.107 | 0.105 | 0.115 | 0.338 |
| LAAOS III | 0.131 | 0.109 | 0.086 | 0.053 | 0.119 | 0.098 | 0.059 | 0.145 |
| PROTECT AF | 0.172 | 0.149 | 0.172 | 0.031 | 0.175 | 0.180 | 0.210 | 0.108 |
| RAFT-AF | 0.164 | 0.170 | 0.148 | 0.194 | 0.165 | 0.157 | 0.143 | 0.166 |
| ACTIVE W | 0.148 | 0.118 | 0.099 | 0.059 | 0.151 | 0.124 | 0.102 | 0.038 |

### Failed cells (< 11 matched pairs or failed fit), trials x configs x arms summed

| cohort | rung | failed cells (trials x configs x arms) |
|---|---|---|
| v1 | Flags | 18 |
| v1 | hdPS200 | 4 |
| v2 | Flags | 28 |
| v2 | hdPS200 | 6 |
| v2meas | Flags | 298 |
| v2meas | P1 | 6 |
| v2meas | P5 | 6 |
| v2meas | PS10 | 7 |
| v2meas | clinical | 19 |
| v2meas | clinical_nolvef | 17 |
| v2meas | hdPS200 | 141 |
| v2old | Flags | 29 |
| v2old | hdPS200 | 6 |

