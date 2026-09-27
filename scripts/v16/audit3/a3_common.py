"""Round-3 audit helpers (own implementations; do not call sweep summary code)."""
import itertools
from functools import lru_cache

import numpy as np
import pandas as pd

A = "/mnt/raid0/rbc58/ecg-tte/audits/"
OUT = A + "claude-v16-audit3/"
CLUSTER = {"aristotle": "DOAC", "rocket-af": "DOAC", "rely": "DOAC", "emperor-preserved-v2": "SGLT2", "empa-reg": "SGLT2",
           "elite-ii": "ARB", "ontarget": "ARB", "east-afnet4": "AF", "cabana-v2": "AF", "allhat": "HTN", "value": "HTN",
           "ascot": "HTN", "life": "HTN", "comet": "comet", "paradigm-hf-seq": "paradigm", "transform-hf": "transform",
           "plato": "plato", "carolina": "carolina"}
PHYS = ["comet", "paradigm-hf-seq", "transform-hf", "elite-ii", "life", "emperor-preserved-v2", "east-afnet4", "cabana-v2"]


@lru_cache(None)
def S(k):
    return np.array(list(itertools.product((-1.0, 1.0), repeat=k)))


def flip(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    k = len(d)
    if k == 0:
        return np.nan
    obs = abs(d.mean())
    M = S(k) if k <= 20 else np.random.default_rng(5).choice([-1., 1.], size=(100000, k))
    return float(np.mean(np.abs(M @ np.abs(d)) / k >= obs - 1e-12))


def cluster_p(d):
    d = d.dropna()
    return flip(d.groupby(d.index.map(CLUSTER)).mean().values)


def loo_max(d):
    d = d.dropna()
    return max(flip(d.drop(t).values) for t in d.index)


def bh(p):
    p = np.asarray(p, float)
    q = np.full(len(p), np.nan)
    ok = np.isfinite(p)
    pv = p[ok]
    m = len(pv)
    if not m:
        return q
    o = np.argsort(pv)
    a = pv[o] * m / np.arange(1, m + 1)
    a = np.minimum.accumulate(a[::-1])[::-1]
    qq = np.empty(m)
    qq[o] = np.minimum(a, 1)
    q[ok] = qq
    return q


def love_count(M):
    """M: trials x vars |SMD| array -> # vars with nanmedian < 0.1 (vars with any finite value)."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(M, axis=-2)
    return (med < 0.1).sum(-1)


def love_swap(a, b, ndraw=20000, seed=4242, groups=None):
    """two-sided arm-swap permutation for love(a) - love(b); a, b trials x vars."""
    keep = np.isfinite(a).any(0) | np.isfinite(b).any(0)
    a, b = a[:, keep], b[:, keep]
    obs = int(love_count(a) - love_count(b))
    units = np.arange(len(a)) if groups is None else pd.factorize(np.asarray(groups))[0]
    nu = units.max() + 1
    Sg = (np.array(list(itertools.product((0, 1), repeat=nu)), bool) if nu <= 12
          else np.random.default_rng(seed).integers(0, 2, (ndraw, nu)).astype(bool))
    null = []
    for i in range(0, len(Sg), 400):
        s = Sg[i:i + 400][:, units][:, :, None]
        null.append(love_count(np.where(s, b[None], a[None])) - love_count(np.where(s, a[None], b[None])))
    null = np.concatenate(null)
    return obs, float(np.mean(np.abs(null) >= abs(obs)))
