#!/usr/bin/env python
"""External reference set for a prognostic score (Stuart, Lee & Leacy 2013 style).

The score is fitted on patients OUTSIDE the trial cohort; no outcome of any
cohort patient is read. Per trial (trial_specs[...]['prognostic']):
  population  persons with a gate code (HF: I50 on/before; ACS: I21/I24/I20.0 in the
              30 days before; AF: I48 on/before) at a pseudo-index date, never in
              the cohort (all cohort person_ids excluded, whatever their date)
  pseudo-index one visit date per person (any visit concept 9201/9202/9203), seeded
              random choice among dates that satisfy the gate, age >= 18,
              >= 365 d prior activity, alive, and index in [spec index_start,
              --last-index] so that 365 d of death capture exist (death data are
              taken to end 2024-12)
  outcome     death in (index, index+365] OR an inpatient visit (9201) starting in
              (index, index+365] with a declared hosp_code recorded between its
              start and end dates. Loss to follow-up is not modelled (binary 1-year
              outcome; EHR out-of-network events are missed).
Output: restricted_reference.parquet (patient_key, person_id, index_date, outcome),
summary.json (n, event rate).
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import code_like, connect, new_private_dir, rp, sha256, write_manifest  # noqa: E402
from trial_specs import TRIALS  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", required=True, choices=sorted(TRIALS))
    ap.add_argument("--cohort", required=True, help="restricted_cohort.parquet of the trial (excluded)")
    ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
    ap.add_argument("--last-index", default="2023-12-31")
    ap.add_argument("--n", type=int, default=30000)
    ap.add_argument("--seed", type=int, default=20260923)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--threads", type=int, default=48)
    a = ap.parse_args()
    spec = TRIALS[a.trial]
    pg = spec["prognostic"]
    out = new_private_dir(a.output_dir)
    G = a.omop_dir
    con = connect(a.threads)
    con.register("coh_df", pd.read_parquet(a.cohort)[["person_id"]])
    con.execute("CREATE TEMP TABLE excl AS SELECT DISTINCT CAST(person_id AS BIGINT) person_id FROM coh_df")
    gate = spec["gate"]
    codes = gate.get("any_before_or_on_index") or gate.get("window_30d")
    within30 = "window_30d" in gate
    con.execute(f"""CREATE TEMP TABLE g AS SELECT person_id, condition_start_date d FROM {rp(G, 'condition_occurrence')}
        WHERE condition_start_date IS NOT NULL AND {code_like("upper(replace(condition_source_value, '.', ''))", codes)}
          AND person_id NOT IN (SELECT person_id FROM excl)""")
    con.execute("CREATE TEMP TABLE gfirst AS SELECT person_id, min(d) d0 FROM g GROUP BY 1")
    con.execute(f"""CREATE TEMP TABLE firstvisit AS SELECT person_id, min(visit_start_date) fv
                    FROM {rp(G, 'visit_occurrence')} GROUP BY 1""")
    con.execute(f"""CREATE TEMP TABLE death AS SELECT person_id, min(death_date) dd FROM {rp(G, 'death')} GROUP BY 1""")
    con.execute(f"""CREATE TEMP TABLE cand AS SELECT DISTINCT v.person_id, v.visit_start_date idx
        FROM {rp(G, 'visit_occurrence')} v JOIN gfirst f USING (person_id)
        JOIN firstvisit fv USING (person_id)
        JOIN (SELECT person_id, person_source_value, CAST(birth_datetime AS DATE) dob FROM {rp(G, 'person')}) p USING (person_id)
        LEFT JOIN death d USING (person_id)
        WHERE v.visit_concept_id IN (9201, 9202, 9203)
          AND v.visit_start_date BETWEEN DATE '{spec['index_start']}' AND DATE '{a.last_index}'
          AND v.visit_start_date >= f.d0 AND fv.fv <= v.visit_start_date - INTERVAL 365 DAY
          AND date_diff('day', p.dob, v.visit_start_date) >= 18 * 365.25
          AND (d.dd IS NULL OR d.dd > v.visit_start_date)""")
    if within30:
        con.execute("""DELETE FROM cand c WHERE NOT EXISTS (SELECT 1 FROM g WHERE g.person_id = c.person_id
                       AND g.d BETWEEN c.idx - INTERVAL 30 DAY AND c.idx)""")
    con.execute(f"SELECT setseed({(a.seed % 1000) / 1000})")
    con.execute(f"""CREATE TEMP TABLE ref AS SELECT person_id, idx FROM (
        SELECT *, row_number() OVER (PARTITION BY person_id ORDER BY hash(person_id, idx, {a.seed})) rn FROM cand)
        WHERE rn = 1 ORDER BY hash(person_id, {a.seed}) LIMIT {a.n}""")
    hosp = pg["hosp_codes"]
    con.execute(f"""CREATE TEMP TABLE hospev AS SELECT DISTINCT r.person_id FROM ref r
        JOIN {rp(G, 'visit_occurrence')} v USING (person_id)
        JOIN {rp(G, 'condition_occurrence')} c USING (person_id)
        WHERE v.visit_concept_id = 9201 AND v.visit_start_date > r.idx AND v.visit_start_date <= r.idx + INTERVAL 365 DAY
          AND c.condition_start_date BETWEEN v.visit_start_date AND coalesce(v.visit_end_date, v.visit_start_date)
          AND {code_like("upper(replace(c.condition_source_value, '.', ''))", hosp)}""")
    ref = con.execute(f"""SELECT p.person_source_value patient_key, r.person_id, r.idx index_date,
            (coalesce(d.dd > r.idx AND d.dd <= r.idx + INTERVAL 365 DAY, false)
             OR r.person_id IN (SELECT person_id FROM hospev))::INT outcome,
            coalesce(d.dd > r.idx AND d.dd <= r.idx + INTERVAL 365 DAY, false)::INT death
        FROM ref r JOIN {rp(G, 'person')} p USING (person_id) LEFT JOIN death d USING (person_id)""").df()
    ref["index_date"] = pd.to_datetime(ref.index_date).dt.date
    ref[["patient_key", "person_id", "index_date", "outcome"]].to_parquet(out / "restricted_reference.parquet")
    summary = dict(trial=a.trial, outcome=pg["outcome"], n=int(len(ref)), event_rate=round(float(ref.outcome.mean()), 4),
                   death_rate=round(float(ref.death.mean()), 4), candidates_persons=int(con.execute(
                       "SELECT count(DISTINCT person_id) FROM cand").fetchone()[0]),
                   last_index=a.last_index, seed=a.seed, cohort_persons_excluded=int(con.execute(
                       "SELECT count(*) FROM excl").fetchone()[0]))
    json.dump(summary, open(out / "summary.json", "w"), indent=2)
    write_manifest(out, dict(script_sha256=sha256(Path(__file__)), cohort=a.cohort))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
