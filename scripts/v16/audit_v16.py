#!/usr/bin/env python
"""Independent audit of the v1.6 sweeps (S1, S3, S4; S2 if present). Exploratory QA, aggregates only.

Deliberately does NOT reuse the sweep scripts' summary code (own sign-flip, own BH, own pairing).
Part A (csv): recomputation, placebo null, halves A+B vs full, benchmark-regression test of the S4
  meta-regression, global BH-FDR and effective number of cells, leave-one-trial-out / clustered tests,
  pair counts.
Part B (restricted data, in memory): placebo permutation validity, split-half validity, roster person
  overlap between trials, C-statistic / SMD subsampling test (base matched set thinned to the ECG pair count).

  python audit_v16.py a          # writes OUT/*.csv, prints aggregates
  python audit_v16.py b [--workers 18]
Outputs: /mnt/raid0/rbc58/ecg-tte/audits/claude-v16-audit/ (umask 077).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import itertools  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from functools import lru_cache  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = A / "claude-v16-audit"
HERE = Path(__file__).resolve().parent
TRIALS = ["comet", "paradigm-hf-seq", "transform-hf", "elite-ii", "life", "plato", "aristotle", "rocket-af", "rely",
          "allhat", "emperor-preserved-v2", "east-afnet4", "cabana-v2", "ontarget", "value", "ascot", "empa-reg", "carolina"]
# clusters of trials that share a clinical question / comparator arm (and potentially patients)
CLUSTER = {"aristotle": "DOAC-vs-warfarin", "rocket-af": "DOAC-vs-warfarin", "rely": "DOAC-vs-warfarin",
           "emperor-preserved-v2": "SGLT2-vs-DPP4", "empa-reg": "SGLT2-vs-DPP4",
           "elite-ii": "ARB-vs-ACEi", "ontarget": "ARB-vs-ACEi",
           "east-afnet4": "AF-rhythm", "cabana-v2": "AF-rhythm",
           "allhat": "HTN", "value": "HTN", "ascot": "HTN", "life": "HTN",
           "comet": "comet", "paradigm-hf-seq": "paradigm", "transform-hf": "transform", "plato": "plato", "carolina": "carolina"}


# ---------------------------------------------------------------- own statistics
@lru_cache(None)
def _signs(k):
    return np.array(list(itertools.product((-1.0, 1.0), repeat=k)))


def sflip(d):
    """Exact two-sided sign-flip p for mean(d) (own implementation)."""
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    k = len(d)
    if k == 0:
        return np.nan
    if k > 20:
        rng = np.random.default_rng(1)
        S = rng.choice([-1.0, 1.0], size=(200000, k))
    else:
        S = _signs(k)
    null = np.abs(S @ np.abs(d)) / k
    return float(np.mean(null >= abs(d.mean()) - 1e-12))


def bh(p):
    p = np.asarray(p, float)
    q = np.full(p.shape, np.nan)
    ok = np.isfinite(p)
    x = p[ok]
    m = len(x)
    if not m:
        return q
    o = np.argsort(x)
    r = x[o] * m / (np.arange(m) + 1)
    r = np.minimum(1, np.minimum.accumulate(r[::-1])[::-1])
    y = np.empty(m)
    y[o] = r
    q[ok] = y
    return q


def metric(x, m):
    if m == "absd":
        return (x.loghr - x.rb).abs()
    if m == "z2":
        return (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2)
    return x[m]


def per_trial_diff(g, a, b, m, role="arm_role"):
    xa = g[g[role] == a].drop_duplicates("trial").set_index("trial")
    xb = g[g[role] == b].drop_duplicates("trial").set_index("trial")
    tt = xa.index.intersection(xb.index)
    return (metric(xa.loc[tt], m) - metric(xb.loc[tt], m)).dropna()


def stat(d):
    d = pd.Series(d).dropna()
    return dict(d=float(d.mean()) if len(d) else np.nan, k=f"{int((d < 0).sum())}/{len(d)}", p=sflip(d.to_numpy()))


# ---------------------------------------------------------------- loading
def load():
    s1 = pd.read_csv(A / "claude-v16-s1-ladder/results.csv", low_memory=False)
    s1["mean_smd_new4"] = s1[[f"smdnew:{v}" for v in ("tobacco_ever", "obesity", "frailty_count", "prior_hf_hosp_365")]].mean(1)
    s3 = pd.read_csv(A / "claude-v16-s3-repr/results.csv", low_memory=False)
    s4 = pd.read_csv(A / "claude-v16-s4-subgroups/results.csv", low_memory=False)
    s4 = s4[s4.loghr.notna()]
    s2p = A / "claude-v16-s2-dropout/results.csv"
    s2 = pd.read_csv(s2p, low_memory=False) if s2p.exists() else None
    return s1, s3, s4, s2


def conf_sets(s4):
    u = s4[(s4.stratum == "lag<=365 (all)") & (s4.half == "full") & (s4.arm_role == "unmatched") & (s4.base == "sparse")]
    u = u.drop_duplicates("trial").set_index("trial")
    conf = (u.loghr - u.rb).abs()
    q = pd.qcut(conf.rank(method="first"), 3, labels=False)
    return conf, {j: list(q[q == j].index) for j in range(3)}


# ---------------------------------------------------------------- check 1
def check1(s1, s3, s4):
    rows = []
    ref1 = pd.read_csv(A / "claude-v16-s1-ladder/summary_pairs.csv")
    for cell in ("r1_demo", "r3_min7", "r5_sparse", "r7_hdPS200", "r8_clinical", "r0_none"):
        g = s1[(s1.cell == cell) & (s1.half == "full")]
        for m in ("absd", "z2", "mean_smd", "cstat", "mean_smd_new4"):
            s = stat(per_trial_diff(g, "ECG", "base", m))
            r = ref1[(ref1.cell == cell) & (ref1.half == "full") & (ref1.arm_b == "base")].iloc[0]
            rows.append(dict(sweep="S1", cell=cell, metric=m, **s, d_rep=r[f"d_{m}"], k_rep=r[f"k_{m}"], p_rep=r[f"p_{m}"]))
    ref3 = pd.read_csv(A / "claude-v16-s3-repr/summary_pairs.csv")
    for cell in ("3a|demo|pc32", "3a|sparse|pc32", "3a|sparse|pc64", "3a|demo|pc64", "3c|sparse|overlap", "3c|sparse|match0.2x3",
                 "3b|sparse|l2C=0.01"):
        g = s3[(s3.cell == cell) & (s3.half == "full")]
        for m in ("absd", "z2", "mean_smd", "cstat"):
            s = stat(per_trial_diff(g, "ECG", "base", m))
            r = ref3[(ref3.cell == cell) & (ref3.half == "full") & (ref3.comp == "ECG-base")].iloc[0]
            rows.append(dict(sweep="S3", cell=cell, metric=m, **s, d_rep=r[f"d_{m}"], k_rep=r[f"k_{m}"], p_rep=r[f"p_{m}"]))
    ref4 = pd.read_csv(A / "claude-v16-s4-subgroups/summary.csv")
    conf, T3 = conf_sets(s4)
    base_all = s4[(s4.stratum == "lag<=365 (all)") & (s4.half == "full")]
    specs = [("demo||unadj-RCT| T3 (high)", base_all[(base_all.base == "demo") & base_all.trial.isin(T3[2])]),
             ("sparse||unadj-RCT| T3 (high)", base_all[(base_all.base == "sparse") & base_all.trial.isin(T3[2])])]
    for c in ("demo|echo=no", "sparse|echo=no", "demo|echo=yes", "sparse|lag<=365 (all)", "demo|lag<=30"):
        specs.append((c, s4[(s4.cell == c) & (s4.half == "full")]))
    for cell, g in specs:
        for m in ("absd", "z2", "mean_smd", "cstat"):
            s = stat(per_trial_diff(g, "ECG", "base", m))
            r = ref4[(ref4.cell == cell) & (ref4.half == "full")].iloc[0]
            rows.append(dict(sweep="S4", cell=cell, metric=m, **s, d_rep=r[f"d_{m}_base"], k_rep=r[f"k_{m}_base"], p_rep=r[f"p_{m}_base"]))
    R = pd.DataFrame(rows)
    R["abs_dev_d"] = (R.d - R.d_rep).abs()
    R["abs_dev_p"] = (R.p - R.p_rep).abs()
    R["k_match"] = R.k == R.k_rep
    R.to_csv(OUT / "check1_recompute.csv", index=False)
    # S1 vs S3 vs S4 default-cell cross-consistency (same design run in three sweeps)
    X = []
    for base, c1, c3, c4 in (("demo", "r1_demo", "3a|demo|pc32", "demo|lag<=365 (all)"), ("sparse", "r5_sparse", "3a|sparse|pc32", "sparse|lag<=365 (all)")):
        a = s1[(s1.cell == c1) & (s1.half == "full")].set_index(["trial", "arm_role"])
        b = s3[(s3.cell == c3) & (s3.half == "full")].set_index(["trial", "arm_role"])
        c = s4[(s4.cell == c4) & (s4.half == "full") & (s4.arm_role != "unmatched")].set_index(["trial", "arm_role"])
        ix = a.index.intersection(b.index)
        ix4 = a.index.intersection(c.index)
        X.append(dict(base=base, rows_s1_s3=len(ix), max_dloghr_s1_s3=float((a.loc[ix].loghr - b.loc[ix].loghr).abs().max()),
                      max_dsmd_s1_s3=float((a.loc[ix].mean_smd - b.loc[ix].mean_smd).abs().max()),
                      rows_s1_s4=len(ix4), rows_s1=len(a), max_dloghr_s1_s4=float((a.loc[ix4].loghr - c.loc[ix4].loghr).abs().max()),
                      max_dsmd_s1_s4=float((a.loc[ix4].mean_smd - c.loc[ix4].mean_smd).abs().max())))
    X = pd.DataFrame(X)
    X.to_csv(OUT / "check1_cross_sweep.csv", index=False)
    return R, X


# ---------------------------------------------------------------- unified long table of per-trial ECG-base diffs
def cell_frames(s1, s3, s4, s2=None, half="full"):
    """yield (sweep, cell, frame with arm_role, trial, loghr, se, rb, rs, metrics) for all cells at the given half."""
    out = []
    for cell in s1.cell.unique():
        if cell == "unmatched":
            continue
        out.append(("S1", cell, s1[(s1.cell == cell) & (s1.half == half)]))
    for cell in s3[s3.family != "ref"].cell.unique():
        out.append(("S3", cell, s3[(s3.cell == cell) & (s3.half == half)]))
    conf, T = conf_sets(s4)
    for cell in s4.cell.unique():
        out.append(("S4", cell, s4[(s4.cell == cell) & (s4.half == half)]))
    base_all = s4[(s4.stratum == "lag<=365 (all)") & (s4.half == half)]
    for base in ("demo", "sparse"):
        for j, lab in enumerate(("T1 (low)", "T2", "T3 (high)")):
            out.append(("S4", f"{base}||unadj-RCT| {lab}", base_all[(base_all.base == base) & base_all.trial.isin(T[j])]))
    if s2 is not None and "cell" in s2 and "arm_role" in s2:
        hc = "half" if "half" in s2 else None
        for cell in s2.cell.dropna().unique():
            g = s2[s2.cell == cell]
            if hc:
                g = g[g[hc] == half]
            if "seed" in g:
                g = g[g.seed == g.seed.min()]
            out.append(("S2", cell, g))
    return out


BAL = ("mean_smd", "cstat")
METRICS = ("absd", "z2", "mean_smd", "cstat")


def diff_long(frames, a="ECG", b="base"):
    L = []
    for sw, cell, g in frames:
        if not len(g) or a not in set(g.arm_role) or b not in set(g.arm_role):
            continue
        for m in METRICS:
            if m not in g and m not in ("absd", "z2"):
                continue
            d = per_trial_diff(g, a, b, m)
            for t, v in d.items():
                L.append(dict(sweep=sw, cell=cell, metric=m, trial=t, diff=v))
    return pd.DataFrame(L)


# ---------------------------------------------------------------- check 3: placebo null
def check3(s1, s3, s4, s2):
    fr = cell_frames(s1, s3, s4, s2)
    rows = []
    for a, b in (("ECG", "base"), ("shufECG", "base"), ("noise", "base")):
        D = diff_long(fr, a, b)
        C = D.groupby(["sweep", "cell", "metric"])["diff"].agg(["mean", "count"]).reset_index()
        C["p"] = [sflip(D[(D.sweep == r.sweep) & (D.cell == r.cell) & (D.metric == r.metric)]["diff"].to_numpy()) for r in C.itertuples()]
        C["contrast"] = f"{a}-base"
        rows.append(C)
    C = pd.concat(rows, ignore_index=True)
    C.to_csv(OUT / "check3_cell_contrasts.csv", index=False)
    S = []
    for (con, m), g in C.groupby(["contrast", "metric"]):
        S.append(dict(contrast=con, metric=m, n_cells=len(g), mean_d=g["mean"].mean(), median_d=g["mean"].median(),
                      frac_neg=(g["mean"] < 0).mean(), frac_p05_better=((g.p < 0.05) & (g["mean"] < 0)).mean(),
                      frac_p05_worse=((g.p < 0.05) & (g["mean"] > 0)).mean()))
    S = pd.DataFrame(S)
    # standardise placebo effect relative to ECG effect per metric
    S.to_csv(OUT / "check3_placebo_null.csv", index=False)
    # pair counts
    P = []
    for sw, cell, g in fr:
        if "n_pairs" not in g or not len(g):
            continue
        piv = g.drop_duplicates(["trial", "arm_role"]).pivot(index="trial", columns="arm_role", values="n_pairs")
        if "base" not in piv or piv["base"].isna().all():
            continue
        for r in ("ECG", "shufECG", "noise"):
            if r in piv:
                ratio = (piv[r] / piv["base"]).dropna()
                if len(ratio):
                    P.append(dict(sweep=sw, cell=cell, role=r, median_ratio=ratio.median(), min_ratio=ratio.min(), frac_fewer=(ratio < 1).mean()))
    P = pd.DataFrame(P)
    P.to_csv(OUT / "check3_pair_ratio.csv", index=False)
    PS = P.groupby(["sweep", "role"]).agg(cells=("cell", "size"), median_ratio=("median_ratio", "median"),
                                          p10=("median_ratio", lambda x: x.quantile(0.1)), min_ratio=("min_ratio", "min"),
                                          frac_trials_fewer=("frac_fewer", "mean")).reset_index()
    PS.to_csv(OUT / "check3_pair_ratio_summary.csv", index=False)
    return S, PS


# ---------------------------------------------------------------- check 4: halves A+B vs full
def check4(s1, s3, s4):
    rows = []
    for sw, df, cellcol in (("S1", s1, "cell"), ("S3", s3[s3.family != "ref"], "cell"), ("S4", s4, "cell")):
        base = df[df.arm_role == "base"].drop_duplicates(["trial", cellcol, "half"])
        piv = base.pivot_table(index=["trial", cellcol], columns="half", values="n_pairs")
        if {"A", "B", "full"} <= set(piv.columns):
            r = ((piv.A + piv.B) / piv.full).dropna()
            rows.append(dict(sweep=sw, what="n_pairs (A+B)/full, base arms", median=r.median(), min=r.min(), max=r.max(), n=len(r)))
        pn = base.pivot_table(index=["trial", cellcol], columns="half", values="n")
        if {"A", "B", "full"} <= set(pn.columns):
            r = ((pn.A + pn.B) / pn.full).dropna()
            rows.append(dict(sweep=sw, what="n (A+B)/full", median=r.median(), min=r.min(), max=r.max(), n=len(r)))
    # agreement of halves with full in sign, per cell x metric (ECG-base)
    for sw_name, fr_full, fr_A, fr_B in (
            ("all", cell_frames(s1, s3, s4, None, "full"), cell_frames(s1, s3, s4, None, "A"), cell_frames(s1, s3, s4, None, "B")),):
        Df, Da, Db = (diff_long(f).groupby(["sweep", "cell", "metric"])["diff"].mean() for f in (fr_full, fr_A, fr_B))
        J = pd.concat([Df.rename("full"), Da.rename("A"), Db.rename("B")], axis=1).dropna()
        J["avgAB"] = (J.A + J.B) / 2
        for m in METRICS:
            j = J.xs(m, level="metric")
            rows.append(dict(sweep="all", what=f"{m}: corr(full, mean(A,B)) over cells", median=float(np.corrcoef(j.full, j.avgAB)[0, 1]),
                             min=float((j.avgAB - j.full).abs().median()), max=float((j.avgAB - j.full).abs().max()), n=len(j)))
            rows.append(dict(sweep="all", what=f"{m}: corr(A, B) over cells", median=float(np.corrcoef(j.A, j.B)[0, 1]), min=np.nan, max=np.nan, n=len(j)))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "check4_halves.csv", index=False)
    return R


# ---------------------------------------------------------------- check 5: regression to the benchmark
def wls_slope(x, y, w):
    Z = np.column_stack([np.ones(len(y)), x])
    sw = np.sqrt(w)
    return np.linalg.lstsq(Z * sw[:, None], y * sw, rcond=None)[0][1]


def perm_p(x, y, w, n=10000, seed=5):
    rng = np.random.default_rng(seed)
    b = wls_slope(x, y, w)
    null = np.array([wls_slope(x[rng.permutation(len(x))], y, w) for _ in range(n)])
    return b, float(np.mean(np.abs(null) >= abs(b) - 1e-12))


def check5(s1, s4):
    al = s4[(s4.stratum == "lag<=365 (all)") & (s4.half == "full")]
    clin = s1[(s1.cell == "r8_clinical") & (s1.half == "full") & (s1.arm_role == "base")].drop_duplicates("trial").set_index("trial")
    unm = al[(al.arm_role == "unmatched") & (al.base == "sparse")].drop_duplicates("trial").set_index("trial")
    rows = []
    for base in ("demo", "sparse"):
        g = al[al.base == base]
        E_ = g[g.arm_role == "ECG"].drop_duplicates("trial").set_index("trial")
        B_ = g[g.arm_role == "base"].drop_duplicates("trial").set_index("trial")
        S_ = g[g.arm_role == "shufECG"].drop_duplicates("trial").set_index("trial")
        tr = B_.index.intersection(E_.index).intersection(unm.index).intersection(clin.index)
        E_, B_, S_, U, Cl = E_.loc[tr], B_.loc[tr], S_.loc[tr], unm.loc[tr], clin.loc[tr]
        rb, rs = B_.rb.to_numpy(), B_.rs.to_numpy()

        def ys(rb_, rs_, arm=E_):
            ya = np.abs(arm.loghr.to_numpy() - rb_) - np.abs(B_.loghr.to_numpy() - rb_)
            yz = (arm.loghr.to_numpy() - rb_) ** 2 / (arm.se.to_numpy() ** 2 + rs_ ** 2) - (B_.loghr.to_numpy() - rb_) ** 2 / (B_.se.to_numpy() ** 2 + rs_ ** 2)
            return dict(absd=ya, z2=yz)
        w = 1 / (B_.se.to_numpy() ** 2 + rs ** 2)
        mods = {"|unadj-RCT| (as S4)": np.abs(U.loghr.to_numpy() - rb),
                "|unadj-clinicalPS| (no RCT)": np.abs(U.loghr.to_numpy() - Cl.loghr.to_numpy()),
                "|unadj-base| (no RCT)": np.abs(U.loghr.to_numpy() - B_.loghr.to_numpy()),
                "|base-RCT|": np.abs(B_.loghr.to_numpy() - rb)}
        Y = ys(rb, rs)
        Ysh = ys(rb, rs, S_)
        for mname, x in mods.items():
            for m in ("absd", "z2"):
                b, p = perm_p(x, Y[m], w)
                bs, ps = perm_p(x, Ysh[m], w, n=4000)
                rows.append(dict(base=base, moderator=mname, metric=m, k=len(tr), slope_per_sd=b * x.std(), perm_p=p,
                                 shuf_slope_per_sd=bs * x.std(), shuf_perm_p=ps))
        # (b) shuffle RCT benchmarks across trials: recompute moderator and outcome with the shuffled benchmark
        rng = np.random.default_rng(55)
        for m in ("absd", "z2"):
            x0 = mods["|unadj-RCT| (as S4)"]
            b0 = wls_slope(x0, Y[m], w) * x0.std()
            null = []
            for _ in range(5000):
                pi = rng.permutation(len(tr))
                rbp, rsp = rb[pi], rs[pi]
                xp = np.abs(U.loghr.to_numpy() - rbp)
                yp = ys(rbp, rsp)[m]
                wp = 1 / (B_.se.to_numpy() ** 2 + rsp ** 2)
                null.append(wls_slope(xp, yp, wp) * xp.std())
            null = np.array(null)
            rows.append(dict(base=base, moderator="RCT-shuffle null (moderator and outcome share shuffled RCT)", metric=m, k=len(tr),
                             slope_per_sd=b0, perm_p=float(np.mean(null <= b0)), shuf_slope_per_sd=float(np.mean(null)),
                             shuf_perm_p=float(np.mean(null < 0)), null_median=float(np.median(null)),
                             null_q05=float(np.quantile(null, 0.05)), null_q95=float(np.quantile(null, 0.95))))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "check5_benchmark_regression.csv", index=False)
    return R


# ---------------------------------------------------------------- check 6: global FDR + effective number
def check6(s1, s3, s4, s2, sfx=""):
    fr = cell_frames(s1, s3, s4, s2)
    D = diff_long(fr)
    D = D[~((D.sweep == "S1") & ~D.metric.isin(METRICS))]
    C = D.groupby(["sweep", "cell", "metric"])["diff"].agg(d="mean", n="count").reset_index()
    C["p"] = [sflip(D[(D.sweep == r.sweep) & (D.cell == r.cell) & (D.metric == r.metric)]["diff"].to_numpy()) for r in C.itertuples()]
    # S1 extra balance metrics (held-out-from-base, new covariates)
    ex = []
    for cell in s1.cell.unique():
        if cell == "unmatched":
            continue
        g = s1[(s1.cell == cell) & (s1.half == "full")]
        for m in ("mean_smd_ho", "cstat_ho", "mean_smd_new", "mean_smd_new4"):
            d = per_trial_diff(g, "ECG", "base", m)
            ex.append(dict(sweep="S1", cell=cell, metric=m, d=d.mean(), n=len(d), p=sflip(d.to_numpy())))
    C = pd.concat([C, pd.DataFrame(ex)], ignore_index=True)
    C = C[C.n >= 6]
    # de-duplicate identical designs (S3 duplicate default cells, S3/S4 copies of S1 demo/sparse default)
    key = C.d.round(10).astype(str) + "|" + C.p.round(10).astype(str) + "|" + C.metric
    C["dup"] = key.duplicated()
    U = C[~C.dup].copy()
    U["q_global"] = bh(U.p)
    U["q_within_metric"] = np.nan
    for m, g in U.groupby("metric"):
        U.loc[g.index, "q_within_metric"] = bh(g.p)
    U.to_csv(OUT / f"check6_global_fdr{sfx}.csv", index=False)
    S = U.groupby(["metric", "sweep"]).agg(cells=("p", "size"), nominal=("p", lambda p: int((p < 0.05).sum())),
                                            nominal_better=("d", lambda d: np.nan)).reset_index()
    S["nominal_better"] = [int(((U.metric == r.metric) & (U.sweep == r.sweep) & (U.p < 0.05) & (U.d < 0)).sum()) for r in S.itertuples()]
    S["global_q05_better"] = [int(((U.metric == r.metric) & (U.sweep == r.sweep) & (U.q_global < 0.05) & (U.d < 0)).sum()) for r in S.itertuples()]
    S["global_q05_worse"] = [int(((U.metric == r.metric) & (U.sweep == r.sweep) & (U.q_global < 0.05) & (U.d > 0)).sum()) for r in S.itertuples()]
    S.to_csv(OUT / f"check6_global_fdr_summary{sfx}.csv", index=False)
    # effective number of independent cells per metric (Li & Ji 2005) from per-trial ECG-base gains
    E_ = []
    Du = D.merge(U[["sweep", "cell", "metric"]], on=["sweep", "cell", "metric"])
    for m, g in Du.groupby("metric"):
        W = g.pivot_table(index="trial", columns=["sweep", "cell"], values="diff")
        W = W.loc[:, W.notna().sum() >= 17].dropna()
        if W.shape[1] < 2:
            continue
        R = np.corrcoef(W.to_numpy().T)
        ev = np.clip(np.linalg.eigvalsh(R), 0, None)
        meff = float(np.sum((ev >= 1).astype(float) + (ev - np.floor(ev))))
        iu = np.triu_indices(R.shape[0], 1)
        E_.append(dict(metric=m, cells=W.shape[1], trials=W.shape[0], median_pairwise_r=float(np.median(R[iu])),
                       q25_r=float(np.quantile(R[iu], 0.25)), q75_r=float(np.quantile(R[iu], 0.75)), meff_liji=meff,
                       top_eig_share=float(ev.max() / ev.sum())))
    E_ = pd.DataFrame(E_)
    E_.to_csv(OUT / f"check6_effective_number{sfx}.csv", index=False)
    return U, S, E_


# ---------------------------------------------------------------- check 7: leave-one-trial-out and clustered
def check7(s1):
    heads = [("r1_demo", "absd"), ("r1_demo", "z2"), ("r5_sparse", "z2"), ("r5_sparse", "mean_smd"), ("r1_demo", "mean_smd"),
             ("r5_sparse", "cstat"), ("r1_demo", "cstat"), ("r7_hdPS200", "mean_smd"), ("r3_min7", "mean_smd"), ("r0_none", "z2")]
    rows = []
    for cell, m in heads:
        g = s1[(s1.cell == cell) & (s1.half == "full")]
        d = per_trial_diff(g, "ECG", "base", m)
        full = stat(d)
        lo = [dict(drop=t, d=d.drop(t).mean(), p=sflip(d.drop(t).to_numpy())) for t in d.index]
        lo = pd.DataFrame(lo)
        worst = lo.loc[lo.p.idxmax()]
        cl = d.groupby(d.index.map(CLUSTER)).mean()
        # drop-one-cluster
        dc = [sflip(d[d.index.map(CLUSTER) != c].to_numpy()) for c in cl.index]
        rows.append(dict(cell=cell, metric=m, d=full["d"], k=full["k"], p=full["p"], loo_d_min=lo.d.min(), loo_d_max=lo.d.max(),
                         loo_p_min=lo.p.min(), loo_p_max=lo.p.max(), loo_worst_drop=worst["drop"], n_loo_p_ge_05=int((lo.p >= 0.05).sum()),
                         cluster_k=len(cl), cluster_d=cl.mean(), cluster_k_better=f"{int((cl < 0).sum())}/{len(cl)}", cluster_p=sflip(cl.to_numpy()),
                         drop_cluster_p_max=max(dc), median_share_top_trial=float(d.abs().max() / d.abs().sum())))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "check7_loo_cluster.csv", index=False)
    return R


def part_a():
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    s1, s3, s4, s2 = load()
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 400)
    r1, x1 = check1(s1, s3, s4)
    print("CHECK1 max|dev d|", r1.abs_dev_d.max(), "max|dev p|", r1.abs_dev_p.max(), "k mismatches", int((~r1.k_match).sum()))
    print(r1[r1.abs_dev_d > 1e-9].to_string())
    print(x1.to_string())
    S3_, PS = check3(s1, s3, s4, None)
    print("CHECK3\n", S3_.to_string(), "\n", PS.to_string())
    print("CHECK4\n", check4(s1, s3, s4).to_string())
    print("CHECK5\n", check5(s1, s4).to_string())
    if s2 is not None:
        U2, S2_, E2 = check6(s1, s3, s4, s2, "_withS2seed0")
        print("CHECK6 with S2 (seed 0)\n", S2_.to_string(), "\n", E2.to_string())
    U, S, E_ = check6(s1, s3, s4, None)
    print("CHECK6\n", S.to_string(), "\n", E_.to_string())
    print(U[(U.q_global < 0.05)].groupby(["metric", "sweep"]).cell.apply(lambda x: ", ".join(x)).to_string())
    print("CHECK7\n", check7(s1).to_string())


# ---------------------------------------------------------------- part B
def _b_trial(n):
    sys.path.insert(0, str(HERE))
    import v16_engine as E
    from v13_common import match, ps_logit
    T = E.load_trial(n)
    i = E.TRIALS.index(n)
    out = {}
    # placebo validity
    p = T.shuffle_perm
    out["perm_is_permutation"] = bool(np.array_equal(np.sort(p), np.arange(len(T.t))))
    out["perm_fixed_points_frac"] = float(np.mean(p == np.arange(len(T.t))))
    out["perm_treat_concord"] = float(np.mean(T.t[p] == T.t))  # expected = pt^2+(1-pt)^2
    pt = T.t.mean()
    out["perm_treat_concord_expected"] = float(pt ** 2 + (1 - pt) ** 2)
    sh = T.ecg_pc[p]
    out["shuf_dim_equal"] = bool(sh.shape == T.ecg_pc.shape)
    out["noise_dim"] = int(T.noise32.shape[1])
    # max |corr| of each shuffled PC with treatment vs real PCs
    cr = lambda M: np.abs([np.corrcoef(M[:, j], T.t)[0, 1] for j in range(M.shape[1])])
    out["max_abs_corr_t_realPC"] = float(cr(T.ecg_pc).max())
    out["max_abs_corr_t_shufPC"] = float(cr(sh).max())
    out["max_abs_corr_t_noise"] = float(cr(T.noise32).max())
    # halves (S1/S3/S4 all use default_rng(16060 + i), stratified)
    rng = np.random.default_rng(16060 + i)
    Aa = []
    for g in (0, 1):
        idx = np.where(T.t == g)[0]
        idx = idx[rng.permutation(len(idx))]
        Aa.append(idx[: len(idx) // 2])
    Ah = np.sort(np.concatenate(Aa))
    Bh = np.setdiff1d(np.arange(len(T.t)), Ah)
    out["halves_disjoint"] = bool(len(np.intersect1d(Ah, Bh)) == 0)
    out["halves_cover"] = bool(len(Ah) + len(Bh) == len(T.t))
    out["half_treat_share_diff"] = float(abs(T.t[Ah].mean() - T.t[Bh].mean()))
    ok = T.y_ok
    ev = T.y_e.astype(float)
    out["half_event_rate_diff"] = float(abs(ev[Ah][ok[Ah]].mean() - ev[Bh][ok[Bh]].mean()))
    # C-stat / SMD subsample test: thin base matched pairs to the ECG pair count (sparse and demo bases)
    bases = {"sparse": np.asarray(T.X_dx, float), "demo": T.cov[T.demo].to_numpy(float)}
    Hv = T.H.to_numpy(float)
    rs = np.random.default_rng(777 + i)
    for bname, Xb in bases.items():
        res = {}
        for arm, X in (("base", Xb), ("ECG", np.hstack([Xb, T.ecg_pc]))):
            lg = ps_logit(X, T.t, model="l2", C=1.0, seed=0)
            s_idx, cl, s_w = match(lg, T.t, cal=0.2, ratio=1)
            res[arm] = (s_idx, cl)
        bi, bcl = res["base"]
        ei, _ = res["ECG"]
        npb, npe = len(bi) // 2, len(ei) // 2
        cb = E.balance_cstat(Hv[bi], T.t[bi], np.ones(len(bi)), seed=0)
        ce = E.balance_cstat(Hv[ei], T.t[ei], np.ones(len(ei)), seed=0)
        smd = lambda idx: float(np.nanmean(E.smd_components(Hv, T.t, idx, np.ones(len(idx)), T.t[idx])))
        sub_c, sub_s = [], []
        anchors = np.unique(bcl)
        for r in range(5):
            keep_a = rs.choice(anchors, size=min(npe, len(anchors)), replace=False)
            kk = np.isin(bcl, keep_a)
            idx = bi[kk]
            sub_c.append(E.balance_cstat(Hv[idx], T.t[idx], np.ones(len(idx)), seed=r))
            sub_s.append(smd(idx))
        # seed variability of the C-statistic folds on the full base set
        cb_seeds = [E.balance_cstat(Hv[bi], T.t[bi], np.ones(len(bi)), seed=s) for s in range(1, 4)]
        out.update({f"{bname}_pairs_base": npb, f"{bname}_pairs_ECG": npe, f"{bname}_c_base": cb, f"{bname}_c_ECG": ce,
                    f"{bname}_c_base_sub": float(np.mean(sub_c)), f"{bname}_c_base_seedsd": float(np.std([cb] + cb_seeds)),
                    f"{bname}_compsmd_base": smd(bi), f"{bname}_compsmd_ECG": smd(ei), f"{bname}_compsmd_base_sub": float(np.mean(sub_s))})
    return n, out


def roster_overlap():
    sys.path.insert(0, str(HERE.parent))
    from v13_common import EXTRA, PRIMARY
    P = {}
    for n in TRIALS:
        cdir = {**PRIMARY, **EXTRA}[n][1]
        P[n] = set(pd.read_parquet(A / cdir / "restricted_cohort.parquet", columns=["person_id"]).person_id.astype("int64"))
    rows = []
    for a, b in itertools.combinations(TRIALS, 2):
        inter = len(P[a] & P[b])
        if inter == 0:
            continue
        rows.append(dict(a=a, b=b, pct_of_smaller=round(100 * inter / min(len(P[a]), len(P[b])), 1), same_cluster=CLUSTER[a] == CLUSTER[b],
                         overlap_ge_11=inter >= 11))
    R = pd.DataFrame(rows).sort_values("pct_of_smaller", ascending=False)
    R = R[R.overlap_ge_11].drop(columns="overlap_ge_11")
    return R


def part_b(workers=18):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(min(workers, 18)) as p:
        res = p.map(_b_trial, TRIALS, chunksize=1)
    B = pd.DataFrame([dict(trial=n, **o) for n, o in res])
    B.to_csv(OUT / "partb_trials.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 60)
    print(B.T.to_string())
    for b in ("sparse", "demo"):
        dc = B[f"{b}_c_ECG"] - B[f"{b}_c_base"]
        dsub = B[f"{b}_c_base_sub"] - B[f"{b}_c_base"]
        dcs = B[f"{b}_c_ECG"] - B[f"{b}_c_base_sub"]
        ds = B[f"{b}_compsmd_ECG"] - B[f"{b}_compsmd_base"]
        dss = B[f"{b}_compsmd_ECG"] - B[f"{b}_compsmd_base_sub"]
        print(b, "pairs ECG/base median", float((B[f"{b}_pairs_ECG"] / B[f"{b}_pairs_base"]).median()),
              "| C: ECG-base", round(dc.mean(), 4), sflip(dc), "| sub-base", round(dsub.mean(), 4), sflip(dsub),
              "| ECG-sub", round(dcs.mean(), 4), sflip(dcs), "| seed sd median", round(B[f"{b}_c_base_seedsd"].median(), 4),
              "| compSMD ECG-base", round(ds.mean(), 4), sflip(ds), "ECG-sub", round(dss.mean(), 4), sflip(dss))
    R = roster_overlap()
    R.to_csv(OUT / "partb_roster_overlap.csv", index=False)
    print(R.head(40).to_string())


# ---------------------------------------------------------------- supplements (run: audit_v16.py c)
def check5b(s1, s4, nperm=5000):
    """No-RCT moderator |unadj - clinical PS|; null = shuffle RCT benchmarks across trials in the OUTCOME only."""
    al = s4[(s4.stratum == "lag<=365 (all)") & (s4.half == "full")]
    clin = s1[(s1.cell == "r8_clinical") & (s1.half == "full") & (s1.arm_role == "base")].drop_duplicates("trial").set_index("trial")
    unm = al[(al.arm_role == "unmatched") & (al.base == "sparse")].drop_duplicates("trial").set_index("trial")
    rows = []
    for base in ("demo", "sparse"):
        g = al[al.base == base]
        for arm in ("ECG", "shufECG", "noise"):
            E_ = g[g.arm_role == arm].drop_duplicates("trial").set_index("trial")
            B_ = g[g.arm_role == "base"].drop_duplicates("trial").set_index("trial")
            tr = B_.index.intersection(E_.index).intersection(unm.index).intersection(clin.index)
            E_, B_, U, Cl = E_.loc[tr], B_.loc[tr], unm.loc[tr], clin.loc[tr]
            rb, rs = B_.rb.to_numpy(), B_.rs.to_numpy()
            x = np.abs(U.loghr.to_numpy() - Cl.loghr.to_numpy())
            le, lb, se_e, se_b = E_.loghr.to_numpy(), B_.loghr.to_numpy(), E_.se.to_numpy(), B_.se.to_numpy()
            def y(rb_, rs_, m):
                if m == "absd":
                    return np.abs(le - rb_) - np.abs(lb - rb_)
                return (le - rb_) ** 2 / (se_e ** 2 + rs_ ** 2) - (lb - rb_) ** 2 / (se_b ** 2 + rs_ ** 2)
            rng = np.random.default_rng(56)
            for m in ("absd", "z2"):
                w = 1 / (se_b ** 2 + rs ** 2)
                b0 = wls_slope(x, y(rb, rs, m), w) * x.std()
                null = []
                for _ in range(nperm):
                    pi = rng.permutation(len(tr))
                    null.append(wls_slope(x, y(rb[pi], rs[pi], m), 1 / (se_b ** 2 + rs[pi] ** 2)) * x.std())
                null = np.array(null)
                # movement toward/away: correlation of |ECG shift| with moderator (no RCT at all)
                shift = np.abs(le - lb)
                rows.append(dict(base=base, arm=arm, metric=m, k=len(tr), slope_per_sd=b0, null_median=float(np.median(null)),
                                 null_q05=float(np.quantile(null, 0.05)), p_one_sided=float(np.mean(null <= b0)),
                                 corr_absshift_moderator=float(np.corrcoef(shift, x)[0, 1])))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "check5b_noRCT_moderator_outcome_shuffle.csv", index=False)
    return R


def part_c():
    os.umask(0o077)
    s1, s3, s4, s2 = load()
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 400)
    print(check5b(s1, s4).to_string())
    U = pd.read_csv(OUT / "check6_global_fdr.csv")
    for m, g in U.groupby("metric"):
        k = g[(g.q_within_metric < 0.05) & (g.d < 0)]
        print(f"[within-metric global BH] {m}: {len(k)}/{len(g)} cells q<0.05:", "; ".join(f"{r.sweep}:{r.cell}" for r in k.itertuples()) if m in ("absd", "z2") else "")
    for m in ("absd", "z2"):
        g = U[U.metric == m].sort_values("p").head(8)
        print(g[["sweep", "cell", "d", "n", "p", "q_global", "q_within_metric"]].to_string())


def check11(s1, s3, s4, nperm=5000):
    """Benchmark specificity: ECG-base gain in |dlogHR| and z2 with the true RCT vs RCT benchmarks shuffled across
    trials (derangement-free permutations). Also: does ECG move log HR toward 0 (shrinkage) or toward the RCT?"""
    cells = [("S1", "r0_none", s1), ("S1", "r1_demo", s1), ("S1", "r3_min7", s1), ("S1", "r5_sparse", s1), ("S1", "r7_hdPS50", s1),
             ("S1", "r7_hdPS200", s1), ("S3", "3a|demo|pc64", s3), ("S3", "3c|sparse|overlap", s3), ("S3", "3c|sparse|match0.2x3", s3),
             ("S3", "3a|demo|raw256", s3)]
    rows = []
    rng = np.random.default_rng(1111)
    for sw, cell, df in cells:
        g = df[(df.cell == cell) & (df.half == "full")]
        E_ = g[g.arm_role == "ECG"].drop_duplicates("trial").set_index("trial")
        B_ = g[g.arm_role == "base"].drop_duplicates("trial").set_index("trial")
        tr = E_.index.intersection(B_.index)
        E_, B_ = E_.loc[tr], B_.loc[tr]
        le, lb, se_e, se_b, rb, rs = (E_.loghr.to_numpy(), B_.loghr.to_numpy(), E_.se.to_numpy(), B_.se.to_numpy(),
                                      B_.rb.to_numpy(), B_.rs.to_numpy())
        ok = np.isfinite(le) & np.isfinite(lb)
        le, lb, se_e, se_b, rb, rs = le[ok], lb[ok], se_e[ok], se_b[ok], rb[ok], rs[ok]
        fa = lambda r_: np.mean(np.abs(le - r_) - np.abs(lb - r_))
        fz = lambda r_, s_: np.mean((le - r_) ** 2 / (se_e ** 2 + s_ ** 2) - (lb - r_) ** 2 / (se_b ** 2 + s_ ** 2))
        na, nz = [], []
        for _ in range(nperm):
            pi = rng.permutation(len(rb))
            na.append(fa(rb[pi]))
            nz.append(fz(rb[pi], rs[pi]))
        na, nz = np.array(na), np.array(nz)
        toward0 = np.mean(np.abs(le) < np.abs(lb))
        towardR = np.mean(np.abs(le - rb) < np.abs(lb - rb))
        # decomposition: does the ECG shift correlate with (RCT - base)? and with (0 - base)?
        sh = le - lb
        rows.append(dict(sweep=sw, cell=cell, k=int(ok.sum()), d_absd=fa(rb), null_absd_median=float(np.median(na)),
                         p_absd_benchmark_specific=float(np.mean(na <= fa(rb))), d_z2=fz(rb, rs), null_z2_median=float(np.median(nz)),
                         p_z2_benchmark_specific=float(np.mean(nz <= fz(rb, rs))), frac_shift_toward_null=toward0,
                         frac_shift_toward_RCT=towardR, corr_shift_with_RCTminusBase=float(np.corrcoef(sh, rb - lb)[0, 1]),
                         corr_shift_with_minusBase=float(np.corrcoef(sh, -lb)[0, 1]),
                         mean_abs_loghr_base=float(np.mean(np.abs(lb))), mean_abs_loghr_ECG=float(np.mean(np.abs(le))),
                         mean_abs_rb=float(np.mean(np.abs(rb)))))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "check11_benchmark_specificity.csv", index=False)
    return R


def part_d():
    os.umask(0o077)
    s1, s3, s4, s2 = load()
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(check11(s1, s3, s4).to_string())


if __name__ == "__main__":
    if sys.argv[1] == "a":
        part_a()
    elif sys.argv[1] == "d":
        part_d()
    elif sys.argv[1] == "c":
        part_c()
    else:
        part_b()
