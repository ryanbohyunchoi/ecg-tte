# Adapted COMET baseline table — declared 33-variable target

2026-09-21. This specifies the extraction target in response to the user's request for a clean PSM table. It supersedes the open-ended feature inventory for primary extraction. It is not evidence that all33 variables are available, validated or sufficient to control confounding. Actual model readiness, transformations and missing-data rules remain gated on source review. No feature is dropped automatically to make a model run.

| Group | Count | Variables |
|---|---:|---|
| Demographics/calendar | 3 | Age at index, recorded sex, index year |
| Physiology | 5 | LVEF, systolic BP, diastolic BP, heart rate, BMI |
| Laboratory | 4 | Creatinine, potassium, sodium, hemoglobin |
| Recorded comorbidities | 9 | Ischemic heart disease/MI, AF, hypertension, diabetes, CKD, stroke, COPD/asthma, peripheral arterial disease, valve disease |
| Prior medication orders | 8 | ACE inhibitor, ARB, ARNI, MRA, loop diuretic, SGLT2 inhibitor, digoxin, amiodarone |
| Healthcare use | 4 | Outpatient visits, ED encounters, hospital admissions, HF hospital admissions |

The selection covers proposed confounding and prognostic domains; it is not chosen by treatment-prediction accuracy, p-values or observed treatment effects. See [Brookhart et al., variable selection for propensity scores](https://pmc.ncbi.nlm.nih.gov/articles/PMC1513192/). Domain-specific causal and measurement review is still required;33 is a concrete specification, not a universal recommended count.

## Clean table layout

`baseline_observed.parquet`: one row per eligible, unmatched patient; three metadata fields (`patient_key`, `treatment_arm`, `index_date`) plus exactly33 declared covariates. Treatment is the PS response, not a PS predictor; identifiers are never predictors. Index year is derived deterministically. Sex encoding needs source-label review. The machine-readable field list is in COMET_PSM_TABLE_V1.json. Dummies and nonlinear terms may expand the33 variables into more model coefficients; that encoding is not frozen here.

Keep eligibility status/reasons, phenotype evidence basis (code-only/EF-only/both), source provenance, measurement recency and cell-level missingness reasons in separate companion tables. Eligibility and extraction QC must not accidentally become predictors. Outcomes and follow-up remain separate from PS predictor columns. Any analysis-stage outcome-informed imputation requires its own frozen specification, as described in COMET_MISSING_DATA_PLAN.md; no outcomes are used to tune this feature selection.

## Extraction rules

- Strictly pre-index: latest BP/pulse/labs within90 days; latest BMI/EF within365 days. BP components come from the same validated reading. Missing/invalid latest values never trigger an unreviewed older fallback. Availability timing and canonical units must be validated.
- Comorbidity indicators represent documented evidence in the previous365 days, not lifetime absence or a full clinical diagnosis. Versioned code maps and adequate source coverage are required. A value of0 means no qualifying recorded evidence under that contract; unknown coverage remains null. Stroke history here is a recorded365-day history window, not lifetime ascertainment.
- Medication indicators represent a mapped order in the previous90 days, not active therapy or adherence. The drug class map must include combination products and resolve route/formulation. Calendar-dependent availability and source coverage must be checked before interpreting0. These adjustment windows do not establish the exposure washout rule.
- Utilization counts require validated encounter setting and cross-delivery deduplication. HF admissions are a subset of admissions, not a separate row-count proxy. Retain both for extraction; assess redundancy/support before encoding without automatic feature selection.
- Select creatinine as the primary renal numeric measure. eGFR is an auxiliary pending equation/source validation, not a34th predictor. BNP and NT-proBNP remain separate optional auxiliaries/sensitivity variables; do not merge assays or add them silently. Site, race/ethnicity and other social/contextual variables remain explicit role-review candidates, not assumed irrelevant.

## MICE and readiness

Impute suitable missing covariate cells within the finalized unmatched COMET population, with both arms and treatment in the imputation predictor set. Preserve observed values. Use type-appropriate models; do not apply continuous PMM to every field. Demographic conflicts, unavailable source columns, unknown units, unknown coverage and structural absence need resolution, not automatic imputation. Imputing adjustment EF cannot make a patient eligible by EF.

Four lab predictors currently lack a complete usable lab extension and validated units. Do not synthesize them across an entirely unavailable source. If a declared variable cannot be supported, pause model readiness and explicitly version an adapted feature set; do not silently switch to a no-lab model. Numeric missingness and categorical/count support must be reported by arm/year before the MICE model is finalized. Eligibility and index definitions are also not yet frozen.

The table specification is implemented as documentation/schema only. No patient baseline table, MICE run or PS model has been produced. Clinical-table conversion is the next execution dependency; feature adapters and mapping review remain necessary.
