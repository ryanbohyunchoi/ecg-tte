#!/usr/bin/env python
"""v1.5 amendment (2026-09-26, death outcome): build claude-v15d-mimic-<trial>-death dirs from the corrected
(post-AUDITFIX) MIMIC trial dirs without touching them. Primary t/e = all-cause death within 365 d of t0
(patients.dod; index-day deaths t = 0.5; censoring min(365, last contact + 365) as before). NCO columns copied
unchanged. rct.json benchmark fields set to null with benchmark_pending = true. Aggregates only.
"""
import datetime as dt
import json
import os
import shutil

import numpy as np
import pandas as pd

from v15_mimic_common import AUDIT, TRIAL_KEYS, connect, out_dir, supp

os.umask(0o077)
con = connect(16)
COPY = ["cohort.parquet", "baseline.parquet", "roles.json", "panel.parquet", "panel_dictionary.csv",
        "ecg_embedding.parquet", "index_time.parquet"]
for K in TRIAL_KEYS:
    SRC = out_dir(K)
    for m in ("AUDITFIX_DONE", "READY_COHORT", "READY_ECG", "READY_OUTCOMES"):
        assert (SRC / m).exists(), (K, m)
    DST = __import__("pathlib").Path(f"{AUDIT}/claude-v15d-mimic-{K}-death")
    DST.mkdir(mode=0o700, exist_ok=False)
    for f in COPY:
        shutil.copy2(SRC / f, DST / f)
    src_o = pd.read_parquet(SRC / "outcomes.parquet")
    coh = pd.read_parquet(SRC / "cohort.parquet")
    it = pd.read_parquet(SRC / "index_time.parquet")
    assert (src_o.pid.values == coh.pid.values).all()
    con.register("it_df", it)
    base = con.execute("""SELECT it.pid, date_diff('day', CAST(it.index_datetime AS DATE), p.dod) death_day,
          date_diff('day', CAST(it.index_datetime AS DATE), CAST(greatest(
              (SELECT max(dischtime) FROM admissions ad WHERE ad.subject_id = it.subject_id),
              (SELECT max(outtime) FROM transfers t WHERE t.subject_id = it.subject_id AND t.eventtype = 'ED')) AS DATE)) + 365 cens_day
          FROM it_df it JOIN patients p USING (subject_id)""").df().set_index("pid").reindex(coh.pid)
    H = 365.0
    cens = np.minimum(H, base.cens_day.astype(float)).values
    death = base.death_day.astype(float).values
    assert np.all(np.nan_to_num(death, nan=1e9) >= 0)
    e = (death <= cens).astype(int)
    t = np.where(e == 1, death, cens)
    t = np.where(t <= 0, 0.5, t).astype(float)
    out = pd.DataFrame({"pid": coh.pid.values, "t": t, "e": e})
    nco = [c for c in src_o.columns if c.startswith(("t_nco_", "e_nco_"))]
    out = pd.concat([out, src_o[nco].reset_index(drop=True)], axis=1)
    pd.testing.assert_frame_equal(out[nco], src_o[nco])
    assert (out.t > 0).all() and (out.t <= H).all()
    if K in ("transform_hf", "comet"):  # primary already all-cause death at 365 d
        assert np.allclose(out.t, src_o.t) and (out.e.values == src_o.e.values).all()
    out.to_parquet(DST / "outcomes.parquet", index=False)
    rct = json.load(open(SRC / "rct.json"))
    rct_src = dict(rct)
    rct.update(endpoint="all-cause death", hr=None, lo=None, hi=None, our_orientation=None, our_lo=None, our_hi=None,
               benchmark_pending=True, horizon_days=365,
               notes=f"death-outcome dir (v1.5 amendment 2026-09-26); benchmark to be filled with the verified RCT all-cause "
                     f"mortality HR. Source primary endpoint: {rct_src['endpoint']}")
    json.dump(rct, open(DST / "rct.json", "w"), indent=2)
    arms = rct["arms"]
    tr = coh.treated.values
    by = {name: dict(n=supp((tr == v).sum()), deaths=supp(e[tr == v].sum()),
                     person_years=round(float(t[tr == v].sum() / 365.25), 1))
          for v, name in ((1, arms[0]), (0, arms[1]))}
    ss = json.load(open(SRC / "summary.json"))
    summ = dict(cohort="mimic", trial=K, variant="death", source_dir=str(SRC), created=dt.datetime.now().isoformat(timespec="seconds"),
                arms=arms, n=supp(len(coh)), by_arm_death=by, horizon_days=365,
                source_attrition=ss.get("attrition"), source_by_arm={a: {k: v[k] for k in ("n", "with_ecg_365d")} for a, v in ss["by_arm"].items()},
                notes=["primary = all-cause death within 365 d of t0 (patients.dod); index-day deaths t = 0.5; "
                       "censoring min(365, 365 d after last hospital contact)",
                       "cohort/baseline/panel/ECG copied from the post-AUDITFIX source dir; NCO columns identical to source",
                       "rct.json benchmark pending (coordinator)"])
    json.dump(summ, open(DST / "summary.json", "w"), indent=2, default=str)
    for m in ("READY_COHORT", "READY_ECG", "READY_OUTCOMES"):
        (DST / m).write_text(dt.datetime.now().isoformat() + "\n")
    print(K, json.dumps(by), flush=True)
