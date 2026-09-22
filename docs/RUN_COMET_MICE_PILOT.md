# COMET diagnostic MICE pilot

Implemented diagnostic pilot only:5 imputations,20 iterations,seed20260922,
5 PMM donors. Cohort stays unchanged. Continuous incomplete variables use PMM;
17 recorded-evidence indicators use logistic imputation when missing. Both arms
are modeled together with fixed treatment as a predictor. Sex is a categorical
predictor using the existing recorded categories, without relabeling. All32
covariates enter the declared model; identifiers, index dates and endpoints do not.
Complete constant columns stay in outputs but are explicitly excluded as predictors.
Unsupported incomplete targets stop instead of becoming silently dropped features.

## H100 run

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
mkdir -p /mnt/raid0/rbc58/ecg-tte/software/R-library /mnt/raid0/rbc58/ecg-tte/software/tmp
export R_LIBS_USER=/mnt/raid0/rbc58/ecg-tte/software/R-library
export TMPDIR=/mnt/raid0/rbc58/ecg-tte/software/tmp
Rscript --vanilla -e 'needed <- c("mice","jsonlite"); absent <- needed[!vapply(needed, requireNamespace, logical(1), quietly=TRUE)]; if(length(absent)) install.packages(absent, repos="https://cloud.r-project.org", lib=Sys.getenv("R_LIBS_USER")); stopifnot(all(vapply(needed, requireNamespace, logical(1), quietly=TRUE)))'
COMET_MICE_RUN=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-pilot-XXXXXXXX)
python scripts/run_comet_mice_pilot.py --output-dir "$COMET_MICE_RUN/report"
cat "$COMET_MICE_RUN/report/summary.json"
```

Requires Rscript plus Python pyarrow already used for preparation. If Rscript is
absent, activate an environment with R before running; this command does not install
R itself. Dependency downloads may need cluster network access/build prerequisites.
No package installations or patient processing occur automatically on the cluster.
Discovery requires one completed preparation; specify --source-report if multiple.
Never print restricted logs/data into chat. Review them locally if a run fails.

## Outputs and interpretation

- Five completed Parquet tables retain exact observed values and immutable roster.
- Restricted R mids object, input, row-key map, original missingness mask and seed.
- Requested vs actual predictors/methods, warnings and MICE logged events.
- Chain plots, traces and lag-1 autocorrelation diagnostic CSV if supported by installed MICE.
  These do not include an R-hat pass/fail declaration.
- Observed/imputed distributions by arm and feature, plus BP-order counts.
- Input/output/code hashes, package version and R session information.

Expected status is complete_pilot_requires_review, never automatic readiness for
PSM or effects. Warnings, removed predictors, poor convergence, sparse donor support,
and SBP<DBP pairs must be reviewed; no silent fallback method or outcome-driven tuning.
The CSV bridge admits only1e-14 floating-point round-trip tolerance; final Parquet
restores exact observed values and exact observed donor values for PMM.

No distributions can prove missing at random. High missingness, unverified source
units, calendar gaps, missingness by treatment and the damaged excluded lab source
remain substantive limitations. This pilot is not the final outcome-compatible
imputation model. Final eligibility/follow-up and imputation precision settings
still need freezing. Matching, balance and effect estimation are separate steps.

References: https://amices.org/mice/reference/mice.html and
https://amices.org/mice/reference/convergence.html .
