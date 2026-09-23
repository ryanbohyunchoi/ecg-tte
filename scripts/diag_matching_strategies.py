"""Matching-strategy diagnostic: clinical PSM vs ECG / EHR-embedding strategies.

Compares, on one common population, pure embedding cosine matching, embedding-only
PS, clinical PS +/- embedding PCs, PS-caliper->cosine hybrids, and the
"claims-only" held-out design (EF/labs/vitals excluded from the PS and used only
to evaluate balance). Aggregate output only (SMD summaries).

Example (COMET, 2026-09-23 audit inputs):
  python scripts/diag_matching_strategies.py \
    --common-inputs  $AUD/comet-cosine-comparison-v3-HKXiJR7g/report/restricted_common_inputs \
    --ecg-emb-glob   "$AUD/comet-bcl-comparison-FZIo043w/linked/restricted_embeddings_part-*.parquet" \
    --ehr-emb-glob   "$AUD/comet-clmbr-full-NAyb4G2x/report/restricted_embeddings_part-*.parquet" \
    --imputation 1 --output-dir $AUD/claude-matching-diagnostic
"""
import argparse, json, glob, sys
import numpy as np, pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ap = argparse.ArgumentParser()
ap.add_argument("--common-inputs", required=True, help="dir with restricted_completed_XX.csv + restricted_row_keys.json")
ap.add_argument("--ecg-emb-glob", required=True)
ap.add_argument("--ehr-emb-glob", required=True)
ap.add_argument("--imputation", type=int, default=1)
ap.add_argument("--output-dir", required=True)
args = ap.parse_args()
CIN, IMP = args.common_inputs, args.imputation
rng = np.random.default_rng(0)

keys = json.load(open(f"{CIN}/restricted_row_keys.json"))
cov = pd.read_csv(f"{CIN}/restricted_completed_{IMP:02d}.csv")
cov.index = keys
cov["male"] = (cov.pop("recorded_sex").astype(str).str.lower().str.startswith("m")).astype(float)
t = (cov.pop("treatment_arm").astype(str).str.contains("metoprolol")).astype(int)  # 1 = metoprolol (smaller arm)
cov = cov.astype(float)

def load_emb(pattern):
    d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(pattern))])
    return pd.DataFrame(np.stack(d.embedding.to_numpy()), index=d.patient_key.values)

ecg = load_emb(args.ecg_emb_glob)
clm = load_emb(args.ehr_emb_glob)
common = cov.index.intersection(ecg.index).intersection(clm.index)
cov, t, ecg, clm = cov.loc[common], t.loc[common].to_numpy(), ecg.loc[common].to_numpy(float), clm.loc[common].to_numpy(float)
print(f"imputation {IMP}: common n={len(common)} metoprolol={t.sum()} carvedilol={(1-t).sum()}")

CLAIMS = [c for c in cov.columns if c not in
          ["lvef", "sbp", "dbp", "heart_rate", "bmi", "creatinine", "potassium", "sodium", "hemoglobin"]]
HELDOUT = [c for c in cov.columns if c not in CLAIMS]
pre_sd = np.sqrt((cov[t == 1].var() + cov[t == 0].var()) / 2)

def smd(idx_t, idx_c, cols):
    d = (cov.iloc[idx_t][cols].mean() - cov.iloc[idx_c][cols].mean()) / pre_sd[cols]
    return d.abs()

def prep(E, k, whiten):
    E = E - E.mean(0)
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    Z = U[:, :k] * (1 if whiten else S[:k])
    return Z / np.linalg.norm(Z, axis=1, keepdims=True), U[:, :k] * S[:k]

def logit_ps(X):
    X = StandardScaler().fit_transform(X)
    p = LogisticRegression(C=1.0, max_iter=5000).fit(X, t).predict_proba(X)[:, 1]
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))

def assign(cost, caliper_mask=None):
    """Optimal 1:1 metoprolol->carvedilol; forbidden edges dropped post-hoc."""
    ti, ci = np.where(t == 1)[0], np.where(t == 0)[0]
    C = cost[np.ix_(ti, ci)].copy()
    if caliper_mask is not None:
        C[~caliper_mask[np.ix_(ti, ci)]] = 1e6
    r, c = linear_sum_assignment(C)
    ok = C[r, c] < 1e6
    return ti[r[ok]], ci[c[ok]]

def ps_greedy(lg, cal=0.2):
    width = cal * np.sqrt((lg[t == 1].var() + lg[t == 0].var()) / 2)
    ti = np.where(t == 1)[0]; ci = list(np.where(t == 0)[0])
    ti = ti[np.argsort(-lg[ti])]; avail = np.ones(len(t), bool)
    mt, mc = [], []
    cl = np.array(ci); order = np.argsort(lg[cl]); cl = cl[order]; vals = lg[cl]
    for i in ti:
        j = np.searchsorted(vals, lg[i]); best, bd = None, width
        for k in range(max(0, j - 50), min(len(cl), j + 50)):
            if avail[cl[k]] and abs(vals[k] - lg[i]) <= bd:
                best, bd = cl[k], abs(vals[k] - lg[i])
        if best is not None:
            avail[best] = False; mt.append(i); mc.append(best)
    return np.array(mt), np.array(mc)

def cos_cost(Z):
    return 1 - Z @ Z.T

def ps_caliper_mask(lg, cal=0.2):
    width = cal * np.sqrt((lg[t == 1].var() + lg[t == 0].var()) / 2)
    return np.abs(lg[:, None] - lg[None, :]) <= width

ecg_raw = ecg / np.linalg.norm(ecg, axis=1, keepdims=True)
ecg_z, ecg_pcs = prep(ecg, 32, whiten=True)
clm_z, clm_pcs = prep(clm, 64, whiten=True)
X_all, X_claims = cov.to_numpy(), cov[CLAIMS].to_numpy()

rows = []
def report(name, mt, mc):
    a, h = smd(mt, mc, list(cov.columns)), smd(mt, mc, HELDOUT)
    rows.append(dict(method=name, pairs=len(mt), met_ret=round(len(mt) / t.sum(), 3),
                     max_smd_all=a.max(), mean_smd_all=a.mean(), n_ge_0_1=int((a >= .1).sum()),
                     lvef=a["lvef"], afib=a["atrial_fibrillation"], age=a["age_at_index"],
                     max_smd_heldout=h.max(), mean_smd_heldout=h.mean()))

allidx = np.arange(len(t))
report("0 unmatched", allidx[t == 1], allidx[t == 0])
report("1 ECG raw cosine (as run)", *assign(cos_cost(ecg_raw)))
report("2 ECG centered+whitened cosine", *assign(cos_cost(ecg_z)))
report("3 CLMBR centered+whitened cosine", *assign(cos_cost(clm_z)))
report("4 ECG+CLMBR concat cosine", *assign(cos_cost(np.hstack([ecg_z, clm_z]) / np.sqrt(2))))
report("5 PS: ECG PCs only", *ps_greedy(logit_ps(ecg_pcs)))
report("6 PS: CLMBR PCs only", *ps_greedy(logit_ps(clm_pcs)))
report("7 PS: ECG+CLMBR PCs only", *ps_greedy(logit_ps(np.hstack([ecg_pcs, clm_pcs]))))
lg_all = logit_ps(X_all)
report("8 PS: all clinical (ref)", *ps_greedy(lg_all))
report("9 PS: clinical + ECG PCs", *ps_greedy(logit_ps(np.hstack([X_all, ecg_pcs]))))
report("10 PS: clinical + ECG + CLMBR PCs", *ps_greedy(logit_ps(np.hstack([X_all, ecg_pcs, clm_pcs]))))
report("11 Hybrid: clin-PS caliper -> ECG cosine", *assign(cos_cost(ecg_z), ps_caliper_mask(lg_all)))
lg_cl = logit_ps(X_claims)
report("12 PS: claims-only (no EF/labs/vitals)", *ps_greedy(lg_cl))
report("13 PS: claims + ECG PCs", *ps_greedy(logit_ps(np.hstack([X_claims, ecg_pcs]))))
report("14 PS: claims + CLMBR PCs", *ps_greedy(logit_ps(np.hstack([X_claims, clm_pcs]))))
report("15 PS: claims + ECG + CLMBR PCs", *ps_greedy(logit_ps(np.hstack([X_claims, ecg_pcs, clm_pcs]))))
report("16 Hybrid: claims-PS caliper -> ECG cosine", *assign(cos_cost(ecg_z), ps_caliper_mask(lg_cl)))

# How much do embeddings "know" the key confounders? (5-fold CV AUC / R2)
from sklearn.model_selection import cross_val_score
diag = {}
for nm, Z in [("ECG", ecg_pcs), ("CLMBR", clm_pcs)]:
    Zs = StandardScaler().fit_transform(Z)
    diag[nm] = dict(
        auc_treatment=cross_val_score(LogisticRegression(max_iter=3000), Zs, t, cv=5, scoring="roc_auc").mean(),
        auc_afib=cross_val_score(LogisticRegression(max_iter=3000), Zs, (cov.atrial_fibrillation > .5).astype(int), cv=5, scoring="roc_auc").mean(),
        auc_lvef_le35=cross_val_score(LogisticRegression(max_iter=3000), Zs, (cov.lvef <= 35).astype(int), cv=5, scoring="roc_auc").mean())
diag["clinical"] = dict(auc_treatment=cross_val_score(LogisticRegression(max_iter=5000), StandardScaler().fit_transform(X_all), t, cv=5, scoring="roc_auc").mean())

out = pd.DataFrame(rows).set_index("method").round(3)
pd.set_option("display.width", 250)
print(out.to_string())
print("\nEmbedding information (5-fold CV AUC):")
print(pd.DataFrame(diag).T.round(3).to_string())
out.to_csv(f"{args.output_dir}/summary_imp{IMP}.csv")
