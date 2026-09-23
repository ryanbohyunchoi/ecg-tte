"""Long-tail balance: do unstructured representations improve balance on
pre-treatment characteristics that the PS does not include?

Base PS = full clinical covariate set (one MICE-completed dataset). Arms add:
ECG (phenotype scores + 32 centred PCs), CLMBR (64 centred PCs), hdPS-style
empirical covariates, and combinations. Panel features (build_preindex_panel.py)
are split per domain (seeded) into pool A (eligible for hdPS selection) and pool B
(evaluation only; never enters any PS). hdPS ranks pool-A binary features by
|log prevalence ratio| between arms (exposure-only; no outcome use).

Note: CLMBR's input includes coded history, so it has seen codes like those in pool
B. The ECG has not, so ECG gains on pool B are information orthogonal to codes.

Aggregate output only: per-method balance summaries on pool B, pool A and the PS
covariates, plus retention.
"""
import argparse
import glob
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ap = argparse.ArgumentParser()
ap.add_argument("--common-inputs", required=True)
ap.add_argument("--imputation", type=int, default=1)
ap.add_argument("--panel", required=True)
ap.add_argument("--panel-dictionary", required=True)
ap.add_argument("--ecg-emb-glob", required=True)
ap.add_argument("--ehr-emb-glob", required=True)
ap.add_argument("--ecg-phenotypes", required=True)
ap.add_argument("--hdps-k", type=int, default=100)
ap.add_argument("--split-seed", type=int, default=0)
ap.add_argument("--output-dir", required=True)
args = ap.parse_args()

CIN = args.common_inputs
keys = json.load(open(f"{CIN}/restricted_row_keys.json"))
cov = pd.read_csv(f"{CIN}/restricted_completed_{args.imputation:02d}.csv", index_col=None)
cov.index = keys
cov["male"] = cov.pop("recorded_sex").astype(str).str.lower().str.startswith("m").astype(float)
t_s = cov.pop("treatment_arm").astype(str).str.contains("metoprolol").astype(int)
cov = cov.astype(float)


def emb(pattern):
    d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(pattern))])
    return pd.DataFrame(np.stack(d.embedding.to_numpy()), index=d.patient_key.values)


def pcs(E, k):
    X = E - E.mean(0)
    U, S, _ = np.linalg.svd(X, full_matrices=False)
    return U[:, :k] * S[:k]


ecg, clm = emb(args.ecg_emb_glob), emb(args.ehr_emb_glob)
ph = pd.read_parquet(args.ecg_phenotypes).set_index("patient_key")
panel = pd.read_parquet(args.panel).set_index("patient_key")
common = cov.index.intersection(ecg.index).intersection(clm.index).intersection(ph.index).intersection(panel.index)
cov, t = cov.loc[common], t_s.loc[common].to_numpy()
ecg_f = np.hstack([ph.loc[common].to_numpy(float), pcs(ecg.loc[common].to_numpy(float), 32)])
clm_f = pcs(clm.loc[common].to_numpy(float), 64)
panel = panel.loc[common]

dic = pd.read_csv(args.panel_dictionary)
rng = np.random.default_rng(args.split_seed)
pool = {}
for dom, grp in dic.groupby("domain"):
    f = grp.feature.to_numpy().copy()
    rng.shuffle(f)
    pool[dom] = (f[: len(f) // 2], f[len(f) // 2:])
A = [f for a, _ in pool.values() for f in a]
B = [f for _, b in pool.values() for f in b]
# labs contribute numeric value + measured flag; evaluate numeric on observed values
expand = lambda fs: fs + [f.replace("lab_", "labn_") for f in fs if f.startswith("lab_")]
A, B = expand(A), expand(B)

# hdPS: exposure-only prioritisation over pool-A binary features
bin_A = [f for f in A if not f.startswith("lab_")]
PA = panel[bin_A]
p1, p0 = PA[t == 1].gt(0).mean() + 1e-3, PA[t == 0].gt(0).mean() + 1e-3
hd = (np.log(p1 / p0)).abs().sort_values(ascending=False).index[: args.hdps_k]
hd_f = panel[hd].gt(0).astype(float).to_numpy()

X_clin = cov.to_numpy()
# Low-dimensional bases: demographics only; claims-like (no EF/labs/vitals)
DEMO = ["age_at_index", "male", "index_year"]
CLAIMS = [c for c in cov.columns if c not in
          ["lvef", "sbp", "dbp", "heart_rate", "bmi", "creatinine", "potassium", "sodium", "hemoglobin"]]
X_demo, X_claims = cov[DEMO].to_numpy(), cov[CLAIMS].to_numpy()


def smd_table(mt, mc, cols, frame):
    out = []
    for c in cols:
        v = frame[c].to_numpy(float)
        a, b = v[t == 1], v[t == 0]
        m1, m0 = ~np.isnan(a), ~np.isnan(b)
        sd = np.sqrt((np.nanvar(a, ddof=1) + np.nanvar(b, ddof=1)) / 2) if m1.sum() > 1 and m0.sum() > 1 else np.nan
        x, y = v[mt], v[mc]
        if not sd or np.isnan(sd) or sd == 0:
            continue
        out.append(abs(np.nanmean(x) - np.nanmean(y)) / sd)
    return np.array(out)


def logit_ps(X):
    X = StandardScaler().fit_transform(X)
    p = LogisticRegression(C=1.0, max_iter=5000).fit(X, t).predict_proba(X)[:, 1]
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def ps_greedy(lg, cal=0.2):
    width = cal * np.sqrt((lg[t == 1].var() + lg[t == 0].var()) / 2)
    ti = np.where(t == 1)[0]
    ti = ti[np.argsort(-lg[ti])]
    cl = np.where(t == 0)[0]
    cl = cl[np.argsort(lg[cl])]
    vals, avail, mt, mc = lg[cl], np.ones(len(t), bool), [], []
    for i in ti:
        j = np.searchsorted(vals, lg[i])
        best, bd = None, width
        for k in range(max(0, j - 60), min(len(cl), j + 60)):
            if avail[cl[k]] and abs(vals[k] - lg[i]) <= bd:
                best, bd = cl[k], abs(vals[k] - lg[i])
        if best is not None:
            avail[best] = False
            mt.append(i)
            mc.append(best)
    return np.array(mt), np.array(mc)


# Placebo: same dimensionality as the representation, pure noise (retention/trimming control)
noise = np.random.default_rng(1000 + args.split_seed).normal(size=(len(t), ecg_f.shape[1] + clm_f.shape[1]))
methods = {
    "unmatched": None,
    f"clinical+noise{noise.shape[1]} (placebo)": np.hstack([X_clin, noise]),
    "clinical": X_clin,
    "clinical+ECG": np.hstack([X_clin, ecg_f]),
    "clinical+CLMBR": np.hstack([X_clin, clm_f]),
    "clinical+ECG+CLMBR": np.hstack([X_clin, ecg_f, clm_f]),
    f"clinical+hdPS{args.hdps_k}": np.hstack([X_clin, hd_f]),
    f"clinical+hdPS{args.hdps_k}+ECG": np.hstack([X_clin, hd_f, ecg_f]),
    f"clinical+hdPS{args.hdps_k}+ECG+CLMBR": np.hstack([X_clin, hd_f, ecg_f, clm_f]),
    "demo": X_demo,
    "demo+ECG": np.hstack([X_demo, ecg_f]),
    "demo+CLMBR": np.hstack([X_demo, clm_f]),
    "demo+ECG+CLMBR": np.hstack([X_demo, ecg_f, clm_f]),
    f"demo+hdPS{args.hdps_k}": np.hstack([X_demo, hd_f]),
    f"demo+hdPS{args.hdps_k}+ECG+CLMBR": np.hstack([X_demo, hd_f, ecg_f, clm_f]),
    "claims": X_claims,
    "claims+ECG+CLMBR": np.hstack([X_claims, ecg_f, clm_f]),
    f"claims+hdPS{args.hdps_k}": np.hstack([X_claims, hd_f]),
    f"claims+hdPS{args.hdps_k}+ECG+CLMBR": np.hstack([X_claims, hd_f, ecg_f, clm_f]),
}
rows = []
idx = np.arange(len(t))
for name, X in methods.items():
    mt, mc = (idx[t == 1], idx[t == 0]) if X is None else ps_greedy(logit_ps(X))
    sB, sA, sC = smd_table(mt, mc, B, panel), smd_table(mt, mc, A, panel), smd_table(mt, mc, list(cov.columns), cov)
    rows.append(dict(method=name, pairs=len(mt), noise_sd=round(float(np.sqrt(2 / max(len(mt), 1))), 3),
                     B_n=len(sB), B_frac_gt_0_1=(sB > 0.1).mean(), B_mean=sB.mean(), B_p95=np.quantile(sB, 0.95),
                     A_frac_gt_0_1=(sA > 0.1).mean(), A_mean=sA.mean(),
                     ps_covs_max=sC.max(), clin32_n_gt_0_1=int((sC > 0.1).sum()),
                     lvef=float(smd_table(mt, mc, ["lvef"], cov)[0]),
                     afib=float(smd_table(mt, mc, ["atrial_fibrillation"], cov)[0]), imputation=args.imputation, split_seed=args.split_seed))
out = pd.DataFrame(rows).set_index("method")
out.to_csv(f"{args.output_dir}/longtail_imp{args.imputation}_seed{args.split_seed}.csv")
pd.set_option("display.width", 250)
print(f"n={len(t)} panel A={len(A)} B={len(B)} hdPS k={len(hd)}")
print(out.round(4).to_string())
