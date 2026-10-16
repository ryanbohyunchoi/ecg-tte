"""AoU OMOP (CDR v8, BigQuery) -> "gold-shaped" source contract used by the unchanged Yale builders.

The Yale builders (build_trial_cohort.py, build_core_baseline.build, build_preindex_panel.py, build_comet_meds.build) read
OMOP gold columns with Yale semantics. This module defines, in BigQuery SQL, how each AoU column is produced:

  drug_exposure.drug_source_value (gold)       normalised drug name: lower(standard concept_name, else source value),
                                               every run of non-alphanumerics -> '-'. trial_common.create_drug_tokens
                                               splits on '-' and matches keywords, so 'sacubitril 49 MG / valsartan 51 MG
                                               Oral Tablet [Entresto]' gives tokens sacubitril, valsartan, entresto, ...
                                               (Yale: Epic order name, first word; formulation not distinguishable there
                                               either, e.g. metoprolol tartrate vs succinate).
  drug_exposure.drug_source_value (meds_gold)  lower(standard concept_name): build_preindex_panel's rx_ feature is the first
                                               word (= the first ingredient, as Yale's first word of the order name).
  condition_source_value                       ICD-10-CM concept_code of condition_source_concept_id; NULL for ICD-9-CM and
                                               other source vocabularies (kept in condition_source_vocabulary), so they never
                                               match an ICD-10 prefix, a panel dx_ feature or the PS-Flags pattern.
  procedure_source_value                       CPT4 / HCPCS / ICD-10-PCS concept_code (Yale: same source codes); NULL otherwise
                                               (procedure_source_vocabulary kept).
  measurement_concept_id (gold)                AoU LOINC concepts remapped to the Yale concept id of each item (MEAS_MAP);
                                               values unit-harmonised (UNIT_FACTOR); AoU program physical measurements (PPI
                                               source vocabulary) excluded: EHR measurements only, as at Yale.
  measurement (meds_gold)                      original standard concept ids, full history, PPI excluded (CLMBR-T input and
                                               the hdPS lab_ / labn_ features).
  visit_concept_id                             rolled up to 9201 inpatient > 9203 ER > 9202 outpatient through concept_ancestor
                                               (Yale gold uses those three); unmapped visit concepts keep their id.
  person.gender_concept_id                     from sex_at_birth_concept_id (AoU PPI answer) -> 8507 / 8532; NULL otherwise.
  person.person_source_value                   CAST(person_id AS STRING) (the patient_key identity contract).
  death                                        aou_death primary record (EHR + HealthPro), else death.
"""
from __future__ import annotations

# ---- measurement items: Yale concept id (trial_specs.NUMERIC_CORE, build_trial_cohort, build_physiology_panel_v2.LABS)
#      -> AoU LOINC codes. Codes are resolved to concept ids in the CDR; the probe reports which resolve and their coverage.
MEAS_MAP = {
    "sbp": (4152194, ["8480-6", "8459-0", "8460-8", "8461-6", "8508-4", "8546-4", "8547-2"]),
    "dbp": (3012888, ["8462-4", "8453-3", "8454-1", "8455-8", "8514-2", "8496-2", "8497-0"]),
    "heart_rate": (3027018, ["8867-4"]),
    "bmi": (4245997, ["39156-5"]),
    "creatinine": (3016723, ["2160-0", "38483-4"]),
    "potassium": (3023103, ["2823-3", "6298-4"]),
    "sodium": (3019550, ["2951-2", "2947-0"]),
    "hemoglobin": (3000963, ["718-7"]),
    "egfr": (40764999, ["62238-1", "33914-3", "48642-3", "48643-1", "50044-7", "50210-4", "77147-7", "88293-6", "88294-4",
                        "98979-8", "98980-6"]),
    "ntprobnp": (3029187, ["33762-6", "83107-3", "83108-1", "71425-3"]),
    "hs_troponin_t": (40769783, ["67151-1"]),
    "albumin": (3024561, ["1751-7", "61151-7", "61152-5"]),
    "bun": (3013682, ["3094-0", "6299-2"]),
    "glucose": (3004501, ["2345-7"]),
    "hba1c": (3004410, ["4548-4", "17856-6", "4549-2"]),
    "wbc": (3000905, ["6690-2", "26464-8"]),
    "platelets": (3024929, ["777-3", "26515-7"]),
    "ldl": (3028288, ["13457-7", "18262-6", "2089-1"]),
}
# unit_concept_id -> multiplicative factor to the US conventional unit used at Yale (applied per item)
UNIT_FACTOR = {
    "creatinine": {8749: 1 / 88.42},            # umol/L -> mg/dL
    "hemoglobin": {8636: 0.1, 8504: 0.1},        # g/L -> g/dL
    "albumin": {8636: 0.1, 8504: 0.1},           # g/L -> g/dL
    "glucose": {8753: 18.016},                   # mmol/L -> mg/dL
    "bun": {8753: 2.801},                        # mmol/L urea -> mg/dL urea nitrogen
    "ldl": {8753: 38.67},                        # mmol/L -> mg/dL
    "hba1c": {9579: None},                       # mmol/mol (IFCC) -> NGSP %: 0.0915 * x + 2.15 (affine, below)
}
HBA1C_IFCC = (0.09148, 2.152)

# ---- AoU survey items (PPI question concept_code). Answers are coded by answer concept_code / name rules in
#      aou_build.SURVEY_RULES after the probe has listed the answer codes present (aggregates only).
SURVEY_QUESTIONS = {
    "smoke_100": "Smoking_100CigsLifetime",
    "smoke_freq": "Smoking_SmokeFrequency",
    "alcohol_any": "Alcohol_AlcoholParticipant",
    "alcohol_freq": "Alcohol_DrinkFrequencyPastYear",
    "education": "Education_HighestGrade",
    "income": "Income_AnnualIncome",
    "employment": "Employment_EmploymentStatus",
    "insurance": "Insurance_HealthInsurance",
    "home_own": "HomeOwn_CurrentHomeOwn",
    "marital": "MaritalStatus_CurrentMaritalStatus",
    "general_health": "OverallHealth_GeneralHealth",
}

VISIT_ROLLUP = [(9201, "inpatient"), (9203, "emergency"), (9202, "outpatient")]  # priority order
SEX_AT_BIRTH = {"male": 45878463, "female": 45880669}  # AoU PPI answers (verified by the probe)


def norm_sql(expr: str) -> str:
    """BigQuery: normalised token string (lower, non-alphanumeric runs -> '-', trimmed)."""
    return f"TRIM(REGEXP_REPLACE(LOWER({expr}), r'[^a-z0-9]+', '-'), '-')"


def drug_concept_sql(D: str, keywords) -> str:
    """drug_concept_ids whose normalised standard name contains any keyword token (+ the normalised name)."""
    kw = ", ".join("'" + k.lower().replace("'", "") + "'" for k in sorted(set(keywords)))
    return f"""SELECT c.concept_id, {norm_sql('c.concept_name')} AS norm
        FROM `{D}.concept` c
        WHERE c.domain_id = 'Drug' AND c.vocabulary_id IN ('RxNorm', 'RxNorm Extension')
          AND EXISTS (SELECT 1 FROM UNNEST(SPLIT({norm_sql('c.concept_name')}, '-')) tok WHERE tok IN ({kw}))"""


def drug_rows_sql(D: str, keywords, where: str = "TRUE") -> str:
    """(person_id, d) drug exposures matching keyword tokens: by standard concept, or by source value when unmapped."""
    kw = ", ".join("'" + k.lower().replace("'", "") + "'" for k in sorted(set(keywords)))
    return f"""SELECT de.person_id, de.drug_exposure_start_date AS d FROM `{D}.drug_exposure` de
        WHERE {where} AND de.drug_exposure_start_date IS NOT NULL AND (
          de.drug_concept_id IN (SELECT concept_id FROM ({drug_concept_sql(D, keywords)}))
          OR (COALESCE(de.drug_concept_id, 0) = 0 AND EXISTS (
              SELECT 1 FROM UNNEST(SPLIT({norm_sql('de.drug_source_value')}, '-')) tok WHERE tok IN ({kw}))))"""


def procedure_rows_sql(D: str, prefixes, where: str = "TRUE") -> str:
    likes = " OR ".join(f"STARTS_WITH(UPPER(sc.concept_code), '{p}')" for p in prefixes)
    return f"""SELECT po.person_id, po.procedure_date AS d FROM `{D}.procedure_occurrence` po
        JOIN `{D}.concept` sc ON sc.concept_id = po.procedure_source_concept_id
        WHERE {where} AND po.procedure_date IS NOT NULL AND sc.vocabulary_id IN ('CPT4', 'HCPCS', 'ICD10PCS') AND ({likes})"""


def condition_code_sql(alias_src: str = "sc") -> str:
    """gold condition_source_value from the source concept (alias_src = joined concept on condition_source_concept_id)."""
    return f"IF({alias_src}.vocabulary_id = 'ICD10CM', {alias_src}.concept_code, NULL)"


def procedure_code_sql(alias_src: str = "sc") -> str:
    return f"IF({alias_src}.vocabulary_id IN ('CPT4', 'HCPCS', 'ICD10PCS'), {alias_src}.concept_code, NULL)"


def loinc_sql(D: str) -> str:
    """item, yale_cid, aou concept_id for every MEAS_MAP LOINC code present in the CDR vocabulary."""
    rows = " UNION ALL ".join(f"SELECT '{item}' item, {cid} yale_cid, '{code}' code"
                              for item, (cid, codes) in MEAS_MAP.items() for code in codes)
    return f"""SELECT m.item, m.yale_cid, m.code, c.concept_id FROM ({rows}) m
        JOIN `{D}.concept` c ON c.vocabulary_id = 'LOINC' AND c.concept_code = m.code"""


def unit_case_sql(item_col: str = "l.item", unit_col: str = "me.unit_concept_id", v: str = "me.value_as_number") -> str:
    """BigQuery CASE converting value_as_number to the Yale unit per item (UNIT_FACTOR)."""
    parts = []
    for item, m in UNIT_FACTOR.items():
        for u, f in m.items():
            if item == "hba1c" and f is None:
                a, b = HBA1C_IFCC
                parts.append(f"WHEN {item_col} = '{item}' AND {unit_col} = {u} THEN {a} * {v} + {b}")
            else:
                parts.append(f"WHEN {item_col} = '{item}' AND {unit_col} = {u} THEN {f!r} * {v}")
    return "CASE " + " ".join(parts) + f" ELSE {v} END"


def visit_rollup_sql(D: str) -> str:
    """visit_concept_id -> rolled-up id (9201 > 9203 > 9202) for every visit concept that descends from one of them."""
    prio = " ".join(f"WHEN {cid} THEN {i}" for i, (cid, _) in enumerate(VISIT_ROLLUP))
    return f"""SELECT descendant_concept_id AS visit_concept_id,
               ARRAY_AGG(ancestor_concept_id ORDER BY CASE ancestor_concept_id {prio} END LIMIT 1)[OFFSET(0)] AS rolled
        FROM `{D}.concept_ancestor`
        WHERE ancestor_concept_id IN ({', '.join(str(c) for c, _ in VISIT_ROLLUP)})
        GROUP BY 1"""


def survey_question_sql(D: str) -> str:
    rows = " UNION ALL ".join(f"SELECT '{k}' item, '{q}' code" for k, q in SURVEY_QUESTIONS.items())
    return f"""SELECT s.item, s.code, c.concept_id FROM ({rows}) s
        JOIN `{D}.concept` c ON c.vocabulary_id = 'PPI' AND LOWER(c.concept_code) = LOWER(s.code)"""
