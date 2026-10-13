# Queue 2026-10-13 (deck revision): results

Unattended run of `docs/queue/QUEUE_2026_10_13_DECK.md`, Steps 1–4. Everything is committed locally and nothing is pushed. The step log is in `/mnt/raid0/rbc58/ecg-tte/audits/claude-deckq-20261013/STATUS.md`.

**Verification:** an independent verifier passed the deck in round 1, with **no BLOCKING issues** and 9 SHOULD-FIX items. Four SHOULD-FIX items were fixed, and round 2 passed them all. Five are left for you (see the end). Report: `docs/presentation/VERIFY_LAB_DECK_2026_10_15.md`.

## Step 1: Figure 2 (updated)

**Files:**
- **Script:** `scripts/figures/make_figure2_latent.py` (new; the v20 script is unchanged).
- **Figure:** `docs/paper/figures_latent/figure2_covariate_balance.{png,pdf}` (300 dpi), plus panels A–D in `panels/`.

**Basis:** version 1 cohorts; paper 1's 32 trials (v19 tiers); 1:1 matching, caliper 0.2, C = 1; 54 held-out items with the leakage-corrected masks.

**Checks:**
- Every plotted value equals the `build_balance_explorer.py` computation on the deck's grid.
- They also match the deck's embedded explorer integers (max |SMD| deviation 4e-6).
- 71 values match the Python summaries exactly.

**Panels:**
- **A.** Love plot of the 54 items (median |SMD| across the 32 trials) for unmatched, PS-CVD5 and PS-CVD5 + ECG, grouped by domain.
- **B.** Mean |SMD| by domain. All 54 items: unmatched 0.144, PS-CVD5 0.130, + ECG 0.118.
- **C.** The PS ladder; no PS-Flags. Mean |SMD| at each level:

  | Level | Unmatched | PS alone | + ECG | + CLMBR-T | + CLMBR-T + ECG | + ECG label |
  |---|---|---|---|---|---|---|
  | PS-Demo | 0.144 | 0.143 | 0.127 | 0.114 | 0.107 | −11.3% (6.0 to 16.1) |
  | PS-CVD5 | 0.144 | 0.130 | 0.118 | 0.114 | 0.112 | −8.8% (4.4 to 13.3) |
  | PS-CVD10 | 0.144 | 0.121 | 0.115 | 0.112 | 0.112 | −5.0% (−0.8 to 10.3) |
  | hdPS | 0.144 | 0.118 | 0.109 | 0.122 | 0.104* | −7.6% (1.7 to 13.0) |
  | PS-Clinical (no LVEF, MI) | 0.143 | 0.119 | 0.115 | 0.117 | 0.116 | −3.2% (−1.0 to 7.2) |

  The + ECG labels match the expected 11.3 / 8.8 / 5.0 / 7.6 / 3.2 exactly. Relative reductions for + CLMBR-T (not labelled in the figure) are 20.7 / 12.4 / 7.4 / −3.5 / 2.2%, and for + CLMBR-T + ECG 25.8 / 13.5 / 7.0 / 8.5 / 2.7%. \*The hdPS + CLMBR-T + ECG point rests on 31 trials (one failed cell), and the figure has a footnote saying so.
- **D.** Kept, now for PS-CVD5 + ECG vs PS-CVD5: 20 of 32 trials improved, mean +3.6 points of items with |SMD| < 0.1 (53.4% → 57.0%), sign-flip P = .009.

## Step 2: what changed per slide

The deck is `docs/presentation/ecg_tte_lab_2026_10_15.html`, built by `scripts/build_lab_deck_1015.py`.
- **Slide 5 (Study overview):** the slide is kept with its number, title bar and footer. **The body is empty, for your own figure**; the overview image was removed.
- **Slide 6 (LATENT-RCT pipeline):** it builds in 5 clicks: 99 candidates → feasibility criteria → 38 → emulation-quality criteria → 32 analysed (with the tier bar) → clinical areas. The feasibility criteria are numbered 1–5. Clicking either criteria box opens a popup:
  - feasibility: the full criteria with examples and the designs and dates, as in A1;
  - quality: the v19 points rule, the ARISTOTLE / COMET / EMPA-REG / ALLHAT examples and the tier counts, as in A2.

  Each popup has a Close button and links to A1/A3 or A2/A4. The A1 table is now numbered the same way.
- **Slide 7 → "PSM experiments":**
  - The ladder graphic and PS-Flags are gone.
  - The PS levels appear one at a time: PS-Demo → PS-CVD5 (primary) → PS-CVD10 → hdPS ("200 yes/no code flags (no values, no dates)") → PS-Clinical (no LVEF).
  - Then the comparisons appear one at a time, each with an icon: 1 + ECG representation, 2 + CLMBR-T, 3 + ECG + CLMBR-T, 4 + permuted placebo.
  - Three popups give the details: **hdPS** (the 200 flags and how they are chosen; treatment-only ranking; random half held out; exposure drugs excluded), **PS-Clinical** (inputs incl. measured values; no LVEF; 5-draw MI; masks) and **PS and matching** (L2 logistic, fixed C = 1; representations; placebo; 1:1 nearest neighbour, caliper 0.2 SD of the logit, without replacement; < 11 pairs = failed).
  - The ECG and CLMBR-T details are in the PS and matching popup.
- **Slide 8 (held-out panel):** the PS-Flags row was removed from the leakage table.
- **Slide 10, "Results 2" (the balance results slide):** now only the updated Figure 2, the title "Results 2: covariate balance (Figure 2)" and a one-line source note. The "More: A4 · A5" links are kept.
- **Slide 17 (open decisions):** item 6 now notes CLMBR-T as a comparison arm (slide 7, Figure 2C).
- **A6 (design history):** a CLMBR-T line was updated, and a PS-Flags note was added. This is the only place PS-Flags appears outside the explorer.
- **Popups:** Esc, the Close button or a click outside close them. While one is open, no key reaches the deck, so arrows do not navigate. Clicking a popup trigger never advances a build.
- **Unchanged:** every other slide, all appendix links and back-links, and the explorers. The balance explorer slide is unchanged. The 10-09 deck still regenerates byte-identically, and the builder's 410 claims all match.
- **CLMBR-T** now appears in slide 7 and Figure 2C only. It is not in the take-home claims and is never called "unstructured".
- **`pipeline.md`:** one deviations-log line was appended (CLMBR-T shown again as a comparison arm).

## The slide-13 mapping

Your "slide 13" (love plot, domains, ladder) is **"Results 2"** (`s-res2`), which is **on-screen slide 10**. It was replaced with Figure 2.

On-screen **slide 13 is "Agreement with the RCTs by emulation quality"**, which is a different slide. It was **left unchanged**, and the verifier confirmed its text matches the checkpoint.

## Step 3: verification

The verifier was a fresh subagent that built nothing, and it used independent code throughout.

**Round 1: PASS on all 6 checks.**
1. All Step 2 items are implemented, with screenshots of every reveal step on slides 3, 4, 6 and 7 and of all 5 popups.
2. Navigation works: keyboard, hash URLs, all appendix links and back-links, and the popups. There are 0 console or page errors. It inspected all 24 slides at 1920×1080 and at 1366×768.
3. 30 numbers recomputed from the cells, including every Figure 2 panel value, all match.
4. Leakage: the masks match `pipeline.md` §6, and no PS input is scored as a held-out item. In the explorer, turning masking off un-masks only eGFR for PS-Clinical and leaves PS-CVD5 unchanged.
5. The slides are consistent with each other.
6. The privacy scan is clean.

**Round 2: PASS on the 4 fixed items:**
- the slide 17 wording;
- the slide 6 box borders, which were clipped at the SVG edge;
- the 31-trial footnote in Figure 2C;
- the space key, which now does nothing while a popup is open.

## Left for you

1. **Slide 5 is empty** for your own content.
2. **Slide 4 wording:** "bring unstructured information into trial emulation" sits above the aim that names CLMBR-T, so it could be read as calling CLMBR-T unstructured. It is your framing (`docs/STRATEGY.md`), so I left it. A possible rewording: "information that coded covariates miss (ECG waveforms; learned EHR representations)".
3. **PS-Flags in the explorers:** it is still a non-default option in the explorers on slides 9, 11 and 13, because the queue said to keep the explorer unchanged. Hide it if you prefer.
4. **Figure 2C label sign:** the labels show "−8.8%" as a relative change, while the text elsewhere says "8.8% reduction". Relabelling them as reductions is optional.
5. **Figure 2 readability on slide 10:** at small screen sizes, panel A's item labels are tiny. Consider adding an extra slide with panel A enlarged (`panels/figure2_covariate_balance_A.png`).
6. **Bootstrap CIs depend on trial order:** they reproduce exactly only in the cells' `idx` order (all of our code uses it). This could be stated in the Methods.
