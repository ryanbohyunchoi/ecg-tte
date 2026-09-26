#!/usr/bin/env python
"""v1.5 MIMIC-IV negative-control outcomes v2 (deviation log 2026-09-26): add 8 hospital-coded NCOs to
outcomes.parquet of every MIMIC trial dir. Existing columns are left unchanged (verified); the old file is
kept as outcomes_preNCO.parquet. Same definition as v15_mimic_outcomes.py: any-position diagnosis in a later
admission, dated to admission start; death censors; truncated at horizon_days; NaN if the code occurred in the
index admission or an admission in the prior 365 d. BPH: NaN for women. Prints aggregates only.
"""
import datetime as dt
import json
import os
import shutil

import numpy as np
import pandas as pd

from v15_mimic_common import TRIAL_KEYS, connect, out_dir, supp

NCO2 = {  # name: (ICD-10 prefixes, ICD-9 prefixes)
    "nco_uti": (["N390"], ["5990"]),
    "nco_osteoarthritis": (["M15", "M16", "M17", "M18", "M19"], ["715"]),
    "nco_diverticular": (["K57"], ["562"]),
    "nco_hypothyroidism": (["E03"], ["244"]),
    "nco_cataract": (["H25", "H26"], ["366"]),
    "nco_bph": (["N40"], ["600"]),
    "nco_glaucoma": (["H40"], ["365"]),
    "nco_back_pain": (["M54"], ["724"]),
}
os.umask(0o077)
con = connect(32)
rows = [(n, 10, p) for n, (a, b) in NCO2.items() for p in a] + [(n, 9, p) for n, (a, b) in NCO2.items() for p in b]
con.register("nco_df", pd.DataFrame(rows, columns=["concept", "v", "prefix"]))
report = {}
for K in TRIAL_KEYS:
    OUT = out_dir(K)
    assert (OUT / "READY_OUTCOMES").exists() and not (OUT / "NCO_V2_DONE").exists()
    old = pd.read_parquet(OUT / "outcomes.parquet")
    assert not any(c in old.columns for n in NCO2 for c in (f"t_{n}", f"e_{n}"))
    if not (OUT / "outcomes_preNCO.parquet").exists():
        shutil.copy2(OUT / "outcomes.parquet", OUT / "outcomes_preNCO.parquet")
    H = float(json.load(open(OUT / "rct.json"))["horizon_days"])
    it = pd.read_parquet(OUT / "index_time.parquet")
    con.register("it_df", it)
    con.execute("""CREATE OR REPLACE TEMP TABLE c AS SELECT it.pid, it.subject_id, it.hadm_id, it.index_datetime t0,
                   CAST(it.index_datetime AS DATE) d0, ad.admittime FROM it_df it
                   JOIN admissions ad ON ad.subject_id = it.subject_id AND ad.hadm_id = it.hadm_id""")
    base = con.execute("""SELECT c.pid, p.gender, date_diff('day', c.d0, p.dod) death_day,
          date_diff('day', c.d0, CAST(greatest(
              (SELECT max(dischtime) FROM admissions ad WHERE ad.subject_id = c.subject_id),
              (SELECT max(outtime) FROM transfers t WHERE t.subject_id = c.subject_id AND t.eventtype = 'ED')) AS DATE)) + 365 cens_day
          FROM c JOIN patients p USING (subject_id)""").df().set_index("pid").reindex(old.pid)
    readm = con.execute("""SELECT c.pid, k.concept, min(date_diff('day', c.d0, CAST(ad.admittime AS DATE))) eday
          FROM c JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime > c.admittime AND ad.hadm_id <> c.hadm_id
          JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
          JOIN nco_df k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix) GROUP BY 1, 2""").df()
    prior = con.execute("""SELECT DISTINCT c.pid, k.concept FROM c JOIN admissions ad ON ad.subject_id = c.subject_id
          AND ad.admittime <= c.admittime AND (ad.hadm_id = c.hadm_id OR ad.admittime >= c.t0 - INTERVAL 365 DAY)
          JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
          JOIN nco_df k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)""").df()
    cens = np.minimum(H, base.cens_day.astype(float))
    end = pd.concat([cens, base.death_day.astype(float)], axis=1).min(axis=1)  # death censors
    new = old.copy()
    for n in NCO2:
        ev = readm[readm.concept == n].set_index("pid").eday.reindex(base.index).astype(float)
        e = (ev <= end).astype(float)
        t = np.where(e == 1, ev, end).astype(float)
        t = np.where(t <= 0, 0.5, t)
        excl = base.index.isin(prior[prior.concept == n].pid)
        if n == "nco_bph":
            excl = excl | (base.gender.values != "M")
        new[f"t_{n}"] = np.where(excl, np.nan, t)
        new[f"e_{n}"] = np.where(excl, np.nan, e.values)
        assert (new[f"t_{n}"].dropna() > 0).all() and (new[f"t_{n}"].dropna() <= H).all()
    pd.testing.assert_frame_equal(new[old.columns], old)
    tmp = OUT / "outcomes.parquet.tmp"
    new.to_parquet(tmp, index=False)
    os.replace(tmp, OUT / "outcomes.parquet")
    coh = pd.read_parquet(OUT / "cohort.parquet").set_index("pid").reindex(new.pid)
    arms = json.load(open(OUT / "rct.json"))["arms"]
    allnco = [c[2:] for c in new.columns if c.startswith("e_nco_")]
    res = {}
    for tr, g in new.assign(treated=coh.treated.values).groupby("treated"):
        res[arms[0] if tr == 1 else arms[1]] = {
            n: dict(eligible=supp(g[f"e_{n}"].notna().sum()), events=supp(g[f"e_{n}"].sum()),
                    lt20=bool(g[f"e_{n}"].sum() < 20)) for n in allnco}
    summ = json.load(open(OUT / "summary.json"))
    summ["nco_v2"] = dict(created=dt.datetime.now().isoformat(timespec="seconds"), added=list(NCO2),
                          definitions={k: dict(icd10=v[0], icd9=v[1]) for k, v in NCO2.items()}, by_arm=res,
                          notes="readmission dx any position; death censors; NaN if code in index admission or prior 365 d; BPH men only")
    json.dump(summ, open(OUT / "summary.json", "w"), indent=2, default=str)
    (OUT / "NCO_V2_DONE").write_text(dt.datetime.now().isoformat() + "\n")
    report[K] = res
    print(K, json.dumps({a: {n: v["events"] for n, v in r.items()} for a, r in res.items()}), flush=True)
