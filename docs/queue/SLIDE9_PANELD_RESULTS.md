# Results: slide 9 new panel D, overall balance of AI representations vs conventional PS (queue `docs/queue/slide9_panelD.md`, 2026-10-14)

Log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide9d-20261014/STATUS.md`. **Deck only:** the paper's Figure 2 (PNG/PDF and `make_figure2_latent.py`) is unchanged. Committed locally; nothing pushed.

## New panel D (`scripts/figures/make_slide9_panelD_overall.py`)

- **Basis:** s31 (31 trials), version 1 cohorts, main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1), the 54 held-out items with the `pipeline.md` §6 masks. Demo = rung P1. The contrasts use only items observed in both arms.
- **Code:** the numbers code of `f4_numbers.py` / `f4_hdps.py`, copied (the audit files are untouched); helpers and style imported from `make_figure2_latent.py`.
- **Outputs:**
  - `docs/paper/figures_latent/panels/deck/slide9_panelD_overall.{png,pdf}`: 1283 × 800 px at 300 dpi. That is the width of Figure 2's panel D slot, extending 83 px further down, still inside the figure box.
  - values: `audits/claude-slide9d-20261014/panelD_values.json`.

| Row | Mean \|SMD\| (54 items, 31 trials) | Label (vs hdPS) |
|---|---|---|
| Unmatched (grey reference) | 0.143 | |
| PS-CVD5 | 0.129 | |
| hdPS (dashed line) | 0.114 | |
| PS-Clinical† | 0.118 | |
| Demo + ECG | 0.126 | 10.2% higher than hdPS (P = .029) |
| Demo + CLMBR-T | 0.112 | 2.0% lower than hdPS (P = .53) |
| Demo + ECG + CLMBR-T | 0.106 | 8.0% lower than hdPS (P = .012) |

Labels: two-sided exact sign-flip P, unadjusted; "lower" / "higher" is set by the sign in the code.

**Checks (the script stops if any fails):**
- All 7 means and the 3 contrasts match `figure4.md` to display precision.
- They match `recomputed_f4.json` exactly (max deviation 0).

## Deck (`scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`, 24 slides)

- **Slide 9:**
  - The clicks reveal A + B, then C, then the new D, which sits in the old D slot at the same left, top and width. The legend is kept, and there is no subtitle.
  - The "Click for other groupings ›" hint and the panel D popup trigger are removed.
  - "More:" now reads "A4 · Per-trial covariate balance improvement", "A5 · Framework v2.0 (sensitivity)", "A6 · Spec-v2 cohort fixes (sensitivity)".
- **New A4:** "Per-trial covariate balance improvement (PS-CVD5 + ECG vs PS-CVD5)".
  - It shows the Figure 2D job's per-trial panel, 488 px tall to fit the slide body.
  - Above it, one line: "19 of 31 trials improved; mean +3.3 points in % of items with |SMD| < 0.1; P = .02 (exact one-sided sign-flip)".
  - The groupings popup is unchanged: it opens from the panel or the hint, with the same tabs, Esc / Close / click-outside, and arrow keys blocked. "Back to slide 9" returns there.
- **Appendix:**

  | Label | Slide |
  |---|---|
  | A1 | Emulation-quality criteria |
  | A2 | Table 1 |
  | A3 | Held-out panel |
  | **A4** | **Per-trial covariate balance improvement (new)** |
  | A5 | Framework v2.0 (was A4) |
  | A6 | Spec-v2 cohort fixes (was A5) |

  All labels, "More:" lines and in-text references come from the slide map, so they updated automatically. That covers slide 6's quality-popup link, the balance explorer, and robustness ("(sensitivity; A5)", "(sensitivity; A6)").
- **Claims:** 485 in total; 483 checked, all 483 match.
  - The Figure 2D claims and the popup's group claims moved to A4.
  - New on slide 9: 7 means and 3 contrasts plus their P values. Each is recomputed in the builder from the version 1 cells (cross-rung, paired on items observed in both cells) and gated against `figure4.md` (`EXPECT_F2N`).
  - New on A4: the summary line (checked against the queue text) and its P as printed.
  - The 10-09 deck still regenerates byte-identical.
- **Unchanged:** the embedded data block and the JS are byte-identical to the previous build.
  - Every other section is byte-identical, apart from the A4→A5 / A5→A6 label changes (slides 6, 10 and 13, and A5 / A6 themselves).
  - Slide 5 is still empty. The take-home slide is unchanged, with no CLMBR-T claim.
  - CSS: the unused `.fig2box` popup-trigger rules are replaced by `.f2dbox` rules for A4.
- **Builder outputs:** `audits/claude-slide9d-20261014/deck`.

## Verification

Report: `docs/presentation/VERIFY_SLIDE9_PANELD.md`, by a fresh verifier subagent run in the foreground.

**Round 1: PASS with minor issues; no BLOCKING issues.** The verifier:
- recomputed every value from the cells with its own code, including its own exact sign-flip enumeration (all match exactly);
- screenshotted slide 9 steps 0–3, A4 and its 4 popup tabs at 1920×1080 and 1366×768 (no clipping or overlap);
- checked all links and back-links after renumbering (no stale labels);
- found 0 console or page errors over 24 slides;
- found the wording rules met and the privacy scan clean.

One minor issue was fixed: the dashed hdPS line touched the "0.112" and "0.106" value labels, which now start right of the line. **Round 2 re-check: PASS with minor issues; no BLOCKING issues.**
- No label touches the line, and nothing is clipped or overlapping at either size.
- The values are unchanged.
- The data block and the other sections are unchanged; only the panel D image in s-res2 differs.
- 0 console or page errors.

Screenshots are in `audits/claude-slide9d-20261014/verify/shots/` and `verify/shots_r2/`.

## For you to check

1. **P format:** the panel uses the deck's static-slide P format (3 decimals below .1), so Demo + ECG vs hdPS reads **P = .029**, where `figure4.md` wrote .03 (the same value, .0286). A4 keeps the Figure 2 format ("P = .02" for .015), as in the queue text.
2. **Footnote: 3 lines, not 2.** The exact queue wording does not fit in 2 lines at a legible size in a 4.3-inch panel. It is still tiny on the slide (about 9 px at 1920×1080, 6–7 px at 1366×768). Shorter wording would help.
3. **Panel title:** a bold "D" plus "Overall balance: AI representations vs conventional PS", as on the other panels (not the literal "D." prefix).
4. **A4 size:** the per-trial panel is 488 px tall, not literally full width, because the slide body's height limits it.
5. **Clicking slide 9 after step 3 now goes to slide 10.** Panel D used to open the popup; this is the deck's normal behaviour.
6. **Files not committed:** your uncommitted `table1_picot.md`, the `.docx`, `scripts/aou/`, `tests/test_aou_stats.py`, the overview check PNG and the `*.err` files were not touched or committed.
