"""Shared loader and estimators for the v1.3 exploratory program (docs/PROTOCOL_V1_3_AMENDMENT.md).

`load_trial` rebuilds the phase-1 capture-grid design matrices of eval_longtail_balance.py (method set
"capture", split seed 0) from the same inputs, using its functions. `check_against_saved` verifies
that the rebuilt PS logits reproduce the saved phase-2 matches. Restricted data stay in memory;
callers write aggregate output only.
"""
from __future__ import annotations

import glob
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_longtail_balance import emb, hdps_levels, hdps_rank, pcs, ps_greedy  # noqa: E402
from trial_specs import COD_END, DEATH_END, HORIZON_MONTHS, OUTCOMES, PUBLISHED  # noqa: E402

warnings.filterwarnings("ignore")
A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
TRAIN_MRNS = "/mnt/raid0/rbc58/mosaic/present_shd_train_mrns.txt"
ECHO_START = "2016-07-31"
# primary set (phase 2, one per RCT): name -> (trial key, cohort dir)
PRIMARY = {"comet": ("comet", "claude-comet-progref-v1/roster"),
           "paradigm-hf-seq": ("paradigm_hf_seq", "claude-paradigm-hf-seq-cohort-v1"),
           "transform-hf": ("transform_hf", "claude-transform-hf-cohort-v1"),
           "elite-ii": ("elite_ii", "claude-elite-ii-cohort-v1"), "life": ("life", "claude-life-cohort-v2"),
           "plato": ("plato", "claude-plato-cohort-v1"), "aristotle": ("aristotle", "claude-aristotle-cohort-v1"),
           "rocket-af": ("rocket_af", "claude-rocket-af-cohort-v1"), "rely": ("rely", "claude-rely-cohort-v1"),
           "allhat": ("allhat", "claude-allhat-cohort-v1")}
# extension trials (part III): name -> (key, cohort dir)
EXTRA = {n: (k, f"claude-{n}-cohort-v1") for n, k in (
    ("emperor-preserved", "emperor_preserved"), ("east-afnet4", "east_afnet4"), ("cabana", "cabana"),
    ("paradise-mi", "paradise_mi"), ("dcp", "dcp"), ("ontarget", "ontarget"), ("value", "value"), ("ascot", "ascot"),
    ("empa-reg", "empa_reg"), ("carolina", "carolina"), ("invest", "invest"))}


def paths(n):
    if n == "comet":
        return dict(ecg=f"{A}/claude-comet-bcl-v2/restricted_embeddings_part-*.parquet",
                    ph=f"{A}/claude-comet-phenotypes-v2/restricted_cohort_phenotypes.parquet",
                    panel=f"{A}/claude-comet-preindex-panel-v2/restricted_panel.parquet",
                    dic=f"{A}/claude-comet-preindex-panel/panel_dictionary.csv")
    return dict(ecg=f"{A}/claude-{n}-bcl/restricted_embeddings_part-*.parquet",
                ph=f"{A}/claude-{n}-phenotypes/restricted_cohort_phenotypes.parquet",
                panel=f"{A}/claude-{n}-panel-v2/restricted_panel.parquet", dic=f"{A}/claude-{n}-panel-v2/panel_dictionary.csv")


def bench(key):
    p = PUBLISHED[key]
    lo, hi = p["ci"]
    if abs(p["our_orientation"] - p["hr"]) > 1e-6:
        lo, hi = 1 / hi, 1 / lo
    from scipy.stats import norm
    z = norm.ppf(0.5 + p.get("ci_level", 0.95) / 2)
    return float(np.log(p["our_orientation"])), float((np.log(hi) - np.log(lo)) / (2 * z))


class Trial:
    """Design matrices for one trial (primary population = all initiators)."""

    def __init__(self, n, imputation=1, split_seed=0, with_shd=False, baseline_dir=None):
        key, cdir = {**PRIMARY, **EXTRA}[n]
        self.n, self.key = n, key
        P = paths(n)
        B = baseline_dir or f"{A}/claude-{n}-baseline-v11"
        roles = json.load(open(f"{B}/roles.json"))
        self.roles = roles
        cov = pd.read_parquet(f"{B}/restricted_completed_{imputation:02d}.parquet").set_index("patient_key")
        t_s = cov.pop("treated").astype(int)
        core = [c for c in roles["core"] if c in cov]
        cov = cov[core].astype(float)
        ecg = emb(P["ecg"])
        clm_common = None
        ph = pd.read_parquet(P["ph"]).set_index("patient_key")
        panel = pd.read_parquet(P["panel"]).set_index("patient_key")
        # the grid intersects with CLMBR embeddings too
        ehr = (f"{A}/comet-clmbr-full-NAyb4G2x/report/restricted_embeddings_part-*.parquet" if n == "comet"
               else f"{A}/claude-{n}-clmbr-codeonly/report/restricted_embeddings_part-*.parquet")
        clm_keys = pd.concat([pd.read_parquet(f, columns=["patient_key"]) for f in sorted(glob.glob(ehr))]).patient_key
        common = cov.index
        for idx in (ecg.index, pd.Index(clm_keys), ph.index, panel.index):
            common = common.intersection(idx)
        self.shd = None
        if with_shd:
            S = pd.read_parquet(f"{A}/claude-{n}-shd/restricted_shd_scores.parquet").set_index("patient_key")
            common = common.intersection(S.index)
        common = common.sort_values()
        self.keys = common
        self.t = t_s.loc[common].to_numpy()
        cov = cov.loc[common]
        self.cov = cov
        self.core = core
        self.ecg_raw = ecg.loc[common].to_numpy(float)
        self.ecg_pc64 = pcs(self.ecg_raw, 64)
        self.ecg_pc = self.ecg_pc64[:, :32]
        self.ph = ph.loc[common].to_numpy(float)
        if with_shd:
            self.shd = S.loc[common].to_numpy(float)
        panel = panel.loc[common]
        dic = pd.read_csv(P["dic"])
        rng = np.random.default_rng(split_seed)
        pool = {}
        for dom, grp in dic.groupby("domain"):
            f = grp.feature.to_numpy().copy()
            rng.shuffle(f)
            pool[dom] = (f[: len(f) // 2], f[len(f) // 2:])
        Af = [f for a, _ in pool.values() for f in a]
        expand = lambda fs: fs + [f.replace("lab_", "labn_") for f in fs if f.startswith("lab_")]
        Af = expand(Af)
        expo = set(roles.get("exposure_features", []))
        Af = [f for f in Af if f not in expo]
        is_code = lambda f: f.split("_")[0] in ("dx", "rx", "px")
        codesA = [f for f in Af if is_code(f)]
        counts_panel = bool(panel[codesA].max().max() > 1)
        self.lv = pd.concat([hdps_levels(panel[codesA], binary_only=not counts_panel),
                             hdps_levels(panel[[f for f in Af if f.startswith("labn_")]], binary_only=True)], axis=1)
        self.lv_np = self.lv.to_numpy(float)
        UTIL = {"outpatient_visits", "ed_encounters", "hospital_admissions"}
        phys = [c for c in roles.get("heldout_physiology", []) if c in cov]
        meds = [c for c in core if c.endswith("_order")]
        dxc = [c for c in core if c not in set(roles["demo"]) | set(phys) | set(meds) | UTIL and c != "pci_index_30d"]
        self.phys, self.meds, self.util = phys, meds, [c for c in core if c in UTIL]
        self.demo = [c for c in roles["demo"] if c in cov]
        self.dxc = dxc
        self.X_dx = cov[self.demo + dxc].to_numpy()
        self.X_core = cov.to_numpy()
        # R+ physiology panel (evaluation panel used as PS covariates; echo masked before ECHO_START)
        PP = pd.read_parquet(f"{A}/claude-{n}-physpanel-v11/restricted_physiology_panel.parquet").set_index("patient_key").reindex(common)
        ro = pd.read_parquet(f"{A}/{cdir}/restricted_cohort.parquet").set_index("patient_key")
        self.index_date = pd.to_datetime(ro.index_date.reindex(common))
        early = self.index_date.lt(pd.Timestamp(ECHO_START)).fillna(True).to_numpy()
        echo_cols = [c for c in PP.columns if c.split("__")[0] not in ("LAB", "BNP")]
        PP.loc[early, echo_cols] = np.nan
        keep = [c for c in PP.columns if PP[c].notna().mean() >= 0.05 and PP[c].nunique() > 1]
        PPk = PP[keep]
        miss = PPk.isna().astype(float).add_suffix("__missing")
        self.X_pp = np.hstack([PPk.fillna(PPk.median()).to_numpy(float), miss.to_numpy(float)])
        self.n_pp = len(keep)
        self.rng_shuffle = np.random.default_rng(424242)
        self.shuffle_perm = self.rng_shuffle.permutation(len(common))
        self.noise32 = np.random.default_rng(3000 + split_seed).normal(size=(len(common), 32))  # as grid placebo

    # ---- design matrices ----
    def hd(self, k=200, t=None, rows=None):
        """hdPS top-k levels ranked on (possibly resampled) treatment vector."""
        lv = self.lv if rows is None else self.lv.iloc[rows]
        tt = self.t if t is None else t
        r = hdps_rank(lv.reset_index(drop=True), tt)[:k]
        return lv[r].to_numpy(float)

    def arms(self, which, rows=None):
        """Dict arm -> X for the given rows (None = full cohort, in order)."""
        sel = (lambda M: M) if rows is None else (lambda M: M[rows])
        t = self.t if rows is None else self.t[rows]
        need_hd = any(a.startswith("hdPS") for a in which)
        H = self.hd(200, t=t, rows=rows) if need_hd else None
        dx, core = sel(self.X_dx), sel(self.X_core)
        pc = sel(self.ecg_pc)
        E = {"ECG": pc, "ECG8": sel(self.ecg_pc64[:, :8]), "ECG16": sel(self.ecg_pc64[:, :16]), "ECG64": sel(self.ecg_pc64),
             "ECGpheno": np.hstack([sel(self.ph), pc]), "noise32": sel(self.noise32),
             "shufECG": sel(self.ecg_pc[self.shuffle_perm])}
        if self.shd is not None:
            E["SHD"] = sel(self.shd)
        if getattr(self, "enc2", None) is not None:
            E["ENC2"] = sel(self.enc2)
        out = {}
        for a in which:
            if a == "unmatched":
                out[a] = None
            elif a == "clinical (reference)":
                out[a] = core
            elif a == "R+":
                out[a] = np.hstack([core, sel(self.X_pp)])
            elif a == "sparse":
                out[a] = dx
            elif a == "hdPS200":
                out[a] = np.hstack([dx, H])
            elif a.startswith("sparse+"):
                out[a] = np.hstack([dx] + [E[p] for p in a.split("+")[1:]])
            elif a.startswith("hdPS200+"):
                out[a] = np.hstack([dx, H] + [E[p] for p in a.split("+")[1:]])
            else:
                raise KeyError(a)
        return out


# ---- PS models ----
def ps_logit(X, t, model="l2", C=1.0, seed=0):
    Xs = StandardScaler().fit_transform(X)
    if model == "l2":
        p = LogisticRegression(C=C, max_iter=5000).fit(Xs, t).predict_proba(Xs)[:, 1]
    elif model == "gbm":  # 5-fold cross-fitted
        p = np.zeros(len(t))
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(Xs, t):
            p[te] = HistGradientBoostingClassifier(random_state=seed).fit(Xs[tr], t[tr]).predict_proba(Xs[te])[:, 1]
    else:
        raise KeyError(model)
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def match(lg, t, cal=0.2, ratio=1):
    """Greedy caliper matching anchored on the smaller arm. ratio 1 = eval_longtail_balance.ps_greedy
    (phase 2); ratio k > 1 = k passes over the remaining controls. Returns (idx, cluster, weight) of the
    matched sample; cluster = anchor index; controls weighted 1/m for an anchor with m controls."""
    anchor = 1 if (t == 1).sum() <= (t == 0).sum() else 0
    if ratio == 1:
        mt, mc = ps_greedy(lg, t, cal)
        A_, O_ = (mt, mc) if anchor == 1 else (mc, mt)
        return np.r_[A_, O_], np.r_[A_, A_], np.ones(2 * len(A_))
    width = cal * np.sqrt((lg[t == 1].var() + lg[t == 0].var()) / 2)
    anc = np.where(t == anchor)[0]
    avail = np.where(t != anchor)[0]
    pairs = []
    for _ in range(ratio):
        if not len(avail):
            break
        a2, o2 = _greedy_fixed_width(lg[anc], lg[avail], width, anchor)
        pairs += list(zip(anc[a2], avail[o2]))
        avail = np.setdiff1d(avail, avail[o2])
    df = pd.DataFrame(pairs, columns=["a", "o"])
    m = df.groupby("a").o.transform("size").to_numpy()
    ua = df.a.unique()
    return np.r_[ua, df.o.to_numpy()], np.r_[ua, df.a.to_numpy()], np.r_[np.ones(len(ua)), 1.0 / m]


def _greedy_fixed_width(la, lo, width, anchor):
    s = la if anchor == 1 else -la
    order = np.argsort(-s, kind="stable")
    so = np.argsort(lo, kind="stable")
    vals = lo[so]
    taken = np.zeros(len(lo), bool)
    ra, ro = [], []
    for i in order:
        j = np.searchsorted(vals, la[i])
        best, bd = None, width
        l, r = j - 1, j
        while l >= 0 and taken[so[l]]:
            l -= 1
        while r < len(vals) and taken[so[r]]:
            r += 1
        if l >= 0 and la[i] - vals[l] <= bd:
            best, bd = l, la[i] - vals[l]
        if r < len(vals) and vals[r] - la[i] <= bd:
            best = r
        if best is not None:
            taken[so[best]] = True
            ra.append(i)
            ro.append(so[best])
    return np.array(ra, int), np.array(ro, int)


def weights(lg, t, kind):
    p = 1 / (1 + np.exp(-lg))
    if kind == "overlap":
        return np.where(t == 1, 1 - p, p)
    if kind == "iptw":
        lo, hi = np.quantile(p, [0.01, 0.99])
        keep = (p >= lo) & (p <= hi)
        pt = t.mean()
        w = np.where(t == 1, pt / p, (1 - pt) / (1 - p))
        return np.where(keep, w, 0.0)
    raise KeyError(kind)


# ---- Cox ----
def cox(t, e, x, w=None, cluster=None, entry=None):
    """log HR and robust SE for a single binary covariate (lifelines, Efron ties)."""
    d = pd.DataFrame({"t": t, "e": e.astype(int), "x": x})
    kw = dict(duration_col="t", event_col="e", robust=True)
    if w is not None:
        d["w"] = w
        kw["weights_col"] = "w"
        d = d[d.w > 0]
    if cluster is not None:
        d["cl"] = cluster if w is None else np.asarray(cluster)[np.asarray(w) > 0]
        kw["cluster_col"] = "cl"
    if entry is not None:
        d["en"] = entry if w is None else np.asarray(entry)[np.asarray(w) > 0]
        kw["entry_col"] = "en"
    if d.e.sum() < 5 or d[d.x == 1].e.sum() == 0 or d[d.x == 0].e.sum() == 0:
        return np.nan, np.nan
    try:
        m = CoxPHFitter().fit(d, **kw)
    except Exception:
        return np.nan, np.nan
    return float(m.params_["x"]), float(m.standard_errors_["x"])


def outcomes(n, key, keys, strict=False, variant="v1"):
    """(t, e) at the trial horizon for the primary outcome, aligned to keys; NaN rows = excluded."""
    f = f"{A}/claude-{n}-outcomes-{variant}/restricted_outcomes.parquet"
    O = pd.read_parquet(f).set_index("patient_key").reindex(keys)
    H = int(round(HORIZON_MONTHS[key] * 30.4375))
    tc, ec = ("t_primary", "e_primary")
    ok = O[tc].notna() & (O.get("exclude_phase2", 0) == 0)
    t = np.minimum(O[tc].to_numpy(float), H)
    e = ((O[ec] == 1) & (O[tc] <= H)).to_numpy(int)
    return t, e, ok.to_numpy(), H, O


def check_against_saved(T: Trial, arms=("sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)")):
    """Max |PS logit difference| between the rebuilt design and the saved phase-2 matches (imputation 1, seed 0)."""
    M = pd.read_parquet(f"{A}/claude-cap4-all-{T.n}/restricted_matches_imp1_seed0.parquet")
    X = T.arms(list(arms))
    res = {}
    for a in arms:
        s = M[M.method == a].set_index("patient_key").reindex(T.keys)
        lg = ps_logit(X[a], T.t)
        res[a] = float(np.nanmax(np.abs(lg - s.ps_logit.to_numpy())))
    return res
