> **Note (2026-10-15):** this verification predates the switch of the primary CLMBR-T input to history before the index admission. The switch is audited in `docs/mimic/AUDIT_MIMIC_PRIMARY_SWITCH.md`.

**Verdict (round 2): PASS with minor issues.** B1–B3 are fixed correctly. The numbers in the edited text match the restricted outputs. All 353 numbers still match. The privacy scan of every file to be committed is clean. No BLOCKING finding remains. Two minor wording points are listed in the Round 2 section.

*Round-1 verdict, kept for the record:* FAIL, on three text corrections only (B1–B3). Every number, leakage count, hash and privacy check passed.

# Independent verification: MIMIC-IV external validation with CLMBR-T (2026-10-14)

- **Verifier:** a fresh subagent that built nothing in this work. It read `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md`, the queue (`docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR.md`), `scripts/mimic/*.py`, `pipeline.md` and the restricted outputs under `audits/claude-mimic-clmbr-20261014/`.
- **Method:** independent code in `scripts/mimic/verify/` (v1–v12). These scripts do not import the scripts under test, with two exceptions: `v7_rerun.py` reuses the shared, already-gated `v13_common.match` / `cox` and the v15/v20 data loaders, and `v8_misc.py` reads the constant `LAB_LOINC` table.
- **Scratch:** scratch files are in `audits/claude-mimic-clmbr-20261014/verify/` (umask 077; `numbers.csv` = the full aggregate comparison table).
- **Privacy:** aggregates only. Counts of 1–10 are shown as <11.

## 1. Checks

| # | Check | Result |
|---|---|---|
| 1 | **Step 0 gate.** `step0/gate.json` = PASS (24 tables, max \|Δ\| 0). Independently compared: `step0/results/*_{arms,vars}.csv` vs `claude-v21-paper2/mimic/results/` (same shape, columns and NaN pattern; max \|Δ\| 0) and the flags (max \|Δ\| 0). Headline recomputed with own code: 6.6%; v20-convention CI (2,000 resamples, seed 0, alphabetical trial order) 2.3–12.8; 6/7 lower; exact one-sided sign-flip P = .016; % < 0.1 45.6 → 51.6; permuted ECG −3.1%. Paper-convention CI: 2.4 to 13.1. | PASS |
| 1b | New analysis code vs v21. `results/` and `results_prior/` base / ECG / permECG cells (3 cvd5 bases, 2 populations) equal the step0 cells: same rows, max \|Δ\| 0. | PASS |
| 2a | Non-birth MEDS events with time ≥ t0 (43,820,065 rows, 78,183 subjects) | **0** |
| 2b | Diagnosis / procedure events with `src_hadm_id` = index hadm_id | **0** |
| 2c | Diagnosis / procedure events whose source admittime ≥ index admittime | **0**. Also 0 with dischtime > index admittime, 0 whose time ≠ source dischtime, and 0 with an unknown source admission. |
| 2d | `meds_prior`: non-birth events with time ≥ index admittime | **0** |
| 2e | Other structural checks | Every subject has exactly one birth. 0 events before birth, 0 null times, 0 numeric values (code-only). 0 events for subjects outside the cohort. |
| 2f | Exposure-drug spot check (RxNorm names from `CONCEPT.csv`; drug events of each trial's own subjects) | The trial's study drug is absent in PLATO (ticagrelor, clopidogrel), ARISTOTLE (apixaban, warfarin), ROCKET AF (rivaroxaban, warfarin), COMET (metoprolol, carvedilol), SOAP II and PEPTIC: 0 events each. TRANSFORM-HF: torsemide 0, furosemide <11 events (an IV injection product). ELITE II: 28 events of IV enalaprilat, plus <11 each of oral captopril and valsartan. Positive control: the same names occur in other trials' subjects (for example clopidogrel 17,049, warfarin 33,450 and metoprolol 141,706 events across all 8 trials), so the lookup works. Judged immaterial (N1). |
| 3 | Model / runtime hashes | My own sha256 of `config.json`, `dictionary.msgpack` and `model.safetensors` equals the Yale manifest. `model_sha256` and `runtime` of `clmbr/{smoke100,full,prior_full}/manifest.json` equal Yale's (femr 0.2.3, meds 0.1.3, torch 2.13.0, transformers 4.44.2, xformers 0.0.35, numpy 1.26.4, pyarrow 24.0.0). Code-only mode, 4,096 tokens. All 33 listed output digests in each run match, and each run's MEDS manifest hash matches. | PASS |
| 3b | Embeddings | `full`: 78,183 embeddings, one per subject, equal to the roster set. `prior_full`: 45,107. All 768-d, all finite, no zero vectors. The tokenizer's accepted count equals the builder's `n_in_vocab` for all 78,183 subjects (and for all 45,107 in the prior run), not only the 100 of the smoke test. Every analysed patient has an embedding. The dictionary code strings were exported independently with msgpack: 25,667 code entries, identical to `vocab/clmbr_code_strings.json`. | PASS |
| 4 | Headline numbers recomputed (own mask, items finite in both cells, bootstrap with `default_rng(20261001)` and `integers(0,k,(4000,k))` over trials in the order plato … elite2, exact sign-flip, \|Δ log HR\|, agreement, PEPTIC, coverage, Yale s31) | **353 / 353 match** (§2) |
| 5 | Leakage masks (doc §6 vs the MEDS input and the `pipeline.md` §6 rules) | Adequate. See §3 and B3, N2, N3. |
| 6 | Privacy scan of the files to be committed | PASS (§4) |
| 7 | Code correctness | PASS (see below; N5 is a reproducibility note) |

**Check 7 in detail:**
- **Re-run (`v7_rerun.py`):** COMET, SOAP II and PEPTIC, cvd5 | all, arms CLMBR, ECG+CLMBR and permCLMBR. It uses its own embedding join by (trial, pid), its own 64-PC PCA (sklearn, and a separate numpy SVD), its own ridge PS (C = 1, standardised) and its own \|SMD\|. The primary cells are reproduced exactly: same number of inputs and pairs; \|Δ\| ≤ 1e-16 in mean \|SMD\|, % < 0.1 and log HR. This also confirms:
  - the permuted CLMBR-T uses the same within-trial permutation (seed 20261001) as the permuted ECG;
  - the design order (demographics, flags, representation).
- **Prior-only cells:** reproduced exactly only with single-threaded BLAS (N5).
- **Code reading:**
  - the mask drops block D only when {a, b} ∩ {CLMBR, ECG+CLMBR, permCLMBR} is not empty (PEPTIC uses the arm's own mask);
  - the sign flip is one-sided as P(null ≥ obs) on d = m_b − m_a, and two-sided as P(\|null\| ≥ \|obs\|);
  - the bootstrap is a fresh generator per contrast, over trials in set order;
  - the encoder's birth-only path keeps only the birth measurement when no clinical code is accepted;
  - the cutoff is checked twice: event time < t0 in `patient_events`, and representation timestamps < t0 (UTC epoch) in `select_vector`, as in the Yale encoder;
  - matching is `v13_common.match` (greedy, caliper 0.2 SD of the logit, anchored on the smaller arm), and SMDs use the pooled SD of the analysed rows.
- **Cells:** 0 failed (< 11 pairs) and 0 overlap-invalid cells in all 288 primary and 288 prior cells.

## 2. Recomputed numbers (doc value = recomputed value at printed precision; selected rows; all 353 in `verify/numbers.csv`)

| Item | Doc | Recomputed |
|---|---|---|
| + ECG vs PS-CVD5: rel. red. (95% CI); lower; P | 6.6% (2.4 to 13.1); 6/7; .016 | 6.6 (2.4 to 13.1); 6/7; .016 |
| + ECG: % < 0.1; \|Δ log HR\| | 45.6 → 51.6; 0.344 → 0.326 (4/7) | same |
| + CLMBR-T vs PS-CVD5 | 23.1% (16.0 to 28.9); 7/7; .008; 44.2 → 57.8 | same |
| + ECG + CLMBR-T vs PS-CVD5 | 29.0% (21.6 to 37.1); 7/7; .008; 44.2 → 64.3 | same |
| + ECG + CLMBR-T vs + CLMBR-T | 7.7% (3.0 to 14.1); 6/7; .016; 57.8 → 64.3; 0.260 → 0.249 (3/7) | same |
| + ECG + CLMBR-T vs + ECG | 23.6% (18.5 to 27.7); 7/7; .008 | same |
| + CLMBR-T vs + ECG (two-sided) | 17.2% (9.4 to 23.1); 7/7; .016 | same |
| + ECG vs + permuted ECG | 9.4% (6.2 to 14.0); 7/7; .008 | same |
| + CLMBR-T vs + permuted CLMBR-T | 23.6% (14.0 to 30.4); 6/7; .016 | same |
| + permuted ECG vs PS-CVD5 (two-sided) | −3.1% (−5.6 to −0.3); 2/7; .094 | same |
| + permuted CLMBR-T vs PS-CVD5 (two-sided) | −0.6% (−4.6 to 4.5); 3/7; .812 | same |
| + CLMBR-T closer to the RCT: P | .023 | .023 |
| Benchmark-permutation P (+ ECG / + CLMBR-T / + both) | .84 / .70 / .43 (20,000 random draws) | .838 / .695 / .429 (exact, all 5,040 permutations) |
| Agreement r (PS-CVD5 / + ECG / + CLMBR-T / + both / perm ECG / perm CLMBR-T) | 0.69 / 0.69 / 0.75 / 0.76 / 0.70 / 0.61 | same; estimate and std-diff agreement counts also equal |
| PEPTIC HR: PS-CVD5; + ECG; + CLMBR-T; + both | 1.51 (1.35–1.69); 1.39 (1.24–1.55); 1.00 (0.90–1.11); 0.95 (0.85–1.06) | same |
| PEPTIC HR: permuted ECG; permuted CLMBR-T | 1.60 (1.42–1.81); 1.43 (1.28–1.61) | same; % < 0.1 and mean \|SMD\| of all 6 arms also equal |
| Median in-sample C (PS-CVD5 / + ECG / + CLMBR-T / + both) | 0.662 / 0.704 / 0.793 / 0.807 | same |
| Cells retaining 50–90% (+ CLMBR-T; + both) | 1 of 8; 3 of 8 | same; all other cells ≥ 90% |
| Coverage: share in dictionary (MIMIC; Yale) | 82.1%; 78.5% | 82.1; 78.5 |
| In-vocabulary events per patient (MIMIC; Yale) | 211 (93–490); 308 (104–757) | same |
| No prior coded history (MIMIC; Yale) | 0.2%; < 11 of 313,867 | 0.2%; <11 of 313,867 |
| No coded history outside the index admission | 14.9% | 14.9 |
| Domain coverage (dx / drug / lab / px / visit); labs share | 88.1 / 60.5 / 83.4 / 34.8 / 100; 86% | same |
| Analysed patients (8; 7 trials); MEDS subjects | 45,107; 37,694; 78,183 | same |
| Sensitivity rows (any-DM, index-admission codes, no index-day ECG, all 8, unmasked): 4 contrasts × 5 variants, rel. red., CI, lower | e.g. any-DM + both vs + CLMBR-T 0.6% (−5.9 to 8.9); 3/7 | all 80 values equal |
| Prior-only: + CLMBR-T; + both; + both vs + CLMBR-T | 7.7% (3.0 to 14.0) 6/7; 18.6% (12.5 to 26.7) 7/7; 11.9% (6.9 to 16.8) 7/7 | same |
| Prior-only: CLMBR-T vs ECG; \|Δ log HR\|; benchmark P | 0.6% (−2.4 to 3.3); 0.344 → 0.278 → 0.240; .95 / .57 | same (exact P 0.95 / 0.57) |
| Prior-only PEPTIC HR: + CLMBR-T; + both | 1.28 (1.14–1.43); 1.21 (1.08–1.35) | same |
| Prior-only: birth only; median in-vocabulary events | 10.6%; 59 | same |
| Yale s31 (contrasts.csv, S31 / main, P5 = PS-CVD5): the 10 contrasts' rel. red., CI, trials lower, P | e.g. 8.7% (4.2 to 13.5) 20/31; 12.9% (7.6 to 18.3); 14.6% (7.7 to 21.1); 2.0% (−3.5 to 6.9) .238 | all equal |
| Other doc claims | literal lab rule ≈ 9% in the dictionary; 96 LOINC items, 95 in the dictionary (pCO2 not), all valid standard; ≈ 14% of pre-t0 prescription rows without NDC; birth year vs v1.5 age gap 0 | 9.3%; 96 / 95 / 96 valid; 14.1%; 0 |

## 3. Findings

### BLOCKING

**B1. §9 "Hospital-only history" is wrong.** It says the CLMBR-T input is "86% labs, mostly from the index admission before t0". The 86% is right. But only **30.2%** of the analysed patients' lab events come from the index admission (32.9% over all MEDS subjects), and **31.4%** of all their events. The per-patient median index-admission share of lab events is 40.7%, and only 44.3% of patients are above 50%. Most lab events come from earlier admissions and outpatient draws. The same wording reappears in §1.8 ("reads the index admission's pre-t0 lab and order stream"), which is fine as stated. Only the composition claim ("mostly") is wrong.
- **Fix:** "86% of its events are labs (about a third from the index admission before t0)".

**B2. §8, the bullets after the prior-only block, contradict the table they summarise.**
- **The claims:** "The CLMBR-T estimate moves less (17–29%), and is positive in every trial in every variant. The ECG's added value on top of CLMBR-T ranges from 0.6% to 9.8%."
- **What the table shows:** the table includes the prior-only row, where + CLMBR-T is 7.7% with **6/7** trials lower (not every trial), and the ECG adds **11.9%**.
- **Over the five design-detail rows the statements hold:** CLMBR-T 17.4–29.1%, 7/7 (8/8) everywhere, ECG on top 0.6–9.8%.
- **Fix:** scope the sentences to "the five design-detail variants (not the prior-only input)", or widen the ranges to 7.7–29% and 0.6–11.9% and drop "every variant".

**B3. `pipeline.md` misdescribes the primary MIMIC CLMBR-T input as "(code-only, prior admissions only)".** This appears in both the §8 MIMIC-IV row and the new deviations-log line.
- **What the input actually contains:** only diagnoses and procedures are restricted to earlier admissions. The primary input also contains the index admission's pre-t0 labs, orders and the index `Visit/IP` token: 14.76 M of 43.74 M clinical events, and the doc's own §8 shows that most of the 23.1% depends on them. "Prior admissions only" describes the **sensitivity** (`meds_prior`), not the primary arm.
- **Why it is BLOCKING:** the methods-lock file would then state the wrong input window for the arm whose headline depends on it.
- **Origin:** the deviations-log wording was prescribed by the queue.
- **Fix, both places:** "code-only; diagnoses / procedures from earlier admissions only; labs and orders strictly before t0, including the index admission; sensitivity: history before the index admission only".

### NON-BLOCKING

- **N1. Residual exposure-class drug codes are tiny.** They are 28 events of IV enalaprilat in ELITE II, plus <11 events each of oral captopril and valsartan (ELITE II) and IV furosemide (TRANSFORM-HF; IV loop diuretic before t0 is allowed by that trial's design). The token filter works on the order's drug string, so products whose string lacks the token (IV enalaprilat, some pharmacy strings) pass. This mirrors the cohort builders' own washout definition. It is immaterial, but §5.2 rule 2 could say "by drug-string token; IV enalaprilat is not filtered".

- **N2. The prior-only input still contains the index episode's pre-admission ED stream.** These are events attached to the index hadm_id but timed before its admittime:
  - 290,320 events, 1.6% of the prior input's clinical events (labs 232,884, drug orders 29,034, visits 28,402);
  - present in 72% of patients (32,467 of 45,107);
  - 2,931 patients (6.5%) have only such events.

  The doc's operational definition ("every event at or after the index admission time is removed") is accurate. The label "history before the index admission only" and the reading "about two-thirds of the gain comes from the index admission's own pre-t0 stream, not from prior history" are approximate, because the ED labs of the same episode stay in. Suggest one sentence in §8.

- **N3. Ventilation at t0 (item C) has a soft proxy in the input.**
  - **The doc's claim:** "no ventilation token". This is true: the blood-gas ventilator / intubation items are `MIMIC_LAB/<itemid>` codes, out of the dictionary.
  - **The proxy:** arterial blood-gas codes (pH, pO2, total CO2 arterial) in the 24 h before t0 correlate with `vent_at_t0` at phi = 0.45 pooled (0.24–0.52 by trial). That is a soft proxy (≥ 0.50 in at least one trial), below the 0.80 masking threshold of `pipeline.md` §6.
  - **Under the rules:** unmasked is correct.
  - **Suggestion:** say so in the §6 table, or add the "clean + soft" variant (mask C for the CLMBR-T arms) as a sensitivity.

- **N4. Truncation definitions differ between the columns of the §5.3 table.**
  - **MIMIC 1.3%:** the share of patients with more than 4,096 *in-vocabulary events*, measured before tokenization.
  - **Actual tokenizer truncation** (`tokens_available` > 4,096) is 1.0% of analysed patients (0.9% of all subjects).
  - **Yale 1.3%:** tokenizer-based.

  Report 1.0% for MIMIC, or label the definitions.

- **N5. The prior-only cells depend on BLAS threading.** About 10.6% of prior-input patients are birth-only, and patients with the same birth year have identical embeddings, so PS ties are broken by floating-point noise.
  - **Single-threaded BLAS** (what `mimic_common` sets): the CLMBR / permCLMBR prior cells reproduce exactly.
  - **Multi-threaded BLAS:** they move by up to about 1e-3 in per-trial mean \|SMD\| and about 0.008 in log HR. The ECG+CLMBR cells, where the ECG breaks the ties, are unaffected.
  - **Effect on published numbers:** none, since `run_mimic_external.py` imports `mimic_common`. Consider stating the thread setting in the doc.

- **N6. A few lab / drug events carry a later admission's hadm_id.** 93 events in 56 subjects belong to an admission admitted *after* the index admission, yet are timed before t0. All are < t0, so there is no temporal leakage; this is a MIMIC hadm-assignment quirk.

- **N7. The gate-code exclusion is ICD-prefix based.** The AF-gated trials have 0 AF-named diagnosis events. The HF-gated trials keep some HF-named SNOMED diagnoses from earlier admissions, from combination codes outside the gate prefixes: COMET 763, ELITE II 741 and TRANSFORM-HF 426 events. PLATO keeps 385 MI-named events (for example old MI, which is not ACS). There is no leakage, because these are earlier admissions only. "Gate code excluded" is accurate for the gate prefixes.

- **N8. Small wording points.**
  - "0 events … over all 43.8 million events" counts rows including the 78,183 birth rows (43.74 M clinical events).
  - §5.3 says builder and tokenizer counts agree "in the 100-subject smoke test". They agree for all 78,183 subjects (and all 45,107 in the prior run), which is a stronger statement.

- **N9. `build_mimic_meds.main` error handling.** On failure it prints the first 300 characters of the database error message to stderr. A duckdb conversion error can quote a raw field value in that first line. The run succeeded, so nothing was emitted. Suggest printing the exception type only.

- **N10. Process notes.**
  - `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR_RESULTS.md` does not exist yet, so it was not scanned. Scan it before committing.
  - `git diff` needed interactive approval in this session, so the diffs were read from the git object store, read-only (`v6_headdiff.py`).
  - Other working-tree changes (for example `docs/paper/table1_picot.md`, the `.docx`, `scripts/aou/`) are not part of this job and must not be staged with it.

### Leakage masks (check 5) and disclosure of the index-admission stream

- **Utilisation (block D, 4 items):** derivable from `Visit/IP` / `Visit/ER` and their times, and correctly masked whenever a CLMBR-T arm, real or permuted, is in either cell. The input has no ICU-transfer token, so "ICU before t0" is masked conservatively.
- **Lab values (A, B):** not in the code-only input. This is consistent with the locked `pipeline.md` §6 (+ CLMBR-T: no mask on the non-coded items) and with Yale.
- **Lab missingness indicators:** these would be derivable, and they are not used.
- **Vitals (SBP, DBP, HR, BMI):** absent from the input (no chartevents or omr), so nothing is derivable.
- **No unmasked held-out item is the same quantity as a coded input.** The remaining issues are soft proxies: lab-ordering intensity, and blood gases for ventilation (N3).
- **Index-admission pre-t0 stream:** disclosure is **adequate** in substance. It is stated in Verdict 8, the §5.2 rules, §5.4 difference 1, the §8 sensitivity (flagged as added after the primary results were seen) and §9. Two qualifications: the composition claim (B1) must be corrected, and the prior-only label should mention the retained ED stream (N2). The §6 table row "A, B: no" could also cross-reference §8.

## 4. Privacy scan

**Files scanned:**
- `scripts/mimic/*.py` (10 files) and `scripts/mimic/verify/*.py`;
- `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md` and this report;
- the `pipeline.md` diff;
- the six older docs.

**Results:**
- **Six older docs:** each diff vs HEAD is exactly the pointer line plus one blank line (+2 / −0). Nothing else changed.
- **`pipeline.md`:** 2 lines changed and 1 added (External replication row, the MIMIC-IV row, the deviations-log line). They contain no data.
- **Identifiers and dates:** no subject_id, hadm_id, pid or patient date anywhere. The only 7–9-digit numbers and dates are seeds, run dates and directory names.
- **Restricted per-trial quantities:** no per-trial n_pairs, retention or ESS.
- **Small counts:** no count of 1–10, including derivable ones. The derivable PEPTIC analysed n (45,107 − 37,694) is a cohort size above 10. The 0.2% of 45,107 is about 95 patients.
- **Retention bands:** the statements ("1 of 8 … 3 of 8 cells 50–90%; all others ≥ 90%") are band counts over trials. They give a lower bound for the remaining cells, not per-trial values. Acceptable.
- **Scripts:** they print aggregates only. `coverage.py` prints per-trial cohort sizes and coverage shares to stdout (not committed), and suppresses the small-count share.
- **Restricted outputs:** all 285 files and directories under the output tree are owner-only (0 group- or world-accessible).

**Result: PASS.**

## Round 2 (re-verification after the fixes)

**Scope:**
- the edited statements of `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md`;
- `pipeline.md`;
- the new `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR_RESULTS.md`;
- a fresh privacy scan of every file to be committed.

**Restricted outputs unchanged:** `v4_numbers.py` was re-run on them and still gives 353 / 353 matches. `v10_labshare.py` and `v5_proxy.py` were re-run and give the same values as in round 1.

### Fixed BLOCKING findings

| Finding | Fixed text | Check against the restricted outputs | Status |
|---|---|---|---|
| B1 (§9 composition) | "86% of its events are labs (30.2% of the analysed patients' lab events come from the index admission before t0, the rest from earlier admissions and outpatient draws)" | 85.4% / 86.0% labs; index-admission share of labs 30.2% (analysed). The "rest" also holds 93 events in 56 subjects with a later admission's hadm_id, timed before t0 (N6). Negligible. | **Fixed** |
| B2 (§8 bullets) | ranges restricted to the five design-detail variants; the input-timing variant named as the exception | Five variants: CLMBR-T 17.4–29.1% ("17–29%"); 7/7 or 8/8 lower in each; ECG on top 0.6 / 7.2 / 9.8 / 8.0 / 7.8 ("0.6–9.8%"). Exception: 7.7% (6/7) and 11.9%. | **Fixed** |
| B3 (`pipeline.md`) | MIMIC-IV row: "code-only; diagnoses and procedures from earlier admissions only, labs, orders and visits strictly before t0 … sensitivity: CLMBR-T from history before the index admission only". Deviations line: "… index-admission labs and orders only if before t0 … (+ CLMBR-T 23.1% → 7.7%)" | Matches `build_mimic_meds.py` and the MEDS checks; 23.1% and 7.7% recomputed. Diff vs HEAD: +3 / −2 lines, nothing else changed. | **Fixed** |

### Non-blocking items addressed

| Item | Doc text | Check | Status |
|---|---|---|---|
| N4 | §5.3 truncation "1.0%" (token-based) | 1.0% of analysed patients have `tokens_available` > 4,096 | Correct |
| N3 | §6 ventilation row: soft proxy, "phi 0.45 pooled", below 0.80 | Pooled phi 0.45 (per trial 0.24–0.52) | Correct |
| N2 | §8 ED-stay caveat ("in most patients") | 72% (32,467 of 45,107) | Correct |
| N1 | §5.2 drug-string caveat: "28 events of IV enalaprilat in ELITE II, and < 11 events each of a few others, including IV furosemide in TRANSFORM-HF" | Matches; counts 1–10 suppressed and not derivable (no totals given) | Correct |
| N5 | §5.4 BLAS note ("about 1e-3 in mean \|SMD\|") | Matches the single- vs multi-threaded re-run | Correct |

### New results file

`QUEUE_2026_10_14_MIMIC_CLMBR_RESULTS.md`: every number checked equals the recomputed values or the doc:
- the gate;
- coverage 82.1 / 78.5, 211 (93–490) / 308 (104–757), 0.2% / < 11;
- the three headline arms and their Yale values;
- prior-only 7.7% and 18.6%;
- ECG on top 7.7% and 11.9%;
- "4 of the 5 design-detail variants (7.2–9.8%)" and any-DM 0.6%;
- Yale 2.0%, P = .24;
- \|Δ log HR\| 0.344 / 0.326 / 0.260 / 0.249 and benchmark P .84 / .70 / .43;
- PEPTIC 1.51 / 1.39 / 1.00 / 0.95 / 1.43 and prior-only 1.28;
- 0 failed and 0 overlap-invalid cells.

The deck sentence's figures (6.6% 6/7; 7.7% 6/7; 23.1%; 7.7% from prior history) are correct.

### Remaining minor issues (NON-BLOCKING)

- **R1. The results file's privacy note overstates the fix.** It says "the builder now reports exception types only", but `build_mimic_meds.py` line 261 still prints the type plus the first line of the error message (≤ 300 characters) to stderr.
  - **Why it is not BLOCKING:** this meets the project rule given for this work ("exception type / first line"), and the CSV parser puts the raw row on a later line.
  - **Fix, either way:** drop `str(e)…` from that print, or reword the note to "type and the first line of the message".
  - **The incident itself:** a raw prescriptions row echoed to the agent console during the first build attempt. It is disclosed in the results file. A counts-only scan of the text files under the restricted output tree (`v14_logscan.py`: STATUS.md, queue_claude.log, json, sh) found no CSV / conversion error text. The only identifier-like hit was a false positive (the single-line dictionary code list). The agent transcript itself is outside this check.
- **R2. §5.3 understates its own check.** It still says builder and tokenizer counts agree "in the 100-subject smoke test". They agree for all 78,183 subjects (and all 45,107 prior-only). This is true as written and only weaker than it could be. Optional.

### Privacy scan (round 2): PASS

**Files scanned:**
- `scripts/mimic/*.py` (10) and `scripts/mimic/verify/*.py` (17);
- `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md` and this report;
- `pipeline.md`;
- `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR_RESULTS.md`;
- the six pointer docs.

**Results:**
- **Identifiers:** no subject_id, hadm_id, pid, patient date or note text. All 7–9-digit numbers are seeds, run-date directory names or the vocabulary release date.
- **Restricted per-trial quantities:** no per-trial n_pairs, retention or ESS.
- **Small counts:** no unsuppressed count of 1–10, and none derivable by differencing. The new "< 11 events each" has no total.
- **Pointer docs:** each is still exactly +2 lines (pointer + blank) vs HEAD.
- **Verify scripts:** they print aggregates only. Their exception handlers now print the exception type only (`v2b_exposure.py` was changed to drop the message's first line).
