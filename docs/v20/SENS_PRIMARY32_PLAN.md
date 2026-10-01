# v2.0 plan: sensitivity and robustness analyses for the primary 32-trial set (committed before results, 2026-10-01)

**Why:** the manuscript audit (docs/paper/AUDIT_MANUSCRIPT_2026-10-01.md, items #96–#97) found two gaps:
- The matching and estimation sensitivity analyses described in the paper were only run for the 18 development trials.
- No robustness results exist for the 32-trial primary set.

The PI asked for both to be rerun. All analyses are exploratory.

## Sets
- **Primary set, S32:** the 38 emulated trials minus the 6 rated "Limited" in docs/v19/quality_tiers.json.
- **Sensitivity set, S38:** all 38.
- **Cohort:** the full cohort only. Split-sample halves are **not** used (PI decision 2026-10-01).

## Engine
`v16_engine.run_cell` on the v18_embed_compare trial objects, with the same PS designs:
- **P1:** T.demo.
- **P5:** v18_clmbr.designs P5DX.
- **hdPS200:** T.X_dx plus T.hd(200), ranked on the full cohort.
- **clinical:** T.X_core. The clinical exclusions of the 58-variable panel (meds/util summaries and T.phys observed values) are applied.

Arms: PS alone (base), + ECG32 (T.ecg_pc), and + permuted ECG32 (T.ecg_pc[T.shuffle_perm]). The C-statistic is not computed (cstat=None).

## Configurations
| Config | Estimator | PS model |
|---|---|---|
| main | 1:1 greedy match, caliper 0.2 SD logit | L2 logistic, C = 1 |
| cal01 | 1:1 match, caliper 0.1 | L2 |
| m13 | 1:3 match, caliper 0.2 (controls weighted 1/m) | L2 |
| iptw | stabilised IPTW, trimmed at the PS 1st/99th percentile | L2 |
| overlap | overlap weights | L2 |
| gbm | 1:1 match, caliper 0.2 | gradient boosting, 5-fold cross-fitted |

**ECG components (P1 only, main config):** k ∈ {4, 8, 16, 32, 64, 128, 256} PCs of the 256-d embedding, using the within-trial PCA of v13_common.pcs. The ECG and permuted-ECG arms use the same k.

## Endpoints (per trial, then across trials)
- **Balance on the 58-variable held-out panel** (per-rung exclusions as in v18):
  - % with |SMD| < 0.1 (lt01);
  - mean |SMD| (m58);
  - relative reduction = 1 − mean_t(m58_arm) / mean_t(m58_base), i.e. the ratio of across-trial means.
- **RCT agreement:**
  - |Δ log HR|;
  - estimate agreement, |Δ| ≤ 1.96·s_RCT;
  - standardized-difference agreement, |Δ| / √(s² + s_RCT²) < 1.96;
  - Pearson r of emulated vs RCT log HR.
- **Tests:**
  - exact one-sided sign-flip across trials (v17_confirm.signflip_1s), with ECG better as H1; the placebo vs base contrast is two-sided;
  - benchmark shuffle for |Δ|: within-set, 20,000 draws, seed 0.

## Robustness (main config, S32 primary, S38 also reported)
- **Comparator-clustered sign-flip:** docs/v17/trial_selection.json clusters.
- **Leave-one-trial-out:** maximum p.
- **BH-FDR** within families, over set × rung × contrast:
  - balance-primary: lt01;
  - balance-secondary: m58;
  - emulation: absd, cons;
  - trial-specific: benchmark shuffle.

## Outpatient-initiator sensitivity
Source: claude-v19-sens-outpatient/results_outpt.csv. Set: OUT-29 (the a priori outpatient RCT setting, minus 3 procedure trials) ∩ S32 (primary), with OUT-29 reported as before. Same endpoints, P1 and P5.

## Bootstrap CIs (regenerated)
- **Method:** percentile 95% CI from 4,000 resamples of trials with replacement, using the ratio of across-trial means.
- **Seed:** each CI uses a fresh generator, `np.random.default_rng(20261001)`, so values do not depend on call order.
- **Applied to:**
  - Yale: the overall 58-variable panel, each of the 8 domains (P1), and each rung, for S32 and S38;
  - MIMIC-IV: each rung, over the 7 cardiovascular trials, from claude-v20-mimic-replication per-trial mean |SMD|.
- **Comparison:** each CI is compared with the value currently in docs/paper/paper.md.

## Reproduction gate
Before any new configuration, the full-cohort main-config cells (P1, P5, hdPS200, clinical × base, ECG, shufECG) must reproduce claude-v18-embed-compare restricted_results_unsuppressed.parquet (half = full) for loghr, se, n, n_pairs and all smd columns. The maximum |Δ| must be ≤ 1e-12.

## Outputs
- **Code:** scripts/v20/sens_primary32.py.
- **Aggregates:** /mnt/raid0/rbc58/ecg-tte/audits/claude-v20-sens-primary32/ (umask 077; counts 1–10 suppressed).
- **Write-up:** docs/v20/SENS_PRIMARY32.md.
