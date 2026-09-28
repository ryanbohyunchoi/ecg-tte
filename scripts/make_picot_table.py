#!/usr/bin/env python
"""Main-manuscript Table 1: PICOT for the 38 emulated trials (from trial_specs.py; aggregate/design info only)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v16"))
import trial_specs as S  # noqa: E402
import v13_common as C  # noqa: E402
import v16_engine as E  # noqa: E402
import json  # noqa: E402
SEL = json.load(open(ROOT.parent / "docs" / "v17" / "trial_selection.json"))["trials"]

SETS = [("Development", list(E.TRIALS)), ("Confirmation (general)", list(C.V17)), ("Confirmation (AF)", list(C.V18))]
REG = {**C.PRIMARY, **C.EXTRA}
POP = {  # concise population as emulated (from spec gates/exclusions)
    "comet": "HF", "paradigm_hf_seq": "HF on ACEi/ARB (switch at time zero)", "transform_hf": "HF hospitalisation (discharge within 30 d)",
    "elite_ii": "HF, age ≥60", "life": "Hypertension with ECG-LVH, age 55–80", "plato": "ACS within 30 d",
    "aristotle": "AF", "rocket_af": "AF", "rely": "AF", "allhat": "Hypertension, age ≥55",
    "emperor_preserved": "HF with T2D", "east_afnet4": "Early AF (diagnosis ≤1 y) on rate control", "cabana": "AF",
    "ontarget": "Established vascular disease or high-risk diabetes, age ≥55", "value": "Hypertension, age ≥50",
    "ascot": "Hypertension, age 40–79", "empa_reg": "T2D with established CVD", "carolina": "T2D",
    "leader": "T2D with CVD, age ≥50", "sustain6": "T2D with CVD, age ≥50", "rewind": "T2D, age ≥50", "declare": "T2D, age ≥40",
    "canvas": "T2D, age ≥30", "tecos": "T2D with CVD, age ≥50", "carmelina": "T2D with kidney disease",
    "valiant": "MI within 30 d", "insight": "High-risk hypertension, age ≥55", "affirm": "AF on rate control, age ≥65",
    "af_chf": "AF with HF on rate control", "precision": "Arthritis with CV risk", "amplify": "Acute VTE",
    "lodestar": "Coronary artery disease", "prove_it": "ACS within 30 d", "frail_af": "AF on warfarin, age ≥75",
    "laaos3": "AF undergoing cardiac surgery", "protect_af": "AF on warfarin with ≥1 stroke risk factor",
    "raft_af": "AF with HF on rate control", "active_w": "AF with ≥1 stroke risk factor, age ≥55",
}
ARM = {"metoprolol_tartrate": "metoprolol", "sacubitril_valsartan": "sacubitril-valsartan", "acei": "ACEi", "arb": "ARB",
       "beta_blocker": "β-blocker", "sglt2i": "SGLT2i", "dpp4i": "DPP-4i", "antiarrhythmic": "rhythm-control drug added",
       "rate_control": "continued rate control", "af_ablation": "catheter ablation", "doac_switch": "switch to DOAC",
       "laa_occlusion": "surgical LAA occlusion", "cardiac_surgery": "surgery without LAA occlusion", "laao": "percutaneous LAA closure",
       "thiazide": "thiazide", "sulfonylurea": "sulfonylurea"}


def qual(k):
    r = SEL.get(k, {})
    if not r:
        return "not rated"
    if r.get("fidelity_include_strict"):
        return "High (strict)"
    return "High" if r.get("fidelity_include") else "Lower"


def arms(t):
    a = t["arms"]
    return [ARM.get(x[0], x[0]) for x in a]


def main():
    rows = ["| Area | Trial | Population | Intervention | Comparator | Outcome (RCT primary endpoint) | Time (mo) | RCT HR (95% CI) | Emulation quality |",
            "|---|---|---|---|---|---|---|---|---|"]
    AREA = {"comet": "HF", "paradigm_hf_seq": "HF", "transform_hf": "HF", "elite_ii": "HF", "emperor_preserved": "HF",
            "aristotle": "AF", "rocket_af": "AF", "rely": "AF", "east_afnet4": "AF", "cabana": "AF", "affirm": "AF", "af_chf": "AF",
            "frail_af": "AF", "laaos3": "AF", "protect_af": "AF", "raft_af": "AF", "active_w": "AF",
            "life": "Hypertension", "allhat": "Hypertension", "value": "Hypertension", "ascot": "Hypertension", "insight": "Hypertension",
            "plato": "ACS / MI", "valiant": "ACS / MI"}
    order = ["AF", "HF", "Hypertension", "ACS / MI", "Diabetes", "Other"]
    allk = [(REG[n][0], n) for _, names in SETS for n in names]
    DM = {"empa_reg", "carolina", "leader", "sustain6", "rewind", "declare", "canvas", "tecos", "carmelina"}
    area = lambda k: AREA.get(k, "Diabetes" if k in DM else "Other")
    allk.sort(key=lambda x: order.index(area(x[0])))
    for _k, n in allk:
        if True:
            sname = area(_k)
            k = REG[n][0]
            t = S.TRIALS[k]
            p = S.PUBLISHED[k]
            i, c = arms(t)
            if p.get("our_orientation") and abs(p["our_orientation"] - p["hr"]) > 1e-6:
                i, c = c, i  # display in the RCT's orientation (e.g., COMET: carvedilol vs metoprolol)
            if k == "cabana":
                c = "antiarrhythmic drug"
            if "placebo" in p.get("rct_arms", ""):
                c += " (placebo proxy)"
            meas = "" if str(p.get("measure", "HR")).startswith("HR") else f" [{str(p['measure']).split(' (')[0].split(',')[0]}]"
            lo, hi = p["ci"]
            nm = t["name"].split(" (")[0].split(":")[0].replace(" switcher, sequential", "").replace(" amlodipine vs thiazide", "")
            rows.append(f"| {sname} | {nm} | {POP[k]} | {i} | {c} | {p['endpoint']} | {S.HORIZON_MONTHS[k]} | "
                        f"{p['hr']:.2f} ({lo:.2f}–{hi:.2f}){meas} | {qual(k)} |")
    out = "\n".join(rows)
    (ROOT.parent / "docs" / "paper" / "table1_picot.md").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
