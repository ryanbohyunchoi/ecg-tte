"""Build an out-of-cohort ECG phenotype training set (ECG <-> echo pairs).

Purpose: learn low-dimensional supervised ECG phenotype scores (P(LVEF<=40), AF,
age, sex) on patients OUTSIDE every emulated trial cohort, then apply the heads to
trial cohorts as PS covariates. Patients in any --exclude-keys file are removed
before sampling. Labels are never taken from the trial cohorts.

Pairing: each echo with numeric EF is matched to that patient's nearest ECG within
+/- --window-days. One pair per patient (seeded random choice). Patient-level
80/20 train/test split.

Outputs (restricted, patient-level; stays on cluster):
  restricted_phenotype_set.parquet  fileID, split, lvef, lvef_le_40, age, male, afib
  restricted_bcl_input.csv          fileID column for the embedder
  restricted_formats_no250.csv      all files flagged non-250 (all_ecgs is 500 Hz)
  summary.json                      aggregate counts only
"""
import argparse
import glob
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def digits(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(r"\D", "", regex=True).str.lstrip("0")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ecg-meta", required=True)
    ap.add_argument("--echo-meta", required=True)
    ap.add_argument("--person-glob", required=True, help="OMOP person parquet glob (gender)")
    ap.add_argument("--exclude-keys", nargs="+", required=True,
                    help="CSV files with a patient_key (=MRN) column to exclude")
    ap.add_argument("--n-patients", type=int, default=40000)
    ap.add_argument("--window-days", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260923)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.output_dir, exist_ok=False)
    os.chmod(args.output_dir, 0o700)
    rng = np.random.default_rng(args.seed)

    excl = set()
    for f in args.exclude_keys:
        excl |= set(digits(pd.read_csv(f, usecols=["patient_key"]).patient_key))

    echo = pq.read_table(args.echo_meta, columns=["MRN", "EchoDate", "EF", "Age_echodata"]).to_pandas()
    echo = echo[echo.EF.between(5, 90)].copy()
    echo["mrn"] = digits(echo.MRN)
    echo["t"] = pd.to_datetime(echo.EchoDate, errors="coerce")
    echo = echo.dropna(subset=["t"])
    echo = echo[~echo.mrn.isin(excl)]

    ecg = pq.read_table(args.ecg_meta, columns=["fileID", "MRN", "ECGDate", "Diagnosis"]).to_pandas()
    ecg = ecg.dropna(subset=["fileID"]).drop_duplicates("fileID")
    ecg["mrn"] = digits(ecg.MRN)
    ecg["t"] = pd.to_datetime(ecg.ECGDate, errors="coerce")
    ecg = ecg.dropna(subset=["t"])
    ecg = ecg[ecg.mrn.isin(set(echo.mrn))]

    pairs = pd.merge_asof(echo.sort_values("t"), ecg[["mrn", "t", "fileID", "Diagnosis"]].sort_values("t"),
                          on="t", by="mrn", direction="nearest",
                          tolerance=pd.Timedelta(days=args.window_days)).dropna(subset=["fileID"])
    pairs = pairs.sample(frac=1, random_state=args.seed).drop_duplicates("mrn")
    pairs = pairs.head(args.n_patients).copy()

    person = pd.concat([pd.read_parquet(f, columns=["person_source_value", "gender_concept_id"])
                        for f in glob.glob(args.person_glob)])
    person["mrn"] = digits(person.person_source_value)
    sex = person.drop_duplicates("mrn").set_index("mrn").gender_concept_id
    pairs["male"] = pairs.mrn.map(sex).map({8507: 1.0, 8532: 0.0})
    pairs["afib"] = pairs.Diagnosis.fillna("").str.upper().str.contains("ATRIAL FIB").astype(float)
    pairs["lvef"] = pairs.EF
    pairs["lvef_le_40"] = (pairs.EF <= 40).astype(float)
    pairs["age"] = pairs.Age_echodata
    pairs["split"] = np.where(rng.random(len(pairs)) < 0.8, "train", "test")

    out = pairs[["fileID", "split", "lvef", "lvef_le_40", "age", "male", "afib"]].reset_index(drop=True)
    out.to_parquet(f"{args.output_dir}/restricted_phenotype_set.parquet")
    out[["fileID"]].to_csv(f"{args.output_dir}/restricted_bcl_input.csv", index=False)
    pd.DataFrame({"fileID": out.fileID, "format_new": "adapter_non250"}).to_csv(
        f"{args.output_dir}/restricted_formats_no250.csv", index=False)
    summary = {
        "excluded_keys": len(excl), "echo_rows_eligible": int(len(echo)),
        "patients": int(len(out)), "train": int((out.split == "train").sum()),
        "lvef_le_40_rate": round(float(out.lvef_le_40.mean()), 4),
        "afib_rate": round(float(out.afib.mean()), 4),
        "male_known": round(float(out.male.notna().mean()), 4),
        "window_days": args.window_days, "seed": args.seed,
    }
    json.dump(summary, open(f"{args.output_dir}/summary.json", "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
