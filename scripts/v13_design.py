#!/usr/bin/env python
"""v1.3 Part II + I8 estimates for one trial (docs/PROTOCOL_V1_3_AMENDMENT.md).

For each imputation (1-5) and arm (M0-M4, R from the saved phase-2 matches; R+ rebuilt), on the
matched sample (primary outcome unless stated, trial horizon):
  strict       hospitalisation components = primary billing diagnosis only (II4)
  transport    entropy-balancing weights to the RCT's published Table-1 means (II1)
  pp_naive_G / pp_ipcw_G   on-treatment: censor at protocol deviation (G = 365, 180, 730, switch-only),
               without / with stabilised IPCW (pooled logistic per 90-day interval on treatment, interval
               and the arm's PS covariates; truncated at the 99th percentile) (II2)
  runin90      landmark at 90 d: pairs with both members event-free, uncensored and with a repeat order
               of their assigned drug by day 90; clock restarts at 90 d (II3)
  nco_*        expanded negative-control outcomes (I8)
Pooled by Rubin's rules. Aggregate CSV only.
"""
import os

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = "1"
import argparse  # noqa: E402
import json  # noqa: E402
from multiprocessing import Pool  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import minimize  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from trial_specs import HORIZON_MONTHS, NCO_EXT  # noqa: E402
from v13_common import A, Trial, cox, match, ps_logit  # noqa: E402

ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "R+"]
FACTS = json.load(open(os.path.join(os.path.dirname(__file__), "..", "docs", "v13", "rct_facts.json")))
T1NAME = {"comet": "COMET", "paradigm_hf_seq": "PARADIGM-HF", "transform_hf": "TRANSFORM-HF", "elite_ii": "ELITE II",
          "life": "LIFE", "plato": "PLATO", "aristotle": "ARISTOTLE", "rocket_af": "ROCKET AF", "rely": "RE-LY",
          "allhat": "ALLHAT", "emperor_preserved": "EMPEROR-Preserved", "east_afnet4": "EAST-AFNET 4", "cabana": "CABANA",
          "dcp": "DCP", "ontarget": "ONTARGET", "value": "VALUE", "ascot": "ASCOT-BPLA", "empa_reg": "EMPA-REG OUTCOME",
          "carolina": "CAROLINA", "invest": "INVEST"}
# RCT Table-1 field -> (core covariate, transform of the published value)
T1MAP = {"age_mean": ("age_at_index", lambda v: v), "female_pct": ("male", lambda v: 1 - v / 100),
         "diabetes_pct": ("diabetes", lambda v: v / 100), "hypertension_pct": ("hypertension", lambda v: v / 100),
         "atrial_fibrillation_pct": ("atrial_fibrillation", lambda v: v / 100),
         "heart_failure_pct": ("heart_failure", lambda v: v / 100), "prior_stroke_tia_pct": ("stroke_history", lambda v: v / 100),
         "lvef_mean": ("lvef", lambda v: v), "sbp_mean": ("sbp", lambda v: v), "bmi_mean": ("bmi", lambda v: v),
         "heart_rate_mean": ("heart_rate", lambda v: v), "creatinine_mean_mg_dl": ("creatinine", lambda v: v)}
G = {}


def table1_targets(key, core):
    rec = {**FACTS["table1"], **FACTS.get("new_trials", {})}.get(T1NAME.get(key, key))
    rec = rec.get("table1", rec) if rec else None
    out = {}
    if not rec:
        return out
    for f, (c, fn) in T1MAP.items():
        v = rec.get(f)
        if v is None or c not in core:
            continue
        tv = fn(float(v))
        if f.endswith("_pct") and not (0 < float(v) < 100):
            continue  # 0/100%: a restriction, not a mean to balance
        out[c] = tv
    return out


def ebal(X, target, tol=0.02, min_ess=0.0):
    """Entropy balancing: weights w ∝ exp(Xs @ lam) with weighted means of X equal to target.
    Drops the variable with the largest standardised gap until converged. Returns (w, used, dropped)."""
    cols = list(target)
    dropped = []
    while cols:
        Z = X[cols].to_numpy(float)
        mu, sd = Z.mean(0), Z.std(0)
        sd[sd == 0] = 1
        Zs = (Z - mu) / sd
        ts = (np.array([target[c] for c in cols]) - mu) / sd
        f = lambda lam: np.log(np.exp((Zs - ts) @ lam).sum())
        res = minimize(f, np.zeros(len(cols)), method="BFGS")
        w = np.exp((Zs - ts) @ res.x)
        w /= w.sum()
        gap = np.abs(w @ Zs - ts)
        ess = w.sum() ** 2 / (w ** 2).sum() / len(w)
        if gap.max() < tol and ess >= min_ess:
            return w * len(w), cols, dropped
        worst = cols[int(np.argmax(np.abs(ts)))]
        dropped.append(worst)
        cols = [c for c in cols if c != worst]
    return np.ones(len(X)), [], dropped


def ipcw(Xarm, tr, t, dev, H):
    """Stabilised IPCW rows (start, stop, event-at-stop, weight, subject) for on-treatment follow-up."""
    K = int(np.ceil(H / 90))
    rows = []
    stop_all = np.minimum(t, np.where(np.isnan(dev), np.inf, dev))
    for k in range(K):
        s0, s1 = 90 * k, 90 * (k + 1)
        at = stop_all > s0
        if not at.any():
            break
        ii = np.where(at)[0]
        cens = (~np.isnan(dev[ii])) & (dev[ii] > s0) & (dev[ii] <= np.minimum(s1, t[ii]))
        rows.append(pd.DataFrame({"i": ii, "k": k, "start": s0, "stop": np.minimum(stop_all[ii], s1), "cens": cens.astype(int)}))
    L = pd.concat(rows, ignore_index=True)
    kd = pd.get_dummies(L.k.clip(upper=12), prefix="k", drop_first=True).to_numpy(float)
    Xs = StandardScaler().fit_transform(Xarm)
    D = np.hstack([tr[L.i][:, None], kd, Xs[L.i]])
    Dn = np.hstack([tr[L.i][:, None], kd])
    if L.cens.sum() < 5 or L.cens.mean() > 0.999:
        return None
    p = LogisticRegression(C=1.0, max_iter=3000).fit(D, L.cens).predict_proba(D)[:, 1]
    pn = LogisticRegression(C=1.0, max_iter=3000).fit(Dn, L.cens).predict_proba(Dn)[:, 1]
    L["ps"], L["pn"] = 1 - p, 1 - pn
    # weight during interval k = prod_{j<k} P(uncensored in j): uses the survival up to interval start
    L = L.sort_values(["i", "k"])
    L["cum"] = L.groupby("i").ps.cumprod() / L.ps
    L["cumn"] = L.groupby("i").pn.cumprod() / L.pn
    w = (L.cumn / L.cum).to_numpy()
    L["w"] = np.minimum(w, np.quantile(w, 0.99))
    L = L[L.stop > L.start]
    return L


def rubin(b, se):
    b, se = np.array(b, float), np.array(se, float)
    ok = ~np.isnan(b) & ~np.isnan(se)
    b, se = b[ok], se[ok]
    if not len(b):
        return np.nan, np.nan, 0
    m = len(b)
    return b.mean(), np.sqrt((se ** 2).mean() + (1 + 1 / m) * (b.var(ddof=1) if m > 1 else 0)), m


def job(args):
    imp, arm = args
    n, key = G["n"], G["key"]
    T = Trial(n, imputation=imp)
    H = int(round(HORIZON_MONTHS[key] * 30.4375))
    O1 = pd.read_parquet(f"{A}/claude-{n}-outcomes-v1/restricted_outcomes.parquet").set_index("patient_key").reindex(T.keys)
    O3 = pd.read_parquet(f"{A}/claude-{n}-outcomes-v13/restricted_outcomes_v13.parquet").set_index("patient_key").reindex(T.keys)
    ok = (O1.t_primary.notna() & (O1.exclude_phase2 == 0)).to_numpy()
    tr = T.t
    if arm == "unmatched":
        idx, cl = np.arange(len(tr)), None
    elif arm == "R+":
        idx, cl, _ = match(ps_logit(T.arms(["R+"])["R+"], tr), tr)
    else:
        M = pd.read_parquet(f"{A}/claude-cap4-all-{n}/restricted_matches_imp{imp}_seed0.parquet")
        s = M[(M.method == arm) & (M.pair >= 0)].set_index("patient_key")
        idx = T.keys.get_indexer(s.index)
        assert (idx >= 0).all() and (tr[idx] == s.treated.to_numpy()).all()
        cl = s.pair.to_numpy()
    m = ok[idx]
    idx = idx[m]
    cl = None if cl is None else cl[m]
    x = tr[idx]
    tp = np.minimum(O1.t_primary.to_numpy(float)[idx], H)
    ep = ((O1.e_primary.to_numpy()[idx] == 1) & (O1.t_primary.to_numpy(float)[idx] <= H)).astype(int)
    out = []

    def add(analysis, b, se, extra=None):
        out.append(dict(imputation=imp, arm=arm, analysis=analysis, loghr=b, se=se, **(extra or {})))

    add("primary", *cox(tp, ep, x, cluster=cl))
    ts, es = O3.t_primary_strict.to_numpy(float)[idx], O3.e_primary_strict.to_numpy()[idx]
    add("strict", *cox(np.minimum(ts, H), ((es == 1) & (ts <= H)).astype(int), x, cluster=cl))
    # transport
    tg = table1_targets(key, T.core)
    if tg:
        for lab, me in (("transport", 0.0), ("transport_ess20", 0.2)):  # ess20: v1.3 deviation 5
            w, used, dropped = ebal(T.cov.iloc[idx], tg, min_ess=me)
            add(lab, *cox(tp, ep, x, w=w, cluster=np.arange(len(x)) if cl is None else cl),
                dict(t1_used=";".join(used), t1_dropped=";".join(dropped), ess=float(w.sum() ** 2 / (w ** 2).sum())))
    # per-protocol and run-in
    if "pp_stop365" in O3:
        Xarm = T.X_dx[idx] if arm == "unmatched" else T.arms([arm])[arm][idx]
        for g in ("365", "180", "730", "switch"):
            dev = O3[f"pp_stop{g}" if g != "switch" else "pp_switch"].to_numpy(float)[idx]
            dstop = np.where(np.isnan(dev), np.inf, dev)
            tt = np.minimum(tp, dstop)
            ee = ((ep == 1) & (tp <= dstop)).astype(int)
            add(f"pp_naive_{g}", *cox(tt, ee, x, cluster=cl))
            L = ipcw(Xarm, x, tp, dev, H)
            if L is not None:
                ev = ((ep[L.i] == 1) & (tp[L.i] <= L.stop.to_numpy()) & (tp[L.i] > L.start.to_numpy())).astype(int)
                clr = (np.arange(len(x)) if cl is None else cl)[L.i]
                add(f"pp_ipcw_{g}", *cox(L.stop.to_numpy(float), ev, x[L.i], w=L.w.to_numpy(), cluster=clr,
                                          entry=L.start.to_numpy(float)),
                    dict(max_w=float(L.w.max())))
        rep = O3.repeat_90.to_numpy()[idx]
        alive = (tp > 90)
        dev = O3.pp_stop365.to_numpy(float)[idx]
        keep = alive & (rep == 1)
        if cl is not None:
            ok_pair = pd.Series(keep).groupby(cl).transform("all").to_numpy()
            keep = keep & ok_pair
        if keep.sum() > 50:
            add("runin90", *cox(tp[keep] - 90, ep[keep], x[keep], cluster=None if cl is None else cl[keep]),
                dict(n_kept=int(keep.sum())))
    # expanded negative controls
    for nm in NCO_EXT:
        tn, en = O3[f"t_{nm}"].to_numpy(float)[idx], O3[f"e_{nm}"].to_numpy(float)[idx]
        mm = ~np.isnan(tn)
        if mm.sum() < 50:
            continue
        add(nm, *cox(np.minimum(tn[mm], H), ((en[mm] == 1) & (tn[mm] <= H)).astype(int), x[mm],
                     cluster=None if cl is None else cl[mm]), dict(events=int(((en[mm] == 1) & (tn[mm] <= H)).sum())))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--output-csv", required=True)
    a = ap.parse_args()
    G.update(n=a.trial, key=a.key)
    jobs = [(i, arm) for i in range(1, 6) for arm in ARMS]
    with Pool(a.workers) as p:
        res = [r for rr in p.imap_unordered(job, jobs) for r in rr]
    D = pd.DataFrame(res)
    if "events" in D:  # small-cell suppression in the per-imputation file
        D["events"] = D.events.where(D.events.isna() | (D.events >= 11) | (D.events == 0))
    D.to_csv(a.output_csv.replace(".csv", "_perimp.csv"), index=False)
    rows = []
    for (arm, an), g in D.groupby(["arm", "analysis"]):
        b, se, mm = rubin(g.loghr, g.se)
        r = dict(trial=a.trial, arm=arm, analysis=an, loghr=b, se=se, imputations=mm)
        for c in ("t1_used", "t1_dropped"):
            if c in g:
                r[c] = g[c].dropna().iloc[0] if g[c].notna().any() else None
        for c in ("ess", "n_kept", "events", "max_w"):
            if c in g and g[c].notna().any():
                r[c] = float(g[c].mean())
        if "events" in r and r["events"] < 11:
            r["events"] = "<11"
        rows.append(r)
    pd.DataFrame(rows).to_csv(a.output_csv, index=False)


if __name__ == "__main__":
    main()
