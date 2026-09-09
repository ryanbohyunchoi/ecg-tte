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
- [x] Push fixes, rerun `bash scripts/run_stage34.sh` for all 32 (now
      resilient — will report FAILED count instead of dying).
      Result: OK=27 SKIPPED=0 FAILED=5. 5 failures TBD (separate from d5896).
- [ ] Separately: rebuild Stage 1 pool for d5896 (config fixed, pool stale)
      so its stage3+4 run uses the corrected arm split.
- [ ] Investigate the other 4 stage3/4 failures (d5896 was 1 of the 5).

## Round 5: stage5_meta.py — cross-trial meta-analysis
New `scripts/stage5_meta.py`. For each trial, reads
`runs/<run_name>/results_summary.csv` (stage4) + `published_hr`/
`published_hr_ci` from `configs/<trial>.yaml`. All 5 ladder rungs
(Unadjusted Cox, Adjusted Cox, Structured PSM, ECG-NN PRIMARY, PS+ECG-NN).

Per-trial-per-method (`meta_results.csv`):
- log_hr, log_published_hr, log_hr_diff, abs_log_hr_diff
- z_pooled = log_hr_diff / sqrt(se_emulated^2 + se_published^2)
  (standardized estimate difference vs published RCT)
- emulated_class/published_class (benefit/harm/null from CI vs 1) + agree
- ci_overlap

Per-method aggregate (`meta_summary.csv`):
- pearson_r (log HR emulated vs log HR published, n>=3 trials)
- mean/var of log_hr_diff, mean abs log_hr_diff
- mean/var of z_pooled
- regulatory_agreement_rate, ci_overlap_rate

Plots: `meta_scatter.png` (5-panel emulated vs published log-HR),
`meta_variance.png` (var + mean|diff| bar per method),
`meta_zscore.png` (z_pooled boxplot per method).

- [x] py_compile OK.
- [x] Smoke-tested with synthetic 2-trial results_summary.csv (vero+comet):
      correctly skips d5896 (no results yet) and lead2 (published_hr null),
      produces meta_results.csv/meta_summary.csv + 3 PNGs.
- [x] Ran on cluster (25/32 trials). Hit `boxplot tick_labels` kwarg error
      (cluster matplotlib < 3.9) — fixed -> `labels=labels`.
- [ ] Re-run after Round 6 fix below (results will change for ~28 trials).

## Round 6: CRITICAL — inclusion.required_icd never filtered (stage3)
Discovered via stage5_meta output: dapa_ckd and declare_timi58 (both
dapagliflozin-vs-DPP4i arm pairs) produced BIT-IDENTICAL results across
all 5 ladder rungs (n=234, hr=0.71904747954881... to 16 sig figs).

Root cause: stage1_build_pool.py computes `inclusion.required_icd` flag
columns (e.g. dm_icd_ever, ckd_icd_ever, afib_icd_ever — the disease
population gate) but only as columns, never filters the pool. stage3
never references `required_icd` either — `_merge_yaml` only applies
flat top-level YAML keys matching argparse dests, and required_icd is
nested under `inclusion:`. Net effect: the population gate was a no-op
for ALL 28/32 trials that use it (everything except impact, lead2,
ontarget, savor_timi — TBD if those use a different gate).

- [x] `_merge_yaml` now stashes the raw cfg dict on `args._yaml_cfg`.
- [x] New step 1c in stage3_filter.py: AND each
      `inclusion.required_icd[].name` column == 1 into the filter chain,
      column-existence-guarded (NOTE+skip if pool lacks the column).
- [ ] Re-run `bash scripts/run_stage34.sh` for all 32 trials — cohort
      sizes/results will change for ~28 trials (this is the FIX taking
      effect, not a regression). COMET (validated baseline,
      rct_duplicate_success=true) also affected — required_icd=
      prior_hf_code_1yr (CHF dx in 1yr), previously dead, now applied.
      Expect COMET cohort to shrink; re-validate against prior COMET
      numbers (n was ~2418 unadjusted before this fix).
- [ ] Re-run stage5_meta.py once all 32 done — pearson_r should improve
      if hypothesis (ECG-NN matching helps) holds on correctly-gated
      populations.
- [ ] Diagnose the original 4 unknown stage3/4 failures (impact,
      ontarget, savor_timi, transcend) — may resolve or change under
      the new filter.

## Round 7: PARADIGM-HF + Rich-Covariate Upgrade

Goal: PARADIGM-HF TTE on new drug_master with 50–100 covariate PSM/IPTW.
See `trials/paradigm/PLAN.md` for full design spec.

Pipeline shape:
  stage1 → stage2 → stage3 → stage3.5_enrich (NEW) → stage4 (model only)

- [ ] Step 0: run `explore_omop_sources.py` on cluster; inspect concept freq
      CSVs; pick LAB_CONCEPTS + VITAL_CONCEPTS concept_id maps.
- [ ] Step 1a: expand COMORBIDITY_ICD 7→~35 Elixhauser in cohort_utils.py;
      add LAB_CONCEPTS / VITAL_CONCEPTS dicts from Step 0.
- [ ] Step 1b: add load_measurement() + load_observation_icd10() to cohort_utils.py.
- [ ] Step 2: write scripts/stage3_5_enrich.py (cohort-restricted enrichment
      + smd_baseline.csv).
- [ ] Step 3: modify stage4_analyze.py: RICH_COVS, wire ipw_hr, drop pre-SMD.
- [ ] Step 4: expand configs/paradigm_hf.yaml covariates block.
- [ ] Run stage1 for PARADIGM-HF (confirm required_icd fix active first).
- [ ] Run stage2 (embed pool ECGs).
- [ ] Run stage3 filter.
- [ ] Run stage3.5 enrich; verify smd_baseline.csv looks sane.
- [ ] Run stage4; compare HR vs published 0.80 [0.73–0.87].

## Round 8: BCL embeddings for LVSD (EF<40) subphenotyping
Goal: embed ECGs (≤30d from a qualifying echo) for up to 50K individuals with
EF<40, using existing BCL biometric encoder. Emit embeddings for unsupervised
clustering / LVSD subphenotype discovery. Output → /mnt/raid0/rbc58/bio/v1.

- [x] New `scripts/bio_embed.py` (reuses load_bcl_encoder + load_ecg_meta/load_echo_meta):
      - filter echo EF < 40 (configurable)
      - match ECG within ±30d of a qualifying echo; nearest ECG per individual
      - cap to 50K individuals (seeded sample)
      - verify signal exists + shape (5000,12); embed 512D L2-norm
      - save embeddings.npy (N,512) + manifest.parquet (row→MRN,fileID,EF,dates,gap)
- [x] `scripts/run_bio_embed.sh` wrapper
- [ ] Run on cluster (H100) — user runs

## Round 9: MICE imputation + PSM/balance upgrade (2026-07-28)
Goal: replace complete-case with multiple imputation (MICE + Rubin) so PSM/balance
run on the full cohort instead of dropping rows with missing EF/ECG/labs. Follows
RCT-DUPLICATE / Leyrat "within" approach. See tasks/lessons.md.

- [x] `scripts/imputation.py` (new): split binaries vs continuous; IterativeImputer
      MICE; EF missing-indicator; Nelson-Aalen outcome in predictor matrix.
- [x] stage4 Rubin pooling: `pool_rubin`, `_pool_over_imputations`, `structured_psm_pooled`;
      `--n-imputations` (default 1 = legacy). cox_hr exposes log_hr/se_log_hr.
- [x] Caliper fix: match on logit(PS) at `--caliper-sd × SD` (Austin 0.2);
      `--structured-caliper` deprecated alias. ps_ecg_match made consistent.
- [x] `balance.pooled_balance_table` (avg SMD over m + complete-case sensitivity cols);
      SMD_COLS 37→44.
- [x] Wire `--denominator {strict,both}` audit (fixes run_stage34.sh argparse crash);
      generalize denominators.audit_table event col.
- [x] Wire labs/vitals/Z-codes: stage1 `--measurement-dir`/`--observation-dir`,
      stage3 OUTPUT_COLS passthrough, stage4 candidates + SMD_COLS, configs.
- [x] Cleanup: dup cohort-load, stale docstrings, delete __pycache__, tasks/lessons.md.
- [x] Verify locally: m=1 == legacy (Unadjusted 0.931 / Adjusted 0.885 exact);
      pool_rubin se=√T; labs/vitals through MICE+balance end-to-end.

Cluster TODO (needs OMOP measurement/observation shards):
- [ ] Locate measurement_*.parquet + observation_icd10_*.parquet dirs on cluster.
- [ ] Re-run stage1 for PARADIGM-HF/COMET with --measurement-dir/--observation-dir.
- [ ] Re-run stage3 → stage4 with --n-imputations 5; compare HR vs complete-case.
- [ ] Confirm FMI per estimate is sane (<0.5 ideally); inspect missingness_audit.csv.
