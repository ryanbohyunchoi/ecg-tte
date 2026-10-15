"""Verifier check 2 (part c): which product names make up the residual exposure-class drug events (concept names
only, counts suppressed 1-10; no patient-level output)."""
import duckdb

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
P = "/mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv"
con = duckdb.connect()
con.execute("SET threads=32")
con.execute(f"CREATE TABLE coh AS SELECT subject_id, trial FROM read_parquet('{OUT}/meds/restricted_cohort.parquet')")
con.execute("CREATE TABLE cn AS SELECT vocabulary_id || '/' || concept_code AS code, lower(concept_name) AS cname FROM read_csv('" + P +
            "', delim='\\t', quote='', header=true, all_varchar=true) WHERE vocabulary_id IN ('RxNorm', 'RxNorm Extension')")
for k, pat in (("elite2", "(enalapril|valsartan|captopril)"), ("transform_hf", "furosemide")):
    try:
        R = con.execute(f"""SELECT cn.cname, count(*) n FROM read_parquet('{OUT}/meds/data/*.parquet') ev JOIN coh USING (subject_id)
            JOIN cn USING (code) WHERE coh.trial = '{k}' AND ev.source_domain = 'drug' AND regexp_matches(cn.cname, '{pat}')
            GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    except Exception as e:
        print(k, "ERROR", type(e).__name__)
        continue
    for name, n in R:
        print(k, "|", name[:90], "|", "<11" if n < 11 else n)
