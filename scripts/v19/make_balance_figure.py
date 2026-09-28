#!/usr/bin/env python
"""Covariate balance figure (2 panels): A primary 58-variable panel by domain; B expanded panel by clinical bucket.
Demographics PS vs + ECG (permuted-ECG placebo, unmatched shown), 38 trials. Values = mean across trials of each
trial's mean |SMD| in the group; p = one-sided sign-flip (ECG vs demographic PS) across 38 trials.
Outputs: docs/abstract/ACC_2027/fig_balance_combined.{png,pdf} (aggregate only)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = ROOT / "docs/abstract/ACC_2027"
K = 5 / 3
plt.rcParams.update({"font.size": 11 * K, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
COL = {"unmatched": "#adb5bd", "base": "#74c0fc", "ECG": "#d9480f", "shufECG": "#495057"}
S = np.random.default_rng(0).choice([1, -1], size=(200000, 38))


def sf(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    return float(((S[:, :len(d)] * np.abs(d)).mean(1) <= d.mean() + 1e-12).mean())


def pstr(p):
    return "p<0.001" if p < 0.001 else f"p={p:.3f}" if p < 0.01 else f"p={p:.2f}"


def panel_a():
    R = pd.read_csv(A / "claude-v18-embed-compare/results.csv")
    R = R[R.half == "full"]
    arms = {"unmatched": R[R.arm_role == "unmatched"].drop_duplicates("trial").set_index("trial")}
    P = R[R.rung == "P1"]
    for r in ("base", "ECG", "shufECG"):
        arms[r] = P[P.arm_role == r].set_index("trial")
    doms = [("Echo: LV function", "LV function (echo)"), ("Echo: LV structure", "LV structure (echo)"),
            ("Echo: diastolic / LA", "Diastolic / LA (echo)"), ("Echo: RV / pulmonary", "RV / pulmonary (echo)"),
            ("Echo: valves / aorta", "Valves (echo)"), ("Vitals & core labs", "Vitals & core labs"), ("Other labs", "Other labs"),
            ("Coded record", "Medications, use, codes")]
    rows = []
    for g, lab in doms:
        c = f"mean_smd_g:{g}"
        rows.append((lab, {r: arms[r][c].mean() for r in arms}, sf((arms["ECG"][c] - arms["base"][c]).values)))
    return rows


def panel_b():
    B = pd.read_csv(A / "claude-v19-expanded-buckets/per_bucket.csv")
    order = ["Comorbidities", "Medications", "Healthcare use & testing", "Additional labs & vitals", "Devices & procedures",
             "Risk & frailty scores", "Preventive care"]
    rows = []
    for b in order:
        P = B[B.bucket == b].pivot(index="trial", columns="arm", values="mean_smd")
        n = int(B[B.bucket == b].groupby("trial").n_vars.first().median())
        rows.append((f"{b} (~{n})", {r: P[r].mean() for r in COL}, sf((P["ECG"] - P["base"]).values)))
    return rows


def draw(ax, rows, title):
    y = np.arange(len(rows))[::-1]
    for i, (lab, v, p) in enumerate(rows):
        b, e = v["base"], v["ECG"]
        ax.plot([b, e], [y[i]] * 2, color="#2b8a3e" if e < b else "#c92a2a", lw=3, zorder=2)
        ax.scatter(v["unmatched"], y[i], marker="X", color=COL["unmatched"], s=110, zorder=3, label="Unmatched" if i == 0 else None)
        ax.scatter(v["shufECG"], y[i], marker="D", color=COL["shufECG"], s=60, zorder=3, label="Permuted-ECG placebo" if i == 0 else None)
        ax.scatter(b, y[i], color=COL["base"], s=150, zorder=4, edgecolors="white", label="Demographic PS" if i == 0 else None)
        ax.scatter(e, y[i], color=COL["ECG"], s=150, zorder=5, edgecolors="white", label="+ ECG embedding" if i == 0 else None)
        ax.text(max(v.values()) + 0.004, y[i], pstr(p), va="center", fontsize=9 * K, color="#444")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("Mean |SMD| (average across 38 trials)")
    ax.set_title(title, loc="left", fontweight="bold", fontsize=12 * K, pad=14)


def main():
    a, b = panel_a(), panel_b()
    fig, axs = plt.subplots(1, 2, figsize=(22, 9.5), gridspec_kw=dict(wspace=0.75))
    draw(axs[0], a, "A  Primary panel (58 characteristics)")
    draw(axs[1], b, "B  Expanded panel (~330 characteristics)")
    lo = min(min(v.values()) for _, v, _ in a + b) - 0.005
    hi = max(max(v.values()) for _, v, _ in a + b) + 0.03
    for ax in axs:
        ax.set_xlim(lo, hi)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=4, frameon=False, fontsize=9.5 * K, bbox_to_anchor=(0.5, 1.02))
    fig.text(0.01, -0.04, "Demographic propensity score (age, sex, calendar year) with vs without AI-ECG embedding; 1:1 matching, caliper 0.2. "
             "None of the characteristics were in the PS. p: one-sided sign-flip test across 38 trials (+ECG vs demographic PS).",
             fontsize=8.5 * K, color="#444")
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_balance_combined.{ext}", dpi=200, bbox_inches="tight")
    for lab, v, p in a + b:
        print(f"{lab:32s} u {v['unmatched']:.3f} base {v['base']:.3f} ECG {v['ECG']:.3f} shuf {v['shufECG']:.3f} {pstr(p)}")


if __name__ == "__main__":
    main()
