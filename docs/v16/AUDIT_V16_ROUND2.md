# v1.6 sweep audit, round 2 (S5, S6, S7, covars2 + global multiplicity) — 2026-09-26

This is an independent, skeptical second-round audit of S5 (negative controls), S6 (extended balance), S7 (diagnosis removal)
and the covars2 expanded covariate set. It follows the round-1 methods in `AUDIT_V16.md`:
- benchmark shuffle (RCT log HR and SE permuted jointly across trials);
- the 10 comparator clusters (`audit_v16.CLUSTER`);
- leave-one-trial-out (LOO).

Audit code is its own (copies in `scripts/v16/audit2/`; run from the scratch directory). It does not call any sweep's summary functions: an exact sign-flip, BH, pairing, shuffle and clustering
are written in `a2_common.py`. Scripts and aggregate outputs are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-audit2/`:
- `s5_check.py`, `s6_check.py`, `s6_synth.py`, `s7_check.py`, `global_fdr.py`;
- `*_recompute.csv`, `global_fdr_cells.csv`, `s6_global_bh.csv`;
- `covars2_check/`.

The audit holds aggregates only. It contains no patient-level rows and no patient counts of 1–10. "k/18" are trial counts.

## Verdict table

| # | Check | Verdict | Fix / consequence |
|---|---|---|---|
| 1 | Independent recomputation | **PASS** | Every recomputed value equals the sweep outputs, with max \|Δd\| 1e-16 and \|Δp\| 6e-17. Coverage: S5 15 rung × metric cells plus pooled σ; S6 144 panel × cell × metric cells; S7 40 cell × metric cells plus shuffles. Headline values: S6 sparse x2np non-proximal \|SMD\| 0.0793 → 0.0722 (14/18, p = 0.0011, cluster p = 0.0078); S7 AF removal \|Δ\| −0.054 (14/18, p = 0.0061, shuffle p = 0.0033 with 20k draws; reported 0.0026). |
| 2 | covars2 validity | **CONCERN** | Date logic is strictly pre-index and verified empirically. Five problems: (i) `index_setting_*` (index day) enter the S6 x2 panels despite the builder's own warning; (ii) `recent_hosp_30d` and `n_inpatient_stays_365` count the ongoing index admission; (iii) `zip_*` use the current address, which is post-index; (iv) composite scores are not PS-overlap-tagged; (v) HFRS is applied to 365-d all-setting codes, so the Gilbert cut-points are not calibrated. Exposure-leak exclusions, Charlson/Elixhauser (Quan 2005) and the HFRS weights (109 codes, 0 mismatches) PASS. The total-protein/PT fix PASSES. |
| 3 | S5 NCO design and power | **CONCERN** | Matched sets are identical to S1 (0 deviations over 1,134 arms). Calibration arithmetic is correct. Eligibility is blind to the arm contrast. Four plausibility gaps (below). **Power is the binding limit.** The 80% minimum detectable ECG − base change in pooled σ is about 0.018–0.022, about 21–23% of the base σ. For per-trial b² − se² it is 0.023–0.039, which is at least the whole base systematic error (0.013–0.038). "S5 null" therefore means *uninformative*, not *no effect*. |
| 4 | S6 measures | **PASS with concerns** | Energy distance equals the brute-force value (7-D) and scipy (1-D) to 1e-10. The outcome model has no treatment term and is fitted in comparators of the unmatched rows; the same β is used for every arm, so no matched-set outcome information is selected on. Mahalanobis ridge λ = 0.1 on standardised components is sane. "Robust" is applied as stated, with halves checked for direction only. PS-overlap drops are applied per cell (demo 1, min-7 11–17, sparse 32–45, clinical 40–54 variables). But hdPS200 drops exactly the sparse list, so covars2 dx variables built from ICD roots already selected into the hdPS are not excluded. Key finding 10 misstates z² as robust. The label "sparse, 50% code dropout" is ambiguous inside comma lists. |
| 5 | S7 design | **PASS with concerns** | The removal order uses unmatched treatment \|SMD\| only (no outcome). Common-10 = demo + the 7 most prevalent shared flags, with no extras, as documented. The benchmark shuffle permutes rb and rs **jointly**. Duplicate designs (4 of 46) enter the BH, so the AF shuffle q is 0.049 over 46 cells but 0.055 over the 42 distinct designs. S5, S6 and S7 default to `Pool(min(workers, 40))`, which is above the container's 32-process rule. |
| 6 | Global multiplicity (S1–S7) | **CONCERN (claims narrowed)** | There are 129 unique full-cohort ECG-vs-base cells after numerical de-duplication. Under BH within metric: \|Δlog HR\| **0/129** (min q 0.058–0.068); benchmark-shuffle p **0/129** (min q 0.052); z² 78/129 significant, but only 5 of those have shuffle p < 0.05; mean \|SMD\| 109/129; C-statistic 110/129. S5 NCO: 0/90 over the 3 NCO sets (min q 0.107). S6: all 127 "robust" balance flags survive BH over the 236 unique S6 balance tests, but only 75 are p < 0.05 in both halves. M_eff (Li–Ji) is 17–22 per metric over 17 complete trials. |
| 7 | Markdown claims | **CONCERN** | The edits are listed below. S6 finding 10 is factually wrong. S7 "consistent with ECG encoding AF" is contradicted by S7's own substitution result. S5 omits a nominal own-calibration z² result and overstates the strict-set FDR survival. COVARIATES2 has four statements that need correction. |
| 8 | Privacy (docs/v16/*.md) | **PASS** | No patient or event counts of 1–10 were found. S5 event table: all cells are 0, ≥ 11 or `<11`. COVARIATES2 uses `<11` 82 times, and summary_by_arm has no percentage implying 1–10. "n (x%)" and "k/18" patterns are trial counts only. Minor: `claude-v16-s6-balance/audit.md` and `key_findings.md` are mode 644 inside a restricted directory; they hold aggregates, but chmod 600 anyway. |

## Details

### 1. Recomputation
**S7** (`s7_recompute.csv`). The audit recomputed these cells on \|Δ\|, z², mean \|SMD\| and C-statistic, with cluster p, LOO max p and a 20k-draw shuffle:
- sparse, loo_AF, cum_k1, cum_k3, cum_k8, demo, common10, noextras, loo_PAD, rand0_k4.

All values reproduce `summary_ecg.csv`. The shuffle p agrees within Monte-Carlo error (for example AF 0.0033 vs 0.0026; PAD z² 0.0076 vs 0.0096).

AF-removal diagnostics:
- **Halves.** A −0.014 (p = 0.52); B −0.056 (p = 0.10).
- **Placebos.** vs shufECG −0.024 (p = 0.34); vs noise −0.043 (p = 0.011).
- **loo_AF+ECG − sparse+ECG.** +0.0007 (p = 0.97).
- **loo_AF base − sparse base.** +0.035 (7/18, p = 0.10).
- **loo_AF+ECG − sparse base.** −0.019 (p = 0.066).
- **Concentration.** The largest single trial accounts for 28% of Σ\|d\| (transform-hf) and the top 3 for 49%. Dropping the top trial gives −0.037 (p = 0.012).

So the "gain" is a no-worse ECG arm set against a worsened base.

**S6** (`s6_recompute.csv`). The audit recomputed, for all 6 cells × 8 measures × 3 panels, d, k, p, cluster p, LOO and the half-A/B p. It also checked the replicated matched sets: max rep_dev_mean_smd = 0 and 0 pair-count mismatches.

Headline values:

| cell | measure | ECG − base (base → ECG) | k | p | cluster p | half A p | half B p |
|---|---|---|---|---|---|---|---|
| sparse x2np | maha_all | −0.046 | 15/18 | 0.0002 | 0.0098 | 0.085 | 0.0025 |
| sparse x2np | ks_mean | −0.0043 | 14/18 | 0.0005 | 0.0098 | 0.018 | 0.069 |
| sparse x2np | ob_signed | 0.110 → 0.091 | 12/18 | 0.0073 | 0.012 | 0.038 | 0.67 |

- The energy-distance reductions reproduce: demo −25.8%, minimal-7 −21.2%, clinical −11.8%.

**S5** (`s5_check.py`).
- NCOs per trial: median 26 (13–35).
- Unmatched: mean \|b\| 0.221, b² − se² 0.028, pooled σ 0.139.
- demo \|b\| −0.0089 (p = 0.207).
- clinical \|b\| −0.0218 (p = 0.044).
- clinical z² −0.160 (p = 0.0071).
- sparse pooled σ 0.091 → 0.074. Own arm-swap permutation p = 0.020 (400 perms); reported 0.034 (500 perms).
- Calibrated-agreement values reproduce: pooled-LOO demo \|Δ\| −0.058 (p = 0.030); own demo \|Δ\| −0.091 (p = 0.009).
- The calibration arithmetic b − μ, √(se² + σ²) is exact to 2e-16.

### 2. covars2 (details in `covars2_check/`)
**(a) Windows.**
- Every date comparison is strict `< idx`: dx, px, rx, labs, visits, Epic encounters, and discharge-before-index for hospital encounters.
- Re-deriving four variables on two trials gives 100% agreement with the strict rule (INR 99.8%, same-timestamp ties). Including the index day would change 2–32% of values.
- **No post-index clinical leakage was found.** Three index-context problems remain:
  1. **`index_setting_inpatient/ed/outpatient` enter S6.** They are domain `index_context` and status `kept` in 18/18 trials, but `s6_balance.load_extra` does not drop them. COVARIATES2 itself says to exclude them where strictly pre-index covariates are required.
  2. **`recent_hosp_30d` and `n_inpatient_stays_365` count an inpatient stay that starts before index and is still ongoing** (build_v16_covars2.py ~l.921: `v.s < idx` with no `v.e < idx`). That is, they count the index admission. recent_hosp_30d = 1 in 59–98% of inpatient-initiated patients vs 3–11% of others, so it is effectively an index-setting proxy. `n_hf_hosp` already applies `v.e < idx`; do the same here.
  3. **`zip_out_of_state` and `zip_missing` use the current (extract-date) Epic address.** The dictionary definition says so, but the domain is `social`. Tag it post-index and exclude it.

  Because index-day ECGs are allowed by design, an ECG taken in the index encounter can "see" index acuity. Balance gains on (1)–(2) are therefore not pure pre-index balance. These are 5 of about 350 variables, so the effect on panel means is small but directional.

**(b) Exposure leak.**
- Dropped medication classes match every trial's arms. Examples:
  - EAST-AFNET4 drops AAD, BB, non-DHP CCB and digoxin;
  - PARADIGM drops ACEi, ARB and ARNI;
  - the DM trials drop SGLT2 and DPP4, with metformin recomputed without combination tokens.
- Leak tags (INR, anticoagulation clinic, Z79.01/.02/.84, prior ablation) are removed in S6.
- Minor gaps:
  - rx_arni_365 is kept in ELITE-II/ONTARGET, where valsartan defines exposure;
  - sotalol stays in rx_antiarrhythmic in COMET;
  - fluticasone is missing from inhaled respiratory drugs;
  - the influenza-vaccine rx tokens barely fire (CPT carries that variable).
- Prior use of the study class itself cannot be measured because the class is dropped. That is acceptable for new-user designs; state it in the doc.

**(c) HFRS.**
- 109 codes, weight sum 173.2, 0 mismatches with the Gilbert 2018 table. Spot-checked: F00 7.1, G81 4.4, G30 4.0, I69 3.7, R29 3.6, N39 3.2, W19 3.2, R54 2.2, Z99 0.8, R50 0.1.
- F00, U80 and X59 do not exist in ICD-10-CM, so they never fire.
- Gilbert used 2 years of *hospital* records. Here it is 365 d of all-setting codes: hfrs ≥ 5 in 39–62% and > 15 in 12–24% of the checked trials.
- The cut-points are not calibrated. Relabel `hfrs_ge5`.

**(d) Charlson / Elixhauser.**
- All 17 Charlson and 31 Elixhauser Quan-2005 ICD-10 lists match, including CHF, mild/severe liver and renal. The weights (Charlson 1/2/3/6; van Walraven) are correct, and the hierarchies are applied.
- elixhauser_count maxes at 30 (HTN merged), but the doc says 31.
- **These composites have no `ps_overlap` tag: charlson_score, elixhauser_vw/count, gagne_ccs, cha2ds2vasc, chads2, hasbled and dcsi.** CHA2DS2-VASc is a near-deterministic function of sparse PS inputs.
- These lab/vital summaries are not tagged either: sbp_mean_365, hb_lt10, egfr_lt30, weight/height. They sit in the clinical PS.
- **Unaffected:** the x2np non-proximal claim at demo/minimal-7.
- **Affected:** the "held-out" status of these variables at sparse and clinical.

**(e) Total protein / PT.**
- Concept 3020630 (LOINC 2885-2) mixes two sources: PROT (median 6.9 g/dL) and LABPROT (median 12.0, i.e. PT in seconds).
- The builder keeps `src = 'PROT'`. Cohort medians are 6.7–6.8 g/dL.
- INR (3022217, 6301-6): median 1.09–1.15.
- True PT (3034426) is too sparse to use.
- Caveats for the doc:
  - "troponin_hs" is hs-TnT;
  - HSCRP has median 10.7 mg/L, so it is not the cardiovascular-risk hsCRP assay range;
  - TROPONINI has 9999999 sentinels, which the plausibility cap removes.

**(f) ECG-proximal block.**
- These are not tagged: MI/ACS (prior_mi_ever, cci_mi, acute_mi_365, acs_365; Q waves / ST changes), CHF-weighted composites (elixhauser_vw, charlson_score, gagne_ccs), lab_bnp, and HF drugs (ARNI, MRA, loop).
- The x2np "non-ECG-proximal" panel therefore still holds some ECG-encodable content. Its gains are an upper bound on "non-ECG" balance.

### 3. S5 negative controls
**Plausibility (independent judgement).** The hard and caution lists are sensible. Additions:

1. **EAST-AFNET4 rate control includes diltiazem and verapamil** (`trial_specs.RATE_CONTROL`), but `CLASSES['east-afnet4'] = ['AAD', 'BB']`. Non-DHP CCB gingival hyperplasia (dental_caries, kept with 28/138 events) and oedema (plantar_fasciitis, carpal tunnel) were not considered. Add CCB-caution.
2. **Amiodarone ophthalmic monitoring** (AAD trials: EAST-AFNET4, CABANA-v2). This raises the ascertainment of blepharitis, chalazion and pterygium, as for cataract, which is excluded. Add these as cautions.
3. **Dermatology surveillance under photosensitising drugs.** Thiazide (ALLHAT) and amiodarone raise the detection of benign_skin_neoplasm (D22/D23) and seborrheic_keratosis (L82), which are kept. Add cautions.
4. **Warfarin INR-clinic contact** (3 DOAC trials) is a differential post-index ascertainment route for every visit-detected NCO. The NCOs test for it correctly, but a baseline ECG cannot fix it. The DOAC trials therefore dilute any ECG signal.

Combination HCTZ products were considered but are negligible in this data: "losartan-hctz" orders are < 11 in 2022 (covars2 audit).

**Eligibility, matched sets, calibration.**
- **Eligibility.** Pooled events ≥ 30 on the full unmatched cohort. It uses NCO events only (no HR and no primary outcome), is fixed before matching and is shared by the halves. `pooled or per_arm` in `run` is equivalent to pooled, because per-arm ≥ 20 implies ≥ 40 pooled.
- **Matched sets.** Identical to S1.
- **Calibration.** This is the simplified OHDSI model: constant μ and σ, b* = b − μ, se* = √(se² + σ²). It is not the se-dependent systematic-error model of `EmpiricalCalibration::fitSystematicErrorModel`. That is acceptable, but name it "simplified empirical calibration". Per-trial fits use 13–35 NCOs, so the trial σ is noisy. With the own-trial fit, se* differs between arms, and the z² comparison then partly reflects σ_ECG vs σ_base rather than agreement.

**Power** (18 trials; 80% power, two-sided α = 0.05; MDE ≈ 2.8 × SD(d)/√18 for per-trial metrics and 2.8 × the arm-swap null SD for pooled σ):

| rung | MDE mean \|b\| | MDE b² − se² (base level) | MDE pooled σ (base σ) |
|---|---|---|---|
| demo | 0.019 | 0.039 (0.038) | 0.022 (0.104; 21%) |
| minimal-7 | 0.025 | 0.023 (0.023) | – |
| sparse | 0.035 | 0.032 (0.013) | 0.021 (0.091; 23%) |
| hdPS200 | 0.033 | 0.018 (≈ 0) | – |
| clinical | 0.028 | 0.034 (0.014) | 0.018 (0.082; 22%) |

- The observed ECG changes in σ at sparse and clinical (−0.017 and −0.016) are just below the MDE.
- demo → minimal-7 lowers base σ by 0.033, so only an ECG effect as large as adding 4 core diagnoses plus race would be reliably detected.
- The per-trial metrics cannot detect even complete removal of systematic error at sparse or clinical.

### 4. S6
- **Outcome-weighted measures.** β comes from a ridge logistic regression of the horizon event on held-out components (no treatment term), fitted in comparators of the unmatched analysed rows. The C value is chosen by CV. The fitted β is shared by all four arms of a trial/half. prog_ho_smd uses cross-fitted comparator predictions (Hansen-style). No treated outcomes are used, and matching never sees outcomes.
  - Residual caveat: the full-fit β is in-sample for comparators. This inflates \|β\| noise equally for every arm. It is not a leak.
  - The model ignores censoring, as the doc already states.
- **Energy / KS / Mahalanobis** (`s6_synth.py`):
  - Energy is the V-statistic 2E\|X−Y\| − E\|X−X'\| − E\|Y−Y'\|. It equals brute-force `cdist` (7-D, Δ 3e-11) and scipy² (1-D). The permutation test is calibrated: null p = 0.61, shifted p = 0.005.
  - KS is `scipy.ks_2samp` on unweighted matched values, which is valid because 1:1 weights are 1.
  - Mahalanobis with λ = 0.1 on unit-variance components shrinks mildly: 0.568 vs exact 0.595 on a synthetic identity-covariance example. It is stable under collinearity.
- **Halves.** Each half has its own Prep (outcome model and standardisation). "Robust" checks the halves for direction only. Of the 127 robust flags, 75 are p < 0.05 in both halves. At sparse only core Mahalanobis (x2all, x2np) is; at hdPS200 none is; at clinical 2 are (both x2all, ECG-proximal-heavy).
- **PS-overlap exclusions** are applied per cell by name, PROXY and overlap tag. Gaps:
  - composites and lab summaries are untagged (§2d);
  - hdPS200 drops only the sparse list. The hdPS-selected pool-A codes are ICD roots that covars2 re-encodes, for example as cci_* and elx_* components. The hdPS "null" on the expanded panel is therefore partly by construction.

### 5. S7
- **Removal order.** Mean across trials of the unmatched treatment \|SMD\| (`profile_one`). It uses no outcome and is computed once on the full cohort. The doc says so.
- **Random orders.** Seeded, rng 7070 + r.
- **Benchmark shuffle.** `bench_shuffle` permutes `rb[pi], rs[pi]` jointly (the correct form), with a one-sided p = P(null ≤ obs).
- **Cluster and LOO.** They use `audit_v16.CLUSTER` and exact sign-flips.
- **Counts.** The synthesis-table counts reproduce: \|Δ\| significant 15, FDR 0, benchmark-specific + cluster + LOO 5 cells. Those 5 cells are **4 distinct designs**, because loo_AF = cum_k1.
- **Minor.** The doc's \|Δ\| "p < 0.05 in both halves = 3" counts halves without requiring full-cohort significance. With that requirement the count is 1.

### 6. Global multiplicity (`global_fdr_cells.csv`)
**Scope.**
- Cells included:
  - S1 (13 cells);
  - S3 (39 unique);
  - S4 (27 subgroup cells; the withdrawn confounding tertiles are excluded);
  - S2 (10 cells, per-trial metrics averaged over 3 seeds; p = 0 cells dropped as S1 copies);
  - S6 sparse_drop50 (the other S6 cells are identical to S1);
  - S7 (39 unique after removing S1 copies and internal duplicates).
- S5 primary arms are identical to S1 and are dropped.
- Total: **129 cells**.

BH within metric (q < 0.05 and ECG better):

| metric | survivors | best cell (q) |
|---|---|---|
| \|Δlog HR\| | **0/129** | S3 demo 64 PCs / demo 4 PCs / sparse 1:3 / S4 sparse lag ≤ 90 (all 0.068) |
| \|Δ\| benchmark-shuffle p | **0/129** | S6 sparse-drop50 and S4 sparse age < 65 (0.052) |
| \|Δ\|, significant AND benchmark-specific (max of the two p) | 0/129 | 0.15 |
| z² | 78/129 | all sweeps (0.023) |
| z² benchmark-shuffle p | 0/129 | 0.49 |
| mean \|SMD\| | 109/129 | S1, S2, S3, S4, S6, S7 |
| C-statistic | 110/129 | S1, S2, S3, S4, S6, S7 |

- **S2 definition sensitivity.** The S2 addendum takes \|seed-mean log HR − RCT\|. Taking the mean over seeds of \|log HR − RCT\| weakens S2 (sparse p = 0.25: p 0.0019 → 0.013). Under either definition no \|Δ\| cell survives (min q 0.058).
- **Specific cells:**
  - AF removal: global \|Δ\| q = 0.12, shuffle q = 0.18.
  - S2 sparse p = 0.25: shuffle q = 0.20.
  - S3 demo 64 PCs: round-1 q was 0.049 over 85 cells; it is now 0.068.
- **Benchmark-shuffle p < 0.05 in 29/129 cells** (6.5 expected). The cells are highly correlated (M_eff about 22 for \|Δ\|), so this is weak aggregate evidence that part of the \|Δ\| gain is benchmark-specific in thin-PS / degraded cells. No individual cell is confirmed.
- **Effective number (Li–Ji over the correlation of per-trial d across 129 cells, 17 complete trials).**

  | metric | M_eff | median r | first-eigenvector share |
  |---|---|---|---|
  | \|Δ\| | 22 | 0.42 | 45% |
  | z² | 17 | 0.75 | 70% |
  | mean \|SMD\| | 22 | 0.53 | 53% |
  | C-statistic | 19 | 0.69 | 68% |

  The 129 cells amount to about 20 independent looks at 18 overlapping trials.
- **S5.** BH over the 90 NCO tests (3 sets × 5 rungs × 6 metrics) leaves none (min q 0.107, strict clinical fixed-SE z²). Pooled σ: BH over 5 rungs gives clinical q = 0.020 and sparse q = 0.085.
- **S6.** 236 unique balance tests (RCT metrics and cross-panel duplicates removed). All 127 robust flags also pass S6-wide BH, and 0 cells are significantly worse.

### 7. Recommended markdown edits (exact)
**S6_BALANCE.md**
1. Key finding 10 is wrong. Replace "The z² gains (sparse flagged "robust") are not specific…" with "The z² gains (p < 0.05 at demo, minimal-7, sparse and 50% dropout, but not 'robust': family q = 0.080 at sparse) are not specific…".
2. Everywhere cell lists are comma-joined ("demo, minimal-7, sparse, sparse, 50% code dropout, …"), rename the label `sparse, 50% code dropout` to `sparse-drop50`. As written, the robust column cannot be read (for example, is sparse robust on mean \|SMD\|? It is not).
3. Finding 1 / bottom line: "holds on about 300 new non-ECG-proximal covariates" → "holds on about 300 additional covariates outside the registered ECG-proximal block (the block misses MI/ACS, CHF-weighted composites and BNP; three index-setting and two admission-count variables carry index-encounter information; see AUDIT_V16_ROUND2 §2)".
4. Finding 3: add "'robust' requires only the same direction in both halves. At sparse, only core Mahalanobis is p < 0.05 in both halves."
5. Finding 4 (hdPS200): add "PS-overlap exclusions use the sparse variable list, so covars2 variables built from ICD roots already selected into the hdPS are not excluded. The null is partly by construction."

**S7_DXREMOVAL.md**
1. "BH over the 46 cells q = 0.049" → "BH over the 46 cells q = 0.049 (0.055 over the 42 distinct designs; 0.18 under the global S1–S7 BH, AUDIT_V16_ROUND2)".
2. Synthesis table: "5 (loo_AF = cum_k1, noextras, rand0_k4, rand1_k3)" → "5 cells = 4 distinct designs (loo_AF ≡ cum_k1, noextras, rand0_k4, rand1_k3)". Same for z² "2 (loo_PAD, cum_k1)".
3. Bottom line: replace "It is consistent with ECG encoding AF" with "The mechanism is that the base worsens when AF is dropped (+0.035, p = 0.10) while the ECG arm does not (+0.0007). ECG rebalances the AF flag itself by only 8.5% (p = 0.27), so this is not direct evidence that the ECG encodes AF."
4. Finding 2 "Mechanism": add "The largest single trial (transform-hf) contributes 28% of Σ\|d\|."

**S5_NCO.md**
1. Finding 6: "In the strict set, clinical z², fixed-SE z² and fraction of CIs excluding 1 survive (family q 0.036–0.039)" → append "…within the strict set only. Over all three NCO sets (90 tests) nothing survives (min q 0.107)."
2. Finding 3: add "BH over the 5 rungs: sparse σ q = 0.085; clinical σ q = 0.020."
3. Finding 7: add the omitted own-calibration result: "With own-NCO calibration, demo z² −3.79 (p = 0.018) is benchmark-specific (shuffled p = 0.002). Sparse own-calibrated z² is −1.40 (p = 0.22, shuffled p = 0.004). Own calibration changes each arm's se* through its own noisy σ (13–35 NCOs), so this is not clean agreement evidence. The halves are null."
4. Finding 8 / bottom line: replace "consistent with a small confounding reduction below this design's detection limit" with a quantified statement: "The 80% minimum detectable change in pooled σ is about 0.02 (about 22% of base σ). The per-trial noise-corrected metric cannot detect even complete removal of systematic error at sparse/clinical. S5 is uninformative about ECG effects of the size seen in balance, not evidence of no effect."
5. Design → Calibration: "empirically calibrated" → "calibrated with a simplified OHDSI model (constant μ, σ; not the se-dependent systematic-error model)".
6. Inventory / cautions: add a CCB caution for EAST-AFNET4 (diltiazem/verapamil in rate control: dental_caries, plantar_fasciitis). Add AAD cautions: blepharitis, chalazion, pterygium (eye monitoring) and benign_skin_neoplasm, seborrheic_keratosis (dermatology surveillance). Add a THZ caution: benign_skin_neoplasm, seborrheic_keratosis. Re-run the strict set.

**COVARIATES2.md**
1. Conventions, index context: "…are the only non-pre-index variables (domain `index_context`)" → "…describe the index day (domain `index_context`). `recent_hosp_30d` and `n_inpatient_stays_365` also count an index admission in progress (to be fixed: require discharge before index). `zip_*` reflect the current, extract-date address. All of these must be excluded where strictly pre-index covariates are required (S6 v1 did not)."
2. "Nothing is derived from the index ECG": keep, and append "(but see the index-encounter variables above; index-day ECGs are allowed by design)".
3. PS overlap: append "Composite scores (Charlson, Elixhauser, Gagne, CHA2DS2-VASc, CHADS2, HAS-BLED, DCSI) and lab/vital summaries (SBP mean, Hb < 10, eGFR < 30, weight/height) are not yet tagged and partly duplicate PS inputs. hdPS-selected ICD codes are not matched by name."
4. HFRS: "F00/U80 do not exist…" → "F00, U80 and X59 do not exist in ICD-10-CM and never fire. The score uses 365 d of all-setting codes (Gilbert: 2 y of hospital records), so the 5/15 cut-points are not calibrated and `hfrs_ge5` is not 'intermediate/high frailty risk'."
5. elixhauser_count: "number of 31" → "number of 30 (hypertension complicated/uncomplicated merged)".
6. Labs: add "troponin_hs = hs-TnT (LOINC 67151-1). HSCRP values (median about 11 mg/L) are standard-range CRP, not cardiovascular-risk hs-CRP. PT is available only inside concept 3020630 (source LABPROT) and is not used."
7. Medication: add "Prior use of the exposure class cannot be described, because the class is dropped. rx_arni_365 is kept in ELITE-II/ONTARGET (valsartan-containing; tag it)."

## Headline claims after round 2
1. **Survives: held-out balance at thin PS.** At demo/minimal-7, and at sparse with 50% code dropout, adding ECG improves held-out balance across measure types:
   - measures: mean \|SMD\|, C-statistic, KS, energy (−21 to −26%), Mahalanobis, subgroup \|SMD\|, BNP/echo/lab-done missingness;
   - panels: the 58-panel and about 300 non-ECG-proximal covars2 variables;
   - checks passed: ECG-specific against placebos, global BH, clustering and LOO; p < 0.05 in both within-trial halves for most measures.
2. **Survives, but small and fragile: sparse and clinical balance.** At sparse and clinical the balance gains are small (for example x2np non-proximal −0.007 and −0.003 \|SMD\|). They pass BH, clustering and LOO, but mostly fail half-B significance. At sparse and clinical the "held-out" panel partly duplicates PS content (untagged composites, index-encounter variables). **At hdPS200 the gain is null.**
3. **Does not survive: RCT agreement.** \|Δlog HR\| gains, including AF removal (S7), S2 dropout and S3 demo 64 PCs, give 0/129 cells under global BH on either the sign-flip or the benchmark-shuffle p. The z² gain is generic shrinkage (0/129 benchmark-specific after BH). Only aggregate hints remain: 29/129 shuffle p < 0.05 among correlated cells.
4. **Uninformative, not null: negative-control outcomes (S5).** Nothing survives BH across the NCO sets. The design cannot detect a change in systematic error below about 22% of σ, so it neither confirms nor refutes an unmeasured-confounding reduction.
5. **Does not survive: net outcome-weighted bias.** Signed outcome-weighted bias (\|Σβ·Δ\|, prognostic-score SMD) is not robust at thin rungs. At sparse it rests on half A.
