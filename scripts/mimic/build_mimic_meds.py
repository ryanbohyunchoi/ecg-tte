#!/usr/bin/env python
"""Step 1: MIMIC-IV -> MEDS for CLMBR-T, matching the Yale input (scripts/build_comet_meds.py, code-only inference).

One MEDS subject per trial-patient-index (`subject_id` = row number over (trial, pid); the same MIMIC patient in two
trials is two subjects with two time zeros). Events (all strictly before time zero t0 = index_datetime):

  diagnoses   diagnoses_icd of EARLIER admissions only (admittime < index admittime, hadm_id <> index, dischtime < t0),
              timed at that admission's dischtime (MIMIC codes carry no timestamp); ICD9CM / ICD10CM (dotted) mapped to
              standard concepts through CONCEPT_RELATIONSHIP 'Maps to' (one event per target, as an OMOP condition
              table); unmapped codes keep the source string (out of the CLMBR-T vocabulary). The trial's gate-condition
              ICD prefixes (v15_mimic_common GATE / CONCEPTS; ELITE II heart failure) are excluded.
  procedures  procedures_icd of earlier admissions only, timed at dischtime; ICD9Proc (dotted) / ICD10PCS strings
              (standard OMOP vocabularies, used directly as at Yale's procedure_occurrence).
  drugs       raw prescriptions (the staged copy has no ndc), any admission, starttime < t0; NDC -> RxNorm / RxNorm
              Extension through 'Maps to' (OHDSI vocabulary with NDC, read in place); the trial's exposure drugs
              (the cohort builders' drug-string tokens) are excluded. emar carries no drug code (its rows repeat the
              prescriptions order through pharmacy_id) and is not used.
  labs        labevents (any admission or outpatient), charttime < t0; LOINC from lab_loinc_map.LAB_LOINC, otherwise
              MIMIC_LAB/<itemid> (MIMIC-IV 3.1 d_labitems has no LOINC).
  visits      Visit/IP at each admission's admittime < t0; Visit/ER at each ED transfer intime < t0.
  birth       MEDS_BIRTH at 1 July of (anchor_year - anchor_age), the de-identified, year-only birth (no exact birth
              date exists in MIMIC); sex is not a token, as at Yale (build_comet_meds v1: no static sex/race tokens).

Code-only mode: no numeric values are written. Coverage gate statistics (aggregate) are written to
OUT/meds/summary.json and OUT/coverage/. Restricted outputs stay under OUT (umask 077); nothing patient-level is printed.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from mimic_common import MEDS, OUT, STAGE, clmbr_codes, status, sup
from lab_loinc_map import LAB_LOINC
import mimic_replication as M  # noqa: E402
import mimic_build_new as B  # noqa: E402
from v15_mimic_common import CONCEPTS, GATE, TS  # noqa: E402

RAW = Path("/mnt/raid0/bb2238/physionet/physionet.org/files/mimiciv/3.1/hosp")
NDC_MAP = OUT / "vocab" / "ndc_maps_to.parquet"
CONCEPT = OUT / "vocab" / "concept.parquet"
MAPS = OUT / "vocab" / "maps_to.parquet"
TRIALS = M.BUILT + M.NEW
VERSION = "mimic_meds_v1"
BIRTH = "MEDS_BIRTH"
SHARDS = 32
SCHEMA = pa.schema([("subject_id", pa.int64()), ("time", pa.timestamp("us")), ("code", pa.string()),
                    ("numeric_value", pa.float32()), ("unit", pa.string()), ("source_domain", pa.string()),
                    ("source_concept_id", pa.int64()), ("src_hadm_id", pa.int64())])


def expo_tokens(k):
    if k in TS.TRIALS:
        return sorted({t.lower() for _, toks in TS.TRIALS[k]["arms"] for t in toks})
    return sorted({t.lower() for t in B.SPECS[k]["expo"]})


def gate_prefixes(k):
    g = {"elite2": "heart_failure"}.get(k) or (GATE[k][0] if k in GATE else None)
    return ([], []) if g is None else CONCEPTS[g]


def digest(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def roster():
    rows = []
    for k in TRIALS:
        it = pd.read_parquet(M.tdir(k) / "index_time.parquet")[["pid", "subject_id", "hadm_id", "index_datetime"]]
        co = pd.read_parquet(M.tdir(k) / "cohort.parquet")[["pid", "treated"]].drop_duplicates("pid")
        it = it.assign(pid=it.pid.astype(str)).drop_duplicates("pid").merge(co.assign(pid=co.pid.astype(str)), on="pid", how="left")
        it["trial"] = k
        rows.append(it)
    R = pd.concat(rows, ignore_index=True).sort_values(["trial", "pid"]).reset_index(drop=True)
    R["mid"] = np.arange(1, len(R) + 1, dtype=np.int64)
    R["subject_id"] = R.subject_id.astype(np.int64)
    R["hadm_id"] = R.hadm_id.astype(np.int64)
    R["t0"] = pd.to_datetime(R.index_datetime)
    assert R.treated.notna().all()
    return R[["mid", "trial", "pid", "subject_id", "hadm_id", "t0", "treated"]]


def build(con, R):
    con.register("r0", R)
    con.execute("CREATE TEMP TABLE r AS SELECT r0.*, a.admittime ix_admit FROM r0 JOIN read_parquet('%s/admissions.parquet') a "
                "ON a.subject_id = r0.subject_id AND a.hadm_id = r0.hadm_id" % STAGE)
    assert con.execute("SELECT count(*) FROM r").fetchone()[0] == len(R), "index admission not found"
    ex = pd.DataFrame([(k, t) for k in TRIALS for t in expo_tokens(k)], columns=["trial", "tok"])
    gt = pd.DataFrame([(k, v, p) for k in TRIALS for v, ps in zip((10, 9), gate_prefixes(k)) for p in ps],
                      columns=["trial", "v", "prefix"])
    lm = pd.DataFrame([(i, "LOINC/" + c) for i, c in LAB_LOINC.items()], columns=["itemid", "code"])
    for n, d in (("expo", ex), ("gate", gt), ("labmap", lm)):
        con.register(n, d)
    # ---- diagnoses (earlier admissions; timed at discharge; gate prefixes excluded)
    con.execute(f"""CREATE TEMP TABLE prior_adm AS SELECT r.mid, r.trial, a.hadm_id, a.dischtime FROM r
        JOIN read_parquet('{STAGE}/admissions.parquet') a ON a.subject_id = r.subject_id
        WHERE a.admittime < r.ix_admit AND a.hadm_id <> r.hadm_id AND a.dischtime < r.t0""")
    con.execute(f"""CREATE TEMP TABLE dx AS SELECT p.mid, p.trial, p.hadm_id, p.dischtime t, CAST(d.icd_version AS INT) v,
        d.icd_code c FROM prior_adm p JOIN r USING (mid, trial)
        JOIN read_parquet('{STAGE}/diagnoses_icd.parquet') d
        ON CAST(d.subject_id AS BIGINT) = r.subject_id AND CAST(d.hadm_id AS BIGINT) = p.hadm_id""")
    n_dx_all = con.execute("SELECT count(*) FROM dx").fetchone()[0]
    con.execute("""DELETE FROM dx WHERE EXISTS (SELECT 1 FROM gate g WHERE g.trial = dx.trial AND g.v = dx.v
                   AND starts_with(dx.c, g.prefix))""")
    n_dx_gate = n_dx_all - con.execute("SELECT count(*) FROM dx").fetchone()[0]
    # dotted source codes -> 'Maps to' standard targets
    con.execute("""CREATE TEMP TABLE dxs AS SELECT *, CASE WHEN v = 10 THEN (CASE WHEN length(c) > 3 THEN substr(c, 1, 3) || '.' || substr(c, 4) ELSE c END)
        WHEN starts_with(c, 'E') THEN (CASE WHEN length(c) > 4 THEN substr(c, 1, 4) || '.' || substr(c, 5) ELSE c END)
        ELSE (CASE WHEN length(c) > 3 THEN substr(c, 1, 3) || '.' || substr(c, 4) ELSE c END) END dotted,
        CASE WHEN v = 10 THEN 'ICD10CM' ELSE 'ICD9CM' END vocab FROM dx""")
    con.execute(f"""CREATE TEMP TABLE dxmap AS SELECT DISTINCT s.vocabulary_id vocab, s.concept_code dotted,
        t.vocabulary_id || '/' || t.concept_code code, CAST(t.concept_id AS BIGINT) cid
        FROM read_parquet('{CONCEPT}') s JOIN read_parquet('{MAPS}') m ON m.concept_id_1 = s.concept_id
        JOIN read_parquet('{CONCEPT}') t ON t.concept_id = m.concept_id_2
        WHERE s.vocabulary_id IN ('ICD9CM', 'ICD10CM')""")
    con.execute("""CREATE TEMP TABLE ev_dx AS SELECT d.mid, d.t, coalesce(m.code, d.vocab || '/' || d.dotted) code, 'diagnosis' dom,
        m.cid, d.hadm_id src FROM dxs d LEFT JOIN dxmap m USING (vocab, dotted)""")
    dx_unmapped = con.execute("SELECT count(*) FROM dxs d WHERE NOT EXISTS (SELECT 1 FROM dxmap m WHERE m.vocab = d.vocab AND m.dotted = d.dotted)").fetchone()[0]
    # ---- procedures (earlier admissions; timed at discharge)
    con.execute(f"""CREATE TEMP TABLE ev_px AS SELECT p.mid, p.dischtime t,
        CASE WHEN x.icd_version = 10 THEN 'ICD10PCS/' || x.icd_code
             ELSE 'ICD9Proc/' || CASE WHEN length(x.icd_code) > 2 THEN substr(x.icd_code, 1, 2) || '.' || substr(x.icd_code, 3) ELSE x.icd_code END END code,
        'procedure' dom, CAST(NULL AS BIGINT) cid, p.hadm_id src
        FROM prior_adm p JOIN r USING (mid, trial) JOIN read_parquet('{STAGE}/procedures_icd.parquet') x
        ON x.subject_id = r.subject_id AND x.hadm_id = p.hadm_id""")
    # ---- drugs (raw prescriptions; starttime < t0; exposure drugs excluded; NDC -> RxNorm)
    con.execute(f"""CREATE TEMP TABLE rx AS SELECT r.mid, r.trial, p.hadm_id src, p.starttime t, p.ndc,
        regexp_split_to_array(lower(coalesce(p.drug, '')), '[^a-z0-9]+') toks
        FROM read_csv('{RAW}/prescriptions.csv.gz', header = true, delim = ',', quote = '"', escape = '"',
                      columns = {{'subject_id': 'BIGINT', 'hadm_id': 'BIGINT', 'pharmacy_id': 'BIGINT', 'poe_id': 'VARCHAR',
                                 'poe_seq': 'VARCHAR', 'order_provider_id': 'VARCHAR', 'starttime': 'TIMESTAMP',
                                 'stoptime': 'TIMESTAMP', 'drug_type': 'VARCHAR', 'drug': 'VARCHAR',
                                 'formulary_drug_cd': 'VARCHAR', 'gsn': 'VARCHAR', 'ndc': 'VARCHAR', 'prod_strength': 'VARCHAR',
                                 'form_rx': 'VARCHAR', 'dose_val_rx': 'VARCHAR', 'dose_unit_rx': 'VARCHAR',
                                 'form_val_disp': 'VARCHAR', 'form_unit_disp': 'VARCHAR', 'doses_per_24_hrs': 'VARCHAR',
                                 'route': 'VARCHAR'}}) p
        JOIN r ON r.subject_id = p.subject_id WHERE p.starttime < r.t0""")
    n_rx_all = con.execute("SELECT count(*) FROM rx").fetchone()[0]
    con.execute("""CREATE TEMP TABLE ex_list AS SELECT trial, list(tok) etoks FROM expo GROUP BY 1""")
    con.execute("""CREATE TEMP TABLE rx2 AS SELECT rx.* FROM rx JOIN ex_list e USING (trial) WHERE NOT list_has_any(rx.toks, e.etoks)""")
    con.execute("DROP TABLE rx")
    con.execute("ALTER TABLE rx2 RENAME TO rx")
    n_rx_expo = n_rx_all - con.execute("SELECT count(*) FROM rx").fetchone()[0]
    n_rx_nondc = con.execute("SELECT count(*) FROM rx WHERE ndc IS NULL OR trim(ndc) IN ('', '0')").fetchone()[0]
    con.execute("DELETE FROM rx WHERE ndc IS NULL OR trim(ndc) IN ('', '0')")
    con.execute(f"""CREATE TEMP TABLE ndcmap AS SELECT DISTINCT ndc, tv || '/' || tc code FROM read_parquet('{NDC_MAP}')
                    WHERE tv IN ('RxNorm', 'RxNorm Extension')""")
    con.execute("""CREATE TEMP TABLE ev_rx AS SELECT x.mid, x.t, coalesce(m.code, 'NDC/' || x.ndc) code, 'drug' dom,
        CAST(NULL AS BIGINT) cid, x.src FROM rx x LEFT JOIN ndcmap m ON m.ndc = lpad(trim(x.ndc), 11, '0')""")
    rx_unmapped = con.execute("SELECT count(*) FROM rx x WHERE NOT EXISTS (SELECT 1 FROM ndcmap m WHERE m.ndc = lpad(trim(x.ndc), 11, '0'))").fetchone()[0]
    # ---- labs (charttime < t0)
    con.execute(f"""CREATE TEMP TABLE ev_lab AS SELECT r.mid, l.charttime t, coalesce(m.code, 'MIMIC_LAB/' || CAST(l.itemid AS VARCHAR)) code,
        'lab' dom, CAST(NULL AS BIGINT) cid, l.hadm_id src FROM read_parquet('{STAGE}/labevents.parquet') l
        JOIN r ON r.subject_id = l.subject_id LEFT JOIN labmap m ON m.itemid = l.itemid WHERE l.charttime < r.t0""")
    # ---- visits
    con.execute(f"""CREATE TEMP TABLE ev_visit AS
        SELECT r.mid, a.admittime t, 'Visit/IP' code, 'visit' dom, CAST(9201 AS BIGINT) cid, a.hadm_id src
          FROM r JOIN read_parquet('{STAGE}/admissions.parquet') a ON a.subject_id = r.subject_id WHERE a.admittime < r.t0
        UNION ALL
        SELECT DISTINCT r.mid, x.intime t, 'Visit/ER' code, 'visit' dom, CAST(9203 AS BIGINT) cid, x.hadm_id src
          FROM r JOIN read_parquet('{STAGE}/transfers.parquet') x ON x.subject_id = r.subject_id
          WHERE x.eventtype = 'ED' AND x.intime < r.t0""")
    # ---- birth (year-only; 1 July)
    con.execute(f"""CREATE TEMP TABLE birth AS SELECT r.mid, make_timestamp(p.anchor_year - p.anchor_age, 7, 1, 0, 0, 0) t,
        p.anchor_age + (year(r.t0) - p.anchor_year) age_v15 FROM r JOIN read_parquet('{STAGE}/patients.parquet') p USING (subject_id)""")
    con.execute(f"""CREATE TEMP TABLE ev AS
        SELECT mid, t, code, dom, cid, src FROM ev_dx UNION ALL SELECT * FROM ev_px UNION ALL SELECT * FROM ev_rx
        UNION ALL SELECT * FROM ev_lab UNION ALL SELECT * FROM ev_visit""")
    con.execute("DELETE FROM ev WHERE t IS NULL")
    qc = dict(dx_rows_prior_admissions=n_dx_all, dx_rows_gate_excluded=n_dx_gate, dx_rows_unmapped=dx_unmapped,
              rx_rows_before_t0=n_rx_all, rx_rows_exposure_excluded=n_rx_expo, rx_rows_without_ndc=n_rx_nondc,
              rx_rows_ndc_unmapped=rx_unmapped)
    return qc


def write(con, R, qc, out):
    vocab = clmbr_codes()
    out.mkdir(parents=True, exist_ok=False)
    (out / "data").mkdir()
    (out / "metadata").mkdir()
    # leakage checks (aggregate): no event at/after t0; no dx/px from the index admission; no exposure drug; birth < t0
    chk = con.execute("""SELECT
        (SELECT count(*) FROM ev JOIN r USING (mid) WHERE ev.t >= r.t0) at_or_after_t0,
        (SELECT count(*) FROM ev JOIN r USING (mid) WHERE ev.dom IN ('diagnosis', 'procedure') AND ev.src = r.hadm_id) dxpx_index_adm,
        (SELECT count(*) FROM birth JOIN r USING (mid) WHERE birth.t >= r.t0) birth_after_t0,
        (SELECT count(*) FROM ev JOIN birth b USING (mid) WHERE ev.t < b.t) before_birth,
        (SELECT max(abs(year(r.t0) - year(b.t) - b.age_v15)) FROM birth b JOIN r USING (mid)) max_age_gap_vs_v15""").df().iloc[0].to_dict()
    qc["leakage_checks"] = {k: int(v) for k, v in chk.items()}
    assert chk["at_or_after_t0"] == 0 and chk["dxpx_index_adm"] == 0 and chk["birth_after_t0"] == 0
    con.execute("DELETE FROM ev USING birth b WHERE ev.mid = b.mid AND ev.t < b.t")
    con.execute(f"""CREATE TEMP TABLE allev AS SELECT mid, t, code, dom, cid, src FROM ev
        UNION ALL SELECT mid, t, '{BIRTH}' code, 'birth' dom, CAST(NULL AS BIGINT) cid, CAST(NULL AS BIGINT) src FROM birth""")
    outputs, rows = {}, 0
    for b in range(SHARDS):
        T = con.execute(f"""SELECT mid AS subject_id, t AS "time", code, CAST(NULL AS FLOAT) numeric_value, CAST(NULL AS VARCHAR) unit,
            dom source_domain, cid source_concept_id, src src_hadm_id FROM allev WHERE mid % {SHARDS} = {b}
            ORDER BY mid, t, code, dom""").fetch_arrow_table()
        if T.num_rows:
            p = out / "data" / f"part-{b:03d}.parquet"
            pq.write_table(T.cast(SCHEMA), p, compression="zstd")
            outputs[str(p.relative_to(out))] = digest(p)
            rows += T.num_rows
    # roster (restricted) and per-patient counts
    # n_history = events outside the index admission (earlier admissions, outpatient labs, ED visits without admission)
    pc = con.execute("""SELECT ev.mid, count(*) n_events, count(DISTINCT ev.code) n_codes,
        sum(CASE WHEN ev.dom IN ('diagnosis', 'procedure') OR ev.src IS NULL OR ev.src <> r.hadm_id THEN 1 ELSE 0 END) n_history
        FROM ev JOIN r USING (mid) GROUP BY 1""").df()
    E = con.execute("SELECT mid, code, dom FROM ev").df()
    E["in_vocab"] = E.code.isin(vocab)
    iv = E[E.in_vocab].groupby("mid").size()
    ro = R.merge(con.execute("SELECT mid, t birth_datetime FROM birth").df(), on="mid", how="left").merge(pc, on="mid", how="left")
    ro[["n_events", "n_codes", "n_history"]] = ro[["n_events", "n_codes", "n_history"]].fillna(0).astype(int)
    ro["n_in_vocab"] = ro.mid.map(iv).fillna(0).astype(int)
    ro = ro.rename(columns={"mid": "subject_id", "subject_id": "mimic_subject_id"})
    ro["patient_key"] = ro.trial + "|" + ro.pid
    ro["treatment_arm"] = np.where(ro.treated == 1, "treated", "comparator")
    ro["clinical_meds_rows"] = ro.n_events
    ro.to_parquet(out / "restricted_cohort.parquet", index=False)
    outputs["restricted_cohort.parquet"] = digest(out / "restricted_cohort.parquet")
    dom = E.groupby("dom").in_vocab.agg(["size", "mean"]).rename(columns={"size": "events", "mean": "share_in_vocab"})
    json.dump(dict(version=VERSION, birth_code=BIRTH, subject="trial-patient-index", sharding=f"subject_id modulo {SHARDS}"),
              open(out / "metadata" / "dataset.json", "w"))
    outputs["metadata/dataset.json"] = digest(out / "metadata" / "dataset.json")
    json.dump(dict(version=VERSION, outputs=outputs), open(out / "manifest.json", "w"), indent=1)
    s = dict(version=VERSION, status="complete_cohort_meds", counts_valid=True, rows=rows, subjects=len(ro), trials=TRIALS,
             timing="strictly before time zero (index_datetime); dx/px from earlier admissions only, timed at discharge",
             numeric_policy="code-only: no numeric values written", qc=qc,
             domain_coverage={d: dict(events=int(r.events), share_in_vocab=round(float(r.share_in_vocab), 4)) for d, r in dom.iterrows()},
             share_events_in_vocab=round(float(E.in_vocab.mean()), 4))
    json.dump(s, open(out / "summary.json", "w"), indent=1, default=int)
    return s, ro


def main():
    import duckdb
    t = time.time()
    R = roster()
    con = duckdb.connect()
    con.execute("SET threads=48")
    con.execute("SET memory_limit='300GB'")
    (OUT / "tmp").mkdir(exist_ok=True)
    con.execute(f"SET temp_directory='{OUT}/tmp'")
    try:
        qc = build(con, R)
        s, ro = write(con, R, qc, MEDS)
    except Exception as e:  # database errors can quote a raw source row: report the type only
        status(f"step 1 MEDS build failed: {type(e).__name__}")
        # first line only (CSV errors put the raw row on a later line)
        print("FAILED:", type(e).__name__, str(e).split("\n")[0][:300], file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in s.items() if k != "trials"}, indent=1, default=int))
    status(f"step 1 MEDS built: {s['subjects']} trial-patient-index subjects, {s['rows']} rows; share of events in the "
           f"CLMBR-T dictionary {s['share_events_in_vocab']:.3f}; leakage checks {qc['leakage_checks']} ({time.time() - t:.0f} s)")


if __name__ == "__main__":
    sys.exit(main())
