# Independent audit: MIMIC-IV hdPS on the AI-EHR input window (2026-10-15)

Auditor: a fresh agent that built nothing in this analysis. Under audit: `docs/mimic/MIMIC_HDPS_WINDOW.md`, `scripts/mimic/hdps_window.py` and the outputs in `/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-hdps-20261015/` (read only). My scripts and restricted check files are in `/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-hdps-audit-20261015/` (umask 077, not committed): `a1_gates.py`, `a2_leakage.py`, `a4_recompute.py`, `a6_rho.py`, `a7_refit.py`, `a8_expo.py`, `a9_overlap.py`.

For independence, I did not import `hdps_window.py` or `mimic_clmbr_summary.py`. My panel rebuild uses pandas window logic and my own drug tokenizer, with duckdb used only to read the staged parquet. I recomputed the summary statistics from the per-trial cells with my own code. The refits use only `ps_logit`, `match`, `cox`, `smd_vector`, `hdps_levels`, `hdps_rank` and `pcs`.

This report gives aggregates only: no patient rows, IDs or dates, no per-trial pair counts, retention or ESS, and no counts of 1–10. I did not open any note text.

## Verdict: PASS

There are no BLOCKING findings. Two findings are SHOULD-FIX (S1, S2), both in the doc only:
- **S1:** the scope of the leakage claim overstates what was checked. The sparse dx flags follow the PS-CVD5 "earlier admission" rule, not the strict discharge-before-cut rule.
- **S2:** four benchmark-permutation P values are mis-rounded in the doc.

Neither changes a result or a conclusion.

## Checks

| # | Check | Result |
|---|---|---|
| 1a | Gate 1: gate1 cells vs v20 demo / hdPS200 × base, ECG, permECG × 2 populations (arms + vars, all columns) | **PASS**, all 8 trials: same rows, max \|Δ\| 0, same NaN pattern, text equal |
| 1b | Gate 1: rebuilt orig panel vs each trial dir's `panel.parquet` | **PASS**, 8/8: same patients, same feature set, max \|Δ\| 0. `gate.json` also records levels = `TrialData.lvl` in 8/8 |
| 1c | Gate 2: gate2 cvd5 cells vs `results_prior` (6 arms × 2 populations) | **PASS**, 8/8, max \|Δ\| 0 |
| 1d | `results/<k>_arms.csv` and `_vars.csv`: demo and hdPS200 base / ECG / permECG (population all) vs v20 | **PASS**, 8/8, max \|Δ\| 0 |
| 1e | Extra: independent refit of hdPS-prior base and + AI-ECG for ARISTOTLE and SOAP II, from the rebuilt prior panel + prior dx flags | **Equal** to `results/`: same input count, same pairs, \|Δ\| ≤ 1e-16 in mean \|SMD\|, log HR and SE |
| 2a | Leakage: own rebuild of the prior candidate panel (dx_, rx_, px_, lab_ under the stated rule) for ARISTOTLE, PLATO (v1.5) and SOAP II, PEPTIC (v20) | **Identical** in all 4 trials: same feature sets, every value equal (0 cells differ) |
| 2b | Events at or after the cut, at or after t0, index-admission dx/px (4 trials, own events) | **0 / 0 / 0**. Per-domain event and index-episode counts equal `panels.json` per trial. The checks have power: in each trial, more than 10 analysed patients have index-admission dx codes, and more than 10 have rx and lab events in [cut, t0) that are excluded |
| 2c | Exposure drugs (all 8 trials; exact tokens plus my own wider brand / generic list) | **0** rx_ features match any exposure name |
| 2d | Sparse prior dx flags vs my own rebuild (4 trials) | **Equal**. Rule difference: see S1 |
| 2e | Doc leakage table (aggregate) | **Confirmed** against `panels.json`: 8,731,376 events; domain shares 90.0 / 8.1 / 1.8 / 0.1%; 18.2% in the index episode; 79.7% / 41.3% / 36.2%; orig column 17.3 M, 49.0%, 353,609, 369,228, 369,278, 57.4%, 97.4%, 39.9%. Index-admission dx/px in the orig window come only from SOAP II / ELITE II / PEPTIC |
| 3 | Window matches the AI-EHR primary input | **Yes for the candidate levels**: dx/px from earlier admissions discharged before the cut and timed at discharge; rx and lab before the cut; the index ED stay kept. Differences are judged below |
| 4 | More than 20 headline numbers recomputed | **2,128 field-level comparisons with `summary.json`, 0 mismatches > 1e-9.** About 150 doc numbers checked; only the 4 P values in S2 differ |
| 5 | Masks | **PASS.** Every cell has 26 items, and 22 after block D is dropped (all 22 observed in every primary cell). Block D is excluded for every arm in the 22-item results. My pooled ρ(creatinine, CKD flag) = 0.3155 matches the reported 0.315. Over all hdPS-prior candidate levels + flags (not only the top 200), the max per-trial \|ρ\| with any A–C item is 0.349 (ARISTOTLE) and 0.369 (SOAP II), so no soft proxy appears even before selection |
| 6 | Cell validity | **Confirmed:** 0 failed cells and 0 overlap-invalid cells in all 192 cells; all cells retain ≥ 50%. Cells with > 10% extreme PS: hdPS-prior 12 (3 trials; max 0.213), hdPS200 24 (4 trials; max 0.287), PS-CVD5 and PS-Demo 0. One hdPS200 cell has C > 0.90. Median C values and input ranges (212–216, 244–248, 276–280, 308–312) as in the doc. The near-separation sensitivity (13.2, 11.8, 3.4, 8.2, 9.0%; k 6 / 5 / 4 / 4 / 4) and the overlap sensitivity (identical) both reproduced |
| 7 | Privacy scan (script, doc, this report) | **PASS.** No patient IDs, no patient-level dates (the only dates are run dates and seeds), no counts of 1–10 and no per-trial pairs, retention or ESS. The doc gives retention only as bands counted across cells; I judge that acceptable. The script prints to stdout only per-step markers, aggregate leakage JSON (event totals, per-trial feature counts), gate summaries and the ρ summary (feature names) |
| 8 | Code review | No correctness bug found. I checked the SQL windows; the column order (orig aligned to the trial-dir panel; prior ordered by domain and then name, deterministic); the shared ECG/CLMBR placebo permutation (as v21; gate 2 equal); the 22/26 item handling; the contrast logic (items observed in both cells; failed cells drop the trial); one- vs two-sided choices (match the queue and `pipeline.md` §6); the sign-flip and benchmark-permutation statistics. Minor notes: N7, N8 |

### Check 3: differences between the hdPS-prior window and the AI-EHR primary input, judged

| Difference | Judgement |
|---|---|
| 365-day look-back for rx/lab/dx/px (AI-EHR has none) | Not leakage. hdPS-prior sees less history than AI-EHR, which if anything handicaps hdPS. It is stated in the §1 rule but not in the limitations (N5) |
| rx_ cut at min(admittime, t0); v20 used the index calendar day | Matches AI-EHR (`starttime < t0` and `< admittime`). Orders between midnight and admission now count. Correctly disclosed in §7 |
| px dated by chartdate for the look-back; event time = the earlier admission's discharge | Matches AI-EHR, which times px at the discharge of earlier admissions discharged before t0 and before admission |
| Sparse dx flags: "earlier admission" (admittime before the index admission, other hadm) with no discharge-before-cut condition and no look-back | Same rule as PS-CVD5 (`mimic_cvd5.flags`), as the queue asked. It is looser than the AI-EHR rule. 13 of 45,107 analysed patients (0.03%) have an earlier admission discharged at or after the cut. Negligible, but the doc's "every input event before the cut" overstates it (S1) |
| PLATO's `stemi_index_adm` / `pci_index_30d`: earlier admissions discharged ≥ t0 − 30 d, with no upper bound | Same as the v1.5 audit fix. In my PLATO rebuild, no flag relies on an admission discharged at or after the cut. Acceptable; the flag names now mean a recent prior event |
| AI-EHR drops the trial's gate-condition ICD prefixes, rows without an NDC, and adds Visit/IP and Visit/ER tokens; hdPS uses drug-string tokens and no visits | Representation differences, not window differences. Worth one line in the limitations (N5) |

## Recomputed numbers (mine vs doc; primary 7 trials, 22 items unless stated)

Each value below is identical to `summary.json`; "doc" means the doc's value.

| Quantity | Mine | Doc |
|---|---|---|
| Mean \|SMD\|: unmatched / PS-CVD5 / hdPS-prior / hdPS200 | 0.169 / 0.158 / 0.140 / 0.113 | same |
| hdPS-prior + AI-ECG / + AI-EHR / + both | 0.124 / 0.141 / 0.126 | same |
| hdPS-prior + permuted AI-ECG / + permuted AI-EHR | 0.143 / 0.145 | same |
| PS-CVD5 + AI-ECG / + AI-EHR / + both | 0.147 / 0.146 / 0.129 | same |
| PS-Demo base / + AI-ECG / + AI-EHR / + both / + permuted AI-ECG / + permuted AI-EHR | 0.166 / 0.147 / 0.147 / 0.131 / 0.170 / 0.175 | same |
| hdPS200 + AI-ECG / + AI-EHR / + both / + permuted AI-ECG / + permuted AI-EHR | 0.105 / 0.110 / 0.095 / 0.115 / 0.117 | same |
| % \|SMD\| < 0.1: unmatched, PS-CVD5, hdPS-prior, + AI-ECG, hdPS200 | 41.6, 44.2, 48.1, 55.2, 60.4 | same |
| Domain means A / B / C: hdPS-prior; PS-CVD5; hdPS200 | .147 / .137 / .110; .170 / .153 / .125; .107 / .118 / .087 | same (all 23 rows checked) |
| Mean \|Δ log HR\|: PS-CVD5, hdPS-prior, + AI-ECG, + AI-EHR, + both | 0.344, 0.239, 0.187, 0.240, 0.213 | same |
| hdPS-prior vs PS-CVD5 (two-sided) | 11.7% (7.1 to 16.8), 7/7, P .016; bench. P 0.8315 (exact 0.833) | same |
| hdPS-prior + AI-ECG vs hdPS-prior | 10.8% (7.2 to 15.7), 7/7, P .008; closer 5/7, P .086; bench. P .20 (exact .195) | same |
| hdPS-prior + AI-EHR vs hdPS-prior | −1.2% (−7.8 to 5.8), 4/7, P .617; bench. P .97 (exact .971) | same |
| hdPS-prior + both vs hdPS-prior | 10.0% (4.2 to 14.3), 6/7, P .016; bench. P **0.4148** (exact .413) | same, except bench. P **.42** (S2) |
| + AI-ECG vs + permuted AI-ECG; + AI-EHR vs + permuted AI-EHR | 12.9% (9.4 to 16.6) 7/7; 2.9% (−3.1 to 9.2) 5/7, bench. P **0.7648** | same, except bench. P **.77** (S2) |
| + both vs + AI-EHR; + both vs + AI-ECG; + AI-EHR vs + AI-ECG | 11.0% (3.7 to 18.2) 6/7; −1.0% (−11.8 to 6.0); −13.5% (−21.6 to −6.6) 0/7 | same |
| PS-Demo vs hdPS-prior; PS-Demo + AI-ECG vs hdPS-prior | −19.1% (−23.5 to −14.7); −5.4% (−12.1 to 1.0); bench. P **0.4047** for both | same, except bench. P **.41** for both (S2) |
| PS-Demo + AI-EHR / + both vs hdPS-prior | −5.6% (−13.5 to 1.8); 5.8% (0.2 to 10.9), 6/7, P .109 | same |
| PS-CVD5 + AI-ECG / + AI-EHR / + both vs hdPS-prior | −5.2%; −4.5% (P .047); 7.9% (4.2 to 12.6), 7/7 | same |
| PS-Demo + AI vs PS-Demo (ECG / EHR / both) | 11.5% / 11.4% / 20.9% | same |
| hdPS200 vs PS-CVD5; hdPS-prior vs hdPS200 | 28.7% (18.6 to 39.8); −24.0% (−39.3 to −13.1) | same |
| hdPS200 + AI-ECG / + AI-EHR / + both vs hdPS200 | 6.9% / 2.6% / 16.0%; bench. P .82 / .17 / .26 | same |
| PS-CVD5 + AI-ECG vs PS-CVD5, 22 and 26 items; + AI-EHR, + both | 7.1% (1.9 to 14.9), 6.6%; 7.7%, 18.6% | same |
| 26 items: hdPS-prior vs PS-CVD5; + AI-ECG vs hdPS-prior; hdPS200 mean \|SMD\| (block D) | 12.9%; 10.3%; 0.105 (0.061) | same |
| All 8 trials: hdPS-prior vs PS-CVD5; + AI-ECG; + AI-EHR; + both; + both vs + AI-EHR | 13.3% 8/8; 10.7% 8/8; 0.1% 5/8; 11.2% 7/8; 11.1% 7/8 | same |
| PEPTIC HR: PS-CVD5; hdPS-prior; + AI-ECG; + AI-EHR; + both; hdPS200 | 1.51 (1.35–1.69); 1.20 (1.08–1.35); 1.15 (1.02–1.28); 1.28 (1.14–1.43); 1.18 (1.05–1.32); 0.93 (0.83–1.04) | same (all 24 arms checked) |
| PEPTIC mean \|SMD\|: unmatched, PS-CVD5, hdPS-prior, + AI-ECG, + both, hdPS200 | 0.189, 0.196, 0.151, 0.136, 0.123, 0.075 | same |

How the benchmark-permutation P was checked: I recomputed the 20,000-draw P with `default_rng(0)` and it equals `summary.json` in every contrast. I also computed the exact P over all 5,040 permutations for every primary 22-item contrast. The largest gap between the two is 0.007.

## Findings

### BLOCKING

None.

### SHOULD-FIX

**S1. The leakage claim is wider than what was checked; the sparse dx flags follow the PS-CVD5 rule.**
- **Where:** `docs/mimic/MIMIC_HDPS_WINDOW.md:16-20` (Verdict 2) and `:56` ("every hdPS input event is strictly before cut … within the existing look-back"). Code: `scripts/mimic/hdps_window.py:210-213`, `:219-227`.
- **What was checked:** the leakage checks cover only the candidate-level events (`ev_*`).
- **What the flags do:** the sparse flags (`prior_dx`) take every admission with admittime before the index admission, with no `dischtime < cut` condition and no look-back. The PLATO 30-day flags have no upper bound on dischtime.
- **Size:** 13 of 45,107 analysed patients (0.03%) have such an "earlier" admission discharged at or after the cut, so codes coded after the cut can reach their flags. PS-CVD5 uses the identical rule, so the hdPS-prior vs PS-CVD5 comparison stays like-for-like. Against the AI-EHR rule (discharge before t0 and before admission) it is a small looseness. The impact is negligible, but the doc should not say "every input event".
- **Fix:** say that the leakage checks cover the candidate levels (8.73 M events), and that the dx flags use the PS-CVD5 "earlier admission" rule (no discharge or look-back condition; 13 analysed patients, 0.03%, have an earlier admission discharged at or after the cut). Alternatively, add `AND ad.dischtime < c.cut` to the three `prior_dx` queries and re-run. I recommend the doc fix, because it keeps hdPS-prior and PS-CVD5 on the same flag rule.

**S2. Four benchmark-permutation P values are mis-rounded (double rounding from the 3-decimal `tables.md`).**

| Where | Contrast | `summary.json` | Doc | Should be |
|---|---|---|---|---|
| `MIMIC_HDPS_WINDOW.md:43` and `:162` | hdPS-prior + both vs hdPS-prior | 0.4148 | .42 | .41 |
| `:164` | + AI-EHR vs + permuted AI-EHR | 0.7648 | .77 | .76 |
| `:170` | PS-Demo vs hdPS-prior | 0.4047 | .41 | .40 |
| `:171` | PS-Demo + AI-ECG vs hdPS-prior | 0.4047 | .41 | .40 |

**Fix:** round from `summary.json` rather than from `tables.md`. No conclusion changes.

### NON-BLOCKING

- **N1** (`:28`): "About half of the v20 hdPS's apparent advantage … came from the index stay". hdPS-prior keeps 11.7 of the 28.7 points, so about 60% of the advantage came from the index stay; mean \|SMD\| gives the same answer: (0.140 − 0.113) / (0.158 − 0.113) = 0.60. §6 already says "less than half" correctly. Suggest "about 60%" or "more than half".
- **N2** (`:100`): "The prior top 200 has more lab and dx levels and fewer rx levels than the original." This holds only in some trials. In SOAP II and PEPTIC, the prior top 200 has fewer dx levels and more rx levels, because the index-admission codes are gone; TRANSFORM-HF has fewer lab levels. Qualify the sentence by trial group.
- **N3** (`:223-229`, §5): the column "Trials with near-separation dropped" actually drops trials where either compared cell has > 10% extreme PS. That is why k is 6 / 5 / 4 even though "3 of 7 trials" have near-separation. Say so in the header.
- **N4** (`:112`): "rx sodium chloride, sporadic" is the level `rx_sodium__spor`. Its token is the first word of the drug string ("sodium"), so the level pools every "sodium …" order. Label it "rx 'sodium' (first drug token)".
- **N5** (§7): add one limitation listing the remaining differences from the AI-EHR input:
  - hdPS keeps the 365-day look-back (it sees less history than AI-EHR);
  - the dx flags have no look-back;
  - AI-EHR removes gate-condition ICD prefixes and orders without an NDC, and adds visit tokens.
- **N6** (`:44`, `:240`): "Every benchmark-permutation P is ≥ .17" is true for the reported contrasts. One unreported head-to-head in `summary.json` (hdPS200 + AI-EHR vs + AI-ECG) has P 0.066. Write "every reported".
- **N7** (`hdps_window.py:524`): `rho_trial` zips `list(D.groups["dx"])` with the columns of `D.Gm["dx"]`. If `Gm["dx"]` ever carried missingness indicators, the names would misalign silently. That does not happen now (the dx flags are complete). An assert on the lengths would guard it.
- **N8** (`hdps_window.py:817`): `Pool(4)` × duckdb `memory_limit='120GB'` can reach 480 GB. For k ≤ 8, the exact benchmark permutation (≤ 40,320 permutations) would remove the Monte Carlo error (≤ 0.007 here).

## Resolution (analysis session, 2026-10-15)

No BLOCKING findings, so no re-run was needed. Fixes applied to `docs/mimic/MIMIC_HDPS_WINDOW.md`:

| Finding | Action |
|---|---|
| S1 | The doc fix the auditor recommended. The leakage checks are now scoped to the candidate levels (8.73 M events). The dx flags are stated to follow the PS-CVD5 rule, with 13 of 45,107 analysed patients (0.03%) having an earlier admission discharged at or after the cut (Verdict 2, §1 rule). The flags stay on the PS-CVD5 rule so that hdPS-prior vs PS-CVD5 stays like-for-like. |
| S2 | Four benchmark-permutation P values re-rounded from `summary.json` (.41, .76, .40, .40). |
| N1 | Changed to "about 60%", with the calculation. |
| N2 | The top-200 domain-mix sentence is now qualified by trial. |
| N3 | §5 column header now reads "Trials dropped where either compared cell has > 10% extreme PS". |
| N4 | Label changed to rx "sodium" = first drug token. |
| N5 | A limitation listing the remaining differences from the AI-EHR input was added. |
| N6 | Changed to "every reported benchmark-permutation P". |
| N7 | Length assert added in `hdps_window.py` `rho_trial`. |
| N8 | Not changed: the queue specifies 20,000 draws. The Monte Carlo error is ≤ 0.007, per the audit. |

Verdict 8 also now says what the near-separation sensitivity shows: the AI-ECG result is unchanged, and the AI-EHR placebo contrast rises to 9.0%.

Round 2 (verification of fixes): PASS. Checked against `summary.json` and the audit outputs: 13 of 45,107 (0.03%); P .41 / .76 / .40 / .40; 60%; 11.8% 5/5, 9.0% 4/4, 3.4%. `hdps_window.py` compiles, and the new N7 assert holds in all 8 trials. The privacy scan still passes. Two remaining wording notes, both NON-BLOCKING. (1) `MIMIC_HDPS_WINDOW.md:252` says hdPS px levels are "dated by chartdate". In fact hdPS-prior px also requires the earlier admission to be discharged before the cut, as AI-EHR does; chartdate is used only for the look-back and the count. (2) `:102` says SOAP II and PEPTIC are the trials "where the index-admission codes are gone"; ELITE II also lost them but follows the other pattern.
