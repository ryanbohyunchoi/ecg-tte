# stage3_filter.py generalization (vero KeyError fix)

Crash: `KeyError: 'prior_meto_days'` at line 277. Root cause: stage3_filter.py
hardcodes COMET arm names ("carvedilol"/"metoprolol") and alias columns
(prior_meto_days/prior_carv_days), but identify_arms_generic() (stage1) only
produces those aliases for COMET — other trials get prior_<arm_name>_days
using their own arm names (e.g. prior_teriparatide_days).

## Fixes
- [x] Attrition.log(): count per actual `arm` value present in df (dynamic n_<arm> cols)
      instead of hardcoded carv/meto.
- [x] Step 2 naive new-user lookback (lines ~272-283): generalize using
      pool["arm"].unique() and prior_<other_arm>_days columns.
- [x] Manifest + final print block (lines ~521-540): dynamic per-arm counts.

## Verify
- [ ] Re-run `bash scripts/run_stage34.sh --trials "vero"` on cluster, confirm
      stage3 completes and produces comet_cohort.parquet + attrition.csv.

## Note
`--meto-formulation tartrate_only` path (lines ~344-384) still hardcodes
"metoprolol"/METOPROLOL — only triggers for non-default flag, COMET-only
analysis, left as-is.

## Round 2: KeyError 'hfref_icd_5y' (vero, after lookback fix)
- [x] New `--require-hfref` flag (default True, COMET behavior preserved).
      Block 4 (HFrEF inclusion) skipped when False; also added 3rd fallback
      (no hfref_icd_* column at all -> ICD arm of criterion = False, NOTE printed).
- [x] Block 8 exclusions (CCB/other-BB/recent-MI/AV-block/ESRD/hepatic/valvular):
      now column-existence guarded via `_exclude()` helper, NOTE+skip if
      pool lacks the COMET-specific cardiac column.
- [x] vero.yaml: added top-level `require-hfref: false` (osteoporosis trial,
      HFrEF criterion N/A).
- [x] Re-run vero stage3+4 on cluster — completed end-to-end.
      n=674, strict D=71 (small, non-cardiac trial). PSM/ECG-NN/hybrid rungs
      fail to converge (n_per_arm ~22-35) — expected for this trial, not a bug.
      results_summary.csv + forest.png saved.

## Next
- [ ] Run `bash scripts/run_stage34.sh` for all 32 trials.

## Round 3: collapse PSM-sparse/PSM-rich into single PSM covariate set
- [x] stage4_analyze.py: removed SPARSE_COVS/RICH_COVS. New STRUCTURED_COVS
      (used for Structured PSM + PS+ECG-NN PS-caliper) = 11 covs:
      age_at_index, sex_binary, race_black, afib, htn, dm, cad_mi, copd,
      hyperlipidemia, stroke, prior_hf_code_1yr.
      ADJ_COVS (3, age/sex/race) unchanged — still its own "Adjusted Cox" rung.
- [x] denominators.py: build_masks(cohort, emb_df, psm_covs) — single list,
      psm_sparse_eligible/psm_rich_eligible -> psm_eligible;
      intersection_strict = ecg_available & psm_eligible.
      missingness_audit() param renamed rich_covs -> covs.
- [x] Re-run vero stage3+4 — confirmed. denominator_audit.csv shows
      psm_eligible/intersection_strict. STRUCTURED_COVS=10 for vero
      (prior_hf_code_1yr not in vero's pool — non-cardiac trial; filtered
      out by column-existence check, working as intended). Structured PSM
      now runs (0 rows dropped vs 49/71 before) — HR=1.00 [0.06-15.99] n=38,
      too small to be informative but no crash/convergence error on PSM step.

## Status: vero stage3+4 fully green. Ready for full 32-trial run.

## Round 4: full-32 run crashed at d5896 (ZeroDivisionError, control arm n=0)
COMET ran clean (STRUCTURED_COVS=11, full ladder incl. PSM/ECG-NN/PS+ECG-NN
all produced results). d5896 crashed: cohort 328 budesonide_formoterol /
1 budesonide -> strict D control arm = 0 -> cohort_1to1 empty -> lifelines
ZeroDivisionError. set -euo pipefail aborted the whole 32-trial loop here
(all alphabetically-later trials never ran).

- [x] configs/d5896.yaml: root cause was treated arm's bare "BUDESONIDE"
      keyword also matching budesonide-alone (Pulmicort/Rhinocort) products;
      ties in identify_arms_generic go to the first/treated arm, so nearly
      everyone landed in budesonide_formoterol. Added formulation_filter:
      treated requires FORMOTEROL (combo product), control excludes
      FORMOTEROL/SYMBICORT (monotherapy only).
      NOTE: requires Stage 1 pool rebuild for d5896 to take effect
      (arm assignment happens in stage1_build_pool.py).
- [x] stage4_analyze.py: new guard — if either arm has 0 patients in the
      active denominator (n_t==0 or n_c==0), print clear ERROR + likely
      cause and sys.exit(1) instead of crashing deep in lifelines with
      ZeroDivisionError. Protects ALL trials, not just d5896.
- [x] run_stage34.sh: stage3 and stage4 calls now use
      `set +e; ... | tee; rc=${PIPESTATUS[0]}; set -e` and
      `continue` + FAIL_COUNT on nonzero exit, so one trial's failure
      no longer aborts the rest of the 32-trial loop. Final summary
      now reports OK/SKIPPED/FAILED.

## Next
- [ ] Push fixes, rerun `bash scripts/run_stage34.sh` for all 32 (now
      resilient — will report FAILED count instead of dying).
- [ ] Separately: rebuild Stage 1 pool for d5896 (config fixed, pool stale)
      so its stage3+4 run uses the corrected arm split.
