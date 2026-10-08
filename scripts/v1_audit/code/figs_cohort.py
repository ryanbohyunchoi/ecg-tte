"""v1 audit: cohort totals, flags range, CV penalties (aggregates only)."""
import json, numpy as np, pandas as pd
C = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/"
R = "/home/rbc58/github/ecg-tte/"
PT = pd.read_csv(C + "per_trial.csv")
print("per_trial cols:", [c for c in PT.columns if not c.startswith("dom:")])
QT = json.load(open(R + "docs/v19/quality_tiers.json"))["trials"]
s32 = {t["key"] for t in QT if t["tier"].split(" - ")[0] != "Limited"}
b = PT[(PT.rung == "P5") & (PT.config == "main") & (PT.arm == "base") & PT.in_S32]
print("S32 trials", len(b), "keys match tiers:", set(b.key) == s32)
print("n sum", int((b.n_t + b.n_c).sum()), "median", (b.n_t + b.n_c).median(), "min", (b.n_t + b.n_c).min(), "max", (b.n_t + b.n_c).max())
print("pairs sum", int(b.n_pairs.sum()), "median", b.n_pairs.median(), "min", b.n_pairs.min(), "max", b.n_pairs.max())
print("retain mean (per_trial)", round(b.retain.mean(), 4), "pairs/min(nt,nc) mean", round((b.n_pairs / np.minimum(b.n_t, b.n_c)).mean(), 4))
# is n constant across rungs/arms within trial?
g = PT[PT.in_S32 & (PT.config == "main")].assign(N=lambda d: d.n_t + d.n_c).groupby("key").N.nunique()
print("n varies across rung/arm within trial:", int((g > 1).sum()))
L = json.load(open(C + "log.json"))
reg2key = {t["registry"]: t["key"] for t in QT}
nf = pd.Series({d["trial"]: d["n_flags"] for d in L})
k = nf.index.map(reg2key)
print("flags 38: min", nf.min(), "max", nf.max(), "median", nf.median(), "n", len(nf))
n32 = nf[[reg2key.get(t) in s32 for t in nf.index]]
print("flags 32: min", n32.min(), "max", n32.max(), "median", n32.median(), "n", len(n32))
FL = pd.read_csv(C + "flagscv_log.csv")
print("flagscv_log cols", list(FL.columns))
c = FL["C_FlagsCV_base"]
print("C_FlagsCV_base: min", c.min(), "max", c.max(), "1/C range", 1 / c.max(), 1 / c.min())
print(c.value_counts().sort_index().to_dict())
