#!/usr/bin/env python
"""Phase-2 effect estimation (protocol v1 8; run once after freeze + amendment v1.1).

For one trial: for each PS arm and imputation, the matched cohort saved by the balance grid
(restricted_matches_imp*_seed0.parquet; split seed 0 defines the hdPS pool) is combined with the
extracted outcomes. Cox proportional-hazards model, treatment only, robust SE clustered on the
matched pair; Rubin's rules across the 5 imputations. Secondary: overlap-weighted Cox on the full
population (weights 1-p for treated, p for comparator; robust SE). Horizons: trial horizon (primary),
12 and 60 months (sensitivity). Outcomes: primary composite, CV-death variant, negative controls.
Aggregate output only; event counts 1-10 suppressed.
"""
import argparse
import glob
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import HORIZON_MONTHS, NCO  # noqa: E402

warnings.filterwarnings("ignore")


def cox(df, weights=None, cluster=None):
    d = df[["t", "e", "treated"]].copy()
    kw = dict(duration_col="t", event_col="e", robust=True)
    if weights is not None:
        d["w"] = weights
        kw["weights_col"] = "w"
    if cluster is not None:
        d["cl"] = cluster
        kw["cluster_col"] = "cl"
    if d.e.sum() < 5 or d[d.treated == 1].e.sum() == 0 or d[d.treated == 0].e.sum() == 0:
        return np.nan, np.nan
    m = CoxPHFitter().fit(d, **kw)
    return float(m.params_["treated"]), float(m.standard_errors_["treated"])


def rubin(b, se):
    b, se = np.array(b, float), np.array(se, float)
    ok = ~np.isnan(b) & ~np.isnan(se)
    b, se = b[ok], se[ok]
    if len(b) == 0:
        return np.nan, np.nan, 0
    m = len(b)
    qbar = b.mean()
    var = (se ** 2).mean() + (1 + 1 / m) * (b.var(ddof=1) if m > 1 else 0.0)
    return qbar, np.sqrt(var), m


def sup(n):
    n = int(n)
    return n if n == 0 or n >= 11 else "<11"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", required=True)
    ap.add_argument("--grid-dir", required=True)
    ap.add_argument("--outcomes", required=True)
    ap.add_argument("--horizon-days", type=int, required=True)
    ap.add_argument("--output-csv", required=True)
    a = ap.parse_args()
    O = pd.read_parquet(a.outcomes).set_index("patient_key")
    assert a.horizon_days == int(round(HORIZON_MONTHS[a.trial] * 30.4375)), "horizon mismatch with trial_specs"
    n_excl = int(O.get("exclude_phase2", pd.Series(0, index=O.index)).sum())
    if "exclude_phase2" in O:
        O = O[O.exclude_phase2 == 0]
    files = sorted(glob.glob(f"{a.grid_dir}/restricted_matches_imp*_seed0.parquet"))
    if not files:
        raise SystemExit("no saved matches")
    outs = [("primary", "t_primary", "e_primary")]
    if "t_primary_cvnoncause" in O:
        outs.append(("primary_cv_noncause_as_nonCV", "t_primary_cvnoncause", "e_primary_cvnoncause"))
    outs += [(k, f"t_{k}", f"e_{k}") for k in NCO]
    horizons = [("trial", a.horizon_days), ("12m", int(round(12 * 30.4375))), ("60m", int(round(60 * 30.4375)))]
    acc = {}
    for f in files:
        M = pd.read_parquet(f)
        for meth, g in M.groupby("method", sort=False):
            g = g.set_index("patient_key")
            missing = ~g.index.isin(O.index)
            # only patients flagged exclude_phase2 may be missing; anything else is a linkage error
            assert missing.sum() <= n_excl, f"{meth}: {missing.sum()} patients without outcomes"
            g = g.join(O, how="inner")
            for oname, tc, ec in outs:
                for hname, H in horizons:
                    if hname != "trial" and oname != "primary":
                        continue
                    d = g[[tc, ec, "treated", "pair", "ps_logit"]].dropna(subset=[tc, ec])
                    d = d.assign(t=np.minimum(d[tc], H), e=((d[ec] == 1) & (d[tc] <= H)).astype(int))
                    for analysis in ("matched", "overlap_weighted"):
                        if analysis == "matched":
                            dm = d if meth == "unmatched" else d[d.pair >= 0]
                            b, se = cox(dm, cluster=None if meth == "unmatched" else dm.pair.to_numpy())
                            n1, n0 = (dm.treated == 1).sum(), (dm.treated == 0).sum()
                            e1, e0 = dm[dm.treated == 1].e.sum(), dm[dm.treated == 0].e.sum()
                        else:
                            if meth == "unmatched" or d.ps_logit.isna().all():
                                continue
                            p = 1 / (1 + np.exp(-d.ps_logit.to_numpy()))
                            w = np.where(d.treated == 1, 1 - p, p)
                            b, se = cox(d, weights=w)
                            n1, n0 = (d.treated == 1).sum(), (d.treated == 0).sum()
                            e1, e0 = d[d.treated == 1].e.sum(), d[d.treated == 0].e.sum()
                        k = (meth, oname, hname, analysis)
                        acc.setdefault(k, dict(b=[], se=[], n1=[], n0=[], e1=[], e0=[]))
                        for kk, v in zip(("b", "se", "n1", "n0", "e1", "e0"), (b, se, n1, n0, e1, e0)):
                            acc[k][kk].append(v)
    rows = []
    for (meth, oname, hname, analysis), v in acc.items():
        b, se, m = rubin(v["b"], v["se"])
        rows.append(dict(trial=a.trial, method=meth, outcome=oname, horizon=hname, analysis=analysis, imputations=m,
                         loghr=b, se=se, hr=np.exp(b), lo=np.exp(b - 1.96 * se), hi=np.exp(b + 1.96 * se),
                         n_treated=round(np.mean(v["n1"])), n_control=round(np.mean(v["n0"])),
                         events_treated=sup(round(np.mean(v["e1"]))) if min(v["e1"]) >= 11 or max(v["e1"]) == 0 else "<11",
                         events_control=sup(round(np.mean(v["e0"]))) if min(v["e0"]) >= 11 or max(v["e0"]) == 0 else "<11"))
    pd.DataFrame(rows).to_csv(a.output_csv, index=False)
    print(json.dumps(dict(trial=a.trial, rows=len(rows))))


if __name__ == "__main__":
    main()
