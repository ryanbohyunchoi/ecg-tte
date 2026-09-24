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
