#!/usr/bin/env python
"""MIMIC-IV hdPS on the AI-EHR input window ("hdPS-prior"), with AI-ECG / AI-EHR arms on the hdPS-prior, demographic
and v20 hdPS200 bases (queue docs/queue/QUEUE_2026_10_15_MIMIC_HDPS.md; doc docs/mimic/MIMIC_HDPS_WINDOW.md).

hdPS construction (scripts/v15/v15_analyze.TrialData, lines ~175-188, and TrialData.hd, re-expressed here so that the
candidate panel can be rebuilt under another window; eval_longtail_balance.hdps_levels / hdps_rank are imported):
  candidate features  dx_ (ICD-10 3-char / ICD-9 'i9_' 3-char, count = distinct admissions), rx_ (first alphabetic drug
                      token, count = distinct order days, exposure-drug orders removed), px_ (ICD-10 4-char / ICD-9 3-char,
                      count = distinct dates), lab_<itemid> (measured yes/no); >= 1% prevalence in the trial's built cohort
  levels              once / sporadic / frequent per code feature (count panel), one 'ever measured' level per lab_
  ranking             |log prevalence ratio| on treatment in the analysed rows (stable sort), top 200
  PS                  L2 logistic regression, fixed C = 1, standardised (v13_common.ps_logit); sparse = demo + dx flags
Windows of the candidate panel (cut = min(index admission time, t0); look-back t0 - 365 d):
  orig   as built: 5 v1.5 trials = v15_mimic_cohort.py rx_/lab_ + v15_mimic_auditfix.py dx_/px_ (earlier admissions);
         SOAP II / ELITE II / PEPTIC = v20 mimic_build_new.py (dx_ and px_ include the index admission); rx_ any order
         before the index day, lab_ any draw before t0 (both include the index admission before t0)
  prior  the AI-EHR primary input rule (build_meds_prior_only.py): dx_ / px_ of earlier admissions only (admittime <
         index admittime, hadm <> index, discharged before the cut; dx admitted within the look-back, px dated within
         it); rx_ order start and lab_ chart time before the cut (the index ED stay before admission is kept, as for
         AI-EHR); exposure drugs excluded as before
Sparse part of hdPS-prior: the trial's roles.json dx flags rebuilt from earlier admissions only (v15_mimic_auditfix
convention; PLATO's index-event features from earlier admissions discharged within 30 d), constant flags dropped.

Subcommands (outputs under OUT, umask 077; restricted files hold per-trial pair counts and are never committed):
  panels     rebuild both panels and the prior dx flags per trial; leakage checks; restricted parquet + aggregates
  gate       Step 0: (1) orig panel == trial-dir panel, levels == TrialData.lvl, and the orig-window hdPS200 / demo
             cells == v20 results exactly; (2) the cvd5 cells (all 6 arms) through this code path == results_prior
  analyze    Step 2: bases hdps_prior / demo / hdPS200 x arms base, ECG, CLMBR, ECG+CLMBR, permECG, permCLMBR
  rho        Step 3 mask check: |rho| between held-out items and the PS inputs of each base
  summarize  Step 3 endpoints -> OUT/summary/{summary.json, tables.md}
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import json  # noqa: E402
import sys  # noqa: E402
from datetime import datetime  # noqa: E402
from multiprocessing import Pool  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

from mimic_common import AUD, STAGE, relred_ci  # noqa: E402  (sets sys.path, umask 077)
import mimic_clmbr_analysis as AN  # noqa: E402
import mimic_clmbr_summary as SM  # noqa: E402
import mimic_replication as M  # noqa: E402
import mimic_summary as MS  # noqa: E402
import v15_analyze as VA  # noqa: E402
from build_mimic_meds import expo_tokens  # noqa: E402
from eval_longtail_balance import hdps_levels, hdps_rank, pcs, smd_vector  # noqa: E402
from v13_common import cox, match, ps_logit  # noqa: E402
from v15_mimic_common import CONCEPTS, PCI_PX, sql_list  # noqa: E402

OUT = AUD / "claude-mimic-hdps-20261015"
CL = AUD / "claude-mimic-clmbr-20261014"
AN.EMB = CL / "clmbr" / "prior_full"  # primary AI-EHR input (history before the index admission time)
V20 = M.OUT / "results"
PRIOR_RES = CL / "results_prior"
TRIALS = M.BUILT + M.NEW
P7 = MS.SETS["primary7"]
K_HD = VA.HDPS_K
ARMS = AN.ARMS  # base, ECG, permECG, CLMBR, ECG+CLMBR, permCLMBR (order of reps as mimic_cvd5.design)
CLM = SM.CLM
SUPPRESS = 11


def status(line):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "STATUS.md", "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} {line}\n")


def pct_sup(n, d):
    """Share in % with the numerator suppressed when it is a count of 1-10 (also when 1-10 below the total)."""
    n, d = int(n), int(d)
    if 0 < n < SUPPRESS or 0 < d - n < SUPPRESS:
        return "suppressed (count within 1-10 of 0 or of the total)"
    return round(100 * n / d, 1) if d else None


# ------------------------------------------------------------------ panel rebuild
def _con(k):
    import duckdb
    con = duckdb.connect()
    con.execute("SET threads=16")
    con.execute("SET memory_limit='120GB'")
    for t in ("admissions", "diagnoses_icd", "procedures_icd", "prescriptions", "labevents"):
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{STAGE}/{t}.parquet')")
    it = pd.read_parquet(M.tdir(k) / "index_time.parquet")[["pid", "subject_id", "hadm_id", "index_datetime"]]
    co = pd.read_parquet(M.tdir(k) / "cohort.parquet")
    assert len(it) == len(co) and set(it.pid) == set(co.pid) and it.subject_id.is_unique
    con.register("it_df", it)
    con.execute("""CREATE TEMP TABLE c AS SELECT it.pid, it.subject_id, it.hadm_id, it.index_datetime t0,
                   CAST(it.index_datetime AS DATE) d0, ad.admittime, ad.dischtime, ad.edregtime,
                   least(ad.admittime, it.index_datetime) cut FROM it_df it
                   JOIN admissions ad ON ad.subject_id = it.subject_id AND ad.hadm_id = it.hadm_id""")
    assert con.execute("SELECT count(*) FROM c").fetchone()[0] == len(it), "index admission not found"
    con.execute("""CREATE TEMP TABLE rxt AS SELECT subject_id, hadm_id, starttime,
                   regexp_split_to_array(lower(coalesce(drug, '')), '[^a-z0-9]+') toks
                   FROM prescriptions WHERE subject_id IN (SELECT subject_id FROM c)""")
    return con, list(co.pid)


def queries(k, window, EXPO):
    """Event-level SQL per domain: (pid, f, event ek,event time, src_hadm) rows; the feature count is
    count(DISTINCT ek). orig reproduces the trial builders' SQL; prior is the AI-EHR window."""
    tok = "list_filter(r.toks, x -> regexp_matches(x, '^[a-z][a-z]+$') AND x <> 'nf')[1]"
    dxf = "CASE WHEN d.icd_version = 10 THEN 'dx_' || substr(d.icd_code, 1, 3) ELSE 'dx_i9_' || substr(d.icd_code, 1, 3) END"
    pxf = "CASE WHEN p.icd_version = 10 THEN 'px_' || substr(p.icd_code, 1, 4) ELSE 'px_i9_' || substr(p.icd_code, 1, 3) END"
    lab = """SELECT c.pid, 'lab_' || CAST(l.itemid AS VARCHAR) f, 1 ek,l.charttime t, l.hadm_id src
             FROM c JOIN labevents l ON l.subject_id = c.subject_id
             WHERE l.charttime < {hi} AND l.charttime >= c.t0 - INTERVAL 365 DAY"""
    rx = f"""SELECT c.pid, 'rx_' || {tok} f, CAST(r.starttime AS DATE) ek,r.starttime t, r.hadm_id src
             FROM c JOIN rxt r ON r.subject_id = c.subject_id
             WHERE r.starttime < {{hi}} AND r.starttime >= c.t0 - INTERVAL 365 DAY AND NOT list_has_any(r.toks, {sql_list(EXPO)})"""
    if window == "orig" and k in M.BUILT:  # v15_mimic_cohort.py rx_/lab_; v15_mimic_auditfix.py dx_/px_
        dx = f"""SELECT c.pid, {dxf} f, d.hadm_id ek,ad.dischtime t, CAST(ad.hadm_id AS BIGINT) src
                 FROM c JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id
                      AND ad.admittime >= c.t0 - INTERVAL 365 DAY
                 JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id"""
        px = f"""SELECT c.pid, {pxf} f, p.chartdate ek,CAST(p.chartdate AS TIMESTAMP) t, p.hadm_id src
                 FROM c JOIN procedures_icd p ON p.subject_id = c.subject_id AND p.hadm_id <> c.hadm_id
                 WHERE p.chartdate < c.d0 AND p.chartdate >= c.d0 - INTERVAL 365 DAY"""
        hi_rx, hi_lab = "CAST(c.d0 AS TIMESTAMP)", "c.t0"
    elif window == "orig":  # mimic_build_new.py (index admission included in dx_ and px_)
        dx = f"""SELECT c.pid, {dxf} f, d.hadm_id ek,ad.dischtime t, CAST(ad.hadm_id AS BIGINT) src
                 FROM c JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime <= c.admittime
                      AND (ad.hadm_id = c.hadm_id OR ad.admittime >= c.t0 - INTERVAL 365 DAY)
                 JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id"""
        px = f"""SELECT c.pid, {pxf} f, p.chartdate ek,CAST(p.chartdate AS TIMESTAMP) t, p.hadm_id src
                 FROM c JOIN procedures_icd p ON p.subject_id = c.subject_id
                 WHERE p.chartdate < c.d0 AND p.chartdate >= c.d0 - INTERVAL 365 DAY"""
        hi_rx, hi_lab = "CAST(c.d0 AS TIMESTAMP)", "c.t0"
    else:  # prior: the AI-EHR primary-input window
        early = """JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id
                   AND ad.dischtime < c.cut"""
        dx = f"""SELECT c.pid, {dxf} f, d.hadm_id ek,ad.dischtime t, CAST(ad.hadm_id AS BIGINT) src
                 FROM c {early} AND ad.admittime >= c.t0 - INTERVAL 365 DAY
                 JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id"""
        px = f"""SELECT c.pid, {pxf} f, p.chartdate ek,ad.dischtime t, p.hadm_id src
                 FROM c {early} JOIN procedures_icd p ON p.subject_id = ad.subject_id AND p.hadm_id = ad.hadm_id
                 WHERE p.chartdate >= c.d0 - INTERVAL 365 DAY"""
        hi_rx = hi_lab = "c.cut"
    return {"dx": dx, "rx": rx.format(hi=hi_rx), "px": px, "lab": lab.format(hi=hi_lab)}


def build_panel(con, k, window, pids_all):
    EXPO = expo_tokens(k)
    n = len(pids_all)
    frames, dic, ev = [], [], {}
    for dom, q in queries(k, window, EXPO).items():
        con.execute(f"CREATE OR REPLACE TEMP TABLE ev_{dom} AS {q}")
        d = con.execute(f"""SELECT f, list(pid) s, list(c) c FROM (SELECT pid, f, count(DISTINCT ek) c FROM ev_{dom}
                            WHERE f IS NOT NULL GROUP BY 1, 2) GROUP BY f HAVING count(DISTINCT pid) >= {0.01 * n} ORDER BY f""").df()
        for f, s, cc in zip(d.f, d.s, d.c):
            name = f.lower() if dom == "rx" else f
            frames.append(pd.Series(np.asarray(cc, float), index=pd.Index(s), name=name))
            dic.append((name, dom))
        ev[dom] = d.f.tolist()
    P = pd.concat(frames, axis=1).reindex(pids_all).fillna(0.0)
    P.index.name = "pid"
    leak = [c for c in P.columns if c.startswith("rx_") and c[3:] in EXPO]
    assert not leak, leak
    return P, pd.DataFrame(dic, columns=["feature", "domain"])


def leakage(con, k, window, P, analysed):
    """Aggregate checks over the input events (rows) that feed the retained candidate features, analysed patients."""
    con.register("an_df", pd.DataFrame({"pid": [str(x) for x in analysed]}))
    con.register("keep_df", pd.DataFrame({"f": list(P.columns)}))  # rx_ names are lower case in both
    # index episode = an event of the index admission (src = index hadm) or timed in the index ED stay [edregtime, admittime)
    con.execute("""CREATE OR REPLACE TEMP TABLE e2 AS
        WITH ein AS (SELECT 'dx' dom, pid, f, t, src FROM ev_dx UNION ALL SELECT 'rx', pid, lower(f), t, src FROM ev_rx
                     UNION ALL SELECT 'px', pid, f, t, src FROM ev_px UNION ALL SELECT 'lab', pid, f, t, src FROM ev_lab)
        SELECT ein.*, c.cut, c.admittime, c.t0, c.subject_id, coalesce(ein.src = c.hadm_id, false) ix_hadm,
               coalesce(ein.src = c.hadm_id, false) OR coalesce(ein.t >= c.edregtime AND ein.t < c.admittime, false) ep
        FROM ein JOIN c USING (pid) WHERE ein.pid IN (SELECT pid FROM an_df) AND ein.f IN (SELECT f FROM keep_df)""")
    by = con.execute("""SELECT dom, count(*) n, count(*) FILTER (WHERE t >= cut) at_or_after_cut,
                        count(*) FILTER (WHERE t >= admittime) at_or_after_admit, count(*) FILTER (WHERE t >= t0) at_or_after_t0,
                        count(*) FILTER (WHERE ix_hadm) index_hadm, count(*) FILTER (WHERE ep) index_episode
                        FROM e2 GROUP BY dom""").df().set_index("dom")
    r = {d: ({kk: int(v) for kk, v in by.loc[d].items()} if d in by.index else
             dict(n=0, at_or_after_cut=0, at_or_after_admit=0, at_or_after_t0=0, index_hadm=0, index_episode=0))
         for d in ("dx", "rx", "px", "lab")}
    # dx / px: the source admission must be an earlier one, discharged before the cut
    r["dxpx_from_index_or_later_admission"] = int(con.execute(
        """SELECT count(*) FROM e2 JOIN admissions ad ON ad.subject_id = e2.subject_id AND ad.hadm_id = e2.src
           WHERE e2.dom IN ('dx', 'px') AND (ad.admittime >= e2.admittime OR ad.dischtime >= e2.cut)""").fetchone()[0])
    a = con.execute("""SELECT count(DISTINCT pid) n_with, count(DISTINCT pid) FILTER (WHERE ep) any_ep FROM e2""").df().iloc[0]
    r["patients_any_index_episode_event"] = int(a.any_ep)
    r["patients_only_index_episode_events"] = int(con.execute(
        "SELECT count(*) FROM (SELECT pid, bool_and(ep) only_ep FROM e2 GROUP BY pid) WHERE only_ep").fetchone()[0])
    r["patients_with_any_event"] = int(a.n_with)
    r["events_total"] = sum(r[d]["n"] for d in ("dx", "rx", "px", "lab"))
    r["events_index_episode"] = sum(r[d]["index_episode"] for d in ("dx", "rx", "px", "lab"))
    r["expo_features"] = [c for c in P.columns if c.startswith("rx_") and c[3:] in set(expo_tokens(k))]
    return r


def prior_dx(con, k, pids):
    """roles.json dx flags from earlier admissions only (v15_mimic_auditfix convention)."""
    from v15_mimic_common import concept_table
    concept_table(con)
    roles = json.load(open(M.tdir(k) / "roles.json"))
    cdx = con.execute("""SELECT DISTINCT c.pid, k.concept FROM c JOIN admissions ad ON ad.subject_id = c.subject_id
        AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id
        JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
        JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)""").df()
    F = pd.DataFrame(index=pd.Index(pids, name="pid"))
    for cname in roles["dx"]:
        if cname in CONCEPTS:
            F[cname] = F.index.isin(cdx[cdx.concept == cname].pid).astype(float)
    if k == "plato":  # index-event features from earlier admissions discharged within 30 d (auditfix)
        st = con.execute("""SELECT DISTINCT c.pid FROM c JOIN admissions ad ON ad.subject_id = c.subject_id
            AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id AND ad.dischtime >= c.t0 - INTERVAL 30 DAY
            JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
            JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)
            WHERE k.concept = 'stemi'""").df()
        p10, p9 = PCI_PX
        pc = con.execute(f"""SELECT DISTINCT c.pid FROM c JOIN admissions ad ON ad.subject_id = c.subject_id
            AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id AND ad.dischtime >= c.t0 - INTERVAL 30 DAY
            JOIN procedures_icd p ON p.subject_id = ad.subject_id AND p.hadm_id = ad.hadm_id
            WHERE (p.icd_version = 10 AND list_has_any({sql_list(p10)}, [lower(substr(p.icd_code, 1, 4))]))
               OR (p.icd_version = 9 AND list_has_any({sql_list(p9)}, [lower(substr(p.icd_code, 1, 4))]))""").df()
        for cname, s in (("stemi_index_adm", st), ("pci_index_30d", pc)):
            if cname in roles["dx"]:
                F[cname] = F.index.isin(s.pid).astype(float)
    assert list(F.columns) == [c for c in roles["dx"]], (k, list(F.columns), roles["dx"])
    return F


def panels_trial(k):
    D = VA.TrialData(M.tdir(k))
    con, pids_all = _con(k)
    res = dict(trial=k)
    (OUT / "panels").mkdir(parents=True, exist_ok=True)
    for window in ("orig", "prior"):
        P, dic = build_panel(con, k, window, pids_all)
        P.reset_index().to_parquet(OUT / "panels" / f"restricted_{k}_{window}.parquet", index=False)
        dic.to_csv(OUT / "panels" / f"{k}_{window}_dictionary.csv", index=False)
        res[window] = dict(n_features=int(P.shape[1]), by_domain=dic.domain.value_counts().to_dict(),
                           leakage=leakage(con, k, window, P, D.pids))
    F = prior_dx(con, k, list(D.pids))
    F.reset_index().to_parquet(OUT / "panels" / f"restricted_{k}_prior_dx.parquet", index=False)
    raw = pd.read_parquet(M.tdir(k) / "baseline.parquet").assign(pid=lambda x: x.pid.astype(str)).drop_duplicates("pid").set_index("pid").reindex(D.pids)
    res["prior_dx_equal_baseline"] = {c: int((raw[c] != F[c]).sum()) == 0 for c in F.columns if c in raw}
    res["prior_dx_discordant_cols"] = [c for c, ok in res["prior_dx_equal_baseline"].items() if not ok]
    print(k, "panels done", flush=True)
    return res


# ------------------------------------------------------------------ hdPS levels and designs
def levels(panel, pids, expo=()):
    """TrialData lines ~176-188, unchanged."""
    pa = panel.loc[pids]
    feats = [c for c in pa.columns if c not in expo and c.split("_")[0] in ("dx", "rx", "px", "lab")]
    codes = [c for c in feats if c.split("_")[0] in ("dx", "rx", "px")]
    labs = [c for c in feats if c.startswith("lab_")]
    P = pa[codes].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    counts_panel = bool(len(codes) and P.to_numpy().max() > 1)
    parts = [hdps_levels(P, binary_only=not counts_panel)]
    if labs:
        parts.append(hdps_levels(pa[labs].apply(pd.to_numeric, errors="coerce").fillna(0.0).gt(0).astype(float), binary_only=True))
    return pd.concat(parts, axis=1)


def hd(lvl, t, rows, k=K_HD):
    """TrialData.hd, unchanged."""
    lv = lvl.iloc[rows]
    r = hdps_rank(lv.reset_index(drop=True), t[rows])[:k]
    return lv[r].to_numpy(float), list(r)


def read_panel(path):
    return pd.read_parquet(path).assign(pid=lambda x: x.pid.astype(str)).drop_duplicates("pid").set_index("pid")


class Ctx:
    """Per-trial inputs of every base: TrialData + rebuilt levels + flags + representations."""

    def __init__(self, k, windows=("orig", "prior"), clmbr=True, align_orig=True):
        self.k = k
        self.D = D = VA.TrialData(M.tdir(k))
        expo = set(json.load(open(D.dir / "roles.json")).get("exposure_features", []))
        self.lvl = {}
        for w in windows:
            P = read_panel(OUT / "panels" / f"restricted_{k}_{w}.parquet")
            if w == "orig" and align_orig:
                # duckdb GROUP BY order is not deterministic: take the trial-dir panel's column order (same column set)
                ref = read_panel(D.dir / "panel.parquet")
                assert set(P.columns) == set(ref.columns), f"{k}: rebuilt orig panel has a different feature set"
                P = P[list(ref.columns)]
            self.lvl[w] = levels(P, D.pids, expo)
        F = pd.read_parquet(OUT / "panels" / f"restricted_{k}_prior_dx.parquet").set_index("pid").reindex(D.pids)
        assert F.notna().all().all()
        self.dxp = F.to_numpy(float)
        C5 = pd.read_parquet(CL / "step0" / "flags" / f"{k}.parquet").set_index("pid").reindex(D.pids)
        assert C5.notna().all().all()
        self.cvd5 = C5[AN.C5.CVD5["cvd5"]].to_numpy(float)
        self.perm = np.random.default_rng(M.SEED).permutation(len(D.t))
        self.REP = {"ECG": D.ecg_pc, "permECG": D.ecg_pc[self.perm]}
        if clmbr:
            clm_pc = pcs(AN.clmbr_matrix(k, D.pids), 64)
            self.REP.update(CLMBR=clm_pc, permCLMBR=clm_pc[self.perm])

    def base_parts(self, base, r):
        D = self.D
        if base == "demo":
            return [D.Gm["demo"][r]]
        if base in ("hdPS200", "hdPS200_rebuilt"):
            H, _ = (D.hd(rows=r) if base == "hdPS200" else hd(self.lvl["orig"], D.t, r))
            return [D.Gm["demo"][r], D.Gm["dx"][r], H]
        if base == "cvd5":
            Cr = self.cvd5[r]
            return [D.Gm["demo"][r], Cr[:, Cr.std(0) > 0]]
        if base == "hdps_prior":
            Cr = self.dxp[r]
            H, _ = hd(self.lvl["prior"], D.t, r)
            return [D.Gm["demo"][r], Cr[:, Cr.std(0) > 0], H]
        raise KeyError(base)


def run_cells(k, bases, arms, pops=("all",), clmbr=True, windows=("orig", "prior"), label=None):
    """Cells as mimic_clmbr_analysis.run_trial (+ the v20 row fields), for any base of Ctx.base_parts."""
    X_ = Ctx(k, windows=windows, clmbr=clmbr)
    D = X_.D
    rct = json.load(open(D.dir / "rct.json"))
    rb = np.log(rct["our_orientation"])
    rs = (np.log(rct["our_hi"]) - np.log(rct["our_lo"])) / (2 * 1.96)
    lag = D.lag if D.lag is not None else np.full(len(D.t), np.nan)
    popmask = {"all": np.ones(len(D.t), bool), "no_index_day_ecg": ~(lag < 1)}
    V, cols, blk, MI, mi_cols = M.panel_for(D, k, "demo")
    rows, vrows = [], []
    for base in bases:
        for pop in pops:
            mask = popmask[pop]
            if min((D.t[mask] == 1).sum(), (D.t[mask] == 0).sum()) < 50:
                continue
            r = np.where(mask)[0]
            t = D.t[r]
            s_un = smd_vector(V[r], t, np.where(t == 1)[0], np.where(t == 0)[0])
            bp = X_.base_parts(base, r)
            for arm in arms:
                X = np.hstack(bp + [X_.REP[x][r] for x in ARMS[arm]])
                lg = ps_logit(X, t)
                idx, cl, _ = match(lg, t)
                mt, mc = idx[t[idx] == 1], idx[t[idx] == 0]
                s = smd_vector(V[r], t, mt, mc)
                smi = smd_vector(MI[r], t, mt, mc) if MI is not None else np.array([])
                ok = np.isfinite(s)
                T, E = D.T[r], D.E[r].astype(int)
                b, se = cox(T[idx], E[idx], t[idx], cluster=cl)
                p = 1 / (1 + np.exp(-lg))
                n_small = int(min((t == 1).sum(), (t == 0).sum()))
                row = dict(trial=k, base=label or base, arm=arm, pop=pop, n_pairs=len(idx) // 2, n_small=n_small,
                           retention=len(idx) / 2 / n_small, n_inputs=X.shape[1], c_insample=float(roc_auc_score(t, lg)),
                           share_extreme_ps=float(np.mean((p < 0.01) | (p > 0.99))), n_vars=int(ok.sum()),
                           pct_bal=float(100 * np.mean(s[ok] < 0.1)), mean_smd=float(np.mean(s[ok])),
                           mean_smd_unmatched=float(np.nanmean(s_un)),
                           pct_bal_miss=float(100 * np.mean(smi[np.isfinite(smi)] < 0.1)) if len(smi) else np.nan,
                           loghr=b, se=se, rct_loghr=rb, rct_se=rs, rct_measure=rct.get("measure", "HR"),
                           events=int(E[idx].sum()) if E[idx].sum() >= 11 else -1)
                for bb in sorted(set(blk)):
                    j = [i for i, x in enumerate(blk) if x == bb and np.isfinite(s[i])]
                    row[f"mean_smd_{bb}"] = float(np.mean(s[j])) if j else np.nan
                    row[f"pct_bal_{bb}"] = float(100 * np.mean(s[j] < 0.1)) if j else np.nan
                if base == "cvd5":
                    row["n_dx_flags_in_ps"] = bp[1].shape[1]
                rows.append(row)
                for c, bb, x, xu in zip(cols, blk, s, s_un):
                    vrows.append(dict(trial=k, base=label or base, arm=arm, pop=pop, var=c, block=bb, abs_smd=x, abs_smd_unmatched=xu))
    return pd.DataFrame(rows), pd.DataFrame(vrows)


# ------------------------------------------------------------------ Step 0 gates
def _cmp(a, b, keys, cols):
    a, b = a.set_index(keys).sort_index(), b.set_index(keys).sort_index()
    same = a.index.equals(b.index)
    if not same:
        return dict(same_rows=False, max_abs_diff=np.inf, nan_equal=False, text_equal=False)
    num = [c for c in cols if pd.api.types.is_numeric_dtype(a[c])]
    txt = [c for c in cols if c not in num]
    d = float((a[num] - b[num]).abs().max().max())
    return dict(same_rows=True, rows=len(a), max_abs_diff=d, nan_equal=bool((a[num].isna() == b[num].isna()).all().all()),
                text_equal=bool((a[txt].astype(str) == b[txt].astype(str)).all().all()) if txt else True)


def _roundtrip(A, Vv, k, name):
    """Write the cells as the reference files were written and compare the re-read copies (same CSV float parser)."""
    (OUT / "gate").mkdir(parents=True, exist_ok=True)
    A.to_csv(OUT / "gate" / f"{k}_{name}_arms.csv", index=False)
    Vv.to_csv(OUT / "gate" / f"{k}_{name}_vars.csv", index=False)
    return pd.read_csv(OUT / "gate" / f"{k}_{name}_arms.csv"), pd.read_csv(OUT / "gate" / f"{k}_{name}_vars.csv")


def gate1_trial(k):
    D = VA.TrialData(M.tdir(k))
    ref = read_panel(D.dir / "panel.parquet")
    P = read_panel(OUT / "panels" / f"restricted_{k}_orig.parquet")
    out = dict(trial=k, panel_same_features=set(P.columns) == set(ref.columns))
    if out["panel_same_features"]:
        Pa = P[list(ref.columns)].reindex(ref.index)
        out["panel_same_rows"] = bool(Pa.index.equals(ref.index))
        out["panel_max_abs_diff"] = float((Pa - ref.astype(float)).abs().max().max())
    else:
        out["n_only_rebuilt"], out["n_only_ref"] = len(set(P.columns) - set(ref.columns)), len(set(ref.columns) - set(P.columns))
    expo = set(json.load(open(D.dir / "roles.json")).get("exposure_features", []))
    L0 = levels(ref, D.pids, expo)
    out["levels_fn_equal_trialdata"] = bool(L0.columns.equals(D.lvl.columns) and (L0.to_numpy() == D.lvl.to_numpy()).all())
    if not out["panel_same_features"]:
        return out, None, None
    A, Vv = run_cells(k, ["demo", "hdPS200_rebuilt"], ["base", "ECG", "permECG"], pops=("all", "no_index_day_ecg"),
                      clmbr=False, windows=("orig",))
    A["base"] = A.base.replace({"hdPS200_rebuilt": "hdPS200"})
    Vv["base"] = Vv.base.replace({"hdPS200_rebuilt": "hdPS200"})
    A, Vv = _roundtrip(A, Vv, k, "gate1")
    ra = pd.read_csv(V20 / f"{k}_arms.csv")
    rv = pd.read_csv(V20 / f"{k}_vars.csv")
    ra, rv = ra[ra.base.isin(["demo", "hdPS200"])], rv[rv.base.isin(["demo", "hdPS200"])]
    keys = ["base", "arm", "pop"]
    out["arms"] = _cmp(ra, A[ra.columns], keys, [c for c in ra.columns if c not in keys + ["trial"]])
    out["vars"] = _cmp(rv, Vv[rv.columns], keys + ["var"], ["abs_smd", "abs_smd_unmatched", "block"])
    return out, A, Vv


def gate2_trial(k):
    A, Vv = run_cells(k, ["cvd5"], list(ARMS), pops=("all", "no_index_day_ecg"), windows=("prior",))
    A, Vv = _roundtrip(A, Vv, k, "gate2")
    ra = pd.read_csv(PRIOR_RES / f"{k}_arms.csv")
    rv = pd.read_csv(PRIOR_RES / f"{k}_vars.csv")
    ra, rv = ra[ra.base == "cvd5"], rv[rv.base == "cvd5"]
    keys = ["base", "arm", "pop"]
    return dict(trial=k, arms=_cmp(ra, A[ra.columns], keys, [c for c in ra.columns if c not in keys + ["trial"]]),
                vars=_cmp(rv, Vv[rv.columns], keys + ["var"], ["abs_smd", "abs_smd_unmatched", "block"])), A, Vv


def gate():
    with Pool(8) as p:
        g1 = p.map(gate1_trial, TRIALS)
        g2 = p.map(gate2_trial, TRIALS)
    r1 = [o for o, _, _ in g1]
    r2 = [o for o, _, _ in g2]

    def ok_tab(t):
        return t["same_rows"] and t["max_abs_diff"] == 0 and t["nan_equal"] and t["text_equal"]

    ok1 = all(o["panel_same_features"] and o.get("panel_same_rows") and o.get("panel_max_abs_diff") == 0 and o["levels_fn_equal_trialdata"]
              and ok_tab(o["arms"]) and ok_tab(o["vars"]) for o in r1)
    ok2 = all(ok_tab(o["arms"]) and ok_tab(o["vars"]) for o in r2)
    res = dict(gate1="PASS" if ok1 else "FAIL", gate2="PASS" if ok2 else "FAIL", gate1_trials=r1, gate2_trials=r2,
               gate1_max_abs_diff=max([max(o["arms"]["max_abs_diff"], o["vars"]["max_abs_diff"]) for o in r1 if "arms" in o] or [np.inf]),
               gate2_max_abs_diff=max(max(o["arms"]["max_abs_diff"], o["vars"]["max_abs_diff"]) for o in r2))
    json.dump(res, open(OUT / "gate" / "gate.json", "w"), indent=1, default=float)
    status(f"step 0 gate 1 (orig-window rebuild: panel, levels, demo + hdPS200 base/ECG/permECG cells == v20, 2 populations) "
           f"{res['gate1']} (max |diff| {res['gate1_max_abs_diff']}); gate 2 (cvd5 x 6 arms x 2 populations through the new "
           f"code path == results_prior) {res['gate2']} (max |diff| {res['gate2_max_abs_diff']})")
    print(json.dumps({kk: v for kk, v in res.items() if not kk.endswith("_trials")}, default=float))
    return ok1 and ok2


# ------------------------------------------------------------------ Step 2
BASES_NEW = ["hdps_prior", "demo", "hdPS200"]


def analyze_trial(k):
    A, Vv = run_cells(k, BASES_NEW, list(ARMS), pops=("all",))
    (OUT / "results").mkdir(parents=True, exist_ok=True)
    A.to_csv(OUT / "results" / f"{k}_arms.csv", index=False)
    Vv.to_csv(OUT / "results" / f"{k}_vars.csv", index=False)
    # candidate levels and no-input shares (aggregate)
    X_ = Ctx(k, clmbr=False)
    D = X_.D
    info = dict(trial=k, n=len(D.t))
    for w, L in X_.lvl.items():
        none = int((L.to_numpy().sum(1) == 0).sum())
        info[f"levels_{w}"] = int(L.shape[1])
        info[f"no_level_input_{w}"] = none
    sp = X_.dxp.sum(1) == 0
    info["no_input_prior_incl_flags"] = int(((X_.lvl["prior"].to_numpy().sum(1) == 0) & sp).sum())
    _, top = hd(X_.lvl["prior"], D.t, np.arange(len(D.t)))
    info["top200_prior_by_domain"] = pd.Series([c.split("_")[0] for c in top]).value_counts().to_dict()
    _, top0 = hd(X_.lvl["orig"], D.t, np.arange(len(D.t)))
    info["top200_orig_by_domain"] = pd.Series([c.split("_")[0] for c in top0]).value_counts().to_dict()
    info["top200_overlap_orig_prior"] = len(set(top) & set(top0))
    print(k, "analysed", flush=True)
    return info


def analyze():
    assert json.load(open(OUT / "gate" / "gate.json"))["gate1"] == "PASS", "gate 1 has not passed"
    assert json.load(open(OUT / "gate" / "gate.json"))["gate2"] == "PASS", "gate 2 has not passed"
    with Pool(8) as p:
        info = p.map(analyze_trial, TRIALS)
    json.dump(info, open(OUT / "results" / "restricted_inputs_info.json", "w"), indent=1, default=int)
    # the existing hdPS200 base / ECG / permECG cells must reproduce v20 (pop all)
    d = []
    for k in TRIALS:
        A = pd.read_csv(OUT / "results" / f"{k}_arms.csv")
        R = pd.read_csv(V20 / f"{k}_arms.csv")
        R = R[(R.base.isin(["hdPS200", "demo"])) & (R["pop"] == "all")].set_index(["base", "arm"])
        a = A.set_index(["base", "arm"]).loc[R.index]
        d.append(float((a[["n_pairs", "pct_bal", "mean_smd", "loghr", "se"]] - R[["n_pairs", "pct_bal", "mean_smd", "loghr", "se"]]).abs().max().max()))
    status(f"step 2 cells written (8 trials x 3 bases x 6 arms, all analysed patients); v20 demo / hdPS200 base, ECG, permECG "
           f"cells reproduced (max |diff| {max(d)})")
    return max(d) == 0


# ------------------------------------------------------------------ Step 3: mask check (|rho|)
def rho_trial(k):
    X_ = Ctx(k, clmbr=False)
    D = X_.D
    V, cols, blk, _, _ = M.panel_for(D, k, "demo")
    allr = np.arange(len(D.t))
    ins = {}
    Hp, topp = hd(X_.lvl["prior"], D.t, allr)
    names_dx = [c for c in pd.read_parquet(OUT / "panels" / f"restricted_{k}_prior_dx.parquet").columns if c != "pid"]
    ins["hdps_prior"] = (np.hstack([X_.dxp, Hp]), names_dx + topp)
    Ho, topo = D.hd()
    assert D.Gm["dx"].shape[1] == len(D.groups["dx"]), "dx block carries missing indicators: names would misalign"
    ins["hdPS200"] = (np.hstack([D.Gm["dx"], Ho]), list(D.groups["dx"]) + topo)
    out = []
    for base, (X, names) in ins.items():
        for j, (c, b) in enumerate(zip(cols, blk)):
            y = V[:, j]
            ok = np.isfinite(y)
            Xo, yo = X[ok], y[ok]
            sx, sy = Xo.std(0), yo.std()
            with np.errstate(invalid="ignore", divide="ignore"):
                r = ((Xo - Xo.mean(0)) * (yo - yo.mean())[:, None]).mean(0) / (sx * sy)
            r = np.where(sx > 0, r, np.nan)
            for nm, rv in zip(names, r):
                if np.isfinite(rv):
                    out.append(dict(trial=k, base=base, item=c, block=b, input=nm, rho=float(rv), n_obs=int(ok.sum())))
    return pd.DataFrame(out)


def rho():
    with Pool(8) as p:
        R = pd.concat(p.map(rho_trial, TRIALS), ignore_index=True)
    R["arho"] = R.rho.abs()
    # pooled = observation-weighted mean of the per-trial rho for the same (item, input name)
    R["w"] = R.n_obs * R.rho
    G = R.groupby(["base", "item", "block", "input"]).agg(w=("w", "sum"), n=("n_obs", "sum"), k=("trial", "nunique"),
                                                           max_trial=("arho", "max")).reset_index()
    G["pooled"] = (G.w / G.n).abs()
    S = []
    for (base, item, block), g in G.groupby(["base", "item", "block"]):
        top = g.sort_values("pooled", ascending=False).iloc[0]
        S.append(dict(base=base, item=item, block=block, max_pooled_abs_rho=round(float(top.pooled), 3), input_at_max=top.input,
                      max_per_trial_abs_rho=round(float(g.max_trial.max()), 3),
                      input_at_max_per_trial=g.sort_values("max_trial", ascending=False).iloc[0].input))
    S = pd.DataFrame(S)
    (OUT / "rho").mkdir(parents=True, exist_ok=True)
    S.to_csv(OUT / "rho" / "rho_by_item.csv", index=False)
    flag = S[S.max_pooled_abs_rho >= 0.80]
    soft = S[(S.max_pooled_abs_rho >= 0.50) & (S.max_pooled_abs_rho < 0.80)]
    res = dict(n_items=int(S.item.nunique()), masked_ge_080=flag[["base", "item", "block", "max_pooled_abs_rho", "input_at_max"]].to_dict("records"),
               soft_050_080=soft[["base", "item", "block", "max_pooled_abs_rho", "input_at_max"]].to_dict("records"),
               max_pooled_by_base_excl_D={b: float(g[g.block != "D"].max_pooled_abs_rho.max()) for b, g in S.groupby("base")},
               max_per_trial_by_base_excl_D={b: float(g[g.block != "D"].max_per_trial_abs_rho.max()) for b, g in S.groupby("base")})
    json.dump(res, open(OUT / "rho" / "rho_summary.json", "w"), indent=1)
    status(f"step 3 mask check: items with pooled |rho| >= 0.80 vs a PS input: {len(flag)} "
           f"({', '.join(sorted(set(flag.item))) or 'none'}); soft proxies 0.50-0.80: {len(soft)}; max pooled |rho| outside block D "
           f"{res['max_pooled_by_base_excl_D']}")
    print(json.dumps(res, indent=1))
    return res


# ------------------------------------------------------------------ Step 3: summary
LBL = {"cvd5": "PS-CVD5", "hdps_prior": "hdPS-prior", "demo": "PS-Demo", "hdPS200": "hdPS200 (v20)"}
ALBL = {"base": "", "ECG": " + AI-ECG", "CLMBR": " + AI-EHR", "ECG+CLMBR": " + AI-ECG + AI-EHR", "permECG": " + permuted AI-ECG",
        "permCLMBR": " + permuted AI-EHR"}


def name(c):
    return LBL[c[0]] + ALBL[c[1]]


def load():
    A = pd.concat([pd.read_csv(OUT / "results" / f"{k}_arms.csv") for k in TRIALS] +
                  [pd.read_csv(PRIOR_RES / f"{k}_arms.csv").query("base == 'cvd5' and pop == 'all'") for k in TRIALS], ignore_index=True)
    V = pd.concat([pd.read_csv(OUT / "results" / f"{k}_vars.csv") for k in TRIALS] +
                  [pd.read_csv(PRIOR_RES / f"{k}_vars.csv").query("base == 'cvd5' and pop == 'all'") for k in TRIALS], ignore_index=True)
    A = A[A["pop"] == "all"].copy()
    V = V[V["pop"] == "all"].copy()
    A["failed"] = A.n_pairs < 11
    A["overlap_ok"] = (A.retention >= 0.30) | (A.n_pairs >= 50)
    return A, V


def items(V, panel, a=None, b=None):
    """22 = block D excluded for every cell (main); 26 = all items (only for cells without AI-EHR); 'masked' =
    the existing rule (D dropped when an AI-EHR arm is in either cell)."""
    if panel == 22:
        return V[V.block != "D"]
    if panel == 26:
        return V
    return SM.mask_items(V, a[1], b[1])


def contrast2(A, V, trials, ca, cb, sided, panel=22, drop_invalid=False, drop_extreme=False):
    """mimic_clmbr_summary.contrast for cells (base, arm) that may differ in base. drop_extreme: trials where either
    cell has > 10% of PS values outside [0.01, 0.99] (near-separation) are dropped."""
    S = A[A.trial.isin(trials)].set_index(["trial", "base", "arm"])
    W = items(V[V.trial.isin(trials)], panel, ca, cb)
    rows = []
    for t in trials:
        if (t, *ca) not in S.index or (t, *cb) not in S.index:
            continue
        xa, xb = S.loc[(t, *ca)], S.loc[(t, *cb)]
        if xa.failed or xb.failed or (drop_invalid and not (xa.overlap_ok and xb.overlap_ok)):
            continue
        if drop_extreme and max(xa.share_extreme_ps, xb.share_extreme_ps) > 0.10:
            continue
        va = W[(W.trial == t) & (W.base == ca[0]) & (W.arm == ca[1])].set_index("var").abs_smd
        vb = W[(W.trial == t) & (W.base == cb[0]) & (W.arm == cb[1])].set_index("var").abs_smd.reindex(va.index)
        ok = va.notna() & vb.notna()
        rows.append(dict(trial=t, m_a=va[ok].mean(), m_b=vb[ok].mean(), p_a=100 * (va[ok] < 0.1).mean(), p_b=100 * (vb[ok] < 0.1).mean(),
                         n_items=int(ok.sum()), e_a=abs(xa.loghr - xa.rct_loghr), e_b=abs(xb.loghr - xb.rct_loghr),
                         la=xa.loghr, lb=xb.loghr, rb=xa.rct_loghr))
    R = pd.DataFrame(rows)
    if len(R) < 2:
        return dict(a=name(ca), b=name(cb), k=len(R), items="", m_a=np.nan, m_b=np.nan, relred=np.nan, lo=np.nan, hi=np.nan, lower="",
                    p=np.nan, sided=sided, pct_a=np.nan, pct_b=np.nan, dpts=np.nan, better_pts="", p_pts=np.nan, absd_a=np.nan,
                    absd_b=np.nan, closer="", p_closer=np.nan, p_bshuf=np.nan)
    est, lo, hi = relred_ci(R.m_b, R.m_a)
    d = (R.m_b - R.m_a).to_numpy()
    dp = (R.p_a - R.p_b).to_numpy()
    de = (R.e_b - R.e_a).dropna()
    g = R.dropna(subset=["la", "lb"])
    return dict(a=name(ca), b=name(cb), k=len(R), items=f"{int(R.n_items.min())}-{int(R.n_items.max())}", m_a=float(R.m_a.mean()),
                m_b=float(R.m_b.mean()), relred=est, lo=lo, hi=hi, lower=f"{int((d > 0).sum())}/{len(d)}", p=SM.signflip(d, sided),
                sided=sided, pct_a=float(R.p_a.mean()), pct_b=float(R.p_b.mean()), dpts=float(dp.mean()),
                better_pts=f"{int((dp > 0).sum())}/{len(dp)}", p_pts=SM.signflip(dp, sided),
                absd_a=float(g.e_a.mean()), absd_b=float(g.e_b.mean()), closer=f"{int((de > 0).sum())}/{len(de)}",
                p_closer=SM.signflip(de.to_numpy(), sided),
                p_bshuf=SM.bshuf(g.la.to_numpy(), g.lb.to_numpy(), g.rb.to_numpy()) if len(g) > 2 else np.nan)


def arm_metrics(A, V, trials, c, panel):
    S = A[A.trial.isin(trials) & (A.base == c[0]) & (A.arm == c[1]) & ~A.failed]
    W = items(V[V.trial.isin(trials) & (V.base == c[0]) & (V.arm == c[1])], panel)
    W = W[W.trial.isin(S.trial)]
    per = W.dropna(subset=["abs_smd"]).groupby("trial")
    out = dict(k=int(S.trial.nunique()), mean_smd=float(per.abs_smd.mean().mean()), pct_lt01=float(per.abs_smd.apply(lambda x: 100 * (x < 0.1).mean()).mean()))
    for b in ("A", "B", "C", "D"):
        x = W[(W.block == b)].dropna(subset=["abs_smd"]).groupby("trial").abs_smd.mean()
        out[f"mean_smd_{b}"] = float(x.mean()) if len(x) else None
    s = S[np.isfinite(S.loghr)]
    out["mean_abs_dloghr"] = float(np.mean(np.abs(s.loghr - s.rct_loghr)))
    out["r"] = float(np.corrcoef(s.loghr, s.rct_loghr)[0, 1]) if len(s) > 2 else None
    out["est_agree"] = f"{int((np.abs(s.loghr - s.rct_loghr) <= 1.96 * s.rct_se).sum())}/{len(s)}"
    out["std_agree"] = f"{int((np.abs(s.loghr - s.rct_loghr) / np.sqrt(s.se ** 2 + s.rct_se ** 2) < 1.96).sum())}/{len(s)}"
    return out


def unmatched_metrics(V, trials, panel):
    W = items(V[V.trial.isin(trials) & (V.base == "cvd5") & (V.arm == "base")], panel).dropna(subset=["abs_smd_unmatched"])
    per = W.groupby("trial").abs_smd_unmatched
    out = dict(k=int(W.trial.nunique()), mean_smd=float(per.mean().mean()), pct_lt01=float(per.apply(lambda x: 100 * (x < 0.1).mean()).mean()))
    for b in ("A", "B", "C", "D"):
        x = W[W.block == b].groupby("trial").abs_smd_unmatched.mean()
        out[f"mean_smd_{b}"] = float(x.mean()) if len(x) else None
    return out


def contrast_list():
    H, C5, DM, H2 = "hdps_prior", "cvd5", "demo", "hdPS200"
    L = [("hdPS-prior vs PS-CVD5", (H, "base"), (C5, "base"), "two")]
    for base in (H, DM, H2):
        for arm in ("ECG", "CLMBR", "ECG+CLMBR"):
            L.append((f"{name((base, arm))} vs {name((base, 'base'))}", (base, arm), (base, "base"), "one"))
        L += [(f"{name((base, 'ECG'))} vs {name((base, 'permECG'))}", (base, "ECG"), (base, "permECG"), "one"),
              (f"{name((base, 'CLMBR'))} vs {name((base, 'permCLMBR'))}", (base, "CLMBR"), (base, "permCLMBR"), "one"),
              (f"{name((base, 'permECG'))} vs {name((base, 'base'))}", (base, "permECG"), (base, "base"), "two"),
              (f"{name((base, 'permCLMBR'))} vs {name((base, 'base'))}", (base, "permCLMBR"), (base, "base"), "two"),
              (f"{name((base, 'ECG+CLMBR'))} vs {name((base, 'CLMBR'))}", (base, "ECG+CLMBR"), (base, "CLMBR"), "one"),
              (f"{name((base, 'ECG+CLMBR'))} vs {name((base, 'ECG'))}", (base, "ECG+CLMBR"), (base, "ECG"), "one"),
              (f"{name((base, 'CLMBR'))} vs {name((base, 'ECG'))}", (base, "CLMBR"), (base, "ECG"), "two")]
    for ref in (H, H2):  # slide 9 panel D analog: Demo + AI and PS-CVD5 + AI vs the conventional hdPS
        for base in (DM, C5):
            for arm in ("base", "ECG", "CLMBR", "ECG+CLMBR"):
                L.append((f"{name((base, arm))} vs {name((ref, 'base'))}", (base, arm), (ref, "base"), "two"))
    L += [("hdPS200 (v20) vs PS-CVD5", (H2, "base"), (C5, "base"), "two"),
          ("hdPS-prior vs hdPS200 (v20)", (H, "base"), (H2, "base"), "two")]
    for arm in ("ECG", "CLMBR", "ECG+CLMBR"):  # PS-CVD5 + AI within base, recomputed on 22 items
        L.append((f"{name((C5, arm))} vs PS-CVD5", (C5, arm), (C5, "base"), "one"))
    return L


def validity(A):
    out = {}
    for base, g in A.groupby("base"):
        out[base] = dict(cells=len(g), failed_lt11_pairs=int(g.failed.sum()), overlap_invalid=int((~g.overlap_ok).sum()),
                         cells_extreme_ps_over_10pct=int((g.share_extreme_ps > 0.10).sum()),
                         trials_with_a_cell_extreme_ps_over_10pct=int(g[g.share_extreme_ps > 0.10].trial.nunique()),
                         primary7_trials_with_a_cell_extreme_ps_over_10pct=int(g[(g.share_extreme_ps > 0.10) & g.trial.isin(P7)].trial.nunique()),
                         cells_c_over_0_90=int((g.c_insample > 0.90).sum()),
                         retention_bands={arm: dict(lt30=int((h.retention < .3).sum()), r30_50=int(((h.retention >= .3) & (h.retention < .5)).sum()),
                                                    r50_90=int(((h.retention >= .5) & (h.retention < .9)).sum()), ge90=int((h.retention >= .9).sum()))
                                          for arm, h in g.groupby("arm")},
                         median_c_insample={arm: round(float(h.c_insample.median()), 3) for arm, h in g.groupby("arm")},
                         max_share_extreme_ps={arm: round(float(h.share_extreme_ps.max()), 3) for arm, h in g.groupby("arm")},
                         n_inputs_range={arm: [int(h.n_inputs.min()), int(h.n_inputs.max())] for arm, h in g.groupby("arm")})
    return out


def peptic(A, V, panel):
    out = {}
    for (base, arm), r in A[A.trial == "peptic"].set_index(["base", "arm"]).iterrows():
        if panel == 26 and arm in CLM:
            continue
        v = items(V[(V.trial == "peptic") & (V.base == base) & (V.arm == arm)], panel).abs_smd.dropna()
        out[name((base, arm))] = dict(hr=float(np.exp(r.loghr)), lo=float(np.exp(r.loghr - 1.96 * r.se)), hi=float(np.exp(r.loghr + 1.96 * r.se)),
                                      pct_lt01=float(100 * (v < 0.1).mean()), mean_smd=float(v.mean()), failed=bool(r.failed))
    v = items(V[(V.trial == "peptic") & (V.base == "cvd5") & (V.arm == "base")], panel).abs_smd_unmatched.dropna()
    out["Unmatched"] = dict(mean_smd=float(v.mean()), pct_lt01=float(100 * (v < 0.1).mean()))
    return out


def summarize():
    A, V = load()
    cells = [(b, a) for b in ("cvd5", "hdps_prior", "demo", "hdPS200") for a in ARMS]
    S = dict(arms={}, contrasts={}, peptic={}, validity=validity(A), gates={}, inputs={}, leakage={}, rho={})
    for setname, tr in (("primary7", P7), ("all8", TRIALS)):
        for panel in (22, 26):
            S["arms"][f"{setname}|{panel}|Unmatched"] = unmatched_metrics(V, tr, panel)
            for c in cells:
                if panel == 26 and c[1] in CLM:
                    continue
                S["arms"][f"{setname}|{panel}|{name(c)}"] = arm_metrics(A, V, tr, c, panel)
        for lab, ca, cb, sided in contrast_list():
            S["contrasts"][f"{setname}|22|{lab}"] = contrast2(A, V, tr, ca, cb, sided, 22)
            if not ({ca[1], cb[1]} & CLM):
                S["contrasts"][f"{setname}|26|{lab}"] = contrast2(A, V, tr, ca, cb, sided, 26)
    for lab, ca, cb, sided in contrast_list():  # sensitivity: overlap-invalid cells dropped
        S["contrasts"][f"primary7|22|{lab}|overlap_valid_only"] = contrast2(A, V, P7, ca, cb, sided, 22, drop_invalid=True)
        S["contrasts"][f"primary7|22|{lab}|no_near_separation"] = contrast2(A, V, P7, ca, cb, sided, 22, drop_extreme=True)
    S["peptic"] = {"22": peptic(A, V, 22), "26": peptic(A, V, 26)}
    # gates: the existing within-cvd5 contrasts recomputed with contrast2 under the existing mask rule == summary_prior
    ref = json.load(open(CL / "summary_prior" / "summary.json"))["contrasts"]
    gd = []
    for lab, a, b, sided in SM.CONTRASTS:
        c = contrast2(A, V, P7, ("cvd5", a), ("cvd5", b), sided, panel="masked")
        r = ref[f"primary7|cvd5|all|{lab}"]
        gd.append(max(abs(c[x] - r[x]) for x in ("relred", "lo", "hi", "p", "pct_a", "pct_b", "absd_a", "absd_b", "p_bshuf")))
    S["gates"]["contrast2_equals_summary_prior"] = dict(n=len(gd), max_abs_diff=float(max(gd)), ok=bool(max(gd) < 1e-12))
    S["gates"]["step0"] = {k: v for k, v in json.load(open(OUT / "gate" / "gate.json")).items() if not k.endswith("_trials")}
    info = json.load(open(OUT / "results" / "restricted_inputs_info.json"))
    pan = json.load(open(OUT / "panels" / "panels.json"))
    n_all = sum(i["n"] for i in info)
    S["inputs"] = dict(
        levels_prior=dict(median=float(np.median([i["levels_prior"] for i in info])), range=[min(i["levels_prior"] for i in info), max(i["levels_prior"] for i in info)]),
        levels_orig=dict(median=float(np.median([i["levels_orig"] for i in info])), range=[min(i["levels_orig"] for i in info), max(i["levels_orig"] for i in info)]),
        levels_by_trial={i["trial"]: dict(prior=i["levels_prior"], orig=i["levels_orig"]) for i in info},
        pct_no_level_input_prior=pct_sup(sum(i["no_level_input_prior"] for i in info), n_all),
        pct_no_level_input_orig=pct_sup(sum(i["no_level_input_orig"] for i in info), n_all),
        pct_no_input_prior_incl_flags=pct_sup(sum(i["no_input_prior_incl_flags"] for i in info), n_all),
        pct_no_level_input_prior_by_trial={i["trial"]: pct_sup(i["no_level_input_prior"], i["n"]) for i in info},
        top200_prior_by_domain={i["trial"]: i["top200_prior_by_domain"] for i in info},
        top200_orig_by_domain={i["trial"]: i["top200_orig_by_domain"] for i in info},
        top200_overlap_orig_prior={i["trial"]: i["top200_overlap_orig_prior"] for i in info}, n_analysed=n_all)
    S["leakage"] = pan["leakage_summary"]
    S["rho"] = json.load(open(OUT / "rho" / "rho_summary.json"))
    (OUT / "summary").mkdir(parents=True, exist_ok=True)
    json.dump(S, open(OUT / "summary" / "summary.json", "w"), indent=1, default=float)
    write_tables(S)
    c = S["contrasts"]
    status("step 3 summary written; contrast2 gate " + ("PASS" if S["gates"]["contrast2_equals_summary_prior"]["ok"] else "FAIL") +
           "; primary7, 22 items: " + "; ".join(f"{lab} {c[f'primary7|22|{lab}']['relred']:.1f}% ({c[f'primary7|22|{lab}']['lo']:.1f} to {c[f'primary7|22|{lab}']['hi']:.1f})"
                                                for lab in ("hdPS-prior vs PS-CVD5", "hdPS-prior + AI-ECG vs hdPS-prior", "hdPS-prior + AI-EHR vs hdPS-prior",
                                                            "hdPS-prior + AI-ECG + AI-EHR vs hdPS-prior")))
    return S["gates"]["contrast2_equals_summary_prior"]["ok"]


def f1(x, d=1):
    return "—" if x is None or not np.isfinite(x) else f"{x:.{d}f}"


def write_tables(S):
    fp = SM.fp
    L = ["# MIMIC-IV hdPS on the AI-EHR input window: generated tables (aggregates only)", "",
         "Cells: all analysed patients, 1:1 greedy NN on the PS logit (caliper 0.2 SD, no replacement), fixed C = 1. "
         "22 items = block D (utilisation) excluded for every arm (main); 26 = all items (arms without AI-EHR only).", "",
         "## Per arm", "", "| Set | Items | Arm | k | mean \\|SMD\\| | % \\|SMD\\| < 0.1 | A | B | C | D | mean \\|Δ log HR\\| | r | est. agree | std-diff agree |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, g in S["arms"].items():
        s, panel, arm = key.split("|")
        L.append(f"| {s} | {panel} | {arm} | {g['k']} | {g['mean_smd']:.3f} | {g['pct_lt01']:.1f} | " +
                 " | ".join(f1(g.get(f'mean_smd_{b}'), 3) for b in "ABCD") +
                 (f" | {g['mean_abs_dloghr']:.3f} | {f1(g['r'], 2)} | {g['est_agree']} | {g['std_agree']} |" if "mean_abs_dloghr" in g else " | | | | |"))
    L += ["", "## Contrasts (relative reduction in mean |SMD| of a vs b; items observed in both cells)", "",
          "| Set | Items | Contrast | k | mean \\|SMD\\| b → a | rel. red. % (95% CI) | lower | P | % <0.1 b → a | \\|Δ log HR\\| b → a | closer (P) | bench.-perm. P |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, c in S["contrasts"].items():
        parts = key.split("|")
        lab = parts[2] + (f" [{parts[3]}]" if len(parts) > 3 else "")
        L.append(f"| {parts[0]} | {parts[1]} | {lab} | {c['k']} | {c['m_b']:.3f} → {c['m_a']:.3f} | {f1(c['relred'])} ({f1(c['lo'])} to {f1(c['hi'])}) | "
                 f"{c['lower']} | {fp(c['p'])} ({c['sided']}) | {c['pct_b']:.1f} → {c['pct_a']:.1f} | {c['absd_b']:.3f} → {c['absd_a']:.3f} | "
                 f"{c['closer']} ({fp(c['p_closer'])}) | {fp(c['p_bshuf'])} |")
    L += ["", "## PEPTIC (negative control; RCT RR 1.05)", "", "| Items | Arm | HR (95% CI) | % \\|SMD\\| < 0.1 | mean \\|SMD\\| |", "|---|---|---|---|---|"]
    for panel, P in S["peptic"].items():
        for arm, g in P.items():
            hr = f"{g['hr']:.2f} ({g['lo']:.2f}–{g['hi']:.2f})" if "hr" in g else "—"
            L.append(f"| {panel} | {arm} | {hr} | {g['pct_lt01']:.1f} | {g['mean_smd']:.3f} |")
    for sec in ("validity", "inputs", "leakage", "rho", "gates"):
        L += ["", f"## {sec}", "", "```", json.dumps(S[sec], indent=1, default=float), "```"]
    (OUT / "summary" / "tables.md").write_text("\n".join(L) + "\n")


# ------------------------------------------------------------------ panels (driver)
def panels():
    with Pool(4) as p:
        res = p.map(panels_trial, TRIALS)
    # aggregate leakage summary over the 8 trials (analysed patients)
    LS = {}
    for w in ("orig", "prior"):
        tot = sum(r[w]["leakage"]["events_total"] for r in res)
        agg = {d: {kk: sum(r[w]["leakage"][d][kk] for r in res) for kk in res[0][w]["leakage"][d]} for d in ("dx", "rx", "px", "lab")}
        npat = sum(r[w]["leakage"]["patients_with_any_event"] for r in res)
        LS[w] = dict(events_total=tot,
                     events_at_or_after_cut=sum(agg[d]["at_or_after_cut"] for d in agg),
                     events_at_or_after_admit=sum(agg[d]["at_or_after_admit"] for d in agg),
                     events_at_or_after_t0=sum(agg[d]["at_or_after_t0"] for d in agg),
                     dxpx_index_hadm=agg["dx"]["index_hadm"] + agg["px"]["index_hadm"],
                     dxpx_from_index_or_later_admission=sum(r[w]["leakage"]["dxpx_from_index_or_later_admission"] for r in res),
                     share_events_index_episode=round(100 * sum(agg[d]["index_episode"] for d in agg) / tot, 2),
                     share_events_index_episode_by_domain={d: round(100 * agg[d]["index_episode"] / agg[d]["n"], 2) if agg[d]["n"] else None for d in agg},
                     share_events_index_hadm_by_domain={d: round(100 * agg[d]["index_hadm"] / agg[d]["n"], 2) if agg[d]["n"] else None for d in agg},
                     events_by_domain={d: agg[d]["n"] for d in agg},
                     pct_patients_any_index_episode_event=pct_sup(sum(r[w]["leakage"]["patients_any_index_episode_event"] for r in res), npat),
                     pct_patients_only_index_episode_events=pct_sup(sum(r[w]["leakage"]["patients_only_index_episode_events"] for r in res), npat),
                     patients_with_any_event=npat,
                     exposure_features=sum(len(r[w]["leakage"]["expo_features"]) for r in res),
                     n_features_by_trial={r["trial"]: r[w]["n_features"] for r in res})
    LS["prior_dx_flags_discordant_with_baseline"] = {r["trial"]: r["prior_dx_discordant_cols"] for r in res}
    json.dump(dict(trials=res, leakage_summary=LS), open(OUT / "panels" / "panels.json", "w"), indent=1, default=int)
    p = LS["prior"]
    ok = (p["events_at_or_after_cut"] == 0 and p["events_at_or_after_admit"] == 0 and p["events_at_or_after_t0"] == 0 and p["dxpx_index_hadm"] == 0
          and p["dxpx_from_index_or_later_admission"] == 0 and p["exposure_features"] == 0)
    status(f"step 1 panels rebuilt (orig, prior) for 8 trials; prior-window leakage checks {'PASS' if ok else 'FAIL'}: events at/after the "
           f"index admission time {p['events_at_or_after_admit']}, at/after t0 {p['events_at_or_after_t0']}, index-admission dx/px "
           f"{p['dxpx_index_hadm']}, exposure features {p['exposure_features']}; index-episode (index hadm or ED stay before admission) "
           f"share of input events {p['share_events_index_episode']}%; prior dx flags discordant with baseline: "
           f"{ {k: v for k, v in LS['prior_dx_flags_discordant_with_baseline'].items() if v} }")
    print(json.dumps(LS, indent=1, default=int))
    return ok


STEPS = dict(panels=panels, gate=gate, analyze=analyze, rho=lambda: rho() is not None, summarize=summarize)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == "all":
        for s in ("panels", "gate", "analyze", "rho", "summarize"):
            if not STEPS[s]():
                print(f"stopped at {s}")
                sys.exit(1)
        sys.exit(0)
    sys.exit(0 if STEPS[cmd]() else 1)
