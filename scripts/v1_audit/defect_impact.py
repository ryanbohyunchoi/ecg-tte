#!/usr/bin/env python
"""Version 1 defect-impact audit for paper2.md (docs/v1_audit/DEFECT_IMPACT.md).

Re-uses version 1 code unchanged: scripts/v21/paper2_grid.py (P2) and scripts/v20/sens_primary32.py (SP) are imported,
never edited. Every re-analysis below works from the saved paper2 cells (audits/claude-v21-paper2/core/
restricted_cells.parquet, restricted_flagscv_cells.parquet: per trial x rung x configuration x arm, 58 held-out |SMD|,
log HR, SE, ESS) except the gate and the leakage correlation check, which reload trials with the version 1 loader.

Subcommands (all write only to OUT = audits/claude-v1-audit/defects/, umask 077):
  gate       cell-level: refit PROTECT AF P5 x main x {base, ECG}, Flags x main x base and FlagsCV x main x base from
             scratch and compare with the saved paper2 cells (<= 1e-12); summary-level: recompute the paper2 row
             "P5: ECG vs base" (S32, main) with P2._row and compare with core/sensitivity.csv; also in-sample C statistic
             of PS-Flags (C = 1) in PROTECT AF and CV-chosen C for 3 trials vs flagscv_log.csv.
  leakcheck  data-driven check of the derived leakage masks: within-trial Spearman between each of the 54 held-out
             items (observed values) and each PS-Clinical input; eGFR vs CKD-EPI 2021 recomputed from the PS inputs
             (creatinine, age, sex); hdPS top-200 rx_/px_ level counts. 38 trials, aggregates only.
  sweep      the full paper2 contrast sweep (337 rows per set) with leakage-clean masks ("clean") on S32 / S35 / S38 and
             with the original masks ("orig") on S35; BH-FDR within set exactly as paper2 (balance and agreement families);
             plus clinical rows with BUN, LVESVi and GLS also masked ("clean+soft").
  extras     defect 2 (shrinkage decomposition of the agreement gains), 4 (IPTW effective sample size), 6 (labels and
             quality strata on S35 / R2 tiers; flagscv on S35), 7 (global FDR family over sweep + domain + label p).
Aggregates only. Counts 1-10 are never written (per-trial rows are not written to the repository at all).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "v21"))
sys.path.insert(0, str(HERE.parent / "v20"))
sys.path.insert(0, str(HERE.parent / "v18"))
sys.path.insert(0, str(HERE.parent))
import paper2_grid as P2  # noqa: E402

SP, E, V, C, AF = P2.SP, P2.E, P2.V, P2.C, P2.AF
CORE = P2.OUT
OUT = SP.A / "claude-v1-audit" / "defects"
VN, GROUP, NONCODED, KEY, ALL = P2.VN, P2.GROUP, P2.NONCODED, P2.KEY, P2.ALL
S32, S38 = P2.S32, P2.S38
CODED4 = ["mean_meds", "mean_util", "B_mean", "smd_prog_full"]
OBS9 = [f"smd_obs_{c}" for c in ("lvef", "sbp", "dbp", "heart_rate", "bmi", "creatinine", "potassium", "sodium", "hemoglobin")]
CLIN_NEAR = ["pp_LAB__egfr", "pp_LVFUNC__ef", "pp_LVFUNC__lv_sys_grade"]  # derived here; = R2 rule set for S3 on the 54 items
CLIN_SOFT = ["pp_LAB__bun", "pp_LVSTRUCT__lvesvi", "pp_LVFUNC__gls"]
MAXW = 16


def r2_show(path):
    return subprocess.run(["git", "-C", str(ROOT), "show", f"r2:{path}"], capture_output=True, text=True, check=True).stdout


def s35():
    """R2 blind re-audit primary set (tiers A-C), read from the r2 branch without checking it out."""
    J = json.loads(r2_show("docs/r2/QUALITY_R2.json"))
    keep = {P2.LABEL_NAME[t["trial"]] for t in J["trials"] if t["primary"]}
    out = [t for t in ALL if t in keep]
    assert len(out) == 35
    return out


def r2_tier():
    J = json.loads(r2_show("docs/r2/QUALITY_R2.json"))
    return {P2.LABEL_NAME[t["trial"]]: t["tier"] for t in J["trials"]}


# ================================================================ masks
def masks(variant):
    """item masks per rung and per arm block; a cell's mask = rung mask | arm mask (placebos take the real arm's mask).
    variant 'orig' = paper2 as run (nothing beyond ex58, already in the cells); 'clean' = derived leakage-clean map;
    'clean+soft' = clean plus the strongest measured-value correlates of PS-Clinical inputs (BUN ~ creatinine,
    LVESVi and GLS ~ LVEF; leakcheck median |rho| 0.49 / 0.75 / 0.61)."""
    if variant == "orig":
        return {r: set() for r in P2.RUNGS}, {}
    rung = {"P1": set(), "P5": {"B_mean", "smd_prog_full"}, "Flags": {"B_mean", "smd_prog_full"},
            "FlagsCV": {"B_mean", "smd_prog_full"}, "FlagsC0.1": {"B_mean", "smd_prog_full"},
            "FlagsC0.01": {"B_mean", "smd_prog_full"}, "P1CV": set(),
            "hdPS200": set(CODED4), "clinical": set(CODED4) | set(OBS9) | set(CLIN_NEAR)}
    if variant == "clean+soft":
        rung["clinical"] |= set(CLIN_SOFT)
    arm = {"CLMBR": set(CODED4), "ECG+CLMBR": set(CODED4), "shufCLMBR": set(CODED4), "CLMBR32": set(CODED4)}
    return rung, arm


def apply_masks(SM, variant):
    rm, am = masks(variant)
    out = {}
    for k, S in SM.items():
        rg, cfg, a = k
        m = rm.get(rg, set()) | am.get(a, set())
        S = S.copy()
        if m:
            S.loc[:, [c for c in S.columns if c in m]] = np.nan
        out[k] = S
    return out


# ================================================================ gate
def gate():
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    n = "protect-af"
    R = pd.read_parquet(CORE / "restricted_cells.parquet")
    RC = pd.read_parquet(CORE / "restricted_flagscv_cells.parquet")
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    b5, _, _ = C.designs(T, n, C.P5DX)
    t = T.t
    r = np.arange(len(t))
    X1 = T.cov.iloc[r][T.demo].to_numpy(float)
    Fl, _, _ = P2.flags_matrix(T, n)
    XF = np.hstack([X1, Fl])
    cols = ["loghr", "se", "n", "n_t", "n_c", "n_pairs", "ess_t", "ess_c"] + [f"smd:{c}" for c in VN]
    rows = []
    cvlog = pd.read_csv(CORE / "flagscv_log.csv").set_index("trial")
    for rg, arm, X, ref, psm in (("P5", "base", b5[r], R, ("l2", 1.0)), ("P5", "ECG", np.hstack([b5[r], T.ecg_pc]), R, ("l2", 1.0)),
                                 ("Flags", "base", XF, R, ("l2", 1.0)),
                                 ("FlagsCV", "base", XF, RC, ("l2", float(cvlog.loc[n, "C_FlagsCV_base"])))):
        est = SP.CONFIGS["main"][0]
        try:
            o = E.run_cell(T, X, rows=r, estimator=est, ps_model=psm, cstat=None)
        except IndexError:
            o = dict(n=len(t), n_t=int(t.sum()), n_c=int((1 - t).sum()), n_pairs=0, loghr=np.nan, se=np.nan, ess_t=0.0, ess_c=0.0,
                     **{f"smd:{c}": np.nan for c in VN})
        y = ref[(ref.trial == n) & (ref.rung == rg) & (ref.config == "main") & (ref.arm == arm)].iloc[0]
        dev, nanmm = 0.0, 0
        for c in cols:
            a_, b_ = float(o[c]), float(y[c])
            if np.isnan(a_) ^ np.isnan(b_):
                nanmm += 1
            elif np.isfinite(a_):
                dev = max(dev, abs(a_ - b_))
        rows.append(dict(level="cell", what=f"{n} {rg} main {arm}", n_values=len(cols), maxdev=dev, nan_mismatch=nanmm,
                         passed=bool(dev <= 1e-12 and nanmm == 0)))
    # in-sample C statistic of PS-Flags C = 1 (claim: 1.00 in PROTECT AF)
    from sklearn.metrics import roc_auc_score
    from v13_common import ps_logit
    lg = ps_logit(XF, t, model="l2", C=1.0)
    auc = float(roc_auc_score(t, lg))
    lg5 = ps_logit(b5[r], t, model="l2", C=1.0)
    rows.append(dict(level="claim", what="PROTECT AF in-sample C statistic, PS-Flags C = 1", value=round(auc, 4),
                     ref="paper2: 1.00", passed=bool(round(auc, 2) == 1.0)))
    rows.append(dict(level="claim", what="PROTECT AF in-sample C statistic, PS-CVD5 C = 1 (context)", value=round(float(roc_auc_score(t, lg5)), 4)))
    # CV-chosen C for the Flags design (3 trials, smallest cohorts) vs flagscv_log.csv
    for m in ("protect-af", "raft-af", "valiant"):
        Tm = E.load_trial(m) if m in AF.V.OLD else E.load_trial(m, cache=False)
        rm = np.arange(len(Tm.t))
        Fm, _, _ = P2.flags_matrix(Tm, m)
        cv = P2.cv_C(np.hstack([Tm.cov.iloc[rm][Tm.demo].to_numpy(float), Fm]), Tm.t)
        ref = float(cvlog.loc[m, "C_FlagsCV_base"])
        rows.append(dict(level="claim", what=f"CV-chosen C, PS-Flags, {m}", value=cv, ref=ref, passed=bool(abs(cv - ref) < 1e-12)))
    # summary-level: P5 ECG vs base, S32, main
    F, SM, RET = P2.load_F(R)
    P2._G.update(F=F, SM=SM, CL=V.cluster_of(), RET=RET, SETS={"S32": S32, "S38": S38})
    job = [c for c in P2.contrasts() if c[0] == "main" and c[1] == "P5: ECG vs base"][0]
    row, _ = P2._row(("S32", job))
    S = pd.read_csv(CORE / "sensitivity.csv")
    ref = S[(S.set == "S32") & (S.config == "main") & (S.contrast == "P5: ECG vs base")].iloc[0]
    dev, k = 0.0, 0
    for c, v in row.items():
        if c in ref and isinstance(v, (float, int, np.floating, np.integer)) and not isinstance(v, bool) and np.isfinite(v) and np.isfinite(ref[c]):
            dev, k = max(dev, abs(float(v) - float(ref[c]))), k + 1
    rows.append(dict(level="summary", what="S32 main 'P5: ECG vs base' row vs core/sensitivity.csv", n_values=k, maxdev=dev,
                     passed=bool(dev <= 1e-9), value=f"relred54 {row['relred54']:.3f} ({row['relred54_lo']:.3f} to {row['relred54_hi']:.3f}), "
                     f"m54_p {row['m54_p']:.2g}, absd {row['absd_b']:.3f}->{row['absd_a']:.3f}, bshuf_p {row['bshuf_p']:.3f}"))
    G = pd.DataFrame(rows)
    G.to_csv(OUT / "gate.csv", index=False)
    print(G.to_string(index=False))


# ================================================================ leakage correlation check
def ckd_epi_2021(scr, age, male):
    k = np.where(male > 0.5, 0.9, 0.7)
    a = np.where(male > 0.5, -0.302, -0.241)
    x = scr / k
    return 142 * np.minimum(x, 1) ** a * np.maximum(x, 1) ** -1.2 * 0.9938 ** age * np.where(male > 0.5, 1.0, 1.012)


def _leak_task(n):
    from scipy.stats import spearmanr
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    H = T.H
    comp = E.var_components(H)
    cov = T.cov
    rows = []
    for item in NONCODED:
        for cc in comp.get(item, []):
            v = H[cc].to_numpy(float)
            ok0 = np.isfinite(v)
            if ok0.sum() < 100 or np.nanstd(v) == 0:
                continue
            for inp in cov.columns:
                w = cov[inp].to_numpy(float)
                ok = ok0 & np.isfinite(w)
                if ok.sum() < 100 or np.std(w[ok]) == 0:
                    continue
                rho = spearmanr(v[ok], w[ok])[0]
                rows.append(dict(trial=n, item=item, component=cc, input=inp, n_obs=int(ok.sum()), rho=float(rho)))
            if item == "pp_LAB__egfr" and {"creatinine", "age_at_index", "male"} <= set(cov.columns):
                e = ckd_epi_2021(cov.creatinine.to_numpy(float), cov.age_at_index.to_numpy(float), cov.male.to_numpy(float))
                okc = ok0 & np.isfinite(e)
                obs_cr = H["obs_creatinine"].notna().to_numpy() if "obs_creatinine" in H else np.zeros(len(v), bool)
                for lab, m_ in (("CKD-EPI 2021 from PS inputs (all with eGFR)", okc), ("same, creatinine observed (not imputed)", okc & obs_cr)):
                    if m_.sum() >= 100:
                        rows.append(dict(trial=n, item=item, component=cc, input=lab, n_obs=int(m_.sum()), rho=float(spearmanr(v[m_], e[m_])[0])))
    # hdPS top-200 code families
    from eval_longtail_balance import hdps_rank
    r_ = np.arange(len(T.t))
    top = list(hdps_rank(T.lv.iloc[r_].reset_index(drop=True), T.t)[:200])  # same ranking as T.hd(200, t, rows)
    fam = pd.Series([str(c).split("_")[0] for c in top]).value_counts().to_dict()
    hd = dict(trial=n, n_levels=len(top), **{f"n_{k}": int(v) for k, v in fam.items()},
              n_px_em=int(sum(str(c).startswith(("px_992", "px_993", "px_994")) for c in top)),
              rx_levels=";".join(sorted({str(c).rsplit("__", 1)[0] for c in top if str(c).startswith("rx_")})),
              meds_flags=";".join(T.meds))
    return rows, hd


def leakcheck(workers):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    big = ("allhat", "value", "ascot", "lodestar", "affirm", "east-afnet4", "aristotle", "cabana-v2")
    tk = sorted(ALL, key=lambda x: x not in big)
    with Pool(min(workers, MAXW)) as p:
        res = p.map(_leak_task, tk, chunksize=1)
    D = pd.DataFrame([r for rr, _ in res for r in rr])
    D.to_parquet(OUT / "restricted_leak_rho_per_trial.parquet")  # per-trial correlations (restricted folder)
    D["arho"] = D.rho.abs()
    S = (D.groupby(["item", "input"]).agg(k_trials=("trial", "nunique"), median_rho=("rho", "median"), median_abs=("arho", "median"),
                                          max_abs=("arho", "max"), min_n=("n_obs", "min")).reset_index())
    S = S[S.min_n >= 11]
    S.sort_values("median_abs", ascending=False).to_csv(OUT / "leak_rho_summary.csv", index=False)
    top = S.sort_values("median_abs", ascending=False).groupby("item").head(1).sort_values("median_abs", ascending=False)
    top.to_csv(OUT / "leak_rho_top_per_item.csv", index=False)
    pd.DataFrame([h for _, h in res]).to_csv(OUT / "hdps_code_families.csv", index=False)
    print(top.head(20).round(3).to_string(index=False))


# ================================================================ sweep with leakage-clean masks / other trial sets
def _setup(variant, extra_sets=None):
    R = pd.read_parquet(CORE / "restricted_cells.parquet")
    F, SM, RET = P2.load_F(R)
    SM = apply_masks(SM, variant)
    sets = {"S32": S32, "S38": S38, "S35": s35()}
    if extra_sets:
        sets.update(extra_sets)
    P2._G.update(F=F, SM=SM, CL=V.cluster_of(), RET=RET, SETS=sets)
    return F, SM, RET, sets


def _init(variant):
    _setup(variant)


def _run_rows(variant, jobs, workers):
    from multiprocessing import Pool
    with Pool(min(workers, MAXW), initializer=_init, initargs=(variant,)) as p:
        res = p.map(P2._row, jobs, chunksize=1)
    return pd.DataFrame([r for r, _ in res]), pd.DataFrame([d for _, ds in res for d in ds])


def bh(S):
    for sname in S["set"].unique():
        ms = S["set"] == sname
        for fam, cols in (("balance", P2.BAL_FAM), ("agreement", P2.AGR_FAM)):
            long = S.loc[ms, cols].stack(dropna=True)
            q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
            for c in cols:
                S.loc[ms, f"q_{c}_fam"] = q[c] if c in q else np.nan
    return S


def sweep(workers):
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    out = []
    for variant, setnames in (("clean", ("S32", "S35", "S38")), ("orig", ("S35",))):
        jobs = [(s, c) for s in setnames for c in P2.contrasts()]
        jobs.sort(key=lambda x: x[0] != "S38")
        S, D = _run_rows(variant, jobs, workers)
        S.insert(0, "variant", variant)
        D.insert(0, "variant", variant)
        out.append((S, D))
        print(variant, len(S), f"{time.time() - t0:.0f}s", flush=True)
    # soft-correlate sensitivity: only rows touching PS-Clinical change; recompute those and splice into the clean S32 sweep
    S_clean = out[0][0]
    jobs = [(s, c) for s in ("S32",) for c in P2.contrasts() if "clinical" in (c[3], c[5])]
    Sb, _ = _run_rows("clean+soft", jobs, workers)
    base = S_clean[S_clean.set == "S32"].copy()
    key = ["set", "config", "contrast"]
    base = base.set_index(key)
    Sb = Sb.set_index(key)
    base.loc[Sb.index, Sb.columns] = Sb
    base = base.reset_index()
    base["variant"] = "clean+soft"
    S = pd.concat([o[0] for o in out] + [base], ignore_index=True)
    parts = []
    for v, g in S.groupby("variant"):
        parts.append(bh(g.copy()))
    S = pd.concat(parts, ignore_index=True)
    D = pd.concat([o[1] for o in out], ignore_index=True)
    for (v, s), g in D.groupby(["variant", "set"]):
        idx = g.index[g.p.notna()]
        D.loc[idx, "q_domain_fam"] = E.bh_fdr(D.loc[idx, "p"].to_numpy())
    S.to_csv(OUT / "sweep_sensitivity.csv", index=False)
    D.to_csv(OUT / "sweep_domains.csv", index=False)
    print("sweep written", len(S), len(D), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gate", "leakcheck", "sweep", "extras"])
    ap.add_argument("--workers", type=int, default=MAXW)
    a = ap.parse_args()
    w = min(a.workers, MAXW)
    if a.cmd == "extras":
        import defect_extras as X  # noqa: E402
        X.main(w)
    else:
        {"gate": gate, "leakcheck": lambda: leakcheck(w), "sweep": lambda: sweep(w)}[a.cmd]()
