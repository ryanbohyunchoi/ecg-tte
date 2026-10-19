#!/usr/bin/env python
"""CHS -> CLMBR-T code map (EXPLORATORY; docs/bdc/CHS_EHR_EXPLORATORY.md). Runs LOCALLY (needs the OMOP vocabulary),
never on BDC. The output is SNOMED-derived, so it is NOT committed: it is written under /mnt/raid0/rbc58 and uploaded to
BDC by the user (and read there by chs_clmbr.py timeline --map).

Maps:
  icd9cm    dotted ICD-9-CM code (full codes and 3-digit categories) -> standard concepts via OMOP 'Maps to', kept
            where the target code is in the CLMBR-T vocabulary (as scripts/mimic/build_mimic_meds.py)
  icd9proc  the ICD9Proc codes in the CLMBR-T vocabulary (used directly, dotted, as at Yale); other common procedures
            through curated category rules (PROC, v2) to the nearest in-vocabulary procedure concept
  med       CHS medication-class flag (`*06`) -> one representative in-vocabulary RxNorm clinical drug per class (crude:
            CHS records classes, not drugs; see MED). Summary flags (any diuretic, any CCB,
            any hypertension medication, counts, interviewer IDs, days taken) map to nothing.
  history   baseline history flags -> one SNOMED condition each
  visit     annual clinic visit -> Visit/OP; hospital admission -> Visit/IP
No participant data is read. Usage:
  python scripts/bdc/chs_clmbr_map.py --vocab-dir <dir with concept.parquet, maps_to.parquet, clmbr_code_strings.json> \
      --out /mnt/raid0/rbc58/ecg-tte/audits/bdc-clmbr-map/chs_clmbr_map.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import pandas as pd

VERSION = "chs_clmbr_map_v2"
# flag -> drug components; each component = ingredient-name alternatives ("a|b", tried in order) or a CVX code.
# CLMBR-T's RxNorm codes are clinical drugs (e.g. 'lisinopril 10 MG Oral Tablet'), so each component resolves to the
# in-vocabulary single-ingredient product with the highest pretraining frequency (dictionary weight); a combination flag
# first looks for one in-vocabulary combination product. [] = summary or non-drug field: no token.
MED = {
    "A2A06": ["losartan"], "A2AD06": ["losartan", "hydrochlorothiazide"], "ACE06": ["lisinopril|enalapril|captopril"],
    "ACED06": ["lisinopril", "hydrochlorothiazide"], "ADPI06": ["ticlopidine|clopidogrel"], "AGDI06": ["acarbose|miglitol"],
    "ALPHA06": ["doxazosin|terazosin|prazosin"], "ALPHAD06": ["prazosin|doxazosin", "hydrochlorothiazide"],
    "ALZH06": ["donepezil"], "AMLOD06": ["amlodipine"], "ANAR1A06": ["quinidine|procainamide|disopyramide"],
    "ANAR1B06": ["mexiletine|lidocaine"], "ANAR1C06": ["flecainide|propafenone"], "ANAR306": ["amiodarone|sotalol"],
    "ANTPSY06": ["haloperidol|risperidone"], "ASA06": ["aspirin"], "ASPR06": ["aspirin"], "ASPIRIN": ["aspirin"],
    "BASQ06": ["cholestyramine resin|colestipol"], "BENZOD06": ["lorazepam|diazepam|alprazolam"],
    "BETA06": ["atenolol|metoprolol|propranolol"], "BETAD06": ["atenolol", "chlorthalidone"], "BGND06": ["metformin"],
    "CCBT06": ["mibefradil"], "COX206": ["celecoxib"], "DIG06": ["digoxin"], "DIHIR06": ["nicardipine|isradipine"],
    "DIHSR06": ["felodipine|nisoldipine|isradipine"], "DLTIR06": ["diltiazem"], "DLTSR06": ["diltiazem"],
    "EDD06": ["sildenafil"], "ESTRGN06": ["estradiol"], "FIBR06": ["gemfibrozil|fenofibrate"],
    "H2B06": ["ranitidine|famotidine|cimetidine"], "HCTZ06": ["hydrochlorothiazide|chlorthalidone"],
    "HCTZK06": ["hydrochlorothiazide", "triamterene"], "HPRNS06": ["heparin|enoxaparin"],
    "INSULN06": ["insulin glargine|insulin, regular, human|insulin isophane, human|insulin lispro"],
    "IPRTR06": ["ipratropium"], "ISTRD06": ["beclomethasone|fluticasone|budesonide"],
    "KBLKR06": ["repaglinide|nateglinide"], "KCL06": ["potassium chloride"], "KSPR06": ["spironolactone|amiloride"],
    "LOOP06": ["furosemide|bumetanide"], "MAOI06": ["phenelzine|selegiline"], "MLPD06": ["ezetimibe"],
    "NIAC06": ["niacin"], "NIFIR06": ["nifedipine"], "NIFSR06": ["nifedipine"], "NSAID06": ["ibuprofen|naproxen"],
    "NTCA06": ["sertraline|fluoxetine|trazodone"], "NTG06": ["isosorbide mononitrate|isosorbide dinitrate"],
    "NITRO06": ["nitroglycerin"], "OAIA06": ["montelukast"], "OHGA06": ["glipizide|glyburide"],
    "OSTRD06": ["prednisone"], "OTCH2B06": ["famotidine|ranitidine"], "PDEI06": ["theophylline"],
    "PPI06": ["omeprazole|pantoprazole"], "PROGST06": ["medroxyprogesterone"],
    "PRKNSN06": ["carbidopa", "levodopa"], "PREMAR06": ["estrogens, conjugated (usp)|estradiol"],
    "PROB06": ["probucol"], "PVDL06": ["pentoxifylline|cilostazol"], "SLF106": ["tolbutamide|chlorpropamide|glipizide"],
    "SLF206": ["glipizide|glyburide"], "STTN06": ["simvastatin|atorvastatin|pravastatin|lovastatin"],
    "SYMPTH06": ["albuterol"], "TCA06": ["amitriptyline|nortriptyline"], "TCAP06": ["perphenazine", "amitriptyline"],
    "THRY06": ["levothyroxine"], "THZD06": ["pioglitazone|rosiglitazone"], "URCOS06": ["probenecid"],
    "VASO06": ["hydralazine"], "VASOD06": ["hydralazine", "hydrochlorothiazide"], "VERIR06": ["verapamil"],
    "VERSR06": ["verapamil"], "WARF06": ["warfarin"], "WTLS06": ["phentermine"], "XOI06": ["allopurinol"],
    "CALC06": ["calcium carbonate"], "LAXATV06": ["docusate|senna|polyethylene glycol 3350"],
    "SLPILL06": ["zolpidem|temazepam"], "ANTHST06": ["diphenhydramine|loratadine"],
    "FSHOIL06": ["omega-3 acid ethyl esters (usp)"], "FLUSH06": ["CVX/88|CVX/141|CVX/140"], "PNEUSH06": ["CVX/33"],
    # summary or non-drug fields: no token
    "CCB06": [], "CCBIR06": [], "CCBSR06": [], "DIURET06": [], "LIPID06": [], "HTNMED06": [], "TAKMED06": [],
    "UNTRAN06": [], "DAYASP06": [], "DAYFSH06": [], "INTID06": [], "NOMEDS06": [],
}
# baseline history -> code alternatives (first one in the vocabulary is used)
HISTORY = {"MI": ["SNOMED/22298006"], "ANGINA": ["SNOMED/194828000"], "HF": ["SNOMED/42343007"],
           "STROKE": ["SNOMED/230690007"], "HTN": ["SNOMED/38341003"], "DIABETES": ["SNOMED/44054006"],
           "AF": ["SNOMED/49436004"], "ANGIOPLASTY": ["SNOMED/11101003"], "BYPASS": ["SNOMED/399261000"]}


# ICD-9 procedure (dotless prefix, longest match wins) -> in-vocabulary procedure codes ("ICD9Proc/.." or an exact SNOMED
# procedure name). Curated (v2, 2026-10-19): CLMBR-T knows only 196 ICD9Proc codes, and ICD9Proc is itself a standard OMOP
# vocabulary (no 'Maps to' SNOMED), so common inpatient procedures of older adults map to the nearest in-vocabulary
# procedure concept. Codes already in the vocabulary are used as they are (chs_clmbr.map_px).
PROC = {
    # coronary / cardiac
    "0066": ["Percutaneous transluminal coronary angioplasty"], "3601": ["Percutaneous transluminal coronary angioplasty"],
    "3602": ["Percutaneous transluminal coronary angioplasty"], "3605": ["Percutaneous transluminal coronary angioplasty"],
    "3606": ["Placement of stent in coronary artery"], "3607": ["Insertion of drug-eluting coronary artery stent"],
    "361": ["SNOMED/399261000"],  # CABG: no procedure concept in the vocabulary -> history of CABG
    "372": ["Cardiac catheterization"], "3721": ["Catheterization of right heart"],
    "3722": ["Catheterization of left heart"], "3723": ["Catheterization of both left and right heart"],
    "3726": ["ICD9Proc/37.26"], "3734": ["Catheter ablation of tissue of heart"],
    "378": ["Insertion of pacemaker pulse generator"], "3794": ["ICD9Proc/37.94"], "3795": ["ICD9Proc/37.94"],
    "3796": ["ICD9Proc/37.94"], "3797": ["ICD9Proc/37.94"], "3798": ["ICD9Proc/37.94"],
    "8852": ["Angiocardiography of left heart"], "8853": ["Angiocardiography of left heart"],
    "8854": ["Angiocardiography of left heart"], "8855": ["Angiography of coronary artery"],
    "8856": ["Angiography of coronary artery"], "8857": ["Angiography of coronary artery"],
    "884": ["Angiography"], "8841": ["Angiography of cerebral arteries"], "8842": ["Angiography of aorta"],
    "8845": ["Angiography of renal artery"], "8843": ["Angiography of pulmonary arteries"],
    "8872": ["Echocardiography"], "8873": ["ICD9Proc/88.73"], "8876": ["ICD9Proc/88.76"],
    "8877": ["Doppler ultrasonography of artery"], "8871": ["Ultrasonography of carotid artery"],
    "8952": ["Electrocardiographic procedure"], "8950": ["48 hour ambulatory electrocardiographic monitoring"],
    "8941": ["Cardiovascular stress testing"], "8943": ["Cardiovascular stress testing"],
    "8944": ["Cardiovascular stress testing"], "8964": ["Introduction of catheter into pulmonary artery"],
    "9962": ["ICD9Proc/99.62"], "9960": ["ICD9Proc/99.60"], "9910": ["ICD9Proc/99.10"],
    # vascular access, dialysis, lines
    "3995": ["Hemodialysis"], "5498": ["Dialysis procedure"], "3927": ["Insertion of graft for vascular access"],
    "3891": ["Insertion of catheter into artery"], "3893": ["ICD9Proc/38.93"], "3897": ["ICD9Proc/38.97"],
    "3899": ["ICD9Proc/38.99"],
    # blood, airway, ventilation, nutrition
    "990": ["Transfusion"], "9904": ["Transfusion of packed red blood cells"], "9905": ["Platelet transfusion"],
    "9907": ["ICD9Proc/99.07"], "9604": ["Insertion of endotracheal tube"], "9605": ["Intubation"],
    "9607": ["Insertion of nasogastric tube"], "9670": ["Artificial ventilation"], "9671": ["ICD9Proc/96.71"],
    "9672": ["ICD9Proc/96.72"], "9390": ["Continuous positive airway pressure ventilation treatment"],
    "9396": ["Oxygen therapy"], "9394": ["Nebulizer therapy"], "9915": ["Administration of nutritional supplement"],
    "4311": ["Percutaneous endoscopic gastrostomy"], "4319": ["Percutaneous endoscopic gastrostomy"],
    # gastrointestinal
    "4513": ["ICD9Proc/45.13"], "4516": ["Endoscopy and biopsy of upper gastrointestinal tract"],
    "4514": ["Endoscopy and biopsy of upper gastrointestinal tract"], "4523": ["Colonoscopy"],
    "4524": ["Diagnostic endoscopic examination on colon"], "4525": ["Endoscopic biopsy of large intestine"],
    "4542": ["Endoscopic polypectomy of large intestine"], "4543": ["ICD9Proc/45.43"],
    "4573": ["ICD9Proc/45.43"], "457": ["ICD9Proc/45.43"],
    "5110": ["Endoscopic retrograde cholangiopancreatography"], "5122": ["Laparoscopic cholecystectomy"],
    "5123": ["Laparoscopic cholecystectomy"], "4701": ["Laparoscopic appendectomy"], "4709": ["Laparoscopic appendectomy"],
    "5491": ["Abdominal paracentesis"], "5411": ["ICD9Proc/54.4"], "5459": ["ICD9Proc/54.59"],
    # respiratory
    "3322": ["Fiberoptic bronchoscopy"], "3323": ["Bronchoscopy"], "3324": ["Bronchoscopy and biopsy of bronchus"],
    "3327": ["Bronchoscopy with transbronchial lung biopsy"], "3404": ["Insertion of pleural tube drain"],
    "3491": ["Insertion of pleural tube drain"],
    # imaging
    "8703": ["CT of head"], "8741": ["CT of chest"], "8801": ["CT of abdomen"], "8838": ["Computed tomography"],
    "8891": ["MRI of brain and brain stem"], "8744": ["Radiographic procedure of chest"],
    "8749": ["Radiographic procedure of chest"], "8719": ["Plain X-ray of abdomen"], "8826": ["ICD9Proc/88.26"],
    "8827": ["ICD9Proc/88.27"], "8874": ["ICD9Proc/88.76"], "8875": ["Ultrasonography of kidney and bladder"],
    "8879": ["ICD9Proc/88.79"],
    # orthopaedic, eye, urology, other surgery
    "8151": ["Total replacement of hip"], "8152": ["Total replacement of hip"], "8153": ["Total replacement of hip"],
    "8154": ["Total knee replacement"], "8155": ["Total knee replacement"], "7915": ["ICD9Proc/79.36"],
    "7935": ["ICD9Proc/79.36"], "7936": ["ICD9Proc/79.36"], "1341": ["Aspiration of cataract by phacoemulsification"],
    "1359": ["One stage extracapsular extraction of lens and insertion of prosthetic intraocular lens"],
    "1371": ["One stage extracapsular extraction of lens and insertion of prosthetic intraocular lens"],
    "6029": ["ICD9Proc/60.29"], "602": ["ICD9Proc/60.29"], "5794": ["Intermittent urethral catheterization"],
    "5732": ["ICD9Proc/57.32"], "0331": ["Lumbar puncture"], "8622": ["ICD9Proc/86.28"], "8628": ["ICD9Proc/86.28"],
    "0624": ["Total thyroidectomy"], "8521": ["Partial mastectomy"], "8522": ["Partial mastectomy"],
    "8523": ["Partial mastectomy"], "9339": ["ICD9Proc/93.39"], "9383": ["Rehabilitation therapy"],
    "9921": ["ICD9Proc/99.21"], "9925": ["Infusion chemotherapy for malignant neoplasm"], "9229": ["ICD9Proc/92.29"],
    "9228": ["ICD9Proc/92.28"], "9227": ["Radiation therapy procedure or service"],
}


def weights(path: Path) -> dict:
    import msgpack
    d = msgpack.unpackb(path.read_bytes(), strict_map_key=False)
    return {e["code_string"]: float(e["weight"]) for e in d["vocab"] if e.get("type") == "code"}


def resolve_drugs(C: pd.DataFrame, vocab: set, w: dict):
    """Ingredient names -> in-vocabulary RxNorm clinical drugs, by pretraining frequency (most negative weight)."""
    r = C[(C.vocabulary_id == "RxNorm") & C.code.isin(vocab)].copy()
    r["parts"] = r.concept_name.str.lower().str.split(" / ")
    r["n"] = r.parts.str.len()
    r["w"] = r.code.map(w).fillna(0.0)
    r = r.sort_values("w")

    r["oral"] = r.concept_name.str.contains(r"\bOral\b", regex=True)

    def find(names, oral=None):
        ok = r[r.n == len(names)]
        if oral:
            ok = ok[ok.oral]
        for nm in names:
            ok = ok[ok.parts.map(lambda ps, nm=nm: any(p == nm or p.startswith(nm + " ") for p in ps))]
        return ok.code.iloc[0] if len(ok) else None

    def first(a):  # CHS records outpatient medicines: an oral product of any alternative first, then any form
        for x in a:
            if x.startswith("CVX/") and x in vocab:
                return x
        for oral in (True, None):
            for x in a:
                c = None if x.startswith("CVX/") else find([x], oral)
                if c:
                    return c
        return None

    med, missing = {}, []
    for flag, comps in MED.items():
        if not comps:
            med[flag] = []
            continue
        alts = [c.split("|") for c in comps]
        codes = []
        if len(alts) > 1:  # combination product: one code first
            c = find([a[0] for a in alts], True) or find([a[0] for a in alts])
            if c:
                med[flag] = [c]
                continue
        for a in alts:
            c = first(a)
            (codes.append(c) if c else missing.append(f"{flag}:{'|'.join(a)}"))
        med[flag] = codes
    names = dict(zip(r.code, r.concept_name))
    return med, missing, {c: names.get(c, c) for v in med.values() for c in v}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build(vocab_dir: Path, dict_path: Path) -> dict:
    C = pd.read_parquet(vocab_dir / "concept.parquet",
                        columns=["concept_id", "concept_name", "vocabulary_id", "concept_class_id", "standard_concept",
                                 "concept_code", "invalid_reason"])
    M = pd.read_parquet(vocab_dir / "maps_to.parquet")
    vocab = set(json.loads((vocab_dir / "clmbr_code_strings.json").read_text())["codes"])
    C["code"] = C.vocabulary_id + "/" + C.concept_code
    # ICD-9-CM -> standard concepts in the CLMBR-T vocabulary
    src = C[C.vocabulary_id == "ICD9CM"][["concept_id", "concept_code"]]
    m = src.merge(M, left_on="concept_id", right_on="concept_id_1").merge(
        C[["concept_id", "code"]].rename(columns={"concept_id": "concept_id_2"}), on="concept_id_2")
    m = m[m.code.isin(vocab)]
    icd9cm = {k: sorted(set(g.code)) for k, g in m.groupby("concept_code")}
    cats = src.concept_code[src.concept_code.str.fullmatch(r"(V\d\d|E\d\d\d|\d\d\d)")]
    # medications and history
    med, missing, drug_names = resolve_drugs(C, vocab, weights(dict_path))
    hist, hmiss = {}, []
    for k, alts in HISTORY.items():
        c = next((x for x in alts if x in vocab), None)
        (hist.__setitem__(k, [c]) if c else hmiss.append(k))
    icd9proc = sorted(c.split("/", 1)[1] for c in vocab if c.startswith("ICD9Proc/"))
    snp = C[(C.vocabulary_id == "SNOMED") & C.code.isin(vocab)]
    by_snomed = dict(zip(snp.concept_name, snp.code))
    proc_rules, proc_missing = {}, []
    for pre, targets in PROC.items():
        if not targets or not pre.isdigit():
            continue
        codes = [t if "/" in t and t in vocab else by_snomed.get(t) for t in targets]
        (proc_missing.append(pre) if not all(codes) else proc_rules.__setitem__(pre, codes))
    visit = {k: v for k, v in {"clinic": "Visit/OP", "admission": "Visit/IP"}.items() if v in vocab}
    return dict(version=VERSION, created=time.strftime("%Y-%m-%d %H:%M"), icd9cm=icd9cm, icd9proc=icd9proc, med=med,
                icd9proc_rules=proc_rules,
                history=hist, visit=visit, drug_names=drug_names,
                coverage=dict(icd9cm_source_codes=int(len(src)), icd9cm_mapped_in_vocab=len(icd9cm),
                              icd9cm_categories=int(len(cats)), icd9cm_categories_mapped=int(cats.isin(icd9cm).sum()),
                              icd9proc_in_vocab=len(icd9proc), med_flags=len(MED),
                              med_flags_with_token=sum(bool(v) for v in med.values()), med_missing=missing,
                              history_missing=hmiss, icd9proc_rules=len(proc_rules), icd9proc_rules_missing=proc_missing,
                              clmbr_vocabulary=len(vocab)),
                sources=dict({p: sha(vocab_dir / p) for p in ("concept.parquet", "maps_to.parquet", "clmbr_code_strings.json")},
                             dictionary_msgpack=sha(dict_path)))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vocab-dir", type=Path, required=True)
    ap.add_argument("--dictionary", type=Path, default=Path("/mnt/raid0/eo287/clmbr/dictionary.msgpack"),
                    help="CLMBR-T dictionary.msgpack (read only): pretraining code weights")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    os.umask(0o077)
    out = build(a.vocab_dir, a.dictionary)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps(out["coverage"], indent=1), "\n", a.out, sha(a.out))


if __name__ == "__main__":
    main()
