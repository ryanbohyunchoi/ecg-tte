"""Verifier: share of lab events (and of all events) that come from the index admission before t0, analysed patients
and all MEDS subjects (aggregate shares only). Doc claim (section 9): 86% of events are labs, mostly from the index
admission before t0."""
import duckdb
import pandas as pd

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
R = pd.read_parquet(f"{OUT}/meds/restricted_cohort.parquet")[["subject_id", "trial", "pid", "hadm_id"]]
A = pd.read_parquet(f"{OUT}/analysed_pids.parquet").assign(analysed=1)
R = R.merge(A, on=["trial", "pid"], how="left").fillna({"analysed": 0})
con = duckdb.connect()
con.execute("SET threads=32")
con.register("r", R)
for lab, cond in (("analysed (45,107)", "r.analysed = 1"), ("all MEDS subjects", "TRUE")):
    x = con.execute(f"""SELECT sum(CASE WHEN e.source_domain='lab' THEN 1 ELSE 0 END) labs,
        sum(CASE WHEN e.source_domain='lab' AND e.src_hadm_id = r.hadm_id THEN 1 ELSE 0 END) labs_ix,
        sum(CASE WHEN e.code <> 'MEDS_BIRTH' THEN 1 ELSE 0 END) ev,
        sum(CASE WHEN e.code <> 'MEDS_BIRTH' AND e.src_hadm_id = r.hadm_id THEN 1 ELSE 0 END) ev_ix
        FROM read_parquet('{OUT}/meds/data/*.parquet') e JOIN r USING (subject_id) WHERE {cond}""").fetchone()
    labs, labs_ix, ev, ev_ix = map(float, x)
    print(f"{lab}: labs share of events {labs / ev:.3f}; index-admission share of labs {labs_ix / labs:.3f}; index-admission share of all events {ev_ix / ev:.3f}")
    q = con.execute(f"""SELECT median(s), avg(CASE WHEN s > 0.5 THEN 1.0 ELSE 0.0 END) FROM (SELECT e.subject_id,
        avg(CASE WHEN e.src_hadm_id = r.hadm_id THEN 1.0 ELSE 0.0 END) s FROM read_parquet('{OUT}/meds/data/*.parquet') e JOIN r USING (subject_id)
        WHERE {cond} AND e.source_domain = 'lab' GROUP BY 1)""").fetchone()
    print(f"   per patient (with labs): median index-admission share of lab events {q[0]:.3f}; share of patients with > 50% {q[1]:.3f}")
