#!/usr/bin/env python
"""CHS -> CLMBR-T code map (EXPLORATORY; docs/bdc/CHS_EHR_EXPLORATORY.md). Runs LOCALLY (needs the OMOP vocabulary),
never on BDC. The output is SNOMED-derived, so it is NOT committed: it is written under /mnt/raid0/rbc58 and uploaded to
BDC by the user (and read there by chs_clmbr.py timeline --map).

Maps:
  icd9cm    dotted ICD-9-CM code (full codes and 3-digit categories) -> standard concepts via OMOP 'Maps to', kept
            where the target code is in the CLMBR-T vocabulary (as scripts/mimic/build_mimic_meds.py)
  icd9proc  the ICD9Proc codes in the CLMBR-T vocabulary (used directly, dotted, as at Yale)
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

VERSION = "chs_clmbr_map_v1"
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
    visit = {k: v for k, v in {"clinic": "Visit/OP", "admission": "Visit/IP"}.items() if v in vocab}
    return dict(version=VERSION, created=time.strftime("%Y-%m-%d %H:%M"), icd9cm=icd9cm, icd9proc=icd9proc, med=med,
                history=hist, visit=visit, drug_names=drug_names,
                coverage=dict(icd9cm_source_codes=int(len(src)), icd9cm_mapped_in_vocab=len(icd9cm),
                              icd9cm_categories=int(len(cats)), icd9cm_categories_mapped=int(cats.isin(icd9cm).sum()),
                              icd9proc_in_vocab=len(icd9proc), med_flags=len(MED),
                              med_flags_with_token=sum(bool(v) for v in med.values()), med_missing=missing,
                              history_missing=hmiss, clmbr_vocabulary=len(vocab)),
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
