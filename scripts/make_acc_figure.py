#!/usr/bin/env python
"""ACC abstract figure (4 panels) from committed aggregate Yale outputs (18 trials). No patient-level data.
A  balance: median % of pre-matching imbalance removed on physiology not in any PS (physiology-driven trials)
B  per-trial |log HR - RCT| for sparse vs sparse+ECG (paired)
C  RCT-agreement metrics per PS (std-difference agreement, excess disagreement phi)
D  plasmode: share of confounding bias removed per PS; ECG gain vs share of coded data deleted
Output: docs/abstract/acc_figure.{png,pdf}
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import TRIALS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
V14 = ROOT / "docs" / "v14"
OUT = ROOT / "docs" / "abstract"
C = {"sparse": "#9ecae1", "sparse+ECG": "#d9480f", "hdPS200": "#4263eb", "hdPS200+ECG": "#f08c00", "clinical (reference)": "#2b8a3e",
     "unmatched": "#adb5bd"}
LAB = {"sparse": "Sparse PS", "sparse+ECG": "Sparse PS + ECG", "hdPS200": "hdPS", "hdPS200+ECG": "hdPS + ECG", "clinical (reference)": "Clinical PS"}
names = {**PRIMARY, **EXTRA}
trials = [n for n in names if (A / "claude-v13-bootstrap" / f"bs_{n}.csv").exists()]

plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
fig = plt.figure(figsize=(12, 8.6))
gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.40)

# ---- A: balance capture
axA = fig.add_subplot(gs[0, 0])
dom = [("LVSTRUCT", "LV\nstructure"), ("LVFUNC", "LV\nfunction"), ("DIAST", "Diastolic\n/ LA"), ("RVPULM", "RV /\npulmonary"),
       ("phys_obs", "Vitals & labs\n(measured)")]
arms = ["sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]
rows = []
for n in trials:
    k = names[n][0]
    if TRIALS[k].get("role") != "physiology":
        continue
    s = pd.read_csv(A / f"claude-cap4-all-{n}" / "summary_pooled.csv", index_col=0)
    for d, _ in dom:
        c = f"excess_{d}"
        if c in s and s.loc["unmatched", c] >= 0.02:
            for a in arms:
                rows.append(dict(trial=n, domain=d, arm=a, cap=min(100.0, 100 * (1 - s.loc[a, c] / s.loc["unmatched", c]))))
R = pd.DataFrame(rows)
med = R.groupby(["domain", "arm"]).cap.median().unstack()
x = np.arange(len(dom))
w = 0.16
for i, a in enumerate(arms):
    v = [med.loc[d, a] for d, _ in dom]
    axA.bar(x + (i - 2) * w, v, w, color=C[a], label=LAB[a], edgecolor="white", linewidth=0.5)
axA.set_xticks(x)
axA.set_xticklabels([l for _, l in dom])
axA.set_ylabel("Imbalance removed by matching (%)\nmedian across physiology trials")
axA.set_ylim(0, 105)
axA.axhline(100, color="#ccc", lw=0.8, ls="--")
axA.legend(frameon=False, ncol=3, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.18))
axA.set_title("A  Balance on physiology not included in any PS", loc="left", fontweight="bold", pad=34)
n_phys = R.trial.nunique()
axA.text(0.0, -0.2, f"Median over {n_phys} physiology-driven trials (echo, core vitals/labs never entered any PS); values capped at 100%.",
         transform=axA.transAxes, ha="left", fontsize=7.3, color="#555")

# ---- B: paired |Δlog HR|
axB = fig.add_subplot(gs[0, 1])
pts = []
for n in trials:
    d = pd.read_csv(A / "claude-v13-bootstrap" / f"bs_{n}.csv")
    d = d[d.rep == 0].set_index("arm")
    b, _ = bench(names[n][0])
    pts.append((n, abs(d.loc["sparse", "loghr"] - b), abs(d.loc["sparse+ECG", "loghr"] - b)))
P = pd.DataFrame(pts, columns=["trial", "sp", "ecg"]).sort_values("sp")
closer = int((P.ecg < P.sp).sum())
for _, r in P.iterrows():
    col = "#2b8a3e" if r.ecg < r.sp else "#c92a2a"
    axB.plot([0, 1], [r.sp, r.ecg], color=col, alpha=0.65, lw=1.3)
    axB.scatter([0, 1], [r.sp, r.ecg], color=[C["sparse"], C["sparse+ECG"]], s=22, zorder=3)
axB.plot([0, 1], [P.sp.mean(), P.ecg.mean()], color="black", lw=2.6, zorder=4)
axB.text(1.04, P.ecg.mean(), f"mean {P.ecg.mean():.2f}", va="center", fontsize=8.5)
axB.text(-0.04, P.sp.mean(), f"mean {P.sp.mean():.2f}", va="center", ha="right", fontsize=8.5)
axB.set_xticks([0, 1])
axB.set_xticklabels(["Sparse PS", "Sparse PS + ECG"])
axB.set_xlim(-0.35, 1.35)
axB.set_ylabel("|log HR (emulation) − log HR (RCT)|")
top = P.sort_values("sp").iloc[-1]
if top.sp > 0.5:
    axB.annotate(f"{TRIALS[names[top.trial][0]]['name'].split(':')[0].split(' (')[0]}", xy=(0, top.sp), xytext=(0.06, top.sp + 0.02), fontsize=7.5, color="#555")
    axB.set_ylim(-0.02, top.sp * 1.12)
axB.set_title("B  Distance from the RCT result, per trial", loc="left", fontweight="bold")
axB.text(0.5, 0.62, f"Closer to the RCT with ECG\nin {closer} of {len(P)} trials (green lines)", transform=axB.transAxes, ha="center", va="top", fontsize=8.5,
         bbox=dict(facecolor="white", edgecolor="#ddd", boxstyle="round,pad=0.3"))

# ---- C: agreement metrics
axC = fig.add_subplot(gs[1, 0])
pan = pd.read_csv(V14 / "panel_all.csv").set_index("arm")
pl = {"sparse": "Sparse", "sparse+ECG": "Sparse + ECG", "hdPS200": "hdPS200", "hdPS200+ECG": "hdPS200 + ECG", "clinical (reference)": "Clinical PS"}
sd = [100 * pan.loc[pl[a], "std_diff_agreement"] for a in arms]
phi = [pan.loc[pl[a], "dispersion_phi"] for a in arms]
x = np.arange(len(arms))
axC.bar(x - 0.2, sd, 0.38, color=[C[a] for a in arms], edgecolor="white")
axC.set_ylabel("Standardized-difference agreement (%)", color="#333")
axC.set_ylim(0, 100)
axC2 = axC.twinx()
axC2.plot(x + 0.2, phi, "o", color="black", ms=7)
for xi, v in zip(x, phi):
    axC2.text(xi + 0.2, v + 0.2, f"{v:.1f}", ha="center", fontsize=8)
axC2.set_ylabel("Excess disagreement φ (●)")
axC2.set_ylim(0, max(phi) * 1.35)
axC2.spines["top"].set_visible(False)
for xi, v in zip(x, sd):
    axC.text(xi - 0.2, v + 1.5, f"{v:.0f}%", ha="center", fontsize=8)
axC.set_xticks(x)
axC.set_xticklabels([LAB[a] for a in arms], fontsize=8)
axC.set_title("C  Agreement with 18 RCT hazard ratios", loc="left", fontweight="bold")
axC.text(0.01, 0.97, "Bars: % of trials whose HR is statistically consistent with the RCT.\nφ: disagreement beyond sampling error (1 = none).\nSparse → sparse + ECG: φ 4.7 → 3.4, sign-flip p = 0.02 (exploratory)",
         transform=axC.transAxes, va="top", fontsize=7.8, color="#333")

# ---- D: plasmode
axD = fig.add_subplot(gs[1, 1])
pb = pd.read_csv(V14 / "ecgonly_plasmode_bias.csv")
pb = pb[pb.scenario == "base"].set_index("arm").mean_abs_bias
order = [("demo", "Demographics"), ("ECGonly", "ECG only"), ("demo+ECG", "Demographics\n+ ECG"), ("sparse", "Sparse PS"),
         ("sparse+ECG", "Sparse PS\n+ ECG"), ("clinical (reference)", "Clinical PS")]
share = [100 * (1 - pb[a] / pb["unmatched"]) for a, _ in order]
cols = ["#ced4da", "#d9480f", "#f08c00", C["sparse"], C["sparse+ECG"], C["clinical (reference)"]]
axD.barh(range(len(order)), share, color=cols, edgecolor="white")
for i, v in enumerate(share):
    axD.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=8.5)
axD.set_yticks(range(len(order)))
axD.set_yticklabels([l for _, l in order], fontsize=8)
axD.invert_yaxis()
axD.set_xlim(0, 118)
axD.set_xlabel("Confounding bias removed in plasmode simulation (% of unadjusted)")
axD.set_title("D  Known-truth simulation (18 trials)", loc="left", fontweight="bold")
# inset: ECG gain vs % of codes deleted
H = pd.read_csv(V14 / "hypotheses.csv")
H = H[H.hypothesis.str.contains("subsampled") & (H.contrast == "C1") & H.test.str.contains("plasmode base")]
gain = {0: None}
for t in H.test:
    m = re.search(r"dropout ([0-9.]+)\).*reductions \+?(-?[0-9.]+) vs \+?(-?[0-9.]+)", t)
    if m:
        gain[int(round(float(m.group(1)) * 100))] = float(m.group(2))
        gain[0] = float(m.group(3))
ks = sorted(gain)
ins = axD.inset_axes([0.60, 0.58, 0.37, 0.24])
ins.plot(ks, [gain[k] for k in ks], "o-", color=C["sparse+ECG"])
ins.set_xticks(ks)
ins.set_xlabel("% of coded data deleted", fontsize=7)
ins.set_ylabel("Bias removed by\nECG (log HR)", fontsize=7)
ins.tick_params(labelsize=7)
ins.set_title("Sparse PS + ECG: gain grows as\ncoded data are removed", fontsize=7.5)

fig.suptitle("ECG embeddings as proxies for unmeasured physiology in 18 emulated cardiovascular trials", fontsize=12, fontweight="bold", y=0.995)
OUT.mkdir(parents=True, exist_ok=True)
for ext in ("png", "pdf"):
    fig.savefig(OUT / f"acc_figure.{ext}", dpi=300, bbox_inches="tight")
print("closer", closer, "of", len(P), "| means", round(P.sp.mean(), 3), round(P.ecg.mean(), 3), "| dropout gains", gain,
      "| shares", dict(zip([a for a, _ in order], [round(s) for s in share])), "| physiology trials", n_phys)
