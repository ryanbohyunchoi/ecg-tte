# Independent audit of the emulation-quality v2.0 scoring and adjudication (38 trials)

Date: 2026-10-08. Auditor: Claude Opus 5.5 agent run. It took no part in rating or adjudication and is another run of the same LLM, so it is not an independent human review.
Audited: [`QUALITY_FRAMEWORK.md`](QUALITY_FRAMEWORK.md), [`scoring_template.json`](scoring_template.json),
[`ADJUDICATION.md`](ADJUDICATION.md), [`quality_v2_final.json`](quality_v2_final.json),
`scripts/emulation_quality_v2/adjudicate.py`, rater files and aggregates in `/mnt/raid0/rbc58/ecg-tte/audits/claude-eq2/`,
the data-check report [`../v1_criteria_check/TRIAL_CRITERIA_CHECK.md`](../v1_criteria_check/TRIAL_CRITERIA_CHECK.md)
and `audits/claude-v1-criteria/*.csv`, `scripts/trial_specs.py` @7fff3d9, eTable 1 (`docs/paper/supplement.md`),
`docs/COMET_ADAPTED_PROTOCOL.md`, and `docs/v17/candidates.md` / `docs/v18/af_candidates.md` (arm sizes).
Audit code (independent of `adjudicate.py` and `sens_primary32.py`) and outputs:
`/mnt/raid0/rbc58/ecg-tte/audits/claude-eq2/audit/` (`recompute_tiers.py`, `recomputed_tiers.csv`, `impact_check.py`,
`impact_recheck.csv`, `agreement_spot.py`). No other file was changed and nothing was committed.

## Verdict (plain language)

**Do not use the 29-trial set as it stands as the frozen primary analysed set. Use it only as a provisional working set,
labelled unfrozen, until the two blocking items below are resolved.**

- **The arithmetic is right.** I recomputed every total, tier and the analysed set from the adjudicated item scores with
  my own code and got no mismatches (38/38). The impact table reproduces exactly: the published-32 gate passes and the
  29-trial row matches.
- **Most cited evidence holds up.** In the 21 trials I checked against the spec, code, data-check bands and publications,
  the scores that *were* given are supported. I found no score that cites results.
- **The problem is what was not scored, unevenly.** Membership of up to five analysed trials depends on deviations that
  the adjudication scores in some trials but leaves unscored in others of the same kind:
  - EMPA-REG OUTCOME, TECOS and CARMELINA each sit exactly at the placebo-proxy line (other points = 2).
  - ALLHAT and ASCOT-BPLA each sit one point below Limited (total 7).

  For each of these five there is at least one unscored deviation of a type that is scored elsewhere (finding B1). One
  extra point moves any of them to Limited.
- **The framework's own freeze conditions are not met** (finding B2):
  - 10 analysed trials have provisional scores that could change their tier;
  - none of the §3.3 data checks has been run;
  - the clinician review (§7.5) has not been done;
  - the rater records were not committed or hashed before adjudication.
- **Five data-check MAJOR trials end at Moderate** (LAAOS III, COMET, TRANSFORM-HF, LIFE, VALIANT). This follows from
  the rules as written, not from scoring errors, but for LAAOS III, TRANSFORM-HF and LIFE it is a real design gap (section
  6). Exclusion-type rebuilds before freeze are the cleanest fix.

## Findings

### BLOCKING

**B1. Same type of deviation scored in some trials and not in others; five analysed-set memberships depend on it.**

The adjudicator scored several deviations under a reading the rubric text supports:
- undocumented numeric entry bounds go to SI type 4, 1 provisional when the share is unknown (LIFE and INSIGHT blood
  pressure; PARADIGM-HF and EMPEROR-Preserved NT-proBNP);
- a new-user design that excludes a large treatment-experienced subgroup of the trial gets an EL point (ARISTOTLE,
  ROCKET-AF, RE-LY);
- a population restriction forced by the proxy comparator gets an EL point separate from CO (EMPEROR-Preserved T2D;
  rater A's calibration lesson).

These readings were not applied to trials where both raters scored 0, because adjudication only revisits disagreements.
Applying them uniformly gives:

| Trial (tier now) | Unscored deviation of an already-scored type | Item it would add | Resulting tier if share unknown (1 provisional) |
|---|---|---|---|
| EMPA-REG OUTCOME (Moderate; PP, other = 2) | HbA1c 7–10% entry window (7–9% if drug-naive) and BMI ≤45. HbA1c is in OMOP gold (`docs/DATA_SOURCES.md`). Not in the spec, not documented. | SI type 4 | **Limited** (PP + 3) |
| TECOS (Moderate; PP, other = 2) | (i) HbA1c 6.5–8.0% on stable background therapy (Green NEJM 2015 Methods). (ii) Background oral agent or insulin required. (iii) About 45% of TECOS patients were on a sulfonylurea at baseline ([secondary summary](https://www.rxfiles.ca/rxfiles/uploads/documents/TECOS-Trial-Summary.pdf); [Bethel 2019](https://onlinelibrary.wiley.com/doi/full/10.1002/edm2.53)); the other-arm washout (no SU in [index−365, index]) excludes this subgroup from the sitagliptin arm. | SI type 4 (i); EL (ii, iii: experienced-subgroup anchor, as in ARISTOTLE) | **Limited** (PP + ≥3) |
| CARMELINA (Moderate; PP, other = 2) | HbA1c 6.5–10.0%. About 32% on SU at baseline ([secondary summary](https://nerdcat.org/studysummaries/linagliptin); verify Table 1), excluded from the linagliptin arm by the SU washout. | SI type 4; EL (EL already 1, so 2) | **Limited** (PP + 3, or N2 = 2) |
| ASCOT-BPLA (Moderate; total 7) | BP entry: untreated ≥160/100 or treated ≥140/90 (uncontrolled). This is a severity stratum beyond "treated hypertension", which is rater A's own criterion for counting LIFE and INSIGHT. | SI type 4 | **Limited** (total 8) |
| ALLHAT (Moderate; total 7) | BP entry bounds (untreated 140–180/90–110; treated ≤160/100). Weaker: mostly upper bounds. It counts only under the adjudicator's broad "any protocol numeric bound → SI type 4" reading, not under rater A's severity reading. | SI type 4 | Limited under the broad reading; Moderate under the severity reading |
| VALUE (Moderate; total 6) | BP entry bounds | SI type 4 | Moderate (7) |
| CAROLINA (Good; total 4) | HbA1c 6.5–8.5%, joined to the known 5–20% age defect | SI (union may exceed 20%) | Good or Moderate (still analysed) |
| LEADER, SUSTAIN-6, CANVAS (Limited) | HbA1c ≥7.0% / 7.0–10.5% | SI | Limited (no change) |

- **Where this comes from.** Rater A recorded the decision openly: "HbA1c windows in the diabetes CVOTs ... were treated
  as not population-defining"; BP ranges counted only for LIFE and INSIGHT. That is a defensible EL judgement.
- **Where it breaks.** The adjudicator moved the LIFE and INSIGHT BP bounds out of EL and into SI type 4 ("numeric bounds
  stated in the protocol but missing from the spec"). SI type 4 has no "population-defining" qualifier; its own example is
  an age range. Once that allocation is used, the same text covers the HbA1c windows and the ASCOT BP thresholds.
- **Consequence.** Under one uniform reading, the analysed set loses EMPA-REG, TECOS, CARMELINA and ASCOT-BPLA, and
  possibly ALLHAT: 24–25 trials instead of 29. Under the opposite uniform reading (numeric entry bounds are not scored
  unless population-defining), INSIGHT SI drops to 0 and no tier changes. Either reading is acceptable. Mixing them is
  not.
- **Required.**
  - A user decision (v2.0.1 clarification, applied to all 38 trials).
  - Transcription of the TECOS and CARMELINA baseline SU shares from Table 1.
  - A DC-SI share check for every numeric bound kept.

**B2. Freeze conditions of framework §7.4–7.6 are not met.** The adjudicator states this too.
- 10 analysed trials have a tier-changing provisional score: RE-LY, EAST-AFNET 4, AF-CHF, PROTECT AF, RAFT-AF,
  PARADIGM-HF, ELITE II, VALIANT, PRECISION, PROVE IT-TIMI 22.
- None of DC-ES-cross, DC-EL-met, DC-DA-meas, DC-DA-size or DC-SI-hf-anyposition exists. The bands come from the v1
  criteria check only.
- `clinician_review` is empty in all 38 records.
- §7.4.1 requires each rater's records to be committed or hashed before either rater sees the other's. Neither was done:
  the files are uncommitted and carry no hash, so independence cannot be verified. File times show the A and B files
  were written 2 minutes apart, then adjudication about 20 minutes later.
- Before any analysis of a new set: commit or hash `scores_A.json`, `scores_B.json` and `quality_v2_final.json`; then
  run the data checks; then complete the clinician review.

### SHOULD-FIX

**S1. The C1 resolution and the numeric-bound allocation pull in opposite directions.**
- **Code-defined criteria (C1).** For undocumented code-defined criteria, the adjudicator held that the text does not
  decide, and applied the more-severe default (EL, additive) in 15 trials.
- **Numeric bounds.** For an undocumented numeric bound, the adjudicator held that the text decides, and routed it to SI,
  where it is absorbed when SI is already 2.
- Each call is defensible on its own. Together they make a protocol BP range free in LIFE, which would otherwise reach
  total 8 (Limited), while a code-defined risk criterion costs a point everywhere.
- PRECISION is the one undocumented code-defined criterion left in SI (no tier change).
- **Fix.** Adopt one allocation for all undocumented population criteria, numeric or code-defined (the C1 proposal), and
  re-run it on all 38 trials together with B1.

**S2. ES.b was applied to only one mechanism.**
- ES.b was scored 1 provisional for warfarin→DOAC replacement (ARISTOTLE, ROCKET-AF, RE-LY, FRAIL-AF, AMPLIFY).
- In the hypertension trials, adding the other arm's class within a 4–5-year ITT-like horizon is a specific, well-known
  way of "starting the other arm's strategy" (ALLHAT amlodipine↔thiazide, ASCOT-BPLA, VALUE, LIFE, INSIGHT). No rater
  considered it there.
- ALLHAT and ASCOT-BPLA are one point from Limited.
- **Fix.** Run DC-ES-cross for all 38 trials before freeze, as C7 proposes, not only for the warfarin trials.

**S3. The TZ.c denominator (C2) must be applied to every trial, not only ACTIVE W.**
- Rater B used "actually switched" for ACTIVE W but "on the drug at entry" for TRANSFORM-HF (67%).
- PLATO has the same structure. About 46% were pretreated with clopidogrel, but only the ticagrelor arm switched, so
  "actually switched" would be below 30% and TZ.c would be absent.
- No tier changes:
  - TRANSFORM-HF keeps TZ 2 through TZ.a + TZ.c;
  - PLATO stays Excellent.
  - ACTIVE W stays Limited under either reading once the EL experienced-subgroup anchor is applied to its continuing-OAC
    half: EL becomes 2, and with TS 2 that gives N2 = 2. The adjudicator notes this.
- **Fix.** Decide C2 once and record it for ACTIVE W, TRANSFORM-HF, PLATO, VALIANT and PRECISION.

**S4. VALIANT EL should be at least 1** (no tier change: total 6, Moderate).
- The trial required LV dysfunction and/or clinical or radiological HF.
- The spec excludes only a known EF >40 and does not require an HF code, although an HF code is a usable EHR proxy.
- That is a documented approximation of a population-defining criterion (EL). It is not only a measurement-coverage
  problem (DA.a). ELITE II and AF-CHF, by contrast, require an I50 gate, so DA.a alone is right for them.

**S5. Publication facts that decide scores came from recall or secondary sources and must be transcribed before freeze.**
- VALIANT prior-ACEi share (TZ.c; tier-changing);
- PRECISION risk definition (SI; tier-changing);
- PLATO pretreatment share;
- EMPEROR-Preserved structural-heart-disease criterion: correct to my knowledge, but unverified;
- TECOS and CARMELINA background SU shares (B1);
- ALLHAT, VALUE and ASCOT-BPLA pretreated shares: well above 50% in every source, so not tier-relevant.

**S6. Repository band rule (framework §3.3, §7.6).**
- `quality_v2_final.json` evidence strings contain exact aggregate arm sizes and pooled event counts, for example
  the LEADER, CANVAS and LAAOS III smaller-arm sizes and the pooled events of the v1.7 and v1.8 trials.
- `adjudicate.py` bands only "n = …" patterns.
- None of these counts is 1–10, and all already appear in `docs/v17/candidates.md` and `docs/v18/af_candidates.md`. So
  this is not a CLAUDE.md privacy breach, but it breaks the framework's "bands only" rule.
- **Fix.** Band these strings, for example "smaller arm <500".

**S7. Documentation corrections the adjudication found.** All four are verified.
- TRANSFORM-HF population label "HF hospitalisation (discharge within 30 d)": the gate does not do this.
- CABANA Table 1 note: "disabling stroke omitted" contradicts the code and eTable 1.
- COMET washout: `TRIAL_CRITERIA_CHECK.md` says "deliberately adopted no washout", but the adapted protocol (L23) defers
  the choice.
- RAFT-AF anchor wording on NT-proBNP.

### NOTE

- **N1. Mechanics (check 1).** My code (`recompute_tiers.py`) applies §6 in order: total ≥8, N2 ≥2, PP with (total − CO)
  ≥3, and SI = 2 with an arm-assignment/time-zero defect flagged "unfixable by exclusion"; then the Moderate cap for
  total 5–7 or N2 = 1; then Good and Excellent.
  - Totals, N2, tiers and set membership match the JSON for all 38 trials.
  - Tier counts are 3 / 5 / 21 / 9; the analysed set has 29 trials.
  - The placebo-proxy flag occurs only with CO = 2.
  - `si_reason` "arm_assignment_or_time_zero" occurs only in CABANA, which has the matching defect.
  - Provisional reach matches the JSON under the stated direction rules (EL, TZ, ES and DA can only fall; SI can move
    either way, with a floor of 1 where a known 5–20% defect exists). A symmetric ±1 perturbation adds only combinations
    that those rules exclude.
- **N2. Agreement figures** verified independently:
  - 36 disagreements in 24 trials (344/380 items agree);
  - EL weighted κ 0.311, SI 0.663, ES 0.252;
  - tier weighted κ 0.723, same tier in 30/38;
  - analysed-set differences: ACTIVE W, LIFE, SUSTAIN-6;
  - mean totals 4.74 / 4.26.
- **N3. Direction of adjudication.**
  - Ten disputed items ended at the less severe rater's score. Every case is a score-once move: the deviation was kept in
    the other item. Nine were scored there; in LIFE it was absorbed because SI was already 2.
  - One score lies outside both raters' range: INSIGHT SI 1 provisional, the consequential re-allocation of the BP bound.
    Framework 7.4.3 does not provide for an adjudicator-originated score. It is logged (`agreed_override`) and should be
    on the clinician list.
- **N4. Results.**
  - No item rationale, evidence string or adjudication reason cites an HR, SMD, m58, |Δ log HR|, balance, matched pairs,
    plasmode, R2 or LEGEND.
  - Last-write times are: `quality_v2_final.json` 12:18:02, then `impact.csv` 12:18:16, then `ADJUDICATION.md`. I cannot
    exclude earlier impact runs during development of `adjudicate.py`, which was last modified 12:18:00. This is one more
    reason to hash before analysis (B2).
- **N5. Evidence completeness.** Every non-zero item cites at least one SPEC, CODE, PUB or DATA source. The OU = 1
  cause-specific-death scores cite SPEC and CODE but no PUB; that is acceptable, because the anchor is code-defined.

## Evidence verification (check 2)

21 trials were checked. For each one, every non-zero item and every zero item where a mechanism was considered was
checked against `trial_specs.py` @7fff3d9 (spec key, version, gate, exclusions, arms, OUTCOMES, HORIZON_MONTHS,
PUBLISHED), eTable 1, the data-check bands, the arm-size sources, and the primary publications (from memory unless
marked). "OK" means the score is supported by the cited evidence.

| Trial | Status change | Items checked → verdict |
|---|---|---|
| CABANA | leaves | SI 2, arm assignment: OK. Dedupe at the earliest index with `washout_arms=[1]`; the data check shows a design-level arm-assignment error that exclusion cannot fix. EL 1 (age ≥65 or risk factor; undocumented): OK. TZ.d (documented prior-AAD allowance): OK, but it overlaps the SI mechanism (C5); no tier effect. CO 1, OU 1, FU 1 (49 mo): OK. **Limited is robust.** |
| ACTIVE W | leaves | TS 2: OK (aspirin not identifiable; framework example). TZ 2 provisional: denominator question C2 (S3). EL 1: OK (age ≥75-alone and CAD routes missing from `CHADS_RISK + PAD`). BM 1 (RR): OK. Limited under either C2 reading if the EL experienced-subgroup anchor is applied to the continuing-OAC half. |
| AMPLIFY | leaves | OU 2: OK (framework example). SI 2: OK (persisting codes; the data check finds that the large majority of events disappear under primary-billing coding). They are separate deviations, sensitivity and specificity. EL 1 provisional (C9): no effect. **Limited is robust.** |
| EMPEROR-Preserved | leaves | CO 2 placebo proxy, TS 1 SGLT2 class (`SGLT2_ALL`), OU 1: OK. EL 2 provisional: the T2D restriction is documented (v2 note), and the structural-heart-disease or HF-hospitalisation requirement is in the trial and not in the spec. SI: saxagliptin/alogliptin <5% (data), NP bound unknown. Limited with EL 1 or 2 (other points ≥3). **Robust.** |
| LEADER | leaves | EL 1: OK (spec note documents that the ≥60 risk-factor stratum is not applied; framework example). DA.b: OK (smaller arm <500 in the analysed cohort; criteria_counts denominator agrees). SI 0: OK (washout <5%). OU 1: OK. Limited by PP + 3. |
| SUSTAIN-6 | leaves | EL 1: OK on fact (≥60 stratum not applied; *not* in the spec note, so it rests on C1). SI 1: OK (GLP-1RA washout 5–20%). Limited by PP + 3. Under the C1-literal reading the EL point moves to SI and SI stays 1 (union), so the tier becomes Moderate (the adjudicator lists this). |
| CANVAS Program | leaves | EL 1: OK (ASCVD or ≥2 risk factors not applied; spec `min_age=30`, gate E11 only). DA.b: OK (smaller arm <500). SI 1: OK (other SGLT2i 5–20%). TS 0: OK (canagliflozin tokens). Limited under either C1 reading (other points ≥3). |
| ALLHAT | enters | TZ 2: OK (about 90% treated at entry, replaced at randomisation; ≥50%). CO 1 (thiazide class), OU 1 (CHD death), FU 1 (59 mo), BM 1 (RR), EL 1 (CHD risk factor; C1): OK. **Total 7: see B1 (BP bounds) and S2 (ES.b).** |
| ASCOT-BPLA | enters | TZ 2: OK (most patients previously treated; PROBE). TS 1 (amlodipine-based strategy with perindopril add-on, first component) and CO 1 (cardioselective β-blocker class; bendroflumethiazide add-on): OK, one per arm. OU 1, FU 1 (66 mo), EL 1 (≥3 risk factors): OK. **Total 7: see B1 (uncontrolled-BP entry criterion) and S2.** |
| VALUE | enters | TZ 2: OK (about 90% switched directly). TS 1 (ARB class), CO 0 (amlodipine), OU 1 (composite approximated; emergency procedures not captured; documented), FU 1 (50 mo), EL 1: OK. Total 6. |
| ONTARGET | enters | TZ 1 (TZ.b active run-in; ACEi/ARB withdrawal happened in the run-in, so TZ.c is exempt): OK. TS 1, CO 1, OU 1, FU 1 (56 mo), BM 1 (RR), EL 1 (E11 for diabetes with end-organ damage): OK. Total 7, one point from Limited. |
| LAAOS III | MAJOR → Moderate | SI 2 by share: OK (the gate admits AF first coded in the index surgical stay; well over 50% of the cohort and strongly differential by arm; fixable by exclusion, so not the arm-assignment clause). CO 1, OU 1 (index-stay events; framework examples): OK. EL 0 (CHA2DS2-VASc ≥90% rule by clinical reasoning): acceptable. DA 0: OK (smaller arm just ≥500). See section 6. |
| LIFE | MAJOR → Moderate | SI 2: OK (hedged LVH statements >20%; fixable by exclusion). TS 1, CO 1 (v2 class adaptations, documented in the spec note), OU 1, FU 1 (58 mo), BM 1 (adjusted HR): OK. TZ 0 (placebo washout run-in): OK. EL 0 with the BP bound absorbed in SI: rules-consistent, but see S1 and D2. |
| COMET | MAJOR → Moderate | Code path is the JDAT roster, not the `trial_specs` 'comet' entry: correctly identified. EL 2 (documented "HF code OR EF <40", EF ≤35% not required, NYHA/admission/background not required): OK. SI 1 (prior succinate 5–20%; the adapted protocol defers the washout, so it is undocumented): OK. FU 1 (58 mo): OK. BM 0 (orientation handled in `v13_common.bench`): OK. |
| TRANSFORM-HF | MAJOR → Moderate | TZ 2 (TZ.a + TZ.c, documented in eTable 1): OK. The data check also shows that the arms' index orders sit at very different shares of inpatient stays (a TZ.d-type non-equivalence); it was not scored, but TZ is capped at 2 anyway. EL 1 (documented gate): OK. FU.b (12 vs about 17 mo): OK. SI 0: follows from the documented/undocumented rule (section 6). |
| VALIANT | MAJOR → Moderate | DA.a (EF known <50%) and SI 1 (index-day echo 5–20%): OK. TS 1 and CO 1 (classes): OK. TZ 1 provisional: share unverified (S5). EL 0: should be ≥1 (S4). ARNI leakage not present: OK. |
| EMPA-REG OUTCOME | consistency | CO 2, TS 1 (class arm), OU 1, EL 0 (E11 + CVD gate): OK as scored; HbA1c window unscored (B1). |
| TECOS | consistency | CO 2, OU 1, ES.a (per-protocol benchmark; spec `measure`): OK; unscored deviations (B1). |
| CARMELINA | consistency | EL 1 (documented kidney-risk code proxy), CO 2, OU 1: OK; unscored deviations (B1). DA 0 (smaller arm ≥500): OK. |
| ROCKET-AF, RE-LY, ARISTOTLE | consistency | Experienced-subgroup EL point (about 62% / 50% / 57% VKA-experienced): OK. ROCKET-AF CHADS2 ≥2 not applied and undocumented: OK. RE-LY's narrower risk list makes the ≥90% rule unproven, so EL 2 provisional (C8): acceptable. ES.b 1 provisional: rule text supports it (S2). |

## Consistency across similar trials (check 3)

Adjudicated item scores. "Δ" = unscored deviation of a type scored elsewhere (B1, S2, S4).

**Placebo-proxy diabetes trials** (OU 1 = CV death everywhere; PP rule: other points ≥3 → Limited)

| Trial | EL | TS | CO | OU | FU | ES | DA | SI | Other | Tier | What separates it | Δ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EMPA-REG | 0 | 1 | 2 | 1 | 0 | 0 | 0 | 0 | 2 | Moderate | CVD gate implemented; class arm instead of a washout | HbA1c → SI |
| TECOS | 0 | 0 | 2 | 1 | 0 | 1 | 0 | 0 | 2 | Moderate | CVD gate; ES.a | HbA1c → SI; SU-background ~45% excluded → EL; background therapy → EL |
| CARMELINA | 1 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 2 | Moderate | kidney gate documented (EL 1) | HbA1c → SI; SU background ~32% → EL 2 |
| LEADER | 1 | 0 | 2 | 1 | 0 | 0 | 1 | 0 | 3 | Limited | ≥60 stratum (documented) + DA.b | (HbA1c) |
| SUSTAIN-6 | 1 | 0 | 2 | 1 | 0 | 0 | 0 | 1 | 3 | Limited | ≥60 stratum (C1) + washout 5–20% | (HbA1c) |
| CANVAS | 1 | 0 | 2 | 1 | 0 | 0 | 1 | 1 | 4 | Limited | risk criteria (C1) + DA.b + washout | (HbA1c) |
| REWIND | 1 | 0 | 2 | 1 | 1 | 0 | 0 | 1 | 4 | Limited | risk criteria + FU.a + washout | |
| DECLARE | 1 | 0 | 2 | 1 | 1 | 0 | 0 | 1 | 4 | Limited | risk criteria + FU.a + washout/saxagliptin | |
| EMPEROR-P | 2 | 1 | 2 | 1 | 0 | 0 | 1 | 1 | 6 | Limited | T2D + structural HD; class; DA; SI | |

The answer to "why are EMPA-REG, TECOS and CARMELINA Moderate but LEADER, SUSTAIN-6 and CANVAS Limited?": every item
that is scored is scored consistently. The three Moderate trials implement their risk enrichment, have no washout defect
and have a smaller arm ≥500. But they were never examined for the HbA1c windows and SU-background exclusions that
the same rules score elsewhere. Their "other = 2" status is therefore not established (B1).

**Warfarin-comparator AF and VTE trials**

| Trial | EL | TZ | TS | CO | OU | ES | BM | DA | SI | Total | Tier | Comment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ARISTOTLE | 1 | 0 | 0 | 0 | 0 | 1p | 0 | 0 | 0 | 2 | Excellent | experienced subgroup; ≥90% risk rule |
| ROCKET-AF | 2 | 0 | 0 | 0 | 0 | 1p | 0 | 0 | 0 | 3 | Moderate | + CHADS2 ≥2 (C6 stacking) |
| RE-LY | 2p | 0 | 0 | 0 | 0 | 1p | 1 | 0 | 0 | 4 | Moderate | + narrower risk list (C8) |
| PROTECT AF | 2p | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 5 | Moderate | ES.b n/a (warfarin→DOAC is not the other arm): consistent |
| FRAIL-AF | 1 | 0 | 0 | 0 | 2 | 1p | 0 | 0 | 0 | 4 | Moderate | |
| ACTIVE W | 1 | 2p | 2 | 0 | 1 | 0 | 1 | 0 | 0 | 7 | Limited | ES.b n/a: consistent; robust Limited (S3) |
| AMPLIFY | 1p | 0 | 0 | 0 | 2 | 1p | 1 | 0 | 2 | 7 | Limited | |

Consistent. ES.b is applied exactly where the comparator→intervention replacement is the secular trend. The
experienced-subgroup point is applied in all three new-user DOAC trials.

**Hypertension switch trials** (plus LIFE and INSIGHT, which had washout run-ins)

| Trial | EL | TZ | TS | CO | OU | FU | BM | DA | SI | Total | Tier | Comment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ALLHAT | 1 | 2 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 7 | Moderate | BP bounds unscored (B1); ES.b add-on unassessed (S2) |
| VALUE | 1 | 2 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 6 | Moderate | same Δ |
| ASCOT-BPLA | 1 | 2 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 7 | Moderate | uncontrolled-BP entry unscored (B1); S2 |
| ONTARGET | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 7 | Moderate | TZ.b; switch in the run-in (exempt) |
| LIFE | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 2 | 7 | Moderate | BP range scored in SI, absorbed (S1) |
| INSIGHT | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 1 | 1p | 6 | Moderate | BP threshold scored in SI (adjudicator-originated) |

The TZ, TS, CO, OU and FU scores are consistent. The inconsistency is the BP entry bounds: scored for LIFE and INSIGHT,
not for ASCOT-BPLA, ALLHAT or VALUE.

**ACEi/ARB trials**

| Trial | EL | TZ | TS | CO | OU | DA | SI | Total | Tier | Comment |
|---|---|---|---|---|---|---|---|---|---|---|
| ELITE II | 0 | 0 | 1 | 1 | 0 | 1p | 0 | 3 | Good | ACEi-naive trial, so no TZ.c; I50 gate; ARNI history <5% |
| VALIANT | 0 (should be ≥1, S4) | 1p | 1 | 1 | 0 | 1 | 1 | 5 | Moderate | no HF/LVD gate; index-day echo 5–20% |
| ONTARGET | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 7 | Moderate | |

Class adaptations (TS 1, CO 1) and ARNI handling are consistent. The only gap is VALIANT EL.

**Other checks.**
- FU.a and FU.b were checked against HORIZON_MONTHS for all 38 trials; all consistent.
- BM.a (RR), BM.b, BM.c and BM.d were applied wherever they apply, and non-95% CI levels were not scored, as the rubric
  says.
- The any-position I50 rule (C3) was applied to the HF-prevalent cohorts and not to cohorts that exclude HF at baseline.

## Rule adherence (check 4)

- **Rubric text or default.** Each of the 36 adjudications records a deciding clause. "Text decides" is a fair reading
  for COMET SI, PARADIGM-HF, LIFE and INSIGHT EL, TRANSFORM-HF and DA (EMPEROR-Preserved). The C1–C10 defaults use the
  more severe score, as 7.4.3 requires. The exception is the asymmetry in S1. Each C1 instance taken alone, and the
  numeric-bound allocation taken alone, follows its stated rule. Together they act in opposite directions.
- **Results never used.** Verified in the text (N4). Results-order cannot be verified without hashes (B2).
- **Score once.** No double counting changes a tier. CABANA TZ.d + SI (C5) is a partial overlap with no effect, because
  SI 2 alone gives Limited. AMPLIFY OU 2 + SI 2 counts two distinct deviations, as the rubric text says. EMPEROR-Preserved
  EL (T2D) and CO (proxy) are a population change and a comparator change; this is consistent with the DAPA-HF
  calibration by both raters.
- **Provisional rules as written.**
  - Unknown share → SI 1 provisional: applied correctly.
  - TZ is never escalated on an unknown share: applied correctly.
  - DA 1 provisional only for EF-defined trials: applied correctly.
  - The arm-assignment/time-zero → SI 2 provisional rule never needed to be applied; CABANA's share is known.
- **Framework 7.1 / 7.5.** Raters and adjudicator are runs of one LLM. The report says so, and κ is labelled as LLM
  agreement. The clinician review is pending (B2).

## Impact gate (check 5)

I recomputed the results with my own code (`impact_check.py`). It reads `restricted_cells.parquet` and selects P1 /
main / base k = 0 vs ECG k = 32. It takes |SMD| over the 58 items, masked to the items observed in both arms, and
computes m58 and the share below 0.1. The relative reduction is 1 − mean(ECG)/mean(base), with 4,000 trial bootstrap
resamples and seed 20261001. P-values use an exact one-sided sign-flip test (my own meet-in-the-middle enumeration). The
code does not import `sens_primary32` or `adjudicate.py`.

| Set | Rel. reduction (95% CI) | m58 | % <0.1; better; P | \|Δ log HR\|; closer; P | Matches `impact.csv` / ADJUDICATION §9 |
|---|---|---|---|---|---|
| (a) published 32 | 11.41% (6.31–15.98) | 0.142 → 0.126 | 49.8 → 55.0; 22/32; .0020 | 0.251 → 0.205; 20/32; .0084 | **yes: gate passes** |
| (b) v2.0 29 | 11.37% (5.73–16.12) | 0.128 → 0.113 | 54.4 → 59.9; 21/29; .0013 | 0.228 → 0.178; 20/29; .0047 | yes |
| (c) Excellent + Good, 8 | 7.21% (2.34–13.17) | 0.114 → 0.106 | 57.5 → 61.4; 6/8; .0625 | 0.207 → 0.129; 7/8; .0234 | yes |
| (d) all 38 | 12.61% (7.85–16.63) | 0.138 → 0.120 | 51.4 → 57.2; 28/38; .0002 | 0.258 → 0.207; 25/38; .0021 | yes |

The benchmark-permutation P was not re-implemented; its values are taken from `impact.csv`.

I deliberately did **not** compute results for the alternative sets implied by B1 or section 6. Any rule change has to
be decided on design grounds before its results are seen (framework §1.1, §7.6).

## Framework-design issues (check 6)

| Issue (adjudicator's D-list) | Real problem? | Consequence for the analysed set | Minimal rule change (not applied) |
|---|---|---|---|
| **D1a. SI = 2 by share caps only at Moderate** (LAAOS III, LIFE) | **Yes.** In LAAOS III the defect affects a majority of the cohort and is strongly differential by arm; in LIFE it affects over 20%. Both are exclusion-fixable, and the data check already has fix cells. | LAAOS III and LIFE stay in the primary set with known, fixable eligibility errors. | Prefer **"rebuild before freeze"**: apply the exclusion-type fixes as new spec versions (LAAOS III AF before admission; LIFE definite-LVH; also CAROLINA age, GLP-1RA/SGLT2i washouts, COMET succinate) and re-score; their SI points then disappear. Alternative rule: "SI = 2 with share >50% or differential by arm → Limited until rebuilt". |
| **D1b. A documented design-level time-zero error caps at Moderate** (TRANSFORM-HF) | **Yes.** The same error undocumented would be SI 2 arm/time-zero → Limited. Documentation written after results (eTable 1 notes) can turn a defect into an "adaptation". | TRANSFORM-HF stays in. | Extend rule 1's last clause: "TZ = 2 including TZ.a or TZ.d confirmed by a data check as differential between arms → Limited until rebuilt". Also: only documentation dated at or before the spec version counts as a "documented adaptation" for §1.4. |
| **D1c. COMET: a documented population change of MAJOR size → EL 2 → Moderate** | Partly. It is the user's explicit, dated adaptation (2026-09-21), and EL 2 is meant to cap at Moderate. | COMET stays. | None needed if the user confirms. Otherwise make EF ≤35% (unknown passes) the primary COMET spec, as the data check proposes. |
| **D1d. VALIANT: unknown-passes coverage capped at DA 1** | Partly. Half of it is S4 (a missing EL point). The rest is DA's design maximum. | VALIANT stays (total 5–6). | Score EL for the missing HF/LVD gate (S4). Or rebuild requiring EF ≤40 or HF. |
| **D2. Score-once makes some deviations free** (SI saturates at 2) | **Yes, but narrow.** It changes a tier only for LIFE (BP bound absorbed at total 7). | LIFE stays in. | "SI = 2 by share plus a second independent undocumented defect (≥5% or unknown) → Limited until rebuilt". Or resolve S1 (one allocation for all population criteria). |
| **D3. Hypertension switch trials re-enter** (ALLHAT, ASCOT-BPLA, VALUE; ONTARGET via TZ.b) | **A pending user decision, not an error.** §11.3 says this outcome is intended. But L8 (Heyard 2024: discontinuation at randomisation is the strongest source of divergence) argues for a combination rule parallel to the placebo-proxy rule. Both change the estimand. | +3 trials versus v19 (ONTARGET is a separate case). | "TZ.c ≥50% and (total − TZ) ≥3 → Limited" (ALLHAT, ASCOT-BPLA, VALUE → Limited; TRANSFORM-HF, with other points = 2, unchanged). Or the adjudicator's "TZ.c ≥50% + FU.a → Limited" (same three trials). |
| **D4. The placebo-proxy line turns on single points** | **Yes, and it is the reason B1 matters.** | EMPA-REG, TECOS and CARMELINA are each one point from Limited. | No rule change. Apply B1 uniformly. Option §11.5 (SU proxy as a second poor item) would also make TECOS and CARMELINA Limited. |
| **Documented vs undocumented asymmetry** (§1.4) | **Yes**, in two directions. (i) Documentation shields design-level errors (D1b). (ii) Undocumented criteria can cost fewer points than documented ones (SUSTAIN-6 vs LEADER under the literal reading; the C1 default currently prevents this). | SUSTAIN-6's tier depends on C1. TRANSFORM-HF's tier depends on documentation. | Score every population criterion in its domain item whether or not it is documented, and add an SI flag (not points) when it is undocumented. Count only pre-results documentation (D1b). |

## Privacy (check 7)

- `ADJUDICATION.md` and `quality_v2_final.json` contain no counts of 1–10 next to a count word, no "n = …" fields, no
  sub-1% shares, no patient-level rows and no identifiers.
- The JSON contains exact aggregate arm sizes and event counts, all well above 10 (S6: framework band rule, not
  CLAUDE.md).
- This audit document reports bands, publication percentages and trial counts only.

## Recommended decisions for the user

1. **Numeric entry bounds (B1, S1).** Decide whether undocumented protocol numeric entry bounds (BP, HbA1c,
   natriuretic peptide, cholesterol caps) are scored, and in which item. Apply the decision to all 38 trials as
   v2.0.1. Under the current "SI type 4" reading, EMPA-REG, TECOS, CARMELINA and ASCOT-BPLA (and possibly ALLHAT) become
   Limited.
2. **Proxy-forced population restrictions and experienced subgroups (B1).** Confirm that the experienced-subgroup EL
   anchor and proxy-forced population restrictions apply to the SU-proxy trials (TECOS and CARMELINA background SU),
   after transcribing their Table 1 shares.
3. **D3 (hypertension switch trials).** Keep Moderate as §11.3 intends, or adopt "TZ.c ≥50% with ≥3 other points →
   Limited".
4. **D1 (MAJOR trials ending at Moderate).** Rebuild the exclusion-fixable MAJOR and MODERATE defects (LAAOS III, LIFE,
   CAROLINA, washouts, COMET succinate) as new spec versions before freeze. Decide whether TRANSFORM-HF's documented
   time-zero error triggers Limited (D1b).
5. **C1, C2, C6–C9.** Decide each once, for all trials (S1, S3).
6. **Before any analysis of a new set:**
   - hash or commit the rater and adjudicated files;
   - run DC-ES-cross (all 38 trials), DC-EL-met, DC-DA-meas, DC-DA-size and DC-SI-hf-anyposition;
   - transcribe the S5 publication facts;
   - complete the clinician review.

   Then recompute tiers, freeze under a dated tag, and only then run the impact analysis on the frozen set.
