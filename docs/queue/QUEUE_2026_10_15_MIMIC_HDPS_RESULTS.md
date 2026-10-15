# Results: MIMIC-IV hdPS on the AI-EHR input window (queue `QUEUE_2026_10_15_MIMIC_HDPS.md`, run 2026-10-15)

Full doc: `docs/mimic/MIMIC_HDPS_WINDOW.md`. Audit: `docs/mimic/AUDIT_MIMIC_HDPS.md` (**PASS**; no BLOCKING findings; 2 SHOULD-FIX items fixed). Code: `scripts/mimic/hdps_window.py`. Outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-hdps-20261015/` (`summary/summary.json`, `summary/tables.md`, `STATUS.md`).

All numbers below: 7 cardiovascular trials, all analysed patients, 22 items (utilisation excluded for every arm). They are relative reductions in mean |SMD|, with 95% trial-bootstrap CIs (4,000 resamples, seed 20261001), trials lower, and exact sign-flip P.

## Gates and leakage

- **Gate 1: PASS (max |Δ| = 0).** Under the original window, the new module rebuilds every trial's hdPS candidate panel exactly. It reproduces `TrialData`'s levels and every v20 demo / hdPS200 base, + ECG and + permuted-ECG cell, in both populations.
- **Gate 2: PASS (max |Δ| = 0).** All 6 PS-CVD5 arms equal `results_prior`. The summary code reproduces the 10 published PS-CVD5 contrasts exactly.
- **Leakage (hdPS-prior candidate levels, 8.73 M events):** all pass.
  - 0 events at or after the index admission time, and 0 at or after t0;
  - 0 index-admission dx / px codes;
  - 0 exposure-drug features.
  - **Index ED stay kept** (as for AI-EHR): 18.2% of input events, almost all ED labs. For 36.2% of analysed patients it is the whole candidate input.
  - **No hdPS input:** 12.3% of patients have no candidate-level input (v20: 0.6%). Candidate levels per trial: median 482.5 (v20: 716).
  - The dx flags follow the PS-CVD5 rule (earlier admissions). 13 patients (0.03%) have an earlier admission discharged after the cut.
- **Correction to the premise.** The v20 hdPS read index-admission *diagnoses* only in SOAP II, ELITE II and PEPTIC; the 5 v1.5 trials were already audit-fixed. In all 8 trials, though, it read the index stay's pre-t0 orders and lab-measured flags: 49% of its input events were at or after the index admission time.
- **Masks:** no held-out item in blocks A–C reaches |ρ| 0.5 with an hdPS-prior input (max pooled 0.32). Utilisation (block D) is derivable from the hdPS inputs (prior admissions |ρ| 0.73, and structurally implied by earlier-admission codes), so excluding it is right. The 26-item hdPS numbers are a sensitivity only.

## Mean |SMD| (22 items)

| | Base | + AI-ECG | + AI-EHR | + AI-ECG + AI-EHR | + permuted AI-ECG | + permuted AI-EHR |
|---|---|---|---|---|---|---|
| Unmatched | 0.169 | | | | | |
| PS-Demo | 0.166 | 0.147 | 0.147 | 0.131 | 0.170 | 0.175 |
| PS-CVD5 | 0.158 | 0.147 | 0.146 | 0.129 | 0.161 | 0.160 |
| **hdPS-prior** | **0.140** | 0.124 | 0.141 | 0.126 | 0.143 | 0.145 |
| hdPS200 (v20; sensitivity) | 0.113 | 0.105 | 0.110 | 0.095 | 0.115 | 0.117 |

## Contrasts vs hdPS-prior

| Contrast | Rel. red. (95% CI) | Lower; P |
|---|---|---|
| hdPS-prior vs PS-CVD5 (two-sided) | **11.7% (7.1 to 16.8)** | 7/7; .016 |
| + AI-ECG vs hdPS-prior | **10.8% (7.2 to 15.7)** | 7/7; .008 |
| + AI-EHR vs hdPS-prior | **−1.2% (−7.8 to 5.8)** | 4/7; .62 |
| + AI-ECG + AI-EHR vs hdPS-prior | **10.0% (4.2 to 14.3)** | 6/7; .016 |
| + AI-ECG vs + permuted AI-ECG | 12.9% (9.4 to 16.6) | 7/7; .008 |
| + AI-EHR vs + permuted AI-EHR | 2.9% (−3.1 to 9.2) | 5/7; .20 |
| + AI-ECG + AI-EHR vs + AI-EHR | 11.0% (3.7 to 18.2) | 6/7; .023 |
| + AI-ECG + AI-EHR vs + AI-ECG | −1.0% (−11.8 to 6.0) | 4/7; .58 |
| PS-Demo + AI-ECG vs hdPS-prior (two-sided) | −5.4% (−12.1 to 1.0) | 2/7; .23 |
| PS-Demo + AI-EHR vs hdPS-prior (two-sided) | −5.6% (−13.5 to 1.8) | 3/7; .30 |
| PS-Demo + both vs hdPS-prior (two-sided) | 5.8% (0.2 to 10.9) | 6/7; .11 |
| PS-CVD5 + AI-ECG / + AI-EHR / + both vs hdPS-prior (two-sided) | −5.2% / −4.5% / +7.9% | 2/7, 1/7, 7/7 |

**hdPS200 (sensitivity):**
- hdPS200 vs PS-CVD5: 28.7%; hdPS-prior is 24.0% worse than hdPS200. About 60% of the v20 hdPS's advantage came from the index stay.
- On hdPS200: + AI-ECG 6.9% (−1.5 to 16.7), 4/7; + AI-EHR 2.6%, 5/7; + both 16.0% (8.6 to 24.5), 6/7.
- Every Demo / PS-CVD5 + AI arm is 14–31% worse than hdPS200.

## Do the AI arms add on top of hdPS-prior?

- **The AI-ECG adds:** 10.8%, 7/7, and 12.9% vs its placebo. That is the same size as on PS-CVD5 or PS-Demo, and it holds with all 8 trials (10.7%, 8/8) and without the near-separated trials (11.8%, 5/5).
- **The AI-EHR does not add:** −1.2%; 2.9% vs placebo. Without the near-separated trials it is 3.4% (3/4), with the placebo contrast at 9.0% (4/4).
- **On a demographic base, either AI representation brings PS-Demo to about the level of hdPS-prior** (−5.4% and −5.6%; CIs include 0). Both together are slightly better than hdPS-prior (+5.8%, 6/7).

## Agreement and PEPTIC

- **Mean |Δ log HR|:** PS-CVD5 0.344 → hdPS-prior 0.239 (7/7 closer) → + AI-ECG 0.187 → + AI-EHR 0.240 → + both 0.213. Benchmark-permutation P: .83, .20, .97 and .41. All of this is attenuation, not trial-specific correction.
- **PEPTIC HR** (RCT 1.05): PS-CVD5 1.51 → hdPS-prior 1.20 (1.08–1.35); + AI-ECG 1.15 (1.02–1.28); + AI-EHR 1.28 (1.14–1.43); + both 1.18 (1.05–1.32). hdPS200 (index stay included) is 0.93.

## Cell validity

- 0 failed cells (< 11 pairs) and 0 overlap-invalid cells out of 192.
- **Near-separation:** cells with > 10% of PS values outside [0.01, 0.99]:
  - hdPS-prior: 12 of 48 cells (3 of 7 trials; max 21%);
  - hdPS200: 24 of 48 (4 of 7; max 29%);
  - PS-CVD5 and PS-Demo: none.
- Median in-sample C: hdPS-prior 0.740 / 0.781 / 0.775 / 0.808 (base / + AI-ECG / + AI-EHR / + both).

## Audit verdict

**PASS** (independent subagent, own code). It checked:
- both gates;
- the leakage of 4 trials' panels, rebuilt independently (identical);
- 2,128 field-level recomputations against `summary.json` (no difference > 1e-9);
- masks, cell validity and privacy.

**Fixes applied:**
- S1: the leakage claim is now scoped to the candidate levels; the dx-flag rule is disclosed.
- S2: 4 benchmark-permutation P values were re-rounded.
- Notes N1–N7 were applied.
- Round 2 (the auditor verified the fixes): PASS. Its two last wording notes were applied.

## Not done / for the interactive session

- Figures, `paper*.md`, `table1_picot.md`, the deck and `scripts/figures/*` were not touched. The numbers for the figure are in `summary/summary.json`: keys `arms|primary7|22|<arm>` and `contrasts|primary7|22|<label>`.
- The no-index-day-ECG population was not run for the new arms.
