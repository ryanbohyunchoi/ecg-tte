# Verification: deck slide 11 new panel C and appendix A7 (2026-10-14)

Independent verifier (built nothing). Spec: `docs/queue/slide11_figure3.md` (Step 3); wording: `docs/queue/figure4.md`.
Verifier scripts and outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide11c-20261014/verify/` (`recompute.py`, `htmldiff.py`,
`imgcheck.py`, `pw_check.py`, `scan.py`, `gaps.py` and their JSON). All counts below are aggregates; no patient-level data were printed.

## Verdict: **PASS with minor issues** (0 BLOCKING, 3 MINOR)

## 1. Values (recomputed independently from the cells)

**Method:**
- The s31 set comes from `docs/v19/quality_tiers.json`: tier not Limited, minus PROTECT AF, which gives 31.
- The `main` cells: P5 / hdPS200 / P1 from `claude-v21-paper2`; `clinical_nolvef` from `claude-v1-psclin-mi`; Unmatched from v18 with `half == full` and `rung == none`.
- No failed cells. The RCT log HRs agree across sources (max deviation 8e-17).
- The sign-flip P is my own exact meet-in-the-middle over all 2^31 sign vectors. Two-sided = min(1, 2 · min one-sided), and it is identical to the |S| ≥ |s_obs| version.

| Value | Shown (panel) | Recomputed | recomputed_f4.json | Queue expected |
|---|---|---|---|---|
| Unmatched | 0.248 | 0.24755 | same | 0.248 |
| PS-CVD5 | 0.232 | 0.23236 | same | 0.232 |
| hdPS | 0.182 | 0.18162 | same | 0.182 |
| PS-Clinical† | 0.171 | 0.17146 | same | 0.171 |
| Demo + ECG | 0.207 | 0.20681 | same | 0.207 |
| Demo + CLMBR-T | 0.174 | 0.17393 | same | 0.174 |
| Demo + ECG + CLMBR-T | 0.164 | 0.16409 | same | 0.164 |
| Demo + ECG vs PS-CVD5 | −0.026 (P = .20) | −0.02555, P = 0.2020 | same | −0.026, .20 |
| Demo + CLMBR-T vs PS-CVD5 | −0.058 (P = .055) | −0.05843, P = 0.05454 | same | −0.058, .055 |
| Demo + ECG + CLMBR-T vs PS-CVD5 | −0.068 (P = .037) | −0.06827, P = 0.03725 | same | −0.068, .037 |
| Demo + ECG vs hdPS | +0.025 (P = .56) | +0.02519, P = 0.5621 | same | +0.025, .56 |
| Demo + CLMBR-T vs hdPS | −0.008 (P = .71) | −0.00769, P = 0.7095 | same | −0.008, .71 |
| Demo + ECG + CLMBR-T vs hdPS | −0.018 (P = .21) | −0.01753, P = 0.2129 | same | −0.018, .21 |
| Footnote benchmark-permutation P | .26 | `bshuf_p_two` = 0.2606 | — | .26 |

**Agreement with other files:**
- Max deviation vs `recomputed_f4.json` and `panelC_values.json`: means and differences ≤ 3e-17; P ≤ 3e-9 (float tolerance).
- The 6 label strings are identical to my recomputed labels.
- The P display rule holds: 3 decimals below .1 (.055, .037), otherwise 2.
- **Consistency with panel B:** Demo + ECG 0.207 and Demo + CLMBR-T 0.174 equal `figure3_values.json` B.P1 (0.206813, 0.173931; deviation < 1e-7). PS-CVD5, hdPS and PS-Clinical also equal panel B's "PS alone" points.
- **A7 line:** I recomputed it from the P5 cells by v19 tier, giving Excellent + Good (14 trials) 0.230 / 0.176 / 0.149 / 0.152 and Moderate (17 trials) 0.235 / 0.217 / 0.185 / 0.168. This equals `figure3_values.json` C (deviation < 5e-7) and the text on A7.
- The builder's claims (`deck/claims.md`): all 13 new slide 11 claims and the 11 claims moved to A7 are marked "yes".

## 2. The panel PNG vs the mock-up and the spec

`docs/paper/figures_latent/panels/deck/slide11_panelC_agreement.png` (2215 × 830) was viewed and matches the mock-up's panel C (`figure3_v4.png`):
- **Bar order:** Unmatched, PS-CVD5, hdPS, PS-Clinical†, a dotted divider, then Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T.
- **Bar colours** (sampled from the pixels): #7a7c8c, #0d1040, #3a8fb7, #c9a227, #d9534f, #2a7f62 (= `GREEN` in `make_figure2_latent.py`), #7b4fa0. All as specified.
- **Text elements:**
  - grey group captions;
  - values with 3 decimals;
  - stacked "vs PS-CVD5: / d (P = …)" and "vs hdPS: / d (P = …)" labels, using the true minus sign;
  - y-axis "Mean |Δ log HR| vs RCT / lower = closer";
  - title "Agreement: demographics + AI representations vs conventional PS" with the panel letter C;
  - the 2-line footnote, verbatim from the spec;
  - no asterisks.
- **Label spacing**, measured in the PNG pixels:
  - between lines within a label: ≥ 7 px;
  - between the two labels: 23 px;
  - from the label to the value label, and from the value label to the bar: 15 px;
  - horizontal clearance between neighbouring label columns: ≥ 160 px.
  - There is no overlap; the labels are more widely spaced than in the mock-up.

## 3. Screenshots (`verify/shots/`)

- `s11_step0..3_1920x1080.png`, `s11_step0..3_1366x768.png`;
- `s11_panelC_crop_1920x1080.png`, `s11_panelC_crop_1366x768.png`;
- `A7_1920x1080.png`, `A7_1366x768.png`, `A7_from11_*.png`.

**Results:**
- **Reveal:** step 0 empty; 1 → A; 2 → A + B; 3 → A + B + full-width C.
- **Panel C position:** it spans the full figure-box width (1058 px at 1920; 752 px at 1366), bottom-aligned under A and B. The figure box keeps its size (705 × 580 design px).
- **Layout:** no panel overlaps another or leaves the figure box, stage or viewport, at either size. The "More:" link sits below the rule and doesn't overlap the figure.
- **A7:** the image is centred and the summary line wraps to 2 lines. Nothing is clipped at either size.

## 4. Links, navigation, errors

- **Slide 11:** "More: A7 · Agreement by emulation quality" → `A7 · 25 / 25`; A7's "Back to slide 11" → `11 / 25` (both sizes).
- **Cross-links:** all 15 non-back cross-links work, including the 3 inside the slide 6 popups. Each lands on its target, and every back-link returns to the slide it came from, at both sizes.
- **Default back-links:** A1–A7 → 6, 6, 8, 9, 9, 13, 11.
- **Hash navigation:** #1–#18 and #A1–#A7 all land correctly; the nav text matches ("11 / 25", "A7 · 25 / 25").
- **Keyboard:** forward order 1–18, then A1–A7 (25 slides, 56 key steps); backward order is the exact reverse.
- **Console and page errors:** 0 at 1920 × 1080 and 1366 × 768, across all 25 slides and every reveal step, plus the old- and new-deck text passes.

## 5. Unchanged checks (previous HTML = the saved `.before.html`)

**The deck HTML:**
- Every section other than `s-res3` is byte-identical, and `a-f3q` is new. The rendered text, hidden text and alt/aria text are identical for all 23 other slides.
- `s-res3` changes only in three places: panel C's image and alt text, the aria-label clause for C, and the new "More:" line.
- Outside the sections, only 3 CSS lines were added (`.f3ql`, `img.f3q`).
- The JS/data `<script>` block is byte-identical (SHA-256 prefix 3f8b3f4bb046c2ce).

**Images:**
- Slide 11 panels A and B: embedded data identical to before.
- The decoded embeds match their source PNGs (correlation > 0.9998): new C = `slide11_panelC_agreement.png`; A7 = `figure3_rct_agreement_C.png`.

**Other slides:**
- Slide 5 (`s-over`) body is empty.
- The take-home slide (`s-take`) is identical and has no CLMBR-T claim.

**Files (`git status` / `git diff --stat HEAD`):**
- No changes to:
  - `make_figure3_latent.py` and `make_figure2_latent.py`;
  - `figure3_rct_agreement.png` / `.pdf` and `panels/figure3_rct_agreement_*.png`;
  - `build_lab_deck.py`, `build_lab_deck_v2.py` and the 10-01 / 10-09 HTML.
- The only tracked change in the deck HTML is the 11+/2− lines above.
- `table1_picot.md` is the user's own pre-existing edit, not this job's.

## 6. Wording

The new HTML text and the panel were checked:
- They say "Demographics + AI representations" (2× in the panel / aria text; the alt text uses lowercase "demographics + AI representations").
- They don't call CLMBR-T "unstructured", don't say "replicate" or "representations alone", and have no asterisks.

The rest of the deck has one pre-existing "unstructured" on the unchanged aims slide ("bring unstructured information into trial emulation"). It is not about CLMBR-T and was not introduced by this change.

## 7. Privacy

I scanned the new `s-res3` / `a-f3q` HTML (text, alt and aria) and the panel text:
- **Excluded content:** none of n_pairs, pairs, retention / retain, ESS or patient keys appear.
- **Numbers:** the only integers are 31 trials, 14 / 17 trials, 32 / 64 PCs and "5-draw MI" (a number of imputation draws, not a count of people).
- **Counts of 1–10:** none appear and none can be derived; the trial counts are aggregates above 10.

## Issues

| # | Severity | Issue | Fix |
|---|---|---|---|
| 1 | MINOR | **Small text in panel C at deck size.** The figure box is scaled, so the footnote's ink height is about 9.6 px at 1920 × 1080 and 6.8 px at 1366 × 768. The comparison-label lines are about 7.6 / 5.4 px. This is legible in the screenshots but small on a projector. (Panels A and B are scaled the same way, and the mock-up looks the same.) | Optional: in `make_slide11_panelC_agreement.py`, raise the footnote and label font sizes by about 15–25%. The 23 px gap between labels and the 15 px gap to the values leave room. Or move the footnote into HTML under the figure box. |
| 2 | MINOR | The A7 image still carries the paper's panel letter "C" and the title "Agreement by emulation quality (PS-CVD5)", which repeats the slide title. | Optional: crop off the letter, or leave it (the spec asked for the existing PNG unchanged). |
| 3 | MINOR | In `deck/claims.md`, the "shown" column prints the contrasts with an ASCII hyphen (−0.026 appears as "-0.026"), while the panel and the reference column use U+2212. Cosmetic only; the values agree. | Optional: write the shown value with "−" in `f3c_claims`. |

**Note for the user (not an issue):** main slide 14 ("agreement by quality") overlaps the new A7 in content, as the spec anticipated.
