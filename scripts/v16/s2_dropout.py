#!/usr/bin/env python
"""v1.6 sweep S2 (docs/V16_SWEEP_PLAN.md): real-data code sparsity. Exploratory.

Cells: dropout p in {0, .25, .5, .75, .9, 1} x base in {sparse, hdPS200} x degradation seed in {0, 1, 2}.
Trial.degraded(p, seed) deletes each recorded dx / medication-order flag and each hdPS code (all levels of a
code together) per patient with probability p; demographics, labs, vitals, echo and ECG are unchanged.
Arms per cell: base, base+ECG (32 PCs), base+shufECG, base+noise32; unmatched once per trial/half.
Halves: full, A, B (rng 16060 + trial index, stratified by treatment). Estimator: engine default
(1:1 caliper-0.2 matching on the L2 C=1 PS logit).

Held-out balance is ALWAYS evaluated on the TRUE (undegraded) held-out matrix of the original trial:
run_cell(..., heldout=T.H) with T the undegraded trial (the degraded copy's cov meds are not used).

Usage:  s2_dropout.py run [--trials a,b] [--workers 40] [--out results.csv]
        s2_dropout.py summarize
Aggregates only.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v16_engine as E  # noqa: E402

SWEEP = "s2-dropout"
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s2-dropout")
DOCS = HERE.parent.parent / "docs" / "v16"
PS = [0.0, 0.25, 0.5, 0.75, 0.9, 1.0]
BASES = ["sparse", "hdPS200"]
SEEDS = [0, 1, 2]
HALVES = ["full", "A", "B"]
ROLES = {"base": "", "ECG": "+ECG", "shufECG": "+shufECG", "noise": "+noise32"}
METRICS = ["absd", "z2", "mean_smd", "cstat"]
_CACHE = {}


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
    A = np.sort(np.concatenate(a))
    B = np.setdiff1d(np.arange(len(T.t)), A)
    return {"full": None, "A": A, "B": B}


def _row(r, **kw):
    d = dict(sweep=SWEEP)
    d.update(kw)
    d.update(r)
    return d


def job(args):
    n, p, seed = args
    T = trial(n)
    H0 = T.H  # TRUE held-out matrix (undegraded)
    D = T.degraded(p, seed)
    assert D.H is H0  # shallow copy keeps the original evaluation matrix
    hv = halves(T, n)
    out = []
    for half, rows in hv.items():
        if p == 0.0 and seed == 0:
            r = E.run_cell(T, None, rows=rows, heldout=H0)
            out.append(_row(r, cell="unmatched", p=np.nan, base="none", seed=np.nan, trial=n, half=half,
                            arm_role="unmatched", arm_label="unmatched", rb=T.rb, rs=T.rs))
        for base in BASES:
            labels = {role: base + suf for role, suf in ROLES.items()}
            X = D.arms(list(labels.values()), rows=rows)
            for role, lab in labels.items():
                r = E.run_cell(D, X[lab], rows=rows, heldout=H0)
                out.append(_row(r, cell=f"{base}_p{p:g}", p=p, base=base, seed=seed, trial=n, half=half,
                                arm_role=role, arm_label=lab, rb=T.rb, rs=T.rs))
    return out


def run(trials, workers, outf):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(n, p, s) for n in trials for p in PS for s in SEEDS]
    # biggest trials first
    t0 = time.time()
    res = []
    with Pool(min(workers, 40)) as pool:
        for i, r in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            res.extend(r)
            if (i + 1) % 20 == 0 or i + 1 == len(jobs):
                print(f"{i + 1}/{len(jobs)} jobs, {time.time() - t0:.0f}s", flush=True)
    df = pd.DataFrame(res)
    df.to_csv(OUT / outf, index=False)
    print("wrote", OUT / outf, df.shape)


# ---------------------------------------------------------------- summaries
def metric_cols(df):
    df = df.copy()
    dd = df.loghr - df.rb
    v = df.se ** 2 + df.rs ** 2
    df["absd"] = dd.abs()
    df["z2"] = dd ** 2 / v
    df["cons"] = np.where(df.loghr.notna(), (np.abs(dd / np.sqrt(v)) < 1.96).astype(float), np.nan)
    return df


def seed_avg(df):
    """Per trial x half x cell x arm: average metrics (and loghr/se) over degradation seeds."""
    g = df.groupby(["cell", "p", "base", "half", "trial", "arm_role"], dropna=False)
    cols = ["absd", "z2", "cons", "mean_smd", "cstat", "loghr", "se", "rb", "rs", "n_pairs", "smd_prog"]
    return g[cols].mean().reset_index()


def paired(S, a, b, metrics=METRICS):
    """Sign-flip paired test on seed-averaged per-trial metrics (a - b; negative favours a)."""
    rows = []
    for (cell, p, base, half), g in S.groupby(["cell", "p", "base", "half"], dropna=False):
        A_ = g[g.arm_role == a].set_index("trial")
        B_ = g[g.arm_role == b].set_index("trial")
        tt = A_.index.intersection(B_.index)
        r = dict(cell=cell, p=p, base=base, half=half, arm_a=a, arm_b=b, n_trials=len(tt))
        for m in metrics:
            d = (A_.loc[tt, m] - B_.loc[tt, m]).to_numpy(float)
            d = d[~np.isnan(d)]
            r[f"d_{m}"] = float(d.mean()) if len(d) else np.nan
            r[f"k_{m}"] = f"{int((d < 0).sum())}/{len(d)}"
            r[f"p_{m}"] = E.sign_flip(d)[1] if len(d) else np.nan
        r["cons_a"], r["cons_b"] = 100 * A_.loc[tt, "cons"].mean(), 100 * B_.loc[tt, "cons"].mean()
        rows.append(r)
    return pd.DataFrame(rows)


def phi_table(df):
    """phi per arm per cell/half: computed per seed (E._phi), then mean / min / max over seeds."""
    rows = []
    for k, g in df.groupby(["cell", "p", "base", "half", "arm_role", "seed"], dropna=False):
        x = g.dropna(subset=["loghr", "se"])
        rows.append(dict(zip(["cell", "p", "base", "half", "arm_role", "seed"], k),
                         phi=E._phi((x.loghr - x.rb).to_numpy(), (x.se ** 2 + x.rs ** 2).to_numpy())))
    P = pd.DataFrame(rows)
    return P.groupby(["cell", "p", "base", "half", "arm_role"], dropna=False).phi.agg(["mean", "min", "max"]).reset_index()


def per_seed(df):
    """E.summarize_pairs per seed for ECG vs base (seed spread)."""
    x = df[df.arm_role != "unmatched"].rename(columns={"arm_role": "arm"})
    return E.summarize_pairs(x, ["cell", "p", "base", "half", "seed"], "ECG", "base")


def fmt_p(p):
    return "–" if pd.isna(p) else (f"{p:.3f}" if p >= 0.001 else "<.001")


def summarize(resf="results.csv"):
    os.umask(0o077)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    df = metric_cols(pd.read_csv(OUT / resf))
    S = seed_avg(df)
    cells = S[S.arm_role != "unmatched"]
    C = {k: paired(cells, "ECG", k) for k in ("base", "shufECG", "noise")}
    Cb = paired(cells, "base", "shufECG")
    Cn = paired(cells, "base", "noise")
    Ps = per_seed(df)
    PH = phi_table(df[df.arm_role != "unmatched"])
    # unmatched reference per half
    U = S[S.arm_role == "unmatched"]
    # FDR for ECG vs base, full, per metric over the 12 cells
    eb = C["base"].copy()
    for m in METRICS + []:
        eb[f"q_{m}"] = np.nan
        f = eb.half == "full"
        eb.loc[f, f"q_{m}"] = E.bh_fdr(eb.loc[f, f"p_{m}"])
    key = ["cell", "p", "base", "half"]
    M = eb.merge(C["shufECG"][key + [f"{x}_{m}" for m in METRICS for x in ("d", "p")]].rename(
        columns={f"{x}_{m}": f"{x}_{m}_vs_shuf" for m in METRICS for x in ("d", "p")}), on=key).merge(
        C["noise"][key + [f"{x}_{m}" for m in METRICS for x in ("d", "p")]].rename(
            columns={f"{x}_{m}": f"{x}_{m}_vs_noise" for m in METRICS for x in ("d", "p")}), on=key)
    for m in METRICS:
        M[f"spec_{m}"] = (M[f"p_{m}"] < 0.05) & (M[f"d_{m}"] < 0) & (M[f"d_{m}_vs_shuf"] < 0) & (M[f"d_{m}_vs_noise"] < 0)
    # seed spread for ECG vs base
    sp = Ps.groupby(key).agg(**{f"{s}_{x}_{m}": (f"{x}_{m}", s) for m in METRICS for x in ("d", "p") for s in ("min", "max")}).reset_index()
    M = M.merge(sp, on=key, how="left")
    M = M.sort_values(["base", "p", "half"], key=lambda s: s.map({"sparse": 0, "hdPS200": 1, "full": 0, "A": 1, "B": 2}).fillna(s) if s.name in ("base", "half") else s)
    M.to_csv(OUT / "summary_ecg.csv", index=False)
    pd.concat([C["shufECG"], C["noise"], Cb, Cn], ignore_index=True).to_csv(OUT / "summary_placebo.csv", index=False)
    PH.to_csv(OUT / "summary_phi.csv", index=False)
    Ps.to_csv(OUT / "summary_perseed.csv", index=False)
    # arm-level means (seed-avg, across trials)
    AM = S.groupby(["cell", "p", "base", "half", "arm_role"], dropna=False)[["absd", "z2", "cons", "mean_smd", "cstat", "smd_prog", "n_pairs"]].mean().reset_index()
    AM["cons"] *= 100
    AM = AM.merge(PH.rename(columns={"mean": "phi"})[["cell", "half", "arm_role", "phi"]], on=["cell", "half", "arm_role"], how="left")
    AM.to_csv(OUT / "summary_arms.csv", index=False)
    figs(M, AM, U, plt)
    write_md(M, AM, C, Cb, Cn, U, df)
    synth(M)
    audit_v14(df)


def synth(M):
    """Per cell x metric: full p / q, placebo p (both), half A / B p, and the combined verdict."""
    rows = []
    for (base, p), g in M.groupby(["base", "p"], sort=False):
        g = g.set_index("half")
        for m in METRICS:
            f, a, b = g.loc["full"], g.loc["A"], g.loc["B"]
            sig = f[f"p_{m}"] < 0.05 and f[f"d_{m}"] < 0
            fdr = f[f"q_{m}"] < 0.05
            plc_dir = f[f"d_{m}_vs_shuf"] < 0 and f[f"d_{m}_vs_noise"] < 0
            plc_sig = plc_dir and f[f"p_{m}_vs_shuf"] < 0.05 and f[f"p_{m}_vs_noise"] < 0.05
            rep = all(h[f"p_{m}"] < 0.05 and h[f"d_{m}"] < 0 for h in (a, b))
            rep_dir = all(h[f"d_{m}"] < 0 for h in (a, b))
            rows.append(dict(base=base, p=p, metric=m, d_full=f[f"d_{m}"], p_full=f[f"p_{m}"], q_full=f[f"q_{m}"],
                             p_vs_shuf=f[f"p_{m}_vs_shuf"], p_vs_noise=f[f"p_{m}_vs_noise"], p_A=a[f"p_{m}"], p_B=b[f"p_{m}"],
                             sig=sig, fdr=fdr, placebo_dir=plc_dir, placebo_sig=plc_sig, rep_AB_sig=rep, rep_AB_dir=rep_dir,
                             all_criteria=bool(sig and fdr and plc_sig and rep)))
    Y = pd.DataFrame(rows)
    Y.to_csv(OUT / "summary_synthesis.csv", index=False)
    x = Y.copy()
    for c in ("p_full", "q_full", "p_vs_shuf", "p_vs_noise", "p_A", "p_B"):
        x[c] = x[c].map(fmt_p)
    for c in ("sig", "fdr", "placebo_dir", "placebo_sig", "rep_AB_sig", "rep_AB_dir", "all_criteria"):
        x[c] = x[c].map({True: "yes", False: "no"})
    (OUT / "synthesis_table.md").write_text(E.md(x, 3) + "\n")


def audit_v14(df):
    """Reconcile with v1.4 real-data dropout (claude-v14/boot_<trial>_dropout.csv rep 0; seed 0, full cohort)."""
    rows, est = [], []
    for n in E.TRIALS:
        fb = E.A / "claude-v14" / f"boot_{n}_dropout.csv"
        if not fb.exists():
            continue
        b = pd.read_csv(fb)
        b = b[b.rep == 0]
        for p in (0.5, 0.75, 0.9):
            for lab in ("sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG"):
                x = df[(df.trial == n) & (df.half == "full") & np.isclose(df.p, p) & (df.seed == 0) & (df.arm_label == lab)]
                y = b[(b.pool == f"dropout_{p}") & (b.arm == lab)]
                if len(x) and len(y):
                    est.append(dict(trial=n, p=p, arm=lab, d_loghr=float(x.loghr.iloc[0] - y.loghr.iloc[0]),
                                    same_pairs=bool(x.n_pairs.iloc[0] == y.pairs.iloc[0]), rb=x.rb.iloc[0],
                                    v16=x.loghr.iloc[0], v14=y.loghr.iloc[0]))
    Es = pd.DataFrame(est)
    Es.to_csv(OUT / "audit_v14_estimates.csv", index=False)
    for src in ("v16", "v14"):
        for p in (0.5, 0.75, 0.9):
            for cn, a1, a0 in (("C1", "sparse+ECG", "sparse"), ("C2", "hdPS200+ECG", "hdPS200")):
                g = Es[np.isclose(Es.p, p)].pivot_table(index="trial", columns="arm", values=src)
                rb = Es[np.isclose(Es.p, p)].groupby("trial").rb.first().loc[g.index]
                d = ((g[a1] - rb) ** 2 - (g[a0] - rb) ** 2).dropna().to_numpy()
                rows.append(dict(source=src, p=p, contrast=cn, trials=len(d), mean_d_sqerr=d.mean(), p_signflip=E.sign_flip(d)[1],
                                 closer=int((d < 0).sum())))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "audit_v14_reconcile.csv", index=False)
    Es["absdev"] = Es.d_loghr.abs()
    s = Es.groupby("arm").agg(n=("absdev", "size"), max_abs_dev=("absdev", "max"), n_dev_gt_1e4=("absdev", lambda v: int((v > 1e-4).sum())),
                              same_pairs=("same_pairs", "sum")).reset_index()
    (OUT / "audit_v14.md").write_text(E.md(R, 4) + "\n\n" + E.md(s, 6) + "\n")


def figs(M, AM, U, plt):
    col = {"base": "#2a78d6", "ECG": "#eb6834", "shufECG": "#1baf7a", "noise": "#eda100"}
    mk = {"base": "o", "ECG": "s", "shufECG": "^", "noise": "D"}
    lab = {"base": "base", "ECG": "base + ECG (32 PCs)", "shufECG": "base + shuffled ECG", "noise": "base + noise32"}
    mets = [("absd", "mean |Δlog HR| vs RCT"), ("z2", "mean z²"), ("cons", "consistency (% |z|<1.96)"),
            ("mean_smd", "mean held-out |SMD|"), ("cstat", "held-out C-statistic")]
    fig, ax = plt.subplots(len(mets), 2, figsize=(11, 17), sharex=True)
    full = AM[AM.half == "full"]
    Mf = M[M.half == "full"]
    for j, base in enumerate(BASES):
        for i, (m, yl) in enumerate(mets):
            a = ax[i, j]
            for role in ("base", "ECG", "shufECG", "noise"):
                x = full[(full.base == base) & (full.arm_role == role)].sort_values("p")
                a.plot(x.p, x[m], color=col[role], marker=mk[role], lw=2, ms=6, label=lab[role])
            u = U[U.half == "full"][m].mean() * (100 if m == "cons" else 1)
            a.axhline(u, color="#8a8984", ls="--", lw=1, label="unmatched")
            if m != "cons":
                mm = Mf[Mf.base == base].sort_values("p")
                e = full[(full.base == base) & (full.arm_role == "ECG")].sort_values("p")
                for (_, r), yv in zip(mm.iterrows(), e[m]):
                    pv = r[f"p_{m}"]
                    a.annotate(f"p={fmt_p(pv)}" + ("*" if r[f"spec_{m}"] else ""), (r.p, yv), textcoords="offset points",
                               xytext=(0, 8), ha="center", fontsize=7, color="#52514e")
            a.set_ylabel(yl)
            a.grid(alpha=0.25, lw=0.5)
            for s in ("top", "right"):
                a.spines[s].set_visible(False)
            if i == 0:
                a.set_title(f"base = {base}")
            if i == len(mets) - 1:
                a.set_xlabel("code dropout probability p")
    ax[0, 0].legend(fontsize=8, frameon=False)
    fig.suptitle("S2 code sparsity (18 trials, full cohort, mean over 3 degradation seeds)\n"
                 "labels: sign-flip p for ECG vs base; * = p<0.05 and ECG beats both placebos in direction", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(DOCS / "S2_DROPOUT_curve.png", dpi=130)
    plt.close(fig)
    # heat map: d and p (ECG vs base) across cells x halves
    rowsl = [(b, h) for b in BASES for h in HALVES]
    fig, ax = plt.subplots(1, 4, figsize=(18, 5.5))
    for k, m in enumerate(METRICS):
        Z = np.full((len(rowsl), len(PS)), np.nan)
        Tx = [[""] * len(PS) for _ in rowsl]
        for i, (b, h) in enumerate(rowsl):
            for jj, p in enumerate(PS):
                r = M[(M.base == b) & (M.half == h) & (np.isclose(M.p, p))]
                if len(r):
                    r = r.iloc[0]
                    Z[i, jj] = r[f"d_{m}"]
                    Tx[i][jj] = f"{r[f'd_{m}']:.3g}\np={fmt_p(r[f'p_{m}'])}" + ("*" if r[f"spec_{m}"] else "")
        vmax = np.nanmax(np.abs(Z)) or 1
        im = ax[k].imshow(Z, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
        for i in range(len(rowsl)):
            for jj in range(len(PS)):
                ax[k].text(jj, i, Tx[i][jj], ha="center", va="center", fontsize=6.5,
                           color="white" if np.isfinite(Z[i, jj]) and abs(Z[i, jj]) > 0.6 * vmax else "#0b0b0b")
        ax[k].set_xticks(range(len(PS)), [f"{p:g}" for p in PS])
        ax[k].set_yticks(range(len(rowsl)), [f"{b} / {h}" for b, h in rowsl] if k == 0 else [""] * len(rowsl))
        ax[k].set_title(f"d_{m} (ECG − base)")
        ax[k].set_xlabel("dropout p")
        fig.colorbar(im, ax=ax[k], fraction=0.04)
    fig.suptitle("S2: ECG − base (negative / blue = ECG better); p = sign-flip over 18 trials; * = also beats shufECG and noise32 in direction", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(DOCS / "S2_DROPOUT_heatmap.png", dpi=130)
    plt.close(fig)


def write_md(M, AM, C, Cb, Cn, U, df):
    # placeholder: markdown is assembled by hand-written sections + generated tables
    L = []
    def tab(x, cols, nd=3):
        x = x[cols].copy()
        return E.md(x, nd)
    for h in HALVES:
        x = M[M.half == h].copy()
        for m in METRICS:
            x[m] = [f"{d:+.3f} ({k}; p={fmt_p(p)}" + (f"; q={fmt_p(q)}" if h == "full" else "") + ")" + (" **S**" if s else "")
                    for d, k, p, q, s in zip(x[f"d_{m}"], x[f"k_{m}"], x[f"p_{m}"], x[f"q_{m}"], x[f"spec_{m}"])]
        L.append(f"### ECG vs base, half = {h}\n\nEntry: d (trials ECG better / n; sign-flip p" + ("; BH q over 12 cells" if h == "full" else "") +
                 "). **S** = ECG-specific significant (p<0.05, and ECG beats shufECG and noise32 in direction).\n")
        L.append(tab(x, ["base", "p", "n_trials"] + METRICS) + "\n")
    for h in HALVES:
        x = M[M.half == h].copy()
        for m in METRICS:
            x[m] = [f"{a:+.3f} (p={fmt_p(b)}) / {c:+.3f} (p={fmt_p(d)})" for a, b, c, d in
                    zip(x[f"d_{m}_vs_shuf"], x[f"p_{m}_vs_shuf"], x[f"d_{m}_vs_noise"], x[f"p_{m}_vs_noise"])]
        L.append(f"### ECG vs placebos, half = {h} (ECG − shufECG / ECG − noise32)\n")
        L.append(tab(x, ["base", "p"] + METRICS) + "\n")
    x = M[M.half == "full"].copy()
    for m in METRICS:
        x[m] = [f"d {a:+.3f}..{b:+.3f}; p {fmt_p(c)}..{fmt_p(d)}" for a, b, c, d in
                zip(x[f"min_d_{m}"], x[f"max_d_{m}"], x[f"min_p_{m}"], x[f"max_p_{m}"])]
    L.append("### Seed spread (full cohort): range over the 3 degradation seeds of the per-seed ECG − base d and p (E.summarize_pairs)\n")
    L.append(tab(x, ["base", "p"] + METRICS) + "\n")
    for h in HALVES:
        a = AM[(AM.half == h)].copy()
        a = a[a.arm_role != "unmatched"]
        a["p"] = a.p.astype(float)
        a = a.sort_values(["base", "p", "arm_role"], key=lambda s: s.map({"sparse": 0, "hdPS200": 1, "base": 0, "ECG": 1, "shufECG": 2, "noise": 3}) if s.name in ("base", "arm_role") else s)
        L.append(f"### Arm means across trials (seed-averaged), half = {h}\n")
        L.append(E.md(a[["base", "p", "arm_role", "absd", "z2", "cons", "phi", "mean_smd", "cstat", "smd_prog", "n_pairs"]], 3) + "\n")
    u = U.groupby("half")[["absd", "z2", "cons", "mean_smd", "cstat", "smd_prog"]].mean().reset_index()
    u["cons"] *= 100
    L.append("### Unmatched reference (mean across trials)\n")
    L.append(E.md(u, 3) + "\n")
    (OUT / "generated_tables.md").write_text("\n".join(L))
    print("tables ->", OUT / "generated_tables.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["run", "summarize"])
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--out", default="results.csv")
    a = ap.parse_args()
    if a.mode == "run":
        run(a.trials.split(","), a.workers, a.out)
    else:
        summarize(a.out)


if __name__ == "__main__":
    main()
