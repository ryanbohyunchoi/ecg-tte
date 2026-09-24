#!/usr/bin/env python
"""Build an adapted active-comparator new-user cohort from OMOP gold.

Spec: scripts/trial_specs.py (one versioned dict per trial). Steps, recorded in
attrition.csv per arm (aggregate, cells 1-10 suppressed):
  1. first-ever order of an arm drug (token match) with index in [index_start, index_end]
  2. no order of the other arm's drug in [index-365, index]
  3. age >= 18 at index; earliest visit_occurrence <= index-365 (prior activity)
  4. person eligible for both arms -> kept once, at the earliest index
  5. disease gate (spec['gate'])
  6. declared exclusions (spec['exclusions']); an unknown value passes (adaptation)

Treatment time zero is the index order date. Nothing after index is read except
nothing: exclusions and gates look only at data on/before index.

Outputs (restricted, private run directory):
  restricted_cohort.parquet  patient_key (=person_source_value), person_id,
                             treatment_arm, treated (1 = first arm), index_date
  attrition.csv, summary.json, manifest.json
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import code_like, connect, create_drug_tokens, mrn_key, new_private_dir, rp, sha256, suppress, write_manifest  # noqa: E402
from trial_specs import TRIALS  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", required=True, choices=sorted(TRIALS))
    ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
    ap.add_argument("--echo-metadata", default="/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--threads", type=int, default=48)
    a = ap.parse_args()
    spec = TRIALS[a.trial]
    out = new_private_dir(a.output_dir)
    G = a.omop_dir
    con = connect(a.threads)

    con.execute(f"""CREATE TEMP TABLE person AS SELECT person_id, person_source_value patient_key,
        CAST(birth_datetime AS DATE) dob, {mrn_key('person_source_value')} k FROM {rp(G, 'person')}""")
    rows = [(i, arm, kw.lower()) for i, (arm, kws) in enumerate(spec["arms"]) for kw in kws]
    con.register("kw_df", pd.DataFrame(rows, columns=["arm_idx", "arm", "kw"]))
    create_drug_tokens(con, G, [r[2] for r in rows])
    con.execute("""CREATE TEMP TABLE armexp AS SELECT DISTINCT k.arm_idx, d.person_id, d.d
                   FROM dtok d JOIN kw_df k ON d.tok = k.kw""")
    con.execute(f"""CREATE TEMP TABLE s1 AS SELECT * FROM
        (SELECT arm_idx, person_id, min(d) idx FROM armexp GROUP BY 1, 2)
        WHERE idx BETWEEN DATE '{spec['index_start']}' AND DATE '{spec['index_end']}'""")
    con.execute("""CREATE TEMP TABLE s2 AS SELECT c.* FROM s1 c WHERE NOT EXISTS (
        SELECT 1 FROM armexp e WHERE e.person_id = c.person_id AND e.arm_idx <> c.arm_idx
          AND e.d BETWEEN c.idx - INTERVAL 365 DAY AND c.idx)""")
    con.execute(f"""CREATE TEMP TABLE firstvisit AS SELECT person_id, min(visit_start_date) fv
                    FROM {rp(G, 'visit_occurrence')} GROUP BY 1""")
    con.execute("""CREATE TEMP TABLE s3 AS SELECT c.* FROM s2 c JOIN person p USING (person_id)
        JOIN firstvisit v USING (person_id)
        WHERE p.dob IS NOT NULL AND date_diff('year', p.dob, c.idx)
              - (CASE WHEN strftime(c.idx, '%m%d') < strftime(p.dob, '%m%d') THEN 1 ELSE 0 END) >= 18
          AND v.fv <= c.idx - INTERVAL 365 DAY""")
    con.execute("""CREATE TEMP TABLE s4 AS SELECT arm_idx, person_id, idx FROM (
        SELECT *, row_number() OVER (PARTITION BY person_id ORDER BY idx, arm_idx) rn FROM s3) WHERE rn = 1""")

    # conditions needed for gate/exclusions (on/before index only)
    gate = spec["gate"]
    ex = spec["exclusions"]
    prefixes = sorted({p for v in gate.values() for p in v} | set(ex.get("ever_codes", [])) | {"I50"})
    con.execute(f"""CREATE TEMP TABLE cond AS SELECT c.person_id, c.idx, x.d, x.code FROM s4 c JOIN (
        SELECT person_id, condition_start_date d, upper(replace(condition_source_value, '.', '')) code
        FROM {rp(G, 'condition_occurrence')}
        WHERE person_id IN (SELECT person_id FROM s4) AND condition_start_date IS NOT NULL) x
        USING (person_id) WHERE x.d <= c.idx AND {code_like('x.code', prefixes)}""")
    conds = []
    if "any_before_or_on_index" in gate:
        conds.append(code_like("code", gate["any_before_or_on_index"]))
    if "window_30d" in gate:
        conds.append(f"({code_like('code', gate['window_30d'])} AND d >= idx - INTERVAL 30 DAY)")
    con.execute(f"CREATE TEMP TABLE s5 AS SELECT * FROM s4 WHERE person_id IN "
                f"(SELECT person_id FROM cond WHERE {' OR '.join(conds)})")

    stages = [("s1_first_use_in_window", "s1"), ("s2_comparator_washout_365", "s2"),
              ("s3_age18_prior_activity_365", "s3"), ("s4_dedupe_earliest_index", "s4"),
              ("s5_disease_gate", "s5")]
    cur = "s5"
    step = 6

    def apply(name, where_not_exists_sql):
        nonlocal cur, step
        nxt = f"s{step}"
        con.execute(f"CREATE TEMP TABLE {nxt} AS SELECT * FROM {cur} c WHERE NOT ({where_not_exists_sql})")
        stages.append((f"{nxt}_{name}", nxt))
        cur, step = nxt, step + 1

    def latest_measure(cid, days):
        return f"""(SELECT arg_max(m.value_as_number, m.measurement_date) FROM meas m
                    WHERE m.person_id = c.person_id AND m.cid = {cid}
                      AND m.measurement_date BETWEEN c.idx - INTERVAL {days} DAY AND c.idx - INTERVAL 1 DAY)"""

    need_meas = [cid for key, cid in (("egfr_lt", 40764999), ("potassium_gt", 3023103), ("sbp_lt", 4152194)) if key in ex]
    if need_meas:
        con.execute(f"""CREATE TEMP TABLE meas AS SELECT person_id, measurement_concept_id cid, measurement_date,
            value_as_number FROM {rp(G, 'measurement')}
            WHERE measurement_concept_id IN ({','.join(map(str, need_meas))}) AND value_as_number IS NOT NULL
              AND person_id IN (SELECT person_id FROM s5)""")
    if "lvef_gt" in ex or ex.get("hfpef_code_only"):
        con.execute(f"""CREATE TEMP TABLE echo AS SELECT {mrn_key('MRN')} k, try_cast(EchoDate AS DATE) d, EF
            FROM read_parquet('{a.echo_metadata}') WHERE EF BETWEEN 5 AND 90 AND try_cast(EchoDate AS DATE) IS NOT NULL""")
        con.execute(f"""CREATE TEMP TABLE ef AS SELECT c.person_id, arg_max(e.EF, e.d) ef FROM {cur} c
            JOIN person p USING (person_id) JOIN echo e ON e.k = p.k
            WHERE e.d BETWEEN c.idx - INTERVAL 365 DAY AND c.idx - INTERVAL 1 DAY GROUP BY 1""")
    if "lvef_gt" in ex:
        apply(f"latest_lvef_gt_{ex['lvef_gt']}",
              f"EXISTS (SELECT 1 FROM ef WHERE ef.person_id = c.person_id AND ef.ef > {ex['lvef_gt']})")
    if ex.get("hfpef_code_only"):
        apply("hfpef_code_without_hfref_code_ef_unknown",
              f"""NOT EXISTS (SELECT 1 FROM ef WHERE ef.person_id = c.person_id)
                  AND EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id AND x.code LIKE 'I503%')
                  AND NOT EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id
                                  AND (x.code LIKE 'I502%' OR x.code LIKE 'I504%'))""")
    if "egfr_lt" in ex:
        apply(f"latest_egfr_lt_{ex['egfr_lt']}", f"coalesce({latest_measure(40764999, 90)} < {ex['egfr_lt']}, false)")
    if "potassium_gt" in ex:
        apply(f"latest_potassium_gt_{ex['potassium_gt']}", f"coalesce({latest_measure(3023103, 90)} > {ex['potassium_gt']}, false)")
    if "sbp_lt" in ex:
        apply(f"latest_sbp_lt_{ex['sbp_lt']}", f"coalesce({latest_measure(4152194, 90)} < {ex['sbp_lt']}, false)")
    if ex.get("ever_codes"):
        apply("history_codes_" + "_".join(ex["ever_codes"]),
              f"EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id AND x.d < c.idx AND "
              f"{code_like('x.code', ex['ever_codes'])})")
    for key, days in (("anticoag_30d", 30), ("other_anticoag_365d", 365)):
        if key in ex:
            create_drug_tokens(con, G, ex[key], table=f"tok_{key}", person_filter=cur)
            apply(key, f"""EXISTS (SELECT 1 FROM tok_{key} o WHERE o.person_id = c.person_id
                          AND o.d BETWEEN c.idx - INTERVAL {days} DAY AND c.idx)""")

    arms = [arm for arm, _ in spec["arms"]]
    att = []
    for name, tbl in stages:
        n = dict(con.execute(f"SELECT arm_idx, count(*) FROM {tbl} GROUP BY 1").fetchall())
        att.append(dict(step=name, **{arm: suppress(n.get(i, 0)) for i, arm in enumerate(arms)}))
    pd.DataFrame(att).to_csv(out / "attrition.csv", index=False)

    coh = con.execute(f"""SELECT p.patient_key, c.person_id, c.arm_idx, c.idx index_date FROM {cur} c
                          JOIN person p USING (person_id) ORDER BY c.person_id""").df()
    if coh.patient_key.isna().any() or coh.patient_key.duplicated().any():
        raise SystemExit("patient_key missing or duplicated; stopping (identity contract)")
    coh["treatment_arm"] = coh.arm_idx.map(dict(enumerate(arms)))
    coh["treated"] = (coh.arm_idx == 0).astype(int)
    coh["index_date"] = pd.to_datetime(coh.index_date).dt.date
    coh[["patient_key", "person_id", "treatment_arm", "treated", "index_date"]].to_parquet(out / "restricted_cohort.parquet")
    years = pd.to_datetime(coh.index_date).dt.year
    summary = dict(trial=a.trial, spec_version=spec["spec_version"], n=int(len(coh)),
                   by_arm={k: suppress(v) for k, v in coh.treatment_arm.value_counts().items()},
                   index_year_range=[int(years.min()), int(years.max())],
                   attrition=att, spec={k: v for k, v in spec.items() if k != "drugs_90d"})
    json.dump(summary, open(out / "summary.json", "w"), indent=2, default=str)
    write_manifest(out, dict(script_sha256=sha256(Path(__file__)), spec_sha256=sha256(Path(__file__).with_name("trial_specs.py")),
                             omop_dir=G))
    print(pd.DataFrame(att).to_string(index=False))


if __name__ == "__main__":
    main()
