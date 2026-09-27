"""Round-3: independent recomputation of S8 from raw per-trial arm rows (results_v2.csv)."""
import sys
sys.path.insert(0, "/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-audit3")
from a3_common import *  # noqa

R = pd.read_csv(A + "claude-v16-s8-headline/results_v2.csv", low_memory=False)
R2 = pd.read_csv(A + "claude-v16-s8-headline/results.csv", low_memory=False)
key = ["cell", "trial", "half", "arm_role", "seed"]
m = R.merge(R2, on=key, suffixes=("", "_c"))
print("results.csv vs results_v2.csv rows", len(R), len(R2), "merged", len(m),
      "max|dloghr|", np.nanmax(np.abs(m.loghr - m.loghr_c)), "max|dpct|", np.nanmax(np.abs(m.p58_pct_lt10 - m.p58_pct_lt10_c)),
      "max|dxo|", np.nanmax(np.abs(m.xo_pct_lt10 - m.xo_pct_lt10_c)))
# half-A rows vs the pre-selection file
RA = pd.read_csv(A + "claude-v16-s8-headline/prev_v1_expanded/results_A.csv", low_memory=False)
mA = RA.merge(R[R.half == "A"], on=key, suffixes=("", "_v2"))
print("half A: pre-selection file rows", len(RA), "matched", len(mA), "max|dpct58|", np.nanmax(np.abs(mA.p58_pct_lt10 - mA.p58_pct_lt10_v2)),
      "max|dloghr|", np.nanmax(np.abs(mA.loghr - mA.loghr_v2)))

SC = [c for c in R.columns if c.startswith("smd:")]
assert len(SC) == 58
V = R[SC].to_numpy(float)
fin = np.isfinite(V)
R["pct"] = 100 * np.where(fin, V < 0.1, False).sum(1) / fin.sum(1)
print("own pct vs p58_pct_lt10 max|d|", np.nanmax(np.abs(R.pct - R.p58_pct_lt10)))
R["retain"] = R.n_pairs / R.n_t

cells = [c for c in R.cell.unique() if c != "unmatched"]


def pt(cell, half, role, col):
    if role == "base" and cell.startswith("none|"):
        g = R[(R.cell == "unmatched") & (R.half == half)]
    else:
        g = R[(R.cell == cell) & (R.half == half) & (R.arm_role == role)]
    return g.groupby("trial")[col].mean()


def cube(cell, half, role, trials):
    if role == "base" and cell.startswith("none|"):
        g = R[(R.cell == "unmatched") & (R.half == half)]
    else:
        g = R[(R.cell == cell) & (R.half == half) & (R.arm_role == role)]
    g = g[g.trial.isin(trials)].groupby("trial")[SC].mean().reindex(trials)
    return g.to_numpy(float)


TR = sorted(R.trial.unique())
rows = []
for cell in cells:
    for sub, trs in (("all", TR), ("phys", PHYS)):
        for h in ("full", "A", "B"):
            r = dict(cell=cell, subset=sub, half=h)
            for panel, col in (("p58", "pct"), ("xo", "xo_pct_lt10")):
                b, e = pt(cell, h, "base", col).reindex(trs), pt(cell, h, "ECG", col).reindex(trs)
                s, nz = pt(cell, h, "shufECG", col).reindex(trs), pt(cell, h, "noise", col).reindex(trs)
                d = (e - b).dropna()
                r.update({f"{panel}_base": b.mean(), f"{panel}_ecg": e.mean(), f"{panel}_d": d.mean(), f"{panel}_k": int((d > 0).sum()),
                          f"{panel}_p": flip(d.values), f"{panel}_p_shuf": flip((e - s).dropna().values),
                          f"{panel}_p_noise": flip((e - nz).dropna().values), f"{panel}_d_shuf": (e - s).mean(), f"{panel}_d_noise": (e - nz).mean()})
                if panel == "p58":
                    r["p58_clp"] = cluster_p(d)
                    r["p58_loo"] = loo_max(d) if h == "full" else np.nan
            if h == "full" or cell in ("demo|cal0.1", "demo|default"):
                Mb, Me = cube(cell, h, "base", trs), cube(cell, h, "ECG", trs)
                r["love_base"], r["love_ecg"] = int(love_count(Mb)), int(love_count(Me))
                if cell in ("demo|cal0.1", "demo|default", "min7|default", "common10|default", "sparse|default", "hdPS200|default") and sub == "all":
                    r["love_d"], r["love_swap_p"] = love_swap(Me, Mb)
                    r["love_swap_clp"] = love_swap(Me, Mb, groups=[CLUSTER[t] for t in trs])[1]
            for role in ("base", "ECG"):
                x = pt(cell, h, role, "retain").reindex(trs)
                r[f"retain_{role}"] = x.mean()
            dr = (pt(cell, h, "ECG", "retain") - pt(cell, h, "base", "retain")).reindex(trs).dropna()
            r["retain_d"], r["retain_p"], r["retain_k_lower"] = dr.mean(), flip(dr.values), int((dr < 0).sum())
            rows.append(r)
G = pd.DataFrame(rows)
# BH families
for (h, sub), k in G.groupby(["half", "subset"]).groups.items():
    G.loc[k, "q_cells"] = bh(G.loc[k, "p58_p"])
for h, k in G.groupby("half").groups.items():
    p = np.r_[G.loc[k, "p58_p"].to_numpy(), G.loc[k, "xo_p"].to_numpy()]
    q = bh(p)
    G.loc[k, "q_all136_p58"], G.loc[k, "q_all136_xo"] = q[:len(k)], q[len(k):]
G.to_csv(OUT + "s8_recompute.csv", index=False)

F = G[(G.half == "full") & (G.subset == "all") & ~G.cell.str.startswith("none")].copy()
F["rank_d"] = F.p58_d.rank(ascending=False)
F["rank_p"] = F.p58_p.rank(method="min")
F["q33"] = bh(F.p58_p)
pd.set_option("display.width", 250)
cols = ["cell", "p58_base", "p58_ecg", "p58_d", "p58_k", "p58_p", "q33", "p58_clp", "p58_loo", "rank_d", "rank_p", "love_base", "love_ecg",
        "retain_base", "retain_ECG", "retain_d", "retain_p"]
print(F.sort_values("p58_d", ascending=False)[cols].round(4).to_string())
print("n full/all cells", len(F), "significant p<0.05 & d>0:", int(((F.p58_p < 0.05) & (F.p58_d > 0)).sum()), "BH q<0.05:", int(((F.q33 < 0.05) & (F.p58_d > 0)).sum()))
for c in ("demo|cal0.1", "demo|default", "min7|default", "common10|default", "sparse|default", "hdPS200|default"):
    x = G[(G.cell == c) & (G.subset == "all")].set_index("half")
    print(c, {h: (round(x.loc[h, "p58_base"], 1), round(x.loc[h, "p58_ecg"], 1), round(x.loc[h, "p58_d"], 2), int(x.loc[h, "p58_k"]), round(x.loc[h, "p58_p"], 4),
                  round(x.loc[h, "p58_clp"], 4), x.loc[h].get("love_base"), x.loc[h].get("love_ecg"), x.loc[h].get("love_swap_p"),
                  round(x.loc[h, "retain_base"], 3), round(x.loc[h, "retain_ECG"], 3)) for h in ("full", "A", "B")})
    print("   xo full", round(x.loc["full", "xo_base"], 2), round(x.loc["full", "xo_ecg"], 2), round(x.loc["full", "xo_d"], 2), round(x.loc["full", "xo_p"], 4))
print("total tests at full cohort, p58+xo x all+phys (excluding none):", int(2 * 2 * len(F)))
