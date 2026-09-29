# v1.9 sensitivity analysis: outpatient initiators (plan)

Status: **exploratory sensitivity analysis** (protocol v1 §4: "Primary: all initiators. Sensitivity: outpatient
initiators"), requested 2026-09-29. This plan, including the RCT-setting classification, is written and committed
before any outpatient-restricted estimate, balance value or cohort count is computed. Deviations found during
implementation are dated and logged at the end, before results are summarised. Results: `docs/v19/SENS_OUTPATIENT.md`;
code: `scripts/v19/sens_outpatient.py`; outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v19-sens-outpatient/`
(umask 077, files 600).

## Question

Do the balance and RCT-agreement conclusions of the 38-trial analysis (thin PS P1 / P5, with or without the 32-PC
AI-ECG embedding) change when trials whose RCTs enrolled outpatients are emulated only in outpatient initiators, and
how much power does the restriction cost?

## Setting (identical to the primary analysis except for the rows analysed)

- **Trials.** The 38 trials of `scripts/v18/v18_af_confirm.py` (v1.6 18, v1.7 15, v1.8 AF 5, in that order;
  index i gives the halves seed 16060 + i).
- **Code path.** `v17_confirm.task` imported unchanged through `v18_af_confirm` (V18 covariate paths; P5 diagnosis
  list of `s11_p5`). P1 = `T.demo`; P5 = demo + hypertension_v11, t2d, cad_ihd, atrial_fibrillation, HF
  (hf_any_365, else elx_chf). Arms: base | +ECG32 | +permuted ECG32 (`T.shuffle_perm`) | +noise32 | unmatched.
  `E.run_cell(T, X[rows], rows=rows, estimator=("match", 0.2, 1))`, L2 PS C = 1, 1:1 greedy caliper 0.2 SD logit.
- **Restriction mechanism.** The only change is the row set: `halves(T, i)[h]` (full / A / B) is intersected with
  the population mask. PS, matching, pooled SDs for the SMD, the covars2b column filter and the Cox model are then
  re-fitted within the restricted rows (as in S4, `run_cell rows=`). Halves A / B keep their all-initiator
  assignment (the seeded split is not redrawn), so an outpatient half is the outpatient part of the original half.
- **Outcome, horizon, benchmark.** Unchanged (`T.y_t`, `T.y_e`, `T.y_ok`; `T.rb`, `T.rs`).
- **Reproduction gate.** With the population mask = all rows, the script must reproduce
  `claude-v17-confirm/results_all.csv` (P1, unmatched), `results_p5.csv` (P5) and `claude-v18-af-confirm/results_af5.csv`
  with maximum absolute deviation 0 on every shared numeric column for 2 trials (one v1.6/v1.7 trial and one V18
  trial: carolina and laaos3). If not, stop. The all-initiator comparison columns are then read from those files.

## 1. Index-setting flag (S4 rule, extended to all 38 trials)

Per patient in the trial cohort (`restricted_cohort.parquet` of the trial's cohort dir, `v13_common.PRIMARY/EXTRA`):
- **inpatient** = the index date lies within an OMOP gold inpatient visit (visit_concept_id 9201,
  visit_start_date .. coalesce(visit_end_date, visit_start_date)) = `s4_subgroups.prep` = `make_outpatient_cohort.py`;
- **ED (descriptive only)** = not inpatient, and the index date lies within an emergency-department visit (9203);
- **outpatient** = not inpatient (ED-day initiators stay in the outpatient population, as in the protocol rule).
Report per trial the % inpatient overall and by arm, and % ED (percentages only; any underlying count 1–10
suppressed). The flag file is written as `restricted_setting_<trial>.parquet` (patient_key, flag only; never printed).

## 2. A priori RCT-setting classification (from trial designs only)

"Hospital-initiated" = randomisation during or just after a hospitalisation or an in-hospital procedure; operationally
the trial_specs gate `window_30d` (qualifying acute event within 30 d) or `procedure_1d` (in-hospital surgery).
Everything else enrolled stable outpatients with a chronic condition ("outpatient RCT").

| Trial | Class | Reason |
|---|---|---|
| COMET | outpatient | chronic HF (NYHA II–IV) on stable therapy |
| PARADIGM-HF (seq) | outpatient | chronic HFrEF on ACEi/ARB, run-in, outpatient randomisation |
| TRANSFORM-HF | **hospital** | randomised during HF hospitalisation, before discharge (gate window_30d I50) |
| ELITE II | outpatient | chronic HF, age ≥ 60 |
| LIFE | outpatient | hypertension with ECG-LVH |
| PLATO | **hospital** | ACS, randomised within 24 h of symptom onset (window_30d) |
| ARISTOTLE | outpatient | AF with stroke risk factor, chronic anticoagulation |
| ROCKET-AF | outpatient | AF, chronic anticoagulation |
| RE-LY | outpatient | AF, chronic anticoagulation |
| ALLHAT | outpatient | hypertension, age ≥ 55 |
| EMPEROR-Preserved | outpatient | chronic HFpEF (+T2D here) |
| EAST-AFNET 4 | outpatient | early AF, rhythm-control add-on |
| CABANA | outpatient, **procedure arm** | stable AF, elective ablation vs AAD |
| ONTARGET | outpatient | stable vascular disease / high-risk diabetes |
| VALUE | outpatient | hypertension |
| ASCOT-BPLA | outpatient | hypertension |
| EMPA-REG OUTCOME | outpatient | T2D with established CVD |
| CAROLINA | outpatient | T2D |
| LEADER | outpatient | T2D with CVD |
| SUSTAIN-6 | outpatient | T2D with CVD |
| REWIND | outpatient | T2D |
| DECLARE-TIMI 58 | outpatient | T2D |
| CANVAS | outpatient | T2D |
| TECOS | outpatient | T2D with CVD |
| CARMELINA | outpatient | T2D with kidney disease |
| VALIANT | **hospital** | acute MI, randomised 0.5–10 d after MI in hospital (window_30d) |
| INSIGHT | outpatient | high-risk hypertension |
| AFFIRM | outpatient | AF, rhythm-control add-on |
| AF-CHF | outpatient | AF + HF, rhythm-control add-on |
| PRECISION | outpatient | arthritis with CV risk, chronic NSAID |
| AMPLIFY | **hospital** | acute VTE, randomised within days of diagnosis (window_30d; hospital or ED presentation) |
| LODESTAR | outpatient | clinically diagnosed CAD, statin choice |
| PROVE IT-TIMI 22 | **hospital** | ACS, randomised within 10 d of hospitalisation (window_30d) |
| FRAIL-AF | outpatient | frail elderly on warfarin, switch to DOAC |
| LAAOS III | **hospital** | AF undergoing cardiac surgery; occlusion during the surgery (procedure_1d) |
| PROTECT AF | outpatient, **procedure arm** | AF on warfarin, elective percutaneous LAA closure |
| RAFT-AF | outpatient, **procedure arm** | AF + HF, elective ablation vs rate control |
| ACTIVE W | outpatient | AF with stroke risk factor, chronic antithrombotic |

**Procedure-arm rule (a priori).** In CABANA, PROTECT AF and RAFT-AF the index date of one arm is the procedure,
which is often coded inside a (planned, overnight) inpatient stay. Restricting to outpatient index dates would then
drop procedure-arm patients selectively on procedure logistics, not on the RCT setting. These three trials are
therefore not in the primary outpatient set; they are reported in a secondary set that includes them.

Sets:
- **OUT-29** (primary): the 29 outpatient-RCT drug trials, outpatient initiators only.
- **OUT-32** (secondary): OUT-29 + CABANA, PROTECT AF, RAFT-AF, outpatient initiators only.
- **HOSP-6**: TRANSFORM-HF, PLATO, VALIANT, AMPLIFY, PROVE IT, LAAOS III, all initiators (= primary results, reported
  separately); secondary: inpatient initiators only.
- **Mixed-38** (secondary): OUT-32 outpatient-only + HOSP-6 all initiators (the "setting-matched" emulation).
- Supplementary (no inference): outpatient-only for the 6 hospital-initiated trials.

Size rule (as S4): a trial × population is analysed only if both arms have ≥ 100 patients (full cohort) and ≥ 50
(each half); otherwise it is marked "not analysable" and drops out of the paired statistics of that set (count
reported). The all-initiator comparison is always computed on the same trials.

## 3. Endpoints and statistics (per set, PS P1 and P5; code of `v17_confirm` / `v18_af_confirm`)

(a) Balance: lt01 = % of the 58 held-out characteristics with |SMD| < 0.1 (primary balance endpoint); x_lt01
(covars2b non-proximal panel); mean |SMD|; domain summaries (mean |SMD| and % < 0.1 within each of the 8 VARS
groups: coded record, vitals & core labs, other labs, echo LV structure / LV function / diastolic-LA / RV-pulmonary /
valves-aorta).

(b) Emulation: absd = |log HR − log HR_RCT| (primary emulation endpoint); consistency = % |z| < 1.96 with
z = (log HR − RCT) / sqrt(se² + se_RCT²); number of trials with ECG closer than base.

Tests (all one-sided exact sign-flip, `v17_confirm.signflip_1s`, H1 = ECG better): ECG vs base, ECG vs permuted ECG
(also vs noise32); halves A / B; leave-one-out max p; comparator-clustered p (clusters of
`docs/v17/trial_selection.json`, cluster-mean difference); for absd (and z2) the benchmark shuffle **within set**
(the set's own k (rb, rs) pairs permuted jointly across trials, 20,000 draws, `np.random.default_rng(0)`, statistic
mean(|le − q| − |lb − q|), p = P(null ≤ observed)) — the v1.7 construction.

Side by side: every statistic is also computed for all initiators on the same trial set (reference files). The
direct effect of restriction (outpatient-only minus all initiators, per arm) is summarised as a mean difference,
trials improved, and an exact two-sided sign-flip p (descriptive).

## 4. Cohort and power (PI request)

Per trial, percentages and ratios only: % of initiators retained after restriction (overall and by arm); % of the
smaller arm retained; matched pairs retained (outpatient / all, %, P1 and P5, base and ECG); primary-outcome events
retained (cohort and matched P1 base, %); SE inflation of log HR = se_outpt / se_all (P1 base, P1 ECG, P5 base);
feasibility after restriction (yes / no): ≥ 300 patients with ECG in the smaller arm and ≥ 50 pooled events
(the v1.7 / v1.8 build thresholds). Summary: median (IQR) SE ratio and % retained across OUT-29 / OUT-32, number of
trials failing feasibility. No closed-form minimal detectable difference is given (not defined for the paired
across-trial sign-flip).

## Interpretation rule (plain language)

The conclusion "changes" if, for P1 or P5 in OUT-29, ECG vs base crosses p = 0.05 on lt01 or absd relative to the
all-initiator result on the same trials, or the absd benchmark-shuffle p crosses 0.05. Any positive emulation result
must also beat permuted ECG and the benchmark shuffle. Exploratory; no multiplicity correction is used to claim a
finding.

## Data rules

Read mounted data; write only under `/mnt/raid0/rbc58` and `/home/rbc58/github`. Aggregates only; counts 1–10
suppressed in every written file; no patient rows printed. Commit only code and md. ≤ 24 worker processes.

## Deviation log

(dated entries added during implementation, before results are summarised)

- **2026-09-29, deviation 1 (reproduction tolerance).** With pop = all, CAROLINA and LAAOS III reproduce the
  reference files exactly for loghr, se, n, n_t, n_c, n_pairs, cstat and every threshold-based count; the SMD
  columns differ by at most one or two floating-point ulps (max 7.1e-15 on x_pct_lt10, ≤ 2.2e-16 on SMDs;
  summation-order noise). The gate is applied as max deviation ≤ 1e-12 (as in the adherence plan), and the check is
  extended from 2 to all 38 trials. Found before any outpatient-restricted result was computed.
