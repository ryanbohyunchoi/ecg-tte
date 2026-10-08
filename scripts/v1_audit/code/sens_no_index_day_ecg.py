#!/usr/bin/env python
"""v1 audit: YNHHS analogue of the MIMIC-IV 'excluding index-day ECGs' sensitivity (not run in v1 for YNHHS).
For each S32 trial: rows = analysed patients whose selected ECG is >= 1 day before index (BCL selection lag_days >= 1);
P5 base / +ECG / +shufECG / +CLMBR / +ECG+CLMBR, main configuration, E.run_cell on those rows (PCs as in v1: fitted on the
full trial cohort, unsupervised). Same rows for every arm, so the contrast is paired. Also the full-cohort contrast for
reference. Aggregates only -> OUT/sens_no_index_day_ecg.csv (per-trial m54 / loghr, restricted dir) and printed summary."""
import os, sys, glob
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import numpy as np, pandas as pd
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v21")
import paper2_grid as G
SP, E, C = G.SP, G.E, G.C
A = SP.A
OUT = A / "claude-v1-audit" / "code"
ARMS = ["base", "ECG", "shufECG", "CLMBR", "ECG+CLMBR"]

def task(n):
    T = E.load_trial(n) if n in SP.AF.V.OLD else E.load_trial(n, cache=False)
    sel = A / ("claude-comet-bcl-v2" if n == "comet" else f"claude-{n}-bcl") / "input" / "restricted_selection.parquet"
    lag = pd.read_parquet(sel).drop_duplicates("patient_key").set_index("patient_key").lag_days.reindex(T.keys).to_numpy()
    rows = np.where(lag >= 1)[0]
    b5, _, _ = C.designs(T, n, C.P5DX)
    blk = {"base": [], "ECG": [T.ecg_pc], "shufECG": [T.ecg_pc[T.shuffle_perm]], "CLMBR": [T.clm_pc], "ECG+CLMBR": [T.clm_pc, T.ecg_pc]}
    out = []
    for a in ARMS:
        X = np.hstack([b5] + blk[a])
        o = E.run_cell(T, X[rows], rows=rows, cstat=None)
        out.append(dict(trial=n, arm=a, share_kept=len(rows) / len(T.t), loghr=o["loghr"], se=o["se"], rb=T.rb,
                        n_pairs_ge11=o["n_pairs"] >= 11, **{f"smd:{c}": o[f"smd:{c}"] for c in G.NONCODED}))
    print(n, "done", flush=True)
    return out

if __name__ == "__main__":
    from multiprocessing import Pool
    with Pool(16) as p:
        res = p.map(task, SP.S32, chunksize=1)
    D = pd.DataFrame([x for r in res for x in r])
    os.umask(0o077); OUT.mkdir(parents=True, exist_ok=True)
    D.to_parquet(OUT / "restricted_sens_no_index_day_ecg.parquet")
    cols = [f"smd:{c}" for c in G.NONCODED]
    S = {a: D[D.arm == a].set_index("trial")[cols].abs() for a in ARMS}
    R = pd.read_parquet(G.OUT / "restricted_cells.parquet")
    R = R[(R.rung == "P5") & (R.config == "main")]
    F = {a: R[R.arm == a].set_index("trial").loc[SP.S32, cols].abs() for a in ARMS}
    rows = []
    for lab, src in (("full cohort (published)", F), ("ECG >= 1 day before index", S)):
        for a in ARMS[1:]:
            Sa, Sb = src[a].loc[SP.S32], src["base"].loc[SP.S32]
            m = Sa.isna() | Sb.isna()
            e, lo, hi, k = SP.relred_ci(Sb.mask(m).mean(1), Sa.mask(m).mean(1))
            d = (Sb.mask(m).mean(1) - Sa.mask(m).mean(1)).to_numpy()
            rows.append(dict(population=lab, contrast=f"P5: {a} vs base", relred54=e, lo=lo, hi=hi, k=k,
                             better=f"{int((d > 0).sum())}/{int(np.isfinite(d).sum())}", p_one_sided=SP.p1s(d)))
    Ssum = pd.DataFrame(rows)
    Ssum.to_csv(OUT / "sens_no_index_day_ecg.csv", index=False)
    print("share of analysed patients kept: median", round(D.groupby("trial").share_kept.first().median(), 3),
          "range", round(D.groupby("trial").share_kept.first().min(), 3), "-", round(D.groupby("trial").share_kept.first().max(), 3))
    print("all cells >= 11 pairs:", bool(D.n_pairs_ge11.all()))
    print(Ssum.round(3).to_string(index=False))
