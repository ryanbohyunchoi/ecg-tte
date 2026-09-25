#!/usr/bin/env python
"""v1.4 E: time to first hospitalisation for heart failure (inpatient stay starting after the index
stay with an I50 code recorded during the stay; v1.2 stay rules). Censoring: death, trial horizon
(and 60 months), end of data 2024-12-31. Also flags an I50 stay in the 365 d before index.
Restricted output restricted_hf_outcome.parquet; aggregate summary.json.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import code_like, connect, new_private_dir, rp  # noqa: E402
from trial_specs import DEATH_END, HORIZON_MONTHS  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--roster", required=True)
    ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
    ap.add_argument("--output-dir", required=True)
    a = ap.parse_args()
    out = new_private_dir(a.output_dir)
    G = a.omop_dir
    con = connect(32)
    r = pd.read_parquet(a.roster)[["patient_key", "person_id", "index_date"]]
    con.register("r0", r)
    con.execute("CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx FROM r0")
    H = int(round(HORIZON_MONTHS[a.trial] * 30.4375))
    follow = max(H, int(round(60 * 30.4375)))
    death = con.execute(f"""SELECT r.patient_key, min(d.death_date) dd FROM r JOIN {rp(G, 'death')} d USING (person_id) GROUP BY 1""").df().set_index("patient_key").dd
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
    cond = code_like("upper(replace(c.condition_source_value, '.', ''))", ["I50"])
    hf = con.execute(f"""SELECT x.patient_key, min(st.s) d FROM idxstay x
        JOIN stays st ON st.person_id = x.person_id AND st.s > x.idx_stay_end
        JOIN {rp(G, 'condition_occurrence')} c ON c.person_id = x.person_id
        WHERE c.condition_start_date BETWEEN st.s AND st.e AND {cond} GROUP BY 1""").df().set_index("patient_key").d
    prior = con.execute(f"""SELECT DISTINCT x.patient_key FROM idxstay x
        JOIN stays st ON st.person_id = x.person_id AND st.s >= x.idx - INTERVAL 365 DAY AND st.s <= x.idx
        JOIN {rp(G, 'condition_occurrence')} c ON c.person_id = x.person_id
        WHERE c.condition_start_date BETWEEN st.s AND st.e AND {cond}""").df().patient_key
    idx = pd.to_datetime(r.set_index("patient_key").index_date)
    keys = idx.index
    dd = pd.to_datetime(death.reindex(keys))
    bad = dd.notna() & (dd < idx)
    dd = dd.where(~bad)
    ev = pd.to_datetime(hf.reindex(keys))
    end = pd.Series(pd.Timestamp(DEATH_END), index=keys).clip(upper=idx + pd.Timedelta(days=follow))
    stop = pd.concat([ev, end, dd], axis=1).min(axis=1)
    event = ev.notna() & (ev <= end) & ~(dd < ev)
    stop = stop.where(~event, ev)
    t = (stop - idx).dt.days.astype(float)
    res = pd.DataFrame({"t_hf": t.where(t > 0, 0.5), "e_hf": event.astype(int),
                        "prior_hf_hosp_365": keys.isin(set(prior)).astype(int),
                        "exclude": (bad | (idx >= pd.Timestamp(DEATH_END))).astype(int)}, index=keys)
    res.index.name = "patient_key"
    res.reset_index().to_parquet(out / "restricted_hf_outcome.parquet")
    sup = lambda n: int(n) if (n == 0 or n >= 11) else "<11"
    h = (res.t_hf <= H) & (res.e_hf == 1)
    s = dict(trial=a.trial, n=int(len(res)), hf_events_by_horizon=sup(h.sum()), share_prior_hf_hosp=round(float(res.prior_hf_hosp_365.mean()), 3))
    json.dump(s, open(out / "summary.json", "w"), indent=2)
    print(json.dumps(s))


if __name__ == "__main__":
    main()
