# TRACE-ECG version 1: claim-by-claim recheck of manuscript 2 (paper2.md) and its figure legends

Audit of `docs/paper/paper2.md` and `docs/paper/figures_paper2/` (legends in `index.html` and paper2.md l.191–203; all PNGs viewed) at tag `trace-v1` (5c98301), branch `main`. Done 2026-10-08 on the HIPAA cluster session. Nothing was committed, and no version 1 file was edited; every fix below is a text proposal.

## Summary

1. **Independent recompute.** I reimplemented the summary layer from the cell-level outputs (`core/restricted_cells.parquet`, `restricted_flagscv_cells.parquet`), without importing `paper2_grid.py` or `sens_primary32.py`. That covers item pairing, relative reduction with trial bootstrap, exact sign-flip, cluster P, benchmark permutation, Benjamini–Hochberg (BH) families, domains, labels, retention/ESS and PS-Flags fairness. All 674 contrast rows, 4,718 domain rows, the label, Spearman and flags-CV tables and every BH q value reproduce the v21 CSVs to ≤ 1e-13.
2. **Numbers are right.** Every number in Results l.77–127 matches its source at the printed precision. That includes the plasmode and MIMIC-IV numbers, which were recomputed from replicate- and trial-level files. No rounding errors were found. The problems are in wording, scope and methods statements.
3. **Load-bearing mismatch (l.35).** "Study-drug codes appeared in the pre-index history of at most 5.9% of patients" was measured in the 33 v1.8 trials only, for new-user designs. In switch designs (AF-CHF, AFFIRM, EAST-AFNET 4, PARADIGM-HF), COMET, FRAIL-AF and PROTECT AF, prior study-drug codes are present in 71–100% of patients by design.
4. **Unsupported framing (l.111, Figure 5 gallery legend).** "The agreement pattern of our previous report reproduced with PS-CVD5" does not hold. Paper 1 reported configuration results only for PS-Demo, and there the benchmark-permutation P was never < .05 (.26–.85, eTable 7). The PS-CVD5 signals here (1:3 matching benchmark P = .037; GBM .005) are new, nominal and do not survive FDR.
5. **Scope overstatement (l.115–117, l.216).** The statements "none of the label differences survived FDR" and "no other domain label … q < .05" hold only in the primary configuration.
   - With 1:3 matching and overlap weighting, the physiologic-label differences reach q < .05 within their label family for the ECG, CLMBR-T and both (e.g. ECG q = .004 and .007).
   - Most of them (ECG and both) still do when BH runs over all six configurations.
   - Under overlap weighting, rhythm/conduction (heart-rate proxy) reaches q = .009 for the ECG.
6. **Omitted signal (l.97–99, l.212).** The flags head-to-head omits a nominal 1:3-matching result favouring PS-Demo + CLMBR-T: 5.1% (95% CI, 1.0–9.4), P = .030, q = .093. "No specification … and no evidence that it does better" should be qualified.
7. **Methods vs code.**
   - IPTW gives zero weight to patients outside the 1st–99th PS percentiles; this is undisclosed.
   - "Every specification and arm" in all six configurations is not literal: the CLMBR-T 32-PC arm ran in the main configuration only.
   - PS-Clinical is described as nested on the hdPS ("further included"), but it does not contain the 200 empirical features.
   - The HF flag in PS-CVD5 is Elixhauser CHF in 6 trials.
   - Index dates reach 2025 (COMET).
   - The MIMIC "2,000 resamples, as in the previous report" contradicts paper 1 and paper2's own window-fix CIs, which use 4,000.
   - The plasmode design is called paper 1's "primary design"; paper 1 calls it post hoc.
8. **Minor wording.** "Restriction … did not explain the gain" and "not correlated (ρ = 0.21)" are null claims without a CI. "The two together improved it most" (Discussion) is not significant in the main configuration (+1.3%, q = .49). The ECG "echo-domain" framing omits CLMBR-T's equal LV-structure gain (14.7% vs 14.9%). "Followed how well each predicted the confounder" fails for BMI.
9. **Denominators.** 32 vs 38 trials and 54 vs 58 items are used consistently, and the 31-trial PS-Flags denominators are stated correctly. The RCT-agreement wording (attenuation toward the null, benchmark-permutation P .70–.94) is correct and is backed by a direct check: CLMBR-T shrinks mean |log HR| from 0.302 to 0.191 (26 of 32 trials move toward 0).
10. **Counts and the earlier audit.** 160 rows below: **137 MATCH, 9 MISMATCH, 1 UNSUPPORTED, 12 OVERSTATED, 1 UNTRACEABLE**. I disagree with the step-H audit (`docs/v21/AUDIT_PAPER2_MANUSCRIPT.md`) on 13 of its MATCH verdicts. In 3 further cases its fix or softening was wrong or incomplete; one of these ("as in the previous report", l.63) introduced an error (see the comparison section).

**Method note.** Plasmode/MIMIC (l.25, 59, 63, 123, 127, 218, 264, eFigures 1–2) and Table 1/Methods facts (l.25–51, 77, 131–191) were rechecked by two forked sub-agents using their own scripts (`recheck_*.py`); I reviewed their findings. One fork's grep for "141 million" printed four lines of the earlier audit before its pass was finished; it did not open the file, and its verdicts rest on its own scripts.

**Abbreviations used in the table.**
- `CR` = `claude-v1-audit/claims/core_recomputed.csv`; `DR` = `domains_recomputed.csv`; `RR` = `retention_recomputed.csv`; `FR` = `flagscv_recomputed.csv`; `LP`/`LD`/`LS` = `labels_{phys,dom,spearman}_recomputed.csv`; `MC` = `misc_checks.txt`; `PM` = `plasmode_recheck.csv`; `MM` = `mimic_recheck.csv`; `T1` = `table1_recheck.csv`; `MF` = `methods_facts.log`. All are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/claims/`.
- v21 sources: `sens`/`dom`/`ret`/`fcv`/`lph`/`ldo`/`lsp` = `claude-v21-paper2/core/{sensitivity,domains,retention_sens,flagscv,labels_physiologic,labels_domain,labels_spearman}.csv`.
- Code: `PG` = `scripts/v21/paper2_grid.py`; `SP` = `scripts/v20/sens_primary32.py`; `v13c` = `scripts/v13_common.py`.
- All values are S32, main configuration, 54 items, unless stated.

## Claims table

| # | l. | Claim (excerpt) | Source (output; code) | Recomputed | Verdict | Suggested fix |
|---|---|---|---|---|---|---|
| 1 | 1, 19, 208 | 32 cardiovascular trials analysed | quality_tiers.json; SP `S32` | 32 non-Limited of 38 | MATCH | — |
| 2 | 25 | YNHHS, OMOP, linked echo/ECG/vital statistics | paper.md (reused) | not data-checkable | MATCH | — |
| 3 | 25 | Index dates 2011 through 2024 | trial objects (T1/MF) | 2011–2025: COMET has 1–10 index dates in 2025 | MISMATCH (minor) | "2011 through 2025", or restrict COMET; same in Figure 1 ("2011–2024") and paper.md |
| 4 | 25 | MIMIC-IV v3.1, BIDMC, deidentified EHR + ECG | v15 staging path; eMethods 11 | 3.1 | MATCH | Also cite ref 21 (MIMIC-IV-ECG), which is never cited |
| 5 | 29 | 99 candidates | supplement eMethods 3 text only | no screening-log tally in the repository | UNTRACEABLE | Add a screening-log tally (eFigure 1 counts by reason) |
| 6 | 29 | 38 emulated, 32 retained; 3 excellent / 12 good / 17 moderate | quality_tiers.json `counts_tier` | 3/12/17 (+6 limited) | MATCH | — |
| 7 | 29 | Grading from design information alone; points-based RCT-DUPLICATE adaptation | quality_tiers.json `scheme` | consistent | MATCH | — |
| 8 | 33 | Most recent ECG within 365 d before or on index | select_cohort_ecgs.py; bcl summary.json | window 365 d, lag 0–365, all 38 | MATCH | — |
| 9 | 33 | 256-d embedding → 32 PCs within each trial | v13c `Trial` (`pcs(ecg_raw,64)[:, :32]`) | 256 → 32, per trial | MATCH | — |
| 10 | 35 | CLMBR-T-base, 141M parameters, 2.57M patients, frozen | model README; safetensors header | 141,650,432 parameters; 2.57M | MATCH | — |
| 11 | 35 | Input domains; index day excluded; last 4,096 tokens | CLMBR_LEAKAGE.md; encoder summary.json | max_tokens 4096 in all 38 | MATCH | — |
| 12 | 35 | Truncation 0.3%–5.7% per trial | clmbr-codeonly summary.json | 0.28–5.71% (roster patients) | MATCH | Optionally "of roster patients" |
| 13 | 35 | Study-drug codes in pre-index history of at most 5.9% of patients | claude-v18-clmbr/leakage.csv (33 trials); claude-v18-audit4 (38) | 5.9% (ARISTOTLE) only across the 33 v1.8 trials, new-user designs. Switch designs (AF-CHF, AFFIRM, EAST-AFNET 4, PARADIGM-HF) ~100%, COMET 71%, FRAIL-AF and PROTECT AF ~100% (warfarin by design) | MISMATCH | "In new-user designs, study-drug codes appeared before index in at most 5.9% of patients; in designs requiring prior use (switch designs, FRAIL-AF, PROTECT AF) the prior drug was present by design." Cite the 38-trial check |
| 14 | 35, 191 | 768-d → 64 PCs within trial; first 32 as sensitivity | v13c `clm_pc = pcs(C,64)`; PG `c32` | 768 → 64; CLMBR32 = first 32 | MATCH | — |
| 15 | 39 | L2 logistic on standardised covariates, C = 1 for every specification | v13c `ps_logit`; SP `CONFIGS` | StandardScaler + LogisticRegression(C=1) | MATCH | — |
| 16 | 39 | PS-Demo = age, sex, index year | roles.json; cells p_ps = 3 | yes | MATCH | — |
| 17 | 39 | PS-CVD5 = PS-Demo + HTN, T2D, CAD, AF, HF | v18_clmbr `P5DX` | yes. HF = hf_any_365 in 32 trials, Elixhauser CHF in 6 (incl. LIFE, INSIGHT in S32); 365-d windows | MATCH (detail undisclosed) | State windows and HF definition in eMethods 5 |
| 18 | 39 | PS-Flags: ICD-10-CM 3-char, before index day, ≥1%, 426–622 flags (median 529 of 38; same range in 32), no dates/counts | core/log.json; PG `flags_matrix` | S38 426/529/622; S32 426–622 (median 532.5) | MATCH | — |
| 19 | 39 | Flags window = CLMBR-T window | PS_FLAGS.md; CLMBR_LEAKAGE.md | both end index−1; full history | MATCH | — |
| 20 | 39 | hdPS = 200 empirical code features + demographics + 9–13 investigator diagnoses | trial objects; cells p_ps | dx 9–13; 200 empirical (incl. lab-count features; PCI/CABG flags among "diagnoses") | MATCH (wording) | "200 empirically selected code and test-count features" |
| 21 | 39, 191 | PS-Clinical "further included" vitals, labs, LVEF, meds, use (implies hdPS + extras; Figure 1 draws a nested ladder) | trial objects `X_core` | X_core = demo + investigator dx + 9 vitals/core labs + meds + utilisation; no 200 hdPS features | MISMATCH (ambiguous) | "PS-Clinical comprised demographics, investigator-selected diagnoses, vitals, labs, LVEF, medications and healthcare use (without the empirical hdPS features)"; drop the chain arrows in Figure 1 |
| 22 | 41 | Placebos = within-trial permutation; dimension preserved | v13c `shuffle_perm`; cells p_ps | yes, same permutation for ECG and CLMBR-T | MATCH | — |
| 23 | 41 | 1:1 NN without replacement on logit, caliper 0.2 SD | eval_longtail_balance `ps_greedy` | greedy, anchored on smaller arm, descending PS; width = 0.2 × pooled SD | MATCH | Optionally "greedy" |
| 24 | 41 | "Every specification and arm" in 5 further configurations; IPTW; GBM 5-fold cross-fitted | PG `task`; v13c `weights`, `ps_logit` | CLMBR32 arm main only. IPTW = stabilised weights, **zero weight outside the 1st–99th PS percentiles** (~2% excluded). GBM = HistGB cross-fitted + 1:1 caliper 0.2 | MISMATCH (incomplete) | "…IPTW (stabilised weights; patients outside the 1st–99th PS percentiles excluded)…"; "every specification and arm except the 32-component CLMBR-T arm" |
| 25 | 43 | Comparison does not isolate timing; no diagnosis-date PS | PG rungs | no timing rung exists | MATCH | — |
| 26 | 47 | Labels fixed before stratified results; two blind runs; κ = 1.00; intersection/union; 11 physiologic of 38 | labels_A/B.json; TRIAL_LABELS.json; git times | κ 1.00 (11/38 each); labels 17:13, label CSVs 18:27 | MATCH | — |
| 27 | 51 | 54 items = 9 + 10 + 35 echo; 58 minus 4 coded summaries; PS-Clinical inputs removed | make_acc_figure `VARS`; SP `per_trial` (ex58) | 9 + 10 + (7 + 4 + 8 + 7 + 9) = 54; clinical masks meds, util and 9 vitals/core labs | MATCH | — |
| 28 | 55 | Cox, robust variance clustered on pairs | v13c `cox`; v16 `run_cell` | cluster = anchor for matching; robust (unclustered) under weighting | MATCH | — |
| 29 | 55 | Estimate agreement = emulated HR within RCT 95% CI; std-diff agreement within 1.96 × combined SE; Pearson r | SP `per_trial`, `agree_metrics` | ea = \|Δ\| ≤ 1.96·rs (symmetric reconstruction from the published CI level); cons = \|z\| < 1.96 | MATCH (note) | Note: in `cons_p`/`ea`, a NaN log HR counts as disagreement (0), not missing. No headline row affected, but worth a code fix |
| 30 | 55 | Benchmark permutation, 20,000 reassignments | SP `bshuf`; PG `bshuf2` | 20,000; one-sided (two-sided analogue for head-to-heads) | MATCH | State sidedness |
| 31 | 59 | "We used its primary design, in which a withheld variable alone drove treatment" | paper.md l.85; eMethods 7; paper2_plasmode `DESIGN` | paper 1 calls this design "post hoc", not primary | MISMATCH | "We used the post hoc design of the previous report in which …; both this design and the clinical orientation were chosen post hoc" |
| 32 | 59 | ref ^19^ attached to "our previous report" | reference list | ref 19 = Franklin 2014 plasmode methods | MISMATCH (minor) | Move ^19^ after "plasmode simulations"; cite ref 20 (Morris) for MCSE |
| 33 | 59 | LVEF/eGFR oriented clinically; post hoc orientation | g2b `ADV_SIGN`; G2_EXTENSION §7 | yes | MATCH | — |
| 34 | 59 | Added arms; same cells, seeds, replicates | paper2_plasmode `NEW_ARMS`, RNG keys | 6 arms; streams keyed by rep, trial, confounder, scenario | MATCH | — |
| 35 | 59 | "Existing arms were reproduced exactly before the new arms were run" | plasmode/gate.csv; summary_check.csv | gate on 6 cells × 3 reps (max dev 0); pooled check 60/60 ≤ 1.4e-14; existing arms reused, not rerun | OVERSTATED (minor) | "…reproduced exactly in a gate subset (6 cells, 3 replicates) and then reused" |
| 36 | 63 | PS-CVD5 analog = demo + 5 dx from prior admissions; 7 trials + PEPTIC; ± ECG / permuted ECG; no CLMBR-T | mimic_cvd5.py `flags()` | as stated | MATCH | — |
| 37 | 63 | 26 held-out items | MIMIC arms `n_vars` | 26 in every trial | MATCH | — |
| 38 | 63 | "As in the previous report, CIs came from 2,000 bootstrap resamples" | mimic_summary `boot_rr`; paper.md MIMIC CIs; l.218/264 | PS-CVD5 CIs use 2,000; paper 1 main-text MIMIC CIs and paper2's own window-fix CIs use 4,000 | MISMATCH | Recompute at 4,000 (6.6% [2.4–13.1]; 11.8 [7.4–16.9]; 11.5 [7.0–17.7]; 6.5 [−0.4 to 13.6]) or say "2,000 for the PS-CVD5 analysis; 4,000 for window-fixed paper 1 values"; drop "as in the previous report" |
| 39 | 63 | P values nominal, no FDR | MIMIC_PAPER2 §5.7 | exact one-sided sign-flip | MATCH | Say "one-sided" |
| 40 | 67 | Mean \|SMD\| over items observed in both arms; relative reduction = 1 − ratio of across-trial means; 4,000 resamples, fixed seed | SP `paired_balance`, `relred_ci` (seed 20261001) | reimplemented; CIs reproduce to 1e-13 | MATCH | — |
| 41 | 67 | Exact sign-flip; one-sided vs base/placebo; two-sided for head-to-heads and placebo vs base | v17 `signflip_1s`; PG `contrasts` | reimplemented (meet-in-the-middle); P reproduce exactly | MATCH | — |
| 42 | 67 | Comparator clustering and leave-one-out | SP `contrast_row` | computed; LOO results never reported | MATCH | Optionally report the LOO max P |
| 43 | 67 | BH within set over 337 rows; balance family {m54, lt01_54, m58, lt01_58}, agreement {absd, cons, bshuf}; domains separate | PG `summarize` | 337 = 55 × 6 + 7; my q = v21 q (≤ 1e-16) | MATCH | — |
| 44 | 69 | CV penalty (5-fold log loss, grid 1e-4–10), C = 0.1 / 0.01; retention ≥ 50/70/90%; outside FDR | PG `cv_C`, `flagscv` | logspace(−4, 1, 11); yes | MATCH | — |
| 45 | 71 | Label test: difference in mean absolute gain, 10,000 permutations, BH within label families; domain mapping; LV structure not tested; heart-rate proxy | PG `labels`, `DOMAIN_ITEMS` | reimplemented; P and q identical | MATCH | — |
| 46 | 71 | Data-driven check vs residual echo imbalance; sensitivity S38 and CLMBR32; Python 3.11 | PG `labels`; env | Spearman on the m54 gain; python 3.11 | MATCH | — |
| 47 | 77 | Areas AF 12, DM 7, HF 5, HTN 2, ACS/MI 2, other 4 | quality_tiers.json | identical | MATCH | — |
| 48 | 77 | 212,496 patients; median 4,730; range 1,442–22,277 | restricted_cells (P5 base main n) | 212,496; 4,729.5; 1,442–22,277 | MATCH | paper.md says 4,729; harmonise |
| 49 | 77 | 43,958 pairs; median 971; range 314–4,100; 88.6% retention | restricted_cells; RR | 43,958; 970.5; 314–4,100; 88.55% | MATCH | — |
| 50 | 77 | Ten physiologic trials (named) | TRIAL_LABELS.json ∩ S32 | same 10 | MATCH | — |
| 51 | 81 | Mean \|SMD\| 0.130 → 0.118 / 0.114 / 0.112 | CR (=sens) | 0.1299 → 0.1184 / 0.1139 / 0.1123 | MATCH | — |
| 52 | 81 | ECG 8.8% (4.4–13.3), 21/32 | CR | 8.85 (4.37–13.30), 21/32 | MATCH | — |
| 53 | 81 | CLMBR-T 12.4% (7.1–17.7), 23/32 | CR | 12.37 (7.09–17.73), 23/32 | MATCH | — |
| 54 | 81 | Both 13.5% (6.6–20.4), 23/32 | CR | 13.54 (6.56–20.42), 23/32 | MATCH | — |
| 55 | 81 | Cluster P ≤ .004; q ≤ .003 | CR | cluster .0022/.0023/.0042; q .0021/.0005/.0026 | MATCH | — |
| 56 | 81 | % < 0.1: 53.4 → 57.0, 58.7, 59.9 | CR | 53.40 → 57.04, 58.65, 59.93 | MATCH | — |
| 57 | 81 | Placebos ECG 1.0% (−2.8 to 4.8); CLMBR-T 2.4% (−2.1 to 6.8); "did not improve" | CR | 0.97 (−2.79 to 4.81); 2.40 (−2.13 to 6.77) | MATCH | — |
| 58 | 81 | 58-item 9.0, 14.0, 15.3% | CR `relred58` | 9.02, 14.03, 15.28 | MATCH | — |
| 59 | 81, 208 | "Adding both improved it most" / "the two together improved it most" | CR | both 13.5 vs CLMBR-T 12.4; ECG over CLMBR-T +1.3% (−4.2 to 6.6), q = .49 (main); significant only under overlap (q = .005) and GBM (.009) | OVERSTATED (minor, l.208) | Discussion: "numerically most; the further gain from adding the ECG to CLMBR-T reached q < .05 only with overlap weighting and the GBM PS" |
| 60 | 83 | CLMBR-T vs ECG 3.9% (−1.8 to 8.9), q = .36 | CR | 3.86 (−1.83 to 8.95), q .363 | MATCH | — |
| 61 | 83 | ECG over P5 + CLMBR-T 1.3% (−4.2 to 6.6), q = .49; CLMBR-T over P5 + ECG 5.2% (−1.5 to 11.6), q = .18 | CR | 1.34 (−4.17 to 6.63) q .485; 5.15 (−1.52 to 11.62) q .179 | MATCH | — |
| 62 | 85, 218 | Retention 79.1 / 77.5 vs 88.6 / 87.6%; "about 10 points less" | RR | 79.08 / 77.50 / 88.55 / 87.61 | MATCH | — |
| 63 | 85 | "Restriction may contribute, but it did not explain the CLMBR-T gain" | RR | gain in 15 low-loss trials 9.3% vs 15.3% in the 17 others | OVERSTATED | "…did not fully explain the gain, which was smaller (9.3% vs 15.3%) but persisted in trials with little retention loss" |
| 64 | 85 | "The per-trial gain was not correlated with the loss of retention (ρ = 0.21; P = .24)" | RR | ρ 0.215, P .238 | OVERSTATED (null claim) | "was weakly and not significantly correlated with…" |
| 65 | 85 | 15 trials: CLMBR-T 9.3% (2.0–16.5); ECG 6.9% (1.2–12.7) | RR | 9.34 (2.00–16.52); 6.93 (1.16–12.71) | MATCH | — |
| 66 | 85 | Overlap CLMBR-T 13.6% (8.8–18.6) | CR overlap | 13.58 (8.75–18.64) | MATCH | — |
| 67 | 85 | 32 PCs 11.2% (6.5–16.0); 64-PC placebo none; "not an artefact of dimension" | CR | 11.20 (6.47–15.98); shufCLMBR 2.4 (−2.1 to 6.8) | MATCH | — |
| 68 | 89 | Gains largest with the sparsest PS and diminishing | CR | P1 > P5 > hdPS/Flags/clinical | MATCH | — |
| 69 | 89 | PS-Demo: 11.3 (6.0–16.1), 20.7 (13.3–27.8), 25.8 (19.0–32.2) | CR | 11.32 (5.97–16.07); 20.66 (13.27–27.79); 25.81 (18.96–32.22) | MATCH | — |
| 70 | 89 | PS-Demo CLMBR-T vs ECG 10.5%, q = .022 | CR | 10.54, q .0218 | MATCH | — |
| 71 | 89 | hdPS + ECG 7.6% (1.7–13.0), q = .033; vs permuted ECG 4.8% (−2.4 to 12.0), q = .26 | CR | 7.60 (1.75–13.03) q .0325; 4.79 (−2.42 to 12.00) q .256 | MATCH | — |
| 72 | 89 | hdPS + CLMBR-T −3.5% (−14.0 to 6.0); CLMBR-T vs ECG −12.1%, q = .021 | CR | −3.54 (−13.98 to 6.01); −12.08 q .0207 | MATCH | — |
| 73 | 89 | Flags: ECG −3.0 (−7.3 to 1.1); CLMBR-T −2.9 (−8.7 to 3.0) | CR | −3.04 (−7.27 to 1.10); −2.87 (−8.69 to 3.03) | MATCH | — |
| 74 | 89 | Clinical: ECG −1.3 (−6.8 to 3.9); CLMBR-T 0.8 (−3.9 to 5.9) | CR | −1.30 (−6.76 to 3.91); 0.76 (−3.87 to 5.92) | MATCH | — |
| 75 | 89 | q < .05 rows (primary endpoint, main) all within PS-Demo/PS-CVD5/hdPS; none Flags/Clinical/cross-rung | CR | 18 rows: 8 P1, 5 P5, 2 hdPS, 3 CLMBR32 rows (P1/P5) | MATCH | — |
| 76 | 93 | ECG: LV function 16.4 (2.5–28.5) q .09; LV structure 14.9 (3.5–25.3) q .07; diastolic 16.1 (6.1–24.3) q .03; vitals 8.7 (3.4–13.8) q .02 | DR (= dom) | 16.39 q .095; 14.91 q .067; 16.08 q .028; 8.71 q .017 | MATCH | — |
| 77 | 93, 210; gallery Fig 3 | "ECG's gains concentrated in echocardiographic domains" vs CLMBR-T in labs/vitals | DR | CLMBR-T LV structure 14.7% (1.3–26.4), q .12, same as the ECG's 14.9% (direct −0.2%) | OVERSTATED (minor) | Add "CLMBR-T also reduced LV-structure imbalance (14.7%)"; restrict the ECG-specific claim to LV function and diastolic/LA |
| 78 | 93 | CLMBR-T vitals 22.7 (15.5–29.4), other labs 24.1 (13.0–33.2), q < .01; valves 15.9 (4.5–25.0) q .04; LV function 1.0, diastolic 0.7 | DR | 22.71 q .0003; 24.07 q .003; 15.89 q .041; 1.04; 0.67 | MATCH | — |
| 79 | 93 | Neither improved RV/pulmonary | DR | −1.8; 0.2 | MATCH | — |
| 80 | 93 | ECG ahead: LV function −18.4% q .14, diastolic −18.4% q .09; m13 −4.6/−6.1; overlap −4.6/−4.6; all q ≥ .38 | DR | −18.36 q .138; −18.37 q .093; m13 −4.6/−6.1 (q .78/.54); overlap −4.6/−4.6 (q .66/.38) | MATCH | — |
| 81 | 93 | CLMBR-T ahead for other labs main 18.4% q .045; vitals q < .05 in cal01, m13, overlap, GBM; other labs m13, overlap; not IPTW | DR | 18.41 q .045; vitals q .043/.003/.001/.001; other labs .001/.001; IPTW .95/.86 | MATCH | Complete: also valves under 1:3 matching (12.9%, q = .004) |
| 82 | 97 | No detectable difference: 0.112 vs 0.113; 0.7% (−5.5 to 6.8); 13/31; P = .81; "not equivalence" | CR | 0.1118 vs 0.1127; 0.75 (−5.47 to 6.82); 13/31; .814 | MATCH | — |
| 83 | 97 | Flags + CLMBR-T −2.9% (−8.7 to 3.0); PS-Demo + CLMBR-T(32) vs Flags −2.9% (−10.1 to 4.4) | CR | −2.87; −2.90 (−10.13 to 4.35) | MATCH | — |
| 84 | 97 | Agreement 0.186 vs 0.174, paired 31; 19/31; P = .50; benchmark P = .97 | CR | 0.1858 vs 0.1739 (n 31); 19/31; .495; .974 | MATCH | — |
| 85 | 97–99, 212 | Head-to-head shown only for the primary configuration; "no specification showed CLMBR-T balancing better … at conventional significance" | CR (m13, cal01, IPTW rows) | 1:3 matching: 5.1% (0.97–9.42), 21/31, P = .030, q = .093; cal01 4.3% (P = .24); IPTW 28.0% (q = .009, disclosed l.101) | OVERSTATED (omission) | Add: "with 1:3 matching, PS-Demo + CLMBR-T was nominally better balanced (5.1%; 95% CI, 1.0–9.4; P = .030; q = .09)"; in l.212 replace "no evidence that it does better" with "no FDR-surviving evidence…" |
| 86 | 99 | "With the common penalty, PS-Flags overfitted small trials" | PS_FLAGS.md table; flag_proxies | in-sample AUC 1.00 in PROTECT AF; low retention also in large trials (LODESTAR, n = 22,277, retention 0.41) | OVERSTATED (minor) | "…overfitted, most extremely in small trials such as PROTECT AF" |
| 87 | 99 | PROTECT AF: 1,442 patients, 622 flags, C = 1.00, < 11 pairs, dropped out | log.json; review/restricted_flag_proxies.csv | n 1,442; 622; AUC 1.000 (3 dp); excluded from matching-config Flags contrasts (31) but present under IPTW/overlap/GBM (32) | MATCH | "dropped out of the matched PS-Flags contrasts" |
| 88 | 99 | Other 31 trials: 73.5% retention | RR | 0.7352 (k 31) | MATCH | — |
| 89 | 99 | CV penalties 300 to 3,000 times stronger | flagscv_log.csv | C ∈ {3.16e-4, 1e-3, 3.16e-3} → 316–3,162× | MATCH | — |
| 90 | 99 | CV-tuned −1.5% (−7.5 to 4.4), P = .63 | FR | −1.52 (−7.45 to 4.38), .628 | MATCH | — |
| 91 | 99 | C = 0.1: 7.7% (−0.1 to 15.8), P = .085; C = 0.01: 1.0% (−5.1 to 6.8) | FR | 7.68 (−0.09 to 15.78) .085; 0.96 (−5.12 to 6.77) | MATCH | — |
| 92 | 99 | Retention ≥ 50/70/90%: 27/19/11 trials; −1.1, −2.6, −5.1 | FR | 27/19/11; −1.07, −2.59, −5.07 | MATCH | — |
| 93 | 99 | Range about −5% to +8% | FR | −5.1 to +7.7 | MATCH | — |
| 94 | 99 | CV agreement 0.216 vs 0.170; 21/32; P = .069; benchmark P = .001 | FR | 0.2157 vs 0.1705; 21/32; .0692; .0013 | MATCH | — |
| 95 | 99 | 1:3: P = .038, benchmark < .001; overlap P = .64, benchmark .70; primary Flags benchmark .97 | FR; CR | .0380, .0007; .639, .696; .974 | MATCH | — |
| 96 | 101 | vs hdPS 3.8% (−3.0 to 10.0) and 3.8% (−2.7 to 9.6) | CR | 3.75 (−2.99 to 9.96); 3.79 (−2.67 to 9.64) | MATCH | — |
| 97 | 101 | vs PS-Clinical −4.9% (−11.2 to 0.9), q = .25; GBM −11.9%, q = .007 | CR | −4.87 (−11.24 to 0.91) q .250; −11.90 q .0070 | MATCH (note) | Note: this contrast excludes the 9 vitals/core labs in PS-Clinical (45 items, by `ex58` pairing), exactly where CLMBR-T gains most; say "on the 45 characteristics not in PS-Clinical" |
| 98 | 101 | IPTW: vs Flags 28.0% (14.0–39.2), q = .009; vs hdPS 17.9%, q = .004 | CR | 28.04 (14.01–39.15) q .0094; 17.91 q .0036 | MATCH | — |
| 99 | 101 | ESS fraction 0.18 and 0.34 vs 0.72 | RR | Flags 0.177; hdPS 0.335; P5 0.721 | MATCH | — |
| 100 | 105 | 0.226 → 0.196 (20/32; P = .049; cluster .20) | CR | 0.2261 → 0.1956; .0486; .197 | MATCH | — |
| 101 | 105 | 0.166 (18/32; .030; cluster .046); 0.158 (18/32; .019; cluster .10) | CR | 0.1663 .0296 .0461; 0.1577 .0193 .0995 | MATCH | — |
| 102 | 105 | q = .58, .51, .43; benchmark P .70, .93, .94 | CR | .580/.514/.427; .698/.934/.944 | MATCH | — |
| 103 | 105 | r 0.56 → 0.57, 0.50, 0.59; EA 15 → 22, 20, 20; std-diff 24 → 25, 26, 30 | CR | 0.560 → 0.566, 0.500, 0.590; 15 → 22/20/20; 24 → 25/26/30 | MATCH | — |
| 104 | 105, 208, 214 | Attenuation toward the null rather than trial-specific correction | CR bshuf; MC | mean \|log HR\| 0.302 → 0.268 (ECG), 0.191 (CLMBR-T), 0.183 (both); toward 0 in 20/26/24 of 32; mean \|RCT log HR\| 0.186 | MATCH | Optionally add the \|log HR\| shrinkage as direct evidence |
| 105 | 105 | Placebos 0.226 and 0.227 | CR | 0.2262; 0.2267 | MATCH | — |
| 106 | 105 | 5 AF trials: 0.135 → 0.212; 1/5 (eTable 9) | supplement eTable 9; recomputed from cells | 0.135 → 0.212; 1/5 | MATCH | — |
| 107 | 109 | cal01 7.8/10.1/15.8; m13 6.4/13.3/13.6; overlap 7.4/13.6/16.2; all q ≤ .010 | CR | 7.83/10.14/15.81; 6.36/13.33/13.64; 7.38/13.58/16.19; max q .0102 | MATCH | — |
| 108 | 109 | IPTW ECG 4.8% (1.5–8.5), q = .013; CLMBR-T −2.0; both −0.9; ESS 0.72 → 0.44 | CR; RR | 4.85 (1.47–8.45) q .0128; −1.99; −0.95; 0.721 → 0.437 | MATCH | — |
| 109 | 109 | GBM ECG −1.1 (−7.3 to 4.3); CLMBR-T 6.9 (1.1–12.7) q .058; both 13.2 (8.8–17.9) q < .001 | CR | −1.07 (−7.29 to 4.30); 6.89 (1.11–12.70) q .058; 13.16 (8.83–17.86) q .0001 | MATCH | — |
| 110 | 109 | Permuted ECG −0.7% q .050 (overlap); −4.2% q .045 (GBM) | CR | −0.66 q .0498; −4.24 q .0452 | MATCH | — |
| 111 | 109 | CLMBR-T vs ECG: m13 7.4 q .022; overlap 6.7 q .012; GBM 8.1 q .036; not main/cal01/IPTW | CR | 7.45 q .0216; 6.69 q .0117; 8.07 q .0360; q .36/.61/.54 | MATCH | — |
| 112 | 109 | ECG over P5 + CLMBR-T: overlap 3.0 q .005; GBM 6.7 q .009; not others | CR | 3.03 q .0053; 6.74 q .0095; cal01 q .067 | MATCH | — |
| 113 | 111 | 98 of 337 rows q < .05 (18/14/18/7/23/18); no agreement row | CR | 98 (18/14/18/7/23/18); agreement 0 | MATCH | — |
| 114 | 111 | ECG m13 P = .007 (benchmark .037); GBM benchmark .005; q .43/.52 (m13), .43 (GBM) | CR | .0070 (.0374); .0048; q .425/.519/.425 | MATCH | — |
| 115 | 111; gallery Fig 5 ("reproduces paper 1") | "For the ECG, the agreement pattern of our previous report reproduced with PS-CVD5" | supplement eTable 7 (PS-Demo configurations); paper.md l.97 | paper 1 reported configurations for PS-Demo only; benchmark P there .26–.85, never < .05; no PS-CVD5 configuration results | UNSUPPORTED | "With PS-CVD5, the ECG gave nominal trial-specific signals not seen with PS-Demo in our previous report: …, neither surviving FDR"; remove "reproduces paper 1" from the Figure 5 legend |
| 116 | 111 | Other ECG benchmark P .20–.96; CLMBR-T and both ≥ .78 everywhere | CR | .70/.85/.96/.20; min .781 | MATCH | — |
| 117 | 111; gallery eFig 5 | S38: 9.0, 12.7, 14.5; Flags 0.2; three GBM agreement rows q < .05 | CR S38 | 9.04, 12.73, 14.45; 0.16; 3 rows (2 \|Δ\|, 1 benchmark) | MATCH | — |
| 118 | 115 | Physiologic vs other: ECG 16.3 (7.8–25.7) vs 5.7 (1.0–10.2), P .048, q .16 | LP | 16.30 (7.78–25.69) vs 5.66 (0.95–10.20); .0482; .163 | MATCH | — |
| 119 | 115 | CLMBR-T 22.6 (14.1–31.0) vs 8.0 (2.5–13.6), P .025, q .13; both 29.6 (20.8–38.3) vs 6.7 (−0.5 to 13.7), P .004, q .060 | LP | 22.64 vs 7.98; .0254; .128; 29.62 vs 6.67; .0040; .060 | MATCH | — |
| 120 | 115 | "None of these differences survived FDR"; "nominally larger" | LP (all configurations); MC | primary only. Within-config label family: m13 ECG/CLMBR-T/both q .004/.033/.004; overlap .007/.022/.013; IPTW ECG .033. BH over all 6 configs × 15: ECG m13 .018, overlap .016, IPTW .022; both m13 .015, main .033, overlap .033 | OVERSTATED (scope) | "None survived FDR in the primary configuration; with 1:3 matching and overlap weighting the differences reached q < .05 for both representations (label analyses by configuration in eTable X)" |
| 121 | 115 | Placebos P ≥ .69; agreement by label P ≥ .87 | LP | .738/.688; .98/.87/.93 | MATCH | — |
| 122 | 115, 216 | "More likely reflect more confounding to remove … than ECG-specific content" | LP | interpretive; supported by CLMBR-T showing the same pattern | MATCH | — |
| 123 | 117 | LV systolic, 7 trials: 0.097 vs 0.011 (.003); 0.079 vs −0.018 (.002); 0.122 vs −0.011 (.001); q .021; permuted ECG P .32 | LD | identical; q .0207; .324 | MATCH | — |
| 124 | 117 | Union: ECG P .005 q .056; CLMBR-T P .037 q .25 | LD | .0048 .056; .0371 .247 | MATCH | — |
| 125 | 117, 216 | "No other domain label was associated with a larger gain at q < .05"; "the only label result to survive FDR" | LD (all configurations); MC | primary only. Overlap weighting: rhythm/conduction (heart rate) ECG q = .009 (8 labelled trials); LV systolic survives in cal01, m13, overlap | OVERSTATED (scope) | Add "in the primary configuration"; mention the overlap-weighting rhythm/conduction row |
| 126 | 117 | Spearman ECG 0.36 (.045), CLMBR-T 0.41 (.021); permuted CLMBR-T 0.46 (.008); permuted ECG 0.19 (.31) | LS | 0.357 .045; 0.407 .021; 0.461 .008; 0.187 .307 | MATCH | — |
| 127 | 119 | ECG by quality: 0.216 → 0.171 (9/15; .078); 0.235 → 0.217 (11/17; .21) (eTable 5) | MC; supplement eTable 5 | identical | MATCH | — |
| 128 | 119 | CLMBR-T gain 0.072 vs 0.049; permuted ECG 0.030 vs −0.027 | MC | 0.072/0.049; 0.030/−0.027 | MATCH | — |
| 129 | 123 | 107 combinations in 31 trials | PM | 107 cells (LVEF 25, NT-proBNP 21, BMI 31, eGFR 30); 31 trials | MATCH | — |
| 130 | 123 | PS-CVD5 18.6% vs PS-Demo 2.4% | PM | 18.57; 2.41 | MATCH | Define "% bias removed (null-corrected)" in Methods |
| 131 | 123 | Added: ECG 11.3 (0.3), CLMBR-T 22.6 (0.3), both 29.5 (0.4); placebo 1.0 (0.4) | PM | 11.32 (0.34); 22.59 (0.35); 29.48 (0.38); 0.97 (0.36) | MATCH | — |
| 132 | 123 | LVEF 15.2 vs 8.4; eGFR 2.5 vs 35.5; NT-proBNP 15.1 vs 28.4 | PM | 15.15/8.41; 2.49/35.53; 15.11/28.39 | MATCH | — |
| 133 | 123 | "This followed how well each representation predicted the confounder" | r2_p5.csv | holds for eGFR, NT-proBNP and LVEF; BMI: CLMBR-T R² 0.25 vs ECG 0.22 but CLMBR-T removed less (10.2 vs 19.2) | OVERSTATED | "largely followed … (except BMI)" |
| 134 | 123 | R² eGFR 0.34 vs 0.05; LVEF 0.19 vs 0.22 | PM | 0.343/0.046; 0.191/0.216 | MATCH | — |
| 135 | 123 | ECG over P5 + CLMBR-T 8.9% overall, 9.7% LVEF; best arm 42.6% vs 93.7%; coverage 76.9% vs 94.4%; non-oracle 51–77% | PM | 8.90; 9.72; 42.57/93.73; 76.91/94.36; 51.2–76.9 | MATCH | Oracle is PS-Demo + C; say so |
| 136 | 127 | MIMIC 6.6% (2.3–12.8); 6/7; P .016 | MM | 6.60 (2.3–12.8); 6/7; .0156 | MATCH | — |
| 137 | 127 | % balanced 45.6 → 51.6; 3/7; P .125; permuted −3.1% | MM | identical; −3.11 | MATCH | — |
| 138 | 127 | Any diabetes 11.8 (7.2–16.7); index codes 11.5 (7.1–17.4); no index-day ECG 6.5 (−0.2 to 13.6) | MM | 11.78; 11.47; 6.48 (CIs identical at 2,000) | MATCH | — |
| 139 | 127 | \|Δ\| 0.344 → 0.326 (4/7; .27); permuted 0.323; PEPTIC 1.05; 1.51 (1.35–1.69) → 1.39 (1.24–1.55); permuted 1.60 | MM | identical | MATCH | — |
| 140 | 135–172 | Table 1 PICOT cells (38 rows) | T1 vs committed and working-copy table1_picot.md | 38/38 identical (working-copy change is whitespace only) | MATCH | — |
| 141 | 135–172 | Table 1 labels and domains | T1 vs TRIAL_LABELS.json | 38/38 | MATCH | — |
| 142 | 135–172 | Table 1 quality tier and points; Time (mo) | T1 vs quality_tiers.json, HORIZON_MONTHS | 38/38 | MATCH | — |
| 143 | 135–172 | Table 1 RCT estimates and CI levels | T1 vs trial_specs `PUBLISHED`; rb/rs in cells | 38/38; COMET analysed as 1/0.83 = 1.205 (reversed orientation) | MATCH (note) | Footnote the COMET orientation |
| 144 | 183, 186 | ROCKET-AF ITT / per-protocol; PROTECT AF credible interval; tier definitions | trial_specs; quality_tiers scheme | match | MATCH | — |
| 145 | 188 | CABANA "disabling stroke" omitted | trial_specs `OUTCOMES` | stroke broadened to any stroke hospitalisation (not omitted); serious bleeding narrowed to GI bleed/ICH | MISMATCH (minor) | "CABANA (any stroke in place of disabling stroke; serious bleeding limited to GI bleeding or ICH)" |
| 146 | 191; Fig 1 | Figure 1: 38/32, 32/64 PCs, ladder, 54 items, 426–622 flags | figure PNG | consistent. Also: "2011–2024" (see #3); "6 arms" (7 with CLMBR32); nested ladder arrows (see #21); "(PI hypothesis)" is a draft label | MISMATCH (minor) | Fix the year, arm count and arrows; drop "PI hypothesis" |
| 147 | 193; Fig 2 | Figure 2 legend and panel values | CR | every estimate, CI, trials better and q matches | MATCH | — |
| 148 | 195; Fig 3 | Figure 3 A/B heatmaps and C head-to-heads | DR; CR; FR | match (e.g. C=0.1 \|Δ\| 0.218 → 0.170; CV 1:3 0.223 → 0.166) | MATCH | See #77 for the gallery wording "ECG's gains sit in the echo domains" |
| 149 | 197; Fig 4 | Figure 4 legend, 10 vs 22, P/q, domain panel | LP; LD | match | MATCH | — |
| 150 | 199; Fig 5 | Figure 5 A–D legend and panels | CR; MC | match (counts 18/14/18/7/23/18 \| 0 \| 0) | MATCH | Gallery legend: see #115 |
| 151 | 203; eFig 1 | eFigure 1 caption and legend | PM | values match; legend says only the orientation is post hoc | OVERSTATED (minor) | "design and orientation post hoc" |
| 152 | 203; eFig 2 | eFigure 2 caption and legend | MM | match; panel A 2,000 / panel B 4,000 resamples, as the legend states | MATCH | Harmonise with #38 |
| 153 | 203; eFig 3 | 62 rows × 6 configurations; 98 balance cells; IPTW ESS 0.18 / 0.34 | CR; RR | 55 × 6 + 7 = 337; 98; 0.177/0.335 | MATCH | — |
| 154 | 203; eFig 4 | Retention, ESS, subsets, CV-Flags panels and legend ("gains persist in 15 trials", "CV-Flags helps only under overlap") | RR; FR | match (overlap CLMBR-T 4.6%, ECG 2.9%, both P < .001; others NS) | MATCH | — |
| 155 | 203; eFig 5 | S38 and CLMBR32 rows; "Flags head-to-head essentially unchanged" with 32 PCs | CR | values match; head-to-head +0.7 → −2.9 (both NS) | MATCH | "remains non-significant" is more exact than "essentially unchanged" |
| 156 | 208, 220 | Gains replicate across most approaches; CLMBR-T adds nothing to Flags/hdPS/Clinical; ECG adds to hdPS (placebo caveat); no agreement q < .05 | CR | consistent with #71–74, #107–113 | MATCH | — |
| 157 | 212 | Holds with CV-tuned Flags and retention restriction; point estimate moves by several points; not equivalence | FR | consistent | MATCH | See #85 for the 1:3 omission |
| 158 | 214 | "This reproduces the finding of our previous report and of earlier unpublished CLMBR-T analyses"; 337 rows; 30/32 | supplement eTables 4/7; docs/v18/CLMBR_RESULTS.md | paper 1 benchmark P .26–.85 (PS-Demo); v18 "generic shrinkage … not trial-specific" | MATCH | — |
| 159 | 218 | Limitations: post hoc orientation; plasmode arms missing; coverage below nominal; truncation; MIMIC ~5 points; window-fix 7.5 → 8.1 (−0.1 to 17.3), 1.2 → 3.0 (−8.6 to 15.2) | PM; MM | values match; "post hoc orientation" understates (design also post hoc) | OVERSTATED (minor) | "with a post hoc design and orientation" |
| 160 | 262 | Paper 1 PS-CVD5 + ECG agreement q = .14 vs .58 here | supplement eTable 4; CR | .14; .580 | MATCH | — |

Reference notes, not counted: ref 20 (Morris) and ref 21 (MIMIC-IV-ECG) are listed but never cited; refs 24–25 keep their [CHECK] markers.

### Verdict counts

| Verdict | Rows | Row numbers |
|---|---|---|
| MATCH (incl. "MATCH (note)", "MATCH (wording)", "MATCH (detail undisclosed)") | 137 | all others |
| MISMATCH | 9 | #3, 13, 21, 24, 31, 32, 38, 145, 146 |
| UNSUPPORTED | 1 | #115 |
| OVERSTATED | 12 | #35, 59, 63, 64, 77, 85, 86, 120, 125, 133, 151, 159 |
| UNTRACEABLE | 1 | #5 |
| **Total** | **160** | |

**MATCH rows that still carry a proposed fix:**
- #17: undisclosed HF definition.
- #20: hdPS wording.
- #29: the NaN log HR = disagreement coding.
- #97: the 45-item PS-Clinical comparison set.
- #143: COMET orientation footnote.
- #81, #155: completeness.

## Comparison with the earlier audit (docs/v21/AUDIT_PAPER2_MANUSCRIPT.md, step H, 155 checks)

I read it only after finishing the pass above. In the table below, the earlier audit's row numbers are its own §2 numbering. On the numbers, we agree completely: every value it marks MATCH, I reproduced independently from cell-level data. Its applied fixes (median 4,730; the CLMBR-T(32) attribution; benchmark-permutation q .43/.52; the domain-replication wording; "for the primary balance endpoint"; the heart-rate proxy; the hdPS placebo caveat; removal of "about as well as") are all present in paper2.md at `trace-v1` and are correct.

**Where I disagree (its verdict → mine):**

| Earlier # | Topic | Earlier | This recheck | Why |
|---|---|---|---|---|
| 1 | Index dates 2011–2024 | MATCH (reused text) | MISMATCH, minor (#3) | COMET has 1–10 index dates in 2025 |
| 2 | 99 candidates | MATCH (QT `counts_tier`) | UNTRACEABLE (#5) | `counts_tier` holds only the 38 tiers; 99 exists only as paper 1 text, with no tally |
| 9 | Study-drug codes ≤ 5.9% | MATCH | MISMATCH (#13) | 33-trial new-user figure; switch designs and FRAIL-AF / PROTECT AF reach ~100% by design |
| 17 | PS-Clinical contents | MATCH | MISMATCH, ambiguous (#21) | "further included" implies the hdPS features are in PS-Clinical; they are not |
| 19–20 | Matching / configurations | MATCH | MISMATCH, incomplete (#24) | IPTW trimming at the 1st/99th PS percentiles is undisclosed; the CLMBR32 arm ran in main only |
| 28 | Plasmode "primary design", exact reproduction | MATCH | MISMATCH (#31) + OVERSTATED (#35) | paper 1 calls the design post hoc; the gate was a subset and the existing arms were reused |
| 30 / fix 8 | MIMIC bootstrap | MISMATCH → fixed by adding "As in the previous report, 2,000 resamples" | MISMATCH (#38) | The fix itself is wrong: paper 1's MIMIC CIs and paper2's window-fix CIs use 4,000 |
| 59 / fix 13 | Restriction "did not explain" | UNSUPPORTED → softened | still OVERSTATED (#63, #64) | "did not explain" and "not correlated (ρ = 0.21, P = .24)" remain null claims without a CI; the low-loss subset gain is about 40% smaller |
| 82, 93 / fix 11 | Flags head-to-head "no detectable difference" | MATCH | OVERSTATED, omission (#85) | 1:3 matching: 5.1% (1.0–9.4), P = .030 favouring PS-Demo + CLMBR-T, unreported |
| 120 | "Agreement pattern of our previous report reproduced" | MATCH (numbers) | UNSUPPORTED (#115) | Paper 1 has no PS-CVD5 configuration results, and its PS-Demo benchmark P were all ≥ .26 |
| 127, 129 | Labels: none survives FDR; no other domain q < .05 | MATCH | OVERSTATED, scope (#120, #125) | True only in main; 1:3 and overlap physiologic-label rows and the overlap rhythm row reach q < .05 |
| 135 | Plasmode "followed how well each predicted" | MATCH | OVERSTATED (#133) | Fails for BMI |
| 2j | Table 1 | MATCH (footnotes not checked) | CABANA footnote MISMATCH (#145) | Stroke broadened, not omitted |
| 2k Fig 1 | "6 arms" | cosmetic note | MISMATCH, minor (#146) | Also "2011–2024", nested-ladder arrows and the draft label "(PI hypothesis)" |
| 2i #140 / 2d #74 | Discussion / domain framing | MATCH | OVERSTATED, minor (#59, #77) | "two together improved it most" is not significant in main; CLMBR-T's equal LV-structure gain is omitted |

**Where it found something I would otherwise have missed:** nothing remaining. Its fixed items (Figure 1 flag range, the attribution and q errors) are verified as fixed in the current text.

**Method difference.** The earlier audit read `sensitivity.csv` and the other summaries and recomputed only cohort totals and quality-tier agreement. It did not read `restricted_*`, parquet or `review/` files. This recheck rebuilt every statistic from the cells, which is why it can confirm the BH families and the ex58-paired item sets, and why it found the configuration-dependence of the label and head-to-head results that the summaries contain but the text does not report.

## Files

- Scripts (no outputs in the repository): `scripts/v1_audit/claims/core_recompute.py` (core grid, domains, BH), `secondary_recompute.py` (retention/ESS, PS-Flags fairness, labels), `misc_checks.py` (attenuation, label q by configuration, quality tiers), `recheck_plasmode.py`, `recheck_mimic.py`, `recheck_table1.py`, `recheck_methods_facts.py`.
- Aggregate outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/claims/`. `restricted_methods_trials.csv` there holds per-trial arm counts and stays on raid0.
