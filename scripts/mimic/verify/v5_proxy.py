"""Verifier check 5: is any unmasked held-out item (C: ventilation at t0) strongly proxied by a code in the CLMBR-T
input? Pooled and per-trial phi correlation between 'any arterial blood-gas code (LOINC 2744-1 / 2703-7 / 2026-3)
in the 24 h before t0' and vent_at_t0, over analysed patients (aggregates only: correlations, no counts)."""
import duckdb
import numpy as np
import pandas as pd

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
HO = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v20-mimic-replication/heldout"
TR = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2"]
R = pd.read_parquet(f"{OUT}/meds/restricted_cohort.parquet")[["subject_id", "trial", "pid", "t0"]]
A = pd.read_parquet(f"{OUT}/analysed_pids.parquet")
R = R.merge(A, on=["trial", "pid"])
con = duckdb.connect()
con.execute("SET threads=32")
con.register("r", R)
G = con.execute(f"""SELECT r.subject_id,
      max(CASE WHEN e.code IN ('LOINC/2744-1','LOINC/2703-7','LOINC/2026-3') AND e."time" >= r.t0 - INTERVAL 24 HOUR THEN 1 ELSE 0 END) abg24,
      max(CASE WHEN e.code IN ('LOINC/2744-1','LOINC/2703-7','LOINC/2026-3') THEN 1 ELSE 0 END) abg_any
    FROM r JOIN read_parquet('{OUT}/meds/data/*.parquet') e USING (subject_id) GROUP BY 1""").df()
R = R.merge(G, on="subject_id", how="left").fillna({"abg24": 0, "abg_any": 0})
rows = []
for k in TR:
    H = pd.read_parquet(f"{HO}/{k}.parquet")[["pid", "vent_at_t0"]].assign(pid=lambda x: x.pid.astype(str))
    rows.append(R[R.trial == k].merge(H, on="pid"))
X = pd.concat(rows)
for c in ("abg24", "abg_any"):
    r_pool = np.corrcoef(X[c], X.vent_at_t0)[0, 1]
    per = [np.corrcoef(g[c], g.vent_at_t0)[0, 1] for _, g in X.groupby("trial") if g[c].std() > 0 and g.vent_at_t0.std() > 0]
    print(f"{c}: pooled phi with vent_at_t0 {r_pool:.2f}; per-trial range {min(per):.2f} to {max(per):.2f}")
