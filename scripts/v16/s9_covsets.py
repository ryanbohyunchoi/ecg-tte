#!/usr/bin/env python
"""v1.6 sweep S9 (covariate sets): does adding AI-ECG move pre-defined sets of held-out covariates below |SMD| 0.1?
Pre-registered plan: docs/v16/S9_COVARIATE_SETS_PLAN.md (committed before any S9 result). Exploratory; aggregates only.

Scenarios (cells = S8 designs, reused from s8_headline.design):
  headline  demo|cal0.1 (1:1 caliper 0.1), min7|default, common10|default   x {all 18 trials, 8 physiology trials}
  reference sparse|default, demo|default (caliper 0.2), hdPS200|default    (18 trials; physiology subset descriptive)
Arms: base, +ECG (32 BCL PCs), +shufECG (T.shuffle_perm rows), +noise32 (T.noise32); unmatched once per trial/half.
Halves: full, A, B (S6.halves: rng 16060 + trial index, stratified by treatment).

Variable universe per trial x half x cell (per-variable |SMD| in the matched sample, E.smd_components /
run_cell's smd:<VARS>):
  p58:<v>  the 58 engine variables (make_acc_figure.VARS)
  x:<v>    claude-v16-covars2b (corrected panel), status kept*, no exposure leak (S6.load_extra), not
           pre-index-failing (timing), all blocks; block = ecg_proximal per covars2b `block` (+ S8 EXTRA_PROX)
  v1:<v>   claude-v16-covars (race/ethnicity, tobacco, obesity, hyperlipidemia, t2d, frailty_count, inpatient days)
  Per cell, variables in (or a proxy of / tagged as overlapping) the cell's PS are dropped (S6.excluded_extra,
  S8.composite_overlap); at hdPS200 extra variables whose codes overlap the codes behind the trial/half's top-200
  hdPS levels are dropped (S6.hdps_selected / hdps_overlap; v1 dx variables with the ICD keys in V1_KEYS).
  Variables with no variance / no observed value in the analysed rows are dropped.
Sets:
  SET1  clinical ECG-relevant confounders (SET1 mapping below; fixed from the plan before results)
  SET2  literature core + common items (docs/v16/lit_covariates.json), mapped through COVARIATES2 cross-check (LIT_MAP)
  SET3  split-sample: per scenario, rank candidates (p58 + x non-proximal) by half-A ECG - base gain in trial-averaged
        |SMD|; top 25 -> selection_S9.json (committed before any half-B / full computation)
  FULL  p58 + x non-proximal (the SET3 candidate pool), reference in every table
  (SET2np = SET2 minus ECG-proximal variables: descriptive only)
Metrics per set x trial x arm: pct_lt10 (primary), mean |SMD|, pct_gt20; love count (# set variables whose median
|SMD| across trials < 0.1). Tests: exact paired sign-flip over trials, placebos (ECG vs shufECG / noise; placebo vs base),
comparator clusters (audit_v16.CLUSTER), leave-one-trial-out, halves A/B, BH-FDR over sets x scenarios x metrics.
Love count: trial-level arm-swap permutation (exact if <= 12 trials, else 20,000 draws), cluster-level swap, LOO.

Usage: s9_covsets.py run --halves A      ->  s9_covsets.py select  ->  (commit selection)  ->
       s9_covsets.py run --halves full,B ->  s9_covsets.py summarize
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import hashlib  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import textwrap  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s6_balance as S6  # noqa: E402
import s8_headline as S8  # noqa: E402  (installs the matched-sample capture into E.match / E.weights)
import v16_engine as E  # noqa: E402
from audit_v16 import CLUSTER  # noqa: E402
from v13_summarize import md  # noqa: E402

SWEEP = "s9-covsets"
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s9-covsets")
DOCS = HERE.parent.parent / "docs" / "v16"
COV2B = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars2b")
SELFILE = DOCS / "selection_S9.json"
CELLS = ["demo|cal0.1", "min7|default", "common10|default", "sparse|default", "demo|default", "hdPS200|default"]
HEADLINE = CELLS[:3]
MODS = {"default": dict(dim=32, est=("match", 0.2, 1)), "cal0.1": dict(dim=32, est=("match", 0.1, 1))}
ROLES = ["base", "ECG", "shufECG", "noise"]
PHYS = S8.PHYS
SUBSETS = S8.SUBSETS
# scenarios: (cell, subset); BH family = headline x both subsets + references x all 18
SCEN = [(c, s) for c in HEADLINE for s in ("all", "phys")] + [(c, "all") for c in CELLS[3:]]
SCEN_DESC = [(c, "phys") for c in CELLS[3:]]  # descriptive only
SETS = ["SET1", "SET2", "SET3", "FULL"]
SET_LAB = {"SET1": "Set 1: clinical ECG-relevant", "SET2": "Set 2: literature core+common", "SET3": "Set 3: split-sample top 25",
           "FULL": "Full panel (58 + expanded non-proximal)", "SET2np": "Set 2, non-ECG-proximal part (descriptive)"}
SMETRICS = ["pct_lt10", "mean", "pct_gt20"]
HIGHER = {"pct_lt10"}
MLAB = {"pct_lt10": "% |SMD|<0.1", "mean": "mean |SMD|", "pct_gt20": "% |SMD|>0.2", "love": "love count <0.1"}
V1COLS = ["race_black", "race_asian", "race_other_unknown", "hispanic", "ethnicity_unknown", "tobacco_current", "tobacco_ever",
          "obesity", "hyperlipidemia", "t2d", "frailty_count", "inpatient_days_365"]
_FRAIL = ("F01 F02 F03 G30 G31 F05 R41 W00 W01 W02 W03 W04 W05 W06 W07 W08 W09 W10 W11 W12 W13 W14 W15 W16 W17 W18 W19 R296 Z9181 "
          "R26 R53 M6281 E40 E41 E42 E43 E44 E45 E46 R634 R636 R64 L89 R32 N394 R15 Z74 Z993 G20 G21 F32 F33 H54 H90 H91 M80 M81 S72")
V1_KEYS = {"tobacco_current": {"dx:F17", "dx:Z720"}, "tobacco_ever": {"dx:F17", "dx:Z720", "dx:Z87891"},
           "obesity": {"dx:E660", "dx:E661", "dx:E662", "dx:E668", "dx:E669", "dx:Z683", "dx:Z684"},
           "hyperlipidemia": {"dx:E780", "dx:E781", "dx:E782", "dx:E783", "dx:E784", "dx:E785"}, "t2d": {"dx:E11"},
           "frailty_count": {f"dx:{c}" for c in _FRAIL.split()}}

# ---------------------------------------------------------------- Set 1 (plan items -> variables), fixed before results
SET1_MAP = [
    ("LV function", "LVEF (observed)", ["p58:smd_obs_lvef"]),
    ("LV function", "echo EF", ["p58:pp_LVFUNC__ef"]),
    ("LV function", "LV systolic grade", ["p58:pp_LVFUNC__lv_sys_grade"]),
    ("LV function", "GLS", ["p58:pp_LVFUNC__gls"]),
    ("LV function", "LV stroke volume index", ["p58:pp_LVFUNC__lvsvi"]),
    ("LV structure", "LVIDd", ["p58:pp_LVSTRUCT__lvidd"]),
    ("LV structure", "LVEDVi", ["p58:pp_LVSTRUCT__lvedvi"]),
    ("LV structure", "LVESVi", ["p58:pp_LVSTRUCT__lvesvi"]),
    ("LV structure", "IVSd", ["p58:pp_LVSTRUCT__ivsd"]),
    ("LV structure", "LVPWd", ["p58:pp_LVSTRUCT__lvpwd"]),
    ("LV structure", "wall-thickness grade", ["p58:pp_LVSTRUCT__wall_thickness_grade"]),
    ("LV structure", "LV mass (if available)", []),
    ("Diastolic and atrial", "LA volume index", ["p58:pp_DIAST__lavi"]),
    ("Diastolic and atrial", "LA size grade", ["p58:pp_DIAST__la_size_grade"]),
    ("Diastolic and atrial", "E/e'", ["p58:pp_DIAST__e_eprime"]),
    ("Diastolic and atrial", "diastolic grade", ["p58:pp_DIAST__diastolic_grade"]),
    ("RV and pulmonary", "RVSP", ["p58:pp_RVPULM__rvsp"]),
    ("RV and pulmonary", "TAPSE", ["p58:pp_RVPULM__tapse"]),
    ("RV and pulmonary", "RV S'", ["p58:pp_RVPULM__rv_s"]),
    ("RV and pulmonary", "RV systolic grade", ["p58:pp_RVPULM__rv_sys_grade"]),
    ("RV and pulmonary", "pulmonary hypertension dx", ["x:pulmonary_hypertension"]),
    ("Neurohormonal and renal", "NT-proBNP", ["p58:pp_BNP__ntprobnp"]),
    ("Neurohormonal and renal", "eGFR", ["p58:pp_LAB__egfr"]),
    ("Neurohormonal and renal", "creatinine", ["p58:smd_obs_creatinine"]),
    ("Neurohormonal and renal", "BUN", ["p58:pp_LAB__bun"]),
    ("Neurohormonal and renal", "hemoglobin", ["p58:smd_obs_hemoglobin"]),
    ("Clinical HF burden", "prior HF hospitalisation (strict pre-index)", ["x:n_hf_hosp_365"]),
    ("Clinical HF burden", "cardiomyopathy dx", ["x:cardiomyopathy_any"]),
    ("Clinical HF burden", "loop diuretic use (if not in the PS or the exposure)", ["x:rx_loop_diuretic_365"]),
]
SET1 = [v for _, _, vs in SET1_MAP for v in vs]

# ---------------------------------------------------------------- Set 2: literature core+common -> variables
# covars2 variables from the COVARIATES2 literature cross-check table; items marked "already in existing panel" /
# "in covars v1" mapped to the 58-panel (p58:) or claude-v16-covars (v1:). Wildcards are expanded on the covars2b dictionary.
LIT_EXISTING = {
    3: ["v1:race_black", "v1:race_asian", "v1:race_other_unknown"], 4: ["v1:hispanic", "v1:ethnicity_unknown"],
    14: ["v1:tobacco_current", "v1:tobacco_ever"], 17: ["v1:obesity"], 18: ["p58:smd_obs_bmi"], 34: ["v1:hyperlipidemia"],
    43: ["v1:t2d"], 76: ["v1:frailty_count"], 112: ["v1:inpatient_days_365"], 126: ["p58:smd_obs_sbp"], 127: ["p58:smd_obs_dbp"],
    128: ["p58:smd_obs_heart_rate"], 129: ["p58:smd_obs_creatinine"], 130: ["p58:pp_LAB__egfr"], 131: ["p58:smd_obs_potassium"],
    132: ["p58:smd_obs_sodium"], 133: ["p58:pp_LAB__bun"], 134: ["p58:smd_obs_hemoglobin"], 135: ["p58:pp_LAB__hba1c"],
    137: ["p58:pp_LAB__ldl"], 139: ["p58:pp_BNP__ntprobnp"], 141: ["p58:pp_LAB__albumin"], 147: ["p58:smd_obs_lvef"]}
LIT_NOT = {1: "in every PS (demo)", 2: "in every PS (demo)", 5: "in every PS (demo)",
           8: "index-day, not pre-index (excluded, AUDIT_V16_ROUND2)", 9: "not in extract", 10: "not in extract",
           11: "needs external ADI file", 145: "not in extract", 149: "notes NLP only", 150: "PS-only construct"}


def lit_map():
    """-> list of (id, name, priority, [variables]) for priority core/common items (COVARIATES2 cross-check table)."""
    lit = {x["id"]: x for x in json.loads((DOCS / "lit_covariates.json").read_text())}
    dic = pd.read_csv(COV2B / "dictionary.csv")
    allv = list(dic.variable)
    tab = {}
    for line in (DOCS / "COVARIATES2.md").read_text().splitlines():
        m = re.match(r"^\| (\d+) \|", line)
        if m:
            f = [x.strip() for x in line.strip().strip("|").split("|")]
            tab[int(f[0])] = f[3]
    out = []
    for i, x in sorted(lit.items()):
        if x["priority"] not in ("core", "common"):
            continue
        vs = []
        if i not in LIT_NOT:
            for tok in re.sub(r"\(.*?\)", "", tab.get(i, "")).split(","):
                tok = tok.strip().strip("`")
                if not tok:
                    continue
                pat = "^" + re.escape(tok).replace(r"\*", ".*") + "$"
                vs += [f"x:{v}" for v in allv if re.match(pat, v)]
            vs += LIT_EXISTING.get(i, [])
        out.append((i, x["name"], x["priority"], list(dict.fromkeys(vs)), LIT_NOT.get(i, "")))
    return out


def set2():
    return list(dict.fromkeys(v for *_, vs, _ in lit_map() for v in vs))


# ---------------------------------------------------------------- data
_TC = {}


def trial(n):
    if n not in _TC:
        T = E.load_trial(n)
        C = S6.load_new(T)
        Xe, ovl, blk = S6.load_extra(T, COV2B)
        hk = S6.HDPS_KEYS[(T.n, str(COV2B))]
        prox = {c for c in Xe.columns if blk[c] == "ecg_proximal" or c in S8.EXTRA_PROX}
        V1 = C[V1COLS].astype(float)
        _TC.clear()
        _TC[n] = (T, C, Xe, ovl, hk, prox, V1)
    return _TC[n]


def universe(n, cell, rows, t):
    """-> (U DataFrame of extra columns 'x:'/'v1:' for rows, list of dropped names, n hdPS-dropped)."""
    T, C, Xe, ovl, hk, prox, V1 = trial(n)
    if cell == "unmatched":
        psn, base = [], "unmatched"
    else:
        base = cell.split("|")[0]
        _, psn = S8.design(T, C, T, base, rows, t)
    xd = set(S6.excluded_extra(psn, list(Xe.columns), ovl)) | {c for c in Xe.columns if S8.composite_overlap(c, psn)}
    vd = set(S6.excluded_extra(psn, list(V1.columns), {}))
    nh = 0
    if base.startswith("hdPS"):
        sel = S6.hdps_selected(T, rows, t)
        hx = {c for c in Xe.columns if c not in xd and hk.get(c) and S6.hdps_overlap(hk[c], sel)}
        hv = {c for c in V1.columns if c not in vd and c in V1_KEYS and S6.hdps_overlap(V1_KEYS[c], sel)}
        nh = len(hx) + len(hv)
        xd |= hx
        vd |= hv
    U = pd.concat([Xe.drop(columns=sorted(xd)).add_prefix("x:"), V1.drop(columns=sorted(vd)).add_prefix("v1:")], axis=1).iloc[rows]
    U = U.loc[:, U.notna().sum() > 0]
    U = U.loc[:, U.nunique() > 1]
    return U, len(xd) + len(vd), nh


def task(args):
    n, half, cell = args
    t0 = time.time()
    T = trial(n)[0]
    i = E.TRIALS.index(n)
    rows = S6.halves(T, i)[half]
    t = T.t[rows]
    U, ndrop, nh = universe(n, cell, rows, t)
    UV = U.to_numpy(float)
    ucols = list(U.columns)
    if cell == "unmatched":
        arms, est, mod = [("unmatched", None)], ("match", 0.2, 1), "default"
    else:
        base, mod = cell.split("|")
        X, _ = S8.design(T, trial(n)[1], T, base, rows, t)
        est = MODS[mod]["est"]
        pc, sh, nz = (M[rows] for M in S8.ecg_mats(T, 32))
        arms = [("base", X), ("ECG", np.hstack([X, pc])), ("shufECG", np.hstack([X, sh])), ("noise", np.hstack([X, nz]))]
    out, vrows = [], []
    for role, Xa in arms:
        S8._LAST.clear()
        r = E.run_cell(T, Xa, rows=rows, heldout=T.H, estimator=est)
        s_idx, s_w = (np.arange(len(t)), np.ones(len(t))) if Xa is None else S8._LAST["m"]
        xs = E.smd_components(UV, t, s_idx, s_w, t[s_idx])
        out.append(dict(sweep=SWEEP, cell=cell, base=cell.split("|")[0], mod=mod, ecg_dim=32, estimator=str(est), trial=n, half=half,
                        arm_role=role, arm_label="unmatched" if role == "unmatched" else f"{S8.cell_label(cell)} [{role}]", **r,
                        n_universe_extra=len(ucols), n_dropped_ps=ndrop, n_dropped_hdps=nh, rb=T.rb, rs=T.rs))
        for c, _, _ in E.VARS:
            v = r[f"smd:{c}"]
            if np.isfinite(v):
                vrows.append((cell, n, half, role, f"p58:{c}", float(v)))
        vrows.extend((cell, n, half, role, c, float(v)) for c, v in zip(ucols, xs) if np.isfinite(v))
    print(f"{n} {half} {cell} {time.time() - t0:.0f}s", flush=True)
    return out, vrows


def run(trials, halves, workers, tag):
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    if any(h != "A" for h in halves):
        assert SELFILE.exists(), "selection_S9.json must exist (and be committed) before half-B / full computation"
    tk = [(n, h, c) for n in trials for h in halves for c in ["unmatched"] + CELLS]
    size = {n: len(E.load_trial(n).t) for n in trials}
    tk.sort(key=lambda x: (-size[x[0]], x[0]))
    res, vres = [], []
    t0 = time.time()
    with Pool(min(workers, 32)) as p:
        for k, (r, v) in enumerate(p.imap(task, tk, chunksize=2)):
            res.extend(r)
            vres.extend(v)
            if (k + 1) % 20 == 0 or k + 1 == len(tk):
                print(f"{k + 1}/{len(tk)} tasks {time.time() - t0:.0f}s", flush=True)
    pd.DataFrame(res).to_csv(OUT / f"results_{tag}.csv", index=False)
    pd.DataFrame(vres, columns=["cell", "trial", "half", "arm_role", "var", "smd"]).to_parquet(OUT / f"var_{tag}.parquet", index=False)
    print("done", tag, len(res), len(vres), flush=True)


# ---------------------------------------------------------------- helpers
def load_var(halves):
    V = pd.concat([pd.read_parquet(f) for f in sorted(OUT.glob("var_*.parquet"))], ignore_index=True)
    V = V[V.half.isin(halves)]
    return V.drop_duplicates(["cell", "trial", "half", "arm_role", "var"])


def load_res(halves):
    df = pd.concat([pd.read_csv(f) for f in sorted(OUT.glob("results_*.csv"))], ignore_index=True)
    df = df[df.half.isin(halves)].drop_duplicates(["cell", "trial", "half", "arm_role"])
    df["seed"] = 0  # (S8.audit_checks groups by seed)
    df["absd"] = (df.loghr - df.rb).abs()
    df["z2"] = (df.loghr - df.rb) ** 2 / (df.se ** 2 + df.rs ** 2)
    return df


def prox_set():
    dic = pd.read_csv(COV2B / "dictionary.csv")
    return {f"x:{v}" for v in dic.variable[dic.block == "ecg_proximal"]} | {f"x:{v}" for v in S8.EXTRA_PROX}


def full_pool(allvars):
    pr = prox_set()
    return [v for v in allvars if v.startswith("p58:") or (v.startswith("x:") and v not in pr)]


def smd_cube(V, cell, half, role, trials, vars_):
    """trials x vars matrix of |SMD| (NaN = unavailable). Unmatched restricted to the cell's base-arm universe."""
    if role == "unmatched":
        g = V[(V.cell == "unmatched") & (V.half == half)]
        b = V[(V.cell == cell) & (V.half == half) & (V.arm_role == "base")][["trial", "var"]]
        g = g.merge(b, on=["trial", "var"])
    else:
        g = V[(V.cell == cell) & (V.half == half) & (V.arm_role == role)]
    g = g[g.trial.isin(trials) & g["var"].isin(vars_)]
    return g.pivot(index="trial", columns="var", values="smd").reindex(index=trials, columns=vars_)


def set_metrics(M):
    """per-trial metrics from a trials x vars |SMD| matrix."""
    ok = np.isfinite(M.to_numpy())
    x = M.to_numpy()
    n = ok.sum(1)
    with np.errstate(invalid="ignore"):
        r = pd.DataFrame({"n": n, "pct_lt10": 100 * np.where(ok, x < 0.1, False).sum(1) / n,
                          "mean": np.nansum(x, 1) / n, "pct_gt20": 100 * np.where(ok, x > 0.2, False).sum(1) / n}, index=M.index)
    r[r.n == 0] = np.nan
    return r


def sflip(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    return S6.sign_flip(d)[1] if len(d) else np.nan


def paired(a, b, m):
    d = (a[m] - b[m]).dropna()
    good = (d > 0) if m in HIGHER else (d < 0)
    return d, dict(d=float(d.mean()) if len(d) else np.nan, k=f"{int(good.sum())}/{len(d)}", p=sflip(d.to_numpy()))


def cluster_loo(d, m):
    d = d.dropna() * (1 if m in HIGHER else -1)  # positive = ECG better
    if len(d) < 3:
        return dict(cluster_p=np.nan, cluster_k="", loo_p_max=np.nan)
    cl = d.groupby(d.index.map(CLUSTER)).mean()
    return dict(cluster_p=sflip(cl.to_numpy()), cluster_k=f"{int((cl > 0).sum())}/{len(cl)}",
                loo_p_max=float(max(sflip(d.drop(k).to_numpy()) for k in d.index)))


def love(M):
    med = np.nanmedian(M.to_numpy(), axis=0) if len(M) else np.array([])
    ok = np.isfinite(med)
    return int((med[ok] < 0.1).sum()), int(ok.sum()), pd.Series(med, index=M.columns)


def _med_count(A):  # A: draws x trials x vars
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(A, axis=1)
    return (med < 0.1).sum(1)


def love_perm(Ma, Mb, groups=None, ndraw=20000, seed=9090):
    """two-sided permutation p for love(Ma) - love(Mb): swap the two arms' per-trial vectors within trial
    (groups: swap whole comparator clusters together). Exact when <= 12 units."""
    a, b = Ma.to_numpy(), Mb.to_numpy()
    keep = np.isfinite(a).any(0) | np.isfinite(b).any(0)
    a, b = a[:, keep], b[:, keep]
    obs = int(_med_count(a[None])[0] - _med_count(b[None])[0])
    units = np.arange(len(a)) if groups is None else pd.factorize(np.asarray(groups))[0]
    nu = units.max() + 1 if len(units) else 0
    if nu == 0:
        return obs, np.nan
    S = np.array(list(itertools.product((0, 1), repeat=nu)), bool) if nu <= 12 else \
        np.random.default_rng(seed).integers(0, 2, (ndraw, nu)).astype(bool)
    null = []
    for i in range(0, len(S), 500):
        s = S[i:i + 500][:, units][:, :, None]
        A = np.where(s, b[None], a[None])
        B = np.where(s, a[None], b[None])
        null.append(_med_count(A) - _med_count(B))
    null = np.concatenate(null)
    return obs, float(np.mean(np.abs(null) >= abs(obs)))


# ---------------------------------------------------------------- selection (half A only)
SEL_RULE = ("Half A only. For each scenario (cell x trial subset), candidates = 58-panel + claude-v16-covars2b non-ECG-proximal "
            "variables that are held out from that cell's PS and available (finite |SMD| in base and ECG) in at least half of the "
            "scenario's trials. Gain = trial-averaged |SMD| (base) - trial-averaged |SMD| (ECG) over the trials where the variable is "
            "available in both arms. Rank by gain (descending; ties by name); take the top 25.")


def select():
    V = load_var(["A"])
    assert set(V.half) == {"A"}
    allv = sorted(V["var"].unique())
    pool = full_pool(allv)
    J = dict(created=time.strftime("%Y-%m-%d %H:%M:%S %Z"), rule=SEL_RULE, halves_available_at_selection=sorted(set(V.half)),
             n_pool=len(pool), scenarios={})
    for cell, sub in SCEN + SCEN_DESC:
        trs = SUBSETS[sub]
        Mb, Me = smd_cube(V, cell, "A", "base", trs, pool), smd_cube(V, cell, "A", "ECG", trs, pool)
        both = np.isfinite(Mb.to_numpy()) & np.isfinite(Me.to_numpy())
        nav = both.sum(0)
        with np.errstate(invalid="ignore"):
            gain = np.nansum(np.where(both, Mb.to_numpy() - Me.to_numpy(), 0), 0) / nav
        g = pd.DataFrame({"var": pool, "gain": gain, "n_trials": nav, "base": np.nanmean(np.where(both, Mb, np.nan), 0),
                          "ecg": np.nanmean(np.where(both, Me, np.nan), 0)})
        g = g[g.n_trials >= np.ceil(len(trs) / 2)].sort_values(["gain", "var"], ascending=[False, True])
        top = g.head(25)
        J["scenarios"][f"{cell}@{sub}"] = dict(n_candidates=int(len(g)), selected=top["var"].tolist(),
                                               detail=[dict(var=r.var, gain=round(float(r.gain), 5), base=round(float(r.base), 5),
                                                            ecg=round(float(r.ecg), 5), n_trials=int(r.n_trials)) for r in top.itertuples()])
    SELFILE.write_text(json.dumps(J, indent=1))
    (OUT / "selection_S9.json").write_text(json.dumps(J, indent=1))
    print(json.dumps({k: v["selected"][:5] for k, v in J["scenarios"].items()}, indent=1))


# ---------------------------------------------------------------- summaries
def set_vars(name, cell, sub, allv, J):
    if name == "SET1":
        return [v for v in SET1 if v in allv]
    if name == "SET2":
        return [v for v in set2() if v in allv]
    if name == "SET2np":
        pr = prox_set()
        return [v for v in set2() if v in allv and v not in pr]
    if name == "SET3":
        return J["scenarios"][f"{cell}@{sub}"]["selected"]
    if name == "FULL":
        return full_pool(allv)
    raise KeyError(name)


def summarize_sets(V, J, halves=("full", "A", "B")):
    allv = set(V["var"].unique())
    rows, per = [], []
    for cell, sub in SCEN + SCEN_DESC:
        trs = SUBSETS[sub]
        for sname in SETS + ["SET2np"]:
            vs = set_vars(sname, cell, sub, allv, J)
            for h in halves:
                M = {r: smd_cube(V, cell, h, r, trs, vs) for r in ROLES + ["unmatched"]}
                A = {r: set_metrics(M[r]) for r in M}
                r = dict(cell=cell, subset=sub, set=sname, half=h, n_set=len(vs), family=(cell, sub) in SCEN and sname in SETS,
                         n_avail_med=float(A["base"].n.median()))
                for m in SMETRICS:
                    for role in ROLES + ["unmatched"]:
                        r[f"{role}_{m}"] = float(A[role][m].mean())
                    for b in ("base", "shufECG", "noise"):
                        dser, x = paired(A["ECG"], A[b], m)
                        tag = {"base": "", "shufECG": "_shuf", "noise": "_noise"}[b]
                        r[f"d{tag}_{m}"], r[f"k{tag}_{m}"], r[f"p{tag}_{m}"] = x["d"], x["k"], x["p"]
                        if b == "base":
                            cl = cluster_loo(dser, m)
                            r[f"clp_{m}"], r[f"clk_{m}"], r[f"loo_{m}"] = cl["cluster_p"], cl["cluster_k"], cl["loo_p_max"]
                            if h == "full":
                                for tn, dv in dser.items():
                                    per.append(dict(cell=cell, subset=sub, set=sname, metric=m, trial=tn, d=dv,
                                                    base=A["base"][m].get(tn), ecg=A["ECG"][m].get(tn)))
                    for b in ("shufECG", "noise"):
                        _, x = paired(A[b], A["base"], m)
                        tag = {"shufECG": "_shufbase", "noise": "_noisebase"}[b]
                        r[f"d{tag}_{m}"], r[f"p{tag}_{m}"] = x["d"], x["p"]
                for role in ROLES + ["unmatched"]:
                    r[f"love_{role}"], r["love_n"], _ = love(M[role])
                ob, pl = love_perm(M["ECG"], M["base"])
                r["d_love"], r["p_love"] = ob, pl
                r["d_shuf_love"], r["p_shuf_love"] = love_perm(M["ECG"], M["shufECG"], ndraw=5000)
                r["d_noise_love"], r["p_noise_love"] = love_perm(M["ECG"], M["noise"], ndraw=5000)
                r["d_shufbase_love"], r["p_shufbase_love"] = love_perm(M["shufECG"], M["base"], ndraw=5000)
                r["d_noisebase_love"], r["p_noisebase_love"] = love_perm(M["noise"], M["base"], ndraw=5000)
                r["clp_love"] = love_perm(M["ECG"], M["base"], groups=[CLUSTER[t_] for t_ in trs])[1]
                if h == "full" and r["family"]:
                    r["loo_love"] = float(max(love_perm(M["ECG"].drop(t_), M["base"].drop(t_), ndraw=2000)[1] for t_ in trs))
                else:
                    r["loo_love"] = np.nan
                rows.append(r)
                print(cell, sub, sname, h, f"{r['base_pct_lt10']:.1f}->{r['ECG_pct_lt10']:.1f} p={r['p_pct_lt10']:.3f} "
                      f"love {r['love_base']}->{r['love_ECG']}/{r['love_n']} p={pl:.3f}", flush=True)
    G = pd.DataFrame(rows)
    for h in halves:
        k = G.index[(G.half == h) & G.family]
        p = np.concatenate([G.loc[k, f"p_{m}"].to_numpy() for m in SMETRICS + ["love"]])
        q = E.bh_fdr(p)
        for j, m in enumerate(SMETRICS + ["love"]):
            G.loc[k, f"q_{m}"] = q[j * len(k):(j + 1) * len(k)]
    return G, pd.DataFrame(per)


def domain_of(v, dic, prox):
    if v.startswith("p58:"):
        return "58: " + {c: g for c, _, g in E.VARS}[v[4:]]
    if v.startswith("v1:"):
        return "covars v1 (race, tobacco, obesity, lipids, T2D, frailty, inpatient days)"
    d = dic.get(v[2:], "other")
    return f"expanded: {d}" + (" [ECG-proximal]" if v in prox else "")


def domain_summary(V, cell, sub):
    """per-domain mean |SMD| per trial (full) for unmatched/base/ECG/shuf/noise + paired test ECG vs base."""
    dic = pd.read_csv(COV2B / "dictionary.csv").set_index("variable").domain.to_dict()
    pr = prox_set()
    trs = SUBSETS[sub]
    allv = sorted(V[(V.cell == cell) & (V.half == "full")]["var"].unique())
    dom = {v: domain_of(v, dic, pr) for v in allv}
    M = {r: smd_cube(V, cell, "full", r, trs, allv) for r in ROLES + ["unmatched"]}
    rows = []
    for d in dict.fromkeys(sorted(dom.values(), key=lambda s: (not s.startswith("58"), s))):
        vs = [v for v in allv if dom[v] == d]
        A = {r: M[r][vs] for r in M}
        pt = {r: A[r].mean(1, skipna=True) for r in A}
        lt = {r: love(A[r])[0] for r in A}
        dd = (pt["ECG"] - pt["base"]).dropna()
        r = dict(domain=d, n_vars=len(vs), **{f"{k}_mean": float(v.mean()) for k, v in pt.items()},
                 d=float(dd.mean()), k=f"{int((dd < 0).sum())}/{len(dd)}", p=sflip(dd.to_numpy()),
                 p_shuf=sflip((pt["ECG"] - pt["shufECG"]).dropna().to_numpy()), p_noise=sflip((pt["ECG"] - pt["noise"]).dropna().to_numpy()),
                 **{f"love_{k}": v for k, v in lt.items()})
        rows.append(r)
    D = pd.DataFrame(rows)
    D["q"] = E.bh_fdr(D.p.to_numpy())
    return D


# ---------------------------------------------------------------- figures
def _pretty(v):
    lab = {c: l for c, l, _ in E.VARS}
    if v.startswith("p58:"):
        return lab[v[4:]]
    return v.split(":", 1)[1].replace("_365", "").replace("_", " ")


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    return plt


C_UNM, C_BASE, C_ECG, C_GOOD, C_BAD = "#868e96", "#74c0fc", "#d9480f", "#2b8a3e", "#c92a2a"


def loveplot_set(V, cell, sub, sname, vs, fname, title, p_txt):
    plt = _plt()
    trs = SUBSETS[sub]
    dic = pd.read_csv(COV2B / "dictionary.csv").set_index("variable").domain.to_dict()
    pr = prox_set()
    Mb, Me, Mu = (smd_cube(V, cell, "full", r, trs, vs) for r in ("base", "ECG", "unmatched"))
    nb, nv, mb = love(Mb)
    ne, _, me = love(Me)
    _, _, mu = love(Mu)
    order = [v for v in vs if np.isfinite(me.get(v, np.nan)) and np.isfinite(mb.get(v, np.nan))]
    order.sort(key=lambda v: (not domain_of(v, dic, pr).startswith("58"), domain_of(v, dic, pr), -mb[v]))
    # rows: a bold header row per domain, then its variables
    rows_ = []
    for g in dict.fromkeys(domain_of(v, dic, pr) for v in order):
        rows_.append(("H", g))
        rows_ += [("V", v) for v in order if domain_of(v, dic, pr) == g]
    n = len(rows_)
    ypos = {k: n - 1 - i for i, k in enumerate(rows_)}
    fig, ax = plt.subplots(figsize=(7.6, max(3.8, 0.15 * n + 1.9)))
    ticks, labs = [], []
    k = 0
    for kind, v in rows_:
        yy = ypos[(kind, v)]
        if kind == "H":
            ax.axhline(yy + 0.5, color="#bbb", lw=0.6)
            ax.text(0.003, yy, v.replace("expanded: ", "expanded covariates: ").replace("58: ", "58-panel: "), fontsize=6.6,
                    fontweight="bold", color="#333", va="center", ha="left", transform=ax.get_yaxis_transform())
            continue
        if k % 2 == 0:
            ax.axhspan(yy - 0.5, yy + 0.5, color="#f4f5f7", zorder=0)
        k += 1
        ax.plot([mb[v], me[v]], [yy] * 2, color=C_GOOD if me[v] < mb[v] else C_BAD, lw=1.5, alpha=0.8, zorder=2)
        ticks.append(yy)
        labs.append(_pretty(v))
    vy = [ypos[("V", v)] for v in order]
    ax.scatter([mu[v] for v in order], vy, marker="x", color=C_UNM, s=18, lw=1, zorder=3, label="Unmatched")
    ax.scatter([mb[v] for v in order], vy, color=C_BASE, s=22, ec="white", lw=0.4, zorder=4, label="Without ECG")
    ax.scatter([me[v] for v in order], vy, color=C_ECG, s=22, ec="white", lw=0.4, zorder=5, label="With ECG")
    ax.axvline(0.1, color="#777", ls="--", lw=0.9)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labs, fontsize=6.3)
    xmax = max(0.3, float(np.nanmax([mu[v] for v in order if np.isfinite(mu.get(v, np.nan))] + [mb[v] for v in order])) * 1.05)
    ax.set_xlim(0, min(xmax, 0.8))
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_xlabel(f"|SMD| after PS adjustment (median across {len(trs)} trials, full cohort)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7, frameon=False)
    ax.set_title(f"variables with median |SMD| < 0.1: {nb} → {ne} of {nv}  (per-trial % < 0.1, sign-flip p = {p_txt})",
                 fontsize=7.5, loc="left", pad=20)
    fig.suptitle("\n".join(textwrap.wrap(title, 85, break_on_hyphens=False)), x=0.01, ha="left", fontweight="bold", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(DOCS / fname, dpi=180 if n < 120 else 110, bbox_inches="tight")
    plt.close(fig)


def domain_plot(D, title, fname):
    plt = _plt()
    D = D.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8.6, 0.3 * len(D) + 1.6))
    y = np.arange(len(D))
    for i, r in D.iterrows():
        if i % 2 == 0:
            ax.axhspan(i - 0.5, i + 0.5, color="#f4f5f7", zorder=0)
        ax.plot([r.base_mean, r.ECG_mean], [i, i], color=C_GOOD if r.ECG_mean < r.base_mean else C_BAD, lw=1.6, zorder=2)
        st = "**" if r.q < 0.05 else ("*" if r.p < 0.05 else "")
        ax.annotate(f"{r.love_base}→{r.love_ECG} of {r.n_vars}   p={_p(r.p)}{st}", xy=(1.0, i), xycoords=("axes fraction", "data"),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=6.3, color="#333")
    ax.scatter(D.unmatched_mean, y, marker="x", color=C_UNM, s=18, lw=1, zorder=3, label="Unmatched")
    ax.scatter(D.base_mean, y, color=C_BASE, s=24, ec="white", lw=0.4, zorder=4, label="Without ECG")
    ax.scatter(D.ECG_mean, y, color=C_ECG, s=24, ec="white", lw=0.4, zorder=5, label="With ECG")
    ax.axvline(0.1, color="#777", ls="--", lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{d} ({n})" for d, n in zip(D.domain, D.n_vars)], fontsize=6.5)
    ax.set_ylim(-0.6, len(D) - 0.4)
    ax.set_xlim(0, max(0.2, float(np.nanmax(D[["unmatched_mean", "base_mean"]].to_numpy())) * 1.08))
    ax.set_xlabel("domain mean |SMD| (mean over the domain's variables per trial, then over trials; full cohort)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7, frameon=False)
    fig.suptitle("\n".join(textwrap.wrap(title, 95, break_on_hyphens=False)) + "\nright: love count < 0.1 (base → ECG, of domain variables); p = sign-flip on the "
                 "per-trial domain mean (* p<0.05, ** BH q<0.05 over domains)", x=0.01, ha="left", fontsize=8, fontweight="bold")
    fig.tight_layout()
    fig.savefig(DOCS / fname, dpi=180, bbox_inches="tight")
    plt.close(fig)


def heatmaps(S, G):
    plt = _plt()
    mets = ["absd", "z2", "mean_smd", "cstat"]
    s = S[S.half == "full"].set_index("cell").reindex(CELLS)
    M = np.array([[-np.sign(s.loc[c, f"d_{m}"]) * -np.log10(max(s.loc[c, f"p_{m}"], 1e-5)) for m in mets] for c in CELLS])
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.2), gridspec_kw=dict(width_ratios=[1, 1.9]))
    ax = axs[0]
    ax.imshow(M, cmap="RdBu", vmin=-5, vmax=5, aspect="auto")
    for i, c in enumerate(CELLS):
        for j, m in enumerate(mets):
            d, p = s.loc[c, f"d_{m}"], s.loc[c, f"p_{m}"]
            ax.text(j, i, f"{d:+.3f}\np={p:.3f}", ha="center", va="center", fontsize=6.5, color="white" if abs(M[i, j]) > 3 else "#111",
                    fontweight="bold" if p < 0.05 else "normal")
    ax.set_xticks(range(4))
    ax.set_xticklabels(["|Δlog HR|", "z²", "58-var mean |SMD|", "held-out C"], fontsize=7.5)
    ax.set_yticks(range(len(CELLS)))
    ax.set_yticklabels([S8.cell_label(c) for c in CELLS], fontsize=7.5)
    ax.set_title("Engine metrics, ECG − base (18 trials, full)\ncolour = signed −log10 p; blue = ECG better", fontsize=8)
    ax = axs[1]
    cols = [(st, h) for st in SETS for h in ("full", "A", "B")]
    rows_ = SCEN
    Z = np.full((len(rows_), len(cols)), np.nan)
    P = Z.copy()
    for i, (c, sb) in enumerate(rows_):
        for j, (st, h) in enumerate(cols):
            r = G[(G.cell == c) & (G.subset == sb) & (G.set == st) & (G.half == h)]
            if len(r):
                Z[i, j], P[i, j] = r.iloc[0].d_pct_lt10, r.iloc[0].p_pct_lt10
    v = np.nanmax(np.abs(Z))
    ax.imshow(Z, cmap="RdBu", vmin=-v, vmax=v, aspect="auto")
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            if np.isfinite(Z[i, j]):
                stx = "**" if P[i, j] < 0.01 else ("*" if P[i, j] < 0.05 else "")
                ax.text(j, i, f"{Z[i, j]:+.1f}{stx}", ha="center", va="center", fontsize=6.5, color="white" if abs(Z[i, j]) > 0.6 * v else "#111")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([f"{st}\n{h}" for st, h in cols], fontsize=6.5)
    ax.set_yticks(range(len(rows_)))
    ax.set_yticklabels([f"{S8.cell_label(c)} ({'18' if sb == 'all' else '8 phys'})" for c, sb in rows_], fontsize=7)
    ax.set_title("Per set: ECG − base in % of set covariates with |SMD| < 0.1 (pp; * p<0.05, ** p<0.01)", fontsize=8)
    fig.tight_layout()
    fig.savefig(DOCS / "S9_COVSETS_heatmap.png", dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------- report
def _p(x):
    return "—" if x is None or not np.isfinite(x) else (f"{x:.3f}" if x >= 0.001 else "<0.001")


def _f(x, nd=1):
    return "—" if x is None or not np.isfinite(x) else f"{x:+.{nd}f}"


def scen_label(cell, sub):
    return f"{S8.cell_label(cell)} ({'18 trials' if sub == 'all' else '8 physiology trials'})"


def mapping_md():
    L = ["## Set definitions (fixed before any S9 result)\n",
         "### Set 1: plan item → variable (58-panel `p58:`, claude-v16-covars2b `x:`)\n",
         "Every item is used when it is held out from the cell's PS and available in the trial (finite |SMD|). Loop diuretic is "
         "dropped automatically where it is the exposure (TRANSFORM-HF: status dropped_exposure) and by the PS-overlap rule where "
         "a PS contains it. LV mass is not in any available panel. `IVSd > 15 mm` (58-panel) is not listed in the plan and is not used.\n",
         md(pd.DataFrame([dict(group=g, item=it, variables=", ".join(vs) if vs else "not available") for g, it, vs in SET1_MAP])) + "\n",
         f"Set 1 = {len(SET1)} variables.\n",
         "### Set 2: literature core + common items (docs/v16/lit_covariates.json) → variables\n",
         "Variables are the covars2 variables listed for the item in the COVARIATES2 literature cross-check (wildcards expanded on the "
         "covars2b dictionary), plus, for items the cross-check marks as already in an existing panel, the 58-panel (`p58:`) or "
         "claude-v16-covars (`v1:`) variable. Exposure leaks (per-trial status dropped_exposure / *leak* / exposure_leak) and "
         "non-pre-index variables are removed by the loader; per cell, variables in or overlapping the PS are removed. ECG-proximal "
         "variables are kept in Set 2 (a descriptive row, Set 2 non-proximal, drops them).\n"]
    rows = [dict(id=i, item=nm, priority=pr, variables=", ".join(vs) if vs else f"none ({why})") for i, nm, pr, vs, why in lit_map()]
    L += [md(pd.DataFrame(rows)) + "\n", f"Set 2 = {len(set2())} distinct variables before per-trial availability and PS exclusion.\n"]
    return "\n".join(L)


def report():
    os.umask(0o077)
    J = json.loads(SELFILE.read_text())
    V = load_var(["full", "A", "B"])
    df = load_res(["full", "A", "B"])
    if os.environ.get("S9_REUSE") and (OUT / "set_summary.csv").exists():  # re-render from the saved set summary
        G, PT = pd.read_csv(OUT / "set_summary.csv"), pd.read_csv(OUT / "set_per_trial.csv")
    else:
        G, PT = summarize_sets(V, J)
        G.to_csv(OUT / "set_summary.csv", index=False)
        PT.to_csv(OUT / "set_per_trial.csv", index=False)
    # engine summary
    S = []
    eng = df[df.cell != "unmatched"].rename(columns={"arm_role": "arm"})
    for h in ("full", "A", "B"):
        g = eng[eng.half == h]
        for b in ("base", "shufECG", "noise"):
            s = E.summarize_pairs(g, ["cell"], "ECG", b)
            s["half"] = h
            S.append(s)
    S = pd.concat(S, ignore_index=True)
    SB = S[S.arm_b == "base"].copy()
    for m in ("absd", "z2", "mean_smd", "cstat"):
        SB.loc[SB.half == "full", f"q_{m}"] = E.bh_fdr(SB.loc[SB.half == "full", f"p_{m}"].to_numpy())
    S.to_csv(OUT / "engine_summary.csv", index=False)
    heatmaps(SB, G)
    # per-trial set metrics into results.csv
    allv = set(V["var"].unique())
    add = []
    for cell in CELLS:
        for h in ("full", "A", "B"):
            for role in ROLES + ["unmatched"]:
                for sname in SETS + ["SET2np"]:
                    vs = set_vars(sname, cell, "all", allv, J) if sname != "SET3" else None
                    for sub in ("all", "phys"):
                        if sname == "SET3":
                            vs = set_vars("SET3", cell, sub, allv, J)
                        elif sub == "phys":
                            continue
                        A = set_metrics(smd_cube(V, cell, h, role, SUBSETS[sub] if sname == "SET3" else E.TRIALS, vs))
                        tag = sname if sname != "SET3" else f"SET3{'' if sub == 'all' else 'phys'}"
                        for tn, rr in A.iterrows():
                            add.append({"cell": cell, "half": h, "arm_role": role, "trial": tn,
                                        **{f"{tag}_{k}": rr[k] for k in ("n", "pct_lt10", "mean", "pct_gt20")}})
    A = pd.DataFrame(add).groupby(["cell", "half", "arm_role", "trial"]).first().reset_index()
    base_u = df[df.cell == "unmatched"]
    df2 = pd.concat([df[df.cell != "unmatched"].merge(A, on=["cell", "half", "arm_role", "trial"], how="left"),
                     base_u.assign(note="unmatched once per trial/half; set metrics per cell are in rows arm_role=unmatched below")],
                    ignore_index=True)
    un = A[A.arm_role == "unmatched"].merge(base_u.drop(columns=["cell"]), on=["half", "arm_role", "trial"], how="left")
    un["note"] = "unmatched, set metrics restricted to the cell's held-out universe"
    pd.concat([df2, un], ignore_index=True).to_csv(OUT / "results.csv", index=False)
    # domain summaries
    DH = domain_summary(V, "demo|cal0.1", "all")
    DH.to_csv(OUT / "domain_headline.csv", index=False)
    DS = domain_summary(V, "sparse|default", "all")
    DS.to_csv(OUT / "domain_sparse.csv", index=False)
    domain_plot(DH, "Headline scenario (demo PS, 1:1 caliper 0.1, 18 trials): held-out balance by covariate domain without vs with AI-ECG",
                "S9_DOMAINS_demo_cal01.png")
    domain_plot(DS, "Reference (sparse PS, 18 trials): held-out balance by covariate domain without vs with AI-ECG", "S9_DOMAINS_sparse.png")
    figs = ["S9_COVSETS_heatmap.png", "S9_DOMAINS_demo_cal01.png", "S9_DOMAINS_sparse.png"]
    for cell, slug in (("demo|cal0.1", "demo_cal01"), ("sparse|default", "sparse")):
        for sname in ("SET1", "SET2", "SET3"):
            vs = set_vars(sname, cell, "all", allv, J)
            r = G[(G.cell == cell) & (G.subset == "all") & (G.set == sname) & (G.half == "full")].iloc[0]
            fn = f"S9_LOVE_{sname}_{slug}.png"
            loveplot_set(V, cell, "all", sname, vs, fn, f"{SET_LAB[sname]}. {scen_label(cell, 'all')}: held-out balance without vs with AI-ECG",
                         _p(r.p_pct_lt10))
            figs.append(fn)
    write_md(G, SB, S, DH, DS, J, df, figs)


def row_txt(r, with_q=True):
    d = {"set": SET_LAB[r.set], "half": r.half, "vars (median avail.)": f"{r.n_set} ({r.n_avail_med:.0f})",
         "% <0.1 unm / base → ECG": f"{r.unmatched_pct_lt10:.1f} / {r.base_pct_lt10:.1f} → {r.ECG_pct_lt10:.1f}",
         "d (k), p": f"{_f(r.d_pct_lt10)} ({r.k_pct_lt10}), {_p(r.p_pct_lt10)}",
         "vs shuf / noise d (p)": f"{_f(r.d_shuf_pct_lt10)} ({_p(r.p_shuf_pct_lt10)}) / {_f(r.d_noise_pct_lt10)} ({_p(r.p_noise_pct_lt10)})",
         "shuf−base / noise−base": f"{_f(r.d_shufbase_pct_lt10)} / {_f(r.d_noisebase_pct_lt10)}",
         "cluster p (k) / LOO": f"{_p(r.clp_pct_lt10)} ({r.clk_pct_lt10}) / {_p(r.loo_pct_lt10)}",
         "love <0.1 unm / base → ECG (p)": f"{r.love_unmatched} / {r.love_base} → {r.love_ECG} of {r.love_n} ({_p(r.p_love)})",
         "love shuf / noise": f"{r.love_shufECG} / {r.love_noise}",
         "mean |SMD| base → ECG (p)": f"{r.base_mean:.3f} → {r.ECG_mean:.3f} ({_p(r.p_mean)})",
         "% >0.2 base → ECG (p)": f"{r.base_pct_gt20:.1f} → {r.ECG_pct_gt20:.1f} ({_p(r.p_pct_gt20)})"}
    if with_q:
        d["q (%<0.1 / love / mean / >0.2)"] = "—" if not r.family else \
            f"{_p(r.q_pct_lt10)} / {_p(r.q_love)} / {_p(r.q_mean)} / {_p(r.q_pct_gt20)}"
    return d


def write_md(G, SB, S, DH, DS, J, df, figs):
    L = [f"# v1.6 S9: covariate sets — where adding AI-ECG moves held-out covariates below |SMD| 0.1 ({time.strftime('%Y-%m-%d')})\n",
         "Exploratory. Plan: `docs/v16/S9_COVARIATE_SETS_PLAN.md` (committed before any S9 result). Script `scripts/v16/s9_covsets.py`; "
         "outputs `/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s9-covsets/` (`results.csv`, `set_summary.csv`, `set_per_trial.csv`, "
         "`engine_summary.csv`, `domain_*.csv`, `var_*.parquet`). Set-3 selection: `docs/v16/selection_S9.json`. Aggregates only.\n",
         "## Key findings\n"]
    kf = OUT / "key_findings.md"
    L.append(kf.read_text() if kf.exists() else "(pending)\n")
    L.append(mapping_md())
    L += ["### Set 3: split-sample selection (half A only; committed before half-B / full)\n", f"Rule: {J['rule']}\n",
          f"Selection timestamp **{J['created']}**; halves present at selection: {J['halves_available_at_selection']}; pool {J['n_pool']} variables.\n"]
    rows = []
    for k, v in J["scenarios"].items():
        c, s = k.split("@")
        rows.append({"scenario": scen_label(c, s), "candidates": v["n_candidates"],
                     "selected (half-A gain in mean |SMD|)": ", ".join(f"{_pretty(x['var'])} ({x['gain']:+.3f})" for x in v["detail"])})
    L += [md(pd.DataFrame(rows)) + "\n",
          "FULL = the 58-panel plus every claude-v16-covars2b non-ECG-proximal variable held out from the cell's PS (the Set-3 pool).\n"]
    L += ["## Results by scenario\n",
          "Per trial: % of the set's available variables with |SMD| < 0.1 (primary), mean |SMD|, % > 0.2; averaged over trials. d = ECG − base "
          "(pp for %; k = trials improved); p = exact sign-flip over trials; placebo columns: ECG − shufECG / ECG − noise and placebo − base; "
          "cluster = sign-flip over comparator clusters; LOO = max p leaving one trial out. Love = number of set variables whose median |SMD| "
          "across trials is < 0.1 (p: trial-level arm-swap permutation). q = BH over 9 scenarios × 4 sets × 4 metrics within half. "
          "Unmatched values use the same held-out variables as the cell. Set 3 in the full cohort includes half A (the selection sample); "
          "half B is the out-of-sample confirmation.\n"]
    for cell, sub in SCEN + SCEN_DESC:
        g = G[(G.cell == cell) & (G.subset == sub)]
        rows = [row_txt(r) for _, r in g.sort_values(["set", "half"], key=lambda s: s.map({**{x: i for i, x in enumerate(SETS + ['SET2np'])},
                                                                                          "full": 0, "A": 1, "B": 2})).iterrows()]
        tag = " (descriptive; not in the FDR family)" if (cell, sub) in SCEN_DESC else ("" if cell in HEADLINE else " (reference)")
        L += [f"### {scen_label(cell, sub)}{tag}\n", md(pd.DataFrame(rows)) + "\n"]
    for nm, D in (("Headline scenario (demo, caliper 0.1, 18 trials)", DH), ("Sparse reference (18 trials)", DS)):
        t = pd.DataFrame({"domain": D.domain, "vars": D.n_vars, "mean |SMD| unm / base → ECG": [f"{a:.3f} / {b:.3f} → {c:.3f}" for a, b, c in
                                                                                                zip(D.unmatched_mean, D.base_mean, D.ECG_mean)],
                          "d (k)": [f"{d:+.4f} ({k})" for d, k in zip(D.d, D.k)], "p": D.p.map(_p), "q (domains)": D.q.map(_p),
                          "vs shuf / noise p": [f"{_p(a)} / {_p(b)}" for a, b in zip(D.p_shuf, D.p_noise)],
                          "love <0.1 unm / base → ECG": [f"{a} / {b} → {c}" for a, b, c in zip(D.love_unmatched, D.love_base, D.love_ECG)]})
        L += [f"## Domain-level balance: {nm}\n", "Domain mean |SMD| per trial (mean over the domain's available variables), then over trials; "
              "paired sign-flip ECG − base; BH over domains.\n", md(t) + "\n"]
    rows = []
    for c in CELLS:
        d = {"cell": S8.cell_label(c)}
        for h in ("full", "A", "B"):
            r = SB[(SB.cell == c) & (SB.half == h)].iloc[0]
            for m, nd in (("absd", 3), ("z2", 2), ("mean_smd", 4), ("cstat", 3)):
                if h == "full":
                    d[f"{m} d (k, p)"] = f"{r[f'd_{m}']:+.{nd}f} ({r[f'k_{m}']}, {_p(r[f'p_{m}'])})"
                else:
                    d[f"{m} {h} p"] = _p(r[f"p_{m}"])
        r = SB[(SB.cell == c) & (SB.half == "full")].iloc[0]
        d["q |Δ| / z² / SMD / C"] = f"{_p(r.q_absd)} / {_p(r.q_z2)} / {_p(r.q_mean_smd)} / {_p(r.q_cstat)}"
        for b in ("shufECG", "noise"):
            rb_ = S[(S.cell == c) & (S.half == "full") & (S.arm_b == b)].iloc[0]
            d[f"vs {b} p (|Δ|, SMD)"] = f"{_p(rb_.p_absd)}, {_p(rb_.p_mean_smd)}"
        d["consistency % base→ECG"] = f"{r.cons_b:.0f}→{r.cons_a:.0f}"
        d["φ base→ECG"] = f"{r.phi_b:.2f}→{r.phi_a:.2f}"
        rows.append(d)
    L += ["## Engine metrics (standard sweep summary; ECG vs base, 18 trials)\n",
          "E.summarize_pairs; negative d = ECG better; q = BH over the 6 cells (full). Heat map `docs/v16/S9_COVSETS_heatmap.png` "
          "(left: these metrics; right: set % < 0.1 across scenarios × sets × halves).\n", md(pd.DataFrame(rows)) + "\n"]
    L += ["## Figures\n", "".join(f"- `docs/v16/{f}`\n" for f in figs)]
    af = OUT / "audit.md"
    L += ["## Audit\n", S8.audit_checks(df).replace("|S8 − ENGINE", "|S9 − ENGINE"), af.read_text() if af.exists() else ""]
    g = G[(G.half == "full") & G.family]
    L += [f"**Placebo − base over the {len(g)} family rows** (full, % < 0.1): shufECG − base mean {g.d_shufbase_pct_lt10.mean():+.2f} pp "
          f"(p<0.05: better {int(((g.p_shufbase_pct_lt10 < 0.05) & (g.d_shufbase_pct_lt10 > 0)).sum())}, worse "
          f"{int(((g.p_shufbase_pct_lt10 < 0.05) & (g.d_shufbase_pct_lt10 < 0)).sum())}); noise − base {g.d_noisebase_pct_lt10.mean():+.2f} pp "
          f"(better {int(((g.p_noisebase_pct_lt10 < 0.05) & (g.d_noisebase_pct_lt10 > 0)).sum())}, worse "
          f"{int(((g.p_noisebase_pct_lt10 < 0.05) & (g.d_noisebase_pct_lt10 < 0)).sum())}); ECG − base {g.d_pct_lt10.mean():+.2f} pp.\n"]
    dv = OUT / "deviations.md"
    L += ["## Deviations from the plan and clarifications\n", dv.read_text() if dv.exists() else "(none)\n"]
    (DOCS / "S9_COVSETS.md").write_text("\n".join(L))
    print("report written")


def write_mapping_only():
    """pre-results: write the set-definition section (committed before any computation)."""
    (DOCS / "S9_COVSETS.md").write_text("# v1.6 S9: covariate sets (definitions; results pending)\n\n" + mapping_md())
    print(f"SET1 {len(SET1)} SET2 {len(set2())}")


def fingerprint():
    h = hashlib.md5()
    for f in sorted(COV2B.glob("*.parquet")) + [COV2B / "dictionary.csv", COV2B / "trial_variable_status.csv", HERE / "s6_balance.py"]:
        h.update(f.read_bytes())
    return h.hexdigest()


def main():
    global CELLS
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["run", "select", "summarize", "mapping", "fingerprint"])
    ap.add_argument("--halves", default="A")
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--cells", default=None)
    ap.add_argument("--out", default=None, help="output dir override (audit test runs)")
    a = ap.parse_args()
    global OUT
    if a.out:
        OUT = Path(a.out)
    if a.mode == "run":
        if a.cells:
            CELLS = a.cells.split(",")
        print("covars2b + s6_balance fingerprint", fingerprint(), flush=True)
        hv = a.halves.split(",")
        run(a.trials.split(","), hv, a.workers, a.tag or "_".join(hv))
    elif a.mode == "select":
        select()
    elif a.mode == "summarize":
        report()
    elif a.mode == "mapping":
        write_mapping_only()
    elif a.mode == "fingerprint":
        print(fingerprint())


if __name__ == "__main__":
    main()
