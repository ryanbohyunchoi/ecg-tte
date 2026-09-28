#!/usr/bin/env python
"""v1.8 Plan A: prespecified AF confirmation (docs/v17/V18_PLANS.md, fixed in 760981a before any v1.8 result).

The code path is scripts/v17/v17_confirm.py, imported unchanged; only the trial list, the covariate paths and the
P5 diagnosis list (exactly as scripts/v17/s11_p5.py) are set here:
  * trial list: V.ALL = the 18 v1.6 trials (i = 0..17) + v13_common.V17 (i = 18..32) + v13_common.V18 in registry
    order (frail-af 33, laaos3 34, protect-af 35, raft-af 36, active-w 37); halves seed = 16060 + i (s1_ladder.halves).
  * cdirs(): V18 trials read claude-v18-covars / claude-v18-covars2b; all others unchanged (v16 / v17).
  * PS: P1 = T.demo; P5 = T.demo + hypertension_v11, t2d, cad_ihd (covars v1) + atrial_fibrillation (T.cov) + HF
    (covars2b hf_any_365, else elx_chf) = s11_p5 (V.P2DX monkeypatched; the engine's "P2" label is renamed "P5" on output).
  * arms base, +ECG32, +shufECG, +noise32, unmatched; E.run_cell(..., estimator=("match", 0.2, 1)).
Benchmarks (rb, rs) are T.rb, T.rs = v13_common.bench(key) from trial_specs.PUBLISHED; for PROTECT AF this is
log(0.62) with SE = (log 1.25 - log 0.35) / (2 * 1.959964) from the registered 95% credible interval.

Endpoints (Plan A). Per trial, full cohort: absd = |loghr - rb| (primary), z2, cons (|z| < 1.96, z uses both SEs),
lt01 (% of the 58 held-out |SMD| < 0.1), x_lt01 (covars2b non-proximal panel, v17 logic).
  * one-sided exact sign-flip across trials of (ECG better than base), also vs shufECG and vs noise32;
    cluster-level (comparator clusters, docs/v17/trial_selection.json), leave-one-out max p, halves A / B.
  * co-primary benchmark shuffle (absd, z2): per draw, the k analysed trials receive k RCT benchmarks drawn
    jointly as (rb, rs) pairs, without replacement, from all 38 RCTs of the benchmark (33 + 5), 20,000 draws,
    numpy default_rng(0); statistic mean(|le - q| - |lb - q|) (absd) or the z2 analogue; p = P(null <= observed).
Sets: AF-5 (the new trials; primary), AF-12 (the 7 v1.7 AF-category trials aristotle, rocket-af, rely, east-afnet4,
cabana-v2, affirm, af-chf + the 5), and blinded subsets S_fid / S_both within each.
The 33 existing trials are read from claude-v17-confirm/results_all.csv (P1, unmatched) and results_p5.csv (P5).

Usage:
  v18_af_confirm.py run [--trials a,b] [--tag NAME]   -> OUT/results_<tag>.csv (default: the 5 V18 trials, tag af5)
  v18_af_confirm.py verify --tag NAME                  compare trials in results_<tag> with the v1.7 files (max dev must be 0)
  v18_af_confirm.py summarize                          -> OUT/summary.csv, OUT/per_trial_af5.csv, OUT/per_trial_af12.csv
Aggregates only; OUT umask 077.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v17"))
import v17_confirm as V  # noqa: E402  (sets thread env vars, imports engine)

import argparse  # noqa: E402
import json  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from v13_common import EXTRA, PRIMARY, V18  # noqa: E402

A = V.A
OUT = A / "claude-v18-af-confirm"
V17OUT = A / "claude-v17-confirm"
AF5 = list(V18)
AF7 = ["aristotle", "rocket-af", "rely", "east-afnet4", "cabana-v2", "affirm", "af-chf"]  # V17_PATTERNS AF category
AF12 = AF7 + AF5
NPERM = 20000

# ---- the only changes to the v1.7 code path (trial list, paths, P5 list)
V.P2DX = ["hypertension_v11", "t2d", "cad_ihd"]  # = s11_p5
V.ALL = V.OLD + V.NEW + AF5  # index 33..37 for V18 -> seed 16060 + i
V.KEY.update({n: {**PRIMARY, **EXTRA}[n][0] for n in AF5})
_cdirs17 = V.cdirs


def cdirs(n):
    if n in AF5:
        return A / "claude-v18-covars", A / "claude-v18-covars2b"
    return _cdirs17(n)


V.cdirs = cdirs
ALL = V.ALL
KEY = V.KEY
ROLES = V.ROLES
PSS = ("P1", "P5")


def run(trials, workers, tag):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    for n in trials:
        if n in AF5 and not (A / f"claude-v18-trials/{n}.READY").exists():
            raise RuntimeError(f"{n} not READY")
    tk = sorted([(n, h) for n in trials for h in ("full", "A", "B")], key=lambda x: x[1] != "full")
    with Pool(min(workers, len(tk), 32)) as p:
        res = p.map(V.task, tk, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    R["ps"] = R.ps.replace({"P2": "P5"})
    R["set"] = np.where(R.trial.isin(AF5), "v18af5", R["set"])
    R.to_csv(OUT / f"results_{tag}.csv", index=False)
    (OUT / f"log_{tag}.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    print("done", tag, flush=True)


def ref33():
    a = pd.read_csv(V17OUT / "results_all.csv")
    a = a[a.ps.isin(["P1", "none"])]
    b = pd.read_csv(V17OUT / "results_p5.csv")
    b = b[b.ps == "P2"].assign(ps="P5")
    return pd.concat([a, b], ignore_index=True)


def verify(tag):
    R = pd.read_csv(OUT / f"results_{tag}.csv")
    Q = ref33()
    cols = [c for c in R.columns if c in Q.columns and c not in ("trial", "key", "set", "idx", "half", "ps", "arm_role", "secs")  # secs = wall clock
            and pd.api.types.is_numeric_dtype(R[c])]
    rows = []
    for (n, h, ps, role), g in R.groupby(["trial", "half", "ps", "arm_role"]):
        q = Q[(Q.trial == n) & (Q.half == h) & (Q.ps == ps) & (Q.arm_role == role)]
        assert len(g) == 1 and len(q) == 1, (n, h, ps, role, len(g), len(q))
        a, b = g.iloc[0], q.iloc[0]
        d = 0.0
        for c in cols:
            if pd.isna(a[c]) and pd.isna(b[c]):
                continue
            d = max(d, np.inf if (pd.isna(a[c]) or pd.isna(b[c])) else abs(float(a[c]) - float(b[c])))
        rows.append(dict(trial=n, half=h, ps=ps, arm=role, idx=int(a["idx"]), idx_ref=int(b["idx"]), ncols=len(cols), maxdev=d))
    Vd = pd.DataFrame(rows)
    Vd.to_csv(OUT / f"verify_{tag}.csv", index=False)
    print(Vd.groupby(["trial", "ps"]).maxdev.max().to_string())
    print("columns compared", len(cols), "cells", len(Vd), "overall max deviation", Vd.maxdev.max())


# ---------------------------------------------------------------- statistics
sf = V.signflip_1s


def analyse(M, trials, BENCH, seed=0, nperm=NPERM):
    CL = V.cluster_of()
    rb_all, rs_all = BENCH
    out = []
    for ps in PSS:
        F = {r: M["full"][ps][r].loc[trials] for r in ROLES}
        for m in V.METRICS:
            sgn = 1 if m in V.HIGHER else -1
            b, e, s, z = (F[r][m] for r in ROLES)
            d = sgn * (e - b)
            row = dict(ps=ps, metric=m, n=len(trials), base=b.mean(), ecg=e.mean(), shuf=s.mean(), noise=z.mean(),
                       d_ecg_minus_base=(e - b).mean(), k_better=f"{int((d > 0).sum())}/{int(d.notna().sum())}",
                       p=sf(d), p_vs_shuf=sf(sgn * (e - s)), p_vs_noise=sf(sgn * (e - z)),
                       d_shuf_minus_base=(s - b).mean(), d_noise_minus_base=(z - b).mean(),
                       p_shuf_vs_base=sf(sgn * (s - b)), p_noise_vs_base=sf(sgn * (z - b)))
            lab = [CL[KEY[t]] for t in trials]
            cl = pd.Series(d.to_numpy(), index=lab).groupby(level=0).mean()
            row.update(n_clusters=len(cl), cluster_p=sf(cl.to_numpy()))
            for nm, other in (("shuf", s), ("noise", z)):
                row[f"cluster_p_vs_{nm}"] = sf(pd.Series((sgn * (e - other)).to_numpy(), index=lab).groupby(level=0).mean().to_numpy())
            row["loo_max_p"] = max(sf(d.drop(t)) for t in trials) if len(trials) > 1 else np.nan
            for h in ("A", "B"):
                row[f"p_{h}"] = sf(sgn * (M[h][ps]["ECG"].loc[trials][m] - M[h][ps]["base"].loc[trials][m]))
            if m in ("absd", "z2"):
                lb, sb, le, se_ = F["base"].loghr.to_numpy(), F["base"].se.to_numpy(), F["ECG"].loghr.to_numpy(), F["ECG"].se.to_numpy()

                def st(q, v):
                    if m == "absd":
                        return (np.abs(le - q) - np.abs(lb - q)).mean()
                    return ((le - q) ** 2 / (se_ ** 2 + v ** 2) - (lb - q) ** 2 / (sb ** 2 + v ** 2)).mean()
                obs = st(F["base"].rb.to_numpy(), F["base"].rs.to_numpy())
                rng = np.random.default_rng(seed)
                k = len(trials)
                null = np.empty(nperm)
                for j in range(nperm):
                    ix = rng.permutation(len(rb_all))[:k]  # joint (rb, rs) pairs, without replacement, from all 38
                    null[j] = st(rb_all[ix], rs_all[ix])
                row.update(bshuf_obs=obs, bshuf_null_mean=null.mean(), bshuf_p=float((null <= obs + 1e-12).mean()),
                           bshuf_nbench=len(rb_all), bshuf_ndraw=nperm)
            out.append(row)
    return out


def load_M():
    R = pd.concat([ref33(), pd.read_csv(OUT / "results_af5.csv")], ignore_index=True)
    R = R[(R.arm_role != "unmatched") & R.trial.isin(ALL)]
    assert R.groupby(["trial", "half", "ps", "arm_role"]).size().max() == 1
    assert R.trial.nunique() == 38, R.trial.nunique()
    return {h: {ps: {r: V.trial_metrics(R[(R.half == h) & (R.ps == ps) & (R.arm_role == r)]) for r in ROLES} for ps in PSS}
            for h in ("full", "A", "B")}


def summarize():
    os.umask(0o077)
    M = load_M()
    F0 = M["full"]["P1"]["base"].loc[ALL]
    BENCH = (F0.rb.to_numpy(), F0.rs.to_numpy())
    J = json.loads((V.DOCS / "trial_selection.json").read_text())
    inv = {v: k for k, v in KEY.items()}
    sets = {("AF5", "all"): AF5, ("AF12", "all"): AF12, ("AF7", "all"): AF7}
    for sub in ("S_fid", "S_both"):
        sets[("AF5", sub)] = [inv[k] for k in J["subsets"]["v18_new_af_5"][sub]]
        allsub = set(J["subsets"]["all_trials"][sub])
        sets[("AF12", sub)] = [t for t in AF12 if KEY[t] in allsub]
    rows = []
    for (scope, sub), trials in sets.items():
        for r in analyse(M, trials, BENCH):
            rows.append(dict(scope=scope, subset=sub, trials=",".join(KEY[t] for t in trials), **r))
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "summary.csv", index=False)
    CL = V.cluster_of()
    for nm, trs in (("af5", AF5), ("af12", AF12)):
        pt = []
        for n in trs:
            tr = J["trials"][KEY[n]]
            rec = dict(trial=n, idx=ALL.index(n), rct_hr=float(np.exp(M["full"]["P1"]["base"].loc[n, "rb"])),
                       rct_logse=M["full"]["P1"]["base"].loc[n, "rs"], fidelity=bool(tr["fidelity_include"]),
                       fidelity_strict=bool(tr["fidelity_include_strict"]), ecg_relevance=tr["ecg_relevance"], cluster=CL[KEY[n]])
            for ps in PSS:
                for role, lab in (("base", "base"), ("ECG", "ecg"), ("shufECG", "shuf"), ("noise", "noise")):
                    x = M["full"][ps][role].loc[n]
                    rec.update({f"{ps}_hr_{lab}": np.exp(x.loghr), f"{ps}_se_{lab}": x.se, f"{ps}_absd_{lab}": x.absd,
                                f"{ps}_cons_{lab}": x.cons, f"{ps}_z2_{lab}": x.z2, f"{ps}_lt01_{lab}": x.lt01, f"{ps}_xlt01_{lab}": x.x_lt01})
            pt.append(rec)
        pd.DataFrame(pt).to_csv(OUT / f"per_trial_{nm}.csv", index=False)
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 60)
    print(S.round(4).to_string(index=False))
    print(pd.read_csv(OUT / "per_trial_af5.csv").round(3).T.to_string())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run", "verify", "summarize"])
    ap.add_argument("--trials", default=",".join(AF5))
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--tag", default="af5")
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
