#!/usr/bin/env python
"""Post-hoc (v1.4 addition H): RCT-DUPLICATE metric panel per PS specification, ratio of ratios, and a
Heyard-style dispersion / meta-regression analysis.

Per arm, across trials (full-cohort point estimates, imputation 1; bootstrap replicate 0):
  significance agreement (RCT-DUPLICATE 'regulatory'), estimate agreement, standardized-difference agreement,
  Pearson r of log HRs (with leave-one-out range), Cohen's kappa on {sig. benefit, n.s., sig. harm},
  ratio of ratios (random-effects pooled exp(log HR_emul - log HR_RCT), I^2), mean |Δlog HR|,
  Heyard dispersion phi = Q/(k-1) (1 = disagreement fully explained by the two estimates' sampling error).
Paired arm comparisons: exact sign-flip test across trials on z_i^2 = (Δ_i)^2 / v_i (precision-standardised
squared disagreement) and on |Δ_i|; exact McNemar on binary agreement.
Closeness: RCT-DUPLICATE rubric rated blind to our results (docs/v14/closeness_rating.json) when present.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import PUBLISHED, TRIALS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402
from v13_summarize import md, sign_flip  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "v14"
ARMS = ["unmatched", "demo", "ECGonly", "demo+ECG", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "R+"]
LAB = {"unmatched": "Unadjusted", "demo": "Demographics", "ECGonly": "ECG only", "demo+ECG": "Demographics + ECG", "sparse": "Sparse",
       "sparse+ECG": "Sparse + ECG", "hdPS200": "hdPS200", "hdPS200+ECG": "hdPS200 + ECG", "clinical (reference)": "Clinical PS",
       "R+": "R+ physiology ref"}
CMP = [("sparse+ECG", "sparse"), ("hdPS200+ECG", "hdPS200"), ("ECGonly", "unmatched"), ("demo+ECG", "demo"),
       ("sparse+ECG", "clinical (reference)"), ("hdPS200+ECG", "clinical (reference)")]


def cat(b, s):
    return np.where(b - 1.96 * s > 0, 1, np.where(b + 1.96 * s < 0, -1, 0))


def kappa(x, y):
    cats = [-1, 0, 1]
    po = np.mean(x == y)
    pe = sum(np.mean(x == c) * np.mean(y == c) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def dl(d, v):
    w = 1 / v
    mf = np.sum(w * d) / np.sum(w)
    Q = np.sum(w * (d - mf) ** 2)
    k = len(d)
    C = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    t2 = max(0.0, (Q - (k - 1)) / C) if C > 0 else 0.0
    ws = 1 / (v + t2)
    mu = np.sum(ws * d) / np.sum(ws)
    se = np.sqrt(1 / np.sum(ws))
    return mu, se, Q, max(0.0, (Q - (k - 1)) / Q) if Q > 0 else 0.0


def load():
    names = {**PRIMARY, **EXTRA}
    rows = []
    for n, (k, _) in names.items():
        f1, f2 = A / "claude-v13-bootstrap" / f"bs_{n}.csv", A / "claude-v14-ecgonly" / f"bs_{n}.csv"
        if not (f1.exists() and f2.exists()):
            continue
        d = pd.concat([pd.read_csv(f1), pd.read_csv(f2)])
        d = d[d.rep == 0].drop_duplicates("arm").set_index("arm")
        b, se = bench(k)
        for a in ARMS:
            if a in d.index:
                rows.append(dict(trial=n, key=k, role=TRIALS[k].get("role"), arm=a, b=d.loc[a, "loghr"], s=d.loc[a, "se"], rb=b, rs=se))
    return pd.DataFrame(rows)


def panel(D):
    out = []
    for a in ARMS:
        g = D[D.arm == a].dropna(subset=["b", "s"])
        if len(g) < 3:
            continue
        b, s, rb, rs = g.b.to_numpy(), g.s.to_numpy(), g.rb.to_numpy(), g.rs.to_numpy()
        ce, cr = cat(b, s), cat(rb, rs)
        sig_agree = np.mean(np.where(cr != 0, ce == cr, ce == 0))
        est = np.mean(np.abs(b - rb) <= 1.96 * rs)
        z = (b - rb) / np.sqrt(s ** 2 + rs ** 2)
        r = np.corrcoef(b, rb)[0, 1]
        loo = [np.corrcoef(np.delete(b, i), np.delete(rb, i))[0, 1] for i in range(len(b))]
        mu, se, Q, I2 = dl(b - rb, s ** 2 + rs ** 2)
        from scipy.stats import spearmanr
        zf, sef = np.arctanh(r), 1 / np.sqrt(max(len(b) - 3, 1))
        out.append(dict(arm=LAB[a], trials=len(g), significance_agreement=sig_agree, estimate_agreement=est, std_diff_agreement=np.mean(np.abs(z) < 1.96),
                        pearson_r=r, r_fisher_lo=np.tanh(zf - 1.96 * sef), r_fisher_hi=np.tanh(zf + 1.96 * sef), spearman=spearmanr(b, rb).statistic,
                        r_loo_min=min(loo), r_loo_max=max(loo), kappa=kappa(ce, cr),
                        ratio_of_ratios=np.exp(mu), ror_lo=np.exp(mu - 1.96 * se), ror_hi=np.exp(mu + 1.96 * se), I2=I2,
                        dispersion_phi=Q / (len(g) - 1), mean_abs_dlog=np.mean(np.abs(b - rb))))
    return pd.DataFrame(out)


def paired(D, trials):
    rows = []
    for a2, a1 in CMP:
        x = D[(D.arm == a2) & D.trial.isin(trials)].set_index("trial")
        y = D[(D.arm == a1) & D.trial.isin(trials)].set_index("trial")
        tt = x.index.intersection(y.index)
        x, y = x.loc[tt], y.loc[tt]
        z2 = (x.b - x.rb) ** 2 / (x.s ** 2 + x.rs ** 2) - (y.b - y.rb) ** 2 / (y.s ** 2 + y.rs ** 2)
        dabs = (x.b - x.rb).abs() - (y.b - y.rb).abs()
        ex, ey = (np.abs(x.b - x.rb) <= 1.96 * x.rs), (np.abs(y.b - y.rb) <= 1.96 * y.rs)
        up, dn = int((ex & ~ey).sum()), int((~ex & ey).sum())
        rows.append(dict(comparison=f"{LAB[a2]} vs {LAB[a1]}", trials=len(tt), mean_diff_abs=dabs.mean(), p_signflip_abs=sign_flip(dabs.to_numpy())[1],
                         closer=f"{int((dabs < 0).sum())}/{len(tt)}", mean_diff_z2=z2.mean(), p_signflip_z2=sign_flip(z2.to_numpy())[1],
                         estimate_agreement_gained=up, lost=dn, p_mcnemar=binomtest(up, up + dn, 0.5).pvalue if up + dn else 1.0))
    return pd.DataFrame(rows)


def metareg(D, close):
    """Heyard-style: weighted regression of Δ = log HR_emul − log HR_RCT on a closeness indicator, per arm;
    residual multiplicative dispersion phi."""
    rows = []
    for a in ARMS:
        g = D[D.arm == a].dropna(subset=["b", "s"])
        g = g[g.trial.isin(close)] if isinstance(close, list) else g
        if len(g) < 4:
            continue
        d = (g.b - g.rb).to_numpy()
        w = 1 / (g.s ** 2 + g.rs ** 2).to_numpy()
        X = np.column_stack([np.ones(len(d)), g.trial.map(close).astype(float).to_numpy()]) if isinstance(close, dict) else np.ones((len(d), 1))
        W = np.diag(w)
        beta = np.linalg.solve(X.T @ W @ X, X.T @ W @ d)
        res = d - X @ beta
        phi = float(np.sum(w * res ** 2) / (len(d) - X.shape[1]))
        rows.append(dict(arm=LAB[a], trials=len(d), phi_residual=phi, intercept=beta[0], close_coef=beta[1] if X.shape[1] > 1 else np.nan))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    D = load()
    trials = sorted(D.trial.unique())
    print("# RCT-DUPLICATE metric panel, ratio of ratios and Heyard-style dispersion (post-hoc v1.4 addition H; exploratory)\n")
    print(f"{len(trials)} trials; full-cohort point estimates (imputation 1). Paired inference: exact sign-flip across trials and McNemar.\n")
    rating = None
    f = OUT / "closeness_rating.json"
    if f.exists():
        R = json.load(open(f))
        key = {n: k for n, (k, _) in {**PRIMARY, **EXTRA}.items()}
        rating = {t: bool(R[key[t]]["close_emulation"]) for t in trials if key[t] in R}
        print(f"Blinded closeness rating (RCT-DUPLICATE rubric): close = {sorted(t for t, v in rating.items() if v)}\n")
    subsets = {"all": trials}
    if rating:
        subsets["close (blinded rubric)"] = [t for t in trials if rating.get(t)]
        subsets["not close (blinded rubric)"] = [t for t in trials if rating.get(t) is False]
    for sname, tr in subsets.items():
        P = panel(D[D.trial.isin(tr)])
        P.to_csv(OUT / f"panel_{sname.split()[0]}.csv", index=False)
        print(f"## Panel — {sname} ({len(tr)} trials)\n")
        print(md(P, 2) + "\n")
        Q = paired(D, tr)
        print("Paired comparisons (negative mean differences favour the first arm):\n")
        print(md(Q, 3) + "\n")
    if rating:
        M = metareg(D, {t: rating[t] for t in trials if t in rating})
        print("## Heyard-style weighted meta-regression of Δlog HR on closeness (per arm)\n")
        print("phi_residual = residual multiplicative dispersion (1 = remaining disagreement explained by sampling error).\n")
        print(md(M, 3) + "\n")


if __name__ == "__main__":
    main()
