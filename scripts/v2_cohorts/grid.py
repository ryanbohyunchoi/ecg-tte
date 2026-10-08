#!/usr/bin/env python
"""Spec-v2 cohort grid: every version 1 rung x arm x configuration on a row subset of the version 1 analysed cohort.

A cohort fix is an exclusion (rows = analysed positions not flagged by specs_v2) plus, for AMPLIFY / LODESTAR / PROVE IT,
an outcome re-definition (T.y_t / T.y_e replaced on a shallow copy). Nothing new is encoded: only patients are removed.

Rungs (PS base design restricted to the rows; built exactly as the version 1 scripts, then row-subset):
  P1, P5, Flags, hdPS200, clinical      = scripts/v21/paper2_grid.task
  PS10                                  = scripts/v1_ps10/ps10.task (design + ex58 from its leakage map)
  clinical_nolvef                       = scripts/v1_psclin_nolvef/psclin_nolvef.task (re-imputed completed covariates
                                          without LVEF, reused; no re-imputation)
  Flags: the >= 1 % prevalence filter (and the constant-column filter) is re-applied within the rows.
  hdPS200: T.hd(200, t[rows], rows) re-ranks the hdPS levels on the fixed cohort (as the existing hd() does).
Arms: base, ECG, CLMBR, ECG+CLMBR, shufECG, shufCLMBR (6 configs) + CLMBR32 (main config; P1, P5, clinical, clinical_nolvef).
Representations (pipeline.md section 3: PCs within trial):
  pc = 'within' (PRIMARY): ECG 32 PCs = pcs(T.ecg_raw[rows], 64)[:, :32]; CLMBR-T 64 PCs = pcs(raw CLMBR-T[rows], 64)
  pc = 'old' (sensitivity): T.ecg_pc[rows], T.clm_pc[rows] (PCs fitted on the version 1 cohort)
  placebos: the arm's PCs permuted within the rows, np.random.default_rng(424242).permutation(len(rows)) (= T.shuffle_perm
  when rows is the full cohort).

Variants (cells/restricted_cells_<variant>.parquet):
  gateA    no fix, pc within, all 38 trials -> must reproduce the version 1 cells exactly (gate subcommand)
  v2       spec-v2 primary rules (unknown value passes), pc within           PRIMARY
  v2old    spec-v2 primary rules, pc old                                      sensitivity
  v2meas   spec-v2 with numeric bounds / COMET LVEF required to be measured, pc within   sensitivity
Trials whose v2 rows equal the full cohort and whose outcome is unchanged are not re-run (their version 1 cells are reused
by assemble).

Usage:
  grid.py run --variant gateA|v2|v2old|v2meas [--trials a,b] [--workers 32]
  grid.py gate                      -> cells/gate.csv, cells/gate_status.json
  grid.py assemble                  -> cells/restricted_cells_v2_all.parquet (+ v2old, v2meas): full 38-trial tables in the
                                       v21 column layout + cohort_spec='v2', variant; cells_v2_all.csv (suppressed)
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2common as K  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import ps10 as P10  # noqa: E402
import psclin_nolvef as PSC  # noqa: E402
from eval_longtail_balance import emb, pcs  # noqa: E402

E, P2, SP, C = K.E, K.P2, K.SP, K.C
VN = K.VN
VARIANTS = {"gateA": (None, "within"), "v2": ("drop_v2", "within"), "v2old": ("drop_v2", "old"), "v2meas": ("drop_v2meas", "within")}
NUMC = ["rb", "rs", "p_ps", "n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c", "retain"] + [f"smd:{c}" for c in VN]
TXT = ["key", "ex58", "cell_failed"]


# ================================================================ designs
def flags_rows(T, n, rows):
    """= paper2_grid.flags_matrix with the prevalence / constant filters computed within `rows`."""
    W = pd.read_parquet(P2.FLAGS / f"restricted_flags_{n}.parquet").set_index("patient_key").reindex(T.keys)
    B = (W.fillna(0) > 0).astype(float)
    expo = set(T.roles.get("exposure_features", []))
    import re
    cols = [c for c in B.columns if re.match(P2.ICD10_3, c) and c not in expo]
    B = B[cols].iloc[rows]
    prev = B.mean()
    keep = prev.index[(prev >= P2.FLAG_MIN_PREV) & (prev < 1.0)]
    return B[keep].to_numpy(float), len(keep)


def clm_raw(T):
    Cm = emb(T._ehr_glob)
    Cm = Cm[~Cm.index.duplicated()].reindex(T.keys)
    return Cm.to_numpy(float)


def subset(Xraw, rows):
    """Xraw[rows] in the memory order of Xraw (pandas to_numpy returns Fortran-ordered blocks; the version 1 PCs were fitted
    on that layout, and the SVD differs in the last bits between layouts)."""
    S = Xraw[rows]
    if Xraw.flags.f_contiguous and not Xraw.flags.c_contiguous:
        S = np.asfortranarray(S)
    return S


def load(n):
    T = E.load_trial(n) if n in K.AF.V.OLD else E.load_trial(n, cache=False)
    return T


def drop_rows(n, col):
    if col is None:
        return None, None
    D = pd.read_parquet(K.FLG / f"restricted_drop_{n}.parquet").set_index("patient_key")
    return D, D[col].to_numpy(bool)


def task(args):
    n, variant = args
    K.umask()
    t0 = time.time()
    col, pcmode = VARIANTS[variant]
    i = K.ALL.index(n)
    T = load(n)
    D, drop = drop_rows(n, col)
    if D is not None:
        assert D.index.equals(T.keys), n
    rows = np.arange(len(T.t)) if drop is None else np.where(~drop)[0]
    # outcome re-definition (restricted file written by flags.py), only in v2 variants
    TT = T
    ofile = K.FLG / f"restricted_outcome_{n}.parquet"
    if variant != "gateA" and ofile.exists():
        O = pd.read_parquet(ofile).set_index("patient_key")
        assert O.index.equals(T.keys), n
        TT = copy.copy(T)
        TT.y_t, TT.y_e = O.y_t.to_numpy(float), O.y_e.to_numpy(int)
    t = T.t[rows]
    # ---- rung designs (full cohort exactly as version 1, then row subset)
    b5, _, _ = C.designs(T, n, C.P5DX)
    X10, _, _, _ = P10.design(T, n)
    ex10 = P10.ex58_ps10()
    X1 = T.cov.iloc[rows][T.demo].to_numpy(float)
    Fl, nfl = flags_rows(T, n, rows)
    dx = T.X_dx[rows]
    Hk = T.hd(200, t=t, rows=rows)
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    nl_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys if c != "lvef"}
    cols_nl = [c for c in T.cov.columns if c != "lvef"]
    Z = pd.read_parquet(PSC.imp_path(n)).set_index("patient_key")
    Xre = Z.loc[T.keys, cols_nl].astype(float).to_numpy()
    rung = {"P1": (X1, set()), "P5": (b5[rows], set()), "PS10": (X10[rows], ex10), "Flags": (np.hstack([X1, Fl]), set()),
            "hdPS200": (np.hstack([dx, Hk]), set()), "clinical": (T.X_core[rows], clin_ex),
            "clinical_nolvef": (Xre[rows], nl_ex)}
    # ---- representations
    if pcmode == "within":
        ecg = pcs(subset(T.ecg_raw, rows), 64)[:, :32]
        clm = pcs(subset(clm_raw(T), rows), 64)
    else:
        ecg, clm = T.ecg_pc[rows], T.clm_pc[rows]
    assert clm.shape == (len(rows), 64) and np.isfinite(clm).all() and np.isfinite(ecg).all()
    perm = np.random.default_rng(424242).permutation(len(rows))
    blk = {"ecg": ecg, "she": ecg[perm], "clm": clm, "shc": clm[perm], "c32": clm[:, :32]}
    comp = {"base": [], "ECG": ["ecg"], "CLMBR": ["clm"], "ECG+CLMBR": ["clm", "ecg"], "shufECG": ["she"],
            "shufCLMBR": ["shc"], "CLMBR32": ["c32"]}
    out = []

    def rec(rg, cfg, arm, X, ex58):  # = paper2_grid.task.rec with rows
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
        out.append(dict(trial=n, key=K.KEY[n], idx=i, rung=rg, config=cfg, arm=arm, k_pcs=K.KPC[arm], rb=T.rb, rs=T.rs,
                        ex58=";".join(sorted(ex58)), p_ps=X.shape[1], cell_failed=fail,
                        **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c")},
                        retain=(o["n_pairs"] / small) if est[0] == "match" else np.nan,
                        **{f"smd:{c}": o[f"smd:{c}"] for c in VN}))

    for rg, (X, ex58) in rung.items():
        for cfg in K.CONFIGS:
            for a in K.ARMS:
                rec(rg, cfg, a, np.hstack([X] + [blk[b] for b in comp[a]]), ex58)
        if rg in K.C32_RUNGS:
            rec(rg, "main", "CLMBR32", np.hstack([X, blk["c32"]]), ex58)
    print(f"{variant} {n} rows {len(rows)}/{len(T.t)} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, variant=variant, secs=round(time.time() - t0, 1), n_flags=nfl, pcmode=pcmode,
                     outcome_redefined=TT is not T, rows_frac=round(len(rows) / len(T.t), 4))


def changed_trials(col):
    """trials whose fix removes >= 1 patient or redefines the outcome."""
    out = []
    for n in K.ALL:
        D = pd.read_parquet(K.FLG / f"restricted_drop_{n}.parquet")
        if D[col].any() or (K.FLG / f"restricted_outcome_{n}.parquet").exists():
            out.append(n)
    return out


def run(variant, trials, workers):
    from multiprocessing import get_context
    K.umask()
    K.CEL.mkdir(parents=True, exist_ok=True)
    col = VARIANTS[variant][0]
    tk = trials or (K.ALL if col is None else changed_trials(col))
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle",
           "rewind", "cabana-v2", "transform-hf", "precision")
    tk = sorted(tk, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    with get_context("fork").Pool(min(workers, len(tk))) as p:
        res = p.map(task, [(n, variant) for n in tk], chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    tag = "" if trials is None else "_partial"
    R.to_parquet(K.CEL / f"restricted_cells_{variant}{tag}.parquet")
    (K.CEL / f"log_{variant}{tag}.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    (K.CEL / f"run_{variant}{tag}.done").write_text(time.strftime("%Y-%m-%d %H:%M") + "\n")
    print("done", variant, len(R), flush=True)


# ================================================================ gate A
def reference():
    """version 1 cells for the 7 rungs (rung names unchanged)."""
    G = pd.read_parquet(K.REF_V21)
    G = G[G.rung.isin(["P1", "P5", "Flags", "hdPS200", "clinical"])]
    P = pd.read_parquet(K.REF_PS10)
    Q = pd.read_parquet(K.REF_PSCLIN)
    Qc = Q[(Q.rung == "clinical") & (Q.arm == "CLMBR32")]
    Qn = Q[Q.rung == "clinical_nolvef"]
    R = pd.concat([G, P, Qc, Qn], ignore_index=True)
    assert not R.duplicated(["trial", "rung", "config", "arm"]).any()
    return R


def gate(tag=""):
    K.umask()
    R = pd.read_parquet(K.CEL / f"restricted_cells_gateA{tag}.parquet")
    P = reference()
    rows = []
    for (rg, cfg, a), y in P.groupby(["rung", "config", "arm"]):
        x = R[(R.rung == rg) & (R.config == cfg) & (R.arm == a)].set_index("trial").sort_index()
        y = y.set_index("trial").sort_index()
        ix = y.index.intersection(x.index)
        for c in NUMC:
            xa, ya = x.loc[ix, c].to_numpy(float), y.loc[ix, c].to_numpy(float)
            dd = np.abs(xa - ya)
            rows.append(dict(rung=rg, config=cfg, arm=a, col=c, n_trials=len(ix), n_ref=len(y),
                             maxdev=float(np.nanmax(dd)) if np.isfinite(dd).any() else 0.0,
                             nan_mismatch=int((np.isnan(xa) ^ np.isnan(ya)).sum())))
        for c in TXT:
            rows.append(dict(rung=rg, config=cfg, arm=a, col=c, n_trials=len(ix), n_ref=len(y),
                             maxdev=float((x.loc[ix, c].fillna("").astype(str) != y.loc[ix, c].fillna("").astype(str)).sum()),
                             nan_mismatch=0))
    G = pd.DataFrame(rows)
    G.to_csv(K.CEL / f"gate{tag}.csv", index=False)
    ncell = int(G[G.col == "loghr"].n_trials.sum())
    st = dict(passed=bool(G.maxdev.max() == 0 and G.nan_mismatch.sum() == 0 and (G.n_trials == G.n_ref).all()
                          and (tag != "" or ncell == len(P))),
              maxdev=float(G.maxdev.max()), nan_mismatch=int(G.nan_mismatch.sum()), cells_compared=ncell, reference_cells=len(P),
              rungs=sorted(set(G.rung)), arms=sorted(set(G.arm)), configs=sorted(set(G.config)),
              worst=G.sort_values("maxdev").tail(5)[["rung", "config", "arm", "col", "maxdev"]].to_dict("records"),
              time=time.strftime("%Y-%m-%d %H:%M"))
    (K.CEL / f"gate_status{tag}.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    return st


# ================================================================ assemble
def assemble():
    """full 38-trial spec-v2 tables: re-run trials from the variant file, unchanged trials from the version 1 cells."""
    K.umask()
    st = json.loads((K.CEL / "gate_status.json").read_text())
    if not st["passed"]:
        raise SystemExit("gate A failed; not assembling")
    P = reference()
    for variant in ("v2", "v2old", "v2meas"):
        f = K.CEL / f"restricted_cells_{variant}.parquet"
        if not f.exists():
            continue
        R = pd.read_parquet(f)
        keep = P[~P.trial.isin(set(R.trial))]
        Z = pd.concat([R, keep[R.columns]], ignore_index=True)
        Z["cohort_spec"] = "v2"
        Z["variant"] = variant
        Z["refit"] = Z.trial.isin(set(R.trial))
        Z = Z.sort_values(["idx", "rung", "config", "arm"]).reset_index(drop=True)
        assert len(Z) == len(P), (variant, len(Z), len(P))
        Z.to_parquet(K.CEL / f"restricted_cells_{variant}_all.parquet")
        Zs = P2.suppress(Z)
        # differencing: v1 minus v2 arm sizes = patients removed per arm; blank the counts (and count-derived columns)
        # of trials where an arm lost 1-10 patients
        col = VARIANTS[variant][0]
        small = []
        for n in K.ALL:
            D = pd.read_parquet(K.FLG / f"restricted_drop_{n}.parquet")
            Fl = pd.read_parquet(K.FLG / f"restricted_meas_{n}.parquet").treated.to_numpy()
            d = D[col].to_numpy(bool)
            if any(1 <= d[Fl == a].sum() < K.MIN_CELL for a in (1, 0)):
                small.append(n)
        m = Zs.trial.isin(small)
        for c in ("n", "n_t", "n_c", "n_pairs", "ess_t", "ess_c", "retain"):
            Zs.loc[m, c] = np.nan
        Zs.loc[m, "suppressed_lt11"] = True
        Zs.to_csv(K.CEL / f"cells_{variant}_all.csv", index=False)
        print(variant, "count columns blanked (removal 1-10 in an arm):", small, flush=True)
        print(variant, len(Z), "refit trials", int(Z.drop_duplicates("trial").refit.sum()), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "gate", "assemble"])
    ap.add_argument("--variant", default="gateA", choices=list(VARIANTS))
    ap.add_argument("--trials", default="")
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    trials = [x for x in a.trials.split(",") if x] or None
    {"run": lambda: run(a.variant, trials, min(a.workers, 32)), "gate": lambda: gate(a.tag), "assemble": assemble}[a.cmd]()
