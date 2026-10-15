"""Verifier check 3: model / runtime hashes vs Yale; embedding QC (aggregate)."""
import glob
import hashlib
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
MODEL = "/mnt/raid0/eo287/clmbr"
Y = json.load(open("/mnt/raid0/rbc58/ecg-tte/audits/claude-plato-clmbr-codeonly/report/manifest.json"))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


own = {n: sha(f"{MODEL}/{n}") for n in ("config.json", "dictionary.msgpack", "model.safetensors")}
print("own sha256 == Yale manifest model_sha256:", own == Y["model_sha256"])
print("Yale runtime:", Y["runtime"])
for run in ("smoke100", "full", "prior_full"):
    m = json.load(open(f"{OUT}/clmbr/{run}/manifest.json"))
    s = json.load(open(f"{OUT}/clmbr/{run}/summary.json"))
    print(run, "| model_sha256 == Yale:", m["model_sha256"] == Y["model_sha256"], "| == own:", m["model_sha256"] == own,
          "| runtime == Yale:", m["runtime"] == Y["runtime"], "| numeric_mode", m.get("numeric_mode"), "| max_tokens", m.get("max_tokens"),
          "| status", s["status"], "| emb dim", s.get("embedding_dimension"))
    # output digests
    bad = sum(sha(f"{OUT}/clmbr/{run}/{n}") != h for n, h in m["outputs"].items())
    print("   output files listed", len(m["outputs"]), "digest mismatches", bad)
    mm = json.load(open(f"{OUT}/{'meds_prior' if run == 'prior_full' else 'meds'}/manifest.json"))
    print("   meds_manifest_sha256 matches current MEDS manifest:", m["meds_manifest_sha256"] == sha(f"{OUT}/{'meds_prior' if run == 'prior_full' else 'meds'}/manifest.json"))
    if run == "smoke100":
        continue
    roster = pd.read_parquet(f"{OUT}/{'meds_prior' if run == 'prior_full' else 'meds'}/restricted_cohort.parquet")
    files = sorted(glob.glob(f"{OUT}/clmbr/{run}/restricted_embeddings_part-*.parquet"))
    n, ids, keys, fin, dims = 0, [], [], True, set()
    for f in files:
        T = pq.read_table(f, columns=["subject_id", "patient_key", "embedding"]).to_pandas()
        X = np.stack(T.embedding.to_numpy()).astype(np.float64)
        dims.add(X.shape[1])
        fin &= bool(np.isfinite(X).all())
        zero = int((np.linalg.norm(X, axis=1) == 0).sum())
        ids += T.subject_id.tolist()
        keys += T.patient_key.tolist()
        n += len(T)
    ids = pd.Series(ids)
    print(f"   embeddings {n:,}; roster {len(roster):,}; unique subject_id {ids.is_unique}; set == roster {set(ids) == set(roster.subject_id)};"
          f" unique patient_key {pd.Series(keys).is_unique}; dims {dims}; all finite {fin}")
    st = pd.read_parquet(f"{OUT}/clmbr/{run}/restricted_patient_status.parquet")
    print("   status shares:", {k: round(float(v), 4) for k, v in st.status.value_counts(normalize=True).items()})
    j = st.merge(roster[["subject_id", "n_in_vocab"]], on="subject_id")
    print(f"   tokenizer accepted == builder n_in_vocab: {int((j.accepted == j.n_in_vocab).sum()):,} of {len(j):,}")
    print(f"   truncated (tokens_available > 4096) share {float((st.tokens_available > 4096).mean()):.4f}")
    A = pd.read_parquet(f"{OUT}/analysed_pids.parquet")
    ja = st.merge(A, on=["trial", "pid"])
    print(f"   analysed patients with an embedding {len(ja):,} of {len(A):,}; birth-only share among analysed {float((ja.status == 'encoded_birth_only').mean()):.4f};"
          f" truncated share among analysed {float((ja.tokens_available > 4096).mean()):.4f}")
