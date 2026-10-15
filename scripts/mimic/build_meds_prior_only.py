#!/usr/bin/env python
"""Sensitivity input for CLMBR-T: history BEFORE the index admission only (events with time < index admittime).

Derived from the primary MEDS (OUT/meds) by dropping every event of the index admission (and any outpatient event
between its admission time and t0), for the analysed patients only. This is the MIMIC analogue of Yale's index-day
exclusion taken to the admission level: the index admission's pre-t0 lab and order stream, which overlaps in time with
the held-out lab values, is removed. Subjects left with birth only are encoded from birth (demographics-only).
Writes OUT/meds_prior (same layout and version string as OUT/meds; restricted).
"""
from __future__ import annotations

import json
import sys

import duckdb
import pandas as pd
import pyarrow.parquet as pq

from mimic_common import MEDS, OUT, STAGE, clmbr_codes, status
from build_mimic_meds import SCHEMA, SHARDS, VERSION, digest

DST = OUT / "meds_prior"


def main():
    R = pd.read_parquet(MEDS / "restricted_cohort.parquet")
    A = pd.read_parquet(OUT / "analysed_pids.parquet")
    R = R.merge(A, on=["trial", "pid"])
    con = duckdb.connect()
    con.execute("SET threads=32")
    con.register("r", R[["subject_id", "mimic_subject_id", "hadm_id", "t0"]])
    con.execute(f"""CREATE TABLE ix AS SELECT r.subject_id, a.admittime FROM r JOIN read_parquet('{STAGE}/admissions.parquet') a
                    ON a.subject_id = r.mimic_subject_id AND a.hadm_id = r.hadm_id""")
    assert con.execute("SELECT count(*) FROM ix").fetchone()[0] == len(R)
    con.execute(f"""CREATE TABLE ev AS SELECT m.* FROM read_parquet('{MEDS}/data/*.parquet') m JOIN ix USING (subject_id)
                    WHERE m.code = 'MEDS_BIRTH' OR m."time" < ix.admittime""")
    chk = con.execute("""SELECT count(*) FROM ev JOIN ix USING (subject_id) WHERE ev.code <> 'MEDS_BIRTH' AND ev."time" >= ix.admittime""").fetchone()[0]
    assert chk == 0
    DST.mkdir(exist_ok=False)
    (DST / "data").mkdir()
    (DST / "metadata").mkdir()
    outputs, rows = {}, 0
    for b in range(SHARDS):
        T = con.execute(f"""SELECT * FROM ev WHERE subject_id % {SHARDS} = {b} ORDER BY subject_id, "time", code, source_domain""").fetch_arrow_table()
        if T.num_rows:
            p = DST / "data" / f"part-{b:03d}.parquet"
            pq.write_table(T.cast(SCHEMA), p, compression="zstd")
            outputs[str(p.relative_to(DST))] = digest(p)
            rows += T.num_rows
    vocab = clmbr_codes()
    E = con.execute("SELECT subject_id, code FROM ev WHERE code <> 'MEDS_BIRTH'").df()
    E["iv"] = E.code.isin(vocab)
    n_ev = E.groupby("subject_id").size()
    n_iv = E[E.iv].groupby("subject_id").size()
    R["n_events"] = R.subject_id.map(n_ev).fillna(0).astype(int)
    R["n_in_vocab"] = R.subject_id.map(n_iv).fillna(0).astype(int)
    R["clinical_meds_rows"] = R.n_events
    R.to_parquet(DST / "restricted_cohort.parquet", index=False)
    outputs["restricted_cohort.parquet"] = digest(DST / "restricted_cohort.parquet")
    json.dump(dict(version=VERSION, variant="prior_only"), open(DST / "metadata" / "dataset.json", "w"))
    outputs["metadata/dataset.json"] = digest(DST / "metadata" / "dataset.json")
    json.dump(dict(version=VERSION, outputs=outputs), open(DST / "manifest.json", "w"), indent=1)
    s = dict(version=VERSION, status="complete_cohort_meds", variant="prior_only: events before the index admission",
             subjects=len(R), rows=rows, events_at_or_after_index_admit=int(chk),
             share_events_in_vocab=float(E.iv.mean()), share_no_prior_coded_history=float((R.n_in_vocab == 0).mean()),
             median_in_vocab=float(R.n_in_vocab.median()))
    json.dump(s, open(DST / "summary.json", "w"), indent=1)
    print(json.dumps(s, indent=1))
    status(f"sensitivity MEDS (history before the index admission only; analysed patients): {len(R)} subjects; in-vocab share "
           f"{s['share_events_in_vocab']:.3f}; no prior coded history {100 * s['share_no_prior_coded_history']:.1f}%")


if __name__ == "__main__":
    sys.exit(main())
