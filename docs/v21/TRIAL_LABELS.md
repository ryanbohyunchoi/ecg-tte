# Trial labels for paper2 (blind, adjudicated)

Written by `scripts/v21/adjudicate_labels.py` on 2026-10-07, **before any label-stratified result was computed**.

## Procedure

- Two independent labellers (separate Claude agents) saw only a results-free PICOT table for the 38 trials (`audits/claude-v21-paper2/labels/picot_blind.md`: area, trial, population, intervention, comparator, RCT primary endpoint, horizon). They saw no emulation results, no RCT estimates and no quality tiers, and they did not see each other's labels.
- Rubric: `physiologic` = yes if, in routine care, the choice between intervention and comparator is plausibly driven substantially by cardiac structure, function, rhythm/conduction or haemodynamic/congestion state (things an ECG can reflect), rather than mainly by metabolic, renal, bleeding, frailty, cost/formulary or prescriber factors. `domains` = one or more of LV_structure, LV_systolic_function, diastolic_LA, RV_pulmonary_congestion, rhythm_conduction, or none_cardiac. `confidence` = high/medium/low.
- Adjudication rule, fixed in advance: an agreed `physiologic` value stands, and a disagreement would go to a third blind labeller. Primary `domains` are the **intersection** of the two labellers' cardiac domains (none_cardiac if empty), and `domains_union` is kept as a sensitivity set. Confidence is the lower of the two.
- Caveat: the labellers know the published trials, and the user accepted some circularity (HANDOFF_PAPER2 §1.6). One labeller listed secondary cardiac domains for some 'no' trials and the other did not; the intersection rule resolves this conservatively.

## Agreement

- physiologic: 11/38 yes (A) and 11/38 yes (B); percent agreement 100%; **Cohen's κ = 1.00**. No third labeller was needed.
- domains: identical for 26/38 trials; the 12 differences are listed below.

| Trial | Labeller A | Labeller B | Final (intersection) |
|---|---|---|---|
| EAST-AFNET 4 | LV_structure, LV_systolic_function, diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, rhythm_conduction |
| CABANA | diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, rhythm_conduction | diastolic_LA, rhythm_conduction |
| AF-CHF | LV_systolic_function, diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, RV_pulmonary_congestion, rhythm_conduction | LV_systolic_function, diastolic_LA, rhythm_conduction |
| LAAOS III | diastolic_LA, rhythm_conduction | diastolic_LA | diastolic_LA |
| RAFT-AF | LV_systolic_function, diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, RV_pulmonary_congestion, rhythm_conduction | LV_systolic_function, diastolic_LA, rhythm_conduction |
| TRANSFORM-HF | LV_systolic_function, RV_pulmonary_congestion | RV_pulmonary_congestion | RV_pulmonary_congestion |
| EMPEROR-Preserved | LV_systolic_function, diastolic_LA, RV_pulmonary_congestion | LV_systolic_function, RV_pulmonary_congestion | LV_systolic_function, RV_pulmonary_congestion |
| LIFE | LV_structure, rhythm_conduction | LV_structure, LV_systolic_function, rhythm_conduction | LV_structure, rhythm_conduction |
| VALUE | LV_systolic_function | none_cardiac | none_cardiac |
| EMPA-REG OUTCOME | LV_systolic_function | none_cardiac | none_cardiac |
| DECLARE-TIMI 58 | LV_systolic_function | none_cardiac | none_cardiac |
| AMPLIFY | RV_pulmonary_congestion | none_cardiac | none_cardiac |

## Final labels

| Area | Trial | Physiologic | Domains (primary) | Domains (union, sensitivity) | Confidence |
|---|---|---|---|---|---|
| AF | ARISTOTLE | no | none_cardiac | none_cardiac | medium |
| AF | ROCKET-AF | no | none_cardiac | none_cardiac | medium |
| AF | RE-LY | no | none_cardiac | none_cardiac | high |
| AF | EAST-AFNET 4 | yes | LV_systolic_function, diastolic_LA, rhythm_conduction | LV_structure, LV_systolic_function, diastolic_LA, rhythm_conduction | medium |
| AF | CABANA | yes | diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, rhythm_conduction | medium |
| AF | AFFIRM | yes | LV_systolic_function, diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, rhythm_conduction | medium |
| AF | AF-CHF | yes | LV_systolic_function, diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, RV_pulmonary_congestion, rhythm_conduction | medium |
| AF | FRAIL-AF | no | none_cardiac | none_cardiac | high |
| AF | LAAOS III | no | diastolic_LA | diastolic_LA, rhythm_conduction | low |
| AF | PROTECT AF | no | none_cardiac | none_cardiac | high |
| AF | RAFT-AF | yes | LV_systolic_function, diastolic_LA, rhythm_conduction | LV_systolic_function, diastolic_LA, RV_pulmonary_congestion, rhythm_conduction | medium |
| AF | ACTIVE W | no | none_cardiac | none_cardiac | medium |
| HF | COMET | yes | LV_systolic_function, rhythm_conduction | LV_systolic_function, rhythm_conduction | medium |
| HF | PARADIGM-HF | yes | LV_systolic_function, RV_pulmonary_congestion | LV_systolic_function, RV_pulmonary_congestion | medium |
| HF | TRANSFORM-HF | yes | RV_pulmonary_congestion | LV_systolic_function, RV_pulmonary_congestion | low |
| HF | ELITE II | no | none_cardiac | none_cardiac | high |
| HF | EMPEROR-Preserved | yes | LV_systolic_function, RV_pulmonary_congestion | LV_systolic_function, diastolic_LA, RV_pulmonary_congestion | low |
| Hypertension | LIFE | yes | LV_structure, rhythm_conduction | LV_structure, LV_systolic_function, rhythm_conduction | medium |
| Hypertension | ALLHAT | no | none_cardiac | none_cardiac | medium |
| Hypertension | VALUE | no | none_cardiac | LV_systolic_function | low |
| Hypertension | ASCOT-BPLA | yes | LV_systolic_function, rhythm_conduction | LV_systolic_function, rhythm_conduction | medium |
| Hypertension | INSIGHT | no | none_cardiac | none_cardiac | medium |
| ACS / MI | PLATO | no | rhythm_conduction | rhythm_conduction | low |
| ACS / MI | VALIANT | no | none_cardiac | none_cardiac | high |
| Diabetes | EMPA-REG OUTCOME | no | none_cardiac | LV_systolic_function | low |
| Diabetes | CAROLINA | no | none_cardiac | none_cardiac | high |
| Diabetes | LEADER | no | none_cardiac | none_cardiac | high |
| Diabetes | SUSTAIN-6 | no | none_cardiac | none_cardiac | high |
| Diabetes | REWIND | no | none_cardiac | none_cardiac | high |
| Diabetes | DECLARE-TIMI 58 | no | none_cardiac | LV_systolic_function | medium |
| Diabetes | CANVAS Program | no | none_cardiac | none_cardiac | medium |
| Diabetes | TECOS | no | none_cardiac | none_cardiac | high |
| Diabetes | CARMELINA | no | none_cardiac | none_cardiac | high |
| Other | ONTARGET | no | none_cardiac | none_cardiac | high |
| Other | PRECISION | no | none_cardiac | none_cardiac | high |
| Other | AMPLIFY | no | none_cardiac | RV_pulmonary_congestion | medium |
| Other | LODESTAR | no | none_cardiac | none_cardiac | high |
| Other | PROVE IT-TIMI 22 | no | none_cardiac | none_cardiac | high |

Domain counts (primary): LV_structure 1; LV_systolic_function 8; diastolic_LA 6; RV_pulmonary_congestion 3; rhythm_conduction 9; none_cardiac 25

Rationales from both labellers are in `TRIAL_LABELS.json` (`rationale_A`, `rationale_B`).
