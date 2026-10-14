# Verification: slide 9 new panel D (overall balance) and appendix A4 (2026-10-14)

**Verdict: PASS with minor issues** (0 BLOCKING; round 1 had 4 MINOR, and round 2 fixed number 3, leaving 3 open; see "Round 2" at the end).

Independent verifier; built nothing. Spec: `docs/queue/slide9_panelD.md`; wording rules and audited numbers: `docs/queue/figure4.md`.
Scratch code, outputs and screenshots: `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide9d-20261014/verify/` (screenshots in `shots/`).

## Checks

| # | Check | Result |
|---|---|---|
| 1 | Values recomputed from the cells with own code (`recompute.py`; `BE.load_grid()` with `NOLVEF` = `claude-v1-psclin-mi/.../restricted_cells_v1_mi_v1layout.parquet`, s31, 54 items, own masks; paired contrasts on items observed in both cells; two-sided P by `BE.signflip_1s` and by an own exact enumeration) | PASS. All 7 means and 3 contrasts match `panelD_values.json` and `recomputed_f4.json` exactly (max deviation 0.0). Display values match the PNG, the claims table and figure4.md. "lower"/"higher" are right by sign. Own exact P = `BE` P. |
| 2 | Screenshots at 1920×1080 and 1366×768: slide 9 steps 0–3, A4, A4 popup tabs 0–3 | PASS. Step 0 = legend only; 1 = A + B; 2 = + C; 3 = + new D. Every element sits inside the viewport and figure box. No overlap between C and D. Popup opens from both the panel and the hint, and closes with Esc, Close and a click outside (all 6 combinations, both viewports). Each tab shows exactly one view. Arrow, PageDown, Space and Down keys leave slide and step unchanged while the popup is open. Reopening starts on tab 0. Slide 9 has no `data-pop`, no `.f2hint` and no modal; a click on the new D opens nothing. |
| 3 | Links after renumbering | PASS. Hashes #1–#18 and #A1–#A6 land correctly; key traversal covers all 24 slides in order. Every "More:" link, including those inside popups, lands on the slide its label names: A4 = per-trial panel, A5 = framework v2.0, A6 = spec-v2 fixes. The return back-link works for every link. Slide 9's "More:" reads "A4 · Per-trial covariate balance improvement · A5 · Framework v2.0 (sensitivity) · A6 · Spec-v2 cohort fixes (sensitivity)". A4's "Back to slide 9" (href #9) works. No stale label in visible or hidden text: slide 6 "(A5)", robustness "(sensitivity; A6)" / "(sensitivity; A5)". |
| 4 | Console and page errors over all 24 slides, both viewports (plus HEAD-deck run) | PASS: 0 errors in all 12 page sessions. |
| 5 | Unchanged elsewhere vs `git show HEAD:` deck | PASS. `const D = …;` is byte-identical, and so is the single `<script>` block. Sections s-title, s-bg, s-prob, s-aims, s-over, s-meth1, s-meth2, s-res3, s-emu, s-agq, s-plas, s-mimic, s-take, s-dec, a-qual, a-t1 and a-panel are identical. s-pipe, s-bal, s-rob, a-fw and a-fix differ only in A4→A5 / A5→A6 labels. s-res2 differs only in the panel D image and alt text, the removed hint and popup, and the "More:" line. The `pop-f2d` popup markup on A4 is byte-identical to HEAD's. CSS changes are limited to the moved hint and box rules. Slide 5's body is empty; the take-home slide is identical, with 0 CLMBR mentions. |
| 6 | Wording rules (figure4.md) | PASS. The PNG group caption reads "Demographics + AI representations". CLMBR-T is never called "unstructured"; the only "unstructured" is the unchanged aims sentence about LATENT-RCT in general, as in HEAD. No "replicate" claim: the 2 "replicat" hits are the unchanged plasmode slide's "50 replicates" and "No representation substitutes…", as in HEAD. The footnote matches the spec text verbatim. |
| 7 | Privacy scan of the HTML (visible text, alt texts, embedded data) and the new PNG/PDF | PASS. No n_pairs, retention, ESS or patient-key/identifier tokens anywhere (new or HEAD). The new content has no patient counts; its only numbers are trial and item counts and aggregates. PNG/PDF metadata is Matplotlib only. No CSV, parquet or JSON in `git status`. |
| 8 | Paper Figure 2 PNG/PDF, `make_figure2_latent.py`, `build_lab_deck.py`, `build_lab_deck_v2.py` | PASS. All unmodified (`git status`, `git diff --stat`). Only `docs/presentation/ecg_tte_lab_2026_10_15.html` and `scripts/build_lab_deck_1015.py` are modified by the job, plus the new script and `panels/deck/` files. `docs/paper/table1_picot.md` was already modified before the job and belongs to the user. |

## Recomputed values (s31, main, 54 held-out items)

| Arm | Mean \|SMD\| (own) | Shown | vs hdPS (own): relative change, two-sided sign-flip P | Shown label |
|---|---|---|---|---|
| Unmatched | 0.14281 | 0.143 | | |
| PS-CVD5 | 0.12857 | 0.129 | | |
| hdPS | 0.11416 | 0.114 | reference | |
| PS-Clinical† | 0.11791 | 0.118 | | |
| Demo + ECG | 0.12587 | 0.126 | −10.18% (higher), P = 0.02858 | 10.2% higher than hdPS (P = .029) |
| Demo + CLMBR-T | 0.11189 | 0.112 | +2.05% (lower), P = 0.5310 | 2.0% lower than hdPS (P = .53) |
| Demo + ECG + CLMBR-T | 0.10568 | 0.106 | +8.01% (lower), P = 0.01248 | 8.0% lower than hdPS (P = .012) |

† Mean over about 45 items per trial (its own inputs masked). The shown values match figure4.md's expected values: .0286 is .03 at 2 decimals and .029 at 3.

## BLOCKING findings

None.

## MINOR findings

1. **P format (builder's choice): acceptable.**
   - Demo + ECG vs hdPS prints P = .029 where figure4.md writes .03. This is the same value; the panel uses the deck's static-slide format (3 decimals below .1), consistently for all three labels.
   - The deck as a whole mixes formats: the A4 line and the per-trial panel print the Figure 2 format, "P = .02" (the exact value is .015).
   - Both formats are as specified, so this is cosmetic only.
2. **Footnote is 3 lines, not "2 short lines" (builder's choice): acceptable.**
   - The text is verbatim and nothing is clipped.
   - It is small on screen: about 9 px type at 1920×1080 and about 6–7 px at 1366×768. That is barely legible at 1366, though comparable to panel A's item labels.
   - If legibility matters, shorten the wording rather than shrinking it further.
3. **(Resolved in round 2.) hdPS reference line touches the value labels (new PNG).** The dashed line at 0.114 sits directly against the "0.112" label (Demo + CLMBR-T) and runs through the "0.106" label (Demo + ECG + CLMBR-T), between "0" and ".106". Both stay legible. A white background box on the value labels (or a lower zorder for the line) would fix it.
4. **A click on fully built slide 9 now advances to slide 10.** Previously a click on panel D opened the popup. Advancing is the deck's standard behaviour on any built slide and is consistent with "no popup on slide 9"; noted only so the presenter expects it.

Not findings, but noted: panels A and B overlap slightly as image boxes (transparent margins, no visible overlap; the positions are unchanged from HEAD). Link-text titles are short forms of the slide titles (e.g. "Framework v2.0" → "Emulation-quality framework v2.0"), as in HEAD.

## Screenshots

`/mnt/raid0/rbc58/ecg-tte/audits/claude-slide9d-20261014/verify/shots/`, at both viewports (`*_1920x1080.png`, `*_1366x768.png`):
- `s9_step0` to `s9_step3`;
- `A4`;
- `A4_pop_tab0` to `A4_pop_tab3`.

Scripts: `recompute.py`, `compare_values.py`, `compare_html.py`, `show_af2d.py`, `pw_check.py` (results in `pw_results.json`), `privacy.py`, `crop.py`.

## Round 2 (re-check after the fix to minor issue 3)

**Verdict: PASS with minor issues** (0 BLOCKING; MINOR 1, 2 and 4 open, number 3 resolved).

Fix under test: in `make_slide9_panelD_overall.py`, the value labels of bars that end at or just short of the hdPS line now start to the right of the dashed line. The PNG/PDF were regenerated and the deck rebuilt.

| Check | Result |
|---|---|
| New PNG viewed (full size and 2.5× crop around the line) and slide 9 step 3 re-screenshotted at 1920×1080 and 1366×768 | PASS. "0.112", "0.106" and "0.114" all start clearly to the right of the dashed line, with a visible gap. The line touches no label, and the group caption is clear of it. Nothing clipped or overlapping; the panel stays inside the figure box at both viewports. |
| Values in the PNG unchanged | PASS. The 7 means (0.143, 0.129, 0.114, 0.118, 0.126, 0.112, 0.106) and the 3 labels (10.2% higher, P = .029; 2.0% lower, P = .53; 8.0% lower, P = .012) are unchanged. `panelD_values.json` still matches my recomputation and `recomputed_f4.json` exactly (deviation 0.0). |
| Deck vs round 1 | PASS. The HEAD-vs-new section diff is the same as in round 1, except that the s-res2 panel D image changed (hash `dc1837eb` → `1094a499`; file grew by 128 bytes). `const D` and the script block are still byte-identical to HEAD. The A4 image (`0e6da894`) is unchanged and its popup still matches HEAD byte for byte. Every other section and the CSS are unchanged from round 1. |
| Console and page errors, all 24 slides, both viewports | PASS: 0 in all 12 sessions. Reveal steps, hashes, key traversal, every "More:" link and back-link, and the A4 popup open/close/tab/key checks all re-pass, with the same results as round 1. |

Round 2 screenshots: `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide9d-20261014/verify/shots_r2/` (results in `pw_results_r2.json`; crop `crop_dashline_r2.png`).
