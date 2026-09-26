"""v1.5 UK Biobank shared definitions (protocol docs/PROTOCOL_V1_5_EXTERNAL.md, interface docs/V15_INTERFACE.md).

Medication classes are regular expressions over UKB coding-4 meanings (field 20003, self-reported
current medication), which is how data.csv stores the values (lower-case names, not numeric codes).
The public coding-4 table (UKB showcase, downloaded 2026-09-26) is cached at
/mnt/raid0/rbc58/ecg-tte/reference/ukb/coding4.tsv and used only to review the class lists.
Coding 4 contains no DOAC entries (apixaban/rivaroxaban/dabigatran/edoxaban are absent).
"""
import re

DATA_CSV = "/mnt/raid0/rbc58/prs/ukb/data.csv"
ECG_DIR = "/mnt/raid0/bb2238/signals/preprocessed/ukb_2025"
MEDS_PQ = "/mnt/raid0/eo287/clmbr/processed_data/ukb/ukb_meds.parquet"
CLMBR_PQ = "/mnt/raid0/rbc58/clmbr/ukb/ukb_clmbr_embeddings_censored_v2.parquet"
CODING4 = "/mnt/raid0/rbc58/ecg-tte/reference/ukb/coding4.tsv"
AUDIT = "/mnt/raid0/rbc58/ecg-tte/audits"
# Hospital inpatient (41270/41280) data end: max observed first-occurrence date (England HES).
# Death (40000) runs to 2024-07 but composites are censored at the hospital data end.
DATA_END = "2022-10-31"

EYE = r"eye drop|eye gel|ophthalmic|% eye|minims"
CLASS_RX = {
    "arb": r"sartan|cozaar|diovan|micardis|aprovel|amias|olmetec|navispare|teveten|coaprovel|exforge|sevikar",
    "acei": r"(capto|enala|lisino|rami|perindo|trandola|fosino|quina|quinala|imida|cilaza|moexi|benaze)pril|tritace|zestril|"
            r"coversyl|innovace|capoten|carace|accupril|gopten|tanatril|zestoretic|innozide|capozide|accuretic|triapin|tarka|"
            r"acezide|vascace|staril|perdix",
    "amlodipine": r"amlodipin|\bistin\b|exforge|sevikar",
    "dhp_ccb_other": r"nifedip|felodip|lacidip|lercanidip|nicardip|nisoldip|isradip|adalat|coracten|plendil|motens|zanidip|"
                     r"triapin|cardene|syscor|nifedipress",
    "rate_ccb": r"diltiazem|verapamil|tildiem|adizem|cordilox|securon|tarka|slozem|dilzem|univer|viazem",
    "thiazide": r"thiazid|thiazide|bendrofluazide|indapamid|chlortalidon|chlorthalidon|metolazon|xipamide|co-amilozide|"
                r"co-triamterzide|co-tenidone|natrilix|hygroton|tenoret|tenoretic|kalten|zestoretic|innozide|capozide|"
                r"cozaar-comp|coaprovel|co-diovan|micardisplus|accuretic|acezide|moduretic|dyazide|neo-naclex|aprinox|"
                r"prestim|navidrex|lodoz|monozide|co-zidocapt|perindopril\+indapamide|coversyl plus|diltiazem hcl\+hydro",
    "bb_trial": r"atenolol|bisoprolol|metoprolol|nebivolol|tenormin|betaloc|lopresor|cardicor|emcor|nebilet|co-tenidone|"
                r"tenoret|tenoretic|kalten|lodoz|monozide|totamol|monocor",
    "bb_other": r"propranolol|penbutolol|carvedilol|labetalol|nadolol|oxprenolol|pindolol|prindolol|acebutolol|celiprolol|sotalol|"
                r"timolol|betaxolol|carteolol|levobunolol|metipranolol|esmolol|inderal|trandate|eucardic|sectral|"
                r"celectol|beta-cardone|sotacor|corgard|trasicor|visken|betim|half-inderal|bedranol|syprol",
    "warfarin": r"warfarin|marevan",
    "other_vka": r"phenindione|acenocoumarol|sinthrome",
    "loop": r"furosemide|frusemide|bumetanide|torasemide|lasix|burinex|co-amilofruse|frumil|torem\b",
    "mra": r"spironolacton|eplerenon|aldactone|inspra|co-flumactone|aldactide|lasilactone",
    "alpha_blocker": r"doxazosin|prazosin|terazosin|indoramin|cardura|hypovase|hytrin|baratol",
    "other_antihtn": r"moxonidin|clonidin|methyldopa|hydralazin|minoxidil|aliskiren|physiotens|catapres|aldomet|apresoline|rasilez",
    "statin": r"(simva|atorva|prava|fluva|rosuva|epta|vela|lova|pitava)statin|lipitor|zocor|crestor|lipostat|lescol",
    "other_lipid": r"ezetimib|ezetrol|fenofibrat|bezafibrat|gemfibrozil|ciprofibrat|nicotinic acid|niaspan|omacor|colestyr",
    "aspirin": r"aspirin|nu-seals|caprin|disprin|angettes|micropirin",
    "p2y12": r"clopidogrel|prasugrel|ticagrelor|plavix|efient|brilique",
    "dipyridamole": r"dipyridamol|persantin|asasantin",
    "nitrate": r"glyceryl trinitrate|\bgtn\b|isosorbide|\bisdn\b|\bismn\b|nicorandil|ikorel|imdur|elantan|\bismo\b|monomax|xismox|tetranitrate|nitrate vasodilator|sorbide nitrate",
    "digoxin": r"digoxin|lanoxin",
    "antiarrhythmic": r"amiodaron|flecainid|propafenon|dronedaron|cordarone|tambocor|multaq",
    "insulin": r"insulin|insulatard|actrapid|humulin|mixtard|lantus|levemir|novorapid|humalog|glargine|detemir|lispro",
    "metformin": r"metformin|glucophage",
    "sulfonylurea": r"gliclazid|glibenclamid|glipizid|glimepirid|tolbutamid|chlorpropamid|diamicron|amaryl|daonil|minodiab",
    "other_oral_dm": r"pioglitazon|rosiglitazon|sitagliptin|vildagliptin|saxagliptin|linagliptin|exenatid|liraglutid|"
                     r"repaglinid|nateglinid|acarbos|actos|avandia|januvia|galvus|byetta|victoza",
    "ppi": r"(lanso|ome|panto|rabe|esome)prazole|losec|nexium|zoton|protium|pariet",
    "levothyroxine": r"thyroxin|levothyrox|eltroxin",
    "nsaid": r"ibuprofen|naproxen|diclofenac|meloxicam|celecoxib|etoricoxib|indometacin|indomethacin|piroxicam|"
             r"nabumetone|etodolac|ketoprofen|mefenamic|brufen|nurofen|voltarol|arcoxia|celebrex|naprosyn",
    "oral_steroid": r"prednisolon|dexamethason|hydrocortison tablet|deltacortril|prednisone",
    "allopurinol": r"allopurinol|zyloric|febuxostat",
    "antidepressant": r"citalopram|sertralin|fluoxetin|paroxetin|escitalopram|mirtazapin|venlafaxin|duloxetin|amitriptylin|"
                      r"dosulepin|trazodon|nortriptylin|lofepramin|clomipramin|imipramin",
    "bronchodilator_ics": r"salbutamol|ventolin|salmeterol|seretide|symbicort|tiotropium|spiriva|beclometasone|budesonide|"
                          r"fluticasone|formoterol|ipratropium|atrovent|terbutaline|bricanyl|serevent|becotide|pulmicort|flixotide|clenil",
}
CLASS_RE = {k: re.compile(v) for k, v in CLASS_RX.items()}
BB_ALL = ("bb_trial", "bb_other")

# Arm definitions per comparison. Arm A = any class in A and none in B; arm B = any class in B and none in A;
# users of any `excl_both` class are removed from both arms (keeps the arms mutually exclusive at class level).
COMPARISONS = {
    "ontarget": dict(comparison="arb_vs_acei", arms=("arb", "acei"), A=["arb"], B=["acei"], excl_both=[],
                     gate="htn", excl_dx=["I50"], outcome=["death", "mi", "stroke", "hf"], horizon_months=56,
                     rct_key="ontarget", secondary=["elite_ii"]),
    "allhat": dict(comparison="amlodipine_vs_thiazide", arms=("amlodipine", "thiazide"), A=["amlodipine"], B=["thiazide"],
                   excl_both=["dhp_ccb_other"], gate="htn", excl_dx=["I50"], outcome=["death", "mi"], horizon_months=59,
                   rct_key="allhat", secondary=[]),
    "ascot": dict(comparison="amlodipine_vs_betablocker", arms=("amlodipine", "beta_blocker"), A=["amlodipine"], B=["bb_trial"],
                  excl_both=["bb_other_systemic", "dhp_ccb_other"], gate="htn", excl_dx=["I50"], outcome=["death", "mi"],
                  horizon_months=66, rct_key="ascot", secondary=[]),
    "aristotle": dict(comparison="doac_vs_warfarin", arms=("doac", "warfarin"), A=[], B=["warfarin"], excl_both=["other_vka"],
                      gate="af", excl_dx=[], outcome=["stroke_se"], horizon_months=22, rct_key="aristotle",
                      secondary=["rocket_af"]),
}
# trial_specs eligibility not applied in the primary cohort (user gate = hypertension + HF exclusion); counted in summary
SPEC_ELIG = {"ontarget": dict(min_age=55, require_any=["I20", "I21", "I22", "I23", "I24", "I25", "I63", "I64", "G45", "I70", "I739", "E11"]),
             "allhat": dict(min_age=55), "ascot": dict(min_age=40, max_age=79, excl=["I21", "I22", "I252", "I20"])}

HTN_ICD = ["I10", "I11", "I12", "I13", "I15"]
ANTIHTN_CLASSES = ["arb", "acei", "amlodipine", "dhp_ccb_other", "thiazide", "bb_trial", "alpha_blocker", "other_antihtn"]
DX_CORE = {  # Yale-core comorbidities from ICD-10 first-occurrence (3-char prefix match unless 4-char given)
    "ihd_mi": ["I20", "I21", "I22", "I23", "I24", "I25"],
    "af": ["I48"],
    "hypertension": HTN_ICD,
    "diabetes": ["E10", "E11", "E12", "E13", "E14"],
    "ckd": ["N18", "N19", "I12", "I13"],
    "stroke": ["I60", "I61", "I63", "I64", "G45"],
    "copd_asthma": ["J43", "J44", "J45", "J46"],
    "pad": ["I70", "I739", "I74"],
    "valve": ["I05", "I06", "I07", "I08", "I34", "I35", "I36", "I37", "Z952"],
    "hf": ["I50"],
}
OUT_CODES = {"mi": ["I21", "I22"], "stroke": ["I60", "I61", "I63", "I64"], "hf": ["I50"],
             "stroke_se": ["I60", "I61", "I63", "I64", "I74"]}
NCO = {"cataract": ["H25", "H26"], "inguinal_hernia": ["K40"], "cholelithiasis": ["K80"]}


def classes_of(name):
    """Return the set of classes a coding-4 meaning belongs to."""
    s = name.lower()
    out = {k for k, r in CLASS_RE.items() if r.search(s)}
    if "bb_other" in out and not re.search(r"timolol|betaxolol|carteolol|levobunolol|metipranolol|" + EYE, s):
        out.add("bb_other_systemic")
    return out


def rx_tokens(name):
    """Coding-4 meaning -> lower-case ingredient tokens (combination products split on '+')."""
    s = name.lower()
    s = re.sub(r"\[.*?\]|\(.*?\)", " ", s)
    toks = []
    for part in s.split("+"):
        part = re.split(r"\s\d|\s[\d.]+(mg|mcg|microgram|%|g|ml|unit)", " " + part.strip())[0].strip()
        part = re.sub(r"\b(tablet|capsule|m/r|e/c|product|sodium|potassium|hydrochloride|hcl|maleate|fumarate|besilate|"
                      r"cilexetil|medoxomil|mesilate|calcium|succinate|tartrate)\b", " ", part)
        part = re.sub(r"[^a-z0-9]+", "_", part).strip("_")
        if part:
            toks.append(part)
    return toks
