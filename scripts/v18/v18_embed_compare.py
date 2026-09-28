#!/usr/bin/env python
"""v1.8 consolidated embedding comparison (exploratory; PI request 2026-09-28): ECG vs CLMBR-T vs both, across the
full PS ladder, in all 38 trials (the v1.6 18 + the v1.7 15 + the v1.8 AF 5).

Code path (imported, unchanged): scripts/v18/v18_af_confirm.py (trial list V.ALL = 18 + 15 + 5 in that order, so the
halves seed is 16060 + i, i = index in that list; V18 covariate paths) -> scripts/v17/v17_confirm.py (xpanel, xsmd,
halves, matched-sample capture S8._LAST) -> scripts/v16/v16_engine.py (load_trial, run_cell with
estimator ("match", 0.2, 1), PS L2 C = 1).  v18_clmbr.designs builds P5 / P2.

Ladder (PS base design; rows = the half's rows):
  P1       T.demo (age, sex, index year)                                           = v1.7 P1 / v18_clmbr P1
  P5       P1 + hypertension_v11, t2d, cad_ihd, atrial_fibrillation, HF            = s11_p5 / v18_clmbr P5
  P2       P5 + obesity                                                            = v1.7 P2 / v18_clmbr P2
  sparse   T.X_dx (= T.arms(["sparse"]))                                          = S1 r5_sparse
  hdPS200  T.X_dx + T.hd(200, t, rows) (ranked on the half's treatment)           = S1 r7_hdPS200
  clinical T.X_core                                                                = S1 r8_clinical
Arms per rung: base | +ECG32 (T.ecg_pc) | +CLMBR64 (T.clm_pc) | +CLMBR64+ECG32 | +shufECG32 (T.ecg_pc[T.shuffle_perm]) |
  +shufCLMBR64 (T.clm_pc[T.shuffle_perm]) | +noise96 (N(0,1), 96 dims, np.random.default_rng(960000 + i), drawn for all
  rows then subset; dimension-matched placebo of the combined arm); unmatched once per half.

Balance endpoints (matched sample; held-out = not in the rung's PS):
  nc_lt01   % of the NON-CODED 58-panel variables (groups Vitals & core labs, Other labs, Echo:*) with |SMD| < 0.1
            -> PRIMARY balance endpoint of this comparison (CLMBR sees codes, so coded-record variables are not
            held out for it).  At `clinical` the observed vitals/labs of T.phys (and meds / util) are in the PS and
            are removed from every 58-panel endpoint (S1 / S6 clin_ex rule).
  lt01      same on the full 58-panel;  nc_mean / m58_mean = mean |SMD| (lower = better)
  lv_lt01   covars2b non-proximal panel, dictionary domain lab_vital (v18_clmbr (iii)); per-rung PS exclusions
            (S6.excluded_extra + S8.composite_overlap with the rung's PS names: P-rungs as v18_clmbr, sparse / hdPS200
            T.demo + T.dxc, clinical T.core; hdPS200 also drops variables whose hdPS keys overlap the half's
            top-200 hdPS codes, S6.hdps_selected / hdps_overlap = S6 v2b); lvv_lt01 = values only.
Emulation: absd = |loghr - rb|, z2 = (loghr - rb)^2 / (se^2 + rs^2), cons = 100 * (|z| < 1.96).
Retention: retain = n_pairs / smaller-arm size of the analysed rows.
Common support (full cohort): for arm a in {ECG, CLMBR, CLMBR+ECG, noise96} and each rung, the anchors (smaller-arm
  patients) matched under BOTH base and a; balance of both arms' pairs restricted to those anchors (round 3/4 audit).

Statistics (summarize): paired across trials, d oriented so that > 0 = a better; exact sign-flip (v17_confirm.signflip_1s;
  one-sided H1 a better, two-sided for ECG vs CLMBR and for placebo vs base); comparator-cluster sign-flip
  (docs/v17/trial_selection.json clusters), LOO max p, halves A / B; benchmark shuffle for absd / z2: per draw the k
  trials receive k RCT benchmarks drawn jointly as (rb, rs) pairs without replacement, 20,000 draws,
  np.random.default_rng(0), from (i) the set's own k trials (within-set permutation) and (ii) all 38 RCTs;
  p = P(null <= obs) (two-sided: 2 * min tail).  BH-FDR within endpoint family (balance-primary nc_lt01;
  balance-secondary lt01 / lv_lt01 / lvv_lt01 / nc_mean / m58_mean; emulation absd / z2 / cons; trial-specific =
  benchmark-shuffle p; retention) over every set x rung x contrast cell.
  Status: "prespecified (v1.8 Plan B)" = set all33, rungs P1 / P5 / P2, Plan B key contrasts; all else exploratory.

Usage:
  v18_embed_compare.py run [--trials a,b] [--workers 32]  -> OUT/results.csv, OUT/common_support.csv, OUT/log.json
  v18_embed_compare.py verify     reuse check vs claude-v18-clmbr/results_all.csv (33 trials, P1/P5/P2),
                                  claude-v18-af-confirm/results_af5.csv (AF 5, P1/P5), claude-v16-s1-ladder/results.csv
                                  (v1.6 18, sparse / hdPS200 / clinical) -> OUT/verify.csv (max deviation must be 0)
  v18_embed_compare.py summarize  -> OUT/summary.csv, OUT/common_summary.csv, OUT/retention.csv
  v18_embed_compare.py tables     -> OUT/tables.md, docs/v18/EMBEDDING_COMPARISON_TABLES.md
  v18_embed_compare.py figure     -> docs/v18/EMBEDDING_COMPARISON.png
Aggregates only; OUT umask 077; patient counts 1-10 are suppressed in every written file.
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
sys.path.insert(0, str(HERE))
import v18_af_confirm as AF  # noqa: E402  (patches v17_confirm: 38-trial ALL, V18 paths)
import v18_clmbr as C  # noqa: E402

V = AF.V
E, S6, S8 = V.E, V.S6, V.S8
from s1_ladder import halves  # noqa: E402

A = V.A
OUT = A / "claude-v18-embed-compare"
DOCS = HERE.parent.parent / "docs" / "v18"
ALL = list(V.ALL)
OLD, NEW, AF5 = list(V.OLD), list(V.NEW), list(AF.AF5)
assert ALL == OLD + NEW + AF5 and len(ALL) == 38
KEY = V.KEY
CATEGORY = {**C.CATEGORY, **{t: "AF" for t in AF5}}
RUNGS = ["P1", "P5", "P2", "sparse", "hdPS200", "clinical"]
RUNG_LAB = {"P1": "P1 demo", "P5": "P5 demo+5dx", "P2": "P2 demo+6dx", "sparse": "sparse", "hdPS200": "hdPS200",
            "clinical": "clinical"}
ARMS = ["base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG", "shufCLMBR", "noise96"]
COMP = {"base": [], "ECG": ["ecg"], "CLMBR": ["clm"], "CLMBR+ECG": ["clm", "ecg"], "shufECG": ["she"], "shufCLMBR": ["shc"],
        "noise96": ["nz96"]}
NOISE96_SEED0 = 960_000
VN = [c for c, _, _ in E.VARS]
NONCODED = list(C.NONCODED)
MIN_CELL = 11
NPERM = 20000
COUNT_COLS = ["n", "n_t", "n_c", "n_pairs"]


def suppress(D):
    """patient counts 1-10 -> NaN (flag column); applied to every written file."""
    D = D.copy()
    flag = np.zeros(len(D), bool)
    for c in COUNT_COLS:
        if c in D:
            v = pd.to_numeric(D[c], errors="coerce")
            b = (v >= 1) & (v < MIN_CELL)
            flag |= b.to_numpy()
            D.loc[b, c] = np.nan
    for c in ("retain", "common_frac_of_base", "common_frac_of_smaller"):  # would reveal the suppressed count
        if c in D:
            D.loc[flag, c] = np.nan
    D["suppressed_lt11"] = flag
    return D


# ================================================================ run
def panel58(T, Hv, vc, t, s_idx, s_w):
    comp = pd.Series(E.smd_components(Hv, t, s_idx, s_w, t[s_idx]), index=T.H.columns)
    return np.array([comp[vc[c]].dropna().mean() if len(comp[vc[c]].dropna()) else np.nan for c in VN])


def task(args):
    n, half = args
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    b5, psn5, hf = C.designs(T, n, C.P5DX)
    b2, psn2, _ = C.designs(T, n, C.P2DX)
    d2 = V.cdirs(n)[1]
    Xe, ovl = V.xpanel(T, d2)
    hk = S6.HDPS_KEYS.get((T.n, str(d2)), {})
    dom = pd.read_csv(d2 / "dictionary.csv").set_index("variable").domain
    r = halves(T, i)[half]
    t = T.t[r]
    X1 = T.cov.iloc[r][T.demo].to_numpy(float)
    dx = T.X_dx[r]
    Hk = T.hd(200, t=t, rows=r)
    sel = S6.hdps_selected(T, r, t, 200)
    xdrop_hd = {c for c in Xe.columns if S6.hdps_overlap(hk.get(c, set()), sel)}
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    dxn = list(T.demo) + list(T.dxc)
    rung = {"P1": (X1, list(T.demo), set(), set()), "P5": (b5[r], psn5, set(), set()), "P2": (b2[r], psn2, set(), set()),
            "sparse": (dx, dxn, set(), set()), "hdPS200": (np.hstack([dx, Hk]), dxn, set(), xdrop_hd),
            "clinical": (T.X_core[r], list(T.core), clin_ex, set())}
    CL = T.clm_pc
    assert CL.shape == (len(T.t), 64) and np.isfinite(CL).all()
    nz96 = np.random.default_rng(NOISE96_SEED0 + i).normal(size=(len(T.t), 96))
    blk = {"clm": CL[r], "shc": CL[T.shuffle_perm][r], "ecg": T.ecg_pc[r], "she": T.ecg_pc[T.shuffle_perm][r], "nz96": nz96[r]}
    Hv = T.H.to_numpy(float)[r]
    vc = E.var_components(T.H)
    out, cs, logx = [], [], {}

    def xv(psn, extra_drop):
        drop = set(S6.excluded_extra(psn, list(Xe.columns), ovl)) | {c for c in Xe.columns if S8.composite_overlap(c, psn)}
        drop |= set(extra_drop)
        U = Xe.drop(columns=sorted(drop)).iloc[r]
        U = U.loc[:, U.notna().sum() > 0]
        U = U.loc[:, U.nunique() > 1]
        lv = [c for c in U.columns if dom.get(c, "") == "lab_vital"]
        lvv = [c for c in lv if not c.endswith("_missing") and c not in ("n_bp_readings_365", "weight_change_missing")]
        return (U.to_numpy(float), U[lv].to_numpy(float), U[lvv].to_numpy(float)), len(drop)

    def pref(d, p):
        return {k.replace("x_", p + "_", 1): v for k, v in d.items()}

    def xrec(XV, s_idx, s_w):
        XA, XL, XLV = XV
        return {**V.xsmd(XA, t, s_idx, s_w), **pref(V.xsmd(XL, t, s_idx, s_w), "lv"), **pref(V.xsmd(XLV, t, s_idx, s_w), "lvv")}

    def rec(rg, role, X, XV, nd, ex58, ndh):
        S8._LAST.clear()
        o = E.run_cell(T, X, rows=r, estimator=("match", 0.2, 1))
        s_idx, s_w = (np.arange(len(t)), np.ones(len(t))) if X is None else S8._LAST["m"]
        small = min(o["n_t"], o["n_c"])
        out.append(dict(trial=n, key=KEY[n], set="old18" if n in OLD else ("new15" if n in NEW else "af5"), category=CATEGORY[n],
                        idx=i, half=half, rung=rg, arm_role=role, rb=T.rb, rs=T.rs, x_ndrop=nd, x_ndrop_hdps=ndh,
                        ex58=";".join(sorted(ex58)), retain=(o["n_pairs"] / small) if X is not None else np.nan, **o,
                        **xrec(XV, s_idx, s_w)))
        return s_idx, s_w, o

    XV0, nd0 = xv([], set())
    rec("none", "unmatched", None, XV0, nd0, set(), 0)
    for rg in RUNGS:
        X, psn, ex58, xdh = rung[rg]
        XV, nd = xv(psn, xdh)
        ms = {}
        for role in ARMS:
            s_idx, s_w, o = rec(rg, role, np.hstack([X] + [blk[b] for b in COMP[role]]), XV, nd, ex58, len(xdh))
            ms[role] = (s_idx, o)
        if half != "full":
            continue
        # common support: anchors matched under both base and the arm (ratio 1: s_idx = [anchors, partners])
        small = min(ms["base"][1]["n_t"], ms["base"][1]["n_c"])
        own = panel58(T, Hv, vc, t, ms["base"][0], np.ones(len(ms["base"][0])))
        ref = np.array([ms["base"][1][f"smd:{c}"] for c in VN], float)
        logx[f"{rg}_panel58_repro_maxdev"] = float(np.nanmax(np.abs(own - ref)))
        anc = {a: ms[a][0][: len(ms[a][0]) // 2] for a in ms}
        for emb in ("ECG", "CLMBR", "CLMBR+ECG", "noise96"):
            common = np.intersect1d(anc["base"], anc[emb])
            for arm in ("base", emb):
                s_idx = ms[arm][0]
                cl = np.r_[anc[arm], anc[arm]]
                k = np.isin(cl, common)
                si, sw = s_idx[k], np.ones(int(k.sum()))
                sv = panel58(T, Hv, vc, t, si, sw)
                cs.append(dict(trial=n, key=KEY[n], category=CATEGORY[n], idx=i, rung=rg, emb=emb, arm=arm, ex58=";".join(sorted(ex58)),
                               n_pairs=len(common), common_frac_of_base=len(common) / max(len(anc["base"]), 1),
                               common_frac_of_smaller=len(common) / small, rb=T.rb, rs=T.rs,
                               **{f"smd:{c}": v for c, v in zip(VN, sv)}, **xrec(XV, si, sw)))
    log = dict(trial=n, half=half, idx=i, seed_halves=16060 + i, seed_noise96=NOISE96_SEED0 + i, hf_column=hf,
               x_ncols_panel=int(Xe.shape[1]), n_hdps_keys=int(sum(bool(v) for v in hk.values())), **logx,
               secs=round(time.time() - t0, 1))
    print(f"{n} {half} {time.time() - t0:.0f}s", flush=True)
    return out, cs, log


def run(trials, workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    for n in trials:
        if n in NEW and not (A / f"claude-v17-trials/{n}.READY").exists():
            raise RuntimeError(f"{n} not READY")
        if n in AF5 and not (A / f"claude-v18-trials/{n}.READY").exists():
            raise RuntimeError(f"{n} not READY")
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4")
    tk = sorted([(n, h) for n in trials for h in ("full", "A", "B")], key=lambda x: (x[0] not in big, x[1] != "full"))
    with Pool(min(workers, len(tk), 32)) as p:
        res = p.map(task, tk, chunksize=1)
    tag = "" if set(trials) == set(ALL) else "_partial"
    R = pd.DataFrame([x for o, _, _ in res for x in o])
    R.to_parquet(OUT / f"restricted_results_unsuppressed{tag}.parquet")  # kept for verify only (aggregates, 600)
    suppress(R).to_csv(OUT / f"results{tag}.csv", index=False)
    CS = pd.DataFrame([x for _, c, _ in res for x in c])
    CS.to_parquet(OUT / f"restricted_common_support_unsuppressed{tag}.parquet")
    suppress(CS).to_csv(OUT / f"common_support{tag}.csv", index=False)
    (OUT / f"log{tag}.json").write_text(json.dumps([lg for _, _, lg in res], indent=1))
    print("done", flush=True)


# ================================================================ verify (reuse of existing cells)
def _cmp(a, b, cols, src, rung, arm):
    rows = []
    ix = a.index.intersection(b.index)
    for c in cols:
        if c not in a or c not in b:
            continue
        x, y = a.loc[ix, c].to_numpy(float), b.loc[ix, c].to_numpy(float)
        bad = int((np.isnan(x) ^ np.isnan(y)).sum())
        d = float(np.nanmax(np.abs(x - y))) if np.isfinite(x - y).any() else 0.0
        rows.append(dict(source=src, rung=rung, arm=arm, col=c, n_rows=len(ix), n_rows_ref=len(b), maxdev=d, nan_mismatch=bad))
    return rows


def verify():
    R = pd.read_parquet(OUT / "restricted_results_unsuppressed.parquet")
    base_cols = ["loghr", "se", "n", "n_t", "n_c", "n_pairs", "mean_smd", "cstat"] + [f"smd:{c}" for c in VN]
    xcols = ["x_pct_lt10", "x_mean", "x_nvars", "lv_pct_lt10", "lv_mean", "lv_nvars", "lvv_pct_lt10", "lvv_mean", "lvv_nvars"]
    rows = []
    # (1) v18_clmbr, 33 trials, P1/P5/P2
    Q = pd.read_csv(C.OUT / "results_all.csv", low_memory=False)
    for rg in ("P1", "P5", "P2"):
        for role in ("unmatched", "base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG", "shufCLMBR"):
            a = R[(R.rung == ("none" if role == "unmatched" else rg)) & (R.arm_role == role) & R.trial.isin(OLD + NEW)].set_index(["trial", "half"])
            b = Q[(Q.ps == ("none" if role == "unmatched" else rg)) & (Q.arm_role == role)].set_index(["trial", "half"])
            rows += _cmp(a, b, base_cols + xcols, "v18_clmbr", rg, role)
    # (2) AF-5 (v18_af_confirm), P1/P5
    Q = pd.read_csv(AF.OUT / "results_af5.csv", low_memory=False)
    for rg in ("P1", "P5"):
        for role in ("unmatched", "base", "ECG", "shufECG"):
            a = R[(R.rung == ("none" if role == "unmatched" else rg)) & (R.arm_role == role) & R.trial.isin(AF5)].set_index(["trial", "half"])
            b = Q[(Q.ps == ("none" if role == "unmatched" else rg)) & (Q.arm_role == role)].set_index(["trial", "half"])
            rows += _cmp(a, b, base_cols + ["x_pct_lt10", "x_mean", "x_nvars"], "v18_af_confirm", rg, role)
    # (3) S1 ladder, v1.6 18, sparse / hdPS200 / clinical
    Q = pd.read_csv(A / "claude-v16-s1-ladder/results.csv", low_memory=False)
    for rg, cell in (("sparse", "r5_sparse"), ("hdPS200", "r7_hdPS200"), ("clinical", "r8_clinical")):
        for role in ("unmatched", "base", "ECG", "shufECG"):
            a = R[(R.rung == ("none" if role == "unmatched" else rg)) & (R.arm_role == role) & R.trial.isin(OLD)].set_index(["trial", "half"])
            b = Q[(Q.cell == ("unmatched" if role == "unmatched" else cell)) & (Q.arm_role == role)].set_index(["trial", "half"])
            rows += _cmp(a, b, base_cols, "s1_ladder", rg, role)
    Vd = pd.DataFrame(rows)
    Vd.to_csv(OUT / "verify.csv", index=False)
    g = Vd.groupby(["source", "rung", "arm"]).agg(n=("n_rows", "max"), nref=("n_rows_ref", "max"), maxdev=("maxdev", "max"),
                                                  nan_mismatch=("nan_mismatch", "sum"))
    print(g.to_string())
    print("overall max deviation", Vd.maxdev.max(), "nan mismatches", Vd.nan_mismatch.sum())
    return g


# ================================================================ summaries
HIGHER = {"nc_lt01", "lt01", "lv_lt01", "lvv_lt01", "cons", "retain"}
METRICS = ["nc_lt01", "lt01", "lv_lt01", "lvv_lt01", "nc_mean", "m58_mean", "absd", "z2", "cons", "retain"]
FAMILY = {"nc_lt01": "balance-primary", "lt01": "balance-secondary", "lv_lt01": "balance-secondary", "lvv_lt01": "balance-secondary",
          "nc_mean": "balance-secondary", "m58_mean": "balance-secondary", "absd": "emulation", "z2": "emulation", "cons": "emulation",
          "retain": "retention"}
# (a, b, sided): d = a - b oriented "a better"; "two" = two-sided
CONTRASTS = [("ECG", "base", "one"), ("CLMBR", "base", "one"), ("CLMBR+ECG", "base", "one"),
             ("ECG", "CLMBR", "two"), ("CLMBR+ECG", "CLMBR", "one"), ("CLMBR+ECG", "ECG", "one"),
             ("ECG", "shufECG", "one"), ("CLMBR", "shufCLMBR", "one"), ("CLMBR+ECG", "noise96", "one"),
             ("shufECG", "base", "two"), ("shufCLMBR", "base", "two"), ("noise96", "base", "two")]
PLANB = {"ECG vs base", "CLMBR vs base", "CLMBR+ECG vs base", "ECG vs CLMBR", "CLMBR+ECG vs CLMBR", "CLMBR+ECG vs ECG",
         "ECG vs shufECG", "CLMBR vs shufCLMBR", "shufECG vs base", "shufCLMBR vs base"}


def trial_metrics(g):
    g = g.copy()
    S = g[[f"smd:{c}" for c in VN]].abs().to_numpy(float)
    for j, ex in enumerate(g.ex58.fillna("").astype(str)):
        for c in filter(None, ex.split(";")):
            S[j, VN.index(c)] = np.nan
    sm = pd.DataFrame(S, columns=VN)
    nc = sm[NONCODED]
    z = (g.loghr - g.rb) / np.sqrt(g.se ** 2 + g.rs ** 2)
    return pd.DataFrame({"nc_lt01": (100 * (nc < 0.1).sum(1) / nc.notna().sum(1)).to_numpy(),
                         "lt01": (100 * (sm < 0.1).sum(1) / sm.notna().sum(1)).to_numpy(),
                         "lv_lt01": g.lv_pct_lt10.to_numpy(), "lvv_lt01": g.lvv_pct_lt10.to_numpy(),
                         "nc_mean": nc.mean(1).to_numpy(), "m58_mean": sm.mean(1).to_numpy(),
                         "absd": (g.loghr - g.rb).abs().to_numpy(), "z2": (z ** 2).to_numpy(), "cons": (100.0 * (z.abs() < 1.96)).to_numpy(),
                         "retain": 100 * g.retain.to_numpy() if "retain" in g else np.nan,
                         "loghr": g.loghr.to_numpy(), "se": g.se.to_numpy(), "rb": g.rb.to_numpy(), "rs": g.rs.to_numpy()},
                        index=g.trial.to_numpy())


def p1s(d):
    return V.signflip_1s(np.asarray(d, float))


def p2s(d):
    d = np.asarray(d, float)
    return min(1.0, 2 * min(V.signflip_1s(d), V.signflip_1s(-d)))


def bshuf(la, sa, lb, sb, rb, rs, m, IX, rb_pool, rs_pool, side):
    def st(q, v):
        if m == "absd":
            return (np.abs(la - q) - np.abs(lb - q)).mean(-1)
        return ((la - q) ** 2 / (sa ** 2 + v ** 2) - (lb - q) ** 2 / (sb ** 2 + v ** 2)).mean(-1)
    obs = float(st(rb, rs))
    null = st(rb_pool[IX], rs_pool[IX])
    lo = float((null <= obs + 1e-12).mean())
    p = lo if side == "one" else float(min(1.0, 2 * min(lo, (null >= obs - 1e-12).mean())))
    return obs, float(null.mean()), p


def sets_def():
    S = {"all38": ALL, "all33": OLD + NEW, "conf20": NEW + AF5, "old18": OLD, "new15": NEW, "af5": AF5}
    for cat in ("AF", "HF", "DM", "HTN", "ACS/post-MI", "Other"):
        S[f"cat:{cat}"] = [t for t in ALL if CATEGORY[t] == cat]
    return S


_M = None


def load_M():
    R = pd.read_parquet(OUT / "restricted_results_unsuppressed.parquet")  # summaries are aggregates over trials
    R = R[R.arm_role != "unmatched"]
    assert R.groupby(["trial", "half", "rung", "arm_role"]).size().max() == 1
    assert R.trial.nunique() == 38
    return {h: {rg: {a: trial_metrics(R[(R.half == h) & (R.rung == rg) & (R.arm_role == a)]) for a in ARMS} for rg in RUNGS}
            for h in ("full", "A", "B")}


def _analyse(args):
    sname, trials, rg = args
    M = _M
    CLm = V.cluster_of()
    F0 = M["full"]["P1"]["base"].loc[ALL]
    rb38, rs38 = F0.rb.to_numpy(), F0.rs.to_numpy()
    k = len(trials)
    rng = np.random.default_rng(0)
    IX38 = np.array([rng.permutation(38)[:k] for _ in range(NPERM)])
    rng = np.random.default_rng(0)
    IXw = np.array([rng.permutation(k) for _ in range(NPERM)])
    F = {a: M["full"][rg][a].loc[trials] for a in ARMS}
    rbw, rsw = F["base"].rb.to_numpy(), F["base"].rs.to_numpy()
    lab = [CLm[KEY[t]] for t in trials]
    out = []
    for a, b, side in CONTRASTS:
        pf = p1s if side == "one" else p2s
        for m in METRICS:
            sgn = 1 if m in HIGHER else -1
            d = sgn * (F[a][m] - F[b][m])
            row = dict(set=sname, rung=rg, contrast=f"{a} vs {b}", sided=side, metric=m, family=FAMILY[m], n=k,
                       mean_a=F[a][m].mean(), mean_b=F[b][m].mean(), diff_a_minus_b=(F[a][m] - F[b][m]).mean(),
                       k_a_better=f"{int((d > 0).sum())}/{int(d.notna().sum())}", p=pf(d.to_numpy()))
            cl = pd.Series(d.to_numpy(), index=lab).groupby(level=0).mean()
            row.update(n_clusters=len(cl), cluster_p=pf(cl.to_numpy()))
            row["loo_max_p"] = max(pf(d.drop(t).to_numpy()) for t in trials) if k > 2 else np.nan
            for h in ("A", "B"):
                row[f"p_{h}"] = pf((sgn * (M[h][rg][a].loc[trials][m] - M[h][rg][b].loc[trials][m])).to_numpy())
            if m in ("absd", "z2"):
                la, sa, lb, sb = (x.to_numpy() for x in (F[a].loghr, F[a].se, F[b].loghr, F[b].se))
                ok = np.isfinite(la) & np.isfinite(sa) & np.isfinite(lb) & np.isfinite(sb)
                if ok.all():
                    Iw, I38 = IXw, IX38
                else:  # trials without an estimate in either arm are dropped; pools re-drawn for k' trials
                    kk = int(ok.sum())
                    rg_ = np.random.default_rng(0)
                    I38 = np.array([rg_.permutation(38)[:kk] for _ in range(NPERM)])
                    rg_ = np.random.default_rng(0)
                    Iw = np.array([rg_.permutation(kk) for _ in range(NPERM)])
                    la, sa, lb, sb = la[ok], sa[ok], lb[ok], sb[ok]
                rbk, rsk = rbw[ok], rsw[ok]
                o, nm, pw = bshuf(la, sa, lb, sb, rbk, rsk, m, Iw, rbk, rsk, side)
                _, nm38, p38 = bshuf(la, sa, lb, sb, rbk, rsk, m, I38, rb38, rs38, side)
                row.update(bshuf_obs=o, bshuf_null_mean_within=nm, bshuf_p_within=pw, bshuf_null_mean_38=nm38, bshuf_p_38=p38,
                           bshuf_ndraw=NPERM)
            out.append(row)
    print(sname, rg, flush=True)
    return out


def _init(M):
    global _M
    _M = M


def bh_all(S):
    S = S.copy()
    S["q"] = np.nan
    for fam, g in S.groupby("family"):
        S.loc[g.index, "q"] = E.bh_fdr(g.p.to_numpy())
    ts = S.metric.isin(["absd", "z2"])
    for col in ("bshuf_p_within", "bshuf_p_38"):
        S[f"q_{col}"] = np.nan
        S.loc[ts, f"q_{col}"] = E.bh_fdr(S.loc[ts, col].to_numpy())
    return S


def status(r):
    if r["set"] == "all33" and r["rung"] in ("P1", "P5", "P2") and r["contrast"] in PLANB and r["metric"] in (
            "nc_lt01", "lt01", "lv_lt01", "lvv_lt01", "nc_mean", "absd", "z2", "cons"):
        return "prespecified (v1.8 Plan B)"
    return "exploratory"


def robust(r):
    """robust = p, cluster p, LOO max p, both halves < 0.05 (and, for absd / z2, benchmark shuffle vs 38 < 0.05)."""
    ok = all((r.get(c, np.nan) < 0.05) for c in ("p", "cluster_p", "loo_max_p", "p_A", "p_B"))
    if r["metric"] in ("absd", "z2"):
        ok = ok and r.get("bshuf_p_38", np.nan) < 0.05
    return bool(ok)


def summarize(workers):
    from multiprocessing import Pool
    os.umask(0o077)
    M = load_M()
    SD = sets_def()
    tk = [(s, tr, rg) for s, tr in SD.items() for rg in RUNGS]
    tk.sort(key=lambda x: -len(x[1]))
    with Pool(min(workers, 32), initializer=_init, initargs=(M,)) as p:
        res = p.map(_analyse, tk, chunksize=1)
    S = pd.DataFrame([x for o in res for x in o])
    S = bh_all(S)
    S["status"] = S.apply(status, axis=1)
    S["robust"] = S.apply(robust, axis=1)
    S.to_csv(OUT / "summary.csv", index=False)
    # retention (full cohort, per rung x arm) and common support
    rt = []
    for rg in RUNGS:
        for a in ARMS:
            x = M["full"][rg][a].loc[ALL].retain
            rt.append(dict(rung=rg, arm=a, mean_retain_pct=x.mean(), min_retain_pct=x.min(), median_retain_pct=x.median()))
    pd.DataFrame(rt).to_csv(OUT / "retention.csv", index=False)
    common_summary()
    print("summary rows", len(S))


def common_summary():
    D = pd.read_parquet(OUT / "restricted_common_support_unsuppressed.parquet")
    CLm = V.cluster_of()
    rows = []
    for (rg, emb), g in D.groupby(["rung", "emb"], sort=False):
        Mb = trial_metrics(g[g.arm == "base"].assign(loghr=np.nan, se=np.nan, lv_pct_lt10=g[g.arm == "base"].lv_pct_lt10)).loc[ALL]
        Me = trial_metrics(g[g.arm == emb].assign(loghr=np.nan, se=np.nan)).loc[ALL]
        frac = g[g.arm == "base"].set_index("trial").common_frac_of_smaller.reindex(ALL)
        for sname, trials in (("all38", ALL), ("all33", OLD + NEW), ("conf20", NEW + AF5), ("old18", OLD)):
            for m in ("nc_lt01", "lt01", "lv_lt01", "nc_mean"):
                sgn = 1 if m in HIGHER else -1
                d = sgn * (Me.loc[trials, m] - Mb.loc[trials, m])
                cl = pd.Series(d.to_numpy(), index=[CLm[KEY[t]] for t in trials]).groupby(level=0).mean()
                rows.append(dict(set=sname, rung=rg, emb=emb, metric=m, n=len(trials), common_pct_of_smaller=100 * frac.loc[trials].mean(),
                                 min_common_pct=100 * frac.loc[trials].min(), base_common=Mb.loc[trials, m].mean(),
                                 emb_common=Me.loc[trials, m].mean(), diff=(Me.loc[trials, m] - Mb.loc[trials, m]).mean(),
                                 k_better=f"{int((d > 0).sum())}/{len(d)}", p=p1s(d.to_numpy()), cluster_p=p1s(cl.to_numpy())))
    pd.DataFrame(rows).to_csv(OUT / "common_summary.csv", index=False)


# ================================================================ tables / figure
def fp(p):
    if pd.isna(p):
        return "–"
    return f"{p:.3f}" if p >= 0.001 else "<0.001"


def tables():
    from v13_summarize import md
    S = pd.read_csv(OUT / "summary.csv")
    CS = pd.read_csv(OUT / "common_summary.csv")
    RT = pd.read_csv(OUT / "retention.csv")
    L = []
    # main table
    L.append("## Main table (all 38 trials, full cohort)\n")
    L.append("Balance = % of non-coded physiology variables with |SMD| < 0.1 (higher better); |Δ| = mean |Δlog HR| vs RCT "
             "(lower better). p = one-sided exact sign-flip vs base; bs = benchmark-shuffle p (38-RCT pool); "
             "\\* = robust (p, cluster, LOO, both halves < 0.05; for |Δ| also bs < 0.05). q = BH within endpoint family.\n")
    rows = []
    for rg in RUNGS:
        q = S[(S.set == "all38") & (S.rung == rg)]
        d = {"rung": RUNG_LAB[rg]}
        b = q[(q.contrast == "ECG vs base") & (q.metric == "nc_lt01")].iloc[0]
        d["bal base"] = f"{b.mean_b:.1f}"
        for a in ("ECG", "CLMBR", "CLMBR+ECG"):
            x = q[(q.contrast == f"{a} vs base") & (q.metric == "nc_lt01")].iloc[0]
            d[f"bal +{a}"] = f"{x.mean_a:.1f} ({x.diff_a_minus_b:+.1f}; p {fp(x.p)}, q {fp(x.q)}){'*' if x.robust else ''}"
        b = q[(q.contrast == "ECG vs base") & (q.metric == "absd")].iloc[0]
        d["\\|Δ\\| base"] = f"{b.mean_b:.3f}"
        for a in ("ECG", "CLMBR", "CLMBR+ECG"):
            x = q[(q.contrast == f"{a} vs base") & (q.metric == "absd")].iloc[0]
            d[f"\\|Δ\\| +{a}"] = f"{x.mean_a:.3f} (p {fp(x.p)}; bs {fp(x.bshuf_p_38)}){'*' if x.robust else ''}"
        rows.append(d)
    L.append(md(pd.DataFrame(rows)) + "\n")
    # key contrasts
    KEYC = ["ECG vs base", "CLMBR vs base", "CLMBR+ECG vs base", "ECG vs CLMBR", "CLMBR+ECG vs CLMBR", "CLMBR+ECG vs ECG",
            "ECG vs shufECG", "CLMBR vs shufCLMBR", "CLMBR+ECG vs noise96", "shufECG vs base", "shufCLMBR vs base", "noise96 vs base"]
    cols = ["rung", "contrast", "mean_a", "mean_b", "diff_a_minus_b", "k_a_better", "p", "q", "cluster_p", "loo_max_p", "p_A", "p_B"]
    lab = {"nc_lt01": "non-coded physiology % |SMD| < 0.1 (PRIMARY)", "lt01": "full 58-panel % |SMD| < 0.1",
           "lv_lt01": "covars2b lab/vital non-proximal % |SMD| < 0.1", "lvv_lt01": "covars2b lab/vital values only % |SMD| < 0.1",
           "nc_mean": "non-coded mean |SMD| (lower better)", "m58_mean": "58-panel mean |SMD| (lower better)",
           "absd": "|Δlog HR| vs RCT (lower better)", "z2": "z² vs RCT (lower better)", "cons": "% consistent with RCT",
           "retain": "retention, pairs / smaller arm, % (higher better)"}
    SET_LAB = {"all38": "All 38 trials", "all33": "All 33 (v1.6 18 + v1.7 15; Plan B set)", "conf20": "Confirmation 20 (v1.7 15 + v1.8 AF 5)",
               "old18": "v1.6 18", "new15": "v1.7 15", "af5": "v1.8 AF 5"}
    Lf = ["# Embedding comparison: complete cell tables (generated by scripts/v18/v18_embed_compare.py tables)\n",
          "Every set × rung × contrast × endpoint cell. Aggregates only. `a − b` in raw units; p oriented \"a better\" "
          "(two-sided for ECG vs CLMBR and placebo vs base); q = BH-FDR within endpoint family over all cells; "
          "bs_w / bs_38 = benchmark-shuffle p with the within-set / 38-RCT pool (20,000 joint draws without replacement). "
          "status P = prespecified (v1.8 Plan B), else exploratory; R = robust.\n"]
    for sname in list(SET_LAB) + [s for s in S.set.unique() if s.startswith("cat:")]:
        Lf.append(f"\n## {SET_LAB.get(sname, sname)}\n")
        for m in METRICS:
            q = S[(S.set == sname) & (S.metric == m)].copy()
            q["rung"] = q.rung.map(RUNG_LAB)
            c = cols + (["bshuf_p_within", "bshuf_p_38"] if m in ("absd", "z2") else [])
            q["st"] = np.where(q.status.str.startswith("pre"), "P", "") + np.where(q.robust, "R", "")
            Lf.append(f"\n**{lab[m]}**\n\n" + md(q[c + ["st"]].rename(columns={"diff_a_minus_b": "a−b", "k_a_better": "a better",
                                                                              "bshuf_p_within": "bs_w", "bshuf_p_38": "bs_38"}), 3))
    (DOCS / "EMBEDDING_COMPARISON_TABLES.md").write_text("\n".join(Lf) + "\n")
    # compact tables for the main doc
    for sname in ("all38", "conf20", "old18", "all33"):
        L.append(f"\n## {SET_LAB[sname]}: key contrasts\n")
        for m in ("nc_lt01", "lt01", "lv_lt01", "absd", "z2"):
            q = S[(S.set == sname) & (S.metric == m) & S.contrast.isin(KEYC)].copy()
            q["rung"] = q.rung.map(RUNG_LAB)
            c = cols + (["bshuf_p_within", "bshuf_p_38"] if m in ("absd", "z2") else [])
            if sname in ("all38", "all33"):
                c = [x for x in c if x != "bshuf_p_within"] if sname == "all38" else c
            q["R"] = np.where(q.robust, "R", "")
            L.append(f"\n**{lab[m]}**\n\n" + md(q[c + ["R"]].rename(columns={"diff_a_minus_b": "a−b", "k_a_better": "a better",
                                                                            "bshuf_p_within": "bs_w", "bshuf_p_38": "bs_38"}), 3))
    L.append("\n## Per category (all rungs; key contrasts)\n")
    for m in ("nc_lt01", "absd"):
        q = S[S.set.str.startswith("cat:") & (S.metric == m) & S.contrast.isin(KEYC[:6])].copy()
        q["rung"] = q.rung.map(RUNG_LAB)
        c = ["set", "rung", "contrast", "n", "mean_a", "mean_b", "diff_a_minus_b", "k_a_better", "p", "q", "cluster_p"] + \
            (["bshuf_p_within", "bshuf_p_38"] if m == "absd" else [])
        L.append(f"\n**{lab[m]}**\n\n" + md(q[c].rename(columns={"diff_a_minus_b": "a−b", "k_a_better": "a better",
                                                                  "bshuf_p_within": "bs_w", "bshuf_p_38": "bs_38"}), 3))
    L.append("\n## Retention (full cohort, 38 trials; pairs / smaller arm, %)\n")
    L.append(md(RT.pivot(index="rung", columns="arm", values="mean_retain_pct").reindex(RUNGS)[ARMS].reset_index(), 1))
    L.append("\nMinimum over trials:\n\n" + md(RT.pivot(index="rung", columns="arm", values="min_retain_pct").reindex(RUNGS)[ARMS].reset_index(), 1))
    L.append("\n## Common support (anchors matched under both base and the arm; full cohort)\n")
    q = CS[CS.metric.isin(["nc_lt01", "lv_lt01"])].copy()
    q["rung"] = q.rung.map(RUNG_LAB)
    L.append(md(q[["set", "rung", "emb", "metric", "common_pct_of_smaller", "min_common_pct", "base_common", "emb_common", "diff",
                   "k_better", "p", "cluster_p"]], 3))
    (OUT / "tables.md").write_text("\n".join(L) + "\n")
    print("tables written")


def figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    S = pd.read_csv(OUT / "summary.csv")
    S = S[S.set == "all38"]
    lines = [("ECG", "+ECG 32", "#eb6834", "-"), ("CLMBR", "+CLMBR-T 64", "#2a78d6", "-"), ("CLMBR+ECG", "+CLMBR 64 + ECG 32", "#4a3aa7", "-"),
             ("shufECG", "shuffled ECG 32", "#eb6834", ":"), ("shufCLMBR", "shuffled CLMBR 64", "#2a78d6", ":"),
             ("noise96", "noise 96", "#4a3aa7", ":")]
    mets = [("nc_lt01", "Balance gain vs base (pp)\nnon-coded physiology vars with |SMD| < 0.1"),
            ("absd", "Change in mean |Δlog HR| vs RCT\n(negative = closer to RCT)")]
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.8))
    x = np.arange(len(RUNGS))
    for j, (m, ylab) in enumerate(mets):
        a = ax[j]
        a.axhline(0, color="#555", lw=0.8)
        for arm, nm, col, ls in lines:
            q = S[(S.metric == m) & (S.contrast == f"{arm} vs base")].set_index("rung").reindex(RUNGS)
            y = q.diff_a_minus_b.to_numpy()
            plac = ls == ":"
            a.plot(x, y, ls=ls, color=col, lw=1.2 if plac else 2.0, alpha=0.75 if plac else 1.0, label=nm, zorder=2)
            sig = (q.p < 0.05).to_numpy()
            rob = q.robust.to_numpy().astype(bool)
            # filled = p < 0.05 and robust; open = p < 0.05 not robust; small dot = p >= 0.05
            for xi, yi, s_, r_ in zip(x, y, sig, rob):
                if r_:
                    a.plot(xi, yi, "o", color=col, ms=7, zorder=3)
                elif s_:
                    a.plot(xi, yi, "o", mfc="white", mec=col, ms=7, mew=1.5, zorder=3)
                else:
                    a.plot(xi, yi, ".", color=col, ms=5 if not plac else 4, zorder=3)
        a.set_xticks(x)
        a.set_xticklabels([RUNG_LAB[r].replace(" ", "\n", 1) for r in RUNGS])
        a.set_xlabel("PS base design (thin → rich)")
        a.set_ylabel(ylab)
        a.set_title(["A. Held-out physiology balance", "B. Agreement with RCT hazard ratio"][j], loc="left", fontsize=10.5)
    h, lb = ax[0].get_legend_handles_labels()
    from matplotlib.lines import Line2D
    h += [Line2D([], [], marker="o", color="#333", ls="", ms=7), Line2D([], [], marker="o", mfc="white", mec="#333", ls="", ms=7)]
    lb += ["robust (p, cluster, LOO, both halves < 0.05;\n|Δ|: also benchmark shuffle < 0.05)", "p < 0.05, not robust"]
    fig.legend(h, lb, loc="lower center", ncol=4, frameon=False, fontsize=8.5)
    fig.text(0.5, 0.965, "38 trials, 1:1 caliper-0.2 PS matching; each line = arm minus base at that rung "
             "(one-sided exact sign-flip; placebos two-sided). Exploratory.", ha="center", fontsize=8.5, color="#333")
    fig.tight_layout(rect=(0, 0.13, 1, 0.95))
    fig.savefig(DOCS / "EMBEDDING_COMPARISON.png", dpi=160)
    print("figure written")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["run", "verify", "summarize", "tables", "figure"])
    ap.add_argument("--trials", default=",".join(ALL))
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    os.umask(0o077)
    if a.cmd == "run":
        run(a.trials.split(","), a.workers)
    elif a.cmd == "verify":
        verify()
    elif a.cmd == "summarize":
        summarize(a.workers)
    elif a.cmd == "tables":
        tables()
    else:
        figure()


if __name__ == "__main__":
    main()
