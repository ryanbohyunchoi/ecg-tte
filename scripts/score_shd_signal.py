"""Supervised structural-heart-disease (SHD) ECG scores for a trial cohort (secondary ECG arm).

Models: the 12-lead signal CNNs behind PRESENT-SHD (TF/Keras-2 checkpoints, architecture
`cnn_0` from the pinned CarDS ECG-signal-pipeline checkout). The epoch per model is the one its
developers saved test predictions for (listed in MODELS). Frozen; inference only, on CPU
(this TF build's cuDNN is incompatible with the node's GPUs).

Input: the ECG already selected for the cohort (`select_cohort_ecgs.py`, 365 d, index day
allowed), from all_ecgs (mV). Preprocessing follows training (modules/utils.DataSequence):
first 5000 samples x 12 leads, baseline removal by median filter (500 samples), input in mV
(scale 1). Unlike the torch BCL checkpoint (uV), these TF models expect mV. This was established
2026-09-24 by comparing scale 1 / 1000 / 0.001 on an 800-patient COMET subsample: LVEF<40 AUC
0.79 / 0.63 / 0.36. The x1000 BCL fix does not apply here.

Output (restricted): restricted_shd_scores.parquet: patient_key + shd_<target> logits.
Validation (aggregate): AUC of each score against the latest pre-index echo label (structured
echo report) in cohort patients (a) not in and (b) in the PRESENT-SHD training MRNs. The
difference shows label leakage for patients in the training set.

Run with: TF_USE_LEGACY_KERAS=1 CUDA_VISIBLE_DEVICES="" <mosaic-env python> score_shd_signal.py ...
"""
import argparse
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import median_filter

UPSTREAM = "/mnt/raid0/rbc58/ecg-tte/software/bcl-smoke-runtime-zZ5FVVsd/upstream"
S = "/mnt/nfs_model_saves/signal_model_saves/12Lead_Signal_training"
BASE = "loadedFrom_Unfrozen_CNN0_10s_500Hz_Under40_LR0.001_Dropout0.5_02_17_2024_epoch14"
MODELS = {
    "lvef_lt40": f"{S}/CNN0_10s_500Hz_Under40_LR0.001_Dropout0.5_02_17_2024/trained_12lead_14",
    "modsev_as": f"{S}/CNN0_10s_500Hz_ModerateOrSevereAS_LR0.001_Dropout0.5_02_26_2024_{BASE}/trained_12lead_05",
    "modsev_ar": f"{S}/CNN0_10s_500Hz_ModerateOrSevereAR_LR0.0001_Dropout0.5_03_11_2024_{BASE}/trained_12lead_01",
    "modsev_mr": f"{S}/CNN0_10s_500Hz_ModerateOrSevereMR_LR0.001_Dropout0.5_02_26_2024_{BASE}/trained_12lead_04",
    "modsev_valve": f"{S}/CNN0_10s_500Hz_ModerateOrSevereValveDisease_LR0.001_Dropout0.5_02_26_2024_{BASE}/trained_12lead_04",
    "hcm_lvdd_ivsd15": f"{S}/CNN0_10s_500Hz_HCM_LVDD_IVSd15_IntermediateAsNA_LR1e-05_Dropout0.5_03_05_2024_{BASE}/trained_12lead_02",
}
ECHO = "/mnt/raid0/bb2238/metadata/echo_metadata_2026_06_12.parquet"
TRAIN_MRNS = "/mnt/raid0/rbc58/mosaic/present_shd_train_mrns.txt"
LABELS = {"lvef_lt40": ("EF", lambda v: (v < 40).astype(float)), "modsev_as": ("ModerateOrSevereAS", None),
          "modsev_ar": ("ModerateOrSevereAR", None), "modsev_mr": ("ModerateOrSevereMR", None),
          "modsev_valve": ("ModerateOrSevereValveDisease", None), "hcm_lvdd_ivsd15": ("IVSdAbove15", None)}
ROOT = "/mnt/raid0/bb2238/signals/preprocessed/all_ecgs"
SCALE = 1.0  # mV (see docstring)


def load(fid):
    try:
        x = np.load(f"{ROOT}/{fid}.npy", allow_pickle=False).astype(np.float32)
    except Exception:
        return None
    if x.ndim != 2:
        return None
    if x.shape[0] == 12 and x.shape[1] != 12:
        x = x.T
    if x.shape[0] < 5000 or x.shape[1] < 12:
        return None
    x = x[:5000, :12] * SCALE
    x = x - median_filter(x, size=(500, 1))
    return x if np.isfinite(x).all() else None


def digits(s):
    return s.astype(str).str.replace(r"\D", "", regex=True).str.lstrip("0")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selection", required=True, help="restricted_selection.parquet (patient_key, fileID, lag_days)")
    ap.add_argument("--cohort", required=True, help="restricted_cohort.parquet (patient_key, index_date)")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    os.umask(0o077)
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    sys.path.insert(0, UPSTREAM)
    import tensorflow as tf  # noqa: F401
    from modules.models import cnn_0

    sel = pd.read_parquet(a.selection)
    with Pool(a.workers) as pool:
        sigs = pool.map(load, sel.fileID.tolist(), chunksize=64)
    ok = np.array([s is not None for s in sigs])
    X = np.stack([s for s in sigs if s is not None])[..., None]
    keys = sel.patient_key.to_numpy()[ok]
    scores = {"patient_key": keys}
    for name, w in MODELS.items():
        m = cnn_0((None, 5000, 12, 1), 0.5, labels=["y"])
        m.load_weights(w).assert_existing_objects_matched()
        p = np.clip(m.predict(X, batch_size=256, verbose=0).ravel(), 1e-6, 1 - 1e-6)
        scores[f"shd_{name}"] = np.log(p / (1 - p))
    S_ = pd.DataFrame(scores)
    S_.to_parquet(out / "restricted_shd_scores.parquet")

    # validation against the latest pre-index echo (index day excluded), by training membership
    from sklearn.metrics import roc_auc_score
    coh = pd.read_parquet(a.cohort)[["patient_key", "index_date"]]
    coh["k"] = digits(coh.patient_key)
    e = pd.read_parquet(ECHO, columns=["MRN", "EchoDate"] + [v[0] for v in LABELS.values()])
    e["k"] = digits(e.MRN)
    e["d"] = pd.to_datetime(e.EchoDate, errors="coerce")
    e = e[e.k.isin(set(coh.k))].merge(coh, on="k")
    lag = (pd.to_datetime(e.index_date) - e.d).dt.days
    e = e[(lag >= 1) & (lag <= 365)].sort_values("d").groupby("patient_key").tail(1).set_index("patient_key")
    train = set(digits(pd.read_csv(TRAIN_MRNS, header=None, dtype=str)[0]))
    V = S_.set_index("patient_key").join(e, how="inner")
    V["in_train"] = digits(pd.Series(V.index, index=V.index)).isin(train)
    res = dict(n_ecg=int(len(sel)), n_scored=int(ok.sum()), n_with_echo=int(len(V)),
               share_in_present_shd_training=round(float(V.in_train.mean()), 3) if len(V) else None, auc={})
    for name, (col, f) in LABELS.items():
        y = V[col]
        y = f(pd.to_numeric(y, errors="coerce")).where(y.notna()) if f else y.map({True: 1.0, False: 0.0, "true": 1.0, "false": 0.0})
        for grp, mask in (("not_in_training", ~V.in_train), ("in_training", V.in_train)):
            yy, ss = y[mask], V.loc[mask, f"shd_{name}"]
            m_ = yy.notna()
            if m_.sum() > 50 and yy[m_].nunique() == 2:
                res["auc"][f"{name}|{grp}"] = dict(auc=round(float(roc_auc_score(yy[m_], ss[m_])), 3), n=int(m_.sum()),
                                                  prevalence=round(float(yy[m_].mean()), 3))
    json.dump(res, open(out / "summary.json", "w"), indent=2)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
