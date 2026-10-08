"""v1 audit: recompute q-counts and BH families from sensitivity.csv (aggregates only)."""
import numpy as np, pandas as pd
C = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/"
S = pd.read_csv(C + "sensitivity.csv"); QC = pd.read_csv(C + "q_counts.csv")
def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); r = p[o] * n / np.arange(1, n + 1)
    r = np.minimum.accumulate(r[::-1])[::-1]; q = np.empty(n); q[o] = np.minimum(r, 1); return q
print(QC.to_string(index=False))
for st in ("S32", "S38"):
    s = S[S.set == st]
    print(st, "rows", len(s), "configs", s.groupby("config").size().to_dict())
    for fam, cols in (("bal", ["m54_p", "lt01_54_p", "m58_p", "lt01_58_p"]), ("agr", ["absd_p", "cons_p", "bshuf_p"])):
        long = s[cols].stack(dropna=True)
        q = pd.Series(bh(long.values), index=long.index).unstack()
        for c in cols:
            d = np.nanmax(np.abs(q[c].reindex(s.index).values - s[f"q_{c}_fam"].values))
            print(f"  {fam} family n_p={len(long)} {c}: max|q-recomputed|={d:.2e}")
    for c in ["m54_p"]:
        ok = s[c].notna(); qs = bh(s.loc[ok, c].values)
        print("  sweep m54 maxdiff", np.max(np.abs(qs - s.loc[ok, "q_m54_p_sweep"].values)))
    g = s.groupby("config")
    print("  n q_m54_fam<.05:", g.q_m54_p_fam.apply(lambda x: (x < .05).sum()).to_dict(), "total", (s.q_m54_p_fam < .05).sum())
    print("  n q_m54_sweep<.05:", g.q_m54_p_sweep.apply(lambda x: (x < .05).sum()).to_dict(), "total", (s.q_m54_p_sweep < .05).sum())
    anyb = s[["q_m54_p_fam", "q_lt01_54_p_fam", "q_m58_p_fam", "q_lt01_58_p_fam"]].lt(.05).any(axis=1)
    print("  rows any balance-family q<.05:", anyb.groupby(s.config).sum().to_dict(), anyb.sum())
    for c in ["q_absd_p_fam", "q_cons_p_fam", "q_bshuf_p_fam", "q_absd_p_sweep", "q_bshuf_p_sweep"]:
        print(f"  n {c}<.05:", int((s[c] < .05).sum()), "min", round(s[c].min(), 4))
    m = s[s.config == "main"]
    print("  main q_m54<.05 contrasts:", sorted(m[m.q_m54_p_fam < .05].contrast))
