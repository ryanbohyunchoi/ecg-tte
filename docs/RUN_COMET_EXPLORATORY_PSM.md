# Exploratory clinical PSM and trace summaries

This is an outcome-blind design experiment on five pilot imputations. It does not
clear the imputation model, declare convergence or estimate effects. Trace review
can proceed alongside matching diagnostics; final analysis cannot bypass it.

Declared exploratory specification, before inspecting matching results:
-32clinical covariates, main-effects unpenalized logistic regression; categorical
 sex dummy coding. Complete constants explicitly reported and omitted from fitting
 only. No silent removal of nonconstant rank-deficient predictors: stop on failure.
-Carvedilol is treated; greedy descending treated-logit order, original row order
 resolves ties;1:1without replacement. Caliper0.2times pooled within-arm pre-match
 SD of logit. No exact matching, additional trimming or outcome-guided selection.
-Maximum possible pairs2960 given available comparator count; do not claim an ATT
 for all carvedilol patients after exclusions. Matched populations may differ across
 imputations. Final estimand and outcome-follow-up eligibility remain unfrozen.
-Each imputation independently fit/matched. Balance includes all clinical features,
 all sex levels and original missingness indicators (the latter are not PS predictors).
-Continuous SMD uses pooled within-arm pre-match sample SD; binary SMD uses pooled
 Bernoulli SD. Denominator fixed for pre/post within each imputation; zero denominator
 explicitly undefined. Report per-feature median/worst absolute SMD and number of
 imputations >=0.1, with undefined counts. No Rubin pooling of SMDs.
-Postmatch variance ratios, ECDF distances, retention, Love plots and PS histograms.
 No balance claim based on p-values. All warnings retained; no automatic pass.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
(
  set -e
  umask 077
  COMET_R_ENV=/mnt/raid0/rbc58/ecg-tte/software/mice-r-v2-tyXlJyw1/env
  unset R_HOME
  export R_LIBS="$COMET_R_ENV/lib/R/library"
  export R_LIBS_USER="$COMET_R_ENV/lib/R/library"
  export R_LIBS_SITE="$COMET_R_ENV/lib/R/library"
  COMET_PSM_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-exploratory-psm-XXXXXXXX)
  echo "Report directory: $COMET_PSM_RUN/report"
  python scripts/run_comet_exploratory_psm.py \
    --report /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-v2-w5ZRCHzh/report \
    --rscript "$COMET_R_ENV/bin/Rscript" \
    --output-dir "$COMET_PSM_RUN/report"
  cat "$COMET_PSM_RUN/report/summary.json"
)
```

No source rescan or MICE rerun. All patient pairs/scores remain private on cluster.
Review aggregate summary plus balance_across_imputations.csv and trace_drift_summary.csv
locally before sharing. Midpoint-versus-final trace differences are descriptive;
inspect original chain_traces.pdf for mixing/separation, not just scalar summaries.
No final MI precision selection, causal effect, RCT agreement or readiness implied.

Caliper reference: https://pmc.ncbi.nlm.nih.gov/articles/PMC3120982/ . The precise
matching order, reference arm and model specification above are project defaults
for this exploratory experiment, not prescriptions from the reference.

## Precision fix
The first implementation rounded the JSON caliper to4decimalplaces, which could
falsely fail cross-language pair validation. Summary now preserves JSON precision
and scores use17significantdigits. Matching and tolerance are unchanged. After
pulling the fix, rerun into a fresh directory from saved imputations; do not reuse
or overwrite failed outputs.
