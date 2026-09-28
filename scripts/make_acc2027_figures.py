#!/usr/bin/env python
"""ACC 2027 abstract figures, three separate panels (aggregate data only):
A love plot (38 trials, demographics PS, caliper 0.2): median |SMD| across trials per held-out variable, without vs with ECG
B per-trial |log HR - RCT| without vs with ECG (38 trials)
C simulation: % of hidden-confounder bias removed vs ECG partial R2 (G2, as-designed scenario), ECG vs permuted ECG
Sources: audits/claude-v18-embed-compare/results.csv, audits/claude-v19-g2-simulation/relationship.csv.
Outputs: docs/abstract/ACC_2027/fig_{A_loveplot,B_hr_gap,C_simulation}.{png,pdf}
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from make_acc_figure import VARS  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = ROOT / "docs" / "abstract" / "ACC_2027"
plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
C_BASE, C_ECG, C_SHUF, C_UNM = "#74c0fc", "#d9480f", "#adb5bd", "#495057"
SHORT = {"Coded record": "Coded", "Vitals & core labs": "Vitals/labs", "Other labs": "Other labs", "Echo: LV structure": "LV struct.",
         "Echo: LV function": "LV func.", "Echo: diastolic / LA": "Diast./LA", "Echo: RV / pulmonary": "RV/pulm.", "Echo: valves / aorta": "Valves"}


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def load():
    R = pd.read_csv(A / "claude-v18-embed-compare/results.csv")
    R = R[R.half == "full"]
    unm = R[R.arm_role == "unmatched"].drop_duplicates("trial").set_index("trial")
    P = R[R.rung == "P1"]
    arms = {r: P[P.arm_role == r].set_index("trial") for r in ("base", "ECG", "shufECG")}
    arms["unmatched"] = unm
    return arms


def panel_a(arms):
    cols = [(c, lab, g) for c, lab, g in VARS if f"smd:{c}" in arms["base"]]
    med = {r: pd.Series({lab: arms[r][f"smd:{c}"].abs().median() for c, lab, g in cols}) for r in arms}
    pct = {r: (100 * (arms[r][[f"smd:{c}" for c, _, _ in cols]].abs() < 0.1).sum(1) / arms[r][[f"smd:{c}" for c, _, _ in cols]].notna().sum(1)) for r in arms}
    order = [(g, lab) for c, lab, g in cols]
    fig, ax = plt.subplots(figsize=(6.2, 10.5))
    y = {o: i for i, o in enumerate(order[::-1])}
    for i, o in enumerate(order):
        if i % 2 == 0:
            ax.axhspan(y[o] - 0.5, y[o] + 0.5, color="#f4f5f7", zorder=0)
    for g, lab in order:
        b, e = med["base"][lab], med["ECG"][lab]
        ax.plot([b, e], [y[(g, lab)]] * 2, color="#2b8a3e" if e < b else "#c92a2a", lw=1.4, alpha=0.8, zorder=2)
    kw = dict(zorder=4, s=22, edgecolors="white", linewidths=0.4)
    ax.scatter([med["unmatched"][l] for _, l in order], [y[o] for o in order], marker="x", color=C_UNM, s=16, lw=1, zorder=3, label="Unmatched")
    ax.scatter([med["shufECG"][l] for _, l in order], [y[o] for o in order], marker="D", color=C_SHUF, s=12, zorder=3, label="Permuted-ECG placebo")
    ax.scatter([med["base"][l] for _, l in order], [y[o] for o in order], color=C_BASE, label="Demographic PS", **kw)
    ax.scatter([med["ECG"][l] for _, l in order], [y[o] for o in order], color=C_ECG, label="Demographic PS + ECG", **kw)
    ax.axvline(0.1, color="#888", ls="--", lw=0.8)
    ax.set_yticks([y[o] for o in order])
    ax.set_yticklabels([l for _, l in order], fontsize=6.8)
    for g in dict.fromkeys(g for g, _ in order):
        ys = [y[o] for o in order if o[0] == g]
        ax.axhline(min(ys) - 0.5, color="#ccc", lw=0.6)
        ax.annotate(SHORT[g], xy=(1.0, np.mean(ys)), xycoords=("axes fraction", "data"), xytext=(4, 0), textcoords="offset points",
                    rotation=270, va="center", fontsize=7, fontweight="bold", color="#444")
    ax.set_ylim(-0.7, len(order) - 0.3)
    ax.set_xlim(0, min(0.45, float(np.nanmax([med[r].max() for r in med])) * 1.05))
    ax.set_xlabel("|Standardized mean difference| (median across 38 trials)")
    nb, ne = int((med["base"] < 0.1).sum()), int((med["ECG"] < 0.1).sum())
    ax.text(0.98, 0.995, f"Variables with median |SMD| < 0.1: {nb} → {ne} of {len(order)}\n"
            f"Per-trial share < 0.1: {pct['base'].mean():.0f}% → {pct['ECG'].mean():.0f}% (28/38 trials, p<0.001)",
            transform=ax.transAxes, ha="right", va="top", fontsize=7.2, bbox=dict(fc="white", ec="#ccc", boxstyle="round,pad=0.3"))
    ax.legend(loc="lower right", fontsize=7, frameon=True, facecolor="white", edgecolor="#ddd")
    ax.set_title("A  Balance on 58 held-out characteristics", loc="left", fontweight="bold")
    save(fig, "fig_A_loveplot")


def panel_b(arms):
    b, e = arms["base"], arms["ECG"]
    db, de = (b.loghr - b.rb).abs(), (e.loghr - e.rb).abs()
    fig, ax = plt.subplots(figsize=(4.2, 4.6))
    for t in db.index:
        ax.plot([0, 1], [db[t], de[t]], color="#2b8a3e" if de[t] < db[t] else "#c92a2a", alpha=0.55, lw=1.1)
    ax.scatter(np.zeros(len(db)), db, color=C_BASE, s=16, zorder=3)
    ax.scatter(np.ones(len(de)), de, color=C_ECG, s=16, zorder=3)
    ax.plot([0, 1], [db.mean(), de.mean()], color="black", lw=3, zorder=4)
    ax.text(-0.06, db.mean(), f"mean {db.mean():.2f}", ha="right", va="center", fontsize=8)
    ax.text(1.06, de.mean(), f"mean {de.mean():.2f}", ha="left", va="center", fontsize=8)
    k = int((de < db).sum())
    ax.text(0.5, 0.97, f"Closer to RCT with ECG: {k} of {len(db)} trials (p=0.002)", transform=ax.transAxes, ha="center", va="top", fontsize=8,
            bbox=dict(fc="white", ec="#ccc", boxstyle="round,pad=0.3"))
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Demographic PS", "+ ECG"])
    ax.set_xlim(-0.45, 1.45)
    ax.set_ylabel("|log HR (emulation) − log HR (RCT)|")
    ax.set_title("B  Distance from RCT result, per trial", loc="left", fontweight="bold")
    save(fig, "fig_B_hr_gap")


def panel_c():
    G = A / "claude-v19-g2-simulation"
    Q = pd.read_csv(G / "relationship.csv")
    X = pd.read_csv(G / "excluded_cells.csv")
    Q = Q[~(Q.trial + "|" + Q.conf).isin(X.trial + "|" + X.conf)]
    F = pd.read_csv(G / "relationship_fits.csv")
    F = F[F.x == "r2_partial"].set_index("conf")  # per-confounder mean % removed (as reported in G2_SIMULATION.md)
    lab = {"lvef": "Ejection fraction", "ntprobnp": "NT-proBNP", "bmi": "BMI", "egfr": "eGFR"}
    col = {"lvef": "#1971c2", "ntprobnp": "#e8590c", "bmi": "#2f9e44", "egfr": "#862e9c"}
    lo, hi = -60, 100
    fig, ax = plt.subplots(figsize=(4.8, 4.4))
    ax.axhline(0, color="#999", lw=0.8)
    ax.scatter(100 * Q.r2_partial, Q.prb_shufECG.clip(lo, hi), color=C_SHUF, marker="D", s=12, alpha=0.6,
               label=f"Permuted-ECG placebo (~0%)")
    for c in ("ntprobnp", "bmi", "lvef", "egfr"):
        g = Q[Q.conf == c]
        ax.scatter(100 * g.r2_partial, g.prb_ECG.clip(lo, hi), color=col[c], s=18, alpha=0.8,
                   label=f"ECG: {lab[c]} ({F.loc[c, 'mean_prb']:.0f}%)")
    xs = np.linspace(0, 100 * Q.r2_partial.max(), 50)
    ax.plot(xs, xs, color="#555", ls=":", lw=1, label="Bias removed = 100 × R²")
    ax.set_xlabel("ECG's ability to predict the hidden confounder (partial R², %)")
    ax.set_ylabel("Confounding bias removed by adding ECG (%)")
    ax.set_ylim(lo - 3, hi + 3)
    ax.text(0.99, 0.02, f"Overall: ECG {F.loc['all', 'mean_prb']:.0f}% of bias removed; Spearman ρ = {F.loc['all', 'spearman']:.2f}\n"
            f"{len(Q)} trial × confounder cells; values beyond axis clipped", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.3, color="#444")
    ax.legend(fontsize=6.5, loc="upper left", frameon=True, facecolor="white", edgecolor="#ddd")
    ax.set_title("C  Simulation with known treatment effect", loc="left", fontweight="bold")
    save(fig, "fig_C_simulation")


if __name__ == "__main__":
    arms = load()
    panel_a(arms)
    panel_b(arms)
    panel_c()
