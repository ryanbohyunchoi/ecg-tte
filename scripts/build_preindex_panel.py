"""Build a broad pre-index covariate panel for a cohort from OMOP gold.

Purpose: an evaluation panel of pre-treatment characteristics that standard PSM
covariate sets omit (diagnosis history, drug history, procedures, labs, visit
intensity). Used to test whether adding unstructured representations to a PS
improves balance beyond the covariates in that PS ("long-tail balance").

Window: [index - lookback_days, index - 1]. Index-day records are excluded.
Features (panel v2, 2026-09-23: code features hold counts so hdPS can form
frequency levels; v1 panels stored 1.0 for "any"):
  dx_<ICD10 3-char>          distinct days with the code in window (count)
  rx_<first word of order>    distinct days with an order in window (count)
  px_<source code>            distinct days with the procedure in window (count)
  lab_<concept_id>            latest value in window (numeric; NaN if unmeasured)
  labn_<concept_id>           measured in window (binary)
  vis_<concept>_365 / _30     visit counts
Code features kept if cohort prevalence (any) >= --min-prevalence. Numeric labs kept if
measured in >= --min-measured of the cohort. With --dictionary (e.g. an external
prognostic reference set), exactly the features of that dictionary are built and
no prevalence filter is applied.

Output (restricted): restricted_panel.parquet (patient_key + features),
panel_dictionary.csv (feature, domain, prevalence), summary.json (aggregates).
"""
import argparse
import glob
import json
import os

import duckdb
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort-csv", required=True,
                    help="CSV/parquet with patient_key and index_date (person_id used directly if present)")
    ap.add_argument("--dictionary", default=None, help="panel_dictionary.csv to reproduce exactly")
    ap.add_argument("--omop-root", required=True)
    ap.add_argument("--lookback-days", type=int, default=365)
    ap.add_argument("--min-prevalence", type=float, default=0.02)
    ap.add_argument("--min-measured", type=float, default=0.20)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--threads", type=int, default=16)
    args = ap.parse_args()
    os.makedirs(args.output_dir, exist_ok=False)
    os.chmod(args.output_dir, 0o700)
    R = args.omop_root
    g = lambda t: [f for f in glob.glob(f"{R}/{t}/**/*.parquet", recursive=True)]

    con = duckdb.connect()
    con.execute(f"SET threads={args.threads}")
    read = pd.read_parquet if args.cohort_csv.endswith(".parquet") else pd.read_csv
    coh = read(args.cohort_csv).drop_duplicates("patient_key")
    coh["mrn"] = coh.patient_key.astype(str).str.replace(r"\D", "", regex=True).str.lstrip("0")
    con.register("coh_df", coh)
    if "person_id" in coh:
        con.execute("""CREATE TABLE pmap AS SELECT patient_key, CAST(index_date AS DATE) AS idx,
                       CAST(person_id AS BIGINT) person_id FROM coh_df""")
    else:
        con.execute("CREATE TABLE coh AS SELECT patient_key, mrn, CAST(index_date AS DATE) AS idx FROM coh_df")
        con.execute(f"""CREATE TABLE pmap AS
            SELECT c.patient_key, c.idx, p.person_id FROM coh c JOIN
            (SELECT person_id, ltrim(regexp_replace(person_source_value, '\\D', '', 'g'), '0') AS mrn
             FROM read_parquet({g('person')})) p USING (mrn)""")
    fixed = pd.read_csv(args.dictionary) if args.dictionary else None
    n = con.execute("SELECT count(DISTINCT patient_key) FROM pmap").fetchone()[0]
    L = args.lookback_days

    def window(table, date_col, select):
        return f"""SELECT m.patient_key, t.{date_col} AS day, {select} FROM read_parquet({g(table)}, hive_partitioning=true) t
                   JOIN pmap m USING (person_id)
                   WHERE t.{date_col} >= m.idx - INTERVAL {L} DAY AND t.{date_col} < m.idx"""

    binary = {
        "dx": window("condition_occurrence", "condition_start_date",
                     "'dx_' || upper(substr(replace(condition_source_value, '.', ''), 1, 3)) AS f"),
        "rx": window("drug_exposure", "drug_exposure_start_date",
                     "'rx_' || lower(split_part(trim(drug_source_value), ' ', 1)) AS f"),
        "px": window("procedure_occurrence", "procedure_date", "'px_' || procedure_source_value AS f"),
    }
    frames, dictionary = [], []
    for dom, q in binary.items():
        having = (f"f IN (SELECT feature FROM fixed_df WHERE domain = '{dom}')" if fixed is not None
                  else f"count(DISTINCT patient_key) >= {args.min_prevalence * n}")
        if fixed is not None:
            con.register("fixed_df", fixed)
        d = con.execute(f"""WITH x AS (SELECT patient_key, f, count(DISTINCT day) AS c FROM ({q})
                                      WHERE f IS NOT NULL GROUP BY 1, 2)
                            SELECT f, list(patient_key) AS keys, list(c) AS cnt FROM x
                            GROUP BY f HAVING {having}""").df()
        for f, keys, cnt in zip(d.f, d["keys"], d["cnt"]):
            frames.append(pd.Series(cnt, index=pd.Index(keys, name="patient_key"), name=f, dtype=float))
            dictionary.append((f, dom, len(keys) / n))

    labs = con.execute(f"""
        WITH w AS ({window('measurement', 'measurement_date',
                           'measurement_concept_id AS c, measurement_date AS d, value_as_number AS v')}
                   AND value_as_number IS NOT NULL),
        keep AS (SELECT c FROM w GROUP BY c HAVING {"'lab_' || c IN (SELECT feature FROM fixed_df)" if fixed is not None
                  else f"count(DISTINCT patient_key) >= {args.min_measured * n}"})
        SELECT patient_key, c, arg_max(v, d) AS v FROM w WHERE c IN (SELECT c FROM keep)
        GROUP BY patient_key, c""").df()
    lab_wide = labs.pivot(index="patient_key", columns="c", values="v")
    for c in lab_wide.columns:
        frames.append(lab_wide[c].rename(f"lab_{c}"))
        frames.append(lab_wide[c].notna().astype(float).rename(f"labn_{c}"))
        dictionary.append((f"lab_{c}", "lab", lab_wide[c].notna().sum() / n))

    vis = con.execute(f"""SELECT patient_key, visit_concept_id AS c,
            count(*) AS n365,
            count(*) FILTER (WHERE day >= idx - INTERVAL 30 DAY) AS n30
        FROM ({window('visit_occurrence', 'visit_start_date', 'visit_concept_id, m.idx')})
        GROUP BY 1, 2""").df()
    for c in vis.c.dropna().unique():
        v = vis[vis.c == c].set_index("patient_key")
        for col in ("n365", "n30"):
            frames.append(v[col].astype(float).rename(f"vis_{int(c)}_{col[1:]}"))
            dictionary.append((f"vis_{int(c)}_{col[1:]}", "visit", (v[col] > 0).sum() / n))

    panel = pd.concat(frames, axis=1).reindex(coh.patient_key.unique())
    if fixed is not None:  # exact column set of the source dictionary (absent features = 0 / NaN)
        cols = []
        for f in fixed.feature:
            cols += [f, f.replace("lab_", "labn_")] if f.startswith("lab_") else [f]
        panel = panel.reindex(columns=cols)
    panel.index.name = "patient_key"
    bin_cols = [c for c in panel.columns if c.split("_")[0] in ("dx", "rx", "px", "labn")]
    vis_cols = [c for c in panel.columns if c.startswith("vis_")]
    panel[bin_cols + vis_cols] = panel[bin_cols + vis_cols].fillna(0.0)
    panel.reset_index().to_parquet(f"{args.output_dir}/restricted_panel.parquet")
    dd = pd.DataFrame(dictionary, columns=["feature", "domain", "prevalence"])
    dd.to_csv(f"{args.output_dir}/panel_dictionary.csv", index=False)
    summary = {"panel_version": 2, "dictionary": args.dictionary,
               "cohort": int(len(coh)), "linked_to_person": int(n), "lookback_days": L,
               "features_by_domain": dd.domain.value_counts().to_dict(),
               "min_prevalence": args.min_prevalence, "min_measured": args.min_measured}
    json.dump(summary, open(f"{args.output_dir}/summary.json", "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
