#!/usr/bin/env python
"""Post-hoc addition I: CLMBR sensitivity analysis + RCT-DUPLICATE-style correlation reporting.

Real data (full-cohort point estimates, imputation 1): RCT-DUPLICATE panel per arm incl. Pearson r of log HRs
(Fisher 95% CI, leave-one-out range), Spearman rho; arm differences in r with 95% CI from resampling TRIALS
(valid: trials are independent); paired exact sign-flip tests on |Δ| and precision-standardised z²; McNemar.
Plasmode (80% subsampling): mean |bias| per arm and bias-reduction contrasts with Monte Carlo CIs.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import TRIALS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402
from v13_summarize import md, plasmode, sign_flip  # noqa: E402
from v14_panel import cat, dl, kappa  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "v14"
F = "claude-v14-clmbr"
ARMS = ["unmatched", "ECGonly", "CLMBR", "CLMBR+ECG", "sparse", "sparse+ECG", "sparse+CLMBR", "sparse+CLMBR+ECG",
        "hdPS200", "hdPS200+ECG", "hdPS200+CLMBR", "hdPS200+CLMBR+ECG", "clinical (reference)", "R+"]
LAB = {"unmatched": "Unadjusted", "ECGonly": "ECG only", "CLMBR": "CLMBR only", "CLMBR+ECG": "CLMBR + ECG", "sparse": "Sparse",
       "sparse+ECG": "Sparse + ECG", "sparse+CLMBR": "Sparse + CLMBR", "sparse+CLMBR+ECG": "Sparse + CLMBR + ECG", "hdPS200": "hdPS200",
       "hdPS200+ECG": "hdPS200 + ECG", "hdPS200+CLMBR": "hdPS200 + CLMBR", "hdPS200+CLMBR+ECG": "hdPS200 + CLMBR + ECG",
       "clinical (reference)": "Clinical PS", "R+": "R+ physiology ref"}
CMP = [("CLMBR", "unmatched"), ("CLMBR", "ECGonly"), ("CLMBR+ECG", "CLMBR"), ("sparse+CLMBR", "sparse"), ("sparse+CLMBR", "sparse+ECG"),
       ("sparse+CLMBR+ECG", "sparse+CLMBR"), ("hdPS200+CLMBR", "hdPS200"), ("hdPS200+CLMBR+ECG", "hdPS200+CLMBR"),
       ("sparse+CLMBR", "clinical (reference)"), ("hdPS200+CLMBR+ECG", "clinical (reference)")]


def fisher_ci(r, n):
    z, se = np.arctanh(r), 1 / np.sqrt(n - 3)
    return np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    names = {**PRIMARY, **EXTRA}
    rows = []
    for n, (k, _) in names.items():
        f = A / F / f"bs_{n}.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f)
        d = d[d.rep == 0].set_index("arm")
        b, se = bench(k)
        for a in ARMS:
            if a in d.index:
                rows.append(dict(trial=n, role=TRIALS[k].get("role"), arm=a, b=d.loc[a, "loghr"], s=d.loc[a, "se"], rb=b, rs=se))
    D = pd.DataFrame(rows)
    trials = sorted(D.trial.unique())
    print(f"# CLMBR sensitivity analysis and RCT-DUPLICATE-style correlation ({len(trials)} trials; post-hoc addition I; exploratory)\n")
    print("CLMBR-T (code-only, 768-d) patient embeddings, 64 PCs, as in the phase-1 grid. Real data: full-cohort estimates (imputation 1).\n")
    rng = np.random.default_rng(11)
    pan = []
    Bt = {a: D[D.arm == a].set_index("trial").reindex(trials) for a in ARMS}
    for a in ARMS:
        g = Bt[a].dropna(subset=["b"])
        b, s, rb, rs = g.b.to_numpy(), g.s.to_numpy(), g.rb.to_numpy(), g.rs.to_numpy()
        r = np.corrcoef(b, rb)[0, 1]
        lo, hi = fisher_ci(r, len(b))
        loo = [np.corrcoef(np.delete(b, i), np.delete(rb, i))[0, 1] for i in range(len(b))]
        ce, cr = cat(b, s), cat(rb, rs)
        mu, sem, Q, I2 = dl(b - rb, s ** 2 + rs ** 2)
        pan.append(dict(arm=LAB[a], trials=len(b), pearson_r=r, r_lo=lo, r_hi=hi, r_loo=f"{min(loo):.2f}–{max(loo):.2f}",
                        spearman=spearmanr(b, rb).statistic, significance_agreement=np.mean(np.where(cr != 0, ce == cr, ce == 0)),
                        estimate_agreement=np.mean(np.abs(b - rb) <= 1.96 * rs), std_diff_agreement=np.mean(np.abs((b - rb) / np.sqrt(s ** 2 + rs ** 2)) < 1.96),
                        ratio_of_ratios=np.exp(mu), dispersion_phi=Q / (len(b) - 1), mean_abs_dlog=np.mean(np.abs(b - rb))))
    P = pd.DataFrame(pan)
    P.to_csv(OUT / "clmbr_panel.csv", index=False)
    print("## RCT-DUPLICATE panel with correlation (Pearson r of log HRs; Fisher 95% CI)\n")
    print(md(P, 2) + "\n")
    # paired comparisons
    pr = []
    for a2, a1 in CMP:
        x, y = Bt[a2], Bt[a1]
        ok = x.b.notna() & y.b.notna()
        x, y = x[ok], y[ok]
        dabs = (x.b - x.rb).abs() - (y.b - y.rb).abs()
        z2 = (x.b - x.rb) ** 2 / (x.s ** 2 + x.rs ** 2) - (y.b - y.rb) ** 2 / (y.s ** 2 + y.rs ** 2)
        rx, ry = np.corrcoef(x.b, x.rb)[0, 1], np.corrcoef(y.b, y.rb)[0, 1]
        idx = np.arange(len(x))
        bs = []
        for _ in range(5000):  # resample trials (independent units)
            j = rng.choice(idx, len(idx))
            if np.std(x.b.to_numpy()[j]) > 0 and np.std(y.b.to_numpy()[j]) > 0 and np.std(x.rb.to_numpy()[j]) > 0:
                bs.append(np.corrcoef(x.b.to_numpy()[j], x.rb.to_numpy()[j])[0, 1] - np.corrcoef(y.b.to_numpy()[j], y.rb.to_numpy()[j])[0, 1])
        ex, ey = np.abs(x.b - x.rb) <= 1.96 * x.rs, np.abs(y.b - y.rb) <= 1.96 * y.rs
        up, dn = int((ex & ~ey).sum()), int((~ex & ey).sum())
        pr.append(dict(comparison=f"{LAB[a2]} vs {LAB[a1]}", trials=int(ok.sum()), closer=f"{int((dabs < 0).sum())}/{int(ok.sum())}",
                       mean_diff_abs=dabs.mean(), p_abs=sign_flip(dabs.to_numpy())[1], mean_diff_z2=z2.mean(), p_z2=sign_flip(z2.to_numpy())[1],
                       diff_pearson_r=rx - ry, r_diff_lo=np.percentile(bs, 2.5), r_diff_hi=np.percentile(bs, 97.5),
                       p_mcnemar_estimate=binomtest(up, up + dn, 0.5).pvalue if up + dn else 1.0))
    Q_ = pd.DataFrame(pr)
    Q_.to_csv(OUT / "clmbr_paired.csv", index=False)
    print("## Paired comparisons (exact sign-flip across trials; r difference CI by resampling trials)\n")
    print(md(Q_, 3) + "\n")
    # plasmode
    S, C = plasmode(trials, rng, f"{F}/pl-ss")
    if S is not None:
        B = S.groupby(["scenario", "arm"]).bias.apply(lambda v: np.mean(np.abs(v))).unstack("scenario").reindex(ARMS)
        B.index = B.index.map(LAB)
        B.to_csv(OUT / "clmbr_plasmode_bias.csv")
        print("## Plasmode (80% subsampling): mean |bias| by arm\n")
        print(md(B.reset_index().rename(columns={"arm": "PS"}), 3) + "\n")
        base = S[S.scenario == "base"].groupby("arm").bias.apply(lambda v: np.mean(np.abs(v)))
        print("Share of unadjusted bias removed (base): " + "; ".join(f"{LAB[a]} {100 * (1 - base[a] / base['unmatched']):.0f}%"
                                                                   for a in ARMS if a in base and a != "unmatched") + "\n")
        per = {}
        for n in trials:
            f = A / F / "pl-ss" / f"reps_{n}.csv"
            if not f.exists():
                continue
            R = pd.read_csv(f, keep_default_na=False, na_values=[""])
            T = pd.read_csv(A / F / "pl-ss" / f"truth_{n}.csv", keep_default_na=False, na_values=[""])
            R = R.merge(T[["scenario", "arm", "truth_loghr"]], on=["scenario", "arm"])
            R["err"] = R.loghr - R.truth_loghr
            per[n] = {(sc, a): g.sort_values("rep").err.to_numpy() for (sc, a), g in R.groupby(["scenario", "arm"])}
        cr = []
        for sc in ("base", "phys_only", "strong"):
            for a2, a1 in CMP:
                pr_ = [(v[(sc, a1)], v[(sc, a2)]) for v in per.values() if (sc, a1) in v and (sc, a2) in v]
                if not pr_:
                    continue
                est = np.mean([abs(np.nanmean(x)) - abs(np.nanmean(y)) for x, y in pr_])
                bs = [np.mean([abs(np.nanmean(x[ix])) - abs(np.nanmean(y[ix])) for x, y in pr_ for ix in [rng.integers(0, len(x), len(x))]])
                      for _ in range(500)]
                cr.append(dict(scenario=sc, comparison=f"{LAB[a2]} vs {LAB[a1]}", trials=len(pr_), bias_reduction=est,
                               lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
        CR = pd.DataFrame(cr)
        CR.to_csv(OUT / "clmbr_plasmode_contrasts.csv", index=False)
        print("Reduction in |bias| (positive = first arm less biased), 95% Monte Carlo CI:\n")
        print(md(CR, 4) + "\n")


if __name__ == "__main__":
    main()
