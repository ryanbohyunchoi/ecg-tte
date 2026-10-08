#!/usr/bin/env python
"""Step 1: analysed keys for the 38 version 1 trials (restricted, OUT/keys/restricted_keys_<n>.parquet) and the
aggregate share of analysed patients whose selected ECG is on the index day (BCL selection lag_days == 0).
Writes OUT/ecg_index_day.csv (aggregate; no counts of 1-10)."""
import sys
from multiprocessing import Pool

import pandas as pd

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v1_criteria_check")
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v20")
import common as K  # noqa: E402
import sens_primary32 as SP  # noqa: E402


def one(n):
    K.umask()
    D = K.analysed_keys(n)
    assert (D.treated == D.treated_cov).all(), n
    D.to_parquet(K.OUT / "keys" / f"restricted_keys_{n}.parquet")
    sel = K.A / ("claude-comet-bcl-v2" if n == "comet" else f"claude-{n}-bcl") / "input" / "restricted_selection.parquet"
    S = pd.read_parquet(sel).drop_duplicates("patient_key").set_index("patient_key").lag_days.reindex(D.patient_key)
    return dict(trial=n, key=SP.KEY[n], in_S32=n in SP.S32, n_analysed=len(D),
                share_ecg_index_day=round(float((S == 0).mean()), 3),
                share_ecg_1_30d=round(float(((S >= 1) & (S <= 30)).mean()), 3),
                share_ecg_31_365d=round(float(((S > 30) & (S <= 365)).mean()), 3),
                share_ecg_missing_lag=round(float(S.isna().mean()), 3),
                median_lag_days=float(S.median()))


if __name__ == "__main__":
    K.umask()
    with Pool(12) as p:
        rows = p.map(one, SP.ALL, chunksize=1)
    E = pd.DataFrame(rows)
    E.to_csv(K.OUT / "ecg_index_day.csv", index=False)
    print(E.to_string(index=False))
    for s, tr in (("S32", SP.S32), ("S38", SP.ALL)):
        e = E[E.trial.isin(tr)]
        w = (e.share_ecg_index_day * e.n_analysed).sum() / e.n_analysed.sum()
        print(s, "median share index-day", e.share_ecg_index_day.median(), "range", e.share_ecg_index_day.min(), e.share_ecg_index_day.max(),
              "pooled", round(w, 3))
