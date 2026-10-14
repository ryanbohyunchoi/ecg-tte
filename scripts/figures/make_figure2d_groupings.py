#!/usr/bin/env python
"""Figure 2D, other groupings (docs/queue/figure2D.md, 2026-10-14): the tabs of the lab deck's panel D popup. Every tab shows the
same per-trial values as Figure 2D (PS-CVD5 + ECG vs PS-CVD5, change in % of the 54 leakage-corrected items with |SMD| < 0.1;
the 31 trials of s31; make_figure2_latent.compute / trial_dpct), grouped descriptively. No group P values or tests.

  1  cardiac-physiology decision (default; make_figure2_latent.panel_d, the same drawing as Figure 2D)
  2  clinical area (trials_meta "area"), grouped layout: bars clustered by area, sorted within it, dashed group mean
  3  type of treatment decision (6 groups, DECISION), grouped layout
  4  physiologic label (blind trial labels, docs/v21/TRIAL_LABELS.json "physiologic"), sorted layout

Group counts and means are gated against EXPECT (the queue file's expected values); a mismatch stops the script. Group titles and
counts are checked for overlap (the mock-ups' BP-lowering / Other titles overlapped).

Outputs: docs/paper/figures_latent/panels/panelD_groupings/tab{1..4}_*.png. Aggregates only.

  python scripts/figures/make_figure2d_groupings.py    (also run at the end of make_figure2_latent.py)
"""
import os
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_figure2_latent as F  # noqa: E402

OUT = F.OUT / "panels" / "panelD_groupings"
NAVY, GREY = F.NAVY, F.GREY
OI = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#999999"]  # Okabe-Ito (colour-blind safe), as the mock-ups
AREAS = ["AF", "HF", "ACS / MI", "Hypertension", "Diabetes", "Other"]
# type of treatment decision (trials_meta "full" names); the first two = make_figure2_latent.CARDIAC_PHYSIOLOGY
DECISION = {"Rhythm control (drug or ablation)": F.CARDIAC_PHYSIOLOGY["rhythm control"],
            "HF / RAAS drug choice": F.CARDIAC_PHYSIOLOGY["HF / RAAS drug choice"],
            "Antithrombotic (incl. LAA occlusion)": ["ARISTOTLE", "ROCKET-AF", "RE-LY", "FRAIL-AF", "ACTIVE W", "AMPLIFY", "PLATO", "LAAOS III"],
            "Glucose-lowering": ["CANVAS Program", "CAROLINA", "CARMELINA", "LEADER", "EMPA-REG OUTCOME", "SUSTAIN-6", "TECOS"],
            "BP-lowering": ["LIFE", "INSIGHT"],
            "Other (statin, NSAID)": ["PROVE IT-TIMI 22", "LODESTAR", "PRECISION"]}
WRAP = {"Rhythm control (drug or ablation)": "Rhythm control\n(drug or ablation)", "HF / RAAS drug choice": "HF / RAAS\ndrug choice",
        "Antithrombotic (incl. LAA occlusion)": "Antithrombotic\n(incl. LAA occlusion)", "Glucose-lowering": "Glucose-\nlowering",
        "BP-lowering": "BP-\nlowering", "Other (statin, NSAID)": "Other\n(statin,\nNSAID)"}
# expected (improved, trials, mean points), queue file
EXPECT = {"area": {"AF": (7, 11, 4.5), "HF": (4, 5, 7.4), "ACS / MI": (1, 2, 5.5), "Hypertension": (1, 2, -4.7), "Diabetes": (3, 7, 0.8),
                   "Other": (3, 4, 2.3)},
          "decision": {"Rhythm control (drug or ablation)": (5, 5, 12.2), "HF / RAAS drug choice": (5, 6, 8.0),
                       "Antithrombotic (incl. LAA occlusion)": (3, 8, -0.5), "Glucose-lowering": (3, 7, 0.8), "BP-lowering": (1, 2, -4.7),
                       "Other (statin, NSAID)": (2, 3, 0.6)},
          "physiologic": {"yes": (9, 10, 8.5), "no": (10, 21, 0.9)}}
TABS = [("tab1_cardiac_physiology.png", "Cardiac-physiology"), ("tab2_clinical_area.png", "Clinical area"),
        ("tab3_treatment_decision.png", "Type of treatment decision"), ("tab4_physiologic_label.png", "Physiologic label")]
FIGSIZE = (6.6, 3.05)
YLAB = "Change in % of items\nwith |SMD| < 0.1"
TITLE = "PS-CVD5 + ECG vs PS-CVD5, per trial"
GAP = 2.0  # space between groups (in bar widths)


def groups(V):
    """per-trial group labels (trial-set order) for tabs 2-4; DECISION must cover exactly the 31."""
    full = V["D"]["full"]
    allD = [t for v in DECISION.values() for t in v]
    assert len(allD) == len(set(allD)) == 31 and set(allD) == set(full), (set(allD) ^ set(full))
    dec = np.array([next(k for k, v in DECISION.items() if f in v) for f in full])
    area = np.array(V["D"]["area"])
    assert set(area) == set(AREAS)
    phys = np.array(["yes" if p else "no" for p in V["D"]["phys"]])
    return dict(area=area, decision=dec, physiologic=phys)


def summaries(V, G):
    """group (improved, trials, mean) at full precision, gated against EXPECT. The queue file's means were computed by the mock-up
    (d_mock2.py) from per-trial values already rounded to 1 decimal; where that alone explains a 0.1 difference (counts equal, and
    the mock-up's arithmetic on the rounded values gives the expected mean) the full-precision mean is shown and the case is logged
    in ROUNDING. Any other difference stops the script."""
    d = V["D"]["d"]
    got, ROUNDING = {}, []
    for k, cats in (("area", AREAS), ("decision", list(DECISION)), ("physiologic", ["yes", "no"])):
        got[k] = {}
        for g in cats:
            m_ = G[k] == g
            a, n, m = F.d_summary(d, m_)
            got[k][g] = (a, n, float(f"{m:.1f}"))
            ea, en, em = EXPECT[k][g]
            mock = float(f"{np.round(d[m_], 1).mean():.1f}")  # the mock-up's arithmetic (1-decimal per-trial inputs)
            if (a, n) != (ea, en) or (got[k][g][2] != em and mock != em):
                raise SystemExit(f"panel D popup ({k}, {g}): got {(a, n, round(m, 3))}, expected {EXPECT[k][g]}")
            if got[k][g][2] != em:
                ROUNDING.append(dict(grouping=k, group=g, expected=em, shown=got[k][g][2], full_precision=round(m, 4), mockup_arithmetic=mock))
    for x in ROUNDING:
        print("  rounding (expected value from 1-decimal inputs):", x)
    return got, ROUNDING


def no_overlap(fig, texts, what):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = [t.get_window_extent(r) for t in texts]
    for i in range(len(bb)):
        for j in range(i + 1, len(bb)):
            assert not bb[i].overlaps(bb[j]), (what, texts[i].get_text(), texts[j].get_text())


def finish(ax):
    ax.axhline(0, color=NAVY, lw=0.6)
    ax.set_ylabel(YLAB, fontsize=6.6)
    ax.tick_params(axis="x", length=2, pad=1.5)


def grouped(V, lab, cats, fn, title, wrap=None):
    d, nm = V["D"]["d"], np.array(V["D"]["name"])
    col = dict(zip(cats, OI))
    fig, ax = plt.subplots(figsize=(FIGSIZE[0], FIGSIZE[1] + 0.35))
    x, ticks, tl, tc, txt = 0.0, [], [], [], []
    for c in cats:
        idx = np.where(lab == c)[0]
        idx = idx[F.sorted_order(d[idx], nm[idx])]
        xs = x + np.arange(len(idx))
        ax.bar(xs, d[idx], color=col[c], width=0.8)
        ticks += list(xs)
        tl += list(nm[idx])
        tc += [col[c]] * len(idx)
        a, n, m = F.d_summary(d, lab == c)
        ax.hlines(m, xs[0] - 0.45, xs[-1] + 0.45, color=NAVY, lw=1.0, ls=(0, (3, 1.5)))
        txt.append(ax.text(xs.mean(), 31.5, (wrap or {}).get(c, c), ha="center", va="top", fontsize=5.7, color=col[c], fontweight="bold",
                           linespacing=1.05))
        txt.append(ax.text(xs.mean(), 22.6, f"{a}/{n} improved\nmean {F.mfmt(m)}", ha="center", va="bottom", fontsize=5.4, color=NAVY,
                           linespacing=1.05))
        x += len(idx) + GAP
    finish(ax)
    ax.set_xticks(ticks, tl, rotation=60, ha="right", rotation_mode="anchor", fontsize=5.4)
    for t, c in zip(ax.get_xticklabels(), tc):
        t.set_color(c)
    ax.set_xlim(-0.9, x - GAP + 0.3)
    ax.set_ylim(-14.5, 32)
    ax.set_yticks(range(-10, 21, 5))
    ax.spines["left"].set_bounds(-14.5, 20)
    ax.set_title(title, fontsize=7, loc="left")
    fig.tight_layout()
    no_overlap(fig, txt, fn)
    lo, hi = d.min(), d.max()
    assert lo > -14.5 and hi < 22.6 - 1.5, (lo, hi)  # bars clear of the group text
    fig.savefig(OUT / fn, dpi=300)
    plt.close(fig)


def sorted_phys(V, lab, fn, title):
    d, nm = V["D"]["d"], np.array(V["D"]["name"])
    o = F.sorted_order(d, nm)
    yes = lab[o] == "yes"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(np.arange(len(d)), d[o], color=[F.CARD if y else F.OTHER for y in yes], width=0.8)
    finish(ax)
    ax.set_xticks(np.arange(len(d)), nm[o], rotation=60, ha="right", rotation_mode="anchor", fontsize=5.4)
    for t, y in zip(ax.get_xticklabels(), yes):
        t.set_color(F.CARD if y else GREY)
        t.set_fontweight("bold" if y else "normal")
    ax.set_xlim(-0.8, len(d) - 0.2)
    s = {g: F.d_summary(d, lab == g) for g in ("yes", "no")}
    ax.legend(handles=[Patch(color=F.CARD, label=f"Physiologic: yes ({s['yes'][0]} of {s['yes'][1]} improved; mean {F.mfmt(s['yes'][2])} points)"),
                       Patch(color=F.OTHER, label=f"Physiologic: no ({s['no'][0]} of {s['no'][1]} improved; mean {F.mfmt(s['no'][2])} points)")],
              loc="upper right", frameon=False, fontsize=6.0, handlelength=1.2)
    ax.set_title(title, fontsize=7, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / fn, dpi=300)
    plt.close(fig)


def tab1(V, fn):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    F.panel_d(ax, V, legend_fs=6.0, tick_fs=5.4, note=False, wrap=False)
    ax.set_title(TITLE, fontsize=7, loc="left")
    fig.tight_layout()
    F.panel_d_note(ax)
    fig.savefig(OUT / fn, dpi=300, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


def make_all(V):
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    G = groups(V)
    got, rounding = summaries(V, G)
    tab1(V, TABS[0][0])
    grouped(V, G["area"], AREAS, TABS[1][0], f"{TITLE}, by clinical area (descriptive grouping; dashed line = group mean)")
    grouped(V, G["decision"], list(DECISION), TABS[2][0],
            f"{TITLE}, by type of treatment decision (descriptive grouping; dashed line = group mean)", wrap=WRAP)
    sorted_phys(V, G["physiologic"], TABS[3][0], f"{TITLE}, by physiologic label (blind trial labels; descriptive grouping)")
    print("wrote", OUT.relative_to(F.ROOT), [t for t, _ in TABS])
    return dict(tabs=TABS, decision=DECISION, summary={k: {g: list(v) for g, v in x.items()} for k, x in got.items()},
                expected={k: {g: list(v) for g, v in x.items()} for k, x in EXPECT.items()}, rounding_differences=rounding)


def main():
    grid, trials = F.load()
    V = F.compute(grid, trials)
    F.check_d(V)
    print(make_all(V)["summary"])


if __name__ == "__main__":
    main()
