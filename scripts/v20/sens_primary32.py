#!/usr/bin/env python
"""v2.0 sensitivity and robustness analyses for the primary 32-trial set (plan: docs/v20/SENS_PRIMARY32_PLAN.md).

Sets: S32 = 38 emulated trials minus the 6 'Limited' (docs/v19/quality_tiers.json); S38 = all 38. Full cohort only
(split halves dropped per PI decision 2026-10-01).

Cells (v16_engine.run_cell on the v18_embed_compare trial objects; cstat=None):
  rungs P1 / P5 / hdPS200 / clinical  x  arms base / ECG (32 PCs) / shufECG  x  configs
  main (match 0.2, 1:1, L2) | cal01 (match 0.1) | m13 (1:3, caliper 0.2) | iptw | overlap | gbm (match 0.2, GBM PS)
  plus P1 ECG-dimension sweep k in {4, 8, 16, 32, 64, 128, 256} (main config; ECG and permuted ECG).
Gate: main-config cells must reproduce claude-v18-embed-compare (half = full) to <= 1e-12.

Usage:
  sens_primary32.py run [--workers 24]   -> OUT/restricted_cells.parquet, OUT/cells.csv (suppressed), OUT/log.json
  sens_primary32.py gate                 -> OUT/gate.csv
  sens_primary32.py summarize            -> OUT/{sensitivity,robustness,pcsweep,outpatient,ci}.csv, OUT/tables.md
Aggregates only; OUT umask 077; patient counts 1-10 suppressed in every written csv.
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
sys.path.insert(0, str(HERE.parent / "v18"))
sys.path.insert(0, str(HERE.parent))
import v18_af_confirm as AF  # noqa: E402
import v18_clmbr as C  # noqa: E402
import v18_embed_compare as M18  # noqa: E402
from eval_longtail_balance import pcs  # noqa: E402

V = AF.V
E = V.E
A = V.A
OUT = A / "claude-v20-sens-primary32"
ALL = list(V.ALL)
KEY = V.KEY
VN = [c for c, _, _ in E.VARS]
GROUP = {c: g for c, _, g in E.VARS}
RUNGS = ["P1", "P5", "hdPS200", "clinical"]
ARMS = ["base", "ECG", "shufECG"]
CONFIGS = {"main": (("match", 0.2, 1), ("l2", 1.0)), "cal01": (("match", 0.1, 1), ("l2", 1.0)),
           "m13": (("match", 0.2, 3), ("l2", 1.0)), "iptw": (("iptw",), ("l2", 1.0)),
           "overlap": (("overlap",), ("l2", 1.0)), "gbm": (("match", 0.2, 1), ("gbm", None))}
KS = [4, 8, 16, 32, 64, 128, 256]
NB, SEED = 4000, 20261001
MIN_CELL = 11
QT = {t["key"]: t["tier"].split(" - ")[0] for t in json.load(open(ROOT / "docs/v19/quality_tiers.json"))["trials"]}
S38 = ALL
S32 = [n for n in ALL if QT[KEY[n]] != "Limited"]
assert len(S38) == 38 and len(S32) == 32


def suppress(D):
    D = D.copy()
    flag = np.zeros(len(D), bool)
    for c in ("n", "n_t", "n_c", "n_pairs"):
        if c in D:
            v = pd.to_numeric(D[c], errors="coerce")
            b = (v >= 1) & (v < MIN_CELL)
            flag |= b.to_numpy()
            D.loc[b, c] = np.nan
    D["suppressed_lt11"] = flag
    return D


# ================================================================ run
def task(n, only=None):
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    b5, psn5, _ = C.designs(T, n, C.P5DX)
    t = T.t
    r = np.arange(len(t))
    X1 = T.cov.iloc[r][T.demo].to_numpy(float)  # row-indexed copies, exactly as v18_embed_compare (BLAS order)
    dx = T.X_dx[r]
    Hk = T.hd(200, t=t, rows=r)
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    rung = {"P1": (X1, set()), "P5": (b5[r], set()), "hdPS200": (np.hstack([dx, Hk]), set()), "clinical": (T.X_core[r], clin_ex)}
    P256 = pcs(T.ecg_raw, min(256, T.ecg_raw.shape[1]))
    perm = T.shuffle_perm
    out = []

    def rec(rg, cfg, arm, k, X, ex58):
        est, psm = CONFIGS[cfg]
        o = E.run_cell(T, X, rows=r, estimator=est, ps_model=psm, cstat=None)
        out.append(dict(trial=n, key=KEY[n], idx=i, rung=rg, config=cfg, arm=arm, k_pcs=k, rb=T.rb, rs=T.rs,
                        ex58=";".join(sorted(ex58)), **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c")},
                        **{f"smd:{c}": o[f"smd:{c}"] for c in VN}))

    for rg, (X, ex58) in rung.items():
        if only and rg not in only:
            continue
        for cfg in CONFIGS:
            rec(rg, cfg, "base", 0, X, ex58)
            rec(rg, cfg, "ECG", 32, np.hstack([X, T.ecg_pc]), ex58)
            rec(rg, cfg, "shufECG", 32, np.hstack([X, T.ecg_pc[perm]]), ex58)
    for k in KS:
        if only and "P1" not in only:
            break
        if k == 32:
            continue
        Z = T.ecg_pc64[:, :k] if k <= 64 else P256[:, :k]
        if Z.shape[1] < k:
            continue
        rec("P1", "main", "ECG", k, np.hstack([X1, Z]), set())
        rec("P1", "main", "shufECG", k, np.hstack([X1, Z[perm]]), set())
    print(f"{n} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, secs=round(time.time() - t0, 1), n_pcs_raw=int(T.ecg_raw.shape[1]))


def run(workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4")
    tk = sorted(ALL, key=lambda x: x not in big)
    with Pool(min(workers, len(tk))) as p:
        res = p.map(task, tk, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    R.to_parquet(OUT / "restricted_cells.parquet")
    suppress(R).to_csv(OUT / "cells.csv", index=False)
    (OUT / "log.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    print("done", flush=True)


def _ptask(args):
    n, rungs = args
    return task(n, only=rungs)


def patch(trials, rungs, workers):
    """recompute selected trials x rungs and replace those rows (logged deviation: BLAS-order fix)."""
    from multiprocessing import Pool
    os.umask(0o077)
    R = pd.read_parquet(OUT / "restricted_cells.parquet")
    with Pool(min(workers, len(trials))) as p:
        res = p.map(_ptask, [(n, rungs) for n in trials])
    N = pd.DataFrame([x for o, _ in res for x in o])
    keep = ~(R.trial.isin(trials) & R.rung.isin(rungs))
    R = pd.concat([R[keep], N], ignore_index=True)
    R.to_parquet(OUT / "restricted_cells.parquet")
    suppress(R).to_csv(OUT / "cells.csv", index=False)
    print("patched", len(N), "rows", flush=True)


# ================================================================ gate
def gate():
    R = pd.read_parquet(OUT / "restricted_cells.parquet")
    Q = pd.read_parquet(M18.OUT / "restricted_results_unsuppressed.parquet")
    Q = Q[Q.half == "full"]
    cols = ["loghr", "se", "n", "n_t", "n_c", "n_pairs"] + [f"smd:{c}" for c in VN]
    rows = []
    for rg in RUNGS:
        for a in ARMS:
            x = R[(R.rung == rg) & (R.config == "main") & (R.arm == a) & (R.k_pcs.isin([0, 32]))].set_index("trial")
            y = Q[(Q.rung == rg) & (Q.arm_role == a)].set_index("trial")
            ix = x.index.intersection(y.index)
            for c in cols:
                xa, ya = x.loc[ix, c].to_numpy(float), y.loc[ix, c].to_numpy(float)
                dev = float(np.nanmax(np.abs(xa - ya))) if np.isfinite(xa - ya).any() else 0.0
                rows.append(dict(rung=rg, arm=a, col=c, n=len(ix), maxdev=dev, nan_mismatch=int((np.isnan(xa) ^ np.isnan(ya)).sum())))
    G = pd.DataFrame(rows)
    os.umask(0o077)
    G.to_csv(OUT / "gate.csv", index=False)
    print(G.groupby(["rung", "arm"]).agg(n=("n", "max"), maxdev=("maxdev", "max"), nan=("nan_mismatch", "sum")).to_string())
    print("overall maxdev", G.maxdev.max(), "nan mismatches", G.nan_mismatch.sum())
    return G


# ================================================================ statistics
def per_trial(g):
    """per-trial endpoints from a block of cells (one row per trial)."""
    S = g[[f"smd:{c}" for c in VN]].abs().to_numpy(float)
    for j, ex in enumerate(g.ex58.fillna("").astype(str)):
        for c in filter(None, ex.split(";")):
            S[j, VN.index(c)] = np.nan
    sm = pd.DataFrame(S, columns=VN, index=g.trial.to_numpy())
    z = ((g.loghr - g.rb) / np.sqrt(g.se ** 2 + g.rs ** 2)).to_numpy()
    d = (g.loghr - g.rb).abs().to_numpy()
    return pd.DataFrame({"lt01": (100 * (sm < 0.1).sum(1) / sm.notna().sum(1)).to_numpy(), "m58": sm.mean(1).to_numpy(),
                         "absd": d, "cons": 100.0 * (np.abs(z) < 1.96), "ea": 100.0 * (d <= 1.96 * g.rs.to_numpy()),
                         "loghr": g.loghr.to_numpy(), "se": g.se.to_numpy(), "rb": g.rb.to_numpy(), "rs": g.rs.to_numpy()},
                        index=g.trial.to_numpy()), sm


def p1s(d):
    d = np.asarray(d, float)
    return V.signflip_1s(d[np.isfinite(d)])


def p2s(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    return min(1.0, 2 * min(V.signflip_1s(d), V.signflip_1s(-d)))


def relred_ci(B, Ev):
    """relative reduction = 1 - mean(E)/mean(B) over trials; percentile CI, NB resamples, fresh fixed-seed generator."""
    B, Ev = np.asarray(B, float), np.asarray(Ev, float)
    ok = np.isfinite(B) & np.isfinite(Ev)
    B, Ev = B[ok], Ev[ok]
    est = 100 * (1 - Ev.mean() / B.mean())
    rng = np.random.default_rng(SEED)
    I = rng.integers(0, len(B), size=(NB, len(B)))
    bs = 100 * (1 - Ev[I].mean(1) / B[I].mean(1))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return est, lo, hi, int(ok.sum())


def bshuf(la, lb, rb, ndraw=20000):
    """within-set benchmark shuffle: stat = mean(|la - q| - |lb - q|); p = P(null <= obs) (one-sided, a better)."""
    st = lambda q: np.mean(np.abs(la - q) - np.abs(lb - q), axis=-1)
    obs = float(st(rb))
    rng = np.random.default_rng(0)
    IX = np.array([rng.permutation(len(rb)) for _ in range(ndraw)])
    return float((st(rb[IX]) <= obs + 1e-12).mean())


def agree_metrics(F):
    ok = np.isfinite(F.loghr) & np.isfinite(F.se)
    G = F[ok]
    r = float(np.corrcoef(G.loghr, G.rb)[0, 1]) if len(G) > 2 else np.nan
    return dict(k=int(ok.sum()), absd=G.absd.mean(), r=r, ea=G.ea.mean(), cons=G.cons.mean())


def paired_balance(Fa, Fb, SMa, SMb, trials):
    """lt01 / m58 recomputed on the variables observed in BOTH arms of each trial (paired, same variable set)."""
    a, b = SMa.loc[trials].copy(), SMb.loc[trials].copy()
    msk = a.isna() | b.isna()
    a[msk], b[msk] = np.nan, np.nan
    Fa, Fb = Fa.copy(), Fb.copy()
    for F_, M_ in ((Fa, a), (Fb, b)):
        F_.loc[trials, "lt01"] = (100 * (M_ < 0.1).sum(1) / M_.notna().sum(1)).to_numpy()
        F_.loc[trials, "m58"] = M_.mean(1).to_numpy()
    return Fa, Fb


def contrast_row(Fa, Fb, trials, side, CL, SMa=None, SMb=None):
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
        cl = pd.Series(d.to_numpy(), index=[CL[KEY[t]] for t in trials]).dropna().groupby(level=0).mean()
        out[f"{m}_cluster_p"], out[f"{m}_n_clusters"] = pf(cl.to_numpy()), len(cl)
        out[f"{m}_loo_max_p"] = max(pf(d.drop(t).to_numpy()) for t in trials)
    e, lo, hi, k = relred_ci(Fb.loc[trials, "m58"], Fa.loc[trials, "m58"])
    out.update(relred=e, relred_lo=lo, relred_hi=hi, relred_k=k)
    la, lb, rb = Fa.loc[trials, "loghr"].to_numpy(), Fb.loc[trials, "loghr"].to_numpy(), Fb.loc[trials, "rb"].to_numpy()
    ok = np.isfinite(la) & np.isfinite(lb)
    out["bshuf_p"] = bshuf(la[ok], lb[ok], rb[ok]) if side == "one" else np.nan
    return out


MIMIC7 = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2"]


def mimic_ci():
    """MIMIC-IV relative reduction in mean |SMD| (7 CV trials) from the per-trial arm files, both populations."""
    rows = []
    D = pd.concat([pd.read_csv(A / f"claude-v20-mimic-replication/results/{t}_arms.csv") for t in MIMIC7])
    for pop in ("all", "no_index_day_ecg"):
        for rg in ("demo", "sparse", "hdPS200", "clinical"):
            g = D[(D["pop"] == pop) & (D.base == rg)].pivot_table(index="trial", columns="arm", values="mean_smd").reindex(MIMIC7)
            for a in ("ECG", "permECG"):
                e, lo, hi, k = relred_ci(g["base"], g[a])
                rows.append(dict(source="MIMIC-IV", set=f"7 CV trials ({pop})", rung=rg, domain="26 held-out", arm=a, k=k,
                                 est=e, lo=lo, hi=hi))
    return rows


def cimimic():
    os.umask(0o077)
    C_ = pd.read_csv(OUT / "ci.csv")
    C_ = pd.concat([C_[C_.source != "MIMIC-IV"], pd.DataFrame(mimic_ci())], ignore_index=True)
    C_.to_csv(OUT / "ci.csv", index=False)
    print(C_[C_.source == "MIMIC-IV"].round(1).to_string(index=False))


def summarize():
    os.umask(0o077)
    R = pd.read_parquet(OUT / "restricted_cells.parquet")
    CL = V.cluster_of()
    sets = {"S32": S32, "S38": S38}
    F, SM = {}, {}
    for (rg, cfg, a, k), g in R.groupby(["rung", "config", "arm", "k_pcs"]):
        F[(rg, cfg, a, k)], SM[(rg, cfg, a, k)] = per_trial(g.set_index("trial", drop=False).loc[[t for t in ALL if t in set(g.trial)]])
    key = lambda rg, cfg, a, k=None: (rg, cfg, a, 0 if a == "base" else (32 if k is None else k))
    # --- sensitivity grid (all configs x rungs x sets): ECG vs base, shufECG vs base
    rows = []
    for sname, tr in sets.items():
        for cfg in CONFIGS:
            for rg in RUNGS:
                Fb = F[key(rg, cfg, "base")]
                for a, side in (("ECG", "one"), ("shufECG", "two")):
                    Fa = F[key(rg, cfg, a)]
                    row = dict(set=sname, config=cfg, rung=rg, contrast=f"{a} vs base", sided=side, n_trials=len(tr))
                    row.update(contrast_row(Fa, Fb, tr, side, CL, SM[key(rg, cfg, a)], SM[key(rg, cfg, "base")]))
                    for arm, FF in (("base", Fb), (a, Fa)):
                        mm = agree_metrics(FF.loc[tr])
                        row.update({f"{arm if arm == 'base' else 'arm'}_{q}": v for q, v in mm.items()})
                    rows.append(row)
                Fa, Fs = F[key(rg, cfg, "ECG")], F[key(rg, cfg, "shufECG")]
                row = dict(set=sname, config=cfg, rung=rg, contrast="ECG vs shufECG", sided="one", n_trials=len(tr))
                row.update(contrast_row(Fa, Fs, tr, "one", CL, SM[key(rg, cfg, "ECG")], SM[key(rg, cfg, "shufECG")]))
                rows.append(row)
    S = pd.DataFrame(rows)
    # BH-FDR within families over set x config x rung x contrast (main config is the primary family)
    for fam, mcol in (("balance-primary", "lt01_p"), ("balance-secondary", "m58_p"), ("emulation", "absd_p"),
                      ("emulation-cons", "cons_p"), ("trial-specific", "bshuf_p")):
        for scope, msk in (("main", S.config == "main"), ("all", S.config.notna())):
            S[f"q_{mcol}_{scope}"] = np.nan
            idx = S.index[msk & S[mcol].notna()]
            S.loc[idx, f"q_{mcol}_{scope}"] = E.bh_fdr(S.loc[idx, mcol].to_numpy())
    S.to_csv(OUT / "sensitivity.csv", index=False)
    # --- ECG dimension sweep (P1, main)
    pr = []
    for sname, tr in sets.items():
        Fb = F[key("P1", "main", "base")]
        for k in KS:
            if ("P1", "main", "ECG", k) not in F:
                continue
            for a in ("ECG", "shufECG"):
                Fa = F[("P1", "main", a, k)]
                row = dict(set=sname, k_pcs=k, contrast=f"{a} vs base", n_trials=len(tr))
                row.update(contrast_row(Fa, Fb, tr, "one" if a == "ECG" else "two", CL, SM[("P1", "main", a, k)], SM[key("P1", "main", "base")]))
                row.update({f"arm_{q}": v for q, v in agree_metrics(Fa.loc[tr]).items()})
                pr.append(row)
    pd.DataFrame(pr).to_csv(OUT / "pcsweep.csv", index=False)
    # --- outpatient initiators (v19 SENS_OUTPATIENT output), OUT-29 and OUT-29 & S32
    O = pd.read_csv(A / "claude-v19-sens-outpatient/results_outpt.csv")
    ST = pd.read_csv(A / "claude-v19-sens-outpatient/setting.csv")
    out29 = sorted(set(ST[ST.rct_setting == "outpatient"].trial))
    O = O[O.half == "full"].assign(ex58="")
    Q = pd.read_parquet(M18.OUT / "restricted_results_unsuppressed.parquet")
    Q = Q[Q.half == "full"]
    orows = []
    for sname, tr in (("OUT29", [t for t in ALL if t in out29]), ("OUT29_S32", [t for t in S32 if t in out29])):
        for ps in ("P1", "P5"):
            blk = {a: per_trial(O[(O.ps == ps) & (O.arm_role == a)].drop_duplicates("trial").set_index("trial", drop=False)
                                .reindex(tr).reset_index(drop=True).assign(trial=tr)) for a in ("base", "ECG", "shufECG")}
            ai = {a: per_trial(Q[(Q.rung == ps) & (Q.arm_role == a)].set_index("trial", drop=False).loc[tr].reset_index(drop=True))
                  for a in ("base", "ECG")}
            for a, side in (("ECG", "one"), ("shufECG", "two")):
                row = dict(set=sname, ps=ps, contrast=f"{a} vs base", n_trials=len(tr), population="outpatient")
                row.update(contrast_row(blk[a][0], blk["base"][0], tr, side, CL, blk[a][1], blk["base"][1]))
                orows.append(row)
            row = dict(set=sname, ps=ps, contrast="ECG vs base", n_trials=len(tr), population="all initiators (same trials)")
            row.update(contrast_row(ai["ECG"][0], ai["base"][0], tr, "one", CL, ai["ECG"][1], ai["base"][1]))
            orows.append(row)
    pd.DataFrame(orows).to_csv(OUT / "outpatient.csv", index=False)
    # --- regenerated bootstrap CIs (relative reduction in mean |SMD|; ratio of across-trial means)
    ci = []
    for sname, tr in sets.items():
        for rg in RUNGS:
            Fb, Fe, Fs = F[key(rg, "main", "base")], F[key(rg, "main", "ECG")], F[key(rg, "main", "shufECG")]
            for a, Fa in (("ECG", Fe), ("shufECG", Fs)):
                Fa_, Fb_ = paired_balance(Fa, Fb, SM[key(rg, "main", a)], SM[key(rg, "main", "base")], tr)
                e, lo, hi, k = relred_ci(Fb_.loc[tr, "m58"], Fa_.loc[tr, "m58"])
                ci.append(dict(source="YNHHS", set=sname, rung=rg, domain="All 58", arm=a, k=k, est=e, lo=lo, hi=hi))
        # domains (P1)
        gb = R[(R.rung == "P1") & (R.config == "main") & (R.arm == "base")].set_index("trial", drop=False).loc[tr]
        smb = per_trial(gb)[1]
        for a in ("ECG", "shufECG"):
            ga = R[(R.rung == "P1") & (R.config == "main") & (R.arm == a) & (R.k_pcs == 32)].set_index("trial", drop=False).loc[tr]
            sma = per_trial(ga)[1]
            sb2, sa2 = smb.copy(), sma.copy()
            msk = sb2.isna() | sa2.isna()
            sb2[msk], sa2[msk] = np.nan, np.nan
            for dmn in dict.fromkeys(GROUP.values()):
                cols = [c for c in VN if GROUP[c] == dmn]
                e, lo, hi, k = relred_ci(sb2[cols].mean(1), sa2[cols].mean(1))
                ci.append(dict(source="YNHHS", set=sname, rung="P1", domain=dmn, arm=a, k=k, est=e, lo=lo, hi=hi))
    ci += mimic_ci()
    pd.DataFrame(ci).to_csv(OUT / "ci.csv", index=False)
    print("summaries written", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "gate", "summarize", "patch", "cimimic"])
    ap.add_argument("--trials", default="")
    ap.add_argument("--rungs", default="")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    {"run": lambda: run(a.workers), "gate": gate, "summarize": summarize,
     "patch": lambda: patch(a.trials.split(","), a.rungs.split(","), a.workers), "cimimic": cimimic}[a.cmd]()
