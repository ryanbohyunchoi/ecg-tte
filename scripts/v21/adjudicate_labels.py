"""Adjudicate the two blind trial labellings (paper2, step A).

Inputs : audits/claude-v21-paper2/labels/labels_{A,B}.json (blind; PICOT only)
Outputs: docs/v21/TRIAL_LABELS.json, docs/v21/TRIAL_LABELS.md

Rules (fixed before any stratified result was computed):
- physiologic: agreed value; disagreements would go to a third blind labeller (none occurred).
- domains (primary): intersection of the two labellers' cardiac domains; ["none_cardiac"] if empty.
- domains_union (sensitivity): union of cardiac domains; ["none_cardiac"] if empty.
- confidence: the lower of the two.
"""
import json, pathlib
A = pathlib.Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/labels")
D = pathlib.Path(__file__).resolve().parents[2] / "docs" / "v21"
PIC = A / "picot_blind.md"
CARD = ["LV_structure", "LV_systolic_function", "diastolic_LA", "RV_pulmonary_congestion", "rhythm_conduction"]
RANK = {"low": 0, "medium": 1, "high": 2}

def main():
    la = {x["trial"]: x for x in json.load(open(A / "labels_A.json"))}
    lb = {x["trial"]: x for x in json.load(open(A / "labels_B.json"))}
    order, area = [], {}
    for l in PIC.read_text().splitlines():
        c = [s.strip() for s in l.strip("|").split("|")]
        if l.startswith("|") and len(c) > 2 and c[1] not in ("Trial", "") and not set(c[1]) <= set("- "):
            order.append(c[1]); area[c[1]] = c[0]
    assert set(order) == set(la) == set(lb) and len(order) == 38, "trial sets differ"
    n = len(order)
    ya = [la[t]["physiologic"] == "yes" for t in order]; yb = [lb[t]["physiologic"] == "yes" for t in order]
    po = sum(a == b for a, b in zip(ya, yb)) / n
    pa, pb = sum(ya) / n, sum(yb) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    out, log, dis = [], [], []
    for t in order:
        a, b = la[t], lb[t]
        da = [d for d in CARD if d in a["domains"]]; db = [d for d in CARD if d in b["domains"]]
        inter = [d for d in CARD if d in da and d in db]; uni = [d for d in CARD if d in da or d in db]
        if a["physiologic"] != b["physiologic"]:
            dis.append(t)
        conf = min(a["confidence"], b["confidence"], key=RANK.get)
        rec = dict(trial=t, area=area[t], physiologic=a["physiologic"] if a["physiologic"] == b["physiologic"] else "DISAGREE",
                   domains=inter or ["none_cardiac"], domains_union=uni or ["none_cardiac"], confidence=conf,
                   confidence_A=a["confidence"], confidence_B=b["confidence"],
                   rationale_A=a["rationale"], rationale_B=b["rationale"])
        out.append(rec)
        if set(da) != set(db):
            log.append(f"| {t} | {', '.join(da) or 'none_cardiac'} | {', '.join(db) or 'none_cardiac'} | {', '.join(rec['domains'])} |")
    assert not dis, f"physiologic disagreements need a third labeller: {dis}"
    meta = dict(n_trials=n, physiologic_yes=sum(ya), kappa_physiologic=round(kappa, 4), percent_agreement=round(po, 4),
                rule="domains = intersection of the two blind labellers (none_cardiac if empty); domains_union = sensitivity; confidence = lower of two",
                sources=["labels/labels_A.json", "labels/labels_B.json", "labels/picot_blind.md"])
    D.mkdir(parents=True, exist_ok=True)
    json.dump(dict(meta=meta, labels=out), open(D / "TRIAL_LABELS.json", "w"), indent=1)
    dom_count = {d: sum(d in r["domains"] for r in out) for d in CARD + ["none_cardiac"]}
    md = ["# Trial labels for paper2 (blind, adjudicated)", "",
          "Written by `scripts/v21/adjudicate_labels.py` on 2026-10-07, **before any label-stratified result was computed**.", "",
          "## Procedure", "",
          "- Two independent labellers (separate Claude agents) saw only a results-free PICOT table for the 38 trials (`audits/claude-v21-paper2/labels/picot_blind.md`: area, trial, population, intervention, comparator, RCT primary endpoint, horizon). They saw no emulation results, no RCT estimates and no quality tiers, and they did not see each other's labels.",
          "- Rubric: `physiologic` = yes if, in routine care, the choice between intervention and comparator is plausibly driven substantially by cardiac structure, function, rhythm/conduction or haemodynamic/congestion state (things an ECG can reflect), rather than mainly by metabolic, renal, bleeding, frailty, cost/formulary or prescriber factors. `domains` = one or more of LV_structure, LV_systolic_function, diastolic_LA, RV_pulmonary_congestion, rhythm_conduction, or none_cardiac. `confidence` = high/medium/low.",
          "- Adjudication rule, fixed in advance: an agreed `physiologic` value stands, and a disagreement would go to a third blind labeller. Primary `domains` are the **intersection** of the two labellers' cardiac domains (none_cardiac if empty), and `domains_union` is kept as a sensitivity set. Confidence is the lower of the two.",
          "- Caveat: the labellers know the published trials, and the user accepted some circularity (HANDOFF_PAPER2 §1.6). One labeller listed secondary cardiac domains for some 'no' trials and the other did not; the intersection rule resolves this conservatively.", "",
          "## Agreement", "",
          f"- physiologic: {sum(ya)}/{n} yes (A) and {sum(yb)}/{n} yes (B); percent agreement {po:.0%}; **Cohen's κ = {kappa:.2f}**. No third labeller was needed.",
          f"- domains: identical for {n - len(log)}/{n} trials; the {len(log)} differences are listed below.", "",
          "| Trial | Labeller A | Labeller B | Final (intersection) |", "|---|---|---|---|", *log, "",
          "## Final labels", "",
          "| Area | Trial | Physiologic | Domains (primary) | Domains (union, sensitivity) | Confidence |", "|---|---|---|---|---|---|"]
    for r in out:
        md.append(f"| {r['area']} | {r['trial']} | {r['physiologic']} | {', '.join(r['domains'])} | {', '.join(r['domains_union'])} | {r['confidence']} |")
    md += ["", "Domain counts (primary): " + "; ".join(f"{k} {v}" for k, v in dom_count.items()), "",
           "Rationales from both labellers are in `TRIAL_LABELS.json` (`rationale_A`, `rationale_B`)."]
    (D / "TRIAL_LABELS.md").write_text("\n".join(md) + "\n")
    print(json.dumps(meta), dom_count)

if __name__ == "__main__":
    main()
