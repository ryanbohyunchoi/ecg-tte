#!/usr/bin/env python
"""Step 5: write the per-issue classification table (aggregate; from criteria_counts.csv, per_trial_fixes.csv,
calibration.csv) to OUT/classification.csv. Classes: NOT PRESENT / PRESENT-MINOR / PRESENT-MODERATE / PRESENT-MAJOR
(rule in docs/v1_criteria_check/TRIAL_CRITERIA_CHECK.md). Proposals only; no spec or paper is changed."""
import sys

import pandas as pd

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v1_criteria_check")
import common as K  # noqa: E402

ROWS = [
    ("CABANA", True, "Earliest-index dedupe puts later-ablation patients in the AAD arm (time zero / arm assignment)", "PRESENT",
     "44.6% of analysed eventual-ablation patients are in the AAD arm; 40% of eligible ablation records (1,378/3,427) removed at dedupe",
     "design-level; not fixable by exclusion", "PRESENT-MAJOR", "Downgrade to Limited, or rebuild as sequential design (RAFT-AF style)"),
    ("LAAOS III", True, "AF gate admits AF first coded in the index surgical stay", "PRESENT", "56.6% (LAAO 23.1%, comparator 64.7%)",
     "base |dlogHR| 0.337->0.064, +ECG 0.143->0.076 (within random-removal range)", "PRESENT-MAJOR",
     "Rebuild requiring AF before the index admission (fix as primary); Limited until rebuilt"),
    ("COMET", True, "Metoprolol arm includes succinate/toprol", "NOT PRESENT",
     "100% of metoprolol arm have a tartrate-named JDAT order on index day; OMOP toprol <11 per arm", "none", "NOT PRESENT", "None"),
    ("COMET", True, "Prior/concurrent succinate exposure (related)", "PRESENT", "15.1% (metoprolol 19.5%, carvedilol 12.0%) in [idx-365, idx]",
     "within random-removal range", "PRESENT-MODERATE", "Add succinate washout (fix as primary) and disclose"),
    ("COMET", True, "No LVEF restriction", "PRESENT", "38.7% of cohort with latest EF > 35 (57.5% of those measured)",
     "balance improves beyond random-removal range; |dlogHR| within range", "PRESENT-MAJOR",
     "Restrict to EF <= 35 (unknown passes) as primary, or downgrade; documented user adaptation"),
    ("TRANSFORM-HF", True, "Time zero not anchored at discharge strategy; switchers excluded; horizon 12 vs 17 mo", "PRESENT",
     "76.9% of furosemide vs 46.6% of torsemide index orders in-hospital; 58% of torsemide first users removed by washout",
     "design-level; not fixable by exclusion", "PRESENT-MAJOR", "Downgrade to Limited (exclude from primary)"),
    ("ELITE II", True, "ARNI orders enter the ARB arm via the 'valsartan' token", "NOT PRESENT",
     "ARNI orders are 'sacubitril'/'entresto' tokens; combined string <11 analysed patients", "none", "NOT PRESENT", "None"),
    ("ELITE II", True, "Prior ARNI use (related)", "PRESENT", "4.0% (ARB 6.6%, ACEi 1.9%)", "within random-removal range",
     "PRESENT-MINOR", "Keep; optional ARNI exclusion; disclose"),
    ("EMPEROR-Preserved", True, "DPP-4i comparator includes saxagliptin/alogliptin", "PRESENT", "1.3% (3.4% of DPP-4i arm)",
     "negligible", "PRESENT-MINOR", "Keep; apply exclusion in any rebuild; disclose"),
    ("LIFE", True, "ECG-LVH text gate admits hedged/negated statements", "PRESENT",
     "21.7% qualify only by hedged statements (32.9% strict); negated statements <11 patients", "within random-removal range",
     "PRESENT-MAJOR", "Rebuild with definite-LVH gate (fix as primary); Limited until rebuilt"),
    ("VALIANT", True, "ARNI orders enter the ARB arm via 'valsartan'", "NOT PRESENT", "combined string 0; prior ARNI ~1%", "none",
     "NOT PRESENT", "None"),
    ("VALIANT", True, "EF-unknown post-MI patients without HF admitted; index-day echo ignored", "PRESENT",
     "58.7% (EF unknown and no HF code 43.2%; index-day EF > 40 15.6%)", "within random-removal range", "PRESENT-MAJOR",
     "Downgrade to Limited, or rebuild requiring LVEF <= 40 or HF (40% retained)"),
    ("CAROLINA", True, "Age bound 40-85 missing", "PRESENT", "11.6% (<40 2.1%, >85 9.5%)", "negligible", "PRESENT-MODERATE",
     "Apply age 40-85 as primary spec"),
    ("LEADER", True, "Other GLP-1RA in prior year not washed out", "PRESENT", "2.1% (liraglutide 6.2%, DPP-4i 1.6%)",
     "negligible", "PRESENT-MINOR", "Keep; apply washout in any rebuild"),
    ("SUSTAIN-6", True, "Other GLP-1RA in prior year not washed out", "PRESENT", "8.7% (semaglutide 16.5%, DPP-4i 2.1%)",
     "negligible", "PRESENT-MODERATE", "Apply washout as primary spec"),
    ("REWIND", False, "Other GLP-1RA in prior year not washed out", "PRESENT", "5.1% (dulaglutide 15.2%, DPP-4i 2.2%)",
     "negligible", "PRESENT-MODERATE", "Already Limited; apply washout"),
    ("DECLARE-TIMI 58", False, "Other SGLT2i not washed out; saxagliptin/alogliptin comparator", "PRESENT",
     "12.0% (SGLT2i 8.8%; saxa/alo 3.6%)", "within random-removal range for +ECG", "PRESENT-MODERATE", "Already Limited; apply fixes"),
    ("CANVAS", True, "Other SGLT2i in prior year not washed out", "PRESENT", "7.9% (canagliflozin 14.4%, DPP-4i 7.3%)",
     "within random-removal range", "PRESENT-MODERATE", "Apply washout as primary spec"),
    ("AMPLIFY", True, "Recurrent VTE counts any VTE code on later stays (persisting codes)", "PRESENT",
     "only 85 of 980 events remain with a primary-billing VTE code; 7.1% of first event stays primary-billing",
     "outcome-level; base |dlogHR| 0.220->0.095, +ECG 0.153->0.084", "PRESENT-MAJOR",
     "Re-specify outcome (primary-billing VTE) or Limited; disclose (not in Table 1 notes)"),
    ("LODESTAR", True, "Coronary revascularisation component missing", "PRESENT (disclosed)",
     "4.0% of patients gain or advance an event (events +14%)", "negligible", "PRESENT-MINOR", "Keep; already disclosed"),
    ("PROVE IT-TIMI 22", True, "Revascularisation >= 30 d missing", "PRESENT (disclosed)",
     "about 2% of patients gain or advance an event (events +7%)", "negligible", "PRESENT-MINOR", "Keep; already disclosed"),
]

if __name__ == "__main__":
    K.umask()
    D = pd.DataFrame(ROWS, columns=["trial", "in_S32", "issue", "present", "affected", "primary_analysis_impact", "classification",
                                    "proposed_action"])
    D.to_csv(K.OUT / "classification.csv", index=False)
    print(D[["trial", "classification", "proposed_action"]].to_string(index=False))
