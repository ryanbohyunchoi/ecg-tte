#!/usr/bin/env python
"""PS-Clinical (no LVEF) with 5-draw multiple imputation on the VERSION 1 cohorts (the primary cohorts again, user decision
2026-10-13, pipeline.md). Doc: docs/v1_psclin_mi/PS_CLINICAL_MI_V1.md.

A mode of scripts/v2_psclin_mi/psclin_mi.py (imported, not changed). Differences from its v2 mode:
  cohort       version 1 analysed rows (all rows, version 1 outcomes); within-cohort PCs = version 1 PCs (rows = all)
  imputation   on the same population as the version 1 no-LVEF re-imputation: the full pre-ECG baseline roster
               (claude-<trial>-baseline-v11/restricted_baseline_observed.parquet), LVEF removed (neither target nor
               predictor), build_core_baseline.impute(m = 5), seeds 20260923 + k - 1; draw 1 asserted equal to the
               version 1 re-imputed table (claude-v1-psclin-nolvef/imputation) in every trial
  cells        psclin_mi.task(n, "v1", k) for k = 1..5 (rung clinical_nolvef; 6 configs x 6 arms + CLMBR32 main)
  gate         draw 1 cells vs audits/claude-v1-psclin-nolvef/cells/restricted_cells.parquet (psclin_mi.gate; exact)
  combine      as psclin_mi.combine (|SMD| averaged across draws; Rubin's rules for log HR)
  summaries    other rungs = version 1 cells (grid.reference()); clinical_nolvef single draw = the version 1 cells
               (renamed clinical_nolvef_v1single; = draw 1 by the gate); sets S32 (paper 1, v19 tiers, Limited excluded),
               S38, and S29 / Snew / SEG for the record
Usage:
  psclin_mi_v1.py impute [--workers 24] | run [--workers 32] | gate | combine | summarize [--workers 32] | privacy | done
Outputs (umask 077, not committed): audits/claude-v1-psclin-mi/
  imputation/restricted_completed_nolvef_v1_<trial>.parquet (5 draws), imputation_log_v1.json
  cells/restricted_cells_v1.parquet (per draw), restricted_cells_v1_mi.parquet (MI, layout of restricted_cells_v2_mi),
        restricted_cells_v1_mi_v1layout.parquet (MI, exact column layout of the version 1 psclin cells, rung clinical_nolvef),
        cells_v1_mi.csv (suppressed), gate.csv, gate_status.json
  summary/contrasts.csv, domains.csv, ladder.csv, per_trial.csv, rubin_diagnostics.csv, failed_cells.csv
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import psclin_mi as PM  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

K, E, P2, SP, GR, PSC, V2S = PM.K, PM.E, PM.P2, PM.SP, PM.GR, PM.PSC, PM.V2S
VN, NONCODED, M, RUNG, MI = PM.VN, PM.NONCODED, PM.M, PM.RUNG, PM.MI

# redirect psclin_mi's output paths (module globals read at call time; inherited by forked workers)
OUT = K.A / "claude-v1-psclin-mi"
IMP, CEL, SUM, LOGD = OUT / "imputation", OUT / "cells", OUT / "summary", OUT / "logs"
PM.OUT, PM.IMP, PM.CEL, PM.SUM = OUT, IMP, CEL, SUM
SINGLE = f"{RUNG}_v1single"
PM.MASK_RUNG[SINGLE] = PM.MASK_RUNG[RUNG]
PM.LABEL[SINGLE] = "PS-Clinical (no LVEF, version 1 single draw)"


# ================================================================ imputation (full baseline roster, 5 draws)
def _imp_task(n):
    from build_core_baseline import impute
    K.umask()
    t0 = time.time()
    B = K.A / f"claude-{n}-baseline-v11"
    obs = pd.read_parquet(B / "restricted_baseline_observed.parquet").set_index("patient_key")
    tr = obs.pop("treated").to_numpy()
    X = obs.drop(columns=["lvef"])
    Z = impute(X, tr, M)
    out = []
    for k, Zk in enumerate(Z, start=1):
        assert list(Zk.columns) == list(X.columns) and Zk.index.equals(X.index)
        assert not Zk.isna().any().any(), (n, k)
        assert bool(np.array_equal(Zk.where(X.notna()).fillna(-9e9).to_numpy(), X.fillna(-9e9).to_numpy()))
        out.append(Zk.assign(draw=k))
    # gate 1: draw 1 = the version 1 re-imputed table (same population, same seed), exactly
    ref = pd.read_parquet(PSC.imp_path(n)).set_index("patient_key")
    assert ref.index.equals(Z[0].index) and np.array_equal(ref[list(X.columns)].to_numpy(float), Z[0].to_numpy(float)), n
    # draws differ from each other where values were imputed
    miss = [c for c in X.columns if X[c].isna().any()]
    if miss:
        assert not np.array_equal(Z[0][miss].to_numpy(float), Z[1][miss].to_numpy(float)), n
    W = pd.concat(out)
    W.insert(0, "treated", np.tile(tr, M))
    W.reset_index().to_parquet(PM.imp_path("v1", n))
    print(f"impute v1 x{M} {n} {time.time() - t0:.0f}s", flush=True)
    return dict(trial=n, cohort="v1", draws=M, draw1_equals_v1=True, cols_with_missing=len(miss),
                miss_frac={c: round(float(X[c].isna().mean()), 3) for c in miss}, secs=round(time.time() - t0, 1))


def impute_all(workers):
    from multiprocessing import get_context
    K.umask()
    IMP.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle")
    tk = sorted(K.ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    with get_context("fork").Pool(min(workers, len(tk))) as p:
        res = p.map(_imp_task, tk, chunksize=1)
    (IMP / "imputation_log_v1.json").write_text(json.dumps(res, indent=1))
    print("imputed v1", len(res), "draw 1 = version 1 in", sum(r["draw1_equals_v1"] for r in res), flush=True)


# ================================================================ cells (5 draws)
def run(workers):
    from multiprocessing import get_context
    K.umask()
    CEL.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle",
           "rewind", "cabana-v2", "transform-hf", "precision")
    tk = sorted(K.ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    jobs = [(n, "v1", k) for n in tk for k in range(1, M + 1)]
    with get_context("fork").Pool(min(workers, len(jobs))) as p:
        res = p.map(PM.task, jobs, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    assert set(R.draw) == set(range(1, M + 1)) and len(R) == M * 38 * (6 * 6 + 1), len(R)
    R.to_parquet(CEL / "restricted_cells_v1.parquet")
    (CEL / "log_v1.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    (CEL / "run_v1.done").write_text(time.strftime("%Y-%m-%d %H:%M") + "\n")
    print("done v1", len(R), flush=True)


# ================================================================ combination (= psclin_mi.combine, v1 source)
def combine():
    K.umask()
    R = pd.read_parquet(CEL / "restricted_cells_v1.parquet")
    assert set(R.draw) == set(range(1, M + 1))
    R = R.assign(failed=V2S.failed(R))
    smd = [f"smd:{c}" for c in VN]
    out = []
    for (n, cfg, a), g in R.groupby(["trial", "config", "arm"], sort=False):
        g = g.sort_values("draw")
        assert len(g) == M and (g.n.nunique() == 1) and (g.n_t.nunique() == 1), (n, cfg, a)
        r = g.iloc[0].to_dict()
        r.update(rung=MI, draw=0)
        if g.failed.any():
            r.update(cell_failed=f"failed in {int(g.failed.sum())}/{M} draws", loghr=np.nan, se=np.nan, between_var=np.nan,
                     within_var=np.nan, **{c: np.nan for c in smd})
            r["n_pairs"] = float(g.n_pairs.min())
        else:
            q, u = g.loghr.to_numpy(float), g.se.to_numpy(float) ** 2
            W, B = float(u.mean()), float(q.var(ddof=1))
            r.update(loghr=float(q.mean()), se=float(np.sqrt(W + (1 + 1 / M) * B)), within_var=W, between_var=B,
                     n_pairs=float(g.n_pairs.min()), ess_t=float(g.ess_t.mean()), ess_c=float(g.ess_c.mean()),
                     retain=float(g.retain.mean()), cell_failed="",
                     **{c: float(g[c].abs().mean()) for c in smd})  # |SMD| averaged across draws (nan if unobserved)
        r.pop("failed")
        out.append(r)
    C = pd.DataFrame(out)
    ref = pd.read_parquet(K.A / "claude-v2-psclin-mi" / "cells" / "restricted_cells_v2_mi.parquet")
    assert list(C.columns) == list(ref.columns), "layout differs from restricted_cells_v2_mi"
    C.to_parquet(CEL / "restricted_cells_v1_mi.parquet")
    # same rows in the exact column layout / dtypes of the version 1 psclin cells (rung clinical_nolvef)
    Q = pd.read_parquet(K.REF_PSCLIN)
    Q = Q[Q.rung == RUNG]
    L = C.assign(rung=RUNG)[list(Q.columns)]
    for c in Q.columns:
        if L[c].dtype != Q[c].dtype:
            L[c] = L[c].astype(Q[c].dtype)
    L = L.set_index(["trial", "config", "arm"]).loc[pd.MultiIndex.from_frame(Q[["trial", "config", "arm"]])].reset_index()[list(Q.columns)]
    assert len(L) == len(Q) and (L.dtypes == Q.dtypes).all()
    L.to_parquet(CEL / "restricted_cells_v1_mi_v1layout.parquet")
    P2.suppress(C).to_csv(CEL / "cells_v1_mi.csv", index=False)
    print("combined", len(C), "failed", int(C.cell_failed.astype(str).ne("").sum()), flush=True)


# ================================================================ summaries
def all_cells():
    """version 1 cells of the other rungs + version 1 single draw (renamed) + MI rung + each draw as a rung."""
    G = GR.reference()
    G = G[G.rung.isin(["P1", "P5", "PS10", "Flags", "hdPS200", "clinical", RUNG])]
    G = G.assign(rung=G.rung.replace({RUNG: SINGLE}))
    C = pd.read_parquet(CEL / "restricted_cells_v1_mi.parquet")
    D = pd.read_parquet(CEL / "restricted_cells_v1.parquet")
    D = D.assign(rung=RUNG + "#" + D.draw.astype(str))
    cols = list(G.columns.intersection(C.columns))
    return pd.concat([G[cols], C[cols], D[cols]], ignore_index=True)


def contrasts():
    L = []
    for c in PM.contrasts():
        c = tuple(x.replace(f"{RUNG}_v2single", SINGLE) if isinstance(x, str) else x for x in c)
        L.append(c)
    return L


def _row(args):
    sname, c = args
    return V2S._row(("v1", sname, c))


def rubin_diag():
    C = pd.read_parquet(CEL / "restricted_cells_v1_mi.parquet")
    C = C[C.cell_failed.fillna("").astype(str).eq("")]
    T = C.within_var + (1 + 1 / M) * C.between_var
    C = C.assign(frac_between=(1 + 1 / M) * C.between_var / T, se_ratio=np.sqrt(T / C.within_var))
    return C.groupby(["config", "arm"]).agg(k_trials=("trial", "size"), frac_between_median=("frac_between", "median"),
                                           frac_between_max=("frac_between", "max"), se_inflation_median=("se_ratio", "median"),
                                           se_inflation_max=("se_ratio", "max")).reset_index()


def summarize(workers):
    from multiprocessing import get_context
    K.umask()
    st = json.loads((CEL / "gate_status.json").read_text())
    if not st["passed"]:
        raise SystemExit("gate failed; not summarising")
    SUM.mkdir(parents=True, exist_ok=True)
    sets = PM.load_sets()
    sets = {k: sets[k] for k in ("S32", "S38", "S29", "Snew", "SEG") if k in sets}
    R = all_cells()
    F, SM, RET, NF = PM.load_F(R)
    P2._G.update(F=F, SM=SM, CL=K.V.cluster_of(), RET=RET, SETS=sets)
    jobs = [(s, c) for s in sets for c in contrasts()]
    with get_context("fork").Pool(min(workers, len(jobs))) as p:
        res = p.map(_row, jobs, chunksize=2)
    S = pd.DataFrame([r for r, _ in res])
    D = pd.DataFrame([d for _, ds in res for d in ds])
    for sname in sets:
        ms = (S.set == sname) & S.kind.eq("within")
        long = S.loc[ms, P2.BAL_FAM].stack(dropna=True)
        q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
        for c in P2.BAL_FAM:
            S.loc[ms, f"q_{c}_fam"] = q[c] if c in q else np.nan
    S.to_csv(SUM / "contrasts.csv", index=False)
    D.to_csv(SUM / "domains.csv", index=False)
    pd.DataFrame(PM.ladder_levels(SM, sets)).to_csv(SUM / "ladder.csv", index=False)
    rubin_diag().to_csv(SUM / "rubin_diagnostics.csv", index=False)
    NFd = pd.DataFrame([dict(rung=a, config=b, arm=c, trial=d) for a, b, c, d in NF])
    (NFd.groupby(["rung", "config", "arm"]).size().rename("n_trials_failed").reset_index() if len(NFd) else
     pd.DataFrame(columns=["rung", "config", "arm", "n_trials_failed"])).to_csv(SUM / "failed_cells.csv", index=False)
    pt = []
    for rg in PM.LADDER:
        for a in ("base", "ECG", "shufECG"):
            k = (rg, "main", a)
            for t in K.ALL:
                pt.append(dict(trial=t, key=K.KEY[t], rung=rg, arm=a, m54=float(SM[k][NONCODED].loc[t].mean()),
                               absd=F[k].loc[t, "absd"], loghr=F[k].loc[t, "loghr"], se=F[k].loc[t, "se"], rb=F[k].loc[t, "rb"]))
    pd.DataFrame(pt).to_csv(SUM / "per_trial.csv", index=False)
    print("summaries written", sorted(sets), flush=True)


def done():
    st = json.loads((CEL / "gate_status.json").read_text())
    pv = json.loads((OUT / "privacy_scan.json").read_text())
    assert st["passed"] and pv["clean"]
    (OUT / "DONE").write_text(json.dumps(dict(gate_passed=True, privacy_clean=True, time=time.strftime("%Y-%m-%d %H:%M"))) + "\n")
    print("DONE written")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["impute", "run", "gate", "combine", "summarize", "privacy", "done"])
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    w = min(a.workers, 32)
    K.umask()
    {"impute": lambda: impute_all(w), "run": lambda: run(w), "gate": PM.gate, "combine": combine,
     "summarize": lambda: summarize(w), "privacy": PM.privacy, "done": done}[a.cmd]()
