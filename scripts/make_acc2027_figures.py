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


DOMS = [("Echo: LV function", "LV function (echo)"), ("Echo: LV structure", "LV structure (echo)"),
        ("Echo: diastolic / LA", "Diastolic / LA (echo)"), ("Echo: RV / pulmonary", "RV / pulmonary (echo)"),
        ("Vitals & core labs", "Vitals & core labs"), ("Coded record", "Medications, utilisation, codes")]
CATS = [("AF", "Atrial fibrillation"), ("HF", "Heart failure"), ("HTN", "Hypertension"), ("ACS/post-MI", "ACS / post-MI"),
        ("DM", "Diabetes"), ("Other", "Other")]


def _sf(d):
    rng = np.random.default_rng(0)
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    if len(d) <= 20:
        import itertools
        sg = np.array(list(itertools.product([1, -1], repeat=len(d))))
    else:
        sg = rng.choice([1, -1], size=(200000, len(d)))
    return float(((sg * np.abs(d)).mean(1) <= d.mean() + 1e-12).mean())


def _pstr(p):
    return "p<0.001" if p < 0.001 else f"p={p:.3f}" if p < 0.01 else f"p={p:.2f}"


def panel_a(arms):
    plt.rcParams.update({"font.size": 11})
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    y = np.arange(len(DOMS))[::-1]
    for i, (g, lab) in enumerate(DOMS):
        c = f"mean_smd_g:{g}"
        b, e, sh = arms["base"][c].median(), arms["ECG"][c].median(), arms["shufECG"][c].median()
        p = _sf((arms["ECG"][c] - arms["base"][c]).values)
        ax.plot([b, e], [y[i]] * 2, color="#2b8a3e", lw=2.2, zorder=2)
        ax.scatter(sh, y[i], marker="D", color=C_SHUF, s=34, zorder=3, label="Permuted-ECG placebo" if i == 0 else None)
        ax.scatter(b, y[i], color=C_BASE, s=70, zorder=4, edgecolors="white", label="Demographic PS" if i == 0 else None)
        ax.scatter(e, y[i], color=C_ECG, s=70, zorder=5, edgecolors="white", label="+ ECG embedding" if i == 0 else None)
        ax.text(max(b, sh) + 0.006, y[i], _pstr(p), va="center", fontsize=9, color="#444")
    ax.set_yticks(y)
    ax.set_yticklabels([lab for _, lab in DOMS])
    ax.set_xlim(0.06, 0.22)
    ax.set_xlabel("Mean |SMD| (median across 38 trials)")
    pct = {r: 100 * (arms[r][[c for c in arms[r] if c.startswith("smd:")]].abs() < 0.1).sum(1) / arms[r][[c for c in arms[r] if c.startswith("smd:")]].notna().sum(1) for r in ("base", "ECG")}
    ax.set_title("A  Balance on held-out characteristics", loc="left", fontweight="bold", fontsize=12, pad=24)
    ax.text(0.0, -0.2, f"All 58 variables: share with |SMD|<0.1 {pct['base'].mean():.0f}% → {pct['ECG'].mean():.0f}% (28/38 trials, p<0.001).\n"
            "No gain for other labs or valves.", transform=ax.transAxes, fontsize=8.5, color="#444", va="top")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3, fontsize=8, frameon=False, handletextpad=0.3, columnspacing=1.0)
    save(fig, "fig_A_loveplot")


def panel_b(arms):
    plt.rcParams.update({"font.size": 11})
    b, e = arms["base"], arms["ECG"]
    db, de = (b.loghr - b.rb).abs(), (e.loghr - e.rb).abs()
    cat = b.category
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    rows = [("All", "All 38 trials", db.index)] + [(k, lab, cat.index[cat == k]) for k, lab in CATS]
    y = np.arange(len(rows))[::-1]
    for i, (k, lab, idx) in enumerate(rows):
        m0, m1 = db[idx].mean(), de[idx].mean()
        kk = int((de[idx] < db[idx]).sum())
        p = _sf((de[idx] - db[idx]).values)
        ax.plot([m0, m1], [y[i]] * 2, color="#2b8a3e" if m1 < m0 else "#c92a2a", lw=2.2, zorder=2)
        ax.scatter(m0, y[i], color=C_BASE, s=70, zorder=4, edgecolors="white", label="Demographic PS" if i == 0 else None)
        ax.scatter(m1, y[i], color=C_ECG, s=70, zorder=5, edgecolors="white", label="+ ECG embedding" if i == 0 else None)
        ax.text(max(m0, m1) + 0.012, y[i], f"{kk}/{len(idx)} closer, {_pstr(p)}", va="center", fontsize=9, color="#444")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{lab} (n={len(idx)})" if k != "All" else lab for k, lab, idx in rows])
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.set_xlim(0, max(db.groupby(cat).mean().max(), db.mean()) * 1.75)
    ax.set_xlabel("Mean |log HR (emulation) − log HR (RCT)|")
    ax.set_title("B  Distance from RCT result, by trial type", loc="left", fontweight="bold", fontsize=12, pad=24)
    ax.text(0.0, -0.2, "Trial-type categories were defined post hoc; the AF gain did not replicate\nin 5 prespecified new AF trials alone (3/5 closer).",
            transform=ax.transAxes, fontsize=8.5, color="#444", va="top")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3, fontsize=8, frameon=False, handletextpad=0.3, columnspacing=1.0)
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


def panel_d(arms):
    """Panel A plus the unmatched (crude) comparison, for inspection."""
    plt.rcParams.update({"font.size": 11})
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    y = np.arange(len(DOMS))[::-1]
    for i, (g, lab) in enumerate(DOMS):
        c = f"mean_smd_g:{g}"
        u, b, e, sh = (arms[r][c].median() for r in ("unmatched", "base", "ECG", "shufECG"))
        ax.plot([min(u, b, e), max(u, b, e)], [y[i]] * 2, color="#dee2e6", lw=1, zorder=1)
        ax.plot([b, e], [y[i]] * 2, color="#2b8a3e", lw=2.2, zorder=2)
        ax.scatter(u, y[i], marker="x", color=C_UNM, s=55, lw=1.6, zorder=3, label="Unmatched" if i == 0 else None)
        ax.scatter(sh, y[i], marker="D", color=C_SHUF, s=34, zorder=3, label="Permuted-ECG placebo" if i == 0 else None)
        ax.scatter(b, y[i], color=C_BASE, s=70, zorder=4, edgecolors="white", label="Demographic PS" if i == 0 else None)
        ax.scatter(e, y[i], color=C_ECG, s=70, zorder=5, edgecolors="white", label="+ ECG embedding" if i == 0 else None)
    ax.set_yticks(y)
    ax.set_yticklabels([lab for _, lab in DOMS])
    ax.set_xlabel("Mean |SMD| (median across 38 trials)")
    ax.set_title("D  Balance incl. unmatched comparison", loc="left", fontweight="bold", fontsize=12, pad=24)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=4, fontsize=7.5, frameon=False, handletextpad=0.3, columnspacing=0.8)
    save(fig, "fig_D_loveplot_unmatched")


def panel_e(arms):
    """Panel A with the unmatched comparison (gray) in place of the permuted-ECG placebo."""
    plt.rcParams.update({"font.size": 11})
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    y = np.arange(len(DOMS))[::-1]
    for i, (g, lab) in enumerate(DOMS):
        c = f"mean_smd_g:{g}"
        u, b, e = (arms[r][c].median() for r in ("unmatched", "base", "ECG"))
        p = _sf((arms["ECG"][c] - arms["base"][c]).values)
        ax.plot([b, e], [y[i]] * 2, color="#2b8a3e", lw=2.2, zorder=2)
        ax.scatter(u, y[i], marker="X", color=C_SHUF, s=70, zorder=3, label="Unmatched" if i == 0 else None)
        ax.scatter(b, y[i], color=C_BASE, s=70, zorder=4, edgecolors="white", label="Demographic PS" if i == 0 else None)
        ax.scatter(e, y[i], color=C_ECG, s=70, zorder=5, edgecolors="white", label="+ ECG embedding" if i == 0 else None)
        ax.text(max(u, b) + 0.006, y[i], _pstr(p), va="center", fontsize=9, color="#444")
    ax.set_yticks(y)
    ax.set_yticklabels([lab for _, lab in DOMS])
    ax.set_xlim(0.06, 0.22)
    ax.set_xlabel("Mean |SMD| (median across 38 trials)")
    ax.set_title("E  Balance on held-out characteristics", loc="left", fontweight="bold", fontsize=12, pad=24)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3, fontsize=8, frameon=False, handletextpad=0.3, columnspacing=1.0)
    ax.text(0.0, -0.2, "p: + ECG vs demographic PS (sign-flip across 38 trials).\nAll 58 variables: share with |SMD|<0.1 51% → 57%. No gain for other labs or valves.",
            transform=ax.transAxes, fontsize=8.5, color="#444", va="top")
    save(fig, "fig_E_loveplot_unmatched")


if __name__ == "__main__":
    arms = load()
    panel_a(arms)
    panel_b(arms)
    panel_c()
    panel_d(arms)
    panel_e(arms)
