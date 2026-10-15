"""Verifier check 1: Step 0 gate. Independent comparison of step0/results vs v21 results and recomputation of the
v21 headline from the cells (aggregates only)."""
import json
import os
import numpy as np
import pandas as pd

os.umask(0o077)
OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
V21 = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/mimic"
TR8 = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2", "peptic"]
P7 = TR8[:7]

g = json.load(open(f"{OUT}/step0/gate.json"))
print("gate.json:", g["gate"], "tables_exact", g["tables_exact"], "n_tables", g["n_tables"], "max_abs_diff", g["max_abs_diff"])
print("PASS file exists:", os.path.exists(f"{OUT}/step0/PASS"), "FAIL file exists:", os.path.exists(f"{OUT}/step0/FAIL"))

worst = 0.0
allsame = True
for k in TR8:
    for kind in ("arms", "vars"):
        a = pd.read_csv(f"{OUT}/step0/results/{k}_{kind}.csv")
        b = pd.read_csv(f"{V21}/results/{k}_{kind}.csv")
        if a.shape != b.shape or list(a.columns) != list(b.columns):
            allsame = False
            print(k, kind, "SHAPE/COLUMN MISMATCH")
            continue
        for c in a.columns:
            x, y = a[c], b[c]
            if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                xn, yn = x.to_numpy(float), y.to_numpy(float)
                if not np.array_equal(np.isnan(xn), np.isnan(yn)):
                    allsame = False
                    print(k, kind, c, "NaN pattern differs")
                m = ~np.isnan(xn)
                d = float(np.max(np.abs(xn[m] - yn[m]))) if m.any() else 0.0
                worst = max(worst, d)
            else:
                if not (x.fillna("").astype(str) == y.fillna("").astype(str)).all():
                    allsame = False
                    print(k, kind, c, "text differs")
print("step0 vs v21 arms+vars: identical structure", allsame, "max |diff|", worst)

# flags
fw = 0.0
for k in TR8:
    a = pd.read_parquet(f"{OUT}/step0/flags/{k}.parquet").set_index("pid").sort_index()
    b = pd.read_parquet(f"{V21}/flags/{k}.parquet").set_index("pid").sort_index()
    assert a.index.equals(b.index) and list(a.columns) == list(b.columns)
    fw = max(fw, float((a.astype(float) - b.astype(float)).abs().max().max()))
print("flags max |diff|", fw)

# v21 headline from step0 cells, own code
A = pd.concat([pd.read_csv(f"{OUT}/step0/results/{k}_arms.csv") for k in P7])
S = A[(A.base == "cvd5") & (A["pop"] == "all")]
m = {arm: S[S.arm == arm].set_index("trial").reindex(P7) for arm in ("base", "ECG", "permECG")}
mb, me, mp = (m[x].mean_smd.to_numpy(float) for x in ("base", "ECG", "permECG"))
rr = 100 * (1 - me.mean() / mb.mean())
rrp = 100 * (1 - mp.mean() / mb.mean())


def signflip_one(d):
    d = np.asarray(d, float)
    k = len(d)
    signs = np.array([[1 if (i >> j) & 1 else -1 for j in range(k)] for i in range(2 ** k)])
    null = (signs * np.abs(d)).mean(1)
    return float(np.mean(null >= d.mean() - 1e-12))


def boot(mb, ma, n, seed):
    rng = np.random.default_rng(seed)
    I = rng.integers(0, len(mb), size=(n, len(mb)))
    r = 100 * (1 - ma[I].mean(1) / mb[I].mean(1))
    return np.percentile(r, [2.5, 97.5])


# v20 convention: 2,000 resamples, seed 0, trials in alphabetical (pivot) order
order = sorted(P7)
mbs = m["base"].reindex(order).mean_smd.to_numpy(float)
mes = m["ECG"].reindex(order).mean_smd.to_numpy(float)
ci_v20 = boot(mbs, mes, 2000, 0)
ci_new = boot(mb, me, 4000, 20261001)
print(f"ECG relred {rr:.1f}% v20-CI ({ci_v20[0]:.1f}-{ci_v20[1]:.1f}) paper-CI ({ci_new[0]:.1f} to {ci_new[1]:.1f})")
print("lower", f"{int((me < mb).sum())}/7", "signflip P", round(signflip_one(mb - me), 3))
print("pct<0.1 base -> ECG", round(m["base"].pct_bal.mean(), 1), "->", round(m["ECG"].pct_bal.mean(), 1))
print(f"permuted ECG relred {rrp:.1f}%")
