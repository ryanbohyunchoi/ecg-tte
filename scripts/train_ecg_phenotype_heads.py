"""Train linear ECG phenotype heads out-of-cohort and score a trial cohort.

Heads (on standardised, centred BCL embeddings): logistic for lvef_le_40, afib,
male; ridge for lvef and age. Fit on the phenotype set's `train` split (patients
excluded from all trial cohorts by build_ecg_phenotype_set.py), evaluated on its
`test` split, then applied unchanged to the cohort embeddings. Cohort labels and
outcomes are never used. --exclude-cohort drops phenotype-set ECGs of the scored
cohort's patients (fileID -> MRN via ECG metadata) from train and test before
fitting, so no cohort patient contributes to the heads (the COMET set was built
excluding COMET only; later trials reuse it with this filter).

Outputs:
  heads_metrics.json                      held-out AUC / R2 per head (aggregate)
  restricted_cohort_phenotypes.parquet    patient_key + phenotype scores
"""
import argparse
import glob
import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.preprocessing import StandardScaler


def load_shards(directory: str) -> pd.DataFrame:
    shards = sorted(glob.glob(f"{directory}/shard_*[0-9].npy"))
    X = np.concatenate([np.load(f) for f in shards])
    idx = pd.concat([pd.read_csv(f.replace(".npy", "_index.csv"), keep_default_na=False) for f in shards])
    ok = (idx.error == "").to_numpy()
    return pd.DataFrame(X[ok], index=idx.fileID.to_numpy()[ok])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phenotype-set", required=True, help="restricted_phenotype_set.parquet")
    ap.add_argument("--phenotype-embeddings", required=True, help="embedder output dir (shards)")
    ap.add_argument("--cohort-embeddings-glob", required=True,
                    help="parquet(s) with patient_key + embedding (cohort)")
    ap.add_argument("--exclude-cohort", nargs="*", default=[],
                    help="parquet/csv roster(s) with patient_key (=MRN); their ECGs are removed")
    ap.add_argument("--ecg-metadata", default="/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.output_dir, exist_ok=False)

    lab = pd.read_parquet(args.phenotype_set).set_index("fileID")
    n_excl = 0
    if args.exclude_cohort:
        digits = lambda s: s.astype(str).str.replace(r"\D", "", regex=True).str.lstrip("0")
        keys = set()
        for f in args.exclude_cohort:
            keys |= set(digits((pd.read_parquet(f) if f.endswith(".parquet") else pd.read_csv(f)).patient_key))
        meta = pd.read_parquet(args.ecg_metadata, columns=["fileID", "MRN"]).dropna().drop_duplicates("fileID")
        mrn = meta.set_index("fileID").MRN
        drop = digits(pd.Series(lab.index.map(mrn), index=lab.index).fillna("")).isin(keys)
        n_excl = int(drop.sum())
        lab = lab[~drop.to_numpy()]
    E = load_shards(args.phenotype_embeddings)
    lab = lab.loc[lab.index.intersection(E.index)]
    X = E.loc[lab.index].to_numpy(np.float64)
    sc = StandardScaler().fit(X[lab.split.to_numpy() == "train"])
    Z = sc.transform(X)
    tr, te = (lab.split == "train").to_numpy(), (lab.split == "test").to_numpy()

    coh = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(args.cohort_embeddings_glob))])
    Zc = sc.transform(np.stack(coh.embedding.to_numpy()).astype(np.float64))
    scores, metrics = {"patient_key": coh.patient_key.to_numpy()}, {"n_train": int(tr.sum()), "n_test": int(te.sum()),
                                                      "excluded_cohort_ecgs": n_excl}

    for name in ["lvef_le_40", "afib", "male"]:
        y = lab[name].to_numpy()
        m = ~np.isnan(y)
        clf = LogisticRegression(C=0.05, max_iter=5000).fit(Z[tr & m], y[tr & m])
        metrics[f"{name}_test_auc"] = round(float(roc_auc_score(y[te & m], clf.decision_function(Z[te & m]))), 4)
        scores[f"ph_{name}_logit"] = clf.decision_function(Zc)
    for name in ["lvef", "age"]:
        y = lab[name].to_numpy()
        m = ~np.isnan(y)
        reg = Ridge(alpha=100.0).fit(Z[tr & m], y[tr & m])
        metrics[f"{name}_test_r2"] = round(float(r2_score(y[te & m], reg.predict(Z[te & m]))), 4)
        scores[f"ph_{name}_pred"] = reg.predict(Zc)

    pd.DataFrame(scores).to_parquet(f"{args.output_dir}/restricted_cohort_phenotypes.parquet")
    json.dump(metrics, open(f"{args.output_dir}/heads_metrics.json", "w"), indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
