# Handoff: TRACE-ECG after the revert to version 1 and the version 1 audit (2026-10-08)

Written **2026-10-08 at about 11:00 EDT**. It covers 2026-10-07 to 2026-10-08:
- the paper2 overnight run;
- the R2 restart;
- the LEGEND-style analysis;
- the user's decision to **revert to version 1**;
- an independent audit of version 1.

The previous brief (the paper2 run) is moved verbatim to [docs/HANDOFF_HISTORY.md](docs/HANDOFF_HISTORY.md), under "Brief superseded on 2026-10-08, later". Read it for paper2 design details, re-run commands and the paper1 state.

**Repository state.**
- `main` = tag `trace-v1` (5c98301, version 1) plus the version 1 audit commit, all local. **Nothing pushed.** `main` is ahead of `origin/main` by the paper2 run, the plan commits, the audit and this handoff. `origin/main` has none of the R2 commits.
- **R2 and the LEGEND-style work are on the local branch `r2`** (tip 964e3c7), not pushed. Read them with `git show r2:<path>`. Its handoff (`git show r2:handoff.md`) has the full R2 record.
- `paper.md`, `paper2.md`, `table1_picot.md` (the user's uncommitted edits) and the `.docx` have not been touched since the paper2 run.
- **Nothing is running** (checked 10:43). GPUs 3–5 and 7 are idle.

## 1. Rules for every agent

- **Writing:** only under `/mnt/raid0/rbc58` and in this repo; everything else is read-only (`CLAUDE.md`). Outputs go to `/mnt/raid0/rbc58/ecg-tte/audits/<name>`, umask 077.
- **Data:** aggregates only.
  - Suppress counts of 1–10, **including counts derivable by differencing other published numbers**.
  - Never commit CSV, parquet, embeddings or note text.
  - Never read clinical note text or free-text echo columns.
- **GPUs:** **never use GPU 7** (user, 2026-10-07). Check `nvidia-smi` before any launch.
- **Clinical notes:** use is covered by the IRB (user, 2026-10-07; PI confirmation still open). Process locally and offline only. Notes exist only on `r2`.
- **Pushes:** commit locally; the user pushes.
- **Scope:** no PGS or genetics and no UKB in any manuscript. CLMBR-T only in paper2. Never call CLMBR-T "unstructured".
- **How the PI works:** the PI edits in Word; pasted text is authoritative.
- **Agent orchestration lesson:** in-process subagents die when their coordinator is stopped, but tmux jobs survive. Verify any "still running" claim with `ps` and output files.

## 2. What happened (chronological)

| When (EDT) | What | Outcome |
|---|---|---|
| 10-07 day | **paper2 run** (HANDOFF_PAPER2.md steps A–H) | Draft `docs/paper/paper2.md`, figures, results, audits. All gates exact. Details in the history brief. |
| 10-07 22:21 – 10-08 01:20 | **R2 overnight restart** (`plan.md`; branch `r2`) | Blind quality re-audit (35-trial primary set), leakage-map gate, CV-tuned PS, data-availability scenarios S0–S3, clinical-note embeddings (Qwen3-Embedding-8B, GPUs 3–5), H1–H6, user's X1 experiment, explorer, run record |
| 10-08 ~01:40 – 09:30 | **Follow-ups on `r2`** | ECG decomposition (why H1 fell); LEGEND-style large-scale PS analysis |
| 10-08 ~10:00 | **Revert to version 1** (user) | `r2` branch created at 964e3c7; `main` reset to `trace-v1` with `git reset --keep` (local edits kept) |
| 10-08 10:00–10:40 | **Version 1 audit** (three independent agents) | `docs/v1_audit/`, commit 589771e |

### R2 and LEGEND results (on `r2`, for reference only)

- **R2 balance** (35 trials, CV-tuned L2 PS, leakage-clean items, Holm):
  - S1 (claims-minimal = PS-CVD5) + CLMBR-T: 15.8%; supported.
  - S1 + notes: 14.4%; supported, but notes may contain the measured value.
  - S1 + ECG: 4.7% (−0.4 to 9.9), Holm P .165; **not supported**.
  - Nothing adds beyond hdPS.
  - No trial-specific RCT agreement (permutation P .72).
- **Why the ECG fell from 8.8% to 4.7%:** almost entirely R2's CV log-loss penalty, which shrinks the ECG arm (median C 0.010 vs 0.032). Trial set and leakage-clean items barely matter: 8.6% at C = 1. Against its shuffled placebo, the ECG still gives 7.9% (3.1–12.5). Source: `audits/claude-r2/followup/h1_ecg_decomposition.csv`.
- **X1** (each representation alone): CLMBR-T PS 21.8%, notes 19.3%, ECG 11.6%, vs 12.8% for S1 alone. Cosine matching was weaker.
- **LEGEND-style** (L1 PS on ~1,200 features, 10-fold CV, LEGEND diagnostics, 37 negative controls):
  - adding the ECG or CLMBR-T changes nothing;
  - 17% of trials pass all LEGEND diagnostics, whatever the arm;
  - ECG vs shuffled ECG: 5.2%, q .29.
- **Reading:** the ECG's value appears when the PS is thin and lightly penalised, not on top of a large-scale or strongly penalised PS.

## 3. Version 1 audit (start with `docs/v1_audit/README.md`)

| Report | What it did |
|---|---|
| `docs/v1_audit/DEFECT_IMPACT.md` | Re-ran each paper2 headline claim with each of the 9 known version 1 defects corrected. Gate: 4 cells refit from scratch, max deviation 0. |
| `docs/v1_audit/CLAIMS_RECHECK.md` | 160 claims in paper2.md and the figure legends, recomputed from cells with independent code. Compared with the earlier step-H audit. |
| `docs/v1_audit/CODE_PRIVACY_REVIEW.md` | Correctness review of the paper2 pipeline, verified on real data; privacy scan of tracked files |

Code: `scripts/v1_audit/`. Outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/{defects,claims,code}/`.

**Holds:**
- PS-CVD5 + ECG 8.8% (4.4–13.3), + CLMBR-T 12.4%, + both 13.5%.
  - Exact from cells; unchanged by leakage masking; survive Benjamini–Yekutieli.
  - Results-blind 35-trial set: 8.6 / 12.0 / 12.8%.
- PS-Demo + CLMBR-T vs PS-Flags: no difference, also with the CV-tuned PS-Flags.
- The agreement wording (attenuation, not agreement).
- The MIMIC window-fix numbers.
- All numbers in paper2.md are correct.
- No blocking code bug: matching, SMD, PS fit, embeddings, placebos, bootstrap, FDR and Cox all check out. No post-index data in the inputs, except index-day ECGs (below).

**ECG caveats:**
- Excluding index-day ECGs (37% of ECGs are on the index day) gives 6.9% (0.4–13.4).
- A CV-tuned penalty gives 5.7% (−0.5 to 11.4).

**Changes a conclusion:**
1. **CLMBR-T vs PS-Clinical.** Echo EF, LV systolic grade and eGFR leak into the held-out set. Masking them moves −4.9% to −2.6% (−8.4 to 3.2); the GBM result moves from −11.9% (q .007) to −8.5% (q .058).
2. **The CLMBR-T loss under IPTW is weight instability.** Trials with ESS ≥ 0.5 give 7.9%.
3. **Agreement by quality tier** reverses under the blind tiers.
4. **Code should-fix (F1).** PROTECT AF hdPS200 cells with 1–10 pairs still enter the balance contrasts (`scripts/v21/paper2_grid.py` `load_F`). Treating them as failed moves hdPS200 + both from −1.4% to +8.5% (q .032), and the q < .05 count from 98 to 104. Figure 2B and eFigure 3 are affected. Two-line diff in the report.

**Text: 23 of 160 claims need fixes**, with suggested wording in CLAIMS_RECHECK.md. Key ones:
- l.35: "study-drug codes ≤5.9%" holds only for new-user designs.
- l.111 and the Figure 5 legend: "reproduced paper 1's agreement pattern" is unsupported.
- Label results hold only in the main configuration.
- The 1:3 PS-Flags head-to-head is omitted (5.1%, q .093).
- Index dates run 2011–2025.
- MIMIC CIs: 4,000 resamples, not 2,000.
- PS-Clinical does not contain the hdPS features.
- Figure 1: "6 arms" should be 7; there is a draft "(PI hypothesis)" label.
- The plasmode null-correction is undisclosed.

**Privacy:**
- paper2, its figures and the gallery are clean. No patient-level or restricted file is tracked anywhere in `main`'s history.
- **Counts of 1–10 in older tracked docs that are already on `origin`:** `docs/COMET_OUTCOMES_HANDOFF.md`, `docs/COMET_OUTCOME_PROPOSAL_V1.json`, `docs/DECISIONS.md`, `docs/HANDOFF_HISTORY.md`, `tasks/todo.md`, `docs/REVIEW_COMET_REPRESENTATION_BALANCE.md`, plus derivable counts in several v15–v19 docs. File:line references are in CODE_PRIVACY_REVIEW.md.
- `.gitignore` lacks `*.docx`, `audits/`, `*.err` and others.

## 4. Not yet checked

1. **Must-fix cohort issues from R2's blind re-audit, still in version 1:**
   - COMET: the metoprolol arm includes the succinate brand; no LVEF restriction.
   - EMPEROR-Preserved: the DPP-4i comparator includes saxagliptin/alogliptin.
   - Also listed on `r2`: GLP-1RA/SGLT2i washout (LEADER, SUSTAIN-6, REWIND, DECLARE, CANVAS); revascularisation missing from outcomes (LODESTAR, PROVE IT); LIFE ECG-LVH; TRANSFORM-HF time zero.
   - Impact unmeasured. Rebuilds need new ECG and CLMBR-T encodes. List: `git show r2:docs/r2/QUALITY_R2.json`.
2. **paper.md** was not rechecked claim by claim this round; its last audit was 2026-10-01. Only the line 91 MIMIC correction is confirmed.
3. **Plasmode** was not re-run with defects corrected.
4. **Privacy scan** did not cover `paper.md`, the `.docx` files, the PDFs or the `r2` branch.
5. **Upstream pipeline:** ECG/BCL and CLMBR-T embedding extraction and the outcome definitions were not reviewed. One outcome mismatch was found in passing: the CABANA footnote.
6. **The no-index-day-ECG sensitivity** ran in the main configuration only, not the full grid.
7. **No clinician review** of the physiologic labels or quality tiers. The labels are LLM-only; the R2 auditors agreed with κ 0.335.

## 5. Decisions for the user (rough priority)

1. **Apply the audit fixes?**
   - the F1 code fix and re-summarise;
   - paper2.md text fixes, or in the PI's Word file;
   - add the no-index-day-ECG sensitivity.
2. **Privacy on GitHub.** Are the small counts already on `origin` acceptable (is the repo private)? Removing them needs a history rewrite and a force-push. Also add `*.docx` and `audits/` to `.gitignore`.
3. **Cohort rebuilds** for COMET and EMPEROR-Preserved (and the rest of the list): scope, or defer.
4. **Push `main`?** A normal push works, since `origin` has no R2 commits.
5. **Keep or drop the `r2` branch.** Should any R2 element (leakage-clean masking, blind 35-trial set, notes) appear in paper2 as a sensitivity analysis?
6. **Carried over from the paper2 handoff (still open):**
   - confirm the `[USER: confirm]` defaults (54 items, 64 PCs, S32);
   - the paper.md line 91 MIMIC correction (7.5 → 8.1%; 1.2 → 3.0%);
   - PS-Flags primary version (C = 1 vs CV);
   - clinician label check;
   - placebo-controlled hdPS + ECG in the main text;
   - length cuts (~6,600 words) and the journal;
   - paper2 supplement tables;
   - the remaining `[CHECK]` markers and reference renumbering.

## 6. Housekeeping

- **tmux:** session `r2` has two idle shells. Close it with `tmux kill-session -t r2`.
- **Note-derived caches** on raid0: `audits/claude-r2/notes/cache/` and `notes/<trial>/restricted_*`. Never commit them; delete the cache when R2 is abandoned.
- **Restricted audit files** (raid0 only):
  - `audits/claude-v1-audit/defects/restricted_leak_rho_per_trial.parquet`;
  - `audits/claude-v1-audit/code/restricted_sens_no_index_day_ecg.parquet`;
  - `audits/claude-v1-audit/claims/restricted_methods_trials.csv`;
  - `audits/claude-v21-paper2/review/restricted_*`.
- **Untracked, as before:** `docs/paper/trial_emulate_manuscript_v2_RC.docx` and the `docs/v13`/`v14` `*.err` logs. Don't use `git add -A`.
- **Memory note:** `docs/r2/V1_MANIFEST.md` (the version 1 contents and the 9 known defects) is only on `r2`. Read it with `git show r2:docs/r2/V1_MANIFEST.md`.
