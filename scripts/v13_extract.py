#!/usr/bin/env python
"""v1.3 extraction (docs/PROTOCOL_V1_3_AMENDMENT.md I8, II2, II3, II4) for one trial roster.

Adds to the frozen phase-2 outcomes (extract_outcomes.py rules unchanged):
  nco_*            expanded negative controls (trial_specs.NCO_EXT; v1.2 rules: new after index,
                   NaN if the event occurred in the prior 365 d; other deaths censor)
  t/e_primary_strict  primary composite with hospitalisation components counted only when the
                   qualifying code is the primary billing diagnosis of the stay (death components unchanged)
  pp_stop{365,180} days from index to the first protocol deviation: order of the other arm's study drug,
                   or discontinuation (no order of the assigned drug within G days after an order; date =
                   last order + G). NaN = none observed (drug designs only)
  repeat_90        >= 1 order of the assigned drug in (index, index + 90]
Restricted output: restricted_outcomes_v13.parquet; aggregate summary.json.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import code_like, connect, create_drug_tokens, mrn_key, new_private_dir, rp  # noqa: E402
from trial_specs import COD_END, DEATH_END, HORIZON_MONTHS, NCO_EXT, OUTCOMES, PRIMARY_BILLING, TRIALS  # noqa: E402

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
    r = pd.read_parquet(a.roster)[["patient_key", "person_id", "index_date", "treated"]]
    con.register("r0", r)
    con.execute("""CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx,
                   treated FROM r0""")
    spec = TRIALS[a.trial]
    comps = OUTCOMES[a.trial]
    uses_cause = any(c in ("cv_death", "chd_death") for c in comps)
    horizon_days = int(round(HORIZON_MONTHS[a.trial] * 30.4375))
    follow_days = max(horizon_days, int(round(60 * 30.4375)))
    admin_end = COD_END if uses_cause else DEATH_END

    death = con.execute(f"""SELECT r.patient_key, min(d.death_date) dd FROM r JOIN {rp(G, 'death')} d USING (person_id)
                            GROUP BY 1""").df().set_index("patient_key").dd
    cause = con.execute(f"""SELECT r.patient_key, bool_or(upper(c.condition_source_value) LIKE 'I%') any_cv,
            bool_or({code_like("upper(replace(c.condition_source_value, '.', ''))", ['I20', 'I21', 'I22', 'I23', 'I24', 'I25'])}) chd,
            count(*) n
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
            cond = f"""({cond} AND (st.s > x.idx + INTERVAL 28 DAY OR upper(replace(c.condition_source_value, '.', '')) LIKE 'I22%'))"""
        return con.execute(f"""SELECT x.patient_key, min(st.s) d FROM idxstay x
            JOIN stays st ON st.person_id = x.person_id AND st.s > x.idx_stay_end
            JOIN {rp(G, 'condition_occurrence')} c ON c.person_id = x.person_id
            WHERE c.condition_start_date BETWEEN st.s AND st.e AND {cond}
              AND c.condition_status_source_value = '{PRIMARY_BILLING}'
            GROUP BY 1""").df().set_index("patient_key").d

    idx = pd.to_datetime(r.set_index("patient_key").index_date)
    keys = idx.index
    dd = pd.to_datetime(death.reindex(keys))
    dd = dd.where(~(dd.notna() & (dd < idx)))
    has_cause = cause.reindex(keys).n.fillna(0) > 0
    any_cv = cause.reindex(keys).any_cv.astype("boolean").fillna(False).astype(bool)
    chd = cause.reindex(keys).chd.astype("boolean").fillna(False).astype(bool)
    end = pd.Series(pd.Timestamp(admin_end), index=keys).clip(upper=idx + pd.Timedelta(days=follow_days))
    res = pd.DataFrame(index=keys)
    # strict primary (hospitalisation components: primary billing diagnosis only)
    ev_dates = []
    for comp in comps:
        if comp == "death":
            ev_dates.append(dd)
        elif comp == "cv_death":
            ev_dates.append(dd.where(any_cv | ~has_cause))
        elif comp == "chd_death":
            ev_dates.append(dd.where(chd))
        else:
            is_mi = any(c_.startswith(("I21", "I22")) for c_ in comp[1])
            ev_dates.append(pd.to_datetime(first_hosp(comp[1], mi=is_mi).reindex(keys)))
    ev = pd.concat(ev_dates, axis=1).min(axis=1)
    stop = pd.concat([ev, end, dd], axis=1).min(axis=1)
    event = ev.notna() & (ev <= end) & ~(dd < ev)
    stop = stop.where(~event, ev)
    t = (stop - idx).dt.days.astype(float)
    res["t_primary_strict"], res["e_primary_strict"] = t.where(t > 0, 0.5), event.astype(int)
    has_hosp = any(isinstance(c, tuple) for c in comps)

    # expanded negative controls
    for name, (kind, codes) in NCO_EXT.items():
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
        evn = post.notna() & (post <= endn) & ~(dd < post)
        stop = stop.where(~evn, post)
        tt = (stop - idx).dt.days.astype(float)
        tt = tt.where(tt > 0, 0.5)
        ee = evn.astype(float)
        m = keys.isin(prior)
        tt[m], ee[m] = np.nan, np.nan
        res[f"t_{name}"], res[f"e_{name}"] = tt, ee

    # on-treatment periods (drug designs)
    pp_note = "not applicable (procedure design)"
    if spec.get("design") not in ("procedure", "proc_vs_drug"):  # audit fix: no drug orders in a procedure arm
        rows = [(i, kw.lower()) for i, (_, kws) in enumerate(spec["arms"]) for kw in kws]
        kwdf = pd.DataFrame(rows, columns=["arm_idx", "kw"])
        con.register("kwdf", kwdf)
        create_drug_tokens(con, G, kwdf.kw.tolist(), person_filter="r")
        o = con.execute("""SELECT DISTINCT r.patient_key, r.treated, k.arm_idx, d.d FROM r JOIN dtok d USING (person_id)
                           JOIN kwdf k ON d.tok = k.kw WHERE d.d >= r.idx""").df()
        o["d"] = pd.to_datetime(o.d)
        o = o.merge(idx.rename("idx").reset_index(), on="patient_key")
        o["own"] = (o.arm_idx == 0) == (o.treated == 1)  # arm_idx 0 = treated arm
        oth = o[~o.own & (o.d > o.idx)]
        if spec.get("add_on"):  # audit fix: add-on designs (EAST-AFNET 4) keep the comparator drug in the treated arm
            oth = oth[oth.treated == 0]
        other = oth.groupby("patient_key").d.min().reindex(keys)
        own = o[o.own][["patient_key", "d"]].drop_duplicates()
        own = pd.concat([own, idx.rename("d").reset_index()]).drop_duplicates().sort_values(["patient_key", "d"])
        own["nxt"] = own.groupby("patient_key").d.shift(-1)
        rep90 = o[o.own & (o.d > o.idx) & (o.d <= o.idx + pd.Timedelta(days=90))].patient_key.unique()
        res["repeat_90"] = keys.isin(rep90).astype(int)
        res["pp_switch"] = (other - idx).dt.days.astype(float)  # v1.3 deviation 2: switch-only censoring
        for Gd in (365, 180, 730):  # 730: v1.3 deviation 1
            gap = own[(own.nxt.isna()) | ((own.nxt - own.d).dt.days > Gd)]
            disc = (gap.groupby("patient_key").d.min() + pd.Timedelta(days=Gd)).reindex(keys)
            dev = pd.concat([disc, other], axis=1).min(axis=1)
            res[f"pp_stop{Gd}"] = (dev - idx).dt.days.astype(float)
        pp_note = "orders of arm keywords; other-arm order or gap > G"
    res.index.name = "patient_key"
    res.reset_index().to_parquet(out / "restricted_outcomes_v13.parquet")
    sup = lambda n: int(n) if (n == 0 or n >= 11) else "<11"
    summ = dict(trial=a.trial, n=int(len(res)), strict_has_hosp_component=has_hosp,
                strict_events=sup(res.e_primary_strict.sum()),
                nco_events={k: sup(np.nansum(res[f"e_{k}"])) for k in NCO_EXT}, per_protocol=pp_note)
    if "pp_stop365" in res:
        summ["share_deviating_by_horizon_G365"] = round(float((res.pp_stop365 <= horizon_days).mean()), 3)
        summ["share_deviating_by_horizon_G180"] = round(float((res.pp_stop180 <= horizon_days).mean()), 3)
        summ["share_deviating_by_horizon_G730"] = round(float((res.pp_stop730 <= horizon_days).mean()), 3)
        summ["share_switching_by_horizon"] = round(float((res.pp_switch <= horizon_days).mean()), 3)
        summ["share_repeat_90"] = round(float(res.repeat_90.mean()), 3)
    json.dump(summ, open(out / "summary.json", "w"), indent=2)
    print(json.dumps(summ))


if __name__ == "__main__":
    main()
