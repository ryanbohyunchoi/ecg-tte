# Emulation quality v2.0, re-scored on the spec-v2 fixed cohorts

Written 2026-10-08 (queue `docs/queue/QUEUE_2026_10_08.md`, step D). Scorer: Claude Opus 5.5 queue agent, not a clinician. Every changed item needs clinician review (framework §7.5).

- **Base record:** [`quality_v2_final.json`](quality_v2_final.json) (adjudicated v2.0 scores on the version 1 cohorts; [`ADJUDICATION.md`](ADJUDICATION.md)).
- **What was fixed:** [`../v2_cohorts/COHORT_FIXES.md`](../v2_cohorts/COHORT_FIXES.md); rules in `scripts/v2_cohorts/specs_v2.py`.
- **Framework:** [`QUALITY_FRAMEWORK.md`](QUALITY_FRAMEWORK.md). Tier rules unchanged; the tier function and the provisional-move rules are imported unchanged from `scripts/emulation_quality_v2/adjudicate.py`.
- **Output:** [`quality_v2_cohorts.json`](quality_v2_cohorts.json) (all 38 records, each with a `rescore_log` and the spec-v2 rules applied).
- **Code:**
  - `scripts/emulation_quality_v2/rescore_v2_cohorts.py` (`score`, then `impact`);
  - `scripts/emulation_quality_v2/dc_v2_cohorts.py` (data checks; bands only).
- **Aggregates:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-eq2-v2cohorts/`.
- **Order kept.** `score` wrote the JSON and its SHA-256 (`json_sha256.txt`) before any impact number was computed. `impact` refuses to run if the JSON changed. No score cites a result.

## Plain-language summary

- **What changed.** The spec-v2 cohorts fix most of the undocumented defects the v2.0 scoring had penalised: washouts, the age bound, gates, numeric entry bounds and the AMPLIFY outcome. Scoring those defects again would double-count. Re-scored:
  - the SI and EL items of every fixed trial;
  - DA, from data checks on the fixed cohorts (a fix can shrink an arm below 500 or cut the events);
  - OU for the two trials whose outcome rebuild added the missing dominant component (LODESTAR, PROVE IT), as the framework's OU text requires.
- **One rule for all 38 trials (numeric entry bounds).**
  - An undocumented numeric entry bound that the data can apply, and that spec v2 applies, scores 0.
  - One the data can apply but spec v2 did not apply would score as the framework says. None was found: `COHORT_FIXES.md` "Could not apply" lists only criteria the data cannot express (fasting values, UACR, NYHA, LA diameter, drug counts) or code-defined criteria (risk-factor routes, which are not numeric bounds).
  - So the audit's blocking item B1 resolves to **0 for the HbA1c windows and the BP entry bounds**: EMPA-REG, TECOS, CARMELINA, ASCOT-BPLA, ALLHAT and VALUE do not gain a point.
- **Tiers (computed mechanically):** 5 Excellent, 7 Good, 18 Moderate, 8 Limited (before: 3 / 5 / 21 / 9).
- **New analysed set: 30 trials** = the provisional 29 **plus AMPLIFY**.
  - AMPLIFY: its persisting-code SI 2 is fixed by the outcome rebuild. It keeps OU 2 and gains DA.b (<100 events), so it is Moderate.
  - Nobody leaves.
  - Against paper 1's 32: entering ALLHAT, ASCOT-BPLA, ONTARGET, VALUE; leaving ACTIVE W, CABANA, CANVAS Program, EMPEROR-Preserved, LEADER, SUSTAIN-6.
- **Tier moves inside the set:**
  - LAAOS III Moderate → Good (SI 2 fixed; DA.b, smaller arm now <500);
  - VALIANT Moderate → Good (SI fixed);
  - LODESTAR and PROVE IT Moderate → Excellent (OU re-score);
  - LIFE stays Moderate, at total 5 instead of 7.
- **Still Limited (8):**
  - CABANA (arm-assignment error; rebuild needed);
  - ACTIVE W (TZ 2 + TS 2);
  - EMPEROR-Preserved (N2 = 2);
  - LEADER, SUSTAIN-6, REWIND, DECLARE-TIMI 58 and CANVAS (placebo proxy + ≥3 other points: the washouts are fixed, but their EL, OU, FU and DA points remain).
- **Impact on the primary** (PS-CVD5 + ECG vs PS-CVD5, spec-v2 cells, 54 items):
  - new 30-trial set: **5.5% (0.8 to 10.7)**, 21/30 trials lower, P = .017;
  - Excellent + Good (12): 9.7% (2.6 to 18.1), P = .016;
  - all 38: 6.7%;
  - paper 1's 32: 6.6%.

  No set shows a trial-specific agreement gain: benchmark-permutation P ≥ .95 everywhere.

## 1. Rescoring decisions, per trial

"p" = provisional. Only items whose basis changed are listed. Every other item keeps its adjudicated score (`quality_v2_cohorts.json` → `rescore_log` for the full text).

| Trial | Item change | Reason |
|---|---|---|
| COMET | SI 1 → 0; DA 0 → 1; EL stays 2 | Succinate washout applied (COMET-SI-1 fixed). LVEF ≤35% now applied with unknown passing, and EF measured in 47% of the fixed cohort → DA.a. EL: prior CV admission and background diuretic + ACEi therapy remain omitted (documented) → still two criteria |
| VALIANT | SI 1 → 0; EL 0 (S4 resolved) | LV dysfunction / HF now required, with the index-day echo used (VALIANT-SI-1 fixed); ARNI excluded. DA stays 1: DA.b (smaller arm now <500); DA.a is a C10 question |
| LAAOS III | SI 2 → 0; DA 0 → 1 | AF before admission required (LAAOS3-SI-1 fixed); the fixed cohort's smaller arm is <500 (DA.b) |
| LIFE | SI 2 → 0 | Definite-LVH gate (LIFE-SI-1) and BP entry range (LIFE-SI-2, uniform rule) applied |
| CAROLINA | SI 1 → 0 | Age 40–85 (CAROLINA-SI-1) and HbA1c window applied |
| AMPLIFY | SI 2 → 0; DA 0 → 1 | Outcome re-defined exactly as the proposed spec edit (AMPLIFY-SI-1 fixed). Primary events fall below 100 (DA.b). OU stays 2 (inpatient-only, documented) |
| INSIGHT | SI 1p → 0 | BP entry threshold applied (INSIGHT-SI-1; uniform rule) |
| CANVAS Program | SI 1 → 0 | Other-SGLT2i washout (CANVAS-SI-1) |
| REWIND | SI 1 → 0 | Other-GLP-1RA washout (REWIND-SI-1) |
| LEADER | SI 0 → 0 | Washout defect (<5%) fixed; no score change |
| SUSTAIN-6 | SI 1p (basis changes) | Washout fixed. Remaining: the generic semaglutide token (SUSTAIN6-SI-2, share unchecked) |
| DECLARE-TIMI 58 | SI 1p (basis changes) | Washout + saxagliptin/alogliptin fixed. Remaining: any-position I50 (C3) |
| EMPEROR-Preserved | SI 1p (basis changes); DA 1p → 0 | Saxagliptin/alogliptin and the NT-proBNP bound fixed. Remaining: any-position I50 (C3). EF measured in 62.5% (DA.a absent), arms ≥500, events ≥100 |
| PARADIGM-HF | SI 1p (basis changes); DA 1p → 1 | NP bound applied (PARADIGM-SI-1-B fixed). Remaining: any-position I50 (C3). EF measured in 32% (DA.a confirmed) |
| AF-CHF, ELITE II | DA 1p → 1 | EF measured in 25% / 26% of the fixed cohort (DA.a confirmed by the data check) |
| LODESTAR | OU 2 → 1p | Revascularisation added (outcome rebuild); the dominant component is now ascertained. Index-stay revascularisations are not counted (anchor (iv), share unknown) |
| PROVE IT-TIMI 22 | OU 2 → 0p | Revascularisation ≥30 days added, as in the trial definition; the other components were already ascertained. Provisional until the component definitions are checked against the publication |

**DA on the fixed cohorts (data checks, `dc_v2_cohorts.py`, bands only).**
- DC-DA-size and DC-DA-meas were run on both cohort versions.
- **Check of the method:** on the version 1 cohorts, DA.b reproduces the adjudicated DA.b exactly. It applies to LEADER, CANVAS, INSIGHT and PROTECT AF, and to no other trial.
- **On the fixed cohorts, DA.b applies to:** LEADER, CANVAS, INSIGHT, PROTECT AF, and newly LAAOS III, VALIANT (smaller arm <500) and AMPLIFY (events <100).
- **DA.a:**
  - is derived from the measured EF share for the EF-defined trials (AF-CHF, ELITE II, PARADIGM-HF, EMPEROR-Preserved, and now COMET);
  - is kept as adjudicated for VALIANT (C10);
  - is unchanged elsewhere.

**Numeric entry bounds that were applied** (uniform rule → 0):
- HbA1c windows: EMPA-REG, CAROLINA, LEADER, SUSTAIN-6, REWIND, DECLARE, CANVAS, TECOS, CARMELINA;
- BP entry bounds: LIFE, INSIGHT, ASCOT-BPLA, ALLHAT, VALUE;
- natriuretic-peptide thresholds: PARADIGM-HF, EMPEROR-Preserved, RAFT-AF;
- PROVE IT cholesterol cap;
- PARADIGM-HF LVEF ≤35%;
- COMET LVEF ≤35%;
- age bounds in all 38 (only CAROLINA removed anyone).

The per-trial lists are in each record's `spec_v2` field. Safety-type exclusions (renal, haemoglobin, platelets, ALT, "uncontrolled BP") were also applied. They are not population-defining, so no score depended on them.

**Coverage of the applied entry bounds.** These bounds are applied with "unknown passes", and coverage is often low (`audits/claude-v2-cohorts/flags/measured_share.csv`): HbA1c is measured in 10–37% of these cohorts, and BP in 22–40%. The rule above scores them 0, because the data apply them. The framework's DA.a covers only population-defining measurements, and the adjudication placed these bounds in SI, not EL. This is a judgement call, listed for the user. The `v2meas` sensitivity of `COHORT_FIXES.md` requires the value to be measured.

## 2. Final tiers (spec-v2 cohorts)

| Tier | Trials |
|---|---|
| Excellent (5) | ARISTOTLE, AFFIRM, PLATO, LODESTAR*, PROVE IT-TIMI 22* |
| Good (7) | AF-CHF, LAAOS III, RAFT-AF, ELITE II, VALIANT, CAROLINA, PRECISION |
| Moderate (18) | ROCKET-AF, RE-LY, EAST-AFNET 4, FRAIL-AF, PROTECT AF, COMET, PARADIGM-HF, TRANSFORM-HF, LIFE, ALLHAT, VALUE, ASCOT-BPLA, INSIGHT, EMPA-REG OUTCOME, TECOS, CARMELINA, ONTARGET, AMPLIFY |
| Limited (8) | CABANA, ACTIVE W, EMPEROR-Preserved, LEADER, SUSTAIN-6, REWIND, DECLARE-TIMI 58, CANVAS Program |

\* Through the OU re-score. Without it (SI/EL-only rescoring), both stay Moderate: Excellent + Good then has 10 trials and the analysed set is unchanged.

**Analysed set (Excellent + Good + Moderate), 30 trials:** AF-CHF, AFFIRM, ALLHAT, AMPLIFY, ARISTOTLE, ASCOT-BPLA, CARMELINA, CAROLINA, COMET, EAST-AFNET 4, ELITE II, EMPA-REG OUTCOME, FRAIL-AF, INSIGHT, LAAOS III, LIFE, LODESTAR, ONTARGET, PARADIGM-HF, PLATO, PRECISION, PROTECT AF, PROVE IT-TIMI 22, RAFT-AF, RE-LY, ROCKET-AF, TECOS, TRANSFORM-HF, VALIANT, VALUE.

| Comparison | Entering | Leaving |
|---|---|---|
| vs the provisional 29 (v2.0 adjudication, version 1 cohorts) | AMPLIFY | none |
| vs paper 1's 32 (v19) | ALLHAT, ASCOT-BPLA, ONTARGET, VALUE | ACTIVE W, CABANA, CANVAS Program, EMPEROR-Preserved, LEADER, SUSTAIN-6 |

**Tier-changing provisional scores (the set is not frozen):**
- RE-LY: EL, Moderate → Good or Excellent;
- EAST-AFNET 4: EL, SI, → Good;
- PROTECT AF: EL, → Good;
- RAFT-AF: OU, Excellent to Moderate;
- PARADIGM-HF: SI, → Good;
- PRECISION: SI, Excellent to Moderate;
- LODESTAR: OU, → Moderate;
- PROVE IT: TS, → Moderate;
- ACTIVE W: TZ, Limited → Moderate (C2).

**Analysed trials without a tier-changing provisional score (22):** AF-CHF, AFFIRM, ALLHAT, AMPLIFY, ARISTOTLE, ASCOT-BPLA, CARMELINA, CAROLINA, COMET, ELITE II, EMPA-REG OUTCOME, FRAIL-AF, INSIGHT, LAAOS III, LIFE, ONTARGET, PLATO, ROCKET-AF, TECOS, TRANSFORM-HF, VALIANT, VALUE.

## 3. Impact on the primary analysis (computed after the scores were fixed)

**Analysis:** PS-CVD5 + ECG vs PS-CVD5; spec-v2 cells (`audits/claude-v2-cohorts`, variant v2, PCs within the fixed cohort); main configuration; 54 leakage-corrected items (PS-CVD5 masks none of them).

**Statistics:** `sens_primary32.contrast_row`, unchanged:
- relative reduction with a 4,000-resample trial bootstrap (seed 20261001);
- exact one-sided sign-flip;
- |Δ log HR| with sign-flip and benchmark-permutation P (20,000 draws).

**Gates:**
- (a) version 1 cells, paper 1's 32 → paper 2's published 8.8% (4.4–13.3): **PASS**;
- (b) spec-v2 cells, provisional 29 → the `scripts/v2_psclin_mi` summary row, exactly: **PASS** (maximum deviation 7e-17).

| Set | Trials | Mean \|SMD\| reduction (95% CI) | m54 base → ECG | lower; P | % \|SMD\|<0.1; better; P | \|Δ log HR\| base → ECG; closer; P | Benchmark-permutation P |
|---|---|---|---|---|---|---|---|
| **New set (rescored)** | 30 | **5.5% (0.8 to 10.7)** | 0.119 → 0.112 | 21/30; .017 | 58.2 → 60.8; 17/30; .037 | 0.194 → 0.208; 15/30; .85 | .96 |
| Excellent + Good (rescored) | 12 | 9.7% (2.6 to 18.1) | 0.115 → 0.104 | 9/12; .016 | 59.1 → 64.6; 7/12; .021 | 0.133 → 0.160; 4/12; .86 | .98 |
| All 38 | 38 | 6.7% (2.5 to 10.8) | 0.127 → 0.118 | 27/38; .002 | 54.9 → 58.6; 23/38; .005 | 0.212 → 0.219; 19/38; .69 | .96 |
| Paper 1's 32 | 32 | 6.6% (2.0 to 11.4) | 0.134 → 0.125 | 22/32; .004 | 52.9 → 56.5; 18/32; .014 | 0.213 → 0.222; 14/32; .71 | .95 |
| (provisional 29) | 29 | 6.5% (2.2 to 11.4) | 0.120 → 0.112 | 21/29; .004 | 58.0 → 61.1; 17/29; .017 | 0.176 → 0.188; 15/29; .80 | .95 |
| (Excellent + Good without the OU re-score) | 10 | 8.1% (−0.0 to 17.6) | 0.114 → 0.105 | 7/10; .051 | 60.0 → 63.9; 5/10; .078 | 0.123 → 0.153; 3/10; .84 | .98 |

**Reading:**
- The ECG still improves balance in every set.
- Adding AMPLIFY to the provisional 29 lowers the estimate from 6.5% to 5.5%. On the spec-v2 cohort, AMPLIFY's ECG arm balances worse than its base.
- The Excellent + Good estimate is larger, but rests on 10–12 trials.
- Agreement with the RCTs does not improve in any set.
- These numbers were not used for any score.

## 4. Decisions for the user (not taken here)

1. **TRANSFORM-HF** (audit D1b): its documented time-zero / arm-assignment error is TZ = 2, which caps it at Moderate. The same error undocumented would be Limited. The fixes did not touch it; it needs a rebuild. Keep it at Moderate, or apply the Limited rule to a data-confirmed TZ = 2?
2. **The hypertension switch trials** (ALLHAT, ASCOT-BPLA, VALUE, with ONTARGET through TZ.b; audit D3): Moderate as the framework's §11.3 intends, or "TZ.c ≥50% with ≥3 other points → Limited"? Under that rule ALLHAT, ASCOT-BPLA and VALUE would leave (27 trials).
3. **Clarifications C1–C10** (ADJUDICATION §7), all still open. C1 (EL vs SI for undocumented code-defined criteria) remains the largest, and the fixes did not change it, because risk-factor routes were not applied. C3 (any-position I50) now carries the remaining SI points of PARADIGM-HF, EMPEROR-Preserved and DECLARE, and EAST-AFNET 4's SI 1p. C10 now concerns VALIANT as well (EF-unknown patients must carry an HF code), but VALIANT's DA is 1 through DA.b either way.
4. **The second half of B1** is not a numeric bound, so the uniform rule does not cover it: the TECOS and CARMELINA sulfonylurea-background subgroups excluded by the SU washout, and the TECOS background-therapy requirement (experienced-subgroup EL anchor). The Table 1 shares still need transcribing. One EL point would make TECOS Limited (placebo proxy + 3); CARMELINA would reach EL 2 (N2 = 2 → Limited).
5. **The OU re-score** for LODESTAR and PROVE IT (framework OU text). The queue asked for SI and EL; this goes slightly further. The analysed set is the same either way; only Excellent + Good changes (12 vs 10).
6. **Entry bounds applied with "unknown passes"** score 0 (this rule), although HbA1c and BP coverage is low. The alternative would add DA.a points to the diabetes and hypertension trials. That would push several placebo-proxy trials to Limited, which is the B1 question again, in DA rather than SI form.
7. **Freeze conditions (B2) are still unmet:**
   - hash or commit the rater files;
   - run DC-ES-cross for all 38, DC-EL-met and DC-SI-hf-anyposition;
   - transcribe the S5 publication facts;
   - complete the clinician review.

   This rescored set is a working set, not a frozen one.
