#!/usr/bin/env python
"""Re-score emulation quality (framework v2.0) on the spec-v2 fixed cohorts (queue docs/queue/QUEUE_2026_10_08.md step D;
doc docs/emulation_quality_v2/RESCORE_V2_COHORTS.md).

Inputs (read-only): docs/emulation_quality_v2/quality_v2_final.json (adjudicated v2.0 scores, version 1 cohorts);
scripts/v2_cohorts/specs_v2.py (the spec-v2 rule table: what was applied); docs/v2_cohorts/COHORT_FIXES.md;
audits/claude-eq2-v2cohorts/dc_bands.csv (scripts/emulation_quality_v2/dc_v2_cohorts.py: DA size / EF-measured bands, no
outcome contrast). Tier rules, item anchors, the provisional-move rules and the tier function are those of
scripts/emulation_quality_v2/adjudicate.py, imported unchanged.

Subcommands (results are never read by `score`; `impact` runs only after quality_v2_cohorts.json is written and hashed):
  score   apply the rescoring decisions (RESCORE below, one reason each) and the uniform numeric-entry-bound rule to all 38
          records; DA re-derived from the spec-v2 data checks; totals, tiers, analysed set, Excellent + Good, provisional
          reach computed mechanically -> docs/emulation_quality_v2/quality_v2_cohorts.json, audits/claude-eq2-v2cohorts/
          tiers_v2cohorts.csv, json_sha256.txt
  impact  primary PS-CVD5 + ECG vs PS-CVD5 (main configuration, 54 leakage-corrected items) on the spec-v2 cells
          (audits/claude-v2-cohorts, variant v2) for: new set, new Excellent + Good, all 38, paper 1's 32; 4,000-resample
          bootstrap (seed 20261001), exact one-sided sign-flip, |dlog HR| with sign-flip and benchmark-permutation P (20,000
          draws): scripts/v20/sens_primary32.contrast_row unchanged. Gates: (a) version 1 cells, paper 1's 32 -> paper 2's
          published 8.8% (4.4-13.3); (b) spec-v2 cells, provisional 29 -> the S29 row of scripts/v2_psclin_mi/psclin_mi.py
          summary (P5: ECG vs base), exactly. -> audits/claude-eq2-v2cohorts/impact_v2cohorts.csv
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import adjudicate as ADJ  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

FINAL = ROOT / "docs/emulation_quality_v2/quality_v2_final.json"
OUTJ = ROOT / "docs/emulation_quality_v2/quality_v2_cohorts.json"
AUD = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-eq2-v2cohorts")
ITEMS = ADJ.ITEMS
DOC = "docs/v2_cohorts/COHORT_FIXES.md"
SPEC = "scripts/v2_cohorts/specs_v2.py"

# ------------------------------------------------------------------------------------------------ rescoring decisions
# trial -> {item: (score, status, reason)}. Only items whose basis changed with the spec-v2 cohort are listed; every other
# item keeps its adjudicated score. DA is handled by da_rule() below (data checks on the fixed cohorts), not here.
RESCORE = {
    "COMET": {
        "SI": (0, "final", "COMET-SI-1 fixed: metoprolol succinate-named orders in [index-365, index] excluded (specs_v2 "
                           "comet_succinate_365). No undocumented defect remains."),
        "EL": (2, "final", "Unchanged at 2: LVEF <= 35% is now applied as an exclusion (comet_lvef_le35, unknown passes; its "
                           "coverage is scored in DA.a), but prior CV admission within 2 years and background diuretic + ACEi "
                           "therapy remain omitted (documented adaptations): two criteria -> 2.")},
    "VALIANT": {
        "SI": (0, "final", "VALIANT-SI-1 fixed: the LV-dysfunction-or-HF rule uses the latest EF in [index-365, index] (index-day "
                           "echo included) and excludes EF > 40 (specs_v2 valiant_lvd_or_hf). ARNI exclusion added (<5%)."),
        "EL": (0, "final", "LV dysfunction and/or HF now required (EF <= 40 known, or EF unknown with an I50 code on/before "
                           "index): the audit's S4 point (missing HF/LVD gate) is resolved by the rebuild; 0.")},
    "EMPEROR-Preserved": {
        "SI": (1, "provisional", "Saxagliptin/alogliptin excluded (fixed); the NT-proBNP entry bound applied (uniform rule: 0). "
                                 "Remaining: any-position I50 for HF hospitalisation (C3, share unknown) -> 1 provisional.")},
    "DECLARE-TIMI 58": {
        "SI": (1, "provisional", "Other-SGLT2i washout and saxagliptin/alogliptin exclusion applied (DECLARE-SI-1 fixed). "
                                 "Remaining: any-position I50 (C3, share unknown) -> 1 provisional.")},
    "CANVAS Program": {
        "SI": (0, "final", "CANVAS-SI-1 fixed: other-SGLT2i orders in [index-365, index] excluded.")},
    "LEADER": {
        "SI": (0, "final", "LEADER-SI-1 (<5%) fixed by the other-GLP-1RA washout; HbA1c >= 7.0% applied (uniform rule: 0).")},
    "SUSTAIN-6": {
        "SI": (1, "provisional", "SUSTAIN6-SI-1 fixed (other-GLP-1RA washout). Remaining: SUSTAIN6-SI-2 generic semaglutide token "
                                 "(oral / obesity formulations; share not checked) -> 1 provisional.")},
    "REWIND": {
        "SI": (0, "final", "REWIND-SI-1 fixed: other-GLP-1RA orders in [index-365, index] excluded.")},
    "LAAOS III": {
        "SI": (0, "final", "LAAOS3-SI-1 fixed: AF must be coded before the index admission (specs_v2 af_before_admission).")},
    "LIFE": {
        "SI": (0, "final", "LIFE-SI-1 fixed (definite-LVH statement gate, specs_v2 definite_lvh); LIFE-SI-2 BP entry range "
                           "applied (bp_life; uniform rule: 0).")},
    "CAROLINA": {
        "SI": (0, "final", "CAROLINA-SI-1 fixed: age 40-85 applied; HbA1c 6.5-8.5% (7.5% on SU) applied (uniform rule: 0).")},
    "AMPLIFY": {
        "SI": (0, "final", "AMPLIFY-SI-1 fixed by the outcome re-definition (its proposed spec edit: first stay >= 7 d after the "
                           "index stay with a primary hospital-billing VTE code). OU stays 2 (inpatient-only ascertainment, "
                           "documented; the stricter definition does not add outpatient events).")},
    "INSIGHT": {
        "SI": (0, "final", "INSIGHT-SI-1 BP entry threshold applied (bp_insight; uniform rule: 0). No other undocumented defect.")},
    "PARADIGM-HF": {
        "SI": (1, "provisional", "PARADIGM-SI-1-B fixed (NP threshold applied; uniform rule: 0). Remaining: PARADIGM-SI-1 "
                                 "any-position I50 (C3, share unknown) -> 1 provisional.")},
    # outcome rebuilds: framework OU text, "Once a rebuild adds it, OU is re-scored" (the dominant component is now captured)
    "LODESTAR": {
        "OU": (1, "provisional", "Coronary revascularisation (PCI/CABG procedure codes) added after the end of the index stay "
                                 "(outcome fix); the dominant component is now ascertained. Index-stay revascularisations are "
                                 "not counted where the trial counted them from randomisation (anchor (iv), share unknown) -> 1 "
                                 "provisional (0 if the share is minor and documented as such).")},
    "PROVE IT-TIMI 22": {
        "OU": (0, "provisional", "Revascularisation >= 30 d after index (PCI/CABG) added, as in the trial definition; every other "
                                 "component (all-cause death, MI, UA rehospitalisation, stroke) was already ascertained -> 0, "
                                 "provisional until the component definitions are checked against Cannon NEJM 2004.")},
}

# si_defects (adjudicated records) removed by the spec-v2 cohort
FIXED = {"COMET": ["COMET-SI-1"], "VALIANT": ["VALIANT-SI-1"], "EMPEROR-Preserved": ["EMPPRES-SI-1", "EMPEROR-P-SI-1"],
         "DECLARE-TIMI 58": ["DECLARE-SI-1"], "CANVAS Program": ["CANVAS-SI-1"], "LEADER": ["LEADER-SI-1"],
         "SUSTAIN-6": ["SUSTAIN6-SI-1"], "REWIND": ["REWIND-SI-1"], "LAAOS III": ["LAAOS3-SI-1"], "LIFE": ["LIFE-SI-1", "LIFE-SI-2"],
         "CAROLINA": ["CAROLINA-SI-1"], "AMPLIFY": ["AMPLIFY-SI-1"], "INSIGHT": ["INSIGHT-SI-1"], "PARADIGM-HF": ["PARADIGM-SI-1-B"],
         "ELITE II": ["ELITE2-SI-1"]}

# uniform numeric-entry-bound rule (step D2): every undocumented numeric entry bound that the data could apply and that the
# spec-v2 cohort applies scores 0 in every item. ENTRY rules of specs_v2 (+ published age bounds). An undocumented bound that
# the data could apply but spec v2 did NOT apply would be scored as the framework says (SI type 4, 1 provisional if the
# share is unknown): NOT_APPLIED lists them (none identified in the spec-v2 rule table or COHORT_FIXES.md).
NOT_APPLIED: dict[str, list[str]] = {}

# DA.a: trials whose population-defining measurement is the echo EF (adjudicated records), plus COMET, whose LVEF <= 35% is
# now applied with unknown values passing. VALIANT keeps its adjudicated DA.a (C10: EF-unknown patients now need an HF code;
# the clarification is the user's), and its smaller arm is now < 500 (DA.b) anyway.
EF_DEFINED = ["AF-CHF", "ELITE II", "PARADIGM-HF", "EMPEROR-Preserved", "COMET"]


def da_rule(rec, B):
    """DA on the spec-v2 cohort: DA.b from DC-DA-size; DA.a from DC-DA-meas for EF-defined trials; else adjudicated DA.a."""
    t = rec["trial"]
    b = B[B.label == t].set_index("cohort")
    v2 = b.loc["v2"]
    dab = int(v2.da_b)
    feats = rec["items"]["DA"].get("features", {})
    if t in EF_DEFINED:
        daa = int(v2.ef_measured_band == "<50%")
        src = f"DC-DA-meas (spec-v2 cohort): echo EF in [index-365, index-1] measured in {v2.ef_measured_pct:.1f}% ({v2.ef_measured_band})"
    else:
        daa = int(bool(feats.get("DA.a"))) if feats else 0
        if t == "VALIANT":
            daa = 1
        src = "DA.a unchanged from the adjudicated record" + (" (C10 for VALIANT)" if t == "VALIANT" else "")
    score = max(daa, dab)
    reason = (f"{src}; DC-DA-size (spec-v2 cohort): smaller arm {v2.smaller_arm_band}, pooled events {v2.events_band} -> DA.b {dab}. "
              f"DA = {score}.")
    return score, "final", reason, {"DA.a": bool(daa), "DA.b": bool(dab)}


def entry_bounds():
    """per trial: specs_v2 entry-type numeric rules and age bound applied (aggregate description only)."""
    sys.path.insert(0, str(ROOT / "scripts/v2_cohorts"))
    import specs_v2 as SV
    import v2common as K
    out = {}
    for n in K.ALL:
        rs = SV.rules(n)
        out[K.NAME[n]] = dict(entry_bounds=[r.rid for r in rs if r.entry], age=[r.rid for r in rs if r.kind == "age"],
                              other_numeric=[r.rid for r in rs if r.kind == "num" and not r.entry],
                              flags=[r.rid for r in rs if r.kind == "flag"], outcome_fix=n in SV.OUTCOME_FIX)
    return out


def score():
    os.umask(0o077)
    AUD.mkdir(parents=True, exist_ok=True)
    Q = json.load(open(FINAL))
    B = pd.read_csv(AUD / "dc_bands.csv")
    EB = entry_bounds()
    assert set(RESCORE) <= {r["trial"] for r in Q["records"]}
    recs, rows = [], []
    for r0 in Q["records"]:
        r = copy.deepcopy(r0)
        t = r["trial"]
        log = []
        for it, (sc, stt, why) in RESCORE.get(t, {}).items():
            old = (r["items"][it]["score"], r["items"][it]["status"])
            r["items"][it].update(score=sc, status=stt)
            r["items"][it]["rescore_v2_cohorts"] = why
            log.append(dict(item=it, old=old[0], old_status=old[1], new=sc, new_status=stt, reason=why))
        sc, stt, why, feats = da_rule(r, B)
        old = (r["items"]["DA"]["score"], r["items"]["DA"]["status"])
        if (sc, stt) != old:
            log.append(dict(item="DA", old=old[0], old_status=old[1], new=sc, new_status=stt, reason=why))
        r["items"]["DA"].update(score=sc, status=stt, features=feats)
        r["items"]["DA"]["rescore_v2_cohorts"] = why
        for it, bounds in ((it, NOT_APPLIED.get(t, [])) for it in ["SI"]):
            if bounds:
                raise SystemExit(f"{t}: unapplied entry bounds {bounds}: score them before running")
        ids = {d["id"] for d in r.get("si_defects") or []}
        assert set(FIXED.get(t, [])) <= ids, (t, FIXED.get(t), ids)
        for d in r.get("si_defects") or []:
            d["fixed_in_spec_v2"] = d["id"] in FIXED.get(t, [])
        s = {k: int(r["items"][k]["score"]) for k in ITEMS}
        si_arm = r["si_reason"] == "arm_assignment_or_time_zero" and s["SI"] == 2
        tier, rule, total, n2 = ADJ.tier(s, bool(r["placebo_proxy"]), si_arm)
        prov = [k for k in ITEMS if r["items"][k]["status"] == "provisional"]
        reach = sorted(ADJ.reachable(s, prov, bool(r["placebo_proxy"]), si_arm, trial=t), key=ADJ.TIERS.index)
        tch = [k for k in prov if len(ADJ.reachable(s, [k], bool(r["placebo_proxy"]), si_arm, trial=t)) > 1]
        r.update(record_type="rescored_v2_cohorts", total=total, n_items_at_2=n2, tier=tier, tier_rule_applied=rule,
                 provisional_items=prov, tiers_reachable_under_provisional=reach, provisional_affects_tier=len(reach) > 1,
                 tier_changing_provisional_items=tch, analysed_set=tier != "Limited",
                 tier_v1_cohorts=r0["tier"], total_v1_cohorts=r0["total"], rescore_log=log, spec_v2=EB[t])
        recs.append(r)
        rows.append(dict(trial=t, tier_v1=r0["tier"], total_v1=r0["total"], tier_v2=tier, total_v2=total, rule=rule,
                         changed="; ".join(f"{x['item']} {x['old']}->{x['new']}{'p' if x['new_status'] == 'provisional' else ''}" for x in log),
                         provisional=";".join(prov), tier_changing=";".join(tch), reachable=";".join(reach),
                         **{k: r["items"][k]["score"] for k in ITEMS}))
    T = pd.DataFrame(rows)
    T.to_csv(AUD / "tiers_v2cohorts.csv", index=False)
    new = sorted(T[T.tier_v2 != "Limited"].trial)
    p29 = sorted(Q["analysed_set"])
    v19 = ADJ.v19_tiers()
    key = {r["trial"]: r["spec_key"] for r in recs}
    p32 = sorted(t for t in T.trial if v19[key[t]] != "Limited")
    meta = dict(
        title="TRACE-ECG emulation quality v2.0: rescored on the spec-v2 fixed cohorts (38 trials)",
        framework="docs/emulation_quality_v2/QUALITY_FRAMEWORK.md (v2.0 draft; tier rules unchanged)",
        base_record="docs/emulation_quality_v2/quality_v2_final.json (adjudicated, version 1 cohorts)",
        cohort_fixes=DOC, spec_v2_rules=SPEC, data_checks="scripts/emulation_quality_v2/dc_v2_cohorts.py (bands only)",
        script="scripts/emulation_quality_v2/rescore_v2_cohorts.py", date="2026-10-08",
        rater="Claude Opus 5.5 (claude-opus-5-5) queue agent, 2026-10-08; not a clinician; every changed item needs clinician review",
        status="rescored; NOT frozen (framework 7.6): provisional scores, open clarifications C1-C10 and the user decisions listed "
               "in RESCORE_V2_COHORTS.md remain",
        uniform_rule="An undocumented numeric entry bound that the data could apply and that the spec-v2 cohort applies scores 0 "
                     "(any item); one not applied scores as the framework says (SI type 4). None unapplied identified.",
        tier_counts={k: int((T.tier_v2 == k).sum()) for k in ADJ.TIERS}, analysed_set=new,
        excellent_good=sorted(T[T.tier_v2.isin(["Excellent", "Good"])].trial),
        no_tier_changing_provisional=sorted(T[(T.tier_v2 != "Limited") & (T.tier_changing == "")].trial),
        vs_provisional_29=dict(entering=sorted(set(new) - set(p29)), leaving=sorted(set(p29) - set(new))),
        vs_paper1_32=dict(entering=sorted(set(new) - set(p32)), leaving=sorted(set(p32) - set(new))),
        records=recs)
    txt = json.dumps(meta, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    OUTJ.write_text(txt)
    h = hashlib.sha256(OUTJ.read_bytes()).hexdigest()
    (AUD / "json_sha256.txt").write_text(f"{h}  {OUTJ.name}  (written before any impact run)\n")
    pd.set_option("display.width", 250)
    print(T[["trial", "tier_v1", "total_v1", "tier_v2", "total_v2", "changed", "provisional", "tier_changing", "reachable"]].to_string(index=False))
    print(meta["tier_counts"], len(new), "vs 29:", meta["vs_provisional_29"], "vs 32:", meta["vs_paper1_32"])
    print("sha256", h)


# ------------------------------------------------------------------------------------------------ impact (after scoring)
def impact():
    os.umask(0o077)
    sys.path.insert(0, str(ROOT / "scripts/v2_cohorts"))
    import v2common as K
    P2, SP = K.P2, K.SP
    Q = json.load(open(OUTJ))
    h = hashlib.sha256(OUTJ.read_bytes()).hexdigest()
    assert (AUD / "json_sha256.txt").read_text().split()[0] == h, "quality_v2_cohorts.json changed after scoring"
    nm = K.LABEL_NAME
    tier = {nm[r["trial"]]: r["tier"] for r in Q["records"]}
    sets = {"new set (rescored, spec-v2)": [n for n in K.ALL if tier[n] != "Limited"],
            "Excellent + Good (rescored)": [n for n in K.ALL if tier[n] in ("Excellent", "Good")],
            "all 38": list(K.S38), "paper 1's 32": list(K.S32), "provisional 29 (v2.0 adjudication)": list(K.S29)}
    # sensitivity: SI/EL-only rescore (no OU re-score after the LODESTAR / PROVE IT outcome rebuilds: both stay Moderate)
    sets["Excellent + Good, no OU re-score"] = [n for n in sets["Excellent + Good (rescored)"] if n not in ("lodestar", "prove-it")]
    CL = K.V.cluster_of()

    def run(R, trials):
        g = {}
        for a in ("base", "ECG"):
            x = R[(R.rung == "P5") & (R.config == "main") & (R.arm == a)].set_index("trial", drop=False).loc[K.ALL]
            F, S = SP.per_trial(x)
            f = (x.cell_failed.fillna("").astype(str).ne("") | (x.n_pairs.notna() & (x.n_pairs < K.MIN_CELL))).to_numpy()
            S.loc[f, :] = np.nan
            F.loc[f, ["lt01", "m58", "absd", "cons", "ea", "loghr", "se"]] = np.nan
            g[a] = (F, P2.mask(S, K.NONCODED))  # P5 masks nothing on the 54 items (pipeline.md section 6)
        return SP.contrast_row(g["ECG"][0], g["base"][0], trials, "one", CL, g["ECG"][1], g["base"][1])

    # gate (a): version 1 cells, paper 1's 32 -> paper 2 published 8.8% (4.4-13.3)
    c = run(pd.read_parquet(K.REF_V21), list(K.S32))
    gate_a = round(c["relred"], 1) == 8.8 and round(c["relred_lo"], 1) == 4.4 and round(c["relred_hi"], 1) == 13.3
    R2 = pd.read_parquet(K.CEL / "restricted_cells_v2_all.parquet")
    rows = []
    for lab, tr in sets.items():
        c = run(R2, tr)
        rows.append(dict(set=lab, n_trials=len(tr), relred54=c["relred"], lo=c["relred_lo"], hi=c["relred_hi"], m54_base=c["m58_b"],
                         m54_ecg=c["m58_a"], m54_better=c["m58_better"], m54_p=c["m58_p"], lt01_base=c["lt01_b"], lt01_ecg=c["lt01_a"],
                         lt01_better=c["lt01_better"], lt01_p=c["lt01_p"], absd_base=c["absd_b"], absd_ecg=c["absd_a"],
                         absd_better=c["absd_better"], absd_p=c["absd_p"], bshuf_p=c["bshuf_p"]))
    D = pd.DataFrame(rows)
    # gate (b): provisional 29 on spec-v2 cells == scripts/v2_psclin_mi summary row 'P5: ECG vs base' (S29, main)
    M = pd.read_csv(K.A / "claude-v2-psclin-mi/summary/contrasts.csv")
    m = M[(M.set == "S29") & (M.config == "main") & (M.contrast == "P5: ECG vs base")].iloc[0]
    d = D[D.set.str.startswith("provisional 29")].iloc[0]
    dev = max(abs(d.relred54 - m.relred54), abs(d.lo - m.relred54_lo), abs(d.hi - m.relred54_hi), abs(d.m54_p - m.m54_p),
              abs(d.absd_p - m.absd_p), abs(d.bshuf_p - m.bshuf_p), abs(d.lt01_p - m.lt01_54_p))
    gate_b = dev < 1e-12 and d.m54_better == m.m54_better
    D["gate_a_v1_32_paper2"] = gate_a
    D["gate_b_v2_29_vs_psclin_mi_summary_maxdev"] = dev
    D.to_csv(AUD / "impact_v2cohorts.csv", index=False)
    pd.set_option("display.width", 250)
    print(D.round(4).to_string(index=False))
    print("GATE a (v1 S32 = 8.8 (4.4-13.3)):", "PASS" if gate_a else "FAIL", "| GATE b (S29 vs psclin_mi summary):",
          "PASS" if gate_b else "FAIL", dev)
    if not (gate_a and gate_b):
        raise SystemExit("impact gate failed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["score", "impact"])
    a = ap.parse_args()
    {"score": score, "impact": impact}[a.cmd]()
