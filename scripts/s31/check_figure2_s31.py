#!/usr/bin/env python
"""Step 3 check (queue 2026-10-14): every Figure 2 value (audits/claude-s31-20261014/figure2_values.json, written by
scripts/figures/make_figure2_latent.py) against build_balance_explorer on s31, here via audits/claude-s31-20261014/s31_numbers.json
(scripts/s31/s31_numbers.py: BE.Grid levels and the s31 summaries) and the s31 Python summaries' domain table."""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build_balance_explorer as BE  # noqa: E402

O = BE.A / "claude-s31-20261014"
F = json.load(open(O / "figure2_values.json"))
N = json.load(open(O / "s31_numbers.json"))["S31"]
rows = []
for rg, z in N["ladder"].items():
    for a in ("unmatched", "base", "ECG", "CLMBR", "ECG+CLMBR"):
        rows.append((f"C level {rg} {a}", F["C"][rg][a], round(z["level_" + a], 6), 2e-6))
        if a != "unmatched":
            rows.append((f"C trials {rg} {a}", F["C"][rg]["k_" + a], z["k_" + a], 0))
    for a in ("ECG", "CLMBR", "ECG+CLMBR"):
        for i, k in enumerate(("rr", "lo", "hi")):
            rows.append((f"C {k} {rg} {a}", F["C"][rg]["rr_" + a][i], round(z[a][k], 4), 2e-4))
p = N["primary"]
rows += [("D improved", F["D"]["improved"], int(p["better"].split("/")[0]), 0), ("D trials", F["D"]["k"], 31, 0),
         ("D mean", F["D"]["mean"], round(p["dpts"], 6), 2e-6), ("D P", F["D"]["p"], round(p["p_pct"], 6), 2e-6),
         ("D pct ref", F["D"]["pct_ref"], round(p["pct_ref"], 6), 2e-6), ("D pct arm", F["D"]["pct_arm"], round(p["pct_arm"], 6), 2e-6),
         ("B All 54 base", F["B"]["All 54"]["base"], round(p["m_ref"], 6), 2e-6), ("B All 54 ECG", F["B"]["All 54"]["ECG"], round(p["m_arm"], 6), 2e-6)]
D = pd.read_csv(O / "summary_v1/domains.csv")
D = D[(D.set == "S31") & (D.config == "main") & (D.contrast == "P5: ECG vs base")].set_index("domain")
for gname, x in F["B"].items():
    if gname in D.index:
        rows += [(f"B {gname} base", x["base"], round(float(D.loc[gname, "mean_b"]), 6), 2e-6), (f"B {gname} ECG", x["ECG"], round(float(D.loc[gname, "mean_a"]), 6), 2e-6)]
bad = [r for r in rows if abs(r[1] - r[2]) > r[3]]
res = dict(checked=len(rows), mismatches=bad, k_set=F["k_set"], basis=F["basis"])
json.dump(res, open(O / "figure2_check.json", "w"), indent=1)
print(f"Figure 2 vs s31: {len(rows)} values checked, {len(bad)} mismatches")
assert not bad, bad
