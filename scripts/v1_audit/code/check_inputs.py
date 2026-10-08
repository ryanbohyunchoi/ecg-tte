#!/usr/bin/env python
"""v1 audit: per-trial input alignment checks for the paper2 grid (aggregates only; shares, no identifiers).
For each of the 38 trials (sens_primary32.ALL):
  * analysed keys K = completed-covariate keys ∩ ECG emb ∩ CLMBR emb ∩ phenotypes ∩ panel (as v13_common.Trial)
  * ECG embedding duplicate keys; CLMBR duplicate keys and whether duplicated embeddings differ
  * CLMBR index_date == cohort index_date (share mismatched among K)
  * ECG selection lag_days: share on the index day among K; max lag
  * P5 design inputs (covars v1 / covars2b reindexed to K): share of K absent from each file and NaN share per column
    (v18_clmbr.designs applies np.nan_to_num -> silently 0)
  * outcomes: share of K with y_ok False
Writes OUT/inputs.csv (restricted dir) and prints a summary with shares only."""
import os, sys, glob, json
import numpy as np, pandas as pd
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v20"); sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v18")
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts")
import sens_primary32 as SP
from v13_common import A, EXTRA, PRIMARY, paths
import v18_clmbr as C
V = SP.V
OUT = A / "claude-v1-audit" / "code"
rows = []
for n in SP.ALL:
    key, cdir = {**PRIMARY, **EXTRA}[n]
    B = f"{A}/claude-{n}-baseline-v11"
    cov = pd.read_parquet(f"{B}/restricted_completed_01.parquet", columns=["patient_key"]).patient_key
    P = paths(n)
    ecg = pd.concat([pd.read_parquet(f, columns=["patient_key"]) for f in sorted(glob.glob(P["ecg"]))]).patient_key
    ehr = (f"{A}/comet-clmbr-full-NAyb4G2x/report/restricted_embeddings_part-*.parquet" if n == "comet"
           else f"{A}/claude-{n}-clmbr-codeonly/report/restricted_embeddings_part-*.parquet")
    clm = pd.concat([pd.read_parquet(f, columns=["patient_key", "index_date"]) for f in sorted(glob.glob(ehr))])
    ph = pd.read_parquet(P["ph"], columns=["patient_key"]).patient_key
    pan = pd.read_parquet(P["panel"], columns=["patient_key"]).patient_key
    K = pd.Index(cov)
    for ix in (pd.Index(ecg), pd.Index(clm.patient_key), pd.Index(ph), pd.Index(pan)):
        K = K.intersection(ix)
    ro = pd.read_parquet(A / cdir / "restricted_cohort.parquet", columns=["patient_key", "index_date"]).drop_duplicates("patient_key").set_index("patient_key")
    cl1 = clm.drop_duplicates("patient_key").set_index("patient_key")
    mism = (pd.to_datetime(cl1.index_date.reindex(K)) != pd.to_datetime(ro.index_date.reindex(K))).mean()
    dupc = clm.patient_key.duplicated().sum()
    sel = sorted(glob.glob(f"{A}/claude-{n}-bcl/input/restricted_selection.parquet")) or sorted(glob.glob(f"{A}/claude-comet-bcl-v2/input/restricted_selection.parquet"))
    lag0 = lagmax = np.nan
    if sel:
        S = pd.read_parquet(sel[0]).drop_duplicates("patient_key").set_index("patient_key").reindex(K)
        lag0, lagmax = float((S.lag_days == 0).mean()), float(S.lag_days.max())
    d1, d2 = V.cdirs(n)
    C1 = pd.read_parquet(d1 / f"{n}.parquet").set_index("patient_key")
    C2 = pd.read_parquet(d2 / f"{n}.parquet").set_index("patient_key")
    hf = "hf_any_365" if "hf_any_365" in C2 else "elx_chf"
    r = dict(trial=n, in_S32=n in SP.S32, n_keys_ge11=len(K) >= 11, ecg_dup_keys=int(ecg.duplicated().sum()), clm_dup_rows_share=dupc / len(clm),
             clm_index_mismatch_share=float(mism), ecg_index_day_share=lag0, ecg_max_lag=lagmax,
             c1_absent_share=float((~K.isin(C1.index)).mean()), c2_absent_share=float((~K.isin(C2.index)).mean()), hf_col=hf)
    for c in C.P5DX:
        r[f"nan_{c}"] = float(C1[c].reindex(K).isna().mean())
    r[f"nan_hf"] = float(C2[hf].reindex(K).isna().mean())
    O = pd.read_parquet(f"{A}/claude-{n}-outcomes-v1/restricted_outcomes.parquet").set_index("patient_key").reindex(K)
    r["y_not_ok_share"] = float(1 - (O.t_primary.notna() & (O.get("exclude_phase2", 0) == 0)).mean())
    rows.append(r)
    print(n, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != "trial"}, flush=True)
D = pd.DataFrame(rows)
os.umask(0o077); OUT.mkdir(parents=True, exist_ok=True)
D.to_csv(OUT / "inputs.csv", index=False)
print(D.drop(columns=["trial"]).describe().T.round(4).to_string())
