# MIMIC-IV: hdPS on the AI-EHR input window, with AI-ECG and AI-EHR arms (2026-10-15)

Queue: `docs/queue/QUEUE_2026_10_15_MIMIC_HDPS.md`. The design is otherwise that of `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md` (7 cardiovascular trials + PEPTIC; fixed C = 1; 1:1 greedy nearest neighbour on the PS logit, caliper 0.2 SD, without replacement; < 11 pairs = failed; per-trial AI-ECG PCs (32) and AI-EHR PCs (64, primary input `clmbr/prior_full`); the v21 within-trial permutation for both placebos).

- **Code:** `scripts/mimic/hdps_window.py`. It imports `v15_analyze`, `eval_longtail_balance`, `v13_common`, `scripts/v20/mimic_replication.py`, `scripts/v21/mimic_cvd5.py` and the existing `scripts/mimic/` modules. None of them is modified. Steps: `panels`, `gate`, `analyze`, `rho`, `summarize`, or `all`.
- **Outputs:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-hdps-20261015/` (umask 077), which holds `summary/summary.json`, `summary/tables.md` and `STATUS.md`. The rebuilt panels and per-trial cells are restricted: they are not committed.
- **Privacy:** aggregates only. Counts of 1–10 are suppressed. No per-trial pair counts, retention or ESS are given. No note text was opened.
- **Labels:** AI-ECG = BCL ECG embedding (32 PCs); AI-EHR = CLMBR-T, code-only (64 PCs).

## Verdict

1. **Both gates pass with max |Δ| = 0.**
   - **Gate 1:** under the original window, the new code rebuilds every trial's hdPS candidate panel exactly (same features, max |Δ| 0). Its level function equals `TrialData.lvl`. It reproduces every v20 demo and hdPS200 base / + ECG / + permuted-ECG cell, in both populations (arms and item tables).
   - **Gate 2:** the 6 PS-CVD5 arms run through the new code path equal `results_prior` exactly, in both populations.
   - **Summary code:** it reproduces the 10 published within-PS-CVD5 contrasts of `summary_prior` exactly.
2. **Leakage checks of hdPS-prior: all pass.** Over the 8.73 M input events of the candidate levels:
   - 0 events at or after the index admission time, and 0 at or after t0;
   - 0 index-admission diagnosis or procedure codes;
   - 0 diagnoses or procedures from an admission that was not earlier and discharged before the cut;
   - 0 exposure-drug features.

   **The investigator dx flags follow the PS-CVD5 rule instead** (any earlier admission, index admission excluded, no look-back), as the queue asked. That rule has no "discharged before the cut" condition: 13 of 45,107 analysed patients (0.03%) have an earlier admission discharged at or after the cut (audit S1).
3. **hdPS-prior improves on PS-CVD5, but much less than the v20 hdPS200.** Mean |SMD| on the 22 items, 7 trials:

   | Unmatched | PS-CVD5 | hdPS-prior | hdPS200 (v20) |
   |---|---|---|---|
   | 0.169 | 0.158 | 0.140 | 0.113 |

   - hdPS-prior vs PS-CVD5: 11.7% (7.1 to 16.8), 7/7, two-sided P = .016.
   - About 60% of the v20 hdPS's apparent advantage over PS-CVD5 (28.7%) came from the index stay: (0.140 − 0.113) / (0.158 − 0.113) = 0.60. hdPS-prior is 24.0% worse than hdPS200.
4. **On top of hdPS-prior, the AI-ECG adds; the AI-EHR does not.**
   - **+ AI-ECG:** 10.8% (7.2 to 15.7), 7/7, P = .008. Vs its permuted placebo: 12.9% (9.4 to 16.6), 7/7.
   - **+ AI-EHR:** −1.2% (−7.8 to 5.8), 4/7, P = .62. Vs its placebo: 2.9% (−3.1 to 9.2).
   - **+ both:** 10.0% (4.2 to 14.3), 6/7, P = .016.
   - **+ both vs + AI-EHR:** 11.0% (3.7 to 18.2), 6/7.
   - **+ both vs + AI-ECG:** −1.0%.
5. **"Demo + AI" vs conventional PS (Yale slide 9 panel D analogue).** Against hdPS-prior, two-sided:
   - PS-Demo + AI-ECG: −5.4% (−12.1 to 1.0);
   - PS-Demo + AI-EHR: −5.6% (−13.5 to 1.8);
   - PS-Demo + both: +5.8% (0.2 to 10.9), 6/7, P = .11;
   - PS-CVD5 + both: +7.9% (4.2 to 12.6), 7/7, P = .016.

   So each AI representation on a demographic base is about as good as hdPS-prior, slightly worse in point estimate, and the two together are slightly better. Against the v20 hdPS200, every Demo / PS-CVD5 + AI arm is worse (−14% to −31%).
6. **Agreement: no trial-specific gain.**
   - Mean |Δ log HR|: PS-CVD5 0.344 → hdPS-prior 0.239 (7/7 closer; benchmark-permutation P .83) → + AI-ECG 0.187 (5/7; .20) → + AI-EHR 0.240 (.97) → + both 0.213 (.41).
   - Every reported benchmark-permutation P is ≥ .17, so these are attenuation toward the null, not trial-specific correction.
7. **PEPTIC (negative control, RCT RR 1.05):**
   - hdPS-prior HR 1.20 (1.08–1.35), between PS-CVD5 1.51 and hdPS200 0.93;
   - + AI-ECG 1.15 (1.02–1.28); + AI-EHR 1.28 (1.14–1.43); + both 1.18 (1.05–1.32).
8. **Cell validity:** 0 failed cells and 0 overlap-invalid cells in all 192 cells. **Near-separation is present in the hdPS bases**:
   - the cells with > 10% of PS values outside [0.01, 0.99] are 12 of 48 hdPS-prior cells (3 of the 7 trials; max share 21%) and 24 of 48 hdPS200 cells (4 of 7; max 29%);
   - PS-CVD5 and PS-Demo cells have none.

   Dropping those trials leaves the AI-ECG result unchanged (11.8%, 5/5). The AI-EHR vs placebo contrast rises (to 9.0%, 4/4), but the AI-EHR still adds little on hdPS-prior (3.4%) (§5).

## 1. The hdPS-prior window

**Rule** (= the primary AI-EHR input, `build_meds_prior_only.py`): every input event of the candidate levels is strictly before cut = min(index admission time, t0), within the existing look-back of t0 − 365 d. The index ED stay before admission is kept, as for AI-EHR. The investigator dx flags use the PS-CVD5 rule (earlier admissions, no look-back; see Verdict 2).

| Part | v20 hdPS200 (original window) | hdPS-prior |
|---|---|---|
| Investigator dx flags (sparse) | roles.json dx flags. 5 v1.5 trials: earlier admissions only (v1.5 audit fix). SOAP II, ELITE II, PEPTIC: **index admission included** | the same flags from **earlier admissions only** (as PS-CVD5); PLATO's index-event features from earlier admissions discharged within 30 d (audit-fix convention); constant flags dropped |
| dx_ levels | 5 v1.5 trials: earlier admissions admitted in [t0 − 365 d, index admission). SOAP II / ELITE II / PEPTIC: **index admission** + earlier admissions in the look-back | earlier admissions (admittime < index admittime, not the index hadm, discharged before the cut) admitted within the look-back |
| px_ levels | dates in [t0 − 365 d, index day). 5 v1.5 trials: non-index admissions. 3 v20 trials: **any admission, including the index admission** | earlier admissions as for dx_, dated within the look-back |
| rx_ levels | order start in [t0 − 365 d, index day): **includes the index admission before the index day** | order start in [t0 − 365 d, cut) |
| lab_ "measured" | chart time in [t0 − 365 d, t0): **includes the index admission's pre-t0 draws** | chart time in [t0 − 365 d, cut) |
| Exposure drugs | orders matching the trial's exposure tokens removed | same |
| Levels, ranking, size, PS | once / sporadic / frequent (count panel) and one "measured" level per lab; ≥ 1% prevalence; \|log prevalence ratio\| on treatment; top 200; L2, C = 1 | unchanged |

**A correction to the queue's premise.** The index admission's *diagnosis codes* enter the v20 hdPS200 only in SOAP II, ELITE II and PEPTIC. In the 5 v1.5 trials, its dx_ / px_ levels and dx flags were already restricted to earlier admissions by the v1.5 audit fix (`scripts/v15/v15_mimic_auditfix.py`). In all 8 trials, though, the v20 hdPS reads the index stay's pre-t0 orders and lab-measured flags. In the original window:
- 49.0% of the hdPS input events are at or after the index admission time;
- 57.4% are in the index episode;
- the 369,228 index-admission dx/px events all come from the 3 v20 trials.

**Leakage checks** (aggregate; analysed patients; events feeding the retained candidate features):

| Check | hdPS-prior | v20 hdPS200 (original window), for contrast |
|---|---|---|
| Input events | 8,731,376 (labs 90.0%, rx 8.1%, dx 1.8%, px 0.1%) | 17,308,948 |
| At or after the index admission time | **0** | 8,474,819 (49.0%) |
| At or after t0 | **0** | 353,609 (dx timed at their admission's discharge: index-admission codes in the 3 v20 trials, plus earlier admissions overlapping t0) |
| Index-admission dx / px codes | **0** | 369,228 |
| dx / px from an admission that is not earlier or not discharged before the cut | **0** | 369,278 |
| Exposure-drug features | **0** | 0 |
| Share of input events in the index episode (index hadm, or the index ED stay [edregtime, admittime)) | 18.2% (labs 19.9%, rx 3.7%, dx 0.02%, px 0) | 57.4% |
| Patients with any index-episode input, among those with any input | 79.7% | 97.4% |
| Patients whose whole candidate input is the index episode, among those with any input | 41.3% (36.2% of all analysed patients; for hdPS-prior this is the index ED stay before admission) | 39.9% |

- **The retained index-episode events of hdPS-prior** are ED-stay labs before admission (most of them without the index hadm_id: 19.9% of lab events are in the index episode, 3.0% carry the index hadm_id) and orders with the index hadm_id timed before the admission time. The 0.02% of dx events fall in the index ED window because an earlier admission was discharged after the index ED registration; none comes from the index admission.
- **This mirrors the primary AI-EHR input.** There, the index ED stay is 8.7% of events and the whole input for 32.3% of patients (`docs/mimic/AUDIT_MIMIC_PRIMARY_SWITCH.md`). The AI-EHR input has no 365-day look-back, which may explain its lower share.
- **Prior dx flags:** equal to `baseline.parquet` in the 5 v1.5 trials (0 discordant patients, as expected). They differ in all flags in the 3 v20 trials, where the index admission is now excluded.

**Size of the input:**

| | hdPS-prior | v20 hdPS200 |
|---|---|---|
| Candidate levels per trial | median 482.5 (347–1,150) | median 716 (522–1,483) |
| Analysed patients with no candidate-level input | 12.3% (6.9–18.4% by trial) | 0.6% |
| … and no dx flag either | 11.4% | |
| Top-200 overlap between the two windows | 56–140 of 200 by trial | |

- The domain mix of the top 200 shifts by trial. In SOAP II and PEPTIC, two of the three trials that lost their index-admission codes, the prior top 200 has fewer dx levels and more rx levels (ELITE II follows the other pattern). In most of the other trials it has more lab and dx levels and fewer rx levels (TRANSFORM-HF has fewer lab levels).
- PS inputs (base): 212–216 for hdPS-prior and hdPS200; 244–248 with AI-ECG, 276–280 with AI-EHR, 308–312 with both.

## 2. Held-out panel and masks

- **Main comparison: 22 items.** These are A core labs and vitals (8), B other labs (13) and C ventilation at t0 (1). Block D (utilisation: prior admissions and ED visits in 365 d, days from admission to t0, ICU before t0) is excluded for every arm, as when AI-EHR is in a contrast.
- **26-item version:** reported for the arms without AI-EHR, as a sensitivity.
- **Mask check** (`pipeline.md` §6: same quantity, derived, or same code family; or pooled |ρ| ≥ 0.80 with a PS input). I computed Pearson ρ between each held-out item (observed values) and each PS input of the base (sparse flags + top-200 levels, full analysed sample), per trial. Pooled ρ = the observation-weighted mean of the per-trial ρ for the same item–input pair.

| Base | Max pooled \|ρ\|, blocks A–C (item; input) | Max per-trial \|ρ\|, A–C | Block D |
|---|---|---|---|
| hdPS-prior | 0.315 (creatinine; CKD flag) | 0.365 | prior admissions 0.726 (rx "sodium" = first drug token, sporadic level); ED visits 0.528 |
| hdPS200 (v20) | 0.475 (creatinine; rx sevelamer) | 0.593 | ICU before t0 0.620 (lab "intubated" measured); days admission → t0 0.519; prior admissions 0.501 |

- **No held-out item in A–C reaches 0.80 or the soft-proxy range (0.50–0.80) for hdPS-prior.** None is the same quantity as an input, or derived from one: the inputs are diagnosis, order and lab-*measured* codes, never values. Ventilation at t0 has a pooled |ρ| of 0.14 (hdPS-prior) and 0.28 (hdPS200).
- **Block D is derivable from the hdPS-prior inputs:**
  - "prior admissions in 365 d" is structurally implied by any dx_ / px_ level, because those come only from earlier admissions within the look-back;
  - ED visits are partly implied by ED-stay lab-measured levels;
  - the soft proxies reach 0.73.

  So the 22-item panel is the right comparison for every hdPS arm. The 26-item hdPS numbers are a sensitivity that includes leakage-affected items. The 26-item hdPS200 is also more favourable to hdPS: 0.105 vs 0.113 on 22 items, with a block D mean of 0.061.

## 3. Results (7 cardiovascular trials, all analysed patients, 22 items)

**Per arm.** Mean |SMD| is the across-trial mean of per-trial means; A, B and C are domain means of |SMD|; % is the share of items with |SMD| < 0.1.

| Arm | Mean \|SMD\| | % \|SMD\| < 0.1 | A | B | C | Mean \|Δ log HR\| | PEPTIC HR (95% CI) |
|---|---|---|---|---|---|---|---|
| Unmatched | 0.169 | 41.6 | 0.188 | 0.160 | 0.138 | | |
| PS-CVD5 | 0.158 | 44.2 | 0.170 | 0.153 | 0.125 | 0.344 | 1.51 (1.35–1.69) |
| PS-CVD5 + AI-ECG | 0.147 | 51.9 | 0.162 | 0.139 | 0.121 | 0.326 | 1.39 (1.24–1.55) |
| PS-CVD5 + AI-EHR | 0.146 | 51.3 | 0.159 | 0.139 | 0.136 | 0.278 | 1.28 (1.14–1.43) |
| PS-CVD5 + AI-ECG + AI-EHR | 0.129 | 51.9 | 0.138 | 0.125 | 0.104 | 0.240 | 1.21 (1.08–1.35) |
| **hdPS-prior** | **0.140** | 48.1 | 0.147 | 0.137 | 0.110 | 0.239 | 1.20 (1.08–1.35) |
| hdPS-prior + AI-ECG | 0.124 | 55.2 | 0.132 | 0.121 | 0.107 | 0.187 | 1.15 (1.02–1.28) |
| hdPS-prior + AI-EHR | 0.141 | 48.7 | 0.152 | 0.136 | 0.120 | 0.240 | 1.28 (1.14–1.43) |
| hdPS-prior + AI-ECG + AI-EHR | 0.126 | 50.6 | 0.134 | 0.121 | 0.121 | 0.213 | 1.18 (1.05–1.32) |
| hdPS-prior + permuted AI-ECG | 0.143 | 48.7 | 0.151 | 0.139 | 0.125 | 0.258 | 1.22 (1.09–1.37) |
| hdPS-prior + permuted AI-EHR | 0.145 | 48.7 | 0.158 | 0.140 | 0.111 | 0.231 | 1.27 (1.13–1.42) |
| PS-Demo | 0.166 | 40.3 | 0.186 | 0.156 | 0.141 | 0.337 | 1.53 (1.36–1.71) |
| PS-Demo + AI-ECG | 0.147 | 53.2 | 0.163 | 0.139 | 0.130 | 0.315 | 1.39 (1.24–1.56) |
| PS-Demo + AI-EHR | 0.147 | 50.0 | 0.161 | 0.140 | 0.133 | 0.239 | 1.26 (1.13–1.42) |
| PS-Demo + AI-ECG + AI-EHR | 0.131 | 51.3 | 0.144 | 0.126 | 0.100 | 0.273 | 1.23 (1.10–1.37) |
| PS-Demo + permuted AI-ECG | 0.170 | 41.6 | 0.191 | 0.159 | 0.135 | 0.373 | 1.61 (1.42–1.81) |
| PS-Demo + permuted AI-EHR | 0.175 | 37.7 | 0.194 | 0.165 | 0.146 | 0.215 | 1.68 (1.49–1.90) |
| hdPS200 (v20; sensitivity) | 0.113 | 60.4 | 0.107 | 0.118 | 0.087 | 0.220 | 0.93 (0.83–1.04) |
| hdPS200 + AI-ECG | 0.105 | 63.6 | 0.104 | 0.108 | 0.065 | 0.179 | 0.94 (0.84–1.06) |
| hdPS200 + AI-EHR | 0.110 | 64.3 | 0.113 | 0.109 | 0.099 | 0.210 | 0.99 (0.88–1.12) |
| hdPS200 + AI-ECG + AI-EHR | 0.095 | 68.8 | 0.095 | 0.095 | 0.077 | 0.210 | 0.94 (0.83–1.06) |
| hdPS200 + permuted AI-ECG | 0.115 | 60.4 | 0.115 | 0.118 | 0.069 | 0.165 | 0.93 (0.83–1.05) |
| hdPS200 + permuted AI-EHR | 0.117 | 61.0 | 0.119 | 0.117 | 0.086 | 0.212 | 0.97 (0.86–1.09) |

- PEPTIC's mean |SMD| on 22 items: unmatched 0.189, PS-CVD5 0.196, hdPS-prior 0.151, + AI-ECG 0.136, + both 0.123, hdPS200 0.075.
- On 22 items, PS-CVD5 + AI-ECG vs PS-CVD5 is 7.1% (1.9 to 14.9). The published 6.6% is the 26-item value. The AI-EHR contrasts equal the published values (7.7%, 18.6%).

**Contrasts.** Relative reduction in mean |SMD| of a vs b, over items observed in both cells. 95% CI from 4,000 trial-bootstrap resamples (seed 20261001). "Lower" = trials lower. P = exact sign-flip (one-sided for a representation vs its base or placebo, two-sided otherwise). The benchmark-permutation P uses 20,000 draws.

| Contrast (a vs b) | Rel. red. (95% CI) | Lower; P | % < 0.1 b → a | \|Δ log HR\| b → a (closer; P) | Bench.-perm. P |
|---|---|---|---|---|---|
| **hdPS-prior vs PS-CVD5** (two-sided) | **11.7% (7.1 to 16.8)** | 7/7; .016 | 44.2 → 48.1 | 0.344 → 0.239 (7/7; .016) | .83 |
| **hdPS-prior + AI-ECG vs hdPS-prior** | **10.8% (7.2 to 15.7)** | 7/7; .008 | 48.1 → 55.2 | 0.239 → 0.187 (5/7; .086) | .20 |
| **hdPS-prior + AI-EHR vs hdPS-prior** | **−1.2% (−7.8 to 5.8)** | 4/7; .617 | 48.1 → 48.7 | 0.239 → 0.240 (2/7; .52) | .97 |
| **hdPS-prior + both vs hdPS-prior** | **10.0% (4.2 to 14.3)** | 6/7; .016 | 48.1 → 50.6 | 0.239 → 0.213 (5/7; .34) | .41 |
| hdPS-prior + AI-ECG vs + permuted AI-ECG | 12.9% (9.4 to 16.6) | 7/7; .008 | 48.7 → 55.2 | 0.258 → 0.187 (6/7; .023) | .20 |
| hdPS-prior + AI-EHR vs + permuted AI-EHR | 2.9% (−3.1 to 9.2) | 5/7; .195 | 48.7 → 48.7 | 0.231 → 0.240 (4/7; .61) | .76 |
| hdPS-prior + permuted AI-ECG vs hdPS-prior (two-sided) | −2.3% (−5.1 to 1.2) | 2/7; .250 | 48.1 → 48.7 | 0.239 → 0.258 | .38 |
| hdPS-prior + permuted AI-EHR vs hdPS-prior (two-sided) | −4.2% (−9.0 to −0.2) | 1/7; .141 | 48.1 → 48.7 | 0.239 → 0.231 | .62 |
| **hdPS-prior + both vs + AI-EHR** | **11.0% (3.7 to 18.2)** | 6/7; .023 | 48.7 → 50.6 | 0.240 → 0.213 (4/7; .34) | .20 |
| hdPS-prior + both vs + AI-ECG | −1.0% (−11.8 to 6.0) | 4/7; .578 | 55.2 → 50.6 | 0.187 → 0.213 | .69 |
| hdPS-prior + AI-EHR vs + AI-ECG (two-sided) | −13.5% (−21.6 to −6.6) | 0/7; .016 | 55.2 → 48.7 | 0.187 → 0.240 | 1.00 |
| PS-Demo vs hdPS-prior (two-sided) | −19.1% (−23.5 to −14.7) | 0/7; .016 | 48.1 → 40.3 | 0.239 → 0.337 | .40 |
| **PS-Demo + AI-ECG vs hdPS-prior** (two-sided) | −5.4% (−12.1 to 1.0) | 2/7; .234 | 48.1 → 53.2 | 0.239 → 0.315 | .40 |
| **PS-Demo + AI-EHR vs hdPS-prior** (two-sided) | −5.6% (−13.5 to 1.8) | 3/7; .297 | 48.1 → 50.0 | 0.239 → 0.239 | .38 |
| **PS-Demo + both vs hdPS-prior** (two-sided) | 5.8% (0.2 to 10.9) | 6/7; .109 | 48.1 → 51.3 | 0.239 → 0.273 | .56 |
| PS-CVD5 + AI-ECG vs hdPS-prior (two-sided) | −5.2% (−10.4 to 0.6) | 2/7; .172 | 48.1 → 51.9 | 0.239 → 0.326 | .67 |
| PS-CVD5 + AI-EHR vs hdPS-prior (two-sided) | −4.5% (−8.9 to −0.8) | 1/7; .047 | 48.1 → 51.3 | 0.239 → 0.278 | .76 |
| PS-CVD5 + both vs hdPS-prior (two-sided) | 7.9% (4.2 to 12.6) | 7/7; .016 | 48.1 → 51.9 | 0.239 → 0.240 | .32 |
| PS-Demo + AI-ECG vs PS-Demo | 11.5% (6.7 to 16.8) | 7/7; .008 | 40.3 → 53.2 | 0.337 → 0.315 | 1.00 |
| PS-Demo + AI-EHR vs PS-Demo | 11.4% (5.1 to 17.4) | 6/7; .016 | 40.3 → 50.0 | 0.337 → 0.239 (5/7; .031) | .71 |
| PS-Demo + both vs PS-Demo | 20.9% (16.6 to 26.4) | 7/7; .008 | 40.3 → 51.3 | 0.337 → 0.273 (7/7; .008) | .73 |
| PS-Demo + AI-ECG vs + permuted AI-ECG | 13.2% (7.5 to 18.9) | 7/7; .008 | 41.6 → 53.2 | 0.373 → 0.315 | 1.00 |
| PS-Demo + AI-EHR vs + permuted AI-EHR | 15.8% (11.7 to 21.0) | 7/7; .008 | 37.7 → 50.0 | 0.215 → 0.239 | .71 |
| PS-Demo + both vs + AI-EHR | 10.8% (5.7 to 16.0) | 7/7; .008 | 50.0 → 51.3 | 0.239 → 0.273 | .61 |

The full set, with the 26-item versions and all 8 trials, is in `summary/tables.md`.

**hdPS200 (v20, index stay included): sensitivity**

| Contrast | Rel. red. (95% CI) | Lower; P | Bench.-perm. P |
|---|---|---|---|
| hdPS200 vs PS-CVD5 (two-sided) | 28.7% (18.6 to 39.8) | 7/7; .016 | .61 |
| hdPS-prior vs hdPS200 (two-sided) | −24.0% (−39.3 to −13.1) | 0/7; .016 | .56 |
| + AI-ECG vs hdPS200 | 6.9% (−1.5 to 16.7) | 4/7; .125 | .82 |
| + AI-EHR vs hdPS200 | 2.6% (−2.9 to 7.3) | 5/7; .180 | .17 |
| + both vs hdPS200 | 16.0% (8.6 to 24.5) | 6/7; .016 | .26 |
| + AI-ECG vs + permuted AI-ECG | 8.6% (1.8 to 17.0) | 6/7; .039 | .82 |
| + AI-EHR vs + permuted AI-EHR | 5.9% (0.8 to 11.1) | 4/7; .062 | .48 |
| + both vs + AI-EHR | 13.8% (9.0 to 21.5) | 7/7; .008 | 1.00 |
| PS-Demo + AI-ECG / + AI-EHR / + both vs hdPS200 (two-sided) | −30.7% / −30.9% / −16.8% | 0/7, 0/7, 1/7 | |
| PS-CVD5 + AI-ECG / + AI-EHR / + both vs hdPS200 (two-sided) | −30.4% / −29.5% / −14.2% | 0/7, 0/7, 2/7 | |

**All 8 trials (with PEPTIC):**
- hdPS-prior vs PS-CVD5: 13.3% (8.2 to 18.2), 8/8;
- + AI-ECG: 10.7% (7.5 to 14.9), 8/8;
- + AI-EHR: 0.1% (−6.4 to 6.3), 5/8;
- + both: 11.2% (5.5 to 15.4), 7/8;
- + both vs + AI-EHR: 11.1% (4.9 to 17.2), 7/8.

## 4. Cell validity

| Base | Cells | Failed (< 11 pairs) | Overlap-invalid | Cells with > 10% extreme PS (trials) | Median in-sample C: base / + AI-ECG / + AI-EHR / + both |
|---|---|---|---|---|---|
| PS-CVD5 | 48 | 0 | 0 | 0 (0) | 0.662 / 0.704 / 0.724 / 0.755 |
| PS-Demo | 48 | 0 | 0 | 0 (0) | 0.653 / 0.695 / 0.722 / 0.750 |
| hdPS-prior | 48 | 0 | 0 | 12 (3 of 7) | 0.740 / 0.781 / 0.775 / 0.808 |
| hdPS200 (v20) | 48 | 0 | 0 | 24 (4 of 7) | 0.819 / 0.831 / 0.837 / 0.846 |

- "Extreme" = PS < 0.01 or > 0.99. The largest share in any cell is 21% for hdPS-prior (+ both) and 29% for hdPS200 (+ both). One hdPS200 cell has an in-sample C above 0.90.
- **Retention:** every cell keeps ≥ 50% of the smaller arm. For hdPS-prior, 1 of 8 cells per arm (2 for + both) keeps 50–90%; for hdPS200, 3–4 of 8.
- **As at Yale, rich hdPS models approach separation:** about 270 inputs with AI-EHR, 308–312 with both. The overlap rule is not violated.

## 5. Sensitivities of the main contrasts (7 trials, 22 items)

| Contrast | Primary | Overlap-invalid cells dropped | Trials dropped where either compared cell has > 10% extreme PS |
|---|---|---|---|
| hdPS-prior vs PS-CVD5 | 11.7% (7/7) | identical (no invalid cells) | 13.2% (8.9 to 18.1), 6/6 |
| hdPS-prior + AI-ECG vs hdPS-prior | 10.8% (7/7) | identical | 11.8% (6.6 to 18.6), 5/5 |
| hdPS-prior + AI-EHR vs hdPS-prior | −1.2% (4/7) | identical | 3.4% (−4.1 to 11.9), 3/4 |
| hdPS-prior + both vs hdPS-prior | 10.0% (6/7) | identical | 8.2% (−2.2 to 14.6), 3/4 |
| hdPS-prior + AI-EHR vs + permuted AI-EHR | 2.9% (5/7) | identical | 9.0% (5.9 to 14.6), 4/4 |
| 26 items (block D included; leakage-affected for hdPS): hdPS-prior vs PS-CVD5 / + AI-ECG vs hdPS-prior | 12.9% / 10.3% | | |

The near-separation sensitivity has only 4–6 trials, so its CIs are crude. The AI-EHR placebo contrast rises to 9.0% there, which suggests that the AI-EHR's null result on hdPS-prior is partly driven by the near-separated trials. Its point estimate against the base stays small (3.4%).

## 6. Reading

- **Like for like, hdPS still beats PS-CVD5, but by less.** Restricted to the AI-EHR input window, hdPS improves on PS-CVD5 by 11.7% (7/7). That is less than half of the v20 hdPS's 28.7%. The difference is the index stay's pre-t0 order and lab stream (all trials) and the index admission's discharge-coded diagnoses (3 trials).
- **The AI-ECG adds on top of a like-for-like hdPS** in MIMIC: 10.8%, 7/7, and 12.9% vs its placebo. That is the size of its gain on PS-CVD5 or PS-Demo. On the v20 hdPS200 it adds less (6.9%, 4/7).
- **The AI-EHR adds nothing on top of hdPS-prior** (−1.2%; 2.9% vs placebo). The two read largely the same coded history (prior diagnoses, orders, lab-ordering codes, the index ED stay). On the demographic base, AI-EHR (11.4%) and AI-ECG (11.5%) are equal, and each brings PS-Demo to about the level of hdPS-prior (−5.6% and −5.4% vs hdPS-prior, CIs including 0). This is the MIMIC analogue of Yale's finding that AI-EHR does not add beyond hdPS.
- **The AI-ECG and AI-EHR are complementary on every base.** + both vs + AI-EHR: 11.0% (hdPS-prior), 10.8% (Demo), 13.8% (hdPS200). PS-Demo + both is slightly better than hdPS-prior (5.8%, 6/7).
- **Agreement:** every move in |Δ log HR| is attenuation, not trial-specific (every reported benchmark-permutation P ≥ .17). PEPTIC moves toward the null with hdPS-prior (1.51 → 1.20) and slightly further with the AI-ECG (1.15). It reaches the null only with the v20 hdPS200 (0.93), which reads the index stay.

## 7. Limitations

- **Post hoc.** This analysis was added after the v20, v21 and AI-EHR results were seen, on the user's request (2026-10-15). hdPS-prior is the like-for-like comparator for the AI-EHR primary input. The v20 hdPS200 becomes a sensitivity analysis.
- **The index ED stay is kept**, as in the AI-EHR primary input. For 36.2% of analysed patients it is the whole hdPS-prior candidate input, and 18.2% of the input events come from it.
- **Remaining differences from the AI-EHR input:**
  - hdPS keeps the 365-day look-back, so it sees less history than AI-EHR;
  - the dx flags have no look-back;
  - AI-EHR also removes the gate-condition ICD prefixes and orders without an NDC, and adds visit tokens;
  - both take px from earlier admissions discharged before the cut; hdPS uses chartdate only for the look-back and the count, while AI-EHR times procedures at that discharge.
- **The rx_ cut is precise in time but differs from v20:** v20 used the calendar index day for rx_ and t0 for lab_; hdPS-prior uses min(admission time, t0) for both. Orders between midnight of the index day and the admission time now count.
- **7 trials:** the CIs are crude. Inference rests on the per-trial direction and the exact sign-flip P (minimum one-sided P 1/128).
- **Near-separation** in 3 of 7 trials for hdPS-prior (§4–5).
- **Single analysis population** (all analysed patients). The no-index-day-ECG population was not run for the new arms.
