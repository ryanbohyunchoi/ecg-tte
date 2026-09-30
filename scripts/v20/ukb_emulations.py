#!/usr/bin/env python
"""v2.0 UKB covariate balance and trial emulation (exploratory; docs/v20/UKB_ANALYSIS_PLAN.md amendment 2).

Trials: ONTARGET, ASCOT, ALLHAT, LIFE, VALUE (hypertension gate, no prior HF) and CAPRIE (prior CAD/stroke/PAD).
Designs:
  d2  primary: new use since baseline = exactly one arm class at the imaging visit (i2) and neither arm class at
      i0 or i1 (if attended); time zero = i2 date.
  d1  secondary: prevalent use at i2 (the v1.5 design; reproduces claude-v15-ukb-* for ontarget/ascot/allhat).
The ECG (20205 instance 2, BCL embedding) is recorded at time zero, i.e. on treatment in both designs.
Cohort, baseline and outcome construction reuse scripts/v15/v15_ukb_build.py (outcomes() and link_ecg() are called
unchanged with MODE['dir_fmt'] pointing into this analysis's audit folder); LIFE, VALUE and CAPRIE are added to
the comparison table at run time.

Usage: ukb_emulations.py build d1|d2 | gate | analyze | report
Outputs (umask 077): /mnt/raid0/rbc58/ecg-tte/audits/claude-v20-ukb-analysis/trials/<design>_<trial>/ (restricted
trial directories) and emu_*.csv aggregates in the parent folder.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import itertools  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import duckdb  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v15"))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import v15_ukb_build as UB  # noqa: E402
import v15_ukb_common as UC  # noqa: E402
import trial_specs as ts  # noqa: E402
from eval_longtail_balance import pcs  # noqa: E402
from v13_common import cox, match, ps_logit  # noqa: E402

AUD = Path(UC.AUDIT)
OUT = AUD / "claude-v20-ukb-analysis"
TR = OUT / "trials"
V15 = {t: AUD / f"claude-v15-ukb-{t}" for t in ("ontarget", "ascot", "allhat")}
TRIALS = ["ontarget", "ascot", "allhat", "life", "value", "caprie"]
EXTRA = {
    "life": dict(comparison="arb_vs_betablocker", arms=("arb", "beta_blocker"), A=["arb"], B=["bb_trial"],
                 excl_both=["bb_other_systemic"], gate="htn", excl_dx=["I50"], outcome=["death", "mi", "stroke"],
                 horizon_months=58, rct_key="life", secondary=[]),
    "value": dict(comparison="arb_vs_amlodipine", arms=("arb", "amlodipine"), A=["arb"], B=["amlodipine"],
                  excl_both=["dhp_ccb_other"], gate="htn", excl_dx=["I50"], outcome=["death", "mi", "hf"],
                  horizon_months=50, rct_key="value", secondary=[]),
    "caprie": dict(comparison="clopidogrel_vs_aspirin", arms=("clopidogrel", "aspirin"), A=["p2y12"], B=["aspirin"],
                   excl_both=["dipyridamole"], gate="cvd", excl_dx=[], outcome=["death", "mi", "isch_stroke"],
                   horizon_months=23, rct_key="caprie", secondary=[]),
}
UC.COMPARISONS.update(EXTRA)          # same dict object as UB.COMPARISONS
UC.OUT_CODES["isch_stroke"] = ["I63", "I64"]
RCT = {  # published benchmarks in our orientation (intervention vs comparator)
    "ontarget": dict(ts.PUBLISHED["ontarget"]), "ascot": dict(ts.PUBLISHED["ascot"]), "allhat": dict(ts.PUBLISHED["allhat"]),
    "life": dict(ts.PUBLISHED["life"]), "value": dict(ts.PUBLISHED["value"]),
    "caprie": dict(hr=0.913, ci=(0.835, 0.997), measure="RR (RRR 8.7%, 95% CI 0.3-16.5)", our_orientation=0.913,
                   endpoint="ischaemic stroke, MI or vascular death", rct_arms="clopidogrel vs aspirin",
                   source="CAPRIE Steering Committee, Lancet 1996")}
ENDPOINT = {"ontarget": "death (for CV death), MI, stroke or HF", "ascot": "death (for CHD death) or MI",
            "allhat": "death (for CHD death) or MI", "life": "death (for CV death), MI or stroke",
            "value": "death (for cardiac death), MI or HF", "caprie": "death (for vascular death), MI or ischaemic stroke"}
CVD_GATE = ["I20", "I21", "I22", "I23", "I24", "I25", "I63", "I64", "G45", "I70", "I739"]
MIN_CELL = 11
PANEL_A = ["sbp_i0", "bmi_i0", "current_smoker_i0", "ever_smoker_i0", "cholesterol_i0", "ldl_i0", "hdl_i0", "creatinine_i0", "hba1c_i0"]
CMR_VARS = ["lvef", "lvedvi", "lvesvi", "lvsvi", "lv_ci", "lvmi", "rvedvi", "rvef", "lavi_max", "laef", "ravi_max"]


def sup(n):
    n = int(n)
    return "<11" if 1 <= n <= 10 else n


# ---------------------------------------------------------------- build
def i0_panel():
    con = duckdb.connect()
    cols = ["eid", "p4080_i0_a0", "p4080_i0_a1", "p23104_i0", "p1239_i0", "p20160_i0"] + \
           [f"p{f}_i0" for f in (30690, 30700, 30750, 30760, 30780)]
    d = con.execute(f"select {', '.join(cols)} from read_csv_auto('{UC.DATA_CSV}', all_varchar=true, sample_size=-1) "
                    "where p53_i2 is not null").df()
    P = pd.DataFrame({"pid": d.eid.astype(str)})
    P["sbp_i0"] = d[["p4080_i0_a0", "p4080_i0_a1"]].apply(pd.to_numeric, errors="coerce").mean(axis=1)
    P["bmi_i0"] = pd.to_numeric(d.p23104_i0, errors="coerce")
    P["current_smoker_i0"] = d.p1239_i0.map({"No": 0.0, "Yes, on most or all days": 1.0, "Only occasionally": 1.0})
    P["ever_smoker_i0"] = d.p20160_i0.map({"No": 0.0, "Yes": 1.0})
    for f, nm in [(30690, "cholesterol"), (30700, "creatinine"), (30750, "hba1c"), (30760, "hdl"), (30780, "ldl")]:
        P[f"{nm}_i0"] = pd.to_numeric(d[f"p{f}_i0"], errors="coerce")
    return P.set_index("pid")


def write_rct(trial, d):
    spec, pub = UC.COMPARISONS[trial], RCT[trial]
    maxfu = (pd.Timestamp(UC.DATA_END) - pd.Timestamp("2014-04-30")).days
    hd = int(min(round(spec["horizon_months"] * 30.4375), maxfu))
    rct = dict(trial=trial, key=spec["rct_key"], arms=list(spec["arms"]), hr=pub["hr"], lo=pub["ci"][0], hi=pub["ci"][1],
               ci_level=pub.get("ci_level", 0.95), our_orientation=pub["our_orientation"], horizon_days=hd,
               endpoint=ENDPOINT[trial], notes=f"RCT: {pub['rct_arms']} ({pub['measure']}; {pub['endpoint']}; {pub['source']}).")
    if trial == "ontarget":
        q = ts.PUBLISHED["elite_ii"]
        rct["secondary"] = [dict(key="elite_ii", hr=q["hr"], lo=q["ci"][0], hi=q["ci"][1], ci_level=q.get("ci_level", 0.95),
                                 our_orientation=q["our_orientation"], endpoint=q["endpoint"], rct_arms=q["rct_arms"],
                                 horizon_days=int(round(ts.HORIZON_MONTHS["elite_ii"] * 30.4375)), outcome_columns="t_sec_death/e_sec_death")]
    json.dump(rct, open(d / "rct.json", "w"), indent=1)


def build(design):
    os.umask(0o077)
    TR.mkdir(parents=True, exist_ok=True)
    base, dx, meds, chk = UB.load()
    dx["eid"] = dx.eid.astype(str)
    dx["date"] = pd.to_datetime(dx.date)
    b = UB.prep_base(base)
    dx = dx.join(b.index_date, on="eid")
    pre = dx[dx.date < dx.index_date]
    m2, medw = UB.med_classes(meds[2])
    _, w0 = UB.med_classes(meds[0])
    _, w1 = UB.med_classes(meds[1])
    prior_use = pd.concat([w0, w1]).groupby(level=0).max()
    P0 = i0_panel()
    END = pd.Timestamp(UC.DATA_END)
    for trial in TRIALS:
        spec = UC.COMPARISONS[trial]
        d = TR / f"{design}_{trial}"
        d.mkdir(mode=0o700, exist_ok=True)
        for f in d.glob("READY_*"):
            f.unlink()
        n = lambda s: sup(int(s.sum()))
        att = []
        elig = pd.Series(True, index=b.index)
        att.append(("imaging visit (instance 2) attended", n(elig)))
        elig &= b.index_date < END
        att.append((f"index before {END.date()}", n(elig)))
        elig &= ~(b.death_date <= b.index_date)
        att.append(("alive at index", n(elig)))
        inA, inB, inEX = UB.build_arms(trial, spec, b, medw)
        att.append((f"any {spec['arms'][0]} or {spec['arms'][1]} at i2", n(elig & (inA | inB))))
        elig &= inA ^ inB
        att.append(("exactly one arm (users of both removed)", n(elig)))
        elig &= ~inEX
        att.append((f"no {'/'.join(spec['excl_both']) or 'n/a'} use", n(elig)))
        if design == "d2":
            pu = prior_use.reindex(b.index).fillna(0)
            cl = [c for c in spec["A"] + spec["B"] if c in pu]
            prev = pu[cl].sum(axis=1) > 0
            elig &= ~prev
            att.append((f"new use since baseline: neither {'/'.join(spec['A'] + spec['B'])} at i0 or i1", n(elig)))
        if spec["gate"] == "htn":
            htn_icd = pre[pre.code.str.startswith(tuple(UC.HTN_ICD))].eid.unique()
            w = medw.reindex(b.index).fillna(0)
            on_ah = w[[c for c in UC.ANTIHTN_CLASSES if c in w]].sum(axis=1) > 0
            gate = b.index.isin(htn_icd) | (b.htn_selfreport == 1) | on_ah
            att.append(("hypertension gate", n(elig & gate)))
        else:  # cvd: prior CAD / ischaemic stroke / TIA / PAD codes or algorithmic MI / stroke before index
            codes = b.index.isin(pre[pre.code.str.startswith(tuple(CVD_GATE))].eid.unique())
            alg = (b.mi_alg_date < b.index_date) | (b.mi_alg_unknown == 1) | (b.stroke_alg_date < b.index_date) | (b.stroke_alg_unknown == 1)
            gate = codes | alg.to_numpy()
            att.append(("prior CAD/stroke/TIA/PAD gate", n(elig & gate)))
        elig &= gate
        for c in spec["excl_dx"]:
            elig &= ~b.index.isin(pre[pre.code.str.startswith(c)].eid.unique())
            att.append((f"no prior {c}", n(elig)))
        coh = b[elig].copy()
        coh["treated"] = inA[elig].astype(int)
        eA, eB = int(coh.has_ecg[coh.treated == 1].sum()), int(coh.has_ecg[coh.treated == 0].sum())
        summ = dict(trial=trial, design={"d1": "prevalent use at imaging visit (i2)", "d2": "new use since baseline (neither arm class at i0/i1; on one at i2)"}[design],
                    comparison=spec["comparison"], arms=list(spec["arms"]), attrition=att,
                    n_arm=[sup(coh.treated.sum()), sup((1 - coh.treated).sum())], n_arm_with_ecg=[sup(eA), sup(eB)],
                    ecg_timing="ECG at time zero (i2): on treatment" + ("; initiation 4-10 y earlier (between i0 and i2)" if design == "d2" else "; duration of use unknown"))
        write_rct(trial, d)
        if min(eA, eB) == 0:
            json.dump(summ, open(d / "summary.json", "w"), indent=1, default=str)
            continue
        coh.index.name = "pid"
        pd.DataFrame({"pid": coh.index.astype(str), "treated": coh.treated.values,
                      "index_day": ((coh.index_date - pd.Timestamp("1970-01-01")).dt.days).astype(float).values,
                      "index_year": coh.index_year.astype(int).values}).to_parquet(d / "cohort.parquet", index=False)
        bl, roles, miss = UB.baseline(spec, coh, pre, medw)
        bl.to_parquet(d / "baseline.parquet", index=False)
        json.dump(roles, open(d / "roles.json", "w"), indent=1)
        P0.reindex(coh.index.astype(str)).reset_index().rename(columns={"index": "pid"}).to_parquet(d / "heldout_i0.parquet", index=False)
        json.dump(summ, open(d / "summary.json", "w"), indent=1, default=str)
        (d / "READY_COHORT").write_text("ok\n")
        print(design, trial, summ["n_arm_with_ecg"], att[-1], flush=True)
    UB.MODE["dir_fmt"] = f"claude-v20-ukb-analysis/trials/{design}_" + "{trial}"
    UB.outcomes(TRIALS)
    UB.link_ecg(TRIALS)


# ---------------------------------------------------------------- reproduction gate (v1.5 ONTARGET / ASCOT / ALLHAT, d1)
def gate():
    rows = []
    for t, v in V15.items():
        d = TR / f"d1_{t}"
        r = dict(trial=t)
        for f, key in (("cohort.parquet", ["pid", "treated", "index_day"]), ("outcomes.parquet", ["pid", "t", "e"]),
                       ("baseline.parquet", None)):
            a = pd.read_parquet(d / f).assign(pid=lambda x: x.pid.astype(str)).sort_values("pid").reset_index(drop=True)
            o = pd.read_parquet(v / f).assign(pid=lambda x: x.pid.astype(str)).sort_values("pid").reset_index(drop=True)
            cols = key or [c for c in o.columns if c in a.columns]
            same = len(a) == len(o) and a[cols].equals(o[cols]) if key else (len(a) == len(o) and
                   np.allclose(a[cols[1:]].to_numpy(float), o[cols[1:]].to_numpy(float), equal_nan=True) and a.pid.equals(o.pid))
            r[f"{f.split('.')[0]}_identical"] = bool(same)
        ea = pd.read_parquet(d / "ecg_embedding.parquet").pid.astype(str)
        eo = pd.read_parquet(v / "ecg_embedding.parquet").pid.astype(str)
        r["ecg_pids_identical"] = set(ea) == set(eo)
        rows.append(r)
    G = pd.DataFrame(rows)
    G.to_csv(OUT / "emu_gate_build.csv", index=False)
    print(G.to_string(index=False))
    return G


# ---------------------------------------------------------------- analysis
def smd(V, t, idx):
    with np.errstate(invalid="ignore", divide="ignore"):
        sd = np.sqrt((np.nanvar(V[t == 1], 0, ddof=1) + np.nanvar(V[t == 0], 0, ddof=1)) / 2)
        S, ts_ = V[idx], t[idx]
        d = np.abs(np.nanmean(S[ts_ == 1], 0) - np.nanmean(S[ts_ == 0], 0)) / sd
    d[~np.isfinite(sd) | (sd == 0)] = np.nan
    return d


def load_trial(d):
    rd = lambda f: pd.read_parquet(d / f).assign(pid=lambda x: x.pid.astype(str)).drop_duplicates("pid").set_index("pid")
    co, ba, oc, h0 = rd("cohort.parquet"), rd("baseline.parquet"), rd("outcomes.parquet"), rd("heldout_i0.parquet")
    em = rd("ecg_embedding.parquet")
    roles, rct = json.load(open(d / "roles.json")), json.load(open(d / "rct.json"))
    oc = oc[oc.t.notna() & oc.e.notna()]
    pids = co.index.intersection(ba.index).intersection(em.index).intersection(oc.index).sort_values()
    return co, ba, oc, h0, em, roles, rct, pids


ARMS = {"unmatched": None, "demo": ["demo"], "demo+ECG": ["demo", "ECG"], "demo+permECG": ["demo", "permECG"],
        "sparse": ["demo", "dx"], "sparse+ECG": ["demo", "dx", "ECG"],
        "rich": ["demo", "dx", "meds", "util"], "rich+ECG": ["demo", "dx", "meds", "util", "ECG"],
        "rich+permECG": ["demo", "dx", "meds", "util", "permECG"]}
REF = {"demo+ECG": "demo", "demo+permECG": "demo", "sparse+ECG": "sparse", "rich+ECG": "rich", "rich+permECG": "rich"}


def analyze_one(design, trial, cmr):
    d = TR / f"{design}_{trial}"
    if not (d / "READY_OUTCOMES").exists():
        return None
    co, ba, oc, h0, em, roles, rct, pids = load_trial(d)
    t = co.loc[pids, "treated"].astype(int).to_numpy()
    T, E = oc.loc[pids, "t"].to_numpy(float), oc.loc[pids, "e"].astype(int).to_numpy()
    G = {g: ba.loc[pids, roles[g]].to_numpy(float) for g in ("demo", "dx", "meds", "util")}
    ecg = pcs(np.stack(em.loc[pids, "embedding"].to_numpy()).astype(float), 32)
    G["ECG"] = ecg
    G["permECG"] = ecg[np.random.default_rng(20261001 + TRIALS.index(trial)).permutation(len(pids))]
    panels = {"A_i0": h0.loc[pids, PANEL_A].to_numpy(float),
              "C_dx_util": np.hstack([G["dx"], G["util"]]),
              "B_cmr_i2": np.hstack([cmr.reindex(pids)[CMR_VARS].to_numpy(float), ba.loc[pids, ["sbp", "bmi"]].to_numpy(float)])}
    pnames = {"A_i0": PANEL_A, "C_dx_util": roles["dx"] + roles["util"], "B_cmr_i2": CMR_VARS + ["sbp_i2", "bmi_i2"]}
    rb = np.log(rct["our_orientation"])
    rs = (np.log(rct["hi"]) - np.log(rct["lo"])) / (2 * 1.959964)
    est, bal, per = [], [], []
    for a, parts in ARMS.items():
        if parts is None:
            idx, cl = np.arange(len(t)), None
        else:
            idx, cl, _ = match(ps_logit(np.hstack([G[p] for p in parts]), t), t)
        b, se = cox(T[idx], E[idx], t[idx]) if cl is None else cox(T[idx], E[idx], t[idx], cluster=cl)
        z = (b - rb) / np.sqrt(se ** 2 + rs ** 2)
        est.append(dict(design=design, trial=trial, arm=a, n_t=sup(t[idx].sum()), n_c=sup((1 - t[idx]).sum()),
                        pairs=np.nan if cl is None else sup(len(idx) // 2), events_t=sup(E[idx][t[idx] == 1].sum()),
                        events_c=sup(E[idx][t[idx] == 0].sum()), loghr=b, se=se, hr=np.exp(b), lo=np.exp(b - 1.96 * se),
                        hi=np.exp(b + 1.96 * se), rct_hr=rct["our_orientation"], rct_lo=rct["lo"], rct_hi=rct["hi"],
                        abs_dlog=abs(b - rb), est_agree=bool(abs(b - rb) <= 1.959964 * rs), std_agree=bool(abs(z) < 1.959964), z=z))
        for pn, V in panels.items():
            if pn == "C_dx_util" and parts is not None and "dx" in parts:
                continue
            s = smd(V, t, idx)
            ok = ~np.isnan(s)
            bal.append(dict(design=design, trial=trial, arm=a, panel=pn, k=int(ok.sum()), mean_abs_smd=float(np.nanmean(s)),
                            pct_lt_0_1=float(100 * np.mean(s[ok] < 0.1))))
            for nm, v in zip(pnames[pn], s):
                per.append(dict(design=design, trial=trial, arm=a, panel=pn, var=nm, abs_smd=float(v)))
    miss = {c: round(100 * float(np.isnan(h0.loc[pids, c].to_numpy(float)).mean()), 1) for c in PANEL_A}
    meta = dict(design=design, trial=trial, n=sup(len(pids)), n_t=sup(t.sum()), n_c=sup((1 - t).sum()), events=sup(E.sum()),
                rct_hr=rct["our_orientation"], panel_A_missing_pct=json.dumps(miss),
                cmr_available_pct=round(100 * float(cmr.reindex(pids).lvef.notna().mean()), 1))
    return est, bal, per, meta, set(pids)


def signflip(d):
    d = np.asarray([x for x in d if np.isfinite(x)])
    if len(d) == 0:
        return np.nan
    obs = d.mean()
    null = [np.mean(d * s) for s in itertools.product([1, -1], repeat=len(d))]
    return float(np.mean(np.array(null) >= obs - 1e-12))


def pooled_balance(B, trials, design, B_boot=2000):
    out = []
    rng = np.random.default_rng(0)
    for pn in B.panel.unique():
        for arm, ref in REF.items():
            x = B[(B.design == design) & (B.panel == pn) & B.trial.isin(trials)].pivot_table(index="trial", columns="arm", values="mean_abs_smd")
            p = B[(B.design == design) & (B.panel == pn) & B.trial.isin(trials)].pivot_table(index="trial", columns="arm", values="pct_lt_0_1")
            if arm not in x or ref not in x:
                continue
            x, p = x[[ref, arm]].dropna(), p[[ref, arm]].dropna()
            rr = 100 * (1 - x[arm].sum() / x[ref].sum())
            bs = []
            for _ in range(B_boot):
                i = rng.integers(0, len(x), len(x))
                bs.append(100 * (1 - x[arm].iloc[i].sum() / x[ref].iloc[i].sum()))
            dpp = (p[arm] - p[ref])
            out.append(dict(design=design, panel=pn, arm=arm, ref=ref, k_trials=len(x), mean_smd_ref=x[ref].mean(), mean_smd_arm=x[arm].mean(),
                            rel_reduction_pct=rr, ci_lo=float(np.percentile(bs, 2.5)), ci_hi=float(np.percentile(bs, 97.5)),
                            pct_lt01_ref=p[ref].mean(), pct_lt01_arm=p[arm].mean(), d_pts=dpp.mean(),
                            trials_better=int(((x[ref] - x[arm]) > 0).sum()), signflip_p=signflip((x[ref] - x[arm]).to_numpy())))
    return pd.DataFrame(out)


def pooled_emu(E, trials, design):
    out = []
    e = E[(E.design == design) & E.trial.isin(trials)]
    for a in ARMS:
        g = e[e.arm == a]
        r = dict(design=design, arm=a, k=len(g), mean_abs_dlog=g.abs_dlog.mean(), est_agree=int(g.est_agree.sum()),
                 std_agree=int(g.std_agree.sum()), pearson_r=float(np.corrcoef(g.loghr, np.log(g.rct_hr))[0, 1]) if len(g) > 2 else np.nan)
        if a in REF:
            ref = e[e.arm == REF[a]].set_index("trial").abs_dlog
            dd = (ref - g.set_index("trial").abs_dlog).dropna()
            r.update(ref=REF[a], closer=int((dd > 0).sum()), signflip_p=signflip(dd.to_numpy()))
        out.append(r)
    return pd.DataFrame(out)


def analyze():
    os.umask(0o077)
    sys.path.insert(0, str(HERE))
    import ukb_cmr_plasmode as U
    cmr = U.cmr_table()
    E, B, Pv, M, ids = [], [], [], [], {}
    for design in ("d1", "d2"):
        for trial in TRIALS:
            r = analyze_one(design, trial, cmr)
            if r is None:
                continue
            e, b, p, m, s = r
            E += e; B += b; Pv += p; M.append(m); ids[(design, trial)] = s
            print(design, trial, m["n"], m["events"], flush=True)
    E, B, Pv, M = pd.DataFrame(E), pd.DataFrame(B), pd.DataFrame(Pv), pd.DataFrame(M)
    E.to_csv(OUT / "emu_estimates.csv", index=False)
    B.to_csv(OUT / "emu_balance.csv", index=False)
    Pv.to_csv(OUT / "emu_balance_by_var.csv", index=False)
    M.to_csv(OUT / "emu_meta.csv", index=False)
    ov = []
    for design in ("d1", "d2"):
        for a, b in itertools.permutations([t for t in TRIALS if (design, t) in ids], 2):
            A_, B_ = ids[(design, a)], ids[(design, b)]
            ov.append(dict(design=design, trial=a, other=b, share_of_trial_in_other=round(len(A_ & B_) / len(A_), 3)))
    pd.DataFrame(ov).to_csv(OUT / "emu_overlap.csv", index=False)
    sets = {"d2": [t for t in TRIALS if ("d2", t) in ids], "d1": [t for t in TRIALS if ("d1", t) in ids]}
    PB = pd.concat([pooled_balance(B, sets[d], d) for d in sets], ignore_index=True)
    PE = pd.concat([pooled_emu(E, sets[d], d) for d in sets], ignore_index=True)
    PB.to_csv(OUT / "emu_pooled_balance.csv", index=False)
    PE.to_csv(OUT / "emu_pooled_emulation.csv", index=False)
    # reproduction vs v1.5 estimates (d1, full population, primary outcome)
    rep = []
    for t, v in V15.items():
        o = pd.read_csv(v / "analysis" / "estimates.csv")
        o = o[(o.population == "full") & (o.outcome == "primary")].set_index("arm")
        for a in ("unmatched", "sparse", "sparse+ECG"):
            m = E[(E.design == "d1") & (E.trial == t) & (E.arm == a)]
            if len(m) and a in o.index:
                rep.append(dict(trial=t, arm=a, loghr_v20=float(m.loghr.iloc[0]), loghr_v15=float(o.loc[a, "loghr"]),
                                absdev=abs(float(m.loghr.iloc[0]) - float(o.loc[a, "loghr"]))))
    R = pd.DataFrame(rep)
    R.to_csv(OUT / "emu_gate_estimates.csv", index=False)
    print(R.to_string(index=False))
    print(PB.round(3).to_string(index=False))
    print(PE.round(3).to_string(index=False))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build(sys.argv[2])
    elif cmd == "gate":
        gate()
    elif cmd == "analyze":
        analyze()
