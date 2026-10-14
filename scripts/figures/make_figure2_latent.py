#!/usr/bin/env python
"""LATENT-RCT manuscript Figure 2 (covariate balance), updated design of 2026-10-13 / 2026-10-14 (pipeline.md):
version 1 cohorts, the 31-trial primary set "s31" (paper 1's 32, v19 tiers, minus PROTECT AF: excluded at feasibility, smaller arm
< 350; build_balance_explorer.trial_set), 1:1 nearest-neighbour matching on the PS logit (caliper 0.2), fixed C = 1,
the 54 non-coded held-out items with the leakage-corrected masks of pipeline.md section 6.

  A  love plot: median |SMD| across the 31 trials per held-out item; unmatched, PS-CVD5, PS-CVD5 + ECG; grouped by domain
  B  mean |SMD| by domain (mean across trials of each trial's domain mean), same arms; "All 54" = the ladder level
  C  PS ladder: PS-Demo, PS-CVD5, PS-CVD10, hdPS, PS-Clinical (no LVEF; 5-draw MI); unmatched (reference), PS alone, PS + ECG,
     PS + CLMBR-T, PS + CLMBR-T + ECG; labels = relative change in mean |SMD| with + ECG vs PS alone (paired by trial). No PS-Flags.
  D  per trial: change in % of items with |SMD| < 0.1, PS-CVD5 + ECG vs PS-CVD5 (paired items), exact one-sided sign-flip P (all 31).
     2026-10-14 (docs/queue/figure2D.md): bars coloured by type of treatment decision, a descriptive grouping (CARDIAC_PHYSIOLOGY:
     rhythm control, HF / RAAS drug choice vs the other 20); trial names on the x-axis; group counts and means in the legend (gated
     against EXPECT_D); no test of the group difference. The popup's other groupings: scripts/figures/make_figure2d_groupings.py.
Deck3 (docs/queue/QUEUE_2026_10_14_DECK3.md): display labels AI-ECG (the ECG embedding) and AI-EHR (CLMBR-T); no highlight band in
C; panel D legend "Physiology trials" / "Other" without drug lists and no footnote. Numbers unchanged.

Style and plotting code follow scripts/v20/make_paper_figures.py (figure2; copied, not imported: importing it rebuilds paper 1's
deck data). Statistics come from scripts/build_balance_explorer.py (Grid.block, pair_stats, the explorer's love-plot / domain /
ladder computations) on the grid used by the 2026-10-15 lab deck:
  audits/claude-v21-paper2/core/restricted_cells.parquet   every version 1 rung and arm (CLMBR-T arms included)
  audits/claude-v1-ps10/cells/restricted_cells.parquet      PS-CVD10
  audits/claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet   PS-Clinical (no LVEF), 5-draw MI (|SMD| averaged)
  audits/claude-v18-embed-compare/results.csv               unmatched |SMD| (as build_balance_explorer.load_grid)
Cells with fewer than 11 matched pairs are failed (missing). Every plotted value is re-derived from the integers embedded in the
lab deck HTML (the explorer's data); ladder levels, relative reductions and panel D are checked against the s31 Python summaries
(scripts/s31/s31_summaries.py) and the + ECG labels are gated against EXPECT_ECG (the s31 summary values).

Outputs: docs/paper/figures_latent/figure2_covariate_balance.{png,pdf} (300 dpi), panels/figure2_covariate_balance_{A..D}.{png,pdf};
panels/panelD_groupings/*.png (the deck's panel D popup); aggregate validation table: audits/claude-fig2d-20261014/figure2_values.json.
Aggregates only (no patient counts).

  python scripts/figures/make_figure2_latent.py
"""
import json
import os
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_balance_explorer as BE  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
MI_V1 = A / "claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet"
DECK = ROOT / "docs/presentation/ecg_tte_lab_2026_10_15.html"
OUT = ROOT / "docs/paper/figures_latent"
VALS = A / "claude-fig2d-20261014/figure2_values.json"  # (Figure 2D job; the s31 job's copy stays in claude-s31-20261014)
SUMS = A / "claude-s31-20261014"  # s31 Python summaries (scripts/s31/s31_summaries.py; S32 rows gated equal to the committed runs)
SET = "s31"
NAVY, RED, GOLD, GREY, LGREY = "#0d1040", "#d9534f", "#c9a227", "#7a7c8c", "#d9dbe6"
GREEN, PURPLE = "#2a7f62", "#7b4fa0"
RUNGS = [("P1", "PS-Demo"), ("P5", "PS-CVD5"), ("PS10", "PS-CVD10"), ("clinical_nolvef", "PS-Clinical\n(no LVEF, MI)"), ("hdPS200", "hdPS")]  # ordered by number of inputs (3, 8, 13, ~30, ~210); user decision 2026-10-14
# arm: (legend label, colour, marker, face); unmatched drawn as a cross
# display labels (deck3 queue, 2026-10-14): AI-ECG = the BCL ECG embedding (32 PCs), AI-EHR = CLMBR-T (64 PCs); analysis unchanged
ARMS = {"unmatched": ("Unmatched", GREY, "x", None), "base": ("PS alone", NAVY, "o", "white"), "ECG": ("PS + AI-ECG", RED, "o", RED),
        "CLMBR": ("PS + AI-EHR", GREEN, "s", "white"), "ECG+CLMBR": ("PS + AI-ECG + AI-EHR", PURPLE, "D", PURPLE)}
EXPECT_ECG = {"P1": 10.6, "P5": 8.7, "PS10": 3.8, "hdPS200": 7.1, "clinical_nolvef": 3.3}  # s31 summaries (docs/s31/S31_RESULTS.md)
# panel D grouping (docs/queue/figure2D.md, 2026-10-14): descriptive, by type of treatment decision; trials_meta "full" names.
# Cardiac-physiology = rhythm control + HF / RAAS drug choice; "Other" = the remaining 20 of s31 (anticoagulant / antithrombotic
# incl. LAA occlusion, glucose-, BP-, lipid-lowering, NSAID).
CARDIAC_PHYSIOLOGY = {"rhythm control": ["AF-CHF", "AFFIRM", "EAST-AFNET 4", "CABANA", "RAFT-AF"],
                      "HF / RAAS drug choice": ["PARADIGM-HF", "ELITE II", "TRANSFORM-HF", "COMET", "EMPEROR-Preserved", "VALIANT"]}
CARDIAC = [t for v in CARDIAC_PHYSIOLOGY.values() for t in v]
EXPECT_D = {"cardiac": (10, 11, 9.9), "other": (9, 20, -0.3), "all": (19, 31, 3.3)}  # (improved, trials, mean points); queue file item 9
CARD, OTHER = "#2f6db5", "#c9cbd6"  # bars; "other" tick labels use GREY (as the mock-up), the light bar grey is too faint for text
# deck3 (2026-10-14): short legend labels (bold, via mathtext), no drug lists, no footnote under the trial names
D_LEG = {"cardiac": r"$\bf{Physiology\ trials}$", "other": r"$\bf{Other}$"}
D_NOTE = "Trials grouped descriptively by type of treatment decision."  # no longer drawn (panel_d note=False by default)
FIG_H, ROW2_H, D_NAMES_H, HSPACE = 5.85, 1.12, 0.55, 0.5  # figure height (in), bottom-row height ratio, share of the D cell kept
# for trial names, row spacing (5.3 in, 0.82, -, 0.62 before the Figure 2D job)
GSHORT = {"Vitals & core labs": "Vitals, core labs", "Other labs": "Other labs", "Echo: LV structure": "LV structure",
          "Echo: LV function": "LV function", "Echo: diastolic / LA": "Diastolic / LA", "Echo: RV / pulmonary": "RV / pulmonary",
          "Echo: valves / aorta": "Valves / aorta"}
plt.rcParams.update({"font.family": "Nimbus Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY,
                     "ytick.color": NAVY, "text.color": NAVY, "pdf.fonttype": 42, "savefig.dpi": 300,
                     "mathtext.fontset": "custom", "mathtext.rm": "Nimbus Sans", "mathtext.bf": "Nimbus Sans:bold"})

# ---------------------------------------------------------------- helpers (scripts/v20/make_paper_figures.py)
PANEL_LETTER = {}  # id(axes) -> panel letter, filled by letter()


def save_panels(fig, path, pad=0.06):
    """Export each lettered panel as its own PNG/PDF in <dir>/panels/<stem>_<letter>.*.
    Axes without a letter join the most recently lettered panel (e.g. stacked sub-axes of one panel)."""
    groups, cur = {}, None
    for ax in fig.axes:
        cur = PANEL_LETTER.get(id(ax), cur)
        if cur is not None:
            groups.setdefault(cur, []).append(ax)
    if not groups:
        return
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    out = path.parent / "panels"
    out.mkdir(parents=True, exist_ok=True)
    for lt, axs in groups.items():
        bb = Bbox.union([a.get_tightbbox(r) for a in axs]).transformed(fig.dpi_scale_trans.inverted())
        bb = Bbox.from_extents(bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad)
        others = [a for a in fig.axes if a not in axs and a.get_visible()]
        hidden_legends = [lg for lg in fig.legends if lg.get_visible()]
        for a in others:
            a.set_visible(False)
        for lg in hidden_legends:
            lg.set_visible(False)
        for ext, kw in ((".png", dict(dpi=300)), (".pdf", {})):
            fig.savefig(out / f"{path.name}_{lt}{ext}", bbox_inches=bb, **kw)
        for a in others:
            a.set_visible(True)
        for lg in hidden_legends:
            lg.set_visible(True)
    print("  panels:", ", ".join(sorted(groups)))


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    save_panels(fig, path)
    plt.close(fig)
    print("wrote", path.relative_to(ROOT))


def letter(ax, s, x=-0.12, y=1.04):
    PANEL_LETTER[id(ax)] = s
    ax.text(x, y, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")


def fmt_p(p):
    return "P < .001" if p < 0.001 else f"P = {p:.3f}".replace("0.", ".") if p < 0.01 else f"P = {p:.2f}".replace("0.", ".")


def scatter(ax, x, y, arm, s=12, **kw):
    lab, col, mk, fc = ARMS[arm]
    if mk == "x":
        return ax.scatter(x, y, s=s, marker="x", color=col, lw=0.8, **kw)
    return ax.scatter(x, y, s=s, marker=mk, facecolors=fc, edgecolors=col, lw=0.8, **kw)


# ---------------------------------------------------------------- data (the lab deck's version 1 grid)
def load():
    """BE.load_grid with PS-Clinical (no LVEF) = the 5-draw MI cells (as build_lab_deck_1015.load_v1)."""
    old = BE.NOLVEF
    BE.NOLVEF = MI_V1
    try:
        g = BE.load_grid()
    finally:
        BE.NOLVEF = old
    trials = BE.trials_meta(g)
    return BE.Grid(g["G"], g["U"], g["ex"]), trials


def deck_grid():
    """the explorer data embedded in the lab deck (integers x 1e5), decoded with BE.Grid.from_data (version 1 cohorts)."""
    h = DECK.read_text()
    m = re.search(r"\nconst D = (\{.*?\});\n", h, flags=re.S)
    D = json.loads(m.group(1))
    return BE.Grid.from_data(D, "v1"), D


ITEMS = BE.items("54")
GROUPS = list(dict.fromkeys(BE.GROUP[BE.VN[j]] for j in ITEMS))


def love(grid, T, rg, arm):
    """explorer love plot (stat = median): per item, median across trials of the cell |SMD| (each arm's own observed items)."""
    M = grid.block("main", rg, arm, True)[np.ix_(T, ITEMS)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-missing items, if any
        return np.nanmedian(M, 0)


def per_trial_mean(grid, T, rg, arm, js):
    M = grid.block("main", rg, arm, True)[np.ix_(T, js)]
    ok = np.isfinite(M).any(1)
    return np.nanmean(M[ok], 1)


def has(grid, rg, arm):
    return arm == "unmatched" or ("main", rg, arm) in grid.G


def level(grid, T, rg, arm, js=None):
    """explorer ladder level / domain view (stat = mean): mean over trials of each trial's mean |SMD| on its observed items."""
    if not has(grid, rg, arm):
        return np.nan  # the deck embeds no CLMBR-T arms (those are checked against the Python summaries instead)
    return float(per_trial_mean(grid, T, rg, arm, ITEMS if js is None else js).mean())


def trial_dpct(grid, T, rg, a="ECG", b="base", thr=0.1):
    """per-trial change in % of items with |SMD| < thr (arm a vs b, items observed in both), as BE.pair_stats."""
    Ma, Mb = grid.block("main", rg, a, True)[np.ix_(T, ITEMS)], grid.block("main", rg, b, True)[np.ix_(T, ITEMS)]
    m = np.isnan(Ma) | np.isnan(Mb)
    n = (~m).sum(1)
    ok = n > 0
    pa = 100 * ((np.where(m, np.inf, Ma) < thr).sum(1))[ok] / n[ok]
    pb = 100 * ((np.where(m, np.inf, Mb) < thr).sum(1))[ok] / n[ok]
    return pa - pb


def compute(grid, trials):
    T = BE.trial_set(trials, SET)
    assert len(T) == 31 and not any(trials[i]["id"] == "protect-af" for i in T)
    V = {"A": {}, "B": {}, "C": {}, "D": {}, "k_set": len(T)}
    for a in ("unmatched", "base", "ECG"):
        V["A"][a] = love(grid, T, "P5", a)
    doms = [("All 54", ITEMS)] + [(gname, [j for j in ITEMS if BE.GROUP[BE.VN[j]] == gname]) for gname in GROUPS]
    for gname, js in doms:
        V["B"][gname] = {a: level(grid, T, "P5", a, js) for a in ("unmatched", "base", "ECG")}
        V["B"][gname]["n_items"] = len(js)
    for rg, _ in RUNGS:
        V["C"][rg] = {a: level(grid, T, rg, a) for a in ARMS}
        for a in ARMS:  # trials behind each ladder point (a trial drops out when its cell failed)
            V["C"][rg][f"k_{a}"] = len(per_trial_mean(grid, T, rg, a, ITEMS)) if has(grid, rg, a) else 0
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            r = BE.pair_stats(grid, "main", rg, a, "base", T, "54", True) if has(grid, rg, a) else dict(rr=np.nan, lo=np.nan, hi=np.nan, k=0)
            V["C"][rg][f"rr_{a}"] = (r["rr"], r["lo"], r["hi"], r["k"])
    d = trial_dpct(grid, T, "P5")
    r = BE.pair_stats(grid, "main", "P5", "ECG", "base", T, "54", True)
    assert len(d) == r["k"] and abs(d.mean() - r["dpts"]) < 1e-9 and int((d > 0).sum()) == r["better"]
    p = BE.signflip_1s(d)
    assert abs(p - r["p"]) < 1e-12
    assert len(d) == len(T)  # every s31 trial has both cells, so d is in trial-set order
    full = [trials[i]["full"] for i in T]
    assert set(CARDIAC) <= set(full) and len(set(CARDIAC)) == len(CARDIAC) == 11, set(CARDIAC) - set(full)
    V["D"] = dict(d=d, improved=int((d > 0).sum()), k=len(d), mean=float(d.mean()), p=p, pct_ref=r["pct_ref"], pct_arm=r["pct_arm"],
                  name=[trials[i]["name"] for i in T], full=full, area=[trials[i]["area"] for i in T], phys=[trials[i]["phys"] for i in T],
                  cardiac=np.array([f in CARDIAC for f in full]))
    return V


def d_summary(d, m):
    """(improved, trials, mean points) of a group of panel D trials."""
    return int((d[m] > 0).sum()), int(m.sum()), float(d[m].mean())


def sorted_order(d, names):
    """largest to smallest change; ties broken by trial name."""
    return np.lexsort((np.array(names), -np.round(d, 9)))


def mfmt(x):
    return f"{x:+.1f}".replace("-", "−")


def panel_d(ax, V, legend_fs=6.0, tick_fs=5.4, note=False, wrap=False):
    """panel D: per trial, PS-CVD5 + ECG vs PS-CVD5, change in % of items with |SMD| < 0.1; bars coloured by cardiac-physiology
    decision (CARDIAC_PHYSIOLOGY; descriptive). Shared by Figure 2 and the popup's first tab (make_figure2d_groupings.py)."""
    from matplotlib.patches import Patch
    D = V["D"]
    d, nm, cm = D["d"], np.array(D["name"]), D["cardiac"]
    o = sorted_order(d, nm)
    x = np.arange(len(d))
    ax.bar(x, d[o], color=[CARD if c else OTHER for c in cm[o]], width=0.8)
    ax.axhline(0, color=NAVY, lw=0.6)
    ax.set_xticks(x, nm[o], rotation=60, ha="right", rotation_mode="anchor", fontsize=tick_fs)
    ax.tick_params(axis="x", length=2, pad=1.5)
    for t, c in zip(ax.get_xticklabels(), cm[o]):
        t.set_color(CARD if c else GREY)
        t.set_fontweight("bold" if c else "normal")
    ax.set_xlim(-0.8, len(d) - 0.2)
    ax.set_ylim(min(-1.0, d.min() - 1.0), max(d.max() + 4.5, 20))  # headroom for the legend and the all-trials line
    sep = ":\n" if wrap else ": "
    lab = {k: f"{D_LEG[k]}{sep}{a} of {n} improved; mean {mfmt(m)} points" for k, (a, n, m) in
           (("cardiac", d_summary(d, cm)), ("other", d_summary(d, ~cm)))}
    lg = ax.legend(handles=[Patch(color=CARD, label=lab["cardiac"]), Patch(color=OTHER, label=lab["other"])], loc="upper right",
                   bbox_to_anchor=(1.0, 1.04), frameon=False, fontsize=legend_fs, handlelength=1.2, handletextpad=0.5, labelspacing=0.45,
                   borderaxespad=0.2)
    a, n, m = d_summary(d, np.ones(len(d), bool))
    ax.annotate(f"All {n} trials: {a} of {n} improved; mean {mfmt(m)} points; {fmt_p(D['p'])}", xy=(1, 0), xycoords=lg, xytext=(-2, -2),
                textcoords="offset points", ha="right", va="top", fontsize=legend_fs - 0.3, color=NAVY)
    ax.set_ylabel("Change in % of items\nwith |SMD| < 0.1", fontsize=6.6)
    ax.set_title("PS-CVD5 + AI-ECG vs PS-CVD5, per trial", fontsize=7, loc="left", x=-0.12)
    if note:
        panel_d_note(ax)
    return lab


def panel_d_note(ax):
    """the footnote, one line under the trial names (placed after a draw, in axes coordinates, so the panel export keeps it)."""
    fig = ax.figure
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    y0 = min(t.get_window_extent(r).y0 for t in ax.get_xticklabels())
    y = ax.transAxes.inverted().transform((0, y0 - 3 * fig.dpi / 72))[1]
    return ax.text(0.0, y, D_NOTE, transform=ax.transAxes, ha="left", va="top", fontsize=5.4, color=GREY, style="italic")


def check_d(V):
    """the queue file's expected panel D values (item 9); stop (do not adjust the grouping) if they differ."""
    d, cm = V["D"]["d"], V["D"]["cardiac"]
    got = {k: (a, n, round(m, 1)) for k, (a, n, m) in (("cardiac", d_summary(d, cm)), ("other", d_summary(d, ~cm)),
                                                         ("all", d_summary(d, np.ones(len(d), bool))))}
    if got != EXPECT_D:
        raise SystemExit(f"panel D grouping values differ from the expected values: got {got}, expected {EXPECT_D}")
    return got


def compare(V, W):
    """max |difference| between two computations of every plotted value (full precision vs the deck's embedded integers)."""
    dev = 0.0
    for a in V["A"]:
        dev = max(dev, float(np.nanmax(np.abs(V["A"][a] - W["A"][a]))))
        assert (np.isnan(V["A"][a]) == np.isnan(W["A"][a])).all()
    for gname in V["B"]:
        for a in ("unmatched", "base", "ECG"):
            dev = max(dev, abs(V["B"][gname][a] - W["B"][gname][a]))
    for rg in V["C"]:
        for a in ("unmatched", "base", "ECG"):
            dev = max(dev, abs(V["C"][rg][a] - W["C"][rg][a]))
    dev = max(dev, float(np.abs(np.sort(V["D"]["d"]) - np.sort(W["D"]["d"])).max()) / 100)
    rrdev = max(abs(V["C"][rg]["rr_ECG"][i] - W["C"][rg]["rr_ECG"][i]) for rg in V["C"] for i in range(3))
    return dev, rrdev


def summaries(V):
    """ladder levels, relative reductions and panel D against the s31 Python summaries (scripts/s31/s31_summaries.py: independent
    runs of the endpoint code, set S31): the v1 MI summary (every rung's PS alone / + ECG; PS-Clinical (no LVEF, MI) incl. the
    CLMBR-T arms) and scripts/v2_cohorts/summarize.py (cohort v1: CLMBR-T arms of PS-Demo, PS-CVD5, PS-CVD10, hdPS).
    Leakage-corrected, F1 applied."""
    import pandas as pd
    MC = pd.read_csv(SUMS / "summary_mi/contrasts.csv")
    ML = pd.read_csv(SUMS / "summary_mi/ladder.csv")
    VC = pd.read_csv(SUMS / "summary_v1/contrasts.csv")
    VL = pd.read_csv(SUMS / "summary_v1/ladder.csv")
    MC = MC[(MC.set == "S31") & (MC.config == "main") & MC.kind.isin(["within", "ladder"]) & (MC.rung_a == MC.rung_b) & (MC.arm_b == "base")]
    VC = VC[(VC.cohort == "v1") & (VC.set == "S31") & (VC.config == "main") & (VC.kind == "within") & (VC.rung_a == VC.rung_b) & (VC.arm_b == "base")]
    ML = ML[(ML.set == "S31") & (ML.config == "main") & (ML.panel.astype(str) == "54")]
    VL = VL[(VL.cohort == "v1") & (VL.set == "S31") & (VL.config == "main") & (VL.panel.astype(str) == "54")]
    rows, unchecked = [], []
    for rg, _ in RUNGS:
        mr = "clinical_nolvef_mi" if rg == "clinical_nolvef" else rg
        for a in ("base", "ECG", "CLMBR", "ECG+CLMBR"):
            src = ML[(ML.rung == mr) & (ML.arm == a)]
            if not len(src) and rg != "clinical_nolvef":
                src = VL[(VL.rung == rg) & (VL.arm == a)]
            if len(src) == 1:
                rows.append((f"C level {rg} {a}", V["C"][rg][a], float(src.mean_smd.iloc[0]), 5e-9))
            else:
                unchecked.append(f"C level {rg} {a}")
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            src = MC[(MC.rung_a == mr) & (MC.arm_a == a)]
            if not len(src):
                src = VC[(VC.rung_a == rg) & (VC.arm_a == a)]
            assert len(src) == 1, (rg, a, len(src))
            s = src.iloc[0]
            for i, c in enumerate(("relred54", "relred54_lo", "relred54_hi")):
                rows.append((f"C {c} {rg} {a}", V["C"][rg][f"rr_{a}"][i], float(s[c]), 1e-6))
    P5 = MC[(MC.rung_a == "P5") & (MC.arm_a == "ECG")].iloc[0]
    rows.append(("D mean change in % < 0.1", V["D"]["mean"], float(P5.lt01_54_diff), 1e-6))
    rows.append(("D trials improved", V["D"]["improved"], float(P5.lt01_54_better.split("/")[0]), 0))
    rows.append(("D P", V["D"]["p"], float(P5.lt01_54_p), 1e-9))
    rows.append(("D % < 0.1, PS-CVD5", V["D"]["pct_ref"], float(P5.lt01_54_b), 1e-6))
    rows.append(("D % < 0.1, + ECG", V["D"]["pct_arm"], float(P5.lt01_54_a), 1e-6))
    for a in ("unmatched", "base", "ECG"):
        rows.append((f"B All 54 = C level P5 {a}", V["B"]["All 54"][a], V["C"]["P5"][a], 1e-12))
    bad = [r for r in rows if not abs(r[1] - r[2]) <= r[3]]
    assert not bad, bad
    return dict(n_checked=len(rows), max_dev=max(abs(r[1] - r[2]) for r in rows), not_in_any_summary=unchecked)


# ---------------------------------------------------------------- figure
def figure2(V):
    fig = plt.figure(figsize=(7.4, FIG_H))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.1, 0.82, 1.18], height_ratios=[1, ROW2_H], hspace=HSPACE, wspace=0.95,
                          left=0.19, right=0.985, top=1 - 0.53 / FIG_H, bottom=0.42 / FIG_H)  # same margins in inches as at 5.3 in
    # shared legend (A, B and D use the first three arms; C all five)
    hs = []
    for a, (lab, col, mk, fc) in ARMS.items():
        hs.append(Line2D([], [], ls="none", marker=mk, ms=4.2 if mk != "D" else 3.6, mew=0.9, color=col, mfc=col if fc is None else fc, label=lab))
    fig.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.58, 0.995), ncol=5, frameon=False, fontsize=6.8, handletextpad=0.2, columnspacing=1.2)
    # A: love plot
    ax = fig.add_subplot(gs[:, 0])
    names = [BE.VARS[j][1] for j in ITEMS]
    groups = [BE.GROUP[BE.VN[j]] for j in ITEMS]
    med = [V["A"][a] for a in ("unmatched", "base", "ECG")]
    y = np.arange(len(names))[::-1]
    for j in range(len(names)):
        vals = [m[j] for m in med if np.isfinite(m[j])]
        if vals:
            ax.plot([min(vals), max(vals)], [y[j]] * 2, color=LGREY, lw=0.8, zorder=1)
    for a, m in zip(("unmatched", "base", "ECG"), med):
        scatter(ax, m, y, a, s=10, zorder={"unmatched": 2, "base": 3, "ECG": 4}[a])
    ax.axvline(0.1, color=RED, ls="--", lw=0.6)
    ax.set_yticks(y, names, fontsize=4.4)
    ax.tick_params(axis="y", length=1.5, pad=1)
    prev, start = None, 0
    bounds = []
    for j, gname in enumerate(groups + [None]):
        if gname != prev:
            if prev is not None:
                bounds.append((prev, start, j - 1))
            start, prev = j, gname
    for gname, j0, j1 in bounds:
        if j0:
            ax.axhline(y[j0] + 0.5, color=LGREY, lw=0.5)
        ax.text(1.02, (y[j0] + y[j1]) / 2, GSHORT[gname], transform=ax.get_yaxis_transform(), rotation=-90, ha="left", va="center",
                fontsize=5.0, color=RED, fontweight="bold")
    xmax = float(np.ceil(np.nanmax(med[0]) * 20) / 20)
    ax.set_xlim(0, max(0.3, xmax))
    ax.set_ylim(-0.8, len(names) - 0.2)
    ax.set_xlabel(f"|SMD| (median across {V['k_set']} trials)", fontsize=7)
    ax.set_title("PS-CVD5 ± AI-ECG, 54 held-out items", fontsize=7, loc="left", x=-0.55)
    letter(ax, "A", x=-0.75, y=1.01)
    # B: mean |SMD| by domain
    ax = fig.add_subplot(gs[0, 1])
    rows = list(V["B"])
    for k, gname in enumerate(rows):
        yy = len(rows) - 1 - k
        mm = [V["B"][gname][a] for a in ("unmatched", "base", "ECG")]
        ax.plot([min(mm), max(mm)], [yy, yy], color=LGREY, lw=0.8, zorder=1)
        for a, v in zip(("unmatched", "base", "ECG"), mm):
            scatter(ax, [v], [yy], a, s=14, zorder=3)
    labs = [f"{g if g == 'All 54' else GSHORT[g]} ({V['B'][g]['n_items']})" for g in rows]
    ax.set_yticks(range(len(rows))[::-1], labs, fontsize=6)
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.axvline(0.1, color=RED, ls="--", lw=0.6)
    ax.set_xlim(0.05, None)
    ax.set_xlabel(f"Mean |SMD| (mean across {V['k_set']} trials)", fontsize=7)
    ax.set_title("PS-CVD5 ± AI-ECG, by domain", fontsize=7, loc="left", x=-0.86)
    letter(ax, "B", x=-1.04)
    # C: PS ladder
    ax = fig.add_subplot(gs[0, 2])
    xs = np.arange(len(RUNGS))
    # deck3 (2026-10-14): no highlight band behind PS-CVD5
    U = [V["C"][rg]["unmatched"] for rg, _ in RUNGS]
    ax.plot(xs, U, "--", color=GREY, lw=0.8, zorder=1)
    scatter(ax, xs, U, "unmatched", s=12, zorder=2)
    offs = {"base": -0.24, "ECG": -0.08, "CLMBR": 0.08, "ECG+CLMBR": 0.24}
    for a, dx in offs.items():
        v = [V["C"][rg][a] for rg, _ in RUNGS]
        lab, col, mk, fc = ARMS[a]
        ax.plot(xs + dx, v, "-", color=col, lw=0.6, alpha=0.55, zorder=2)
        scatter(ax, xs + dx, v, a, s=11 if mk != "D" else 8, zorder=3)
    lo_y = np.floor((min(V["C"][rg][a] for rg, _ in RUNGS for a in offs) - 0.016) * 100) / 100
    for k, (rg, _) in enumerate(RUNGS):  # + ECG labels in one row at the foot of the panel
        rr = V["C"][rg]["rr_ECG"][0]
        ax.text(k, lo_y + 0.0025, f"−{rr:.1f}%" if rr >= 0 else f"+{-rr:.1f}%", ha="center", va="bottom", fontsize=5.1, color=RED, fontweight="bold")
    ax.set_xticks(xs, [l for _, l in RUNGS], rotation=35, ha="right", fontsize=5.8, rotation_mode="anchor")
    ax.set_xlim(-0.62, len(RUNGS) - 0.45)
    ax.set_ylim(max(0, lo_y), max(U) + 0.012)
    short = {rg: l.split("\n")[0] for rg, l in RUNGS}
    fewer = [f"{ARMS[a][0].replace('PS', short[rg], 1)}: {V['C'][rg]['k_' + a]} trials (failed cell)" for rg, _ in RUNGS for a in ARMS
             if a != "unmatched" and V["C"][rg]["k_" + a] < V["k_set"]]  # footnote whenever an arm rests on fewer trials than the set
    ax.set_ylabel(f"Mean |SMD| ({V['k_set']} trials" + ("*)" if fewer else ")"), fontsize=7)
    ax.set_title("PS ladder (fewer → more covariates)", fontsize=7, loc="left", x=-0.3)
    ax.text(0.99, 0.985, "red: relative change in mean\n|SMD| with + AI-ECG vs PS alone", transform=ax.transAxes, ha="right", va="top", fontsize=5.2,
            color=RED, linespacing=1.1)
    notes = (["* " + "; ".join(fewer)] if fewer else [])
    if notes:
        ax.text(-0.3, -0.42, "\n".join(notes), transform=ax.transAxes, ha="left", va="top", fontsize=5.0, color=GREY, linespacing=1.15)
    letter(ax, "C", x=-0.42)
    # D: per-trial change in % balanced (PS-CVD5 + ECG vs PS-CVD5), coloured by cardiac-physiology decision (descriptive); the
    # lower part of the bottom-row cell is left for the rotated trial names and the footnote
    ax = fig.add_subplot(gs[1, 1:].subgridspec(2, 1, height_ratios=[1, D_NAMES_H], hspace=0)[0])
    panel_d(ax, V)
    letter(ax, "D", x=-0.2)
    save(fig, OUT / "figure2_covariate_balance")


def main():
    os.umask(0o077)
    grid, trials = load()
    V = compute(grid, trials)
    eg, D = deck_grid()
    assert [t["id"] for t in D["trials"]] == [t["id"] for t in trials] and [t["s32"] for t in D["trials"]] == [t["s32"] for t in trials]
    W = compute(eg, trials)
    dev, rrdev = compare(V, W)
    print(f"full precision vs the deck's embedded integers: max |SMD| deviation {dev:.2e}; max relative-reduction deviation {rrdev:.2e}")
    assert dev < 1e-5 and rrdev < 0.05
    SM = summaries(V)
    print(f"vs the Python summaries: {SM['n_checked']} values, max deviation {SM['max_dev']:.2e}; not in any summary: {SM['not_in_any_summary']}")
    got = {rg: round(V["C"][rg]["rr_ECG"][0], 1) for rg, _ in RUNGS}
    print("+ ECG labels:", got)
    assert got == EXPECT_ECG, (got, EXPECT_ECG)
    # display roundings must agree too (3 decimals for |SMD|, 1 decimal for %)
    for rg, _ in RUNGS:
        for a in ("unmatched", "base", "ECG"):
            assert f"{V['C'][rg][a]:.3f}" == f"{W['C'][rg][a]:.3f}", (rg, a)
        assert f"{V['C'][rg]['rr_ECG'][0]:.1f}" == f"{W['C'][rg]['rr_ECG'][0]:.1f}", rg
    gotD = check_d(V)
    gotDW = check_d(W)  # the same groups from the deck's embedded integers
    assert gotD == gotDW and W["D"]["full"] == V["D"]["full"]
    print("panel D groups (improved, trials, mean):", gotD)
    figure2(V)
    import make_figure2d_groupings as G  # the popup's tabs (the same per-trial values)
    GV = G.make_all(V)
    out = dict(
        basis="version 1 cohorts; the 31-trial primary set s31 (paper 1's 32, v19 tiers, minus PROTECT AF: excluded at feasibility); main configuration (1:1, caliper 0.2, C = 1); 54 items, leakage-corrected masks",
        A_median_all_items={a: dict(median_of_items=round(float(np.nanmedian(V["A"][a])), 4), n_items_plotted=int(np.isfinite(V["A"][a]).sum()))
                            for a in V["A"]},
        A_items={BE.VARS[j][1]: {a: (None if not np.isfinite(V["A"][a][i]) else round(float(V["A"][a][i]), 4)) for a in V["A"]} for i, j in enumerate(ITEMS)},
        B={g: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in x.items()} for g, x in V["B"].items()},
        C={rg: {k: (round(v, 6) if isinstance(v, float) else v if isinstance(v, int) else [round(float(u), 4) for u in v[:3]] + [int(v[3])])
                for k, v in x.items() if not isinstance(v, dict)} for rg, x in V["C"].items()},
        k_set=V["k_set"],
        D={k: (v if isinstance(v, int) else round(float(v), 6)) for k, v in V["D"].items() if k in ("improved", "k", "mean", "p", "pct_ref", "pct_arm")},
        D_per_trial={f: round(float(x), 6) for f, x in zip(V["D"]["full"], V["D"]["d"])},  # per-trial aggregates (no patient counts)
        D_groups=dict(cardiac_physiology=CARDIAC_PHYSIOLOGY, summary={k: list(v) for k, v in gotD.items()}, expected={k: list(v) for k, v in EXPECT_D.items()},
                      popup_tabs=GV),
        check=dict(embedded_vs_full_max_smd_dev=dev, embedded_vs_full_max_rr_dev=rrdev, ecg_labels=got, expected=EXPECT_ECG, summaries=SM))
    VALS.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(VALS, "w"), indent=1)
    print("wrote", VALS)
    for rg, lab in RUNGS:
        c = V["C"][rg]
        print(f"  {lab.replace(chr(10), ' '):28s} U {c['unmatched']:.3f}  PS {c['base']:.3f}  +ECG {c['ECG']:.3f}  +CLMBR-T {c['CLMBR']:.3f}  "
              f"+both {c['ECG+CLMBR']:.3f}  | rr ECG {c['rr_ECG'][0]:.1f} ({c['rr_ECG'][1]:.1f} to {c['rr_ECG'][2]:.1f})  "
              f"CLMBR-T {c['rr_CLMBR'][0]:.1f}  both {c['rr_ECG+CLMBR'][0]:.1f}")
    print("  B:", {g: tuple(round(V["B"][g][a], 3) for a in ("unmatched", "base", "ECG")) for g in V["B"]})
    print("  D:", {k: V["D"][k] for k in ("improved", "k", "mean", "p", "pct_ref", "pct_arm")})


if __name__ == "__main__":
    main()
