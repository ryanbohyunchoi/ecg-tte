#!/usr/bin/env python
"""v1.5 analysis engine for one external trial directory (docs/PROTOCOL_V1_5_EXTERNAL.md,
docs/V15_INTERFACE.md). Imports the audited Yale machinery; nothing is reimplemented:
  eval_longtail_balance: hdps_levels, hdps_rank, pcs, smd_vector, chance_smd
  v13_common: ps_logit (L2, C=1, standardised), match (1:1 greedy, caliper 0.2 pooled SD of the logit,
              anchored on the smaller arm), cox (lifelines, Efron ties, robust SE clustered on pair)
  v13_plasmode logic (Weibull-smoothed baseline, lifelines-centring lambda fix, counterfactual truth with
              common random numbers, --resample --subsample 0.8 mode) re-expressed on the interface inputs.

Steps
 1. pids = cohort ∩ baseline ∩ panel ∩ ecg_embedding ∩ outcomes (t, e non-missing). Covariates = the
    roles.json groups demo / dx / meds / labs_vitals / util (index_year is taken from cohort.parquet when a
    role lists it and baseline lacks it, or added to demo when no role lists it). All-missing columns are
    dropped. One sklearn IterativeImputer (BayesianRidge, max_iter 10, random_state 0, deterministic
    conditional means, bounded by each column's observed range) over all covariates jointly; treatment and
    outcome are NOT in the imputation model. Columns with > 5% missing get a missing-indicator that joins the
    column's group, so it enters every arm containing that group.
 2. Designs: sparse = demo + dx; hdPS200 = sparse + top-200 hdPS levels (all dx_/rx_/px_ panel features ->
    once/sporadic/frequent levels when the panel holds counts, once-only if binary; lab_ features as one
    'ever ordered' level; no pool split: every panel feature is a candidate; exposure_features in roles.json,
    if any, removed defensively); ranked by |log prevalence ratio| (hdps_rank) on the analysed sample's
    treatment (re-ranked in each plasmode subsample, as v13 Trial.hd); ECG = 32 PCs of the 256-d embedding;
    CLMBR = 64 PCs (if clmbr_embedding.parquet: CLMBR arms run in the CLMBR subset only, together with
    unmatched/sparse/sparse+ECG/hdPS200/hdPS200+ECG re-run in that subset, labelled '<arm> [clmbr-subset]';
    population column = full / clmbr_subset); clinical = demo + dx + meds + labs_vitals + util.
 3. Per arm: PS, 1:1 match, pair-clustered Cox (unmatched arm: unclustered) -> analysis/estimates.csv
    (primary outcome, t_nco_/e_nco_ negative-control outcomes with NaN rows dropped per outcome, and rct.json
    'secondary' benchmarks' t_sec_/e_sec_ outcomes truncated at their horizon_days). Event counts < 11 suppressed.
 4. Balance on labs_vitals (observed values only, before imputation): mean |SMD| (pre-match pooled SD),
    chance |SMD| from measured counts, excess = mean(|SMD| - chance); capture % = 1 - excess(arm) /
    excess(unmatched) where the unmatched excess >= 0.02 (summarize_capture.py rule) -> analysis/balance.csv
    (groups labs_vitals and phys) and analysis/balance_by_column.csv.
 5. Plasmode (Franklin 2014; v1.3 deviation 6 mode): outcome model = Cox (penalizer 0.01) of the real outcome
    on treatment + standardised imputed clinical covariates (missing indicators excluded); Weibull smoothing
    of the Breslow baseline; lambda corrected for lifelines' centring of `treated`. Scenarios base (all
    coefficients) and phys_only (medication and utilisation coefficients set to 0), true conditional HR 0.8.
    Censoring is administrative at each patient's observed maximum follow-up: C_i = t_i if e_i = 0, else the
    protocol horizon (rct.json horizon_days; max t if absent) -- a patient with an event is assumed to have
    been followable to the horizon. Each replicate subsamples 80% without replacement, re-ranks hdPS, refits
    every PS and match, simulates both scenarios (seeds as v13_plasmode) and fits the pair-clustered Cox.
    Truth per arm and scenario = marginal log HR in that arm's full-data matched population from 20
    counterfactual copies under both treatments with common random numbers -> analysis/plasmode_reps.csv,
    analysis/plasmode_truth.csv.
Output: aggregates only (analysis/*.csv, analysis/meta.json).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from lifelines import CoxPHFitter  # noqa: E402
from sklearn.experimental import enable_iterative_imputer  # noqa: E402,F401
from sklearn.impute import IterativeImputer  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eval_longtail_balance import chance_smd, hdps_levels, hdps_rank, pcs, smd_vector  # noqa: E402
from v13_common import cox, match, ps_logit  # noqa: E402

warnings.filterwarnings("ignore")
GROUPS = ["demo", "dx", "meds", "labs_vitals", "util"]
BASE_ARMS = {"unmatched": None, "sparse": ["demo", "dx"], "sparse+ECG": ["demo", "dx", "ECG"],
             "hdPS200": ["demo", "dx", "HD"], "hdPS200+ECG": ["demo", "dx", "HD", "ECG"], "ECGonly": ["ECG"],
             "clinical": GROUPS}
CLMBR_ARMS = {"CLMBR": ["CLMBR"], "sparse+CLMBR": ["demo", "dx", "CLMBR"],
              "sparse+CLMBR+ECG": ["demo", "dx", "CLMBR", "ECG"], "hdPS200+CLMBR": ["demo", "dx", "HD", "CLMBR"]}
SCEN = {"base": dict(hr=0.8, phys_only=False), "phys_only": dict(hr=0.8, phys_only=True)}
MISS_IND = 0.05
MIN_EXCESS = 0.02
HDPS_K = 200
SUPPRESS = 11
G: dict = {}


def sup(n):
    n = int(n)
    return f"<{SUPPRESS}" if 0 < n < SUPPRESS else str(n)


def emb_frame(path):
    d = pd.read_parquet(path)
    d["pid"] = d.pid.astype(str)
    d = d.drop_duplicates("pid").set_index("pid")
    return d, pd.DataFrame(np.stack(d.embedding.to_numpy()).astype(float), index=d.index)


class TrialData:
    def __init__(self, D: Path):
        self.dir = D
        rd = lambda f: pd.read_parquet(D / f).assign(pid=lambda x: x.pid.astype(str)).drop_duplicates("pid").set_index("pid")
        co, ba, pa = rd("cohort.parquet"), rd("baseline.parquet"), rd("panel.parquet")
        oc = rd("outcomes.parquet")
        roles = json.load(open(D / "roles.json"))
        self.rct = json.load(open(D / "rct.json"))
        dic = pd.read_csv(D / "panel_dictionary.csv")
        ecg_df, ecg = emb_frame(D / "ecg_embedding.parquet")
        clm = None
        if (D / "clmbr_embedding.parquet").exists():
            _, clm = emb_frame(D / "clmbr_embedding.parquet")
        oc = oc[oc.t.notna() & oc.e.notna()]
        pids = co.index.intersection(ba.index).intersection(pa.index).intersection(ecg.index).intersection(oc.index)
        pids = pids.sort_values()
        self.pids = pids
        self.population = "full"
        self.clm_mask = None if clm is None else pids.isin(clm.index)
        self.t = co.loc[pids, "treated"].astype(int).to_numpy()
        self.T = oc.loc[pids, "t"].to_numpy(float)
        self.E = oc.loc[pids, "e"].astype(int).to_numpy()
        self.nco = {c[2:]: (oc.loc[pids, c].to_numpy(float), oc.loc[pids, "e" + c[1:]].to_numpy(float))
                    for c in oc.columns if c.startswith("t_nco_") and "e" + c[1:] in oc}
        # secondary benchmarks (rct.json 'secondary', outcome columns t_sec_<name>/e_sec_<name>), truncated at their horizon
        self.sec = {}
        for sb in self.rct.get("secondary", []) or []:
            tc = str(sb.get("outcome_columns", "")).split("/")[0]
            if tc.startswith("t_sec_") and tc in oc and "e" + tc[1:] in oc:
                Ts, Es = oc.loc[pids, tc].to_numpy(float), oc.loc[pids, "e" + tc[1:]].to_numpy(float)
                Hs = float(sb.get("horizon_days") or np.nanmax(Ts))
                Es = np.where(np.isnan(Ts), np.nan, ((Es == 1) & (Ts <= Hs)).astype(float))
                self.sec[f"sec_{tc[6:]}"] = (np.minimum(Ts, Hs), Es)
        self.lag = ecg_df.loc[pids, "lag_days"].to_numpy(float) if "lag_days" in ecg_df else None
        # ---- covariates ----
        ba = ba.loc[pids].copy()
        notes = []
        role_cols = {g: list(dict.fromkeys(roles.get(g, []))) for g in GROUPS}
        if "index_year" in co and "index_year" not in ba:
            if not any("index_year" in v for v in role_cols.values()):
                role_cols["demo"].append("index_year")
                notes.append("index_year added to demo from cohort.parquet")
            ba["index_year"] = co.loc[pids, "index_year"].astype(float)
        cols, grp_of = [], {}
        for g in GROUPS:
            for c in role_cols[g]:
                if c in ba and c not in grp_of:
                    grp_of[c] = g
                    cols.append(c)
        missing_role_cols = [c for g in GROUPS for c in role_cols[g] if c not in ba]
        raw = ba[cols].apply(pd.to_numeric, errors="coerce").astype(float)
        allnan = [c for c in cols if raw[c].isna().all()]
        cols = [c for c in cols if c not in allnan]
        raw = raw[cols]
        miss = raw.isna().mean()
        self.miss_frac = miss
        if raw.isna().any().any():
            lo, hi = raw.min().to_numpy(), raw.max().to_numpy()
            hi = np.where(hi > lo, hi, lo + 1e-9)  # constant columns
            imp = IterativeImputer(max_iter=10, random_state=0, min_value=lo, max_value=hi)
            X = pd.DataFrame(imp.fit_transform(raw.to_numpy()), index=raw.index, columns=cols)
        else:
            X = raw.copy()
        self.cov = X
        self.groups = {g: [c for c in cols if grp_of[c] == g] for g in GROUPS}
        self.ind = {g: [c for c in self.groups[g] if miss[c] > MISS_IND] for g in GROUPS}
        self.Gm = {}
        for g in GROUPS:
            parts = [X[self.groups[g]].to_numpy(float)]
            if self.ind[g]:
                parts.append(raw[self.ind[g]].isna().to_numpy(float))
            self.Gm[g] = np.hstack(parts)
        lv_cols = [c for c in role_cols["labs_vitals"] if c in raw]
        self.lv_names = lv_cols
        self.lv_obs = raw[lv_cols].to_numpy(float)
        self.phys = [c for c in roles.get("phys", []) if c in lv_cols]
        self.meds, self.util = self.groups["meds"], self.groups["util"]
        # ---- hdPS candidate levels (all panel features; no pool split) ----
        pa = pa.loc[pids]
        expo = set(roles.get("exposure_features", []))
        dom = dict(zip(dic.feature, dic.domain))
        feats = [c for c in pa.columns if c not in expo and c.split("_")[0] in ("dx", "rx", "px", "lab")]
        self.n_undictionaried = sum(c not in dom for c in feats)
        codes = [c for c in feats if c.split("_")[0] in ("dx", "rx", "px")]
        labs = [c for c in feats if c.startswith("lab_")]
        P = pa[codes].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        counts_panel = bool(len(codes) and P.to_numpy().max() > 1)
        parts = [hdps_levels(P, binary_only=not counts_panel)]
        if labs:
            parts.append(hdps_levels(pa[labs].apply(pd.to_numeric, errors="coerce").fillna(0.0).gt(0).astype(float), binary_only=True))
        self.lvl = pd.concat(parts, axis=1)
        self.counts_panel = counts_panel
        self.n_panel = dict(dx=sum(c.startswith("dx_") for c in feats), rx=sum(c.startswith("rx_") for c in feats),
                            px=sum(c.startswith("px_") for c in feats), lab=len(labs), expo_dropped=sum(c in expo for c in pa.columns))
        # ---- embeddings ----
        self.ecg_pc = pcs(ecg.loc[pids].to_numpy(float), 32)
        self.clm_pc = None
        self._clm = clm
        self.arm_spec = dict(BASE_ARMS)
        self.notes = notes + ([f"dropped all-missing: {allnan}"] if allnan else []) + \
            ([f"role columns absent from baseline: {missing_role_cols}"] if missing_role_cols else [])

    def clmbr_view(self):
        """CLMBR population (pids with a CLMBR embedding): CLMBR arms plus the base arms re-run in the same subset
        (labelled '<arm> [clmbr-subset]') for like-for-like CLMBR comparisons. Imputation and ECG PCs are those of
        the full cohort (rows subset); CLMBR PCs are computed within the subset."""
        import copy
        if self._clm is None or not self.clm_mask.any():
            return None
        r = np.where(self.clm_mask)[0]
        V = copy.copy(self)
        V.population = "clmbr_subset"
        V.pids = self.pids[r]
        V.t, V.T, V.E = self.t[r], self.T[r], self.E[r]
        V.nco = {k: (a[r], b[r]) for k, (a, b) in self.nco.items()}
        V.sec = {k: (a[r], b[r]) for k, (a, b) in self.sec.items()}
        V.cov = self.cov.iloc[r]
        V.Gm = {g: m[r] for g, m in self.Gm.items()}
        V.lv_obs = self.lv_obs[r]
        V.lvl = self.lvl.iloc[r]
        V.ecg_pc = self.ecg_pc[r]
        V.clm_pc = pcs(self._clm.loc[V.pids].to_numpy(float), 64)
        V.rows_in_full = r
        V.arm_spec = {f"{a} [clmbr-subset]": v for a, v in BASE_ARMS.items() if a in ("unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG")}
        V.arm_spec.update(CLMBR_ARMS)
        return V

    def hd(self, rows=None, k=HDPS_K):
        lv = self.lvl if rows is None else self.lvl.iloc[rows]
        tt = self.t if rows is None else self.t[rows]
        r = hdps_rank(lv.reset_index(drop=True), tt)[:k]
        return lv[r].to_numpy(float), list(r)

    def designs(self, arms=None, rows=None):
        arms = list(self.arm_spec) if arms is None else arms
        sel = (lambda M: M) if rows is None else (lambda M: M[rows])
        comp = {g: sel(self.Gm[g]) for g in GROUPS}
        comp["ECG"] = sel(self.ecg_pc)
        if self.clm_pc is not None:
            comp["CLMBR"] = sel(self.clm_pc)
        if any("HD" in (self.arm_spec[a] or []) for a in arms):
            comp["HD"], top = self.hd(rows)
            self.last_top = top
        return {a: None if self.arm_spec[a] is None else np.hstack([comp[c] for c in self.arm_spec[a]]) for a in arms}


def split(idx, t):
    return idx[t[idx] == 1], idx[t[idx] == 0]


def fit_matches(X, t):
    M = {}
    for a, Xa in X.items():
        if Xa is None:
            M[a] = (None, None, np.nan)
            continue
        lg = ps_logit(Xa, t)
        idx, cl, _ = match(lg, t)
        M[a] = (idx, cl, float(roc_auc_score(t, lg)) if 0 < t.sum() < len(t) else np.nan)
    return M


def estimates(D: TrialData, M):
    rows = []
    outs = {"primary": (D.T, D.E.astype(float))}
    outs.update({k: v for k, v in D.nco.items()})
    outs.update({k: v for k, v in D.sec.items()})
    for oname, (T, E) in outs.items():
        ok = ~np.isnan(T) & ~np.isnan(E)
        for a, (idx, cl, auc) in M.items():
            if idx is None:
                i = np.where(ok)[0]
                b, se = cox(T[i], E[i].astype(int), D.t[i])
                npairs = np.nan
            else:
                m = ok[idx]
                i, c = idx[m], cl[m]
                b, se = cox(T[i], E[i].astype(int), D.t[i], cluster=c)
                npairs = len(idx) // 2
            it, ic = split(i, D.t)
            rows.append(dict(population=D.population, outcome=oname, arm=a, loghr=b, se=se, hr=np.exp(b), lo=np.exp(b - 1.96 * se), hi=np.exp(b + 1.96 * se),
                             pairs=npairs, n_treated=len(it), n_control=len(ic), events_treated=sup(E[it].sum()),
                             events_control=sup(E[ic].sum()), ps_auc=auc))
    return pd.DataFrame(rows)


def balance(D: TrialData, M):
    rows, cols = [], []
    idx_all = np.arange(len(D.t))
    res = {}
    for a, (idx, _, _) in M.items():
        mt, mc = split(idx_all if idx is None else idx, D.t)
        s = smd_vector(D.lv_obs, D.t, mt, mc)
        c = chance_smd(D.lv_obs, mt, mc)
        res[a] = (s, c)
        for j, name in enumerate(D.lv_names):
            cols.append(dict(population=D.population, arm=a, column=name, phys=name in D.phys, abs_smd=s[j], chance=c[j], excess=s[j] - c[j],
                             measured_frac=float(np.mean(~np.isnan(D.lv_obs[:, j])))))
    for gname, names in (("labs_vitals", D.lv_names), ("phys", D.phys)):
        j = [D.lv_names.index(n) for n in names]
        if not j:
            continue
        su, cu = res[[a for a, (idx, _, _) in M.items() if idx is None][0]]
        oku = ~np.isnan(su[j]) & ~np.isnan(cu[j])
        ex_u = float(np.mean(su[j][oku] - cu[j][oku])) if oku.any() else np.nan
        for a, (s, c) in res.items():
            ok = ~np.isnan(s[j]) & ~np.isnan(c[j])
            ex = float(np.mean(s[j][ok] - c[j][ok])) if ok.any() else np.nan
            cap = 100 * (1 - ex / ex_u) if (ex_u >= MIN_EXCESS and not np.isnan(ex)) else np.nan
            rows.append(dict(population=D.population, group=gname, arm=a, k=int(ok.sum()), mean_abs_smd=float(np.mean(s[j][ok])) if ok.any() else np.nan,
                             n_gt_0_1=int(np.sum(s[j][ok] > 0.1)), chance=float(np.mean(c[j][ok])) if ok.any() else np.nan,
                             excess=ex, unmatched_excess=ex_u, capture_pct=cap))
    return pd.DataFrame(rows), pd.DataFrame(cols)


# ---------------- plasmode ----------------
def simulate(lp, lam, rho, C, rng):
    u = rng.uniform(size=len(lp))
    tev = (-np.log(u) / (lam * np.exp(lp))) ** (1 / rho)
    return np.minimum(tev, C), (tev <= C).astype(int)


def truth(lp0, lam, rho, C, hr, idx, copies=20):
    sel = np.arange(len(lp0)) if idx is None else idx
    rng = np.random.default_rng(99)
    b = np.log(hr)
    ts, es, xs = [], [], []
    for _ in range(copies):
        u = rng.uniform(size=len(sel))
        for x in (0, 1):
            tev = (-np.log(u) / (lam * np.exp(lp0[sel] + b * x))) ** (1 / rho)
            ts.append(np.minimum(tev, C[sel])); es.append((tev <= C[sel]).astype(int)); xs.append(np.full(len(sel), x))
    d = pd.DataFrame({"t": np.concatenate(ts), "e": np.concatenate(es), "x": np.concatenate(xs)})
    return float(CoxPHFitter().fit(d, "t", "e").params_["x"])


def one_rep(rep):
    D, lam, rho, C, lp0, fr = G["D"], G["lam"], G["rho"], G["C"], G["lp0"], G["fr"]
    N = len(D.t)
    rows = np.sort(np.random.default_rng(50_000 + rep).choice(N, int(round(fr * N)), replace=False))
    trt = D.t[rows]
    M = fit_matches(D.designs(rows=rows), trt)
    out = []
    for si, scen in enumerate(SCEN):
        rng = np.random.default_rng(7_000_000 + 1_000_000 * si + rep)
        lp = lp0[scen][rows] + np.log(SCEN[scen]["hr"]) * trt
        tt, ee = simulate(lp, lam, rho, C[rows], rng)
        for a, (idx, cl, _) in M.items():
            b, se = cox(tt, ee, trt) if idx is None else cox(tt[idx], ee[idx], trt[idx], cluster=cl)
            out.append(dict(scenario=scen, rep=rep, arm=a, loghr=b, se=se, pairs=np.nan if idx is None else len(idx) // 2,
                            sim_events=int(ee.sum()) if idx is None else int(ee[idx].sum())))
    return out


def outcome_model(D: TrialData):
    """Plasmode outcome model on the full analysed cohort (see module docstring)."""
    cc = [c for g in GROUPS for c in D.groups[g]]
    Xc = D.cov[cc].to_numpy(float)
    sd = Xc.std(0)
    Z = (Xc - Xc.mean(0)) / np.where(sd > 0, sd, 1)
    var = sd > 0
    names = [c for c, v in zip(cc, var) if v]
    d = pd.DataFrame(Z[:, var], columns=names)
    d["treated"], d["t"], d["e"] = D.t, D.T, D.E
    cph = CoxPHFitter(penalizer=0.01).fit(d, "t", "e")
    beta = cph.params_.reindex(cc).fillna(0.0).to_numpy()
    bh = cph.baseline_cumulative_hazard_
    tb, Hb = bh.index.to_numpy(float), bh.iloc[:, 0].to_numpy(float)
    m = (tb > 0) & (Hb > 0)
    rho, loglam = np.polyfit(np.log(tb[m]), np.log(Hb[m]), 1)
    lam = float(np.exp(loglam)) * float(np.exp(-cph.params_["treated"] * d.treated.mean()))
    medutil = np.isin(cc, D.meds + D.util)
    lp0 = {s: Z @ np.where(medutil & cfg["phys_only"], 0.0, beta) for s, cfg in SCEN.items()}
    H = float(D.rct.get("horizon_days") or np.nanmax(D.T))
    C = np.where(D.E == 1, H, D.T).clip(min=0.5)
    sim_rate = {s: round(float(simulate(lp0[s] + np.log(0.8) * D.t, lam, rho, C, np.random.default_rng(7))[1].mean()), 4) for s in SCEN}
    meta = dict(weibull_rho=round(float(rho), 3), horizon_days=H, real_event_rate=round(float(D.E.mean()), 4),
                sim_event_rate=sim_rate, n_outcome_model_covariates=int(var.sum()), n_meds_util_zeroed_phys_only=int(medutil.sum()),
                outcome_model_treated_loghr=round(float(cph.params_["treated"]), 4),
                censoring="C_i = t_i if e_i = 0 else horizon (administrative at observed maximum follow-up)")
    return dict(lam=lam, rho=rho, lp0=lp0, C=C), meta


def plasmode(V: TrialData, M, model, reps, workers, fr=0.8):
    """Replicates within population V (full cohort or CLMBR subset; the outcome model is always the full-cohort one)."""
    r = getattr(V, "rows_in_full", None)
    sub = (lambda a: a) if r is None else (lambda a: a[r])
    lam, rho, C = model["lam"], model["rho"], sub(model["C"])
    lp0 = {s: sub(v) for s, v in model["lp0"].items()}
    tr = [dict(population=V.population, scenario=s, arm=a, truth_loghr=truth(lp0[s], lam, rho, C, SCEN[s]["hr"], M[a][0]),
               conditional_loghr=float(np.log(SCEN[s]["hr"])), pairs_full=np.nan if M[a][0] is None else len(M[a][0]) // 2)
          for s in SCEN for a in M]
    G.update(D=V, lam=lam, rho=rho, C=C, lp0=lp0, fr=fr)
    if reps > 0:
        with Pool(workers) as p:
            res = [x for rr in p.imap_unordered(one_rep, range(reps)) for x in rr]
        R = pd.DataFrame(res).sort_values(["scenario", "rep", "arm"])
    else:
        R = pd.DataFrame(columns=["scenario", "rep", "arm", "loghr", "se", "pairs", "sim_events"])
    R.insert(0, "population", V.population)
    return R, pd.DataFrame(tr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial-dir", required=True)
    ap.add_argument("--plasmode-reps", type=int, default=200)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--out-subdir", default="analysis")
    a = ap.parse_args()
    os.umask(0o077)
    t0 = time.time()
    Dd = Path(a.trial_dir)
    out = Dd / a.out_subdir
    out.mkdir(exist_ok=True)
    D = TrialData(Dd)
    V = D.clmbr_view()
    pops = [D] + ([V] if V is not None else [])
    Ms, tops = {}, {}
    for P_ in pops:
        Ms[P_.population] = fit_matches(P_.designs(), P_.t)
        tops[P_.population] = getattr(P_, "last_top", [])
    top = tops["full"]
    est = pd.concat([estimates(P_, Ms[P_.population]) for P_ in pops], ignore_index=True)
    est.insert(0, "trial_dir", Dd.name)
    est.to_csv(out / "estimates.csv", index=False)
    bb = [balance(P_, Ms[P_.population]) for P_ in pops]
    bal = pd.concat([b[0] for b in bb], ignore_index=True)
    balc = pd.concat([b[1] for b in bb], ignore_index=True)
    bal.insert(0, "trial_dir", Dd.name)
    balc.insert(0, "trial_dir", Dd.name)
    bal.to_csv(out / "balance.csv", index=False)
    balc.to_csv(out / "balance_by_column.csv", index=False)
    print(est[est.outcome == "primary"].round(3).to_string(index=False))
    print(bal[bal.group == "labs_vitals"].round(3).to_string(index=False))
    t1 = time.time()
    model, pm = outcome_model(D)
    pr = [plasmode(P_, Ms[P_.population], model, a.plasmode_reps, a.workers) for P_ in pops]
    R = pd.concat([x[0] for x in pr], ignore_index=True)
    TR = pd.concat([x[1] for x in pr], ignore_index=True)
    pm.update(subsample=0.8, reps=a.plasmode_reps)
    R.insert(0, "trial_dir", Dd.name)
    TR.insert(0, "trial_dir", Dd.name)
    R.to_csv(out / "plasmode_reps.csv", index=False)
    TR.to_csv(out / "plasmode_truth.csv", index=False)
    meta = dict(trial_dir=Dd.name, rct=D.rct, n=int(len(D.t)), n_treated=int(D.t.sum()), n_control=int((1 - D.t).sum()),
                n_clmbr_subset=None if V is None else int(len(V.t)),
                n_clmbr_subset_treated=None if V is None else int(V.t.sum()), events=sup(D.E.sum()),
                arms=list(D.arm_spec) + ([] if V is None else list(V.arm_spec)), secondary_outcomes=list(D.sec), covariates={g: len(D.groups[g]) for g in GROUPS},
                missing_indicators={g: D.ind[g] for g in GROUPS if D.ind[g]},
                missing_frac={c: round(float(v), 3) for c, v in D.miss_frac.items() if v > 0},
                phys=D.phys, panel_features=D.n_panel, count_panel=D.counts_panel, hdps_candidate_levels=int(D.lvl.shape[1]),
                hdps_top_by_domain=pd.Series([c.split("_")[0] for c in top]).value_counts().to_dict(),
                hdps_top_by_level=pd.Series([c.rsplit("__", 1)[1] for c in top]).value_counts().to_dict(),
                features_not_in_dictionary=int(D.n_undictionaried),
                ecg_lag_days_median=None if D.lag is None else float(np.nanmedian(D.lag)),
                clmbr=V is not None, nco=list(D.nco), plasmode=pm, notes=D.notes,
                seconds_estimates=round(t1 - t0, 1), seconds_plasmode=round(time.time() - t1, 1),
                imputation="sklearn IterativeImputer(BayesianRidge, max_iter=10, random_state=0), covariates only, bounded to observed range",
                hdps="all panel features are candidates (no pool split); lab_ = single 'ordered' level")
    json.dump(meta, open(out / "meta.json", "w"), indent=2, default=str)
    (out / "DONE").write_text(time.strftime("%Y-%m-%d %H:%M:%S\n"))
    print(json.dumps({k: meta[k] for k in ("n", "n_treated", "n_control", "events", "hdps_candidate_levels", "seconds_estimates", "seconds_plasmode")}))


if __name__ == "__main__":
    main()
