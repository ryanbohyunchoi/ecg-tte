#!/usr/bin/env python
"""COMET index-date cut sensitivity (docs/v1_comet_cut/COMET_INDEX_CUT.md).

COMET's version 1 cohort comes from the JDAT roster (claude-comet-progref-v1/roster), not from a trial_specs builder, so the
project-wide index-date cut (index_end = 2024-06-30 in every trial_specs cohort) was never applied to it. This script applies
the cut to COMET as a ROW SUBSET of the version 1 analysed cohort (T.keys; index date = T.index_date, from the roster) and
re-runs every COMET cell of the primary ladder; the other 37 trials keep their version 1 cells.

Version 1 code is imported unchanged: scripts/v2_cohorts/grid.py (load, subset, clm_raw; the cell recorder mirrors
grid.task.rec), scripts/v1_ps10/ps10.py (design, ex58_ps10), scripts/v18 designs (C.designs, P5DX),
scripts/v2_psclin_mi/psclin_mi.py (load_F, masks, MI combination rule), scripts/v21/paper2_grid.py (_row, endpoints).

Rungs (each built on the full version 1 cohort exactly as in version 1, then row-subset, as grid.task):
  P1, P5 (PRIMARY PS-CVD5), PS10 (CVD10), hdPS200 (T.hd(200, t[rows], rows): levels re-ranked within the rows),
  clinical (version 1 PS-Clinical with LVEF; gate only), clinical_nolvef 5-draw MI (draws = the existing version 1 imputed
  tables audits/claude-v1-psclin-mi/imputation/restricted_completed_nolvef_v1_comet.parquet, restricted to the kept rows;
  no re-imputation; combined as psclin_mi_v1.combine: |SMD| averaged over draws, log HR by Rubin's rules).
Arms: base, ECG, CLMBR, ECG+CLMBR, shufECG, shufCLMBR x 6 configs, + CLMBR32 (main) for P1, P5, clinical, clinical_nolvef.
Variants (rows, PCs):
  gate_v1pc      all rows, version 1 PCs (T.ecg_pc, T.clm_pc), placebo rng(424242).permutation(n) = T.shuffle_perm
  gate_within    all rows, PCs refit within the rows (= version 1 PCs when rows = all)
  cut_v1pc       index_date <= 2024-06-30, version 1 PCs restricted to the rows           (PRIMARY sensitivity)
  cut_within     index_date <= 2024-06-30, ECG 32 / CLMBR-T 64 PCs refit within the cut cohort
  Placebos: the arm's PCs permuted within the rows, rng(424242).permutation(len(rows)).

Usage (python = /mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python):
  comet_cut.py share                      -> OUT/share.json (aggregate shares; counts 1-10 suppressed)
  comet_cut.py run [--workers 16]         -> OUT/cells/restricted_cells_<variant>.parquet (+ _draws), log.json
  comet_cut.py gate                       -> OUT/cells/gate.csv, gate_status.json (gate variants vs version 1, exact)
  comet_cut.py summarize [--workers 16]   -> OUT/summary/contrasts.csv, per_trial_comet.csv, ladder.csv
  comet_cut.py privacy                    -> OUT/privacy_scan.json
OUT = /mnt/raid0/rbc58/ecg-tte/audits/claude-v1-comet-cut (umask 077). Aggregates only outside restricted_* files.
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
import psclin_mi as PM  # noqa: E402  (imports v2common: thread env vars, sys.path for the version 1 modules)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

K, E, P2, SP, GR, PSC, V2S = PM.K, PM.E, PM.P2, PM.SP, PM.GR, PM.PSC, PM.V2S
import ps10 as P10  # noqa: E402
from eval_longtail_balance import pcs  # noqa: E402

C = K.C
VN, NONCODED = K.VN, K.NONCODED
N = "comet"
CUT = pd.Timestamp("2024-06-30")
DEATH_END_PROXY = pd.Timestamp("2024-12-31")
OUT = K.A / "claude-v1-comet-cut"
CEL, SUM, LOGD = OUT / "cells", OUT / "summary", OUT / "logs"
IMP_V1 = K.A / "claude-v1-psclin-mi" / "imputation" / f"restricted_completed_nolvef_v1_{N}.parquet"
REF_MI = K.A / "claude-v1-psclin-mi" / "cells" / "restricted_cells_v1_mi_v1layout.parquet"
REF_DRAWS = K.A / "claude-v1-psclin-mi" / "cells" / "restricted_cells_v1.parquet"
M, RUNG, MI = PM.M, PM.RUNG, PM.MI
VARIANTS = {"gate_v1pc": ("all", "v1"), "gate_within": ("all", "within"), "cut_v1pc": ("cut", "v1"), "cut_within": ("cut", "within")}
PS_RUNGS = ["P1", "P5", "PS10", "hdPS200", "clinical"]
C32 = {"P1", "P5", "clinical"}
COMP = {"base": [], "ECG": ["ecg"], "CLMBR": ["clm"], "ECG+CLMBR": ["clm", "ecg"], "shufECG": ["she"], "shufCLMBR": ["shc"],
        "CLMBR32": ["c32"]}
NUMC, TXT = GR.NUMC, GR.TXT
_S: dict = {}  # parent-prepared state, inherited by forked workers


def rows_of(T, mode):
    return np.arange(len(T.t)) if mode == "all" else np.where(T.index_date.le(CUT).to_numpy())[0]


# ================================================================ share removed
def share():
    K.umask()
    OUT.mkdir(parents=True, exist_ok=True)
    T = GR.load(N)
    d = T.index_date
    assert d.notna().all()
    n = len(d)
    out = dict(analysed_cohort=dict(n=K.sup(n)))
    for lab, c in (("after_2024_06_30", CUT), ("after_2024_12_31", DEATH_END_PROXY)):
        m = d.gt(c).to_numpy()
        out["analysed_cohort"][lab] = dict(n=K.sup(m.sum()), pct=K.pct(m.sum(), n, 2),
                                           n_treated=K.sup(m[T.t == 1].sum()), n_comparator=K.sup(m[T.t == 0].sum()))
    # roster (pre-intersection), for reference
    ro = pd.read_parquet(K.A / K.E.PRIMARY[N][1] / "restricted_cohort.parquet")
    rd = pd.to_datetime(ro.index_date)
    nr = len(rd)
    out["roster"] = dict(n=K.sup(nr), index_date_missing=K.sup(rd.isna().sum()))
    for lab, c in (("after_2024_06_30", CUT), ("after_2024_12_31", DEATH_END_PROXY)):
        k = int(rd.gt(c).sum())
        out["roster"][lab] = dict(n=K.sup(k), pct=K.pct(k, nr, 2))
    out["index_year_range_analysed"] = [int(d.min().year), int(d.max().year)]
    out["cut"] = str(CUT.date())
    (OUT / "share.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


# ================================================================ cells
def prep(variant):
    """designs and representation blocks for one variant (computed in the parent)."""
    T = _S["T"]
    mode, pcmode = VARIANTS[variant]
    rows = rows_of(T, mode)
    t = T.t[rows]
    b5, _, _ = C.designs(T, N, C.P5DX)
    X10, _, _, _ = P10.design(T, N)
    X1 = T.cov.iloc[rows][T.demo].to_numpy(float)
    Hk = T.hd(200, t=t, rows=rows)
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    rung = {"P1": (X1, set()), "P5": (b5[rows], set()), "PS10": (X10[rows], P10.ex58_ps10()),
            "hdPS200": (np.hstack([T.X_dx[rows], Hk]), set()), "clinical": (T.X_core[rows], clin_ex)}
    # clinical_nolvef MI: existing version 1 draws (full-roster imputation), restricted to the kept rows (= psclin_mi.task)
    nl_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys if c != "lvef"}
    cols_nl = [c for c in T.cov.columns if c != "lvef"]
    Zall = pd.read_parquet(IMP_V1)
    obs = pd.read_parquet(K.A / f"claude-{N}-baseline-v11" / "restricted_baseline_observed.parquet").set_index("patient_key")
    ok = ~np.isnan(obs.loc[T.keys[rows], cols_nl].to_numpy(float))
    for k in range(1, M + 1):
        Z = Zall[Zall.draw == k].set_index("patient_key")
        Xre = Z.loc[T.keys[rows], cols_nl].astype(float).to_numpy()[np.arange(len(rows))]
        assert np.array_equal(Z.loc[T.keys[rows], "treated"].to_numpy(int), t.astype(int))
        assert np.array_equal(Xre[ok], T.cov[cols_nl].to_numpy(float)[rows][ok])
        rung[f"{RUNG}#{k}"] = (Xre, nl_ex)
    if pcmode == "within":
        ecg = pcs(GR.subset(T.ecg_raw, rows), 64)[:, :32]
        clm = pcs(GR.subset(_S["clm_raw"], rows), 64)
    else:
        ecg, clm = T.ecg_pc[rows], T.clm_pc[rows]
    assert clm.shape == (len(rows), 64) and np.isfinite(clm).all() and np.isfinite(ecg).all()
    perm = np.random.default_rng(424242).permutation(len(rows))
    if mode == "all":
        assert np.array_equal(perm, T.shuffle_perm)
    blk = {"ecg": ecg, "she": ecg[perm], "clm": clm, "shc": clm[perm], "c32": clm[:, :32]}
    from eval_longtail_balance import hdps_rank  # hdPS levels selected within the rows vs on the full cohort (aggregate)
    top_rows = set(hdps_rank(T.lv.iloc[rows].reset_index(drop=True), t)[:200])
    top_full = set(hdps_rank(T.lv.reset_index(drop=True), T.t)[:200])
    info = dict(variant=variant, rows=len(rows), rows_frac=round(len(rows) / len(T.t), 4), pcmode=pcmode,
                hdps_top200_overlap_with_full=len(top_rows & top_full))
    return dict(rows=rows, t=t, rung=rung, blk=blk, info=info)


def _task(args):
    variant, rg, cfg = args
    K.umask()
    T = _S["T"]
    st = _S[variant]
    rows, t, blk = st["rows"], st["t"], st["blk"]
    X0, ex58 = st["rung"][rg]
    i = K.ALL.index(N)
    draw = int(rg.split("#")[1]) if "#" in rg else 0
    rname = RUNG if draw else rg
    out = []

    def rec(arm, X):  # = grid.task.rec / psclin_mi.task.rec
        est, psm = K.CONFIGS[cfg]
        try:
            o, fail = E.run_cell(T, X, rows=rows, estimator=est, ps_model=psm, cstat=None), ""
        except IndexError as e:
            from v13_common import match, ps_logit
            lg = ps_logit(np.asarray(X, float), t, model=psm[0], C=psm[1] if psm[1] is not None else 1.0)
            if est[0] != "match" or len(match(lg, t, cal=est[1], ratio=est[2])[0]) > 0:
                raise
            o = dict(n=len(t), n_t=int(t.sum()), n_c=int((1 - t).sum()), n_pairs=0, loghr=np.nan, se=np.nan, ess_t=0.0, ess_c=0.0,
                     **{f"smd:{c}": np.nan for c in VN})
            fail = f"no matched pairs ({type(e).__name__})"
        small = min(o["n_t"], o["n_c"])
        r = dict(trial=N, key=K.KEY[N], idx=i, rung=rname, config=cfg, arm=arm, k_pcs=K.KPC[arm], rb=T.rb, rs=T.rs,
                 ex58=";".join(sorted(ex58)), p_ps=X.shape[1], cell_failed=fail,
                 **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c")},
                 retain=(o["n_pairs"] / small) if est[0] == "match" else np.nan,
                 **{f"smd:{c}": o[f"smd:{c}"] for c in VN})
        if draw:
            r["draw"] = draw
        out.append(r)

    for a in K.ARMS:
        rec(a, np.hstack([X0] + [blk[b] for b in COMP[a]]))
    if cfg == "main" and (rg in C32 or draw):
        rec("CLMBR32", np.hstack([X0, blk["c32"]]))
    return variant, out


def combine(D):
    """= psclin_mi_v1.combine (MI rule) + layout of the version 1 psclin cells (rung clinical_nolvef)."""
    D = D.assign(failed=V2S.failed(D))
    smd = [f"smd:{c}" for c in VN]
    out = []
    for (n, cfg, a), g in D.groupby(["trial", "config", "arm"], sort=False):
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
                     retain=float(g.retain.mean()), cell_failed="", **{c: float(g[c].abs().mean()) for c in smd})
        r.pop("failed")
        out.append(r)
    Cc = pd.DataFrame(out)
    Q = pd.read_parquet(REF_MI)
    Q = Q[Q.trial == N]
    L = Cc.assign(rung=RUNG)[list(Q.columns)]
    for c in Q.columns:
        if L[c].dtype != Q[c].dtype:
            L[c] = L[c].astype(Q[c].dtype)
    L = L.set_index(["trial", "config", "arm"]).loc[pd.MultiIndex.from_frame(Q[["trial", "config", "arm"]])].reset_index()[list(Q.columns)]
    assert len(L) == len(Q) == 37
    return L


def run(workers):
    from multiprocessing import get_context
    K.umask()
    for d in (CEL, LOGD):
        d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    T = GR.load(N)
    _S["T"] = T
    _S["clm_raw"] = GR.clm_raw(T)
    _ = T.clm_pc  # version 1 CLMBR-T PCs (lazy), computed once in the parent
    info = []
    for v in VARIANTS:
        _S[v] = prep(v)
        info.append(_S[v]["info"])
        print("prepared", v, _S[v]["info"], flush=True)
    rgs = PS_RUNGS + [f"{RUNG}#{k}" for k in range(1, M + 1)]
    jobs = [(v, rg, cfg) for v in VARIANTS for rg in rgs for cfg in K.CONFIGS]
    jobs.sort(key=lambda x: x[2] != "gbm")  # slow configuration first
    with get_context("fork").Pool(min(workers, 16, len(jobs))) as p:
        res = p.map(_task, jobs, chunksize=1)
    for v in VARIANTS:
        R = pd.DataFrame([r for vv, o in res if vv == v for r in o])
        D = R[R.rung == RUNG].copy()
        P = R[R.rung != RUNG].drop(columns=["draw"], errors="ignore")
        D.to_parquet(CEL / f"restricted_cells_{v}_draws.parquet")
        L = combine(D)
        Z = pd.concat([P, L], ignore_index=True)
        Z.to_parquet(CEL / f"restricted_cells_{v}.parquet")
        print(v, "cells", len(P), "+ MI", len(L), "draw cells", len(D), flush=True)
    (CEL / "log.json").write_text(json.dumps(dict(variants=info, secs=round(time.time() - t0, 1), workers=min(workers, 16),
                                                  time=time.strftime("%Y-%m-%d %H:%M")), indent=1))


# ================================================================ gate
def reference():
    """version 1 COMET cells of the ladder rungs + clinical (with LVEF): grid.reference() and the MI cells (v1 layout)."""
    G = GR.reference()
    G = G[G.rung.isin(PS_RUNGS) & (G.trial == N)]
    Q = pd.read_parquet(REF_MI)
    Q = Q[Q.trial == N]
    return pd.concat([G, Q], ignore_index=True)


def _cmp(x, y, tag):
    rows = []
    kk = ["rung", "config", "arm"] + (["draw"] if "draw" in y else [])
    x, y = x.set_index(kk).sort_index(), y.set_index(kk).sort_index()
    ix = y.index.intersection(x.index)
    for c in NUMC:
        xa, ya = x.loc[ix, c].to_numpy(float), y.loc[ix, c].to_numpy(float)
        dd = np.abs(xa - ya)
        rows.append(dict(compare=tag, col=c, n_cells=len(ix), n_ref=len(y),
                         maxdev=float(np.nanmax(dd)) if np.isfinite(dd).any() else 0.0,
                         nan_mismatch=int((np.isnan(xa) ^ np.isnan(ya)).sum())))
    for c in TXT:
        rows.append(dict(compare=tag, col=c, n_cells=len(ix), n_ref=len(y),
                         maxdev=float((x.loc[ix, c].fillna("").astype(str) != y.loc[ix, c].fillna("").astype(str)).sum()),
                         nan_mismatch=0))
    return rows


def gate():
    K.umask()
    ref = reference()
    D1 = pd.read_parquet(REF_DRAWS)
    D1 = D1[(D1.trial == N)]
    rows = []
    for v in ("gate_v1pc", "gate_within"):
        X = pd.read_parquet(CEL / f"restricted_cells_{v}.parquet")
        rows += _cmp(X, ref, f"{v} vs version 1 cells (P1/P5/PS10/hdPS200/clinical + clinical_nolvef MI)")
        Xd = pd.read_parquet(CEL / f"restricted_cells_{v}_draws.parquet")
        rows += _cmp(Xd, D1[list(Xd.columns.intersection(D1.columns))], f"{v} draws vs claude-v1-psclin-mi per-draw cells")
    G = pd.DataFrame(rows)
    G.to_csv(CEL / "gate.csv", index=False)
    by = G[G.col == "loghr"].groupby("compare")[["n_cells", "n_ref"]].first().to_dict("index")
    st = dict(passed=bool(G.maxdev.max() == 0 and G.nan_mismatch.sum() == 0 and (G.n_cells == G.n_ref).all()),
              maxdev=float(G.maxdev.max()), nan_mismatch=int(G.nan_mismatch.sum()), cells=by,
              values_compared=int(G[G.col.isin(NUMC)].n_cells.sum()), reference_rungs=sorted(set(ref.rung)),
              time=time.strftime("%Y-%m-%d %H:%M"))
    (CEL / "gate_status.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    return st


# ================================================================ summaries
LADDER = PM.LADDER  # P1, P5, PS10, hdPS200, clinical_nolvef_mi
LABEL = {"P1": "PS-Demo", "P5": "PS-CVD5", "PS10": "PS-CVD10", "hdPS200": "hdPS", MI: "PS-Clinical (no LVEF), MI"}
COHORTS = ["v1", "gate_v1pc", "cut_v1pc", "cut_within"]


def cells(cohort):
    """38-trial table of the ladder rungs: version 1 cells, COMET replaced by the variant's cells (v1 = unchanged)."""
    G = GR.reference()
    G = G[G.rung.isin(["P1", "P5", "PS10", "hdPS200"])]
    Q = pd.read_parquet(REF_MI)
    R = pd.concat([G, Q], ignore_index=True)
    if cohort != "v1":
        X = pd.read_parquet(CEL / f"restricted_cells_{cohort}.parquet")
        X = X[X.rung.isin(["P1", "P5", "PS10", "hdPS200", RUNG])][list(R.columns)]
        assert len(X) == int((R.trial == N).sum())
        R = pd.concat([R[R.trial != N], X], ignore_index=True)
    R = R.assign(rung=R.rung.replace({RUNG: MI}))
    R = R[R.arm.isin(["base", "ECG", "shufECG"])]
    return R


def contrasts():
    L = []
    for cfg in K.CONFIGS:
        for rg in LADDER:
            L.append((cfg, f"{rg}: ECG vs base", "ladder", rg, "ECG", rg, "base", "one"))
            L.append((cfg, f"{rg}: shufECG vs base", "ladder", rg, "shufECG", rg, "base", "two"))
            L.append((cfg, f"{rg}: ECG vs shufECG", "ladder", rg, "ECG", rg, "shufECG", "one"))
    return L


def _row(args):
    cohort, sname, c = args
    row, _ = P2._row((sname, c))
    row["cohort"] = cohort
    return row


def summarize(workers):
    from multiprocessing import get_context
    K.umask()
    st = json.loads((CEL / "gate_status.json").read_text())
    if not st["passed"]:
        raise SystemExit("gate failed; not summarising")
    SUM.mkdir(parents=True, exist_ok=True)
    sets = {"S32": K.S32, "S38": K.S38}
    S_all, PT, LV = [], [], []
    for cohort in COHORTS:
        t0 = time.time()
        R = cells(cohort)
        F, SM, RET, NF = PM.load_F(R)
        assert not [x for x in NF if x[3] == N], "a COMET cell failed"
        P2._G.update(F=F, SM=SM, CL=K.V.cluster_of(), RET=RET, SETS=sets)
        jobs = [(cohort, s, c) for s in sets for c in contrasts()]
        with get_context("fork").Pool(min(workers, 16, len(jobs))) as p:
            S_all += p.map(_row, jobs, chunksize=2)
        for rg in LADDER:
            for cfg in K.CONFIGS:
                for a in ("base", "ECG", "shufECG"):
                    k = (rg, cfg, a)
                    PT.append(dict(cohort=cohort, trial=N, rung=rg, label=LABEL[rg], config=cfg, arm=a,
                                   m54=float(SM[k][NONCODED].loc[N].mean()), items54=int(SM[k][NONCODED].loc[N].notna().sum()),
                                   loghr=F[k].loc[N, "loghr"], se=F[k].loc[N, "se"], rb=F[k].loc[N, "rb"],
                                   absd=F[k].loc[N, "absd"]))
                    for sname, tr in sets.items():
                        X = SM[k].loc[tr, NONCODED]
                        LV.append(dict(cohort=cohort, set=sname, rung=rg, label=LABEL[rg], config=cfg, arm=a,
                                       k_trials=int(X.mean(1).notna().sum()), mean_smd54=float(X.mean(1).mean()),
                                       mean_absd=float(F[k].loc[tr, "absd"].mean())))
        print(cohort, f"{time.time() - t0:.0f}s", flush=True)
    S = pd.DataFrame(S_all)
    S.to_csv(SUM / "contrasts.csv", index=False)
    pd.DataFrame(PT).to_csv(SUM / "per_trial_comet.csv", index=False)
    pd.DataFrame(LV).to_csv(SUM / "ladder.csv", index=False)
    # check: the no-cut summary equals the existing version 1 MI summary (deck numbers) to the last digit
    ref = pd.read_csv(K.A / "claude-v1-psclin-mi" / "summary" / "contrasts.csv")
    chk = []
    for c in contrasts():
        lab = c[1]
        a = S[(S.cohort == "v1") & (S.set == "S32") & (S.config == c[0]) & (S.contrast == lab)]
        b = ref[(ref.set == "S32") & (ref.config == c[0]) & (ref.contrast == lab)]
        if len(a) == 1 and len(b) == 1:
            for col in ("m54_a", "m54_b", "relred54", "relred54_lo", "relred54_hi", "m54_p", "absd_a", "absd_b", "absd_p", "bshuf_p"):
                chk.append(dict(config=c[0], contrast=lab, col=col, dev=abs(float(a[col].iloc[0]) - float(b[col].iloc[0]))))
    Ck = pd.DataFrame(chk)
    Ck.to_csv(SUM / "check_vs_v1_mi_summary.csv", index=False)
    g1 = S[S.cohort.isin(["v1", "gate_v1pc"])]
    num = [c for c in S.columns if S[c].dtype.kind == "f"]
    piv = {co: g1[g1.cohort == co].sort_values(["set", "config", "contrast"])[num].to_numpy(float) for co in ("v1", "gate_v1pc")}
    dg = np.nanmax(np.abs(piv["v1"] - piv["gate_v1pc"]))
    res = dict(rows_checked=len(Ck), max_dev_vs_existing_v1_mi_summary=float(Ck.dev.max()),
               max_dev_gate_cells_summary_vs_v1=float(dg))
    (SUM / "summary_checks.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def privacy():
    K.umask()
    bad = []
    for f in sorted(OUT.rglob("*.csv")):
        if f.name.startswith("restricted_"):
            continue
        D = pd.read_csv(f, low_memory=False)
        for c in ("n", "n_t", "n_c", "n_pairs"):
            if c in D:
                v = pd.to_numeric(D[c], errors="coerce")
                if int(((v >= 1) & (v < K.MIN_CELL)).sum()):
                    bad.append((str(f.relative_to(OUT)), c))
        if "patient_key" in D or "person_id" in D:
            bad.append((str(f.relative_to(OUT)), "identifier column"))
    for f in sorted(OUT.rglob("*.json")):
        s = f.read_text()
        if "patient_key" in s or "person_id" in s:
            bad.append((str(f.relative_to(OUT)), "identifier key"))
    out = dict(clean=not bad, issues=bad, time=time.strftime("%Y-%m-%d %H:%M"))
    (OUT / "privacy_scan.json").write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["share", "run", "gate", "summarize", "privacy"])
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    w = min(a.workers, 16)
    K.umask()
    {"share": share, "run": lambda: run(w), "gate": gate, "summarize": lambda: summarize(w), "privacy": privacy}[a.cmd]()
