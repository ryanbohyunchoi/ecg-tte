import sys; sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v16")
import numpy as np, s6_balance as S
from scipy.stats import energy_distance as ed1, ks_2samp
from scipy.spatial.distance import cdist
rng = np.random.default_rng(0)
# 1D check vs scipy (scipy returns sqrt of the V-statistic energy distance)
x, y = rng.normal(0, 1, (400, 1)), rng.normal(0.3, 1.2, (300, 1))
print("1D energy: ours", S.energy_distance(x, y), "scipy^2", ed1(x[:, 0], y[:, 0]) ** 2)
# multi-D vs brute force
X, Y = rng.normal(0, 1, (500, 7)), rng.normal(0.2, 1, (450, 7))
bf = 2 * cdist(X, Y).mean() - cdist(X, X).mean() - cdist(Y, Y).mean()
print("7D energy: ours", S.energy_distance(X, Y), "brute", bf)
# same distribution -> near 0, permutation p uniform-ish
Z1, Z2 = rng.normal(0, 1, (300, 5)), rng.normal(0, 1, (300, 5))
print("null energy", S.energy_distance(Z1, Z2), "perm", S.energy_perm(Z1, Z2, nperm=199, seed=1))
print("alt perm", S.energy_perm(X[:300], Y[:300], nperm=199, seed=1))
# Mahalanobis: lambda effect on identity-cov data; compare exact with lambda=0
t = np.r_[np.ones(500), np.zeros(450)].astype(int); Z = np.vstack([X, Y])
Si = S._pooled_cov_inv(Z, t)
d = Z[t == 1].mean(0) - Z[t == 0].mean(0)
Zc = Z.copy()
for g in (0, 1): Zc[t == g] -= Zc[t == g].mean(0)
Sx = Zc.T @ Zc / (len(t) - 2)
print("maha lam0.1", np.sqrt(d @ Si @ d), "exact", np.sqrt(d @ np.linalg.inv(Sx) @ d), "true", np.sqrt(7 * .04))
# highly collinear case: shows shrinkage bias of ridge
W = rng.normal(0, 1, (950, 1)) @ np.ones((1, 50)) + 0.05 * rng.normal(0, 1, (950, 50)); W[t == 1] += 0.1
W = (W - W.mean(0)) / W.std(0)
d = W[t == 1].mean(0) - W[t == 0].mean(0)
print("collinear maha lam0.1", np.sqrt(d @ S._pooled_cov_inv(W, t) @ d))
# KS: s6 uses scipy ks_2samp directly on unweighted matched values: fine for 1:1 matching
