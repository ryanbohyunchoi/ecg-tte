#!/usr/bin/env python
"""paper2 figures (step F): main Figures 1-5, eFigures 1-5 and a self-contained HTML gallery.

Inputs: only aggregate (trial-level, counts 1-10 suppressed) outputs in
/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/:
  core/      sensitivity.csv, headline.csv, headline_domains.csv, per_trial.csv (m54 / absd / domain means only),
             labels_physiologic.csv, labels_domain.csv, labels_per_trial.csv, flagscv.csv, retention_sens.csv,
             q_counts.csv, log.json (per-trial PS-Flags feature counts only)
  plasmode/  pooled_trtC_cliniorient_p5.csv, added_value_p5.csv, performance_trtC_cliniorient_p5.csv
  mimic/     summary/summary.json, windowfix/summary/balance.csv
plus docs/v19/quality_tiers.json (tiers, areas) in the repo.
Never read: restricted_* files, cells / parquet files, anything under review/ (enforced by rd()).
No patient counts are plotted; per-trial retention and ESS are never plotted.

Outputs: docs/paper/figures_paper2/{main,supplementary}/*.png (300 dpi) + *.pdf, per-panel exports in */panels/,
docs/paper/figures_paper2/index.html (base64 gallery), copied to the audits folder (umask 077).

  /mnt/raid0/rbc58/ecg-tte/software/tte-analysis/bin/python scripts/v21/make_paper2_figures.py
"""
import base64
import datetime
import html
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUD = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2")
CORE, PLAS, MIM = AUD / "core", AUD / "plasmode", AUD / "mimic"
OUT = ROOT / "docs/paper/figures_paper2"
OUTM, OUTS = OUT / "main", OUT / "supplementary"

# ---------------------------------------------------------------- style (as scripts/v20/make_paper_figures.py)
NAVY, RED, GOLD, GREY, LGREY, DRED = "#0d1040", "#d9534f", "#c9a227", "#7a7c8c", "#d9dbe6", "#8f2d2a"
BLUE = "#2f6db5"      # CLMBR-T (new in paper2; CVD-checked against RED / NAVY / GOLD, worst OKLab dE 11.8)
LBLUE = "#8fb3e0"     # CLMBR-T 32-PC sensitivity
CMAP = plt.get_cmap("PuOr")  # diverging, CVD-safe: orange = worse, purple = better, white = 0
plt.rcParams.update({"font.family": "Nimbus Sans", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY,
                     "ytick.color": NAVY, "text.color": NAVY, "pdf.fonttype": 42, "savefig.dpi": 300})

# ---------------------------------------------------------------- guarded reads
SOURCES = set()


def _guard(p):
    p = Path(p)
    bad = ("restricted" in p.name or p.suffix == ".parquet" or "review" in p.parts or p.name.startswith("cells")
           or "flagscv_cells" in p.name)
    assert not bad, f"forbidden input {p}"
    SOURCES.add(str(p))
    return p


def rd(p):
    return pd.read_csv(_guard(p))


def rj(p):
    with open(_guard(p)) as f:
        return json.load(f)


SENS = rd(CORE / "sensitivity.csv")
HEAD = rd(CORE / "headline.csv")
HD = rd(CORE / "headline_domains.csv")
PT = rd(CORE / "per_trial.csv")[["key", "in_S32", "rung", "config", "arm", "m54", "absd", "suppressed_lt11"]]
LP = rd(CORE / "labels_physiologic.csv")
LD = rd(CORE / "labels_domain.csv")
LPT = rd(CORE / "labels_per_trial.csv")
FCV = rd(CORE / "flagscv.csv")
RET = rd(CORE / "retention_sens.csv")
QC = rd(CORE / "q_counts.csv")
FLAGLOG = rj(CORE / "log.json")
QT = rj(ROOT / "docs/v19/quality_tiers.json")["trials"]
NAME = {t["key"]: t["trial"] for t in QT}
TIER = {t["key"]: t["tier"].split(" - ")[0] for t in QT}
AREA = {t["key"]: t["area"] for t in QT}
S32KEYS = [k for k in NAME if TIER[k] != "Limited"]
assert len(S32KEYS) == 32

DOMS = ["Vitals & core labs", "Other labs", "Echo: LV structure", "Echo: LV function", "Echo: diastolic / LA",
        "Echo: RV / pulmonary", "Echo: valves / aorta"]
DOMLAB = {"Vitals & core labs": "Vitals &\ncore labs", "Other labs": "Other\nlabs", "Echo: LV structure": "Echo: LV\nstructure",
          "Echo: LV function": "Echo: LV\nfunction", "Echo: diastolic / LA": "Echo:\ndiastolic/LA",
          "Echo: RV / pulmonary": "Echo: RV/\npulmonary", "Echo: valves / aorta": "Echo:\nvalves/aorta"}
RUNGS = [("P1", "PS-Demo"), ("P5", "PS-CVD5"), ("Flags", "PS-Flags"), ("hdPS200", "hdPS200"), ("clinical", "PS-Clinical")]
RL = dict(RUNGS)
CONFIGS = [("main", "1:1, caliper 0.2 (main)"), ("cal01", "1:1, caliper 0.1"), ("m13", "1:3 matching"), ("iptw", "IPTW"),
           ("overlap", "Overlap weights"), ("gbm", "Gradient-boosted PS")]
CL = dict(CONFIGS)
ARM = {"ECG": ("+ ECG", RED, "o"), "CLMBR": ("+ CLMBR-T", BLUE, "s"), "ECG+CLMBR": ("+ ECG + CLMBR-T", NAVY, "D"),
       "shufECG": ("+ permuted ECG", GOLD, "^"), "shufCLMBR": ("+ permuted CLMBR-T", GOLD, "v"),
       "CLMBR32": ("+ CLMBR-T (32 PCs)", LBLUE, "s")}
ARMS5 = ["ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR"]
CHECK = {}
FIGS = []  # (section, stem, title, legend, [(panel, source)])
MINUS = "−"


def S(set_, config, contrast, df=None):
    df = SENS if df is None else df
    r = df[(df.set == set_) & (df.config == config) & (df.contrast == contrast)]
    assert len(r) == 1, (set_, config, contrast, len(r))
    return r.iloc[0]


def pv(p):
    if p is None or not np.isfinite(p):
        return "—"
    if p < 0.001:
        return "<.001"
    s = f"{p:.3f}" if p < 0.0995 else f"{p:.2f}"
    return s[1:] if s.startswith("0.") else s


def num(x, d=1):
    return f"{x:.{d}f}".replace("-", MINUS)


def ci_txt(e, lo, hi, d=1):
    return f"{num(e, d)} ({num(lo, d)} to {num(hi, d)})"


# ---------------------------------------------------------------- export helpers (as v20)
PANEL_LETTER = {}


def letter(ax, s, x=-0.12, y=1.04):
    PANEL_LETTER[id(ax)] = s
    ax.text(x, y, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")


def save_panels(fig, path, pad=0.06):
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
        legs = [lg for lg in fig.legends if lg.get_visible()]
        ftexts = [t for t in fig.texts if t.get_visible()]
        for a in others:
            a.set_visible(False)
        for o in legs + ftexts:
            o.set_visible(False)
        for ext, kw in ((".png", dict(dpi=300)), (".pdf", {})):
            fig.savefig(out / f"{path.name}_{lt}{ext}", bbox_inches=bb, **kw)
        for a in others:
            a.set_visible(True)
        for o in legs + ftexts:
            o.set_visible(True)


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    save_panels(fig, path)
    plt.close(fig)
    print("wrote", path.relative_to(ROOT))


def rel(p):
    return str(Path(p).relative_to(AUD)) if str(p).startswith(str(AUD)) else str(Path(p).relative_to(ROOT))


def mark(ax, x, y, arm, sig, ms=4.6, z=4):
    lab, col, mk = ARM[arm]
    ax.plot(x, y, mk, color=col, mfc=col if sig else "white", mec=col, ms=ms, mew=1.0, zorder=z)


def heat(ax, M, Q, P, rowlabs, collabs, vmax=30, fs=6.4, fmt=lambda v: num(v)):
    M = np.asarray(M, float)
    ax.imshow(np.clip(M, -vmax, vmax), cmap=CMAP, vmin=-vmax, vmax=vmax, aspect="auto")
    nr, nc = M.shape
    for i in range(nr):
        for j in range(nc):
            v = M[i, j]
            if not np.isfinite(v):
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fc="#f2f2f5", ec="none"))
                ax.text(j, i, "—", ha="center", va="center", fontsize=fs, color=GREY)
                continue
            tag = "*" if np.isfinite(Q[i, j]) and Q[i, j] < 0.05 else ("°" if np.isfinite(P[i, j]) and P[i, j] < 0.05 else "")
            ax.text(j, i, fmt(v) + tag, ha="center", va="center", fontsize=fs,
                    color="white" if abs(v) > 0.55 * vmax else NAVY, fontweight="bold" if tag == "*" else "normal")
    ax.set_xticks(range(nc), collabs)
    ax.set_yticks(range(nr), rowlabs)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-0.5, nc, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nr, 1), minor=True)
    ax.grid(which="minor", color="white", lw=1.5)
    ax.tick_params(which="minor", length=0)


def cbar(fig, rect, vmax, label):
    cax = fig.add_axes(rect)
    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(-vmax, vmax))
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label(label, fontsize=6.5)
    cb.ax.tick_params(labelsize=6)
    cb.outline.set_visible(False)
    return cax


# ================================================================ Figure 1: design schematic
def figure1():
    s32 = S32KEYS
    areas = pd.Series([AREA[k] for k in s32]).value_counts()
    tiers = pd.Series([TIER[k] for k in s32]).value_counts()
    lab = LPT[(LPT.arm == "ECG") & LPT.in_S32]
    n_phys = int(lab.physiologic.sum())
    nfl = [d["n_flags"] for d in FLAGLOG if d["trial"] in s32]
    CHECK["fig1 S32 areas"] = areas.to_dict()
    CHECK["fig1 physiologic"] = (n_phys, len(lab))
    CHECK["fig1 flags range S32"] = (min(nfl), max(nfl))
    order = ["AF", "Diabetes", "HF", "Hypertension", "ACS / MI", "Other"]
    area_txt = ", ".join(f"{a.replace('ACS / MI', 'ACS')} {areas.get(a, 0)}" for a in order if areas.get(a, 0))
    area_txt2 = area_txt.replace(", Hypertension", ",\nhypertension").replace("Diabetes", "diabetes").replace("Other", "other")

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(11, 66)
    ax.axis("off")

    def box(x, y, w, h, txt, fc="white", ec=NAVY, tc=NAVY, fs=6.3, lw=0.9, ha="center"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc, ec=ec, lw=lw))
        lines = txt.split("\n")
        xt = x + w / 2 if ha == "center" else x + 1
        ax.text(xt, y + h - 0.9, lines[0], ha=ha, va="top", fontsize=fs + 0.6, color=tc, fontweight="bold")
        ax.text(xt, y + h - 3.6, "\n".join(lines[1:]), ha=ha, va="top", fontsize=fs, color=tc, linespacing=1.3)

    def arrow(x0, y0, x1, y1, col=NAVY):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=col, lw=0.9, shrinkA=0, shrinkB=0))

    # trials
    box(0.5, 42, 22, 23.5, f"Trials\n38 emulated cardiovascular\nRCTs (new user, active\ncomparator); {len(s32)} analysed\n"
        f"({tiers.get('Excellent', 0)} excellent, {tiers.get('Good', 0)} good,\n{tiers.get('Moderate', 0)} moderate emulations)\n"
        f"{area_txt2}\n"
        f"Blind labels: physiologic\n{n_phys}/{len(lab)}; cardiac domains")
    arrow(22.8, 54, 25.2, 54)
    # data
    box(25.5, 42, 21.5, 23.5, "Data (YNHHS, 2011–2024)\nEHR in OMOP: diagnoses,\ndrugs, procedures,\nmeasurements, visits\n"
        "Raw 12-lead ECG\n(≤ 365 d before t0)\nEchocardiography reports\n(held-out balance items\nonly; in no PS)")
    arrow(47.3, 60, 50.2, 60)
    arrow(47.3, 48, 50.2, 48)
    # representations
    box(50.5, 55, 23.5, 10.5, "ECG embedding\nself-supervised 12-lead\nencoder → 32 PCs\n(physiological signal)", ec=RED, lw=1.3)
    box(50.5, 42, 23.5, 11.5, "CLMBR-T\nfoundation model of the coded\nEHR (codes, no values; index\nday excluded) → 64 PCs\n(32-PC sensitivity)",
        ec=BLUE, lw=1.3)
    # PS ladder
    ax.text(0.8, 37.6, "Propensity-score ladder (hand-built covariates)", fontsize=7.2, fontweight="bold", va="bottom")
    ax.text(73.8, 37.6, "each representation is added to every rung", fontsize=6.0, color=GREY, va="bottom", ha="right")
    rungs = [("PS-Demo", "age, sex,\nindex year"), ("PS-CVD5", "PS-Demo + HTN,\nT2D, CAD, AF, HF\n(primary)"),
             ("PS-Flags", f"PS-Demo +\n{min(nfl)}–{max(nfl)} yes/no\nICD-10 flags,\nno dates"),
             ("hdPS200", "200 empirically\nselected codes"), ("PS-Clinical", "incl. measured\nvitals and labs")]
    w, g, x0 = 13.5, 1.6, 0.5
    for i, (nm, ds) in enumerate(rungs):
        x = x0 + i * (w + g)
        prim = nm == "PS-CVD5"
        box(x, 26.5, w, 10.5, f"{nm}\n{ds}", fc=NAVY if prim else "white", tc="white" if prim else NAVY, fs=5.9)
        if i:
            arrow(x - g + 0.1, 31.75, x - 0.1, 31.75)
    box(0.5, 12.5, 73.5, 11.5, "Each rung × 6 arms × 6 configurations\n"
        "Arms: base, + ECG, + CLMBR-T, + ECG + CLMBR-T, + permuted ECG, + permuted CLMBR-T (placebos)\n"
        "Configurations: 1:1 caliper 0.2 (main), caliper 0.1, 1:3 matching, IPTW, overlap weights, gradient-boosted PS\n"
        "Head-to-heads: PS-Demo + CLMBR-T vs PS-Flags (PI hypothesis); CLMBR-T vs hdPS200 and PS-Clinical\n"
        "Trial sets: 32 analysed (primary), all 38 (sensitivity)", fs=6.1, fc="#f5f5f8", ec=GREY, ha="left")
    # analyses
    box(77.5, 52.5, 22, 13, "1  Covariate balance\n54 non-coded held-out items\n(vitals & labs, 5 echo\ndomains), in no PS; relative\n"
        "reduction in mean |SMD|")
    box(77.5, 39.5, 22, 11, "2  RCT agreement\nemulated vs published HR:\n|Δ log HR|, trials closer;\nbenchmark permutation")
    box(77.5, 26.5, 22, 11, "3  Label stratification\nphysiologic vs not;\nlabelled cardiac domain vs\nnot (label permutation)")
    ax.plot([74.3, 75.8], [31.75, 31.75], color=NAVY, lw=0.9)
    ax.plot([75.8, 75.8], [32.0, 59.0], color=NAVY, lw=0.9)
    for y in (59.0, 45.0, 32.0):
        arrow(75.8, y, 77.2, y)
    box(77.5, 12.5, 22, 11.5, "Multiplicity and support\nBH-FDR across all contrasts\n× configurations;\n"
        "supplement: plasmode (known\ntruth), MIMIC-IV (ECG only)", fc="#f5f5f8", ec=GREY)
    save(fig, OUTM / "figure1_study_design")
    FIGS.append(("main", "figure1_study_design", "Figure 1. Study design",
                 f"Thirty-eight new-user, active-comparator emulations of cardiovascular RCTs; {len(s32)} pass emulation-quality grading "
                 f"and form the primary set. Two learned representations are added to each rung of a ladder of hand-built propensity "
                 f"scores: the AI-ECG embedding (32 principal components; the physiological signal) and CLMBR-T, a foundation model "
                 f"of the coded EHR (diagnoses, drugs, procedures, measurement codes without values and visits; index day excluded; "
                 f"64 PCs, 32 as sensitivity). CLMBR-T embeds the structured, coded record; it is not an unstructured-data model. "
                 f"PS-CVD5 is the primary comparison; PS-Flags is PS-Demo plus {min(nfl)}–{max(nfl)} yes/no ICD-10 3-character "
                 f"diagnosis flags (full pre-index history, ≥1% prevalence, no dates). Balance is assessed on 54 non-coded "
                 f"held-out characteristics that are in no PS. Trial labels (physiologic yes/no, cardiac domains) come from two "
                 f"blind runs of the same LLM working from a results-free PICOT table.",
                 [("A", "core/log.json (PS-Flags counts per trial), core/labels_per_trial.csv (labels), docs/v19/quality_tiers.json (tiers, areas)")]))


# ================================================================ Figure 2: balance by PS rung
def figure2():
    fig = plt.figure(figsize=(7.2, 7.4))
    ax = fig.add_axes([0.25, 0.36, 0.40, 0.60])
    y, rows, heads = 0, [], []
    for rg, rname in RUNGS:
        heads.append((y, rname + (" (primary)" if rg == "P5" else ""), rg))
        y -= 1
        for a in ARMS5:
            r = S("S32", "main", f"{rg}: {a} vs base")
            rows.append((y, rg, a, r))
            y -= 1
        y -= 0.5
    for yy, rg, a, r in rows:
        sig = r.q_m54_p_fam < 0.05
        ax.plot([r.relred54_lo, r.relred54_hi], [yy, yy], color=ARM[a][1], lw=1.1, zorder=2)
        mark(ax, r.relred54, yy, a, sig)
        tx = ax.get_yaxis_transform()
        ax.text(1.03, yy, ci_txt(r.relred54, r.relred54_lo, r.relred54_hi), transform=tx, fontsize=6.3, va="center")
        ax.text(1.43, yy, r.m54_better, transform=tx, fontsize=6.3, va="center", ha="center")
        ax.text(1.62, yy, pv(r.q_m54_p_fam), transform=tx, fontsize=6.3, va="center", ha="center",
                fontweight="bold" if sig else "normal")
        CHECK[f"fig2A {rg} {a}"] = (round(r.relred54, 1), round(r.relred54_lo, 1), round(r.relred54_hi, 1), pv(r.q_m54_p_fam))
    for yy, nm, rg in heads:
        ax.text(-0.02, yy, nm, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=7.2, fontweight="bold")
        if rg == "P5":
            ax.axhspan(yy + 0.5, yy - 5.5, color="#eef0f7", zorder=0, lw=0)
    ax.set_yticks([r[0] for r in rows], [ARM[r[2]][0] for r in rows], fontsize=6.6)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_xlim(-25, 35)
    ax.set_ylim(y + 0.6, 0.8)
    ax.set_xlabel("Relative reduction in mean |SMD| vs the rung's base PS, % (95% CI)\n54 non-coded held-out characteristics; 32 trials; 1:1, caliper 0.2")
    tx = ax.transAxes
    for x, t in ((1.03, "Estimate (95% CI)"), (1.43, "Trials better"), (1.62, "q")):
        ax.text(x, 1.005, t, transform=tx, fontsize=6.5, fontweight="bold", va="bottom", ha="left" if x < 1.1 else "center")
    ax.text(0.99, 0.01, "filled: q < .05 (BH, balance family)\nopen: q ≥ .05", transform=tx, fontsize=5.8, ha="right",
            va="bottom", color=GREY)
    letter(ax, "A", x=-0.42, y=1.0)
    # B: absolute mean |SMD| by rung
    ax = fig.add_axes([0.25, 0.05, 0.70, 0.17])
    offs = {"base": -0.3, "ECG": -0.1, "CLMBR": 0.1, "ECG+CLMBR": 0.3}
    for k, (rg, rname) in enumerate(RUNGS):
        b = S("S32", "main", f"{rg}: ECG vs base").m54_b
        ax.plot(k + offs["base"], b, "o", color=GREY, mfc="white", ms=5, mew=1.0, zorder=3)
        vals = [b]
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            r = S("S32", "main", f"{rg}: {a} vs base")
            mark(ax, k + offs[a], r.m54_a, a, True, ms=5)
            vals.append(r.m54_a)
        ax.plot([k - 0.3, k + 0.3], [b, b], color=LGREY, lw=0.8, zorder=1)
        CHECK[f"fig2B {rg}"] = tuple(round(v, 3) for v in vals)
    ax.set_xticks(range(len(RUNGS)), [n for _, n in RUNGS])
    ax.set_xlim(-0.6, len(RUNGS) - 0.4)
    ax.set_ylabel("Mean |SMD|, 54 items\n(mean across 32 trials)", fontsize=7)
    ax.set_ylim(0.10, 0.15)
    h = [Line2D([], [], color=GREY, marker="o", mfc="white", ls="", label="base PS")] + \
        [Line2D([], [], color=ARM[a][1], marker=ARM[a][2], ls="", label=ARM[a][0]) for a in ("ECG", "CLMBR", "ECG+CLMBR")]
    ax.legend(handles=h, frameon=False, fontsize=6.3, ncol=4, loc="upper right", bbox_to_anchor=(1.0, 1.04))
    letter(ax, "B", x=-0.24, y=1.02)
    save(fig, OUTM / "figure2_balance_by_ps")
    p5 = {a: S("S32", "main", f"P5: {a} vs base") for a in ARMS5}
    FIGS.append(("main", "figure2_balance_by_ps", "Figure 2. Held-out balance: each representation added to each PS rung",
                 f"(A) Relative reduction in mean |SMD| over the 54 non-coded held-out characteristics when each representation is "
                 f"added to the rung's base PS (S32, main configuration: 1:1 matching, caliper 0.2). 95% CI from a 4,000-resample "
                 f"trial bootstrap; filled markers, q < .05 (BH across the whole sweep, balance family). With PS-CVD5 (primary): "
                 f"ECG {ci_txt(p5['ECG'].relred54, p5['ECG'].relred54_lo, p5['ECG'].relred54_hi)}%, CLMBR-T "
                 f"{ci_txt(p5['CLMBR'].relred54, p5['CLMBR'].relred54_lo, p5['CLMBR'].relred54_hi)}%, both "
                 f"{ci_txt(p5['ECG+CLMBR'].relred54, p5['ECG+CLMBR'].relred54_lo, p5['ECG+CLMBR'].relred54_hi)}%; permuted "
                 f"placebos ≈ 0 (two-sided). Gains shrink or vanish against PS-Flags, hdPS200 (the ECG still adds "
                 f"{S('S32', 'main', 'hdPS200: ECG vs base').relred54:.1f}%) and PS-Clinical. "
                 f"(B) The absolute mean |SMD| behind panel A: the richer the base PS, the less imbalance is left; base value "
                 f"shown is the one paired with the + ECG item set (it differs by ≤ 0.001 across arms).",
                 [("A", "core/sensitivity.csv (set = S32, config = main, kind = within; relred54, relred54_lo/hi, m54_better, q_m54_p_fam)"),
                  ("B", "core/sensitivity.csv (m54_b, m54_a)")]))


# ================================================================ Figure 3: what each representation captures
H2H = [
    ("vs PS-Flags", [
        ("PS-Demo + CLMBR-T vs PS-Flags, C = 1 (primary)", "sens", "S32", "main", "P1+CLMBR vs Flags base", "CLMBR"),
        ("vs PS-Flags, C = 0.1", "fcv", "S32", "main", "P1+CLMBR vs FlagsC0.1 base", "CLMBR"),
        ("vs PS-Flags, C = 0.01", "fcv", "S32", "main", "P1+CLMBR vs FlagsC0.01 base", "CLMBR"),
        ("vs PS-Flags, CV-tuned C", "fcv", "S32", "main", "P1+CLMBR vs FlagsCV base", "CLMBR"),
        ("vs PS-Flags, CV-tuned C (1:3 matching)", "fcv", "S32", "m13", "P1+CLMBR vs FlagsCV base", "CLMBR"),
        ("vs PS-Flags, CV-tuned C (overlap weights)", "fcv", "S32", "overlap", "P1+CLMBR vs FlagsCV base", "CLMBR"),
        ("vs PS-Flags C = 1, trials with Flags retention ≥ 0.5", "fcv", "S32_flagsret>=0.5", "main", "P1+CLMBR vs Flags base", "CLMBR"),
        ("vs PS-Flags C = 1, Flags retention ≥ 0.7", "fcv", "S32_flagsret>=0.7", "main", "P1+CLMBR vs Flags base", "CLMBR"),
        ("vs PS-Flags C = 1, Flags retention ≥ 0.9", "fcv", "S32_flagsret>=0.9", "main", "P1+CLMBR vs Flags base", "CLMBR"),
        ("PS-Demo + CLMBR-T (32 PCs) vs PS-Flags, C = 1", "sens", "S32", "main", "P1+CLMBR32 vs Flags base", "CLMBR32"),
    ]),
    ("vs hdPS200", [
        ("PS-Demo + CLMBR-T vs hdPS200", "sens", "S32", "main", "P1+CLMBR vs hdPS200 base", "CLMBR"),
        ("PS-CVD5 + CLMBR-T vs hdPS200", "sens", "S32", "main", "P5+CLMBR vs hdPS200 base", "CLMBR"),
    ]),
    ("vs PS-Clinical (measured vitals and labs)", [
        ("PS-CVD5 + CLMBR-T vs PS-Clinical", "sens", "S32", "main", "P5+CLMBR vs clinical base", "CLMBR"),
        ("PS-CVD5 + ECG + CLMBR-T vs PS-Clinical", "sens", "S32", "main", "P5+ECG+CLMBR vs clinical base", "ECG+CLMBR"),
    ]),
]


def h2h_row(src, set_, cfg, con):
    return S(set_, cfg, con) if src == "sens" else S(set_, cfg, con, FCV)


def figure3():
    fig = plt.figure(figsize=(7.2, 9.0))
    cols = ["All 54"] + DOMS
    nitems = {d: int(HD[(HD.set == "S32") & (HD.config == "main") & (HD.domain == d)].n_items.iloc[0]) for d in DOMS}
    collabs = ["All 54\nitems"] + [f"{DOMLAB[d]}\n({nitems[d]})" for d in DOMS]

    def domrow(set_, cfg, con):
        r0 = S(set_, cfg, con)
        v, q, p = [r0.relred54], [r0.q_m54_p_fam], [r0.m54_p]
        for d in DOMS:
            r = HD[(HD.set == set_) & (HD.config == cfg) & (HD.contrast == con) & (HD.domain == d)]
            assert len(r) == 1, (cfg, con, d)
            r = r.iloc[0]
            v.append(r.relred if r.k > 0 else np.nan)
            q.append(r.q_domain_fam)
            p.append(r.p)
        return v, q, p
    # A
    ax = fig.add_axes([0.25, 0.775, 0.70, 0.155])
    rowsA = [("P5: ECG vs base", "+ ECG"), ("P5: CLMBR vs base", "+ CLMBR-T"), ("P5: ECG+CLMBR vs base", "+ ECG + CLMBR-T"),
             ("P5: CLMBR vs ECG", "CLMBR-T vs ECG (2-sided)"), ("P5: shufECG vs base", "+ permuted ECG"),
             ("P5: shufCLMBR vs base", "+ permuted CLMBR-T")]
    M, Q, P = zip(*[domrow("S32", "main", c) for c, _ in rowsA])
    heat(ax, M, np.array(Q), np.array(P), [l for _, l in rowsA], collabs)
    ax.axhline(2.5, color=NAVY, lw=0.8)
    ax.axhline(3.5, color=NAVY, lw=0.8)
    ax.set_title("PS-CVD5, main configuration: relative reduction in mean |SMD| vs PS-CVD5 base, %", loc="left", fontsize=7,
                 color=GREY, pad=34)
    for (c, _), m in zip(rowsA, M):
        CHECK[f"fig3A {c}"] = [round(x, 1) if np.isfinite(x) else None for x in m]
    letter(ax, "A", x=-0.33, y=1.32)
    # B: CLMBR-T vs ECG by configuration
    ax = fig.add_axes([0.25, 0.56, 0.70, 0.155])
    M, Q, P = zip(*[domrow("S32", c, "P5: CLMBR vs ECG") for c, _ in CONFIGS])
    heat(ax, M, np.array(Q), np.array(P), [n for _, n in CONFIGS], collabs)
    ax.set_xticklabels([])
    ax.set_title("PS-CVD5: CLMBR-T vs ECG, by configuration (positive = CLMBR-T better balanced)", loc="left", fontsize=7,
                 color=GREY, pad=4)
    for (c, _), m in zip(CONFIGS, M):
        CHECK[f"fig3B {c}"] = [round(x, 1) for x in m]
    letter(ax, "B", x=-0.33, y=1.04)
    cbar(fig, [0.70, 0.525, 0.25, 0.010], 30, "relative reduction, % (clipped at ±30)")
    fig.text(0.25, 0.512, "* q < .05 (BH; overall column: balance family; domains: exploratory domain family)\n"
             "° nominal P < .05 only.  Domain differences are nominal; see legend.", fontsize=5.8, color=GREY, va="top")
    # C: head-to-heads
    ax = fig.add_axes([0.25, 0.05, 0.36, 0.39])
    y, ys, labs = 0, [], []
    for gname, items in H2H:
        ax.text(-0.02, y, gname, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=7, fontweight="bold")
        y -= 1
        for lab, src, set_, cfg, con, arm in items:
            r = h2h_row(src, set_, cfg, con)
            sig = src == "sens" and r.q_m54_p_fam < 0.05
            ax.plot([r.relred54_lo, r.relred54_hi], [y, y], color=ARM[arm][1], lw=1.1)
            mark(ax, r.relred54, y, arm, sig)
            tx = ax.get_yaxis_transform()
            k = int(r.relred54_k)
            ax.text(1.03, y, ci_txt(r.relred54, r.relred54_lo, r.relred54_hi), transform=tx, fontsize=6.0, va="center")
            ax.text(1.50, y, str(r.m54_better), transform=tx, fontsize=6.0, va="center", ha="center")
            ax.text(1.66, y, pv(r.m54_p), transform=tx, fontsize=6.0, va="center", ha="center")
            ax.text(1.82, y, pv(r.q_m54_p_fam) if src == "sens" else "sens.", transform=tx, fontsize=6.0, va="center", ha="center",
                    color=NAVY if src == "sens" else GREY)
            ax.text(2.05, y, f"{r.absd_b_pair:.3f} → {r.absd_a_pair:.3f}", transform=tx, fontsize=6.0, va="center", ha="center")
            ax.text(2.33, y, pv(r.bshuf_p), transform=tx, fontsize=6.0, va="center", ha="center")
            ys.append(y)
            labs.append(lab if not lab.startswith("vs") else "    " + lab)
            CHECK[f"fig3C {lab} [{cfg}]"] = (k, round(r.relred54, 1), round(r.relred54_lo, 1), round(r.relred54_hi, 1), pv(r.m54_p),
                                              round(r.absd_b_pair, 3), round(r.absd_a_pair, 3), pv(r.bshuf_p))
            y -= 1
        y -= 0.4
    ax.set_yticks(ys, labs, fontsize=6.0)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_xlim(-20, 20)
    ax.set_ylim(y + 0.5, 0.7)
    ax.set_xlabel("Relative reduction in mean |SMD|, 54 items, %\n(> 0: learned-representation PS better balanced)", fontsize=7)
    tx = ax.transAxes
    for x, t, ha in ((1.03, "Estimate (95% CI)", "left"), (1.50, "Better", "center"), (1.66, "P", "center"), (1.82, "q", "center"),
                     (2.05, "|Δ log HR|\nref → learned", "center"), (2.33, "Perm.\nP", "center")):
        ax.text(x, 1.0, t, transform=tx, fontsize=6.2, fontweight="bold", va="bottom", ha=ha)
    ax.set_title("Head-to-heads (S32, main unless stated; two-sided)", loc="left", fontsize=7, color=GREY, pad=16)
    letter(ax, "C", x=-0.65, y=1.06)
    save(fig, OUTM / "figure3_what_representations_capture")
    pf = S("S32", "main", "P1+CLMBR vs Flags base")
    cv = S("S32", "main", "P1+CLMBR vs FlagsCV base", FCV)
    FIGS.append(("main", "figure3_what_representations_capture", "Figure 3. What each representation captures, and CLMBR-T against hand-built PS models",
                 "(A) Per-domain relative reduction in mean |SMD| when the ECG, CLMBR-T or both are added to PS-CVD5 (S32, main), with "
                 "the direct CLMBR-T vs ECG contrast and the two permuted placebos. In the main configuration the ECG's gains sit in "
                 "the echo domains (LV structure, LV function, diastolic/LA) and CLMBR-T's in vitals and labs (and valves). "
                 "(B) The CLMBR-T vs ECG domain contrast in every configuration: the ECG's echo-domain advantage seen in the main "
                 "configuration does not replicate under 1:3 matching or overlap weights. Domain-level results are exploratory and "
                 "nominal (q from a separate domain family; * q < .05, ° nominal P < .05 only); only the overall column belongs to "
                 "the prespecified balance family. "
                 f"(C) Head-to-heads of learned-representation PS models against hand-built PS models (two-sided). PS-Demo + "
                 f"CLMBR-T vs PS-Flags: {ci_txt(pf.relred54, pf.relred54_lo, pf.relred54_hi)}%, {pf.m54_better} trials better, "
                 f"P = {pv(pf.m54_p)}; with CV-tuned PS-Flags {ci_txt(cv.relred54, cv.relred54_lo, cv.relred54_hi)}%. No specification "
                 "shows CLMBR-T beating the flags (no detectable difference, not equivalence). Fixed-C, CV-tuned and "
                 "retention-restricted rows are sensitivity analyses outside the FDR sweep (q column 'sens.'). |Δ log HR| means are "
                 "paired over trials with an estimate in both PS models; Perm. P is the benchmark-permutation P.",
                 [("A", "core/headline_domains.csv (S32, main; relred, p, q_domain_fam) + core/sensitivity.csv (overall column: relred54, m54_p, q_m54_p_fam)"),
                  ("B", "core/headline_domains.csv (contrast 'P5: CLMBR vs ECG', all configurations) + core/sensitivity.csv"),
                  ("C", "core/sensitivity.csv (kind across / clmbr32) and core/flagscv.csv (fixed-C, CV-tuned and retention-restricted rows)")]))


# ================================================================ Figure 4: which trials benefit
def figure4():
    fig = plt.figure(figsize=(7.2, 7.6))
    L = LPT[LPT.in_S32].copy()
    e = L[L.arm == "ECG"].set_index("key")
    c = L[L.arm == "CLMBR"].set_index("key")
    # verify labels_per_trial gain = P5 main base - arm (per_trial.csv)
    pb = PT[(PT.rung == "P5") & (PT.config == "main") & (PT.arm == "base")].set_index("key").m54
    pe = PT[(PT.rung == "P5") & (PT.config == "main") & (PT.arm == "ECG")].set_index("key").m54
    assert np.allclose((pb - pe).loc[e.index], e.gain_m54, atol=1e-9)
    order = []
    for ph in (True, False):
        ks = e.index[e.physiologic == ph]
        order += sorted(ks, key=lambda k: -(e.gain_m54[k] + c.gain_m54[k]))
    n = len(order)
    ax = fig.add_axes([0.16, 0.06, 0.30, 0.86])
    ypos = {}
    y = 0
    for i, k in enumerate(order):
        if i and e.physiologic[k] != e.physiologic[order[i - 1]]:
            y -= 1.2
        ypos[k] = y
        y -= 1
    nph = int(e.physiologic.sum())
    for k in order:
        yy = ypos[k]
        ax.plot([e.gain_m54[k], c.gain_m54[k]], [yy, yy], color=LGREY, lw=0.8, zorder=1)
        mark(ax, e.gain_m54[k], yy + 0.0, "ECG", True, ms=4.0)
        mark(ax, c.gain_m54[k], yy, "CLMBR", True, ms=3.8)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_yticks([ypos[k] for k in order], [NAME[k] for k in order], fontsize=6.0)
    ax.set_ylim(y + 0.4, 1.4)
    ax.set_xlim(-0.035, 0.085)
    ax.set_xlabel("Gain in mean |SMD|, 54 items\n(PS-CVD5 base − PS-CVD5 + representation)", fontsize=7)
    yph = [ypos[k] for k in order if e.physiologic[k]]
    ynp = [ypos[k] for k in order if not e.physiologic[k]]
    ax.text(0.084, max(yph) + 0.9, f"Physiologic (n = {nph})", fontsize=7, fontweight="bold", ha="right", va="center")
    ax.text(0.084, max(ynp) + 0.9, f"Not physiologic (n = {n - nph})", fontsize=7, fontweight="bold", ha="right", va="center")
    h = [Line2D([], [], color=ARM[a][1], marker=ARM[a][2], ls="", label=ARM[a][0]) for a in ("ECG", "CLMBR")]
    ax.legend(handles=h, frameon=False, fontsize=6.3, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    letter(ax, "A", x=-0.62, y=1.03)
    # label matrix
    axm = fig.add_axes([0.465, 0.06, 0.075, 0.86], sharey=ax)
    dcols = [("LV_structure", "LV str."), ("LV_systolic_function", "LV sys."), ("diastolic_LA", "Diast./LA"),
             ("RV_pulmonary_congestion", "RV/pulm."), ("rhythm_conduction", "Rhythm")]
    for k in order:
        doms = str(e.domains[k]).split(";")
        for j, (dk, _) in enumerate(dcols):
            on = dk in doms
            axm.plot(j, ypos[k], "s", ms=3.6, color=NAVY if on else "white", mec=NAVY if on else LGREY, mew=0.6)
    axm.set_xticks(range(len(dcols)), [d for _, d in dcols], rotation=90, fontsize=5.6)
    axm.xaxis.tick_top()
    axm.tick_params(axis="y", left=False, labelleft=False)
    axm.tick_params(axis="x", length=0)
    for s in axm.spines.values():
        s.set_visible(False)
    axm.set_xlim(-0.7, len(dcols) - 0.3)
    # B: physiologic vs not, relative reduction within group
    ax = fig.add_axes([0.73, 0.60, 0.25, 0.32])
    rows = []
    for i, a in enumerate(ARMS5):
        r = LP[(LP.set == "S32") & (LP.config == "main") & (LP.arm == a) & LP.endpoint.str.startswith("m54")].iloc[0]
        yy = -i
        ax.plot([r.relred_yes_lo, r.relred_yes_hi], [yy + 0.15] * 2, color=ARM[a][1], lw=1.0)
        ax.plot(r.relred_yes, yy + 0.15, ARM[a][2], color=ARM[a][1], ms=4.4)
        ax.plot([r.relred_no_lo, r.relred_no_hi], [yy - 0.15] * 2, color=GREY, lw=1.0)
        ax.plot(r.relred_no, yy - 0.15, ARM[a][2], color=GREY, mfc="white", ms=4.4, mew=0.9)
        ax.text(1.03, yy, f"P {pv(r.perm_p)}\nq {pv(r.q_family)}", transform=ax.get_yaxis_transform(), fontsize=5.8, va="center")
        rows.append(yy)
        CHECK[f"fig4B {a}"] = (round(r.relred_yes, 1), round(r.relred_no, 1), pv(r.perm_p), pv(r.q_family))
    ax.set_yticks(rows, [ARM[a][0] for a in ARMS5], fontsize=6.3)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_xlim(-10, 42)
    ax.set_ylim(-4.6, 0.6)
    ax.set_xlabel("Relative reduction in mean |SMD|\nwithin label group, % (95% CI)", fontsize=6.8)
    h = [Line2D([], [], color=NAVY, marker="o", ls="", label=f"physiologic ({nph})"),
         Line2D([], [], color=GREY, marker="o", mfc="white", ls="", label=f"not ({n - nph})")]
    ax.legend(handles=h, frameon=False, fontsize=6.0, ncol=2, loc="lower center", bbox_to_anchor=(0.4, 1.0), handletextpad=0.2,
              columnspacing=0.8)
    letter(ax, "B", x=-0.55, y=1.1)
    # C: domain labels
    ax = fig.add_axes([0.73, 0.06, 0.25, 0.43])
    LDs = LD[(LD.set == "S32") & (LD.config == "main") & (LD.label_source == "domains") & LD.tested]
    doms = [("LV_systolic_function", "LV systolic function\n(LV-function items + LVEF)"), ("diastolic_LA", "Diastolic / LA"),
            ("RV_pulmonary_congestion", "RV / pulmonary\n(+ NT-proBNP)"), ("rhythm_conduction", "Rhythm / conduction\n(heart-rate proxy)")]
    y, ys, yl = 0, [], []
    for dk, dl in doms:
        r0 = LDs[(LDs.label_domain == dk)].iloc[0]
        ax.text(-0.04, y, f"{dl}\n{int(r0.n_labelled)} vs {int(r0.n_not)} trials", transform=ax.get_yaxis_transform(), ha="right",
                va="center", fontsize=6.0, fontweight="bold")
        y -= 1.7
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            r = LDs[(LDs.label_domain == dk) & (LDs.arm == a)].iloc[0]
            ax.plot([r.mean_gain_not, r.mean_gain_labelled], [y, y], color=LGREY, lw=0.8)
            ax.plot(r.mean_gain_not, y, ARM[a][2], color=GREY, mfc="white", ms=4.0, mew=0.9)
            ax.plot(r.mean_gain_labelled, y, ARM[a][2], color=ARM[a][1], ms=4.0)
            ax.text(1.03, y, f"{pv(r.perm_p)} ({pv(r.q_family)})", transform=ax.get_yaxis_transform(), fontsize=5.8, va="center",
                    fontweight="bold" if r.q_family < 0.05 else "normal")
            ys.append(y)
            yl.append(ARM[a][0].replace("+ ", "", 1))
            CHECK[f"fig4C {dk} {a}"] = (round(r.mean_gain_labelled, 3), round(r.mean_gain_not, 3), pv(r.perm_p), pv(r.q_family))
            y -= 1
        y -= 0.9
    ax.set_yticks(ys, yl, fontsize=5.8)
    ax.tick_params(axis="y", pad=1)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_ylim(y + 0.5, 1.4)
    ax.set_xlim(-0.03, 0.14)
    ax.set_xlabel("Gain in mean |SMD| over the\nmapped items (colour: labelled;\nopen grey: not labelled)", fontsize=6.6)
    ax.text(1.03, 1.0, "P (q)", transform=ax.transAxes, fontsize=6.2, fontweight="bold", va="bottom")
    letter(ax, "C", x=-0.55, y=1.04)
    save(fig, OUTM / "figure4_which_trials_benefit")
    r = {a: LP[(LP.set == "S32") & (LP.config == "main") & (LP.arm == a) & LP.endpoint.str.startswith("m54")].iloc[0] for a in ARMS5}
    FIGS.append(("main", "figure4_which_trials_benefit", "Figure 4. Which trials benefit: per-trial gains by trial label (PS-CVD5, main)",
                 f"(A) Per-trial gain in mean |SMD| over the 54 held-out items when the ECG (red) or CLMBR-T (blue) is added to PS-CVD5, "
                 f"for the 32 analysed trials, grouped by the blind physiologic label (n = {nph} vs {n - nph}) and sorted by the summed "
                 f"gain; the matrix shows each trial's labelled cardiac domain(s). (B) Relative reduction within each label group "
                 f"(descriptive, 95% bootstrap CI). The test statistic is the difference in mean absolute gain (physiologic − not), "
                 f"with a two-sided 10,000-draw label-permutation P and BH q within the label family: ECG P = {pv(r['ECG'].perm_p)} "
                 f"(q = {pv(r['ECG'].q_family)}), CLMBR-T P = {pv(r['CLMBR'].perm_p)} (q = {pv(r['CLMBR'].q_family)}), both P = "
                 f"{pv(r['ECG+CLMBR'].perm_p)} (q = {pv(r['ECG+CLMBR'].q_family)}); none reaches q < .05. CLMBR-T, which is not a "
                 "physiological signal, shows the same pattern as the ECG, so larger gains in physiologic trials more likely reflect more "
                 "confounding to remove than ECG-specific content. (C) Gain over the items mapped to each labelled domain, labelled vs "
                 "not labelled trials; P (q within the domain family). LV_structure (1 labelled trial) is not tested. All P values are "
                 "nominal unless q is shown; the labels come from two runs of one LLM, and the labeller knows the published trials.",
                 [("A", "core/labels_per_trial.csv (gain_m54, physiologic, domains; checked against core/per_trial.csv m54)"),
                  ("B", "core/labels_physiologic.csv (S32, main, m54 endpoint)"),
                  ("C", "core/labels_domain.csv (S32, main, label_source = domains, tested rows)")]))


# ================================================================ Figure 5: replication across configurations
def figure5():
    fig = plt.figure(figsize=(7.2, 9.0))
    axA = fig.add_axes([0.22, 0.43, 0.25, 0.53])
    axB = fig.add_axes([0.50, 0.43, 0.21, 0.53], sharey=axA)
    y, ys, yl = 0, [], []
    for cfg, cname in CONFIGS:
        axA.text(-0.02, y, cname, transform=axA.get_yaxis_transform(), ha="right", va="center", fontsize=6.8, fontweight="bold")
        y -= 1
        for a in ARMS5:
            r = S("S32", cfg, f"P5: {a} vs base")
            sb = r.q_m54_p_fam < 0.05
            axA.plot([r.relred54_lo, r.relred54_hi], [y, y], color=ARM[a][1], lw=1.0)
            mark(axA, r.relred54, y, a, sb, ms=4.2)
            d = r.absd_a - r.absd_b
            sa = r.q_absd_p_fam < 0.05
            axB.plot([0, d], [y, y], color=ARM[a][1], lw=1.0, alpha=0.6)
            mark(axB, d, y, a, sa, ms=4.2)
            tx = axB.get_yaxis_transform()
            axB.text(1.04, y, str(r.absd_better), transform=tx, fontsize=5.8, va="center")
            axB.text(1.28, y, pv(r.absd_p), transform=tx, fontsize=5.8, va="center", ha="center")
            axB.text(1.48, y, pv(r.bshuf_p), transform=tx, fontsize=5.8, va="center", ha="center")
            axB.text(1.68, y, pv(r.q_absd_p_fam), transform=tx, fontsize=5.8, va="center", ha="center")
            ys.append(y)
            yl.append(ARM[a][0])
            CHECK[f"fig5 {cfg} {a}"] = (round(r.relred54, 1), pv(r.q_m54_p_fam), round(r.absd_b, 3), round(r.absd_a, 3), r.absd_better,
                                        pv(r.absd_p), pv(r.bshuf_p), pv(r.q_absd_p_fam))
            y -= 1
        y -= 0.5
    axA.set_yticks(ys, yl, fontsize=6.0)
    axA.set_ylim(y + 0.5, 0.7)
    for ax in (axA, axB):
        ax.axvline(0, color=GREY, ls="--", lw=0.7)
    axA.set_xlim(-25, 30)
    axB.set_xlim(-0.08, 0.03)
    axB.tick_params(axis="y", left=False, labelleft=False)
    axA.set_xlabel("Balance: relative reduction in\nmean |SMD|, 54 items, % (95% CI)", fontsize=6.8)
    axB.set_xlabel("Agreement: change in mean\n|Δ log HR| vs RCT (< 0: closer)", fontsize=6.8)
    tx = axB.transAxes
    for x, t, ha in ((1.04, "Closer", "left"), (1.28, "P", "center"), (1.48, "Perm.\nP", "center"), (1.68, "q", "center")):
        axB.text(x, 1.0, t, transform=tx, fontsize=6.2, fontweight="bold", va="bottom", ha=ha)
    axA.set_title("PS-CVD5 + arm vs base (S32)\nfilled: q < .05; open: q ≥ .05", loc="left", fontsize=6.3, color=GREY, pad=4)
    letter(axA, "A", x=-0.85, y=1.0)
    letter(axB, "B", x=-0.06, y=1.04)
    # C: q-value landscape for every S32 contrast row
    ax = fig.add_axes([0.10, 0.06, 0.45, 0.27])
    s = SENS[SENS.set == "S32"]
    rng = np.random.default_rng(7)
    tot = 0
    for k, (cfg, cname) in enumerate(CONFIGS):
        d = s[s.config == cfg]
        for off, col, mk, colname in ((-0.25, NAVY, "o", "q_m54_p_fam"), (0.0, GOLD, "^", "q_absd_p_fam"), (0.25, GREY, "s", "q_bshuf_p_fam")):
            v = d[colname].dropna().clip(lower=1e-6).values
            ax.scatter(k + off + rng.uniform(-0.08, 0.08, len(v)), v, s=6, color=col, marker=mk, alpha=0.75, lw=0, zorder=2)
        qc = QC[(QC.set == "S32") & (QC.config == cfg)].iloc[0]
        assert int((d.q_m54_p_fam < 0.05).sum()) == qc.n_q05_m54 and int((d.q_absd_p_fam < 0.05).sum()) == qc.n_q05_absd
        tot += int(qc.n_contrasts)
        ax.text(k, 2.2, f"{int(qc.n_q05_m54)} | {int(qc.n_q05_absd)} | {int(qc.n_q05_bshuf)}", ha="center", fontsize=5.8)
        CHECK[f"fig5C {cfg}"] = (int(qc.n_contrasts), int(qc.n_q05_m54), int(qc.n_q05_absd), int(qc.n_q05_bshuf))
    ax.axhline(0.05, color=RED, ls="--", lw=0.8)
    ax.text(5.55, 0.05, "q = .05", fontsize=5.8, color=RED, va="center")
    ax.set_yscale("log")
    ax.set_ylim(1e-6 * 0.5, 6)
    ax.set_xticks(range(len(CONFIGS)), ["main", "caliper 0.1", "1:3", "IPTW", "overlap", "GBM PS"], fontsize=6.5)
    ax.set_ylabel("BH q (whole sweep, by family)", fontsize=7)
    n_agree = int(QC[QC.set == "S32"].n_q05_absd.sum() + QC[QC.set == "S32"].n_q05_bshuf.sum() + QC[QC.set == "S32"].n_q05_cons.sum())
    assert n_agree == 0
    ax.set_title(f"All {tot} S32 contrast rows. No agreement row reaches q < .05 in S32\n(numbers: rows with q < .05 for balance | "
                 "|Δ log HR| | benchmark permutation)", loc="left", fontsize=6.6, color=NAVY, pad=12)
    h = [Line2D([], [], color=NAVY, marker="o", ls="", ms=4, label="balance (mean |SMD|, 54)"),
         Line2D([], [], color=GOLD, marker="^", ls="", ms=4, label="agreement (|Δ log HR|)"),
         Line2D([], [], color=GREY, marker="s", ls="", ms=4, label="benchmark permutation")]
    ax.legend(handles=h, frameon=False, fontsize=5.8, loc="lower center", bbox_to_anchor=(0.5, -0.24), ncol=3)
    letter(ax, "C", x=-0.16, y=1.08)
    # D: agreement gain by label and tier
    ax = fig.add_axes([0.66, 0.06, 0.32, 0.27])
    L = LPT[LPT.in_S32]
    groups = [("Physio-\nlogic", lambda k, ph: ph), ("Not", lambda k, ph: not ph),
              ("Excellent\n/good", lambda k, ph: TIER[k] in ("Excellent", "Good")), ("Moderate", lambda k, ph: TIER[k] == "Moderate")]
    xs = [0, 1, 2.4, 3.4]
    lim = 0.3
    ncl = 0
    for (gl, f), x in zip(groups, xs):
        for a, off in (("ECG", -0.17), ("CLMBR", 0.17)):
            d = L[L.arm == a]
            v = np.array([g for k, ph, g in zip(d.key, d.physiologic, d.gain_absd) if f(k, ph)])
            jit = np.linspace(-0.07, 0.07, len(v))
            ncl += int((np.abs(v) > lim).sum())
            ax.scatter(x + off + jit, np.clip(v, -lim, lim), s=7, color=ARM[a][1], marker=ARM[a][2], alpha=0.55, lw=0)
            ax.plot([x + off - 0.12, x + off + 0.12], [v.mean()] * 2, color=ARM[a][1], lw=1.6)
            CHECK[f"fig5D {gl.replace(chr(10), '')} {a}"] = (len(v), round(v.mean(), 3))
    ax.axhline(0, color=GREY, ls="--", lw=0.7)
    ax.axvline(1.7, color=LGREY, lw=0.6)
    ax.set_xticks(xs, [g for g, _ in groups], fontsize=6.3)
    ax.set_ylim(-lim - 0.02, lim + 0.08)
    ax.set_ylabel("Agreement gain per trial:\n|Δ log HR| base − arm (> 0: closer)", fontsize=6.8)
    pe = LP[(LP.set == "S32") & (LP.config == "main") & (LP.arm == "ECG") & LP.endpoint.str.startswith("absd")].iloc[0]
    pc = LP[(LP.set == "S32") & (LP.config == "main") & (LP.arm == "CLMBR") & LP.endpoint.str.startswith("absd")].iloc[0]
    ax.text(0.5, lim + 0.05, f"label-perm. P: ECG {pv(pe.perm_p)},\nCLMBR-T {pv(pc.perm_p)}", ha="center", fontsize=5.6, va="center")
    ax.text(2.9, lim + 0.05, "quality tier:\ndescriptive only", ha="center", fontsize=5.6, va="center")
    if ncl:
        ax.set_xlabel(f"{ncl} trial points beyond ±{lim} drawn at the limit", fontsize=5.6, color=GREY)
    h = [Line2D([], [], color=ARM[a][1], marker=ARM[a][2], ls="", ms=4, label=ARM[a][0]) for a in ("ECG", "CLMBR")]
    ax.legend(handles=h, frameon=False, fontsize=5.8, loc="lower center", bbox_to_anchor=(0.5, -0.30), ncol=2)
    letter(ax, "D", x=-0.30, y=1.08)
    save(fig, OUTM / "figure5_replication")
    e = S("S32", "main", "P5: ECG vs base")
    cm = S("S32", "main", "P5: CLMBR vs base")
    bo = S("S32", "main", "P5: ECG+CLMBR vs base")
    m13 = S("S32", "m13", "P5: ECG vs base")
    FIGS.append(("main", "figure5_replication", "Figure 5. Replication across every configuration and arm",
                 f"(A) Balance and (B) agreement with the RCT result for each arm added to PS-CVD5 in each of the six matching / weighting "
                 f"configurations (S32); filled markers, q < .05. Balance gains replicate under caliper 0.1, 1:3 matching and overlap weights and are attenuated "
                 f"or lost under IPTW (weight-driven, low effective sample size) and, for the ECG, under the gradient-boosted PS. The permuted "
                 f"ECG slightly worsens balance under overlap weights and the gradient-boosted PS (q ≈ .05; two-sided). "
                 f"Agreement: |Δ log HR| falls from {e.absd_b:.3f} to {e.absd_a:.3f} (ECG), {cm.absd_a:.3f} (CLMBR-T) and "
                 f"{bo.absd_a:.3f} (both) in the main configuration, but benchmark-permutation P values are {pv(e.bshuf_p)}, "
                 f"{pv(cm.bshuf_p)} and {pv(bo.bshuf_p)}: attenuation toward the null, not trial-specific agreement. The ECG's "
                 f"1:3-matching row (P = {pv(m13.absd_p)}, permutation P = {pv(m13.bshuf_p)}) reproduces paper 1 but does not survive FDR "
                 f"(q = {pv(m13.q_absd_p_fam)}). (C) BH q for every S32 contrast row (all rungs, arms and head-to-heads) by configuration "
                 f"and family. No agreement row (|Δ log HR|, benchmark permutation or standardized-difference agreement) reaches q < .05 "
                 f"in S32, in any configuration. (D) Per-trial agreement gain for the ECG and CLMBR-T at PS-CVD5 (main) by physiologic "
                 f"label (label-permutation P shown) and by emulation-quality tier (descriptive; no test). Bars are group means.",
                 [("A", "core/sensitivity.csv (S32, contrasts 'P5: <arm> vs base', all configurations; relred54, q_m54_p_fam)"),
                  ("B", "core/sensitivity.csv (absd_a, absd_b, absd_better, absd_p, bshuf_p, q_absd_p_fam)"),
                  ("C", "core/sensitivity.csv (q_m54_p_fam, q_absd_p_fam, q_bshuf_p_fam; all S32 rows), counts checked against core/q_counts.csv"),
                  ("D", "core/labels_per_trial.csv (gain_absd), core/labels_physiologic.csv (absd endpoint P), docs/v19/quality_tiers.json")]))


# ================================================================ eFigure 1: plasmode
def efigure1():
    po = rd(PLAS / "pooled_trtC_cliniorient_p5.csv")
    av = rd(PLAS / "added_value_p5.csv")
    pf = rd(PLAS / "performance_trtC_cliniorient_p5.csv")
    po = po[po.analysis == "null-corrected"]
    av = av[av.analysis == "null-corrected"]
    confs = [("lvef", "LVEF"), ("ntprobnp", "NT-proBNP"), ("bmi", "BMI"), ("egfr", "eGFR"), ("all", "All")]
    fig = plt.figure(figsize=(7.2, 7.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.62, wspace=0.28)
    ax = fig.add_subplot(gs[0, :])
    arms = [("base", "PS-Demo", "white", GREY, ""), ("P5", "PS-CVD5", "white", NAVY, ""), ("P5ECG", "PS-CVD5 + ECG", RED, RED, ""),
            ("P5CLMBR", "PS-CVD5 + CLMBR-T", BLUE, BLUE, ""), ("P5ECGCLMBR", "PS-CVD5 + ECG + CLMBR-T", NAVY, NAVY, ""),
            ("CLMBRonly", "CLMBR-T only", "white", BLUE, "////"), ("ECGonly", "ECG only", "white", RED, "////"),
            ("P5shufCLMBR", "PS-CVD5 + permuted CLMBR-T", "white", GOLD, "")]
    w = 0.105
    for i, (c, cl) in enumerate(confs):
        for k, (a, lab, fc, ec, ht) in enumerate(arms):
            r = po[(po.conf == c) & (po.arm == a)].iloc[0]
            ax.bar(i + (k - 3.5) * w, r.pct_vs_unmatched, w * 0.92, color=fc, edgecolor=ec, hatch=ht, lw=0.8,
                   yerr=1.96 * r.mcse_vs_unmatched, error_kw=dict(lw=0.5, capsize=1.0), label=lab if i == 0 else None)
        o = po[(po.conf == c) & (po.arm == "oracle")].iloc[0]
        ax.text(i, 57, f"oracle {o.pct_vs_unmatched:.0f}%", ha="center", fontsize=6.0, color=GREY)
        CHECK[f"efig1A {c}"] = {a: round(po[(po.conf == c) & (po.arm == a)].pct_vs_unmatched.iloc[0], 1) for a, *_ in arms}
    ax.axhline(0, color=NAVY, lw=0.6)
    ax.set_xticks(range(len(confs)), [l for _, l in confs])
    ax.set_ylim(-14, 62)
    ax.set_ylabel("% of confounder-induced bias removed\nvs unmatched (null-corrected; ±1.96 MCSE)", fontsize=7)
    ax.legend(frameon=False, fontsize=6.0, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    letter(ax, "A", x=-0.08)
    ax = fig.add_subplot(gs[1, 0])
    cons = [("ECG over P5", "ECG over PS-CVD5", RED, ""), ("CLMBR-T over P5", "CLMBR-T over PS-CVD5", BLUE, ""),
            ("ECG+CLMBR-T over P5", "both over PS-CVD5", NAVY, ""), ("ECG over P5+CLMBR-T", "ECG over PS-CVD5 + CLMBR-T", "white", ""),
            ("CLMBR-T over P5+ECG", "CLMBR-T over PS-CVD5 + ECG", "white", ""), ("permuted CLMBR-T over P5 (placebo)", "permuted CLMBR-T (placebo)", GOLD, "")]
    edges = [RED, BLUE, NAVY, RED, BLUE, GOLD]
    w = 0.13
    for i, (c, cl) in enumerate(confs):
        for k, ((cn, lab, fc, ht), ec) in enumerate(zip(cons, edges)):
            r = av[(av.conf == c) & (av.contrast == cn)].iloc[0]
            ax.bar(i + (k - 2.5) * w, r.added_pct_of_ref_bias, w * 0.92, color=fc, edgecolor=ec, lw=0.8,
                   yerr=1.96 * r.mcse, error_kw=dict(lw=0.5, capsize=1.0), label=lab if i == 0 else None)
        CHECK[f"efig1B {c}"] = [round(av[(av.conf == c) & (av.contrast == cn)].added_pct_of_ref_bias.iloc[0], 1) for cn, *_ in cons]
    ax.axhline(0, color=NAVY, lw=0.6)
    ax.set_xticks(range(len(confs)), [l for _, l in confs], fontsize=6.6)
    ax.set_ylabel("% of the remaining bias removed\n(null-corrected; ±1.96 MCSE)", fontsize=7)
    ax.set_ylim(-3, 42)
    ax.legend(frameon=False, fontsize=5.6, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    letter(ax, "B", x=-0.2)
    ax = fig.add_subplot(gs[1, 1])
    p = pf[pf.conf == "all"].set_index("arm")
    carms = [("unmatched", "Unmatched", GREY, "white"), ("base", "PS-Demo", GREY, "white"), ("ECG", "PS-Demo + ECG", RED, RED),
             ("P5", "PS-CVD5", NAVY, "white"), ("P5ECG", "PS-CVD5 + ECG", RED, RED), ("P5CLMBR", "PS-CVD5 + CLMBR-T", BLUE, BLUE),
             ("P5ECGCLMBR", "PS-CVD5 + both", NAVY, NAVY), ("CLMBRonly", "CLMBR-T only", BLUE, "white"),
             ("P5shufCLMBR", "PS-CVD5 + perm. CLMBR-T", GOLD, "white"), ("oracle", "Oracle", NAVY, LGREY)]
    for k, (a, lab, ec, fc) in enumerate(carms):
        ax.bar(k, p.loc[a, "coverage"], 0.7, color=fc, edgecolor=ec, lw=0.8, yerr=1.96 * p.loc[a, "coverage_mcse"],
               error_kw=dict(lw=0.5, capsize=1.0))
    ax.axhline(95, color=GREY, ls="--", lw=0.7)
    ax.set_xticks(range(len(carms)), [l for _, l, *_ in carms], rotation=50, ha="right", fontsize=6.0)
    ax.set_ylim(40, 100)
    ax.set_ylabel("95% CI coverage of the true effect, %", fontsize=7)
    CHECK["efig1C coverage"] = {a: round(p.loc[a, "coverage"], 1) for a, *_ in carms}
    letter(ax, "C", x=-0.2)
    save(fig, OUTS / "efigure1_plasmode")
    g = lambda a, c="all": po[(po.conf == c) & (po.arm == a)].pct_vs_unmatched.iloc[0]
    ga = lambda cn, c="all": av[(av.conf == c) & (av.contrast == cn)].added_pct_of_ref_bias.iloc[0]
    FIGS.append(("supplementary", "efigure1_plasmode", "eFigure 1. Plasmode simulation with PS-CVD5, ECG and CLMBR-T arms",
                 f"Clinically oriented design with treatment driven by the withheld confounder only (107 trial × confounder cells in 31 "
                 f"trials, 50 replicates, 9 non-null scenarios, true HR 0.80). (A) % of confounder-induced bias removed vs unmatched "
                 f"(null-corrected). All confounders: PS-CVD5 {g('P5'):.1f}%, + ECG {g('P5ECG'):.1f}%, + CLMBR-T {g('P5CLMBR'):.1f}%, "
                 f"+ both {g('P5ECGCLMBR'):.1f}%, oracle {g('oracle'):.1f}%. (B) Share of PS-CVD5's remaining bias removed by adding "
                 f"each representation: ECG {ga('ECG over P5'):.1f}%, CLMBR-T {ga('CLMBR-T over P5'):.1f}%, both "
                 f"{ga('ECG+CLMBR-T over P5'):.1f}%, permuted CLMBR-T {ga('permuted CLMBR-T over P5 (placebo)'):.1f}%. For LVEF the ECG "
                 f"adds more than CLMBR-T ({ga('ECG over P5', 'lvef'):.1f}% vs {ga('CLMBR-T over P5', 'lvef'):.1f}%); for eGFR and "
                 f"NT-proBNP CLMBR-T adds far more (coded kidney / heart-failure care is proxy information, not physiology). "
                 f"(C) Coverage of the true effect (all confounders); no representation approaches the oracle. MCSEs reflect "
                 f"simulation error only. The clinical orientation is post hoc (inherited from paper 1).",
                 [("A", "plasmode/pooled_trtC_cliniorient_p5.csv (analysis = null-corrected; pct_vs_unmatched, mcse_vs_unmatched)"),
                  ("B", "plasmode/added_value_p5.csv (null-corrected; added_pct_of_ref_bias, mcse)"),
                  ("C", "plasmode/performance_trtC_cliniorient_p5.csv (conf = all; coverage, coverage_mcse)")]))


# ================================================================ eFigure 2: MIMIC-IV
MNAME = {"plato": "PLATO", "aristotle": "ARISTOTLE", "rocket_af": "ROCKET AF", "transform_hf": "TRANSFORM-HF", "comet": "COMET",
         "soap2": "SOAP II [OR]", "elite2": "ELITE II", "peptic": "PEPTIC (negative control) [RR]"}


def efigure2():
    sm = rj(MIM / "summary/summary.json")
    wf = rd(MIM / "windowfix/summary/balance.csv")
    fig = plt.figure(figsize=(7.2, 6.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1, 1.1], hspace=0.62, wspace=0.75)
    ax = fig.add_subplot(gs[0, 0])
    bases = [("demo", "PS-Demo (paper 1)"), ("cvd5", "PS-CVD5 (primary)"), ("cvd5_anydm", "CVD5, any diabetes"),
             ("cvd5_incl", "CVD5, incl. index admission")]
    y, ys, yl = 0, [], []
    for b, bl in bases:
        for pop, pl, dy in (("all", "all patients", 0), ("no_index_day_ecg", "no index-day ECG", 0)):
            r = sm["balance"][f"primary7|{b}|{pop}"]
            lo, hi = r["relred_ECG_ci"]
            ax.plot([lo, hi], [y, y], color=RED, lw=1.0)
            ax.plot(r["relred_ECG"], y, "o", color=RED, mfc=RED if pop == "all" else "white", ms=4.4)
            ax.plot(r["relred_permECG"], y, "^", color=GOLD, mfc="white", ms=4.2)
            ax.text(1.03, y, f"{r['lower_smd_ECG']}", transform=ax.get_yaxis_transform(), fontsize=5.8, va="center")
            ys.append(y)
            yl.append(f"{bl}, {pl}" if pop == "all" else pl)
            CHECK[f"efig2A {b} {pop}"] = (round(r["relred_ECG"], 1), round(lo, 1), round(hi, 1), r["lower_smd_ECG"], round(r["relred_permECG"], 1))
            y -= 1
        y -= 0.5
    ax.set_yticks(ys, yl, fontsize=5.8)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_xlabel("Relative reduction in mean |SMD| with the\nECG, 26 held-out items, % (95% CI)", fontsize=6.8)
    ax.text(1.03, 1.0, "lower", transform=ax.transAxes, fontsize=6, fontweight="bold", va="bottom")
    h = [Line2D([], [], color=RED, marker="o", ls="", label="+ ECG"), Line2D([], [], color=GOLD, marker="^", mfc="white", ls="", label="+ permuted ECG")]
    ax.legend(handles=h, frameon=False, fontsize=5.8, loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2)
    letter(ax, "A", x=-1.05, y=1.04)
    # C: window fix
    ax = fig.add_subplot(gs[0, 1])
    y, ys, yl = 0, [], []
    for b, bl in (("sparse", "PS-Sparse"), ("hdPS200", "hdPS"), ("clinical", "PS-Clinical-lite")):
        for ver, vl, mfc in (("v20", "v20 (as published)", "white"), ("fixed", "window-fixed", RED)):
            r = wf[(wf.set == "primary7") & (wf.base == b) & (wf["pop"] == "all") & (wf.version == ver) & (wf.arm == "ECG")].iloc[0]
            ax.plot([r.ci4000_lo, r.ci4000_hi], [y, y], color=RED, lw=1.0)
            ax.plot(r.relred, y, "o", color=RED, mfc=mfc, ms=4.4)
            ys.append(y)
            yl.append(f"{bl}, {vl}")
            CHECK[f"efig2B {b} {ver}"] = (round(r.relred, 1), round(r.ci4000_lo, 1), round(r.ci4000_hi, 1))
            y -= 1
        y -= 0.5
    ax.set_yticks(ys, yl, fontsize=5.8)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_xlabel("Relative reduction in mean |SMD| with the\nECG, % (4,000-resample CI); 7 trials", fontsize=6.8)
    ax.set_title("Diagnosis-window fix (SOAP II, ELITE II, PEPTIC)", loc="left", fontsize=6.6, color=GREY)
    letter(ax, "B", x=-0.95, y=1.04)
    # B: per-trial HRs, PS-CVD5
    ax = fig.add_subplot(gs[1, :])
    order = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2", "peptic"]
    lo_, hi_ = np.log(0.2), np.log(3.0)
    clip = lambda v: min(max(v, lo_), hi_)
    for r_, t in enumerate(order):
        y = len(order) - 1 - r_
        pt = sm["per_trial"][t]
        rct = pt["cvd5|base"]["rct"]
        ax.plot([np.log(rct)] * 2, [y - 0.4, y + 0.4], color=NAVY, lw=1.8)
        for k, (a, col, mk, mfc) in enumerate((("base", NAVY, "o", "white"), ("ECG", RED, "o", RED), ("permECG", GOLD, "^", "white"))):
            d = pt[f"cvd5|{a}"]
            yy = y + 0.22 - 0.22 * k
            ax.plot([clip(np.log(d["lo"])), clip(np.log(d["hi"]))], [yy] * 2, color=col, lw=0.9)
            ax.plot(clip(np.log(d["hr"])), yy, mk, color=col, mfc=mfc, ms=4.0, mew=0.9)
        CHECK[f"efig2C {t}"] = (pt["cvd5|base"]["hr"], pt["cvd5|ECG"]["hr"], pt["cvd5|permECG"]["hr"], rct)
    ax.set_yticks(range(len(order))[::-1], [MNAME[t] for t in order], fontsize=6.3)
    ax.axvline(0, color=GREY, ls=":", lw=0.7)
    tk = [0.25, 0.5, 1, 2]
    ax.set_xticks(np.log(tk), [str(x) for x in tk])
    ax.set_xlim(lo_, hi_)
    ax.set_xlabel("Hazard ratio (log scale); vertical bar: RCT estimate")
    h = [Line2D([], [], color=NAVY, marker="o", mfc="white", ls="", label="PS-CVD5"), Line2D([], [], color=RED, marker="o", ls="", label="+ ECG"),
         Line2D([], [], color=GOLD, marker="^", mfc="white", ls="", label="+ permuted ECG")]
    ax.legend(handles=h, frameon=False, fontsize=6.3, loc="lower center", bbox_to_anchor=(0.6, 1.0), ncol=3)
    letter(ax, "C", x=-0.25, y=1.0)
    save(fig, OUTS / "efigure2_mimic")
    c5 = sm["balance"]["primary7|cvd5|all"]
    ag = sm["agreement"]["primary7|cvd5|all"]
    c_txt = (f"(C) Per-trial hazard ratios (95% CI) under PS-CVD5, + ECG and + permuted ECG. Mean |Δ log HR| "
             f"{ag['base']['mean_abs_diff']:.3f} → {ag['ECG']['mean_abs_diff']:.3f} with the ECG and "
             f"{ag['permECG']['mean_abs_diff']:.3f} with the permuted ECG: no ECG-specific agreement gain. ")
    FIGS.append(("supplementary", "efigure2_mimic", "eFigure 2. MIMIC-IV external replication with a PS-CVD5 analog (ECG only)",
                 f"Seven cardiovascular trials plus PEPTIC (negative control); no CLMBR-T in MIMIC. (A) Relative reduction in mean |SMD| "
                 f"over the 26-item held-out panel when the ECG is added to each base PS (2,000-resample trial bootstrap, as v20). "
                 f"PS-CVD5 (diagnoses from earlier admissions only): {ci_txt(c5['relred_ECG'], *c5['relred_ECG_ci'])}%, lower in "
                 f"{c5['lower_smd_ECG']} trials; permuted ECG {num(c5['relred_permECG'])}%. Near-identical specifications move the point "
                 f"estimate by about ±5 points; open markers, index-day ECGs excluded. (B) Window-fix "
                 f"sensitivity for paper 1's MIMIC numbers (open: v20 as published; filled: window-fixed): index-admission diagnoses removed from the v20 sparse, hdPS and "
                 f"PS-Clinical-lite PS for SOAP II, ELITE II and PEPTIC (4,000-resample CI, the paper.md convention). "
                 f"{c_txt}P values nominal; no FDR (single supplementary family).",
                 [("A", "mimic/summary/summary.json (balance['primary7|<base>|<pop>'])"),
                  ("B", "mimic/windowfix/summary/balance.csv (set = primary7, pop = all, arm = ECG; relred, ci4000_lo/hi)"),
                  ("C", "mimic/summary/summary.json (per_trial[<trial>]['cvd5|<arm>']: hr, lo, hi, rct)")]))


# ================================================================ eFigure 3: all-configuration sweep
def efigure3():
    s = SENS[SENS.set == "S32"]
    rows = list(dict.fromkeys(s[s.config == "main"].contrast))
    nm = lambda c: (c.replace("P1", "PS-Demo").replace("P5", "PS-CVD5").replace("Flags", "PS-Flags").replace("clinical", "PS-Clinical")
                    .replace("shufECG", "perm. ECG").replace("shufCLMBR", "perm. CLMBR-T").replace("CLMBR32", "CLMBR-T(32)")
                    .replace("CLMBR", "CLMBR-T").replace("CLMBR-T-T", "CLMBR-T").replace("+", " + ")
                    .replace(" base", "" if ":" not in c else " base"))
    cfgs = [c for c, _ in CONFIGS]
    Mb = np.full((len(rows), 6), np.nan)
    Qb, Pb, Ma, Qa, Pa = (Mb.copy() for _ in range(5))
    for i, c in enumerate(rows):
        for j, cfg in enumerate(cfgs):
            r = s[(s.contrast == c) & (s.config == cfg)]
            if len(r):
                r = r.iloc[0]
                Mb[i, j], Qb[i, j], Pb[i, j] = r.relred54, r.q_m54_p_fam, r.m54_p
                Ma[i, j], Qa[i, j], Pa[i, j] = 100 * (r.absd_b_pair - r.absd_a_pair), r.q_absd_p_fam, r.absd_p
    fig = plt.figure(figsize=(7.2, 10.6))
    ax = fig.add_axes([0.30, 0.04, 0.32, 0.89])
    heat(ax, Mb, Qb, Pb, [nm(c) for c in rows], ["main", "cal.\n0.1", "1:3", "IPTW", "over-\nlap", "GBM"], vmax=30, fs=4.9)
    ax.tick_params(axis="y", labelsize=5.4)
    ax.set_title("Balance: relative reduction in\nmean |SMD|, 54 items, %", fontsize=6.6, color=NAVY, pad=18)
    letter(ax, "A", x=-0.85, y=1.03)
    ax2 = fig.add_axes([0.665, 0.04, 0.32, 0.89], sharey=ax)
    heat(ax2, Ma, Qa, Pa, [nm(c) for c in rows], ["main", "cal.\n0.1", "1:3", "IPTW", "over-\nlap", "GBM"], vmax=8, fs=4.9)
    ax2.tick_params(axis="y", left=False, labelleft=False)
    ax2.set_title("Agreement: reduction in mean\n|Δ log HR| × 100 (> 0: closer)", fontsize=6.6, color=NAVY, pad=18)
    letter(ax2, "B", x=-0.05, y=1.03)
    for a in (ax, ax2):
        prev = None
        for i, c in enumerate(rows):
            g = c.split(":")[0] if ":" in c else "across"
            g = "clmbr32" if "CLMBR32" in c else g
            if prev is not None and g != prev:
                a.axhline(i - 0.5, color=NAVY, lw=0.7)
            prev = g
    cbar(fig, [0.30, 0.012, 0.25, 0.006], 30, "balance, % (clipped ±30)")
    cbar(fig, [0.665, 0.012, 0.25, 0.006], 8, "agreement × 100 (clipped ±8)")
    CHECK["efig3 rows"] = len(rows)
    CHECK["efig3 n q<.05 balance / agreement"] = (int(np.nansum(Qb < 0.05)), int(np.nansum(Qa < 0.05)))
    save(fig, OUTS / "efigure3_all_configurations")
    FIGS.append(("supplementary", "efigure3_all_configurations", "eFigure 3. Every contrast in every configuration (S32)",
                 f"All {len(rows)} S32 contrast rows (within-rung, cross-rung head-to-heads and CLMBR-T 32-PC rows, which exist for the "
                 f"main configuration only) × 6 configurations. (A) Balance: relative reduction in mean |SMD| over the 54 items. "
                 f"(B) Agreement: reduction in mean |Δ log HR| vs the RCT, × 100, paired over trials with an estimate in both PS models "
                 f"(positive = the first-named PS is closer). "
                 f"Bold * marks q < .05 from BH across the whole S32 sweep within each family (balance: {int(np.nansum(Qb < 0.05))} "
                 f"cells; agreement: {int(np.nansum(Qa < 0.05))}); ° marks nominal P < .05 only. One-sided for 'arm better than base' "
                 f"and 'embedding better than placebo'; two-sided for head-to-heads, CLMBR-T vs ECG and placebo vs base. The extreme "
                 f"IPTW rows against PS-Flags and hdPS200 reflect near-separation of those rich PS models (median ESS fraction 0.18 "
                 f"and 0.34), not a CLMBR-T effect.",
                 [("A", "core/sensitivity.csv (set = S32; relred54, m54_p, q_m54_p_fam)"),
                  ("B", "core/sensitivity.csv (absd_b_pair − absd_a_pair, absd_p, q_absd_p_fam)")]))


# ================================================================ eFigure 4: PS-Flags fairness and retention
def efigure4():
    fig = plt.figure(figsize=(7.2, 6.8))
    gs = fig.add_gridspec(2, 2, hspace=0.62, wspace=0.95, width_ratios=[1, 1.15])
    # A: retention (means / medians over trials; cells with 1-10 pairs excluded upstream)
    ax = fig.add_subplot(gs[0, 0])
    R = RET[RET.analysis.str.startswith("retention") & (RET.set == "S32")]
    arms = ["P5 base", "P5 ECG", "P5 CLMBR", "P5 ECG+CLMBR", "P1 CLMBR", "Flags base", "hdPS200 base", "clinical base"]
    LABS = {"P5 base": "PS-CVD5", "P5 ECG": "PS-CVD5 + ECG", "P5 CLMBR": "PS-CVD5 + CLMBR-T", "P5 ECG+CLMBR": "PS-CVD5 + ECG + CLMBR-T",
            "P1 base": "PS-Demo", "P1 CLMBR": "PS-Demo + CLMBR-T", "Flags base": "PS-Flags (C = 1)", "hdPS200 base": "hdPS200",
            "clinical base": "PS-Clinical"}
    lab = LABS.get
    for k, a in enumerate(arms):
        r = R[R.arm == a].iloc[0]
        col = BLUE if "CLMBR" in a else (RED if "ECG" in a else NAVY)
        ax.barh(-k, r["mean"], 0.6, color="white", edgecolor=col, lw=0.9)
        ax.plot(r["median"], -k, "|", color=col, ms=8, mew=1.4)
        ax.text(1.02, -k, f"{r['mean']:.2f} / {r['median']:.2f}", va="center", fontsize=5.8, transform=ax.get_yaxis_transform())
        CHECK[f"efig4A {a}"] = (int(r.k), round(r["mean"], 3), round(r["median"], 3))
    ax.set_yticks([-k for k in range(len(arms))], [lab(a) for a in arms], fontsize=6.0)
    ax.set_xlim(0.5, 1.0)
    ax.text(1.02, 1.0, "mean / median", transform=ax.transAxes, fontsize=5.8, fontweight="bold", va="bottom")
    ax.set_xlabel("Matched share of the smaller arm, main\n(bar: mean; tick: median over trials)", fontsize=6.6)
    letter(ax, "A", x=-0.75)
    # B: ESS fraction under weighting
    ax = fig.add_subplot(gs[0, 1])
    E = RET[RET.analysis.str.startswith("ESS")]
    earms = ["P1 base", "P1 CLMBR", "P5 base", "P5 ECG", "P5 CLMBR", "Flags base", "hdPS200 base", "clinical base"]
    for k, a in enumerate(earms):
        for cfg, off, mfc in (("iptw", 0.15, NAVY), ("overlap", -0.15, "white")):
            r = E[(E.arm == a) & E.analysis.str.endswith(cfg)].iloc[0]
            ax.plot([r["min"], r["median"]], [-k + off] * 2, color=LGREY, lw=0.8)
            ax.plot(r["median"], -k + off, "o", color=NAVY, mfc=mfc, ms=4)
            ax.plot(r["min"], -k + off, "|", color=GREY, ms=5)
            CHECK[f"efig4B {a} {cfg}"] = (round(r["median"], 3), round(r["min"], 3))
    ax.set_yticks([-k for k in range(len(earms))], [lab(a) for a in earms], fontsize=6.0)
    ax.set_xlim(0, 1)
    ax.set_xlabel("ESS fraction min(ESS_t/n_t, ESS_c/n_c)\n(dot: median; tick: minimum over trials)", fontsize=6.6)
    h = [Line2D([], [], color=NAVY, marker="o", ls="", label="IPTW"), Line2D([], [], color=NAVY, marker="o", mfc="white", ls="", label="overlap")]
    ax.legend(handles=h, frameon=False, fontsize=6.0, loc="lower right")
    letter(ax, "B", x=-0.7)
    # C: restriction sensitivity
    ax = fig.add_subplot(gs[1, 0])
    sub = RET[RET.set == "S32 subset"]
    y, ys, yl = 0, [], []
    for a in ("ECG", "CLMBR", "ECG+CLMBR"):
        full = S("S32", "main", f"P5: {a} vs base")
        ov = S("S32", "overlap", f"P5: {a} vs base")
        items = [("all 32 trials (main)", full.relred54, full.relred54_lo, full.relred54_hi, True),
                 ("CLMBR-T retention drop ≤ 0.05 (15)", *sub[(sub.arm == a) & sub.analysis.str.contains("<=")][["relred", "relred_lo", "relred_hi"]].iloc[0], False),
                 ("drop > 0.05 (17)", *sub[(sub.arm == a) & sub.analysis.str.contains("> 0.05")][["relred", "relred_lo", "relred_hi"]].iloc[0], False),
                 ("overlap weights, no trimming (32)", ov.relred54, ov.relred54_lo, ov.relred54_hi, False)]
        for lb, e_, lo, hi, _ in items:
            ax.plot([lo, hi], [y, y], color=ARM[a][1], lw=1.0)
            mark(ax, e_, y, a, True, ms=4.2)
            ys.append(y)
            yl.append(f"{ARM[a][0]}: {lb}" if lb.startswith("all") else lb)
            CHECK[f"efig4C {a} {lb}"] = (round(e_, 1), round(lo, 1), round(hi, 1))
            y -= 1
        y -= 0.5
    ax.set_yticks(ys, yl, fontsize=5.6)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    rho = RET[(RET.analysis.str.startswith("Spearman")) & (RET.arm == "CLMBR")].iloc[0]
    ax.set_xlabel(f"Relative reduction in mean |SMD| vs PS-CVD5, %\nper-trial CLMBR-T gain vs its retention loss: Spearman ρ = {rho.rho:.2f}, P = {pv(rho.p)}", fontsize=6.6)
    letter(ax, "C", x=-1.25)
    # D: CV-tuned PS-Flags rows
    ax = fig.add_subplot(gs[1, 1])
    rows = [("FlagsCV: CLMBR vs base", "CLMBR", "PS-Flags CV + CLMBR-T vs PS-Flags CV"), ("FlagsCV: ECG vs base", "ECG", "PS-Flags CV + ECG vs PS-Flags CV"),
            ("FlagsCV base vs Flags base (C=1)", "ECG+CLMBR", "PS-Flags CV vs PS-Flags C = 1"), ("P1+CLMBR vs FlagsCV base", "CLMBR", "PS-Demo + CLMBR-T vs PS-Flags CV")]
    y, ys, yl = 0, [], []
    for con, a, lb in rows:
        ax.text(-0.03, y, lb, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=5.9, fontweight="bold")
        y -= 1
        for cfg in ("main", "m13", "overlap"):
            r = S("S32", cfg, con, FCV)
            col = GREY if "base vs" in con else ARM[a][1]
            ax.plot([r.relred54_lo, r.relred54_hi], [y, y], color=col, lw=1.0)
            ax.plot(r.relred54, y, "o" if "base vs" in con else ARM[a][2], color=col, ms=4.2)
            ax.text(1.03, y, pv(r.bshuf_p), transform=ax.get_yaxis_transform(), fontsize=5.6, va="center")
            ys.append(y)
            yl.append({"main": "main", "m13": "1:3", "overlap": "overlap"}[cfg])
            CHECK[f"efig4D {con} {cfg}"] = (round(r.relred54, 1), round(r.relred54_lo, 1), round(r.relred54_hi, 1), pv(r.m54_p), pv(r.bshuf_p))
            y -= 1
        y -= 0.4
    ax.set_yticks(ys, yl, fontsize=5.8)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_ylim(y + 0.5, 0.6)
    ax.text(1.03, 1.0, "agreement\nperm. P", transform=ax.transAxes, fontsize=5.8, fontweight="bold", va="bottom")
    ax.set_xlabel("Relative reduction in mean |SMD|, 54 items, %\n(sensitivity rows, outside the FDR sweep)", fontsize=6.6)
    letter(ax, "D", x=-1.25)
    save(fig, OUTS / "efigure4_flags_fairness_retention")
    cv = S("S32", "main", "P1+CLMBR vs FlagsCV base", FCV)
    FIGS.append(("supplementary", "efigure4_flags_fairness_retention", "eFigure 4. Retention, weighting and PS-Flags regularisation sensitivities",
                 "(A) Matched share of the smaller arm (main configuration, S32): CLMBR-T arms trim about 10 points more than base or ECG; "
                 "PS-Flags (C = 1) trims most. Means and medians are over trials; cells with 1–10 matched pairs are excluded upstream "
                 "(PS-Flags: 31 trials), and no per-trial retention is shown. (B) Effective-sample-size fraction under IPTW and overlap "
                 "weights: rich PS models (PS-Flags, hdPS200) have extreme IPTW weights. (C) Is the matched-sample gain a restriction "
                 "effect? The gains persist in the 15 trials where CLMBR-T loses ≤ 5 points of retention and under overlap weights, "
                 "which trim no one. (D) CV-tuned PS-Flags (L2 C chosen per trial by 5-fold CV): adding CLMBR-T or the ECG to the tuned "
                 f"flags helps only under overlap weights; PS-Demo + CLMBR-T vs tuned PS-Flags {ci_txt(cv.relred54, cv.relred54_lo, cv.relred54_hi)}% "
                 f"(main). Its agreement contrast has benchmark-permutation P = {pv(cv.bshuf_p)} in main (nominal, not overlap-robust).",
                 [("A", "core/retention_sens.csv (analysis = retention ..., set = S32; mean, median)"),
                  ("B", "core/retention_sens.csv (analysis = ESS fraction ...; median, min)"),
                  ("C", "core/retention_sens.csv (set = S32 subset; relred, relred_lo/hi; Spearman row) + core/sensitivity.csv (all-trial and overlap rows)"),
                  ("D", "core/flagscv.csv (set = S32; relred54, relred54_lo/hi, bshuf_p)")]))


# ================================================================ eFigure 5: 38-trial and CLMBR-T 32-PC sensitivities
def efigure5():
    fig = plt.figure(figsize=(7.2, 7.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.25, 1], hspace=0.55, wspace=1.15)
    ax = fig.add_subplot(gs[0, :])
    cons = [("P5: ECG vs base", "PS-CVD5 + ECG", "ECG"), ("P5: CLMBR vs base", "PS-CVD5 + CLMBR-T", "CLMBR"),
            ("P5: ECG+CLMBR vs base", "PS-CVD5 + ECG + CLMBR-T", "ECG+CLMBR"), ("P5: CLMBR vs ECG", "PS-CVD5: CLMBR-T vs ECG", "CLMBR"),
            ("P1+CLMBR vs Flags base", "PS-Demo + CLMBR-T vs PS-Flags", "CLMBR"), ("P5+CLMBR vs hdPS200 base", "PS-CVD5 + CLMBR-T vs hdPS200", "CLMBR"),
            ("P5+CLMBR vs clinical base", "PS-CVD5 + CLMBR-T vs PS-Clinical", "CLMBR")]
    for i, (c, lb, a) in enumerate(cons):
        for st, off, filled in (("S32", 0.17, True), ("S38", -0.17, False)):
            r = S(st, "main", c)
            y = -i + off
            ax.plot([r.relred54_lo, r.relred54_hi], [y, y], color=ARM[a][1], lw=1.0)
            mark(ax, r.relred54, y, a, filled, ms=4.4)
            ax.text(1.02, y, f"{st}: {ci_txt(r.relred54, r.relred54_lo, r.relred54_hi)}; q {pv(r.q_m54_p_fam)} | |Δ| {r.absd_b_pair:.3f} → "
                    f"{r.absd_a_pair:.3f}, perm. P {pv(r.bshuf_p)}", transform=ax.get_yaxis_transform(), fontsize=5.8, va="center")
            CHECK[f"efig5A {st} {c}"] = (round(r.relred54, 1), round(r.relred54_lo, 1), round(r.relred54_hi, 1), pv(r.q_m54_p_fam), round(r.absd_a_pair, 3), pv(r.bshuf_p))
    ax.set_yticks([-i for i in range(len(cons))], [lb for _, lb, _ in cons], fontsize=6.3)
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_xlim(-15, 25)
    ax.set_xlabel("Relative reduction in mean |SMD|, 54 items, % (95% CI); main configuration")
    q38 = QC[QC.set == "S38"]
    ax.set_title(f"Filled: 32 analysed trials (S32); open: all 38 (S38). S38 agreement rows with q < .05: "
                 f"{int(q38.n_q05_absd.sum())} (|Δ|) + {int(q38.n_q05_bshuf.sum())} (perm.), all under the GBM PS", loc="left", fontsize=6.4, color=GREY)
    letter(ax, "A", x=-0.3)
    # B: CLMBR-T 32 vs 64 PCs
    ax = fig.add_subplot(gs[1, 0])
    rows = [("P1: CLMBR vs base", "PS-Demo + CLMBR-T (64)", "CLMBR"), ("P1: CLMBR32 vs base", "PS-Demo + CLMBR-T (32)", "CLMBR32"),
            ("P1: CLMBR vs CLMBR32", "PS-Demo: 64 vs 32 PCs", "CLMBR"), ("P5: CLMBR vs base", "PS-CVD5 + CLMBR-T (64)", "CLMBR"),
            ("P5: CLMBR32 vs base", "PS-CVD5 + CLMBR-T (32)", "CLMBR32"), ("P5: CLMBR vs CLMBR32", "PS-CVD5: 64 vs 32 PCs", "CLMBR"),
            ("P5: CLMBR32 vs ECG", "PS-CVD5: CLMBR-T (32) vs ECG", "CLMBR32"), ("P1+CLMBR32 vs Flags base", "PS-Demo + CLMBR-T (32) vs PS-Flags", "CLMBR32")]
    for i, (c, lb, a) in enumerate(rows):
        r = S("S32", "main", c)
        ax.plot([r.relred54_lo, r.relred54_hi], [-i, -i], color=ARM[a][1] if a != "CLMBR32" else "#5f8fcf", lw=1.0)
        mark(ax, r.relred54, -i, a, r.q_m54_p_fam < 0.05, ms=4.4)
        ax.text(1.03, -i, pv(r.q_m54_p_fam), transform=ax.get_yaxis_transform(), fontsize=5.8, va="center")
        CHECK[f"efig5B {c}"] = (round(r.relred54, 1), round(r.relred54_lo, 1), round(r.relred54_hi, 1), pv(r.q_m54_p_fam))
    ax.set_yticks([-i for i in range(len(rows))], [lb for _, lb, _ in rows], fontsize=5.9)
    ax.text(1.03, 1.0, "q", transform=ax.transAxes, fontsize=6.2, fontweight="bold", va="bottom")
    ax.axvline(0, color=GREY, ls="--", lw=0.7)
    ax.set_xlabel("Relative reduction in mean |SMD|, %\n(S32, main; filled: q < .05)", fontsize=6.6)
    letter(ax, "B", x=-1.3)
    # C: domain heatmap 64 vs 32
    ax = fig.add_subplot(gs[1, 1])
    hrows = [("P5: CLMBR vs base", "CLMBR-T 64"), ("P5: CLMBR32 vs base", "CLMBR-T 32"), ("P5: CLMBR32 vs ECG", "32 vs ECG")]
    M, Q, P = [], [], []
    for c, _ in hrows:
        d = HD[(HD.set == "S32") & (HD.config == "main") & (HD.contrast == c)].set_index("domain").loc[DOMS]
        M.append(d.relred.values)
        Q.append(d.q_domain_fam.values)
        P.append(d.p.values)
        CHECK[f"efig5C {c}"] = [round(v, 1) for v in d.relred.values]
    heat(ax, np.array(M).T, np.array(Q).T, np.array(P).T, [DOMLAB[d].replace("\n", " ") for d in DOMS], [l for _, l in hrows], fs=5.8)
    ax.tick_params(axis="y", labelsize=5.8)
    ax.tick_params(axis="x", labelsize=5.8)
    letter(ax, "C", x=-0.95, y=1.08)
    save(fig, OUTS / "efigure5_s38_clmbr32")
    FIGS.append(("supplementary", "efigure5_s38_clmbr32", "eFigure 5. 38-trial and CLMBR-T 32-PC sensitivities",
                 "(A) Key contrasts in the main configuration for the 32 analysed trials (filled) and all 38 trials (open); the right-hand "
                 "text gives the balance estimate with its q and the paired agreement means with the benchmark-permutation P. S38 gives the same "
                 "picture; its only agreement rows with q < .05 are isolated gradient-boosted-PS rows (not shown). (B) CLMBR-T with 32 "
                 "instead of 64 principal components (the same SVD, first 32 PCs; main configuration only): the balance gain and the "
                 "PS-Flags head-to-head are essentially unchanged, so the CLMBR-T gain is not a dimension artefact. (C) Per-domain relative "
                 "reduction at PS-CVD5 for 64 and 32 PCs and for CLMBR-T (32) vs ECG (exploratory; * q < .05 domain family, ° nominal P < .05).",
                 [("A", "core/sensitivity.csv (set = S32 and S38, config = main; relred54, q_m54_p_fam, absd_b_pair, absd_a_pair, bshuf_p); S38 q counts from core/q_counts.csv"),
                  ("B", "core/sensitivity.csv (kind = clmbr32 and within; S32, main)"),
                  ("C", "core/headline_domains.csv (S32, main; P5 CLMBR / CLMBR32 rows)")]))


# ================================================================ spot checks vs PAPER2_RESULTS.md
def spot_checks():
    exp = {("P5: ECG vs base", "relred54"): 8.8, ("P5: CLMBR vs base", "relred54"): 12.4, ("P5: ECG+CLMBR vs base", "relred54"): 13.5,
           ("P5: ECG vs base", "relred54_lo"): 4.4, ("P5: ECG vs base", "relred54_hi"): 13.3, ("P5: CLMBR vs base", "relred54_lo"): 7.1,
           ("P5: CLMBR vs base", "relred54_hi"): 17.7, ("P5: ECG+CLMBR vs base", "relred54_lo"): 6.6, ("P5: ECG+CLMBR vs base", "relred54_hi"): 20.4,
           ("P1+CLMBR vs Flags base", "relred54"): 0.7, ("P1+CLMBR vs Flags base", "relred54_lo"): -5.5, ("P1+CLMBR vs Flags base", "relred54_hi"): 6.8,
           ("hdPS200: ECG vs base", "relred54"): 7.6, ("P5+CLMBR vs clinical base", "relred54"): -4.9}
    for (c, col), v in exp.items():
        got = round(float(S("S32", "main", c)[col]), 1)
        assert got == v, (c, col, got, v)
        h = HEAD[(HEAD.set == "S32") & (HEAD.config == "main") & (HEAD.contrast == c)]
        assert len(h) == 1 and round(float(h[col].iloc[0]), 1) == v, ("headline.csv", c, col)
    r = S("S32", "main", "P1+CLMBR vs Flags base")
    assert (r.m54_better, pv(r.m54_p), round(r.absd_b_pair, 3), round(r.absd_a_pair, 3), pv(r.bshuf_p)) == ("13/31", ".81", 0.186, 0.174, ".97")
    r = S("S32", "main", "P5: ECG vs base")
    assert (round(r.absd_b, 3), round(r.absd_a, 3), r.absd_better, pv(r.absd_p), pv(r.bshuf_p)) == (0.226, 0.196, "20/32", ".049", ".70")
    r = S("S32", "main", "P1+CLMBR vs FlagsCV base", FCV)
    assert (round(r.relred54, 1), round(r.relred54_lo, 1), round(r.relred54_hi, 1)) == (-1.5, -7.5, 4.4)
    r = LP[(LP.set == "S32") & (LP.config == "main") & (LP.arm == "ECG") & LP.endpoint.str.startswith("m54")].iloc[0]
    assert (round(r.relred_yes, 1), round(r.relred_no, 1), pv(r.perm_p)) == (16.3, 5.7, ".048")
    assert int(QC[QC.set == "S32"].n_contrasts.sum()) == 337 and int(QC[QC.set == "S32"].n_q05_absd.sum()) == 0
    print("spot checks vs PAPER2_RESULTS.md: OK")


# ================================================================ HTML gallery
def write_html():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    parts = ["<!doctype html><html lang='en'><head><meta charset='utf-8'><title>TRACE-ECG paper 2 figures</title>",
             "<style>body{font-family:'Nimbus Sans',Helvetica,Arial,sans-serif;color:#0d1040;background:#fcfcfb;max-width:1100px;margin:auto;"
             "padding:24px;line-height:1.45}h1{font-size:22px}h2{font-size:17px;margin-top:40px;border-top:1px solid #d9dbe6;padding-top:18px}"
             "img{max-width:100%;border:1px solid #eee;background:white}p.leg{font-size:14px}table{border-collapse:collapse;font-size:12.5px}"
             "td,th{border:1px solid #d9dbe6;padding:3px 7px;text-align:left;vertical-align:top}code{font-size:12px}nav a{margin-right:10px}"
             ".note{background:#f5f5f8;padding:10px 14px;font-size:13.5px}</style></head><body>",
             "<h1>TRACE-ECG paper 2: learned representations (ECG, CLMBR-T) vs hand-built PS covariates</h1>",
             f"<p class='note'>Draft figures (step F), generated {now} by <code>scripts/v21/make_paper2_figures.py</code>. Inputs are "
             "aggregate trial-level outputs in <code>/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/</code> (paths below are relative to it); "
             "no restricted, cell-level or review files are read, no patient counts are shown and no per-trial retention or ESS is "
             "plotted. Primary set: 32 analysed trials (S32); primary comparison PS-CVD5; primary balance endpoint: 54 non-coded "
             "held-out characteristics. CLMBR-T embeds the coded EHR (it is not an unstructured-data model). PNG 300 dpi and PDF "
             "versions, and one file per panel, are in <code>docs/paper/figures_paper2/{main,supplementary}/</code>.</p><nav>"]
    for sec, stem, title, *_ in FIGS:
        parts.append(f"<a href='#{stem}'>{html.escape(title.split('.')[0])}</a>")
    parts.append("</nav>")
    for sec, stem, title, legend, srcs in FIGS:
        png = (OUTM if sec == "main" else OUTS) / f"{stem}.png"
        b64 = base64.b64encode(png.read_bytes()).decode()
        parts.append(f"<h2 id='{stem}'>{html.escape(title)}</h2><img alt='{html.escape(title)}' src='data:image/png;base64,{b64}'>")
        parts.append(f"<p class='leg'>{html.escape(legend)}</p><table><tr><th>Panel</th><th>Source</th></tr>")
        for p, s in srcs:
            parts.append(f"<tr><td>{p}</td><td><code>{html.escape(s)}</code></td></tr>")
        parts.append(f"</table><p style='font-size:12px;color:#7a7c8c'>Files: <code>docs/paper/figures_paper2/{sec}/{stem}.png|.pdf</code>, "
                     f"panels in <code>{sec}/panels/{stem}_*.png|.pdf</code></p>")
    parts.append("<h2>All input files read</h2><ul>" + "".join(f"<li><code>{html.escape(rel(s))}</code></li>" for s in sorted(SOURCES)) + "</ul>")
    parts.append("</body></html>")
    out = OUT / "index.html"
    out.write_text("\n".join(parts))
    print("wrote", out.relative_to(ROOT), f"({out.stat().st_size / 1e6:.1f} MB)")
    old = os.umask(0o077)
    try:
        dst = AUD / "figures_paper2.html"
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(out.read_text())
        os.chmod(dst, 0o600)
    finally:
        os.umask(old)
    print("copied to", dst)


if __name__ == "__main__":
    os.umask(0o022)
    spot_checks()
    for f in (figure1, figure2, figure3, figure4, figure5, efigure1, efigure2, efigure3, efigure4, efigure5):
        f()
    write_html()
    (OUT / "check_values.json").write_text(json.dumps(CHECK, indent=1, default=str))
    print("check values -> docs/paper/figures_paper2/check_values.json")
