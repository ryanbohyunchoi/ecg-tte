#!/usr/bin/env python
"""Validation fixture for v15_analyze.py: convert the Yale LIFE trial into the v1.5 interface
(docs/V15_INTERFACE.md) in a private scratch dir, so the engine can be checked end-to-end against the
Yale phase-2 estimates (imputation 1; claude-v13-bootstrap/bs_life.csv rep 0).

Conversions: roles from Yale roles.json (demo; dx = core minus demo/physiology/meds/util; meds = *_order;
labs_vitals = phys = heldout_physiology; util); panel keeps dx_/rx_/px_ counts, maps Yale labn_<id>
('measured' flag) to lab_<id>, drops lab values, visit counts and exposure features; outcomes =
t_primary / e_primary truncated at the LIFE horizon (58 months = 1765 d), exclude_phase2 rows dropped;
rct.json from trial_specs.PUBLISHED['life']. Restricted files stay in the scratch dir (umask 077).

  python v15_validate_yale_life.py build   [--out DIR] [--yale-imputation1]
  python v15_validate_yale_life.py compare [--out DIR]
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from trial_specs import HORIZON_MONTHS, PUBLISHED  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = A / "claude-v15-validate-life"


def build(out: Path, completed=False):
    os.umask(0o077)
    out.mkdir(exist_ok=True)
    B = A / "claude-life-baseline-v11"
    roles = json.load(open(B / "roles.json"))
    obs = pd.read_parquet(B / ("restricted_completed_01.parquet" if completed else "restricted_baseline_observed.parquet")).rename(columns={"patient_key": "pid"})
    co = pd.read_parquet(A / "claude-life-cohort-v2/restricted_cohort.parquet").rename(columns={"patient_key": "pid"})
    idx = pd.to_datetime(co.index_date)
    cohort = pd.DataFrame({"pid": co.pid.astype(str), "treated": co.treated.astype(int),
                           "index_day": (idx - pd.Timestamp("2000-01-01")).dt.days.astype(float), "index_year": idx.dt.year})
    cohort.to_parquet(out / "cohort.parquet", index=False)
    core = roles["core"]
    phys = roles["heldout_physiology"]
    meds = [c for c in core if c.endswith("_order")]
    util = [c for c in core if c in ("outpatient_visits", "ed_encounters", "hospital_admissions")]
    dx = [c for c in core if c not in set(roles["demo"]) | set(phys) | set(meds) | set(util) and c != "pci_index_30d"]
    base = obs[["pid"] + core].copy()
    base["pid"] = base.pid.astype(str)
    base.to_parquet(out / "baseline.parquet", index=False)
    json.dump(dict(demo=roles["demo"], dx=dx, meds=meds, labs_vitals=phys, util=util, phys=phys), open(out / "roles.json", "w"), indent=2)
    pa = pd.read_parquet(A / "claude-life-panel-v2/restricted_panel.parquet")
    expo = set(roles["exposure_features"])
    keep = {c: c for c in pa.columns if c.split("_")[0] in ("dx", "rx", "px") and c not in expo}
    keep.update({c: c.replace("labn_", "lab_") for c in pa.columns if c.startswith("labn_")})
    P = pa[list(keep)].rename(columns=keep)
    P.insert(0, "pid", pa.patient_key.astype(str))
    P.to_parquet(out / "panel.parquet", index=False)
    pd.DataFrame({"feature": P.columns[1:], "domain": [c.split("_")[0] for c in P.columns[1:]]}).to_csv(out / "panel_dictionary.csv", index=False)
    E = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(A / "claude-life-bcl/restricted_embeddings_part-*.parquet")))])
    pd.DataFrame({"pid": E.patient_key.astype(str), "embedding": E.embedding, "lag_days": np.nan}).to_parquet(out / "ecg_embedding.parquet", index=False)
    O = pd.read_parquet(A / "claude-life-outcomes-v1/restricted_outcomes.parquet")
    H = int(round(HORIZON_MONTHS["life"] * 30.4375))
    O = O[O.t_primary.notna() & (O.exclude_phase2 == 0)]
    oc = pd.DataFrame({"pid": O.patient_key.astype(str), "t": np.minimum(O.t_primary, H).clip(lower=0.5),
                       "e": ((O.e_primary == 1) & (O.t_primary <= H)).astype(int)})
    oc.to_parquet(out / "outcomes.parquet", index=False)
    p = PUBLISHED["life"]
    json.dump(dict(trial="LIFE", key="life", arms=["losartan (ARB)", "atenolol (beta-blocker)"], hr=p["hr"], lo=p["ci"][0], hi=p["ci"][1],
                   ci_level=p.get("ci_level", 0.95), our_orientation=p["our_orientation"], horizon_days=H, endpoint=p["endpoint"],
                   notes="validation fixture from Yale files"), open(out / "rct.json", "w"), indent=2)
    for m in ("READY_COHORT", "READY_ECG", "READY_OUTCOMES"):
        (out / m).write_text("fixture\n")
    print(f"built {out}: n cohort={len(cohort)}, panel features={P.shape[1] - 1}, outcomes={len(oc)}")


def compare(out: Path):
    est = pd.read_csv(out / "analysis/estimates.csv")
    est = est[est.outcome == "primary"].set_index("arm")
    Y = pd.read_csv(A / "claude-v13-bootstrap/bs_life.csv")
    Y = Y[Y.rep == 0].set_index("arm")
    ymap = {"unmatched": "unmatched", "sparse": "sparse", "sparse+ECG": "sparse+ECG", "hdPS200": "hdPS200",
            "hdPS200+ECG": "hdPS200+ECG", "clinical": "clinical (reference)"}
    rows = []
    for a, ya in ymap.items():
        rows.append(dict(arm=a, v15_loghr=est.loc[a, "loghr"], v15_se=est.loc[a, "se"], v15_pairs=est.loc[a, "pairs"],
                         yale_loghr=Y.loc[ya, "loghr"], yale_se=Y.loc[ya, "se"], yale_pairs=Y.loc[ya, "pairs"],
                         diff=est.loc[a, "loghr"] - Y.loc[ya, "loghr"],
                         diff_in_se=(est.loc[a, "loghr"] - Y.loc[ya, "loghr"]) / Y.loc[ya, "se"]))
    R = pd.DataFrame(rows)
    R.to_csv(out / "analysis/compare_yale.csv", index=False)
    print(R.round(3).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "compare"])
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--yale-imputation1", action="store_true", help="build: baseline = Yale completed_01 (no missing) instead of observed")
    a = ap.parse_args()
    build(Path(a.out), a.yale_imputation1) if a.cmd == "build" else compare(Path(a.out))
