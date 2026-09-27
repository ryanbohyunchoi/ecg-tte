#!/usr/bin/env python
"""v1.6 sweep S8 (headline): where does adding AI-ECG to the PS move held-out covariates below |SMD| 0.1?
Exploratory (docs/V16_SWEEP_PLAN.md guardrails). Aggregates only.

PART 1 grid (each cell run as base, base+ECG, base+shufECG (T.shuffle_perm rows, same dimension), base+noise
(Gaussian, same dimension); unmatched once per trial/half):
  bases (1:1 caliper-0.2 matching, L2 C=1 PS, 32 BCL PCs):
    none        ECG only (base arm = unmatched)
    demo        T.demo (age, sex, index_year)
    demo_race   demo + race block (claude-v16-covars)
    min7        age, sex, race block, t2d, cad_ihd, hypertension_v11, hyperlipidemia (= S1/S6)
    min7_afhf   min7 + atrial_fibrillation, heart_failure (T.cov, where present; = S1 r4)
    common10    demo + the 7 most prevalent shared flags (S7 spec.json common7)
    sparse      T.X_dx
    sparse_p25/p50/p75  sparse on T.degraded(p, seed), seeds 0,1,2; balance on the TRUE (undegraded) panels
    sparse_noAF sparse minus atrial_fibrillation
    hdPS25/50/200  sparse + top-k hdPS levels ranked on the analysed rows' treatment (= S1)
  modifiers (crossed with demo, min7, sparse, sparse_p50, hdPS200): pc64 (64 PCs; shuf = same permutation, noise64
  seeded 3000+1000*64 as S3), cal0.1 (1:1 caliper 0.1), m1to3 (1:3 caliper 0.2), overlap (overlap weights).
  Trial subsets (analysis level): all 18 vs physiology trials (trial_specs role == 'physiology').
Panels: p58 = engine 58 variables (make_acc_figure.VARS); xo = claude-v16-covars2 block 'other' (non-ECG-proximal),
kept, exposure leaks removed, PS-overlap/proxy columns of each cell removed (s6_balance.load_extra / excluded_extra).
Threshold metrics per trial x cell x arm: pct_lt10 (% of available held-out variables with |SMD| < 0.1; primary),
pct_lt05, pct_gt20, max |SMD|, keyphys_all (all available key-physiology variables < 0.1; p58 only).
Love-plot count: number of variables whose median |SMD| across trials is < 0.1 (summary level).

Usage: s8_headline.py run --halves A [--trials ..] [--workers 40]
       s8_headline.py select            (half A only -> selection.json)
       s8_headline.py run --halves full,B
       s8_headline.py summarize         (all halves; markdown, figures)
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s6_balance as S6  # noqa: E402  (also installs the cached exact sign-flip into the engine)
import v16_engine as E  # noqa: E402
from audit_v16 import CLUSTER  # noqa: E402
from make_acc_figure import names  # noqa: E402
from trial_specs import TRIALS as SPECS  # noqa: E402
from v13_summarize import md  # noqa: E402

SWEEP = "s8-headline"
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s8-headline")
DOCS = HERE.parent.parent / "docs" / "v16"
COV2 = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars2")
S7SPEC = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s7-dxremoval/spec.json")
SEEDS = (0, 1, 2)
DROP = {"sparse_p25": 0.25, "sparse_p50": 0.5, "sparse_p75": 0.75}
BASES = ["none", "demo", "demo_race", "min7", "min7_afhf", "common10", "sparse", "sparse_p25", "sparse_p50", "sparse_p75",
         "sparse_noAF", "hdPS25", "hdPS50", "hdPS200"]
BASE_LAB = {"none": "none (ECG only)", "demo": "demo", "demo_race": "demo+race", "min7": "minimal-7", "min7_afhf": "min-7+AF+HF",
            "common10": "common-10", "sparse": "sparse", "sparse_p25": "sparse, 25% dropout", "sparse_p50": "sparse, 50% dropout",
            "sparse_p75": "sparse, 75% dropout", "sparse_noAF": "sparse minus AF", "hdPS25": "hdPS25", "hdPS50": "hdPS50",
            "hdPS200": "hdPS200"}
MOD_BASES = ["demo", "min7", "sparse", "sparse_p50", "hdPS200"]
MODS = {"default": dict(dim=32, est=("match", 0.2, 1)), "pc64": dict(dim=64, est=("match", 0.2, 1)),
        "cal0.1": dict(dim=32, est=("match", 0.1, 1)), "m1to3": dict(dim=32, est=("match", 0.2, 3)),
        "overlap": dict(dim=32, est=("overlap",))}
MOD_LAB = {"default": "1:1 cal0.2, 32 PCs", "pc64": "64 PCs", "cal0.1": "caliper 0.1", "m1to3": "1:3 matching", "overlap": "overlap weights"}
CELLS = [f"{b}|default" for b in BASES] + [f"{b}|{m}" for b in MOD_BASES for m in MODS if m != "default"]
ROLES = ["base", "ECG", "shufECG", "noise"]
KEYPHYS = ["smd_obs_lvef", "pp_BNP__ntprobnp", "pp_LAB__egfr", "smd_obs_hemoglobin", "pp_LVSTRUCT__lvidd", "pp_LVSTRUCT__lvesvi",
           "pp_DIAST__lavi", "pp_DIAST__e_eprime", "pp_RVPULM__rvsp"]
PHYS = [n for n in E.TRIALS if SPECS[names[n][0]].get("role") == "physiology"]
SUBSETS = {"all": list(E.TRIALS), "phys": PHYS}
TH = ["pct_lt10", "pct_lt05", "pct_gt20", "max_smd", "keyphys_all"]
HIGHER_BETTER = {"pct_lt10", "pct_lt05", "keyphys_all"}
MLAB = {"pct_lt10": "% |SMD|<0.1", "pct_lt05": "% |SMD|<0.05", "pct_gt20": "% |SMD|>0.2", "max_smd": "max |SMD|",
        "keyphys_all": "all key physiology <0.1", "absd": "|Δlog HR| vs RCT", "z2": "z² vs RCT", "mean_smd": "58-var mean |SMD|",
        "cstat": "held-out C"}


def cell_label(c):
    b, m = c.split("|")
    return BASE_LAB[b] + ("" if m == "default" else f" / {MOD_LAB[m]}")


# ---------------------------------------------------------------- capture matched sample from run_cell
_LAST = {}
_match0, _weights0 = E.match, E.weights


def _match(lg, t, cal=0.2, ratio=1):
    r = _match0(lg, t, cal=cal, ratio=ratio)
    _LAST["m"] = (r[0], r[2])
    return r


def _weights(lg, t, kind):
    w = _weights0(lg, t, kind)
    i = np.where(w > 0)[0]
    _LAST["m"] = (i, w[i])
    return w


E.match, E.weights = _match, _weights

_TC = {}


def trial(n):
    if n not in _TC:
        T = E.load_trial(n)
        C = S6.load_new(T)
        Xe, ovl, blk = S6.load_extra(T, COV2)
        Xe = Xe[[c for c in Xe.columns if blk[c] != "ecg_proximal"]]
        _TC.clear()
        _TC[n] = (T, C, Xe, ovl)
    return _TC[n]


def design(T, C, D, base, rows, t):
    """-> (X, ps_names). D = degraded trial (or T)."""
    cov = T.cov.iloc[rows]
    dxn = T.demo + T.dxc
    if base == "none":
        return None, []
    if base == "demo":
        return cov[T.demo].to_numpy(float), list(T.demo)
    if base == "demo_race":
        return np.hstack([cov[T.demo].to_numpy(float), C[S6.RACE].to_numpy(float)[rows]]), list(T.demo) + S6.RACE
    m7n = ["age_at_index", "male"] + S6.RACE + S6.MIN7 + ["diabetes", "ischemic_heart_disease_or_mi", "hypertension"]
    m7 = np.hstack([cov[["age_at_index", "male"]].to_numpy(float), C[S6.RACE].to_numpy(float)[rows], C[S6.MIN7].to_numpy(float)[rows]])
    if base == "min7":
        return m7, m7n
    if base == "min7_afhf":
        af = [c for c in ("atrial_fibrillation", "heart_failure") if c in T.cov]
        return np.hstack([m7, cov[af].to_numpy(float)]), m7n + af
    if base == "common10":
        c7 = json.loads(S7SPEC.read_text())["common7"]
        cols = T.demo + [f for f in T.dxc if f in c7]
        return cov[cols].to_numpy(float), cols
    if base == "sparse":
        return T.X_dx[rows], dxn
    if base in DROP:
        return D.X_dx[rows], dxn
    if base == "sparse_noAF":
        cols = T.demo + [f for f in T.dxc if f != "atrial_fibrillation"]
        return cov[cols].to_numpy(float), cols
    if base.startswith("hdPS"):
        k = int(base[4:])
        return np.hstack([T.X_dx[rows], T.hd(200, t=t, rows=rows)[:, :k]]), dxn
    raise KeyError(base)


def ecg_mats(T, dim):
    if dim == 32:
        return T.ecg_pc, T.ecg_pc[T.shuffle_perm], T.noise32
    return T.ecg_pc64, T.ecg_pc64[T.shuffle_perm], np.random.default_rng(3000 + 1000 * dim).normal(size=(len(T.t), dim))


def thresholds(v, key=None):
    v = np.asarray(v, float)
    ok = np.isfinite(v)
    x = v[ok]
    r = dict(n=int(ok.sum()))
    if not len(x):
        return dict(r, pct_lt10=np.nan, pct_lt05=np.nan, pct_gt20=np.nan, max_smd=np.nan)
    r.update(pct_lt10=100 * float(np.mean(x < 0.1)), pct_lt05=100 * float(np.mean(x < 0.05)),
             pct_gt20=100 * float(np.mean(x > 0.2)), max_smd=float(x.max()))
    return r


def task(args):
    n, half, cell, seed = args
    t0 = time.time()
    base, mod = cell.split("|") if "|" in cell else ("none", "default")
    T, C, Xe0, ovl = trial(n)
    i = E.TRIALS.index(n)
    rows = S6.halves(T, i)[half]
    t = T.t[rows]
    D = T.degraded(DROP[base], seed) if base in DROP else T
    X, psn = design(T, C, D, base, rows, t)
    dim, est = MODS[mod]["dim"], MODS[mod]["est"]
    xdrop = S6.excluded_extra(psn, list(Xe0.columns), ovl)
    Xe = Xe0.drop(columns=xdrop).iloc[rows]
    Xe = Xe.loc[:, Xe.notna().sum() > 0]
    Xe = Xe.loc[:, Xe.nunique() > 1]
    XV = Xe.to_numpy(float)
    xcols = list(Xe.columns)
    pc, sh, nz = (M[rows] for M in ecg_mats(T, dim))
    if cell == "unmatched":
        arms = [("unmatched", None)]
    elif base == "none":
        arms = [("ECG", pc), ("shufECG", sh), ("noise", nz)]
    else:
        arms = [("base", X), ("ECG", np.hstack([X, pc])), ("shufECG", np.hstack([X, sh])), ("noise", np.hstack([X, nz]))]
    out, xrows = [], []
    for role, Xa in arms:
        _LAST.clear()
        r = E.run_cell(D, Xa, rows=rows, heldout=T.H, estimator=est if Xa is not None else ("match", 0.2, 1))
        if Xa is None:
            s_idx, s_w = np.arange(len(t)), np.ones(len(t))
        else:
            s_idx, s_w = _LAST["m"]
        sv = np.array([r[f"smd:{c}"] for c, _, _ in E.VARS])
        p58 = thresholds(sv)
        kp = np.array([r[f"smd:{c}"] for c in KEYPHYS])
        kp = kp[np.isfinite(kp)]
        xs = E.smd_components(XV, t, s_idx, s_w, t[s_idx]) if xcols else np.array([])
        xo = thresholds(xs)
        rec = dict(sweep=SWEEP, cell=cell, base=base if cell != "unmatched" else "unmatched", mod=mod, seed=seed, p_drop=DROP.get(base, 0.0), ecg_dim=dim,
                   estimator=str(est), trial=n, half=half, arm_role=role,
                   arm_label=("unmatched" if role == "unmatched" else f"{cell_label(cell)} [{role}]"), **r,
                   **{f"p58_{k}": v for k, v in p58.items()}, p58_keyphys_all=float(np.all(kp < 0.1)) if len(kp) else np.nan,
                   p58_keyphys_n=len(kp), **{f"xo_{k}": v for k, v in xo.items()}, xo_mean=float(np.nanmean(xs)) if len(xs) and np.isfinite(xs).any() else np.nan,
                   xo_ndrop=len(xdrop), rb=T.rb, rs=T.rs)
        out.append(rec)
        if half == "full" and len(xs):
            xrows.extend(dict(cell=cell, seed=seed, trial=n, arm_role=role, var=c, smd=float(v)) for c, v in zip(xcols, xs) if np.isfinite(v))
    print(f"{n} {half} {cell} s{seed} {time.time() - t0:.0f}s", flush=True)
    return out, xrows


def tasks_for(trials, halves):
    tk = []
    for n in trials:
        for h in halves:
            tk.append((n, h, "unmatched", 0))
            for c in CELLS:
                for s in (SEEDS if c.split("|")[0] in DROP else (0,)):
                    tk.append((n, h, c, s))
    return tk


def run(trials, halves, workers, tag):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    tk = tasks_for(trials, halves)
    size = {n: len(E.load_trial(n).t) for n in trials}
    tk.sort(key=lambda x: (-size[x[0]], x[0]))  # same trial consecutive -> worker trial cache reuse
    res, xres = [], []
    t0 = time.time()
    with Pool(min(workers, 40)) as p:
        for k, (r, x) in enumerate(p.imap(task, tk, chunksize=4)):
            res.extend(r)
            xres.extend(x)
            if (k + 1) % 100 == 0 or k + 1 == len(tk):
                print(f"{k + 1}/{len(tk)} tasks {time.time() - t0:.0f}s", flush=True)
    pd.DataFrame(res).to_csv(OUT / f"results_{tag}.csv", index=False)
    if xres:
        pd.DataFrame(xres).to_parquet(OUT / f"xvar_{tag}.parquet", index=False)
    print("done", tag, len(res), flush=True)


# ---------------------------------------------------------------- summaries
def load_results(halves=None):
    fs = sorted(OUT.glob("results_*.csv"))
    df = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    if halves is not None:
        df = df[df.half.isin(halves)]
    df["absd"] = (df.loghr - df.rb).abs()
    df["z2"] = (df.loghr - df.rb) ** 2 / (df.se ** 2 + df.rs ** 2)
    return df


METRICS = [f"p58_{m}" for m in TH] + [f"xo_{m}" for m in TH if m != "keyphys_all"] + ["absd", "z2", "mean_smd", "cstat"]


def per_trial(df, cell, half, role):
    """trial-level value of every metric for (cell, half, role); dropout cells averaged over seeds.
    'none' cell: base = unmatched."""
    if role == "base" and cell.startswith("none|"):
        g = df[(df.cell == "unmatched") & (df.half == half)]
    else:
        g = df[(df.cell == cell) & (df.half == half) & (df.arm_role == role)]
    return g.groupby("trial")[METRICS].mean()


def sflip(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    return S6.sign_flip(d)[1] if len(d) else np.nan


def paired(a, b, m, trials):
    d = (a[m] - b[m]).reindex(trials).dropna()
    if not len(d):
        return dict(d=np.nan, k="0/0", p=np.nan)
    good = (d > 0) if m.split("_", 1)[-1] in HIGHER_BETTER or m in HIGHER_BETTER else (d < 0)
    return dict(d=float(d.mean()), k=f"{int(good.sum())}/{len(d)}", p=sflip(d.to_numpy()), dser=d)


def cluster_loo(d):
    d = d.dropna()
    if len(d) < 3:
        return dict(cluster_p=np.nan, cluster_k="", loo_p_max=np.nan)
    cl = d.groupby(d.index.map(CLUSTER)).mean()
    loo = [sflip(d.drop(k).to_numpy()) for k in d.index]
    return dict(cluster_p=sflip(cl.to_numpy()), cluster_k=f"{int((cl > 0).sum())}/{len(cl)}+", loo_p_max=float(max(loo)))


def love_count(df, cell, half, role, trials):
    """# of 58 variables whose median |SMD| across trials is < 0.1 (dropout: trial value = mean over seeds)."""
    if role == "base" and cell.startswith("none|"):
        g = df[(df.cell == "unmatched") & (df.half == half)]
    elif role == "unmatched":
        g = df[(df.cell == "unmatched") & (df.half == half)]
    else:
        g = df[(df.cell == cell) & (df.half == half) & (df.arm_role == role)]
    g = g[g.trial.isin(trials)]
    cols = [f"smd:{c}" for c, _, _ in E.VARS]
    med = g.groupby("trial")[cols].mean().median()
    return int((med < 0.1).sum()), int(med.notna().sum()), med


def grid_summary(df, halves):
    rows = []
    for cell in CELLS:
        for h in halves:
            A = {r: per_trial(df, cell, h, r) for r in ROLES}
            for sub, trs in SUBSETS.items():
                r = dict(cell=cell, base=cell.split("|")[0], mod=cell.split("|")[1], half=h, subset=sub)
                for m in METRICS:
                    r[f"base_{m}"] = float(A["base"][m].reindex(trs).mean())
                    r[f"ecg_{m}"] = float(A["ECG"][m].reindex(trs).mean())
                    for b in ("base", "shufECG", "noise"):
                        x = paired(A["ECG"], A[b], m, trs)
                        tag = {"base": "", "shufECG": "_shuf", "noise": "_noise"}[b]
                        r[f"d{tag}_{m}"], r[f"k{tag}_{m}"], r[f"p{tag}_{m}"] = x["d"], x["k"], x["p"]
                        if b == "base" and m in ("p58_pct_lt10", "xo_pct_lt10", "p58_max_smd", "absd", "z2") and "dser" in x:
                            cl = cluster_loo(x["dser"] * (1 if m.endswith("lt10") else -1))
                            r[f"clp_{m}"], r[f"clk_{m}"], r[f"loo_{m}"] = cl["cluster_p"], cl["cluster_k"], cl["loo_p_max"]
                    for b in ("shufECG", "noise"):
                        x = paired(A[b], A["base"], m, trs)
                        tag = {"shufECG": "_shufbase", "noise": "_noisebase"}[b]
                        r[f"d{tag}_{m}"], r[f"p{tag}_{m}"] = x["d"], x["p"]
                for role in ("base", "ECG", "shufECG", "noise"):
                    c, nv, _ = love_count(df, cell, h, role, trs)
                    r[f"love_{role}"] = c
                r["love_nvars"] = nv
                r["love_unmatched"] = love_count(df, cell, h, "unmatched", trs)[0]
                rows.append(r)
    G = pd.DataFrame(rows)
    return G


def add_fdr(G):
    for m in ("p58_pct_lt10", "xo_pct_lt10", "p58_pct_lt05", "p58_pct_gt20", "p58_max_smd", "p58_keyphys_all", "absd", "z2"):
        G[f"q_{m}"] = np.nan
        for (h, s), k in G.groupby(["half", "subset"]).groups.items():
            G.loc[k, f"q_{m}"] = E.bh_fdr(G.loc[k, f"p_{m}"])
    # global BH over cells x subsets x panels for the primary metric (per half)
    G["q_global_lt10_p58"] = np.nan
    G["q_global_lt10_xo"] = np.nan
    for h, k in G.groupby("half").groups.items():
        p = np.r_[G.loc[k, "p_p58_pct_lt10"].to_numpy(), G.loc[k, "p_xo_pct_lt10"].to_numpy()]
        q = E.bh_fdr(p)
        G.loc[k, "q_global_lt10_p58"], G.loc[k, "q_global_lt10_xo"] = q[: len(k)], q[len(k):]
    return G


SEL_RULE = ("Half A only; panel p58; metric = trial-level % of held-out variables with |SMD| < 0.1 (ECG − base, dropout cells "
            "averaged over 3 seeds). Eligible scenario = (cell, trial subset) with ECG − base gain > 0, exact sign-flip p < 0.05, "
            "and ECG − shufECG > 0 and ECG − noise > 0. Base 'none' (ECG only vs unmatched) excluded from the headline pool "
            "(it measures matching vs no matching, not ECG added to a PS); reported descriptively. Rank by gain (descending); take the "
            "top 3 with at most one scenario per base (the base's modifier variants and trial subsets compete for its slot).")


def select():
    df = load_results(["A"])
    G = grid_summary(df, ["A"])
    G.to_csv(OUT / "grid_halfA.csv", index=False)
    e = G[(G.d_p58_pct_lt10 > 0) & (G.p_p58_pct_lt10 < 0.05) & (G.d_shuf_p58_pct_lt10 > 0) & (G.d_noise_p58_pct_lt10 > 0) & (G.base != "none")]
    e = e.sort_values(["d_p58_pct_lt10", "p_p58_pct_lt10"], ascending=[False, True])
    sel, used = [], set()
    for _, r in e.iterrows():
        if r.base in used:
            continue
        used.add(r.base)
        sel.append(dict(cell=r.cell, subset=r.subset, label=cell_label(r.cell) + ("" if r.subset == "all" else " (physiology trials)"),
                        halfA_d=r.d_p58_pct_lt10, halfA_k=r.k_p58_pct_lt10, halfA_p=r.p_p58_pct_lt10, halfA_d_shuf=r.d_shuf_p58_pct_lt10,
                        halfA_d_noise=r.d_noise_p58_pct_lt10, halfA_base=r.base_p58_pct_lt10, halfA_ecg=r.ecg_p58_pct_lt10))
        if len(sel) == 3:
            break
    top = e.head(15)[["cell", "subset", "d_p58_pct_lt10", "k_p58_pct_lt10", "p_p58_pct_lt10", "d_shuf_p58_pct_lt10", "d_noise_p58_pct_lt10"]]
    J = dict(created=time.strftime("%Y-%m-%d %H:%M:%S %Z"), rule=SEL_RULE, n_eligible=int(len(e)), n_scenarios=int(len(G)),
             selected=sel, eligible_top15=top.to_dict("records"), halves_available_at_selection=sorted(set(df.half)))
    (OUT / "selection.json").write_text(json.dumps(J, indent=1, default=float))
    print(json.dumps(J, indent=1, default=float))


# ---------------------------------------------------------------- part 2: trial emulation
def emu_trial(df, cell, half, role, trials):
    """per-trial loghr/se (+rb/rs); dropout: per-seed rows kept (seed column)."""
    if role == "base" and cell.startswith("none|"):
        g = df[(df.cell == "unmatched") & (df.half == half)]
    else:
        g = df[(df.cell == cell) & (df.half == half) & (df.arm_role == role)]
    return g[g.trial.isin(trials)][["trial", "seed", "loghr", "se", "rb", "rs"]]


def emu_metrics(g):
    """seed-averaged agreement metrics over trials."""
    out = []
    for s, x in g.groupby("seed"):
        x = x.dropna(subset=["loghr", "se"])
        z = (x.loghr - x.rb) / np.sqrt(x.se ** 2 + x.rs ** 2)
        lo, hi = x.rb - 1.96 * x.rs, x.rb + 1.96 * x.rs
        out.append(dict(absd=float((x.loghr - x.rb).abs().mean()), z2=float((z ** 2).mean()), cons=100 * float(np.mean(np.abs(z) < 1.96)),
                        est_agree=100 * float(np.mean((x.loghr >= lo) & (x.loghr <= hi))),
                        phi=E._phi((x.loghr - x.rb).to_numpy(), (x.se ** 2 + x.rs ** 2).to_numpy()),
                        sig_agree=100 * float(np.mean(np.sign(x.loghr) == np.sign(x.rb)))))
    return pd.DataFrame(out).mean().to_dict()


def bench_shuffle(le, lb, se_e, se_b, rb, rs, nperm=5000, seed=1111):
    rng = np.random.default_rng(seed)
    fa = lambda r_: np.mean(np.abs(le - r_) - np.abs(lb - r_))
    fz = lambda r_, s_: np.mean((le - r_) ** 2 / (se_e ** 2 + s_ ** 2) - (lb - r_) ** 2 / (se_b ** 2 + s_ ** 2))
    na, nz = np.empty(nperm), np.empty(nperm)
    for i in range(nperm):
        pi = rng.permutation(len(rb))
        na[i], nz[i] = fa(rb[pi]), fz(rb[pi], rs[pi])
    return dict(d_absd=fa(rb), null_absd=float(np.median(na)), p_bs_absd=float(np.mean(na <= fa(rb))),
                d_z2=fz(rb, rs), null_z2=float(np.median(nz)), p_bs_z2=float(np.mean(nz <= fz(rb, rs))))


def part2(df, scen):
    rows, per = [], []
    for sc in scen:
        cell, sub = sc["cell"], sc["subset"]
        trs = SUBSETS[sub]
        for h in ("full", "A", "B"):
            G = {r: emu_trial(df, cell, h, r, trs) for r in ROLES}
            r = dict(scenario=sc["label"], cell=cell, subset=sub, half=h)
            for role in ROLES:
                for k, v in emu_metrics(G[role]).items():
                    r[f"{role}_{k}"] = v
            # paired per-trial (seed-averaged |Δ| / z²)
            def tl(g):
                g = g.assign(absd=(g.loghr - g.rb).abs(), z2=(g.loghr - g.rb) ** 2 / (g.se ** 2 + g.rs ** 2))
                return g.groupby("trial")[["absd", "z2", "loghr", "se", "rb", "rs"]].mean()
            P = {role: tl(G[role]) for role in ROLES}
            for m in ("absd", "z2"):
                for b in ("base", "shufECG", "noise"):
                    d = (P["ECG"][m] - P[b][m]).dropna()
                    tag = {"base": "", "shufECG": "_shuf", "noise": "_noise"}[b]
                    r[f"d{tag}_{m}"], r[f"k{tag}_{m}"], r[f"p{tag}_{m}"] = float(d.mean()), f"{int((d < 0).sum())}/{len(d)}", sflip(d.to_numpy())
                    if b == "base":
                        cl = cluster_loo(-d)
                        r[f"clp_{m}"], r[f"clk_{m}"], r[f"loo_{m}"] = cl["cluster_p"], cl["cluster_k"], cl["loo_p_max"]
            # benchmark shuffle (seed-averaged per-trial statistics: use per-seed average over seeds of the permutation stat)
            bs = []
            for s in sorted(set(G["ECG"].seed)):
                e_ = G["ECG"][G["ECG"].seed == s].set_index("trial")
                b_ = G["base"][G["base"].seed == s].set_index("trial") if not cell.startswith("none|") else G["base"].set_index("trial")
                tt = e_.index.intersection(b_.index)
                e_, b_ = e_.loc[tt], b_.loc[tt]
                ok = np.isfinite(e_.loghr.to_numpy()) & np.isfinite(b_.loghr.to_numpy())
                bs.append(bench_shuffle(e_.loghr.to_numpy()[ok], b_.loghr.to_numpy()[ok], e_.se.to_numpy()[ok], b_.se.to_numpy()[ok],
                                        e_.rb.to_numpy()[ok], e_.rs.to_numpy()[ok], seed=1111 + s))
            bsd = pd.DataFrame(bs).mean().to_dict()
            r.update({f"bs_{k}": v for k, v in bsd.items()})
            rows.append(r)
            if h == "full":
                for n in trs:
                    pr = dict(scenario=sc["label"], trial=n, rct_hr=np.exp(P["ECG"].rb.get(n, np.nan)))
                    for role in ("base", "ECG", "shufECG"):
                        if n in P[role].index:
                            pr[f"{role}_hr"] = float(np.exp(P[role].loghr[n]))
                            pr[f"{role}_absd"] = float(P[role].absd[n])
                    per.append(pr)
    return pd.DataFrame(rows), pd.DataFrame(per)


# ---------------------------------------------------------------- figures
SHORT = {"Coded record": "Coded", "Vitals & core labs": "Vitals/labs", "Other labs": "Other labs", "Echo: LV structure": "LV struct.",
         "Echo: LV function": "LV func.", "Echo: diastolic / LA": "Diast./LA", "Echo: RV / pulmonary": "RV/pulm.", "Echo: valves / aorta": "Valves"}


def loveplot(df, sc, fname, p_txt):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    cell, trs = sc["cell"], SUBSETS[sc["subset"]]
    nb, nv, mb = love_count(df, cell, "full", "base", trs)
    ne, _, me = love_count(df, cell, "full", "ECG", trs)
    _, _, mu = love_count(df, cell, "full", "unmatched", trs)
    lab = {c: (l, g) for c, l, g in E.VARS}
    order = [c for c, _, _ in E.VARS if np.isfinite(me.get(f"smd:{c}", np.nan))]
    y = dict(zip(order, np.arange(len(order))[::-1]))
    fig, ax = plt.subplots(figsize=(7.2, 10.5))
    for i, c in enumerate(order):
        if i % 2 == 0:
            ax.axhspan(y[c] - 0.5, y[c] + 0.5, color="#f4f5f7", zorder=0)
        b, e = mb[f"smd:{c}"], me[f"smd:{c}"]
        ax.plot([b, e], [y[c]] * 2, color="#2b8a3e" if e < b else "#c92a2a", lw=1.5, alpha=0.8, zorder=2)
    ax.scatter([mu[f"smd:{c}"] for c in order], [y[c] for c in order], marker="x", color="#868e96", s=18, lw=1, zorder=3, label="Unmatched")
    ax.scatter([mb[f"smd:{c}"] for c in order], [y[c] for c in order], color="#74c0fc", s=22, ec="white", lw=0.4, zorder=4, label="Without ECG")
    ax.scatter([me[f"smd:{c}"] for c in order], [y[c] for c in order], color="#d9480f", s=22, ec="white", lw=0.4, zorder=5, label="With ECG")
    ax.axvline(0.1, color="#777", ls="--", lw=0.9)
    ax.set_yticks(list(y.values()))
    ax.set_yticklabels([lab[c][0] for c in order], fontsize=6.5)
    for g in dict.fromkeys(lab[c][1] for c in order):
        ys = [y[c] for c in order if lab[c][1] == g]
        ax.axhline(min(ys) - 0.5, color="#bbb", lw=0.6)
        ax.annotate(SHORT[g], xy=(1.0, np.mean(ys)), xycoords=("axes fraction", "data"), xytext=(3, 0), textcoords="offset points",
                    rotation=270, va="center", fontsize=6.5, fontweight="bold", color="#444")
    xmax = max(0.3, float(np.nanmax([mu[f"smd:{c}"] for c in order])) * 1.05)
    ax.set_xlim(0, min(xmax, 0.8))
    ax.set_ylim(-0.7, len(order) - 0.3)
    ax.text(0.98, 0.995, f"variables < 0.1: {nb} → {ne} of {nv}\n(per-trial % p={p_txt})", transform=ax.transAxes, ha="right", va="top",
            fontsize=7.5, bbox=dict(fc="white", ec="#ccc", boxstyle="round,pad=0.3"))
    ax.set_xlabel(f"|SMD| after PS adjustment (median across {len(trs)} trials, full cohort)")
    ax.set_title(f"{sc['label']}: held-out balance without vs with AI-ECG", loc="left", fontweight="bold", fontsize=8.5)
    ax.legend(loc="lower right", fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(DOCS / fname, dpi=200)
    plt.close(fig)


def grid_heatmap(G):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cols = [(p, s, h) for p in ("p58", "xo") for s in ("all", "phys") for h in ("full", "A", "B")]
    M = np.full((len(CELLS), len(cols)), np.nan)
    Pp = M.copy()
    for i, c in enumerate(CELLS):
        for j, (p, s, h) in enumerate(cols):
            r = G[(G.cell == c) & (G.subset == s) & (G.half == h)]
            if len(r):
                M[i, j], Pp[i, j] = r.iloc[0][f"d_{p}_pct_lt10"], r.iloc[0][f"p_{p}_pct_lt10"]
    fig, ax = plt.subplots(figsize=(13, 12))
    v = np.nanmax(np.abs(M))
    im = ax.imshow(M, cmap="RdBu", vmin=-v, vmax=v, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isfinite(M[i, j]):
                st = "**" if Pp[i, j] < 0.01 else ("*" if Pp[i, j] < 0.05 else "")
                ax.text(j, i, f"{M[i, j]:+.1f}{st}", ha="center", va="center", fontsize=6.8,
                        color="white" if abs(M[i, j]) > 0.6 * v else "#111", fontweight="bold" if st else "normal")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([f"{'58-panel' if p == 'p58' else 'expanded non-ECG'}\n{'18 trials' if s == 'all' else '8 physiology'}\n{h}" for p, s, h in cols],
                       fontsize=6.5)
    ax.set_yticks(range(len(CELLS)))
    ax.set_yticklabels([cell_label(c) for c in CELLS], fontsize=7.5)
    ax.set_title("ECG − base: percentage points of held-out covariates with |SMD| < 0.1 (mean over trials; blue = ECG better)\n"
                 "* p<0.05, ** p<0.01 exact sign-flip across trials", fontsize=9)
    fig.colorbar(im, ax=ax, shrink=0.6, label="Δ % of variables with |SMD| < 0.1")
    fig.tight_layout()
    fig.savefig(DOCS / "S8_THRESHOLD_grid.png", dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------- report
def _f(x, nd=1):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{nd}f}"


def _p(x):
    return "—" if not np.isfinite(x) else (f"{x:.3f}" if x >= 0.001 else "<0.001")


def engine_heatmap(G):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    mets = ["absd", "z2", "mean_smd", "cstat"]
    g = G[(G.half == "full") & (G.subset == "all")].set_index("cell").reindex(CELLS)
    M = np.array([[-np.sign(g.loc[c, f"d_{m}"]) * -np.log10(max(g.loc[c, f"p_{m}"], 1e-5)) for m in mets] for c in CELLS])
    fig, ax = plt.subplots(figsize=(9, 11))
    im = ax.imshow(M, cmap="RdBu", vmin=-5, vmax=5, aspect="auto")
    for i, c in enumerate(CELLS):
        for j, m in enumerate(mets):
            d, p = g.loc[c, f"d_{m}"], g.loc[c, f"p_{m}"]
            ax.text(j, i, f"{d:+.3f}\np={p:.3f}", ha="center", va="center", fontsize=6, color="white" if abs(M[i, j]) > 3 else "#111",
                    fontweight="bold" if p < 0.05 else "normal")
    ax.set_xticks(range(len(mets)))
    ax.set_xticklabels([MLAB[m] for m in mets], fontsize=8)
    ax.set_yticks(range(len(CELLS)))
    ax.set_yticklabels([cell_label(c) for c in CELLS], fontsize=7.5)
    ax.set_title("S8: ECG − base, full cohort, 18 trials (d, sign-flip p). Colour = signed −log10 p; blue = ECG better", fontsize=8.5)
    fig.colorbar(im, ax=ax, shrink=0.6)
    fig.tight_layout()
    fig.savefig(DOCS / "S8_HEADLINE_heatmap.png", dpi=130)
    plt.close(fig)


def audit_checks(df):
    L = []
    v = pd.read_csv(E.OUT / "validation_estimates.csv").set_index(["trial", "arm"])
    f = df[df.half == "full"]
    dev = []
    for cell, role, arm in (("sparse|default", "base", "sparse"), ("sparse|default", "ECG", "sparse+ECG"), ("hdPS200|default", "base", "hdPS200"),
                            ("hdPS200|default", "ECG", "hdPS200+ECG"), ("unmatched", "unmatched", "unmatched")):
        g = f[(f.cell == cell) & (f.arm_role == role)].set_index("trial")
        for n in g.index:
            s = v.loc[(n, arm)]
            dev.append(dict(arm=arm, d_loghr=abs(g.loc[n, "loghr"] - s.loghr), d_mean_smd=abs(g.loc[n, "mean_smd"] - s.mean_smd),
                            d_pairs=abs(g.loc[n, "n_pairs"] - s.n_pairs) if np.isfinite(s.n_pairs) else 0.0,
                            d_cstat=abs(g.loc[n, "cstat"] - s.cstat)))
    D = pd.DataFrame(dev).groupby("arm").max().reset_index()
    L.append("**(1) Reproduction of engine validation** (full cohort, 18 trials; max |S8 − ENGINE_VALIDATION| over trials):\n")
    L.append(md(D, 8) + "\n")
    # pair counts
    pc = f[f.estimator.str.startswith("('match'")].copy()
    b = pc[pc.arm_role == "base"].groupby(["cell", "trial", "seed"]).n_pairs.first()
    rat = {r: (pc[pc.arm_role == r].groupby(["cell", "trial", "seed"]).n_pairs.first() / b).dropna() for r in ("ECG", "shufECG", "noise")}
    L.append("**(2) Pair counts** (matching cells, full cohort; arm pairs / base pairs): " +
             "; ".join(f"{r} median {x.median():.3f} (5th–95th pct {x.quantile(.05):.3f}–{x.quantile(.95):.3f})" for r, x in rat.items()) + ".\n")
    return "\n".join(L)


def report():
    os.umask(0o077)
    df = load_results(["full", "A", "B"])
    J = json.loads((OUT / "selection.json").read_text())
    G = add_fdr(grid_summary(df, ["full", "A", "B"]))
    G.to_csv(OUT / "grid_summary.csv", index=False)
    sel = J["selected"]
    scen = sel + [dict(cell="sparse|default", subset="all", label="sparse (reference)")]
    P2, PT = part2(df, scen)
    P2.to_csv(OUT / "part2_emulation.csv", index=False)
    PT.to_csv(OUT / "part2_per_trial.csv", index=False)
    grid_heatmap(G)
    engine_heatmap(G)
    figs = []
    for sc in scen:
        r = G[(G.cell == sc["cell"]) & (G.subset == sc["subset"]) & (G.half == "full")].iloc[0]
        slug = sc["cell"].replace("|default", "").replace("|", "_").replace(".", "") + ("_phys" if sc["subset"] == "phys" else "")
        fn = f"S8_LOVEPLOT_{slug}.png"
        loveplot(df, sc, fn, _p(r.p_p58_pct_lt10))
        figs.append(fn)
    kf = OUT / "key_findings.md"
    L = [f"# v1.6 S8 headline: where adding AI-ECG moves held-out covariates below |SMD| 0.1 ({time.strftime('%Y-%m-%d')})\n",
         "Exploratory, post-hoc. Script `scripts/v16/s8_headline.py`; outputs `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s8-headline/` "
         "(`results.csv`, `grid_summary.csv`, `part2_*.csv`, `selection.json`). Aggregates only; no patient-level rows.\n",
         "## Key findings\n", kf.read_text() if kf.exists() else "(pending)\n"]
    L += ["## Selection (half A only; written and committed before half-B / full confirmation)\n",
          f"Rule: {J['rule']}\n", f"Selection timestamp: **{J['created']}**; halves present in the results at selection: {J['halves_available_at_selection']}. "
          f"{J['n_eligible']} of {J['n_scenarios']} scenarios (cells × trial subsets) were eligible.\n", "```json", json.dumps(J["selected"], indent=1, default=float), "```\n",
          "Top eligible scenarios in half A:\n", md(pd.DataFrame(J["eligible_top15"]), 3) + "\n"]
    # confirmation
    rows = []
    for sc in scen:
        for h in ("A", "B", "full"):
            r = G[(G.cell == sc["cell"]) & (G.subset == sc["subset"]) & (G.half == h)].iloc[0]
            rows.append({"scenario": sc["label"], "half": h, "base %<0.1": f"{r.base_p58_pct_lt10:.1f}", "ECG %<0.1": f"{r.ecg_p58_pct_lt10:.1f}",
                         "d (k)": f"{_f(r.d_p58_pct_lt10)} ({r.k_p58_pct_lt10})", "p": _p(r.p_p58_pct_lt10), "q (grid)": _p(r.q_p58_pct_lt10),
                         "vs shuf d (p)": f"{_f(r.d_shuf_p58_pct_lt10)} ({_p(r.p_shuf_p58_pct_lt10)})",
                         "vs noise d (p)": f"{_f(r.d_noise_p58_pct_lt10)} ({_p(r.p_noise_p58_pct_lt10)})",
                         "cluster p (k)": f"{_p(r.clp_p58_pct_lt10)} ({r.clk_p58_pct_lt10})", "LOO max p": _p(r.loo_p58_pct_lt10),
                         "love <0.1 unm/base→ECG": f"{r.love_unmatched}/{r.love_base}→{r.love_ECG} of {r.love_nvars}",
                         "love shuf/noise": f"{r.love_shufECG}/{r.love_noise}",
                         "expanded d (p)": f"{_f(r.d_xo_pct_lt10)} ({_p(r.p_xo_pct_lt10)})"})
    L += ["## Confirmation of the selected scenarios (58-panel % of variables with |SMD| < 0.1)\n",
          "d = ECG − base in percentage points (mean over trials; positive = more variables below 0.1); k = trials improved; p = exact "
          "sign-flip; q = BH over the 34 cells within half × subset; cluster = sign-flip over 10 comparator clusters (k = clusters "
          "improved); LOO = max p leaving one trial out. Love = number of the 58 variables whose median |SMD| across trials is < 0.1 "
          "(unmatched / base → ECG). Expanded = claude-v16-covars2 non-ECG-proximal panel.\n", md(pd.DataFrame(rows)) + "\n"]
    # other thresholds for selected
    rows = []
    for sc in scen:
        for h in ("A", "B", "full"):
            r = G[(G.cell == sc["cell"]) & (G.subset == sc["subset"]) & (G.half == h)].iloc[0]
            d = {"scenario": sc["label"], "half": h}
            for m in ("p58_pct_lt05", "p58_pct_gt20", "p58_max_smd", "p58_keyphys_all", "xo_pct_lt05", "xo_pct_gt20", "xo_max_smd", "mean_smd"):
                d[m] = f"{r[f'base_{m}']:.3f}→{r[f'ecg_{m}']:.3f} ({_p(r[f'p_{m}'])})" if "max" in m or m == "mean_smd" else \
                    f"{r[f'base_{m}'] * (100 if m.endswith('keyphys_all') else 1):.1f}→{r[f'ecg_{m}'] * (100 if m.endswith('keyphys_all') else 1):.1f} ({_p(r[f'p_{m}'])})"
            rows.append(d)
    L += ["## Other threshold metrics for the selected scenarios (base → ECG, sign-flip p)\n",
          "pct_lt05 / pct_gt20: % of variables with |SMD| < 0.05 / > 0.2; max = largest |SMD|; keyphys_all = % of trials in which all "
          "available key physiology variables (LVEF, NT-proBNP, eGFR, Hb, LVIDd, LVESVi, LAVI, E/e', RVSP) are < 0.1.\n",
          md(pd.DataFrame(rows)) + "\n"]
    # part 2
    rows = []
    for _, r in P2.iterrows():
        rows.append({"scenario": r.scenario, "half": r.half,
                     "|Δ| base→ECG": f"{r.base_absd:.3f}→{r.ECG_absd:.3f}", "d |Δ| (k, p)": f"{r.d_absd:+.3f} ({r.k_absd}, {_p(r.p_absd)})",
                     "shuffled-RCT null d (p)": f"{r.bs_null_absd:+.3f} ({_p(r.bs_p_bs_absd)})",
                     "cluster p / LOO": f"{_p(r.clp_absd)} ({r.clk_absd}) / {_p(r.loo_absd)}",
                     "vs shuf / noise p": f"{r.d_shuf_absd:+.3f} ({_p(r.p_shuf_absd)}) / {r.d_noise_absd:+.3f} ({_p(r.p_noise_absd)})",
                     "z² base→ECG": f"{r.base_z2:.2f}→{r.ECG_z2:.2f}", "d z² (p)": f"{r.d_z2:+.2f} ({_p(r.p_z2)})",
                     "z² shuffled-RCT p": _p(r.bs_p_bs_z2), "z² cluster p": _p(r.clp_z2),
                     "consistency %": f"{r.base_cons:.0f}→{r.ECG_cons:.0f} (shuf {r.shufECG_cons:.0f})",
                     "estimate agreement %": f"{r.base_est_agree:.0f}→{r.ECG_est_agree:.0f} (shuf {r.shufECG_est_agree:.0f})",
                     "φ": f"{r.base_phi:.2f}→{r.ECG_phi:.2f} (shuf {r.shufECG_phi:.2f})"})
    L += ["## Part 2: trial emulation in the selected scenarios (+ sparse reference)\n",
          "|Δ| = |log HR − RCT log HR| (mean over trials); z² = Δ²/(SE² + SE_RCT²); consistency = % trials with |z| < 1.96; estimate "
          "agreement = % trials whose point estimate lies in the RCT 95% CI; φ = Q/(k−1). Shuffled-RCT null: RCT log HR and SE "
          "permuted jointly across trials (5,000 draws), median null d and one-sided p = P(null d ≤ observed d). Dropout cells: "
          "seed-averaged.\n", md(pd.DataFrame(rows)) + "\n"]
    for scn, g in PT.groupby("scenario", sort=False):
        g = g.copy()
        t = pd.DataFrame({"trial": g.trial, "RCT HR": g.rct_hr.map("{:.2f}".format), "base HR": g.base_hr.map("{:.2f}".format),
                          "+ECG HR": g.ECG_hr.map("{:.2f}".format), "+shufECG HR": g.shufECG_hr.map("{:.2f}".format),
                          "|Δ| base": g.base_absd.map("{:.3f}".format), "|Δ| ECG": g.ECG_absd.map("{:.3f}".format),
                          "ECG closer": np.where(g.ECG_absd < g.base_absd, "yes", "no")})
        L += [f"### Per-trial estimates: {scn} (full cohort)\n", md(t) + "\n"]
    # full grid, primary metric
    for panel, pl in (("p58", "58-panel"), ("xo", "expanded non-ECG-proximal panel")):
        for sub in ("all", "phys"):
            rows = []
            for c in CELLS:
                d = {"cell": cell_label(c)}
                for h in ("full", "A", "B"):
                    r = G[(G.cell == c) & (G.subset == sub) & (G.half == h)].iloc[0]
                    d[f"{h} base→ECG"] = f"{r[f'base_{panel}_pct_lt10']:.1f}→{r[f'ecg_{panel}_pct_lt10']:.1f}"
                    d[f"{h} d (k, p)"] = f"{_f(r[f'd_{panel}_pct_lt10'])} ({r[f'k_{panel}_pct_lt10']}, {_p(r[f'p_{panel}_pct_lt10'])})"
                r = G[(G.cell == c) & (G.subset == sub) & (G.half == "full")].iloc[0]
                d["full q"] = _p(r[f"q_{panel}_pct_lt10"])
                d["full q global"] = _p(r[f"q_global_lt10_{panel}"])
                d["shuf−base / noise−base d"] = f"{_f(r[f'd_shufbase_{panel}_pct_lt10'])} / {_f(r[f'd_noisebase_{panel}_pct_lt10'])}"
                d["ECG−shuf / ECG−noise p"] = f"{_p(r[f'p_shuf_{panel}_pct_lt10'])} / {_p(r[f'p_noise_{panel}_pct_lt10'])}"
                if panel == "p58":
                    d["love unm/base→ECG"] = f"{r.love_unmatched}/{r.love_base}→{r.love_ECG}"
                    d["cluster p / LOO"] = f"{_p(r.clp_p58_pct_lt10)} / {_p(r.loo_p58_pct_lt10)}"
                else:
                    d["cluster p / LOO"] = f"{_p(r.clp_xo_pct_lt10)} / {_p(r.loo_xo_pct_lt10)}"
                rows.append(d)
            L += [f"## Grid: % of held-out variables with |SMD| < 0.1, {pl}, {'all 18 trials' if sub == 'all' else f'{len(PHYS)} physiology trials'}\n",
                  "q = BH over cells within half × subset × panel; q global = BH over cells × both panels (within half, subset).\n",
                  md(pd.DataFrame(rows)) + "\n"]
    # other thresholds, full grid (full cohort, all trials)
    rows = []
    for c in CELLS:
        r = G[(G.cell == c) & (G.subset == "all") & (G.half == "full")].iloc[0]
        d = {"cell": cell_label(c)}
        for m in ("p58_pct_lt05", "p58_pct_gt20", "p58_max_smd", "p58_keyphys_all", "xo_pct_gt20", "xo_max_smd"):
            k = 100 if m.endswith("keyphys_all") else 1
            nd = 3 if "max" in m else 1
            d[m] = f"{r[f'base_{m}'] * k:.{nd}f}→{r[f'ecg_{m}'] * k:.{nd}f} ({_p(r[f'p_{m}'])})"
        rows.append(d)
    L += ["## Grid: other threshold metrics (full cohort, 18 trials; base → ECG, sign-flip p)\n", md(pd.DataFrame(rows)) + "\n"]
    # engine metrics
    rows = []
    for c in CELLS:
        d = {"cell": cell_label(c)}
        for m in ("absd", "z2", "mean_smd", "cstat"):
            r = G[(G.cell == c) & (G.subset == "all") & (G.half == "full")].iloc[0]
            nd = 2 if m == "z2" else 3
            d[f"{m} full d (p)"] = f"{r[f'd_{m}']:+.{nd}f} ({_p(r[f'p_{m}'])})"
            d[f"{m} A/B p"] = "/".join(_p(G[(G.cell == c) & (G.subset == "all") & (G.half == h)].iloc[0][f"p_{m}"]) for h in ("A", "B"))
        r = G[(G.cell == c) & (G.subset == "all") & (G.half == "full")].iloc[0]
        d["|Δ| q"] = _p(r.q_absd)
        d["|Δ| vs shuf/noise p"] = f"{_p(r.p_shuf_absd)}/{_p(r.p_noise_absd)}"
        e = {role: emu_metrics(emu_trial(df, c, "full", role, E.TRIALS)) for role in ("base", "ECG")}
        d["consistency % base→ECG"] = f"{e['base']['cons']:.0f}→{e['ECG']['cons']:.0f}"
        d["φ base→ECG"] = f"{e['base']['phi']:.2f}→{e['ECG']['phi']:.2f}"
        rows.append(d)
    L += ["## Grid: engine metrics (ECG − base, 18 trials; standard sweep summary)\n",
          "Heat map: `docs/v16/S8_HEADLINE_heatmap.png`.\n", md(pd.DataFrame(rows)) + "\n"]
    L += ["## Figures\n", "- `docs/v16/S8_THRESHOLD_grid.png`: ECG gain in % < 0.1 across the grid.\n",
          "- `docs/v16/S8_HEADLINE_heatmap.png`: engine metrics.\n"] + [f"- `docs/v16/{f}`\n" for f in figs]
    af = OUT / "audit.md"
    L += ["## Audit\n", audit_checks(df), af.read_text() if af.exists() else ""]
    # placebo null summary across the grid
    g = G[(G.half == "full") & (G.subset == "all")]
    L += [f"**(3) Placebo − base across the {len(g)} cells** (full, 18 trials, % < 0.1, 58-panel): shufECG − base mean "
          f"{g.d_shufbase_p58_pct_lt10.mean():+.2f} pp (p<0.05 better in {int(((g.p_shufbase_p58_pct_lt10 < 0.05) & (g.d_shufbase_p58_pct_lt10 > 0)).sum())}, "
          f"worse in {int(((g.p_shufbase_p58_pct_lt10 < 0.05) & (g.d_shufbase_p58_pct_lt10 < 0)).sum())}); noise − base mean "
          f"{g.d_noisebase_p58_pct_lt10.mean():+.2f} pp (better {int(((g.p_noisebase_p58_pct_lt10 < 0.05) & (g.d_noisebase_p58_pct_lt10 > 0)).sum())}, "
          f"worse {int(((g.p_noisebase_p58_pct_lt10 < 0.05) & (g.d_noisebase_p58_pct_lt10 < 0)).sum())}); ECG − base mean {g.d_p58_pct_lt10.mean():+.2f} pp "
          f"(better {int(((g.p_p58_pct_lt10 < 0.05) & (g.d_p58_pct_lt10 > 0)).sum())}, worse {int(((g.p_p58_pct_lt10 < 0.05) & (g.d_p58_pct_lt10 < 0)).sum())}).\n"]
    (DOCS / "S8_HEADLINE.md").write_text("\n".join(L))
    df.to_csv(OUT / "results.csv", index=False)
    print("report written")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["run", "select", "summarize", "audit"])
    ap.add_argument("--halves", default="A")
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--cells", default=None)
    a = ap.parse_args()
    if a.mode == "run":
        global CELLS
        if a.cells:
            CELLS = a.cells.split(",")
        hv = a.halves.split(",")
        run(a.trials.split(","), hv, a.workers, a.tag or "_".join(hv))
    elif a.mode == "select":
        select()
    elif a.mode == "summarize":
        report()


if __name__ == "__main__":
    main()
