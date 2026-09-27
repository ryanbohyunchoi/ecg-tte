#!/usr/bin/env python
"""Summarise S10 (demo + HTN/T2D/CAD/AF/obesity/HF) with vs without ECG. Aggregates only."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import v16_engine as E  # noqa: E402
from audit_v16 import CLUSTER  # noqa: E402
from v13_summarize import sign_flip  # noqa: E402

R = pd.read_csv("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s10-demo6/results.csv")
SMD = [c for c in R.columns if c.startswith("smd:")]
NOBMI = [c for c in SMD if "bmi" not in c.lower()]
rng = np.random.default_rng(0)


def metrics(g, cols):
    a = g[cols].abs()
    return pd.DataFrame({"lt01": 100 * (a < 0.1).sum(1) / a.notna().sum(1), "gt02": 100 * (a > 0.2).sum(1) / a.notna().sum(1),
                         "mean_smd": a.mean(1), "absd": (g.loghr - g.rb).abs(),
                         "z2": (g.loghr - g.rb) ** 2 / (g.se ** 2 + g.rs ** 2), "cstat": g.cstat}, index=g.trial)


def p(d):
    return sign_flip(np.asarray(d, float))[1]


out = []
for cal in (0.2, 0.1):
    for panel, cols in (("58", SMD), ("57 no BMI", NOBMI)):
        M = {}
        for h in ("full", "A", "B"):
            g = R[(R.half == h) & (R.caliper == cal)]
            M[h] = {r: metrics(g[g.arm_role == r].set_index("trial", drop=False), cols) for r in ("base", "ECG", "shufECG", "noise")}
        for m in ("lt01", "gt02", "mean_smd", "cstat", "absd", "z2"):
            b, e = M["full"]["base"][m], M["full"]["ECG"][m]
            d = e - b
            cl = d.groupby(d.index.map(CLUSTER)).mean()
            row = dict(caliper=cal, panel=panel, metric=m, base=b.mean(), ecg=e.mean(), d=d.mean(),
                       k=f"{int((d > 0).sum() if m == 'lt01' else (d < 0).sum())}/18", p=p(d),
                       p_vs_shuf=p(e - M["full"]["shufECG"][m]), p_vs_noise=p(e - M["full"]["noise"][m]),
                       d_shuf=(M["full"]["shufECG"][m] - b).mean(), cluster_p=p(cl), loo_max=max(p(d.drop(t)) for t in d.index),
                       pA=p(M["A"]["ECG"][m] - M["A"]["base"][m]), pB=p(M["B"]["ECG"][m] - M["B"]["base"][m]))
            if m in ("absd", "z2"):
                gb = R[(R.half == "full") & (R.caliper == cal)]
                bb, ee = gb[gb.arm_role == "base"].set_index("trial"), gb[gb.arm_role == "ECG"].set_index("trial")
                rb, rs = bb.rb.values, bb.rs.values

                def st(ix):
                    q, s = rb[ix], rs[ix]
                    if m == "absd":
                        return (np.abs(ee.loghr.values - q) - np.abs(bb.loghr.values - q)).mean()
                    return ((ee.loghr.values - q) ** 2 / (ee.se.values ** 2 + s ** 2) - (bb.loghr.values - q) ** 2 / (bb.se.values ** 2 + s ** 2)).mean()
                obs = st(np.arange(18))
                null = np.array([st(rng.permutation(18)) for _ in range(5000)])
                row.update(shuffle_null_mean=null.mean(), shuffle_p=(null <= obs).mean())
            out.append(row)
        if panel == "58":
            g = R[(R.half == "full") & (R.caliper == cal)]
            med = {r: g[g.arm_role == r][cols].abs().median() for r in ("unmatched", "base", "ECG")}
            print(f"caliper {cal}: love-plot medians <0.1: unmatched {(med['unmatched'] < 0.1).sum()}, base {(med['base'] < 0.1).sum()}, "
                  f"ECG {(med['ECG'] < 0.1).sum()} of {len(cols)}")
            ret = g[g.arm_role.isin(['base', 'ECG'])].groupby('arm_role').apply(lambda x: (x.n_pairs / np.minimum(x.n_t, x.n_c)).mean())
            print(f"  retention (pairs / smaller arm): base {ret['base']:.3f}, ECG {ret['ECG']:.3f}")
S = pd.DataFrame(out)
S["q"] = E.bh_fdr(S.p.values)
pd.set_option("display.width", 250)
print(S.round(4).to_string(index=False))
S.to_csv("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s10-demo6/summary.csv", index=False)
