import itertools, numpy as np, pandas as pd
from functools import lru_cache
CLUSTER = {"aristotle": "DOAC", "rocket-af": "DOAC", "rely": "DOAC", "emperor-preserved-v2": "SGLT2", "empa-reg": "SGLT2",
           "elite-ii": "ARB", "ontarget": "ARB", "east-afnet4": "AF", "cabana-v2": "AF", "allhat": "HTN", "value": "HTN",
           "ascot": "HTN", "life": "HTN", "comet": "comet", "paradigm-hf-seq": "paradigm", "transform-hf": "transform",
           "plato": "plato", "carolina": "carolina"}
@lru_cache(None)
def S(k): return np.array(list(itertools.product((-1.0, 1.0), repeat=k)))
def flip(d):
    d = np.asarray(d, float); d = d[np.isfinite(d)]
    k = len(d); obs = abs(d.mean())
    M = S(k) if k <= 20 else np.random.default_rng(5).choice([-1., 1.], size=(100000, k))
    return float(np.mean(np.abs(M @ np.abs(d)) / k >= obs - 1e-12))
def metric(x, m):
    if m == "absd": return (x.loghr - x.rb).abs()
    if m == "z2": return (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2)
    return x[m]
def diff(a, b, m):
    a = a.drop_duplicates("trial").set_index("trial"); b = b.drop_duplicates("trial").set_index("trial")
    t = a.index.intersection(b.index)
    return (metric(a.loc[t], m) - metric(b.loc[t], m)).dropna()
def summ(d):
    cl = d.groupby(d.index.map(CLUSTER)).mean()
    return dict(d=d.mean(), k=f"{(d<0).sum()}/{len(d)}", p=flip(d.values), cl_p=flip(cl.values),
                loo_pmax=max(flip(d.drop(t).values) for t in d.index))
def shuffle(a, b, m, nperm=20000, seed=11):
    a = a.drop_duplicates("trial").set_index("trial"); b = b.drop_duplicates("trial").set_index("trial")
    t = a.index.intersection(b.index); a, b = a.loc[t], b.loc[t]
    ok = np.isfinite(a.loghr.values) & np.isfinite(b.loghr.values)
    la, lb, sa, sb, rb, rs = [v[ok] for v in (a.loghr.values, b.loghr.values, a.se.values, b.se.values, b.rb.values, b.rs.values)]
    def f(r, s):
        if m == "absd": return np.mean(np.abs(la - r) - np.abs(lb - r))
        return np.mean((la - r) ** 2 / (sa ** 2 + s ** 2) - (lb - r) ** 2 / (sb ** 2 + s ** 2))
    rng = np.random.default_rng(seed); o = f(rb, rs)
    nl = np.array([f(rb[p], rs[p]) for p in (rng.permutation(len(rb)) for _ in range(nperm))])
    # also: independent permutation of rb and rs (not joint) as sensitivity
    return dict(obs=o, null_mean=nl.mean(), p=float(np.mean(nl <= o)))
