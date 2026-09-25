#!/usr/bin/env python
"""Phase-2 outcome extraction (protocol v1 4b/8; frozen before this code ran).

For a trial roster (patient_key, person_id, index_date): time-to-event (days from index; follow-up
starts the day after index) and event indicator for
  primary   the trial's composite (trial_specs.OUTCOMES), first component event
  nco_*     negative-control outcomes (trial_specs.NCO); NaN for patients with the event in the prior 365 d
Censoring: max(trial horizon, 60 months) (phase 2 truncates to the trial horizon / 12 / 60 months), end of data (death 2024-12-31; composites that include
CV/CHD death: 2024-06-24, end of cause-of-death records), or death from other causes (cause-specific).
Horizon sensitivities (12, 60 months) are applied downstream by truncation.
Variants: primary_cvnoncause (deaths without a cause record counted as non-CV).
Outputs restricted_outcomes.parquet and an aggregate summary.json (event counts pooled over arms only).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import code_like, connect, mrn_key, new_private_dir, rp  # noqa: E402
from trial_specs import COD_END, DEATH_END, HORIZON_MONTHS, NCO, OUTCOMES  # noqa: E402

B = "/mnt/raid0/bb2238/ecg_ascvd/omop_database"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--roster", required=True)
    ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
    ap.add_argument("--output-dir", required=True)
    a = ap.parse_args()
    out = new_private_dir(a.output_dir)
    G = a.omop_dir
    con = connect(48)
    r = pd.read_parquet(a.roster)[["patient_key", "person_id", "index_date"]]
    con.register("r0", r)
    con.execute("CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx FROM r0")
    comps = OUTCOMES[a.trial]
    uses_cause = any(c in ("cv_death", "chd_death") for c in comps)
    horizon_days = int(round(HORIZON_MONTHS[a.trial] * 30.4375))
    follow_days = max(horizon_days, int(round(60 * 30.4375)))  # follow to max(trial horizon, 60 mo); phase 2 truncates
    admin_end = COD_END if uses_cause else DEATH_END

    # deaths (gold) and causes (CT Vital Statistics, linked by MRN)
    death = con.execute(f"""SELECT r.patient_key, min(d.death_date) dd FROM r JOIN {rp(G, 'death')} d USING (person_id)
                            GROUP BY 1""").df().set_index("patient_key").dd
    cause = con.execute(f"""SELECT r.patient_key,
            bool_or(upper(c.condition_source_value) LIKE 'I%') any_cv,
            bool_or({code_like("upper(replace(c.condition_source_value, '.', ''))", ['I20', 'I21', 'I22', 'I23', 'I24', 'I25'])}) chd,
            count(*) n
        FROM r JOIN (SELECT person_id, {mrn_key('person_source_value')} k FROM {rp(G, 'person')}) gp USING (person_id)
        JOIN (SELECT person_id apid, {mrn_key('PAT_MRN_ID')} k FROM read_parquet('{B}/person/*.parquet')) ap ON ap.k = gp.k
        JOIN read_parquet('{B}/condition_occurrence/condition_occurrence_ct_vitals.parquet') c ON c.person_id = ap.apid
        GROUP BY 1""").df().set_index("patient_key")

    def first_hosp(codes):
        return con.execute(f"""SELECT r.patient_key, min(v.visit_start_date) d FROM r
            JOIN {rp(G, 'visit_occurrence')} v USING (person_id)
            JOIN {rp(G, 'condition_occurrence')} c ON c.person_id = r.person_id
            WHERE v.visit_concept_id = 9201 AND v.visit_start_date > r.idx
              AND c.condition_start_date BETWEEN v.visit_start_date AND coalesce(v.visit_end_date, v.visit_start_date)
              AND {code_like("upper(replace(c.condition_source_value, '.', ''))", codes)}
            GROUP BY 1""").df().set_index("patient_key").d

    idx = pd.to_datetime(r.set_index("patient_key").index_date)
    keys = idx.index
    dd = pd.to_datetime(death.reindex(keys))
    dd = dd.where(dd > idx)                     # deaths on/before index are data errors: not events
    has_cause = cause.reindex(keys).n.fillna(0) > 0
    any_cv = cause.reindex(keys).any_cv.fillna(False).astype(bool)
    chd = cause.reindex(keys).chd.fillna(False).astype(bool)
    end = pd.Series(pd.Timestamp(admin_end), index=keys).clip(upper=idx + pd.Timedelta(days=follow_days))

    def build(cv_rule):
        ev_dates = []
        for comp in comps:
            if comp == "death":
                ev_dates.append(dd)
            elif comp == "cv_death":
                is_cv = any_cv | (~has_cause if cv_rule == "nocause_cv" else False)
                ev_dates.append(dd.where(is_cv))
            elif comp == "chd_death":
                ev_dates.append(dd.where(chd))
            else:
                ev_dates.append(pd.to_datetime(first_hosp(comp[1]).reindex(keys)))
        ev = pd.concat(ev_dates, axis=1).min(axis=1)
        stop = pd.concat([ev, end, dd], axis=1).min(axis=1)  # other-cause death censors
        event = ev.notna() & (ev <= end)
        stop = stop.where(~event, ev)
        t = (stop - idx).dt.days.clip(lower=1)
        return t, event.astype(int)

    res = pd.DataFrame(index=keys)
    res["t_primary"], res["e_primary"] = build("nocause_cv")
    if uses_cause:
        res["t_primary_cvnoncause"], res["e_primary_cvnoncause"] = build("nocause_noncv")
    # negative controls
    for name, (kind, codes) in NCO.items():
        if kind == "proc":
            q = f"""SELECT r.patient_key, p.procedure_date d FROM r JOIN {rp(G, 'procedure_occurrence')} p USING (person_id)
                    WHERE {code_like('upper(p.procedure_source_value)', codes)}"""
        else:
            q = f"""SELECT r.patient_key, c.condition_start_date d FROM r JOIN {rp(G, 'condition_occurrence')} c USING (person_id)
                    WHERE {code_like("upper(replace(c.condition_source_value, '.', ''))", codes)}"""
        e = con.execute(q).df()
        e["d"] = pd.to_datetime(e.d)
        e = e.merge(idx.rename("idx").reset_index(), on="patient_key")
        prior = set(e[(e.d >= e.idx - pd.Timedelta(days=365)) & (e.d <= e.idx)].patient_key)
        post = e[e.d > e.idx].groupby("patient_key").d.min().reindex(keys)
        endn = pd.Series(pd.Timestamp(DEATH_END), index=keys).clip(upper=idx + pd.Timedelta(days=follow_days))
        stop = pd.concat([post, endn, dd], axis=1).min(axis=1)
        ev = post.notna() & (post <= endn) & ~(dd < post)
        stop = stop.where(~ev, post)
        tt = (stop - idx).dt.days.clip(lower=1).astype(float)
        ee = ev.astype(float)
        m = keys.isin(prior)
        tt[m], ee[m] = np.nan, np.nan
        res[f"t_{name}"], res[f"e_{name}"] = tt, ee
    res.index.name = "patient_key"
    res.reset_index().to_parquet(out / "restricted_outcomes.parquet")
    summ = dict(trial=a.trial, n=int(len(res)), horizon_days=horizon_days, follow_days=follow_days, admin_end=admin_end, components=[str(c) for c in comps],
                events_primary=int(res.e_primary.sum()), deaths_after_index=int(dd.notna().sum()),
                deaths_with_cause_record=int((dd.notna() & has_cause).sum()),
                nco_events={k: int(np.nansum(res[f"e_{k}"])) for k in NCO})
    json.dump(summ, open(out / "summary.json", "w"), indent=2)
    print(json.dumps(summ))


if __name__ == "__main__":
    main()
