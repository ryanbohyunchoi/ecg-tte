#!/usr/bin/env python
"""AoU extraction: BigQuery CDR -> gold-shaped parquet (aou_concepts module docstring = column contract).

stage1   candidates = every person with an exposure to any arm drug (keyword tokens) or arm procedure of any adapted trial
         on or after ICD10_ERA_START. For them, full history of:
           gold/person, gold/condition_occurrence, gold/drug_exposure (normalised-name drug_source_value),
           gold/procedure_occurrence, gold/visit_occurrence (rolled-up visit concept), gold/death, gold/observation_period,
           gold/measurement (MEAS_MAP items only, Yale concept ids, unit-harmonised, PPI excluded),
           survey/ (AoU survey answers for SURVEY_QUESTIONS), meds_gold/drug_exposure (concept-name drug_source_value)
         and the per-person last EHR activity date (restricted_last_ehr.parquet; outcome censoring).
stage2   persons in the built trial cohorts (trials/<n>/cohort/restricted_cohort.parquet): full measurement history with
         original standard concept ids (meds_gold/measurement), the concept table rows used (meds_gold/concept), and hard
         links of gold person / condition / procedure / visit into meds_gold (build_comet_meds.build reads one root; it
         rejects symlinks, not hard links).

Restricted output stays under $AOU_TTE_OUT/extract (umask 077). summary.json holds aggregates only (rounded, 1-20
suppressed). A stage refuses to overwrite a completed stage (delete the directory to rebuild).

Usage: python scripts/aou/aou_extract.py stage1 --ehr-cutoff YYYY-MM-DD
       python scripts/aou/aou_extract.py stage2
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aou_common as AC  # noqa: E402
import aou_concepts as K  # noqa: E402

ROWS_PER_FILE = 5_000_000


def export(client, sql: str, dest: Path, params=None, append: bool = False) -> int:
    """Stream a query result into dest/part-*.parquet (Storage Read API); returns the row count."""
    from google.cloud import bigquery
    from google.cloud import bigquery_storage
    AC.private_dir(dest)
    if not append and any(dest.glob("*.parquet")):
        raise SystemExit(f"{dest} already has parquet files; refusing to overwrite")
    cfg = bigquery.QueryJobConfig(query_parameters=params or [])
    rows = client.query(sql, job_config=cfg).result()
    k0 = len(list(dest.glob("part-*.parquet")))
    n, k, writer, in_file = 0, k0, None, 0
    for batch in rows.to_arrow_iterable(bqstorage_client=bigquery_storage.BigQueryReadClient()):
        if batch.num_rows == 0:
            continue
        tbl = pa.Table.from_batches([batch]) if isinstance(batch, pa.RecordBatch) else batch
        if writer is None or in_file >= ROWS_PER_FILE:
            if writer:
                writer.close()
            writer = pq.ParquetWriter(dest / f"part-{k:04d}.parquet", tbl.schema, compression="zstd")
            k, in_file = k + 1, 0
        writer.write_table(tbl)
        n += tbl.num_rows
        in_file += tbl.num_rows
    if writer:
        writer.close()
    if n == 0 and not append:  # keep the schema readable for DuckDB / pyarrow: write an empty file with the result schema
        empty = client.query(f"SELECT * FROM ({sql}) LIMIT 0", job_config=cfg).result().to_arrow()
        pq.write_table(empty, dest / "part-0000.parquet")
    return n


def candidate_sql(D: str, cutoff: str) -> str:
    import aou_specs as S
    A = S.adapt_all(cutoff)
    drug_kw, proc = set(), set()
    for a in A.values():
        if "spec" not in a:
            continue
        sp = a["spec"]
        p0 = sp.get("design") in ("procedure", "proc_vs_drug") or sp.get("arm0_procedure")
        for i, (_, kws) in enumerate(sp["arms"]):
            if sp.get("design") == "procedure" or (i == 0 and p0):
                proc |= set(kws)
            else:
                drug_kw |= set(kws)
        drug_kw |= set(sp.get("prior_class", []))
    parts = [f"SELECT person_id FROM ({K.drug_rows_sql(D, sorted(drug_kw))}) WHERE d BETWEEN DATE '{AC.ICD10_ERA_START}' AND DATE '{cutoff}'"]
    if proc:
        parts.append(f"SELECT person_id FROM ({K.procedure_rows_sql(D, sorted(proc))}) "
                     f"WHERE d BETWEEN DATE '{AC.ICD10_ERA_START}' AND DATE '{cutoff}'")
    return "SELECT DISTINCT person_id FROM (" + " UNION ALL ".join(parts) + ")"


def stage1_queries(D: str, cand: str) -> dict:
    m, f = K.SEX_AT_BIRTH["male"], K.SEX_AT_BIRTH["female"]
    return {
        "gold/person": f"""SELECT p.person_id, CAST(p.person_id AS STRING) person_source_value,
                CAST(p.birth_datetime AS DATETIME) birth_datetime, p.year_of_birth,
                CASE p.sex_at_birth_concept_id WHEN {m} THEN 8507 WHEN {f} THEN 8532 END gender_concept_id,
                p.race_concept_id, p.ethnicity_concept_id
            FROM `{D}.person` p WHERE p.person_id IN (SELECT person_id FROM cand)""",
        "gold/condition_occurrence": f"""SELECT co.person_id, co.condition_start_date, CAST(co.condition_start_datetime AS DATETIME)
                condition_start_datetime, co.condition_end_date, co.condition_concept_id, co.visit_occurrence_id,
                {K.condition_code_sql('sc')} condition_source_value, sc.vocabulary_id condition_source_vocabulary
            FROM `{D}.condition_occurrence` co LEFT JOIN `{D}.concept` sc ON sc.concept_id = co.condition_source_concept_id
            WHERE co.person_id IN (SELECT person_id FROM cand) AND co.condition_start_date IS NOT NULL""",
        "gold/drug_exposure": f"""SELECT de.person_id, de.drug_exposure_start_date, CAST(de.drug_exposure_start_datetime AS DATETIME)
                drug_exposure_start_datetime, de.drug_concept_id, de.drug_type_concept_id,
                IF(COALESCE(de.drug_concept_id, 0) > 0, {K.norm_sql('c.concept_name')}, {K.norm_sql('de.drug_source_value')}) drug_source_value
            FROM `{D}.drug_exposure` de LEFT JOIN `{D}.concept` c ON c.concept_id = de.drug_concept_id
            WHERE de.person_id IN (SELECT person_id FROM cand) AND de.drug_exposure_start_date IS NOT NULL""",
        "meds_gold/drug_exposure": f"""SELECT de.person_id, de.drug_exposure_start_date, CAST(de.drug_exposure_start_datetime AS DATETIME)
                drug_exposure_start_datetime, de.drug_concept_id,
                LOWER(IF(COALESCE(de.drug_concept_id, 0) > 0, c.concept_name, de.drug_source_value)) drug_source_value
            FROM `{D}.drug_exposure` de LEFT JOIN `{D}.concept` c ON c.concept_id = de.drug_concept_id
            WHERE de.person_id IN (SELECT person_id FROM cand) AND de.drug_exposure_start_date IS NOT NULL""",
        "gold/procedure_occurrence": f"""SELECT po.person_id, po.procedure_date, CAST(po.procedure_datetime AS DATETIME) procedure_datetime,
                po.procedure_concept_id, {K.procedure_code_sql('sc')} procedure_source_value, sc.vocabulary_id procedure_source_vocabulary
            FROM `{D}.procedure_occurrence` po LEFT JOIN `{D}.concept` sc ON sc.concept_id = po.procedure_source_concept_id
            WHERE po.person_id IN (SELECT person_id FROM cand) AND po.procedure_date IS NOT NULL""",
        "gold/visit_occurrence": f"""SELECT v.person_id, v.visit_occurrence_id, COALESCE(r.rolled, v.visit_concept_id) visit_concept_id,
                v.visit_concept_id visit_concept_id_source, v.visit_start_date, CAST(v.visit_start_datetime AS DATETIME) visit_start_datetime,
                v.visit_end_date
            FROM `{D}.visit_occurrence` v LEFT JOIN ({K.visit_rollup_sql(D)}) r ON r.visit_concept_id = v.visit_concept_id
            WHERE v.person_id IN (SELECT person_id FROM cand) AND v.visit_start_date IS NOT NULL""",
        "gold/observation_period": f"""SELECT person_id, observation_period_start_date, observation_period_end_date
            FROM `{D}.observation_period` WHERE person_id IN (SELECT person_id FROM cand)""",
        "gold/measurement": f"""SELECT me.person_id, l.yale_cid measurement_concept_id, l.item, me.measurement_concept_id aou_concept_id,
                me.measurement_date, CAST(me.measurement_datetime AS DATETIME) measurement_datetime,
                {K.unit_case_sql()} value_as_number, me.unit_concept_id
            FROM `{D}.measurement` me JOIN ({K.loinc_sql(D)}) l ON l.concept_id = me.measurement_concept_id
            LEFT JOIN `{D}.concept` sc ON sc.concept_id = me.measurement_source_concept_id
            WHERE me.person_id IN (SELECT person_id FROM cand) AND me.measurement_date IS NOT NULL
              AND COALESCE(sc.vocabulary_id, '') != 'PPI'""",
        "survey": f"""SELECT o.person_id, s.item, ac.concept_code answer_code, LOWER(ac.concept_name) answer_name, o.observation_date
            FROM `{D}.observation` o JOIN ({K.survey_question_sql(D)}) s ON s.concept_id = o.observation_source_concept_id
            LEFT JOIN `{D}.concept` ac ON ac.concept_id = o.value_source_concept_id
            WHERE o.person_id IN (SELECT person_id FROM cand)""",
        "restricted_last_ehr": f"""SELECT person_id, MAX(d) last_ehr_date FROM (
                SELECT person_id, GREATEST(visit_start_date, COALESCE(visit_end_date, visit_start_date)) d FROM `{D}.visit_occurrence`
                WHERE person_id IN (SELECT person_id FROM cand)
                UNION ALL SELECT person_id, condition_start_date FROM `{D}.condition_occurrence` WHERE person_id IN (SELECT person_id FROM cand)
                UNION ALL SELECT person_id, drug_exposure_start_date FROM `{D}.drug_exposure` WHERE person_id IN (SELECT person_id FROM cand)
                UNION ALL SELECT person_id, measurement_date FROM `{D}.measurement` WHERE person_id IN (SELECT person_id FROM cand))
            WHERE d <= CURRENT_DATE() GROUP BY 1""",
    }


def death_sql(D: str, tables: set) -> str:
    if "aou_death" in tables:
        return f"""SELECT person_id, MIN(death_date) death_date FROM `{D}.aou_death`
                   WHERE primary_death_record AND death_date IS NOT NULL AND person_id IN (SELECT person_id FROM cand) GROUP BY 1"""
    return f"""SELECT person_id, MIN(death_date) death_date FROM `{D}.death`
               WHERE death_date IS NOT NULL AND person_id IN (SELECT person_id FROM cand) GROUP BY 1"""


def stage1(cutoff: str, only=None):
    P = AC.paths()
    X = AC.private_dir(P["extract"])
    st = X / "stage1_summary.json"
    if st.exists() and not only:
        raise SystemExit("stage1 already complete (stage1_summary.json); delete the extract directory to rebuild")
    D = AC.cdr()
    client = AC.bq_client()
    tables = set(AC.bq_df(f"SELECT table_id FROM `{D}.__TABLES__`", client).table_id)
    cand = candidate_sql(D, cutoff)
    Q = stage1_queries(D, "cand")
    Q["gold/death"] = death_sql(D, tables)
    summ = dict(stage="stage1", cdr=D, ehr_cutoff=cutoff, index_floor=AC.ICD10_ERA_START, git_sha=AC.git_sha(),
                death_source="aou_death (primary_death_record)" if "aou_death" in tables else "death", tables={})
    t0 = time.time()
    for name, sql in Q.items():
        if only and name not in only:
            continue
        t1 = time.time()
        n = export(client, f"WITH cand AS ({cand}) {sql}", X / name)
        summ["tables"][name] = dict(rows=AC.round_count(n, 1000), secs=round(time.time() - t1))
        print(name, summ["tables"][name], flush=True)
    n = AC.bq_df(f"SELECT COUNT(*) n FROM ({cand})", client).n[0]
    summ.update(candidate_persons=AC.round_count(n), secs=round(time.time() - t0), when=time.strftime("%Y-%m-%d %H:%M"))
    # empty stubs for the Yale-only metadata arguments (ECG text, echo EF): zero rows, the columns the builders read
    stub = AC.private_dir(X / "stubs")
    pq.write_table(pa.table({"MRN": pa.array([], pa.string()), "Diagnosis": pa.array([], pa.string()),
                             "ECGDate": pa.array([], pa.string())}), stub / "ecg_metadata_empty.parquet")
    pq.write_table(pa.table({"MRN": pa.array([], pa.string()), "EchoDate": pa.array([], pa.string()),
                             "EF": pa.array([], pa.float64())}), stub / "echo_metadata_empty.parquet")
    AC.write_json(X / ("stage1_summary.json" if not only else f"stage1_partial_{int(time.time())}.json"), summ)
    json.dump(dict(ehr_cutoff=cutoff, index_floor=AC.ICD10_ERA_START, cdr=D), open(X / "config.json", "w"), indent=1)


def stage2(chunk: int = 20000):
    P = AC.paths()
    X = P["extract"]
    if not (X / "stage1_summary.json").exists():
        raise SystemExit("stage1 not complete")
    if (X / "stage2_summary.json").exists():
        raise SystemExit("stage2 already complete")
    import pandas as pd
    from google.cloud import bigquery
    pids = set()
    for f in sorted(P["trials"].glob("*/cohort/restricted_cohort.parquet")):
        pids |= set(pd.read_parquet(f, columns=["person_id"]).person_id.astype(int))
    if not pids:
        raise SystemExit("no built cohorts under trials/*/cohort")
    pids = sorted(pids)
    D = AC.cdr()
    client = AC.bq_client()
    MG = AC.private_dir(P["meds_gold"])
    n_meas, t0 = 0, time.time()
    for i in range(0, len(pids), chunk):
        prm = [bigquery.ArrayQueryParameter("pids", "INT64", pids[i:i + chunk])]
        n_meas += export(client, f"""SELECT me.person_id, me.measurement_concept_id, me.measurement_date,
                CAST(me.measurement_datetime AS DATETIME) measurement_datetime, me.value_as_number, me.unit_source_value
            FROM `{D}.measurement` me LEFT JOIN `{D}.concept` sc ON sc.concept_id = me.measurement_source_concept_id
            WHERE me.person_id IN UNNEST(@pids) AND me.measurement_date IS NOT NULL AND COALESCE(sc.vocabulary_id, '') != 'PPI'
              AND COALESCE(me.measurement_concept_id, 0) > 0""", MG / "measurement", prm, append=i > 0)
        print("measurement", i + chunk, "/", len(pids), flush=True)
    # concept rows (concept_id, vocabulary_id, concept_code) for every standard concept the MEDS builder can meet
    used = []
    for t, c in (("condition_occurrence", "condition_concept_id"), ("drug_exposure", "drug_concept_id"),
                 ("procedure_occurrence", "procedure_concept_id"), ("visit_occurrence", "visit_concept_id"),
                 ("measurement", "measurement_concept_id")):
        root = (MG if t in ("measurement", "drug_exposure") else P["gold"]) / t
        import duckdb
        used.append(duckdb.sql(f"SELECT DISTINCT {c} cid FROM read_parquet('{root}/*.parquet') WHERE {c} > 0").df())
    cids = sorted(set(pd.concat(used).cid.astype(int)))
    n_con = 0
    for i in range(0, len(cids), 50000):
        prm = [bigquery.ArrayQueryParameter("c", "INT64", cids[i:i + 50000])]
        n_con += export(client, f"SELECT concept_id, vocabulary_id, concept_code FROM `{D}.concept` WHERE concept_id IN UNNEST(@c)",
                        MG / "concept_parts", prm, append=i > 0)
    import duckdb
    duckdb.sql(f"COPY (SELECT * FROM read_parquet('{MG}/concept_parts/*.parquet')) TO '{MG}/concept.parquet' (FORMAT parquet)")
    # hard links: same files, one root for build_comet_meds / build_preindex_panel
    for t in ("person", "condition_occurrence", "procedure_occurrence", "visit_occurrence"):
        d = AC.private_dir(MG / t)
        for f in sorted((P["gold"] / t).glob("*.parquet")):
            if not (d / f.name).exists():
                os.link(f, d / f.name)
    AC.write_json(X / "stage2_summary.json", dict(stage="stage2", cohort_persons=AC.round_count(len(pids)),
                                                  measurement_rows=AC.round_count(n_meas, 1000), concepts=AC.round_count(n_con),
                                                  secs=round(time.time() - t0), when=time.strftime("%Y-%m-%d %H:%M")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["stage1", "stage2"])
    ap.add_argument("--ehr-cutoff", default=os.environ.get("AOU_EHR_CUTOFF"))
    ap.add_argument("--only", default="", help="stage1: comma-separated table names to (re)export into empty directories")
    a = ap.parse_args()
    if a.stage == "stage1":
        if not a.ehr_cutoff:
            raise SystemExit("--ehr-cutoff is required (from probe.json 'dates')")
        stage1(a.ehr_cutoff, [x for x in a.only.split(",") if x] or None)
    else:
        stage2()


if __name__ == "__main__":
    main()
