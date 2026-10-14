# Verification: lab deck 2026-10-15, third edit round (queue `docs/queue/QUEUE_2026_10_14_DECK3.md`)

Independent verifier (built nothing). Checked on 2026-10-14 against `HEAD` (a153a81). The backup `prev/deck_prev.html` is byte-identical to `git show HEAD:…/ecg_tte_lab_2026_10_15.html`. I did not re-run the builder.

**Verdict: PASS with minor issues.** No BLOCKING issues.

## Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Queue edits 1–7 | PASS | Order: 1 title · 2 bg · 3 problem · 4 aims · 5 empty · 6 pipeline · 7 PSM · 8 aims (aim 2) + balance box · 9 Figure 2 · 10 aims (aim 3) + agreement box · 11 Figure 3 · 12 MIMIC-IV · 13 take-home · 14 open decisions · S2 · S3 · A1–A9 (A4 per-trial, A5 plasmode, A6 framework, A7 fixes, A8 agreement by quality, A9 interactive). `s-rob` is gone. Headings read "Figure 2. Covariate balance", "Figure 3. Agreement with RCTs", "Supplementary Figure 2. Covariate balance explorer" and "Supplementary Figure 3. Trial emulation". The definitions appear on slide 4 (graphic headings) and slide 7 (arm subtitles). Slides 8 and 10 have no reveal (0 steps). Slide 8 keeps "More: A3". Slide 9 More: A4 · A5 Plasmode · A6 · A7. Slide 11 More: A8, and A8 links to A9. The `pipeline.md` deviation line is present. |
| 2 | Screenshots, reveal steps, explorer states | PASS (one minor) | Slide 8: 1 state. Slide 9: 4 (A+B → C → D). Slide 10: 1. Slide 11: 5 (A → B → C → button). Captured at both sizes. S2/S3: all 12 states at 1920, defaults at both sizes. A4 (and its popup), A5, A8, A9 at both sizes. Every slide fully built at both sizes. DOM overflow scan: nothing outside the slide except A2's scroll box (by design, unchanged). Minor: the S2 domain labels overlap (M1). |
| 3 | Labels (figures, options, text, popups, alt/aria) | PASS | PNGs inspected: Figure 2 full + panels, Figure 3 full + panels, slide 9 panel D, slide 11 panel C, 4 popup tabs. All read AI-ECG / AI-EHR. Explorer options: PS-CVD5/PS-CVD10/PS-Clinical/hdPS; + AI-ECG / + AI-EHR / + AI-ECG + AI-EHR. Remaining "ECG"/"CLMBR-T" in the rendered DOM (text, hidden popups, alt/aria, options; A9 checked in 28 control states) are listed below. None is a violation. |
| 4 | Grey text / band | PASS | Slide 11 panel C: no grey headings, no footnote, no † (the paired-difference value labels are kept). Paper Figure 3 has no grey annotations. Figure 2D (paper, A4): the new legend matches the queue wording, the caption is removed and the "All 31 trials" line is kept. Slide 9 panel D: no grey headings, no footnote, no †, dotted separator kept. Figure 2C: pink band gone; the red relative-change labels are kept. |
| 5 | Links, back-links, Esc, browser back | PASS | All 26 a.xref / a.sback / [data-sopen] elements were clicked with real mouse clicks at 1920×1080 and 1366×768, including the links inside popups. All were visible and in the viewport, and all landed on the right slide. Round trips return to the origin slide, fully built. S2 from slide 9 panel A (hidden at step 0, cursor: pointer at step ≥1) and S3 from slide 11's button (step 4): "← Back", Esc and browser back each return to slide 9 at 3/3 and slide 11 at 4/4. Opening S2/S3 directly by hash and then using the back link also works. No link to robustness: no "robust"/`s-rob` string anywhere in the HTML. |
| 6 | Console / page errors | PASS | 0 errors and 0 warnings at both sizes: full ArrowRight walk through all 25 slides, all link tests, all explorer states, A9 controls. |
| 7 | Numbers unchanged | PASS | Numbers compared slide by slide in textContent (including hidden popups), prev vs current. The only differences are slide and appendix numbers, and the expected removals: s-rob; the old explorers; on slide 8, "4,000 resamples" and the formula, dropped by the shortened box. No new numbers on static slides, apart from the aims list copied from slide 4 (1–4 and 31) and link labels. Embedded `const D`: every previous key and value is identical. The only additions are `S.main.{P5,PS10,clinical_nolvef,hdPS200}.{CLMBR,ECG+CLMBR}`, `EST.v1.main.*.{CLMBR,ECG+CLMBR}` and `leak.arm.{CLMBR,ECG+CLMBR}`. Matches S31_RESULTS: 8.7% (4.2 to 13.5), 20/31; 0.232 → 0.198; 3.8%, 7.1%, 3.3% (−1.1 to 7.5); 10.6%. S2 default: 0.129 → 0.117, 8.7% (4.2 to 13.5), P <.001, 20/31. S3 default: 0.232 → 0.198, 20/31. All 12 S2 states match `balance_combos.json` (S2 tags) exactly. All 12 S3 states match `emu_refs.json` exactly (mean \|Δ log HR\|, trials closer, sign-flip P); the benchmark-permutation P is within ±0.015 (tolerance ±0.03). |
| 8 | Figure value JSONs | PASS | `figure2_values.json`: identical. `panelD_values.json`: identical. `figure3_values.json`: only the 3 `arms` display-label strings differ. `panelC_values.json`: only `layout.labels` (a count of text boxes for the overlap check, 25 → 22, because the headings and footnote were removed) differs. Not a displayed value. |
| 9 | Privacy | PASS | Deck markup and scripts (data URIs stripped), D block, and the added diff lines of the scripts and `pipeline.md`: no n_pairs, retention, ESS, patient keys or identifiers. The added D arrays are per-trial \|SMD\| integers and log HR / SE only. New on-screen counts are trial counts only (e.g. 18/31). No patient counts of 1–10. |
| 10 | Protected files | PASS | `paper.md`, `paper2.md`, `build_lab_deck.py`, `build_lab_deck_v2.py`, `ecg_tte_lab_2026_10_01.html` and `ecg_tte_lab_2026_10_09.html` are unmodified (`git status`). The only `.docx` is the user's untracked `trial_emulate_manuscript_v2_RC.docx` (mtime 10-07). `table1_picot.md` (mtime 10-06, before the job) is only read by the builder for A2; A2's text is identical to the previous deck. `docs/DATA_ACCESS_MAP.md` changed at 15:33, during the job window, but the change is BDC wording (another session's work) and the builder does not read the file. |

### Remaining "ECG" / "CLMBR-T" occurrences (rendered DOM)

| Where | Text | Class |
|---|---|---|
| Slides 4, 8, 10 | aim 1 title "Integrate ECG and EHR foundation models into matching" | generic (kept by request) |
| Slide 4 graphic | "AI-ECG (ECG foundation model embedding, BCL encoder)", "AI-EHR (EHR foundation model, CLMBR-T; coded history)"; encoder boxes "BCL encoder", "CLMBR-T" | definition |
| Slide 4 graphic | "raw ECG waveform (12-lead)" | raw test |
| Slide 6 + popup | "≥ 350 with an ECG in the smaller arm" (×2) | raw test |
| Slide 7 | subtitles "(ECG foundation model embedding, BCL encoder)", "(EHR foundation model, CLMBR-T; coded history)" | definition |
| Slide 7 popup | "latest 12-lead ECG in [index − 365 d, index] … 37% of ECGs", "frozen CLMBR-T-base" | raw test / model name |
| Slide 12 | "Index-day ECGs excluded" | raw test |
| Slide 14, A2 | "LIFE ECG-LVH", "Hypertension with ECG-LVH" | raw test |
| A5 | "Real covariates, ECGs and follow-up" | raw test |

## BLOCKING issues

None.

## MINOR issues

- **M1. S2 love plot: the rotated domain labels collide** (both sizes, every state with the full 54-item panel). "Valves / aorta" runs into "RV / pulmonary", which runs into "Diastolic / LA". All three cross the group separator lines, and "LV function" gets no label. Cause: `s2Update` (SX_JS) uses `gh > gl.length * 4.6`, which underestimates the width of 9.5-unit bold text. Fix: use about 6.2 per character, shrink the font, or abbreviate (e.g. "RV / PA", "Valves", "Diastolic"). See `shots/crop_s2_groups.png`.
- **M2. S3 default P values differ slightly from the docs (within tolerance).** The JS Monte Carlo benchmark-permutation P shows .54, against .56 in `S31_RESULTS.md` (Python .555). The sign-flip P shows .04, against .035 in the docs (2-decimal format). Optional: format P with 3 decimals below .1, as the paper does, or align the JS draws with the Python seed.
- **M3. S2 and S3 are still in the linear sequence.** ArrowRight from slide 14 goes to S2 → S3 → A1. This is consistent with "then the supplementary figures and the appendix", but S2/S3 are not reachable *only* from slides 9 and 11. Optional: skip `data-supp` slides in `next()`/`prev()`.
- **M4. Appendix → appendix links.** A9's "More: A1" opens A1, whose back-link points to slide 6, not A9. This is the existing nav design (backTo is set only from main slides), so it is information only.
- **M5. Mechanical rename wording.** "The AI-ECG improves held-out balance…" (slide 13, point 1) and "The AI-ECG removes…" (slide 13, point 4 and A5) read awkwardly. Optional: "Adding AI-ECG…".

## Screenshots and logs

`/mnt/raid0/rbc58/ecg-tte/audits/claude-deck3-20261014/verify/`:
- `shots/1920x1080/` and `shots/1366x768/`:
  - `step_{8,9,10,11}_k.png` and `step_4_2.png`
  - `all_NN_label.png`
  - `S2_*.png` and `S3_*.png` (the 12 states at 1920; defaults at both sizes)
  - `app_A4.png`, `app_A4_popup.png`, `app_A5.png`, `app_A8.png`, `app_A9.png`, `app_A9_allmethods.png`
- Logs: `render_*.json`, `shots_*.json`, `links_*.json`, `d_compare.json`.
- Scripts: `v*.py`.

## Round 2 re-check

A second independent verifier (built nothing) re-checked the rebuilt deck on 2026-10-14. It checked the four claimed fixes and re-ran the round 1 regressions at 1920×1080 and 1366×768. The baseline was again the pre-job deck (`prev/deck_prev.html`). The round 1 rendered text was in fact saved (`verify/render_*.json`, key `cur`), so the deck was also diffed round 1 → round 2.

**Verdict: PASS with minor issues.** No BLOCKING issues. Round 1's M1, M2 (format part), M3 and M5 are fixed.

### Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| R1 | Fix 1: S2 rotated domain labels | PASS | Label lengths were measured in SVG units with `getComputedTextLength` and compared with the group separators, in all 12 states at both sizes. Every label fits inside its own group. The smallest margin is 5.5 units ("LV func.", PS-CVD5/PS-CVD10/hdPS). Nothing crosses a separator. Labels: Vitals, labs · Other labs · LV structure · LV func. · Diastolic · RV / PA · Valves. With 54 items all 7 groups are labelled; "LV func." now has a label. The labels' right edge sits well left of the item labels (screen px 243 vs 312 at 1366; 342 vs 438 at 1920). Crops were inspected at both sizes (`verify_r2/shots/*/S2_*_svg.png`, `crop_S2_lvfunc_*.png`). |
| R2 | Fix 2: P format | PASS | S2 and S3 P values use the static-slide format (`<.001`; 3 decimals below .1; otherwise 2). S3 default: sign-flip P **.035** and benchmark-permutation P .54 (Monte Carlo; Python .555; difference within ±0.03). S2 examples: .095, .015, .024, .079, .029, .008, .11, .44. |
| R3 | Fix 3: arrow keys skip S2/S3 | PASS | Full ArrowRight walk: 1–14 → A1–A9, never S2/S3 (both sizes). Full ArrowLeft walk back: A9 → … → A1 → 14 → … → 1. ArrowRight (also ArrowDown, PageDown, Space) from slide 14 at its last step lands on A1. ArrowLeft (also ArrowUp, PageUp) from A1 at step 0 lands on slide 14. The on-screen › / ‹ do the same. On S2 and S3, none of ArrowRight/Left/Up/Down, PageUp/Down, Space, a stage click or ‹ / › moves the deck. Slide 9 panel A (step ≥1) and slide 11's button (step 4) still open S2/S3. "← Back", Esc and browser back each return to 9 at 3/3 and 11 at 4/4. After returning, ArrowRight goes 9 → 10 and 11 → 12, and ArrowLeft comes back built. Direct `#S2` / `#S3` entry and then Back also work. |
| R4 | Fix 4: wording | PASS | Slide 13: "**AI-ECG improves held-out balance when the PS is thin**" and "(AI-ECG removes part of a hidden physiological confounder's bias …)". A5: "**AI-ECG removes a further 11.3% of the bias that PS-CVD5 leaves**". No "The AI-ECG" remains anywhere. The round 1 → round 2 text diff (textContent including hidden popups, plus attrs, options and modals; all 25 slides) shows only these changes: 2 "The/the" removed on 13, 1 on A5, the S2 group labels, and the S3 sign-flip P (.04 → .035). Nothing else changed. |
| R5 | Console / page errors | PASS | 0 errors and 0 warnings at both sizes: every slide shown built (including S2/S3), full forward and backward walks of every step, every popup opened (all 7 `[data-pop]` triggers on 6, 7 and A4, tab buttons clicked, closed with Esc), all link tests, and all 12 states of both explorers. |
| R6 | Links | PASS | All 26 a.xref / a.sback / [data-sopen] elements were clicked with real mouse clicks at both sizes. All were visible and in the viewport, and all landed on the right slide. Back-links return to the origin slide, fully built. The only exceptions are A8 → A9 and A9 → A1, whose back-links point to the main slide (11 and 6), as in round 1's M4. |
| R7 | S2 vs `balance_combos.json` | PASS | Default: 0.129 → 0.117, **8.7% (4.2 to 13.5)**, P <.001, **20/31**. All 12 S2 states match `py_full` exactly (means, RR and CI, P in the .3f-below-.1 format, trials improved) at both sizes. 0 mismatches. |
| R8 | S3 vs `emu_refs.json` | PASS | All 12 states match exactly (mean \|Δ log HR\|, trials closer, sign-flip P) at both sizes. Benchmark-permutation P max \|JS − Python\| = 0.015 (tolerance ±0.03). Default 0.232 → 0.198, 20/31. |
| R9 | Static-slide numbers vs pre-job deck | PASS | The per-slide number multisets (textContent including hidden popups, titles excluded) differ from the pre-job deck only as in round 1: renumbering (slide and appendix numbers, link labels), the aims list on 8/10, the dropped "4,000" on 8, and the removed `s-rob`. No other number changed. |
| R10 | Bare "ECG" / "CLMBR-T" | PASS | The rendered-DOM scan (text including hidden popups, alt/aria/title, options) finds exactly the round 1 set: definitions on 4 and 7, raw-test wording (raw ECG waveform, with an ECG in, 12-lead ECG, ECG-LVH, ECGs), "frozen CLMBR-T-base", and the aim 1 title "Integrate ECG and EHR foundation models" (4, 8, 10). Nothing new. |
| R11 | Embedded `const D` | PASS | Every pre-job key and value is identical (0 value or length differences). The 18 added keys are the same set as in round 1. |
| R12 | Layout / overflow | PASS | DOM overflow scan of S2/S3 in all 12 states at both sizes: nothing outside the slide. |

### BLOCKING issues

None.

### MINOR issues (all optional)

- **R2-M1. "LV func." is the smallest S2 group label.** It is drawn at 6.2 SVG units, about 6.8 px at 1366×768 and 9.5 px at 1920×1080, against about 8–9 px item labels at 1366. It is legible and does not overlap. "LV structure" is at 7.8 units. Optional: reduce the gap from separators, or accept.
- **R2-M2. The PS-Clinical states (3 of the 12 S2 states) have one unlabelled group.** With PS-Clinical the held-out panel has 45 items, and "Vitals & core labs" has a single row (LVEF), too short for a rotated label. The row sits between two separators with no domain label. Before the fix this group was not labelled in that state either. Optional: skip the separator for one-row groups, or use a horizontal mini-label.
- **R2-M3. The on-screen ‹ / › buttons stay visible but do nothing on S2/S3.** This is consistent with fix 3 (arrows do nothing there). Optional: hide or dim `#nav` on `data-supp` slides so the inert buttons don't look broken.
- **R2-M4 (carried over, information only).** Round 1's M4: the appendix → appendix links (A8 → A9, A9 → A1) have back-links to the main slide, not to the appendix origin.
- **R2-M5 (carried over, accepted).** The S3 benchmark-permutation P is Monte Carlo in the JS: .54 against Python .555 (docs .56). This is within tolerance.

### Round 2 files

`/mnt/raid0/rbc58/ecg-tte/audits/claude-deck3-20261014/verify_r2/` (umask 077):
- Scripts: `r1_render.py`, `r2_explorers.py`, `r3_links.py`, `r4_cmp.py`, `r5_crop.py`, `r6_navbtn.py`, `r7_perms.py`.
- Logs: `render_*.json`, `explorers_*.json`, `links_*.json`.
- Screenshots: `shots/{1920x1080,1366x768}/S2_*_svg.png` and `S3_*.png` (12 states each, both sizes); `shots/crop_S2_lvfunc_*.png`.

No commits, no pushes, no GPU, and no background tasks left running. The only repo file modified is this report.
