#!/usr/bin/env python
"""v2.0 MIMIC-IV: build trial directories for SOAP II, ELITE II (class) and PEPTIC (docs/v20/MIMIC_REPLICATION_PLAN.md).

Cohort = the frozen feasibility-screen definition (audits/claude-v20-mimic-feasibility/stage/cohort_<k>.parquet:
subject_id, hadm_id, t0, treated [first-listed arm], ecg flag), re-checked for age >= 18 and no death before t0.
Baseline, panel and outcome conventions mirror scripts/v15/v15_mimic_cohort.py, v15_mimic_outcomes.py and
v15_mimic_death_dirs.py:
  demo  age, sex, estimated real index year
  dx    DX_CORE + heart failure, liver disease, GI bleed (index admission or any earlier admission)
  meds  fixed generic set, any order in [t0 - 365 d, t0) (the trial's own exposure classes removed)
  labs  latest creatinine / K / Na / Hb in [t0 - 365 d, t0); vitals SBP / DBP / HR (ICU chartevents before t0 or
        OMR dates before the index day), BMI (OMR)
  util  prior admissions (365 d), ED visits (365 d), days admission -> t0, ICU before t0
  panel dx / rx / px / lab features in the 365 d before t0 (min prevalence 1 %), exposure tokens removed
Outcome: all-cause death within the horizon (patients.dod); censoring min(horizon, last contact + 365 d);
index-day deaths t = 0.5.
Output: <OUT>/trials/<k>/ (restricted, umask 077). Prints aggregates only (counts 1-10 suppressed).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v15"))
from v15_mimic_common import (LABS, TS, VITAL_RANGES, concept_table, connect, pid_of, sql_list,  # noqa: E402
                              supp)

os.umask(0o077)
AUD = Path("/mnt/raid0/rbc58/ecg-tte/audits")
SCREEN = AUD / "claude-v20-mimic-feasibility/stage"
OUT = AUD / "claude-v20-mimic-replication/trials"

ACEI = ["enalapril", "lisinopril", "captopril", "ramipril", "quinapril", "benazepril", "fosinopril", "perindopril",
        "trandolapril", "moexipril", "vasotec", "zestril", "prinivil", "capoten", "altace", "accupril", "lotensin"]
ARB = ["losartan", "valsartan", "candesartan", "irbesartan", "olmesartan", "telmisartan", "cozaar", "diovan",
       "atacand", "avapro", "benicar", "micardis"]
SACVAL = ["sacubitril", "entresto"]
PPI = ["pantoprazole", "omeprazole", "esomeprazole", "lansoprazole", "rabeprazole", "protonix", "prilosec", "nexium"]
H2 = ["famotidine", "ranitidine", "cimetidine", "pepcid", "zantac"]
MEDS = {
    "aspirin_365d": ["aspirin", "ecotrin"],
    "statin_365d": [x.lower() for x in TS.STATIN],
    "beta_blocker_365d": ["metoprolol", "carvedilol", "atenolol", "bisoprolol", "propranolol", "labetalol", "nadolol",
                          "nebivolol", "lopressor", "toprol", "coreg"],
    "acei_arb_365d": ACEI + ARB,
    "loop_diuretic_365d": [x.lower() for x in TS.LOOP],
    "oral_anticoagulant_365d": ["warfarin", "coumadin", "jantoven", "apixaban", "eliquis", "rivaroxaban", "xarelto",
                                "dabigatran", "pradaxa", "edoxaban", "savaysa"],
    "ppi_365d": PPI,
    "insulin_365d": ["insulin"],
}
SPECS = {
    "soap2": dict(name="SOAP II", arms=["dopamine", "norepinephrine"], horizon=28,
                  expo=["dopamine", "intropin", "norepinephrine", "levophed", "noradrenaline"], drop_meds=[],
                  rct=dict(hr=1.17, lo=0.97, hi=1.42, measure="OR (95% CI)",
                           endpoint="all-cause death within 28 d (patients.dod)",
                           source="De Backer D, et al. N Engl J Med 2010;362:779-89 (PMID 20200382); death at 28 d, "
                                  "odds ratio with dopamine")),
    "elite2": dict(name="ELITE II (class)", arms=["ARB", "ACE inhibitor"], horizon=365,
                   expo=ACEI + ARB + SACVAL, drop_meds=["acei_arb_365d"],
                   rct=dict(hr=1.13, lo=0.95, hi=1.35, measure="HR (95.7% CI)",
                            endpoint="all-cause death within 365 d (patients.dod)",
                            source="Pitt B, et al. Lancet 2000;355:1582-7 (trial_specs PUBLISHED elite_ii); losartan vs "
                                   "captopril, all-cause mortality")),
    "peptic": dict(name="PEPTIC (negative-control trial)", arms=["PPI", "H2RA"], horizon=90,
                   expo=PPI + H2, drop_meds=["ppi_365d"],
                   rct=dict(hr=1.05, lo=1.00, hi=1.10, measure="RR (95% CI)",
                            endpoint="all-cause death within 90 d (patients.dod)",
                            source="PEPTIC Investigators, Young PJ, et al. JAMA 2020;323:616-26 (PMID 31950977); "
                                   "in-hospital death by day 90, risk ratio PPI vs H2RB")),
}
DXN = list(TS.DX_CORE) + ["heart_failure", "liver_disease", "gi_bleed"]


def build(k):
    spec = SPECS[k]
    D = OUT / k
    if (D / "READY_COHORT").exists():
        print(k, "READY_COHORT exists; skipping")
        return
    D.mkdir(parents=True, exist_ok=True, mode=0o700)
    con = connect(16)
    concept_table(con)
    scr = pd.read_parquet(SCREEN / f"cohort_{k}.parquet")
    con.register("scr", scr[["subject_id", "hadm_id", "t0", "treated"]])
    con.execute("""CREATE TEMP TABLE c2 AS SELECT s.*, ad.admittime, ad.dischtime, p.gender,
                   p.anchor_age + (year(s.t0) - p.anchor_year) age,
                   CAST(split_part(p.anchor_year_group, ' - ', 1) AS INT) + 1 + (year(s.t0) - p.anchor_year) est_year, p.dod
                   FROM scr s JOIN admissions ad USING (subject_id, hadm_id) JOIN patients p USING (subject_id)""")
    attr = [("screen cohort", len(scr))]
    con.execute("DELETE FROM c2 WHERE age < 18 OR dod < CAST(t0 AS DATE)")
    attr.append(("age >= 18 and no death before t0", con.execute("SELECT count(*) FROM c2").fetchone()[0]))
    con.execute("""CREATE TEMP TABLE rxt AS SELECT subject_id, hadm_id, starttime, upper(trim(route)) route,
                   regexp_split_to_array(lower(coalesce(drug, '')), '[^a-z0-9]+') toks FROM prescriptions""")
    coh = con.execute("SELECT * FROM c2 ORDER BY subject_id").df().set_index("subject_id")
    base = pd.DataFrame(index=coh.index)
    base["age_at_index"] = coh.age.astype(float)
    base["male"] = (coh.gender == "M").astype(float)
    base["index_year"] = coh.est_year.astype(float)
    # labs
    labrows = [(n, i) for n, (ids, lo, hi) in LABS.items() for i in ids]
    con.register("labmap_df", pd.DataFrame(labrows, columns=["name", "itemid"]))
    labs = con.execute("""SELECT c2.subject_id, m.name, arg_max(l.valuenum, l.charttime) v FROM c2
        JOIN labevents l ON l.subject_id = c2.subject_id JOIN labmap_df m ON m.itemid = l.itemid
        WHERE l.valuenum IS NOT NULL AND l.charttime < c2.t0 AND l.charttime >= c2.t0 - INTERVAL 365 DAY
        GROUP BY 1, 2""").df().pivot(index="subject_id", columns="name", values="v")
    for n, (ids, lo, hi) in LABS.items():
        s = labs[n].reindex(base.index) if n in labs else pd.Series(np.nan, index=base.index)
        base[n] = s.where((s >= lo) & (s <= hi))
    # dx
    dxd = con.execute("""SELECT DISTINCT c2.subject_id, k.concept FROM c2 JOIN admissions ad ON ad.subject_id = c2.subject_id
        AND ad.admittime <= c2.admittime JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
        JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)""").df()
    for n in DXN:
        base[n] = base.index.isin(dxd[dxd.concept == n].subject_id).astype(float)
    # meds
    meds = {m: v for m, v in MEDS.items() if m not in spec["drop_meds"]}
    alltok = sorted({x for v in meds.values() for x in v})
    mt = con.execute(f"""SELECT DISTINCT subject_id, tok FROM (SELECT c2.subject_id,
                         UNNEST(list_intersect(r.toks, {sql_list(alltok)})) tok FROM c2 JOIN rxt r USING (subject_id)
                         WHERE r.starttime < c2.t0 AND r.starttime >= c2.t0 - INTERVAL 365 DAY)""").df()
    for n, kws in meds.items():
        base[n] = base.index.isin(mt[mt.tok.isin(set(kws))].subject_id).astype(float)
    # vitals (as v1.5)
    vit = con.execute("""WITH vv AS (
          SELECT c2.subject_id, CASE WHEN itemid IN (220179, 220050) THEN 'sbp' WHEN itemid IN (220180, 220051) THEN 'dbp'
                 ELSE 'heart_rate' END AS vname, i.charttime ts, i.valuenum v, 1 src
          FROM c2 JOIN icu_vitals i USING (subject_id) WHERE i.charttime < c2.t0 AND i.charttime >= c2.t0 - INTERVAL 365 DAY
          UNION ALL
          SELECT c2.subject_id, x.vname AS vname, CAST(o.chartdate AS TIMESTAMP) ts,
                 try_cast(CASE WHEN x.vname = 'sbp' THEN split_part(o.result_value, '/', 1) ELSE split_part(o.result_value, '/', 2) END AS DOUBLE) v, 0
          FROM c2 JOIN omr o USING (subject_id), (VALUES ('sbp'), ('dbp')) x(vname)
          WHERE o.result_name LIKE 'Blood Pressure%' AND o.chartdate < CAST(c2.t0 AS DATE)
            AND o.chartdate >= CAST(c2.t0 AS DATE) - INTERVAL 365 DAY
          UNION ALL
          SELECT c2.subject_id, 'bmi', CAST(o.chartdate AS TIMESTAMP), try_cast(o.result_value AS DOUBLE), 0
          FROM c2 JOIN omr o USING (subject_id)
          WHERE o.result_name IN ('BMI (kg/m2)', 'BMI') AND o.chartdate < CAST(c2.t0 AS DATE)
            AND o.chartdate >= CAST(c2.t0 AS DATE) - INTERVAL 365 DAY)
        SELECT subject_id, vname, arg_max(v, epoch(ts) * 10 + src) v FROM vv WHERE v IS NOT NULL GROUP BY 1, 2""").df()
    for n, (lo, hi) in VITAL_RANGES.items():
        vv = vit[vit.vname == n].set_index("subject_id").v.reindex(base.index)
        base[n] = vv.where((vv >= lo) & (vv <= hi))
    # utilisation (as v1.5)
    ut = con.execute("""SELECT c2.subject_id,
          (SELECT count(*) FROM admissions ad WHERE ad.subject_id = c2.subject_id AND ad.admittime < c2.admittime
              AND ad.admittime >= c2.t0 - INTERVAL 365 DAY) prior_admissions_365d,
          (SELECT count(*) FROM transfers t WHERE t.subject_id = c2.subject_id AND t.eventtype = 'ED'
              AND t.intime < c2.t0 AND t.intime >= c2.t0 - INTERVAL 365 DAY
              AND (t.hadm_id IS NULL OR t.hadm_id <> c2.hadm_id)) ed_visits_365d,
          date_diff('minute', c2.admittime, c2.t0) / 1440.0 days_admit_to_index,
          (SELECT count(*) > 0 FROM transfers t WHERE t.subject_id = c2.subject_id AND t.hadm_id = c2.hadm_id
              AND t.intime < c2.t0 AND regexp_matches(t.careunit, 'Intensive Care|CCU|SICU|MICU|CVICU')) icu_before_index
        FROM c2""").df().set_index("subject_id")
    util = ["prior_admissions_365d", "ed_visits_365d", "days_admit_to_index", "icu_before_index"]
    for u in util:
        base[u] = ut[u].reindex(base.index).astype(float)
    roles = dict(demo=["age_at_index", "male", "index_year"], dx=DXN, meds=list(meds),
                 labs_vitals=list(LABS) + list(VITAL_RANGES), util=util)
    const = [c for c in base.columns if base[c].nunique(dropna=True) <= 1]
    base = base.drop(columns=const)
    roles = {r: [c for c in v if c not in const] for r, v in roles.items()}
    roles["phys"] = list(roles["labs_vitals"])
    roles["exposure_features"] = []
    # write cohort / index_time / baseline / roles
    coh["pid"] = [pid_of(s) for s in coh.index]
    epoch = pd.Timestamp("2100-01-01")
    pd.DataFrame({"pid": coh.pid.values, "treated": coh.treated.astype(int).values,
                  "index_day": ((coh.t0 - epoch) / pd.Timedelta(days=1)).astype(float).values,
                  "index_year": coh.est_year.astype(float).values}).to_parquet(D / "cohort.parquet", index=False)
    pd.DataFrame({"pid": coh.pid.values, "subject_id": coh.index.values.astype("int64"), "index_datetime": coh.t0.values,
                  "hadm_id": coh.hadm_id.values.astype("int64"),
                  "treated": coh.treated.astype(int).values}).to_parquet(D / "index_time.parquet", index=False)
    b = base.copy()
    b.insert(0, "pid", coh.pid.reindex(b.index).values)
    b.reset_index(drop=True).astype({c: float for c in base.columns}).to_parquet(D / "baseline.parquet", index=False)
    json.dump(roles, open(D / "roles.json", "w"), indent=2)
    # panel (as v1.5)
    EXPO = sorted({x.lower() for x in spec["expo"]})
    con.execute("CREATE TEMP TABLE pc AS SELECT subject_id, hadm_id, t0, admittime FROM c2")
    n = len(coh)
    q = {
        "dx": """SELECT pc.subject_id, CASE WHEN d.icd_version = 10 THEN 'dx_' || substr(d.icd_code, 1, 3)
                 ELSE 'dx_i9_' || substr(d.icd_code, 1, 3) END f, count(DISTINCT d.hadm_id) c
          FROM pc JOIN admissions ad ON ad.subject_id = pc.subject_id AND ad.admittime <= pc.admittime
               AND (ad.hadm_id = pc.hadm_id OR ad.admittime >= pc.t0 - INTERVAL 365 DAY)
          JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id GROUP BY 1, 2""",
        "rx": f"""WITH r AS (SELECT pc.subject_id, CAST(r.starttime AS DATE) dday,
                 list_filter(r.toks, x -> regexp_matches(x, '^[a-z][a-z]+$') AND x <> 'nf')[1] tok
          FROM pc JOIN rxt r USING (subject_id)
          WHERE r.starttime < CAST(CAST(pc.t0 AS DATE) AS TIMESTAMP) AND r.starttime >= pc.t0 - INTERVAL 365 DAY
            AND NOT list_has_any(r.toks, {sql_list(EXPO)}))
          SELECT subject_id, 'rx_' || tok f, count(DISTINCT dday) c FROM r WHERE tok IS NOT NULL GROUP BY 1, 2""",
        "px": """SELECT pc.subject_id, CASE WHEN p.icd_version = 10 THEN 'px_' || substr(p.icd_code, 1, 4)
                 ELSE 'px_i9_' || substr(p.icd_code, 1, 3) END f, count(DISTINCT p.chartdate) c
          FROM pc JOIN procedures_icd p USING (subject_id)
          WHERE p.chartdate < CAST(pc.t0 AS DATE) AND p.chartdate >= CAST(pc.t0 AS DATE) - INTERVAL 365 DAY GROUP BY 1, 2""",
        "lab": """SELECT pc.subject_id, 'lab_' || CAST(l.itemid AS VARCHAR) f, 1 c
          FROM pc JOIN labevents l USING (subject_id)
          WHERE l.charttime < pc.t0 AND l.charttime >= pc.t0 - INTERVAL 365 DAY GROUP BY 1, 2""",
    }
    frames, dic = [], []
    for dom, qq in q.items():
        d = con.execute(f"""WITH x AS ({qq}) SELECT f, list(subject_id) s, list(c) c FROM x GROUP BY f
                            HAVING count(DISTINCT subject_id) >= {0.01 * n}""").df()
        for f, s, cc in zip(d.f, d.s, d.c):
            name = f.lower() if dom == "rx" else f
            frames.append(pd.Series(np.asarray(cc, float), index=pd.Index(s), name=name))
            dic.append((name, dom, len(s) / n))
    panel = pd.concat(frames, axis=1).reindex(coh.index).fillna(0.0)
    assert not [c for c in panel.columns if c.startswith("rx_") and c[3:] in EXPO]
    panel.insert(0, "pid", coh.pid.values)
    panel.reset_index(drop=True).to_parquet(D / "panel.parquet", index=False)
    pd.DataFrame(dic, columns=["feature", "domain", "prevalence"])[["feature", "domain"]].to_csv(D / "panel_dictionary.csv", index=False)
    # outcome: all-cause death within horizon (v1.5 death-dir convention)
    H = float(spec["horizon"])
    it = pd.read_parquet(D / "index_time.parquet")
    con.register("it_df", it)
    o = con.execute("""SELECT it.pid, date_diff('day', CAST(it.index_datetime AS DATE), p.dod) death_day,
          date_diff('day', CAST(it.index_datetime AS DATE), CAST(greatest(
              (SELECT max(dischtime) FROM admissions ad WHERE ad.subject_id = it.subject_id),
              (SELECT max(outtime) FROM transfers t WHERE t.subject_id = it.subject_id AND t.eventtype = 'ED')) AS DATE)) + 365 cens_day
          FROM it_df it JOIN patients p USING (subject_id)""").df().set_index("pid").reindex(it.pid)
    cens = np.minimum(H, o.cens_day.astype(float)).values
    death = o.death_day.astype(float).values
    assert np.all(np.nan_to_num(death, nan=1e9) >= 0)
    e = (death <= cens).astype(int)
    t = np.where(e == 1, death, cens)
    t = np.where(t <= 0, 0.5, t).astype(float)
    pd.DataFrame({"pid": it.pid.values, "t": t, "e": e}).to_parquet(D / "outcomes.parquet", index=False)
    R = spec["rct"]
    json.dump(dict(trial=spec["name"], key=k, arms=spec["arms"], hr=R["hr"], lo=R["lo"], hi=R["hi"], ci_level=0.95,
                   our_orientation=R["hr"], our_lo=R["lo"], our_hi=R["hi"], measure=R["measure"], horizon_days=int(H),
                   endpoint=R["endpoint"], notes=R["source"] + "; benchmark verified from the PubMed abstract 2026-09-30"),
              open(D / "rct.json", "w"), indent=2)
    by = {spec["arms"][1 - int(tr)]: dict(n=supp(len(g)), deaths=supp(int(e[it.treated.values == tr].sum())))
          for tr, g in it.groupby("treated")}
    summ = dict(trial=k, created=dt.datetime.now().isoformat(timespec="seconds"), attrition=[(s, supp(v)) for s, v in attr],
                n=supp(n), by_arm=by, dropped_constant=const, panel=dict(n_features=len(dic)), horizon_days=H)
    json.dump(summ, open(D / "summary.json", "w"), indent=2, default=str)
    (D / "READY_COHORT").write_text(dt.datetime.now().isoformat() + "\n")
    (D / "READY_OUTCOMES").write_text(dt.datetime.now().isoformat() + "\n")
    print(json.dumps(summ, default=str), flush=True)


if __name__ == "__main__":
    for k in sys.argv[1:]:
        build(k)
