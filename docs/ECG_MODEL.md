# ECG representation — status and plan (2026-09-23)

## Bug found: input scale (fixed)
- BCL checkpoints under `/mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/` were
  trained on **µV** input.
  - The first BatchNorm's stored running variance is ~1.5e4.
  - `/mnt/raid0/bb2238/signals/preprocessed/all_ecgs` stores **mV**.
  - The legacy `modules/utils.py` divided `numpy_rp` by 1000, and the default roots in
    `utils_torch.py` don't exist on this node.
- Fed mV, the eval-mode network is nearly input-invariant. COMET embeddings had
  ‖mean unit vector‖ = 0.999995 and matched-pair cosine distance ~1e-7.
- **Fix:** `scripts/bcl_embed_uv.py --scale 1000`, a wrapper around the upstream
  `bcl_embed_torch.py`.
- **Second bug (~5% of ECGs):** `formats` rows flagged `5_0` (250 Hz) are already 500 Hz in
  `all_ecgs`. `process_ecg` then takes 5 s and stretches it to 10 s. Pass a formats CSV
  with no 250 Hz flags.
- The June `stage2_embed.py` run (ecg_biometric checkpoint) also fed raw signal with no
  normalisation. Treat those 319K embeddings as unusable.

## Probe results (5-fold linear probe, standardised)
| Embedding | Population | Sex | Age | AF | Low EF |
|---|---|---|---|---|---|
| Transformer BCL, mV input (as run) | COMET n=6103 | 0.69 | 0.64 (≥65) | 0.62 | 0.59 (LVEF≤40, MICE) |
| **Transformer BCL, ×1000** | COMET n=6103 | 0.81 | 0.80 (≥65) | 0.75 | 0.69 |
| Transformer BCL, ×1 | all-comers n=2400 | 0.83 | R² 0.26 | 0.89* | 0.88† |
| **Transformer BCL, ×1000** | all-comers n=2400 | 0.92 | R² 0.59 | 0.96* | 0.91† |
| global_mean BCL 08_18 (64-D), ×1000 | all-comers | 0.88 | R² 0.41 | 0.97* | 0.91† |

\* AF from the ECG diagnosis text, only ~55 positives. † Label is the top decile of an existing ECG
LVSD model score, not echo.
COMET is harder: an older HF population, AF as a *history* diagnosis, and LVEF partly imputed.

## Out-of-cohort phenotype heads (done 2026-09-23)
- Training data: 40,000 ECG–echo pairs within ±30 d, from patients outside COMET
  (`scripts/build_ecg_phenotype_set.py`). Embedded with the fixed BCL model.
- Heads: linear, on standardised embeddings (`scripts/train_ecg_phenotype_heads.py`).
- Held-out (8,127 patients) performance:

  | Head | Metric | Result |
  |---|---|---|
  | LVEF ≤ 40 | AUC | 0.90 |
  | AF | AUC | 0.95 |
  | Male sex | AUC | 0.85 |
  | LVEF | R² | 0.32 |
  | Age | R² | 0.52 |

- The fixed BCL embedding therefore meets the LVEF and AF gates on echo-linked labels.
- The five scores are available as PS covariates:
  `audits/claude-ecg-phenotype-heads/restricted_cohort_phenotypes.parquet`.
- **Retraining is not needed for now.** A fine-tuned multi-task model could raise
  LVEF R² above 0.32. In COMET, phenotype scores already match the 32-PC result.

## Candidate checkpoints
1. **`CNN0_lead_time_transformer_…_08_26_2026/trained_12lead_30.pt`**: 256-D, 12-lead 10 s 500 Hz.
   Best probes after the fix. **Current default.**
2. `global_mean` BCL 08_18: 64-D, compact, weaker on age and sex.
3. `spatiotemporal_flatten` 08_26: 15K-D, training accuracy 0.999 (memorisation). Avoid.
4. Supervised models:
   - ECG-Cath CLIP (`AK_model_saves/ECG_cath_clip_signal`).
   - TF EchoElig Under40 / valve / HCM CNNs.
   - Their disease probabilities are ideal low-dimensional PS covariates. Some are
     precomputed in `mosaic/allcomers_ecg.parquet`.

## Plan
1. **Done for COMET:** re-embedded with the fixed wrapper; heads gated on echo LVEF. Next:
   re-embed each trial pool the same way and gate it
   (`embedding_utils.probe_gate`, echo-linked LVEF on observed values only).
2. **Cheap add-on:** a supervised "ECG phenotype" vector as PS covariates:
   - P(LVEF<40) from the EchoElig/LVSD model
   - AF / LVH / conduction flags from MUSE text
   - intervals
3. **If LVEF recovery stays partial (COMET held-out LVEF SMD 0.56 → 0.42 now):** train a
   supervised multi-task model.
   - Targets: EF≤40 plus EF regression, AF, LVH, age, sex.
   - Data: ~907K ECG–echo pairs within ±30 d (193K patients, 14.8% EF≤40), plus 5.08M ECGs
     for text labels.
   - Cost: ~1–2 days on 4 H100s; data loading is the bottleneck.
   - **Train only on patients outside every emulated trial cohort** (or cross-fit) to avoid
     leakage into the PS.

## Gate before any use in matching or PS (held-out patients, linear probe)
- Sex AUC ≥ 0.90 (all-comers) / ≥ 0.80 (disease cohorts).
- Age R² ≥ 0.5.
- AF AUC ≥ 0.93 with ≥ 200 positives.
- Echo-linked LVEF≤40 AUC ≥ 0.85.
- Not collapsed (`anisotropy_report`).
- Outputs at ×1 and ×1000 must differ (proves the scale was applied).
