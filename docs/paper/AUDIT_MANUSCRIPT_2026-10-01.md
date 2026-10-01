# Manuscript audit: docs/paper/paper.md against code, reports and aggregate outputs (2026-10-01)

Independent audit. Everything was read-only except this file. Only aggregates were used (no patient rows, counts 1–10 suppressed).

- **Version audited:** paper.md at HEAD `3e56086`, which includes the parallel agent's commits `817d033` (PI comments, MIMIC-IV), `fdb1eed` (figures) and `3e56086` (UK Biobank removed). An earlier working copy (2026-09-30 Results draft) was also read. Line numbers (`l.`) refer to `3e56086`.
- **Recomputed from aggregate CSVs, without refitting any model:**
  - balance and agreement: `audits/claude-v18-embed-compare/results.csv` (full cohort) and `claude-v19-expanded-buckets/per_var_all_rungs.csv`;
  - simulation: `claude-v20-g2-ext/*.csv`;
  - MIMIC-IV: `claude-v20-mimic-replication/summary/`;
  - tiers: `docs/v19/quality_tiers.json`.
- **Scripts used for the recomputation:** session scratchpad `recompute.py`, `audit_exp.py`, `audit_dom.py`, plus `audA_*`, `audB_*` and `audC_*` from three helper agents.

## 1. Summary verdict

**The numbers are sound; the Methods need revision before submission.**

- **Headline numbers reproduce.** Every headline number in Results reproduces from the aggregate outputs, usually to the last digit:
  - balance and RCT agreement in the 32-trial primary set and in all 38;
  - the agreement-by-quality comparisons;
  - plasmode;
  - MIMIC-IV.
- **Trial and tier counts are correct:** 99/38/32, 3/12/17/6, and the area counts 12/7/5/2/2/4.
- **No genetics content.** paper.md has no polygenic-score or genetics content.

The Methods and eMethods, however, describe several things that were not done as stated, or not done for the trial set the paper uses:

1. **Sensitivity analyses run only in the 18 development trials.** Caliper 0.1, 1:3 matching, IPTW and overlap weighting, gradient-boosted PS, and 4–256 PCs exist only for the 18 v1.6 trials, never for the 32 or 38.
2. **Robustness checks and FDR not done for the 32-trial set.** Comparator-cluster, leave-one-out, split-half and FDR results do not exist in any committed file. "Independent audits" of the 32-set headline did not exist before this audit.
3. **Relative-reduction definition does not match the code.** eMethods 6 defines the relative reduction in mean |SMD| as an average of per-trial ratios with 2,000 resamples. The code uses the ratio of across-trial means with 4,000 resamples. The two estimators differ materially for some domains, for example LV systolic function: 14.6% vs 1.4%.
4. **Several design statements are wrong:**
   - lab/vital look-back is 90 days, not 365, for 7 of 9 covariates;
   - the 58-variable panel has no missingness indicators, and it contains an undisclosed prognostic score;
   - the 58-variable list was not "specified before analysis" for the 18 development trials;
   - the expanded panel has 245–336 variables per trial, not 300–345;
   - the v1.8 noise placebo is 96-dimensional;
   - statsmodels is never used.
5. **Table 1 still shows the old v1.7 three-class quality labels.** Its footnote describes them inaccurately, and the labels disagree with the four-tier scale used in the text; COMET, INSIGHT and LIFE differ.
6. **The outpatient sensitivity uses a 29-trial subset of the 38, not of the 32.** All 6 Limited trials are in it. In the 32-set subset (23 trials), the balance gain is not significant (P = .083).
7. **Analyses described without results, and a result without a description.**
   - Design-step diagnostics and enrichment (Introduction aim iv, eMethods 8) are described but have no Results.
   - The echo-subset analysis has an eFigure but no Methods or Results text.
8. **Post hoc choices presented without disclosure.**
   - The simulation's primary orientation and its ECG-only "clean" design are post hoc, and the main text does not say so. eMethods 7 contradicts itself on orientation.
   - The main balance metric (relative reduction in mean |SMD|) and the 32-trial primary set are post hoc. Only "% |SMD| < 0.1 on the 58 panel" was the prespecified primary endpoint, and only for the 15 + 5 confirmation trials.
9. **References are not numbered in order of first citation.** Refs 16–17 are cited before 11–15, and 12 before 11. Two citations in eMethods are unnumbered.

None of these changes the direction of a headline result. Items 1, 2, 3, 6 and 8 change what may be claimed.

### Claim counts by status (rows of the table in section 2)

| Status | Claims |
|---|---|
| CONFIRMED | 79 |
| MISMATCH | 29 |
| UNSUPPORTED | 12 |
| NOT CHECKED | 4 |
| **Total** | **130** |

## 2. Claims inventory and verification

Abbreviations:
- **Trial sets:** S32 = 32-trial primary set (tiers other than Limited); S38 = all 38 emulated trials.
- **PS specifications:** P1 = demographic PS; P5 = five-diagnosis PS.
- **Outputs and scripts:**
  - ec = `claude-v18-embed-compare/results.csv`;
  - ebk = `claude-v19-expanded-buckets/per_var_all_rungs.csv`;
  - g2x = `claude-v20-g2-ext/`;
  - mim = `claude-v20-mimic-replication/summary/`;
  - mpf = `scripts/v20/make_paper_figures.py`.
- **Relative reductions** below are 1 − (mean over trials of the +ECG mean |SMD|) / (mean over trials of the base mean |SMD|), the estimator the code uses.

### 2a. Trial selection, design and quality (Methods l.47–55; eMethods 1–3; Table 1)

| # | Claim (line / section) | Source checked | Status | Correct value or fix |
|---|---|---|---|---|
| 1 | 99 candidate RCTs (l.51, l.92, Fig 1) | trial_specs.py (63 unique after collapsing 3 design variants) + v17 candidates (8) + v18 AF candidates (28) | CONFIRMED | 99 under the draft-note rule. Defensible range 99–104: the af_candidates.md:71 peri-procedural group and PARTNER 2A/3 are ambiguous. State the counting rule in eFigure 1. |
| 2 | 38 "met the feasibility criteria and were emulated" (l.51, l.92) | candidates.md:115; candidates.json | MISMATCH (incomplete) | PARAGON-HF, DAPA-HF/EMPEROR-Reduced and PARTNER (and DIONYSOS) were built and analysed earlier but are not in the 38. eFigure 1 must give their exclusion reason, which is not among the eMethods 3 reasons. |
| 3 | 32 retained: 3 excellent, 12 good, 17 moderate; 6 limited excluded (l.92, eMethods 3) | quality_tiers.json `counts_tier` | CONFIRMED | — |
| 4 | Limited = ALLHAT, ASCOT-BPLA, DECLARE, ONTARGET, REWIND, VALUE (l.235) | quality_tiers.json | CONFIRMED | — |
| 5 | Areas in S32: AF 12, DM 7, HF 5, HTN 2, ACS 2, Other 4 (l.51) | tiers × v18 `category` | CONFIRMED | Methods says "acute coronary syndromes" but VALIANT is post-MI (Table: "ACS / MI"). PROVE IT (ACS population) is counted as Other. Harmonise. |
| 6 | Candidates identified "from landmark trials^4,5^" (l.51) | candidates.md, af_candidates.md | UNSUPPORTED (partly) | Most v1.7/v1.8 candidates came from investigator scouting, not from RCT-DUPLICATE. Reword. |
| 7 | Feasibility thresholds: ≥300 with ECG in the smaller arm, ≥50 pooled events (l.233) | candidates.md rules 2–3; af_candidates.md:23-24 | CONFIRMED | Events are counted among ECG-covered patients. |
| 8 | Near-duplicate = >80% shared records (l.233) | candidates.md rule 4 | CONFIRMED (with disclosure needed) | Boundary is ≥80%. The rule was added after the count-only screen (ACCOMPLISH 96%). Overlap of 50–80% was kept (ACTIVE W 69% with RE-LY; INSIGHT 63%; VALIANT 61%; LEADER 58%). The 18 development cohorts were never checked against each other. |
| 9 | Specification and published HR recorded before outcomes were extracted (l.53) | PROTOCOL_V1 tag (18 trials); V17/V18 registration commits | CONFIRMED | — |
| 10 | Stages 2–3 (15 and 5 trials): specs, benchmarks and plan committed before any results (l.233) | git: v1.7 plan 0e66e3c → registration b0c82e9 → first result; v1.8 760981a → 91cc8a3 → results | CONFIRMED | Caveat: a count-only pooled-event screen preceded v1.7 registration. The AF hypothesis came from a post hoc v1.7 pattern. |
| 11 | Results for the prespecified sets "reported separately in the supplement" (l.233) | V17_CONFIRMATION_RESULTS.md | UNSUPPORTED | No eTable is assigned to them. The 15-trial result is: P1 balance 52.4→58.3% (11/15, P=.033; cluster .078); \|Δ\| 0.250→0.208 (P=.074; benchmark shuffle .97). Add an eTable. |
| 12 | Grading: 5 flags F1–F5, comparator/outcome 0/1/2 points, total 0–9 (l.235) | quality_tiers.json `scheme` | CONFIRMED | — |
| 13 | Tier definitions (excellent 0; good 1–2 with no poor item and ≤1 flag; moderate 3, or 1–2 with a poor item or two flags; limited ≥4) (l.235) | quality_tiers.json; QUALITY_REAUDIT.md §5 | CONFIRMED | — |
| 14 | Main text: scored deviations are "time zero, run-in, baseline-therapy switching and follow-up duration" (l.55) | quality_tiers.json | MISMATCH (minor) | F1, in-hospital initiation not mirrored, is omitted. Add it. |
| 15 | Points additive per Heyard et al.; poor proxies weighted double per ref 4 (l.235) | QUALITY_REAUDIT.md §5 | CONFIRMED | Heyard is unnumbered: BMJ Med 2024;3:e000709. |
| 16 | Second reviewer re-rated independently, "blind to the first ratings and to all results" (l.235) | QUALITY_REAUDIT.md:3, 22-56 | MISMATCH | The re-rater (an AI agent) inadvertently saw the Table 1 three-class labels; its own report calls the class agreement an upper bound. Disclose that both raters were AI agents and that this exposure occurred. |
| 17 | Agreement 82%, κ 0.71 (l.235) | QUALITY_REAUDIT.md:70 | CONFIRMED | 81.6%, κ 0.71. |
| 18 | Graded scale defined after the primary analyses; quality analyses post hoc (l.55, l.235, l.269) | QUALITY_REAUDIT.md; git 46d5022 | CONFIRMED | — |
| 19 | Table 1 quality column (High (strict) / High / Lower) and its use for the tiers (l.92 "eFigure 1; Table 1") | quality_tiers.json `class_3_adjudicated`, `tier` | MISMATCH | Table 1 shows the v1.7 labels (9/9/20), not the v1.9 tiers (3/12/17/6) or the adjudicated classes (10/10/18). COMET (Lower→High), INSIGHT (High→High strict) and LIFE (Lower→High) differ. Regenerate with the v1.9 tier column (make_picot_table.py). |
| 20 | Table 1 footnote: "blinded rating made before results were examined" (l.172) | TRIAL_SELECTION_RULE.md:3, 239 | MISMATCH | The 18 development trials had already been analysed. Say "rated from design information, blind to emulation results". |
| 21 | Footnote: "High (strict) means no design flag" (l.172) | TRIAL_SELECTION_RULE.md:18-19 | MISMATCH | The rule is 0 flags and comparator and outcome ≥ moderate. For example, EMPA-REG has 0 flags but is Lower. |
| 22 | Table 1 HR, CI, measure, horizon, arms and endpoint for all 38 rows | trial_specs.PUBLISHED / HORIZON_MONTHS / OUTCOMES; rct_facts.json (8 trials) | CONFIRMED | Identical to table1_picot.md and to the script output. |
| 23 | Column header "RCT HR (95% CI)" | trial_specs `ci_level` | MISMATCH | Non-95% CIs: ELITE II 95.7%; EAST-AFNET 4 96%; VALIANT 97.5%; CAROLINA 95.47%; EMPA-REG 95.02%. PROTECT AF is a Bayesian credible interval. ROCKET AF is the ITT estimate (the published primary was per-protocol). Footnote these. |
| 24 | "Outcome (RCT primary endpoint)" vs the emulated outcome | OUTCOMES; QUALITY_REAUDIT rationales | NOT CHECKED (presentation) | The emulated outcome omits components for LODESTAR and PROVE IT (revascularisation), AMPLIFY (VTE death), FRAIL-AF (CRNM bleeding) and CABANA (disabling stroke). eTable 1 must state these. |
| 25 | eMethods 1: index dates 2011–2024 (l.47) | cohort summary.json `index_year_range` | CONFIRMED | — |
| 26 | Death follow-up to Dec 2024; cause-specific to June 2024 (l.225) | trial_specs DEATH_END / COD_END | CONFIRMED | COD_END is 2024-06-24. |
| 27 | ECG raw 10 s, 500 Hz (l.225) | bcl_embed_uv.py:10-11 | CONFIRMED | — |
| 28 | Echo from structured reports | v13_common.py:31,157-159 | MISMATCH (omission) | Echo and LVEF held-out values are masked for index dates before 2016-07-31. Disclose. |
| 29 | Age ≥18; ≥365 d prior activity; comparator washout 365 d; follow-up from the day after time zero (l.229) | build_trial_cohort.py:126-135; extract_outcomes.py:4-5 | CONFIRMED | "Prior activity" means the earliest visit is ≥365 d before index, not continuous activity. The washout window includes the index day. |

### 2b. Representations, PS and matching (l.59–65; eMethods 4–5)

| # | Claim | Source | Status | Correct value or fix |
|---|---|---|---|---|
| 30 | Most recent ECG within 365 d before or on index (l.59) | select_cohort_ecgs.py:55; PROTOCOL_V1:41 | CONFIRMED | — |
| 31 | 256-d embedding, 32 PCs within each trial (l.59, l.239) | v13_common.py:116-118 | CONFIRMED | — |
| 32 | ECG model is a "transformer encoder", trained in-house (l.239) | — | NOT CHECKED | Architecture and training details are a placeholder in the paper. |
| 33 | Permuted-ECG placebo, reassigned between patients within each cohort (l.65, l.239) | v13_common.py:170-171 | CONFIRMED | One fixed permutation per trial. |
| 34 | Noise placebo "of the same dimension" (l.239) | v18_embed_compare.py:18-19 | MISMATCH | In the main v18 analysis it is 96-dimensional (CLMBR 64 + ECG 32) and contrasted only with CLMBR+ECG. A 32-dimensional noise placebo exists only in v1.7 and in the plasmode. |
| 35 | CLMBR-T-base: 768-d → 64 PCs, pre-index coded history (l.61, l.239) | encode_comet_clmbr.py:157; CLMBR_LEAKAGE.md | CONFIRMED | Inputs are codes only, the last 4,096 tokens, strictly before the index day; state this. |
| 36 | CLMBR-T: 141M parameters, 2.57M Stanford patients (l.239) | ref 11 (EHRSHOT) | CONFIRMED | Matches the EHRSHOT paper; not documented in the repo. |
| 37 | PS = L2 logistic, C = 1, standardized, same spec for all sets (l.65, l.245) | v13_common.py:261-272 | CONFIRMED | — |
| 38 | Demographic PS = age, sex, index year (l.65, l.243) | v13_common.py:149 | CONFIRMED | — |
| 39 | Main text: "five cardiometabolic diagnoses" (l.65) | v18_clmbr.py:65 | MISMATCH (wording) | AF and HF are not cardiometabolic. Say "five cardiovascular and metabolic diagnoses". HF uses Elixhauser CHF in 6/38 trials. |
| 40 | P5 = HTN, T2D, CAD, AF, HF (l.243) | v18_clmbr.py:223-234 | CONFIRMED | — |
| 41 | hdPS base = demographics + 9–13 investigator-selected **cardiovascular** diagnoses (l.243) | v13_common.py:147-151 | MISMATCH (wording) | The count of 9–13 is correct, but the set includes diabetes, CKD, COPD/asthma, liver disease, cancer and GI bleeding. Drop "cardiovascular". |
| 42 | hdPS codes: diagnosis, medication, procedure **and laboratory-order** codes, each as any / sporadic / frequent (l.243) | eval_longtail_balance.py:20-25,77-96; build_preindex_panel.py | MISMATCH | Labs enter as "measured in window" flags with the "any" level only. Candidates also need ≥2% prevalence (unstated). |
| 43 | Ranked by \|log prevalence ratio\| on treatment only; top 200 (l.243) | eval_longtail_balance.py:98-101 | CONFIRMED | Unstated: a 0.001 offset, and per-level ranking (several levels of one code can enter). |
| 44 | Candidates from a random half of code features; other half for balance; exposure drugs excluded (l.243) | v13_common.py:126-137 | CONFIRMED | — |
| 45 | Clinical PS: median 32 covariates (28–37) (l.243) | roles.json + completed-file schema, 38 trials | CONFIRMED | — |
| 46 | 24 covariates common to all trials (list, l.243) | same | CONFIRMED | — |
| 47 | Trial-specific 3–10 medications + extra diagnoses (l.243) | same | CONFIRMED | Unstated: STEMI and PCI-within-30-d items use an [idx−30, idx] window that includes the index day. |
| 48 | Diagnoses in the prior 365 d, medications in the prior 90 d (l.243) | build_core_baseline.py:76-79,92-95 | CONFIRMED | — |
| 49 | Labs/vitals: "latest plausible value in the prior 365 days" (l.243) | trial_specs.py:55-64; PROTOCOL_V1:154-155 | MISMATCH | SBP, DBP, HR, creatinine, K, Na and Hb use 90 d; only BMI and LVEF use 365 d. The latest value is taken and set to missing if implausible; there is no search for an older plausible value. |
| 50 | Single chained-equation imputation, posterior sampling, treatment included, no outcome (l.243) | build_core_baseline.py:108-126 | CONFIRMED | scikit-learn IterativeImputer(sample_posterior=True). Imputation 1 of M is used. |
| 51 | Greedy 1:1 nearest-neighbour matching without replacement on the logit (l.65, l.245) | eval_longtail_balance.py:111-152 | CONFIRMED | — |
| 52 | Smaller group processed in descending order of the PS (l.245) | eval_longtail_balance.py:116-120 | MISMATCH (minor) | Descending order of the anchor group's own propensity. When the comparator is smaller, this is ascending P(treatment). |
| 53 | Caliper 0.2 SD of the logit (l.65, l.245) | eval_longtail_balance.py:118 | CONFIRMED | Define the SD as the pooled within-arm SD in the analysed cohort. |
| 54 | Sensitivity analyses: caliper 0.1, 1:3, IPTW and overlap weighting, gradient-boosted PS with 5-fold cross-fitting, 4–256 PCs (l.245, l.86) | docs/v16/S3_REPR.md; S8_HEADLINE.md; claude-v16-s8-headline | UNSUPPORTED for S32/S38 | These exist only in the 18 v1.6 trials (P1 and sparse bases), where they agree with the default: 1:3 53.2→61.8% (14/18); overlap 53.8→61.8% (18/18); the gain plateaus at 64 PCs; GBM weakens every gain. Rerun for S32, or label them "18 development trials". |

### 2c. Balance outcome and panels (l.69; eMethods 6)

| # | Claim | Source | Status | Correct value or fix |
|---|---|---|---|---|
| 55 | Primary outcome = balance on held-out characteristics; \|SMD\| < 0.1 balanced (l.69) | V17_CONFIRMATION_PLAN.md:25 | CONFIRMED | Make explicit that the prespecified primary endpoint (v1.7/v1.8) was % \|SMD\| < 0.1 on the 58 panel. The relative reduction in mean \|SMD\| was introduced on 2026-09-29 (post hoc). |
| 56 | 58-panel "specified before analysis" (l.69) | git 8304d5d (2026-09-26); PROTOCOL_V1 §12 | UNSUPPORTED for the 18 development trials | The list was first written for the ACC figure after v1.3–v1.6 results existed, and the echo source changed after balance results were seen. It was prespecified only for the 15 + 5 confirmation trials. |
| 57 | 58 = 35 echo + vitals + labs incl. NT-proBNP + summaries of medications, utilisation and coded record (l.69) | make_acc_figure.py:33-63 | CONFIRMED (incomplete) | Echo 35 (7/4/8/7/9); vitals and core labs 9 (incl. LVEF); other labs 10; coded record 4. The coded record includes an **external prognostic risk score** (`smd_prog_full`), which is undisclosed. |
| 58 | 58-panel excludes every variable in the demographic and diagnosis PS; at clinical, in-PS variables also removed (l.249) | ec `ex58` | MISMATCH (partial) | The named variables are removed (47 remain at clinical). Leaks: the prognostic score (built from age, sex, diagnoses and labs) is kept at every rung, including clinical. `B_mean` pool-B codes duplicate PS diagnoses (I10, I48, E11 in 19–20/38 trials). |
| 59 | SMD denominator = pooled SD of the unmatched analysed cohort (l.249) | v16_engine.py:217-225 | CONFIRMED | — |
| 60 | Held-out characteristics not imputed; labs compared among observed (l.249) | v16_engine.py:106-161 | CONFIRMED | — |
| 61 | "Each laboratory value had a separate indicator of missingness included as its own characteristic" (l.249) | make_acc_figure VARS; ebk | MISMATCH | True only for the expanded panel (37 `_missing` variables). The 58 panel has none. |
| 62 | Expanded panel: 12 sources, 150 candidates, 431 variables, 67 ECG-proximal, prevalence and pre-index rules (l.251) | LIT_COVARIATES.md:23-37; lit_covariates.json; covars2b dictionary; COVARIATES2.md:16 | CONFIRMED | Sentinel, OHDSI and the 12 sources are uncited. |
| 63 | Per-PS overlap exclusions in the expanded panel (l.251) | s6_balance.py:274-283 | MISMATCH (P5/P2 only) | A naming mismatch leaves HTN, DM, CAD and obesity variables "held out" at P5/P2 in 38/38 trials. Exclusions work at sparse, hdPS and clinical. The paper reports the expanded panel only at P1, so the reported numbers are unaffected. Fix before any P5 expanded result is reported. |
| 64 | "About 300 to 345 characteristics per trial depending on the PS" (l.251) | ebk (base arm) | MISMATCH | P1/P5/P2 314–336 (median 326.5); sparse 278–304; hdPS 245–283; clinical 255–285. Overall about 245–336. |
| 65 | "Approximately 330" per trial (l.69, l.95) | ebk | CONFIRMED (for P1 only) | S32 P1 314–336, median 329.5. The union is 344. |
| 66 | Seven display domains (l.251) | expanded_buckets.py | CONFIRMED | — |
| 67 | Relative reduction = 1 − ratio, "averaged across trials", 2,000 bootstrap resamples (l.253; CAPTIONS.md:23) | mpf:41, 65-73; scratchpad effsize.py | MISMATCH | The code computes 1 − mean_t(E)/mean_t(B), the ratio of across-trial means, with 4,000 resamples. The per-trial-average definition gives 10.6% (not 11.4%) overall and 1.4% (not 14.6%) for LV systolic function. Fix the text to the ratio-of-means definition and B = 4,000, or change the estimator. |
| 68 | Cross-fitted 5-fold treatment classifier AUC (l.253) | v16_engine.py:228-250; ec `cstat` | UNSUPPORTED (described, not reported) | It is computed with C = 0.01, on the 58-panel components only, and keeps in-PS components at clinical. It is reported nowhere. S38 base medians: P1 0.69, P5 0.67, hdPS 0.585, clinical 0.62. Report it or delete the sentence. |

### 2d. Balance results (Results l.95)

| # | Claim | Source | Status | Correct value or fix |
|---|---|---|---|---|
| 69 | P1, S32: mean \|SMD\| 0.142 → 0.126 | ec, recomputed | CONFIRMED | 0.1420 → 0.1258 |
| 70 | Relative reduction 11.4% (95% CI, 6.3–15.9) | ec; bootstrap of trials, 4,000 resamples, seed 0 | CONFIRMED | 11.41 [6.3, 15.9] (ratio-of-means estimator; see #67). |
| 71 | % \|SMD\| < 0.1: 49.8 → 55.0 | ec | CONFIRMED | 49.79 → 55.02 |
| 72 | 22 of 32 trials improved; P = .002 | ec; exact sign-flip | CONFIRMED | 22/32 (3 ties), P = .0020. Mean \|SMD\| was lower in 26/32. |
| 73 | Permuted ECG: −0.6% | ec | CONFIRMED | −0.58% |
| 74 | LV structure 24.6% (14.6–32.5) | ec | CONFIRMED | 24.6; CI [14.5–14.7, 32.3–32.7] over seeds. |
| 75 | Diastolic / LA 17.7% (8.1–26.2) | ec | CONFIRMED | 17.7; CI [7.7–8.3, 26.0–26.1] |
| 76 | LV systolic function 14.6% (0.1–27.2) | ec | MISMATCH | Point estimate confirmed. The CI lower bound is −0.5 to −0.2 in every seed tried, so the CI includes 0. Report about −0.3% to 27.5%, from a committed seeded script. |
| 77 | Vitals and core labs 13.9%; RV/pulmonary 13.0% | ec | CONFIRMED | 13.87; 12.99 |
| 78 | Valves/aorta 1.3% (−12.2 to 13.0); other labs −0.9% | ec | CONFIRMED | 1.31 [−11.8, 12.9]; −0.86 |
| 79 | P5 9.0% (4.9–13.2) | ec | CONFIRMED | 9.02 [4.8, 13.2] |
| 80 | hdPS 8.1% (2.3–12.9) | ec; deck | MISMATCH (minor) | The deck's common-variable estimator gives 8.05 [2.3, 13.4]; the full-58 estimator gives 7.9. The upper bound of 12.9 is not reproduced (13.1–13.4). |
| 81 | Clinical −1.1% (−6.2 to 4.0) | ec | CONFIRMED | −1.13 [−6.2, 4.1] |
| 82 | Expanded panel 9.8% (6.3–13.2) | ebk | CONFIRMED | 9.82 [6.3–6.4, 13.1–13.2]. The Figure caption (eFig 3) says 13.1; align. |
| 83 | S38: 12.6% (8.0–16.7) | ec | CONFIRMED | 12.61 [7.8–8.1, 16.6–16.8]. The earlier draft's +5.8 pp and 28/38 are also confirmed. |
| 84 | Relative-reduction CIs reproducible | scratchpad effsize.py (shared default RNG across calls) | MISMATCH (process) | The CIs depend on call order. The script that produced them was only in the scratchpad, and mpf.py was committed only in fdb1eed. Pin seeds and regenerate every CI from mpf.py. |

### 2e. RCT agreement (Results l.98–100; eMethods 6)

| # | Claim | Source | Status | Correct value or fix |
|---|---|---|---|---|
| 85 | P1, S32: \|Δ\| 0.251 → 0.205; 20/32 closer; P = .008 | ec | CONFIRMED | P = .0084 |
| 86 | r 0.51 → 0.59 | ec | CONFIRMED | — |
| 87 | Std-difference agreement 20 → 27 of 32 | ec | CONFIRMED | Estimate agreement 15 → 18 (earlier draft) is also confirmed. |
| 88 | Benchmark-permutation P = .27 (S32); .22 (S38, earlier draft) | deck benchShuffle (within-set, 20,000 draws); v18 summary.csv (S38 .220) | CONFIRMED | — |
| 89 | P5 0.226 → 0.196 (P = .049); hdPS 0.181 → 0.167 (P = .20); clinical 0.158 → 0.155 (P = .42) | ec | CONFIRMED | — |
| 90 | Clinical PS alone: r 0.56, estimate agreement 69%, std-diff 84% (earlier draft; now in eTable 6) | ec | CONFIRMED | — |
| 91 | S38: 0.258 → 0.207, 25/38, P = .002 | ec | CONFIRMED | — |
| 92 | Quality tiers: n = 15 vs 17; clinical PS r 0.83 vs 0.39; std-diff 100% vs 71% | ec + tiers | CONFIRMED | Estimate agreement 80% vs 59% (earlier draft) also confirmed. |
| 93 | Excellent/good: std-diff 67% → 93%, 11/15 closer, P = .009; moderate 9/17, P = .13 | ec | CONFIRMED | The P is the \|Δ\| sign-flip, not a test of std-diff agreement; say "(\|Δ\| closer in 11 of 15; P = .009)". |
| 94 | Agreement definitions (estimate: \|θE−θR\| ≤ 1.96 sR; std-diff: \|z\| < 1.96; Pearson r) | ec / deck agree() | CONFIRMED | — |
| 95 | Benchmark permutation: "20,000 times" (l.255) | deck; mpf:95 | CONFIRMED | Within-set reassignment. |
| 96 | Robustness to comparator clustering, leave-one-out, split halves; FDR within families (l.86) | v18 summary.csv (S38/S33 only) | UNSUPPORTED for S32 | Not computed for S32 in any committed file. Helper recomputation for S32, P1: %<0.1 cluster P .033, LOO max .005, halves .0005/.0001; \|Δ\| cluster .026, **half A .30**, q .084. Commit these, or restrict the sentence to S38. |
| 97 | "Headline estimates were re-derived in independent audits" (l.86) | AUDIT_V16*, AUDIT_ROUND4 (pre-date the 32-set, 2026-09-29) | UNSUPPORTED (before this audit) | This document is the first independent re-derivation of the S32 numbers. Cite it, or delete the sentence. |
| 98 | Cox PH with robust variance clustered on pairs (l.73) | v13_common.py:340-360 | CONFIRMED | lifelines, Efron ties; NaN if fewer than 5 events. |

### 2f. Simulation (l.77, l.103; eMethods 7)

| # | Claim | Source | Status | Correct value or fix |
|---|---|---|---|---|
| 99 | 107 trial × confounder combinations, 31 trials; ≥300 per arm; one calibration-failure cell excluded (l.103, l.259) | G2_SIMULATION.md; excluded_cells.csv | CONFIRMED | ROCKET AF × LVEF excluded. |
| 100 | ECG-only PS removed 18.0% overall; LVEF 27.9, NT-proBNP 22.2, BMI 17.5, eGFR 9.7 | g2x/pooled_trtC_cliniorient.csv | CONFIRMED | This uses the post hoc clean (trtC) design in the post hoc clinical orientation; see #105. |
| 101 | Oracle 93.1%; permuted ECG −0.2% | same | CONFIRMED | Monte Carlo SE ≤ 0.6 (earlier draft) also confirmed. |
| 102 | Added share: demographic 14.9, hdPS 8.6, clinical 11.7; LVEF 22.4 / 13.0 / 13.7 | g2x/ecg_added_value_cliniorient.csv | CONFIRMED | null-corrected |
| 103 | Tracks about 100 × R²; median R² LVEF 0.26, BMI 0.22, NT-proBNP 0.20, eGFR 0.04 | G2_SIMULATION.md | CONFIRMED | The median R² is over 38 trials, and the slope refers to partial R² (1.16 in the adverse orientation). Say so. |
| 104 | Coverage 68%–83% with the ECG; oracle 95%; no dependence on the true HR (14.2% at 0.6/0.8/1.0) | g2x/performance_cliniorient.csv; pooled_hr*.csv | CONFIRMED | The 14.2% comes from the as-designed main design. It differs from the 14.9% (clinical orientation, null-corrected) quoted in the same paragraph; label the design. |
| 105 | Orientation and design status (main text l.77, l.103) | G2_EXTENSION.md §7.2; G2_SIMULATION.md deviations | MISMATCH (undisclosed post hoc) | The clinical orientation and the trtC design were chosen after the as-designed results (logged deviations). The main text does not say so. Add "post hoc" and give the as-designed values (ECG added 10.6% null-corrected; LVEF 9.1%, eGFR −4.8%) in the supplement. |
| 106 | eMethods 7 orientation statements (l.259 vs l.261) | — | MISMATCH (internal contradiction) | l.259 says the confounders were oriented "higher = more treatment and hazard" and calls the adverse orientation a post hoc sensitivity variant. l.261 says the main analyses used the clinical (adverse) orientation. Rewrite as a single statement. |
| 107 | Simulation design details (Weibull PH, ridge-fitted β, OR/HR grid, true HR 0.80, 50 replicates at 80% subsampling, administrative censoring, event rate 21.0% vs 20.4%, non-collapsibility-correct truth, MCSE 1,000 resamples) | G2_SIMULATION.md "Design"; G2_EXTENSION.md | CONFIRMED | — |

### 2g. Design steps, enrichment, sensitivity, CLMBR (l.77, l.109; eMethods 8–9)

| # | Claim | Source | Status | Correct value or fix |
|---|---|---|---|---|
| 108 | Design-step diagnostics over five steps (l.77, l.265) | G1_DESIGN_STEPS.md | UNSUPPORTED in Results | The analysis exists (S38): phenotype mean \|SMD\| 0.206 → 0.144 → 0.088 → 0.079 → 0.075, and residual imbalance does not predict \|Δ\| (ρ ≈ 0). Step 3 is the "sparse" PS, which the Methods no longer define. There is no Results text. |
| 109 | Enrichment (Intro aim iv l.39; l.77; l.265) | G3_ENRICHMENT.md | UNSUPPORTED in Results | Exists (S38): top-quartile sample-size reduction ECG 34%, clinical 44%, CLMBR 44%, combined 45%. The "clinical" score is demographics + sparse diagnoses, not the clinical PS. There is no Results text; Results l.109 dropped the placeholder entirely. |
| 110 | Outpatient: 29 trials, +2.3 pp, 17/29, P = .035, vs +5.7 (l.109) | SENS_OUTPATIENT.md T3; setting.csv | MISMATCH (denominator) | The numbers are right, but OUT-29 is a subset of S38 and includes all 6 Limited trials. Within S32 (23 trials): +2.2 pp, 12/23, **P = .083**, vs +4.9 for all initiators. Write "29 of the 38 emulated trials", or report the 23-trial values. Also report SE ×1.37 and that the \|Δ\| gain vanishes (P = .24). |
| 111 | Outpatient classification a priori (l.269) | SENS_OUTPATIENT_PLAN.md; git ac0a347 → 418af03 | CONFIRMED | — |
| 112 | "All sensitivity estimands were computed in the same matched samples" (l.269) | sens_adherence.py; sens_outpatient.py | MISMATCH (minor) | True for the adherence estimands, but the outpatient analysis refits and rematches. Note the exception. |
| 113 | Per-protocol IPCW (grace 180/365/730, stabilized), switch-only, landmark 90 d, run-in 90 d; 4 procedure trials; run-in not estimable when ≤50 retained (l.269) | SENS_ADHERENCE.md; cells.csv | CONFIRMED | Unstated: weights truncated at the 99th percentile; the landmark analysis was a deviation added after the plan. Results exist (S38; S32 recomputed, e.g. switch-only 0.253 → 0.199, P = .002) but are "to be added". |
| 114 | 5 prespecified AF trials: 0.254 → 0.199, 3/5, P = .19 (l.109) | AF_CONFIRMATION_RESULTS.md | CONFIRMED (incomplete) | State that the prespecified confirmation failed: co-primary benchmark shuffle P = .28; with P5 the ECG worsened agreement (0.135 → 0.212). Cite eMethods 3. |
| 115 | CLMBR-T comparisons "to be added" (l.61, l.109) | EMBEDDING_COMPARISON.md; ec | NOT CHECKED (no text to check) | Results exist. S32, P1: CLMBR 60.7% balanced (26/32) and CLMBR+ECG 62.6%; ECG adds +1.9 pp over CLMBR (P = .025). \|Δ\| with CLMBR 0.171. No benchmark-shuffle pass. |

### 2h. External validation, software, references

| # | Claim | Source | Status | Correct value or fix |
|---|---|---|---|---|
| 116 | MIMIC balance: 10.3% (6.4–14.5), 7/7, P = .008; 41.2 → 51.6%; permuted −2.5%; excluding index-day ECGs 14.5% (9.7–19.7); hdPS 7.5% (−0.5 to 15.9); clinical 1.2% (−9.6 to 10.8); 26 held-out characteristics (8/13/1/4); 16–53% index-day ECGs (l.81, l.106, l.280) | mim/summary.json, tables.md; MIMIC_REPLICATION.md | CONFIRMED | Call the MIMIC clinical PS "clinical-lite (no LVEF)" in the main text. |
| 117 | MIMIC agreement and PEPTIC: 0.337 → 0.315, 4/7, P = .27; "ECG outperformed placebo for 3 of 4 specifications"; PEPTIC 1.53 (1.36–1.71) → 1.39 (1.24–1.56), placebo 1.61; 441–1,841 matched pairs | mim/tables.md | CONFIRMED | Wording problems: (a) "4 specifications" includes the sparse PS, which the paper never defines (the Methods list 3). (b) "Agreement … improved directionally for every PS" holds only for mean \|Δ\|; r and std-diff agreement fell with the demographic PS (0.71 → 0.67; 5/7 → 4/7). (c) The pair range is for the demographic PS alone. |
| 118 | "Seven cardiovascular trials met these criteria"; plan specified before results (l.81) | MIMIC_FEASIBILITY.md:43-58; git 25c58b2 16:43 vs first output 16:45 | MISMATCH (nuance) | RE-LY and three proxy trials also passed the count rules but were rated "P" and not analysed; say "7 were feasible without substitution". The plan did precede results, but v1.5 HRs for 5 of the 7 already existed. |

Remaining items, scored separately:

| # | Claim | Source | Status | Correct value or fix |
|---|---|---|---|---|
| S1 | Python 3.11.16; pandas 2.3.3; NumPy 2.4.6; DuckDB 1.5.5; scikit-learn 1.9.1; lifelines 0.30.3; SciPy 1.17.1; matplotlib 3.11.2 (l.273) | software/tte-analysis conda-meta, dist-info | CONFIRMED | — |
| S2 | statsmodels 0.15.0 (l.273) | repo-wide grep | UNSUPPORTED | Installed but never imported. Remove it. |
| S3 | PyTorch 2.5.0 for ECG; PyTorch 2.13.0 + FEMR 0.2.3 for CLMBR-T (l.273) | bcl-smoke-runtime env; mosaic-env | CONFIRMED | mosaic-env runs Python 3.11.15 with scikit-learn 1.9.0; state this if PCs were computed there. |
| S4 | "Python 3.11" (l.86) | as S1 | CONFIRMED | — |
| R1 | References numbered in order of first citation | paper.md citation scan | MISMATCH | First-citation order is 1–10, 16, 17, 12, 11, 13, 14, 15. Renumber: MIMIC-IV → 11, MIMIC-IV-ECG → 12, TARGET → 13, EHRSHOT → 14, hdPS → 15, Austin → 16, plasmode → 17, or move the MIMIC citation to the External validation subsection. |
| R2 | Unnumbered citations (Heyard BMJ Med 2024; Morris Stat Med 2019; Sentinel; OHDSI; DISCO in notes) | — | UNSUPPORTED (uncited) | Heyard R et al. BMJ Med 2024;3:e000709. Morris TP, White IR, Crowther MJ. Stat Med 2019;38:2074–2102. |
| R3 | Ref 10 BCL page range; ref 12 TARGET details | PubMed | MISMATCH (incomplete) | BCL: JAMIA 2024;31(4):855–865. TARGET: JAMA 2025;334(12):1084–1093, doi:10.1001/jama.2025.13350. |
| R4 | Refs 11, 13–17 | PubMed / PhysioNet / arXiv | CONFIRMED | Drop the [verify] tags on 15–17. Only 17 references against the 50–75 target; the 38 trial publications are uncited. |
| R5 | Ref 9 author list | — | NOT CHECKED | — |
| X1 | Polygenic score / genetics content in paper.md | grep for polygenic, PGS, genet*, genotype, German, SNP, ancestry | CONFIRMED absent | No genetics content. UK Biobank is now removed entirely (3e56086). PGS content remains only in non-manuscript docs (docs/v20/UKB_ANALYSIS*.md, docs/v18/LIT_GERMAN_2025_PGS_TTE.md); keep them out of the supplement. |
| X2 | Display items ≤5 (Table 1 + Figures 1–4) | paper.md l.113-181 | CONFIRMED | 5 items. A 38-row Table 1 may need condensing. |
| X3 | eFigure 6 echo-subset analysis | ECHO_SUBSET.md; paper Methods/Results | UNSUPPORTED (result not described) | It appears only in the eFigure list. The Methods and Results never describe it. S32: the ECG closes 60% of the LVEF imbalance (placebo 3%); placebo-corrected F 0.27 (−0.31 to 0.72). Plan e098888 preceded the results. Add a sentence, or drop the eFigure. |

The status counts in section 1 cover all 130 rows of section 2: rows 1–118 plus S1–S4, R1–R5 and X1–X3. Rows marked "CONFIRMED (with caveat)" are counted as CONFIRMED.

## 3. Prioritized fixes

**P1: must fix (they change what is claimed)**

1. **Sensitivity analyses (#54).** Either run caliper 0.1, 1:3, IPTW, overlap weighting, GBM PS and 4–256 PCs for S32 (and S38), or rewrite eMethods 5 and the Statistical analysis to say "in the 18 development trials" and cite S3/S8.
2. **Robustness claims (#96, #97).** Commit S32 comparator-cluster, leave-one-out, split-half and BH-FDR results (note that half A fails for \|Δ\|, P = .30), or restrict the sentence to S38. Replace "re-derived in independent audits" with a reference to this audit, or delete it.
3. **Relative-reduction definition (#67, #84, #76).** Change eMethods 6 and the Figure 2 caption to "1 − ratio of the across-trial means of mean \|SMD\|; 4,000 bootstrap resamples". Regenerate all CIs from the committed mpf.py with fixed seeds. The LV systolic-function CI then includes 0 (about −0.3% to 27.5%); revise the text accordingly.
4. **Outpatient sensitivity denominator (#110).** State "29 of 38 emulated trials", or report the S32 subset (23 trials: +2.2 pp, P = .083).
5. **Post hoc disclosure.** Label as post hoc in the main text:
   - the 32-trial primary set;
   - the relative-reduction metric as headline (#55);
   - the 58-panel's status in the development trials (#56);
   - the simulation orientation and ECG-only design (#105).
   Make eMethods 7 consistent (#106).
6. **Table 1 (#19–21, #23).** Regenerate with the v1.9 tiers, correct the footnote definitions and "before results" wording, and footnote the non-95% and non-HR benchmarks.

**P2: factual errors in Methods**

7. Lab/vital look-back is 90 d for SBP, DBP, HR, creatinine, K, Na and Hb; 365 d only for BMI and LVEF. Describe it as the latest value, set to missing if implausible (#49).
8. 58 panel: remove the "missingness indicator" sentence (it applies to the expanded panel only) and disclose the prognostic-score component and its PS overlap (#57, #58, #61).
9. Expanded panel size: "about 245–336 per trial (about 330 with the demographic PS)" (#64).
10. Noise placebo dimension (96 in v1.8) (#34); hdPS details (lab flags any-level only, ≥2% prevalence, 0.001 offset, non-CV base diagnoses) (#41–43); matching order and caliper SD definition (#52–53); echo masking before 2016-07-31 (#28).
11. Treatment-classifier AUC: report it with its actual spec (C = 0.01, 58-panel components) or delete it (#68).
12. Remove statsmodels from eMethods 10 (S2).
13. Renumber references in first-citation order and number Heyard and Morris (R1–R3).

**P3: missing results and wording**

14. Add Results, or drop the Methods/Introduction text, for enrichment (aim iv) and design-step diagnostics (#108, #109). Correct the enrichment "clinical score" description.
15. Fill the adherence-estimand and CLMBR-T placeholders; results exist (#113, #115). Add the echo-subset sentence or drop eFigure 6 (X3).
16. AF confirmation: state that it failed (benchmark shuffle P = .28; P5 worse) (#114). Add the 15-trial prespecified results to the supplement as promised (#11).
17. MIMIC wording: "clinical-lite", define or drop "sparse" (the 4th specification), restrict "improved" to mean \|Δ\|, and say "7 feasible without substitution" (#117–118).
18. Minor: re-rater disclosure (#16), F1 in the main-text list (#14), "cardiometabolic" (#39), "landmark trials" sourcing (#6), the 38 vs previously analysed trials in eFigure 1 (#2), and the P = .009 attribution (#93).

## 4. Analyses described but not found (for the trial set the paper uses)

| Described in | Analysis | What exists |
|---|---|---|
| eMethods 5; Statistical analysis | Caliper 0.1; 1:3 matching; IPTW; overlap weighting; gradient-boosted PS with 5-fold cross-fitting; 4–256 ECG PCs | 18 v1.6 trials only (docs/v16/S3_REPR.md, S8_HEADLINE.md). None for S32 or S38. |
| Statistical analysis | Comparator-cluster, leave-one-out and split-half robustness; BH-FDR within families, for the primary S32 analyses | S38/S33 only (v18 summary.csv); S32 values are not committed. |
| Statistical analysis | "Headline estimates were re-derived in independent audits" | No audit of S32 before this document. |
| eMethods 6 | Cross-fitted treatment-classifier AUC | Computed (`cstat`), never reported. |
| eMethods 6 | Missingness indicators as 58-panel characteristics | Not in the 58 panel (expanded panel only). |
| eMethods 8; Introduction aim (iv) | Design-step diagnostics; AI-ECG enrichment | S38 results in docs/v19/G1, G3; absent from Results. |
| eMethods 3 | Separate supplement results for the 15-trial and 5-AF prespecified sets | Docs exist (V17_CONFIRMATION_RESULTS.md, AF_CONFIRMATION_RESULTS.md); no eTable is planned. |
| Results l.109 | Per-protocol, switch-only, landmark and run-in; alternative matching/weighting; CLMBR-T ("eTables 9–11, to be added") | Adherence and CLMBR results exist (S38; S32 computable). Alternative matching/weighting exists for 18 trials only. |
| eMethods 4 | ECG model architecture and training data | Placeholder. |

**Results present but not described in the Methods or Results:** the echo-subset analysis (eFigure 6). The sparse PS also appears in MIMIC "4 specifications", design step 3 and the enrichment "clinical" score, but the Methods no longer define it.

## 5. Reproduction notes

- **Primary-set recomputation.** Every S32/S38 balance and agreement number was recomputed from `claude-v18-embed-compare/results.csv` (`half == "full"`), with `ex58` exclusions applied per arm, and the tiers from `quality_tiers.json`. P values use `v17_confirm.signflip_1s`.
- **Deck estimator.** The deck and mpf.py drop, per trial, any variable missing in any displayed arm. This explains the hdPS 8.05% vs the full-58 7.9%; no other headline number is affected.
- **Simulation.** Simulation values were read directly from the committed v2.0 pooled CSVs; they match `docs/v20/G2_EXTENSION.md` exactly.
- **MIMIC-IV.** MIMIC-IV values match `summary/tables.md` exactly.
- **Side effect.** One helper run created an untracked bytecode file, `scripts/v19/__pycache__/sens_outpatient.cpython-311.pyc` (gitignored). It was left in place.
