"""Declared trial specifications for the multi-trial long-tail balance replication.

One dict per adapted trial. Every field is a design choice recorded in
docs/DECISIONS.md; changing one is a new spec version, never a silent edit.

Drug matching follows scripts/screen_trial_feasibility.py: lower(drug_source_value)
is split on '-' and an order matches an arm if any token is one of the arm's
keywords. In OMOP gold drug_source_value is the first word of the order name, so
formulation, route and dose cannot be distinguished (IV enalaprilat is a distinct
token and therefore excluded from ACEi).

Diagnosis prefixes match upper(replace(condition_source_value, '.', '')) (ICD-10-CM;
gold carries ICD-10 source values for every year audited).
"""

ACEI = ["captopril", "enalapril", "lisinopril", "ramipril", "benazepril", "fosinopril",
        "quinapril", "perindopril", "trandolapril", "moexipril",
        "vasotec", "zestril", "prinivil", "altace", "lotensin", "accupril", "monopril"]
ARB = ["losartan", "valsartan", "candesartan", "irbesartan", "olmesartan", "telmisartan",
       "eprosartan", "azilsartan"]
BETA_BLOCKER = ["carvedilol", "metoprolol", "bisoprolol", "atenolol", "nebivolol", "propranolol",
                "labetalol", "nadolol", "coreg", "toprol", "lopressor"]
MRA = ["spironolactone", "eplerenone", "finerenone"]
LOOP = ["furosemide", "bumetanide", "torsemide", "torasemide", "ethacrynic", "lasix", "bumex"]
SGLT2 = ["dapagliflozin", "empagliflozin", "canagliflozin", "ertugliflozin", "bexagliflozin",
         "sotagliflozin", "farxiga", "jardiance", "invokana"]
STATIN = ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin", "lovastatin",
          "pitavastatin", "fluvastatin", "lipitor", "crestor", "zocor"]
ANTICOAG = ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban", "coumadin",
            "eliquis", "xarelto", "pradaxa", "savaysa"]
P2Y12 = ["clopidogrel", "prasugrel", "ticagrelor", "plavix", "effient", "brilinta"]
ANTIPLATELET_ASA = ["aspirin"]
PPI = ["omeprazole", "pantoprazole", "esomeprazole", "lansoprazole", "rabeprazole",
       "dexlansoprazole", "prilosec", "protonix", "nexium"]
ANTIARRHYTHMIC = ["amiodarone", "dronedarone", "sotalol", "flecainide", "propafenone", "dofetilide"]
CCB_RATE = ["diltiazem", "verapamil"]
INSULIN = ["insulin", "lantus", "humalog", "novolog", "levemir", "tresiba", "basaglar"]
NSAID = ["ibuprofen", "naproxen", "meloxicam", "diclofenac", "celecoxib", "ketorolac", "indomethacin"]

# Shared comorbidity prefixes (COMET staging v3 vocabulary, scripts/build_comet_baseline_staging.py)
DX_CORE = {
    "ischemic_heart_disease_or_mi": ["I20", "I21", "I22", "I23", "I24", "I25"],
    "atrial_fibrillation": ["I48"],
    "hypertension": ["I10", "I11", "I12", "I13", "I15"],
    "diabetes": ["E08", "E09", "E10", "E11", "E13"],
    "ckd": ["N18"],
    "stroke_history": ["I60", "I61", "I62", "I63", "I64", "I69"],
    "copd_or_asthma": ["J44", "J45", "J46"],
    "peripheral_arterial_disease": ["I702", "I739"],
    "valve_disease": ["I05", "I06", "I07", "I08", "I34", "I35", "I36", "I37"],
}

# OMOP gold measurement concepts (verified by aggregate concept counts, 2026-09-23)
# name: (concept_id, lookback_days, plausible_low, plausible_high)
NUMERIC_CORE = {
    "sbp": (4152194, 90, 50, 300),
    "dbp": (3012888, 90, 20, 200),
    "heart_rate": (3027018, 90, 20, 250),
    "bmi": (4245997, 365, 10, 100),
    "creatinine": (3016723, 90, 0.1, 25),
    "potassium": (3023103, 90, 1.5, 9),
    "sodium": (3019550, 90, 100, 180),
    "hemoglobin": (3000963, 90, 3, 25),
}
# Index-event characteristics (PLATO): STEMI = I21.0-I21.3; PCI = CPT 92920-92944, C9600-C9608,
# legacy 92980-92982/92995-92996, ICD-10-PCS coronary dilation 0270-0273
STEMI_CODES = ["I210", "I211", "I212", "I213"]
PCI_CODES = ["9292", "9293", "92941", "92943", "92944", "C960", "9298", "9299", "0270", "0271", "0272", "0273"]
# EF comes from echo metadata (EF 5-90), latest in [index-365, index-1].
LVEF_LOOKBACK = 365
# Variables withheld from the "claims-like" base (EF, labs, vitals)
HELDOUT_PHYSIOLOGY = ["lvef", "sbp", "dbp", "heart_rate", "bmi", "creatinine", "potassium",
                      "sodium", "hemoglobin"]
DEMO = ["age_at_index", "male", "index_year"]
UTILISATION = {"outpatient_visits": 9202, "ed_encounters": 9203, "hospital_admissions": 9201}

TRIALS = {
    # COMET: cohort from the JDAT pipeline (docs/COMET_ADAPTED_PROTOCOL.md). This entry is used only
    # to build OMOP-side core features for the external prognostic score (same code as other trials).
    "comet": dict(
        name="COMET (adapted)", spec_version="comet_prognostic_features_v1", published_hr=0.83,
        arms=[("metoprolol_tartrate", ["metoprolol"]), ("carvedilol", ["carvedilol"])],
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I50"]}, exclusions={},
        drugs_90d={"ace_inhibitor_order": ACEI, "arb_order": ARB,
                   "arni_order": ["sacubitril", "entresto"], "mra_order": MRA,
                   "loop_diuretic_order": LOOP, "sglt2_inhibitor_order": SGLT2,
                   "digoxin_order": ["digoxin", "lanoxin"], "amiodarone_order": ["amiodarone"]},
        extra_dx={},
        report_covariates=["lvef", "atrial_fibrillation", "creatinine", "sbp"],
        prognostic=dict(outcome="death_or_hf_hosp_365", gate_codes=["I50"], hosp_codes=["I50"]),
    ),
    "paradigm_hf": dict(
        name="PARADIGM-HF (adapted)", spec_version="paradigm_hf_adapted_v1", published_hr=0.80,
        arms=[("sacubitril_valsartan", ["sacubitril", "entresto"]), ("acei", ACEI)],
        index_start="2015-07-07", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I50"]},
        # Exclusions evaluated on the latest pre-index value (index day excluded). Unknown passes.
        exclusions=dict(
            lvef_gt=40,                   # latest echo EF within 365 d > 40 -> exclude (HFrEF adaptation)
            hfpef_code_only=True,         # EF unknown AND I503x without I502x/I504x -> exclude
            egfr_lt=30, potassium_gt=5.2, sbp_lt=100,
            ever_codes=["T783"],          # angioedema history
        ),
        drugs_90d={"arb_order": ARB, "beta_blocker_order": BETA_BLOCKER, "mra_order": MRA,
                   "loop_diuretic_order": LOOP, "sglt2_inhibitor_order": SGLT2,
                   "digoxin_order": ["digoxin", "lanoxin"], "amiodarone_order": ["amiodarone"]},
        extra_dx={},
        report_covariates=["lvef", "atrial_fibrillation", "creatinine", "sbp"],
        prognostic=dict(outcome="death_or_hf_hosp_365", gate_codes=["I50"], hosp_codes=["I50"]),
    ),
    "plato": dict(
        name="PLATO (adapted)", spec_version="plato_adapted_v1", published_hr=0.84,
        arms=[("ticagrelor", ["ticagrelor", "brilinta"]), ("clopidogrel", ["clopidogrel", "plavix"])],
        index_start="2011-07-20", index_end="2024-06-30",
        gate={"window_30d": ["I21", "I24", "I200"]},
        exclusions=dict(anticoag_30d=ANTICOAG, ever_codes=["I61", "I62"]),  # OAC use; prior ICH
        drugs_90d={"aspirin_order": ANTIPLATELET_ASA, "statin_order": STATIN,
                   "beta_blocker_order": BETA_BLOCKER, "acei_arb_order": ACEI + ARB,
                   "ppi_order": PPI, "insulin_order": INSULIN},
        extra_dx={"heart_failure": ["I50"], "prior_pci_cabg_z": ["Z951", "Z955", "Z9861"],
                  "stemi_30d": None, "gi_bleed": ["K92", "K25", "K26", "K27", "K28"]},
        index_event_pci=True,
        report_covariates=["lvef", "stemi_30d", "pci_index_30d", "creatinine"],
        prognostic=dict(outcome="death_mi_stroke_365", gate_codes=["I21", "I24", "I200"],
                        hosp_codes=["I21", "I22", "I63", "I64"]),
    ),
    "aristotle": dict(
        name="ARISTOTLE (adapted)", spec_version="aristotle_adapted_v1", published_hr=0.79,
        arms=[("apixaban", ["apixaban", "eliquis"]), ("warfarin", ["warfarin", "coumadin", "jantoven"])],
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"]},
        exclusions=dict(ever_codes=["I050", "I052", "I342", "Z952"], other_anticoag_365d=[
            "rivaroxaban", "xarelto", "dabigatran", "pradaxa", "edoxaban", "savaysa"]),
        drugs_90d={"aspirin_order": ANTIPLATELET_ASA, "p2y12_order": P2Y12, "statin_order": STATIN,
                   "beta_blocker_order": BETA_BLOCKER, "acei_arb_order": ACEI + ARB,
                   "antiarrhythmic_order": ANTIARRHYTHMIC, "rate_ccb_order": CCB_RATE,
                   "nsaid_order": NSAID},
        extra_dx={"heart_failure": ["I50"], "prior_bleed": ["K92", "I60", "I61", "I62", "R31", "R58", "D62"],
                  "tia": ["G45"], "liver_disease": ["K70", "K72", "K74", "K76"]},
        report_covariates=["lvef", "age_at_index", "creatinine", "stroke_history"],
        prognostic=dict(outcome="death_stroke_365", gate_codes=["I48"], hosp_codes=["I63", "I64", "I61"]),
    ),
}
