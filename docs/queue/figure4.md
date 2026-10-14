# Figure 4: AI representations alone vs conventional PS matching (2026-10-14)

**Status:** the draft and its numbers are **audited** (independent recomputation, exact). The figure is **not yet in the repo, deck or paper.** Two user decisions are pending (end of file). Once they are made, this file doubles as the queue instructions for an unattended job.

**Files** (all under `/mnt/raid0/rbc58/ecg-tte/audits/claude-fig4-standalone-20261014/`, restricted):
- draft figure: `figure4_draft_v4.png`;
- draft scripts: `f4_numbers.py`, `f4_draw_v4.py`;
- numbers: `f4_numbers.json`, `f4_hdps.json`;
- audit: `AUDIT_STANDALONE.md`, `recompute_f4.py`, `recomputed_f4.json`, `robust_tables.md`.

## The question

Can a PS built from **AI representations alone** stand in for conventional, investigator-chosen PS covariates? "Alone" means the representations plus age, sex and index year ("Demo"), with no hand-picked diagnoses, labs or code flags.

**This is different from Figure 2.** Figure 2 asks whether *adding* the ECG to a conventional PS helps. Figure 4 compares the representations *instead of* the conventional covariates.

**Arms:**
| Group | Arm | Grid cell | Inputs |
|---|---|---|---|
| Representation | Demo + ECG | rung P1, arm `ECG` | 3 + 32 ECG PCs |
| Representation | Demo + ECG + CLMBR-T | rung P1, arm `ECG+CLMBR` | 3 + 32 ECG PCs + 64 CLMBR-T PCs |
| Representation, shown in robustness only | Demo + CLMBR-T | rung P1, arm `CLMBR` | 3 + 64 CLMBR-T PCs |
| Conventional comparator | PS-CVD5 | `base` | |
| Conventional comparator | hdPS | `base` | |
| Conventional comparator | PS-Clinical (no LVEF, 5-draw MI) | `base` | |
| Reference | Unmatched | | |

**Basis:** s31 (31 trials); main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1); 54 held-out items with the `pipeline.md` §6 leakage masks. Cross-rung contrasts use only items observed in both arms (the union of both masks).

**Cell sources:**
- `claude-v21-paper2/core/restricted_cells.parquet` (P1, P5, hdPS200);
- `claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet` (PS-Clinical);
- `claude-v18-embed-compare/results.csv`, rung `none` (unmatched HR);
- unmatched |SMD| as `build_balance_explorer.py` derives it.

## Audited results (31 trials, main)

**Balance:** mean |SMD| over the 54 items (each arm's own masks):
| | Unmatched | PS-CVD5 | hdPS | PS-Clinical† | Demo + ECG | Demo + CLMBR-T | Demo + ECG + CLMBR-T |
|---|---|---|---|---|---|---|---|
| Mean |SMD| | 0.143 | 0.129 | 0.114 | 0.118 | 0.126 | 0.112 | **0.106** |

† PS-Clinical's mean uses the ~45 items that are not its own inputs.

**Paired contrasts:** relative reduction in mean |SMD|, bootstrap 95% CI, two-sided sign-flip P:
| Contrast | Balance | Mean |Δ log HR| (a vs b), P |
|---|---|---|
| Demo + ECG vs PS-CVD5 | 1.5% (−4.0 to 7.4), 15/31, P = .61 | 0.207 vs 0.232, P = .20 |
| Demo + ECG vs hdPS | **−10.2%** (−19.7 to −1.5), P = .03 | 0.207 vs 0.182, P = .56 |
| Demo + CLMBR-T vs PS-CVD5 | 12.5% (6.3 to 18.4), P = .001 | 0.174 vs 0.232, P = .055 |
| Demo + CLMBR-T vs hdPS | 2.0% (−4.4 to 8.0), P = .53 | 0.174 vs 0.182, P = .71 |
| **Demo + ECG + CLMBR-T vs PS-CVD5** | **17.8% (11.8 to 23.6), 27/31, P < .001** | **0.164 vs 0.232, P = .037** |
| Demo + ECG + CLMBR-T vs hdPS | 8.0% (1.9 to 13.6), 25/31, P = .012 | 0.164 vs 0.182, P = .21 |
| Demo + ECG + CLMBR-T vs PS-Clinical | 7.0% (1.1 to 12.7), P = .033 | 0.164 vs 0.171, P = .67 |

**Statistical agreement** (|z| < 1.96, emulated vs RCT log HR): Unmatched 68%; PS-CVD5 74%; hdPS 74%; PS-Clinical 87%; Demo + ECG 84%; Demo + ECG + CLMBR-T 84%.

## What the audit found

1. **The numbers reproduce exactly** (max deviation 7e-15). The leakage checks pass:
   - Demo is exactly age, sex and index year in 38/38 trials.
   - No PS input is a held-out item.
   - Masking eGFR or heart rate as a sensitivity changes nothing.
2. **Demo + ECG ≈ PS-CVD5** in every configuration and trial set (−3.1% to +2.9%). It is **worse than hdPS**.
3. **Demo + ECG + CLMBR-T beats PS-CVD5 robustly** under matching:
   - caliper 0.1: 15.5%; 1:3 matching: 17.3%; overlap weights: 16.4%; 32 or 38 trials: about 17.7%;
   - gradient-boosted PS: weaker, 9.0%;
   - **IPTW: not significant**, 5.8% (P = .086) on 31 trials and about 0 on 32 or 38.
4. **Input count doesn't explain it.** Demo + permuted CLMBR-T has the same number of inputs and is 11.8% *worse* than PS-CVD5.
5. **Retention:** the CLMBR-T arms keep 0.79–0.81 of the smaller arm, vs 0.88 for PS-CVD5. In the 12 trials with ≤ 5 points of retention loss, the gain still holds: 13.8% (5.5 to 22.9), P = .006.
6. **Beating hdPS and PS-Clinical is fragile:**
   - **vs hdPS:** P = .067 with caliper 0.1, .097 with overlap weights, .28 with a gradient-boosted PS;
   - **vs PS-Clinical:** P = .065 in the worst drop-one-trial case and .063 by comparator cluster;
   - no FDR adjustment applied.
   - **Wording:** "comparable to or modestly better than hdPS and PS-Clinical".
7. **The agreement gain vs PS-CVD5 is weak and generic:**
   - P = .074 without CABANA and .088 on 32 trials; not significant with IPTW or overlap weights;
   - benchmark-permutation P = .26 (two-sided);
   - Demo + ECG + CLMBR-T estimates are less dispersed (SD 0.22 vs 0.37) and less biased toward benefit (mean bias −0.01 vs −0.07), but **not more correlated** with the RCT results (r 0.49 vs 0.55);
   - **wording:** "closer on average, about as close as PS-Clinical", **not** "better replicates each trial".
8. **The permutation test is coded correctly.** For head-to-head contrasts, report its **two-sided** version, and don't use it as an agreement P.
   - Demo + ECG vs hdPS gives one-sided P = .001 only because Demo + ECG tracks individual trials better (r .59 vs .34), although hdPS is closer on average.
9. **Not run:** a data-driven check of whether the ECG PCs correlate with held-out items (an optional leakage sensitivity).

## Figure specification (match `figure4_draft_v4.png`)

New script `scripts/figures/make_figure4_standalone.py`, in the style of `make_figure2_latent.py`. Reuse `load()`, `love()` and `per_trial_mean()`; don't modify that file. Output to `docs/paper/figures_latent/figure4_standalone.{png,pdf}` (300 dpi), with per-panel PNGs in `docs/paper/figures_latent/panels/figure4/`.

- **Legend (top):** Unmatched (grey hollow circle), PS-CVD5 (navy), Demo + ECG (red), Demo + ECG + CLMBR-T (purple diamond).
- **A. Balance on each of 54 held-out items:** a love plot as in Figure 2A; median |SMD| across 31 trials; grouped by domain; 0.1 reference line.
- **B. Overall balance:** horizontal bars of mean |SMD|.
  - Rows: Unmatched, PS-CVD5, hdPS, PS-Clinical†, then a dotted divider, then Demo + ECG and Demo + ECG + CLMBR-T.
  - Right-aligned labels on the two representation rows: "vs PS-CVD5: *x*% lower/higher (P = …)" and "vs hdPS: …" (paired contrasts).
  - The label code must print "lower" or "higher" from the sign. No asterisks.
- **C. Agreement with the RCT:** horizontal bars of mean |Δ log HR|, same rows, labels with the paired difference and two-sided P vs PS-CVD5 and vs hdPS.
- **D. Statistical agreement:** % of trials with |z| < 1.96, same rows, no labels.
- **Colours:** grey `#7a7c8c`, navy `#0d1040`, hdPS `#3a8fb7`, PS-Clinical gold `#c9a227`, ECG red `#d9534f`, ECG + CLMBR-T purple `#7b4fa0`.
- **Footnote** (full width, 4 lines):
  - Demo = age, sex, index year. ECG = 32 PCs of the pre-index ECG embedding. CLMBR-T = 64 PCs of a foundation-model embedding of the **coded pre-index EHR**.
  - Labels are paired differences on items observed in both arms; two-sided sign-flip P across 31 trials, unadjusted.
  - † PS-Clinical uses ~45 items.
  - The agreement gain is not trial-specific (benchmark-permutation P = .26, two-sided): less dispersed and less biased estimates, not more correlated with the RCT results (r 0.49 vs 0.55).
- **Wording rules:**
  - Call the group "Demographics + AI representations", never "representation-based PS alone" without the demographics.
  - Never call CLMBR-T "unstructured".
  - No claim that the representations "replicate" trials better.
- **Expected values (checks):** all numbers in the two tables above, within display precision. Stop and log any mismatch.

## Deck (proposed, pending decision 2)

- **One new slide right after the balance explorer** (which follows the Figure 2 slide), titled "AI representations instead of hand-picked covariates".
- **Click reveal:** A + B → C → D. Use per-panel PNGs as in the Figure 2 slide, and add the footnote under D.
- **Robustness popup** on click (the `popup()` mechanism): the robustness table from `robust_tables.md` for the three key contrasts (config × 31 trials), with the IPTW row highlighted.
- **One take-home line on the slide:** "Without hand-picked covariates, demographics + ECG + CLMBR-T balanced held-out vitals, labs and echo 18% better than PS-CVD5 and comparably to hdPS; ECG alone matched PS-CVD5; agreement with RCTs improved only on average."
- **Update** the claims table and expected values in `build_lab_deck_1015.py`. Renumber the slides and appendix links, and keep everything else unchanged.

## Verification and commit (when queued)

1. **Fresh verifier subagent:**
   - recompute every plotted value independently, or check it against `recomputed_f4.json`;
   - check the wording rules;
   - screenshots of each reveal step and the popup at 1920×1080 and 1366×768;
   - 0 console errors; a privacy scan (no n_pairs, retention per trial or counts of 1–10).
2. **Commit locally:** the script, the figure, the deck builder, the deck and the verify report. Don't push. Restricted files stay in the audit directory.
3. **Add a deviations-log line to `pipeline.md`** (if decision 1 = yes): "Figure 4: demographics + AI representations (ECG, CLMBR-T) vs conventional PS (PS-CVD5, hdPS, PS-Clinical); CLMBR-T now appears in a take-home claim; IPTW and agreement caveats disclosed."

## Decisions pending (user)

1. **CLMBR-T in the headline.** `pipeline.md` currently keeps CLMBR-T out of the take-home claims. This figure's main result depends on CLMBR-T: Demo + CLMBR-T alone is 12.5% better than PS-CVD5. Change the lock?
2. **Where it goes:** the deck (Thursday), the paper, or both. This also decides the slide placement above.
3. **Optional:**
   - add Demo + CLMBR-T as its own bar, to show how much of the gain is CLMBR-T vs ECG;
   - drop panel D;
   - run the ECG-PC vs held-out-item correlation sensitivity.
