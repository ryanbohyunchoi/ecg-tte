# Handoff: paper2 (TRACE-ECG v2, learned representations for confounding control)

Written **2026-10-07** at the end of a Claude desktop session. Nothing in this plan has been run yet. This file is self-contained: a fresh Claude Code CLI session should be able to execute it from here. The general project brief is [handoff.md](handoff.md); the rules in `CLAUDE.md` and §1 of `handoff.md` apply to every agent.

---

## 0. How to start (server, tmux, Claude CLI)

```bash
tmux new -s paper2
cd /home/rbc58/github/ecg-tte
claude
```

Then paste the **kickoff prompt** in §6.0. Detach with `Ctrl-b d`; reattach with `tmux attach -t paper2`.

- Long jobs started by Claude should run in **new windows of the same tmux session** (see §4), so they are visible with `Ctrl-b w`, and they survive if Claude stops.
- Unattended runs need tool permissions. Choose a permission mode you are comfortable with when launching `claude` (for example `claude --permission-mode acceptEdits`); Bash commands may still ask for approval in that mode.
- Check load before starting: `nvidia-smi` and `uptime`. On 2026-10-07 the load was about 40 of 192 cores. All paper2 analyses are CPU-only.

---

## 1. Decisions made on 2026-10-07 (locked unless the user changes them)

1. **New manuscript file:** `docs/paper/paper2.md`. **Do not edit `docs/paper/paper.md`**, and do not touch `docs/paper/table1_picot.md`, which has the user's uncommitted edits.
2. **Primary comparison is PS-CVD5**, not PS-Demo: age, sex, index year plus hypertension, type 2 diabetes, CAD, AF and HF. In code this is rung `P5`, built by `v18_clmbr.designs(T, n, C.P5DX)`.
3. **Framing:** *learned representations* (the ECG embedding and CLMBR-T) compared with hand-built PS covariates.
   - Do **not** call CLMBR-T "unstructured": it embeds the coded EHR (diagnoses, drugs, procedures, measurement codes without values, visits).
   - The ECG is the physiological signal.
4. **The PI approved bringing CLMBR-T back (2026-10-07).** This reverses the earlier decision to remove it from `paper.md`. The PI's message is that the ECG should not be the only factor:
   - show the use cases where the ECG helps;
   - show whether CLMBR-T outperforms clinical or high-dimensional PS matching.

   The PI's hypothesis is that CLMBR-T captures diagnosis dates and time to the treatment decision, which yes/no code flags do not.
5. **PS-Flags (new):** demographics plus a yes/no flag for every diagnosis code.
   - Codes are ICD-10 3-character, from the **full pre-index history** (index day excluded, matching the CLMBR-T input window), at **≥1% prevalence** in the trial cohort.
   - It has no dates, counts or recency.
   - The key test is **PS-Demo + CLMBR-T vs PS-Flags**, head to head.
   - **No PS-Timing arm** (the user declined it).
6. **Trial labels:** each trial is labelled physiologic yes/no plus the expected cardiac confounding domain(s). Results are then stratified by label.
   - The user accepts some circularity.
   - Labelling is still done **blind**, by two independent labellers working only from a results-free PICOT table (it already exists, see §7), then adjudicated. It's cheap, and it makes the result more credible.
7. **Replication across configurations:** run every matching and weighting configuration and every arm, and **report all of them, with BH-FDR across the whole sweep**. Don't lead with the best one.
8. **Git:** commit code and docs locally to `main` as you go, and **don't push**; the user pushes. Never commit CSV, parquet or other restricted outputs. The Word file `docs/paper/trial_emulate_manuscript_v2_RC.docx` is untracked; leave it alone.

### Proposed defaults (Claude's; flag them in paper2.md for the user to confirm)

- **Primary balance endpoint: the 54 non-coded held-out characteristics** (vitals & core labs, other labs, the echo domains).
  - CLMBR-T and PS-Flags see the codes behind the 4 "coded record" items, so those items aren't held out for them.
  - Report the 58-item panel as secondary.
  - This matches the v1.8 CLMBR-T analysis.
- **CLMBR-T dimension:** 64 PCs (`T.clm_pc`, the v1.8 convention), with a 32-PC CLMBR-T sensitivity arm so that it matches the ECG's 32 PCs.
- **Primary trial set:** 32 analysed trials (`S32`); all 38 (`S38`) as sensitivity.

---

## 2. What is already known (from existing outputs; see the source files)

**PS-CVD5 ± ECG, 32 trials, main configuration** (1:1, caliper 0.2). Sources: `docs/paper/supplement.md` eTables 3–5 and `audits/claude-v20-sens-primary32/sensitivity.csv`.

- **Balance (58 items):**
  - mean |SMD| 0.128 → 0.117, a relative reduction of 9.0% (95% CI 4.8–13.3);
  - % with |SMD| < 0.1: 53.6 → 57.6, 21/32 trials improved, P = .003, cluster P = .016, q = .008;
  - permuted ECG: 1.1%.
- **Agreement:**
  - |Δ log HR| 0.226 → 0.196, 20/32 closer, P = .049, cluster P = .20, q = .14, **benchmark-permutation P = .70**, so mostly generic attenuation;
  - estimate agreement 15 → 22/32; standardized-difference agreement 24 → 25/32; r 0.56 → 0.57.
- **Agreement by configuration** (|Δ| P, then benchmark-permutation P):

  | Configuration | P | Benchmark-permutation P |
  |---|---|---|
  | 1:3 matching | **.007** | **.037** |
  | Overlap weighting | .011 | .20 |
  | Caliper 0.1 | .11 | — |
  | IPTW | .69 | — |
  | Gradient-boosted PS | .32 | .005 |

- **Per trial:**
  - ECG moves standardized-difference agreement from ✗ to ✓ in AF-CHF and ARISTOTLE, and from ✓ to ✗ in EMPA-REG;
  - 15 of the 20 "closer" trials moved toward HR = 1;
  - the largest movers were INSIGHT, CABANA, AF-CHF, ARISTOTLE, RE-LY and SUSTAIN-6.
- **Prespecified AF confirmation (5 trials, PS-CVD5)** went the wrong way: |Δ| 0.135 → 0.212, 1/5 closer (eTable 9).
- **Gaps:** plasmode, on-treatment estimands and MIMIC-IV have no PS-CVD5 arm yet.

**CLMBR-T results from v1.8** (older 33/38-trial sets and older masking; must be recomputed). Sources: `docs/v18/CLMBR_RESULTS.md`, `docs/v18/EMBEDDING_COMPARISON.md`, `docs/v18/CLMBR_LEAKAGE.md`.

- **Physiology balance at P5:** CLMBR+ECG gives +7.5 percentage points and is the only robust arm; CLMBR-T +5.3 and ECG +3.6 are nominal only.
- **Ladder:** CLMBR-T's gain **vanishes at hdPS200 (+0.0)**; the ECG still adds +4.1 there, though not robustly. Nothing is robust at the clinical rung.
- **No embedding gives trial-specific RCT agreement** at any rung; it's shrinkage toward the null.
- **Lab balance:** CLMBR-T dominates, partly because it sees which labs were ordered (measurement codes).
- **Leakage audit:** passed. The index day is excluded, and exposure tokens reach the model for ≤5.9% of patients.
- **Matching retention:** about 93% of the base pairs with CLMBR-T, vs 99.7% with the ECG.

---

## 3. Analysis spec for paper2

### 3.1 PS ladder (rungs) and arms

| Rung | Covariates |
|---|---|
| `P1` PS-Demo | age, sex, index year (needed for the PS-Demo + CLMBR-T vs PS-Flags head-to-head) |
| `P5` PS-CVD5 (**primary**) | P1 + 5 CVD diagnoses |
| `Flags` PS-Flags (**new**) | P1 + binary ICD-10 3-character diagnosis flags, full pre-index history, ≥1% prevalence |
| `hdPS200` | as in `sens_primary32.py` |
| `clinical` PS-Clinical | as in `sens_primary32.py` (with its `ex58` masking) |

The arms, each added to every rung:
- `base`;
- `ECG` (32 PCs, `T.ecg_pc`);
- `CLMBR` (64 PCs, `T.clm_pc`);
- `ECG+CLMBR`;
- `shufECG` (`T.ecg_pc[T.shuffle_perm]`);
- `shufCLMBR` (`T.clm_pc[T.shuffle_perm]`);
- `CLMBR32` (main configuration only; `P1` and `P5` only).

The configurations are the six in `sens_primary32.CONFIGS`: `main`, `cal01`, `m13`, `iptw`, `overlap`, `gbm`.

### 3.2 Contrasts

- **Within each rung:**
  - ECG, CLMBR-T and ECG+CLMBR-T, each vs base;
  - ECG+CLMBR-T vs CLMBR-T, and ECG+CLMBR-T vs ECG;
  - CLMBR-T vs ECG (two-sided);
  - each placebo vs base, and each embedding vs its placebo.
- **Across rungs:**
  - **P1+CLMBR vs Flags base (head-to-head, two-sided)** — this is the PI hypothesis test;
  - Flags+CLMBR vs Flags;
  - P1+CLMBR and P5+CLMBR vs hdPS200 base;
  - P5+CLMBR and P5+ECG+CLMBR vs clinical base;
  - clinical+CLMBR vs clinical.

### 3.3 Endpoints

**Balance:**
- the relative reduction in mean |SMD| over the 54 non-coded items, with a 4,000-resample trial bootstrap and fixed seed (primary);
- % of items with |SMD| < 0.1 over the 54 items;
- the 58-item panel (secondary);
- per-domain relative reductions, using the domain groups in `E.VARS`.

**Agreement:**
- mean |Δ log HR|, trials closer, and the exact one-sided sign-flip P (two-sided for head-to-heads);
- comparator-cluster P, leave-one-out max P, and the benchmark-permutation P (20,000 draws);
- Pearson r, estimate agreement and standardized-difference agreement.

**Multiplicity:** BH-FDR within the balance and agreement families, **across all configurations × contrasts**.

Reuse `sens_primary32` helpers (`paired_balance`, `contrast_row`, `relred_ci`, `bshuf`, cluster map) by importing them, not copying.

### 3.4 Trial-type analysis

Using the adjudicated labels (§5, step A):
- ECG and CLMBR-T gains, physiologic vs not, at P5: balance (54 items and per domain) and agreement;
  - the difference is tested by permuting labels across trials (10,000 draws);
- per-domain gain in trials labelled with that domain vs trials not labelled with it;
- data-driven check: Spearman correlation of the ECG gain with the residual echo-domain imbalance under P5 base, with `shufECG` as the control for room to improve.

### 3.5 Plasmode (supplement)

Extend `scripts/v20/g2b_simulation_ext.py` (by importing it) with the arms P5 base, P5+ECG, P5+CLMBR, P5+ECG+CLMBR and CLMBR-only.
- Use the same design as the paper's primary plasmode: the post hoc clinical orientation, with the withheld confounder alone driving treatment.
- Gate first: existing arms must reproduce `audits/claude-v20-g2-ext/reps_*.csv` exactly.

### 3.6 MIMIC-IV (supplement, ECG only, lowest priority)

Add a PS-CVD5 analog (demographics + ICD codes for HTN, T2D, CAD, AF and HF) to `scripts/v20/mimic_replication.py` (by importing it), ± ECG.
- First check whether the existing `sparse` base already matches it.
- There's no CLMBR-T in MIMIC.

---

## 4. Technical map

- **Python:** `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`. New code goes in `scripts/v21/`, new docs in `docs/v21/`. Import v13–v20 modules; don't modify them.
- **Outputs:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/<sub>/`, with `umask 077`. `STATUS.md` there is the progress log; agents append one line per milestone.
- **Long jobs in tmux:**

  ```bash
  tmux new-window -d -t paper2 -n <name> "bash -lc 'umask 077; cd /home/rbc58/github/ecg-tte/scripts; <cmd> 2>&1 | tee /mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/logs/<name>.log'"
  ```

  Run `tmux set-option -t paper2 remain-on-exit on` once, so finished windows stay readable.
- **Trial grid template:** `scripts/v20/sens_primary32.py`.
  - `task()` builds each rung and calls `E.run_cell(T, X, rows=r, estimator=est, ps_model=psm, cstat=None)`.
  - `S32` and `S38` are defined at its top.
  - The `run` / `gate` / `summarize` pattern and the suppression helper are there too.
  - Previous runtime: 50–509 s per trial for about 84 cells, with a 24-worker pool. Paper2 has about 2× the cells.
- **Trial object:** `v16_engine.load_trial(n)` (via `v18_af_confirm.V.E`).
  - Fields: `T.ecg_pc`, `T.ecg_pc64`, `T.clm_pc` (lazy, 64 PCs), `T.shuffle_perm`, `T.hd(200, t=, rows=)`, `T.X_dx`, `T.X_core`, `T.cov`, `T.demo`, `T.keys`, `T.rb`, `T.rs`.
  - The cohort is already the intersection with CLMBR-T availability.
- **PS-Flags source:** `scripts/build_preindex_panel.py`.
  - `dx_<ICD10 3-char>` counts; options `--lookback-days` (default 365) and `--min-prevalence` (default 0.02).
  - Run it with `--lookback-days 36500 --min-prevalence 0.01`. Keep `dx_` columns only, binarised (count > 0).
  - OMOP root: `/mnt/raid0/rbc58/omop/gold`. Roster: `$A/claude-<n>-cohort-v1/restricted_cohort.parquet` (see `scripts/v18/build_queue.sh`; check the cohort directory names for the v1.6 trials).
  - Check the window semantics (`[index − lookback, index − 1]`) against the CLMBR-T input window in `docs/v18/CLMBR_LEAKAGE.md`.
  - Exclude any `roles["exposure_features"]`.
- **Existing outputs to gate against:**
  - `audits/claude-v20-sens-primary32/restricted_cells.parquet`: P1/P5/hdPS200/clinical × base/ECG/shufECG must reproduce to ≤ 1e-12;
  - `audits/claude-v18-embed-compare/restricted_results_unsuppressed.parquet`: the CLMBR-T cells; report any deviation from the newer masking.
- **Figures template:** `scripts/v20/make_paper_figures.py` (style, palette, panel export).
- **Quality tiers:** `docs/v19/quality_tiers.json`.

---

## 5. Workplan (order and dependencies)

| Step | What | Depends on | Est. time |
|---|---|---|---|
| A | Two blind labellers → adjudicated `docs/v21/TRIAL_LABELS.{json,md}`, committed **before** any stratified result is computed | — | 20 min |
| B | Core grid: PS-Flags panels → grid → gate → summarize → `docs/v21/PAPER2_RESULTS.md` | — (labels needed only for its final step) | 1.5–3 h |
| C | Plasmode extension → `docs/v21/PLASMODE_PAPER2.md` | — | 1–2 h |
| D | MIMIC PS-CVD5 analog → `docs/v21/MIMIC_PAPER2.md` | — | 1–2 h |
| E | Reviewer audit of B (and of C and D when done) → `docs/v21/AUDIT_PAPER2_ANALYSES.md` | B | 45 min |
| F | Figures + HTML gallery: `scripts/v21/make_paper2_figures.py` → `docs/paper/figures_paper2/` + `docs/paper/figures_paper2/index.html` | B, E | 1 h |
| G | `docs/paper/paper2.md` | B, E, F | 1 h |
| H | Final claim-by-claim audit of `paper2.md` + figures vs sources → `docs/v21/AUDIT_PAPER2_MANUSCRIPT.md`; fix, then commit | G | 45 min |

A, B, C and D run in parallel; B, C and D are long jobs in tmux windows.

### Paper2 outline (agreed with the user)

| Item | Content |
|---|---|
| **Table 1** | PICOT for each trial + quality tier + physiologic label and domains |
| **Figure 1** | Design: trials, data, representations (ECG, CLMBR-T), PS ladder (PS-CVD5, PS-Flags, hdPS, PS-Clinical), analyses |
| **Figure 2** | Balance: each PS × (base, +ECG, +CLMBR-T, +both), relative reduction, placebos |
| **Figure 3** | What each representation captures: domain heatmap (ECG vs CLMBR-T vs both), plus **PS-Demo + CLMBR-T vs PS-Flags** and CLMBR-T vs hdPS / PS-Clinical |
| **Figure 4** | Which trials benefit: per-trial gains by label (physiologic vs not; by domain) |
| **Figure 5** | Replication: agreement metrics across every configuration and arm, with the benchmark-permutation test, by label and quality tier |
| **Supplement** | Plasmode with PS-CVD5 arms; MIMIC-IV (ECG only); all-configuration tables; 38-trial sensitivity; CLMBR-T 32-PC sensitivity; estimands and echo subset carried over from paper.md |

---

## 6. Prompts

### 6.0 Kickoff prompt (paste into the Claude CLI)

> Read `CLAUDE.md`, `handoff.md` §1, and `HANDOFF_PAPER2.md` in full. You are the coordinator for paper2. Execute the workplan in HANDOFF_PAPER2.md §5 using subagents (Agent tool) with the prompts in §6.1–6.8, running A, B, C and D in parallel and long jobs in windows of the existing tmux session `paper2` (§4). Don't redo anything already done; check `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/STATUS.md` first. After each agent finishes, check its report against its files, append a line to STATUS.md, and commit code and docs locally (never restricted outputs, never push, don't touch paper.md, table1_picot.md or the .docx). Launch the reviewer (6.5) as soon as B's results exist, and don't start figures or writing until the reviewer's blocking issues are fixed. If a gate fails or a decision in §1 can't be met, stop that branch, write the problem to STATUS.md, and continue the others. At the end, write a short summary for the user at the top of STATUS.md: what was done, the key results, open questions, and the paths to paper2.md and the figure HTML.

### 6.1 Step A: blind labeller (run twice, as labels_A and labels_B)

> You are an independent clinical labeller (cardiology / pharmacoepidemiology). STRICT BLINDING: read ONLY `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/labels/picot_blind.md` (PICOT for 38 trials, no results) and use your own clinical knowledge of the trials and real-world prescribing. Do not read anything else in the repo or on /mnt/raid0, and don't run analyses.
>
> Context: in EHR emulations (new-user, active-comparator), we test whether an AI-ECG embedding added to the PS controls confounding. For EACH trial give:
> 1. `physiologic`: "yes"/"no". In routine care, is the choice between intervention and comparator plausibly driven substantially by cardiac structure, function, rhythm/conduction or haemodynamic/congestion state (things an ECG can reflect), rather than mainly by metabolic, renal, bleeding, frailty, cost/formulary or prescriber factors? Think about channelling: who actually gets each drug.
> 2. `domains`: one or more of `["LV_structure","LV_systolic_function","diastolic_LA","RV_pulmonary_congestion","rhythm_conduction","none_cardiac"]` (`none_cardiac` alone if none apply).
> 3. `confidence`: high / medium / low.
> 4. `rationale`: at most 25 words.
>
> Run `umask 077`, then write a JSON list (keys: trial, physiologic, domains, confidence, rationale; all 38 trials, named exactly as in the table) to `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/labels/labels_<A|B>.json`. Write nothing else. Reply with the yes/no counts and any hard cases.

**Adjudication (coordinator):**
- compute agreement (Cohen's κ for `physiologic`);
- resolve disagreements with a third blind agent given both rationales, or flag them for the user;
- write `docs/v21/TRIAL_LABELS.json` and `docs/v21/TRIAL_LABELS.md`, with the rubric, κ, the adjudication log and the final labels;
- **commit them before step B's stratified analysis runs.**

### 6.2 Step B: core analysis agent

> You implement and run the paper2 core analysis. Read `CLAUDE.md`, `HANDOFF_PAPER2.md` (§1–§4 in full; §3 is your spec), `scripts/v20/sens_primary32.py`, `scripts/v18/v18_clmbr.py`, the `Trial` class in `scripts/v13_common.py`, `scripts/v16/v16_engine.py` (`load_trial`, `run_cell`, `VARS`), `scripts/build_preindex_panel.py` and `docs/v18/CLMBR_LEAKAGE.md`. Rules: write only to `scripts/v21/`, `docs/v21/` and `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/` (`umask 077`). Aggregates only; suppress counts of 1–10; never print patient rows or identifiers. Don't modify existing scripts (import them). Don't commit (the coordinator does). Run long jobs in the `paper2` tmux session (§4) with at most 24 workers, after checking `uptime`.
>
> Steps:
> 1. **PS-Flags panels** for all 38 trials (§4 PS-Flags source): full pre-index history, ICD-10 3-character diagnosis codes only, binary, ≥1% prevalence, index day excluded, exposure features excluded. Verify the window matches the CLMBR-T input window, and write a short check (feature counts and window) to `docs/v21/PS_FLAGS.md`.
> 2. **`scripts/v21/paper2_grid.py`** with `run`, `gate`, `summarize` and `labels` subcommands, implementing §3.1–3.3 for all 38 trials (rungs × arms × 6 configurations).
> 3. **Gate:** P1/P5/hdPS200/clinical × base/ECG/shufECG must reproduce `claude-v20-sens-primary32` cells to ≤ 1e-12. Compare the CLMBR-T cells with `claude-v18-embed-compare` and explain any deviation. If the sens-primary32 gate fails, stop and report.
> 4. **Summarize** for S32 (primary) and S38: every contrast in §3.2 × every configuration × every endpoint in §3.3, with BH-FDR across the full sweep. Write `sensitivity.csv`-style tables plus per-trial, per-domain aggregates (trial-level only) to the audits folder.
> 5. **Labels:** when `docs/v21/TRIAL_LABELS.json` exists (check every 5 minutes, for up to 90 minutes), run §3.4. If it never appears, skip this step and say so.
> 6. **Write `docs/v21/PAPER2_RESULTS.md`:** a plain-language verdict first, then tables (aggregates only), with every number traceable to a named CSV.
>
> Report: files written, gate result, the headline numbers (PS-CVD5 balance and agreement for ECG, CLMBR-T and both; PS-Demo + CLMBR-T vs PS-Flags; CLMBR-T vs hdPS and PS-Clinical; configurations that reach q < .05), and any deviations from the spec.

### 6.3 Step C: plasmode agent

> Extend the plasmode simulation for paper2 per `HANDOFF_PAPER2.md` §3.5. Read `CLAUDE.md`, `HANDOFF_PAPER2.md` §1–§4, `scripts/v20/g2b_simulation_ext.py`, `docs/v20/G2_EXTENSION.md` and `docs/v19/G2_SIMULATION.md`. Write `scripts/v21/paper2_plasmode.py`, which imports g2b and adds the arms P5 base, P5+ECG, P5+CLMBR (64 PCs, `T.clm_pc`), P5+ECG+CLMBR and CLMBR-only, on the same cells, seeds and replicates as the paper's primary (clinically oriented, treatment-from-C) design. Gate first: existing arms must reproduce `audits/claude-v20-g2-ext/` exactly; stop and report if not. Outputs go to `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/plasmode/` (`umask 077`, aggregates only). Run in the `paper2` tmux session with at most 24 workers. Write `docs/v21/PLASMODE_PAPER2.md`: % bias removed by confounder, Monte Carlo SEs, and coverage. Don't commit. Report the gate result and the headline numbers.

### 6.4 Step D: MIMIC agent (lowest priority)

> Add a PS-CVD5 analog to the MIMIC-IV replication per `HANDOFF_PAPER2.md` §3.6. Read `CLAUDE.md`, `HANDOFF_PAPER2.md` §1–§4, `scripts/v20/mimic_replication.py`, `docs/v20/MIMIC_REPLICATION.md` and `docs/v20/MIMIC_REPLICATION_PLAN.md`. First check whether the existing `sparse` base (demo + dx) already equals demographics + HTN, T2D, CAD, AF and HF; if it does, just report that. Otherwise write `scripts/v21/mimic_cvd5.py` (importing `mimic_replication`). Gate on the existing demo cells, then run CVD5 ± ECG ± permuted ECG for the 7 trials + PEPTIC. Outputs go to `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/mimic/` (`umask 077`, aggregates only, suppress 1–10). Write `docs/v21/MIMIC_PAPER2.md`. Time-box to 2 hours; if it isn't feasible, report why. Don't commit.

### 6.5 Step E: reviewer / auditor agent

> You are an adversarial reviewer of the paper2 analyses. Read `CLAUDE.md`, `HANDOFF_PAPER2.md`, `docs/v21/PAPER2_RESULTS.md`, `docs/v21/PS_FLAGS.md`, `docs/v21/TRIAL_LABELS.md`, `scripts/v21/*.py` and the outputs in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/`. Check:
> 1. **Spec compliance** with §1 and §3: rungs, arms, configurations, contrasts, endpoints, FDR across the full sweep.
> 2. **Leakage:** the PS-Flags window vs CLMBR-T's; exposure features excluded; held-out items not used by any PS they evaluate (54-item primary; masking for clinical).
> 3. **The gate** actually passed and was computed correctly.
> 4. **Recompute independently**, from `restricted_cells`, at least: the P5 ECG / CLMBR-T / both balance relative reductions with CIs, the P1+CLMBR vs Flags head-to-head, one agreement row with its benchmark-permutation P, and one label-stratified result. They must match the reported values.
> 5. **Every number in PAPER2_RESULTS.md** traces to a file.
> 6. **Privacy:** no patient-level rows anywhere in the repo, no counts of 1–10 unsuppressed, no CSV or parquet staged in git.
> 7. **Statistical issues:** multiplicity, one- vs two-sided tests, circularity of the labels, dimension mismatch (64 vs 32 PCs), retention differences.
>
> Write `docs/v21/AUDIT_PAPER2_ANALYSES.md`: findings marked BLOCKING / SHOULD-FIX / NOTE, each with evidence. Don't edit analysis code. Reply with the list of blocking issues.

### 6.6 Step F: figures + HTML agent

> Build the paper2 figures per the outline in `HANDOFF_PAPER2.md` §5 (Figures 1–5, plus the supplementary figures for plasmode, MIMIC and the all-configuration sweep if their results exist). Read `HANDOFF_PAPER2.md`, `docs/v21/PAPER2_RESULTS.md`, `docs/v21/AUDIT_PAPER2_ANALYSES.md`, `docs/v21/TRIAL_LABELS.md` and `scripts/v20/make_paper_figures.py`, and match its style, palette and per-panel export. Write `scripts/v21/make_paper2_figures.py`, reading only the aggregate outputs in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/`. Outputs: `docs/paper/figures_paper2/{main,supplementary}/` (PNG 300 dpi + PDF) and `docs/paper/figures_paper2/index.html`, a single self-contained gallery (images base64-embedded) with each figure, a concise legend, and the source file for each panel. Also copy the HTML to `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/figures_paper2.html`. No patient-level data, and suppress counts of 1–10. Open each PNG to check legibility, overlap and labels. Don't commit. Report the file list and any design choices for the user to approve.

### 6.7 Step G: paper2.md writer

> Draft `docs/paper/paper2.md`. Read `HANDOFF_PAPER2.md` (decisions §1, outline §5), `docs/paper/paper.md` (style; reuse Introduction, Methods and Discussion text where still valid), `docs/paper/supplement.md`, `docs/v21/*.md` and the figure legends in `docs/paper/figures_paper2/index.html`.
> - **Framing:** learned representations (ECG, CLMBR-T) vs hand-built PS covariates; PS-CVD5 primary; PS-Flags vs CLMBR-T tests whether the learned record representation adds beyond yes/no diagnosis flags (the PI's timing hypothesis, untested directly); trial-type results are descriptive.
> - **CLMBR-T** is not "unstructured".
> - **Replication:** report it honestly. Lead with balance; report every configuration with FDR, and state the benchmark-permutation result plainly.
> - **Every number** must come from `docs/v21/` or existing supplement sources. Mark anything unverified as `[CHECK]`, and the proposed defaults (54-item primary, 64 PCs) as `[USER: confirm]`.
> - Keep the paper.md section structure (Abstract placeholder, Introduction, Methods, Results, Tables and Figures, Discussion), and add a short "Changes from paper.md" note at the end.
>
> Don't edit `paper.md`. Don't commit.

### 6.8 Step H: final manuscript audit

> Audit `docs/paper/paper2.md` and `docs/paper/figures_paper2/` claim by claim, as in `docs/paper/AUDIT_MANUSCRIPT_2026-10-01.md`. For every number and claim: the source file, MATCH / MISMATCH / UNSUPPORTED, and the fix. Also check consistency with the decisions in `HANDOFF_PAPER2.md` §1, the figure-text agreement, and that no patient-level data or counts of 1–10 appear. Write `docs/v21/AUDIT_PAPER2_MANUSCRIPT.md`, then apply the fixes to paper2.md (not to paper.md) and list what changed. Don't commit.

---

## 7. Current state (2026-10-07, end of desktop session)

- **Nothing has been run.** A first attempt was cancelled by the user before any output. The `paper2` tmux session was killed, so recreate it (§0).
- **Already exists:**
  - `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/labels/picot_blind.md`: results-free PICOT (38 trials) for the blind labellers. Check it before use: it's lines 106–145 and 157–164 of `paper.md`, with the RCT estimate and quality columns removed.
  - `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/STATUS.md`: stale; overwrite it at kickoff.
  - Empty `docs/v21/` and `scripts/v21/` folders.
- **Untracked in git:** `docs/paper/trial_emulate_manuscript_v2_RC.docx` (the user's Word manuscript, moved from `/mnt/raid0/rbc58/` on 2026-10-07) and the `docs/v13`/`docs/v14` `*.err` logs. `docs/paper/table1_picot.md` has the user's uncommitted edits.
- **Note:** a per-trial PS-CVD5 agreement table was viewed in the desktop session (§2). The labellers must still work only from `picot_blind.md`.
