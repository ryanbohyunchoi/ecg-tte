"""Embedding preprocessing + validation gate for confounder-proxy embeddings.

Why this exists (2026-09-23 COMET audit):
  - BCL lead_time_transformer backbone vectors were all ~the same direction
    (||mean unit vector|| = 0.999995). Raw cosine distance between patients was
    ~1e-7, so cosine matching was effectively random.
  - Even after centering, that embedding predicted sex at AUC 0.70 (a usable
    12-lead model should be >= 0.90), i.e. it carried little clinical signal.

Every embedding must pass `anisotropy_report` + `probe_gate` before it is used
for matching or as a PS covariate. Always use `preprocess` (center -> PCA ->
optional whiten -> L2) instead of L2-normalising raw vectors.

All outputs are aggregate. Never log patient-level rows.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

# Minimum 5-fold linear-probe AUCs. Targets are ones any clinically useful
# 12-lead representation should encode; EHR-model thresholds are looser on sex.
DEFAULT_GATE = {
    "ecg":   {"male": 0.85, "age_ge_65": 0.75, "afib": 0.75, "lvef_le_40": 0.75},
    "ehr":   {"afib": 0.75, "lvef_le_40": 0.65},
}


def anisotropy_report(X: np.ndarray, n_pairs: int = 5000, seed: int = 0) -> dict:
    """Geometry summary. mean_unit_norm near 1 => collapsed/anisotropic space."""
    X = np.asarray(X, dtype=np.float64)
    rng = np.random.default_rng(seed)
    i, j = rng.integers(0, len(X), n_pairs), rng.integers(0, len(X), n_pairs)

    def _pair_q(Z):
        U = Z / np.linalg.norm(Z, axis=1, keepdims=True)
        return np.quantile(1 - (U[i] * U[j]).sum(1), [0.05, 0.5, 0.95]).tolist()

    U = X / np.linalg.norm(X, axis=1, keepdims=True)
    Xc = X - X.mean(0)
    s = np.linalg.svd(Xc, compute_uv=False)
    ev = s ** 2 / np.sum(s ** 2)
    return {
        "n": int(len(X)),
        "dim": int(X.shape[1]),
        "mean_unit_norm": float(np.linalg.norm(U.mean(0))),
        "raw_pair_cosdist_q05_50_95": _pair_q(X),
        "centered_pair_cosdist_q05_50_95": _pair_q(Xc),
        "pcs_for_90pct_var": int(np.searchsorted(np.cumsum(ev), 0.9) + 1),
        "top5_pc_var": ev[:5].round(4).tolist(),
        "collapsed": bool(np.linalg.norm(U.mean(0)) > 0.95),
    }


def preprocess(X: np.ndarray, k: int | None = 32, whiten: bool = True,
               l2: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Center -> PCA(k) -> optional whiten -> optional L2.

    Returns (Z_for_distance, pcs_for_ps_model). `pcs` are unwhitened principal
    component scores, suitable as PS covariates (standardise downstream).
    Fit on the analysis cohort only; no outcome information is used.
    """
    X = np.asarray(X, dtype=np.float64)
    Xc = X - X.mean(0)
    U, S, _ = np.linalg.svd(Xc, full_matrices=False)
    k = min(k or X.shape[1], X.shape[1])
    pcs = U[:, :k] * S[:k]
    Z = U[:, :k] if whiten else pcs
    if l2:
        Z = Z / np.linalg.norm(Z, axis=1, keepdims=True)
    return Z, pcs


def probe_auc(X: np.ndarray, y: np.ndarray, cv: int = 5) -> float:
    y = np.asarray(y).astype(int)
    if y.min() == y.max():
        return float("nan")
    Z = StandardScaler().fit_transform(np.asarray(X, dtype=np.float64))
    clf = LogisticRegression(C=0.1, max_iter=5000)
    return float(cross_val_score(clf, Z, y, cv=cv, scoring="roc_auc").mean())


def probe_gate(X: np.ndarray, labels: pd.DataFrame, modality: str = "ecg",
               thresholds: dict | None = None) -> pd.DataFrame:
    """Linear-probe AUC per label vs threshold. `labels` columns: binary targets
    named as in DEFAULT_GATE (missing columns are skipped)."""
    thr = thresholds or DEFAULT_GATE[modality]
    rows = []
    for name, t in thr.items():
        if name not in labels:
            continue
        m = labels[name].notna().to_numpy()
        auc = probe_auc(np.asarray(X)[m], labels.loc[m, name].to_numpy())
        rows.append({"label": name, "auc": round(auc, 3), "threshold": t,
                     "pass": bool(auc >= t), "n": int(m.sum())})
    return pd.DataFrame(rows)


def labels_from_covariates(cov: pd.DataFrame) -> pd.DataFrame:
    """Build gate labels from a baseline covariate frame (COMET column names)."""
    out = pd.DataFrame(index=cov.index)
    if "recorded_sex" in cov:
        out["male"] = cov["recorded_sex"].astype(str).str.lower().str.startswith("m").astype(float)
    elif "sex_binary" in cov:
        out["male"] = cov["sex_binary"].astype(float)
    if "age_at_index" in cov:
        out["age_ge_65"] = (cov["age_at_index"] >= 65).astype(float)
    for c in ("atrial_fibrillation", "afib"):
        if c in cov:
            out["afib"] = (cov[c] > 0.5).astype(float)
            break
    for c in ("lvef", "echo_ef"):
        if c in cov:
            out["lvef_le_40"] = (cov[c] <= 40).where(cov[c].notna())
            break
    return out
