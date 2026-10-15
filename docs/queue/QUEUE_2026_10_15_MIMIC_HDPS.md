# MIMIC-IV: hdPS on the same input window as AI-EHR, with AI-ECG and AI-EHR arms (queued 2026-10-15)

You are running unattended in tmux.

**Read first:**
- `CLAUDE.md`, `handoff.md` §1 and `pipeline.md` (§6 masks; the MIMIC rows and the 2026-10-15 deviations-log line);
- `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md`, `docs/mimic/AUDIT_MIMIC_PRIMARY_SWITCH.md`;
- code: `scripts/mimic/` (entry point `run_mimic_external.py`; `mimic_clmbr_analysis.py`; `build_meds_prior_only.py`), `scripts/v15/v15_analyze.py` (`TrialData`, hdPS levels at about line 175, `hd()`), `scripts/v15/v15_mimic_cohort.py` (panel construction about lines 160–365), `scripts/v20/mimic_replication.py`, `scripts/v21/mimic_cvd5.py`.

## Why

The MIMIC hdPS from v20 (`hdPS200` = sparse + top-200 levels) reads information that the primary AI-EHR input no longer reads:
- **the index admission's diagnosis codes,** which are coded at discharge and may describe events after t0;
- **dx / rx / px and "lab measured" flags from the index stay before t0.**

So hdPS (mean |SMD| 0.113 on the 22 items) is not comparable with PS-CVD5 + AI-EHR (0.146), whose input stops at the index admission time. **The user asked for (2026-10-15):**
1. an hdPS built on the same window as the primary AI-EHR input;
2. hdPS + AI-ECG, hdPS + AI-EHR and hdPS + both;
3. the AI-EHR arms on the demographic base too, to mirror the Yale slide 9 panel D ("Demo + AI" vs conventional PS).

## Rules

**Access**
- Write only under `/mnt/raid0/rbc58` and this repo.
- MIMIC staged tables and all other inputs are **read-only**.

**Outputs and privacy**
- New outputs go to `/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-hdps-20261015/` (`umask 077`).
- Aggregates only. Suppress counts of 1–10, including derivable ones.
- Never print patient rows, IDs or dates. Never open note text.
- Never commit restricted files (CSV / parquet with patient data). Never push.

**Compute**
- **No GPU needed.** The AI-EHR embeddings already exist (`audits/claude-mimic-clmbr-20261014/clmbr/prior_full`, the primary input).
- Never use GPU 7.
- Python: `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`.

**Files**
- Don't edit `paper.md`, `paper2.md`, `table1_picot.md`, any `.docx`, the deck or its builders, or `scripts/figures/*`. I (the interactive session) will update the figure from your summary.
- Don't modify `scripts/v15/*`, `scripts/v20/*` or `scripts/v21/*`. Import them.
- Commit only your own paths (`git add <paths>`, never `-a`). Retry if the index is locked.

**Logging**
- One line per step to `audits/claude-mimic-hdps-20261015/STATUS.md`.

## Step 0: gates

1. **Re-implement the hdPS construction** in a new module, `scripts/mimic/hdps_window.py`, importing the v15 code where possible. With the **original** window, it must reproduce the v20 `hdPS200` cells exactly (base, ECG, permECG; `audits/claude-v20-mimic-replication/results/*_vars.csv` and `*_arms.csv`; max |Δ| = 0, or explain any floating-point difference below 1e-9).
2. **The current primary cells** (`audits/claude-mimic-clmbr-20261014/results_prior`) must reproduce unchanged through the new code path for the `cvd5` base.

If either gate fails, stop and log why.

## Step 1: hdPS on the AI-EHR window ("hdPS-prior")

Use the same cut as the primary AI-EHR input: **events strictly before the index admission time** (the index ED stay before admission is kept, as for AI-EHR; record this).

1. **Investigator diagnosis flags** (the `sparse` part): from **earlier admissions only**, as in the PS-CVD5 analog (`cvd5`).
2. **dx candidate levels:** codes of earlier admissions only. Index-admission codes are excluded.
3. **rx / px / "lab measured" candidate levels:** events before the index admission time, within the existing 365-day look-back.
4. **Exposure drugs** are excluded, as now.
5. **Ranking and size:** keep the hdPS algorithm unchanged otherwise: the same level construction, ranking and top-200 selection, with fixed C = 1.
6. **Leakage checks** (aggregate counts only):
   - 0 input events at or after the index admission time, except index ED-stay events before admission; report their share;
   - 0 index-admission diagnosis or procedure codes;
   - 0 exposure-drug features.
7. **Report:** the number of candidate levels and the share of patients with no hdPS input (aggregate).

## Step 2: arms

All arms use the 7 cardiovascular trials + PEPTIC, all analysed patients, the same matching (1:1 greedy NN, caliper 0.2 SD of the logit, without replacement; < 11 pairs = failed), and the same per-trial ECG PCs and AI-EHR PCs (primary input) as the current analysis.

| Base | Arms |
|---|---|
| **hdPS-prior** (new) | base, + ECG, + CLMBR, + ECG + CLMBR, + permECG, + permCLMBR |
| demo (v20 demographic base) | base, + ECG, + CLMBR, + ECG + CLMBR, + permECG, + permCLMBR |
| hdPS200 (v20, index admission included) | + CLMBR, + ECG + CLMBR, in addition to the existing base / ECG / permECG. **Sensitivity only.** |

The existing `cvd5` arms are reused unchanged.

## Step 3: endpoints

**Item panel**
- The main comparison uses the **22 items** (utilisation, block D, excluded for every arm, as when AI-EHR is in a contrast).
- Also report the 26-item version for the arms without AI-EHR.
- Apply the `pipeline.md` §6 masks. In particular, check whether any held-out item is derivable from the hdPS-prior inputs (e.g. visit-derived utilisation), and document the result.

**Per arm**
- mean |SMD| (across-trial mean of per-trial means);
- % |SMD| < 0.1;
- by domain (A core labs and vitals, B other labs, C ventilation);
- mean |Δ log HR| vs the RCTs;
- the PEPTIC HR.

**Contrasts** (relative change in mean |SMD| over items observed in both cells; 95% CI from 4,000 trial-bootstrap resamples, seed 20261001; trials lower; exact sign-flip P, one-sided for a representation vs its base or placebo, two-sided otherwise):
- hdPS-prior vs PS-CVD5 (two-sided);
- each of hdPS-prior + ECG / + CLMBR / + both vs hdPS-prior;
- each real arm vs its placebo;
- the "Demo + AI" arms and the PS-CVD5 + AI arms vs hdPS-prior (two-sided; as on Yale slide 9 panel D);
- + ECG + CLMBR vs + CLMBR, on the hdPS-prior base;
- agreement contrasts with the benchmark-permutation P (20,000 draws);
- the same for the hdPS200 sensitivity.

**Cell validity:** failed cells, plus the overlap rule from the PROTECT AF audit (≥ 30% of the smaller arm matched or ≥ 50 pairs). hdPS + AI-EHR has about 270 inputs, so watch for near-separation as at Yale. **Don't print** per-trial n_pairs, retention or ESS.

**Write:**
- `audits/claude-mimic-hdps-20261015/summary/summary.json` and `tables.md` (aggregates);
- a short doc, `docs/mimic/MIMIC_HDPS_WINDOW.md`.

## Step 4: independent audit (a fresh subagent that built nothing)

The auditor checks:
- both Step 0 gates;
- the leakage checks of Step 1;
- that the hdPS-prior window matches the AI-EHR primary input rule;
- at least 20 headline numbers recomputed with independent code from the per-trial cells;
- the masks;
- cell validity;
- a privacy scan of the committed files.

Fix BLOCKING issues and re-audit, up to 3 rounds. Report: `docs/mimic/AUDIT_MIMIC_HDPS.md`.

## Step 5: commit and summary

1. **Commit locally:** `scripts/mimic/hdps_window.py` (and any runner), the doc and the audit report. Don't push.
2. **Add one line to `pipeline.md`'s deviations log:** "2026-10-15: MIMIC-IV hdPS rebuilt on the AI-EHR input window (history before the index admission time; index-admission codes excluded); the v20 hdPS (index admission included) becomes a sensitivity; hdPS and demographic bases gain AI-EHR arms."
3. **Write the summary** at the top of the status log and in `docs/queue/QUEUE_2026_10_15_MIMIC_HDPS_RESULTS.md` (commit). Cover:
   - the gates and leakage;
   - mean |SMD| (22 items) for unmatched, PS-CVD5, hdPS-prior, hdPS200 (sensitivity), and each AI arm on each base;
   - the vs-hdPS-prior contrasts;
   - whether the AI arms add on top of hdPS-prior;
   - agreement and PEPTIC;
   - cell validity;
   - the audit verdict.
