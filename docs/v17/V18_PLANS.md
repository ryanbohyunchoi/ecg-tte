# v1.8 plans, fixed before any v1.8 result (2026-09-27)

## Plan A: prespecified AF confirmation
**Hypothesis** (from v1.7 exploratory pattern, `docs/v17/V17_PATTERNS.md`). In AF trials, adding the ECG embedding (32 PCs) to a demographics-only PS moves emulated HRs closer to the RCT HR, beyond placebo and beyond generic shrinkage.

**Confirmation set.** New AF trials not previously analysed:
- AF population;
- active comparator;
- built with the existing pipeline;
- spec plus verified RCT HR committed before outcome extraction;
- ≥ 300 per arm with ECG, and ≥ 50 pooled events.

They are rated by the same blinded rater (`docs/v17/TRIAL_SELECTION_RULE.md`) before analysis. All built AF trials are analysed regardless of rating, and the rating is used for a subset analysis.

**Fixed analysis.** The code path is `v17_confirm.py`, unchanged.
- **PS:** P1 = demographics; P5 = demographics + HTN, T2D, CAD, AF, HF (`s11_p5.py`). AF is constant in AF trials.
- **Arms:** base, +ECG32, +shufECG, +noise32.
- **Matching:** 1:1, caliper 0.2.

**Endpoints.**
- **Primary:** |Δlog HR| vs RCT. This uses a one-sided exact sign-flip across the new AF trials and, co-primary, the benchmark-shuffle permutation (benchmarks drawn from all RCTs in the benchmark: 33 + new).
- **Secondary:**
  - consistency (|z| < 1.96);
  - z²;
  - % held-out |SMD| < 0.1;
  - the combined AF set (7 existing + new).

Every result is reported regardless of direction.

## Plan B: the same analyses with CLMBR (EHR foundation-model embedding) in place of or added to ECG
**Question.** Does a code-based EHR foundation-model embedding (CLMBR-T, 64 PCs, as in `v13_common.Trial.clm_pc`) give the same balance and emulation gains as the ECG, and does ECG add to CLMBR?

**Arms**, per PS (P1, P5, P2), 33 trials (the v1.6 18 plus the v1.7 15), halves full/A/B:
- base;
- +CLMBR64;
- +ECG32;
- +CLMBR64+ECG32;
- +shufCLMBR (rows permuted, same dimension);
- +noise64.

The engine and estimator are unchanged.

**Leakage rules** (must be checked and documented before results):
- the CLMBR input window must end before index, with the index day excluded;
- exposure-defining codes must be absent from the input or documented.

CLMBR is trained on the coded record, so the "coded record" held-out variables (medications, utilisation, held-out codes) are NOT unmeasured for CLMBR. Balance is therefore reported:
- (i) on the full 58-panel;
- (ii) on the non-coded physiology subset only (vitals, labs, echo) = the primary balance endpoint for the CLMBR comparison;
- (iii) on the covars2b non-proximal panel, excluding code-derived variables.

**Endpoints.** These are the same as v1.7:
- % |SMD| < 0.1;
- |Δlog HR| vs RCT with the benchmark shuffle;
- placebo contrasts;
- comparator clustering;
- LOO;
- halves;
- per-category (AF, HF, DM, HTN, ACS, other).

**Key contrasts:**
- CLMBR vs base;
- CLMBR vs ECG;
- CLMBR+ECG vs CLMBR (does ECG add to CLMBR?);
- CLMBR+ECG vs ECG.

This analysis is exploratory; all cells are reported.
