"""Round-4 audit: patient-level overlap between selected trial cohorts (the near-duplicate rule uses exact
(patient, index date) identity only). Shares are of the first cohort's persons. Aggregates only."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts")
from a4_common import A, OUT  # noqa: E402
import pandas as pd  # noqa: E402
from v13_common import PRIMARY, EXTRA  # noqa: E402

os.umask(0o077)
CD = {n: v[1] for n, v in {**PRIMARY, **EXTRA}.items()}
PAIRS = [("affirm", "east-afnet4"), ("af-chf", "east-afnet4"), ("af-chf", "affirm"), ("active-w", "rely"), ("active-w", "aristotle"),
         ("frail-af", "aristotle"), ("frail-af", "rocket-af"), ("frail-af", "rely"), ("frail-af", "affirm"), ("protect-af", "affirm"),
         ("raft-af", "cabana-v2"), ("raft-af", "east-afnet4"), ("raft-af", "af-chf"), ("laaos3", "affirm"), ("leader", "empa-reg"),
         ("insight", "allhat"), ("valiant", "ontarget"), ("sustain6", "leader"), ("declare", "empa-reg")]


def coh(n):
    c = pd.read_parquet(A + CD[n] + "/restricted_cohort.parquet", columns=["person_id", "index_date", "treatment_arm"])
    c["index_date"] = pd.to_datetime(c.index_date)
    return c


rows = []
for a, b in PAIRS:
    x, y = coh(a), coh(b)
    m = x.merge(y, on="person_id", suffixes=("", "_b"))
    dd = (m.index_date - m.index_date_b).dt.days.abs()
    n = x.person_id.nunique()
    rows.append(dict(cohort=a, other=b, n_persons=n, share_persons_in_other=round(m.person_id.nunique() / n, 3),
                     share_same_index=round(m[dd == 0].person_id.nunique() / n, 3),
                     share_index_within_30d=round(m[dd <= 30].person_id.nunique() / n, 3),
                     share_index_within_365d=round(m[dd <= 365].person_id.nunique() / n, 3)))
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(OUT + "overlap_persons.csv", index=False)
