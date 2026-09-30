# v2.0 MIMIC-IV external replication: held-out balance and RCT agreement (2026-09-30)

**Exploratory external replication.** The plan was committed before any result (`docs/v20/MIMIC_REPLICATION_PLAN.md`, local commit 25c58b2).
- Code: `scripts/v20/mimic_replication.py` (gate, held-out blocks, analysis), `mimic_build_new.py` (new trials), `mimic_ecg_new.py` (ECG pipeline wrapper) and `mimic_summary.py`.
- Outputs: `/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-mimic-replication/` (umask 077).
  - The generated tables are in `summary/tables.md` and `summary/summary.json`.
  - The per-trial CSVs are in `results/`.
- Aggregates only; counts 1–10 are suppressed. No note text was opened and no patient rows were printed.

## Verdict (plain language)

1. **The headline Yale finding replicates in MIMIC-IV.**
   - **Result:** in the 7 cardiovascular emulations, adding the ECG embedding to a demographic PS improved balance on held-out characteristics **in every trial**.
     - The share of characteristics with |SMD| < 0.1 rose from 41.2% to 51.6% (+10.4 points; 7/7 trials; exact sign-flip p = 0.008).
     - Mean |SMD| fell by **10.3% (95% CI 6.4–14.5)**, lower in 7/7 trials (p = 0.008).
   - **Placebo:** the permuted-ECG placebo did nothing (+0.5 points; −2.5%).
   - **Comparison with Yale:** 12.6% (8.0–16.7) in 38 trials.
   - **By block:** the gain appears for core labs and vitals (12.4%) and for additional labs such as NT-proBNP, troponin, lactate and albumin (11.2%). It is smaller for utilisation (4.4%).
2. **It survives dropping index-day ECGs.** Excluding patients whose ECG was recorded on the index day (16–53% per trial), mean |SMD| still fell by 14.5% (9.7–19.7), in 7/7 trials. The gain in % balanced was +6.6 points (5/7; p = 0.094).
3. **As in Yale, the gain shrinks as the PS gets richer:**
   - sparse diagnosis PS 10.2% (7.6–14.4; 7/7);
   - hdPS200 7.5% (−0.5 to 15.9; 4/7);
   - clinical-lite PS 1.2% (−9.6 to 10.8).

   The clinical-lite PS already contains the core labs and vitals.
4. **RCT agreement was not reliably improved, also as in Yale.**
   - **Demographic PS:** the mean |Δ log HR| vs the RCT went from 0.337 to 0.315 with the ECG (4/7 closer; p = 0.27).
   - **Clinical-lite PS:** 0.297 → 0.175 (5/7 closer; p = 0.078). The permuted ECG, however, also moved it to 0.231, so part of this is generic.
   - **Caveats:** with 7 trials and short in-hospital designs, agreement is weakly powered. Two benchmarks are an OR (SOAP II) and an RR (PEPTIC).
5. **Negative-control trial (PEPTIC, PPI vs H2RA in ventilated patients; RCT RR 1.05).**
   - **Demographic PS:** strongly confounded, HR 1.53 (1.36–1.71). Adding the ECG moved it toward the benchmark, to 1.39 (1.24–1.56), and improved balance (30.8% → 42.3% of characteristics balanced). The permuted ECG did not (1.61).
   - **Clinical-lite PS:** it recovered the null, 0.98 (0.88–1.10), and the ECG added nothing (0.96).
   - **Reading:** the ECG partly captures the illness-severity confounding in this non-cardiac question, but it does not replace measured physiology. This matches the plasmode and the Yale results.

## 1. What was run

| Step | Result |
|---|---|
| Reproduction gate | v1.5 primary-outcome estimates for 5 trials × 7 arms recomputed with the v1.5 engine: max \|Δ log HR\| 8.3e-17, max \|Δ SE\| 8.3e-17 → **PASS** |
| New trials built | SOAP II (dopamine vs norepinephrine; 9,764 initiators), ELITE II class (ARB vs ACEi in HF; 12,667), PEPTIC (PPI vs H2RA in ventilated ICU patients; 12,449), from the frozen screen definitions |
| ECG linkage (new trials) | SOAP II 6,159 / 6,172 with a candidate ECG; ELITE II 7,783 / 7,798; PEPTIC 7,413 / 7,432. Same BCL checkpoint, ×1000 µV fix, GPU 0 (free per nvidia-smi) |
| Held-out panel | 26 characteristics for the demographic, sparse and hdPS PS: A core labs and vitals (8), B additional labs (13), C ventilation at t0 (1), D utilisation (4). For the clinical-lite PS: B + C (14), since A and D are in that PS |

**Coverage of the additional labs before t0**, among analysed initiators (range over the 8 trials):
- NT-proBNP 11–52%;
- troponin T 26–73%;
- lactate 36–88%;
- albumin 41–74%;
- BUN, WBC, platelets and bicarbonate ≥ 89%;
- INR 80–95%;
- LDL 13–37%;
- HbA1c 25–40%.

## 2. Balance (mean over trials; full ECG cohort unless stated)

| Set | Base PS | k | % \|SMD\| < 0.1: base → + ECG | Δ pts (better; p) | Relative reduction in mean \|SMD\| [95% CI] (lower; p) | Permuted ECG: Δ pts / rel. red. |
|---|---|---|---|---|---|---|
| **Primary (7 CV trials)** | **demographic** | 7 | **41.2 → 51.6** | **+10.4 (7/7; 0.008)** | **10.3 [6.4, 14.5] (7/7; 0.008)** | +0.5 / −2.5 |
| Primary, excluding index-day ECG | demographic | 7 | 41.2 → 47.8 | +6.6 (5/7; 0.094) | 14.5 [9.7, 19.7] (7/7; 0.008) | +1.1 / −1.9 |
| Primary | sparse | 7 | 47.3 → 50.0 | +2.7 (4/7; 0.28) | 10.2 [7.6, 14.4] (7/7; 0.008) | +1.1 / −3.6 |
| Primary | hdPS200 | 7 | 65.9 → 68.1 | +2.2 (3/7; 0.31) | 7.5 [−0.5, 15.9] (4/7; 0.10) | 0.0 / −0.3 |
| Primary | clinical-lite | 7 | 68.4 → 69.4 | +1.0 (4/7; 0.50) | 1.2 [−9.6, 10.8] (3/7; 0.42) | +1.0 / 0.5 |
| All 8 (incl. PEPTIC) | demographic | 8 | 39.9 → 50.5 | +10.6 (8/8; 0.004) | 11.0 [7.3, 14.9] (8/8; 0.004) | +1.0 / −1.7 |

**By block** (primary set, demographic PS; relative reduction in mean |SMD| with the ECG): core labs and vitals 12.4%, additional labs 11.2%, utilisation 4.4%. Excluding index-day ECGs: 13.8%, 15.0% and 7.6%.

The bootstrap CIs over 7–8 trials are crude. The exact sign-flip p (minimum 1/128 with 7 trials) and the per-trial direction (7/7) carry the inference.

## 3. Agreement with RCT results (trial primary outcome; primary set of 7)

| Base PS | Arm | r | Estimate agreement | Std-diff agreement | Mean \|Δ log HR\| | ECG closer (p) |
|---|---|---|---|---|---|---|
| demographic | PS alone | 0.71 | 0/7 | 5/7 | 0.337 | |
| demographic | + ECG | 0.67 | 1/7 | 4/7 | 0.315 | 4/7 (0.27) |
| demographic | + permuted ECG | 0.76 | 1/7 | 4/7 | 0.373 | |
| hdPS200 | PS alone | 0.68 | 1/7 | 5/7 | 0.220 | |
| hdPS200 | + ECG | 0.54 | 3/7 | 5/7 | 0.179 | 4/7 (0.22) |
| clinical-lite | PS alone | 0.74 | 2/7 | 4/7 | 0.297 | |
| clinical-lite | + ECG | 0.82 | 2/7 | 6/7 | 0.175 | 5/7 (0.078) |
| clinical-lite | + permuted ECG | 0.84 | 2/7 | 6/7 | 0.231 | |

Benchmarks:
- SOAP II is an OR, 1.17 (0.97–1.42).
- ELITE II is an HR, 1.13 (95.7% CI).
- The 5 v1.5 trials use their v1.5 `rct.json`.

Death-only outcomes are used for SOAP II, ELITE II, TRANSFORM-HF and COMET. The trial composite is used for PLATO; stroke/SE for ARISTOTLE and ROCKET AF.

## 4. New trials (full ECG cohort)

| Trial | Base PS | Arm | Pairs | % balanced | Mean \|SMD\| | HR (95% CI) | RCT |
|---|---|---|---|---|---|---|---|
| SOAP II | demographic | PS alone / + ECG / + permuted | 926 / 926 / 926 | 42.3 / 57.7 / 34.6 | 0.157 / 0.125 / 0.165 | 0.77 (0.66–0.89) / 0.75 (0.64–0.88) / 0.81 (0.69–0.94) | OR 1.17 (0.97–1.42) |
| SOAP II | clinical-lite | PS alone / + ECG | 890 / 873 | 57.1 / 64.3 | 0.113 / 0.101 | 0.87 (0.74–1.03) / 0.89 (0.75–1.05) | |
| ELITE II | demographic | PS alone / + ECG / + permuted | 1,841 / 1,837 / 1,841 | 53.8 / 61.5 / 50.0 | 0.126 / 0.108 / 0.127 | 0.74 (0.64–0.86) / 0.77 (0.66–0.90) / 0.69 (0.60–0.80) | HR 1.13 (0.95–1.35) |
| ELITE II | clinical-lite | PS alone / + ECG | 1,840 / 1,840 | 85.7 / 85.7 | 0.056 / 0.043 | 0.83 (0.71–0.97) / 0.90 (0.77–1.05) | |
| PEPTIC (negative control) | demographic | PS alone / + ECG / + permuted | 2,139 / 2,137 / 2,139 | 30.8 / 42.3 / 34.6 | 0.179 / 0.151 / 0.171 | 1.53 (1.36–1.71) / 1.39 (1.24–1.56) / 1.61 (1.42–1.81) | RR 1.05 (1.00–1.10) |
| PEPTIC (negative control) | clinical-lite | PS alone / + ECG | 1,927 / 1,915 | 50.0 / 42.9 | 0.097 / 0.099 | 0.98 (0.88–1.10) / 0.96 (0.85–1.07) | |

Hospital-initiated emulations of SOAP II and ELITE II do not reproduce the RCT direction with any PS: both show a lower HR for the first-listed arm. This most likely reflects residual confounding by indication and severity in inpatient prescribing, e.g. dopamine chosen in less severe shock, or ACEi vs ARB selection in HF admissions. It is a limitation of these emulations, not of the ECG comparison.

## 5. Deviations and notes (logged)

1. **Echocardiography was excluded from the held-out panel** as planned: the provenance and data-use status of the structured echo table on disk are unverified. The Yale echo-specific result is therefore not replicated here.
2. **New-trial cohorts** use the frozen, simplified screen definitions (gates, washout, ties, age, calendar). Trial exclusion criteria beyond these are not applied, and trial exposure classes were removed from the generic medication covariates.
3. **Outcomes:**
   - PEPTIC uses all-cause death within 90 d, not in-hospital death by day 90, to avoid censoring at discharge.
   - SOAP II uses death within 28 d.
   - ELITE II uses death within 365 d (trial horizon about 18 months).
4. **The index-day sensitivity analysis** reuses the within-trial ECG PCs of the full cohort.
5. **Technical:** the wfdb conversion dependency came from the v1.5 pip target (`software/claude-v15-wfdb`) via PYTHONPATH. The first launch failed before any conversion without it, and was relaunched.
6. **Not pushed:** this work is committed locally only, pending the PI's review of the UKB/MIMIC documents before publication.
