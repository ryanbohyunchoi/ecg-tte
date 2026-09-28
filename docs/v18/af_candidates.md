# v1.8 AF candidate trials (Plan A confirmation set): scouting, specs, screen

2026-09-27. This implements the confirmation set of `docs/v17/V18_PLANS.md` Plan A. It follows the v1.7 conventions of `docs/v17/candidates.md`; the companion `af_candidates.json` uses the same schema as `docs/v17/candidates.json`.

## Blinding
No propensity score, matching, balance, SMD or hazard ratio has been computed for any trial in this file. No v1.6/v1.7 result file was read in preparing it.

The screen uses counts only:
- persons per arm;
- persons per arm with an ECG in [index−365 d, index];
- primary events and deaths within the trial horizon, **pooled across arms**;
- the share of the candidate's (patient, index date) records that are identical to those of one existing cohort.

It is run by `scripts/v18/screen_feasibility.py`, which reuses `pooled_events` from the v1.7 screen unchanged: the function is given no arm column. The runner is `scripts/v18/run_screen.sh`, and its output is under `/mnt/raid0/rbc58/ecg-tte/audits/claude-v18-screen/`.

## Order of work
1. Candidate specs and benchmarks were committed in the registration commit ("register v1.8 AF trials ..."), before the screen and before any outcome extraction. Benchmarks come from the primary-paper abstracts (PubMed E-utilities text, 2026-09-27), with PMIDs.
2. The count-only screen was run.
3. Trials were selected by the fixed rules below.
4. Selected trials were added to the `v13_common.V18` registry and committed before the build, which includes outcome extraction.

## Selection rule (fixed before the screen; identical to v1.7 except that rule 4 now covers every existing cohort)
1. AF population with an active-comparator or strategy comparison, emulable with the existing designs:
   - new user;
   - sequential prevalent new-user (`switch_seq`, as for EAST-AFNET 4, AFFIRM and AF-CHF);
   - procedure.
   The endpoint must be a hard EHR endpoint (death, stroke/SE, MI, HF or major-bleeding hospitalisation), and the primary publication must report a primary HR/RR with a CI.
2. The smaller arm has ≥ 300 persons with an ECG in the window.
3. There are ≥ 50 pooled primary events within the horizon among ECG-covered persons.
4. The trial is not a near-duplicate: < 80% of its (patient, index) records are identical to any single existing cohort directory (`audits/claude-*-cohort-v*`, i.e. the 33 analysed trials plus earlier builds) or to an already-selected v1.8 candidate. Overlap of 50–80% is flagged for the rater.
5. The trial has not been analysed before.

## Candidates screened (specs in `scripts/trial_specs.py`, `V18` block)
The last column gives the design used in our emulation.

| key | RCT (PMID) | RCT comparison | primary endpoint; RCT estimate | our design |
|---|---|---|---|---|
| prague17 | PRAGUE-17 (32586585) | LAA closure vs DOAC | stroke/TIA, SE, CV death, major/CRNM bleeding, procedure complications; sHR 0.84 (0.53–1.31) | sequential: LAAO (with OAC in the prior year) vs established DOAC users; prior bleed or thromboembolism code |
| protect_af | PROTECT AF (19683639) | Watchman vs warfarin | stroke, CV death, SE; RR 0.62 (95% CrI 0.35–1.25) | sequential: LAAO vs established warfarin users; CHADS2 risk code |
| frail_af | FRAIL-AF (37634130) | switch VKA to NOAC vs continue VKA | major/CRNM bleeding; HR 1.69 (1.23–2.32) | sequential: first DOAC after warfarin vs continued warfarin; age ≥ 75; eGFR ≥ 30 |
| laaos3 | LAAOS III (33999547) | LAA occlusion vs none at cardiac surgery | ischaemic stroke or SE; HR 0.67 (0.53–0.85) | procedure: open CABG/valve surgery with vs without a same-day LAA occlusion code; ICD-10-PCS era |
| raft_af | RAFT-AF (35313733) | ablation-based rhythm vs rate control in HF | death or HF event; HR 0.71 (0.49–1.03) | sequential: AF ablation vs established rate-control users; HF code |
| augustus | AUGUSTUS (30883055) | apixaban vs VKA after ACS/PCI | ISTH major/CRNM bleeding; HR 0.69 (0.58–0.81) | new user ≤ 30 d after PCI, with a P2Y12 order in the prior year |
| pioneer_af_pci | PIONEER AF-PCI (27959713) | rivaroxaban 15 mg + P2Y12 vs VKA triple | clinically significant bleeding; HR 0.59 (0.47–0.76) | as AUGUSTUS, with rivaroxaban |
| re_dual_pci | RE-DUAL PCI (28844193) | dabigatran 150 mg dual vs warfarin triple | major/CRNM bleeding; HR 0.72 (0.58–0.88) | as AUGUSTUS, with dabigatran |
| active_w | ACTIVE W (16765759) | clopidogrel + aspirin vs OAC | stroke, SE, MI, vascular death; RR 1.44 (1.18–1.76) | new user: clopidogrel vs warfarin; recent ACS/stent excluded |
| renal_af | RENAL-AF (36335914) | apixaban vs warfarin on haemodialysis | major/CRNM bleeding; HR 1.20 (0.63–2.30) | new user; ESKD/dialysis code |
| engage_af | ENGAGE AF-TIMI 48 (24251359) | edoxaban vs warfarin | stroke/SE; ITT HR 0.87 (97.5% CI 0.73–1.04) | re-check of the v1.3 spec (previously infeasible) |

Where the RCT endpoint includes major or CRNM bleeding, our emulation uses major-bleeding hospitalisation instead: a new inpatient stay after the index stay coded with GI bleeding, peptic ulcer with haemorrhage, or intracranial haemorrhage (`BLEED_HOSP`).

## Not screened (design, population or outcome not emulable; decided before any count)
| trial (PMID) | reason |
|---|---|
| RACE II (20231232) | lenient vs strict heart-rate target: a treat-to-target strategy with no identifiable time zero; primary result is an absolute difference, with no HR |
| RATE-AF (33351042) | primary outcome is quality of life (SF-36) |
| ATHENA (19213680) | dronedarone vs placebo; no standard active-comparator adaptation; "CV hospitalisation" is not reliably identifiable in AF patients |
| PALLAS, ELDERCARE-AF, NOAH-AFNET 6 | placebo-controlled |
| AVERROES, BAFTA | aspirin comparator (largely OTC) |
| ARTESiA (37952132) | device-detected subclinical AF is not identifiable; aspirin comparator |
| CASTLE-HTx (37634135) | end-stage HF (LVAD/transplant work-up) with ablation; the parent CASTLE-AF ablation arm had 149 persons after gates (v1.3), so infeasible |
| CASTLE-AF | v1.3: ablation arm 149 |
| RAAFT-2, MANTRA-PAF, EARLY-AF, STOP AF First, Cryo-FIRST, AATAC | primary outcome is arrhythmia recurrence or burden (needs rhythm monitoring) |
| DIONYSOS | outcome (AF recurrence) not emulable; analysed before |
| CHAMPION-AF (41910347) | LAAO vs NOAC: the primary efficacy result is a risk difference; also the same comparison and cohort as PRAGUE-17 (near-duplicate) |
| CLOSURE-AF (41849741) | LAAO vs best medical care; the primary result is an RMST difference with no HR; mixed comparator |
| PREVAIL (24998121) | same comparison as PROTECT AF (near-duplicate cohort); PROTECT AF is the pivotal trial |
| OPTION (39555822) | LAAO after ablation vs OAC; primary efficacy result is a difference in proportions; subset of the LAAO cohort |
| ENTRUST-AF PCI (31492505), ENVISAGE-TAVI AF (34449183) | edoxaban (about 150 persons ever ordered at this site, v1.3) |
| AFIRE (31475793) | de-escalation (stopping antiplatelet on rivaroxaban), with Japanese rivaroxaban doses; no identifiable initiation |
| RE-CIRCUIT, AXAFA-AFNET 5, VENTURE-AF, BRUISE CONTROL(-2) | peri-procedural anticoagulation; outcomes are peri-procedural or pocket haematoma; no primary HR |
| ELAN, TIMING, OPTIMAS | timing of DOAC after stroke; primary results are risk differences |
| INVICTUS, RIVER | rheumatic / bioprosthetic-mitral AF (rare); primary results are an RMST or other non-HR |
| DOAC vs DOAC | no head-to-head AF RCT with a hard primary endpoint and HR was identified |

## Screen results and selection
Pending: this section is filled in after the count-only screen.
