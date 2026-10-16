#!/usr/bin/env python
"""AoU grid (pipeline.md sections 4-7 without the ECG): PS ladder x arms x configurations, then across-trial contrasts.

Rungs (PS design; full cohort rows; fixed L2 C = 1 except the gbm configuration):
  P1        PS-Demo: age, sex, index year
  P5        PS-CVD5 (PRIMARY): P1 + hypertension, T2D, CAD, AF, HF (aou_build.step_dx10 = v1_ps10 CODES rule)
  CVD10     P1 + 10 fixed diagnoses (main ladder, as a comparison)
  Flags     P1 + ICD-10 3-character flags, full history, >= 1 % (supplement)
  hdPS200   P1 + investigator diagnoses (X_dx) + top 200 hdPS levels
  clinical  PS-Clinical without LVEF; 5-draw multiple imputation: per-item |SMD| averaged over draws, Cox log HR pooled by
            Rubin's rules (pipeline.md section 4)
Arms: base | CLMBR (+64 PCs) | shufCLMBR (+64 PCs permuted between patients, seed 424242) | CLMBR32 (main config, P1/P5)
Configurations: main (1:1 caliper 0.2) | cal01 | m13 (1:3) | iptw | overlap | gbm (= sens_primary32.CONFIGS)

Held-out items (aou_trial): 18 EHR vitals / labs (no LVEF, no echo), 11 survey items (answer on or before index), and
3 coded-record items. PRIMARY panel = the 29 non-coded items; secondary: EHR 18, survey 11, all 32, survey any-time.
Leakage masks (pipeline.md section 6, applied per cell = rung mask | arm mask | pooled |rho| >= 0.80 hits):
  P1 none | P5, CVD10, Flags: B_mean | hdPS200: coded 3 | clinical: coded 3 + 8 observed vitals/labs + eGFR | CLMBR: coded 3
A cell with < 11 matched pairs or a failed fit is failed: all items and the log HR are missing (F1 rule).

Usage: aou_grid.py leakage | run [--workers 8] [--trials a,b] | summarize [--workers 8] | privacy
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from collections import defaultdict  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aou_common as AC  # noqa: E402
import aou_stats as ST  # noqa: E402
import aou_trial as AT  # noqa: E402
from aou_build import CVD10_COLS, P5_COLS  # noqa: E402

CONFIGS = {"main": (("match", 0.2, 1), ("l2", 1.0)), "cal01": (("match", 0.1, 1), ("l2", 1.0)),
           "m13": (("match", 0.2, 3), ("l2", 1.0)), "iptw": (("iptw",), ("l2", 1.0)),
           "overlap": (("overlap",), ("l2", 1.0)), "gbm": (("match", 0.2, 1), ("gbm", None))}
RUNGS = ["P1", "P5", "CVD10", "Flags", "hdPS200", "clinical"]
ARMS = ["base", "CLMBR", "shufCLMBR"]
KPC = {"base": 0, "CLMBR": 64, "shufCLMBR": 64, "CLMBR32": 32}
N_IMP = 5
VARS = AT.all_vars()
VN = [c for c, _, _ in VARS]
GROUP = {c: g for c, _, g in VARS}
CODED = [c for c, _, _ in AT.CODED_VARS]
EHR = [c for c, _, _ in AT.EHR_VARS]
SV = [c for c, _, _ in AT.survey_vars()]
SV_ANY = [c for c, _, _ in AT.survey_vars_other()]
PANELS = {"prim": EHR + SV, "ehr": EHR, "sv": SV, "all": CODED + EHR + SV, "svany": EHR + SV_ANY}
OBS8 = [c for c in EHR if c.startswith("smd_obs_")]
MASK_RUNG = {"P1": [], "P5": ["B_mean"], "CVD10": ["B_mean"], "Flags": ["B_mean"], "hdPS200": CODED,
             "clinical": CODED + OBS8 + ["pp_LAB__egfr"]}
MASK_ARM = {"CLMBR": CODED, "shufCLMBR": CODED, "CLMBR32": CODED}
RHO_MASK, RHO_SOFT, MIN_ROWS = 0.80, 0.50, 100
G = lambda: AC.paths()["grid"]  # noqa: E731


def trials_ready() -> list:
    out = []
    for n in AC.S38:
        D = AC.trial_dir(n)
        need = [D / "baseline" / "DONE", D / "dx10" / "DONE", D / "flags" / "DONE", D / "panel" / "restricted_panel.parquet",
                D / "labs" / "DONE", D / "survey" / "DONE", D / "outcomes" / "DONE"]
        if all(p.exists() for p in need) and any((D / "clmbr").glob("restricted_embeddings_*.parquet")):
            out.append(n)
    return out


def designs(T, n_imp=N_IMP):
    """rung -> list of design matrices (one per imputation draw for clinical; one otherwise) and column names."""
    X1 = T.cov[T.demo].to_numpy(float)
    P5 = np.nan_to_num(np.column_stack([X1, T.dx10[P5_COLS].to_numpy(float)]))
    C10 = np.nan_to_num(np.column_stack([X1, T.dx10[CVD10_COLS].to_numpy(float)]))
    Fl, fnames = T.flags_matrix()
    Hk = T.hd(200)
    clin = []
    D = AC.trial_dir(T.n) / "baseline"
    for i in range(1, n_imp + 1):
        Z = pd.read_parquet(D / f"restricted_completed_{i:02d}.parquet").set_index("patient_key").reindex(T.keys)
        clin.append(Z[T.core].to_numpy(float))
    assert np.allclose(clin[0], T.X_core, equal_nan=True)
    return {"P1": ([X1], list(T.demo)), "P5": ([P5], list(T.demo) + P5_COLS), "CVD10": ([C10], list(T.demo) + CVD10_COLS),
            "Flags": ([np.hstack([X1, Fl])], list(T.demo) + fnames), "hdPS200": ([np.hstack([T.X_dx, Hk])], None),
            "clinical": (clin, list(T.core))}


# ================================================================ leakage (= v1_ps10.leakage algorithm, AoU inputs)
def _rank(x):
    from scipy.stats import rankdata
    return rankdata(x)


def _pearson(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else np.nan


def leakage():
    os.umask(0o077)
    out = AC.private_dir(G() / "leakage")
    Y, X = {}, defaultdict(dict)
    for n in trials_ready():
        T = AT.AouTrial(n)
        vc = AT.var_components(T.H, VARS)
        Y[n] = {c: (v, T.H[c].to_numpy(float)) for v, cs in vc.items() for c in cs}
        Dz = designs(T, n_imp=1)
        for rg in ("P5", "CVD10", "clinical"):
            M, names = Dz[rg]
            for j, nm in enumerate(names):
                X[rg][(n, nm)] = M[0][:, j]
        print(n, "loaded", flush=True)
    rows = []
    for rg, Xr in X.items():
        inputs = sorted({nm for (_, nm) in Xr})
        comps = sorted({c for n in Y for c in Y[n]})
        for c in comps:
            ycache = {}
            for nm in inputs:
                tl = [n for n in Y if c in Y[n] and (n, nm) in Xr]
                if not tl:
                    continue
                y = np.concatenate([Y[n][c][1] for n in tl])
                x = np.concatenate([Xr[(n, nm)] for n in tl])
                ok = np.isfinite(y) & np.isfinite(x)
                if ok.sum() < MIN_ROWS or np.std(y[ok]) == 0 or np.std(x[ok]) == 0:
                    rho = np.nan
                else:
                    sig = (tuple(tl), ok.tobytes())
                    if sig not in ycache:
                        ycache = {sig: _rank(y[ok])}
                    xb = x[ok]
                    rho = _pearson(xb if np.isin(xb, (0.0, 1.0)).all() else _rank(xb), ycache[sig])
                item = next(v for n in tl for v, _ in [Y[n][c]])
                rows.append(dict(rung=rg, component=c, item=item, input=nm, n_trials=len(tl), rho=rho))
    PO = pd.DataFrame(rows)
    PO["arho"] = PO.rho.abs()
    PO.to_csv(out / "pooled.csv", index=False)
    hits = {rg: sorted(set(PO[(PO.rung == rg) & (PO.arho >= RHO_MASK)].item)) for rg in X}
    soft = {rg: sorted(set(PO[(PO.rung == rg) & (PO.arho >= RHO_SOFT) & (PO.arho < RHO_MASK)].item)) for rg in X}
    AC.write_json(out / "leakage_status.json", dict(masked=hits, soft=soft, rule=f"pooled |rho| >= {RHO_MASK} masks the item",
                                                    when=time.strftime("%Y-%m-%d %H:%M")))
    print(json.dumps(dict(masked=hits, soft=soft), indent=1))


def leak_hits() -> dict:
    f = G() / "leakage" / "leakage_status.json"
    if not f.exists():
        raise SystemExit("run `aou_grid.py leakage` first")
    return json.loads(f.read_text())["masked"]


# ================================================================ cells
def task(n):
    t0 = time.time()
    T = AT.AouTrial(n)
    Dz = designs(T)
    perm = T.shuffle_perm
    CLM = T.clm_pc
    assert CLM.shape == (len(T.t), 64) and np.isfinite(CLM).all()
    blk = {"base": None, "CLMBR": CLM, "shufCLMBR": CLM[perm], "CLMBR32": CLM[:, :32]}
    out = []

    def one(X, cfg):
        est, psm = CONFIGS[cfg]
        try:
            return ST.run_cell(T, X, VARS, estimator=est, ps_model=psm), ""
        except IndexError as e:  # empty matched set (paper2_grid.rec)
            return dict(n=len(T.t), n_t=int(T.t.sum()), n_c=int((1 - T.t).sum()), n_pairs=0, loghr=np.nan, se=np.nan,
                        loghr_admin=np.nan, se_admin=np.nan, ess_t=0.0, ess_c=0.0, **{f"smd:{c}": np.nan for c in VN}), \
                f"no matched pairs ({type(e).__name__})"

    def rec(rg, cfg, arm, Xs):
        res = [one(X if blk[arm] is None else np.hstack([X, blk[arm]]), cfg) for X in Xs]
        o = dict(res[0][0])
        fail = ";".join(sorted({f for _, f in res if f}))
        if len(res) > 1:  # multiple imputation: average item |SMD|, Rubin's rules, minimum pairs (failure rule)
            for c in VN:
                v = np.array([r[f"smd:{c}"] for r, _ in res], float)
                o[f"smd:{c}"] = float(np.nanmean(v)) if np.isfinite(v).any() else np.nan
            o["loghr"], o["se"] = ST.rubin([r["loghr"] for r, _ in res], [r["se"] for r, _ in res])
            o["loghr_admin"], o["se_admin"] = ST.rubin([r["loghr_admin"] for r, _ in res], [r["se_admin"] for r, _ in res])
            o["n_pairs"] = np.nanmin([r["n_pairs"] for r, _ in res]) if CONFIGS[cfg][0][0] == "match" else np.nan
        small = min(o["n_t"], o["n_c"])
        out.append(dict(trial=n, key=T.key, rung=rg, config=cfg, arm=arm, k_pcs=KPC[arm], rb=T.rb, rs=T.rs, n_draws=len(res),
                        p_ps=Xs[0].shape[1] + (0 if blk[arm] is None else blk[arm].shape[1]), cell_failed=fail,
                        **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se", "loghr_admin", "se_admin", "ess_t", "ess_c")},
                        retain=(o["n_pairs"] / small) if CONFIGS[cfg][0][0] == "match" else np.nan,
                        **{f"smd:{c}": o[f"smd:{c}"] for c in VN}))

    for rg in RUNGS:
        Xs, _ = Dz[rg]
        for cfg in CONFIGS:
            for a in ARMS:
                rec(rg, cfg, a, Xs)
        if rg in ("P1", "P5"):
            rec(rg, "main", "CLMBR32", Xs)
    print(f"{n} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, n=AC.suppress20(len(T.t)), secs=round(time.time() - t0, 1))


def run(workers, trials=None):
    from multiprocessing import get_context
    os.umask(0o077)
    out = AC.private_dir(G() / "cells")
    tk = trials or trials_ready()
    if not tk:
        raise SystemExit("no trial is ready (see aou_build.py status)")
    with get_context("spawn").Pool(min(workers, len(tk))) as p:
        res = p.map(task, tk, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    tag = "" if trials is None else "_partial"
    R.to_parquet(out / f"restricted_cells{tag}.parquet")
    AC.suppress_frame(R).to_csv(out / f"cells{tag}.csv", index=False)
    AC.write_json(out / f"log{tag}.json", [lg for _, lg in res])


# ================================================================ summaries
def failed(g):
    return g.cell_failed.fillna("").astype(str).ne("") | (g.n_pairs.notna() & (g.n_pairs < AC.MIN_PAIRS))


def load_F(R, hits, outcome="primary"):
    F, SM, RET = {}, {}, {}
    order = [t for t in AC.S38 if t in set(R.trial)]
    for (rg, cfg, a), g in R.groupby(["rung", "config", "arm"]):
        g = g.set_index("trial", drop=False).loc[[t for t in order if t in set(g.trial)]].copy()
        if outcome == "admin":
            g["loghr"], g["se"] = g.loghr_admin, g.se_admin
        fl = failed(g).to_numpy()
        g.loc[fl, [f"smd:{c}" for c in VN] + ["loghr", "se"]] = np.nan
        m = sorted(set(MASK_RUNG[rg]) | set(MASK_ARM.get(a, [])) | set(hits.get(rg, [])))
        g["ex58"] = ";".join(m)
        F[(rg, cfg, a)], SM[(rg, cfg, a)] = ST.per_trial(g, VN)
        small = (pd.to_numeric(g.n_pairs, errors="coerce") >= 1) & (pd.to_numeric(g.n_pairs, errors="coerce") <= AC.MIN_COUNT)
        RET[(rg, cfg, a)] = g.retain.mask(small)
    return F, SM, RET


def contrasts():
    L = []
    for cfg in CONFIGS:
        for rg in RUNGS:
            for a, b, side in (("CLMBR", "base", "one"), ("shufCLMBR", "base", "two"), ("CLMBR", "shufCLMBR", "one")):
                L.append((cfg, f"{rg}: {a} vs {b}", "within", rg, a, rg, b, side))
        for ra, aa, rb, ab in (("P1", "CLMBR", "Flags", "base"), ("P1", "CLMBR", "hdPS200", "base"), ("P5", "CLMBR", "hdPS200", "base"),
                               ("P5", "CLMBR", "clinical", "base"), ("P5", "CLMBR", "CVD10", "base")):
            L.append((cfg, f"{ra}+{aa} vs {rb} {ab}", "across", ra, aa, rb, ab, "two"))
        for ra, rb in (("P5", "P1"), ("CVD10", "P5"), ("hdPS200", "P5"), ("clinical", "P5"), ("Flags", "P1")):
            L.append((cfg, f"ladder: {ra} vs {rb}", "ladder", ra, "base", rb, "base", "two"))
    for rg in ("P1", "P5"):
        for a, b, side in (("CLMBR32", "base", "one"), ("CLMBR", "CLMBR32", "two")):
            L.append(("main", f"{rg}: {a} vs {b}", "clmbr32", rg, a, rg, b, side))
    L.append(("main", "P1+CLMBR32 vs Flags base", "clmbr32", "P1", "CLMBR32", "Flags", "base", "two"))
    return L


def mask(SM, keep):
    S = SM.copy()
    S.loc[:, [c for c in S.columns if c not in keep]] = np.nan
    return S


_G = {}


def _row(args):
    sname, (cfg, lab, kind, ra, aa, rb, ab, side) = args
    F, SM, CL, RET, FA = _G["F"], _G["SM"], _G["CL"], _G["RET"], _G["FA"]
    ka, kb = (ra, cfg, aa), (rb, cfg, ab)
    if ka not in F or kb not in F:
        return None, []
    tr = [t for t in _G["SETS"][sname] if t in F[ka].index and t in F[kb].index]
    if len(tr) < 3:
        return None, []
    Fa, Fb = F[ka], F[kb]
    row = dict(set=sname, config=cfg, contrast=lab, kind=kind, rung_a=ra, arm_a=aa, rung_b=rb, arm_b=ab, sided=side, n_trials=len(tr))
    for pn, items in PANELS.items():
        r = ST.contrast_row(Fa, Fb, tr, side, CL, mask(SM[ka], items), mask(SM[kb], items))
        for k, v in r.items():
            if k.startswith(("lt01_", "m58_", "relred")):
                row[f"{pn}_{k.replace('m58_', 'm_').replace('relred', 'relred')}"] = v
            elif pn == "prim":  # agreement endpoints do not depend on the panel
                row[k] = v
    if side == "two":
        la, lb, rbv = Fa.loc[tr, "loghr"].to_numpy(), Fb.loc[tr, "loghr"].to_numpy(), Fb.loc[tr, "rb"].to_numpy()
        ok = np.isfinite(la) & np.isfinite(lb)
        row["bshuf_p"] = ST.bshuf2(la[ok], lb[ok], rbv[ok])
    # agreement under the censoring sensitivity (administrative end only = Yale rule)
    Fa2, Fb2 = FA[ka], FA[kb]
    r2 = ST.contrast_row(Fa2, Fb2, tr, side, CL, mask(SM[ka], PANELS["prim"]), mask(SM[kb], PANELS["prim"]))
    row.update(absd_admin_a=r2["absd_a"], absd_admin_b=r2["absd_b"], absd_admin_p=r2["absd_p"])
    for lab_, FF, k in (("a", Fa, ka), ("b", Fb, kb)):
        mm = ST.agree_metrics(FF.loc[tr])
        row.update({f"{lab_}_{q}": v for q, v in mm.items()})
        row[f"{lab_}_retain"] = float(RET[k].loc[tr].mean())
    dom = []
    for g in dict.fromkeys(GROUP[c] for c in PANELS["all"] + SV_ANY):
        cols = [c for c in VN if GROUP[c] == g]
        Fa_, Fb_ = ST.paired_balance(Fa, Fb, mask(SM[ka], cols), mask(SM[kb], cols), tr)
        pf = ST.p1s if side == "one" else ST.p2s
        d = -(Fa_.loc[tr, "m58"] - Fb_.loc[tr, "m58"])
        e, lo, hi, kk = ST.relred_ci(Fb_.loc[tr, "m58"], Fa_.loc[tr, "m58"])
        dom.append(dict(set=sname, config=cfg, contrast=lab, kind=kind, sided=side, domain=g, n_items=len(cols),
                        mean_a=Fa_.loc[tr, "m58"].mean(), mean_b=Fb_.loc[tr, "m58"].mean(),
                        better=f"{int((d > 0).sum())}/{int(d.notna().sum())}", p=pf(d.to_numpy()), relred=e, relred_lo=lo,
                        relred_hi=hi, k=kk))
    return row, dom


BAL_FAM = ["prim_m_p", "prim_lt01_p", "all_m_p", "all_lt01_p"]
AGR_FAM = ["absd_p", "cons_p", "bshuf_p"]


def summarize(workers):
    from multiprocessing import get_context
    os.umask(0o077)
    out = AC.private_dir(G() / "summary")
    R = pd.read_parquet(G() / "cells" / "restricted_cells.parquet")
    hits = leak_hits()
    F, SM, RET = load_F(R, hits)
    FA, _, _ = load_F(R, hits, outcome="admin")
    reg = AC.registry()
    CLk = AC.comparator_clusters()
    CL = {n: CLk.get(reg[n], n) for n in reg}
    sets = {k: [t for t in v if t in set(R.trial)] for k, v in AC.analysed_sets().items()}
    _G.update(F=F, SM=SM, CL=CL, RET=RET, FA=FA, SETS=sets)
    jobs = [(s, c) for s in sets for c in contrasts()]
    with get_context("fork").Pool(min(workers, len(jobs))) as p:
        res = p.map(_row, jobs, chunksize=4)
    S = pd.DataFrame([r for r, _ in res if r is not None])
    Dm = pd.DataFrame([d for _, ds in res for d in ds])
    for sname in sets:
        ms = S.set == sname
        for fam, cols in (("balance", BAL_FAM), ("agreement", AGR_FAM)):
            long = S.loc[ms, cols].stack(dropna=True)
            if len(long):
                q = pd.Series(ST.bh_fdr(long.to_numpy()), index=long.index).unstack()
                for c in cols:
                    S.loc[ms, f"q_{c}_fam"] = q[c] if c in q else np.nan
        if len(Dm):
            md_ = Dm.set == sname
            idx = Dm.index[md_ & Dm.p.notna()]
            Dm.loc[idx, "q_domain_fam"] = ST.bh_fdr(Dm.loc[idx, "p"].to_numpy())
    S.to_csv(out / "contrasts.csv", index=False)
    Dm.to_csv(out / "domains.csv", index=False)
    # per-trial aggregates (trial level only; counts suppressed at 1-20)
    pt = []
    for k, Fk in F.items():
        rg, cfg, a = k
        for t in Fk.index:
            S_ = SM[k].loc[t]
            row = dict(trial=t, rung=rg, config=cfg, arm=a, absd=Fk.loc[t, "absd"], loghr=Fk.loc[t, "loghr"], se=Fk.loc[t, "se"],
                       rb=Fk.loc[t, "rb"], rs=Fk.loc[t, "rs"], retain=float(RET[k].loc[t]))
            for pn, items in PANELS.items():
                v = S_[[c for c in items if c in S_.index]]
                row[f"m_{pn}"] = float(v.mean())
                row[f"lt01_{pn}"] = float(100 * (v < 0.1).sum() / v.notna().sum()) if v.notna().any() else np.nan
            pt.append(row)
    PT = pd.DataFrame(pt).merge(R[["trial", "rung", "config", "arm", "n_pairs", "n_t", "n_c", "n"]], on=["trial", "rung", "config", "arm"], how="left")
    AC.suppress_frame(PT).to_csv(out / "per_trial.csv", index=False)
    tables(out, S)
    AC.write_json(out / "privacy_scan.json", AC.privacy_scan(out))
    print(S[(S.config == "main") & S.contrast.str.startswith("P5")][["set", "contrast", "n_trials", "prim_relred", "prim_relred_lo",
                                                                     "prim_relred_hi", "prim_m_p"]].to_string(index=False))


def tables(out: Path, S: pd.DataFrame):
    def md(D, d=3):
        D = D.copy()
        for c in D.columns:
            if pd.api.types.is_float_dtype(D[c]):
                D[c] = D[c].map(lambda x: "" if pd.isna(x) else f"{x:.{d}g}" if abs(x) < 1e-3 else f"{x:.{d}f}")
        return "| " + " | ".join(D.columns) + " |\n|" + "---|" * len(D.columns) + "\n" + \
            "\n".join("| " + " | ".join(str(v) for v in r) + " |" for r in D.itertuples(index=False))
    cb = ["contrast", "n_trials", "prim_m_a", "prim_m_b", "prim_relred", "prim_relred_lo", "prim_relred_hi", "prim_m_better", "prim_m_p",
          "q_prim_m_p_fam", "ehr_relred", "sv_relred", "all_relred", "svany_relred"]
    ca = ["contrast", "absd_a", "absd_b", "absd_better", "absd_p", "bshuf_p", "q_absd_p_fam", "absd_admin_p", "a_r", "b_r", "a_retain", "b_retain"]
    L = ["# AoU grid tables (scripts/aou/aou_grid.py; source grid/summary/contrasts.csv; aggregates only)\n"]
    for sname in S.set.unique():
        for cfg in CONFIGS:
            q = S[(S.set == sname) & (S.config == cfg)]
            L.append(f"\n## {sname}, {cfg}: balance (29 non-coded items primary)\n\n" + md(q[[c for c in cb if c in q]]))
            L.append(f"\n## {sname}, {cfg}: agreement\n\n" + md(q[[c for c in ca if c in q]]))
    (out / "tables.md").write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["leakage", "run", "summarize", "privacy"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--trials", default="")
    a = ap.parse_args()
    if a.cmd == "leakage":
        leakage()
    elif a.cmd == "run":
        run(a.workers, [x for x in a.trials.split(",") if x] or None)
    elif a.cmd == "summarize":
        summarize(a.workers)
    else:
        print(json.dumps(AC.privacy_scan(G()), indent=1))


if __name__ == "__main__":
    main()
