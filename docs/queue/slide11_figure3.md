# Queued deck edit, 2026-10-14: slide 11 (Figure 3) new panel C = agreement, demographics + AI representations vs conventional PS; old panel C moves to an appendix slide

You are running unattended in tmux. Read first:
- `CLAUDE.md`, `handoff.md` §1 and `pipeline.md` (2026-10-14 updates: the s31 primary set);
- `docs/queue/figure4.md` (audited numbers and wording rules);
- the latest results: `docs/queue/FIGURE3_RESULTS.md` and `docs/queue/SLIDE9_PANELD_RESULTS.md`.

**Rules:**
- Write only under `/mnt/raid0/rbc58` and this repo (code and docs).
- Aggregates only; no counts of 1–10 (including derivable ones); no n_pairs, retention, ESS or patient keys in HTML or figures.
- Never commit restricted files; never push. No GPU.
- Python: `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`.
- Set the Playwright environment variables inside Python (`os.environ`), as in the earlier queue jobs.
- Log each step, one line each, to `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide11c-20261014/STATUS.md` (`umask 077`).
- Don't edit `paper.md`, `paper2.md`, `table1_picot.md` or any `.docx`.
- **Deck only:**
  - don't modify `build_lab_deck.py`, `build_lab_deck_v2.py` or their HTML;
  - don't modify `scripts/figures/make_figure3_latent.py` or the paper's Figure 3 PNG/PDF.
- Run verifier subagents in the **foreground** (not background).

**Builder:** `scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`. Slide 11 is "Results: agreement with the RCTs (Figure 3)" (`s-res3`).

## User decisions (2026-10-14)

- Slide 11 keeps panels **A** (scatter) and **B** (agreement ladder) **unchanged**.
- **The new panel C** is a **full-width vertical bar chart** of agreement (mean |Δ log HR| vs RCT): **conventional PS** vs **demographics + AI representations**. It replaces the old panel C (agreement by emulation quality).
- **The old panel C** moves to a **new appendix slide**, linked from slide 11.
- **Deck only.** The paper's Figure 3 stays as it is for now.

**Mock-up to match:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig3-20261014/mockup/figure3_v4.png`, panel C (script `f3_v4.py` in the same folder). **Match its panel C exactly**, apart from the layout fixes below.

## Step 1: the new panel C (deck-only PNG)

1. **New script** `scripts/figures/make_slide11_panelC_agreement.py`.
   - **Numbers:** reuse the code of `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig4-standalone-20261014/f4_numbers.py` / `f4_hdps.py` (import or copy; don't modify the audit files).
   - **Style:** reuse `make_figure3_latent.py` / `make_figure2_latent.py` (import their helpers; don't modify them).
2. **Basis:**
   - s31 (31 trials); main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1); log HRs of the existing cells.
   - Demo = rung P1 (age, sex, index year).
   - Unmatched HR = `claude-v18-embed-compare/results.csv`, rung `none`, as in `f4_numbers.py`.
   - PS-Clinical = no LVEF, 5-draw MI.
3. **The panel:**
   - **Bars:** vertical bars of mean |Δ log HR| vs RCT, left to right:
     - Unmatched (grey);
     - PS-CVD5, hdPS, PS-Clinical† (conventional);
     - a dotted vertical divider;
     - Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T.
   - **Group captions** above each side, in grey: "Conventional PS" and "Demographics + AI representations".
   - **Values:** printed on top of each bar, 3 decimals.
   - **Comparison labels:** above each of the three representation bars, stacked as "vs PS-CVD5: / *d* (P = …)" and "vs hdPS: / *d* (P = …)".
     - *d* is the paired difference in mean |Δ log HR| (sign shown).
     - P is the two-sided sign-flip across 31 trials, unadjusted.
     - Print P below .1 to 3 decimals (e.g. .055, .037), otherwise 2.
     - No asterisks.
   - **Axes:** y-axis "Mean |Δ log HR| vs RCT" with "lower = closer"; title "C. Agreement: demographics + AI representations vs conventional PS".
   - **Footnote** (2 short lines, inside the PNG): "Demo = age, sex, index year; ECG = 32 PCs of the pre-index ECG embedding; CLMBR-T = 64 PCs of a foundation-model embedding of the coded pre-index EHR. Labels: paired differences; two-sided sign-flip P across 31 trials, unadjusted. † PS-Clinical without LVEF (5-draw MI). The gains are not trial-specific (benchmark-permutation P = .26 for Demo + ECG + CLMBR-T vs PS-CVD5, two-sided)."
4. **Colours:** the figure4.md palette:
   - grey `#7a7c8c`; PS-CVD5 navy `#0d1040`; hdPS `#3a8fb7`; PS-Clinical gold `#c9a227`;
   - Demo + ECG red `#d9534f`; Demo + ECG + CLMBR-T purple `#7b4fa0`;
   - Demo + CLMBR-T in the CLMBR-T green that `make_figure2_latent.py` uses.
5. **Size and layout:**
   - The PNG spans the **full width** of the slide-11 figure box, under A and B (the old C was centred, narrower). Keep the figure box height.
   - **Make sure the stacked comparison labels don't overlap each other or the value labels.** In the mock-up they're tight; widen the spacing or shrink the font slightly if needed.
   - **Outputs:** `docs/paper/figures_latent/panels/deck/slide11_panelC_agreement.png` (and `.pdf`); values to `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide11c-20261014/panelC_values.json`.
6. **Expected values** (audited, from `figure4.md` and the mock-up; stop and log any mismatch beyond display precision):
   - **Mean |Δ log HR|:** Unmatched 0.248, PS-CVD5 0.232, hdPS 0.182, PS-Clinical 0.171, Demo + ECG 0.207, Demo + CLMBR-T 0.174, Demo + ECG + CLMBR-T 0.164.
   - **vs PS-CVD5:** Demo + ECG −0.026 (P = .20); Demo + CLMBR-T −0.058 (P = .055); Demo + ECG + CLMBR-T −0.068 (P = .037).
   - **vs hdPS:** Demo + ECG +0.025 (P = .56); Demo + CLMBR-T −0.008 (P = .71); Demo + ECG + CLMBR-T −0.018 (P = .21).
   - Also cross-check against `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig4-standalone-20261014/recomputed_f4.json`.
   - **Consistency:** Demo + ECG and Demo + CLMBR-T must equal slide 11 panel B's PS-Demo "+ ECG" (0.207) and "+ CLMBR-T" (0.174) points.
7. **View the PNG** (Read tool) at deck size and fix any overlap or clipping.

## Step 2: the deck

1. **Slide 11:**
   - Click 1 → A; click 2 → B; click 3 → the **new** panel C, full width under A and B (same reveal mechanism, no subtitle).
   - Update the figure box's `aria-label` caption so that C describes the new panel.
   - **Bottom-left "More:" link:** add "**A7 · Agreement by emulation quality**" (or the next free appendix number), with the usual style.
2. **New appendix slide "Agreement by emulation quality (PS-CVD5)":**
   - the existing old panel C PNG (`docs/paper/figures_latent/panels/figure3_rct_agreement_C.png`), centred, at a readable size;
   - one plain line: "Mean |Δ log HR| vs RCT with PS-CVD5: Excellent + Good (14) 0.230 / 0.176 / 0.149 / 0.152 vs Moderate (17) 0.235 / 0.217 / 0.185 / 0.168 (PS alone / + ECG / + CLMBR-T / + both)", taken from the existing claims / `figure3_values.json` (no new numbers);
   - a back-link "Back to slide 11".
   - **Placement:** append it at the end of the appendix (after the current last appendix slide), so no existing appendix number changes. Check that every existing appendix label and link still resolves.
3. **Claims:**
   - move the old panel C claims to the new appendix slide;
   - add claims for every new panel C value (7 means; 6 contrasts with P), each checked against an independent recomputation from the cells and against the expected values above.
4. **Unchanged:**
   - every other slide, animation, popup and the explorers;
   - slide 5 empty; slide 9 as the slide9 job left it;
   - the take-home slide (no new CLMBR-T claim there);
   - the existing "agreement by quality" main slide (note in the summary that it overlaps the new appendix slide, for the user).
   - The embedded data block should be byte-identical unless the change requires otherwise (log it).
5. **Wording rules** (figure4.md):
   - say "Demographics + AI representations";
   - never call CLMBR-T "unstructured";
   - no claim that the representations "replicate" trials better (they are "closer on average", not trial-specific).

## Step 3: verification (a fresh verifier subagent, foreground, that built nothing)

The verifier checks:
- **Every new panel C value,** recomputed independently from the cells (or matched to `recomputed_f4.json`), including all 6 contrasts and their P values.
- **Screenshots** of slide 11 reveal steps 0–3 and the new appendix slide, at 1920×1080 and 1366×768. Nothing clipped or overlapping, **especially the stacked comparison labels**.
- **All appendix links and back-links;** the new "More:" link lands on the new appendix slide.
- **0 console or page errors** over all slides.
- **The wording rules;** a privacy scan of the HTML and the new PNG.

Fix BLOCKING issues and re-verify, up to 3 rounds. Report: `docs/presentation/VERIFY_SLIDE11_PANELC.md`.

## Step 4: commit and summary

1. **Add one line to `pipeline.md`'s deviations log:** "2026-10-14: deck slide 11 panel C shows agreement (mean |Δ log HR|) for demographics + AI representations (ECG, CLMBR-T) vs conventional PS; the quality-tier panel moved to an appendix slide; deck only, paper Figure 3 unchanged; CLMBR-T still not in the take-home claims."
2. **Commit locally:** the new script, the panel PNG/PDF, the builder, the deck, the verify report and `pipeline.md`. Don't push. Don't stage the user's uncommitted files (e.g. `docs/paper/table1_picot.md`).
3. **Write the summary** at the top of the status log and in `docs/queue/SLIDE11_PANELC_RESULTS.md` (commit). Cover:
   - what changed;
   - the panel C values;
   - the new appendix slide's number;
   - the verification verdict;
   - anything for the user to check.
