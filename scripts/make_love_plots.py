#!/usr/bin/env python
"""Love plots (aggregate only): median |SMD| after matching per balancing variable not in the sparse PS,
without vs with ECG, for sparse PS and hdPS, across all 18 trials and the physiology-driven subset.
Output: docs/abstract/love_plots.{png,pdf}
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_acc_figure import OUT, VARS, names, trials  # noqa: E402
from trial_specs import TRIALS  # noqa: E402
from v13_common import A  # noqa: E402

ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG"]
SHORT = {"Coded record": "Coded", "Vitals & core labs": "Vitals/labs", "Other labs": "Other labs", "Echo: LV structure": "LV struct.",
         "Echo: LV function": "LV func.", "Echo: diastolic / LA": "Diast./LA", "Echo: RV / pulmonary": "RV/pulm.", "Echo: valves / aorta": "Valves"}


def load(sub):
    rows = []
    for n in sub:
        s = pd.read_csv(A / f"claude-cap4-all-{n}" / "summary_pooled.csv", index_col=0)
        for c, lab, g in VARS:
            if c in s:
                for a in ARMS:
                    if a in s.index and not pd.isna(s.loc[a, c]):
                        rows.append(dict(trial=n, var=lab, group=g, arm=a, smd=abs(s.loc[a, c])))
    return pd.DataFrame(rows)


def panel(ax, D, base, ecg, title, show_labels):
    L = D.groupby(["group", "var", "arm"]).smd.median().unstack("arm")
    order = [(g, lab) for _, lab, g in VARS if (g, lab) in L.index]
    y = dict(zip(order, np.arange(len(order))[::-1]))
    for i, o in enumerate(order):
        if i % 2 == 0:
            ax.axhspan(y[o] - 0.5, y[o] + 0.5, color="#f4f5f7", zorder=0)
    for o in order:
        b, e = L.loc[o, base], L.loc[o, ecg]
        ax.plot([b, e], [y[o]] * 2, color="#2b8a3e" if e < b else "#c92a2a", lw=1.6, zorder=2, alpha=0.8)
    ax.scatter([L.loc[o, "unmatched"] for o in order], [y[o] for o in order], marker="x", color="#868e96", s=18, lw=1, zorder=3, label="Unmatched")
    ax.scatter([L.loc[o, base] for o in order], [y[o] for o in order], color="#74c0fc", s=22, zorder=4, ec="white", lw=0.4, label="Without ECG")
    ax.scatter([L.loc[o, ecg] for o in order], [y[o] for o in order], color="#d9480f", s=22, zorder=5, ec="white", lw=0.4, label="With ECG")
    ax.axvline(0.1, color="#999", ls="--", lw=0.8)
    ax.set_yticks(list(y.values()))
    ax.set_yticklabels([lab for _, lab in order] if show_labels else [], fontsize=6.5)
    for g in dict.fromkeys(g for g, _ in order):
        ys = [y[o] for o in order if o[0] == g]
        ax.axhline(min(ys) - 0.5, color="#bbb", lw=0.6)
        ax.annotate(SHORT[g], xy=(1.0, np.mean(ys)), xycoords=("axes fraction", "data"), xytext=(3, 0), textcoords="offset points",
                    rotation=270, va="center", fontsize=6.5, fontweight="bold", color="#444")
    ax.set_xlim(0, 0.45)
    ax.set_ylim(-0.7, len(order) - 0.3)
    nb = int(sum(L.loc[o, ecg] < L.loc[o, base] for o in order))
    nlt = (int(sum(L.loc[o, base] < 0.1 for o in order)), int(sum(L.loc[o, ecg] < 0.1 for o in order)))
    P = D[D.arm.isin([base, ecg])].pivot_table(index=["trial", "var"], columns="arm", values="smd").dropna()
    pair = (P[ecg] < P[base]).mean()
    ax.set_title(title, loc="left", fontweight="bold", fontsize=9)
    ax.text(0.98, 0.995, f"ECG lower in {nb}/{len(order)} variables\n{100 * pair:.0f}% of trial×variable pairs\n"
            f"|SMD|<0.1: {nlt[0]} → {nlt[1]} of {len(order)}\nmean |SMD| {P[base].mean():.3f} → {P[ecg].mean():.3f}",
            transform=ax.transAxes, ha="right", va="top", fontsize=6.8, bbox=dict(fc="white", ec="#ccc", boxstyle="round,pad=0.3"))
    ax.set_xlabel("|SMD| after matching (median across trials)", fontsize=7.5)


def main():
    plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    phys = [n for n in trials if TRIALS[names[n][0]].get("role") == "physiology"]
    Dall, Dph = load(trials), load(phys)
    fig, axs = plt.subplots(1, 4, figsize=(17, 11), sharey=False)
    panel(axs[0], Dall, "sparse", "sparse+ECG", f"A  Sparse PS, all {len(trials)} trials", True)
    panel(axs[1], Dph, "sparse", "sparse+ECG", f"B  Sparse PS, {len(phys)} physiology trials", False)
    panel(axs[2], Dall, "hdPS200", "hdPS200+ECG", f"C  hdPS, all {len(trials)} trials", False)
    panel(axs[3], Dph, "hdPS200", "hdPS200+ECG", f"D  hdPS, {len(phys)} physiology trials", False)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h + [plt.Line2D([], [], color="#2b8a3e", lw=2), plt.Line2D([], [], color="#c92a2a", lw=2)],
               l + ["ECG reduced imbalance", "ECG increased imbalance"], loc="lower center", ncol=5, frameon=False, fontsize=8)
    fig.suptitle("Love plots: covariate balance on 58 variables not in the sparse PS, without vs with AI-ECG embedding (Yale)", fontweight="bold")
    fig.subplots_adjust(left=0.12, right=0.98, wspace=0.18, bottom=0.08, top=0.93)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"love_plots.{ext}", dpi=220)


if __name__ == "__main__":
    main()
