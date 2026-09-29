#!/usr/bin/env python
"""v1.9 sensitivity: adherence / on-treatment and run-in estimands (docs/v19/SENS_ADHERENCE_PLAN.md, committed c1f22c3
before any result).

Setting = the current 38-trial analysis: trial list / halves seeds / covariate paths from scripts/v18/v18_af_confirm.py
(-> scripts/v17/v17_confirm.py -> scripts/v16/v16_engine.py); PS P1 = T.demo, P5 = v18_clmbr.designs(T, n, P5DX);
arms base | +ECG32 | +shufECG32 (permuted) | unmatched; E.run_cell(..., estimator=("match", 0.2, 1)); matched set captured
from the engine matcher (s8_headline._LAST), pair = anchor.  ITT log HR / SE / n / n_pairs are checked against
claude-v18-embed-compare (restricted_results_unsuppressed.parquet) before anything else (verify).

Sensitivity estimands on each cell's matched set (v1.3 II2 / II3; deviation times from scripts/v13_extract.py,
IPCW = scripts/v13_design.ipcw unchanged):
  pp_naive_{365,180,730,switch}   censor at pp_stop{G} / pp_switch, no weights
  pp_ipcw_{365,180,730,switch}    same with stabilised, 99th-pct-truncated IPCW (pooled logistic per 90-d interval on
                                  treatment, interval and the arm's PS covariates; unmatched: P1 demographics)
  runin90                          pairs with both members followed > 90 d and >= 1 repeat own-drug order in (0, 90];
                                  clock restarts at day 90
  landmark90                       (deviation 1) same without the repeat-order requirement
Procedure-arm trials (cabana-v2, laaos3, protect-af, raft-af): not applicable (no pp_* columns in v13 extraction).

Usage:
  sens_adherence.py run [--trials a,b] [--workers 32]  -> OUT/restricted_cells.parquet (unsuppressed), OUT/cells.csv
  sens_adherence.py verify                              -> OUT/verify.csv (ITT vs claude-v18-embed-compare; max dev 0)
  sens_adherence.py summarize                           -> OUT/summary.csv, OUT/per_trial.csv, OUT/tables.md
Aggregates only; OUT umask 077; counts 1-10 suppressed in every non-restricted file.
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
sys.path.insert(0, str(HERE.parent / "v18"))
sys.path.insert(0, str(HERE.parent))
import v18_af_confirm as AF  # noqa: E402  (patches v17_confirm: 38-trial ALL, V18 paths)
import v18_clmbr as C  # noqa: E402
from trial_specs import TRIALS as SPECS  # noqa: E402
from v13_common import cox  # noqa: E402
from v13_design import ipcw  # noqa: E402

V = AF.V
E, S8 = V.E, V.S8
from s1_ladder import halves  # noqa: E402

A = V.A
OUT = A / "claude-v19-sens-adherence"
DOCS = HERE.parent.parent / "docs" / "v19"
REF = A / "claude-v18-embed-compare" / "restricted_results_unsuppressed.parquet"
ALL = list(V.ALL)
OLD = list(V.OLD)
KEY = V.KEY
assert len(ALL) == 38
PSS = ("P1", "P5")
ROLES = ("base", "ECG", "shufECG")
GS = ("365", "180", "730", "switch")
ESTIMANDS = ["itt"] + [f"pp_ipcw_{g}" for g in GS] + [f"pp_naive_{g}" for g in GS] + ["runin90", "landmark90"]
EST_LAB = {"itt": "ITT (primary)", "pp_ipcw_365": "PP IPCW G=365 (base)", "pp_ipcw_180": "PP IPCW G=180",
           "pp_ipcw_730": "PP IPCW G=730", "pp_ipcw_switch": "switch-only IPCW", "pp_naive_365": "PP naive G=365",
           "pp_naive_180": "PP naive G=180", "pp_naive_730": "PP naive G=730", "pp_naive_switch": "switch-only naive",
           "runin90": "90-d run-in landmark",
           "landmark90": "90-d landmark, no repeat-order rule (dev. 1)"}
MIN_CELL = 11
NPERM = 20000


def design_flag(n):
    s = SPECS[KEY[n]]
    if s.get("design") in ("procedure", "proc_vs_drug") or s.get("arm0_procedure"):
        return "NA: procedure arm"
    if s.get("add_on"):
        return "sequential add-on (AAD vs rate control; only AAD order censors comparator)"
    if s.get("design") == "switch_seq":
        return "sequential switch (other-arm order after index censors)"
    return "parallel drug"


# ================================================================ run
def task(args):
    n, half = args
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    b5, psn5, _ = C.designs(T, n, C.P5DX)
    r = halves(T, i)[half]
    t = T.t[r]
    yt, ye, ok = T.y_t[r], T.y_e[r], T.y_ok[r]
    H = T.horizon
    f3 = A / f"claude-{n}-outcomes-v13" / "restricted_outcomes_v13.parquet"
    O3 = pd.read_parquet(f3).set_index("patient_key").reindex(T.keys).iloc[r]
    has_pp = "pp_stop365" in O3
    cov_rate = float(O3.index.isin(pd.read_parquet(f3, columns=["patient_key"]).patient_key).mean())
    X1 = T.cov.iloc[r][T.demo].to_numpy(float)
    P = {"P1": X1, "P5": b5[r]}
    pc, sh = T.ecg_pc[r], T.ecg_pc[T.shuffle_perm][r]
    out = []

    def cell(ps, role, X):
        S8._LAST.clear()
        o = E.run_cell(T, X, rows=r, estimator=("match", 0.2, 1), cstat=None)
        if X is None:
            s_idx, cl = np.arange(len(t)), None
            Xarm = X1
        else:
            s_idx, _ = S8._LAST["m"]
            k = len(s_idx) // 2
            cl = np.r_[s_idx[:k], s_idx[:k]]
            Xarm = X
        m = ok[s_idx]
        idx = s_idx[m]
        cl = None if cl is None else cl[m]
        x = t[idx]
        tp, ep = yt[idx], ye[idx]
        base = dict(trial=n, key=KEY[n], idx=i, half=half, ps=ps, arm_role=role, rb=T.rb, rs=T.rs, n=o["n"], n_t=o["n_t"],
                    n_c=o["n_c"], n_pairs=o["n_pairs"], n_analysed=int(len(idx)))
        b, se = cox(tp, ep, x, cluster=cl)
        assert (np.isnan(b) and np.isnan(o["loghr"])) or abs(b - o["loghr"]) < 1e-12, (n, half, ps, role, b, o["loghr"])
        out.append(dict(base, estimand="itt", loghr=o["loghr"], se=o["se"], n_events=int(ep.sum())))
        if not has_pp:
            return
        Xa = Xarm[idx]
        for g in GS:
            dev = O3[f"pp_stop{g}" if g != "switch" else "pp_switch"].to_numpy(float)[idx]
            dstop = np.where(np.isnan(dev), np.inf, dev)
            tt = np.minimum(tp, dstop)
            ee = ((ep == 1) & (tp <= dstop)).astype(int)
            dev_pct = 100 * float(np.mean(dstop < tp))  # censored by deviation before event / end of follow-up
            b, se = cox(tt, ee, x, cluster=cl)
            out.append(dict(base, estimand=f"pp_naive_{g}", loghr=b, se=se, dev_pct=dev_pct, n_events=int(ee.sum())))
            L = ipcw(Xa, x, tp, dev, H)
            if L is None:
                out.append(dict(base, estimand=f"pp_ipcw_{g}", loghr=np.nan, se=np.nan, dev_pct=dev_pct, note="ipcw not estimable"))
                continue
            ev = ((ep[L.i] == 1) & (tp[L.i] <= L.stop.to_numpy()) & (tp[L.i] > L.start.to_numpy())).astype(int)
            clr = (np.arange(len(x)) if cl is None else cl)[L.i]
            b, se = cox(L.stop.to_numpy(float), ev, x[L.i], w=L.w.to_numpy(), cluster=clr, entry=L.start.to_numpy(float))
            out.append(dict(base, estimand=f"pp_ipcw_{g}", loghr=b, se=se, dev_pct=dev_pct, max_w=float(L.w.max()),
                            mean_w=float(L.w.mean()), n_events=int(ev.sum())))
        rep = O3.repeat_90.to_numpy()[idx]
        keep = (tp > 90) & (rep == 1)
        if cl is not None:
            keep = keep & pd.Series(keep).groupby(cl).transform("all").to_numpy()
        nk = int(keep.sum())
        rec = dict(base, estimand="runin90", n_kept=nk, retain_pct=100 * nk / len(idx), repeat90_pct=100 * float(np.mean(rep == 1)))
        if nk > 50:
            b, se = cox(tp[keep] - 90, ep[keep], x[keep], cluster=None if cl is None else cl[keep])
            rec.update(loghr=b, se=se, n_events=int(ep[keep].sum()))
        else:
            rec.update(loghr=np.nan, se=np.nan, note="<=50 kept")
        out.append(rec)
        # deviation 1 (2026-09-29): landmark-only reference (both members followed > 90 d; no repeat-order requirement)
        keep = tp > 90
        if cl is not None:
            keep = keep & pd.Series(keep).groupby(cl).transform("all").to_numpy()
        nk = int(keep.sum())
        rec = dict(base, estimand="landmark90", n_kept=nk, retain_pct=100 * nk / len(idx))
        if nk > 50:
            b, se = cox(tp[keep] - 90, ep[keep], x[keep], cluster=None if cl is None else cl[keep])
            rec.update(loghr=b, se=se, n_events=int(ep[keep].sum()))
        else:
            rec.update(loghr=np.nan, se=np.nan, note="<=50 kept")
        out.append(rec)

    cell("none", "unmatched", None)
    for ps in PSS:
        X = P[ps]
        for role, Z in (("base", X), ("ECG", np.hstack([X, pc])), ("shufECG", np.hstack([X, sh]))):
            cell(ps, role, Z)
    print(f"{n} {half} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, half=half, has_pp=has_pp, v13_key_coverage=cov_rate, secs=round(time.time() - t0, 1))


def suppress(D):
    D = D.copy()
    for c in ("n", "n_t", "n_c", "n_pairs", "n_analysed", "n_kept", "n_events"):
        if c in D:
            v = pd.to_numeric(D[c], errors="coerce")
            b = (v >= 1) & (v < MIN_CELL)
            D.loc[b, c] = np.nan
            if c == "n_kept" and "retain_pct" in D:
                D.loc[b, "retain_pct"] = np.nan
    return D


def run(trials, workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    big = ["value", "allhat", "ascot", "lodestar", "aristotle", "affirm", "east-afnet4", "transform-hf", "ontarget"]
    tk = sorted([(n, h) for n in trials for h in ("full", "A", "B")],
                key=lambda x: (x[1] != "full", big.index(x[0]) if x[0] in big else 99))
    with Pool(min(workers, len(tk), 32)) as p:
        res = p.map(task, tk, chunksize=1)
    D = pd.DataFrame([x for o, _ in res for x in o])
    D.to_parquet(OUT / "restricted_cells.parquet")
    suppress(D).to_csv(OUT / "cells.csv", index=False)
    (OUT / "log.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    print("done", flush=True)


def verify():
    D = pd.read_parquet(OUT / "restricted_cells.parquet")
    D = D[D.estimand == "itt"]
    Q = pd.read_parquet(REF)
    Q = Q[Q.rung.isin(["P1", "P5", "none"]) & Q.arm_role.isin(list(ROLES) + ["unmatched"])].rename(columns={"rung": "ps"})
    M = D.merge(Q, on=["trial", "half", "ps", "arm_role"], suffixes=("", "_ref"), how="outer", indicator=True)
    assert (M._merge == "both").all(), M._merge.value_counts()
    rows = []
    for c in ("loghr", "se", "n", "n_t", "n_c", "n_pairs"):
        a, b = M[c].astype(float), M[f"{c}_ref"].astype(float)
        both_nan = a.isna() & b.isna()
        d = (a - b).abs().where(~both_nan, 0.0).fillna(np.inf)
        M[f"dev_{c}"] = d
        rows.append(dict(column=c, cells=len(M), max_abs_dev=float(d.max()), n_nonzero=int((d > 1e-12).sum())))
    Vd = pd.DataFrame(rows)
    Vd.to_csv(OUT / "verify.csv", index=False)
    print(Vd.to_string(index=False))
    ok = bool((Vd.max_abs_dev <= 1e-12).all())
    print("REPRODUCTION", "PASS" if ok else "FAIL")
    return ok


# ================================================================ statistics
sf = V.signflip_1s


def bshuf_within(le, lb, rb, rs, seed=0, nperm=NPERM):
    obs = float((np.abs(le - rb) - np.abs(lb - rb)).mean())
    rng = np.random.default_rng(seed)
    null = np.empty(nperm)
    for j in range(nperm):
        ix = rng.permutation(len(rb))
        null[j] = (np.abs(le - rb[ix]) - np.abs(lb - rb[ix])).mean()
    return obs, float((null <= obs + 1e-12).mean())


def cons(lh, se, rb, rs):
    z = (lh - rb) / np.sqrt(se ** 2 + rs ** 2)
    return 100 * float(np.mean(np.abs(z) < 1.96))


def wide(D, half, est, ps):
    """trial x role table of loghr / se (+ unmatched)."""
    g = D[(D.half == half) & (D.estimand == est) & (D.ps.isin([ps, "none"]))]
    L = g.pivot_table(index="trial", columns="arm_role", values="loghr", aggfunc="first")
    S = g.pivot_table(index="trial", columns="arm_role", values="se", aggfunc="first")
    rb = g.groupby("trial").rb.first()
    rs = g.groupby("trial").rs.first()
    return L, S, rb, rs


def analyse(D, est, ps, trials_scope, scope):
    CL = V.cluster_of()
    L, S, rb, rs = wide(D, "full", est, ps)
    tr = [t for t in ALL if t in trials_scope and t in L.index]
    tr = [t for t in tr if all(np.isfinite(L.loc[t].get(r, np.nan)) and np.isfinite(S.loc[t].get(r, np.nan)) for r in ROLES)]
    k = len(tr)
    row = dict(scope=scope, estimand=est, ps=ps, n_trials=k)
    if k == 0:
        return row
    q, v = rb.loc[tr].to_numpy(), rs.loc[tr].to_numpy()
    ab = {r: np.abs(L.loc[tr, r].to_numpy() - q) for r in ROLES}
    for r in ROLES:
        row[f"absd_{r}"] = float(ab[r].mean())
        row[f"cons_{r}"] = cons(L.loc[tr, r].to_numpy(), S.loc[tr, r].to_numpy(), q, v)
    um = [t for t in tr if np.isfinite(L.loc[t].get("unmatched", np.nan))]
    row["absd_unmatched"] = float(np.abs(L.loc[um, "unmatched"] - rb.loc[um]).mean()) if um else np.nan
    row["cons_unmatched"] = cons(L.loc[um, "unmatched"].to_numpy(), S.loc[um, "unmatched"].to_numpy(), rb.loc[um].to_numpy(),
                                 rs.loc[um].to_numpy()) if um else np.nan
    row["n_unmatched"] = len(um)
    d = ab["base"] - ab["ECG"]
    ds = ab["shufECG"] - ab["ECG"]
    row.update(k_closer=f"{int((d > 0).sum())}/{k}", p_ecg_vs_base=sf(d), p_ecg_vs_shuf=sf(ds),
               k_closer_vs_shuf=f"{int((ds > 0).sum())}/{k}", p_shuf_vs_base=sf(ab["base"] - ab["shufECG"]))
    obs, p = bshuf_within(L.loc[tr, "ECG"].to_numpy(), L.loc[tr, "base"].to_numpy(), q, v)
    row.update(bshuf_obs=obs, bshuf_p=p)
    lab = [CL[KEY[t]] for t in tr]
    row["n_clusters"] = len(set(lab))
    row["cluster_p"] = sf(pd.Series(d, index=lab).groupby(level=0).mean().to_numpy())
    row["cluster_p_vs_shuf"] = sf(pd.Series(ds, index=lab).groupby(level=0).mean().to_numpy())
    for h in ("A", "B"):
        Lh, _, rbh, _ = wide(D, h, est, ps)
        th = [t for t in tr if t in Lh.index and np.isfinite(Lh.loc[t, "base"]) and np.isfinite(Lh.loc[t, "ECG"])]
        row[f"p_{h}"] = sf((np.abs(Lh.loc[th, "base"] - rbh.loc[th]) - np.abs(Lh.loc[th, "ECG"] - rbh.loc[th])).to_numpy())
        row[f"n_{h}"] = len(th)
    return row


def fmt_p(p):
    return "" if p is None or not np.isfinite(p) else (f"{p:.3f}" if p >= 0.001 else f"{p:.0e}")


def summarize():
    os.umask(0o077)
    D = pd.read_parquet(OUT / "restricted_cells.parquet")
    applicable = [n for n in ALL if not design_flag(n).startswith("NA")]
    rows = []
    for ps in PSS:
        rows.append(analyse(D, "itt", ps, ALL, "all38"))
        for est in ESTIMANDS:
            rows.append(analyse(D, est, ps, applicable, "applicable34"))
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "summary.csv", index=False)
    # per-trial
    pt = []
    F = suppress(D[D.half == "full"])  # counts 1-10 -> NaN (and their retain_pct)
    for n in ALL:
        rec = dict(trial=n, design=design_flag(n), rct_hr=float(np.exp(F[F.trial == n].rb.iloc[0])))
        u = F[(F.trial == n) & (F.arm_role == "unmatched")].set_index("estimand")
        for est in ESTIMANDS:
            if est not in u.index:
                continue
            rec[f"{est}_hr_unmatched"] = float(np.exp(u.loc[est, "loghr"]))
            for ps in PSS:
                g = F[(F.trial == n) & (F.ps == ps) & (F.estimand == est)].set_index("arm_role")
                for r in ROLES:
                    rec[f"{est}_{ps}_hr_{r}"] = float(np.exp(g.loc[r, "loghr"])) if r in g.index else np.nan
                if est == "runin90":
                    rec[f"runin90_{ps}_retain_pct_base"] = float(g.loc["base", "retain_pct"]) if "base" in g.index else np.nan
                    rec[f"runin90_{ps}_retain_pct_ECG"] = float(g.loc["ECG", "retain_pct"]) if "ECG" in g.index else np.nan
                if est == "pp_ipcw_365":
                    rec[f"dev365_{ps}_pct_base"] = float(g.loc["base", "dev_pct"]) if "base" in g.index else np.nan
                    rec[f"switch_{ps}_pct_base"] = float(F[(F.trial == n) & (F.ps == ps) & (F.estimand == "pp_ipcw_switch") &
                                                           (F.arm_role == "base")].dev_pct.iloc[0])
            if est == "runin90":
                rec["runin90_retain_pct_unmatched"] = float(u.loc[est, "retain_pct"])
        pt.append(rec)
    P = pd.DataFrame(pt)
    P.to_csv(OUT / "per_trial.csv", index=False)
    # retention aggregates (% of matched patients kept at landmark), applicable trials
    R = F[F.estimand.isin(["runin90", "landmark90"])]
    ret = R.groupby(["estimand", "ps", "arm_role"]).agg(trials=("trial", "nunique"), median_retain_pct=("retain_pct", "median"),
                                             min_retain_pct=("retain_pct", "min"), max_retain_pct=("retain_pct", "max")).reset_index()
    tot = R.assign(k=R.n_kept.astype(float), a=R.n_analysed.astype(float)).groupby(["estimand", "ps", "arm_role"])[["k", "a"]].sum()
    ret = ret.merge((100 * tot.k / tot.a).rename("aggregate_retain_pct").reset_index(), on=["estimand", "ps", "arm_role"])
    ret.to_csv(OUT / "retention.csv", index=False)
    Dv = F[F.estimand.str.startswith("pp_ipcw")].groupby(["estimand", "ps", "arm_role"]).agg(
        median_dev_pct=("dev_pct", "median"), median_max_w=("max_w", "median"), max_max_w=("max_w", "max")).reset_index()
    Dv.to_csv(OUT / "deviation.csv", index=False)
    # markdown tables
    Lm = ["# v1.9 adherence / run-in sensitivity: tables (generated by scripts/v19/sens_adherence.py summarize)\n",
          "|Δ| = mean |log HR − RCT log HR|; closer = trials with ECG |Δ| < base |Δ|; cons = % |z| < 1.96; p = exact one-sided "
          "sign-flip (ECG better); bs = within-set benchmark shuffle (20,000); cl = comparator-cluster sign-flip. "
          "Full cohort; A/B = split halves.\n"]
    for ps in PSS:
        Lm += [f"\n## {ps}\n", "| estimand | set | k | \\|Δ\\| unmatched | \\|Δ\\| base | \\|Δ\\| +ECG | \\|Δ\\| +perm ECG | closer | cons base→ECG (perm) "
               "| p ECG vs base | p ECG vs perm | bs p | cl p (n cl) | p A / B |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, x in S[S.ps == ps].iterrows():
            if x.n_trials == 0:
                continue
            Lm.append(f"| {EST_LAB[x.estimand]} | {x.scope} | {x.n_trials} | {x.absd_unmatched:.3f} | {x.absd_base:.3f} | {x.absd_ECG:.3f} | "
                      f"{x.absd_shufECG:.3f} | {x.k_closer} | {x.cons_base:.0f}→{x.cons_ECG:.0f} ({x.cons_shufECG:.0f}) | {fmt_p(x.p_ecg_vs_base)} | "
                      f"{fmt_p(x.p_ecg_vs_shuf)} | {fmt_p(x.bshuf_p)} | {fmt_p(x.cluster_p)} ({x.n_clusters}) | {fmt_p(x.p_A)} / {fmt_p(x.p_B)} |")
    Lm += ["\n## Landmark retention (% of analysed matched patients kept at day 90; applicable trials)\n",
           "| estimand | PS | arm | trials | aggregate % | median % | min % | max % |", "|---|---|---|---|---|---|---|---|"]
    for _, x in ret.iterrows():
        Lm.append(f"| {x.estimand} | {x.ps} | {x.arm_role} | {x.trials} | {x.aggregate_retain_pct:.1f} | {x.median_retain_pct:.1f} | "
                  f"{x.min_retain_pct:.1f} | {x.max_retain_pct:.1f} |")
    Lm += ["\n## Per-trial (P1; HR base → +ECG, RCT HR; — = not applicable / not estimable)\n",
           "| trial | design | RCT | ITT | PP IPCW 365 | switch IPCW | run-in 90 | retained % (base) | deviating % G365 (base) |",
           "|---|---|---|---|---|---|---|---|---|"]

    def hh(x, est, ps="P1"):
        a, b = x.get(f"{est}_{ps}_hr_base", np.nan), x.get(f"{est}_{ps}_hr_ECG", np.nan)
        return "—" if not (np.isfinite(a) and np.isfinite(b)) else f"{a:.2f}→{b:.2f}"

    for _, x in P.iterrows():
        rp = x.get("runin90_P1_retain_pct_base", np.nan)
        dp = x.get("dev365_P1_pct_base", np.nan)
        Lm.append(f"| {x.trial} | {x.design.split(' (')[0]} | {x.rct_hr:.2f} | {hh(x, 'itt')} | {hh(x, 'pp_ipcw_365')} | "
                  f"{hh(x, 'pp_ipcw_switch')} | {hh(x, 'runin90')} | {'—' if not np.isfinite(rp) else f'{rp:.0f}'} | "
                  f"{'—' if not np.isfinite(dp) else f'{dp:.0f}'} |")
    txt = "\n".join(Lm) + "\n"
    (OUT / "tables.md").write_text(txt)
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 60)
    print(S.round(4).to_string(index=False))
    print(ret.round(1).to_string(index=False))
    print(Dv.round(2).to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run", "verify", "summarize"])
    ap.add_argument("--trials", default=",".join(ALL))
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    os.umask(0o077)
    if a.cmd == "run":
        run(a.trials.split(","), a.workers)
    elif a.cmd == "verify":
        verify()
    else:
        summarize()


if __name__ == "__main__":
    main()
