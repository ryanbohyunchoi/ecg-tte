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
PCI_CODES = ["92920", "92921", "92924", "92925", "92928", "92929", "92933", "92934", "92937", "92938", "92941",
             "92943", "92944", "C9600", "C9601", "C9602", "C9603", "C9604", "C9605", "C9606", "C9607", "C9608",
             "92980", "92981", "92982", "92984", "92995", "92996", "0270", "0271", "0272", "0273"]  # v1.1: explicit codes (no valvuloplasty)
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
        arms=[("metoprolol_tartrate", ["metoprolol", "lopressor", "toprol"]), ("carvedilol", ["carvedilol", "coreg"])],
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

# ---- Overnight expansion (2026-09-24): physiology-driven trials (primary tests) and
# ACS/AF anticoagulation controls (no ECG benefit expected). Published HRs are the trials'
# primary-endpoint estimates as recalled; verify against the source papers before any
# RCT-agreement analysis (report.md lists this as an open item).
DOAC_OTHER = ["rivaroxaban", "xarelto", "dabigatran", "pradaxa", "edoxaban", "savaysa", "apixaban", "eliquis"]
HF_DRUGS = {"beta_blocker_order": BETA_BLOCKER, "mra_order": MRA, "loop_diuretic_order": LOOP,
            "sglt2_inhibitor_order": SGLT2, "digoxin_order": ["digoxin", "lanoxin"],
            "amiodarone_order": ["amiodarone"]}
HF_PROG = dict(outcome="death_or_hf_hosp_365", hosp_codes=["I50"])
THIAZIDE = ["chlorthalidone", "hydrochlorothiazide", "indapamide", "thalitone", "microzide"]
AF_VALVE = ["I050", "I052", "I342", "Z952"]

TRIALS.update({
    "paragon_hf": dict(
        name="PARAGON-HF (adapted)", spec_version="paragon_hf_adapted_v1", published_hr=0.87, role="physiology",
        arms=[("sacubitril_valsartan", ["sacubitril", "entresto"]), ("valsartan", ["valsartan", "diovan"])],
        index_start="2015-07-07", index_end="2024-06-30", min_age=50,
        gate={"any_before_or_on_index": ["I50"]},
        exclusions=dict(lvef_lt=45, ef_unknown_require_codes=["I503"], egfr_lt=30, potassium_gt=5.2,
                        sbp_lt=110, ever_codes=["T783"]),
        drugs_90d={"acei_order": ACEI, **HF_DRUGS}, extra_dx={},
        report_covariates=["lvef", "atrial_fibrillation", "creatinine", "sbp"], prognostic=HF_PROG,
        note="valsartan token also matches sacubitril-valsartan combination strings; those persons fall in both arms and the washout removes them"),
    "transform_hf": dict(
        name="TRANSFORM-HF (adapted)", spec_version="transform_hf_adapted_v1", published_hr=1.02, role="physiology",
        arms=[("torsemide", ["torsemide", "torasemide", "demadex"]), ("furosemide", ["furosemide", "lasix"])],
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"window_30d": ["I50"]}, exclusions=dict(egfr_lt=15),
        drugs_90d={"acei_arb_arni_order": ACEI + ARB + ["sacubitril", "entresto"],
                   **{k: v for k, v in HF_DRUGS.items() if k != "loop_diuretic_order"},
                   "thiazide_order": THIAZIDE},
        extra_dx={}, report_covariates=["lvef", "creatinine", "sodium", "atrial_fibrillation"], prognostic=HF_PROG),
    "elite_ii": dict(
        name="ELITE II (adapted)", spec_version="elite_ii_adapted_v1", published_hr=1.13, role="physiology",
        arms=[("arb", ARB + ["cozaar", "diovan"]), ("acei", ACEI)],
        index_start="2013-01-01", index_end="2024-06-30", min_age=60,
        gate={"any_before_or_on_index": ["I50"]},
        exclusions=dict(lvef_gt=40, hfpef_code_only=True, sbp_lt=90, ever_codes=["T783"]),
        drugs_90d=dict(HF_DRUGS), extra_dx={},
        report_covariates=["lvef", "atrial_fibrillation", "creatinine", "sbp"], prognostic=HF_PROG,
        note="class adaptation: any ARB vs any ACEi (trial: losartan vs captopril)"),
    "life": dict(
        name="LIFE (adapted)", spec_version="life_adapted_v1", published_hr=0.87, role="physiology",
        arms=[("losartan", ["losartan", "cozaar"]), ("atenolol", ["atenolol", "tenormin"])],
        index_start="2013-01-01", index_end="2024-06-30", min_age=55, max_age=80,
        gate={"any_before_or_on_index": ["I10", "I11", "I12", "I13", "I15"],
              "ecg_text_365d": ["LEFT VENTRICULAR HYPERTROPHY", "LVH"]},
        exclusions=dict(ever_codes=["I50"], codes_window=[(180, ["I21", "I22", "I63"])]),
        drugs_90d={"acei_order": ACEI, "other_arb_order": [a for a in ARB if a != "losartan"],
                   "other_beta_blocker_order": [b for b in BETA_BLOCKER if b != "atenolol"],
                   "thiazide_order": THIAZIDE, "ccb_order": ["amlodipine", "nifedipine", "diltiazem", "verapamil", "felodipine"],
                   "statin_order": STATIN, "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={"heart_failure": ["I50"]},
        report_covariates=["lvef", "sbp", "creatinine", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"])),
    "dionysos": dict(
        name="DIONYSOS (adapted)", spec_version="dionysos_adapted_v1", published_hr=1.59, role="physiology",
        arms=[("dronedarone", ["dronedarone", "multaq"]), ("amiodarone", ["amiodarone", "pacerone", "cordarone"])],
        index_start="2010-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"]}, exclusions=dict(),
        drugs_90d={"beta_blocker_order": BETA_BLOCKER, "rate_ccb_order": CCB_RATE, "anticoag_order": ANTICOAG,
                   "digoxin_order": ["digoxin", "lanoxin"], "acei_arb_order": ACEI + ARB, "loop_diuretic_order": LOOP,
                   "other_antiarrhythmic_order": ["sotalol", "flecainide", "propafenone", "dofetilide"]},
        extra_dx={"heart_failure": ["I50"]},
        report_covariates=["lvef", "heart_failure", "creatinine", "age_at_index"],
        prognostic=dict(outcome="death_af_hf_stroke_hosp_365", hosp_codes=["I48", "I50", "I63", "I64"])),
    "allhat": dict(
        name="ALLHAT amlodipine vs thiazide (adapted)", spec_version="allhat_adapted_v1", published_hr=0.98, role="control",
        arms=[("amlodipine", ["amlodipine", "norvasc"]), ("thiazide", THIAZIDE)],
        index_start="2013-01-01", index_end="2024-06-30", min_age=55,
        gate={"any_before_or_on_index": ["I10", "I11", "I12", "I13", "I15"]},
        exclusions=dict(ever_codes=["I50"]),
        drugs_90d={"acei_arb_order": ACEI + ARB, "beta_blocker_order": BETA_BLOCKER, "statin_order": STATIN,
                   "aspirin_order": ANTIPLATELET_ASA, "insulin_order": INSULIN},
        extra_dx={}, report_covariates=["sbp", "creatinine", "potassium", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="thiazide class (trial: chlorthalidone); HF history excluded (ALLHAT excluded symptomatic HF)"),
    "triton": dict(
        name="TRITON-TIMI 38 (adapted)", spec_version="triton_adapted_v1", published_hr=0.81, role="control",
        arms=[("prasugrel", ["prasugrel", "effient"]), ("clopidogrel", ["clopidogrel", "plavix"])],
        index_start="2009-07-10", index_end="2024-06-30",
        gate={"window_30d": ["I21", "I24", "I200"], "pci_30d": True},
        exclusions=dict(anticoag_30d=ANTICOAG, ever_codes=["I61", "I62"]),
        drugs_90d=TRIALS["plato"]["drugs_90d"], extra_dx=TRIALS["plato"]["extra_dx"], index_event_pci=True,
        report_covariates=["lvef", "stemi_30d", "stroke_history", "creatinine"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"])),
    "rocket_af": dict(
        name="ROCKET-AF (adapted)", spec_version="rocket_af_adapted_v1", published_hr=0.79, role="control",
        arms=[("rivaroxaban", ["rivaroxaban", "xarelto"]), ("warfarin", ["warfarin", "coumadin", "jantoven"])],
        index_start="2011-11-04", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"]},
        exclusions=dict(ever_codes=AF_VALVE, other_anticoag_365d=[d for d in DOAC_OTHER if d not in ("rivaroxaban", "xarelto")]),
        drugs_90d=TRIALS["aristotle"]["drugs_90d"], extra_dx=TRIALS["aristotle"]["extra_dx"],
        report_covariates=TRIALS["aristotle"]["report_covariates"], prognostic=TRIALS["aristotle"]["prognostic"]),
    "rely": dict(
        name="RE-LY (adapted)", spec_version="rely_adapted_v1", published_hr=0.66, role="control",
        arms=[("dabigatran", ["dabigatran", "pradaxa"]), ("warfarin", ["warfarin", "coumadin", "jantoven"])],
        index_start="2010-10-19", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"]},
        exclusions=dict(ever_codes=AF_VALVE, other_anticoag_365d=[d for d in DOAC_OTHER if d not in ("dabigatran", "pradaxa")]),
        drugs_90d=TRIALS["aristotle"]["drugs_90d"], extra_dx=TRIALS["aristotle"]["extra_dx"],
        report_covariates=TRIALS["aristotle"]["report_covariates"], prognostic=TRIALS["aristotle"]["prognostic"],
        note="published HR = dabigatran 150 mg stroke/SE; dose not identifiable"),
})
for _k, _v in TRIALS.items():
    _v.setdefault("role", "physiology" if _k in ("comet", "paradigm_hf") else "control")

# LIFE v1 (losartan vs atenolol) failed feasibility (atenolol arm 226 after gates). v2 widens,
# before any balance was examined, to ARB class vs cardioselective beta-blockers.
TRIALS["life"] = dict(TRIALS["life"], spec_version="life_adapted_v2",
    arms=[("arb", ARB + ["cozaar", "diovan"]),
          ("beta_blocker", ["atenolol", "tenormin", "metoprolol", "lopressor", "toprol", "bisoprolol", "nebivolol"])],
    drugs_90d={k: v for k, v in TRIALS["life"]["drugs_90d"].items() if k not in ("other_arb_order", "other_beta_blocker_order")}
              | {"other_beta_blocker_order": ["carvedilol", "propranolol", "labetalol", "nadolol", "coreg"]},
    note="v2 class adaptation after v1 feasibility failure (trial: losartan vs atenolol)")

# ---- Published primary results, verified 2026-09-24 against the source papers (web search of
# NEJM/Lancet/JAMA/JCE abstracts). `hr` is in the RCT's own orientation (first arm vs second);
# `our_orientation` gives the estimate with our arm order (arms[0] vs arms[1]).
PUBLISHED = {
    "comet": dict(hr=0.83, ci=(0.74, 0.93), measure="HR", endpoint="all-cause mortality",
                  rct_arms="carvedilol vs metoprolol tartrate", our_orientation=round(1 / 0.83, 3),
                  source="Poole-Wilson et al. Lancet 2003"),
    "paradigm_hf": dict(hr=0.80, ci=(0.73, 0.87), measure="HR", endpoint="CV death or first HF hospitalisation",
                        rct_arms="sacubitril/valsartan vs enalapril", our_orientation=0.80, source="McMurray et al. NEJM 2014"),
    "paragon_hf": dict(hr=0.87, ci=(0.75, 1.01), measure="rate ratio", endpoint="total HF hospitalisations and CV death",
                       rct_arms="sacubitril/valsartan vs valsartan", our_orientation=0.87, source="Solomon et al. NEJM 2019"),
    "transform_hf": dict(hr=1.02, ci=(0.89, 1.18), measure="HR", endpoint="all-cause mortality",
                         rct_arms="torsemide vs furosemide", our_orientation=1.02, source="Mentz et al. JAMA 2023"),
    "elite_ii": dict(hr=1.13, ci=(0.95, 1.35), measure="HR (95.7% CI)", endpoint="all-cause mortality",
                     rct_arms="losartan vs captopril", our_orientation=1.13, source="Pitt et al. Lancet 2000"),
    "life": dict(hr=0.87, ci=(0.77, 0.98), measure="HR (adjusted for Framingham score and ECG-LVH)",
                 endpoint="CV death, MI or stroke", rct_arms="losartan vs atenolol", our_orientation=0.87,
                 source="Dahlöf et al. Lancet 2002"),
    "dionysos": dict(hr=1.59, ci=(1.28, 1.98), measure="HR", endpoint="AF recurrence or premature study-drug discontinuation",
                     rct_arms="dronedarone vs amiodarone", our_orientation=1.59, source="Le Heuzey et al. J Cardiovasc Electrophysiol 2010"),
    "plato": dict(hr=0.84, ci=(0.77, 0.92), measure="HR", endpoint="vascular death, MI or stroke",
                  rct_arms="ticagrelor vs clopidogrel", our_orientation=0.84, source="Wallentin et al. NEJM 2009"),
    "triton": dict(hr=0.81, ci=(0.73, 0.90), measure="HR", endpoint="CV death, MI or stroke",
                   rct_arms="prasugrel vs clopidogrel", our_orientation=0.81, source="Wiviott et al. NEJM 2007"),
    "aristotle": dict(hr=0.79, ci=(0.66, 0.95), measure="HR", endpoint="stroke or systemic embolism",
                      rct_arms="apixaban vs warfarin", our_orientation=0.79, source="Granger et al. NEJM 2011"),
    "rocket_af": dict(hr=0.88, ci=(0.74, 1.03), measure="HR, intention-to-treat (per-protocol 0.79, 0.66-0.96)",
                      endpoint="stroke or systemic embolism", rct_arms="rivaroxaban vs warfarin", our_orientation=0.88,
                      source="Patel et al. NEJM 2011"),
    "rely": dict(hr=0.66, ci=(0.53, 0.82), measure="RR (dabigatran 150 mg)", endpoint="stroke or systemic embolism",
                 rct_arms="dabigatran 150 mg vs warfarin", our_orientation=0.66, source="Connolly et al. NEJM 2009"),
    "allhat": dict(hr=0.98, ci=(0.90, 1.07), measure="RR", endpoint="fatal CHD or nonfatal MI",
                   rct_arms="amlodipine vs chlorthalidone", our_orientation=0.98, source="ALLHAT Officers, JAMA 2002"),
}
TRIALS["rocket_af"]["published_hr"] = 0.88  # ITT benchmark for an initiator (ITT-like) emulation

# ---- Switcher variants (Ryan, 2026-09-24): PARADIGM-HF and PARAGON-HF enrolled patients already
# on ACEi/ARB. Arm 0 = ARNI starters switching from ACEi/ARB; arm 1 = established users continuing
# the trial comparator (PARADIGM: any ACEi; PARAGON: valsartan). See build_trial_cohort.py.
TRIALS["paradigm_hf_switch"] = dict(TRIALS["paradigm_hf"], name="PARADIGM-HF switcher (adapted)",
    spec_version="paradigm_hf_switch_v1", design="switch", prior_class=ACEI + ARB,
    drugs_90d={k: v for k, v in TRIALS["paradigm_hf"]["drugs_90d"].items() if k != "arb_order"},
    note="prevalent new-user design; ARB history is part of the switch definition, so ARB order is not a covariate")
TRIALS["paragon_hf_switch"] = dict(TRIALS["paragon_hf"], name="PARAGON-HF switcher (adapted)",
    spec_version="paragon_hf_switch_v1", design="switch", prior_class=ACEI + ARB + ["cozaar", "diovan"],
    drugs_90d={k: v for k, v in TRIALS["paragon_hf"]["drugs_90d"].items() if k != "acei_order"},
    note="prevalent new-user design; comparator = valsartan continuers")
PUBLISHED["paradigm_hf_switch"] = PUBLISHED["paradigm_hf"]
PUBLISHED["paragon_hf_switch"] = PUBLISHED["paragon_hf"]

# ---- Candidate additions screened 2026-09-24 ----
DPP4I = ["sitagliptin", "januvia", "janumet", "saxagliptin", "onglyza", "kombiglyze", "linagliptin",
         "tradjenta", "jentadueto", "alogliptin", "nesina", "kazano"]
TRIALS["dapa_hf"] = dict(
    name="DAPA-HF / EMPEROR-Reduced (adapted, DPP-4i active-comparator proxy)", spec_version="dapa_hf_adapted_v1",
    published_hr=0.74, role="physiology",
    arms=[("sglt2i", SGLT2 + ["synjardy", "xigduo", "invokamet", "glyxambi", "qtern", "trijardy", "segluromet"]),
          ("dpp4i", DPP4I)],
    index_start="2014-01-08", index_end="2024-06-30",
    gate={"any_before_or_on_index": ["I50"]},
    exclusions=dict(lvef_gt=40, hfpef_code_only=True, egfr_lt=30, sbp_lt=95, ever_codes=["E10"]),
    drugs_90d={"acei_arb_arni_order": ACEI + ARB + ["sacubitril", "entresto"],
               **{k: v for k, v in HF_DRUGS.items() if k != "sglt2_inhibitor_order"},
               "metformin_order": ["metformin"], "insulin_order": INSULIN,
               "sulfonylurea_order": ["glipizide", "glimepiride", "glyburide"],
               "glp1ra_order": ["liraglutide", "semaglutide", "dulaglutide", "exenatide", "victoza", "ozempic", "trulicity"]},
    extra_dx={}, report_covariates=["lvef", "creatinine", "atrial_fibrillation", "diabetes"],
    prognostic=HF_PROG, note="RCTs were placebo-controlled; restricted to T2D via DPP-4i comparator (type 1 excluded)")
TAVR_PCS = ["02RF3", "X2RF3"]
SAVR_PCS = ["02RF0", "02RF4", "X2RF0"]
CABG_CODES = ["0210", "0211", "0212", "0213", "3351", "3352", "3353"]
MITRAL_SURG = ["02RG", "02QG", "02UG"]
TRIALS["partner"] = dict(
    name="PARTNER 2A/3 (adapted): TAVR vs surgical AVR", spec_version="partner_adapted_v1",
    published_hr=0.89, role="physiology", design="procedure",
    arms=[("tavr", TAVR_PCS), ("savr", SAVR_PCS)],
    index_start="2015-10-01", index_end="2024-06-30",
    gate={"any_before_or_on_index": ["I350", "I352", "I060", "I062"]},
    exclusions=dict(concomitant_procedure_codes=CABG_CODES + MITRAL_SURG, ever_codes=["Z952"]),
    drugs_90d={"beta_blocker_order": BETA_BLOCKER, "acei_arb_order": ACEI + ARB, "loop_diuretic_order": LOOP,
               "statin_order": STATIN, "anticoag_order": ANTICOAG, "antiplatelet_order": ANTIPLATELET_ASA + P2Y12},
    extra_dx={"heart_failure": ["I50"], "prior_cabg_pci_z": ["Z951", "Z955", "Z9861"], "liver_disease": ["K70", "K72", "K74"]},
    report_covariates=["lvef", "age_at_index", "creatinine", "copd_or_asthma"],
    prognostic=dict(outcome="death_stroke_365", hosp_codes=["I63", "I64", "I61"]),
    note="procedure exposure by ICD-10-PCS (CPT TAVR family co-coded; ICD-PCS used for arm). Concomitant CABG/mitral surgery within 1 day excluded; prior prosthetic valve excluded")
PUBLISHED["dapa_hf"] = dict(hr=0.74, ci=(0.65, 0.85), measure="HR vs placebo (EMPEROR-Reduced: 0.75, 0.65-0.86)",
                            endpoint="worsening HF or CV death", rct_arms="dapagliflozin vs placebo", our_orientation=0.74,
                            source="McMurray et al. NEJM 2019; Packer et al. NEJM 2020")
PUBLISHED["partner"] = dict(hr=0.89, ci=(0.73, 1.09), measure="HR, ITT (PARTNER 2A, intermediate risk); PARTNER 3 low-risk 0.54 (0.37-0.79) for death/stroke/rehospitalisation at 1 y",
                            endpoint="death or disabling stroke at 2 years", rct_arms="TAVR vs surgical AVR", our_orientation=0.89,
                            source="Leon et al. NEJM 2016; Mack et al. NEJM 2019")

# ---- Outcome contract (protocol v1 draft, 2026-09-24) ----
# CV death: death (Epic/OMOP date) with any listed cause I00-I99 in the CT Vital Statistics
# cause-of-death records (/mnt/raid0/bb2238/ecg_ascvd/omop_database/condition_occurrence/
# condition_occurrence_ct_vitals.parquet; listed causes, no underlying-cause flag; linked by MRN;
# records end 2024-06). Deaths without a cause record count as CV (trial convention: undetermined
# = CV); sensitivity: count them as non-CV. Horizon = the trial's primary-analysis follow-up
# (months; median/mean/planned as published; verify before freeze); sensitivity 12 and 60 months.
CV_DEATH_ICD = ["I"]  # ICD-10 chapter IX
HORIZON_MONTHS = {"comet": 58, "paradigm_hf": 27, "paradigm_hf_switch": 27, "paragon_hf": 35, "transform_hf": 12,
                  "elite_ii": 18, "life": 58, "dionysos": 12, "plato": 12, "aristotle": 22, "rocket_af": 23,
                  "rely": 24, "allhat": 59, "dapa_hf": 18, "partner": 24}

# ---- v1.1 (2026-09-24): sequential switcher design replaces the "switch" design for PARADIGM-HF
TRIALS["paradigm_hf_seq"] = dict(TRIALS["paradigm_hf_switch"], name="PARADIGM-HF switcher, sequential (adapted)",
    spec_version="paradigm_hf_seq_v1", design="switch_seq", seq_ratio=4, seq_window_days=30,
    note="sequential prevalent new-user design: switchers vs established ACEi users sampled at the switch date (+/-30 d, up to 4), no future information; later switching ignored (ITT)")
PUBLISHED["paradigm_hf_seq"] = PUBLISHED["paradigm_hf"]
HORIZON_MONTHS["paradigm_hf_seq"] = 27

# ---- Phase-2 outcome definitions (protocol v1 4b; frozen). Components:
#   "death"        all-cause death (OMOP gold death; data to 2024-12-31)
#   "cv_death"     death with any listed CT-Vitals cause I00-I99, or no cause record (sensitivity: non-CV);
#                  cause records end 2024-06-24, so composites with cv_death are censored there
#   "chd_death"    death with a listed cause I20-I25 (ALLHAT)
#   ("hosp", [codes])  first inpatient stay (visit 9201) starting after index with a qualifying
#                  ICD-10 prefix recorded between its start and end dates
OUTCOMES = {
    "comet": ["death"],
    "paradigm_hf": ["cv_death", ("hosp", ["I50"])],
    "paradigm_hf_switch": ["cv_death", ("hosp", ["I50"])],
    "paradigm_hf_seq": ["cv_death", ("hosp", ["I50"])],
    "paragon_hf": ["cv_death", ("hosp", ["I50"])],
    "transform_hf": ["death"],
    "elite_ii": ["death"],
    "life": ["cv_death", ("hosp", ["I21", "I22"]), ("hosp", ["I60", "I61", "I62", "I63", "I64"])],
    "plato": ["cv_death", ("hosp", ["I21", "I22"]), ("hosp", ["I60", "I61", "I62", "I63", "I64"])],
    "aristotle": [("hosp", ["I61", "I62", "I63", "I64", "I74"])],
    "rocket_af": [("hosp", ["I61", "I62", "I63", "I64", "I74"])],
    "rely": [("hosp", ["I61", "I62", "I63", "I64", "I74"])],
    "allhat": ["chd_death", ("hosp", ["I21", "I22"])],
    "dapa_hf": ["cv_death", ("hosp", ["I50"])],
    "partner": ["death", ("hosp", ["I61", "I62", "I63", "I64"])],
    # dionysos: not emulable (balance-only, protocol v1 4b)
}
# Negative-control outcomes (protocol v1 8): first occurrence; patients with the event in the prior 365 d excluded
NCO = {"nco_cataract": ("proc", ["66982", "66984", "66987", "66988", "08RJ3JZ", "08RK3JZ"]),
       "nco_hernia": ("proc", ["49505", "49507", "49520", "49521", "49525", "49650", "49651",
                                "0YQ5", "0YQ6", "0YQ7", "0YQ8", "0YU5", "0YU6", "0YU7", "0YU8"]),
       "nco_skin_cancer": ("dx", ["C44"])}
DEATH_END, COD_END = "2024-12-31", "2024-06-24"

# ---- v1.2 (2026-09-24, before outcome extraction): harmonised stroke codes (I60 SAH, I61 ICH, I63 ischaemic,
# I64 legacy; subdural I62 excluded), systemic embolism I74; femoral hernia repair codes added.
STROKE = ["I60", "I61", "I63", "I64"]
OUTCOMES.update({
    "life": ["cv_death", ("hosp", ["I21", "I22"]), ("hosp", STROKE)],
    "plato": ["cv_death", ("hosp", ["I21", "I22"]), ("hosp", STROKE)],
    "aristotle": [("hosp", STROKE + ["I74"])], "rocket_af": [("hosp", STROKE + ["I74"])], "rely": [("hosp", STROKE + ["I74"])],
    "partner": ["death", ("hosp", STROKE)],
})
NCO["nco_hernia"] = ("proc", NCO["nco_hernia"][1] + ["49550", "49553", "49555", "49557"])
PUBLISHED["elite_ii"]["ci_level"] = 0.957
# Cross-trial summaries count each RCT once: PARADIGM-HF is represented by the sequential switcher design
# (closest to the trial population, which was already on ACEi/ARB); the new-user design is a sensitivity.
ONE_PER_RCT_EXCLUDE = ["paradigm"]
# Emulation-rating rubric items (a) comparator, (b) eligibility, (c) time zero/setting, (d) endpoint; item (e)
# data sufficiency is computed from clinical-PS pairs in the all-initiator v1.1 grid (>=800: 2; 400-799: 1; <400: 0).
RATING_ITEMS = {"comet": (1, 1, 2, 2), "paradigm_hf": (1, 1, 1, 1), "paradigm_hf_switch": (1, 1, 2, 1),
                "paradigm_hf_seq": (1, 1, 2, 1), "paragon_hf": (2, 1, 1, 1), "transform_hf": (2, 1, 1, 2),
                "elite_ii": (1, 1, 2, 2), "life": (1, 2, 2, 1), "dionysos": (2, 1, 2, 0), "plato": (2, 2, 2, 1),
                "aristotle": (2, 1, 2, 2), "rocket_af": (2, 1, 2, 2), "rely": (1, 1, 2, 2), "allhat": (1, 1, 2, 1),
                "dapa_hf": (0, 1, 2, 1), "partner": (2, 1, 2, 2)}


def rating(key, pairs):
    e = 2 if pairs >= 800 else 1 if pairs >= 400 else 0
    total = sum(RATING_ITEMS[key]) + e
    return total, ("close" if total >= 8 else "moderate" if total >= 6 else "limited"), e

# ---- v1.3 (2026-09-25, exploratory; docs/PROTOCOL_V1_3_AMENDMENT.md I8): expanded negative-control
# outcomes. Chosen for no plausible effect of any study drug class. Excluded: bleeding (anticoagulants,
# antiplatelets), gout (diuretics), angioedema/cough (ACEi/ARNI), gingival hyperplasia/oedema (CCB),
# hypoglycaemia/genital infection/ketoacidosis (SGLT2i), falls/syncope/hypotension, hyperkalaemia,
# photosensitivity-related skin disease beyond the frozen C44 control (thiazides).
NCO_EXT = dict(NCO, **{
    "nco_ingrown_nail": ("dx", ["L600"]), "nco_otitis_externa": ("dx", ["H60"]),
    "nco_seborrheic_keratosis": ("dx", ["L82"]), "nco_carpal_tunnel": ("dx", ["G560"]),
    "nco_plantar_fasciitis": ("dx", ["M722"]), "nco_conjunctivitis": ("dx", ["H10"]),
    "nco_allergic_rhinitis": ("dx", ["J30"]), "nco_lipoma": ("dx", ["D17"]),
    "nco_contact_dermatitis": ("dx", ["L23", "L24", "L25"]), "nco_acne": ("dx", ["L70"]),
    "nco_warts": ("dx", ["B07"]), "nco_onychomycosis": ("dx", ["B351"]), "nco_epidermal_cyst": ("dx", ["L720"]),
    "nco_rotator_cuff": ("dx", ["M751"]), "nco_trigger_finger": ("dx", ["M653"]), "nco_dupuytren": ("dx", ["M720"]),
    "nco_cerumen": ("dx", ["H612"]), "nco_pterygium": ("dx", ["H110"]), "nco_ganglion": ("dx", ["M674"]),
    "nco_hallux_valgus": ("dx", ["M201"]), "nco_chalazion": ("dx", ["H001"]), "nco_dental_caries": ("dx", ["K02"]),
})
PRIMARY_BILLING = "HOSPITAL_BILLING_DX Y"  # v1.3 II4: primary diagnosis of the hospital billing record

# ---- v1.3 Part III (2026-09-25): extension trials. Benchmarks verified from the primary papers /
# PubMed abstracts / ClinicalTrials.gov (docs/v13/rct_facts.json; PARADISE-MI PMID 34758252, CASTLE-AF
# PMID 29385358). Same frozen v1.1/v1.2 pipeline; primary-set rule (>= 400 clinical-PS pairs) before outcomes.
AF_ABLATION = ["93656", "02573ZZ", "025S3ZZ", "025T3ZZ"]  # CPT AF ablation; ICD-10-PCS LA / pulmonary-vein destruction (AV-node ablation excluded)
RATE_CONTROL = ["metoprolol", "lopressor", "toprol", "atenolol", "carvedilol", "coreg", "bisoprolol", "nebivolol",
                "diltiazem", "cardizem", "verapamil", "digoxin", "lanoxin"]
HCTZ = ["hydrochlorothiazide", "microzide"]
CVD_CODES = ["I20", "I21", "I22", "I23", "I24", "I25", "I63", "I64", "G45", "I70", "I739"]
HTN = ["I10", "I11", "I12", "I13", "I15"]
SGLT2_ALL = SGLT2 + ["synjardy", "xigduo", "invokamet", "glyxambi", "qtern", "trijardy", "segluromet"]
MI_CODES = ["I21", "I22"]
EXT = {
    "emperor_preserved": dict(
        name="EMPEROR-Preserved (adapted, DPP-4i active-comparator proxy)", spec_version="emperor_preserved_adapted_v1",
        published_hr=0.79, role="physiology", arms=[("sglt2i", SGLT2_ALL), ("dpp4i", DPP4I)],
        index_start="2014-01-08", index_end="2024-06-30", gate={"any_before_or_on_index": ["I50"]},
        exclusions=dict(lvef_lt=41, ef_unknown_require_codes=["I503"], egfr_lt=20, sbp_lt=100, ever_codes=["E10"]),
        drugs_90d=TRIALS["dapa_hf"]["drugs_90d"], extra_dx={}, report_covariates=["lvef", "creatinine", "atrial_fibrillation", "diabetes"],
        prognostic=HF_PROG, note="RCT placebo-controlled; T2D via DPP-4i comparator; HFpEF = latest EF > 40 or I503 code when EF unknown"),
    "east_afnet4": dict(
        name="EAST-AFNET 4 (adapted, sequential: rhythm-control drug added vs continued rate control)",
        spec_version="east_afnet4_adapted_v1", published_hr=0.79, role="physiology", design="switch_seq",
        arms=[("antiarrhythmic", ANTIARRHYTHMIC + ["multaq", "pacerone", "tikosyn", "betapace", "rythmol", "tambocor"]),
              ("rate_control", RATE_CONTROL)], prior_class=RATE_CONTROL,
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "first_dx_within": (["I48"], 365)},
        exclusions=dict(ever_codes=["I050", "I052", "Z952"]),
        drugs_90d={"anticoag_order": ANTICOAG, "acei_arb_order": ACEI + ARB, "loop_diuretic_order": LOOP,
                   "statin_order": STATIN, "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={"heart_failure": ["I50"], "tia": ["G45"]}, report_covariates=["lvef", "heart_failure", "creatinine", "age_at_index"],
        prognostic=dict(outcome="death_af_hf_stroke_hosp_365", hosp_codes=["I48", "I50", "I63", "I64"]),
        note="early AF (first I48 <= 365 d); ablation-first rhythm control not captured; comparator = established rate-control users sampled +/-30 d"),
    "cabana": dict(
        name="CABANA (adapted): AF ablation vs antiarrhythmic drug", spec_version="cabana_adapted_v1", published_hr=0.86,
        role="physiology", design="proc_vs_drug",
        arms=[("af_ablation", AF_ABLATION), ("antiarrhythmic", ANTIARRHYTHMIC + ["multaq", "pacerone", "tikosyn", "betapace", "rythmol", "tambocor"])],
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I48"]},
        exclusions=dict(ever_codes=["I050", "I052", "Z952"]),
        drugs_90d={"anticoag_order": ANTICOAG, "beta_blocker_order": BETA_BLOCKER, "rate_ccb_order": CCB_RATE,
                   "digoxin_order": ["digoxin", "lanoxin"], "acei_arb_order": ACEI + ARB, "loop_diuretic_order": LOOP},
        extra_dx={"heart_failure": ["I50"], "tia": ["G45"]}, report_covariates=["lvef", "heart_failure", "creatinine", "age_at_index"],
        prognostic=dict(outcome="death_stroke_365", hosp_codes=["I63", "I64", "I61"]),
        note="drug arm = antiarrhythmic initiators (trial drug arm allowed rate or rhythm drugs)"),
    "castle_af": dict(
        name="CASTLE-AF (adapted): AF ablation vs antiarrhythmic drug in HFrEF", spec_version="castle_af_adapted_v1",
        published_hr=0.62, role="physiology", design="proc_vs_drug", arms=[("af_ablation", AF_ABLATION),
        ("antiarrhythmic", ANTIARRHYTHMIC + ["multaq", "pacerone", "tikosyn", "betapace", "rythmol", "tambocor"])],
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I48"], "require_all": [["I50"]]},
        exclusions=dict(lvef_gt=35, hfpef_code_only=True, ever_codes=["I050", "I052", "Z952"]),
        drugs_90d={"anticoag_order": ANTICOAG, **HF_DRUGS}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["lvef", "atrial_fibrillation", "creatinine", "sbp"], prognostic=HF_PROG,
        note="trial comparator = medical rate or rhythm control"),
    "paradise_mi": dict(
        name="PARADISE-MI (adapted)", spec_version="paradise_mi_adapted_v1", published_hr=0.90, role="physiology",
        arms=[("sacubitril_valsartan", ["sacubitril", "entresto"]), ("acei", ACEI)],
        index_start="2015-07-07", index_end="2024-06-30", gate={"window_30d": MI_CODES},
        exclusions=dict(lvef_gt=40, egfr_lt=30, potassium_gt=5.2, sbp_lt=100, ever_codes=["T783"]),
        drugs_90d={"arb_order": ARB, "beta_blocker_order": BETA_BLOCKER, "mra_order": MRA, "statin_order": STATIN,
                   "p2y12_order": P2Y12, "loop_diuretic_order": LOOP},
        extra_dx={"heart_failure": ["I50"], "stemi_30d": None}, report_covariates=["lvef", "stemi_30d", "creatinine", "sbp"],
        prognostic=dict(outcome="death_or_hf_hosp_365", gate_codes=MI_CODES, hosp_codes=["I50"]),
        note="trial: LVEF <= 40 and/or pulmonary congestion within 7 d of MI, no prior HF; adaptation: EF > 40 excluded when known"),
    "dcp": dict(
        name="Diuretic Comparison Project (adapted, sequential switch)", spec_version="dcp_adapted_v1", published_hr=1.04,
        role="control", design="switch_seq", arms=[("chlorthalidone", ["chlorthalidone", "thalitone"]), ("hctz", HCTZ)],
        prior_class=HCTZ, index_start="2013-01-01", index_end="2024-06-30", min_age=65, gate={"any_before_or_on_index": HTN},
        exclusions=dict(), drugs_90d={"acei_arb_order": ACEI + ARB, "beta_blocker_order": BETA_BLOCKER, "ccb_order": ["amlodipine", "nifedipine"],
                                     "statin_order": STATIN, "potassium_suppl_order": ["potassium chloride", "klor-con"]},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["sbp", "potassium", "creatinine", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="VA pragmatic switch trial; non-cancer death approximated by all-cause death; urgent revascularisation not captured"),
    "ontarget": dict(
        name="ONTARGET (adapted): ARB vs ACEi in high-risk patients", spec_version="ontarget_adapted_v1", published_hr=1.01,
        role="control", arms=[("arb", ARB + ["cozaar", "diovan", "micardis"]), ("acei", ACEI)], min_age=55,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": CVD_CODES + ["E11"]},
        exclusions=dict(ever_codes=["I50", "T783"], potassium_gt=5.5), drugs_90d={"beta_blocker_order": BETA_BLOCKER, "statin_order": STATIN,
            "aspirin_order": ANTIPLATELET_ASA, "thiazide_order": THIAZIDE, "ccb_order": ["amlodipine", "nifedipine"]},
        extra_dx={}, report_covariates=["sbp", "creatinine", "diabetes", "age_at_index"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="class adaptation (trial: telmisartan vs ramipril); symptomatic HF excluded"),
    "value": dict(
        name="VALUE (adapted): ARB vs amlodipine in hypertension", spec_version="value_adapted_v1", published_hr=1.04,
        role="control", arms=[("arb", ARB + ["cozaar", "diovan"]), ("amlodipine", ["amlodipine", "norvasc"])], min_age=50,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": HTN},
        exclusions=dict(ever_codes=["I50"], codes_window=[(90, MI_CODES + ["I63"])]),
        drugs_90d={"acei_order": ACEI, "beta_blocker_order": BETA_BLOCKER, "thiazide_order": THIAZIDE, "statin_order": STATIN,
                   "aspirin_order": ANTIPLATELET_ASA}, extra_dx={}, report_covariates=["sbp", "creatinine", "diabetes", "age_at_index"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="class adaptation (trial: valsartan); HF requiring ACEi excluded as any HF history"),
    "ascot": dict(
        name="ASCOT-BPLA (adapted): amlodipine vs beta-blocker in hypertension", spec_version="ascot_adapted_v1", published_hr=0.90,
        role="control", arms=[("amlodipine", ["amlodipine", "norvasc"]),
                               ("beta_blocker", ["atenolol", "tenormin", "metoprolol", "lopressor", "toprol", "bisoprolol", "nebivolol"])],
        min_age=40, max_age=79, index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": HTN},
        exclusions=dict(ever_codes=["I50", "I21", "I22", "I252", "I20"], codes_window=[(90, ["I63", "G45"])]),
        drugs_90d={"acei_arb_order": ACEI + ARB, "thiazide_order": THIAZIDE, "statin_order": STATIN, "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={}, report_covariates=["sbp", "creatinine", "diabetes", "age_at_index"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="class adaptation (trial: atenolol); prior MI, treated angina and HF excluded"),
    "empa_reg": dict(
        name="EMPA-REG OUTCOME (adapted, DPP-4i active-comparator proxy)", spec_version="empa_reg_adapted_v1", published_hr=0.86,
        role="control", arms=[("sglt2i", SGLT2_ALL), ("dpp4i", DPP4I)], index_start="2014-01-08", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["E11"], "require_all": [CVD_CODES]},
        exclusions=dict(egfr_lt=30, ever_codes=["E10"], codes_window=[(60, MI_CODES + ["I63", "G45"])]),
        drugs_90d={"metformin_order": ["metformin"], "insulin_order": INSULIN, "sulfonylurea_order": ["glipizide", "glimepiride", "glyburide"],
                   "glp1ra_order": ["liraglutide", "semaglutide", "dulaglutide", "exenatide", "victoza", "ozempic", "trulicity"],
                   "statin_order": STATIN, "acei_arb_order": ACEI + ARB, "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["lvef", "creatinine", "heart_failure", "age_at_index"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="RCT placebo-controlled; DPP-4i comparator as in RCT-DUPLICATE"),
    "carolina": dict(
        name="CAROLINA (adapted): linagliptin vs glimepiride", spec_version="carolina_adapted_v1", published_hr=0.98, role="control",
        arms=[("linagliptin", ["linagliptin", "tradjenta", "jentadueto"]), ("glimepiride", ["glimepiride", "amaryl"])],
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["E11"]},
        exclusions=dict(ever_codes=["E10"], other_drugs_365d=INSULIN + [d for d in DPP4I if d not in ("linagliptin", "tradjenta", "jentadueto")]
                        + ["liraglutide", "semaglutide", "dulaglutide", "exenatide", "victoza", "ozempic", "trulicity", "pioglitazone", "actos"]),
        drugs_90d={"metformin_order": ["metformin"], "sglt2_order": SGLT2_ALL, "statin_order": STATIN, "acei_arb_order": ACEI + ARB,
                   "aspirin_order": ANTIPLATELET_ASA}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="high-CV-risk criterion not applied; insulin/other incretin/TZD users in prior year excluded"),
    "invest": dict(
        name="INVEST (adapted): verapamil vs atenolol in hypertension with CAD", spec_version="invest_adapted_v1", published_hr=0.98,
        role="control", arms=[("verapamil", ["verapamil", "calan", "isoptin"]), ("atenolol", ["atenolol", "tenormin"])], min_age=50,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I20", "I21", "I22", "I25"], "require_all": [HTN]},
        exclusions=dict(other_drugs_365d=[b for b in BETA_BLOCKER if b != "atenolol"] + ["lopressor", "toprol", "coreg"]),
        drugs_90d={"acei_arb_order": ACEI + ARB, "thiazide_order": THIAZIDE, "statin_order": STATIN, "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["sbp", "heart_rate", "creatinine", "heart_failure"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="strategy trial adapted to initiator comparison; other beta-blockers in prior year excluded"),
    "engage_af": dict(
        name="ENGAGE AF-TIMI 48 (adapted): edoxaban vs warfarin", spec_version="engage_af_adapted_v1", published_hr=0.87,
        role="control", arms=[("edoxaban", ["edoxaban", "savaysa"]), ("warfarin", ["warfarin", "coumadin", "jantoven"])],
        index_start="2015-01-08", index_end="2024-06-30", gate={"any_before_or_on_index": ["I48"]},
        exclusions=dict(ever_codes=AF_VALVE, other_anticoag_365d=[d for d in DOAC_OTHER if d not in ("edoxaban", "savaysa")]),
        drugs_90d=TRIALS["aristotle"]["drugs_90d"], extra_dx=TRIALS["aristotle"]["extra_dx"],
        report_covariates=TRIALS["aristotle"]["report_covariates"], prognostic=TRIALS["aristotle"]["prognostic"]),
}
TRIALS.update(EXT)
PUBLISHED.update({
    "emperor_preserved": dict(hr=0.79, ci=(0.69, 0.90), measure="HR vs placebo", endpoint="CV death or HF hospitalisation",
                              rct_arms="empagliflozin vs placebo", our_orientation=0.79, source="Anker et al. NEJM 2021"),
    "east_afnet4": dict(hr=0.79, ci=(0.66, 0.94), ci_level=0.96, measure="HR", endpoint="CV death, stroke, HF or ACS hospitalisation",
                        rct_arms="early rhythm control vs usual care", our_orientation=0.79, source="Kirchhof et al. NEJM 2020"),
    "cabana": dict(hr=0.86, ci=(0.65, 1.15), measure="HR, ITT", endpoint="death, disabling stroke, serious bleeding or cardiac arrest",
                   rct_arms="ablation vs drug therapy", our_orientation=0.86, source="Packer et al. JAMA 2019"),
    "castle_af": dict(hr=0.62, ci=(0.43, 0.87), measure="HR", endpoint="death or HF hospitalisation",
                      rct_arms="ablation vs medical therapy (HFrEF)", our_orientation=0.62, source="Marrouche et al. NEJM 2018 (PMID 29385358)"),
    "paradise_mi": dict(hr=0.90, ci=(0.78, 1.04), measure="HR", endpoint="CV death or incident HF",
                        rct_arms="sacubitril/valsartan vs ramipril", our_orientation=0.90, source="Pfeffer et al. NEJM 2021 (PMID 34758252)"),
    "dcp": dict(hr=1.04, ci=(0.94, 1.16), measure="HR", endpoint="MI, stroke, HF hospitalisation, urgent revascularisation, non-cancer death",
                rct_arms="chlorthalidone vs hydrochlorothiazide", our_orientation=1.04, source="Ishani et al. NEJM 2022"),
    "ontarget": dict(hr=1.01, ci=(0.94, 1.09), measure="RR", endpoint="CV death, MI, stroke or HF hospitalisation",
                     rct_arms="telmisartan vs ramipril", our_orientation=1.01, source="ONTARGET Investigators, NEJM 2008"),
    "value": dict(hr=1.04, ci=(0.94, 1.15), measure="HR", endpoint="cardiac morbidity and mortality composite",
                  rct_arms="valsartan vs amlodipine", our_orientation=1.04, source="Julius et al. Lancet 2004"),
    "ascot": dict(hr=0.90, ci=(0.79, 1.02), measure="HR", endpoint="nonfatal MI and fatal CHD",
                  rct_arms="amlodipine vs atenolol", our_orientation=0.90, source="Dahlöf et al. Lancet 2005"),
    "empa_reg": dict(hr=0.86, ci=(0.74, 0.99), ci_level=0.9502, measure="HR vs placebo", endpoint="3-point MACE",
                     rct_arms="empagliflozin vs placebo", our_orientation=0.86, source="Zinman et al. NEJM 2015"),
    "carolina": dict(hr=0.98, ci=(0.84, 1.14), ci_level=0.9547, measure="HR", endpoint="3-point MACE",
                     rct_arms="linagliptin vs glimepiride", our_orientation=0.98, source="Rosenstock et al. JAMA 2019"),
    "invest": dict(hr=0.98, ci=(0.90, 1.06), measure="RR", endpoint="death, nonfatal MI or nonfatal stroke",
                   rct_arms="verapamil-SR vs atenolol strategy", our_orientation=0.98, source="Pepine et al. JAMA 2003"),
    "engage_af": dict(hr=0.87, ci=(0.73, 1.04), ci_level=0.975, measure="HR, ITT (superiority)", endpoint="stroke or systemic embolism",
                      rct_arms="edoxaban 60 mg vs warfarin", our_orientation=0.87, source="Giugliano et al. NEJM 2013"),
})
HORIZON_MONTHS.update({"emperor_preserved": 26, "east_afnet4": 61, "cabana": 49, "castle_af": 38, "paradise_mi": 22, "dcp": 29,
                       "ontarget": 56, "value": 50, "ascot": 66, "empa_reg": 37, "carolina": 76, "invest": 32, "engage_af": 34})
OUTCOMES.update({
    "emperor_preserved": ["cv_death", ("hosp", ["I50"])],
    "east_afnet4": ["cv_death", ("hosp", STROKE), ("hosp", ["I50"]), ("hosp", MI_CODES + ["I200", "I24"])],
    "cabana": ["death", ("hosp", STROKE), ("hosp", ["I46"]), ("hosp", ["K920", "K921", "K922", "I62", "R58", "D62"])],
    "castle_af": ["death", ("hosp", ["I50"])],
    "paradise_mi": ["cv_death", ("hosp", ["I50"])],
    "dcp": ["death", ("hosp", MI_CODES), ("hosp", STROKE), ("hosp", ["I50"])],
    "ontarget": ["cv_death", ("hosp", MI_CODES), ("hosp", STROKE), ("hosp", ["I50"])],
    "value": ["cv_death", ("hosp", ["I50"]), ("hosp", MI_CODES)],
    "ascot": ["chd_death", ("hosp", MI_CODES)],
    "empa_reg": ["cv_death", ("hosp", MI_CODES), ("hosp", STROKE)],
    "carolina": ["cv_death", ("hosp", MI_CODES), ("hosp", STROKE)],
    "invest": ["death", ("hosp", MI_CODES), ("hosp", STROKE)],
    "engage_af": [("hosp", STROKE + ["I74"])],
})
RATING_ITEMS.update({"emperor_preserved": (0, 1, 2, 1), "east_afnet4": (1, 1, 2, 1), "cabana": (1, 1, 2, 1), "castle_af": (1, 1, 2, 1),
                     "paradise_mi": (1, 1, 2, 1), "dcp": (2, 1, 2, 1), "ontarget": (1, 1, 2, 2), "value": (1, 1, 2, 1),
                     "ascot": (1, 1, 2, 1), "empa_reg": (0, 1, 2, 2), "carolina": (2, 1, 2, 2), "invest": (1, 1, 2, 1), "engage_af": (2, 1, 2, 2)})

# ---- v1.3/v1.4 audit fixes (2026-09-25): new cohort versions; v1 cohorts kept as history ----
TRIALS["emperor_preserved"] = dict(TRIALS["emperor_preserved"], spec_version="emperor_preserved_adapted_v2",
    gate={"any_before_or_on_index": ["I50"], "require_all": [["E11"]]},
    note=TRIALS["emperor_preserved"]["note"] + "; v2: type 2 diabetes required (DPP-4i comparator implies T2D; audit fix)")
TRIALS["cabana"] = dict(TRIALS["cabana"], spec_version="cabana_adapted_v2", washout_arms=[1],
    note="v2 (audit fix): ablation arm may have prior antiarrhythmic use (as in CABANA); antiarrhythmic arm = new users without "
         "ablation in the prior year; serious bleeding = GI bleeding / non-traumatic ICH hospitalisation only")
OUTCOMES["cabana"] = ["death", ("hosp", STROKE), ("hosp", ["I46"]), ("hosp", ["K920", "K921", "K922", "I62"])]
TRIALS["east_afnet4"]["add_on"] = True  # per-protocol: rate-control orders in the rhythm-control arm are expected, not switching

# ---- v1.7 (2026-09-27; docs/v16/V17_CONFIRMATION_PLAN.md B): confirmation-set candidate trials. Specs are fixed from the
# published protocols and count-only feasibility (docs/v17/candidates.md); benchmarks verified from the primary papers
# before any outcome extraction. Same pipeline as v1.3 Part III. No v1.7 trial has any balance or effect result.
SU = ["glipizide", "glucotrol", "glimepiride", "amaryl", "glyburide", "glynase", "micronase", "diabeta"]
GLP1RA = ["liraglutide", "victoza", "semaglutide", "ozempic", "rybelsus", "dulaglutide", "trulicity", "exenatide", "byetta",
          "bydureon", "lixisenatide", "adlyxin", "albiglutide", "tanzeum", "xultophy", "soliqua", "tirzepatide", "mounjaro"]
TZD = ["pioglitazone", "actos", "rosiglitazone", "avandia", "duetact", "actoplus"]
DM_BASE = {"metformin_order": ["metformin", "glucophage"], "insulin_order": INSULIN, "statin_order": STATIN,
           "acei_arb_order": ACEI + ARB, "aspirin_order": ANTIPLATELET_ASA}
DM_EXCL_RECENT = [(60, MI_CODES + ["I63", "G45"])]
MACE3 = ["cv_death", ("hosp", MI_CODES), ("hosp", STROKE)]
DM_PROG = dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"])
HIGH_RISK = CVD_CODES + ["N18", "I50"]
ARTHRITIS = ["M05", "M06", "M15", "M16", "M17", "M18", "M19"]
V17 = {
    "leader": dict(
        name="LEADER (adapted, DPP-4i active-comparator proxy): liraglutide vs DPP-4i", spec_version="leader_adapted_v1",
        role="control", arms=[("liraglutide", ["liraglutide", "victoza"]), ("dpp4i", DPP4I)], min_age=50,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["E11"], "require_all": [HIGH_RISK]},
        exclusions=dict(ever_codes=["E10"], codes_window=DM_EXCL_RECENT),
        drugs_90d={**DM_BASE, "sulfonylurea_order": SU, "sglt2_order": SGLT2_ALL}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"], prognostic=DM_PROG,
        note="RCT placebo-controlled; DPP-4i comparator as in RCT-DUPLICATE; age >= 50 with CVD, CKD or HF (the >= 60 risk-factor stratum not applied)"),
    "sustain6": dict(
        name="SUSTAIN-6 (adapted, DPP-4i active-comparator proxy): semaglutide vs DPP-4i", spec_version="sustain6_adapted_v1",
        role="control", arms=[("semaglutide", ["semaglutide", "ozempic"]), ("dpp4i", DPP4I)], min_age=50,
        index_start="2017-12-05", index_end="2024-06-30", gate={"any_before_or_on_index": ["E11"], "require_all": [HIGH_RISK]},
        exclusions=dict(ever_codes=["E10"], codes_window=DM_EXCL_RECENT),
        drugs_90d={**DM_BASE, "sulfonylurea_order": SU, "sglt2_order": SGLT2_ALL}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"], prognostic=DM_PROG,
        note="RCT placebo-controlled (injectable semaglutide); oral (rybelsus) and obesity-dose (wegovy) tokens not counted"),
    "rewind": dict(
        name="REWIND (adapted, DPP-4i active-comparator proxy): dulaglutide vs DPP-4i", spec_version="rewind_adapted_v1",
        role="control", arms=[("dulaglutide", ["dulaglutide", "trulicity"]), ("dpp4i", DPP4I)], min_age=50,
        index_start="2014-09-18", index_end="2024-06-30", gate={"any_before_or_on_index": ["E11"]},
        exclusions=dict(ever_codes=["E10"], codes_window=DM_EXCL_RECENT, egfr_lt=15),
        drugs_90d={**DM_BASE, "sulfonylurea_order": SU, "sglt2_order": SGLT2_ALL}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"], prognostic=DM_PROG,
        note="RCT placebo-controlled; broad T2D age >= 50 (trial: CVD or risk factors; ~31% with CVD)"),
    "declare": dict(
        name="DECLARE-TIMI 58 (adapted, DPP-4i active-comparator proxy): dapagliflozin vs DPP-4i", spec_version="declare_adapted_v1",
        role="control", arms=[("dapagliflozin", ["dapagliflozin", "farxiga", "xigduo", "qtern"]), ("dpp4i", DPP4I)], min_age=40,
        index_start="2014-01-08", index_end="2024-06-30", gate={"any_before_or_on_index": ["E11"]},
        exclusions=dict(ever_codes=["E10"], codes_window=DM_EXCL_RECENT, egfr_lt=60),
        drugs_90d={**DM_BASE, "sulfonylurea_order": SU, "glp1ra_order": GLP1RA}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"], prognostic=HF_PROG,
        note="RCT placebo-controlled; DPP-4i comparator as in RCT-DUPLICATE; benchmark = co-primary CV death or HF hospitalisation; CrCl >= 60 approximated by eGFR >= 60"),
    "canvas": dict(
        name="CANVAS Program (adapted, DPP-4i active-comparator proxy): canagliflozin vs DPP-4i", spec_version="canvas_adapted_v1",
        role="control", arms=[("canagliflozin", ["canagliflozin", "invokana", "invokamet"]), ("dpp4i", DPP4I)], min_age=30,
        index_start="2013-03-29", index_end="2024-06-30", gate={"any_before_or_on_index": ["E11"]},
        exclusions=dict(ever_codes=["E10"], codes_window=DM_EXCL_RECENT, egfr_lt=30),
        drugs_90d={**DM_BASE, "sulfonylurea_order": SU, "glp1ra_order": GLP1RA}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"], prognostic=DM_PROG,
        note="RCT placebo-controlled; DPP-4i comparator as in RCT-DUPLICATE"),
    "tecos": dict(
        name="TECOS (adapted, sulfonylurea active-comparator proxy): sitagliptin vs sulfonylurea", spec_version="tecos_adapted_v1",
        role="control", arms=[("sitagliptin", ["sitagliptin", "januvia", "janumet"]), ("sulfonylurea", SU)], min_age=50,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["E11"], "require_all": [CVD_CODES]},
        exclusions=dict(ever_codes=["E10"], egfr_lt=30, other_drugs_365d=GLP1RA + [d for d in DPP4I if d not in ("sitagliptin", "januvia", "janumet")]),
        drugs_90d={**DM_BASE, "sglt2_order": SGLT2_ALL, "tzd_order": TZD}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"], prognostic=DM_PROG,
        note="RCT placebo-controlled; sulfonylurea comparator as in RCT-DUPLICATE; other incretin users in prior year excluded"),
    "savor": dict(
        name="SAVOR-TIMI 53 (adapted, sulfonylurea proxy): saxagliptin vs sulfonylurea", spec_version="savor_adapted_v1",
        role="control", arms=[("saxagliptin", ["saxagliptin", "onglyza", "kombiglyze", "qtern"]), ("sulfonylurea", SU)], min_age=40,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["E11"], "require_all": [CVD_CODES + ["N18"]]},
        exclusions=dict(ever_codes=["E10"], egfr_lt=15, other_drugs_365d=GLP1RA + [d for d in DPP4I if d not in ("saxagliptin", "onglyza", "kombiglyze")]),
        drugs_90d={**DM_BASE, "sglt2_order": SGLT2_ALL, "tzd_order": TZD}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"], prognostic=DM_PROG,
        note="RCT placebo-controlled; sulfonylurea comparator as in RCT-DUPLICATE"),
    "carmelina": dict(
        name="CARMELINA (adapted, sulfonylurea proxy): linagliptin vs sulfonylurea in T2D with kidney disease", spec_version="carmelina_adapted_v1",
        role="control", arms=[("linagliptin", ["linagliptin", "tradjenta", "jentadueto"]), ("sulfonylurea", SU)], min_age=18,
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["E11"], "require_all": [["N18", "E112", "R80", "R809"]]},
        exclusions=dict(ever_codes=["E10", "N186", "Z992"], egfr_lt=15, other_drugs_365d=GLP1RA + [d for d in DPP4I if d not in ("linagliptin", "tradjenta", "jentadueto")]),
        drugs_90d={**DM_BASE, "sglt2_order": SGLT2_ALL, "tzd_order": TZD}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"], prognostic=DM_PROG,
        note="RCT placebo-controlled; sulfonylurea comparator as in RCT-DUPLICATE; kidney risk = CKD/diabetic kidney disease/albuminuria code; dialysis excluded"),
    "tosca_it": dict(
        name="TOSCA.IT (adapted): pioglitazone vs sulfonylurea added to metformin", spec_version="tosca_it_adapted_v1",
        role="control", arms=[("pioglitazone", ["pioglitazone", "actos", "actoplus", "duetact"]), ("sulfonylurea", SU)], min_age=50, max_age=75,
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["E11"], "require_drugs_365d": [["metformin", "glucophage"]]},
        exclusions=dict(ever_codes=["E10", "I50"], other_drugs_365d=INSULIN),
        drugs_90d={k: v for k, v in DM_BASE.items() if k not in ("metformin_order", "insulin_order")} | {"dpp4i_order": DPP4I, "glp1ra_order": GLP1RA, "sglt2_order": SGLT2_ALL},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["creatinine", "age_at_index", "sbp", "bmi"], prognostic=DM_PROG,
        note="pragmatic open-label active-comparator RCT; HF excluded (trial excluded HF); urgent coronary revascularisation not captured"),
    "valiant": dict(
        name="VALIANT (adapted): ARB vs ACEi after MI with LV dysfunction", spec_version="valiant_adapted_v1", role="physiology",
        arms=[("arb", ARB + ["cozaar", "diovan"]), ("acei", ACEI)], index_start="2013-01-01", index_end="2024-06-30", min_age=18,
        gate={"window_30d": MI_CODES}, exclusions=dict(lvef_gt=40, egfr_lt=30, sbp_lt=100, ever_codes=["T783"]),
        drugs_90d={"beta_blocker_order": BETA_BLOCKER, "mra_order": MRA, "statin_order": STATIN, "p2y12_order": P2Y12,
                   "loop_diuretic_order": LOOP, "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={"heart_failure": ["I50"], "stemi_30d": None}, report_covariates=["lvef", "stemi_30d", "creatinine", "sbp"],
        prognostic=dict(outcome="death_or_hf_hosp_365", hosp_codes=["I50"]),
        note="class adaptation (trial: valsartan vs captopril, 0.5-10 d after MI with LVEF <= 35-40% and/or HF); EF > 40 excluded when known (as PARADISE-MI)"),
    "accomplish": dict(
        name="ACCOMPLISH (adapted): amlodipine vs HCTZ added to RAS blockade in high-risk hypertension", spec_version="accomplish_adapted_v1",
        role="control", arms=[("amlodipine", ["amlodipine", "norvasc", "lotrel"]), ("hctz", HCTZ)], min_age=55,
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": HTN, "require_all": [CVD_CODES + ["N18", "E11", "I517"]], "require_drugs_365d": [ACEI + ARB]},
        exclusions=dict(ever_codes=["I50"], codes_window=[(90, MI_CODES + ["I63"])]),
        drugs_90d={"beta_blocker_order": BETA_BLOCKER, "statin_order": STATIN, "aspirin_order": ANTIPLATELET_ASA, "insulin_order": INSULIN,
                   "loop_diuretic_order": LOOP},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["sbp", "creatinine", "diabetes", "age_at_index"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="trial: benazepril + amlodipine vs benazepril + HCTZ; adaptation: ACEi/ARB order in prior 365 d (or at index) required; coronary revascularisation not captured"),
    "insight": dict(
        name="INSIGHT (adapted): nifedipine vs thiazide in high-risk hypertension", spec_version="insight_adapted_v1", role="control",
        arms=[("nifedipine", ["nifedipine", "procardia", "adalat"]), ("thiazide", THIAZIDE)], min_age=55, max_age=80,
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": HTN, "require_all": [CVD_CODES + ["E11", "I517", "E78"]]},
        exclusions=dict(ever_codes=["I50"], codes_window=[(90, MI_CODES + ["I63"])]),
        drugs_90d={"acei_arb_order": ACEI + ARB, "beta_blocker_order": BETA_BLOCKER, "statin_order": STATIN, "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={}, report_covariates=["sbp", "creatinine", "diabetes", "age_at_index"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="trial: nifedipine GITS vs co-amilozide; thiazide class; risk factor = CVD, diabetes, LVH or hyperlipidaemia code"),
    "affirm": dict(
        name="AFFIRM (adapted, sequential: rhythm-control drug added vs continued rate control)", spec_version="affirm_adapted_v1",
        role="physiology", design="switch_seq",
        arms=[("antiarrhythmic", ANTIARRHYTHMIC + ["multaq", "pacerone", "tikosyn", "betapace", "rythmol", "tambocor"]), ("rate_control", RATE_CONTROL)],
        prior_class=RATE_CONTROL, min_age=65, index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I48"]},
        exclusions=dict(ever_codes=["I050", "I052", "Z952"]), add_on=True,
        drugs_90d={"anticoag_order": ANTICOAG, "acei_arb_order": ACEI + ARB, "loop_diuretic_order": LOOP, "statin_order": STATIN,
                   "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={"heart_failure": ["I50"], "tia": ["G45"]}, report_covariates=["lvef", "heart_failure", "creatinine", "age_at_index"],
        prognostic=dict(outcome="death_af_hf_stroke_hosp_365", hosp_codes=["I48", "I50", "I63", "I64"]),
        note="as EAST-AFNET 4 design without the early-AF gate; trial age >= 65 or stroke risk factor (age >= 65 applied)"),
    "af_chf": dict(
        name="AF-CHF (adapted, sequential: rhythm-control drug added vs continued rate control in HFrEF)", spec_version="af_chf_adapted_v1",
        role="physiology", design="switch_seq",
        arms=[("antiarrhythmic", ANTIARRHYTHMIC + ["multaq", "pacerone", "tikosyn", "betapace", "rythmol", "tambocor"]), ("rate_control", RATE_CONTROL)],
        prior_class=RATE_CONTROL, index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I48"], "require_all": [["I50"]]},
        exclusions=dict(lvef_gt=35, hfpef_code_only=True, ever_codes=["I050", "I052", "Z952"]), add_on=True,
        drugs_90d={"anticoag_order": ANTICOAG, "acei_arb_arni_order": ACEI + ARB + ["sacubitril", "entresto"], "mra_order": MRA,
                   "loop_diuretic_order": LOOP, "sglt2_inhibitor_order": SGLT2},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["lvef", "atrial_fibrillation", "creatinine", "sbp"], prognostic=HF_PROG,
        note="trial: LVEF <= 35% with HF and AF; EF > 35 excluded when known"),
    "euclid": dict(
        name="EUCLID (adapted): ticagrelor vs clopidogrel in PAD", spec_version="euclid_adapted_v1", role="control",
        arms=[("ticagrelor", ["ticagrelor", "brilinta"]), ("clopidogrel", ["clopidogrel", "plavix"])], min_age=50,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I702", "I739"]},
        exclusions=dict(anticoag_30d=ANTICOAG, ever_codes=["I61", "I62"], codes_window=[(90, MI_CODES + ["I24", "I200"])]),
        drugs_90d={"aspirin_order": ANTIPLATELET_ASA, "statin_order": STATIN, "beta_blocker_order": BETA_BLOCKER, "acei_arb_order": ACEI + ARB,
                   "ppi_order": PPI, "insulin_order": INSULIN}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "diabetes", "age_at_index", "stroke_history"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="PAD by code; recent ACS excluded (trial excluded patients needing DAPT)"),
    "isar_react5": dict(
        name="ISAR-REACT 5 (adapted): ticagrelor vs prasugrel in ACS", spec_version="isar_react5_adapted_v1", role="control",
        arms=[("ticagrelor", ["ticagrelor", "brilinta"]), ("prasugrel", ["prasugrel", "effient"])],
        index_start="2013-01-01", index_end="2024-06-30", gate={"window_30d": ["I21", "I24", "I200"]},
        exclusions=dict(anticoag_30d=ANTICOAG, ever_codes=["I61", "I62", "I63", "G45"]),
        drugs_90d=TRIALS["plato"]["drugs_90d"], extra_dx=TRIALS["plato"]["extra_dx"], index_event_pci=True,
        report_covariates=["lvef", "stemi_30d", "pci_index_30d", "creatinine"],
        prognostic=dict(outcome="death_mi_stroke_365", gate_codes=["I21", "I24", "I200"], hosp_codes=["I21", "I22", "I63", "I64"]),
        note="prior stroke/TIA excluded (prasugrel contraindication)"),
    "precision": dict(
        name="PRECISION (adapted): celecoxib vs naproxen in arthritis with CV risk", spec_version="precision_adapted_v1", role="control",
        arms=[("celecoxib", ["celecoxib", "celebrex"]), ("naproxen", ["naproxen", "naprosyn", "anaprox", "aleve"])], min_age=18,
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ARTHRITIS, "require_all": [CVD_CODES + ["E11", "E78", "I10", "I11", "I12", "I13", "I15"]]},
        exclusions=dict(codes_window=[(90, MI_CODES + ["I63", "I24", "I200"])], egfr_lt=30,
                        other_drugs_365d=["ibuprofen", "meloxicam", "diclofenac", "ketorolac", "indomethacin", "etodolac", "nabumetone"]),
        drugs_90d={"aspirin_order": ANTIPLATELET_ASA, "ppi_order": PPI, "statin_order": STATIN, "acei_arb_order": ACEI + ARB,
                   "anticoag_order": ANTICOAG, "steroid_order": ["prednisone", "methylprednisolone"]},
        extra_dx={"heart_failure": ["I50"], "gi_bleed": ["K92", "K25", "K26", "K27", "K28"]},
        report_covariates=["creatinine", "sbp", "age_at_index", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="trial arms celecoxib / ibuprofen / naproxen; this emulation = celecoxib vs naproxen (prescribed orders; OTC use unseen); other NSAIDs in prior year excluded"),
    "cares": dict(
        name="CARES (adapted): febuxostat vs allopurinol in gout with CVD", spec_version="cares_adapted_v1", role="control",
        arms=[("febuxostat", ["febuxostat", "uloric"]), ("allopurinol", ["allopurinol", "zyloprim"])], washout_arms=[1],
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["M10", "M1A"], "require_all": [CVD_CODES]},
        exclusions=dict(codes_window=[(60, MI_CODES + ["I63"])], egfr_lt=15),
        drugs_90d={"colchicine_order": ["colchicine", "colcrys", "mitigare"], "aspirin_order": ANTIPLATELET_ASA, "statin_order": STATIN,
                   "acei_arb_order": ACEI + ARB, "thiazide_order": THIAZIDE, "loop_diuretic_order": LOOP, "beta_blocker_order": BETA_BLOCKER},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="febuxostat arm may have prior allopurinol use (as in CARES); allopurinol arm = new users; urgent revascularisation for UA approximated by UA hospitalisation"),
    "fast": dict(
        name="FAST (adapted, sequential switch): febuxostat vs continued allopurinol", spec_version="fast_adapted_v1", role="control",
        design="switch_seq", arms=[("febuxostat", ["febuxostat", "uloric"]), ("allopurinol", ["allopurinol", "zyloprim"])],
        prior_class=["allopurinol", "zyloprim"], min_age=60, index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["M10", "M1A"]}, exclusions=dict(codes_window=[(90, MI_CODES + ["I63"])]),
        drugs_90d=None, extra_dx={"heart_failure": ["I50"]}, report_covariates=["creatinine", "heart_failure", "age_at_index", "sbp"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="trial: allopurinol users age >= 60 with >= 1 CV risk factor, randomised to switch or continue"),
    "oral_surv": dict(
        name="ORAL Surveillance (adapted): tofacitinib vs TNF inhibitor in RA", spec_version="oral_surv_adapted_v1", role="control",
        arms=[("tofacitinib", ["tofacitinib", "xeljanz"]), ("tnfi", ["adalimumab", "humira", "etanercept", "enbrel"])], min_age=50,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["M05", "M06"]}, exclusions=dict(),
        drugs_90d={"methotrexate_order": ["methotrexate"], "steroid_order": ["prednisone"], "statin_order": STATIN, "aspirin_order": ANTIPLATELET_ASA},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["creatinine", "age_at_index", "sbp", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"])),
    "pronounce": dict(
        name="PRONOUNCE (adapted): degarelix vs leuprolide in prostate cancer with ASCVD", spec_version="pronounce_adapted_v1", role="control",
        arms=[("degarelix", ["degarelix", "firmagon"]), ("leuprolide", ["leuprolide", "lupron", "eligard"])],
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["C61"], "require_all": [CVD_CODES]}, exclusions=dict(),
        drugs_90d={"statin_order": STATIN, "aspirin_order": ANTIPLATELET_ASA, "acei_arb_order": ACEI + ARB, "beta_blocker_order": BETA_BLOCKER},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["creatinine", "age_at_index", "sbp", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"])),
    "amplify": dict(
        name="AMPLIFY (adapted): apixaban vs warfarin for acute VTE", spec_version="amplify_adapted_v1", role="control",
        arms=[("apixaban", ["apixaban", "eliquis"]), ("warfarin", ["warfarin", "coumadin", "jantoven"])],
        index_start="2014-08-21", index_end="2024-06-30", gate={"window_30d": ["I26", "I801", "I802", "I824"]},
        exclusions=dict(ever_codes=["I48"], other_anticoag_365d=[d for d in DOAC_OTHER if d not in ("apixaban", "eliquis")]),
        drugs_90d={"aspirin_order": ANTIPLATELET_ASA, "statin_order": STATIN, "nsaid_order": NSAID}, extra_dx={"heart_failure": ["I50"],
        "cancer": ["C"]}, report_covariates=["creatinine", "age_at_index", "heart_failure", "hemoglobin"],
        prognostic=dict(outcome="death_stroke_365", gate_codes=["I26", "I801", "I802", "I824"], hosp_codes=["I26", "I801", "I802", "I824"]),
        note="VTE within 30 d; AF excluded; recurrent VTE = new inpatient stay after the index stay with a VTE code"),
    "ideal": dict(
        name="IDEAL (adapted): atorvastatin vs simvastatin after MI", spec_version="ideal_adapted_v1", role="control",
        arms=[("atorvastatin", ["atorvastatin", "lipitor"]), ("simvastatin", ["simvastatin", "zocor"])], max_age=80,
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I21", "I22", "I252"]},
        exclusions=dict(ever_codes=["I50"], other_drugs_365d=[s for s in STATIN if s not in ("atorvastatin", "lipitor", "simvastatin", "zocor")]),
        drugs_90d={"aspirin_order": ANTIPLATELET_ASA, "p2y12_order": P2Y12, "beta_blocker_order": BETA_BLOCKER, "acei_arb_order": ACEI + ARB,
                   "ezetimibe_order": ["ezetimibe", "zetia"]}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "age_at_index", "sbp", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="dose not identifiable (trial: atorvastatin 80 vs simvastatin 20-40); HF excluded (trial excluded HF)"),
    "lodestar": dict(
        name="LODESTAR (adapted): rosuvastatin vs atorvastatin in CAD", spec_version="lodestar_adapted_v1", role="control",
        arms=[("rosuvastatin", ["rosuvastatin", "crestor"]), ("atorvastatin", ["atorvastatin", "lipitor"])],
        index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I20", "I21", "I22", "I24", "I25"]},
        exclusions=dict(other_drugs_365d=[s for s in STATIN if s not in ("atorvastatin", "lipitor", "rosuvastatin", "crestor")]),
        drugs_90d={"aspirin_order": ANTIPLATELET_ASA, "p2y12_order": P2Y12, "beta_blocker_order": BETA_BLOCKER, "acei_arb_order": ACEI + ARB,
                   "ezetimibe_order": ["ezetimibe", "zetia"]}, extra_dx={"heart_failure": ["I50"]},
        report_covariates=["creatinine", "age_at_index", "sbp", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", hosp_codes=["I21", "I22", "I63", "I64"]),
        note="coronary revascularisation (part of the trial composite) not captured"),
    "prove_it": dict(
        name="PROVE IT-TIMI 22 (adapted): atorvastatin vs pravastatin after ACS", spec_version="prove_it_adapted_v1", role="control",
        arms=[("atorvastatin", ["atorvastatin", "lipitor"]), ("pravastatin", ["pravastatin", "pravachol"])],
        index_start="2013-01-01", index_end="2024-06-30", gate={"window_30d": ["I21", "I24", "I200"]},
        exclusions=dict(other_drugs_365d=[s for s in STATIN if s not in ("atorvastatin", "lipitor", "pravastatin", "pravachol")]),
        drugs_90d={"aspirin_order": ANTIPLATELET_ASA, "p2y12_order": P2Y12, "beta_blocker_order": BETA_BLOCKER, "acei_arb_order": ACEI + ARB},
        extra_dx={"heart_failure": ["I50"], "stemi_30d": None}, report_covariates=["creatinine", "age_at_index", "stemi_30d", "diabetes"],
        prognostic=dict(outcome="death_mi_stroke_365", gate_codes=["I21", "I24", "I200"], hosp_codes=["I21", "I22", "I63", "I64"])),
}
V17["fast"]["drugs_90d"] = {k: v for k, v in V17["cares"]["drugs_90d"].items()}
TRIALS.update(V17)
OUTCOMES.update({
    "leader": MACE3, "sustain6": MACE3, "rewind": MACE3, "canvas": MACE3, "savor": MACE3, "carmelina": MACE3,
    "declare": ["cv_death", ("hosp", ["I50"])],
    "tecos": MACE3 + [("hosp", ["I200"])],
    "tosca_it": ["death", ("hosp", MI_CODES), ("hosp", STROKE)],
    "valiant": ["death"],
    "accomplish": MACE3 + [("hosp", ["I200"]), ("hosp", ["I46"])],
    "insight": MACE3 + [("hosp", ["I50"])],
    "affirm": ["death"], "af_chf": ["cv_death"],
    "euclid": MACE3, "isar_react5": ["death", ("hosp", MI_CODES), ("hosp", STROKE)],
    "precision": MACE3, "cares": MACE3 + [("hosp", ["I200"])], "fast": ["cv_death", ("hosp", MI_CODES + ["I24"]), ("hosp", STROKE)],
    "oral_surv": MACE3, "pronounce": ["death", ("hosp", MI_CODES), ("hosp", STROKE)],
    "amplify": [("hosp", ["I26", "I801", "I802", "I824"])],
    "ideal": ["chd_death", ("hosp", MI_CODES), ("hosp", ["I46"])],
    "lodestar": ["death", ("hosp", MI_CODES), ("hosp", STROKE)],
    "prove_it": ["death", ("hosp", MI_CODES), ("hosp", ["I200"]), ("hosp", STROKE)],
})
HORIZON_MONTHS.update({"leader": 46, "sustain6": 25, "rewind": 65, "declare": 50, "canvas": 43, "tecos": 36, "savor": 25,
                       "carmelina": 26, "tosca_it": 57, "valiant": 25, "accomplish": 36, "insight": 42, "affirm": 42, "af_chf": 37,
                       "euclid": 30, "isar_react5": 12, "precision": 34, "cares": 32, "fast": 48, "oral_surv": 48, "pronounce": 12,
                       "amplify": 6, "ideal": 58, "lodestar": 36, "prove_it": 24})
# v1.7 benchmarks: primary-paper abstracts (PubMed E-utilities text, 2026-09-27); `hr` in the RCT orientation (first-listed
# arm vs comparator/placebo), `our_orientation` = arms[0] vs arms[1]. Registered before any v1.7 outcome extraction.
PUBLISHED.update({
    "leader": dict(hr=0.87, ci=(0.78, 0.97), measure="HR vs placebo", endpoint="CV death, nonfatal MI or nonfatal stroke",
                   rct_arms="liraglutide vs placebo", our_orientation=0.87, source="Marso et al. NEJM 2016;375:311-22 (PMID 27295427)"),
    "sustain6": dict(hr=0.74, ci=(0.58, 0.95), measure="HR vs placebo", endpoint="CV death, nonfatal MI or nonfatal stroke",
                     rct_arms="semaglutide vs placebo", our_orientation=0.74, source="Marso et al. NEJM 2016;375:1834-44 (PMID 27633186)"),
    "rewind": dict(hr=0.88, ci=(0.79, 0.99), measure="HR vs placebo", endpoint="nonfatal MI, nonfatal stroke or CV death (incl. unknown causes)",
                   rct_arms="dulaglutide vs placebo", our_orientation=0.88, source="Gerstein et al. Lancet 2019;394:121-30 (PMID 31189511)"),
    "declare": dict(hr=0.83, ci=(0.73, 0.95), measure="HR vs placebo (co-primary; MACE 0.93, 0.84-1.03)", endpoint="CV death or HF hospitalisation",
                    rct_arms="dapagliflozin vs placebo", our_orientation=0.83, source="Wiviott et al. NEJM 2019;380:347-57 (PMID 30415602)"),
    "canvas": dict(hr=0.86, ci=(0.75, 0.97), measure="HR vs placebo", endpoint="CV death, nonfatal MI or nonfatal stroke",
                   rct_arms="canagliflozin vs placebo", our_orientation=0.86, source="Neal et al. NEJM 2017;377:644-57 (PMID 28605608)"),
    "tecos": dict(hr=0.98, ci=(0.88, 1.09), measure="HR vs placebo (per-protocol primary)", endpoint="CV death, nonfatal MI, nonfatal stroke or UA hospitalisation",
                  rct_arms="sitagliptin vs placebo", our_orientation=0.98, source="Green et al. NEJM 2015;373:232-42 (PMID 26052984)"),
    "carmelina": dict(hr=1.02, ci=(0.89, 1.17), measure="HR vs placebo", endpoint="CV death, nonfatal MI or nonfatal stroke",
                      rct_arms="linagliptin vs placebo", our_orientation=1.02, source="Rosenstock et al. JAMA 2019;321:69-79 (PMID 30418475)"),
    "valiant": dict(hr=1.00, ci=(0.90, 1.11), ci_level=0.975, measure="HR (97.5% CI)", endpoint="all-cause death",
                    rct_arms="valsartan vs captopril", our_orientation=1.00, source="Pfeffer et al. NEJM 2003;349:1893-906 (PMID 14610160)"),
    "insight": dict(hr=1.10, ci=(0.91, 1.34), measure="RR", endpoint="CV death, MI, HF or stroke",
                    rct_arms="nifedipine GITS vs co-amilozide", our_orientation=1.10, source="Brown et al. Lancet 2000;356:366-72 (PMID 10972368)"),
    "affirm": dict(hr=1.15, ci=(0.99, 1.34), measure="HR", endpoint="all-cause death",
                   rct_arms="rhythm control vs rate control", our_orientation=1.15, source="Wyse et al. NEJM 2002;347:1825-33 (PMID 12466506)"),
    "af_chf": dict(hr=1.06, ci=(0.86, 1.30), measure="HR", endpoint="CV death",
                   rct_arms="rhythm control vs rate control (LVEF <= 35%)", our_orientation=1.06, source="Roy et al. NEJM 2008;358:2667-77 (PMID 18565859)"),
    "precision": dict(hr=0.93, ci=(0.76, 1.13), measure="HR, ITT", endpoint="CV death (incl. haemorrhagic), nonfatal MI or nonfatal stroke (APTC)",
                      rct_arms="celecoxib vs naproxen", our_orientation=0.93, source="Nissen et al. NEJM 2016;375:2519-29 (PMID 27959716)"),
    "amplify": dict(hr=0.84, ci=(0.60, 1.18), measure="RR", endpoint="recurrent symptomatic VTE or VTE-related death",
                    rct_arms="apixaban vs enoxaparin/warfarin", our_orientation=0.84, source="Agnelli et al. NEJM 2013;369:799-808 (PMID 23808982)"),
    "lodestar": dict(hr=1.06, ci=(0.86, 1.30), measure="HR", endpoint="3-y death, MI, stroke or any coronary revascularisation",
                     rct_arms="rosuvastatin vs atorvastatin", our_orientation=1.06, source="Lee YJ et al. BMJ 2023;383:e075837 (PMID 37852649)"),
    "prove_it": dict(hr=0.84, ci=(0.74, 0.95), measure="HR (16% reduction, 95% CI 5-26%)", endpoint="death, MI, UA rehospitalisation, revascularisation >= 30 d or stroke",
                     rct_arms="atorvastatin 80 vs pravastatin 40", our_orientation=0.84, source="Cannon et al. NEJM 2004;350:1495-504 (PMID 15007110)"),
})

# ---- v1.8 (2026-09-27; docs/v17/V18_PLANS.md Plan A): prespecified AF confirmation candidates. Specs are fixed from the
# primary publications (PubMed abstracts, E-utilities text, 2026-09-27) before any count-only screen or outcome extraction;
# candidate list and screen in docs/v18/af_candidates.md. Same pipeline as v1.7. No v1.8 trial has any balance or effect result.
# New cohort options (default off): 'arm0_procedure' (switch_seq with a procedure arm 0) and gate 'procedure_1d'.
WARFARIN = ["warfarin", "coumadin", "jantoven"]
LAAO_PERC = ["33340", "02L73DK"]  # CPT percutaneous LAA closure; ICD-10-PCS occlusion of LAA with intraluminal device, percutaneous
# surgical LAA occlusion/excision at open-heart surgery (ICD-10-PCS open approach; CPT 2023+ open codes); thoracoscopic stand-alone excluded
LAAO_SURG = ["02L70", "02B70ZK", "33267", "33268"]
CARDIAC_SURG = CABG_CODES + ["02RF0", "02RF4", "X2RF0", "02RG0", "02RG4", "02QG0", "02QG4", "02UG0", "02UG4",
                             "33405", "33406", "33410", "33411", "33412", "33413", "33425", "33426", "33427", "33430"]
# major bleeding hospitalisation: GI bleeding, peptic ulcer with haemorrhage, intracranial haemorrhage
BLEED_HOSP = ["K920", "K921", "K922", "K250", "K252", "K254", "K256", "K260", "K262", "K264", "K266", "K270", "K272", "K274",
              "K276", "K280", "K282", "K284", "K286", "I60", "I61", "I62"]
PRIOR_BLEED = ["K92", "I60", "I61", "I62", "R31", "R58", "D62"]
PRIOR_TE = ["I63", "I64", "G45", "I69", "I74", "Z8673"]
CHADS_RISK = HTN + ["E10", "E11", "I50"] + PRIOR_TE
AF_DRUGS = TRIALS["aristotle"]["drugs_90d"]
AF_EXTRA = TRIALS["aristotle"]["extra_dx"]
AF_PROG = TRIALS["aristotle"]["prognostic"]
V18 = {
    "prague17": dict(
        name="PRAGUE-17 (adapted, sequential): percutaneous LAA closure vs continued DOAC", spec_version="prague17_adapted_v1",
        role="control", design="switch_seq", arm0_procedure=True, arms=[("laao", LAAO_PERC), ("doac", DOAC_OTHER)],
        prior_class=ANTICOAG + ["jantoven"], index_start="2015-03-13", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "require_all": [PRIOR_BLEED + PRIOR_TE]}, exclusions=dict(ever_codes=AF_VALVE),
        drugs_90d=AF_DRUGS, extra_dx=AF_EXTRA, report_covariates=TRIALS["aristotle"]["report_covariates"], prognostic=AF_PROG,
        note="LAAO with an OAC order in the prior year vs established DOAC users (sequential, +/-30 d, 1:4); high risk = prior bleeding or "
             "thromboembolism code (the CHA2DS2-VASc >= 3 with HAS-BLED > 2 route is not identifiable); procedure complications during the "
             "index stay not captured"),
    "protect_af": dict(
        name="PROTECT AF (adapted, sequential): percutaneous LAA closure vs continued warfarin", spec_version="protect_af_adapted_v1",
        role="control", design="switch_seq", arm0_procedure=True, arms=[("laao", LAAO_PERC), ("warfarin", WARFARIN)],
        prior_class=ANTICOAG + ["jantoven"], index_start="2015-03-13", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "require_all": [CHADS_RISK]}, exclusions=dict(ever_codes=AF_VALVE),
        drugs_90d=AF_DRUGS, extra_dx=AF_EXTRA, report_covariates=TRIALS["aristotle"]["report_covariates"], prognostic=AF_PROG,
        note="LAAO with an OAC order in the prior year vs established warfarin users (sequential); CHADS2 risk factor by code "
             "(age >= 75 alone not applied); shares the LAAO arm with PRAGUE-17"),
    "frail_af": dict(
        name="FRAIL-AF (adapted, sequential): switch from warfarin to a DOAC vs continued warfarin, age >= 75",
        spec_version="frail_af_adapted_v1", role="control", design="switch_seq", arms=[("doac_switch", DOAC_OTHER), ("warfarin", WARFARIN)],
        prior_class=WARFARIN, min_age=75, index_start="2013-01-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I48"]},
        exclusions=dict(ever_codes=AF_VALVE, egfr_lt=30), drugs_90d=AF_DRUGS, extra_dx=AF_EXTRA,
        report_covariates=TRIALS["aristotle"]["report_covariates"], prognostic=AF_PROG,
        note="frailty (Groningen Frailty Indicator >= 3) not identifiable; age >= 75 applied; major/CRNM bleeding -> major-bleeding hospitalisation"),
    "laaos3": dict(
        name="LAAOS III (adapted): surgical LAA occlusion vs none at cardiac surgery in AF", spec_version="laaos3_adapted_v1",
        role="control", design="procedure", arms=[("laa_occlusion", LAAO_SURG), ("cardiac_surgery", CARDIAC_SURG)], washout_arms=[1],
        index_start="2015-10-01", index_end="2024-06-30", gate={"any_before_or_on_index": ["I48"], "procedure_1d": CARDIAC_SURG},
        exclusions=dict(), drugs_90d={**AF_DRUGS, "anticoag_order": ANTICOAG}, extra_dx=AF_EXTRA,
        report_covariates=["lvef", "age_at_index", "creatinine", "stroke_history"], prognostic=AF_PROG,
        note="CABG / valve surgery (open) with vs without a same-day LAA occlusion/excision code; ICD-10-PCS era only; comparator = "
             "surgery without LAA code (washout of arm 1 only); perioperative (index-stay) strokes not counted"),
    "raft_af": dict(
        name="RAFT-AF (adapted, sequential): AF ablation vs continued rate control in HF", spec_version="raft_af_adapted_v1",
        role="physiology", design="switch_seq", arm0_procedure=True, arms=[("af_ablation", AF_ABLATION), ("rate_control", RATE_CONTROL)],
        prior_class=RATE_CONTROL, index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "require_all": [["I50"]]}, exclusions=dict(ever_codes=AF_VALVE),
        drugs_90d={"anticoag_order": ANTICOAG, "antiarrhythmic_order": ANTIARRHYTHMIC, "acei_arb_arni_order": ACEI + ARB + ["sacubitril", "entresto"],
                   "mra_order": MRA, "loop_diuretic_order": LOOP, "sglt2_inhibitor_order": SGLT2},
        extra_dx={"heart_failure": ["I50"]}, report_covariates=["lvef", "atrial_fibrillation", "creatinine", "sbp"], prognostic=HF_PROG,
        note="HF by code (any EF; trial NYHA II-III with raised NT-proBNP); ablation with rate-control use in the prior year vs established "
             "rate-control users without ablation (sequential); comparator antiarrhythmic use not excluded"),
    "augustus": dict(
        name="AUGUSTUS (adapted): apixaban vs warfarin initiation within 30 d after PCI in AF, on a P2Y12 inhibitor",
        spec_version="augustus_adapted_v1", role="control", arms=[("apixaban", ["apixaban", "eliquis"]), ("warfarin", WARFARIN)],
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "pci_30d": True, "require_drugs_365d": [P2Y12]},
        exclusions=dict(ever_codes=AF_VALVE, other_anticoag_365d=[d for d in DOAC_OTHER if d not in ("apixaban", "eliquis")]),
        drugs_90d=AF_DRUGS, extra_dx={**AF_EXTRA, "stemi_30d": None}, index_event_pci=True,
        report_covariates=["creatinine", "age_at_index", "stemi_30d", "hemoglobin"], prognostic=AF_PROG,
        note="PCI in the 30 d before OAC initiation (ACS without PCI not captured); ISTH major/CRNM bleeding -> major-bleeding hospitalisation"),
    "pioneer_af_pci": dict(
        name="PIONEER AF-PCI (adapted): rivaroxaban vs warfarin initiation within 30 d after PCI in AF, on a P2Y12 inhibitor",
        spec_version="pioneer_af_pci_adapted_v1", role="control", arms=[("rivaroxaban", ["rivaroxaban", "xarelto"]), ("warfarin", WARFARIN)],
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "pci_30d": True, "require_drugs_365d": [P2Y12]},
        exclusions=dict(ever_codes=AF_VALVE, other_anticoag_365d=[d for d in DOAC_OTHER if d not in ("rivaroxaban", "xarelto")]),
        drugs_90d=AF_DRUGS, extra_dx={**AF_EXTRA, "stemi_30d": None}, index_event_pci=True,
        report_covariates=["creatinine", "age_at_index", "stemi_30d", "hemoglobin"], prognostic=AF_PROG,
        note="trial group 1 (rivaroxaban 15 mg + P2Y12) vs VKA triple therapy; aspirin not identifiable; dose not identifiable"),
    "re_dual_pci": dict(
        name="RE-DUAL PCI (adapted): dabigatran vs warfarin initiation within 30 d after PCI in AF, on a P2Y12 inhibitor",
        spec_version="re_dual_pci_adapted_v1", role="control", arms=[("dabigatran", ["dabigatran", "pradaxa"]), ("warfarin", WARFARIN)],
        index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "pci_30d": True, "require_drugs_365d": [P2Y12]},
        exclusions=dict(ever_codes=AF_VALVE, other_anticoag_365d=[d for d in DOAC_OTHER if d not in ("dabigatran", "pradaxa")]),
        drugs_90d=AF_DRUGS, extra_dx={**AF_EXTRA, "stemi_30d": None}, index_event_pci=True,
        report_covariates=["creatinine", "age_at_index", "stemi_30d", "hemoglobin"], prognostic=AF_PROG,
        note="benchmark = 150 mg dual vs triple (the US dose); aspirin not identifiable"),
    "active_w": dict(
        name="ACTIVE W (adapted): clopidogrel vs warfarin initiation in AF", spec_version="active_w_adapted_v1", role="control",
        arms=[("clopidogrel", ["clopidogrel", "plavix"]), ("warfarin", WARFARIN)], min_age=55, index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "require_all": [CHADS_RISK + ["I702", "I739"]]},
        exclusions=dict(ever_codes=AF_VALVE + ["I61", "I62"], other_anticoag_365d=DOAC_OTHER,
                        codes_window=[(365, MI_CODES + ["I24", "I200", "Z955"])]),
        drugs_90d=AF_DRUGS, extra_dx=AF_EXTRA, report_covariates=TRIALS["aristotle"]["report_covariates"], prognostic=AF_PROG,
        note="trial: clopidogrel + aspirin vs VKA; aspirin not identifiable; recent ACS/stent (clopidogrel indication) excluded"),
    "renal_af": dict(
        name="RENAL-AF (adapted): apixaban vs warfarin initiation in AF on haemodialysis", spec_version="renal_af_adapted_v1", role="control",
        arms=[("apixaban", ["apixaban", "eliquis"]), ("warfarin", WARFARIN)], index_start="2013-01-01", index_end="2024-06-30",
        gate={"any_before_or_on_index": ["I48"], "require_all": [["N186", "Z992", "Z4931", "Z4932"]]},
        exclusions=dict(ever_codes=AF_VALVE, other_anticoag_365d=[d for d in DOAC_OTHER if d not in ("apixaban", "eliquis")]),
        drugs_90d=AF_DRUGS, extra_dx=AF_EXTRA, report_covariates=TRIALS["aristotle"]["report_covariates"], prognostic=AF_PROG,
        note="ESKD / dialysis by code; major/CRNM bleeding -> major-bleeding hospitalisation"),
}
TRIALS.update(V18)
OUTCOMES.update({
    "prague17": ["cv_death", ("hosp", STROKE + ["G45", "I74"]), ("hosp", BLEED_HOSP)],
    "protect_af": ["cv_death", ("hosp", STROKE + ["I74"])],
    "frail_af": [("hosp", BLEED_HOSP)],
    "laaos3": [("hosp", ["I63", "I64", "I74"])],
    "raft_af": ["death", ("hosp", ["I50"])],
    "augustus": [("hosp", BLEED_HOSP)], "pioneer_af_pci": [("hosp", BLEED_HOSP)], "re_dual_pci": [("hosp", BLEED_HOSP)],
    "active_w": ["cv_death", ("hosp", STROKE + ["I74"]), ("hosp", MI_CODES)],
    "renal_af": [("hosp", BLEED_HOSP)],
})
HORIZON_MONTHS.update({"prague17": 20, "protect_af": 18, "frail_af": 12, "laaos3": 46, "raft_af": 36, "augustus": 6,
                       "pioneer_af_pci": 12, "re_dual_pci": 14, "active_w": 15, "renal_af": 12})
# v1.8 benchmarks: primary-paper abstracts (PubMed E-utilities text, 2026-09-27); `hr` in the RCT orientation, `our_orientation` = arms[0] vs arms[1].
PUBLISHED.update({
    "prague17": dict(hr=0.84, ci=(0.53, 1.31), measure="subdistribution HR, modified ITT", rct_arms="LAA closure vs DOAC",
                     endpoint="stroke/TIA, systemic embolism, CV death, major or CRNM bleeding, procedure/device complications",
                     our_orientation=0.84, source="Osmancik et al. J Am Coll Cardiol 2020;75:3122-35 (PMID 32586585)"),
    "protect_af": dict(hr=0.62, ci=(0.35, 1.25), measure="rate ratio (Bayesian; 95% credible interval), ITT", rct_arms="Watchman LAA closure vs warfarin",
                       endpoint="stroke, CV death or systemic embolism", our_orientation=0.62,
                       source="Holmes et al. Lancet 2009;374:534-42 (PMID 19683639)"),
    "frail_af": dict(hr=1.69, ci=(1.23, 2.32), measure="cause-specific HR, ITT", rct_arms="switch VKA to NOAC vs continue VKA (frail, >= 75 y)",
                     endpoint="major or clinically relevant non-major bleeding", our_orientation=1.69,
                     source="Joosten et al. Circulation 2024;149:279-89 (PMID 37634130)"),
    "laaos3": dict(hr=0.67, ci=(0.53, 0.85), measure="HR", rct_arms="LAA occlusion vs no occlusion during cardiac surgery",
                   endpoint="ischaemic stroke or systemic embolism", our_orientation=0.67,
                   source="Whitlock et al. NEJM 2021;384:2081-91 (PMID 33999547)"),
    "raft_af": dict(hr=0.71, ci=(0.49, 1.03), measure="HR", rct_arms="ablation-based rhythm control vs rate control (HF)",
                    endpoint="all-cause death or HF event", our_orientation=0.71,
                    source="Parkash et al. Circulation 2022;145:1693-704 (PMID 35313733)"),
    "augustus": dict(hr=0.69, ci=(0.58, 0.81), measure="HR (factorial, apixaban vs VKA)", rct_arms="apixaban vs VKA after ACS/PCI",
                     endpoint="ISTH major or clinically relevant non-major bleeding", our_orientation=0.69,
                     source="Lopes et al. NEJM 2019;380:1509-24 (PMID 30883055)"),
    "pioneer_af_pci": dict(hr=0.59, ci=(0.47, 0.76), measure="HR (group 1 vs group 3)", rct_arms="rivaroxaban 15 mg + P2Y12 vs VKA + DAPT",
                           endpoint="clinically significant bleeding", our_orientation=0.59,
                           source="Gibson et al. NEJM 2016;375:2423-34 (PMID 27959713)"),
    "re_dual_pci": dict(hr=0.72, ci=(0.58, 0.88), measure="HR (150 mg dual vs corresponding triple)", rct_arms="dabigatran 150 mg + P2Y12 vs warfarin triple",
                        endpoint="major or clinically relevant non-major bleeding", our_orientation=0.72,
                        source="Cannon et al. NEJM 2017;377:1513-24 (PMID 28844193)"),
    "active_w": dict(hr=1.44, ci=(1.18, 1.76), measure="RR", rct_arms="clopidogrel + aspirin vs oral anticoagulation",
                     endpoint="stroke, non-CNS systemic embolism, MI or vascular death", our_orientation=1.44,
                     source="ACTIVE Writing Group. Lancet 2006;367:1903-12 (PMID 16765759)"),
    "renal_af": dict(hr=1.20, ci=(0.63, 2.30), measure="HR", rct_arms="apixaban vs warfarin (haemodialysis)",
                     endpoint="major or clinically relevant non-major bleeding", our_orientation=1.20,
                     source="Pokorney et al. Circulation 2022;146:1735-45 (PMID 36335914)"),
})
