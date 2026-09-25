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
    ap.add_argument("--ecg-metadata", default="/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet")
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
    if spec.get("design") == "procedure":
        # Procedure exposure: arm codes are procedure_source_value prefixes (ICD-10-PCS/CPT).
        conds = " UNION ALL ".join(
            f"SELECT {i} arm_idx, person_id, procedure_date d FROM {rp(G, 'procedure_occurrence')} "
            f"WHERE procedure_date IS NOT NULL AND {code_like('upper(procedure_source_value)', codes)}"
            for i, (_, codes) in enumerate(spec["arms"]))
        con.execute(f"CREATE TEMP TABLE armexp AS SELECT DISTINCT * FROM ({conds})")
    elif spec.get("design") == "proc_vs_drug":
        # v1.3: arm 0 = procedure codes (procedure_source_value prefixes), arm 1 = drug keywords
        (_, pcodes), (arm1, kws1) = spec["arms"]
        con.execute(f"""CREATE TEMP TABLE armexp0 AS SELECT DISTINCT 0 arm_idx, person_id, procedure_date d
            FROM {rp(G, 'procedure_occurrence')} WHERE procedure_date IS NOT NULL
              AND {code_like('upper(procedure_source_value)', pcodes)}""")
        con.register("kw_df", pd.DataFrame([(1, arm1, k.lower()) for k in kws1], columns=["arm_idx", "arm", "kw"]))
        create_drug_tokens(con, G, [k.lower() for k in kws1])
        con.execute("""CREATE TEMP TABLE armexp AS SELECT * FROM armexp0 UNION
                       SELECT DISTINCT k.arm_idx, d.person_id, d.d FROM dtok d JOIN kw_df k ON d.tok = k.kw""")
    else:
        rows = [(i, arm, kw.lower()) for i, (arm, kws) in enumerate(spec["arms"]) for kw in kws]
        con.register("kw_df", pd.DataFrame(rows, columns=["arm_idx", "arm", "kw"]))
        create_drug_tokens(con, G, [r[2] for r in rows])
        con.execute("""CREATE TEMP TABLE armexp AS SELECT DISTINCT k.arm_idx, d.person_id, d.d
                       FROM dtok d JOIN kw_df k ON d.tok = k.kw""")
    if spec.get("design") == "switch_seq":
        # v1.1 sequential ("prevalent new-user") switcher design. Candidate records:
        #   arm 0: first-ever arm-0 order with a prior-class order in [index-365, index-1];
        #   arm 1: established arm-1 users: an arm-1 order at index and another in [index-365, index-1],
        #          with no arm-0 order on/before index; at most one candidate date per person-month.
        # Eligibility is applied per record; comparators are then sampled sequentially (see below).
        create_drug_tokens(con, G, spec["prior_class"], table="priortok")
        win = f"BETWEEN DATE '{spec['index_start']}' AND DATE '{spec['index_end']}'"
        con.execute(f"""CREATE TEMP TABLE s1a AS SELECT 0 arm_idx, f.person_id, f.idx FROM
            (SELECT person_id, min(d) idx FROM armexp WHERE arm_idx = 0 GROUP BY 1) f
            WHERE f.idx {win} AND EXISTS (SELECT 1 FROM priortok p WHERE p.person_id = f.person_id
              AND p.d BETWEEN f.idx - INTERVAL 365 DAY AND f.idx - INTERVAL 1 DAY)""")
        con.execute(f"""CREATE TEMP TABLE s1b AS SELECT 1 arm_idx, person_id, idx FROM (
            SELECT c.person_id, c.d idx, row_number() OVER (PARTITION BY c.person_id, date_trunc('month', c.d) ORDER BY c.d) rn
            FROM (SELECT DISTINCT person_id, d FROM armexp WHERE arm_idx = 1) c
            WHERE c.d {win}
              AND EXISTS (SELECT 1 FROM armexp e WHERE e.arm_idx = 1 AND e.person_id = c.person_id
                          AND e.d BETWEEN c.d - INTERVAL 365 DAY AND c.d - INTERVAL 1 DAY)
              AND NOT EXISTS (SELECT 1 FROM armexp e WHERE e.arm_idx = 0 AND e.person_id = c.person_id AND e.d <= c.d))
            WHERE rn = 1""")
        con.execute("CREATE TEMP TABLE s1 AS SELECT * FROM s1a UNION ALL SELECT * FROM s1b")
        con.execute("CREATE TEMP TABLE s2 AS SELECT * FROM s1")
    elif spec.get("design") == "switch":
        # Prevalent new-user ("switcher") design: arm 0 = first-ever order of arm-0 drug with a
        # prior-class order in [index-365, index-1]; arm 1 = established arm-1 users (an arm-1
        # order at index and another in [index-365, index-1]) with no arm-0 order on/before index;
        # one seeded-random qualifying order date per person.
        create_drug_tokens(con, G, spec["prior_class"], table="priortok")
        win = f"BETWEEN DATE '{spec['index_start']}' AND DATE '{spec['index_end']}'"
        con.execute(f"""CREATE TEMP TABLE s1a AS SELECT 0 arm_idx, f.person_id, f.idx FROM
            (SELECT person_id, min(d) idx FROM armexp WHERE arm_idx = 0 GROUP BY 1) f
            WHERE f.idx {win} AND EXISTS (SELECT 1 FROM priortok p WHERE p.person_id = f.person_id
              AND p.d BETWEEN f.idx - INTERVAL 365 DAY AND f.idx - INTERVAL 1 DAY)""")
        con.execute(f"""CREATE TEMP TABLE s1b AS SELECT 1 arm_idx, person_id, idx FROM (
            SELECT c.person_id, c.d idx, row_number() OVER (PARTITION BY c.person_id ORDER BY hash(c.person_id, c.d, 20260924)) rn
            FROM (SELECT DISTINCT person_id, d FROM armexp WHERE arm_idx = 1) c
            WHERE c.d {win}
              AND EXISTS (SELECT 1 FROM armexp e WHERE e.arm_idx = 1 AND e.person_id = c.person_id
                          AND e.d BETWEEN c.d - INTERVAL 365 DAY AND c.d - INTERVAL 1 DAY)
              AND NOT EXISTS (SELECT 1 FROM armexp e WHERE e.arm_idx = 0 AND e.person_id = c.person_id AND e.d <= c.d))
            WHERE rn = 1""")
        con.execute("CREATE TEMP TABLE s1 AS SELECT * FROM s1a UNION ALL SELECT * FROM s1b")
        con.execute("CREATE TEMP TABLE s2 AS SELECT * FROM s1")  # no comparator washout by design
    else:
        con.execute(f"""CREATE TEMP TABLE s1 AS SELECT * FROM
            (SELECT arm_idx, person_id, min(d) idx FROM armexp GROUP BY 1, 2)
            WHERE idx BETWEEN DATE '{spec['index_start']}' AND DATE '{spec['index_end']}'""")
        # v1.3 audit fix: spec['washout_arms'] limits the comparator washout to the listed arms
        # (CABANA: ablation patients may have prior antiarrhythmic use, as in the trial)
        wa = spec.get("washout_arms")
        warm = f"AND c.arm_idx IN ({','.join(map(str, wa))})" if wa else ""
        con.execute(f"""CREATE TEMP TABLE s2 AS SELECT c.* FROM s1 c WHERE NOT (EXISTS (
            SELECT 1 FROM armexp e WHERE e.person_id = c.person_id AND e.arm_idx <> c.arm_idx
              AND e.d BETWEEN c.idx - INTERVAL 365 DAY AND c.idx) {warm})""")
    con.execute(f"""CREATE TEMP TABLE firstvisit AS SELECT person_id, min(visit_start_date) fv
                    FROM {rp(G, 'visit_occurrence')} GROUP BY 1""")
    age = """date_diff('year', p.dob, c.idx)
              - (CASE WHEN strftime(c.idx, '%m%d') < strftime(p.dob, '%m%d') THEN 1 ELSE 0 END)"""
    max_age = f"AND {age} <= {spec['max_age']}" if spec.get("max_age") else ""
    con.execute(f"""CREATE TEMP TABLE s3 AS SELECT c.* FROM s2 c JOIN person p USING (person_id)
        JOIN firstvisit v USING (person_id)
        WHERE p.dob IS NOT NULL AND {age} >= {spec.get('min_age', 18)} {max_age}
          AND v.fv <= c.idx - INTERVAL 365 DAY""")
    # Dedupe: earliest index by default. Switch design: the switcher role (arm 0) wins, because
    # nearly every switcher was earlier an established comparator user (documented limitation:
    # comparators are continuers who did not switch within the data).
    order = "arm_idx, idx" if spec.get("design") == "switch" else "idx, arm_idx"
    if spec.get("design") == "switch_seq":  # records kept; one person per study decided by sequential sampling
        con.execute("CREATE TEMP TABLE s4 AS SELECT arm_idx, person_id, idx FROM s3")
    else:
        con.execute(f"""CREATE TEMP TABLE s4 AS SELECT arm_idx, person_id, idx FROM (
            SELECT *, row_number() OVER (PARTITION BY person_id ORDER BY {order}) rn FROM s3) WHERE rn = 1""")

    # conditions needed for gate/exclusions (on/before index only)
    gate = spec["gate"]
    ex = spec["exclusions"]
    code_gates = {k: v for k, v in gate.items() if k in ("any_before_or_on_index", "window_30d")}
    extra_gate_codes = {p for lst in gate.get("require_all", []) for p in lst} | set(gate.get("first_dx_within", ([], 0))[0])
    prefixes = sorted({p for v in code_gates.values() for p in v} | set(ex.get("ever_codes", [])) | {"I50"} | extra_gate_codes
                      | set(ex.get("ef_unknown_require_codes", []))
                      | {p for _, codes in ex.get("codes_window", []) for p in codes})
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
    con.execute(f"CREATE TEMP TABLE s5 AS SELECT * FROM s4 WHERE (person_id, idx) IN "
                f"(SELECT person_id, idx FROM cond WHERE {' OR '.join(conds)})")

    switch = spec.get("design") in ("switch", "switch_seq")
    stages = [("s1_switchers_and_continuers" if switch else "s1_first_use_in_window", "s1"),
              ("s2_no_washout_switch_design" if switch else "s2_comparator_washout_365", "s2"),
              (f"s3_age{spec.get('min_age', 18)}{'-' + str(spec['max_age']) if spec.get('max_age') else '+'}_prior_activity_365", "s3"),
              ("s4_records_kept_for_sequential_sampling" if spec.get("design") == "switch_seq" else
               "s4_dedupe_switcher_role_first" if switch else "s4_dedupe_earliest_index", "s4"), ("s5_disease_gate", "s5")]
    cur = "s5"
    step = 6

    def apply(name, where_not_exists_sql):
        nonlocal cur, step
        nxt = f"s{step}"
        con.execute(f"CREATE TEMP TABLE {nxt} AS SELECT * FROM {cur} c WHERE NOT ({where_not_exists_sql})")
        stages.append((f"{nxt}_{name}", nxt))
        cur, step = nxt, step + 1

    def latest_measure(cid, days):
        return f"""(SELECT arg_max(m.value_as_number, (m.measurement_date, m.value_as_number)) FROM meas m
                    WHERE m.person_id = c.person_id AND m.cid = {cid}
                      AND m.measurement_date BETWEEN c.idx - INTERVAL {days} DAY AND c.idx - INTERVAL 1 DAY)"""

    # additional required gates (AND): ECG diagnosis text, index PCI
    if gate.get("ecg_text_365d"):
        likes = " OR ".join(f"upper(Diagnosis) LIKE '%{t.upper()}%'" for t in gate["ecg_text_365d"])
        con.execute(f"""CREATE TEMP TABLE ecgtxt AS SELECT DISTINCT {mrn_key('MRN')} k, try_cast(ECGDate AS DATE) d
            FROM read_parquet('{a.ecg_metadata}') WHERE Diagnosis IS NOT NULL AND ({likes})""")
        apply("gate_no_ecg_text_365d", """NOT EXISTS (SELECT 1 FROM ecgtxt e JOIN person p ON e.k = p.k
              WHERE p.person_id = c.person_id AND e.d BETWEEN c.idx - INTERVAL 365 DAY AND c.idx)""")
    if gate.get("pci_30d"):
        from trial_specs import PCI_CODES
        con.execute(f"""CREATE TEMP TABLE pci AS SELECT DISTINCT person_id, procedure_date d FROM {rp(G, 'procedure_occurrence')}
            WHERE person_id IN (SELECT person_id FROM {cur}) AND {code_like('upper(procedure_source_value)', PCI_CODES)}""")
        apply("gate_no_pci_30d", """NOT EXISTS (SELECT 1 FROM pci x WHERE x.person_id = c.person_id
              AND x.d BETWEEN c.idx - INTERVAL 30 DAY AND c.idx)""")

    # v1.3 gates: every listed code group present on/before index; first-ever diagnosis recent
    for j, lst in enumerate(gate.get("require_all", [])):
        apply(f"gate_require_{'_'.join(lst[:3])}", f"""NOT EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id
              AND x.idx = c.idx AND {code_like('x.code', lst)})""")
    if gate.get("first_dx_within"):
        fcodes, fdays = gate["first_dx_within"]
        apply(f"gate_first_{'_'.join(fcodes)}_within_{fdays}d", f"""EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id
              AND x.idx = c.idx AND {code_like('x.code', fcodes)} AND x.d < c.idx - INTERVAL {fdays} DAY)""")

    need_meas = [cid for key, cid in (("egfr_lt", 40764999), ("potassium_gt", 3023103), ("sbp_lt", 4152194)) if key in ex]
    if need_meas:
        con.execute(f"""CREATE TEMP TABLE meas AS SELECT person_id, measurement_concept_id cid, measurement_date,
            value_as_number FROM {rp(G, 'measurement')}
            WHERE measurement_concept_id IN ({','.join(map(str, need_meas))}) AND value_as_number IS NOT NULL
              AND person_id IN (SELECT person_id FROM s5)""")
    if "lvef_gt" in ex or "lvef_lt" in ex or ex.get("hfpef_code_only") or ex.get("ef_unknown_require_codes"):
        con.execute(f"""CREATE TEMP TABLE echo AS SELECT {mrn_key('MRN')} k, try_cast(EchoDate AS DATE) d, EF
            FROM read_parquet('{a.echo_metadata}') WHERE EF BETWEEN 5 AND 90 AND try_cast(EchoDate AS DATE) IS NOT NULL""")
        con.execute(f"""CREATE TEMP TABLE ef AS SELECT c.person_id, c.idx, arg_max(e.EF, (e.d, e.EF)) ef FROM {cur} c
            JOIN person p USING (person_id) JOIN echo e ON e.k = p.k
            WHERE e.d BETWEEN c.idx - INTERVAL 365 DAY AND c.idx - INTERVAL 1 DAY GROUP BY 1, 2""")
    if "lvef_gt" in ex:
        apply(f"latest_lvef_gt_{ex['lvef_gt']}",
              f"EXISTS (SELECT 1 FROM ef WHERE ef.person_id = c.person_id AND ef.idx = c.idx AND ef.ef > {ex['lvef_gt']})")
    if "lvef_lt" in ex:
        apply(f"latest_lvef_lt_{ex['lvef_lt']}",
              f"EXISTS (SELECT 1 FROM ef WHERE ef.person_id = c.person_id AND ef.idx = c.idx AND ef.ef < {ex['lvef_lt']})")
    if ex.get("ef_unknown_require_codes"):
        req = ex["ef_unknown_require_codes"]
        apply("ef_unknown_without_" + "_".join(req),
              f"""NOT EXISTS (SELECT 1 FROM ef WHERE ef.person_id = c.person_id AND ef.idx = c.idx)
                  AND NOT EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id AND x.idx = c.idx AND {code_like('x.code', req)})""")
    if ex.get("hfpef_code_only"):
        apply("hfpef_code_without_hfref_code_ef_unknown",
              f"""NOT EXISTS (SELECT 1 FROM ef WHERE ef.person_id = c.person_id AND ef.idx = c.idx)
                  AND EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id AND x.idx = c.idx AND x.code LIKE 'I503%')
                  AND NOT EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id AND x.idx = c.idx
                                  AND (x.code LIKE 'I502%' OR x.code LIKE 'I504%'))""")
    if "egfr_lt" in ex:
        apply(f"latest_egfr_lt_{ex['egfr_lt']}", f"coalesce({latest_measure(40764999, 90)} < {ex['egfr_lt']}, false)")
    if "potassium_gt" in ex:
        apply(f"latest_potassium_gt_{ex['potassium_gt']}", f"coalesce({latest_measure(3023103, 90)} > {ex['potassium_gt']}, false)")
    if "sbp_lt" in ex:
        apply(f"latest_sbp_lt_{ex['sbp_lt']}", f"coalesce({latest_measure(4152194, 90)} < {ex['sbp_lt']}, false)")
    if ex.get("ever_codes"):
        apply("history_codes_" + "_".join(ex["ever_codes"]),
              f"EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id AND x.idx = c.idx AND x.d < c.idx AND "
              f"{code_like('x.code', ex['ever_codes'])})")
    if ex.get("concomitant_procedure_codes"):
        cc = ex["concomitant_procedure_codes"]
        con.execute(f"""CREATE TEMP TABLE conproc AS SELECT DISTINCT person_id, procedure_date d FROM {rp(G, 'procedure_occurrence')}
            WHERE person_id IN (SELECT person_id FROM {cur}) AND {code_like('upper(procedure_source_value)', cc)}""")
        # v1.1: window [index-1, index] (no post-index information)
        apply("concomitant_procedure_day_before_or_index", """EXISTS (SELECT 1 FROM conproc x WHERE x.person_id = c.person_id
              AND x.d BETWEEN c.idx - INTERVAL 1 DAY AND c.idx)""")
    for days, codes in ex.get("codes_window", []):
        apply(f"codes_{days}d_" + "_".join(codes),
              f"EXISTS (SELECT 1 FROM cond x WHERE x.person_id = c.person_id AND x.idx = c.idx AND x.d >= c.idx - INTERVAL {days} DAY AND "
              f"{code_like('x.code', codes)})")
    for key, days in (("anticoag_30d", 30), ("other_anticoag_365d", 365), ("other_drugs_365d", 365)):
        if key in ex:
            create_drug_tokens(con, G, ex[key], table=f"tok_{key}", person_filter=cur)
            apply(key, f"""EXISTS (SELECT 1 FROM tok_{key} o WHERE o.person_id = c.person_id
                          AND o.d BETWEEN c.idx - INTERVAL {days} DAY AND c.idx)""")

    if spec.get("design") == "switch_seq":
        # Sequential sampling (no future information): switchers in calendar order; for each, up to
        # K comparator records within +/- W days of the switch date, from persons not yet in the study
        # and not the switcher; one record per person (closest date). A person enters once: someone
        # already sampled as a comparator is not re-entered as a later switcher (ITT; later switching
        # ignored). Seeded.
        K, W = spec.get("seq_ratio", 4), spec.get("seq_window_days", 30)
        rec = con.execute(f"SELECT arm_idx, person_id, idx FROM {cur}").df()
        rec["idx"] = pd.to_datetime(rec.idx)
        sw = rec[rec.arm_idx == 0].sort_values(["idx", "person_id"])
        cp = rec[rec.arm_idx == 1].sort_values("idx").reset_index(drop=True)
        cpd = cp.idx.to_numpy()
        rng = __import__("numpy").random.default_rng(20260924)
        used, seq_out = set(), []
        for r in sw.itertuples():
            if r.person_id in used:
                continue
            lo = cpd.searchsorted(r.idx - pd.Timedelta(days=W), "left")
            hi = cpd.searchsorted(r.idx + pd.Timedelta(days=W), "right")
            cand = cp.iloc[lo:hi]
            cand = cand[~cand.person_id.isin(used) & (cand.person_id != r.person_id)]
            if cand.empty:
                continue
            cand = cand.assign(gap=(cand.idx - r.idx).abs()).sort_values(["person_id", "gap"]).drop_duplicates("person_id")
            pick = cand.iloc[rng.permutation(len(cand))[:K]]
            used.add(r.person_id)
            seq_out.append((0, r.person_id, r.idx))
            for q in pick.itertuples():
                used.add(q.person_id)
                seq_out.append((1, q.person_id, q.idx))
        seq = pd.DataFrame(seq_out, columns=["arm_idx", "person_id", "idx"])
        con.register("seq_df", seq)
        nxt = f"s{step}"
        con.execute(f"CREATE TEMP TABLE {nxt} AS SELECT arm_idx, person_id, CAST(idx AS DATE) idx FROM seq_df")
        stages.append((f"{nxt}_sequential_sampling_ratio{K}_window{W}d", nxt))
        cur, step = nxt, step + 1

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
