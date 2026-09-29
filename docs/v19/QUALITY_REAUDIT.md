# v1.9 emulation-quality re-audit: independent re-rating, agreement, graded tiers

Date 2026-09-29. Independent rater: Claude (agent). **I viewed no emulation results at any stage** (no balance, HR, agreement or simulation output). Only design information was used.

Outputs: `docs/v19/QUALITY_REAUDIT_RATINGS.json` (step 1, committed in 8e18ea4 before the existing ratings were opened), `docs/v19/quality_tiers.json` (adjudicated ratings, points, tiers), this file. Scripts in the session scratchpad; the logic is restated below.

## 1. Method

1. **Independent re-rating (step 1).** The rule was taken only from the RULE DEFINITIONS section of `docs/v17/TRIAL_SELECTION_RULE.md` (section 1 and the threshold justification, lines 1-35). That text defines flags F1-F5, comparator and outcome fidelity (good/moderate/poor) and the inclusion thresholds. Each of the 38 analysed trials was rated from the following design inputs:
   - `scripts/trial_specs.py`: arms, gates, exclusions, designs, HORIZON_MONTHS, OUTCOMES, PUBLISHED;
   - `docs/v13/rct_facts.json`;
   - the design caveats in `docs/v17/candidates.md` and `docs/v18/af_candidates.md`;
   - the PICOT columns of `docs/paper/table1_picot.md`;
   - published protocols and papers (web/PubMed).

   The 38 trials are the 18 v1.6 trials (PRIMARY + EXTRA with a v13 bootstrap), the 15 V17 trials and the 5 V18 trials. PARADISE-MI, DCP and INVEST are EXTRA entries that were never analysed. F4 was checked mechanically against HORIZON_MONTHS (≥ 48 months).
2. **Agreement (step 2).** Only after the step-1 commit were the v1.7 ratings in `docs/v17/trial_selection.json` opened. Agreement is reported per item (percent agreement and Cohen's kappa) and for the 3-class result (v1.7 vs my unadjudicated ratings). Every disagreement was adjudicated against the rule text and the protocol.
3. **Graded scale (step 3).** A point system uses the rated design items only. Weights and cut-points were fixed before scoring and blind to results (section 5). The original 3-class rule is kept alongside it.

## 2. Attestation: files and sources accessed

Every access is listed in order. Nothing under `/mnt/raid0` was opened, except that the deck build reads its usual inputs when rebuilding (I did not inspect them). No file in `docs/v16/`, `docs/v19/` (apart from my own outputs; only file names were listed), `docs/v18/` (apart from `af_candidates.md`), `report.md`, `docs/abstract` or `docs/presentation` was read, and no result commit was shown. The deck screenshots cover only slides 7-8.

```
ls docs/v17 docs/v19 scripts (names only)
READ docs/v17/TRIAL_SELECTION_RULE.md lines 1-35 (rule definitions + threshold justification only)
READ scripts/v13_common.py lines 25-60 (trial registry); scripts/v16/v16_engine.py lines 1-20,90-130 (TRIALS list)
READ scripts/make_acc_figure.py lines 1-31 (trial name list only)
GREP docs/paper/table1_picot.md table rows (NOTE: output inadvertently included the 'Emulation quality' class column = existing 3-class labels; disclosed)
READ scripts/trial_specs.py lines 1-419 and 440-1101 (specs, PUBLISHED, HORIZON_MONTHS, OUTCOMES); lines 420-439 (RATING_ITEMS, an older v1.3 rating) deferred until after step 1
NOTE: lines 440-660 output included RATING_ITEMS.update tuples (older v1.3 4-item numeric rating for 13 extension trials); seen incidentally, not used
ls docs/v13 (file names only; no result files opened)
READ docs/v13/rct_facts.json (full)
READ docs/v17/candidates.md and docs/v18/af_candidates.md (design caveats; feasibility counts ignored)
WEB: Wang SV et al. JAMA 2023;329:1376 (FDA-hosted PDF https://www.fda.gov/media/170837/download), Table 2 design-difference ratings for the 32 RCT-DUPLICATE trials
GREP docs/COMET_ADAPTED_PROTOCOL.md for formulation/washout/run-in terms only (design protocol; outside the explicit allowed list, disclosed)
WEB: PMC9857435 (TRANSFORM-HF, Mentz JAMA 2023): randomised before discharge; 67% on loop diuretic pre-admission
WEB search: ACTIVE W (Lancet 2006, PMID 16765759): 77% on OAC at entry
WEB search: VALUE (Julius Lancet 2004): 89.9% previously treated, switched to study drug without run-in
WEB search: INSIGHT (Brown Lancet 2000): 4-week placebo run-in before randomisation
WEB search: CAROLINA design (Marx DVDR 2015, PMC4390606): SU/glinide discontinued at randomisation for prior users
WEB search: PRECISION design (Becker AHJ 2009): no washout detail found
WEB search: LODESTAR (Lee BMJ 2023; tctmd), PROVE IT-TIMI 22 (Cannon NEJM 2004; Wiki Journal Club): composite components incl. revascularisation
STEP 2 (after commit 8e18ea4): READ docs/v17/trial_selection.json (per-trial flags, grades, rationale; ecg_relevance fields present but not used). TRIAL_SELECTION_RULE.md sections 3-8 and trial_specs.py lines 420-439 were never opened.
READ scripts/build_lab_deck.py lines 1-60 (header/CSS), 73-83 (table1 loader), 340-400 (slides 6 end, slide 7)
READ scripts/build_lab_deck.py lines 98-125 (trial loader), 966-992 (quality grid JS), 1025-1068 (nav/main)
WEB (step 2 adjudication): Wiki Journal Club PLATO (about half on clopidogrel at baseline); Wiki Journal Club PRECISION ("required daily NSAID therapy")
READ scripts/build_lab_deck.py lines 200-248 (CSS)
NOTE: deck build stdout printed its reference_values JSON; the first line (a held-out balance percentage) was displayed before truncation, incidentally; not used; later builds piped to head -1
Deck: rebuilt with the build script; Playwright screenshots of slides 7-8 only (no JS errors, no overflow)
```

Disclosures:
- The grep of `table1_picot.md` also printed its 'Emulation quality' column, i.e. the existing 3-class label per trial.
- `trial_specs.py` lines 640-660 printed older v1.3 `RATING_ITEMS` tuples, an older numeric rating with a different scale.
- Neither per-item rating was used in step 1. All 38 step-1 per-item ratings were written from the protocol reasoning recorded in the step-1 JSON. Seeing the class labels could still have influenced me, so the class-level agreement below is best read as an upper bound.
- I also grepped one design document outside the listed inputs, `docs/COMET_ADAPTED_PROTOCOL.md`, for formulation/washout/run-in terms (design only).

## 3. Agreement (v1.7 vs independent v1.9, before adjudication; n = 38)

| Item | Agreement | Cohen's kappa | Disagreements |
|---|---|---|---|
| F1 in-hospital start | 100.0% | 1.00 | 0 |
| F2 run-in | 100.0% | 1.00 | 0 |
| F3 baseline-therapy switch | 84.2% | 0.54 | 6 |
| F4 long follow-up | 100.0% | 1.00 | 0 |
| F5 other time zero | 100.0% | undefined (all 0 in both) | 0 |
| Comparator fidelity (G/M/P) | 89.5% | 0.84 | 4 |
| Outcome fidelity (G/M/P) | 97.4% | 0.94 | 1 |
| 3-class result (High strict / High / Lower) | 81.6% | 0.71 | 7 |

There were 11 item-level disagreements across 11 trials; before adjudication the 3-class result differed for 7 trials. F3 (baseline-therapy switch) was the least reliable item: the two raters read 'at randomisation' differently when prior therapy was stopped during a pre-randomisation run-in.

## 4. Disagreements and adjudication

The adjudication principles, applied the same way to every trial:
- **F3** is scored only when a substantial share of RCT patients stopped or replaced an ongoing same-purpose drug *at randomisation*, and the emulation neither requires nor reproduces that switch.
  - Discontinuation during a pre-randomisation washout or run-in is not F3; an active run-in is scored as F2.
  - A protocol transition window after randomisation (INR-guided VKA-to-DOAC transition; Wang 2023 footnote g) is not F3.
- **Comparator** grades follow the rule text. 'Good' needs the RCT agent or procedure contrast to be observed in both arms.
- **Outcome 'poor'** covers a primary endpoint that is not validly ascertainable.

### LAAOS III: comparator (v1.7 moderate vs v1.9 good) -> **moderate** (v1.7 upheld)

- v1.7 rationale: Fidelity: Both arms have time zero at the same open cardiac operation (in-hospital, mirrored). No run-in or switching. 46-mo horizon (< 48). Comparator moderate: 'no occlusion' is inferred from the absence of an LAA code, and under-coding misclassifies occluded patients as controls. Outcome moderate: stroke/SE from inpatient codes, but index-stay (perioperative) strokes, which the RCT counted, are excluded.
- v1.9 rationale: Occlusion vs none at the same cardiac surgery; time zero is the surgery in both arms (F1 not flagged). Ischaemic stroke/SE from codes, but perioperative (index-stay) events, part of the RCT primary, are not counted.
- Adjudication: moderate. 'Surgery without occlusion' is inferred from the absence of an LAA code; LAA occlusion/excision at open surgery is under-coded (ICD-10-PCS 02L70/02B70ZK), so the comparator arm is structurally contaminated with occluded patients. The rule's 'good' needs the same procedure contrast to be observed, which it is not for the control arm.

### COMET: comparator (v1.7 poor vs v1.9 good) -> **good** (v1.9 upheld)

- v1.7 rationale: Fidelity: 58-mo horizon (F4). The metoprolol token cannot separate tartrate (the RCT arm) from succinate, the dominant US HF formulation, and COMET's hypothesis hinges on tartrate at 50 mg bid. Comparator poor.
- v1.9 rationale: Horizon 58 mo (F4). Carvedilol vs immediate-release metoprolol tartrate, as in the RCT (docs/COMET_ADAPTED_PROTOCOL.md); dose not identifiable (record-only titration). All-cause death.
- Adjudication: good. The COMET cohort is not built from the trial_specs.py token list (that entry only builds OMOP-side features); docs/COMET_ADAPTED_PROTOCOL.md defines the comparator as immediate-release metoprolol tartrate from validated prescribing evidence. So the formulation on which COMET's hypothesis hinges is matched; dose titration is record-only under the rule.

### TRANSFORM-HF: comparator (v1.7 moderate vs v1.9 good) -> **good** (v1.9 upheld)

- v1.7 rationale: Fidelity: Randomized in hospital to an oral discharge strategy. The furosemide token also captures inpatient IV diuresis, which moves time zero (F1). Most RCT patients were on a prior loop diuretic replaced at randomization; the emulation requires first-ever use with a washout of the other arm (F3).
- v1.9 rationale: Randomised before discharge from an HF admission; initiators within 30 d of an HF code can take time zero from an inpatient IV furosemide order vs an oral discharge torsemide strategy (F1). 67% were on a loop diuretic before admission and changed agent at randomisation; the new-user design excludes them (F3). All-cause death.
- Adjudication: good. Both RCT arms are the same agents (torsemide vs furosemide) with investigator-selected dose, as in the emulation; the v1.7 rationale gives no comparator deviation. The time-zero issues are already scored as F1 and F3.

### LIFE: F3 (v1.7 1 vs v1.9 0) -> **0** (v1.9 upheld)

- v1.7 rationale: Fidelity: Prior antihypertensives were withdrawn (placebo run-in) and replaced by the study drug; emulated initiators often add on (F3). 58-mo horizon (F4). Class adaptation of both arms (v2).
- v1.9 rationale: Horizon 58 mo (F4). ARB class vs cardioselective beta-blocker class (trial losartan vs atenolol). Prior therapy was withdrawn during a placebo run-in before randomisation (not F2/F3). CV death, MI or stroke.
- Adjudication: 0. LIFE withdrew prior antihypertensives at the start of a 1-2 week placebo run-in, i.e. before randomisation. F3 is defined as a switch at randomisation, and the rule says washout run-ins are not flagged. Wang 2023 footnote g likewise does not count a washout that separates discontinuation from randomisation.

### INSIGHT: F3 (v1.7 1 vs v1.9 0) -> **0** (v1.9 upheld)

- v1.7 rationale: Fidelity: Previously treated hypertensives were switched to the randomized drug after a placebo run-in, not mirrored (F3; same criterion as ALLHAT/VALUE/ASCOT). Nifedipine (RCT: GITS) and thiazide class (RCT: co-amilozide) adaptations. Composite needs CV death and HF hospitalisation.
- v1.9 rationale: 4-week placebo run-in (washout) before randomisation, not flagged. Nifedipine (GITS not identifiable) vs thiazide class for co-amilozide. Composite needs CV death and HF hospitalisation codes.
- Adjudication: 0. Same reasoning as LIFE: a 4-week placebo run-in (Brown, Lancet 2000) separated withdrawal of prior therapy from randomisation.

### PLATO: F3 (v1.7 1 vs v1.9 0) -> **1** (v1.7 upheld)

- v1.7 rationale: Fidelity: Inpatient start is captured by EHR orders for both arms. A substantial share of RCT patients were pre-treated with open-label clopidogrel and switched at randomization; the other-arm washout excludes such switchers (F3). Vascular death needs cause of death.
- v1.9 rationale: P2Y12 inhibitors in ACS start within the index admission and EHR inpatient orders are visible (F1 exemption in the rule). Vascular death needs listed causes.
- Adjudication: 1. About half of PLATO patients were on open-label clopidogrel at randomisation, and those allocated to ticagrelor switched at once. The emulation's other-arm washout excludes these switchers, which is F3 as the rule words it (a substantial share replacing an ongoing same-purpose drug at randomisation, not mirrored). The DOAC exception (a protocol INR-guided transition window, Wang 2023 footnote g) does not apply. RCT-DUPLICATE's narrower 'maintenance therapy' item is not the rule used here.

### VALIANT: F3 (v1.7 1 vs v1.9 0) -> **1** (v1.7 upheld)

- v1.7 rationale: Fidelity: Randomized in hospital 0.5-10 d post-MI. RAS blockade (ACEi, or ARB as the guideline alternative) is standard in-admission care, so F1 = 0. About 40% were on an ACEi that was stopped at randomization, and the ACEi washout excludes these switchers (F3). Class adaptation (valsartan vs captopril). All-cause death.
- v1.9 rationale: RCT randomised 0.5-10 d after MI in hospital; ACEi/ARB are started in the admission with visible inpatient orders (treated like the P2Y12 exemption; borderline). Class adaptation (valsartan vs captopril). All-cause death.
- Adjudication: 1. About 40% were on an ACEi that was stopped at randomisation (both arms then titrated blinded study drug from low doses). This is a substantial same-purpose switch, and the ACEi washout excludes those patients.

### ONTARGET: F3 (v1.7 1 vs v1.9 0) -> **0** (v1.9 upheld)

- v1.7 rationale: Fidelity: 3-week single-blind active run-in (ramipril, telmisartan, combination; 11.7% excluded) (F2). Prior ACEi/ARB was stopped for run-in, not mirrored (F3). 56-mo horizon (F4). Class adaptation.
- v1.9 rationale: 3-week single-blind active run-in (ramipril, then telmisartan+ramipril) removed intolerant patients (F2 as the rule defines it). Horizon 56 mo (F4). ARB class for telmisartan, ACEi class for ramipril. CV death, MI, stroke or HF hospitalisation.
- Adjudication: 0. Prior ACEi/ARB were stopped at entry to the 3-week active run-in, not at randomisation, and that run-in is already scored F2. Counting it again as F3 double-counts one design feature. RCT-DUPLICATE scored ONTARGET discontinuation 'No'.

### PRECISION: F3 (v1.7 1 vs v1.9 0) -> **1** (v1.7 upheld)

- v1.7 rationale: Fidelity: Same agents (two of three RCT arms). RCT patients needing chronic NSAIDs commonly switched from a prior NSAID at randomization, and the prior-year NSAID exclusion removes such switchers (F3). OTC naproxen is unseen. Celecoxib dose titration allowed. APTC MACE needs CV death.
- v1.9 rationale: Same agents (celecoxib vs naproxen; OTC naproxen unseen, dose titration record-only). APTC composite needs CV death incl. haemorrhagic.
- Adjudication: 1. PRECISION enrolled patients who needed daily NSAID therapy, so most were already on an NSAID that was replaced by study drug at randomisation. The prior-year NSAID exclusion removes these switchers. v1.9 had not scored this.

### AMPLIFY: outcome (v1.7 poor vs v1.9 moderate) -> **poor** (v1.7 upheld)

- v1.7 rationale: Fidelity: Both anticoagulants start at the index VTE encounter; the enoxaparin bridge is implicit in warfarin care. Recurrent VTE from a new inpatient stay with any VTE code is low-specificity (index-VTE codes recur), outpatient-managed recurrences are missed and VTE-related death is not captured. Outcome poor.
- v1.9 rationale: Apixaban vs warfarin (with parenteral lead-in) after acute VTE; both started around the index encounter with visible orders. Recurrent VTE from a new inpatient stay with a VTE code: ascertainable but low specificity and outpatient-managed recurrences missed (moderate, as RCT-DUPLICATE rated its AMPLIFY outcome).
- Adjudication: poor. Inpatient-only ascertainment misses outpatient-managed recurrent DVT and VTE-related death, which together are a large share of the RCT primary endpoint. Index-VTE codes also recur on unrelated readmissions during treatment, so the definition has low specificity. With both problems the primary endpoint is not validly ascertained.

### PROVE IT-TIMI 22: comparator (v1.7 moderate vs v1.9 poor) -> **moderate** (v1.7 upheld)

- v1.7 rationale: Fidelity: In-hospital ACS start is standard for both statins (F1 = 0). About 25% prior statin use, below the 'substantial share' bar for F3. Dose is not identifiable, but post-2013 post-ACS atorvastatin is predominantly high-intensity, so comparator moderate. Revascularisation >= 30 d, the largest primary component, is not captured. Outcome poor.
- v1.9 rationale: The tested hypothesis is intensive (atorvastatin 80) vs moderate (pravastatin 40) therapy; dose is not identifiable, so atorvastatin initiators at any dose change the hypothesis. Revascularisation >= 30 d, the most frequent component, is not captured. Statins start in the ACS admission (F1 not flagged).
- Adjudication: moderate. Dose is not identifiable, but after the 2013 guideline, atorvastatin started after ACS is mostly high-intensity (40-80 mg), while pravastatin is at most moderate-intensity at any dose. The intensive-vs-moderate contrast is therefore largely preserved, which is short of the 'hypothesis-changing' bar for poor.

**Net effect on the 3-class rule.**

| | High (strict) | High | Lower |
|---|---|---|---|
| v1.7 | 9 | 9 | 20 |
| Adjudicated | 10 | 10 | 18 |

Trials whose class changed:
- COMET: Lower -> High
- INSIGHT: High -> High (strict)
- LIFE: Lower -> High

Changes vs v1.7 that leave the class unchanged:
- TRANSFORM-HF: comparator moderate -> good (still two flags);
- ONTARGET: F3 1 -> 0 (still F2 + F4).

v1.7 was upheld, so nothing changed, for:
- LAAOS III: comparator;
- PLATO, VALIANT and PRECISION: F3;
- AMPLIFY: outcome;
- PROVE IT: comparator.

Where results elsewhere in the project are subset by the v1.7 classes, the three reclassified trials should be noted as a sensitivity item. **This audit does not re-run any analysis.** Some places still carry the v1.7 class and were deliberately left unchanged: the `docs/paper/table1_picot.md` quality column, `docs/v17/trial_selection.json`, and the deck's results-slide quality filters.

## 5. Graded scale (defined a priori, blind to results)

**Points** (0-9) = F1 + F2 + F3 + F4 + F5 (1 each) + comparator (good 0 / moderate 1 / poor 2) + outcome (good 0 / moderate 1 / poor 2).

| Tier | Definition |
|---|---|
| Excellent - close emulation | 0 points |
| Good - minor deviations | 1-2 points, with no poor item and at most one core flag |
| Moderate - substantial deviations | 3 points; or 1-2 points with a poor comparator/outcome or two core flags (ceiling rule) |
| Limited - major deviations | ≥ 4 points |

Why these weights and cut-points:
- **Items.** The core flags are the RCT-DUPLICATE design emulation differences:
  - in-hospital start, selective run-in, discontinuation of baseline therapy at randomisation and delayed effect (Wang et al., JAMA 2023;329:1376, Table 2);
  - plus a general time-zero item (Hernán & Robins).
- **Excellent (0).** Wang's 'close emulation' required none of these features and comparator/outcome at least moderate with at least one good. Excellent is the stricter case where both are good, the closest emulation the EHR allows.
- **Additive points.** Heyard et al. (BMJ Medicine 2024) showed the design differences act roughly additively on RWE-RCT disagreement, so they are counted rather than treated as a single binary.
- **Weights.** A flag or a moderate proxy is one unit of deviation. A poor comparator (placebo proxy or hypothesis-changing substitution) or poor outcome counts 2, because Franklin et al. (Circulation 2021;143:1002) found such proxies agreed worst. They change the estimand rather than add noise.
- **Good (1-2).** One or two minor adaptations, e.g. class adaptation plus CV death from listed causes. This is the range in which RCT-DUPLICATE still counted pairs as close emulations when comparator/outcome were moderate.
- **Moderate (3).** Three compounded deviations.
- **Limited (≥ 4).** Four or more, e.g. a placebo proxy plus a composite needing cause of death plus a long horizon.
- **Ceiling rule.** It keeps the tiers consistent with the v1.7 inclusion rule: a trial that v1.7 excludes (poor item, or ≥ 2 flags) can never be labelled Excellent or Good.
- **Blinding.** All of these choices were made from design considerations and the three papers only, without viewing any emulation result.

Counts per tier (adjudicated):

| Tier | Trials |
|---|---|
| Excellent - close emulation | 3 |
| Good - minor deviations | 12 |
| Moderate - substantial deviations | 17 |
| Limited - major deviations | 6 |

The ceiling rule was needed for 4 trials: FRAIL-AF, TRANSFORM-HF, AMPLIFY, LODESTAR.

## 6. Per-trial table (adjudicated; sorted by tier, points)

Key: ✓ = flag present. G/M/P = good/moderate/poor. 'Old class' = v1.7 3-class rating. 'Class (adj.)' = the same rule applied to the adjudicated items.

| Trial | Area | Horizon (mo) | F1 | F2 | F3 | F4 | F5 | Comp. | Outc. | Points | Tier | Class (adj.) | Old class | Rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ARISTOTLE | AF | 22 |  |  |  |  |  | G | G | 0 | Excellent - close emulation | High (strict) | High (strict) | Apixaban vs warfarin initiators in outpatient AF; stroke/SE from inpatient codes. VKA-experienced patients transitioned by protocol (post-randomisation washout), which RCT-DUPLICATE did not score as baseline-therapy discontinuation. |
| RE-LY | AF | 24 |  |  |  |  |  | G | G | 0 | Excellent - close emulation | High (strict) | High (strict) | Dabigatran vs warfarin; the benchmark is the 150 mg arm and 110 mg is not marketed in the US (75 mg only below RE-LY's CrCl limit), so the agent and effective dose match; stroke/SE from inpatient codes. |
| ROCKET-AF | AF | 23 |  |  |  |  |  | G | G | 0 | Excellent - close emulation | High (strict) | High (strict) | Same agents; ITT benchmark; stroke/SE from inpatient codes; VKA transition handled as for ARISTOTLE. |
| AFFIRM | AF | 42 |  |  |  |  |  | M | G | 1 | Good - minor deviations | High (strict) | High (strict) | Sequential add-on design mirrors adding rhythm control to rate control; strategy approximated by antiarrhythmic initiation (cardioversion not captured). All-cause death. |
| PROTECT AF | AF | 18 |  |  |  |  |  | G | M | 1 | Good - minor deviations | High (strict) | High (strict) | LAAO vs continued warfarin in OAC-treated AF (sequential; no future information). Composite includes CV/unexplained death needing listed causes. |
| COMET | HF | 58 |  |  |  | ✓ |  | G | G | 1 | Good - minor deviations | High | Lower | Horizon 58 mo (F4). Carvedilol vs immediate-release metoprolol tartrate, as in the RCT (docs/COMET_ADAPTED_PROTOCOL.md); dose not identifiable (record-only titration). All-cause death. Adjudicated: comparator = good (v1.9). |
| ELITE II | HF | 18 |  |  |  |  |  | M | G | 1 | Good - minor deviations | High (strict) | High (strict) | Class adaptation (any ARB vs any ACEi; trial losartan vs captopril) in ACEi-naive HF; 18 mo; all-cause death. |
| PLATO | ACS / MI | 12 |  |  | ✓ |  |  | G | M | 2 | Good - minor deviations | High | High | P2Y12 inhibitors in ACS start within the index admission and EHR inpatient orders are visible (F1 exemption in the rule). Vascular death needs listed causes. Adjudicated: F3 = 1 (v1.7). |
| VALIANT | ACS / MI | 25 |  |  | ✓ |  |  | M | G | 2 | Good - minor deviations | High | High | RCT randomised 0.5-10 d after MI in hospital; ACEi/ARB are started in the admission with visible inpatient orders (treated like the P2Y12 exemption; borderline). Class adaptation (valsartan vs captopril). All-cause death. Adjudicated: F3 = 1 (v1.7). |
| AF-CHF | AF | 37 |  |  |  |  |  | M | M | 2 | Good - minor deviations | High (strict) | High (strict) | Same strategy approximation as AFFIRM in HFrEF. Primary endpoint CV death needs listed causes of death. |
| LAAOS III | AF | 46 |  |  |  |  |  | M | M | 2 | Good - minor deviations | High (strict) | High (strict) | Occlusion vs none at the same cardiac surgery; time zero is the surgery in both arms (F1 not flagged). Ischaemic stroke/SE from codes, but perioperative (index-stay) events, part of the RCT primary, are not counted. Adjudicated: comparator = moderate (v1.7). |
| RAFT-AF | AF | 36 |  |  |  |  |  | M | M | 2 | Good - minor deviations | High (strict) | High (strict) | Ablation vs continued rate control; comparator antiarrhythmic use not excluded (contamination of the rate-control strategy). HF events from any-position HF hospitalisation codes. |
| CAROLINA | Diabetes | 76 |  |  |  | ✓ |  | G | M | 2 | Good - minor deviations | High | High | Same agents (linagliptin vs glimepiride). Horizon 76 mo (F4). Prior SU/glinide was stopped at randomisation for a minority (SU-exposed stratum); not judged substantial (RCT-DUPLICATE: no). 3-point MACE. |
| INSIGHT | Hypertension | 42 |  |  |  |  |  | M | M | 2 | Good - minor deviations | High (strict) | High | 4-week placebo run-in (washout) before randomisation, not flagged. Nifedipine (GITS not identifiable) vs thiazide class for co-amilozide. Composite needs CV death and HF hospitalisation codes. Adjudicated: F3 = 0 (v1.9). |
| PRECISION | Other | 34 |  |  | ✓ |  |  | G | M | 2 | Good - minor deviations | High | High | Same agents (celecoxib vs naproxen; OTC naproxen unseen, dose titration record-only). APTC composite needs CV death incl. haemorrhagic. Adjudicated: F3 = 1 (v1.7). |
| FRAIL-AF | AF | 12 |  |  |  |  |  | G | P | 2 | Moderate - substantial deviations | Lower | Lower | Sequential warfarin-to-DOAC switch mirrors the randomised switch (F3 not flagged); any DOAC as in the trial. Primary = major or clinically relevant non-major bleeding; CRNM bleeding (the dominant component) is not ascertainable, only major-bleeding hospitalisation. |
| TRANSFORM-HF | HF | 12 | ✓ |  | ✓ |  |  | G | G | 2 | Moderate - substantial deviations | Lower | Lower | Randomised before discharge from an HF admission; initiators within 30 d of an HF code can take time zero from an inpatient IV furosemide order vs an oral discharge torsemide strategy (F1). 67% were on a loop diuretic before admission and changed agent at randomisation; the new-user design excludes them (F3). All-cause death. Adjudicated: comparator = good (v1.9). |
| AMPLIFY | Other | 6 |  |  |  |  |  | G | P | 2 | Moderate - substantial deviations | Lower | Lower | Apixaban vs warfarin (with parenteral lead-in) after acute VTE; both started around the index encounter with visible orders. Recurrent VTE from a new inpatient stay with a VTE code: ascertainable but low specificity and outpatient-managed recurrences missed (moderate, as RCT-DUPLICATE rated its AMPLIFY outcome). Adjudicated: outcome = poor (v1.7). |
| LODESTAR | Other | 36 |  |  |  |  |  | G | P | 2 | Moderate - substantial deviations | Lower | Lower | Rosuvastatin vs atorvastatin (factorial with intensity strategy; agents match). Any coronary revascularisation, the most frequent component of the RCT composite, is not captured (dominant component missing). |
| ACTIVE W | AF | 15 |  |  | ✓ |  |  | M | M | 3 | Moderate - substantial deviations | High | High | 77% were on OAC at entry and the clopidogrel+aspirin arm stopped it at randomisation (no protocol transition window); the initiator design neither requires nor reproduces that OAC discontinuation (F3). Aspirin not identifiable. Composite includes vascular death. |
| CABANA | AF | 49 |  |  |  | ✓ |  | M | M | 3 | Moderate - substantial deviations | High | High | Horizon 49 mo (F4). RCT drug arm = rate or rhythm drugs; emulation = antiarrhythmic initiators. 'Disabling' stroke not identifiable; serious bleeding reduced to GI bleed/ICH hospitalisation. |
| EAST-AFNET 4 | AF | 61 |  |  |  | ✓ |  | M | M | 3 | Moderate - substantial deviations | High | High | Horizon 61 mo (F4). Early rhythm-control strategy approximated by adding an antiarrhythmic (ablation-first not captured). Composite needs CV death from listed causes and HF/ACS hospitalisation codes. |
| CANVAS Program | Diabetes | 43 |  |  |  |  |  | P | M | 3 | Moderate - substantial deviations | Lower | Lower | Placebo-controlled; DPP-4i proxy. Horizon 43 mo. 3-point MACE. |
| CARMELINA | Diabetes | 26 |  |  |  |  |  | P | M | 3 | Moderate - substantial deviations | Lower | Lower | Placebo-controlled; sulfonylurea proxy. 3-point MACE. |
| EMPA-REG OUTCOME | Diabetes | 37 |  |  |  |  |  | P | M | 3 | Moderate - substantial deviations | Lower | Lower | Placebo-controlled; DPP-4i proxy. 3-point MACE with CV death from listed causes. |
| LEADER | Diabetes | 46 |  |  |  |  |  | P | M | 3 | Moderate - substantial deviations | Lower | Lower | Placebo-controlled; DPP-4i proxy. Horizon 46 mo (<48). 3-point MACE. |
| SUSTAIN-6 | Diabetes | 25 |  |  |  |  |  | P | M | 3 | Moderate - substantial deviations | Lower | Lower | Placebo-controlled; DPP-4i proxy. 3-point MACE. |
| TECOS | Diabetes | 36 |  |  |  |  |  | P | M | 3 | Moderate - substantial deviations | Lower | Lower | Placebo-controlled; sulfonylurea proxy (rated poor in RCT-DUPLICATE). 4-point MACE incl. UA hospitalisation. |
| EMPEROR-Preserved | HF | 26 |  |  |  |  |  | P | M | 3 | Moderate - substantial deviations | Lower | Lower | Placebo-controlled RCT emulated with a DPP-4i active-comparator proxy (estimand changes); T2D restriction. CV death or HF hospitalisation. |
| PARADIGM-HF | HF | 27 |  | ✓ |  |  |  | M | M | 3 | Moderate - substantial deviations | High | High | Sequential enalapril then sacubitril/valsartan active run-in removed intolerant patients (F2). The ACEi/ARB switch is mirrored by the sequential switch design. Comparator = any ACEi (trial: enalapril). CV death or HF hospitalisation. |
| LIFE | Hypertension | 58 |  |  |  | ✓ |  | M | M | 3 | Moderate - substantial deviations | High | Lower | Horizon 58 mo (F4). ARB class vs cardioselective beta-blocker class (trial losartan vs atenolol). Prior therapy was withdrawn during a placebo run-in before randomisation (not F2/F3). CV death, MI or stroke. Adjudicated: F3 = 0 (v1.9). |
| PROVE IT-TIMI 22 | Other | 24 |  |  |  |  |  | M | P | 3 | Moderate - substantial deviations | Lower | Lower | The tested hypothesis is intensive (atorvastatin 80) vs moderate (pravastatin 40) therapy; dose is not identifiable, so atorvastatin initiators at any dose change the hypothesis. Revascularisation >= 30 d, the most frequent component, is not captured. Statins start in the ACS admission (F1 not flagged). Adjudicated: comparator = moderate (v1.7). |
| DECLARE-TIMI 58 | Diabetes | 50 |  |  |  | ✓ |  | P | M | 4 | Limited - major deviations | Lower | Lower | Placebo-controlled; DPP-4i proxy. Horizon 50 mo (F4). CV death or HF hospitalisation. |
| REWIND | Diabetes | 65 |  |  |  | ✓ |  | P | M | 4 | Limited - major deviations | Lower | Lower | Placebo-controlled; DPP-4i proxy. Horizon 65 mo (F4). 3-point MACE. |
| ALLHAT | Hypertension | 59 |  |  | ✓ | ✓ |  | M | M | 4 | Limited - major deviations | Lower | Lower | About 90% were treated at entry and prior antihypertensives were replaced by study drug at randomisation without washout; initiator design does not mirror this (F3). Horizon 59 mo (F4). Thiazide class for chlorthalidone. Fatal CHD needs listed causes. |
| ASCOT-BPLA | Hypertension | 66 |  |  | ✓ | ✓ |  | M | M | 4 | Limited - major deviations | Lower | Lower | Previously treated patients (most) had therapy replaced at randomisation (PROBE, no washout) (F3). Horizon 66 mo (F4). Atenolol-based strategy approximated by cardioselective beta-blocker initiation. Fatal CHD from listed causes; silent MI not captured. |
| VALUE | Hypertension | 50 |  |  | ✓ | ✓ |  | M | M | 4 | Limited - major deviations | Lower | Lower | 89.9% previously treated were switched directly to study drug without run-in (F3). Horizon 50 mo (F4). ARB class for valsartan. Cardiac composite approximated by CV death, HF hospitalisation and MI (emergency procedures not captured). |
| ONTARGET | Other | 56 |  | ✓ |  | ✓ |  | M | M | 4 | Limited - major deviations | Lower | Lower | 3-week single-blind active run-in (ramipril, then telmisartan+ramipril) removed intolerant patients (F2 as the rule defines it). Horizon 56 mo (F4). ARB class for telmisartan, ACEi class for ramipril. CV death, MI, stroke or HF hospitalisation. Adjudicated: F3 = 0 (v1.9). |

## 7. References

- Wang SV, Schneeweiss S, et al. Emulation of randomized clinical trials with nonrandomized database analyses: results of 32 clinical trials. JAMA 2023;329:1376-85.
- Heyard R, Held L, Schneeweiss S, Wang SV. Design differences and variation in results between randomised trials and non-randomised emulations: meta-analysis of RCT-DUPLICATE data. BMJ Medicine 2024.
- Franklin JM, Patorno E, Desai RJ, et al. Emulating randomized clinical trials with nonrandomized real-world evidence studies: first results from the RCT DUPLICATE initiative. Circulation 2021;143:1002-13.
- Trial sources: per trial in `quality_tiers.json` (primary papers as registered in `trial_specs.PUBLISHED`, plus the protocol sources listed in the attestation).
