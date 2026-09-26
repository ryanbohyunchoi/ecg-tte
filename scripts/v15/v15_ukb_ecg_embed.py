#!/usr/bin/env python
"""v1.5 UK Biobank ECG embedding with the Yale BCL checkpoint (protocol v1.5, UKB arm).

Source: /mnt/raid0/bb2238/signals/preprocessed/ukb_2025/<eid>_20205_<inst>_0.npy, float32
(12, 5000), made by bb2238 setup_ukb_signals.ipynb as raw[:, :5000] / 200 (-> mV) minus a
500-sample median filter; lead order I, II, III, aVR, aVL, aVF, V1-V6 (UKB export metadata).
This matches the Yale all_ecgs layout except orientation; the upstream `load_ecg` transposes
lead-first arrays, so files are read in place. Scale x1000 (mV -> uV) is applied once, by
scripts/bcl_embed_uv.py; no 250 Hz flags.

Subcommands
  prepare  --out DIR           write input CSVs (split into N parts) for bcl_embed_uv.py
  pool     --out DIR           embedder shards -> restricted_ukb_bcl_embeddings.parquet
                               (eid, instance, embedding) + aggregate validation.json
  watch    --out DIR [--hours 24]  link every claude-v15-ukb-<trial> dir once READY_COHORT appears
  link     --out DIR --trial-dir T [--force]
                               cohort.parquet pid -> ecg_embedding.parquet (instance 2,
                               lag_days = 0) + READY_ECG
Aggregates only are printed.
"""
import argparse
import glob
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

SRC = "/mnt/raid0/bb2238/signals/preprocessed/ukb_2025"
YALE_GLOB = "/mnt/raid0/rbc58/ecg-tte/audits/claude-*-bcl*/restricted_embeddings_part-00000.parquet"
os.umask(0o077)


def prepare(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    fids = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith(".npy") and "_20205_" in f)
    inst = pd.Series([f.split("_")[2] for f in fids])
    keep = inst.isin(a.instances.split(",")).to_numpy()
    fids = [f for f, k in zip(fids, keep) if k]
    for p in range(a.parts):
        d = out / f"input_part{p}"
        d.mkdir(exist_ok=False, mode=0o700)
        sub = fids[p :: a.parts]
        pd.DataFrame({"fileID": sub}).to_csv(d / "restricted_input.csv", index=False)
        pd.DataFrame({"fileID": sub, "format_new": "adapter_non250"}).to_csv(
            d / "restricted_formats_no250.csv", index=False)
    print(json.dumps(dict(n_files=len(fids), parts=a.parts,
                          by_instance=inst[keep].value_counts().to_dict())))


def load_all(out: Path):
    X, idx = [], []
    for d in sorted(out.glob("embeddings_part*")):
        for f in sorted(glob.glob(f"{d}/shard_*[0-9].npy")):
            X.append(np.load(f))
            idx.append(pd.read_csv(f.replace(".npy", "_index.csv"), dtype={"fileID": str},
                                   keep_default_na=False))
    return np.concatenate(X), pd.concat(idx, ignore_index=True)


def summ(E):
    E = np.asarray(E, dtype=np.float64)
    n = np.linalg.norm(E, axis=1)
    U = E / n[:, None]
    rng = np.random.default_rng(0)
    s = rng.choice(len(E), size=min(2000, len(E)), replace=False)
    cos = U[s] @ U[s].T
    off = cos[~np.eye(len(s), dtype=bool)]
    Z = E - E.mean(0)
    sv = np.linalg.svd(Z[rng.choice(len(E), size=min(20000, len(E)), replace=False)],
                       compute_uv=False)
    ev = sv**2 / (sv**2).sum()
    return dict(n=int(len(E)), mean_norm=round(float(n.mean()), 3), sd_norm=round(float(n.std()), 3),
                mean_unit_norm=round(float(np.linalg.norm(U.mean(0))), 4),
                mean_pairwise_cos=round(float(off.mean()), 4), p99_pairwise_cos=round(float(np.quantile(off, 0.99)), 4),
                median_dim_sd=round(float(np.median(E.std(0))), 4), n_dims_sd_lt_1e6=int((E.std(0) < 1e-6).sum()),
                pc_var_explained_top5=[round(float(v), 4) for v in ev[:5]],
                n_pcs_for_90pct=int(np.searchsorted(np.cumsum(ev), 0.9) + 1),
                pc1_sd=round(float(sv[0] / np.sqrt(len(sv))), 3))


def pool(a):
    out = Path(a.out)
    X, idx = load_all(out)
    ok = (idx.error == "").to_numpy() & np.isfinite(X).all(1) & (np.abs(X).sum(1) > 0)
    parts = idx.fileID.str.split("_", expand=True)
    df = pd.DataFrame({"eid": parts[0].to_numpy(), "instance": parts[2].astype(int).to_numpy()})[ok]
    df["embedding"] = list(X[ok].astype(np.float32))
    dest = out / "restricted_ukb_bcl_embeddings.parquet"
    if dest.exists():
        raise SystemExit("pooled output exists; refusing to overwrite")
    df.to_parquet(dest, index=False)
    E = np.stack(df.embedding.to_numpy())
    yale = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(YALE_GLOB))[: a.yale_max_files]])
    Y = np.stack(yale.embedding.to_numpy())
    Y = Y[np.random.default_rng(1).choice(len(Y), size=min(20000, len(Y)), replace=False)]
    # distance of UKB mean from Yale mean relative to Yale spread
    shift = float(np.linalg.norm(E.mean(0) - Y.mean(0)) / np.sqrt((Y.var(0)).sum()))
    # Yale PCs applied to UKB: variance captured by Yale's top 32 PCs
    mu = Y.mean(0)
    _, _, Vt = np.linalg.svd(Y - mu, full_matrices=False)
    P = Vt[:32]
    cap = lambda M: float(((M - M.mean(0)) @ P.T).var(0).sum() / (M - M.mean(0)).var(0).sum())
    res = dict(n_rows=int(len(idx)), n_embedded=int(ok.sum()), n_failed=int((~ok).sum()),
               errors=idx.error[idx.error != ""].str[:60].value_counts().head(5).to_dict(),
               by_instance=df.instance.value_counts().to_dict(), n_eid=int(df.eid.nunique()),
               ukb=summ(E), ukb_instance2=summ(E[df.instance.to_numpy() == 2]),
               yale_reference=dict(summ(Y), n_files=int(min(len(glob.glob(YALE_GLOB)), a.yale_max_files))),
               mean_shift_over_yale_total_sd=round(shift, 3),
               yale_top32pc_var_captured=dict(yale=round(cap(Y), 3), ukb=round(cap(E), 3)))
    json.dump(res, open(out / "validation.json", "w"), indent=2)
    print(json.dumps(res, indent=2))


def link(a):
    t = Path(a.trial_dir)
    if not (t / "READY_COHORT").exists():
        raise SystemExit(f"{t.name}: no READY_COHORT")
    dest = t / "ecg_embedding.parquet"
    if dest.exists() and not a.force:
        raise SystemExit(f"{t.name}: ecg_embedding.parquet exists; use --force")
    coh = pd.read_parquet(t / "cohort.parquet", columns=["pid", "treated"])
    emb = pd.read_parquet(Path(a.out) / "restricted_ukb_bcl_embeddings.parquet")
    emb = emb[emb.instance == 2].drop_duplicates("eid")
    m = coh.assign(pid=coh.pid.astype(str)).merge(emb.rename(columns={"eid": "pid"}), on="pid")
    res = m[["pid", "embedding"]].assign(lag_days=0)
    res["embedding"] = [list(map(float, e)) for e in res.embedding]
    tmp = t / ".ecg_embedding.parquet.tmp"
    res.to_parquet(tmp, index=False)
    os.replace(tmp, dest)
    cov = coh.assign(has=coh.pid.astype(str).isin(set(m.pid))).groupby("treated").has.agg(["size", "sum"])
    info = dict(trial_dir=t.name, n_cohort=int(len(coh)), n_with_ecg=int(len(res)),
                with_ecg_by_treated={str(k): int(v) for k, v in cov["sum"].items()},
                source="UKB field 20205 instance 2 (imaging visit = index), BCL trained_12lead_30.pt")
    (t / "READY_ECG").write_text(json.dumps(info) + "\n")
    print(json.dumps(info))


def watch(a):
    """Poll claude-v15-ukb-*/ for READY_COHORT without READY_ECG and link each (detached use)."""
    import time
    root = Path("/mnt/raid0/rbc58/ecg-tte/audits")
    t_end = time.time() + a.hours * 3600
    while time.time() < t_end:
        for t in sorted(root.glob("claude-v15-ukb-*")):
            if t.name in {"claude-v15-ukb-bcl", "claude-v15-ukb-common"}:
                continue
            rc, fl = t / "READY_COHORT", t / ".ecg_link_failed"
            if fl.exists() and rc.exists() and fl.stat().st_mtime > rc.stat().st_mtime:
                continue  # already failed for this READY_COHORT; retry only if it is re-touched
            if rc.exists() and not (t / "READY_ECG").exists():
                time.sleep(30)  # let the cohort agent finish writing
                try:
                    link(argparse.Namespace(out=a.out, trial_dir=str(t), force=False))
                except (SystemExit, Exception) as e:  # keep watching other dirs
                    print(json.dumps(dict(trial_dir=t.name, error=str(e)[:200])), flush=True)
                    (t / ".ecg_link_failed").write_text(str(e)[:500])
        time.sleep(a.poll)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--out", required=True)
    p.add_argument("--parts", type=int, default=2); p.add_argument("--instances", default="2,3")
    q = sub.add_parser("pool"); q.add_argument("--out", required=True)
    q.add_argument("--yale-max-files", type=int, default=12)
    r = sub.add_parser("link"); r.add_argument("--out", required=True)
    r.add_argument("--trial-dir", required=True); r.add_argument("--force", action="store_true")
    w = sub.add_parser("watch"); w.add_argument("--out", required=True)
    w.add_argument("--hours", type=float, default=24); w.add_argument("--poll", type=int, default=60)
    a = ap.parse_args()
    dict(prepare=prepare, pool=pool, link=link, watch=watch)[a.cmd](a)


if __name__ == "__main__":
    main()
