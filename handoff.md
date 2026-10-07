# Handoff: TRACE-ECG paper2 run (2026-10-07, overnight)

Written **2026-10-07 at about 19:30** by the coordinator session at the end of an unattended run of [HANDOFF_PAPER2.md](HANDOFF_PAPER2.md). The previous brief is moved verbatim to [docs/HANDOFF_HISTORY.md](docs/HANDOFF_HISTORY.md), under "Brief superseded on 2026-10-08". Read that brief for the paper1 state (paper.md, supplement, figures and build commands), which is unchanged.

**Steps A–H of the paper2 workplan are all done.** Every gate passed. Everything is committed locally to `main`, and **nothing has been pushed**; there are 10 commits ahead of `origin/main`, including the plan commit 14dbfff and this handoff. `paper.md`, `table1_picot.md` (your uncommitted edits) and the `.docx` were not touched.

## 1. Rules that apply to every agent (unchanged)

- **Writing:** write only under `/mnt/raid0/rbc58`, plus code and docs in this repository, committed to `main`. Everything else is read-only (`/mnt/nfs_*`, other users' raid0 folders, S3). See `CLAUDE.md`.
- **Outputs:** put them in `/mnt/raid0/rbc58/ecg-tte/audits/<name>` with umask 077.
- **Patient data:** aggregates only. Suppress counts of 1–10, never print patient rows or identifiers, and never commit CSV or parquet files.
- **Pushes:** commit locally; the user pushes.
- **Licensed data:** MIMIC-IV and UKB may be read and checked by agents, aggregates only (2026-09-30).
- **Scope:**
  - no PGS or genetics and no UKB in any manuscript;
  - **CLMBR-T is back for paper2 only** (PI, 2026-10-07); `paper.md` stays without it;
  - never call CLMBR-T "unstructured" (it embeds the coded EHR).
- **How the PI works:** the PI edits in Word and pastes the text back; the pasted text is authoritative.

## 2. Where to look first

| What | Path |
|---|---|
| **Draft manuscript** | `docs/paper/paper2.md` (5 `[CHECK]` and 7 `[USER: confirm]` markers) |
| **Figure gallery** (self-contained HTML) | `docs/paper/figures_paper2/index.html`; copy at `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/figures_paper2.html` |
| Figures (PNG 300 dpi + PDF, panels) | `docs/paper/figures_paper2/{main,supplementary}/`; built by `scripts/v21/make_paper2_figures.py` |
| Core results (verdict first; §9 responds to the audit) | `docs/v21/PAPER2_RESULTS.md` |
| Trial labels (blind, adjudicated before analysis) | `docs/v21/TRIAL_LABELS.{md,json}` |
| PS-Flags construction and window check | `docs/v21/PS_FLAGS.md` |
| Plasmode | `docs/v21/PLASMODE_PAPER2.md` |
| MIMIC-IV PS-CVD5, plus the v20 window fix | `docs/v21/MIMIC_PAPER2.md` (window fix in §6) |
| Analysis audit (reviewer) | `docs/v21/AUDIT_PAPER2_ANALYSES.md` |
| Manuscript audit (claim by claim) | `docs/v21/AUDIT_PAPER2_MANUSCRIPT.md` |
| Run log | `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/STATUS.md` (summary at the top) |
| Code | `scripts/v21/` (`adjudicate_labels.py`, `ps_flags.py`, `paper2_grid.py`, `paper2_plasmode.py`, `mimic_cvd5.py`, `mimic_window_fix.py`, `make_paper2_figures.py`) |
| Aggregate outputs | `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/{core,plasmode,mimic}/` |

**Re-run:** `paper2_grid.py run | gate | summarize | labels | headline | flagscv | retsens | privacy`. Each step-B subcommand after `run` works on its own.

## 3. What was done

| Step | Result |
|---|---|
| **A. Labels** | Two blind labellers (two runs of the same LLM, seeing only a results-free PICOT table) agreed on `physiologic` for 38/38 trials: 11 yes. Domains are the intersection of the two labellings, with the union as a sensitivity. Committed before any stratified result. κ = 1.0 is **not** evidence of human inter-rater reliability. |
| **B. Core grid** | 5 rungs (PS-Demo, PS-CVD5, PS-Flags, hdPS200, PS-Clinical) × 7 arms × 6 configurations × 38 trials. **Gate exact:** 2,736 cells vs v20 sens-primary32 and 912 CLMBR-T cells vs v1.8 (max deviation 0). BH-FDR across the whole sweep. |
| **C. Plasmode** | PS-CVD5 arms on the trtC clinically oriented design. Gate exact vs v20 g2-ext. |
| **D. MIMIC** | PS-CVD5 analog (the v20 `sparse` base is not CVD5). Gate exact vs v20. |
| **E. Reviewer** | 1 blocking issue: a PROTECT AF small count could be recovered from ESS and retention columns. Fixed, and the step-B commit was amended so the exact value never entered git history. All 7 should-fix items were addressed (PAPER2_RESULTS §9). The reviewer independently recomputed the headline numbers, and they matched. |
| **F. Figures** | Figures 1–5 and eFigures 1–5, plus the HTML gallery, built from aggregate files only. |
| **G. Draft** | `paper2.md`: about 6,600 words of main text, which is long and must be cut once a journal is chosen. |
| **H. Manuscript audit** | 155 checks: 141 match; 8 mismatches fixed (including a Figure 1 flag-count bug); 5 unsupported claims softened. 10 `[CHECK]` markers resolved. |

## 4. Key results (32 trials, main configuration, 54 non-coded held-out items)

- **Balance with PS-CVD5:** relative reduction in mean |SMD|:

  | Added to PS-CVD5 | Reduction (95% CI) | q |
  |---|---|---|
  | ECG | 8.8% (4.4–13.3) | .002 |
  | CLMBR-T | 12.4% (7.1–17.7) | < .001 |
  | Both | 13.5% (6.6–20.4) | .003 |

  - Both placebos give about 0.
  - The ECG's gains lean toward the echo domains and CLMBR-T's toward labs and vitals, but the echo-domain differences are **nominal** and don't replicate across configurations.
  - CLMBR-T beats the ECG overall in 3 of 6 configurations (q < .05), but not in the main one.
- **Agreement with the RCTs:**
  - |Δ log HR| shrinks with every arm (ECG 0.226 → 0.196; CLMBR-T → 0.166; both → 0.158), but benchmark-permutation P is .70–.94;
  - **no agreement row reaches q < .05 in the 32-trial set, in any configuration;**
  - this is attenuation toward HR = 1, not trial-specific agreement.
- **PI head-to-head, PS-Demo + CLMBR-T vs PS-Flags: no detectable difference.**
  - Balance +0.7% (−5.5 to 6.8), P = .81.
  - The paired |Δ| is 0.186 → 0.174.
  - The as-specified PS-Flags (L2 penalty, C = 1, 426–622 flags) overfits small trials: median retention 0.72 vs 0.99 for PS-CVD5, and PROTECT AF keeps fewer than 11 pairs.
  - With PS-Flags tuned by cross-validation, the difference is −1.5% (P = .63); restricting to trials where Flags retains well gives −2.6%.
  - It depends on the penalty: C = 0.1 gives +7.7% (P = .085).
  - The PI's timing hypothesis is not tested directly.
- **CLMBR-T vs hdPS200 and PS-Clinical:**
  - CLMBR-T adds nothing on top of hdPS200 (−3.5%) or PS-Clinical (+0.8%).
  - The ECG adds +7.6% on top of hdPS200 (q = .033), but that is not distinguishable from the permuted ECG in the main configuration.
  - P5 + CLMBR-T is nominally worse than PS-Clinical.
- **Labels:**
  - Gains are larger in the 10 physiologic trials, for CLMBR-T as much as for the ECG. No physiologic-vs-other contrast survives BH; the ECG's P = .048 has q = .16.
  - LV-systolic-function trials show larger LV-function gains (q = .021), shared by both representations.
  - Read this as more confounding in those trials, not ECG-specific content.
- **Plasmode (null-corrected % of bias removed):**

  | Arm | % of bias removed |
  |---|---|
  | PS-CVD5 | 18.6 |
  | + ECG | 27.8 |
  | + CLMBR-T | 37.0 |
  | + both | 42.6 |
  | Oracle | 93.7 |

  - The ECG adds more than CLMBR-T for LVEF; CLMBR-T adds far more for eGFR and NT-proBNP.
- **MIMIC-IV:** PS-CVD5 + ECG reduces mean |SMD| by 6.6% (2.3–12.8), better in 6/7 trials; agreement is not ECG-specific.

## 5. Decisions for the user (in rough priority order)

1. **Confirm the proposed defaults** (marked `[USER: confirm]` in paper2.md): the 54-item primary balance endpoint, 64 CLMBR-T PCs as primary (32 as sensitivity), and S32 as the primary set.
2. **Paper1 MIMIC correction.** In v20, `mimic_build_new.py` used diagnosis codes from the index admission (recorded after time zero) for SOAP II, ELITE II and PEPTIC.
   - With the window fixed (`docs/v21/MIMIC_PAPER2.md` §6), the numbers on paper.md line 91 change: hdPS + ECG 7.5% → **8.1% (−0.1 to 17.3)**; PS-Clinical-lite + ECG 1.2% → **3.0% (−8.6 to 15.2)**.
   - eTable 6B PS-Sparse goes 10.2 → 10.9.
   - All PS-Demo numbers are unchanged.
   - The PEPTIC v20 sparse result (HR 1.16) partly depended on the leak; with the fix it is 1.51.
   - **paper.md was not edited**; decide whether to update it.
3. **How to present PS-Flags.** Should the C = 1 version stay primary, as specified, or should the CV-tuned version become primary? The text currently keeps C = 1 primary and presents CV-tuned as a sensitivity.
4. **Clinician check of labels.** Optionally, have a clinician review the 11 physiologic labels. They currently come from LLM labellers only.
5. **Main-text emphasis.** Whether to put the placebo-controlled hdPS + ECG result in the main text: it is significant against the permuted ECG under 1:3 matching and overlap, but not in the main configuration.
6. **Length.** The main text is about 6,600 words and needs a target journal and cuts. The paper2 supplement (eTables) is not built yet; paper2.md lists the eTables' sources.
7. **Small items:**
   - the remaining `[CHECK]` markers: eFigure numbering, the supplement note, and the Benjamini–Hochberg and Li 2018 references;
   - Figure 1 says "6 arms" where there are 7 (the CLMBR32 arm is main configuration only); cosmetic.
   - New references 22–25 need renumbering by first citation.

## 6. Housekeeping

- **tmux:** session `paper2` is still open, with finished windows kept (`remain-on-exit`). Close it with `tmux kill-session -t paper2`.
- **Reviewer scratch files:** `audits/claude-v21-paper2/review/` contains files renamed `restricted_*`, because they could be differenced to recover a PROTECT AF count of 1–10. Use the `core/` outputs instead; `core/flagscv.csv` reproduces them exactly.
- **Blind PICOT table:** `labels/picot_blind.md` was trimmed at kickoff to remove footnotes that mentioned a published HR. The original is kept as `picot_blind_orig.md`.
- **Still untracked:** `docs/paper/trial_emulate_manuscript_v2_RC.docx` and the `docs/v13`/`v14` `*.err` logs, as before.
