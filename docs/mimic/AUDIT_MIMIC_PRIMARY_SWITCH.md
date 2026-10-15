# Independent audit: MIMIC-IV CLMBR-T primary-input switch (commit 0bf4cbe, 2026-10-15)

**Verdict: FAIL on disclosure; there are 2 BLOCKING findings, both text fixes.** All numbers are correct. All leakage rules hold.
- **Numbers:** every headline number I recomputed (56 values; 112 counting both inputs) matches the doc.
- **Cells:** the ECG / base / permuted-ECG cells are identical under both inputs.
- **Entry point:** `check-doc` passes 105/105.
- **Leakage:** no event in the primary input is at or after the index admission time or t0.
- **Privacy:** the scan is clean.
- **The 2 BLOCKING findings:**
  - B1: "history before the index admission only" understates how much of the index episode the primary input still holds.
  - B2: the robustness claim "the ECG adds on top of CLMBR-T in every variant" leaves out a contrary result under the first-run input.

- **Auditor:** an independent subagent. It built nothing here and did not import the summary module.
- **Method:** own code in `audits/claude-mimic-audit-20261015/` (umask 077): `a1_leakage.py`, `a1b_ed.py`, `a1c_heldout_timing.py`, `a2_recompute.py`.
- **Read-only:** I read the restricted outputs in `audits/claude-mimic-clmbr-20261014/` and wrote nothing there. I did not call `check-doc` directly, because it writes `summary/doc_numbers.json` and `STATUS.md`. Instead I ran `run_mimic_external.numbers()` and compared its output with the doc myself, with no writes.
- **Privacy:** aggregates only. Counts of 1–10 are suppressed. No note text was opened.

## Results per check

| # | Check | Result |
|---|---|---|
| 1 | Leakage of the primary input (`meds_prior`) | **PASS** on the leakage rules. **FAIL** on how the documented approximation is quantified: see B1. |
| 2 | Headline numbers recomputed independently | **PASS**: 56/56 primary values match, and so do all first-run values. |
| 3 | Consistency of the switch | **PASS** for the doc, `pipeline.md`, identity of the cells and `check-doc`. **SHOULD-FIX:** stale or contradictory labels in the results file, the verify report and the code (S1–S4). |
| 4 | Masks | **PASS**. The masks follow `pipeline.md` §6. No held-out value can be derived from the input. The soft proxy is not worse than at Yale; the primary input is stricter than Yale's. The doc's "closer to Yale" is wrong on this point (S5). |
| 5 | Robustness claim and caveats | **FAIL**: see B2. The two stated caveats are present but not sufficient. |
| 6 | Privacy scan | **PASS** |

## 1. Leakage of the primary input (`meds_prior`; 45,107 analysed subjects; 18,635,430 clinical events)

**Hard checks.** Each count below is 0 (`a1_leakage.json`):
- non-birth events at or after the index admittime;
- non-birth events at or after t0;
- null times; numeric values (the input is code-only);
- diagnosis or procedure events whose `src_hadm_id` is the index admission;
- diagnosis or procedure events whose source admission starts at or after the index admittime;
- diagnosis or procedure events with an unknown source admission;
- any index-hadm event at or after admittime;
- index `Visit/IP` tokens;
- subjects outside the roster.

Every subject has exactly one `MEDS_BIRTH`. The `prior_full` embeddings were built from this exact MEDS: the manifest sha256 equals the `meds_manifest_sha256` recorded in `clmbr/prior_full/manifest.json`.

**Exposure drugs.** I matched the RxNorm concept names of each trial's own drug events against that trial's exposure tokens (taken from `build_mimic_meds.expo_tokens`). There are 0 events in all 8 trials. The positive control works: the same names occur 1,116–54,592 times in the other trials' subjects.
- This includes IV enalaprilat, because the `enalapril` pattern matches it. The 28 events the verifier found came from the index admission, which the primary input drops.
- Drug events with unmapped NDC are out of vocabulary, and the tokenizer drops them.

**Gate codes.**
- **AF trials:** 0 diagnosis events named "atrial fibrillation".
- **HF-gated trials (TRANSFORM-HF, COMET, ELITE II):** 120, 251 and 290 events named "heart failure". All are combination concepts outside the I50/428 prefixes, such as hypertensive heart failure (I11.0 / I13.x / 402 / 404). None is a plain "Congestive heart failure", which shows that the I50/428 filter works.
- **PLATO:** 11 ACS-named events.
- **Why this is not leakage:** all of these come from earlier admissions only. The gate is a cohort condition, not an outcome.

**The documented approximation: the index ED stay before admission.** This is larger than the doc and the verifier report suggest (`a1b_ed.json`).

| Definition of the pre-admission index episode | Events (share of the input) | Patients with any | Patients whose whole clinical input is this episode |
|---|---|---|---|
| Tagged with the index hadm_id (definition used in verifier N2) | 290,320 (1.6%) | 32,467 (72.0%) | 2,931 (6.5%) |
| **Tagged with the index hadm_id, or timed in [edregtime, admittime)** | **1,623,952 (8.7%; 9.7% of lab events)** | **32,485 (72.0%)** | **14,561 (32.3%)** |

- **Most ED-stay lab events have no hadm_id.** In MIMIC, 1,333,366 of the lab events in the ED window carry a null hadm_id. This is why the hadm-tag definition undercounts by a factor of about 5.
- **Only 57.7% of patients have any input from before the index episode.** That is 26,043 of 45,107. The other 42.3% are birth only (10.0% with no clinical event) or have the index ED stay only (32.3%). The per-patient median share of episode events is 23% (IQR 1.6% to 100%).
- **Timing:** index-episode events are a median of 24 h before t0 (IQR 10 to 78 h).
- **t0 before admittime:** in 1,251 subjects (2.8%), t0 falls before the admittime (ED initiation). For them the primary input equals the first-run input.

**Does this matter for the held-out lab values?** For each analysed patient and each of the 17 panel labs, I located the latest value in [t0 − 365 d, t0) (`a1c_heldout_timing.json`; 574,921 patient-lab values):
- **68.5%** were measured inside the index admission. The primary input removes these.
- **21.6%** were measured in the index ED stay or the 24 h before admission. The primary input **keeps their order codes**.
- **9.9%** were measured earlier.
- For the core labs (creatinine, K, Na, Hb, BUN, WBC, platelets), 19–21% are in the ED window. The median lag of the held-out value is about 5.5–6 h before t0.
- For NT-proBNP, 58.7% are in the ED window.

**Judgement.**
- **Not a leakage violation.** The model is code-only, so it never sees a value, and order codes are a soft proxy that `pipeline.md` §6 does not mask.
- **But the label does not hold.** For a third of patients, the primary input consists only of the same acute-episode lab-ordering stream, hours before t0, that the switch was meant to remove.
- **The reported gain may still include this stream.** The primary + CLMBR-T gain (7.7%) may partly reflect this residual stream. It cannot be separated without one more GPU encoding, with the cutoff at min(edregtime, admittime).
- **Rating:** this is a disclosure defect (B1), not a numerical one.

## 2. Recomputed numbers

My code is `a2_recompute.py`. It reads the per-trial cells `results_prior/*_{arms,vars}.csv` and `results/*`. It does not import `mimic_clmbr_summary`. Method:
- items are those finite in both cells; block D is dropped whenever {a, b} ∩ {CLMBR, ECG+CLMBR, permCLMBR} is not empty, which leaves 26 or 22 items;
- relative reduction = 1 − mean_t(m_a) / mean_t(m_b);
- the bootstrap uses `default_rng(20261001).integers(0, 7, (4000, 7))` over trials in the order plato … elite2;
- the sign-flip test is exact over all 2^k sign patterns (one- or two-sided);
- the benchmark-permutation P is computed both exactly (all 5,040 permutations) and with 20,000 draws (`default_rng(0)`).

Every value below equals the doc (`MIMIC_EXTERNAL_VALIDATION.md` lines 16–24, 33–42, 50–55, 61–66, 185–191, 204–206).

| # | Number (primary, `results_prior`) | Recomputed | Doc |
|---|---|---|---|
| 1–5 | + ECG: rel. red.; trials lower; P; % < 0.1; \|Δ log HR\| | 6.6% (2.4 to 13.1); 6/7; .016; 45.6 → 51.6; 0.344 → 0.326 (4/7) | same |
| 6–10 | + CLMBR-T: same five | 7.7% (3.0 to 14.0); 6/7; .023; 44.2 → 51.3; 0.344 → 0.278 (4/7) | same |
| 11–15 | + both: same five | 18.6% (12.5 to 26.7); 7/7; .008; 44.2 → 51.9; 0.344 → 0.240 (6/7) | same |
| 16–19 | both vs CLMBR-T | 11.9% (6.9 to 16.8); 7/7; .008; 51.3 → 51.9 | same |
| 20–21 | both vs ECG | 12.4% (8.8 to 16.2); 7/7; .008 | same |
| 22–23 | CLMBR-T vs ECG (two-sided) | 0.6% (−2.4 to 3.3); 3/7; .734 | same |
| 24–25 | ECG vs permuted ECG | 9.4% (6.2 to 14.0); 7/7; .008 | same |
| 26–27 | CLMBR-T vs permuted CLMBR-T | 8.9% (5.6 to 11.9); 6/7; .016 | same |
| 28–29 | permuted ECG vs base (two-sided) | −3.1% (−5.6 to −0.3); 2/7; .094 | same |
| 30–31 | permuted CLMBR-T vs base (two-sided) | −1.3% (−5.5 to 3.9); 2/7; .609 | same |
| 32–34 | Benchmark-permutation P: + ECG / + CLMBR-T / + both | .838 / .952 / .571 (exact); .836 / .953 / .569 (draws) | .84 / .95 / .57 |
| 35–40 | PEPTIC HR: base, ECG, CLMBR-T, both, permuted ECG, permuted CLMBR-T | 1.51 (1.35–1.69), 1.39 (1.24–1.55), 1.28 (1.14–1.43), 1.21 (1.08–1.35), 1.60 (1.42–1.81), 1.61 (1.43–1.81) | same, and % < 0.1 and mean \|SMD\| also equal |
| 41–46 | Agreement r / estimate agreement / std-diff agreement / mean \|Δ log HR\| (6 arms) | all equal | same |
| 47–52 | §8 rows (any-DM, index-admission codes, no index-day ECG, all 8, unmasked) × 4 contrasts | all 20 values equal | same |
| 53–56 | First-run input: + CLMBR-T 23.1% (16.0 to 28.9) 7/7; + both 29.0% (21.6 to 37.1) 7/7; both vs CLMBR-T 7.7% (3.0 to 14.1) 6/7; \|Δ log HR\| 0.260 / 0.249; benchmark P .695 / .429; PEPTIC 1.00 / 0.95 / 1.43; median C 0.793 / 0.807 | equal | §8 |

**Cell validity:** 0 failed cells and 0 overlap-invalid cells out of 288, under both inputs. In the primary run, 1 of 8 CLMBR-T cells and 1 of 8 both-arm cells retain 50–90% of the smaller arm. Median in-sample C is 0.662 / 0.704 / 0.724 / 0.755. Both match line 24.

**Yale s31 column:** every value is re-read from `contrasts.csv` (S31 / main) and is equal. Yale's "<.001" values are 0.00054 and 0.00066.

**Masking:** utilisation is dropped (22 items) in every contrast that involves a CLMBR-T arm, including CLMBR-T vs ECG and both vs ECG. PEPTIC uses each arm's own mask (26 vs 22 items).

## 3. Consistency of the switch

- **Primary numbers come from `summary_prior`:**
  - `run_mimic_external.numbers()` reads `summary_prior/summary.json` (`run_mimic_external.py:126`). Only the `sens_idx_*` keys read `summary/` (lines 169–173).
  - Every number labelled primary in the doc (lines 15–24, 27–66, 185) and in `pipeline.md:140,173` equals my recomputation from `results_prior`.
- **First-run numbers are labelled as the sensitivity in the doc and in `pipeline.md`:** doc lines 5, 23, 25, 68, 191, 199–206, 214, and `pipeline.md:173`. `pipeline.md:172` is an append-only log line from 2026-10-14, superseded by line 173. That is acceptable.
- **The ECG / base / permuted-ECG cells are identical:** 144 arm rows and 3,744 item rows, with the same index and NaN pattern, max |Δ| = 0 in every column. All CLMBR-T cells differ, as they should. `gate_v21.json` reads PASS in both result directories.
- **`check-doc`:** 105/105, replicated read-only.
  - **Weakness:** the test is a substring match. It does not check that a number sits under the right label.
  - **Not covered:** the first-run |Δ log HR| values, the benchmark P values, the C medians, the cell-validity counts and the coverage rows of the primary input. I checked all of these by hand (§2).
- **Stale first-run numbers presented as primary:** none in `docs/paper/`, the deck builder `scripts/build_lab_deck_1015.py` or `docs/presentation/ecg_tte_lab_2026_10_15.html`. The deck's MIMIC slide is ECG-only: 6.6%, −3.1%, PEPTIC 1.51 → 1.39. I found no MIMIC CLMBR-T number in the untracked manuscript `.docx`. The stale or contradictory spots are in S1–S4.

## 4. Masks (`pipeline.md` §6)

- **Utilisation:** block D (4 items) is masked whenever any CLMBR-T arm is in either cell. This is the MIMIC analogue of Yale's coded-item mask (`pipeline.md:101`) and is correctly applied (§2).
- **Lab and vital values (A, B):** unmasked, as at Yale. The input is code-only, and `numeric_value` is null in all 18.7 M rows. Vitals are not in the input at all (no chartevents or omr).
- **Ventilation at t0:** a soft proxy (ABG codes; phi 0.45), unmasked under the rules. In the primary input only ED-stay ABGs remain.
- **No held-out value is derivable** from the primary input, and no item is the same quantity or code family as an input.

**Soft proxy vs Yale.** At Yale the held-out labs are the latest values in [index − 365, index − 1] (`scripts/build_physiology_panel_v2.py:5,7`; vitals "latest strictly prior day", `scripts/extract_comet_vital_candidates.py:113`). CLMBR-T reads everything up to index − 1. So at Yale, essentially every held-out lab measurement is present as an order code in the CLMBR-T input.

| Input | Held-out lab measurements whose code is in the CLMBR-T input |
|---|---|
| MIMIC first-run | about 100% (all are before t0) |
| Yale | about 100% |
| MIMIC primary | 31.5% (21.6% from the index ED stay + 9.9% earlier) |

What sets the first-run input apart from Yale is closeness in time (hours, within the same acute episode), not the structure. **Judgement:** the soft-proxy exposure of the primary input is not materially worse than Yale's; it is stricter. The doc's line 201, "It is closer to Yale", holds only in the sense of "prior record". On held-out overlap, the first-run input is structurally closer to Yale (S5). Under the §6 rules, nothing needs masking.

## 5. Robustness

The claim at doc lines 21 and 193, "**The ECG's added value on top of CLMBR-T holds in every variant (6.3–11.9%; 5/7 to 8/8 trials lower), including the first-run input (7.7%)**", is numerically right for the 7 rows of the §8 table:

| Row | ECG on top of CLMBR-T |
|---|---|
| Primary | 11.9% |
| Any-DM | 6.3% |
| Index-admission codes | 8.0% |
| No index-day ECG | 11.5% |
| All 8 trials | 11.0% |
| Unmasked | 11.7% |
| First-run input | 7.7% |

All CIs exclude 0.

**It leaves out the first-run input crossed with the design variants**, which exists in `summary/` and was reported before the switch:

| Variant (first-run input) | ECG on top of CLMBR-T |
|---|---|
| any-DM | **0.6% (−5.9 to 8.9), 3/7** |
| index-admission codes | 7.2% |
| no index-day ECG | 9.8% |
| all 8 trials | 8.0% |
| unmasked | 7.8% |

So under the first-run input the ECG's added value fails in 1 of 5 variants. The switch was made post hoc, and it turned "holds in 4 of 5 variants" (results file line 32) into "in every variant". Read with the words "including the first-run input", the sentence is misleading (B2).

**Caveats:**
- "CLMBR-T 0.1% (−11.7 to 12.0) without index-day ECGs" (line 194) is correct.
- The post hoc disclosure (lines 5, 198, 214; `pipeline.md:173`) is adequate.
- **Missing caveats:**
  - the size of the retained index-episode stream (B1);
  - that 42.3% of patients have no input from before the index episode;
  - that the primary input's coverage statistics (83.4% in the dictionary, median 59, 10.6% birth only) differ from the gate statistics in Verdict 2 (S2).

## 6. Privacy scan

**Scope:** the committed MIMIC docs (`docs/mimic/*.md`, `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR{,_RESULTS}.md`), `pipeline.md` and the 27 tracked files in `scripts/mimic/` (including `verify/`).

**Results:**
- **Identifiers:** the only 7+-digit numbers are seeds (20260923, 20261001), a run date (20261014) and the vocabulary release (20240825). No subject_id, hadm_id or pid appears; MIMIC IDs are 8-digit 1xxxxxxx / 2xxxxxxx.
- **Dates:** the only dates are project dates (2026-10-07 to 10-15). There are no timestamps.
- **Small counts:** none unsuppressed. Searches for "1–10 patients / events / subjects" and "n = 1–10" found nothing.
- **Restricted per-trial quantities:** no per-trial n_pairs, retention or ESS.
- **Scripts:** they print aggregates only.

**Minor:**
- `coverage.py:97,108` prints per-trial `pct_no_history_outside_index_adm` to stdout without small-count suppression. Nothing is committed.
- `build_mimic_meds.py:261` prints the first line of a DB error message. This is already noted as R1.
- This report states only aggregates; every count is ≥ 11.

**Result: PASS.**

## Findings

### BLOCKING

**B1. The primary input is labelled "history before the index admission only", but it keeps the index ED stay for most patients, and for a third of them the ED stay is the whole input.**
- **Where:**
  - `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md:5, 15, 25, 27, 116–118, 122, 138–139, 201, 214`;
  - `pipeline.md:140, 173`;
  - `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR_RESULTS.md:3`.
- **The doc's only caveat:** doc line 201 says "labs and orders of the index ED stay before the admission time are kept (verification report: in most patients)". The verifier's figures (`VERIFY_MIMIC_CLMBR.md:104–107`: 1.6% of events, 6.5% of patients with only such events) count hadm-tagged events only.
- **What the data show:**
  - including the null-hadm ED labs, the stream is 1.62 M events (8.7% of the input; 9.7% of lab events) in 72.0% of patients;
  - it is the **only** clinical input for 14,561 patients (32.3%);
  - 21.6% of the held-out lab values were measured in that window (core labs about 20%; NT-proBNP 59%);
  - in 2.8% of subjects, t0 falls before the admittime, and their primary input equals the first-run input.
- **Fix:** replace the label with "events before the index admission time (the index ED stay before admission is kept)". In §5.3 / §8 / §9 and `pipeline.md:140`, add one sentence with these figures. In §8, reword "about two-thirds … rather than prior history" (line 200). The 7.7% still contains the index ED stream, so the difference is the in-admission pre-t0 stream, not "prior history vs the index admission".
- **Optional sensitivity (not required for the fix):** re-encode with the cutoff at min(edregtime, admittime). This needs one GPU run and the same analysis code.

**B2. "The ECG adds on top of CLMBR-T in every variant … including the first-run input" leaves out a contrary result.**
- **Where:** `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md:21, 193`.
- **The omitted result:** under the first-run input with the any-diabetes base, the ECG on top of CLMBR-T is 0.6% (−5.9 to 8.9), 3/7. This was reported before the switch (results file line 32: "holds in 4 of the 5 design-detail variants … but not with any diabetes").
- **Fix:** scope the sentence to "every variant under the primary input". Add: "under the first-run input it holds in 4 of 5 design-detail variants (7.2–9.8%) but not with any diabetes (0.6%, 3/7)".

### SHOULD-FIX

- **S1. The results file contradicts its own banner.** `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR_RESULTS.md`:
  - lines 20–26 present the first-run 23.1% / 29.0% as "Headline balance";
  - line 28 calls the now-primary input a "Caveat (sensitivity added after the results were seen)";
  - lines 30, 34 and 36 give first-run numbers as the main answers;
  - **line 42, the ready-to-paste deck sentence, uses first-run numbers** ("AI-EHR alone gave 23.1% … the AI-ECG still added 7.7%"). The deck does not use it at present.
  - **Fix:** mark lines 20–42 "(first-run input; now the sensitivity)", or strike them, and replace the deck sentence with primary numbers (+ CLMBR-T 7.7%, 6/7; ECG on top 11.9%, 7/7).
- **S2. Verdict 2 gives the gate statistics without saying which input they describe.** `MIMIC_EXTERNAL_VALIDATION.md:14` (and `QUEUE_..._RESULTS.md:12–16`) gives 82.1% / 211 (93–490) / 0.2% with no prior history. These describe the **first-run** input. For the primary input the values are 83.4% in the dictionary, median 59, and 10.6% birth only; the doc mentions this only at lines 138–139 and 144. **Fix:** label Verdict 2 and add the primary-input values.
- **S3. The verify report predates the switch and has no banner.** In `docs/mimic/VERIFY_MIMIC_CLMBR.md:45–66`, the first-run values (23.1%, 29.0%, 7.7%, C 0.793 / 0.807, "3 of 8") appear unlabelled, and the prior-only values are labelled "Prior-only". Round 2 also treats the prior-only input as the sensitivity (lines 188–189). **Fix:** add a header note that it verified commit 7b52b10, before the switch, with the labels now reversed, and point to this audit for 0bf4cbe.
- **S4. The code still uses the old labels, and the entry point cannot rebuild the primary arm.**
  - `scripts/mimic/build_meds_prior_only.py:2` says "Sensitivity input". Line 4 calls `OUT/meds` "the primary MEDS". Line 69 logs "sensitivity MEDS".
  - `scripts/mimic/run_mimic_external.py:104` logs every primary summary line to `STATUS.md` with the prefix "sensitivity (…)".
  - Line 179 writes `doc_numbers.json` (the primary numbers) into `OUT/summary/`, which is the sensitivity directory.
  - The `all` pipeline (line 194) has no step that builds `meds_prior` (`build_meds_prior_only` is never called). `ENCODE_CMD` (lines 30–32) covers only `meds` → `clmbr/full`.
  - `prior()` (lines 90–105) checks only the model and runtime hashes of `prior_full`. It does not check one finite embedding per subject or the MEDS manifest hash, which `encode()` (lines 56–77) checks for `full`. I verified the MEDS manifest hash by hand: it matches.
- **S5. "Closer to Yale" is not right on the dimension that drove the switch.** `MIMIC_EXTERNAL_VALIDATION.md:201` says the primary input is "closer to Yale". At Yale the held-out labs ([index − 365, index − 1]) all lie inside the CLMBR-T input window, so the first-run input mirrors Yale structurally (about 100% of held-out measurements coded in the input). The primary input is stricter (31.5%). The comparison at line 25 ("less than at Yale (12.9%) … expected: thin prior record") should also note that the primary MIMIC input is stricter than Yale's rule, not only thinner.
- **S6. `check-doc` is a substring match.** Short strings such as ".008", ".016" or "6/7" are matched trivially, and the check cannot tell a primary number from a sensitivity number placed under the wrong label. Consider keying it to table rows, or adding the |Δ log HR|, benchmark-P, C-median and cell-validity values of both inputs.
- **S7. Wording.** At line 201, "0 remaining events were checked" should read "a check found 0 remaining events at or after the admission time".

### NON-BLOCKING notes

- The gate exclusion is by ICD prefix. HF combination concepts (hypertensive HF) remain from earlier admissions in the HF-gated trials. This is not leakage (verifier N7, confirmed on the primary input).
- The prior-only cells depend on BLAS threading, because birth-only patients share an embedding. This is disclosed at doc line 151, and the published numbers are unaffected.
- Not tested: the CLMBR-T inference itself. No GPU was used, and the verifier already checked the hashes, the embeddings and the tokenizer counts.
