# CLMBR cosine versus clinical PSM: first exploratory comparison

Run this after the full codes-only embeddings. No GPU inference or MICE rerun.
The original clinical PSM is the primary comparator; the previously refined PSM
is shown separately with its history of refinement after balance review disclosed.
The 7,498 embedding-available patients define the common population. Original
7,499-person PSM runs are preserved. Five saved imputed datasets are subsetted in
their original order, without refitting MICE.

## Rules specified before embedding balance is examined

- CLMBR: frozen existing 768D checkpoint; codes-only; latest 4,096 token positions.
- L2-normalized vectors, cosine distance = 1 minus dot product.
- Carvedilol ordered by SHA256 of `comet_cosine_v1|patient_key`, lexical key breaks
  hash ties. Each receives the closest unused metoprolol patient; lexical control
  key breaks exact distance ties. 1:1, no replacement, no similarity cutoff.
- PSM formulas, descending treated-logit order and 0.2 pooled within-arm logit SD
  caliper remain unchanged for both original and previously refined versions.
- This compares method bundles with different ordering/support rules, not the
  isolated causal contribution of the distance metric. Cosine will retain the
  smaller arm without a cutoff; weak similarity pairs are not silently removed.
  Report distance distribution and retention together with balance. No tuning.
- Clinical/missingness evaluation variables and pre-match denominators are shared
  across methods within each saved imputation. Cosine pairs stay fixed across all
  five; PSM is re-estimated and matched separately in each. Do not pool SMDs with
  Rubin's rules. Observed-only balance has separate available-case denominators
  shared across methods, and reports measurement counts; it is not a replacement
  for missingness diagnostics.
- No outcomes, effect estimation, convergence approval, or final trial readiness.

## Run on H100

```bash
(
set -e
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
COMET_R_ENV=/mnt/raid0/rbc58/ecg-tte/software/mice-r-v2-tyXlJyw1/env
unset R_HOME
export R_LIBS="$COMET_R_ENV/lib/R/library"
export R_LIBS_USER="$COMET_R_ENV/lib/R/library"
export R_LIBS_SITE="$COMET_R_ENV/lib/R/library"
# Keep numerical libraries single-threaded for reproducible ties and small matrices.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
COMPARE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-cosine-comparison-XXXXXXXX)
export TMPDIR="$COMPARE_RUN/tmp"
mkdir -p "$TMPDIR"
echo "Report directory: $COMPARE_RUN/report"
/home/rbc58/miniconda3/envs/mosaic/bin/python scripts/compare_comet_clmbr.py \
  --embeddings /mnt/raid0/rbc58/ecg-tte/audits/comet-clmbr-full-NAyb4G2x/report \
  --mice /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-v2-w5ZRCHzh/report \
  --rscript "$COMET_R_ENV/bin/Rscript" \
  --output-dir "$COMPARE_RUN/report" || {
    cat "$COMPARE_RUN/report/summary.json"
    exit 1
  }
cat "$COMPARE_RUN/report/summary.json"
)
```

Review `summary.json` for per-method/per-imputation pair counts, retention and
balance metrics. `comparison_balance.csv` contains clinical and missingness SMDs,
variance ratios and ECDF distances. `comparison_observed_balance.csv` contains
observed-only SMDs and available measurement counts. `comparison_love_plots.pdf`
shows all three methods against the same unadjusted reference, one page per
imputation. `restricted_cosine_pairs.csv` includes cosine distance per pair and
must remain on H100. All patient-level inputs, logs and results remain restricted.
The cosine folder's propensity plots/scores are auxiliary original-PS fits from
the shared evaluation engine; they do not determine cosine matching.

Computational success does not remove source limitations, high missingness,
uncertainty in the imputation model or unresolved outcome/estimand definitions.

## Missingness-mask compatibility fix

The first H100 comparison stopped with AttributeError. The MICE producer saves
missingness as an array of per-patient objects; the comparison now validates and
subsets that exact row format. Pull the fix and rerun the block above to create a
fresh report. Existing embeddings and imputations remain unchanged. Failures now
report execution stage and allowlisted code locations without patient values.
