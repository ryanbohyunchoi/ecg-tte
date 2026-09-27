#!/usr/bin/env python
"""v1.6 sweep S7: structured removal of diagnoses from the sparse PS (docs/V16_SWEEP_PLAN.md; exploratory).

Sparse = T.demo (age, sex, index year) + T.dxc. The 9 SHARED flags (all 18 trials): ischemic_heart_disease_or_mi,
atrial_fibrillation, hypertension, diabetes, ckd, stroke_history, copd_or_asthma, peripheral_arterial_disease,
valve_disease; 10 trials have trial-specific extras (heart_failure, tia, prior_bleed, ...).

Cells (base designs; each run as base, base+ECG (32 BCL PCs), base+shufECG (T.shuffle_perm rows), base+noise32):
  sparse          k = 0 (full sparse; = engine 'sparse')
  loo_<flag>      A. sparse minus one shared flag (9 cells)
  cum_k<k>        B. cumulative removal of the k most treatment-associated shared flags (order = mean over trials of
                     the unmatched full-cohort |SMD| between arms; computed once, profile.csv), k = 1..9 (k = 9:
                     demo + trial extras)
  noextras        sparse minus trial-specific extras (demo + 9 shared)
  demo            demo only (all shared flags and extras removed)
  rand<r>_k<k>    B control: cumulative removal in random order r in {0,1,2} (rng 7070 + r), k = 1..8
  common10        C. age, sex, index year + the 7 most prevalent shared flags (mean prevalence across trials)
Unmatched once per trial/half. Halves: full, A, B (rng 16060 + trial index, stratified by treatment).
Estimator: engine default (1:1 caliper-0.2 matching, L2 C=1 PS); balance on the engine 58-variable panel (T.H).
Extra per arm: |SMD| of every sparse flag in the matched sample (smdflag:<flag>), from the matched set captured
from run_cell (v16_engine.match wrapped; identical call).

Usage: s7_dxremoval.py run [--trials a,b] [--workers 32]
       s7_dxremoval.py summarize
Aggregates only.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v16_engine as E  # noqa: E402
from audit_v16 import CLUSTER, sflip  # noqa: E402

SWEEP = "s7-dxremoval"
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s7-dxremoval")
DOCS = HERE.parent.parent / "docs" / "v16"
SHARED = ["ischemic_heart_disease_or_mi", "atrial_fibrillation", "hypertension", "diabetes", "ckd", "stroke_history",
          "copd_or_asthma", "peripheral_arterial_disease", "valve_disease"]
SHORT = {"ischemic_heart_disease_or_mi": "IHD/MI", "atrial_fibrillation": "AF", "hypertension": "HTN", "diabetes": "DM",
         "ckd": "CKD", "stroke_history": "stroke", "copd_or_asthma": "COPD/asthma", "peripheral_arterial_disease": "PAD",
         "valve_disease": "valve"}
HALVES = ["full", "A", "B"]
ROLES = ["base", "ECG", "shufECG", "noise"]
METRICS = ["absd", "z2", "mean_smd", "cstat"]
NRAND = 3
_CACHE = {}
_LAST = {}


# ---------------------------------------------------------------- capture the matched set of run_cell
_orig_match = E.match


def _match_capture(*a, **k):
    r = _orig_match(*a, **k)
    _LAST["m"] = r
    return r


E.match = _match_capture

# exact sign-flip identical to v13_summarize.sign_flip, with the sign matrix cached (speed only)
_SGN = {}


def _sign_flip_fast(d):
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    obs = d.mean()
    k = len(d)
    if k > 20:
        return E.__dict__["_orig_sign_flip"](d)
    if k not in _SGN:
        _SGN[k] = np.array(list(itertools.product([-1, 1], repeat=k)), dtype=np.float64)
    null = (_SGN[k] @ np.abs(d)) / k
    return float(obs), float(np.mean(np.abs(null) >= abs(obs) - 1e-12))


E._orig_sign_flip = E.sign_flip
E.sign_flip = _sign_flip_fast


def trial(n):
    if n not in _CACHE:
        _CACHE.clear()
        _CACHE[n] = E.load_trial(n)
    return _CACHE[n]


def halves(T, n):
    rng = np.random.default_rng(16060 + E.TRIALS.index(n))
    a = []
    for g in (0, 1):
        idx = np.where(T.t == g)[0]
        perm = rng.permutation(idx)
        a.append(perm[: len(idx) // 2])
    A_ = np.sort(np.concatenate(a))
    B_ = np.setdiff1d(np.arange(len(T.t)), A_)
    return {"full": None, "A": A_, "B": B_}


# ---------------------------------------------------------------- profile (order, prevalence, ECG predictability)
def _smd_unw(x, t):
    a, b = x[t == 1], x[t == 0]
    sd = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float(abs(a.mean() - b.mean()) / sd) if sd > 0 else np.nan


def profile_one(n):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    T = trial(n)
    rows = []
    for f in T.dxc:
        x = T.cov[f].to_numpy(float)
        auc = np.nan
        y = (x > 0).astype(int)
        if 20 <= y.sum() <= len(y) - 20:
            p = np.zeros(len(y))
            for tr, te in StratifiedKFold(5, shuffle=True, random_state=0).split(T.ecg_pc, y):
                p[te] = LogisticRegression(C=1.0, max_iter=2000).fit(T.ecg_pc[tr], y[tr]).decision_function(T.ecg_pc[te])
            auc = float(roc_auc_score(y, p))
        rows.append(dict(trial=n, flag=f, shared=f in SHARED, prevalence=float(np.mean(x > 0)), smd_unmatched=_smd_unw(x, T.t),
                         auc_from_ecg=auc))
    return rows


def build_profile(trials, workers):
    from multiprocessing import Pool
    with Pool(min(workers, 18)) as p:
        res = p.map(profile_one, trials, chunksize=1)
    P = pd.DataFrame([r for x in res for r in x])
    P.to_csv(OUT / "profile.csv", index=False)
    S = P[P.shared].groupby("flag").agg(mean_abs_smd=("smd_unmatched", "mean"), mean_prev=("prevalence", "mean"),
                                        mean_auc_ecg=("auc_from_ecg", "mean"), n_trials=("trial", "size")).reindex(SHARED)
    order = list(S.sort_values("mean_abs_smd", ascending=False).index)
    prev7 = list(S.sort_values("mean_prev", ascending=False).index[:7])
    rand = [list(np.random.default_rng(7070 + r).permutation(SHARED)) for r in range(NRAND)]
    spec = dict(order=order, common7=prev7, rand=rand)
    (OUT / "spec.json").write_text(json.dumps(spec, indent=1))
    S.reset_index().to_csv(OUT / "profile_shared.csv", index=False)
    return spec


def cells(spec):
    """cell id -> dict(family, k_removed, removed (list of shared flags), extras (bool kept), order)."""
    C = {"sparse": dict(family="sparse", k_removed=0, removed=[], extras=True, order="-")}
    for f in SHARED:
        C[f"loo_{f}"] = dict(family="loo", k_removed=1, removed=[f], extras=True, order="-")
    for k in range(1, len(SHARED) + 1):
        C[f"cum_k{k}"] = dict(family="cum", k_removed=k, removed=spec["order"][:k], extras=True, order="assoc")
    C["noextras"] = dict(family="noextras", k_removed=0, removed=[], extras=False, order="-")
    C["demo"] = dict(family="demo", k_removed=len(SHARED), removed=list(SHARED), extras=False, order="-")
    for r, o in enumerate(spec["rand"]):
        for k in range(1, len(SHARED)):
            C[f"rand{r}_k{k}"] = dict(family="rand", k_removed=k, removed=o[:k], extras=True, order=f"rand{r}")
    C["common10"] = dict(family="common10", k_removed=len(SHARED) - 7, removed=[f for f in SHARED if f not in spec["common7"]],
                         extras=False, order="-")
    return C


def design_cols(T, c):
    keep = [f for f in T.dxc if (f in SHARED and f not in c["removed"]) or (f not in SHARED and c["extras"])]
    return T.demo + keep


# ---------------------------------------------------------------- run
def _row(r, **kw):
    d = dict(sweep=SWEEP)
    d.update(kw)
    d.update(r)
    return d


def _flag_smd(T, rows, t):
    """|SMD| of every sparse flag in the matched sample of the last run_cell call (NaN-aware, pre-match pooled SD)."""
    V = T.cov[T.dxc].to_numpy(float)
    V = V if rows is None else V[rows]
    if "m" in _LAST and _LAST["m"] is not None:
        s_idx, _, s_w = _LAST["m"]
    else:
        s_idx, s_w = np.arange(len(t)), np.ones(len(t))
    d = E.smd_components(V, t, s_idx, s_w, t[s_idx])
    return {f"smdflag:{f}": float(v) for f, v in zip(T.dxc, d)}


def job(args):
    n, cid, c = args
    T = trial(n)
    hv = halves(T, n)
    cols = design_cols(T, c)
    meta = dict(family=c["family"], k_removed=c["k_removed"], removed=";".join(c["removed"]), extras_kept=c["extras"],
                order=c["order"], p_design=len(cols))
    out = []
    for half, rows in hv.items():
        sel = (lambda M: M) if rows is None else (lambda M: M[rows])
        t = T.t if rows is None else T.t[rows]
        if cid == "sparse":
            _LAST["m"] = None
            r = E.run_cell(T, None, rows=rows)
            r.update(_flag_smd(T, rows, t))
            out.append(_row(r, cell="unmatched", family="unmatched", k_removed=np.nan, removed="", extras_kept=np.nan,
                            order="-", p_design=0, trial=n, half=half, arm_role="unmatched", arm_label="unmatched", rb=T.rb, rs=T.rs))
        Xb = sel(T.cov[cols].to_numpy(float))
        X = {"base": Xb, "ECG": np.hstack([Xb, sel(T.ecg_pc)]), "shufECG": np.hstack([Xb, sel(T.ecg_pc[T.shuffle_perm])]),
             "noise": np.hstack([Xb, sel(T.noise32)])}
        for role in ROLES:
            _LAST.pop("m", None)
            r = E.run_cell(T, X[role], rows=rows)
            r.update(_flag_smd(T, rows, t))
            out.append(_row(r, cell=cid, **meta, trial=n, half=half, arm_role=role,
                            arm_label=f"{cid}{'' if role == 'base' else '+' + role}", rb=T.rb, rs=T.rs))
    return out


def run(trials, workers, outf="results.csv"):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    spec = build_profile(E.TRIALS, workers)
    print("order:", spec["order"], "\ncommon7:", spec["common7"], flush=True)
    C = cells(spec)
    size = {n: i for i, n in enumerate(["value", "allhat", "ascot", "aristotle", "east-afnet4", "transform-hf", "ontarget", "cabana-v2"])}
    jobs = sorted([(n, cid, c) for n in trials for cid, c in C.items()], key=lambda j: size.get(j[0], 99))
    t0 = time.time()
    res = []
    with Pool(min(workers, 32)) as pool:
        for i, r in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            res.extend(r)
            if (i + 1) % 50 == 0 or i + 1 == len(jobs):
                print(f"{i + 1}/{len(jobs)} jobs, {time.time() - t0:.0f}s", flush=True)
    df = pd.DataFrame(res)
    df.to_csv(OUT / outf, index=False)
    print("wrote", OUT / outf, df.shape)


# ---------------------------------------------------------------- summaries
def fmt_p(p):
    return "–" if pd.isna(p) else (f"{p:.3f}" if p >= 0.001 else "<.001")


def per_trial(g, m, a="ECG", b="base"):
    xa = g[g.arm_role == a].drop_duplicates("trial").set_index("trial")
    xb = g[g.arm_role == b].drop_duplicates("trial").set_index("trial")
    tt = xa.index.intersection(xb.index)
    xa, xb = xa.loc[tt], xb.loc[tt]
    f = {"absd": lambda x: (x.loghr - x.rb).abs(), "z2": lambda x: (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2)}.get(m, lambda x: x[m])
    return (f(xa) - f(xb)).dropna()


def bench_shuffle(g, nperm=5000, seed=0):
    """ECG - base |dlogHR| and z2 with the true vs shuffled RCT benchmarks (rb, rs permuted jointly across trials)."""
    E_ = g[g.arm_role == "ECG"].drop_duplicates("trial").set_index("trial")
    B_ = g[g.arm_role == "base"].drop_duplicates("trial").set_index("trial")
    tr = E_.index.intersection(B_.index)
    E_, B_ = E_.loc[tr], B_.loc[tr]
    le, lb, se_e, se_b, rb, rs = (E_.loghr.to_numpy(), B_.loghr.to_numpy(), E_.se.to_numpy(), B_.se.to_numpy(), B_.rb.to_numpy(), B_.rs.to_numpy())
    ok = np.isfinite(le) & np.isfinite(lb)
    le, lb, se_e, se_b, rb, rs = le[ok], lb[ok], se_e[ok], se_b[ok], rb[ok], rs[ok]
    fa = lambda r_: np.mean(np.abs(le - r_) - np.abs(lb - r_))
    fz = lambda r_, s_: np.mean((le - r_) ** 2 / (se_e ** 2 + s_ ** 2) - (lb - r_) ** 2 / (se_b ** 2 + s_ ** 2))
    rng = np.random.default_rng(seed)
    na, nz = np.empty(nperm), np.empty(nperm)
    for i in range(nperm):
        pi = rng.permutation(len(rb))
        na[i], nz[i] = fa(rb[pi]), fz(rb[pi], rs[pi])
    oa, oz = fa(rb), fz(rb, rs)
    return dict(bs_absd_obs=oa, bs_absd_null_mean=na.mean(), bs_absd_null_median=float(np.median(na)), bs_absd_specific=oa - na.mean(),
                bs_absd_p=float(np.mean(na <= oa)), bs_z2_obs=oz, bs_z2_null_mean=nz.mean(), bs_z2_null_median=float(np.median(nz)),
                bs_z2_specific=oz - nz.mean(), bs_z2_p=float(np.mean(nz <= oz)),
                shrink_abs_loghr_base=float(np.mean(np.abs(lb))), shrink_abs_loghr_ECG=float(np.mean(np.abs(le))))


def cluster_loo(g, m):
    d = per_trial(g, m)
    if len(d) < 3:
        return {}
    cl = d.groupby(d.index.map(CLUSTER)).mean()
    lo = [sflip(d.drop(t).to_numpy()) for t in d.index]
    return {f"cl_d_{m}": float(cl.mean()), f"cl_k_{m}": f"{int((cl < 0).sum())}/{len(cl)}", f"cl_p_{m}": sflip(cl.to_numpy()),
            f"loo_pmax_{m}": float(max(lo)), f"loo_worst_{m}": d.index[int(np.argmax(lo))]}


def summarize(resf="results.csv"):
    os.umask(0o077)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    df = pd.read_csv(OUT / resf, low_memory=False)
    spec = json.loads((OUT / "spec.json").read_text())
    C = cells(spec)
    cid_order = list(C)
    X = df[df.arm_role != "unmatched"].rename(columns={"arm_role": "arm"})
    key = ["cell", "half"]
    S = {b: E.summarize_pairs(X, key, "ECG", b) for b in ("base", "shufECG", "noise")}
    Pl = {b: E.summarize_pairs(X, key, b, "base") for b in ("shufECG", "noise")}
    M = S["base"].copy()
    for b in ("shufECG", "noise"):
        s = S[b][key + [f"{x}_{m}" for m in METRICS for x in ("d", "p", "k")]].rename(
            columns={f"{x}_{m}": f"{x}_{m}_vs_{b}" for m in METRICS for x in ("d", "p", "k")})
        M = M.merge(s, on=key)
    for m in METRICS:
        M[f"q_{m}"] = np.nan
        f = M.half == "full"
        M.loc[f, f"q_{m}"] = E.bh_fdr(M.loc[f, f"p_{m}"])
        M[f"spec_{m}"] = (M[f"p_{m}"] < 0.05) & (M[f"d_{m}"] < 0) & (M[f"d_{m}_vs_shufECG"] < 0) & (M[f"d_{m}_vs_noise"] < 0)
    # benchmark shuffle, cluster, LOO (full cohort)
    extra = []
    for i, cid in enumerate(cid_order):
        g = df[(df.cell == cid) & (df.half == "full")]
        r = dict(cell=cid, half="full")
        r.update(bench_shuffle(g, seed=7000 + i))
        for m in METRICS:
            r.update(cluster_loo(g, m))
        extra.append(r)
    EX = pd.DataFrame(extra)
    # benchmark shuffle in halves (share only)
    for h in ("A", "B"):
        for i, cid in enumerate(cid_order):
            g = df[(df.cell == cid) & (df.half == h)]
            r = dict(cell=cid, half=h)
            r.update(bench_shuffle(g, nperm=2000, seed=8000 + i))
            extra.append(r)
    EXh = pd.DataFrame(extra)
    M = M.merge(EXh, on=key, how="left")
    meta = pd.DataFrame([dict(cell=k, **{kk: (";".join(v) if isinstance(v, list) else v) for kk, v in c.items()}) for k, c in C.items()])
    M = meta.merge(M, on="cell")
    M["_o"] = M.cell.map({c: i for i, c in enumerate(cid_order)})
    M["_h"] = M.half.map({h: i for i, h in enumerate(HALVES)})
    M = M.sort_values(["_o", "_h"]).drop(columns=["_o", "_h"])
    M["bh_q_bs_absd"] = np.nan
    M["bh_q_bs_z2"] = np.nan
    f = M.half == "full"
    M.loc[f, "bh_q_bs_absd"] = E.bh_fdr(M.loc[f, "bs_absd_p"])
    M.loc[f, "bh_q_bs_z2"] = E.bh_fdr(M.loc[f, "bs_z2_p"])
    M.to_csv(OUT / "summary_ecg.csv", index=False)
    pd.concat([Pl["shufECG"], Pl["noise"]], ignore_index=True).to_csv(OUT / "summary_placebo_vs_base.csv", index=False)
    # arm means
    dd = df.copy()
    dd["absd"] = (dd.loghr - dd.rb).abs()
    dd["z2"] = (dd.loghr - dd.rb) ** 2 / (dd.se ** 2 + dd.rs ** 2)
    dd["cons"] = 100 * (np.sqrt(dd.z2) < 1.96)
    AM = dd.groupby(["cell", "half", "arm_role"])[["absd", "z2", "cons", "mean_smd", "cstat", "smd_prog", "n_pairs"]].mean().reset_index()
    AM.to_csv(OUT / "summary_arms.csv", index=False)
    sub = substitution(df, spec)
    sub.to_csv(OUT / "summary_substitution.csv", index=False)
    figs(M, AM, spec, plt, df)
    tables(M, AM, spec, sub, Pl, df)


def substitution(df, spec):
    """Per shared flag f (full cohort): cost of removing f from sparse (base_loo - base_sparse), ECG recovery
    (ECG_loo - base_loo) on the metrics and on |SMD| of f itself; placebo recovery; and the same for the cumulative path
    on the mean |SMD| of all removed flags."""
    full = df[df.half == "full"]
    rows = []
    sp = full[full.cell == "sparse"]
    for f in SHARED:
        g = full[full.cell == f"loo_{f}"]
        r = dict(flag=f)
        col = f"smdflag:{f}"
        def pv(a, b, m, ga=g, gb=g):
            xa = ga[ga.arm_role == a].set_index("trial")
            xb = gb[gb.arm_role == b].set_index("trial")
            tt = xa.index.intersection(xb.index)
            fn = {"absd": lambda x: (x.loghr - x.rb).abs(), "z2": lambda x: (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2)}.get(m, lambda x: x[m])
            d = (fn(xa.loc[tt]) - fn(xb.loc[tt])).dropna()
            return float(d.mean()), sflip(d.to_numpy()), f"{int((d < 0).sum())}/{len(d)}"
        for m in ["absd", "z2", "mean_smd", "cstat", col]:
            nm = "flagsmd" if m == col else m
            r[f"cost_{nm}"], r[f"cost_p_{nm}"], _ = pv("base", "base", m, g, sp)
            r[f"ecg_{nm}"], r[f"ecg_p_{nm}"], r[f"ecg_k_{nm}"] = pv("ECG", "base", m)
            r[f"shuf_{nm}"], r[f"shuf_p_{nm}"], _ = pv("shufECG", "base", m)
            r[f"noise_{nm}"], r[f"noise_p_{nm}"], _ = pv("noise", "base", m)
            r[f"ecgvsshuf_p_{nm}"] = pv("ECG", "shufECG", m)[1]
        r["recovered_frac_flagsmd"] = -r["ecg_flagsmd"] / r["cost_flagsmd"] if r["cost_flagsmd"] > 0 else np.nan
        r["flagsmd_base_sparse"] = sp[sp.arm_role == "base"][col].mean()
        r["flagsmd_base_loo"] = g[g.arm_role == "base"][col].mean()
        r["flagsmd_ECG_loo"] = g[g.arm_role == "ECG"][col].mean()
        rows.append(r)
    return pd.DataFrame(rows)


def _curve_data(M, spec):
    full = M[M.half == "full"].set_index("cell")
    xs = list(range(0, len(SHARED) + 1))
    path = ["sparse"] + [f"cum_k{k}" for k in range(1, len(SHARED) + 1)]
    rpaths = [["sparse"] + [f"rand{r}_k{k}" for k in range(1, len(SHARED))] + [f"cum_k{len(SHARED)}"] for r in range(NRAND)]
    return full, xs, path, rpaths


def figs(M, AM, spec, plt, df):
    full, xs, path, rpaths = _curve_data(M, spec)
    ink, grey = "#0b0b0b", "#8a8984"
    c_obs, c_null, c_spec, c_rand = "#eb6834", "#2a78d6", "#1baf7a", "#b9b8b2"
    mets = [("absd", "ECG − base  mean |Δlog HR|"), ("z2", "ECG − base  mean z²"), ("mean_smd", "ECG − base  held-out mean |SMD|"),
            ("cstat", "ECG − base  held-out C-statistic")]
    fig, ax = plt.subplots(4, 2, figsize=(14, 16), gridspec_kw=dict(width_ratios=[1.6, 1]))
    xl = ["0\n(sparse)"] + [f"{k}\n−{SHORT[spec['order'][k - 1]]}" for k in xs[1:]]
    for i, (m, yl) in enumerate(mets):
        a = ax[i, 0]
        for r, rp in enumerate(rpaths):
            a.plot(xs, [full.loc[c, f"d_{m}"] for c in rp], color=c_rand, lw=1, zorder=1, label="random removal orders (3)" if r == 0 else None)
        y = np.array([full.loc[c, f"d_{m}"] for c in path])
        a.plot(xs, y, color=c_obs, lw=2.2, zorder=3, label="ECG − base (true RCT)")
        if m in ("absd", "z2"):
            yn = np.array([full.loc[c, f"bs_{m}_null_mean"] for c in path])
            ys = y - yn
            a.plot(xs, yn, color=c_null, lw=1.6, ls="--", zorder=2, label="ECG − base, shuffled-RCT mean")
            a.bar(xs, ys, width=0.35, color=c_spec, alpha=0.55, zorder=2, label="trial-specific share (observed − shuffled)")
            for x, c, ss in zip(xs, path, ys):
                bp = full.loc[c, f"bs_{m}_p"]
                if bp < 0.05:
                    a.annotate("†", (x, ss), textcoords="offset points", xytext=(0, -12 if ss < 0 else 4), ha="center", fontsize=11, color=c_spec)
        for x, c, yy in zip(xs, path, y):
            p = full.loc[c, f"p_{m}"]
            sig = p < 0.05 and yy < 0
            a.scatter([x], [yy], s=55, zorder=4, facecolor=c_obs if sig else "white", edgecolor=c_obs, lw=1.5)
            if full.loc[c, f"spec_{m}"]:
                a.annotate("*", (x, yy), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=12, color=ink)
        # extras removed markers
        for c, x, mk, lab in (("noextras", 0, "D", "no trial extras (k=0)"), ("demo", len(SHARED), "s", "demo only"), ("common10", 2, "^", "common-10 (k=2)")):
            a.scatter([x + 0.12], [full.loc[c, f"d_{m}"]], marker=mk, s=45, color=grey, zorder=4, label=lab,
                      edgecolor=ink if full.loc[c, f"p_{m}"] < 0.05 and full.loc[c, f"d_{m}"] < 0 else grey)
        a.axhline(0, color=grey, lw=0.8)
        a.set_ylabel(yl)
        a.set_xticks(xs, xl if i == 3 else [""] * len(xs), fontsize=8)
        a.grid(alpha=0.25, lw=0.5)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        if i == 0:
            a.legend(fontsize=7.5, frameon=False, loc="lower left", ncol=2)
            a.set_title("B. cumulative removal, most → least treatment-associated", fontsize=10)
        # LOO panel
        b = ax[i, 1]
        loo = [f"loo_{f}" for f in SHARED]
        yv = [full.loc[c, f"d_{m}"] for c in loo]
        b.barh(range(len(SHARED)), yv, color=c_obs, alpha=0.8, height=0.55, label="ECG − base")
        if m in ("absd", "z2"):
            b.barh(np.arange(len(SHARED)) + 0.3, [full.loc[c, f"bs_{m}_specific"] for c in loo], color=c_spec, alpha=0.7, height=0.25,
                   label="trial-specific share")
        for j, c in enumerate(loo):
            p = full.loc[c, f"p_{m}"]
            t = f"p={fmt_p(p)}" + ("*" if full.loc[c, f"spec_{m}"] else "")
            if m in ("absd", "z2"):
                t += f"; shuf p={fmt_p(full.loc[c, f'bs_{m}_p'])}"
            b.annotate(t, (0, j), textcoords="offset points", xytext=(4, -3), fontsize=7, color=ink)
        b.axvline(full.loc["sparse", f"d_{m}"], color=grey, ls=":", lw=1.2, label="full sparse")
        b.axvline(0, color=grey, lw=0.8)
        b.set_yticks(range(len(SHARED)), [SHORT[f] for f in SHARED] if True else [], fontsize=8)
        b.invert_yaxis()
        from matplotlib.ticker import MaxNLocator
        b.xaxis.set_major_locator(MaxNLocator(4))
        b.grid(alpha=0.25, lw=0.5, axis="x")
        for s in ("top", "right"):
            b.spines[s].set_visible(False)
        if i == 0:
            b.set_title("A. leave one diagnosis out", fontsize=10)
            b.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=3)
    ax[3, 0].set_xlabel("number of shared diagnoses removed (label = diagnosis removed at that step)")
    fig.suptitle("S7 diagnosis removal from the sparse PS (18 trials, full cohort; negative = ECG better)\n"
                 "filled = sign-flip p<0.05; * = also beats shufECG and noise32 in direction; † = beats shuffled-RCT benchmark null (p<0.05)",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(DOCS / "S7_DXREMOVAL_curve.png", dpi=130)
    plt.close(fig)
    # heat map
    cid = list(dict.fromkeys(M.cell))
    fig, ax = plt.subplots(1, 4, figsize=(22, 17))
    for k, m in enumerate(METRICS):
        Z = np.full((len(cid), 3), np.nan)
        Tx = [[""] * 3 for _ in cid]
        for i, c in enumerate(cid):
            for j, h in enumerate(HALVES):
                r = M[(M.cell == c) & (M.half == h)]
                if len(r):
                    r = r.iloc[0]
                    Z[i, j] = r[f"d_{m}"]
                    Tx[i][j] = f"{r[f'd_{m}']:.3g} p={fmt_p(r[f'p_{m}'])}" + ("*" if r[f"spec_{m}"] else "") + \
                        ("†" if m in ("absd", "z2") and r.get(f"bs_{m}_p", 1) < 0.05 else "")
        vmax = np.nanmax(np.abs(Z)) or 1
        im = ax[k].imshow(Z, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
        for i in range(len(cid)):
            for j in range(3):
                ax[k].text(j, i, Tx[i][j], ha="center", va="center", fontsize=6,
                           color="white" if np.isfinite(Z[i, j]) and abs(Z[i, j]) > 0.6 * vmax else ink)
        ax[k].set_xticks(range(3), HALVES)
        ax[k].set_yticks(range(len(cid)), [c.replace("loo_", "loo−").replace("ischemic_heart_disease_or_mi", "IHD/MI") for c in cid] if k == 0 else [""] * len(cid), fontsize=7)
        ax[k].set_title(f"d_{m} (ECG − base)")
        fig.colorbar(im, ax=ax[k], fraction=0.04)
    fig.suptitle("S7: ECG − base per cell and half (blue = ECG better); sign-flip p over 18 trials; * = beats shufECG and noise32 in direction; "
                 "† = beats shuffled-RCT benchmark (p<0.05)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(DOCS / "S7_DXREMOVAL_heatmap.png", dpi=110)
    plt.close(fig)


def tables(M, AM, spec, sub, Pl, df):
    L = []
    for h in HALVES:
        x = M[M.half == h].copy()
        for m in METRICS:
            x[m] = [f"{d:+.3f} ({k}; p={fmt_p(p)}" + (f"; q={fmt_p(q)}" if h == "full" else "") + ")" + (" **S**" if s else "")
                    for d, k, p, q, s in zip(x[f"d_{m}"], x[f"k_{m}"], x[f"p_{m}"], x[f"q_{m}"], x[f"spec_{m}"])]
        x["cons base→ECG"] = [f"{a:.0f}→{b:.0f}" for a, b in zip(x.cons_b, x.cons_a)]
        x["phi base→ECG"] = [f"{a:.2f}→{b:.2f}" for a, b in zip(x.phi_b, x.phi_a)]
        L.append(f"### ECG vs base, half = {h}\n")
        L.append(E.md(x[["cell", "k_removed", "n_trials"] + METRICS + ["cons base→ECG", "phi base→ECG"]], 3) + "\n")
    for h in HALVES:
        x = M[M.half == h].copy()
        for m in METRICS:
            x[m] = [f"{a:+.3f} (p={fmt_p(b)}) / {c:+.3f} (p={fmt_p(d)})" for a, b, c, d in
                    zip(x[f"d_{m}_vs_shufECG"], x[f"p_{m}_vs_shufECG"], x[f"d_{m}_vs_noise"], x[f"p_{m}_vs_noise"])]
        L.append(f"### ECG vs placebos, half = {h} (ECG − shufECG / ECG − noise32)\n")
        L.append(E.md(x[["cell"] + METRICS], 3) + "\n")
    x = M[M.half == "full"].copy()
    cols = ["cell", "d_absd", "bs_absd_null_mean", "bs_absd_specific", "bs_absd_p", "bh_q_bs_absd", "cl_p_absd", "cl_k_absd", "loo_pmax_absd",
            "d_z2", "bs_z2_null_mean", "bs_z2_specific", "bs_z2_p", "bh_q_bs_z2", "cl_p_z2", "loo_pmax_z2", "shrink_abs_loghr_base", "shrink_abs_loghr_ECG"]
    L.append("### Benchmark specificity, clustering and leave-one-trial-out (full cohort)\n")
    L.append(E.md(x[cols], 3) + "\n")
    cols = ["cell"] + [f"{a}_{m}" for m in ("mean_smd", "cstat") for a in ("cl_p", "cl_k", "loo_pmax")]
    L.append("### Balance: comparator-clustered p and leave-one-trial-out max p (full cohort)\n")
    L.append(E.md(x[cols], 3) + "\n")
    for h in ("A", "B"):
        x = M[M.half == h]
        L.append(f"### Benchmark shuffle in half {h} (2,000 draws)\n")
        L.append(E.md(x[["cell", "d_absd", "bs_absd_specific", "bs_absd_p", "d_z2", "bs_z2_specific", "bs_z2_p"]], 3) + "\n")
    L.append("### Substitution (full cohort, leave-one-out)\n")
    L.append(E.md(sub, 3) + "\n")
    for h in HALVES:
        a = AM[AM.half == h]
        L.append(f"### Arm means across trials, half = {h}\n")
        L.append(E.md(a, 3) + "\n")
    (OUT / "generated_tables.md").write_text("\n".join(L))
    print("tables ->", OUT / "generated_tables.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["run", "summarize"])
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--out", default="results.csv")
    a = ap.parse_args()
    if a.mode == "run":
        run(a.trials.split(","), a.workers, a.out)
    else:
        summarize(a.out)


if __name__ == "__main__":
    main()
