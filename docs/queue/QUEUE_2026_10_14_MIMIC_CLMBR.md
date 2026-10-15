# MIMIC-IV external validation: clean up and add CLMBR-T (queued 2026-10-14)

You are running unattended in tmux, in parallel with the deck jobs (`s31q` → `deck2q` → `fig2dq`).

**Read first:**
- `CLAUDE.md`, `handoff.md` §1 and `pipeline.md` (2026-10-14 update);
- `docs/v21/MIMIC_PAPER2.md`, `docs/v20/MIMIC_REPLICATION.md`, `docs/v20/MIMIC_REPLICATION_PLAN.md`, `docs/PROTOCOL_V1_5_EXTERNAL.md` (MIMIC sections);
- `scripts/v20/mimic_replication.py`, `scripts/v21/mimic_cvd5.py`;
- the Yale CLMBR-T pipeline: `scripts/run_trial_pipeline.sh`, `scripts/build_comet_meds.py`, `scripts/encode_comet_clmbr.py`, `scripts/v13_common.py` (`clm_pc`: per-trial PCA, 64 PCs).

**The user's request:** "clean up and add the CLMBR for MIMIC for external validation".

## Rules

**Access**
- Write only under `/mnt/raid0/rbc58` and this repo (code and docs).
- MIMIC (staged tables under `audits/claude-v15-mimic-shared/stage/` and any raw source), the CLMBR-T checkpoint `/mnt/raid0/eo287/clmbr` and the OMOP vocabulary `/mnt/raid0/rbc58/mosaic/mapping/` are **read-only**.

**Outputs and privacy**
- New outputs go to `/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014/` (`umask 077`).
- Aggregates only. Suppress counts of 1–10, including derivable ones.
- Never print patient rows, subject_ids, hadm_ids or dates. Never open note text.
- Never commit CSV, parquet or other restricted files. Never push.

**Compute**
- **GPU:** check `nvidia-smi` and use a free GPU (currently GPU 3). **Never use GPU 7.**
- Python: `/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python`. For CLMBR-T inference, use the mosaic env exactly as `run_trial_pipeline.sh` does (`$MOS/bin/python` with its `LD_PRELOAD`).

**Files**
- Don't edit `paper.md`, `paper2.md`, `table1_picot.md`, any `.docx`, the deck, its builders, or the Figure 2 scripts. The deck jobs own those.
- Commit only your own paths (`git add <paths>`, never `-a`). If the git index is locked by another job, wait and retry.

**Logging**
- One line per step to `audits/claude-mimic-clmbr-20261014/STATUS.md`.

## Step 0: gate, before anything new

Re-run the existing MIMIC PS-CVD5 ± ECG ± permuted-ECG analysis (`scripts/v21/mimic_cvd5.py`, via import). It must reproduce `docs/v21/MIMIC_PAPER2.md` **exactly**:
- 6.6% (2.3–12.8), 6/7 trials lower, sign-flip P = .016;
- % < 0.1 45.6 → 51.6;
- permuted ECG −3.1%.

If it doesn't, stop and log why.

## Step 1: MIMIC → MEDS, matching the Yale CLMBR-T input (time-box: about 3 hours)

1. **Build a MEDS extract** for the patients in the 7 cardiovascular trials + PEPTIC, from the staged MIMIC hosp tables:
   - `diagnoses_icd` → ICD9CM / ICD10CM;
   - `procedures_icd` → ICD9Proc / ICD10PCS;
   - `prescriptions` / `emar` → NDC, mapped to RxNorm through `CONCEPT_RELATIONSHIP` "Maps to";
   - `labevents` → lab codes: LOINC where `d_labitems` has it, otherwise the MIMIC itemid code;
   - `admissions` / `transfers` → visit codes;
   - birth and sex as static events, the same way `build_comet_meds.py` handles them.
2. **Use the code strings the CLMBR-T dictionary expects.** Check them against `dictionary.msgpack`, the same way `build_comet_meds.py` / `encode_comet_clmbr.py` format Yale codes.
3. **Code-only mode** (`--numeric-mode code-only`, `--max-tokens 4096`), as at Yale.
4. **No leakage past time zero:**
   - Include only events **strictly before time zero**.
   - MIMIC diagnoses and procedures from an admission have no reliable timestamp. Assign them to that admission's discharge time, and **exclude all codes from the index admission**. This matches the MIMIC PS-CVD5 analog, which uses earlier admissions only.
   - Labs and medication orders from the index admission count only if they are timestamped before time zero. Exclude the exposure drugs and the gate code itself, as at Yale.
   - Record the rule in the doc.
5. **Vocabulary coverage gate** (report aggregates):
   - share of events whose code is in the CLMBR-T dictionary;
   - median (IQR) in-vocabulary tokens per patient;
   - share of patients with no prior coded history (birth/sex only).
   - Compare each with the Yale cohorts (the same statistics from an existing Yale MEDS extract).
   - **Stop rule:** if fewer than 50% of events are in the dictionary, or more than 50% of analysed patients have no prior coded history, **don't run inference**. Write a feasibility memo (Step 4) explaining why CLMBR-T isn't usable in MIMIC, and finish.

## Step 2: CLMBR-T embeddings

1. **Run a small inference test** (about 100 patients), then the full set, with the same checkpoint, runtime and settings as Yale. The model and runtime hashes must match the Yale `manifest.json`.
2. **Quality checks:** finite vectors; one embedding per patient–index; the output manifest has hashes.
3. **Per-trial PCA, 64 PCs,** as in `v13_common.clm_pc`.
4. **Patients with no prior history** keep their (demographics-only) embedding, as at Yale. Report the share; don't drop them.

## Step 3: analysis (same design as the existing MIMIC PS-CVD5 analysis)

1. **Population:** the same 7 cardiovascular trials + the PEPTIC negative control.
2. **Arms:**
   - PS-CVD5 analog alone;
   - + ECG; + CLMBR-T; + ECG + CLMBR-T;
   - + permuted ECG; + permuted CLMBR-T.
3. **Same as now:** fixed C = 1 ridge (L2) logistic regression; 1:1 greedy nearest neighbour, caliper 0.2 SD of the logit, without replacement; < 11 pairs = failed cell.
4. **Held-out panel:** the same as the existing MIMIC analysis.
5. **Leakage, as in `pipeline.md` §6:** for the CLMBR-T arms, mask any held-out item that is derivable from codes in CLMBR-T's input. A code-only model sees which labs were ordered and which diagnoses were coded. Document the mask list.
6. **Endpoints:**
   - relative reduction in mean |SMD| (bootstrap over trials, 4,000 resamples, seed 20261001);
   - trials lower;
   - exact one-sided sign-flip P;
   - % |SMD| < 0.1;
   - |Δ log HR| vs the RCTs;
   - PEPTIC HR.
7. **Contrasts:**
   - + CLMBR-T vs PS-CVD5;
   - + ECG + CLMBR-T vs PS-CVD5;
   - + ECG + CLMBR-T vs + CLMBR-T, which asks whether the ECG still adds once CLMBR-T is in;
   - each placebo vs its real arm.
8. **Retention / overlap:**
   - **Check** retention as in the PROTECT AF audit (`docs/audits_balance/AUDIT_PROTECT_AF_RICH_PS.md`). Use the overlap rule (≥ 30% of the smaller arm matched or ≥ 50 pairs) as a cell-validity check.
   - **Report** the number of failed cells.
   - **Never print** n_pairs, retention or ESS per trial.
9. **Compare with Yale.** Put the MIMIC results next to the Yale s31 values (`docs/s31/S31_RESULTS.md`, when the s31 job has written it) for the same contrasts.

## Step 4: clean up

1. **Write one consolidated doc,** `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md`, that supersedes the scattered MIMIC notes (v1.5, v20, v21) for the current design. Cover:
   - the cohorts and time zero;
   - trials and benchmarks;
   - covariates (PS-CVD5 analog);
   - the ECG and CLMBR-T inputs (MEDS build, coverage, leakage rule);
   - the held-out panel and masks;
   - results (ECG and CLMBR-T arms; agreement; PEPTIC);
   - sensitivities (the existing design-detail ones: any-diabetes, index-admission codes, index-day ECG);
   - limitations (hospital-only history; 12-month horizon; 7 trials);
   - a short "history" section linking the older docs.
2. **Add a one-line pointer** at the top of each older MIMIC doc: "Superseded for the current design by `docs/mimic/MIMIC_EXTERNAL_VALIDATION.md`". Don't delete or rewrite them.
3. **Add a single entry-point script,** `scripts/mimic/run_mimic_external.py`. It imports the existing modules (don't modify `scripts/v20/*` or `scripts/v21/*`) and reproduces every number in the new doc from the restricted outputs, with gates.
4. **Update `pipeline.md`:**
   - the External replication row becomes "MIMIC-IV 3.1 (ECG and CLMBR-T; no echo)";
   - the MIMIC-IV row of the analysis table lists the new arms;
   - add a deviations-log line: "2026-10-14: CLMBR-T added to the MIMIC-IV external validation (code-only, prior admissions only; added after the Yale results; reported as a comparison arm, as at Yale)".
   - If the stop rule fired, record that instead.

## Step 5: independent verification (a fresh subagent that built nothing)

The verifier checks:
- the Step 0 gate;
- that no event at or after time zero, and no index-admission diagnosis or procedure code, entered the MEDS input (aggregate checks only);
- that the model and runtime hashes match Yale;
- at least 15 headline numbers recomputed with independent code from the restricted outputs;
- the leakage masks;
- a privacy scan of every committed file.

Fix BLOCKING issues and re-verify, up to 3 rounds. Report: `docs/mimic/VERIFY_MIMIC_CLMBR.md`.

## Step 6: commit and summary

1. **Commit locally:** the code, the docs, the `pipeline.md` update and the verify report. No restricted files. Don't push.
2. **Write the summary** at the top of the status log and copy it to `docs/queue/QUEUE_2026_10_14_MIMIC_CLMBR_RESULTS.md` (commit). Cover:
   - feasibility and coverage vs Yale;
   - the headline MIMIC numbers for + ECG, + CLMBR-T and + both vs PS-CVD5, next to Yale;
   - whether the ECG still adds once CLMBR-T is in;
   - agreement and PEPTIC;
   - the verification verdict;
   - one or two sentences ready for the deck's MIMIC slide. **Don't edit the deck.**
