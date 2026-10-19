#!/usr/bin/env python
"""CHS 'crude backbone' AI-EHR representation (EXPLORATORY, post hoc; docs/bdc/CHS_EHR_EXPLORATORY.md).

An unsupervised representation of the same coded information the PS-Codes (hdPS-like) arm uses: per emulation row,
the ICD-9 hospital diagnosis ('D:', 3-digit) and procedure ('P:', 2-digit) codes admitted before the visit k-1 day and
the medication-class flags ('M:') at visit k-1 (chs_cohort.code_features; exposure drugs already excluded).
Representation = TF-IDF (binary, smooth idf) -> truncated SVD (64 components), fitted once on all distinct person-time
rows of all emulations. No treatment, outcome or held-out information enters the fit. Rows without any code get the
zero-input projection.

Input (restricted): chs_emulations, chs_codes. Output (restricted): chs_ehr_backbone.{parquet|pkl} (row, b0..b63) and an
aggregate summary <out>/chs_backbone/report.json (vocabulary size, explained variance; no participant data).
Usage: python scripts/bdc/chs_backbone.py [--dim 64] [--min-df 20]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bdc_common as BC  # noqa: E402


def _read(p: Path) -> pd.DataFrame:
    for q in (p.with_suffix(".parquet"), p.with_suffix(".pkl")):
        if q.exists():
            return pd.read_parquet(q) if q.suffix == ".parquet" else pd.read_pickle(q)
    raise SystemExit(f"missing {p}.parquet/.pkl (run chs_cohort.py first)")


def backbone(R: pd.DataFrame, K: pd.DataFrame, dim: int = 64, min_df: int = 20, seed: int = 20261019):
    from scipy import sparse
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfTransformer
    # distinct person-time: the same person at the same visit k-1 has the same codes in every emulation
    key = R.id.astype(str) + "|" + R.k1.astype(int).astype(str)
    first = pd.Series(R.row.to_numpy(), index=key).groupby(level=0).first()
    rows_u = first.to_numpy()
    k = K[K.row.isin(set(rows_u))]
    df = k.groupby("code").row.nunique()
    vocab = df[df >= min_df].index
    k = k[k.code.isin(vocab)]
    ci = {c: j for j, c in enumerate(vocab)}
    ri = {r: i for i, r in enumerate(rows_u)}
    X = sparse.csr_matrix((np.ones(len(k)), ([ri[r] for r in k.row], [ci[c] for c in k.code])),
                          shape=(len(rows_u), len(vocab)))
    X.data[:] = 1.0
    T = TfidfTransformer(smooth_idf=True, sublinear_tf=False).fit(X)
    dim = max(2, min(dim, len(vocab) - 1))
    svd = TruncatedSVD(n_components=dim, random_state=seed).fit(T.transform(X))
    Z_u = svd.transform(T.transform(X))
    # map every emulation row to its person-time representation
    pos = key.map({kk: i for i, kk in enumerate(first.index)}).to_numpy()
    Z = Z_u[pos]
    out = pd.DataFrame(Z, columns=[f"b{j}" for j in range(dim)])
    out.insert(0, "row", R.row.to_numpy())
    info = dict(person_time_rows=BC.suppress(len(rows_u)), vocabulary=len(vocab), min_df=min_df, dim=dim,
                explained_variance=round(float(svd.explained_variance_ratio_.sum()), 3),
                share_rows_with_any_code=round(float((X.getnnz(axis=1) > 0).mean()), 3),
                code_families={f: int(sum(str(c).startswith(f + ":") for c in vocab)) for f in ("D", "P", "M")})
    return out, info


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dim", type=int, default=64)
    ap.add_argument("--min-df", type=int, default=20)
    a = ap.parse_args(argv)
    t0 = time.time()
    rd = Path(os.environ.get("BDC_RESTRICTED", "/sbgenomics/workspace/bdc-restricted"))
    R = _read(rd / "chs_emulations")
    K = _read(rd / "chs_codes")
    Z, info = backbone(R, K, a.dim, a.min_df)
    try:
        Z.to_parquet(rd / "chs_ehr_backbone.parquet", index=False)
    except Exception:  # noqa: BLE001
        Z.to_pickle(rd / "chs_ehr_backbone.pkl")
    out = BC.out_root() / "chs_backbone"
    out.mkdir(parents=True, exist_ok=True)
    info.update(when=time.strftime("%Y-%m-%d %H:%M"), git=BC.git_sha(), seconds=round(time.time() - t0))
    BC.write_json(out / "report.json", info)
    print(info)


if __name__ == "__main__":
    main()
