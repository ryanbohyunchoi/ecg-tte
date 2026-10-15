# Results: MIMIC-IV external validation clean-up and CLMBR-T arms (queue 2026-10-14)

Queue: `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR.md`. Consolidated doc: `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md`. Verification: `docs/mimic/VERIFY_MIMIC_CLMBR.md`. Code: `scripts/mimic/` (entry point `run_mimic_external.py`). Restricted outputs: `audits/claude-mimic-clmbr-20261014/` (not committed). Aggregates only.

## Summary

1. **Step 0 gate: PASS.** The existing MIMIC PS-CVD5 analysis, re-run from scratch, reproduces `docs/v21/MIMIC_PAPER2.md` exactly: 6.6% (2.3–12.8), 6/7 trials lower, P = .016; % |SMD| < 0.1 45.6 → 51.6; permuted ECG −3.1%. All 24 tables have max |Δ| 0.
2. **Feasibility and coverage vs Yale: GO** (the stop rule did not fire).

   | | MIMIC (analysed) | Yale s31 |
   |---|---|---|
   | Coded events in the CLMBR-T dictionary | 82.1% | 78.5% |
   | In-vocabulary events per patient, median (IQR) | 211 (93–490) | 308 (104–757) |
   | No prior coded history | 0.2% | < 11 patients |

   - Built to match the Yale input: diagnoses mapped ICD → SNOMED; NDC → RxNorm; a curated lab LOINC map (MIMIC-IV 3.1 has no LOINC; under the literal itemid rule only about 9% of events would be in the dictionary).
   - Model and runtime hashes equal Yale's. One finite 768-d embedding per subject; 0 events at or after t0; 0 index-admission diagnosis or procedure codes.
3. **Headline balance, PS-CVD5 analog (7 cardiovascular trials; MIMIC vs Yale s31):**

   | Arm vs PS-CVD5 | MIMIC | Yale s31 |
   |---|---|---|
   | + ECG | 6.6% (2.4 to 13.1), 6/7 | 8.7% (4.2 to 13.5) |
   | + CLMBR-T | 23.1% (16.0 to 28.9), 7/7 | 12.9% (7.6 to 18.3) |
   | + ECG + CLMBR-T | 29.0% (21.6 to 37.1), 7/7 | 14.6% (7.7 to 21.1) |

   - **Caveat (sensitivity added after the results were seen):** with CLMBR-T restricted to history before the index admission, + CLMBR-T is 7.7% (3.0 to 14.0) and + both 18.6% (12.5 to 26.7). Most of the large MIMIC CLMBR-T gain comes from the index admission's own pre-t0 lab and order stream, which is close in time to the held-out lab values.
4. **Does the ECG still add once CLMBR-T is in?**
   - **MIMIC, yes:** 7.7% (3.0 to 14.1), 6/7, P = .016.
     - It is 11.9% (6.9 to 16.8; 7/7) with the prior-history-only CLMBR-T.
     - It holds in 4 of the 5 design-detail variants (7.2–9.8%), but not with any diabetes in place of T2D (0.6%).
   - **Yale, no:** 2.0% (−3.5 to 6.9), P = .24.
5. **Agreement:** mean |Δ log HR| 0.344 → 0.326 (+ ECG) → 0.260 (+ CLMBR-T) → 0.249 (+ both), but the benchmark-permutation P is .84, .70 and .43. The placebos also attenuate the estimates, so this is attenuation, not trial-specific agreement, as at Yale.
6. **PEPTIC (RR 1.05):**
   - PS-CVD5 1.51 (1.35–1.69); + ECG 1.39 (1.24–1.55); + CLMBR-T 1.00 (0.90–1.11); + both 0.95 (0.85–1.06); permuted CLMBR-T 1.43 (1.28–1.61).
   - With prior-history-only CLMBR-T: 1.28 (1.14–1.43).
7. **Cell validity:** 0 failed cells and 0 overlap-rule failures in every base and population.
8. **Verification:**
   - **Round 1: FAIL**, on three text statements only (index-admission share of labs; the range in a sensitivity sentence; "prior admissions only" in `pipeline.md`). All three are fixed. All 353 recomputed numbers matched, leakage counts were 0, hashes matched and the privacy scan was clean.
   - **Round 2: PASS with minor issues**, with no BLOCKING finding. The two wording notes are fixed. Report: `docs/mimic/VERIFY_MIMIC_CLMBR.md`.
9. **Deck sentence (MIMIC slide; do not paste into the deck without review):** "In MIMIC-IV (7 cardiovascular trials), adding the AI-ECG to the PS-CVD5 analog improved held-out balance by 6.6% (6/7 trials), and the AI-ECG still added 7.7% (6/7) once AI-EHR (CLMBR-T) was in the model. AI-EHR alone gave 23.1%, but most of that came from in-hospital codes recorded before time zero (7.7% from prior history only), and neither representation made agreement with the RCTs trial-specific."

## Notes

- **Deviations from the queue** (all documented in the doc):
  - curated lab LOINC map;
  - NDC → RxNorm from a second OHDSI vocabulary, read in place;
  - emar not used (it has no drug code);
  - birth at 1 July of the de-identified birth year; no sex token (as at Yale);
  - birth-only subjects encoded from birth;
  - inference on GPU 6 (shared; GPU 3 was busy at launch), and the sensitivity run on GPU 3.
- **Privacy note:** in the first MEDS build attempt, a DuckDB CSV parse error echoed one raw prescriptions row to the agent console. It was not written to any file or doc; the builder now catches database errors and prints only the exception type and the first line of the message (CSV errors put the raw row on a later line).
