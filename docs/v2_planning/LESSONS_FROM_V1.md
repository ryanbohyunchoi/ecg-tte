# Lessons from version 1 for the version 2 restart (working note, started 2026-10-07)

"Version 1" here means everything up to and including paper.md and paper2.md (scripts v13–v21). Not to be confused with `archive/2026-09-09-legacy-v1/`, the earlier implementation. Final naming is still to be decided.

## 1. Held-out balance leakage (found 2026-10-07; not yet fixed in v1 outputs)

The held-out panel is masked per PS only by exact variable name. Near-duplicates and code overlaps are not masked.

**hdPS (all rungs that contain hdPS200):**
- **What hdPS contains:** `T.X_dx`, i.e. demographics + investigator diagnoses (CKD, HF, valve disease, …), plus the top 200 hdPS levels from pool-A panel features: dx / rx / px codes (365-day window) and pool-A `labn_` lab-was-measured flags. It has no lab values, vitals, echo values or visit counts.
- **Real leak, 58-item panel only:**
  - `mean_meds` is built from medication-order flags (`T.meds`, 90-day window). hdPS can contain `rx_` codes for the same drugs.
  - `sens_primary32.py` and `v21/paper2_grid.py` mask nothing for hdPS (`ex58 = set()`).
  - Affects paper.md's 58-item hdPS rows. The 54-item primary endpoint of paper2 is not affected.
- **Soft overlaps** (proxies, not the same variable): `labn_` measured flags vs held-out lab values (SMD on observed values); diagnosis codes vs eGFR / LVEF / valve grades.

**PS-Clinical:**
- **What's masked:** only `mean_meds`, `mean_util` and `smd_obs_<T.phys>` (`clin_ex` in `sens_primary32.py` line 89; `v21/paper2_grid.py` line 140).
- **Near-duplicates still in the 54-item panel:**
  - `pp_LVFUNC__ef` (echo EF), which is essentially LVEF, and LVEF is in PS-Clinical;
  - `pp_LAB__egfr`, which is derived from creatinine, age and sex, all of which are in PS-Clinical;
  - likely also `pp_LAB__bun` and `pp_LVFUNC__lv_sys_grade` (close correlates).
- **Effect:** PS-Clinical's base balance is flattered. This affects:
  - head-to-heads against PS-Clinical (paper2: "PS-CVD5 + CLMBR-T nominally worse than PS-Clinical, −4.9%");
  - "nothing adds to PS-Clinical", which is partly mechanical.
- **Within-rung contrasts** (PS-Clinical ± ECG) share the leak in both arms, so they are less affected.

**Fix for v1, if wanted:** re-mask in the summarize step from the saved per-trial SMDs (no refitting). Then mask `mean_meds` for hdPS on the 58-item panel, and mask echo EF, eGFR, and possibly BUN and LV systolic grade for PS-Clinical.

**Rule for v2:** define the held-out panel per PS specification with an explicit leakage map. For every PS input, list the held-out items that are the same quantity, derived from it, or the same code family, and mask them. Make a leakage audit of that map a gate before any balance result is computed.
