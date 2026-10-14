# Independent verification: s31 update of the LATENT-RCT lab deck (15 October 2026)

Queue `docs/queue/QUEUE_2026_10_14_S31.md`, Step 6. The verifier built nothing in this project. Verified on 2026-10-14:
- `docs/presentation/ecg_tte_lab_2026_10_15.html` (24 slides: 17 main + A1–A6);
- `docs/paper/figures_latent/` (Figure 2 and its panels);
- `docs/presentation/figures/latent_rct_overview.*`;
- `docs/s31/S31_RESULTS.md`, plus `s31_numbers.json`, `figure2_values.json` and `deck/claims.csv` in `audits/claude-s31-20261014/`.

Verifier scripts and outputs are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-deck2-20261014/verify_s31/` (umask 077, aggregates only). The main ones:
- `recompute.py`: independent recomputation, written fresh;
- `compare.py`: 939 comparisons, saved to `compare.csv`;
- `extras.py`;
- `dump_text.py` and `scan_counts.py`: visible text of every slide and popup;
- `functional.py`: adapted from the earlier verifier;
- `explorer_test.py`: fresh-page explorer checks;
- `privacy_masks.py`, `fig_embed.py`, `pdf_raw.py`;
- `shots/`: 124 screenshots.

## Verdict: **PASS with minor issues**

There are no BLOCKING issues:
- every checked number matches the independent recomputation;
- PROTECT AF is excluded from every primary number and labelled correctly;
- all functions work, with 0 console or page errors;
- the masks follow pipeline.md §6 on the 54-item panel;
- the privacy scan is clean.

## Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | No stale 32 / 38 where 31 / 37 is meant | **PASS** | Every slide (all builds revealed), all 5 popups, SVG text and every select option were scanned for 32 / 38 / 12 / 300 / PROTECT. The remaining instances are all allowed: the 32-trial sensitivity (slide 12 row 1, slides 16 and 17, A1, A5, A6, explorer options "Sens.: paper 1's 32 (with PROTECT AF)"); the 38 in the A3 / A3b titles ("All 38 emulated trials"); the A2 viewer filter "All 38 emulated"; explorer options "All 38 emulated (with PROTECT AF)" and "Physiologic: …, all 38"; A5's "All 38" sensitivity row and "Age bounds checked in all 38"; A1's "38 new candidates" (trial search, a different quantity); "32 PCs" (ECG components). The overview figure's text layer has no 32, 38 or 12. |
| 2 | PROTECT AF excluded from every primary number and labelled | **PASS** | Embedded data: PROTECT AF has `s31 = false`, `f37 = false`, `s32 = true`, status "excluded at feasibility (smaller arm < 350)"; 31 / 37 / 32 flags overall. A1 and the slide 6 popup read: "PROTECT AF (LAA closure) excluded: smaller arm < 350", plus the 300 → 350 disclosure line. A2: "Good … no (feasibility)". A3: grey row with "excluded at feasibility (smaller arm < 350)", In 31 = no. A5: grey bar (`#b9bbc8`, not navy). The quality popup says "PROTECT AF (Good) was excluded earlier, at feasibility". Slide 13 defaults to 37 feasible. The two framework v2.0 sets (29 / 30) still contain PROTECT AF, and the deck says so ("defined before the size-rule change, both include PROTECT AF"). Every s31 number the verifier recomputed excludes PROTECT AF and differs from the 32-trial value. |
| 3 | ≥ 25 headline numbers recomputed with independent code | **PASS** | 939 values compared (s31 and s32: primary, placebo, domains, six methods, the full ladder, \|Δ log HR\|, agreement by tier, plus Figure 2A/2B/2C/2D). 0 mismatches beyond tolerance, except 4 Pearson r values for the Limited tier that differ by ≤ 2.6e-6 (deterministic quantities; tolerance 1e-6). Benchmark-permutation P was checked within Monte Carlo tolerance (max \|diff\| 0.006). See "Recomputed numbers" below. |
| 4 | Rendering, navigation, builds, popups, links, explorers | **PASS** | 24 slides screenshotted at 1920×1080 and 1366×768, with every build step (shots/). Overflow outside the stage: none at either size. ArrowRight runs through all 49 slide/step states in order and stops at the end; ArrowLeft returns to (0, 0); PageUp/Down, Arrow Up/Down, Space, Home and End work. Hash URLs work for all 24 labels, as does hashchange. 5 popups: open without advancing, inside the viewport; close by Esc, button and backdrop; an inside click keeps them open; keys are blocked while open. 17 cross-links all land correctly; every back-link returns to its origin and is labelled with it; direct-entry back-links go to the default slide. Explorers default to s31 (slides 9 and 11), 37 feasible (slide 13) and v1 / main / PS-CVD5 / 54 / leakage on. Every select option and checkbox changes the output, except where no change is expected (below). 0 console or page errors in all runs. |
| 5 | Leakage masks (pipeline.md §6) | **PASS** (one 58-panel documentation mismatch, MINOR) | Cells (ex58) and deck data (`D.ex`, `D.leak`), 54-item panel: PS-Demo, PS-CVD5, PS-CVD10 and hdPS mask nothing. PS-Clinical (no LVEF) masks the 8 `smd_obs_*` (not LVEF) plus eGFR; the explorer shows 45 items, matching. ex58 is identical across arms and trials of a rung, so placebos take the real arm's mask. 58-item panel: PS-CVD5 and PS-CVD10 mask `B_mean` and the prognostic score; hdPS and PS-Clinical mask all 4 coded items; CLMBR-T arms mask the 4 coded items (builder `LEAK_ARM`; the deck embeds no CLMBR-T arms). My recomputation imposed the pipeline.md masks independently and reproduced every builder value exactly. One difference: pipeline.md lists `B_mean` and the prognostic score for PS-Demo on the 58, but the builder (`LEAK_RUNG["P1"] = []`), the explorer and slide 8 ("PS-Demo none none") mask nothing. See MINOR-3. |
| 6 | Privacy | **PASS** | HTML: no `n_pairs`, ESS, retain or retention, and no patient or person ids. The 3 hits for "n_t" are inside item names (e.g. `hs_troponin_t`). Embedded per-trial fields hold only design and benchmark information. Patient-count phrases occur only as the rule "fewer than 11 matched pairs" (×3). Small numbers on the slides are trial counts (e.g. 3/6, 6/7, Excellent 3) or percentages; none are patient counts. Figure PDFs (6) and the overview SVG: no forbidden tokens; metadata is Matplotlib only. The deck's embedded Figure 2 is the rebuilt s31 file, resized (pixel correlation 0.99998). The deck still embeds per-trial \|SMD\| and per-trial HR and SE, as in the earlier decks; these are trial-level aggregates, not patient-level data. |
| — | 10-09 deck and old builders unchanged | **PASS** | `git diff --quiet` is empty for `docs/presentation/ecg_tte_lab_2026_10_09.html`, `scripts/build_lab_deck.py` and `scripts/build_lab_deck_v2.py`. |

Explorer options that leave the output unchanged, all as expected:
- the domain option "Physiology only" equals "All domains" on the 54-item panel, because all 54 items are physiology;
- the quick-view radios All / Physiology are the same on the 54 for the same reason;
- the emulation-explorer set "Excellent or Good or Moderate (31)" equals s31, because it is the same 31 trials;
- the ladder checkboxes affect only the ladder view. On a fresh page in that view, they do change the plot (`explorer_test.py`).

The earlier verifier's `functional.py` reloads with `goto(DECK + "#1")`, which only changes the hash. Its leakage-toggle readout was therefore taken in a stale state and is invalid. I re-ran that check on fresh pages (`explorer_test.py`):
- PS-Clinical, leakage on: 3.3% (−1.1 to 7.5), 45 items shown, note "Also masked here: Systolic BP, …, eGFR";
- PS-Clinical, leakage off: 3.2% (−1.1 to 7.4), 46 items shown;
- PS-CVD5 is identical on and off (8.7% (4.2 to 13.5), 54 items).

## Recomputed numbers (deck / builder value vs verifier)

The verifier's code (`recompute.py`, `extras.py`) imports nothing from the builder, the s31 scripts or the earlier verifier. It has its own:
- ex58 plus pipeline.md masks;
- failed-cell rule (cell_failed, or n_pairs < 11);
- per-trial mean \|SMD\| on items observed in both arms;
- relative reduction, and a 4,000-resample bootstrap (seed 20261001) over trials in index order;
- exact sign-flip (meet-in-the-middle enumeration of all 2^k sign vectors);
- benchmark permutation, with its own seed and 20,000 draws (200,000 for the precise check);
- RCT-DUPLICATE agreement metrics.

The cells come from the three restricted parquets (read only); unmatched \|SMD\| come from `claude-v18-embed-compare/results.csv`. No failed cells exist in s31 (0 in every rung, configuration and arm).

### Primary and placebo (s31, PS-CVD5 + ECG vs PS-CVD5, 54 items)

| Quantity | Deck (slide) | S31_RESULTS / JSON | Verifier |
|---|---|---|---|
| Relative reduction | 8.7% (4.2 to 13.5) (9, 12, 16, Fig 2C) | 8.6513 (4.2232 to 13.5085) | 8.6513 (4.2232 to 13.5085) |
| One-sided sign-flip P | < .001 | 0.000542 | 0.000542 |
| Trials lower | 20/31 | 20/31 | 20/31 |
| Mean \|SMD\| | 0.129 → 0.117 | 0.12857 → 0.11744 | 0.12857 → 0.11744 |
| % items < 0.1 | 53.9 → 57.3, +3.3, 19/31, P .02 (9, Fig 2D) | 53.923 → 57.271, +3.348, 19/31, P .0152 | identical |
| Trials with mean \|SMD\| < 0.10 (PS alone / + ECG / + permuted) | 7/31, 10/31, 8/31 (9) | — | 7, 10, 8 |
| Permuted vs PS alone | 0.4% (−3.5 to 4.3), P = .83 two-sided (12); .42 one-sided (9) | 0.4214 (−3.459 to 4.273), P .834 | 0.4214 (−3.459 to 4.273), two-sided .834, one-sided .417 |
| ECG vs permuted | 8.3% (4.0 to 12.7) (12, 16) | 8.2647 (3.995 to 12.746) | identical |
| ECG vs permuted, five sets | 8.3 to 9.4% (12) | 8.26 / 8.74 / 8.91 / 9.27 / 9.38 | 8.26 / 8.74 / 8.91 / 9.27 / 9.38 |
| Leave-one-trial-out, largest P | .001 (12) | 0.00108 | 0.00108 |
| \|Δ log HR\| | 0.232 → 0.198, 20/31, sign-flip .04 (11) | 0.2324 → 0.1984, P .0351 | 0.2324 → 0.1984, 20/31, P .0351 |
| Benchmark-permutation P | 0.54 (11, JS) | 0.555 | 0.5505; precise (200k draws) 0.549 |
| Agreement, PS alone / + ECG / + permuted (r, est., std.) | .55/45%/74%; .56/68%/77%; .51/45%/77% (11) | same | 0.548/45.2/74.2; 0.562/67.7/77.4; 0.513/45.2/77.4 |
| 32-trial sensitivity | 8.8% (4.4 to 13.3), 21/32, P < .001 (12, 16, A5) | 8.8457 (4.367 to 13.295) | 8.8457 (4.367 to 13.295), 21/32 |
| All 37 feasible / all 38 (explorer) | 8.9% (4.7 to 13.2) / 9.0% (5.0 to 13.5) | — | 8.876 (4.70 to 13.17) / 9.039 (4.97 to 13.47) |
| Framework v2.0, 29 / 30 | 9.4% (4.5 to 14.4) / 9.9% (5.2 to 14.7) (12) | 9.378 / 9.863 | 9.378 (4.46 to 14.42) / 9.863 (5.16 to 14.74) |
| Benchmark P, 37 feasible / v2.0 29 | "≥ 0.53" (16) | 0.530 / 0.90 | 0.536 / 0.907 |

### Figure 2C: all values (s31, 54 items, mean across 31 trials; every arm has k = 31)

| Level | Unmatched | PS alone | + ECG | + CLMBR-T | + both | + ECG reduction, % (CI) | + CLMBR-T reduction | + both reduction |
|---|---|---|---|---|---|---|---|---|
| PS-Demo | 0.14281 | 0.14084 | 0.12587 | 0.11189 | 0.10568 | 10.6 (5.3 to 15.6) | 20.6 (12.9 to 28.5) | 25.4 (18.2 to 32.4) |
| PS-CVD5 | 0.14281 | 0.12857 | 0.11744 | 0.11198 | 0.10974 | 8.7 (4.2 to 13.5) | 12.9 (7.6 to 18.3) | 14.6 (7.7 to 21.1) |
| PS-CVD10 | 0.14281 | 0.11841 | 0.11391 | 0.11000 | 0.11001 | 3.8 (−1.6 to 9.0) | 7.0 (1.2 to 12.6) | 6.9 (0.3 to 13.3) |
| PS-Clinical (no LVEF, MI) | 0.14171 | 0.11791 | 0.11403 | 0.11273 | 0.11386 | 3.3 (−1.1 to 7.5) | 4.4 (0.3 to 8.6) | 3.4 (−1.9 to 8.5) |
| hdPS | 0.14281 | 0.11416 | 0.10558 | 0.11277 | 0.10380 | 7.1 (0.7 to 12.8) | 0.6 (−7.0 to 7.4) | 8.5 (2.0 to 14.7) |

All 25 levels and 45 relative-change values (point and CI) equal `figure2_values.json` to ≤ 5e-7 (levels) and ≤ 5e-4 percentage points (relative changes; the JSON is rounded to 4 decimals). They also equal S31_RESULTS §2. The PNG labels read −10.6 / −8.7 / −3.8 / −3.3 / −7.1%; the axes read "31 trials".

Other Figure 2 panels:
- 2A: all 54 × 3 item medians match to ≤ 5e-5 (JSON rounding).
- 2B: all 8 domains × 3 arms match to ≤ 5e-7.
- 2D: 19 of 31 improved, mean +3.35 points, P = .0152 ("P = .02"), matching.

### Ladder + ECG, six methods, domains, \|Δ log HR\| (s31; deck slides 9 / 12 / 16 / 17)

| Quantity | Deck | Verifier |
|---|---|---|
| PS-Demo / CVD5 / CVD10 / Clinical / hdPS + ECG, P | 10.6 (P < .001) / 8.7 / 3.8 (.09) / 3.3 (.079) / 7.1 (.01) | 10.63 (.0005) / 8.65 / 3.79 (.095) / 3.29 (.079) / 7.13 (.015) |
| Trials lower (explorer) | 25/31, 20/31, 22/31, 18/31, 21/31 | 25, 20, 22, 18, 21 |
| 1:1 cal. 0.1 / 1:3 / IPTW / overlap / GBM | 7.6 (3.1 to 12.5) / 6.2 (2.8 to 9.9) / 5.1 (1.6 to 8.8) / 7.5 (4.4 to 11.0) / −1.5 (−8.0 to 4.2) | 7.56 (3.09 to 12.49) / 6.20 (2.76 to 9.91) / 5.13 (1.58 to 8.84) / 7.45 (4.44 to 11.03) / −1.46 (−7.99 to 4.21) |
| Domains (Fig 2B and S31_RESULTS): vitals / other labs / LV structure / LV function / diastolic / RV / valves / echo-35 | 8.5 / 6.5 / 15.0 / 16.1 / 16.0 / −2.2 / 3.7 / 9.1 | 8.50 / 6.53 / 14.97 / 16.11 / 16.02 / −2.16 / 3.73 / 9.08 (CIs equal to 1e-6) |
| CVD10 + ECG benchmark P | P < .001 (16) | 0.0006 (builder 0.00075) |
| PS-Clinical + ECG benchmark P | — | 0.0032 (builder 0.0028) |
| 32-trial ladder (S31_RESULTS brackets) | 11.3 / 8.8 / 5.0 / 3.2 / 7.6 | 11.3 / 8.85 / 5.0 / 3.2 / 7.6 (every S32 row exact) |

### Agreement by v19 tier among the 37 feasible (slide 13)

| Group | Deck (n, r, est., std., \|Δ\|, closer, benchmark P), PS alone / + ECG | Verifier |
|---|---|---|
| Excellent + Good | 14; .63 / .69; 43% / 79%; 71% / 86%; .230 / .176; 9/14; 0.48 | 14; .631 / .691; 42.9 / 78.6; 71.4 / 85.7; .2296 / .1760; 9; 0.482 |
| Moderate | 17; .50 / .48; 47% / 59%; 76% / 71%; .235 / .217; 11/17; 0.63 | 17; .496 / .484; 47.1 / 58.8; 76.5 / 70.6; .2346 / .2169; 11; 0.626 |
| Limited | 6; −.05 / −.12; 0% / 17%; 33% / 33%; .211 / .192; 3/6; 0.86 | 6; −.046 / −.123; 0 / 16.7; 33.3 / 33.3; .2110 / .1916; 3; 0.865 |
| All-38 option, Excellent + Good | 15; .65 / .70; 47% / 80%; 73% / 87%; .216 / .171; 9/15; 0.65 | 15; S32 column of S31_RESULTS §4 reproduced exactly |

### Counts

| Quantity | Deck / figures | Verifier (from `docs/v19/quality_tiers.json`) |
|---|---|---|
| Flow | 99 → 37 → 31 (slide 6, overview) | 38 − PROTECT AF = 37; 32 − PROTECT AF = 31 |
| Tiers of the 37 | 3 / 11 / 17 / 6 (slide 6, popup, overview, explorer options) | 3 / 11 / 17 / 6 (of the 38: 3 / 12 / 17 / 6) |
| Areas of the 31 | AF 11, Diabetes 7, HF 5, Other 4, Hypertension 2, ACS / MI 2 | identical |
| Robustness "11 of 12" and "5–10%" | slide 12 | 11 of 12 positive (GBM is the exception); range floor(5.13) to ceil(9.86) |

Not independently recomputed, because their cells are not among the three sources:
- CV-tuned penalty 5.2%;
- index-day exclusion 7.8%;
- spec-v2 fixes 7.0% and random removal 6.7 (2.6 to 9.0);
- MI single-draw range;
- comparator-cluster P .002;
- plasmode and MIMIC.

These match S31_RESULTS and the builder's claims table (424 of 424 checked claims match).

## Issues

### BLOCKING

None.

### MINOR

1. **The emulation explorer's benchmark-permutation P depends on the sort order (slide 11).**
   - Expected: about 0.55 (S31_RESULTS 0.56; precise 0.549).
   - Found: the "+ ECG" row reads 0.54 with the default sort (area), 0.55 sorted by name and 0.56 sorted by RCT HR.
   - Cause: the JS Monte Carlo (`benchShuffle`, fixed seed, 20,000 draws) permutes trials in display order. The spread is within MC error, but the same quantity changes when the user re-sorts.
   - Fix: sort the trial list by index before `closer()` / `benchShuffle`, or use more draws.
2. **Hand-entered index-day share (slide 7 popup "PS and matching").**
   - Found: "index day included, 37% of ECGs". The source is `docs/v1_criteria_check/TRIAL_CRITERIA_CHECK.md` (median across S32 trials); the claims table marks it HAND.
   - Not recomputed on s31. The value is likely about the same, but it is not s31-sourced.
   - Fix: recompute on s31 or label it "(32-trial median)".
3. **PS-Demo mask on the 58-item panel: pipeline.md vs deck/builder.**
   - pipeline.md §6 row "PS-Demo, CVD10": `B_mean` and the prognostic score are masked on the 58.
   - The builder (`LEAK_RUNG["P1"] = []`), the explorer (58 panel, PS-Demo: "Nothing extra to mask", 58 shown) and slide 8 ("PS-Demo none none") mask nothing. DEFECT_IMPACT.md §1, which pipeline.md cites, has no PS-Demo row.
   - This is not caused by s31 and affects only the secondary panel.
   - Fix: correct pipeline.md, or add the mask.
   - Slide 8's masking table also has no "+ CLMBR-T" row (pipeline: none on the 54, all 4 coded on the 58), although CLMBR-T is shown in Figure 2C.
4. **Limited-tier Pearson r in `s31_numbers.json`** differs from the cell-level value by 2–3e-6 (−0.045824 vs −0.045821; −0.122570 vs −0.122568), apparently because it comes from the deck's rounded embedded estimates. It is invisible at the 2 decimals shown. Informational.
5. **A2 quality viewer default filter is "All 38 emulated".** This falls under the allowed exception (an appendix table of all emulated trials), and "Analysed (31)" is an option, so it conforms. The filter counts are correct: 38 rows / 31 analysed / 7 excluded (6 Limited + PROTECT AF).
