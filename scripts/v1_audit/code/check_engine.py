#!/usr/bin/env python
"""v1 audit: engine invariants on one real trial (aggregates only; no identifiers printed).
  (a) reproduce core/restricted_cells.parquet for P5 main base / ECG / CLMBR and Flags main base (loghr, se, n_pairs, 58 SMDs)
  (b) 1:1 and 1:3 matching invariants: anchors from the smaller arm, no unit reused, |logit diff| <= caliper width,
      width = cal * sqrt((var_t + var_c) / 2) of the logit
  (c) |SMD| for every held-out component vs an independent pandas implementation (pooled pre-match SD, ddof 1)
  (d) determinism (two runs identical)
  (e) L2 PS convergence: lbfgs n_iter_ vs max_iter 5000 for each rung x arm design (warnings are silenced in v13_common)
Usage: check_engine.py <trial>"""
import sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v21")
import paper2_grid as G
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import v13_common as V13
SP, E, C = G.SP, G.E, G.C
n = sys.argv[1] if len(sys.argv) > 1 else "rely"
t0 = time.time()
T = E.load_trial(n) if n in SP.AF.V.OLD else E.load_trial(n, cache=False)
t = T.t; r = np.arange(len(t))
b5, _, _ = C.designs(T, n, C.P5DX)
X1 = T.cov.iloc[r][T.demo].to_numpy(float)
Fl, _, finfo = G.flags_matrix(T, n)
des = {("P5", "base"): b5, ("P5", "ECG"): np.hstack([b5, T.ecg_pc]), ("P5", "CLMBR"): np.hstack([b5, T.clm_pc]),
       ("P5", "ECG+CLMBR"): np.hstack([b5, T.clm_pc, T.ecg_pc]), ("Flags", "base"): np.hstack([X1, Fl]),
       ("Flags", "CLMBR"): np.hstack([X1, Fl, T.clm_pc]), ("P1", "CLMBR"): np.hstack([X1, T.clm_pc]),
       ("clinical", "base"): T.X_core, ("hdPS200", "base"): np.hstack([T.X_dx, T.hd(200, t=t, rows=r)])}
R = pd.read_parquet(G.OUT / "restricted_cells.parquet")
R = R[(R.trial == n) & (R.config == "main")]
VN = G.VN
print(f"trial {n}: n_rows>=11: {len(t) >= 11}; load {time.time() - t0:.0f}s")
# (a) reproduce
for (rg, a), X in des.items():
    if (rg, a) in (("P1", "CLMBR"), ("Flags", "CLMBR"), ("clinical", "base"), ("hdPS200", "base")):
        continue
    o = E.run_cell(T, X, rows=r, cstat=None)
    ref = R[(R.rung == rg) & (R.arm == a)].iloc[0]
    dev = max(abs(o["loghr"] - ref.loghr), abs(o["se"] - ref.se), abs(o["n_pairs"] - ref.n_pairs),
              np.nanmax(np.abs(np.array([o[f"smd:{c}"] for c in VN], float) - ref[[f"smd:{c}" for c in VN]].to_numpy(float))))
    print(f"(a) {rg}/{a}: max |dev| vs restricted_cells = {dev:.2e}")
    o2 = E.run_cell(T, X, rows=r, cstat=None)
    print(f"(d) {rg}/{a}: rerun identical = {all((o[k] == o2[k]) or (np.isnan(o[k]) and np.isnan(o2[k])) for k in o if k != 'secs')}")
# (b) matching invariants
for (rg, a) in (("P5", "base"), ("P5", "ECG+CLMBR")):
    lg = V13.ps_logit(des[(rg, a)], t)
    width = 0.2 * np.sqrt((lg[t == 1].var() + lg[t == 0].var()) / 2)
    anchor = 1 if (t == 1).sum() <= (t == 0).sum() else 0
    for ratio in (1, 3):
        idx, cl, w = V13.match(lg, t, cal=0.2, ratio=ratio)
        anc = np.unique(cl)
        others = idx[len(anc):] if ratio > 1 else idx[len(idx) // 2:]
        ok_arm = bool((t[anc] == anchor).all() and (t[others] != anchor).all())
        reuse = bool(len(np.unique(others)) != len(others) or len(np.unique(anc)) != len(anc))
        if ratio == 1:
            pairs_a, pairs_o = idx[: len(idx) // 2], idx[len(idx) // 2:]
        else:
            pairs_a, pairs_o = cl[len(anc):], others
        maxd = float(np.max(np.abs(lg[pairs_a] - lg[pairs_o]))) / width
        wsum = pd.Series(w[len(anc):]).groupby(cl[len(anc):]).sum() if ratio > 1 else pd.Series([1.0])
        print(f"(b) {rg}/{a} 1:{ratio}: anchors from smaller arm & others from larger: {ok_arm}; any unit reused: {reuse}; "
              f"max |dlogit| / width = {maxd:.3f}; control weights per anchor sum to 1: {bool(np.allclose(wsum, 1))}")
# (c) SMD formula vs independent implementation, P5 base main matched sample
lg = V13.ps_logit(b5, t)
idx, cl, w = V13.match(lg, t, cal=0.2, ratio=1)
H = T.H
comp = E.smd_components(H.to_numpy(float), t, idx, w, t[idx])
Hm = H.iloc[idx]; tm = t[idx]
m1, m0 = Hm[tm == 1].mean(), Hm[tm == 0].mean()
sd = np.sqrt((H[t == 1].var(ddof=1) + H[t == 0].var(ddof=1)) / 2)
ind = ((m1 - m0).abs() / sd).replace([np.inf], np.nan).to_numpy()
ind[(sd == 0).to_numpy()] = np.nan
print(f"(c) SMD components: {H.shape[1]} columns; max |engine - independent| = {np.nanmax(np.abs(comp - ind)):.2e}; "
      f"NaN pattern equal: {bool((np.isnan(comp) == np.isnan(ind)).all())}")
# (e) convergence of the L2 PS
for (rg, a), X in des.items():
    Xs = StandardScaler().fit_transform(X)
    m = LogisticRegression(C=1.0, max_iter=5000).fit(Xs, t)
    print(f"(e) {rg}/{a}: p = {X.shape[1]}, lbfgs n_iter = {int(m.n_iter_[0])} (max 5000), "
          f"in-sample AUC-free check: max |coef| = {np.abs(m.coef_).max():.2f}")
print(f"done {time.time() - t0:.0f}s")
