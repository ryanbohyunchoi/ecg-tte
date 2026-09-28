#!/usr/bin/env python
"""Write docs/v18/af_candidates.json (schema of docs/v17/candidates.json) from the V18 specs and the count-only screen
(audits/claude-v18-screen/<trial>.json; aggregates only). Selection rules: docs/v18/af_candidates.md."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import trial_specs as TS  # noqa: E402

S = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v18-screen")
DOC = HERE.parent.parent / "docs" / "v18"
RULE = dict(min_arm_with_ecg=300, min_pooled_events_with_ecg=50, max_same_record_share_one_existing_cohort=0.80)
REG = {"frail_af": "frail-af", "laaos3": "laaos3", "protect_af": "protect-af", "raft_af": "raft-af", "active_w": "active-w"}
SCREENED = ["prague17", "protect_af", "frail_af", "laaos3", "raft_af", "augustus", "pioneer_af_pci", "re_dual_pci", "active_w",
            "renal_af", "engage_af"]
# a re-check of a trial already built in v1.3 matches its own earlier cohort; that is not a near-duplicate of another trial
SELF = {"engage_af": "claude-engage-af-cohort-v1"}
NOT_SCREENED = {
    "race_ii": "lenient vs strict heart-rate target: treat-to-target strategy without identifiable time zero; primary result is an absolute difference (PMID 20231232)",
    "rate_af": "primary outcome quality of life (SF-36) (PMID 33351042)",
    "athena": "dronedarone vs placebo; no standard active-comparator adaptation; CV hospitalisation not reliably identifiable in AF (PMID 19213680)",
    "pallas_eldercare_noah": "placebo-controlled",
    "averroes_bafta": "aspirin comparator (largely OTC)",
    "artesia": "device-detected subclinical AF not identifiable; aspirin comparator (PMID 37952132)",
    "castle_htx": "end-stage HF with ablation; parent CASTLE-AF ablation arm 149 after gates (v1.3) (PMID 37634135)",
    "raaft2_mantra_earlyaf_stopaf_cryofirst_aatac": "primary outcome arrhythmia recurrence/burden",
    "champion_af": "LAAO vs NOAC; primary efficacy result is a risk difference; same comparison/cohort as PRAGUE-17 (PMID 41910347)",
    "closure_af": "LAAO vs best medical care; RMST difference, no HR; mixed comparator (PMID 41849741)",
    "prevail": "same comparison as PROTECT AF (near-duplicate cohort) (PMID 24998121)",
    "option": "LAAO after ablation vs OAC; primary efficacy difference in proportions; subset of LAAO cohort (PMID 39555822)",
    "entrust_af_pci_envisage_tavi": "edoxaban (~150 persons ever ordered) (PMIDs 31492505, 34449183)",
    "afire": "antiplatelet de-escalation on rivaroxaban; no identifiable initiation (PMID 31475793)",
    "periprocedural_oac_bruise_control": "peri-procedural outcomes / pocket haematoma; no primary HR",
    "elan_timing_optimas": "timing of DOAC after stroke; risk differences",
    "invictus_river": "rheumatic / bioprosthetic-mitral AF; non-HR primary results",
    "castle_af": "v1.3: ablation arm 149 after gates",
    "dionysos": "outcome not emulable; analysed before",
}


def main():
    out = {}
    for k in SCREENED:
        scr = json.load(open(S / f"{k}.json"))
        spec, pub = TS.TRIALS[k], TS.PUBLISHED[k]
        mn = scr["min_arm_with_ecg"] if isinstance(scr["min_arm_with_ecg"], int) else 0
        ev = scr["pooled_primary_events_horizon_with_ecg"]
        ev = ev if isinstance(ev, int) else 0
        top = {c: s for c, s in scr["same_record_share_top3"].items() if c != SELF.get(k)}
        same = max(top.items(), key=lambda x: x[1]) if top else None
        reasons = []
        if mn < RULE["min_arm_with_ecg"]:
            reasons.append(f"smaller arm with ECG = {scr['min_arm_with_ecg']} < 300")
        if ev < RULE["min_pooled_events_with_ecg"]:
            reasons.append(f"pooled events with ECG = {scr['pooled_primary_events_horizon_with_ecg']} < 50")
        if same and same[1] >= RULE["max_same_record_share_one_existing_cohort"]:
            reasons.append(f"near-duplicate cohort: {same[1]:.0%} of (patient, index) records identical to {same[0]}")
        if k == "engage_af":
            reasons.append("re-check of v1.3 spec: still infeasible")
        status = "selected_for_build" if (not reasons and k in REG) else "not_built"
        out[k] = dict(
            name=spec["name"], registry_name=REG.get(k), status=status, reasons_not_built=reasons,
            arms=[a for a, _ in spec["arms"]], arm_keywords={a: kws for a, kws in spec["arms"]}, design=spec.get("design", "new_user")
            + ("+arm0_procedure" if spec.get("arm0_procedure") else ""),
            gates=spec["gate"], exclusions=spec["exclusions"], min_age=spec.get("min_age", 18), max_age=spec.get("max_age"),
            index_window=[spec["index_start"], spec["index_end"]], outcome=[str(c) for c in TS.OUTCOMES[k]], rct_endpoint=pub["endpoint"],
            horizon_months=TS.HORIZON_MONTHS[k], rct_hr=pub["hr"], rct_ci=list(pub["ci"]), rct_ci_level=pub.get("ci_level", 0.95),
            rct_measure=pub.get("measure"), rct_arms=pub.get("rct_arms"), our_orientation=pub.get("our_orientation"), citation=pub["source"],
            spec_version=spec["spec_version"], note=spec.get("note", ""),
            feasibility=dict(n_by_arm={a: v["n"] for a, v in scr["arms"].items()}, n_with_ecg_by_arm={a: v["n_with_ecg"] for a, v in scr["arms"].items()},
                             min_arm_with_ecg=scr["min_arm_with_ecg"], pooled_primary_events_horizon=scr["pooled_primary_events_horizon"],
                             pooled_primary_events_horizon_with_ecg=scr["pooled_primary_events_horizon_with_ecg"],
                             pooled_deaths_horizon=scr["pooled_deaths_horizon"],
                             max_same_record_share_one_existing_cohort=({"cohort": same[0], "share": same[1]} if same else None),
                             same_record_share_top3=scr["same_record_share_top3"]))
    for k, r in NOT_SCREENED.items():
        out[k] = dict(status="not_screened", reasons_not_built=[r], feasibility=None)
    DOC.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(DOC / "af_candidates.json", "w"), indent=1)
    print(json.dumps({k: (v["status"], v.get("reasons_not_built")) for k, v in out.items()}, indent=0))


if __name__ == "__main__":
    main()
