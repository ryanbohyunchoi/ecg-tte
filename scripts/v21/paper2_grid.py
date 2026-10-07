#!/usr/bin/env python
"""paper2 core grid (HANDOFF_PAPER2.md §3.1-3.4): learned representations (ECG embedding, CLMBR-T) vs hand-built PS
covariates, 38 trials x 5 rungs x 7 arms x 6 configurations. Template: scripts/v20/sens_primary32.py (imported, unchanged;
its helpers per_trial / paired_balance / contrast_row / relred_ci / bshuf / agree_metrics / p1s / p2s / suppress and the
sets S32 / S38 and CONFIGS are used as-is).

Rungs (PS base design, full cohort rows r = arange(n), built exactly as sens_primary32.task):
  P1       T.demo (age, sex, index year)
  P5       P1 + hypertension, T2D, CAD, AF, HF (v18_clmbr.designs(T, n, C.P5DX))              PRIMARY
  Flags    P1 + binary ICD-10 3-char dx flags, full pre-index history, index day excluded, >= 1 % prevalence in T.keys,
           roles["exposure_features"] removed (scripts/v21/ps_flags.py; flags_matrix below)
  hdPS200  T.X_dx + T.hd(200, t, rows)
  clinical T.X_core; ex58 = mean_meds, mean_util, smd_obs_<T.phys> (in the PS, so masked from every balance endpoint)
Arms (columns appended to the rung design; v18_embed_compare column order):
  base | ECG (+T.ecg_pc, 32) | CLMBR (+T.clm_pc, 64) | ECG+CLMBR (+T.clm_pc, +T.ecg_pc) | shufECG (+T.ecg_pc[T.shuffle_perm])
  | shufCLMBR (+T.clm_pc[T.shuffle_perm]) | CLMBR32 (+T.clm_pc[:, :32]; main config, P1 and P5 only)
Configurations: sens_primary32.CONFIGS (main, cal01, m13, iptw, overlap, gbm).  E.run_cell(..., cstat=None).

Endpoints (summarize; paired across trials, d > 0 = arm a better):
  balance  m54 = mean |SMD| over the 54 non-coded held-out items (E.VARS minus group "Coded record"); PRIMARY =
           relative reduction 100 * (1 - mean_a / mean_b) with a 4,000-resample trial bootstrap (relred_ci, seed 20261001);
           lt01_54 = % of the 54 with |SMD| < 0.1; the same on the 58-item panel (m58, lt01_58); per-domain relative
           reductions over the E.VARS groups. Items are paired within trial (paired_balance: an item counts only if
           observed in both arms; the clinical ex58 masking therefore carries over to cross-rung contrasts).
  agreement |dlog HR| vs RCT (absd), trials closer, exact sign-flip p (one-sided; two-sided for head-to-heads and
           placebo-vs-base), comparator-cluster p, leave-one-out max p, within-set benchmark-permutation p (20,000 draws,
           sens_primary32.bshuf; two-sided analogue for two-sided contrasts), Pearson r, estimate agreement (ea) and
           standardized-difference agreement (cons).
  BH-FDR within set, across all configurations x contrasts: balance family = {m54, lt01_54, m58, lt01_58} p-values;
           agreement family = {absd, cons, bshuf} p-values; per-endpoint q (q_<m>_sweep) as well; domain p-values are
           a separate exploratory family.

Usage:
  paper2_grid.py run [--workers 24] [--trials a,b]   -> core/restricted_cells.parquet, cells.csv (suppressed), log.json
  paper2_grid.py gate                                -> core/gate_sp32.csv, gate_v18.csv, gate_status.json
  paper2_grid.py summarize [--workers 24]            -> core/sensitivity.csv, domains.csv, per_trial.csv, tables.md
  paper2_grid.py labels                              -> core/labels_*.csv (needs docs/v21/TRIAL_LABELS.json)
  paper2_grid.py headline                            -> core/headline.csv, q_counts.csv, headline_domains.csv (subsets)
  paper2_grid.py flagscv [--stage all|run|summarize] -> core/restricted_flagscv_cells.parquet, flagscv_cells.csv, flagscv_log.csv,
                                                        flagscv.csv, flagscv_domains.csv (audit S1: CV-tuned PS-Flags)
  paper2_grid.py retsens                             -> core/retention_sens.csv (audit S7)
  paper2_grid.py privacy                             -> re-suppress log.json / flags_build.csv; scan core csvs (audit B1)
Aggregates only; OUT umask 077; patient counts 1-10 suppressed in every csv.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "v20"))
sys.path.insert(0, str(HERE.parent / "v18"))
sys.path.insert(0, str(HERE.parent))
import sens_primary32 as SP  # noqa: E402

AF, C, M18, V, E = SP.AF, SP.C, SP.M18, SP.V, SP.E
A = SP.A
OUT = A / "claude-v21-paper2" / "core"
FLAGS = OUT / "flags"
ALL, KEY, VN, GROUP = SP.ALL, SP.KEY, SP.VN, SP.GROUP
CONFIGS = SP.CONFIGS
S32, S38 = SP.S32, SP.S38
RUNGS = ["P1", "P5", "Flags", "hdPS200", "clinical"]
ARMS = ["base", "ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"]
KPC = {"base": 0, "ECG": 32, "CLMBR": 64, "ECG+CLMBR": 96, "shufECG": 32, "shufCLMBR": 64, "CLMBR32": 32}
CODED = [c for c in VN if GROUP[c] == "Coded record"]
NONCODED = [c for c in VN if GROUP[c] != "Coded record"]
DOMAINS = [g for g in dict.fromkeys(GROUP.values()) if g != "Coded record"]
assert len(CODED) == 4 and len(NONCODED) == 54 and NONCODED == list(C.NONCODED)
FLAG_MIN_PREV = 0.01
ICD10_3 = r"^dx_[A-Z][0-9][0-9A-Z]$"
NDRAW = 20000
LABELS_JSON = ROOT / "docs" / "v21" / "TRIAL_LABELS.json"


# ================================================================ PS-Flags design
def flags_matrix(T, n):
    """binary dx flags aligned to T.keys: count > 0, ICD-10 3-char only, exposure features removed, prevalence >= 1 %."""
    W = pd.read_parquet(FLAGS / f"restricted_flags_{n}.parquet").set_index("patient_key")
    miss = int((~T.keys.isin(W.index)).sum())
    W = W.reindex(T.keys)
    B = (W.fillna(0) > 0).astype(float)
    expo = set(T.roles.get("exposure_features", []))
    cols = [c for c in B.columns if re.match(ICD10_3, c) and c not in expo]
    n_expo = int(sum(c in expo for c in B.columns))
    B = B[cols]
    prev = B.mean()
    keep = prev.index[(prev >= FLAG_MIN_PREV) & (prev < 1.0)]
    pmax = float(prev[keep].max())
    compl = int(round(len(T.keys) * (1 - pmax)))  # patients WITHOUT the most prevalent flag: suppress if 1-10 (B1)
    info = dict(n_keys=len(T.keys), n_keys_not_in_roster=miss, n_codes_stored=int(W.shape[1]), n_expo_removed=n_expo,
                n_flags=len(keep), flag_prev_median=round(float(prev[keep].median()), 4),
                flag_prev_max=round(pmax, 4) if not (1 <= compl < SP.MIN_CELL) else None,
                flag_prev_max_suppressed=bool(1 <= compl < SP.MIN_CELL), lookback_days=36500)
    return B[keep].to_numpy(float), list(keep), info


# ================================================================ suppression (audit B1)
DERIVED = ["ess_t", "ess_c", "retain"]  # equal to / recover n_pairs under 1:1 matching (retain = n_pairs / min(n_t, n_c))


def suppress(D):
    """sens_primary32.suppress (counts 1-10 -> NaN) + blank every column from which a suppressed count can be recovered."""
    D = SP.suppress(D)
    if "suppressed_lt11" in D:
        for c in DERIVED + ["retain_main", "n_pairs_frac"]:
            if c in D:
                D.loc[D.suppressed_lt11, c] = np.nan
    return D


def small_pairs(g):
    v = pd.to_numeric(g["n_pairs"], errors="coerce")
    return (v >= 1) & (v < SP.MIN_CELL)


# ================================================================ run
def task(n):
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    b5, psn5, _ = C.designs(T, n, C.P5DX)
    t = T.t
    r = np.arange(len(t))
    X1 = T.cov.iloc[r][T.demo].to_numpy(float)  # row-indexed copies, exactly as sens_primary32 / v18_embed_compare
    dx = T.X_dx[r]
    Hk = T.hd(200, t=t, rows=r)
    clin_ex = {"mean_meds", "mean_util"} | {f"smd_obs_{c}" for c in T.phys}
    Fl, fnames, finfo = flags_matrix(T, n)
    rung = {"P1": (X1, set()), "P5": (b5[r], set()), "Flags": (np.hstack([X1, Fl]), set()),
            "hdPS200": (np.hstack([dx, Hk]), set()), "clinical": (T.X_core[r], clin_ex)}
    perm = T.shuffle_perm
    CLM = T.clm_pc
    assert CLM.shape == (len(t), 64) and np.isfinite(CLM).all()
    blk = {"ecg": T.ecg_pc, "she": T.ecg_pc[perm], "clm": CLM[r], "shc": CLM[perm][r], "c32": CLM[:, :32]}
    comp = {"base": [], "ECG": ["ecg"], "CLMBR": ["clm"], "ECG+CLMBR": ["clm", "ecg"], "shufECG": ["she"],
            "shufCLMBR": ["shc"], "CLMBR32": ["c32"]}
    out = []

    def rec(rg, cfg, arm, X, ex58):
        est, psm = CONFIGS[cfg]
        try:
            o, fail = E.run_cell(T, X, rows=r, estimator=est, ps_model=psm, cstat=None), ""
        except IndexError as e:  # empty matched set (no pair within caliper): v13_common.match returns float-typed empty arrays
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
        if rg in ("P1", "P5"):
            rec(rg, "main", "CLMBR32", np.hstack([X, blk["c32"]]), ex58)
    print(f"{n} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, secs=round(time.time() - t0, 1), **finfo)


def run(workers, trials=None):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "ontarget", "lodestar", "affirm", "insight", "declare", "east-afnet4", "aristotle",
           "rewind", "cabana-v2", "transform-hf", "precision")
    tk = sorted(trials or ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
    with Pool(min(workers, len(tk))) as p:
        res = p.map(task, tk, chunksize=1)
    R = pd.DataFrame([x for o, _ in res for x in o])
    tag = "" if trials is None else "_partial"
    R.to_parquet(OUT / f"restricted_cells{tag}.parquet")
    suppress(R).to_csv(OUT / f"cells{tag}.csv", index=False)
    (OUT / f"log{tag}.json").write_text(json.dumps([lg for _, lg in res], indent=1))
    (OUT / f"run{tag}.done").write_text(time.strftime("%Y-%m-%d %H:%M") + "\n")
    print("done", flush=True)


# ================================================================ gate
def _dev(x, y, cols):
    rows = []
    ix = x.index.intersection(y.index)
    for c in cols:
        xa, ya = x.loc[ix, c].to_numpy(float), y.loc[ix, c].to_numpy(float)
        dev = float(np.nanmax(np.abs(xa - ya))) if np.isfinite(xa - ya).any() else 0.0
        rows.append(dict(col=c, n=len(ix), n_ref=len(y), maxdev=dev, nan_mismatch=int((np.isnan(xa) ^ np.isnan(ya)).sum())))
    return rows


def gate(tag=""):
    os.umask(0o077)
    R = pd.read_parquet(OUT / f"restricted_cells{tag}.parquet")
    P = pd.read_parquet(SP.OUT / "restricted_cells.parquet")
    P = P[P.k_pcs.isin([0, 32])]
    cols = ["loghr", "se", "n", "n_t", "n_c", "n_pairs", "ess_t", "ess_c"] + [f"smd:{c}" for c in VN]
    rows = []
    for rg in SP.RUNGS:
        for cfg in CONFIGS:
            for a in SP.ARMS:
                x = R[(R.rung == rg) & (R.config == cfg) & (R.arm == a)].set_index("trial")
                y = P[(P.rung == rg) & (P.config == cfg) & (P.arm == a)].set_index("trial")
                rows += [dict(rung=rg, config=cfg, arm=a, **d) for d in _dev(x, y, cols)]
    G = pd.DataFrame(rows)
    G.to_csv(OUT / f"gate_sp32{tag}.csv", index=False)
    Q = pd.read_parquet(M18.OUT / "restricted_results_unsuppressed.parquet")
    Q = Q[Q.half == "full"]
    amap = {"base": "base", "ECG": "ECG", "CLMBR": "CLMBR", "ECG+CLMBR": "CLMBR+ECG", "shufECG": "shufECG", "shufCLMBR": "shufCLMBR"}
    rows = []
    for rg in ("P1", "P5", "hdPS200", "clinical"):
        for a, b in amap.items():
            x = R[(R.rung == rg) & (R.config == "main") & (R.arm == a)].set_index("trial")
            y = Q[(Q.rung == rg) & (Q.arm_role == b)].set_index("trial")
            rows += [dict(rung=rg, arm=a, **d) for d in _dev(x, y, ["loghr", "se", "n", "n_t", "n_c", "n_pairs"] + [f"smd:{c}" for c in VN])]
            # ex58 masking: v18 and this grid record the same clinical ex58 string?
            ix = x.index.intersection(y.index)
            rows.append(dict(rung=rg, arm=a, col="ex58_equal", n=len(ix), n_ref=len(y),
                             maxdev=float((x.loc[ix, "ex58"].fillna("") != y.loc[ix, "ex58"].fillna("")).sum()), nan_mismatch=0))
    G2 = pd.DataFrame(rows)
    G2.to_csv(OUT / f"gate_v18{tag}.csv", index=False)
    n_exp = len(set(R.trial))
    ok = bool(G.maxdev.max() <= 1e-12 and G.nan_mismatch.sum() == 0 and (G.n == n_exp).all() and (tag != "" or n_exp == 38))
    st = dict(sp32_pass=ok, sp32_maxdev=float(G.maxdev.max()), sp32_nan_mismatch=int(G.nan_mismatch.sum()),
              sp32_cells_compared=int(G.groupby(["rung", "config", "arm"]).n.max().sum()), trials=n_exp,
              v18_maxdev_numeric=float(G2[G2.col != "ex58_equal"].maxdev.max()),
              v18_nan_mismatch=int(G2.nan_mismatch.sum()), v18_ex58_mismatch=int(G2[G2.col == "ex58_equal"].maxdev.sum()),
              v18_cells_compared=int(G2[G2.col == "loghr"].n.sum()))
    (OUT / f"gate_status{tag}.json").write_text(json.dumps(st, indent=1))
    print(G.groupby(["rung", "arm"]).agg(n=("n", "max"), maxdev=("maxdev", "max"), nan=("nan_mismatch", "sum")).to_string())
    print(G2[G2.col != "ex58_equal"].groupby(["rung", "arm"]).agg(n=("n", "max"), maxdev=("maxdev", "max"), nan=("nan_mismatch", "sum")).to_string())
    print(json.dumps(st, indent=1))
    return st


# ================================================================ statistics
def bshuf2(la, lb, rb, ndraw=NDRAW):
    """two-sided analogue of sens_primary32.bshuf (same statistic and draws): 2 * min tail."""
    st = lambda q: np.mean(np.abs(la - q) - np.abs(lb - q), axis=-1)
    obs = float(st(rb))
    rng = np.random.default_rng(0)
    IX = np.array([rng.permutation(len(rb)) for _ in range(ndraw)])
    null = st(rb[IX])
    return float(min(1.0, 2 * min((null <= obs + 1e-12).mean(), (null >= obs - 1e-12).mean())))


def mask(SM, keep):
    S = SM.copy()
    S.loc[:, [c for c in S.columns if c not in keep]] = np.nan
    return S


def bal_light(Fa, Fb, SMa, SMb, trials, side, CL, full=True):
    """lt01 / mean |SMD| contrast on the item set of SMa / SMb (paired), plus the relative reduction with CI."""
    pf = SP.p1s if side == "one" else SP.p2s
    Fa, Fb = SP.paired_balance(Fa, Fb, SMa, SMb, trials)
    out = {}
    for m, sgn in (("lt01", 1), ("m58", -1)):
        a, b = Fa.loc[trials, m], Fb.loc[trials, m]
        d = sgn * (a - b)
        ok = d.notna()
        out[f"{m}_a"], out[f"{m}_b"], out[f"{m}_diff"] = a.mean(), b.mean(), (a - b).mean()
        out[f"{m}_better"] = f"{int((d > 0).sum())}/{int(ok.sum())}"
        out[f"{m}_p"] = pf(d.to_numpy())
        if full:
            cl = pd.Series(d.to_numpy(), index=[CL[KEY[t]] for t in trials]).dropna().groupby(level=0).mean()
            out[f"{m}_cluster_p"] = pf(cl.to_numpy())
            out[f"{m}_loo_max_p"] = max(pf(d.drop(t).to_numpy()) for t in trials)
    e, lo, hi, k = SP.relred_ci(Fb.loc[trials, "m58"], Fa.loc[trials, "m58"])
    out.update(relred=e, relred_lo=lo, relred_hi=hi, relred_k=k)
    return out


def contrasts():
    """(config, label, kind, rung_a, arm_a, rung_b, arm_b, side)."""
    L = []
    for cfg in CONFIGS:
        for rg in RUNGS:
            for a, b, side in (("ECG", "base", "one"), ("CLMBR", "base", "one"), ("ECG+CLMBR", "base", "one"),
                               ("ECG+CLMBR", "CLMBR", "one"), ("ECG+CLMBR", "ECG", "one"), ("CLMBR", "ECG", "two"),
                               ("shufECG", "base", "two"), ("shufCLMBR", "base", "two"),
                               ("ECG", "shufECG", "one"), ("CLMBR", "shufCLMBR", "one")):
                L.append((cfg, f"{rg}: {a} vs {b}", "within", rg, a, rg, b, side))
        for ra, aa, rb, ab in (("P1", "CLMBR", "Flags", "base"), ("P1", "CLMBR", "hdPS200", "base"), ("P5", "CLMBR", "hdPS200", "base"),
                               ("P5", "CLMBR", "clinical", "base"), ("P5", "ECG+CLMBR", "clinical", "base")):
            L.append((cfg, f"{ra}+{aa} vs {rb} {ab}", "across", ra, aa, rb, ab, "two"))
    for rg in ("P1", "P5"):
        for a, b, side in (("CLMBR32", "base", "one"), ("CLMBR32", "ECG", "two"), ("CLMBR", "CLMBR32", "two")):
            L.append(("main", f"{rg}: {a} vs {b}", "clmbr32", rg, a, rg, b, side))
    L.append(("main", "P1+CLMBR32 vs Flags base", "clmbr32", "P1", "CLMBR32", "Flags", "base", "two"))
    return L


_G = {}


def _row(args):
    sname, (cfg, lab, kind, ra, aa, rb, ab, side) = args
    F, SM, CL = _G["F"], _G["SM"], _G["CL"]
    tr = _G.get("SETS", {"S32": S32, "S38": S38})[sname]
    ka, kb = (ra, cfg, aa), (rb, cfg, ab)
    Fa, Fb = F[ka], F[kb]
    row = dict(set=sname, config=cfg, contrast=lab, kind=kind, rung_a=ra, arm_a=aa, rung_b=rb, arm_b=ab, sided=side, n_trials=len(tr))
    # 54 non-coded items (primary) + agreement
    r54 = SP.contrast_row(Fa, Fb, tr, side, CL, mask(SM[ka], NONCODED), mask(SM[kb], NONCODED))
    for k, v in r54.items():
        k2 = (k.replace("lt01_", "lt01_54_").replace("m58_", "m54_") if k.startswith(("lt01_", "m58_"))
              else k.replace("relred", "relred54") if k.startswith("relred") else k)
        row[k2] = v
    if side == "two":
        la, lb, rbv = Fa.loc[tr, "loghr"].to_numpy(), Fb.loc[tr, "loghr"].to_numpy(), Fb.loc[tr, "rb"].to_numpy()
        ok = np.isfinite(la) & np.isfinite(lb)
        row["bshuf_p"] = bshuf2(la[ok], lb[ok], rbv[ok])
    row["bshuf_sided"] = side
    la_, lb_ = Fa.loc[tr, "absd"], Fb.loc[tr, "absd"]
    okp = la_.notna() & lb_.notna()
    row.update(absd_a_pair=float(la_[okp].mean()), absd_b_pair=float(lb_[okp].mean()), n_agree_pair=int(okp.sum()))
    # 58-item panel (secondary)
    r58 = bal_light(Fa, Fb, SM[ka], SM[kb], tr, side, CL)
    row.update({(k.replace("lt01_", "lt01_58_") if k.startswith("lt01_") else k.replace("relred", "relred58") if k.startswith("relred") else k): v
                for k, v in r58.items()})
    # agreement levels
    for lab_, FF in (("a", Fa), ("b", Fb)):
        mm = SP.agree_metrics(FF.loc[tr])
        row.update({f"{lab_}_{q}": v for q, v in mm.items()})
        row[f"{lab_}_retain"] = float(_G["RET"][ka if lab_ == "a" else kb].loc[tr].mean())
    # per domain (exploratory; p without cluster / LOO)
    dom = []
    for g in DOMAINS:
        cols = [c for c in VN if GROUP[c] == g]
        d = bal_light(Fa, Fb, mask(SM[ka], cols), mask(SM[kb], cols), tr, side, CL, full=False)
        dom.append(dict(set=sname, config=cfg, contrast=lab, kind=kind, sided=side, domain=g, n_items=len(cols),
                        mean_a=d["m58_a"], mean_b=d["m58_b"], better=d["m58_better"], p=d["m58_p"],
                        lt01_a=d["lt01_a"], lt01_b=d["lt01_b"], lt01_p=d["lt01_p"],
                        relred=d["relred"], relred_lo=d["relred_lo"], relred_hi=d["relred_hi"], k=d["relred_k"]))
    return row, dom


def load_F(R):
    F, SM, RET = {}, {}, {}
    for (rg, cfg, a), g in R.groupby(["rung", "config", "arm"]):
        g = g.set_index("trial", drop=False).loc[[t for t in ALL if t in set(g.trial)]]
        F[(rg, cfg, a)], SM[(rg, cfg, a)] = SP.per_trial(g)
        RET[(rg, cfg, a)] = g.retain.mask(small_pairs(g))  # cells with 1-10 pairs excluded from retention means (B1)
    return F, SM, RET


BAL_FAM = ["m54_p", "lt01_54_p", "m58_p", "lt01_58_p"]
AGR_FAM = ["absd_p", "cons_p", "bshuf_p"]


def summarize(workers):
    from multiprocessing import Pool
    os.umask(0o077)
    st = json.loads((OUT / "gate_status.json").read_text())
    if not st["sp32_pass"]:
        raise SystemExit("gate failed; not summarising")
    R = pd.read_parquet(OUT / "restricted_cells.parquet")
    F, SM, RET = load_F(R)
    _G.update(F=F, SM=SM, CL=V.cluster_of(), RET=RET)
    jobs = [(s, c) for s in ("S32", "S38") for c in contrasts()]
    jobs.sort(key=lambda x: x[0] != "S38")  # slow S38 rows first
    with Pool(min(workers, len(jobs))) as p:
        res = p.map(_row, jobs, chunksize=1)
    S = pd.DataFrame([r for r, _ in res])
    D = pd.DataFrame([d for _, ds in res for d in ds])
    for sname in ("S32", "S38"):
        ms = S.set == sname
        for fam, cols in (("balance", BAL_FAM), ("agreement", AGR_FAM)):
            long = S.loc[ms, cols].stack(dropna=True)
            q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
            for c in cols:
                S.loc[ms, f"q_{c}_fam"] = q[c] if c in q else np.nan
        for c in BAL_FAM + AGR_FAM:
            idx = S.index[ms & S[c].notna()]
            S.loc[idx, f"q_{c}_sweep"] = E.bh_fdr(S.loc[idx, c].to_numpy())
        md_ = D.set == sname
        idx = D.index[md_ & D.p.notna()]
        D.loc[idx, "q_domain_fam"] = E.bh_fdr(D.loc[idx, "p"].to_numpy())
    order = {c: i for i, c in enumerate(dict.fromkeys(c[1] for c in contrasts()))}
    S = S.sort_values(["set", "config", "contrast"], key=lambda s: s.map(order) if s.name == "contrast" else s).reset_index(drop=True)
    S.to_csv(OUT / "sensitivity.csv", index=False)
    D.to_csv(OUT / "domains.csv", index=False)
    # per-trial aggregates (one row per trial x rung x config x arm; trial-level only)
    pt = []
    for k, Fk in F.items():
        rg, cfg, a = k
        S54 = mask(SM[k], NONCODED)
        for t in Fk.index:
            row = dict(trial=t, key=KEY[t], in_S32=t in S32, rung=rg, config=cfg, arm=a,
                       m54=float(S54.loc[t].mean()), lt01_54=float(100 * (S54.loc[t] < 0.1).sum() / S54.loc[t].notna().sum()),
                       m58=Fk.loc[t, "m58"], lt01_58=Fk.loc[t, "lt01"], absd=Fk.loc[t, "absd"], loghr=Fk.loc[t, "loghr"],
                       se=Fk.loc[t, "se"], rb=Fk.loc[t, "rb"], rs=Fk.loc[t, "rs"], ea=Fk.loc[t, "ea"], cons=Fk.loc[t, "cons"],
                       retain=float(RET[k].loc[t]))
            for g in DOMAINS:
                row[f"dom:{g}"] = float(SM[k].loc[t, [c for c in VN if GROUP[c] == g]].mean())
            pt.append(row)
    PT = pd.DataFrame(pt)
    PT = PT.merge(R[["trial", "rung", "config", "arm", "n_pairs", "n_t", "n_c"]], on=["trial", "rung", "config", "arm"], how="left")
    suppress(PT).to_csv(OUT / "per_trial.csv", index=False)
    tables()
    headline()
    print("summaries written", len(S), len(D), len(PT), flush=True)


# ================================================================ tables (markdown, aggregates)
def fmt(x, d=3):
    return "" if pd.isna(x) else (f"{x:.{d}f}" if isinstance(x, (float, np.floating)) else str(x))


def md(D, d=3):
    cols = list(D.columns)
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in D.iterrows():
        L.append("| " + " | ".join(fmt(r[c], d) for c in cols) + " |")
    return "\n".join(L)


def tables():
    S = pd.read_csv(OUT / "sensitivity.csv")
    L = ["# paper2 core tables (generated by scripts/v21/paper2_grid.py tables; source core/sensitivity.csv)\n"]
    cb = ["contrast", "m54_a", "m54_b", "relred54", "relred54_lo", "relred54_hi", "m54_better", "m54_p", "m54_cluster_p",
          "q_m54_p_fam", "lt01_54_a", "lt01_54_b", "lt01_54_p", "relred58", "relred58_lo", "relred58_hi", "m58_p"]
    ca = ["contrast", "absd_a", "absd_b", "absd_better", "absd_p", "absd_cluster_p", "absd_loo_max_p", "bshuf_p", "q_absd_p_fam",
          "a_r", "b_r", "a_ea", "b_ea", "a_cons", "b_cons", "a_retain", "b_retain"]
    for sname in ("S32", "S38"):
        for cfg in CONFIGS:
            q = S[(S.set == sname) & (S.config == cfg)]
            L.append(f"\n## {sname}, config {cfg}: balance (54 non-coded items primary; 58 secondary)\n\n" + md(q[cb]))
            L.append(f"\n## {sname}, config {cfg}: agreement\n\n" + md(q[ca]))
    (OUT / "tables.md").write_text("\n".join(L) + "\n")


# ================================================================ §3.4 trial labels
LABEL_NAME = {"ARISTOTLE": "aristotle", "ROCKET-AF": "rocket-af", "RE-LY": "rely", "EAST-AFNET 4": "east-afnet4", "CABANA": "cabana-v2",
              "AFFIRM": "affirm", "AF-CHF": "af-chf", "FRAIL-AF": "frail-af", "LAAOS III": "laaos3", "PROTECT AF": "protect-af",
              "RAFT-AF": "raft-af", "ACTIVE W": "active-w", "COMET": "comet", "PARADIGM-HF": "paradigm-hf-seq",
              "TRANSFORM-HF": "transform-hf", "ELITE II": "elite-ii", "EMPEROR-Preserved": "emperor-preserved-v2", "LIFE": "life",
              "ALLHAT": "allhat", "VALUE": "value", "ASCOT-BPLA": "ascot", "INSIGHT": "insight", "PLATO": "plato",
              "VALIANT": "valiant", "EMPA-REG OUTCOME": "empa-reg", "CAROLINA": "carolina", "LEADER": "leader",
              "SUSTAIN-6": "sustain6", "REWIND": "rewind", "DECLARE-TIMI 58": "declare", "CANVAS Program": "canvas",
              "TECOS": "tecos", "CARMELINA": "carmelina", "ONTARGET": "ontarget", "PRECISION": "precision", "AMPLIFY": "amplify",
              "LODESTAR": "lodestar", "PROVE IT-TIMI 22": "prove-it"}
# label domain -> held-out items (E.VARS columns). rhythm_conduction has no held-out balance item set except heart rate.
DOMAIN_ITEMS = {
    "LV_structure": [c for c in VN if GROUP[c] == "Echo: LV structure"],
    "LV_systolic_function": [c for c in VN if GROUP[c] == "Echo: LV function"] + ["smd_obs_lvef"],
    "diastolic_LA": [c for c in VN if GROUP[c] == "Echo: diastolic / LA"],
    "RV_pulmonary_congestion": [c for c in VN if GROUP[c] == "Echo: RV / pulmonary"] + ["pp_BNP__ntprobnp"],
    "rhythm_conduction": ["smd_obs_heart_rate"],
}
ECHO = [c for c in VN if GROUP[c].startswith("Echo:")]
NPERM_LAB = 10000
LAB_ARMS = ["ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"]


def load_labels():
    J = json.loads(LABELS_JSON.read_text())
    L = {}
    for x in J["labels"]:
        n = LABEL_NAME[x["trial"]]
        L[n] = dict(phys=x["physiologic"] == "yes", dom=set(x["domains"]), dom_u=set(x.get("domains_union", x["domains"])))
    assert sorted(L) == sorted(ALL), set(ALL) ^ set(L)
    return L


def perm_diff(g, lab, rng_seed=0, n=NPERM_LAB):
    """mean(g | lab) - mean(g | ~lab); two-sided label-permutation p (n draws)."""
    g, lab = np.asarray(g, float), np.asarray(lab, bool)
    ok = np.isfinite(g)
    g, lab = g[ok], lab[ok]
    if lab.sum() == 0 or (~lab).sum() == 0:
        return np.nan, np.nan, int(lab.sum()), int((~lab).sum())
    obs = g[lab].mean() - g[~lab].mean()
    rng = np.random.default_rng(rng_seed)
    null = np.empty(n)
    for j in range(n):
        p = rng.permutation(lab)
        null[j] = g[p].mean() - g[~p].mean()
    return float(obs), float((np.abs(null) >= abs(obs) - 1e-12).mean()), int(lab.sum()), int((~lab).sum())


def labels():
    from scipy.stats import spearmanr
    os.umask(0o077)
    if not LABELS_JSON.exists():
        raise SystemExit(f"{LABELS_JSON} missing")
    LB = load_labels()
    R = pd.read_parquet(OUT / "restricted_cells.parquet")
    F, SM, _ = load_F(R)
    rows, drows, srows, prow = [], [], [], []
    for cfg in CONFIGS:
        kb = ("P5", cfg, "base")
        Sb = SM[kb]
        for a in LAB_ARMS:
            ka = ("P5", cfg, a)
            Sa = SM[ka]
            msk = Sa.isna() | Sb.isna()
            Sa2, Sb2 = Sa.mask(msk), Sb.mask(msk)
            for sname, tr in (("S32", S32), ("S38", S38)):
                phys = np.array([LB[t]["phys"] for t in tr])
                gain54 = (Sb2.loc[tr, NONCODED].mean(1) - Sa2.loc[tr, NONCODED].mean(1)).to_numpy()  # > 0 = arm better
                gainlt = (100 * (Sa2.loc[tr, NONCODED] < 0.1).sum(1) / Sa2.loc[tr, NONCODED].notna().sum(1)
                          - 100 * (Sb2.loc[tr, NONCODED] < 0.1).sum(1) / Sb2.loc[tr, NONCODED].notna().sum(1)).to_numpy()
                gabs = (F[kb].loc[tr, "absd"] - F[ka].loc[tr, "absd"]).to_numpy()  # > 0 = closer to RCT
                for ep, g in (("m54 gain (base - arm mean |SMD|)", gain54), ("lt01_54 gain (pp)", gainlt), ("absd gain (closer > 0)", gabs)):
                    d, p, ny, nn = perm_diff(g, phys)
                    rr = {}
                    for grp, m_ in (("yes", phys), ("no", ~phys)):
                        tt = [t for t, k in zip(tr, m_) if k]
                        if ep.startswith("m54"):
                            e, lo, hi, k = SP.relred_ci(Sb2.loc[tt, NONCODED].mean(1), Sa2.loc[tt, NONCODED].mean(1))
                            rr.update({f"relred_{grp}": e, f"relred_{grp}_lo": lo, f"relred_{grp}_hi": hi})
                        rr[f"mean_gain_{grp}"] = float(np.nanmean(g[m_]))
                        rr[f"k_better_{grp}"] = f"{int((g[m_] > 0).sum())}/{int(np.isfinite(g[m_]).sum())}"
                    rows.append(dict(set=sname, config=cfg, arm=a, endpoint=ep, n_yes=ny, n_no=nn, diff_yes_minus_no=d, perm_p=p, **rr))
                # per domain, primary (intersection) and sensitivity (union) labels
                for src, fld in (("domains", "dom"), ("domains_union", "dom_u")):
                    for D_, items in DOMAIN_ITEMS.items():
                        lab = np.array([D_ in LB[t][fld] for t in tr])
                        g = (Sb2.loc[tr, items].mean(1) - Sa2.loc[tr, items].mean(1)).to_numpy()
                        if lab.sum() < 2:
                            d, p = (float(np.nanmean(g[lab]) - np.nanmean(g[~lab])) if lab.sum() else np.nan), np.nan
                            ny, nn = int(lab.sum()), int((~lab).sum())
                        else:
                            d, p, ny, nn = perm_diff(g, lab)
                        drows.append(dict(set=sname, config=cfg, arm=a, label_source=src, label_domain=D_, items=";".join(items),
                                          n_items=len(items), n_labelled=ny, n_not=nn, mean_gain_labelled=float(np.nanmean(g[lab])) if lab.any() else np.nan,
                                          mean_gain_not=float(np.nanmean(g[~lab])), diff=d, perm_p=p,
                                          tested=bool(lab.sum() >= 2 and D_ != "LV_structure")))
                # data-driven: Spearman of the arm's gain with residual echo imbalance under P5 base
                resid = Sb.loc[tr, ECHO].mean(1).to_numpy()
                for ep, g in (("m54 gain", gain54), ("echo gain", (Sb2.loc[tr, ECHO].mean(1) - Sa2.loc[tr, ECHO].mean(1)).to_numpy())):
                    ok = np.isfinite(g) & np.isfinite(resid)
                    rho, p = spearmanr(g[ok], resid[ok])
                    srows.append(dict(set=sname, config=cfg, arm=a, endpoint=ep, k=int(ok.sum()), spearman_rho=float(rho), p=float(p)))
                if cfg == "main" and sname == "S38":
                    for j, t in enumerate(tr):
                        prow.append(dict(trial=t, key=KEY[t], in_S32=t in S32, physiologic=LB[t]["phys"], domains=";".join(sorted(LB[t]["dom"])),
                                         arm=a, gain_m54=gain54[j], gain_lt01_54=gainlt[j], gain_absd=gabs[j],
                                         resid_echo_P5base=resid[j]))
    PH, DM = pd.DataFrame(rows), pd.DataFrame(drows)
    # audit S4: BH-FDR within label families (per set x configuration): physiologic = 5 arms x 3 endpoints; domain = tested
    # rows (5 arms x tested label domains) per label source. The permutation statistic is the ABSOLUTE gain difference.
    PH["test_statistic"] = "difference in mean absolute gain (yes - no)"
    PH["q_family"] = np.nan
    for _, g in PH.groupby(["set", "config"]):
        ix = g.index[g.perm_p.notna()]
        PH.loc[ix, "q_family"] = E.bh_fdr(PH.loc[ix, "perm_p"].to_numpy())
    DM["q_family"] = np.nan
    for _, g in DM.groupby(["set", "config", "label_source"]):
        ix = g.index[g.tested & g.perm_p.notna()]
        DM.loc[ix, "q_family"] = E.bh_fdr(DM.loc[ix, "perm_p"].to_numpy())
    PH.to_csv(OUT / "labels_physiologic.csv", index=False)
    DM.to_csv(OUT / "labels_domain.csv", index=False)
    pd.DataFrame(srows).to_csv(OUT / "labels_spearman.csv", index=False)
    pd.DataFrame(prow).to_csv(OUT / "labels_per_trial.csv", index=False)
    print("labels written", flush=True)


# ================================================================ headline extract (subset of sensitivity.csv / domains.csv)
KEYC = ["P5: ECG vs base", "P5: CLMBR vs base", "P5: ECG+CLMBR vs base", "P5: shufECG vs base", "P5: shufCLMBR vs base",
        "P5: ECG vs shufECG", "P5: CLMBR vs shufCLMBR", "P5: CLMBR vs ECG", "P5: ECG+CLMBR vs CLMBR", "P5: ECG+CLMBR vs ECG",
        "P1: CLMBR vs base", "Flags: CLMBR vs base", "Flags: ECG vs base", "hdPS200: ECG vs base", "hdPS200: CLMBR vs base",
        "clinical: ECG vs base", "clinical: CLMBR vs base", "P1+CLMBR vs Flags base", "P1+CLMBR32 vs Flags base",
        "P1+CLMBR vs hdPS200 base", "P5+CLMBR vs hdPS200 base", "P5+CLMBR vs clinical base", "P5+ECG+CLMBR vs clinical base",
        "P5: CLMBR32 vs base", "P5: CLMBR32 vs ECG"]
HCOLS = ["set", "config", "contrast", "sided", "m54_b", "m54_a", "relred54", "relred54_lo", "relred54_hi", "m54_better", "m54_p",
         "m54_cluster_p", "m54_loo_max_p", "q_m54_p_fam", "lt01_54_b", "lt01_54_a", "lt01_54_better", "lt01_54_p", "q_lt01_54_p_fam",
         "relred58", "relred58_lo", "relred58_hi", "m58_p", "q_m58_p_fam", "lt01_58_b", "lt01_58_a", "lt01_58_p",
         "absd_b", "absd_a", "absd_better", "absd_p", "absd_cluster_p", "absd_loo_max_p", "bshuf_p", "q_absd_p_fam", "q_bshuf_p_fam",
         "absd_b_pair", "absd_a_pair", "n_agree_pair", "b_r", "a_r", "b_ea", "a_ea", "b_cons", "a_cons", "cons_p", "q_cons_p_fam", "b_retain", "a_retain"]


def headline():
    os.umask(0o077)
    S = pd.read_csv(OUT / "sensitivity.csv")
    H = S[S.contrast.isin(KEYC)][HCOLS].copy()
    H["contrast"] = pd.Categorical(H.contrast, KEYC, ordered=True)
    H = H.sort_values(["set", "contrast", "config"])
    H.to_csv(OUT / "headline.csv", index=False)
    Q = S.groupby(["set", "config"]).agg(n_contrasts=("contrast", "size"),
                                          n_q05_m54=("q_m54_p_fam", lambda x: int((x < .05).sum())),
                                          n_q05_lt01_54=("q_lt01_54_p_fam", lambda x: int((x < .05).sum())),
                                          n_q05_absd=("q_absd_p_fam", lambda x: int((x < .05).sum())),
                                          n_q05_bshuf=("q_bshuf_p_fam", lambda x: int((x < .05).sum())),
                                          n_q05_cons=("q_cons_p_fam", lambda x: int((x < .05).sum()))).reset_index()
    Q.to_csv(OUT / "q_counts.csv", index=False)
    D = pd.read_csv(OUT / "domains.csv")
    D[D.contrast.isin(KEYC)].to_csv(OUT / "headline_domains.csv", index=False)  # all configurations (Figure 3 heatmap source)
    print(Q.to_string(index=False))


# ================================================================ audit S1: fairer PS-Flags (CV-tuned L2 penalty)
CV_CS = np.logspace(-4, 1, 11)
CV_CONFIGS = ["main", "m13", "overlap"]


def cv_C(X, t):
    """C chosen by 5-fold CV log-loss (sklearn LogisticRegressionCV; default unshuffled stratified folds = deterministic) on the
    standardised design, Cs = logspace(-4, 1, 11); same as review/fair_flags.py."""
    from sklearn.linear_model import LogisticRegressionCV
    from sklearn.preprocessing import StandardScaler
    Xs = StandardScaler().fit_transform(X)
    m = LogisticRegressionCV(Cs=CV_CS, cv=5, scoring="neg_log_loss", max_iter=5000, n_jobs=1).fit(Xs, t)
    return float(m.C_[0])


def cv_task(n):
    t0 = time.time()
    i = ALL.index(n)
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    t = T.t
    r = np.arange(len(t))
    X1 = T.cov.iloc[r][T.demo].to_numpy(float)
    Fl, _, finfo = flags_matrix(T, n)
    XF = np.hstack([X1, Fl])
    CLM = T.clm_pc
    des = {("FlagsCV", "base"): XF, ("FlagsCV", "CLMBR"): np.hstack([XF, CLM[r]]), ("FlagsCV", "ECG"): np.hstack([XF, T.ecg_pc]),
           ("P1CV", "CLMBR"): np.hstack([X1, CLM[r]])}
    Cs = {k: cv_C(X, t) for k, X in des.items()}
    out = []

    def rec(rg, cfg, arm, X, C):
        est = CONFIGS[cfg][0]
        try:
            o, fail = E.run_cell(T, X, rows=r, estimator=est, ps_model=("l2", C), cstat=None), ""
        except IndexError as e:
            o = dict(n=len(t), n_t=int(t.sum()), n_c=int((1 - t).sum()), n_pairs=0, loghr=np.nan, se=np.nan, ess_t=0.0, ess_c=0.0,
                     **{f"smd:{c}": np.nan for c in VN})
            fail = f"no matched pairs ({type(e).__name__})"
        small = min(o["n_t"], o["n_c"])
        out.append(dict(trial=n, key=KEY[n], idx=i, rung=rg, config=cfg, arm=arm, k_pcs=KPC.get(arm, 0), rb=T.rb, rs=T.rs, ex58="",
                        p_ps=X.shape[1], cell_failed=fail, C=C,
                        **{c: o[c] for c in ("n", "n_t", "n_c", "n_pairs", "loghr", "se", "ess_t", "ess_c")},
                        retain=(o["n_pairs"] / small) if est[0] == "match" else np.nan, **{f"smd:{c}": o[f"smd:{c}"] for c in VN}))

    for (rg, arm), X in des.items():
        for cfg in CV_CONFIGS:
            rec(rg, cfg, arm, X, Cs[(rg, arm)])
    for C in (0.1, 0.01):
        rec(f"FlagsC{C:g}", "main", "base", XF, C)
    print(f"{n} {time.time() - t0:.0f}s", flush=True)
    return out, dict(trial=n, secs=round(time.time() - t0, 1), n_flags=finfo["n_flags"],
                     **{f"C_{rg}_{arm}": c for (rg, arm), c in Cs.items()})


def cv_contrasts():
    L = []
    for cfg in CV_CONFIGS:
        L += [(cfg, "P1+CLMBR vs FlagsCV base", "flagscv", "P1", "CLMBR", "FlagsCV", "base", "two"),
              (cfg, "P1CV+CLMBR vs FlagsCV base", "flagscv", "P1CV", "CLMBR", "FlagsCV", "base", "two"),
              (cfg, "FlagsCV: CLMBR vs base", "flagscv", "FlagsCV", "CLMBR", "FlagsCV", "base", "one"),
              (cfg, "FlagsCV: ECG vs base", "flagscv", "FlagsCV", "ECG", "FlagsCV", "base", "one"),
              (cfg, "FlagsCV base vs Flags base (C=1)", "flagscv", "FlagsCV", "base", "Flags", "base", "two")]
    L += [("main", f"P1+CLMBR vs FlagsC{C} base", "flagsC", "P1", "CLMBR", f"FlagsC{C}", "base", "two") for C in ("0.1", "0.01")]
    return L


def flagscv(workers, stage):
    from multiprocessing import Pool
    os.umask(0o077)
    if stage in ("all", "run"):
        big = ("allhat", "value", "ascot", "lodestar", "ontarget", "affirm", "east-afnet4", "aristotle", "cabana-v2", "transform-hf")
        tk = sorted(ALL, key=lambda x: (x not in big, big.index(x) if x in big else 0))
        with Pool(min(workers, len(tk))) as p:
            res = p.map(cv_task, tk, chunksize=1)
        R2 = pd.DataFrame([x for o, _ in res for x in o])
        R2.to_parquet(OUT / "restricted_flagscv_cells.parquet")
        suppress(R2).to_csv(OUT / "flagscv_cells.csv", index=False)
        pd.DataFrame([lg for _, lg in res]).to_csv(OUT / "flagscv_log.csv", index=False)  # chosen C per trial x design
    if stage in ("all", "summarize"):
        R = pd.concat([pd.read_parquet(OUT / "restricted_cells.parquet"), pd.read_parquet(OUT / "restricted_flagscv_cells.parquet")],
                      ignore_index=True)
        F, SM, RET = load_F(R)
        # retention-restricted head-to-head (C = 1 PS-Flags), sets defined on PS-Flags base main retention (restricted values)
        rf = R[(R.rung == "Flags") & (R.config == "main") & (R.arm == "base")].set_index("trial").retain
        sets = {"S32": S32, "S38": S38}
        for thr in (0.5, 0.7, 0.9):
            sets[f"S32_flagsret>={thr}"] = [t for t in S32 if rf[t] >= thr]
        _G.update(F=F, SM=SM, CL=V.cluster_of(), RET=RET, SETS=sets)
        jobs = [(s, c) for s in ("S32", "S38") for c in cv_contrasts()]
        jobs += [(s, ("main", "P1+CLMBR vs Flags base", "across", "P1", "CLMBR", "Flags", "base", "two"))
                 for s in sets if s.startswith("S32_flagsret")]
        with Pool(min(workers, len(jobs))) as p:
            res = p.map(_row, jobs, chunksize=1)
        S = pd.DataFrame([r for r, _ in res])
        S.insert(1, "set_k", [len(sets[x]) for x in S["set"]])
        S.to_csv(OUT / "flagscv.csv", index=False)
        pd.DataFrame([d for _, ds in res for d in ds]).to_csv(OUT / "flagscv_domains.csv", index=False)
        print(S[["set", "set_k", "config", "contrast", "relred54", "relred54_lo", "relred54_hi", "m54_better", "m54_p", "absd_b_pair",
                 "absd_a_pair", "absd_better", "absd_p", "bshuf_p", "a_retain", "b_retain"]].round(3).to_string(index=False))


# ================================================================ audit S7: retention sensitivity
def retsens():
    from scipy.stats import spearmanr
    os.umask(0o077)
    R = pd.read_parquet(OUT / "restricted_cells.parquet")
    F, SM, RET = load_F(R)
    CL = V.cluster_of()
    rows = []
    kb = ("P5", "main", "base")
    rbase = RET[kb].loc[S32]
    for a in ("ECG", "CLMBR", "ECG+CLMBR"):
        ka = ("P5", "main", a)
        Sa, Sb = mask(SM[ka], NONCODED), mask(SM[kb], NONCODED)
        m_ = Sa.isna() | Sb.isna()
        gain = (Sb.mask(m_).mean(1) - Sa.mask(m_).mean(1)).loc[S32]
        drop = rbase - RET[ka].loc[S32]
        rho, p = spearmanr(gain, drop)
        rows.append(dict(analysis="Spearman(per-trial m54 gain, retention drop vs base)", arm=a, set="S32", k=len(S32), rho=rho, p=p))
    rcl = RET[("P5", "main", "CLMBR")].loc[S32]
    small = [t for t in S32 if rbase[t] - rcl[t] <= 0.05]
    big = [t for t in S32 if t not in small]
    for nm, tr in (("CLMBR-T retention drop <= 0.05", small), ("CLMBR-T retention drop > 0.05", big)):
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            ka = ("P5", "main", a)
            b = bal_light(F[ka], F[kb], mask(SM[ka], NONCODED), mask(SM[kb], NONCODED), tr, "one", CL, full=False)
            rows.append(dict(analysis=f"P5 {a} vs base, subset: {nm}", arm=a, set="S32 subset", k=len(tr), relred=b["relred"],
                             relred_lo=b["relred_lo"], relred_hi=b["relred_hi"], better=b["m58_better"], p=b["m58_p"]))
    for rg, a in (("P1", "base"), ("P1", "CLMBR"), ("P5", "base"), ("P5", "ECG"), ("P5", "CLMBR"), ("Flags", "base"), ("hdPS200", "base"),
                  ("clinical", "base")):
        for cfg in ("iptw", "overlap"):
            g = R[(R.rung == rg) & (R.config == cfg) & (R.arm == a)].set_index("trial").loc[S32]
            f = np.minimum(g.ess_t / g.n_t, g.ess_c / g.n_c)
            rows.append(dict(analysis=f"ESS fraction min(ess_t/n_t, ess_c/n_c), {cfg}", arm=f"{rg} {a}", set="S32", k=len(S32),
                             median=float(f.median()), min=float(f.min()), mean_absd=float(np.abs(g.loghr - g.rb).mean())))
    for rg, a in (("P5", "base"), ("P5", "ECG"), ("P5", "CLMBR"), ("P5", "ECG+CLMBR"), ("P1", "CLMBR"), ("Flags", "base"),
                  ("hdPS200", "base"), ("clinical", "base")):
        for sname, tr in (("S32", S32), ("S38", S38)):
            x = RET[(rg, "main", a)].loc[tr]
            rows.append(dict(analysis="retention (matched anchors / smaller arm), main; cells with 1-10 pairs excluded", arm=f"{rg} {a}",
                             set=sname, k=int(x.notna().sum()), mean=float(x.mean()), median=float(x.median()),
                             n_lt07=int((x < 0.7).sum())))
    D = pd.DataFrame(rows)
    D.to_csv(OUT / "retention_sens.csv", index=False)
    print(D.round(3).to_string(index=False))


# ================================================================ audit B1: privacy pass over the written aggregates
def privacy():
    """re-suppress log.json (flag_prev_max whose complement is 1-10 patients) and flags/flags_build.csv (pct_with_any_dx whose
    complement is 1-10), then scan every non-restricted csv in core/ for count columns with values 1-10 and for derived
    columns (ess_t, ess_c, retain) left unblanked in rows with suppressed n_pairs."""
    os.umask(0o077)
    suppress(pd.read_parquet(OUT / "restricted_cells.parquet")).to_csv(OUT / "cells.csv", index=False)
    if (OUT / "restricted_flagscv_cells.parquet").exists():
        suppress(pd.read_parquet(OUT / "restricted_flagscv_cells.parquet")).to_csv(OUT / "flagscv_cells.csv", index=False)
    L = json.loads((OUT / "log.json").read_text())
    for d in L:
        if d.get("flag_prev_max") is not None:
            c = int(round(d["n_keys"] * (1 - d["flag_prev_max"])))
            d["flag_prev_max_suppressed"] = bool(1 <= c < SP.MIN_CELL)
            if d["flag_prev_max_suppressed"]:
                d["flag_prev_max"] = None
    (OUT / "log.json").write_text(json.dumps(L, indent=1))
    B = pd.read_csv(FLAGS / "flags_build.csv")
    B["pct_with_any_dx_suppressed"] = False
    for j, r in B.iterrows():
        W = pd.read_parquet(FLAGS / f"restricted_flags_{r.trial}.parquet").set_index("patient_key")
        nw = int((~(W > 0).any(axis=1)).sum())
        if 1 <= nw < SP.MIN_CELL:
            B.loc[j, "pct_with_any_dx"] = np.nan
            B.loc[j, "pct_with_any_dx_suppressed"] = True
    B.to_csv(FLAGS / "flags_build.csv", index=False)
    bad = []
    for f in sorted(list(OUT.glob("*.csv")) + list(FLAGS.glob("*.csv"))):
        D = pd.read_csv(f, low_memory=False)
        for c in ("n", "n_t", "n_c", "n_pairs"):
            if c in D:
                v = pd.to_numeric(D[c], errors="coerce")
                k = int(((v >= 1) & (v < SP.MIN_CELL)).sum())
                if k:
                    bad.append((f.name, c, k))
        if "n_pairs" in D:
            sup = D.get("suppressed_lt11", pd.Series(False, index=D.index)).astype(bool)
            for c in DERIVED:
                if c in D and D.loc[sup, c].notna().any():
                    bad.append((f.name, c, int(D.loc[sup, c].notna().sum())))
    print("privacy scan:", "CLEAN" if not bad else bad)
    (OUT / "privacy_scan.json").write_text(json.dumps(dict(clean=not bad, issues=bad, time=time.strftime("%Y-%m-%d %H:%M")), indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "gate", "summarize", "labels", "tables", "headline", "flagscv", "retsens", "privacy"])
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--trials", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--stage", default="all", choices=["all", "run", "summarize"])
    a = ap.parse_args()
    trials = [x for x in a.trials.split(",") if x] or None
    {"run": lambda: run(a.workers, trials), "gate": lambda: gate(a.tag), "summarize": lambda: summarize(a.workers),
     "labels": labels, "tables": tables, "headline": headline,
     "flagscv": lambda: flagscv(a.workers, a.stage), "retsens": retsens, "privacy": privacy}[a.cmd]()
