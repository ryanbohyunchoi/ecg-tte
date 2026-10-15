"""Verifier check 2: leakage counts on the MEDS input (aggregate counts only; 1-10 suppressed).
Independent duckdb queries over meds/data, meds/restricted_cohort.parquet, meds_prior and the staged admissions."""
import os
import sys
import duckdb

os.umask(0o077)
OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
STAGE = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-shared/stage"
CONCEPT_CSV = "/mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv"
TMP = f"{OUT}/verify/tmp"
os.makedirs(TMP, exist_ok=True)


def sup(n):
    n = int(n)
    return "<11" if 0 < n < 11 else f"{n:,}"


con = duckdb.connect()
con.execute("SET threads=32")
con.execute("SET memory_limit='200GB'")
con.execute(f"SET temp_directory='{TMP}'")


def q(label, sql):
    try:
        v = con.execute(sql).fetchone()[0]
        print(f"{label}: {sup(v)}", flush=True)
        return v
    except Exception as e:  # never print the message body (may quote a row)
        print(f"{label}: ERROR {type(e).__name__}", flush=True)
        return None


try:
    con.execute(f"CREATE TABLE coh AS SELECT subject_id, mimic_subject_id, hadm_id, CAST(t0 AS TIMESTAMP) t0, trial FROM read_parquet('{OUT}/meds/restricted_cohort.parquet')")
    con.execute(f"CREATE VIEW ev AS SELECT * FROM read_parquet('{OUT}/meds/data/*.parquet')")
    con.execute(f"CREATE TABLE adm AS SELECT CAST(subject_id AS BIGINT) subject_id, CAST(hadm_id AS BIGINT) hadm_id, admittime, dischtime FROM read_parquet('{STAGE}/admissions.parquet')")
    con.execute("CREATE TABLE ix AS SELECT c.*, a.admittime ix_admit, a.dischtime ix_disch FROM coh c JOIN adm a ON a.subject_id = c.mimic_subject_id AND a.hadm_id = c.hadm_id")
except Exception as e:
    print("setup ERROR", type(e).__name__)
    sys.exit(1)

q("MEDS subjects in cohort", "SELECT count(*) FROM coh")
q("cohort subjects with index admission found", "SELECT count(*) FROM ix")
q("MEDS rows (all)", "SELECT count(*) FROM ev")
q("MEDS distinct subjects in shards", "SELECT count(DISTINCT subject_id) FROM ev")
q("events with subject not in cohort", "SELECT count(*) FROM ev LEFT JOIN coh USING (subject_id) WHERE coh.subject_id IS NULL")
q("subjects without exactly one birth", "SELECT count(*) FROM (SELECT subject_id, sum(CASE WHEN code='MEDS_BIRTH' THEN 1 ELSE 0 END) nb FROM ev GROUP BY 1) WHERE nb <> 1")
q("(a) non-birth events with time >= t0", "SELECT count(*) FROM ev JOIN coh USING (subject_id) WHERE ev.code <> 'MEDS_BIRTH' AND ev.\"time\" >= coh.t0")
q("    birth events with time >= t0", "SELECT count(*) FROM ev JOIN coh USING (subject_id) WHERE ev.code = 'MEDS_BIRTH' AND ev.\"time\" >= coh.t0")
q("    events with null time", "SELECT count(*) FROM ev WHERE \"time\" IS NULL")
q("    non-null numeric_value rows (code-only)", "SELECT count(*) FROM ev WHERE numeric_value IS NOT NULL")
q("    events before birth", "SELECT count(*) FROM ev e JOIN (SELECT subject_id, \"time\" bt FROM ev WHERE code='MEDS_BIRTH') b USING (subject_id) WHERE e.\"time\" < b.bt")
q("dx/px events total", "SELECT count(*) FROM ev WHERE source_domain IN ('diagnosis','procedure')")
q("(b) dx/px events with src_hadm_id = index hadm_id", "SELECT count(*) FROM ev JOIN coh USING (subject_id) WHERE ev.source_domain IN ('diagnosis','procedure') AND ev.src_hadm_id = coh.hadm_id")
q("    dx/px events with NULL src_hadm_id", "SELECT count(*) FROM ev WHERE source_domain IN ('diagnosis','procedure') AND src_hadm_id IS NULL")
q("    dx/px events whose src admission not found for that patient", "SELECT count(*) FROM ev JOIN coh USING (subject_id) LEFT JOIN adm a ON a.subject_id = coh.mimic_subject_id AND a.hadm_id = ev.src_hadm_id WHERE ev.source_domain IN ('diagnosis','procedure') AND a.hadm_id IS NULL")
q("(c) dx/px events whose src admittime >= index admittime", "SELECT count(*) FROM ev JOIN ix USING (subject_id) JOIN adm a ON a.subject_id = ix.mimic_subject_id AND a.hadm_id = ev.src_hadm_id WHERE ev.source_domain IN ('diagnosis','procedure') AND a.admittime >= ix.ix_admit")
q("    dx/px events whose time <> src dischtime", "SELECT count(*) FROM ev JOIN coh USING (subject_id) JOIN adm a ON a.subject_id = coh.mimic_subject_id AND a.hadm_id = ev.src_hadm_id WHERE ev.source_domain IN ('diagnosis','procedure') AND ev.\"time\" <> a.dischtime")
q("    dx/px events whose src dischtime > index admittime (overlapping stay)", "SELECT count(*) FROM ev JOIN ix USING (subject_id) JOIN adm a ON a.subject_id = ix.mimic_subject_id AND a.hadm_id = ev.src_hadm_id WHERE ev.source_domain IN ('diagnosis','procedure') AND a.dischtime > ix.ix_admit")
q("    lab/drug events from an admission admitted after the index admission", "SELECT count(*) FROM ev JOIN ix USING (subject_id) JOIN adm a ON a.subject_id = ix.mimic_subject_id AND a.hadm_id = ev.src_hadm_id WHERE ev.source_domain IN ('lab','drug') AND a.admittime > ix.ix_admit")
q("    Visit/IP events with time >= index admittime other than the index admission", "SELECT count(*) FROM ev JOIN ix USING (subject_id) WHERE ev.code = 'Visit/IP' AND ev.\"time\" >= ix.ix_admit AND ev.src_hadm_id <> ix.hadm_id")
q("    rows by domain: lab", "SELECT count(*) FROM ev WHERE source_domain='lab'")
q("    rows by domain: drug", "SELECT count(*) FROM ev WHERE source_domain='drug'")
q("    rows by domain: visit", "SELECT count(*) FROM ev WHERE source_domain='visit'")
q("    lab+drug events from the index admission (pre-t0 stream)", "SELECT count(*) FROM ev JOIN coh USING (subject_id) WHERE ev.source_domain IN ('lab','drug') AND ev.src_hadm_id = coh.hadm_id")

# meds_prior
try:
    con.execute(f"CREATE VIEW evp AS SELECT * FROM read_parquet('{OUT}/meds_prior/data/*.parquet')")
    con.execute(f"CREATE TABLE cohp AS SELECT subject_id FROM read_parquet('{OUT}/meds_prior/restricted_cohort.parquet')")
except Exception as e:
    print("prior setup ERROR", type(e).__name__)
q("meds_prior subjects", "SELECT count(*) FROM cohp")
q("meds_prior rows", "SELECT count(*) FROM evp")
q("(d) meds_prior non-birth events with time >= index admittime", "SELECT count(*) FROM evp JOIN ix USING (subject_id) WHERE evp.code <> 'MEDS_BIRTH' AND evp.\"time\" >= ix.ix_admit")
q("    meds_prior events with src_hadm_id = index hadm_id", "SELECT count(*) FROM evp JOIN ix USING (subject_id) WHERE evp.src_hadm_id = ix.hadm_id")
q("    meds_prior subjects without exactly one birth", "SELECT count(*) FROM (SELECT subject_id, sum(CASE WHEN code='MEDS_BIRTH' THEN 1 ELSE 0 END) nb FROM evp GROUP BY 1) WHERE nb <> 1")
q("    meds_prior cohort subjects absent from shards", "SELECT count(*) FROM cohp LEFT JOIN (SELECT DISTINCT subject_id FROM evp) e USING (subject_id) WHERE e.subject_id IS NULL")

# exposure drug spot check via RxNorm concept names
try:
    con.execute(f"""CREATE TABLE cn AS SELECT vocabulary_id || '/' || concept_code code, lower(concept_name) name, vocabulary_id
        FROM read_csv('{CONCEPT_CSV}', delim='\t', quote='', header=true, all_varchar=true)
        WHERE vocabulary_id IN ('RxNorm', 'RxNorm Extension', 'SNOMED')""")
    q("concept names loaded (RxNorm, RxNorm Ext, SNOMED)", "SELECT count(*) FROM cn")
except Exception as e:
    print("concept load ERROR", type(e).__name__)
q("drug events total", "SELECT count(*) FROM ev WHERE source_domain='drug'")
q("drug events with a named RxNorm/RxNorm Ext code", "SELECT count(*) FROM ev JOIN cn USING (code) WHERE ev.source_domain='drug'")
q("drug events whose code is RxNorm Extension without a name in CONCEPT.csv", "SELECT count(*) FROM ev LEFT JOIN cn USING (code) WHERE ev.source_domain='drug' AND cn.code IS NULL AND ev.code NOT LIKE 'NDC/%'")
DRUGS = {"plato": ["ticagrelor", "clopidogrel"], "aristotle": ["apixaban", "warfarin"], "rocket_af": ["rivaroxaban", "warfarin"],
         "transform_hf": ["torsemide", "furosemide"], "comet": ["metoprolol", "carvedilol"],
         "soap2": ["dopamine", "norepinephrine"], "elite2": ["losartan", "valsartan", "candesartan", "irbesartan", "lisinopril", "enalapril", "captopril", "ramipril"],
         "peptic": ["pantoprazole", "omeprazole", "esomeprazole", "lansoprazole", "famotidine", "ranitidine"]}
for k, ds in DRUGS.items():
    for d in ds:
        q(f"  {k}: drug events with concept name containing '{d}'",
          f"SELECT count(*) FROM ev JOIN coh USING (subject_id) JOIN cn USING (code) WHERE coh.trial = '{k}' AND ev.source_domain='drug' AND cn.name LIKE '%{d}%'")
# cross-check: same ingredients appear for OTHER trials (shows the name lookup works)
for d in ("clopidogrel", "warfarin", "furosemide", "metoprolol", "pantoprazole"):
    q(f"  all trials: drug events with name containing '{d}'", f"SELECT count(*) FROM ev JOIN cn USING (code) WHERE ev.source_domain='drug' AND cn.name LIKE '%{d}%'")
# gate code spot check (SNOMED names)
for k, nm in (("aristotle", "atrial fibrillation"), ("rocket_af", "atrial fibrillation"), ("comet", "heart failure"), ("elite2", "heart failure"),
              ("transform_hf", "heart failure"), ("plato", "myocardial infarction")):
    q(f"  {k}: diagnosis events with SNOMED name containing '{nm}'",
      f"SELECT count(*) FROM ev JOIN coh USING (subject_id) JOIN cn USING (code) WHERE coh.trial = '{k}' AND ev.source_domain='diagnosis' AND cn.name LIKE '%{nm}%'")
for nm in ("atrial fibrillation", "heart failure"):
    q(f"  all trials: diagnosis events with SNOMED name containing '{nm}'", f"SELECT count(*) FROM ev JOIN cn USING (code) WHERE ev.source_domain='diagnosis' AND cn.name LIKE '%{nm}%'")
