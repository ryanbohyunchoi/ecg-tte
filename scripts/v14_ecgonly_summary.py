#!/usr/bin/env python
"""v1.4 post-hoc F: how much confounding does the ECG capture on its own? Markdown to stdout, CSV to docs/v14/."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import TRIALS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402
from v13_summarize import bootstrap, md, plasmode  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "v14"
F = "claude-v14-ecgonly"
ARMS = ["unmatched", "demo", "ECGonly", "demo+ECG", "sparse", "sparse+ECG", "clinical (reference)", "R+"]
LAB = {"unmatched": "Unadjusted", "demo": "Demographics only", "ECGonly": "ECG only", "demo+ECG": "Demographics + ECG",
       "sparse": "Sparse (demo + dx)", "sparse+ECG": "Sparse + ECG", "clinical (reference)": "Clinical PS", "R+": "R+ physiology ref"}
PAIRS = [("ECG only vs unadjusted", "ECGonly", "unmatched"), ("ECG only vs demographics", "ECGonly", "demo"),
         ("Demographics + ECG vs demographics", "demo+ECG", "demo"), ("ECG only vs sparse", "ECGonly", "sparse"),
         ("Demographics + ECG vs sparse", "demo+ECG", "sparse"), ("Sparse + ECG vs sparse", "sparse+ECG", "sparse")]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    trials = [n for n in {**PRIMARY, **EXTRA} if (A / F / f"bs_{n}.csv").exists()]
    key = {n: k for n, (k, _) in {**PRIMARY, **EXTRA}.items()}
    rng = np.random.default_rng(7)
    print(f"# v1.4 post-hoc F — the ECG on its own ({len(trials)} trials; exploratory)\n")
    # point estimates (bootstrap replicate 0 = full cohort, imputation 1)
    rows = []
    for n in trials:
        P = pd.read_csv(A / F / f"bs_{n}.csv")
        P = P[P.rep == 0].set_index("arm")
        b, se = bench(key[n])
        for a in ARMS:
            if a in P.index:
                x, s = P.loc[a, "loghr"], P.loc[a, "se"]
                rows.append(dict(trial=n, role=TRIALS[key[n]].get("role"), arm=a, loghr=x, hr=np.exp(x),
                                 d_rct=abs(x - b), d_rplus=abs(x - P.loc["R+", "loghr"]), std_ok=abs((x - b) / np.sqrt(s ** 2 + se ** 2)) < 1.96,
                                 est_ok=(b - 1.96 * se) <= x <= (b + 1.96 * se)))
    D = pd.DataFrame(rows)
    D.to_csv(OUT / "ecgonly_point.csv", index=False)
    for grp, sub in (("all", D), ("physiology", D[D.role == "physiology"]), ("control", D[D.role == "control"])):
        g = sub.groupby("arm").agg(trials=("trial", "nunique"), mean_abs_vs_RCT=("d_rct", "mean"), mean_abs_vs_Rplus=("d_rplus", "mean"),
                                   estimate_agreement=("est_ok", "sum"), std_diff_agreement=("std_ok", "sum")).reindex(ARMS).reset_index()
        g["arm"] = g.arm.map(LAB)
        print(f"## Agreement ({grp} trials; imputation 1 point estimates)\n")
        print(md(g, 3) + "\n")
    # plasmode
    S, C = plasmode(trials, rng, f"{F}/pl")
    if S is not None:
        P = S.groupby(["scenario", "arm"]).agg(mean_abs_bias=("bias", lambda v: np.mean(np.abs(v))), mean_rmse=("rmse", "mean"),
                                               coverage=("coverage", "mean")).reset_index()
        P.to_csv(OUT / "ecgonly_plasmode_bias.csv", index=False)
        print("## Plasmode: mean |bias| by arm (true conditional HR 0.8; 1.0 in null)\n")
        W = P.pivot(index="arm", columns="scenario", values="mean_abs_bias").reindex(ARMS)
        W.index = W.index.map(LAB)
        print(md(W.reset_index(), 3) + "\n")
        base = P[P.scenario == "base"].set_index("arm").mean_abs_bias
        print(f"Share of the unadjusted bias removed (base scenario): " + "; ".join(
            f"{LAB[a]} {100 * (1 - base[a] / base['unmatched']):.0f}%" for a in ARMS if a in base and a != "unmatched") + "\n")
        # contrasts with MC CIs
        from v13_summarize import CONTRASTS  # noqa: F401
        per = {}
        for n in trials:
            f = A / F / "pl" / f"reps_{n}.csv"
            if not f.exists():
                continue
            R = pd.read_csv(f, keep_default_na=False, na_values=[""])
            T = pd.read_csv(A / F / "pl" / f"truth_{n}.csv", keep_default_na=False, na_values=[""])
            R = R.merge(T[["scenario", "arm", "truth_loghr"]], on=["scenario", "arm"])
            R["err"] = R.loghr - R.truth_loghr
            per[n] = {(sc, a): g.sort_values("rep").err.to_numpy() for (sc, a), g in R.groupby(["scenario", "arm"])}
        cr = []
        for sc in ("base", "phys_only", "strong", "null"):
            for lab, a2, a1 in PAIRS:
                pr = [(v[(sc, a1)], v[(sc, a2)]) for v in per.values() if (sc, a1) in v and (sc, a2) in v]
                est = np.mean([abs(np.nanmean(x)) - abs(np.nanmean(y)) for x, y in pr])
                bs = [np.mean([abs(np.nanmean(x[ix])) - abs(np.nanmean(y[ix])) for x, y in pr for ix in [rng.integers(0, len(x), len(x))]])
                      for _ in range(500)]
                cr.append(dict(scenario=sc, contrast=lab, trials=len(pr), bias_reduction=est, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
        CR = pd.DataFrame(cr)
        CR.to_csv(OUT / "ecgonly_plasmode_contrasts.csv", index=False)
        print("Reduction in |bias| (positive = first arm less biased), 95% Monte Carlo CI:\n")
        print(md(CR, 4) + "\n")
    # real-data paired bootstrap
    _, B = bootstrap(trials, rng, targets=("RCT", "R+"), arms_pairs=PAIRS, folder=F)
    if B is not None:
        B.to_csv(OUT / "ecgonly_bootstrap.csv", index=False)
        print("## Real-data paired bootstrap: mean over trials of err(first)² − err(second)² (negative = first closer)\n")
        print(md(B[["target", "contrast", "trials", "mean_d_sqerr", "lo", "hi", "share_trials_closer"]], 4) + "\n")


if __name__ == "__main__":
    main()
