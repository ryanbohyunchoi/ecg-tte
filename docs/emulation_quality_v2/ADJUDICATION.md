# Emulation quality v2.0: adjudication of the two ratings (38 trials)

Date: 2026-10-08. Framework: [`QUALITY_FRAMEWORK.md`](QUALITY_FRAMEWORK.md) (v2.0 draft, section 11 defaults; not edited).
Ratings: `/mnt/raid0/rbc58/ecg-tte/audits/claude-eq2/scores_A.json`, `scores_B.json` (rater A and rater B, both Claude
Opus 5.5 agent runs). Adjudicated records: [`quality_v2_final.json`](quality_v2_final.json). Code:
[`scripts/emulation_quality_v2/adjudicate.py`](../../scripts/emulation_quality_v2/adjudicate.py) (`all`, then `impact`).
Aggregate outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-eq2/` (`agreement.csv`, `disagreements.csv`, `tiers.csv`,
`alt_tiers.csv`, `rater_tier_check.csv`, `impact.csv`). Nothing was committed.

**Who rated.** Both raters and the adjudicator are runs of the same LLM. The agreement below is between two LLM runs. It is
not human inter-rater reliability. The adjudicator is not a clinician, so framework 7.1 and 7.5 require a clinician to
confirm or override every adjudicated point (list in section 10).

## Plain-language summary

- **Agreement.** The raters agreed on 344 of 380 item scores (36 disagreements in 24 trials).
  - Total score: ICC 0.89 (95% CI 0.82–0.94).
  - Tier: weighted κ 0.72 (0.52–0.89); same tier in 30/38 trials.
  - Analysed-set membership: κ 0.77 (0.49–1.00); 3 trials differ (ACTIVE W, LIFE, SUSTAIN-6).
  - Eligibility (EL) drove most of the disagreement: 19 of 36, κ 0.31. Most of these were one question: whether an
    *undocumented* omitted eligibility criterion goes to EL (rater A) or SI (rater B).
- **Final tiers (computed by code from the adjudicated items).** 3 Excellent, 5 Good, 21 Moderate, 9 Limited.
- **Analysed set (Excellent + Good + Moderate): 29 trials, against the 32 in paper 1.**
  - Leaving (7): ACTIVE W, AMPLIFY, CABANA, CANVAS Program, EMPEROR-Preserved, LEADER, SUSTAIN-6.
  - Entering (4): ALLHAT, ASCOT-BPLA, ONTARGET, VALUE.
  - DECLARE-TIMI 58 and REWIND stay excluded.
- **Primary result (paper 1, PS-Demo + ECG vs PS-Demo).** The gate reproduces the published numbers exactly. On the new
  29-trial set, the ECG still lowers mean |SMD| by 11.4% (95% CI 5.7–16.1). It improves the share of balanced
  characteristics in 21/29 trials (P = .001) and reduces |Δ log HR| from 0.228 to 0.178 (P = .005). The
  benchmark-permutation P is .15, against .26 published. Table in section 9.
- **Framework-design issues for you (section 6).** Five of the seven trials the data check classed MAJOR end at Moderate,
  and so stay in the analysed set: LAAOS III, COMET, TRANSFORM-HF, LIFE and VALIANT. This follows from how the tier rules
  are written, not from scoring errors. The main reasons:
  - SI = 2 by share caps a trial at Moderate. Only an SI arm-assignment or time-zero error makes it Limited.
  - A *documented* time-zero error (TZ = 2) also only caps at Moderate.
  - "Unknown passes" for a defining measurement is worth at most 1 point (DA).
  - The majority-switch hypertension trials come back in, because TZ is capped at 2.
- **Framework clarifications needed (v2.0.1): ten (C1–C10), plus two design questions (D2, D3).** Each would change at
  least one tier, or a resolved data check could. Section 7. The largest is C1, the EL vs SI allocation:
  - its literal reading moves ROCKET-AF, RE-LY and EAST-AFNET 4 to Good, and SUSTAIN-6 back into the analysed set;
  - once the shares are checked, the same reading could make ALLHAT, ASCOT-BPLA, ONTARGET and VALUE Limited.
- **Provisional scores (section 8).** Ten trials in the analysed set have a provisional item that could change their
  tier: RE-LY, EAST-AFNET 4, AF-CHF, PROTECT AF, RAFT-AF, PARADIGM-HF, ELITE II, VALIANT, PRECISION and PROVE IT-TIMI 22.
  ACTIVE W, which is Limited, could also move back in (C2). The set is **not frozen** (framework 7.6). 19 trials have no tier-changing provisional score
  (sensitivity set).
- **Code-bug check (`v13_summarize.py` L212–215).** Not a bug. `np.log` wraps the whole conditional expression, so the
  flipped COMET bounds are logged. No published number depends on it, because paper 1 agreement metrics come from
  `scripts/v20/sens_primary32.py`. Section 11.

## 1. Agreement (unadjudicated ratings)

95% percentile bootstrap CIs over trials, 2,000 resamples (seed 20261008). Linear-weighted κ for 0–2 items and the tier;
Cohen's κ for 0–1 items and features. Tiers were recomputed by code from each rater's items; they match the tiers the
raters reported for all 76 records.

| Element | % exact agreement | κ (95% CI) | Prevalence ≠ 0 | Disagreements |
|---|---|---|---|---|
| EL (0–2) | 50.0 | 0.31 (0.14–0.51) | 54% | 19 |
| TZ (0–2) | 94.7 | 0.91 (0.77–1.00) | 28% | 2 |
| TS (0–2) | 100 | 1.00 | 37% | 0 |
| CO (0–2) | 100 | 1.00 | 55% | 0 |
| OU (0–2) | 100 | 1.00 | 79% | 0 |
| FU (0–1) | 100 | 1.00 | 32% | 0 |
| ES (0–1) | 86.8 | 0.25 (0.00–0.65) | 9% | 5 |
| BM (0–1) | 100 | 1.00 | 21% | 0 |
| DA (0–1) | 97.4 | 0.92 (0.72–1.00) | 22% | 1 |
| SI (0–2) | 76.3 | 0.66 (0.42–0.85) | 46% | 9 |
| Features | TZ.c 97.4% (κ 0.92); ES.b 86.8% (κ 0.00, B never scored it); DA.a 97.4% (κ 0.87); all others 100% (BM.e, BM.f never present, κ undefined) | | | |
| Placebo proxy | 100 | 1.00 | 24% | 0 |
| Tier, 4 levels | 78.9 | weighted 0.72 (0.52–0.89); unweighted 0.68 (0.46–0.86) | | 8 |
| Analysed set | 92.1 | 0.77 (0.49–1.00) | | 3 |
| Total (0–16) | 52.6 | ICC(2,1) 0.89 (0.82–0.94); mean A 4.74, B 4.26 | | 18 |

The 8 tier disagreements (A / B):
- ROCKET-AF and RE-LY: Moderate / Excellent;
- EAST-AFNET 4, PROTECT AF and VALIANT: Moderate / Good;
- ACTIVE W, LIFE and SUSTAIN-6: Limited / Moderate.

## 2. Every item-level disagreement and its adjudication

"Rubric text" means the framework text decides the score. "Default" means the text does not decide, so the more severe
score stands (framework 7.4.3) and the case is listed in section 7. Section 1.3 (score each deviation once) *is* text. So
when the raters put one deviation in different items, it is scored in one item only. The full reasons and evidence are in
each record's `adjudication` log in `quality_v2_final.json`.

| # | Trial | Item | A | B | Adjudicated | Decided by | Deciding clause, in short |
|---|---|---|---|---|---|---|---|
| 1 | ARISTOTLE | ES | 1 | 0 | 1 prov. | Default, C7 | Secular warfarin→DOAC replacement as the ES.b "specific mechanism" |
| 2 | ROCKET-AF | EL | 2 | 1 | 2 | Default, C1/C6 | CHADS2 ≥2 omitted (undocumented) + new-user exclusion of ~62% VKA-experienced |
| 3 | ROCKET-AF | ES | 1 | 0 | 1 prov. | Default, C7 | as #1 |
| 4 | ROCKET-AF | SI | 0 | 1 | 0 | Score once (C1) | B's SI point is the CHADS2 omission, now in EL |
| 5 | RE-LY | EL | 2 | 1 | 2 prov. | Default, C1/C6/C8 | RE-LY's risk list is narrower than the framework's "≥1 risk factor" example; ≥90%-met not shown |
| 6 | RE-LY | ES | 1 | 0 | 1 prov. | Default, C7 | as #1 (weakest mechanism here) |
| 7 | EAST-AFNET 4 | EL | 1 | 0 | 1 prov. | Default, C1 | CV-risk criterion omitted, undocumented |
| 8 | CABANA | EL | 1 | 0 | 1 | Default, C1 | Age ≥65 or risk-factor criterion omitted, undocumented |
| 9 | FRAIL-AF | ES | 1 | 0 | 1 prov. | Default, C7 | as #1 |
| 10 | PROTECT AF | EL | 2 | 1 | 2 prov. | Default, C9 | Warfarin-eligibility requirement vs LAAO selected for bleeding risk ("plausibly material") |
| 11 | ACTIVE W | EL | 1 | 0 | 1 | Default, C1 | Age ≥75-alone and CAD routes omitted, undocumented |
| 12 | ACTIVE W | TZ | 2 | 1 | 2 prov. | Default, C2 | TZ.c ≥50%: 77% on OAC (A) vs ~38% actually switched (B) |
| 13 | ACTIVE W | SI | 0 | 1 | 0 | Score once (C1) | moved to EL (#11) |
| 14 | COMET | SI | 1 | 0 | 1 | Rubric text | Section 5 "same-class agent not washed out" → SI type 2; the adapted protocol defers the washout, so it is not a documented choice; 5–20% (data) |
| 15 | PARADIGM-HF | EL | 1 | 0 | 0 | Rubric text | NT-proBNP is in OMOP gold (`docs/DATA_SOURCES.md`), so the omitted NP bound is a correctable numeric bound → SI type 4 |
| 16 | TRANSFORM-HF | EL | 1 | 0 | 1 | Rubric text | The gate approximation is stated in the eTable 1 design notes → documented → EL |
| 17 | TRANSFORM-HF | SI | 0 | 1 | 0 | Rubric text | as #16; nothing undocumented remains |
| 18 | EMPEROR-Preserved | EL | 2 | 1 | 2 prov. | Default, C1 | T2D restriction (documented) + structural-heart-disease / HF-hospitalisation requirement (A; verify). NT-proBNP → SI (text, as #15) |
| 19 | EMPEROR-Preserved | DA | 0 | 1 | 1 prov. | Rubric text (C10 flagged) | DA unknown rule: data check not run and the trial is EF-defined → 1 provisional |
| 20 | LIFE | EL | 1 | 0 | 0 | Rubric text | The BP entry range is an undocumented numeric bound → SI type 4 (EL "scored elsewhere"); SI already 2 |
| 21 | ALLHAT | EL | 1 | 0 | 1 | Default, C1 | ≥1 additional CHD risk factor omitted, undocumented |
| 22 | ALLHAT | SI | 0 | 1 | 0 | Score once (C1) | moved to EL |
| 23 | VALUE | EL | 1 | 0 | 1 | Default, C1 | High-CV-risk requirement omitted, undocumented |
| 24 | VALUE | SI | 0 | 1 | 0 | Score once (C1) | moved to EL |
| 25 | ASCOT-BPLA | EL | 1 | 0 | 1 | Default, C1 | ≥3 risk factors omitted, undocumented |
| 26 | ASCOT-BPLA | SI | 0 | 1 | 0 | Score once (C1) | moved to EL |
| 27 | INSIGHT | EL | 1 | 0 | 0 | Rubric text | BP entry threshold = numeric bound → SI type 4. SI re-scored 0 → 1 provisional (consequential; total unchanged at 6) |
| 28 | VALIANT | TZ | 1 | 0 | 1 prov. | Rubric text | ACEi stopped at randomisation; ~40% on ACEi (secondary source) → TZ.c present, below 50%; verify against Pfeffer 2003 Table 1 |
| 29 | SUSTAIN-6 | EL | 1 | 0 | 1 | Default, C1 | ≥60-year risk-factor stratum omitted. It is documented for LEADER but not for SUSTAIN-6 |
| 30 | DECLARE-TIMI 58 | EL | 1 | 0 | 1 | Default, C1 | ASCVD or multiple-risk-factor requirement omitted, undocumented |
| 31 | CANVAS Program | EL | 1 | 0 | 1 | Default, C1 | ASCVD or ≥2 risk factors omitted, undocumented |
| 32 | ONTARGET | EL | 1 | 0 | 1 | Default, C1 | "Diabetes with end-organ damage" approximated by any E11 code, undocumented |
| 33 | ONTARGET | SI | 0 | 1 | 0 | Score once (C1) | moved to EL |
| 34 | PRECISION | SI | 0 | 1 | 1 prov. | Default | The gate accepts one HTN or lipid code; the trial required CVD, diabetes or multiple risk factors (definition from secondary sources; verify the appendix) |
| 35 | AMPLIFY | EL | 1 | 0 | 1 prov. | Default, C9 | Cancer with planned LMWH not excluded ("plausibly material"); Limited either way |
| 36 | AMPLIFY | ES | 1 | 0 | 1 prov. | Default, C7 | as #1 |

**Same score, different basis.** Both raters gave SI 1 in four trials, for different defects:
- **EAST-AFNET 4:** any-position I50 (C3). B's CV-risk point moved to EL.
- **PARADIGM-HF:** NP bound plus any-position I50.
- **EMPEROR-Preserved:** saxagliptin/alogliptin under 5%, NP bound and any-position I50.
- **DECLARE-TIMI 58:** washout plus saxagliptin/alogliptin at 5–20%, and any-position I50.

**Other basis notes:**
- The CABANA disabling-stroke footnote is a documentation error, not an SI defect. eTable 1 matches the code; the paper
  Table 1 note is wrong.
- The TRANSFORM-HF population label "HF hospitalisation (discharge within 30 d)" contradicts the gate. Under 5% of index
  orders fall within 30 days after a discharge (data). The label should be corrected.

## 3. Final tiers

Computed by `adjudicate.py` from the adjudicated item scores (framework section 6). "p" = provisional.

| Trial | EL | TZ | TS | CO | OU | FU | ES | BM | DA | SI | Total | Tier (v2.0) | Rule | v19 tier | Rater A / B tier | Tier-changing provisional |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ARISTOTLE | 1 | 0 | 0 | 0 | 0 | 0 | 1p | 0 | 0 | 0 | 2 | **Excellent** | total 0–2 | Excellent | Excellent / Excellent | none |
| ROCKET-AF | 2 | 0 | 0 | 0 | 0 | 0 | 1p | 0 | 0 | 0 | 3 | **Moderate** | N2 = 1 cap | Excellent | Moderate / Excellent | none |
| RE-LY | 2p | 0 | 0 | 0 | 0 | 0 | 1p | 1 | 0 | 0 | 4 | **Moderate** | N2 = 1 cap | Excellent | Moderate / Excellent | EL (→ Good or Excellent) |
| EAST-AFNET 4 | 1p | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 1p | 5 | **Moderate** | total 5–7 | Moderate | Moderate / Good | EL, SI (→ Good) |
| CABANA | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 2 | 7 | **Limited** | SI 2 arm-assignment | Moderate | Limited / Limited | none |
| AFFIRM | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | **Excellent** | total 0–2 | Good | Excellent / Excellent | none |
| AF-CHF | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1p | 0 | 3 | **Good** | total 3–4 | Good | Good / Good | DA (→ Excellent) |
| FRAIL-AF | 1 | 0 | 0 | 0 | 2 | 0 | 1p | 0 | 0 | 0 | 4 | **Moderate** | N2 = 1 cap | Moderate | Moderate / Moderate | none |
| LAAOS III | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 2 | 4 | **Moderate** | N2 = 1 cap | Good | Moderate / Moderate | none |
| PROTECT AF | 2p | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 5 | **Moderate** | total 5–7; N2 = 1 | Good | Moderate / Good | EL (→ Good) |
| RAFT-AF | 1 | 0 | 0 | 1 | 1p | 0 | 0 | 0 | 0 | 0 | 3 | **Good** | total 3–4 | Good | Good / Good | OU (→ Excellent or Moderate) |
| ACTIVE W | 1 | 2p | 2 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 7 | **Limited** | N2 ≥ 2 | Moderate | Limited / Moderate | TZ (→ Moderate) |
| COMET | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 4 | **Moderate** | N2 = 1 cap | Good | Moderate / Moderate | none |
| PARADIGM-HF | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 1p | 1p | 5 | **Moderate** | total 5–7 | Moderate | Moderate / Moderate | DA, SI (→ Good) |
| TRANSFORM-HF | 1 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 4 | **Moderate** | N2 = 1 cap | Moderate | Moderate / Moderate | none |
| ELITE II | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 1p | 0 | 3 | **Good** | total 3–4 | Good | Good / Good | DA (→ Excellent) |
| EMPEROR-Preserved | 2p | 0 | 1 | 2 | 1 | 0 | 0 | 0 | 1p | 1p | 8 | **Limited** | total ≥ 8; N2 ≥ 2; PP + ≥3 | Moderate | Limited / Limited | none |
| LIFE | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 2 | 7 | **Moderate** | total 5–7; N2 = 1 | Moderate | Limited / Moderate | none |
| ALLHAT | 1 | 2 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 7 | **Moderate** | total 5–7; N2 = 1 | Limited | Moderate / Moderate | none |
| VALUE | 1 | 2 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 6 | **Moderate** | total 5–7; N2 = 1 | Limited | Moderate / Moderate | none |
| ASCOT-BPLA | 1 | 2 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 7 | **Moderate** | total 5–7; N2 = 1 | Limited | Moderate / Moderate | none |
| INSIGHT | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 1p | 6 | **Moderate** | total 5–7 | Good | Moderate / Moderate | none |
| PLATO | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | **Excellent** | total 0–2 | Good | Excellent / Excellent | none |
| VALIANT | 0 | 1p | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 5 | **Moderate** | total 5–7 | Good | Moderate / Good | TZ (→ Good) |
| EMPA-REG OUTCOME | 0 | 0 | 1 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 4 | **Moderate** | N2 = 1 cap (PP, other 2) | Moderate | Moderate / Moderate | none |
| CAROLINA | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 4 | **Good** | total 3–4 | Good | Good / Good | none |
| LEADER | 1 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 5 | **Limited** | PP + ≥3 | Moderate | Limited / Limited | none |
| SUSTAIN-6 | 1 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 1p | 5 | **Limited** | PP + ≥3 | Moderate | Limited / Moderate | none |
| REWIND | 1 | 0 | 0 | 2 | 1 | 1 | 0 | 0 | 0 | 1 | 6 | **Limited** | PP + ≥3 | Limited | Limited / Limited | none |
| DECLARE-TIMI 58 | 1 | 0 | 0 | 2 | 1 | 1 | 0 | 0 | 0 | 1p | 6 | **Limited** | PP + ≥3 | Limited | Limited / Limited | none |
| CANVAS Program | 1 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 1 | 1 | 6 | **Limited** | PP + ≥3 | Moderate | Limited / Limited | none |
| TECOS | 0 | 0 | 0 | 2 | 1 | 0 | 1 | 0 | 0 | 0 | 4 | **Moderate** | N2 = 1 cap (PP, other 2) | Moderate | Moderate / Moderate | none |
| CARMELINA | 1 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 4 | **Moderate** | N2 = 1 cap (PP, other 2) | Moderate | Moderate / Moderate | none |
| ONTARGET | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 7 | **Moderate** | total 5–7 | Limited | Moderate / Moderate | none |
| PRECISION | 0 | 1p | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 1p | 4 | **Good** | total 3–4 | Good | Good / Good | SI (→ Excellent or Moderate) |
| AMPLIFY | 1p | 0 | 0 | 0 | 2 | 0 | 1p | 1 | 0 | 2 | 7 | **Limited** | N2 ≥ 2 | Moderate | Limited / Limited | none |
| LODESTAR | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | **Moderate** | N2 = 1 cap | Moderate | Moderate / Moderate | none |
| PROVE IT-TIMI 22 | 0 | 0 | 1p | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 3 | **Moderate** | N2 = 1 cap | Moderate | Moderate / Moderate | TS (→ Limited) |

**How provisional scores can move** (used for the last column):
- EL, TZ, ES and DA provisional scores can only fall: they encode a deviation that is present but not confirmed. TZ is
  never escalated on an unknown share.
- SI and OU provisional scores can move either way. Where a known 5–20% defect exists, SI cannot fall below 1.
- TS (PROVE IT) can only rise.
- ACTIVE W TZ can move between 2 and 1 (C2).

## 4. Analysed set and changes against paper 1

| Set | Trials |
|---|---|
| **Primary (Excellent + Good + Moderate), 29** | AF-CHF, AFFIRM, ALLHAT, ARISTOTLE, ASCOT-BPLA, CARMELINA, CAROLINA, COMET, EAST-AFNET 4, ELITE II, EMPA-REG OUTCOME, FRAIL-AF, INSIGHT, LAAOS III, LIFE, LODESTAR, ONTARGET, PARADIGM-HF, PLATO, PRECISION, PROTECT AF, PROVE IT-TIMI 22, RAFT-AF, RE-LY, ROCKET-AF, TECOS, TRANSFORM-HF, VALIANT, VALUE |
| Excellent + Good, 8 | AF-CHF, AFFIRM, ARISTOTLE, CAROLINA, ELITE II, PLATO, PRECISION, RAFT-AF |
| Analysed set without a tier-changing provisional score, 19 | AFFIRM, ALLHAT, ARISTOTLE, ASCOT-BPLA, CARMELINA, CAROLINA, COMET, EMPA-REG OUTCOME, FRAIL-AF, INSIGHT, LAAOS III, LIFE, LODESTAR, ONTARGET, PLATO, ROCKET-AF, TECOS, TRANSFORM-HF, VALUE |
| Limited (excluded), 9 | ACTIVE W, AMPLIFY, CABANA, CANVAS Program, DECLARE-TIMI 58, EMPEROR-Preserved, LEADER, REWIND, SUSTAIN-6 |

Against the paper 1 set (32 = 38 minus ALLHAT, ASCOT-BPLA, DECLARE-TIMI 58, ONTARGET, REWIND, VALUE):

- **Leaving (7).**
  - CABANA: SI arm-assignment error.
  - ACTIVE W: TZ 2 + TS 2.
  - AMPLIFY: OU 2 + SI 2.
  - EMPEROR-Preserved, LEADER, SUSTAIN-6, CANVAS Program: placebo proxy plus ≥3 other points.
- **Entering (4).** ALLHAT, ASCOT-BPLA, VALUE and ONTARGET, all at Moderate.
  - v19 summed F3 and F4 flags without a cap.
  - v2.0 caps TZ at 2, and TZ = 2 alone only caps the tier at Moderate. Their totals are 6–7, below 8.

## 5. Consistency with the data-check MAJOR findings

| Trial (MAJOR finding, `TRIAL_CRITERIA_CHECK.md`) | EL | TZ | OU | SI (basis) | Other | Total | Tier | Limited by the rules? |
|---|---|---|---|---|---|---|---|---|
| CABANA (dedupe assigns eventual-ablation patients to the AAD arm) | 1 | 1 | 1 | 2 (type 7, arm assignment) | CO 1, FU 1 | 7 | Limited | **Yes**: SI arm-assignment rule |
| LAAOS III (57% first AF code in the index surgical stay) | 0 | 0 | 1 | 2 (type 5 gate, >20%, fixable by exclusion) | CO 1 | 4 | Moderate | **No**: SI 2 by share caps at Moderate (D1) |
| COMET (no LVEF restriction; 39% EF >35%) | 2 (documented adaptation) | 0 | 0 | 1 (succinate, 5–20%) | FU 1 | 4 | Moderate | **No**: a documented adaptation of MAJOR size is EL 2, which caps at Moderate (D1) |
| TRANSFORM-HF (time zero at the in-hospital loop order; switchers excluded) | 1 | 2 (TZ.a + TZ.c, documented) | 0 | 0 | FU 1 | 4 | Moderate | **No**: the error is documented, so it is TZ (cap at Moderate). The same error undocumented would be SI 2 arm-assignment → Limited (D1) |
| LIFE (22% qualify only through hedged LVH statements) | 0 | 0 | 1 | 2 (type 5 gate, >20%, fixable; BP bound absorbed) | TS 1, CO 1, FU 1, BM 1 | 7 | Moderate | **No**: SI 2 by share caps at Moderate. One point short of the total-8 rule; the BP bound adds nothing because SI is already 2 (D1, D2) |
| VALIANT (59% have neither documented LV dysfunction nor HF) | 0 | 1p | 0 | 1 (index-day echo, 5–20%) | TS 1, CO 1, DA 1 (EF measured in <50%) | 5 | Moderate | **No**: the 43% "EF unknown, no HF" is documented "unknown passes", worth at most DA 1 (D1) |
| AMPLIFY (recurrent VTE mostly persisting codes) | 1p | 0 | 2 | 2 (type 6, >20% of events) | ES 1p, BM 1 | 7 | Limited | **Yes**: N2 ≥ 2 |

These are **framework-design issues, not scoring errors**: the items were scored as the text says.

## 6. Framework-design issues for the user

- **D1. MAJOR data findings can end at Moderate (LAAOS III, COMET, TRANSFORM-HF, LIFE, VALIANT).**
  - The Limited rule reacts to an SI arm-assignment or time-zero error, to N2 ≥ 2, or to a total ≥8.
  - A single item at 2 for any other reason (SI by share, a documented EL or TZ deviation) caps the tier at Moderate.
  - So a fixable defect affecting 20–60% of the cohort leaves a trial in the analysed set.
  - TRANSFORM-HF shows the asymmetry most clearly. Its time-zero and arm-assignment problem is documented, so it is TZ =
    2 (Moderate). An identical undocumented problem would be SI = 2 arm-assignment (Limited).
  - Options:
    - (a) SI = 2 with a share above 50%, or any MAJOR data-check class, gives Limited until rebuilt;
    - (b) apply the arm-assignment/time-zero Limited rule to TZ = 2 as well when the data check shows a design-level
      error;
    - (c) accept the design and rely on the rebuilds.
- **D2. Score-once makes some deviations free.** When SI is already 2, further undocumented defects add no points. LIFE's
  BP entry range is an example: scored in EL, it would make LIFE Limited (total 8). The same happens for CABANA's eligibility
  criterion under the literal C1 reading. A separate count of SI defects, or SI on a 0–3 scale, would avoid this.
- **D3. The hypertension switch trials re-enter (ALLHAT, ASCOT-BPLA, VALUE; ONTARGET with TZ.b).**
  - Section 11.3 says TZ.c ≥50% caps at Moderate "regardless of total". That is what happens here.
  - v19 excluded these trials, and Heyard 2024 names discontinuation at randomisation as the strongest divergence source.
  - Please confirm that Moderate is intended, rather than Limited for TZ.c ≥50% combined with FU.a.
- **D4. The placebo-proxy rule turns on the EL point.**
  - LEADER, SUSTAIN-6 and CANVAS are Limited because a risk-enrichment criterion is omitted (EL 1). EMPA-REG, TECOS and
    CARMELINA represent their enrichment and stay Moderate.
  - SUSTAIN-6 depends entirely on C1.
  - This is a defensible consequence of section 6, but the user should know the line.
- **D5. Two LLM runs are not two raters.** The κ values are between two runs of one model (framework 7.1). All 36
  adjudicated points plus the items at 2 need clinician review (section 10).

## 7. Framework clarifications needed (v2.0.1)

For each case the more severe score was applied (7.4.3). "Tier changes" lists the trials whose adjudicated tier would
change under the alternative reading (`alt_tiers.csv`).

| ID | Ambiguity | Applied now (more severe) | Proposed clarification | Tier changes under the alternative |
|---|---|---|---|---|
| **C1** | An *undocumented* omitted or approximated code-defined population criterion (risk enrichment, a disease route, a risk score). Section 5 row 1 says SI "type 4–5", but types 4–5 list numeric bounds and gate mechanics. The EL anchors list "risk enrichment not applied" by type. The literal reading makes the undocumented deviation cost the same as or less than the documented one (SUSTAIN-6 vs LEADER). | EL, scored once, uniformly in 15 trials: ROCKET-AF, RE-LY, EAST-AFNET 4, CABANA, PROTECT AF, ACTIVE W, ALLHAT, VALUE, ASCOT-BPLA, ONTARGET, SUSTAIN-6, DECLARE, CANVAS, EMPEROR-Preserved, AMPLIFY. (PRECISION kept in SI: both raters had EL 0.) | Score a population criterion in EL whether or not it is documented. Use SI only for numeric bounds, gate mechanics and code errors, and add 1 SI point when the omission is also undocumented. Alternatively, state that SI applies and give the SI share check (1 − DC-EL-met). | Literal SI reading, shares unknown: ROCKET-AF Moderate→Good; RE-LY Moderate→Good; EAST-AFNET 4 Moderate→Good; **SUSTAIN-6 Limited→Moderate (enters)**. If those SI shares then prove >20%: **ALLHAT, ASCOT-BPLA, ONTARGET, VALUE Moderate→Limited (leave)**; PRECISION Good→Moderate. |
| **C2** | TZ.c share denominator when only one arm stops the baseline drug (ACTIVE W: 77% on OAC; ~38% of randomised patients actually stopped it) | 77% → TZ 2 → Limited | Define the share as the proportion of randomised patients on the drug at entry when either arm's protocol stops it, or as the proportion who actually stopped. If the latter, score the continuing-user half under the EL experienced-subgroup anchor. | ACTIVE W Limited→Moderate (enters). Under the "actually switched" reading, the EL experienced-subgroup anchor may still give EL 2 and keep it Limited. |
| **C3** | HF hospitalisation counted from I50 in any diagnosis position, in HF-gated or HF-prevalent cohorts, as an SI type-6 persisting-code defect (the framework names only AMPLIFY) | SI 1 provisional (EAST-AFNET 4, PARADIGM-HF, EMPEROR-Preserved, DECLARE) | Name it explicitly as SI type 6 with a data check: share of first HF events whose stay lacks a primary-billing I50 (`PRIMARY_BILLING`, trial_specs L451). RAFT-AF, where it is documented, stays in OU. | EAST-AFNET 4 Moderate→Good |
| **C4** | Combining SI defects on different denominators (patients vs events) | Higher of the per-denominator scores (both raters' values) | State it: either the maximum, or the sum capped at 2 | Sum: PARADIGM-HF, EMPEROR-Preserved, DECLARE SI→2; no tier change |
| **C5** | CABANA TZ.d (documented prior-AAD allowance in the ablation arm) and SI type 7 (dedupe): one deviation or two | Both kept (both raters) | Name CABANA in one place only, or state that TZ.d is the documented stage difference and SI the code error | None now (Limited by the SI rule); matters after a rebuild |
| **C6** | Whether the new-user exclusion of an experienced subgroup (EL anchor) stacks with a second criterion to reach EL 2 | Stacks (ROCKET-AF, RE-LY EL 2) | State whether the experienced-subgroup point counts as a criterion for the "two or more" rule | ROCKET-AF Moderate→Excellent; RE-LY Moderate→Good. With C7 too: both Excellent |
| **C7** | ES.b "specific mechanism documented" without DC-ES-cross: secular warfarin→DOAC replacement | ES 1 provisional (ARISTOTLE, ROCKET-AF, RE-LY, FRAIL-AF, AMPLIFY) | Require DC-ES-cross before freeze, or state that a general secular trend is not "documented" | None alone (see C6) |
| **C8** | ≥90%-met rule by clinical reasoning when a trial's risk list is narrower than the framework example (RE-LY: under 65 only stroke/TIA, EF <40 or HF qualify) | Not met → EL 2 provisional | Run DC-EL-met for every risk-enrichment criterion that the ≥90% rule is used to waive | RE-LY Moderate→Good |
| **C9** | Materiality of an omitted exclusion that is not population-defining (PROTECT AF warfarin eligibility vs LAAO selected for bleeding risk; AMPLIFY cancer with planned LMWH) | Material → EL point, provisional | Give a materiality threshold (e.g. a DC-EL-met-type share >10%) | PROTECT AF Moderate→Good |
| **C10** | DA.a "applies by design (an EF-defined trial)" when EF-unknown patients must carry a phenotype code (EMPEROR-Preserved, I503) | DA 1 provisional (the parenthetical decides) | Say whether a code requirement for EF-unknown patients removes DA.a | None |

Two further text-decided points need wording fixes but were not ambiguous:
- **NP thresholds** are numeric bounds on a measurable lab (NT-proBNP is in OMOP gold), so they go to SI type 4. Rater
  A's "not available" was factually wrong. The RAFT-AF anchor ("NT-proBNP not available") should say "documented as not
  applied".
- **COMET washout.** `TRIAL_CRITERIA_CHECK.md` says the protocol "deliberately adopted no washout". The adapted protocol
  actually defers it. One of the two documents should be corrected.

## 8. Provisional scores to resolve before freeze (framework 7.6)

Tier-changing provisional scores, with the check that would settle each one:

| Trial | Item | Check | Tier now → possible |
|---|---|---|---|
| RE-LY | EL 2p | DC-EL-met for the RE-LY risk list (C8) | Moderate → Good / Excellent |
| EAST-AFNET 4 | EL 1p, SI 1p | DC-EL-met (CV-risk); DC-SI-hf-anyposition (C3) | Moderate → Good |
| PROTECT AF | EL 2p | Share with prior bleeding or an OAC-contraindication code (C9) | Moderate → Good |
| ACTIVE W | TZ 2p | C2 decision | Limited → Moderate |
| PARADIGM-HF | DA 1p, SI 1p | DC-DA-meas (EF measured share); NP-bound share; DC-SI-hf-anyposition | Moderate → Good |
| VALIANT | TZ 1p | Transcribe Pfeffer 2003 Table 1 ACEi-before-randomisation share | Moderate → Good if <30% |
| PRECISION | SI 1p | Check the trial's risk definition (Supplementary Appendix); then the share failing it | Good → Excellent / Moderate |
| PROVE IT-TIMI 22 | TS 1p | Practice-pattern evidence that atorvastatin starts after ACS are high-intensity (or dose from orders) | Moderate → Limited if not preserved |
| RAFT-AF | OU 1p | Any-position HF share among events | Good → Excellent / Moderate |
| AF-CHF, ELITE II | DA 1p | DC-DA-meas | Good → Excellent |

Provisional scores that do not change the tier:
- ES (ARISTOTLE, ROCKET-AF, RE-LY, FRAIL-AF, AMPLIFY): DC-ES-cross.
- EMPEROR-Preserved EL/DA/SI.
- SUSTAIN-6 and DECLARE SI.
- INSIGHT SI.
- AMPLIFY EL.

None of the data checks in framework 3.3 (`audits/emulation_quality_v2/data_checks/`) has been run. The bands used here
come from `audits/claude-v1-criteria/`.

## 9. Primary-analysis impact (computed after the scores above were fixed)

Paper 1 primary analysis:
- PS-Demo (P1) + 32 ECG PCs vs P1 base;
- main configuration (1:1 greedy matching, caliper 0.2, L2 C = 1);
- 58 held-out items;
- published cells (`audits/claude-v20-sens-primary32/restricted_cells.parquet`) and statistics (`sens_primary32.contrast_row`), unchanged.

Statistics:
- relative reduction: 4,000 bootstrap resamples, seed 20261001;
- sign-flip P: exact, one-sided;
- benchmark permutation: 20,000 draws.

**Gate passed.** Set (a) reproduces 11.4% (6.3–16.0), 22/32, P = .002, and 0.251 → 0.205, P = .008.

| Set | Trials | Mean \|SMD\| reduction (95% CI) | m58 base → ECG | % \|SMD\|<0.1 base → ECG; trials improved; P | \|Δ log HR\| base → ECG; trials closer; sign-flip P | Benchmark-permutation P |
|---|---|---|---|---|---|---|
| (a) Published 32 (v19) | 32 | 11.4% (6.3–16.0) | 0.142 → 0.126 | 49.8 → 55.0; 22/32; .002 | 0.251 → 0.205; 20/32; .008 | .26 |
| (b) New analysed set (v2.0) | 29 | 11.4% (5.7–16.1) | 0.128 → 0.113 | 54.4 → 59.9; 21/29; .001 | 0.228 → 0.178; 20/29; .005 | .15 |
| (c) New Excellent + Good | 8 | 7.2% (2.3–13.2) | 0.114 → 0.106 | 57.5 → 61.4; 6/8; .063 | 0.207 → 0.129; 7/8; .023 | .46 |
| (d) All 38 | 38 | 12.6% (7.8–16.6) | 0.138 → 0.120 | 51.4 → 57.2; 28/38; <.001 | 0.258 → 0.207; 25/38; .002 | .22 |

**Reading:**
- The balance result is unchanged on the v2.0 analysed set, and the agreement result is slightly stronger.
- The benchmark-permutation P stays non-significant in every set. So, as in paper 1, the agreement gain is not shown to be
  trial-specific.
- The Excellent + Good set has only 8 trials and is underpowered.
- These numbers were not used for any score.

## 10. Clinician review list (framework 7.5)

- **All 36 disagreements** in section 2, and the 4 same-score basis changes.
- **Items scored 2:**
  - EL: ROCKET-AF, RE-LY, PROTECT AF, COMET, EMPEROR-Preserved;
  - TZ: ACTIVE W, TRANSFORM-HF, ALLHAT, VALUE, ASCOT-BPLA;
  - TS: ACTIVE W;
  - CO (placebo proxy): EMPEROR-Preserved, EMPA-REG, LEADER, SUSTAIN-6, REWIND, DECLARE, CANVAS, TECOS, CARMELINA;
  - OU: FRAIL-AF, AMPLIFY, LODESTAR, PROVE IT;
  - SI: CABANA, LAAOS III, LIFE, AMPLIFY.
- **Placebo-proxy combination rule:**
  - Limited: LEADER, SUSTAIN-6, REWIND, DECLARE, CANVAS, EMPEROR-Preserved;
  - not triggered (other points = 2): EMPA-REG, TECOS, CARMELINA.
- **Within 1 point of a threshold, or with a tier-changing provisional score:**
  - the section 8 list;
  - LIFE, ALLHAT and ASCOT-BPLA at total 7, one point below 8;
  - CAROLINA and PRECISION at total 4.
- **Every SI defect, with band and proposed spec edit:** the `si_defects` list of each record. New spec versions only; no
  silent edits.

## 11. Code check: `scripts/v13_summarize.py` L212–215 (rater A note 18)

- **Not a bug.** The expression is `np.log(min(ci) if same_orientation else 1 / max(ci))`. `np.log` wraps the whole
  conditional expression (verified with `ast`: the call's argument is an `IfExp`).
- For COMET, the only trial with a flipped orientation, it returns log(1/0.93) and log(1/0.74), as intended.
- **No published number depends on this function.** In paper 1 (`paper.md`, `supplement.md`), estimate agreement and
  |Δ log HR| come from `scripts/v20/sens_primary32.per_trial`, which uses `rb ± 1.96·rs`. `rb` and `rs` come from
  `v13_common.bench`, which handles orientation correctly. `v13_summarize.agreement` is called only inside `v13_summarize.py` (v1.3-era outputs); no other script imports it.
- The benchmark transcription (BM.f) is unaffected.

## 12. What was and was not checked

- **Checked:**
  - every disputed item against the framework text;
  - `trial_specs.py` notes and gates at 7fff3d9;
  - `build_trial_cohort.py` and `extract_outcomes.py` logic;
  - eTable 1 design notes, the COMET adapted protocol, the data-check bands, and `DATA_SOURCES.md` (NT-proBNP).
- **Publication facts verified only from memory or secondary sources** (marked provisional where they matter):
  - VALIANT ACEi share (~40%, secondary summary);
  - PRECISION risk definition (secondary sources disagree on the risk-factor count);
  - EMPEROR-Preserved structural-heart-disease criterion (rater A).
  - The primary full texts were not retrieved (NEJM blocked).
- **Not done:** no new data check was run, and no score used any result. The framework, specs and other files were not
  edited.
