#!/usr/bin/env python
"""Build the interactive results page (docs/presentation/ecg_tte_results.html) from aggregate outputs only
(phase-1 capture summaries, phase-2 estimates, v1.3 / v1.4 summary tables). Self-contained: data are
embedded as JSON, charts are drawn with vanilla JavaScript/SVG; no external resources.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import HORIZON_MONTHS, PUBLISHED, RATING_ITEMS, TRIALS, rating  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
V13, V14 = ROOT / "docs" / "v13", ROOT / "docs" / "v14"
OUT = ROOT / "docs" / "presentation" / "ecg_tte_results.html"
ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "R+"]
LAB = {"unmatched": "M0 unadjusted", "sparse": "M1 sparse", "sparse+ECG": "M2 sparse + ECG", "hdPS200": "M3 hdPS200",
       "hdPS200+ECG": "M4 hdPS200 + ECG", "clinical (reference)": "R clinical PS", "R+": "R+ physiology reference"}
DOMAINS = [("phys_obs", "Core-9 physiology (measured)"), ("LVSTRUCT", "Echo: LV structure"), ("LVFUNC", "Echo: LV function"),
           ("DIAST", "Echo: diastolic / LA"), ("RVPULM", "Echo: RV / pulmonary"), ("VALVE", "Echo: valves"),
           ("AORTA", "Echo: aortic root"), ("BNP", "NT-proBNP"), ("LAB", "Other labs"), ("meds", "Medications"),
           ("util", "Healthcare use"), ("poolB", "Rest of coded record"), ("prog_full", "Prognostic score")]
V14_NOTES = [
    "<b>Thin coded record → the ECG helps, and it shows up against the RCTs (hypothesis B supported).</b> When 50–90% of each patient's recorded codes are deleted at random (same patients, same ECGs), the plasmode bias reduction from adding the ECG to sparse grows from +0.004 (codes intact) to +0.013, +0.016 and +0.022 log HR, and on the <i>real</i> data sparse+ECG moves significantly closer to both the RCTs (e.g. 75% dropout: −0.056, 95% CI −0.079 to −0.016) and the physiology reference R+ (−0.018, −0.034 to −0.005). On top of hdPS the gain is smaller (plasmode +0.005 to +0.010; real-data CIs include 0).",
    "<b>Naturally data-poor patients (hypothesis A) did not show it.</b> The lowest code-density tertile had no larger ECG gain for sparse; for hdPS the plasmode gain was larger in the low tertile (+0.010, CI 0.0005–0.019) but not in the real-data bootstrap. Patients with few codes also tend to be less confounded, so natural thinness is not the same as losing information.",
    "<b>No echo vs echo (hypothesis C): no difference.</b> The sparse+ECG gain is similar whether or not the patient had an echo (+0.011 vs +0.009).",
    "<b>Echo physiology as the hidden confounder (hypothesis D): little confounding to remove.</b> When only demographics, diagnoses and measured echo physiology drive the outcome, sparse is already about as unbiased as the clinical PS (|bias| 0.033 vs 0.036), so there is nothing for the ECG to fix. Conditional on coded diagnoses, the cardiac structure the ECG captures is a weak confounder in these cohorts — which explains why large balance gains (phase 1) translate into small bias reductions.",
    "<b>HF-hospitalisation outcome (hypothesis E): small.</b> Plasmode gains of +0.001 to +0.005; real-data bootstrap vs R+ not significant.",
]
FAILED = {"castle_af": "ablation arm 149 at cohort", "engage_af": "edoxaban arm 70 at cohort", "dcp": "smaller arm with ECG 255",
          "invest": "smaller arm with ECG 224", "paradise_mi": "smaller arm with ECG 296",
          "dionysos": "not emulable (outcome); balance only", "paradigm_hf": "new-user design; sensitivity only (sequential design used)"}


def csv(p):
    return pd.read_csv(p, keep_default_na=False, na_values=[""]) if Path(p).exists() else None


def recs(df):
    if df is None:
        return []
    return json.loads(df.replace({np.inf: None, -np.inf: None}).to_json(orient="records"))


def main():
    names = {**PRIMARY, **EXTRA}
    done = [n for n in names if (A / f"claude-phase2-all-{n}.csv").exists()]
    trials, capture, phase2 = [], {}, {}
    for n in done:
        k = names[n][0]
        sp = pd.read_csv(A / f"claude-cap4-all-{n}" / "summary_pooled.csv", index_col=0)
        pairs = int(sp.loc["clinical (reference)", "pairs"])
        b, se = bench(k)
        p = PUBLISHED[k]
        tot, lab, _ = rating(k, pairs)
        trials.append(dict(id=n, key=k, name=TRIALS[k]["name"].replace(" (adapted)", ""), role=TRIALS[k].get("role", "control"),
                           set="primary" if n in PRIMARY else "extension", rct_hr=round(float(np.exp(b)), 3),
                           rct_lo=round(float(np.exp(b - 1.96 * se)), 3), rct_hi=round(float(np.exp(b + 1.96 * se)), 3),
                           rct_arms=p.get("rct_arms"), endpoint=p.get("endpoint"), source=p.get("source"),
                           horizon=HORIZON_MONTHS[k], pairs=pairs, rating=lab, rating_score=int(tot),
                           arms=" vs ".join(a for a, _ in TRIALS[k]["arms"]), note=TRIALS[k].get("note", "")))
        cap = {}
        for arm in ["sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]:
            cap[arm] = {}
            for d, _ in DOMAINS:
                c = f"excess_{d}"
                if c in sp and arm in sp.index and not pd.isna(sp.loc["unmatched", c]) and sp.loc["unmatched", c] >= 0.02:
                    cap[arm][d] = round(float(100 * (1 - sp.loc[arm, c] / sp.loc["unmatched", c])), 1)
        capture[n] = cap
        d = pd.read_csv(A / f"claude-phase2-all-{n}.csv")
        ph = {}
        for (meth, out, hor, an), g in d.groupby(["method", "outcome", "horizon", "analysis"]):
            if meth not in ARMS or not (out in ("primary",) and an in ("matched", "overlap_weighted")):
                continue
            r = g.iloc[0]
            ph.setdefault(f"{hor}|{an}", {})[meth] = dict(hr=r.hr, lo=r.lo, hi=r.hi, loghr=r.loghr, se=r.se,
                                                          n1=int(r.n_treated), n0=int(r.n_control))
        phase2[n] = ph
    # R+ point estimate from the v1.3 design run (primary analysis, Rubin)
    dall = csv(V13 / "design_all_combined.csv")
    if dall is not None:
        for r in dall[(dall.analysis == "primary") & (dall.arm == "R+")].itertuples():
            if r.trial in phase2:
                phase2[r.trial].setdefault("trial|matched", {})["R+"] = dict(hr=float(np.exp(r.loghr)), lo=float(np.exp(r.loghr - 1.96 * r.se)),
                                                                            hi=float(np.exp(r.loghr + 1.96 * r.se)), loghr=r.loghr, se=r.se)
    failed = [dict(key=k, name=TRIALS[k]["name"].replace(" (adapted)", "") if k in TRIALS else k, reason=v) for k, v in FAILED.items()]
    # v1.3 multiverse per specification diffs
    mv = csv(V13 / "multiverse_specs_combined.csv")
    mvd = []
    if mv is not None:
        for cn, a2, a1 in (("C1", "sparse+ECG", "sparse"), ("C2", "hdPS200+ECG", "hdPS200")):
            x = mv[mv.arm == a2].merge(mv[mv.arm == a1], on=["model", "seed", "estimator"], suffixes=("_2", "_1"))
            for r in x.itertuples():
                mvd.append(dict(contrast=cn, model=r.model, seed=int(r.seed), estimator=r.estimator,
                                d_abs_rct=r.err_rct_2 - r.err_rct_1, d_sq_rct=r.sq_rct_2 - r.sq_rct_1,
                                d_abs_rplus=r.err_rplus_2 - r.err_rplus_1, d_sq_rplus=r.sq_rplus_2 - r.sq_rplus_1))
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    DATA = dict(
        meta=dict(generated=datetime.now().strftime("%Y-%m-%d %H:%M"), commit=commit),
        labels=LAB, domains=DOMAINS, trials=trials, failed=failed, capture=capture, phase2=phase2,
        v13=dict(
            plasmode_rs=recs(csv(V13 / "plasmode_rs_contrasts_combined.csv")),
            plasmode_fixed=recs(csv(V13 / "plasmode_fixed_contrasts_combined.csv")),
            plasmode_rs_trial=recs(csv(V13 / "plasmode_rs_by_trial_combined.csv")),
            boot_cross=recs(csv(V13 / "bootstrap_cross_combined.csv")),
            boot_trial=recs(csv(V13 / "bootstrap_by_trial_combined.csv")),
            boot_shd=recs(csv(V13 / "bootstrap_shd_enc2_cross_combined.csv")),
            multiverse=mvd, design=recs(csv(V13 / "design_agreement_combined.csv")),
            calibrated=recs(csv(V13 / "calibrated_agreement_combined.csv")),
            nco=recs(csv(V13 / "nco_systematic_error_combined.csv")),
            rules=recs(csv(V13 / "decision_rules_combined.csv").rename(columns={"Unnamed: 0": "rule", "0": "met"})
                       if csv(V13 / "decision_rules_combined.csv") is not None else None)),
        v14=dict(notes=V14_NOTES, plasmode=recs(csv(V14 / "plasmode_contrasts.csv")), boot=recs(csv(V14 / "bootstrap_contrasts.csv")),
                 hypotheses=recs(csv(V14 / "hypotheses.csv")), strata=recs(csv(V14 / "strata.csv"))),
    )
    html = TEMPLATE.replace("/*DATA*/", "const DATA = " + json.dumps(DATA, default=float).replace("</", "<\\/") + ";")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB; {len(trials)} trials)")


TEMPLATE = (Path(__file__).resolve().parent / "presentation_template.html").read_text()

if __name__ == "__main__":
    main()
