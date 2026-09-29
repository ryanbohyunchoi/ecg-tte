# v1.9 sensitivity analysis: adherence / on-treatment and run-in estimands (plan)

Status: **exploratory sensitivity analysis**, requested 2026-09-29. This plan is written and committed before any
sensitivity estimate is computed. Deviations found during implementation are dated and logged at the end, before
results are summarised. Results will be in `docs/v19/SENS_ADHERENCE.md`; code in `scripts/v19/sens_adherence.py`;
restricted and aggregate outputs in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v19-sens-adherence/` (umask 077).

## Question

Do the conclusions of the current 38-trial analysis (ECG embedding added to a thin PS; RCT agreement) change when
the intention-to-treat (ITT) estimand is replaced by on-treatment (per-protocol) or run-in estimands, which are
closer to what several RCTs estimated?

## Setting (identical to the current primary analysis)

- **Trials.** The 38 trials of `scripts/v18/v18_af_confirm.py` / `scripts/v18/v18_embed_compare.py`
  (v1.6 18 + v1.7 15 + v1.8 AF 5, in that order; index i sets the halves seed 16060 + i).
- **PS designs.** P1 = demographics (`T.demo`); P5 = P1 + hypertension_v11, t2d, cad_ihd, atrial_fibrillation,
  HF (hf_any_365, else elx_chf) = `v18_clmbr.designs(T, n, P5DX)`.
- **Arms.** base | +ECG32 (`T.ecg_pc`) | +permuted ECG32 (`T.ecg_pc[T.shuffle_perm]`) | unmatched (crude, once).
- **Matching.** `E.run_cell(T, X, rows, estimator=("match", 0.2, 1))`: L2 logistic PS (C = 1), 1:1 greedy caliper
  0.2 SD of the logit, anchored on the smaller arm. The matched set of each cell is captured from the engine's
  matcher (`S8._LAST`); pair = anchor. **The sensitivity estimands are computed on exactly these matched sets.**
- **Endpoint, horizon, censoring.** Primary outcome at the trial horizon, `T.y_t`, `T.y_e`, `T.y_ok`
  (v13_common.outcomes), i.e. identical to the primary analysis. The only change is the additional censoring or
  landmark defined below.
- **Halves.** Full cohort is primary; split halves A / B (s1_ladder.halves) are reported as a stability check.

**Reproduction gate.** Before any sensitivity estimate is used, the ITT log HR, SE, n and n_pairs of every
(trial, half, PS, arm) cell recomputed by this script must equal `claude-v18-embed-compare/results.csv` (rungs P1 /
P5 / none) with maximum absolute deviation 0 (tolerance 1e-12). If not, stop and investigate.

## Sensitivity estimands (v1.3 amendment II2 / II3 rules, reused from `scripts/v13_design.py`)

Order-derived deviation times are those of `scripts/v13_extract.py` (`claude-<trial>-outcomes-v13/
restricted_outcomes_v13.parquet`; drug orders matched by arm keyword, orders on or after index, no days-supply):

- `pp_switch`: first order of the other arm's study drug after index;
- `pp_stop{G}`: min(switch, discontinuation), discontinuation = first own-drug order followed by no further
  own-drug order within G days, date = that order + G (index date counts as an order);
- `repeat_90`: at least one order of the assigned drug in (index, index + 90].

Estimands, each on the matched set of every cell:

- **(a) pp_ipcw_G**, G = 365 (base), 180, 730: follow-up censored at `pp_stop{G}`; stabilised IPCW from a pooled
  logistic model of deviation per 90-day interval on treatment, interval dummies (capped at 12) and the arm's own PS
  covariates (P1 / P5 [+ ECG32 or permuted ECG32]); numerator model = treatment + interval; weights truncated at the
  99th percentile; weighted start–stop Cox, robust SE clustered on pair (`v13_design.ipcw` unchanged).
  Unmatched arm: IPCW covariates = P1 demographics (it has no PS; logged as a rule of this plan).
- **(b) pp_ipcw_switch**: censored at `pp_switch` only, same IPCW.
- **(c) pp_naive_G / pp_naive_switch**: same censoring, no weights (reference).
- **(d) runin90**: landmark at day 90. Keep pairs in which both members have follow-up > 90 d (alive, event-free,
  uncensored at day 90) and `repeat_90` = 1; the clock restarts at day 90 (t − 90), horizon otherwise unchanged
  (events up to the original horizon). Unmatched: individual-level rule. Retention = kept / analysed matched
  patients (aggregate %).

Estimability: an estimate is NaN when the Cox fit has < 5 events or no events in one arm (v13_common.cox), when the
IPCW model has < 5 deviation events (v13_design.ipcw), or when the run-in sample has ≤ 50 patients. Paired
cross-trial statistics use the trials in which both compared arms are estimable (count reported).

### Applicability (v1.3 rules)

- **Not applicable (procedure arm; no drug-order adherence):** CABANA (catheter ablation vs AAD; `proc_vs_drug`),
  LAAOS III (surgical LAA occlusion vs cardiac surgery; `procedure`), PROTECT AF (LAAO vs warfarin;
  `arm0_procedure`), RAFT-AF (ablation vs rate control; `arm0_procedure`). Per-protocol and run-in are not defined
  for a one-time procedure arm (v13_extract skips them; the v1.3 amendment excludes PARTNER for the same reason).
  These 4 trials enter only the ITT column; sensitivity sets have 34 trials.
- **Sequential / switch designs** (`switch_seq`): PARADIGM-HF-seq (switch ACEi → ARNI; deviation in the comparator =
  ARNI order), FRAIL-AF (switch warfarin → DOAC; deviation in the switch arm includes a warfarin order after
  the index day), and the add-on rhythm-control designs EAST-AFNET 4, AFFIRM, AF-CHF (`add_on`: rate-control drugs
  are allowed in the AAD arm, so only an AAD order censors the rate-control arm; discontinuation of the assigned
  drug class censors either arm). Rules exactly as in `v13_extract` / `v13_design`; each such trial is flagged in
  the per-trial table.

## Reported statistics

Per estimand × PS × arm contrast, over the applicable trials (and for ITT also on all 38):

- mean |Δlog HR| vs RCT (base, ECG, permuted ECG, unmatched), number of trials with ECG closer than base;
- consistency: % of trials with |z| < 1.96, z = (log HR − RCT) / sqrt(se² + se_RCT²);
- exact one-sided sign-flip p (`v17_confirm.signflip_1s`) of d = |Δ|_base − |Δ|_ECG (ECG better), and of
  |Δ|_shufECG − |Δ|_ECG (ECG vs permuted ECG);
- benchmark-shuffle p within set (the set's own k (rb, rs) pairs permuted jointly across trials; 20,000 draws,
  `np.random.default_rng(0)`; statistic mean(|le − q| − |lb − q|); p = P(null ≤ observed));
- comparator-clustered sign-flip p (clusters of `docs/v17/trial_selection.json`, cluster-mean d);
- halves A / B sign-flip p;
- side-by-side with the ITT results computed by the same code on the same trial set;
- per-trial table (HR base / ECG / permuted / unmatched per estimand, design flags), and % of matched patients
  retained at the landmark (aggregate %, never counts 1–10).

**Verdict rule (plain language).** Conclusions "change" if, for P1 or P5, an on-treatment/run-in estimand gives a
different qualitative answer from ITT on either (i) ECG vs base sign-flip p crossing 0.05, or (ii) benchmark-shuffle
p crossing 0.05 (i.e. trial-specific gain appearing / disappearing). All analyses are exploratory; no multiplicity
correction is used to claim a finding, and any "positive" cell must also beat permuted ECG and the benchmark shuffle.

## Data rules

Read mounted data; write only under `/mnt/raid0/rbc58` and `/home/rbc58/github`. Aggregates only; patient counts
1–10 suppressed in every written file; no patient rows printed. Only code and md are committed.

## Deviation log

(dated entries added during implementation, before results are summarised)
