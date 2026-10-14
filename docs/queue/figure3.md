# Figure 3: agreement with the RCT results, with the CLMBR-T arms (queued 2026-10-14; runs after the Figure 2D job)

You are running unattended in tmux. Read `CLAUDE.md`, `handoff.md` §1 and `pipeline.md` (2026-10-14 update: the **31-trial primary set**, PROTECT AF excluded at feasibility).

**First:** read the results of the three earlier jobs:
- `docs/queue/QUEUE_2026_10_14_S31_RESULTS.md`
- `docs/queue/QUEUE_2026_10_14_DECK2_RESULTS.md`
- `docs/queue/FIGURE2D_RESULTS.md`

If any of them did not finish cleanly, log it and do only what this change needs.

**Rules:**
- The same rules as `docs/queue/QUEUE_2026_10_14_DECK2.md`.
- Write only under `/mnt/raid0/rbc58` and the repo.
- Aggregates only; no patient counts of 1–10; no n_pairs, retention or ESS.
- No commits of restricted files; no push; no GPU.
- Python: `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`.
- Set the Playwright environment variables inside Python.
- Log to `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig3-20261014/STATUS.md` (`umask 077`).
- Don't edit `paper.md`, `paper2.md`, `table1_picot.md` or any `.docx`.
- CLMBR-T is a comparison arm: never call it "unstructured", and keep it out of the take-home claims.

**Mock-ups to match**, in `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig3-20261014/mockup/`:
- `figure3_mock.png`: panels A and B as wanted. **Ignore its panels C and D.**
- `figure3_C_variants.png`: the wanted panel C is the **left one, "V1"**.
- The scripts `f3_mock.py` and `f3_C_variants.py` compute every value from the cells via `scripts/s31/s31_numbers.load()`. Reuse that code path.

## The figure

1. **Write `scripts/figures/make_figure3_latent.py`.**
   - Use the style of `make_figure2_latent.py`: the same fonts, colours, arm markers (PS alone open navy circle; + ECG red circle; + CLMBR-T open green square; + CLMBR-T + ECG purple diamond) and level order.
   - **Basis:** s31, main configuration (1:1 NN, caliper 0.2), log HRs from the existing cells (no refitting).
   - **Outputs:** `docs/paper/figures_latent/figure3_rct_agreement.{png,pdf}` (300 dpi), plus per-panel PNGs in `docs/paper/figures_latent/panels/`.
   - **Layout:** three panels, A and B on top and C below, or all three in one row if that reads better. **There is no panel D.**
2. **Panel A: emulated vs RCT HR, PS-CVD5 vs PS-CVD5 + ECG.**
   - Log–log axes; the identity line dashed.
   - PS-CVD5 as open navy circles, + ECG as red dots, with a light line joining each trial's two estimates.
   - An inset text: "Mean |Δ log HR|: 0.232 → 0.198 / 20 of 31 trials closer".
3. **Panel B: agreement ladder.**
   - **Plot:** mean |Δ log HR| vs RCT (31 trials) at PS-Demo, PS-CVD5, PS-CVD10, PS-Clinical (no LVEF, MI) and hdPS. Four arms (PS alone, + ECG, + CLMBR-T, + CLMBR-T + ECG), offset within each level and joined by thin lines per arm, as in Figure 2C.
   - **Labels:** title "Agreement ladder (fewer → more covariates)"; y-axis label "Mean |Δ log HR| vs RCT (31 trials)" with "lower = closer to the RCT"; the legend.
   - **Leave out:**
     - any P-value rows or numbers on the panel;
     - the grey "trial-specific / RCT results shuffled" text;
     - the red highlight of PS-CVD5;
     - the permutation bands.
4. **Panel C: agreement by emulation quality (PS-CVD5).**
   - **Bars** of mean |Δ log HR| vs RCT for the four arms (PS alone white with a navy edge; + ECG red; + CLMBR-T green; + CLMBR-T + ECG purple), in two groups: "Excellent + Good (14)" and "Moderate (17)".
   - **Labels:** the value on top of each bar (3 decimals); y-axis "Mean |Δ log HR| vs RCT" with "lower = closer"; the legend below the panel.
   - **Tiers:** v19, from `trials_meta`.
5. **Expected values** (add them as checks; stop and log if any differ by more than 0.001):
   - **A:** 0.232 → 0.198; 20 of 31 closer.
   - **B** (PS alone / + ECG / + CLMBR-T / + both):
     - PS-Demo 0.255 / 0.207 / 0.174 / 0.164;
     - PS-CVD5 0.232 / 0.198 / 0.169 / 0.161;
     - PS-CVD10 0.213 / 0.173 / 0.181 / 0.157;
     - PS-Clinical 0.171 / 0.151 / 0.151 / 0.152;
     - hdPS 0.182 / 0.172 / 0.184 / 0.169.
   - **C:**
     - Excellent + Good 0.230 / 0.176 / 0.149 / 0.152;
     - Moderate 0.235 / 0.217 / 0.185 / 0.168.
   - The ECG values must also equal `docs/s31/S31_RESULTS.md` (§2 ladder and §4 tiers).
6. **Write the values** to `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig3-20261014/figure3_values.json` (aggregates).
7. **View the PNGs** (Read tool) and fix any overlap or clipping.
8. **Caption**, for the summary and the deck speaker notes:
   > Figure 3. Agreement of emulated and RCT results (31 trials). A, Emulated vs RCT hazard ratios with PS-CVD5 and PS-CVD5 + ECG. B, Mean absolute difference from RCT log HRs across the PS ladder with the ECG, CLMBR-T or both added. C, Mean absolute difference by emulation quality (PS-CVD5). Lower is closer to the RCT.

## The deck

1. **Add a slide "Results: agreement with the RCTs (Figure 3)"** to `scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`. It goes **directly after the balance explorer slide**, i.e. after Figure 2 → balance explorer, and before the emulation explorer.
2. **Build it like the Figure 2 slide:**
   - built from the per-panel PNGs, laid out like the full figure;
   - a minimal title, no subtitle or source line;
   - **panels revealed one per click: A → B → C.**
3. **Keep every other slide, popup, explorer and link unchanged**, including the existing "agreement by quality" slide and the take-home slide's wording.
   - Renumber the slide numbers, and every "Back to slide N" link, that shift by one.
   - In the summary, note that panel C overlaps the existing "agreement by quality" slide, for the user to decide whether to keep both.
4. **Register the static numbers** shown on the new slide (panel A's text) in the builder's claims table, with checks against `figure3_values.json` / `S31_RESULTS.md`.
5. **Add one line to `pipeline.md`'s deviations log:** "Figure 3 (agreement): A scatter, B agreement ladder with CLMBR-T arms, C by emulation quality; CLMBR-T shown as a comparison arm, not in take-home claims."

## Verification (a fresh subagent that built nothing)

The verifier checks:
- **All values,** recomputed independently from the cells: every B and C value, plus panel A.
- **Panel B** has no P values, grey text, highlight or bands; **there is no panel D**.
- **Screenshots** of the new slide at each reveal step, at 1920×1080 and 1366×768.
- **Navigation:** keyboard, links and back-links after the renumbering; 0 console or page errors.
- **The other slides' numbers** are unchanged from the Figure 2D build.
- **A privacy scan.**

Run the verifier subagent in the **foreground** (Agent tool with `run_in_background: false`), and wait for it: the headless session ends if background tasks run longer than 600 s, which is what stopped the s31 job. Fix BLOCKING issues and re-verify, up to 3 rounds. Report: `docs/presentation/VERIFY_FIGURE3.md`.

## Commit and summary

1. **Commit locally:** `make_figure3_latent.py`, `docs/paper/figures_latent/` (Figure 3 files), the deck builder, the deck, `pipeline.md` and the verify report. Don't push.
2. **Write the summary** at the top of the status log and copy it to `docs/queue/FIGURE3_RESULTS.md` (commit). Cover:
   - the Figure 3 values;
   - the new slide's position and the renumbering;
   - the verification verdict;
   - the overlap with the "agreement by quality" slide.
