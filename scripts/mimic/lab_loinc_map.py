"""Curated MIMIC-IV lab itemid -> LOINC map for the CLMBR-T MEDS input (docs/mimic/MIMIC_EXTERNAL_VALIDATION.md).

MIMIC-IV 3.1 `d_labitems` has no `loinc_code` column (removed after v1.0) and no MIMIC lab -> LOINC table exists on
disk, so the queue rule "LOINC where d_labitems has it, otherwise the MIMIC itemid code" would code every lab as
`MIMIC_LAB/<itemid>`, which is not in the CLMBR-T dictionary. This map covers the most frequent pre-time-zero lab
itemids in the 8 trial cohorts (profiled by count, aggregate only). Each LOINC was chosen by the analyst from the item
label, fluid and category, then checked by `verify()` against the OMOP CONCEPT table (LOINC, standard, valid) and the
CLMBR-T dictionary; the verified table (item label next to the LOINC long name) is written to
OUT/vocab/lab_loinc_verified.csv for review. Items that are not tests (hemolysis / lipemia / icterus indices, hold
tubes, specimen type, ventilator settings, smear morphology) are not mapped and stay MIMIC itemid codes.
Where the first-choice LOINC is not in the CLMBR-T dictionary, an equivalent in-dictionary code was chosen (noted per
item); blood-gas pH, pO2 and total CO2 use the arterial codes (most MIMIC blood gases are arterial; the dictionary has
no specimen-agnostic form). pCO2 keeps an out-of-dictionary code (no in-dictionary equivalent). RDW-SD (52172) is not
mapped (its LOINC 21000-5 is deprecated).
"""
LAB_LOINC = {
    # chemistry (serum / plasma)
    50912: "2160-0",   # Creatinine
    50971: "2823-3",   # Potassium
    51006: "3094-0",   # Urea nitrogen
    50983: "2951-2",   # Sodium
    50902: "2075-0",   # Chloride
    50882: "2028-9",   # Bicarbonate (= total CO2, serum / plasma; 1963-8 is not in the dictionary)
    50868: "33037-3",  # Anion gap
    50931: "2345-7",   # Glucose
    50960: "19123-9",  # Magnesium
    50893: "17861-6",  # Calcium, total
    50970: "2777-1",   # Phosphate
    50861: "1742-6",   # ALT
    50920: "77147-7",  # eGFR (MDRD; 33914-3 is deprecated)
    50878: "1920-8",   # AST
    50885: "1975-2",   # Bilirubin, total
    50883: "1968-7",   # Bilirubin, direct
    50863: "6768-6",   # Alkaline phosphatase
    50862: "1751-7",   # Albumin
    51003: "6598-7",   # Troponin T
    50954: "2532-0",   # LDH
    50911: "13969-1",  # CK-MB
    50910: "2157-6",   # CK
    50993: "3016-3",   # TSH
    50852: "4548-4",   # HbA1c
    51613: "27353-2",  # eAG
    51000: "2571-8",   # Triglycerides
    50907: "2093-3",   # Cholesterol, total
    50904: "2085-9",   # HDL
    50903: "9830-1",   # Cholesterol / HDL ratio
    50905: "13457-7",  # LDL, calculated
    50956: "3040-3",   # Lipase
    50976: "2885-2",   # Protein, total
    50963: "33762-6",  # NT-proBNP
    50924: "2276-4",   # Ferritin
    51007: "3084-1",   # Uric acid
    50952: "2498-4",   # Iron
    50930: "10834-0",  # Globulin
    50998: "3034-6",   # Transferrin
    50953: "2500-7",   # TIBC
    50889: "1988-5",   # CRP
    51010: "2132-9",   # Vitamin B12
    # hematology / coagulation (blood)
    51221: "4544-3",   # Hematocrit
    51265: "777-3",    # Platelets
    51222: "718-7",    # Hemoglobin
    51301: "6690-2",   # WBC
    51249: "786-4",    # MCHC
    51248: "785-6",    # MCH
    51250: "787-2",    # MCV
    51279: "789-8",    # RBC
    51277: "788-0",    # RDW
    51237: "6301-6",   # INR
    51274: "5902-2",   # PT
    51275: "14979-9",  # PTT
    51214: "3255-7",   # Fibrinogen
    51256: "770-8",    # Neutrophils %
    51244: "736-9",    # Lymphocytes %
    51254: "5905-5",   # Monocytes %
    51146: "706-2",    # Basophils %
    51200: "713-8",    # Eosinophils %
    51144: "764-1",    # Bands %
    52075: "751-8",    # Absolute neutrophils
    52073: "711-2",    # Absolute eosinophils
    52074: "742-7",    # Absolute monocytes
    51133: "731-0",    # Absolute lymphocytes
    52069: "704-7",    # Absolute basophils
    52135: "71695-1",  # Immature granulocytes %
    # blood gas (blood, specimen-agnostic)
    50820: "2744-1",   # pH (arterial)
    50821: "2703-7",   # pO2 (arterial)
    50818: "11557-6",  # pCO2 (not in the dictionary)
    50802: "11555-0",  # Base excess
    50804: "2026-3",   # Calculated total CO2 (arterial)
    50813: "32693-4",  # Lactate
    50808: "1994-3",   # Free (ionized) calcium
    50822: "6298-4",   # Potassium, whole blood
    50824: "2947-0",   # Sodium, whole blood
    50806: "2069-3",   # Chloride, whole blood
    50809: "2339-0",   # Glucose, whole blood
    50817: "2713-6",   # Oxygen saturation (calculated from pO2, in Blood)
    50811: "718-7",    # Hemoglobin (blood gas)
    50810: "20570-8",  # Hematocrit, calculated
    # urine
    51478: "25428-4",  # Glucose (dipstick, presence)
    51498: "5811-5",   # Specific gravity
    51508: "5778-6",   # Color
    51491: "5803-2",   # pH
    51486: "5799-2",   # Leukocyte esterase
    51506: "5767-9",   # Appearance
    51487: "5802-4",   # Nitrite
    51484: "2514-8",   # Ketones (dipstick, presence)
    51514: "20405-7",  # Urobilinogen (dipstick)
    51464: "5770-3",   # Bilirubin
    51492: "20454-5",  # Protein (dipstick, presence)
    51466: "5794-3",   # Blood (hemoglobin)
    51516: "5821-4",   # WBC (sediment)
    51493: "13945-1",  # RBC (sediment)
    51463: "25145-4",  # Bacteria
    51082: "2161-8",   # Creatinine, urine
}


def verify(out_csv=None):
    """Join the map with d_labitems, the OMOP LOINC concepts and the CLMBR-T dictionary. Returns the verified table;
    `ok` = LOINC exists, standard and valid. Metadata only (no patient data)."""
    import duckdb
    import pandas as pd
    from mimic_common import OUT, STAGE, clmbr_codes
    vocab = clmbr_codes()
    con = duckdb.connect()
    m = pd.DataFrame(list(LAB_LOINC.items()), columns=["itemid", "loinc"])
    con.register("m", m)
    T = con.execute(f"""SELECT m.itemid, d.label, d.fluid, d.category, m.loinc, c.concept_name, c.standard_concept,
                        c.invalid_reason FROM m LEFT JOIN read_parquet('{STAGE}/d_labitems.parquet') d USING (itemid)
                        LEFT JOIN (SELECT * FROM read_parquet('{OUT}/vocab/concept.parquet') WHERE vocabulary_id = 'LOINC') c
                        ON c.concept_code = m.loinc ORDER BY m.itemid""").df()
    T["ok"] = T.concept_name.notna() & (T.standard_concept == "S") & T.invalid_reason.isna()
    T["in_dictionary"] = ("LOINC/" + T.loinc).isin(vocab)
    if out_csv:
        T.to_csv(out_csv, index=False)
    return T


if __name__ == "__main__":
    import pandas as pd
    from mimic_common import OUT
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 200)
    pd.set_option("display.max_colwidth", 70)
    T = verify(OUT / "vocab" / "lab_loinc_verified.csv")
    print(T[["itemid", "label", "fluid", "loinc", "concept_name", "ok", "in_dictionary"]].to_string())
    print("ok", int(T.ok.sum()), "/", len(T), "in dictionary", int(T.in_dictionary.sum()))
