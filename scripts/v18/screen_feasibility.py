#!/usr/bin/env python
"""v1.8 count-only feasibility screen for one AF candidate (docs/v18/af_candidates.md; rules of docs/v17/candidates.md).

Same counts as scripts/v17/screen_feasibility.py (whose pooled_events is reused unchanged: the roster passed to it has no
arm column and only pooled sums are kept): n per arm, n per arm with a selected ECG in [index-365, index], pooled primary
events and pooled deaths within the horizon. Near-duplicate check (v1.8: against EVERY existing cohort directory
audits/claude-*-cohort-v*/, not only the v1.6 18): share of this cohort's (patient, index date) records identical to one
existing cohort; max and top 3 reported. Aggregates only; counts 1-10 suppressed. No PS, balance, SMD or HR.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v17"))
sys.path.insert(0, str(HERE.parent))
from screen_feasibility import pooled_events, sup  # noqa: E402
from trial_specs import HORIZON_MONTHS, OUTCOMES  # noqa: E402

A = "/mnt/raid0/rbc58/ecg-tte/audits"


def record_share(coh: pd.DataFrame, exclude=()):
    """{cohort dir: share of coh's (patient_key, index_date) records present in it} for all existing cohort dirs."""
    rec = set(zip(coh.patient_key, pd.to_datetime(coh.index_date).dt.date))
    out = {}
    for f in sorted(glob.glob(f"{A}/claude-*-cohort-v*/restricted_cohort.parquet")):
        d = Path(f).parent.name
        if d in exclude:
            continue
        o = pd.read_parquet(f, columns=["patient_key", "index_date"])
        s = set(zip(o.patient_key, pd.to_datetime(o.index_date).dt.date))
        out[d] = len(rec & s) / len(rec) if rec else 0.0
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--cohort-dir", required=True)
    ap.add_argument("--selection-dir", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--threads", type=int, default=12)
    a = ap.parse_args()
    os.umask(0o077)
    coh = pd.read_parquet(f"{a.cohort_dir}/restricted_cohort.parquet")
    sel = pd.read_parquet(f"{a.selection_dir}/restricted_selection.parquet", columns=["patient_key"])
    coh["ecg"] = coh.patient_key.isin(set(sel.patient_key))
    arms = coh.groupby("treatment_arm", sort=False).agg(n=("ecg", "size"), n_ecg=("ecg", "sum"))
    ev, dh = pooled_events(coh[["patient_key", "person_id", "index_date"]].copy(), a.trial, a.threads)
    ecgk = coh.set_index("patient_key").ecg.reindex(ev.index).to_numpy()
    share = record_share(coh)
    top = sorted(share.items(), key=lambda x: -x[1])[:3]
    mn = int(arms.n_ecg.min()) if len(arms) == 2 else 0
    res = dict(trial=a.trial, n=sup(len(coh)),
               arms={str(k): dict(n=sup(v.n), n_with_ecg=sup(v.n_ecg), frac_ecg=round(v.n_ecg / v.n, 3) if v.n else None) for k, v in arms.iterrows()},
               n_arms_nonempty=int(len(arms)), min_arm_with_ecg=mn if (mn == 0 or mn >= 11) else "<11",
               horizon_months=HORIZON_MONTHS[a.trial], outcome=[str(c) for c in OUTCOMES[a.trial]],
               pooled_primary_events_horizon=sup(ev.sum()), pooled_primary_events_horizon_with_ecg=sup(ev[ecgk].sum()),
               pooled_deaths_horizon=sup(dh.sum()),
               max_same_record_share=dict(cohort=top[0][0], share=round(top[0][1], 3)) if top else None,
               same_record_share_top3={k: round(v, 3) for k, v in top},
               index_years=[int(pd.to_datetime(coh.index_date).dt.year.min()), int(pd.to_datetime(coh.index_date).dt.year.max())] if len(coh) else None)
    Path(a.out_json).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(a.out_json, "w"), indent=1, default=str)
    print(json.dumps(res, default=str))


if __name__ == "__main__":
    main()
