# Results: Figure 2D, trials coloured by cardiac-physiology decision (queue `docs/queue/figure2D.md`, 2026-10-14)

Log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig2d-20261014/STATUS.md`. Both earlier jobs had finished cleanly (s31: PASS with minor issues, completed by the deck2 job; deck2: PASS with minor issues), so the full change was made. Committed locally; nothing pushed.

## New panel D

Same data and endpoint as before: s31, main configuration, PS-CVD5 + ECG vs PS-CVD5, change in % of the 54 leakage-corrected items with |SMD| < 0.1, from `trial_dpct()` with the `BE.pair_stats` asserts kept.

| Group (descriptive, by type of treatment decision) | Improved | Mean change (points) |
|---|---|---|
| Cardiac-physiology: rhythm control (AF-CHF, AFFIRM, EAST-AFNET 4, CABANA, RAFT-AF); HF / RAAS drug choice (PARADIGM-HF, ELITE II, TRANSFORM-HF, COMET, EMPEROR-Preserved, VALIANT) | **10 of 11** | **+9.9** |
| Other (anticoagulant / antithrombotic incl. LAA occlusion, glucose-, BP-, lipid-lowering, NSAID) | **9 of 20** | **−0.3** |
| All 31 | **19 of 31** | **+3.3**; P = .02 (exact one-sided sign-flip, .015; unchanged) |

All match the queue file's expected values exactly; the script stops if they differ (`EXPECT_D`). No P value or test for the group difference is shown.

**What changed in the figure:**
- **Bars:** sorted from largest to smallest change, ties broken by trial name. Cardiac-physiology bars are `#2f6db5`, other bars `#c9cbd6`.
- **x-axis:** trial short names at 60°. Cardiac-physiology names are blue and bold; the "Trials (sorted)" label is gone.
- **Text:** the legend (top right) gives the group counts and means, computed in the script. One line covers all 31 trials. The footnote reads "Trials grouped descriptively by type of treatment decision."
- **Code:** the grouping is the constant `CARDIAC_PHYSIOLOGY` in `scripts/figures/make_figure2_latent.py`, keyed by `trials_meta` full names and asserted to be in s31.
- **Layout:** the figure is now 5.85 in tall (it was 5.3), so panel D has room for the trial names. The rows are slightly closer together, and there is no overlap or clipping.
- **Regenerated:** the full figure (`.png` / `.pdf`) and all per-panel PNGs / PDFs.
- **Values file:** now `audits/claude-fig2d-20261014/figure2_values.json`. The s31 job's copy is kept.

## Popup of other groupings (new `scripts/figures/make_figure2d_groupings.py`)

There are four tabs, all showing the same 31 per-trial values. The PNGs are in `docs/paper/figures_latent/panels/panelD_groupings/`.

1. **Cardiac-physiology** (the default): drawn by the same function as panel D.
2. **Clinical area**, grouped layout: AF 7/11, +4.5; HF 4/5, +7.4; ACS / MI 1/2, **+5.6**; Hypertension 1/2, **−4.6**; Diabetes 3/7, +0.8; Other 3/4, +2.3.
3. **Type of treatment decision**, 6 groups, grouped layout: rhythm control 5/5, +12.2; HF / RAAS 5/6, +8.0; antithrombotic 3/8, −0.5; glucose-lowering 3/7, +0.8; BP-lowering 1/2, **−4.6**; other (statin, NSAID) 2/3, +0.6. The script asserts that the six groups cover exactly the 31 trials.
4. **Physiologic label** (blind labels): yes 9/10, +8.5; no 10/21, +0.9.

**Three means differ by 0.1 from the queue file** (+5.5, −4.7, −4.7). The counts and the grouping are as specified. The queue values came from the mock-up `d_mock2.py`, which hard-codes per-trial values at one decimal: (11.1 + 0.0)/2 = 5.55 and (3.7 − 13.0)/2 = −4.65. The exact means are 5.556 and −4.630, and the figure shows those, rounded. The check accepts the difference only where the mock-up's arithmetic reproduces the queue value, and it logs each case. The independent verifier confirmed this.

The mock-ups' group titles overlapped (BP-lowering / Other). They are now wrapped, the groups are spaced further apart, and an overlap assertion checks every group title and count box. Each tab says "descriptive grouping" (in the image title or footnote, and in the popup caption), and no tab shows a group P value.

## Deck (`scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`)

- **Figure 2 slide (slide 9):** click 3 now shows the new panel D. Once it is revealed, clicking it, or the hint "Click for other groupings ›" under it, opens the popup.
  - The popup uses the deck's existing `popup()` mechanism: a close button, click-outside and Esc close it, and arrow keys don't navigate while it is open.
  - It has four tab buttons, one view at a time, and always opens on the first tab. It fits without scrolling at 1366×768.
- **Speaker note:** there are no speaker notes, so panel D's alt text carries the note: "Gains were concentrated in cardiac-physiology decisions (rhythm control, HF / RAAS drugs); descriptive grouping."
- **Slide size:** the Figure 2 box is now 580 px tall (it was 560), because the figure is taller.
- **No other changes:** no deck text quoted the old panel D summary. Every other slide and the embedded data block are byte-identical to the deck2 build.
- **Claims:** 17 new claims cover every group count and mean, each checked against `pair_stats` on that group's trials, plus `EXPECT_F2D`. Of 437 claims, 435 are checked and all 435 match. The 10-09 deck still regenerates byte-identical.
- **Builder outputs:** `audits/claude-fig2d-20261014/deck`.
- **`pipeline.md`:** one line added to the deviations log.

## Verification

Report: `docs/presentation/VERIFY_FIGURE2D.md`, by a fresh verifier subagent run in the foreground. **Verdict: PASS with minor issues; no BLOCKING issues.**
- **Values:** recomputed independently from the cells, and they match. The overall P is 0.0152 by an exact sign-flip over all 2^31 patterns.
- **Groupings:** match the queue file exactly.
- **Interaction:** checked at 1920×1080 and 1366×768. Panel D and the hint appear only at click 3. The popup opens from D, from the hint and with Enter. The tabs are correct, and Esc, Close and click-outside all close it. Arrow keys, PageDown and Space don't change the slide while it is open.
- **Errors:** 0 console or page errors over all 22 slides.
- **Privacy:** the scan is clean.
- **Screenshots:** `audits/claude-fig2d-20261014/verify/shots/`.

## For you to check (minor)

1. **The three 0.1 differences** in the popup means (above). The figure shows the exact values.
2. **Tick-label colour for "Other":** the labels are text grey `#7a7c8c`, as in the mock-up, not the bar grey `#c9cbd6`, which is too faint to read.
3. **Wording in tab 1:** its image says "grouped descriptively" (the same footnote as panel D). The popup caption under every tab says "Descriptive grouping".
4. **P rounding:** the claims table records P as .015 while the figure shows .02. This was already the case before this job.
5. **Tab 2 spacing (cosmetic):** the gap between the area titles and their counts is large, and "Hypertension" sits about 1 px higher than the other titles.
6. **Files not committed:** your uncommitted `table1_picot.md`, the `.docx`, `scripts/aou/`, `tests/test_aou_stats.py`, the overview check PNG and the `*.err` files were not touched or committed.
