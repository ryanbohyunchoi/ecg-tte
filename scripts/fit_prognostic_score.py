#!/usr/bin/env python
"""Fit prognostic scores on an external reference set and score a trial cohort.

Inputs are built by the same code for reference and cohort
(build_core_baseline.py observed table + build_preindex_panel.py with the
cohort's dictionary), so feature definitions are identical. No cohort outcome
is read (cohort outcomes are never extracted).

Features: core covariates (reference-median fill + missing indicators; treatment
indicator excluded) and, for prog_full, every panel feature (codes as any-use
indicators, lab values median-filled + measured flags, log1p visit counts).
Models: L2 logistic regression; C for prog_full chosen by 5-fold CV AUC on the
reference training split. 20% of the reference set is held out for AUC.

Outputs: restricted_prognostic_scores.parquet (patient_key, prog_core, prog_full:
linear predictors), metrics.json (reference AUCs, event rate).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler


def core_matrix(obs: pd.DataFrame, med: pd.Series | None = None):
    X = obs.drop(columns=[c for c in ("treated",) if c in obs]).astype(float)
    med = X.median() if med is None else med
    miss = X.isna().astype(float).add_suffix("__missing")
    miss = miss.loc[:, [c for c in miss.columns if c.replace("__missing", "") in med.index]]
    return pd.concat([X.fillna(med), miss], axis=1), med


def panel_matrix(panel: pd.DataFrame, med: pd.Series | None = None):
    P = panel.astype(float)
    code = [c for c in P.columns if c.split("_")[0] in ("dx", "rx", "px")]
    lab = [c for c in P.columns if c.startswith("lab_")]
    vis = [c for c in P.columns if c.startswith("vis_")]
    other = [c for c in P.columns if c.startswith("labn_")]
    med = P[lab].median() if med is None else med
    out = pd.concat([P[code].gt(0).astype(float), P[lab].fillna(med), P[other].fillna(0), np.log1p(P[vis].fillna(0))], axis=1)
    return out, med


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", required=True, help="restricted_reference.parquet (patient_key, outcome)")
    ap.add_argument("--reference-baseline", required=True, help="restricted_baseline_observed.parquet")
    ap.add_argument("--reference-panel", required=True)
    ap.add_argument("--cohort-baseline", required=True, help="restricted_baseline_observed.parquet (OMOP builder)")
    ap.add_argument("--cohort-panel", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--seed", type=int, default=20260923)
    a = ap.parse_args()
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=False, mode=0o700)

    ref = pd.read_parquet(a.reference).set_index("patient_key")
    rb = pd.read_parquet(a.reference_baseline).set_index("patient_key").loc[ref.index]
    rp_ = pd.read_parquet(a.reference_panel).set_index("patient_key").loc[ref.index]
    cb = pd.read_parquet(a.cohort_baseline).set_index("patient_key")
    cp = pd.read_parquet(a.cohort_panel).set_index("patient_key").reindex(cb.index)
    cp = cp.reindex(columns=rp_.columns)
    y = ref.outcome.to_numpy()

    Xc_r, cmed = core_matrix(rb)
    Xc_c, _ = core_matrix(cb[rb.columns], cmed)
    Xp_r, pmed = panel_matrix(rp_)
    Xp_c, _ = panel_matrix(cp, pmed)
    Xf_r, Xf_c = pd.concat([Xc_r, Xp_r], axis=1), pd.concat([Xc_c, Xp_c], axis=1)

    tr, te = train_test_split(np.arange(len(y)), test_size=0.2, random_state=a.seed, stratify=y)
    metrics = dict(n_reference=int(len(y)), event_rate=round(float(y.mean()), 4), n_cohort=int(len(cb)))
    scores = {"patient_key": cb.index.to_numpy()}
    for name, Xr, Xc, grid in (("prog_core", Xc_r, Xc_c, [1.0]), ("prog_full", Xf_r, Xf_c, [0.00003, 0.0001, 0.0003, 0.001, 0.003, 0.01])):
        sc = StandardScaler().fit(Xr.iloc[tr])
        Zr, Zc = sc.transform(Xr), sc.transform(Xc)
        gs = GridSearchCV(LogisticRegression(max_iter=5000), {"C": grid}, scoring="roc_auc", cv=5, n_jobs=len(grid))
        gs.fit(Zr[tr], y[tr])
        m = gs.best_estimator_
        metrics[f"{name}_C"] = gs.best_params_["C"]
        metrics[f"{name}_test_auc"] = round(float(roc_auc_score(y[te], m.decision_function(Zr[te]))), 4)
        metrics[f"{name}_n_features"] = int(Xr.shape[1])
        # refit on the full reference set with the chosen C, then score the cohort
        m = LogisticRegression(C=gs.best_params_["C"], max_iter=5000).fit(StandardScaler().fit(Xr).transform(Xr), y)
        scores[name] = m.decision_function(StandardScaler().fit(Xr).transform(Xc))
        metrics[f"{name}_cohort_mean_risk"] = round(float((1 / (1 + np.exp(-scores[name]))).mean()), 4)
    pd.DataFrame(scores).to_parquet(out / "restricted_prognostic_scores.parquet")
    json.dump(metrics, open(out / "metrics.json", "w"), indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
