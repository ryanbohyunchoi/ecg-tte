#!/usr/bin/env python
"""paper2 step C (HANDOFF_PAPER2.md §3.5): the v2.0 G2 plasmode (scripts/v20/g2b_simulation_ext.py, docs/v20/G2_EXTENSION.md)
with PS-CVD5 (rung P5) and CLMBR-T arms, on the same cells, seeds, grid and replicates as the paper's primary plasmode
design: treatment driven by the withheld confounder C only ("trtC"), clinically oriented (LVEF and eGFR sign-flipped:
trtC_adv for LVEF / eGFR, trtC for NT-proBNP / BMI, = g2b pooled_trtC_cliniorient).

New arms (C is in none of them):
  P5            PS-CVD5 = demographics + hypertension, T2D, CAD, AF, HF (v18_clmbr.designs(T, n, P5DX), as sens_primary32)
  P5ECG         P5 + 32 ECG PCs (T.ecg_pc)
  P5CLMBR       P5 + 64 CLMBR-T PCs (T.clm_pc)
  P5ECGCLMBR    P5 + ECG + CLMBR-T
  CLMBRonly     64 CLMBR-T PCs only
  P5shufCLMBR   P5 + permuted CLMBR-T (T.clm_pc[T.shuffle_perm]; placebo, addition logged in docs/v21/PLASMODE_PAPER2.md)
Existing trtC arms (unmatched, base = demographic PS, ECG, ECGonly, shufECGonly, oracle) are taken from g2b's
reps_trtC.csv / reps_trtC_adv.csv after an exact reproduction gate; all arms share subsamples, treatments and outcome
uniforms (the random streams are keyed by replicate / trial / confounder / scenario, never by arm).

Usage: paper2_plasmode.py prep | gate | run [--workers 24] | summarize
Outputs (aggregates only, umask 077): /mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/plasmode/
  cache/restricted_p5_<trial>.npz (restricted design matrices), reps_<variant>_p5.csv (replicate-level aggregates,
  counts 1-10 suppressed), gate.csv, pooled_*.csv, performance_*.csv, added_value_p5.csv, retention_p5.csv, r2_p5.csv.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v20"))
sys.path.insert(0, str(HERE.parent / "v19"))
sys.path.insert(0, str(HERE.parent / "v18"))
sys.path.insert(0, str(HERE.parent))
import g2b_simulation_ext as G2B  # noqa: E402  (imported, never modified; we only call its pure functions)

G2 = G2B.G2
from v13_common import A, cox, match, ps_logit  # noqa: E402

OUT = A / "claude-v21-paper2" / "plasmode"
CX = OUT / "cache"
CONF = G2.CONF
OLD_ARMS = list(G2B.VARIANTS["trtC"]["arms"])  # unmatched, base, ECG, ECGonly, shufECGonly, oracle
NEW_ARMS = ["P5", "P5ECG", "P5CLMBR", "P5ECGCLMBR", "CLMBRonly", "P5shufCLMBR"]
ALL_ARMS = OLD_ARMS + NEW_ARMS
LAB = {**G2B.LAB, "P5": "PS-CVD5", "P5ECG": "PS-CVD5 + ECG", "P5CLMBR": "PS-CVD5 + CLMBR-T", "P5ECGCLMBR": "PS-CVD5 + ECG + CLMBR-T",
       "CLMBRonly": "CLMBR-T only", "P5shufCLMBR": "PS-CVD5 + permuted CLMBR-T"}
# primary design = clinically oriented trtC: (g2b variant, confounders taken from it)
DESIGN = {"trtC_adv": ["lvef", "egfr"], "trtC": ["ntprobnp", "bmi"]}
GATE_CELLS = {"trtC_adv": [("comet", "lvef"), ("aristotle", "lvef"), ("plato", "egfr")],
              "trtC": [("aristotle", "bmi"), ("affirm", "ntprobnp"), ("comet", "ntprobnp")]}
MIN_CELL = 11
P = {}


def status(msg):
    os.umask(0o077)
    with open(A / "claude-v21-paper2" / "STATUS.md", "a") as f:
        f.write(f"- {time.strftime('%Y-%m-%d %H:%M')} [C] {msg}\n")


# ---------------------------------------------------------------- prep: P5 and CLMBR-T matrices per trial
def prep_one(n):
    import v18_af_confirm as AF
    import v18_clmbr as C
    E = AF.V.E
    _, OLD, _ = G2.trial_list()
    T = E.load_trial(n) if n in OLD else E.load_trial(n, cache=False)
    D = dict(np.load(G2.CACHE / f"restricted_prep_{n}.npz"))
    X = dict(np.load(G2B.CX / f"restricted_ext_{n}.npz"))
    # identity checks against the v1.9 and v2.0 caches (same patients, same order)
    same = (np.array_equal(D["demo"], T.cov[T.demo].to_numpy(float)) and np.array_equal(D["ecg"], T.ecg_pc.astype(float))
            and np.array_equal(D["shuf"], T.ecg_pc[T.shuffle_perm].astype(float)) and np.array_equal(X["dx"], T.X_dx.astype(float)))
    if not same:
        raise RuntimeError(f"{n}: v1.9 / v2.0 cache does not match the reloaded trial")
    b5, psn5, hf = C.designs(T, n, C.P5DX)
    clm = np.asarray(T.clm_pc, float)
    if clm.shape != (len(T.t), 64) or not np.isfinite(clm).all() or not np.isfinite(b5).all():
        raise RuntimeError(f"{n}: P5 / CLMBR-T matrix not finite or wrong shape")
    os.umask(0o077)
    CX.mkdir(parents=True, exist_ok=True)
    np.savez(CX / f"restricted_p5_{n}.npz", p5=b5.astype(float), clm=clm, shufclm=clm[T.shuffle_perm], p5_names=np.array(psn5))
    # real-data cross-fitted R² of Cz (as v1.9: Cz standardised in S) on each representation, eligible cells only
    P_ = pd.read_csv(G2B.V19 / "prep_conf.csv")
    r2 = []
    for c in P_[(P_.trial == n) & P_.eligible].conf:
        rows, cz = D[f"{c}__rows"], D[f"{c}__cz"]
        d = dict(trial=n, conf=c, n_s=len(rows))
        for lab, M in (("p5", b5), ("clm", clm), ("ecg", D["ecg"]), ("p5_ecg", np.hstack([b5, D["ecg"]])),
                       ("p5_clm", np.hstack([b5, clm])), ("p5_ecg_clm", np.hstack([b5, D["ecg"], clm])),
                       ("shufclm", clm[T.shuffle_perm])):
            d[f"r2_{lab}"] = G2.cv_r2(M[rows], cz)
        r2.append(d)
    info = dict(trial=n, n_p5=b5.shape[1], p5_names=";".join(psn5), hf_col=hf, n_clm=clm.shape[1])
    print(n, info["n_p5"], hf, flush=True)
    return info, r2


def prep(workers):
    from multiprocessing import Pool
    Pc = pd.read_csv(G2B.V19 / "prep_conf.csv")
    trials = sorted(Pc[Pc.eligible].trial.unique())
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(min(workers, len(trials))) as p:
        res = p.map(prep_one, trials, chunksize=1)
    pd.DataFrame([i for i, _ in res]).to_csv(OUT / "prep_p5.csv", index=False)
    pd.DataFrame([x for _, r in res for x in r]).to_csv(OUT / "r2_p5.csv", index=False)
    status(f"prep done: P5 + CLMBR-T matrices for {len(trials)} trials, cache identity checks passed")


# ---------------------------------------------------------------- simulation (= g2b.one, with the P5 / CLMBR-T blocks)
def load_p5(n):
    if n not in P:
        P.clear()
        P[n] = dict(np.load(CX / f"restricted_p5_{n}.npz"))
    return P[n]


def one(job):
    """Identical to g2b_simulation_ext.one (same seeds, same order of draws) except that the arm list is a job argument
    and the P5 / CLMBR-T blocks are added. Gated against g2b's reps for the existing arms."""
    n, c, rep, info, variant, arms = job
    from scipy.optimize import brentq
    from scipy.special import expit
    V = G2B.VARIANTS[variant]
    D, X = G2B.load(n)
    Si, cz, lpd, lpc = D[f"{c}__rows"], D[f"{c}__cz"], D[f"{c}__lpd"], D[f"{c}__lpc"]
    if V.get("sign") == "adverse":
        cz = G2B.ADV_SIGN[c] * cz
    lam0, rho = info["lam"], info["rho"]
    alpha = {float(k): v for k, v in json.loads(info["alpha"]).items()}
    if not V["trt_demo"]:
        alpha = {o: brentq(lambda a: expit(a + np.log(o) * cz).mean() - info["pbar"], -30, 30) for o in G2B.OR_ALL}
    ti, ci = info["idx"], list(CONF).index(c)
    N = len(Si)
    sub = np.sort(np.random.default_rng([50_000 + rep, ti, ci]).choice(N, int(round(G2.FRAC * N)), replace=False))
    rows = Si[sub]
    czs, lpds, lpcs, Cadm = cz[sub], lpd[sub], lpc[sub], D["Cadm"][rows]
    if not V["trt_demo"]:
        lpds = np.zeros_like(lpds)
    X1, ecg = D["demo"][rows], D["ecg"][rows]
    blocks = {"base": lambda t: X1, "ECG": lambda t: np.hstack([X1, ecg]), "oracle": lambda t: np.column_stack([X1, czs]),
              "ECGonly": lambda t: ecg, "shufECGonly": lambda t: D["shuf"][rows]}
    if any(a in NEW_ARMS for a in arms):
        Q = load_p5(n)
        p5, clm, shc = Q["p5"][rows], Q["clm"][rows], Q["shufclm"][rows]
        blocks.update({"P5": lambda t: p5, "P5ECG": lambda t: np.hstack([p5, ecg]), "P5CLMBR": lambda t: np.hstack([p5, clm]),
                       "P5ECGCLMBR": lambda t: np.hstack([p5, ecg, clm]), "CLMBRonly": lambda t: clm,
                       "P5shufCLMBR": lambda t: np.hstack([p5, shc])})
    scen = V["scen"]
    out = []
    for orr in sorted(set(s[0] for s in scen)):
        oi = G2B.OR_ALL.index(orr)
        trt = (np.random.default_rng([60_000 + rep, ti, ci, oi]).uniform(size=len(rows)) <
               expit(alpha[orr] + lpds + np.log(orr) * czs)).astype(int)
        if min(trt.sum(), (1 - trt).sum()) < 50:
            continue
        M = {}
        for a in arms:
            if a == "unmatched":
                M[a] = (np.arange(len(rows)), None)
            else:
                idx, cl, _ = match(ps_logit(blocks[a](trt), trt), trt)
                M[a] = (idx, cl)
        for hry in [s[1] for s in scen if s[0] == orr]:
            hi = G2.HRS.index(hry) if hry in G2.HRS else -1
            lam = lam0 / float(np.mean(np.exp(np.log(hry) * cz)))
            lp0 = lpcs + np.log(hry) * czs
            u = np.random.default_rng([70_000 + rep, ti, ci, oi, hi + 1]).uniform(size=len(rows))
            tt, ee = G2.simulate(lp0 + np.log(V["true_hr"]) * trt, lam, rho, Cadm, u)
            U = np.random.default_rng([80_000 + rep, ti, ci, oi, hi + 1]).uniform(size=(G2.COPIES, len(rows)))
            for a, (idx, cl) in M.items():
                b, se = cox(tt[idx], ee[idx], trt[idx], cluster=cl)
                ts, es, xs = [], [], []
                for k in range(G2.COPIES):
                    for x in (0, 1):
                        t_, e_ = G2.simulate(lp0[idx] + np.log(V["true_hr"]) * x, lam, rho, Cadm[idx], U[k, idx])
                        ts.append(t_); es.append(e_); xs.append(np.full(len(idx), x))
                tr = G2.cox_fast(np.concatenate(ts), np.concatenate(es), np.concatenate(xs))
                out.append(dict(trial=n, conf=c, or_t=orr, hr_y=hry, rep=rep, arm=a, loghr=b, se=se, truth=tr,
                                n_an=len(idx), n_t=int(trt[idx].sum()), events=int(ee[idx].sum()), n_sub=len(rows)))
    return out


def suppress(R):
    R = R.copy()
    flag = np.zeros(len(R), bool)
    for c in ("n_an", "n_t", "events", "n_sub"):
        b = (R[c] >= 1) & (R[c] < MIN_CELL)
        flag |= b.to_numpy()
        R[c] = R[c].astype(float)
        R.loc[b, c] = np.nan
    R["suppressed_lt11"] = flag
    return R


def roundtrip(R):
    buf = io.StringIO()
    R.to_csv(buf, index=False)
    buf.seek(0)
    return pd.read_csv(buf, float_precision="round_trip")


# ---------------------------------------------------------------- gate
def gate(workers):
    """Existing trtC arms recomputed with this code must equal g2b reps_trtC.csv / reps_trtC_adv.csv exactly."""
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    info = G2B.cells()
    res = []
    for variant, pick in GATE_CELLS.items():
        ref = pd.read_csv(G2B.OUT / f"reps_{variant}.csv", float_precision="round_trip")
        jobs = [(n, c, rep, info[(n, c)], variant, OLD_ARMS) for (n, c) in pick for rep in range(3)]
        with Pool(min(workers, len(jobs))) as p:
            R = pd.DataFrame([x for o in p.map(one, jobs) for x in o]).drop(columns="n_sub")
        R = roundtrip(R)
        key = ["trial", "conf", "or_t", "hr_y", "rep", "arm"]
        sel = ref.merge(R[key].drop_duplicates()[["trial", "conf", "rep"]].drop_duplicates(), on=["trial", "conf", "rep"])
        m = R.merge(ref, on=key, suffixes=("", "_ref"))
        dev = {v: float(np.nanmax(np.abs(m[v] - m[f"{v}_ref"]))) for v in ("loghr", "se", "truth", "n_an", "n_t", "events")}
        nan_ok = all((m[v].isna() == m[f"{v}_ref"].isna()).all() for v in ("loghr", "se", "truth"))
        ok = len(m) == len(R) == len(sel) and all(d == 0 for d in dev.values()) and nan_ok
        print(variant, "rows", len(R), "ref rows", len(sel), "matched", len(m), "max |dev|", dev, "PASS" if ok else "FAIL", flush=True)
        res.append(dict(variant=variant, cells=";".join(f"{a}x{b}" for a, b in pick), reps=3, rows=len(R), ref_rows=len(sel), matched=len(m),
                        **{f"maxdev_{k}": v for k, v in dev.items()}, nan_pattern_equal=nan_ok, passed=ok))
    G = pd.DataFrame(res)
    G.to_csv(OUT / "gate.csv", index=False)
    if not G.passed.all():
        status("GATE FAILED: existing trtC arms do not reproduce claude-v20-g2-ext reps exactly; see plasmode/gate.csv. Branch stopped.")
        raise SystemExit("reproduction gate failed")
    status(f"gate PASSED: {int(G.rows.sum())} rows ({', '.join(G.variant)}; 6 cells x 3 reps x 10 scenarios x 6 arms) "
           "reproduce claude-v20-g2-ext reps exactly (max |dev| 0)")


# ---------------------------------------------------------------- run
def run(workers, reps=50):
    from multiprocessing import Pool
    os.umask(0o077)
    if not (OUT / "gate.csv").exists() or not pd.read_csv(OUT / "gate.csv").passed.all():
        raise SystemExit("run the gate first (it must pass)")
    info = G2B.cells()
    status(f"run started: arms {','.join(NEW_ARMS)}; {workers} workers")
    for variant, confs in DESIGN.items():
        cl = {k: v for k, v in info.items() if k[1] in confs}
        jobs = [(n, c, rep, cl[(n, c)], variant, NEW_ARMS) for (n, c) in cl for rep in range(reps)]
        t0 = time.time()
        res = []
        with Pool(workers) as p:
            for k, o in enumerate(p.imap(one, jobs, chunksize=4)):
                res.extend(o)
                if k % 200 == 0:
                    print(f"{variant} {k}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
        R = pd.DataFrame(res)
        S = suppress(R)
        S.to_csv(OUT / f"reps_{variant}_p5.csv", index=False)
        print("done", variant, len(R), f"{time.time() - t0:.0f}s", "suppressed rows", int(S.suppressed_lt11.sum()), flush=True)
        status(f"run {variant} done: {len(cl)} cells x {reps} reps, {len(R)} estimates, {time.time() - t0:.0f}s")


# ---------------------------------------------------------------- summaries
def combined():
    parts = []
    for variant, confs in DESIGN.items():
        old = pd.read_csv(G2B.OUT / f"reps_{variant}.csv")
        new = pd.read_csv(OUT / f"reps_{variant}_p5.csv")
        old, new = old[old.conf.isin(confs)], new[new.conf.isin(confs)]
        # same subsample per (trial, conf, rep): attach n_sub to the old arms for the retention table
        ns = new.groupby(["trial", "conf", "rep"]).n_sub.first()
        old = old.join(ns, on=["trial", "conf", "rep"])
        parts += [old, new.drop(columns="suppressed_lt11")]
    return pd.concat(parts, ignore_index=True)


def added(S, pairs):
    out = []
    for lab in ("raw", "null-corrected"):
        for conf in list(CONF) + ["all"]:
            s = S[(S.analysis == lab) & (S.conf == conf)].set_index("arm")
            for ref, arm, what in pairs:
                if ref in s.index and arm in s.index:
                    out.append(dict(analysis=lab, conf=conf, contrast=what, ref_arm=ref, arm=arm,
                                    ref_pct_vs_unm=s.loc[ref, "pct_vs_unmatched"], arm_pct_vs_unm=s.loc[arm, "pct_vs_unmatched"],
                                    added_pct_of_ref_bias=s.loc[arm, f"pct_vs_{ref}"], mcse=s.loc[arm, f"mcse_vs_{ref}"]))
    return pd.DataFrame(out)


PAIRS = [("P5", "P5ECG", "ECG over P5"), ("P5", "P5CLMBR", "CLMBR-T over P5"), ("P5", "P5ECGCLMBR", "ECG+CLMBR-T over P5"),
         ("P5CLMBR", "P5ECGCLMBR", "ECG over P5+CLMBR-T"), ("P5ECG", "P5ECGCLMBR", "CLMBR-T over P5+ECG"),
         ("P5", "P5shufCLMBR", "permuted CLMBR-T over P5 (placebo)"), ("base", "ECG", "ECG over demographic PS"),
         ("base", "P5", "CVD5 diagnoses over demographic PS")]


def summarize():
    os.umask(0o077)
    R0 = combined()
    R = G2B.errs(R0)
    S, Pf = G2B.pooled(R, ALL_ARMS, ref_arms=("unmatched", "base", "P5", "P5ECG", "P5CLMBR"))
    S.to_csv(OUT / "pooled_trtC_cliniorient_p5.csv", index=False)
    Pf.to_csv(OUT / "performance_trtC_cliniorient_p5.csv", index=False)
    Ad = added(S, PAIRS)
    Ad.to_csv(OUT / "added_value_p5.csv", index=False)
    # consistency check: the existing arms' pooled results equal g2b pooled_trtC_cliniorient.csv
    ref = pd.read_csv(G2B.OUT / "pooled_trtC_cliniorient.csv")
    m = S.merge(ref, on=["analysis", "conf", "arm"], suffixes=("", "_ref"))
    chk = {c: float(np.nanmax(np.abs(m[c] - m[f"{c}_ref"]))) for c in ("pct_vs_unmatched", "pct_vs_base", "mean_bias")}
    print("existing-arm pooled vs g2b pooled_trtC_cliniorient: rows", len(m), "of", len(ref), "max |dev|", chk, flush=True)
    # null scenario check and retention (matched share of the replicate subsample), aggregates only
    nul = R[R.or_t == 1.0].groupby("arm").agg(null_bias=("err", "mean"), null_coverage=("cover", "mean")).reindex(ALL_ARMS)
    nul["null_coverage"] *= 100
    ret = R.assign(ret=R.n_an / R.n_sub).groupby(["conf", "arm"]).ret.mean().unstack(0).reindex(ALL_ARMS)
    ret["all"] = R.assign(ret=R.n_an / R.n_sub).groupby("arm").ret.mean().reindex(ALL_ARMS)
    ret = (100 * ret).round(2)
    nul.round(4).to_csv(OUT / "null_check_p5.csv")
    ret.to_csv(OUT / "retention_p5.csv")
    pd.DataFrame([dict(check="existing-arm pooled vs g2b pooled_trtC_cliniorient", rows=len(m), ref_rows=len(ref),
                       **{f"maxdev_{k}": v for k, v in chk.items()})]).to_csv(OUT / "summary_check.csv", index=False)
    pd.set_option("display.width", 250)
    for lab in ("raw", "null-corrected"):
        t = S[S.analysis == lab].pivot(index="arm", columns="conf", values="pct_vs_unmatched").reindex(ALL_ARMS)[list(CONF) + ["all"]]
        print(f"\n% of C-induced bias removed vs unmatched ({lab})\n", t.round(1).to_string())
    print("\nadded value (null-corrected)\n", Ad[Ad.analysis == "null-corrected"].pivot(index="contrast", columns="conf",
                                                                                     values="added_pct_of_ref_bias")[list(CONF) + ["all"]].round(1).to_string())
    print("\nperformance (all)\n", Pf[Pf.conf == "all"].round(3).to_string())
    print("\nnull check\n", nul.round(4).to_string(), "\nretention %\n", ret.to_string())
    status("summarize done: pooled_trtC_cliniorient_p5.csv, added_value_p5.csv, performance_trtC_cliniorient_p5.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "gate", "run", "summarize"])
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--reps", type=int, default=50)
    a = ap.parse_args()
    os.umask(0o077)
    if a.workers > 24:
        raise SystemExit("at most 24 workers")
    {"prep": lambda: prep(a.workers), "gate": lambda: gate(a.workers), "run": lambda: run(a.workers, a.reps),
     "summarize": summarize}[a.cmd]()
