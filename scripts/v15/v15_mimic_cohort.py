#!/usr/bin/env python
"""v1.5 MIMIC-IV cohort, baseline, panel, rct.json, index_time and summary for one trial (protocol-v1.5).

Design (in-hospital initiation, new-user, active comparator):
  exposure order   prescriptions row whose lower(drug), split on non-alphanumerics, contains an arm token
                   (trial_specs arms; generic + brand) with an enteral route (ORAL_ROUTES)
  time zero (t0)   starttime of the first enteral exposure order of either arm
  washout          no order (any route, incl. null starttime) of either drug in any earlier admission, and no
                   order of either drug before t0 in the index admission (any route) -- except TRANSFORM-HF,
                   where IV loop diuretic before t0 in the index admission is allowed and is a covariate
  ties             both arms ordered at t0 -> excluded
  calendar         estimated real year (anchor_year_group midpoint + index year - anchor_year) >= year of the
                   trial_specs index_start (drug availability; mirrors the Yale index_start)
  gate             concept code in the index admission or an earlier admission ('any'), or in the index
                   admission / an admission discharged within 30 d before t0 ('window_30d')
Outputs go to /mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-<trial>/ (private). Prints aggregates only.
"""
import argparse
import datetime as dt
import json
import os

import numpy as np
import pandas as pd

from v15_mimic_common import (CONCEPTS, ENDPOINT, GATE, IV_ROUTES, LABS, ORAL_ROUTES, PCI_PX, VITAL_RANGES, TS,
                              concept_table, connect, out_dir, pid_of, sql_list, supp)

ap = argparse.ArgumentParser()
ap.add_argument("--trial", required=True)
ap.add_argument("--threads", type=int, default=32)
ap.add_argument("--min-prev", type=float, default=0.01)
ap.add_argument("--rebuild", action="store_true", help="replace this script's own earlier (not-ready) outputs")
a = ap.parse_args()
os.umask(0o077)
K = a.trial
spec = TS.TRIALS[K]
OUT = out_dir(K)
if a.rebuild and OUT.exists():
    assert not (OUT / "READY_OUTCOMES").exists() and not (OUT / "READY_ECG").exists(), "downstream outputs exist"
    for f in ["cohort.parquet", "index_time.parquet", "baseline.parquet", "roles.json", "panel.parquet",
              "panel_dictionary.csv", "rct.json", "summary.json", "READY_COHORT"]:
        (OUT / f).unlink(missing_ok=True)
OUT.mkdir(parents=True, exist_ok=a.rebuild, mode=0o700)
con = connect(a.threads)
A0 = [k.lower() for k in spec["arms"][0][1]]
A1 = [k.lower() for k in spec["arms"][1][1]]
EXPO = sorted(set(A0 + A1))
oral = "[" + ", ".join(f"'{r}'" for r in ORAL_ROUTES) + "]"
attr = []


def step(name, n):
    attr.append((name, int(n)))
    print(f"{name}: {supp(n)}", flush=True)


concept_table(con)
con.execute("""CREATE TEMP TABLE rxt AS SELECT subject_id, hadm_id, starttime, upper(trim(route)) route, lower(drug) drug,
               regexp_split_to_array(lower(coalesce(drug, '')), '[^a-z0-9]+') toks FROM prescriptions""")
con.execute(f"""CREATE TEMP TABLE ex AS SELECT r.*, list_has_any(toks, {sql_list(A0)}) a0, list_has_any(toks, {sql_list(A1)}) a1,
                list_contains({oral}, route) is_oral, ad.admittime, ad.dischtime
                FROM rxt r JOIN admissions ad USING (subject_id, hadm_id)
                WHERE list_has_any(toks, {sql_list(EXPO)})""")
# drug-string verification table (aggregate): matched strings by arm
tokmatch = con.execute("""SELECT CASE WHEN a0 AND a1 THEN 'both' WHEN a0 THEN 'arm0' ELSE 'arm1' END arm, drug,
                          count(*) n_orders, count(DISTINCT subject_id) n_pat FROM ex GROUP BY ALL ORDER BY 1, 4 DESC""").df()
step("patients with any order of either study drug", con.execute("SELECT count(DISTINCT subject_id) FROM ex").fetchone()[0])

con.execute("""CREATE TEMP TABLE first AS WITH o AS (SELECT * FROM ex WHERE is_oral AND starttime IS NOT NULL AND starttime <= dischtime),
               t AS (SELECT subject_id, min(starttime) t0 FROM o GROUP BY 1)
               SELECT t.subject_id, t.t0, any_value(o.hadm_id) hadm_id, bool_or(o.a0) a0, bool_or(o.a1) a1,
                      count(DISTINCT o.hadm_id) nh
               FROM t JOIN o ON o.subject_id = t.subject_id AND o.starttime = t.t0 GROUP BY 1, 2""")
step("with an enteral exposure order starting before discharge (candidate time zero)", con.execute("SELECT count(*) FROM first").fetchone()[0])
con.execute("DELETE FROM first WHERE (a0 AND a1) OR nh > 1")
step("after excluding both arms ordered at time zero", con.execute("SELECT count(*) FROM first").fetchone()[0])
con.execute("""CREATE TEMP TABLE c AS SELECT f.subject_id, f.hadm_id, f.t0, CASE WHEN f.a0 THEN 1 ELSE 0 END treated,
               ad.admittime, ad.dischtime FROM first f JOIN admissions ad USING (subject_id, hadm_id)""")
allow_same_adm_iv = K == "transform_hf"
same_adm = ("(e.hadm_id = c.hadm_id AND e.starttime < c.t0 AND e.is_oral)" if allow_same_adm_iv
            else "(e.hadm_id = c.hadm_id AND (e.starttime < c.t0 OR e.starttime IS NULL))")
con.execute(f"""DELETE FROM c WHERE subject_id IN (SELECT c.subject_id FROM c JOIN ex e USING (subject_id)
                WHERE e.admittime < c.admittime OR {same_adm})""")
step("after washout (no order of either drug in any earlier admission / before t0)", con.execute("SELECT count(*) FROM c").fetchone()[0])

con.execute("""CREATE TEMP TABLE c2 AS SELECT c.*, p.gender, p.anchor_age + (year(c.t0) - p.anchor_year) age,
               CAST(split_part(p.anchor_year_group, ' - ', 1) AS INT) + 1 + (year(c.t0) - p.anchor_year) est_year,
               p.anchor_year_group, p.dod
               FROM c JOIN patients p USING (subject_id)""")
con.execute("DELETE FROM c2 WHERE dod < CAST(t0 AS DATE)")
step("no recorded death before time zero (data error)", con.execute("SELECT count(*) FROM c2").fetchone()[0])
con.execute("DELETE FROM c2 WHERE age < 18")
step("age >= 18", con.execute("SELECT count(*) FROM c2").fetchone()[0])
y0 = int(spec["index_start"][:4])
con.execute(f"DELETE FROM c2 WHERE est_year < {y0}")
step(f"estimated real index year >= {y0} (trial_specs index_start)", con.execute("SELECT count(*) FROM c2").fetchone()[0])

# diagnoses of the index and earlier admissions, concept-matched
con.execute("""CREATE TEMP TABLE cdx AS SELECT c2.subject_id, d.hadm_id, ad.admittime, ad.dischtime, k.concept,
               d.hadm_id = c2.hadm_id is_index FROM c2 JOIN admissions ad ON ad.subject_id = c2.subject_id
               AND ad.admittime <= c2.admittime
               JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id
               JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)""")
gname, gmode = GATE[K]
win = ("(x.is_index OR x.dischtime >= c2.t0 - INTERVAL 30 DAY)" if gmode == "window_30d" else "TRUE")
con.execute(f"""DELETE FROM c2 WHERE subject_id NOT IN (SELECT x.subject_id FROM cdx x JOIN c2 USING (subject_id)
                WHERE x.concept = '{gname}' AND {win})""")
step(f"disease gate {gname} ({gmode})", con.execute("SELECT count(*) FROM c2").fetchone()[0])

ex = spec.get("exclusions", {})
if K in ("aristotle", "rocket_af"):
    con.execute("DELETE FROM c2 WHERE subject_id IN (SELECT subject_id FROM cdx WHERE concept = 'excl_af_valve')")
    step("no mitral stenosis / prosthetic valve code (index or earlier admission)", con.execute("SELECT count(*) FROM c2").fetchone()[0])
    oth = [x.lower() for x in ex["other_anticoag_365d"]]
    con.execute(f"""DELETE FROM c2 WHERE subject_id IN (SELECT c2.subject_id FROM c2 JOIN rxt r USING (subject_id)
                    WHERE list_has_any(r.toks, {sql_list(oth)}) AND r.starttime <= c2.t0
                      AND r.starttime >= c2.t0 - INTERVAL 365 DAY)""")
    step("no other DOAC order in [t0-365 d, t0]", con.execute("SELECT count(*) FROM c2").fetchone()[0])
if K == "plato":
    oac = [x.lower() for x in ex["anticoag_30d"]]
    con.execute(f"""DELETE FROM c2 WHERE subject_id IN (SELECT c2.subject_id FROM c2 JOIN rxt r USING (subject_id)
                    WHERE list_has_any(r.toks, {sql_list(oac)}) AND r.starttime <= c2.t0
                      AND r.starttime >= c2.t0 - INTERVAL 30 DAY)""")
    step("no oral anticoagulant order in [t0-30 d, t0]", con.execute("SELECT count(*) FROM c2").fetchone()[0])
    con.execute("DELETE FROM c2 WHERE subject_id IN (SELECT subject_id FROM cdx WHERE concept = 'excl_ich' AND NOT is_index)")
    step("no prior intracranial haemorrhage code (earlier admissions)", con.execute("SELECT count(*) FROM c2").fetchone()[0])

# ---- labs (latest in [t0-365 d, t0)), needed for the TRANSFORM-HF eGFR exclusion
labrows = [(n, i) for n, (ids, lo, hi) in LABS.items() for i in ids]
con.register("labmap_df", pd.DataFrame(labrows, columns=["name", "itemid"]))
labs = con.execute("""SELECT c2.subject_id, m.name, arg_max(l.valuenum, l.charttime) v FROM c2
    JOIN labevents l ON l.subject_id = c2.subject_id JOIN labmap_df m ON m.itemid = l.itemid
    WHERE l.valuenum IS NOT NULL AND l.charttime < c2.t0 AND l.charttime >= c2.t0 - INTERVAL 365 DAY
    GROUP BY 1, 2""").df().pivot(index="subject_id", columns="name", values="v")
coh = con.execute("SELECT * FROM c2 ORDER BY subject_id").df().set_index("subject_id")
base = pd.DataFrame(index=coh.index)
base["age_at_index"] = coh.age.astype(float)
base["male"] = (coh.gender == "M").astype(float)
base["index_year"] = coh.est_year.astype(float)
for n, (ids, lo, hi) in LABS.items():
    s = labs[n].reindex(base.index) if n in labs else pd.Series(np.nan, index=base.index)
    base[n] = s.where((s >= lo) & (s <= hi))


def ckd_epi_2021(scr, age, male):
    k = np.where(male == 1, 0.9, 0.7)
    al = np.where(male == 1, -0.302, -0.241)
    r = scr / k
    return 142 * np.minimum(r, 1) ** al * np.maximum(r, 1) ** -1.2 * 0.9938 ** age * np.where(male == 1, 1.0, 1.012)


if "egfr_lt" in ex:
    egfr = ckd_epi_2021(base.creatinine.to_numpy(), base.age_at_index.to_numpy(), base.male.to_numpy())
    drop = base.index[np.nan_to_num(egfr, nan=999) < ex["egfr_lt"]]
    coh, base = coh.drop(drop), base.drop(drop)
    con.register("drop_df", pd.DataFrame({"subject_id": np.asarray(drop, dtype="int64")}))
    con.execute("DELETE FROM c2 WHERE subject_id IN (SELECT subject_id FROM drop_df)")
    step(f"eGFR (CKD-EPI 2021, latest creatinine in 365 d) not < {ex['egfr_lt']} (unknown passes)", len(coh))
step("final cohort", len(coh))

# ---- dx covariates: any code in the index admission or any earlier admission
dxn = list(TS.DX_CORE) + [k for k, v in spec.get("extra_dx", {}).items() if v]
if K in ("aristotle", "rocket_af", "plato") and "heart_failure" not in dxn:
    dxn.append("heart_failure")
dxd = con.execute("SELECT DISTINCT subject_id, concept FROM cdx WHERE subject_id IN (SELECT subject_id FROM c2)").df()
for n in dxn:
    base[n] = base.index.isin(dxd[dxd.concept == n].subject_id).astype(float)
if K == "plato":  # index-event characteristics
    st = con.execute("SELECT DISTINCT subject_id FROM cdx WHERE concept = 'stemi' AND is_index").df()
    base["stemi_index_adm"] = base.index.isin(st.subject_id).astype(float)
    dxn.append("stemi_index_adm")
    p10, p9 = PCI_PX
    pc = con.execute(f"""SELECT DISTINCT c2.subject_id FROM c2 JOIN procedures_icd p USING (subject_id)
        JOIN admissions ad ON ad.subject_id = p.subject_id AND ad.hadm_id = p.hadm_id
        WHERE (p.hadm_id = c2.hadm_id OR ad.dischtime >= c2.t0 - INTERVAL 30 DAY) AND ad.admittime <= c2.admittime
          AND p.chartdate <= CAST(c2.t0 AS DATE)
          AND ((p.icd_version = 10 AND list_has_any({sql_list(p10)}, [lower(substr(p.icd_code, 1, 4))]))
            OR (p.icd_version = 9 AND list_has_any({sql_list(p9)}, [lower(substr(p.icd_code, 1, 4))])))""").df()
    base["pci_index_30d"] = base.index.isin(pc.subject_id).astype(float)
    dxn.append("pci_index_30d")

# ---- medications: any order (any route) in [t0-365 d, t0)
meds = []
alltok = sorted({k.lower() for v in spec["drugs_90d"].values() for k in v})
mt = con.execute(f"""SELECT DISTINCT subject_id, tok FROM (SELECT c2.subject_id,
                     UNNEST(list_intersect(r.toks, {sql_list(alltok)})) tok FROM c2 JOIN rxt r USING (subject_id)
                     WHERE r.starttime < c2.t0 AND r.starttime >= c2.t0 - INTERVAL 365 DAY)""").df()
for n, kws in spec["drugs_90d"].items():
    col = n.replace("_order", "_365d")
    base[col] = base.index.isin(mt[mt.tok.isin({k.lower() for k in kws})].subject_id).astype(float)
    meds.append(col)
if K == "transform_hf":
    iv = con.execute(f"""SELECT DISTINCT c2.subject_id FROM c2 JOIN rxt r USING (subject_id)
        WHERE r.hadm_id = c2.hadm_id AND r.starttime < c2.t0 AND list_has_any(r.toks, {sql_list(TS.LOOP)})
          AND list_contains({"[" + ", ".join(f"'{x}'" for x in IV_ROUTES) + "]"}, r.route)""").df()
    base["iv_loop_before_index"] = base.index.isin(iv.subject_id).astype(float)
    meds.append("iv_loop_before_index")

# ---- vitals: latest in [t0-365 d, t0): ICU chartevents (time-stamped) or OMR (date; index day excluded)
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
    SELECT subject_id, vname, arg_max(v, epoch(ts) * 10 + src) v, arg_max(src, epoch(ts) * 10 + src) src FROM vv WHERE v IS NOT NULL GROUP BY 1, 2""").df()
vsrc = {}
for n, (lo, hi) in VITAL_RANGES.items():
    s = vit[vit.vname == n].set_index("subject_id")
    vv = s.v.reindex(base.index)
    base[n] = vv.where((vv >= lo) & (vv <= hi))
    vsrc[n] = {"icu_chartevents": int((s.src == 1).sum()), "omr": int((s.src == 0).sum())}
labs_vitals = list(LABS) + list(VITAL_RANGES)

# ---- utilisation
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

# drop constant covariates (e.g. the gate diagnosis)
roles = dict(demo=["age_at_index", "male", "index_year"], dx=dxn, meds=meds, labs_vitals=labs_vitals, util=util)
const = [c for c in base.columns if base[c].nunique(dropna=True) <= 1]
base = base.drop(columns=const)
roles = {k: [c for c in v if c not in const] for k, v in roles.items()}
roles["phys"] = list(roles["labs_vitals"])

# ---- write cohort / index_time / baseline / roles
coh["pid"] = [pid_of(s) for s in coh.index]
epoch = pd.Timestamp("2100-01-01")
cohort = pd.DataFrame({"pid": coh.pid.values, "treated": coh.treated.astype(int).values,
                       "index_day": ((coh.t0 - epoch) / pd.Timedelta(days=1)).astype(float).values,
                       "index_year": coh.est_year.astype(float).values})
cohort.to_parquet(OUT / "cohort.parquet", index=False)
pd.DataFrame({"pid": coh.pid.values, "subject_id": coh.index.values.astype("int64"),
              "index_datetime": coh.t0.values, "hadm_id": coh.hadm_id.values.astype("int64"),
              "treated": coh.treated.astype(int).values}).to_parquet(OUT / "index_time.parquet", index=False)
b = base.copy()
b.insert(0, "pid", coh.pid.reindex(b.index).values)
b.reset_index(drop=True).astype({c: float for c in base.columns}).to_parquet(OUT / "baseline.parquet", index=False)
json.dump(roles, open(OUT / "roles.json", "w"), indent=2)

# ---- panel (365 d before t0)
con.execute("CREATE TEMP TABLE pc AS SELECT subject_id, hadm_id, t0, admittime FROM c2")
n = len(coh)
q_dx = """SELECT pc.subject_id, CASE WHEN d.icd_version = 10 THEN 'dx_' || substr(d.icd_code, 1, 3)
                 ELSE 'dx_i9_' || substr(d.icd_code, 1, 3) END f, count(DISTINCT d.hadm_id) c
          FROM pc JOIN admissions ad ON ad.subject_id = pc.subject_id AND ad.admittime <= pc.admittime
               AND (ad.hadm_id = pc.hadm_id OR ad.admittime >= pc.t0 - INTERVAL 365 DAY)
          JOIN diagnoses_icd d ON d.subject_id = ad.subject_id AND d.hadm_id = ad.hadm_id GROUP BY 1, 2"""
q_rx = f"""WITH r AS (SELECT pc.subject_id, CAST(r.starttime AS DATE) dday,
                 list_filter(r.toks, x -> regexp_matches(x, '^[a-z][a-z]+$') AND x <> 'nf')[1] tok
          FROM pc JOIN rxt r USING (subject_id)
          WHERE r.starttime < CAST(CAST(pc.t0 AS DATE) AS TIMESTAMP) AND r.starttime >= pc.t0 - INTERVAL 365 DAY
            AND NOT list_has_any(r.toks, {sql_list(EXPO)}))
          SELECT subject_id, 'rx_' || tok f, count(DISTINCT dday) c FROM r WHERE tok IS NOT NULL GROUP BY 1, 2"""
q_px = """SELECT pc.subject_id, CASE WHEN p.icd_version = 10 THEN 'px_' || substr(p.icd_code, 1, 4)
                 ELSE 'px_i9_' || substr(p.icd_code, 1, 3) END f, count(DISTINCT p.chartdate) c
          FROM pc JOIN procedures_icd p USING (subject_id)
          WHERE p.chartdate < CAST(pc.t0 AS DATE) AND p.chartdate >= CAST(pc.t0 AS DATE) - INTERVAL 365 DAY GROUP BY 1, 2"""
q_lab = """SELECT pc.subject_id, 'lab_' || CAST(l.itemid AS VARCHAR) f, 1 c
          FROM pc JOIN labevents l USING (subject_id)
          WHERE l.charttime < pc.t0 AND l.charttime >= pc.t0 - INTERVAL 365 DAY GROUP BY 1, 2"""
frames, dic = [], []
for dom, q in (("dx", q_dx), ("rx", q_rx), ("px", q_px), ("lab", q_lab)):
    d = con.execute(f"""WITH x AS ({q}) SELECT f, list(subject_id) s, list(c) c FROM x GROUP BY f
                        HAVING count(DISTINCT subject_id) >= {a.min_prev * n}""").df()
    for f, s, cc in zip(d.f, d.s, d.c):
        frames.append(pd.Series(np.asarray(cc, float), index=pd.Index(s), name=f.lower() if dom == "rx" else f))
        dic.append((f.lower() if dom == "rx" else f, dom, len(s) / n))
panel = pd.concat(frames, axis=1).reindex(coh.index).fillna(0.0)
leak = [c for c in panel.columns if c.startswith("rx_") and c[3:] in EXPO]
assert not leak, leak
panel.insert(0, "pid", coh.pid.values)
panel.reset_index(drop=True).to_parquet(OUT / "panel.parquet", index=False)
dd = pd.DataFrame(dic, columns=["feature", "domain", "prevalence"])
dd[["feature", "domain"]].to_csv(OUT / "panel_dictionary.csv", index=False)

# ---- rct.json
P = TS.PUBLISHED[K]
flip = abs(P["our_orientation"] - P["hr"]) > 1e-6
lo, hi = P["ci"]
rct = dict(trial=spec["name"].replace(" (adapted)", ""), key=K, arms=[spec["arms"][0][0], spec["arms"][1][0]],
           hr=P["hr"], lo=lo, hi=hi, ci_level=P.get("ci_level", 0.95), our_orientation=P["our_orientation"],
           our_lo=round(1 / hi, 3) if flip else lo, our_hi=round(1 / lo, 3) if flip else hi,
           horizon_days=int(min(round(TS.HORIZON_MONTHS[K] * 30.4375), 365)), endpoint=ENDPOINT[K],
           notes=(f"published: {P['endpoint']} ({P['rct_arms']}; {P['measure']}; {P['source']}); hr/lo/hi in the RCT's own "
                  f"orientation, our_orientation/our_lo/our_hi = first arm vs second arm. MIMIC horizon capped at 365 d "
                  f"(trial {TS.HORIZON_MONTHS[K]} months)."))
json.dump(rct, open(OUT / "rct.json", "w"), indent=2)

# ---- summary (aggregates only)
ecg = con.execute("""SELECT c2.treated, count(DISTINCT c2.subject_id) n FROM c2 JOIN ecg_records e USING (subject_id)
     WHERE e.ecg_time <= c2.t0 AND e.ecg_time >= c2.t0 - INTERVAL 365 DAY GROUP BY 1""").df().set_index("treated").n
emar = con.execute(f"""SELECT c2.treated, count(DISTINCT c2.subject_id) n FROM c2 JOIN emar m ON m.subject_id = c2.subject_id
     AND m.hadm_id = c2.hadm_id WHERE m.event_txt IN ('Administered', 'Delayed Administered', 'Confirmed')
     AND list_has_any(regexp_split_to_array(lower(m.medication), '[^a-z0-9]+'),
                      CASE WHEN c2.treated = 1 THEN {sql_list(A0)} ELSE {sql_list(A1)} END)
     AND m.charttime >= c2.t0 - INTERVAL 1 HOUR GROUP BY 1""").df().set_index("treated").n
emar_any = con.execute("""SELECT c2.treated, count(DISTINCT c2.subject_id) n FROM c2 JOIN emar m
     ON m.subject_id = c2.subject_id AND m.hadm_id = c2.hadm_id GROUP BY 1""").df().set_index("treated").n
other_arm = con.execute("""SELECT c2.treated, count(DISTINCT c2.subject_id) n FROM c2 JOIN ex e
     ON e.subject_id = c2.subject_id AND e.hadm_id = c2.hadm_id
     WHERE (c2.treated = 1 AND e.a1) OR (c2.treated = 0 AND e.a0) GROUP BY 1""").df().set_index("treated").n
arm_names = {1: spec["arms"][0][0], 0: spec["arms"][1][0]}
by_arm = {}
for t, g in coh.groupby("treated"):
    bb = base.loc[g.index]
    by_arm[arm_names[int(t)]] = dict(
        n=supp(len(g)), with_ecg_365d=supp(ecg.get(t, 0)),
        emar_present_in_index_adm=supp(emar_any.get(t, 0)),
        emar_administration_of_index_drug_after_t0=supp(emar.get(t, 0)),
        other_arm_ordered_in_index_adm=supp(other_arm.get(t, 0)),
        anchor_year_group={k: supp(v) for k, v in g.anchor_year_group.value_counts().sort_index().items()},
        est_index_year={k: supp(v) for k, v in g.est_year.value_counts().sort_index().items()},
        missing_frac={c: round(float(bb[c].isna().mean()), 3) for c in base.columns if bb[c].isna().any()},
        mean={c: round(float(bb[c].mean()), 3) for c in base.columns})
tm = tokmatch.copy()
tm["n_pat"] = tm.n_pat.map(supp)
tm["n_orders"] = tm.n_orders.map(supp)
summary = dict(
    cohort="mimic", trial=K, spec=spec["spec_version"] + "|v15_mimic_v1", created=dt.datetime.now().isoformat(timespec="seconds"),
    arms=[spec["arms"][0][0], spec["arms"][1][0]], arm_tokens=[A0, A1],
    attrition=[dict(step=s, n=supp(v)) for s, v in attr], n=supp(n), by_arm=by_arm,
    feasible_ecg_rule=bool(all(ecg.get(t, 0) >= 200 for t in (0, 1))),
    vital_source_counts={k: {kk: supp(vv) for kk, vv in v.items()} for k, v in vsrc.items()},
    dropped_constant_covariates=const,
    panel=dict(n_features=int(len(dd)), by_domain=dd.domain.value_counts().to_dict(), min_prevalence=a.min_prev,
               exposure_tokens_excluded=EXPO),
    matched_drug_strings=tm.to_dict(orient="records"),
    notes=[
        "time zero = first enteral prescriptions.starttime of either study drug that starts before the admission's discharge time "
        "(orders timed after discharge are not time-zero candidates; they still count for the washout); date-shifted per patient",
        "new user = first order in MIMIC inpatient prescriptions; home medication continued on admission cannot be distinguished",
        "investigational-drug order strings ('inv-<drug>', <11 patients) are counted as the drug",
        "index_year = anchor_year_group midpoint + (shifted index year - anchor_year); age = anchor_age + same offset",
        "dx covariates use all diagnoses of the index admission (coded at discharge; may include post-t0 events) and of every earlier admission",
        "meds = any order in [t0-365 d, t0) incl. the index admission before t0; labs latest in [t0-365 d, t0); "
        "SBP/DBP/HR latest from ICU chartevents (before t0) or OMR (dates before the index day); HR only from ICU; BMI from OMR; "
        "LVEF not available (omitted); MIMIC-IV-ED vitals not staged",
        "ICD-9 codes mapped to trial_specs concepts by hand (v15_mimic_common.CONCEPTS); panel keeps ICD-9 as dx_i9_<3 char> / px_i9_<3 char> "
        "(no GEMs table on disk); panel dx includes the index admission; rx/px exclude the index day; lab_ = itemid measured (binary)",
        "ED visits = transfers eventtype 'ED' not belonging to the index admission",
    ] + (["COMET: metoprolol tartrate and succinate (and toprol/lopressor) both count as metoprolol"] if K == "comet" else [])
      + (["TRANSFORM-HF: IV loop diuretic in the index admission before t0 is allowed (covariate iv_loop_before_index); "
          "exposure = first enteral torsemide or furosemide order"] if K == "transform_hf" else []),
)
json.dump(summary, open(OUT / "summary.json", "w"), indent=2, default=str)
(OUT / "READY_COHORT").write_text(dt.datetime.now().isoformat() + "\n")
print(json.dumps({k: summary[k] for k in ("attrition", "n", "feasible_ecg_rule")}, indent=1, default=str))
print(json.dumps({k: {kk: v[kk] for kk in ("n", "with_ecg_365d", "emar_present_in_index_adm",
                                           "emar_administration_of_index_drug_after_t0", "other_arm_ordered_in_index_adm")}
                  for k, v in by_arm.items()}, indent=1, default=str))
print("panel", summary["panel"]["by_domain"], "const", const)
