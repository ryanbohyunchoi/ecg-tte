# Results: Figure 3, agreement with the RCT results with the CLMBR-T arms (queue `docs/queue/figure3.md`, 2026-10-14)

Log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig3-20261014/STATUS.md`. The three earlier jobs had all finished cleanly: s31 (PASS with minor issues, finished by the deck2 job), deck2 (PASS with minor issues) and Figure 2D (PASS with minor issues, 1fa046a). So the full change was made. Committed locally; nothing pushed.

## Figure 3 (`scripts/figures/make_figure3_latent.py`)

- **Basis:** s31 (31 trials), version 1 cohorts, main configuration (1:1 NN, caliper 0.2, C = 1). It uses the log HRs of the existing cells (PS-Clinical (no LVEF): 5-draw MI, Rubin-combined), with no refitting. The data are loaded through `scripts/s31/s31_numbers.load()`, the mock-ups' code path.
- **Style and layout:** Figure 2's style (fonts, colours, arm markers, ladder order, panel export, all imported from `make_figure2_latent.py`). A and B sit on top, with C centred below. There is no panel D.
- **Outputs:**
  - `docs/paper/figures_latent/figure3_rct_agreement.{png,pdf}` (300 dpi)
  - `panels/figure3_rct_agreement_{A,B,C}.{png,pdf}`
  - values: `audits/claude-fig3-20261014/figure3_values.json` (aggregates)

Mean |Δ log HR| vs RCT, 31 trials:

| | PS alone | + ECG | + CLMBR-T | + CLMBR-T + ECG |
|---|---|---|---|---|
| **A** (PS-CVD5) | 0.232 | 0.198 (20 of 31 trials closer) | | |
| **B** PS-Demo | 0.255 | 0.207 | 0.174 | 0.164 |
| PS-CVD5 | 0.232 | 0.198 | 0.169 | 0.161 |
| PS-CVD10 | 0.213 | 0.173 | 0.181 | 0.157 |
| PS-Clinical (no LVEF, MI) | 0.171 | 0.151 | 0.151 | 0.152 |
| hdPS | 0.182 | 0.172 | 0.184 | 0.169 |
| **C** Excellent + Good (14), PS-CVD5 | 0.230 | 0.176 | 0.149 | 0.152 |
| Moderate (17), PS-CVD5 | 0.235 | 0.217 | 0.185 | 0.168 |

**Checks (the script stops if any fails):**
- All 30 values are within 0.001 of the queue file's (max 0.0005), and they also round to the same 3 decimals.
- The ECG values equal `docs/s31/S31_RESULTS.md` §1, §2 and §4, and `s31_numbers.json`: 41 values, max deviation 1.2e-7.
- 20/31 closer equals the summary.

**Panel B:** no P values, grey text, highlight or permutation bands. **Panel C:** v19 tiers. **Panel A inset:** "Mean |Δ log HR|: 0.232 → 0.198 / 20 of 31 trials closer". I viewed the figure and each panel: no overlap or clipping.

**Caption** (the deck has no speaker notes, so it is the figure box's `aria-label` on the slide):
> Figure 3. Agreement of emulated and RCT results (31 trials). A, Emulated vs RCT hazard ratios with PS-CVD5 and PS-CVD5 + ECG. B, Mean absolute difference from RCT log HRs across the PS ladder with the ECG, CLMBR-T or both added. C, Mean absolute difference by emulation quality (PS-CVD5). Lower is closer to the RCT.

## Deck (`scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`)

- **New slide 11:** "Results: agreement with the RCTs (Figure 3)", directly after the balance explorer (10) and before the emulation explorer.
  - It is built from the three per-panel PNGs, laid out as in the full figure (located by image matching, as on the Figure 2 slide).
  - Each click reveals one panel: A → B → C. It has a minimal title and no subtitle or source line.
- **Renumbering:** the former slides 11–17 are now 12–18: emulation explorer 12, robustness 13, agreement by quality 14, plasmode 15, MIMIC-IV 16, take-home 17, open decisions 18. The deck has 23 slides.
  - The only back-link that changed is A5 → "Back to slide 13" (was 12).
  - No visible text or JS held another hard-coded slide number. The one mention left is "slide 7" on the open-decisions slide, and slide 7 did not move.
- **Unchanged:** every other section is byte-identical to the Figure 2D build, as are the JS and the embedded data. That includes the "agreement by quality" slide and the take-home wording.
  - Figure 2's image helpers were moved to module level so Figure 3 can reuse them. The Figure 2 slide is still byte-identical.
- **Claims:** 33 new claims cover the panel A inset (vs `S31_RESULTS.md` and the deck's log HRs) and every B and C value (vs the log HRs and the tiers). That makes 470 claims; all 468 checked claims match.
  - Builder outputs: `audits/claude-fig3-20261014/deck`.
- **`pipeline.md`:** one line added to the deviations log.

## Verification

Report: `docs/presentation/VERIFY_FIGURE3.md`, by a fresh verifier subagent run in the foreground. **Verdict: PASS with minor issues; no BLOCKING issues, so no fix rounds were needed.**
- **Values:** recomputed from the raw cells with the verifier's own code. All B, C and panel A values match; tiers were rebuilt from `quality_tiers.json`.
- **Figure:** panel B has no P values, grey text, highlight or bands, and there is no panel D.
- **Reveal steps:** checked by screenshot at 1920×1080 and 1366×768.
- **Navigation:** all 23 slides by keyboard, every hash link, the 13 "More:" links and their back-links (A5 → 13, A4 → 9) work. There were 0 console or page errors.
- **Other slides:** unchanged apart from the shifted slide numbers.
- **Privacy:** the scan is clean.

## For you to decide or check

1. **Overlap with "Agreement with the RCTs by emulation quality" (now slide 14).** Panel C repeats that slide's PS-CVD5 and + ECG values by tier (0.230 → 0.176; 0.235 → 0.217) and adds the CLMBR-T arms. Decide whether to keep both slides.
2. **Title numbering.** The new title (queue wording) has no number, so the sequence reads "Results 1", "Results 2", "Results: agreement…", "Results 3". Say if it should be renumbered (e.g., "Results 3: …" and the explorer "Results 4").
3. **Figure size on the slide.** The figure is 705×580 px, the same height as Figure 2, with wide side margins. At 1366×768 the axis text is small but legible. A one-row layout would fill the width better, at the cost of a shorter figure.
4. **The caption is not visible to the presenter.** The deck has no speaker-notes mechanism, so the caption is only an accessibility label. It is in this file for the notes.
5. **CLMBR-T** appears only as a comparison arm (panels B and C). It is not in the take-home slide and is never called "unstructured".
6. **Files not committed:** your uncommitted `table1_picot.md`, the `.docx`, `scripts/aou/`, `tests/test_aou_stats.py`, the overview check PNG and the `*.err` files were not touched or committed.
