"""EXPLORATORY (post hoc, requested 2026-09-25): SE-aware comparison of PS arms against the RCT.
Uses only the aggregate phase-2 estimates (loghr, se). Per arm, over the primary-set trials:
  - z_i = (b_obs - b_rct) / sqrt(se_obs^2 + se_rct^2); mean |z|; share |z| < 1.96
  - random-effects meta-analysis (DerSimonian-Laird) of d_i = b_obs - b_rct with variance v_i = se_obs^2 + se_rct^2:
    pooled bias (95% CI), tau^2 (heterogeneity beyond sampling error), I^2, Cochran Q
  - coverage: emulated 95% CI contains the RCT point estimate
  - median se_obs (precision cost)
  - paired Wilcoxon of |z| vs the sparse arm
Not pre-specified; reported as exploratory.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import summarize_phase2 as S  # noqa: E402

POP = sys.argv[1] if len(sys.argv) > 1 else "all"
S.POP = POP


def dl(d, v):
    w = 1 / v
    mu_f = np.sum(w * d) / np.sum(w)
    Q = np.sum(w * (d - mu_f) ** 2)
    k = len(d)
    C = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (Q - (k - 1)) / C) if C > 0 else 0.0
    ws = 1 / (v + tau2)
    mu = np.sum(ws * d) / np.sum(ws)
    se = np.sqrt(1 / np.sum(ws))
    I2 = max(0.0, (Q - (k - 1)) / Q) if Q > 0 else 0.0
    return mu, se, tau2, I2, Q


def main():
    D = S.load()
    P = S.primary_set()
    prim = D[(D.outcome == "primary") & (D.horizon == "trial") & (D.analysis == "matched") & D.name.isin(P)]
    arms = S.ARMS
    rows, zs = [], {}
    for a in arms:
        s = prim[prim.method == a].dropna(subset=["loghr", "se"])
        if s.empty:
            continue
        b_rct = np.array([S.bench(k)[0] for k in s.key]); se_rct = np.array([S.bench(k)[1] for k in s.key])
        d = s.loghr.to_numpy() - b_rct
        v = s.se.to_numpy() ** 2 + se_rct ** 2
        z = d / np.sqrt(v)
        zs[a] = pd.Series(np.abs(z), index=s.name.to_numpy())
        mu, se, tau2, I2, Q = dl(d, v)
        cover = np.mean((s.lo.to_numpy() <= np.exp(b_rct)) & (np.exp(b_rct) <= s.hi.to_numpy()))
        rows.append(dict(arm=S.LABEL[a], k=len(s), mean_abs_z=np.mean(np.abs(z)), share_abs_z_lt196=np.mean(np.abs(z) < 1.96),
                         pooled_bias=mu, bias_lo=mu - 1.96 * se, bias_hi=mu + 1.96 * se, tau=np.sqrt(tau2), I2=I2, Q=Q,
                         coverage=cover, median_se=np.median(s.se)))
    R = pd.DataFrame(rows)
    print(f"# EXPLORATORY SE-aware agreement — population: {POP} (primary set: {', '.join(P)})\n")
    print("| Arm | Trials | Mean abs z | abs z < 1.96 | Pooled bias, log HR (95% CI) | tau (between-trial SD beyond sampling error) | I² | Emulated CI covers RCT HR | Median SE (log HR) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in R.itertuples():
        print(f"| {r.arm} | {r.k} | {r.mean_abs_z:.2f} | {r.share_abs_z_lt196:.0%} | {r.pooled_bias:+.3f} ({r.bias_lo:+.3f} to {r.bias_hi:+.3f}) | "
              f"{r.tau:.3f} | {r.I2:.0%} | {r.coverage:.0%} | {r.median_se:.3f} |")
    print("\nPaired Wilcoxon of |z| against M1 sparse (two-sided):\n")
    base = zs.get("sparse")
    for a in arms:
        if a in ("sparse", "unmatched") or a not in zs or base is None:
            continue
        x = pd.concat([zs[a], base], axis=1, keys=["a", "b"]).dropna()
        if len(x) >= 3 and (x.a - x.b).abs().sum() > 0:
            print(f"- {S.LABEL[a]} vs M1 sparse: median |z| {x.a.median():.2f} vs {x.b.median():.2f}; smaller in {(x.a < x.b).sum()}/{len(x)}; "
                  f"p = {wilcoxon(x.a, x.b).pvalue:.3f}")


if __name__ == "__main__":
    main()
