#!/usr/bin/env python
"""v1.5 MIMIC ECG pipeline: select -> convert -> BCL embed -> link, per trial.

prepare <trial>: latest 12-lead ECG with ecg_time in [index_datetime - 365 d, index_datetime] per
    pid (record_list.csv, joined on subject_id). Candidates are tried latest-first; if the
    latest fails conversion the next latest in the window is used (analogue of the Yale rule
    "latest ECG with an existing waveform"). Writes restricted inputs for bcl_embed_uv.py into
    audits/claude-v15-mimic-bcl-<trial>/input.
embed <trial>: bcl_embed_uv.py with the Yale flags (checkpoint CK, x1000 uV fix inside the
    wrapper, adapter_non250 formats), data root = the private MIMIC npy dir. Picks GPU 2 or 3
    only, after checking nvidia-smi (<1 GB used); waits otherwise.
link <trial>: shards -> <trial dir>/ecg_embedding.parquet (pid, embedding[256], lag_days),
    aggregate ecg_summary.json in the BCL dir, then READY_ECG.
run <trials...>: poll READY_COHORT and do all of the above for each trial.

Only aggregate numbers are printed.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v15_mimic_ecg_convert import MIMIC_ROOT, NPY_ROOT, convert  # noqa: E402

ROOT = Path("/mnt/raid0/rbc58/ecg-tte")
AUD = ROOT / "audits"
BCL = ROOT / "software/bcl-smoke-runtime-zZ5FVVsd"
CK = ("/mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/CNN0_lead_time_transformer_10s_500Hz"
      "_BCL_LR0.0001_Dropout0.5_08_26_2026/trained_12lead_30.pt")
WRAPPER = Path(__file__).resolve().parents[1] / "bcl_embed_uv.py"
GPUS = (2, 3)
WINDOW = pd.Timedelta(days=365)
os.umask(0o077)


def tdir(trial):
    """Trial dir; accepts rocket_af / rocket-af spellings (whichever exists, underscore first)."""
    for name in (trial, trial.replace("_", "-"), trial.replace("-", "_")):
        if (AUD / f"claude-v15-mimic-{name}").exists():
            return AUD / f"claude-v15-mimic-{name}"
    return AUD / f"claude-v15-mimic-{trial}"


def bdir(trial):
    return AUD / f"claude-v15-mimic-bcl-{trial}"


def log(msg):
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)


def _conv(args):
    return convert(*args)


def prepare(trial, workers=48):
    T, B = tdir(trial), bdir(trial)
    inp = B / "input"
    inp.mkdir(parents=True, exist_ok=True)
    Path(NPY_ROOT).mkdir(parents=True, exist_ok=True)
    it = pd.read_parquet(T / "index_time.parquet")
    it["pid"] = it.pid.astype(str)
    it["index_datetime"] = pd.to_datetime(it.index_datetime)
    rl = pd.read_csv(f"{MIMIC_ROOT}/record_list.csv", usecols=["subject_id", "study_id", "ecg_time", "path"])
    rl["ecg_time"] = pd.to_datetime(rl.ecg_time)
    m = it[["pid", "subject_id", "index_datetime"]].merge(rl, on="subject_id")
    m = m[(m.ecg_time <= m.index_datetime) & (m.ecg_time >= m.index_datetime - WINDOW)].copy()
    m = m.sort_values(["pid", "ecg_time", "study_id"], ascending=[True, False, False])
    m["rank"] = m.groupby("pid").cumcount()
    status = {}
    fail_detail = {}
    chosen = {}
    tried = 0
    r = 0
    pending = m[m["rank"] == 0]
    with ProcessPoolExecutor(workers) as ex:
        while len(pending):
            todo = pending.drop_duplicates("study_id")
            todo = todo[~todo.study_id.isin(status)]
            res = list(ex.map(_conv, zip(todo.study_id, todo.path), chunksize=16))
            tried += len(todo)
            for sid, (st, det) in zip(todo.study_id, res):
                status[sid] = st
                if st == "fail":
                    fail_detail[det] = fail_detail.get(det, 0) + 1
            ok = pending[pending.study_id.map(lambda s: status[s] != "fail")]
            for row in ok.itertuples():
                chosen[row.pid] = row
            failed_pids = set(pending.pid) - set(ok.pid)
            r += 1
            pending = m[(m["rank"] == r) & m.pid.isin(failed_pids)]
    sel = pd.DataFrame([dict(pid=c.pid, fileID=str(c.study_id), ecg_time=c.ecg_time,
                             index_datetime=c.index_datetime) for c in chosen.values()])
    sel["lag_days"] = (sel.index_datetime.dt.normalize() - sel.ecg_time.dt.normalize()).dt.days
    sel["fallback"] = sel.pid.map(lambda p: chosen[p].rank > 0)
    sel[["pid", "fileID", "lag_days"]].to_parquet(inp / "restricted_selection.parquet")
    u = sel.drop_duplicates("fileID")
    u[["fileID"]].to_csv(inp / "restricted_input.csv", index=False)
    pd.DataFrame({"fileID": u.fileID, "format_new": "adapter_non250"}).to_csv(
        inp / "restricted_formats_no250.csv", index=False)
    n_with_cand = int(m.pid.nunique())
    summary = dict(trial=trial, n_index=int(len(it)), n_with_candidate_ecg=n_with_cand,
                   n_selected=int(len(sel)), records_converted_or_reused=int(sum(s != "fail" for s in status.values())),
                   records_tried=int(tried), conversion_failures=fail_detail,
                   pids_all_candidates_failed=int(n_with_cand - len(sel)),
                   pids_using_fallback_ecg=int(sel.fallback.sum()),
                   index_day_share=round(float((sel.lag_days == 0).mean()), 3) if len(sel) else None,
                   lag_days_median=float(sel.lag_days.median()) if len(sel) else None)
    json.dump(summary, open(inp / "prepare_summary.json", "w"), indent=2)
    log(f"{trial} prepare: {json.dumps(summary)}")
    return summary


def gpu_used():
    q = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True, check=True).stdout
    return {int(a): float(b) for a, b in (l.split(",") for l in q.strip().splitlines())}


def pick_gpu():
    while True:
        used = gpu_used()
        free = [g for g in GPUS if used.get(g, 1e9) < 1024]
        if free:
            return free[0]
        log(f"GPUs {GPUS} busy ({[used.get(g) for g in GPUS]} MiB); waiting")
        time.sleep(120)


def embed(trial):
    B = bdir(trial)
    inp, emb = B / "input", B / "embeddings"
    gpu = pick_gpu()
    log(f"{trial} BCL on GPU {gpu} (nvidia-smi checked just now)")
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu))
    cmd = [str(BCL / "env/bin/python"), str(WRAPPER), "--upstream-dir", str(BCL / "upstream"), "--",
           "--checkpoint-path", CK, "--input-file", str(inp / "restricted_input.csv"),
           "--formats-csv", str(inp / "restricted_formats_no250.csv"), "--data-roots", NPY_ROOT,
           "--output-dir", str(emb), "--batch-size", "64", "--num-workers", "8", "--shard-size", "512",
           "--no-quality-filter", "--no-deduplicate", "--no-partial", "--no-amp", "--no-overwrite",
           "--no-ddp-autodetect"]
    with open(B / "run.log", "w") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, check=True,
                       cwd=str(WRAPPER.parent))
    log(f"{trial} BCL done: {subprocess.run(['tail', '-2', str(B / 'run.log')], capture_output=True, text=True).stdout.strip()}")


def emb_stats(X):
    X = X.astype(np.float64)
    U = X / np.linalg.norm(X, axis=1, keepdims=True)
    rng = np.random.default_rng(0)
    i = rng.integers(0, len(U), 20000)
    j = rng.integers(0, len(U), 20000)
    keep = i != j
    cos = float((U[i[keep]] * U[j[keep]]).sum(1).mean())
    Z = X - X.mean(0)
    s = np.linalg.svd(Z[: min(len(Z), 20000)], compute_uv=False)
    ev = s ** 2 / (s ** 2).sum()
    return dict(n=int(len(X)), mean_pairwise_cosine=round(cos, 4),
                mean_unit_norm=round(float(np.linalg.norm(U.mean(0))), 4),
                median_dim_sd=round(float(np.median(X.std(0))), 4),
                n_dims_sd_below_1e4=int((X.std(0) < 1e-4).sum()),
                pc1_5_explained=[round(float(v), 4) for v in ev[:5]],
                pcs_for_90pct=int(np.searchsorted(np.cumsum(ev), 0.9) + 1),
                pc1_sd=round(float(s[0] / np.sqrt(min(len(Z), 20000))), 4))


def link(trial):
    T, B = tdir(trial), bdir(trial)
    sel = pd.read_parquet(B / "input/restricted_selection.parquet")
    shards = sorted(glob.glob(f"{B}/embeddings/shard_*[0-9].npy"))
    X = np.concatenate([np.load(f) for f in shards])
    idx = pd.concat([pd.read_csv(f.replace(".npy", "_index.csv"), keep_default_na=False, dtype={"fileID": str})
                     for f in shards])
    ok = (idx.error == "").to_numpy() & np.isfinite(X).all(1) & (np.abs(X).sum(1) > 0)
    E = pd.Series(list(X[ok].astype(np.float32)), index=idx.fileID.to_numpy()[ok])
    E = E[~E.index.duplicated()]
    sel = sel[sel.fileID.isin(E.index)]
    df = pd.DataFrame({"pid": sel.pid.astype(str).to_numpy(),
                       "embedding": [list(map(float, v)) for v in E.loc[sel.fileID]],
                       "lag_days": sel.lag_days.astype(float).to_numpy()})
    assert df.pid.is_unique and (df.lag_days >= 0).all() and all(len(v) == 256 for v in df.embedding)
    out = T / "ecg_embedding.parquet"
    if out.exists():
        raise SystemExit(f"{out} exists; refusing to overwrite")
    tmp = T / ".ecg_embedding.tmp.parquet"
    df.to_parquet(tmp)
    os.replace(tmp, out)
    # aggregate coverage by arm
    cov = {}
    cp = T / "cohort.parquet"
    if cp.exists():
        c = pd.read_parquet(cp, columns=["pid", "treated"])
        c["pid"] = c.pid.astype(str)
        c["has"] = c.pid.isin(set(df.pid))
        for k, g in c.groupby("treated"):
            cov[str(int(k))] = dict(n=int(len(g)), with_ecg=int(g.has.sum()), share=round(float(g.has.mean()), 3))
    summ = dict(json.load(open(B / "input/prepare_summary.json")), linked=int(len(df)),
                embed_failed=int((~ok).sum()), coverage_by_treated=cov,
                embedding_stats=emb_stats(np.stack(df.embedding.map(np.asarray).to_list())))
    json.dump(summ, open(B / "ecg_summary.json", "w"), indent=2)
    (T / "READY_ECG").write_text(json.dumps(dict(linked=int(len(df)), time=time.strftime("%F %T"))) + "\n")
    log(f"{trial} linked: {json.dumps(summ)}")


def run(trials, poll=300):
    left = list(trials)
    while left:
        for t in list(left):
            T = tdir(t)
            if (T / "READY_ECG").exists():
                log(f"{t}: READY_ECG already present; skipping")
                left.remove(t)
                continue
            if not (T / "READY_COHORT").exists():
                continue
            if not (T / "index_time.parquet").exists():
                log(f"{t}: READY_COHORT but no index_time.parquet; waiting")
                continue
            try:
                log(f"{t}: READY_COHORT found; start")
                if not (bdir(t) / "input/prepare_summary.json").exists():
                    prepare(t)
                embed(t)
                link(t)
            except Exception as e:  # noqa: BLE001
                log(f"{t}: FAILED {type(e).__name__}: {e}")
                (bdir(t) / "FAILED").write_text(f"{type(e).__name__}: {e}\n")
            left.remove(t)
        if left:
            log(f"waiting for READY_COHORT: {left}")
            time.sleep(poll)
    log("all trials processed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "embed", "link", "run"])
    ap.add_argument("trials", nargs="+")
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.trials)
    else:
        for t in a.trials:
            globals()[a.cmd](t)


if __name__ == "__main__":
    main()
