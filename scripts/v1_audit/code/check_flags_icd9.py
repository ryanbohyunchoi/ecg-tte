#!/usr/bin/env python
"""v1 audit: does the PS-Flags dx query (scripts/v21/ps_flags.py) mix ICD-9 history into 'ICD-10 3-char' flags?
Aggregates only. For a trial roster: share of pre-index condition rows by source-code shape (letter-first vs digit-first)
and by period (before / after 2015-10-01), and the share of letter-first rows before 2015-10-01 whose 3-char prefix is an
ICD-9 V/E code that collides with an ICD-10 3-char code. Prints proportions only."""
import sys, glob
import duckdb, pandas as pd
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts")
from v13_common import A, EXTRA, PRIMARY
n = sys.argv[1] if len(sys.argv) > 1 else "aristotle"
cdir = {**PRIMARY, **EXTRA}[n][1]
ro = pd.read_parquet(A / cdir / "restricted_cohort.parquet", columns=["patient_key", "person_id", "index_date"]).drop_duplicates("patient_key")
g = glob.glob("/mnt/raid0/rbc58/omop/gold/condition_occurrence/**/*.parquet", recursive=True)
con = duckdb.connect(); con.execute("SET threads=8")
con.register("coh_df", ro)
con.execute("CREATE TABLE pmap AS SELECT patient_key, CAST(index_date AS DATE) idx, CAST(person_id AS BIGINT) person_id FROM coh_df")
q = f"""SELECT m.patient_key, t.condition_start_date d, upper(replace(condition_source_value,'.','')) c,
        condition_source_concept_id sc
        FROM read_parquet({g}, hive_partitioning=true) t JOIN pmap m USING (person_id)
        WHERE t.condition_start_date < m.idx"""
con.execute(f"CREATE TABLE x AS {q}")
r = con.execute("""SELECT (d < DATE '2015-10-01') early,
       CASE WHEN regexp_matches(c, '^[A-Z][0-9][0-9A-Z]') THEN 'letter3' WHEN regexp_matches(c, '^[0-9]') THEN 'digit' ELSE 'other' END shape,
       count(*) n FROM x GROUP BY 1,2 ORDER BY 1,2""").df()
r["share_within_period"] = r.n / r.groupby("early").n.transform("sum")
print(n, "pre-index condition rows by period x code shape (shares only):")
print(r[["early", "shape", "share_within_period"]].round(4).to_string(index=False))
# ICD-9 V/E-like prefixes (V01-V91, E80-E99) among letter-first rows, by period
v = con.execute("""SELECT (d < DATE '2015-10-01') early, substr(c,1,1) l, count(*) n FROM x
    WHERE regexp_matches(c, '^(V[0-9][0-9]|E[89][0-9])') GROUP BY 1,2""").df()
tot = con.execute("SELECT (d < DATE '2015-10-01') early, count(*) n FROM x WHERE regexp_matches(c, '^[A-Z][0-9][0-9A-Z]') GROUP BY 1").df().set_index("early").n
v["share_of_letter3_rows_in_period"] = v.apply(lambda r_: r_.n / tot[r_.early], axis=1)
print("V../E8x-E9x prefixes (ICD-9 V/E codes collide with ICD-10 V00-V99 / E80-E99):")
print(v[["early", "l", "share_of_letter3_rows_in_period"]].round(4).to_string(index=False))
# patients: share with ANY pre-index history before 2015-10-01, and share of those whose pre-2015 history has no letter3 code
p = con.execute("""SELECT count(DISTINCT patient_key) FILTER (WHERE d < DATE '2015-10-01') e,
                          count(DISTINCT patient_key) FILTER (WHERE d < DATE '2015-10-01' AND regexp_matches(c, '^[0-9]')) e_digit,
                          (SELECT count(*) FROM pmap) N FROM x""").fetchone()
print(f"share of roster with pre-2015-10 dx history: {p[0]/p[2]:.3f}; with digit-first (ICD-9 numeric) codes then: {p[1]/p[2]:.3f}")
# index-date distribution
idx = pd.to_datetime(ro.index_date)
print(f"share of roster with index before 2016-01-01: {(idx < '2016-01-01').mean():.3f}")
