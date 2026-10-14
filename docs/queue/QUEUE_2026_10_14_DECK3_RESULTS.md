# Results: queue 2026-10-14, third deck-edit job (deck3)

Queue file: `docs/queue/QUEUE_2026_10_14_DECK3.md`. Log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-deck3-20261014/STATUS.md`. Builder: `scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html` (25 slides). Committed locally; nothing pushed.

**Numbers unchanged.** All four figure value files are identical to before; only their label strings and one layout counter changed. The deck's claims table has 446 of 446 checked claims matching, and the 10-09 deck still regenerates byte-identical.

## 1. What changed, per slide

| Slide | Change |
|---|---|
| **Whole deck** | Every label now reads **AI-ECG** (was "ECG") and **AI-EHR** (was "CLMBR-T"): slide text, popups, alt text, explorer options and every figure.<br>A `relabel()` pass in the builder protects four kinds of text: the raw-test wording ("12-lead ECG", "raw ECG waveform", "with an ECG in the smaller arm", "ECGs", "ECG-LVH"), the two definitions, the aim 1 title and "frozen CLMBR-T-base" in the slide 7 popup. |
| **4 Aims** | The two path headings in the graphic are the definitions: "AI-ECG (ECG foundation model embedding, BCL encoder)" and "AI-EHR (EHR foundation model, CLMBR-T; coded history)".<br>The encoder boxes read "BCL encoder" and "CLMBR-T". The aim 1 subtitle reads "AI-ECG and AI-EHR · easy to operationalize". |
| **7 PSM experiments** | The comparison arms read "+ AI-ECG", "+ AI-EHR" and "+ AI-ECG + AI-EHR". The two definitions are their subtitles (→ 32 / 64 PCs). The placebo is "AI-ECG shuffled between patients". |
| **8** | "Methods: covariate balancing": a static copy of the slide 4 aims list, with aim 2 highlighted (red border, pink fill) and the other aims dimmed.<br>Below it, one box: the endpoints (primary: relative reduction in mean \|SMD\| over the 54 held-out items; secondary: % of items with \|SMD\| < 0.1) and the tests (paired by trial · bootstrap CI · exact sign-flip · placebo with permuted AI-ECG).<br>The "More: A3" link is kept. |
| **9** | Headed "Figure 2. Covariate balance".<br>Panel C has no pink band. Panel D has no grey headings, footnote or †.<br>Once revealed, panel A opens Supplementary Figure 2 (cursor and outline on hover). The A+B → C → D reveal is unchanged.<br>"More:" lists A4, A5 (plasmode), A6 and A7. |
| **10 (new)** | "Methods: agreement with RCTs": the same aims copy with aim 3 highlighted.<br>Below it, one box: the endpoint (mean \|Δ log HR\|, lower = closer) and the tests (paired by trial with exact sign-flip · benchmark permutation). |
| **11** | Headed "Figure 3. Agreement with RCTs".<br>Panel C has no grey headings, footnote or †.<br>Click 4 shows the button "Supplementary Figure 3. Trial emulation", which opens S3. "More: A8". |
| **S2, S3 (new)** | **Supplementary Figure 2. Covariate balance explorer** and **Supplementary Figure 3. Trial emulation**.<br>Two selects only: PS (PS-CVD5 default, PS-CVD10, PS-Clinical, hdPS) and representation (+ AI-ECG default, + AI-EHR, + AI-ECG + AI-EHR). Fixed: version 1 cohorts, the 31 trials, main configuration, 54 leakage-corrected items.<br>S2 shows the love plot; S3 shows the HR forest plot. The numbers column lists the mean, relative reduction with 95% CI, P and trials improved for S2; for S3, the mean \|Δ log HR\|, trials closer, sign-flip P and benchmark-permutation P.<br>Leave with "← Back to Figure 2/3", Esc or the browser back button. The figure slide comes back fully built. |
| **A4** | The per-trial panel legend reads "Physiology trials: 10 of 11 improved; mean +9.9 points" and "Other: 9 of 20 improved; mean −0.3 points". The caption is removed. The "All 31 trials" line and the groupings popup are kept. |
| **Removed** | The robustness slide and every link to it. No text referred to it. |

**New order:** 1 title · 2 background · 3 problem · 4 aims · 5 empty · 6 pipeline · 7 PSM experiments · 8 aims (aim 2) + balance methods · 9 Figure 2 · 10 aims (aim 3) + agreement methods · 11 Figure 3 · 12 MIMIC-IV · 13 take-home · 14 open decisions · S2 · S3 · A1–A9.

**Appendix:**

| Label | Content | Before |
|---|---|---|
| A1 | Emulation-quality criteria + quality viewer | A1 |
| A2 | Table 1 | A2 |
| A3 | Held-out panel and leakage map | A3 |
| A4 | Per-trial covariate balance improvement | A4 |
| **A5** | **Plasmode** (linked from slide 9) | slide 15 |
| A6 | Framework v2.0 | A5 |
| A7 | Spec-v2 cohort fixes (back to slide 9, was robustness) | A6 |
| **A8** | Agreement by emulation quality (panel; links to A9) | A7 |
| **A9** | Agreement by emulation quality, interactive (unchanged apart from labels) | slide 14 |

**Figures regenerated** (paper and deck):
- Figure 2: full figure and panels A–D;
- the A4 popup tabs;
- Figure 3: full figure and panels;
- slide 9 panel D and slide 11 panel C (`panels/deck/`).

The paper figures change only in labels, plus the Figure 2C band and the Figure 2D legend and caption.

**`pipeline.md`:** one deviations-log line was added (display labels; analysis unchanged).

## 2. Verification

The report is `docs/presentation/VERIFY_LAB_DECK_2026_10_15_EDITS3.md`, from two fresh verifier subagents run in the foreground.
- **Round 1: PASS with minor issues, no BLOCKING issues.**
  - All 7 edits are confirmed, and nothing still links to the robustness slide.
  - All 26 links work at 1920×1080 and 1366×768, as do Esc and the browser back button. There were 0 console or page errors.
  - The static numbers are unchanged, apart from the renumbering and the removals. Every data key that existed before is identical.
  - All 12 states of S2 and of S3 match the Python references. Defaults: 8.7% (4.2 to 13.5), 20/31.
  - The privacy scan is clean, and no protected file was touched.
- **Fixed after round 1:**
  - the S2 domain labels overlapped (they are now sized to fit, with shorter names);
  - the explorer P format is now that of the static slides;
  - the arrow keys now skip S2 and S3;
  - "The AI-ECG improves / removes" now reads "AI-ECG improves / removes".
- **Round 2: PASS with minor issues, no BLOCKING issues.** All four fixes are confirmed, and the regressions above were all re-run.

## 3. Judgement calls for you to check

1. **New numbers in the explorers.** The requested "+ AI-EHR" and "+ AI-ECG + AI-EHR" options show CIs and P values that were not displayed in the deck before. Their relative changes equal Figure 2C, and their \|Δ log HR\| values equal Figure 3B. To support them, the embedded data gained these arms (version 1 cohorts, main configuration, the four PS).
2. **S2 hdPS mean.** S2 shows the paired-item means, as the old explorer did. For hdPS that is 0.113 → 0.105, while Figure 2C shows 0.114 for hdPS alone on its own items.
3. **S3 benchmark-permutation P** is the deck's Monte Carlo value, .54 for PS-CVD5 + AI-ECG. The Python value is .555 (.56 in `S31_RESULTS.md`), as before. The explorer P format is now 3 decimals below .1: sign-flip P .035, where the old explorer showed .04.
4. **Slide 4.**
   - The aim 1 title "Integrate ECG and EHR foundation models into matching" is kept as generic wording.
   - The old subtitle was replaced by "AI-ECG and AI-EHR · easy to operationalize".
   - The encoder boxes now name the models (BCL encoder, CLMBR-T) instead of "AI-ECG encoder".
   - The goal line ("unstructured information") is unchanged.
5. **Slide 8 box.** The relative-reduction formula and "4,000 resamples" were dropped to keep it short. The queue wording is used as written. The highlight style (red border, pink fill) is mine.
6. **Slide titles.** Slides 8 and 10 are titled "Methods: covariate balancing" and "Methods: agreement with RCTs".
7. **Figure 2D legend.** The group names are bold (mathtext). The same caption was also removed from the first popup tab.
8. **Supplementary slides.**
   - They are labelled S2 / S3 (hashes #S2 / #S3) and keep the grey appendix title bar.
   - The arrow keys skip them and do nothing on them, but the ‹ › buttons still show (verifier minor).
   - S2 uses short domain labels ("LV func." is small but legible). In the PS-Clinical states, the single-row vitals group has no label.
9. **Agreement by quality** is two consecutive slides (A8 → A9), because the interactive view and the panel don't fit on one. A8's PNG still carries its old letter "C". The appendix-to-appendix back-links go to the main slide (existing design).
10. **No longer in the deck:** the robustness numbers (six PS methods, cluster / leave-one-out, CV penalty, no index-day ECG, R2 4.7%).
11. **Value files rewritten.** The figure scripts rewrote their value files in the earlier jobs' audit folders (`claude-fig2d`, `claude-fig3`, `claude-slide9d`, `claude-slide11c`). The values are identical, and the old copies are in `audits/claude-deck3-20261014/prev/`.
12. **Files not committed:**
    - your uncommitted `table1_picot.md`;
    - the `.docx`;
    - `docs/DATA_ACCESS_MAP.md` (changed during this job by other work);
    - `scripts/aou/`, `scripts/bdc/` and the tests;
    - the overview check PNG and the `*.err` files.
