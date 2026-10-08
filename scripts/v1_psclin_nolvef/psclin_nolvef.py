#!/usr/bin/env python
"""PS-Clinical without LVEF (user decision 2026-10-08): no propensity score uses an echocardiographic measurement, so all
35 echo items and the observed-LVEF item are held out for every PS. Doc: docs/v1_psclin_nolvef/PS_CLINICAL_NO_LVEF.md.

Version 1 code is imported unchanged: scripts/v21/paper2_grid.py (P2; its rec / contrast / _row machinery) and
scripts/v20/sens_primary32.py (SP); scripts/build_core_baseline.impute (the baseline imputation); v16_engine.run_cell.

Rungs (PS design, full cohort rows r = arange(n), exactly as paper2_grid.task):
  clinical              T.X_core (with LVEF; gate rung, must equal claude-v21-paper2/core cells exactly)
  clinical_nolvef       PRIMARY: core covariates minus lvef, RE-IMPUTED without LVEF (build_core_baseline.impute, same seed
                        20260923, same settings, imputation 1, lvef column dropped from the imputation model)
  clinical_nolvef_drop  SENSITIVITY: lvef column dropped from the existing completed table (other covariates imputed with
                        LVEF as a predictor)
Arms: base, ECG, CLMBR, ECG+CLMBR, shufECG, shufCLMBR x configs main, cal01, m13, iptw, overlap, gbm (+ CLMBR32, main only),
L2 C = 1 (sens_primary32.CONFIGS), E.run_cell(..., cstat=None).

Masks (a cell's mask = rung mask | arm mask; placebos take the real arm's mask; DEFECT_IMPACT.md section 1):
  'v1'    (paper 1 / paper 2 style; = the cells' ex58): PS inputs only. clinical: mean_meds, mean_util, smd_obs_<9 phys>;
          clinical_nolvef*: mean_meds, mean_util, smd_obs_<8 phys other than lvef>.
  'clean' (PRIMARY for this rung; DEFECT_IMPACT 'clean' rules): clinical: CODED4 + OBS9 + eGFR, echo EF, LV systolic grade;
          clinical_nolvef*: CODED4 + OBS8 + eGFR (echo EF, LV systolic grade and observed LVEF are no longer masked);
          P1 none; P5 / Flags: B_mean, prognostic score; hdPS200: CODED4; CLMBR arms (real, permuted, 32-PC): CODED4.
F1 rule: a cell with < 11 matched pairs (or a failed fit) is treated as failed: all items and log HR missing.

Usage:
  psclin_nolvef.py impute [--workers 12]   -> OUT/imputation/ (restricted re-imputed tables; repro + change aggregates)
  psclin_nolvef.py run [--workers 24]      -> OUT/cells/restricted_cells.parquet, cells.csv (suppressed), log.json
  psclin_nolvef.py gate                    -> OUT/cells/gate.csv, gate_status.json
  psclin_nolvef.py summarize [--workers 24]-> OUT/summary/*.csv (aggregates)
Aggregates only; OUT umask 077; counts 1-10 suppressed in every csv.
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
for p in ("v21", "v20", "v18", ""):
    sys.path.insert(0, str(HERE.parent / p) if p else str(HERE.parent))
import paper2_grid as P2  # noqa: E402

SP, E, V, C, AF = P2.SP, P2.E, P2.V, P2.C, P2.AF
A = SP.A
OUT = A / "claude-v1-psclin-nolvef"
IMP, CEL, SUM = OUT / "imputation", OUT / "cells", OUT / "summary"
GRID = P2.OUT / "restricted_cells.parquet"
ALL, KEY, VN, GROUP, NONCODED = P2.ALL, P2.KEY, P2.VN, P2.GROUP, P2.NONCODED
CONFIGS, S32, S38 = P2.CONFIGS, P2.S32, P2.S38
ARMS = P2.ARMS
KPC = P2.KPC
NEW = ["clinical", "clinical_nolvef", "clinical_nolvef_drop"]
PHYS9 = ("lvef", "sbp", "dbp", "heart_rate", "bmi", "creatinine", "potassium", "sodium", "hemoglobin")
CODED4 = ["mean_meds", "mean_util", "B_mean", "smd_prog_full"]
OBS9 = [f"smd_obs_{c}" for c in PHYS9]
OBS8 = [c for c in OBS9 if c != "smd_obs_lvef"]
CLIN_NEAR = ["pp_LAB__egfr", "pp_LVFUNC__ef", "pp_LVFUNC__lv_sys_grade"]
LVEF_ITEMS = ["smd_obs_lvef", "pp_LVFUNC__ef", "pp_LVFUNC__lv_sys_grade"]  # LVEF-derived; held out only without LVEF
ECHO = [c for c in VN if GROUP[c].startswith("Echo:")]
assert len(ECHO) == 35
MASK_RUNG = {"P1": [], "P5": ["B_mean", "smd_prog_full"], "Flags": ["B_mean", "smd_prog_full"], "hdPS200": CODED4,
             "clinical": CODED4 + OBS9 + CLIN_NEAR, "clinical_nolvef": CODED4 + OBS8 + ["pp_LAB__egfr"],
             "clinical_nolvef_drop": CODED4 + OBS8 + ["pp_LAB__egfr"]}
MASK_ARM = {"CLMBR": CODED4, "ECG+CLMBR": CODED4, "shufCLMBR": CODED4, "CLMBR32": CODED4}
MIN_PAIRS = SP.MIN_CELL  # 11
SEED_IMP = 20260923
LABEL = {"P1": "PS-Demo", "P5": "PS-CVD5", "Flags": "PS-Flags", "hdPS200": "hdPS", "clinical": "PS-Clinical (with LVEF, v1)",
         "clinical_nolvef": "PS-Clinical (no LVEF)", "clinical_nolvef_drop": "PS-Clinical (no LVEF, column dropped)"}


def umask():
    os.umask(0o077)


# ================================================================ 2. imputation
def imp_path(n):
    return IMP / f"restricted_completed_nolvef_01_{n}.parquet"


def _imp_task(n):
    from build_core_baseline import impute
    t0 = time.time()
    B = A / f"claude-{n}-baseline-v11"
    obs = pd.read_parquet(B / "restricted_baseline_observed.parquet").set_index("patient_key")
    tr = obs.pop("treated").to_numpy()
    ref = pd.read_parquet(B / "restricted_completed_01.parquet").set_index("patient_key")
    tr_ref = ref.pop("treated").to_numpy()
    assert ref.index.equals(obs.index) and list(ref.columns) == list(obs.columns) and (tr_ref == tr).all()
    # (a) reproduce the existing completed table (with LVEF): validates code, seed and library versions
    Z1 = impute(obs, tr, 1)[0]
    D = Z1.to_numpy(float) - ref.to_numpy(float)
    repro = float(np.nanmax(np.abs(D))) if np.isfinite(D).any() else 0.0
    nan_mis = int((np.isnan(Z1.to_numpy(float)) ^ np.isnan(ref.to_numpy(float))).sum())
    # (b) re-impute without LVEF: lvef removed from the data before IterativeImputer (neither target nor predictor)
    Z0 = impute(obs.drop(columns=["lvef"]), tr, 1)[0]
    out = Z0.copy()
    out.insert(0, "treated", tr)
    out.reset_index().to_parquet(imp_path(n))
    # aggregates: how much the other imputed values moved (standardised by the observed SD), per covariate
    miss = [c for c in obs.columns if obs[c].isna().any()]
    chg = {}
    for c in miss:
        if c == "lvef":
            continue
        m = obs[c].isna().to_numpy()
        sd = float(obs[c].std())
        d = np.abs(Z0[c].to_numpy(float)[m] - ref[c].to_numpy(float)[m])
        chg[c] = dict(miss_frac=round(float(m.mean()), 3), mean_abs_change_sd=round(float(d.mean() / sd), 4) if sd > 0 else None,
                      frac_changed=round(float((d > 1e-12).mean()), 3))
    obs_eq = bool(np.allclose(Z0[[c for c in obs.columns if c != "lvef"]].where(obs.drop(columns="lvef").notna()).fillna(-9e9),
                              obs.drop(columns="lvef").fillna(-9e9)))
    print(f"impute {n} repro {repro:g} {time.time() - t0:.0f}s", flush=True)
    return dict(trial=n, repro_maxdev_with_lvef=repro, repro_nan_mismatch=nan_mis, observed_preserved=obs_eq,
                lvef_miss_frac=round(float(obs["lvef"].isna().mean()), 3), cols_with_missing=";".join(miss),
                secs=round(time.time() - t0, 1), change=chg)


def impute_all(workers):
    from multiprocessing import Pool
    umask()
    IMP.mkdir(parents=True, exist_ok=True)
    with Pool(min(workers, len(ALL))) as p:
        res = p.map(_imp_task, ALL, chunksize=1)
    (IMP / "imputation_log.json").write_text(json.dumps(res, indent=1))
    rows = [dict(trial=r["trial"], covariate=c, **v) for r in res for c, v in r["change"].items()]
    pd.DataFrame(rows).to_csv(IMP / "imputation_change.csv", index=False)
    S = pd.DataFrame([{k: v for k, v in r.items() if k != "change"} for r in res])
    S.to_csv(IMP / "imputation_summary.csv", index=False)
    st = dict(trials=len(res), repro_maxdev=float(S.repro_maxdev_with_lvef.max()), repro_nan_mismatch=int(S.repro_nan_mismatch.sum()),
              observed_preserved_all=bool(S.observed_preserved.all()), secs_total=float(S.secs.sum()), seed=SEED_IMP,
              method="build_core_baseline.impute(obs without lvef, treated, m=1): IterativeImputer(sample_posterior=True, "
                     "max_iter=10, random_state=20260923, skip_complete=True), all other covariates + treatment as predictors")
    (IMP / "imputation_status.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))


# ================================================================ 1/3. cells
def task(n):
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    t = T.t
    r = np.arange(len(t))
    assert "lvef" in T.cov.columns and "lvef" in T.phys
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    nl_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys if c != "lvef"}
    cols_nl = [c for c in T.cov.columns if c != "lvef"]
    Xdrop = T.cov[cols_nl].to_numpy()
    Z = pd.read_parquet(imp_path(n)).set_index("patient_key")
    Xre = Z.loc[T.keys, cols_nl].astype(float).to_numpy()
    # sanity: non-imputed columns identical; the held-out matrix uses the completed meds / util (no missing values)
    ok_obs = ~np.isnan(pd.read_parquet(A / f"claude-{n}-baseline-v11" / "restricted_baseline_observed.parquet")
                       .set_index("patient_key").loc[T.keys, cols_nl].to_numpy(float))
    assert np.array_equal(Xre[ok_obs], Xdrop[ok_obs])
    for c in T.meds + T.util:
        assert np.array_equal(Z.loc[T.keys, c].to_numpy(float), T.cov[c].to_numpy(float)), c
    rung = {"clinical": (T.X_core[r], clin_ex), "clinical_nolvef": (Xre[r], nl_ex), "clinical_nolvef_drop": (Xdrop[r], nl_ex)}
    perm = T.shuffle_perm
    CLM = T.clm_pc
    assert CLM.shape == (len(t), 64) and np.isfinite(CLM).all()
    blk = {"ecg": T.ecg_pc, "she": T.ecg_pc[perm], "clm": CLM[r], "shc": CLM[perm][r], "c32": CLM[:, :32]}
    comp = {"base": [], "ECG": ["ecg"], "CLMBR": ["clm"], "ECG+CLMBR": ["clm", "ecg"], "shufECG": ["she"],
            "shufCLMBR": ["shc"], "CLMBR32": ["c32"]}
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
        rec(rg, "main", "CLMBR32", np.hstack([X, blk["c32"]]), ex58)
    print(f"{n} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, secs=round(time.time() - t0, 1), p_core=int(T.X_core.shape[1]), p_nolvef=len(cols_nl))


def run(workers):
    from multiprocessing import Pool
    umask()
    CEL.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle",
           "rewind", "cabana-v2", "transform-hf", "precision")
    tk = sorted(ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    with Pool(min(workers, len(tk))) as p:
        res = p.map(task, tk, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    R.to_parquet(CEL / "restricted_cells.parquet")
    P2.suppress(R).to_csv(CEL / "cells.csv", index=False)
    (CEL / "log.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    (CEL / "run.done").write_text(time.strftime("%Y-%m-%d %H:%M") + "\n")
    print("done", flush=True)


def gate():
    """clinical rung (with LVEF) vs paper2 grid cells: every arm x config x trial, every stored column; exact."""
    umask()
    R = pd.read_parquet(CEL / "restricted_cells.parquet")
    G = pd.read_parquet(GRID)
    num = ["rb", "rs", "p_ps", "n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c", "retain"] + [f"smd:{c}" for c in VN]
    txt = ["key", "ex58", "cell_failed"]
    rows = []
    for cfg in CONFIGS:
        for a in ARMS:
            x = R[(R.rung == "clinical") & (R.config == cfg) & (R.arm == a)].set_index("trial").sort_index()
            y = G[(G.rung == "clinical") & (G.config == cfg) & (G.arm == a)].set_index("trial").sort_index()
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
    st = dict(passed=bool(D.maxdev.max() == 0 and D.nan_mismatch.sum() == 0 and (D.n_trials == 38).all()),
              maxdev=float(D.maxdev.max()), nan_mismatch=int(D.nan_mismatch.sum()), cells=int(len(CONFIGS) * len(ARMS) * 38),
              values_compared=int(D[D.col.isin(num)].n_trials.sum()), arms=ARMS, configs=list(CONFIGS),
              reference=str(GRID), time=time.strftime("%Y-%m-%d %H:%M"))
    (CEL / "gate_status.json").write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    return st


# ================================================================ 4. summaries
def failed(g):
    return g.cell_failed.fillna("").astype(str).ne("") | (g.n_pairs.notna() & (g.n_pairs < MIN_PAIRS))


def cells_all():
    R = pd.read_parquet(CEL / "restricted_cells.parquet")
    G = pd.read_parquet(GRID)
    G = G[G.rung.isin(["P1", "P5", "Flags", "hdPS200"])]
    return pd.concat([G, R], ignore_index=True)


def load_F(R, variant):
    """per (rung, config, arm): SP.per_trial endpoints and |SMD| (ex58 applied), F1 rule, then the variant's extra masks."""
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
            m = set(MASK_RUNG[rg]) | set(MASK_ARM.get(a, []))
            Sk.loc[:, [c for c in Sk.columns if c in m]] = np.nan
        F[(rg, cfg, a)], SM[(rg, cfg, a)] = Fk, Sk
        RET[(rg, cfg, a)] = g.retain.mask(P2.small_pairs(g))
    return F, SM, RET, NF


NL = ("clinical_nolvef", "clinical_nolvef_drop")
WITHIN = (("ECG", "base", "one"), ("CLMBR", "base", "one"), ("ECG+CLMBR", "base", "one"), ("ECG+CLMBR", "CLMBR", "one"),
          ("ECG+CLMBR", "ECG", "one"), ("CLMBR", "ECG", "two"), ("shufECG", "base", "two"), ("shufCLMBR", "base", "two"),
          ("ECG", "shufECG", "one"), ("CLMBR", "shufCLMBR", "one"))


def contrasts():
    L = []
    for cfg in CONFIGS:
        for rg in NL + ("clinical",):
            for a, b, side in WITHIN:
                L.append((cfg, f"{rg}: {a} vs {b}", "within", rg, a, rg, b, side))
        for rg in ("P1", "P5", "hdPS200", "Flags"):
            for a in ("ECG", "CLMBR", "ECG+CLMBR", "shufECG"):
                L.append((cfg, f"{rg}: {a} vs base", "ladder", rg, a, rg, "base", "one" if a != "shufECG" else "two"))
        for nl in NL:
            L.append((cfg, f"clinical base vs {nl} base", "lvef", "clinical", "base", nl, "base", "two"))
            L.append((cfg, f"{nl} ECG vs clinical base", "lvef", nl, "ECG", "clinical", "base", "two"))
            L.append((cfg, f"clinical ECG vs {nl} ECG", "lvef", "clinical", "ECG", nl, "ECG", "two"))
        for ra, aa in (("P5", "CLMBR"), ("P5", "ECG+CLMBR"), ("P5", "ECG"), ("hdPS200", "base")):
            L.append((cfg, f"{ra}+{aa} vs clinical_nolvef base", "across", ra, aa, "clinical_nolvef", "base", "two"))
        L.append((cfg, "clinical_nolvef base vs P5 base", "across", "clinical_nolvef", "base", "P5", "base", "one"))
        L.append((cfg, "clinical_nolvef base vs hdPS200 base", "across", "clinical_nolvef", "base", "hdPS200", "base", "two"))
    for rg in NL + ("clinical",):
        for a, b, side in (("CLMBR32", "base", "one"), ("CLMBR32", "ECG", "two"), ("CLMBR", "CLMBR32", "two")):
            L.append(("main", f"{rg}: {a} vs {b}", "clmbr32", rg, a, rg, b, side))
    return L


EXTRA_DOM = {"Echo, all 35 items": ECHO, "LVEF-derived (3 items)": LVEF_ITEMS, "item: observed LVEF": ["smd_obs_lvef"],
             "item: echo EF": ["pp_LVFUNC__ef"], "item: LV systolic grade": ["pp_LVFUNC__lv_sys_grade"]}


def _row(args):
    sname, c = args
    row, dom = P2._row((sname, c))
    cfg, lab, kind, ra, aa, rb, ab, side = c
    F, SM, CL = P2._G["F"], P2._G["SM"], P2._G["CL"]
    tr = P2._G["SETS"][sname]
    ka, kb = (ra, cfg, aa), (rb, cfg, ab)
    for g, cols in EXTRA_DOM.items():
        d = P2.bal_light(F[ka], F[kb], P2.mask(SM[ka], cols), P2.mask(SM[kb], cols), tr, side, CL, full=False)
        dom.append(dict(set=sname, config=cfg, contrast=lab, kind=kind, sided=side, domain=g, n_items=len(cols),
                        mean_a=d["m58_a"], mean_b=d["m58_b"], better=d["m58_better"], p=d["m58_p"],
                        lt01_a=d["lt01_a"], lt01_b=d["lt01_b"], lt01_p=d["lt01_p"],
                        relred=d["relred"], relred_lo=d["relred_lo"], relred_hi=d["relred_hi"], k=d["relred_k"]))
    # items paired (non-masked, observed in both arms): median over trials, 54 and 58 panels
    for pn, cols in (("54", NONCODED), ("58", VN)):
        a_, b_ = SM[ka].loc[tr, cols], SM[kb].loc[tr, cols]
        k = (a_.notna() & b_.notna()).sum(1)
        row[f"items{pn}_median"] = float(k[k > 0].median()) if (k > 0).any() else np.nan
        row[f"items{pn}_max"] = int(k.max())
    return row, dom


def ladder(F, SM, variant):
    """unpaired levels (explorer 'levels'): mean over trials of each trial's mean |SMD| on its own observed items."""
    common = [c for c in VN if c not in set(MASK_RUNG["clinical_nolvef"])]  # = 45 items, held out for every ladder rung
    rows = []
    for sname, tr in (("S32", S32), ("S38", S38)):
        for (rg, cfg, a), S in SM.items():
            for pn, cols in (("58", VN), ("54", NONCODED), ("common45", common), ("echo35", ECHO)):
                X = S.loc[tr, cols]
                m = X.mean(1)
                p = 100 * (X < 0.1).sum(1) / X.notna().sum(1)
                rows.append(dict(variant=variant, set=sname, rung=rg, label=LABEL[rg], config=cfg, arm=a, panel=pn,
                                 k_trials=int(m.notna().sum()), mean_smd=float(m.mean()), pct_lt01=float(p.mean()),
                                 items_median=float(X.notna().sum(1)[m.notna()].median()) if m.notna().any() else np.nan))
    return rows


def summarize(workers):
    from multiprocessing import Pool
    umask()
    st = json.loads((CEL / "gate_status.json").read_text())
    if not st["passed"]:
        raise SystemExit("gate failed; not summarising")
    SUM.mkdir(parents=True, exist_ok=True)
    R = cells_all()
    S_all, D_all, L_all, nf_all = [], [], [], []
    for variant in ("clean", "v1"):
        t0 = time.time()
        F, SM, RET, NF = load_F(R, variant)
        nf_all += [dict(variant=variant, rung=a, config=b, arm=c, trial=d) for a, b, c, d in NF]
        P2._G.update(F=F, SM=SM, CL=V.cluster_of(), RET=RET, SETS={"S32": S32, "S38": S38})
        jobs = [(s, c) for s in ("S38", "S32") for c in contrasts()]
        with Pool(min(workers, len(jobs))) as p:
            res = p.map(_row, jobs, chunksize=1)
        S = pd.DataFrame([r for r, _ in res])
        D = pd.DataFrame([d for _, ds in res for d in ds])
        S.insert(0, "variant", variant)
        D.insert(0, "variant", variant)
        # BH-FDR within set over the within-rung contrasts of the primary rung (all configs), balance family as paper2
        for sname in ("S32", "S38"):
            ms = (S.set == sname) & S.rung_a.eq("clinical_nolvef") & S.kind.eq("within")
            long = S.loc[ms, P2.BAL_FAM].stack(dropna=True)
            q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
            for c in P2.BAL_FAM:
                S.loc[ms, f"q_{c}_nolvef_fam"] = q[c]
        S_all.append(S)
        D_all.append(D)
        L_all += ladder(F, SM, variant)
        print(variant, len(S), f"{time.time() - t0:.0f}s", flush=True)
    S = pd.concat(S_all, ignore_index=True)
    S.to_csv(SUM / "contrasts.csv", index=False)
    pd.concat(D_all, ignore_index=True).to_csv(SUM / "domains.csv", index=False)
    pd.DataFrame(L_all).to_csv(SUM / "ladder.csv", index=False)
    NFd = pd.DataFrame(nf_all)
    NFd = NFd[NFd.variant == "clean"].drop(columns="variant")
    NFd.groupby(["rung", "config", "arm"]).size().rename("n_trials_failed").reset_index().to_csv(SUM / "failed_cells.csv", index=False)
    print("summaries written", flush=True)


def privacy():
    """scan every csv / json written under OUT (non-restricted) for counts 1-10 in count columns."""
    bad = []
    for f in sorted(OUT.rglob("*.csv")):
        D = pd.read_csv(f, low_memory=False)
        for c in ("n", "n_t", "n_c", "n_pairs"):
            if c in D:
                v = pd.to_numeric(D[c], errors="coerce")
                k = int(((v >= 1) & (v < MIN_PAIRS)).sum())
                if k:
                    bad.append((str(f.relative_to(OUT)), c, k))
        if "n_pairs" in D and "suppressed_lt11" in D:
            sup = D.suppressed_lt11.astype(bool)
            for c in P2.DERIVED:
                if c in D and D.loc[sup, c].notna().any():
                    bad.append((str(f.relative_to(OUT)), c, int(D.loc[sup, c].notna().sum())))
    out = dict(clean=not bad, issues=bad, time=time.strftime("%Y-%m-%d %H:%M"))
    (OUT / "privacy_scan.json").write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["impute", "run", "gate", "summarize", "privacy"])
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    w = min(a.workers, 24)
    {"impute": lambda: impute_all(min(w, 12)), "run": lambda: run(w), "gate": gate, "summarize": lambda: summarize(w),
     "privacy": privacy}[a.cmd]()
