#!/usr/bin/env python
"""v2.0 echo-subset analysis (plan: docs/v20/ECHO_SUBSET_PLAN.md, committed e098888 before any result).

Real-data counterpart of the plasmode.  Within patients with a measured physiological confounder (E: echo LVEF;
N: NT-proBNP), how much of the shift in the emulated log HR produced by adding the measured physiology to the PS is
reproduced by adding the ECG embedding instead?
  num_i = logHR_base - logHR_base+ECG;  den_i = logHR_base - logHR_base+phys
  F = sum(num*den) / sum(den^2)  (slope through the origin), placebo-corrected F - F_permutedECG; trial bootstrap CIs.
Bases: P1 (primary), P5, hdPS200 (re-ranked within the subset), clinical minus the physiology analogue(s).
Engine: v16_engine.run_cell (L2 logistic C = 1, 1:1 greedy caliper 0.2, pair-clustered Cox).

Usage: echo_subset.py run [--workers 10] [--trials a,b] | summarize
Outputs (aggregates only, umask 077): /mnt/raid0/rbc58/ecg-tte/audits/claude-v20-echo-subset/
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
ROOT = HERE.parent.parent
for p in ("v19", "v18", "v16", ""):
    sys.path.insert(0, str(HERE.parent / p) if p else str(HERE.parent))
import v18_af_confirm as AF  # noqa: E402  (38-trial ALL; installs S8._LAST capture via v17_confirm)
import v18_clmbr as CL  # noqa: E402
from g2_simulation import CONF, clean_c, cv_r2  # noqa: E402

V = AF.V
E, S8 = V.E, V.S8
A = V.A
OUT = Path(os.environ.get("ES_OUT", str(A / "claude-v20-echo-subset")))
DOCS = ROOT / "docs" / "v20"
ALL, OLD, AF5 = list(AF.ALL), list(V.OLD), list(AF.AF5)
MIN_ARM, MIN_EV, MIN_CELL = 300, 50, 11
SUBSETS = {"E": "lvef", "N": "ntprobnp"}
PHYS4 = ["lvef", "ntprobnp", "bmi", "egfr"]
ANALOGUE = {"lvef": "lvef", "ntprobnp": None, "bmi": "bmi", "egfr": "creatinine"}
NBOOT, SEED = 2000, 20261001


def tiers():
    q = json.load(open(ROOT / "docs/v19/quality_tiers.json"))["trials"]
    m = {x["registry"]: x["tier"].split(" ")[0] for x in q}
    missing = [n for n in ALL if n not in m]
    assert not missing, missing
    return m


def zs(v):
    return (v - np.nanmean(v)) / np.nanstd(v)


def phys_ext(vals, r):
    cols = []
    for c in PHYS4:
        v = vals[c][r].copy()
        miss = np.isnan(v)
        if miss.all():
            continue
        v[miss] = np.nanmedian(v)
        cols.append(zs(v))
        if miss.any():
            cols.append(miss.astype(float))
    return np.column_stack(cols)


def task(n):
    t0 = time.time()
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    i = ALL.index(n)
    # reproduction gate: full-cohort P1 base
    X1f = T.cov[T.demo].to_numpy(float)
    o = E.run_cell(T, X1f, estimator=("match", 0.2, 1), cstat=None)
    ref = pd.read_csv(A / ("claude-v18-af-confirm/results_af5.csv" if n in AF5 else "claude-v17-confirm/results_all.csv"))
    ref = ref[(ref.trial == n) & (ref.half == "full") & (ref.ps == "P1") & (ref.arm_role == "base")]
    gate = dict(trial=n, engine_loghr=o["loghr"], ref_loghr=float(ref.loghr.iloc[0]) if len(ref) else np.nan)
    gate["absdev"] = abs(gate["engine_loghr"] - gate["ref_loghr"])
    b5, _, _ = CL.designs(T, n, CL.P5DX)
    vals = {c: clean_c(T, c) for c in PHYS4}
    P4 = np.column_stack([vals[c] for c in PHYS4])
    core = list(T.core)
    ecg, shuf, noise = T.ecg_pc, T.ecg_pc[T.shuffle_perm], T.noise32
    rows, elig = [], []
    for sub, dc in SUBSETS.items():
        S = T.y_ok & ~np.isnan(vals[dc])
        r = np.where(S)[0]
        t = T.t[r]
        nt, nc, ev = int(t.sum()), int((1 - t).sum()), int(T.y_e[r].sum())
        ok = min(nt, nc) >= MIN_ARM and ev >= MIN_EV
        elig.append(dict(trial=n, subset=sub, n=len(r), n_t=nt, n_c=nc, events=ev, obs_frac=float(S.mean()), eligible=ok))
        if not ok:
            continue
        p1 = zs(vals[dc][r])[:, None]
        px = phys_ext(vals, r)
        X1 = X1f[r]
        hd = np.hstack([T.X_dx[r], T.hd(200, t=t, rows=r)])
        Xc = T.X_core[r]
        drop1 = {ANALOGUE[dc]} - {None}
        dropx = {ANALOGUE[c] for c in PHYS4} - {None}
        c1 = [j for j, k in enumerate(core) if k not in drop1]
        cx = [j for j, k in enumerate(core) if k not in dropx]
        bases = {"P1": (X1, ("single", "ext")), "P5": (b5[r], ("single", "ext")), "hdPS200": (hd, ("single", "ext")),
                 "clinical": (Xc[:, c1], ("single",)), "clinical_ext": (Xc[:, cx], ("ext",))}
        z = zs(vals[dc][r])
        for rg, (B, psets) in bases.items():
            arms = {"base": B, "ECG": np.hstack([B, ecg[r]]), "shufECG": np.hstack([B, shuf[r]]), "noise32": np.hstack([B, noise[r]])}
            if "single" in psets:
                arms["phys1"] = np.hstack([B, p1])
            if "ext" in psets:
                arms["physX"] = np.hstack([B, px])
            r2b, r2be = cv_r2(B, z), cv_r2(np.hstack([B, ecg[r]]), z)
            for a, X in arms.items():
                S8._LAST.clear()
                try:
                    oc = E.run_cell(T, X, rows=r, estimator=("match", 0.2, 1), cstat=None)
                    s_idx, s_w = S8._LAST["m"]
                    smd = E.smd_components(P4[r], t, s_idx, s_w, t[s_idx])
                except Exception as ex:  # logged, cell excluded
                    oc, smd = dict(loghr=np.nan, se=np.nan, n=len(r), n_t=nt, n_c=nc, n_pairs=np.nan, err=str(ex)[:120]), [np.nan] * 4
                rows.append(dict(trial=n, key=T.key, idx=i, subset=sub, rung=rg, arm=a, loghr=oc["loghr"], se=oc["se"],
                                 n=oc["n"], n_t=oc["n_t"], n_c=oc["n_c"], n_pairs=oc["n_pairs"], err=oc.get("err", ""),
                                 rb=T.rb, rs=T.rs, r2_base=r2b, r2_base_ecg=r2be,
                                 r2_partial=(r2be - r2b) / (1 - r2b) if r2b < 1 else np.nan,
                                 **{f"asmd_{c}": abs(v) for c, v in zip(PHYS4, smd)}))
    print(f"{n} {time.time() - t0:.0f}s gate {gate['absdev']:.2e}", flush=True)
    return gate, elig, rows


def suppress(D, cols):
    D = D.copy()
    for c in cols:
        if c in D:
            v = pd.to_numeric(D[c], errors="coerce")
            D.loc[(v >= 1) & (v < MIN_CELL), c] = np.nan
    return D


def run(trials, workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(min(workers, len(trials))) as p:
        res = p.map(task, trials, chunksize=1)
    G = pd.DataFrame([g for g, _, _ in res])
    El = pd.DataFrame([e for _, ee, _ in res for e in ee])
    R = pd.DataFrame([x for _, _, rr in res for x in rr])
    G.to_csv(OUT / "gate.csv", index=False)
    suppress(El, ["n", "n_t", "n_c", "events"]).to_csv(OUT / "eligibility.csv", index=False)
    suppress(R, ["n", "n_t", "n_c", "n_pairs"]).to_csv(OUT / "per_trial.csv", index=False)
    print("gate max absdev", G.absdev.max(), "cells", len(R), "errors", int((R.err.astype(str) != "").sum()) if len(R) else 0)


# ---------------------------------------------------------------- summarize
def slope(num, den):
    return float(np.sum(num * den) / np.sum(den ** 2))


def boot(fn, k, rng):
    return np.array([fn(rng.integers(0, k, k)) for _ in range(NBOOT)])


def pooled(R, sub, rg, phys, trials):
    W = R[(R.subset == sub) & (R.rung == rg) & R.trial.isin(trials)].pivot_table(index="trial", columns="arm", values="loghr")
    need = ["base", "ECG", "shufECG", "noise32", phys]
    if not set(need) <= set(W.columns):
        return None
    W = W[need].dropna()
    k = len(W)
    if k < 3:
        return dict(k=k)
    den = (W.base - W[phys]).to_numpy()
    nums = {a: (W.base - W[a]).to_numpy() for a in ("ECG", "shufECG", "noise32")}
    r2 = R[(R.subset == sub) & (R.rung == rg) & (R.arm == "base")].set_index("trial").r2_partial.reindex(W.index).to_numpy()
    rng = np.random.default_rng(SEED)
    out = dict(k=k, mean_abs_den=float(np.mean(np.abs(den))), mean_abs_num_ecg=float(np.mean(np.abs(nums["ECG"]))),
               corr_ecg=float(np.corrcoef(nums["ECG"], den)[0, 1]))
    for a, nu in nums.items():
        out[f"F_{a}"] = slope(nu, den)
        b = boot(lambda ix: slope(nu[ix], den[ix]), k, rng)
        out[f"F_{a}_lo"], out[f"F_{a}_hi"] = np.percentile(b, [2.5, 97.5])
        out[f"aligned_{a}"] = float(np.sum(nu * np.sign(den)) / np.sum(np.abs(den)))
    d = lambda ix: slope(nums["ECG"][ix], den[ix]) - slope(nums["shufECG"][ix], den[ix])
    out["F_corr"] = d(np.arange(k))
    b = boot(d, k, rng)
    out["F_corr_lo"], out["F_corr_hi"] = np.percentile(b, [2.5, 97.5])
    w = den ** 2
    out["r2_partial_w"] = float(np.nansum(w * r2) / np.nansum(w[~np.isnan(r2)])) if phys == "phys1" else np.nan
    out["r2_partial_median"] = float(np.nanmedian(r2)) if phys == "phys1" else np.nan
    # descriptive: distance to the RCT and balance on the defining variable
    rb = R[(R.subset == sub) & (R.rung == rg) & (R.arm == "base")].set_index("trial").rb.reindex(W.index).to_numpy()
    for a in ("base", "ECG", "shufECG", phys):
        out[f"absd_rct_{a}"] = float(np.mean(np.abs(W[a].to_numpy() - rb)))
    dc = SUBSETS[sub]
    S = R[(R.subset == sub) & (R.rung == rg) & R.trial.isin(W.index)].groupby("arm")[f"asmd_{dc}"].mean()
    for a in ("base", "ECG", "shufECG", phys):
        out[f"asmd_def_{a}"] = float(S.get(a, np.nan))
    return out


def summarize():
    R = pd.read_csv(OUT / "per_trial.csv")
    G = pd.read_csv(OUT / "gate.csv")
    El = pd.read_csv(OUT / "eligibility.csv")
    tier = tiers()
    sets = {"32": [n for n in ALL if tier[n] != "Limited"], "38": ALL}
    rows = []
    for sn, tr in sets.items():
        for sub in SUBSETS:
            for rg in ("P1", "P5", "hdPS200", "clinical", "clinical_ext"):
                for phys in ("phys1", "physX"):
                    o = pooled(R, sub, rg, phys, tr)
                    if o is not None:
                        rows.append(dict(set=sn, subset=sub, rung=rg, phys=phys, **o))
    P = pd.DataFrame(rows)
    P.to_csv(OUT / "pooled.csv", index=False)
    json.dump(dict(gate_max_absdev=float(G.absdev.max()), gate_n=int(len(G)),
                   eligible={s: int(El[(El.subset == s) & El.eligible].shape[0]) for s in SUBSETS},
                   eligible32={s: int(El[(El.subset == s) & El.eligible & El.trial.isin(sets["32"])].shape[0]) for s in SUBSETS},
                   errors=int((R.err.fillna("").astype(str) != "").sum())),
              open(OUT / "summary.json", "w"), indent=1)
    figure(R, sets["32"])
    print(P[["set", "subset", "rung", "phys", "k", "F_ECG", "F_ECG_lo", "F_ECG_hi", "F_shufECG", "F_corr", "F_corr_lo", "F_corr_hi",
             "r2_partial_w", "mean_abs_den"]].round(3).to_string())


def figure(R, trials):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.6))
    for ax, sub, lab in zip(axs, ("E", "N"), ("Echo LVEF subset", "NT-proBNP subset")):
        W = R[(R.subset == sub) & (R.rung == "P1") & R.trial.isin(trials)].pivot_table(index="trial", columns="arm", values="loghr")
        if not {"base", "ECG", "shufECG", "phys1"} <= set(W.columns):
            continue
        W = W.dropna(subset=["base", "ECG", "shufECG", "phys1"])
        den, ne, ns = W.base - W.phys1, W.base - W.ECG, W.base - W.shufECG
        ax.axhline(0, color="#999", lw=0.6)
        ax.axvline(0, color="#999", lw=0.6)
        ax.scatter(den, ne, s=26, color="#d9534f", label="+ ECG", zorder=3)
        ax.scatter(den, ns, s=26, facecolor="none", edgecolor="#1f2a5a", label="+ permuted ECG", zorder=3)
        lim = max(0.05, float(np.nanmax(np.abs(np.r_[den, ne, ns]))) * 1.1)
        xx = np.array([-lim, lim])
        F = slope(ne.to_numpy(), den.to_numpy())
        r2 = R[(R.subset == sub) & (R.rung == "P1") & (R.arm == "base")].set_index("trial").r2_partial.reindex(W.index)
        w = den ** 2
        r2w = float(np.nansum(w * r2) / np.nansum(w[r2.notna()]))
        ax.plot(xx, F * xx, color="#d9534f", lw=1.4, label=f"ECG slope F = {F:.2f}")
        ax.plot(xx, r2w * xx, color="#1f2a5a", lw=1.2, ls="--", label=f"plasmode prediction (partial R² = {r2w:.2f})")
        ax.plot(xx, xx, color="#bbb", lw=0.8, ls=":", label="= physiology (oracle)")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_xlabel("Shift in log HR from adding measured physiology")
        ax.set_ylabel("Shift in log HR from adding ECG")
        ax.set_title(f"{lab} ({len(W)} trials; demographic PS)", fontsize=10)
        ax.legend(fontsize=7.5, loc="upper left", frameon=False)
    fig.tight_layout()
    DOCS.mkdir(parents=True, exist_ok=True)
    fig.savefig(DOCS / "ECHO_SUBSET_F.png", dpi=160)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["run", "summarize"])
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--trials", default="")
    a = ap.parse_args()
    os.umask(0o077)
    if a.mode == "run":
        run(a.trials.split(",") if a.trials else ALL, a.workers)
    else:
        summarize()
