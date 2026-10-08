# Version 1 trial-criteria check: the R2 blind re-audit must-fix list, tested against the data

Date: 2026-10-08. Scope: version 1 (paper 1 = `docs/paper/paper.md`). Input list: `git show r2:docs/r2/QUALITY_R2.json`
(`mustfix_all`, `consensus_mustfix`), 17 flagged trials. Code: `scripts/v1_criteria_check/`. Aggregate outputs:
`/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-criteria/`. No spec, cohort, paper or existing file was changed. Everything
below is a proposal for the user.

## Plain-language summary

- **Not present.** Three flagged problems are not in the analysed data.
  - **COMET metoprolol arm.** It does not include metoprolol succinate. The analysed roster is the JDAT roster, and every
    metoprolol-arm patient has a tartrate-named order on the index day. The auditors read the `trial_specs` 'comet'
    entry, which is used only for prognostic features.
  - **ELITE II and VALIANT ARB arms.** Sacubitril-valsartan does not enter them. In OMOP gold, ARNI orders are coded
    'sacubitril' or 'entresto', not 'valsartan'.
- **Major (design or outcome level, or more than 20% of the cohort affected).** Seven trials.
  - **CABANA:** arm assignment by the earliest index date.
  - **TRANSFORM-HF:** time zero is the in-hospital loop order, not the discharge strategy.
  - **AMPLIFY:** the recurrent-VTE outcome is mostly persisting codes. 91% of events disappear when a primary
    hospital-billing VTE code is required. This is not disclosed in paper 1.
  - **LAAOS III:** 57% of patients have their first AF code in the index surgical stay.
  - **COMET:** there is no LVEF restriction. 39% of the cohort has a latest EF above 35%.
  - **VALIANT:** 59% of patients have neither documented LV dysfunction nor HF.
  - **LIFE:** 22% of patients qualify only through hedged LVH statements (minimal voltage, "may be normal variant",
    "possible"). Negated statements are practically absent (fewer than 11 patients).
- **Moderate (5–20%).** CAROLINA age bounds (12%). GLP-1RA/SGLT2i washouts in SUSTAIN-6 (9%), CANVAS (8%), REWIND (5%)
  and DECLARE (12%, with saxagliptin/alogliptin). COMET prior or concurrent succinate exposure (15%).
- **Minor (under 5%).** LEADER washout (2%). EMPEROR-Preserved saxagliptin/alogliptin (1%). ELITE II prior ARNI (4%).
  LODESTAR and PROVE IT revascularisation; this omission is already disclosed.
- **Paper 1's primary result holds with every exclusion-type fix applied at once.**
  - Mean |SMD| reduction: **12.2% (95% CI 7.1–16.7)**, vs **11.4% (6.3–16.0)** as published.
  - |Δ log HR| vs RCT: **0.249 → 0.210 (P = .018)**, vs 0.251 → 0.205 (P = .008) as published.
  - Dropping the proposed design-level Major trials gives 10.7% (5.5–15.6). Dropping all seven Major trials gives 9.7%
    (3.9–15.0); the ECG still improves both endpoints.
- **Per-trial effect of each fix.** Changes in |Δ log HR| were mostly within the range seen when the same number of
  patients is removed at random. The fixes matter for emulation validity, not for the ECG conclusion.
- **Index-day ECGs.** Same-day ECGs are acceptable by design (user decision). For disclosure, the share of analysed
  patients whose selected ECG is on the index day ranges from 15% to 62% (median 37%, pooled 40%, in S32).

## Summary table (one row per issue)

| Trial | In S32 | Issue | Classification | Proposed action |
|---|---|---|---|---|
| CABANA | yes | Earliest-index dedupe assigns later-ablation patients to the AAD arm | PRESENT-MAJOR (design) | Downgrade to Limited, or rebuild as sequential design |
| LAAOS III | yes | AF first coded in the index surgical stay | PRESENT-MAJOR (56.6%) | Rebuild requiring AF before admission; Limited until rebuilt |
| COMET | yes | Succinate in the metoprolol arm | NOT PRESENT | None |
| COMET | yes | Prior or concurrent succinate exposure (related) | PRESENT-MODERATE (15.1%) | Succinate washout as primary; disclose |
| COMET | yes | No LVEF restriction | PRESENT-MAJOR (38.7%) | Restrict to EF ≤35% (unknown passes), or downgrade |
| TRANSFORM-HF | yes | Time zero / washout not anchored to discharge strategy | PRESENT-MAJOR (design) | Downgrade to Limited |
| ELITE II | yes | ARNI enters the ARB arm via 'valsartan' | NOT PRESENT | None |
| ELITE II | yes | Prior ARNI use (related) | PRESENT-MINOR (4.0%) | Keep; optional exclusion; disclose |
| EMPEROR-Preserved | yes | Saxagliptin/alogliptin in the DPP-4i comparator | PRESENT-MINOR (1.3%) | Keep; disclose |
| LIFE | yes | Hedged or negated ECG-LVH statements | PRESENT-MAJOR (21.7%) | Rebuild with a definite-LVH gate; Limited until rebuilt |
| VALIANT | yes | ARNI enters the ARB arm via 'valsartan' | NOT PRESENT | None |
| VALIANT | yes | EF unknown without HF; index-day echo ignored | PRESENT-MAJOR (58.7%) | Downgrade to Limited, or rebuild (40% retained) |
| CAROLINA | yes | Age 40–85 bound missing | PRESENT-MODERATE (11.6%) | Apply the age bound as primary |
| LEADER | yes | Other GLP-1RA not washed out | PRESENT-MINOR (2.1%) | Keep; apply in any rebuild |
| SUSTAIN-6 | yes | Other GLP-1RA not washed out | PRESENT-MODERATE (8.7%) | Washout as primary |
| REWIND | no (Limited) | Other GLP-1RA not washed out | PRESENT-MODERATE (5.1%) | Already Limited; apply washout |
| DECLARE-TIMI 58 | no (Limited) | SGLT2i washout; saxagliptin/alogliptin | PRESENT-MODERATE (12.0%) | Already Limited; apply fixes |
| CANVAS | yes | Other SGLT2i not washed out | PRESENT-MODERATE (7.9%) | Washout as primary |
| AMPLIFY | yes | Recurrent VTE = any VTE code on a later stay | PRESENT-MAJOR (outcome; undisclosed) | Re-specify the outcome (primary-billing VTE) or Limited; disclose |
| LODESTAR | yes | Revascularisation missing from the outcome | PRESENT-MINOR (disclosed) | Keep |
| PROVE IT-TIMI 22 | yes | Revascularisation ≥30 d missing | PRESENT-MINOR (disclosed) | Keep |

Machine-readable versions:
- `audits/claude-v1-criteria/classification.csv`;
- `criteria_counts.csv`, all flags, suppressed;
- `per_trial_fixes.csv`, `calibration.csv`, `pooled.csv`, `ecg_index_day.csv`, `life_lvh_categories.csv`.

## Methods

**Analysed cohort.** The analysed cohort is the patient set the engine analyses: completed covariates ∩ ECG embedding ∩
CLMBR embedding ∩ phenotypes ∩ panel, as in `v13_common.Trial`. Arms come from the trial's cohort roster (COMET: the JDAT
roster `claude-comet-progref-v1/roster`). For every trial, the flag file matches `T.keys` and `T.t` exactly; this is
asserted.

**Data, read in place, read-only:**
- OMOP gold:
  - drug tokens exactly as `trial_common.create_drug_tokens`;
  - condition, procedure and visit tables;
  - inpatient stays merged as in `extract_outcomes.py`.
- Echo metadata EF (5–90%), latest value in a window, as in `build_trial_cohort.py`.
- ECG metadata `Diagnosis`, LIFE only. This is the field the LIFE gate already uses. Only category counts are written.
- COMET JDAT medication buckets, from `comet-candidates-c2FSBqdW/report/restricted_candidates.sqlite`, written by
  `build_comet_candidates.py` with the same `classify()` rule as the roster.
- Outcome files.

**Re-analysis.** This is paper 1's primary analysis: PS-Demo (P1) base vs P1 + 32 ECG PCs, main configuration (1:1 greedy
matching, caliper 0.2 SD of the PS logit, L2 C = 1).
- Each cell is `E.run_cell` exactly as in `sens_primary32.task()`. A fix is a row subset: `rows=`, with the design
  rows as X.
- ECG PCs were **not** recomputed. `T.ecg_pc`, the unsupervised PCA on the full analysed cohort, is kept, as in the
  v1 audit's subset analyses. The existing code never refits PCs per subset.
- Outcome fixes (secondary) replace `T.y_t` / `T.y_e` on a copy of the trial object.

**Gate.** All 30 unchanged cells (15 trials × base/ECG) reproduce
`audits/claude-v20-sens-primary32/restricted_cells.parquet` exactly. The maximum |deviation| is **0.0** over loghr, se,
n, n_t, n_c, n_pairs and all 58 SMDs, with 0 NaN mismatches (`gate.csv`). The pooled computation on the published cells
reproduces 11.407% (6.311–15.977) and 0.2508 → 0.2051, P = .0084.

**Random-removal calibration** (`calibration.csv`). For each fix, the same number of patients per arm was removed at
random 30 times. A per-trial change counts as noticeable only if it falls outside the 5th–95th percentile of these random
changes. The check is needed because matching makes per-trial |Δ log HR| unstable.

**Classification rule (task brief).**
- NOT PRESENT: the issue does not occur in the analysed data.
- MINOR: under 5% of the analysed cohort affected, and negligible impact.
- MODERATE: 5–20% affected, or a noticeable impact.
- MAJOR: over 20% affected, or a design-level time-zero / arm-assignment / outcome error that exclusion cannot fix.

**Suppression.**
- Counts of 1–10 are shown as "<11".
- When one arm's count is 1–10, the total is shown only as a rounded percentage, and retained n is not shown.
- Redundant nested flags whose differences would reveal a count of 1–10 were dropped from the published tables.

## Per-trial results

Abbreviations:
- m58: mean |SMD| over the 58 held-out items, in the matched sample.
- |Δ|: |log HR − RCT log HR|.
- "base → +ECG": P1 base and P1 + ECG.
- "within noise": the change lies inside the random-removal 90% range.

### CABANA (S32; v19 tier Moderate)

| Item | Value |
|---|---|
| Issue (auditor B) | Earliest-index dedupe assigns eventual-ablation patients to the AAD arm |
| Present? | **Yes, but not "most"** |
| Aggregate attrition | Dedupe removed 1,378 of 3,427 eligible ablation records (40%). These people had an earlier qualifying AAD start. |
| Analysed cohort (1,573 ablation / 11,560 AAD) | 11.0% of the AAD arm have a later ablation (9.0% within the 49-month horizon; 5.3% within 1 year). 44.6% of all analysed patients with an ablation on or after their index are in the AAD arm. 21.4% of the ablation arm had an AAD order in the prior 365 days, which the design allows. |
| Why it matters | The ablation arm contains only people without an in-window AAD start. These are people whose AAD started before 2013, or who never had one. So the arms differ in disease stage at time zero. Crossover to ablation in the AAD arm is 9% within the horizon (the RCT had about 27.5%). Excluding the later-ablated would condition on the future, so exclusion cannot fix this. |
| Impact | Not re-run (design-level) |
| Classification | **PRESENT-MAJOR** (design-level arm assignment) |
| Proposed action | Downgrade to Limited, or rebuild with the sequential design (auditor B: `switch_seq`, `arm0_procedure`). The outcome-footnote mismatch from the v1 audit also stands. |

### LAAOS III (S32; v19 tier Good)

| Item | Value |
|---|---|
| Issue (B) | The AF gate admits AF first coded during the index surgical stay |
| Present? | **Yes** |
| % affected | **56.6%** of patients have their first-ever I48 code dated within the index inpatient stay. This is 23.1% of the LAAO arm and 64.7% of comparators, so it is strongly differential. Under the auditor's literal rule (first I48 on or after index − 1 day) the figure is 33.0%. |
| Why the date cannot separate pre-op from post-op AF | 89% of hospital-billing diagnoses in the index stays are dated at the admission date, and 93.5% of the in-stay first-AF codes fall on the admission date. A post-operative AF coded at discharge therefore carries a date before surgery and passes the "on or before index" gate. |
| Impact (fix = AF before the index admission; 1,137 retained, 43.4%) | m58 0.127 → 0.149 (base) and 0.131 → 0.111 (+ECG). Base \|Δ\| 0.337 → 0.064; +ECG \|Δ\| 0.143 → 0.076. All within noise for removing 57% of patients. |
| Classification | **PRESENT-MAJOR** (over 20%, differential) |
| Proposed action | Rebuild with an AF code before the index admission as the primary spec. Limited until rebuilt. |

### COMET (S32; v19 tier Good). Analysis roster = JDAT `claude-comet-progref-v1/roster`, not the `trial_specs` 'comet' entry

| Item | Value |
|---|---|
| Issue A1 | The metoprolol arm includes succinate ('toprol') |
| Present? | **NOT PRESENT.** All 2,633 analysed metoprolol-arm patients (100%) have a tartrate-named JDAT order (bucket `metoprolol_tartrate_candidate`) on the index day. The JDAT rule quarantines any name containing succinate, 'toprol' or an ER/XL marker. In OMOP gold, 'toprol' orders in [index − 365, index] number <11 in each arm. The 'toprol' token sits only in the `trial_specs` prognostic-feature entry. This confirms the user's belief and the coordinator's finding. |
| Related, present | Succinate-named JDAT orders in [index − 365, index]: 19.5% of the metoprolol arm vs 12.0% of the carvedilol arm (15.1% overall). On the index day: 2.6% vs 0.4%. Any time before index: 29.7% vs 20.2%. Days 1–90 after index: 12.3% vs 3.1%. So the tartrate arm includes prevalent beta-blocker users and switchers; the COMET protocol deliberately adopted no washout. |
| Impact (succinate washout; 5,418 retained, 84.9%) | m58 0.143 → 0.147 (base), 0.111 → 0.117 (+ECG). \|Δ\| 0.007 → 0.051 (base), 0.038 → 0.030 (+ECG). All within noise. |
| Classification | **PRESENT-MODERATE** (15.1%) |
| Proposed action | Succinate washout as the primary spec; disclose |
| Issue A2 | No LVEF restriction (RCT required EF ≤35%) |
| Present? | **Yes.** The roster rule is "HF code OR latest EF < 40", by documented user decision (COMET_ADAPTED_PROTOCOL.md). EF was measured in [index − 365, index − 1] for 67.3%. Among the measured, **57.5% have EF > 35%**. That is **38.7% of the analysed cohort** (45.8% of metoprolol, 33.7% of carvedilol). 29.0% have EF ≥40%. |
| Impact (EF > 35% excluded; 3,910 retained, 61.3%) | m58 0.143 → 0.132 (base) and 0.111 → 0.093 (+ECG); both improve beyond noise. \|Δ\| 0.007 → 0.088 (base), 0.038 → 0.039 (+ECG), within noise. With both COMET fixes (3,349 retained): \|Δ\| 0.060 (base), 0.111 (+ECG), within noise. |
| Classification | **PRESENT-MAJOR** (over 20%), although it is a documented adaptation |
| Proposed action | Restrict to EF ≤35% (unknown passes) as the primary COMET spec, or downgrade one or two tiers. User decision: the broader rule was chosen on 2026-09-21. |

### TRANSFORM-HF (S32; v19 tier Moderate; R2 tier D)

| Item | Value |
|---|---|
| Issue (A, B) | Time zero is the first loop-diuretic order, often in-hospital, not the discharge strategy. Torsemide switchers are excluded. The 12-month horizon differs from the RCT's 17.4-month median. |
| Present? | **Yes** |
| Quantified | 76.9% of furosemide-arm vs 46.6% of torsemide-arm index orders fall inside an inpatient stay. Furosemide route cannot be told apart in OMOP, so many are likely IV. Only 4.4% of index orders fall within 30 days after a discharge. Aggregate attrition: the washout removed 58% of first torsemide orders (9,518 → 4,019) because of a furosemide order in the prior 365 days; these are exactly the switchers TRANSFORM-HF randomised. HORIZON_MONTHS = 12. |
| Impact | Not re-run (design-level; needs a new discharge-anchored cohort with new encodes) |
| Classification | **PRESENT-MAJOR** (design-level time zero and arm assignment) |
| Proposed action | Downgrade to Limited, which excludes it from the primary set |

### ELITE II (S32; Good) and VALIANT (S32; Good)

| Item | ELITE II | VALIANT |
|---|---|---|
| Issue (A) | ARNI orders tokenised as 'valsartan' enter the ARB arm | same |
| Present? | **NOT PRESENT** | **NOT PRESENT** |
| Evidence | OMOP gold keeps the first word of the order name. ARNI orders are 'sacubitril' (concept 46275719) or 'entresto'. Only 0.03% of 'sacubitril' rows have a same-day 'valsartan' row. The literal 'sacubitril-valsartan' string occurs on the index day in <11 analysed ELITE II ARB patients. | Combined string: 0 |
| Related: ARNI order in [index − 365, index] | 4.0% (ARB 6.6%, ACEi 1.9%); index day: ARB 14 patients (1.0%) | about 1% (ARB 2.1%, ACEi <11) |
| Impact of the exclusion | 3,092 retained (96.0%). \|Δ\| base 0.269 → 0.157, +ECG 0.108 → 0.164 (within noise). Base m58 +0.011 is just outside noise. | \|Δ\| base 0.180 → 0.153, +ECG 0.218 → 0.144 (within noise) |
| Classification | PRESENT-MINOR (related issue) | PRESENT-MINOR (related issue) |
| Proposed action | Keep; optional ARNI exclusion; disclose | Keep |

**VALIANT, issue B:** post-MI patients with unknown EF and no HF are admitted, although the trial required LV dysfunction
and/or HF; the index-day echo is also ignored.
- **Present: 58.7%.**
  - 43.2% have no echo in [index − 365, index] and no I50 code on or before index.
  - Another 15.6% have a latest echo EF above 40% once the index-day echo is included.
  - Only 38.6% have any EF measured in that window.
- **Impact.** With all VALIANT fixes, 846 are retained (40.4%). |Δ| moves 0.180 → 0.622 (base) and 0.218 → 0.365 (+ECG).
  Both are within the random-removal range for dropping 60% of patients.
- **Classification: PRESENT-MAJOR.** Proposed action: downgrade to Limited, or rebuild requiring LVEF ≤40% or HF.

### EMPEROR-Preserved (S32; Moderate) and DECLARE-TIMI 58 (Limited; not in S32)

| Item | EMPEROR-Preserved | DECLARE-TIMI 58 |
|---|---|---|
| Issue | DPP-4i comparator includes saxagliptin/alogliptin | same, plus other SGLT2i not washed out |
| Present? | Yes | Yes |
| % affected | Saxagliptin/alogliptin in [index − 365, index]: 1.3% overall, 3.4% of the DPP-4i arm. All of these started saxagliptin/alogliptin on the index day. | Saxagliptin/alogliptin: 3.6% (5.1% of DPP-4i). Other SGLT2i: 8.8% (dapagliflozin 13.2%, DPP-4i 6.9%). Either: 12.0%. |
| Impact | 2,385 retained. \|Δ\| base 0.032 → 0.056 (just outside noise), +ECG 0.019 → 0.007 | 6,129 retained. \|Δ\| base 0.779 → 0.904 (outside noise), +ECG 0.492 → 0.484 |
| Classification | PRESENT-MINOR | PRESENT-MODERATE |
| Proposed action | Keep; apply in any rebuild; disclose | Already Limited; apply fixes |

### GLP-1RA / SGLT2i washouts: LEADER, SUSTAIN-6, REWIND, CANVAS

The issue: another GLP-1RA (or SGLT2i) order in [index − 365, index] was not excluded. The window includes the index day,
as the builder's `other_drugs_365d` does.

| Trial | In S32 | % affected (treated / DPP-4i) | Retained | m58 base → +ECG (unchanged → fixed) | \|Δ\| base, +ECG (unchanged → fixed) | Class |
|---|---|---|---|---|---|---|
| LEADER | yes | 2.1% (6.2% / 1.6%) | 3,702 | 0.146/0.171 → 0.188/0.149 | 0.423 → 0.380; 0.478 → 0.459 | PRESENT-MINOR |
| SUSTAIN-6 | yes | 8.7% (16.5% / 2.1%) | 3,404 | 0.160/0.147 → 0.174/0.162 | 0.407 → 0.405; 0.307 → 0.304 | PRESENT-MODERATE |
| REWIND | no (Limited) | 5.1% (15.2% / 2.2%) | 5,742 | 0.130/0.087 → 0.115/0.109 | 0.019 → 0.035; 0.073 → 0.062 | PRESENT-MODERATE |
| CANVAS | yes | 7.9% (14.4% / 7.3%) | 5,563 | 0.225/0.197 → 0.224/0.244 | 0.050 → 0.067; 0.095 → 0.086 | PRESENT-MODERATE |

All |Δ| changes are within noise. The LEADER base m58 change (+0.042) is just outside noise. Proposed action: make the
washout part of the primary spec (an exclusion only, so no new encodes are needed). No tier change: the impact is
negligible, and LEADER, SUSTAIN-6 and CANVAS are already Moderate.

For SUSTAIN-6, oral semaglutide ('rybelsus') was treated as the same molecule (auditor B's list).

### CAROLINA (S32; Good)

| Item | Value |
|---|---|
| Issue (A) | Age bound 40–85 missing |
| Present? | Yes |
| % affected | 11.6%: under 40 = 2.1%; over 85 = 9.5% (linagliptin 12.1%, glimepiride 11.1%) |
| Impact | 1,586 retained. \|Δ\| base 0.009 → 0.014, +ECG 0.076 → 0.055; m58 unchanged. All within noise. |
| Classification | PRESENT-MODERATE |
| Proposed action | Apply age 40–85 as the primary spec. No downgrade needed. |

### LIFE (S32; Moderate)

| Item | Value |
|---|---|
| Issue (A, B) | The ECG-LVH text gate matches hedged or negated statements |
| Present? | **Yes for hedged statements; negated statements practically absent** |
| Category frequency | Each analysed patient is classified by the strongest LVH statement in [index − 365, index], splitting `Diagnosis` into statements: definite 36.0%; voltage criteria 8.2%; probable 22.9%; consider 9.4%; other finding "possibly due to LVH" 1.9%; possible / cannot rule out / negated 7.8% (negated: <11 patients); minimal voltage / "may be normal variant" 13.9%. File: `life_lvh_categories.csv`. |
| % affected | **21.7%** qualify only through the auditors' hedged categories (A ∪ B: minimal voltage / normal variant, possible / cannot rule out, negated / no longer present). 32.9% under a strict rule that also drops "consider" and "possibly due to LVH". |
| Impact (A ∪ B fix; 2,452 retained) | m58 0.148 → 0.142 (base), 0.126 → 0.127 (+ECG). \|Δ\| 0.240 → 0.079 (base), 0.074 → 0.090 (+ECG). All within noise. |
| Classification | **PRESENT-MAJOR** by the over-20% rule, although exclusion can fix it |
| Proposed action | Rebuild the gate on definite-LVH statements (A ∪ B exclusion list, applied per statement) as the primary spec. Limited until rebuilt. |

### AMPLIFY (S32; Moderate)

| Item | Value |
|---|---|
| Issue (B) | Recurrent VTE counts any VTE code on a later stay, including persisting index-event codes |
| Present? | **Yes; it is the dominant source of events** |
| Quantified | 980 primary events within 6 months; 42% of them occur within 30 days of index. In only 7.1% of first event stays is a VTE code the primary hospital-billing diagnosis. Requiring a primary-billing VTE code on a stay after the index stay leaves **85 events (−91%)**. |
| Disclosure | Not disclosed. Paper 1 Table 1 notes disclose only the missing VTE-related death. |
| Impact (outcome fix, secondary) | \|Δ\| base 0.220 → 0.095, +ECG 0.153 → 0.084; balance unchanged by construction |
| Classification | **PRESENT-MAJOR** (outcome misclassification, design-level, undisclosed) |
| Proposed action | Re-specify the outcome as a primary-billing VTE stay ≥7 days after the index stay, or downgrade to Limited. Disclose in either case. |

### LODESTAR and PROVE IT-TIMI 22 (S32; Moderate)

| Item | LODESTAR | PROVE IT-TIMI 22 |
|---|---|---|
| Issue (A, B) | Coronary revascularisation missing from the composite | Revascularisation ≥30 days missing |
| Present? | Yes; **already disclosed** (paper.md Table 1 note) | Yes; **already disclosed** |
| Quantified | PCI/CABG after the index stay within 36 months: 6.1%. It would add an event for 3.2% and bring forward an event for 0.8%. Events 5,103 → 5,825 (+14%). | PCI/CABG at ≥30 days within 24 months: 5.0%. It would add or bring forward an event for about 2%. Events 1,116 → 1,193 (+7%). |
| Impact (outcome fix) | \|Δ\| base 0.030 → 0.032, +ECG 0.157 → 0.143 | \|Δ\| base 0.335 → 0.292, +ECG 0.240 → 0.222 |
| Classification | PRESENT-MINOR (disclosed) | PRESENT-MINOR (disclosed) |
| Proposed action | Keep; optional sensitivity with a procedure component | Keep |

## Pooled re-analysis (paper 1 primary)

S32 set (as in `sens_primary32`), main configuration, P1 + ECG vs P1 base:
- relative reduction in mean |SMD|, bootstrap CI with 4,000 resamples and seed 20261001;
- |Δ log HR| with a one-sided sign-flip P.

The exclusion-type fixes, applied simultaneously, are the "all" variants:
- COMET: succinate washout plus EF > 35% excluded;
- ELITE II: ARNI;
- VALIANT: ARNI, EF unknown without HF, and index-day EF > 40%;
- EMPEROR-Preserved: saxagliptin/alogliptin;
- LEADER, SUSTAIN-6, CANVAS: washout;
- CAROLINA: age;
- LAAOS III: AF before admission;
- LIFE: hedged statements (A ∪ B).

REWIND and DECLARE were fixed too but are not in S32.

| Analysis | Trials | Mean \|SMD\| reduction (95% CI) | m58 base → ECG | \|Δ log HR\| base → ECG | ECG better | Sign-flip P |
|---|---|---|---|---|---|---|
| Published cells (gate) | 32 | **11.4% (6.3–16.0)** | 0.142 → 0.126 | **0.251 → 0.205** | 20/32 | .008 |
| **All exclusion-type fixes** | 32 | **12.2% (7.1–16.7)** | 0.146 → 0.128 | **0.249 → 0.210** | 18/32 | .018 |
| Exclusion fixes + outcome fixes (AMPLIFY, LODESTAR, PROVE IT) | 32 | 12.2% (7.1–16.7) | 0.146 → 0.128 | 0.244 → 0.207 | 18/32 | .022 |
| S29: minus CABANA, TRANSFORM-HF, AMPLIFY (published cells) | 29 | 9.8% (4.2–14.7) | 0.138 → 0.125 | 0.223 → 0.181 | 18/29 | .013 |
| S29, remaining fixes applied | 29 | 10.7% (5.5–15.6) | 0.143 → 0.127 | 0.222 → 0.186 | 16/29 | .028 |
| S25: minus all seven proposed MAJOR (published cells) | 25 | 9.7% (3.7–15.0) | 0.139 → 0.125 | 0.228 → 0.191 | 16/25 | .029 |
| S25, remaining fixes applied | 25 | 9.7% (3.9–15.0) | 0.142 → 0.128 | 0.224 → 0.190 | 15/25 | .038 |

Fixing one trial at a time moves the relative reduction between 10.3% (CANVAS only) and 12.7% (LEADER only), and the
|Δ log HR| P between .004 and .016 (`pooled.csv`).

**Reading.** The balance result is unchanged or slightly stronger with the fixes. The emulation-agreement result is
slightly attenuated, with the ECG better in 18 rather than 20 of 32 trials, but it remains significant. Removing the
proposed Major trials lowers the balance gain to about 10%; the CI still excludes 0.

The pooled fixes are exclusion-only approximations of the rebuilt cohorts:
- ECG PCs are not refit.
- A full rebuild with restricted arm definitions could admit some patients at a later index. Examples: a later
  sitagliptin start after saxagliptin, or a later first GLP-1RA. Those patients would need new ECG and CLMBR encodes.

## Index-day ECG share (disclosure only)

Same-day ECGs are acceptable by design (user decision, 2026-10-08). The timestamp-ordering check in the original brief
was dropped. The table gives the share of analysed patients whose selected ECG (BCL selection `lag_days`) is on the index
day, at 1–30 days before index, and at 31–365 days before index (`ecg_index_day.csv`).

| Trial | S32 | Index day | 1–30 d | 31–365 d |
|---|---|---|---|---|
| COMET | yes | 16.5% | 64.5% | 19.0% |
| PARADIGM-HF (seq) | yes | 26.3% | 36.0% | 37.7% |
| TRANSFORM-HF | yes | 51.0% | 39.4% | 9.5% |
| ELITE II | yes | 38.4% | 41.6% | 20.0% |
| LIFE | yes | 44.0% | 27.2% | 28.8% |
| PLATO | yes | 62.0% | 33.7% | 4.3% |
| ARISTOTLE | yes | 42.1% | 39.0% | 18.9% |
| ROCKET-AF | yes | 40.7% | 36.9% | 22.5% |
| RE-LY | yes | 36.9% | 42.4% | 20.6% |
| ALLHAT | no | 40.2% | 29.2% | 30.7% |
| EMPEROR-Preserved | yes | 22.9% | 38.3% | 38.8% |
| EAST-AFNET 4 | yes | 40.7% | 35.8% | 23.5% |
| CABANA | yes | 55.1% | 28.6% | 16.4% |
| ONTARGET | no | 43.9% | 25.3% | 30.7% |
| VALUE | no | 41.0% | 25.9% | 33.1% |
| ASCOT | no | 44.4% | 26.5% | 29.1% |
| EMPA-REG | yes | 24.0% | 27.0% | 49.0% |
| CAROLINA | yes | 36.5% | 20.6% | 42.9% |
| LEADER | yes | 27.0% | 25.4% | 47.6% |
| SUSTAIN-6 | yes | 18.5% | 21.7% | 59.8% |
| REWIND | no | 26.2% | 23.0% | 50.8% |
| DECLARE-TIMI 58 | no | 29.6% | 26.3% | 44.2% |
| CANVAS | yes | 28.4% | 24.3% | 47.3% |
| TECOS | yes | 32.4% | 27.0% | 40.6% |
| CARMELINA | yes | 32.0% | 32.9% | 35.1% |
| VALIANT | yes | 54.4% | 38.3% | 7.3% |
| INSIGHT | yes | 38.2% | 22.3% | 39.5% |
| AFFIRM | yes | 36.7% | 30.9% | 32.4% |
| AF-CHF | yes | 38.3% | 32.6% | 29.1% |
| PRECISION | yes | 21.9% | 26.6% | 51.5% |
| AMPLIFY | yes | 15.3% | 66.9% | 17.8% |
| LODESTAR | yes | 49.9% | 28.5% | 21.6% |
| PROVE IT-TIMI 22 | yes | 56.4% | 40.3% | 3.3% |
| FRAIL-AF | yes | 22.3% | 39.7% | 37.9% |
| LAAOS III | yes | 61.1% | 26.1% | 12.8% |
| PROTECT AF | yes | 20.0% | 38.2% | 41.7% |
| RAFT-AF | yes | 34.1% | 27.7% | 38.2% |
| ACTIVE-W | yes | 38.5% | 39.6% | 21.9% |

S32: median 36.8% (range 15.3–62.0%); 39.7% pooled over patients. S38: median 37.6%, pooled 39.9%. The share is highest
in trials whose time zero is an in-hospital order or event (PLATO, LAAOS III, PROVE IT, CABANA, VALIANT, TRANSFORM-HF).

## Not checked, or checked only partly

- **Rebuilt cohorts.** Real rebuilds were not run: CABANA sequential design, TRANSFORM-HF discharge anchor, and a VALIANT
  rebuild that would admit patients at a later index. They need new cohort builds plus ECG and CLMBR encodes; the brief
  defers them. Their effect is described, not estimated.
- **VALIANT EF source.** EF comes from the echo metadata EF field, as in the cohort builder. The COMET roster used the
  JDAT echo table, so its EF classification may differ slightly from this check.
- **Clinical validity of the definitions used here.** The LIFE statement categories are keyword rules on templated ECG
  statements. The LAAOS III "first AF in index stay" uses merged inpatient stays. Neither has been reviewed by a
  clinician.
- **AMPLIFY outcome fix.** It requires a primary hospital-billing code. That is specific but probably insensitive: true
  recurrences coded in a secondary position are lost. A middle-ground definition (for example, a stay ≥7 days after the
  index stay with a VTE code plus a new anticoagulant or imaging order) was not built.
- **Grid coverage.** Only the main configuration and P1 were re-run, as the brief specifies. The full grid (P5, hdPS200,
  clinical; calipers, IPTW, GBM) and the paper 2 arms (CLMBR-T) were not.

## Files

- Code (`scripts/v1_criteria_check/`):
  - `common.py`
  - `s1_keys.py`: analysed keys; index-day ECG share
  - `s2_flags.py`: criterion flags and counts
  - `s3_reanalysis.py`: gate, per-trial and pooled re-analysis
  - `s4_calibration.py`: random-removal ranges
  - `s5_classification.py`
- Aggregate outputs (`/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-criteria/`):
  - `criteria_counts.csv`, `life_lvh_categories.csv`, `ecg_index_day.csv`;
  - `gate.csv`, `per_trial_fixes.csv`, `calibration.csv`, `pooled.csv`, `classification.csv`.
- Restricted files (never commit):
  - `keys/restricted_keys_*.parquet`
  - `flags/restricted_flags_*.parquet`
  - `flags/restricted_criteria_counts_raw.parquet`
  - `restricted_fix_cells.parquet`
  - `restricted_fix_meta.parquet`
