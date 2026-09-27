# v1.7 candidate trials (confirmation set): screen and selection

2026-09-27. This implements `docs/v16/V17_CONFIRMATION_PLAN.md` section B. The companion `candidates.json` is keyed by trial.

## Blinding
No propensity score, matching, balance, SMD or hazard ratio has been computed for any trial in this file.

Screening used counts only:
- persons per arm;
- persons per arm with an ECG in [index−365 d, index];
- primary-composite events and deaths within the trial horizon, **pooled across arms**;
- patient overlap with the 18 v1.6 cohorts.

The pooled event counts come from `scripts/v17/screen_feasibility.py`:
- It uses the event rules of `extract_outcomes.py` v1.2.
- It is given no arm column and writes no per-patient outcome.
- It is run on cohorts built by the registered `build_trial_cohort.py` specs (`scripts/trial_specs.py`, `V17`).

The screen's working directories are under `/mnt/raid0/rbc58/ecg-tte/audits/claude-v17-screen/`.

## Selection rule
A trial is selected only if all of the following hold:
1. It is an active-comparator CV RCT emulable with new-user or sequential-switch designs. RCT-DUPLICATE proxies are allowed: DPP-4i or sulfonylurea as the placebo proxy.
2. Its smaller arm has ≥ 300 persons with an ECG in the window.
3. It has ≥ 50 pooled primary events within the horizon among ECG-covered persons.
4. It is not a near-duplicate of a v1.6 cohort: < 80% of its (patient, index date) records may be identical to any single v1.6 trial cohort.
5. It has not been analysed before.

Rules 1–3 and 5 were fixed before the screen. Rule 4 was added after the count-only screen showed that ACCOMPLISH reuses 96% of the ALLHAT records. No result informed it.

Overlap of 50–80% is flagged for the blinded rater and for sensitivity analysis, but does not exclude a trial.

## Selected for build (15)

| key | registry | arms (ours) | RCT HR (CI) | horizon (mo) | n per arm (with ECG) | pooled events w/ ECG | max same-record share |
|---|---|---|---|---|---|---|---|
| leader | leader | liraglutide vs dpp4i | 0.87 (0.78–0.97) | 46 | liraglutide 994 (453) / dpp4i 6,077 (3,329) | 794 | 0.58 (empa-reg) **flag** |
| sustain6 | sustain6 | semaglutide vs dpp4i | 0.74 (0.58–0.95) | 25 | semaglutide 3,690 (1,701) / dpp4i 3,444 (2,026) | 410 | 0.32 (empa-reg) |
| rewind | rewind | dulaglutide vs dpp4i | 0.88 (0.79–0.99) | 65 | dulaglutide 3,607 (1,335) / dpp4i 11,135 (4,714) | 1158 | 0.27 (empa-reg) |
| declare | declare | dapagliflozin vs dpp4i | 0.83 (0.73–0.95) | 50 | dapagliflozin 3,992 (2,102) / dpp4i 12,184 (4,865) | 1811 | 0.35 (empa-reg) |
| canvas | canvas | canagliflozin vs dpp4i | 0.86 (0.75–0.97) | 43 | canagliflozin 1,645 (485) / dpp4i 13,666 (5,552) | 928 | 0.31 (empa-reg) |
| tecos | tecos | sitagliptin vs sulfonylurea | 0.98 (0.88–1.09) | 36 | sitagliptin 2,720 (1,513) / sulfonylurea 2,653 (1,412) | 630 | 0.36 (empa-reg) |
| carmelina | carmelina | linagliptin vs sulfonylurea | 1.02 (0.89–1.17) | 26 | linagliptin 1,261 (803) / sulfonylurea 1,411 (743) | 313 | 0.31 (carolina) |
| valiant | valiant | arb vs acei | 1.00 (0.90–1.11) [0.975] | 25 | arb 1,033 (669) / acei 1,969 (1,427) | 253 | 0.61 (ontarget) **flag** |
| insight | insight | nifedipine vs thiazide | 1.10 (0.91–1.34) | 42 | nifedipine 907 (397) / thiazide 19,101 (8,450) | 1211 | 0.63 (allhat) **flag** |
| affirm | affirm | antiarrhythmic vs rate_control | 1.15 (0.99–1.34) | 42 | antiarrhythmic 4,606 (4,100) / rate_control 18,424 (13,534) | 4874 | 0.25 (east-afnet4) |
| af_chf | af-chf | antiarrhythmic vs rate_control | 1.06 (0.86–1.30) | 37 | antiarrhythmic 1,412 (1,272) / rate_control 5,648 (4,286) | 1130 | 0.21 (east-afnet4) |
| precision | precision | celecoxib vs naproxen | 0.93 (0.76–1.13) | 34 | celecoxib 6,342 (2,440) / naproxen 7,649 (2,870) | 511 | 0.02 (value) |
| amplify | amplify | apixaban vs warfarin | 0.84 (0.60–1.18) | 6 | apixaban 5,490 (4,068) / warfarin 1,395 (1,012) | 980 | 0.01 (aristotle) |
| lodestar | lodestar | rosuvastatin vs atorvastatin | 1.06 (0.86–1.30) | 36 | rosuvastatin 16,895 (10,954) / atorvastatin 18,137 (11,323) | 5103 | 0.09 (ontarget) |
| prove_it | prove-it | atorvastatin vs pravastatin | 0.84 (0.74–0.95) | 24 | atorvastatin 4,668 (3,848) / pravastatin 714 (531) | 1116 | 0.35 (plato) |

Benchmarks were read from the primary-paper abstracts, retrieved as PubMed E-utilities text on 2026-09-27. Citations and PMIDs are in `candidates.json` and in `trial_specs.PUBLISHED`.

### Emulation caveats for the rater
These are design-level caveats only:
- **Placebo-controlled trials with active-comparator proxies.** LEADER, SUSTAIN-6, REWIND, DECLARE and CANVAS use DPP-4i. TECOS and CARMELINA use a sulfonylurea. RCT-DUPLICATE found the sulfonylurea proxy less reliable.
- **Strategy trials.** AFFIRM and AF-CHF are emulated with the EAST-AFNET 4 sequential add-on design.
- **Class adaptations.** VALIANT uses ARB vs ACEi; INSIGHT uses nifedipine vs thiazide class. Dose is not identifiable for PROVE IT (atorvastatin 80 vs pravastatin 40).
- **Components not captured.** LODESTAR and PROVE IT omit coronary revascularisation from the composite; ACCOMPLISH would have too.
- **AMPLIFY outcome.** Recurrent VTE is taken as a new inpatient stay with a VTE code after the index stay, which has low specificity.
- **Patient overlap.** The DPP-4i-comparator trials share comparator patients with each other and with EMPA-REG. AFFIRM contains most of the EAST-AFNET 4 records.

## Screened, not built

| key | reason | RCT HR (CI) | citation |
|---|---|---|---|
| savor | smaller arm with ECG = 101 < 300 [not_built] | 1.00 (0.89–1.12) | Scirica et al. NEJM 2013;369:1317-26 (PMID 23992601) |
| tosca_it | smaller arm with ECG = 96 < 300 [not_built] | 0.96 (0.74–1.26) | Vaccaro et al. Lancet Diabetes Endocrinol 2017;5:887-97 (PMID 28917544) |
| accomplish | near-duplicate cohort: 96% of (patient, index) records identical to v1.6 allhat [not_built] | 0.80 (0.72–0.9) | Jamerson et al. NEJM 2008;359:2417-28 (PMID 19052124) |
| euclid | smaller arm with ECG = 153 < 300 [not_built] | 1.02 (0.92–1.13) | Hiatt et al. NEJM 2017;376:32-40 (PMID 27959717) |
| isar_react5 | smaller arm with ECG = 245 < 300 [not_built] | 1.36 (1.09–1.7) | Schupke et al. NEJM 2019;381:1524-34 (PMID 31475799) |
| cares | smaller arm with ECG = 161 < 300 [not_built] | 1.03 (—–1.23) | White et al. NEJM 2018;378:1200-10 (PMID 29527974); one-sided 98.5% upper bound only |
| fast | smaller arm with ECG = 94 < 300 [not_built] | 0.85 (0.7–1.03) | Mackenzie et al. Lancet 2020;396:1745-57 (PMID 33181081); on-treatment primary |
| oral_surv | smaller arm with ECG = 87 < 300; pooled events with ECG = 40 < 50 [not_built] | 1.33 (0.91–1.94) | Ytterberg et al. NEJM 2022;386:316-26 (PMID 35081280) |
| pronounce | smaller arm with ECG = 126 < 300 [not_built] | 1.28 (0.59–2.79) | Lopes et al. Circulation 2021;144:1295-307 (PMID 34459214) |
| ideal | smaller arm with ECG = 151 < 300 [not_built] | 0.89 (0.78–1.01) | Pedersen et al. JAMA 2005;294:2437-45 (PMID 16287954) |
| paradise_mi | v1.3 ext queue FAILED_FEASIBILITY: smaller arm (sacubitril/valsartan) with ECG = 296 < 300 (cohort 356 ARNI / 1,375 ACEi) [not_built] | 0.90 (0.78–1.04) | Pfeffer et al. NEJM 2021 (PMID 34758252) |
| dcp | v1.3 ext queue FAILED_FEASIBILITY: smaller arm (chlorthalidone switchers) with ECG = 255 < 300 (cohort 441 / 1,764) [not_built] | 1.04 (0.94–1.16) | Ishani et al. NEJM 2022 |
| invest | v1.3 ext queue FAILED_FEASIBILITY: smaller arm (verapamil) with ECG = 224 < 300 (cohort 316 / 1,234) [not_built] | 0.98 (0.9–1.06) | Pepine et al. JAMA 2003 |
| paragon_hf | built 2026-09-24 and analysed (phase-1 balance and phase-2 HR); results seen, so not a blind confirmation trial [excluded_previously_analysed] | — | — |
| dapa_hf | DAPA-HF/EMPEROR-Reduced DPP-4i design built and analysed 2026-09-24 (phase 1 and 2); results seen [excluded_previously_analysed] | — | — |
| partner | built and analysed 2026-09-24; results seen [excluded_previously_analysed] | — | — |
| dionysos | built and balance-analysed 2026-09-24; outcome not emulable [excluded_previously_analysed] | — | — |
| triton | 2026-09-24 FAILED_FEASIBILITY: smaller arm with ECG = 278 [not_built] | — | — |
| engage_af | v1.3: edoxaban arm 70 after gates (edoxaban ~150 persons ever ordered) [not_built] | — | — |
| castle_af | v1.3: ablation arm 149 after gates [not_built] | — | — |
| topcat | placebo-controlled with no accepted active-comparator proxy for spironolactone in HFpEF [not_screened] | — | — |
| hope3 | placebo-controlled polypill/statin primary prevention; no active comparator [not_screened] | — | — |
| credence | primary endpoint renal (ESKD, doubling of creatinine); CANVAS covers canagliflozin vs DPP-4i [not_screened] | — | — |
| devote | degludec vs glargine not identifiable: generic insulin orders carry the token 'insulin' only [not_screened] | — | — |
| averroes | aspirin largely OTC; trial population = VKA-unsuitable, not identifiable [not_screened] | — | — |
| race | no HR reported for the primary endpoint (absolute difference); AFFIRM/AF-CHF cover the question [not_screened] | — | — |
| empa_reg_emperor_reduced_alt | EMPEROR-Reduced/DELIVER re-use SGLT2i cohorts already analysed (DAPA-HF, EMPEROR-Preserved) [not_screened] | — | — |

## Why PARADISE-MI, DCP and INVEST were not among the 18
The v1.3 extension queue (`audits/claude-v13-ext-queue.sh`) built all three trials to the baseline, panel and ECG-selection stage. It then stopped each at the pre-declared gate of a smaller arm with an ECG ≥ 300:

| Trial | Smaller arm with ECG | Cohort size (smaller / larger arm) |
|---|---|---|
| PARADISE-MI | 296 | 356 ARNI / 1,375 ACEi |
| DCP | 255 | 441 chlorthalidone switchers / 1,764 HCTZ continuers |
| INVEST | 224 | 316 verapamil / 1,234 atenolol |

None of the three went on to BCL, CLMBR, the grid or outcomes.

None can be completed under the same gate without changing an eligibility rule that mirrors the trial:
- PARADISE-MI: the MI window, EF, eGFR, K and SBP rules all mirror the trial.
- DCP: the age ≥ 65 rule and the switch design mirror the trial.
- INVEST: the verapamil arm has only 316 initiators in total.

They are therefore not candidates for v1.7.

## Previously analysed trials excluded
PARAGON-HF, DAPA-HF/EMPEROR-Reduced (DPP-4i design), PARTNER and DIONYSOS were built on 2026-09-24. They have phase-1 balance results and, except DIONYSOS, phase-2 HRs. Their results have been seen, so they are not blind confirmation trials.

