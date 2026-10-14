#!/usr/bin/env python
"""Step 2 of the queue 2026-10-14 (s31): the version 1 Python summaries re-run on the new primary trial set S31 (paper 1's 32
minus PROTECT AF, excluded at feasibility: smaller arm < 350; pipeline.md update 2026-10-14), with the same code paths as before
and S32 re-run alongside as an exact regression gate. Nothing is refitted: existing cells only.

  A. scripts/v2_cohorts/summarize.py, cohort v1 (version 1 cells: P1, P5, PS10, Flags, hdPS200, clinical, clinical_nolvef single
     draw; every WITHIN contrast incl. CLMBR-T arms, base-to-base and across contrasts, all 6 PS methods; per-domain relative
     reductions; ladder levels)                                  -> OUT/summary_v1/{contrasts,domains,ladder}.csv
  B. scripts/v2_psclin_mi/psclin_mi_v1.py summarize (PS-Clinical (no LVEF), 5-draw MI on version 1 cohorts, plus the P1 / P5 /
     PS10 / hdPS200 ladder rows, the 5 single draws and the v1 single draw)  -> OUT/summary_mi/{contrasts,domains,ladder}.csv
  C. scripts/v2_cohorts/random_removal.py pooled() on its existing restricted random-removal cells (spec-v2 fixes sensitivity)
                                                                 -> OUT/summary_v1/random_removal_summary.csv
Gates: every S32 row of A, B and C equals the committed run (to 1e-12: floating-point summation order) (audits/claude-v2-cohorts/summary, audits/claude-v1-psclin-mi/summary)
in every column (NaN = NaN). Endpoints and tests are the summarizers' own (paper2_grid._row): relative reduction in mean |SMD|
(4,000 trial resamples, seed 20261001), exact sign-flip (one-sided for a representation vs its base or placebo, two-sided
otherwise), comparator-cluster sign-flip, leave-one-trial-out, |dlog HR| with sign-flip and benchmark-permutation P (20,000
draws), BH-FDR within (cohort, set).

Usage (tte-analysis env): python scripts/s31/s31_summaries.py [--workers 32]
Outputs: audits/claude-s31-20261014/summary_{v1,mi}/ (umask 077; restricted directory, aggregates only, not committed)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v2_psclin_mi"))
sys.path.insert(0, str(HERE.parent / "v2_cohorts"))
import psclin_mi_v1 as MV1  # noqa: E402  (imports psclin_mi, v2common, summarize; sets thread env vars)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import random_removal as RRM  # noqa: E402

PM, K, V2S, P2, E = MV1.PM, MV1.K, MV1.V2S, MV1.P2, MV1.E
OUT = K.A / "claude-s31-20261014"
PROT = "protect-af"


def s31_sets():
    S = dict(K.SETS)
    s31 = [n for n in S["S32"] if n != PROT]
    assert len(S["S32"]) == 32 and len(s31) == 31 and PROT in S["S32"]
    return {"S31": s31, "S32": S["S32"]}


def fdr(S, sets):
    for sname in sets:
        ms = (S.set == sname) & S.kind.eq("within")
        long = S.loc[ms, P2.BAL_FAM].stack(dropna=True)
        q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
        for c in P2.BAL_FAM:
            S.loc[ms, f"q_{c}_fam"] = q[c] if c in q else np.nan
    return S


def run_v1(workers, sets):
    """A: scripts/v2_cohorts/summarize.run for cohort v1, on the given sets (same functions; K.SETS patched for ladder_levels)."""
    from multiprocessing import get_context
    out = OUT / "summary_v1"
    out.mkdir(parents=True, exist_ok=True)
    R = V2S.cells("v1")
    F, SM, RET, NF = V2S.load_F(R)
    K.SETS = sets
    P2._G.update(F=F, SM=SM, CL=K.V.cluster_of(), RET=RET, SETS=sets)
    jobs = [("v1", s, c) for s in sets for c in V2S.contrasts()]
    with get_context("fork").Pool(min(workers, len(jobs))) as p:
        res = p.map(V2S._row, jobs, chunksize=2)
    S = fdr(pd.DataFrame([r for r, _ in res]), sets)
    S.to_csv(out / "contrasts.csv", index=False)
    pd.DataFrame([d for _, ds in res for d in ds]).to_csv(out / "domains.csv", index=False)
    pd.DataFrame(V2S.ladder_levels(SM, "v1")).to_csv(out / "ladder.csv", index=False)
    return S


def run_mi(workers, sets):
    """B: psclin_mi_v1.summarize on the given sets (its all_cells / load_F / contrasts / _row; outputs redirected)."""
    from multiprocessing import get_context
    out = OUT / "summary_mi"
    out.mkdir(parents=True, exist_ok=True)
    assert json.loads((MV1.CEL / "gate_status.json").read_text())["passed"]
    R = MV1.all_cells()
    F, SM, RET, NF = PM.load_F(R)
    P2._G.update(F=F, SM=SM, CL=K.V.cluster_of(), RET=RET, SETS=sets)
    jobs = [(s, c) for s in sets for c in MV1.contrasts()]
    with get_context("fork").Pool(min(workers, len(jobs))) as p:
        res = p.map(MV1._row, jobs, chunksize=2)
    S = fdr(pd.DataFrame([r for r, _ in res]), sets)
    S.to_csv(out / "contrasts.csv", index=False)
    pd.DataFrame([d for _, ds in res for d in ds]).to_csv(out / "domains.csv", index=False)
    pd.DataFrame(PM.ladder_levels(SM, sets)).to_csv(out / "ladder.csv", index=False)
    return S


def run_rr(sets):
    """C: random_removal.run's pooling step on its existing restricted cells (no new draws)."""
    K.SETS = sets
    R = pd.read_parquet(K.SUM / "restricted_random_removal_cells.parquet")
    tk = sorted(set(R.trial))
    V1 = MV1.GR.reference()
    V1 = V1[(V1.rung == "P5") & (V1.config == "main") & V1.arm.isin(RRM.ARMS4)]
    V2 = pd.read_parquet(K.CEL / "restricted_cells_v2_all.parquet")
    V2 = V2[(V2.rung == "P5") & (V2.config == "main") & V2.arm.isin(RRM.ARMS4)]
    rows = RRM.pooled(V1, "v1") + RRM.pooled(V2, "v2")
    keepv2 = V2[~V2.trial.isin(tk)]
    for b in sorted(set(R.draw)):
        Z = pd.concat([R[R.draw == b].drop(columns="draw"), keepv2[R.columns.drop("draw")]], ignore_index=True)
        rows += [dict(r, draw=b) for r in RRM.pooled(Z, "random")]
    P = pd.DataFrame(rows)
    out = []
    for (sname, a), g in P.groupby(["set", "arm"]):
        rnd, v1, v2 = g[g.source == "random"], g[g.source == "v1"].iloc[0], g[g.source == "v2"].iloc[0]
        out.append(dict(set=sname, arm=a, relred54_v1=v1.relred54, relred54_v2=v2.relred54, relred54_random_median=rnd.relred54.median(),
                        relred54_random_p5=rnd.relred54.quantile(0.05), relred54_random_p95=rnd.relred54.quantile(0.95),
                        frac_random_le_v2=float((rnd.relred54 <= v2.relred54).mean()), draws=len(rnd),
                        absd_gain_v1=v1.absd_b - v1.absd_a, absd_gain_v2=v2.absd_b - v2.absd_a,
                        absd_gain_random_median=(rnd.absd_b - rnd.absd_a).median(),
                        absd_gain_random_p5=(rnd.absd_b - rnd.absd_a).quantile(0.05),
                        absd_gain_random_p95=(rnd.absd_b - rnd.absd_a).quantile(0.95)))
    S = pd.DataFrame(out)
    S.to_csv(OUT / "summary_v1" / "random_removal_summary.csv", index=False)
    return S


def same(new, old, keys):
    """equality of the S32 rows (all shared columns; NaN = NaN; text exact). Returns (rows, columns, max abs numeric deviation, its column)."""
    a = new.set_index(keys).sort_index()
    b = old.set_index(keys).sort_index()
    assert a.index.equals(b.index), (len(a), len(b))
    cols = [c for c in a.columns if c in b.columns]
    dev, worst = 0.0, None
    for c in cols:
        x, y = a[c], b[c]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            xv, yv = x.to_numpy(float), y.to_numpy(float)
            assert (np.isnan(xv) == np.isnan(yv)).all(), c
            d = float(np.nanmax(np.abs(xv - yv))) if np.isfinite(xv).any() else 0.0
            if d > dev:
                dev, worst = d, c
        else:
            assert (x.fillna("").astype(str) == y.fillna("").astype(str)).all(), c
    return len(a), len(cols), dev, worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    K.umask()
    OUT.mkdir(parents=True, exist_ok=True)
    sets = s31_sets()
    t0 = time.time()
    A = run_v1(min(a.workers, 32), sets)
    print("A done", len(A), f"{time.time() - t0:.0f}s", flush=True)
    B = run_mi(min(a.workers, 32), sets)
    print("B done", len(B), f"{time.time() - t0:.0f}s", flush=True)
    C = run_rr(sets)
    print("C done", f"{time.time() - t0:.0f}s", flush=True)
    gate = {}
    oa = pd.read_csv(K.SUM / "contrasts.csv")
    oa = oa[(oa.cohort == "v1") & (oa.set == "S32")]
    k = ["config", "contrast", "kind"]
    gate["A_contrasts_S32"] = same(A[A.set == "S32"], oa, k)
    od = pd.read_csv(K.SUM / "domains.csv")
    nd = pd.read_csv(OUT / "summary_v1" / "domains.csv")
    gate["A_domains_S32"] = same(nd[nd.set == "S32"], od[(od.cohort == "v1") & (od.set == "S32")], k + ["domain"])
    ol = pd.read_csv(K.SUM / "ladder.csv")
    nl = pd.read_csv(OUT / "summary_v1" / "ladder.csv")
    gate["A_ladder_S32"] = same(nl[nl.set == "S32"], ol[(ol.cohort == "v1") & (ol.set == "S32")], ["rung", "config", "arm", "panel"])
    ob = pd.read_csv(MV1.SUM / "contrasts.csv")
    gate["B_contrasts_S32"] = same(B[B.set == "S32"], ob[ob.set == "S32"], k)
    obd = pd.read_csv(MV1.SUM / "domains.csv")
    nbd = pd.read_csv(OUT / "summary_mi" / "domains.csv")
    gate["B_domains_S32"] = same(nbd[nbd.set == "S32"], obd[obd.set == "S32"], k + ["domain"])
    obl = pd.read_csv(MV1.SUM / "ladder.csv")
    nbl = pd.read_csv(OUT / "summary_mi" / "ladder.csv")
    gate["B_ladder_S32"] = same(nbl[nbl.set == "S32"], obl[obl.set == "S32"], ["rung", "config", "arm", "panel"])
    orr = pd.read_csv(K.SUM / "random_removal_summary.csv")
    gate["C_random_removal_S32"] = same(C[C.set == "S32"], orr[orr.set == "S32"], ["set", "arm"])
    ok = all(v[2] <= 1e-12 for v in gate.values())  # floating-point summation order only (observed <= 1.5e-14)
    res = dict(passed=ok, tolerance=1e-12, gate={k_: dict(rows=v[0], cols=v[1], max_abs_dev=v[2], worst_column=v[3]) for k_, v in gate.items()},
               sets={k_: len(v) for k_, v in sets.items()}, removed=PROT, secs=round(time.time() - t0))
    (OUT / "summary_gate.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    assert ok


if __name__ == "__main__":
    main()
