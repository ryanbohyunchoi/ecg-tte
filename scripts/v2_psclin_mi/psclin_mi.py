#!/usr/bin/env python
"""PS-Clinical (no LVEF) with 5-draw multiple imputation on the spec-v2 fixed cohorts (pipeline.md sections 4 and 6;
queue docs/queue/QUEUE_2026_10_08.md step B). Doc: docs/v2_psclin_mi/PS_CLINICAL_MI.md.

Reused unchanged: build_core_baseline.impute (IterativeImputer(sample_posterior=True), seeds 20260923 + k - 1, k = 1..5,
as scripts/v1_psclin_nolvef/imputation_draws.py); the clinical_nolvef design and masks of
scripts/v1_psclin_nolvef/psclin_nolvef.py; the spec-v2 rows, outcome re-definitions, within-cohort PCs and placebo
permutation of scripts/v2_cohorts/grid.py; the endpoint code of scripts/v21/paper2_grid.py (_row) and
scripts/v20/sens_primary32.py (per_trial).

Cohorts:
  v1  version 1 cohort (all rows), imputation on the full baseline roster exactly as version 1 (gate only, draw 1)
  v2  spec-v2 fixed cohort (rows = not drop_v2; AMPLIFY / LODESTAR / PROVE IT outcomes re-defined); imputation WITHIN the
      fixed cohort (observed baseline rows of the fixed cohort's patients only), LVEF removed (neither target nor predictor)
Rung clinical_nolvef, draws 1-5, 6 configs x arms base, ECG, CLMBR, ECG+CLMBR, shufECG, shufCLMBR (+ CLMBR32, main).
PCs within the cohort rows (ECG 32 = pcs(ecg_raw[rows], 64)[:, :32]; CLMBR-T 64); placebo = rng(424242) permutation.
Combination (per trial, config, arm): |SMD| per item averaged across the 5 draws; log HR by Rubin's rules
  (mean of the 5 log HRs; total variance = mean within variance + (1 + 1/5) x between-draw variance). A combined cell is
  failed if any draw failed (F1 rule: < 11 matched pairs or a failed fit).
Usage:
  psclin_mi.py impute --cohort v1|v2 [--workers 24]  -> OUT/imputation/ (restricted completed tables; aggregate log)
  psclin_mi.py run --cohort v1|v2 [--workers 32]     -> OUT/cells/restricted_cells_<cohort>.parquet
  psclin_mi.py gate                                  -> OUT/cells/gate.csv, gate_status.json (v1 draw 1 vs version 1 cells)
  psclin_mi.py combine                               -> OUT/cells/restricted_cells_v2_mi.parquet, cells_v2_mi.csv
  psclin_mi.py summarize [--workers 32]              -> OUT/summary/*.csv
  psclin_mi.py privacy                               -> OUT/privacy_scan.json
Aggregates only; OUT umask 077; counts 1-10 suppressed in every csv.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v2_cohorts"))
import v2common as K  # noqa: E402  (sets thread env vars and sys.path for the version 1 modules)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import grid as GR  # noqa: E402
import psclin_nolvef as PSC  # noqa: E402
import summarize as V2S  # noqa: E402
from eval_longtail_balance import pcs  # noqa: E402

E, P2, SP = K.E, K.P2, K.SP
VN, NONCODED = K.VN, K.NONCODED
OUT = K.A / "claude-v2-psclin-mi"
IMP, CEL, SUM = OUT / "imputation", OUT / "cells", OUT / "summary"
M = 5
RUNG = "clinical_nolvef"
MI = "clinical_nolvef_mi"
ARMS = K.ARMS
NUMC, TXT = GR.NUMC, GR.TXT


def imp_path(cohort, n):
    return IMP / f"restricted_completed_nolvef_{cohort}_{n}.parquet"


def rows_of(T, n, cohort):
    if cohort == "v1":
        return np.arange(len(T.t))
    D, drop = GR.drop_rows(n, "drop_v2")
    assert D.index.equals(T.keys), n
    return np.where(~drop)[0]


# ================================================================ imputation
def _imp_task(args):
    n, cohort = args
    from build_core_baseline import impute
    K.umask()
    t0 = time.time()
    B = K.A / f"claude-{n}-baseline-v11"
    obs = pd.read_parquet(B / "restricted_baseline_observed.parquet").set_index("patient_key")
    if cohort == "v1":
        m = 1
    else:
        T = GR.load(n)
        keys = T.keys[rows_of(T, n, cohort)]
        assert set(keys) <= set(obs.index)
        obs = obs.loc[keys].rename_axis("patient_key")  # the fixed cohort only, in cohort order
        m = M
    tr = obs.pop("treated").to_numpy()
    X = obs.drop(columns=["lvef"])
    Z = impute(X, tr, m)
    out = []
    for k, Zk in enumerate(Z, start=1):
        assert list(Zk.columns) == list(X.columns) and Zk.index.equals(X.index)
        assert not Zk.isna().any().any(), (n, k)
        assert bool(np.array_equal(Zk.where(X.notna()).fillna(-9e9).to_numpy(), X.fillna(-9e9).to_numpy()))
        out.append(Zk.assign(draw=k))
    W = pd.concat(out)
    W.insert(0, "treated", np.tile(tr, m))
    W.reset_index().to_parquet(imp_path(cohort, n))
    if cohort == "v1":  # draw 1 must equal the version 1 re-imputed table
        ref = pd.read_parquet(PSC.imp_path(n)).set_index("patient_key")
        assert ref.index.equals(Z[0].index) and np.array_equal(ref[list(X.columns)].to_numpy(float), Z[0].to_numpy(float)), n
    miss = [c for c in X.columns if X[c].isna().any()]
    print(f"impute {cohort} {n} {time.time() - t0:.0f}s", flush=True)
    return dict(trial=n, cohort=cohort, draws=m, cols_with_missing=len(miss),
                miss_frac={c: round(float(X[c].isna().mean()), 3) for c in miss}, secs=round(time.time() - t0, 1))


def impute_all(cohort, workers):
    from multiprocessing import get_context
    K.umask()
    IMP.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle")
    tk = sorted(K.ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    with get_context("fork").Pool(min(workers, len(tk))) as p:
        res = p.map(_imp_task, [(n, cohort) for n in tk], chunksize=1)
    (IMP / f"imputation_log_{cohort}.json").write_text(json.dumps(res, indent=1))
    print("imputed", cohort, len(res), flush=True)


# ================================================================ cells
def task(args):
    n, cohort, k = args
    K.umask()
    t0 = time.time()
    i = K.ALL.index(n)
    T = GR.load(n)
    rows = rows_of(T, n, cohort)
    TT = T
    ofile = K.FLG / f"restricted_outcome_{n}.parquet"
    if cohort == "v2" and ofile.exists():  # = grid.task
        O = pd.read_parquet(ofile).set_index("patient_key")
        assert O.index.equals(T.keys), n
        TT = copy.copy(T)
        TT.y_t, TT.y_e = O.y_t.to_numpy(float), O.y_e.to_numpy(int)
    t = T.t[rows]
    nl_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys if c != "lvef"}
    cols_nl = [c for c in T.cov.columns if c != "lvef"]
    Z = pd.read_parquet(imp_path(cohort, n))
    Z = Z[Z.draw == k].set_index("patient_key")
    # row-indexed copy, as version 1 (Xre[r]): pandas returns a Fortran-ordered block, and the base-arm PS fit (no hstack
    # partner) is layout-sensitive (gbm ties, lbfgs round-off); found by the gate
    Xre = Z.loc[T.keys[rows], cols_nl].astype(float).to_numpy()[np.arange(len(rows))]
    assert np.array_equal(Z.loc[T.keys[rows], "treated"].to_numpy(int), t.astype(int)), n
    # observed values unchanged; medication / utilisation columns identical to the version 1 completed covariates
    obs = pd.read_parquet(K.A / f"claude-{n}-baseline-v11" / "restricted_baseline_observed.parquet").set_index("patient_key")
    ok = ~np.isnan(obs.loc[T.keys[rows], cols_nl].to_numpy(float))
    assert np.array_equal(Xre[ok], T.cov[cols_nl].to_numpy(float)[rows][ok]), n
    ecg = pcs(GR.subset(T.ecg_raw, rows), 64)[:, :32]
    clm = pcs(GR.subset(GR.clm_raw(T), rows), 64)
    assert clm.shape == (len(rows), 64) and np.isfinite(clm).all() and np.isfinite(ecg).all()
    perm = np.random.default_rng(424242).permutation(len(rows))
    blk = {"ecg": ecg, "she": ecg[perm], "clm": clm, "shc": clm[perm], "c32": clm[:, :32]}
    comp = {"base": [], "ECG": ["ecg"], "CLMBR": ["clm"], "ECG+CLMBR": ["clm", "ecg"], "shufECG": ["she"],
            "shufCLMBR": ["shc"], "CLMBR32": ["c32"]}
    out = []

    def rec(cfg, arm, X):  # = grid.task.rec
        est, psm = K.CONFIGS[cfg]
        try:
            o, fail = E.run_cell(TT, X, rows=rows, estimator=est, ps_model=psm, cstat=None), ""
        except IndexError as e:
            from v13_common import match, ps_logit
            lg = ps_logit(np.asarray(X, float), t, model=psm[0], C=psm[1] if psm[1] is not None else 1.0)
            if est[0] != "match" or len(match(lg, t, cal=est[1], ratio=est[2])[0]) > 0:
                raise
            o = dict(n=len(t), n_t=int(t.sum()), n_c=int((1 - t).sum()), n_pairs=0, loghr=np.nan, se=np.nan, ess_t=0.0, ess_c=0.0,
                     **{f"smd:{c}": np.nan for c in VN})
            fail = f"no matched pairs ({type(e).__name__})"
        small = min(o["n_t"], o["n_c"])
        out.append(dict(trial=n, key=K.KEY[n], idx=i, rung=RUNG, draw=k, cohort=cohort, config=cfg, arm=arm, k_pcs=K.KPC[arm],
                        rb=T.rb, rs=T.rs, ex58=";".join(sorted(nl_ex)), p_ps=X.shape[1], cell_failed=fail,
                        **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c")},
                        retain=(o["n_pairs"] / small) if est[0] == "match" else np.nan,
                        **{f"smd:{c}": o[f"smd:{c}"] for c in VN}))

    for cfg in K.CONFIGS:
        for a in ARMS:
            rec(cfg, a, np.hstack([Xre] + [blk[b] for b in comp[a]]))
    rec("main", "CLMBR32", np.hstack([Xre, blk["c32"]]))
    print(f"{cohort} {n} draw {k} rows {len(rows)}/{len(T.t)} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, cohort=cohort, draw=k, secs=round(time.time() - t0, 1), rows_frac=round(len(rows) / len(T.t), 4),
                     outcome_redefined=TT is not T)


def run(cohort, workers):
    from multiprocessing import get_context
    K.umask()
    CEL.mkdir(parents=True, exist_ok=True)
    draws = [1] if cohort == "v1" else list(range(1, M + 1))
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle",
           "rewind", "cabana-v2", "transform-hf", "precision")
    tk = sorted(K.ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    jobs = [(n, cohort, k) for n in tk for k in draws]
    with get_context("fork").Pool(min(workers, len(jobs))) as p:
        res = p.map(task, jobs, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    R.to_parquet(CEL / f"restricted_cells_{cohort}.parquet")
    (CEL / f"log_{cohort}.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    (CEL / f"run_{cohort}.done").write_text(time.strftime("%Y-%m-%d %H:%M") + "\n")
    print("done", cohort, len(R), flush=True)


def gate():
    """v1 cohort, draw 1 vs audits/claude-v1-psclin-nolvef/cells (rung clinical_nolvef): every arm x config x trial,
    every stored column; exact."""
    K.umask()
    R = pd.read_parquet(CEL / "restricted_cells_v1.parquet")
    Q = pd.read_parquet(K.REF_PSCLIN)
    Q = Q[Q.rung == RUNG]
    rows = []
    for (cfg, a), y in Q.groupby(["config", "arm"]):
        x = R[(R.config == cfg) & (R.arm == a) & (R.draw == 1)].set_index("trial").sort_index()
        y = y.set_index("trial").sort_index()
        assert x.index.equals(y.index), (cfg, a)
        for c in NUMC:
            xa, ya = x[c].to_numpy(float), y[c].to_numpy(float)
            dd = np.abs(xa - ya)
            rows.append(dict(config=cfg, arm=a, col=c, n_trials=len(x), maxdev=float(np.nanmax(dd)) if np.isfinite(dd).any() else 0.0,
                             nan_mismatch=int((np.isnan(xa) ^ np.isnan(ya)).sum())))
        for c in TXT:
            rows.append(dict(config=cfg, arm=a, col=c, n_trials=len(x),
                             maxdev=float((x[c].fillna("").astype(str) != y[c].fillna("").astype(str)).sum()), nan_mismatch=0))
    G = pd.DataFrame(rows)
    G.to_csv(CEL / "gate.csv", index=False)
    ncell = int(G[G.col == "loghr"].n_trials.sum())
    st = dict(passed=bool(G.maxdev.max() == 0 and G.nan_mismatch.sum() == 0 and ncell == len(Q) and (G.n_trials == 38).all()),
              maxdev=float(G.maxdev.max()), nan_mismatch=int(G.nan_mismatch.sum()), cells_compared=ncell, reference_cells=len(Q),
              values_compared=int(G[G.col.isin(NUMC)].n_trials.sum()), configs=sorted(set(G.config)), arms=sorted(set(G.arm)),
              reference=str(K.REF_PSCLIN), time=time.strftime("%Y-%m-%d %H:%M"))
    (CEL / "gate_status.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    return st


# ================================================================ combination
def combine():
    K.umask()
    R = pd.read_parquet(CEL / "restricted_cells_v2.parquet")
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
    C.to_parquet(CEL / "restricted_cells_v2_mi.parquet")
    P2.suppress(C).to_csv(CEL / "cells_v2_mi.csv", index=False)
    print("combined", len(C), "failed", int(C.cell_failed.astype(str).ne("").sum()), flush=True)


# ================================================================ summaries
LABEL = dict(V2S.LABEL)
LABEL[MI] = "PS-Clinical (no LVEF, 5-draw MI)"
MASK_RUNG = dict(V2S.MASK_RUNG)
MASK_RUNG[MI] = MASK_RUNG[RUNG]
for _k in range(1, M + 1):
    MASK_RUNG[f"{RUNG}#{_k}"] = MASK_RUNG[RUNG]
    LABEL[f"{RUNG}#{_k}"] = f"PS-Clinical (no LVEF, draw {_k})"
LADDER = ["P1", "P5", "PS10", "hdPS200", MI]


def load_sets():
    S = dict(K.SETS)
    f = K.ROOT / "docs/emulation_quality_v2/quality_v2_cohorts.json"
    if f.exists():
        q = json.loads(f.read_text())
        S["Snew"] = [n for n in K.ALL if n in {K.LABEL_NAME[x] for x in q["analysed_set"]}]
        S["SEG"] = [n for n in K.ALL if n in {K.LABEL_NAME[x] for x in q["excellent_good"]}]
    return S


def all_cells():
    """spec-v2 cells of the other rungs (claude-v2-cohorts, variant v2, all 38 trials) + MI rung + each draw as a rung."""
    G = pd.read_parquet(K.CEL / "restricted_cells_v2_all.parquet")
    G = G[G.rung.isin(["P1", "P5", "PS10", "Flags", "hdPS200", "clinical", RUNG])]
    G = G.assign(rung=G.rung.replace({RUNG: f"{RUNG}_v2single"}))
    C = pd.read_parquet(CEL / "restricted_cells_v2_mi.parquet")
    D = pd.read_parquet(CEL / "restricted_cells_v2.parquet")
    D = D.assign(rung=RUNG + "#" + D.draw.astype(str))
    cols = list(G.columns.intersection(C.columns))
    return pd.concat([G[cols], C[cols], D[cols]], ignore_index=True)


def load_F(R):
    F, SM, RET, NF = {}, {}, {}, []
    for (rg, cfg, a), g in R.groupby(["rung", "config", "arm"]):
        g = g.set_index("trial", drop=False).loc[[t for t in K.ALL if t in set(g.trial)]]
        Fk, Sk = SP.per_trial(g)
        f = V2S.failed(g).to_numpy()
        if f.any():
            Sk.loc[f, :] = np.nan
            Fk.loc[f, ["lt01", "m58", "absd", "cons", "ea", "loghr", "se"]] = np.nan
            NF += [(rg, cfg, a, t) for t in g.trial[f]]
        base = rg.replace("_v2single", "")
        m = set(MASK_RUNG[base]) | set(V2S.MASK_ARM.get(a, []))
        Sk.loc[:, [c for c in Sk.columns if c in m]] = np.nan
        F[(rg, cfg, a)], SM[(rg, cfg, a)] = Fk, Sk
        RET[(rg, cfg, a)] = g.retain.mask(P2.small_pairs(g))
    return F, SM, RET, NF


def contrasts():
    L = []
    for cfg in K.CONFIGS:
        for a, b, side in PSC.WITHIN:
            L.append((cfg, f"{MI}: {a} vs {b}", "within", MI, a, MI, b, side))
        for rg in ("P1", "P5", "PS10", "hdPS200"):
            for a, side in (("ECG", "one"), ("shufECG", "two")):
                L.append((cfg, f"{rg}: {a} vs base", "ladder", rg, a, rg, "base", side))
            L.append((cfg, f"{rg}: ECG vs shufECG", "ladder", rg, "ECG", rg, "shufECG", "one"))
        L.append((cfg, f"{MI} base vs P5 base", "base2base", MI, "base", "P5", "base", "two"))
        L.append((cfg, f"{MI} base vs hdPS200 base", "base2base", MI, "base", "hdPS200", "base", "two"))
        L.append((cfg, f"P5+ECG vs {MI} base", "across", "P5", "ECG", MI, "base", "two"))
    for k in range(1, M + 1):  # draw-to-draw range of the main contrast (and its placebo contrast)
        for a, b, side in (("ECG", "base", "one"), ("ECG", "shufECG", "one"), ("shufECG", "base", "two")):
            L.append(("main", f"{RUNG}#{k}: {a} vs {b}", "draw", f"{RUNG}#{k}", a, f"{RUNG}#{k}", b, side))
    for a, b, side in (("ECG", "base", "one"), ("ECG", "shufECG", "one")):
        L.append(("main", f"{RUNG}_v2single: {a} vs {b}", "single", f"{RUNG}_v2single", a, f"{RUNG}_v2single", b, side))
    for a, side in (("CLMBR32", "one"),):
        L.append(("main", f"{MI}: {a} vs base", "clmbr32", MI, a, MI, "base", side))
    return L


def _row(args):
    sname, c = args
    row, dom = V2S._row(("v2", sname, c))
    return row, dom


def ladder_levels(SM, sets):
    rows = []
    for sname, tr in sets.items():
        for (rg, cfg, a), S in SM.items():
            if rg not in LADDER or a not in ("base", "ECG", "shufECG"):
                continue
            for pn, cols in (("54", NONCODED), ("58", VN), ("echo35", PSC.ECHO)):
                X = S.loc[tr, cols]
                m = X.mean(1)
                rows.append(dict(set=sname, rung=rg, label=LABEL[rg], config=cfg, arm=a, panel=pn, k_trials=int(m.notna().sum()),
                                 mean_smd=float(m.mean()), pct_lt01=float((100 * (X < 0.1).sum(1) / X.notna().sum(1)).mean())))
    return rows


def rubin_diag(R):
    """fraction of the total variance due to between-draw variance (aggregates over trials), per config x arm."""
    C = pd.read_parquet(CEL / "restricted_cells_v2_mi.parquet")
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
    sets = load_sets()
    R = all_cells()
    F, SM, RET, NF = load_F(R)
    P2._G.update(F=F, SM=SM, CL=K.V.cluster_of(), RET=RET, SETS=sets)
    jobs = [(s, c) for s in sets for c in contrasts()]
    with get_context("fork").Pool(min(workers, len(jobs))) as p:
        res = p.map(_row, jobs, chunksize=2)
    S = pd.DataFrame([r for r, _ in res])
    D = pd.DataFrame([d for _, ds in res for d in ds])
    for sname in sets:  # BH-FDR within set over the MI rung's within contrasts x configs (balance family)
        ms = (S.set == sname) & S.kind.eq("within")
        long = S.loc[ms, P2.BAL_FAM].stack(dropna=True)
        q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
        for c in P2.BAL_FAM:
            S.loc[ms, f"q_{c}_fam"] = q[c] if c in q else np.nan
    S.to_csv(SUM / "contrasts.csv", index=False)
    D.to_csv(SUM / "domains.csv", index=False)
    pd.DataFrame(ladder_levels(SM, sets)).to_csv(SUM / "ladder.csv", index=False)
    rubin_diag(R).to_csv(SUM / "rubin_diagnostics.csv", index=False)
    NFd = pd.DataFrame([dict(rung=a, config=b, arm=c, trial=d) for a, b, c, d in NF])
    (NFd.groupby(["rung", "config", "arm"]).size().rename("n_trials_failed").reset_index() if len(NFd) else
     pd.DataFrame(columns=["rung", "config", "arm", "n_trials_failed"])).to_csv(SUM / "failed_cells.csv", index=False)
    # per-trial aggregates (main config, 54 items; no counts) for the explorer and the quality impact table
    pt = []
    for rg in LADDER:
        for a in ("base", "ECG", "shufECG"):
            k = (rg, "main", a)
            for t in K.ALL:
                pt.append(dict(trial=t, key=K.KEY[t], rung=rg, arm=a, m54=float(SM[k][NONCODED].loc[t].mean()),
                               absd=F[k].loc[t, "absd"], loghr=F[k].loc[t, "loghr"], se=F[k].loc[t, "se"], rb=F[k].loc[t, "rb"]))
    pd.DataFrame(pt).to_csv(SUM / "per_trial.csv", index=False)
    print("summaries written", sorted(sets), flush=True)


def privacy():
    """every csv / json under OUT that is not restricted_*: no count 1-10 in count columns; suppressed rows blank derived."""
    K.umask()
    bad = []
    for f in sorted(OUT.rglob("*.csv")):
        if f.name.startswith("restricted_"):
            continue
        D = pd.read_csv(f, low_memory=False)
        for c in ("n", "n_t", "n_c", "n_pairs"):
            if c in D:
                v = pd.to_numeric(D[c], errors="coerce")
                k = int(((v >= 1) & (v < K.MIN_CELL)).sum())
                if k:
                    bad.append((str(f.relative_to(OUT)), c, k))
        if "suppressed_lt11" in D:
            sup = D.suppressed_lt11.fillna(False).astype(bool)
            for c in P2.DERIVED:
                if c in D and D.loc[sup, c].notna().any():
                    bad.append((str(f.relative_to(OUT)), c, int(D.loc[sup, c].notna().sum())))
        if "patient_key" in D or "person_id" in D:
            bad.append((str(f.relative_to(OUT)), "identifier column", 1))
    for f in sorted(OUT.rglob("*.json")):
        s = f.read_text()
        if "patient_key\":" in s or "person_id" in s:
            bad.append((str(f.relative_to(OUT)), "identifier key", 1))
    out = dict(clean=not bad, issues=bad, time=time.strftime("%Y-%m-%d %H:%M"))
    (OUT / "privacy_scan.json").write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["impute", "run", "gate", "combine", "summarize", "privacy"])
    ap.add_argument("--cohort", default="v2", choices=["v1", "v2"])
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    w = min(a.workers, 32)
    {"impute": lambda: impute_all(a.cohort, w), "run": lambda: run(a.cohort, w), "gate": gate, "combine": combine,
     "summarize": lambda: summarize(w), "privacy": privacy}[a.cmd]()
