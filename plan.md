# plan.md: R2 overnight run (clean restart on the 38 trials, new rules, interactive explorer, clinical-note embeddings)

Written **2026-10-07, 22:15 EDT**.

**Deadline: everything below is done by 08:00 EDT on 2026-10-08.** The user reads the results in the morning, starting with the interactive HTML explorer.

The rules in `CLAUDE.md` and `handoff.md` §1 apply to every agent: write only under `/mnt/raid0/rbc58` and this repo; aggregates only; suppress counts of 1–10; never commit restricted outputs.

**Naming:**
- "R2" is the clean restart.
- "Version 1" is everything to date (paper.md, paper2.md, scripts v13–v21). It's frozen and not moved (§1).
- Don't call this "v2": `docs/v20` is already "v2.0", and `archive/2026-09-09-legacy-v1/` is an older implementation.

---

## 0. How to run (server, tmux, Claude CLI)

```bash
tmux new -s r2
cd /home/rbc58/github/ecg-tte
claude
```

Paste the **kickoff prompt** (§7.0), then detach with `Ctrl-b d`. Reattach with `tmux attach -t r2`; `Ctrl-b w` lists the job windows.

- **Permissions:** the run is unattended for about 9 hours. Launch `claude` in a permission mode that won't block on routine Bash and Edit prompts; that choice is yours. A blocked prompt at 23:00 means nothing is done by 08:00.
- **Progress log:** `/mnt/raid0/rbc58/ecg-tte/audits/claude-r2/STATUS.md`. The coordinator writes a summary for the user at the top before 08:00.

---

## 1. Version 1 is frozen, not moved

Moving files would break every import and path, so freeze version 1 instead:
1. tag `trace-v1` on the current `main`;
2. write `docs/r2/V1_MANIFEST.md`: one page listing what version 1 contains (paper.md, paper2.md, the supplement, figures, docs v13–v21, key audit folders) and its known defects (`docs/v2_planning/LESSONS_FROM_V1.md`).

R2 writes only to new locations:
- `scripts/r2/`, `docs/r2/`;
- `/mnt/raid0/rbc58/ecg-tte/audits/claude-r2/<sub>/` (`umask 077`).

R2 code may **import** version 1 modules; it must not modify them.

---

## 2. What R2 changes, and why (lessons from version 1)

| # | Version 1 problem | R2 rule |
|---|---|---|
| 1 | Held-out masking by exact name only; near-duplicates leaked (PS-Clinical: echo EF ≈ LVEF, eGFR from creatinine + age + sex; hdPS: `rx_` codes vs the medications item) | **A leakage map for every PS scenario** (§4.3), audited, as a **gate** before any balance result |
| 2 | Agreement "improved" for every arm by shrinking toward the null (benchmark-permutation P .70–.94) | **Primary agreement test = the benchmark-permutation test** (trial-specific). |
| 3 | One fixed L2 penalty; PS-Flags overfitted small trials (PROTECT AF dropped) | **Penalty tuned per trial × PS specification × arm**, by 5-fold cross-validated log loss |
| 4 | IPTW unstable with rich PS models (effective sample size 0.18–0.44) | **No IPTW.** Estimators: 1:1 caliper-0.2 matching (primary), overlap weighting, 1:3 matching |
| 5 | Ad hoc PS ladder | **PS scenarios defined by data availability** (§4.1) |
| 6 | Quality tiers and the 32-trial set were finalised after results | **Fresh, blind quality re-audit under a written rubric** (§4.4); the primary set is fixed before any R2 result |
| 7 | Many contrasts, few declared hypotheses | **Six declared primary hypotheses** (§4.5); everything else is exploratory, with BH-FDR across the full sweep |
| 8 | "Does the representation substitute for missing physiology?" was never asked directly | **A substitution (gap-closure) endpoint** (§4.2) |
| 9 | Coded-record and physiological representations only | **Add clinical-note embeddings** (Qwen3-Embedding-8B, §5) |

**Kept from version 1:**
- the 38 trial cohorts and their RCT benchmarks (re-verified, §4.4);
- the ECG embedding (32 PCs) and CLMBR-T (64 PCs; 32 as sensitivity);
- the blind trial labels (`docs/v21/TRIAL_LABELS.json`);
- the Cox/HR pipeline and the plasmode code (not re-run in R2 tonight).

**Cohort definitions:** they change only if the re-audit finds a must-fix error that a mechanical spec edit can correct (a wrong washout, age bound or code list), and only if the rebuild finishes by 01:30. Everything else is recorded as "deferred".

---

## 3. Schedule (EDT) and fallbacks

| Time | Milestone | Fallback if late |
|---|---|---|
| 22:30 | Kickoff. Freeze version 1 (§1). Launch, in parallel: protocol writer (P), two quality re-auditors (Q-A, Q-B), notes agent (N) | — |
| 23:30 | Protocol drafted (`docs/r2/PROTOCOL_R2.md`); protocol auditor (PA) starts | — |
| 00:00 | **Protocol frozen and committed** (PA's blocking issues fixed). Re-audit adjudicated → `docs/r2/QUALITY_R2.{json,md}` committed. Leakage-map agent (K) starts | Protocol not frozen by 00:30 → freeze as is and log the open issues |
| 00:45 | **Leakage map gate passed** (`docs/r2/LEAKAGE_MAP.md`). Core grid (B) launched without the notes arms | Gate fails → B uses the map with the failing items additionally masked; log it |
| 01:30 | Last chance for must-fix cohort rebuilds | Defer them |
| 02:30 | Core grid done and summarized | — |
| ~03:30 | Notes embeddings ready. **B patch run adds the NOTES arms** | Notes not ready by 04:30 → the explorer ships without notes, with a "notes pending" banner; N keeps going and the coordinator patches after 08:00 |
| 04:30 | Reviewer (E) audits K, B and N | — |
| 05:30 | Explorer (H) and results doc (W) start, from audited outputs | — |
| 07:30 | Final audit (F), fixes, STATUS summary, local commit | Anything unfinished is listed at the top of STATUS.md |
| **08:00** | **Done** | — |

**Resources:** CPU jobs use at most 48 workers, after checking `uptime`; the load was about 60 of 192 cores at 22:15. GPUs 3, 4, 5 and 7 were free at 22:15. **Use only GPUs with <1 GB in use when you start; never touch other users' jobs.** Run long jobs in windows of tmux session `r2`:

```bash
tmux set-option -t r2 remain-on-exit on
tmux new-window -d -t r2 -n <name> "bash -lc 'umask 077; cd /home/rbc58/github/ecg-tte/scripts; <cmd> 2>&1 | tee /mnt/raid0/rbc58/ecg-tte/audits/claude-r2/logs/<name>.log'"
```

---

## 4. R2 analysis design (the protocol writer turns this into PROTOCOL_R2.md)

### 4.1 PS scenarios (data-availability levels)

| Scenario | Name | Covariates | Version 1 source |
|---|---|---|---|
| S0 | Demographics | age, sex, index year (reference only) | `P1` |
| **S1** | **Claims-minimal (primary)** | S0 + HTN, T2D, CAD, AF, HF | `P5` (`v18_clmbr.designs`) |
| S2a | Claims-rich, flags | S0 + yes/no ICD-10 3-character diagnosis flags, full pre-index history, ≥1% | v21 `Flags` (panels in `audits/claude-v21-paper2/core/flags/`) |
| S2b | Claims-rich, hdPS | hdPS200 (treatment-only ranking) | `hdPS200` |
| S3 | EHR-structured | PS-Clinical: vitals, labs, LVEF, meds, utilisation (single imputation) | `clinical` (`T.X_core`) |

**Representations added to each scenario:**
- `ECG` (32 PCs), `CLMBR` (64 PCs), `NOTES` (64 PCs, §5);
- the pairs `ECG+CLMBR`, `ECG+NOTES`, `CLMBR+NOTES`, and all three, `ALL`;
- placebos `shufECG`, `shufCLMBR`, `shufNOTES`, permuted within trial with `T.shuffle_perm`;
- `CLMBR32` (S1 only).

**Representation-only PS** (demographics + one representation, no diagnoses), to show what each carries alone.

**Fitting:** L2 logistic regression with the penalty chosen by 5-fold cross-validated log loss over the grid 10⁻⁴…10 (reuse the v21 `flagscv` code path). Gradient-boosted PS as a sensitivity only, if time allows.

**Estimators:** `match02` (1:1, caliper 0.2 SD of the logit; primary), `overlap`, `m13` (1:3, caliper 0.2).

### 4.2 Endpoints

1. **Balance (primary):** the relative reduction in mean |SMD| over each scenario's **leakage-clean held-out set** (§4.3), with a 4,000-resample trial bootstrap. Also report % |SMD| < 0.1 and per-domain results.
2. **Substitution / gap closure (primary for H5):** for the measured-physiology items that S3 contains (the vitals & core labs, and LVEF):

   > closure = (imbalance(S1) − imbalance(S1 + representation)) / (imbalance(S1) − imbalance(S3))

   It's computed on those items, which are held out for S1 and in the PS for S3. This answers "how much of what measuring physiology buys does the representation recover?" Use the trial-pooled ratio of means, with a bootstrap CI.
3. **Agreement with the RCT result:**
   - **primary:** benchmark-permutation P for the reduction in |Δ log HR| (20,000 reassignments);
   - **secondary:** |Δ log HR|, trials closer, estimate agreement, standardized-difference agreement, Pearson r.
4. **Diagnostics for every cell:**
   - retention of the smaller arm;
   - effective sample size (overlap weighting);
   - cross-fitted treatment C statistic. **A PS with C > 0.90 is flagged as a near-instrument**, which matters for notes.

### 4.3 Leakage map (gate)

For every scenario × representation, list every held-out item that is:
- the same quantity as a PS input (LVEF ↔ echo EF);
- derived from PS inputs (eGFR ← creatinine, age, sex);
- in the same code family as a PS input (the medications item ↔ `rx_` codes in hdPS; coded-record summaries ↔ CLMBR-T, flags and notes);
- or, data-driven: Spearman |ρ| ≥ 0.80 between the item and any single PS input in the pooled trial data (aggregate correlations only).

Mapped items are masked for that scenario. **Notes** see free text that can state measured values (e.g. "EF 35%"), so held-out physiology is *not* masked for NOTES. This is labelled explicitly as "notes may contain the value", and a digits-masked notes variant is a stretch goal (§5).

Output: `docs/r2/LEAKAGE_MAP.md` and `scripts/r2/leakage_map.json`. The reviewer audits it, and **the grid reads the JSON, so masking can't drift from the document.**

### 4.4 Trial re-audit

- **Who:** two independent blind auditors (Q-A, Q-B), working only from the results-free PICOT (`/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/labels/picot_blind.md`) and the trial specification code (`scripts/trial_specs.py` and the cohort builders). They see no emulation results.
- **Rubric v2, scored per trial:**
  - time-zero alignment (in-hospital initiation, run-in, switch designs);
  - comparator fidelity, with **placebo-proxy comparators penalised**;
  - outcome fidelity (components ascertainable, cause-specific vs all-cause);
  - eligibility fidelity;
  - treatment-strategy identifiability;
  - follow-up horizon vs the delayed effect;
  - benchmark type (HR vs RR, ITT vs per-protocol);
  - expected adherence and switching;
  - feasibility (size, events).
- **Tiers:** A (close), B (minor deviations), C (substantial), D (limited, excluded). Rules: any one "poor" item → at most C; two or more poor items, or a placebo proxy plus a poor item → D.
- **Benchmarks:** the auditors also check each RCT HR and CI in `trial_specs.PUBLISHED` against the cited publication. Use web access if available; flag, don't fix.
- **Adjudication (coordinator):** compute κ; resolve disagreements by the rubric text. **The R2 primary set is tiers A–C, committed before B runs.**
- **Labels:** physiologic and domains, reused from `docs/v21/TRIAL_LABELS.json`.

### 4.5 Declared primary hypotheses (S1 = claims-minimal; primary estimator `match02`; 32-or-so trial primary set from §4.4)

| | Hypothesis |
|---|---|
| H1 | S1 + ECG improves leakage-clean balance vs S1 |
| H2 | S1 + CLMBR-T improves balance vs S1 |
| H3 | S1 + NOTES improves balance vs S1 |
| H4 | Any representation improves balance beyond S2b (hdPS), tested for ECG, CLMBR-T and NOTES separately |
| H5 | Representations close part of the S1 → S3 gap on measured physiology (closure > 0), for ECG, CLMBR-T, NOTES and ALL |
| H6 | S1 + ALL shows **trial-specific** agreement gain (benchmark-permutation P < .05) |

- Holm correction within H1–H6.
- Everything else is exploratory: BH-FDR across the full sweep (all scenarios × arms × estimators), separately for balance and agreement.
- Label, area and quality-tier analyses are descriptive.

---

## 5. Clinical-note embeddings (agent N), running in parallel from 22:30

**Governance:** the user requested this on 2026-10-07. The user should confirm with the PI that use of note text is covered by the IRB. Processing must stay fully local:
- **no external APIs** and no text in logs, stdout, docs or git;
- only public model weights are downloaded;
- note text is read programmatically and never printed or summarized by an agent;
- set `HF_HUB_OFFLINE=1` after the download, and `VLLM_NO_USAGE_STATS=1` and `DO_NOT_TRACK=1`.

**Sources:**
- `/mnt/raid0/rbc58/mosaic/mosaic5/notes_parquet/*.parquet`: columns `note_id`, `mrn`, `note_type`, `note_created_time`, `note_text`; 2021–2026; about 3.4M notes in the first 5 files;
- `/mnt/raid0/rbc58/mosaic6/`: 2013–2023; inventory it first.

These are read-only inputs, so read them in place. Join `mrn` to `patient_key` (= OMOP `person_source_value`, see `select_cohort_ecgs.digits`). Deduplicate by `note_id`.

**Model:** `Qwen/Qwen3-Embedding-8B` (Apache-2.0), downloaded to `/mnt/raid0/rbc58/models/qwen3-embedding-8b/`.
- Environment: a new one at `/mnt/raid0/rbc58/ecg-tte/software/qwen-env/` (vLLM with the embedding/pooling task if it installs cleanly; otherwise transformers ≥ 4.51 with last-token pooling, as on the model card).
- Use bf16 and an instruction prefix such as "Represent this clinical note for summarizing the patient's clinical state".
- **Fallback:** if the embedding model can't run, use `Qwen/Qwen3-8B` mean-pooled last hidden states, and log the deviation.

**Per-patient note set** (for each trial × patient, fixed by the plan, not tuned on results):
- **Window:** notes with `note_created_time` < index date (index day excluded, matching CLMBR-T), within 365 days.
- **Selection:** the K most recent notes, preferring note types in this order: H&P / consult / progress / discharge summary / other.
- **Exposure masking:** before embedding, replace every study-arm drug or procedure term for that trial (generic and brand names, from `trial_specs` keywords and `roles.json` `exposure_features`) with `[TREATMENT]`. Log only aggregate replacement rates.
- **Truncation:** the first T tokens of each note (history first; this avoids the assessment-and-plan section, which states the treatment decision).
- **Patient vector:** mean of the note embeddings; reduce to 64 PCs within each trial.
- **Patients with no note:** a zero vector plus a `notes_missing` indicator in the NOTES arm.
- Report coverage per trial (aggregates, suppressed).

**Budget:** first count the notes and tokens (counts only), then pick **K and T to fit about 3 GPU-hours on the free GPUs**. The default is K = 4, T = 1,024. Embed each unique `note_id` once, then aggregate per trial window. Log the chosen K and T and why.

**Sensitivity variants** (if time allows, in this order):
1. exclude notes from the last 7 days before index (residual decision leakage);
2. a digits-masked variant (removes numeric values such as "EF 35%");
3. an analysis restricted to patients with ≥1 note.

**Outputs** (restricted, `umask 077`):
- `audits/claude-r2/notes/<trial>/restricted_notes_pc64.parquet`, with `patient_key` and 64 PCs;
- `notes_coverage.csv` (aggregate);
- `docs/r2/NOTES_EMBEDDINGS.md`: method, coverage, K and T, masking rates, timing, deviations;
- the hand-off flag `audits/claude-r2/notes/READY` once all trials are written.

---

## 6. Interactive explorer (agent H): the main deliverable

A single self-contained HTML file, with no CDN, vanilla JS and the data embedded as JSON, in the style of the version 1 lab deck (`scripts/build_lab_deck.py`: balance explorer around line 696, emulation explorer around line 720, plasmode explorer around line 771) and the paper2 gallery (`docs/paper/figures_paper2/index.html`).

Built by `scripts/r2/build_explorer.py` from audited aggregate outputs only. Written to `docs/r2/explorer/index.html` and copied to `/mnt/raid0/rbc58/ecg-tte/audits/claude-r2/explorer.html`.

**Tabs:**
1. **Summary:** the headline results for H1–H6, with q and P values, plus what's still pending (e.g. notes).
2. **Where it works best: balance.**
   - Controls: scenario (S0–S3), representation(s) (checkboxes, including combinations and placebos), estimator, trial subset (all, primary set, quality tier, physiologic label, area, single trial), metric (relative reduction, mean |SMD|, % < 0.1) and view (by domain, by item).
   - Shows: an estimate with CI and q; a heatmap of trials × representations (gain), sortable by gain, label or area; and a love plot of items for the selected arms in single-trial view.
3. **Substitution:** gap closure by representation and estimator, overall and per trial; which measured items each representation recovers.
4. **Where it works best: trial emulation.**
   - A per-trial forest of emulated vs RCT HR for the selected arms;
   - an agreement metrics table (|Δ log HR|, trials closer, estimate and standardized-difference agreement, r, **benchmark-permutation P**, q);
   - the same subsets as tab 2.
5. **Leakage map:** for each scenario × representation, which items are masked and why.
6. **Diagnostics:** retention, effective sample size, treatment C statistic (near-instrument flags), notes coverage, cross-validated penalties.
7. **Methods and provenance:** a short version of the protocol, the source file for every panel, the git commit, and what changed from version 1.

**Rules:**
- aggregates only; counts of 1–10 suppressed (shown as "<11");
- no patient keys;
- every number comes from a named CSV;
- open the HTML headlessly (Playwright from the session scratchpad, as in `handoff.md` §2) and screenshot each tab to check that it renders.

---

## 7. Prompts

### 7.0 Kickoff prompt (paste into the Claude CLI)

> Read `CLAUDE.md`, `handoff.md` §1 and `plan.md` in full. You are the R2 coordinator. The deadline is 08:00 EDT on 2026-10-08 (plan.md §3). Run the plan with subagents (Agent tool) using the prompts in plan.md §7.1–7.10, in parallel where the schedule allows. Run long jobs in windows of tmux session `r2` (§3).
>
> First:
> 1. Create `/mnt/raid0/rbc58/ecg-tte/audits/claude-r2/{logs,STATUS.md}` (`umask 077`).
> 2. Freeze version 1 (§1: `git tag trace-v1`; write `docs/r2/V1_MANIFEST.md`).
> 3. Launch P, Q-A, Q-B and N immediately.
>
> After each agent finishes, check its report against its files, append one line to STATUS.md, and commit code and docs locally to `main`: never restricted outputs or note text; never push; don't touch paper.md, paper2.md, table1_picot.md or the .docx.
>
> Enforce the gates: the protocol is frozen and committed before K; the quality set is committed before B; the leakage gate passes before any balance result; reviewer E's blocking issues are fixed before H and W use the outputs. Follow the fallbacks in §3 exactly when a milestone slips. Never wait on the user, who is asleep; log any decision you make in STATUS.md under "Decisions taken overnight".
>
> Before 08:00, write a summary for the user at the top of STATUS.md: what was done, the H1–H6 results, the path to the explorer, what's pending, and the decisions you took.

### 7.1 P: protocol writer (22:30–23:30)

> Write `docs/r2/PROTOCOL_R2.md` from `plan.md` §2 and §4 (and §5 for the NOTES arm). Read `plan.md`, `docs/v2_planning/LESSONS_FROM_V1.md`, `HANDOFF_PAPER2.md`, `docs/v21/PAPER2_RESULTS.md` §1–2 (design only; don't restate results), `scripts/v21/paper2_grid.py` and `scripts/v20/sens_primary32.py`.
>
> The protocol must specify exactly: scenarios and covariates; representations and placebos; penalty tuning; estimators; the leakage-map rules; endpoints, including the gap-closure formula; H1–H6 with their tests and Holm correction; FDR families; trial sets; diagnostics and flags; sensitivity analyses; deviations policy. **Add no new analyses beyond plan.md.**
>
> Include a short "what R2 does not do tonight" section: plasmode, MIMIC, cohort redefinitions beyond must-fix. Don't commit. Reply with any ambiguity you resolved and how.

### 7.2 PA: protocol auditor (23:30–00:00)

> Adversarially audit `docs/r2/PROTOCOL_R2.md` against `plan.md` and `docs/v2_planning/LESSONS_FROM_V1.md`. Check:
> - every version 1 lesson is addressed;
> - each hypothesis has an unambiguous test;
> - the leakage rules are complete (same quantity, derived, code family, |ρ| ≥ 0.80);
> - the gap-closure formula is well defined when the denominator is ≤ 0, and the protocol says what happens then;
> - no analysis depends on results not yet computed;
> - the deadline is feasible.
>
> Write `docs/r2/AUDIT_PROTOCOL_R2.md` with BLOCKING / SHOULD-FIX / NOTE items. Don't edit the protocol. Reply with the blocking items.

### 7.3 Q-A and Q-B: blind quality re-auditors (run twice, independently; 22:30–23:45)

> You are an independent auditor of target trial emulation quality. Read ONLY:
> - `/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/labels/picot_blind.md`;
> - `scripts/trial_specs.py`, `scripts/build_trial_cohort.py`, `scripts/trial_common.py`;
> - plan.md §4.4 (the rubric).
>
> Don't read any results, audit folders, docs/v1x–v21, paper drafts, existing quality ratings (`docs/v19/*`) or the other auditor's file. Web access, if available, is only for checking RCT publications.
>
> For each of the 38 trials, score each rubric item as good / moderate / poor with one line of evidence (the code location or publication), assign a tier A–D by the plan's rules, and flag:
> - any **must-fix** cohort-definition error, with the exact proposed spec edit;
> - any benchmark (HR, CI, ITT) that disagrees with the publication.
>
> Run `umask 077`, then write a JSON list to `/mnt/raid0/rbc58/ecg-tte/audits/claude-r2/quality/quality_<A|B>.json`. Reply with the tier counts, must-fix list and benchmark flags.

**Coordinator adjudication:** κ for the tiers; resolve disagreements by the rubric text; write `docs/r2/QUALITY_R2.{json,md}` (the primary set = tiers A–C; must-fix decisions; benchmark flags); commit. Must-fix edits go into `scripts/r2/specs_r2.py`, never into `trial_specs.py`. Rebuild only if it can finish by 01:30, using the `scripts/v18/build_queue.sh` pattern with outputs under `audits/claude-r2/cohorts/`.

### 7.4 K: leakage map (00:00–00:45)

> Build the R2 leakage map per `docs/r2/PROTOCOL_R2.md` §(leakage) and plan.md §4.3. Read the protocol, `scripts/v16/v16_engine.py` (`heldout_matrix`, `VARS`), the `Trial` class in `scripts/v13_common.py`, the `roles.json` files, and `docs/v2_planning/LESSONS_FROM_V1.md`.
>
> For every scenario × representation, list every held-out item to mask, with its reason (same quantity / derived / code family / data-driven |ρ| ≥ 0.80). Compute the data-driven correlations as pooled aggregate Spearman ρ across trials; write only aggregate tables.
>
> Write `scripts/r2/leakage_map.json` (machine-readable, the only source the grid uses) and `docs/r2/LEAKAGE_MAP.md`. **Gate:** confirm that the version 1 defects are caught (echo EF and eGFR for S3; the medications item for S2b; the coded-record items for CLMBR-T, flags and notes). Report the gate result. Outputs go to `audits/claude-r2/leakage/`. Don't commit.

### 7.5 B: core grid (launch about 00:45; NOTES patch about 03:30)

> Implement and run the R2 core grid. Read `docs/r2/PROTOCOL_R2.md`, `plan.md` §3–4, `docs/r2/QUALITY_R2.json`, `scripts/r2/leakage_map.json`, `scripts/v21/paper2_grid.py` (reuse its structure, `flagscv` cross-validated tuning, summary helpers) and `scripts/v20/sens_primary32.py`.
>
> Write `scripts/r2/r2_grid.py` with `run`, `gate`, `summarize` and `patch-notes` subcommands:
> - scenarios S0, S1, S2a, S2b, S3 × arms (base, ECG, CLMBR, ECG+CLMBR, placebos, CLMBR32, representation-only) × estimators (match02, overlap, m13);
> - cross-validated penalty per cell;
> - all 38 trials; report both the R2 primary set and all 38.
>
> **Gate:** with C fixed at 1 and the version 1 masking, S1/S2b/S3 × base/ECG/shufECG under match02 must reproduce `audits/claude-v20-sens-primary32` exactly. If not, stop and report.
>
> **Summarize** (masking strictly from `leakage_map.json`): every endpoint in plan.md §4.2, H1–H6 with Holm correction, the full-sweep BH-FDR, per-trial and per-domain aggregates, the diagnostics (retention, effective sample size, cross-fitted treatment C statistic, near-instrument flags) and label/area/tier subsets. Also write the JSON-ready aggregate tables the explorer needs, to `audits/claude-r2/core/explorer_data/`.
>
> When `audits/claude-r2/notes/READY` exists, run `patch-notes`: add the NOTES, ECG+NOTES, CLMBR+NOTES, ALL and shufNOTES arms to every scenario and estimator, then re-summarize.
>
> Rules: at most 48 workers, after checking `uptime`; long jobs in tmux `r2`; outputs go to `audits/claude-r2/core/` (`umask 077`); aggregates only, suppression of 1–10, privacy scan before finishing; don't commit. Write `docs/r2/R2_CORE_RESULTS.md`: a plain-language verdict for H1–H6 first, then tables, every number traceable to a CSV. Report the gate result and the headline numbers.

### 7.6 N: clinical-note embeddings (22:30 → READY, ideally by 03:30)

> Build clinical-note embeddings with Qwen3-Embedding-8B exactly as in `plan.md` §5. Read `plan.md` §5, `CLAUDE.md`, `docs/DATA_ACCESS_MAP.md`, `scripts/select_cohort_ecgs.py` (MRN normalisation), `scripts/trial_specs.py` (arm keywords), the `roles.json` exposure features, and `docs/v18/CLMBR_LEAKAGE.md` (window convention).
>
> **Privacy is absolute:**
> - never print, log, summarize or write note text outside restricted caches under `audits/claude-r2/notes/` (`umask 077`);
> - write no patient-level rows to stdout;
> - no external APIs: download only the public model weights, then go offline (`HF_HUB_OFFLINE=1`, `VLLM_NO_USAGE_STATS=1`, `DO_NOT_TRACK=1`).
>
> **Steps:**
> 1. Inventory both note sources (counts by year and note type only). Map MRNs to the 38 trial cohorts (`audits/claude-<trial>-cohort-v1/restricted_cohort.parquet`; find the cohort directory for each trial via `scripts/v13_common.py` paths). Compute coverage, and note and token counts, in each trial window.
> 2. Choose K and T to fit about 3 GPU-hours on the GPUs that are free when you start (check `nvidia-smi`; only GPUs with <1 GB used; at most 4). Log the choice.
> 3. Set up `/mnt/raid0/rbc58/ecg-tte/software/qwen-env/` and download `Qwen/Qwen3-Embedding-8B` to `/mnt/raid0/rbc58/models/qwen3-embedding-8b/`. Run a smoke test on 100 notes: check the embedding dimension, and that norms and timing are reasonable.
> 4. Apply exposure-term masking per trial, embed each unique `note_id` once (resumable, sharded, in tmux `r2` windows, one per GPU), aggregate per trial × patient (mean), reduce to 64 PCs within each trial, and add the missing indicator.
> 5. Write the outputs and `docs/r2/NOTES_EMBEDDINGS.md`, then touch `audits/claude-r2/notes/READY`.
> 6. If time remains, run the sensitivity variants in plan.md §5, in order.
>
> Report: coverage per trial (suppressed), K and T, masking rates, GPU-hours, deviations. Don't commit.

### 7.7 E: reviewer (about 04:30)

> Adversarially review R2: `docs/r2/PROTOCOL_R2.md`, `LEAKAGE_MAP.md`, `QUALITY_R2.md`, `R2_CORE_RESULTS.md`, `NOTES_EMBEDDINGS.md`, `scripts/r2/*` and `audits/claude-r2/`. Check:
> 1. **Protocol compliance:** no undeclared changes.
> 2. **Leakage:** masking applied from the JSON; the version 1 defects are fixed; notes windows exclude the index day; exposure masking works (aggregate rates); near-instrument flags.
> 3. **Gates:** genuinely passed.
> 4. **Independent recomputation** from the restricted cells of H1, H3, H5 (gap closure) and H6 (benchmark-permutation P).
> 5. **Every number** in the results doc traces to a file.
> 6. **Privacy:** no note text anywhere outside `notes/` restricted caches; no counts of 1–10; nothing restricted staged in git; no patient keys in `explorer_data/`.
> 7. **Statistics:** Holm/BH applied as declared; one- vs two-sided tests; denominator handling for gap closure.
>
> Write `docs/r2/AUDIT_R2.md` (BLOCKING / SHOULD-FIX / NOTE, with evidence). Don't edit code. Reply with the blocking items.

### 7.8 H: interactive explorer (about 05:30–07:00)

> Build the R2 interactive explorer exactly as in `plan.md` §6. Read plan.md §6, `scripts/build_lab_deck.py` (explorer patterns, style), `docs/paper/figures_paper2/index.html` (style), `docs/r2/R2_CORE_RESULTS.md`, `docs/r2/AUDIT_R2.md`, `docs/r2/LEAKAGE_MAP.md`, `docs/r2/NOTES_EMBEDDINGS.md` and `audits/claude-r2/core/explorer_data/`.
>
> Write `scripts/r2/build_explorer.py`. It reads only aggregate files and produces one self-contained `docs/r2/explorer/index.html` (no CDN; vanilla JS; inline SVG; data embedded as JSON), copied to `audits/claude-r2/explorer.html`.
>
> If the NOTES arms aren't ready, show a "notes pending" banner and hide those controls. Verify it headlessly: Playwright from the session scratchpad (`handoff.md` §2 env vars); screenshot every tab and check the controls change the panels, with no console errors.
>
> Aggregates only; suppress 1–10; no patient keys. Don't commit. Report the file paths, a one-line description of each tab, and any known limitations.

### 7.9 W: results write-up (about 05:30–07:00, in parallel with H)

> Write `docs/r2/R2_RESULTS.md`, a short results report (not a manuscript), about 1,500 words:
> - what changed from version 1 and why (from plan.md §2);
> - the R2 primary set;
> - H1–H6 results with estimates, CIs, P and q;
> - where each representation works best (scenarios, domains, trial labels, areas) for balance and for emulation;
> - the substitution findings;
> - notes coverage and caveats, including "notes may contain the value", decision leakage and near-instrument flags;
> - what didn't hold;
> - open decisions for the user and PI.
>
> Every number must come from `docs/r2/R2_CORE_RESULTS.md`, `NOTES_EMBEDDINGS.md` or the `audits/claude-r2/` CSVs; mark anything unverified `[CHECK]`. Don't commit.

### 7.10 F: final audit (about 07:00–07:45)

> Audit `docs/r2/R2_RESULTS.md` and `docs/r2/explorer/index.html` claim by claim against the sources, as in `docs/paper/AUDIT_MANUSCRIPT_2026-10-01.md` (MATCH / MISMATCH / UNSUPPORTED, with fixes). Spot-check at least 30 explorer values against the CSVs. Check privacy: no note text, no patient keys, no counts of 1–10. Write `docs/r2/AUDIT_R2_FINAL.md`, apply text fixes to R2_RESULTS.md, and list explorer fixes for H to apply (or apply them yourself if they are data-file fixes in `build_explorer.py`'s inputs). Don't commit.

---

## 8. Deliverables at 08:00

| What | Where |
|---|---|
| **Interactive explorer** | `docs/r2/explorer/index.html` (copy: `audits/claude-r2/explorer.html`) |
| Results report | `docs/r2/R2_RESULTS.md` |
| Frozen protocol and its audit | `docs/r2/PROTOCOL_R2.md`, `docs/r2/AUDIT_PROTOCOL_R2.md` |
| Quality re-audit | `docs/r2/QUALITY_R2.{json,md}` |
| Leakage map | `docs/r2/LEAKAGE_MAP.md`, `scripts/r2/leakage_map.json` |
| Notes embeddings report | `docs/r2/NOTES_EMBEDDINGS.md` |
| Reviewer and final audits | `docs/r2/AUDIT_R2.md`, `docs/r2/AUDIT_R2_FINAL.md` |
| Version 1 freeze | tag `trace-v1`, `docs/r2/V1_MANIFEST.md` |
| Overnight log and summary | `audits/claude-r2/STATUS.md` (summary at top) |

Everything is committed locally to `main` except restricted outputs; nothing is pushed.

## 9. Open items for the user after the run (not blockers tonight)

- Confirm with the PI that clinical-note use is covered by the IRB (§5).
- Decide whether R2 replaces paper2 or feeds a separate paper.
- Clinician review of the trial labels and of the R2 quality tiers.
- Whether to re-run plasmode and MIMIC under R2 rules (not done tonight).
