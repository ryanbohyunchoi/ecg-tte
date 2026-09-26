"""v1.5 UK Biobank cohort builder (prevalent-user, active-comparator, anchored at the imaging visit).

Usage:  python v15_ukb_build.py cohort      # cohort/baseline/roles/panel/rct/summary + READY_COHORT (or INFEASIBLE)
        python v15_ukb_build.py outcomes    # feasibility rule, then outcomes.parquet + READY_OUTCOMES (or INFEASIBLE)
        python v15_ukb_build.py clmbr       # CLMBR usability checks; clmbr_embedding.parquet where usable

Index = p53_i2 (imaging visit); ECG = <eid>_20205_2_0.npy (lag 0). Arms from p20003_i2 (coding-4 names).
Writes restricted files only to /mnt/raid0/rbc58/ecg-tte/audits/claude-v15-ukb-<trial>/ (umask 077).
Reports are aggregate; counts 1-10 are suppressed as "<11".
"""
import json
import os
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v15_ukb_common import (AUDIT, CLMBR_PQ, COMPARISONS, DATA_CSV, DATA_END, DX_CORE, ECG_DIR, MEDS_PQ, NCO, OUT_CODES,
                            SPEC_ELIG, CLASS_RX, classes_of, rx_tokens, HTN_ICD, ANTIHTN_CLASSES)
import trial_specs as ts

os.umask(0o077)
END = pd.Timestamp(DATA_END)
MED_CLASSES = [k for k in CLASS_RX if k not in ("bb_other",)] + ["bb_other_systemic"]


def sup(n):
    n = int(n)
    return "<11" if 0 < n < 11 else n


def outdir(trial):
    d = Path(AUDIT) / f"claude-v15-ukb-{trial}"
    d.mkdir(mode=0o700, exist_ok=True)
    return d


# ------------------------------------------------------------------ loading
def load():
    con = duckdb.connect()
    con.execute(f"create table raw as select * from read_csv_auto('{DATA_CSV}', all_varchar=true, sample_size=-1) "
                "where p53_i2 is not null")  # materialise once (imaging-visit attenders only)
    cols = [r[0] for r in con.execute("describe raw").fetchall()]
    base_cols = ["eid", "p31", "p34", "p52", "p53_i0", "p53_i1", "p53_i2", "p1239_i2", "p20160_i2", "p2966_i0", "p2966_i1",
                 "p2966_i2", "p4080_i2_a0", "p4080_i2_a1", "p23104_i2", "p21000_i0", "p40000_i0", "p40000_i1", "p42000", "p42006"]
    base_cols += [f"p{f}_i{i}" for f in (30690, 30700, 30750, 30760, 30780) for i in (0, 1)]
    con.execute(f"create table b as select {', '.join(base_cols)} from raw where p53_i2 is not null")
    base = con.execute("select * from b").df()
    # hospital ICD-10 first occurrences (41270 pipe list; 41280_aK = date of the K-th listed code)
    d41280 = sorted([c for c in cols if c.startswith("p41280_a")], key=lambda c: int(c.split("_a")[1]))
    un = " union all ".join(f"select eid, split_part(p41270, '|', {int(c.split('_a')[1]) + 1}) item, {c} date "
                            f"from raw where {c} is not null" for c in d41280)
    con.execute(f"create table dx as select eid, replace(split_part(item, ' ', 1), '.', '') code, date from ({un})")
    chk = con.execute("select count(distinct eid), sum((code is null or code = '')::int) from dx").fetchall()[0]
    con.execute("delete from dx where code is null or code = ''")
    dx = con.execute("select eid, code, cast(date as date) date from dx").df()
    meds = {}
    for inst in (0, 1, 2):
        mc = [c for c in cols if c.startswith(f"p20003_i{inst}_")]
        un = " union all ".join(f"select eid, {c} m from raw where p53_i2 is not null and {c} is not null" for c in mc)
        meds[inst] = con.execute(un).df()
    return base, dx, meds, dict(dx_people=int(chk[0]), dx_dates_without_code=int(chk[1] or 0))


def prep_base(base):
    b = pd.DataFrame({"eid": base.eid.astype(str)})
    b["index_date"] = pd.to_datetime(base.p53_i2)
    months = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                           "September", "October", "November", "December"], 1)}
    dob = pd.to_datetime(dict(year=pd.to_numeric(base.p34), month=base.p52.map(months).fillna(7), day=15), errors="coerce")
    b["age"] = (b.index_date - dob).dt.days / 365.25
    b["male"] = (base.p31 == "Male").astype(float)
    b["index_year"] = b.index_date.dt.year
    sbp = base[["p4080_i2_a0", "p4080_i2_a1"]].apply(pd.to_numeric, errors="coerce")
    b["sbp"] = sbp.mean(axis=1)
    b["bmi"] = pd.to_numeric(base.p23104_i2, errors="coerce")
    b["current_smoker"] = base.p1239_i2.map({"No": 0.0, "Yes, on most or all days": 1.0, "Only occasionally": 1.0})
    b["ever_smoker"] = base.p20160_i2.map({"No": 0.0, "Yes": 1.0})
    for f, nm in [(30690, "cholesterol"), (30700, "creatinine"), (30750, "hba1c"), (30760, "hdl"), (30780, "ldl")]:
        v1 = pd.to_numeric(base[f"p{f}_i1"], errors="coerce")
        v0 = pd.to_numeric(base[f"p{f}_i0"], errors="coerce")
        b[nm] = v1.fillna(v0)  # latest pre-imaging biomarker (instance 1 if present, else instance 0)
    b["htn_selfreport"] = base[["p2966_i0", "p2966_i1", "p2966_i2"]].notna().any(axis=1).astype(float)
    d0 = pd.to_datetime(base.p40000_i0, errors="coerce")
    d1 = pd.to_datetime(base.p40000_i1, errors="coerce")
    b["death_date"] = pd.concat([d0, d1], axis=1).min(axis=1)
    for f, nm in [("p42000", "mi_alg"), ("p42006", "stroke_alg")]:
        b[f"{nm}_date"] = pd.to_datetime(base[f], errors="coerce")
        b[f"{nm}_unknown"] = (base[f] == "Date is unknown").astype(float)
    b["has_ecg"] = b.eid.map(lambda e: os.path.exists(f"{ECG_DIR}/{e}_20205_2_0.npy")).astype(int)
    return b.set_index("eid")


def med_classes(meds_i):
    m = meds_i.copy()
    m["eid"] = m.eid.astype(str)
    m["cls"] = m.m.map(lambda x: sorted(classes_of(x)))
    long = m.explode("cls").dropna(subset=["cls"])
    wide = pd.crosstab(long.eid, long.cls).clip(upper=1)
    return m, wide


def first_date(dx, codes, before=None):
    """Earliest first-occurrence date per eid over codes (prefix match)."""
    sel = dx[dx.code.str.startswith(tuple(codes))]
    return sel.groupby("eid").date.min()


# ------------------------------------------------------------------ cohort
def build_arms(trial, spec, b, medw):
    A, B, EX = spec["A"], spec["B"], spec["excl_both"]
    w = medw.reindex(b.index).fillna(0)
    get = lambda cl: w[[c for c in cl if c in w]].sum(axis=1) > 0 if any(c in w for c in cl) else pd.Series(False, index=w.index)
    inA, inB, inEX = get(A), get(B), get(EX)
    return inA, inB, inEX


def cohort(trials):
    base, dx, meds, chk = load()
    dx["eid"] = dx.eid.astype(str)
    dx["date"] = pd.to_datetime(dx.date)
    b = prep_base(base)
    dx = dx.join(b.index_date, on="eid")
    pre = dx[dx.date < dx.index_date]
    m2, medw = med_classes(meds[2])
    info = dict(i2_attenders=len(b), dx_check=chk, data_end=DATA_END,
                index_range=[str(b.index_date.min().date()), str(b.index_date.max().date())])
    # ukb_meds screen (claimed GP prescriptions) — record-date provenance
    mp = duckdb.connect().execute(f"select cast(PAT_MRN_ID as varchar) eid, event_date, medication_name from '{MEDS_PQ}'").df()
    for trial in trials:
        spec = COMPARISONS[trial]
        d = outdir(trial)
        att = []
        n = lambda s: sup(int(s.sum()) if s.dtype == bool else len(s))
        elig = pd.Series(True, index=b.index)
        att.append(("imaging visit (instance 2) attended", n(elig)))
        elig &= b.index_date < END
        att.append((f"index before data end {DATA_END}", n(elig)))
        elig &= ~(b.death_date <= b.index_date)
        att.append(("alive at index", n(elig)))
        inA, inB, inEX = build_arms(trial, spec, b, medw)
        att.append((f"any {spec['arms'][0]} or {spec['arms'][1]} at i2", n(elig & (inA | inB))))
        elig &= inA ^ inB
        att.append(("exactly one arm (users of both removed)", n(elig)))
        elig &= ~inEX
        att.append((f"no {'/'.join(spec['excl_both']) or 'n/a'} use", n(elig)))
        if spec["gate"] == "htn":
            htn_icd = pre[pre.code.str.startswith(tuple(HTN_ICD))].eid.unique()
            w = medw.reindex(b.index).fillna(0)
            on_ah = w[[c for c in ANTIHTN_CLASSES if c in w]].sum(axis=1) > 0
            gate = b.index.isin(htn_icd) | (b.htn_selfreport == 1) | on_ah
            att.append(("hypertension gate (I10-I15 before index, self-report 2966, or antihypertensive)", n(elig & gate)))
        else:
            af = pre[pre.code.str.startswith("I48")].eid.unique()
            gate = b.index.isin(af)
            att.append(("AF gate (I48 before index)", n(elig & gate)))
        elig &= gate
        for c in spec["excl_dx"]:
            prior = pre[pre.code.str.startswith(c)].eid.unique()
            elig &= ~b.index.isin(prior)
            att.append((f"no prior {c}", n(elig)))
        coh = b[elig].copy()
        coh["treated"] = inA[elig].astype(int)
        nA, nB = int(coh.treated.sum()), int((1 - coh.treated).sum())
        eA, eB = int(coh.has_ecg[coh.treated == 1].sum()), int(coh.has_ecg[coh.treated == 0].sum())
        summ = dict(trial=trial, comparison=spec["comparison"], arms=list(spec["arms"]), design="prevalent-user active comparator at imaging visit (instance 2)",
                    attrition=att, n_arm=[sup(nA), sup(nB)], n_arm_with_ecg=[sup(eA), sup(eB)],
                    ecg_coverage=round((eA + eB) / max(1, nA + nB), 3), feasible_200_with_ecg=bool(min(eA, eB) >= 200), **info)
        # new-user screen in the processed "ukb_meds" table
        summ["new_user_screen"] = new_user_screen(spec, b, mp)
        # trial_specs eligibility sensitivity count
        if trial in SPEC_ELIG:
            se = SPEC_ELIG[trial]
            s2 = pd.Series(True, index=coh.index)
            if "min_age" in se: s2 &= coh.age >= se["min_age"]
            if "max_age" in se: s2 &= coh.age <= se["max_age"]
            if "require_any" in se:
                req = set(pre[pre.code.str.startswith(tuple(se["require_any"]))].eid) | set(coh.index[coh.mi_alg_date < coh.index_date])
                s2 &= coh.index.isin(req)
            if "excl" in se:
                s2 &= ~coh.index.isin(pre[pre.code.str.startswith(tuple(se["excl"]))].eid)
            summ["trial_specs_eligibility_sensitivity"] = dict(criteria=se, n_arm_with_ecg=[
                sup((s2 & (coh.treated == 1) & (coh.has_ecg == 1)).sum()), sup((s2 & (coh.treated == 0) & (coh.has_ecg == 1)).sum())])
        write_rct(trial, spec, d)
        if nA == 0 or nB == 0:
            summ["notes"] = infeasible_note(trial)
            json.dump(summ, open(d / "summary.json", "w"), indent=1, default=str)
            (d / "INFEASIBLE").write_text(summ["notes"] + "\n")
            print(json.dumps(summ, indent=1, default=str))
            continue
        coh.index.name = "pid"
        cdf = pd.DataFrame({"pid": coh.index.astype(str), "treated": coh.treated.values,
                            "index_day": ((coh.index_date - pd.Timestamp("1970-01-01")).dt.days).astype(float).values,
                            "index_year": coh.index_year.astype(int).values})
        cdf.to_parquet(d / "cohort.parquet", index=False)
        ecg = coh[coh.has_ecg == 1]
        pd.DataFrame({"pid": ecg.index.astype(str), "ecg_path": [f"{ECG_DIR}/{e}_20205_2_0.npy" for e in ecg.index],
                      "lag_days": 0.0}).to_parquet(d / "ecg_manifest.parquet", index=False)
        bl, roles, miss = baseline(spec, coh, pre, medw)
        bl.to_parquet(d / "baseline.parquet", index=False)
        json.dump(roles, open(d / "roles.json", "w"), indent=1)
        pan, dic = panel(spec, coh, pre, m2)
        pan.to_parquet(d / "panel.parquet", index=False)
        dic.to_csv(d / "panel_dictionary.csv", index=False)
        summ.update(missingness_pct=miss, panel_features=dict(dx=int((dic.domain == "dx").sum()), rx=int((dic.domain == "rx").sum())),
                    age_mean_by_arm=[round(coh.age[coh.treated == 1].mean(), 1), round(coh.age[coh.treated == 0].mean(), 1)],
                    index_year_range=[int(coh.index_year.min()), int(coh.index_year.max())],
                    notes=cohort_notes(trial))
        json.dump(summ, open(d / "summary.json", "w"), indent=1, default=str)
        (d / "READY_COHORT").write_text("ok\n")
        print(json.dumps({k: summ[k] for k in ("trial", "attrition", "n_arm", "n_arm_with_ecg", "feasible_200_with_ecg", "new_user_screen")}, indent=1, default=str))


def new_user_screen(spec, b, mp):
    """New users in ukb_meds whose first arm-drug record is within (index, index+365] with none on/before index."""
    cls = mp.medication_name.map(lambda x: classes_of(x))
    mp = mp.assign(date=pd.to_datetime(mp.event_date, errors="coerce"))
    mp = mp[mp.eid.isin(b.index)].join(b.index_date, on="eid")
    res = {}
    for arm, cl in zip(spec["arms"], (spec["A"], spec["B"])):
        if not cl:
            res[arm] = 0
            continue
        isarm = cls.loc[mp.index].map(lambda s: bool(s & set(cl)))
        x = mp[isarm]
        before = set(x.eid[x.date <= x.index_date])
        after = x[(x.date > x.index_date) & (x.date <= x.index_date + pd.Timedelta(days=365)) & ~x.eid.isin(before)]
        res[arm] = sup(after.eid.nunique())
    res["note"] = ("ukb_meds records carry coding-4 self-report names mapped to RxNorm and are dated at assessment visits "
                   "(not GP prescriptions); new-user variant not feasible from this table")
    return res


def infeasible_note(trial):
    if trial == "aristotle":
        return ("INFEASIBLE: UKB coding 4 (field 20003) has no DOAC entries (apixaban/rivaroxaban/dabigatran/edoxaban absent), "
                "so no DOAC arm exists at the imaging visit; the processed ukb_meds table has no DOAC records either. "
                "Warfarin-only users counted in attrition.")
    return "INFEASIBLE: an arm is empty"


def cohort_notes(trial):
    s = [f"index = imaging visit date p53_i2; ECG = 20205 instance 2 (lag 0); ecg_manifest.parquet lists npy paths",
         "arms from self-reported current medication at instance 2 (prevalent users; duration unknown)",
         f"covariates: ICD-10 first occurrences (41270/41280) strictly before index; hospital data end {DATA_END}",
         "biomarkers: latest pre-imaging blood sample (instance 1 if present else instance 0), 4-10 years before index",
         "SBP = mean of automated readings (4080) at instance 2; manual readings (93) not in extract",
         "panel dx_ = all-history (not 365-d) count of distinct ICD-10 codes per 3-char category (first-occurrence data); rx_ = i2 self-report tokens",
         "util = distinct first-occurrence dates / distinct codes before index and number of non-exposure i2 medications"]
    if trial == "ontarget":
        s.append("ELITE II (losartan vs captopril, all-cause death) = secondary benchmark; see rct.json secondary")
    return s


def baseline(spec, coh, pre, medw):
    X = pd.DataFrame(index=coh.index)
    X["age_at_index"], X["male"], X["index_year"] = coh.age, coh.male, coh.index_year.astype(float)
    p = pre[pre.eid.isin(coh.index)]
    for k, codes in DX_CORE.items():
        X[f"dx_{k}"] = X.index.isin(p[p.code.str.startswith(tuple(codes))].eid).astype(float)
    X["dx_hypertension"] = np.maximum(X.dx_hypertension, coh.htn_selfreport)
    prior_mi = (coh.mi_alg_date < coh.index_date) | (coh.mi_alg_unknown == 1)
    prior_st = (coh.stroke_alg_date < coh.index_date) | (coh.stroke_alg_unknown == 1)
    X["dx_ihd_mi"] = np.maximum(X.dx_ihd_mi, prior_mi.astype(float))
    X["dx_stroke"] = np.maximum(X.dx_stroke, prior_st.astype(float))
    expo = set(spec["A"]) | set(spec["B"]) | set(spec["excl_both"])
    if "bb_trial" in expo or "bb_other_systemic" in expo:
        expo |= {"bb_trial", "bb_other_systemic"}
    w = medw.reindex(coh.index).fillna(0)
    meds = []
    for c in MED_CLASSES:
        if c in expo:
            continue
        X[f"med_{c}"] = w[c].astype(float) if c in w else 0.0
        meds.append(f"med_{c}")
    labs = ["sbp", "bmi", "current_smoker", "ever_smoker", "cholesterol", "creatinine", "hba1c", "hdl", "ldl"]
    for c in labs:
        X[c] = coh[c]
    X["util_n_dx_dates"] = p.groupby("eid").date.nunique().reindex(X.index).fillna(0)
    X["util_n_dx_codes"] = p.groupby("eid").code.nunique().reindex(X.index).fillna(0)
    X["util_n_i2_meds_nonexposure"] = X[meds].sum(axis=1)
    dxc = [f"dx_{k}" for k in DX_CORE]
    const = [c for c in X.columns if X[c].nunique(dropna=True) <= 1]
    X = X.drop(columns=const)
    keep = lambda L: [c for c in L if c in X.columns]
    roles = dict(demo=keep(["age_at_index", "male", "index_year"]), dx=keep(dxc), meds=keep(meds), labs_vitals=keep(labs),
                 util=keep(["util_n_dx_dates", "util_n_dx_codes", "util_n_i2_meds_nonexposure"]),
                 phys=keep(["sbp", "bmi", "creatinine", "cholesterol", "hba1c"]))
    roles["_dropped_constant"] = const
    miss = {c: round(100 * X[c].isna().mean(), 1) for c in X.columns if X[c].isna().any()}
    X = X.astype(float).reset_index().rename(columns={"eid": "pid"})
    X["pid"] = X.pid.astype(str)
    return X, roles, miss


def panel(spec, coh, pre, m2):
    p = pre[pre.eid.isin(coh.index)].copy()
    p["c3"] = p.code.str[:3]
    dxp = p.groupby(["eid", "c3"]).code.nunique().unstack(fill_value=0)
    dxp.columns = [f"dx_{c}" for c in dxp.columns]
    expo = set(spec["A"]) | set(spec["B"]) | set(spec["excl_both"])
    if expo & {"bb_trial", "bb_other_systemic"}:
        expo |= {"bb_trial", "bb_other_systemic", "bb_other"}
    m = m2[m2.eid.isin(coh.index)].copy()
    m["tok"] = m.m.map(rx_tokens)
    m = m.explode("tok").dropna(subset=["tok"])
    bad = {t for t in m.tok.unique() if classes_of(t.replace("_", " ")) & expo}
    # also drop tokens of combination products whose full name is exposure-defining only via brand
    m = m[~m.tok.isin(bad)]
    rxp = pd.crosstab(m.eid, m.tok).clip(upper=1)
    rxp.columns = [f"rx_{c}" for c in rxp.columns]
    P = pd.concat([dxp, rxp], axis=1).reindex(coh.index).fillna(0)
    prev = (P > 0).mean()
    P = P.loc[:, prev >= 0.01]
    # hard check: no exposure token survives
    assert not [c for c in P.columns if c.startswith("rx_") and classes_of(c[3:].replace("_", " ")) & expo]
    dic = pd.DataFrame({"feature": P.columns, "domain": [c.split("_")[0] for c in P.columns]})
    P = P.astype(float).reset_index().rename(columns={"eid": "pid", "index": "pid"})
    P["pid"] = P.pid.astype(str)
    return P, dic


def write_rct(trial, spec, d):
    pub = ts.PUBLISHED[spec["rct_key"]]
    months = ts.HORIZON_MONTHS[spec["rct_key"]]
    maxfu = (END - pd.Timestamp("2014-04-30")).days
    hd = int(min(round(months * 30.4375), maxfu))
    rct = dict(trial=trial, key=spec["rct_key"], arms=list(spec["arms"]), hr=pub["hr"], lo=pub["ci"][0], hi=pub["ci"][1],
               ci_level=pub.get("ci_level", 0.95), our_orientation=pub["our_orientation"], horizon_days=hd,
               endpoint={"ontarget": "all-cause death (for CV death), MI, stroke or HF (first hospital ICD-10 / algorithmic dates)",
                         "allhat": "all-cause death (for CHD death) or MI", "ascot": "all-cause death (for CHD death) or MI",
                         "aristotle": "stroke or systemic embolism"}[trial],
               notes=f"RCT: {pub['rct_arms']} ({pub['measure']}; {pub['endpoint']}; {pub['source']}). "
                     f"Horizon {months} months (trial), not capped: max possible follow-up {maxfu} d to data end {DATA_END}. "
                     "Class adaptation, prevalent users.")
    if spec["secondary"]:
        rct["secondary"] = []
        for k in spec["secondary"]:
            q = ts.PUBLISHED[k]
            rct["secondary"].append(dict(key=k, hr=q["hr"], lo=q["ci"][0], hi=q["ci"][1], ci_level=q.get("ci_level", 0.95),
                                         our_orientation=q["our_orientation"], endpoint=q["endpoint"], rct_arms=q["rct_arms"],
                                         horizon_days=int(round(ts.HORIZON_MONTHS[k] * 30.4375)),
                                         outcome_columns="t_sec_death/e_sec_death" if k == "elite_ii" else None))
    json.dump(rct, open(d / "rct.json", "w"), indent=1)


# ------------------------------------------------------------------ outcomes
def outcomes(trials):
    base, dx, _, _ = load()
    dx["eid"] = dx.eid.astype(str)
    dx["date"] = pd.to_datetime(dx.date)
    b = prep_base(base)
    for trial in trials:
        d = outdir(trial)
        if not (d / "READY_COHORT").exists():
            continue
        spec = COMPARISONS[trial]
        summ = json.load(open(d / "summary.json"))
        rct = json.load(open(d / "rct.json"))
        coh = pd.read_parquet(d / "cohort.parquet")
        c = b.loc[coh.pid].copy()
        c["treated"] = coh.treated.values
        eA, eB = int(c.has_ecg[c.treated == 1].sum()), int(c.has_ecg[c.treated == 0].sum())
        if min(eA, eB) < 200:
            (d / "INFEASIBLE").write_text(f"fewer than 200 per arm with ECG ({sup(eA)}, {sup(eB)})\n")
            continue
        H = rct["horizon_days"]
        idx = c.index_date
        dd = dx[dx.eid.isin(c.index)].join(idx, on="eid")
        admin_end = pd.concat([pd.Series(END, index=c.index), c.death_date.where(c.death_date <= END)], axis=1).min(axis=1)

        def first_after(codes, extra=None):
            s = dd[dd.code.str.startswith(tuple(codes)) & (dd.date > dd.index_date)].groupby("eid").date.min().reindex(c.index)
            if extra is not None:
                s = pd.concat([s, extra.where(extra > idx)], axis=1).min(axis=1)
            return s

        comp = {}
        same_day = 0
        for k in spec["outcome"]:
            if k == "death":
                comp[k] = c.death_date.where((c.death_date > idx) & (c.death_date <= END))
            elif k == "mi":
                comp[k] = first_after(OUT_CODES["mi"], c.mi_alg_date)
            elif k == "stroke":
                comp[k] = first_after(OUT_CODES["stroke"], c.stroke_alg_date)
            else:
                comp[k] = first_after(OUT_CODES[k])
            if k != "death":
                same_day += int(dd[dd.code.str.startswith(tuple(OUT_CODES[k])) & (dd.date == dd.index_date)].eid.nunique())
        ev = pd.concat(comp.values(), axis=1).min(axis=1)

        def te(evdate, horizon):
            end = pd.concat([admin_end, idx + pd.Timedelta(days=horizon)], axis=1).min(axis=1)
            e = (evdate.notna() & (evdate <= end)).astype(int)
            t = np.where(e == 1, (evdate - idx).dt.days, (end - idx).dt.days).astype(float)
            t = np.where(t <= 0, 0.5, t)
            return t, e.values

        out = pd.DataFrame({"pid": c.index.astype(str)})
        out["t"], out["e"] = te(ev, H)
        if trial == "ontarget":
            out["t_sec_death"], out["e_sec_death"] = te(comp["death"], rct["secondary"][0]["horizon_days"])
        ncos = {}
        for nm, codes in NCO.items():
            prev = dd[dd.code.str.startswith(tuple(codes)) & (dd.date <= dd.index_date)].eid.unique()
            t, e = te(first_after(codes), H)
            t = np.where(c.index.isin(prev), np.nan, t).astype(float)
            e = np.where(c.index.isin(prev), np.nan, e).astype(float)
            out[f"t_nco_{nm}"], out[f"e_nco_{nm}"] = t, e
            ok = ~np.isnan(e)
            ncos[nm] = dict(n_at_risk=sup(ok.sum()), events=[sup(np.nansum(e[ok & (coh.treated.values == 1)])),
                                                              sup(np.nansum(e[ok & (coh.treated.values == 0)]))])
        out.to_parquet(d / "outcomes.parquet", index=False)
        tr = coh.treated.values == 1
        fu = lambda m: [round(float(np.median(out.t[m])) / 365.25, 2), round(float(np.percentile(out.t[m], 25)) / 365.25, 2),
                        round(float(np.percentile(out.t[m], 75)) / 365.25, 2)]
        per_comp = {k: [sup(((v.notna()) & (v <= pd.concat([admin_end, idx + pd.Timedelta(days=H)], axis=1).min(axis=1)))[tr].sum()),
                        sup(((v.notna()) & (v <= pd.concat([admin_end, idx + pd.Timedelta(days=H)], axis=1).min(axis=1)))[~tr].sum())]
                    for k, v in comp.items()}
        summ["outcomes"] = dict(components=spec["outcome"], horizon_days=H, events_primary=[sup(out.e[tr].sum()), sup(out.e[~tr].sum())],
                                events_by_component=per_comp, followup_years_median_iqr=dict(first=fu(tr), second=fu(~tr)),
                                persons_with_component_code_on_index_day=sup(same_day), nco=ncos,
                                notes=["events strictly after index; censoring at min(death, hospital data end %s, horizon)" % DATA_END,
                                       "CV/CHD death unavailable (no 40001 in extract): all-cause death used",
                                       "41280 gives only the first date per ICD-10 code: recurrent events of an already-coded code are not observable",
                                       "MI/stroke also from algorithmic dates 42000/42006 (first event only)",
                                       "NCO: prevalent cases (code on/before index) set to NaN"])
        if trial == "ontarget":
            summ["outcomes"]["secondary_death_elite_ii"] = dict(horizon_days=rct["secondary"][0]["horizon_days"],
                                                              events=[sup(out.e_sec_death[tr].sum()), sup(out.e_sec_death[~tr].sum())])
        json.dump(summ, open(d / "summary.json", "w"), indent=1, default=str)
        (d / "READY_OUTCOMES").write_text("ok\n")
        print(trial, json.dumps(summ["outcomes"], default=str))


# ------------------------------------------------------------------ CLMBR
def clmbr(trials):
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict
    from sklearn.metrics import roc_auc_score
    E = pd.read_parquet(CLMBR_PQ)
    E["pid"] = E.PAT_MRN_ID.astype(str)
    E = E.set_index("pid")
    base, _, meds, _ = load()
    b = prep_base(base)
    E["censor"] = pd.to_datetime(E.censor_date)
    j = E.join(b.index_date, how="inner")
    idcheck = dict(n_embeddings=len(E), matched_to_eid_with_i2=len(j), censor_eq_index=int((j.censor.dt.normalize() == j.index_date).sum()),
                   censor_lt_index=int((j.censor.dt.normalize() < j.index_date).sum()), censor_gt_index=int((j.censor.dt.normalize() > j.index_date).sum()))
    _, w0 = med_classes(meds[0])
    _, w1 = med_classes(meds[1])
    prior = pd.concat([w0, w1]).groupby(level=0).max()
    for trial in trials:
        d = outdir(trial)
        if not (d / "READY_COHORT").exists():
            continue
        spec = COMPARISONS[trial]
        summ = json.load(open(d / "summary.json"))
        coh = pd.read_parquet(d / "cohort.parquet").set_index("pid")
        cj = coh.join(j[["clmbr_embedding", "censor", "index_date"]], how="inner")
        cj = cj[cj.censor.dt.normalize() <= cj.index_date]
        # leakage probe: can the embedding separate arms among people with neither arm drug at i0/i1?
        cl = spec["A"] + spec["B"]
        pr = prior.reindex(cj.index).fillna(0)
        naive = pr[[c for c in cl if c in pr]].sum(axis=1) == 0
        X = np.vstack(cj.clmbr_embedding.values)
        y = cj.treated.values
        probe = {}
        for nm, m in [("all", np.ones(len(y), bool)), ("no_arm_drug_at_i0_i1", naive.values)]:
            if m.sum() < 100 or len(set(y[m])) < 2:
                continue
            p = cross_val_predict(LogisticRegression(C=0.1, max_iter=2000), X[m], y[m], cv=5, method="predict_proba")[:, 1]
            probe[nm] = dict(n=sup(m.sum()), auc=round(roc_auc_score(y[m], p), 3))
        usable = probe.get("no_arm_drug_at_i0_i1", {}).get("auc", 1) < 0.85
        summ["clmbr"] = dict(id_check=idcheck, n_with_embedding=sup(len(cj)), n_arm=[sup((cj.treated == 1).sum()), sup((cj.treated == 0).sum())],
                             leakage_probe_cv_auc=probe, usable=bool(usable),
                             note="PAT_MRN_ID = eid; censor_date = imaging date (p53_i2). Whether index-day events (i2 self-reported "
                                  "medications) enter the embedding is not documented; probe AUC among people without either arm drug at "
                                  "i0/i1 tests it (threshold 0.85).")
        if usable:
            pd.DataFrame({"pid": cj.index.astype(str), "embedding": [list(map(float, v)) for v in cj.clmbr_embedding.values]}).to_parquet(
                d / "clmbr_embedding.parquet", index=False)
        json.dump(summ, open(d / "summary.json", "w"), indent=1, default=str)
        print(trial, json.dumps(summ["clmbr"], default=str))


if __name__ == "__main__":
    stage = sys.argv[1]
    trials = sys.argv[2:] or list(COMPARISONS)
    dict(cohort=cohort, outcomes=outcomes, clmbr=clmbr)[stage](trials)
