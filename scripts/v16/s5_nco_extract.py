#!/usr/bin/env python
"""v1.6 S5: extract additional negative-control outcomes (NCOs) for the 18 v1.6 trials (exploratory).

Same conventions as scripts/v13_extract.py (NCO block; v1.2 rules): first diagnosis strictly after index,
patients with the code in [index - 365 d, index] set to NaN (excluded for that NCO), follow-up to
min(DEATH_END, index + max(horizon, 60 months)), death (OMOP gold death table; deaths before index ignored)
censors, t <= 0 set to 0.5.  Diagnosis codes matched as prefixes on upper(replace(condition_source_value,
'.', '')).  Validation NCOs (nco_skin_cancer C44, nco_dental_caries K02, already in the v1.3 file) are
re-extracted and must match restricted_outcomes_v13.parquet exactly.

  python s5_nco_extract.py [--trials a,b] [--threads 16]
Restricted output: /mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s5-nco/extract/restricted_nco_<trial>.parquet
Aggregate: extract/summary_<trial>.json (event counts, 1-10 suppressed).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from trial_common import code_like, connect, rp  # noqa: E402
from trial_specs import DEATH_END, HORIZON_MONTHS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY  # noqa: E402

OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s5-nco/extract")
TRIALS = ["comet", "paradigm-hf-seq", "transform-hf", "elite-ii", "life", "plato", "aristotle", "rocket-af", "rely",
          "allhat", "emperor-preserved-v2", "east-afnet4", "cabana-v2", "ontarget", "value", "ascot", "empa-reg", "carolina"]
# new v1.6 NCOs (ICD-10-CM prefixes); plausibility exclusions per trial are applied in s5_nco.py
NEW_NCO = {"nco_hearing_loss": ["H90", "H91"], "nco_benign_skin_neoplasm": ["D22", "D23"],
           "nco_cholelithiasis": ["K80"], "nco_appendicitis": ["K35"], "nco_radiculopathy": ["M541", "M511"],
           "nco_knee_oa": ["M17"], "nco_hip_oa": ["M16"], "nco_actinic_keratosis": ["L570"],
           "nco_lateral_epicondylitis": ["M771"], "nco_blepharitis": ["H010"], "nco_de_quervain": ["M654"],
           "nco_low_back_pain": ["M545"]}
CHECK = {"nco_skin_cancer": ["C44"], "nco_dental_caries": ["K02"]}


def one(n, threads, gold="/mnt/raid0/rbc58/omop/gold"):
    key, cdir = {**PRIMARY, **EXTRA}[n]
    r = pd.read_parquet(f"{A}/{cdir}/restricted_cohort.parquet")[["patient_key", "person_id", "index_date", "treated"]]
    con = connect(threads)
    con.register("r0", r)
    con.execute("""CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx,
                   treated FROM r0""")
    horizon_days = int(round(HORIZON_MONTHS[key] * 30.4375))
    follow_days = max(horizon_days, int(round(60 * 30.4375)))
    death = con.execute(f"""SELECT r.patient_key, min(d.death_date) dd FROM r JOIN {rp(gold, 'death')} d USING (person_id)
                            GROUP BY 1""").df().set_index("patient_key").dd
    idx = pd.to_datetime(r.set_index("patient_key").index_date)
    keys = idx.index
    dd = pd.to_datetime(death.reindex(keys))
    dd = dd.where(~(dd.notna() & (dd < idx)))
    allc = {**NEW_NCO, **CHECK}
    codes = sorted({c for v in allc.values() for c in v})
    q = f"""SELECT r.patient_key, upper(replace(c.condition_source_value, '.', '')) code, c.condition_start_date d
            FROM r JOIN {rp(gold, 'condition_occurrence')} c USING (person_id)
            WHERE {code_like("upper(replace(c.condition_source_value, '.', ''))", codes)}"""
    ev_all = con.execute(q).df()
    ev_all["d"] = pd.to_datetime(ev_all.d)
    ev_all = ev_all.merge(idx.rename("idx").reset_index(), on="patient_key")
    res = pd.DataFrame(index=keys)
    endn = pd.Series(pd.Timestamp(DEATH_END), index=keys).clip(upper=idx + pd.Timedelta(days=follow_days))
    for name, pref in allc.items():
        e = ev_all[ev_all.code.str.startswith(tuple(pref))]
        prior = set(e[(e.d >= e.idx - pd.Timedelta(days=365)) & (e.d <= e.idx)].patient_key)
        post = e[e.d > e.idx].groupby("patient_key").d.min().reindex(keys)
        stop = pd.concat([post, endn, dd], axis=1).min(axis=1)
        evn = post.notna() & (post <= endn) & ~(dd < post)
        stop = stop.where(~evn, post)
        tt = (stop - idx).dt.days.astype(float)
        tt = tt.where(tt > 0, 0.5)
        ee = evn.astype(float)
        m = keys.isin(prior)
        tt[m], ee[m] = np.nan, np.nan
        res[f"t_{name}"], res[f"e_{name}"] = tt, ee
    # validation against the v1.3 extraction
    O3 = pd.read_parquet(f"{A}/claude-{n}-outcomes-v13/restricted_outcomes_v13.parquet").set_index("patient_key").reindex(keys)
    val = {}
    for name in CHECK:
        for p in ("t", "e"):
            a, b = res[f"{p}_{name}"].to_numpy(float), O3[f"{p}_{name}"].to_numpy(float)
            val[f"{p}_{name}"] = bool(np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a[~np.isnan(a)], b[~np.isnan(b)]))
    res = res[[c for c in res.columns if not any(c.endswith(k) for k in CHECK)]]
    res.index.name = "patient_key"
    res.reset_index().to_parquet(OUT / f"restricted_nco_{n}.parquet")
    sup = lambda k: int(k) if (k == 0 or k >= 11) else "<11"
    summ = dict(trial=n, n=int(len(res)), follow_days=follow_days, validation_identical_to_v13=val,
                nco_events_any_followup={k: sup(np.nansum(res[f"e_{k}"])) for k in NEW_NCO})
    json.dump(summ, open(OUT / f"summary_{n}.json", "w"), indent=2)
    print(json.dumps(dict(trial=n, validation=val)), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trials", default=",".join(TRIALS))
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--out", default=None, help="v1.7: output dir (default claude-v16-s5-nco/extract)")
    a = ap.parse_args()
    global OUT
    if a.out:
        OUT = Path(a.out)
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    for n in a.trials.split(","):
        one(n, a.threads)


if __name__ == "__main__":
    main()
