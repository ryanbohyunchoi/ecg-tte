# COMET MICE preparation

Apply user-approved cleaning first. This is implemented preparation, not a MICE run.
No patient is excluded: DBP exactly zero and BMI below1 or above1000 become missing.
Raw values remain in the immutable parent and private cell change log. Other extremes
are not changed. No unit conversion or measurement validation is inferred.

```bash
cd "$HOME/github/ecg-tte"
git pull --ff-only origin psm-mice-imputation
umask 077
COMET_MICE_PREP=$(mktemp -d /mnt/raid0/rbc58/ecg-tte/audits/comet-mice-prep-XXXXXXXX)
python scripts/prepare_comet_mice.py --output-dir "$COMET_MICE_PREP/report"
cat "$COMET_MICE_PREP/report/summary.json"
```

Discovery requires exactly one complete calendar report; otherwise pass its explicit
absolute directory using --source-report. All patient artifacts stay on H100.
Expected roster7499 unchanged and5 cells cleaned; expectations are checks against
reviewed aggregates, not enforced counts for future compatible cohorts.

## Proposed diagnostic pilot — not yet implemented or final analysis

Use the selected cohort, both arms with treatment as a fixed predictor; exclude
identifiers, post-index variables and endpoints from this outcome-blind pilot.
Use predictive mean matching for continuous measurements and suitable categorical
models for incomplete binary/categorical recorded-evidence features. Never impute
treatment, index dates, eligibility or reinterpret recorded absence as confirmed
absence. Complete baseline variables are predictors, not imputation targets.

Start with5 imputations and20 iterations as a diagnostic run, not a final precision
choice. Review chains, logged events, observed/imputed distributions by arm and
calendar, donor support, joint missingness, and unexpected BP relationships. Do not
silently drop singular predictors or reinterpret convergence as proof of missing at
random. Specify a larger final run using diagnostics and Monte Carlo precision.

All32 candidate features still need explicit type/coding and predictor specifications.
The preparation report now includes missingness for all32, not only numeric fields.
Source units remain assumptions, and high missingness requires sensitivity analyses.
Upper index-date/follow-up eligibility must be finalized before definitive analysis.
An outcome-blind pilot is not automatically the final effect-analysis imputation
model; outcome compatibility needs a separate statistical specification.

Primary references: https://amices.org/mice/reference/mice and
https://amices.org/mice/reference/convergence.html .
