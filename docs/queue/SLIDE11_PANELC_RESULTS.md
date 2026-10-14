# Results: slide 11 new panel C, agreement of AI representations vs conventional PS (queue `docs/queue/slide11_figure3.md`, 2026-10-14)

Log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide11c-20261014/STATUS.md`. **Deck only:** the paper's Figure 3 (PNG/PDF, per-panel PNGs and `make_figure3_latent.py`) is unchanged. Committed locally; nothing pushed.

## New panel C (`scripts/figures/make_slide11_panelC_agreement.py`)

- **Basis:** s31 (31 trials), version 1 cohorts, main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1), log HRs of the existing cells (no refitting).
  - Demo = rung P1. Unmatched = `claude-v18-embed-compare/results.csv`, rung `none`. PS-Clinical = no LVEF, 5-draw MI.
- **Code:** the agreement part of `f4_numbers.py` / `f4_hdps.py`, copied (the audit files are untouched); style and helpers imported from `make_figure3_latent.py` / `make_figure2_latent.py`.
- **Outputs:**
  - `docs/paper/figures_latent/panels/deck/slide11_panelC_agreement.{png,pdf}`: 2215 × 830 px at 300 dpi. That is Figure 3's full width, placed bottom-aligned under A and B in the unchanged 705 × 580 figure box.
  - values: `audits/claude-slide11c-20261014/panelC_values.json`.

| Bar | Mean \|Δ log HR\| vs RCT (31 trials) | vs PS-CVD5 | vs hdPS |
|---|---|---|---|
| Unmatched (grey) | 0.248 | | |
| PS-CVD5 | 0.232 | | |
| hdPS | 0.182 | | |
| PS-Clinical† | 0.171 | | |
| Demo + ECG | 0.207 | −0.026 (P = .20) | +0.025 (P = .56) |
| Demo + CLMBR-T | 0.174 | −0.058 (P = .055) | −0.008 (P = .71) |
| Demo + ECG + CLMBR-T | 0.164 | −0.068 (P = .037) | −0.018 (P = .21) |

Labels show the paired difference in mean |Δ log HR| and the two-sided exact sign-flip P across the 31 trials, unadjusted. The footnote's benchmark-permutation P = .26 (two-sided, Demo + ECG + CLMBR-T vs PS-CVD5) comes from `recomputed_f4.json` (0.2606).

**Checks (the script stops if any fails):**
- All 7 means and 6 contrasts equal `figure4.md` and the queue file to display precision.
- They equal `recomputed_f4.json` exactly (max deviation 0).
- They equal Figure 3 panel B (max deviation 0): Demo + ECG 0.207 = PS-Demo "+ ECG"; Demo + CLMBR-T 0.174 = PS-Demo "+ CLMBR-T". PS-CVD5, hdPS and PS-Clinical also equal panel B's "PS alone" points.
- **Built-in layout check:** 25 text labels, none overlapping, nothing clipped. The stacked labels are spaced more widely than in the mock-up (two separate labels with a gap between them).

## Deck (`scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`, 25 slides)

- **Slide 11:**
  - Click 1 → A, click 2 → B, click 3 → the new full-width panel C. Same mechanism as before, with no subtitle.
  - The figure box's `aria-label` caption and panel C's alt text now describe the new panel.
  - The bottom-left line now reads "More: **A7 · Agreement by emulation quality**".
- **New appendix A7: "Agreement by emulation quality (PS-CVD5)".**
  - It is appended after A6, so no existing appendix label changes.
  - It shows the existing old panel C PNG (unchanged), centred, 480 px tall.
  - Above it, one line from `figure3_values.json`: "Mean |Δ log HR| vs RCT with PS-CVD5: Excellent + Good (14) 0.230 / 0.176 / 0.149 / 0.152 vs Moderate (17) 0.235 / 0.217 / 0.185 / 0.168 (PS alone / + ECG / + CLMBR-T / + both)".
  - "Back to slide 11" returns there.
- **Claims:** 505 in total; 503 checked, all 503 match.
  - The old panel C claims moved to A7, plus the A7 line (checked against the queue text).
  - 19 new claims on slide 11: the 7 means, and the 6 differences each with its P. Each is recomputed in the builder from the version 1 cells (Unmatched from the v18 results) and gated against `figure4.md` (`EXPECT_F3C`).
  - The 10-09 deck still regenerates byte-identical.
- **Unchanged:** vs the previous build, only slide 11 changed and A7 is new.
  - The JS and embedded data block are byte-identical, as is every other section.
  - The CSS gains 3 lines for A7. Slide 11's A and B images are byte-identical.
  - Slide 5 is still empty. The take-home slide is unchanged, with no CLMBR-T claim.
- **Builder outputs:** `audits/claude-slide11c-20261014/deck`. The previous HTML is saved in `…/prev/`.

## Verification

Report: `docs/presentation/VERIFY_SLIDE11_PANELC.md`, by a fresh verifier subagent run in the foreground. **Verdict: PASS with minor issues; no BLOCKING issues, so no fix rounds were needed.** The verifier:
- recomputed every value from the cells with its own code, including its own exact meet-in-the-middle sign-flip over all 2^31 sign vectors (all match);
- matched the colours by pixel sampling against the spec and the mock-up;
- screenshotted slide 11 steps 0–3 and A7 at 1920×1080 and 1366×768, with panel C crops. Nothing is clipped or overlapping, and the stacked labels sit 23 px apart, with 15 px to the values;
- checked every link and back-link (the new "More:" lands on A7, and A7 returns to 11), hash navigation and keyboard order;
- found 0 console or page errors over 25 slides at both sizes;
- found the wording rules met and the privacy scan clean.

Screenshots: `audits/claude-slide11c-20261014/verify/shots/`.

## For you to check

1. **Slide 14 "Agreement with the RCTs by emulation quality" overlaps the new A7.** Both show PS-CVD5 and + ECG agreement by tier; A7 adds the CLMBR-T arms. Decide whether to keep both.
2. **Text size on the slide.** Panel C is scaled like A and B. The footnote is about 9.6 px tall at 1920×1080 (6.8 px at 1366×768), and the comparison labels about 7.6 / 5.4 px. The spacing leaves room to raise those font sizes by 15–25% if you want them easier to read on a projector (verifier MINOR 1).
3. **Panel title:** a bold "C" plus "Agreement: demographics + AI representations vs conventional PS", as on the other panels, not the literal "C." prefix. The differences use the typographic minus (−).
4. **A7 image:** the existing PNG still carries its letter "C" and its own title, which repeats the slide title (verifier MINOR 2). It is left as is because the spec asked for the existing PNG.
5. **Minor (cosmetic):** the claims table's "shown" column prints ASCII "-" for the differences (verifier MINOR 3).
6. **Files not committed:** your uncommitted `table1_picot.md`, the `.docx`, `scripts/aou/`, `tests/test_aou_stats.py`, the overview check PNG and the `*.err` files were not touched or committed.
