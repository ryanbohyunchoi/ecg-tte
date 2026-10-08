"""v1 audit: re-derive TRIAL_LABELS.json from labels_A/B (no writes), kappa, S32 physiologic / domain counts."""
import json, numpy as np, pandas as pd, sys
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v21")
A = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/labels/"
R = "/home/rbc58/github/ecg-tte/"
la = {x["trial"]: x for x in json.load(open(A + "labels_A.json"))}
lb = {x["trial"]: x for x in json.load(open(A + "labels_B.json"))}
J = json.load(open(R + "docs/v21/TRIAL_LABELS.json"))
CARD = ["LV_structure", "LV_systolic_function", "diastolic_LA", "RV_pulmonary_congestion", "rhythm_conduction"]
print("meta", J["meta"])
allv = set()
for t in la:
    allv |= set(la[t]["domains"]) | set(lb[t]["domains"])
print("domain vocab seen:", sorted(allv))
print("physiologic values A:", {la[t]["physiologic"] for t in la}, "B:", {lb[t]["physiologic"] for t in lb})
ya = np.array([la[t]["physiologic"] == "yes" for t in la]); yb = np.array([lb[t]["physiologic"] == "yes" for t in la])
from sklearn.metrics import cohen_kappa_score
print("kappa sklearn", cohen_kappa_score(ya, yb), "agree", (ya == yb).mean(), "yesA", ya.sum(), "yesB", yb.sum())
bad = 0
for r in J["labels"]:
    t = r["trial"]; a, b = la[t], lb[t]
    inter = [d for d in CARD if d in a["domains"] and d in b["domains"]] or ["none_cardiac"]
    uni = [d for d in CARD if d in a["domains"] or d in b["domains"]] or ["none_cardiac"]
    if r["domains"] != inter or r["domains_union"] != uni or r["physiologic"] != a["physiologic"]:
        bad += 1; print("MISMATCH", t)
    if a["physiologic"] != b["physiologic"]: print("DISAGREE", t)
    # both lists contain none_cardiac + cardiac?
    for x, nm in ((a, "A"), (b, "B")):
        if "none_cardiac" in x["domains"] and any(d in CARD for d in x["domains"]): print("none+cardiac in", nm, t)
print("json mismatches:", bad, "n", len(J["labels"]))
import paper2_grid as G  # imports only; no run
QT = json.load(open(R + "docs/v19/quality_tiers.json"))["trials"]
tier = {t["key"]: t["tier"].split(" - ")[0] for t in QT}
rows = []
for r in J["labels"]:
    n = G.LABEL_NAME[r["trial"]]; k = G.KEY[n]
    rows.append(dict(trial=r["trial"], s32=tier[k] != "Limited", phys=r["physiologic"] == "yes", dom=set(r["domains"]), domu=set(r["domains_union"])))
D = pd.DataFrame(rows)
s = D[D.s32]
print("S32 n", len(s), "physiologic:", int(s.phys.sum()), list(s[s.phys].trial))
print("S38 physiologic:", int(D.phys.sum()), list(D[D.phys & ~D.s32].trial))
for d in CARD:
    print(f"  {d}: S32 inter {int(s.dom.apply(lambda x: d in x).sum())} union {int(s.domu.apply(lambda x: d in x).sum())}; S38 inter {int(D.dom.apply(lambda x: d in x).sum())}")
# Table 1 check vs JSON
P = open(R + "docs/paper/paper2.md").read().splitlines()
tab = {}
for l in P:
    c = [x.strip() for x in l.strip("|").split("|")]
    if l.startswith("|") and len(c) == 11 and c[1] in G.LABEL_NAME: tab[c[1]] = (c[9], c[10])
m = {"LV_structure": "LV structure", "LV_systolic_function": "LV systolic function", "diastolic_LA": "diastolic/LA",
     "RV_pulmonary_congestion": "RV/pulmonary congestion", "rhythm_conduction": "rhythm/conduction", "none_cardiac": "none"}
nb = 0
for r in J["labels"]:
    exp = ("Yes" if r["physiologic"] == "yes" else "No", ", ".join(m[d] for d in r["domains"]))
    if tab.get(r["trial"]) != exp: nb += 1; print("TABLE1 MISMATCH", r["trial"], tab.get(r["trial"]), exp)
print("Table 1 rows", len(tab), "mismatches", nb)
