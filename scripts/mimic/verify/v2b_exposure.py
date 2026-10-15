"""Verifier check 2 (part b): exposure-drug and gate-code spot checks via concept names, and the pre-admission
(index-episode ED) share of the prior-only input. Aggregate counts only; 1-10 suppressed."""
import os
import duckdb

os.umask(0o077)
OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
STAGE = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-shared/stage"
P = "/mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv"
TMP = f"{OUT}/verify/tmp"


def sup(n):
    n = int(n)
    return "<11" if 0 < n < 11 else f"{n:,}"


con = duckdb.connect()
con.execute("SET threads=32")
con.execute(f"SET temp_directory='{TMP}'")


def q(label, sql):
    try:
        v = con.execute(sql).fetchone()[0]
        print(f"{label}: {sup(v) if v is not None else 'NULL'}", flush=True)
        return v
    except Exception as e:
        print(f"{label}: ERROR {type(e).__name__}", flush=True)


con.execute(f"CREATE TABLE coh AS SELECT subject_id, mimic_subject_id, hadm_id, trial FROM read_parquet('{OUT}/meds/restricted_cohort.parquet')")
con.execute(f"CREATE VIEW ev AS SELECT * FROM read_parquet('{OUT}/meds/data/*.parquet')")
sql = ("CREATE TABLE cn AS SELECT vocabulary_id || '/' || concept_code AS code, lower(concept_name) AS cname FROM read_csv('" + P +
       "', delim='\\t', quote='', header=true, all_varchar=true) WHERE vocabulary_id IN ('RxNorm', 'RxNorm Extension', 'SNOMED')")
try:
    con.execute(sql)
except Exception as e:
    print("concept load ERROR", type(e).__name__)
q("concept names loaded", "SELECT count(*) FROM cn")
q("duplicate code strings in concept names", "SELECT count(*) - count(DISTINCT code) FROM cn")
con.execute("CREATE TABLE dv AS SELECT ev.subject_id, ev.code, ev.source_domain, coh.trial, cn.cname FROM ev JOIN coh USING (subject_id) LEFT JOIN cn USING (code) WHERE ev.source_domain IN ('drug', 'diagnosis')")
q("drug events total", "SELECT count(*) FROM dv WHERE source_domain='drug'")
q("drug events with a concept name", "SELECT count(*) FROM dv WHERE source_domain='drug' AND cname IS NOT NULL")
q("drug events coded NDC/ (unmapped)", "SELECT count(*) FROM dv WHERE source_domain='drug' AND code LIKE 'NDC/%'")
q("drug events RxNorm/RxNorm Ext without a name", "SELECT count(*) FROM dv WHERE source_domain='drug' AND cname IS NULL AND code NOT LIKE 'NDC/%'")
DRUGS = {"plato": ["ticagrelor", "clopidogrel"], "aristotle": ["apixaban", "warfarin"], "rocket_af": ["rivaroxaban", "warfarin"],
         "transform_hf": ["torsemide", "furosemide"], "comet": ["metoprolol", "carvedilol"],
         "soap2": ["dopamine", "norepinephrine"],
         "elite2": ["losartan", "valsartan", "candesartan", "irbesartan", "lisinopril", "enalapril", "captopril", "ramipril"],
         "peptic": ["pantoprazole", "omeprazole", "esomeprazole", "lansoprazole", "famotidine", "ranitidine"]}
for k, ds in DRUGS.items():
    for d in ds:
        q(f"  {k}: drug events named '{d}'", f"SELECT count(*) FROM dv WHERE trial='{k}' AND source_domain='drug' AND cname LIKE '%{d}%'")
for d in ("ticagrelor", "clopidogrel", "apixaban", "warfarin", "furosemide", "metoprolol", "carvedilol", "pantoprazole"):
    q(f"  all 8 trials: drug events named '{d}'", f"SELECT count(*) FROM dv WHERE source_domain='drug' AND cname LIKE '%{d}%'")
for k, nm in (("aristotle", "atrial fibrillation"), ("rocket_af", "atrial fibrillation"), ("comet", "heart failure"),
              ("elite2", "heart failure"), ("transform_hf", "heart failure"), ("plato", "myocardial infarction")):
    q(f"  {k}: diagnosis events named '%{nm}%'", f"SELECT count(*) FROM dv WHERE trial='{k}' AND source_domain='diagnosis' AND cname LIKE '%{nm}%'")
for k in ("plato", "soap2", "peptic"):
    for nm in ("atrial fibrillation", "heart failure"):
        q(f"  {k} (non-gate): diagnosis events named '%{nm}%'", f"SELECT count(*) FROM dv WHERE trial='{k}' AND source_domain='diagnosis' AND cname LIKE '%{nm}%'")

# prior-only input: events attached to the index hadm_id but timed before its admittime (index ED episode)
con.execute(f"CREATE VIEW evp AS SELECT * FROM read_parquet('{OUT}/meds_prior/data/*.parquet')")
q("meds_prior non-birth events", "SELECT count(*) FROM evp WHERE code <> 'MEDS_BIRTH'")
q("meds_prior events with src_hadm_id = index hadm_id (pre-admission, index episode)", "SELECT count(*) FROM evp JOIN coh USING (subject_id) WHERE evp.src_hadm_id = coh.hadm_id")
q("  of which labs", "SELECT count(*) FROM evp JOIN coh USING (subject_id) WHERE evp.src_hadm_id = coh.hadm_id AND evp.source_domain='lab'")
q("  of which drugs", "SELECT count(*) FROM evp JOIN coh USING (subject_id) WHERE evp.src_hadm_id = coh.hadm_id AND evp.source_domain='drug'")
q("  of which visits", "SELECT count(*) FROM evp JOIN coh USING (subject_id) WHERE evp.src_hadm_id = coh.hadm_id AND evp.source_domain='visit'")
q("meds_prior subjects with >=1 such event", "SELECT count(DISTINCT evp.subject_id) FROM evp JOIN coh USING (subject_id) WHERE evp.src_hadm_id = coh.hadm_id")
q("meds_prior subjects whose ONLY non-birth events are such events", """SELECT count(*) FROM (SELECT evp.subject_id,
   sum(CASE WHEN evp.src_hadm_id = coh.hadm_id THEN 0 ELSE 1 END) other, count(*) n FROM evp JOIN coh USING (subject_id)
   WHERE evp.code <> 'MEDS_BIRTH' GROUP BY 1) WHERE other = 0""")
q("meds_prior lab events with NULL src_hadm_id (outpatient labs)", "SELECT count(*) FROM evp WHERE source_domain='lab' AND src_hadm_id IS NULL")
# primary input: lab/drug events from an admission admitted after the index admission (timed before t0)
con.execute(f"CREATE TABLE adm AS SELECT CAST(subject_id AS BIGINT) subject_id, CAST(hadm_id AS BIGINT) hadm_id, admittime FROM read_parquet('{STAGE}/admissions.parquet')")
q("primary: subjects with lab/drug events from a later-admitted admission (time < t0)", """SELECT count(DISTINCT ev.subject_id) FROM ev JOIN coh USING (subject_id)
   JOIN adm a ON a.subject_id = coh.mimic_subject_id AND a.hadm_id = ev.src_hadm_id
   JOIN adm ia ON ia.subject_id = coh.mimic_subject_id AND ia.hadm_id = coh.hadm_id
   WHERE ev.source_domain IN ('lab','drug') AND a.admittime > ia.admittime""")
