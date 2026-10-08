#!/usr/bin/env python
"""v1 audit: re-run the balance-family BH-FDR of paper2_grid.summarize after treating cells with 1-10 matched pairs as failed
(SMDs -> NaN, as for the PS-Flags PROTECT AF cells). Only rows that use such a cell are recomputed (54- and 58-item
endpoints); all other p-values are taken from core/sensitivity.csv. Prints q<.05 counts per set x configuration, published
vs fixed, and the changed rows. Aggregates only."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v21")
import paper2_grid as G
SP, E = G.SP, G.E
OUT = SP.A / "claude-v1-audit" / "code"
R = pd.read_parquet(G.OUT / "restricted_cells.parquet")
tiny = (R.n_pairs >= 1) & (R.n_pairs < 11)
R2 = R.copy()
R2.loc[tiny, [f"smd:{c}" for c in G.VN]] = np.nan
bad = set(map(tuple, R[tiny][["rung", "config", "arm"]].to_numpy()))
F, SM, RET = G.load_F(R2)
CL = SP.V.cluster_of()
S = pd.read_csv(G.OUT / "sensitivity.csv")
S0 = S.copy()
for i, r in S.iterrows():
    ka, kb = (r.rung_a, r.config, r.arm_a), (r.rung_b, r.config, r.arm_b)
    if ka not in bad and kb not in bad:
        continue
    tr = SP.S32 if r.set == "S32" else SP.S38
    x = SP.contrast_row(F[ka], F[kb], tr, r.sided, CL, G.mask(SM[ka], G.NONCODED), G.mask(SM[kb], G.NONCODED))
    y = G.bal_light(F[ka], F[kb], SM[ka], SM[kb], tr, r.sided, CL, full=False)
    S.loc[i, ["m54_p", "lt01_54_p", "relred54", "relred54_lo", "relred54_hi"]] = [x["m58_p"], x["lt01_p"], x["relred"], x["relred_lo"], x["relred_hi"]]
    S.loc[i, ["m58_p", "lt01_58_p", "relred58"]] = [y["m58_p"], y["lt01_p"], y["relred"]]
for sname in ("S32", "S38"):
    ms = S.set == sname
    long = S.loc[ms, G.BAL_FAM].stack()
    q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
    S.loc[ms, "q_m54_p_fam"] = q["m54_p"]
cnt = lambda D: D.groupby(["set", "config"]).q_m54_p_fam.apply(lambda x: int((x < .05).sum()))
C = pd.DataFrame({"published": cnt(S0), "fixed": cnt(S)})
print(C.to_string()); print(C.groupby(level=0).sum().to_string())
chg = S[(S0.q_m54_p_fam < .05) != (S.q_m54_p_fam < .05)]
pd.set_option("display.width", 250)
print("rows whose q<.05 status changes:")
print(pd.concat([chg[["set", "config", "contrast"]], S0.loc[chg.index, ["relred54", "m54_p", "q_m54_p_fam"]].add_prefix("pub_"),
                 chg[["relred54", "relred54_lo", "relred54_hi", "m54_p", "q_m54_p_fam"]].add_prefix("fix_")], axis=1).round(3).to_string(index=False))
os.umask(0o077)
S.to_csv(OUT / "sensitivity_tinyfix.csv", index=False)
