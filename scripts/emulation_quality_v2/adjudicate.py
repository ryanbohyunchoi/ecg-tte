#!/usr/bin/env python
"""Adjudication of the two independent emulation-quality v2.0 ratings (38 TRACE-ECG trial emulations).

Framework: docs/emulation_quality_v2/QUALITY_FRAMEWORK.md (v2.0 draft, section 11 defaults).
Inputs (read-only): /mnt/raid0/rbc58/ecg-tte/audits/claude-eq2/scores_{A,B}.json.

Steps (one subcommand each; `all` runs 1-3, `impact` runs 4):
  agreement  inter-rater agreement on the unadjudicated ratings: % exact agreement, Cohen's kappa (0-1 items, features,
             placebo proxy, analysed-set membership), linear-weighted kappa (0-2 items, 4-level tier) and unweighted tier
             kappa, ICC(2,1) absolute agreement for the total; 95% percentile bootstrap CIs over trials (2,000 resamples).
             Rater tiers are recomputed mechanically from the rater item scores (section 6) and checked against the
             tiers the raters reported.
  adjudicate every item-level disagreement resolved by the DECISIONS table below (deciding clause, whether the
             section 7.4.3 more-severe default was used, clarification id); totals and tiers computed mechanically.
  alt        tiers under each pending v2.0.1 clarification (alternative readings), and tiers reachable by moving
             provisional items by +/-1 (all combinations).
  impact     paper 1 primary analysis (PS-Demo P1 base vs P1 + 32 ECG PCs, main config) on the published cells
             (audits/claude-v20-sens-primary32/restricted_cells.parquet) for: published 32; new analysed set; new
             Excellent+Good; all 38. Uses scripts/v20/sens_primary32.contrast_row unchanged. Needs the analysis env
             (/mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python). Gate: published 32 must reproduce 11.4%
             (6.3-16.0), 22/32, P = .002, |dlogHR| 0.251 -> 0.205, P = .008.

Results are never used by the adjudication (framework section 1.1): `impact` runs only after quality_v2_final.json is
written, and nothing in DECISIONS reads it.

Outputs:
  docs/emulation_quality_v2/quality_v2_final.json                (repo; scores, evidence citations, bands only)
  /mnt/raid0/rbc58/ecg-tte/audits/claude-eq2/agreement.csv, disagreements.csv, tiers.csv, alt_tiers.csv,
  provisional_reach.csv, impact.csv                                (aggregate; umask 077)
No patient-level data are read except by `impact` (published restricted cells, aggregate per-trial outputs only).
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-eq2")
FINAL = ROOT / "docs/emulation_quality_v2/quality_v2_final.json"
V19 = ROOT / "docs/v19/quality_tiers.json"
ITEMS = ["EL", "TZ", "TS", "CO", "OU", "FU", "ES", "BM", "DA", "SI"]
MAXP = {"EL": 2, "TZ": 2, "TS": 2, "CO": 2, "OU": 2, "FU": 1, "ES": 1, "BM": 1, "DA": 1, "SI": 2}
TIERS = ["Excellent", "Good", "Moderate", "Limited"]
NBOOT, BSEED = 2000, 20261008
SHA = "7fff3d9"


# ----------------------------------------------------------------------------- tier rules (framework section 6)
def tier(items: dict, pp: bool, si_arm: bool):
    s = {k: int(items[k]) for k in ITEMS}
    total = sum(s.values())
    n2 = sum(v == 2 for v in s.values())
    lim = []
    if total >= 8:
        lim.append("total >= 8")
    if n2 >= 2:
        lim.append("N2 >= 2")
    if pp and total - s["CO"] >= 3:
        lim.append("PP and other points >= 3")
    if s["SI"] == 2 and si_arm:
        lim.append("SI = 2 arm-assignment/time-zero error")
    if lim:
        return "Limited", "; ".join(lim), total, n2
    if 5 <= total <= 7 or n2 == 1:
        return "Moderate", "; ".join(r for r, c in (("5 <= total <= 7", 5 <= total <= 7), ("N2 = 1 cap", n2 == 1)) if c), total, n2
    if 3 <= total <= 4:
        return "Good", "3 <= total <= 4, N2 = 0", total, n2
    return "Excellent", "0 <= total <= 2, N2 = 0", total, n2


def load_raters():
    A = json.load(open(AUD / "scores_A.json"))
    B = json.load(open(AUD / "scores_B.json"))
    return A, B


def scores(rec):
    return {k: int(rec["items"][k]["score"]) for k in ITEMS}


def rater_tier(rec):
    return tier(scores(rec), bool(rec["placebo_proxy"]), rec.get("si_reason") == "arm_assignment_or_time_zero")


# ----------------------------------------------------------------------------- agreement statistics
def kappa(a, b, cats, weights=None):
    a, b = np.asarray(a), np.asarray(b)
    k = len(cats)
    idx = {c: i for i, c in enumerate(cats)}
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        O[idx[x], idx[y]] += 1
    O /= O.sum()
    Ex = np.outer(O.sum(1), O.sum(0))
    i, j = np.indices((k, k))
    W = np.abs(i - j) / (k - 1) if weights == "linear" else (i != j).astype(float)
    de = (W * Ex).sum()
    return np.nan if de == 0 else 1 - (W * O).sum() / de


def icc21(x, y):
    """ICC(2,1), two-way random effects, absolute agreement, single rater (Shrout & Fleiss)."""
    Y = np.column_stack([x, y]).astype(float)
    n, k = Y.shape
    gm = Y.mean()
    msr = k * ((Y.mean(1) - gm) ** 2).sum() / (n - 1)
    msc = n * ((Y.mean(0) - gm) ** 2).sum() / (k - 1)
    sse = ((Y - Y.mean(1, keepdims=True) - Y.mean(0, keepdims=True) + gm) ** 2).sum()
    mse = sse / ((n - 1) * (k - 1))
    de = msr + (k - 1) * mse + k * (msc - mse) / n
    return np.nan if de == 0 else (msr - mse) / de


def boot(stat, a, b, rng):
    n = len(a)
    out = []
    for _ in range(NBOOT):
        I = rng.integers(0, n, n)
        out.append(stat(a[I], b[I]))
    out = np.array(out, float)
    if np.isfinite(out).sum() < 0.5 * NBOOT:
        return np.nan, np.nan
    return tuple(np.nanpercentile(out, [2.5, 97.5]))


def agreement(A, B):
    ra = {r["trial"]: r for r in A["records"]}
    rb = {r["trial"]: r for r in B["records"]}
    trials = list(ra)
    rng = np.random.default_rng(BSEED)
    rows = []

    def add(name, kind, a, b, cats, weights):
        a, b = np.asarray(a), np.asarray(b)
        st = lambda x, y: kappa(x, y, cats, weights)
        k = st(a, b)
        lo, hi = boot(st, a, b, rng)
        prev = np.mean(np.concatenate([a, b]) != cats[0])
        rows.append(dict(element=name, kind=kind, statistic=f"{'linear-weighted ' if weights == 'linear' else ''}kappa",
                         pct_agree=100 * np.mean(a == b), kappa=k, lo=lo, hi=hi,
                         prevalence_nonzero_pct=100 * prev, n_disagree=int((a != b).sum())))

    for it in ITEMS:
        a = [ra[t]["items"][it]["score"] for t in trials]
        b = [rb[t]["items"][it]["score"] for t in trials]
        add(it, f"item 0-{MAXP[it]}", a, b, list(range(MAXP[it] + 1)), "linear" if MAXP[it] == 2 else None)
    feats = [f for it in ITEMS for f in (ra[trials[0]]["items"][it].get("features") or {})]
    for f in feats:
        it = f.split(".")[0]
        a = [int(bool(ra[t]["items"][it]["features"][f])) for t in trials]
        b = [int(bool(rb[t]["items"][it]["features"][f])) for t in trials]
        add(f, "feature", a, b, [0, 1], None)
    add("placebo_proxy", "flag", [int(ra[t]["placebo_proxy"]) for t in trials], [int(rb[t]["placebo_proxy"]) for t in trials], [0, 1], None)
    ta = [rater_tier(ra[t])[0] for t in trials]
    tb = [rater_tier(rb[t])[0] for t in trials]
    add("tier (4-level)", "tier", [TIERS.index(x) for x in ta], [TIERS.index(x) for x in tb], [0, 1, 2, 3], "linear")
    add("tier (4-level), unweighted", "tier", [TIERS.index(x) for x in ta], [TIERS.index(x) for x in tb], [0, 1, 2, 3], None)
    add("analysed set (Exc+Good+Mod)", "membership", [int(x != "Limited") for x in ta], [int(x != "Limited") for x in tb], [0, 1], None)
    tot_a = np.array([sum(scores(ra[t]).values()) for t in trials])
    tot_b = np.array([sum(scores(rb[t]).values()) for t in trials])
    lo, hi = boot(icc21, tot_a, tot_b, rng)
    rows.append(dict(element="total (0-16)", kind="total", statistic="ICC(2,1) absolute agreement", pct_agree=100 * np.mean(tot_a == tot_b),
                     kappa=icc21(tot_a, tot_b), lo=lo, hi=hi, prevalence_nonzero_pct=np.nan, n_disagree=int((tot_a != tot_b).sum())))
    # reported vs mechanical tiers
    chk = []
    for lab, R in (("A", ra), ("B", rb)):
        for t in trials:
            m = rater_tier(R[t])
            chk.append(dict(rater=lab, trial=t, reported=R[t]["tier"], mechanical=m[0], total_reported=R[t]["total"], total_mech=m[2]))
    chk = pd.DataFrame(chk)
    dis = []
    for t in trials:
        for it in ITEMS:
            a, b = ra[t]["items"][it], rb[t]["items"][it]
            if a["score"] != b["score"]:
                dis.append(dict(trial=t, item=it, rater_A=a["score"], status_A=a["status"], rater_B=b["score"], status_B=b["status"]))
    return pd.DataFrame(rows), pd.DataFrame(dis), chk, (tot_a.mean(), tot_b.mean(), np.mean(np.abs(tot_a - tot_b)))


# ----------------------------------------------------------------------------- adjudication decisions
# Clarification ids (docs/emulation_quality_v2/ADJUDICATION.md, "Framework clarifications needed (v2.0.1)"):
#   C1 undocumented omitted/approximated code-defined population criterion: EL vs SI allocation and weight
#   C2 TZ.c share denominator when only one arm stops baseline therapy (ACTIVE W)
#   C3 any-position HF hospitalisation codes in HF-prevalent cohorts as an SI type-6 defect
#   C4 combining SI defects on different denominators (patients vs events)
#   C5 CABANA TZ.d (documented prior-AAD allowance) and SI type 7 (dedupe): one deviation or two
#   C6 new-user restriction excluding an experienced subgroup: does it stack with a second EL criterion (ROCKET-AF, RE-LY)
#   C7 ES.b "specific mechanism documented": secular warfarin -> DOAC replacement without DC-ES-cross
#   C8 >=90%-met rule by clinical reasoning when the trial's risk list is narrower than the framework example (RE-LY)
#   C9 materiality of omitted non-population-defining exclusions (PROTECT AF warfarin eligibility; AMPLIFY cancer)
#   C10 DA.a "applies by design" when EF-unknown patients must carry a phenotype code (EMPEROR-Preserved)
TEXT = "text decides"
DEF = "section 7.4.3 default: more severe score stands"

E = lambda typ, ref, note="": dict(type=typ, ref=ref, note=note)
EV_NTPROBNP = E("DOC", "docs/DATA_SOURCES.md L21 (OMOP gold measurement: NT-proBNP, 558K rows)", "NP is measurable, so an omitted NP bound is correctable (type 4)")
EV_ALLOC = E("DOC", "docs/emulation_quality_v2/QUALITY_FRAMEWORK.md section 1.4, section 5 row 1, EL 'scored elsewhere', SI types 4-5", "allocation text")

C1_EL = ("allocation dispute (A: EL, B: SI) for an undocumented, code-defined population criterion. Section 5 row 1 routes "
         "undocumented omissions to SI 'type 4-5', but types 4-5 enumerate numeric bounds and gate mechanics, not wholesale "
         "omission of a criterion, and the EL level-1 anchors list 'risk enrichment not applied' by type; the text does not "
         "settle the allocation or its weight (C1). Default: more severe stands, scored once (section 1.3), applied uniformly "
         "to all 38 trials; at current evidence the EL allocation is never less severe, so the deviation is scored in EL and "
         "the SI point that rater B gave for the same deviation is removed.")
C1_SI0 = "same deviation scored in EL (C1); score once (section 1.3), so rater B's SI point for it is removed; no other undocumented defect found by either rater."
C7_ES = ("ES unknown rule: 'score ES.b 0 unless a specific mechanism is documented (e.g. secular replacement of the comparator by "
         "the intervention during the study period); in that case 1 provisional'. Rater A cites exactly that mechanism (warfarin -> "
         "DOAC replacement over the index window); rater B read 'documented' as documented in the project sources with a share. "
         "The text does not say where the mechanism must be documented (C7). Default: more severe (1 provisional). Resolve with DC-ES-cross.")

DECISIONS = {
    "ARISTOTLE": [dict(item="ES", score=1, status="provisional", stand="A", clause=DEF, clar="C7", reason=C7_ES)],
    "ROCKET-AF": [
        dict(item="EL", score=2, status="final", stand="A", clause=DEF, clar="C1,C6",
             reason=C1_EL + " ROCKET-AF: CHADS2 >= 2 (undocumented; not plausibly met by >= 90% of AF OAC initiators) plus the new-user "
             "exclusion of the ~62% VKA-experienced (EL anchor type) = two criteria -> 2. Whether the experienced-subgroup point stacks "
             "with a second criterion is C6."),
        dict(item="ES", score=1, status="provisional", stand="A", clause=DEF, clar="C7", reason=C7_ES),
        dict(item="SI", score=0, status="final", stand="A", clause=DEF, clar="C1", reason=C1_SI0, drop_B=["ROCKET-SI-1"])],
    "RE-LY": [
        dict(item="EL", score=2, status="provisional", stand="A", clause=DEF, clar="C1,C6,C8",
             reason="RE-LY risk list (Connolly NEJM 2009 Methods: prior stroke/TIA, LVEF < 40%, NYHA >= II HF within 6 mo, age >= 75, or "
             "65-74 with diabetes, hypertension or CAD) is narrower than the framework's '>=1 stroke risk factor' example: under 65 only "
             "stroke/TIA, EF < 40 or HF qualify. Rater B applied the example; rater A showed the example does not fit this list. The "
             ">=90%-met rule is not established without DC-EL-met (C8), so the EL unknown rule (1 provisional for this criterion) applies; "
             "with the new-user exclusion of ~50% VKA-experienced, two criteria -> 2 provisional. Undocumented code-defined criterion: "
             "allocation per C1 (EL). Stacking: C6."),
        dict(item="ES", score=1, status="provisional", stand="A", clause=DEF, clar="C7",
             reason=C7_ES + " The mechanism is weakest here (dabigatran was not the main DOAC replacing warfarin).")],
    "EAST-AFNET 4": [
        dict(item="EL", score=1, status="provisional", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " EAST-AFNET 4 CV-risk criterion (age > 75, prior stroke/TIA, or two risk conditions; Kirchhof NEJM 2020), "
             "undocumented; impact unknown -> 1 provisional."),
        dict(item="SI", score=1, status="provisional", stand="A", clause=DEF, clar="C3",
             reason="Both raters scored SI 1 provisional but for different defects. B's (CV-risk omission) moves to EL (C1). A's: the HF "
             "component counts I50 in any position on any later stay (extract_outcomes.py L75-85), so in AF patients with prior HF the "
             "chronic code can turn unrelated admissions into HF events (persisting-code mechanism, SI type 6). The framework names "
             "only AMPLIFY; whether chronic-code persistence in HF-prevalent cohorts is an SI defect is C3. Default: more severe "
             "(1 provisional, share of events unchecked).", drop_B=["EAST-SI-1"])],
    "CABANA": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " CABANA: age >= 65, or < 65 with >= 1 stroke risk factor (Packer JAMA 2019), undocumented. (SI is 2 either way.)",
             drop_B=["CABANA-SI-2", "CABANA-SI-3"],
             note="B's CABANA-SI-2 (disabling-stroke footnote) is a documentation error, not a code defect: eTable 1 says 'disabling' "
                  "is not identifiable and the code uses any stroke, consistent with OU 1; the paper Table 1 note should be corrected.")],
    "FRAIL-AF": [dict(item="ES", score=1, status="provisional", stand="A", clause=DEF, clar="C7", reason=C7_ES)],
    "PROTECT AF": [
        dict(item="EL", score=2, status="provisional", stand="A", clause=DEF, clar="C9,C1",
             reason="Agreed: CHADS2 risk factor by code with the age >= 75 route not applied (documented; EL anchor). Disputed: the trial "
             "required eligibility for long-term warfarin (Holmes Lancet 2009), while US percutaneous LAAO (2015+) is indicated for "
             "patients seeking a non-pharmacological alternative to warfarin, typically because of bleeding risk; the emulation does not "
             "exclude prior bleeding. EL text: safety exclusions are scored 'only if their omission plausibly changes the population "
             "materially'; rater A gives a specific mechanism, rater B is silent. The text leaves the materiality judgement open (C9); "
             "default: more severe (2 provisional). Undocumented code-defined criterion: allocation per C1 (EL).")],
    "ACTIVE W": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " ACTIVE W: age >= 75 alone and age 55-74 with CAD routes not applied (Lancet 2006 Methods), undocumented."),
        dict(item="TZ", score=2, status="provisional", stand="A", clause=DEF, clar="C2",
             reason="TZ.c present by both raters (77% on OAC at entry; clopidogrel+aspirin arm stopped it at randomisation; ACTIVE "
             "Writing Group Lancet 2006 Table 1; eTable 1). The >= 50% escalation turns on the denominator: 77% on the drug (A) or ~38% "
             "actually switched (B). The text ('>=30% of randomised patients were on a same-purpose drug that was stopped or replaced at "
             "randomisation'; '>=50% of randomised patients switched') supports both readings (C2). Default: more severe (2), provisional "
             "until C2 is settled."),
        dict(item="SI", score=0, status="final", stand="A", clause=DEF, clar="C1", reason=C1_SI0, drop_B=["ACTIVEW-SI-1"])],
    "COMET": [
        dict(item="SI", score=1, status="final", stand="A", clause=TEXT, clar=None,
             reason="Section 5 row 'same-class agent not washed out': documented -> n/a, undocumented -> SI type 2. COMET excluded current "
             "beta-blocker users (Poole-Wilson Lancet 2003). docs/COMET_ADAPTED_PROTOCOL.md 'Prior beta-blockers' defers the washout "
             "('neither 365 days nor the original trial's two-week rule is adopted automatically'), so no-washout is not stated as a "
             "deliberate choice (section 1.4). Data: succinate-named orders in [index-365, index] 5-20% of analysed patients "
             "(criteria_counts.csv comet jdat_succ_w365_incl_index). SI 1. EL stays 2 on the other criteria (both raters: LVEF <= 35% "
             "replaced by 'HF code or EF < 40', and prior CV admission / NYHA / background therapy not required), so nothing is double "
             "counted. Note: TRIAL_CRITERIA_CHECK.md says the protocol 'deliberately adopted no washout'; the protocol text says otherwise.",
             extra_ev=[E("DOC", "docs/COMET_ADAPTED_PROTOCOL.md L23 'Prior beta-blockers'", "washout not chosen")])],
    "PARADIGM-HF": [
        dict(item="EL", score=0, status="final", stand="B", clause=TEXT, clar=None,
             reason="Rater A's only EL point is the natriuretic-peptide threshold (BNP >= 150 / NT-proBNP >= 600; McMurray NEJM 2014), "
             "scored as 'not available'. NT-proBNP is in OMOP gold (docs/DATA_SOURCES.md), so the omission is an undocumented, "
             "correctable numeric bound: EL 'scored elsewhere' and SI type 4 (text decides). EL 0; the deviation is carried in SI.",
             extra_ev=[EV_NTPROBNP, EV_ALLOC]),
        dict(item="SI", score=1, status="provisional", stand="both", clause=DEF, clar="C3,C4",
             reason="Union of two undocumented defects of unknown share: NP threshold omitted (patients; type 4, B) and any-position I50 "
             "for HF hospitalisation in an HF-gated cohort (events; type 6, A; C3). SI unknown rule -> 1 provisional; combining "
             "denominators is C4.")],
    "TRANSFORM-HF": [
        dict(item="EL", score=1, status="final", stand="A", clause=TEXT, clar=None,
             reason="eTable 1 design notes state the gate ('initiators within 30 d of an HF code ...'), so the approximation of the index "
             "HF hospitalisation by any I50 code within 30 d is a documented adaptation (section 1.4) -> EL. The Table 1/eTable 1 "
             "population label 'HF hospitalisation (discharge within 30 d)' contradicts the code and should be corrected (data: <5% "
             "of index orders fall within 30 d after a discharge; criteria_counts.csv).",
             extra_ev=[E("DOC", "docs/paper/supplement.md eTable 1 TRANSFORM-HF design note", "gate documented")]),
        dict(item="SI", score=0, status="final", stand="A", clause=TEXT, clar=None,
             reason="The gate deviation is documented (EL); the in-hospital time zero and switcher exclusion are documented (TZ = 2). "
             "No undocumented defect remains.", drop_B=["TRANSFORM-SI-1"])],
    "EMPEROR-Preserved": [
        dict(item="EL", score=2, status="provisional", stand="A", clause=DEF, clar="C1",
             reason="(1) T2D restriction (documented; ~49% diabetic in Anker NEJM 2021) -> EL, agreed. (2) NT-proBNP threshold: measurable "
             "(docs/DATA_SOURCES.md), undocumented numeric bound -> SI type 4 (text decides; rater B's allocation). (3) Rater A also cites "
             "the requirement of structural heart disease or a recent HF hospitalisation (Anker 2021 Methods), not applied and undocumented; "
             "rater B is silent. Code-defined criterion -> EL per C1. Two EL criteria -> 2, provisional until (3) is verified against the "
             "publication. The tier is Limited with EL 1 or 2.", extra_ev=[EV_NTPROBNP]),
        dict(item="DA", score=1, status="provisional", stand="B", clause=TEXT, clar="C10",
             reason="DA unknown rule: 'if a data check is not run, score 1 provisional only when DA.a applies by design (an EF-defined "
             "trial)'. EMPEROR-Preserved is EF-defined (LVEF > 40%), and DC-DA-meas was not run. Rater A argued that EF-unknown patients "
             "must carry an I503 code, so they do not pass freely; the parenthetical decides, and C10 asks whether it should."),
        dict(item="SI", score=1, status="provisional", stand="both", clause=DEF, clar="C3,C4",
             reason="Union: saxagliptin/alogliptin in the DPP-4i comparator (<5% of patients; data), NT-proBNP bound omitted (patients, "
             "unknown; B), any-position I50 in an HF-gated cohort (events, unknown; A; C3). SI unknown rule -> 1 provisional.",
             drop_B=["EMPEROR-P-SI-2"])],
    "LIFE": [
        dict(item="EL", score=0, status="final", stand="B", clause=TEXT, clar=None,
             reason="Rater A's EL point is the blood-pressure entry range (sitting 160-200 / 95-115 mm Hg after placebo run-in; Dahlof "
             "Lancet 2002). That is a numeric bound stated in the protocol, absent from the spec and undocumented: EL 'scored elsewhere' "
             "('an undocumented missing numeric bound ... -> SI') and SI type 4 (text decides). EL 0; SI is already 2, so the bound adds "
             "no point (see framework-design issue D2).", extra_ev=[EV_ALLOC], add_si=[dict(
                 id="LIFE-SI-2", description="Blood-pressure entry range (SBP 160-200 / DBP 95-115 after placebo run-in) not applied, undocumented",
                 type="4", documented=False, denominator="analysed_patients", share_band="unknown",
                 arm_assignment_or_time_zero_unfixable_by_exclusion=False, data_check_id="DC-SI-life-bp (not run)",
                 evidence=[E("PUB", "Dahlof et al. Lancet 2002;359:995-1003, Methods")],
                 proposed_spec_edit="life_adapted_v3: latest pre-index SBP/DBP in the trial range, or document as adaptation")])],
    "ALLHAT": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " ALLHAT: >= 1 additional CHD risk factor (ALLHAT Officers JAMA 2002), undocumented."),
        dict(item="SI", score=0, status="final", stand="A", clause=DEF, clar="C1", reason=C1_SI0, drop_B=["ALLHAT-SI-1"])],
    "VALUE": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " VALUE: high-CV-risk requirement (Julius Lancet 2004), undocumented."),
        dict(item="SI", score=0, status="final", stand="A", clause=DEF, clar="C1", reason=C1_SI0, drop_B=["VALUE-SI-1"])],
    "ASCOT-BPLA": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " ASCOT-BPLA: >= 3 additional CV risk factors (Dahlof Lancet 2005), undocumented."),
        dict(item="SI", score=0, status="final", stand="A", clause=DEF, clar="C1", reason=C1_SI0, drop_B=["ASCOT-SI-1"])],
    "INSIGHT": [
        dict(item="EL", score=0, status="final", stand="B", clause=TEXT, clar=None,
             reason="Rater A's EL point is the blood-pressure entry threshold (>= 150/95 or SBP >= 160 mm Hg; Brown Lancet 2000): an "
             "undocumented numeric bound -> SI type 4 (text decides). The risk-factor routes are documented in the spec note (B).",
             extra_ev=[EV_ALLOC]),
        dict(item="SI", score=1, status="provisional", stand="adjudicator", clause=TEXT, clar=None, agreed_override=True,
             reason="Consequential re-allocation of the BP bound identified by rater A (both raters had SI 0): undocumented numeric bound, "
             "share not checked -> SI unknown rule, 1 provisional. Total unchanged from rater A (6).", add_si=[dict(
                 id="INSIGHT-SI-1", description="Blood-pressure entry threshold (>= 150/95 or SBP >= 160 after placebo run-in) not applied, undocumented",
                 type="4", documented=False, denominator="analysed_patients", share_band="unknown",
                 arm_assignment_or_time_zero_unfixable_by_exclusion=False, data_check_id="DC-SI-insight-bp (not run)",
                 evidence=[E("PUB", "Brown et al. Lancet 2000;356:366-72, Methods"), E("SPEC", f"scripts/trial_specs.py:L760-769 @{SHA}, insight, insight_adapted_v1")],
                 proposed_spec_edit="insight_adapted_v2: latest pre-index BP threshold, or document as adaptation")])],
    "VALIANT": [
        dict(item="TZ", score=1, status="provisional", stand="A", clause=TEXT, clar=None,
             reason="TZ.c: ACEi/ARB were permitted up to 12 h before randomisation and stopped at randomisation (Pfeffer NEJM 2003 Methods; "
             "both raters). Share: about 40% on ACEi at randomisation (secondary summary of the trial; rater A from recall), i.e. "
             ">= 30% and < 50% -> TZ.c present, TZ 1 (text decides once the share is known; the framework lists VALIANT as a TZ.c example). "
             "Rater B scored 0 only because the share was not found. Provisional until the Pfeffer 2003 Table 1 figure is transcribed.",
             extra_ev=[E("PUB", "Pfeffer et al. NEJM 2003;349:1893-906, Methods and Table 1 (ACEi before randomisation; verify)")])],
    "SUSTAIN-6": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " SUSTAIN-6: the age >= 60 risk-factor stratum is not applied; unlike LEADER, not stated in the spec note or "
             "eTable 1, so the literal reading puts it in SI (rater B). Default -> EL, as for LEADER.",
             drop_B=["SUSTAIN6-SI-2", "SUSTAIN6-SI-3"])],
    "DECLARE-TIMI 58": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " DECLARE: established ASCVD or multiple risk factors (Wiviott NEJM 2019), undocumented.",
             drop_B=["DECLARE-SI-1", "DECLARE-SI-2"])],
    "CANVAS Program": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " CANVAS: symptomatic ASCVD (age >= 30) or >= 2 risk factors (age >= 50) (Neal NEJM 2017), undocumented.",
             drop_B=["CANVAS-SI-1", "CANVAS-SI-2"],
             si_status="final", si_note="SI 1 agreed; rater B's provisional status came from the risk-criterion omission, now in EL; "
             "the remaining defect (other SGLT2i not washed out) has a known band (5-20%), so SI 1 final.")],
    "ONTARGET": [
        dict(item="EL", score=1, status="final", stand="A", clause=DEF, clar="C1",
             reason=C1_EL + " ONTARGET: 'high-risk diabetes with end-organ damage' approximated by any E11 code, undocumented."),
        dict(item="SI", score=0, status="final", stand="A", clause=DEF, clar="C1", reason=C1_SI0, drop_B=["ONTARGET-SI-1"])],
    "PRECISION": [
        dict(item="SI", score=1, status="provisional", stand="B", clause=DEF, clar="C1",
             reason="Rater B: the CV-risk gate accepts any one of CVD, E11, E78 or hypertension codes (trial_specs.py L810-822), broader "
             "than the trial's 'established CVD or increased CV risk' (Nissen NEJM 2016; the definition is in the Supplementary Appendix; "
             "secondary sources describe diabetes or multiple concomitant risk factors). Rater A scored the gate as an accepted proxy "
             "(EL 0) and no SI. The mechanism is verified in code; the trial definition is verified only from secondary sources. Default: "
             "more severe (SI 1 provisional). Both raters had EL 0, so this is not an allocation dispute; under a uniform C1 allocation it "
             "would sit in EL instead (no tier change).",
             extra_ev=[E("PUB", "Nissen et al. NEJM 2016;375:2519-29, Methods (definition in Supplementary Appendix; verify)")])],
    "AMPLIFY": [
        dict(item="EL", score=1, status="provisional", stand="A", clause=DEF, clar="C9",
             reason="Rater A: AMPLIFY excluded patients with cancer in whom long-term LMWH was planned (Agnelli NEJM 2013); the emulation "
             "keeps cancer as a covariate only, and cancer-associated VTE is a materially different routine-care population. Rater B "
             "silent. Materiality of an omitted exclusion is a judgement the text leaves open (C9); default: more severe (1 provisional). "
             "(Tier is Limited either way.)"),
        dict(item="ES", score=1, status="provisional", stand="A", clause=DEF, clar="C7", reason=C7_ES)],
}

# cases where both raters scored the same item but the adjudicated basis changes (no score change unless stated)
BASIS_NOTES = {
    "DECLARE-TIMI 58": ("SI", "SI 1 agreed (both provisional). Basis: other SGLT2i / saxagliptin-alogliptin, union 5-20% of patients (data); plus "
                        "any-position I50 (events, unknown; A; C3). Rater B's risk-criterion SI component moved to EL (C1). Provisional: union could exceed 20%."),
    "SUSTAIN-6": ("SI", "SI 1 agreed (both provisional). Basis: other GLP-1RA not washed out (5-20%; data) plus generic 'semaglutide' token "
                  "admitting oral/obesity formulations contrary to the spec note (unknown). Rater B's age >= 60 stratum component moved to EL (C1)."),
    "CABANA": ("SI", "SI 2 agreed: earliest-index dedupe is an arm-assignment/time-zero error that exclusion cannot fix (Limited until rebuilt). "
                     "TZ.d (documented prior-AAD allowance in the ablation arm) is kept as scored by both raters; whether it double counts the "
                     "dedupe is C5."),
}


def merge_ev(*lists):
    seen, out = set(), []
    for L in lists:
        for e in L or []:
            k = (e.get("type"), e.get("ref"))
            if k not in seen:
                seen.add(k)
                out.append(e)
    return out


def adjudicate(A, B):
    ra = {r["trial"]: r for r in A["records"]}
    rb = {r["trial"]: r for r in B["records"]}
    out = []
    for t in ra:
        a, b = ra[t], rb[t]
        dec = {d["item"]: d for d in DECISIONS.get(t, [])}
        rec = dict(trial=t, area=a["area"], spec_key=a["spec_key"], spec_version=a["spec_version"], code_path=a["code_path"],
                   git_sha=SHA, rater=dict(id="ADJ", kind="llm_agent",
                                           model_or_role="Claude Opus 5.5 (claude-opus-5-5) adjudicator subagent, 2026-10-08; "
                                           "not a clinician: every adjudicated point needs clinician review (framework 7.1, 7.5)"),
                   record_type="adjudicated", date="2026-10-08", items={}, adjudication=[])
        for it in ITEMS:
            ia, ib = a["items"][it], b["items"][it]
            if it in dec:
                d = dec[it]
                src = {"A": [ia], "B": [ib], "both": [ia, ib], "adjudicator": [ia, ib]}[d["stand"]]
                feats = copy.deepcopy((ia if d["stand"] in ("A", "both", "adjudicator") else ib).get("features"))
                item = dict(score=d["score"], status=d["status"], evidence=merge_ev(*[s["evidence"] for s in src], d.get("extra_ev")),
                            rationale=d["reason"])
                if feats is not None:
                    item["features"] = feats
                if True:  # every decision is logged (disagreements and consequential re-allocations)
                    rec["adjudication"].append(dict(item=it, rater_A=ia["score"], rater_B=ib["score"], adjudicated=d["score"],
                                                    status=d["status"], deciding_clause=d["clause"], clarification=d.get("clar"),
                                                    more_severe_default_used=d["clause"] == DEF, standing=d["stand"],
                                                    reason=d["reason"], note=d.get("note", "")))
            else:
                assert ia["score"] == ib["score"], (t, it)
                status = "provisional" if "provisional" in (ia["status"], ib["status"]) else "final"
                rat = ia["rationale"] if ia["rationale"] == ib["rationale"] else f"Agreed ({ia['score']}). A: {ia['rationale']} | B: {ib['rationale']}"
                item = dict(score=ia["score"], status=status, evidence=merge_ev(ia["evidence"], ib["evidence"]), rationale=rat)
                if ia.get("features") is not None:
                    item["features"] = copy.deepcopy(ia["features"])
            rec["items"][it] = item
        # notes on unchanged scores with changed basis
        if t in BASIS_NOTES:
            it, txt = BASIS_NOTES[t]
            rec["items"][it]["rationale"] = txt
        for d in DECISIONS.get(t, []):
            if d.get("si_status"):
                rec["items"]["SI"]["status"] = d["si_status"]
                rec["items"]["SI"]["rationale"] = d["si_note"]
        # SI defects: union of both raters' lists, minus defects re-allocated to EL / duplicates, plus additions
        drop = {x for d in DECISIONS.get(t, []) for x in d.get("drop_B", [])}
        defs = [dict(x, source="A") for x in a["si_defects"]]
        a_ids = {y["id"]: y["type"] for y in a["si_defects"]}
        for x in b["si_defects"]:
            if x["id"] in drop or a_ids.get(x["id"]) == x["type"]:  # re-allocated, or the same defect as rater A's
                continue
            defs.append(dict(x, id=x["id"] + ("-B" if x["id"] in a_ids else ""), source="B"))
        for d in DECISIONS.get(t, []):
            defs += [dict(x, source="adjudicator") for x in d.get("add_si", [])]
        if rec["items"]["SI"]["score"] == 0:
            defs = [x for x in defs if x.get("share_band") == "<5%"]
        rec["si_defects"] = defs
        rec["placebo_proxy"] = bool(a["placebo_proxy"])
        assert a["placebo_proxy"] == b["placebo_proxy"]
        si_arm = rec["items"]["SI"]["score"] == 2 and any(x.get("arm_assignment_or_time_zero_unfixable_by_exclusion") for x in defs)
        rec["si_reason"] = "arm_assignment_or_time_zero" if si_arm else ("share" if rec["items"]["SI"]["score"] > 0 else "none")
        sc = {k: rec["items"][k]["score"] for k in ITEMS}
        tr, rule, total, n2 = tier(sc, rec["placebo_proxy"], si_arm)
        rec.update(total=total, n_items_at_2=n2, tier=tr, tier_rule_applied=rule,
                   provisional_items=[k for k in ITEMS if rec["items"][k]["status"] == "provisional"])
        reach = reachable(sc, rec["provisional_items"], rec["placebo_proxy"], si_arm, t)
        rec["tiers_reachable_under_provisional"] = sorted(reach, key=TIERS.index)
        rec["provisional_affects_tier"] = len(reach) > 1
        rec["tier_changing_provisional_items"] = [k for k in rec["provisional_items"]
                                                  if len(reachable(sc, [k], rec["placebo_proxy"], si_arm, t)) > 1]
        rec["analysed_set"] = tr != "Limited"
        rec["rater_scores"] = dict(A=scores(a), B=scores(b), A_tier=rater_tier(a)[0], B_tier=rater_tier(b)[0])
        rec["clinician_review"] = []
        rec["results_attestation"] = dict(results_viewed=True, no_result_used_as_evidence=True,
                                          signed_by="Adjudicator (Claude Opus 5.5 agent), 2026-10-08. Data-check documents show result "
                                          "columns; only share bands, design, specification and publication evidence were used. The "
                                          "primary-analysis impact (step 5) was computed after this record was fixed.")
        out.append(rec)
    return out


# Directions in which a provisional score can still move once resolved (framework 1.6 and item unknown rules):
# EL/TZ/ES/DA provisional scores encode "present but unconfirmed" -> may fall, not rise (TZ: the >=50% escalation is never
# applied to an unknown share); SI/OU shares unknown -> either way; TS (practice-preserved dose contrast unverified) -> may rise.
MOVES = {"EL": (-1, 0), "TZ": (-1, 0), "ES": (-1, 0), "DA": (-1, 0), "SI": (-1, 0, 1), "OU": (-1, 0, 1), "TS": (0, 1), "CO": (-1, 0, 1),
         "FU": (-1, 0, 1), "BM": (-1, 0, 1)}
MOVES_TRIAL = {("ACTIVE W", "TZ"): (-1, 0),  # C2: 2 under the 77% reading, 1 under the ~38% reading
               ("SUSTAIN-6", "SI"): (0, 1), ("DECLARE-TIMI 58", "SI"): (0, 1)}  # a known 5-20% defect floors SI at 1


def reachable(sc, prov, pp, si_arm, trial=None):
    opts = [[sc[k] + m for m in MOVES_TRIAL.get((trial, k), MOVES[k]) if 0 <= sc[k] + m <= MAXP[k]] for k in prov]
    res = set()
    for combo in itertools.product(*opts) if prov else [()]:
        s = dict(sc)
        s.update(dict(zip(prov, combo)))
        res.add(tier(s, pp, si_arm and s["SI"] == 2)[0])
    return res


# ----------------------------------------------------------------------------- alternative readings (clarifications)
ALT = {
    "C1 literal: undocumented code-defined criteria -> SI 1 provisional, not EL": {
        "ROCKET-AF": {"EL": 1, "SI": 1}, "RE-LY": {"EL": 1, "SI": 1}, "EAST-AFNET 4": {"EL": 0}, "CABANA": {"EL": 0},
        "ACTIVE W": {"EL": 0, "SI": 1}, "ALLHAT": {"EL": 0, "SI": 1}, "VALUE": {"EL": 0, "SI": 1}, "ASCOT-BPLA": {"EL": 0, "SI": 1},
        "ONTARGET": {"EL": 0, "SI": 1}, "SUSTAIN-6": {"EL": 0}, "DECLARE-TIMI 58": {"EL": 0}, "CANVAS Program": {"EL": 0},
        "PROTECT AF": {"EL": 1, "SI": 1}, "AMPLIFY": {"EL": 0}, "EMPEROR-Preserved": {"EL": 1}},
    "C1 literal, then SI share > 20% when checked": {
        "ROCKET-AF": {"EL": 1, "SI": 2}, "RE-LY": {"EL": 1, "SI": 2}, "EAST-AFNET 4": {"EL": 0, "SI": 2}, "CABANA": {"EL": 0},
        "ACTIVE W": {"EL": 0, "SI": 2}, "ALLHAT": {"EL": 0, "SI": 2}, "VALUE": {"EL": 0, "SI": 2}, "ASCOT-BPLA": {"EL": 0, "SI": 2},
        "ONTARGET": {"EL": 0, "SI": 2}, "SUSTAIN-6": {"EL": 0, "SI": 2}, "DECLARE-TIMI 58": {"EL": 0, "SI": 2},
        "CANVAS Program": {"EL": 0, "SI": 2}, "PROTECT AF": {"EL": 1, "SI": 2}, "PRECISION": {"SI": 2}},
    "C2 ACTIVE W: TZ.c share = patients actually switched (~38%)": {"ACTIVE W": {"TZ": 1}},
    "C3 any-position HF codes not an SI defect": {"EAST-AFNET 4": {"SI": 0}},
    "C4 SI defects on different denominators summed (1 + 1 -> 2)": {"PARADIGM-HF": {"SI": 2}, "EMPEROR-Preserved": {"SI": 2},
                                                                    "DECLARE-TIMI 58": {"SI": 2}},
    "C5 CABANA TZ.d not scored separately from the SI dedupe": {"CABANA": {"TZ": 0}},
    "C6 experienced-subgroup point does not stack (EL capped at 1)": {"ROCKET-AF": {"EL": 1}, "RE-LY": {"EL": 1}},
    "C7 ES.b 0 without DC-ES-cross": {"ARISTOTLE": {"ES": 0}, "ROCKET-AF": {"ES": 0}, "RE-LY": {"ES": 0}, "FRAIL-AF": {"ES": 0},
                                      "AMPLIFY": {"ES": 0}},
    "C8 RE-LY >=90%-met by clinical reasoning": {"RE-LY": {"EL": 1}},
    "C9 omitted exclusions not material (PROTECT AF, AMPLIFY)": {"PROTECT AF": {"EL": 1}, "AMPLIFY": {"EL": 0}},
    "C10 DA.a not applicable when EF-unknown must carry a code": {"EMPEROR-Preserved": {"DA": 0}},
    "D2 LIFE BP bound scored in EL instead of SI": {"LIFE": {"EL": 1}},
    "C6+C7 together (ROCKET-AF, RE-LY)": {"ROCKET-AF": {"EL": 1, "ES": 0}, "RE-LY": {"EL": 1, "ES": 0}},
}


def alt_tiers(recs):
    by = {r["trial"]: r for r in recs}
    rows = []
    for name, ov in ALT.items():
        for t, o in ov.items():
            r = by[t]
            sc = {k: r["items"][k]["score"] for k in ITEMS}
            sc.update(o)
            si_arm = r["si_reason"] == "arm_assignment_or_time_zero" and sc["SI"] == 2
            tr = tier(sc, r["placebo_proxy"], si_arm)
            rows.append(dict(reading=name, trial=t, adjudicated_tier=r["tier"], adjudicated_total=r["total"], alt_total=tr[2], alt_tier=tr[0],
                             changes=tr[0] != r["tier"], enters_or_leaves=("leaves" if tr[0] == "Limited" and r["tier"] != "Limited" else
                                                                         "enters" if tr[0] != "Limited" and r["tier"] == "Limited" else "")))
    return pd.DataFrame(rows)


def v19_tiers():
    d = json.load(open(V19))
    return {t["key"]: t["tier"].split(" - ")[0] for t in d["trials"]}


# ----------------------------------------------------------------------------- impact (step 5)
def impact(recs):
    sys.path.insert(0, str(ROOT / "scripts/v20"))
    import sens_primary32 as SP  # noqa: E402  (published engine and statistics, unchanged)
    R = pd.read_parquet(SP.OUT / "restricted_cells.parquet")
    R = R[(R.rung == "P1") & (R.config == "main") & (((R.arm == "base") & (R.k_pcs == 0)) | ((R.arm == "ECG") & (R.k_pcs == 32)))]
    inv = {v: k for k, v in SP.KEY.items()}
    tier_of = {inv[r["spec_key"]]: r["tier"] for r in recs}
    assert len(tier_of) == 38
    sets = {"(a) published 32 (v19)": SP.S32,
            "(b) new analysed set (Exc+Good+Mod)": [n for n in SP.ALL if tier_of[n] != "Limited"],
            "(c) new Excellent+Good": [n for n in SP.ALL if tier_of[n] in ("Excellent", "Good")],
            "(d) all 38": SP.S38}
    CL = SP.V.cluster_of()
    rows = []
    for lab, trials in sets.items():
        g = {a: R[R.arm == a].set_index("trial", drop=False).loc[trials] for a in ("base", "ECG")}
        Fb, SMb = SP.per_trial(g["base"])
        Fa, SMa = SP.per_trial(g["ECG"])
        c = SP.contrast_row(Fa, Fb, trials, "one", CL, SMa, SMb)
        rows.append(dict(set=lab, n_trials=len(trials), relred=c["relred"], relred_lo=c["relred_lo"], relred_hi=c["relred_hi"],
                         m58_base=c["m58_b"], m58_ecg=c["m58_a"], lt01_base=c["lt01_b"], lt01_ecg=c["lt01_a"], lt01_better=c["lt01_better"],
                         lt01_p=c["lt01_p"], absd_base=c["absd_b"], absd_ecg=c["absd_a"], absd_better=c["absd_better"], absd_p=c["absd_p"],
                         bshuf_p=c["bshuf_p"]))
    D = pd.DataFrame(rows)
    g = D.iloc[0]
    gate = (round(g.relred, 1) == 11.4 and round(g.relred_lo, 1) == 6.3 and round(g.relred_hi, 1) == 16.0 and g.lt01_better == "22/32"
            and round(g.lt01_p, 3) == 0.002 and round(g.absd_base, 3) == 0.251 and round(g.absd_ecg, 3) == 0.205 and round(g.absd_p, 3) == 0.008)
    D["gate_pass"] = [gate] + [None] * (len(D) - 1)
    return D, gate, sets


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["all", "impact"])
    a = ap.parse_args()
    os.umask(0o077)
    A, B = load_raters()
    if a.step == "all":
        ag, dis, chk, means = agreement(A, B)
        ag.to_csv(AUD / "agreement.csv", index=False)
        dis.to_csv(AUD / "disagreements.csv", index=False)
        chk.to_csv(AUD / "rater_tier_check.csv", index=False)
        recs = adjudicate(A, B)
        v19 = v19_tiers()
        T = pd.DataFrame([dict(trial=r["trial"], key=r["spec_key"], total=r["total"], tier=r["tier"], rule=r["tier_rule_applied"],
                               v19=v19[r["spec_key"]], A_tier=r["rater_scores"]["A_tier"], B_tier=r["rater_scores"]["B_tier"],
                               provisional=";".join(r["provisional_items"]), tier_changing=";".join(r["tier_changing_provisional_items"]),
                               reachable=";".join(r["tiers_reachable_under_provisional"]),
                               **{k: r["items"][k]["score"] for k in ITEMS}) for r in recs])
        T.to_csv(AUD / "tiers.csv", index=False)
        AL = alt_tiers(recs)
        AL.to_csv(AUD / "alt_tiers.csv", index=False)
        new = set(T[T.tier != "Limited"].trial)
        old = set(T[T.v19 != "Limited"].trial)
        meta = dict(
            title="TRACE-ECG emulation quality v2.0: adjudicated scores (38 trials)",
            framework="docs/emulation_quality_v2/QUALITY_FRAMEWORK.md (v2.0 draft; section 11 defaults)",
            date="2026-10-08", git_sha=SHA, script="scripts/emulation_quality_v2/adjudicate.py",
            raters=dict(A=A["rater_identity"], B=B["rater_identity"],
                        caveat="Both raters and the adjudicator are runs of the same LLM; agreement is between two LLM runs, not human "
                               "inter-rater reliability. Framework 7.1/7.5 require clinician review of every adjudicated point."),
            status="adjudicated; NOT frozen: provisional scores that can change tiers remain (framework 7.6); clinician review pending",
            agreement=ag.round(4).to_dict(orient="records"),
            tier_counts={k: int((T.tier == k).sum()) for k in TIERS},
            analysed_set=sorted(new), entering_vs_v19=sorted(new - old), leaving_vs_v19=sorted(old - new),
            excellent_good=sorted(T[T.tier.isin(["Excellent", "Good"])].trial),
            no_tier_changing_provisional=sorted(T[(T.tier != "Limited") & (T.tier_changing == "")].trial),
            clarification_alternatives=AL[AL.changes].to_dict(orient="records"),
            records=recs)
        # framework 3.3 / 7.6: only bands enter the repository; rater notes quoting exact arm sizes are banded here
        txt = json.dumps(meta, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
        band = lambda m: "n " + (">= 500" if int(m.group(1).replace(",", "")) >= 500 else "< 500 (DA.b band)")
        txt = re.sub(r"\bn = ([0-9][0-9,]*)(?![0-9/.])", band, txt)
        FINAL.write_text(txt)
        pd.set_option("display.width", 250)
        print(ag[["element", "pct_agree", "kappa", "lo", "hi", "prevalence_nonzero_pct", "n_disagree"]].round(3).to_string(index=False))
        print("mean totals A, B, mean |diff|:", np.round(means, 2))
        print("reported != mechanical tier:", chk[(chk.reported != chk.mechanical) | (chk.total_reported != chk.total_mech)].to_string())
        print(T[["trial", "total", "tier", "v19", "A_tier", "B_tier", "provisional", "tier_changing", "reachable"]].to_string(index=False))
        print(meta["tier_counts"], len(new), "entering", meta["entering_vs_v19"], "leaving", meta["leaving_vs_v19"])
        print(AL[AL.changes].to_string(index=False))
    else:
        recs = json.load(open(FINAL))["records"]
        D, gate, sets = impact(recs)
        D.to_csv(AUD / "impact.csv", index=False)
        print(D.round(4).to_string(index=False))
        print("GATE", "PASS" if gate else "FAIL")
        if not gate:
            raise SystemExit("gate failed: published 32 not reproduced; impact numbers must not be used")


if __name__ == "__main__":
    main()
