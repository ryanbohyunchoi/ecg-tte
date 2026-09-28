# CLMBR input leakage check (v1.8 Plan B, STEP 0; written before any v1.8 result)

**Script.** `scripts/v18/v18_clmbr.py leakage` → `audits/claude-v18-clmbr/leakage.csv`. Aggregates only; counts 1–10 are suppressed ("<11 pts").

**Population.** For each of the 33 trials, the analysed cohort is `E.load_trial(n).keys`: the intersection of baseline, ECG, CLMBR, phenotype and panel keys. Percentages are pooled over both arms.

**Code examined:**
- `scripts/build_comet_meds.py` (OMOP gold → MEDS);
- `scripts/encode_comet_clmbr.py` (MEDS → frozen CLMBR-T, `--numeric-mode code-only --max-tokens 4096`);
- `scripts/build_trial_cohort.py` / `trial_common.create_drug_tokens` (exposure definition);
- `v13_common.Trial.clm_pc` (64 PCs of the 768-d vector).

## (a) Input window ends before index and excludes the index day: PASS

**From the code:**
- `build_comet_meds.build` sets `cuts[pid] = datetime.combine(index_date, 00:00)`. It drops every event with `t >= cut` (counted as `same_day_or_future`), every event with missing or offset time, and every event before birth.
- Date-only events are timestamped at 00:00 of their date. An index-day event is therefore always ≥ the cut.
- `encode_comet_clmbr.patient_events` re-checks every event and raises `non_preindex_event` if `time >= index midnight`.
- `select_vector` requires every representation timestamp to be < index midnight. It takes the last pre-index token representation.
- Five domains are used: condition, drug_exposure, procedure, measurement and visit. Numeric values are dropped at model input (code-only).
- The history is all available pre-index history, truncated to the last 4,096 tokens.

**From the data, all 33 trials:**
- **Events at or after index midnight:** 0.
- **Latest event:** 1–5 minutes before index midnight (23:59, or 23:55 at worst), i.e. on index − 1.
- **Index dates:** the MEDS roster index date equals the cohort index date for every analysed patient in all 33 trials.
- **MEDS lineage:** the sha256 of each MEDS `manifest.json` equals `meds_manifest_sha256` in its CLMBR manifest, for 33/33 trials.
- **Last event on index − 1:** 21–77% of patients have their last input event on the day before index. That day is part of the pre-index record (e.g. pre-admission labs and visits). The index day itself is excluded.

## (b) Exposure-defining codes: PRESENT IN INPUT ROWS, LARGELY NOT SEEN BY THE MODEL, INDEX PRESCRIPTION EXCLUDED

**How exposure is defined.** It uses orders whose `-`-split `drug_source_value` contains an arm keyword; for CABANA ablation, procedure-code prefixes.
- **Index:** the first-ever order of the arm drug.
- **New-user designs:** no comparator-arm order in the 365 days up to and including index.
- **Switch (`switch_seq`) designs:** PARADIGM-HF-seq, EAST-AFNET 4, AFFIRM and AF-CHF. By design, both arms require an order of the comparator/prior class in the 365 days before index. Comparator arm = established users; switchers must have a prior-class order, and the prior class is the comparator class in all four.

**Exposure concept sets.** These are the gold `drug_concept_id`s (ingredient-level) of orders matching an arm keyword. A concept is kept only if its name contains an arm keyword; this removes cross-mapped combination rows. CABANA ablation uses `procedure_concept_id`s of matching procedure codes.

**Presence in the MEDS input** (any pre-index event with an exposure concept) is counted at two levels:
- rows passed to the tokenizer;
- **vocab-accepted** tokens, i.e. the MEDS code is a `code` entry of the CLMBR-T dictionary (`/mnt/raid0/eo287/clmbr/dictionary.msgpack`). Only accepted codes reach the model.

**Findings:**
1. **The index prescription is never in the input**, because the index day is excluded (see (a)).
2. **Own-arm drug before index, new-user designs:** 0–1.7% of patients in the input rows. These are ingredient concepts reached through combination products, e.g. `sacubitril-valsartan` → valsartan. Vocab-accepted: 0% in 27/29 trials, <11 patients in SUSTAIN-6, 0.59% in INSIGHT.
3. **Switch designs.** The comparator class is in the prior-365-day input for ~100% of patients in both arms, as required by design, so it does not separate the arms by construction. The own-arm drug appears in 76–79% of input rows, i.e. the continuers' drug. The CLMBR-T vocabulary accepts only a few of these ingredient codes: 2.4–2.8% of patients have an accepted own-arm token; 0% in PARADIGM-HF-seq.
4. **Other-arm drug earlier in history** (outside the 365-day washout, or COMET with no washout rule): 1–71% of input rows. It is vocab-accepted only where the drug's RxNorm ingredient is in the dictionary:
   - apixaban/warfarin/rivaroxaban/dabigatran trials: ARISTOTLE 5.9%, ROCKET-AF 5.8%, RELY 1.5%, AMPLIFY 2.9%;
   - TRANSFORM-HF 1.7%;
   - ≤ 0.8% elsewhere.
5. **Only 13 of 226 trial-level exposure concepts** across trials are in the CLMBR-T vocabulary. For context, pooled over all MEDS builds, the tokenizer accepts:

   | Domain | Rows accepted |
   |---|---|
   | condition | 95% |
   | measurement | 87% |
   | procedure | 55% |
   | drug_exposure | 37% |
   | visit | 100% |

   For example, RxNorm metoprolol, carvedilol and lisinopril are not in the vocabulary; apixaban, warfarin and rivaroxaban are.

**Judgement.** No arm-defining information from the index day enters CLMBR.
- Pre-index exposure-class history reaches the model for at most 5.9% of any trial's patients.
- It is legitimate baseline history, since an hdPS would use it too, but it is documented here.
- Because of it, two sensitivity sets are fixed now, before results:
  - **S_noown** (27 trials): excludes the four switch-design trials and every trial with any vocab-accepted own-arm token (SUSTAIN-6, INSIGHT).
  - **S_noexpo** (23 trials): excludes every trial with any vocab-accepted exposure token. The excluded trials are TRANSFORM-HF, ARISTOTLE, ROCKET-AF, RELY, EAST-AFNET 4, SUSTAIN-6, INSIGHT, AFFIRM, AF-CHF and AMPLIFY.

The key contrasts (CLMBR vs base, CLMBR+ECG vs CLMBR) are also reported on both sets.

## (c) CLMBR embeddings exist for all 33 analysed trials: PASS

For 33/33 trials:
- 100% of analysed patients have an encoded CLMBR-T vector;
- `T.clm_pc` is n × 64 and finite for all rows;
- numeric mode is code-only and `max_tokens` is 4096.

`v13_common.Trial` intersects the keys with the CLMBR keys, so there is no CLMBR-specific loss inside the analysed cohort. The CLMBR-T PCs are unsupervised and fitted on all analysed rows. No treatment or outcome is used.

## Per-trial facts (pooled over arms; % of analysed patients)

| trial | design | n | % last event on index−1 | expo concepts | in vocab | % any expo token | % any ≤365 d | % any vocab-accepted | % own-arm | % own-arm on index−1 | % own-arm vocab | % other-arm | % other-arm ≤365 d | % other-arm vocab | % prior-class ≤365 d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| comet | new_user | 6381 | 67.86 | 2 | 0 | 71.32 | 59.32 | 0.0 | 0.0 | 0.0 | 0.0 | 71.32 | 59.32 | 0.0 |  |
| paradigm-hf-seq | switch_seq | 5129 | 36.17 | 11 | 0 | 91.32 | 87.66 | 0.0 | 76.16 | 3.76 | 0.0 | 15.17 | 11.52 | 0.0 | 99.98 |
| transform-hf | new_user | 15657 | 52.94 | 2 | 1 | 1.92 | 0.0 | 1.67 | 0.0 | 0.0 | 0.0 | 1.92 | 0.0 | 1.67 |  |
| elite-ii | new_user | 3222 | 49.6 | 18 | 0 | 20.92 | 0.47 | 0.0 | 1.4 | 0.0 | 0.0 | 19.65 | <11 pts | 0.0 |  |
| life | new_user | 3131 | 30.92 | 12 | 0 | 12.9 | 0.54 | 0.0 | 1.5 | <11 pts | 0.0 | 11.66 | <11 pts | 0.0 |  |
| plato | new_user | 6759 | 58.65 | 2 | 0 | 4.01 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.01 | 0.0 | 0.0 |  |
| aristotle | new_user | 18771 | 50.31 | 2 | 2 | 5.91 | 0.0 | 5.91 | 0.0 | 0.0 | 0.0 | 5.91 | 0.0 | 5.91 |  |
| rocket-af | new_user | 7055 | 45.92 | 2 | 2 | 5.84 | 0.0 | 5.84 | 0.0 | 0.0 | 0.0 | 5.84 | 0.0 | 5.84 |  |
| rely | new_user | 4172 | 53.67 | 2 | 1 | 2.42 | 0.0 | 1.49 | 0.0 | 0.0 | 0.0 | 2.42 | 0.0 | 1.49 |  |
| allhat | new_user | 26592 | 31.89 | 4 | 0 | 9.73 | 0.05 | 0.0 | 0.22 | 0.0 | 0.0 | 9.51 | <11 pts | 0.0 |  |
| emperor-preserved-v2 | new_user | 2417 | 41.75 | 10 | 0 | 6.58 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 6.58 | 0.0 | 0.0 |  |
| east-afnet4 | switch_seq | 16109 | 50.75 | 14 | 1 | 99.99 | 99.99 | 3.12 | 78.5 | 10.12 | 2.41 | 21.49 | 21.49 | 0.71 | 99.99 |
| cabana-v2 | proc_vs_drug | 13133 | 55.09 | 10 | 0 | 4.01 | 2.51 | 0.0 | 0.0 | 0.0 | 0.0 | 4.01 | 2.51 | 0.0 |  |
| ontarget | new_user | 14853 | 28.29 | 18 | 0 | 13.88 | 0.53 | 0.0 | 1.7 | <11 pts | 0.0 | 12.31 | <11 pts | 0.0 |  |
| value | new_user | 26657 | 27.35 | 9 | 0 | 10.5 | 0.55 | 0.0 | 1.59 | <11 pts | 0.0 | 9.06 | 0.13 | 0.0 |  |
| ascot | new_user | 26021 | 30.01 | 5 | 0 | 8.56 | 0.05 | 0.0 | 0.15 | 0.0 | 0.0 | 8.42 | <11 pts | 0.0 |  |
| empa-reg | new_user | 5649 | 29.12 | 10 | 0 | 8.27 | <11 pts | 0.0 | <11 pts | 0.0 | 0.0 | 8.25 | 0.0 | 0.0 |  |
| carolina | new_user | 1794 | 21.52 | 2 | 0 | 3.68 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3.68 | 0.0 | 0.0 |  |
| leader | new_user | 3782 | 26.81 | 5 | 0 | 2.62 | 0.0 | 0.0 | <11 pts | 0.0 | 0.0 | 2.59 | 0.0 | 0.0 |  |
| sustain6 | new_user | 3727 | 22.83 | 5 | 1 | 12.07 | 0.46 | 0.67 | 0.59 | 0.0 | 0.59 | 11.62 | <11 pts | <11 pts |  |
| rewind | new_user | 6049 | 23.01 | 5 | 0 | 5.26 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 5.26 | 0.0 | 0.0 |  |
| declare | new_user | 6967 | 28.16 | 5 | 0 | 4.79 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.79 | 0.0 | 0.0 |  |
| canvas | new_user | 6037 | 24.2 | 5 | 0 | 1.62 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.62 | 0.0 | 0.0 |  |
| tecos | new_user | 2925 | 26.6 | 4 | 0 | 11.9 | <11 pts | 0.0 | <11 pts | 0.0 | 0.0 | 11.79 | 0.0 | 0.0 |  |
| carmelina | new_user | 1546 | 38.1 | 4 | 0 | 12.81 | 0.0 | 0.0 | <11 pts | 0.0 | 0.0 | 12.74 | 0.0 | 0.0 |  |
| valiant | new_user | 2096 | 57.01 | 18 | 0 | 10.16 | <11 pts | 0.0 | 0.81 | 0.0 | 0.0 | 9.4 | 0.0 | 0.0 |  |
| insight | new_user | 8847 | 22.76 | 4 | 1 | 1.13 | <11 pts | 0.53 | <11 pts | 0.0 | <11 pts | 1.03 | <11 pts | 0.43 |  |
| affirm | switch_seq | 17634 | 42.38 | 14 | 1 | 99.99 | 99.98 | 3.58 | 76.74 | 5.9 | 2.84 | 23.25 | 23.24 | 0.75 | 99.98 |
| af-chf | switch_seq | 5558 | 46.28 | 14 | 1 | 100.0 | 100.0 | 2.91 | 77.11 | 6.12 | 2.36 | 22.89 | 22.89 | 0.56 | 100.0 |
| precision | new_user | 5310 | 27.01 | 2 | 0 | 4.99 | <11 pts | 0.0 | <11 pts | 0.0 | 0.0 | 4.92 | 0.0 | 0.0 |  |
| amplify | new_user | 5080 | 76.99 | 2 | 2 | 2.89 | 0.0 | 2.89 | 0.0 | 0.0 | 0.0 | 2.89 | 0.0 | 2.89 |  |
| lodestar | new_user | 22277 | 39.52 | 2 | 0 | 20.51 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 20.51 | 0.0 | 0.0 |  |
| prove-it | new_user | 4379 | 60.36 | 2 | 0 | 7.15 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 7.15 | 0.0 | 0.0 |  |
