"""Verifier: for analysed patients with the lab code before t0, share whose LATEST pre-t0 event of that code belongs to
the index admission (doc section 8: held-out values are 'mostly from the same admission'). Aggregate shares only."""
import duckdb
import pandas as pd

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
R = pd.read_parquet(f"{OUT}/meds/restricted_cohort.parquet")[["subject_id", "trial", "pid", "hadm_id"]]
R = R.merge(pd.read_parquet(f"{OUT}/analysed_pids.parquet"), on=["trial", "pid"])
con = duckdb.connect()
con.execute("SET threads=32")
con.register("r", R)
for name, code in (("creatinine", "LOINC/2160-0"), ("potassium", "LOINC/2823-3"), ("hemoglobin", "LOINC/718-7"),
                   ("NT-proBNP", "LOINC/33762-6"), ("troponin T", "LOINC/6598-7"), ("lactate", "LOINC/32693-4"), ("HbA1c", "LOINC/4548-4"), ("LDL", "LOINC/13457-7")):
    x = con.execute(f"""SELECT avg(CASE WHEN h = r.hadm_id THEN 1.0 ELSE 0.0 END) FROM
        (SELECT subject_id, arg_max(src_hadm_id, "time") h FROM read_parquet('{OUT}/meds/data/*.parquet') WHERE code = '{code}' GROUP BY 1) l
        JOIN r USING (subject_id)""").fetchone()[0]
    print(f"{name}: latest pre-t0 event in the index admission for {100 * x:.1f}% of analysed patients with the code")
