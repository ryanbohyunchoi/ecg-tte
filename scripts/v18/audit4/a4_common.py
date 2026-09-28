"""Round-4 audit helpers: own implementations (do not call v17_confirm / v18_* statistics code).

Only constants are imported from the engine (the 58-panel variable list and its groups)."""
import itertools
import json
import sys
from functools import lru_cache

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v16")
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts")
from v16_engine import VARS  # noqa: E402  (constant: (name, label, group))

A = "/mnt/raid0/rbc58/ecg-tte/audits/"
OUT = A + "claude-v18-audit4/"
REPO = "/home/rbc58/github/ecg-tte/"
V58 = [f"smd:{c}" for c, _, _ in VARS]
NC54 = [f"smd:{c}" for c, _, g in VARS if g != "Coded record"]
OLD18 = ['comet', 'paradigm-hf-seq', 'transform-hf', 'elite-ii', 'life', 'plato', 'aristotle', 'rocket-af', 'rely', 'allhat',
         'emperor-preserved-v2', 'east-afnet4', 'cabana-v2', 'ontarget', 'value', 'ascot', 'empa-reg', 'carolina']
NEW15 = ['leader', 'sustain6', 'rewind', 'declare', 'canvas', 'tecos', 'carmelina', 'valiant', 'insight', 'affirm', 'af-chf',
         'precision', 'amplify', 'lodestar', 'prove-it']
AF5 = ['frail-af', 'laaos3', 'protect-af', 'raft-af', 'active-w']
AF7 = ["aristotle", "rocket-af", "rely", "east-afnet4", "cabana-v2", "affirm", "af-chf"]
ALL33 = OLD18 + NEW15
CATEGORY = {**{t: "AF" for t in AF7},
            **{t: "HF" for t in ("comet", "paradigm-hf-seq", "transform-hf", "elite-ii", "emperor-preserved-v2")},
            **{t: "DM" for t in ("empa-reg", "carolina", "leader", "sustain6", "rewind", "declare", "canvas", "tecos", "carmelina")},
            **{t: "HTN" for t in ("life", "allhat", "value", "ascot", "insight")},
            **{t: "ACS" for t in ("plato", "valiant")},
            **{t: "Other" for t in ("ontarget", "precision", "amplify", "lodestar", "prove-it")}}


def clusters():
    J = json.load(open(REPO + "docs/v17/trial_selection.json"))
    return {t: c for c, ts in J["comparator_clusters"]["clusters"].items() for t in ts}


# ------------------------------------------------------------------ exact sign-flip (own code)
@lru_cache(None)
def _signs(k):
    return np.array(list(itertools.product((-1.0, 1.0), repeat=k)))


def _half_sums(a):
    return _signs(len(a)) @ a if len(a) else np.zeros(1)


def flip1(d, tol=1e-9):
    """one-sided exact sign-flip: P(sum_i s_i|d_i| >= sum d) under uniform random signs (H1: mean d > 0).
    Exact for any k <= ~40 by splitting into two halves (each enumerated) and counting pairs with sorting."""
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    k = len(d)
    if k == 0:
        return np.nan
    a = np.abs(d)
    obs = d.sum() - tol * max(1.0, a.sum())
    h = k // 2
    L = _half_sums(a[:h])
    R = np.sort(_half_sums(a[h:]))
    # count pairs with L + R >= obs
    cnt = (len(R) - np.searchsorted(R, obs - L, side="left")).sum()
    return float(cnt) / 2.0 ** k


def flip2(d):
    return min(1.0, 2 * min(flip1(d), flip1(-np.asarray(d, float))))


def flip1_mc(d, n=200000, seed=11):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    s = np.random.default_rng(seed).choice([-1.0, 1.0], size=(n, len(d)))
    return float(((s @ np.abs(d)) >= d.sum() - 1e-9).mean())


def cluster_p(d: pd.Series, CL, key, two=False):
    g = d.groupby([CL[key[t]] for t in d.index]).mean()
    return (flip2 if two else flip1)(g.values), len(g)


def loo(d: pd.Series, two=False):
    f = flip2 if two else flip1
    return max(f(d.drop(t).values) for t in d.index)


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


# ------------------------------------------------------------------ per-trial metrics (own code)
def metrics(g: pd.DataFrame) -> pd.DataFrame:
    g = g.set_index("trial")
    s = g[V58].abs()
    nc = g[NC54].abs()
    z = (g.loghr - g.rb) / np.sqrt(g.se ** 2 + g.rs ** 2)
    out = pd.DataFrame({
        "lt01": 100 * (s < 0.1).sum(1) / s.notna().sum(1),
        "nc_lt01": 100 * (nc < 0.1).sum(1) / nc.notna().sum(1),
        "mean_smd": s.mean(1),
        "cstat": g.cstat,
        "absd": (g.loghr - g.rb).abs(),
        "z2": z ** 2,
        "cons": 100.0 * (z.abs() < 1.96),
        "loghr": g.loghr, "se": g.se, "rb": g.rb, "rs": g.rs,
        "n_pairs": g.n_pairs, "n_t": g.n_t, "n_c": g.n_c,
    })
    if "x_pct_lt10" in g:
        out["x_lt01"] = g.x_pct_lt10
    if "key" in g:
        out["key"] = g.key
    return out


HIGHER = {"lt01", "nc_lt01", "x_lt01", "cons"}


def bshuffle(le, lb, se_e, se_b, pool_rb, pool_rs, obs_rb, obs_rs, metric="absd", mode="pool_norep", nd=200000, seed=7):
    """benchmark-shuffle p = P(null <= obs) for mean(|le-q| - |lb-q|) (or z2 analogue).
    mode: 'perm' = permute the analysed trials' own benchmarks; 'pool_norep' = draw k joint (rb, rs) pairs without
    replacement from the pool; 'pool_rep' = with replacement; 'pool_indep' = rb and rs drawn independently (no rep)."""
    rng = np.random.default_rng(seed)
    k = len(le)

    def st(q, v):
        if metric == "absd":
            return (np.abs(le - q) - np.abs(lb - q)).mean(-1)
        return ((le - q) ** 2 / (se_e ** 2 + v ** 2) - (lb - q) ** 2 / (se_b ** 2 + v ** 2)).mean(-1)
    obs = st(obs_rb, obs_rs)
    P = len(pool_rb)
    if mode == "perm":
        ix = np.argsort(rng.random((nd, k)), axis=1)
        q, v = obs_rb[ix], obs_rs[ix]
    elif mode == "pool_norep":
        ix = np.argsort(rng.random((nd, P)), axis=1)[:, :k]
        q, v = pool_rb[ix], pool_rs[ix]
    elif mode == "pool_rep":
        ix = rng.integers(0, P, (nd, k))
        q, v = pool_rb[ix], pool_rs[ix]
    else:
        ix = np.argsort(rng.random((nd, P)), axis=1)[:, :k]
        ix2 = np.argsort(rng.random((nd, P)), axis=1)[:, :k]
        q, v = pool_rb[ix], pool_rs[ix2]
    null = st(q, v)
    return float(obs), float(null.mean()), float((null <= obs + 1e-12).mean())
