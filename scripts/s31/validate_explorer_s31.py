#!/usr/bin/env python
"""Step 1 gate (queue 2026-10-14, s31): after adding the s31 trial set to scripts/build_balance_explorer.py, re-run its full
validation (build_balance_explorer.check: published values, paper 2 / leakage / no-LVEF / PS-CVD10 / spec-v2 cross-checks) with the
outputs redirected to audits/claude-s31-20261014/be_check, and compare the summary with the previous run
(audits/claude-balance-explorer/validation_summary.json). The standalone explorer HTML is not rewritten. Also checks the new sets.

Usage (tte-analysis env): python scripts/s31/validate_explorer_s31.py
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build_balance_explorer as BE  # noqa: E402

OUT = BE.A / "claude-s31-20261014" / "be_check"


def main():
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    old = json.load(open(BE.SCR / "validation_summary.json"))
    g = BE.load_grid()
    vs = BE.verify_sources(g)
    assert vs["v20_vs_grid"]["max_abs_dev"] == 0 and vs["v20_vs_grid"]["ex58_mismatch"] == 0
    g2 = BE.load_grid_v2(g)
    D = BE.build_data(g, g2)
    tr = D["trials"]
    sets = {v: len(BE.trial_set(tr, v)) for v in ("s31", "s32", "f37", "all", "v2", "v2c")}
    assert sets["s31"] == 31 and sets["s32"] == 32 and sets["f37"] == 37 and sets["all"] == 38, sets
    assert [tr[i]["full"] for i in BE.trial_set(tr, "s32") if i not in BE.trial_set(tr, "s31")] == ["PROTECT AF"]
    pa = next(t for t in tr if t["full"] == "PROTECT AF")
    assert pa["status"] == "excluded at feasibility (smaller arm < 350)" and not pa["s31"] and not pa["f37"] and pa["s32"]
    tiers = {q: len(BE.trial_set(tr, "q37:" + q)) for q in ("Excellent", "Good", "Moderate", "Limited")}
    assert tiers == {"Excellent": 3, "Good": 11, "Moderate": 17, "Limited": 6}, tiers
    areas = {a: len(BE.trial_set(tr, "area31:" + a)) for a in ("AF", "HF", "Diabetes", "Hypertension", "ACS / MI", "Other")}
    BE.SCR = OUT  # check() writes its tables here
    if "--compare-only" not in sys.argv:
        BE.check(g, g2, D)
    new = json.load(open(OUT / "validation_summary.json"))
    diff = {k: (old.get(k), new.get(k)) for k in set(old) | set(new) if old.get(k) != new.get(k)}
    # the only admissible differences: more spec-v2 rows checked, because the PS-Clinical MI summary (claude-v2-psclin-mi) gained the
    # rescored set "Snew" after the previous explorer run; every deviation, match count and flag must be identical
    counts = {"v2_sets", "v2_js_targets", "v2_rows_by_source", "v2_level_rows", "v2_rows"}
    explained = set(diff) <= counts and (not diff or new["v2_sets"] == sorted(old["v2_sets"] + ["Snew"]))
    res = dict(sets=sets, tiers_of_37=tiers, areas_of_31=areas, protect_af_status=pa["status"], summary_identical=not diff,
               differences_only_extra_Snew_rows=explained, diff=diff,
               published_match=f"{new['published_match']}/{new['published_checks']}", ps10_doc_match=f"{new['ps10_doc_match']}/{new['ps10_doc_checks']}")
    json.dump(res, open(OUT / "s31_gate.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
    assert explained and new["published_match"] == new["published_checks"] and new["ps10_doc_match"] == new["ps10_doc_checks"], diff


if __name__ == "__main__":
    main()
