# Proposed COMET missing-covariate approach

2026-09-20: proposed, not frozen or implemented. First define the cohort and audit
pre-index covariate missingness by arm/year/site and source coverage. Separate
unmeasured, uncaptured, invalid and structural absence. Do not impute eligibility,
treatment, outcomes, or an absent imaging modality to create cohort membership.

Preferred candidate: multiple imputation by chained equations (MICE), using
predictive mean matching for suitable continuous variables and appropriate
binary/categorical models. PMM uses observed donor values but still needs adequate
donors, compatible models, missing-at-random assumptions and sensitivity analysis.
Mean replacement shrinks variance/relationships and does not represent uncertainty.
Clustering-based single imputation is not proposed as the primary inferential method.

Include treatment and relevant baseline/auxiliary predictors. Outcome information
may be needed in an analysis-stage imputation model for valid inference; keep that
frozen analysis separate from outcome-blind design/method selection and pre-index
representation construction. Retain an outcome-free sensitivity. Decide the number
of imputations using missing-information/Monte Carlo diagnostics, not a fixed
universal number. Check convergence, clinical ranges, donor support and observed
versus imputed distributions by arm. Missing-not-at-random sensitivity is required
where plausible; MI cannot fix an entirely absent confounder source.

Estimate PS and perform matching separately within each completed dataset; pool
treatment effects with a justified matched-data variance/MI procedure. Do not
average propensity scores and match once. Matching retention and target-population
changes across imputations need explicit handling before freezing this approach.
Do not simply invoke Rubin pooling without validating the full estimator. Compare
complete-case results as sensitivity where feasible, not as an unbiased reference.

References:
- https://www.jstatsoft.org/article/view/v045i03
- https://journals.sagepub.com/doi/10.1177/0962280217713032
The latter primarily studies IPTW; it is not proof of every matching+MI pipeline.
