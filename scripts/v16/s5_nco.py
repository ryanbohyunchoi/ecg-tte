#!/usr/bin/env python
"""v1.6 sweep S5: negative-control outcomes (NCOs) across PS set points (exploratory; docs/v16/S5_NCO.md).

Question: does adding the BCL AI-ECG (32 PCs) to a PS move negative-control HRs (truth log HR = 0) toward the
null, i.e. is there direct evidence of reduced confounding?  Placebo-controlled (shufECG, noise32), all halves.

NCOs: trial_specs.NCO_EXT (25; v1.3 extraction, restricted_outcomes_v13.parquet) + 12 new v1.6 NCOs
(s5_nco_extract.py; identical conventions).  Pharmacological exclusions per trial (EXCL, hard) and cautions
(CAUTION; dropped in the "strict" sensitivity set).  Eligibility per trial x NCO (fixed on the full cohort,
before any matching): pooled events >= 30 in the analysable unmatched cohort at the trial horizon
(sensitivity: >= 20 events in each arm).
Rungs (s1_ladder.base_designs): r1_demo, r3_min7, r5_sparse, r7_hdPS200, r8_clinical; roles base / ECG /
shufECG / noise (s1_ladder conventions) + unmatched.  Matched sets replicate E.run_cell (l2 C=1 PS, 1:1 greedy
caliper 0.2; v13_common.ps_logit / match): the primary Cox is re-estimated on the same set and checked against
S1's run_cell output (n_pairs, log HR).  NCO Cox exactly as v13_design (pair-clustered robust SE, time from index,
capped at the trial horizon, rows with the NCO in the prior 365 d removed, primary-outcome exclusions applied).

Usage: s5_nco.py run [--trials a,b] [--workers 40] [--out DIR]
       s5_nco.py summarize [--out DIR]          (tables, figure, markdown; includes OUT/audit.md)
       s5_nco.py audit [--out DIR]              (checks -> OUT/audit.md; needs summarize outputs; re-run summarize after)
Aggregates only (event counts 1-10 suppressed in every written file).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import argparse  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import minimize  # noqa: E402
from scipy.stats import norm  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v16_engine as E  # noqa: E402
from s1_ladder import base_designs, halves, load_new  # noqa: E402
from s5_nco_extract import NEW_NCO  # noqa: E402
from s5_nco_extract import OUT as XOUT  # noqa: E402
from trial_specs import NCO_EXT  # noqa: E402
from v13_common import A, cox, match, ps_logit  # noqa: E402

SWEEP = "s5-nco"
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s5-nco")
DOCS = HERE.parent.parent / "docs" / "v16"
S1 = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s1-ladder/results.csv")
NCOS = list(NCO_EXT) + list(NEW_NCO)
RUNGS = [("r1_demo", "demo"), ("r3_min7", "minimal-7"), ("r5_sparse", "sparse"), ("r7_hdPS200", "hdPS200"),
         ("r8_clinical", "clinical")]
RUNG_LAB = dict(RUNGS)
ROLES = ["base", "ECG", "shufECG", "noise"]
MIN_POOLED, MIN_ARM = 30, 20

# ---------------------------------------------------------------- pharmacological plausibility
# drug classes of the two arms
CLASSES = {"comet": ["BB"], "paradigm-hf-seq": ["ARNI", "ACEi"], "transform-hf": ["LOOP"], "elite-ii": ["ARB", "ACEi"],
           "life": ["ARB", "BB"], "plato": ["P2Y12"], "aristotle": ["OAC"], "rocket-af": ["OAC"], "rely": ["OAC"],
           "allhat": ["CCB", "THZ"], "emperor-preserved-v2": ["SGLT2", "DPP4"], "east-afnet4": ["AAD", "BB"],
           "cabana-v2": ["ABL", "AAD"], "ontarget": ["ARB", "ACEi"], "value": ["ARB", "CCB"], "ascot": ["CCB", "BB"],
           "empa-reg": ["SGLT2", "DPP4"], "carolina": ["DPP4", "SU"]}
# hard exclusions (plausible drug effect on the NCO or its ascertainment)
EXCL_CLASS = {
    "ACEi": {"nco_allergic_rhinitis": "ACEi/ARNI bradykinin rhinitis and cough can be coded as rhinitis"},
    "ARNI": {"nco_allergic_rhinitis": "ACEi/ARNI bradykinin rhinitis and cough can be coded as rhinitis"},
    "CCB": {"nco_carpal_tunnel": "dihydropyridine CCB peripheral oedema (median-nerve compression)",
            "nco_dental_caries": "CCB gingival hyperplasia (dental visits / plaque)"},
    "THZ": {"nco_skin_cancer": "thiazide photosensitivity; HCTZ-NMSC association",
            "nco_actinic_keratosis": "thiazide photosensitivity"},
    "LOOP": {"nco_hearing_loss": "loop-diuretic ototoxicity (furosemide vs torsemide potency/dosing)"},
    "AAD": {"nco_skin_cancer": "amiodarone photosensitivity", "nco_actinic_keratosis": "amiodarone photosensitivity",
            "nco_cataract": "amiodarone lens/corneal deposits and eye monitoring"},
    "ABL": {"nco_hernia": "femoral venous access for ablation (groin complications / exam)"},
    "DPP4": {"nco_cholelithiasis": "DPP-4 inhibitor gallbladder/biliary signal",
             "nco_allergic_rhinitis": "DPP-4 inhibitor nasopharyngitis / upper-airway adverse events"},
}
# cautions (kept in the main set; dropped in the strict sensitivity set)
CAUTION_CLASS = {
    "OAC": {"nco_cataract": "elective surgery timing around anticoagulation (warfarin bridging)",
            "nco_hernia": "elective surgery timing around anticoagulation (warfarin bridging)"},
    "P2Y12": {"nco_cataract": "elective surgery deferred on potent antiplatelet therapy",
              "nco_hernia": "elective surgery deferred on potent antiplatelet therapy"},
    "DPP4": {"nco_knee_oa": "DPP-4 inhibitor arthralgia warning", "nco_hip_oa": "DPP-4 inhibitor arthralgia warning",
             "nco_rotator_cuff": "DPP-4 inhibitor arthralgia warning"},
    "SGLT2": {"nco_onychomycosis": "glycosuria-related fungal infection (dermatophyte, weak)",
              "nco_knee_oa": "weight loss", "nco_hip_oa": "weight loss"},
    "LOOP": {"nco_skin_cancer": "furosemide photosensitivity (weak)", "nco_actinic_keratosis": "furosemide photosensitivity (weak)"},
    "SU": {"nco_skin_cancer": "sulfonylurea photosensitivity (rare)", "nco_actinic_keratosis": "sulfonylurea photosensitivity (rare)"},
    "AAD": {"nco_conjunctivitis": "amiodarone ocular effects", "nco_carpal_tunnel": "amiodarone neuropathy"},
    "CCB": {"nco_plantar_fasciitis": "peripheral oedema (weak)"},
}


def excl(n, kind="hard"):
    src = EXCL_CLASS if kind == "hard" else CAUTION_CLASS
    out = {}
    for c in CLASSES[n]:
        out.update(src.get(c, {}))
    return out


# ---------------------------------------------------------------- data
def nco_arrays(T):
    """name -> (t capped at horizon, event at horizon, usable mask) aligned to T.keys."""
    O3 = pd.read_parquet(f"{A}/claude-{T.n}-outcomes-v13/restricted_outcomes_v13.parquet").set_index("patient_key").reindex(T.keys)
    ON = pd.read_parquet(XOUT / f"restricted_nco_{T.n}.parquet").set_index("patient_key").reindex(T.keys)
    H = T.horizon
    out = {}
    for nm in NCOS:
        O = O3 if nm in NCO_EXT else ON
        tn, en = O[f"t_{nm}"].to_numpy(float), O[f"e_{nm}"].to_numpy(float)
        ok = ~np.isnan(tn) & T.y_ok
        out[nm] = (np.minimum(np.nan_to_num(tn, nan=0.0), H), ((en == 1) & (tn <= H) & ok).astype(int), ok)
    return out


def sup(k):
    k = int(k)
    return k if (k == 0 or k >= 11) else np.nan


def run_trial_half(args):
    n, half = args
    t0 = time.time()
    i = E.TRIALS.index(n)
    T = E.load_trial(n)
    C = load_new(T)
    NC = nco_arrays(T)
    hard = excl(n, "hard")
    # eligibility on the full unmatched cohort (fixed before matching; same for every half)
    elig = {}
    for nm, (tt, ee, ok) in NC.items():
        et, ec = int(ee[(T.t == 1) & ok].sum()), int(ee[(T.t == 0) & ok].sum())
        elig[nm] = dict(pooled=et + ec >= MIN_POOLED, per_arm=min(et, ec) >= MIN_ARM, hard_excl=nm in hard)
    rows = halves(T, i)[half]
    t = T.t[rows]
    D = base_designs(T, C, rows, t)
    pc = T.ecg_pc[rows]
    placebo = {"ECG": pc, "shufECG": T.ecg_pc[T.shuffle_perm][rows], "noise": T.noise32[rows]}
    yt, ye, yok = T.y_t[rows], T.y_e[rows], T.y_ok[rows]
    prim, ncos = [], []

    def one(cell, role, label, X):
        if X is None:
            s_idx, cl, npairs = np.arange(len(rows)), None, np.nan
        else:
            lg = ps_logit(np.asarray(X, float), t, model="l2", C=1.0, seed=0)
            s_idx, cl, _ = match(lg, t, cal=0.2, ratio=1)
            npairs = int(len(np.unique(cl)))
        m = yok[s_idx]
        b, se = cox(yt[s_idx][m], ye[s_idx][m], t[s_idx][m], cluster=None if cl is None else cl[m])
        base = dict(sweep=SWEEP, cell=cell, rung_label=RUNG_LAB.get(cell, cell), trial=n, half=half, arm_role=role,
                    arm_label=label)
        prim.append(dict(**base, n=len(rows), n_pairs=npairs, loghr=b, se=se, rb=T.rb, rs=T.rs))
        for nm, (tt, ee, ok) in NC.items():
            if elig[nm]["hard_excl"] or not (elig[nm]["pooled"] or elig[nm]["per_arm"]):
                continue
            tr = rows[s_idx]
            mm = ok[tr]
            x = t[s_idx][mm]
            e_ = ee[tr][mm]
            bn, sn = cox(tt[tr][mm], e_, x, cluster=None if cl is None else cl[mm])
            ncos.append(dict(**base, nco=nm, loghr=bn, se=sn, n_at_risk=int(mm.sum()),
                             ev_t=sup(e_[x == 1].sum()), ev_c=sup(e_[x == 0].sum()),
                             elig_pooled=elig[nm]["pooled"], elig_per_arm=elig[nm]["per_arm"]))

    one("unmatched", "unmatched", "unmatched", None)
    for cell, lab in RUNGS:
        X = D[cell][0]
        one(cell, "base", lab, X)
        for role, P in placebo.items():
            one(cell, role, f"{lab}+{role}", np.hstack([X, P]))
    print(f"{n} {half} done {time.time() - t0:.0f}s", flush=True)
    return prim, ncos


def run(trials, workers, out):
    from multiprocessing import Pool
    os.umask(0o077)
    out.mkdir(parents=True, exist_ok=True)
    tasks = [(n, h) for n in trials for h in ("full", "A", "B")]
    size = {n: len(E.load_trial(n).t) for n in trials}
    tasks.sort(key=lambda x: -size[x[0]])
    with Pool(min(workers, len(tasks), 40)) as p:
        res = p.map(run_trial_half, tasks, chunksize=1)
    P = pd.DataFrame([r for rr in res for r in rr[0]])
    N = pd.DataFrame([r for rr in res for r in rr[1]])
    P.to_csv(out / "primary_raw.csv", index=False)
    N.to_csv(out / "nco_estimates.csv", index=False)
    print("wrote", out, P.shape, N.shape)


# ---------------------------------------------------------------- statistics
def fit_syserr(b, se):
    """OHDSI-style systematic-error model b_i ~ N(mu, sigma^2 + se_i^2), ML (as v13_summarize.fit_syserr)."""
    b, se = np.asarray(b, float), np.asarray(se, float)
    ok = np.isfinite(b) & np.isfinite(se)
    b, se = b[ok], se[ok]
    if len(b) < 3:
        return np.nan, np.nan, len(b)
    nll = lambda p: -np.sum(norm.logpdf(b, p[0], np.sqrt(np.exp(2 * p[1]) + se ** 2)))
    r = minimize(nll, [0.0, np.log(0.1)], method="Nelder-Mead", options=dict(xatol=1e-6, fatol=1e-8, maxiter=4000))
    return float(r.x[0]), float(np.exp(r.x[1])), len(b)


def ease(mu, sd):
    """Expected absolute systematic error E|N(mu, sd^2)| (OHDSI EASE)."""
    if not np.isfinite(mu) or not np.isfinite(sd):
        return np.nan
    if sd < 1e-9:
        return abs(mu)
    return float(sd * np.sqrt(2 / np.pi) * np.exp(-mu ** 2 / (2 * sd ** 2)) + mu * (1 - 2 * norm.cdf(-mu / sd)))


def sflip(d):
    """(mean, exact two-sided sign-flip p, 'k improved/n'); p identical to v13_summarize.sign_flip (cached signs)."""
    from audit_v16 import sflip as _sf
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    return (float(d.mean()), _sf(d), f"{int((d < 0).sum())}/{len(d)}") if len(d) else (np.nan, np.nan, "0/0")


def cluster_flip(s):
    """sign-flip over comparator-cluster means (audit_v16.CLUSTER)."""
    from audit_v16 import CLUSTER
    g = s.groupby(s.index.map(CLUSTER)).mean()
    return sflip(g.to_numpy())


def nco_set(N, kind):
    """Filter NCO rows to the analysis set: 'main' (pooled>=30, no hard exclusion), 'strict' (also no cautions),
    'per_arm' (>=20 events per arm). Then keep, per trial x half, NCOs estimable in every arm of that trial-half."""
    if kind == "per_arm":
        M = N[N.elig_per_arm]
    else:
        M = N[N.elig_pooled]
        if kind == "strict":
            M = M[[nm not in excl(tr, "caution") for tr, nm in zip(M.trial, M.nco)]]
    M = M.copy()
    M["fin"] = np.isfinite(M.loghr) & np.isfinite(M.se)
    narm = M.groupby(["trial", "half"]).apply(lambda g: g[["cell", "arm_role"]].drop_duplicates().shape[0]).rename("narm")
    okn = M.groupby(["trial", "half", "nco"]).fin.agg(["sum"]).join(narm, on=["trial", "half"])
    okn = okn[okn["sum"] == okn.narm].reset_index()[["trial", "half", "nco"]]
    return M.merge(okn, on=["trial", "half", "nco"])


def per_trial_metrics(M):
    """trial x half x cell x role: mean |b|, mean z2, % CI excluding 1, mean (b^2 - se^2), trial-level mu/sigma/EASE;
    z2_fixse = mean b^2 / se_base^2 (same NCO's SE in the rung's base arm; removes the SE-inflation route by which a
    smaller matched set lowers z2); lse = mean log(se / se_base)."""
    ref = M[M.arm_role.isin(["base", "unmatched"])][["trial", "half", "cell", "nco", "se"]].rename(columns={"se": "se_ref"})
    M = M.merge(ref, on=["trial", "half", "cell", "nco"], how="left")
    rows = []
    for key, g in M.groupby(["trial", "half", "cell", "arm_role"]):
        b, se, sr = g.loghr.to_numpy(), g.se.to_numpy(), g.se_ref.to_numpy()
        mu, sd, k = fit_syserr(b, se)
        rows.append(dict(zip(["trial", "half", "cell", "arm_role"], key), n_nco=len(g), abs_b=np.mean(np.abs(b)),
                         z2=np.mean(b ** 2 / se ** 2), frac_sig=np.mean(np.abs(b / se) > 1.96), b2x=np.mean(b ** 2 - se ** 2),
                         z2_fixse=np.mean(b ** 2 / sr ** 2), lse=np.mean(np.log(se / sr)),
                         mean_b=np.mean(b), mu=mu, sigma=sd, ease=ease(mu, sd)))
    return pd.DataFrame(rows)


def pooled_sigma_perm(M, cells, nperm=500, seed=16066):
    """Pooled OHDSI sigma/EASE: arm a minus arm b, p from swapping the two arms' NCO sets within random trials."""
    rng = np.random.default_rng(seed)
    rows = []
    for half in ("full", "A", "B"):
        for cell in cells:
            for a, b in ((("ECG", "base"), ("shufECG", "base"), ("noise", "base"), ("ECG", "shufECG"), ("ECG", "noise"))
                         if half == "full" else (("ECG", "base"),)):
                g = M[(M.half == half) & (M.cell == cell)]
                Ga = {n: x for n, x in g[g.arm_role == a].groupby("trial")}
                Gb = {n: x for n, x in g[g.arm_role == b].groupby("trial")}
                tr = sorted(set(Ga) & set(Gb))

                def stat(sw):
                    A_ = pd.concat([Gb[n] if s else Ga[n] for n, s in zip(tr, sw)])
                    B_ = pd.concat([Ga[n] if s else Gb[n] for n, s in zip(tr, sw)])
                    ma, sa, _ = fit_syserr(A_.loghr, A_.se)
                    mb, sb, _ = fit_syserr(B_.loghr, B_.se)
                    return sa - sb, ease(ma, sa) - ease(mb, sb)

                o = stat([False] * len(tr))
                null = np.array([stat(rng.random(len(tr)) < 0.5) for _ in range(nperm)])
                rows.append(dict(half=half, cell=cell, a=a, b=b, d_sigma=o[0], p_sigma=float(np.mean(np.abs(null[:, 0]) >= abs(o[0]) - 1e-12)),
                                 d_ease=o[1], p_ease=float(np.mean(np.abs(null[:, 1]) >= abs(o[1]) - 1e-12))))
    return pd.DataFrame(rows)


METRICS = ["abs_b", "z2", "z2_fixse", "frac_sig", "b2x", "ease", "lse"]
METLAB = {"abs_b": "mean |log HR_NCO|", "z2": "mean z² (b²/se²)", "frac_sig": "fraction 95% CI excl. 1",
          "b2x": "mean (b² − se²)", "ease": "trial EASE (E|syst. error|)",
          "z2_fixse": "mean b²/se_base² (fixed SE)", "lse": "mean log(se/se_base) (precision)"}


def paired(PT, half, cell, a, b, m):
    g = PT[(PT.half == half) & (PT.cell == cell)]
    xa = g[g.arm_role == a].set_index("trial")[m]
    xb = g[g.arm_role == b].set_index("trial")[m]
    tt = xa.index.intersection(xb.index)
    d = (xa.loc[tt] - xb.loc[tt])
    return d


def contrasts(PT, cells):
    rows = []
    for half in ("full", "A", "B"):
        for cell in cells:
            for a, b in (("ECG", "base"), ("shufECG", "base"), ("noise", "base"), ("ECG", "shufECG"), ("ECG", "noise"),
                         ("base", "unmatched")):
                for m in METRICS:
                    if b == "unmatched":
                        g = PT[(PT.half == half)]
                        xa = g[(g.cell == cell) & (g.arm_role == a)].set_index("trial")[m]
                        xb = g[g.arm_role == "unmatched"].set_index("trial")[m]
                        tt = xa.index.intersection(xb.index)
                        d = xa.loc[tt] - xb.loc[tt]
                    else:
                        d = paired(PT, half, cell, a, b, m)
                    mean, p, k = sflip(d.to_numpy())
                    r = dict(half=half, cell=cell, a=a, b=b, metric=m, d=mean, k=k, p=p, n_trials=len(d))
                    if half == "full":
                        cm, cp, ck = cluster_flip(d)
                        r.update(d_cluster=cm, p_cluster=cp, k_cluster=ck)
                        loo = [sflip(d.drop(tr).to_numpy())[1] for tr in d.index]
                        r.update(p_loo_min=min(loo), p_loo_max=max(loo), loo_lost=int(np.sum(np.array(loo) >= 0.05)))
                    rows.append(r)
    R = pd.DataFrame(rows)
    R["q_bh"] = np.nan
    for m in METRICS:  # BH within metric over rungs, ECG vs base, full cohort
        s = (R.half == "full") & (R.a == "ECG") & (R.b == "base") & (R.metric == m)
        R.loc[s, "q_bh"] = E.bh_fdr(R.loc[s, "p"].to_numpy())
    s = (R.half == "full") & (R.a == "ECG") & (R.b == "base") & (R.metric != "lse")
    R.loc[s, "q_bh_family"] = E.bh_fdr(R.loc[s, "p"].to_numpy())  # over rungs x metrics
    return R


def pooled_syserr(M):
    rows = []
    for key, g in M.groupby(["half", "cell", "arm_role"]):
        mu, sd, k = fit_syserr(g.loghr, g.se)
        rows.append(dict(zip(["half", "cell", "arm_role"], key), mu=mu, sigma=sd, ease=ease(mu, sd), n_est=k,
                         n_trials=g.trial.nunique()))
    return pd.DataFrame(rows)


def calibrate(P, M, PT):
    """Empirically calibrate each primary log HR with its own NCO systematic-error fit (trial x half x cell x role):
    b* = b - mu, se* = sqrt(se^2 + sigma^2).  Trial fit if >= 8 NCOs else pooled over the other trials
    (same half/cell/role).  Variant 'pooled_loo': always the leave-this-trial-out pooled fit."""
    out = []
    for key, g in P.groupby(["half", "cell", "arm_role"]):
        half, cell, role = key
        Mg = M[(M.half == half) & (M.cell == cell) & (M.arm_role == role)]
        for _, r in g.iterrows():
            tp = PT[(PT.trial == r.trial) & (PT.half == half) & (PT.cell == cell) & (PT.arm_role == role)]
            mo, so, ko = fit_syserr(Mg[Mg.trial != r.trial].loghr, Mg[Mg.trial != r.trial].se)
            if len(tp) and tp.n_nco.iloc[0] >= 8 and np.isfinite(tp.mu.iloc[0]):
                mu, sd, src = tp.mu.iloc[0], tp.sigma.iloc[0], "trial"
            else:
                mu, sd, src = mo, so, "pooled_loo"
            for var, (m_, s_) in (("own", (mu, sd)), ("pooled_loo", (mo, so))):
                out.append(dict(trial=r.trial, half=half, cell=cell, arm_role=role, calib=var, source=src if var == "own" else var,
                                loghr=r.loghr - m_, se=np.sqrt(r.se ** 2 + s_ ** 2), loghr_raw=r.loghr, se_raw=r.se,
                                mu=m_, sigma=s_, rb=r.rb, rs=r.rs))
    return pd.DataFrame(out)


def agree_contrasts(Cal, cells, rng_seed=16065, nperm=2000):
    """ECG vs base (and placebos) on |dlogHR| and z2 vs RCT with calibrated (and raw) estimates; shuffled-benchmark null."""
    rows = []
    rng = np.random.default_rng(rng_seed)
    for (half, calib), G in Cal.groupby(["half", "calib"]):
        for cell in cells:
            g = G[G.cell == cell]
            for est in ("raw", "cal"):
                lh = "loghr_raw" if est == "raw" else "loghr"
                sh = "se_raw" if est == "raw" else "se"
                if est == "raw" and calib != "own":
                    continue
                W = {r: g[g.arm_role == r].set_index("trial") for r in ROLES}
                tt = W["base"].index
                for r in ROLES:
                    tt = tt.intersection(W[r].dropna(subset=[lh, sh]).index)
                rb, rs = W["base"].loc[tt].rb.to_numpy(), W["base"].loc[tt].rs.to_numpy()
                f = {"absd": lambda x, rb=rb: np.abs(x[lh].to_numpy() - rb),
                     "z2": lambda x, rb=rb, rs=rs: (x[lh].to_numpy() - rb) ** 2 / (x[sh].to_numpy() ** 2 + rs ** 2)}
                for a, b in (("ECG", "base"), ("shufECG", "base"), ("noise", "base")):
                    for m, fn in f.items():
                        d = fn(W[a].loc[tt]) - fn(W[b].loc[tt])
                        mean, p, k = sflip(d)
                        r = dict(half=half, calib=calib, est=est, cell=cell, a=a, b=b, metric=m, d=mean, k=k, p=p,
                                 n_trials=len(tt), mean_a=float(np.mean(fn(W[a].loc[tt]))), mean_b=float(np.mean(fn(W[b].loc[tt]))))
                        if half == "full" and a == "ECG":
                            null = []
                            for _ in range(nperm):
                                pi = rng.permutation(len(tt))
                                rb2, rs2 = rb[pi], rs[pi]
                                if m == "absd":
                                    dd = np.abs(W[a].loc[tt][lh].to_numpy() - rb2) - np.abs(W[b].loc[tt][lh].to_numpy() - rb2)
                                else:
                                    dd = ((W[a].loc[tt][lh].to_numpy() - rb2) ** 2 / (W[a].loc[tt][sh].to_numpy() ** 2 + rs2 ** 2)
                                          - (W[b].loc[tt][lh].to_numpy() - rb2) ** 2 / (W[b].loc[tt][sh].to_numpy() ** 2 + rs2 ** 2))
                                null.append(dd.mean())
                            null = np.array(null)
                            r.update(shuf_null_median=float(np.median(null)), p_shuf=float(np.mean(null <= mean)))
                            from audit_v16 import CLUSTER
                            s = pd.Series(d, index=tt)
                            cm, cp, ck = cluster_flip(s)
                            r.update(p_cluster=cp, k_cluster=ck)
                        rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- summarize
def summarize(out):
    P = pd.read_csv(out / "primary_raw.csv")
    N = pd.read_csv(out / "nco_estimates.csv")
    cells = [c for c, _ in RUNGS]
    # --- verification against S1 (run_cell)
    s1 = pd.read_csv(S1)
    s1 = s1[s1.cell.isin(cells + ["unmatched"])]
    V = P.merge(s1[["cell", "trial", "half", "arm_role", "n_pairs", "loghr", "se", "mean_smd", "cstat"]],
                on=["cell", "trial", "half", "arm_role"], suffixes=("", "_s1"), how="left")
    V["dpairs"] = (V.n_pairs - V.n_pairs_s1).abs()
    V["dlog"] = (V.loghr - V.loghr_s1).abs()
    V.to_csv(out / "verify_vs_s1.csv", index=False)
    # --- results.csv (common layout): primary + S1 balance metrics + NCO per-arm summaries
    Ms = {k: nco_set(N, k) for k in ("main", "strict", "per_arm")}
    PTs = {k: per_trial_metrics(M) for k, M in Ms.items()}
    R = V.drop(columns=["dpairs", "dlog", "n_pairs_s1", "loghr_s1", "se_s1"]).merge(
        PTs["main"], on=["trial", "half", "cell", "arm_role"], how="left")
    # unmatched rows are shared by every rung; copy unmatched NCO metrics
    R.to_csv(out / "results.csv", index=False)
    for k, PT in PTs.items():
        PT.to_csv(out / f"per_trial_nco_metrics_{k}.csv", index=False)
    # --- unmatched in the per-trial table (cell = 'unmatched')
    Cs = {k: contrasts(PT, cells) for k, PT in PTs.items()}
    for k, Cc in Cs.items():
        Cc.to_csv(out / f"contrasts_{k}.csv", index=False)
    SY = {k: pooled_syserr(M) for k, M in Ms.items()}
    SP = pooled_sigma_perm(Ms["main"], cells)
    SP.to_csv(out / "pooled_sigma_perm_main.csv", index=False)
    for k, S in SY.items():
        S.to_csv(out / f"pooled_syserr_{k}.csv", index=False)
    # --- level table (means over trials)
    L = PTs["main"].groupby(["half", "cell", "arm_role"])[METRICS + ["n_nco", "mu", "sigma"]].mean().reset_index()
    L.to_csv(out / "levels_main.csv", index=False)
    # --- inventory (full cohort unmatched events; suppressed)
    inv = N[(N.half == "full") & (N.arm_role == "unmatched")][["trial", "nco", "ev_t", "ev_c", "elig_pooled", "elig_per_arm"]]
    inv.to_csv(out / "inventory.csv", index=False)
    # --- calibration
    Cal = calibrate(P[P.arm_role != "unmatched"], Ms["main"], PTs["main"])
    Cal.to_csv(out / "calibrated_primary.csv", index=False)
    AG = agree_contrasts(Cal, cells)
    AG.to_csv(out / "calibrated_agreement.csv", index=False)
    return V, Ms, PTs, Cs, SY, L, inv, Cal, AG


# ---------------------------------------------------------------- report
ROLE_LAB = {"base": "base", "ECG": "base + ECG (32 PCs)", "shufECG": "base + shuffled ECG", "noise": "base + noise32"}


def _pf(p):
    return "–" if not np.isfinite(p) else (f"{p:.3f}" if p >= 0.001 else "<0.001")


def primary_pairs(V):
    """Primary-outcome contrasts (E.summarize_pairs) on the matched sets used here (common sweep layout)."""
    df = V[V.cell != "unmatched"].rename(columns={"arm_role": "arm"})
    out = []
    for half in ("full", "A", "B"):
        g = df[df.half == half]
        for b in ("base", "shufECG", "noise"):
            s = E.summarize_pairs(g, ["cell"], "ECG", b)
            s["half"] = half
            out.append(s)
        s = E.summarize_pairs(g, ["cell"], "shufECG", "base"); s["half"] = half; out.append(s)
        s = E.summarize_pairs(g, ["cell"], "noise", "base"); s["half"] = half; out.append(s)
    S = pd.concat(out, ignore_index=True)
    for m in ("absd", "z2", "mean_smd", "cstat"):
        sel = (S.half == "full") & (S.arm_a == "ECG") & (S.arm_b == "base")
        S.loc[sel, f"q_{m}"] = E.bh_fdr(S.loc[sel, f"p_{m}"].to_numpy())
    return S


def figs(out, V, Ms, PTs, Cs, SY, L, inv, Cal, AG):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    DOCS.mkdir(parents=True, exist_ok=True)
    cells = [c for c, _ in RUNGS]
    x = np.arange(len(cells))
    col = {"base": "#2a78d6", "ECG": "#eb6834", "shufECG": "#8a8985", "noise": "#b9b8b1"}
    mk = {"base": "o", "ECG": "s", "shufECG": "^", "noise": "v"}
    off = {"base": -0.15, "ECG": -0.05, "shufECG": 0.05, "noise": 0.15}
    PT = PTs["main"]
    C = Cs["main"]
    F = PT[PT.half == "full"]
    SYf = SY["main"][SY["main"].half == "full"].set_index(["cell", "arm_role"])
    panels = [("abs_b", "mean |log HR| across NCOs (truth 0)"), ("b2x", "mean (log HR² − se²) ≈ systematic error²"),
              ("sigma", "pooled systematic-error SD σ (OHDSI)\np: within-trial arm-swap permutation")]
    fig, axs = plt.subplots(1, 3, figsize=(16, 5.6))
    for ax, (m, title) in zip(axs, panels):
        for role in ROLES:
            if m == "sigma":
                y = [SYf.loc[(c, role), "sigma"] for c in cells]
                lo = hi = None
            else:
                g = F[F.arm_role == role].groupby("cell")[m]
                y = [g.mean()[c] for c in cells]
                se = [g.std()[c] / np.sqrt(g.count()[c]) for c in cells]
            ax.plot(x + off[role], y, marker=mk[role], color=col[role], lw=2 if role in ("base", "ECG") else 1.2, ms=8,
                    label=ROLE_LAB[role], zorder=3 if role in ("base", "ECG") else 2)
            if m != "sigma":
                ax.errorbar(x + off[role], y, yerr=se, fmt="none", ecolor=col[role], lw=1, alpha=0.7)
        if m == "sigma":
            u = SYf.loc[("unmatched", "unmatched"), "sigma"]
        else:
            u = F[F.arm_role == "unmatched"][m].mean()
        ax.axhline(u, color="#52514e", ls=":", lw=1)
        ax.text(len(cells) - 0.6, u, "unmatched", color="#52514e", fontsize=8, va="bottom", ha="right")
        if m != "sigma":
            yl = ax.get_ylim()
            ax.set_ylim(yl[0], yl[1] + 0.12 * (yl[1] - yl[0]))
            for xi, c in zip(x, cells):
                r = C[(C.half == "full") & (C.cell == c) & (C.a == "ECG") & (C.b == "base") & (C.metric == m)].iloc[0]
                txt = f"Δ {r.d:+.3f}\np={_pf(r.p)}\nclust p={_pf(r.p_cluster)}"
                ax.text(xi, yl[1] + 0.01 * (yl[1] - yl[0]), txt, ha="center", va="bottom", fontsize=7,
                        color="#0b0b0b" if r.p < 0.05 else "#6b6a66", fontweight="bold" if (r.p < 0.05 and r.d < 0) else "normal")
        else:
            SPf = pd.read_csv(out / "pooled_sigma_perm_main.csv")
            SPf = SPf[(SPf.half == "full") & (SPf.a == "ECG")]
            yl = ax.get_ylim()
            ax.set_ylim(yl[0], yl[1] + 0.12 * (yl[1] - yl[0]))
            for xi, c in zip(x, cells):
                r = SPf[(SPf.cell == c) & (SPf.b == "base")].iloc[0]
                rs_ = SPf[(SPf.cell == c) & (SPf.b == "shufECG")].iloc[0]
                txt = f"Δ {r.d_sigma:+.3f}\np={_pf(r.p_sigma)}\nvs shuf p={_pf(rs_.p_sigma)}"
                ax.text(xi, yl[1] + 0.01 * (yl[1] - yl[0]), txt, ha="center", va="bottom", fontsize=7,
                        color="#0b0b0b" if r.p_sigma < 0.05 else "#6b6a66",
                        fontweight="bold" if (r.p_sigma < 0.05 and r.d_sigma < 0) else "normal")
        ax.set_xticks(x)
        ax.set_xticklabels([RUNG_LAB[c] for c in cells], fontsize=9)
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", color="#e6e5e0", lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    h, lb = axs[0].get_legend_handles_labels()
    fig.legend(h, lb, loc="lower center", ncol=4, fontsize=9, frameon=False)
    fig.suptitle("S5 negative-control outcomes: 18 trials, full cohort, 1:1 caliper-0.2 matching (mean ± SE over trials). "
                 "Text: ECG − base, exact sign-flip p over trials and over 10 comparator clusters", fontsize=10)
    fig.tight_layout(rect=(0, 0.06, 1, 0.97))
    fig.savefig(DOCS / "S5_NCO_fig.png", dpi=140)
    plt.close(fig)
    # heat map: d and p (ECG - comparator) for NCO metrics + primary metrics
    S = primary_pairs(V)
    comps = [("full", "base"), ("full", "shufECG"), ("full", "noise"), ("A", "base"), ("B", "base")]
    mets = [("nco", m) for m in ("abs_b", "z2", "frac_sig", "b2x")] + [("prim", m) for m in ("absd", "z2", "mean_smd", "cstat")]
    fig, axs = plt.subplots(1, len(mets), figsize=(24, 5.2), sharey=True)
    for ax, (src, m) in zip(axs, mets):
        M = np.full((len(cells), len(comps)), np.nan)
        P = np.full_like(M, np.nan)
        for j, (h, b) in enumerate(comps):
            for i, c in enumerate(cells):
                if src == "nco":
                    r = C[(C.half == h) & (C.cell == c) & (C.a == "ECG") & (C.b == b) & (C.metric == m)].iloc[0]
                    M[i, j], P[i, j] = r.d, r.p
                else:
                    r = S[(S.half == h) & (S.cell == c) & (S.arm_a == "ECG") & (S.arm_b == b)].iloc[0]
                    M[i, j], P[i, j] = r[f"d_{m}"], r[f"p_{m}"]
        v = np.nanmax(np.abs(M))
        im = ax.imshow(M, cmap="RdBu_r", vmin=-v, vmax=v, aspect="auto")
        for i in range(len(cells)):
            for j in range(len(comps)):
                ax.text(j, i, f"{M[i, j]:+.3f}\np={P[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if abs(M[i, j]) > 0.6 * v else "black", fontweight="bold" if P[i, j] < 0.05 else "normal")
        ax.set_xticks(range(len(comps)))
        ax.set_xticklabels([f"{b}\n{h}" for h, b in comps], fontsize=7)
        ax.set_title(("NCO " if src == "nco" else "primary ") + f"{m}\n(ECG − comparator; blue = ECG better)", fontsize=9)
        fig.colorbar(im, ax=ax, shrink=0.6)
    axs[0].set_yticks(range(len(cells)))
    axs[0].set_yticklabels([RUNG_LAB[c] for c in cells], fontsize=8)
    fig.tight_layout()
    fig.savefig(DOCS / "S5_NCO_heatmap.png", dpi=130)
    plt.close(fig)
    S.to_csv(out / "summary_primary_pairs.csv", index=False)


KEY_FINDINGS = """**Short answer: no robust evidence. Adding the ECG does not reliably move negative-control HRs toward the null.** The direction mostly favours ECG. The only nominally significant signals are at the *clinical* rung (and for the pooled σ at sparse). None of them passes all of these: placebo-specific in test (not just in direction), FDR, comparator clustering, and both split halves.

1. **NCO systematic error is small and noise dominates.** Setup: 18 trials, median 26 eligible NCOs per trial (range 13–35; out of 37 candidates, after pharmacological exclusions and the ≥ 30-event rule). Unmatched: mean |log HR_NCO| = 0.221, but mean (b² − se²) is only 0.028 and the pooled OHDSI σ = 0.139. Any PS matching cuts σ to 0.05–0.10 (hdPS200 lowest, 0.053). Mean |log HR| gets *larger*, though (0.23–0.26), because the matched samples are smaller. So per-trial NCO metrics have low power, and differences of ~0.01 in log HR are within noise.
2. **Thin bases (demo, minimal-7), where ECG gives the largest held-out balance gains (S1): no NCO gain.** ECG − base mean |log HR_NCO| −0.009 (10/18, p = 0.21) and −0.010 (p = 0.28). The same holds for b² − se² (p = 0.19 and 0.34), fixed-SE z² (p = 0.68 and 0.35) and pooled σ (−0.008, p = 0.33; +0.002, p = 0.83). One exception: demo "fraction of CIs excluding 1" is −0.024 (p = 0.026, cluster p = 0.031), but q = 0.12 and both halves go the wrong way (+0.006, −0.004).
3. **Sparse: only the pooled σ moves.** Pooled σ 0.091 → 0.074 (−0.017, arm-swap permutation p = 0.034). It beats shufECG (p = 0.008), but noise only marginally (p = 0.064), and it is not significant in either half (A p = 0.89, B p = 0.48). Per-trial metrics are null: |log HR| p = 0.49, z² −0.149 (p = 0.056), fixed-SE z² p = 0.13. In the strict NCO set, z² −0.205 (p = 0.018, q = 0.045) is placebo-specific (ECG − shufECG p = 0.007), but cluster p = 0.18 and the halves disagree (A +0.086, B −0.034).
4. **hdPS200: null.** No NCO metric reaches p < 0.05; the closest is EASE +0.014 (p = 0.067), with ECG worse. Shuffled ECG and noise are *worse* than base here (for example shufECG EASE +0.022, p = 0.005).
5. **Clinical: the strongest, but not ECG-specific in test and not replicated.**
   - Mean |log HR_NCO| 0.246 → 0.225 (−0.022, 12/18, p = 0.044, cluster p = 0.029, q = 0.22).
   - z² −0.160 (14/18, p = 0.007, q = 0.036, cluster p = 0.041). But shufECG also lowers z² (−0.097, p = 0.026), and ECG − shufECG gives p = 0.31. The fixed-SE z² is −0.143 (p = 0.028, q = 0.14).
   - Pooled σ 0.082 → 0.065 (p = 0.004), yet ECG − shufECG p = 0.20 and ECG − noise p = 0.09.
   - Halves: every clinical metric has p ≥ 0.18 in each half.
   - Strict set (caution NCOs dropped): the gain is larger (|log HR| −0.029, p = 0.009, q = 0.047, cluster p = 0.014; b² − se² −0.024, p = 0.021). In the ≥ 20-events-per-arm set it weakens (|log HR| p = 0.10).
   - Read this as suggestive only.
6. **Placebo guardrail.** Across 60 placebo − base tests, 2 are better and 7 worse at p < 0.05 (about 1.5 of each expected). ECG − base is better at p < 0.05 in 7/30 tests and worse in 0/30. BH within metric over the 5 rungs leaves only clinical z² in the main set (q = 0.036). Over the whole family (5 rungs × 6 metrics, column q_bh_family) nothing in the main set survives (smallest q = 0.20). In the strict set, clinical z², fixed-SE z² and fraction of CIs excluding 1 survive (family q 0.036–0.039), and in the ≥ 20-per-arm set nothing does.
7. **NCO-calibrated primary estimates: ECG does not help any more (or less) after calibration.** Calibration mostly widens CIs, because the fitted systematic-error means are near 0 (pooled |μ| ≤ 0.024).
   - Pooled leave-one-trial-out calibration keeps the pre-calibration picture: demo |Δlog HR| vs RCT −0.058 (p = 0.030; shuffled-benchmark p = 0.038), and z² −1.56 (p = 0.024) is *not* benchmark-specific (shuffled p = 0.42). Minimal-7 is borderline (|Δ| −0.039, p = 0.056; z² −1.67, p = 0.042, shuffled p = 0.54). Sparse, hdPS200 and clinical are null.
   - With each trial's own NCO fit, demo |Δ| is −0.091 (p = 0.009, shuffled p = 0.032), but both halves are null (A p = 0.76, B p = 0.27).
   - At clinical, own-NCO calibration makes ECG look worse on z² (+0.67, p = 0.028), because its smaller σ widens CIs less.
8. **Bottom line.** Negative controls give no placebo-specific, replicated evidence that the AI-ECG reduces residual confounding at any PS set point. The held-out-balance gains at thin bases (S1) do not show up as less NCO bias. The only hints are at the richest (clinical) PS and in the sparse σ. They are consistent with a small confounding reduction below this design's detection limit, not with a demonstrated one.
"""


def write_md(out, V, Ms, PTs, Cs, SY, L, inv, Cal, AG):
    from v13_summarize import md
    cells = [c for c, _ in RUNGS]
    S = pd.read_csv(out / "summary_primary_pairs.csv")
    PT, C = PTs["main"], Cs["main"]
    L_ = []
    # ---- inventory
    ninc = {k: M[(M.half == "full") & (M.cell == "unmatched")].groupby("trial").nco.nunique() for k, M in Ms.items()}
    hard = {n: excl(n, "hard") for n in E.TRIALS}
    caut = {n: excl(n, "caution") for n in E.TRIALS}
    I = pd.DataFrame({"trial": E.TRIALS, "drug classes": [" vs ".join(CLASSES[n]) if len(CLASSES[n]) > 1 else CLASSES[n][0] + " (both)" for n in E.TRIALS],
                      "NCOs main": [int(ninc["main"].get(n, 0)) for n in E.TRIALS],
                      "NCOs strict": [int(ninc["strict"].get(n, 0)) for n in E.TRIALS],
                      "NCOs ≥20/arm": [int(ninc["per_arm"].get(n, 0)) for n in E.TRIALS],
                      "hard exclusions": [", ".join(k.replace("nco_", "") for k in hard[n]) or "–" for n in E.TRIALS],
                      "cautions (strict set drops)": [", ".join(k.replace("nco_", "") for k in caut[n]) or "–" for n in E.TRIALS]})
    ev = inv.copy()
    fmt = lambda a, b: ("<11" if not np.isfinite(a) else f"{int(a)}") + "/" + ("<11" if not np.isfinite(b) else f"{int(b)}")
    ev["cell"] = [fmt(a, b) + ("" if el else "*") for a, b, el in zip(ev.ev_t, ev.ev_c, ev.elig_pooled)]
    EV = ev.pivot(index="nco", columns="trial", values="cell").reindex(columns=E.TRIALS).reindex(NCOS).fillna("–")
    EV.index = [i.replace("nco_", "") for i in EV.index]
    EV = EV.reset_index().rename(columns={"index": "NCO"})
    # ---- levels
    F = PT[PT.half == "full"]
    lv = []
    for c in ["unmatched"] + cells:
        for role in (["unmatched"] if c == "unmatched" else ROLES):
            g = F[(F.cell == c) & (F.arm_role == role)]
            sy = SY["main"][(SY["main"].half == "full") & (SY["main"].cell == c) & (SY["main"].arm_role == role)].iloc[0]
            lv.append(dict(rung=RUNG_LAB.get(c, c), arm=role, trials=len(g), mean_NCOs=g.n_nco.mean(), mean_abs_logHR=g.abs_b.mean(),
                           mean_z2=g.z2.mean(), pct_CI_excl_1=100 * g.frac_sig.mean(), mean_b2_minus_se2=g.b2x.mean(),
                           pooled_mu=sy.mu, pooled_sigma=sy.sigma, pooled_EASE=sy.ease))
    LV = pd.DataFrame(lv)

    # ---- contrast table
    def ctab(Cc, metrics):
        rows = []
        for c in cells:
            for m in metrics:
                g = Cc[(Cc.cell == c) & (Cc.metric == m)]
                r = g[(g.half == "full") & (g.a == "ECG") & (g.b == "base")].iloc[0]
                gp = lambda a, b, h="full": g[(g.half == h) & (g.a == a) & (g.b == b)].iloc[0]
                rs, rn = gp("ECG", "shufECG"), gp("ECG", "noise")
                sb, nb = gp("shufECG", "base"), gp("noise", "base")
                ra, rb_ = gp("ECG", "base", "A"), gp("ECG", "base", "B")
                spec = (r.p < 0.05) and (r.d < 0) and (rs.d < 0) and (rn.d < 0)
                rows.append({"rung": RUNG_LAB[c], "metric": METLAB[m], "ECG−base d": r.d, "k": r.k, "p": _pf(r.p), "q (BH, metric)": _pf(r.q_bh),
                             "cluster p (k)": f"{_pf(r.p_cluster)} ({r.k_cluster})", "LOO p range": f"{_pf(r.p_loo_min)}–{_pf(r.p_loo_max)}",
                             "shuf−base d (p)": f"{sb.d:+.3f} ({_pf(sb.p)})", "noise−base d (p)": f"{nb.d:+.3f} ({_pf(nb.p)})",
                             "ECG−shuf p": _pf(rs.p), "ECG−noise p": _pf(rn.p), "half A d (p)": f"{ra.d:+.3f} ({_pf(ra.p)})",
                             "half B d (p)": f"{rb_.d:+.3f} ({_pf(rb_.p)})",
                             "ECG-specific": "yes" if spec else "no"})
        return pd.DataFrame(rows)

    CT = ctab(C, METRICS)
    CTs = ctab(Cs["strict"], ["abs_b", "z2", "z2_fixse", "b2x"])
    CTp = ctab(Cs["per_arm"], ["abs_b", "z2", "z2_fixse", "b2x"])
    # base vs unmatched
    BU = C[(C.half == "full") & (C.a == "base") & (C.b == "unmatched") & (C.metric.isin(["abs_b", "b2x"]))][["cell", "metric", "d", "k", "p"]].copy()
    BU["cell"] = BU.cell.map(RUNG_LAB)
    # ---- pooled systematic error by half
    SYt = SY["main"].copy()
    SYt = SYt[SYt.cell != "unmatched"].pivot_table(index=["cell", "arm_role"], columns="half", values=["sigma", "mu", "ease"]).reset_index()
    SYt.columns = [" ".join(c).strip() for c in SYt.columns]
    SYt["cell"] = SYt.cell.map(RUNG_LAB)
    # ---- primary (common layout)
    pr = []
    for c in cells:
        for m in ("absd", "z2", "mean_smd", "cstat"):
            g = S[S.cell == c]
            r = g[(g.half == "full") & (g.arm_a == "ECG") & (g.arm_b == "base")].iloc[0]
            f = lambda a, b, h="full": g[(g.half == h) & (g.arm_a == a) & (g.arm_b == b)].iloc[0]
            pr.append({"rung": RUNG_LAB[c], "metric": m, "ECG−base d": r[f"d_{m}"], "k": r[f"k_{m}"], "p": _pf(r[f"p_{m}"]),
                       "q": _pf(r[f"q_{m}"]), "ECG−shuf d (p)": f"{f('ECG', 'shufECG')[f'd_{m}']:+.3f} ({_pf(f('ECG', 'shufECG')[f'p_{m}'])})",
                       "ECG−noise d (p)": f"{f('ECG', 'noise')[f'd_{m}']:+.3f} ({_pf(f('ECG', 'noise')[f'p_{m}'])})",
                       "half A p": _pf(f("ECG", "base", "A")[f"p_{m}"]), "half B p": _pf(f("ECG", "base", "B")[f"p_{m}"]),
                       "cons % base→ECG": f"{r.cons_b:.0f}→{r.cons_a:.0f}", "phi base→ECG": f"{r.phi_b:.2f}→{r.phi_a:.2f}"})
    PR = pd.DataFrame(pr)
    # ---- calibration
    ag = AG[(AG.half == "full") & (AG.a == "ECG") & (AG.b == "base")]
    cal_rows = []
    for c in cells:
        for m in ("absd", "z2"):
            rr = {"rung": RUNG_LAB[c], "metric": m}
            for lab, sel in (("raw", (ag.est == "raw") & (ag.calib == "own")), ("calibrated (own NCOs)", (ag.est == "cal") & (ag.calib == "own")),
                             ("calibrated (pooled LOO)", (ag.est == "cal") & (ag.calib == "pooled_loo"))):
                r = ag[sel & (ag.cell == c) & (ag.metric == m)].iloc[0]
                rr[f"{lab}: base→ECG"] = f"{r.mean_b:.3f}→{r.mean_a:.3f}"
                rr[f"{lab}: d, k, p"] = f"{r.d:+.3f}, {r.k}, {_pf(r.p)}"
                rr[f"{lab}: shuffled-RCT null median (p)"] = f"{r.shuf_null_median:+.3f} ({_pf(r.p_shuf)})"
            cal_rows.append(rr)
    CA = pd.DataFrame(cal_rows)
    agp = AG[(AG.half == "full") & (AG.est == "cal") & (AG.calib == "own") & (AG.b == "base") & (AG.a != "ECG")]
    agp = agp[["cell", "a", "metric", "d", "k", "p"]].copy()
    agp["cell"] = agp.cell.map(RUNG_LAB)
    agh = AG[(AG.half != "full") & (AG.est == "cal") & (AG.calib == "own") & (AG.a == "ECG") & (AG.b == "base")]
    agh = agh[["half", "cell", "metric", "d", "k", "p"]].copy()
    agh["cell"] = agh.cell.map(RUNG_LAB)
    SPt = pd.read_csv(out / "pooled_sigma_perm_main.csv")
    SPt["cell"] = SPt.cell.map(RUNG_LAB)
    src = Cal[(Cal.half == "full") & (Cal.calib == "own")].groupby("source").size()
    audit_f = out / "audit.md"
    audit = audit_f.read_text() if audit_f.exists() else "(audit section not found)"
    L_ += ["# S5 — negative-control outcomes across PS set points (v1.6 exploratory sweep)\n",
           "Script `scripts/v16/s5_nco.py` (NCO extraction `scripts/v16/s5_nco_extract.py`); aggregates in "
           "`/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s5-nco/`. Exploratory and post hoc (docs/V16_SWEEP_PLAN.md guardrails). "
           "Aggregates only; event counts 1–10 shown as <11.\n",
           "## Key findings (plain language)\n", KEY_FINDINGS, "\n",
           "![S5 NCO figure](S5_NCO_fig.png)\n",
           "## Design\n",
           "- **Why NCOs.** A negative-control outcome has a known truth (HR = 1, log HR = 0) for the drug contrast, so any non-zero "
           "NCO HR after adjustment is systematic error (residual confounding, detection or selection bias). Unlike RCT agreement "
           "(AUDIT_V16 check 11, where ECG gains were mostly generic shrinkage toward the null), moving NCO HRs toward 0 *is* the correct "
           "direction, so it directly tests confounding reduction.",
           "- **NCOs.** 25 v1.3 NCOs (`trial_specs.NCO_EXT`: 3 frozen protocol-v1 NCOs + 22 from amendment I8) plus 12 new v1.6 NCOs "
           "extracted with identical conventions (`s5_nco_extract.py`; re-extraction of C44 and K02 reproduces the v1.3 file exactly in "
           "all 18 trials): " + ", ".join(f"{k.replace('nco_', '')} ({'/'.join(v)})" for k, v in NEW_NCO.items()) + ".",
           "- **Outcome conventions (same as v1.3 / primary).** First diagnosis (or procedure) strictly after index; patients with the code in "
           "the 365 d before or on index are removed for that NCO; death censors; follow-up from index capped at the trial horizon "
           "(same as the primary outcome); primary-outcome exclusions (exclude_phase2, missing primary time) applied.",
           f"- **Eligibility** (fixed on the full unmatched cohort, before matching): pooled events ≥ {MIN_POOLED} at the horizon and no "
           f"pharmacological exclusion (main set). Sensitivity sets: *strict* (also drops caution NCOs) and *≥ {MIN_ARM} events per arm*. "
           "Within a trial × half, only NCOs estimable in all 21 arms are used, so every arm is compared on the same NCOs.",
           "- **Arms.** Rungs demo, minimal-7, sparse, hdPS200, clinical (S1 definitions, `s1_ladder.base_designs`), each as base, "
           "+ECG (32 BCL PCs), +shufECG (same PCs, rows permuted with `T.shuffle_perm`), +noise32 (`T.noise32`); plus unmatched. "
           "Matched sets replicate `E.run_cell` (L2 C=1 PS, 1:1 greedy caliper 0.2). The primary Cox reproduced S1's run_cell output "
           "exactly (see Audit).",
           "- **NCO estimation.** Cox (lifelines, Efron) on the matched set with pair-clustered robust SE, exactly as v13_design.",
           "- **Metrics per trial × rung × arm** (over that trial's NCOs): mean |log HR|; mean z² = b²/se²; fraction of 95% CIs excluding 1; "
           "mean (b² − se²) (a noise-corrected estimate of mean squared systematic error); per-trial OHDSI systematic-error fit "
           "b ~ N(μ, σ² + se²) and its EASE = E|N(μ, σ²)|. Pooled across trials: μ, σ, EASE from all trial-NCO estimates.",
           "- **Inference.** Exact sign-flip over 18 trials on per-trial (ECG − base), (ECG − shufECG), (ECG − noise); clustered sign-flip over "
           "10 comparator clusters (`audit_v16.CLUSTER`); leave-one-trial-out; halves A/B (seeded split, 16060 + trial index, eligibility "
           "from the full cohort). BH-FDR within metric over the 5 rungs (ECG vs base, full) and over all 25 rung × metric tests "
           "(column q_bh_family in the CSV). ECG-specific = ECG vs base p < 0.05, ECG better, and ECG better than both placebos in direction.",
           "- **Calibration.** Each primary log HR is empirically calibrated with its own arm's NCO systematic-error fit "
           "(b* = b − μ, se* = √(se² + σ²); trial-specific fit if ≥ 8 NCOs else pooled over the other trials, same rung/arm/half) and, as a "
           "variant, always with the leave-this-trial-out pooled fit. Agreement with the RCT (|Δlog HR|, z²) is re-evaluated, with the "
           "shuffled-benchmark null of AUDIT_V16 check 11 (RCT HRs permuted across trials, 2000 draws; p = P(null ≤ observed)).\n",
           "### NCO inventory per trial\n", md(I, 0) + "\n",
           "Exclusion rationale (hard): " + "; ".join(f"**{c}** – " + ", ".join(f"{k.replace('nco_', '')} ({v})" for k, v in d.items())
                                                        for c, d in EXCL_CLASS.items()) + ".\n",
           "Cautions (kept in main, dropped in strict): " + "; ".join(f"**{c}** – " + ", ".join(f"{k.replace('nco_', '')} ({v})" for k, v in d.items())
                                                                      for c, d in CAUTION_CLASS.items()) + ".\n",
           "Not used anywhere (not in the candidate list by design): bleeding and bleeding-adjacent outcomes (anticoagulant/antiplatelet trials), "
           "gout, angioedema/cough, hypoglycaemia, genital infection/UTI, ketoacidosis, fractures/falls/syncope/sprains, hyperkalaemia, oedema.\n",
           "Classes: BB beta-blocker, ARNI sacubitril/valsartan, ACEi, ARB, LOOP loop diuretic, P2Y12 inhibitor, OAC (DOAC vs warfarin), "
           "CCB amlodipine, THZ thiazide, SGLT2i, DPP4i, SU sulfonylurea, AAD antiarrhythmic (incl. amiodarone), ABL catheter ablation.\n",
           "### NCO events at the horizon, full unmatched cohort (treated/comparator; – = pharmacologically excluded or pooled events < 30 in that trial, not estimated)\n",
           md(EV, 0) + "\n",
           "## Results\n",
           "### Levels (full cohort; mean over trials; pooled = OHDSI fit over all trial-NCO estimates)\n", md(LV, 3) + "\n",
           "### ECG vs base and placebos on NCO metrics (main NCO set)\n", md(CT, 3) + "\n",
           "### Sensitivity: strict NCO set (cautions dropped)\n", md(CTs, 3) + "\n",
           "### Sensitivity: NCOs with ≥ 20 events per arm\n", md(CTp, 3) + "\n",
           "### Base (no ECG) vs unmatched on NCO metrics\n", md(BU, 3) + "\n",
           "### Pooled systematic-error distribution by rung, arm and half\n", md(SYt, 3) + "\n",
           "Pooled σ and EASE contrasts (arm a − arm b); p from randomly swapping the two arms' NCO sets within trials (500 draws):\n",
           md(SPt, 3) + "\n",
           "### Primary outcome on the same matched sets (common sweep layout; balance metrics from S1 run_cell)\n", md(PR, 3) + "\n",
           "### NCO-calibrated primary estimates: agreement with the RCT, ECG vs base (full cohort)\n",
           f"Calibration source counts (own variant, full): {src.to_dict()}.\n", md(CA, 3) + "\n",
           "Placebo arms after calibration (vs base):\n", md(agp, 3) + "\n",
           "Halves after calibration (ECG vs base):\n", md(agh, 3) + "\n",
           "![S5 heat map](S5_NCO_heatmap.png)\n",
           "## Audit\n", audit]
    (DOCS / "S5_NCO.md").write_text("\n".join(L_) + "\n")

# ---------------------------------------------------------------- audit
def audit(out):
    """Pre-/post-run checks written to OUT/audit.md (included in the markdown)."""
    import json
    from v13_summarize import md
    L_ = []
    # A1 extraction
    val = [json.load(open(XOUT / f"summary_{n}.json"))["validation_identical_to_v13"] for n in E.TRIALS]
    ok1 = sum(all(v.values()) for v in val)
    L_.append(f"1. **New-NCO extraction reproduces v1.3 conventions.** Re-extracting nco_skin_cancer (C44) and nco_dental_caries (K02) "
              f"with `s5_nco_extract.py` gives times and event indicators identical to `restricted_outcomes_v13.parquet` in {ok1}/18 trials.")
    # A2 matched-set replication vs S1 run_cell
    V = pd.read_csv(out / "verify_vs_s1.csv")
    L_.append(f"2. **Matched sets = run_cell's.** All {len(V)} primary rows (18 trials × 3 halves × 21 arms) found in S1 results: "
              f"{int(V.loghr_s1.notna().sum())}; max |Δ pairs| = {V.dpairs.max():.0f}; max |Δ log HR| = {V.dlog.max():.2e}.")
    # A3 engine validation, sparse / sparse+ECG
    ev = pd.read_csv(E.OUT / "validation_estimates.csv")
    P = pd.read_csv(out / "primary_raw.csv")
    P = P[P.half == "full"]
    rows = []
    for arm, (c, r) in {"unmatched": ("unmatched", "unmatched"), "sparse": ("r5_sparse", "base"), "sparse+ECG": ("r5_sparse", "ECG"),
                        "hdPS200": ("r7_hdPS200", "base"), "clinical (reference)": ("r8_clinical", "base")}.items():
        a = ev[ev.arm == arm].set_index("trial")
        b = P[(P.cell == c) & (P.arm_role == r)].set_index("trial")
        tt = a.index.intersection(b.index)
        rows.append(dict(arm=arm, trials=len(tt), max_abs_dloghr=float((a.loc[tt].loghr - b.loc[tt].loghr).abs().max()),
                         max_abs_dpairs=float((a.loc[tt].n_pairs - b.loc[tt].n_pairs).abs().max()) if arm != "unmatched" else np.nan))
    L_.append("3. **Engine validation reproduced** (ENGINE_VALIDATION estimates vs this sweep, full cohort):\n\n" + md(pd.DataFrame(rows), 6) + "\n")
    # A4 NCO estimates vs v13_design (imputation 1, saved phase-2 matches)
    N = pd.read_csv(out / "nco_estimates.csv")
    rows = []
    for n in E.TRIALS:
        f = A / "claude-v13-design" / f"design_{n}_perimp.csv"
        if not f.exists():
            continue
        D = pd.read_csv(f)
        D = D[(D.imputation == 1) & D.analysis.str.startswith("nco_")]
        for arm, (c, r) in {"unmatched": ("unmatched", "unmatched"), "sparse": ("r5_sparse", "base"), "sparse+ECG": ("r5_sparse", "ECG"),
                            "hdPS200": ("r7_hdPS200", "base"), "hdPS200+ECG": ("r7_hdPS200", "ECG"),
                            "clinical (reference)": ("r8_clinical", "base")}.items():
            a = D[D.arm == arm].set_index("analysis").loghr
            b = N[(N.trial == n) & (N.half == "full") & (N.cell == c) & (N.arm_role == r)].set_index("nco").loghr
            tt = a.index.intersection(b.index)
            d = (a[tt] - b[tt]).abs()
            rows.append(dict(trial=n, arm=arm, n_nco=len(tt), maxd=float(d.max()) if len(d) else np.nan))
    R = pd.DataFrame(rows)
    g = R.groupby("arm").agg(trials=("trial", "nunique"), nco_pairs=("n_nco", "sum"), max_abs_dloghr=("maxd", "max")).reset_index()
    L_.append("4. **NCO Cox reproduces v13_design** (imputation 1, saved phase-2 matched sets; v1.3 NCOs only) — max |Δ log HR_NCO| "
              "(ECG arms: v13 `sparse+ECG`/`hdPS200+ECG` use the same 32 PCs):\n\n" + md(g, 6) + "\n")
    # A5 placebo sanity
    C = pd.read_csv(out / "contrasts_main.csv")
    pl = C[(C.half == "full") & (C.b == "base") & C.a.isin(["shufECG", "noise"]) & (C.metric != "lse")]
    ec = C[(C.half == "full") & (C.b == "base") & (C.a == "ECG") & (C.metric != "lse")]
    L_.append(f"5. **Placebo null.** Placebo − base over {len(pl)} rung × metric tests (main set, full): mean d by metric "
              + ", ".join(f"{m} {pl[pl.metric == m].d.mean():+.4f}" for m in METRICS if m != "lse")
              + f"; p < 0.05 with placebo better in {int(((pl.p < 0.05) & (pl.d < 0)).sum())}, worse in {int(((pl.p < 0.05) & (pl.d > 0)).sum())} "
              f"(≈{0.025 * len(pl):.1f} each expected by chance). ECG − base: better at p < 0.05 in {int(((ec.p < 0.05) & (ec.d < 0)).sum())}/{len(ec)}, "
              f"worse in {int(((ec.p < 0.05) & (ec.d > 0)).sum())}. So the NCO metrics have a placebo false-positive rate close to nominal, "
              "and ECG's hit rate is only modestly above it.")
    # A6 precision
    PT = pd.read_csv(out / "per_trial_nco_metrics_main.csv")
    f = PT[(PT.half == "full") & (PT.arm_role != "unmatched")].groupby(["cell", "arm_role"]).lse.mean().unstack()
    f.index = f.index.map(RUNG_LAB)
    L_.append("6. **Precision / pair-count route.** Mean log(se_NCO / se_NCO,base) by rung (positive = wider CIs than base). Wider CIs "
              "mechanically lower z² and the fraction of CIs excluding 1, so `z2_fixse` (each arm's b² over the base arm's se²) and "
              "b² − se² are the precision-robust metrics:\n\n" + md(f.reset_index().rename(columns={"cell": "rung"}), 4) + "\n")
    # A7 small cells in matched sets
    Nm = N[N.half == "full"]
    Mm = nco_set(N, "main")
    Mm = Mm[Mm.half == "full"]
    small = (Mm.ev_t.isna() | Mm.ev_c.isna()).mean()
    L_.append(f"7. **Sparse NCO cells.** Main set, full cohort: {Mm.groupby('trial').nco.nunique().median():.0f} NCOs per trial "
              f"(median; range {Mm.groupby('trial').nco.nunique().min()}–{Mm.groupby('trial').nco.nunique().max()}); "
              f"{100 * small:.1f}% of arm-level NCO estimates have < 11 events in one matched arm (kept; they are noisy but unbiased "
              "for the null; the ≥ 20-per-arm sensitivity set removes most).")
    L_.append("8. **Eligibility is outcome-blind to arm contrasts.** Eligibility uses only pooled event counts in the full unmatched cohort "
              "(no HR), is fixed before matching and is shared by all arms and halves; hard exclusions were written from pharmacology "
              "before any NCO HR was computed (the plausibility table is in the script header).")
    L_.append("9. **Privacy.** All written event counts pass through the 1–10 suppression (`<11`); markdown tables contain trial-level aggregates, "
              "counts ≥ 11 or `<11`, and no identifiers. Restricted parquet outputs stay in the audits dir (umask 077).")
    (out / "audit.md").write_text("\n".join(L_) + "\n")
    print("\n".join(L_))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["run", "summarize", "audit"])
    ap.add_argument("--trials", default=",".join(E.TRIALS))
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    os.umask(0o077)
    if a.mode == "run":
        run(a.trials.split(","), a.workers, out)
    elif a.mode == "audit":
        audit(out)
    else:
        res = summarize(out)
        figs(out, *res)
        write_md(out, *res)


if __name__ == "__main__":
    main()
