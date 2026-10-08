#!/usr/bin/env python
"""v1 audit (claims recheck): independent recompute of the paper2 plasmode claims (paper2.md l.59, l.123, l.203, l.218)
from the replicate-level outputs, without calling g2b_simulation_ext.pooled / paper2_plasmode.summarize.

Inputs (read only):
  claude-v20-g2-ext/reps_trtC_adv.csv (LVEF, eGFR) and reps_trtC.csv (NT-proBNP, BMI)      existing arms
  claude-v21-paper2/plasmode/reps_trtC_adv_p5.csv and reps_trtC_p5.csv                    new PS-CVD5 / CLMBR-T arms
  claude-v19-g2-simulation/excluded_cells.csv; claude-v21-paper2/plasmode/r2_p5.csv
Definitions re-implemented from the manuscript text / docs: err = loghr - truth; null-corrected err = err(scenario) -
err(null scenario, same trial x conf x rep, same arm); % bias removed = 100 * (1 - sum over cells of cell-mean err (arm) /
sum of cell-mean err (reference)), cells = trial x conf x non-null (OR_T, HR_Y); coverage = |err| <= 1.96 se.
MCSE: own bootstrap of replicates within cells (seed 12345, 400 resamples; approximate check of the reported MCSE).
Output: /mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/claims/plasmode_recheck.csv (aggregates only).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = A / "claude-v1-audit" / "claims"
DESIGN = {"trtC_adv": ["lvef", "egfr"], "trtC": ["ntprobnp", "bmi"]}


def load():
    parts = []
    for v, confs in DESIGN.items():
        for f in (A / "claude-v20-g2-ext" / f"reps_{v}.csv", A / "claude-v21-paper2" / "plasmode" / f"reps_{v}_p5.csv"):
            d = pd.read_csv(f, usecols=["trial", "conf", "or_t", "hr_y", "rep", "arm", "loghr", "se", "truth"])
            parts.append(d[d.conf.isin(confs)])
    R = pd.concat(parts, ignore_index=True)
    ex = pd.read_csv(A / "claude-v19-g2-simulation" / "excluded_cells.csv")
    R = R.merge(ex.assign(_x=1), on=["trial", "conf"], how="left")
    R = R[R._x.isna()].drop(columns="_x")
    R["err"] = R.loghr - R.truth
    return R


def main():
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    R = load()
    rows = []
    cells = R[["trial", "conf"]].drop_duplicates()
    rows.append(dict(item="n trial x conf cells", value=len(cells)))
    rows.append(dict(item="n trials", value=cells.trial.nunique()))
    for c, g in cells.groupby("conf"):
        rows.append(dict(item=f"n cells {c}", value=len(g)))
    rows.append(dict(item="replicates per cell (max)", value=int(R.rep.max() + 1)))
    W = R.pivot_table(index=["trial", "conf", "or_t", "hr_y", "rep"], columns="arm", values="err").reset_index()
    nul = W[W.or_t == 1.0].drop(columns=["or_t", "hr_y"]).set_index(["trial", "conf", "rep"])
    nn = W[W.or_t != 1.0].set_index(["trial", "conf", "rep"])
    arms = [a for a in W.columns if a not in ("trial", "conf", "or_t", "hr_y", "rep")]
    NC = nn[arms] - nul.reindex(nn.index)[arms]
    NC[["or_t", "hr_y"]] = nn[["or_t", "hr_y"]]
    NC = NC.reset_index()
    RAW = nn.reset_index()
    rows.append(dict(item="n non-null scenario cells (trial x conf x scenario)", value=RAW.groupby(["trial", "conf", "or_t", "hr_y"]).ngroups))
    pairs = {"P5 vs unmatched": ("unmatched", "P5"), "base vs unmatched": ("unmatched", "base"),
             "P5ECGCLMBR vs unmatched": ("unmatched", "P5ECGCLMBR"), "oracle vs unmatched": ("unmatched", "oracle"),
             "P5ECG vs unmatched": ("unmatched", "P5ECG"), "P5CLMBR vs unmatched": ("unmatched", "P5CLMBR"),
             "ECG over P5": ("P5", "P5ECG"), "CLMBR over P5": ("P5", "P5CLMBR"), "both over P5": ("P5", "P5ECGCLMBR"),
             "shufCLMBR over P5": ("P5", "P5shufCLMBR"), "ECG over P5+CLMBR": ("P5CLMBR", "P5ECGCLMBR")}
    rng = np.random.default_rng(12345)
    for lab, D in (("raw", RAW), ("null-corrected", NC)):
        for conf in ["lvef", "ntprobnp", "bmi", "egfr", "all"]:
            d = D if conf == "all" else D[D.conf == conf]
            grp = d.groupby(["trial", "conf", "or_t", "hr_y"])
            cm = grp[arms].mean().sum()
            arrs = [g[arms].to_numpy() for _, g in grp] if conf == "all" else None
            for nm, (ref, arm) in pairs.items():
                val = 100 * (1 - cm[arm] / cm[ref])
                r = dict(item=f"% removed {nm} [{lab}, {conf}]", value=round(val, 3))
                if arrs is not None and lab == "null-corrected" and "over" in nm:
                    i, j = arms.index(arm), arms.index(ref)
                    bs = []
                    for _ in range(400):
                        s = np.sum([g[rng.integers(0, len(g), len(g))].mean(0) for g in arrs], axis=0)
                        bs.append(100 * (1 - s[i] / s[j]))
                    r["mcse"] = round(float(np.std(bs, ddof=1)), 3)
                rows.append(r)
    # coverage (raw, non-null cells), mean over cells
    Rn = R[R.or_t != 1.0].copy()
    Rn["cover"] = np.where(Rn.se.notna(), (Rn.err.abs() <= 1.96 * Rn.se).astype(float), np.nan)
    cov = Rn.groupby(["arm", "trial", "conf", "or_t", "hr_y"]).cover.mean().groupby("arm").mean() * 100
    for a, v in cov.items():
        rows.append(dict(item=f"coverage % {a}", value=round(v, 2)))
    rows.append(dict(item="coverage range non-oracle arms", value=f"{cov.drop('oracle').min():.1f}-{cov.drop('oracle').max():.1f}"))
    # real-data cross-fitted R2 (cell means)
    r2 = pd.read_csv(A / "claude-v21-paper2" / "plasmode" / "r2_p5.csv")
    r2 = r2.merge(pd.read_csv(A / "claude-v19-g2-simulation" / "excluded_cells.csv").assign(_x=1), on=["trial", "conf"], how="left")
    r2 = r2[r2._x.isna()]
    rows.append(dict(item="r2 cells", value=len(r2)))
    for c in ("egfr", "lvef"):
        g = r2[r2.conf == c]
        rows.append(dict(item=f"R2 {c} CLMBR", value=round(g.r2_clm.mean(), 3)))
        rows.append(dict(item=f"R2 {c} ECG", value=round(g.r2_ecg.mean(), 3)))
    D = pd.DataFrame(rows)
    D.to_csv(OUT / "plasmode_recheck.csv", index=False)
    pd.set_option("display.width", 200, "display.max_rows", 500)
    print(D.to_string(index=False))


if __name__ == "__main__":
    main()
