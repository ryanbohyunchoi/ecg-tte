# Independent verification: lab deck 15 Oct 2026 (queue 2026-10-13, Step 3)

**Verifier:** a fresh subagent that built nothing. It did not modify the deck, its builders, the figure script or any data.

**Inputs checked:**
- **Deck:** `docs/presentation/ecg_tte_lab_2026_10_15.html`;
- **Figure 2:** `docs/paper/figures_latent/`;
- **Figure 2 values:** `figure2_values.json`.

**Evidence:**
- **Screenshots and scratch output:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-deckq-20261013/verify/` (screenshots in `shots/`; navigation results in `nav_results.json`; recomputed numbers in `order_idx_numbers.json`);
- **Scripts:** `/tmp/claude-0/-home-rbc58-github-ecg-tte/28c2d747-4dd0-403d-9171-f38918099ced/scratchpad/verify/`.

## Verdict

**PASS. No BLOCKING issues.**
- **Step 2:** every item is implemented as written.
- **Navigation:** keyboard, popups, hash URLs and all 17 appendix links work. There were 0 console or page errors.
- **Numbers:** every displayed number I recomputed matches my own code, run on the source cells (Figure 2 values to ±5e-5, i.e. 4-decimal rounding).
- **Masks:** the leakage-corrected masks are correct.
- **Privacy:** the scan is clean.

There are 9 SHOULD-FIX items, mostly wording and cosmetics. They are listed at the end.

**Round 2: PASS.**
- **Fixed:** SF-2, SF-3, SF-4 and SF-7, all verified.
- **Open for the user, on purpose:** SF-1, SF-5, SF-6, SF-8 and SF-9.
- **Errors:** 0 console or page errors.
- **Other slides:** text unchanged.

**Slide mapping:**
- The user's "slide 13" (love plot, domains, ladder) is **Results 2 (`s-res2`)**. It is on-screen **slide 10** and now shows only Figure 2.
- On-screen **slide 13** is "Agreement with the RCTs by emulation quality". Its text is identical to the HEAD checkpoint (unchanged).
- The balance explorer (slide 9) is also text-identical to HEAD.

## Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Step 2 items implemented | **PASS** | See the detail below. Screenshots: `shots/steps_3_s-prob_step0-4.png`, `steps_4_s-aims_step0-5.png`, `steps_6_s-pipe_step0-5.png`, `steps_7_s-meth1_step0-9.png`, `popup_6_pop-feas_step{1,5}.png`, `popup_6_pop-qual_step{3,5}.png`, `popup_7_pop-hdps_step4.png`, `popup_7_pop-clin_step5.png`, `popup_7_pop-match_step{0,9}.png` |
| 2 | Navigation, popups, layout at 1920×1080 and 1366×768 | **PASS** (notes in SF-3, SF-7, SF-8) | `nav_results.json`. Screenshots of all 24 slides at both sizes: `shots/1920_*.png`, `shots/1366_*.png`; contact sheets `shots/montage_{1920,1366}_{1-6}.png` |
| 3 | Numbers (≥25, independent code) | **PASS** | Table below. Code: `verify/numbers.py` (it imports none of `build_balance_explorer`, `build_lab_deck*` or `make_figure2_latent`) |
| 4 | Leakage masks; explorer toggle | **PASS** | Masks recovered from the cells (below). Explorer toggle screenshots: `shots/explorer_{clinical_nolvef,P5}_leak{True,False}.png` |
| 5 | Consistency across slides | **PASS** (SF-1, SF-2 and SF-5 are wording) | Text dump and HEAD-vs-new slide diff (`diffslides.py`) |
| 6 | Privacy (HTML and figures) | **PASS** | `privacy.py`, `privacy2.py`, `privacy3.py` |

**Check 1 detail:**
- **Slide 5:** title bar, number 5 and footer are kept; the body is empty; no overview figure.
- **Slide 6:**
  - Steps, in order: 99 (shown at step 0) → feasibility box (1) → 38 (2) → emulation-quality box (3) → 32 analysed plus the tier bar (4) → clinical areas (5).
  - The feasibility criteria are numbered 1–5.
  - The `pop-feas` text is identical to A1's criteria table, "Designs and dates" included. `pop-qual` has A2's rule and its 4 worked examples.
  - Each popup has a "✕ Close" button and stays inside the slide (no scrolling needed).
- **Slide 7:**
  - Titled "PSM experiments". There is no ladder graphic and no PS-Flags.
  - Steps 1–5 reveal PS-Demo → PS-CVD5 (primary) → PS-CVD10 → hdPS ("200 yes/no code flags (no values, no dates)") → PS-Clinical (no LVEF; 5-draw MI).
  - Steps 6–9 reveal, each with an icon: 1 + ECG representation, 2 + CLMBR-T, 3 + ECG + CLMBR-T, 4 + permuted placebo.
  - The three popups have the required content:
    - **hdPS:** 200 flags, how they are chosen, treatment-only ranking, random half held out, exposure drugs excluded.
    - **PS-Clinical:** inputs including measured values; no LVEF; 5-draw MI.
    - **PS and matching:** L2 logistic, fixed C = 1, 1:1 nearest neighbour, caliper 0.2 SD of the logit, without replacement, <11 pairs = failed.
- **Slide 10:** only Figure 2, the title "Results 2: covariate balance (Figure 2)" and a one-line source note (plus the deck's standard "More: A4 · A5" links).
- **PS-Flags:** absent from all main-slide prose and tables (the s-meth2 leakage-map row was removed). It remains only in the A6 note and as a non-default option in the explorers (SF-5). Explorer ladder default: P1, P5, PS10, hdPS200, clinical_nolvef (no Flags).
- **CLMBR-T:** not in the take-home slide. The word "unstructured" occurs once, on the aims slide (SF-1).
- **pipeline.md:** the deviations-log line for 2026-10-13 (CLMBR-T in the PSM-experiments slide and Figure 2C) is present.

**Check 2 detail:**
- **Keyboard:**
  - 48 ArrowRight presses visit every (slide, step) once and end on A6. 48 ArrowLeft presses return to slide 1, step 0.
  - PageDown, space and ArrowDown advance; PageUp and ArrowUp go back; Home and End work.
  - The last step plus ArrowRight goes to the next slide (slides 3, 4, 6 and 7).
- **Hash URLs:** #1–#17, #A1, #A2, #A3, #A3b, #A4, #A5 and #A6 each load the right slide. A hashchange to #A3b while the deck is loaded also navigates.
- **Links:** all 17 `a.xref` links reach their target, including the 4 inside popups (which close the popup). Every "Back to slide N" returns to the originating slide.
- **Popups (all 5):**
  - Clicking a trigger opens the popup and does not advance the build. This was tested at intermediate and final steps.
  - While a popup is open, ArrowRight, ArrowLeft, ArrowUp, ArrowDown, PageUp, PageDown, Home, End and F change nothing.
  - Esc closes the popup. Arrows navigate again after it closes.
  - The close button and a backdrop click close the popup. A click inside the box does not.
  - Enter on a focused trigger opens the popup. A hidden (not yet revealed) trigger cannot be clicked.
- **Errors:** 0 page errors and 0 console errors.
- **Layout:**
  - I inspected all 48 screenshots. Nothing overlaps.
  - The only DOM "outside the stage" hits are the explorer's lower controls on slide 9. They sit inside a scrollable `.ctrl` column (`overflow-y: auto`), identical to HEAD.
  - There are minor edge clips on slide 6 (SF-3).

## Numbers: displayed vs recomputed

**Basis of the recomputation:**
- **Cells:** version 1 cells, the PS-CVD10 cells and the PS-Clinical (no LVEF) MI cells.
- **Configuration and trials:** config `main` unless stated; 32 trials (v19, non-Limited).
- **Items and masks:** the 54 items with `ex58` plus the §6 leakage masks. Unmatched |SMD| comes from v18 `results.csv` (`full`/`none`/`unmatched`) with the rung's mask.
- **Failed cells:** `cell_failed` or `n_pairs` < 11. Only one is found: hdPS + ECG + CLMBR-T in one trial.
- **Bootstrap:** 4,000 trial resamples with `default_rng(20261001)`. Exact sign-flip by meet-in-the-middle enumeration of all 2^k sign patterns.

**Note on CIs:** the seeded bootstrap CI depends on the order of the trials. With the trials in the cells' `idx` order, every displayed CI reproduces exactly. With alphabetical order, bounds move by 0.1–0.4 points; for example, 8.8% (4.5 to 13.3). See SF-9.

| # | Number (where shown) | Displayed | Recomputed | Match |
|---|---|---|---|---|
| 1 | PS-CVD5 + ECG vs PS-CVD5, relative reduction (slides 9, 12, 16; Fig 2C) | 8.8% (4.4 to 13.3) | 8.85% (4.37 to 13.30) | ✓ |
| 2 | … mean \|SMD\| PS alone → + ECG; lower; P (slide 9) | 0.130 → 0.118; 21/32; <.001 | 0.1299 → 0.1184; 21/32; P = .0003 | ✓ |
| 3 | … % balanced; Δ pts; better; P (slide 9; Fig 2D) | 53.4 → 57.0; +3.6; 20/32; .009 | 53.40 → 57.04; +3.65; 20/32; .0090 | ✓ |
| 4 | + permuted ECG vs PS alone (slides 9, 12) | 1.0% (−2.8 to 4.8), P = .63 two-sided | 0.97% (−2.79 to 4.81), P = .628 | ✓ |
| 5 | + permuted ECG, % balanced (slide 9) | 53.4 → 54.0; +0.6; 13/32 | 53.40 → 54.03; +0.64; 13/32 | ✓ |
| 6 | ECG vs permuted ECG (slides 12, 16) | 8.0% (3.6 to 12.2) | 7.96% (3.64 to 12.18), P = .0005 | ✓ |
| 7 | ECG vs permuted across trial sets (slide 12) | 8.0 to 9.4% (five sets) | 32: 8.0; 38: 8.6; 29: 9.3; 30: 9.4 (fifth set not identified; within range) | ✓ |
| 8 | PS-Demo + ECG (slide 16; Fig 2C label) | 11.3% | 11.32% (5.97 to 16.07), P = .0002 | ✓ |
| 9 | PS-CVD10 + ECG (slide 16; Fig 2C) | 5.0% | 5.03% (−0.76 to 10.33), P = .051 | ✓ |
| 10 | hdPS + ECG (slide 16; Fig 2C) | 7.6% | 7.60% (1.75 to 13.03), P = .008 | ✓ |
| 11 | PS-Clinical (no LVEF, MI) + ECG (slides 12, 16, 17; Fig 2C) | 3.2% (−1.0 to 7.2), P = .075 | 3.21% (−0.99 to 7.20), P = .0754 | ✓ |
| 12 | Caliper 0.1 (slide 12) | 7.8% (3.2 to 12.6) | 7.8% (3.2 to 12.6) | ✓ |
| 13 | 1:3 matching (slide 12) | 6.4% (2.8 to 9.9) | 6.4% (2.8 to 9.9) | ✓ |
| 14 | IPTW (slide 12) | 4.8% (1.5 to 8.5) | 4.8% (1.5 to 8.5) | ✓ |
| 15 | Overlap weighting (slide 12) | 7.4% (4.3 to 10.9) | 7.4% (4.3 to 10.9) | ✓ |
| 16 | Gradient-boosted PS (slide 12) | −1.1% (−7.3 to 4.3) | −1.1% (−7.3 to 4.3), P = .63 | ✓ |
| 17 | "5 of 6 CIs exclude 0" (slide 12) | 5 of 6 | 5 of 6 (all but GBM) | ✓ |
| 18 | Framework v2.0 provisional 29 (slide 12) | 9.4% (4.5 to 14.4) | 9.4% (4.5 to 14.4) | ✓ |
| 19 | Framework v2.0 rescored 30 (slide 12) | 9.9% (5.2 to 14.7) | 9.9% (5.2 to 14.7) | ✓ |
| 20 | All 38, version 1 (A5) | 9.0% | 9.0% (5.0 to 13.5) | ✓ |
| 21 | Fig 2A: per-item medians across the 32 (54 items × unmatched / PS-CVD5 / + ECG = 162 values) | `figure2_values.json` A_items | max \|dev\| 5.0e-5 (rounding); medians of the item medians 0.1051 / 0.0922 / 0.0837 | ✓ |
| 22 | Fig 2B: domain means, unmatched / PS-CVD5 / + ECG | All 54: .1439/.1299/.1184; vitals: .1452/.1290/.1178; other labs: .1120/.0958/.0892; LV structure: .1322/.1192/.1014; LV function: .1922/.1948/.1629; diastolic/LA: .1456/.1176/.0987; RV/pulm: .1373/.1220/.1242; valves/aorta: .1699/.1656/.1586 | identical (max \|dev\| 4.9e-5); item counts 54/9/10/7/4/8/7/9 | ✓ |
| 23 | Fig 2C levels, unmatched / PS alone / + ECG / + CLMBR-T / + CLMBR-T + ECG | P1: .1439/.1433/.1271/.1137/.1070; P5: .1439/.1299/.1184/.1139/.1123; PS10: .1439/.1211/.1150/.1121/.1119; hdPS: .1439/.1181/.1087/.1219/.1038; PS-Clin: .1428/.1192/.1154/.1165/.1159 | all 25 values match (max \|dev\| 5e-5) | ✓ |
| 24 | Fig 2C + ECG labels | −11.3 / −8.8 / −5.0 / −7.6 / −3.2% | 11.32 / 8.85 / 5.03 / 7.60 / 3.21% reductions | ✓ |
| 25 | Fig 2C CLMBR-T arms (values JSON; plotted, not labelled) | + CLMBR-T: 20.66 / 12.37 / 7.38 / −3.54 / 2.25; + ECG + CLMBR-T: 25.81 / 13.54 / 7.00 / 8.48 / 2.74 | identical, CIs included (hdPS + ECG + CLMBR-T on 31 trials: one failed cell) | ✓ |
| 26 | Fig 2D | 20 of 32 improved; mean +3.6 points; P = .009 | 20/32; +3.648; P = .00902 | ✓ |
| 27 | Explorer, PS-Clinical (no LVEF), leakage on → off (slide 9) | 45 → 46 items; 0.119 → 0.118; 3.2% (−1.0 to 7.2) → 3.2% (−1.1 to 7.1); P .08 | eGFR only is unmasked; 3.2% (−1.1 to 7.1), P = .079; base level .1182 | ✓ |
| 28 | Explorer, PS-CVD5, leakage on vs off | unchanged (8.8%, 4.4 to 13.3) | unchanged | ✓ |
| 29 | Take-home: PS-Clinical gain "concentrated in observed LVEF and echo structure" | wording | domain reductions: LVEF 24.8% (the only unmasked vital), LV structure 7.0%, diastolic/LA 6.8%, RV 4.1%, LV function 3.0%, other labs 2.9%, valves −3.8% | ✓ (consistent) |
| 30 | v19 tiers, 3/12/17/6; areas of the 32: AF 12, diabetes 7, HF 5, other 4, hypertension 2, ACS/MI 2 (slide 6; popup) | as shown | identical (`quality_tiers.json`) | ✓ |

**Not recomputed** (other sources, outside the scope of the listed cells): the cluster sign-flip and leave-one-out values, the MI single-draw range, the spec-v2 6.6% and random-removal values, the CV-tuned, index-day and R2 sensitivities, the plasmode, MIMIC-IV and the agreement / benchmark-permutation P values.

## Leakage (check 4)

**Masks on the 54 items, recovered from the cells** (`ex58` ∪ the §6 leakage map):

| Level | Masked items |
|---|---|
| PS-Demo, PS-CVD5, PS-CVD10, hdPS (and Flags) | none |
| PS-Clinical (no LVEF) | SBP, DBP, heart rate, BMI, creatinine, K, Na, Hb (`ex58`) + eGFR (leakage map) |

**What this confirms:**
- These match pipeline.md §6.
- Every PS-Clinical measured input is masked, so no PS input is scored as a held-out item.
- LVEF and the echo items are not masked at any level, which is consistent with no PS using them. The with-LVEF `clinical` rung masks LVEF but is not used.
- The CLMBR-T and ECG arms add nothing on the 54 items.
- PS-CVD10 masks only `B_mean` (58-item panel).

**Explorer toggle (slide 9):**
- **Defaults:** leakage on.
- **PS-Clinical (no LVEF):** toggling leakage off unmasks only eGFR. It shows 46 items; the panel text changes to "Off: only the items that are themselves PS inputs are masked".
- **PS-CVD5:** the numbers stay identical.

## Privacy (check 6)

- **Embedded data:**
  - per-trial × item scaled |SMD| arrays (38 × 58);
  - unmatched |SMD|;
  - per-trial log HR and SE (`D.EST`);
  - trial metadata (name, area, tier, points, rationale, RCT log HR and SE).
- **Key search, outside the base64 images:** no `n_pairs`, `n_t`/`n_c`, `ess`, `retain`, `person_id`, `patient_id`, MRN, `hadm_id` or `dob`.
- **Visible text:** no "n = 1–10" or "k patients/pairs/events" patterns with k ≤ 10.
- **Figure files** (10 PNG/PDF): no suspicious metadata strings. Panel D shows per-trial changes in % of items (trial-level aggregates).
- **Explorer note "one PS-Flags trial" with < 11 pairs, and Fig 2C's 31-trial hdPS + ECG + CLMBR-T cell:** both state only that a cell failed, not its pair count. Acceptable.

## Round 2 (re-check after the builder's fixes)

**Scope:** only the fixed items, plus errors and unchanged claims elsewhere.

**Evidence:**
- **Screenshots:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-deckq-20261013/verify/shots_r2/`:
  - all 24 slides at 1920×1080 and 1366×768 (`{1920,1366}_NN_<id>.png`);
  - slide 6, steps 0–5, at both sizes (`{W}_slide6_step{0-5}.png`);
  - popup end states (`popup_after_*.png`, `popup_feas_after_space.png`).
- **Results:** `round2_results.json`.
- **Script:** `scratchpad/verify/round2.py`.

**Round-2 verdict: PASS. No BLOCKING issues.**

| Item | Result | Evidence |
|---|---|---|
| SF-2: slide 17, item 6 | **PASS** | It reads "CLMBR-T: back on the aims slide and as a comparison arm (slide 7, Figure 2C); how and where its results return … to be confirmed with the PI." No overflow (`1366_17_s-dec.png`). |
| SF-3: slide 6 SVG edges | **PASS** | See below. |
| SF-4: Figure 2C footnote | **PASS** | See below. |
| SF-7: space key in popups | **PASS** | See below. |
| Errors, all 24 slides, both sizes | **PASS** | 0 page errors and 0 console errors. ArrowRight traversal still visits all 49 (slide, step) states and ends on A6. |
| Claims unchanged elsewhere | **PASS** | See below. |

**SF-3 detail** (`1920_slide6_step{0,5}.png`, `1366_slide6_step{0,5}.png`):
- The viewBox is now `-3 0 1198 470`.
- The rendered rects sit inside the SVG with a 3–4 px margin on each side: at 1920, rects span 70.5–1849.5 px inside an SVG at 66–1854 px.
- The "99 candidate RCTs" and "32 analysed" boxes show full borders and rounded corners at both sizes.
- The rest of the slide is scaled by 0.5%; nothing shifted visibly or clipped.

**SF-4 detail** (`docs/paper/figures_latent/figure2_covariate_balance.png`; `1920_10_s-res2.png`, `1366_10_s-res2.png`):
- **Text:** the y-axis reads "Mean |SMD| (32 trials*)". The footnote "* hdPS + CLMBR-T + ECG: 31 trials (failed cell)" sits between panel C's x-labels and panel D's title. It overlaps or clips nothing in the PNG or on slide 10.
- **Count:** 31 matches my recomputation (one hdPS + ECG + CLMBR-T cell failed: `n_pairs` < 11).
- **Values:** `figure2_values.json` still matches my code (A, B and C max |dev| ≤ 5e-5; D 20/32, +3.6, P .009).
- **Privacy:** the footnote gives no pair count.

**SF-7 detail:** I ran 176 key presses: 8 popup states on slides 6 and 7 × 11 keys (arrows, PageUp/PageDown, Home/End, space, F, Enter) × 2 focus positions (on the Close button, or inside the box).
- **Never navigated:** no key changed the slide or build step.
- **Space and other keys:** the popup stayed open for space, arrows, PageUp/PageDown, Home/End and F.
- **Enter:** it closes the popup only when focus is on the Close button. That is native button activation, and it does not navigate.
- **Esc and after:** Esc closes the popup in all 8 states, and ArrowRight navigates afterwards.

**Claims unchanged detail:**
- Of the 24 slides' visible text, only `s-dec` differs from round 1 (the SF-2 edit).
- Slide 10's text is unchanged; its figure image was regenerated with the footnote.
- No number elsewhere changed.

**Open items, confirmed as left on purpose:**
- **SF-1:** the "unstructured information" framing is the user's own (`docs/STRATEGY.md` line 8: "Show that adding unstructured information (ECG waveform embeddings, EHR foundation-model…").
- **SF-5, SF-6, SF-8, SF-9:** as stated below.

## Issues

**BLOCKING:** none (round 1 or round 2).

**SHOULD-FIX** (status after round 2 in bold):
1. **Status: open (user decision).** **Slide 4 (`s-aims`), goal line:**
   - **Problem:** "The goal of LATENT-RCT is to bring **unstructured** information into trial emulation" sits directly above Aim 1, "ECG and EHR foundation models … EHR foundation model (CLMBR-T)". It can be read as calling CLMBR-T (coded-record input) unstructured. The wording is unchanged from HEAD and may be the user's own.
   - **Fix:** confirm with the user, or reword, e.g. "to bring information that coded covariates miss (ECG waveforms; learned EHR representations) into trial emulation".
2. **Status: fixed (round 2 PASS).** **Slide 17 (`s-dec`), item 6:**
   - **Problem:** "CLMBR-T: back on the aims slide; …" is stale. CLMBR-T is now also a comparison arm on slide 7 and in Figure 2C.
   - **Fix:** "CLMBR-T: back on the aims slide and as a comparison arm (slide 7, Figure 2C); how and where its results return … to be confirmed with the PI."
3. **Status: fixed (round 2 PASS).** **Slide 6 (`s-pipe`) SVG edges:**
   - **Problem:** the "99 candidate RCTs" box (x = 0) loses its left stroke, and the "32 analysed" box (right edge = viewBox width 1192) loses its right stroke and rounded corners. See `shots/steps_6_s-pipe_step5.png`.
   - **Fix:** pad the viewBox (e.g. `viewBox="-3 0 1198 470"`), or inset both boxes by 2–3 px.
4. **Status: fixed (round 2 PASS).** **Figure 2C (and slide 10):**
   - **Problem:** the hdPS + CLMBR-T + ECG point and its relative change rest on 31 trials (one cell failed, < 11 pairs), but the axis reads "Mean |SMD| (32 trials)".
   - **Fix:** add a footnote, "hdPS + CLMBR-T + ECG: 31 trials (one failed cell)". No pair count is needed.
5. **Status: open (user decision; the queue says to keep the explorer unchanged, and PS-Flags is not a default).** **Explorers on slides 9, 11 and 13:**
   - **Problem:** "PS-Flags (supplement)" is still visible as a non-default checkbox or dropdown option. This is consistent with the A6 note and with the "explorer unchanged" instruction. On a literal reading, though, it is main-slide text.
   - **Fix:** leave as is if the user accepts it; otherwise hide supplement levels behind a "show supplement levels" toggle.
6. **Status: open (user decision; the queue asks for "labels giving the relative change", so the signed change is kept, with its caption).** **Figure 2C label sign:**
   - **Problem:** the labels read "−8.8%" ("relative change"), while every slide reports "8.8%" as a reduction. This is correct but could confuse.
   - **Fix (optional):** label as "reduction 11.3% / 8.8% / …", or keep the caption explicit, as now.
7. **Status: fixed (round 2 PASS; space now does nothing; Enter on the focused Close button still closes, natively).** **Popups and the space key:**
   - **Problem:** the Close button gets focus on open, so space activates it natively and closes the popup. It never navigates. This is acceptable.
   - **Fix (optional):** `preventDefault` on " " in the capture handler, so that only Esc, the button or the backdrop close the popup.
8. **Status: open (noted for the user).** **Slide 10 legibility:** at 1366×768, panel A's item labels render at about 6–7 px.
   - **Fix (optional):** for the talk, consider a second slide with panel A enlarged (`panels/figure2_covariate_balance_A.png`), or present panels C and D larger.
9. **Status: open (noted for the user).** **Bootstrap reproducibility:**
   - **Problem:** the seeded CIs depend on the trial order. They reproduce exactly only in the cells' `idx` order.
   - **Fix:** state "trials ordered by idx before resampling" in the methods / explorer note, or sort by trial key in all code paths.
