#!/usr/bin/env python
"""v1 audit (claims recheck): independent recompute of the paper2 MIMIC-IV claims (paper2.md l.63, l.127, l.218, l.264)
from the per-trial arm tables (results/<trial>_arms.csv), without calling mimic_summary / mimic_cvd5.summarize.

Inputs (read only, trial-level aggregates):
  claude-v21-paper2/mimic/results/<k>_arms.csv              bases demo / sparse / cvd5 / cvd5_anydm / cvd5_incl
  claude-v21-paper2/mimic/windowfix/results/<k>_arms.csv    window-fixed sparse / hdPS200 / clinical (new trials rebuilt)
  claude-v20-mimic-replication/results/<k>_arms.csv          v20 as published
Re-implemented: relative reduction 100 * (1 - mean(arm mean|SMD|) / mean(base mean|SMD|)) over the 7 cardiovascular trials;
percentile bootstrap of trials (2,000 resamples seed 0 = v20 convention, and 4,000 resamples seed 20261001 = paper.md
convention); exact one-sided sign-flip test by full enumeration of the 2^7 sign vectors; agreement |loghr - rct_loghr|.
Output: /mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/claims/mimic_recheck.csv (aggregates only).
"""
import itertools
import os
from pathlib import Path

import numpy as np
import pandas as pd

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = A / "claude-v1-audit" / "claims"
P7 = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2"]
ALL8 = P7 + ["peptic"]


def load(d):
    return pd.concat([pd.read_csv(d / f"{k}_arms.csv") for k in ALL8 if (d / f"{k}_arms.csv").exists()], ignore_index=True)


def signflip(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    obs = d.mean()
    s = np.array(list(itertools.product([-1, 1], repeat=len(d))))
    return float(np.mean((s * np.abs(d)).mean(1) >= obs - 1e-12))


def boot(mb, ma, n, seed):
    rng = np.random.default_rng(seed)
    i = rng.integers(0, len(mb), (n, len(mb)))
    r = 100 * (1 - ma[i].mean(1) / mb[i].mean(1))
    return np.percentile(r, [2.5, 97.5])


def piv(D, base, pop, col, trials=P7):
    S = D[(D.base == base) & (D["pop"] == pop) & D.trial.isin(trials)]
    return S.pivot(index="trial", columns="arm", values=col).reindex(trials)


def summ(D, base, pop, tag):
    rows = []
    m = piv(D, base, pop, "mean_smd")
    pb = piv(D, base, pop, "pct_bal")
    mb, ma, mp = m["base"].to_numpy(), m["ECG"].to_numpy(), m["permECG"].to_numpy()
    rr = 100 * (1 - ma.mean() / mb.mean())
    c2, c4 = boot(mb, ma, 2000, 0), boot(mb, ma, 4000, 20261001)
    ms = piv(D, base, pop, "mean_smd", trials=sorted(P7))  # v20 summary pivots alphabetically: CI depends on trial order
    c2a = boot(ms["base"].to_numpy(), ms["ECG"].to_numpy(), 2000, 0)
    rows.append(dict(item=f"{tag} {base} {pop}: relred ECG", value=round(rr, 2), ci2000=f"{c2[0]:.1f} to {c2[1]:.1f}",
                     ci2000_alpha=f"{c2a[0]:.1f} to {c2a[1]:.1f}",
                     ci4000=f"{c4[0]:.1f} to {c4[1]:.1f}", k_lower=f"{int((ma < mb).sum())}/7", p=round(signflip(mb - ma), 4)))
    rows.append(dict(item=f"{tag} {base} {pop}: relred permECG", value=round(100 * (1 - mp.mean() / mb.mean()), 2)))
    d = (pb["ECG"] - pb["base"]).to_numpy()
    rows.append(dict(item=f"{tag} {base} {pop}: pct_bal base -> ECG", value=f"{pb['base'].mean():.1f} -> {pb['ECG'].mean():.1f}",
                     k_lower=f"{int((d > 0).sum())}/7 better", p=round(signflip(d), 4)))
    lh = piv(D, base, pop, "loghr")
    rb = piv(D, base, pop, "rct_loghr")["base"]
    e = {a: (lh[a] - rb).abs() for a in ("base", "ECG", "permECG")}
    dd = (e["base"] - e["ECG"]).dropna().to_numpy()
    rows.append(dict(item=f"{tag} {base} {pop}: mean |dlogHR| base / ECG / perm",
                     value=f"{e['base'].mean():.3f} / {e['ECG'].mean():.3f} / {e['permECG'].mean():.3f}",
                     k_lower=f"{int((dd > 0).sum())}/{len(dd)} closer", p=round(signflip(dd), 4)))
    return rows


def main():
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    V21 = load(A / "claude-v21-paper2" / "mimic" / "results")
    WF = load(A / "claude-v21-paper2" / "mimic" / "windowfix" / "results")
    V20 = load(A / "claude-v20-mimic-replication" / "results")
    rows = []
    for base in ("cvd5", "cvd5_anydm", "cvd5_incl"):
        for pop in ("all", "no_index_day_ecg"):
            rows += summ(V21, base, pop, "v21")
    for base in ("demo", "sparse", "hdPS200", "clinical"):
        for D, tag in ((V20, "v20"), (WF, "windowfix")):
            if ((D.base == base) & (D["pop"] == "all")).any():
                rows += summ(D, base, "all", tag)[:2]
    pe = V21[(V21.trial == "peptic") & (V21.base == "cvd5") & (V21["pop"] == "all")].set_index("arm")
    for a in ("base", "ECG", "permECG"):
        b, se = pe.loc[a, "loghr"], pe.loc[a, "se"]
        rows.append(dict(item=f"PEPTIC cvd5 {a} HR (95% CI)", value=f"{np.exp(b):.2f} ({np.exp(b - 1.96 * se):.2f}-{np.exp(b + 1.96 * se):.2f})"))
    rows.append(dict(item="PEPTIC RCT benchmark", value=f"{np.exp(pe.loc['base', 'rct_loghr']):.2f} {pe.loc['base', 'rct_measure']}"))
    rows.append(dict(item="n held-out vars (cvd5, all; min-max over trials)",
                     value=f"{int(V21[V21.base == 'cvd5'].n_vars.min())}-{int(V21[V21.base == 'cvd5'].n_vars.max())}"))
    rows.append(dict(item="dx flags in PS-CVD5 (min-max)", value=f"{V21[V21.base == 'cvd5'].n_dx_flags_in_ps.min():.0f}-{V21[V21.base == 'cvd5'].n_dx_flags_in_ps.max():.0f}"))
    T = pd.DataFrame(rows)
    T.to_csv(OUT / "mimic_recheck.csv", index=False)
    pd.set_option("display.width", 250, "display.max_rows", 200, "display.max_colwidth", 70)
    print(T.to_string(index=False))


if __name__ == "__main__":
    main()
