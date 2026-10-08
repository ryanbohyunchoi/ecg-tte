#!/usr/bin/env python
"""Spec-v2 per-patient eligibility inputs and exclusion flags for the 38 version 1 analysed cohorts.

Steps (restricted outputs under OUT/flags, umask 077; nothing patient-level is printed):
  extract  per trial, on the analysed keys of scripts/v1_criteria_check/s1_keys.py (= T.keys, asserted in grid.py):
           exact age at index (builder formula); latest plausible value of each MEASURE in [index - lookback,
           index - 1] (index day excluded; arg_max by (date, value) as build_trial_cohort.latest_measure) and whether
           measured; AF code on/before index (I48); I50 code dated inside an inpatient stay in [index - 365, index - 1]
           (HF hospitalisation, merged stays as extract_outcomes.py); antihypertensive order in [index - 365, index - 1]
           (treated hypertension); latest echo EF in [index - 365, index - 1].  -> restricted_meas_<n>.parquet
  outcome  outcome re-definitions (AMPLIFY, LODESTAR, PROVE IT) -> restricted_outcome_<n>.parquet (y_t, y_e on T.keys)
  apply    specs_v2 rules -> restricted_drop_<n>.parquet (one column per rule, drop_v2, drop_v2meas) and the aggregate
           exclusion tables OUT/flags/exclusions_by_rule.csv, exclusions_by_trial.csv (shares; counts 1-10 suppressed,
           including complements and arm cells).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2common as K  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from trial_common import code_like, connect, mrn_key, rp, sql_list  # noqa: E402
from trial_specs import ACEI, ARB, BETA_BLOCKER, MRA, THIAZIDE  # noqa: E402

G = K.GOLD
ECHO_META = "/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet"
# name: (OMOP concept, lookback days, plausible low, plausible high). Concepts as trial_specs.NUMERIC_CORE and
# build_physiology_panel_v2.LABS; BNP / total cholesterol / ALT / triglycerides from aggregate concept listings (LOINC
# 30934-4, 2093-3, 1742-6, 2571-8). Lookback: 90 d for labs and vitals, 365 d for BMI (NUMERIC_CORE convention).
MEASURE = {
    "sbp": (4152194, 90, 50, 300), "dbp": (3012888, 90, 20, 200), "heart_rate": (3027018, 90, 20, 250),
    "bmi": (4245997, 365, 10, 100), "creatinine": (3016723, 90, 0.1, 25), "potassium": (3023103, 90, 1.5, 9),
    "hemoglobin": (3000963, 90, 3, 25), "egfr": (40764999, 90, 1, 200), "hba1c": (3004410, 90, 3, 20),
    "ntprobnp": (3029187, 90, 5, 100000), "bnp": (3011960, 90, 1, 20000), "ldl": (3028288, 90, 5, 600),
    "total_chol": (3027114, 90, 30, 1000), "triglycerides": (3022192, 90, 10, 10000), "platelets": (3024929, 90, 1, 2000),
    "alt": (3006923, 90, 1, 10000),
}
ANTIHTN = ACEI + ARB + BETA_BLOCKER + THIAZIDE + MRA + [
    "amlodipine", "norvasc", "nifedipine", "procardia", "adalat", "felodipine", "isradipine", "nicardipine", "diltiazem",
    "cardizem", "verapamil", "hydralazine", "clonidine", "doxazosin", "terazosin", "prazosin", "methyldopa", "minoxidil",
    "aliskiren", "amiloride", "triamterene", "furosemide", "torsemide", "bumetanide", "cozaar", "diovan", "tenormin"]


from trial_specs import GLP1RA, INSULIN, SGLT2_ALL, TZD  # noqa: E402

SU_GLINIDE = ["glipizide", "glucotrol", "glimepiride", "amaryl", "glyburide", "glynase", "micronase", "diabeta", "gliclazide",
              "repaglinide", "prandin", "nateglinide", "starlix"]
DPP4 = ["sitagliptin", "januvia", "janumet", "saxagliptin", "onglyza", "kombiglyze", "linagliptin", "tradjenta", "jentadueto",
        "alogliptin", "nesina", "kazano"]
GLUCOSE_LOWERING = (["metformin", "glucophage", "acarbose", "precose", "miglitol"] + INSULIN + SU_GLINIDE + DPP4 + GLP1RA
                    + SGLT2_ALL + TZD)


def drug_any(con, kws, lo, hi):
    """patient_keys with an order (token match, as trial_common.create_drug_tokens) in [index + lo, index + hi] days."""
    kw = sql_list(sorted({x.lower() for x in kws}))
    return set(con.execute(f"""SELECT DISTINCT k.patient_key FROM k JOIN (
            SELECT person_id, drug_exposure_start_date d, unnest(string_split(lower(drug_source_value), '-')) tok
            FROM {rp(G, 'drug_exposure')} WHERE drug_source_value IS NOT NULL AND drug_exposure_start_date IS NOT NULL
              AND person_id IN (SELECT person_id FROM k)) x USING (person_id)
        WHERE x.tok IN ({kw}) AND x.d BETWEEN k.idx + INTERVAL ({lo}) DAY AND k.idx + INTERVAL ({hi}) DAY""").df().patient_key)


def keys(n):
    return pd.read_parquet(K.CRIT / "keys" / f"restricted_keys_{n}.parquet")


def extract_one(n):
    K.umask()
    t0 = time.time()
    D = keys(n)
    con = connect(12, "60GB")
    con.register("k0", D[["patient_key", "person_id", "treated", "index_date"]])
    con.execute("CREATE TEMP TABLE k AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, treated, CAST(index_date AS DATE) idx FROM k0")
    M = pd.DataFrame(index=pd.Index(D.patient_key, name="patient_key"))
    M["treated"] = D.treated.to_numpy()
    a = con.execute(f"""SELECT k.patient_key, date_diff('year', CAST(p.birth_datetime AS DATE), k.idx)
          - (CASE WHEN strftime(k.idx, '%m%d') < strftime(CAST(p.birth_datetime AS DATE), '%m%d') THEN 1 ELSE 0 END) age
        FROM k JOIN {rp(G, 'person')} p USING (person_id)""").df().set_index("patient_key").age
    M["age"] = a.reindex(M.index).to_numpy(float)
    sx = con.execute(f"""SELECT k.patient_key, p.gender_concept_id = 8507 male FROM k JOIN {rp(G, 'person')} p USING (person_id)""").df()
    M["male"] = sx.set_index("patient_key").male.reindex(M.index).astype(float).to_numpy()
    con.register("mdef", pd.DataFrame([(k_, v[0], v[1], v[2], v[3]) for k_, v in MEASURE.items()],
                                      columns=["name", "cid", "lb", "lo", "hi"]))
    L = con.execute(f"""SELECT k.patient_key, d.name, arg_max(m.value_as_number, (m.measurement_date, m.value_as_number)) v
        FROM k JOIN {rp(G, 'measurement')} m USING (person_id) JOIN mdef d ON m.measurement_concept_id = d.cid
        WHERE m.value_as_number IS NOT NULL AND m.value_as_number BETWEEN d.lo AND d.hi
          AND m.measurement_date BETWEEN k.idx - to_days(CAST(d.lb AS INTEGER)) AND k.idx - INTERVAL 1 DAY
        GROUP BY 1, 2""").df()
    L = L.pivot(index="patient_key", columns="name", values="v").reindex(M.index)
    for c in MEASURE:
        M[c] = L[c].to_numpy(float) if c in L else np.nan
    # AF code on / before index; I50 inside an inpatient stay in the prior year
    af = con.execute(f"""SELECT DISTINCT k.patient_key FROM k JOIN {rp(G, 'condition_occurrence')} c USING (person_id)
        WHERE c.condition_start_date <= k.idx AND {code_like("upper(replace(c.condition_source_value, '.', ''))", ['I48'])}""").df().patient_key
    M["af_code_on_before"] = M.index.isin(set(af))
    con.execute(f"""CREATE TEMP TABLE iv AS SELECT v.person_id, v.visit_start_date s, coalesce(v.visit_end_date, v.visit_start_date) e
        FROM {rp(G, 'visit_occurrence')} v WHERE v.visit_concept_id = 9201 AND v.person_id IN (SELECT person_id FROM k)""")
    con.execute("""CREATE TEMP TABLE stays AS
        WITH o AS (SELECT *, max(e) OVER (PARTITION BY person_id ORDER BY s, e ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) pe FROM iv),
             g AS (SELECT *, sum(CASE WHEN pe IS NULL OR s > pe + INTERVAL 1 DAY THEN 1 ELSE 0 END)
                            OVER (PARTITION BY person_id ORDER BY s, e ROWS UNBOUNDED PRECEDING) gid FROM o)
        SELECT person_id, gid, min(s) s, max(e) e FROM g GROUP BY 1, 2""")
    hh = con.execute(f"""SELECT DISTINCT k.patient_key FROM k JOIN {rp(G, 'condition_occurrence')} c USING (person_id)
        JOIN stays st ON st.person_id = k.person_id AND c.condition_start_date BETWEEN st.s AND st.e
        WHERE c.condition_start_date BETWEEN k.idx - INTERVAL 365 DAY AND k.idx - INTERVAL 1 DAY
          AND {code_like("upper(replace(c.condition_source_value, '.', ''))", ['I50'])}""").df().patient_key
    M["hf_hosp_365"] = M.index.isin(set(hh))
    hh9 = con.execute(f"""SELECT DISTINCT k.patient_key FROM k JOIN {rp(G, 'condition_occurrence')} c USING (person_id)
        JOIN stays st ON st.person_id = k.person_id AND c.condition_start_date BETWEEN st.s AND st.e
        WHERE c.condition_start_date BETWEEN k.idx - INTERVAL 274 DAY AND k.idx - INTERVAL 1 DAY
          AND {code_like("upper(replace(c.condition_source_value, '.', ''))", ['I50'])}""").df().patient_key
    M["hf_hosp_274"] = M.index.isin(set(hh9))
    M["glucose_lowering_84"] = M.index.isin(drug_any(con, GLUCOSE_LOWERING, -84, -1))  # 12 weeks before index
    M["su_glinide_84"] = M.index.isin(drug_any(con, SU_GLINIDE, -84, -1))
    kw = sql_list(sorted({x.lower() for x in ANTIHTN}))
    tr = con.execute(f"""SELECT DISTINCT k.patient_key FROM k JOIN (
            SELECT person_id, drug_exposure_start_date d, unnest(string_split(lower(drug_source_value), '-')) tok
            FROM {rp(G, 'drug_exposure')} WHERE drug_source_value IS NOT NULL AND drug_exposure_start_date IS NOT NULL
              AND person_id IN (SELECT person_id FROM k)) x USING (person_id)
        WHERE x.tok IN ({kw}) AND x.d BETWEEN k.idx - INTERVAL 365 DAY AND k.idx - INTERVAL 1 DAY""").df().patient_key
    M["treated_htn_365"] = M.index.isin(set(tr))
    con.execute(f"""CREATE TEMP TABLE pk AS SELECT person_id, {mrn_key('person_source_value')} kk FROM {rp(G, 'person')}
        WHERE person_id IN (SELECT person_id FROM k)""")
    con.execute(f"""CREATE TEMP TABLE echo AS SELECT {mrn_key('MRN')} kk, try_cast(EchoDate AS DATE) d, EF
        FROM read_parquet('{ECHO_META}') WHERE EF BETWEEN 5 AND 90 AND try_cast(EchoDate AS DATE) IS NOT NULL""")
    ef = con.execute("""SELECT k.patient_key, arg_max(e.EF, (e.d, e.EF)) ef FROM k JOIN pk USING (person_id) JOIN echo e ON e.kk = pk.kk
        WHERE e.d BETWEEN k.idx - INTERVAL 365 DAY AND k.idx - INTERVAL 1 DAY GROUP BY 1""").df().set_index("patient_key").ef
    M["ef"] = ef.reindex(M.index).to_numpy(float)
    con.close()
    M.reset_index().to_parquet(K.FLG / f"restricted_meas_{n}.parquet")
    cov = {c: round(float(M[c].notna().mean()), 3) for c in MEASURE}
    print(n, f"{time.time() - t0:.0f}s", flush=True)
    return dict(trial=n, n=len(M), secs=round(time.time() - t0), **{f"measured:{c}": v for c, v in cov.items()})


def extract(workers):
    from multiprocessing import Pool
    K.umask()
    K.FLG.mkdir(parents=True, exist_ok=True)
    with Pool(workers) as p:
        res = p.map(extract_one, K.ALL, chunksize=1)
    pd.DataFrame(res).to_csv(K.FLG / "measured_share.csv", index=False)  # shares only


# ================================================================ outcome re-definitions
def amplify_outcome(T, n, gap_days=7):
    """recurrent VTE = first inpatient stay starting >= gap_days after the end of the index stay with a primary
    hospital-billing VTE code (I26, I80.1, I80.2, I82.4); death and data end censor (as s3_reanalysis.outcome_fix)."""
    import s2_flags as S
    from trial_specs import DEATH_END, HORIZON_MONTHS, PRIMARY_BILLING
    Dk, con = S.setup(n)
    assert (pd.Index(Dk.patient_key) == T.keys).all()
    S.stays(con)
    idx = Dk.set_index("patient_key").index_date
    H = int(round(HORIZON_MONTHS["amplify"] * 30.4375))
    ev = con.execute(f"""SELECT x.patient_key, min(st.s) d FROM idxstay x JOIN stays st ON st.person_id = x.person_id
            AND st.s >= x.idx_stay_end + INTERVAL {gap_days} DAY
        JOIN {rp(G, 'condition_occurrence')} c ON c.person_id = x.person_id AND c.condition_start_date BETWEEN st.s AND st.e
        WHERE c.condition_status_source_value = '{PRIMARY_BILLING}' AND {code_like("upper(replace(c.condition_source_value, '.', ''))", S.VTE)}
        GROUP BY 1""").df().set_index("patient_key").d
    dd = con.execute(f"SELECT k.patient_key, min(d.death_date) dd FROM k JOIN {rp(G, 'death')} d USING (person_id) GROUP BY 1").df().set_index("patient_key").dd
    con.close()
    i = idx.reindex(T.keys)
    evd = pd.to_datetime(ev.reindex(T.keys))
    ddd = pd.to_datetime(dd.reindex(T.keys))
    ddd = ddd.where(~(ddd < i))
    end = pd.Series(pd.Timestamp(DEATH_END), index=T.keys).clip(upper=i + pd.Timedelta(days=max(H, int(round(60 * 30.4375)))))
    stop = pd.concat([evd, end, ddd], axis=1).min(axis=1)
    event = evd.notna() & (evd <= end) & ~(ddd < evd)
    stop = stop.where(~event, evd)
    t = (stop - i).dt.days.astype(float)
    t = t.where(t > 0, 0.5).to_numpy()
    return np.minimum(t, H), (event.to_numpy() & (t <= H)).astype(int)


def outcome_one(n):
    K.umask()
    import s3_reanalysis as S3
    T = K.E.load_trial(n) if n in K.AF.V.OLD else K.E.load_trial(n, cache=False)
    if n == "amplify":
        yt, ye = amplify_outcome(T, n)
    else:  # LODESTAR: + PCI/CABG after the index stay; PROVE IT: + PCI/CABG >= 30 d after index (data-check definitions)
        yt, ye = S3.outcome_fix(T, n)
    pd.DataFrame({"patient_key": T.keys, "y_t": yt, "y_e": ye}).to_parquet(K.FLG / f"restricted_outcome_{n}.parquet")
    ok = T.y_ok
    return dict(trial=n, events_v1=int((T.y_e[ok] == 1).sum()), events_v2=int((ye[ok] == 1).sum()), n_ok=int(ok.sum()))


def outcome():
    from multiprocessing import Pool
    K.umask()
    with Pool(3) as p:
        res = p.map(outcome_one, ["amplify", "lodestar", "prove-it"])
    R = pd.DataFrame(res)
    for c in ("events_v1", "events_v2", "n_ok"):
        R[c] = R[c].map(K.sup)
    R.to_csv(K.FLG / "outcome_events.csv", index=False)
    print(R.to_string(index=False))


# ================================================================ apply rules
def apply():
    import specs_v2 as SV
    K.umask()
    by_rule, by_trial = [], []
    for n in K.ALL:
        M = pd.read_parquet(K.FLG / f"restricted_meas_{n}.parquet").set_index("patient_key")
        Fo = K.CRIT / "flags" / f"restricted_flags_{n}.parquet"
        F = pd.read_parquet(Fo).set_index("patient_key").reindex(M.index) if Fo.exists() else pd.DataFrame(index=M.index)
        Dr = pd.DataFrame(index=M.index)
        prim, meas = [], []
        for r in SV.rules(n):
            d_main, d_meas = r.evaluate(M, F)
            Dr[f"rule:{r.rid}"] = d_main
            prim.append(d_main)
            meas.append(d_meas)
            by_rule.append(SV.count_row(n, r, M.treated.to_numpy(), d_main, d_meas))
        z = np.zeros(len(M), bool)
        Dr["drop_v2"] = np.logical_or.reduce(prim) if prim else z
        Dr["drop_v2meas"] = np.logical_or.reduce(meas) if meas else z
        Dr.reset_index().to_parquet(K.FLG / f"restricted_drop_{n}.parquet")
        t = M.treated.to_numpy()
        by_trial.append(SV.count_trial(n, t, Dr.drop_v2.to_numpy(), Dr.drop_v2meas.to_numpy(), [r.rid for r in SV.rules(n)]))
    pd.DataFrame(by_rule).to_csv(K.FLG / "exclusions_by_rule.csv", index=False)
    T = pd.DataFrame(by_trial)
    T.to_csv(K.FLG / "exclusions_by_trial.csv", index=False)
    pd.set_option("display.width", 250)
    print(T.to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["extract", "outcome", "apply"])
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    {"extract": lambda: extract(min(a.workers, 12)), "outcome": outcome, "apply": apply}[a.cmd]()
