#!/usr/bin/env python
"""v1.5 MIMIC audit fix (docs/AUDIT_V15_2026_09_26.md M2/M3; protocol v1.5 corrections 2-3).

Per trial dir (requires BACKUP_DONE; writes AUDITFIX_DONE):
  1. copies baseline/panel/panel_dictionary/outcomes/roles -> *_v1
  2. baseline dx covariates (and PLATO stemi/pci index-event features) from EARLIER admissions only
     (admittime before the index admission; index-admission diagnoses and procedures excluded). Same column set
     as v1 (columns that become constant are dropped and listed). meds/labs/vitals/util unchanged.
     Panel dx_/px_ rebuilt from earlier admissions only (dx: admittime in [t0-365 d, index admittime);
     px: chartdate in [t0-365 d, index day), earlier admissions only); rx_/lab_ columns unchanged; >= 1% prevalence.
  3. primary outcome: an MI / stroke / systemic-embolism readmission starting within 28 days of the index
     discharge counts only if it has I22 (ICD-10, MI) or the qualifying code in position 1 (seq_num = 1);
     after 28 days any position (as before). Deaths unchanged. NCO columns kept unchanged.
  4. cohort.parquet untouched (hash verified); summary.json gets an 'auditfix' section (aggregates, suppressed).
"""
import datetime as dt
import hashlib
import json
import os
import shutil

import numpy as np
import pandas as pd

from v15_mimic_common import CONCEPTS, PCI_PX, PRIMARY, TRIAL_KEYS, TS, concept_table, connect, out_dir, sql_list, supp

os.umask(0o077)
con = connect(32)
concept_table(con)
FLAG = {"E93x (ICD-9 E93)": "dx_i9_E93", "790.9x (ICD-9 790)": "dx_i9_790", "V58.6x (ICD-9 V58)": "dx_i9_V58",
        "I46": "dx_I46", "R57": "dx_R57", "Z51": "dx_Z51"}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
allres = {}
for K in TRIAL_KEYS:
    OUT = out_dir(K)
    assert (OUT / "BACKUP_DONE").exists(), K
    assert not (OUT / "AUDITFIX_DONE").exists(), K
    h_coh = sha(OUT / "cohort.parquet")
    for f in ["baseline.parquet", "panel.parquet", "panel_dictionary.csv", "outcomes.parquet", "roles.json"]:
        dst = OUT / f.replace(".", "_v1.", 1)
        if not dst.exists():
            shutil.copy2(OUT / f, dst)
    b1 = pd.read_parquet(OUT / "baseline_v1.parquet")
    p1 = pd.read_parquet(OUT / "panel_v1.parquet")
    o1 = pd.read_parquet(OUT / "outcomes_v1.parquet")
    r1 = json.load(open(OUT / "roles_v1.json"))
    coh = pd.read_parquet(OUT / "cohort.parquet")
    it = pd.read_parquet(OUT / "index_time.parquet")
    assert (b1.pid.values == coh.pid.values).all() and (p1.pid.values == coh.pid.values).all() and (o1.pid.values == coh.pid.values).all()
    assert set(it.pid) == set(coh.pid)
    con.register("it_df", it)
    con.execute("""CREATE OR REPLACE TEMP TABLE c AS SELECT it.pid, it.subject_id, it.hadm_id, it.index_datetime t0,
                   CAST(it.index_datetime AS DATE) d0, ad.admittime, ad.dischtime FROM it_df it
                   JOIN admissions ad ON ad.subject_id = it.subject_id AND ad.hadm_id = it.hadm_id""")
    n = len(coh)
    # ---- 2a. baseline dx from earlier admissions only
    cdx = con.execute("""SELECT DISTINCT c.pid, k.concept FROM c JOIN admissions ad ON ad.subject_id = c.subject_id
        AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id
        JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
        JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)""").df()
    b2 = b1.set_index("pid").copy()
    dxcols = [c for c in r1["dx"] if c in CONCEPTS]
    for cname in dxcols:
        b2[cname] = b2.index.isin(cdx[cdx.concept == cname].pid).astype(float)
    if K == "plato":
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
            if cname in b2:
                b2[cname] = b2.index.isin(s.pid).astype(float)
    newconst = [c for c in b2.columns if b2[c].nunique(dropna=True) <= 1]
    b2 = b2.drop(columns=newconst)
    roles = {k: [c for c in v if c not in newconst] for k, v in r1.items()}
    other = [c for c in b1.columns if c != "pid" and c not in dxcols + ["stemi_index_adm", "pci_index_30d"] and c not in newconst]
    pd.testing.assert_frame_equal(b2[other].reset_index(drop=True), b1[other].reset_index(drop=True))
    # ---- 2b. panel dx/px from earlier admissions only
    q_dx = """SELECT c.pid, CASE WHEN d.icd_version = 10 THEN 'dx_' || substr(d.icd_code, 1, 3)
                   ELSE 'dx_i9_' || substr(d.icd_code, 1, 3) END f, count(DISTINCT d.hadm_id) cnt
              FROM c JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id
                   AND ad.admittime >= c.t0 - INTERVAL 365 DAY
              JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id GROUP BY 1, 2"""
    q_px = """SELECT c.pid, CASE WHEN p.icd_version = 10 THEN 'px_' || substr(p.icd_code, 1, 4)
                   ELSE 'px_i9_' || substr(p.icd_code, 1, 3) END f, count(DISTINCT p.chartdate) cnt
              FROM c JOIN procedures_icd p ON p.subject_id = c.subject_id AND p.hadm_id <> c.hadm_id
              WHERE p.chartdate < c.d0 AND p.chartdate >= c.d0 - INTERVAL 365 DAY GROUP BY 1, 2"""
    frames, dic = [], []
    for dom, q in (("dx", q_dx), ("px", q_px)):
        d = con.execute(f"""WITH x AS ({q}) SELECT f, list(pid) s, list(cnt) cc FROM x GROUP BY f
                            HAVING count(DISTINCT pid) >= {0.01 * n}""").df()
        for f, s, cc in zip(d.f, d.s, d.cc):
            frames.append(pd.Series(np.asarray(cc, float), index=pd.Index(s), name=f))
            dic.append((f, dom))
    keep = [c for c in p1.columns if c.startswith(("rx_", "lab_"))]
    p2 = pd.concat(frames, axis=1).reindex(coh.pid).fillna(0.0)
    p2 = pd.concat([p2.reset_index(drop=True), p1[keep].reset_index(drop=True)], axis=1)
    p2.insert(0, "pid", coh.pid.values)
    d1 = pd.read_csv(OUT / "panel_dictionary_v1.csv")
    dd = pd.DataFrame(dic + [(f, dm) for f, dm in zip(d1.feature, d1.domain) if f in keep], columns=["feature", "domain"])
    assert list(dd.feature) == [c for c in p2.columns if c != "pid"]
    expo = {k.lower() for arm in TS.TRIALS[K]["arms"] for k in arm[1]}
    assert not [c for c in p2.columns if c.startswith("rx_") and c[3:] in expo]
    # ---- 3. outcomes with the 28-day rule
    comp = PRIMARY[K]
    readm = con.execute("""SELECT c.pid, k.concept,
          min(date_diff('day', c.d0, CAST(ad.admittime AS DATE))) FILTER (WHERE ad.admittime > c.dischtime + INTERVAL 28 DAY
              OR CAST(d.seq_num AS INT) = 1 OR (k.concept = 'out_mi' AND CAST(d.icd_version AS INT) = 10 AND starts_with(d.icd_code, 'I22'))) eday,
          min(date_diff('day', c.d0, CAST(ad.admittime AS DATE))) eday_v1
          FROM c JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime > c.admittime AND ad.hadm_id <> c.hadm_id
          JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
          JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)
          WHERE k.concept LIKE 'out_%' GROUP BY 1, 2""").df()
    base = con.execute("""SELECT c.pid, date_diff('day', c.d0, p.dod) death_day,
          date_diff('day', c.d0, CAST(greatest(
              (SELECT max(dischtime) FROM admissions ad WHERE ad.subject_id = c.subject_id),
              (SELECT max(outtime) FROM transfers t WHERE t.subject_id = c.subject_id AND t.eventtype = 'ED')) AS DATE)) + 365 cens_day
          FROM c JOIN patients p USING (subject_id)""").df().set_index("pid").reindex(coh.pid)
    H = float(json.load(open(OUT / "rct.json"))["horizon_days"])
    cens = np.minimum(H, base.cens_day.astype(float))
    death = base.death_day.astype(float)

    def build(col):
        ev = pd.concat([readm[readm.concept == cc].set_index("pid")[col].reindex(base.index).astype(float)
                        for cc in comp if cc != "death"] + [pd.Series(np.nan, index=base.index)], axis=1).min(axis=1)
        if "death" in comp:
            ev = pd.concat([ev, death], axis=1).min(axis=1)
            end = cens
        else:
            end = pd.concat([cens, death], axis=1).min(axis=1)
        e = (ev <= end).astype(int)
        t = np.where(e == 1, ev, end).astype(float)
        return np.where(t <= 0, 0.5, t), e.values

    t_chk, e_chk = build("eday_v1")  # must reproduce v1
    assert np.allclose(t_chk, o1.t.values) and (e_chk == o1.e.values).all(), "v1 reproduction failed"
    t2, e2 = build("eday")
    o2 = o1.copy()
    o2["t"], o2["e"] = t2, e2
    assert (o2.t > 0).all() and (o2.t <= H).all()
    pd.testing.assert_frame_equal(o2.drop(columns=["t", "e"]), o1.drop(columns=["t", "e"]))
    # ---- write
    b2.reset_index().to_parquet(OUT / "baseline.parquet.tmp", index=False)
    p2.to_parquet(OUT / "panel.parquet.tmp", index=False)
    o2.to_parquet(OUT / "outcomes.parquet.tmp", index=False)
    for f in ["baseline.parquet", "panel.parquet", "outcomes.parquet"]:
        os.replace(OUT / (f + ".tmp"), OUT / f)
    dd.to_csv(OUT / "panel_dictionary.csv", index=False)
    json.dump(roles, open(OUT / "roles.json", "w"), indent=2)
    assert sha(OUT / "cohort.parquet") == h_coh
    # ---- summary
    arms = json.load(open(OUT / "rct.json"))["arms"]
    tr = coh.treated.values
    ev_by = {}
    for v, name in ((1, arms[0]), (0, arms[1])):
        m = tr == v
        ev_by[name] = dict(n=supp(m.sum()), events_v1=supp(o1.e.values[m].sum()), events_v2=supp(o2.e.values[m].sum()))
    prevb = {c: dict(v1=round(float(b1[c].mean()), 3), v2=(round(float(b2[c].mean()), 3) if c in b2 else None))
             for c in dxcols + [x for x in ("stemi_index_adm", "pci_index_30d") if x in b1]}
    flags = {k: dict(v1_prev=(round(float((p1[f] > 0).mean()), 4) if f in p1 else None),
                     v2_prev=(round(float((p2[f] > 0).mean()), 4) if f in p2 else None)) for k, f in FLAG.items()}
    res = dict(created=dt.datetime.now().isoformat(timespec="seconds"),
               panel_features=dict(v1=d1.domain.value_counts().to_dict(), v2=dd.domain.value_counts().to_dict()),
               primary_events_by_arm=ev_by, dx_covariate_prevalence=prevb, newly_constant_dropped=newconst,
               audit_flagged_panel_features=flags,
               notes=["dx covariates and panel dx/px from earlier admissions only (index-admission diagnoses/procedures excluded; "
                      "gate still from index admission for eligibility)",
                      "MI/stroke/SE readmission within 28 d of index discharge counts only if I22 (MI) or seq_num = 1",
                      "v1 files kept as *_v1; NCO columns unchanged; cohort.parquet unchanged"])
    summ = json.load(open(OUT / "summary.json"))
    summ["auditfix"] = res
    json.dump(summ, open(OUT / "summary.json", "w"), indent=2, default=str)
    (OUT / "AUDITFIX_DONE").write_text(dt.datetime.now().isoformat() + "\n")
    allres[K] = res
    print(K, json.dumps(dict(panel=res["panel_features"], events=ev_by, const=newconst, flags=flags)), flush=True)
