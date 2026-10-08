#!/usr/bin/env python
"""v1 audit: cells with 1-10 matched pairs (all PROTECT AF) that still carry held-out SMDs and therefore enter the
balance contrasts. Recomputes the affected S32 contrasts with and without such cells (trial dropped from the pair).
Aggregates only (no per-cell counts printed)."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v21")
import paper2_grid as G
SP = G.SP
OUT = SP.A / "claude-v1-audit" / "code"
R = pd.read_parquet(G.OUT / "restricted_cells.parquet")
tiny = R[(R.n_pairs >= 1) & (R.n_pairs < 11)]
cols = [f"smd:{c}" for c in G.NONCODED]
tiny = tiny[tiny[cols].notna().any(axis=1)]
keys = set(map(tuple, tiny[["trial", "rung", "config", "arm"]].to_numpy()))
print("cells with 1-10 pairs and non-missing SMDs:", sorted({(r, c, a) for _, r, c, a in keys}))
# per-trial m54 of such cells vs the same trial's base cell and vs other trials
for (n, rg, cfg, a) in sorted(keys):
    g = R[(R.rung == rg) & (R.config == cfg) & (R.arm == a)].set_index("trial")
    m = g[cols].abs().mean(1)
    print(f"  {rg}/{cfg}/{a}: m54 in the tiny-cell trial = {m[n]:.3f}; median over other trials = {m.drop(n).median():.3f}")
S = pd.read_csv(G.OUT / "sensitivity.csv")
S = S[S.set == "S32"]
F, SM, RET = G.load_F(R)
CL = SP.V.cluster_of()
rows = []
for _, r in S.iterrows():
    ka, kb = (r.rung_a, r.config, r.arm_a), (r.rung_b, r.config, r.arm_b)
    hit = [n for (n, rg, cfg, a) in keys if (rg, cfg, a) in (ka, kb)]
    if not hit:
        continue
    tr = [t for t in SP.S32 if t not in hit]
    x = SP.contrast_row(F[ka], F[kb], tr, r.sided, CL, G.mask(SM[ka], G.NONCODED), G.mask(SM[kb], G.NONCODED))
    rows.append(dict(config=r.config, contrast=r.contrast, pub_relred54=r.relred54, pub_lo=r.relred54_lo, pub_hi=r.relred54_hi,
                     pub_p=r.m54_p, pub_q=r.q_m54_p_fam, fixed_relred54=x["relred"], fixed_lo=x["relred_lo"], fixed_hi=x["relred_hi"],
                     fixed_p=x["m58_p"], fixed_k=x["relred_k"]))
D = pd.DataFrame(rows)
os.umask(0o077); OUT.mkdir(parents=True, exist_ok=True)
D.to_csv(OUT / "tiny_cells.csv", index=False)
pd.set_option("display.width", 250)
print(D.round(3).to_string(index=False))
