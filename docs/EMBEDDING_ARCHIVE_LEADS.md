# Embedding leads and clinical comparator refinement

Archive inspection on2026-09-23; these are unverified cluster leads, not validated
assets. Neither archive was modified or imported.

| Lead | Historical source |
|---|---|
| ECG metadata `/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet` and signals `/mnt/raid0/bb2238/signals/preprocessed/all_ecgs` | ecg-tte archive scripts/stage2_embed.py and README |
| ECG biometric checkpoint `/mnt/raid0/rbc58/cardiomap/experiments/ecg_biometric/best.pt` | ecg-tte archive scripts/stage2_embed.py |
| ECG similarity checkpoint `/mnt/raid0/rbc58/cardiomap/experiments/ecg_sim_from_biometric/best.pt` | ecg-tte archive scripts/embed_cohort.py |
| Legacy COMET ECG vectors `/mnt/raid0/rbc58/cardiomap/trialemulation/methods/comet/embeddings/biometric` | ecg-tte archive scripts/stage2_embed.py |
| CLMBR weights `/mnt/raid0/eo287/clmbr` | ../mosaic/archive/mosaic1/mosaic1.md and scripts/check_clmbr_vocab.py |
| CLMBR caches under `/mnt/raid0/rbc58/mosaic/prog_clmbr_*` and MEDS `meds_extract_ascvd` | mosaic1/mosaic1.md and scripts/run_echo_anchored_ecgtte.sh, run_disease_as_ecg.sh, run_ukb_prs.sh |

Legacy ECG pool included candidates within a +/-365day window. A vector keyed to an
ECG might be reusable only after linking that specific recording strictly before
COMET index and checking encoder provenance/training overlap. A per-patient vector
without timestamp provenance is not enough. CLMBR cached representations may be
as-of a different ECG/landmark; verify full input-history cutoff, not filename alone.
No old phenotype, OMOP mapping, checkpoint or eligibility contract adopted here.

Run bounded path/footer inspection (no patient rows or directory filenames printed):

```bash
umask 077
EMBED_ASSETS=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/embedding-assets-XXXXXXXX)
python scripts/inspect_embedding_assets.py --output-dir "$EMBED_ASSETS/report"
cat "$EMBED_ASSETS/report/summary.json"
```

Next after schema evidence: exact-key coverage by arm at the current index, explicit
pre-index ECG window, mapping/OOV coverage and temporal cutoffs for CLMBR; immutable
model hashes and preprocessing contract. Existing cached source tables remain source
of truth; no GPU job or warehouse rebuild until this linkage is specified.

## Refined clinical PSM v2

Use --refined with run_comet_exploratory_psm.py. Explicit newversion
comet_exploratory_psm_v2_refined replaces linear EF with natural spline with internal
knots30,50 and boundaries1,100 on the existing EF candidate scale. Adds all original
nonconstant missingness flags. Knots declared before inspecting refined matching
results. This assumes the existing percent-like EF scale; does not validate units.
All other covariates/cohort/imputations/caliper/order unchanged. Common clinical+
missingness evaluation set stays identical to v1; do not compare overall scores
using different evaluation sets. Constant predictors and QR-identified exact
linear dependencies are explicitly reported; removing dependent columns preserves
model span. Do not remove difficult clinical features from evaluation.

Preserve v1 as benchmark. Compare pair counts, arm retention, per-feature median/
worst SMD and distribution checks before freezing a clinical specification. This is
outcome-blind design refinement, not confirmation that v2 is superior. Traces and
final causal estimand remain unresolved. ECG/CLMBR comparisons must rerun the same
clinical comparator on their common available population and use frozen pre-index
representations. Modality availability cannot be treated as method improvement.
