# Ordered BP diagnostic pilot v2

User-approved direction: preserve cohort/observed measurements; address imputed BP
ordering and extend to50iterations. Use --ordered-bp to select the explicit new
comet_mice_pilot_v2_ordered_bp contract; default v1 retains20iterations.

For each BP target update, draw standard PMM values. If a draw violates SBP>DBP,
refit PMM using observed target donors satisfying that recipient's current counterpart
value and redraw. Require at least5eligible observed donors. Both missing components
are updated sequentially during each iteration. This is a changed conditional
imputation model, not a post-hoc swap or clipping rule. All other variables and5
imputations remain unchanged. Runtime stops on observed invalid pairs, unavailable
counterpart predictors, insufficient donors or invalid final pairs. No patient removal.
This pilot does not prove model compatibility, MAR or adequate mixing.

## Repair/isolate R, then verify

The prior ABI warning may reflect incompatible packages or libraries mixed across
installations. Use a fresh environment, explicitly isolate R library paths, and
verify loading without any warnings. Do not overwrite the previous environment.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
export CONDA_PKGS_DIRS=/mnt/raid0/rbc58/ecg-tte/software/conda-pkgs
export TMPDIR=/mnt/raid0/rbc58/ecg-tte/software/tmp
mkdir -p "$CONDA_PKGS_DIRS" "$TMPDIR"
COMET_R_BUILD=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/software/mice-r-v2-XXXXXXXX)
COMET_R_ENV="$COMET_R_BUILD/env"
conda create -y --prefix "$COMET_R_ENV" --override-channels \
  --strict-channel-priority -c conda-forge \
  r-base=4.4 r-mice=3.19.0 r-jsonlite r-lme4 r-matrix
```

If creation succeeds, run this block. It stops if package verification warns or fails.
Library verification does not claim to have repaired anything until it passes on H100.

```bash
(
  unset R_HOME
  export R_LIBS="$COMET_R_ENV/lib/R/library"
  export R_LIBS_USER="$COMET_R_ENV/lib/R/library"
  export R_LIBS_SITE="$COMET_R_ENV/lib/R/library"
  "$COMET_R_ENV/bin/Rscript" --vanilla -e '
    options(warn=2)
    library(Matrix); library(lme4); library(mice); library(jsonlite)
    print(vapply(c("Matrix","lme4","mice"), function(p) as.character(packageVersion(p)), character(1)))
  ' || exit 1
  conda list --prefix "$COMET_R_ENV" --explicit > "$COMET_R_BUILD/conda-explicit.txt"
  COMET_MICE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-v2-XXXXXXXX)
  python scripts/run_comet_mice_pilot.py --ordered-bp \
    --rscript "$COMET_R_ENV/bin/Rscript" \
    --source-report /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-prep-M9F28Lk2/report \
    --output-dir "$COMET_MICE_RUN/report"
  cat "$COMET_MICE_RUN/report/summary.json"
  echo "Report directory: $COMET_MICE_RUN/report"
)
```

Expected5imputations50iterations,7499patients,zero invalid completed BP pairs. No
automatic PSM approval. Preserve the earlier pilot for comparison. Existing saved
review tool accepts both versions. Dependency setup time is separate from imputation.
