#!/usr/bin/env python
"""v1.5 MIMIC NCO v2b (coordinator decision 2026-09-26): bleeding-free diverticular disease NCO.

Events: K57* / 562* readmission diagnoses EXCLUDING the with-bleeding codes (checked against d_icd_diagnoses):
  ICD-10 K5701 K5711 K5713 K5721 K5731 K5733 K5741 K5751 K5753 K5781 K5791 K5793; ICD-9 56202 56203 56212 56213.
Prior/index exclusion (NaN): ANY K57 / 562 code, bleeding codes included.
Only t_nco_diverticular / e_nco_diverticular are overwritten; all other columns verified identical.
Backup: outcomes_preDIVfix.parquet. Prints aggregates only.
"""
import datetime as dt
import json
import os
import shutil

import numpy as np
import pandas as pd

from v15_mimic_common import TRIAL_KEYS, connect, out_dir, supp

BLEED10 = ["K5701", "K5711", "K5713", "K5721", "K5731", "K5733", "K5741", "K5751", "K5753", "K5781", "K5791", "K5793"]
BLEED9 = ["56202", "56203", "56212", "56213"]
DIV = "((CAST(d.icd_version AS INT) = 10 AND starts_with(d.icd_code, 'K57')) OR (CAST(d.icd_version AS INT) = 9 AND starts_with(d.icd_code, '562')))"
BLEED = "list_contains([" + ", ".join(f"'{c}'" for c in BLEED10 + BLEED9) + "], d.icd_code)"
os.umask(0o077)
con = connect(32)
for K in TRIAL_KEYS:
    OUT = out_dir(K)
    assert (OUT / "NCO_V2_DONE").exists() and not (OUT / "NCO_V2B_DONE").exists()
    old = pd.read_parquet(OUT / "outcomes.parquet")
    if not (OUT / "outcomes_preDIVfix.parquet").exists():
        shutil.copy2(OUT / "outcomes.parquet", OUT / "outcomes_preDIVfix.parquet")
    H = float(json.load(open(OUT / "rct.json"))["horizon_days"])
    it = pd.read_parquet(OUT / "index_time.parquet")
    con.register("it_df", it)
    con.execute("""CREATE OR REPLACE TEMP TABLE c AS SELECT it.pid, it.subject_id, it.hadm_id, it.index_datetime t0,
                   CAST(it.index_datetime AS DATE) d0, ad.admittime FROM it_df it
                   JOIN admissions ad ON ad.subject_id = it.subject_id AND ad.hadm_id = it.hadm_id""")
    base = con.execute("""SELECT c.pid, date_diff('day', c.d0, p.dod) death_day,
          date_diff('day', c.d0, CAST(greatest(
              (SELECT max(dischtime) FROM admissions ad WHERE ad.subject_id = c.subject_id),
              (SELECT max(outtime) FROM transfers t WHERE t.subject_id = c.subject_id AND t.eventtype = 'ED')) AS DATE)) + 365 cens_day
          FROM c JOIN patients p USING (subject_id)""").df().set_index("pid").reindex(old.pid)
    ev = con.execute(f"""SELECT c.pid, min(date_diff('day', c.d0, CAST(ad.admittime AS DATE))) eday
          FROM c JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime > c.admittime AND ad.hadm_id <> c.hadm_id
          JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
          WHERE {DIV} AND NOT {BLEED} GROUP BY 1""").df().set_index("pid").eday.reindex(base.index).astype(float)
    prior = con.execute(f"""SELECT DISTINCT c.pid FROM c JOIN admissions ad ON ad.subject_id = c.subject_id
          AND ad.admittime <= c.admittime AND (ad.hadm_id = c.hadm_id OR ad.admittime >= c.t0 - INTERVAL 365 DAY)
          JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id WHERE {DIV}""").df()
    cens = np.minimum(H, base.cens_day.astype(float))
    end = pd.concat([cens, base.death_day.astype(float)], axis=1).min(axis=1)
    e = (ev <= end).astype(float)
    t = np.where(e == 1, ev, end).astype(float)
    t = np.where(t <= 0, 0.5, t)
    excl = base.index.isin(prior.pid)
    new = old.copy()
    new["t_nco_diverticular"] = np.where(excl, np.nan, t)
    new["e_nco_diverticular"] = np.where(excl, np.nan, e.values)
    keep = [c for c in old.columns if c not in ("t_nco_diverticular", "e_nco_diverticular")]
    pd.testing.assert_frame_equal(new[keep], old[keep])
    assert list(new.columns) == list(old.columns)
    assert (new.t_nco_diverticular.dropna() > 0).all() and (new.t_nco_diverticular.dropna() <= H).all()
    # eligibility must be unchanged (prior exclusion already used all K57/562 codes)
    assert (new.e_nco_diverticular.isna() == old.e_nco_diverticular.isna()).all()
    tmp = OUT / "outcomes.parquet.tmp"
    new.to_parquet(tmp, index=False)
    os.replace(tmp, OUT / "outcomes.parquet")
    coh = pd.read_parquet(OUT / "cohort.parquet").set_index("pid").reindex(new.pid)
    arms = json.load(open(OUT / "rct.json"))["arms"]
    summ = json.load(open(OUT / "summary.json"))
    out = {}
    for tr, g in new.assign(treated=coh.treated.values, e_old=old.e_nco_diverticular.values).groupby("treated"):
        arm = arms[0] if tr == 1 else arms[1]
        r = dict(eligible=supp(g.e_nco_diverticular.notna().sum()), events=supp(g.e_nco_diverticular.sum()),
                 lt20=bool(g.e_nco_diverticular.sum() < 20))
        summ["nco_v2"]["by_arm"][arm]["nco_diverticular"] = r
        out[arm] = dict(events=r["events"], before=supp(g.e_old.sum()), lt20=r["lt20"])
    summ["nco_v2"]["definitions"]["nco_diverticular"] = dict(
        icd10=["K57"], icd9=["562"], event_excludes_bleeding=BLEED10 + BLEED9,
        prior_exclusion="any K57/562 code incl. bleeding codes", revised=dt.datetime.now().isoformat(timespec="seconds"))
    json.dump(summ, open(OUT / "summary.json", "w"), indent=2, default=str)
    (OUT / "NCO_V2B_DONE").write_text(dt.datetime.now().isoformat() + "\n")
    print(K, json.dumps(out), flush=True)
