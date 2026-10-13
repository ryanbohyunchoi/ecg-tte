# Queued deck revision, 2026-10-13 afternoon (headless Claude session in tmux `deckq`)

You are running unattended; the user has closed their computer. Read `CLAUDE.md`, `handoff.md` §1 and `pipeline.md` first, including the 2026-10-13 update. The design is fixed:
- **primary:** version 1 cohorts + paper 1's 32 trials (v19 tiers); PS-CVD5; fixed C = 1; 1:1 caliper 0.2;
- **held-out panel:** 54 leakage-corrected items;
- **PS-Clinical:** no LVEF, 5-draw multiple imputation;
- **sensitivities:** the spec-v2 fixed cohorts and framework v2.0;
- **study name:** LATENT-RCT.

**Rules:**
- Write only under `/mnt/raid0/rbc58` and this repo (code and docs).
- Aggregates only; no counts of 1–10 (including derivable ones); no n_pairs, retention, ESS or patient keys in any HTML or figure.
- Never commit CSV, parquet or restricted files; never push.
- Never use GPU 7 (no GPU needed).
- Python: `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`.
- Set the Playwright environment variables inside Python (`os.environ`), not in the shell. Paths: the session scratchpad's `pw`, `pylib` and `syslib/usr/lib/x86_64-linux-gnu` under `/tmp/claude-0/-home-rbc58-github-ecg-tte/28c2d747-4dd0-403d-9171-f38918099ced/scratchpad/`; see `handoff.md` §2.
- Log each step, one line each, to `/mnt/raid0/rbc58/ecg-tte/audits/claude-deckq-20261013/STATUS.md` (`umask 077`).
- Don't edit `docs/paper/paper.md`, `paper2.md`, `table1_picot.md` or any `.docx`.

**Files:**
- **The deck:** `docs/presentation/ecg_tte_lab_2026_10_15.html`, built by `scripts/build_lab_deck_1015.py`. The current build is committed as a checkpoint.
- **Builders not to modify:** `build_lab_deck.py`, `build_lab_deck_v2.py`, and their HTML outputs.
- **Explorer data:** comes via `scripts/build_balance_explorer.py`. Keep its validations passing if you touch it.

## Step 1: manuscript Figure 2 (updated), for the deck and the paper

1. **Find the current script.** Figure 2 is built by `scripts/v20/make_paper_figures.py`; its output is `docs/paper/figures/main/figure2_covariate_balance.png`.
2. **Write a new script** `scripts/figures/make_figure2_latent.py`. Reuse its style and plotting code by importing or copying; don't modify the v20 script.
3. **Output:** `docs/paper/figures_latent/figure2_covariate_balance.{png,pdf}` (300 dpi) and per-panel PNGs.
4. **Basis:** version 1 cohorts, paper 1's 32 trials, 1:1 caliper 0.2, and the **54 leakage-corrected held-out items** with the `pipeline.md` §6 masks.
5. **Panels:**
   - **A.** Love plot: the 54 held-out items (median |SMD| across the 32 trials) for **unmatched, PS-CVD5, and PS-CVD5 + ECG**, grouped by domain.
   - **B.** Mean |SMD| by domain for the same arms.
   - **C.** The PS ladder: mean |SMD| at PS-Demo, PS-CVD5, PS-CVD10, hdPS and PS-Clinical (no LVEF, MI). Plot **unmatched (reference), PS alone, PS + ECG, PS + CLMBR-T, and PS + CLMBR-T + ECG** at each level, with labels giving the relative change for + ECG. **PS-Flags is not shown.**
   - **D.** Keep the original's per-trial panel (change in % balanced with the ECG for PS-CVD5), if it fits cleanly; otherwise drop it and say so.
6. **Sources:**
   - version 1 cells: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/restricted_cells.parquet` (all rungs; CLMBR arms included);
   - PS-CVD10: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-ps10/cells/restricted_cells.parquet`;
   - PS-Clinical (no LVEF, MI): `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet`;
   - unmatched |SMD| as `build_balance_explorer.py` derives it.
7. **Validate:** every plotted summary must equal `build_balance_explorer.py`'s values for the same combination. Expected: PS-CVD5 + ECG 8.8%; ladder ECG labels 11.3 / 8.8 / 5.0 / 7.6 / 3.2. Then view the PNG (Read tool) and fix any overlap or clipping.

## Step 2: deck revisions (the user's feedback)

1. **Slide 5:** keep the slide, its slide number and its footer, but leave the body **empty**. Remove the overview figure from it; the user will add their own.
2. **Slide 6 (LATENT-RCT pipeline):**
   - Keep the existing click-reveal behaviour, and make the flow **populate one step after another**: 99 candidates → feasibility criteria → 38 → emulation-quality criteria → 32 analysed → clinical areas.
   - **Number the feasibility criteria** (1–5).
   - **Popups:** clicking "Feasibility criteria" opens a popup (modal) with the full criteria and examples (as in appendix A1); clicking "Emulation-quality criteria" opens a popup with the rule and examples (as in A2). Each popup has a close button. Popups must not break keyboard navigation (Esc closes; arrow keys only navigate when no popup is open).
3. **Slide 7 (PS / matching methods)**, retitled **"PSM experiments"**. Less text throughout. Changes:
   - **Remove** the "PS information ladder" graphic.
   - **Remove PS-Flags** from the slide (and from main-slide text and explorer defaults; it may remain only in an appendix note).
   - **The PS levels** PS-Demo → PS-CVD5 (primary) → PS-CVD10 → hdPS → PS-Clinical (no LVEF) appear **one at a time** (click reveal).
   - **State explicitly that hdPS inputs are yes/no code flags** (no values, no dates).
   - **After the levels, the comparison options appear one at a time, each with an icon and very short labels, in this order:** **1. + ECG representation**, **2. + CLMBR-T**, **3. + ECG + CLMBR-T**, **4. + permuted placebo** (last).
   - **Links:** add clickable appendix links (or popups) for **hdPS** (what the 200 yes/no code flags are, how they are chosen; treatment-only ranking; random half held out; exposure drugs excluded), **PS-Clinical** (inputs incl. measured values, no LVEF, 5-draw MI), and **PS and matching** (L2 logistic, fixed C = 1, 1:1 nearest neighbour, caliper 0.2 SD of the logit, without replacement, <11 pairs = failed).
4. **The balance results slide:** the user calls this "slide 13" and describes a slide with a love plot, domains and the ladder. In the current deck that matches **"Results 2: primary contrast, ladder, domains"**. Replace its content with **just the updated Figure 2** from Step 1 (full slide, a minimal title, one-line source note). Keep the interactive balance explorer slide unchanged.
   - Record the mapping in the final summary, because on-screen slide 13 may currently be a different slide (e.g. "Agreement by quality"). If on-screen slide 13 is something else, leave it unchanged and say so.
5. **CLMBR-T now appears in the methods slide and Figure 2C.** Keep it out of the take-home claims. Never call it "unstructured".
6. **Rebuild** the deck. Keep every other slide, all appendix links and back-links, and all explorers working.
7. **Update `pipeline.md`'s deviations log** (one line): CLMBR-T is shown again in the PSM-experiments slide and Figure 2C as a comparison arm.

## Step 3: independent verification (separate subagent), then fixes

**Spawn a fresh verifier subagent** (Agent tool) that did not build anything. Give it this file and the checks below. It writes `docs/presentation/VERIFY_LAB_DECK_2026_10_15.md`, with PASS / FAIL per check and BLOCKING / SHOULD-FIX issues.

**Checks:**
1. **Every item in Step 2** is implemented as written, with screenshot evidence. That includes each reveal step on slides 3, 4, 6 and 7, and both popups on slide 6 plus the slide 7 links.
2. **Navigation:** keyboard, links and back-links, hash URLs; popups and Esc; 0 console or page errors. Nothing clipped or overlapping at 1920×1080 and 1366×768: screenshot every slide at both sizes and inspect them.
3. **Numbers:** at least 25 headline numbers recomputed with independent code from the source cells listed in Step 1 (relative reduction = 1 − ratio of across-trial means over items observed in both cells; bootstrap 4,000, seed 20261001; exact one-sided sign-flip; < 11 pairs = failed). Include all Figure 2 panel values.
4. **Leakage:** displayed numbers and explorer defaults use the leakage-corrected masks of `pipeline.md` §6; no PS input is a held-out item for any rung; toggling leakage off changes PS-Clinical as expected.
5. **Consistency:** no slide contradicts another (32 trials, version 1, v19 tiers, LATENT-RCT). TRACE-ECG appears only as a historical note. CLMBR-T is not in the take-home claims and is never called "unstructured". UK Biobank appears only as planned.
6. **Privacy scan** of the HTML and the figure files.

**Then:** fix every BLOCKING issue (and SHOULD-FIX issues where quick), rebuild, and have the verifier re-check the fixed items. Repeat until there are no BLOCKING issues, or until 3 rounds have passed. Log anything left open.

## Step 4: commit and summary

1. **Commit locally:** `scripts/figures/make_figure2_latent.py`, `docs/paper/figures_latent/`, `scripts/build_lab_deck_1015.py`, the deck HTML, `docs/presentation/VERIFY_LAB_DECK_2026_10_15.md` and `pipeline.md`. Don't push.
2. **Write a short summary for the user** at the top of `/mnt/raid0/rbc58/ecg-tte/audits/claude-deckq-20261013/STATUS.md`, and copy it to `docs/queue/QUEUE_2026_10_13_DECK_RESULTS.md` (commit that too). Cover:
   - what changed per slide;
   - the slide-13 mapping;
   - the Figure 2 values;
   - the verification verdict;
   - anything left for the user (e.g. slide 5 is empty for their content).
