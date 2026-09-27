#!/usr/bin/env python
"""v1.6 sweep S4: populations / effect modifiers (docs/V16_SWEEP_PLAN.md, exploratory).

Bases: demo and sparse, ECG = 32 BCL PCs, default estimator (1:1 caliper-0.2 matching, L2 C=1 PS,
l2 C-statistic). Arms per base: base, base+ECG, base+shufECG (T.shuffle_perm rows), base+noise32;
unmatched once per trial x stratum x half. PS is re-fitted and matching redone within each stratum
(run_cell rows=).

Row strata (per trial): all (= ECG lag <= 365 d), ECG lag <= 30 d / <= 90 d (lag from the trial's ECG
selection file <bcl dir>/input/restricted_selection.parquet), echo available (T.echo_any & T.post2016)
vs not, code-density tertile (T.density, tertiles within trial), age < 65 / >= 65, sex, care setting at
index (inpatient = index date inside an OMOP gold inpatient visit 9201, as scripts/make_outpatient_subset.py).
Minimum size: a trial x stratum is skipped if either arm < 100 (full) or < 50 (each half).
Trial-level strata (no re-run; subsets of the 18 trials at stratum 'all'): role, blinded closeness,
unmatched confounding tertile, trial-size tertile. Plus a trial-level meta-regression.

Usage:  python s4_subgroups.py prep            # restricted per-trial flags (lag, inpatient) in OUT
        python s4_subgroups.py run [--trials a,b] [--workers 32] [--tag audit]
        python s4_subgroups.py summarize [--tag ...]
Aggregates only in results/summaries; counts 1-10 suppressed.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import v16_engine as E  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, paths  # noqa: E402
from v13_summarize import md, sign_flip  # noqa: E402

SWEEP = "s4-subgroups"
OUT = A / f"claude-v16-{SWEEP}"
DOCS = HERE.parent.parent / "docs" / "v16"
BASES = ("demo", "sparse")
ROLES = ("base", "ECG", "shufECG", "noise")
METRICS = ("absd", "z2", "mean_smd", "cstat")
MIN_ARM, MIN_ARM_HALF, MIN_TRIALS = 100, 50, 6
ROW_STRATA = [("recency", "lag<=365 (all)"), ("recency", "lag<=90"), ("recency", "lag<=30"),
              ("echo", "echo=yes"), ("echo", "echo=no"),
              ("density", "density=T1 (low)"), ("density", "density=T2"), ("density", "density=T3 (high)"),
              ("age", "age<65"), ("age", "age>=65"), ("sex", "sex=female"), ("sex", "sex=male"),
              ("setting", "setting=outpatient"), ("setting", "setting=inpatient")]
ALL = "lag<=365 (all)"


# ---------------------------------------------------------------- prep: lag + inpatient flags
def prep(trials):
    import duckdb
    from trial_common import rp
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET threads=16")
    agg = []
    for n in trials:
        cdir = {**PRIMARY, **EXTRA}[n][1]
        coh = pd.read_parquet(f"{A}/{cdir}/restricted_cohort.parquet")[["patient_key", "person_id", "index_date"]]
        sel = pd.read_parquet(Path(paths(n)["ecg"]).parent / "input" / "restricted_selection.parquet")
        con.register("c", coh)
        ip = con.execute(f"""SELECT DISTINCT c.patient_key FROM c JOIN {rp('/mnt/raid0/rbc58/omop/gold', 'visit_occurrence')} v
            ON v.person_id = c.person_id AND v.visit_concept_id = 9201
            AND CAST(c.index_date AS DATE) BETWEEN v.visit_start_date AND coalesce(v.visit_end_date, v.visit_start_date)""").df()
        con.unregister("c")
        f = coh[["patient_key"]].drop_duplicates().copy()
        f["inpatient_index"] = f.patient_key.isin(set(ip.patient_key))
        f = f.merge(sel.drop_duplicates("patient_key")[["patient_key", "lag_days"]], on="patient_key", how="left")
        f.to_parquet(OUT / f"restricted_flags_{n}.parquet", index=False)
        agg.append(dict(trial=n, pct_inpatient_index=round(100 * f.inpatient_index.mean(), 1),
                        pct_lag_known=round(100 * f.lag_days.notna().mean(), 1)))
        print(agg[-1], flush=True)
    pd.DataFrame(agg).to_csv(OUT / "prep_flags_summary.csv", index=False)


# ---------------------------------------------------------------- strata
def halves(T, i):
    rng = np.random.default_rng(16060 + i)
    h = np.zeros(len(T.t), dtype="U1")
    for a in (0, 1):
        idx = np.where(T.t == a)[0]
        idx = idx[rng.permutation(len(idx))]
        h[idx[: len(idx) // 2]] = "A"
        h[idx[len(idx) // 2:]] = "B"
    return h


def strata_masks(T):
    F = pd.read_parquet(OUT / f"restricted_flags_{T.n}.parquet").set_index("patient_key").reindex(T.keys)
    lag = F.lag_days.to_numpy(float)
    inp = F.inpatient_index.fillna(False).to_numpy(bool)
    dens = pd.Series(T.density).rank(method="average")
    tert = pd.qcut(dens, 3, labels=False).to_numpy()
    age = T.cov["age_at_index"].to_numpy(float)
    male = T.cov["male"].to_numpy(float) > 0.5
    echo = np.asarray(T.echo_any, bool) & np.asarray(T.post2016, bool)
    n = len(T.t)
    M = {ALL: np.ones(n, bool), "lag<=90": lag <= 90, "lag<=30": lag <= 30,
         "echo=yes": echo, "echo=no": ~echo,
         "density=T1 (low)": tert == 0, "density=T2": tert == 1, "density=T3 (high)": tert == 2,
         "age<65": age < 65, "age>=65": age >= 65, "sex=female": ~male, "sex=male": male,
         "setting=outpatient": ~inp, "setting=inpatient": inp}
    info = dict(lag_known=float(np.isfinite(lag).mean()), inp=float(inp.mean()))
    return M, info


def base_X(T, base, rows):
    return T.cov[T.demo].to_numpy(float)[rows] if base == "demo" else T.X_dx[rows]


def run_trial(args):
    n, i, only = args
    T = E.load_trial(n)
    M, info = strata_masks(T)
    H = halves(T, i)
    pc, shuf, noise = T.ecg_pc, T.ecg_pc[T.shuffle_perm], T.noise32
    out, skips = [], []
    for fam, s in ROW_STRATA:
        if s != only:
            continue
        m = M[s]
        full_ok = min((m & (T.t == 1)).sum(), (m & (T.t == 0)).sum()) >= MIN_ARM
        for half in ("full", "A", "B"):
            mm = m if half == "full" else m & (H == half)
            thr = MIN_ARM if half == "full" else MIN_ARM_HALF
            if not full_ok or min((mm & (T.t == 1)).sum(), (mm & (T.t == 0)).sum()) < thr:
                skips.append(dict(trial=n, stratum_family=fam, stratum=s, half=half,
                                  reason=f"stratum arm < {MIN_ARM}" if not full_ok else f"half arm < {thr}"))
                continue
            rows = np.where(mm)[0]
            common = dict(sweep=SWEEP, stratum_family=fam, stratum=s, trial=n, half=half, rb=T.rb, rs=T.rs,
                          stratum_share=float(mm.sum() / (len(T.t) if half == "full" else (H == half).sum())))
            try:
                ru = E.run_cell(T, None, rows=rows)
            except Exception as e:  # noqa: BLE001
                ru = dict(error=str(e)[:80])
            for base in BASES:
                Xb = base_X(T, base, rows)
                des = {"base": (base, Xb), "ECG": (f"{base}+ECG", np.hstack([Xb, pc[rows]])),
                       "shufECG": (f"{base}+shufECG", np.hstack([Xb, shuf[rows]])),
                       "noise": (f"{base}+noise32", np.hstack([Xb, noise[rows]]))}
                out.append(dict(common, cell=f"{base}|{s}", base=base, arm_role="unmatched", arm_label="unmatched", **ru))
                for role, (lab, X) in des.items():
                    try:
                        r = E.run_cell(T, X, rows=rows)
                    except Exception as e:  # noqa: BLE001
                        r = dict(error=str(e)[:80])
                    out.append(dict(common, cell=f"{base}|{s}", base=base, arm_role=role, arm_label=lab, **r))
    meta = dict(trial=n, n=len(T.t), pct_lag_known=round(100 * info["lag_known"], 1), pct_inpatient=round(100 * info["inp"], 1),
                pct_echo=round(100 * float((np.asarray(T.echo_any, bool) & np.asarray(T.post2016, bool)).mean()), 1),
                median_density=float(np.median(T.density)), **{f"pct:{s}": round(100 * float(M[s].mean()), 1) for _, s in ROW_STRATA})
    meta = meta if only == ALL else None
    print(f"[{time.strftime('%H:%M:%S')}] done {n} {only}: {len(out)} rows, {len(skips)} skips", flush=True)
    return out, skips, meta


def run(trials, workers, tag):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(n, E.TRIALS.index(n), s) for n in trials for _, s in ROW_STRATA]
    jobs.sort(key=lambda j: (-os.path.getsize(E.CACHE / f"restricted_trial_{j[0]}_v{E.CACHE_VERSION}.pkl"), j[2]))
    with Pool(min(workers, len(jobs), 32)) as p:
        res = p.map(run_trial, jobs, chunksize=1)
    R = pd.DataFrame([r for x in res for r in x[0]])
    for c in ("n", "n_t", "n_c", "n_pairs"):  # suppress 1-10
        if c in R:
            R.loc[R[c].between(1, 10), c] = np.nan
    sfx = f"_{tag}" if tag else ""
    R.to_csv(OUT / f"results{sfx}.csv", index=False)
    pd.DataFrame([r for x in res for r in x[1]], columns=["trial", "stratum_family", "stratum", "half", "reason"]).to_csv(OUT / f"skips{sfx}.csv", index=False)
    pd.DataFrame([x[2] for x in res if x[2] is not None]).to_csv(OUT / f"trial_meta{sfx}.csv", index=False)


# ---------------------------------------------------------------- summaries
def metric_vals(x, m):
    if m == "absd":
        return (x.loghr - x.rb).abs()
    if m == "z2":
        return (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2)
    return x[m]


def diffs(g, a, b, m):
    A_ = g[g.arm == a].drop_duplicates("trial").set_index("trial")
    B_ = g[g.arm == b].drop_duplicates("trial").set_index("trial")
    tt = A_.index.intersection(B_.index)
    return (metric_vals(A_.loc[tt], m) - metric_vals(B_.loc[tt], m)).dropna()


def tci(d):
    from scipy.stats import t as tdist
    d = np.asarray(d, float)
    k = len(d)
    if k < 2:
        return np.nan, np.nan
    h = tdist.ppf(0.975, k - 1) * d.std(ddof=1) / np.sqrt(k)
    return d.mean() - h, d.mean() + h


def trial_level_sets(R, meta):
    """Trial-level strata from the full-cohort 'all' cell: dict (family, label) -> list of trials."""
    from trial_specs import TRIALS as SPEC
    key = {n: {**PRIMARY, **EXTRA}[n][0] for n in E.TRIALS}
    cr = json.load(open(HERE.parent.parent / "docs" / "v14" / "closeness_rating.json"))
    u = R[(R.stratum == ALL) & (R.half == "full") & (R.arm_role == "unmatched") & (R.base == "sparse")].set_index("trial")
    conf = (u.loghr - u.rb).abs()
    size = meta.set_index("trial").n.reindex(conf.index)
    tr = list(conf.index)
    S = {}
    S[("role", "role=physiology")] = [n for n in tr if SPEC[key[n]]["role"] == "physiology"]
    S[("role", "role=control")] = [n for n in tr if SPEC[key[n]]["role"] != "physiology"]
    S[("closeness", "close emulation=yes")] = [n for n in tr if cr[key[n]]["close_emulation"]]
    S[("closeness", "close emulation=no")] = [n for n in tr if not cr[key[n]]["close_emulation"]]
    for fam, v, lab in (("confounding", conf, "|unadj-RCT|"), ("size", size, "N")):
        q = pd.qcut(v.rank(method="first"), 3, labels=False)
        for j, nm in enumerate(("T1 (low)", "T2", "T3 (high)")):
            S[(fam, f"{lab} {nm}")] = list(q[q == j].index)
    return S, conf


def summarize(tag):
    sfx = f"_{tag}" if tag else ""
    R = pd.read_csv(OUT / f"results{sfx}.csv")
    meta = pd.read_csv(OUT / f"trial_meta{sfx}.csv")
    skips = pd.read_csv(OUT / f"skips{sfx}.csv")
    R["arm"] = R.arm_role
    R = R[R.loghr.notna()] if "loghr" in R else R
    TL, conf = trial_level_sets(R, meta)
    # cells: (base, family, stratum, kind, frame)
    cells = []
    for base in BASES:
        for fam, s in ROW_STRATA:
            cells.append((base, fam, s, "row", R[(R.base == base) & (R.stratum == s)]))
        for (fam, s), trs in TL.items():
            cells.append((base, fam, s, "trial", R[(R.base == base) & (R.stratum == ALL) & R.trial.isin(trs)]))
    rows, forest = [], []
    for base, fam, s, kind, g0 in cells:
        for half in ("full", "A", "B"):
            g = g0[g0.half == half]
            r = dict(cell=f"{base}|{s}", base=base, family=fam, stratum=s, level=kind, half=half)
            for b, lab in (("base", "base"), ("shufECG", "shuf"), ("noise", "noise")):
                sp = E.summarize_pairs(g, [], "ECG", b)
                if not len(sp):
                    continue
                sp = sp.iloc[0]
                if lab == "base":
                    r["n_trials"] = int(sp.n_trials)
                    for arm_lab, col in (("ECG", "a"), ("base", "b")):
                        r[f"cons_{arm_lab}"], r[f"phi_{arm_lab}"] = sp[f"cons_{col}"], sp[f"phi_{col}"]
                for m in METRICS:
                    ok = sp.n_trials >= MIN_TRIALS
                    r[f"d_{m}_{lab}"] = sp[f"d_{m}"]
                    r[f"k_{m}_{lab}"] = sp[f"k_{m}"]
                    r[f"p_{m}_{lab}"] = sp[f"p_{m}"] if ok else np.nan
            for arm in ("shufECG", "noise", "unmatched"):
                x = g[g.arm == arm].dropna(subset=["loghr", "se"]).drop_duplicates("trial")
                z = (x.loghr - x.rb) / np.sqrt(x.se ** 2 + x.rs ** 2)
                r[f"cons_{arm}"] = float(100 * np.mean(np.abs(z) < 1.96)) if len(x) else np.nan
                r[f"phi_{arm}"] = E._phi((x.loghr - x.rb).to_numpy(), (x.se ** 2 + x.rs ** 2).to_numpy())
            for m in METRICS:
                d = diffs(g, "ECG", "base", m)
                lo, hi = tci(d)
                r[f"lo_{m}"], r[f"hi_{m}"] = lo, hi
            rows.append(r)
    S = pd.DataFrame(rows)
    full = S.half == "full"
    for m in METRICS:
        S.loc[full, f"q_{m}"] = E.bh_fdr(S.loc[full, f"p_{m}_base"])
        S[f"specific_{m}"] = ((S[f"p_{m}_base"] < 0.05) & (S[f"d_{m}_base"] < 0) & (S[f"d_{m}_shuf"] < 0) & (S[f"d_{m}_noise"] < 0))
    # replication columns onto full rows
    W = S.set_index(["cell", "half"])
    for m in METRICS:
        for h in ("A", "B"):
            S.loc[full, f"d_{m}_{h}"] = [W.loc[(c, h), f"d_{m}_base"] if (c, h) in W.index else np.nan for c in S.cell[full]]
            S.loc[full, f"p_{m}_{h}"] = [W.loc[(c, h), f"p_{m}_base"] if (c, h) in W.index else np.nan for c in S.cell[full]]
        S.loc[full, f"repl_{m}"] = (np.sign(S[f"d_{m}_A"]) == np.sign(S[f"d_{m}_base"])) & (np.sign(S[f"d_{m}_B"]) == np.sign(S[f"d_{m}_base"]))
    S.to_csv(OUT / f"summary{sfx}.csv", index=False)
    MR = meta_regression(R, meta, conf)
    MR.to_csv(OUT / f"metaregression{sfx}.csv", index=False)
    if not tag:
        forest_fig(S)
        heatmap(S)
    write_md(S, MR, meta, skips, R, TL, conf, tag)
    return S


def meta_regression(R, meta, conf, nperm=10000):
    from trial_specs import TRIALS as SPEC
    key = {n: {**PRIMARY, **EXTRA}[n][0] for n in E.TRIALS}
    mt = meta.set_index("trial")
    out = []
    for base in BASES:
        for half in ("full", "A", "B"):
            g = R[(R.base == base) & (R.stratum == ALL) & (R.half == half)]
            bse = g[g.arm == "base"].drop_duplicates("trial").set_index("trial")
            P = pd.DataFrame(dict(conf=conf, pct_echo=mt.pct_echo, log_density=np.log1p(mt.median_density),
                                  physiology=[float(SPEC[key[n]]["role"] == "physiology") for n in mt.index])).reindex(bse.index)
            w = 1 / (bse.se ** 2 + bse.rs ** 2)
            for arm_a, m in [("ECG", mm) for mm in METRICS] + [(pl, mm) for pl in ("shufECG", "noise") for mm in METRICS]:
                y = diffs(g, arm_a, "base", m).reindex(bse.index)
                ok = y.notna() & P.notna().all(1) & w.notna()
                Y, X, Wt = y[ok].to_numpy(), P[ok].to_numpy(float), w[ok].to_numpy()
                if len(Y) < MIN_TRIALS:
                    continue
                rng = np.random.default_rng(16064)

                def wls(Xm, Yv):
                    Z = np.column_stack([np.ones(len(Yv)), Xm])
                    sw = np.sqrt(Wt)
                    return np.linalg.lstsq(Z * sw[:, None], Yv * sw, rcond=None)[0][1:]
                perms = [rng.permutation(len(Y)) for _ in range(nperm if arm_a == "ECG" else 2000)]
                for j, pn in enumerate(P.columns):  # univariable
                    b = wls(X[:, [j]], Y)[0]
                    null = np.array([wls(X[pi][:, [j]], Y)[0] for pi in perms])
                    out.append(dict(base=base, half=half, contrast=f"{arm_a} - base", metric=m, model="univariable", predictor=pn, k=len(Y), slope=b,
                                    slope_per_sd=b * X[:, j].std(), perm_p=float(np.mean(np.abs(null) >= abs(b) - 1e-12))))
                if arm_a != "ECG":
                    continue
                bj = wls(X, Y)
                for j, pn in enumerate(P.columns):  # joint; permute one column, others fixed
                    null = []
                    for pi in perms[:2000]:
                        Xp = X.copy()
                        Xp[:, j] = X[pi, j]
                        null.append(wls(Xp, Y)[j])
                    null = np.array(null)
                    out.append(dict(base=base, half=half, contrast=f"{arm_a} - base", metric=m, model="joint (4 predictors)", predictor=pn, k=len(Y), slope=bj[j],
                                    slope_per_sd=bj[j] * X[:, j].std(), perm_p=float(np.mean(np.abs(null) >= abs(bj[j]) - 1e-12))))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- figures
BLUE, ORANGE, GRAY, INK, INK2 = "#2a78d6", "#eb6834", "#f0efec", "#0b0b0b", "#52514e"
MLAB = {"absd": "|Δlog HR| vs RCT", "z2": "z²", "mean_smd": "mean held-out |SMD|", "cstat": "held-out C-statistic"}


def _order(S):
    f = S[(S.half == "full") & (S.base == "demo")]
    return list(zip(f.family, f.stratum))


def forest_fig(S):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    order = _order(S)
    ny = len(order)
    fig, axes = plt.subplots(1, 8, figsize=(24, 0.36 * ny + 2.2), sharey=True)
    ylab = [f"{s}" for _, s in order]
    for bi, base in enumerate(BASES):
        f = S[(S.half == "full") & (S.base == base)].set_index("stratum")
        col = BLUE if base == "demo" else ORANGE
        for mi, m in enumerate(METRICS):
            ax = axes[bi * 4 + mi]
            ax.axvline(0, color=INK2, lw=0.8)
            fams = [fm for fm, _ in order]
            for y in range(1, ny):
                if fams[y] != fams[y - 1]:
                    ax.axhline(y - 0.5, color="#d9d8d4", lw=0.6)
            for y, (_, s) in enumerate(order):
                r = f.loc[s]
                d, lo, hi, p = r[f"d_{m}_base"], r[f"lo_{m}"], r[f"hi_{m}"], r[f"p_{m}_base"]
                if pd.isna(d):
                    continue
                ax.plot([lo, hi], [y, y], color=col, lw=2, solid_capstyle="round")
                spec = bool(r[f"specific_{m}"]) and bool(r.get(f"repl_{m}", False))
                ax.plot(d, y, "D" if spec else "o", ms=8, mfc=col if (p < 0.05) else "white", mec=INK if spec else col,
                        mew=1.2 if spec else 1.8, zorder=3)
                ptxt = "–" if pd.isna(p) else f"{p:.3f}"
                ax.text(1.02, y, f"p={ptxt} k={int(r.n_trials)}", transform=ax.get_yaxis_transform(), fontsize=6.5,
                        va="center", color=INK2)
            ax.set_title(f"{base}: {MLAB[m]}", fontsize=9, color=INK)
            ax.tick_params(labelsize=7, colors=INK2)
            for sp in ("top", "right"):
                ax.spines[sp].set_visible(False)
            ax.set_xlabel("ECG − base (neg. = ECG better)", fontsize=7, color=INK2)
    axes[0].set_yticks(range(ny))
    axes[0].set_yticklabels(ylab, fontsize=7.5)
    axes[0].invert_yaxis()
    fig.suptitle("S4 subgroups: ECG − base per stratum (full cohort; mean across trials, 95% t-interval, sign-flip p, k trials). "
                 "Filled = p<0.05; diamond = ECG-specific (p<0.05, beats shufECG & noise in direction) and same sign in both halves",
                 fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97), w_pad=4.5)
    fig.savefig(DOCS / "S4_SUBGROUPS_forest.png", dpi=150)
    plt.close(fig)


def heatmap(S):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", [BLUE, GRAY, ORANGE])
    order = [(b, s) for b in BASES for _, s in _order(S)]
    fig, axes = plt.subplots(1, 3, figsize=(15, 0.2 * len(order) + 2))
    for ax, half in zip(axes, ("full", "A", "B")):
        f = S[S.half == half].set_index(["base", "stratum"])
        V = np.full((len(order), 4), np.nan)
        for i, c in enumerate(order):
            for j, m in enumerate(METRICS):
                if c in f.index:
                    d, p = f.loc[c, f"d_{m}_base"], f.loc[c, f"p_{m}_base"]
                    V[i, j] = np.sign(d) * -np.log10(max(p, 1e-4)) if pd.notna(p) else np.nan
                    ax.text(j, i, "–" if pd.isna(d) else f"{d:+.3f}", ha="center", va="center", fontsize=5.5, color=INK)
        ax.imshow(V, cmap=cmap, vmin=-3, vmax=3, aspect="auto")
        ax.set_xticks(range(4))
        ax.set_xticklabels([MLAB[m] for m in METRICS], fontsize=7, rotation=20)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([f"{b} | {s}" for b, s in order] if half == "full" else [], fontsize=6)
        ax.set_title(f"half = {half}", fontsize=9)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(-3, 3))
    cb = fig.colorbar(sm, ax=axes, shrink=0.5)
    cb.set_label("sign(d) × −log10 p  (blue = ECG better)", fontsize=8)
    fig.suptitle("S4 subgroups heat map: ECG − base mean difference (text) and sign-flip p (colour)", fontsize=10)
    fig.savefig(DOCS / "S4_SUBGROUPS_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- markdown
def fp(p):
    return "–" if pd.isna(p) else (f"{p:.3f}" if p >= 0.001 else "<0.001")


def write_md(S, MR, meta, skips, R, TL, conf, tag):
    sfx = f"_{tag}" if tag else ""
    f = S[S.half == "full"].copy()
    L = [f"# v1.6 sweep S4: populations / effect modifiers ({time.strftime('%Y-%m-%d')})\n",
         "Exploratory (post-hoc specification, `docs/V16_SWEEP_PLAN.md`). Script `scripts/v16/s4_subgroups.py`; "
         f"long results `{OUT}/results{sfx}.csv`, summaries `summary{sfx}.csv`, `metaregression{sfx}.csv` (restricted dir, gitignored). "
         "Bases demo (age, sex, index year) and sparse; ECG = 32 BCL PCs; 1:1 caliper-0.2 matching on an L2 (C=1) PS "
         "re-fitted within each stratum; held-out balance and C-statistic computed in the stratum's matched set. "
         "Arms: base, base+ECG, base+shufECG, base+noise32; unmatched reference. Halves A/B = seeded patient split within trial "
         "(seed 16060 + trial index, stratified by treatment); strata are defined on the full trial cohort then intersected "
         "with the half. d = mean over trials of (ECG − base); negative = ECG better for all four metrics "
         "(|Δlog HR|, z², mean held-out |SMD|, held-out C-statistic). p = exact sign-flip; q = BH-FDR over all "
         f"{len(f)} full-cohort cells (both bases, row and trial-level strata) per metric. "
         f"Trial x stratum skipped if either arm < {MIN_ARM} (full) or < {MIN_ARM_HALF} (per half); tests need >= {MIN_TRIALS} trials. "
         "**ECG-specific** = ECG vs base p < 0.05 with d < 0 AND ECG beats shufECG and noise32 in direction. "
         "**Replicated** = half A and half B d have the same sign as full.\n",
         "KEYFINDINGS_PLACEHOLDER\n"]
    # main tables per metric
    for m in METRICS:
        t = f[["base", "family", "stratum", "n_trials", f"d_{m}_base", f"lo_{m}", f"hi_{m}", f"k_{m}_base", f"p_{m}_base", f"q_{m}",
               f"d_{m}_shuf", f"p_{m}_shuf", f"d_{m}_noise", f"p_{m}_noise", f"specific_{m}", f"d_{m}_A", f"p_{m}_A", f"d_{m}_B", f"p_{m}_B", f"repl_{m}"]].copy()
        for c in t.columns:
            if c.startswith("p_") or c.startswith("q_"):
                t[c] = t[c].map(fp)
        t.columns = ["base", "family", "stratum", "k", "d ECG−base", "95% lo", "95% hi", "improved", "p", "q", "d vs shuf", "p vs shuf",
                     "d vs noise", "p vs noise", "ECG-specific", "d half A", "p A", "d half B", "p B", "replicated"]
        L += [f"## {MLAB[m]} (ECG − base; full cohort, with half A/B replication)\n", md(t, 4 if m in ("mean_smd", "cstat") else 3) + "\n"]
    # consistency / phi
    c = f[["base", "stratum", "n_trials", "cons_unmatched", "cons_base", "cons_ECG", "cons_shufECG", "cons_noise",
           "phi_unmatched", "phi_base", "phi_ECG", "phi_shufECG", "phi_noise"]]
    L += ["## Consistency (% trials |z| < 1.96) and dispersion φ per arm (full cohort)\n", md(c, 2) + "\n"]
    # trial-level sets
    L += ["## Trial-level strata (subsets of the 18 trials at stratum 'all')\n",
          "Confounding magnitude = |unmatched log HR − RCT log HR| in the full trial cohort; size = analysed N; tertiles by rank.\n",
          md(pd.DataFrame([dict(family=k[0], stratum=k[1], k=len(v), trials=", ".join(v)) for k, v in TL.items()])) + "\n"]
    # meta-regression
    mr = MR.copy() if len(MR) else pd.DataFrame(columns=["base", "half", "metric", "model", "predictor", "k", "slope", "slope_per_sd", "perm_p"])
    mr["perm_p"] = mr.perm_p.map(fp)
    L += ["## Trial-level meta-regression of the ECG gain (ECG − base at stratum 'all')\n",
          "Weighted least squares, weight = 1/(SE_base² + SE_RCT²); predictors: confounding magnitude (|unadj − RCT|), % patients "
          "with echo (post-2016 echo measure), log(1 + median code density), physiology role (1/0). Univariable slopes: "
          "permutation p (10,000 permutations of the predictor). Joint model: each predictor permuted with the others fixed "
          "(2,000 permutations). slope_per_sd = slope × SD of the predictor across trials. Negative slope = larger ECG gain "
          "with higher predictor values.\n",
          md(mr[(mr.half == "full") & (mr.contrast == "ECG - base")], 4) + "\n",
          "Placebo control: the same univariable regressions for shufECG − base and noise32 − base (2,000 permutations). "
          "A slope that also appears for the placebos reflects the base arm's error, not ECG information.\n",
          md(mr[(mr.half == "full") & (mr.contrast != "ECG - base")], 4) + "\n",
          "Half A / half B replication of the meta-regression (ECG − base):\n",
          md(mr[(mr.half != "full") & (mr.contrast == "ECG - base")], 4) + "\n"]
    # coverage
    mt = meta.copy()
    mt["confounding"] = mt.trial.map(conf)
    L += ["## Stratum coverage per trial (% of trial cohort in each stratum)\n",
          md(mt, 1) + "\n",
          "Skipped trial × stratum × half (either arm below the minimum size):\n",
          md(skips.groupby(["stratum", "half"]).trial.nunique().rename("n_trials_skipped").reset_index()) + "\n" if len(skips) else "none\n"]
    L += ["AUDIT_PLACEHOLDER\n"]
    p = DOCS / f"S4_SUBGROUPS{sfx.upper()}.md"
    old = p.read_text() if p.exists() else ""
    txt = "\n".join(L)
    # keep hand-written key findings / audit sections across re-runs
    for tagname in ("KEYFINDINGS", "AUDIT"):
        a, b = f"<!-- {tagname} -->", f"<!-- /{tagname} -->"
        if a in old:
            blk = old[old.index(a): old.index(b) + len(b)]
        else:
            blk = f"{a}\n## {'Key findings' if tagname == 'KEYFINDINGS' else 'Audit'}\n(to be written)\n{b}"
        txt = txt.replace(f"{tagname}_PLACEHOLDER", blk)
    p.write_text(txt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["prep", "run", "summarize"])
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    tr = a.trials.split(",")
    if a.cmd == "prep":
        prep(tr)
    elif a.cmd == "run":
        run(tr, min(a.workers, 40), a.tag)
    else:
        summarize(a.tag)


if __name__ == "__main__":
    main()
