# Audit round 4: S10, v1.7 confirmation, S11, v1.8 (CLMBR, AF confirmation), ACC abstract (2026-09-28)

This is an independent, skeptical fourth-round audit of everything committed after round 3 (`d40af18` / `9edcd26`):
- S10 (`e1636c7`, `551524f`);
- the v1.7 plan, blinded rule, builds, confirmation, patterns and S11 (`0e66e3c` … `693fa8e`);
- the v1.8 plans, CLMBR and AF confirmation (`760981a` … `1b78da9`);
- the ACC 2027 abstract (`89568ad`, `57e6bd2`).

**Audit code (own implementations).** It lives in `scripts/v18/audit4/`:
- `a4_common.py`: exact sign-flip by two-half enumeration, benchmark-shuffle variants, BH, metrics;
- `a4_stats.py`: recomputation;
- `a4_clmbr_common.py`: CLMBR retention and common-anchor balance; it re-fits the PS and re-matches with the engine;
- `a4_leak.py`: CLMBR input window and exposure tokens, read directly from the MEDS inputs;
- `a4_overlap.py`: person-level cohort overlap;
- `a4_global.py`: multiplicity.

The only thing imported from the pipeline is the 58-variable list constant (plus `ps_logit` / `match` for the re-matching). No sweep's statistics code is called.

**Outputs.** Aggregates only, in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v18-audit4/` (umask 077):
- `recompute.csv`;
- `clmbr_common_anchor.csv`, `clmbr_retention_from_results.csv`;
- `clmbr_leak_independent.csv`;
- `overlap_persons.csv`;
- `global_v17_v18.csv`;
- `s10_per_trial_recomputed.csv`.

"k/n" are trial counts. Counts of 1–10 patients are suppressed.

## Verdict table

| # | Check | Verdict | Fix |
|---|---|---|---|
| 1 | Independent recomputation | **PASS** | Every headline reproduces to the printed precision (below). The single arithmetic error is in the S10 summary: consistency is **10 → 12/18**, not 11 → 13 (the per-trial table itself is correct). |
| 2 | Pre-registration integrity | **PASS with 2 minor concerns** | Every plan, spec/benchmark and rating commit precedes its result files (timeline below), and no analysis choice deviates from the written plans. (a) In v1.7 the count-only pooled-event screen (09:56–10:00) ran *before* the registration commit `b0c82e9` (10:04). v1.8 fixed this order. (b) The v1.7 category / patterns tables (`per_trial_patterns.csv`, `emulation_by_category.csv`) were produced by **uncommitted code**. Commit it. |
| 3 | Benchmarks (20 checked against the PubMed abstracts) | **PASS** | All 20 v1.7/v1.8 HRs and CIs match the primary abstracts. VALIANT's 97.5% CI is handled (z = 2.24). PROTECT AF's credible interval is treated as a 95% CI (documented). DECLARE uses the co-primary CV death/HHF (0.83), not MACE (0.93). This is pre-registered and the outcome matches, but it is the favourable co-primary: note it. |
| 4 | New-trial design validity (DECLARE, LODESTAR, ACTIVE W, LAAOS III, PROTECT AF) | **PASS with caveats** | Arms, washout, outcome codes and horizon match the specs and the RCT horizons. The near-duplicate rule (< 80% identical (patient, index) records) was applied consistently. However, it measures only *exact* (patient, index) identity. Person-level overlap is larger: ACTIVE W–ARISTOTLE 78% of persons; INSIGHT–ALLHAT 79%; AFFIRM–EAST-AFNET 4 48% (the docs' "AFFIRM contains most EAST-AFNET 4 records" is imprecise). State person-level overlap. |
| 5 | CLMBR leakage, stop rule, retention | **PASS** | Independent MEDS check: 0 events at or after index midnight in 38/38 trials; the latest event is index − 1 min. Exposure-token rates reproduce. The plan said "absent from the input **or documented**", so proceeding was consistent with the written plan (there was no stop rule). CLMBR keeps 93% of base pairs (min 71%). On the common-anchor population the P1 non-coded gain is **+7.6 pp (91% of +8.4)**, p = 6e-5. Trimming explains little. |
| 6 | Statistics | **PASS with concerns** | The sign-flip is exact for n = 33 (meet-in-the-middle; S11's "Monte Carlo" is a doc error). Benchmark draws are joint (rb, rs); with/without replacement changes nothing (Δp ≤ 0.006). **The pool matters for AF-7:** within-set permutation p = 0.096; 33-pool p = 0.032; 38-pool p = 0.063. v1.7's primary construction (within-set) gives 0.096, so "trial-specific" for AF-7 rests on a post-hoc pool choice. Cluster floors: AF-5 1/8 (3 clusters), AF-12 1/8, new-15 S_both 1/4. |
| 7 | Prespecified vs post-hoc labelling | **CONCERN (ACC abstract: FAIL)** | The sweep docs label status correctly, apart from 4 wording fixes (§7). The ACC abstract presents the post-hoc AF finding as a result and draws its conclusion from it, although the prespecified AF confirmation failed. It also cites all-33 \|Δ\| without the failed confirmation (p = 0.074) or the failed benchmark shuffle, and claims "absent from structured data" although CLMBR matched the ECG. Replace it (§7). |
| 8 | Global multiplicity (v1.7 + v1.8; 1,314 tests) | **Confirmatory: nothing survives** | 5 prespecified primaries (v1.7 new-15 P1/P2 × balance/\|Δ\|, v1.8 AF-5 P1 \|Δ\|): min p 0.033, Bonferroni threshold 0.01, BH min q 0.16. Exploratory balance: 166/798 survive BH within domain. Emulation: 10/516 survive BH (all are all-33 z²/\|Δ\| cells), but **0** are also benchmark-shuffle significant (min shuffle q 0.13). |
| 9 | Privacy and permissions | **PASS (after fix)** | 10 aggregate files in `claude-v16-s10-demo6`, `claude-v17-confirm`, `claude-v17-screen`, `claude-v17-trials` and `claude-v18-screen` were 644 inside 700 directories; they are now chmod 600. There are no group/world-accessible files or directories under `claude-v17-*` / `claude-v18-*`. The committed markdown/JSON contain no patient counts of 1–10: the only "n = 1/2" are trial counts, and small counts are shown as "<11". |

## 1. Recomputation (own code, from `results_all.csv`, `results_p5.csv`, `claude-v18-clmbr/results_all.csv`, `results_af5.csv`, S10 `results.csv`)

All p values are one-sided exact sign-flips unless stated. "bs" = benchmark shuffle, 200,000 draws.

| cell | reproduced | doc |
|---|---|---|
| v1.7 new-15 P1 % < 0.1 | 52.4 → 58.3, 11/15, p = 0.0326; vs shufECG 0.0003, vs noise 0.040; cluster 0.078 (8); LOO max 0.064; A 0.089 / B 0.0064 | same |
| v1.7 new-15 P2 % < 0.1 | 57.2 → 59.0, 9/15, p = 0.172; vs shufECG 0.372 | same |
| v1.7 new-15 P1 \|Δ\| | 0.250 → 0.208, 8/15, p = 0.074; bs within-set 0.971 (33-pool 0.964, 38-pool 0.886) | 0.074 / 0.971 |
| v1.7 new-15 P2 \|Δ\| | 0.192 → 0.193, p = 0.522; bs 0.355 | same |
| all-33 P1 % < 0.1 | 53.1 → 59.3, 25/33, p = 1.2e-4 (MC 9e-5); cluster 0.0005 (13) | same |
| all-33 P1 \|Δ\| | 0.258 → 0.208, 22/33, p = 0.0044; cluster 0.034; bs 0.366 | same |
| S11 P5 all-33 lt / x / gap | p 0.0021 / < 1e-4 / 0.0028; gap bs 0.101 | same (bs 0.099) |
| S11 P5 new-15 lt / x / gap | 0.066 / 0.031 / 0.069 | same |
| S11 P5 old-18 lt / gap; AF-7 gap | 0.0059 / 0.0093; AF-7 0.376 → 0.261, 6/7, p = 0.023, bs(33) 0.272 | same |
| AF-7 P1 \|Δ\| (v1.7 category) | 0.437 → 0.317, 7/7, p = 0.0078; vs shufECG 0.0156; consistency 2 → 5; **bs: within-7 0.096, 33-pool 0.032, 38-pool 0.063** | 0.008 / 0.016; bs 0.035 (v1.7), 0.028 (CLMBR doc), 0.062 (AF doc) |
| AF-5 P1 \|Δ\| (primary) | 0.254 → 0.199, 3/5, p = 0.1875; bs(38) 0.286; vs noise32 0.75 | 0.19 / 0.28 |
| AF-5 P5 \|Δ\| | 0.135 → 0.212, 1/5, p = 0.969; bs 1.00 | same |
| AF-12 P1 \|Δ\| | 0.361 → 0.268, 10/12, p = 0.0037; bs(38) 0.135; vs noise 0.055; cluster 0.125 | same |
| AF-12 P1 58-panel % < 0.1 | 44.0 → 51.6, p = 0.016, **vs shufECG p = 0.112**, vs noise 0.014 | doc says "beyond shufECG" (see §7) |
| CLMBR P1 non-coded % < 0.1 | 53.3 → 61.6, 26/33, p = 4e-5; cluster 0.0005; LOO 1e-4; A/B < 0.001; vs shufCLMBR / noise64 < 1e-4 | same |
| CLMBR vs ECG (P1, non-coded, 2-sided) | +2.2 pp, p = 0.216 | same |
| CLMBR+ECG vs CLMBR (P1 non-coded) | +2.6, p = 0.0031; vs CLMBR+shufECG 0.056 | same |
| CLMBR P1 \|Δ\| | 0.258 → 0.157, p = 0.0019; cluster 0.017; bs(33) 0.595 | same |
| CLMBR new-15 P1 non-coded | +4.4, p = 0.063 | same |
| S10 (two-sided, as coded) | % < 0.1 60.4 → 64.0, p = 0.017; \|Δ\| p = 0.012, vs shufECG 0.956; bs 0.0011 (5,000 draws in S10: 0.002) | same; **consistency 10 → 12** (doc 11 → 13) |

**Sign-flip exactness.** `v17_confirm.signflip_1s` enumerates all 2^k sign vectors by meet-in-the-middle (2^16 × 2^17 for k = 33). The own implementation (different code) agrees to machine precision, and Monte Carlo agrees within MC error. S10 uses `v13_summarize.sign_flip`: two-sided, exact for k ≤ 20. S10 does not state that its p values are two-sided; add this.

## 2. Pre-registration integrity (commit time vs file birth time)

| step | time (09-27 unless noted) | precedes |
|---|---|---|
| S10 results.csv / summary | 09:28 / 09:29 | S10 is post hoc (PI request): OK |
| V17 plan `0e66e3c` | 09:43:57 | everything v1.7 |
| rule `68a13a5` (rule file saved 09:51:22) | 09:51:44 | existing-18 subset table 09:53:00 (commit `20f9112` 09:53:46) |
| v1.7 count-only screen | 09:56–10:00 | **before** registration `b0c82e9` 10:04:33 (minor; pooled counts only, no arm column) |
| builds (`--blind`) | 10:07–11:15 (`52cfb8d`) | rating |
| rating `f66e7a0` | 11:19:13 | results: first verify 11:25:10, all 11:26:13, commit `a9ee8aa` 11:30 |
| patterns / category | 11:54 / 19:38 | post hoc, labelled exploratory |
| ACC abstract `89568ad` | 22:43 | **before** the prespecified AF test; never updated after it |
| S11 run | 23:15 | post hoc, labelled |
| V18 plans `760981a` | 23:23:53 | all v1.8 |
| CLMBR leakage doc saved 23:34:08; run launched 23:34:57; commit `3bec2b8` 23:35:08; first result file 23:36:52 | | no result existed before the commit (the log holds timings only) |
| AF specs `6221162` | 23:38:19 | screen 23:38:47–23:41:02; selection registry `91cc8a3` 23:42:36; build `c6724bd` 09-28 00:07 |
| AF rating `79ffb98` | 09-28 00:09:29 | AF run directory created 00:12:36; results 00:12:42; commit 00:15:45 |

**Plan compliance (code vs text).**
- **v1.7.** P1/P2, arms, 1:1 caliper 0.2, one-sided exact sign-flip, placebos, clusters, LOO, halves, sets (i)–(iii), and secondary endpoints all match plan section C. The v1.6 18 rows reproduce S1/S10 exactly.
- **S11.** Only `P2DX` is changed.
- **v1.8 A.** It imports `v17_confirm` unchanged. The co-primary shuffle pool is "33 + new" as written. The rating preceded the analysis, and all built trials were analysed.
- **v1.8 B.**
  - Arms, PSs and panels match the plan, with non-coded physiology primary.
  - The plan says the tests are "the same as v1.7" (one-sided). CLMBR vs ECG was made two-sided, which is conservative but unlogged.
  - The shuffle pool is 33 (v1.7 used within-set permutation). For all-33 the two are identical.

**Blinding.**
- The attestations list the files read. The rater saw file *names* of CLMBR results and count-only screens, but no HR/SMD.
- Existing ratings, clusters and the rule text are byte-identical across `68a13a5` → `f66e7a0` → `79ffb98` (only additions).
- No result-like file exists in `claude-v17-trials`, `claude-v18-trials`, `claude-v18-covars*` or `claude-v18-s5-nco` (logs, READY flags, parquet covariates, pooled NCO counts only).
- Screens report pooled events only.
- Rater independence (same agent family) cannot be verified beyond the attestation. It is plausible.

## 3. Benchmarks
Checked against the PubMed abstracts (E-utilities):

| trial | estimate (CI) |
|---|---|
| VALIANT | HR 1.00 (97.5% CI 0.90–1.11) |
| PROTECT AF | RR 0.62 (95% CrI 0.35–1.25) |
| ACTIVE W | RR 1.44 (1.18–1.76) |
| LODESTAR | 1.06 (0.86–1.30) |
| DECLARE | CV death/HHF 0.83 (0.73–0.95) vs MACE 0.93 (0.84–1.03) |
| FRAIL-AF | 1.69 (1.23–2.32) |
| RAFT-AF | 0.71 (0.49–1.03) |
| LAAOS III | 0.67 (0.53–0.85) |
| AF-CHF | 1.06 (0.86–1.30) |
| INSIGHT | 1.10 (0.91–1.34) |
| AFFIRM | 1.15 (0.99–1.34) |
| PRECISION | ITT 0.93 (0.76–1.13) |
| AMPLIFY | RR 0.84 (0.60–1.18) |

LEADER, SUSTAIN-6, REWIND, CANVAS, TECOS, CARMELINA and PROVE IT match the registered values. SE conversions were checked for RAFT-AF (0.190), ACTIVE W (0.102), FRAIL-AF (0.162) and LAAOS III (0.121).

## 4. Design spot-check
- **DECLARE.** Dapagliflozin vs DPP-4i, T2D, eGFR ≥ 60, CV death or HF hospitalisation, 50 months. This matches the co-primary.
- **LODESTAR.** Rosuvastatin vs atorvastatin in CAD, other statins excluded for 365 d, 36 months. Revascularisation is omitted from the composite (documented).
- **ACTIVE W.** Clopidogrel vs warfarin initiators, AF, age ≥ 55 with a CHADS risk code, no DOAC in 365 d, recent ACS/stent excluded, CV death/stroke/SE/MI, 15 months. Aspirin cannot be identified. The comparator arm is the warfarin arm shared with RE-LY/ARISTOTLE/ROCKET-AF (78% of ACTIVE W persons are in the ARISTOTLE cohort).
- **LAAOS III.** Open CABG/valve surgery ± same-day LAA occlusion code, washout on arm 1, ischaemic stroke/SE, 46 months. Coding of occlusion is likely incomplete, which misclassifies occlusion as none.
- **PROTECT AF.** Sequential LAAO vs continued warfarin, 18 months (the RCT had 1,065 patient-years). Real-world LAAO is channelled to OAC-unsuitable patients.

The near-duplicate rule was applied identically in v1.7 (against the v1.6 18; rule 4 was added after the screen, as disclosed) and v1.8 (against every cohort). The 50–80% cases were flagged, not excluded.

## 5. CLMBR
- **Leakage.** Checked independently by reading the MEDS parquet files:
  - 0 events at or after index in all 33 + 5 trials;
  - max offset −1 min;
  - vocab-accepted exposure tokens: ARISTOTLE 6.6%, ROCKET-AF 6.1% and AMPLIFY 3.2% (roster-level, other arm); switch designs 2.4–2.9% own arm; 0% in 27 trials.

  This agrees with `CLMBR_LEAKAGE.md`. One residual cannot be tested from counts: pre-index visit tokens of an index admission that began before index day. They are baseline, but correlated with in-hospital initiation.
- **Decision to proceed.** The written rule is "absent **or documented**" (V18_PLANS Plan B). The documentation, plus the sensitivity sets S_noown / S_noexpo fixed before results, satisfies it, and the results hold in both sets. This was not a stop-rule violation.
- **Retention.**
  - Pairs / smaller arm: base 0.883, CLMBR 0.821, ECG 0.878.
  - The gain is larger where CLMBR drops more pairs (Spearman 0.26, p = 0.15; +10.8 vs +6.1 pp by median split).
  - On the common-anchor population (identical anchors; 77% of anchors), the CLMBR P1 non-coded gain is +7.6 pp (26/33, p = 6e-5, cluster p = 0.0007), vs +8.4 on its own matched set.
  - For ECG it is +5.1 vs +6.1.

  Trimming is a minor contributor. Report retention next to the CLMBR balance claim.

## 6. Statistics notes
- The one-sided usage matches the plans. Two-sided was used in S10 (post hoc) and for CLMBR vs ECG.
- **AF-7 benchmark shuffle.** Three pool definitions give 0.096 / 0.032 / 0.063. The 33-pool value in `V17_PATTERNS` is the most favourable. v1.7's own confirmatory construction (within-set) was not used there. Report all three, or the within-set value.
- **Floors.** Many "p = 0.125 / 0.25" cluster results are the smallest attainable p, not evidence of absence. AF-5 with 5 trials has a floor of 0.031, so the confirmation could only succeed with 5/5 closer.

## 7. Claim status and wording fixes

| claim (source) | status | issue |
|---|---|---|
| New-15 balance P1 (V17_CONFIRMATION_RESULTS) | prespecified confirmatory | correctly described as "confirmed at trial-level test, not robust" |
| New-15 \|Δ\| (same) | prespecified confirmatory | correctly "not confirmed" |
| All-33 balance and \|Δ\| | prespecified secondary set (ii), not out-of-sample | fine in doc; the abstract does not say that 18 of the 33 are the discovery trials |
| Blinded subsets (V17_BLINDED_SUBSET_EXISTING18) | prespecified rule, in-sample data | labelled |
| Where ECG helps, domains, trial size (V17_PATTERNS) | post hoc | labelled "hypothesis-generating". "The blinded, pre-specified 'high ECG relevance' class shows significantly larger gap reduction": the *class* was prespecified, the *test* was not; its shuffled-RCT p = 0.43 (generic). |
| AF-7 emulation "passes all four checks" (V17_PATTERNS) | post hoc | **now falsified by the prespecified v1.8 test**; the shuffle pass depends on the pool (§6) |
| S10 balance / RCT agreement | post hoc | labelled; fix the consistency count; state two-sided |
| S11 P5 | post hoc | labelled; "Monte Carlo sign-flip" → "exact sign-flip"; the "obesity removes the ECG gain / voltage encodes habitus" explanation is speculation |
| CLMBR results | prespecified-exploratory (Plan B) | the bottom line "the one trial-specific signal … AF … belongs to the ECG" was written before the AF test and must be updated |
| AF confirmation | prespecified confirmatory | correct verdict. Fix: "The one robust signal in AF-12 is held-out balance … beyond shufECG and noise32": on the 58-panel, ECG vs shufECG p = 0.11 and cluster p = 0.50, and AF-12 contains the 7 discovery trials |
| ACC abstract: balance 53 → 59, 25/33 | in-sample secondary | numbers correct; not labelled |
| ACC: "replicated in the 15 prespecified trials (p = 0.03)" | confirmatory | "replicated" overstates it: one-sided, cluster p 0.078, LOO 0.064, null with the P2 PS, and no multiplicity survival (BH q 0.16) |
| ACC: \|Δ\| 0.26 → 0.21 (p = 0.004) | in-sample secondary | omits that the confirmation failed (p = 0.074) and that the benchmark shuffle fails (0.37): generic shrinkage |
| ACC: "Gains were largest in AF … all 7 … 0.44 → 0.32 … 2 → 5" | post hoc | **misrepresents status and is contradicted by the prespecified confirmation (3/5, p = 0.19; worse with P5)** |
| ACC conclusion: "absent from structured data … improving … agreement with RCTs, particularly in AF" | — | unsupported: CLMBR (structured codes) matches the ECG, and no trial-specific agreement survives |
| ACC title "Improves Confounding Control" | — | overstates: held-out balance is a surrogate, and emulation agreement did not improve |

### Recommended ACC abstract

This replacement is 1,298 characters excluding spaces, counted the same way as the current draft, which counts 1,300.

> **Title:** AI-ECG Embeddings Modestly Improve Covariate Balance but Not Trial-Specific Agreement in Emulations of 38 Cardiovascular Trials
>
> **Background:** Trial emulation with real-world data is limited by unmeasured confounding. We tested whether AI-ECG embeddings capturing latent cardiac phenotypes improve confounding control.
>
> **Methods:** Using Yale New Haven Health System records, we emulated 38 cardiovascular randomized trials (RCTs) with new-user, active-comparator designs; 20 (15 general, 5 atrial fibrillation [AF]) were analyzed under prespecified confirmation protocols. Patients were matched 1:1 on a demographic propensity score with or without an ECG foundation-model embedding, or a permuted-ECG placebo. Balance was assessed on 58 held-out clinical, laboratory and echocardiographic variables; emulated hazard ratios (HR) were compared with RCT results.
>
> **Results:** In 33 trials, ECG embeddings increased the share of held-out covariates with standardized difference <0.1 from 53% to 59% (25/33 trials, p<0.001); the placebo did not. In the 15 confirmation trials the gain was 52% to 58% (p=0.03), but not robust to comparator clustering or a richer score. The mean absolute log-HR difference from RCTs fell from 0.26 to 0.21 (p=0.004), but not in the confirmation trials (p=0.07), and equally with shuffled RCT benchmarks (generic shrinkage). An exploratory AF signal did not replicate in 5 new AF trials (3/5 closer, p=0.19). A structured-EHR embedding matched the ECG.
>
> **Conclusion:** AI-ECG embeddings modestly improve balance on held-out variables when structured covariates are sparse but did not improve trial-specific agreement with RCTs.

**README edits.**
- Add the AF-5 source (`docs/v18/AF_CONFIRMATION_RESULTS.md`) and the CLMBR source (`docs/v18/CLMBR_RESULTS.md`).
- Change caveat 2 to "the AF category is post hoc and failed prespecified confirmation".
- Add "18 of the 33 are the hypothesis-generating v1.6 trials".

**Other exact fixes.**
- `S10_DEMO6.md`:
  - "Consistency with the RCT: 11/18 … → 13/18" → "10/18 → 12/18";
  - add "p values two-sided".
- `S11_P5.md`: "Monte Carlo sign-flip for 33 trials" → "exact sign-flip (full enumeration)".
- `V17_PATTERNS.md`, AF row:
  - add "shuffled-RCT p = 0.096 within the 7 trials, 0.063 with 38 RCTs";
  - add at the top "The AF pattern did not replicate in the prespecified v1.8 confirmation (docs/v18/AF_CONFIRMATION_RESULTS.md)";
  - commit the code that produced `per_trial_patterns.csv` / `emulation_by_category.csv`.
- `CLMBR_RESULTS.md`:
  - bottom line → "The AF ECG signal (exploratory; shuffle p 0.03–0.10 depending on pool) failed prespecified confirmation in 5 new AF trials";
  - add "CLMBR matched 93% of base pairs; on the common matched population its non-coded gain is +7.6 pp";
  - note that CLMBR vs ECG tests are two-sided (a deviation from the plan's one-sided tests, conservative).
- `AF_CONFIRMATION_RESULTS.md`: "improves 58-panel and covars2b balance under P1 beyond shufECG and noise32" → "improves covars2b balance beyond both placebos and 58-panel balance beyond noise32 (vs shufECG p = 0.11); AF-12 includes the 7 discovery trials and the cluster p is at its floor".
- `V17_CONFIRMATION_RESULTS.md` / `candidates.md`:
  - "AFFIRM contains most EAST-AFNET 4 records" → "48% of AFFIRM persons (25% with the same index date) are in the EAST-AFNET 4 cohort";
  - note that the v1.7 count-only screen preceded the registration commit.

## 8. Global multiplicity (`global_v17_v18.csv`)

**Family.** 1,314 ECG/CLMBR-vs-base and key-contrast tests:
- v1.7 summary: 182;
- S11: 12;
- v1.8 AF: 98;
- CLMBR all-33 key contrasts: 144;
- CLMBR per category: 864;
- v1.7 category: 14.

**Prespecified primaries (5).**

| test | p |
|---|---|
| new-15 P1 balance | 0.033 |
| new-15 P1 \|Δ\| | 0.074 |
| new-15 P2 balance | 0.17 |
| new-15 P2 \|Δ\| | 0.52 |
| AF-5 P1 \|Δ\| | 0.19 (co-primary shuffle 0.28) |

None passes Bonferroni (0.01) or BH (min q 0.16).

**Exploratory.**
- **Balance:** 166/798 survive BH within domain.
- **Emulation:** 10/516 survive: all-33 z² or \|Δ\| for ECG/CLMBR, every one with shuffle p ≥ 0.20. The all-33 ECG \|Δ\| itself has q = 0.072 and does not survive.
- **Benchmark-specific:** 0 cells (min shuffle q 0.13), consistent with round 3 (0/143).
- **Confirmation-set balance cells surviving global BH:** new-15 P1 covars2b panel (q = 0.009), and S_ecg P1 covars2b and C-statistic (q = 0.038).

## 9. Privacy
- The permissions fix is described in the verdict table.
- The audit outputs are 600 and the directory is 700.
- The committed audit scripts contain no data.
- This document contains trial counts, percentages and p values only.

## State of the evidence
Adding a 32-PC AI-ECG embedding to a thin (demographics-only) propensity score consistently improves balance on held-out clinical, laboratory and echocardiographic covariates. The gain is about +6 points in % |SMD| < 0.1, beats permuted and noise placebos, and is barely changed on a common matched population. It replicated at the prespecified trial-level test in 15 unseen trials (p = 0.033), though not robustly: it fails comparator clustering and a richer 6-diagnosis PS on the primary panel, and does not survive multiplicity, while the secondary covars2b panel is robust. It did not appear in the 5 new AF trials, and it shrinks as the PS gets richer. A code-based EHR foundation model (CLMBR-T) gives an equal or larger gain, and ECG adds only a small, placebo-borderline increment to it. There is no confirmed evidence that the ECG moves emulated HRs toward trial-specific RCT results. Every |Δlog HR| improvement (ECG or CLMBR, any PS) is matched by shuffled RCT benchmarks, i.e. generic shrinkage toward typical effects. The only apparently trial-specific signal, AF with a demographics PS, was post hoc, depends on the benchmark pool (p 0.03–0.10), and failed its prespecified confirmation (3/5 trials closer, p = 0.19; worse with P5). Defensible claim: "modest, placebo-specific improvement in held-out balance when structured covariates are sparse; no demonstrated improvement in RCT agreement". The current ACC draft goes beyond that and should be replaced as above.
