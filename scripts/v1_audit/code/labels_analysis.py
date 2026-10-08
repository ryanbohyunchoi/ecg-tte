"""v1 audit: recheck label analyses (paper2_grid.labels) from aggregate CSVs."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v21")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
C = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/"
LP = pd.read_csv(C + "labels_physiologic.csv"); LD = pd.read_csv(C + "labels_domain.csv"); LPT = pd.read_csv(C + "labels_per_trial.csv")
SP = pd.read_csv(C + "labels_spearman.csv")
def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); r = p[o] * n / np.arange(1, n + 1)
    r = np.minimum.accumulate(r[::-1])[::-1]; q = np.empty(n); q[o] = np.minimum(r, 1); return q
def perm_diff(g, lab, n=10000):
    g, lab = np.asarray(g, float), np.asarray(lab, bool); ok = np.isfinite(g); g, lab = g[ok], lab[ok]
    obs = g[lab].mean() - g[~lab].mean(); rng = np.random.default_rng(0); null = np.empty(n)
    for j in range(n):
        p = rng.permutation(lab); null[j] = g[p].mean() - g[~p].mean()
    return obs, (np.abs(null) >= abs(obs) - 1e-12).mean()
m = LP[(LP.set == "S32") & (LP.config == "main")]
print(m[["arm", "endpoint", "n_yes", "n_no", "diff_yes_minus_no", "perm_p", "q_family", "relred_yes", "relred_yes_lo", "relred_yes_hi", "relred_no", "relred_no_lo", "relred_no_hi", "mean_gain_yes", "mean_gain_no"]].round(4).to_string(index=False))
print("family sizes per (set,config):", LP.groupby(["set", "config"]).perm_p.count().unique())
mx = 0
for (st, cfg), g in LP.groupby(["set", "config"]):
    mx = max(mx, np.nanmax(np.abs(bh(g.perm_p.values) - g.q_family.values)))
print("max |q_family - BH(perm_p)|", mx)
L = LPT[LPT.in_S32]
for a in ["ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"]:
    d = L[L.arm == a]
    for ep in ("gain_m54", "gain_lt01_54", "gain_absd"):
        o, p = perm_diff(d[ep].values, d.physiologic.values)
        row = m[(m.arm == a) & m.endpoint.str.startswith(ep.replace("gain_", "")[:4])].iloc[0]
        print(f"  recompute {a:10s} {ep:13s} diff {o:.5f} (csv {row.diff_yes_minus_no:.5f}) p {p:.4f} (csv {row.perm_p:.4f})")
print("## domains S32 main (primary + union)")
dm = LD[(LD.set == "S32") & (LD.config == "main")]
print(dm[["label_source", "label_domain", "arm", "n_items", "n_labelled", "n_not", "mean_gain_labelled", "mean_gain_not", "perm_p", "tested", "q_family"]].round(4).to_string(index=False))
print("domain family sizes:", LD[LD.tested].groupby(["set", "config", "label_source"]).perm_p.count().unique())
mx = 0
for k, g in LD.groupby(["set", "config", "label_source"]):
    g = g[g.tested & g.perm_p.notna()]
    mx = max(mx, np.nanmax(np.abs(bh(g.perm_p.values) - g.q_family.values)))
print("max |q_domain - BH|", mx)
print("## spearman S32 main"); print(SP[(SP.set == "S32") & (SP.config == "main")].round(4).to_string(index=False))
