"""
scripts/cohort_utils.py

Shared helpers for the multi-trial RCT emulation pipeline (ecg-tte).

Key functions:
  load_trial_config / validate_config — load & validate per-trial YAML configs
  identify_arms_generic               — config-driven new-user arm identification
  compute_adherence_metrics_generic   — config-driven refill / adherence metrics
  build_composite_endpoint            — composite endpoint builder (mortality +
                                        inpatient_icd + condition_icd + procedure)
  load_visit_occurrence               — OMOP visit_occurrence shard loader
  load_procedure_occurrence           — OMOP procedure_occurrence shard loader
  conds_within                        — ICD-prefix window filter (person_id set)

Backward-compat wrappers (COMET output byte-identical):
  identify_arms_naive_new_user        — wraps identify_arms_generic with COMET spec
  compute_adherence_metrics           — wraps compute_adherence_metrics_generic

Changelog vs legacy version:
  1. identify_arms_naive_new_user() now wraps a generic function; COMET output unchanged.
  2. compute_adherence_metrics() now wraps a generic function; COMET output unchanged.
  3. load_conditions_with_dates() optionally keeps visit_occurrence_id when present.
  4. add_comorbidities() accepts optional `keys` list to filter which flags are computed.
  5. conds_within() added as a public export (moved from stage1_build_pool.py).
  6. New OMOP loaders: load_visit_occurrence, load_procedure_occurrence.
  7. New config machinery: KEYWORD_REGISTRY, MEDICATION_KEYWORDS, load_trial_config,
     validate_config, resolve_keywords.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml
from tqdm import tqdm

# ── ICD-10 prefix constants ────────────────────────────────────────────────────
ICD_HFREF       = ["I502"]
ICD_MI_ACS      = ["I21", "I22", "I24"]
ICD_HEART_BLOCK = ["I441", "I442", "I443"]   # 4-char: 2nd/3rd degree + bifascicular
ICD_COPD        = ["J44"]
ICD_CKD_SEVERE  = ["N185", "N186"]
ICD_LIVER       = ["K72"]
ICD_HF          = ["I50"]
ICD_REVASC      = ["Z951", "Z955"]
ICD_VALVULAR    = ["I05", "I06", "I07", "I08", "I09", "I34", "I35", "I36", "I37",
                    "I38", "I39"]
ICD_ASTHMA      = ["J45"]
ICD_ESRD            = ["N185", "N186"]
ICD_ANGIOEDEMA      = ["T783", "T886"]        # 4-char (T78.3, T88.6)
ICD_CKD_STAGE4_PLUS = ["N184", "N185", "N186"]  # 4-char; CKD stage 4+ (eGFR<30)
ICD_LVH             = ["I517", "I513", "I515"]  # cardiomegaly/structural proxy

# ── Drug keyword constants ─────────────────────────────────────────────────────
CARVEDILOL   = ["CARVEDILOL"]
METOPROLOL   = ["METOPROLOL"]
BISOPROLOL   = ["BISOPROLOL"]
ACEI_KEYWORDS = [
    "LISINOPRIL", "ENALAPRIL", "RAMIPRIL", "CAPTOPRIL",
    "PERINDOPRIL", "QUINAPRIL", "FOSINOPRIL", "BENAZEPRIL",
    "TRANDOLAPRIL", "MOEXIPRIL",
]
ARB_KEYWORDS = [
    "LOSARTAN", "VALSARTAN", "CANDESARTAN", "IRBESARTAN",
    "TELMISARTAN", "OLMESARTAN", "AZILSARTAN", "EPROSARTAN",
]
CCB_NONDIHYDRO      = ["VERAPAMIL", "DILTIAZEM"]
OTHER_BB            = [
    "BISOPROLOL", "ATENOLOL", "PROPRANOLOL", "NEBIVOLOL",
    "LABETALOL", "ACEBUTOLOL", "PINDOLOL", "NADOLOL",
]
LOOP_DIURETICS      = ["FUROSEMIDE", "TORSEMIDE", "BUMETANIDE", "ETHACRYNIC"]
ALDOSTERONE_ANTAG   = ["SPIRONOLACTONE", "EPLERENONE"]
DIGOXIN             = ["DIGOXIN"]
STATIN              = ["ATORVASTATIN", "ROSUVASTATIN", "SIMVASTATIN", "PRAVASTATIN",
                        "LOVASTATIN", "FLUVASTATIN", "PITAVASTATIN"]
NITRATE             = ["NITROGLYCERIN", "ISOSORBIDE"]
SGLT2I              = [
    "EMPAGLIFLOZIN", "DAPAGLIFLOZIN", "CANAGLIFLOZIN",
    "ERTUGLIFLOZIN", "SOTAGLIFLOZIN", "BEXAGLIFLOZIN",
]
WARFARIN            = ["WARFARIN"]
DOAC                = ["APIXABAN", "RIVAROXABAN", "DABIGATRAN", "EDOXABAN"]
APIXABAN            = ["APIXABAN"]
RIVAROXABAN         = ["RIVAROXABAN"]
DABIGATRAN          = ["DABIGATRAN"]
ANTIPLATELET        = ["CLOPIDOGREL", "PRASUGREL", "TICAGRELOR", "ASPIRIN"]
P2Y12               = ["CLOPIDOGREL", "PRASUGREL", "TICAGRELOR"]
ASPIRIN             = ["ASPIRIN"]
SACUBITRIL_VALSARTAN = ["SACUBITRIL", "ENTRESTO", "VYMADA"]
IVABRADINE          = ["IVABRADINE"]
GLP1RA              = ["SEMAGLUTIDE", "LIRAGLUTIDE", "DULAGLUTIDE", "EXENATIDE",
                        "ALBIGLUTIDE", "EFPEGLENATIDE"]
INSULIN             = ["INSULIN"]
PCSK9I              = ["EVOLOCUMAB", "ALIROCUMAB"]
EZETIMIBE           = ["EZETIMIBE"]
TICAGRELOR          = ["TICAGRELOR"]
CLOPIDOGREL         = ["CLOPIDOGREL"]
PRASUGREL           = ["PRASUGREL"]
AMIODARONE          = ["AMIODARONE"]
DOFETILIDE          = ["DOFETILIDE"]
DRONEDARONE         = ["DRONEDARONE"]
RIOCIGUAT           = ["RIOCIGUAT"]
SACUBITRIL          = ["SACUBITRIL"]
ENALAPRIL           = ["ENALAPRIL"]
TOLVAPTAN           = ["TOLVAPTAN"]
ROSUVASTATIN        = ["ROSUVASTATIN"]
EMPAGLIFLOZIN       = ["EMPAGLIFLOZIN"]
DAPAGLIFLOZIN       = ["DAPAGLIFLOZIN"]
CANAGLIFLOZIN       = ["CANAGLIFLOZIN"]

COMORBIDITY_ICD = {
    "copd":           ["J44"],
    "htn":            ["I10"],
    "dm":             ["E10", "E11"],
    "cad_mi":         ["I21", "I22", "I25"],
    "afib":           ["I48"],
    "hyperlipidemia": ["E78"],
    "stroke":         ["I63", "G45"],
}

EF_MIN, EF_MAX = 10.0, 80.0

# ── Keyword registry — resolve YAML keyword_const references ──────────────────
KEYWORD_REGISTRY: dict[str, list[str]] = {
    "CARVEDILOL":        CARVEDILOL,
    "METOPROLOL":        METOPROLOL,
    "BISOPROLOL":        BISOPROLOL,
    "ACEI_KEYWORDS":     ACEI_KEYWORDS,
    "ARB_KEYWORDS":      ARB_KEYWORDS,
    "CCB_NONDIHYDRO":    CCB_NONDIHYDRO,
    "OTHER_BB":          OTHER_BB,
    "LOOP_DIURETICS":    LOOP_DIURETICS,
    "ALDOSTERONE_ANTAG": ALDOSTERONE_ANTAG,
    "DIGOXIN":           DIGOXIN,
    "STATIN":            STATIN,
    "NITRATE":           NITRATE,
    "SGLT2I":            SGLT2I,
    "WARFARIN":          WARFARIN,
    "DOAC":              DOAC,
    "APIXABAN":          APIXABAN,
    "RIVAROXABAN":       RIVAROXABAN,
    "DABIGATRAN":        DABIGATRAN,
    "ANTIPLATELET":      ANTIPLATELET,
    "P2Y12":             P2Y12,
    "ASPIRIN":           ASPIRIN,
    "SACUBITRIL_VALSARTAN": SACUBITRIL_VALSARTAN,
    "IVABRADINE":        IVABRADINE,
    "GLP1RA":            GLP1RA,
    "INSULIN":           INSULIN,
    "PCSK9I":            PCSK9I,
    "EZETIMIBE":         EZETIMIBE,
    "TICAGRELOR":        TICAGRELOR,
    "CLOPIDOGREL":       CLOPIDOGREL,
    "PRASUGREL":         PRASUGREL,
    "AMIODARONE":        AMIODARONE,
    "DOFETILIDE":        DOFETILIDE,
    "DRONEDARONE":       DRONEDARONE,
    "RIOCIGUAT":         RIOCIGUAT,
    "SACUBITRIL":        SACUBITRIL,
    "ENALAPRIL":         ENALAPRIL,
    "TOLVAPTAN":         TOLVAPTAN,
    "ROSUVASTATIN":      ROSUVASTATIN,
    "EMPAGLIFLOZIN":     EMPAGLIFLOZIN,
    "DAPAGLIFLOZIN":     DAPAGLIFLOZIN,
    "CANAGLIFLOZIN":     CANAGLIFLOZIN,
}

# Map medication group name → keyword list (for add_medication_flags_generic)
MEDICATION_KEYWORDS: dict[str, list[str]] = {
    "loop_diuretic":     LOOP_DIURETICS,
    "acei_arb":          ACEI_KEYWORDS + ARB_KEYWORDS,
    "acei":              ACEI_KEYWORDS,
    "arb":               ARB_KEYWORDS,
    "aldosterone_antag": ALDOSTERONE_ANTAG,
    "digoxin":           DIGOXIN,
    "statin":            STATIN,
    "nitrate":           NITRATE,
    "sglt2i":            SGLT2I,
    "beta_blocker":      CARVEDILOL + METOPROLOL + OTHER_BB,
    "warfarin":          WARFARIN,
    "doac":              DOAC,
    "antiplatelet":      ANTIPLATELET,
    "aspirin":           ASPIRIN,
    "p2y12":             P2Y12,
    "pcsk9i":            PCSK9I,
    "ezetimibe":         EZETIMIBE,
    "ticagrelor":        TICAGRELOR,
    "clopidogrel":       CLOPIDOGREL,
    "prasugrel":         PRASUGREL,
    "glp1ra":            GLP1RA,
    "insulin":           INSULIN,
    "amiodarone":        AMIODARONE,
    "dronedarone":       DRONEDARONE,
    "dofetilide":        DOFETILIDE,
}

# COMET arm spec (used by backward-compat wrappers)
COMET_ARMS_SPEC: list[dict] = [
    {"name": "carvedilol", "role": "treated", "keywords": CARVEDILOL,
     "stage3_alias": "carv"},
    {"name": "metoprolol", "role": "control", "keywords": METOPROLOL,
     "stage3_alias": "meto"},
]


# ── Core helpers ──────────────────────────────────────────────────────────────

def icd_prefix(code: str, n: int = 3) -> str:
    return str(code).replace(".", "").strip()[:n]


def drug_mask(series: pd.Series, keywords: list[str]) -> pd.Series:
    """Vectorized keyword match — ~100x faster than apply+any for long lists."""
    pattern = "|".join(keywords)
    return series.str.contains(pattern, regex=True, na=False)


def safe_hr_from_rr(rr: pd.Series) -> pd.Series:
    """HR = 60000 / RR_Interval(ms). Returns NaN for RR ≤ 0."""
    rr = pd.to_numeric(rr, errors="coerce")
    return (60000.0 / rr.where(rr > 0)).round(1)


def pid_mrn_maps(df: pd.DataFrame) -> tuple[dict, dict]:
    """Return (pid→mrn, mrn→pid) dicts from a DataFrame with both columns."""
    pid2mrn = dict(zip(df["person_id"].astype(str), df["MRN"].astype(str)))
    mrn2pid = {v: k for k, v in pid2mrn.items()}
    return pid2mrn, mrn2pid


# ── Config loader ─────────────────────────────────────────────────────────────

def load_trial_config(config_path: str) -> dict:
    """Load and validate a per-trial YAML config. Raises ValueError on invalid."""
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    """Raise ValueError if config is missing required keys or has invalid values."""
    for section in ["trial", "design", "arms", "endpoint", "ecg"]:
        if section not in cfg:
            raise ValueError(f"Config missing required section: {section!r}")

    for key in ["key", "name"]:
        if key not in cfg["trial"]:
            raise ValueError(f"Config trial.{key} is required")

    arms = cfg["arms"]
    if not isinstance(arms, list) or len(arms) < 2:
        raise ValueError("Config arms must be a list of at least 2 entries")
    arm_names = [a.get("name") for a in arms]
    if len(set(arm_names)) != len(arm_names):
        raise ValueError(f"Config arms must have unique names. Got: {arm_names}")
    roles = [a.get("role") for a in arms]
    if roles.count("treated") != 1:
        raise ValueError(f"Exactly one arm must have role: treated. Got: {roles}")
    for arm in arms:
        if not arm.get("keywords"):
            raise ValueError(f"Arm {arm.get('name')!r} must have a non-empty keywords list")

    ecg_window = cfg["ecg"].get("window_days")
    if ecg_window is None or ecg_window >= 90:
        raise ValueError(f"ecg.window_days must be < 90. Got: {ecg_window}")

    ef = cfg.get("inclusion", {}).get("ef", {})
    if ef and ef.get("direction") not in (None, "<=", ">="):
        raise ValueError(f"inclusion.ef.direction must be '<=' or '>='. Got: {ef.get('direction')!r}")

    endpoint = cfg["endpoint"].get("primary", {})
    if not endpoint.get("components"):
        raise ValueError("endpoint.primary.components must be a non-empty list")
    valid_types = {"mortality", "inpatient_icd", "condition_icd", "procedure"}
    for comp in endpoint["components"]:
        ct = comp.get("type")
        if ct not in valid_types:
            raise ValueError(f"Unknown endpoint component type: {ct!r}. Must be one of {valid_types}")


def resolve_keywords(
    keywords_or_const,
    registry: Optional[dict] = None,
) -> list[str]:
    """
    Resolve a YAML keywords / keyword_const value to a flat list of strings.

    Accepts:
      - A list of strings: returned as-is (no registry lookup)
      - A list of mixed strings + registry keys: registry keys expanded
      - A string: looked up in registry; if not found treated as single keyword
      - None / empty: returns []
    """
    if registry is None:
        registry = KEYWORD_REGISTRY

    if keywords_or_const is None:
        return []

    if isinstance(keywords_or_const, str):
        return list(registry.get(keywords_or_const, [keywords_or_const]))

    if isinstance(keywords_or_const, list):
        result: list[str] = []
        for item in keywords_or_const:
            if isinstance(item, str):
                if item in registry:
                    result.extend(registry[item])
                else:
                    result.append(item)
        return result

    return []


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_conditions_with_dates(
    condition_dir: str, person_ids: set
) -> pd.DataFrame:
    """
    Load condition_occurrence shards; keeps condition_source_value for 4-char ICD.
    Also keeps visit_occurrence_id when present (for inpatient-gated endpoints).
    COMET is unaffected: it never reads visit_occurrence_id.
    """
    person_ids_str = {str(p) for p in person_ids}
    frames = []
    for shard in tqdm(sorted(Path(condition_dir).glob("condition_occurrence*.parquet")),
                      desc="Condition shards"):
        try:
            # Try to read with visit_occurrence_id
            try:
                df = pd.read_parquet(
                    shard,
                    columns=["person_id", "condition_source_value",
                             "condition_start_date", "visit_occurrence_id"],
                )
            except Exception:
                df = pd.read_parquet(
                    shard,
                    columns=["person_id", "condition_source_value",
                             "condition_start_date"],
                )
        except Exception:
            continue
        df["person_id"] = df["person_id"].astype(str)
        df = df[df["person_id"].isin(person_ids_str)]
        if df.empty:
            continue
        df["_pfx"]  = df["condition_source_value"].apply(lambda v: icd_prefix(str(v), 3))
        df["_pfx4"] = df["condition_source_value"].apply(lambda v: icd_prefix(str(v), 4))
        df["cond_date"] = pd.to_datetime(df["condition_start_date"], errors="coerce")
        keep = ["person_id", "condition_source_value", "_pfx", "_pfx4", "cond_date"]
        if "visit_occurrence_id" in df.columns:
            keep.append("visit_occurrence_id")
        frames.append(df[keep].dropna(subset=["cond_date"]))
    if not frames:
        return pd.DataFrame(
            columns=["person_id", "condition_source_value", "_pfx", "_pfx4", "cond_date"]
        )
    return pd.concat(frames, ignore_index=True)


def load_visit_occurrence(
    visit_dir: str,
    person_ids: set,
) -> pd.DataFrame:
    """
    Load OMOP visit_occurrence shards.
    Returns: person_id, visit_concept_id, visit_start_date, visit_end_date,
             visit_occurrence_id
    """
    person_ids_str = {str(p) for p in person_ids}
    frames = []
    for shard in tqdm(sorted(Path(visit_dir).glob("visit_occurrence*.parquet")),
                      desc="Visit shards"):
        try:
            df = pd.read_parquet(
                shard,
                columns=["person_id", "visit_concept_id", "visit_start_date",
                         "visit_end_date", "visit_occurrence_id"],
            )
        except Exception:
            continue
        df["person_id"] = df["person_id"].astype(str)
        df = df[df["person_id"].isin(person_ids_str)]
        if df.empty:
            continue
        df["visit_start_date"] = pd.to_datetime(df["visit_start_date"], errors="coerce")
        df["visit_end_date"]   = pd.to_datetime(df["visit_end_date"],   errors="coerce")
        frames.append(df.dropna(subset=["visit_start_date"]))
    if not frames:
        return pd.DataFrame(
            columns=["person_id", "visit_concept_id", "visit_start_date",
                     "visit_end_date", "visit_occurrence_id"],
        )
    return pd.concat(frames, ignore_index=True)


def load_procedure_occurrence(
    proc_dir: str,
    person_ids: set,
) -> pd.DataFrame:
    """
    Load OMOP procedure_occurrence shards.
    Returns: person_id, procedure_concept_id, procedure_source_value, procedure_date
    """
    person_ids_str = {str(p) for p in person_ids}
    frames = []
    for shard in tqdm(sorted(Path(proc_dir).glob("procedure_occurrence*.parquet")),
                      desc="Procedure shards"):
        try:
            df = pd.read_parquet(
                shard,
                columns=["person_id", "procedure_concept_id",
                         "procedure_source_value", "procedure_date"],
            )
        except Exception:
            continue
        df["person_id"] = df["person_id"].astype(str)
        df = df[df["person_id"].isin(person_ids_str)]
        if df.empty:
            continue
        df["procedure_date"] = pd.to_datetime(df["procedure_date"], errors="coerce")
        frames.append(df.dropna(subset=["procedure_date"]))
    if not frames:
        return pd.DataFrame(
            columns=["person_id", "procedure_concept_id",
                     "procedure_source_value", "procedure_date"],
        )
    return pd.concat(frames, ignore_index=True)


def load_drug_master(drug_master_path: str,
                     mrns: Optional[set] = None) -> pd.DataFrame:
    """
    Load drug master, filtering to mrns during load (chunked) to minimise peak RAM.
    Reads one 500k-row batch at a time; only matching rows accumulate in memory.
    """
    import pyarrow.parquet as pq

    raw_schema  = pq.read_schema(drug_master_path)
    # Strip whitespace from schema names for consistent lookup
    avail_lower = {c.lower().strip(): c.strip() for c in raw_schema.names}

    REQUIRED = ["MRN", "drug_name"]
    OPTIONAL = ["order_date", "start_date", "end_date", "discontinue_date",
                "discontinue_reason", "order_status", "frequency", "dose", "dose_unit"]
    OPTIONAL_DATE = {"end_date", "discontinue_date"}

    cols_to_read = []
    for c in REQUIRED:
        match = avail_lower.get(c.lower())
        if match:
            cols_to_read.append(match)
    for c in OPTIONAL:
        match = avail_lower.get(c.lower())
        if match:
            cols_to_read.append(match)

    # Detect column roles from schema — no data read yet
    mrn_col  = avail_lower.get("mrn")
    drug_col = avail_lower.get("drug_name")
    if mrn_col is None or drug_col is None:
        raise ValueError(f"drug_master missing MRN or drug_name. Found: {list(avail_lower.values())}")

    date_col = avail_lower.get("order_date") or avail_lower.get("start_date")

    optional_keep: list[str] = [
        avail_lower[c] for c in ["end_date", "discontinue_date", "discontinue_reason",
                                   "order_status", "frequency", "dose", "dose_unit"]
        if c in avail_lower
    ]

    mrns_set = {str(m) for m in mrns} if mrns is not None else None

    chunks: list[pd.DataFrame] = []
    for batch in pq.ParquetFile(drug_master_path).iter_batches(
        batch_size=500_000, columns=cols_to_read
    ):
        chunk = batch.to_pandas()
        chunk.columns = [c.strip() for c in chunk.columns]

        chunk["MRN"]        = chunk[mrn_col].astype(str).str.strip()
        chunk["drug_upper"] = chunk[drug_col].astype(str).str.upper()
        chunk["_date"]      = (pd.to_datetime(chunk[date_col], errors="coerce")
                               if date_col else pd.NaT)

        if mrns_set is not None:
            chunk = chunk[chunk["MRN"].isin(mrns_set)]

        chunk = chunk.dropna(subset=["_date"])
        if chunk.empty:
            continue

        keep = ["MRN", "drug_upper", "_date"]
        for c, orig in [(c, avail_lower[c]) for c in ["end_date", "discontinue_date",
                         "discontinue_reason", "order_status", "frequency",
                         "dose", "dose_unit"] if c in avail_lower]:
            if orig in chunk.columns:
                if c in OPTIONAL_DATE:
                    chunk[orig] = pd.to_datetime(chunk[orig], errors="coerce")
                keep.append(orig)

        chunks.append(chunk[keep])

    if not chunks:
        return pd.DataFrame(columns=["MRN", "drug_upper", "_date"] + optional_keep)

    return pd.concat(chunks, ignore_index=True)


def load_ecg_meta(ecg_meta_path: str, mrns: Optional[set] = None) -> pd.DataFrame:
    """
    Load ECG metadata including fileID and extended interval/voltage columns.
    Required: MRN, fileID, ECGDate, RR_Interval, PR_Interval, QRS_Duration
    Optional (kept if present): QTc, QT_Interval, QRS_Axis, P_Axis, T_Axis
    Prints available columns on first call for cluster verification.
    """
    meta = pd.read_parquet(ecg_meta_path)
    orig_cols = list(meta.columns)
    print(f"  [load_ecg_meta] available columns: {orig_cols}")

    fid_col  = next((c for c in orig_cols if c == "fileID"),
                    next((c for c in orig_cols if c.lower() == "fileid"), None))
    mrn_col  = next((c for c in orig_cols if c.lower() == "mrn"), None)
    date_col = next((c for c in orig_cols if "ecg" in c.lower() and "date" in c.lower()),
                    next((c for c in orig_cols if "date" in c.lower()), None))

    if not all([mrn_col, date_col]):
        raise ValueError(f"ECG meta missing required cols. Found: {orig_cols}")

    meta["MRN"]     = meta[mrn_col].astype(str).str.strip()
    meta["ECGDate"] = pd.to_datetime(meta[date_col], errors="coerce")

    for col in ["RR_Interval", "PR_Interval", "QRS_Duration"]:
        if col in meta.columns:
            meta[col] = pd.to_numeric(meta[col], errors="coerce")

    if "QTc_Interval" in meta.columns:
        meta["QTc"] = pd.to_numeric(meta["QTc_Interval"], errors="coerce")
    for col in ["QT_Interval", "QRS_Axis", "P_Axis", "T_Axis"]:
        if col in meta.columns:
            meta[col] = pd.to_numeric(meta[col], errors="coerce")

    if fid_col:
        meta["fileID"] = meta[fid_col].astype(str).str.replace(".npy", "", regex=False)
    else:
        meta["fileID"] = meta.index.astype(str)

    if mrns is not None:
        meta = meta[meta["MRN"].isin(mrns)]

    keep = ["MRN", "fileID", "ECGDate"] + [
        c for c in ["RR_Interval", "PR_Interval", "QRS_Duration",
                    "QTc", "QT_Interval", "QRS_Axis", "P_Axis", "T_Axis"]
        if c in meta.columns
    ]
    return meta[keep].dropna(subset=["ECGDate"])


def load_echo_meta(echo_meta_path: str, mrns: Optional[set] = None) -> pd.DataFrame:
    """
    Load echo metadata with EF values.
    Returns: MRN, EchoDate, EF (filtered to EF_MIN..EF_MAX range).
    """
    echo = pd.read_parquet(echo_meta_path)
    mrn_col  = next((c for c in echo.columns if c.lower() == "mrn"), None)
    date_col = next((c for c in echo.columns if "echo" in c.lower() and "date" in c.lower()),
                    next((c for c in echo.columns if "date" in c.lower()), None))
    ef_col   = next((c for c in echo.columns if c.upper() == "EF" or c.lower() == "ef"), None)
    if not all([mrn_col, date_col, ef_col]):
        raise ValueError(f"Echo meta missing required cols. Found: {list(echo.columns)}")

    echo["MRN"]      = echo[mrn_col].astype(str).str.strip()
    echo["EchoDate"] = pd.to_datetime(echo[date_col], errors="coerce")
    echo["EF"]       = pd.to_numeric(echo[ef_col], errors="coerce")
    echo = echo[(echo["EF"] >= EF_MIN) & (echo["EF"] <= EF_MAX)].dropna(
        subset=["EchoDate", "EF"]
    )
    if mrns is not None:
        echo = echo[echo["MRN"].isin(mrns)]
    return echo[["MRN", "EchoDate", "EF"]]


def load_death(death_parquet: str, person_ids: Optional[set] = None) -> pd.DataFrame:
    death = pd.read_parquet(death_parquet)
    death.columns = [c.lower().strip() for c in death.columns]
    death = death.loc[:, ~death.columns.duplicated()]
    date_col = next((c for c in death.columns if "date" in c), None)
    death["death_date"] = pd.to_datetime(death[date_col], errors="coerce")
    death["person_id"]  = death["person_id"].astype(str)
    death = death[["person_id", "death_date"]].dropna()
    if person_ids is not None:
        person_ids_str = {str(p) for p in person_ids}
        death = death[death["person_id"].isin(person_ids_str)]
    return death


# ── Person table ──────────────────────────────────────────────────────────────

def parse_person_table(person_parquet: str) -> pd.DataFrame:
    """
    Load OMOP person table; extract MRN, person_id, birth_date, sex, race_black.
    Reads only needed columns to minimise memory.
    """
    import pyarrow.parquet as pq

    raw_schema = pq.read_schema(person_parquet)
    avail_lower = {c.lower().strip(): c for c in raw_schema.names}

    WANT = [
        "person_id",
        "birth_datetime", "year_of_birth",
        "gender_concept_id", "gender_source_value",
        "race_concept_id", "race_source_value",
    ]
    # MRN-like columns
    mrn_candidates = [orig for low, orig in avail_lower.items()
                      if "mrn" in low or "source_value" in low]
    cols_to_read = list({
        avail_lower[c] for c in WANT if c in avail_lower
    } | set(mrn_candidates))

    person = pd.read_parquet(person_parquet, columns=cols_to_read)
    person.columns = [c.lower().strip() for c in person.columns]
    person = person.loc[:, ~person.columns.duplicated()]

    mrn_col = next((c for c in person.columns if "mrn" in c or "source_value" in c), None)
    if mrn_col is None:
        raise ValueError(f"person table has no MRN-like column. Found: {list(person.columns)}")
    person["MRN"] = person[mrn_col].astype(str).str.strip()

    if "birth_datetime" in person.columns:
        person["birth_date"] = pd.to_datetime(person["birth_datetime"], errors="coerce")
    elif "year_of_birth" in person.columns:
        person["birth_date"] = pd.to_datetime(
            person["year_of_birth"].astype(str) + "-07-01", errors="coerce"
        )
    else:
        person["birth_date"] = pd.NaT

    gender_col = next((c for c in person.columns if "gender" in c), None)
    if gender_col:
        person["sex"] = person[gender_col].astype(str).str.upper().map(
            lambda v: "F" if ("F" in v or "8532" in v) else "M"
        )
    else:
        person["sex"] = "M"

    race_concept_col = next((c for c in person.columns if c == "race_concept_id"), None)
    race_source_col  = next((c for c in person.columns if "race_source" in c), None)
    if race_concept_col:
        person["race_black"] = (person[race_concept_col].astype(str) == "8516").astype(int)
    elif race_source_col:
        person["race_black"] = (
            person[race_source_col].astype(str).str.upper()
            .str.contains(r"BLACK|AFRICAN", na=False)
        ).astype(int)
    else:
        person["race_black"] = 0

    return person[["person_id", "MRN", "birth_date", "sex", "race_black"]]


# ── ICD window filter ─────────────────────────────────────────────────────────

def conds_within(
    conditions: pd.DataFrame,
    prefixes: list[str],
    idx_df: pd.DataFrame,          # person_id, index_date
    days_before: int,
    days_after: int = 0,
    use_4char: bool = False,
) -> set:
    """
    Return person_ids with any of the given ICD prefixes within the time window
    [index_date - days_before, index_date + days_after].
    """
    pfx_col = "_pfx4" if use_4char else "_pfx"
    sub = conditions[conditions[pfx_col].isin(prefixes)].copy()
    sub["person_id"] = sub["person_id"].astype(str)
    sub = sub.merge(
        idx_df.assign(person_id=idx_df["person_id"].astype(str)),
        on="person_id",
    )
    lo = sub["index_date"] - pd.Timedelta(days=days_before)
    hi = sub["index_date"] + pd.Timedelta(days=days_after)
    mask = (sub["cond_date"] >= lo) & (sub["cond_date"] <= hi)
    return set(sub.loc[mask, "person_id"].unique())


# ── Arm identification ────────────────────────────────────────────────────────

def identify_arms_generic(
    drug_master: pd.DataFrame,
    arms_spec: list[dict],
    index_definition: str = "first_ever_arm_dispense",
) -> pd.DataFrame:
    """
    Generic arm identification for two-or-more-arm trials.

    arms_spec: list of dicts, each with:
      name:               str  (becomes arm column value and column-name prefix)
      role:               "treated" | "control"
      keywords:           list[str]  (already resolved to flat keyword list)
      formulation_filter: optional dict {require: [...], exclude: [...]}
      stage3_alias:       optional str  (for backward-compat alias columns)

    Arm assignment: patient assigned to the arm whose first dispense is earliest.
    Ties broken by arms_spec list order (first = treated arm wins).

    Returns columns: MRN, arm, index_date,
                     first_{name}_date  (one per arm)
                     prior_{other_name}_days  (one per arm × other arms)
    Plus any stage3_alias columns, e.g. first_carv_date, prior_meto_days.
    """
    if index_definition != "first_ever_arm_dispense":
        raise NotImplementedError(
            f"index_definition={index_definition!r} not supported. "
            "Only 'first_ever_arm_dispense' is implemented."
        )

    dm = drug_master[["MRN", "drug_upper", "_date"]].copy()
    arm_names = [a["name"] for a in arms_spec]

    # ── Per-arm first-dispense date ────────────────────────────────────────────
    arm_records: dict[str, pd.DataFrame] = {}   # name → {MRN, {name}_date}
    first_dfs: list[pd.DataFrame] = []

    for arm in arms_spec:
        name = arm["name"]
        keywords = arm["keywords"]
        mask = drug_mask(dm["drug_upper"], keywords)

        ff = arm.get("formulation_filter") or {}
        if ff.get("require"):
            mask = mask & drug_mask(dm["drug_upper"], ff["require"])
        if ff.get("exclude"):
            mask = mask & ~drug_mask(dm["drug_upper"], ff["exclude"])

        rel = dm[mask].copy()
        arm_records[name] = rel[["MRN", "_date"]].rename(
            columns={"_date": f"{name}_date"}
        )
        first = (rel.groupby("MRN")["_date"]
                 .min()
                 .rename(f"first_{name}")
                 .reset_index())
        first_dfs.append(first)

    if not first_dfs:
        empty_cols = (
            ["MRN", "arm", "index_date"] +
            [f"first_{n}_date" for n in arm_names] +
            [f"prior_{n}_days" for n in arm_names]
        )
        return pd.DataFrame(columns=empty_cols)

    # Outer-merge all per-arm first-dispense tables on MRN
    merged = first_dfs[0]
    for fd in first_dfs[1:]:
        merged = merged.merge(fd, on="MRN", how="outer")

    # ── Arm assignment via idxmin ──────────────────────────────────────────────
    first_cols = [f"first_{n}" for n in arm_names]
    date_matrix = merged[first_cols].copy()
    for col in date_matrix.columns:
        date_matrix[col] = pd.to_datetime(date_matrix[col], errors="coerce")

    # Keep only patients with ≥1 non-NaT dispense
    has_any = date_matrix.notna().any(axis=1)
    merged = merged[has_any].copy()
    date_matrix = date_matrix[has_any]

    if merged.empty:
        empty_cols = (
            ["MRN", "arm", "index_date"] +
            [f"first_{n}_date" for n in arm_names] +
            [f"prior_{n}_days" for n in arm_names]
        )
        return pd.DataFrame(columns=empty_cols)

    # idxmin: ties go to first column = first arm in list = treated arm (matches COMET)
    min_col = date_matrix.idxmin(axis=1)      # e.g. "first_carvedilol"
    merged["arm"]        = min_col.str.replace("first_", "", n=1)
    merged["index_date"] = date_matrix.min(axis=1)

    # Rename first_{name} → first_{name}_date
    merged = merged.rename(columns={f"first_{n}": f"first_{n}_date" for n in arm_names})

    result = merged[["MRN", "arm", "index_date"] +
                    [f"first_{n}_date" for n in arm_names]].copy()

    # ── Prior-exposure days (OTHER arm dispenses before index) ────────────────
    prior_data: dict[str, dict] = {}  # col_name → {MRN: days}

    for arm_name in arm_names:
        arm_patients = result[result["arm"] == arm_name][["MRN", "index_date"]].copy()
        if arm_patients.empty:
            continue
        for other_name in arm_names:
            if other_name == arm_name:
                continue
            col = f"prior_{other_name}_days"
            other_recs = arm_records.get(other_name, pd.DataFrame())
            if other_recs.empty:
                continue

            joined = arm_patients.merge(
                other_recs.rename(columns={f"{other_name}_date": "_other_date"}),
                on="MRN",
                how="inner",
            )
            before = joined[joined["_other_date"] < joined["index_date"]]
            if before.empty:
                continue

            latest = (before.groupby("MRN")["_other_date"].max().reset_index())
            latest = latest.merge(arm_patients[["MRN", "index_date"]], on="MRN")
            latest[col] = (latest["index_date"] - latest["_other_date"]).dt.days
            prior_data.setdefault(col, {}).update(dict(zip(latest["MRN"], latest[col])))

    for col, mapping in prior_data.items():
        result[col] = result["MRN"].map(mapping)

    # Ensure all prior columns exist (NaN for arms without prior exposure data)
    for n in arm_names:
        col = f"prior_{n}_days"
        if col not in result.columns:
            result[col] = np.nan

    # ── Stage 3 alias columns ─────────────────────────────────────────────────
    for arm in arms_spec:
        alias = arm.get("stage3_alias")
        if not alias:
            continue
        name = arm["name"]
        alias_map = [
            (f"first_{name}_date", f"first_{alias}_date"),
            (f"prior_{name}_days", f"prior_{alias}_days"),
        ]
        for src, dst in alias_map:
            if src in result.columns and dst not in result.columns:
                result[dst] = result[src]

    return result


def identify_arms_naive_new_user(drug_master: pd.DataFrame) -> pd.DataFrame:
    """
    COMET-specific wrapper. Identifies first-ever carvedilol / metoprolol initiators.
    Output is byte-identical to the original implementation.

    Returns: MRN, arm, index_date, first_carv_date, first_meto_date,
             prior_meto_days, prior_carv_days
    """
    result = identify_arms_generic(drug_master, COMET_ARMS_SPEC)
    if result.empty:
        return pd.DataFrame(
            columns=["MRN", "arm", "index_date", "first_carv_date", "first_meto_date",
                     "prior_meto_days", "prior_carv_days"]
        )
    keep = [c for c in [
        "MRN", "arm", "index_date",
        "first_carv_date", "first_meto_date",
        "prior_meto_days", "prior_carv_days",
    ] if c in result.columns]
    return result[keep]


# ── Drug adherence ────────────────────────────────────────────────────────────

def compute_adherence_metrics_generic(
    drug_master: pd.DataFrame,
    arm_df: pd.DataFrame,
    arms_spec: list[dict],
    windows: tuple[int, ...] = (90, 180, 365),
    max_followup_days: int = 1825,
    early_disc_days: int = 30,
) -> pd.DataFrame:
    """
    Generic refill counts and days_on_therapy for any trial arms_spec.

    arm_df must have: MRN, arm, index_date.
    Processes each arm independently. Does NOT drop any patients.
    """
    arm_results = []
    for arm in arms_spec:
        arm_name = arm["name"]
        kw = arm["keywords"]
        arm_sub = arm_df[arm_df["arm"] == arm_name].copy()
        if arm_sub.empty:
            continue

        mrns = set(arm_sub["MRN"])
        extra_cols = [c for c in ["discontinue_date", "discontinue_reason"]
                      if c in drug_master.columns]
        drug_recs = drug_master[
            drug_mask(drug_master["drug_upper"], kw) & drug_master["MRN"].isin(mrns)
        ][["MRN", "_date"] + extra_cols].copy()

        merged = arm_sub[["MRN", "index_date"]].merge(drug_recs, on="MRN", how="left")

        for w in windows:
            in_win = (
                (merged["_date"] >= merged["index_date"]) &
                (merged["_date"] <= merged["index_date"] + pd.Timedelta(days=w))
            )
            counts = (merged[in_win]
                      .drop_duplicates(["MRN", "_date"])
                      .groupby("MRN")
                      .size()
                      .rename(f"n_refills_assigned_{w}d")
                      .reset_index())
            arm_sub = arm_sub.merge(counts, on="MRN", how="left")
            arm_sub[f"n_refills_assigned_{w}d"] = (
                arm_sub[f"n_refills_assigned_{w}d"].fillna(0).astype(int)
            )

        in_followup = (
            (merged["_date"] >= merged["index_date"]) &
            (merged["_date"] <= merged["index_date"] + pd.Timedelta(days=max_followup_days))
        )
        last_fill = (merged[in_followup]
                     .drop_duplicates(["MRN", "_date"])
                     .groupby("MRN")["_date"]
                     .max()
                     .rename("last_fill_date")
                     .reset_index())
        arm_sub = arm_sub.merge(last_fill, on="MRN", how="left")
        arm_sub["days_on_therapy"] = (
            (arm_sub["last_fill_date"] - arm_sub["index_date"]).dt.days.clip(lower=0)
        )
        arm_sub = arm_sub.drop(columns=["last_fill_date"])

        if "discontinue_date" in merged.columns and "discontinue_reason" in merged.columns:
            disc = merged[merged["discontinue_date"].notna()].copy()
            if not disc.empty:
                disc["discontinue_date"] = pd.to_datetime(
                    disc["discontinue_date"], errors="coerce"
                )
                early = (
                    (disc["discontinue_date"] >= disc["index_date"]) &
                    (disc["discontinue_date"] <=
                     disc["index_date"] + pd.Timedelta(days=early_disc_days))
                )
                bad = disc["discontinue_reason"].astype(str).str.upper().str.contains(
                    r"ADVERSE|SIDE EFFECT|PATIENT CHOICE|PATIENT REQUEST|INTOLERAN",
                    regex=True, na=False,
                )
                early_disc_mrns = set(disc.loc[early & bad, "MRN"].unique())
                arm_sub["early_adverse_disc"] = arm_sub["MRN"].isin(early_disc_mrns).astype(int)
            else:
                arm_sub["early_adverse_disc"] = 0
        else:
            arm_sub["early_adverse_disc"] = 0

        if "discontinue_date" in drug_recs.columns:
            disc_cols = ["MRN", "discontinue_date"] + (
                ["discontinue_reason"] if "discontinue_reason" in drug_recs.columns else []
            )
            disc_info = (drug_recs[drug_recs["discontinue_date"].notna()]
                         .sort_values("discontinue_date")
                         .groupby("MRN")
                         .first()
                         .reset_index()[disc_cols])
            arm_sub = arm_sub.merge(disc_info, on="MRN", how="left")

        arm_results.append(arm_sub)

    if not arm_results:
        return arm_df.copy()
    return pd.concat(arm_results, ignore_index=True)


def compute_adherence_metrics(
    drug_master: pd.DataFrame,
    arm_df: pd.DataFrame,
    windows: tuple[int, ...] = (90, 180, 365),
    max_followup_days: int = 1825,
    early_disc_days: int = 30,
) -> pd.DataFrame:
    """COMET backward-compat wrapper — delegates to compute_adherence_metrics_generic."""
    return compute_adherence_metrics_generic(
        drug_master, arm_df, COMET_ARMS_SPEC,
        windows=windows,
        max_followup_days=max_followup_days,
        early_disc_days=early_disc_days,
    )


# ── Concurrent drug checks (end-date-aware) ───────────────────────────────────

def on_drug_at_index(
    drug_master: pd.DataFrame,
    keywords: list[str],
    mrn_to_idx: pd.DataFrame,
    window_days: int = 30,
) -> set:
    """
    Return set of MRNs with any keyword drug active within ±window_days of index.

    End-date-aware: if drug has end_date, drug is 'active' if
      start_date ≤ index + window AND (end_date NaN OR end_date ≥ index - window)
    Fallback (no end_date): order_date within [-window, +window] of index.
    Missing end_date → assumed active for 30 days from order_date.
    """
    sub = drug_master[drug_mask(drug_master["drug_upper"], keywords)].copy()
    sub = sub.merge(mrn_to_idx[["MRN", "index_date"]], on="MRN", how="inner")
    lo = sub["index_date"] - pd.Timedelta(days=window_days)
    hi = sub["index_date"] + pd.Timedelta(days=window_days)

    if "end_date" in sub.columns:
        end = pd.to_datetime(sub["end_date"], errors="coerce")
        end_effective = end.fillna(sub["_date"] + pd.Timedelta(days=30))
        active = (sub["_date"] <= hi) & (end_effective >= lo)
    else:
        active = (sub["_date"] >= lo) & (sub["_date"] <= hi)

    return set(sub.loc[active, "MRN"].unique())


# ── Covariate flags ───────────────────────────────────────────────────────────

def add_comorbidities(
    cohort: pd.DataFrame,
    conditions: pd.DataFrame,
    keys: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Add binary comorbidity flags (any time before index). No lookback window.
    keys: subset of COMORBIDITY_ICD keys to compute. Default = all.
    """
    if keys is None:
        keys = list(COMORBIDITY_ICD.keys())
    idx = cohort[["person_id", "index_date"]].copy()
    idx["person_id"] = idx["person_id"].astype(str)
    conds = conditions.copy()
    conds["person_id"] = conds["person_id"].astype(str)
    conds_before = conds.merge(idx, on="person_id")
    conds_before = conds_before[conds_before["cond_date"] < conds_before["index_date"]]

    for col in keys:
        if col not in COMORBIDITY_ICD:
            continue
        prefixes = COMORBIDITY_ICD[col]
        pids = set(conds_before[conds_before["_pfx"].isin(prefixes)]["person_id"].unique())
        cohort[col] = cohort["person_id"].astype(str).isin(pids).astype(int)
    return cohort


def add_medication_flags_generic(
    cohort: pd.DataFrame,
    drug_master: pd.DataFrame,
    med_names: list[str],
    window_days: int = 90,
) -> pd.DataFrame:
    """
    Add binary medication flags (lookback window_days before index).
    med_names: list of keys in MEDICATION_KEYWORDS.
    Produces column `{med_name}_90d` (or `{med_name}` if name already has suffix).
    """
    idx = cohort[["MRN", "index_date"]].copy()

    def flag(keywords: list[str]) -> pd.Series:
        sub = drug_master[drug_mask(drug_master["drug_upper"], keywords)].merge(
            idx, on="MRN", how="inner"
        )
        lo = sub["index_date"] - pd.Timedelta(days=window_days)
        active = (sub["_date"] >= lo) & (sub["_date"] <= sub["index_date"])
        return cohort["MRN"].isin(set(sub.loc[active, "MRN"])).astype(int)

    for med in med_names:
        kw = MEDICATION_KEYWORDS.get(med)
        if not kw:
            continue
        col = med if med.endswith("_90d") else f"{med}_{window_days}d"
        cohort[col] = flag(kw)
    return cohort


def add_medication_flags(
    cohort: pd.DataFrame,
    drug_master: pd.DataFrame,
    window_days: int = 90,
) -> pd.DataFrame:
    """COMET backward-compat wrapper. Produces the same six columns as before."""
    idx = cohort[["MRN", "index_date"]].copy()

    def flag(keywords: list[str]) -> pd.Series:
        sub = drug_master[drug_mask(drug_master["drug_upper"], keywords)].merge(
            idx, on="MRN", how="inner"
        )
        lo = sub["index_date"] - pd.Timedelta(days=window_days)
        active = (sub["_date"] >= lo) & (sub["_date"] <= sub["index_date"])
        return cohort["MRN"].isin(set(sub.loc[active, "MRN"])).astype(int)

    cohort["loop_diuretic"]     = flag(LOOP_DIURETICS)
    cohort["acei_arb"]          = flag(ACEI_KEYWORDS + ARB_KEYWORDS)
    cohort["aldosterone_antag"] = flag(ALDOSTERONE_ANTAG)
    cohort["digoxin_90d"]       = flag(DIGOXIN)
    cohort["statin_90d"]        = flag(STATIN)
    cohort["nitrate_90d"]       = flag(NITRATE)
    return cohort


def add_prior_hf_code(
    cohort: pd.DataFrame,
    conditions: pd.DataFrame,
    lookback_days: int = 365,
) -> pd.DataFrame:
    idx = cohort[["person_id", "index_date"]].copy()
    idx["person_id"] = idx["person_id"].astype(str)
    hf = conditions[conditions["_pfx"] == "I50"].copy()
    hf["person_id"] = hf["person_id"].astype(str)
    hf = hf.merge(idx, on="person_id")
    hf = hf[
        (hf["cond_date"] < hf["index_date"]) &
        (hf["cond_date"] >= hf["index_date"] - pd.Timedelta(days=lookback_days))
    ]
    cohort["prior_hf_code_1yr"] = (
        cohort["person_id"].astype(str).isin(set(hf["person_id"])).astype(int)
    )
    return cohort


# ── Composite endpoint builder ────────────────────────────────────────────────

def build_composite_endpoint(
    cohort: pd.DataFrame,
    endpoint_spec: dict,
    *,
    death: Optional[pd.DataFrame],
    conditions: Optional[pd.DataFrame],
    visits: Optional[pd.DataFrame] = None,
    procedures: Optional[pd.DataFrame] = None,
    end_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Build composite endpoint for each cohort patient.

    cohort must have: person_id, index_date, MRN
    endpoint_spec keys: followup_days, censor, components[]

    Component types:
      mortality      — OMOP death table (date-only)
      inpatient_icd  — ICD code during inpatient visit; falls back to date-overlap
                       if visit_occurrence_id absent in conditions
      condition_icd  — bare ICD prefix, any setting
      procedure      — procedure_occurrence by concept_id or source_value prefix

    Returns DataFrame: person_id, event_primary, time_to_primary, primary_event_date,
                       flag_<comp_type>_<comp_name_or_index>  (per component, 0/1)

    Mortality-only config: event_primary == event_death; time_to_primary == time_to_death.
    Administrative censoring: end_date or `death_date.max()` or 2024-12-31.
    """
    followup_days = endpoint_spec.get("followup_days", 1825)
    components    = endpoint_spec.get("components", [])

    cohort_idx = cohort[["person_id", "index_date", "MRN"]].copy()
    cohort_idx["person_id"] = cohort_idx["person_id"].astype(str)
    cohort_idx = cohort_idx.reset_index(drop=True)

    # Administrative censor date
    if end_date is None:
        if death is not None and not death.empty and "death_date" in death.columns:
            end_date = death["death_date"].max()
        if end_date is None or (hasattr(end_date, "__bool__") and pd.isna(end_date)):
            end_date = pd.Timestamp("2024-12-31")

    event_dates: dict[str, pd.Series] = {}   # flag_col → Series(date per patient)

    for i, comp in enumerate(components):
        comp_type = comp.get("type")
        comp_label = comp.get("name", f"comp{i}")
        col = f"flag_{comp_type}_{comp_label}"

        if comp_type == "mortality":
            if death is None or death.empty:
                event_dates[col] = pd.Series(pd.NaT, index=cohort_idx.index,
                                             dtype="datetime64[ns]")
                continue
            d = death.copy()
            d["person_id"] = d["person_id"].astype(str)
            merged = cohort_idx.merge(d, on="person_id", how="left")
            valid  = merged[merged["death_date"] > merged["index_date"]]
            earliest = valid.groupby("person_id")["death_date"].min()
            event_dates[col] = cohort_idx["person_id"].map(earliest)

        elif comp_type == "inpatient_icd":
            codes  = comp.get("codes", [])
            char   = comp.get("char", 3)
            vcids  = comp.get("visit_concept_ids", [9201, 262])

            if conditions is None or conditions.empty:
                event_dates[col] = pd.Series(pd.NaT, index=cohort_idx.index,
                                             dtype="datetime64[ns]")
                continue

            pfx_col = "_pfx4" if char == 4 else "_pfx"
            cond_match = conditions[conditions[pfx_col].isin(set(codes))].copy()
            cond_match["person_id"] = cond_match["person_id"].astype(str)

            vcids_str = {str(v) for v in vcids}
            if visits is not None and not visits.empty:
                if "visit_occurrence_id" in conditions.columns:
                    # Join via visit_occurrence_id (preferred)
                    vis_inpt = visits[
                        visits["visit_concept_id"].astype(str).isin(vcids_str)
                    ][["visit_occurrence_id", "visit_start_date"]].copy()
                    cond_match_vis = cond_match.merge(
                        vis_inpt, on="visit_occurrence_id", how="inner"
                    )
                    event_col = cond_match_vis.rename(
                        columns={"cond_date": "_event_date"}
                    )[["person_id", "_event_date"]]
                else:
                    # Date-overlap fallback
                    vis = visits[
                        visits["visit_concept_id"].astype(str).isin(vcids_str)
                    ].copy()
                    vis["person_id"] = vis["person_id"].astype(str)
                    cv = cond_match.merge(
                        vis[["person_id", "visit_start_date", "visit_end_date"]],
                        on="person_id", how="inner",
                    )
                    cv["visit_end_date"] = cv["visit_end_date"].fillna(
                        cv["visit_start_date"] + pd.Timedelta(days=7)
                    )
                    in_visit = (
                        (cv["cond_date"] >= cv["visit_start_date"]) &
                        (cv["cond_date"] <= cv["visit_end_date"])
                    )
                    event_col = cv[in_visit].rename(
                        columns={"cond_date": "_event_date"}
                    )[["person_id", "_event_date"]]
            else:
                # No visit data: use condition dates (documented approximation)
                event_col = cond_match.rename(
                    columns={"cond_date": "_event_date"}
                )[["person_id", "_event_date"]]

            event_col = event_col.drop_duplicates()
            merged = cohort_idx.merge(event_col, on="person_id", how="left")
            valid  = merged[merged["_event_date"] > merged["index_date"]]
            earliest = valid.groupby("person_id")["_event_date"].min()
            event_dates[col] = cohort_idx["person_id"].map(earliest)

        elif comp_type == "condition_icd":
            codes = comp.get("codes", [])
            char  = comp.get("char", 3)
            if conditions is None or conditions.empty:
                event_dates[col] = pd.Series(pd.NaT, index=cohort_idx.index,
                                             dtype="datetime64[ns]")
                continue
            pfx_col = "_pfx4" if char == 4 else "_pfx"
            cm = conditions[conditions[pfx_col].isin(set(codes))].copy()
            cm["person_id"] = cm["person_id"].astype(str)
            merged = cohort_idx.merge(cm[["person_id", "cond_date"]], on="person_id", how="left")
            valid  = merged[merged["cond_date"] > merged["index_date"]]
            earliest = valid.groupby("person_id")["cond_date"].min()
            event_dates[col] = cohort_idx["person_id"].map(earliest)

        elif comp_type == "procedure":
            concept_ids     = comp.get("concept_ids", [])
            source_prefixes = comp.get("source_prefixes", [])
            if procedures is None or procedures.empty:
                event_dates[col] = pd.Series(pd.NaT, index=cohort_idx.index,
                                             dtype="datetime64[ns]")
                continue
            proc = procedures.copy()
            proc["person_id"] = proc["person_id"].astype(str)
            pmask = pd.Series(False, index=proc.index)
            if concept_ids:
                pmask |= proc["procedure_concept_id"].astype(str).isin(
                    {str(c) for c in concept_ids}
                )
            if source_prefixes:
                pmask |= proc["procedure_source_value"].astype(str).apply(
                    lambda v: any(
                        str(v).replace(".", "").startswith(str(p))
                        for p in source_prefixes
                    )
                )
            pm = proc[pmask][["person_id", "procedure_date"]].rename(
                columns={"procedure_date": "_event_date"}
            )
            merged = cohort_idx.merge(pm, on="person_id", how="left")
            valid  = merged[merged["_event_date"] > merged["index_date"]]
            earliest = valid.groupby("person_id")["_event_date"].min()
            event_dates[col] = cohort_idx["person_id"].map(earliest)

        else:
            raise ValueError(f"Unknown endpoint component type: {comp_type!r}")

    # ── Composite: time-to-first across all components ────────────────────────
    if event_dates:
        edf = pd.DataFrame(event_dates, index=cohort_idx.index)
        primary_event_date = edf.min(axis=1)  # NaT if all NaT
    else:
        primary_event_date = pd.Series(pd.NaT, index=cohort_idx.index,
                                       dtype="datetime64[ns]")

    followup_td = pd.Timedelta(days=followup_days)
    censor_date = (cohort_idx["index_date"] + followup_td).clip(upper=end_date)

    event_primary  = (primary_event_date.notna() &
                      (primary_event_date <= censor_date)).astype(int)
    event_time_raw = (
        primary_event_date.where(event_primary.astype(bool), censor_date)
        - cohort_idx["index_date"]
    ).dt.days.clip(lower=0)

    # Cap at followup_days
    too_long = event_time_raw > followup_days
    event_primary.loc[too_long]  = 0
    event_time_raw.loc[too_long] = followup_days

    result = cohort_idx[["person_id"]].copy()
    result["event_primary"]       = event_primary.values
    result["time_to_primary"]     = event_time_raw.values
    result["primary_event_date"]  = primary_event_date.values
    for col, dates in event_dates.items():
        result[col] = (cohort_idx["person_id"].map(
            dict(zip(cohort_idx["person_id"], dates.notna().astype(int)))
        )).fillna(0).astype(int)

    return result
