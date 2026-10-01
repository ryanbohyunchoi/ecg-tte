#!/usr/bin/env python
"""Manuscript figures (first draft): main Figures 1-4 and eFigures 1-8.

All inputs are aggregate audit outputs (the same sources as the lab deck and the v19/v20 docs):
  - per-trial held-out balance and HRs: build_lab_deck.build_data() (claude-v18-embed-compare, covars2b expanded
    panel, v19 sensitivity estimands);
  - emulation-quality tiers: docs/v19/quality_tiers.json (primary set = 32 trials, tiers other than Limited);
  - plasmode: claude-v19-g2-simulation (per-cell relationship, clinically oriented "adverse" variant) and
    claude-v20-g2-ext (ECG-only PS, richer PS, true-HR checks, Monte Carlo SEs);
  - echo subset: claude-v20-echo-subset; MIMIC-IV: claude-v20-mimic-replication;
  - sensitivity: claude-v19-sens-outpatient/summary.csv.
Outputs: docs/paper/figures/{main,supplementary}/*.png (300 dpi) and *.pdf. No patient-level data are read
beyond what the aggregate builders already summarise; no counts 1-10 are displayed.

  python scripts/v20/make_paper_figures.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_lab_deck as DK  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUTM = ROOT / "docs/paper/figures/main"
OUTS = ROOT / "docs/paper/figures/supplementary"
NAVY, RED, GOLD, GREY, LGREY, DRED = "#0d1040", "#d9534f", "#c9a227", "#7a7c8c", "#d9dbe6", "#8f2d2a"
RUNGS = [("P1", "Demographic"), ("P5", "Five-diagnosis"), ("hdPS200", "High-dimensional"), ("clinical", "Clinical")]
CONFS = [("lvef", "LVEF"), ("ntprobnp", "NT-proBNP"), ("bmi", "BMI"), ("egfr", "eGFR"), ("all", "All")]
NB = 4000
plt.rcParams.update({"font.family": "Nimbus Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY,
                     "ytick.color": NAVY, "text.color": NAVY, "pdf.fonttype": 42, "savefig.dpi": 300})


# ---------------------------------------------------------------- helpers
def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", path.relative_to(ROOT))


def letter(ax, s, x=-0.12, y=1.04):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")


def arr(lst):
    return np.array([[np.nan if v is None else v for v in row] for row in lst], float)


def relred(B, E, idx, rng, nb=NB):
    """Relative reduction in mean |SMD| (%): 1 - mean_t(E_t) / mean_t(B_t); B, E = per-trial means."""
    B, E = np.asarray(B)[idx], np.asarray(E)[idx]
    ok = np.isfinite(B) & np.isfinite(E)
    B, E = B[ok], E[ok]
    est = 100 * (1 - E.mean() / B.mean())
    ii = rng.integers(0, len(B), (nb, len(B)))
    bs = 100 * (1 - E[ii].mean(1) / B[ii].mean(1))
    return est, *np.percentile(bs, [2.5, 97.5])


def signflip_exact(d):
    """One-sided exact sign-flip p: P(sum of randomly signed |d| >= observed sum); meet-in-the-middle."""
    d = np.asarray([x for x in d if np.isfinite(x)], float)
    n = len(d)
    S = d.sum()
    h = n // 2

    def sums(v):
        out = np.zeros(1)
        for x in v:
            out = np.concatenate([out + x, out - x])
        return out
    L, R = sums(np.abs(d[:h])), np.sort(sums(np.abs(d[h:])))
    cnt = 0
    for x in L:
        cnt += len(R) - np.searchsorted(R, S - 1e-12 - x, side="left")
    return cnt / 2.0 ** n


def bench_shuffle(la, lb, rb, ndraw=20000, seed=20261001):
    """Benchmark permutation: stat = mean(|la - q| - |lb - q|); p = P(null <= observed)."""
    la, lb, rb = map(np.asarray, (la, lb, rb))
    st = lambda q: np.mean(np.abs(la - q) - np.abs(lb - q))
    obs = st(rb)
    rng = np.random.default_rng(seed)
    null = np.array([st(rb[rng.permutation(len(rb))]) for _ in range(ndraw)])
    return float(np.mean(null <= obs + 1e-12))


def agree(L, SE, rb, rs):
    L, SE, rb, rs = map(np.asarray, (L, SE, rb, rs))
    ok = np.isfinite(L) & np.isfinite(SE)
    L, SE, rb, rs = L[ok], SE[ok], rb[ok], rs[ok]
    d = np.abs(L - rb)
    return dict(n=len(L), gap=d.mean(), r=np.corrcoef(L, rb)[0, 1] if len(L) > 2 else np.nan,
                ea=100 * np.mean(d <= 1.96 * rs), sd=100 * np.mean(d / np.sqrt(SE ** 2 + rs ** 2) < 1.96))


def fmt_p(p):
    return "P < .001" if p < 0.001 else f"P = {p:.3f}".replace("0.", ".") if p < 0.01 else f"P = {p:.2f}".replace("0.", ".")


# ---------------------------------------------------------------- data
D = DK.build_data()
TR = D["trials"]
TIER = [t["qt"]["tier"] for t in TR]
I32 = np.array([i for i, t in enumerate(TIER) if t != "Limited"])
I38 = np.arange(len(TR))
assert len(I32) == 32 and len(TR) == 38
RB = np.array([t["rb"] for t in TR])
RS = np.array([t["rs"] for t in TR])
VG = [v["g"] for v in D["vars"]]
GROUPS = list(dict.fromkeys(VG))


CI32 = pd.read_csv(A / "claude-v20-sens-primary32/ci.csv")


def ci(source, set_, rung, domain, arm):
    """Fixed-seed, paired-variable bootstrap CIs from SENS_PRIMARY32 (4,000 resamples; ratio of across-trial means)."""
    r = CI32[(CI32.source == source) & (CI32.set == set_) & (CI32.rung == rung) & (CI32.domain == domain) & (CI32.arm == arm)]
    assert len(r) == 1, (source, set_, rung, domain, arm)
    r = r.iloc[0]
    return float(r.est), float(r.lo), float(r.hi)


def tmean(rung, arm, cols=None):
    """Per-trial mean |SMD| over the 58-panel cells; cells where PS-alone |SMD| is missing are masked in every arm (as the deck)."""
    M = arr(D["bal"][rung][arm])
    # paired variable sets (as SENS_PRIMARY32): a cell counts only if observed under both PS alone and the ECG arm
    M[np.isnan(arr(D["bal"][rung]["base"])) | np.isnan(arr(D["bal"][rung]["ECG"]))] = np.nan
    if cols is not None:
        M = M[:, cols]
    with np.errstate(all="ignore"):
        return np.nanmean(M, 1)


def est(rung, arm):
    E = D["est"][rung][arm]
    return np.array([np.nan if x[0] is None else x[0] for x in E]), np.array([np.nan if x[1] is None else x[1] for x in E])


CHECK = {}


# ---------------------------------------------------------------- Figure 1
def figure1():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.axis("off")

    def box(x, y, w, h, txt, fc="white", ec=NAVY, tc=NAVY, fs=7.6, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc, ec=ec, lw=0.9))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal",
                linespacing=1.25)

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=0.9, shrinkA=0, shrinkB=0))
    # selection column
    box(0.5, 51, 25, 8, "99 candidate\ncardiovascular RCTs", bold=True)
    arrow(13, 51, 13, 47.5)
    box(0.5, 35.5, 25, 11.5, "Feasibility criteria\nactive comparator or proxy;\nEHR-ascertainable endpoint;\nidentifiable strategies; ≥300 with\nECG in smaller arm; ≥50 events", fs=6.1)
    arrow(13, 35.5, 13, 32)
    box(0.5, 25.5, 25, 6.5, "38 emulated", bold=True)
    arrow(13, 25.5, 13, 22.5)
    box(0.5, 12.5, 25, 10, "Emulation-quality grading\n(design deviations, comparator\nand outcome fidelity);\n6 limited excluded", fs=6.1)
    arrow(13, 12.5, 13, 10)
    box(0.5, 1.5, 25, 8.5, "32 analysed\n3 excellent, 12 good,\n17 moderate", fc=NAVY, tc="white", bold=True, fs=7.0)
    # data sources and representation
    box(30, 49, 30, 10, "YNHHS EHR (OMOP), 2011–2024\n+ raw 12-lead ECG (≤365 d before t0)\n+ echocardiography reports\n+ state death records", fs=6.3)
    arrow(45, 49, 45, 45.5)
    box(30, 31, 30, 14.5, "AI-ECG encoder (BCL, self-supervised)\n256-d embedding → 32 PCs\n\nPS: demographic → five-diagnosis →\nhigh-dimensional → clinical,\neach with vs without ECG;\n1:1 caliper matching", fs=6.1)
    arrow(26, 27.5, 29.5, 33)
    # analyses
    box(64.5, 48, 35, 11, "1  Covariate balance\nheld-out characteristics not in the PS\n(58 primary; ~330 expanded);\npermuted-ECG placebo", fs=6.1)
    box(64.5, 34.5, 35, 10.5, "2  Agreement with RCT results\nemulated vs published HR\n(RCT-DUPLICATE metrics);\nbenchmark-permutation test", fs=6.1)
    box(64.5, 21, 35, 10.5, "3  Plasmode simulation (known truth)\nhidden LVEF, NT-proBNP, BMI or eGFR;\n% of bias removed by the ECG\nvs the confounder itself", fs=6.1)
    for y in (53.5, 39.75, 26.25):
        arrow(60.5, 38, 64, y)
    # external validation
    box(30, 1.5, 69.5, 14, "External validation: MIMIC-IV (Beth Israel Deaconess hospital/ICU cohort)\n7 cardiovascular trials: PLATO, ARISTOTLE, ROCKET AF, TRANSFORM-HF,\nCOMET, SOAP II, ELITE II; PEPTIC as a negative-control trial\nsame ECG encoder; covariate balance and RCT agreement",
        fc="#f5f5f8", ec=GREY, fs=6.1)
    save(fig, OUTM / "figure1_study_design")


# ---------------------------------------------------------------- Figure 2
def figure2():
    rng = np.random.default_rng(0)
    fig = plt.figure(figsize=(7.2, 6.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1], hspace=0.55, wspace=0.55)
    # A: by domain
    ax = fig.add_subplot(gs[0, :])
    rows = [("All 58 characteristics", list(range(len(VG))))] + [(g, [j for j, x in enumerate(VG) if x == g]) for g in GROUPS]
    labs, ys = [], []
    for k, (g, cols) in enumerate(rows):
        y = len(rows) - 1 - k
        for a, col, mk, dy in (("ECG", RED, "o", 0.13), ("shufECG", GOLD, "^", -0.13)):
            e, lo, hi = ci("YNHHS", "S32", "P1", "All 58" if k == 0 else g, a)
            ax.plot([lo, hi], [y + dy, y + dy], color=col, lw=1.2)
            ax.plot(e, y + dy, mk, color=col, mfc=col if mk == "o" else "white", ms=5)
            if a == "ECG":
                ax.text(max(hi, 0) + 1.5, y + dy, f"{e:.1f}%", va="center", fontsize=6.8, color=col)
                if k == 0:
                    CHECK["fig2A all58 P1 32"] = (round(e, 1), round(lo, 1), round(hi, 1))
        labs.append(f"{g} ({len(cols)})")
        ys.append(y)
    ax.axvline(0, color=GREY, lw=0.8, ls="--")
    ax.set_yticks(ys, labs)
    ax.set_xlabel("Relative reduction in mean |SMD| vs PS alone, % (95% CI)")
    ax.set_xlim(-25, 45)
    ax.plot([], [], "o", color=RED, label="+ ECG")
    ax.plot([], [], "^", color=GOLD, mfc="white", label="+ permuted ECG")
    ax.legend(loc="lower right", frameon=False)
    letter(ax, "A", x=-0.32)
    # B: by PS specification
    ax = fig.add_subplot(gs[1, 0])
    for k, (rg, lab) in enumerate(RUNGS):
        y = len(RUNGS) - 1 - k
        for a, col, mk, dy in (("ECG", RED, "o", 0.13), ("shufECG", GOLD, "^", -0.13)):
            e, lo, hi = ci("YNHHS", "S32", rg, "All 58", a)
            ax.plot([lo, hi], [y + dy, y + dy], color=col, lw=1.2)
            ax.plot(e, y + dy, mk, color=col, mfc=col if mk == "o" else "white", ms=5)
            CHECK[f"fig2B {rg} {a}"] = (round(e, 1), round(lo, 1), round(hi, 1))
    ax.axvline(0, color=GREY, lw=0.8, ls="--")
    ax.set_yticks(range(len(RUNGS))[::-1], [l for _, l in RUNGS])
    ax.set_xlabel("Relative reduction in mean |SMD|, % (95% CI)")
    ax.set_xlim(-15, 25)
    ax.set_title("YNHHS, 32 trials", loc="left", fontsize=7.5, color=GREY)
    letter(ax, "B", x=-0.5)
    # C: MIMIC-IV
    S = json.load(open(A / "claude-v20-mimic-replication/summary/summary.json"))["balance"]
    ax = fig.add_subplot(gs[1, 1])
    mr = [("demo", "Demographic"), ("hdPS200", "High-dimensional"), ("clinical", "Clinical-lite")]
    for k, (rg, lab) in enumerate(mr):
        y = len(mr) - 1 - k
        for a, col, mk, dy in (("ECG", RED, "o", 0.13), ("permECG", GOLD, "^", -0.13)):
            e, lo, hi = ci("MIMIC-IV", "7 CV trials (all)", rg, "26 held-out", a)
            ax.plot([lo, hi], [y + dy, y + dy], color=col, lw=1.2)
            ax.plot(e, y + dy, mk, color=col, mfc=col if mk == "o" else "white", ms=5)
            CHECK[f"fig2C mimic {rg} {a}"] = (round(e, 1), round(lo, 1), round(hi, 1))
    ax.axvline(0, color=GREY, lw=0.8, ls="--")
    ax.set_yticks(range(len(mr))[::-1], [l for _, l in mr])
    ax.set_xlabel("Relative reduction in mean |SMD|, % (95% CI)")
    ax.set_xlim(-15, 25)
    ax.set_title("MIMIC-IV, 7 trials", loc="left", fontsize=7.5, color=GREY)
    letter(ax, "C", x=-0.5)
    save(fig, OUTM / "figure2_covariate_balance")


# ---------------------------------------------------------------- Figure 3
def figure3():
    fig = plt.figure(figsize=(7.2, 6.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.2, 1], hspace=0.6, wspace=0.55)
    # A: scatter
    ax = fig.add_subplot(gs[0, :2])
    Lb, Sb = est("P1", "base")
    Le, Se = est("P1", "ECG")
    for i in I32:
        ax.plot([RB[i], RB[i]], [Lb[i], Le[i]], color=LGREY, lw=0.8, zorder=1)
    ax.scatter(RB[I32], Lb[I32], s=16, facecolors="white", edgecolors=NAVY, lw=0.9, zorder=2, label="PS alone")
    ax.scatter(RB[I32], Le[I32], s=16, color=RED, zorder=3, label="PS + ECG")
    lim = (np.log(0.3), np.log(3.2))
    ax.plot(lim, lim, color=GREY, ls="--", lw=0.8)
    ticks = [0.33, 0.5, 0.67, 1, 1.5, 2, 3]
    ax.set_xticks(np.log(ticks), [str(t) for t in ticks])
    ax.set_yticks(np.log(ticks), [str(t) for t in ticks])
    ax.set_xlim(np.log(0.5), np.log(2.0))
    ax.set_ylim(*lim)
    ax.set_xlabel("RCT hazard ratio")
    ax.set_ylabel("Emulated hazard ratio (demographic PS)")
    gb, ge = agree(Lb[I32], Sb[I32], RB[I32], RS[I32]), agree(Le[I32], Se[I32], RB[I32], RS[I32])
    CHECK["fig3A gap base/ECG"] = (round(gb["gap"], 3), round(ge["gap"], 3))
    ax.text(0.02, 0.97, f"Mean |Δ log HR|: PS alone {gb['gap']:.3f}; + ECG {ge['gap']:.3f}\nr: {gb['r']:.2f} → {ge['r']:.2f}",
            transform=ax.transAxes, va="top", fontsize=7)
    ax.legend(loc="lower right", frameon=False)
    letter(ax, "A", x=-0.13)
    # B: mean |Δ| by rung
    ax = fig.add_subplot(gs[0, 2])
    xs = np.arange(len(RUNGS))
    for k, (rg, lab) in enumerate(RUNGS):
        Lb, Sb = est(rg, "base")
        Le, Se = est(rg, "ECG")
        ok = I32[np.isfinite(Lb[I32]) & np.isfinite(Le[I32])]
        db, de = np.abs(Lb[ok] - RB[ok]), np.abs(Le[ok] - RB[ok])
        p = signflip_exact(db - de)
        ps = bench_shuffle(Le[ok], Lb[ok], RB[ok])
        CHECK[f"fig3B {rg}"] = (round(db.mean(), 3), round(de.mean(), 3), int((de < db).sum()), round(p, 4), round(ps, 3))
        ax.bar(k - 0.18, db.mean(), 0.34, color="white", edgecolor=NAVY, lw=0.9)
        ax.bar(k + 0.18, de.mean(), 0.34, color=RED)
        ax.text(k, max(db.mean(), de.mean()) + 0.01, f"{int((de < db).sum())}/{len(ok)}\n{fmt_p(p)}\nperm. {ps:.2f}".replace("0.", "."),
                ha="center", fontsize=5.4, va="bottom")
    ax.set_xticks(xs, ["Demog.", "5-dx", "High-dim.", "Clinical"], rotation=35, ha="right")
    ax.set_ylabel("Mean |Δ log HR| vs RCT")
    ax.set_ylim(0, 0.42)
    ax.legend(handles=[Patch(facecolor="white", edgecolor=NAVY, label="PS alone"), Patch(facecolor=RED, label="+ ECG")],
              loc="upper right", frameon=False, fontsize=6.3)
    letter(ax, "B", x=-0.38)
    # C: by quality
    grp = [("Excellent or good (15)", [i for i in I32 if TIER[i] in ("Excellent", "Good")]),
           ("Moderate (17)", [i for i in I32 if TIER[i] == "Moderate"])]
    meth = [("P1", "base", "Demographic PS", "white", NAVY), ("P1", "ECG", "Demographic + ECG", RED, RED),
            ("clinical", "base", "Clinical PS", "#b9bbd0", NAVY), ("clinical", "ECG", "Clinical + ECG", DRED, DRED)]
    for m, (key, title, scale) in enumerate((("r", "Pearson r", 1), ("ea", "Estimate agreement, %", 100), ("sd", "Std. difference agreement, %", 100))):
        ax = fig.add_subplot(gs[1, m])
        for gi, (glab, idx) in enumerate(grp):
            idx = np.array(idx)
            for k, (rg, a, lab, fc, ec) in enumerate(meth):
                L, SE = est(rg, a)
                v = agree(L[idx], SE[idx], RB[idx], RS[idx])[key]
                CHECK[f"fig3C {glab} {lab} {key}"] = round(v, 2)
                ax.bar(gi + (k - 1.5) * 0.19, v, 0.18, color=fc, edgecolor=ec, lw=0.8, label=lab if gi == 0 else None)
        ax.set_xticks([0, 1], ["Excellent/\ngood", "Moderate"])
        ax.set_ylabel(title)
        ax.set_ylim(0, 1.0 if scale == 1 else 105)
        if m == 0:
            letter(ax, "C", x=-0.45)
    fig.legend(*fig.axes[-1].get_legend_handles_labels(), loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02))
    save(fig, OUTM / "figure3_rct_agreement")


# ---------------------------------------------------------------- Figure 4
def figure4():
    G = A / "claude-v19-g2-simulation"
    rel = pd.read_csv(G / "relationship_adverse.csv")
    ex = pd.read_csv(G / "excluded_cells_adverse.csv")
    rel = rel[~rel.set_index(["trial", "conf"]).index.isin(ex.set_index(["trial", "conf"]).index)]
    assert len(rel) == 107
    E = A / "claude-v20-g2-ext"
    tc = pd.read_csv(E / "pooled_trtC_cliniorient.csv")
    av = pd.read_csv(E / "ecg_added_value_cliniorient.csv")
    fig = plt.figure(figsize=(7.2, 3.3))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.35], wspace=0.32)
    ax = fig.add_subplot(gs[0, 0])
    cc = {"lvef": RED, "ntprobnp": NAVY, "bmi": GOLD, "egfr": GREY}
    lo_, hi_ = -20, 100
    for c, lab in CONFS[:4]:
        r = rel[rel.conf == c]
        y = r.prb_ECG.clip(lo_, hi_)
        ax.scatter(r.r2_partial, y, s=12, color=cc[c], alpha=0.85, label=lab, edgecolors="white", lw=0.3)
    ncl = int(((rel.prb_ECG < lo_) | (rel.prb_ECG > hi_)).sum())
    xx = np.linspace(0, 0.4, 10)
    ax.plot(xx, 100 * xx, color=NAVY, lw=0.9, ls="--")
    ax.text(0.398, 22, "100 × R²", fontsize=6.5, ha="right")
    ax.axhline(rel.prb_oracle.median(), color=NAVY, lw=0.6, ls=":")
    ax.text(0.005, rel.prb_oracle.median() + 2, f"oracle median {rel.prb_oracle.median():.0f}%", fontsize=6.3)
    ax.axhline(rel.prb_shufECG.median(), color=GOLD, lw=0.6, ls=":")
    ax.text(0.26, rel.prb_shufECG.median() - 7, f"permuted ECG {abs(rel.prb_shufECG.median()):.0f}%", fontsize=6.3, color=GOLD)
    ax.set_xlim(-0.01, 0.4)
    ax.set_ylim(lo_ - 3, hi_ + 3)
    ax.set_xlabel("Partial R² of ECG for the confounder (real data)")
    ax.set_ylabel("% of bias removed by adding the ECG")
    ax.legend(loc="upper left", frameon=False, fontsize=6.3, bbox_to_anchor=(0.0, 0.92), ncol=2)
    if ncl:
        ax.text(0.99, 0.02, f"{ncl} cells outside axis range shown at limit", transform=ax.transAxes, ha="right", fontsize=5.8, color=GREY)
    letter(ax, "A", x=-0.2)
    CHECK["fig4A cells"] = len(rel)
    ax = fig.add_subplot(gs[0, 1])
    bars = [("PS of ECG alone", RED), ("ECG added to demographic PS", DRED), ("ECG added to high-dim. PS", "#e8a29f"),
            ("ECG added to clinical PS", "#b06b68"), ("Oracle (confounder itself)", NAVY)]

    def v_only(arm, c):
        r = tc[(tc.analysis == "raw") & (tc.arm == arm) & (tc.conf == c)].iloc[0]
        return r.pct_vs_unmatched, r.mcse_vs_unmatched

    def v_add(ps, c):
        r = av[(av.analysis == "null-corrected") & (av.ps == ps) & (av.conf == c)].iloc[0]
        return r.ecg_added_pct_of_ps_bias, r.mcse
    w = 0.16
    for i, (c, lab) in enumerate(CONFS):
        vals = [v_only("ECGonly", c), v_add("base", c), v_add("hdPS", c), v_add("clin", c), v_only("oracle", c)]
        for k, ((v, m), (bl, col)) in enumerate(zip(vals, bars)):
            ax.bar(i + (k - 2) * w, v, w * 0.95, color=col, yerr=1.96 * m, error_kw=dict(lw=0.6, capsize=1.2), label=bl if i == 0 else None)
        CHECK[f"fig4B {c}"] = [round(v, 1) for v, _ in vals]
    ax.axhline(0, color=NAVY, lw=0.6)
    ax.set_xticks(range(len(CONFS)), [l for _, l in CONFS])
    ax.set_ylabel("% of confounder-induced bias removed")
    ax.set_ylim(-5, 105)
    ax.legend(frameon=False, fontsize=6.0, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    letter(ax, "B", x=-0.12)
    save(fig, OUTM / "figure4_plasmode")


# ---------------------------------------------------------------- eFigure 1
def efigure1():
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis("off")

    def box(x, y, w, h, txt, fc="white", tc=NAVY, fs=7.2, bold=False, ha="center"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.8", fc=fc, ec=NAVY, lw=0.9))
        ax.text(x + (w / 2 if ha == "center" else 1.2), y + h / 2, txt, ha=ha, va="center", fontsize=fs, color=tc,
                fontweight="bold" if bold else "normal", linespacing=1.3)

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=0.9))
    box(3, 60, 34, 8, "99 candidate cardiovascular RCTs\n(landmark trials; prior emulation\ninitiatives)", bold=True, fs=6.8)
    arrow(20, 60, 20, 45.5)
    box(45, 44, 52, 22, "Excluded, 61 [counts by reason to be filled from the screening log]\n"
        "• Placebo-only design without an accepted active proxy, n = [ ]\n"
        "• Primary endpoint not ascertainable from EHR data, n = [ ]\n"
        "• Treatment strategy not identifiable, n = [ ]\n"
        "• Insufficient size (<300 with ECG in smaller arm or <50 events), n = [ ]\n"
        "• Near-duplicate cohort (>80% shared records), n = [ ]\n"
        "• Not screened / previously analysed design variant, n = [ ]", fs=6.4, ha="left")
    arrow(20, 53, 44.5, 53)
    box(5, 37, 30, 8, "38 trials emulated\nAF 12, diabetes 9, HF 5,\nhypertension 5, ACS 2, other 5", bold=False, fs=6.8)
    arrow(20, 37, 20, 23.5)
    box(45, 24, 52, 12, "Excluded after emulation-quality grading, 6 (limited, ≥4 points)\n"
        "ALLHAT, ASCOT-BPLA, DECLARE-TIMI 58,\nONTARGET, REWIND, VALUE", fs=6.4, ha="left")
    arrow(20, 30, 44.5, 30)
    box(5, 13, 30, 10, "32 trials analysed (primary set)\n3 excellent, 12 good, 17 moderate\nAF 12, diabetes 7, HF 5,\nhypertension 2, ACS 2, other 4", fc=NAVY, tc="white", bold=True, fs=6.6)
    box(45, 6, 52, 12, "External validation (MIMIC-IV): 7 cardiovascular trials meeting the\nsame feasibility criteria + PEPTIC (negative control)\nUK Biobank: cardiac-MRI plasmode", fs=6.4, ha="left", fc="#f5f5f8")
    save(fig, OUTS / "efigure1_trial_flow")


# ---------------------------------------------------------------- eFigure 2: love plot
def efigure2():
    names = [v["lab"] for v in D["vars"]]
    med = {a: np.nanmedian(arr(D["bal"]["P1"][a])[I32], 0) for a in ("base", "ECG", "shufECG")}
    fig, ax = plt.subplots(figsize=(6.0, 9.0))
    y = np.arange(len(names))[::-1]
    for j in range(len(names)):
        ax.plot([min(med["base"][j], med["ECG"][j]), max(med["base"][j], med["ECG"][j])], [y[j]] * 2, color=LGREY, lw=1)
    ax.scatter(med["base"], y, s=14, facecolors="white", edgecolors=NAVY, lw=0.9, label="PS alone", zorder=3)
    ax.scatter(med["ECG"], y, s=14, color=RED, label="+ ECG", zorder=4)
    ax.scatter(med["shufECG"], y, s=12, marker="^", facecolors="white", edgecolors=GOLD, lw=0.8, label="+ permuted ECG", zorder=2)
    ax.axvline(0.1, color=RED, ls="--", lw=0.7)
    ax.set_yticks(y, names, fontsize=6)
    prev = None
    for j, g in enumerate(VG):
        if g != prev and j:
            ax.axhline(y[j] + 0.5, color=LGREY, lw=0.6)
        if g != prev:
            n = VG.count(g)
            ax.text(0.995, y[j] - (n - 1) / 2, g, fontsize=6.3, color=GREY, va="center", ha="right", transform=ax.get_yaxis_transform())
        prev = g
    ax.set_xlim(0, 0.42)
    ax.set_ylim(-1, len(names))
    ax.set_xlabel("|SMD| after matching (median across 32 trials; demographic PS)")
    ax.legend(loc="lower center", frameon=False, bbox_to_anchor=(0.5, 1.0), ncol=3)
    save(fig, OUTS / "efigure2_loveplot_58")


# ---------------------------------------------------------------- eFigure 3: expanded panel by bucket
def efigure3():
    rng = np.random.default_rng(1)
    ev = D["exp"]["vars"]
    bk = D["exp"]["buckets"]
    X = {a: arr(D["exp"]["smd"]["P1"][a]) for a in ("base", "ECG", "shufECG")}
    have = np.isfinite(X["base"][I32]).any(0)
    rows = [("All expanded characteristics", [j for j in range(len(ev)) if have[j]])] + [(b, [j for j, v in enumerate(ev) if v["b"] == b and have[j]]) for b in bk]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for k, (b, cols) in enumerate(rows):
        yy = len(rows) - 1 - k
        with np.errstate(all="ignore"):
            mb = np.nanmean(X["base"][:, cols], 1)
            for a, col, mk, dy in (("ECG", RED, "o", 0.13), ("shufECG", GOLD, "^", -0.13)):
                e, lo, hi = relred(mb, np.nanmean(X[a][:, cols], 1), I32, rng)
                ax.plot([lo, hi], [yy + dy] * 2, color=col, lw=1.2)
                ax.plot(e, yy + dy, mk, color=col, mfc=col if mk == "o" else "white", ms=5)
                if k == 0:
                    CHECK[f"efig3 all {a}"] = (round(e, 1), round(lo, 1), round(hi, 1))
    ax.axvline(0, color=GREY, ls="--", lw=0.8)
    ax.set_yticks(range(len(rows))[::-1], [f"{b} ({len(c)})" for b, c in rows])
    ax.set_xlabel("Relative reduction in mean |SMD| vs demographic PS alone, % (95% CI); 32 trials")
    ax.plot([], [], "o", color=RED, label="+ ECG")
    ax.plot([], [], "^", color=GOLD, mfc="white", label="+ permuted ECG")
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    save(fig, OUTS / "efigure3_expanded_panel")


# ---------------------------------------------------------------- eFigure 4: forest, 38 trials
def efigure4():
    order = sorted(I38, key=lambda i: (["Excellent", "Good", "Moderate", "Limited"].index(TIER[i]), TR[i]["area"], TR[i]["name"]))
    Lb, Sb = est("P1", "base")
    Le, Se = est("P1", "ECG")
    fig, ax = plt.subplots(figsize=(6.6, 9.4))
    lo, hi = math.log(0.2), math.log(5)
    clip = lambda v: min(max(v, lo), hi)
    for r, i in enumerate(order):
        y = len(order) - 1 - r
        a, b = RB[i] - 1.96 * RS[i], RB[i] + 1.96 * RS[i]
        ax.add_patch(plt.Rectangle((a, y - 0.4), b - a, 0.8, color=LGREY, lw=0))
        ax.plot([RB[i]] * 2, [y - 0.4, y + 0.4], color=NAVY, lw=1.6)
        for L, S, col, dy, mfc in ((Lb, Sb, NAVY, 0.15, "white"), (Le, Se, RED, -0.15, RED)):
            ax.plot([clip(L[i] - 1.96 * S[i]), clip(L[i] + 1.96 * S[i])], [y + dy] * 2, color=col, lw=0.9)
            ax.plot(clip(L[i]), y + dy, "o", ms=3.5, color=col, mfc=mfc, mew=0.8)
        tl = TIER[i]
        ax.text(lo - 0.05, y, f"{TR[i]['name']}", ha="right", va="center", fontsize=6.3, color=GREY if tl == "Limited" else NAVY)
        ax.text(hi + 0.05, y, tl, ha="left", va="center", fontsize=6.0, color=GREY if tl == "Limited" else NAVY)
    ax.axvline(0, color=GREY, ls=":", lw=0.7)
    t = [0.25, 0.5, 1, 2, 4]
    ax.set_xticks(np.log(t), [str(x) for x in t])
    ax.set_xlim(lo, hi)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_ylim(-1, len(order))
    ax.set_xlabel("Hazard ratio (log scale); grey band, RCT 95% CI; bar, RCT estimate")
    ax.plot([], [], "o", color=NAVY, mfc="white", label="PS alone (demographic)")
    ax.plot([], [], "o", color=RED, label="+ ECG")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=2)
    save(fig, OUTS / "efigure4_forest_38")


# ---------------------------------------------------------------- eFigure 8: sensitivity analyses
def efigure8_sens():
    S = pd.read_csv(A / "claude-v19-sens-outpatient/summary.csv")
    fig = plt.figure(figsize=(7.2, 3.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[0.8, 1.4], wspace=0.35)
    ax = fig.add_subplot(gs[0, 0])
    sets = [("OUT-29 all (same trials)", "All initiators"), ("OUT-29 outpt", "Outpatient initiators")]
    for k, (s, lab) in enumerate(sets):
        r = S[(S.set == s) & (S.ps == "P1") & (S.metric == "lt01")].iloc[0]
        ax.bar(k - 0.25, r.base, 0.24, color="white", edgecolor=NAVY)
        ax.bar(k, r.ecg, 0.24, color=RED)
        ax.bar(k + 0.25, r.shuf, 0.24, color="white", edgecolor=GOLD, hatch="///")
        ax.text(k, max(r.base, r.ecg) + 1.2, f"+{r.d_ecg_minus_base:.1f} pts\n{r.k_better}; {fmt_p(r.p)}", ha="center", fontsize=6.2)
        CHECK[f"efig5A {lab}"] = (round(r.base, 1), round(r.ecg, 1), round(r.d_ecg_minus_base, 1))
    ax.set_xticks([0, 1], [l for _, l in sets])
    ax.set_ylim(40, 66)
    ax.set_ylabel("% held-out characteristics |SMD| < 0.1")
    ax.set_title("29 outpatient-RCT trials; demographic PS", loc="left", fontsize=7, color=GREY)
    ax.legend(handles=[Patch(facecolor="white", edgecolor=NAVY, label="PS alone"), Patch(facecolor=RED, label="+ ECG"),
                       Patch(facecolor="white", edgecolor=GOLD, hatch="///", label="+ permuted ECG")], frameon=False, fontsize=6, loc="upper right")
    letter(ax, "A", x=-0.3)
    ax = fig.add_subplot(gs[0, 1])
    estims = [("itt", "Initiation\n(primary)"), ("outpt", "Outpatient\ninitiators"), ("pp_ipcw_365", "Per-protocol\n(IPCW)"),
              ("pp_ipcw_switch", "Switch-only\n(IPCW)"), ("landmark90", "90-day\nlandmark"), ("runin90", "90-day\nrun-in")]

    def getE(e, a):
        if e == "itt":
            return est("P1", a)
        L = D["sens"][e]["P1"][a]
        return (np.array([np.nan if x is None else x[0] for x in L]), np.array([np.nan if x is None else x[1] for x in L]))
    for k, (e, lab) in enumerate(estims):
        Lb, _ = getE(e, "base")
        Le, _ = getE(e, "ECG")
        ok = I32[np.isfinite(Lb[I32]) & np.isfinite(Le[I32])]
        db, de = np.abs(Lb[ok] - RB[ok]), np.abs(Le[ok] - RB[ok])
        ax.bar(k - 0.18, db.mean(), 0.34, color="white", edgecolor=NAVY)
        ax.bar(k + 0.18, de.mean(), 0.34, color=RED)
        ax.text(k, max(db.mean(), de.mean()) + 0.01, f"n={len(ok)}\n{int((de < db).sum())} closer", ha="center", fontsize=5.8)
        CHECK[f"efig5B {e}"] = (len(ok), round(db.mean(), 3), round(de.mean(), 3))
    ax.set_xticks(range(len(estims)), [l for _, l in estims], fontsize=6.3)
    ax.set_ylabel("Mean |Δ log HR| vs RCT")
    ax.set_ylim(0, 0.62)
    ax.legend(handles=[Patch(facecolor="white", edgecolor=NAVY, label="PS alone"), Patch(facecolor=RED, label="+ ECG")],
              frameon=False, loc="upper left", fontsize=6.5)
    ax.set_title("Primary set (32 trials; estimable trials shown); demographic PS", loc="left", fontsize=7, color=GREY)
    letter(ax, "B", x=-0.12)
    save(fig, OUTS / "efigure8_sensitivity")


# ---------------------------------------------------------------- eFigure 6: echo subset
def efigure6():
    P = pd.read_csv(A / "claude-v20-echo-subset/pooled.csv")
    P = P[(P.set == 32) & (P.phys == "phys1")]
    fig = plt.figure(figsize=(7.2, 3.0))
    gs = fig.add_gridspec(1, 2, wspace=0.35)
    ax = fig.add_subplot(gs[0, 0])
    rl = [("P1", "Demog."), ("P5", "5-dx"), ("hdPS200", "High-dim."), ("clinical", "Clinical")]
    for si, (sub, lab, off) in enumerate((("E", "LVEF subset", -0.2), ("N", "NT-proBNP subset", 0.2))):
        for k, (rg, _) in enumerate(rl):
            r = P[(P.subset == sub) & (P.rung == rg)]
            if not len(r):
                continue
            r = r.iloc[0]
            den = r.asmd_def_base - r.asmd_def_phys1
            se = 100 * (r.asmd_def_base - r.asmd_def_ECG) / den
            sp = 100 * (r.asmd_def_base - r.asmd_def_shufECG) / den
            ax.bar(k + off - 0.09, se, 0.17, color=RED if sub == "E" else DRED, label=f"+ ECG, {lab}" if k == 0 else None)
            ax.bar(k + off + 0.09, sp, 0.17, color="white", edgecolor=GOLD, hatch="///", label=f"+ permuted ECG, {lab}" if k == 0 else None)
            if rg == "P1":
                CHECK[f"efig6A {sub}"] = (round(se, 1), round(sp, 1))
    ax.axhline(0, color=NAVY, lw=0.6)
    ax.set_xticks(range(len(rl)), [l for _, l in rl])
    ax.set_ylabel("% of measured-physiology imbalance closed\n(relative to adjusting for it)")
    ax.legend(frameon=False, fontsize=5.8, loc="upper right")
    ax.set_ylim(-20, 105)
    letter(ax, "A", x=-0.25)
    ax = fig.add_subplot(gs[0, 1])
    mks = {"P1": "o", "P5": "s", "hdPS200": "^", "clinical": "D"}
    for si, (sub, col) in enumerate((("E", RED), ("N", NAVY))):
        for k, (rg, lab) in enumerate(rl):
            r = P[(P.subset == sub) & (P.rung == rg)]
            if not len(r):
                continue
            r = r.iloc[0]
            x = r.r2_partial_w + (k - 1.5) * 0.0025
            ax.errorbar(x, r.F_corr, yerr=[[r.F_corr - r.F_corr_lo], [r.F_corr_hi - r.F_corr]], fmt=mks[rg], color=col, ms=4,
                        lw=0.8, capsize=1.5, mfc=col if sub == "E" else "white")
    ax.plot([0, 0.3], [0, 0.3], color=GREY, ls="--", lw=0.8)
    ax.axhline(0, color=GREY, lw=0.5)
    ax.set_xlim(0.05, 0.3)
    ax.set_xlabel("Plasmode prediction (partial R² of ECG)")
    ax.set_ylabel("Placebo-corrected share of HR shift, F")
    h = [plt.Line2D([], [], color=RED, marker="o", ls="", label="LVEF subset"),
         plt.Line2D([], [], color=NAVY, marker="o", mfc="white", ls="", label="NT-proBNP subset")]
    h += [plt.Line2D([], [], color=GREY, marker=mks[rg], ls="", label=lab) for rg, lab in rl]
    ax.legend(handles=h, frameon=False, fontsize=5.8, loc="upper left", ncol=2)
    letter(ax, "B", x=-0.2)
    save(fig, OUTS / "efigure6_echo_subset")


# ---------------------------------------------------------------- eFigure 7: MIMIC-IV per trial
def efigure7():
    M = A / "claude-v20-mimic-replication/results"
    names = DK.MNAME if hasattr(DK, "MNAME") else {}
    order = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2", "peptic"]
    fig = plt.figure(figsize=(7.2, 3.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[0.9, 1.3], wspace=0.08)
    axA, axB = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    lo, hi = math.log(0.2), math.log(5)
    clip = lambda v: min(max(v, lo), hi)
    labels = []
    for r, t in enumerate(order):
        d = pd.read_csv(M / f"{t}_arms.csv")
        d = d[(d.base == "demo") & (d["pop"] == "all")].set_index("arm")
        y = len(order) - 1 - r
        for a, col, mk, mfc in (("base", NAVY, "o", "white"), ("ECG", RED, "o", RED), ("permECG", GOLD, "^", "white")):
            axA.plot(d.loc[a, "pct_bal"], y, mk, color=col, mfc=mfc, ms=4.5)
        rb, rs = float(d.iloc[0].rct_loghr), float(d.iloc[0].rct_se)
        axB.add_patch(plt.Rectangle((rb - 1.96 * rs, y - 0.4), 3.92 * rs, 0.8, color=LGREY, lw=0))
        axB.plot([rb] * 2, [y - 0.4, y + 0.4], color=NAVY, lw=1.6)
        for k, (a, col, mk, mfc) in enumerate((("base", NAVY, "o", "white"), ("ECG", RED, "o", RED), ("permECG", GOLD, "^", "white"))):
            l, s = d.loc[a, "loghr"], d.loc[a, "se"]
            yy = y + 0.2 - 0.2 * k
            axB.plot([clip(l - 1.96 * s), clip(l + 1.96 * s)], [yy] * 2, color=col, lw=0.8)
            axB.plot(clip(l), yy, mk, color=col, mfc=mfc, ms=3.5, mew=0.8)
        meas = str(d.iloc[0].rct_measure).split(" ")[0]
        labels.append(names.get(t, t) + ("" if meas == "HR" else f" [{meas}]"))
    axA.set_yticks(range(len(order))[::-1], labels)
    axA.set_xlabel("% of 26 held-out characteristics |SMD| < 0.1")
    axA.set_xlim(20, 70)
    letter(axA, "A", x=-0.5)
    axB.set_yticks([])
    axB.spines["left"].set_visible(False)
    t_ = [0.25, 0.5, 1, 2, 4]
    axB.set_xticks(np.log(t_), [str(x) for x in t_])
    axB.set_xlim(lo, hi)
    axB.axvline(0, color=GREY, ls=":", lw=0.7)
    axB.set_xlabel("Hazard ratio (log scale)")
    letter(axB, "B", x=0.0)
    for ax_ in (axA, axB):
        ax_.set_ylim(-0.7, len(order) - 0.3)
    axA.plot([], [], "o", color=NAVY, mfc="white", label="PS alone")
    axA.plot([], [], "o", color=RED, label="+ ECG")
    axA.plot([], [], "^", color=GOLD, mfc="white", label="+ permuted ECG")
    fig.legend(*axA.get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.06))
    save(fig, OUTS / "efigure7_mimic_per_trial")


# ---------------------------------------------------------------- eFigure 5: simulation robustness
def efigure5_sim():
    E = A / "claude-v20-g2-ext"
    fig = plt.figure(figsize=(7.2, 3.0))
    gs = fig.add_gridspec(1, 2, wspace=0.35)
    ax = fig.add_subplot(gs[0, 0])
    files = [("pooled_hr0.6.csv", "0.6"), ("pooled_hr0.8_subset.csv", "0.8"), ("pooled_hr1.0.csv", "1.0")]
    for k, (f, lab) in enumerate(files):
        p = pd.read_csv(E / f)
        p = p[(p.analysis == "raw") & (p.conf == "all")].set_index("arm")
        for j, (a, col, nm) in enumerate((("ECG", RED, "Demographic PS + ECG"), ("ECGonly", DRED, "PS of ECG alone"), ("oracle", NAVY, "Oracle"))):
            ax.bar(k + (j - 1) * 0.26, p.loc[a, "pct_vs_base"], 0.24, color=col, yerr=1.96 * p.loc[a, "mcse_vs_base"],
                   error_kw=dict(lw=0.6, capsize=1.2), label=nm if k == 0 else None)
        CHECK[f"efig8A hr{lab}"] = round(p.loc["ECG", "pct_vs_base"], 1)
    ax.set_xticks(range(len(files)), [f"True HR {l}" for _, l in files])
    ax.set_ylabel("% of demographic-PS bias removed (± 1.96 MCSE)")
    ax.set_ylim(0, 105)
    ax.legend(frameon=False, fontsize=6.0, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    letter(ax, "A", x=-0.2)
    ax = fig.add_subplot(gs[0, 1])
    pf = pd.read_csv(E / "performance_cliniorient.csv")
    pf = pf[pf.conf == "all"].set_index("arm")
    arms = [("unmatched", "Unmatched"), ("base", "Demographic"), ("ECG", "+ ECG"), ("ECGonly", "ECG alone"), ("hdPS", "High-dim."),
            ("hdPSECG", "+ ECG"), ("clin", "Clinical"), ("clinECG", "+ ECG"), ("oracle", "Oracle")]
    cols = [GREY, NAVY, RED, DRED, NAVY, RED, NAVY, RED, NAVY]
    for k, ((a, lab), c) in enumerate(zip(arms, cols)):
        ax.bar(k, pf.loc[a, "coverage"], 0.7, color=c if "ECG" in a or a == "oracle" else "white", edgecolor=c,
               yerr=1.96 * pf.loc[a, "coverage_mcse"], error_kw=dict(lw=0.6, capsize=1.2))
    ax.axhline(95, color=GREY, ls="--", lw=0.7)
    ax.set_xticks(range(len(arms)), [l for _, l in arms], rotation=45, ha="right", fontsize=6.5)
    ax.set_ylabel("95% CI coverage of the true effect, %")
    ax.set_ylim(40, 100)
    letter(ax, "B", x=-0.2)
    CHECK["efig8B coverage ECG/oracle"] = (round(pf.loc["ECG", "coverage"], 1), round(pf.loc["oracle", "coverage"], 1))
    save(fig, OUTS / "efigure5_simulation_robustness")


if __name__ == "__main__":
    for f in (figure1, figure2, figure3, figure4, efigure1, efigure2, efigure3, efigure4, efigure5_sim, efigure6, efigure7, efigure8_sens):
        f()
    print(json.dumps(CHECK, indent=1, default=str))
