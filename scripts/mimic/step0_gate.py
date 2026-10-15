#!/usr/bin/env python
"""Step 0 gate: rebuild the MIMIC PS-CVD5 flags and re-run the PS-CVD5 +/- ECG +/- permuted-ECG analysis from
scratch through scripts/v21/mimic_cvd5.py (imported, output dir redirected to OUT/step0), then require

  1. the flags and every results/<k>_{arms,vars}.csv cell equal to the v21 outputs (max |diff| 0, same NaN pattern);
  2. the docs/v21/MIMIC_PAPER2.md headline: 6.6% (2.3-12.8), 6/7 lower, sign-flip P .016; % < 0.1 45.6 -> 51.6;
     permuted ECG -3.1% (v20 bootstrap convention: 2,000 resamples, seed 0, as published).

Writes OUT/step0/gate.json and PASS or FAIL. Aggregates only.
"""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

from mimic_common import OUT, V21, status
import mimic_cvd5 as C5  # noqa: E402
import mimic_summary as MS  # noqa: E402

S0 = OUT / "step0"
EXPECT = dict(relred=6.6, ci=(2.3, 12.8), lower="6/7", p_smd=0.016, pct0=45.6, pct1=51.6, relred_perm=-3.1)


def _flags(k):
    return C5.flags(k)


def _analyze(k):
    return C5.analyze(k)


def compare_tables():
    rows = []
    for k in C5.TRIALS:
        f_old = pd.read_parquet(V21 / "flags" / f"{k}.parquet").set_index("pid").sort_index()
        f_new = pd.read_parquet(S0 / "flags" / f"{k}.parquet").set_index("pid").sort_index()
        same = f_old.index.equals(f_new.index) and list(f_old.columns) == list(f_new.columns)
        rows.append(dict(trial=k, table="flags", same_rows=same,
                         max_abs_diff=float((f_old - f_new).abs().max().max()) if same else np.inf, nan_equal=same))
        for kind in ("arms", "vars"):
            a = pd.read_csv(V21 / "results" / f"{k}_{kind}.csv")
            b = pd.read_csv(S0 / "results" / f"{k}_{kind}.csv")
            same = a.shape == b.shape and list(a.columns) == list(b.columns)
            num = a.select_dtypes("number").columns
            d = float((a[num] - b[num]).abs().max().max()) if same else np.inf
            nan_eq = bool((a[num].isna() == b[num].isna()).all().all()) if same else False
            obj = [c for c in a.columns if c not in num]
            txt = bool((a[obj].fillna("") == b[obj].fillna("")).all().all()) if same else False
            rows.append(dict(trial=k, table=kind, same_rows=same and txt, max_abs_diff=d, nan_equal=nan_eq))
    return pd.DataFrame(rows)


def headline():
    # the published table row (MIMIC_PAPER2.md section 3) is mimic_summary.balance (trials in sorted order for the
    # v20 bootstrap); mimic_cvd5.contrast resamples in another trial order and gives a slightly different CI
    A = C5.load()
    b = MS.balance(A, MS.SETS["primary7"], "cvd5", "all")
    got = dict(relred=round(b["relred_ECG"], 1), ci=tuple(round(x, 1) for x in b["relred_ECG_ci"]), lower=b["lower_smd_ECG"],
               p_smd=round(b["p_smd_ECG"], 3), pct0=round(b["pct_bal_base"], 1), pct1=round(b["pct_bal_ECG"], 1),
               relred_perm=round(b["relred_permECG"], 1))
    return got, got == EXPECT


def main():
    C5.OUT = S0  # flags, results and summary of the re-run go to the new audit dir (fork inherits this)
    S0.mkdir(parents=True, exist_ok=True)
    if "--reuse" not in sys.argv:
        ch = [_flags(k) for k in C5.TRIALS]
        pd.DataFrame(ch).to_csv(S0 / "flags" / "flag_check.csv", index=False)
        with Pool(8) as p:
            p.map(_analyze, C5.TRIALS)
    T = compare_tables()
    exact = bool(T.same_rows.all() and (T.max_abs_diff == 0).all() and T.nan_equal.all())
    got, ok_head = headline()
    ok = exact and ok_head
    res = dict(tables_exact=exact, n_tables=len(T), max_abs_diff=float(T.max_abs_diff.max()), headline=got,
               expected=EXPECT, headline_exact=ok_head, gate="PASS" if ok else "FAIL")
    T.to_csv(S0 / "gate_tables.csv", index=False)
    json.dump(res, open(S0 / "gate.json", "w"), indent=1, default=str)
    for f in ("PASS", "FAIL"):
        (S0 / f).unlink(missing_ok=True)
    (S0 / res["gate"]).write_text(json.dumps(res, default=str))
    print(json.dumps(res, indent=1, default=str))
    status(f"step 0 gate {res['gate']}: {len(T)} flag/arms/vars tables vs v21 max |diff| {res['max_abs_diff']}; "
           f"headline {got}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
