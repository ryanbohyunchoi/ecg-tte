# Results: queue 2026-10-14, the 31-trial primary set (s31)

Queue file: `docs/queue/QUEUE_2026_10_14_S31.md`. Steps 1–5 were done by the s31 job (log: `/mnt/raid0/rbc58/ecg-tte/audits/claude-s31-20261014/STATUS.md`). That session was terminated at the 600 s background-wait limit while its verifier was still running, so Steps 6–7 (independent verification, commit, this summary) were finished by the deck2 job (`docs/queue/QUEUE_2026_10_14_DECK2.md`; log `/mnt/raid0/rbc58/ecg-tte/audits/claude-deck2-20261014/STATUS.md`) before it made any deck edits.

## Headline numbers: s31 vs the 32 trials (with PROTECT AF)

Full table: `docs/s31/S31_RESULTS.md`.

| Quantity | s31 (primary) | 32 trials (sensitivity) |
|---|---|---|
| **PS-CVD5 + ECG vs PS-CVD5** (relative reduction in mean \|SMD\|, 54 items) | **8.7% (4.2 to 13.5)**, P < .001, 20/31 lower | 8.8% (4.4 to 13.3), P < .001, 21/32 |
| Items with \|SMD\| < 0.1 | 53.9% → 57.3% (P = .015) | 53.4% → 57.0% (P = .009) |
| Permuted ECG vs PS-CVD5 | 0.4% (−3.5 to 4.3), P = .83 | 1.0% (−2.8 to 4.8), P = .63 |
| ECG vs permuted ECG | 8.3% (4.0 to 12.7) | 8.0% (3.6 to 12.2) |
| Ladder + ECG: PS-Demo / CVD5 / CVD10 / PS-Clinical (no LVEF, MI) / hdPS | 10.6 / 8.7 / 3.8 / 3.3 / 7.1% | 11.3 / 8.8 / 5.0 / 3.2 / 7.6% |
| Six PS methods: CIs excluding 0 | 5 of 6 (gradient-boosted PS −1.5%) | 5 of 6 |
| \|Δ log HR\| PS-CVD5 → + ECG; benchmark-permutation P | 0.232 → 0.198; P = .56 | 0.226 → 0.196; P = .70 |
| PS-CVD10 + ECG benchmark-permutation P (post hoc, exploratory) | < .001 | .003 |
| CV-tuned penalty; index-day ECGs excluded | 5.2% (−1.0 to 11.3); 7.8% (0.7 to 14.6) | 5.7%; 6.9% |
| Spec-v2 fixed cohorts (point estimate) | 8.7% → 7.0% (random removal median 6.7) | 8.8% → 6.6% (6.9) |

Every arm of every ladder level has all 31 trials (no failed cells, including hdPS + CLMBR-T + ECG).

## What changed

- **Trial-set definition** (`scripts/build_balance_explorer.py`): sets `s31` (primary), `f37` (the 37 feasible), `q37:` / `area31:` subsets; PROTECT AF status "excluded at feasibility (smaller arm < 350)". Every validation of the old sets is unchanged.
- **Numbers** (`scripts/s31/`): s31 summaries and `docs/s31/S31_RESULTS.md`; the S32 rows reproduce the committed runs.
- **Figure 2** (`scripts/figures/make_figure2_latent.py` → `docs/paper/figures_latent/`): on the 31; PROTECT AF footnote and dagger removed; all arms have 31 trials.
- **Overview figure** (`scripts/figures/make_study_overview.py`): 37 feasible / 31 analysed; tiers 3 / 11 / 17 / 6; AF 11.
- **Deck** (`scripts/build_lab_deck_1015.py` → `docs/presentation/ecg_tte_lab_2026_10_15.html`): s31 is the default everywhere.
  - Slide 6 flow reads 99 → 37 → 31, and criterion 4 reads "≥ 350 with an ECG in the smaller arm and ≥ 50 events".
  - The size-rule disclosure line is in A1 and the slide 6 popup.
  - A2 and A3 mark PROTECT AF as excluded at feasibility.
  - The results, robustness, agreement-by-quality (default: 37 feasible), take-home and open-decisions slides are all updated.
  - The claims table holds 424 claims, all checked and all matching.

## Verification

`docs/presentation/VERIFY_LAB_DECK_2026_10_15_S31.md`, by a fresh verifier subagent. **Verdict: PASS with minor issues; no BLOCKING issues.**
- 939 values were recomputed with independent code, including all of Figure 2A–D and the primary.
- 0 console or page errors at 1920×1080 and 1366×768.
- Masks follow pipeline.md §6 on the 54-item panel.
- The privacy scan is clean.

## Open items (MINOR, for the user)

1. **Slide 11 benchmark P:** the "+ ECG" P reads 0.54–0.56 depending on how the table is sorted. The in-browser Monte Carlo follows display order; the precise value is 0.549.
2. **Slide 7 popup:** "index day included, 37% of ECGs" is the 32-trial figure and was not recomputed on the 31.
3. **PS-Demo on the 58-item panel:** pipeline.md §6 lists `B_mean` and the prognostic score as masked, but the builder, explorer and slide 8 mask nothing. This predates s31 and affects only the secondary panel.
4. **Limited-tier Pearson r:** the value in `s31_numbers.json` differs from the cells by about 2e-6, which is invisible at 2 decimals.
