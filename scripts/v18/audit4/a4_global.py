"""Round-4 audit: multiplicity over the v1.7 / S11 / v1.8 test families (from the committed-analysis summary CSVs,
whose headline rows were independently reproduced in a4_stats). Aggregates only."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from a4_common import *  # noqa

os.umask(0o077)
EMU = {"absd", "z2", "cons"}
R = []
v = pd.read_csv(A + "claude-v17-confirm/summary.csv")
for _, r in v.iterrows():
    R.append(dict(src="v17", cell=f"{r.scope}|{r.subset}|{r.ps}", metric=r.metric, contrast="ECG vs base", p=r.p, bshuf_p=r.get("bshuf_p"),
                  prespec_primary=(r.scope == "new15" and r.subset == "all" and r.metric in ("lt01", "absd"))))
s = pd.read_csv(A + "claude-v17-confirm/summary_p5.csv")
mm = {"lt": "lt01", "x": "x_lt01", "gap": "absd"}
for _, r in s.iterrows():
    R.append(dict(src="s11", cell=f"{r.set}|P5", metric=mm.get(r.metric, r.metric), contrast="ECG vs base", p=r.p, bshuf_p=r.shuffleRCT_p,
                  prespec_primary=False))
a = pd.read_csv(A + "claude-v18-af-confirm/summary.csv")
for _, r in a.iterrows():
    R.append(dict(src="v18af", cell=f"{r.scope}|{r.subset}|{r.ps}", metric=r.metric, contrast="ECG vs base", p=r.p, bshuf_p=r.get("bshuf_p"),
                  prespec_primary=(r.scope == "AF5" and r.subset == "all" and r.ps == "P1" and r.metric == "absd")))
c = pd.read_csv(A + "claude-v18-clmbr/summary.csv")
key = ["CLMBR vs base", "ECG vs base", "CLMBR+ECG vs base", "CLMBR vs ECG", "CLMBR+ECG vs CLMBR", "CLMBR+ECG vs ECG"]
c = c[c.contrast.isin(key) & (c.scope == "all33")]
for _, r in c.iterrows():
    R.append(dict(src="clmbr", cell=f"{r.scope}|{r.ps}", metric=r.metric, contrast=r.contrast, p=r.p, bshuf_p=r.get("bshuf_p"), prespec_primary=False))
k = pd.read_csv(A + "claude-v18-clmbr/per_category.csv")
k = k[k.contrast.isin(key)]
for _, r in k.iterrows():
    R.append(dict(src="clmbr_cat", cell=f"{r.category}|{r.ps}", metric=r.metric, contrast=r.contrast, p=r.p, bshuf_p=r.get("bshuf_p"),
                  prespec_primary=False))
e = pd.read_csv(A + "claude-v17-confirm/emulation_by_category.csv")
for _, r in e.iterrows():
    R.append(dict(src="v17cat", cell=f"{r.category}|{r.PS}", metric="absd", contrast="ECG vs base", p=r.p_gap, bshuf_p=r.shuffleRCT_p,
                  prespec_primary=False))
G = pd.DataFrame(R)
G = G[np.isfinite(G.p)]
G["domain"] = np.where(G.metric.isin(EMU), "emulation", "balance")
G["q_all"] = bh(G.p.values)
for d in ("balance", "emulation"):
    ix = G.domain == d
    G.loc[ix, "q_domain"] = bh(G.loc[ix, "p"].values)
ix = (G.domain == "emulation") & G.bshuf_p.notna()
G.loc[ix, "q_bshuf"] = bh(G.loc[ix, "bshuf_p"].values)
G.to_csv(OUT + "global_v17_v18.csv", index=False)
print("tests:", len(G), G.groupby(["src", "domain"]).size().to_dict())
print("prespecified confirmatory primaries:\n", G[G.prespec_primary][["src", "cell", "metric", "p", "bshuf_p"]].to_string())
pp = G[G.prespec_primary]
print("Holm/Bonferroni over", len(pp), "primaries: min p", pp.p.min(), "threshold", 0.05 / len(pp), "BH q", bh(pp.p.values).round(3))
for d in ("balance", "emulation"):
    g = G[G.domain == d]
    print(d, "n", len(g), "q_all<0.05:", int((g.q_all < 0.05).sum()), "q_domain<0.05:", int((g.q_domain < 0.05).sum()))
g = G[(G.domain == "emulation") & G.q_bshuf.notna()]
both = g[(g.q_domain < 0.05) & (g.q_bshuf < 0.05)]
print("emulation cells with benchmark shuffle:", len(g), "min q_bshuf", round(g.q_bshuf.min(), 3), "sign-flip AND shuffle BH survivors:", len(both))
print(both[["src", "cell", "metric", "contrast", "p", "bshuf_p", "q_domain", "q_bshuf"]].to_string())
bal = G[(G.domain == "balance") & (G.src.isin(["v17", "v18af"]))]
print("\nconfirmation-set balance cells (v17 new15 / v18 AF5) surviving q_all:")
print(bal[(bal.cell.str.startswith(("new15", "AF5"))) & (bal.q_all < 0.05)][["src", "cell", "metric", "p", "q_all"]].to_string())
print("\nconfirmation-set emulation cells surviving q_all:")
em = G[(G.domain == "emulation") & G.cell.str.startswith(("new15", "AF5"))]
print(em[em.q_all < 0.05][["src", "cell", "metric", "p", "q_all", "bshuf_p"]].to_string())
