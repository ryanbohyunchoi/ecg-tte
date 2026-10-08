"""v1 audit: quality-tier agreement numbers (paper2 'Which trials benefit' para 3) and axis-limit clipping checks."""
import json, itertools, numpy as np, pandas as pd
C = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core/"; R = "/home/rbc58/github/ecg-tte/"
QT = json.load(open(R + "docs/v19/quality_tiers.json"))["trials"]; tier = {t["key"]: t["tier"].split(" - ")[0] for t in QT}
PT = pd.read_csv(C + "per_trial.csv"); LPT = pd.read_csv(C + "labels_per_trial.csv")
def sf1(d):  # exact one-sided sign-flip P(mean >= obs)
    d = np.asarray(d, float); d = d[np.isfinite(d)]; obs = d.mean(); n = len(d)
    S = np.array(list(itertools.product([1, -1], repeat=n))); return float(((S * np.abs(d)).mean(1) >= obs - 1e-12).mean())
g = lambda a: PT[(PT.rung == "P5") & (PT.config == "main") & (PT.arm == a) & PT.in_S32].set_index("key").absd
b, e = g("base"), g("ECG")
for nm, ks in (("exc/good", [k for k in b.index if tier[k] in ("Excellent", "Good")]), ("moderate", [k for k in b.index if tier[k] == "Moderate"])):
    d = b[ks] - e[ks]
    print(nm, len(ks), "absd", round(b[ks].mean(), 3), "->", round(e[ks].mean(), 3), "closer", int((d > 0).sum()), "P1s", round(sf1(d.values), 3))
L = LPT[LPT.in_S32].copy(); L["tier"] = L.key.map(tier)
for a in ("ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"):
    x = L[L.arm == a]
    print(a, "gain_absd exc/good", round(x[x.tier.isin(["Excellent", "Good"])].gain_absd.mean(), 3), "moderate", round(x[x.tier == "Moderate"].gain_absd.mean(), 3))
x = L[L.arm.isin(["ECG", "CLMBR"])]
print("Fig4A gain_m54 range", round(x.gain_m54.min(), 4), round(x.gain_m54.max(), 4), "xlim (-0.035, 0.085)")
print("Fig5D |gain_absd|>0.3:", int((x.gain_absd.abs() > 0.3).sum()))
S = pd.read_csv(C + "sensitivity.csv"); s = S[S.set == "S32"]
print("S32 q_m54_fam < 1e-6 (clipped in Fig5C):", int((s.q_m54_p_fam < 1e-6).sum()))
for c, lo, hi in (("relred54_lo", -25, 35), ("relred54_hi", -25, 35)):
    m = s[(s.config == "main") & (s.kind == "within")]
    print("Fig2A", c, "outside xlim:", int(((m[c] < lo) | (m[c] > hi)).sum()))
p5 = s[s.contrast.str.match(r"^P5: (ECG|CLMBR|ECG\+CLMBR|shufECG|shufCLMBR) vs base$")]
print("Fig5A CI outside (-25,30):", int(((p5.relred54_lo < -25) | (p5.relred54_hi > 30)).sum()), "Fig5B d range", round((p5.absd_a - p5.absd_b).min(), 3), round((p5.absd_a - p5.absd_b).max(), 3))
F = pd.read_csv(C + "flagscv.csv")
print("Fig3C CI outside (-20,20) sens/fcv rows:", int(((F.relred54_lo < -20) | (F.relred54_hi > 20)).sum()))
