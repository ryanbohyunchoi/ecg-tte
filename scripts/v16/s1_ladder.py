#!/usr/bin/env python
"""v1.6 sweep S1: baseline PS richness ladder (docs/V16_SWEEP_PLAN.md, exploratory).

Rungs (base designs); each run as base, base+ECG (32 BCL PCs), base+shufECG (same PCs, rows permuted with
T.shuffle_perm), base+noise32 (T.noise32).  Rung 0 "none": base = unmatched, "+ECG" = ECG PCs alone.
   1  demo            age, sex, index_year (T.demo)
   2  demo+race       + race_black, race_asian, race_other_unknown (White ref), hispanic, ethnicity_unknown
   3  min7            age, sex, race block, t2d, cad_ihd, hypertension_v11, hyperlipidemia (no index_year)
   3b min7+year       min7 + index_year
   4  min7+AF+HF      min7 + atrial_fibrillation, heart_failure (T.cov, where present)
   5  sparse          T.X_dx
   6  sparse+race+HLD sparse + race block + hyperlipidemia
   7  hdPS k          sparse + top-k hdPS levels, k in {25, 50, 100, 200} (ranked on the half's treatment)
   8  clinical        T.X_core
Estimator 1:1 greedy caliper-0.2 matching, L2 C=1 PS (engine defaults).  Halves: full, A, B (seeded split
stratified by treatment, rng 16060 + trial index).

Balance: engine 58-variable panel (mean_smd, cstat) plus
  mean_smd_ho / cstat_ho: restricted to panel variables NOT in the base design (only clinical overlaps:
      meds, util and observed vitals/labs of T.phys are in X_core);
  mean_smd_new: new v1.6 candidate held-out covariates (claude-v16-covars) not in (or proxied by) the base.
Matched sets for the extra balance metrics are obtained by replicating run_cell's PS fit + match
(v13_common.ps_logit / match; deterministic, checked against run_cell's n_pairs).

Usage: s1_ladder.py run [--trials a,b] [--workers 36] [--out DIR]   (writes DIR/results.csv)
       s1_ladder.py summarize [--out DIR] [--doc]                   (summaries, heat map, curve, markdown)
Aggregates only.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v16_engine as E  # noqa: E402
from v13_common import match, ps_logit  # noqa: E402
from v13_summarize import md  # noqa: E402

SWEEP = "s1-ladder"
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s1-ladder")
DOCS = HERE.parent.parent / "docs" / "v16"
COV = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars")
RACE = ["race_black", "race_asian", "race_other_unknown", "hispanic", "ethnicity_unknown"]
MIN7 = ["t2d", "cad_ihd", "hypertension_v11", "hyperlipidemia"]
NEW = ["tobacco_ever", "obesity", "frailty_count", "inpatient_days_365", "prior_hf_hosp_365",
       "race_black", "race_asian", "race_other_unknown", "hispanic", "hyperlipidemia", "t2d"]
HDK = [25, 50, 100, 200]
# (cell id, rung position for the curve, label)
CELLS = [("r0_none", 0, "none (ECG only)"), ("r1_demo", 1, "demo"), ("r2_demo+race", 2, "demo+race"),
         ("r3_min7", 3, "minimal-7"), ("r3b_min7+year", 3.5, "minimal-7+year"), ("r4_min7+AF+HF", 4, "min-7+AF+HF"),
         ("r5_sparse", 5, "sparse"), ("r6_sparse+race+HLD", 6, "sparse+race+HLD")] + \
        [(f"r7_hdPS{k}", 7 + i * 0.5, f"hdPS{k}") for i, k in enumerate(HDK)] + [("r8_clinical", 9, "clinical")]
CELL_POS = {c: p for c, p, _ in CELLS}
CELL_LAB = {c: lab for c, _, lab in CELLS}
ROLES = ["base", "ECG", "shufECG", "noise"]
METRICS = ["absd", "z2", "mean_smd", "cstat", "mean_smd_ho", "cstat_ho", "mean_smd_new", "mean_smd_new4"]
NEW4 = ["tobacco_ever", "obesity", "frailty_count", "prior_hf_hosp_365"]  # held out from every rung


def halves(T, i):
    """full / A / B row positions; A/B = seeded split stratified by treatment."""
    rng = np.random.default_rng(16060 + i)
    A = []
    for g in (0, 1):
        idx = np.where(T.t == g)[0]
        idx = idx[rng.permutation(len(idx))]
        A.append(idx[: len(idx) // 2])
    A = np.sort(np.concatenate(A))
    B = np.setdiff1d(np.arange(len(T.t)), A)
    return {"full": np.arange(len(T.t)), "A": A, "B": B}


def load_new(T):
    C = pd.read_parquet(COV / f"{T.n}.parquet").set_index("patient_key").reindex(T.keys)
    assert C.treated.astype(int).to_numpy().tolist() == T.t.tolist()
    return C


def base_designs(T, C, rows, t):
    """cell -> (X or None, held-out 58-panel VARS set excluded, new-variable list excluded)."""
    cov = T.cov.iloc[rows]
    race = C[RACE].to_numpy(float)[rows]
    age_sex = cov[["age_at_index", "male"]].to_numpy(float)
    m7 = np.hstack([age_sex, race, C[MIN7].to_numpy(float)[rows]])
    afhf = [c for c in ("atrial_fibrillation", "heart_failure") if c in T.cov]
    dx = T.X_dx[rows]
    H = T.hd(200, t=t, rows=rows)
    race_new = ["race_black", "race_asian", "race_other_unknown", "hispanic"]
    # new-variable exclusion: in the base or a near-identical proxy (sparse `diabetes` ~ t2d)
    dx_new = ["t2d"]
    core_new = dx_new + (["inpatient_days_365"] if "hospital_admissions" in T.cov else [])
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    d = {"r0_none": (None, set(), []),
         "r1_demo": (cov[T.demo].to_numpy(float), set(), []),
         "r2_demo+race": (np.hstack([cov[T.demo].to_numpy(float), race]), set(), race_new),
         "r3_min7": (m7, set(), race_new + ["t2d", "hyperlipidemia"]),
         "r3b_min7+year": (np.hstack([m7, cov[["index_year"]].to_numpy(float)]), set(), race_new + ["t2d", "hyperlipidemia"]),
         "r4_min7+AF+HF": (np.hstack([m7, cov[afhf].to_numpy(float)]), set(), race_new + ["t2d", "hyperlipidemia"]),
         "r5_sparse": (dx, set(), dx_new),
         "r6_sparse+race+HLD": (np.hstack([dx, race, C[["hyperlipidemia"]].to_numpy(float)[rows]]), set(),
                                dx_new + race_new + ["hyperlipidemia"]),
         "r8_clinical": (T.X_core[rows], clin_ex, core_new)}
    for k in HDK:
        d[f"r7_hdPS{k}"] = (np.hstack([dx, H[:, :k]]), set(), dx_new)
    return d


def extra_balance(T, X, rows, t, Hsub, Vnew):
    """Replicate run_cell's PS + match; return (n_pairs, cstat_ho or None, new-variable |SMD| vector)."""
    if X is None:
        s_idx, s_w = np.arange(len(rows)), np.ones(len(rows))
        npairs = np.nan
    else:
        lg = ps_logit(np.asarray(X, float), t, model="l2", C=1.0, seed=0)
        s_idx, cl, s_w = match(lg, t, cal=0.2, ratio=1)
        npairs = int(len(np.unique(cl)))
    s_t = t[s_idx]
    cs = None if Hsub is None else E.balance_cstat(Hsub[s_idx], s_t, s_w, model=("l2", 0.01), seed=0)
    new = E.smd_components(Vnew, t, s_idx, s_w, s_t)
    return npairs, cs, new


def run_trial_half(args):
    n, half = args
    t0 = time.time()
    i = E.TRIALS.index(n)
    T = E.load_trial(n)
    C = load_new(T)
    rows = halves(T, i)[half]
    t = T.t[rows]
    Vnew_all = C[NEW].to_numpy(float)[rows]
    D = base_designs(T, C, rows, t)
    pc = T.ecg_pc[rows]
    placebo = {"ECG": pc, "shufECG": T.ecg_pc[T.shuffle_perm][rows], "noise": T.noise32[rows]}
    Hfull = T.H
    out = []

    def one(cell, role, label, X, ex58, exnew):
        r = E.run_cell(T, X, rows=rows)
        ho = [c for c, _, _ in E.VARS if c not in ex58]
        r["mean_smd_ho"] = float(pd.Series({c: r[f"smd:{c}"] for c in ho}).mean())
        r["n_vars_ho"] = int(pd.Series({c: r[f"smd:{c}"] for c in ho}).notna().sum())
        Hsub = None
        if ex58:
            vc = E.var_components(Hfull)
            drop = {x for c in ex58 for x in vc[c]}
            Hsub = Hfull[[c for c in Hfull.columns if c not in drop]].to_numpy(float)[rows]
        npairs, cs, new = extra_balance(T, X, rows, t, Hsub, Vnew_all)
        if not (np.isnan(npairs) and np.isnan(r["n_pairs"])) and npairs != r["n_pairs"]:
            raise RuntimeError(f"match replication mismatch {n} {half} {cell} {role}: {npairs} vs {r['n_pairs']}")
        r["cstat_ho"] = r["cstat"] if cs is None else cs
        keep = [j for j, v in enumerate(NEW) if v not in exnew]
        for j, v in enumerate(NEW):
            r[f"smdnew:{v}"] = float(new[j]) if j in keep else np.nan
        kv = new[keep]
        r["mean_smd_new"] = float(np.nanmean(kv)) if np.isfinite(kv).any() else np.nan
        r["n_vars_new"] = int(np.isfinite(kv).sum())
        out.append(dict(sweep=SWEEP, cell=cell, rung=CELL_POS.get(cell, -1), rung_label=CELL_LAB.get(cell, cell),
                        trial=n, half=half, arm_role=role, arm_label=label, **r, rb=T.rb, rs=T.rs))

    one("unmatched", "unmatched", "unmatched", None, set(), [])
    for cell, (X, ex58, exnew) in D.items():
        lab = CELL_LAB[cell]
        if X is None:
            one(cell, "base", "unmatched", None, ex58, exnew)
            for role, P in placebo.items():
                one(cell, role, f"{role} only", P, ex58, exnew)
        else:
            one(cell, "base", lab, X, ex58, exnew)
            for role, P in placebo.items():
                one(cell, role, f"{lab}+{role}", np.hstack([X, P]), ex58, exnew)
    print(f"{n} {half} done {time.time() - t0:.0f}s", flush=True)
    return out


def run(trials, workers, out):
    from multiprocessing import Pool
    os.umask(0o077)
    out.mkdir(parents=True, exist_ok=True)
    tasks = [(n, h) for n in trials for h in ("full", "A", "B")]
    # biggest trials first for load balance
    size = {n: len(E.load_trial(n).t) for n in trials}
    tasks.sort(key=lambda x: -size[x[0]])
    with Pool(min(workers, len(tasks), 40)) as p:
        res = p.map(run_trial_half, tasks, chunksize=1)
    df = pd.DataFrame([r for rr in res for r in rr])
    df.to_csv(out / "results.csv", index=False)
    print("wrote", out / "results.csv", df.shape)


# ---------------------------------------------------------------- summaries
def pairs(df, a, b, half):
    """E.summarize_pairs over cells for metrics absd, z2 and all balance metrics (via column substitution)."""
    g = df[(df.half == half) & df.arm_role.isin([a, b])].copy()
    g["arm"] = g.arm_role
    base = E.summarize_pairs(g[["cell", "trial", "arm", "loghr", "se", "rb", "rs", "mean_smd", "cstat"]], ["cell"], a, b)
    for m in ("mean_smd_ho", "cstat_ho", "mean_smd_new", "mean_smd_new4"):
        h = g[["cell", "trial", "arm", "loghr", "se", "rb", "rs"]].assign(mean_smd=g[m])
        s = E.summarize_pairs(h, ["cell"], a, b)[["cell", "d_mean_smd", "k_mean_smd", "p_mean_smd"]]
        base = base.merge(s.rename(columns={"d_mean_smd": f"d_{m}", "k_mean_smd": f"k_{m}", "p_mean_smd": f"p_{m}"}), on="cell")
    base["half"] = half
    base["rung"] = base.cell.map(CELL_POS)
    return base.sort_values("rung").reset_index(drop=True)


def summarize(out, doc):
    df = pd.read_csv(out / "results.csv")
    df["mean_smd_new4"] = df[[f"smdnew:{v}" for v in NEW4]].mean(1)
    S = []
    for half in ("full", "A", "B"):
        for b in ("base", "shufECG", "noise"):
            S.append(pairs(df, "ECG", b, half))
    S = pd.concat(S, ignore_index=True)
    S["comparison"] = "ECG vs " + S.arm_b
    full_eb = (S.half == "full") & (S.arm_b == "base")
    for m in METRICS:
        S.loc[full_eb, f"q_{m}"] = E.bh_fdr(S.loc[full_eb, f"p_{m}"])
    S.to_csv(out / "summary_pairs.csv", index=False)
    # verdict table per cell x metric
    V = []
    for cell in [c for c, _, _ in CELLS]:
        for m in METRICS:
            row = dict(cell=cell, metric=m)
            for half in ("full", "A", "B"):
                for b in ("base", "shufECG", "noise"):
                    s = S[(S.cell == cell) & (S.half == half) & (S.arm_b == b)].iloc[0]
                    row[f"d_{b}_{half}"], row[f"p_{b}_{half}"] = s[f"d_{m}"], s[f"p_{m}"]
                    if b == "base":
                        row[f"k_{half}"] = s[f"k_{m}"]
            row["q_full"] = S[(S.cell == cell) & full_eb][f"q_{m}"].iloc[0]
            f = row
            row["sig_full"] = bool(f["p_base_full"] < 0.05)
            row["placebo_ok"] = bool(f["d_shufECG_full"] < 0 and f["d_noise_full"] < 0 and f["d_base_full"] < 0)
            row["ecg_specific"] = row["sig_full"] and row["placebo_ok"]
            row["fdr_ok"] = bool(row["q_full"] < 0.05)
            same = np.sign(f["d_base_A"]) == np.sign(f["d_base_full"]) == np.sign(f["d_base_B"])
            row["repl_dir"] = bool(same)
            row["repl_sig"] = bool(same and f["p_base_A"] < 0.05 and f["p_base_B"] < 0.05)
            V.append(row)
    V = pd.DataFrame(V)
    V.to_csv(out / "verdicts.csv", index=False)
    # per-arm level summaries (curve)
    df["absd"] = (df.loghr - df.rb).abs()
    df["z2"] = (df.loghr - df.rb) ** 2 / (df.se ** 2 + df.rs ** 2)
    df["cons"] = 100 * (np.sqrt(df.z2) < 1.96)
    L = df[df.arm_role != "unmatched"].groupby(["half", "cell", "arm_role"]).agg(
        absd=("absd", "mean"), z2_mean=("z2", "mean"), z2_median=("z2", "median"), cons=("cons", "mean"),
        mean_smd=("mean_smd", "mean"), mean_smd_ho=("mean_smd_ho", "mean"), cstat=("cstat", "mean"),
        cstat_ho=("cstat_ho", "mean"), mean_smd_new=("mean_smd_new", "mean"), mean_smd_new4=("mean_smd_new4", "mean"), n_pairs=("n_pairs", "median"),
        n_trials=("trial", "nunique")).reset_index()
    L["rung"] = L.cell.map(CELL_POS)
    L = L.sort_values(["half", "rung", "arm_role"])
    L.to_csv(out / "levels.csv", index=False)
    U = df[df.arm_role == "unmatched"].groupby("half").agg(absd=("absd", "mean"), z2_mean=("z2", "mean"),
                                                             cons=("cons", "mean"), mean_smd=("mean_smd", "mean"),
                                                             cstat=("cstat", "mean"), mean_smd_new=("mean_smd_new", "mean"),
                                                             mean_smd_new4=("mean_smd_new4", "mean"))
    NV = df[(df.half == "full") & (df.arm_role != "unmatched")]
    NVt = NV.groupby(["cell", "arm_role"])[[f"smdnew:{v}" for v in NEW]].mean().reset_index()
    NVt["rung"] = NVt.cell.map(CELL_POS)
    NVt = NVt.sort_values(["rung", "arm_role"]).drop(columns="rung")
    NVt.columns = [c.replace("smdnew:", "") for c in NVt.columns]
    NVt.to_csv(out / "new_vars_smd.csv", index=False)
    figs(S, L, U)
    if doc:
        write_md(df, S, V, L, U, NVt, out)


def figs(S, L, U):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    DOCS.mkdir(parents=True, exist_ok=True)
    col = {"base": "#2a78d6", "ECG": "#eb6834", "shufECG": "#1baf7a", "noise": "#eda100"}
    mk = {"base": "o", "ECG": "s", "shufECG": "^", "noise": "v"}
    cells = [c for c, _, _ in CELLS]
    x = np.arange(len(cells))
    labs = [CELL_LAB[c] for c in cells]
    F = L[L.half == "full"].set_index(["cell", "arm_role"])
    SB = S[(S.half == "full") & (S.arm_b == "base")].set_index("cell")
    panels = [("absd", "mean |Δlog HR| vs RCT", "absd"), ("z2_median", "median z² vs RCT", "z2"),
              ("cons", "% consistent with RCT (|z|<1.96)", None), ("mean_smd", "held-out mean |SMD| (58-var)", "mean_smd"),
              ("mean_smd_new4", "new held-out covariates (common 4) mean |SMD|", "mean_smd_new4"), ("cstat_ho", "held-out C-statistic", "cstat_ho")]
    fig, axs = plt.subplots(2, 3, figsize=(17, 9.5), sharex=True)
    for ax, (m, title, pm) in zip(axs.ravel(), panels):
        for role in ROLES:
            y = [F.loc[(c, role), m] if (c, role) in F.index else np.nan for c in cells]
            if role == "base":
                y[0] = np.nan  # rung 0 base = unmatched; shown as reference line
            ax.plot(x, y, marker=mk[role], color=col[role], lw=2 if role in ("base", "ECG") else 1.2, ms=7,
                    alpha=1 if role in ("base", "ECG") else 0.8, label={"base": "base", "ECG": "base + ECG (32 PCs)",
                                                                          "shufECG": "base + shuffled ECG", "noise": "base + noise32"}[role])
        um = {"absd": "absd", "z2_median": None, "cons": "cons", "mean_smd": "mean_smd", "mean_smd_new4": "mean_smd_new4",
              "cstat_ho": "cstat"}[m]
        if um and um in U:
            ax.axhline(U.loc["full", um], color="#52514e", ls=":", lw=1)
            ax.text(len(cells) - 0.5, U.loc["full", um], "unmatched", color="#52514e", fontsize=8, va="bottom", ha="right")
        if pm:
            yl = ax.get_ylim()
            for xi, c in zip(x, cells):
                p = SB.loc[c, f"p_{pm}"]
                d = SB.loc[c, f"d_{pm}"]
                s = f"{p:.2f}" if p >= 0.01 else f"{p:.3f}"
                ax.text(xi, yl[1], s, ha="center", va="bottom", fontsize=7,
                        color="#0b0b0b" if p < 0.05 else "#8a8984", fontweight="bold" if (p < 0.05 and d < 0) else "normal")
        ax.set_title(title, fontsize=10, pad=14)
        ax.grid(axis="y", color="#e6e5e0", lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    for ax in axs[1]:
        ax.set_xticks(x)
        ax.set_xticklabels(labs, rotation=50, ha="right", fontsize=8)
    h, lb = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, lb, loc="lower center", ncol=4, fontsize=9, frameon=False)
    fig.suptitle("S1 PS richness ladder (18 trials, full cohort, 1:1 caliper-0.2 matching). Numbers above panels: "
                 "sign-flip p, ECG vs base on paired per-trial differences (bold = ECG better & p<0.05)", fontsize=10)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(DOCS / "S1_LADDER_curve.png", dpi=140)
    plt.close(fig)
    # heat map: d and p across cells for absd, z2, mean_smd, cstat, per comparison, full + halves
    mets = ["absd", "z2", "mean_smd", "cstat", "mean_smd_new", "mean_smd_new4"]
    comps = [("full", "base"), ("full", "shufECG"), ("full", "noise"), ("A", "base"), ("B", "base")]
    fig, axs = plt.subplots(1, len(mets), figsize=(20, 6.5), sharey=True)
    for ax, m in zip(axs, mets):
        M = np.full((len(cells), len(comps)), np.nan)
        P = np.full_like(M, np.nan)
        for j, (h, b) in enumerate(comps):
            s = S[(S.half == h) & (S.arm_b == b)].set_index("cell")
            M[:, j] = s.loc[cells, f"d_{m}"]
            P[:, j] = s.loc[cells, f"p_{m}"]
        v = np.nanmax(np.abs(M))
        im = ax.imshow(M, cmap="RdBu_r", vmin=-v, vmax=v, aspect="auto")
        for i in range(len(cells)):
            for j in range(len(comps)):
                ax.text(j, i, f"{M[i, j]:+.3f}\np={P[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if abs(M[i, j]) > 0.6 * v else "black",
                        fontweight="bold" if P[i, j] < 0.05 else "normal")
        ax.set_xticks(range(len(comps)))
        ax.set_xticklabels([f"{b}\n{h}" for h, b in comps], fontsize=7)
        ax.set_title(f"d_{m} (ECG − comparator;\nblue = ECG better)", fontsize=9)
        fig.colorbar(im, ax=ax, shrink=0.6)
    axs[0].set_yticks(range(len(cells)))
    axs[0].set_yticklabels(labs, fontsize=8)
    fig.tight_layout()
    fig.savefig(DOCS / "S1_LADDER_heatmap.png", dpi=130)
    plt.close(fig)


def write_md(df, S, V, L, U, NVt, out):
    audit_f = out / "audit.md"
    audit = audit_f.read_text() if audit_f.exists() else "(audit section not found)"
    kf_f = out / "key_findings.md"  # hand-written interpretation of the numbers below
    keyf = kf_f.read_text() if kf_f.exists() else "(key findings not yet written)"
    cells = [c for c, _, _ in CELLS]
    F = S[S.half == "full"]
    eb = F[F.arm_b == "base"].set_index("cell").loc[cells]
    es = F[F.arm_b == "shufECG"].set_index("cell").loc[cells]
    en = F[F.arm_b == "noise"].set_index("cell").loc[cells]
    A_ = S[(S.half == "A") & (S.arm_b == "base")].set_index("cell").loc[cells]
    B_ = S[(S.half == "B") & (S.arm_b == "base")].set_index("cell").loc[cells]

    def ft(d, p):
        return f"{d:+.3f} (p={p:.3f})" if abs(d) < 10 else f"{d:+.1f} (p={p:.3f})"

    def mt(m):
        rows = []
        for c in cells:
            rows.append({"cell": CELL_LAB[c], "k better (full)": eb.loc[c, f"k_{m}"],
                         "ECG−base full": ft(eb.loc[c, f"d_{m}"], eb.loc[c, f"p_{m}"]),
                         "q (BH)": f"{eb.loc[c, f'q_{m}']:.3f}",
                         "ECG−shufECG": ft(es.loc[c, f"d_{m}"], es.loc[c, f"p_{m}"]),
                         "ECG−noise": ft(en.loc[c, f"d_{m}"], en.loc[c, f"p_{m}"]),
                         "half A": ft(A_.loc[c, f"d_{m}"], A_.loc[c, f"p_{m}"]),
                         "half B": ft(B_.loc[c, f"d_{m}"], B_.loc[c, f"p_{m}"])})
        return md(pd.DataFrame(rows), 3)

    def flag(m):
        v = V[V.metric == m].set_index("cell")
        out_ = []
        for c in cells:
            r = v.loc[c]
            tags = []
            if r.sig_full:
                tags.append("p<0.05" + ("(ECG better)" if r.d_base_full < 0 else "(ECG WORSE)"))
            if r.ecg_specific:
                tags.append("placebo-beating")
            if r.fdr_ok:
                tags.append("FDR q<0.05")
            if r.repl_sig:
                tags.append("replicated p<0.05 both halves")
            elif r.repl_dir:
                tags.append("same direction both halves")
            out_.append((c, tags))
        return out_

    # levels table (full)
    Lf = L[L.half == "full"].copy()
    lv = []
    for c in cells:
        r = {"cell": CELL_LAB[c]}
        for role in ROLES:
            x = Lf[(Lf.cell == c) & (Lf.arm_role == role)].iloc[0]
            r[f"absd {role}"] = x.absd
        for role in ("base", "ECG"):
            x = Lf[(Lf.cell == c) & (Lf.arm_role == role)].iloc[0]
            r[f"z2 med {role}"] = x.z2_median
            r[f"cons% {role}"] = x.cons
            r[f"smd58 {role}"] = x.mean_smd
            r[f"smdHO {role}"] = x.mean_smd_ho
            r[f"smdNEW {role}"] = x.mean_smd_new
            r[f"smdNEW4 {role}"] = x.mean_smd_new4
            r[f"C_HO {role}"] = x.cstat_ho
        r["pairs(med) base"] = Lf[(Lf.cell == c) & (Lf.arm_role == "base")].n_pairs.iloc[0]
        lv.append(r)
    lv = pd.DataFrame(lv)
    cons = eb[["cons_a", "phi_a", "cons_b", "phi_b"]].rename(columns={"cons_a": "cons% ECG", "phi_a": "phi ECG",
                                                                      "cons_b": "cons% base", "phi_b": "phi base"})
    cons.insert(0, "cell", [CELL_LAB[c] for c in cons.index])
    consp = pd.concat([cons.reset_index(drop=True),
                       es[["cons_b", "phi_b"]].rename(columns={"cons_b": "cons% shufECG", "phi_b": "phi shufECG"}).reset_index(drop=True),
                       en[["cons_b", "phi_b"]].rename(columns={"cons_b": "cons% noise", "phi_b": "phi noise"}).reset_index(drop=True)], axis=1)

    # key findings text
    kf = []
    for m, nm in (("absd", "|Δlog HR| vs RCT"), ("z2", "z²"), ("mean_smd", "held-out mean |SMD| (58-var)"),
                  ("cstat", "held-out C-statistic"), ("mean_smd_ho", "58-var |SMD| restricted to variables held out from that base"),
                  ("mean_smd_new", "new held-out covariates |SMD|"), ("mean_smd_new4", "common-4 new covariates |SMD|")):
        fl = flag(m)
        sig = [CELL_LAB[c] for c, t in fl if any(x.startswith("p<0.05(ECG better") for x in t)]
        spec = [CELL_LAB[c] for c, t in fl if "placebo-beating" in t]
        fdr = [CELL_LAB[c] for c, t in fl if "FDR q<0.05" in t and V[(V.metric == m) & (V.cell == c)].d_base_full.iloc[0] < 0]
        rep = [CELL_LAB[c] for c, t in fl if "replicated p<0.05 both halves" in t and V[(V.metric == m) & (V.cell == c)].d_base_full.iloc[0] < 0]
        full = [CELL_LAB[c] for c, t in fl if "placebo-beating" in t and "FDR q<0.05" in t and "replicated p<0.05 both halves" in t]
        worse = [CELL_LAB[c] for c, t in fl if any("WORSE" in x for x in t)]
        kf.append(f"- **{nm}**: ECG better at p<0.05 in {len(sig)}/{len(cells)} rungs ({', '.join(sig) or 'none'}); "
                  f"placebo-beating: {', '.join(spec) or 'none'}; BH q<0.05: {', '.join(fdr) or 'none'}; "
                  f"replicated (p<0.05 in both halves): {', '.join(rep) or 'none'}; **all four (sig + placebo + FDR + "
                  f"replicated): {', '.join(full) or 'none'}**" + (f"; ECG significantly WORSE: {', '.join(worse)}" if worse else "") + ".")
    Lpath = DOCS / "S1_LADDER.md"
    txt = [f"# v1.6 S1 — baseline PS richness ladder ({time.strftime('%Y-%m-%d')})\n",
           "**Exploratory, post-hoc specification (docs/V16_SWEEP_PLAN.md).** 18 trials; 1:1 greedy caliper-0.2 matching on an "
           "L2 (C=1) logistic PS; imputation 1, pool-split seed 0; primary outcome at trial horizon. ECG = 32 BCL PCs; placebos = "
           "same PCs with rows permuted (`shufECG`) and 32 Gaussian columns (`noise32`). Paired exact sign-flip across trials; "
           "d = mean over trials of (ECG arm − comparator), negative = ECG better. BH-FDR over the "
           f"{len(cells)} rungs per metric (ECG vs base, full cohort). Script `scripts/v16/s1_ladder.py`; "
           "aggregates in `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s1-ladder/`.\n",
           "## Key findings (plain language)\n", keyf + "\n",
           "Automatic flags per metric (a rung is *ECG-specific* only if ECG vs base p<0.05 and ECG also beats shufECG and "
           "noise32 in direction; *replicated* = p<0.05 in half A and half B, same direction):\n", "\n".join(kf) + "\n",
           "![S1 ladder curve](S1_LADDER_curve.png)\n",
           "Figure: x = PS richness rung; lines = mean over 18 trials per arm (median for z², which is heavy-tailed); dotted = "
           "unmatched. Rung 'none' = no baseline covariates: its '+ECG' point is ECG PCs alone (and placebos alone). Numbers above "
           "each panel = sign-flip p for ECG vs base at that rung (bold = ECG better and p<0.05). C-statistic panel uses the "
           "held-out-from-base component set (differs from the engine C only for clinical).\n",
           "![S1 heat map](S1_LADDER_heatmap.png)\n",
           "## Rungs (base designs)\n",
           "| cell | design |\n|---|---|\n"
           "| none (ECG only) | base = unmatched; +ECG = 32 ECG PCs alone |\n"
           "| demo | age, sex, index year (`T.demo`) |\n"
           "| demo+race | demo + race_black, race_asian, race_other_unknown (White reference), hispanic, ethnicity_unknown |\n"
           "| minimal-7 | age, sex, race block (as above), t2d, cad_ihd, hypertension_v11, hyperlipidemia (no index year) |\n"
           "| minimal-7+year | minimal-7 + index year |\n"
           "| min-7+AF+HF | minimal-7 + atrial_fibrillation, heart_failure flags from `T.cov` where present (heart_failure is absent in HF-population trials) |\n"
           "| sparse | `T.X_dx` (demo + v1.1 diagnosis flags) |\n"
           "| sparse+race+HLD | sparse + race block + hyperlipidemia |\n"
           "| hdPS k | sparse + top-k hdPS levels (pool A, ranked on the analysed rows' treatment), k = 25/50/100/200 |\n"
           "| clinical | `T.X_core` (demo, dx flags, medication orders, utilisation, imputed vitals/labs) |\n",
           "## Held-out balance definitions\n",
           "- `mean_smd` / `cstat`: engine 58-variable panel (all components) in the matched sample.\n"
           "- Overlap of the 58-panel with base designs: only **clinical** contains panel variables (`mean_meds`, `mean_util` and "
           "the 9 `smd_obs_*` vitals/labs are in `T.X_core`, as completed values). `mean_smd_ho` = mean over panel variables NOT "
           "in the base (47 for clinical, 58/57 otherwise); `cstat_ho` = C-statistic on components excluding those (identical to "
           "`cstat` for other rungs). The prognostic score and pool-B codes are treated as held-out for every rung. "
           "Race/HLD/T2D/CAD/HTN are not in the 58-panel. hdPS uses pool-A codes only; pool B is held out by construction.\n"
           f"- `mean_smd_new`: |SMD| on the v1.6 candidate covariates ({', '.join(NEW)}), matched sample, pooled pre-match SD of "
           "the analysed rows (as the engine). Excluded when in the base or proxied by it: race vars + hyperlipidemia + t2d in "
           "demo+race/min-7 rungs (race only for demo+race), t2d in any rung containing the sparse `diabetes` flag, "
           "`inpatient_days_365` in clinical (proxied by `hospital_admissions`). `prior_hf_hosp_365` kept even where a "
           "heart_failure flag is in the PS (different construct: hospitalisation).\n",
           "## Results by metric (ECG vs base, and placebos; full cohort + halves)\n"]
    for m, nm in (("absd", "|Δlog HR| vs RCT"), ("z2", "z² = Δ²/(se²+se_RCT²)"), ("mean_smd", "held-out mean |SMD|, 58-var panel"),
                  ("cstat", "held-out C-statistic (engine)"), ("mean_smd_ho", "58-var |SMD|, held-out-from-base subset"),
                  ("cstat_ho", "held-out C-statistic, held-out-from-base components"), ("mean_smd_new", "new candidate covariates mean |SMD| (rung-specific set)"),
                  ("mean_smd_new4", "common-4 new covariates mean |SMD| (tobacco_ever, obesity, frailty_count, prior_hf_hosp_365)")):
        txt += [f"### {nm}\n", mt(m) + "\n"]
    txt += ["## Arm levels (full cohort; mean over trials)\n",
            "absd = mean |Δlog HR|; z2 med = median z²; smd58 = 58-panel mean |SMD|; smdHO = held-out-from-base subset; "
            "smdNEW = new covariates; C_HO = held-out C-statistic.\n", md(lv, 3) + "\n",
            "Unmatched reference (mean over trials, by half):\n", md(U.reset_index(), 3) + "\n",
            "## Consistency % and dispersion φ per arm (full)\n", md(consp, 2) + "\n",
            "## New candidate covariates: mean |SMD| per variable (full cohort, mean over trials; NaN = in/proxied by base)\n",
            md(NVt, 3) + "\n",
            "## Audit\n", audit + "\n",
            "## Limitations\n",
            "Exploratory: rungs and metrics chosen after v1.3–v1.5. One imputation, one pool split; halves are patient splits of "
            "the same trials (not independent trials). Sign-flip tests use 18 trials (smallest attainable p ≈ 7.6e-6). "
            "hdPS rungs are nested (k=25 ⊂ 50 ⊂ ...) and share matched-sample structure, so the rung tests are correlated; "
            "BH assumes PRDS. External confirmation (MIMIC/UKB) deferred.\n"]
    Lpath.write_text("\n".join(txt))
    print("wrote", Lpath)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["run", "summarize"])
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=36)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--doc", action="store_true")
    a = ap.parse_args()
    os.umask(0o077)
    if a.mode == "run":
        run(a.trials.split(","), a.workers, Path(a.out))
    else:
        summarize(Path(a.out), a.doc)


if __name__ == "__main__":
    main()
