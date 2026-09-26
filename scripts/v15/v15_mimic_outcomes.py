#!/usr/bin/env python
"""v1.5 MIMIC-IV outcomes for one trial (protocol-v1.5), run only after READY_COHORT and the feasibility rule.

Primary outcome (v15_mimic_common.PRIMARY), truncated at rct.json horizon_days:
  death        patients.dod (date); event day = dod - index date
  readmission  any diagnosis position of a later admission (admittime after the index admission's admittime,
               index admission excluded); event day = admission date - index date
  Index-day events -> t = 0.5. For composites without death, death censors.
  Censoring: min(horizon, 365 d after the last recorded hospital contact (admission discharge / ED out-time)).
Negative-control outcomes (readmission diagnosis; death censors): patients with the NCO code in the index
admission or an admission in the prior 365 d get NaN (excluded) for that NCO.
Writes outcomes.parquet, updates summary.json (aggregates, suppressed), writes READY_OUTCOMES.
"""
import argparse
import datetime as dt
import json
import os

import numpy as np
import pandas as pd

from v15_mimic_common import NCOS, PRIMARY, concept_table, connect, out_dir, supp

ap = argparse.ArgumentParser()
ap.add_argument("--trial", required=True)
ap.add_argument("--threads", type=int, default=32)
a = ap.parse_args()
os.umask(0o077)
OUT = out_dir(a.trial)
assert (OUT / "READY_COHORT").exists()
assert not (OUT / "outcomes.parquet").exists()
summ = json.load(open(OUT / "summary.json"))
if not summ["feasible_ecg_rule"]:
    (OUT / "INFEASIBLE").write_text("fewer than 200 per arm with an ECG in [t0-365 d, t0]\n")
    raise SystemExit("infeasible")
rct = json.load(open(OUT / "rct.json"))
H = float(rct["horizon_days"])
con = connect(a.threads)
it = pd.read_parquet(OUT / "index_time.parquet")
con.register("it_df", it)
con.execute("""CREATE TEMP TABLE c AS SELECT it.pid, it.subject_id, it.hadm_id, it.index_datetime t0,
               CAST(it.index_datetime AS DATE) d0, ad.admittime FROM it_df it
               JOIN admissions ad ON ad.subject_id = it.subject_id AND ad.hadm_id = it.hadm_id""")
assert con.execute("SELECT count(*) FROM c").fetchone()[0] == len(it)
concept_table(con)
base = con.execute("""SELECT c.pid, date_diff('day', c.d0, p.dod) death_day,
      date_diff('day', c.d0, CAST(greatest(
          (SELECT max(dischtime) FROM admissions ad WHERE ad.subject_id = c.subject_id),
          (SELECT max(outtime) FROM transfers t WHERE t.subject_id = c.subject_id AND t.eventtype = 'ED')) AS DATE)) + 365 cens_day
      FROM c JOIN patients p USING (subject_id)""").df().set_index("pid").reindex(it.pid)
assert (base.death_day.dropna() >= 0).all(), "death before index"
readm = con.execute("""SELECT c.pid, k.concept, min(date_diff('day', c.d0, CAST(ad.admittime AS DATE))) eday
      FROM c JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime > c.admittime AND ad.hadm_id <> c.hadm_id
      JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
      JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)
      WHERE k.concept LIKE 'out_%' OR k.concept LIKE 'nco_%' GROUP BY 1, 2""").df()
prior = con.execute("""SELECT DISTINCT c.pid, k.concept FROM c JOIN admissions ad ON ad.subject_id = c.subject_id
      AND ad.admittime <= c.admittime AND (ad.hadm_id = c.hadm_id OR ad.admittime >= c.t0 - INTERVAL 365 DAY)
      JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
      JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)
      WHERE k.concept LIKE 'nco_%'""").df()


def ev_day(concept):
    return readm[readm.concept == concept].set_index("pid").eday.reindex(base.index).astype(float)


cens = np.minimum(H, base.cens_day.astype(float))
death = base.death_day.astype(float)


def build(components, death_is_event):
    ev = pd.concat([ev_day(cc) for cc in components if cc != "death"] + [pd.Series(np.nan, index=base.index)], axis=1).min(axis=1)
    if death_is_event:
        ev = pd.concat([ev, death], axis=1).min(axis=1)
        end = cens
    else:
        end = pd.concat([cens, death], axis=1).min(axis=1)  # death censors
    e = (ev <= end).astype(int)
    t = np.where(e == 1, ev, end).astype(float)
    t = np.where(t <= 0, 0.5, t)
    return pd.Series(t, index=base.index), e


comp = PRIMARY[a.trial]
t, e = build(comp, "death" in comp)
out = pd.DataFrame({"pid": base.index, "t": t.values, "e": e.values})
for nco in NCOS:
    tn, en = build([nco], False)
    excl = base.index.isin(prior[prior.concept == nco].pid)
    out[f"t_{nco}"] = np.where(excl, np.nan, tn.values)
    out[f"e_{nco}"] = np.where(excl, np.nan, en.values.astype(float))
assert (out.t > 0).all() and (out.t <= H).all()
out.to_parquet(OUT / "outcomes.parquet", index=False)

coh = pd.read_parquet(OUT / "cohort.parquet").set_index("pid").reindex(out.pid)
names = {1: rct["arms"][0], 0: rct["arms"][1]}
res = {}
for tr, g in out.assign(treated=coh.treated.values).groupby("treated"):
    r = dict(n=supp(len(g)), events=supp(g.e.sum()), person_years=round(float(g.t.sum() / 365.25), 1),
             censored_before_horizon=supp(((g.e == 0) & (g.t < H)).sum()))
    r["deaths_within_followup"] = supp((death.reindex(g.pid).values <= cens.reindex(g.pid).values).sum())
    for nco in NCOS:
        r[nco] = dict(eligible=supp(g[f"e_{nco}"].notna().sum()), events=supp(g[f"e_{nco}"].sum()))
    res[names[int(tr)]] = r
summ["outcomes"] = dict(primary_components=comp, horizon_days=H, by_arm=res, endpoint=rct["endpoint"],
                        created=dt.datetime.now().isoformat(timespec="seconds"),
                        notes=["readmission outcomes use later MIMIC admissions only (events at other hospitals missed); "
                               "in-hospital events during the index admission are not counted (discharge-coded, undated)",
                               "death from patients.dod (hospital + state records, captured to ~1 y after last discharge)",
                               "NCO: NaN = NCO code in the index admission or an admission in the prior 365 d (excluded)"])
json.dump(summ, open(OUT / "summary.json", "w"), indent=2, default=str)
(OUT / "READY_OUTCOMES").write_text(dt.datetime.now().isoformat() + "\n")
print(json.dumps(summ["outcomes"], indent=1, default=str))
