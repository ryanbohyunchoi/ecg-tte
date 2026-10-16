"""Cell runner and across-trial statistics for the AoU grid, with the held-out item list as a parameter.

These are copies of the Yale functions with the module-level 58-item list (make_acc_figure.VARS) replaced by an argument.
The Yale modules that hold them (v20/sens_primary32, v17/v17_confirm, v21/paper2_grid) cannot be imported in AoU: at import
they require the 38 Yale trial caches. tests/test_aou_stats.py checks every copy against the Yale original (exact equality
on synthetic data) wherever the Yale modules import.

  run_cell        = v16_engine.run_cell (cstat=None), VARS argument; primitives imported unchanged from v13_common
                    (ps_logit, match, weights, cox) and v16_engine (smd_components, _ess)
  signflip_1s     = v17_confirm.signflip_1s
  p1s, p2s, relred_ci, bshuf, agree_metrics, paired_balance, contrast_row = sens_primary32 (NB 4,000, seed 20261001)
  per_trial       = sens_primary32.per_trial with VN as an argument
  bshuf2, bal_light = paper2_grid
  bh_fdr          = v16_engine.bh_fdr (imported)
  rubin           Rubin's rules for the 5-draw PS-Clinical imputation (pipeline.md section 4)
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from v13_common import cox, match, ps_logit, weights  # noqa: E402
from v16_engine import _ess, bh_fdr, smd_components  # noqa: E402,F401

import aou_trial as AT

NB, SEED, NDRAW = 4000, 20261001, 20000


# ---------------------------------------------------------------- one cell
def run_cell(T, X, VARS, t=None, rows=None, estimator=("match", 0.2, 1), ps_model=("l2", 1.0), heldout=None, seed=0) -> dict:
    t0 = time.time()
    rows = np.arange(len(T.t)) if rows is None else np.asarray(rows)
    t = T.t[rows] if t is None else np.asarray(t).astype(int)
    yt, ye, ok = T.y_t[rows], T.y_e[rows], T.y_ok[rows]
    H = T.H if heldout is None else heldout
    Hv = H.to_numpy(float)[rows]
    N = len(rows)
    r = dict(n=N, n_t=int(t.sum()), n_c=int((1 - t).sum()), n_pairs=np.nan)
    kind = "crude" if X is None else estimator[0]
    if X is None:
        s_idx, s_w = np.arange(N), np.ones(N)
        m = ok
        b, se = cox(yt[m], ye[m], t[m])
    else:
        mk, C = ps_model[0], ps_model[1] if len(ps_model) > 1 and ps_model[1] is not None else 1.0
        lg = ps_logit(np.asarray(X, float), t, model=mk, C=C, seed=seed)
        if kind == "match":
            cal, ratio = estimator[1], estimator[2]
            s_idx, cl, s_w = match(lg, t, cal=cal, ratio=ratio)
            r["n_pairs"] = int(len(np.unique(cl)))
            m = ok[s_idx]
            b, se = cox(yt[s_idx][m], ye[s_idx][m], t[s_idx][m], w=None if ratio == 1 else s_w[m], cluster=cl[m])
        elif kind in ("iptw", "overlap"):
            w = weights(lg, t, kind)
            b, se = cox(yt[ok], ye[ok], t[ok], w=w[ok])
            s_idx = np.where(w > 0)[0]
            s_w = w[s_idx]
        else:
            raise KeyError(estimator)
    r.update(loghr=b, se=se)
    if getattr(T, "y_t2", None) is not None:  # AoU addition: censoring sensitivity on the same matched / weighted sample
        yt2, ye2 = T.y_t2[rows], T.y_e2[rows]
        if X is None:
            b2, se2 = cox(yt2[m], ye2[m], t[m])
        elif kind == "match":
            b2, se2 = cox(yt2[s_idx][m], ye2[s_idx][m], t[s_idx][m], w=None if estimator[2] == 1 else s_w[m], cluster=cl[m])
        else:
            b2, se2 = cox(yt2[ok], ye2[ok], t[ok], w=w[ok])
        r.update(loghr_admin=b2, se_admin=se2)
    s_t = t[s_idx]
    r["ess_t"], r["ess_c"] = _ess(s_w[s_t == 1]), _ess(s_w[s_t == 0])
    comp = smd_components(Hv, t, s_idx, s_w, s_t)
    cs = pd.Series(comp, index=H.columns)
    vc = AT.var_components(H, VARS)
    smd = {}
    for c, _, _ in VARS:
        g = cs[vc[c]].dropna()
        smd[c] = float(g.mean()) if len(g) else np.nan
    sv = pd.Series(smd)
    r["mean_smd"], r["n_vars"] = float(sv.mean()), int(sv.notna().sum())
    r.update({f"smd:{c}": v for c, v in smd.items()})
    r["secs"] = round(time.time() - t0, 2)
    return r


def rubin(b, se):
    """Pooled log HR and SE over imputation draws (Rubin's rules); NaN draws dropped, NaN if < 2 remain."""
    b, se = np.asarray(b, float), np.asarray(se, float)
    ok = np.isfinite(b) & np.isfinite(se)
    if ok.sum() < 2:
        return (float(b[ok][0]), float(se[ok][0])) if ok.sum() == 1 else (np.nan, np.nan)
    b, se = b[ok], se[ok]
    m = len(b)
    W, B = np.mean(se ** 2), np.var(b, ddof=1)
    return float(b.mean()), float(np.sqrt(W + (1 + 1 / m) * B))


# ---------------------------------------------------------------- tests across trials
def signflip_1s(d):
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    k = len(d)
    if k == 0:
        return np.nan
    a = np.abs(d)
    S = d.sum()
    eps = 1e-10 * max(a.sum(), 1e-300)

    def sums(x):
        s = np.zeros(1)
        for v in x:
            s = np.concatenate([s + v, s - v])
        return s
    L, Rr = sums(a[: k // 2]), np.sort(sums(a[k // 2:]))
    cnt = (len(Rr) - np.searchsorted(Rr, S - eps - L, side="left")).sum()
    return float(cnt) / 2.0 ** k


def p1s(d):
    d = np.asarray(d, float)
    return signflip_1s(d[np.isfinite(d)])


def p2s(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    return min(1.0, 2 * min(signflip_1s(d), signflip_1s(-d)))


def relred_ci(B, Ev):
    B, Ev = np.asarray(B, float), np.asarray(Ev, float)
    ok = np.isfinite(B) & np.isfinite(Ev)
    B, Ev = B[ok], Ev[ok]
    est = 100 * (1 - Ev.mean() / B.mean())
    rng = np.random.default_rng(SEED)
    I = rng.integers(0, len(B), size=(NB, len(B)))  # noqa: E741
    bs = 100 * (1 - Ev[I].mean(1) / B[I].mean(1))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return est, lo, hi, int(ok.sum())


def bshuf(la, lb, rb, ndraw=NDRAW):
    st = lambda q: np.mean(np.abs(la - q) - np.abs(lb - q), axis=-1)  # noqa: E731
    obs = float(st(rb))
    rng = np.random.default_rng(0)
    IX = np.array([rng.permutation(len(rb)) for _ in range(ndraw)])
    return float((st(rb[IX]) <= obs + 1e-12).mean())


def bshuf2(la, lb, rb, ndraw=NDRAW):
    st = lambda q: np.mean(np.abs(la - q) - np.abs(lb - q), axis=-1)  # noqa: E731
    obs = float(st(rb))
    rng = np.random.default_rng(0)
    IX = np.array([rng.permutation(len(rb)) for _ in range(ndraw)])
    null = st(rb[IX])
    return float(min(1.0, 2 * min((null <= obs + 1e-12).mean(), (null >= obs - 1e-12).mean())))


def per_trial(g, VN):
    S = g[[f"smd:{c}" for c in VN]].abs().to_numpy(float)
    for j, ex in enumerate(g.ex58.fillna("").astype(str)):
        for c in filter(None, ex.split(";")):
            if c in VN:
                S[j, VN.index(c)] = np.nan
    sm = pd.DataFrame(S, columns=VN, index=g.trial.to_numpy())
    z = ((g.loghr - g.rb) / np.sqrt(g.se ** 2 + g.rs ** 2)).to_numpy()
    d = (g.loghr - g.rb).abs().to_numpy()
    return pd.DataFrame({"lt01": (100 * (sm < 0.1).sum(1) / sm.notna().sum(1)).to_numpy(), "m58": sm.mean(1).to_numpy(),
                         "absd": d, "cons": 100.0 * (np.abs(z) < 1.96), "ea": 100.0 * (d <= 1.96 * g.rs.to_numpy()),
                         "loghr": g.loghr.to_numpy(), "se": g.se.to_numpy(), "rb": g.rb.to_numpy(), "rs": g.rs.to_numpy()},
                        index=g.trial.to_numpy()), sm


def agree_metrics(F):
    ok = np.isfinite(F.loghr) & np.isfinite(F.se)
    G = F[ok]
    r = float(np.corrcoef(G.loghr, G.rb)[0, 1]) if len(G) > 2 else np.nan
    return dict(k=int(ok.sum()), absd=G.absd.mean(), r=r, ea=G.ea.mean(), cons=G.cons.mean())


def paired_balance(Fa, Fb, SMa, SMb, trials):
    a, b = SMa.loc[trials].copy(), SMb.loc[trials].copy()
    msk = a.isna() | b.isna()
    a[msk], b[msk] = np.nan, np.nan
    Fa, Fb = Fa.copy(), Fb.copy()
    for F_, M_ in ((Fa, a), (Fb, b)):
        F_.loc[trials, "lt01"] = (100 * (M_ < 0.1).sum(1) / M_.notna().sum(1)).to_numpy()
        F_.loc[trials, "m58"] = M_.mean(1).to_numpy()
    return Fa, Fb


def contrast_row(Fa, Fb, trials, side, CL, SMa=None, SMb=None):
    """= sens_primary32.contrast_row; CL maps trial name -> comparator cluster (Yale: CL[KEY[name]])."""
    out = {}
    pf = p1s if side == "one" else p2s
    if SMa is not None:
        Fa, Fb = paired_balance(Fa, Fb, SMa, SMb, trials)
    for m, sgn in (("lt01", 1), ("m58", -1), ("absd", -1), ("cons", 1)):
        a, b = Fa.loc[trials, m], Fb.loc[trials, m]
        d = sgn * (a - b)
        ok = d.notna()
        out[f"{m}_a"], out[f"{m}_b"], out[f"{m}_diff"] = a.mean(), b.mean(), (a - b).mean()
        out[f"{m}_better"] = f"{int((d > 0).sum())}/{int(ok.sum())}"
        out[f"{m}_p"] = pf(d.to_numpy())
        cl = pd.Series(d.to_numpy(), index=[CL[t] for t in trials]).dropna().groupby(level=0).mean()
        out[f"{m}_cluster_p"], out[f"{m}_n_clusters"] = pf(cl.to_numpy()), len(cl)
        out[f"{m}_loo_max_p"] = max(pf(d.drop(t).to_numpy()) for t in trials)
    e, lo, hi, k = relred_ci(Fb.loc[trials, "m58"], Fa.loc[trials, "m58"])
    out.update(relred=e, relred_lo=lo, relred_hi=hi, relred_k=k)
    la, lb, rb = Fa.loc[trials, "loghr"].to_numpy(), Fb.loc[trials, "loghr"].to_numpy(), Fb.loc[trials, "rb"].to_numpy()
    ok = np.isfinite(la) & np.isfinite(lb)
    out["bshuf_p"] = bshuf(la[ok], lb[ok], rb[ok]) if side == "one" else np.nan  # two-sided: bshuf2 in the grid (paper2_grid)
    return out
