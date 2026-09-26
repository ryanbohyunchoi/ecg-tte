#!/usr/bin/env python
"""v1.5 MIMIC-IV staging: convert the needed MIMIC-IV 3.1 csv.gz tables to parquet (restricted).

Output: /mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-shared/stage/*.parquet (private, umask 077).
No outputs are printed except row counts.
"""
import os
import sys
import time

import duckdb

os.umask(0o077)
M = "/mnt/raid0/bb2238/physionet/physionet.org/files/mimiciv/3.1"
ECG = "/mnt/raid0/bb2238/physionet/physionet.org/files/mimic-iv-ecg/1.0/record_list.csv"
OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-shared/stage"
os.makedirs(OUT, exist_ok=True)
os.chmod(os.path.dirname(OUT), 0o700)
os.chmod(OUT, 0o700)
con = duckdb.connect()
con.execute("SET threads=32")
con.execute("SET memory_limit='200GB'")
con.execute(f"SET temp_directory='{OUT}/tmp'")

T = {
    "patients": f"SELECT * FROM read_csv_auto('{M}/hosp/patients.csv.gz')",
    "admissions": f"SELECT subject_id, hadm_id, admittime, dischtime, deathtime, admission_type, admission_location, "
                  f"discharge_location, edregtime, edouttime, hospital_expire_flag FROM read_csv_auto('{M}/hosp/admissions.csv.gz')",
    "diagnoses_icd": f"SELECT subject_id, hadm_id, seq_num, upper(replace(trim(icd_code), '.', '')) icd_code, icd_version "
                     f"FROM read_csv('{M}/hosp/diagnoses_icd.csv.gz', header=true, all_varchar=true)",
    "procedures_icd": f"SELECT subject_id, hadm_id, seq_num, chartdate, upper(trim(icd_code)) icd_code, icd_version "
                      f"FROM read_csv('{M}/hosp/procedures_icd.csv.gz', header=true, types={{'icd_code':'VARCHAR','chartdate':'DATE'}})",
    "prescriptions": f"SELECT subject_id, hadm_id, pharmacy_id, poe_id, starttime, stoptime, drug_type, drug, route, prod_strength "
                     f"FROM read_csv('{M}/hosp/prescriptions.csv.gz', header=true, all_varchar=false, "
                     f"types={{'drug':'VARCHAR','route':'VARCHAR','prod_strength':'VARCHAR','poe_id':'VARCHAR','ndc':'VARCHAR','gsn':'VARCHAR'}})",
    "omr": f"SELECT * FROM read_csv('{M}/hosp/omr.csv.gz', header=true, types={{'result_value':'VARCHAR'}})",
    "transfers": f"SELECT * FROM read_csv_auto('{M}/hosp/transfers.csv.gz')",
    "d_labitems": f"SELECT * FROM read_csv_auto('{M}/hosp/d_labitems.csv.gz')",
    "emar": f"SELECT subject_id, hadm_id, charttime, medication, event_txt FROM read_csv('{M}/hosp/emar.csv.gz', header=true, "
            f"types={{'medication':'VARCHAR','event_txt':'VARCHAR','poe_id':'VARCHAR','pharmacy_id':'VARCHAR'}})",
    "labevents": f"SELECT subject_id, hadm_id, itemid, charttime, valuenum FROM read_csv('{M}/hosp/labevents.csv.gz', header=true, "
                 f"types={{'value':'VARCHAR','valueuom':'VARCHAR','comments':'VARCHAR','flag':'VARCHAR','priority':'VARCHAR',"
                 f"'ref_range_lower':'DOUBLE','ref_range_upper':'DOUBLE','hadm_id':'BIGINT','order_provider_id':'VARCHAR'}})",
    # ICU vitals subset: HR 220045, NIBP sys/dia 220179/220180, arterial sys/dia 220050/220051
    "icu_vitals": f"SELECT subject_id, hadm_id, itemid, charttime, valuenum FROM read_csv('{M}/icu/chartevents.csv.gz', header=true, "
                  f"types={{'value':'VARCHAR','valueuom':'VARCHAR','warning':'VARCHAR','hadm_id':'BIGINT','stay_id':'BIGINT','caregiver_id':'BIGINT'}}) "
                  f"WHERE itemid IN (220045, 220179, 220180, 220050, 220051) AND valuenum IS NOT NULL",
    "ecg_records": f"SELECT subject_id, study_id, ecg_time FROM read_csv_auto('{ECG}')",
}
only = sys.argv[1:] or list(T)
for name in only:
    t0 = time.time()
    dst = f"{OUT}/{name}.parquet"
    if os.path.exists(dst):
        print(name, "exists", flush=True)
        continue
    con.execute(f"COPY ({T[name]}) TO '{dst}.tmp' (FORMAT parquet, COMPRESSION zstd)")
    os.rename(f"{dst}.tmp", dst)
    n = con.execute(f"SELECT count(*) FROM '{dst}'").fetchone()[0]
    print(name, n, f"{time.time() - t0:.0f}s", flush=True)
