"""Shared definitions for the v1.5 MIMIC-IV cohort / outcome builders (protocol-v1.5).

ICD-10 prefixes follow scripts/trial_specs.py; ICD-9-CM equivalents are hand-mapped here
(no GEMs table is available on disk). Codes are matched per icd_version on the dot-free
upper-case code (diagnoses_icd stores codes without dots).
"""
import hashlib
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import trial_specs as TS  # noqa: E402

STAGE = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-shared/stage"
AUDIT = "/mnt/raid0/rbc58/ecg-tte/audits"
TABLES = ["patients", "admissions", "diagnoses_icd", "procedures_icd", "prescriptions", "omr", "transfers",
          "d_labitems", "ecg_records", "labevents", "emar", "icu_vitals"]
TRIAL_KEYS = ["plato", "aristotle", "rocket_af", "transform_hf", "comet"]

# enteral routes that define an exposure order (all study drugs are oral in the RCTs)
ORAL_ROUTES = ["PO", "PO/NG", "ORAL", "NG", "OG", "NG/OG", "PO/OG", "G TUBE", "J TUBE",
               "PO OR ENTERAL TUBE", "ENTERAL TUBE ONLY – NOT ORAL"]
IV_ROUTES = ["IV", "IV DRIP", "IV BOLUS", "IV INFUSION"]

STROKE9 = ["430", "431", "43301", "43311", "43321", "43331", "43381", "43391", "43401", "43411", "43491", "436"]

# concept -> (ICD-10 prefixes, ICD-9 prefixes)
CONCEPTS = {
    # DX_CORE (trial_specs.DX_CORE) + ICD-9 equivalents
    "ischemic_heart_disease_or_mi": (TS.DX_CORE["ischemic_heart_disease_or_mi"], ["410", "411", "412", "413", "414"]),
    "atrial_fibrillation": (TS.DX_CORE["atrial_fibrillation"], ["42731"]),
    "hypertension": (TS.DX_CORE["hypertension"], ["401", "402", "403", "404", "405"]),
    "diabetes": (TS.DX_CORE["diabetes"], ["250"]),
    "ckd": (TS.DX_CORE["ckd"], ["585"]),
    "stroke_history": (TS.DX_CORE["stroke_history"], STROKE9 + ["432", "438"]),
    "copd_or_asthma": (TS.DX_CORE["copd_or_asthma"], ["491", "492", "493", "496"]),
    "peripheral_arterial_disease": (TS.DX_CORE["peripheral_arterial_disease"], ["4402", "4439"]),
    "valve_disease": (TS.DX_CORE["valve_disease"], ["394", "395", "396", "397", "424"]),
    # trial extra_dx
    "heart_failure": (["I50"], ["428"]),
    "prior_pci_cabg_z": (["Z951", "Z955", "Z9861"], ["V4581", "V4582"]),
    "gi_bleed": (["K92", "K25", "K26", "K27", "K28"], ["578", "531", "532", "533", "534"]),
    "prior_bleed": (["K92", "I60", "I61", "I62", "R31", "R58", "D62"], ["578", "430", "431", "432", "5997", "4590", "2851"]),
    "tia": (["G45"], ["435"]),
    "liver_disease": (["K70", "K72", "K74", "K76"], ["571", "5722", "5723", "5724", "5728", "573"]),
    # gates / exclusions / index-event
    "gate_acs": (["I21", "I24", "I200"], ["410", "4111"]),
    "gate_af": (["I48"], ["42731"]),
    "gate_hf": (["I50"], ["428"]),
    "excl_af_valve": (TS.AF_VALVE, ["3940", "3942", "V433"]),
    "excl_ich": (["I61", "I62"], ["431", "432"]),
    "stemi": (TS.STEMI_CODES, ["4100", "4101", "4102", "4103", "4104", "4105", "4106"]),
    # outcomes
    "out_mi": (["I21", "I22"], ["410"]),
    "out_stroke": (TS.STROKE, STROKE9),
    "out_stroke_se": (TS.STROKE + ["I74"], STROKE9 + ["444"]),
    # negative-control outcomes (hospital-coded, no plausible effect of the study drugs)
    "nco_appendicitis": (["K35"], ["540"]),
    "nco_inguinal_hernia": (["K40"], ["550"]),
    "nco_cholelithiasis": (["K80"], ["574"]),
}
PCI_PX = (["0270", "0271", "0272", "0273"], ["0066", "3601", "3602", "3605", "3606", "3607"])

LABS = {  # name: (itemids, lo, hi)  plausible ranges from trial_specs.NUMERIC_CORE
    "creatinine": ([50912, 52546], 0.1, 25), "potassium": ([50971, 52610], 1.5, 9),
    "sodium": ([50983, 52623], 100, 180), "hemoglobin": ([51222, 51640], 3, 25),
}
VITAL_RANGES = {k: TS.NUMERIC_CORE[k][2:] for k in ("sbp", "dbp", "heart_rate", "bmi")}

GATE = {"plato": ("gate_acs", "window_30d"), "aristotle": ("gate_af", "any"), "rocket_af": ("gate_af", "any"),
        "transform_hf": ("gate_hf", "window_30d"), "comet": ("gate_hf", "any")}
PRIMARY = {  # components: "death" or concept name (readmission diagnosis)
    "plato": ["death", "out_mi", "out_stroke"], "aristotle": ["out_stroke_se"], "rocket_af": ["out_stroke_se"],
    "transform_hf": ["death"], "comet": ["death"]}
ENDPOINT = {
    "plato": "all-cause death or readmission with MI (I21/I22; ICD-9 410) or stroke (I60/I61/I63/I64; ICD-9 430/431/433.x1/434.x1/436), any diagnosis position",
    "aristotle": "readmission with stroke (I60/I61/I63/I64) or systemic embolism (I74; ICD-9 444), any position; death censors",
    "rocket_af": "readmission with stroke (I60/I61/I63/I64) or systemic embolism (I74; ICD-9 444), any position; death censors",
    "transform_hf": "all-cause death (patients.dod)", "comet": "all-cause death (patients.dod)"}
NCOS = ["nco_appendicitis", "nco_inguinal_hernia", "nco_cholelithiasis"]


def out_dir(trial):
    return Path(f"{AUDIT}/claude-v15-mimic-{trial}")


def pid_of(subject_id) -> str:
    return "m" + hashlib.sha256(f"v15-mimic:{int(subject_id)}".encode()).hexdigest()[:15]


def connect(threads=32):
    con = duckdb.connect()
    con.execute(f"SET threads={threads}")
    con.execute("SET memory_limit='150GB'")
    for t in TABLES:
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{STAGE}/{t}.parquet')")
    return con


def concept_table(con, names=None):
    rows = [(n, 10, p) for n, (c10, c9) in CONCEPTS.items() if names is None or n in names for p in c10]
    rows += [(n, 9, p) for n, (c10, c9) in CONCEPTS.items() if names is None or n in names for p in c9]
    import pandas as pd
    con.register("concept_df", pd.DataFrame(rows, columns=["concept", "v", "prefix"]))
    con.execute("CREATE OR REPLACE TEMP TABLE concept AS SELECT * FROM concept_df")


def supp(n):
    n = int(n)
    return n if n == 0 or n >= 11 else "<11"


def sql_list(xs):
    return "[" + ", ".join("'" + x.replace("'", "''").lower() + "'" for x in xs) + "]"
