#!/usr/bin/env python
"""Write docs/v17/candidates.json + candidates.md from the v1.7 specs and the count-only screen (aggregates only)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import trial_specs as TS  # noqa: E402

S = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v17-screen")
DOC = HERE.parent.parent / "docs" / "v17"
RULE = dict(min_arm_with_ecg=300, min_pooled_events_with_ecg=50, max_same_record_share_one_v16_cohort=0.80)
# share of (patient, index date) records identical to a single v1.6 cohort (max over the 18), from the screen
SAME = {"accomplish": ("allhat", 0.96), "af_chf": ("east-afnet4", 0.21), "affirm": ("east-afnet4", 0.25), "amplify": ("aristotle", 0.01),
        "canvas": ("empa-reg", 0.31), "carmelina": ("carolina", 0.31), "declare": ("empa-reg", 0.35), "leader": ("empa-reg", 0.58),
        "lodestar": ("ontarget", 0.09), "precision": ("value", 0.02), "rewind": ("empa-reg", 0.27), "sustain6": ("empa-reg", 0.32),
        "tecos": ("empa-reg", 0.36), "valiant": ("ontarget", 0.61), "prove_it": ("plato", 0.35), "insight": ("allhat", 0.63)}
REG = {"leader": "leader", "sustain6": "sustain6", "rewind": "rewind", "declare": "declare", "canvas": "canvas", "tecos": "tecos",
       "carmelina": "carmelina", "valiant": "valiant", "insight": "insight", "affirm": "affirm", "af_chf": "af-chf", "precision": "precision",
       "amplify": "amplify", "lodestar": "lodestar", "prove_it": "prove-it"}
EXTRA_BENCH = {  # screened-but-not-built candidates: benchmark from the primary-paper abstract (PubMed), for the record
    "accomplish": (0.80, (0.72, 0.90), "Jamerson et al. NEJM 2008;359:2417-28 (PMID 19052124)", "CV death, MI, stroke, angina hospitalisation, resuscitated arrest, coronary revascularisation"),
    "savor": (1.00, (0.89, 1.12), "Scirica et al. NEJM 2013;369:1317-26 (PMID 23992601)", "CV death, MI or ischaemic stroke"),
    "tosca_it": (0.96, (0.74, 1.26), "Vaccaro et al. Lancet Diabetes Endocrinol 2017;5:887-97 (PMID 28917544)", "death, nonfatal MI, nonfatal stroke, urgent coronary revascularisation"),
    "euclid": (1.02, (0.92, 1.13), "Hiatt et al. NEJM 2017;376:32-40 (PMID 27959717)", "CV death, MI or ischaemic stroke"),
    "isar_react5": (1.36, (1.09, 1.70), "Schupke et al. NEJM 2019;381:1524-34 (PMID 31475799)", "death, MI or stroke at 1 y (ticagrelor vs prasugrel)"),
    "cares": (1.03, (None, 1.23), "White et al. NEJM 2018;378:1200-10 (PMID 29527974); one-sided 98.5% upper bound only", "CV death, MI, stroke, UA with urgent revascularisation"),
    "fast": (0.85, (0.70, 1.03), "Mackenzie et al. Lancet 2020;396:1745-57 (PMID 33181081); on-treatment primary", "hospitalisation for MI/biomarker-positive ACS, stroke or CV death"),
    "oral_surv": (1.33, (0.91, 1.94), "Ytterberg et al. NEJM 2022;386:316-26 (PMID 35081280)", "MACE (tofacitinib vs TNFi)"),
    "pronounce": (1.28, (0.59, 2.79), "Lopes et al. Circulation 2021;144:1295-307 (PMID 34459214)", "death, MI or stroke at 12 months"),
    "ideal": (0.89, (0.78, 1.01), "Pedersen et al. JAMA 2005;294:2437-45 (PMID 16287954)", "coronary death, nonfatal MI or resuscitated cardiac arrest"),
}
EXTRA_H = {"accomplish": 36, "savor": 25, "tosca_it": 57, "euclid": 30, "isar_react5": 12, "cares": 32, "fast": 48, "oral_surv": 48, "pronounce": 12, "ideal": 58}


def main():
    out = {}
    for k in TS.V17:
        f = S / f"{k}.json"
        scr = json.load(open(f))
        spec = TS.TRIALS[k]
        pub = TS.PUBLISHED.get(k)
        n_ecg = scr["min_arm_with_ecg"] if isinstance(scr["min_arm_with_ecg"], int) else 0
        ev = scr["pooled_primary_events_horizon_with_ecg"]
        ev = ev if isinstance(ev, int) else 0
        same = SAME.get(k)
        reasons = []
        if n_ecg < RULE["min_arm_with_ecg"]:
            reasons.append(f"smaller arm with ECG = {scr['min_arm_with_ecg']} < 300")
        if ev < RULE["min_pooled_events_with_ecg"]:
            reasons.append(f"pooled events with ECG = {ev} < 50")
        if same and same[1] >= RULE["max_same_record_share_one_v16_cohort"]:
            reasons.append(f"near-duplicate cohort: {same[1]:.0%} of (patient, index) records identical to v1.6 {same[0]}")
        status = "selected_for_build" if (not reasons and k in REG) else "not_built"
        if pub:
            hr, ci, cit, ep = pub["hr"], list(pub["ci"]), pub["source"], pub["endpoint"]
        else:
            hr, ci, cit, ep = EXTRA_BENCH[k]
            ci = list(ci)
        out[k] = dict(
            name=spec["name"], registry_name=REG.get(k), status=status, reasons_not_built=reasons,
            arms=[a for a, _ in spec["arms"]], arm_keywords={a: kws for a, kws in spec["arms"]}, design=spec.get("design", "new_user"),
            gates=spec["gate"], exclusions=spec["exclusions"], min_age=spec.get("min_age", 18), max_age=spec.get("max_age"),
            index_window=[spec["index_start"], spec["index_end"]], outcome=[str(c) for c in TS.OUTCOMES[k]], rct_endpoint=ep,
            horizon_months=TS.HORIZON_MONTHS.get(k, EXTRA_H.get(k)), rct_hr=hr, rct_ci=ci,
            rct_ci_level=(pub or {}).get("ci_level", 0.95), rct_measure=(pub or {}).get("measure"), rct_arms=(pub or {}).get("rct_arms"),
            our_orientation=(pub or {}).get("our_orientation"), citation=cit, spec_version=spec["spec_version"], note=spec.get("note", ""),
            feasibility=dict(n_by_arm={a: v["n"] for a, v in scr["arms"].items()}, n_with_ecg_by_arm={a: v["n_with_ecg"] for a, v in scr["arms"].items()},
                             min_arm_with_ecg=scr["min_arm_with_ecg"], pooled_primary_events_horizon=scr["pooled_primary_events_horizon"],
                             pooled_primary_events_horizon_with_ecg=scr["pooled_primary_events_horizon_with_ecg"],
                             pooled_deaths_horizon=scr["pooled_deaths_horizon"],
                             max_same_record_share_one_v16_cohort=({"cohort": same[0], "share": same[1]} if same else None),
                             patients_in_any_v16_cohort=scr["overlap_with_v16_18_cohorts"]))
    # previously built / analysed / infeasible trials (not new confirmation trials)
    prior = {
        "paradise_mi": dict(status="not_built", reasons_not_built=["v1.3 ext queue FAILED_FEASIBILITY: smaller arm (sacubitril/valsartan) with ECG = 296 < 300 (cohort 356 ARNI / 1,375 ACEi)"],
                            rct_hr=0.90, rct_ci=[0.78, 1.04], citation=TS.PUBLISHED["paradise_mi"]["source"], horizon_months=22),
        "dcp": dict(status="not_built", reasons_not_built=["v1.3 ext queue FAILED_FEASIBILITY: smaller arm (chlorthalidone switchers) with ECG = 255 < 300 (cohort 441 / 1,764)"],
                    rct_hr=1.04, rct_ci=[0.94, 1.16], citation=TS.PUBLISHED["dcp"]["source"], horizon_months=29),
        "invest": dict(status="not_built", reasons_not_built=["v1.3 ext queue FAILED_FEASIBILITY: smaller arm (verapamil) with ECG = 224 < 300 (cohort 316 / 1,234)"],
                       rct_hr=0.98, rct_ci=[0.90, 1.06], citation=TS.PUBLISHED["invest"]["source"], horizon_months=32),
        "paragon_hf": dict(status="excluded_previously_analysed", reasons_not_built=["built 2026-09-24 and analysed (phase-1 balance and phase-2 HR); results seen, so not a blind confirmation trial"]),
        "dapa_hf": dict(status="excluded_previously_analysed", reasons_not_built=["DAPA-HF/EMPEROR-Reduced DPP-4i design built and analysed 2026-09-24 (phase 1 and 2); results seen"]),
        "partner": dict(status="excluded_previously_analysed", reasons_not_built=["built and analysed 2026-09-24; results seen"]),
        "dionysos": dict(status="excluded_previously_analysed", reasons_not_built=["built and balance-analysed 2026-09-24; outcome not emulable"]),
        "triton": dict(status="not_built", reasons_not_built=["2026-09-24 FAILED_FEASIBILITY: smaller arm with ECG = 278"]),
        "engage_af": dict(status="not_built", reasons_not_built=["v1.3: edoxaban arm 70 after gates (edoxaban ~150 persons ever ordered)"]),
        "castle_af": dict(status="not_built", reasons_not_built=["v1.3: ablation arm 149 after gates"]),
        "topcat": dict(status="not_screened", reasons_not_built=["placebo-controlled with no accepted active-comparator proxy for spironolactone in HFpEF"]),
        "hope3": dict(status="not_screened", reasons_not_built=["placebo-controlled polypill/statin primary prevention; no active comparator"]),
        "credence": dict(status="not_screened", reasons_not_built=["primary endpoint renal (ESKD, doubling of creatinine); CANVAS covers canagliflozin vs DPP-4i"]),
        "devote": dict(status="not_screened", reasons_not_built=["degludec vs glargine not identifiable: generic insulin orders carry the token 'insulin' only"]),
        "averroes": dict(status="not_screened", reasons_not_built=["aspirin largely OTC; trial population = VKA-unsuitable, not identifiable"]),
        "race": dict(status="not_screened", reasons_not_built=["no HR reported for the primary endpoint (absolute difference); AFFIRM/AF-CHF cover the question"]),
        "empa_reg_emperor_reduced_alt": dict(status="not_screened", reasons_not_built=["EMPEROR-Reduced/DELIVER re-use SGLT2i cohorts already analysed (DAPA-HF, EMPEROR-Preserved)"]),
    }
    for k, v in prior.items():
        out[k] = dict(v, feasibility=None)
    DOC.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(DOC / "candidates.json", "w"), indent=1)
    print(json.dumps({k: (v["status"], v.get("reasons_not_built")) for k, v in out.items()}, indent=0))


if __name__ == "__main__":
    main()
