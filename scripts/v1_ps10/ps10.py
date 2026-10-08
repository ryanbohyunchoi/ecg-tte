#!/usr/bin/env python
"""PS-10 (user decision 2026-10-08): a FIXED propensity-score design for every trial = PS-Demo (age, sex, index year) +
yes/no flags for 10 diagnoses, no obesity. Doc: docs/v1_ps10/PS10.md.

Version 1 code is imported unchanged: scripts/v21/paper2_grid.py (P2: CONFIGS, ARMS, suppress, _row / bal_light machinery),
scripts/v20/sens_primary32.py (SP), scripts/v18/v18_clmbr.designs (the PS-CVD5 design), v16_engine.run_cell.

PS-10 design columns (full cohort rows r = arange(n), nan_to_num as P5):
  1-8   = v18_clmbr.designs(T, n, P5DX), unchanged: age_at_index, male, index_year, hypertension_v11, t2d, cad_ihd,
          atrial_fibrillation, hf_any_365 (elx_chf where hf_any_365 is absent)
  9     ckd                          = T.cov["ckd"]                          (v1.1 core baseline; N18)
  10    copd_or_asthma               = T.cov["copd_or_asthma"]               (J44, J45, J46)
  11    peripheral_arterial_disease  = T.cov["peripheral_arterial_disease"]  (I70.2, I73.9)
  12    stroke_tia                   = T.cov["stroke_history"] OR tia        (I60-I64, I69 OR G45)
  13    valve_disease                = T.cov["valve_disease"]                (I05-I08, I34-I37)
  v1.1 core baseline rule (scripts/build_core_baseline.build): OMOP gold condition_occurrence, condition_source_value with
  dots removed, ICD-10 prefix match, condition_start_date in [index-365, index-1]. tia (G45) is stored in the v1.1
  baseline only for trials that declare it in trial_specs extra_dx; it is re-extracted here for every trial with that exact
  rule (`extract`), and the re-extraction is checked against every stored v1.1 diagnosis column.

Usage (OUT = audits/claude-v1-ps10, umask 077):
  ps10.py extract                 -> OUT/flags/restricted_dx_<trial>.parquet, flags/extract_check.csv, flags/extract_status.json
  ps10.py designlog [--workers]   -> OUT/flags/design_log.csv (prevalence per flag x trial, suppressed; constant flags)
  ps10.py leakage [--workers]     -> OUT/leakage/pooled.csv, items.csv, soft_pairs.csv, gate_vs_r2.csv, leakage_status.json
  ps10.py run [--workers 24]      -> OUT/cells/restricted_cells.parquet (rung PS10), restricted_cells_P5gate.parquet,
                                     cells.csv (suppressed), log.json
  ps10.py gate                    -> OUT/cells/gate.csv, gate_status.json (rebuilt P5 vs claude-v21-paper2 cells, exact)
  ps10.py summarize [--workers]   -> OUT/summary/contrasts.csv, domains.csv, ladder.csv, failed_cells.csv
  ps10.py tables                  -> OUT/summary/tables.md
  ps10.py privacy                 -> OUT/privacy_scan.json
Aggregates only; counts 1-10 suppressed (incl. derivable) in every csv.
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
for p in ("v21", "v20", "v18", ""):
    sys.path.insert(0, str(HERE.parent / p) if p else str(HERE.parent))
import paper2_grid as P2  # noqa: E402

SP, E, V, C, AF = P2.SP, P2.E, P2.V, P2.C, P2.AF
A = SP.A
OUT = A / "claude-v1-ps10"
FLG, LEAK, CEL, SUM = OUT / "flags", OUT / "leakage", OUT / "cells", OUT / "summary"
GRID = P2.OUT / "restricted_cells.parquet"
R2POOL = A / "claude-r2" / "leakage" / "r4_pooled.csv"
ALL, KEY, VN, GROUP, NONCODED = P2.ALL, P2.KEY, P2.VN, P2.GROUP, P2.NONCODED
CONFIGS, S32, S38 = P2.CONFIGS, P2.S32, P2.S38
ARMS = P2.ARMS  # base, ECG, CLMBR, ECG+CLMBR, shufECG, shufCLMBR
KPC = P2.KPC
MIN_PAIRS = SP.MIN_CELL  # 11
GOLD = "/mnt/raid0/rbc58/omop/gold"
RHO_MASK, RHO_SOFT, MIN_ROWS = 0.80, 0.50, 100

from trial_specs import DX_CORE  # noqa: E402

TIA = ["G45"]
NEW5 = ["ckd", "copd_or_asthma", "peripheral_arterial_disease", "stroke_tia", "valve_disease"]
CODES = {"hypertension (hypertension_v11)": DX_CORE["hypertension"], "t2d": ["E11"],
         "cad_ihd": DX_CORE["ischemic_heart_disease_or_mi"], "atrial_fibrillation": DX_CORE["atrial_fibrillation"],
         "hf_any_365": ["I50", "I110", "I130", "I132"], "ckd": DX_CORE["ckd"], "copd_or_asthma": DX_CORE["copd_or_asthma"],
         "peripheral_arterial_disease": DX_CORE["peripheral_arterial_disease"],
         "stroke_tia": DX_CORE["stroke_history"] + TIA, "valve_disease": DX_CORE["valve_disease"]}
CODED4 = ["mean_meds", "mean_util", "B_mean", "smd_prog_full"]
PHYS9 = ("lvef", "sbp", "dbp", "heart_rate", "bmi", "creatinine", "potassium", "sodium", "hemoglobin")
OBS9 = [f"smd_obs_{c}" for c in PHYS9]
CLIN_NEAR = ["pp_LAB__egfr", "pp_LVFUNC__ef", "pp_LVFUNC__lv_sys_grade"]
LABEL = {"P1": "PS-Demo", "P5": "PS-CVD5", "PS10": "PS-10", "Flags": "PS-Flags", "hdPS200": "hdPS", "clinical": "PS-Clinical (v1, with LVEF)"}


def umask():
    os.umask(0o077)


def sup_n(k):
    return None if 1 <= int(k) < MIN_PAIRS else int(k)


# ================================================================ 1. extraction (tia, plus re-extraction check)
def roster(n):
    s = json.loads((A / f"claude-{n}-baseline-v11" / "summary.json").read_text())
    R = pd.read_parquet(s["roster"])
    assert "person_id" in R, n
    return R[["patient_key", "person_id", "index_date"]].assign(trial=n)


def extract():
    from trial_common import code_like, connect, rp
    umask()
    FLG.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    R = pd.concat([roster(n) for n in ALL], ignore_index=True)
    con = connect(16, "100GB")
    con.register("roster_df", R)
    con.execute("CREATE TEMP TABLE r AS SELECT trial, patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx "
                "FROM roster_df")
    dx = {k: v for k, v in DX_CORE.items()}
    dx["tia"] = TIA
    allp = sorted({p for v in dx.values() for p in v})
    # = build_core_baseline.build: condition_occurrence, source value without dots, [idx-365, idx], then d < idx per flag
    con.execute(f"""CREATE TEMP TABLE cond AS SELECT r.trial, r.patient_key, r.idx, c.condition_start_date d,
            upper(replace(c.condition_source_value, '.', '')) code
        FROM r JOIN {rp(GOLD, 'condition_occurrence')} c USING (person_id)
        WHERE c.condition_start_date BETWEEN r.idx - INTERVAL 365 DAY AND r.idx""")
    con.execute(f"DELETE FROM cond WHERE NOT {code_like('code', allp)}")
    F = {}
    for name, pre in dx.items():
        s = con.execute(f"SELECT DISTINCT trial, patient_key FROM cond WHERE d < idx AND {code_like('code', pre)}").df()
        F[name] = set(zip(s.trial, s.patient_key))
    rows, st = [], dict(trials=len(ALL), secs=None)
    for n in ALL:
        Rn = R[R.trial == n]
        D = pd.DataFrame({name: [float((n, k) in F[name]) for k in Rn.patient_key] for name in dx}, index=Rn.patient_key.to_numpy())
        D.index.name = "patient_key"
        D.reset_index().to_parquet(FLG / f"restricted_dx_{n}.parquet")
        B = pd.read_parquet(A / f"claude-{n}-baseline-v11" / "restricted_baseline_observed.parquet").set_index("patient_key")
        assert B.index.equals(D.index) or set(B.index) == set(D.index), n
        for name in dx:
            if name not in B:
                rows.append(dict(trial=n, flag=name, stored=False, n_roster=len(D), exact=None, agree_frac=None))
                continue
            a, b = D[name].to_numpy(), B.loc[D.index, name].to_numpy(float)
            mis = int((a != b).sum())
            rows.append(dict(trial=n, flag=name, stored=True, n_roster=len(D), exact=mis == 0,
                             agree_frac=round(1 - mis / len(D), 6) if (mis == 0 or mis > 10) else "suppressed (1-10 mismatches)"))
    X = pd.DataFrame(rows)
    X.to_csv(FLG / "extract_check.csv", index=False)
    s = X[X.stored]
    st.update(secs=round(time.time() - t0), stored_checks=int(len(s)), stored_exact=int(s.exact.sum()),
              all_exact=bool(s.exact.all()), tia_stored_trials=sorted(X[(X.flag == "tia") & X.stored].trial),
              tia_extracted_trials=len(ALL), codes={k: v for k, v in dx.items()})
    (FLG / "extract_status.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))


# ================================================================ 2. design
def design(T, n):
    """-> PS-10 design (all rows of T.keys), column names, P5 base (from C.designs, untouched), info."""
    b5, psn5, hf = C.designs(T, n, C.P5DX)
    D = pd.read_parquet(FLG / f"restricted_dx_{n}.parquet").set_index("patient_key").reindex(T.keys)
    assert D.notna().all().all(), f"{n}: extracted flags missing for some T.keys"
    cov = T.cov
    # binary dx are never imputed: completed == observed (checked)
    Bo = pd.read_parquet(A / f"claude-{n}-baseline-v11" / "restricted_baseline_observed.parquet").set_index("patient_key").reindex(T.keys)
    for c in ("ckd", "copd_or_asthma", "peripheral_arterial_disease", "stroke_history", "valve_disease"):
        assert np.array_equal(cov[c].to_numpy(float), Bo[c].to_numpy(float)), (n, c)
    tia = D["tia"].to_numpy(float)
    if "tia" in cov:
        assert np.array_equal(cov["tia"].to_numpy(float), tia), f"{n}: stored tia != re-extracted tia"
    stroke_tia = np.maximum(cov["stroke_history"].to_numpy(float), tia)
    new = np.column_stack([cov["ckd"].to_numpy(float), cov["copd_or_asthma"].to_numpy(float),
                           cov["peripheral_arterial_disease"].to_numpy(float), stroke_tia, cov["valve_disease"].to_numpy(float)])
    X = np.nan_to_num(np.hstack([b5, new]))
    names = list(psn5) + NEW5
    return X, names, b5, hf


def _dlog(n):
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    X, names, _, hf = design(T, n)
    out = []
    N = len(T.t)
    for j, c in enumerate(names[3:]):
        for arm, m in (("all", np.ones(N, bool)), ("treated", T.t == 1), ("control", T.t == 0)):
            k, nn = int(X[m, j + 3].sum()), int(m.sum())
            ok = not (1 <= k < MIN_PAIRS or 1 <= nn - k < MIN_PAIRS)
            out.append(dict(trial=n, key=KEY[n], flag=c, group=arm, prevalence=round(k / nn, 4) if ok else None,
                            suppressed=not ok, constant=bool(k == 0 or k == nn)))
    print(n, flush=True)
    return out, dict(trial=n, hf_column=hf, n_cols=X.shape[1])


def designlog(workers):
    from multiprocessing import Pool
    umask()
    with Pool(min(workers, len(ALL))) as p:
        res = p.map(_dlog, ALL, chunksize=1)
    L = pd.DataFrame([x for o, _ in res for x in o])
    L.to_csv(FLG / "design_log.csv", index=False)
    pd.DataFrame([i for _, i in res]).to_csv(FLG / "design_hf_column.csv", index=False)
    c = L[(L.group == "all") & L.constant]
    print("constant flags (all rows):", c[["trial", "flag"]].to_string(index=False) if len(c) else "none")


# ================================================================ 3. leakage (pooled Spearman, R2 r4 algorithm)
def _rank(v):
    from scipy.stats import rankdata
    return rankdata(v)


def _pearson(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else np.nan


def _lload(n):
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    X, names, _, _ = design(T, n)
    vc = E.var_components(T.H)
    Y, ci = {}, {}
    for v, cs in vc.items():
        for c in cs:
            Y[c] = T.H[c].to_numpy(np.float32)
            ci[c] = v
    # PS-10 inputs, plus the 5 S3 source columns (stroke_history alone) for the R2 cross-check
    Xd = dict(zip(names, X.astype(np.float32).T))
    Xd.update({f"S3::{c}": T.X_core[:, list(T.cov.columns).index(c)].astype(np.float32)
               for c in ("ckd", "copd_or_asthma", "peripheral_arterial_disease", "stroke_history", "valve_disease")})
    print(n, "loaded", flush=True)
    return n, Y, ci, Xd


_G = {}


def _ptask(c):
    Ys, Xs, TR = _G["Y"], _G["X"], _G["trials"]
    tr_c = [n for n in TR if c in Ys[n]]
    inputs = defaultdict(list)
    for n in tr_c:
        for k in Xs[n]:
            inputs[k].append(n)
    out, ycache = [], {}
    for k, tl in inputs.items():
        sig = tuple(tl)
        if sig not in ycache:
            y = np.concatenate([Ys[n][c] for n in tl]).astype(float)
            ok = np.isfinite(y)
            ycache[sig] = (ok, _rank(y[ok]) if ok.sum() >= MIN_ROWS else None)
        ok, ry = ycache[sig]
        nok = int(ok.sum())
        if ry is None or ry.std() == 0:
            out.append((c, k, len(tl), nok, np.nan))
            continue
        x = np.concatenate([Xs[n][k] for n in tl]).astype(float)[ok]
        if not np.isfinite(x).all() or x.std() == 0:
            out.append((c, k, len(tl), nok, np.nan))
            continue
        binary = np.isin(x, (0.0, 1.0)).all()
        out.append((c, k, len(tl), nok, _pearson(x if binary else _rank(x), ry)))
    return out


def _within_max(c, k):
    """max / median within-trial |Spearman| (aggregate) for one pair."""
    vals = []
    for n in _G["trials"]:
        if c not in _G["Y"][n] or k not in _G["X"][n]:
            continue
        y, x = _G["Y"][n][c].astype(float), _G["X"][n][k].astype(float)
        ok = np.isfinite(y) & np.isfinite(x)
        if ok.sum() < MIN_ROWS or np.std(y[ok]) == 0 or np.std(x[ok]) == 0:
            continue
        vals.append(abs(_pearson(_rank(x[ok]), _rank(y[ok]))))
    return (float(np.max(vals)), float(np.median(vals)), len(vals)) if vals else (np.nan, np.nan, 0)


def leakage(workers):
    from multiprocessing import get_context
    umask()
    LEAK.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    Y, X, CI = {}, {}, {}
    with get_context("fork").Pool(min(workers, 24)) as p:
        for n, y, ci, x in p.imap_unordered(_lload, ALL):
            Y[n], X[n] = y, x
            CI.update(ci)
    _G.update(Y=Y, X=X, trials=list(ALL))
    comps = sorted(CI)
    res = []
    with get_context("fork").Pool(min(workers, 24)) as p:
        for r in p.imap_unordered(_ptask, comps, chunksize=4):
            res.extend(r)
    PO = pd.DataFrame(res, columns=["component", "input", "n_trials", "n", "rho"])
    PO["item"] = PO.component.map(CI)
    PO["group"] = PO["item"].map(GROUP)
    PO["arho"] = PO.rho.abs()
    PO["n"] = PO["n"].astype(float).where(~PO["n"].between(1, 10), np.nan)
    # gate vs R2 r4_pooled: P5 inputs (S1) and the 5 v1.1 core columns (S3), same components, same algorithm
    R2 = pd.read_csv(R2POOL)
    g1 = PO[~PO.input.str.startswith("S3::")].merge(R2[R2.scenario == "S1"], on=["component", "input"], suffixes=("", "_r2"))
    s3 = PO[PO.input.str.startswith("S3::")].assign(input=lambda d: d.input.str[4:])
    g3 = s3.merge(R2[R2.scenario == "S3"], on=["component", "input"], suffixes=("", "_r2"))
    G = pd.concat([g1.assign(scenario="S1"), g3.assign(scenario="S3")])
    G["dev"] = (G.rho - G.rho_r2).abs()
    G["ntr_eq"] = G.n_trials == G.n_trials_r2
    G.groupby(["scenario", "input"]).agg(pairs=("dev", "size"), maxdev=("dev", "max"), n_trials_equal=("ntr_eq", "all")).reset_index().to_csv(
        LEAK / "gate_vs_r2.csv", index=False)
    PO = PO[~PO.input.str.startswith("S3::")].copy()
    PO.to_csv(LEAK / "pooled.csv", index=False)
    # item level: max |rho| over components x PS-10 inputs
    H = PO.dropna(subset=["arho"]).sort_values("arho", ascending=False)
    top = H.groupby("item").head(1).set_index("item")
    items = []
    for v in VN:
        if v in top.index:
            r = top.loc[v]
            items.append(dict(item=v, group=GROUP[v], max_abs_rho=r.arho, component=r.component, input=r.input, n_trials=r.n_trials,
                              masked=bool(r.arho >= RHO_MASK), soft=bool(RHO_SOFT <= r.arho < RHO_MASK)))
        else:
            items.append(dict(item=v, group=GROUP[v], max_abs_rho=np.nan, masked=False, soft=False))
    I = pd.DataFrame(items)
    I.to_csv(LEAK / "items.csv", index=False)
    SO = H[H.arho >= RHO_SOFT].copy()
    w = [_within_max(r.component, r.input) for r in SO.itertuples()]
    SO["within_max_abs_rho"], SO["within_median_abs_rho"], SO["within_k_trials"] = zip(*w) if w else ([], [], [])
    SO.to_csv(LEAK / "soft_pairs.csv", index=False)
    st = dict(when=time.strftime("%Y-%m-%d %H:%M"), secs=round(time.time() - t0), n_trials=len(ALL),
              n_pairs_estimable=int(PO.rho.notna().sum()), n_pairs_not_estimable=int(PO.rho.isna().sum()),
              masked_items=sorted(I[I.masked].item), soft_items=sorted(I[I.soft].item),
              gate_r2_maxdev=float(G.dev.max()), gate_r2_pairs=int(len(G)), gate_r2_n_trials_equal=bool(G.ntr_eq.all()),
              rule=f"item masked if pooled |rho| >= {RHO_MASK} for any component x PS-10 input; soft if >= {RHO_SOFT}")
    (LEAK / "leakage_status.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))


def ex58_ps10():
    st = json.loads((LEAK / "leakage_status.json").read_text())
    return set(st["masked_items"])


# ================================================================ 4. cells
def task(n):
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    t = T.t
    r = np.arange(len(t))
    X10, names, b5, hf = design(T, n)
    ex10 = _G["ex10"]
    rung = {"P5": (b5[r], set()), "PS10": (X10[r], ex10)}
    perm = T.shuffle_perm
    CLM = T.clm_pc
    assert CLM.shape == (len(t), 64) and np.isfinite(CLM).all()
    blk = {"ecg": T.ecg_pc, "she": T.ecg_pc[perm], "clm": CLM[r], "shc": CLM[perm][r]}
    comp = {"base": [], "ECG": ["ecg"], "CLMBR": ["clm"], "ECG+CLMBR": ["clm", "ecg"], "shufECG": ["she"], "shufCLMBR": ["shc"]}
    out = []

    def rec(rg, cfg, arm, X, ex58):  # = paper2_grid.task.rec
        est, psm = CONFIGS[cfg]
        try:
            o, fail = E.run_cell(T, X, rows=r, estimator=est, ps_model=psm, cstat=None), ""
        except IndexError as e:
            from v13_common import match, ps_logit
            lg = ps_logit(np.asarray(X, float), t, model=psm[0], C=psm[1] if psm[1] is not None else 1.0)
            if est[0] != "match" or len(match(lg, t, cal=est[1], ratio=est[2])[0]) > 0:
                raise
            o = dict(n=len(t), n_t=int(t.sum()), n_c=int((1 - t).sum()), n_pairs=0, loghr=np.nan, se=np.nan, ess_t=0.0, ess_c=0.0,
                     **{f"smd:{c}": np.nan for c in VN})
            fail = f"no matched pairs ({type(e).__name__})"
        small = min(o["n_t"], o["n_c"])
        out.append(dict(trial=n, key=KEY[n], idx=i, rung=rg, config=cfg, arm=arm, k_pcs=KPC[arm], rb=T.rb, rs=T.rs,
                        ex58=";".join(sorted(ex58)), p_ps=X.shape[1], cell_failed=fail,
                        **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c")},
                        retain=(o["n_pairs"] / small) if est[0] == "match" else np.nan,
                        **{f"smd:{c}": o[f"smd:{c}"] for c in VN}))

    for rg, (X, ex58) in rung.items():
        for cfg in CONFIGS:
            for a in ARMS:
                rec(rg, cfg, a, np.hstack([X] + [blk[b] for b in comp[a]]), ex58)
    print(f"{n} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, secs=round(time.time() - t0, 1), hf_column=hf, ps10_columns=names)


def run(workers):
    from multiprocessing import get_context
    umask()
    CEL.mkdir(parents=True, exist_ok=True)
    _G["ex10"] = ex58_ps10()
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle",
           "rewind", "cabana-v2", "transform-hf", "precision")
    tk = sorted(ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    with get_context("fork").Pool(min(workers, len(tk))) as p:
        res = p.map(task, tk, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    R[R.rung == "PS10"].reset_index(drop=True).to_parquet(CEL / "restricted_cells.parquet")
    R[R.rung == "P5"].reset_index(drop=True).to_parquet(CEL / "restricted_cells_P5gate.parquet")
    P2.suppress(R[R.rung == "PS10"].reset_index(drop=True)).to_csv(CEL / "cells.csv", index=False)
    (CEL / "log.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    (CEL / "run.done").write_text(time.strftime("%Y-%m-%d %H:%M") + "\n")
    print("done", flush=True)


def gate():
    """rebuilt P5 (through this script's code path) vs claude-v21-paper2 cells: every arm x config x trial, every column."""
    umask()
    R = pd.read_parquet(CEL / "restricted_cells_P5gate.parquet")
    G = pd.read_parquet(GRID)
    num = ["rb", "rs", "p_ps", "n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c", "retain"] + [f"smd:{c}" for c in VN]
    txt = ["key", "ex58", "cell_failed"]
    rows = []
    for cfg in CONFIGS:
        for a in ARMS:
            x = R[(R.config == cfg) & (R.arm == a)].set_index("trial").sort_index()
            y = G[(G.rung == "P5") & (G.config == cfg) & (G.arm == a)].set_index("trial").sort_index()
            assert x.index.equals(y.index), (cfg, a)
            for c in num:
                xa, ya = x[c].to_numpy(float), y[c].to_numpy(float)
                dd = np.abs(xa - ya)
                rows.append(dict(config=cfg, arm=a, col=c, n_trials=len(x), maxdev=float(np.nanmax(dd)) if np.isfinite(dd).any() else 0.0,
                                 nan_mismatch=int((np.isnan(xa) ^ np.isnan(ya)).sum())))
            for c in txt:
                rows.append(dict(config=cfg, arm=a, col=c, n_trials=len(x), maxdev=float((x[c].fillna("") != y[c].fillna("")).sum()),
                                 nan_mismatch=0))
    D = pd.DataFrame(rows)
    D.to_csv(CEL / "gate.csv", index=False)
    P = pd.read_parquet(CEL / "restricted_cells.parquet")
    st = dict(passed=bool(D.maxdev.max() == 0 and D.nan_mismatch.sum() == 0 and (D.n_trials == 38).all()),
              maxdev=float(D.maxdev.max()), nan_mismatch=int(D.nan_mismatch.sum()), cells=int(len(CONFIGS) * len(ARMS) * 38),
              values_compared=int(D[D.col.isin(num)].n_trials.sum()), reference=str(GRID),
              ps10_cells=int(len(P)), ps10_p_ps_base=sorted(set(P[P.arm == "base"].p_ps.astype(int))),
              ps10_ex58=sorted(set(P.ex58.fillna(""))), time=time.strftime("%Y-%m-%d %H:%M"))
    (CEL / "gate_status.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    return st


# ================================================================ 5. summaries
def mask_rung():
    hits = sorted(ex58_ps10())
    return {"P1": [], "P5": ["B_mean", "smd_prog_full"], "PS10": sorted(set(["B_mean", "smd_prog_full"] + hits)),
            "Flags": ["B_mean", "smd_prog_full"], "hdPS200": CODED4, "clinical": CODED4 + OBS9 + CLIN_NEAR}


MASK_ARM = {"CLMBR": CODED4, "ECG+CLMBR": CODED4, "shufCLMBR": CODED4}


def failed(g):
    return g.cell_failed.fillna("").astype(str).ne("") | (g.n_pairs.notna() & (g.n_pairs < MIN_PAIRS))


def cells_all():
    R = pd.read_parquet(CEL / "restricted_cells.parquet")
    G = pd.read_parquet(GRID)
    G = G[G.rung.isin(["P1", "P5", "hdPS200", "clinical"]) & G.arm.isin(ARMS)]
    return pd.concat([G, R], ignore_index=True)


def load_F(R, variant):
    """per (rung, config, arm): SP.per_trial (ex58 applied), F1 rule (< 11 pairs or failed fit = failed), variant masks."""
    MR = mask_rung()
    F, SM, RET, NF = {}, {}, {}, []
    for (rg, cfg, a), g in R.groupby(["rung", "config", "arm"]):
        g = g.set_index("trial", drop=False).loc[[t for t in ALL if t in set(g.trial)]]
        Fk, Sk = SP.per_trial(g)
        f = failed(g).to_numpy()
        if f.any():
            Sk.loc[f, :] = np.nan
            Fk.loc[f, ["lt01", "m58", "absd", "cons", "ea", "loghr", "se"]] = np.nan
            NF += [(rg, cfg, a, t) for t in g.trial[f]]
        if variant == "clean":
            m = set(MR[rg]) | set(MASK_ARM.get(a, []))
            Sk.loc[:, [c for c in Sk.columns if c in m]] = np.nan
        F[(rg, cfg, a)], SM[(rg, cfg, a)] = Fk, Sk
        RET[(rg, cfg, a)] = g.retain.mask(P2.small_pairs(g))
    return F, SM, RET, NF


WITHIN = (("ECG", "base", "one"), ("shufECG", "base", "two"), ("CLMBR", "base", "one"), ("ECG+CLMBR", "base", "one"),
          ("shufCLMBR", "base", "two"), ("ECG", "shufECG", "one"), ("CLMBR", "shufCLMBR", "one"), ("ECG+CLMBR", "CLMBR", "one"),
          ("ECG+CLMBR", "ECG", "one"), ("CLMBR", "ECG", "two"))


def contrasts():
    L = []
    for cfg in CONFIGS:
        for a, b, side in WITHIN:
            L.append((cfg, f"PS10: {a} vs {b}", "within", "PS10", a, "PS10", b, side))
        for rg in ("P1", "P5", "hdPS200", "clinical"):
            for a in ("ECG", "shufECG", "CLMBR", "ECG+CLMBR"):
                L.append((cfg, f"{rg}: {a} vs base", "ladder", rg, a, rg, "base", "one" if a != "shufECG" else "two"))
        L.append((cfg, "PS10 base vs P5 base", "base2base", "PS10", "base", "P5", "base", "two"))
        L.append((cfg, "PS10 base vs hdPS200 base", "base2base", "PS10", "base", "hdPS200", "base", "two"))
        L.append((cfg, "PS10+ECG vs hdPS200 base", "across", "PS10", "ECG", "hdPS200", "base", "two"))
        L.append((cfg, "PS10+CLMBR vs hdPS200 base", "across", "PS10", "CLMBR", "hdPS200", "base", "two"))
    return L


def _row(args):
    sname, c = args
    row, dom = P2._row((sname, c))
    cfg, lab, kind, ra, aa, rb, ab, side = c
    SM = P2._G["SM"]
    tr = P2._G["SETS"][sname]
    ka, kb = (ra, cfg, aa), (rb, cfg, ab)
    for pn, cols in (("54", NONCODED), ("58", VN)):
        a_, b_ = SM[ka].loc[tr, cols], SM[kb].loc[tr, cols]
        k = (a_.notna() & b_.notna()).sum(1)
        row[f"items{pn}_median"] = float(k[k > 0].median()) if (k > 0).any() else np.nan
        row[f"items{pn}_min"] = int(k[k > 0].min()) if (k > 0).any() else 0
    return row, dom


def levels(SM, variant):
    """unpaired levels: mean over trials of each trial's mean |SMD| on its own available items."""
    rows = []
    for sname, tr in (("S32", S32), ("S38", S38)):
        for (rg, cfg, a), S in SM.items():
            for pn, cols in (("58", VN), ("54", NONCODED)):
                X = S.loc[tr, cols]
                m = X.mean(1)
                p = 100 * (X < 0.1).sum(1) / X.notna().sum(1)
                rows.append(dict(variant=variant, set=sname, rung=rg, label=LABEL[rg], config=cfg, arm=a, panel=pn,
                                 k_trials=int(m.notna().sum()), mean_smd=float(m.mean()), pct_lt01=float(p.mean())))
    return rows


def summarize(workers):
    from multiprocessing import get_context
    umask()
    st = json.loads((CEL / "gate_status.json").read_text())
    if not st["passed"]:
        raise SystemExit("gate failed; not summarising")
    SUM.mkdir(parents=True, exist_ok=True)
    R = cells_all()
    S_all, D_all, L_all, nf_all = [], [], [], []
    for variant in ("v1", "clean"):
        t0 = time.time()
        F, SM, RET, NF = load_F(R, variant)
        nf_all += [dict(variant=variant, rung=a, config=b, arm=c, trial=d) for a, b, c, d in NF]
        P2._G.update(F=F, SM=SM, CL=V.cluster_of(), RET=RET, SETS={"S32": S32, "S38": S38})
        jobs = [(s, c) for s in ("S38", "S32") for c in contrasts()]
        with get_context("fork").Pool(min(workers, len(jobs))) as p:
            res = p.map(_row, jobs, chunksize=1)
        S = pd.DataFrame([r for r, _ in res])
        D = pd.DataFrame([d for _, ds in res for d in ds])
        S.insert(0, "variant", variant)
        D.insert(0, "variant", variant)
        for sname in ("S32", "S38"):  # BH within set over the PS-10 within-rung contrasts (all configs), paper2 balance family
            ms = (S.set == sname) & S.kind.eq("within")
            long = S.loc[ms, P2.BAL_FAM].stack(dropna=True)
            q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
            for c in P2.BAL_FAM:
                S.loc[ms, f"q_{c}_ps10_fam"] = q[c]
        S_all.append(S)
        D_all.append(D)
        L_all += levels(SM, variant)
        print(variant, len(S), f"{time.time() - t0:.0f}s", flush=True)
    pd.concat(S_all, ignore_index=True).to_csv(SUM / "contrasts.csv", index=False)
    pd.concat(D_all, ignore_index=True).to_csv(SUM / "domains.csv", index=False)
    pd.DataFrame(L_all).to_csv(SUM / "levels.csv", index=False)
    NFd = pd.DataFrame(nf_all)
    NFd = NFd[NFd.variant == "v1"].drop(columns="variant")
    NFd.groupby(["rung", "config", "arm"]).size().rename("n_trials_failed").reset_index().to_csv(SUM / "failed_cells.csv", index=False)
    tables()
    print("summaries written", flush=True)


# ================================================================ 6. tables (markdown, aggregates)
def f1(x, d=1):
    return "" if pd.isna(x) else f"{x:.{d}f}"


def fp(x):
    return "" if pd.isna(x) else (f"{x:.3f}" if x >= 0.001 else "<.001")


def tables():
    S = pd.read_csv(SUM / "contrasts.csv")
    D = pd.read_csv(SUM / "domains.csv")
    L = ["# PS-10 tables (generated by scripts/v1_ps10/ps10.py tables; source summary/contrasts.csv, domains.csv)\n"]
    for variant in ("v1", "clean"):
        for sname in ("S32", "S38"):
            q = S[(S.variant == variant) & (S.set == sname)]
            L.append(f"\n## {variant} masks, {sname}: PS-10 arms vs base (all configs)\n")
            L.append("| config | contrast | m58 base | m58 arm | rel. red. 58 (95% CI) | P58 | m54 base | m54 arm | rel. red. 54 (95% CI) | "
                     "better 54 | P54 | q54 | %<0.1 54 base→arm | P %<0.1 | absd base→arm | closer | P absd | P bench-perm |")
            L.append("|" + "---|" * 18)
            for _, r in q[q.kind == "within"].iterrows():
                L.append(f"| {r.config} | {r.contrast} | {f1(r.m58_b, 3)} | {f1(r.m58_a, 3)} | {f1(r.relred58)} ({f1(r.relred58_lo)} to {f1(r.relred58_hi)}) | "
                         f"{fp(r.m58_p)} | {f1(r.m54_b, 3)} | {f1(r.m54_a, 3)} | {f1(r.relred54)} ({f1(r.relred54_lo)} to {f1(r.relred54_hi)}) | "
                         f"{r.m54_better} | {fp(r.m54_p)} | {fp(r.q_m54_p_ps10_fam)} | {f1(r.lt01_54_b)}→{f1(r.lt01_54_a)} | {fp(r.lt01_54_p)} | "
                         f"{f1(r.absd_b, 3)}→{f1(r.absd_a, 3)} | {r.absd_better} | {fp(r.absd_p)} | {fp(r.bshuf_p)} |")
            L.append(f"\n## {variant} masks, {sname}: ladder and base-to-base\n")
            L.append("| config | contrast | m58 b | m58 a | rel. red. 58 (95% CI) | P58 | m54 b | m54 a | rel. red. 54 (95% CI) | better 54 | P54 | "
                     "absd b→a | P absd |")
            L.append("|" + "---|" * 13)
            for _, r in q[q.kind != "within"].iterrows():
                L.append(f"| {r.config} | {r.contrast} | {f1(r.m58_b, 3)} | {f1(r.m58_a, 3)} | {f1(r.relred58)} ({f1(r.relred58_lo)} to {f1(r.relred58_hi)}) | "
                         f"{fp(r.m58_p)} | {f1(r.m54_b, 3)} | {f1(r.m54_a, 3)} | {f1(r.relred54)} ({f1(r.relred54_lo)} to {f1(r.relred54_hi)}) | "
                         f"{r.m54_better} | {fp(r.m54_p)} | {f1(r.absd_b, 3)}→{f1(r.absd_a, 3)} | {fp(r.absd_p)} |")
            d = D[(D.variant == variant) & (D.set == sname) & (D.config == "main") & D.contrast.str.startswith("PS10: ") &
                  D.contrast.str.endswith("vs base")]
            L.append(f"\n## {variant} masks, {sname}, main: PS-10 per-domain relative reduction (P one-sided; two-sided for placebos)\n")
            L.append("| contrast | domain | items | mean base | mean arm | rel. red. (95% CI) | better | P |")
            L.append("|---|---|---|---|---|---|---|---|")
            for _, r in d.iterrows():
                L.append(f"| {r.contrast} | {r.domain} | {r.n_items} | {f1(r.mean_b, 3)} | {f1(r.mean_a, 3)} | {f1(r.relred)} ({f1(r.relred_lo)} to "
                         f"{f1(r.relred_hi)}) | {r.better} | {fp(r.p)} |")
    (SUM / "tables.md").write_text("\n".join(L) + "\n")


# ================================================================ 7. privacy
def privacy():
    bad = []
    for f in sorted(OUT.rglob("*.csv")):
        D = pd.read_csv(f, low_memory=False)
        for c in ("n", "n_t", "n_c", "n_pairs", "n_roster"):
            if c in D:
                v = pd.to_numeric(D[c], errors="coerce")
                k = int(((v >= 1) & (v < MIN_PAIRS)).sum())
                if k:
                    bad.append((str(f.relative_to(OUT)), c, k))
        if "n_pairs" in D and "suppressed_lt11" in D:
            s = D.suppressed_lt11.astype(bool)
            for c in P2.DERIVED:
                if c in D and D.loc[s, c].notna().any():
                    bad.append((str(f.relative_to(OUT)), c, int(D.loc[s, c].notna().sum())))
    out = dict(clean=not bad, issues=bad, time=time.strftime("%Y-%m-%d %H:%M"))
    (OUT / "privacy_scan.json").write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["extract", "designlog", "leakage", "run", "gate", "summarize", "tables", "privacy"])
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    w = min(a.workers, 24)
    {"extract": extract, "designlog": lambda: designlog(w), "leakage": lambda: leakage(w), "run": lambda: run(w), "gate": gate,
     "summarize": lambda: summarize(w), "tables": tables, "privacy": privacy}[a.cmd]()
