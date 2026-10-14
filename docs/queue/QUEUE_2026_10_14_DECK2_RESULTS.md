# Results: queue 2026-10-14, second deck-edit job (deck2)

Queue file: `docs/queue/QUEUE_2026_10_14_DECK2.md`. Log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-deck2-20261014/STATUS.md`. Builder: `scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`.

## 0. First: the s31 job was finished

The s31 job had **not** finished cleanly. Its session was terminated at the 600 s background-wait limit while its verifier was still running: there was no results file, no verify report and no commit. This job completed its Steps 6–7 before making any deck edits.
- **Verification:** a fresh verifier rechecked the deck. **PASS with minor issues, no BLOCKING issues.** Report: `docs/presentation/VERIFY_LAB_DECK_2026_10_15_S31.md`.
- **Commit:** local commit **0d6562c**, covering the s31 scripts, `docs/s31/`, Figure 2, the overview figure, the deck and the report.
- **Summary:** `docs/queue/QUEUE_2026_10_14_S31_RESULTS.md`, also added at the top of the s31 STATUS.md.

The deck edits below are local commit **3c567a6**. Nothing was pushed.

## 1. What changed, per slide (on-screen numbers before the edits)

| Slide | Change |
|---|---|
| **4 Aims** | **Click 2** (after aim 1) shows a graphic with two paths, both feeding into **propensity score matching**:<br>• **ECG embedding:** raw ECG waveform (12-lead) → AI-ECG encoder → embedding vector<br>• **EHR embedding:** coded patient timeline (diagnoses, drugs, procedures over time, up to index) → CLMBR-T, "EHR foundation model (coded history)" → embedding vector<br>Aim 1 stays highlighted while the graphic shows. **Click 3** hides the graphic and reveals aim 2; aims 3 and 4 follow as before. |
| **6 Pipeline** | The old **A1 (trial selection)** and every link to it are removed.<br>The feasibility popup keeps the numbered criteria (≥ 350 with an ECG in the smaller arm), examples, the size-rule note, and designs and dates.<br>"Ratings from design information only, blind to all emulation results" is removed from the slide, and "(design information only, blind to results)" from the quality popup.<br>Links now go to A1 (quality viewer) and A2 (Table 1). |
| **Table 1** | One appendix slide (**A2**) holds all 38 trials in a scroll box. The header row is sticky, and the box always opens at the top, including when you return to it.<br>PROTECT AF is marked "excluded at feasibility (smaller arm < 350)". The 31 analysed have a red bar and a red "yes"; excluded trials are grey. |
| **7 PSM experiments** | The old **A6 (design history)** link is removed.<br>"logistic PS" becomes **"Ridge (L2) logistic regression"** on the strip, and "L2-penalised logistic regression" becomes the same in the popup.<br>The order is now PS-Demo → PS-CVD5 → PS-CVD10 → **PS-Clinical → hdPS**, and the reveal follows it.<br>The label "PS-Clinical (no LVEF)" is now "PS-Clinical", in the popup title too. The popup has one plain line, "LVEF and echo are never PS inputs."; the other LVEF wording is dropped. |
| **8** | Retitled **"Methods: covariate balancing"**. It shows two cards:<br>• **Endpoints:** the primary relative reduction in mean \|SMD\| over the 54 held-out items, with its formula; secondary % \|SMD\| < 0.1.<br>• **Tests:** paired by trial; bootstrap CI (4,000 trial resamples); exact sign-flip; permuted-ECG placebo.<br>A bottom-left "More:" link goes to the new **A3**, which has a back-link. |
| **New A3** | The held-out characteristics list, the leakage-corrected masking table and its rules, moved from slide 8.<br>Additions: a "+ CLMBR-T (any level): none / all 4 coded items" row (pipeline.md §6), and the agreement-endpoint line from slide 8 as a note. |
| **9 ↔ 10** | Swapped. **Slide 9 = Figure 2**, retitled "Results 1: covariate balance (Figure 2)"; **slide 10 = the balance explorer**, retitled "Results 2: …". |
| **Figure 2** | Built from the four per-panel PNGs. Each panel is positioned where it sits in the full figure (located by image matching; white made transparent). The shared legend is cropped from the full figure and shown from the start.<br>Click 1 shows A + B, click 2 shows C, click 3 shows D. The subtitle / source line is removed. |
| **Appendix** | Renumbered, and all links and back-links are generated from one registry. Slide 5 stays empty. All other slides, animations, popups and explorers are unchanged: the verifier compared their visible text with 0d6562c, and the embedded data block is byte-identical. |

## 2. New slide order and appendix numbering

1 Title · 2 Background · 3 Problem · 4 Aims · 5 Study overview (empty) · 6 LATENT-RCT pipeline · 7 PSM experiments · 8 Methods: covariate balancing · **9 Results 1: Figure 2** · **10 Results 2: balance explorer** · 11 Results 3: emulation explorer · 12 Robustness · 13 Agreement by quality · 14 Plasmode · 15 MIMIC-IV · 16 Take-home · 17 Open decisions.

| New | Content | Old |
|---|---|---|
| A1 | Emulation-quality criteria + quality viewer | A2 |
| A2 | All 38 emulated trials (Table 1, scrollable) | A3 + A3b |
| A3 | Held-out panel and leakage-corrected masking | new (from slide 8) |
| A4 | Framework v2.0 (sensitivity) | A4 |
| A5 | Spec-v2 cohort fixes (sensitivity) | A5 |
| — | Trial selection; design history | A1, A6 (removed) |

## 3. Verification

The report is `docs/presentation/VERIFY_LAB_DECK_2026_10_15_EDITS2.md`, from a fresh verifier subagent that built nothing. **Verdict: PASS with minor issues; no BLOCKING issues, so no fix rounds were needed.**
- All 7 edits are confirmed, with 177 screenshots of every reveal step on slides 4, 6, 7 and 9, and of all 5 popups.
- Nothing links to or mentions the old A1 / A6. The old hashes #A6 and #A3b fall back to slide 1.
- The full table is reachable, and it opens at the top even after being scrolled.
- Navigation works at 1920×1080 and 1366×768: 51 slide/step states, 22 hash labels, and 13 cross-links with their back-links.
- There were 0 console or page errors.
- 33 numbers match `docs/s31/S31_RESULTS.md` and `figure2_values.json`, including the primary 8.7% (4.2 to 13.5), 20/31.
- The privacy scan is clean.
- The 10-09 deck and both older builders are unchanged.
- The builder's claims table has 418 of 418 checked claims matching, and the 10-09 deck regenerates byte-identical.

## 4. For you to check

1. **"PS-Clinical (no LVEF)"** still appears on slides 10, 12, 16, 17, on A3 and on the Figure 2C axis. Only slide 7 was asked to change, so the naming is now inconsistent. Say if it should go everywhere (the Figure 2C label comes from `make_figure2_latent.py`).
2. **hdPS before PS-Clinical** remains in the A3 masking table and in the level menus of the explorers (slides 10, 11, 13). Only slide 7 was reordered.
3. **"Blind to results"** is gone from slide 6 and its popups, as asked. It remains on A1 (the points-rule text), on A4 ("Process and agreement"), and in the explorer captions and menus (slides 10, 11 and 13).
4. **Details no longer in the deck.** Shortening slide 8 dropped "trials improved; per-domain reductions", "one-sided vs base or placebo" and "BH-FDR within families". Everything else moved to A3 word for word.
5. **The 99-candidate breakdown is gone.** With the old A1 removed, the three waves (63 + 8 + 28) and the PRISMA coverage check no longer appear anywhere.
6. **Slide 4 goal line:** "bring unstructured information into trial emulation" is unchanged. It sits just above the new graphic, which labels CLMBR-T "EHR foundation model (coded history)". This was flagged before (2026-10-13).
7. **Two small wording choices of mine:**
   - The slide 8 link reads "A3 · Held-out panel and leakage map", while the A3 title says "…and leakage-corrected masking".
   - "Results 1" and "Results 2" were renumbered to follow the new order.
8. **Still open from the s31 verification:**
   - The slide 11 benchmark P depends on sort order (0.54 to 0.56; precise 0.549).
   - The "37% of ECGs" on the index day is the 32-trial figure.
   - The PS-Demo 58-item mask differs between pipeline.md and the builder.
9. **Next job:** the queued Figure 2D job (`claude-fig2d-20261014`) starts after this one. Figure 2 is now the per-panel slide 9, not one image on slide 10.
