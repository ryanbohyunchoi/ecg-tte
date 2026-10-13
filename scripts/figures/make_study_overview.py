#!/usr/bin/env python3
"""LATENT-RCT study overview figure (slide and manuscript Figure 1).

Hand-built with matplotlib primitives (no raster icons), so the SVG and PDF are fully vector.
Only design-level counts (numbers of trials and of held-out items) appear; no patient data.

Sources for every number on the figure:
- 99 candidates -> 38 emulated -> 32 analysed; tiers 3/12/17/6: docs/paper/paper.md (Methods, Results),
  docs/paper/supplement.md eMethods 3, docs/v19/quality_tiers.json (counted by area, Limited excluded).
- Areas of the 32 (AF 12, diabetes 7, HF 5, other 4, hypertension 2, ACS/MI 2): docs/v19/quality_tiers.json.
- MIMIC-IV set (7 CV trials + PEPTIC negative control): docs/v21/MIMIC_PAPER2.md, eMethods 11.
- PS ladder, representations, matching, 54-item held-out panel, analyses: pipeline.md (2026-10-13 update).
- Planned validation cohorts (ACCORD, WHI, CHS waveforms on BDC): docs/v20/COHORT_ECG_AVAILABILITY.md.

Usage: python scripts/figures/make_study_overview.py  [--out DIR]
Writes latent_rct_overview.{svg,pdf,png} (PNG at 300 dpi) to docs/presentation/figures/.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Arc, Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle, Wedge  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
OUT_DEFAULT = REPO / "docs/presentation/figures"

# ---- palette (scripts/build_lab_deck.py CSS: --navy, --red, --muted, --faint, --line, --band; arm colours) ----
NAVY = "#0E103C"
RED = "#DC5A55"
DRED = "#a8322e"
PRED = "#fbe3e2"
MNAVY = "#5b5d86"
MUTED = "#55576f"
FAINT = "#8a8ca0"
LINE = "#dcdde5"
BAND = "#f3f3f7"
BLUE = "#2a78d6"   # CLMBR-T in the deck
PBLUE = "#e3eefb"
GOLD = "#d69a00"   # permuted-ECG placebo in the deck
PGOLD = "#fbf3dc"
WHITE = "#ffffff"

W, H = 1600, 900   # drawing units; 100 units = 1 inch (figure 16 x 9 in)

for f in Path("/usr/share/fonts/truetype/lato").glob("Lato-*.ttf"):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({
    "font.family": "Lato",
    "svg.fonttype": "path",
    "pdf.fonttype": 42,
    "axes.linewidth": 0,
})

ax = None  # set in main()


# ---------------------------------------------------------------- primitives
def box(x, y, w, h, fc=WHITE, ec=NAVY, lw=1.4, ls="-", r=10, z=1, alpha=1.0):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                       ls=ls, zorder=z, alpha=alpha, joinstyle="round")
    ax.add_patch(p)
    return p


def t(x, y, s, size=12, color=NAVY, weight="normal", ha="left", va="center", style="normal", z=10, **kw):
    return ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, style=style,
                   zorder=z, **kw)


def line(xs, ys, color=NAVY, lw=1.4, ls="-", z=5, **kw):
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=z, solid_capstyle="round", **kw)


def arrow(x1, y1, x2, y2, color=NAVY, lw=1.6, hw=7, hl=9, z=6):
    """Straight arrow with a filled triangular head at (x2, y2)."""
    d = np.array([x2 - x1, y2 - y1], float)
    n = np.hypot(*d)
    u = d / n
    v = np.array([-u[1], u[0]])
    base = np.array([x2, y2]) - u * hl
    line([x1, base[0]], [y1, base[1]], color=color, lw=lw, z=z)
    ax.add_patch(Polygon([(x2, y2), base + v * hw / 2, base - v * hw / 2], closed=True, fc=color, ec=color,
                         lw=0.5, zorder=z))


def pill(x, y, s, fc=NAVY, tc=WHITE, size=10.5, ec=None, ls="-", pad=7, h=20, weight="bold", check=False):
    """Pill-shaped tag; (x, y) is the right-centre if ha='right' style is wanted, here it is the left-centre."""
    tw = text_width(s, size, weight)
    extra = 14 if check else 0
    w = tw + 2 * pad + extra
    box(x, y - h / 2, w, h, fc=fc, ec=ec or fc, lw=1.1, ls=ls, r=h / 2, z=8)
    if check:
        tick(x + pad + 5, y, 9, tc, lw=1.8)
    t(x + pad + extra + tw / 2, y - 0.5, s, size=size, color=tc, weight=weight, ha="center", z=9)
    return w


def tick(cx, cy, s, color, lw=2.0, z=9):
    line([cx - s * 0.5, cx - s * 0.12, cx + s * 0.55], [cy, cy - s * 0.4, cy + s * 0.45], color=color, lw=lw, z=z)


_renderer = None


def text_width(s, size, weight="normal"):
    """Width of a string in drawing units."""
    global _renderer
    fig = ax.figure
    if _renderer is None:
        fig.canvas.draw()
        _renderer = fig.canvas.get_renderer()
    tt = ax.text(0, 0, s, fontsize=size, fontweight=weight)
    bb = tt.get_window_extent(renderer=_renderer)
    tt.remove()
    inv = ax.transData.inverted()
    (x0, _), (x1, _) = inv.transform([(bb.x0, 0), (bb.x1, 0)])
    return x1 - x0


# ---------------------------------------------------------------- icons
def ecg_trace(x, y, w, h, color=RED, lw=1.6, beats=2, z=6):
    tt = np.linspace(0, 1, 400)
    sig = np.zeros_like(tt)
    for b in range(beats):
        c = (b + 0.5) / beats
        sc = 1.0 / beats
        sig += 0.12 * np.exp(-((tt - (c - 0.18 * sc)) / (0.035 * sc)) ** 2)      # P
        sig -= 0.15 * np.exp(-((tt - (c - 0.035 * sc)) / (0.012 * sc)) ** 2)     # Q
        sig += 1.00 * np.exp(-((tt - c) / (0.016 * sc)) ** 2)                    # R
        sig -= 0.28 * np.exp(-((tt - (c + 0.035 * sc)) / (0.014 * sc)) ** 2)     # S
        sig += 0.25 * np.exp(-((tt - (c + 0.22 * sc)) / (0.06 * sc)) ** 2)       # T
    ax.plot(x + tt * w, y + h * 0.28 + sig * h * 0.62, color=color, lw=lw, zorder=z, solid_joinstyle="round")


def ecg_icon(x, y, w=64, h=46, z=6):
    box(x, y, w, h, fc=WHITE, ec=NAVY, lw=1.4, r=6, z=z - 1)
    for gx in np.linspace(x + w / 6, x + w - w / 6, 5):
        line([gx, gx], [y + 3, y + h - 3], color=PRED, lw=0.7, z=z - 0.5)
    for gy in np.linspace(y + h / 5, y + h - h / 5, 4):
        line([x + 3, x + w - 3], [gy, gy], color=PRED, lw=0.7, z=z - 0.5)
    ecg_trace(x + 4, y + 2, w - 8, h - 4, z=z)


def cylinder(cx, y, w=44, h=46, color=NAVY, z=6):
    eh = w * 0.32
    ax.add_patch(Rectangle((cx - w / 2, y + eh / 2), w, h - eh, fc=WHITE, ec="none", zorder=z))
    line([cx - w / 2, cx - w / 2], [y + eh / 2, y + h - eh / 2], color=color, z=z + 0.1)
    line([cx + w / 2, cx + w / 2], [y + eh / 2, y + h - eh / 2], color=color, z=z + 0.1)
    ax.add_patch(Arc((cx, y + eh / 2), w, eh, theta1=180, theta2=360, ec=color, lw=1.4, zorder=z + 0.1))
    for k in (1, 2):
        yy = y + eh / 2 + (h - eh) * k / 3
        ax.add_patch(Arc((cx, yy), w, eh, theta1=180, theta2=360, ec=color, lw=1.1, zorder=z + 0.1))
    ax.add_patch(Ellipse((cx, y + h - eh / 2), w, eh, fc=BAND, ec=color, lw=1.4, zorder=z + 0.2))


def echo_icon(cx, ytop, r=46, color=NAVY, z=6):
    """Ultrasound sector with a small heart outline."""
    ax.add_patch(Wedge((cx, ytop), r, 240, 300, fc=BAND, ec=color, lw=1.4, zorder=z))
    for rr in (r * 0.45, r * 0.72):
        ax.add_patch(Arc((cx, ytop), 2 * rr, 2 * rr, theta1=240, theta2=300, ec=FAINT, lw=0.8, zorder=z + 0.1))
    # heart (parametric), centred low in the sector
    s = np.linspace(0, 2 * np.pi, 200)
    hx = 16 * np.sin(s) ** 3
    hy = 13 * np.cos(s) - 5 * np.cos(2 * s) - 2 * np.cos(3 * s) - np.cos(4 * s)
    k = r * 0.019
    ax.fill(cx + hx * k, ytop - r * 0.62 + hy * k, fc=RED, ec=RED, lw=0.8, zorder=z + 0.2)


def document(x, y, w=36, h=46, color=NAVY, z=6, lines=4, fold=10, fc=WHITE, cross=False):
    pts = [(x, y), (x + w, y), (x + w, y + h - fold), (x + w - fold, y + h), (x, y + h)]
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=color, lw=1.4, zorder=z, joinstyle="round"))
    ax.add_patch(Polygon([(x + w - fold, y + h), (x + w - fold, y + h - fold), (x + w, y + h - fold)], closed=True,
                         fc=LINE, ec=color, lw=1.1, zorder=z + 0.1, joinstyle="round"))
    top = y + h - fold - 6 if not cross else y + h - fold - 16
    for i in range(lines):
        yy = top - i * (h - fold - 8) / max(lines, 1)
        if yy < y + 5:
            break
        line([x + 6, x + w - 7 - (6 if i == lines - 1 else 0)], [yy, yy], color=FAINT, lw=1.2, z=z + 0.2)
    if cross:
        cx, cy = x + w / 2 - 3, y + h - fold - 4
        line([cx, cx], [cy - 7, cy + 7], color=NAVY, lw=1.8, z=z + 0.3)
        line([cx - 5, cx + 5], [cy + 3, cy + 3], color=NAVY, lw=1.8, z=z + 0.3)


def hospital(x, y, w=40, h=38, z=6):
    ax.add_patch(Rectangle((x, y), w, h * 0.7, fc=WHITE, ec=NAVY, lw=1.4, zorder=z))
    ax.add_patch(Rectangle((x + w * 0.25, y + h * 0.7), w * 0.5, h * 0.3, fc=WHITE, ec=NAVY, lw=1.4, zorder=z))
    cx, cy = x + w / 2, y + h * 0.85
    line([cx, cx], [cy - 4.5, cy + 4.5], color=RED, lw=2.2, z=z + 0.2)
    line([cx - 4.5, cx + 4.5], [cy, cy], color=RED, lw=2.2, z=z + 0.2)
    for i in range(3):
        for j in range(2):
            ax.add_patch(Rectangle((x + 5 + i * (w - 10) / 3 + 1, y + 6 + j * 10), (w - 10) / 3 - 4, 6, fc=MNAVY,
                                   ec="none", zorder=z + 0.1))


def clipboard(x, y, w=34, h=44, color=NAVY, z=6):
    box(x, y, w, h, fc=WHITE, ec=color, lw=1.4, r=4, z=z)
    box(x + w * 0.3, y + h - 5, w * 0.4, 9, fc=color, ec=color, lw=1, r=2, z=z + 0.1)
    step = (h - 16) / 4
    for i in range(4):
        yy = y + h - 12 - i * step
        ax.add_patch(Circle((x + 7, yy), 1.8, fc=RED if i == 1 else color, ec="none", zorder=z + 0.2))
        line([x + 12, x + w - 6], [yy, yy], color=FAINT, lw=1.2, z=z + 0.2)


def nn_icon(x, y, w=60, h=48, color=NAVY, node=RED, z=6):
    layers = [3, 4, 4, 2]
    xs = np.linspace(x + 5, x + w - 5, len(layers))
    pts = []
    for lx, n in zip(xs, layers):
        ys = np.linspace(y + h / 2 - (n - 1) * h / 8, y + h / 2 + (n - 1) * h / 8, n)
        pts.append([(lx, yy) for yy in ys])
    for a, b in zip(pts[:-1], pts[1:]):
        for p in a:
            for q in b:
                line([p[0], q[0]], [p[1], q[1]], color=LINE, lw=0.8, z=z)
    for k, layer in enumerate(pts):
        for p in layer:
            ax.add_patch(Circle(p, 4.2, fc=WHITE if k in (0, len(pts) - 1) else node, ec=color, lw=1.1, zorder=z + 0.2))


def vector_icon(x, y, n=6, s=9, color=RED, z=6):
    shades = [0.95, 0.35, 0.7, 0.15, 0.55, 0.85, 0.3, 0.6]
    for i in range(n):
        a = shades[i % len(shades)]
        ax.add_patch(Rectangle((x, y + i * s), s, s, fc=color, alpha=0.25 + 0.75 * a, ec=WHITE, lw=0.8, zorder=z))
    ax.add_patch(Rectangle((x, y), s, n * s, fc="none", ec=NAVY, lw=1.1, zorder=z + 0.1))


def codes_icon(x, y, w=60, h=46, z=6):
    box(x, y, w, h, fc=WHITE, ec=NAVY, lw=1.4, r=6, z=z)
    rows = [[0.30, 0.22, 0.28], [0.22, 0.36], [0.26, 0.20, 0.24], [0.34, 0.26]]
    cols = [BLUE, MNAVY, LINE]
    for i, row in enumerate(rows):
        xx = x + 6
        yy = y + h - 10 - i * 9.5
        for j, frac in enumerate(row):
            ww = frac * (w - 12)
            box(xx, yy - 3, ww - 3, 6, fc=cols[(i + j) % 3], ec="none", lw=0, r=2, z=z + 0.1)
            xx += ww


def person(cx, y, s=1.0, color=NAVY, z=6):
    ax.add_patch(Circle((cx, y + 30 * s), 8.5 * s, fc=color, ec="none", zorder=z))
    ax.add_patch(Wedge((cx, y), 15 * s, 0, 180, fc=color, ec="none", zorder=z))


def lock_icon(cx, y, s=1.0, color=RED, z=7):
    ax.add_patch(Arc((cx, y + 20 * s), 20 * s, 24 * s, theta1=0, theta2=180, ec=color, lw=3.0, zorder=z))
    line([cx - 10 * s, cx - 10 * s], [y + 14 * s, y + 20 * s], color=color, lw=3.0, z=z)
    line([cx + 10 * s, cx + 10 * s], [y + 14 * s, y + 20 * s], color=color, lw=3.0, z=z)
    box(cx - 15 * s, y, 30 * s, 22 * s, fc=color, ec=color, lw=1, r=3, z=z + 0.1)
    ax.add_patch(Circle((cx, y + 12 * s), 3 * s, fc=WHITE, ec="none", zorder=z + 0.2))
    line([cx, cx], [y + 5 * s, y + 11 * s], color=WHITE, lw=2.0, z=z + 0.2)


def loveplot_icon(x, y, w=80, h=70, z=6):
    ax.add_patch(Rectangle((x, y), w, h, fc=WHITE, ec=LINE, lw=1, zorder=z - 0.2))
    x0 = x + 10
    line([x0, x0], [y + 4, y + h - 4], color=NAVY, lw=1.2, z=z)
    xt = x0 + (w - 16) * 0.33
    line([xt, xt], [y + 4, y + h - 4], color=FAINT, lw=1.1, ls=(0, (3, 2)), z=z)
    base = [0.95, 0.70, 0.85, 0.60, 0.78]
    adj = [0.20, 0.12, 0.28, 0.08, 0.16]
    for i, (b, a) in enumerate(zip(base, adj)):
        yy = y + h - 10 - i * (h - 18) / 4
        line([x0, x + w - 4], [yy, yy], color=BAND, lw=0.8, z=z - 0.1)
        ax.add_patch(Circle((x0 + (w - 16) * b, yy), 3.6, fc=WHITE, ec=NAVY, lw=1.2, zorder=z + 0.1))
        ax.add_patch(Circle((x0 + (w - 16) * a, yy), 3.6, fc=RED, ec=RED, lw=1.0, zorder=z + 0.2))


def scatter_icon(x, y, w=80, h=70, z=6):
    ax.add_patch(Rectangle((x, y), w, h, fc=WHITE, ec=LINE, lw=1, zorder=z - 0.2))
    line([x + 8, x + 8, x + w - 4], [y + h - 4, y + 8, y + 8], color=NAVY, lw=1.2, z=z)
    line([x + 8, x + w - 6], [y + 8, y + h - 6], color=FAINT, lw=1.1, ls=(0, (3, 2)), z=z)
    pts = [(0.15, 0.22), (0.28, 0.24), (0.36, 0.45), (0.52, 0.47), (0.6, 0.68), (0.72, 0.62), (0.84, 0.86), (0.45, 0.30)]
    for px, py in pts:
        ax.add_patch(Circle((x + 8 + px * (w - 14), y + 8 + py * (h - 14)), 3.4, fc=RED, ec=WHITE, lw=0.6,
                            zorder=z + 0.1))


def bias_icon(x, y, w=80, h=70, z=6):
    ax.add_patch(Rectangle((x, y), w, h, fc=WHITE, ec=LINE, lw=1, zorder=z - 0.2))
    line([x + 8, x + w - 6], [y + 10, y + 10], color=NAVY, lw=1.2, z=z)
    ax.add_patch(Rectangle((x + 14, y + 10), 18, h - 26, fc=MNAVY, ec="none", zorder=z))
    ax.add_patch(Rectangle((x + 46, y + 10), 18, (h - 26) * 0.45, fc=RED, ec="none", zorder=z))
    arrow(x + 40, y + h - 14, x + 56, y + 10 + (h - 26) * 0.45 + 6, color=NAVY, lw=1.2, hw=6, hl=7, z=z + 0.2)


def layers_icon(x, y, w=80, h=70, z=6):
    ax.add_patch(Rectangle((x, y), w, h, fc=WHITE, ec=LINE, lw=1, zorder=z - 0.2))
    for k, c in enumerate([LINE, FAINT, NAVY]):
        box(x + 12 + k * 8, y + 10 + k * 12, w - 40, h - 40, fc=WHITE if k < 2 else NAVY, ec=c, lw=1.3, r=4,
            z=z + k * 0.1)
    tick(x + 12 + 16 + (w - 40) / 2, y + 10 + 24 + (h - 40) / 2, 13, WHITE, lw=2.4, z=z + 0.5)


def shuffle_icon(x, y, w=40, h=30, color=GOLD, z=6):
    arrow(x, y + 4, x + w, y + h - 4, color=color, lw=2, hw=8, hl=9, z=z)
    arrow(x, y + h - 4, x + w, y + 4, color=color, lw=2, hw=8, hl=9, z=z)


def drop_icon(cx, y, s=1.0, color=RED, z=7):
    tt = np.linspace(0, 2 * np.pi, 120)
    xs = cx + 9 * s * np.sin(tt) * np.sin(tt / 2) ** 1.0
    ys = y + 12 * s - 12 * s * np.cos(tt) * 0.9
    ax.fill(xs, ys, fc=color, ec=color, lw=0.6, zorder=z)


# ---------------------------------------------------------------- layout helpers
PANEL_Y0, PANEL_Y1 = 74, 820


def panel(x, w, num, title):
    box(x, PANEL_Y0, w, PANEL_Y1 - PANEL_Y0, fc=WHITE, ec=NAVY, lw=1.6, r=14, z=0)
    ax.add_patch(Circle((x + 26, PANEL_Y1 - 28), 15, fc=NAVY, ec="none", zorder=3))
    t(x + 26, PANEL_Y1 - 28.5, str(num), size=15, color=WHITE, weight="bold", ha="center", z=4)
    t(x + 50, PANEL_Y1 - 28, title, size=16.5, weight="bold")
    line([x + 14, x + w - 14], [PANEL_Y1 - 54, PANEL_Y1 - 54], color=LINE, lw=1.2, z=2)


def label(x, y, s, color=RED):
    t(x, y, s, size=11, color=color, weight="bold")


def connector(x, y):
    ax.add_patch(Circle((x, y), 14, fc=NAVY, ec=WHITE, lw=2.5, zorder=20))
    ax.add_patch(Polygon([(x - 4, y + 7), (x + 7, y), (x - 4, y - 7)], closed=True, fc=WHITE, ec="none", zorder=21))


# ---------------------------------------------------------------- columns
COLS = {  # x, width
    "data": (14, 296),
    "trials": (328, 262),
    "rep": (608, 384),
    "match": (1010, 282),
    "eval": (1310, 276),
}


def col_data():
    x, w = COLS["data"]
    panel(x, w, 1, "Data")
    # development site
    label(x + 16, 744, "DEVELOPMENT SITE")
    cy0, ch = 500, 232
    box(x + 12, cy0, w - 24, ch, fc=BAND, ec=NAVY, lw=1.4, r=10, z=1)
    hospital(x + 22, cy0 + ch - 54, 40, 40)
    t(x + 72, cy0 + ch - 24, "Yale New Haven Health", size=13.5, weight="bold")
    t(x + 72, cy0 + ch - 44, "index dates 2011–2024", size=11.5, color=MUTED)
    cells = [("EHR (OMOP)", "db"), ("Raw 12-lead ECG", "ecg"), ("Echo reports", "echo"), ("Death records", "doc")]
    cw = (w - 24) / 2
    for k, (lab, kind) in enumerate(cells):
        i, j = k % 2, k // 2
        cx = x + 12 + cw * i + cw / 2
        yb = cy0 + 92 - j * 84  # icon bottom
        if kind == "db":
            cylinder(cx, yb + 20, 40, 44)
        elif kind == "ecg":
            ecg_icon(cx - 32, yb + 20, 64, 44)
        elif kind == "echo":
            echo_icon(cx, yb + 66, 50)
        else:
            document(cx - 17, yb + 20, 34, 44, cross=True, lines=3)
        t(cx, yb + 6, lab, size=12, ha="center", weight="semibold")

    # external validation
    label(x + 16, 470, "EXTERNAL VALIDATION")
    # MIMIC (done)
    y0 = 368
    box(x + 12, y0, w - 24, 86, fc=WHITE, ec=NAVY, lw=1.6, r=10, z=1)
    t(x + 26, y0 + 62, "MIMIC-IV + MIMIC-IV-ECG", size=13.5, weight="bold")
    t(x + 26, y0 + 40, "Beth Israel Deaconess, Boston", size=11.5, color=MUTED)
    pill(x + 26, y0 + 17, "DONE", fc=NAVY, tc=WHITE, size=10.5, check=True)
    t(x + 104, y0 + 17, "ECG only; 8 trials", size=11.5, color=MUTED)

    # planned: UK Biobank
    y0 = 270
    box(x + 12, y0, w - 24, 84, fc=WHITE, ec=FAINT, lw=1.6, ls=(0, (5, 3)), r=10, z=1)
    t(x + 26, y0 + 60, "UK Biobank", size=13.5, weight="bold", color=MUTED)
    t(x + 26, y0 + 38, "cohort with ECG and cardiac MRI", size=11.5, color=MUTED)
    pill(x + 26, y0 + 16, "PLANNED", fc=WHITE, tc=MUTED, ec=FAINT, ls=(0, (3, 2)), size=10.5)

    # planned: dbGaP / BDC
    y0 = 90
    box(x + 12, y0, w - 24, 166, fc=WHITE, ec=FAINT, lw=1.6, ls=(0, (5, 3)), r=10, z=1)
    t(x + 26, y0 + 142, "dbGaP / BioData Catalyst", size=13.5, weight="bold", color=MUTED)
    t(x + 26, y0 + 120, "NHLBI trial and cohort data", size=11.5, color=MUTED)
    xx = x + 26
    for s in ("ACCORD", "WHI", "CHS"):
        ww = pill(xx, y0 + 90, s, fc=BAND, tc=NAVY, ec=FAINT, size=11.5, h=24, pad=9)
        xx += ww + 8
    ecg_trace(x + 26, y0 + 44, 70, 26, color=FAINT, lw=1.4, beats=2)
    t(x + 104, y0 + 58, "raw ECG waveforms", size=11.5, color=MUTED)
    t(x + 104, y0 + 42, "on BDC", size=11.5, color=MUTED)
    pill(x + 26, y0 + 16, "PLANNED", fc=WHITE, tc=MUTED, ec=FAINT, ls=(0, (3, 2)), size=10.5)


def col_trials():
    x, w = COLS["trials"]
    panel(x, w, 2, "Target trials")
    cx = x + w / 2
    # funnel
    bars = [(99, "candidate RCTs", 236, MNAVY), (38, "emulated", 196, NAVY), (32, "analysed", 156, RED)]
    steps = ["feasibility", "emulation quality"]
    y = 718
    bh = 40
    for k, (n, lab, bw, col) in enumerate(bars):
        box(cx - bw / 2, y, bw, bh, fc=col, ec=col, lw=1, r=8, z=2)
        nw = text_width(str(n), 19, "bold")
        lw_ = text_width(lab, 12.5, "semibold")
        tot = nw + 7 + lw_
        t(cx - tot / 2, y + bh / 2, str(n), size=19, color=WHITE, weight="bold", z=4)
        t(cx - tot / 2 + nw + 7, y + bh / 2 - 1, lab, size=12.5, color=WHITE, weight="semibold", z=4)
        if k < 2:
            arrow(cx - 52, y - 2, cx - 52, y - 34, color=NAVY, lw=1.4, hw=7, hl=8)
            t(cx - 40, y - 18, steps[k], size=11.5, color=MUTED, style="italic")
            y -= bh + 36
    # quality tiers of the 38
    yq = 516
    t(x + 16, yq + 28, "Quality of the 38 (points-based)", size=11.5, weight="bold")
    tiers = [("Excellent", 3, NAVY), ("Good", 12, MNAVY), ("Moderate", 17, "#a6a8c2"), ("Limited", 6, PRED)]
    sx, sw = x + 16, w - 32
    cell = sw / 38
    xx = sx
    for name, n, col in tiers:
        for i in range(n):
            box(xx + 0.6, yq, cell - 1.2, 16, fc=col, ec=RED if name == "Limited" else col, lw=0.8, r=1.5, z=3)
            xx += cell
    # cross out Limited
    lx0 = sx + cell * 32
    line([lx0 + 1, sx + sw - 1], [yq + 1, yq + 15], color=DRED, lw=1.3, z=4)
    leg = [("Excellent 3", NAVY), ("Good 12", MNAVY), ("Moderate 17", "#a6a8c2"), ("Limited 6 (out)", PRED)]
    pos = [(sx, yq - 18), (sx + 118, yq - 18), (sx, yq - 38), (sx + 118, yq - 38)]
    for (s, col), (px, py) in zip(leg, pos):
        box(px, py - 5.5, 11, 11, fc=col, ec=RED if col == PRED else col, lw=0.8, r=2, z=3)
        t(px + 16, py, s, size=11.5, color=NAVY)

    # areas of the 32
    ya = 438
    t(x + 16, ya, "Analysed 32 by clinical area", size=11.5, weight="bold")
    areas = [("AF", 12, RED), ("Diabetes", 7, NAVY), ("Heart failure", 5, NAVY), ("Other", 4, NAVY),
             ("Hypertension", 2, NAVY), ("ACS / MI", 2, NAVY)]
    for k, (name, n, col) in enumerate(areas):
        yy = ya - 30 - k * 28
        t(x + 110, yy, name, size=12, ha="right")
        t(x + 134, yy, str(n), size=12.5, weight="bold", ha="right", color=col)
        for i in range(n):
            ax.add_patch(Circle((x + 146 + i * 9.3, yy), 3.8, fc=col, ec="none", zorder=4))

    # MIMIC set
    y0 = 90
    box(x + 12, y0, w - 24, 124, fc=BAND, ec=NAVY, lw=1.4, r=10, z=1)
    t(x + 26, y0 + 102, "MIMIC-IV set", size=13.5, weight="bold")
    for i in range(7):
        ax.add_patch(Circle((x + 32 + i * 10, y0 + 72), 3.8, fc=NAVY, ec="none", zorder=4))
    t(x + 32 + 6 * 10 + 12, y0 + 72, "7 CV trials", size=12, weight="semibold")
    ax.add_patch(Circle((x + 32, y0 + 46), 4.5, fc=WHITE, ec=GOLD, lw=2, zorder=4))
    t(x + 46, y0 + 46, "PEPTIC (negative control)", size=12)
    t(x + 26, y0 + 20, "in-hospital initiations", size=11, color=MUTED)


def col_rep():
    x, w = COLS["rep"]
    panel(x, w, 3, "Representations in the PS")
    # card 1: structured EHR
    y0, ch = 542, 222
    box(x + 12, y0, w - 24, ch, fc=WHITE, ec=NAVY, lw=1.6, r=10, z=1)
    clipboard(x + 26, y0 + ch - 54, 32, 42)
    t(x + 70, y0 + ch - 22, "Structured EHR covariates", size=14, weight="bold")
    t(x + 70, y0 + ch - 42, "PS ladder, increasingly rich", size=11.5, color=MUTED)
    rows = [("PS-Demo", "age, sex, index year"), ("PS-CVD5", "+ 5 CV diagnoses"), ("PS-CVD10", "+ 10 diagnoses"),
            ("hdPS", "+ 200 code features"), ("PS-Clinical", "+ vitals, labs, meds")]
    for k, (nm, desc) in enumerate(rows):
        yy = y0 + ch - 72 - k * 30
        prim = k == 1
        col = RED if prim else (MNAVY if k else "#a6a8c2")
        t(x + 110, yy, nm, size=12, weight="bold", ha="right", color=DRED if prim else NAVY)
        box(x + 118, yy - 8, 8 + k * 9, 16, fc=col, ec=col, lw=1, r=3, z=3)
        t(x + 168, yy, desc, size=11.5, color=NAVY if prim else MUTED, weight="semibold" if prim else "normal")
        if prim:
            pill(x + 168 + text_width(desc, 11.5, "semibold") + 8, yy, "PRIMARY", fc=RED, tc=WHITE, size=9.5, h=18,
                 pad=6)
    t(x + 168, y0 + ch - 72 - 4 * 30 - 17, "(no LVEF; no echo in any PS)", size=10.5, color=MUTED)

    # card 2: AI-ECG
    y0, ch = 380, 148
    box(x + 12, y0, w - 24, ch, fc=WHITE, ec=RED, lw=1.8, r=10, z=1)
    t(x + 26, y0 + ch - 20, "AI-ECG foundation model", size=14, weight="bold")
    yi = y0 + 46
    ecg_icon(x + 51, yi, 70, 48)
    arrow(x + 126, yi + 24, x + 150, yi + 24, color=NAVY)
    nn_icon(x + 156, yi, 74, 48, node=RED)
    arrow(x + 236, yi + 24, x + 260, yi + 24, color=NAVY)
    vector_icon(x + 268, yi - 2, n=6, s=8.5, color=RED)
    t(x + 290, yi + 34, "32 PCs", size=13, weight="bold", color=DRED)
    t(x + 290, yi + 14, "of 256-d", size=11, color=MUTED)
    t(x + 86, y0 + 22, "raw waveform", size=11.5, ha="center", color=MUTED)
    t(x + 193, y0 + 22, "BCL encoder", size=11.5, ha="center", color=MUTED)
    t(x + 310, y0 + 22, "embedding", size=11.5, ha="center", color=MUTED)

    # card 3: CLMBR-T
    y0, ch = 218, 148
    box(x + 12, y0, w - 24, ch, fc=WHITE, ec=BLUE, lw=1.8, r=10, z=1)
    t(x + 26, y0 + ch - 20, "EHR foundation model", size=14, weight="bold")
    yi = y0 + 46
    codes_icon(x + 51, yi, 70, 48)
    arrow(x + 126, yi + 24, x + 150, yi + 24, color=NAVY)
    nn_icon(x + 156, yi, 74, 48, node=BLUE)
    arrow(x + 236, yi + 24, x + 260, yi + 24, color=NAVY)
    vector_icon(x + 268, yi - 2, n=6, s=8.5, color=BLUE)
    t(x + 290, yi + 34, "64 PCs", size=13, weight="bold", color=BLUE)
    t(x + 290, yi + 14, "of 768-d", size=11, color=MUTED)
    t(x + 86, y0 + 22, "code history", size=11.5, ha="center", color=MUTED)
    t(x + 193, y0 + 22, "CLMBR-T", size=11.5, ha="center", color=MUTED)
    t(x + 310, y0 + 22, "embedding", size=11.5, ha="center", color=MUTED)

    # placebo
    y0, ch = 132, 72
    box(x + 12, y0, w - 24, ch, fc=PGOLD, ec=GOLD, lw=1.6, ls=(0, (5, 3)), r=10, z=1)
    shuffle_icon(x + 30, y0 + 21, 40, 30)
    t(x + 86, y0 + 48, "Placebo: permuted embedding", size=13.5, weight="bold")
    t(x + 86, y0 + 26, "shuffled between patients", size=11.5, color=MUTED)

    # combination rule
    t(x + w / 2, 106, "Each PS level: alone, + ECG, + CLMBR-T, + placebo", size=11.5, ha="center",
      weight="semibold")


def col_match():
    x, w = COLS["match"]
    panel(x, w, 4, "Emulation design")
    # new-user active comparator timeline
    t(x + 16, 744, "New-user, active-comparator", size=13.5, weight="bold")
    ya = 650
    xl, x0, xr = x + 22, x + 140, x + w - 18
    box(xl, ya - 7, x0 - xl, 14, fc=BAND, ec=LINE, lw=1, r=3, z=2)
    arrow(xl, ya, xr, ya, color=NAVY, lw=1.8, hw=9, hl=11, z=3)
    line([x0, x0], [ya - 16, ya + 16], color=RED, lw=3, z=4)
    # look-back contents (above the axis)
    ecg_icon(xl + 4, ya + 16, 44, 34)
    clipboard(xl + 54, ya + 16, 24, 34)
    # arms at time zero (above the axis)
    person(x0 + 40, ya + 18, s=0.62, color=NAVY)
    person(x0 + 74, ya + 18, s=0.62, color=RED)
    t(x0 + 57, ya + 62, "drug A vs B", size=11.5, ha="center", color=NAVY, weight="semibold")
    # labels (below the axis)
    t((xl + x0) / 2 - 10, ya - 26, "look-back", size=11.5, ha="center", color=MUTED)
    t((xl + x0) / 2 - 10, ya - 42, "≤365 d", size=11.5, ha="center", color=MUTED)
    t(x0 + 2, ya - 26, "time 0", size=12, ha="center", weight="bold", color=DRED)
    t((x0 + xr) / 2 + 24, ya - 26, "follow-up to", size=11.5, ha="center", color=MUTED)
    t((x0 + xr) / 2 + 24, ya - 42, "trial horizon", size=11.5, ha="center", color=MUTED)

    # matching
    y0 = 410
    box(x + 12, y0, w - 24, 148, fc=BAND, ec=NAVY, lw=1.4, r=10, z=1)
    t(x + 26, y0 + 124, "Propensity-score matching", size=13.5, weight="bold")
    for k in range(2):
        person(x + 52, y0 + 66 - k * 46 + 6, s=0.55, color=NAVY)
        person(x + 118, y0 + 66 - k * 46 + 6, s=0.55, color=RED)
        line([x + 64, x + 106], [y0 + 78 - k * 46, y0 + 78 - k * 46], color=FAINT, lw=1.4, ls=(0, (3, 2)), z=5)
    t(x + 146, y0 + 84, "1:1 nearest", size=12, weight="semibold")
    t(x + 146, y0 + 66, "neighbour", size=12, weight="semibold")
    t(x + 146, y0 + 42, "caliper 0.2 SD", size=11.5, color=MUTED)
    t(x + 146, y0 + 26, "of the PS logit", size=11.5, color=MUTED)

    # held-out characteristics
    y0, ch = 90, 300
    box(x + 12, y0, w - 24, ch, fc=PRED, ec=RED, lw=2.2, r=10, z=1)
    t(x + 24, y0 + ch - 24, "Held-out characteristics", size=14, weight="bold")
    lock_icon(x + 34, y0 + ch - 58, s=0.62)
    t(x + 50, y0 + ch - 48, "never in any PS", size=12.5, weight="bold", color=DRED)
    t(x + 26, y0 + ch - 100, "54", size=40, weight="bold", color=DRED)
    t(x + 90, y0 + ch - 88, "non-coded", size=13, weight="semibold")
    t(x + 90, y0 + ch - 108, "measurements", size=13, weight="semibold")
    # two chips
    cy = y0 + 104
    box(x + 24, cy, w - 48, 44, fc=WHITE, ec=RED, lw=1.2, r=8, z=2)
    drop_icon(x + 46, cy + 10, s=1.0)
    t(x + 66, cy + 22, "19", size=15, weight="bold", color=DRED)
    t(x + 92, cy + 22, "vitals and labs", size=12.5)
    cy = y0 + 52
    box(x + 24, cy, w - 48, 44, fc=WHITE, ec=RED, lw=1.2, r=8, z=2)
    echo_icon(x + 46, cy + 38, 32)
    t(x + 66, cy + 22, "35", size=15, weight="bold", color=DRED)
    t(x + 92, cy + 22, "echo measures", size=12.5)
    tick(x + 32, y0 + 24, 12, DRED, lw=2.4)
    t(x + 46, y0 + 24, "leakage-corrected masking", size=12, color=DRED, weight="semibold")


def col_eval():
    x, w = COLS["eval"]
    panel(x, w, 5, "Evaluation")
    cards = [
        ("Covariate balance", loveplot_icon, ["held-out |SMD|", "after matching;", "relative reduction"], True),
        ("Agreement with RCTs", scatter_icon, ["RCT-DUPLICATE", "metrics; benchmark-", "permutation test"], False),
        ("Plasmode simulation", bias_icon, ["withheld confounder", "(LVEF, NT-proBNP,", "BMI, eGFR): % bias", "removed"], False),
        ("Robustness", layers_icon, ["matching, weighting,", "trial sets, cohort", "specs, leave-one-out"], False),
    ]
    top, bot, gap = 750, 90, 10
    chh = (top - bot - gap * 3) / 4
    for k, (title, icon, body, primary) in enumerate(cards):
        y0 = top - (k + 1) * chh - k * gap
        box(x + 12, y0, w - 24, chh, fc=WHITE, ec=RED if primary else NAVY, lw=2.0 if primary else 1.4, r=10, z=1)
        t(x + 24, y0 + chh - 20, title, size=13.5, weight="bold")
        if primary:
            pill(x + w - 30 - text_width("PRIMARY", 10, "bold") - 14, y0 + chh, "PRIMARY", fc=RED, tc=WHITE,
                 size=10)
        icon(x + 22, y0 + 14, 78, chh - 52)
        for i, s in enumerate(body):
            t(x + 110, y0 + chh - 48 - i * 18, s, size=11.5, color=NAVY if i == 0 else MUTED)


def header_footer():
    t(18, 864, "LATENT-RCT", size=26, weight="black")
    t(18 + text_width("LATENT-RCT", 26, "black") + 18, 862,
      "AI foundation-model representations for confounding control in target trial emulation of cardiovascular RCTs",
      size=15, color=MUTED)
    # legend
    lx = W - 18 - 250
    box(lx, 852, 32, 20, fc=WHITE, ec=NAVY, lw=1.6, r=5, z=2)
    t(lx + 40, 862, "completed", size=11.5, color=NAVY)
    box(lx + 136, 852, 32, 20, fc=WHITE, ec=FAINT, lw=1.6, ls=(0, (4, 2.5)), r=5, z=2)
    t(lx + 176, 862, "planned", size=11.5, color=MUTED)
    foot = [
        "Counts are numbers of trials or held-out measurements; no patient-level data are shown.  ACS, acute coronary "
        "syndrome; AF, atrial fibrillation; BCL, biometric contrastive learning; BDC, BioData Catalyst;",
        "CV, cardiovascular; hdPS, high-dimensional PS; LVEF, left ventricular ejection fraction; MI, myocardial "
        "infarction; PC, principal component; PS, propensity score; SMD, standardized mean difference.",
    ]
    for i, s_ in enumerate(foot):
        t(18, 50 - i * 18, s_, size=10, color=MUTED)


def check_layout(fig):
    """Report text that overlaps other text or crosses its panel edge (drawing units)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    boxes = []
    for tt in ax.texts:
        if not tt.get_text().strip():
            continue
        bb = tt.get_window_extent(renderer=r)
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        boxes.append((tt.get_text(), x0, y0, x1, y1))
    problems = []
    for i, (a, ax0, ay0, ax1, ay1) in enumerate(boxes):
        for b, bx0, by0, bx1, by1 in boxes[i + 1:]:
            if min(ax1, bx1) - max(ax0, bx0) > 0.5 and min(ay1, by1) - max(ay0, by0) > 1.5:
                problems.append(f"overlap: {a!r} / {b!r}")
        cx = (ax0 + ax1) / 2
        for name, (px, pw) in COLS.items():
            if px <= cx <= px + pw and PANEL_Y0 <= (ay0 + ay1) / 2 <= PANEL_Y1:
                if ax0 < px + 6 or ax1 > px + pw - 6:
                    problems.append(f"edge ({name}): {a!r} [{ax0:.0f}, {ax1:.0f}] vs [{px}, {px + pw}]")
        if ax0 < 4 or ax1 > W - 4 or ay0 < 2 or ay1 > H - 2:
            problems.append(f"canvas: {a!r}")
    return problems


def build(out: Path):
    global ax, _renderer
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.axis("off")
    _renderer = None
    header_footer()
    col_data()
    col_trials()
    col_rep()
    col_match()
    col_eval()
    names = list(COLS)
    for a, b in zip(names[:-1], names[1:]):
        xa = COLS[a][0] + COLS[a][1]
        xb = COLS[b][0]
        connector((xa + xb) / 2, 470)
    for pr in check_layout(fig):
        print("LAYOUT", pr)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / "latent_rct_overview"
    fig.savefig(f"{stem}.svg")
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    a = ap.parse_args()
    stem = build(a.out)
    for ext in ("svg", "pdf", "png"):
        p = Path(f"{stem}.{ext}")
        print(p, f"{p.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
