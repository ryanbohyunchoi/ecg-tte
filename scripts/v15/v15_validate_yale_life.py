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
  python v15_validate_yale_life.py exact   [--out DIR]   (audit M6: Yale's exact design and population)
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


def exact(out: Path):
    """Exact-design validation (audit M6): fixture with Yale's own design inputs for the LIFE phase-2 population
    (v13_common.Trial('life'): same 3,131 patients, imputation-1 completed covariates, X_dx = demo + Trial.dxc, pool-A
    hdPS candidates in Yale's order, ECG PCs on the same patients). Matching uses all 3,131 and the 5 exclude_phase2 /
    missing-outcome patients are dropped after matching, exactly as v13_bootstrap does. The engine's own
    TrialData / designs / fit_matches / cox are then compared with bs_life.csv rep 0."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from v13_common import Trial, outcomes  # noqa: E402
    import v15_analyze as V  # noqa: E402
    os.umask(0o077)
    F = out / "fixture-yale-exact"
    F.mkdir(exist_ok=True)
    T = Trial("life")
    keys = pd.Index(T.keys).astype(str)
    co = pd.read_parquet(A / "claude-life-cohort-v2/restricted_cohort.parquet").set_index("patient_key").reindex(T.keys)
    idx = pd.to_datetime(co.index_date)
    pd.DataFrame({"pid": keys, "treated": T.t, "index_day": (idx - pd.Timestamp("2000-01-01")).dt.days.to_numpy(float),
                  "index_year": idx.dt.year.to_numpy()}).to_parquet(F / "cohort.parquet", index=False)
    cov = T.cov.copy()
    cov.index = keys
    cov.reset_index(names="pid").to_parquet(F / "baseline.parquet", index=False)
    json.dump(dict(demo=T.demo, dx=T.dxc, meds=T.meds, labs_vitals=T.phys, util=T.util, phys=T.phys), open(F / "roles.json", "w"), indent=2)
    pa = pd.read_parquet(A / "claude-life-panel-v2/restricted_panel.parquet").set_index("patient_key").reindex(T.keys)
    feats = list(dict.fromkeys(c.rsplit("__", 1)[0] for c in T.lv.columns))  # pool-A candidates, Yale order
    P = pa[feats].rename(columns=lambda c: c.replace("labn_", "lab_"))
    P.index = keys
    P.reset_index(names="pid").to_parquet(F / "panel.parquet", index=False)
    pd.DataFrame({"feature": P.columns, "domain": [c.split("_")[0] for c in P.columns]}).to_csv(F / "panel_dictionary.csv", index=False)
    E = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(A / "claude-life-bcl/restricted_embeddings_part-*.parquet")))])
    E = E.drop_duplicates("patient_key").set_index("patient_key").reindex(T.keys)
    pd.DataFrame({"pid": keys, "embedding": E.embedding.to_numpy(), "lag_days": np.nan}).to_parquet(F / "ecg_embedding.parquet", index=False)
    t, e, ok, H, _ = outcomes("life", "life", T.keys)
    # every patient needs an outcome row to enter the engine's population; excluded rows are dropped after matching below
    pd.DataFrame({"pid": keys, "t": np.where(ok, t, 1.0), "e": np.where(ok, e, 0)}).to_parquet(F / "outcomes.parquet", index=False)
    for f in ("rct.json",):
        (F / f).write_text((out / f).read_text())
    D = V.TrialData(F)
    assert list(D.pids) == sorted(keys), "population differs"
    order = np.argsort(keys.to_numpy())  # engine sorts pids as strings; Yale order = sorted patient_key too
    assert (keys.to_numpy()[order] == D.pids.to_numpy()).all()
    Yx = T.arms(["sparse", "sparse+ECG", "hdPS200", "clinical (reference)"])
    Dx = D.designs(["sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical"])
    okD = ok[order]
    Y = pd.read_csv(A / "claude-v13-bootstrap/bs_life.csv")
    Y = Y[Y.rep == 0].set_index("arm")
    ymap = {"unmatched": "unmatched", "sparse": "sparse", "sparse+ECG": "sparse+ECG", "hdPS200": "hdPS200",
            "hdPS200+ECG": "hdPS200+ECG", "clinical": "clinical (reference)"}
    rows = []
    M = V.fit_matches({a: (None if a == "unmatched" else Dx[a]) for a in ymap}, D.t)
    for a, ya in ymap.items():
        idx_, cl, _ = M[a]
        if idx_ is None:
            i = np.where(okD)[0]
            b, se = V.cox(D.T[i], D.E[i], D.t[i])
            pairs = np.nan
        else:
            m = okD[idx_]
            b, se = V.cox(D.T[idx_][m], D.E[idx_][m], D.t[idx_][m], cluster=cl[m])
            pairs = len(idx_) // 2
        ddiff = np.nan
        if ya in Yx:
            Xy = Yx[ya][order]
            if a == "clinical":  # same columns, engine groups them demo/dx/meds/labs/util: compare as sets of columns
                cols = [c for g in V.GROUPS for c in D.groups[g]]
                Xy = pd.DataFrame(Xy, columns=T.core)[cols].to_numpy()
            ddiff = float(np.abs(Xy - Dx[a]).max()) if Xy.shape == Dx[a].shape else np.inf
        rows.append(dict(arm=a, design_max_abs_diff=ddiff, v15_loghr=b, v15_se=se, v15_pairs=pairs, yale_loghr=Y.loc[ya, "loghr"],
                         yale_se=Y.loc[ya, "se"], yale_pairs=Y.loc[ya, "pairs"], diff=b - Y.loc[ya, "loghr"]))
    R = pd.DataFrame(rows)
    (out / "analysis").mkdir(exist_ok=True)
    R.to_csv(out / "analysis/compare_yale_exact.csv", index=False)
    pd.set_option("display.width", 200)
    print(R.to_string(index=False, float_format=lambda v: f"{v:.6g}"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "compare", "exact"])
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--yale-imputation1", action="store_true", help="build: baseline = Yale completed_01 (no missing) instead of observed")
    a = ap.parse_args()
    if a.cmd == "exact":
        exact(Path(a.out))
    else:
        build(Path(a.out), a.yale_imputation1) if a.cmd == "build" else compare(Path(a.out))
