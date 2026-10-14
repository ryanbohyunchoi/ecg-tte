# Queued deck edit, 2026-10-14: slide 9 (Figure 2) new panel D = overall balance, AI representations vs conventional PS; old panel D moves to appendix A4

You are running unattended in tmux. Read `CLAUDE.md`, `handoff.md` §1, `pipeline.md` (2026-10-14 updates: s31 primary set), `docs/queue/figure4.md` (audited numbers and wording rules), and the latest results files `docs/queue/FIGURE2D_RESULTS.md` and `docs/queue/FIGURE3_RESULTS.md`.

**Rules:**
- Write only under `/mnt/raid0/rbc58` and this repo (code and docs).
- Aggregates only; no counts of 1–10 (including derivable ones); no n_pairs, retention, ESS or patient keys in HTML or figures.
- Never commit restricted files; never push. No GPU.
- Python: `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`.
- Set the Playwright environment variables inside Python (`os.environ`), as in the earlier queue jobs (see `handoff.md` §2 and the fig2d / fig3 job scripts).
- Log each step, one line each, to `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide9d-20261014/STATUS.md` (`umask 077`).
- Don't edit `paper.md`, `paper2.md`, `table1_picot.md` or any `.docx`.
- Don't modify `build_lab_deck.py`, `build_lab_deck_v2.py` or their HTML; don't modify `scripts/figures/make_figure2_latent.py` or the paper's Figure 2 PNG/PDF (**deck only**; the paper figure stays as it is).
- Run verifier subagents in the **foreground** (not background).

**Builder:** `scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`. Slide 9 is "Results 1: covariate balance (Figure 2)" (`s-res2`).

## User decisions (2026-10-14)

- Panel D on slide 9 becomes an **overall-balance comparison**: conventional PS vs demographics + AI representations.
- Rows: **PS-CVD5, hdPS, PS-Clinical** (conventional) and **Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T** (representations), with Unmatched as a grey reference.
- Bar labels compare **against hdPS only**.
- **Deck slide 9 only**; the paper's Figure 2 is unchanged for now.
- The old per-trial panel D (and its groupings popup) moves to a **new appendix slide A4**, linked from slide 9.
- **No separate Figure 4 slide** (figure4.md's "Deck" section is superseded by this file).

## Step 1: the new panel (deck-only PNG)

1. **New script** `scripts/figures/make_slide9_panelD_overall.py`. Reuse the numbers code in `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig4-standalone-20261014/f4_numbers.py` / `f4_hdps.py` (import or copy into the repo script; don't modify the audit files) and the style of `make_figure2_latent.py` (import its helpers; don't modify it).
2. **Basis:** s31 (31 trials); main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1); 54 held-out items with the `pipeline.md` §6 masks. Demo = rung P1 (age, sex, index year). Paired contrasts use only items observed in both arms.
3. **Panel:** horizontal bars of mean |SMD| over the 54 items, top to bottom:
   - Unmatched (grey, reference);
   - PS-CVD5, hdPS, PS-Clinical† (conventional);
   - a dotted divider, with small group captions "Conventional PS" / "Demographics + AI representations";
   - Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T.
   - Value printed at each bar end (3 decimals).
   - Right-aligned label on each of the three representation rows: "*x*% lower than hdPS (P = …)" or "*x*% higher than hdPS (P = …)", sign-driven in code; two-sided sign-flip P, unadjusted; no asterisks.
   - A vertical dashed line at the hdPS value.
   - Title: "D. Overall balance: AI representations vs conventional PS".
4. **Colours:** the figure4.md palette (grey `#7a7c8c`, PS-CVD5 navy `#0d1040`, hdPS `#3a8fb7`, PS-Clinical gold `#c9a227`, ECG red `#d9534f`, ECG + CLMBR-T purple `#7b4fa0`); Demo + CLMBR-T in the CLMBR-T colour that `make_figure2_latent.py` uses for "PS + CLMBR-T".
5. **Footnote (2 short lines, inside the PNG):** "Demo = age, sex, index year; ECG = 32 PCs of the pre-index ECG embedding; CLMBR-T = 64 PCs of a foundation-model embedding of the coded pre-index EHR. Labels: paired differences vs hdPS over items observed in both arms; two-sided sign-flip P across 31 trials, unadjusted. † PS-Clinical on the ~45 items that are not its inputs."
6. **Size:** the PNG must fit the current panel D slot of the slide 9 layout (same width as panels C/D row; keep the figure box height). Output: `docs/paper/figures_latent/panels/deck/slide9_panelD_overall.png` (and `.pdf`), values to `/mnt/raid0/rbc58/ecg-tte/audits/claude-slide9d-20261014/panelD_values.json`.
7. **Expected values** (from `figure4.md`, audited; stop and log any mismatch beyond display precision):
   - mean |SMD|: Unmatched 0.143, PS-CVD5 0.129, hdPS 0.114, PS-Clinical† 0.118, Demo + ECG 0.126, Demo + CLMBR-T 0.112, Demo + ECG + CLMBR-T 0.106;
   - vs hdPS: Demo + ECG 10.2% higher (P = .03); Demo + CLMBR-T 2.0% lower (P = .53); Demo + ECG + CLMBR-T 8.0% lower (P = .012).
   - Also cross-check against `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig4-standalone-20261014/recomputed_f4.json`.
8. View the PNG (Read tool) at deck size and fix any overlap or clipping.

## Step 2: the deck

1. **Slide 9:**
   - Click 1 → A + B; click 2 → C; click 3 → the **new** panel D (same reveal mechanism; keep the legend; no subtitle).
   - Remove the "Click for other groupings ›" hint and the panel D popup trigger from slide 9.
   - The figure legend at the top covers panels A–C; the new D carries its own row labels, so no legend change is needed. If the shared legend would mislead for D, add nothing; D is self-labelled.
   - Bottom-left "More:" links: add **"A4 · Per-trial covariate balance improvement"** first, then keep the existing links (framework v2.0, spec-v2 fixes) with their new numbers.
2. **New appendix slide A4** "Per-trial covariate balance improvement (PS-CVD5 + ECG vs PS-CVD5)":
   - the existing per-trial panel D PNG (the Figure 2D job's version, coloured by cardiac-physiology decision), full width;
   - the groupings popup moves here unchanged (click the panel or the hint "Click for other groupings ›"; same `popup()` behaviour, tabs, Esc/close/click-outside, arrow keys blocked while open);
   - one line: "19 of 31 trials improved; mean +3.3 points in % of items with |SMD| < 0.1; P = .02 (exact one-sided sign-flip)", taken from the existing claims/values (no new numbers);
   - back-link "Back to slide 9".
3. **Appendix order:** insert A4 after A3 (held-out panel) in `APP`; framework v2.0 becomes **A5**, spec-v2 fixes **A6**. All labels, "More:" lines, in-text references (e.g. "(sensitivity; A4)" → A5) and back-links update automatically or by hand; check them all.
4. **Claims:** move the panel D claims to A4; add claims for every new panel D value (7 means, 3 contrasts with P), each checked against `build_balance_explorer.pair_stats`-style recomputation on the cells and against the expected values above.
5. **Unchanged:** every other slide, animation, popup and the explorers; slide 5 empty; the take-home slide (no new CLMBR-T claim there). The embedded data block should be byte-identical unless the move requires otherwise (log it).
6. **Wording rules** (figure4.md): say "Demographics + AI representations"; never call CLMBR-T "unstructured"; no claim that representations "replicate" trials better.

## Step 3: verification (fresh verifier subagent, foreground, built nothing)

Checks:
- every panel D value recomputed independently from the cells (or matched to `recomputed_f4.json`), including the three vs-hdPS contrasts and P values;
- slide 9 reveal steps 0–3 and A4 (with popup and every tab) screenshotted at 1920×1080 and 1366×768; nothing clipped or overlapping;
- all appendix links and back-links after renumbering; no stale "A4" pointing to framework v2.0;
- 0 console or page errors over all slides;
- wording rules; privacy scan of the HTML and the new PNG.

Fix BLOCKING issues and re-verify, up to 3 rounds. Report: `docs/presentation/VERIFY_SLIDE9_PANELD.md`.

## Step 4: commit and summary

1. **`pipeline.md` deviations log**, one line: "2026-10-14: deck slide 9 panel D shows demographics + AI representations (ECG, CLMBR-T) vs conventional PS (PS-CVD5, hdPS, PS-Clinical) as a comparison; per-trial panel moved to appendix A4; deck only, paper Figure 2 unchanged; CLMBR-T still not in the take-home claims."
2. **`docs/queue/figure4.md`:** add a short note under "Decisions pending" that decision 2 is resolved as "deck slide 9 panel D only; no separate Figure 4 slide" (decision 1 stays open for the paper).
3. **Commit locally:** the new script, the panel PNG/PDF, the builder, the deck, the verify report, `pipeline.md`, `figure4.md`. Don't push. Don't stage the user's uncommitted files.
4. **Summary** at the top of the status log and in `docs/queue/SLIDE9_PANELD_RESULTS.md` (commit): what changed, the panel D values, the new appendix numbering, the verification verdict, anything for the user to check.
