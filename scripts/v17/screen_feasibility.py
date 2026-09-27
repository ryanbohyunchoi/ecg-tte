#!/usr/bin/env python
"""v1.7 count-only feasibility screen for one candidate trial (docs/v16/V17_CONFIRMATION_PLAN.md B).

Inputs: a cohort built by build_trial_cohort.py and an ECG selection by select_cohort_ecgs.py select.
Reports (aggregate only, counts 1-10 suppressed):
  n per arm; n per arm with a selected ECG in [index-365, index] (the analysis-population gate);
  pooled (arms ignored) primary-composite events within the trial horizon, among all cohort patients and among
  those with an ECG, using the extract_outcomes.py v1.2 event rules (first component event; inpatient stays merged;
  index-stay events excluded; MI codes within 28 d need I22; CV death = any listed I-cause or no cause record;
  follow-up to min(horizon, admin end)); pooled all-cause deaths within the horizon.
Treatment is never read by the event part: the roster passed to it has no arm column, and only pooled sums are kept.
No per-patient outcome is written anywhere. Patient overlap with the 18 v1.6 trial cohorts is reported as a count.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from trial_common import code_like, connect, mrn_key, rp  # noqa: E402
from trial_specs import COD_END, DEATH_END, HORIZON_MONTHS, OUTCOMES  # noqa: E402

B = "/mnt/raid0/bb2238/ecg_ascvd/omop_database"
G = "/mnt/raid0/rbc58/omop/gold"


def sup(n):
    n = int(n)
    return n if (n == 0 or n >= 11) else "<11"


def pooled_events(r: pd.DataFrame, trial: str, threads: int = 16) -> pd.Series:
    """Boolean Series (index patient_key) of a primary event within the horizon; r has patient_key, person_id, index_date only."""
    assert set(r.columns) == {"patient_key", "person_id", "index_date"}
    con = connect(threads)
    con.register("r0", r)
    con.execute("CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx FROM r0")
    comps = OUTCOMES[trial]
    uses_cause = any(c in ("cv_death", "chd_death") for c in comps)
    H = int(round(HORIZON_MONTHS[trial] * 30.4375))
    admin_end = COD_END if uses_cause else DEATH_END
    death = con.execute(f"SELECT r.patient_key, min(d.death_date) dd FROM r JOIN {rp(G, 'death')} d USING (person_id) GROUP BY 1").df().set_index("patient_key").dd
    cause = con.execute(f"""SELECT r.patient_key, bool_or(upper(c.condition_source_value) LIKE 'I%') any_cv,
            bool_or({code_like("upper(replace(c.condition_source_value, '.', ''))", ['I20', 'I21', 'I22', 'I23', 'I24', 'I25'])}) chd, count(*) n
        FROM r JOIN (SELECT person_id, {mrn_key('person_source_value')} k FROM {rp(G, 'person')}) gp USING (person_id)
        JOIN (SELECT person_id apid, {mrn_key('PAT_MRN_ID')} k FROM read_parquet('{B}/person/*.parquet')) ap ON ap.k = gp.k
        JOIN read_parquet('{B}/condition_occurrence/condition_occurrence_ct_vitals.parquet') c ON c.person_id = ap.apid
        GROUP BY 1""").df().set_index("patient_key")
    con.execute(f"""CREATE TEMP TABLE iv AS SELECT v.person_id, v.visit_start_date s, coalesce(v.visit_end_date, v.visit_start_date) e
        FROM {rp(G, 'visit_occurrence')} v WHERE v.visit_concept_id = 9201 AND v.person_id IN (SELECT person_id FROM r)""")
    con.execute("""CREATE TEMP TABLE stays AS
        WITH o AS (SELECT *, max(e) OVER (PARTITION BY person_id ORDER BY s, e ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) pe FROM iv),
             g AS (SELECT *, sum(CASE WHEN pe IS NULL OR s > pe + INTERVAL 1 DAY THEN 1 ELSE 0 END)
                            OVER (PARTITION BY person_id ORDER BY s, e ROWS UNBOUNDED PRECEDING) gid FROM o)
        SELECT person_id, gid, min(s) s, max(e) e FROM g GROUP BY 1, 2""")
    con.execute("""CREATE TEMP TABLE idxstay AS SELECT r.patient_key, r.person_id, r.idx,
            coalesce(max(st.e) FILTER (WHERE st.s <= r.idx AND st.e >= r.idx), r.idx) idx_stay_end
        FROM r LEFT JOIN stays st USING (person_id) GROUP BY 1, 2, 3""")

    def first_hosp(codes, mi=False):
        cond = code_like("upper(replace(c.condition_source_value, '.', ''))", codes)
        if mi:
            cond = f"({cond} AND (st.s > x.idx + INTERVAL 28 DAY OR upper(replace(c.condition_source_value, '.', '')) LIKE 'I22%'))"
        return con.execute(f"""SELECT x.patient_key, min(st.s) d FROM idxstay x
            JOIN stays st ON st.person_id = x.person_id AND st.s > x.idx_stay_end
            JOIN {rp(G, 'condition_occurrence')} c ON c.person_id = x.person_id
            WHERE c.condition_start_date BETWEEN st.s AND st.e AND {cond} GROUP BY 1""").df().set_index("patient_key").d

    idx = pd.to_datetime(r.set_index("patient_key").index_date)
    keys = idx.index
    dd = pd.to_datetime(death.reindex(keys))
    dd = dd.where(~(dd.notna() & (dd < idx)))
    has_cause = cause.reindex(keys).n.fillna(0) > 0
    any_cv = cause.reindex(keys).any_cv.fillna(False).astype(bool)
    chd = cause.reindex(keys).chd.fillna(False).astype(bool)
    end = pd.Series(pd.Timestamp(admin_end), index=keys).clip(upper=idx + pd.Timedelta(days=H))
    ev_dates = []
    for comp in comps:
        if comp == "death":
            ev_dates.append(dd)
        elif comp == "cv_death":
            ev_dates.append(dd.where(any_cv | ~has_cause))
        elif comp == "chd_death":
            ev_dates.append(dd.where(chd))
        else:
            ev_dates.append(pd.to_datetime(first_hosp(comp[1], mi=any(c.startswith(("I21", "I22")) for c in comp[1])).reindex(keys)))
    ev = pd.concat(ev_dates, axis=1).min(axis=1)
    event = ev.notna() & (ev <= end) & ~(dd < ev) & (idx < pd.Timestamp(admin_end))
    death_h = dd.notna() & (dd <= idx + pd.Timedelta(days=H)) & (dd <= pd.Timestamp(DEATH_END))
    return event, death_h


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--cohort-dir", required=True)
    ap.add_argument("--selection-dir", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--threads", type=int, default=16)
    a = ap.parse_args()
    os.umask(0o077)
    coh = pd.read_parquet(f"{a.cohort_dir}/restricted_cohort.parquet")
    sel = pd.read_parquet(f"{a.selection_dir}/restricted_selection.parquet", columns=["patient_key"])
    coh["ecg"] = coh.patient_key.isin(set(sel.patient_key))
    arms = coh.groupby("treatment_arm", sort=False).agg(n=("ecg", "size"), n_ecg=("ecg", "sum"))
    ev, dh = pooled_events(coh[["patient_key", "person_id", "index_date"]].copy(), a.trial, a.threads)
    ecgk = coh.set_index("patient_key").ecg
    # overlap with the 18 v1.6 cohorts (count of this cohort's patients appearing in any of them)
    sys.path.insert(0, str(HERE.parent))
    from v13_common import A, EXTRA, PRIMARY  # noqa: E402
    from make_acc_figure import trials as T18  # noqa: E402
    names = {**PRIMARY, **EXTRA}
    other = set()
    per = {}
    for n in T18:
        k = set(pd.read_parquet(f"{A}/{names[n][1]}/restricted_cohort.parquet", columns=["patient_key"]).patient_key)
        per[n] = len(k & set(coh.patient_key))
        other |= k
    top = sorted(per.items(), key=lambda x: -x[1])[:3]
    res = dict(trial=a.trial, n=sup(len(coh)),
               arms={str(k): dict(n=sup(v.n), n_with_ecg=sup(v.n_ecg), frac_ecg=round(v.n_ecg / v.n, 3) if v.n else None) for k, v in arms.iterrows()},
               min_arm_with_ecg=int(arms.n_ecg.min()) if int(arms.n_ecg.min()) >= 11 or int(arms.n_ecg.min()) == 0 else "<11",
               horizon_months=HORIZON_MONTHS[a.trial], outcome=[str(c) for c in OUTCOMES[a.trial]],
               pooled_primary_events_horizon=sup(ev.sum()), pooled_primary_events_horizon_with_ecg=sup(ev[ecgk.reindex(ev.index).to_numpy()].sum()),
               pooled_deaths_horizon=sup(dh.sum()),
               overlap_with_v16_18_cohorts=sup(len(other & set(coh.patient_key))),
               overlap_top3={k: sup(v) for k, v in top},
               index_years=[int(pd.to_datetime(coh.index_date).dt.year.min()), int(pd.to_datetime(coh.index_date).dt.year.max())] if len(coh) else None)
    Path(a.out_json).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(a.out_json, "w"), indent=1, default=str)
    print(json.dumps(res, default=str))


if __name__ == "__main__":
    main()
