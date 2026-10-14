# Independent verification: second round of user edits to the LATENT-RCT lab deck (15 October 2026)

This checks queue `docs/queue/QUEUE_2026_10_14_DECK2.md` (sections "Edits" and "Verification"). The verifier built nothing in this project. Verified on 2026-10-14:
- `docs/presentation/ecg_tte_lab_2026_10_15.html` (working tree, built 12:58);
- `scripts/build_lab_deck_1015.py`.

These were compared with the pre-edit state in commit `0d6562c`, which was verified PASS in `VERIFY_LAB_DECK_2026_10_15_S31.md`.

Verifier scripts and outputs are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-deck2-20261014/verify_deck2/` (umask 077, aggregates only):
- `pre_deck.html` and `pre_builder.py`: the `0d6562c` copies;
- `static_scan.py`, `refs_scan.py`, `privacy_scan.py`: source scans;
- `dump_text.py` and `compare_text.py`: visible text of every slide and popup, new vs pre-edit (output in `compare_text.txt`);
- `functional.py`: builds, popups, walk, hashes, links, Table 1, Figure 2, explorers (output in `functional_results.json`);
- `fig2_compare.py`, `numbers_check.py`, `moved_check.py`;
- `shots/`: 177 screenshots.

## Verdict: **PASS with minor issues**

All 7 edits are done as specified, and there are no BLOCKING issues:
- no link or reference to the removed A1 / A6 remains;
- every link and back-link works at both viewport sizes;
- there are 0 console or page errors;
- the numbers are unchanged and match S31_RESULTS;
- the embedded data block is byte-identical to the pre-edit deck;
- the privacy scan is clean.

The minor issues are consistency and judgement points outside the literal scope of the edits.

New structure: 22 slides, namely main slides 1–17 and appendix A1–A5.
- Slide 9: Results 1 (Figure 2).
- Slide 10: Results 2 (balance explorer).
- A1: emulation-quality criteria and viewer.
- A2: all 38 trials (Table 1, scrollable).
- A3: held-out panel and leakage-corrected masking (new).
- A4: framework v2.0.
- A5: spec-v2 fixes.

## Edits

| # | Edit | Result | Evidence |
|---|---|---|---|
| 1 | **Slide 4: representations sub-animation** | **PASS** | **Order** (fresh page, ArrowRight; `builds` in `functional_results.json`; shots `{1920,1366}_slide4_step0–6`):<br>• step 1: aim 1;<br>• step 2: aim 1 stays highlighted and the graphic is shown;<br>• step 3: the graphic is hidden, aim 2 is shown and aim 1 is dimmed;<br>• step 4: aim 3;<br>• step 5: aim 4;<br>• step 6: all four aims undimmed, as the pre-edit final step.<br>**Content** (SVG text):<br>• ECG row: "ECG embedding": 12-lead grid (3 × 4 leads) "raw ECG waveform (12-lead)" → "AI-ECG encoder" → "embedding vector";<br>• EHR row: "EHR embedding": timeline with lanes for diagnoses, drugs and procedures, a time arrow and an index line, "coded patient timeline" → "CLMBR-T / EHR foundation model / (coded history)" → "embedding vector";<br>• both arrows → "Propensity score matching".<br>**Wording:** 16 short labels. "unstructured" does not appear in the graphic (see MINOR-5 for the unchanged goal line). The aim text is identical to the pre-edit deck. |
| 2a | **Slide 6: former A1 removed, popups keep what they need** | **PASS** | **Removed:** `a-sel` / "Trial selection" are gone from the HTML (0 hits). The slide 6 "More:" line is now "A1 · Emulation-quality criteria · A2 · All 38 trials (Table 1)". The pop-feas link is now "A2 · All 38 trials (Table 1)" (was A1 + A3).<br>**pop-feas still has:**<br>• the 5 numbered criteria, including "4. Size: ≥350 with an ECG in the smaller arm; ≥50 pooled events";<br>• examples (EMPA-REG / LEADER / TECOS proxies, DIONYSOS, PROTECT AF, ACCOMPLISH 96%, ACTIVE W vs RE-LY 69%);<br>• the 300 → 350 note;<br>• "Designs and dates" (new-user active-comparator, sequential add-on / switch, 2011–2024, COMET into 2025).<br>The text is identical to pre-edit apart from the link (shot `*_popup_slide6_pop-feas.png`). |
| 2b | **"Blind to results" wording removed from slide 6 and its popups** | **PASS** | **Removed from slide 6:** the SVG line "Ratings from design information only, blind to all emulation results."<br>**Removed from pop-qual:** "(design information only, blind to results)"; its text now starts "Points: design flags …".<br>No "blind" remains on slide 6 or in either popup.<br>**Still present elsewhere** (outside the stated scope, see MINOR-3): A1, and the slide 11 / slide 10 explorer text. |
| 2c | **Table 1 complete in one place** | **PASS** | **One slide:** A2 is a single scrollable table (`.t1scroll`, 526 px visible of 927 px, sticky header). It has 38 rows, identical in content and order to the pre-edit A3 + A3b.<br>**Scrolling:** the mouse wheel reaches the end at both sizes, and the last row (PROVE IT-TIMI 22) is visible (`*_A2_table_bottom.png`). The footer says "Scroll for all 38 trials".<br>**PROTECT AF:** grey row, sub-label "excluded at feasibility (smaller arm < 350)", In 31 = "no".<br>**The 31 analysed:** 31 rows with class `an`, a red left bar, and a bold red "yes" (7 rows show "no").<br>**Landing at the top:** scrollTop = 0 with the first row visible, after first scrolling to the bottom, for all of these entry routes:<br>• slide 6 "More:" link;<br>• pop-feas link;<br>• back-link then the link again;<br>• ArrowLeft from A3;<br>• ArrowRight from A1;<br>• hashchange.<br>Both sizes pass. Slide 7 has no Table 1 link, and had none before. |
| 3 | **Slide 7** | **PASS** | **A6 link:** "More: A6 · Design history" removed; slide 7 has no xref.<br>**Ridge wording:**<br>• strip: "PS and matching: Ridge (L2) logistic regression, C = 1 · …" (was "logistic PS");<br>• pop-match: "PS model: Ridge (L2) logistic regression on standardised covariates" (was "L2-penalised logistic regression").<br>**Order** (DOM and reveal steps 1–5): PS-Demo → PS-CVD5 → PS-CVD10 → PS-Clinical → hdPS. Steps 6–9 (comparisons) are unchanged.<br>**"No LVEF" wording:** labels now read "PS-Clinical", and the pop-clin title is "PS-Clinical: inputs". The popup line "No LVEF and no echo measurement in any PS: echo is the held-out test domain." became "LVEF and echo are never PS inputs.". The MI line lost "; LVEF neither imputed nor used" (consistent with the spec).<br>**Popups:** pop-hdps is unchanged. All 3 slide 7 popups open, close and block keys at both sizes. |
| 4 | **Slide 8: "Methods: covariate balancing", details moved to new A3** | **PASS** | **Title:** "Methods: covariate balancing".<br>**Endpoints:** primary is the relative reduction in mean \|SMD\| over the 54 held-out items, with the formula; secondary is % of items with \|SMD\| < 0.1.<br>**Tests:** paired by trial; bootstrap CI (4,000 resamples of trials); exact sign-flip; placebo (permuted ECG).<br>**Links:** bottom-left "More: A3 · Held-out panel and leakage map" → A3; "Back to slide 8" returns to slide 8.<br>**Moved to A3, verbatim** (`moved_check.py`):<br>• the held-out characteristics table (9 / 10 / 7 / 4 / 8 / 7 / 9 → 54; 4 coded → 58);<br>• the leakage map;<br>• the rules;<br>• "Items are used only where they are observed in both compared cells";<br>• the agreement (secondary) note.<br>**Added on A3:** row "+ CLMBR-T (any level): none / all 4 coded items" (consistent with pipeline.md §6; it closes part of the earlier MINOR-3).<br>**Dropped, intentionally shortened:**<br>• "trials improved; per-domain reductions" (secondary endpoints);<br>• "(one-sided vs base or placebo); BH-FDR within families".<br>These now appear nowhere in the deck (MINOR-4). |
| 5 | **Slides 9 / 10 swapped** | **PASS** | Slide 9 is `s-res2` "Results 1: covariate balance (Figure 2)"; slide 10 is `s-bal` "Results 2: covariate balance explorer". Explorer text, all select options and data are otherwise identical to pre-edit.<br>**Explorer controls:** every select option changes the output, except "Physiology only" on the 54-panel (expected). The ladder checkboxes and quick-view radios have no effect in the default Love-plot view (expected, as in the earlier verification).<br>**Defaults:** v1 / s31 / main / PS-CVD5 / 54 / leakage on; "+ ECG 0.129 → 0.117, 20/31, < .001, 8.7%, 4.2 to 13.5". |
| 6 | **Figure 2 slide** | **PASS** | **Reveal:** at step 0 only the legend; click 1 shows A and B together; click 2 shows C; click 3 shows D (computed opacity and visibility at both sizes; shots `*_slide9_step0–3`).<br>**Built from the per-panel PNGs** (`figure2_covariate_balance_{A–D}.png`, committed in 0d6562c, unchanged): each decoded embedded panel equals its PNG resized (r ≥ 0.9999, mean \|diff\| ≤ 0.12 grey levels).<br>**Layout:** the final-state 2× screenshot of the panel box equals the full figure resized (aspect 1.3143 vs 1.3151; r = 0.907, mean \|diff\| 4.1 of 255). The amplified difference image shows only anti-aliasing outlines, with no shifted, doubled or missing element (`shots/fig2_deck_vs_full_absdiff.png`, `fig2_deck_vs_full_side_by_side.png`).<br>**Text:** the source line "Version 1 cohorts · 31 trials …" and the `.fig2src` element are gone. The title is "Results 1: covariate balance (Figure 2)". The legend (Unmatched / PS alone / PS + ECG / PS + CLMBR-T / PS + CLMBR-T + ECG) is shown from step 0. |
| 7 | **Appendix renumbered; links updated; rest unchanged** | **PASS** | **Labels:** A1 a-qual, A2 a-t1, A3 a-panel, A4 a-fw, A5 a-fix.<br>**Updated references:**<br>• slide 13 "More: A1";<br>• slide 12 rows "(sensitivity; A5)" and "(sensitivity; A4)";<br>• pop-qual "(A4)";<br>• A4 "primary: v19 tiers, A1".<br>**Default back-links:** A1 / A2 → 6, A3 → 8, A4 → 9 (Figure 2, as before), A5 → 12.<br>**Slide 5:** still empty (25 chars: title, number, footer).<br>**Unchanged slides:** visible text, SVG text and select options are identical to pre-edit for slides 1, 2, 3, 5, 11, 12, 14, 15, A5.<br>**The only differences elsewhere:**<br>• slide 4: the graphic;<br>• slide 6: link line, "blind" line;<br>• slide 7: as in row 3;<br>• slide 8: as in row 4;<br>• slides 9 / 10: title and number, source line;<br>• slide 13: A2 → A1;<br>• slides 16 and 17: "More: A6" removed;<br>• A1: label;<br>• A2: title "All 38 emulated trials (paper Table 1)", 38 rows, footer;<br>• A4: A2 → A1, "Back to slide 9";<br>• popups: as above.<br>The data block `const D` is byte-identical (`compare_text.txt`, `privacy_scan.py`). |

## Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Screenshots of every reveal step and popup | **PASS** | **Reveal steps**, both sizes: slide 4 steps 0–6, slide 6 steps 0–5, slide 7 steps 0–9, slide 9 steps 0–3 (`{size}_slide{N}_step{k}.png`).<br>**Popups**, both sizes: pop-feas and pop-qual (slide 6); pop-clin, pop-hdps and pop-match (slide 7) (`{size}_popup_*.png`).<br>**Walk:** 51 states × 2 sizes (`{size}_walk_*.png`).<br>**Table 1:** top, middle, bottom and landing after a scroll. |
| 2 | No link or reference to the removed A1 / A6 | **PASS** | Source (base64 stripped): 0 hits for `a-sel`, `a-hist`, `a-t1b`, `A3b`, `A6`, "Design history", "Trial selection", "PRISMA", "three waves".<br>All 18 `data-goto` and hrefs point to existing slides; the remaining "A1" references are to the new A1 (quality criteria).<br>Rendered text of all slides (all builds), all popups and every explorer option has no stale label.<br>Hash `#A6` / `#A3b` falls back to slide 1, with no error. |
| 3 | Navigation, links, back-links at 1920×1080 and 1366×768 | **PASS** | **ArrowRight walk:** 51 slide/step states in the expected order at both sizes; it stops at the end, and ArrowLeft returns to (0, 0).<br>**Hash entry:** all 22 labels land correctly at both sizes (fresh page, then reload).<br>**Xref links:** all 13 non-back links clicked at both sizes (slide 6 ×2, pop-feas, pop-qual ×2, slide 8, slide 9 ×2, slide 10 ×2, slide 12 ×2, slide 13). Each lands on its target, closes its popup, and sets the hash.<br>**Back-links:** each is labelled with its origin ("Back to slide N", href `#N`) and returns there.<br>**Popups:** open without advancing (also at their own build step); stay inside the viewport; close with Esc, the button or the backdrop; stay open on an inside click; block navigation keys.<br>**Overflow:** none outside the stage on any slide or step at either size. |
| 4 | 0 console or page errors | **PASS** | 0 in every run: text dumps of both decks, and the functional run (≈ 140 page loads at both sizes, including explorer control sweeps). |
| 5 | Default numbers match S31_RESULTS | **PASS** | 33 strings checked on slides 10, 11, 12, 13, 16 and 17.<br>**Primary and placebo:**<br>• explorer default 8.7%, 4.2 to 13.5, 20/31;<br>• ECG vs permuted 8.3% (4.0 to 12.7); permuted 0.4%;<br>• 32-trial 8.8% (4.4 to 13.3);<br>• framework v2.0 9.4% (4.5 to 14.4) / 9.9% (5.2 to 14.7).<br>**PS methods:** caliper 0.1 7.6% (3.1 to 12.5); 1:3 6.2% (2.8 to 9.9); IPTW 5.1% (1.6 to 8.8); overlap 7.5% (4.4 to 11.0); GBM −1.5% (−8.0 to 4.2).<br>**Other robustness rows:** CV penalty 5.2%; index day 7.8%; spec-v2 7.0%; PS-Clinical 3.3% (−1.1 to 7.5), P .079; 11 of 12; 5–10%.<br>**Take-home:** 3.8%, 7.1%, 0.53.<br>**Agreement (slide 13):** 0.63, 0.48, 0.86, 9/14, 11/17, 3/6.<br>**Slide 11:** 0.54.<br>All are present, and each equals S31_RESULTS §1–5 and the pre-edit deck.<br>**Figure 2** (`figure2_values.json`): C −10.6 / −8.7 / −3.8 / −3.3 / −7.1% with k = 31; D 19/31, +3.3, P .015 → ".02"; the panels are pixel-identical to the validated PNGs (Edit 6).<br>**Claims table** (`deck/claims.csv`, 420 claims): 418 match; 2 are definition-only (take-home agreement on the 37, no independent copy), as before. |
| 6 | Privacy scan | **PASS** | No `n_pairs`, ESS, retention or retain, person or patient ids, MRN or DOB. The 3 "n_t" hits are item names or comments.<br>"N pairs" phrases occur only as the rule "fewer than 11 matched pairs" (×3, unchanged).<br>The new content (aims graphic, slide 8, A3, Table 1) holds no patient counts.<br>JSON key set and `const D` are identical to the pre-edit deck. |
| — | 10-09 deck and old builders unchanged | **PASS** | `git diff --quiet` is empty against both `0d6562c` and HEAD for `docs/presentation/ecg_tte_lab_2026_10_09.html`, `scripts/build_lab_deck.py` and `scripts/build_lab_deck_v2.py`. `docs/paper/table1_picot.md` shows as modified, but its mtime is 2026-10-06 (the user's working copy, which the builder reads); this job did not touch it. |

## Issues

### BLOCKING

None.

### MINOR (cosmetic or judgement)

1. **The "no LVEF" label remains outside slide 7.** "PS-Clinical (no LVEF)" still appears in these places:
   - slide 12 MI row;
   - slide 16 take-home;
   - slide 17 open decisions;
   - A3 masking table;
   - slide 10 explorer options and legend ("PS-Clin. (no LVEF)");
   - the Figure 2C axis, "PS-Clinical (no LVEF, MI)", which is in the PNG.

   The spec limits the edit to slide 7 labels, so this conforms. Slide 7 now reads "PS-Clinical" while the rest of the deck reads "PS-Clinical (no LVEF)". Change it everywhere only if the user wants uniform naming.
2. **The level order is unchanged outside slide 7.** The A3 masking table and the slide 10 / 11 / 13 rung selects still list hdPS before PS-Clinical. Only slide 7 (and Figure 2C) use the new order. If wanted, reorder `LEAK` rows in `s_apanel` and the rung option lists.
3. **"Blind to results" wording remains outside slide 6.** It appears in these places:
   - A1, the qrule header "Points (design information only, blind to results)";
   - A1, "Two independent raters, blind to results, scored …";
   - slide 11 explorer note "Tiers were assigned from design information, blind to the results";
   - the slide 10 explorer optgroup "Physiologic label (LLM, blind to results)".

   This conforms to the spec's scope (slide 6 and its popups), but A1 is the first link from slide 6. If the user's intent was deck-wide, remove it there too (use the same `QRULE.replace` in `s_a2`).
4. **Some methods details are no longer anywhere in the deck.** Shortening slide 8 dropped them, and A3 did not take them over:
   - secondary endpoints "trials improved; per-domain reductions";
   - "one-sided vs base or placebo";
   - "BH-FDR within families".

   This is intentional under the spec. If they should stay findable, add one line to A3.
5. **The slide 4 goal line still says "unstructured".** It reads "The goal of LATENT-RCT is to bring unstructured information into trial emulation." The line is unchanged and is not in the graphic, and CLMBR-T itself is never called unstructured. It sits directly above the graphic labelled "EHR foundation model (coded history)", so the user may want to reword it (e.g. "rich, high-dimensional information").
6. **Link label and title differ.** The slide 8 link reads "A3 · Held-out panel and leakage map", but the A3 title is "Held-out panel and leakage-corrected masking". This is cosmetic.
7. **Former A1 / A6 content is no longer in the deck.** The A1 content was the three candidate waves (63 + 8 + 28 = 99; range 99–104) and the PRISMA coverage check; the A6 content was the design history (R2 4.7%, fixed cohorts 6.6% vs 8.8%). This is intentional. The "99 candidate RCTs" on slide 6 now has no breakdown in the deck.
8. **Earlier MINOR issues carried over unchanged** (not introduced by these edits):
   - slide 11 benchmark P depends on the sort order (0.54 by default vs 0.56 in S31_RESULTS);
   - hand-entered "37% of ECGs" in pop-match;
   - PS-Demo mask on the 58: pipeline.md vs the builder.
