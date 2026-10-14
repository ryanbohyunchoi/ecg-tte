# Figure 2D: colour trials by cardiac-physiology decision (queued 2026-10-14; runs after the deck2 job)

You are running unattended in tmux. Read `CLAUDE.md`, `handoff.md` §1 and `pipeline.md` (2026-10-14 update: the **31-trial primary set**, PROTECT AF excluded at feasibility).

**First:** read `docs/queue/QUEUE_2026_10_14_S31_RESULTS.md` and `docs/queue/QUEUE_2026_10_14_DECK2_RESULTS.md`. If either job did not finish cleanly, log it and finish only what this change needs.

**Rules:**
- The same rules as `docs/queue/QUEUE_2026_10_14_DECK2.md`.
- Write only under `/mnt/raid0/rbc58` and the repo.
- Aggregates only; no counts of 1–10 that refer to patients.
- No commits of restricted files; no push; no GPU.
- Python: `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`.
- Playwright environment variables are set inside Python (see the deck2 queue file).
- Log to `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig2d-20261014/STATUS.md` (`umask 077`).
- Don't edit `paper.md`, `paper2.md`, `table1_picot.md` or any `.docx`.

## The change

Replace the current Figure 2 **panel D** (per-trial change in % of items with |SMD| < 0.1, PS-CVD5 + ECG vs PS-CVD5, with red/grey bars by sign). Keep the same data and endpoint. Change only how the bars are coloured and labelled.

**Mock-up to match:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig2d-20261014/mockup/panelD_cardiac_grouping.png` (script `d_mock3.py` in the same folder; it reads `d_predict.json`, per-trial aggregates only).

1. **Data:**
   - Unchanged: s31; main configuration; PS-CVD5 `base` vs `ECG`; 54 leakage-corrected items.
   - Use the existing `trial_dpct()`.
   - Keep the existing `BE.pair_stats` asserts.
2. **Grouping** (descriptive, by type of treatment decision): put it in `scripts/figures/make_figure2_latent.py` as a named constant keyed by trial `full` name. Assert that all 11 are in s31.
   - **Cardiac-physiology** (11):
     - rhythm control: AF-CHF, AFFIRM, EAST-AFNET 4, CABANA, RAFT-AF;
     - HF / RAAS drug choice: PARADIGM-HF, ELITE II, TRANSFORM-HF, COMET, EMPEROR-Preserved, VALIANT.
   - **Other** (the remaining 20): anticoagulant / antithrombotic (incl. LAA occlusion), glucose-lowering, BP-lowering, lipid-lowering, NSAID.
3. **Bars:**
   - Sorted from largest to smallest change; break ties by trial name.
   - Colour: cardiac-physiology `#2f6db5`; other `#c9cbd6`.
4. **x-axis:**
   - Trial short names (as in `trials_meta`), rotated about 60°.
   - Tick labels coloured to match the bars; cardiac-physiology names in bold.
   - Drop the "Trials (sorted)" axis label.
5. **Legend** (top right; numbers computed, not typed in):
   - "Cardiac-physiology (rhythm control, HF / RAAS drugs): *a* of *n* improved; mean *+x.x* points"
   - "Other (anticoagulant, glucose-, BP-, lipid-lowering, NSAID): *b* of *m* improved; mean *+y.y* points"
6. **One small line for all 31 trials:** "*c* of 31 improved; mean *+z.z* points; P = …".
   - This is the existing overall sign-flip P.
   - **Don't show a P value or test for the group difference.**
7. **Title** "PS-CVD5 + ECG vs PS-CVD5, per trial"; y-axis label unchanged.
8. **Caption / footnote** (one short line under the panel or in the figure legend text): "Trials grouped descriptively by type of treatment decision."
9. **Expected values** (add them as checks in the script):
   - cardiac-physiology: **10 of 11 improved, mean +9.9**;
   - other: **9 of 20 improved, mean −0.3**;
   - all 31: **19 improved**.
   - If they differ, stop and log why. Don't adjust the grouping.
10. **Layout:**
    - The full figure must still fit, with no overlap or clipping. Panel D sits in the bottom row; give it the height the trial names need.
    - Regenerate the full figure (`.png`/`.pdf`) and the per-panel PNGs in `docs/paper/figures_latent/panels/`.
    - View both (Read tool) and fix any overlap.

## The deck

1. **Rebuild** `scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html` so the Figure 2 slide uses the new panel D:
   - click 3 of the reveal (A+B → C → D) shows the new panel;
   - everything else on the slide, and in the deck, stays unchanged.
2. **Clicking panel D opens a popup of other groupings.** Once panel D is revealed (click 3), clicking on it opens a popup.
   - **Use the deck's existing `popup()` mechanism** (`data-pop`; a close button, click-outside and Esc close it; arrow keys don't navigate while it is open).
   - **Add a small hint** under panel D, e.g. "Click for other groupings".
   - **The popup has tab buttons**, one view at a time, each a PNG of the same per-trial values (same endpoint, same 31 trials). Generate them from `make_figure2_latent.py`, or a new `scripts/figures/make_figure2d_groupings.py`, into `docs/paper/figures_latent/panels/panelD_groupings/`. The tabs:
     1. **Cardiac-physiology** (default; identical to panel D).
     2. **Clinical area:** AF, HF, ACS/MI, Hypertension, Diabetes, Other, from `trials_meta` `area`.
        - **Grouped layout:** bars clustered by area and sorted within each area; a dashed group-mean line; above each group, the group name plus "*k*/*n* improved, mean *±x.x*".
        - One distinct colour per area, colour-blind safe (Okabe–Ito, as in the mock-up).
     3. **Type of treatment decision** (6 groups), in the same grouped layout:
        - rhythm control (drug or ablation): AF-CHF, AFFIRM, EAST-AFNET 4, CABANA, RAFT-AF;
        - HF / RAAS drug choice: PARADIGM-HF, ELITE II, TRANSFORM-HF, COMET, EMPEROR-Preserved, VALIANT;
        - antithrombotic (incl. LAA occlusion): ARISTOTLE, ROCKET-AF, RE-LY, FRAIL-AF, ACTIVE W, AMPLIFY, PLATO, LAAOS III;
        - glucose-lowering: CANVAS, CAROLINA, CARMELINA, LEADER, EMPA-REG OUTCOME, SUSTAIN-6, TECOS;
        - BP-lowering: LIFE, INSIGHT;
        - other (statin, NSAID): PROVE IT, LODESTAR, PRECISION.
        - Assert that this covers exactly the 31.
     4. **Physiologic label** (blind labels, `docs/v21/TRIAL_LABELS.json` `physiologic`): the sorted layout, blue = yes, grey = no, legend with "*k* of *n* improved; mean".
   - **Mock-ups** (same folder as above):
     - `panelD_v3_area_grouped.png` (tab 2);
     - `panelD_v3_decision_grouped.png` (tab 3);
     - `panelD_option1_coloured_bars.png` (tab 4);
     - scripts `d_mock.py` and `d_mock2.py`.
     - **Fix the mock-ups' overlapping group titles** (BP-lowering / Other); wrap or shorten them.
   - **Every tab says "descriptive grouping".** Show no group P values.
   - **Expected values** (add them as checks):
     - area: AF 7/11, +4.5; HF 4/5, +7.4; ACS/MI 1/2, +5.5; Hypertension 1/2, −4.7; Diabetes 3/7, +0.8; Other 3/4, +2.3;
     - decision: rhythm 5/5, +12.2; HF/RAAS 5/6, +8.0; antithrombotic 3/8, −0.5; glucose 3/7, +0.8; BP 1/2, −4.7; other 2/3, +0.6;
     - physiologic: yes 9/10, +8.5; no 10/21, +0.9.
   - **Readable at 1366×768:** the popup image fits without scrolling, or scrolls cleanly.
3. **Update any deck text** that quotes the old panel D summary (e.g. "20 of 32 trials improved") to the new computed values. Also update the builder's claims table and expected values for these numbers.
4. **Speaker note or alt text, if the builder has them:** "Gains were concentrated in cardiac-physiology decisions (rhythm control, HF / RAAS drugs); descriptive grouping."

## Verification (a fresh subagent that built nothing)

The verifier checks:
- the panel D values, recomputed independently from the cells (group counts, means, the overall P);
- the grouping matches item 2 exactly;
- the panel D popup: it opens on click; each of the 4 tabs shows the right image; the tab values are recomputed independently and match the expected values; Esc, the close button and click-outside work; arrow keys don't navigate while it is open; screenshots of each tab at both sizes;
- screenshots of the Figure 2 slide at each reveal step, at 1920×1080 and 1366×768;
- no overlap or clipping in the full figure or the slide;
- 0 console or page errors;
- the other deck numbers are unchanged from the deck2 build;
- a privacy scan.

Fix BLOCKING issues and re-verify, up to 3 rounds. Report: `docs/presentation/VERIFY_FIGURE2D.md`.

## Commit and summary

1. **Commit locally:** the figure script(s), `docs/paper/figures_latent/` (including `panels/panelD_groupings/`), the deck builder, the deck and the verify report. Don't push.
2. **Add one line to `pipeline.md`'s deviations log:** "Figure 2D colours trials by cardiac-physiology decision (rhythm control, HF / RAAS drugs; descriptive grouping); endpoint unchanged."
3. **Write the summary** at the top of the status log and copy it to `docs/queue/FIGURE2D_RESULTS.md` (commit). Cover the new panel D values, what changed in the deck, and the verification verdict.
