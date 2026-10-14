# Verification: Figure 2D (cardiac-physiology grouping) and the deck popup

Verifier: an independent subagent that built nothing. Date: 2026-10-14. Spec: `docs/queue/figure2D.md`.
Scratch scripts: `/tmp/claude-0/-home-rbc58-github-ecg-tte/fig2d-verify/` (`recompute.py`, `deck_check.py`, `deck_diff.py`, `privacy.py`).
Outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig2d-20261014/verify/` (`recompute.json`, `deck_check.json`, `shots/`). Aggregates only.

## Verdict: **PASS with minor issues** (no BLOCKING issues)

## Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Panel D values recomputed from the cells | PASS | Own code on `BE.load_grid()` (NOLVEF = MI v1-layout cells), `grid.block("main","P5",arm,True)` on the 54 items, items observed in both cells (53–54 per trial). Cardiac-physiology 10 of 11, mean +9.93; other 9 of 20, −0.27; all 31: 19 of 31, +3.35. Every group equals `BE.pair_stats` (better, k, dpts). Per-trial values equal the builder's `D_per_trial` (max abs diff 0.0). |
| 1b | Overall exact one-sided sign-flip P | PASS | Own meet-in-the-middle over all 2^31 patterns: P = 0.0152249; `BE.signflip_1s` and `pair_stats` give the same; Monte Carlo (400k) gives 0.0151. Shown as "P = .02" (`fmt_p`, as in the previous panel D). |
| 2 | Grouping matches queue item 2 | PASS | `CARDIAC_PHYSIOLOGY` = rhythm control {AF-CHF, AFFIRM, EAST-AFNET 4, CABANA, RAFT-AF} + HF / RAAS {PARADIGM-HF, ELITE II, TRANSFORM-HF, COMET, EMPEROR-Preserved, VALIANT}, `full` names, asserted ⊂ s31. The 6-group `DECISION` covers exactly the 31 (asserted; my independent assert agrees), with CANVAS Program, EMPA-REG OUTCOME and PROVE IT-TIMI 22 mapped correctly. Area from `trials_meta["area"]`; the physiologic label in `trials_meta["phys"]` equals `TRIAL_LABELS.json` "physiologic" for all 31 (checked directly). |
| 3 | Popup tab values recomputed | PASS (3 means differ from the queue file by 0.1; the queue values are wrong, see below) | Area: AF 7/11 +4.5; HF 4/5 +7.4; ACS / MI 1/2 **+5.6**; Hypertension 1/2 **−4.6**; Diabetes 3/7 +0.8; Other 3/4 +2.3. Decision: rhythm 5/5 +12.2; HF/RAAS 5/6 +8.0; antithrombotic 3/8 −0.5; glucose 3/7 +0.8; BP 1/2 **−4.6**; other 2/3 +0.6. Physiologic: yes 9/10 +8.5; no 10/21 +0.9. All counts match the queue file. The tab PNGs show exactly these values (viewed). |
| 3b | The 0.1 rounding deviation | Builder's claim CONFIRMED; display is correct | `d_mock2.py` hard-codes per-trial values at 1 decimal (max abs diff from full precision 0.048). ACS / MI = PLATO 0.000 and VALIANT 11.111: exact mean 5.556 → +5.6; the mock-up's (0.0 + 11.1)/2 = 5.55 → "+5.5". LIFE 3.704 and INSIGHT −12.963: exact −4.630 → −4.6; the mock-up's (3.7 − 13.0)/2 = −4.65 → "−4.7". No other group changes when computed from 1-decimal inputs. (The panel D expectations came from `d_mock3.py`, which used full-precision `d_predict.json`, so they match exactly.) |
| 4 | Bars, colours, labels, legend, title, footnote, no group test | PASS | Sorted order recomputed (desc, ties by name: AFFIRM, ELITE II, PARADIGM-HF at 16.67; AMPLIFY, PROVE IT; CAROLINA, ROCKET-AF, TRANSFORM-HF; ...) and matches the figure. Bars #2f6db5 / #c9cbd6; cardiac tick labels blue and bold; other labels grey #7a7c8c (see MINOR 2). No "Trials (sorted)". Legend text exact per item 5; "All 31 trials: 19 of 31 improved; mean +3.3 points; P = .02". Title "PS-CVD5 + ECG vs PS-CVD5, per trial"; y label unchanged. Footnote "Trials grouped descriptively by type of treatment decision." No group P or test in the figure, tabs or deck (popup text has no "P ="; captions say "no tests of group differences"). Every tab caption in the popup says "Descriptive grouping"; tabs 2–4 PNG titles say "descriptive grouping". Tab 3 group titles wrapped, no overlap (BP-lowering / Other separated). |
| 5 | Figure 2 slide reveal steps (both sizes) | PASS | Step 0: legend only; 1: A + B; 2: + C; 3: + D and the hint "Click for other groupings ›". Before step 3, D and the hint are `visibility:hidden`; `elementFromPoint` at their centres is `.fig2box` (no popup trigger); real clicks there at steps 0 and 2 advanced the build (0→1, 2→3) and did **not** open the popup. |
| 6 | Popup behaviour (both sizes) | PASS | Opens on click on D at step 3, on the hint, and on Enter with D focused. 4 tab buttons; exactly one view visible at a time; default and every reopen = tab 1 (cardiac-physiology), whose image is the panel D drawing with the same values. Each tab shows the right image (viewed). Esc, the Close button, and click-outside (top-left and bottom-right corners) each close it. ArrowRight / ArrowLeft / PageDown / Space / ArrowDown while open: slide stays #9, step 3, popup stays open. `.mbox` scrollHeight = clientHeight = 599 (design px) at both sizes: fits without scrolling. |
| 7 | No overlap / clipping | PASS | Viewed the full figure, panel D PNG, the 4 tab PNGs and the slide at both sizes: no overlap or clipping (trial names, footnote and the hint clear the slide's bottom rule). Panels A–C values are unchanged (`figure2_values.json` A, B, C, D, check sections identical to the s31 run's copy). |
| 8 | Console / page errors, full walk | PASS | 0 console errors, 0 page errors at 1920×1080 and 1366×768, including a full ArrowRight walk through all 22 slides (50 presses, ended on A5, the last slide). |
| 9 | Rest of the deck unchanged vs HEAD (deck2 build) | PASS | Per-`<section>` comparison: all 21 sections other than `s-res2` are byte-identical (markup, text, alt, data URIs). `const D = {...};` byte-identical (sha1 89a271349ce1). Outside sections, the only additions are the new CSS block (`.f2d`, `.f2hint`, `.f2tab`, `.f2view`), the new `f2dInit()` and its call in the init line. In `s-res2`: new hint, new popup, panel D image / alt (now carries the speaker note), slightly taller figure box (580 vs 560 px). |
| 10 | Old panel D summary text; claims | PASS | Neither the HEAD deck nor the current one contains "20 of 32", "trials improved" or "improved" in text (the old summary lived only inside the PNG). `claims.csv`: 437 claims, 435 match = True, 2 blank (pre-existing slide-16 "definition" rows); 17 new group claims (cardiac, other, all, 6 area, 6 decision, 2 physiologic), each vs `pair_stats` on the group's trials; all True, values equal to my recomputation. No claim from the deck2 table was removed or changed. |
| 11 | Privacy scan | PASS | Added lines in the scripts, `pipeline.md` and the deck: no MRN / person_id / dates of birth / identifiers, no n_pairs / retention / ESS, no patient counts (only trial counts of 31/11/20 etc., item counts 54, and per-trial % changes). The figures and tabs show trial-level aggregates only. No CSV / parquet / pickle in the working-tree changes; the restricted cells and the per-trial JSON stay under `/mnt/raid0`. |

## Recomputed numbers (independent; full precision)

| Group | Improved / n | Mean change (points) | Shown |
|---|---|---|---|
| Cardiac-physiology | 10 / 11 | +9.933 | +9.9 |
| Other | 9 / 20 | −0.274 | −0.3 |
| All 31 | 19 / 31 | +3.348; P = 0.01522 | +3.3; P = .02 |
| Area: AF | 7 / 11 | +4.536 | +4.5 |
| Area: HF | 4 / 5 | +7.407 | +7.4 |
| Area: ACS / MI | 1 / 2 | +5.556 | +5.6 (queue +5.5) |
| Area: Hypertension | 1 / 2 | −4.630 | −4.6 (queue −4.7) |
| Area: Diabetes | 3 / 7 | +0.819 | +0.8 |
| Area: Other | 3 / 4 | +2.315 | +2.3 |
| Decision: rhythm control | 5 / 5 | +12.222 | +12.2 |
| Decision: HF / RAAS | 5 / 6 | +8.025 | +8.0 |
| Decision: antithrombotic | 3 / 8 | −0.476 | −0.5 |
| Decision: glucose-lowering | 3 / 7 | +0.819 | +0.8 |
| Decision: BP-lowering | 1 / 2 | −4.630 | −4.6 (queue −4.7) |
| Decision: other (statin, NSAID) | 2 / 3 | +0.617 | +0.6 |
| Physiologic: yes | 9 / 10 | +8.519 | +8.5 |
| Physiologic: no | 10 / 21 | +0.885 | +0.9 |

## Screenshots

Under `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig2d-20261014/verify/shots/`:
- `s9_1920_step0.png` … `s9_1920_step3.png`, `s9_1366_step0.png` … `s9_1366_step3.png` (Figure 2 slide at each reveal step);
- `pop_1920_default.png`, `pop_1920_tab0.png` … `pop_1920_tab3.png`, `pop_1366_default.png`, `pop_1366_tab0.png` … `pop_1366_tab3.png` (popup, each tab).

## Issues

1. MINOR: the queue file's expected values for ACS / MI (+5.5), Hypertension (−4.7) and BP-lowering (−4.7) come from the mock-up's 1-decimal per-trial inputs. The full-precision values shown (+5.6, −4.6, −4.6) are correct. Fix: state this in `docs/queue/FIGURE2D_RESULTS.md`; optionally set `EXPECT` in `make_figure2d_groupings.py` to the full-precision values and drop the rounding-tolerance branch.
2. MINOR: item 4 says tick labels should match the bar colours, but the "other" labels use the text grey #7a7c8c, not the bar grey #c9cbd6. This follows the mock-up (`d_mock3.py`), and #c9cbd6 is too faint for text. Fix: none needed; note it as an intended deviation in the results file.
3. MINOR: the tab 1 PNG itself says "Trials grouped descriptively…" rather than "descriptive grouping". The popup caption under every tab does say "Descriptive grouping", so the spec is met. Fix: optional.
4. MINOR (already in the deck2 build): the claims table records the overall P as ".015", but the figure shows "P = .02" (`fmt_p` rounds to 2 decimals when P ≥ .01). Fix: optional; add the displayed form to the claim, or say in the claim that it is shown rounded.
5. MINOR (cosmetic): in tab 2 there is a large vertical gap between the one-line area titles and their "k/n improved" boxes, and "Hypertension" sits about 1 px higher than the other titles. Fix: optional; lower the title y for tab 2, or align the titles on their baseline.
6. MINOR (commit hygiene): the working tree has changes this job did not make: `docs/paper/table1_picot.md` (modified 2026-10-06; on the queue file's do-not-edit list), `docs/paper/trial_emulate_manuscript_v2_RC.docx`, `docs/presentation/figures/latent_rct_overview_zoom2x_check.png`, `scripts/aou/`, `tests/test_aou_stats.py` and `docs/v13|v14/*.err`. Fix: commit only the files the queue file lists (figure scripts, `docs/paper/figures_latent/` including `panelD_groupings/`, the deck builder, the deck, `pipeline.md`, this report, `FIGURE2D_RESULTS.md`).
