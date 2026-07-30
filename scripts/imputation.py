"""
imputation.py

Multiple imputation (MICE) of missing CONTINUOUS baseline covariates for the
stage-4 comparator ladder. Follows the TTE-standard "within" approach
(Leyrat 2019; RCT-DUPLICATE): impute → match → estimate within each of m
completed datasets, then pool effects with Rubin's rules (see
stage4_analyze.pool_rubin). This module only produces the m completed
datasets; matching and pooling live in stage4.

Statistical guardrails
-----------------------
- Structurally-complete binaries are NEVER imputed. Comorbidity / medication /
  ICD-proxy flags encode absence as literal 0 (cohort_utils.py:1304,1381); they
  carry no NaN, and imputing them would fabricate comorbidities. Only continuous
  covariates with real NaN (echo EF, ECG intervals, labs, vitals) are imputed.
- The imputation model includes treatment and a proper survival-outcome summary
  (event indicator + Nelson-Aalen cumulative baseline hazard H0(t); White &
  Royston 2009) as predictors, so covariate-treatment and covariate-outcome
  associations are preserved. The outcome / follow-up time themselves are never
  imputed or overwritten.
- A missing-indicator is added for informative-missingness covariates
  (ef_at_index: echo-not-ordered is clinically informative / MNAR-ish). The
  value is still imputed; the indicator carries the informativeness. This is a
  documented EHR design choice layered on top of MICE, not RCT-orthodox.
- Labs/vitals already ship {name}_measured indicators from
  cohort_utils.load_measurement — those are reused, not duplicated here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# IterativeImputer is experimental — the enable_* import MUST precede it.
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

from balance import _is_binary

# ── Covariate classification ──────────────────────────────────────────────────

# Continuous covariates that carry TRUE missingness (NaN = not measured).
CONTINUOUS_MISSING: list[str] = [
    # Echo
    "ef_at_index",
    # ECG intervals
    "hr_at_index", "RR_Interval", "PR_Interval", "QRS_Duration",
    "QTc", "QT_Interval", "QRS_Axis", "P_Axis", "T_Axis",
    # Labs (wired in via stage1 --measurement-dir)
    "lab_egfr", "lab_creatinine", "lab_chol_total", "lab_hdl", "lab_hba1c",
    # Vitals
    "vital_sbp", "vital_bmi",
]

# Covariates whose missingness is itself informative → add {col}_missing indicator.
MISSING_INDICATOR_COVS: list[str] = ["ef_at_index"]


def split_covariates(
    df: pd.DataFrame, covariates: list[str]
) -> tuple[list[str], list[str]]:
    """
    Partition `covariates` into (passthrough, to_impute).

    to_impute  = present columns that are in CONTINUOUS_MISSING, OR are
                 non-binary (per balance._is_binary) AND contain >=1 NaN.
    passthrough = the remainder (structurally-complete 0-encoded binaries and
                 continuous columns that happen to have no missing values).
    """
    present = [c for c in covariates if c in df.columns]
    to_impute: list[str] = []
    passthrough: list[str] = []
    for c in present:
        col = df[c]
        has_nan = bool(col.isna().any())
        vals = col.dropna().values
        binary = _is_binary(vals, vals) if len(vals) else True
        if c in CONTINUOUS_MISSING or (not binary and has_nan):
            to_impute.append(c)
        else:
            passthrough.append(c)
    return passthrough, to_impute


def add_missing_indicators(
    df: pd.DataFrame, cols: list[str] = MISSING_INDICATOR_COVS
) -> tuple[pd.DataFrame, list[str]]:
    """
    Add a {col}_missing binary indicator for each present col with >=1 NaN,
    computed BEFORE imputation so it reflects true missingness. Returns
    (df_with_indicators, added_column_names).
    """
    df = df.copy()
    added: list[str] = []
    for c in cols:
        if c not in df.columns:
            continue
        ind = f"{c}_missing"
        df[ind] = df[c].isna().astype(int)
        # Only keep the indicator if it actually varies (some missingness present).
        if df[ind].nunique() > 1:
            added.append(ind)
        else:
            df.drop(columns=[ind], inplace=True)
    return df, added


def _outcome_predictors(
    df: pd.DataFrame, event_col: str | None, time_col: str | None
) -> pd.DataFrame:
    """
    Correct survival-outcome terms for the imputation predictor matrix
    (White & Royston 2009): the event indicator plus the Nelson-Aalen estimate
    of the cumulative baseline hazard H0(t) evaluated at each subject's time.
    Raw follow-up time is NOT used directly. Returns a complete 2-col frame; an
    empty frame if the outcome columns are absent or lifelines is unavailable.
    """
    if not event_col or not time_col:
        return pd.DataFrame(index=df.index)
    if event_col not in df.columns or time_col not in df.columns:
        return pd.DataFrame(index=df.index)
    event = pd.to_numeric(df[event_col], errors="coerce").fillna(0).astype(float)
    time = pd.to_numeric(df[time_col], errors="coerce")
    time = time.fillna(time.median() if time.notna().any() else 0.0).clip(lower=0.0)
    try:
        from lifelines import NelsonAalenFitter
        naf = NelsonAalenFitter()
        naf.fit(time.values, event_observed=event.values)
        h0 = naf.cumulative_hazard_at_times(time.values).values
    except Exception:
        # Fallback: rank-transformed time (monotone in H0) keeps the outcome
        # association without the lifelines dependency.
        h0 = time.rank(method="average").values / max(len(time), 1)
    return pd.DataFrame(
        {"_na_cumhaz": np.asarray(h0, dtype=float), "_event": event.values},
        index=df.index,
    )


def make_imputations(
    df: pd.DataFrame,
    covariates: list[str],
    n_imputations: int = 1,
    seed: int = 42,
    treatment_col: str = "arm",
    treated_arm: str = "carvedilol",
    event_col: str | None = None,
    time_col: str | None = None,
    add_indicator_for: list[str] = MISSING_INDICATOR_COVS,
    max_iter: int = 10,
) -> tuple[list[pd.DataFrame], list[str]]:
    """
    Produce m completed copies of `df` with missing CONTINUOUS covariates
    imputed by MICE (sklearn IterativeImputer, one proper draw per copy).

    Returns (list_of_m_frames, added_indicator_cols). The added indicator
    columns should be appended to the covariate set used for PS/balance by the
    caller. Passthrough binaries, treatment, and the outcome are restored to
    their originals in every returned frame — only `to_impute` cells change.

    n_imputations <= 1 returns a single deterministic pass (callers route the
    m==1 backward-compat path to complete-case and normally do not call this).
    """
    df = df.copy().reset_index(drop=True)
    df, added_ind = add_missing_indicators(df, add_indicator_for)

    passthrough, to_impute = split_covariates(df, covariates)
    if not to_impute:
        # Nothing to impute — return m identical frames (indicators already added).
        return [df.copy() for _ in range(max(n_imputations, 1))], added_ind

    # Predictor matrix: columns to impute + passthrough binaries + treatment
    # + Nelson-Aalen outcome terms. Only `to_impute` columns are written back.
    treat = (df[treatment_col] == treated_arm).astype(float).rename("_treat")
    outcome = _outcome_predictors(df, event_col, time_col)
    # All passthrough columns are complete (binaries + no-NaN continuous) and
    # numeric-coercible, so they serve as auxiliary predictors for the imputer.
    predictor_cols = to_impute + passthrough
    base = df[predictor_cols].apply(pd.to_numeric, errors="coerce")
    base = base.replace([np.inf, -np.inf], np.nan)
    aux = pd.concat([treat, outcome], axis=1)
    matrix = pd.concat([base, aux], axis=1)
    impute_idx = [matrix.columns.get_loc(c) for c in to_impute]

    m = max(n_imputations, 1)
    frames: list[pd.DataFrame] = []
    for i in range(m):
        imp = IterativeImputer(
            max_iter=max_iter,
            sample_posterior=(m >= 2),
            random_state=seed + i,
        )
        filled = imp.fit_transform(matrix.values)
        out = df.copy()
        for col, j in zip(to_impute, impute_idx):
            out[col] = filled[:, j]
        frames.append(out)
    return frames, added_ind
