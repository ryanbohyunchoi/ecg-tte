#!/usr/bin/env python
"""v1.7 FIXED confirmatory analysis (docs/v16/V17_CONFIRMATION_PLAN.md section C, commit 0e66e3c).

No analysis choice differs from v1.6:
  P1 = T.demo (age, sex, index year)                                  = s1_ladder cell r1_demo (no nan_to_num)
  P2 = demo + hypertension_v11, t2d, cad_ihd, obesity (covars v1), atrial_fibrillation (T.cov) and HF
       (covars2b hf_any_365, fallback elx_chf when the column is absent)     = s10_demo6.py, nan_to_num on base
  arms: base, +ECG (T.ecg_pc), +shufECG (T.ecg_pc[T.shuffle_perm]), +noise32 (T.noise32); unmatched once per half.
  E.run_cell(T, X[rows], rows=rows, estimator=("match", 0.2, 1)), PS L2 C=1 (engine default).
  halves full / A / B from s1_ladder.halves(T, i), i = index of the trial in ALL = E.TRIALS (the 18 v1.6
  trials, i = 0..17, exactly as S1/S10) + list(v13_common.V17) (the 15 v1.7 trials, i = 18..32), so the
  seed is 16060 + i; the existing 18 keep their v1.6 seeds.
Paths: v1.6 trials read claude-v16-covars / claude-v16-covars2b, v1.7 trials claude-v17-covars / claude-v17-covars2b.

Secondary balance panel ("x", covars2b non-ECG-proximal): S6.load_extra(T, covars2b dir) (status kept*, no
exposure leak, timing pre_index only), minus block ecg_proximal, S8.EXTRA_PROX, S8.NOT_PREINDEX, zip_*, domain
index_context (= S8.trial / S9 non-proximal); per PS, variables in / proxy of / tagged-overlapping a PS variable
(S6.excluded_extra) or composite scores with a PS component (S8.composite_overlap) are dropped; then columns with
no observed value or no variance in the analysed rows. PS variable names: P1 = T.demo; P2 = T.demo + the six
column names actually used. Unmatched uses no exclusion.

Usage:
  v17_confirm.py run [--trials a,b] [--workers 32] [--tag NAME]   -> OUT/results_<tag>.csv, OUT/log_<tag>.json
  v17_confirm.py verify [--tag NAME]   compare P1/P2 of v1.6 trials in results_<tag> vs S1 / S10 results.csv
  v17_confirm.py summarize             -> OUT/summary.csv, OUT/per_trial_new15.csv, markdown tables to stdout
Aggregates only; OUT has umask 077.
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
sys.path.insert(0, str(HERE.parent / "v16"))
sys.path.insert(0, str(HERE.parent))
import v16_engine as E  # noqa: E402
import s6_balance as S6  # noqa: E402
import s8_headline as S8  # noqa: E402  (installs the matched-sample capture S8._LAST around E.match)
from s1_ladder import halves  # noqa: E402
from v13_common import EXTRA, PRIMARY, V17  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = A / "claude-v17-confirm"
DOCS = HERE.parent.parent / "docs" / "v17"
NEW = list(V17)
OLD = list(E.TRIALS)
ALL = OLD + NEW
KEY = {n: {**PRIMARY, **EXTRA}[n][0] for n in ALL}
ROLES = ["base", "ECG", "shufECG", "noise"]
P2DX = ["hypertension_v11", "t2d", "cad_ihd", "obesity"]


def cdirs(n):
    v = "v17" if n in NEW else "v16"
    return A / f"claude-{v}-covars", A / f"claude-{v}-covars2b"


def xpanel(T, d2):
    Xe, ovl, blk = S6.load_extra(T, d2)
    dom = pd.read_csv(d2 / "dictionary.csv").set_index("variable").domain
    keep = [c for c in Xe.columns if blk[c] != "ecg_proximal" and c not in S8.NOT_PREINDEX and not c.startswith("zip_")
            and dom.get(c, "") != "index_context" and c not in S8.EXTRA_PROX]
    return Xe[keep], ovl


def designs(T, n):
    """-> {ps: (base matrix over all rows or None for P1-built-per-rows, ps names)}, log dict."""
    d1, d2 = cdirs(n)
    C1 = pd.read_parquet(d1 / f"{n}.parquet").set_index("patient_key").reindex(T.keys)
    C2 = pd.read_parquet(d2 / f"{n}.parquet").set_index("patient_key").reindex(T.keys)
    log = dict(trial=n, n_demo=len(T.demo), demo=list(T.demo))
    miss = [c for c in P2DX if c not in C1]
    if miss:
        raise RuntimeError(f"{n}: P2 covars v1 columns missing {miss} (no v1.6 fallback rule exists)")
    hf = "hf_any_365" if "hf_any_365" in C2 else "elx_chf"  # s10 rule
    if "atrial_fibrillation" not in T.cov:
        raise RuntimeError(f"{n}: atrial_fibrillation not in T.cov (no v1.6 fallback rule exists)")
    log["hf_column"] = hf
    base = np.column_stack([T.cov[T.demo].to_numpy(float), C1[P2DX].to_numpy(float),
                            T.cov["atrial_fibrillation"].to_numpy(float), C2[hf].to_numpy(float)])
    log["p2_nan_cells_zeroed"] = int(np.isnan(base).sum() > 0)  # flag only (no count)
    base = np.nan_to_num(base)
    return base, list(T.demo) + P2DX + ["atrial_fibrillation", hf], log


def xsmd(XV, t, s_idx, s_w):
    if XV.shape[1] == 0:
        return dict(x_pct_lt10=np.nan, x_mean=np.nan, x_nvars=0)
    v = E.smd_components(XV, t, s_idx, s_w, t[s_idx])
    v = v[np.isfinite(v)]
    return dict(x_pct_lt10=100 * float(np.mean(v < 0.1)) if len(v) else np.nan, x_mean=float(v.mean()) if len(v) else np.nan,
                x_nvars=int(len(v)))


def task(args):
    n, half = args
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    base2, psn2, log = designs(T, n)
    Xe, ovl = xpanel(T, cdirs(n)[1])
    r = halves(T, i)[half]
    t = T.t[r]
    cov = T.cov.iloc[r]
    X1 = cov[T.demo].to_numpy(float)  # s1_ladder r1_demo
    pc, sh, nz = T.ecg_pc[r], T.ecg_pc[T.shuffle_perm][r], T.noise32[r]
    P = {"P1": (X1, list(T.demo)), "P2": (base2[r], psn2)}
    out = []

    def xv(psn):
        drop = set(S6.excluded_extra(psn, list(Xe.columns), ovl)) | {c for c in Xe.columns if S8.composite_overlap(c, psn)}
        U = Xe.drop(columns=sorted(drop)).iloc[r]
        U = U.loc[:, U.notna().sum() > 0]
        U = U.loc[:, U.nunique() > 1]
        return U.to_numpy(float), len(drop)

    def rec(ps, role, X, XV, nd):
        S8._LAST.clear()
        o = E.run_cell(T, X, rows=r, estimator=("match", 0.2, 1))
        s_idx, s_w = (np.arange(len(t)), np.ones(len(t))) if X is None else S8._LAST["m"]
        out.append(dict(trial=n, key=KEY[n], set="new15" if n in NEW else "old18", idx=i, half=half, ps=ps, arm_role=role,
                        rb=T.rb, rs=T.rs, x_ndrop=nd, **o, **xsmd(XV, t, s_idx, s_w)))

    XV0, nd0 = xv([])
    rec("none", "unmatched", None, XV0, nd0)
    for ps, (X, psn) in P.items():
        XV, nd = xv(psn)
        for role, Z in (("base", X), ("ECG", np.hstack([X, pc])), ("shufECG", np.hstack([X, sh])), ("noise", np.hstack([X, nz]))):
            rec(ps, role, Z, XV, nd)
    log.update(half=half, idx=i, seed=16060 + i, x_ncols_panel=int(Xe.shape[1]), secs=round(time.time() - t0, 1))
    print(f"{n} {half} {time.time() - t0:.0f}s", flush=True)
    return out, log


def run(trials, workers, tag):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    tk = [(n, h) for n in trials for h in ("full", "A", "B")]
    for n in trials:
        f = A / f"claude-v17-trials/{n}.READY"
        if n in NEW and not f.exists():
            raise RuntimeError(f"{n} not READY")
    tk.sort(key=lambda x: (x[0] not in ("lodestar", "affirm", "allhat", "insight", "declare"), x[1] != "full"))
    with Pool(min(workers, len(tk), 32)) as p:
        res = p.map(task, tk, chunksize=1)
    pd.DataFrame([x for o, _ in res for x in o]).to_csv(OUT / f"results_{tag}.csv", index=False)
    (OUT / f"log_{tag}.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    print("done", tag, flush=True)


# ---------------------------------------------------------------- verification vs v1.6 files
def verify(tag):
    R = pd.read_csv(OUT / f"results_{tag}.csv")
    S1 = pd.read_csv(A / "claude-v16-s1-ladder/results.csv")
    S10 = pd.read_csv(A / "claude-v16-s10-demo6/results.csv")
    S10 = S10[S10.caliper == 0.2]
    cols = ["loghr", "se", "n_pairs", "mean_smd", "cstat"] + [f"smd:{c}" for c, _, _ in E.VARS]
    rows = []
    for n in sorted(set(R.trial) & set(OLD)):
        for h in ("full", "A", "B"):
            for ps, ref, cell in (("P1", S1, "r1_demo"), ("P2", S10, None)):
                for role in ROLES + ["unmatched"]:
                    a = R[(R.trial == n) & (R.half == h) & (R.arm_role == role) & (R.ps == ("none" if role == "unmatched" else ps))]
                    if cell is not None:
                        b = ref[(ref.trial == n) & (ref.half == h) & (ref.arm_role == role) & (ref.cell == ("unmatched" if role == "unmatched" else cell))]
                    else:
                        b = ref[(ref.trial == n) & (ref.half == h) & (ref.arm_role == role)]
                    assert len(a) == 1 and len(b) == 1, (n, h, ps, role, len(a), len(b))
                    d = max(float(np.nan_to_num(abs(a[c].iloc[0] - b[c].iloc[0]), nan=0.0)) if not (pd.isna(a[c].iloc[0]) ^ pd.isna(b[c].iloc[0])) else np.inf
                            for c in cols)
                    rows.append(dict(trial=n, half=h, ps=ps, arm=role, maxdev=d))
    V = pd.DataFrame(rows)
    V.to_csv(OUT / f"verify_{tag}.csv", index=False)
    print(V.groupby(["trial", "ps"]).maxdev.max().to_string())
    print("overall max deviation", V.maxdev.max())
    return V


# ---------------------------------------------------------------- statistics
def signflip_1s(d):
    """Exact one-sided sign-flip p for H1: mean(d) > 0 (d oriented so positive = ECG better).
    p = P(sum of randomly signed |d| >= observed sum), all 2^k sign vectors (meet-in-the-middle for large k)."""
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


HIGHER = {"lt01", "x_lt01", "cons"}  # higher = better; others lower = better
METRICS = ["lt01", "x_lt01", "mean_smd", "cstat", "absd", "z2", "cons"]


def trial_metrics(g):
    sm = g[[f"smd:{c}" for c, _, _ in E.VARS]].abs()
    z = (g.loghr - g.rb) / np.sqrt(g.se ** 2 + g.rs ** 2)
    return pd.DataFrame({"lt01": (100 * (sm < 0.1).sum(1) / sm.notna().sum(1)).to_numpy(), "x_lt01": g.x_pct_lt10.to_numpy(),
                         "mean_smd": sm.mean(1).to_numpy(), "cstat": g.cstat.to_numpy(), "absd": (g.loghr - g.rb).abs().to_numpy(),
                         "z2": (z ** 2).to_numpy(), "cons": (100.0 * (z.abs() < 1.96)).to_numpy(),
                         "loghr": g.loghr.to_numpy(), "se": g.se.to_numpy(), "rb": g.rb.to_numpy(), "rs": g.rs.to_numpy()},
                        index=g.trial.to_numpy())


def load_all():
    """per-trial rows for all 33 trials. v1.6 trials: 58-panel / HR / C-stat columns from the v1.6 results files
    (S1 r1_demo, S10 caliper 0.2); covars2b 'x' columns from this run (not in the v1.6 files)."""
    R = pd.concat([pd.read_csv(f) for f in sorted(OUT.glob("results_*.csv"))], ignore_index=True)
    R = R.drop_duplicates(["trial", "half", "ps", "arm_role"], keep="last")
    S1 = pd.read_csv(A / "claude-v16-s1-ladder/results.csv")
    S1 = S1[S1.cell == "r1_demo"].assign(ps="P1")
    S10 = pd.read_csv(A / "claude-v16-s10-demo6/results.csv")
    S10 = S10[(S10.caliper == 0.2) & (S10.arm_role != "unmatched")].assign(ps="P2")
    V = pd.concat([S1, S10], ignore_index=True)
    V = V[V.trial.isin(OLD)]
    keep = ["loghr", "se", "cstat", "mean_smd", "n_pairs", "rb", "rs"] + [f"smd:{c}" for c, _, _ in E.VARS]
    idx = ["trial", "half", "ps", "arm_role"]
    V = V.set_index(idx)[keep]
    R = R.set_index(idx)
    old = R.index.get_level_values(0).isin(OLD) & R.index.isin(V.index)
    R.loc[old, keep] = V.loc[R.index[old], keep].to_numpy()
    return R.reset_index()


def sel(M, trials):
    return {h: {ps: {r: M[h][ps][r].loc[[t for t in trials if t in M[h][ps][r].index]] for r in ROLES} for ps in ("P1", "P2")}
            for h in M}


def cluster_of():
    J = json.loads((DOCS / "trial_selection.json").read_text())["comparator_clusters"]["clusters"]
    return {t: c for c, ts in J.items() for t in ts}


def analyse(M, trials, rng_seed=0, nperm=20000):
    CL = cluster_of()
    out = []
    for ps in ("P1", "P2"):
        F = {r: M["full"][ps][r].loc[trials] for r in ROLES}
        for m in METRICS:
            sgn = 1 if m in HIGHER else -1
            b, e, s, z = (F[r][m] for r in ROLES)
            d = sgn * (e - b)
            row = dict(ps=ps, metric=m, n=len(trials), base=b.mean(), ecg=e.mean(), shuf=s.mean(), noise=z.mean(),
                       d_ecg_minus_base=(e - b).mean(), k_better=f"{int((d > 0).sum())}/{int(d.notna().sum())}",
                       p=signflip_1s(d), p_vs_shuf=signflip_1s(sgn * (e - s)), p_vs_noise=signflip_1s(sgn * (e - z)),
                       d_shuf_minus_base=(s - b).mean(), d_noise_minus_base=(z - b).mean())
            cl = pd.Series(d.to_numpy(), index=[CL[KEY[t]] for t in trials]).groupby(level=0).mean()
            row["n_clusters"] = len(cl)
            row["cluster_p"] = signflip_1s(cl.to_numpy())
            for lab, other in (("shuf", s), ("noise", z)):
                c2 = pd.Series((sgn * (e - other)).to_numpy(), index=[CL[KEY[t]] for t in trials]).groupby(level=0).mean()
                row[f"cluster_p_vs_{lab}"] = signflip_1s(c2.to_numpy())
            row["loo_max_p"] = max(signflip_1s(d.drop(t)) for t in trials) if len(trials) > 1 else np.nan
            for h in ("A", "B"):
                Hh = {r: M[h][ps][r].loc[trials] for r in ("base", "ECG")}
                row[f"p_{h}"] = signflip_1s(sgn * (Hh["ECG"][m] - Hh["base"][m]))
            if m in ("absd", "z2"):
                rb, rs = F["base"].rb.to_numpy(), F["base"].rs.to_numpy()
                lb, sb, le, se_ = F["base"].loghr.to_numpy(), F["base"].se.to_numpy(), F["ECG"].loghr.to_numpy(), F["ECG"].se.to_numpy()

                def st(ix):
                    q, v = rb[ix], rs[ix]
                    if m == "absd":
                        return (np.abs(le - q) - np.abs(lb - q)).mean()
                    return ((le - q) ** 2 / (se_ ** 2 + v ** 2) - (lb - q) ** 2 / (sb ** 2 + v ** 2)).mean()
                obs = st(np.arange(len(trials)))
                rng = np.random.default_rng(rng_seed)
                null = np.array([st(rng.permutation(len(trials))) for _ in range(nperm)])
                row.update(bshuf_obs=obs, bshuf_null_mean=null.mean(), bshuf_p=float((null <= obs + 1e-12).mean()))
            out.append(row)
    return out


def summarize():
    R = load_all()
    R = R[R.arm_role != "unmatched"]
    M = {h: {ps: {r: trial_metrics(R[(R.half == h) & (R.ps == ps) & (R.arm_role == r)]) for r in ROLES} for ps in ("P1", "P2")}
         for h in ("full", "A", "B")}
    J = json.loads((DOCS / "trial_selection.json").read_text())
    inv = {v: k for k, v in KEY.items()}
    sets = {("new15", "all"): NEW, ("all33", "all"): ALL}
    for sub in ("S_fid", "S_fid_strict", "S_ecg", "S_both", "S_both_high"):
        sets[("new15", sub)] = [inv[k] for k in J["subsets"]["v17_new_15"][sub] if k in inv and inv[k] in NEW]
        sets[("all33", sub)] = [inv[k] for k in J["subsets"]["all_trials"][sub] if k in inv and inv[k] in ALL]
    sets[("old18", "all")] = OLD  # reference: must equal the v1.6 numbers
    rows = []
    for (scope, sub), trials in sets.items():
        trials = [t for t in ALL if t in trials]
        for r in analyse(M, trials):
            rows.append(dict(scope=scope, subset=sub, trials=",".join(KEY[t] for t in trials), **r))
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "summary.csv", index=False)
    # per-trial table, new 15
    pt = []
    for n in NEW:
        tr = J["trials"][KEY[n]]
        rec = dict(trial=n, rct_hr=float(np.exp(M["full"]["P1"]["base"].loc[n, "rb"])), fidelity=bool(tr["fidelity_include"]),
                   fidelity_strict=bool(tr["fidelity_include_strict"]), ecg_relevance=tr["ecg_relevance"], cluster=tr["comparator_cluster"])
        for ps in ("P1", "P2"):
            b, e = M["full"][ps]["base"].loc[n], M["full"][ps]["ECG"].loc[n]
            rec.update({f"{ps}_hr_base": np.exp(b.loghr), f"{ps}_hr_ecg": np.exp(e.loghr), f"{ps}_se_base": b.se, f"{ps}_se_ecg": e.se,
                        f"{ps}_absd_base": b.absd, f"{ps}_absd_ecg": e.absd, f"{ps}_lt01_base": b.lt01, f"{ps}_lt01_ecg": e.lt01,
                        f"{ps}_xlt01_base": b.x_lt01, f"{ps}_xlt01_ecg": e.x_lt01})
        pt.append(rec)
    P = pd.DataFrame(pt)
    P.to_csv(OUT / "per_trial_new15.csv", index=False)
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 60)
    print(S.round(4).to_string(index=False))
    print(P.round(3).to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run", "verify", "summarize"])
    ap.add_argument("--trials", default=",".join(ALL))
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--tag", default="all")
    a = ap.parse_args()
    os.umask(0o077)
    if a.cmd == "run":
        run(a.trials.split(","), a.workers, a.tag)
    elif a.cmd == "verify":
        verify(a.tag)
    else:
        summarize()


if __name__ == "__main__":
    main()
