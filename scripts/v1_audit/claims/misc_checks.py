#!/usr/bin/env python
"""v1 audit (claims recheck): small independent checks for paper2.md l.105 (attenuation toward the null), l.115 (label q values in
every configuration, and BH over all configurations), l.119 (agreement by emulation quality), l.99 (PROTECT AF C=1 PS-Flags AUC
source; reports only a rounded aggregate). Aggregates only."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core_recompute as K  # noqa: E402

R, order, key, tiers, S32, S38, CL = K.load()
B = K.blocks(R, order)
# l.105: do the arms shrink |log HR| toward 0 (attenuation) and does the shrink account for the |dlogHR| gain?
print("== l.105 attenuation: mean |log HR| (S32), base vs arm, by config")
for cfg in K.CONFIGS:
    b = B[("P5", cfg, "base")]["lg"].loc[S32]
    out = [f"{cfg:8s} base {np.nanmean(np.abs(b)):.3f}"]
    for a in ("ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"):
        x = B[("P5", cfg, a)]["lg"].loc[S32]
        sh = (np.abs(x) < np.abs(b)).sum()
        out.append(f"{a} {np.nanmean(np.abs(x)):.3f} (closer to 0 in {sh}/32)")
    print("  ".join(out))
rb = B[("P5", "main", "base")]["rb"].loc[S32]
print("mean |RCT log HR| S32", round(float(np.abs(rb).mean()), 3), "; mean RCT log HR", round(float(rb.mean()), 3))
# share of |dlogHR| gain explained by estimates moving toward zero
for a in ("ECG", "CLMBR", "ECG+CLMBR"):
    b = B[("P5", "main", "base")]["lg"].loc[S32]
    x = B[("P5", "main", a)]["lg"].loc[S32]
    print(a, "corr(per-trial |dlogHR| gain, per-trial shrink of |logHR|) =",
          round(float(np.corrcoef(np.abs(b - rb) - np.abs(x - rb), np.abs(b) - np.abs(x))[0, 1]), 2))
# l.115: label q values per config and BH across all configs (S32)
P = pd.read_csv(K.OUT / "labels_phys_recomputed.csv")
p = P[P.set == "S32"].copy()
p["q_allcfg"] = K.bh(p.p.to_numpy())
print("== l.115 physiologic label m54: p / q(within config) / q(BH over all 6 configs x 15)")
print(p[p.endpoint == "m54"].pivot_table(index="arm", columns="config", values=["p", "q", "q_allcfg"]).round(3).to_string())
D = pd.read_csv(K.OUT / "labels_dom_recomputed.csv")
d = D[(D.set == "S32") & (D.src == "dom") & D.tested]
print("== l.117 domain label rows with q<.05 in any config (S32, intersection labels)")
print(d[d.q < .05][["config", "arm", "domain", "n_lab", "mean_lab", "mean_not", "p", "q"]].round(3).to_string(index=False))
# l.119: agreement by emulation quality (S32)
tier = {t: tiers[key[t]] for t in S32}
eg = [t for t in S32 if tier[t] in ("Excellent", "Good")]
mo = [t for t in S32 if tier[t] == "Moderate"]
print("== l.119 quality groups: excellent/good", len(eg), "moderate", len(mo))
for nm, tr in (("exc/good", eg), ("moderate", mo)):
    xb = np.abs(B[("P5", "main", "base")]["lg"].loc[tr] - B[("P5", "main", "base")]["rb"].loc[tr])
    for a in ("ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"):
        xa = np.abs(B[("P5", "main", a)]["lg"].loc[tr] - B[("P5", "main", a)]["rb"].loc[tr])
        d_ = xb - xa
        print(f"  {nm:9s} {a:10s} |d| {xb.mean():.3f} -> {xa.mean():.3f}; closer {int((d_ > 0).sum())}/{int(d_.notna().sum())}; "
              f"one-sided sign-flip P {K.p_one(d_):.3f}; mean gain {d_.mean():.3f}")
