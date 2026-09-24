"""Long-tail balance, generic over trials (v2, 2026-09-23).

Question: does adding unstructured representations to a PS improve balance on
pre-treatment characteristics that the PS does not include?

Inputs (any trial; COMET via scripts/export_comet_baseline.py):
  --baseline-dir  restricted_completed_XX.parquet (patient_key, treated, covariates),
                  restricted_baseline_observed.parquet (NaN = unobserved), roles.json
                  (core / demo / claims / heldout_physiology / report_covariates)
  --panel         pre-index panel (build_preindex_panel.py; v1 binary or v2 counts)
  ECG BCL embeddings, ECG phenotype scores, CLMBR embeddings (patient_key + embedding)
  --prognostic-scores (optional) patient_key + prog_core / prog_full (fit_prognostic_score.py)

Design (unchanged from v1): panel features are split per domain (seeded) into pool A
(hdPS may select from it) and pool B (evaluation only; never in any PS). ECG = 5
phenotype scores + 32 centred PCs; CLMBR = 64 centred PCs; noise placebo has the same
dimension as ECG+CLMBR. 1:1 greedy nearest-neighbour matching without replacement on
the PS logit, caliper 0.2 pooled SD, anchored on the smaller arm.

hdPS (v2): exposure-only. Candidate codes are pool-A dx/rx/px features. With count
panels (v2) every code gives up to three binary levels (Schneeweiss 2009): once
(>= 1 day), sporadic (>= median count among users), frequent (>= 75th percentile);
identical levels are dropped. Pool-A lab-measured flags are added as single-level
candidates. Levels are ranked by |log prevalence ratio| between
arms (+1e-3 smoothing) and the top k enter the PS (k = --hdps-k). "hdPS100bin" is
the v1 comparator (any-use levels only), kept for continuity.

Exposure-defining panel features (roles.json 'exposure_features': rx_<arm keyword>) are
removed from hdPS candidates, pool B and the C-statistic (v2 change; v1 kept them).

Diagnostics per method:
  pool-B / pool-A share of features with |SMD| > 0.1, mean and p95 |SMD| (code
  features evaluated as any-use indicators; lab values on observed values);
  core covariates max |SMD| and count > 0.1; SMD of report covariates on completed
  and on observed-only values; SMD of external prognostic scores (linear predictor,
  pre-match pooled SD); post-matching C-statistic of treatment (5-fold CV AUC of an
  L2 logistic model in the matched sample) on (a) core covariates and (b) core +
  pool-B features. 0.5 = arms indistinguishable. Franklin et al. (2014) found the
  post-matching C-statistic of the PS model itself uninformative; here it is fitted on
  covariates, including ones never in the PS.
Aggregate output only.
"""
import argparse
import glob
import json
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler


def smd_vector(v: np.ndarray, t: np.ndarray, mt: np.ndarray, mc: np.ndarray) -> np.ndarray:
    """|SMD| per column. Means use non-missing values; SD = pre-match pooled SD."""
    a, b = v[t == 1], v[t == 0]
    with np.errstate(invalid="ignore", divide="ignore"):
        sd = np.sqrt((np.nanvar(a, axis=0, ddof=1) + np.nanvar(b, axis=0, ddof=1)) / 2)
        d = np.abs(np.nanmean(v[mt], axis=0) - np.nanmean(v[mc], axis=0)) / sd
    d[~np.isfinite(sd) | (sd == 0)] = np.nan
    return d


def chance_smd(v: np.ndarray, mt: np.ndarray, mc: np.ndarray) -> np.ndarray:
    """Expected |SMD| from chance alone given the measured counts in each matched arm:
    SMD ~ N(0, 1/n1 + 1/n0) in pre-match SD units, E|SMD| = sqrt(2/pi) * sqrt(1/n1 + 1/n0)."""
    n1 = np.sum(~np.isnan(v[mt]), axis=0).astype(float)
    n0 = np.sum(~np.isnan(v[mc]), axis=0).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        c = np.sqrt(2 / np.pi) * np.sqrt(1 / n1 + 1 / n0)
    c[(n1 < 2) | (n0 < 2)] = np.nan
    return c


def hdps_levels(counts: pd.DataFrame, binary_only: bool = False) -> pd.DataFrame:
    """Once / sporadic / frequent binary levels per code (Schneeweiss 2009)."""
    out = {}
    for c in counts.columns:
        v = counts[c].to_numpy(float)
        v = np.nan_to_num(v)
        users = v[v > 0]
        if not len(users):
            continue
        levels = {"once": 1.0} if binary_only else {"once": 1.0, "spor": np.median(users), "freq": np.quantile(users, 0.75)}
        seen = set()
        for lv, thr in levels.items():
            x = (v >= max(thr, 1.0)).astype(float)
            key = x.tobytes()
            if key in seen or x.sum() == 0:
                continue
            seen.add(key)
            out[f"{c}__{lv}"] = x
    return pd.DataFrame(out, index=counts.index)


def hdps_rank(levels: pd.DataFrame, t: np.ndarray) -> pd.Index:
    p1 = levels[t == 1].mean() + 1e-3
    p0 = levels[t == 0].mean() + 1e-3
    return np.log(p1 / p0).abs().sort_values(ascending=False, kind="stable").index


def logit_ps(X: np.ndarray, t: np.ndarray) -> np.ndarray:
    X = StandardScaler().fit_transform(X)
    p = LogisticRegression(C=1.0, max_iter=5000).fit(X, t).predict_proba(X)[:, 1]
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def ps_greedy(lg: np.ndarray, t: np.ndarray, cal: float = 0.2, window: int = 60):
    """Greedy 1:1 caliper matching; anchor = smaller arm, processed in descending
    anchor-propensity order. Returns (treated_idx, control_idx)."""
    anchor = 1 if (t == 1).sum() <= (t == 0).sum() else 0
    s = lg if anchor == 1 else -lg
    width = cal * np.sqrt((lg[t == 1].var() + lg[t == 0].var()) / 2)
    ai = np.where(t == anchor)[0]
    ai = ai[np.argsort(-s[ai], kind="stable")]
    cl = np.where(t != anchor)[0]
    cl = cl[np.argsort(lg[cl], kind="stable")]
    vals, avail, ma, mo = lg[cl], np.ones(len(t), bool), [], []
    for i in ai:
        j = np.searchsorted(vals, lg[i])
        best, bd = None, width
        for k in range(max(0, j - window), min(len(cl), j + window)):
            if avail[cl[k]] and abs(vals[k] - lg[i]) <= bd:
                best, bd = cl[k], abs(vals[k] - lg[i])
        if best is not None:
            avail[best] = False
            ma.append(i)
            mo.append(best)
    ma, mo = np.array(ma, int), np.array(mo, int)
    return (ma, mo) if anchor == 1 else (mo, ma)


def cstat_after_matching(X: np.ndarray, t: np.ndarray, mt, mc, C: float, seed: int = 0) -> float:
    idx = np.concatenate([mt, mc])
    y = np.r_[np.ones(len(mt)), np.zeros(len(mc))]
    if len(mt) < 20:
        return np.nan
    Z = X[idx]
    Z = Z[:, Z.std(0) > 0]
    Z = StandardScaler().fit_transform(Z)
    p = cross_val_predict(LogisticRegression(C=C, max_iter=3000), Z, y,
                          cv=StratifiedKFold(5, shuffle=True, random_state=seed), method="decision_function")
    return float(roc_auc_score(y, p))


def emb(pattern):
    d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(pattern))])
    return pd.DataFrame(np.stack(d.embedding.to_numpy()), index=d.patient_key.values)


def pcs(E, k):
    X = E - E.mean(0)
    U, S, _ = np.linalg.svd(X, full_matrices=False)
    return U[:, :k] * S[:k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-dir", required=True)
    ap.add_argument("--imputation", type=int, default=1)
    ap.add_argument("--panel", required=True)
    ap.add_argument("--panel-dictionary", required=True)
    ap.add_argument("--ecg-emb-glob", required=True)
    ap.add_argument("--ehr-emb-glob", required=True)
    ap.add_argument("--ecg-phenotypes", required=True)
    ap.add_argument("--prognostic-scores", default=None)
    ap.add_argument("--physiology-panel", default=None,
                    help="restricted_physiology_panel.parquet (build_physiology_panel.py); evaluation only")
    ap.add_argument("--shd-scores", default=None, help="restricted_shd_scores.parquet (score_shd_signal.py); adds SHD arms")
    ap.add_argument("--hdps-k", type=int, nargs="+", default=[100, 200, 500])
    ap.add_argument("--split-seed", type=int, default=0)
    ap.add_argument("--no-cstat", action="store_true")
    ap.add_argument("--keep-exposure-features", action="store_true", help="v1 behaviour")
    ap.add_argument("--label", default="")
    ap.add_argument("--method-set", choices=["full", "sparse", "capture"], default="full",
                    help="sparse: demographics + diagnoses base (no meds/utilisation/physiology) +/- ECG")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    t0 = time.time()

    B = args.baseline_dir
    roles = json.load(open(f"{B}/roles.json"))
    cov = pd.read_parquet(f"{B}/restricted_completed_{args.imputation:02d}.parquet").set_index("patient_key")
    obs = pd.read_parquet(f"{B}/restricted_baseline_observed.parquet").set_index("patient_key")
    t_s = cov.pop("treated").astype(int)
    core = [c for c in roles["core"] if c in cov]
    cov = cov[core].astype(float)

    ecg, clm = emb(args.ecg_emb_glob), emb(args.ehr_emb_glob)
    ph = pd.read_parquet(args.ecg_phenotypes).set_index("patient_key")
    panel = pd.read_parquet(args.panel).set_index("patient_key")
    common = cov.index
    for d in (ecg, clm, ph, panel):
        common = common.intersection(d.index)
    common = common.sort_values()
    cov, t = cov.loc[common], t_s.loc[common].to_numpy()
    obs = obs.reindex(common)
    ecg_f = np.hstack([ph.loc[common].to_numpy(float), pcs(ecg.loc[common].to_numpy(float), 32)])
    clm_f = pcs(clm.loc[common].to_numpy(float), 64)
    panel = panel.loc[common]
    SHD = None
    if args.shd_scores:
        SHD = pd.read_parquet(args.shd_scores).set_index("patient_key")
        common = common.intersection(SHD.index).sort_values()
        cov, t = cov.loc[common], t_s.loc[common].to_numpy()
        obs = obs.reindex(common)
        ecg_f = np.hstack([ph.loc[common].to_numpy(float), pcs(ecg.loc[common].to_numpy(float), 32)])
        clm_f = pcs(clm.loc[common].to_numpy(float), 64)
        panel = panel.loc[common]
        SHD = SHD.loc[common].to_numpy(float)
    PP = None
    if args.physiology_panel:
        PP = pd.read_parquet(args.physiology_panel).set_index("patient_key").reindex(common)
    prog = None
    if args.prognostic_scores:
        prog = pd.read_parquet(args.prognostic_scores).set_index("patient_key").reindex(common)

    dic = pd.read_csv(args.panel_dictionary)
    rng = np.random.default_rng(args.split_seed)
    pool = {}
    for dom, grp in dic.groupby("domain"):
        f = grp.feature.to_numpy().copy()
        rng.shuffle(f)
        pool[dom] = (f[: len(f) // 2], f[len(f) // 2:])
    A = [f for a, _ in pool.values() for f in a]
    Bf = [f for _, b in pool.values() for f in b]
    expand = lambda fs: fs + [f.replace("lab_", "labn_") for f in fs if f.startswith("lab_")]
    A, Bf = expand(A), expand(Bf)
    # Exposure-defining features (prior orders of either arm's study drug) are part of the
    # treatment definition, not confounders: dropped from hdPS candidates, pool B and the
    # C-statistic after the split (so other features keep their v1 pool assignment).
    expo = set(roles.get("exposure_features", []))
    n_expo = sum(f in expo for f in A + Bf)
    if not args.keep_exposure_features:
        A, Bf = [f for f in A if f not in expo], [f for f in Bf if f not in expo]
    is_code = lambda f: f.split("_")[0] in ("dx", "rx", "px")
    # evaluation matrix: code features as any-use indicators
    ev = panel.copy()
    code_cols = [c for c in ev.columns if is_code(c)]
    ev[code_cols] = ev[code_cols].gt(0).astype(float)
    EA, EB = ev[A].to_numpy(float), ev[Bf].to_numpy(float)

    codesA = [f for f in A if is_code(f)]
    counts_panel = bool(panel[codesA].max().max() > 1)  # v2 count panel?
    lv = pd.concat([hdps_levels(panel[codesA], binary_only=not counts_panel),
                    hdps_levels(panel[[f for f in A if f.startswith("labn_")]], binary_only=True)], axis=1)
    rank = hdps_rank(lv, t)
    hd = {k: lv[rank[:k]].to_numpy() for k in args.hdps_k}
    # v1 comparator, exactly as in v1: every non-numeric pool-A feature as an any-use indicator
    PA = panel[[f for f in A if not f.startswith("lab_")]].gt(0).astype(float)
    hd_bin100 = PA[hdps_rank(PA, t)[:100]].to_numpy()
    lvl_counts = pd.Series([c.rsplit("__", 1)[1] for c in rank[:max(args.hdps_k)]]).value_counts().to_dict()

    X_core = cov.to_numpy()
    X_demo = cov[[c for c in roles["demo"] if c in cov]].to_numpy()
    X_claims = cov[[c for c in roles["claims"] if c in cov]].to_numpy()
    bases = {"clinical": X_core, "claims": X_claims, "demo": X_demo}
    # Covariate groups. "dx" base = demographics + recorded diagnoses only (incl. index-event
    # diagnoses such as STEMI); no medications, utilisation, procedures, EF, labs or vitals.
    UTIL = {"outpatient_visits", "ed_encounters", "hospital_admissions"}
    phys = [c for c in roles.get("heldout_physiology", []) if c in cov]
    meds = [c for c in core if c.endswith("_order")]
    util = [c for c in core if c in UTIL]
    dxc = [c for c in core if c not in set(roles["demo"]) | set(phys) | set(meds) | UTIL and "pci" not in c]
    X_dx = cov[[c for c in roles["demo"] if c in cov] + dxc].to_numpy()
    ecg_pc = ecg_f[:, ph.shape[1]:]  # 32 PCs only: no supervised phenotype predictions
    noise = np.random.default_rng(1000 + args.split_seed).normal(size=(len(t), ecg_f.shape[1] + clm_f.shape[1]))
    noise_k = np.random.default_rng(2000 + args.split_seed).normal(size=(len(t), max(args.hdps_k)))

    methods = {"unmatched": None,
               f"clinical+noise{noise.shape[1]} (placebo)": np.hstack([X_core, noise]),
               f"clinical+noise{noise_k.shape[1]} (placebo)": np.hstack([X_core, noise_k]),
               "clinical+hdPS100bin (v1)": np.hstack([X_core, hd_bin100])}
    # "dxall": demographics + every diagnosis code of the panel (3-char ICD-10, any use in 365 d,
    # prevalence >= 2%), not only the investigator-chosen comorbidities.
    dx_panel = [c for c in panel.columns if c.startswith("dx_")]
    X_dxall = np.hstack([X_demo, panel[dx_panel].gt(0).astype(float).to_numpy()])
    if args.method_set == "capture":
        # Capture map (2026-09-24): four arms + references. "sparse" = demographics + selected dx.
        noise_e = np.random.default_rng(3000 + args.split_seed).normal(size=(len(t), ecg_pc.shape[1]))
        methods = {"unmatched": None, "clinical (reference)": X_core,
                   "sparse": X_dx, f"sparse+noise{ecg_pc.shape[1]} (placebo)": np.hstack([X_dx, noise_e]),
                   "sparse+ECG": np.hstack([X_dx, ecg_pc]),
                   "hdPS200": np.hstack([X_dx, hd[200]]), "hdPS200+ECG": np.hstack([X_dx, hd[200], ecg_pc]),
                   "hdPS100": np.hstack([X_dx, hd[100]]), "hdPS100+ECG": np.hstack([X_dx, hd[100], ecg_pc]),
                   "hdPS500": np.hstack([X_dx, hd[500]]), "hdPS500+ECG": np.hstack([X_dx, hd[500], ecg_pc]),
                   "sparse+CLMBR": np.hstack([X_dx, clm_f]), "hdPS200+ECG+CLMBR": np.hstack([X_dx, hd[200], ecg_pc, clm_f]),
                   "dxall": X_dxall, "dxall+ECG": np.hstack([X_dxall, ecg_pc]),
                   "claims": X_claims, "claims+ECG": np.hstack([X_claims, ecg_pc]),
                   "clinical+ECG": np.hstack([X_core, ecg_pc])}
        if SHD is not None:
            methods.update({"sparse+SHD": np.hstack([X_dx, SHD]), "sparse+ECG+SHD": np.hstack([X_dx, ecg_pc, SHD]),
                            "hdPS200+SHD": np.hstack([X_dx, hd[200], SHD]),
                            "hdPS200+ECG+SHD": np.hstack([X_dx, hd[200], ecg_pc, SHD])})
        bases = {}
    elif args.method_set == "sparse":
        noise_e = np.random.default_rng(3000 + args.split_seed).normal(size=(len(t), ecg_pc.shape[1]))
        methods = {"unmatched": None, "clinical": X_core, "claims": X_claims, "claims+ECGpc": np.hstack([X_claims, ecg_pc]),
                   "demo": X_demo, "demo+ECGpc": np.hstack([X_demo, ecg_pc]),
                   "dx": X_dx, f"dx+noise{ecg_pc.shape[1]} (placebo)": np.hstack([X_dx, noise_e]),
                   "dx+ECGpc": np.hstack([X_dx, ecg_pc]), "dx+ECG(pc+phenotypes)": np.hstack([X_dx, ecg_f]),
                   "dx+CLMBR": np.hstack([X_dx, clm_f]), "dx+ECGpc+CLMBR": np.hstack([X_dx, ecg_pc, clm_f]),
                   "dx+hdPS200": np.hstack([X_dx, hd[200]]), "dx+hdPS200+ECGpc": np.hstack([X_dx, hd[200], ecg_pc]),
                   "dxall": X_dxall, "dxall+ECGpc": np.hstack([X_dxall, ecg_pc]),
                   "dxall+hdPS200": np.hstack([X_dxall, hd[200]]), "dxall+hdPS200+ECGpc": np.hstack([X_dxall, hd[200], ecg_pc]),
                   "claims+hdPS200": np.hstack([X_claims, hd[200]]), "claims+hdPS200+ECGpc": np.hstack([X_claims, hd[200], ecg_pc]),
                   "clinical+hdPS200": np.hstack([X_core, hd[200]])}
        bases = {}
    for bn, Xb in bases.items():
        methods[bn] = Xb
        methods[f"{bn}+ECG"] = np.hstack([Xb, ecg_f])
        methods[f"{bn}+CLMBR"] = np.hstack([Xb, clm_f])
        methods[f"{bn}+ECG+CLMBR"] = np.hstack([Xb, ecg_f, clm_f])
        for k in args.hdps_k:
            methods[f"{bn}+hdPS{k}"] = np.hstack([Xb, hd[k]])
            methods[f"{bn}+hdPS{k}+ECG+CLMBR"] = np.hstack([Xb, hd[k], ecg_f, clm_f])

    # observed-only values for report covariates / held-out physiology
    rep = [c for c in roles["report_covariates"] if c in cov]
    obs_cols = [c for c in dict.fromkeys(rep + roles.get("heldout_physiology", [])) if c in obs]
    O = obs[obs_cols].to_numpy(float)
    C_core = cov.to_numpy(float)
    # C-statistic matrices: core; core + pool B (lab NaN -> pre-match median)
    EBf = pd.DataFrame(EB, columns=Bf)
    EBf = EBf.fillna(EBf.median()).fillna(0).to_numpy()
    X_c_core = C_core
    X_c_B = np.hstack([C_core, EBf])

    rows = []
    idx = np.arange(len(t))
    for name, X in methods.items():
        mt, mc = (idx[t == 1], idx[t == 0]) if X is None else ps_greedy(logit_ps(X, t), t)
        if len(mt) < 20:  # near-complete separation: record retention, no balance metrics
            rows.append(dict(method=name, pairs=len(mt), imputation=args.imputation, split_seed=args.split_seed))
            continue
        sB, sA = smd_vector(EB, t, mt, mc), smd_vector(EA, t, mt, mc)
        sC = smd_vector(C_core, t, mt, mc)
        sO = smd_vector(O, t, mt, mc)
        cB = chance_smd(EB, mt, mc)
        okB = ~np.isnan(sB) & ~np.isnan(cB)
        r_excess_B = float(np.mean(sB[okB] - cB[okB])) if okB.any() else np.nan
        nondx = np.array([not f.startswith("dx_") for f in Bf])
        sBn = sB[nondx & ~np.isnan(sB)]
        sB, sA = sB[~np.isnan(sB)], sA[~np.isnan(sA)]
        r = dict(method=name, pairs=len(mt), anchor_retention=round(len(mt) / min((t == 1).sum(), (t == 0).sum()), 3),
                 B_n=len(sB), B_frac_gt_0_1=(sB > 0.1).mean(), B_mean=sB.mean(), B_p95=np.quantile(sB, 0.95),
                 A_frac_gt_0_1=(sA > 0.1).mean(), A_mean=sA.mean(),
                 core_max=np.nanmax(sC), core_n_gt_0_1=int(np.nansum(sC > 0.1)),
                 B_nondx_frac_gt_0_1=(sBn > 0.1).mean(), excess_poolB=r_excess_B)
        cC = chance_smd(C_core, mt, mc)
        if PP is not None:
            sP = pd.Series(smd_vector(PP.to_numpy(float), t, mt, mc), index=PP.columns)
            cP = pd.Series(chance_smd(PP.to_numpy(float), mt, mc), index=PP.columns)
            doms = sorted({c.split("__")[0] for c in PP.columns if "__" in c})
            for dom in doms:
                g = sP[[c for c in sP.index if c.startswith(dom + "__")]].dropna()
                if len(g):
                    r[f"mean_{dom}"], r[f"k_{dom}"] = float(g.mean()), int(len(g))
                    r[f"chance_{dom}"] = float(cP[g.index].mean())
                    r[f"excess_{dom}"] = float((g - cP[g.index]).mean())
            for grp, pre in (("labs", "lab_"), ("echo", "echo_")):
                cols_g = [c for c in sP.index if c.startswith(pre)]
                g = sP[cols_g].dropna()
                r[f"n_{grp}_gt_0_1"], r[f"mean_{grp}"], r[f"k_{grp}"] = int((g > 0.1).sum()), float(g.mean()), int(len(g))
                r[f"chance_{grp}"] = float(cP[g.index].mean())
                r[f"excess_{grp}"] = float((g - cP[g.index]).mean())
            for c, v in sP.items():
                r[f"pp_{c}"] = float(v)
        gi = lambda cols: [core.index(c) for c in cols]
        for gname, cols in (("dx", dxc), ("meds", meds), ("util", util)):
            if cols:
                r[f"n_{gname}_gt_0_1"] = int(np.nansum(sC[gi(cols)] > 0.1))
                r[f"mean_{gname}"] = float(np.nanmean(sC[gi(cols)]))
                r[f"excess_{gname}"] = float(np.nanmean(sC[gi(cols)] - cC[gi(cols)]))
        ph_obs = [obs_cols.index(c) for c in phys if c in obs_cols]
        if ph_obs:  # physiology balance on measured (non-imputed) values
            r["n_phys_obs_gt_0_1"] = int(np.nansum(sO[ph_obs] > 0.1))
            r["mean_phys_obs"] = float(np.nanmean(sO[ph_obs]))
            cO = chance_smd(O[:, ph_obs], mt, mc)
            r["chance_phys_obs"] = float(np.nanmean(cO))
            r["excess_phys_obs"] = float(np.nanmean(sO[ph_obs] - cO))
        for c in rep:
            r[f"smd_{c}"] = float(sC[core.index(c)])
        for j, c in enumerate(obs_cols):
            if obs[c].isna().any():
                r[f"smd_obs_{c}"] = float(sO[j])
        if prog is not None:
            P = prog.to_numpy(float)
            for j, c in enumerate(prog.columns):
                r[f"smd_{c}"] = float(smd_vector(P[:, [j]], t, mt, mc)[0])
                r[f"excess_{c}"] = r[f"smd_{c}"] - float(chance_smd(P[:, [j]], mt, mc)[0])
        if not args.no_cstat and X is not None:
            r["cstat_core"] = cstat_after_matching(X_c_core, t, mt, mc, C=1.0, seed=args.split_seed)
            r["cstat_core_poolB"] = cstat_after_matching(X_c_B, t, mt, mc, C=0.01, seed=args.split_seed)
        elif not args.no_cstat:
            r["cstat_core"] = cstat_after_matching(X_c_core, t, idx[t == 1], idx[t == 0], C=1.0, seed=args.split_seed)
            r["cstat_core_poolB"] = cstat_after_matching(X_c_B, t, idx[t == 1], idx[t == 0], C=0.01, seed=args.split_seed)
        r.update(imputation=args.imputation, split_seed=args.split_seed)
        rows.append(r)
    out = pd.DataFrame(rows).set_index("method")
    out.to_csv(f"{args.output_dir}/longtail_imp{args.imputation}_seed{args.split_seed}.csv")
    meta = dict(label=args.label, n=int(len(t)), n_treated=int(t.sum()), n_control=int((1 - t).sum()),
                panel_A=len(A), panel_B=len(Bf), exposure_features_dropped=0 if args.keep_exposure_features else n_expo,
                count_panel=bool(counts_panel), hdps_candidates=int(lv.shape[1]),
                hdps_levels_in_top=lvl_counts, seconds=round(time.time() - t0, 1))
    json.dump(meta, open(f"{args.output_dir}/meta_imp{args.imputation}_seed{args.split_seed}.json", "w"), indent=2)
    pd.set_option("display.width", 250)
    print(json.dumps(meta))
    print(out.round(3).to_string())


if __name__ == "__main__":
    main()
