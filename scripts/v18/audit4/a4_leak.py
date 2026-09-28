"""Round-4 audit: independent CLMBR input-window and exposure-token check from the MEDS inputs (not the v18 leakage code).

Per trial (MEDS roster = all cohort members with a MEDS build; not restricted to the analysed intersection):
  * events at/after index midnight, max event offset, % patients whose last event is on index-1, domain mix on index-1;
  * exposure tokens: drug_exposure rows whose concept NAME (CONCEPT.csv) contains any arm keyword (own arm / other arm),
    matched on source_concept_id; and whether the MEDS `code` string is in the CLMBR-T code vocabulary.
Aggregates only; counts 1-10 suppressed."""
import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts")
sys.path.insert(0, os.path.dirname(__file__))
from a4_common import A, OUT, ALL33, AF5  # noqa: E402
from trial_specs import TRIALS as SPECS  # noqa: E402
from v13_common import PRIMARY, EXTRA  # noqa: E402

os.umask(0o077)
KEY = {n: {**PRIMARY, **EXTRA}[n][0] for n in ALL33 + AF5}
MOS = "/mnt/raid0/rbc58/ecg-tte/software/mosaic-env/bin/python"
code = ("import msgpack,sys;d=msgpack.load(open('/mnt/raid0/eo287/clmbr/dictionary.msgpack','rb'));"
        "sys.stdout.write('\\n'.join(sorted({x['code_string'] for x in d['vocab'] if x['type']=='code'})))")
VOC = set(subprocess.run([MOS, "-c", code], capture_output=True, text=True, check=True).stdout.split("\n"))
con = duckdb.connect()
con.execute("SET threads=16")
CN = con.execute("SELECT CAST(concept_id AS BIGINT) cid, lower(concept_name) nm FROM read_csv('/mnt/raid0/rbc58/mosaic/mapping/CONCEPT.csv', "
                 "delim='\t', quote='', header=true, all_varchar=true) WHERE domain_id = 'Drug'").df()


def sup(k, n):
    return 0.0 if k == 0 else (round(100 * k / n, 2) if k >= 11 else "<11 pts")


rows = []
for n in ALL33 + AF5:
    root = Path("/mnt/raid0/rbc58/ecg-tte/shared/comet-meds-v1-3hgAkgoB/meds") if n == "comet" else \
        Path(f"/mnt/raid0/rbc58/ecg-tte/shared/claude-{n}-meds-v2/meds")
    if not root.exists():
        rows.append(dict(trial=n, status="no MEDS dir"))
        continue
    ro = pd.read_parquet(root / "restricted_cohort.parquet", columns=["subject_id", "treatment_arm", "index_date"])
    ro["idx"] = pd.to_datetime(ro.index_date)
    spec = SPECS[KEY[n]]
    arms = [a for a, _ in spec["arms"]]
    ro["arm"] = ro.treatment_arm.map({a: i for i, a in enumerate(arms)})
    con.register("ro", ro[["subject_id", "arm", "idx"]])
    g = f"{root}/data/*.parquet"
    t = con.execute(f"""SELECT count(*) FILTER (WHERE m.time >= r.idx), max(m.time - r.idx), count(*)
        FROM read_parquet('{g}') m JOIN ro r USING (subject_id) WHERE m.source_domain <> 'birth'""").fetchone()
    last = con.execute(f"""SELECT count(*) FILTER (WHERE d = 1), count(*) FROM (SELECT m.subject_id,
        min(date_diff('day', CAST(m.time AS DATE), CAST(r.idx AS DATE))) d FROM read_parquet('{g}') m JOIN ro r USING (subject_id)
        WHERE m.source_domain <> 'birth' GROUP BY 1)""").fetchone()
    dom1 = con.execute(f"""SELECT m.source_domain, count(*) FROM read_parquet('{g}') m JOIN ro r USING (subject_id)
        WHERE CAST(m.time AS DATE) = CAST(r.idx AS DATE) - 1 GROUP BY 1""").df()
    # exposure concepts by concept name (independent of the builder's '-'-split source-value rule)
    ex = []
    for i, (_, kws) in enumerate(spec["arms"]):
        kl = [k.lower() for k in kws if len(k) >= 5]
        c = CN[CN.nm.apply(lambda s: any(k in s for k in kl))].cid
        ex += [(i, int(x)) for x in c]
    X = pd.DataFrame(ex, columns=["arm_e", "cid"]).drop_duplicates()
    con.register("ex", X)
    H = con.execute(f"""SELECT m.subject_id, r.arm, e.arm_e, m.code, min(date_diff('day', CAST(m.time AS DATE), CAST(r.idx AS DATE))) dmin
        FROM read_parquet('{g}') m JOIN ro r USING (subject_id) JOIN ex e ON CAST(m.source_concept_id AS BIGINT) = e.cid
        WHERE m.source_domain = 'drug_exposure' GROUP BY 1, 2, 3, 4""").df()
    H["voc"] = H.code.isin(VOC)
    N = len(ro)
    own, oth = H[H.arm == H.arm_e], H[H.arm != H.arm_e]
    r = dict(trial=n, design=spec.get("design") or "new_user", n_roster=N, events_at_or_after_index=(0 if t[0] == 0 else (int(t[0]) if t[0] >= 11 else "<11")), max_offset=str(t[1]),
             pct_last_event_index_minus1=sup(last[0], last[1]),
             idx_minus1_domain_share=json.dumps((dom1.set_index(dom1.columns[0]).iloc[:, 0] / dom1.iloc[:, 1].sum()).round(3).to_dict()),
             n_expo_codes=int(H.code.nunique()), n_expo_codes_in_vocab=int(H[H.voc].code.nunique()),
             pct_own_any=sup(own.subject_id.nunique(), N), pct_own_vocab=sup(own[own.voc].subject_id.nunique(), N),
             pct_own_vocab_365d=sup(own[own.voc & (own.dmin <= 365)].subject_id.nunique(), N),
             pct_other_any=sup(oth.subject_id.nunique(), N), pct_other_vocab=sup(oth[oth.voc].subject_id.nunique(), N),
             pct_other_vocab_365d=sup(oth[oth.voc & (oth.dmin <= 365)].subject_id.nunique(), N))
    rows.append(r)
    print(r, flush=True)
L = pd.DataFrame(rows)
L.to_csv(OUT + "clmbr_leak_independent.csv", index=False)
print(L.drop(columns=["idx_minus1_domain_share"]).to_string())
