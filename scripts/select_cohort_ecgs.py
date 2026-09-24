#!/usr/bin/env python
"""Select one ECG per cohort patient for BCL embedding, and link embeddings back.

select: latest ECG with an existing waveform in [index-365, index] (index day
        allowed: Ryan's decision 2026-09-23). Ties on the latest day -> the
        lexically last canonical fileID (later acquisition time in the ID).
        Writes restricted_input.csv + restricted_formats_no250.csv for
        bcl_embed_uv.py (all_ecgs is already 500 Hz: no 250 Hz flags).
link:   embedder shards + selection -> restricted_embeddings_part-00000.parquet
        (patient_key, embedding), the format read by the evaluators.

Aggregate coverage only is printed.
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import new_private_dir, sha256, write_manifest  # noqa: E402


def digits(s):
    return s.astype(str).str.replace(r"\D", "", regex=True).str.lstrip("0")


def canonical(fid: str) -> str | None:
    fid = str(fid).strip()
    if fid.endswith(".npy"):
        fid = fid[:-4]
    if not fid or fid.startswith("/") or ".." in fid.split("/"):
        return None
    return fid


def select(a):
    out = new_private_dir(a.output_dir)
    coh = pd.read_parquet(a.cohort)
    coh["mrn"] = digits(coh.person_source_value if "person_source_value" in coh else coh.patient_key)
    coh["idx"] = pd.to_datetime(coh.index_date)
    ecg = pq.read_table(a.ecg_metadata, columns=["fileID", "MRN", "ECGDate"]).to_pandas()
    ecg["mrn"] = digits(ecg.MRN)
    ecg = ecg[ecg.mrn.isin(set(coh.mrn))].copy()
    ecg["t"] = pd.to_datetime(ecg.ECGDate, errors="coerce")
    ecg["fid"] = ecg.fileID.map(canonical)
    ecg = ecg.dropna(subset=["t", "fid"]).drop_duplicates("fid")
    m = coh[["patient_key", "mrn", "idx", "treated"]].merge(ecg[["mrn", "t", "fid"]], on="mrn")
    lag = (m.idx - m.t.dt.normalize()).dt.days
    m = m[(lag >= 0) & (lag <= a.window_days)].copy()
    root = Path(a.waveform_root)
    m["exists"] = [os.path.isfile(root / (f + ".npy")) and not os.path.islink(root / (f + ".npy")) for f in m.fid]
    n_missing_file = int((~m.exists).sum())
    m = m[m.exists].sort_values(["patient_key", "t", "fid"])
    sel = m.groupby("patient_key").tail(1).copy()
    sel["lag_days"] = (sel.idx - sel.t.dt.normalize()).dt.days
    sel[["patient_key", "fid", "lag_days"]].rename(columns={"fid": "fileID"}).to_parquet(out / "restricted_selection.parquet")
    sel[["fid"]].rename(columns={"fid": "fileID"}).to_csv(out / "restricted_input.csv", index=False)
    pd.DataFrame({"fileID": sel.fid, "format_new": "adapter_non250"}).to_csv(out / "restricted_formats_no250.csv", index=False)
    cov = coh.assign(has=coh.patient_key.isin(sel.patient_key)).groupby("treated").has.agg(["size", "mean"])
    summary = dict(window_days=a.window_days, index_day_allowed=True, n_cohort=int(len(coh)),
                   n_selected=int(len(sel)), candidate_ecgs_missing_waveform=n_missing_file,
                   index_day_share=round(float((sel.lag_days == 0).mean()), 3),
                   coverage_by_treated={str(k): round(float(v), 3) for k, v in cov["mean"].items()})
    json.dump(summary, open(out / "summary.json", "w"), indent=2)
    write_manifest(out, dict(script_sha256=sha256(Path(__file__)), cohort=a.cohort))
    print(json.dumps(summary, indent=2))


def link(a):
    sel = pd.read_parquet(Path(a.selection_dir) / "restricted_selection.parquet")
    shards = sorted(glob.glob(f"{a.embeddings_dir}/shard_*[0-9].npy"))
    X = np.concatenate([np.load(f) for f in shards])
    idx = pd.concat([pd.read_csv(f.replace(".npy", "_index.csv"), keep_default_na=False) for f in shards])
    ok = (idx.error == "").to_numpy() & np.isfinite(X).all(1) & (np.abs(X).sum(1) > 0)
    E = pd.Series(list(X[ok].astype(np.float32)), index=idx.fileID.to_numpy()[ok])
    E = E[~E.index.duplicated()]
    sel = sel[sel.fileID.isin(E.index)]
    df = pd.DataFrame({"patient_key": sel.patient_key.to_numpy(), "embedding": E.loc[sel.fileID].to_list()})
    out = Path(a.embeddings_dir).parent / "restricted_embeddings_part-00000.parquet"
    if out.exists():
        raise SystemExit("linked output exists; refusing to overwrite")
    df.to_parquet(out)
    U = X[ok] / np.linalg.norm(X[ok], axis=1, keepdims=True)
    print(json.dumps(dict(linked=int(len(df)), failed=int((~ok).sum()),
                          mean_unit_norm=round(float(np.linalg.norm(U.mean(0))), 4)), indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--cohort", required=True)
    s.add_argument("--ecg-metadata", default="/mnt/raid0/rbc58/mm_vhd/metadata/ecg_metadata.parquet")
    s.add_argument("--waveform-root", default="/mnt/raid0/bb2238/signals/preprocessed/all_ecgs")
    s.add_argument("--window-days", type=int, default=365)
    s.add_argument("--output-dir", required=True)
    l = sub.add_parser("link")
    l.add_argument("--selection-dir", required=True)
    l.add_argument("--embeddings-dir", required=True)
    a = ap.parse_args()
    select(a) if a.cmd == "select" else link(a)


if __name__ == "__main__":
    main()
