#!/usr/bin/env python
"""v1 audit (claims recheck): Table 1 of docs/paper/paper2.md vs its sources.

Checks, per trial row of paper2.md Table 1:
  PICOT cells (area, population, intervention, comparator, outcome, time) vs docs/paper/table1_picot.md, both the committed
  version (git HEAD) and the working copy; physiologic label and domains vs docs/v21/TRIAL_LABELS.json (and the raw
  labeller files: kappa); quality tier / points / horizon vs docs/v19/quality_tiers.json; RCT estimate (CI) vs
  trial_specs.PUBLISHED (the bench() source) and vs rb in claude-v21-paper2/core/restricted_cells.parquet (log of the
  analysed orientation); time vs trial_specs.HORIZON_MONTHS; S32 counts by tier and by area.
Trial-level metadata only (no patient data). Output: audits/claude-v1-audit/claims/table1_recheck.csv + printed summary.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/rbc58/github/ecg-tte")
A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = A / "claude-v1-audit" / "claims"
sys.path.insert(0, str(ROOT / "scripts"))
import trial_specs as TS  # noqa: E402  (PUBLISHED / HORIZON_MONTHS: the bench() inputs)

DOM = {"LV_structure": "LV structure", "LV_systolic_function": "LV systolic function", "diastolic_LA": "diastolic/LA",
       "RV_pulmonary_congestion": "RV/pulmonary congestion", "rhythm_conduction": "rhythm/conduction", "none_cardiac": "none"}


def md_rows(text):
    rows = []
    for ln in text.splitlines():
        if ln.startswith("|") and not re.match(r"^\|\s*-", ln) and "Trial" not in ln.split("|")[2]:
            rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p2 = (ROOT / "docs/paper/paper2.md").read_text().splitlines()
    i0 = next(i for i, l in enumerate(p2) if l.startswith("**Table 1."))
    tab = []
    for j in range(i0 + 1, len(p2)):
        if p2[j].startswith("|"):
            tab.append((j + 1, p2[j]))
        elif tab:
            break
    P = {}
    for ln, s in tab:
        c = [x.strip() for x in s.strip().strip("|").split("|")]
        if c[1] == "Trial" or c[0].startswith("-"):
            continue
        P[c[1]] = dict(line=ln, cells=c)
    committed = md_rows(subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:docs/paper/table1_picot.md"], capture_output=True,
                                       text=True, check=True).stdout)
    working = md_rows((ROOT / "docs/paper/table1_picot.md").read_text())
    CM = {r[1]: r for r in committed}
    WK = {r[1]: r for r in working}
    LB = {x["trial"]: x for x in json.loads((ROOT / "docs/v21/TRIAL_LABELS.json").read_text())["labels"]}
    QT = {x["trial"]: x for x in json.loads((ROOT / "docs/v19/quality_tiers.json").read_text())["trials"]}
    R = pd.read_parquet(A / "claude-v21-paper2/core/restricted_cells.parquet", columns=["trial", "key", "rb", "rs"]).drop_duplicates("trial")
    RB = dict(zip(R.key, R.rb))
    RS = dict(zip(R.key, R.rs))
    out, issues = [], []
    for name, d in P.items():
        c = d["cells"]
        area, pop, itv, cmp_, outc, tm, est, qual, phys, doms = c[0], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10]
        r = dict(line=d["line"], trial=name)
        # PICOT vs table1_picot.md
        for lab, M in (("committed", CM), ("working", WK)):
            ref = M.get(name)
            r[f"picot_eq_{lab}"] = ref is not None and [x for x in ref[:9]] == c[:9]
            if not r[f"picot_eq_{lab}"]:
                issues.append((d["line"], name, f"PICOT cells differ from {lab} table1_picot.md", ref, c[:9]))
        # labels
        L = LB[name]
        r["phys_ok"] = phys.lower() == L["physiologic"]
        exp_dom = ", ".join(DOM[x] for x in L["domains"])
        r["dom_ok"] = doms == exp_dom
        if not (r["phys_ok"] and r["dom_ok"]):
            issues.append((d["line"], name, "label mismatch", (L["physiologic"], exp_dom), (phys, doms)))
        r["area_label_json"] = L["area"] == area
        # quality
        q = QT[name]
        tier = q["tier"].split(" - ")[0]
        r["tier_ok"] = qual == f"{tier} ({q['points']})"
        r["area_ok"] = q["area"] == area
        r["time_ok_qt"] = str(q["horizon_months"]) == tm
        r["time_ok_specs"] = str(TS.HORIZON_MONTHS.get(q["key"], "NA")) == tm
        if not (r["tier_ok"] and r["area_ok"] and r["time_ok_qt"]):
            issues.append((d["line"], name, "tier/area/time mismatch", (tier, q["points"], q["area"], q["horizon_months"]), (qual, area, tm)))
        if not r["time_ok_specs"]:
            issues.append((d["line"], name, "time vs trial_specs.HORIZON_MONTHS", TS.HORIZON_MONTHS.get(q["key"]), tm))
        # RCT estimate
        pub = TS.PUBLISHED[q["key"]]
        m = re.match(r"([\d.]+) \(([\d.]+)–([\d.]+)\)", est)
        hr, lo, hi = (float(x) for x in m.groups())
        r["hr_ok"] = abs(hr - pub["hr"]) < 5e-3 and abs(lo - pub["ci"][0]) < 5e-3 and abs(hi - pub["ci"][1]) < 5e-3
        r["ci_level_pub"] = pub.get("ci_level", 0.95)
        r["measure_pub"] = pub.get("measure", "")
        r["orientation_flipped"] = abs(pub["our_orientation"] - pub["hr"]) > 1e-6
        rb = RB.get(q["key"])
        r["exp_rb"] = round(float(np.exp(rb)), 4) if rb is not None else np.nan
        r["rb_matches_printed"] = rb is not None and abs(np.exp(rb) - (pub["our_orientation"])) < 1e-6 and (
            abs(np.exp(rb) - hr) < 5e-3 or r["orientation_flipped"])
        # rs vs CI: (log hi - log lo) / (2 z)
        from scipy.stats import norm
        z = norm.ppf(0.5 + r["ci_level_pub"] / 2)
        r["rs_ok"] = rb is not None and abs(RS[q["key"]] - (np.log(pub["ci"][1]) - np.log(pub["ci"][0])) / (2 * z)) < 1e-9
        lvl = re.search(r"\[([\d.]+)% (CI|credible)", est)
        r["ci_level_printed"] = float(lvl.group(1)) / 100 if lvl else 0.95
        r["ci_level_ok"] = abs(r["ci_level_printed"] - r["ci_level_pub"]) < 1e-9
        if not (r["hr_ok"] and r["rb_matches_printed"] and r["rs_ok"] and r["ci_level_ok"]):
            issues.append((d["line"], name, "RCT estimate", (pub["hr"], pub["ci"], r["ci_level_pub"], pub["our_orientation"], r["exp_rb"]),
                           (est,)))
        r["in_S32"] = tier != "Limited"
        r["tier"] = tier
        r["area"] = area
        out.append(r)
    D = pd.DataFrame(out)
    D.to_csv(OUT / "table1_recheck.csv", index=False)
    print("rows", len(D))
    for c in [x for x in D.columns if x.endswith("_ok") or x.startswith("picot_eq") or x in ("rb_matches_printed", "area_label_json")]:
        print(f"{c:22s} all True: {bool(D[c].all())}  ({int(D[c].sum())}/{len(D)})")
    print("orientation flipped (analysed HR = 1/published):", list(D.trial[D.orientation_flipped]))
    s = D[D.in_S32]
    print("S32 n", len(s), "tiers", dict(Counter(s.tier)), "limited", int((~D.in_S32).sum()), list(D.trial[~D.in_S32]))
    print("S32 areas", dict(Counter(s.area)))
    print("physiologic yes S38", int((D.trial.map(lambda t: LB[t]["physiologic"]) == "yes").sum()), "S32",
          list(s.trial[s.trial.map(lambda t: LB[t]["physiologic"]) == "yes"]))
    lvsys = [t for t in s.trial if "LV_systolic_function" in LB[t]["domains"]]
    lvst = [t for t in s.trial if "LV_structure" in LB[t]["domains"]]
    print("S32 LV systolic labelled", len(lvsys), "LV structure labelled", lvst)
    # kappa from the raw labeller files
    la = {x["trial"]: x["physiologic"] for x in json.loads((A / "claude-v21-paper2/labels/labels_A.json").read_text())}
    lb = {x["trial"]: x["physiologic"] for x in json.loads((A / "claude-v21-paper2/labels/labels_B.json").read_text())}
    ks = sorted(la)
    a_ = np.array([la[k] == "yes" for k in ks])
    b_ = np.array([lb[k] == "yes" for k in ks])
    po = (a_ == b_).mean()
    pe = a_.mean() * b_.mean() + (1 - a_.mean()) * (1 - b_.mean())
    print("labeller kappa", round((po - pe) / (1 - pe), 4), "A yes", int(a_.sum()), "B yes", int(b_.sum()))
    # blind PICOT table: does it carry estimates or tiers?
    pb = (A / "claude-v21-paper2/labels/picot_blind.md").read_text()
    print("picot_blind has RCT-estimate / quality columns:", "RCT estimate" in pb, "quality" in pb.lower())
    # committed vs working table1_picot.md: content identical after whitespace normalisation?
    print("table1_picot committed vs working, cell-identical:", CM == WK, len(CM), len(WK))
    print("ISSUES", len(issues))
    for x in issues:
        print(x)


if __name__ == "__main__":
    main()
