#!/usr/bin/env python
"""v1.6 extended held-out covariate set (docs/v16/COVARIATES2.md).

Extends scripts/v16/build_v16_covars.py with a broad set of PRE-INDEX balance variables that are never used in
any propensity score: full Charlson / Elixhauser (Quan 2005 ICD-10) components and scores, CHA2DS2-VASc and
HAS-BLED, extra comorbidities, devices / procedures, medication classes (365 d, per-trial exclusion of
exposure-defining drugs), polypharmacy, healthcare use and testing intensity, extra labs / vitals (latest in
365 d + missingness flag), Hospital Frailty Risk Score, preventive-care markers and the few social fields that
exist in the Yale Epic extract.

For each of the 18 trials (make_acc_figure.trials) writes
  /mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars2/<trial>.parquet
keyed by patient_key (every row of the trial's cohort roster, the same key set as claude-v16-covars), plus
dictionary.csv, trial_variable_status.csv, summary_by_arm.csv, summary.json and docs/v16/COVARIATES2.md.

Conventions (match build_v16_covars.py / build_core_baseline.py): windows use the cohort index_date and exclude
the index day; diagnoses = ICD-10-CM prefix (dots removed) in OMOP gold condition_occurrence + observation;
procedures = upper(procedure_source_value) prefix (CPT / HCPCS / ICD-10-PCS); medication orders = '-'-split
lowercase drug_source_value token match (trial_common.create_drug_tokens rule); labs / vitals = OMOP gold
measurement concept ids; Epic encounter tables linked by person.person_source_value (MRN) = PAT_MRN_ID.
Nothing is derived from the index ECG.

Restricted outputs stay under the private output dir (umask 077); stdout and markdown are aggregates with
counts 1-10 (and complements 1-10) suppressed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from trial_common import connect, mrn_key, rp, sha256, sql_list  # noqa: E402
import trial_specs as TS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY  # noqa: E402
from build_v16_covars import analysis_keys, sup, smd, trial_list  # noqa: E402

GOLD = "/mnt/raid0/rbc58/omop/gold"
SNAP = "/mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-t9ZGomLT/snapshot"
OUT = A / "claude-v16-covars2"
DOC = HERE.parent.parent / "docs" / "v16" / "COVARIATES2.md"
LIT = HERE.parent.parent / "docs" / "v16" / "lit_covariates.json"
ALL = 36500  # "all available history" window (days)


def rng(a: str, b: str) -> list[str]:
    """Inclusive ICD/CPT prefix range with a shared alphabetic stem and equal-length numeric tail."""
    m1, m2 = re.match(r"^([A-Z]*)(\d+)$", a), re.match(r"^([A-Z]*)(\d+)$", b)
    assert m1 and m2 and m1.group(1) == m2.group(1) and len(m1.group(2)) == len(m2.group(2)), (a, b)
    w = len(m1.group(2))
    return [f"{m1.group(1)}{i:0{w}d}" for i in range(int(m1.group(2)), int(m2.group(2)) + 1)]


def R(*items) -> list[str]:
    out = []
    for it in items:
        out += rng(*it.split("-")) if "-" in it else [it]
    return out


# ---------------------------------------------------------------------------------------------------------------
# Variable registry. Each variable: name, domain, type (bin / num), definition, source, and one or more of
#   dx=(include prefixes, exclude prefixes), px=[prefixes], rx=[tokens]; win = lookback days (index day excluded);
#   ps = PS core variables of which this is a (partial) duplicate (marked per trial when present in roles core).
# ---------------------------------------------------------------------------------------------------------------
VARS: dict[str, dict] = {}


def add(name, domain, definition, dx=None, dxx=(), px=None, rx=None, win=365, ps=(), typ="bin", source=None):
    src = source or "+".join(s for s, v in (("OMOP condition_occurrence+observation (ICD-10-CM)", dx),
                                              ("OMOP procedure_occurrence (CPT/HCPCS/ICD-10-PCS)", px),
                                              ("OMOP drug_exposure tokens", rx)) if v)
    VARS[name] = dict(name=name, domain=domain, type=typ, definition=definition, source=src, dx=list(dx or []),
                      dxx=list(dxx), px=list(px or []), rx=sorted({t.lower() for t in (rx or [])}), win=win, ps=list(ps))


def wtxt(win):
    return "all prior history" if win >= ALL else f"{win} d"


# ---- Charlson (Quan 2005 ICD-10) --------------------------------------------------------------------------------
DMX = ["E10", "E11", "E12", "E13", "E14"]
CCI = {
    "cci_mi": (["I21", "I22", "I252"], 1, ["ischemic_heart_disease_or_mi"]),
    "cci_chf": (R("I099", "I110", "I130", "I132", "I255", "I420", "I425-I429", "I43", "I50", "P290"), 1, ["heart_failure"]),
    "cci_pvd": (R("I70", "I71", "I731", "I738", "I739", "I771", "I790", "I792", "K551", "K558", "K559", "Z958", "Z959"), 1,
                ["peripheral_arterial_disease"]),
    "cci_cvd": (R("G45", "G46", "H340", "I60-I69"), 1, ["stroke_history", "tia"]),
    "cci_dementia": (R("F00-F03", "F051", "G30", "G311"), 1, []),
    "cci_cpd": (R("I278", "I279", "J40-J47", "J60-J67", "J684", "J701", "J703"), 1, ["copd_or_asthma"]),
    "cci_rheum": (R("M05", "M06", "M315", "M32-M34", "M351", "M353", "M360"), 1, []),
    "cci_pud": (R("K25-K28"), 1, []),
    "cci_mild_liver": (R("B18", "K700-K703", "K709", "K713-K715", "K717", "K73", "K74", "K760", "K762-K764", "K768", "K769", "Z944"), 1,
                       ["liver_disease"]),
    "cci_dm_uncomplicated": ([f"{d}{s}" for d in DMX for s in "01689"], 1, ["diabetes"]),
    "cci_dm_complicated": ([f"{d}{s}" for d in DMX for s in "23457"], 2, ["diabetes"]),
    "cci_hemiplegia": (R("G041", "G114", "G801", "G802", "G81", "G82", "G830-G834", "G839"), 2, []),
    "cci_renal": (R("I120", "I131", "N032-N037", "N052-N057", "N18", "N19", "N250", "Z490-Z492", "Z940", "Z992"), 2, ["ckd"]),
    "cci_malignancy": (R("C00-C26", "C30-C34", "C37-C41", "C43", "C45-C58", "C60-C76", "C81-C85", "C88", "C90-C97"), 2, []),
    "cci_severe_liver": (R("I850", "I859", "I864", "I982", "K704", "K711", "K721", "K729", "K765", "K766", "K767"), 3, ["liver_disease"]),
    "cci_metastatic": (R("C77-C80"), 6, []),
    "cci_hiv": (R("B20-B22", "B24"), 6, []),
}
for k, (codes, w, ps) in CCI.items():
    add(k, "charlson", f"Charlson (Quan 2005 ICD-10) component, weight {w}; any code in 365 d", dx=codes, ps=ps)

# ---- Elixhauser (Quan 2005 ICD-10), van Walraven weights --------------------------------------------------------
ELX = {
    "elx_chf": (CCI["cci_chf"][0], 7, ["heart_failure"]),
    "elx_arrhythmia": (R("I441-I443", "I456", "I459", "I47-I49", "R000", "R001", "R008", "T821", "Z450", "Z950"), 5, ["atrial_fibrillation"]),
    "elx_valvular": (R("A520", "I05-I08", "I091", "I098", "I34-I39", "Q230-Q233", "Z952-Z954"), -1, ["valve_disease"]),
    "elx_pulm_circ": (R("I26", "I27", "I280", "I288", "I289"), 4, []),
    "elx_pvd": (CCI["cci_pvd"][0], 2, ["peripheral_arterial_disease"]),
    "elx_htn_uncomplicated": (["I10"], 0, ["hypertension"]),
    "elx_htn_complicated": (R("I11-I13", "I15"), 0, ["hypertension"]),
    "elx_paralysis": (CCI["cci_hemiplegia"][0], 7, []),
    "elx_other_neuro": (R("G10-G13", "G20-G22", "G254", "G255", "G312", "G318", "G319", "G32", "G35-G37", "G40", "G41", "G931", "G934",
                          "R470", "R56"), 6, []),
    "elx_cpd": (CCI["cci_cpd"][0], 3, ["copd_or_asthma"]),
    "elx_dm_uncomplicated": ([f"{d}{s}" for d in DMX for s in "019"], 0, ["diabetes"]),
    "elx_dm_complicated": ([f"{d}{s}" for d in DMX for s in "2345678"], 0, ["diabetes"]),
    "elx_hypothyroid": (R("E00-E03", "E890"), 0, []),
    "elx_renal": (R("I120", "I131", "N18", "N19", "N250", "Z490-Z492", "Z940", "Z992"), 5, ["ckd"]),
    "elx_liver": (R("B18", "I85", "I864", "I982", "K70", "K711", "K713-K715", "K717", "K72-K74", "K760", "K762-K769", "Z944"), 11,
                  ["liver_disease"]),
    "elx_pud": (R("K257", "K259", "K267", "K269", "K277", "K279", "K287", "K289"), 0, []),
    "elx_hiv": (CCI["cci_hiv"][0], 0, []),
    "elx_lymphoma": (R("C81-C85", "C88", "C96", "C900", "C902"), 9, []),
    "elx_metastatic": (R("C77-C80"), 12, []),
    "elx_solid_tumor": (R("C00-C26", "C30-C34", "C37-C41", "C43", "C45-C58", "C60-C76", "C97"), 4, []),
    "elx_rheum": (R("L940", "L941", "L943", "M05", "M06", "M08", "M120", "M123", "M30", "M310-M313", "M32-M35", "M45", "M461", "M468", "M469"), 0, []),
    "elx_coagulopathy": (R("D65-D68", "D691", "D693-D696"), 3, []),
    "elx_obesity": (["E66"], -4, []),
    "elx_weight_loss": (R("E40-E46", "R634", "R64"), 6, []),
    "elx_fluid_electrolyte": (R("E222", "E86", "E87"), 5, []),
    "elx_blood_loss_anemia": (["D500"], -2, []),
    "elx_deficiency_anemia": (R("D508", "D509", "D51-D53"), -2, []),
    "elx_alcohol": (R("F10", "E52", "G621", "I426", "K292", "K700", "K703", "K709", "T51", "Z502", "Z714", "Z721"), 0, []),
    "elx_drug_abuse": (R("F11-F16", "F18", "F19", "Z715", "Z722"), -7, []),
    "elx_psychoses": (R("F20", "F22-F25", "F28", "F29", "F302", "F312", "F315"), 0, []),
    "elx_depression": (R("F204", "F313-F315", "F32", "F33", "F341", "F412", "F432"), -3, []),
}
for k, (codes, w, ps) in ELX.items():
    add(k, "elixhauser", f"Elixhauser (Quan 2005 ICD-10) component, van Walraven weight {w:+d}; any code in 365 d", dx=codes, ps=ps)

# ---- Hospital Frailty Risk Score (Gilbert 2018), 3-character ICD-10 codes and weights ---------------------------
HFRS = dict(F00=7.1, G81=4.4, G30=4.0, I69=3.7, R29=3.6, N39=3.2, F05=3.2, W19=3.2, S00=3.2, R31=3.0, B96=2.9, R41=2.7, R26=2.6,
            I67=2.6, R56=2.6, R40=2.5, T83=2.4, S06=2.4, S42=2.3, E87=2.3, M25=2.3, E86=2.3, R54=2.2, Z50=2.1, F03=2.1, W18=2.1,
            Z75=2.0, F01=2.0, S80=2.0, L03=2.0, H54=1.9, E53=1.9, Z60=1.8, G20=1.8, R55=1.8, S22=1.8, K59=1.8, N17=1.8, L89=1.7,
            Z22=1.7, B95=1.7, L97=1.6, R44=1.6, K26=1.6, I95=1.6, N19=1.6, A41=1.6, Z87=1.5, J96=1.5, X59=1.5, M19=1.5, G40=1.5,
            M81=1.4, S72=1.4, S32=1.4, E16=1.4, R94=1.4, N18=1.4, R33=1.3, R69=1.3, N28=1.3, R32=1.2, G31=1.2, Y95=1.2, S09=1.2,
            R45=1.2, G45=1.2, Z74=1.1, M79=1.1, W06=1.1, S01=1.1, A04=1.1, A09=1.1, J18=1.1, J69=1.0, R47=1.0, E55=1.0, Z93=1.0,
            R02=1.0, R63=0.9, H91=0.9, W10=0.9, W01=0.9, E05=0.9, M41=0.9, R13=0.8, Z99=0.8, U80=0.8, M80=0.8, K92=0.8, I63=0.8,
            N20=0.7, F10=0.7, Y84=0.7, R00=0.7, J22=0.7, Z73=0.6, R79=0.6, Z91=0.5, S51=0.5, F32=0.5, M48=0.5, E83=0.4, M15=0.4,
            D64=0.4, L08=0.4, R11=0.3, K52=0.3, R50=0.1)

# ---- additional comorbidities (365 d unless noted) --------------------------------------------------------------
CANCER = CCI["cci_malignancy"][0] + CCI["cci_metastatic"][0]
C = "comorbidity"
add("cancer_365", C, "any malignancy C00-C97 (Charlson list incl. metastatic; excludes C44 NMSC) in 365 d", dx=CANCER)
add("cancer_history_ever", C, "malignancy code (as cancer_365) or personal history Z85 at any time before index", dx=CANCER + ["Z85"],
    dxx=["Z85828", "Z8582"], win=ALL)
add("cancer_treatment_365", C, "chemotherapy/radiotherapy encounter Z51.0/Z51.1 or chemo administration CPT 96401-96549, "
    "radiation oncology 77261-77799 in 365 d", dx=["Z510", "Z511"], px=R("96401-96549", "77261-77799"))
add("metastatic_365", C, "C77-C80 in 365 d", dx=R("C77-C80"))
add("dementia", C, "F01-F03, G30, G31.0/.1/.8 in 365 d", dx=R("F01-F03", "G30", "G310", "G311", "G318"))
add("delirium", C, "F05 in 365 d", dx=["F05"])
add("depression", C, "F32, F33, F34.1 in 365 d", dx=["F32", "F33", "F341"])
add("anxiety", C, "F40, F41 in 365 d", dx=["F40", "F41"])
add("ptsd", C, "F43.1 in 365 d", dx=["F431"])
add("serious_mental_illness", C, "schizophrenia/psychotic F20-F29 or bipolar F30-F31 in 365 d", dx=R("F20-F29", "F30", "F31"))
add("alcohol_use_disorder", C, "F10, Z71.41 in 365 d", dx=["F10", "Z7141"])
add("opioid_use_disorder", C, "F11 in 365 d", dx=["F11"])
add("drug_use_disorder_any", C, "F11-F16, F18, F19 in 365 d", dx=R("F11-F16", "F18", "F19"))
add("anemia", C, "D50-D64 in 365 d", dx=R("D50-D64"))
add("iron_deficiency", C, "D50, E61.1 in 365 d", dx=["D50", "E611"])
add("sleep_apnea", C, "G47.3 in 365 d", dx=["G473"])
add("hypothyroidism", C, "E01-E03, E89.0 in 365 d", dx=R("E01-E03", "E890"))
add("hyperthyroidism", C, "E05 in 365 d", dx=["E05"])
add("gout", C, "M10, M1A in 365 d", dx=["M10", "M1A"])
add("osteoporosis", C, "M80, M81 in 365 d", dx=["M80", "M81"])
add("osteoarthritis", C, "M15-M19 in 365 d", dx=R("M15-M19"))
add("rheumatoid_arthritis", C, "M05, M06 in 365 d", dx=["M05", "M06"])
add("falls", C, "W00-W19, R29.6, Z91.81 in 365 d", dx=R("W00-W19", "R296", "Z9181"))
add("hip_fracture", C, "S72 in 365 d", dx=["S72"])
add("pressure_ulcer", C, "L89 in 365 d", dx=["L89"])
add("vte_365", C, "PE I26, DVT I80.1-I80.2, I82.4, I82.5, I82.9, I82.A, I82.B, I82.C in 365 d",
    dx=R("I26", "I801", "I802", "I824", "I825", "I829", "I82A", "I82B", "I82C"))
add("vte_history_ever", C, "VTE code (as vte_365) or Z86.71 at any time before index",
    dx=R("I26", "I801", "I802", "I824", "I825", "I829", "I82A", "I82B", "I82C", "Z8671"), win=ALL)
add("pulmonary_embolism", C, "I26 in 365 d", dx=["I26"])
add("pulmonary_hypertension", C, "I27.0, I27.2, I27.8, I27.9 in 365 d", dx=["I270", "I272", "I278", "I279"])
add("cardiomyopathy_any", C, "I42, I43, I25.5 in 365 d", dx=["I42", "I43", "I255"])
add("cm_dilated", C, "I42.0 in 365 d", dx=["I420"])
add("cm_hypertrophic", C, "I42.1, I42.2 in 365 d", dx=["I421", "I422"])
add("cm_ischemic", C, "I25.5 in 365 d", dx=["I255"])
add("cm_other_restrictive", C, "I42.3-I42.9, I43 in 365 d", dx=R("I423-I429", "I43"))
add("cardiac_amyloidosis", C, "E85 (amyloidosis) with or without I43 in 365 d", dx=["E85"])
add("takotsubo", C, "I51.81 in 365 d", dx=["I5181"])
add("myocarditis_pericarditis", C, "I30-I31, I40-I41 in 365 d", dx=R("I30-I31", "I40-I41"))
add("hf_any_365", C, "I50, I11.0, I13.0, I13.2 in 365 d", dx=["I50", "I110", "I130", "I132"], ps=["heart_failure"])
add("hf_systolic", C, "I50.2 (HFrEF) or I50.4 (combined) in 365 d", dx=["I502", "I504"], ps=["heart_failure"])
add("hf_diastolic", C, "I50.3 (HFpEF) in 365 d", dx=["I503"], ps=["heart_failure"])
add("hf_unspecified_only", C, "I50.1/I50.8/I50.9 in 365 d", dx=["I501", "I508", "I509"], ps=["heart_failure"])
add("syncope", C, "R55 in 365 d", dx=["R55"])
add("cardiac_arrest_ever", C, "I46 or Z86.74 at any time before index", dx=["I46", "Z8674"], win=ALL)
add("ventricular_arrhythmia_ever", C, "VT I47.2, VF/flutter I49.0 at any time before index", dx=["I472", "I490"], win=ALL)
add("ventricular_arrhythmia_365", C, "I47.2, I49.0 in 365 d", dx=["I472", "I490"])
add("svt", C, "I47.1 in 365 d", dx=["I471"])
add("atrial_flutter", C, "I48.3, I48.4, I48.92 in 365 d", dx=["I483", "I484", "I4892"], ps=["atrial_fibrillation"])
add("af_persistent_permanent", C, "I48.1x, I48.2x in 365 d", dx=["I481", "I482"], ps=["atrial_fibrillation"])
add("av_block", C, "I44.0-I44.3 in 365 d", dx=R("I440-I443"))
add("bundle_branch_block", C, "I44.4-I44.7, I45.0-I45.2 (fascicular/LBBB/RBBB) in 365 d", dx=R("I444-I447", "I450-I452"))
add("sick_sinus_brady", C, "sick sinus I49.5 or bradycardia R00.1 in 365 d", dx=["I495", "R001"])
add("long_qt_wpw_other_conduction", C, "I45.5-I45.9 (incl. WPW I45.6, long QT I45.81) in 365 d", dx=R("I455-I459"))
add("conduction_disease_any", C, "I44-I45, I49.5 in 365 d", dx=["I44", "I45", "I495"])
add("prior_mi_ever", C, "I21, I22, I25.2 at any time before index", dx=["I21", "I22", "I252"], win=ALL, ps=["ischemic_heart_disease_or_mi"])
add("acute_mi_365", C, "I21, I22 in 365 d", dx=["I21", "I22"], ps=["ischemic_heart_disease_or_mi"])
add("unstable_angina", C, "I20.0 in 365 d", dx=["I200"], ps=["ischemic_heart_disease_or_mi"])
add("angina_any", C, "I20 in 365 d", dx=["I20"], ps=["ischemic_heart_disease_or_mi"])
add("aortic_stenosis", C, "I35.0, I35.2, I06.0, I06.2 in 365 d", dx=["I350", "I352", "I060", "I062"], ps=["valve_disease"])
add("mitral_regurgitation", C, "I34.0, I05.1 in 365 d", dx=["I340", "I051"], ps=["valve_disease"])
add("aortic_aneurysm", C, "I71 in 365 d", dx=["I71"])
add("carotid_stenosis", C, "I65.2 in 365 d", dx=["I652"])
add("ischemic_stroke_365", C, "I63 in 365 d", dx=["I63"], ps=["stroke_history"])
add("hemorrhagic_stroke_ever", C, "I60-I62 at any time before index", dx=R("I60-I62"), win=ALL, ps=["stroke_history"])
add("stroke_tia_history_ever", C, "I60-I64, I69, G45, Z86.73 at any time before index", dx=R("I60-I64", "I69", "G45", "Z8673"), win=ALL,
    ps=["stroke_history", "tia"])
add("systemic_embolism", C, "arterial embolism/thrombosis I74 in 365 d", dx=["I74"])
add("ckd_stage4_5", C, "N18.4, N18.5, N18.6 in 365 d", dx=["N184", "N185", "N186"], ps=["ckd"])
add("esrd", C, "N18.6 or Z99.2 in 365 d", dx=["N186", "Z992"], ps=["ckd"])
add("aki_365", C, "N17 in 365 d", dx=["N17"])
add("kidney_transplant", C, "Z94.0 at any time before index", dx=["Z940"], win=ALL)
add("cirrhosis", C, "K70.3, K74.6, K74.3-K74.5 in 365 d", dx=["K703", "K743", "K744", "K745", "K746"], ps=["liver_disease"])
add("thrombocytopenia", C, "D69.6, D69.4x in 365 d", dx=["D696", "D694"])
add("hyperkalemia", C, "E87.5 in 365 d", dx=["E875"])
add("hyponatremia", C, "E87.1 in 365 d", dx=["E871"])
add("hypoglycemia", C, "E16.0-E16.2, E11.64x, E10.64x, E13.64x in 365 d", dx=["E160", "E161", "E162", "E1164", "E1064", "E1364"])
add("dm_retinopathy", C, "E08-E13 .3x in 365 d", dx=[f"E{d}3" for d in ("08", "09", "10", "11", "13")], ps=["diabetes"])
add("dm_neuropathy", C, "E08-E13 .4x in 365 d", dx=[f"E{d}4" for d in ("08", "09", "10", "11", "13")], ps=["diabetes"])
add("dm_nephropathy", C, "E08-E13 .2x in 365 d", dx=[f"E{d}2" for d in ("08", "09", "10", "11", "13")], ps=["diabetes", "ckd"])
add("type1_diabetes", C, "E10 in 365 d", dx=["E10"], ps=["diabetes"])
add("prediabetes", C, "R73.0x, R73.9 in 365 d", dx=["R730", "R739"])
add("copd", C, "J44 in 365 d", dx=["J44"], ps=["copd_or_asthma"])
add("asthma", C, "J45 in 365 d", dx=["J45"], ps=["copd_or_asthma"])
add("interstitial_lung_disease", C, "J84 in 365 d", dx=["J84"])
add("home_oxygen", C, "Z99.81 in 365 d", dx=["Z9981"])
add("resp_failure_365", C, "J96 in 365 d", dx=["J96"])
add("pneumonia_365", C, "J12-J18 in 365 d", dx=R("J12-J18"))
add("sepsis_365", C, "A40, A41, R65.2 in 365 d", dx=["A40", "A41", "R652"])
add("uti_365", C, "N39.0 in 365 d", dx=["N390"])
add("gi_bleed_365", C, "K92.0-K92.2, K62.5, peptic ulcer with haemorrhage (K25-K28 .0/.2/.4/.6) in 365 d",
    dx=["K920", "K921", "K922", "K625"] + [f"K{a}{b}" for a in (25, 26, 27, 28) for b in (0, 2, 4, 6)], ps=["prior_bleed", "gi_bleed"])
add("intracranial_bleed_ever", C, "I60-I62, S06.3-S06.6 at any time before index", dx=R("I60-I62", "S063-S066"), win=ALL, ps=["prior_bleed"])
add("bleed_any_365", C, "major/clinically relevant bleeding: GI (as gi_bleed_365), I60-I62, S06.3-S06.6, R04, R31, D62, H35.6, H43.1, "
    "M25.0, N02, R58 in 365 d", dx=["K920", "K921", "K922", "K625"] + [f"K{a}{b}" for a in (25, 26, 27, 28) for b in (0, 2, 4, 6)]
    + R("I60-I62", "S063-S066", "R04", "R31", "D62", "H356", "H431", "M250", "N02", "R58"), ps=["prior_bleed", "gi_bleed"])
add("ibd", C, "K50, K51 in 365 d", dx=["K50", "K51"])
add("psoriasis", C, "L40 in 365 d", dx=["L40"])
add("lupus", C, "M32 in 365 d", dx=["M32"])
add("hiv", C, "B20, Z21 in 365 d", dx=["B20", "Z21"])
add("hepatitis_c", C, "B18.2, B17.1 in 365 d", dx=["B182", "B171"])
add("parkinsonism", C, "G20-G21 in 365 d", dx=["G20", "G21"])
add("epilepsy", C, "G40 in 365 d", dx=["G40"])
add("multiple_sclerosis", C, "G35 in 365 d", dx=["G35"])
add("hemiplegia_paralysis", C, "G81-G83 in 365 d", dx=R("G81-G83"))
add("chronic_pain", C, "G89 in 365 d", dx=["G89"])
add("back_pain", C, "M54 in 365 d", dx=["M54"])
add("obesity_class1_2_bmi30_39", C, "Z68.30-Z68.39 in 365 d", dx=R("Z6830-Z6839"))
add("obesity_class3", C, "severe obesity E66.01, E66.2 or Z68.41-Z68.45 in 365 d", dx=["E6601", "E662"] + R("Z6841-Z6845"))
add("overweight", C, "E66.3 or Z68.25-Z68.29 in 365 d", dx=["E663"] + R("Z6825-Z6829"))
add("underweight_bmi_lt20", C, "Z68.1, Z68.20-Z68.24 in 365 d", dx=["Z681"] + R("Z6820-Z6824"))
add("malnutrition", C, "E40-E46 in 365 d", dx=R("E40-E46"))
add("cachexia_weight_loss", C, "R64, R63.4 in 365 d", dx=["R64", "R634"])
add("dysphagia", C, "R13 in 365 d", dx=["R13"])
add("incontinence", C, "R32, N39.4, R15 in 365 d", dx=["R32", "N394", "R15"])
add("gait_abnormality", C, "R26 in 365 d", dx=["R26"])
add("weakness_debility", C, "R53, R54, M62.81 in 365 d", dx=["R53", "R54", "M6281"])
add("cognitive_symptoms", C, "R41 in 365 d", dx=["R41"])
add("visual_hearing_impairment", C, "H54, H90, H91 in 365 d", dx=["H54", "H90", "H91"])
add("care_dependence", C, "Z74, Z99.3 (wheelchair) in 365 d", dx=["Z74", "Z993"])
add("dnr_status", C, "Z66 (do not resuscitate) in 365 d", dx=["Z66"])
add("palliative_care", C, "Z51.5 in 365 d", dx=["Z515"])
add("institutional_residence", C, "Z59.3 (problems related to living in a residential institution) in 365 d", dx=["Z593"])
add("sdoh_any", C, "social determinants Z55-Z65 in 365 d", dx=R("Z55-Z65"))
add("housing_instability", C, "Z59.0, Z59.1, Z59.8x in 365 d", dx=["Z590", "Z591", "Z598"])
add("noncompliance", C, "Z91.1x (non-adherence to medical treatment) in 365 d", dx=["Z911"])
add("lt_anticoagulant_code", C, "Z79.01 long-term anticoagulant use in 365 d (medication-like; dropped where anticoagulants define exposure)",
    dx=["Z7901"], rx=TS.ANTICOAG)
add("lt_antiplatelet_code", C, "Z79.02 long-term antiplatelet use in 365 d (dropped where antiplatelets define exposure)", dx=["Z7902"],
    rx=TS.P2Y12 + ["aspirin"])
add("lt_insulin_code", C, "Z79.4 long-term insulin use in 365 d", dx=["Z794"], rx=TS.INSULIN)
add("lt_oral_hypoglycemic_code", C, "Z79.84 long-term oral hypoglycemic use in 365 d (dropped where oral hypoglycemics define exposure)",
    dx=["Z7984"], rx=["metformin", "glimepiride", "linagliptin", "sitagliptin", "empagliflozin", "dapagliflozin"])
add("lt_steroid_code", C, "Z79.52 long-term systemic steroid use in 365 d", dx=["Z7952"])
add("tobacco_counseling_or_history", C, "Z71.6, Z87.891, F17 in 365 d", dx=["Z716", "Z87891", "F17"])

# ---- devices / procedures (all prior history unless noted) ------------------------------------------------------
D = "device_procedure"
PM_PX = R("33206-33208", "33212", "33213", "33221", "33227-33229", "33274", "0JH604Z", "0JH605Z", "0JH606Z", "0JH804Z", "0JH805Z",
          "0JH806Z", "93279-93281", "93288", "93293", "93294")
ICD_PX = R("33230", "33231", "33240", "33249", "33262-33264", "33270", "33271", "0JH608Z", "0JH808Z", "93282-93284", "93287", "93289",
           "93295")
CRT_PX = R("33224-33226", "0JH607Z", "0JH609Z", "0JH807Z", "0JH809Z")
add("pacemaker_ever", D, "pacemaker: Z95.0, Z45.01x or pacemaker implant/programming/interrogation CPT/PCS, any prior history",
    dx=["Z950", "Z4501"], px=PM_PX, win=ALL)
add("icd_ever", D, "ICD: Z95.810, Z45.02 or ICD implant/programming/interrogation CPT/PCS, any prior history", dx=["Z95810", "Z4502"],
    px=ICD_PX, win=ALL)
add("crt_ever", D, "CRT (P or D): LV-lead / CRT generator CPT 33224-33226 or PCS 0JH607Z/0JH609Z/0JH807Z/0JH809Z", px=CRT_PX, win=ALL)
add("cied_any_ever", D, "any cardiac implantable electronic device (pacemaker, ICD, CRT, remote CIED monitoring 93296)",
    dx=["Z950", "Z4501", "Z95810", "Z4502"], px=PM_PX + ICD_PX + CRT_PX + ["93296"], win=ALL)
add("loop_recorder_ever", D, "implantable loop recorder: CPT 33285, 93285, 93291, 93298, E0616, Z95.818", px=["33285", "93285", "93291", "93298",
    "E0616"], dx=["Z95818"], win=ALL)
add("lvad_or_heart_tx_ever", D, "LVAD Z95.811 or heart transplant Z94.1, any prior history", dx=["Z95811", "Z941"], win=ALL)
add("prior_pci_ever", D, "PCI: trial_specs.PCI_CODES (CPT/HCPCS/PCS) or Z95.5 / Z98.61, any prior history", px=TS.PCI_CODES,
    dx=["Z955", "Z9861"], win=ALL, ps=["prior_pci_cabg_z"])
add("prior_cabg_ever", D, "CABG: trial_specs.CABG_CODES + CPT 33510-33536 or Z95.1, any prior history", px=TS.CABG_CODES + R("33510-33536"),
    dx=["Z951"], win=ALL, ps=["prior_pci_cabg_z"])
add("prior_pci_365", D, "PCI (as prior_pci_ever) in 365 d", px=TS.PCI_CODES)
add("prior_cath_ever", D, "diagnostic coronary angiography CPT 93454-93461 / 93451-93453, any prior history", px=R("93451-93461"), win=ALL)
add("prior_af_ablation_ever", D, "AF ablation trial_specs.AF_ABLATION (CPT 93656, PCS 02573ZZ/025S3ZZ/025T3ZZ), any prior history",
    px=TS.AF_ABLATION, win=ALL)
add("prior_ablation_any_ever", D, "any EP ablation CPT 93650, 93653-93657, PCS 02583ZZ/02573ZZ/025S3ZZ/025T3ZZ, any prior history",
    px=["93650"] + R("93653-93657") + ["02583ZZ"] + TS.AF_ABLATION, win=ALL)
add("prior_cardioversion_ever", D, "external cardioversion CPT 92960, 92961, PCS 5A2204Z, any prior history", px=["92960", "92961", "5A2204Z"],
    win=ALL)
add("prior_valve_procedure_ever", D, "valve replacement/repair (TAVR, SAVR, mitral surgery/TEER, tricuspid) CPT 33361-33369, 33390-33391, "
    "33405-33430, 33460-33468, 33418-33420, 0483T, PCS TAVR/SAVR/MITRAL_SURG, or Z95.2-Z95.4, any prior history",
    px=R("33361-33369", "33390-33391", "33405-33430", "33460-33468", "0483T") + TS.TAVR_PCS + TS.SAVR_PCS + TS.MITRAL_SURG,
    dx=R("Z952-Z954"), win=ALL, ps=["valve_disease"])
add("prior_laao_ever", D, "left atrial appendage occlusion CPT 33340, PCS 02L73DK, any prior history", px=["33340", "02L73DK"], win=ALL)
add("dialysis_365", D, "dialysis: Z99.2, Z49.x, or CPT 90935-90947, 90951-90970, 90989-90999, PCS 5A1D in 365 d",
    dx=["Z992", "Z49"], px=R("90935-90947", "90951-90970", "90989-90999", "5A1D"), ps=["ckd"])
add("mech_ventilation_365", D, "mechanical ventilation PCS 5A193-5A195 or CPT 94002-94004, 94656-94657 in 365 d",
    px=["5A193", "5A194", "5A195"] + R("94002-94004", "94656-94657"))
add("transfusion_365", D, "RBC transfusion CPT 36430 or PCS 30233N1/30243N1 in 365 d", px=["36430", "30233N1", "30243N1"])
add("stress_test_365", D, "stress test / MPI / stress echo CPT 93015-93018, 78451-78454, 78491-78492, 93350-93351 in 365 d",
    px=R("93015-93018", "78451-78454", "78491-78492", "93350-93351"))
add("ambulatory_ecg_monitor_365", D, "Holter / event / patch monitor CPT 93224-93248, 93268-93272, 0295T-0298T in 365 d",
    px=R("93224-93248", "93268-93272", "0295T", "0296T", "0297T", "0298T"))
add("cardiac_ct_mri_365", D, "cardiac CT/CTA/calcium score CPT 75571-75574 or cardiac MRI 75557-75565 in 365 d", px=R("75557-75565", "75571-75574"))
add("tee_365", D, "TEE CPT 93312-93318, 93355 in 365 d", px=R("93312-93318", "93355"))
add("major_surgery_anesthesia_365", D, "any anesthesia service CPT 00100-01999 in 365 d (proxy for surgery)", px=R("00100-01999"))

# ---- preventive care / healthy-user markers ---------------------------------------------------------------------
P = "preventive"
add("flu_vaccine_365", P, "influenza vaccine CPT 90630, 90653-90689, 90756, G0008 or order token (influenza, fluzone, flublok, afluria, fluad, "
    "flucelvax, fluarix, flulaval) in 365 d", px=["90630", "90756", "G0008"] + R("90653-90689"),
    rx=["influenza", "fluzone", "flublok", "afluria", "fluad", "flucelvax", "fluarix", "flulaval"])
add("pneumococcal_vaccine_ever", P, "pneumococcal vaccine CPT 90670, 90671, 90677, 90732, G0009 or token (pneumococcal, prevnar, pneumovax, "
    "vaxneuvance, capvaxive), any prior history", px=["90670", "90671", "90677", "90732", "G0009"],
    rx=["pneumococcal", "prevnar", "pneumovax", "vaxneuvance", "capvaxive"], win=ALL)
add("covid_vaccine_ever", P, "COVID-19 vaccine CPT 91300-91322, 0001A-0164A (prefix 91 3x) or tokens (moderna, pfizer, spikevax, comirnaty, "
    "novavax, covid), any prior history", px=R("91300-91322"), rx=["spikevax", "comirnaty", "novavax", "covid"], win=ALL)
add("colonoscopy_10y", P, "colonoscopy CPT 45378-45398, G0105, G0121 in 3650 d", px=R("45378-45398", "G0105", "G0121"), win=3650)
add("mammogram_2y", P, "mammography CPT 77065-77067, 77055-77057, G0202 in 730 d", px=R("77065-77067", "77055-77057", "G0202"), win=730)
add("annual_wellness_visit_365", P, "Medicare AWV / preventive visit G0438, G0439, G0402, 99381-99397 in 365 d",
    px=R("G0438", "G0439", "G0402", "99381-99397"))
add("lipid_panel_measured_365", P, "any total cholesterol/LDL/HDL result in 365 d", source="OMOP measurement")  # computed from labs

# ---- medication classes (365 d, ever ordered) -------------------------------------------------------------------
M = "medication"
MED = {
    "oral_anticoagulant": (TS.ANTICOAG + ["jantoven", "bevyxxa"], ["anticoag_order"]),
    "parenteral_anticoagulant": (["enoxaparin", "lovenox", "fondaparinux", "arixtra", "dalteparin", "fragmin"], []),
    "aspirin": (["aspirin", "ecotrin", "aggrenox", "bayer"], ["aspirin_order"]),
    "p2y12_inhibitor": (TS.P2Y12 + ["ticlopidine", "cangrelor", "kengreal"], ["p2y12_order"]),
    "statin": (TS.STATIN + ["pravachol", "mevacor", "lescol", "livalo", "zypitamag", "vytorin", "caduet", "altoprev", "ezallor", "flolipid"],
               ["statin_order"]),
    "other_lipid_lowering": (["ezetimibe", "zetia", "fenofibrate", "tricor", "trilipix", "lipofen", "fenoglide", "gemfibrozil", "lopid", "niacin",
                              "niaspan", "icosapent", "vascepa", "lovaza", "evolocumab", "repatha", "alirocumab", "praluent", "inclisiran",
                              "leqvio", "bempedoic", "nexletol", "nexlizet", "colesevelam", "welchol", "cholestyramine", "colestipol",
                              "vytorin", "roszet"], []),
    "acei": (TS.ACEI + ["lotensin", "vaseretic", "zestoretic", "lotrel", "tarka", "enalaprilat"],
             ["ace_inhibitor_order", "acei_order", "acei_arb_order", "acei_arb_arni_order"]),
    "arb": (TS.ARB + ["cozaar", "hyzaar", "diovan", "micardis", "benicar", "avapro", "avalide", "atacand", "edarbi", "edarbyclor", "exforge",
                      "azor", "tribenzor", "twynsta", "teveten"], ["arb_order", "acei_arb_order", "acei_arb_arni_order"]),
    "arni": (["sacubitril", "entresto"], ["arni_order", "acei_arb_arni_order"]),
    "beta_blocker": (TS.BETA_BLOCKER + ["tenormin", "bystolic", "zebeta", "ziac", "inderal", "innopran", "corgard", "trandate", "kapspargo",
                                        "acebutolol", "pindolol", "betaxolol", "tenoretic"],
                     ["beta_blocker_order", "other_beta_blocker_order"]),
    "mra": (TS.MRA + ["aldactone", "carospir", "inspra", "kerendia", "aldactazide"], ["mra_order"]),
    "loop_diuretic": (TS.LOOP + ["demadex", "soaanz", "edecrin"], ["loop_diuretic_order"]),
    "thiazide": (TS.THIAZIDE + ["metolazone", "zaroxolyn", "chlorothiazide", "diuril", "hyzaar", "zestoretic", "vaseretic", "avalide",
                                "edarbyclor", "tribenzor", "ziac", "tenoretic", "aldactazide", "dyazide", "maxzide"], ["thiazide_order"]),
    "sglt2_inhibitor": (TS.SGLT2_ALL + ["brenzavvy", "inpefa", "steglatro"], ["sglt2_inhibitor_order", "sglt2_order"]),
    "glp1_ra": (["liraglutide", "victoza", "saxenda", "semaglutide", "ozempic", "wegovy", "rybelsus", "dulaglutide", "trulicity", "exenatide",
                 "byetta", "bydureon", "lixisenatide", "adlyxin", "tirzepatide", "mounjaro", "zepbound", "soliqua", "xultophy", "albiglutide",
                 "tanzeum"], ["glp1ra_order"]),
    "insulin": (TS.INSULIN + ["toujeo", "humulin", "novolin", "admelog", "apidra", "fiasp", "lyumjev", "semglee", "ryzodeg", "afrezza",
                              "rezvoglar", "soliqua", "xultophy", "glargine", "lispro", "aspart", "detemir", "degludec"], ["insulin_order"]),
    "metformin": (["metformin", "glucophage", "glumetza", "fortamet", "riomet", "janumet", "jentadueto", "kombiglyze", "invokamet", "synjardy",
                   "xigduo", "segluromet", "trijardy", "kazano", "actoplus", "glucovance"], ["metformin_order"]),
    "sulfonylurea": (["glipizide", "glucotrol", "glyburide", "glimepiride", "amaryl", "glynase", "micronase", "diabeta", "glucovance",
                      "duetact", "tolbutamide", "chlorpropamide"], ["sulfonylurea_order"]),
    "dpp4_inhibitor": (TS.DPP4I + ["steglujan", "oseni"], []),
    "tzd": (["pioglitazone", "actos", "rosiglitazone", "avandia", "actoplus", "duetact", "oseni"], []),
    "ccb_dhp": (["amlodipine", "norvasc", "katerzia", "nifedipine", "procardia", "adalat", "felodipine", "plendil", "isradipine", "nicardipine",
                 "cardene", "nisoldipine", "sular", "exforge", "azor", "lotrel", "twynsta", "caduet", "tribenzor", "clevidipine", "levamlodipine",
                 "conjupri", "nimodipine", "prestalia"], ["ccb_order"]),
    "ccb_nondhp": (TS.CCB_RATE + ["cardizem", "calan", "tiazac", "cartia", "taztia", "matzim", "dilt", "verelan", "tarka"],
                   ["rate_ccb_order", "ccb_order"]),
    "nitrate": (["nitroglycerin", "isosorbide", "imdur", "nitrostat", "nitro", "ismo", "isordil", "monoket", "nitrolingual", "nitromist",
                 "bidil"], []),
    "ranolazine": (["ranolazine", "ranexa", "aspruzyo"], []),
    "hydralazine": (["hydralazine", "bidil"], []),
    "other_antihypertensive": (["clonidine", "catapres", "kapvay", "doxazosin", "cardura", "terazosin", "prazosin", "minipress", "minoxidil",
                                "methyldopa", "guanfacine", "aliskiren", "tekturna"], []),
    "antiarrhythmic": (TS.ANTIARRHYTHMIC + ["pacerone", "nexterone", "multaq", "betapace", "sorine", "sotylize", "tambocor", "rythmol",
                                            "tikosyn", "mexiletine", "disopyramide", "norpace", "quinidine"],
                       ["antiarrhythmic_order", "amiodarone_order"]),
    "digoxin": (["digoxin", "lanoxin", "digitek"], ["digoxin_order"]),
    "other_hf_drug": (["ivabradine", "corlanor", "vericiguat", "verquvo"], []),
    "other_glucose_lowering": (["repaglinide", "prandin", "nateglinide", "starlix", "acarbose", "precose", "miglitol", "glyset"], []),
    "potassium_binder": (["patiromer", "veltassa", "lokelma", "kayexalate", "polystyrene"], []),
    "potassium_supplement": (["potassium", "klor", "kcl"], []),
    "ppi": (TS.PPI + ["aciphex", "dexilant", "prevacid", "zegerid"], ["ppi_order"]),
    "h2_blocker": (["famotidine", "pepcid", "ranitidine", "zantac", "cimetidine", "nizatidine"], []),
    "nsaid": (TS.NSAID + ["naprosyn", "aleve", "anaprox", "advil", "motrin", "mobic", "toradol", "celebrex", "etodolac", "nabumetone",
                          "ketoprofen", "piroxicam", "sulindac", "oxaprozin", "voltaren", "flurbiprofen", "diflunisal", "salsalate"],
              ["nsaid_order"]),
    "opioid": (["oxycodone", "hydrocodone", "morphine", "hydromorphone", "dilaudid", "fentanyl", "tramadol", "ultram", "codeine", "tapentadol",
                "nucynta", "methadone", "buprenorphine", "suboxone", "percocet", "norco", "vicodin", "oxycontin", "oxymorphone", "meperidine",
                "demerol", "roxicodone", "kadian", "butrans", "belbuca", "sublocade", "zubsolv"], []),
    "systemic_corticosteroid": (["prednisone", "prednisolone", "methylprednisolone", "medrol", "solu", "dexamethasone", "decadron",
                                 "hydrocortisone", "cortisone", "fludrocortisone", "deltasone", "orapred", "millipred"], []),
    "inhaled_respiratory": (["albuterol", "proair", "ventolin", "proventil", "levalbuterol", "xopenex", "tiotropium", "spiriva", "salmeterol",
                             "advair", "symbicort", "budesonide", "formoterol", "ipratropium", "atrovent", "duoneb", "combivent", "breo",
                             "trelegy", "anoro", "umeclidinium", "incruse", "stiolto", "wixela", "dulera", "arnuity", "flovent", "qvar",
                             "pulmicort", "breztri", "bevespi", "montelukast", "singulair", "roflumilast", "daliresp"], []),
    "antidepressant": (["sertraline", "zoloft", "fluoxetine", "prozac", "citalopram", "celexa", "escitalopram", "lexapro", "paroxetine", "paxil",
                        "venlafaxine", "effexor", "duloxetine", "cymbalta", "desvenlafaxine", "pristiq", "bupropion", "wellbutrin",
                        "mirtazapine", "remeron", "trazodone", "amitriptyline", "nortriptyline", "pamelor", "doxepin", "imipramine",
                        "vortioxetine", "trintellix", "vilazodone", "viibryd", "fluvoxamine", "clomipramine", "desipramine"], []),
    "antipsychotic": (["quetiapine", "seroquel", "olanzapine", "zyprexa", "risperidone", "risperdal", "haloperidol", "haldol", "aripiprazole",
                       "abilify", "ziprasidone", "geodon", "lurasidone", "latuda", "clozapine", "clozaril", "paliperidone", "invega",
                       "chlorpromazine", "brexpiprazole", "rexulti", "cariprazine", "vraylar", "perphenazine", "fluphenazine", "lithium"], []),
    "benzodiazepine": (["lorazepam", "ativan", "alprazolam", "xanax", "clonazepam", "klonopin", "diazepam", "valium", "temazepam", "restoril",
                        "chlordiazepoxide", "librium", "oxazepam", "clorazepate"], []),
    "z_drug_hypnotic": (["zolpidem", "ambien", "eszopiclone", "lunesta", "zaleplon", "suvorexant", "belsomra", "lemborexant", "dayvigo"], []),
    "gabapentinoid": (["gabapentin", "neurontin", "gralise", "horizant", "pregabalin", "lyrica"], []),
    "antiepileptic_other": (["levetiracetam", "keppra", "lamotrigine", "lamictal", "topiramate", "topamax", "valproate", "valproic", "divalproex",
                             "depakote", "carbamazepine", "tegretol", "oxcarbazepine", "trileptal", "phenytoin", "dilantin", "lacosamide",
                             "vimpat", "zonisamide", "phenobarbital"], []),
    "thyroid_replacement": (["levothyroxine", "synthroid", "levoxyl", "unithroid", "euthyrox", "tirosint", "liothyronine", "cytomel", "armour",
                             ], []),
    "antithyroid": (["methimazole", "tapazole", "propylthiouracil"], []),
    "gout_urate": (["allopurinol", "zyloprim", "febuxostat", "uloric", "colchicine", "colcrys", "mitigare", "probenecid", "gloperba"], []),
    "osteoporosis_drug": (["alendronate", "fosamax", "risedronate", "actonel", "atelvia", "ibandronate", "boniva", "zoledronic", "reclast",
                           "denosumab", "prolia", "teriparatide", "forteo", "abaloparatide", "romosozumab", "raloxifene", "evista"], []),
    "dementia_drug": (["donepezil", "aricept", "memantine", "namenda", "namzaric", "rivastigmine", "exelon", "galantamine", "razadyne"], []),
    "parkinson_drug": (["carbidopa", "levodopa", "sinemet", "rytary", "pramipexole", "mirapex", "ropinirole", "requip", "rasagiline", "azilect",
                        "selegiline", "entacapone", "amantadine"], []),
    "iron_esa": (["ferrous", "iron", "venofer", "injectafer", "feraheme", "ferrlecit", "infed", "monoferric", "epoetin", "procrit", "epogen",
                  "retacrit", "darbepoetin", "aranesp", "mircera"], []),
    "immunosuppressant": (["tacrolimus", "prograf", "envarsus", "cyclosporine", "neoral", "sandimmune", "mycophenolate", "cellcept", "myfortic",
                           "azathioprine", "imuran", "methotrexate", "sirolimus", "everolimus", "leflunomide", "hydroxychloroquine",
                           "plaquenil"], []),
    "pulm_htn_pde5": (["sildenafil", "revatio", "viagra", "tadalafil", "adcirca", "cialis", "bosentan", "tracleer", "ambrisentan", "letairis",
                       "macitentan", "opsumit", "riociguat", "adempas", "treprostinil", "tyvaso", "remodulin", "orenitram", "epoprostenol",
                       "selexipag", "uptravi"], []),
    "alpha_blocker_bph": (["tamsulosin", "flomax", "alfuzosin", "uroxatral", "silodosin", "rapaflo", "finasteride", "proscar", "dutasteride",
                           "avodart", "jalyn"], []),
    "anticholinergic_bladder": (["oxybutynin", "ditropan", "tolterodine", "detrol", "solifenacin", "vesicare", "trospium", "darifenacin",
                                 "fesoterodine", "toviaz", "mirabegron", "myrbetriq"], []),
    "smoking_cessation": (["varenicline", "chantix", "nicotine", "nicoderm", "nicorette", "nicotrol", "habitrol"], []),
    "antibiotic_any": (["amoxicillin", "augmentin", "azithromycin", "zithromax", "cephalexin", "keflex", "ciprofloxacin", "cipro",
                        "levofloxacin", "levaquin", "doxycycline", "sulfamethoxazole", "bactrim", "nitrofurantoin", "macrobid",
                        "clindamycin", "cefdinir", "ceftriaxone", "rocephin", "vancomycin", "piperacillin", "zosyn", "cefazolin",
                        "metronidazole", "flagyl", "cefuroxime", "cefepime", "meropenem", "penicillin", "ampicillin", "linezolid"], []),
    "oncology_systemic": (["tamoxifen", "anastrozole", "arimidex", "letrozole", "femara", "exemestane", "leuprolide", "lupron", "eligard",
                           "enzalutamide", "xtandi", "abiraterone", "zytiga", "bicalutamide", "capecitabine", "carboplatin", "cisplatin",
                           "paclitaxel", "docetaxel", "pembrolizumab", "keytruda", "nivolumab", "opdivo", "ibrutinib", "imbruvica",
                           "lenalidomide", "revlimid", "rituximab", "trastuzumab", "herceptin", "bortezomib", "cyclophosphamide",
                           "doxorubicin", "gemcitabine", "fluorouracil", "oxaliplatin", "osimertinib", "palbociclib"], []),
    "sedating_antihistamine": (["hydroxyzine", "atarax", "vistaril", "diphenhydramine", "benadryl", "promethazine", "phenergan", "meclizine",
                                "antivert"], []),
    "muscle_relaxant": (["cyclobenzaprine", "flexeril", "methocarbamol", "robaxin", "tizanidine", "zanaflex", "baclofen", "carisoprodol",
                         "soma", "metaxalone"], []),
}
for k, (toks, ps) in MED.items():
    add(f"rx_{k}_365", M, f"any order of class '{k}' in 365 d; tokens: {', '.join(sorted(set(t.lower() for t in toks)))}", rx=toks, ps=ps)
VARS["lipid_panel_measured_365"]["domain"] = "preventive"

# ---- labs / vitals (latest in 365 d; + _missing flag) ----------------------------------------------------------
# name: (concept_id, low, high, unit note, scale)
LABS = {
    "total_cholesterol": (3027114, 50, 700, "mg/dL", 1), "hdl": (3007070, 5, 200, "mg/dL", 1), "triglycerides": (3022192, 10, 5000, "mg/dL", 1),
    "non_hdl": (3044491, 20, 600, "mg/dL", 1), "chol_hdl_ratio": (3011163, 0.5, 30, "ratio", 1),
    "alt": (3006923, 1, 3000, "U/L", 1), "ast": (3013721, 1, 3000, "U/L", 1), "alk_phos": (3035995, 10, 3000, "U/L", 1),
    "bilirubin_total": (3024128, 0.05, 40, "mg/dL", 1), "bilirubin_direct": (3027597, 0.0, 30, "mg/dL", 1),
    "total_protein": (3020630, 2, 15, "g/dL; source PROT only (LABPROT under this concept is prothrombin time)", 1, "PROT"), "globulin": (3027970, 0.5, 10, "g/dL", 1),
    "inr": (3022217, 0.5, 15, "ratio", 1), "ptt": (3018677, 10, 200, "s", 1), "tsh": (3009201, 0.001, 150, "mIU/L", 1),
    "free_t4": (3008598, 0.05, 10, "ng/dL", 1), "uric_acid": (3037556, 0.5, 25, "mg/dL", 1), "calcium": (3006906, 4, 16, "mg/dL", 1),
    "chloride": (3014576, 60, 150, "mmol/L", 1), "bicarbonate": (3015632, 5, 50, "mmol/L", 1), "anion_gap": (3037278, -5, 50, "mmol/L", 1),
    "bun_creatinine_ratio": (3018311, 1, 100, "ratio", 1),
    "crp": (3020460, 0.01, 600, "mg/L", 1), "hs_crp": (3010156, 0.01, 600, "mg/L (as reported)", 1),
    "bnp": (3011960, 1, 50000, "pg/mL", 1), "troponin_i": (3021337, 0.0, 1000, "ng/mL (as reported)", 1),
    "troponin_hs": (40769783, 0.0, 100000, "ng/L (as reported)", 1),
    "hematocrit": (3023314, 10, 70, "%", 1), "rdw": (3019897, 8, 40, "%", 1), "mcv": (3023599, 50, 140, "fL", 1),
    "neutrophils_abs": (3013650, 0.0, 100, "10^3/uL", 1), "lymphocytes_abs": (3004327, 0.0, 100, "10^3/uL", 1),
    "lipoprotein_a": (3013861, 0.0, 1000, "as reported", 1), "osmolality": (3008295, 200, 400, "mOsm/kg", 1),
    "spo2": (40762499, 50, 100, "%", 1), "resp_rate": (3024171, 4, 60, "/min", 1), "temperature": (3020891, 90, 110, "F", 1),
    "weight_kg": (3025315, 30, 300, "kg (source oz x 0.0283495)", 0.0283495), "height_cm": (3036277, 120, 220, "cm (source in x 2.54)", 2.54),
}
VITAL_CONCEPTS = {4152194, 3012888, 3027018, 40762499, 3024171, 3020891, 3025315, 4245997, 3036277}
L = "lab_vital"
WARF = ["warfarin", "coumadin", "jantoven"]
for k, t in LABS.items():
    cid, lo, hi, unit = t[:4]
    add(f"lab_{k}", L, f"latest value in 365 d (concept {cid}; {unit}; plausible {lo}-{hi}); NaN if none", typ="num", source="OMOP measurement",
        rx=WARF if k == "inr" else None)
    add(f"lab_{k}_missing", L, f"no plausible {k} value in 365 d", source="OMOP measurement", rx=WARF if k == "inr" else None)
VARS["lab_inr"]["definition"] += " (reflects prior warfarin; dropped where warfarin defines exposure)"
add("weight_change_pct_365", L, "100 x (latest - earliest weight) / earliest, weights in 365 d at least 90 d apart; NaN otherwise", typ="num",
    source="OMOP measurement")
add("weight_change_missing", L, "weight_change_pct_365 not computable", source="OMOP measurement")
add("weight_loss_5pct_365", L, "weight_change_pct_365 <= -5", source="OMOP measurement")
add("ldl_lt70", L, "latest LDL (concept 3028288) in 365 d < 70 mg/dL (0 if missing)", source="OMOP measurement")
add("hba1c_ge9", L, "latest HbA1c (3004410) in 365 d >= 9% (0 if missing)", source="OMOP measurement")
add("hb_lt10", L, "latest haemoglobin (3000963) in 365 d < 10 g/dL (0 if missing)", source="OMOP measurement")
add("egfr_lt30", L, "latest CKD-EPI eGFR (40764999) in 365 d < 30 (0 if missing)", source="OMOP measurement")
add("sbp_mean_365", L, "mean of all systolic BP readings in 365 d", typ="num", source="OMOP measurement")
add("sbp_sd_365", L, "SD of systolic BP readings in 365 d (>= 3 readings)", typ="num", source="OMOP measurement")
add("n_bp_readings_365", L, "number of systolic BP readings in 365 d", typ="num", source="OMOP measurement")

# ---- healthcare use / testing intensity (365 d) ---------------------------------------------------------------
U = "utilisation"
for k, d in {"n_outpatient_days_365": "distinct dates with an outpatient (9202) visit",
             "n_office_visits_365": "outpatient visits with source Office Visit / Follow Up / Initial consult / Evaluation / Walk-In",
             "n_telemedicine_365": "outpatient visits with source Telemedicine",
             "n_anticoag_clinic_365": "outpatient visits with source 'Anti-coag visit' (dropped where anticoagulants define exposure)",
             "n_infusion_visits_365": "outpatient visits with source Infusion",
             "n_ed_days_365": "distinct dates with an ED (9203) visit",
             "n_inpatient_stays_365": "inpatient (9201) visits starting in 365 d",
             "n_ecg_days_365": "distinct dates with ECG CPT 93000/93005/93010 (index day excluded)",
             "n_echo_days_365": "distinct dates with echo CPT 93303-93308, 93350-93351, 93312-93318",
             "n_venipuncture_days_365": "distinct dates with CPT 36415",
             "n_lab_results_365": "number of lab results (OMOP measurement, vitals excluded)",
             "n_lab_days_365": "distinct dates with any lab result",
             "n_distinct_lab_tests_365": "distinct lab concepts measured",
             "n_distinct_procedures_365": "distinct procedure source codes",
             "n_distinct_dx_365": "distinct ICD-10 codes (condition_occurrence + observation)",
             "days_since_last_visit": "days from the latest visit (any type, start <= index-1) to index; NaN if none",
             "ehr_history_days": "days from the first recorded visit to index; NaN if none"}.items():
    add(k, U, d + ("" if k.startswith(("days", "ehr")) else " in 365 d"), typ="num", source="OMOP visit/procedure/measurement/condition",
        rx=TS.ANTICOAG if k == "n_anticoag_clinic_365" else None)
VARS["n_ed_days_365"]["ps"] = ["ed_encounters"]
VARS["n_inpatient_stays_365"]["ps"] = ["hospital_admissions"]
VARS["n_outpatient_days_365"]["ps"] = ["outpatient_visits"]
for k in ("n_anticoag_clinic_365",):
    VARS[k]["source"] = "OMOP visit_occurrence"
add("no_prior_visit", U, "no visit before index (days_since_last_visit missing)", source="OMOP visit_occurrence")
EPIC_DEPTS = {"cardiology": r"CARDIO|HEART|\bEP\b|ELECTROPHYS|VALVE CLINIC|ARRHYTHM|VASCULAR MED",
              "cardiac_rehab": r"CARDIAC REHAB", "nephrology": r"NEPHRO|RENAL|DIALYSIS|KIDNEY",
              "oncology_hematology": r"ONCOL|HEMATOL|HEM ONC|HEME ONC|SMILOW|CANCER|RADIATION",
              "endocrinology": r"ENDOCRIN|DIABETES", "pulmonology": r"PULMON|CHEST|SLEEP|LUNG",
              "neurology": r"NEUROL|STROKE", "primary_care": r"PRIMARY CARE|INTERNAL MED|FAMILY MED|ADULT MED|GERIATR|COMMUNITY HEALTH",
              "behavioral_health": r"PSYCH|BEHAV|ADDICTION|MENTAL"}
EPIC_EXCL = {"cardiology": r"REHAB|PEDI|THORACIC|SURG", "pulmonology": r"PEDI|REHAB"}
for k in EPIC_DEPTS:
    add(f"n_{k}_visits_365", U, f"distinct dates with an Epic outpatient encounter in a department matching /{EPIC_DEPTS[k]}/"
        + (f" (excluding /{EPIC_EXCL[k]}/)" if k in EPIC_EXCL else "") + " in 365 d", typ="num", source="Epic outpatient_enc (2025 + 2026 deliveries)")
add("n_distinct_outpatient_providers_365", U, "distinct VISIT_PROV_ID (Physician/NP/PA/Fellow/Resident) on Epic outpatient encounters in 365 d",
    typ="num", source="Epic outpatient_enc")
add("n_distinct_depts_365", U, "distinct Epic outpatient departments visited in 365 d", typ="num", source="Epic outpatient_enc")
for k, (rx_, d) in {"disch_snf_365": ("Skilled Nursing|Nursing Facility|Intermediate Care|Long Term Care", "skilled nursing / long-term care"),
                    "disch_rehab_365": ("Rehab", "inpatient rehabilitation"), "disch_home_health_365": ("Home-Health", "home health care"),
                    "disch_hospice_365": ("Hospice", "hospice"), "left_ama_365": ("Against Medical Advice|Eloped|Left without", "left AMA / eloped / LWBS")}.items():
    VARS[k] = dict(name=k, domain=U, type="bin", definition=f"Epic hospital encounter admitted >= index-365 and discharged <= index-1 with "
                   f"disposition {d} (/{rx_}/)", source="Epic hosp_enc (DISCH_DISP)", dx=[], dxx=[], px=[], rx=[], win=365, ps=[], _re=rx_)
add("icu_stay_365", U, "Epic hospital encounter (admitted >= index-365, discharged <= index-1) with a first/second/last department name "
    "containing ICU / CCU / CRITICAL CARE", source="Epic hosp_enc")
add("observation_stay_365", U, "Epic hospital encounter of class Observation (discharged <= index-1) in 365 d", source="Epic hosp_enc")

# ---- scores ----------------------------------------------------------------------------------------------------
S_ = "score"
add("charlson_score", S_, "Charlson/Deyo weights on Quan 2005 ICD-10 components (hierarchies: severe>mild liver, complicated>uncomplicated DM, "
    "metastatic>malignancy); no age points", typ="num")
add("charlson_age_score", S_, "charlson_score + age points (50-59 1, 60-69 2, 70-79 3, >=80 4; age from v1.1 baseline)", typ="num")
add("elixhauser_count", S_, "number of 31 Elixhauser components (hierarchies: complicated>uncomplicated DM and HTN, metastatic>solid tumour)", typ="num")
add("elixhauser_vw", S_, "van Walraven (2009) weighted Elixhauser score", typ="num")
add("hfrs_365", S_, "Hospital Frailty Risk Score (Gilbert 2018): sum of weights of 109 3-character ICD-10 codes recorded in 365 d "
    "(original uses 2 y of inpatient codes; here all settings, 365 d)", typ="num")
add("hfrs_ge5", S_, "hfrs_365 >= 5 (intermediate/high frailty risk)")
add("cha2ds2vasc", S_, "CHF (cci_chf) + HTN (I10-I16) + 2 x age>=75 + DM (E08-E13) + 2 x stroke/TIA/thromboembolism (I63, I64, G45, I74, "
    "Z86.73; I60-I64/I69 ever) + vascular (prior MI ever, I70, I73.9) + age 65-74 + female; age/sex from v1.1 baseline", typ="num")
add("cha2ds2vasc_ge2", S_, "cha2ds2vasc >= 2 (men) / >= 3 (women)")
add("hasbled_nodrug", S_, "HAS-BLED without the drug item and without labile INR: HTN dx + abnormal renal (dialysis, Z94.0, N18.6 or latest "
    "creatinine >= 2.26 mg/dL) + abnormal liver (cirrhosis or bilirubin > 2.4 with AST/ALT > 120) + stroke ever + bleeding 365 d (bleed_any_365) "
    "+ age > 65 + alcohol (F10)", typ="num")
add("hasbled", S_, "hasbled_nodrug + 1 if any aspirin / P2Y12 / NSAID order in 365 d (dropped where these define exposure)", typ="num",
    rx=MED["aspirin"][0] + MED["p2y12_inhibitor"][0] + MED["nsaid"][0])
add("n_med_classes_365", S_, "number of medication classes (rx_*_365, excluding antibiotic_any) with any order in 365 d, counting only classes "
    "retained for the trial (exposure classes removed)", typ="num")
add("polypharmacy_ge5", S_, "n_med_classes_365 >= 5")
add("n_distinct_drugs_365", S_, "distinct drug tokens (first-word order names) ordered in 365 d, excluding the trial's exposure tokens and all "
    "tokens of removed classes", typ="num", source="OMOP drug_exposure tokens")

# ---- additions from docs/v16/lit_covariates.json (literature list) --------------------------------------------
add("other_dysrhythmia", C, "I49.1-I49.9 (premature beats, SSS, other) in 365 d [lit #33]", dx=R("I491-I499"))
add("hypotension", C, "I95 in 365 d [lit #41]", dx=["I95"])
add("pad_broad", C, "atherosclerosis of extremities I70.2-I70.7, I73.9, arterial embolism of extremities I74.2-I74.4, lower-limb amputation "
    "status Z89.4-Z89.6 or peripheral endovascular revascularisation CPT 37220-37235 in 365 d [lit #47]",
    dx=R("I702-I707", "I739", "I742-I744", "Z894-Z896"), px=R("37220-37235"), ps=["peripheral_arterial_disease"])
add("aortic_disease", C, "aortic atherosclerosis I70.0 or aneurysm/dissection I71 in 365 d [lit #48]", dx=["I700", "I71"])
add("acs_365", C, "I20.0, I21-I24 in 365 d [lit #29]", dx=["I200", "I21", "I22", "I23", "I24"], ps=["ischemic_heart_disease_or_mi"])
add("ckd_stage3", C, "N18.3x in 365 d [lit #59]", dx=["N183"], ps=["ckd"])
add("chronic_resp_failure_o2", C, "chronic respiratory failure J96.1x, oxygen dependence Z99.81 or oxygen concentrator E1390 in 365 d [lit #71]",
    dx=["J961", "Z9981"], px=["E1390"])
add("chronic_skin_ulcer", C, "L97, L98.4 (non-pressure chronic ulcer) in 365 d [lit #87]", dx=["L97", "L984"])
add("fracture_hip_spine_rib", C, "S72, S22, S32 in 365 d [lit #89]", dx=["S72", "S22", "S32"])
add("dme_mobility_365", D, "DME HCPCS canes/walkers E0100-E0159, hospital beds E0250-E0304, wheelchairs E1130-E1161 in 365 d [lit #155]",
    px=R("E0100-E0159", "E0250-E0304", "E1130-E1161"))
add("psa_test_2y", P, "PSA CPT 84152-84154, G0103 in 730 d [lit #153]", px=R("84152-84154", "G0103"), win=730)
add("dxa_2y", P, "bone densitometry CPT 77080-77081, 77085 in 730 d [lit #153]", px=["77080", "77081", "77085"], win=730)
add("recent_hosp_30d", U, "inpatient (9201) visit starting in [index-30, index-1] [lit #142]", source="OMOP visit_occurrence")
add("n_hf_hosp_365", U, "number of inpatient (9201) visits starting >= index-365 and ending <= index-1 with an I50 code dated within the visit "
    "[lit #26]", typ="num", source="OMOP visit_occurrence + condition_occurrence")
add("index_month", "calendar", "calendar month of the index date (1-12) [lit #6]", typ="num", source="cohort index_date")
add("index_winter", "calendar", "index date in December-February [lit #6]", source="cohort index_date")
for k, pat in {"ynh": "^YNH", "bh": "^BH", "src": "^SRC", "gh": "^GH", "lmh": "^LMH", "wh": "^WH"}.items():
    VARS[f"campus_{k}_365"] = dict(name=f"campus_{k}_365", domain=U, type="bin", definition=f"any Epic hospital encounter in 365 d (admitted "
        f">= index-365, discharged <= index-1) at a hospital area matching /{pat}/ (YNH / SRC = Yale New Haven York St / Saint Raphael "
        f"campuses; BH Bridgeport; GH Greenwich; LMH Lawrence+Memorial; WH Westerly) [lit #8]", source="Epic hosp_enc (HOSPITAL_AREA_NAME)",
        dx=[], dxx=[], px=[], rx=[], win=365, ps=[], _re=pat)
add("chads2", S_, "CHF + HTN + age>=75 + DM + 2 x stroke/TIA (definitions as cha2ds2vasc) [lit #52]", typ="num")
add("gagne_ccs", S_, "Gagne 2011 combined comorbidity score from Elixhauser/Charlson components (metastatic 5; CHF, dementia, renal, weight "
    "loss 2; hemiplegia, alcohol, any tumour, arrhythmia, CPD, coagulopathy, complicated DM, deficiency anaemia, fluid/electrolyte, liver, "
    "PVD, psychosis, pulmonary circulation 1; HIV -1; hypertension -1); 365 d [lit #97]", typ="num")
add("dcsi_domains", S_, "diabetes-complication domain count (DCSI-like, unweighted, 0 if no diabetes code in 365 d): retinopathy (E08-E13 .3, "
    "H36), nephropathy (E08-E13 .2, N18), neuropathy (E08-E13 .4, G63.2), cerebrovascular (I60-I69, G45), cardiovascular (I20-I25, I50), "
    "peripheral vascular (E08-E13 .5, I70-I73), metabolic (E08-E13 .0/.1); complications from any prior history [lit #56]", typ="num")
DCSI = {"retino": [f"E{d}3" for d in ("08", "09", "10", "11", "13")] + ["H36"],
        "nephro": [f"E{d}2" for d in ("08", "09", "10", "11", "13")] + ["N18"],
        "neuro": [f"E{d}4" for d in ("08", "09", "10", "11", "13")] + ["G632"],
        "cerebro": R("I60-I69", "G45"), "cardio": R("I20-I25", "I50"),
        "pvd": [f"E{d}5" for d in ("08", "09", "10", "11", "13")] + R("I70-I73"),
        "metab": [f"E{d}{s}" for d in ("08", "09", "10", "11", "13") for s in "01"]}
MEDVAR = {f"rx_{k}_365" for k in MED}
TOKCOUNT = {}
for _k, (_toks, _) in MED.items():
    for _t in {t.lower() for t in _toks}:
        TOKCOUNT[_t] = TOKCOUNT.get(_t, 0) + 1


# literature list (docs/v16/lit_covariates.json) name -> covars2 variables covering it ("" = not built here)
LITMAP = {
    "index_month": "index_month, index_winter", "prior_observation_days": "ehr_history_days", "care_site_campus": "campus_*_365",
    "insurance_type": "", "low_income_or_dual": "", "area_deprivation_index": "",
    "social_vulnerability_index": "", "zip_median_income": "", "preferred_language_non_english": "", "marital_or_lives_alone": "",
    "smoking_current": "tobacco_counseling_or_history, rx_smoking_cessation_365", "smoking_ever": "tobacco_counseling_or_history",
    "alcohol_use_disorder": "alcohol_use_disorder, elx_alcohol", "drug_use_disorder": "drug_use_disorder_any, opioid_use_disorder, elx_drug_abuse",
    "obesity_dx": "elx_obesity, obesity_class1_2_bmi30_39, obesity_class3, overweight", "heart_failure": "hf_any_365, cci_chf, elx_chf",
    "hf_subtype_code": "hf_systolic, hf_diastolic, hf_unspecified_only", "prior_hf_hospitalization": "n_hf_hosp_365",
    "n_hf_hospitalizations": "n_hf_hosp_365", "ischemic_heart_disease": "angina_any, acs_365, cci_mi", "prior_mi": "prior_mi_ever, cci_mi",
    "acs_unstable_angina": "acs_365, unstable_angina", "prior_pci": "prior_pci_ever, prior_pci_365", "prior_cabg": "prior_cabg_ever",
    "atrial_fibrillation_flutter": "atrial_flutter, af_persistent_permanent, elx_arrhythmia", "other_dysrhythmia": "other_dysrhythmia, svt",
    "ventricular_arrhythmia_arrest": "ventricular_arrhythmia_ever, cardiac_arrest_ever",
    "conduction_disorder": "conduction_disease_any, av_block, bundle_branch_block, long_qt_wpw_other_conduction",
    "cardiac_device": "pacemaker_ever, icd_ever, crt_ever, cied_any_ever, loop_recorder_ever", "valve_disease": "elx_valvular, aortic_stenosis, mitral_regurgitation",
    "prior_valve_procedure": "prior_valve_procedure_ever", "cardiomyopathy": "cardiomyopathy_any, cm_*", "hypertension": "elx_htn_uncomplicated, elx_htn_complicated",
    "hypotension": "hypotension", "pulmonary_hypertension": "pulmonary_hypertension, elx_pulm_circ", "hyperlipidemia": "",
    "ischemic_stroke": "ischemic_stroke_365, stroke_tia_history_ever", "intracranial_hemorrhage": "hemorrhagic_stroke_ever, intracranial_bleed_ever",
    "tia": "stroke_tia_history_ever, cci_cvd", "peripheral_arterial_disease": "pad_broad, cci_pvd", "aortic_disease": "aortic_disease, aortic_aneurysm",
    "vte_history": "vte_history_ever, vte_365", "cha2ds2_vasc": "cha2ds2vasc, cha2ds2vasc_ge2", "has_bled_modified": "hasbled, hasbled_nodrug",
    "chads2": "chads2", "diabetes_any": "cci_dm_*, elx_dm_*", "t2d": "", "t1d": "type1_diabetes",
    "diabetes_complications_dcsi": "dcsi_domains, dm_retinopathy, dm_neuropathy, dm_nephropathy", "hypoglycemia": "hypoglycemia",
    "ckd_any": "cci_renal, elx_renal", "ckd_stage": "ckd_stage3, ckd_stage4_5, esrd", "eskd_dialysis_transplant": "esrd, dialysis_365, kidney_transplant",
    "acute_kidney_injury": "aki_365", "hyperkalemia": "hyperkalemia", "fluid_electrolyte_disorder": "elx_fluid_electrolyte, hyponatremia",
    "hypothyroidism": "hypothyroidism, elx_hypothyroid", "hyperthyroidism": "hyperthyroidism", "gout": "gout", "obstructive_sleep_apnea": "sleep_apnea",
    "copd": "copd, cci_cpd", "asthma": "asthma", "pneumonia_recent": "pneumonia_365", "chronic_respiratory_failure_o2": "chronic_resp_failure_o2, home_oxygen",
    "liver_disease": "elx_liver, cci_mild_liver, cci_severe_liver, cirrhosis", "gi_bleed": "gi_bleed_365", "major_bleed_other": "bleed_any_365",
    "anemia": "anemia, iron_deficiency, elx_deficiency_anemia", "coagulopathy_thrombocytopenia": "elx_coagulopathy, thrombocytopenia",
    "peptic_ulcer_disease": "cci_pud, elx_pud", "dementia": "dementia, cci_dementia", "depression": "depression, elx_depression",
    "anxiety": "anxiety", "serious_mental_illness": "serious_mental_illness, elx_psychoses", "parkinsonism": "parkinsonism",
    "hemiplegia_paralysis": "hemiplegia_paralysis, cci_hemiplegia", "falls": "falls", "gait_mobility_weakness": "gait_abnormality, weakness_debility",
    "malnutrition_weight_loss": "malnutrition, cachexia_weight_loss, elx_weight_loss", "pressure_ulcer": "pressure_ulcer, chronic_skin_ulcer",
    "urinary_incontinence": "incontinence", "osteoporosis_fracture": "osteoporosis, hip_fracture, fracture_hip_spine_rib",
    "cancer_any": "cancer_365, cancer_history_ever", "metastatic_cancer": "metastatic_365", "cancer_therapy_recent": "cancer_treatment_365",
    "rheumatologic_disease": "elx_rheum, cci_rheum, rheumatoid_arthritis, lupus", "hiv": "hiv", "charlson_index": "charlson_score, charlson_age_score",
    "elixhauser_index": "elixhauser_count, elixhauser_vw", "combined_comorbidity_score": "gagne_ccs", "claims_frailty_index_kim": "",
    "hospital_frailty_risk_score": "hfrs_365, hfrs_ge5", "cardiovascular_risk_equation": "",
    "acei": "rx_acei_365", "arb": "rx_arb_365", "arni": "rx_arni_365", "beta_blocker": "rx_beta_blocker_365", "mra": "rx_mra_365",
    "loop_diuretic": "rx_loop_diuretic_365", "thiazide": "rx_thiazide_365", "ccb_dhp": "rx_ccb_dhp_365", "ccb_nondhp": "rx_ccb_nondhp_365",
    "other_antihypertensive": "rx_other_antihypertensive_365, rx_hydralazine_365", "nitrate": "rx_nitrate_365", "digoxin": "rx_digoxin_365",
    "antiarrhythmic": "rx_antiarrhythmic_365", "other_hf_drugs": "rx_other_hf_drug_365", "statin": "rx_statin_365",
    "nonstatin_lipid": "rx_other_lipid_lowering_365", "aspirin": "rx_aspirin_365", "p2y12": "rx_p2y12_inhibitor_365",
    "oral_anticoagulant": "rx_oral_anticoagulant_365", "metformin": "rx_metformin_365", "sulfonylurea": "rx_sulfonylurea_365",
    "dpp4i": "rx_dpp4_inhibitor_365", "glp1ra": "rx_glp1_ra_365", "sglt2i": "rx_sglt2_inhibitor_365", "insulin": "rx_insulin_365",
    "other_glucose_lowering": "rx_other_glucose_lowering_365, rx_tzd_365", "nsaid": "rx_nsaid_365", "ppi": "rx_ppi_365",
    "oral_corticosteroid": "rx_systemic_corticosteroid_365", "opioid": "rx_opioid_365", "antidepressant": "rx_antidepressant_365",
    "antipsychotic": "rx_antipsychotic_365", "benzodiazepine_hypnotic": "rx_benzodiazepine_365, rx_z_drug_hypnotic_365",
    "cns_other": "rx_gabapentinoid_365, rx_antiepileptic_other_365, rx_dementia_drug_365, rx_parkinson_drug_365",
    "copd_asthma_inhaler": "rx_inhaled_respiratory_365", "thyroid_hormone": "rx_thyroid_replacement_365",
    "potassium_supplement_binder": "rx_potassium_supplement_365, rx_potassium_binder_365", "urate_lowering": "rx_gout_urate_365",
    "n_distinct_drug_ingredients": "n_distinct_drugs_365, n_med_classes_365", "n_inpatient_admissions": "n_inpatient_stays_365",
    "inpatient_days": "", "recent_hospitalization_30d": "recent_hosp_30d", "n_ed_visits": "n_ed_days_365", "n_outpatient_visits": "n_outpatient_days_365, n_office_visits_365",
    "n_cardiology_visits": "n_cardiology_visits_365", "n_pcp_visits": "n_primary_care_visits_365",
    "other_specialist_visits": "n_nephrology/oncology_hematology/endocrinology/pulmonology/neurology/behavioral_health_visits_365",
    "n_ecgs": "n_ecg_days_365", "n_echos": "n_echo_days_365, tee_365", "ischemia_testing_or_cath": "stress_test_365, cardiac_ct_mri_365, prior_cath_ever",
    "lab_test_intensity": "n_lab_results_365, n_lab_days_365, n_distinct_lab_tests_365, n_venipuncture_days_365",
    "influenza_vaccination": "flu_vaccine_365", "cancer_screening": "colonoscopy_10y, mammogram_2y, psa_test_2y, dxa_2y",
    "discharge_to_facility_or_home_health": "disch_snf_365, disch_rehab_365, disch_home_health_365, disch_hospice_365",
    "durable_medical_equipment": "dme_mobility_365", "sbp": "sbp_mean_365, sbp_sd_365", "spo2": "lab_spo2", "weight_change": "weight_change_pct_365, weight_loss_5pct_365",
    "egfr": "egfr_lt30", "hemoglobin": "hb_lt10, lab_hematocrit", "hba1c": "hba1c_ge9", "ldl_c": "ldl_lt70",
    "hdl_tc_tg": "lab_total_cholesterol, lab_hdl, lab_triglycerides, lab_non_hdl, lab_chol_hdl_ratio", "natriuretic_peptide": "lab_bnp",
    "troponin": "lab_troponin_i, lab_troponin_hs", "liver_panel": "lab_alt, lab_ast, lab_alk_phos, lab_bilirubin_total, lab_bilirubin_direct",
    "inr": "lab_inr", "tsh": "lab_tsh, lab_free_t4", "crp": "lab_crp, lab_hs_crp", "uacr": "", "lipoprotein_a": "lab_lipoprotein_a (365 d)",
    "bicarbonate_chloride_calcium": "lab_bicarbonate, lab_chloride, lab_calcium, lab_anion_gap", "magnesium": "",
    "lab_measured_flags": "lab_*_missing, lipid_panel_measured_365", "nyha_class": "", "empirical_hdps_codes": "",
    "area_ses_other": "zip_out_of_state", "other_arrhythmia": "other_dysrhythmia, svt, ventricular_arrhythmia_ever, cardiac_arrest_ever",
    "thyroid_disease": "hypothyroidism, hyperthyroidism, elx_hypothyroid", "antipsychotic_or_hypnotic": "rx_antipsychotic_365, rx_benzodiazepine_365, rx_z_drug_hypnotic_365",
    "index_setting_inpatient": "index_setting_inpatient, index_setting_ed, index_setting_outpatient (index-day)",
}
LIT_REASON = {
    "index_setting_inpatient": "index-day characteristic (setting of initiation): not pre-index, tagged domain index_context",
    "insurance_type": "no payer field in extract", "low_income_or_dual": "no payer field in extract",
    "area_deprivation_index": "needs external ADI file", "social_vulnerability_index": "needs external SVI file",
    "zip_median_income": "needs external ACS file", "preferred_language_non_english": "no language field in extract",
    "marital_or_lives_alone": "no social-history table", "claims_frailty_index_kim": "full Kim CFI needs DME/CPT weights; HFRS + covars v1 frailty_count used instead",
    "cardiovascular_risk_equation": "PCE needs cholesterol+SBP+treatment inputs; components provided (lab_total_cholesterol, lab_hdl, sbp_mean_365)",
    "uacr": "not in gold measurement or Epic lab extracts", "magnesium": "not in gold measurement or Epic lab extracts",
    "nyha_class": "notes NLP only (2021+)", "empirical_hdps_codes": "PS-only construct", "hyperlipidemia": "in covars v1",
    "t2d": "in covars v1", "inpatient_days": "in covars v1 (inpatient_days_365)",
}


add("index_setting_inpatient", "index_context", "INDEX-DAY (not pre-index): an inpatient (9201) visit spans the index date (start <= index <= end); "
    "setting of initiation [lit #9, coordinator request]", source="OMOP visit_occurrence")
add("index_setting_ed", "index_context", "INDEX-DAY: ED (9203) visit on the index date and no spanning inpatient visit", source="OMOP visit_occurrence")
add("index_setting_outpatient", "index_context", "INDEX-DAY: neither inpatient nor ED on the index date", source="OMOP visit_occurrence")
ECG_PROXIMAL = {
    "elx_arrhythmia", "atrial_flutter", "af_persistent_permanent", "svt", "other_dysrhythmia", "sick_sinus_brady", "av_block",
    "bundle_branch_block", "long_qt_wpw_other_conduction", "conduction_disease_any", "ventricular_arrhythmia_ever",
    "ventricular_arrhythmia_365", "cardiac_arrest_ever", "syncope", "cardiomyopathy_any", "cm_dilated", "cm_hypertrophic", "cm_ischemic",
    "cm_other_restrictive", "cardiac_amyloidosis", "takotsubo", "myocarditis_pericarditis", "pacemaker_ever", "icd_ever", "crt_ever",
    "cied_any_ever", "loop_recorder_ever", "prior_af_ablation_ever", "prior_ablation_any_ever", "prior_cardioversion_ever",
    "ambulatory_ecg_monitor_365", "n_ecg_days_365", "rx_beta_blocker_365", "rx_ccb_nondhp_365", "rx_digoxin_365", "rx_antiarrhythmic_365",
    "rx_other_hf_drug_365", "elx_chf", "cci_chf", "hf_any_365", "hf_systolic", "hf_diastolic", "hf_unspecified_only", "lvad_or_heart_tx_ever",
    "hyperkalemia", "cha2ds2vasc", "cha2ds2vasc_ge2", "chads2"}

# ---- social ----------------------------------------------------------------------------------------------------
add("zip_out_of_state", "social", "current Epic ZIP does not start with 06 (Connecticut); current address, not at index", source="Epic patients (ZIP)")
add("zip_missing", "social", "no ZIP in Epic patient table (or unlinked)", source="Epic patients (ZIP)")


# ---------------------------------------------------------------------------------------------------------------
def load_lit():
    """Optional literature list (docs/v16/lit_covariates.json): returns list of names for the coverage table."""
    if not LIT.exists():
        return None
    try:
        return json.load(open(LIT))
    except Exception:
        return None


def build_all(con, rosters):
    con.register("r0", rosters[["trial", "patient_key", "person_id", "index_date"]])
    con.execute("""CREATE TEMP TABLE r AS SELECT trial, patient_key, CAST(person_id AS BIGINT) person_id,
                   CAST(index_date AS DATE) idx FROM r0""")
    con.execute("CREATE TEMP TABLE pp AS SELECT DISTINCT person_id FROM r")
    K = ["trial", "patient_key"]
    base = rosters[K].copy().reset_index(drop=True)
    feats = {}  # name -> Series indexed by (trial, patient_key)

    def put(df, col, name=None, fill=None):
        s = df.set_index(K)[col]
        feats[name or col] = s

    # ---------- diagnoses ----------
    print("dx ...", flush=True)
    con.execute(f"""CREATE TEMP TABLE codes_all AS
        SELECT DISTINCT person_id, d, code FROM (
            SELECT person_id, condition_start_date d, upper(replace(condition_source_value, '.', '')) code
              FROM {rp(GOLD, 'condition_occurrence')} WHERE person_id IN (SELECT person_id FROM pp)
            UNION ALL
            SELECT person_id, observation_date d, upper(replace(observation_source_value, '.', '')) code
              FROM {rp(GOLD, 'observation')} WHERE person_id IN (SELECT person_id FROM pp))
        WHERE code IS NOT NULL AND d IS NOT NULL""")
    ucodes = con.execute("SELECT DISTINCT code FROM codes_all").df().code.tolist()
    rows = []
    dxvars = [v for v in VARS.values() if v["dx"]]
    for v in dxvars:
        inc, exc = tuple(v["dx"]), tuple(v["dxx"])
        for c in ucodes:
            if c.startswith(inc) and not (exc and c.startswith(exc)):
                rows.append((c, v["name"], int(v["win"])))
    for c in ucodes:
        if c[:3] in HFRS:
            rows.append((c, f"hfrs__{c[:3]}", 365))
    for k, pre in DCSI.items():
        rows += [(c, f"_dcsi_{k}", ALL) for c in ucodes if c.startswith(tuple(pre))]
    con.register("dxmap0", pd.DataFrame(rows, columns=["code", "var", "win"]))
    con.execute("CREATE TEMP TABLE dxmap AS SELECT * FROM dxmap0")
    dxf = con.execute("""SELECT DISTINCT r.trial, r.patient_key, m.var FROM r JOIN codes_all c USING (person_id)
        JOIN dxmap m ON m.code = c.code WHERE c.d < r.idx AND c.d >= r.idx - CAST(m.win AS INTEGER)""").df()
    # counts of distinct dx codes in 365 d
    nd = con.execute("""SELECT r.trial, r.patient_key, count(DISTINCT c.code) n FROM r JOIN codes_all c USING (person_id)
        WHERE c.d < r.idx AND c.d >= r.idx - 365 GROUP BY 1, 2""").df()
    put(nd, "n", "n_distinct_dx_365")
    hfh = con.execute(f"""SELECT r.trial, r.patient_key, count(DISTINCT v.visit_occurrence_id) n FROM r
        JOIN (SELECT person_id, visit_occurrence_id, visit_start_date s, coalesce(visit_end_date, visit_start_date) e
              FROM {rp(GOLD, 'visit_occurrence')} WHERE visit_concept_id = 9201 AND person_id IN (SELECT person_id FROM pp)) v
          ON v.person_id = r.person_id AND v.s >= r.idx - 365 AND v.e < r.idx
        JOIN (SELECT DISTINCT person_id, d FROM codes_all WHERE code LIKE 'I50%') c ON c.person_id = r.person_id AND c.d BETWEEN v.s AND v.e
        GROUP BY 1, 2""").df()
    put(hfh, "n", "n_hf_hosp_365")
    con.execute("DROP TABLE codes_all")

    # ---------- procedures ----------
    print("px ...", flush=True)
    con.execute(f"""CREATE TEMP TABLE proc_all AS SELECT DISTINCT person_id, procedure_date d, upper(trim(procedure_source_value)) code
        FROM {rp(GOLD, 'procedure_occurrence')} WHERE person_id IN (SELECT person_id FROM pp)
        AND procedure_source_value IS NOT NULL AND procedure_date IS NOT NULL""")
    ucodes = con.execute("SELECT DISTINCT code FROM proc_all").df().code.tolist()
    rows = []
    for v in VARS.values():
        if v["px"]:
            inc = tuple(p.upper() for p in v["px"])
            rows += [(c, v["name"], int(v["win"])) for c in ucodes if c.startswith(inc)]
    UTILPX = {"n_ecg_days_365": ["93000", "93005", "93010"], "n_echo_days_365": R("93303-93308", "93350-93351", "93312-93318"),
              "n_venipuncture_days_365": ["36415"]}
    for k, cs in UTILPX.items():
        rows += [(c, k, 365) for c in ucodes if c in set(cs)]
    con.register("pxmap0", pd.DataFrame(rows, columns=["code", "var", "win"]))
    con.execute("CREATE TEMP TABLE pxmap AS SELECT * FROM pxmap0")
    pxf = con.execute("""SELECT DISTINCT r.trial, r.patient_key, m.var FROM r JOIN proc_all c USING (person_id)
        JOIN pxmap m ON m.code = c.code WHERE c.d < r.idx AND c.d >= r.idx - CAST(m.win AS INTEGER) AND m.var NOT IN
        ('n_ecg_days_365', 'n_echo_days_365', 'n_venipuncture_days_365')""").df()
    pu = con.execute("""SELECT r.trial, r.patient_key, m.var, count(DISTINCT c.d) n FROM r JOIN proc_all c USING (person_id)
        JOIN pxmap m ON m.code = c.code WHERE c.d < r.idx AND c.d >= r.idx - 365 AND m.var IN
        ('n_ecg_days_365', 'n_echo_days_365', 'n_venipuncture_days_365') GROUP BY 1, 2, 3""").df()
    for k in UTILPX:
        put(pu[pu["var"] == k], "n", k)
    npx = con.execute("""SELECT r.trial, r.patient_key, count(DISTINCT c.code) n FROM r JOIN proc_all c USING (person_id)
        WHERE c.d < r.idx AND c.d >= r.idx - 365 GROUP BY 1, 2""").df()
    put(npx, "n", "n_distinct_procedures_365")
    con.execute("DROP TABLE proc_all")

    # ---------- drug tokens ----------
    print("rx ...", flush=True)
    con.execute(f"""CREATE TEMP TABLE tok365 AS SELECT DISTINCT r.trial, r.patient_key, t.tok, (t.d >= r.idx - 365) in365 FROM r JOIN (
            SELECT DISTINCT person_id, drug_exposure_start_date d, unnest(string_split(lower(drug_source_value), '-')) tok
            FROM {rp(GOLD, 'drug_exposure')} WHERE drug_source_value IS NOT NULL AND drug_exposure_start_date IS NOT NULL
              AND person_id IN (SELECT person_id FROM pp)) t USING (person_id)
        WHERE t.d < r.idx AND trim(t.tok) <> ''""")
    rows = []
    for v in VARS.values():
        if v["rx"] and (v["domain"] in ("medication", "preventive")):
            rows += [(t, v["name"], int(v["win"])) for t in v["rx"]]
    con.register("rxmap0", pd.DataFrame(rows, columns=["tok", "var", "win"]))
    rxf = con.execute("""SELECT DISTINCT t.trial, t.patient_key, m.var FROM tok365 t JOIN rxmap0 m ON m.tok = t.tok
        WHERE t.in365 OR m.win > 365""").df()
    toks = con.execute("SELECT DISTINCT trial, patient_key, tok FROM tok365 WHERE in365").df()
    con.execute("DROP TABLE tok365")

    flags = pd.concat([dxf, pxf, rxf], ignore_index=True).drop_duplicates()
    flags["one"] = 1.0
    W = flags.pivot_table(index=K, columns="var", values="one", aggfunc="max")
    for c in W.columns:
        feats[c] = W[c]

    # ---------- measurements ----------
    print("labs ...", flush=True)
    lab_rows = [(cid, k, lo, hi, sc, (t[5] if len(t) > 5 else None)) for k, t in LABS.items() for cid, lo, hi, _, sc in [t[:5]]]
    extra = {"ldl": (3028288, 5, 500, 1), "hba1c": (3004410, 3, 20, 1), "hgb": (3000963, 3, 25, 1), "egfr": (40764999, 1, 200, 1),
             "creat": (3016723, 0.1, 25, 1)}
    lab_rows += [(cid, f"_{k}", lo, hi, sc, None) for k, (cid, lo, hi, sc) in extra.items()]
    con.register("lb0", pd.DataFrame(lab_rows, columns=["cid", "name", "lo", "hi", "sc", "src"]))
    con.execute(f"""CREATE TEMP TABLE mw AS SELECT r.trial, r.patient_key, m.cid, m.d, m.dt, m.v, m.src FROM r JOIN (
            SELECT person_id, measurement_concept_id cid, measurement_date d,
                   coalesce(measurement_datetime, CAST(measurement_date AS TIMESTAMP)) dt, value_as_number v, measurement_source_value src
            FROM {rp(GOLD, 'measurement')} WHERE person_id IN (SELECT person_id FROM pp) AND measurement_date IS NOT NULL) m
        USING (person_id) WHERE m.d < r.idx AND m.d >= r.idx - 365""")
    lat = con.execute("""SELECT w.trial, w.patient_key, l.name, arg_max(w.v * l.sc, w.dt) val FROM mw w JOIN lb0 l ON l.cid = w.cid
        WHERE w.v * l.sc BETWEEN l.lo AND l.hi AND (l.src IS NULL OR w.src = l.src) GROUP BY 1, 2, 3""").df()
    LW = lat.pivot_table(index=K, columns="name", values="val", aggfunc="first")
    for k in LABS:
        feats[f"lab_{k}"] = LW[k] if k in LW else pd.Series(dtype=float)
    for k in extra:
        feats[f"_{k}"] = LW[f"_{k}"] if f"_{k}" in LW else pd.Series(dtype=float)
    wt = con.execute("""WITH w AS (SELECT trial, patient_key, d, dt, v * 0.0283495 kg FROM mw WHERE cid = 3025315
                        AND v * 0.0283495 BETWEEN 30 AND 300)
        SELECT trial, patient_key, arg_min(kg, dt) w0, min(d) d0, arg_max(kg, dt) w1, max(d) d1 FROM w GROUP BY 1, 2""").df()
    wt["chg"] = np.where((pd.to_datetime(wt.d1) - pd.to_datetime(wt.d0)).dt.days >= 90, 100 * (wt.w1 - wt.w0) / wt.w0, np.nan)
    put(wt, "chg", "weight_change_pct_365")
    bp = con.execute("""SELECT trial, patient_key, avg(v) m, CASE WHEN count(*) >= 3 THEN stddev_samp(v) END s, count(*) n FROM mw
        WHERE cid = 4152194 AND v BETWEEN 50 AND 300 GROUP BY 1, 2""").df()
    put(bp, "m", "sbp_mean_365")
    put(bp, "s", "sbp_sd_365")
    put(bp, "n", "n_bp_readings_365")
    vit = ",".join(str(c) for c in VITAL_CONCEPTS)
    lc = con.execute(f"""SELECT trial, patient_key, count(*) n, count(DISTINCT d) nd, count(DISTINCT cid) nc FROM mw
        WHERE cid NOT IN ({vit}) GROUP BY 1, 2""").df()
    put(lc, "n", "n_lab_results_365")
    put(lc, "nd", "n_lab_days_365")
    put(lc, "nc", "n_distinct_lab_tests_365")
    lp = con.execute("""SELECT DISTINCT trial, patient_key, 1.0 f FROM mw WHERE cid IN (3027114, 3028288, 3007070) AND v IS NOT NULL""").df()
    put(lp, "f", "lipid_panel_measured_365")
    con.execute("DROP TABLE mw")

    # ---------- visits ----------
    print("visits ...", flush=True)
    vis = con.execute(f"""SELECT r.trial, r.patient_key,
            count(DISTINCT CASE WHEN v.visit_concept_id = 9202 AND v.s >= r.idx - 365 THEN v.s END) n_outpatient_days_365,
            count(CASE WHEN v.src IN ('Office Visit', 'Follow Up', 'Initial consult', 'Evaluation', 'Walk-In') AND v.s >= r.idx - 365 THEN 1 END) n_office_visits_365,
            count(CASE WHEN v.src = 'Telemedicine' AND v.s >= r.idx - 365 THEN 1 END) n_telemedicine_365,
            count(CASE WHEN v.src = 'Anti-coag visit' AND v.s >= r.idx - 365 THEN 1 END) n_anticoag_clinic_365,
            count(CASE WHEN v.src = 'Infusion' AND v.s >= r.idx - 365 THEN 1 END) n_infusion_visits_365,
            count(DISTINCT CASE WHEN v.visit_concept_id = 9203 AND v.s >= r.idx - 365 THEN v.s END) n_ed_days_365,
            count(CASE WHEN v.visit_concept_id = 9201 AND v.s >= r.idx - 365 THEN 1 END) n_inpatient_stays_365,
            CAST(count(CASE WHEN v.visit_concept_id = 9201 AND v.s >= r.idx - 30 THEN 1 END) > 0 AS DOUBLE) recent_hosp_30d,
            date_diff('day', max(v.s), r.idx) days_since_last_visit, date_diff('day', min(v.s), r.idx) ehr_history_days
        FROM r JOIN (SELECT person_id, visit_concept_id, visit_start_date s, visit_source_value src FROM {rp(GOLD, 'visit_occurrence')}
                     WHERE person_id IN (SELECT person_id FROM pp)) v USING (person_id)
        WHERE v.s < r.idx GROUP BY r.trial, r.patient_key, r.idx""").df()
    for c in vis.columns[2:]:
        put(vis, c)
    ixs = con.execute(f"""SELECT r.trial, r.patient_key,
            max(CASE WHEN v.visit_concept_id = 9201 AND v.s <= r.idx AND v.e >= r.idx THEN 1 ELSE 0 END) inp,
            max(CASE WHEN v.visit_concept_id = 9203 AND v.s = r.idx THEN 1 ELSE 0 END) ed
        FROM r JOIN (SELECT person_id, visit_concept_id, visit_start_date s, coalesce(visit_end_date, visit_start_date) e
                     FROM {rp(GOLD, 'visit_occurrence')} WHERE person_id IN (SELECT person_id FROM pp) AND visit_concept_id IN (9201, 9203)) v
          USING (person_id) WHERE v.s <= r.idx AND v.e >= r.idx - 1 GROUP BY 1, 2""").df()
    ixs["index_setting_inpatient"] = ixs.inp.astype(float)
    ixs["index_setting_ed"] = ((ixs.ed == 1) & (ixs.inp == 0)).astype(float)
    put(ixs, "index_setting_inpatient")
    put(ixs, "index_setting_ed")

    # ---------- Epic encounters / patients (MRN linkage) ----------
    print("epic ...", flush=True)
    con.execute(f"""CREATE TEMP TABLE rk AS SELECT r.*, p.k FROM r JOIN (SELECT person_id, {mrn_key('person_source_value')} k
        FROM {rp(GOLD, 'person')} WHERE person_id IN (SELECT person_id FROM pp)) p USING (person_id)""")
    oe = f"""(SELECT DISTINCT ON (PAT_ENC_CSN_ID) {mrn_key('PAT_MRN_ID')} k, PAT_ENC_CSN_ID csn, __day_CONTACT_DATE d,
                upper(coalesce(DEPARTMENT_NAME, '')) dept, VISIT_PROV_ID prov, VISIT_PROV_TYPE ptype
             FROM read_parquet(['{SNAP}/Data_2026_04_15_outpatient_enc/*.parquet', '{SNAP}/Data_2025_04_03_outpatient_enc/*.parquet'],
                               union_by_name=1) WHERE __day_CONTACT_DATE IS NOT NULL)"""
    con.execute(f"""CREATE TEMP TABLE ow AS SELECT rk.trial, rk.patient_key, o.d, o.dept, o.prov, o.ptype FROM rk JOIN {oe} o ON o.k = rk.k
        WHERE o.d < rk.idx AND o.d >= rk.idx - 365""")
    ow = con.execute("SELECT trial, patient_key, d, dept, prov, ptype FROM ow").df()
    con.execute("DROP TABLE ow")
    for k, pat in EPIC_DEPTS.items():
        m = ow.dept.str.contains(pat, regex=True)
        if k in EPIC_EXCL:
            m &= ~ow.dept.str.contains(EPIC_EXCL[k], regex=True)
        g = ow[m].groupby(K).d.nunique().rename("n").reset_index()
        put(g, "n", f"n_{k}_visits_365")
    pv = ow[ow.ptype.isin(["Physician", "Nurse Practitioner", "Physician Assistant", "Fellow", "Resident"]) & ow.prov.notna()]
    put(pv.groupby(K).prov.nunique().rename("n").reset_index(), "n", "n_distinct_outpatient_providers_365")
    put(ow[ow.dept != ""].groupby(K).dept.nunique().rename("n").reset_index(), "n", "n_distinct_depts_365")
    del ow
    he = f"""(SELECT DISTINCT ON (PAT_ENC_CSN_ID) {mrn_key('PAT_MRN_ID')} k, __day_HOSP_ADMSN_DATE a, __day_HOSP_DISCH_DATE e,
                coalesce(DISCH_DISP, '') disp, coalesce(ADT_PAT_CLASS, '') cls, upper(coalesce(HOSPITAL_AREA_NAME, '')) area,
                upper(coalesce(FIRST_DEPARTMENT_NAME, '') || '|' || coalesce(SECOND_DEPARTMENT_NAME, '') || '|' || coalesce(LAST_DEPARTMENT_NAME, '')) depts
             FROM read_parquet(['{SNAP}/Data_2026_04_15_hosp_enc/*.parquet', '{SNAP}/Data_2025_04_03_hosp_enc/*.parquet'], union_by_name=1)
             WHERE __day_HOSP_DISCH_DATE IS NOT NULL)"""
    hw = con.execute(f"""SELECT rk.trial, rk.patient_key, h.disp, h.cls, h.depts, h.area FROM rk JOIN {he} h ON h.k = rk.k
        WHERE h.a >= rk.idx - 365 AND h.e < rk.idx""").df()
    for k in ("disch_snf_365", "disch_rehab_365", "disch_home_health_365", "disch_hospice_365", "left_ama_365"):
        g = hw[hw.disp.str.contains(VARS[k]["_re"], regex=True)][K].drop_duplicates().assign(f=1.0)
        put(g, "f", k)
    g = hw[hw.depts.str.contains(r"(?<![NP])ICU\b|\bCCU\b|CRITICAL CARE", regex=True)][K].drop_duplicates().assign(f=1.0)
    put(g, "f", "icu_stay_365")
    for k in [v for v in VARS if v.startswith("campus_")]:
        put(hw[hw.area.str.contains(VARS[k]["_re"], regex=True)][K].drop_duplicates().assign(f=1.0), "f", k)
    g = hw[hw.cls.str.contains("Observation")][K].drop_duplicates().assign(f=1.0)
    put(g, "f", "observation_stay_365")
    zp = con.execute(f"""SELECT rk.trial, rk.patient_key, any_value(q.ZIP) zip FROM rk LEFT JOIN
        (SELECT {mrn_key('PAT_MRN_ID')} k, ZIP FROM read_parquet('{SNAP}/Data_2025_04_03_patients/*.parquet')) q ON q.k = rk.k GROUP BY 1, 2""").df()
    z = zp.zip.fillna("").astype(str).str.strip()
    zp["zip_missing"] = (z == "").astype(float)
    zp["zip_out_of_state"] = ((z != "") & ~z.str.startswith("06")).astype(float)
    put(zp, "zip_missing")
    put(zp, "zip_out_of_state")

    F = pd.DataFrame(feats)
    F.index.names = K
    base = base.merge(F.reset_index(), on=K, how="left")
    return base, toks


def finalize_trial(n, d, roles, obs, toks_n, index_date):
    """Per-trial derivation: fill zeros, scores, exposure exclusion. Returns (frame, status rows)."""
    expo = {e.lower()[3:] if e.lower().startswith("rx_") else e.lower() for e in roles.get("exposure_features", [])}
    core = set(roles["core"])
    status = {}
    # binary flags: missing -> 0 ; count vars -> 0 ; lab values stay NaN
    for v in VARS.values():
        c = v["name"]
        if c not in d:
            d[c] = np.nan
        if v["type"] == "bin" and not c.endswith("_missing"):
            d[c] = d[c].fillna(0.0)
    for c in [v["name"] for v in VARS.values() if v["type"] == "num" and v["name"].startswith("n_")]:
        d[c] = d[c].fillna(0.0)
    for k in LABS:
        d[f"lab_{k}_missing"] = d[f"lab_{k}"].isna().astype(float)
    d["weight_change_missing"] = d["weight_change_pct_365"].isna().astype(float)
    d["weight_loss_5pct_365"] = (d["weight_change_pct_365"] <= -5).astype(float)
    d["ldl_lt70"] = (d["_ldl"] < 70).astype(float)
    d["hba1c_ge9"] = (d["_hba1c"] >= 9).astype(float)
    d["hb_lt10"] = (d["_hgb"] < 10).astype(float)
    d["egfr_lt30"] = (d["_egfr"] < 30).astype(float)
    d["no_prior_visit"] = d["days_since_last_visit"].isna().astype(float)
    d["days_since_last_visit"] = d["days_since_last_visit"].astype(float)
    d["ehr_history_days"] = d["ehr_history_days"].astype(float)
    g = lambda c: d.get(c, pd.Series(0.0, index=d.index)).fillna(0.0)
    # Charlson
    comp = {k: g(k).copy() for k in CCI}
    comp["cci_mild_liver"] = comp["cci_mild_liver"] * (1 - comp["cci_severe_liver"])
    comp["cci_dm_uncomplicated"] = comp["cci_dm_uncomplicated"] * (1 - comp["cci_dm_complicated"])
    comp["cci_malignancy"] = comp["cci_malignancy"] * (1 - comp["cci_metastatic"])
    d["charlson_score"] = sum(comp[k] * CCI[k][1] for k in CCI)
    age = obs["age_at_index"].reindex(d.index).astype(float) if "age_at_index" in obs else pd.Series(np.nan, index=d.index)
    male = obs["male"].reindex(d.index).astype(float) if "male" in obs else pd.Series(np.nan, index=d.index)
    agep = np.select([age >= 80, age >= 70, age >= 60, age >= 50], [4, 3, 2, 1], 0).astype(float)
    d["charlson_age_score"] = np.where(age.isna(), np.nan, d["charlson_score"] + agep)
    ecomp = {k: g(k).copy() for k in ELX}
    ecomp["elx_dm_uncomplicated"] *= (1 - ecomp["elx_dm_complicated"])
    ecomp["elx_htn_uncomplicated"] *= (1 - ecomp["elx_htn_complicated"])
    ecomp["elx_solid_tumor"] *= (1 - ecomp["elx_metastatic"])
    htn_any = ((ecomp["elx_htn_uncomplicated"] + ecomp["elx_htn_complicated"]) > 0).astype(float)
    d["elixhauser_count"] = sum(ecomp[k] for k in ELX if not k.startswith("elx_htn")) + htn_any
    d["elixhauser_vw"] = sum(ecomp[k] * ELX[k][1] for k in ELX)
    hf = [c for c in d.columns if c.startswith("hfrs__")]
    d["hfrs_365"] = sum(g(c) * HFRS[c[6:]] for c in hf) if hf else 0.0
    d["hfrs_ge5"] = (d["hfrs_365"] >= 5).astype(float)
    d.drop(columns=hf, inplace=True)
    # CHA2DS2-VASc (HTN from elixhauser HTN codes I10-I13, I15 plus I16 not separately coded)
    dm = ((g("cci_dm_uncomplicated") + g("cci_dm_complicated") + g("elx_dm_uncomplicated") + g("elx_dm_complicated")) > 0).astype(float)
    stroke = ((g("ischemic_stroke_365") + g("stroke_tia_history_ever") + g("systemic_embolism")) > 0).astype(float)
    vasc = ((g("prior_mi_ever") + g("cci_pvd")) > 0).astype(float)
    a75, a65 = (age >= 75).astype(float), ((age >= 65) & (age < 75)).astype(float)
    d["cha2ds2vasc"] = np.where(age.isna() | male.isna(), np.nan, g("cci_chf") + htn_any + 2 * a75 + dm + 2 * stroke + vasc + a65 + (1 - male))
    d["cha2ds2vasc_ge2"] = np.where(male == 1, d["cha2ds2vasc"] >= 2, d["cha2ds2vasc"] >= 3).astype(float)
    creat = obs["creatinine"].reindex(d.index).astype(float) if "creatinine" in obs else pd.Series(np.nan, index=d.index)
    creat = creat.fillna(d["_creat"])
    renal = ((g("dialysis_365") + g("kidney_transplant") + g("esrd") + (creat >= 2.26).astype(float)) > 0).astype(float)
    liver = ((g("cirrhosis") + ((d["lab_bilirubin_total"] > 2.4) & ((d["lab_ast"] > 120) | (d["lab_alt"] > 120))).astype(float)) > 0).astype(float)
    d["hasbled_nodrug"] = np.where(age.isna(), np.nan, htn_any + renal + liver + g("stroke_tia_history_ever").clip(0, 1) + g("bleed_any_365")
                                   + (age > 65).astype(float) + g("alcohol_use_disorder"))
    drug = ((g("rx_aspirin_365") + g("rx_p2y12_inhibitor_365") + g("rx_nsaid_365")) > 0).astype(float)
    d["hasbled"] = d["hasbled_nodrug"] + drug
    d["chads2"] = np.where(age.isna(), np.nan, g("cci_chf") + htn_any + a75 + dm + 2 * stroke)
    tumour = ((g("cci_malignancy") + g("elx_lymphoma") + g("elx_solid_tumor")) > 0).astype(float)
    d["gagne_ccs"] = (5 * g("elx_metastatic") + 2 * (g("elx_chf") + g("cci_dementia") + g("elx_renal") + g("elx_weight_loss"))
                      + g("elx_paralysis") + g("elx_alcohol") + tumour + g("elx_arrhythmia") + g("elx_cpd") + g("elx_coagulopathy")
                      + ecomp["elx_dm_complicated"] + g("elx_deficiency_anemia") + g("elx_fluid_electrolyte") + g("elx_liver") + g("elx_pvd")
                      + g("elx_psychoses") + g("elx_pulm_circ") - g("elx_hiv") - htn_any)
    d["dcsi_domains"] = dm * sum(g(f"_dcsi_{k}") for k in DCSI)
    ix = pd.to_datetime(index_date.reindex(d.index))
    d["index_month"] = ix.dt.month.astype(float)
    d["index_winter"] = ix.dt.month.isin([12, 1, 2]).astype(float)
    d["index_setting_outpatient"] = ((d["index_setting_inpatient"] == 0) & (d["index_setting_ed"] == 0)).astype(float)
    d.drop(columns=[c for c in d.columns if c.startswith("_")], inplace=True)

    # exposure exclusion
    def hits(v):
        codes = {t.lower() for t in v["rx"]} | {p.lower() for p in v["px"]}
        return sorted(codes & expo)
    dropped_expo = []
    tk365 = toks_n.groupby("patient_key").tok.agg(set)
    for v in VARS.values():
        h = hits(v)
        if not h:
            continue
        if v["name"] in MEDVAR and all(TOKCOUNT[t] > 1 for t in h):
            # only combination-brand tokens overlap the exposure: recompute the class without them
            keep = set(v["rx"]) - set(h)
            d[v["name"]] = tk365.reindex(d.index).apply(lambda x: float(bool(x & keep)) if isinstance(x, set) else 0.0)
            status[v["name"]] = dict(status="kept_exposure_tokens_removed", note="combination tokens removed: " + ",".join(h[:8]),
                                     exposure_leak="possible")
            continue
        if v["name"] not in MEDVAR:
            # not itself an exposure-defining drug but tied to the exposure (e.g. INR / anticoagulation clinic / Z79.01 in warfarin
            # trials, prior ablation in CABANA): keep and tag so balance analyses can exclude or separate it
            status[v["name"]] = dict(status="kept_exposure_leak", note="tied to exposure: " + ",".join(h[:6]), exposure_leak="yes")
            continue
        dropped_expo.append(v["name"])
        status[v["name"]] = dict(status="dropped_exposure", note="exposure-defining drug class: " + ",".join(h[:6]), exposure_leak="yes")
    kept_classes = [f"rx_{k}_365" for k in MED if f"rx_{k}_365" not in dropped_expo and k != "antibiotic_any"]
    d["n_med_classes_365"] = d[kept_classes].sum(1)
    d["polypharmacy_ge5"] = (d["n_med_classes_365"] >= 5).astype(float)
    bad = set(expo)
    for k in MED:
        if f"rx_{k}_365" in dropped_expo:
            bad |= {t.lower() for t in MED[k][0]}
    tk = toks_n[~toks_n.tok.isin(bad)]
    d["n_distinct_drugs_365"] = tk.groupby("patient_key").tok.nunique().reindex(d.index).fillna(0).astype(float)
    d.drop(columns=[c for c in dropped_expo if c in d], inplace=True)
    for v in VARS.values():
        if v["name"] in status:
            continue
        ov = [p for p in v["ps"] if p in core]
        status[v["name"]] = dict(status="kept", note=("PS overlap: " + ",".join(ov)) if ov else "", exposure_leak="")
    for k, st in status.items():
        ov = [p for p in VARS[k]["ps"] if p in core]
        st["ps_overlap"] = ",".join(ov)
    return d, status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threads", type=int, default=28)
    ap.add_argument("--trials", nargs="*")
    a = ap.parse_args()
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    names = {**PRIMARY, **EXTRA}
    trials = a.trials or trial_list()
    ros = []
    for n in trials:
        r = pd.read_parquet(f"{A}/{names[n][1]}/restricted_cohort.parquet")[["patient_key", "person_id", "treated", "treatment_arm", "index_date"]]
        r = r.drop_duplicates("patient_key")
        r.insert(0, "trial", n)
        ros.append(r)
    ros = pd.concat(ros, ignore_index=True)
    con = connect(a.threads)
    allc, toks = build_all(con, ros)
    rows, cover, st_rows = [], {}, []
    for n in trials:
        roles = json.load(open(f"{A}/claude-{n}-baseline-v11/roles.json"))
        obs = pd.read_parquet(f"{A}/claude-{n}-baseline-v11/restricted_baseline_observed.parquet").drop_duplicates("patient_key").set_index("patient_key")
        d = allc[allc.trial == n].drop(columns="trial").set_index("patient_key")
        r = ros[ros.trial == n].set_index("patient_key")
        d, status = finalize_trial(n, d, roles, obs, toks[toks.trial == n], r.index_date)
        keys = analysis_keys(n)
        g = d.loc[d.index.intersection(keys)]
        # low-prevalence / zero-variance drop (analysis population)
        for v in list(d.columns):
            meta = VARS.get(v, {})
            x = g[v]
            if meta.get("type") == "bin":
                p = float(x.mean()) if len(x) else 0.0
                if p < 0.01 or p > 0.99:
                    status[v] = dict(status[v], status="dropped_low_prevalence",
                                     note=f"prevalence {100 * p:.2f}%")
            elif x.notna().mean() < 0.01 or x.nunique(dropna=True) <= 1:
                status[v] = dict(status[v], status="dropped_zero_variance_or_missing", note=f"observed {100 * x.notna().mean():.1f}%")
        drop = [v for v, s in status.items() if s["status"].startswith("dropped") and v in d]
        # keep a lab missing flag only if the value column survives, and vice versa keep value only with its flag
        d = d.drop(columns=drop)
        d = d[[v for v in VARS if v in d.columns]]
        d.insert(0, "treated", r.treated.reindex(d.index).astype(int))
        d.reset_index().to_parquet(OUT / f"{n}.parquet")
        for v, s in status.items():
            st_rows.append(dict(trial=n, variable=v, **s))
        cover[n] = dict(roster=int(len(d)), trial_keys=int(len(keys)), trial_keys_covered=int(keys.isin(d.index).sum()),
                        n_vars=int(d.shape[1] - 1), arms={int(t): str(x) for t, x in r.groupby("treated").treatment_arm.agg(lambda s: s.mode().iloc[0]).items()})
        g = d.loc[d.index.intersection(keys)]
        g1, g0 = g[g.treated == 1], g[g.treated == 0]
        for v in d.columns[1:]:
            typ = VARS[v]["type"]
            row = dict(trial=n, variable=v, domain=VARS[v]["domain"], type=typ, n_treated=len(g1), n_control=len(g0),
                       missing_frac=round(float(g[v].isna().mean()), 4), smd=round(smd(g1[v], g0[v]), 3))
            if typ == "bin":
                c1, c0 = int(g1[v].sum()), int(g0[v].sum())
                row.update(treated=sup(c1, len(g1)), control=sup(c0, len(g0)),
                           pct_treated=np.nan if (1 <= c1 <= 10 or 1 <= len(g1) - c1 <= 10) else round(100 * c1 / max(len(g1), 1), 1),
                           pct_control=np.nan if (1 <= c0 <= 10 or 1 <= len(g0) - c0 <= 10) else round(100 * c0 / max(len(g0), 1), 1))
            else:
                fmt = lambda x: "<11 obs" if 1 <= x.notna().sum() <= 10 else f"{x.mean():.2f} (sd {x.std():.2f})"
                row.update(treated=fmt(g1[v]), control=fmt(g0[v]), pct_treated=np.nan, pct_control=np.nan)
                if "<11" in row["treated"] + row["control"]:
                    row["smd"] = np.nan
            rows.append(row)
        print(n, cover[n], flush=True)
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "summary_by_arm.csv", index=False)
    ST = pd.DataFrame(st_rows)
    ST["exposure_leak"] = ST["exposure_leak"].fillna("")
    ST.to_csv(OUT / "trial_variable_status.csv", index=False)
    dic = pd.DataFrame([dict(variable=v["name"], domain=v["domain"], type=v["type"], definition=v["definition"], source=v["source"],
                             window=wtxt(v["win"]) if v["domain"] not in ("score",) else "", ps_overlap_candidates=",".join(v["ps"]),
                             block="ecg_proximal" if v["name"] in ECG_PROXIMAL else "other")
                        for v in VARS.values()])
    dic.to_csv(OUT / "dictionary.csv", index=False)
    json.dump(dict(coverage=cover, n_registry=len(VARS), script_sha256=sha256(Path(__file__))), open(OUT / "summary.json", "w"), indent=2)
    write_md(S, ST, dic, cover)


def write_md(S, ST, dic, cover):
    trials = list(cover)
    L = ["# v1.6 extended held-out covariates (covars2)", "",
         "Built by `scripts/v16/build_v16_covars2.py`; extends `docs/v16/COVARIATES.md` (`claude-v16-covars`). Restricted per-trial files "
         "`/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars2/<trial>.parquet`, keyed by `patient_key` (same roster key set as "
         "`claude-v16-covars`), with `treated`. **Held-out balance variables only: never enter any PS.** Aggregate companions in the same "
         "directory: `dictionary.csv` (variable, domain, type, definition, source, window, PS-overlap candidates), "
         "`trial_variable_status.csv` (per trial: kept / dropped_exposure / dropped_low_prevalence / dropped_zero_variance_or_missing, and "
         "which PS core variables a kept variable partly duplicates), `summary_by_arm.csv`.", "",
         "## Conventions",
         "- All windows end at index−1 (index day excluded). Default lookback 365 d; `_ever` = all prior history; a few preventive items use "
         "730 d / 3650 d (stated in the definition).",
         "- Diagnoses: ICD-10-CM prefix (dots removed) in OMOP gold `condition_occurrence` + `observation` (as covars v1). Procedures: "
         "upper(`procedure_source_value`) prefix (CPT/HCPCS/ICD-10-PCS; 88% of gold procedure concept ids are 0). Medications: "
         "'-'-split lowercase `drug_source_value` token match (generic + brand + common combination-brand tokens; a combination brand counts "
         "for every component class). Labs/vitals: OMOP gold `measurement` concept ids, latest plausible value in 365 d plus a `_missing` "
         "flag; weight source unit is ounces, height inches.",
         "- Epic (Yale clinical-sources-v1 snapshot: outpatient_enc, hosp_enc, patients; 2025-04-03 and 2026-04-15 deliveries deduplicated on "
         "`PAT_ENC_CSN_ID`) linked by `person.person_source_value` = `PAT_MRN_ID` (digits, leading zeros stripped).",
         "- **Exposure-defining drugs removed:** a medication class containing a single-ingredient token listed in the trial's `roles.json` "
         "`exposure_features` is removed for that trial (e.g. `rx_beta_blocker_365` for COMET/EAST-AFNET4/ASCOT/LIFE, "
         "`rx_oral_anticoagulant_365` for the warfarin trials). If only combination-brand tokens overlap (e.g. janumet in the SGLT2i/DPP4i "
         "trials), the class is recomputed without those tokens (`kept_exposure_tokens_removed`, `exposure_leak = possible`). "
         "`n_med_classes_365` counts only retained classes; `n_distinct_drugs_365` drops exposure tokens and every token of a removed class.",
         "- **Exposure-leak tag:** non-drug variables tied to the exposure (INR, anticoagulation-clinic visits and Z79.01 in the warfarin "
         "trials; Z79.02 / `hasbled` drug item in PLATO; Z79.84 in the DM trials; prior ablation in CABANA) are kept but tagged "
         "`exposure_leak = yes` in `trial_variable_status.csv` so balance analyses can exclude or separate them.",
         "- **Blocks:** `dictionary.csv` column `block` = `ecg_proximal` for variables an ECG is expected to encode directly (rhythm/AF/flutter, "
         "conduction disease, devices/pacing, ablation/cardioversion, ventricular arrhythmia/arrest, cardiomyopathy/HF, rate-control and "
         "antiarrhythmic drugs, prior ECG count, CHA2DS2-VASc/CHADS2 via CHF, hyperkalaemia) and `other` otherwise.",
         "- **Index context:** `index_setting_inpatient/ed/outpatient` describe the index day (setting of initiation) and are the only "
         "non-pre-index variables (domain `index_context`); exclude them where strictly pre-index covariates are required.",
         "- **PS overlap:** kept variables that partly duplicate a PS core variable of that trial (e.g. `rx_statin_365` vs `statin_order` "
         "(90 d), Charlson CHF vs `heart_failure`) are listed in `trial_variable_status.csv` (column `ps_overlap`) so they can be "
         "excluded per cell. They are longer-window / finer versions, not identical copies.",
         "- **Dropping:** per trial, binary variables with prevalence < 1% or > 99% in the analysis population (v13_common.Trial keys) and "
         "numeric variables observed in < 1% or with zero variance are removed from that trial's parquet (listed below).",
         "- Nothing is derived from the index ECG (no machine intervals, no index-ECG text). ECG counts use prior ECG CPT dates only.",
         "- Suppression: `<11` = count or complement in 1–10; percentages derived from such cells are blanked.", ""]
    L += ["## Variables by domain", "", "| Domain | Registered | Kept in ≥1 trial | Kept in all trials |", "|---|---|---|---|"]
    kept = ST[ST.status.str.startswith("kept")].groupby("variable").trial.nunique()
    for dom, grp in dic.groupby("domain", sort=False):
        vs = grp.variable
        L.append(f"| {dom} | {len(vs)} | {int((kept.reindex(vs).fillna(0) > 0).sum())} | {int((kept.reindex(vs).fillna(0) == len(trials)).sum())} |")
    L += ["", f"Registry total: {len(dic)} variables.", "",
          "## Coverage", "", "| Trial | treated arm | comparator arm | roster rows | Trial keys | covered | variables kept |", "|---|---|---|---|---|---|---|"]
    for n, c in cover.items():
        L.append(f"| {n} | {c['arms'].get(1)} | {c['arms'].get(0)} | {c['roster']:,} | {c['trial_keys']:,} | {c['trial_keys_covered']:,} | {c['n_vars']} |")
    L += ["", "## Gaps (not buildable from mounted data)",
          "- **Insurance / payer, preferred language, marital status:** not present in the Epic patient or encounter tables of the extract "
          "(patients table = MRN, birth/death date, sex, race, ethnicity, ZIP; hosp_enc account class is inpatient/outpatient/ED, not payer) "
          "and not in OMOP gold (`person` has no such fields; no `payer_plan_period`).",
          "- **Smoking status from social history:** re-checked; OMOP gold `observation` contains only ICD-10 codes (100% ICD-like source "
          "values), there is no social-history table in the Epic snapshot. Tobacco remains dx-code based (covars v1 + `tobacco_counseling_or_history`, "
          "`rx_smoking_cessation_365`).",
          "- **Magnesium, ferritin, urine albumin/creatinine ratio, vitamin D, phosphate:** not among the 83 gold measurement concepts, and the "
          "Epic hospital/outpatient lab extracts are limited panels without them.",
          "- **Distinct prescribers:** `drug_exposure` and Epic medication orders carry no prescriber; distinct outpatient *visit* providers "
          "(`n_distinct_outpatient_providers_365`) is offered instead.",
          "- **Area deprivation:** as in covars v1, no ADI/SVI file; only `zip_out_of_state` (current address).",
          "- **Labile INR (HAS-BLED L):** not scored (time-in-range needs warfarin exposure periods; exposure-adjacent in the AF trials).",
          "- **HFRS** weights transcribed from Gilbert et al. 2018 (Lancet) table; F00/U80 do not exist in ICD-10-CM so never fire.",
          "- Epic outpatient encounter coverage is narrower than OMOP 9202 visits (12.2 M + 2.6 M vs 29 M rows), so specialty-visit counts are "
          "lower bounds.", ""]
    lit = load_lit()
    if lit is not None:
        L += ["## Literature list cross-check (docs/v16/lit_covariates.json)", "",
              "Each literature item and where it is covered: `covars2` variables built here, the existing panel it already sits in "
              "(per the literature file's `current_panel`), or why it is not built.", "",
              "| # | Literature item | Existing panel | covars2 variables | Note |", "|---|---|---|---|---|"]
        for it in lit:
            nm = it.get("name", "")
            cv = LITMAP.get(nm, "")
            note = LIT_REASON.get(nm, "")
            if not cv and not note and it.get("current_panel", "none") != "none":
                note = "already in existing panel"
            L.append(f"| {it.get('id', '')} | {nm} | {it.get('current_panel', '')} | {cv} | {note} |")
        L.append("")
    L += ["## Dropped / tagged per trial", ""]
    for n in trials:
        s = ST[(ST.trial == n) & ST.status.str.startswith("dropped")]
        ex = sorted(s[s.status == "dropped_exposure"].variable)
        lk = sorted(ST[(ST.trial == n) & (ST.exposure_leak != "") & ST.status.str.startswith("kept")].variable)
        lo = sorted(s[s.status != "dropped_exposure"].variable)
        L.append(f"- **{n}** — exposure ({len(ex)}): {', '.join(f'`{v}`' for v in ex) or 'none'}; low prevalence / no variance ({len(lo)}): "
                 + (", ".join(f"`{v}`" for v in lo) or "none") + "; kept with exposure-leak tag: " + (", ".join(f"`{v}`" for v in lk) or "none"))
    L += ["", "## Prevalence by arm", "",
          "Cells: binary = treated % / comparator % (SMD); numeric = treated mean / comparator mean (SMD). SMD = treated − comparator, pooled "
          "SD, unadjusted, analysis population. Blank = dropped for that trial; `<11` = suppressed. Full rows with counts and SD in "
          "`summary_by_arm.csv`.", ""]
    short = {n: n.replace("emperor-preserved-v2", "emperor-p").replace("paradigm-hf-seq", "paradigm").replace("transform-hf", "transform")
             for n in trials}
    for dom, grp in dic.groupby("domain", sort=False):
        vs = [v for v in grp.variable if v in set(S.variable)]
        if not vs:
            continue
        L += [f"### {dom}", "", "| Variable | " + " | ".join(short[n] for n in trials) + " |", "|---|" + "---|" * len(trials)]
        Si = S.set_index(["variable", "trial"])
        for v in vs:
            cells = []
            for n in trials:
                if (v, n) not in Si.index:
                    cells.append("")
                    continue
                r = Si.loc[(v, n)]
                if r.type == "bin":
                    if pd.isna(r.pct_treated) or pd.isna(r.pct_control):
                        a_ = "<11" if pd.isna(r.pct_treated) else f"{r.pct_treated:.1f}"
                        b_ = "<11" if pd.isna(r.pct_control) else f"{r.pct_control:.1f}"
                        cells.append(f"{a_}/{b_}")
                    else:
                        cells.append(f"{r.pct_treated:.1f}/{r.pct_control:.1f} ({r.smd:+.2f})")
                else:
                    if "<11" in str(r.treated) + str(r.control):
                        cells.append("<11 obs")
                        continue
                    m1, m0 = float(r.treated.split(" ")[0]), float(r.control.split(" ")[0])
                    cells.append(f"{m1:.3g}/{m0:.3g} ({r.smd:+.2f})")
            L.append(f"| `{v}` | " + " | ".join(cells) + " |")
        L.append("")
    L += ["## Definitions", "", "| Variable | Domain | Type | Window | Definition | Source |", "|---|---|---|---|---|---|"]
    for r in dic.itertuples():
        L.append(f"| `{r.variable}` | {r.domain} | {r.type} | {r.window} | {r.definition.replace('|', '/')} | {r.source} |")
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text("\n".join(L) + "\n")



if __name__ == "__main__":
    main()
