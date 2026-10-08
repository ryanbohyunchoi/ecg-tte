# Emulation-quality framework v2.0 (TRACE-ECG, paper 1): trial selection stage 2

Status: **draft for user confirmation** (2026-10-08). Nothing has been scored under this framework. Machine-readable version: [`scoring_template.json`](scoring_template.json).

## 0. Scope

- **What it replaces.** Stage 2 of trial selection in paper 1 (`docs/paper/paper.md`, Methods "Trial selection and target trial specification"; `docs/paper/supplement.md` eMethods 3). That stage graded emulation quality and took the 38 emulated trials down to the analysed set. The current scheme is v1.9 (`docs/v19/quality_tiers.json`, `docs/v19/QUALITY_REAUDIT.md`): flags F1–F5 plus comparator and outcome fidelity, 0–9 points, four tiers.
- **What it does not touch.**
  - Stage 1 (feasibility, 99 → 38; eMethods 3) is unchanged and out of scope. Only the 38 trials that passed stage 1 are scored.
  - The physiologic/domain trial labels (`docs/v21/TRIAL_LABELS.md`) are a separate instrument.
- **What it grades.**
  - (a) How closely the emulation, **as actually built**, reproduces the target-trial protocol.
  - (b) How suitable the question is for emulation in YNHHS EHR data.
- **What it does not grade.** It does not grade confounding adjustment (PS specification, covariates, ECG or CLMBR-T representations). Confounding adjustment is what paper 1 studies, so it cannot also be a selection criterion.

## 1. Principles (apply to every item)

1. **Results are never a scoring criterion.** Raters may see emulation results; the user chose not to blind. No score, adjudication or tier may cite or be motivated by:
   - an emulated HR or CI;
   - agreement with the RCT;
   - balance or SMD;
   - matched-pair counts under any PS specification;
   - plasmode output;
   - any ECG/CLMBR-T effect;
   - R2 or LEGEND-style results.

   Every score must cite design, specification or data-fidelity evidence (§3). A score whose only support is "the estimate looks wrong" is invalid and is reset to the level the cited evidence supports. Each rater record carries a signed attestation (`results_attestation` in the template).
2. **Target = the published protocol.** The comparison is with the primary publication of the trial, plus its design paper or protocol where needed. The benchmark is the one registered in `scripts/trial_specs.py` `PUBLISHED`.
3. **Score every deviation exactly once**, using the allocation table (§5). When an item lists something as "scored elsewhere", it is not scored again here.
4. **Documented adaptation vs undocumented defect.**
   - A *documented adaptation* is a departure from the trial protocol that is stated as a deliberate choice in one of:
     - the spec `note` or `name`;
     - eTable 1 "Design notes and adaptations";
     - an adapted-protocol document (e.g. `docs/COMET_ADAPTED_PROTOCOL.md`).

     It is scored in its domain item (EL, TZ, TS, CO, OU, FU, ES).
   - An *undocumented defect* is a place where the code that built the analysed cohort does something that neither the trial protocol nor the documentation says. It is scored **only** in SI, by the share of patients or events affected.
   - Exception: a placebo proxy is always scored in CO.
   - Once a defect is fixed by a rebuild, its SI points disappear and the domain items are unchanged. Rebuilds are therefore traceable.
5. **Score the code path that built the analysed cohort.** For example, COMET's cohort was built by the JDAT pipeline described in `docs/COMET_ADAPTED_PROTOCOL.md`; its `trial_specs.py` entry only builds OMOP-side features (v19 adjudication). Cite the spec key and `spec_version` (e.g. `cabana_adapted_v2`, `emperor_preserved_adapted_v2`).
6. **Unknowns.**
   - If a deviation is known to be present but its magnitude is unknown, score the middle level (1). If the mechanism is an arm-assignment or time-zero error, score 2. In both cases mark the score `provisional`.
   - If no deviation is found after the item's required sources have been checked, score 0.
   - If an item's required data check is missing, score 1 provisional, but **only** when code review has identified a specific mechanism. With no identified mechanism, score 0.
   - Provisional scores must be resolved before the analysed set is frozen (§7.6).
7. **Thresholds use published numbers.** Take them from the primary paper's baseline table, component table or text. If a trial reports several figures, use the one from the primary-endpoint publication cited in `PUBLISHED`.
8. **Examples are anchors, not scores.** The trial examples below come from earlier audits (v1.9, the R2 blind re-audit, the version 1 audit). They show what kind of feature reaches each level. They do not pre-empt the raters' scores, and each one still needs the evidence listed for its item.

## 2. Items at a glance

| ID | Domain | Item | Points | Assesses |
|---|---|---|---|---|
| EL | Population | Eligibility fidelity | 0–2 | (a) |
| TZ | Time zero and strategies | Time-zero alignment (in-hospital start, run-in, baseline-therapy switch, other misalignment, immortal time) | 0–2 | (a) |
| TS | Time zero and strategies | Intervention-strategy identifiability | 0–2 | (a), (b) |
| CO | Comparator | Comparator fidelity (placebo proxy, substitution, inherent contamination) | 0–2 | (a), (b) |
| OU | Outcome and follow-up | Outcome fidelity (ascertainability, cause-specific death, missing components) | 0–2 | (a), (b) |
| FU | Outcome and follow-up | Follow-up horizon vs trial; long horizon (delayed effect) | 0–1 | (a) |
| ES | Estimand and benchmark | Estimand alignment (per-protocol benchmark; excess crossover) | 0–1 | (a) |
| BM | Estimand and benchmark | Benchmark quality (measure, interval type, precision, isolability, transcription) | 0–1 | (b) |
| DA | Data adequacy | Measurability of population-defining variables; size and events | 0–1 | (b) |
| SI | Implementation | Specification/implementation fidelity: undocumented defects, by share affected | 0–2 | (a) |

**Total 0–16.** Higher is worse. Tiers and caps are in §6.

## 3. Evidence

### 3.1 Citation format (every non-zero score, and every zero on an item where a mechanism was considered)

| Type | Format | Example |
|---|---|---|
| `SPEC` | file:line @ git short SHA, spec key, spec_version | `scripts/trial_specs.py:L874-883 @605f806, lodestar, lodestar_adapted_v1` |
| `CODE` | builder or extractor file:line @ SHA | `scripts/build_trial_cohort.py:L136-144` (earliest-index dedupe) |
| `PUB` | citation + table/figure/page | `Mentz JAMA 2023, Table 1 (prior loop diuretic)` |
| `DATA` | data-check ID (§3.3) + band | `DC-SI-washout: 5-20%` |
| `DOC` | repo document (pointer only; cannot be the sole support) | `docs/v19/QUALITY_REAUDIT.md §4` |

Earlier ratings (v19, R2) may be cited only as `DOC` pointers. Every score must also cite at least one `SPEC`, `CODE`, `PUB` or `DATA` source.

### 3.2 What the code can and cannot express (for raters)

These are facts of the current pipeline that recur in scoring.

- **Drug tokens.** An order matches an arm if any `-`-split token of the lower-cased `drug_source_value` is a keyword (`scripts/trial_common.py` `create_drug_tokens`; `trial_specs.py` header).
  - Formulation, route and dose are not identifiable. Brand tokens can split formulations, e.g. `toprol` is the succinate brand.
  - Combination strings can leak into arms, e.g. a sacubitril-valsartan order whose token is `valsartan`.
- **New-user definition** (`build_trial_cohort.py:L116-126`):
  - first-ever order of an arm drug;
  - no order of the *other arm's* tokens in [index−365, index];
  - `washout_arms` restricts that washout to the listed arms.

  Same-class agents outside both arms are excluded only if listed in `other_drugs_365d` or `other_anticoag_365d`.
- **Dedupe.** A person eligible for both arms is kept once, at the earliest index (`L136-144`). The exceptions are the switch designs and `switch_seq` (sequential sampling, `L281-316`).
- **Gates.**
  - Diagnosis gates use codes dated on or before index, including the index day (`L152-158`). Codes from the index stay can therefore satisfy a "pre-existing condition" gate.
  - The ECG-text gate is a substring match (`L189-193`).
- **Exclusions on measurements** use the latest pre-index value with the index day excluded. **An unknown value passes** (`L11`, `L225-259`). The echo EF window is [index−365, index−1].
- **Outcomes** (`scripts/extract_outcomes.py`):
  - follow-up starts the day after index;
  - `("hosp", codes)` is the first inpatient stay starting after index with a qualifying code in **any** position;
  - `cv_death` is any listed I00–I99 cause, and deaths without a cause record count as CV;
  - composites with cause-specific death are censored at 2024-06-24 (end of cause records);
  - a `proc` outcome component exists only for negative controls.
- **Horizon:** `HORIZON_MONTHS`. **Benchmark:** `PUBLISHED`, with `hr` in the RCT orientation and `our_orientation` for our arm order.

### 3.3 Data checks (computed once, by a data analyst who is not a rater; given to both raters)

- **Scope.** Aggregate checks on the analysed cohort: patients with ECG, before any matching. They contain no outcome contrast and no effect estimate.
- **Where they run.** On the cluster, with `umask 077`. Outputs go to `/mnt/raid0/rbc58/ecg-tte/audits/emulation_quality_v2/data_checks/`.
- **What enters the repo:** only the **band** (`<5%`, `5–20%`, `>20%`, or the DA/ES thresholds). Exact counts stay on raid0. Counts of 1–10 are suppressed, including counts derivable by differencing.

| ID | Used by | Quantity |
|---|---|---|
| DC-SI-* | SI | Share of analysed patients (exposure, eligibility and time-zero defects) or of primary-outcome events (outcome defects) whose arm, eligibility, time zero, or event status/time would change if a suspected undocumented defect were corrected. One check per suspected defect. Seed list: R2 `mustfix_all` (`git show r2:docs/r2/QUALITY_R2.json`), handoff §4 items 1 and 5, and the raters' code review. |
| DC-DA-meas | DA | Share of the analysed cohort with the population-defining measurement in its window (e.g. echo EF in [index−365, index−1] for EF-defined HF trials) |
| DC-DA-size | DA | Smaller-arm size (patients with ECG) and pooled primary-outcome events within the horizon, as bands `<500` / `≥500` and `<100` / `≥100` |
| DC-ES-cross | ES | Share of each arm starting the other arm's strategy within the horizon (orders and procedures only) |
| DC-EL-met | EL | For an omitted population-defining criterion that can be approximated from codes: share of the analysed cohort that meets it anyway (≥90% rule) |

## 4. Items

Every item includes: what it assesses; levels with anchors; required evidence; how to score unknowns; and what is scored elsewhere.

### EL. Eligibility fidelity (0–2)

**Assesses** whether the emulated population matches the trial's **population-defining** criteria:
- the disease or index event;
- required severity or phenotype (e.g. an LVEF threshold, ECG-LVH, early AF);
- risk enrichment (e.g. established CVD, ≥1 stroke risk factor, kidney disease);
- age bounds;
- required prior or background therapy (e.g. "on rate control", "on warfarin").

Safety exclusions (eGFR, potassium, SBP, angioedema, bleeding history) are not population-defining. Score them only if their omission plausibly changes the population materially.

| Points | Anchor |
|---|---|
| 0 | Every population-defining criterion is represented, exactly or by an accepted code/measurement proxy. Or an omitted criterion would be met by ≥90% of the emulated population anyway (DC-EL-met, or clinical reasoning stated in the evidence; e.g. ≥1 stroke risk factor among AF patients starting oral anticoagulation). |
| 1 | **One** population-defining criterion is omitted or approximated in a way that changes who is included. Examples of the type: risk enrichment not applied (CAROLINA high CV risk; REWIND CVD or risk factors; the LEADER ≥60-year risk-factor stratum); frailty instrument replaced by age ≥75 (FRAIL-AF); NYHA class or NT-proBNP not available (RAFT-AF); a stroke-risk route not applied (PROTECT AF, age ≥75 alone); new-user restriction excludes a large experienced subgroup the trial enrolled (ARISTOTLE, ~57% VKA-experienced), unless that is a switch at randomisation (TZ.c). |
| 2 | **Two or more** population-defining criteria omitted or approximated. Or the defining phenotype has no usable EHR proxy, so the emulated population is a different clinical population. |

- **Evidence:**
  - `PUB` (eligibility section or table of the trial);
  - `SPEC` (`gate`, `exclusions`, `min_age`/`max_age`);
  - `DATA` (DC-EL-met) when the ≥90% rule is invoked.
- **Unknown:** if the impact of an omitted criterion is unknown, score 1 provisional.
- **Scored elsewhere:**
  - an undocumented missing numeric bound or a gate error (e.g. an age bound in the protocol but not in the spec and not documented) → SI;
  - criteria that are specified but rarely measurable (unknown passes) → DA.a;
  - baseline therapy stopped at randomisation → TZ.c.

### TZ. Time-zero alignment (0–2)

**Assesses** whether time zero is the same decision point as randomisation, at which eligibility is met and the strategy is assigned. Four features, each present or absent:

| Feature | Present when | Not scored when |
|---|---|---|
| **TZ.a** In-hospital initiation not mirrored | The trial started or randomised treatment during a hospital stay, and emulated time zero cannot be placed at the equivalent in-hospital decision point. Example: an oral discharge strategy whose emulated time zero can fall on an inpatient IV order of the comparator drug (TRANSFORM-HF, v19 F1). | EHR inpatient orders are visible and time zero is the in-hospital start in both arms (PLATO, VALIANT, PROVE IT-TIMI 22; LAAOS III, where surgery is time zero in both arms). |
| **TZ.b** Selective run-in | Before randomisation, an active run-in removed patients for intolerance, non-adherence or non-response to a study drug (PARADIGM-HF enalapril then sacubitril-valsartan; ONTARGET). | A placebo or washout run-in that did not select on response to a study drug (LIFE, INSIGHT; v19 adjudication). |
| **TZ.c** Baseline same-purpose therapy switched at randomisation, not reproduced | ≥30% of randomised patients were on a same-purpose drug that was stopped or replaced **at randomisation**, and the emulation (new-user design with the other-arm washout) neither requires nor reproduces that switch. Examples of the type: ALLHAT, VALUE, ASCOT-BPLA, ACTIVE W, PLATO, VALIANT, PRECISION, TRANSFORM-HF (v19 F3). | The switch happened during a pre-randomisation washout or run-in (that is TZ.b or nothing). A protocol transition window after randomisation, e.g. INR-guided VKA-to-DOAC (ARISTOTLE, ROCKET-AF; Wang 2023 footnote g). A switch or sequential design reproduces the switch (FRAIL-AF; PARADIGM-HF sequential; PROTECT AF). A minority below 30% (e.g. CAROLINA's SU-exposed stratum; PROVE IT ~25% prior statin). |
| **TZ.d** Other misalignment, including immortal time | Eligibility uses information after time zero. Or time is unequally at risk between arms before assignment (immortal time). Or the two arms' time zeros sit at non-equivalent points in the disease course, e.g. a procedure arm that may include prior drug failures vs a drug-initiation arm (check CABANA). | A sequential prevalent new-user comparator sampled at the switch date (±30 d, no future information) is not misalignment by itself. |

| Points | Rule |
|---|---|
| 0 | No feature present |
| 1 | Exactly one feature present |
| 2 | Two or more features. Or TZ.c with **≥50%** of randomised patients switched at randomisation. Or immortal time that the design does not remove. |

- **Evidence:**
  - `PUB` (setting and timing of randomisation; run-in description and the share excluded; baseline-medication table for TZ.c);
  - `SPEC`/`CODE` (`design`, `gate`, washout, dedupe).
- **Unknown:**
  - If the TZ.c share is not reported, use the design paper or baseline table.
  - If it is still unknown, score TZ.c present only when eligibility required or implied prior same-purpose therapy (e.g. treated hypertensives), and mark it provisional.
  - Do not apply the ≥50% escalation to an unknown share.
- **Scored elsewhere:**
  - an undocumented code error in time zero or arm assignment (e.g. a dedupe that assigns most eventual-ablation patients to the drug arm; the R2 CABANA flag) → SI, at 2 if confirmed;
  - horizon → FU.

### TS. Intervention-strategy identifiability (0–2)

**Assesses** whether the **intervention** strategy can be identified from orders and procedures. The comparator arm is scored in CO.

| Points | Anchor |
|---|---|
| 0 | The trial's agent or procedure is identified. Alternatively, the trial allowed any agent of a class and the emulation uses that class (FRAIL-AF, any DOAC). Dose or formulation either does not define the contrast, or the marketed dose equals the trial dose. Dose titration of a fixed agent is not scored (Heyard 2024 found no association). |
| 1 | Class adaptation of the intervention (any ARB for losartan, valsartan or telmisartan; SGLT2i class for empagliflozin). A strategy approximated by its first identifiable component (rhythm control = antiarrhythmic initiation, with cardioversion or ablation-first not captured: AFFIRM, AF-CHF, EAST-AFNET 4). A trial-specified formulation that cannot be identified, where it plausibly does not change the hypothesis (nifedipine GITS). A dose- or intensity-defined contrast that is largely preserved by routine practice, **with evidence** (the PROVE IT-TIMI 22 question: atorvastatin 80 vs pravastatin 40). |
| 2 | The hypothesis depends on a strategy feature that cannot be identified: an arm-defining co-therapy (ACTIVE W, clopidogrel **plus aspirin**, with aspirin OTC and not identifiable), or a dose or intensity contrast with no evidence that routine practice preserves it. |

- **Evidence:**
  - `PUB` (intervention definition and dosing);
  - `SPEC` (arm tokens or procedure codes);
  - for the "preserved by practice" clause, a cited practice-pattern source or a `DATA` check if dose is recoverable.
- **Unknown:** if it is unclear whether practice preserves the contrast, score 1 provisional.
- **Scored elsewhere:**
  - an undocumented token error (wrong formulation brand in an arm; combination-product leakage) → SI;
  - missing class washouts → SI.

### CO. Comparator fidelity (0–2)

**Assesses** whether the comparator strategy reproduces the trial's comparator.

| Points | Anchor |
|---|---|
| 0 | The trial's comparator agent or procedure (or its allowed set) is observable and used. For "continue current therapy" comparators, established users are sampled by a sequential design (FRAIL-AF; PROTECT AF). |
| 1 | Class adaptation of the comparator: any ACEi for enalapril, captopril or ramipril; thiazide class for chlorthalidone or co-amilozide; cardioselective β-blocker for atenolol. A comparator strategy narrower or broader than the trial's, e.g. antiarrhythmic initiators only vs "rate or rhythm drugs" (CABANA). A comparator defined by the absence of an under-recorded code (LAAOS III, surgery without an LAA-occlusion code). A documented, inherent contamination that cannot be removed with available data. |
| 2 | **Placebo proxy**: a placebo-controlled trial emulated with an active comparator assumed to have no effect on the outcome (DPP-4i or sulfonylurea proxies). Or a substitution that changes the trial hypothesis. Or a comparator with its own established effect on the primary outcome that cannot be removed. |

- **Placebo-proxy flag.** Set `placebo_proxy = true` whenever CO = 2 because of a placebo proxy. The flag drives a tier rule (§6).
- **Evidence:** `PUB` (comparator arm), `SPEC` (comparator tokens or codes, `washout_arms`).
- **Unknown:** n/a; the comparator is always documented.
- **Scored elsewhere:** contamination that a list edit could remove and that is not documented as accepted goes to SI, scored by share. Examples: saxagliptin or alogliptin in a DPP-4i proxy for an HF-hospitalisation endpoint (R2 flag for EMPEROR-Preserved and DECLARE-TIMI 58); antiarrhythmic users in a "continued rate control" arm, if undocumented.

### OU. Outcome fidelity (0–2)

**Assesses** whether the trial's primary endpoint can be ascertained, and how it is defined in the emulation.

| Points | Anchor |
|---|---|
| 0 | Every component is ascertained as coded hospitalisations, coded procedures or all-cause death, with the index stay excluded, and matches the trial's definition (e.g. stroke or systemic embolism; all-cause death). |
| 1 | Any one or more of: (i) cause-specific death required (CV, vascular or CHD death from listed causes, undetermined counted as CV; **always 1**, as an explicit anchor); (ii) a **non-dominant** component (<33% of RCT primary events and not the most frequent) missing or approximated; (iii) events ascertained only from inpatient stays where the trial also counted outpatient-diagnosed events in a minor share; (iv) peri-procedural or index-stay events excluded where the trial counted them, in a minor share (LAAOS III). Level-1 features do not add up to 2. |
| 2 | The **dominant** component (the most frequent, or ≥33% of RCT primary events) cannot be ascertained with available data (FRAIL-AF: clinically relevant non-major bleeding). Or inpatient-only ascertainment misses a large share of the endpoint (AMPLIFY: outpatient-managed recurrent DVT and VTE-related death). Or the emulated endpoint is a materially different construct. |

- **Evidence:**
  - `PUB` (component table, or first-event counts by component);
  - `SPEC` (`OUTCOMES`);
  - `CODE` (`extract_outcomes.py`);
  - the eTable 1 and Table 1 notes, checked against the code (the CABANA footnote mismatch is a known case to verify).
- **Unknown:** if component shares are not published, use total component counts. If those are not reported either, treat the component as non-dominant unless it is the most frequent component in comparable trials, and mark provisional.
- **Scored elsewhere (SI):**
  - a component that **is** ascertainable with existing data (e.g. coronary revascularisation from procedure codes) but is omitted *without* being documented;
  - persisting index-event codes counted as new events (AMPLIFY: VTE codes in any position on later stays, R2 flag);
  - a code list that contradicts the documented definition.

  A component whose omission is documented ("not captured") is scored here, by the dominance rule. For example, LODESTAR and PROVE IT-TIMI 22 revascularisation is documented as not captured, so it is scored in OU. Once a rebuild adds it, OU is re-scored.

### FU. Follow-up horizon and delayed effect (0–1)

| Points | Anchor |
|---|---|
| 0 | `HORIZON_MONTHS` is <48 months **and** within 0.75–1.33 times the benchmark's median (or primary-analysis) follow-up |
| 1 | Either: **FU.a** horizon ≥48 months, where an ITT-like emulation accumulates routine-care discontinuation and delayed effects are diluted (RCT-DUPLICATE "delayed effect with long follow-up"; v19 F4, applied mechanically for reliability); or **FU.b** horizon ratio outside 0.75–1.33 (e.g. TRANSFORM-HF, 12 months vs a benchmark median of about 17 months; R2 flag) |

- **Evidence:** `SPEC` (`HORIZON_MONTHS`), `PUB` (median follow-up of the benchmark analysis).
- **Unknown:** if median follow-up is not reported, use the mean or the planned follow-up and note which.

### ES. Estimand alignment (0–1)

**Assesses** whether the emulation's estimand, the effect of initiation (ITT-like), matches the benchmark's estimand, and whether routine-care crossover makes the emulated contrast a different question.

| Points | Anchor |
|---|---|
| 0 | The benchmark is an ITT (or modified ITT) estimate, and emulated crossover is not materially above the trial's |
| 1 | Either: **ES.a** the registered benchmark is a per-protocol or on-treatment estimate (TECOS per-protocol primary; this is why ROCKET-AF uses the ITT benchmark); or **ES.b** the share of either arm starting the other arm's strategy within the horizon (DC-ES-cross) exceeds the trial's reported crossover by ≥20 percentage points. If the trial does not report crossover, assume ≤10% for blinded drug trials. |

- **Evidence:** `SPEC` (`PUBLISHED` `measure`), `PUB` (analysis population; crossover), `DATA` (DC-ES-cross).
- **Unknown:** if DC-ES-cross is not available, score ES.b 0 unless a specific mechanism is documented (e.g. secular replacement of the comparator by the intervention during the study period). In that case score 1 provisional.
- **Scored elsewhere:** the measure type (HR vs RR) → BM.

### BM. Benchmark quality (0–1)

**Assesses** whether the RCT benchmark is a usable, comparable target for an emulated Cox HR.

| Points | Anchor |
|---|---|
| 0 | An ITT HR with a frequentist 95% (or similar level) CI, for the endpoint emulated, transcribed and oriented correctly |
| 1 | Any of: **BM.a** a measure other than an HR (RR, rate ratio, subdistribution HR, odds ratio; e.g. ALLHAT, ONTARGET, INSIGHT, ACTIVE W, AMPLIFY, RE-LY); **BM.b** a Bayesian credible interval (PROTECT AF); **BM.c** a covariate-adjusted primary HR (LIFE); **BM.d** an imprecise benchmark, with an upper/lower CI-limit ratio >3; **BM.e** a benchmark for an arm, dose or co-primary endpoint that the emulation cannot isolate (check RE-LY 150 mg, where 110 mg is not US-marketed, and DECLARE-TIMI 58 co-primary); **BM.f** any transcription or orientation discrepancy between `PUBLISHED` and the publication (check the COMET CI orientation). |

- A CI level other than 95% (95.02%, 95.7%, 96%, 97.5%) is not scored.
- A BM point never triggers a cap (§6). It is mainly a guard for the agreement analyses.
- **Evidence:** `SPEC` (`PUBLISHED`), `PUB` (abstract and results table).
- **Unknown:** n/a.

### DA. Data adequacy (0–1)

| Points | Anchor |
|---|---|
| 0 | Neither feature present |
| 1 | Either: **DA.a** a population-defining criterion that depends on a measurement (LVEF, ECG-LVH text, a population-defining eGFR range) is measured in <50% of the analysed cohort, so most patients pass it as unknown (DC-DA-meas; R2 flag for VALIANT EF-unknown patients); or **DA.b** the smaller arm of the analysed cohort has <500 patients, or pooled primary-outcome events within the horizon are <100 (DC-DA-size). |

- **Evidence:** `DATA` (DC-DA-meas, DC-DA-size), `CODE` (unknown-passes rule).
- **Unknown:** if a data check is not run, score 1 provisional only when DA.a applies by design (an EF-defined trial); otherwise 0.
- **Notes:**
  - Stage 1 already required ≥300 in the smaller arm and ≥50 pooled events. DA.b flags trials just above that floor, where downstream analyses are fragile.
  - Pooled event counts are a feasibility quantity, not a result. Arm-specific counts and any effect estimate are never used.

### SI. Specification and implementation fidelity: undocumented defects (0–2)

**Assesses** whether the code that built the analysed cohort implements the protocol and the documented adaptations, **verified against data**. Defect types to check in every trial:

1. **Arm tokens or codes:** wrong agent or formulation token (e.g. `toprol` in an arm labelled metoprolol tartrate), or combination-product leakage (ARNI orders tokenised as `valsartan` in an ARB arm: ELITE II, VALIANT).
2. **Washout lists**, including **class washouts** the trial imposed: other GLP-1RAs (LEADER, SUSTAIN-6, REWIND); other SGLT2i (DECLARE-TIMI 58, CANVAS); other DOACs.
3. **Removable comparator contamination** by agents with their own effect on the outcome (saxagliptin or alogliptin for HF outcomes).
4. **Numeric bounds** stated in the protocol but missing from the spec (e.g. the CAROLINA age range 40–85).
5. **Gates:**
   - text matches including hedged or negated statements (LIFE ECG-LVH);
   - index-stay codes satisfying a pre-existing-condition gate (LAAOS III post-operative AF);
   - measurement windows that miss the relevant day.
6. **Outcome code lists:**
   - ascertainable components omitted without documentation;
   - persisting index-event codes counted as events (AMPLIFY);
   - definitions that contradict the table or footnote.
7. **Arm assignment and time zero in code:** dedupe or ordering rules that put patients in the wrong arm or at the wrong date (R2 CABANA flag).

**Denominator.**
- For defect types 1–5 and 7: analysed patients, i.e. patients with ECG before matching.
- For type 6: primary-outcome events within the horizon.
- The share is the proportion whose arm, eligibility, time zero, or event status or time would change if the defect were corrected (DC-SI-*).
- With several defects on the same denominator, use the share of the union. If only per-defect shares are known, use their sum (conservative).

| Points | Rule |
|---|---|
| 0 | No undocumented defect, or the affected share is <5% |
| 1 | Affected share 5–20% |
| 2 | Affected share >20%, **or** an arm-assignment or time-zero error that cannot be fixed by excluding the affected patients (e.g. patients assigned to the wrong arm, or to the wrong index date within the right arm) |

- **Evidence:**
  - `CODE`/`SPEC` (the exact line and the proposed edit);
  - `DATA` (DC-SI-* band);
  - `PUB` (the protocol rule the code contradicts).
- **Unknown:** if the share is not checked, score 1 provisional. If the mechanism is arm assignment or time zero, score 2 provisional.
- **Record each defect** in `si_defects` (template): description, type, denominator, band, whether it is fixable by exclusion, and the proposed spec edit. New spec edits go in a new spec version, never as a silent edit to `trial_specs.py` (AGENTS.md).

## 5. Allocation table (score once)

| Deviation | Documented adaptation → | Undocumented / correctable defect → |
|---|---|---|
| Population criterion omitted or approximated | EL | SI (type 4–5) |
| Population-defining measurement mostly unknown (unknown passes) | DA.a | n/a |
| In-hospital start, run-in, switch at randomisation, other time zero | TZ | SI (type 7) if a code error |
| Intervention agent, formulation, strategy | TS | SI (type 1) |
| Same-class agent not washed out | n/a | SI (type 2) |
| Comparator agent, class or strategy; placebo proxy | CO | SI (type 1, 3) |
| Outcome component not ascertainable, or omitted with documentation | OU | n/a |
| Outcome component ascertainable but omitted undocumented; persisting codes; code list contradicts the definition | n/a | SI (type 6) |
| Horizon | FU | n/a |
| Per-protocol benchmark; excess crossover | ES | n/a |
| Measure, interval, precision, isolability, transcription of the benchmark | BM | BM.f |
| Small arm or few events | DA.b | n/a |

## 6. Total, tiers and the analysed set

**Total** = EL + TZ + TS + CO + OU + FU + ES + BM + DA + SI (0–16). Let *N2* be the number of items scored 2, and *PP* the placebo-proxy flag.

Rules are applied in order; the first that matches sets the tier.

| Order | Tier | Rule |
|---|---|---|
| 1 | **Limited** | Total ≥ 8; **or** N2 ≥ 2; **or** PP **and** (total − CO) ≥ 3; **or** SI = 2 because of an arm-assignment or time-zero error (until rebuilt and re-scored) |
| 2 | **Moderate** | Total 5–7; **or** N2 = 1 (any single item at 2 caps the tier at Moderate, whatever the total) |
| 3 | **Good** | Total 3–4, with no item at 2 |
| 4 | **Excellent** | Total 0–2, with no item at 2 |

- **Placebo-proxy combination rule.** A placebo proxy (CO = 2) by itself caps a trial at Moderate. Together with another item at 2, or with ≥3 points from the other items, it gives Limited. The rationale is that a placebo proxy already changes the estimand, and further deviations then compound it (§9, L4).
- **Analysed set (primary).** **Excellent + Good + Moderate.** Limited emulations are excluded from the primary analysed set.
- **Sensitivity sets.**
  - Excellent + Good.
  - All 38.
  - Trials with no provisional score that could change their tier.
- **Rebuilds.** A trial that is Limited only because of SI (rule 1, last clause, or SI points pushing the total over 7) is re-scored after a rebuild that fixes the defect. It enters the analysed set only through a dated amendment committed before any analysis of the new set (§7.6).

## 7. Scoring procedure

### 7.1 Raters

- Two independent raters score all 38 trials from this text.
- Rater identity (human clinician, human methodologist, or LLM agent with model and run) is recorded in every record.
- If either rater is an LLM agent, the report says so. Agreement between two runs of one model is reported as such, not as human inter-rater reliability (the R2 caveat).
- The adjudicator should be a clinician, or the clinician review (§7.5) covers every adjudicated point.

### 7.2 Inputs given to both raters

- this framework and the template;
- `scripts/trial_specs.py`, `scripts/build_trial_cohort.py`, `scripts/trial_common.py` and `scripts/extract_outcomes.py` at a fixed SHA;
- `docs/COMET_ADAPTED_PROTOCOL.md`;
- eTable 1 design notes;
- the trial publications;
- the data-check bands (§3.3).

Raters may also see emulation results; results are not a criterion (§1.1). To keep the ratings independent, raters do not consult the v19 or R2 per-trial tiers or item scores before submitting. The R2 must-fix list enters only as seeds for the data checks, which both raters receive.

### 7.3 Calibration (before scoring the 38)

- Both raters score 4 trials that are **not** among the 38, then compare and discuss: PARAGON-HF, DAPA-HF/EMPEROR-Reduced, PARTNER and PARADISE-MI, which are specified in `trial_specs.py` but not in the analysed set.
- Clarifications are written into this document as v2.0.x before any of the 38 are scored.
- No anchor may be changed after scoring of the 38 starts, except by a logged amendment applied to all trials (§7.6).

### 7.4 Independent scoring, then adjudication

1. Each rater fills one record per trial (`scoring_template.json` → `records`), with an item score, features, evidence and a `final`/`provisional` status. Records are committed (or hashed) before either rater sees the other's.
2. Total and tier are computed **mechanically** from the item scores by the §6 rules, not by judgement.
3. **Adjudication**, item by item, by the adjudicator:
   - The adjudicator compares the two scores against the rubric text and the cited evidence, and records the deciding clause (e.g. "TZ.c exemption: transition window").
   - If the rubric text does not decide, the more severe score stands, and the ambiguity is logged as a clarification for the next version.
   - No adjudication may cite results.
4. **Reliability, reported for the unadjudicated ratings with 95% bootstrap CIs over trials (2,000 resamples):**
   - percent agreement and Cohen's κ for each 0–1 item, each TZ/ES/BM/DA feature and analysed-set membership;
   - linear-weighted κ for each 0–2 item and for the 4-level tier, plus unweighted tier κ;
   - ICC(2,1), absolute agreement, for the total;
   - prevalence of each item alongside κ, because κ is unstable for rare features such as TZ.b.

   There is no re-scoring loop based on κ.

### 7.5 Clinician review list (output of adjudication)

- every item-level disagreement, with both scores and the adjudicated score;
- every item scored 2 in the adjudicated record;
- every trial within 1 point of a tier threshold, or whose tier depends on a provisional score;
- every application of the placebo-proxy combination rule;
- every SI defect, with its band and proposed spec edit.

The clinician confirms or overrides each one, citing a rubric clause. Overrides are logged in the adjudicated record (`clinician_review`).

### 7.6 Freeze, amendments, privacy

- **Freeze.** The adjudicated scores, tiers and analysed set are committed under a dated tag before any analysis is run, or text is updated, on the new set. While a provisional score could change a tier, the analysed set is not frozen. Either resolve it with a data check, or freeze with the trial listed under "provisional" and carry it into the sensitivity set (§6).
- **Amendments** (after a rebuild, or a rubric clarification) apply to all 38 trials, carry a version number and date, and are committed before the affected analyses are re-run. Results are never the reason for an amendment.
- **Privacy.**
  - The repository holds item scores, evidence citations and data-check **bands** only.
  - Exact counts and patient-level outputs stay under `/mnt/raid0/rbc58/ecg-tte/audits/emulation_quality_v2/` (umask 077).
  - Counts of 1–10 are suppressed, including derivable ones.

### 7.7 Rater steps per trial (checklist)

1. From the publication, write the target protocol: eligibility, strategies, assignment and time zero, outcome, follow-up, estimand, and benchmark measure.
2. Read the spec entry (key, `spec_version`) and the code path that built the cohort.
3. List every departure. Classify each as a documented adaptation or an undocumented defect (§1.4).
4. Assign each departure to one item (§5). Score each item with its anchors.
5. Cite evidence for each item. Mark statuses.
6. Fill `si_defects`, `si_reason`, `placebo_proxy` and the attestation. Total and tier are computed by script.

## 8. Mapping from v1.9 (traceability)

| v1.9 item (points) | v2.0 item | Change |
|---|---|---|
| F1 in-hospital initiation not mirrored (1) | TZ.a | Same definition, including the visible-inpatient-order exemption |
| F2 selective run-in (1) | TZ.b | Same. Placebo or washout run-ins not scored (v19 adjudication made explicit) |
| F3 baseline-therapy switch at randomisation (1) | TZ.c | "Substantial share" is made numeric (≥30%). ≥50% gives TZ = 2 on its own. Exemptions written in. |
| F4 horizon ≥48 mo with delayed effect (1) | FU.a | Unchanged and mechanical. FU.b (horizon vs benchmark follow-up) added. |
| F5 other time-zero misalignment (1) | TZ.d | Immortal time and non-equivalent decision points are named explicitly |
| Flags summed without cap (0–5) | TZ capped at 2; FU 0–1 | One time-zero domain cannot dominate the total |
| Comparator fidelity good/moderate/poor (0/1/2) | CO (comparator arm) + TS (intervention arm) | v19 graded class adaptations of either arm under "comparator". v2 splits them by arm. Placebo proxy = CO 2, as before. |
| Outcome fidelity good/moderate/poor (0/1/2) | OU (documented or not ascertainable) + SI type 6 (undocumented or correctable) | Explicit anchor: cause-specific death = 1. Dominance threshold set at 33% of RCT events. |
| (none) | EL, ES, BM, DA, SI | New items (§9) |
| Tiers on 0–9: Excellent 0; Good 1–2 (no poor item, ≤1 flag); Moderate 3 or capped; Limited ≥4 | Tiers on 0–16: Excellent 0–2; Good 3–4; Moderate 5–7 or one item at 2; Limited ≥8, two items at 2, placebo proxy + ≥3, or an SI arm-assignment error | The ceiling rule is generalised to "any item at 2 caps at Moderate". A combination rule is added for placebo proxies. |
| Analysed set = Excellent–Moderate | Same | The rule is unchanged; the items behind it are not |

## 9. Rationale for each new or changed element, with the lesson behind it

| Lesson | Source | What it changed |
|---|---|---|
| **L1.** Quality tiers and the analysed set were finalised after results were seen | v1 known defect 6 (`git show r2:docs/r2/V1_MANIFEST.md`); eMethods 3 ("graded scale defined after the primary analyses") | §1.1: results are never a criterion. Mandatory evidence per score; signed attestation; mechanical tiers; freeze before any analysis (§7.6) |
| **L2.** Agreement by quality tier reverses under blind tiers | `docs/v1_audit/DEFECT_IMPACT.md` §6 (C22) | The framework is not validated or weighted by RCT agreement. Weights come from design reasoning and external evidence (RCT-DUPLICATE) only. |
| **L3.** Benchmark-permutation and attenuation: emulated estimates move toward the null, and "agreement" gains are not trial-specific | paper.md Results (permutation P = .26); v1 defect 2; DEFECT_IMPACT (shrinkage reproduces 79–110% of the gains) | Features that make an emulation answer a weaker or different contrast are scored as design deviations, not left to agreement metrics: excess crossover (**ES.b**), long horizons under an ITT-like estimand (**FU.a**), removable comparator contamination (**SI** type 3). **BM.d** flags benchmarks too imprecise to tell trial-specific agreement from shrinkage. |
| **L4.** Placebo proxies agree worst and change the estimand | Franklin et al. Circulation 2021; Wang et al. JAMA 2023; Heyard et al. BMJ Med 2024 (placebo control a significant univariate term); `docs/LITERATURE_RCT_DUPLICATE_LANDSCAPE.md` (sulfonylurea proxies worse than DPP-4i); v19 weighting | CO = 2 for any placebo proxy; PP + ≥3 other points → Limited |
| **L5.** Code-level defects persisted that a design-only rating could not see | R2 blind re-audit: 11 consensus must-fix flags (COMET token, EMPEROR-Preserved DPP-4i agents, GLP-1RA/SGLT2i class washouts ×5, LIFE ECG text, LODESTAR/PROVE IT revascularisation, TRANSFORM-HF time zero), plus single-auditor flags (CABANA dedupe, ELITE II/VALIANT ARNI tokens, CAROLINA age, AMPLIFY persisting codes, LAAOS III post-operative AF); handoff §4 items 1 and 5 | **SI**, scored by the share affected and verified against data. It drops to 0 after a rebuild. **Documented vs undocumented** allocation (§1.4) |
| **L6.** The R2 rubric had low reliability: tier κ 0.33 (weighted 0.42) | `git show r2:docs/r2/QUALITY_R2.md`. Item agreement recomputed from the R2 auditor files: outcome 20/38, benchmark 26/38, strategy 28/38; adherence 36/38, nearly all "moderate", so it did not discriminate. B/C thresholds were undefined, and the auditors invented their own. | Points with numeric thresholds instead of counts of good/moderate/poor; explicit anchors where R2 split (cause-specific death = OU 1; RR vs HR = BM, not ES); the vague "adherence" item replaced by a measurable crossover criterion (ES.b); fully specified tier rules; calibration on non-analysed trials (§7.3) |
| **L7.** F3 was the least reliable v19 item (κ 0.54) | `docs/v19/QUALITY_REAUDIT.md` §3–4 | TZ.c threshold (≥30%) and written exemptions (washout run-in; transition window; switch designs) |
| **L8.** Discontinuation of maintenance therapy without washout was the strongest single source of RCT–RWE divergence; in-hospital start and delayed effect were retained in the final model | Heyard et al. BMJ Med 2024 (discontinuation R² 0.56); Wang et al. JAMA 2023 close-emulation criteria | TZ.c ≥50% → TZ = 2 on its own; TZ.a and FU.a kept |
| **L9.** Unknown measurement values pass exclusions, so EF-defined populations can be mostly unverified | `build_trial_cohort.py` L11; R2 VALIANT flag | **DA.a** (coverage <50%) |
| **L10.** Small trials are fragile downstream | v1 defect 3 (PROTECT AF effectively dropped under a fixed penalty); version 1 audit code should-fix F1 (PROTECT AF hdPS cells with 1–10 pairs) | **DA.b**, on pre-matching size and pooled events, so no result is used |
| **L11.** The benchmark estimand and statistic need checking, not assuming | R2 benchmark flags (TECOS per-protocol, PROTECT AF Bayesian rate ratio, RR trials, LIFE adjusted HR, COMET CI orientation, TRANSFORM-HF horizon); ROCKET-AF ITT choice (Table 1 note) | **ES.a**, **BM**, **FU.b** |
| **L12.** No eligibility item in v19, although R2 rated eligibility "poor" in 5 trials | `QUALITY_R2.json` (FRAIL-AF, PROTECT AF, ACTIVE W, TRANSFORM-HF, VALIANT) | **EL**, with a ≥90%-met rule so that it discriminates instead of being "moderate" everywhere |
| **L13.** Intervention-side and comparator-side adaptations were mixed in one v19 item, which caused 4 adjudications (LAAOS III, COMET, TRANSFORM-HF, PROVE IT) | `docs/v19/QUALITY_REAUDIT.md` §4 | **TS** for the intervention arm vs **CO** for the comparator arm |
| **L14.** Footnotes and code diverged | handoff §4 item 5 (CABANA outcome footnote) | OU and SI require the outcome definition to be checked against the code, not only the table |

## 10. Alignment with RCT-DUPLICATE and TARGET

- **RCT-DUPLICATE design-emulation dimensions** (Wang 2023; Heyard 2024):

  | Dimension | Item |
  |---|---|
  | In-hospital start | TZ.a |
  | Selective run-in | TZ.b |
  | Discontinuation of baseline therapy at randomisation | TZ.c |
  | Delayed effect with long follow-up | FU.a |
  | Comparator emulation | CO |
  | Outcome emulation | OU |
  | Placebo emulated with an active comparator | CO = 2 / PP |
  | Dose titration | TS (not scored unless dose defines the contrast) |

  RCT-DUPLICATE's "close emulation" corresponds roughly to Excellent/Good with TZ = 0 and FU = 0.
- **TARGET guideline protocol components** (Cashin et al. 2025):

  | Component | Item |
  |---|---|
  | Eligibility | EL, DA.a |
  | Treatment strategies | TS, CO |
  | Assignment and time zero | TZ |
  | Outcome | OU |
  | Follow-up | FU |
  | Causal contrast | ES |
  | Statistical analysis | Not graded (the object of study) |

  TARGET's requirement to report differences between target and emulated protocol is met by eTable 1 (documented adaptations) and the `si_defects` list.

## 11. Design choices for the user to confirm

1. **Outcome-defect denominator in SI.** The brief says "share of the analysed cohort". For outcome-code defects, this framework uses the share of **primary-outcome events**, because event rates are 5–25%: a defect touching half the events would otherwise score only 0–1.
2. **Documented vs undocumented split** (§1.4). Documented adaptations go to the domain items. Undocumented, correctable defects go only to SI, by share. Example: the LODESTAR and PROVE IT revascularisation omission is documented, so it stays in OU (likely 2) until a rebuild adds a procedure component.
3. **TZ.c thresholds:** ≥30% switched at randomisation for the feature, and ≥50% for TZ = 2 on its own. This makes the majority-switch hypertension trials capped at Moderate regardless of total.
4. **Tier cut-points on 0–16** (0–2 / 3–4 / 5–7 / ≥8) and the placebo-proxy rule (PP + ≥3 other points → Limited).
5. **Sulfonylurea proxies.** By default, sulfonylurea and DPP-4i proxies are treated alike (CO = 2). An option is to count a sulfonylurea proxy as a second poor item (→ Limited for TECOS and CARMELINA), because RCT-DUPLICATE found SU proxies agreed worst. That finding is mainly attributed to channelling (residual confounding), not a pharmacological effect, and CAROLINA showed glimepiride ≈ linagliptin, so this option is not the default.
6. **FU.a stays mechanical** (≥48 months, whatever the intervention), as in v19, for reliability.
7. **DA.b thresholds** (<500 in the smaller arm; <100 pooled events) above the stage-1 floor (300/50).
8. **BM is in the total (0–1) but never caps.** An alternative is to report BM separately, outside the total, because it concerns the agreement analysis rather than emulation fidelity.
9. **Raters.** Who are the two raters (clinician, methodologist, LLM agent)? Who adjudicates? Is the calibration on PARAGON-HF, DAPA-HF/EMPEROR-Reduced, PARTNER and PARADISE-MI acceptable?

## 12. References

- Wang SV, Schneeweiss S, et al. Emulation of randomized clinical trials with nonrandomized database analyses: results of 32 clinical trials. JAMA 2023;329:1376-85.
- Heyard R, Held L, Schneeweiss S, Wang SV. Design differences and variation in results between randomised trials and non-randomised emulations: meta-analysis of RCT-DUPLICATE data. BMJ Med 2024;3:e000709.
- Franklin JM, Patorno E, Desai RJ, et al. Emulating randomized clinical trials with nonrandomized real-world evidence studies: first results from the RCT DUPLICATE initiative. Circulation 2021;143:1002-13.
- Cashin AG, Hansford HJ, Hernán MA, et al. Transparent reporting of observational studies emulating a target trial: the TARGET guideline. 2025 (JAMA; BMJ).
- Hernán MA, Robins JM. Using big data to emulate a target trial when a randomized trial is not available. Am J Epidemiol 2016;183:758-64.
- Project sources:
  - `docs/v19/QUALITY_REAUDIT.md`, `docs/v19/quality_tiers.json`;
  - `git show r2:docs/r2/PROTOCOL_R2.md` §1.3, `git show r2:docs/r2/QUALITY_R2.{md,json}`;
  - `plan.md` §2 and §4.4;
  - `docs/v1_audit/`;
  - `docs/v21/TRIAL_LABELS.md`;
  - `docs/LITERATURE_RCT_DUPLICATE_LANDSCAPE.md`.
