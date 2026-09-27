#!/usr/bin/env python
"""v1.6 sweep S3 (docs/V16_SWEEP_PLAN.md): ECG representation, PS model and estimator. Exploratory.

Base designs: demo (T.cov[T.demo]) and sparse (T.X_dx); both are run for every cell.
  3a representation (L2 C=1 PS, 1:1 caliper-0.2 matching): ECG PCs {4,8,16,32,64} (T.ecg_pc64),
     PCs 128 and the full 256-d embedding (eval_longtail_balance.pcs on T.ecg_raw / raw), phenotype
     scores only (T.ph), phenotypes + 32 PCs. Unsupervised variants only (no outcome or held-out target).
  3b PS model (ECG = 32 PCs, 1:1 caliper 0.2): L2 C in {0.01, 0.1, 1, 100}, GBM (5-fold cross-fitted).
  3c estimator (ECG = 32 PCs, L2 C=1): matching caliper {0.05, 0.1, 0.2} x ratio {1, 3}; IPTW; overlap weights.
Arms per cell: base, base+ECG, base+shufECG (ECG rows permuted with T.shuffle_perm), base+noise (Gaussian,
same dimension as the ECG variant; noise32 = T.noise32). Unmatched once per trial/half. Halves: full, A, B
(rng = default_rng(16060 + trial_index), split stratified by treatment). Held-out C-statistic: engine default.

  python s3_repr.py --run [--trials a,b] [--workers 32] [--out results.csv]
  python s3_repr.py --summarize [--workers 32]
Outputs (aggregates only): /mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s3-repr/, docs/v16/S3_REPR*.{md,png}.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v16_engine as E  # noqa: E402
from eval_longtail_balance import pcs  # noqa: E402
from v13_summarize import md  # noqa: E402

SWEEP = "s3-repr"
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s3-repr")
DOCS = HERE.parent.parent / "docs" / "v16"
MD = DOCS / "S3_REPR.md"
HALVES = ("full", "A", "B")
BASES = ("demo", "sparse")
METRICS = ("absd", "z2", "mean_smd", "cstat")
REPS = ["pc4", "pc8", "pc16", "pc32", "pc64", "pc128", "raw256", "ph", "ph+pc32"]
REP_DIM_ORDER = ["pc4", "pc8", "pc16", "pc32", "pc64", "pc128", "raw256"]
NPC = {"pc4": 4, "pc8": 8, "pc16": 16, "pc32": 32, "pc64": 64, "pc128": 128, "raw256": 256}


def cells():
    """List of cell dicts: family, cell, base, rep, ps_model, C, estimator, caliper, ratio."""
    out = []
    for b in BASES:
        for r in REPS:
            out.append(dict(family="3a", cell=f"3a|{b}|{r}", base=b, rep=r, ps_model="l2", C=1.0, estimator="match", caliper=0.2, ratio=1))
        for C in (0.01, 0.1, 1.0, 100.0):
            out.append(dict(family="3b", cell=f"3b|{b}|l2C={C:g}", base=b, rep="pc32", ps_model="l2", C=C, estimator="match", caliper=0.2, ratio=1))
        out.append(dict(family="3b", cell=f"3b|{b}|gbm", base=b, rep="pc32", ps_model="gbm", C=np.nan, estimator="match", caliper=0.2, ratio=1))
        for cal in (0.05, 0.1, 0.2):
            for ratio in (1, 3):
                out.append(dict(family="3c", cell=f"3c|{b}|match{cal:g}x{ratio}", base=b, rep="pc32", ps_model="l2", C=1.0, estimator="match", caliper=cal, ratio=ratio))
        for est in ("iptw", "overlap"):
            out.append(dict(family="3c", cell=f"3c|{b}|{est}", base=b, rep="pc32", ps_model="l2", C=1.0, estimator=est, caliper=np.nan, ratio=np.nan))
    return out


def half_rows(T, ti):
    """Seeded stratified split: dict half -> sorted row positions."""
    rng = np.random.default_rng(16060 + ti)
    a = []
    for v in (0, 1):
        idx = rng.permutation(np.where(T.t == v)[0])
        a.append(idx[: len(idx) // 2])
    A_ = np.sort(np.concatenate(a))
    B_ = np.setdiff1d(np.arange(len(T.t)), A_)
    return {"full": None, "A": A_, "B": B_}


def ecg_matrix(T, rep, cache):
    if rep in cache:
        return cache[rep]
    if rep.startswith("pc") and NPC[rep] <= 64:
        M = T.ecg_pc64[:, :NPC[rep]]
    elif rep == "pc128":
        M = pcs(T.ecg_raw, 128)
    elif rep == "raw256":
        M = T.ecg_raw  # full embedding (standardised inside ps_logit)
    elif rep == "ph":
        M = T.ph
    elif rep == "ph+pc32":
        M = np.hstack([T.ph, T.ecg_pc64[:, :32]])
    else:
        raise KeyError(rep)
    cache[rep] = np.asarray(M, float)
    return cache[rep]


def noise_matrix(T, d, cache):
    k = f"noise{d}"
    if k not in cache:
        cache[k] = T.noise32 if d == 32 else np.random.default_rng(3000 + 1000 * d).normal(size=(len(T.t), d))
    return cache[k]


def _task(args):
    trial, half, family = args
    ti = E.TRIALS.index(trial)
    T = E.load_trial(trial)
    rows = half_rows(T, ti)[half]
    sel = (lambda M: M) if rows is None else (lambda M: M[rows])
    base_X = {"demo": T.cov[T.demo].to_numpy(float), "sparse": np.asarray(T.X_dx, float)}
    cache, base_memo, out = {}, {}, []
    common = dict(sweep=SWEEP, trial=trial, half=half, rb=T.rb, rs=T.rs)
    if family == "ref":
        r = E.run_cell(T, None, rows=rows)
        out.append({**common, "family": "ref", "cell": "unmatched", "arm_role": "unmatched", "arm_label": "unmatched", **r})
        return out
    for c in [c for c in cells() if c["family"] == family]:
        estm = ("match", c["caliper"], int(c["ratio"])) if c["estimator"] == "match" else (c["estimator"],)
        psm = ("l2", c["C"]) if c["ps_model"] == "l2" else ("gbm", None)
        Em = ecg_matrix(T, c["rep"], cache)
        d = Em.shape[1]
        Xb = base_X[c["base"]]
        designs = {"base": (c["base"], Xb),
                   "ECG": (f"{c['base']}+{c['rep']}", np.hstack([Xb, Em])),
                   "shufECG": (f"{c['base']}+shuf_{c['rep']}", np.hstack([Xb, Em[T.shuffle_perm]])),
                   "noise": (f"{c['base']}+noise{d}", np.hstack([Xb, noise_matrix(T, d, cache)]))}
        for role, (lab, X) in designs.items():
            bkey = (c["base"], estm, psm)
            if role == "base" and bkey in base_memo:
                r = dict(base_memo[bkey])
            else:
                r = E.run_cell(T, sel(X), rows=rows, estimator=estm, ps_model=psm)
                if role == "base":
                    base_memo[bkey] = r
            out.append({**common, **c, "dim": d, "arm_role": role, "arm_label": lab, **r})
    return out


def run(trials, workers, fname):
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = [(t, h, f) for f in ("3b", "3a", "3c", "ref") for t in trials for h in HALVES]
    # big trials / gbm first
    size = {t: len(E.load_trial(t).t) for t in trials}
    tasks.sort(key=lambda x: -(size[x[0]] * (3 if x[2] == "3b" else 2 if x[2] == "3a" else 1 if x[2] == "3c" else 0.1) * (1 if x[1] == "full" else 0.5)))
    rows, t0 = [], time.time()
    with Pool(min(workers, 32, len(tasks))) as p:
        for i, res in enumerate(p.imap_unordered(_task, tasks, chunksize=1)):
            rows += res
            print(f"[{time.time() - t0:7.0f}s] {i + 1}/{len(tasks)} {res[0]['trial']} {res[0]['half']} {res[0]['family']}", flush=True)
    df = pd.DataFrame(rows)
    front = ["sweep", "family", "cell", "base", "rep", "dim", "ps_model", "C", "estimator", "caliper", "ratio", "trial", "half", "arm_role", "arm_label"]
    df = df[[c for c in front if c in df] + [c for c in df if c not in front]]
    df.to_csv(OUT / fname, index=False)
    print("wrote", OUT / fname, df.shape, f"{time.time() - t0:.0f}s")


# ---------------------------------------------------------------- summaries
COMPS = [("ECG", "base"), ("ECG", "shufECG"), ("ECG", "noise"), ("shufECG", "base"), ("noise", "base")]


def _sum_one(args):
    g, a, b = args
    return E.summarize_pairs(g.rename(columns={"arm_role": "arm"}), ["cell", "half"], a, b)


def summarize(workers, fname="results.csv"):
    df = pd.read_csv(OUT / fname)
    ref = df[df.family == "ref"]
    R = df[df.family != "ref"]
    jobs = [(g, a, b) for (_, _), g in R.groupby(["cell", "half"]) for a, b in COMPS]
    with Pool(min(workers, 32)) as p:
        S = pd.concat(p.map(_sum_one, jobs, chunksize=4), ignore_index=True)
    meta = R.drop_duplicates("cell").set_index("cell")[["family", "base", "rep", "dim", "ps_model", "C", "estimator", "caliper", "ratio"]]
    S = S.join(meta, on="cell")
    S["comp"] = S.arm_a + "-" + S.arm_b
    # BH-FDR: ECG vs base, full, per metric, within family and sweep-wide
    for m in METRICS:
        S[f"q_{m}"] = np.nan
        S[f"qsweep_{m}"] = np.nan
        k = (S.comp == "ECG-base") & (S.half == "full")
        S.loc[k, f"qsweep_{m}"] = E.bh_fdr(S.loc[k, f"p_{m}"])
        for fam in ("3a", "3b", "3c"):
            kf = k & (S.family == fam)
            S.loc[kf, f"q_{m}"] = E.bh_fdr(S.loc[kf, f"p_{m}"])
    S.to_csv(OUT / "summary_pairs.csv", index=False)
    # wide cell-level table
    order = [c["cell"] for c in cells()]
    W = []
    for cell in order:
        x = S[S.cell == cell].set_index(["comp", "half"])
        r = dict(cell=cell, **meta.loc[cell].to_dict())
        for m in METRICS:
            eb = x.loc[("ECG-base", "full")]
            r[f"d_{m}"], r[f"p_{m}"], r[f"k_{m}"] = eb[f"d_{m}"], eb[f"p_{m}"], eb[f"k_{m}"]
            r[f"q_{m}"], r[f"qsweep_{m}"] = eb[f"q_{m}"], eb[f"qsweep_{m}"]
            for comp, lab in (("ECG-shufECG", "vs_shuf"), ("ECG-noise", "vs_noise"), ("shufECG-base", "shuf_base"), ("noise-base", "noise_base")):
                r[f"d_{m}_{lab}"] = x.loc[(comp, "full"), f"d_{m}"]
                r[f"p_{m}_{lab}"] = x.loc[(comp, "full"), f"p_{m}"]
            for h in ("A", "B"):
                r[f"d_{m}_{h}"] = x.loc[("ECG-base", h), f"d_{m}"]
                r[f"p_{m}_{h}"] = x.loc[("ECG-base", h), f"p_{m}"]
            sig = r[f"p_{m}"] < 0.05 and r[f"d_{m}"] < 0
            beats = r[f"d_{m}_vs_shuf"] < 0 and r[f"d_{m}_vs_noise"] < 0
            r[f"spec_{m}"] = bool(sig and beats)
            r[f"rep_{m}"] = bool(r[f"d_{m}_A"] < 0 and r[f"d_{m}_B"] < 0)
            r[f"rep05_{m}"] = bool(r[f"rep_{m}"] and r[f"p_{m}_A"] < 0.05 and r[f"p_{m}_B"] < 0.05)
            # placebo artifact: a placebo arm significantly improves on base (p < 0.05, d < 0)
            r[f"plac_{m}"] = bool((r[f"d_{m}_shuf_base"] < 0 and r[f"p_{m}_shuf_base"] < 0.05) or
                                  (r[f"d_{m}_noise_base"] < 0 and r[f"p_{m}_noise_base"] < 0.05))
        for role in ("base", "ECG", "shufECG", "noise"):
            comp = "ECG-base" if role in ("ECG", "base") else f"{role}-base"
            lab = "a" if role != "base" else "b"
            r[f"cons_{role}"] = x.loc[(comp, "full"), f"cons_{lab}"]
            r[f"phi_{role}"] = x.loc[(comp, "full"), f"phi_{lab}"]
        W.append(r)
    W = pd.DataFrame(W)
    W.to_csv(OUT / "summary_cells.csv", index=False)
    # SE of per-trial differences (for the line plot)
    rr = R.copy()
    rr["absd"] = (rr.loghr - rr.rb).abs()
    rr["z2"] = (rr.loghr - rr.rb) ** 2 / (rr.se ** 2 + rr.rs ** 2)
    piv = rr.pivot_table(index=["cell", "half", "trial"], columns="arm_role", values=list(METRICS))
    audit = audit_checks(df, R)
    plots(W, S, piv)
    write_md(W, S, ref, R, audit)


def audit_checks(df, R):
    """Default-cell reproduction vs engine validation, placebo means, pair counts."""
    V = pd.read_csv(E.OUT / "validation_estimates.csv").set_index(["trial", "arm"])
    k = (R.cell == "3a|sparse|pc32") & (R.half == "full")
    x = R[k].set_index(["trial", "arm_role"])
    dev = []
    for (tr, role), v in x.iterrows():
        va = {"base": "sparse", "ECG": "sparse+ECG"}.get(role)
        if va is None or (tr, va) not in V.index:
            continue
        s = V.loc[(tr, va)]
        dev.append(dict(trial=tr, arm=va, d_loghr=abs(v.loghr - s.loghr), d_se=abs(v.se - s.se), d_mean_smd=abs(v.mean_smd - s.mean_smd),
                        d_cstat=abs(v.cstat - s.cstat), d_pairs=abs(v.n_pairs - s.n_pairs)))
    dev = pd.DataFrame(dev)
    # noise32 placebo vs engine's sparse+noise32 design: same matrix; check it's the same noise
    ref = df[df.family == "ref"].set_index(["trial", "half"])
    un = [(tr, abs(ref.loc[(tr, "full")].loghr - V.loc[(tr, "unmatched")].loghr)) for tr in ref.reset_index().trial.unique() if (tr, "unmatched") in V.index]
    pc = R[R.estimator == "match"].copy()
    pc["pair_frac"] = pc.n_pairs / np.minimum(pc.n_t, pc.n_c)
    pairs = pc.groupby(["half", "arm_role"]).pair_frac.agg(["min", "median", "max"]).reset_index()
    ess = R[R.estimator.isin(["iptw", "overlap"])].groupby(["estimator", "half", "arm_role"])[["ess_t", "ess_c"]].median().reset_index()
    nsz = R[R.arm_role == "base"].drop_duplicates(["trial", "half"]).pivot(index="trial", columns="half", values="n").reset_index()
    nsz["A+B-full"] = nsz.A + nsz.B - nsz.full
    nan = R.groupby("family")[["loghr", "cstat", "mean_smd"]].apply(lambda g: g.isna().sum()).reset_index()
    return dict(dev=dev, max_unmatched_dev=max(u[1] for u in un) if un else np.nan, pairs=pairs, ess=ess, nsz=nsz, nan=nan,
                secs=R.groupby(["family", "ps_model"]).secs.agg(["median", "max"]).reset_index())


def _cell_label(c):
    return c.split("|", 1)[1]


def plots(W, S, piv):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    cmap = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f0efec", "#e34948"])  # blue = ECG better
    mnames = {"absd": "|Δlog HR| vs RCT", "z2": "z² vs RCT", "mean_smd": "mean held-out |SMD|", "cstat": "held-out C-stat"}
    fig, axes = plt.subplots(1, 2, figsize=(15, 14), constrained_layout=True)
    for ax, b in zip(axes, BASES):
        w = W[W.base == b].reset_index(drop=True)
        Z = np.array([[np.sign(r[f"d_{m}"]) * -np.log10(max(r[f"p_{m}"], 1e-4)) for m in METRICS] for _, r in w.iterrows()])
        im = ax.imshow(Z, cmap=cmap, norm=TwoSlopeNorm(0, -3, 3), aspect="auto")
        for i, r in w.iterrows():
            for j, m in enumerate(METRICS):
                s = f"{r[f'd_{m}']:+.3f}\np={r[f'p_{m}']:.3f}"
                tag = ""
                if r[f"spec_{m}"]:
                    tag += "S"
                if r[f"spec_{m}"] and r[f"rep_{m}"]:
                    tag += "R"
                if r[f"spec_{m}"] and r[f"rep05_{m}"]:
                    tag += "*"
                if r[f"plac_{m}"]:
                    tag += " P!"
                ax.text(j, i, s + (f" {tag}" if tag else ""), ha="center", va="center", fontsize=6.5, color="#1a1a1a")
        ax.set_xticks(range(len(METRICS)), [mnames[m] for m in METRICS], fontsize=8)
        ax.set_yticks(range(len(w)), [_cell_label(c) for c in w.cell], fontsize=7.5)
        for y in np.where(w.family.ne(w.family.shift()))[0][1:]:
            ax.axhline(y - 0.5, color="#1a1a1a", lw=1)
        ax.set_title(f"base = {b}: ECG − base (full cohort, 18 trials)", fontsize=10)
        ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=axes, shrink=0.4, label="sign(d) × −log10(p)   (blue = ECG better)")
    cb.outline.set_visible(False)
    fig.suptitle("S3 ECG representation / PS model / estimator. Cell text: mean paired difference d, sign-flip p. "
                 "S = ECG-specific (p<0.05, beats shufECG and noise), R = same direction in both halves, * = p<0.05 in both halves, P! = a placebo also "
                 "significantly improves on base", fontsize=8.5)
    fig.savefig(DOCS / "S3_REPR_heatmap.png", dpi=150)
    plt.close(fig)
    # line plot: gain vs number of PCs
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.2), constrained_layout=True)
    xs = [NPC[r] for r in REP_DIM_ORDER]
    col = {"demo": "#2a78d6", "sparse": "#eb6834"}
    for ax, m in zip(axes, METRICS):
        for b in BASES:
            for role, ls, lab in (("ECG", "-", "ECG"), ("shufECG", ":", "shufECG"), ("noise", "--", "noise")):
                mu, se = [], []
                for r in REP_DIM_ORDER:
                    cell = f"3a|{b}|{r}"
                    p = piv.loc[(cell, "full")][m]
                    dd = (p[role] - p["base"]).dropna()
                    mu.append(dd.mean())
                    se.append(dd.std(ddof=1) / np.sqrt(len(dd)))
                mu, se = np.array(mu), np.array(se)
                ax.plot(xs, mu, ls=ls, color=col[b], lw=2 if role == "ECG" else 1.2, marker="o" if role == "ECG" else None, ms=4,
                        label=f"{b}: {lab} − base")
                if role == "ECG":
                    ax.fill_between(xs, mu - se, mu + se, color=col[b], alpha=0.12, lw=0)
        ax.axhline(0, color="#8a8a8a", lw=0.8)
        ax.set_xscale("log", base=2)
        ax.set_xticks(xs, [str(x) if x < 256 else "256\n(raw)" for x in xs])
        ax.set_xlabel("ECG dimensions (PCs)")
        ax.set_title(f"{mnames[m]}: arm − base (neg = better)", fontsize=9)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.grid(axis="y", color="#e6e6e6", lw=0.6)
    axes[0].legend(fontsize=7, frameon=False)
    fig.suptitle("S3a: ECG gain vs number of ECG PCs (full cohort, mean over 18 trials ± 1 SE of per-trial difference; placebos dotted/dashed)", fontsize=9)
    fig.savefig(DOCS / "S3_REPR_pcs.png", dpi=150)
    plt.close(fig)


def _fmt(v, f=3):
    return "–" if pd.isna(v) else f"{v:.{f}f}"


def write_md(W, S, ref, R, audit):
    manual = ""
    if MD.exists():
        m = re.search(r"<!-- BEGIN MANUAL -->.*?<!-- END MANUAL -->", MD.read_text(), re.S)
        manual = m.group(0) if m else ""
    if not manual:
        manual = "<!-- BEGIN MANUAL -->\n## Key findings (plain language)\n\n(to be written)\n<!-- END MANUAL -->"
    L = [f"# v1.6 sweep S3: ECG representation, PS model and estimator ({time.strftime('%Y-%m-%d')})\n",
         "Exploratory (post-hoc specification accepted; docs/V16_SWEEP_PLAN.md guardrails apply). Script "
         "`scripts/v16/s3_repr.py`; long results `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s3-repr/results.csv`; "
         "summaries `summary_pairs.csv`, `summary_cells.csv`. 18 trials, imputation 1, pool split seed 0. Aggregates only.\n",
         manual + "\n",
         "## Design\n",
         "- Bases: **demo** (age, sex, index year) and **sparse** (demo + coded diagnoses). Every cell has four arms: "
         "base, base+ECG, base+shufECG (the same ECG matrix with rows permuted by `T.shuffle_perm`), base+noise (Gaussian, "
         "same dimension; 32-d = `T.noise32`, else seed 3000+1000·d). Unmatched is run once per trial/half.\n"
         "- 3a representation (L2 C=1, 1:1 caliper 0.2): PCs 4/8/16/32/64 (from `T.ecg_pc64`), PCs 128 "
         "(`pcs(T.ecg_raw, 128)`, unsupervised, full cohort), full 256-d embedding (standardised), phenotype scores (5), "
         "phenotypes + 32 PCs. Supervised ECG summaries were not run (any ECG→treatment model is just the PS; any "
         "ECG→held-out-variable model would leak the evaluation targets).\n"
         "- 3b PS model (32 PCs, 1:1 caliper 0.2): L2 C ∈ {0.01, 0.1, 1, 100} (applied to base and ECG arms alike), GBM "
         "(5-fold cross-fitted). 3c estimator (32 PCs, L2 C=1): matching caliper {0.05, 0.1, 0.2} × ratio {1, 3}; "
         "stabilised trimmed IPTW; overlap weights. `3b|*|l2C=1` and `3c|*|match0.2x1` are the same cell as `3a|*|pc32` "
         "(kept in each family for FDR completeness).\n"
         "- Halves: full; A/B = seeded treatment-stratified 50/50 patient split (`default_rng(16060 + trial_index)`); "
         "PCs are unsupervised and computed once on the full cohort.\n"
         "- Metrics (ECG − base, paired over trials; negative = ECG better): absd = |Δlog HR vs RCT|, z2 = Δ²/(se²+se_RCT²), "
         "mean_smd = mean |SMD| over the 58 held-out variables, cstat = cross-fitted held-out C-statistic (L2 C=0.01). "
         "p = exact sign-flip. q = BH-FDR within family (3a/3b/3c) per metric over cells (ECG vs base, full); qsweep = over all 44 cells.\n"
         "- **ECG-specific** (S) = ECG vs base p<0.05 with d<0 AND ECG beats both shufECG and noise in direction. "
         "**Replicated** (R) = d<0 in both half A and half B (R05 = also p<0.05 in both). **Placebo flag** (P!) = shufECG or "
         "noise significantly improves on base (d<0, p<0.05): dimension/regularisation artifact.\n",
         "![heat map](S3_REPR_heatmap.png)\n",
         "![gain vs PCs](S3_REPR_pcs.png)\n"]
    # status table
    L.append("## Status per cell and metric (full cohort)\n")
    L.append("Entry: `d (p; q)` for ECG − base, then flags. S = ECG-specific, R = same direction in halves A and B, "
             "R05 = p<0.05 in both halves, P! = placebo also significantly improves.\n")
    rows = []
    for _, r in W.iterrows():
        e = dict(cell=_cell_label(r.cell), fam=r.family)
        for m in METRICS:
            fl = ("S" if r[f"spec_{m}"] else "") + (" R" if r[f"rep_{m}"] else "") + (" R05" if r[f"rep05_{m}"] else "") + (" P!" if r[f"plac_{m}"] else "")
            e[m] = f"{r[f'd_{m}']:+.3f} ({r[f'p_{m}']:.3f}; {r[f'q_{m}']:.2f}){' ' + fl.strip() if fl.strip() else ''}"
        rows.append(e)
    L.append(md(pd.DataFrame(rows)) + "\n")
    # per metric detailed tables
    for m in METRICS:
        L.append(f"## {m}: ECG vs base, vs placebos, and halves\n")
        t = pd.DataFrame(dict(cell=W.cell.map(_cell_label), d=W[f"d_{m}"], k=W[f"k_{m}"], p=W[f"p_{m}"], q=W[f"q_{m}"], qsweep=W[f"qsweep_{m}"],
                              d_vs_shuf=W[f"d_{m}_vs_shuf"], p_vs_shuf=W[f"p_{m}_vs_shuf"], d_vs_noise=W[f"d_{m}_vs_noise"],
                              p_vs_noise=W[f"p_{m}_vs_noise"], d_shuf_base=W[f"d_{m}_shuf_base"], p_shuf_base=W[f"p_{m}_shuf_base"],
                              d_noise_base=W[f"d_{m}_noise_base"], p_noise_base=W[f"p_{m}_noise_base"],
                              d_A=W[f"d_{m}_A"], p_A=W[f"p_{m}_A"], d_B=W[f"d_{m}_B"], p_B=W[f"p_{m}_B"]))
        L.append(md(t, 3) + "\n")
    L.append("## Consistency (% |z|<1.96 vs RCT) and dispersion φ per arm (full cohort)\n")
    t = W[["cell"] + [f"{s}_{r}" for r in ("base", "ECG", "shufECG", "noise") for s in ("cons", "phi")]].copy()
    t["cell"] = t.cell.map(_cell_label)
    L.append(md(t, 1) + "\n")
    rf = ref.groupby("half").agg(mean_smd=("mean_smd", "mean"), cstat=("cstat", "mean")).reset_index()
    L.append("Unmatched reference (mean over trials): \n\n" + md(rf, 3) + "\n")
    # audit
    dev = audit["dev"]
    L.append("## Audit\n")
    L.append("1. **Default cell reproduces the engine validation.** Cell `3a|sparse|pc32`, full cohort, base and ECG arms "
             "vs `claude-v16-engine/validation_estimates.csv` (`sparse`, `sparse+ECG`) over "
             f"{dev.trial.nunique()} trials: max |Δlog HR| = {dev.d_loghr.max():.2e}, max |ΔSE| = {dev.d_se.max():.2e}, "
             f"max |Δmean_smd| = {dev.d_mean_smd.max():.2e}, max |Δcstat| = {dev.d_cstat.max():.2e}, max |Δpairs| = {dev.d_pairs.max():.0f}. "
             f"Unmatched (full) max |Δlog HR| vs validation = {audit['max_unmatched_dev']:.2e}.\n")
    L.append("2. **Half sizes** (base arm n; A + B − full should be 0):\n\n" + md(audit["nsz"], 0) + "\n")
    L.append("3. **Matched-pair fraction** (pairs / smaller arm) by half and arm, matching cells:\n\n" + md(audit["pairs"], 3) + "\n")
    L.append("4. **Weighting ESS** (median over trials):\n\n" + md(audit["ess"], 0) + "\n")
    L.append("5. **Missing results** (NaN counts by family):\n\n" + md(audit["nan"], 0) + "\n")
    L.append("6. **Runtime** (s per run_cell):\n\n" + md(audit["secs"], 2) + "\n")
    pl = W[[f"plac_{m}" for m in METRICS]].sum()
    L.append("7. **Placebo arms vs base**: number of cells (of 44) where a placebo significantly improved on base: " +
             ", ".join(f"{m} {int(pl[f'plac_{m}'])}" for m in METRICS) + ". See the P! flags above.\n")
    extra = OUT / "audit_notes.md"
    if extra.exists():
        L.append(extra.read_text() + "\n")
    MD.write_text("\n".join(L))
    print("wrote", MD)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--out", default="results.csv")
    a = ap.parse_args()
    os.umask(0o077)
    if a.run:
        run(a.trials.split(","), a.workers, a.out)
    if a.summarize:
        summarize(a.workers, a.out)


if __name__ == "__main__":
    main()
