# Queue 2026-10-08 (afternoon): results summary

Unattended run of `docs/queue/QUEUE_2026_10_08.md` (steps A–E), 13:53–15:00 EDT. Full step log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-queue-20261008/STATUS.md`.

- Commits (local `main`, **not pushed**):
  - c8ac627 B;
  - d243ecd A;
  - 33308d6 D;
  - 49c7160 C;
  - plus this results file.
- B was committed before A because the cohort-fix agent finished its doc later; its code did not change after the B commit.
- No CSV, parquet or restricted file was committed.
- `paper.md`, `paper2.md`, `table1_picot.md` and the `.docx` files were not touched.
- No GPU was used.

## What finished

| Step | Output | Status |
|---|---|---|
| A. Cohort fixes | `scripts/v2_cohorts/`, `docs/v2_cohorts/COHORT_FIXES.md` (written by the separate agent; it finished at 14:43, before the 60-minute takeover point, so no takeover was needed) | Done; verified; committed |
| B. PS-Clinical (no LVEF), 5-draw MI | `scripts/v2_psclin_mi/psclin_mi.py`, `docs/v2_psclin_mi/PS_CLINICAL_MI.md` | Done; committed |
| C. Balance explorer on spec-v2 cohorts | `scripts/build_balance_explorer.py`, new `scripts/explorer_unmatched_v2.py`, `docs/presentation/ecg_tte_balance_explorer_2026_10_08.html` | Done; committed |
| D. Quality re-score | `scripts/emulation_quality_v2/rescore_v2_cohorts.py`, `dc_v2_cohorts.py`, `docs/emulation_quality_v2/RESCORE_V2_COHORTS.md`, `quality_v2_cohorts.json` | Done; committed |
| E. Summary | this file | Done |

## Gate results

- **A (cohort fixes).**
  - Gate A: the spec-v2 pipeline with no fix applied reproduces the version 1 cells exactly: 9,728/9,728 cells, maximum deviation 0.
  - Privacy scan clean (the agent's run at 14:42, and mine re-run before commit).
  - The two summaries (theirs, and mine in step B) agree exactly for PS-CVD5 + ECG.
- **B (MI).**
  - Gate: with the version 1 cohorts and draw 1, the code reproduces all 1,406 existing PS-Clinical-no-LVEF cells (6 methods × 7 arms × 38 trials): 98,420 values, maximum deviation 0.
  - The first attempt failed on the PS-alone arm only (gbm up to 0.04 on one SMD). The cause was the design matrix's memory layout (Fortran- vs C-ordered), which the gbm PS and lbfgs are sensitive to. Fixed by indexing exactly as version 1.
  - Privacy scan clean.
- **C (explorer).**
  - **Version 1 checks, all unchanged and passing:** 141/141 published values; 196/196 PS10 doc values; paper 2 sweep (600 rows, 4.5e-14); leakage-clean sweep; psclin (240 rows) and ladder (1,728); the same 28 F1 rows.
  - **New spec-v2 checks:** 2,520 contrast rows against the two Python summaries (maximum deviation 7e-14) and 1,404 ladder levels (1e-16). Unmatched |SMD| on the fixed cohorts is gated against the v1.8 values (1e-16).
  - **Headless Chromium:** 0 page or console errors; 933 control actions; defaults equal the pipeline.md primary on the spec-v2 cohorts. JS equals Python on the embedded data in 170/170 combinations (2,210 values).
  - **JS vs the Python summaries for the spec-v2 rungs:** 831/840 equal at displayed precision. The 9 others differ by one in the "trials lower" count only, on near-zero placebo contrasts under IPTW/overlap. Their per-trial differences (~1e-7) are below the 1e-5 integer encoding; estimates, CIs and P are equal.
  - Paper 1, PS10 and MI views show their published or summary values. HTML privacy scan pass.
- **D (re-score).**
  - The data-check method reproduces the adjudicated DA.b on the version 1 cohorts exactly.
  - The scores were written and hashed before any impact number.
  - Impact gates: (a) version 1 cells → paper 2's 8.8% (4.4–13.3): PASS; (b) spec-v2 cells, provisional 29 → the step B summary row: PASS (7e-17).

## Headline numbers

**PS-CVD5 + ECG vs PS-CVD5** (primary): main configuration, 54 leakage-corrected items, spec-v2 cohorts.

| Set | version 1 cohorts | spec-v2 cohorts |
|---|---|---|
| Provisional 29 | 9.4% | **6.5% (2.2 to 11.4)**, 21/29, P = .004 |
| **New analysed set, 30 (rescored)** | | **5.5% (0.8 to 10.7)**, 21/30, P = .017 |
| Excellent + Good, 12 (rescored) | | 9.7% (2.6 to 18.1), P = .016 |
| Paper 1's 32 | 8.8% | 6.6% (2.0 to 11.4), P = .004 |
| All 38 | 9.0% | 6.7% (2.5 to 10.8), P = .002 |

- ECG vs permuted ECG: 6.3–8.1% in every set (P ≤ .035).
- **No set shows agreement with the RCTs:** |Δ log HR| does not improve, and the benchmark-permutation P is ≥ .95.
- The cohort-fix agent's random-removal check shrinks the ECG gain as much as the fixes do: about 6.9% when the same numbers of patients are removed at random. So the drop from 9% to about 6.5% reflects refitting on smaller cohorts, not the fixes as such.

**Ladder, spec-v2, + ECG vs PS alone** (main, 54 items; new 30-trial set; provisional 29 in brackets):

| PS base | + ECG |
|---|---|
| PS-Demo | 9.8% (5.6 to 14.0) [9.5%] |
| **PS-CVD5 (primary)** | **5.5% (0.8 to 10.7)** [6.5%] |
| PS-CVD10 | 4.3% (−1.3 to 10.0), P = .09 [4.7%] |
| hdPS | −0.2% (−4.6 to 4.7) [−0.9%]. It was 7.6% on version 1; see "Decisions", item 7 |
| **PS-Clinical (no LVEF), 5-draw MI** | **4.5% (1.2 to 7.9), P = .006** [4.4% (0.9 to 8.0), P = .009] |

- The single draws range 2.4–5.7% on the 30 trials (1.7–5.6% on the 29).
- The MI result is 2.4% (n.s.) on paper 1's 32, and 3.0% (P = .06) on all 38.
- The gain sits in observed LVEF: 16% on the 29 trials.

**New analysed set: 30 trials** = the provisional 29 + **AMPLIFY** (its outcome defect is fixed; it is now Moderate).
- Tiers: 5 Excellent / 7 Good / 18 Moderate / 8 Limited.
- Against paper 1's 32: entering ALLHAT, ASCOT-BPLA, ONTARGET, VALUE; leaving ACTIVE W, CABANA, CANVAS, EMPEROR-Preserved, LEADER, SUSTAIN-6.
- The audit's B1 resolves at 0: the HbA1c and BP entry bounds are applied in spec v2, so EMPA-REG, TECOS, CARMELINA, ASCOT-BPLA, ALLHAT and VALUE stay in.
- The set is **not frozen**: 9 tier-changing provisional scores remain, and B2 is unmet.

## What failed (and what was done)

- **B gate, attempt 1:** memory-layout difference; fixed and re-run, exact.
- **B spec-v2 run, attempt 1:** a read error (the imputed tables were saved without the `patient_key` index name). Fixed, re-imputed and re-run. Nothing was reported from the failed run.
- **C:** 9/840 JS-vs-summary count mismatches from encoding ties (above). Accepted and disclosed, not fixed.
- **Monitoring:** the first wait-loop matched its own command line. No effect on results.
- **Timestamps:** several in the step log were hand-written and run up to about 10 minutes ahead; the order of events is right.

## Decisions for the user

1. **Cohort fixes as primary** (pipeline.md §2 and §10.2 are still PENDING). This queue made spec-v2 the explorer default, as instructed. pipeline.md itself was not edited.
2. **MI imputation population.** I imputed within the fixed analysed cohort, as the queue says. Version 1 imputed on the larger pre-ECG baseline roster. Keep this, or impute roster-wide and drop the patients afterwards?
3. **Re-score scope.**
   - I also re-derived DA from data checks on the fixed cohorts: new DA.b for LAAOS III and AMPLIFY, DA.a for COMET, and the DA provisionals of AF-CHF, ELITE II, PARADIGM-HF and EMPEROR-P resolved.
   - I re-scored OU for LODESTAR and PROVE IT after their outcome rebuilds (framework OU text). Both become Excellent; without this, Excellent + Good is 10 instead of 12. The analysed set is unchanged either way.
4. **Not decided, as instructed:**
   - TRANSFORM-HF (documented TZ = 2 caps it at Moderate);
   - the hypertension switch trials (a "TZ.c ≥50% + ≥3 other points → Limited" rule would remove ALLHAT, ASCOT-BPLA and VALUE → 27 trials);
   - clarifications C1–C10. C3 (any-position I50) now carries the remaining SI points of PARADIGM-HF, EMPEROR-P, DECLARE and EAST-AFNET 4; C10 now also concerns VALIANT.
5. **B1, second half:** the TECOS and CARMELINA sulfonylurea-background subgroups and the TECOS background-therapy requirement. These are not numeric bounds; their Table 1 shares need transcribing. One EL point makes either trial Limited.
6. **Entry bounds applied with "unknown passes".** HbA1c is measured in 10–37% and BP in 22–40% of these cohorts. I scored them 0. Adding DA.a instead would push several placebo-proxy trials to Limited.
7. **hdPS and PS-Flags on the smaller fixed cohorts:** + ECG on hdPS fell from 7.6% to about 0, and PS-Flags degrades (within-cohort ≥1% filter, fixed C = 1). The cohort-fix agent flags these as likely artefacts. The sensitivity with the version 1 flag columns has not been run.
8. **Freeze (framework §7.6):**
   - hash or commit the rater files;
   - run DC-ES-cross, DC-EL-met and DC-SI-hf-anyposition;
   - transcribe the S5 publication facts;
   - complete the clinician review.
9. **Explorer default trial set:** still the provisional 29 (pipeline.md). Switch it to the rescored 30 once frozen? The 30-trial set is already selectable.
