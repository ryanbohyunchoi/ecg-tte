#!/usr/bin/env python
"""Lab deck slide 9 (Figure 2 slide), new panel D (docs/queue/slide9_panelD.md, 2026-10-14): overall balance, demographics + AI
representations vs conventional PS. DECK ONLY: the paper's Figure 2 (scripts/figures/make_figure2_latent.py) is unchanged.

Basis: s31 (31 trials), version 1 cohorts, main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1), the 54 held-out
items with the leakage-corrected masks of pipeline.md section 6. Demo = rung P1 (age, sex, index year).
  bars    mean |SMD| over the 54 items (mean across trials of each trial's mean on its observed items; each arm's own masks):
          Unmatched (reference); PS-CVD5, hdPS, PS-Clinical (no LVEF, 5-draw MI; ~45 items, its inputs masked) (conventional);
          Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T (demographics + AI representations)
  labels  representation rows vs hdPS: relative change in mean |SMD| on items observed in both arms (paired by trial), two-sided
          exact sign-flip P across the 31 trials, unadjusted; "lower" / "higher" from the sign
The numbers code is that of audits/claude-fig4-standalone-20261014/f4_numbers.py / f4_hdps.py (copied here; the audit files are not
modified); the style and helpers are those of make_figure2_latent.py (imported, not modified). Every value is gated against the
audited figure4.md values (display precision) and audits/claude-fig4-standalone-20261014/recomputed_f4.json (the independent
recomputation; 1e-9).

Outputs: docs/paper/figures_latent/panels/deck/slide9_panelD_overall.{png,pdf} (300 dpi, 1283 px wide: the width of Figure 2's
panel D slot); aggregate values: audits/claude-slide9d-20261014/panelD_values.json. Aggregates only (no patient counts).

  python scripts/figures/make_slide9_panelD_overall.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_figure2_latent as F  # noqa: E402  (rcParams, colours, load(), ITEMS, letter())

BE = F.BE
ROOT = F.ROOT
OUT = ROOT / "docs/paper/figures_latent/panels/deck/slide9_panelD_overall"
VALS = F.A / "claude-slide9d-20261014/panelD_values.json"
REF = F.A / "claude-fig4-standalone-20261014/recomputed_f4.json"
HDPS = "#3a8fb7"
CLMBR = F.ARMS["CLMBR"][1]  # the colour of "PS + CLMBR-T" in Figure 2
# (label, (rung, arm), colour, group); top to bottom
ROWS = [("Unmatched", ("P5", "unmatched"), F.GREY, "ref"),
        ("PS-CVD5", ("P5", "base"), F.NAVY, "conv"), ("hdPS", ("hdPS200", "base"), HDPS, "conv"),
        ("PS-Clinical", ("clinical_nolvef", "base"), F.GOLD, "conv"),
        ("Demo + ECG", ("P1", "ECG"), F.RED, "rep"), ("Demo + CLMBR-T", ("P1", "CLMBR"), CLMBR, "rep"),
        ("Demo + ECG + CLMBR-T", ("P1", "ECG+CLMBR"), F.PURPLE, "rep")]
YL = {"PS-Clinical": "PS-Clinical†"}
YP = [0.0, 1.55, 2.45, 3.35, 4.95, 5.85, 6.75]  # bar positions (inverted axis); group captions above rows 1 and 4
DIV, CAP_CONV, CAP_REP = 4.05, 0.92, 4.32  # dotted divider; caption baselines
REFARM = "hdPS"
# figure4.md (audited): mean |SMD| (3 decimals) and the vs-hdPS contrasts (relative change %, 1 decimal; direction; P)
EXPECT_MEAN = {"Unmatched": "0.143", "PS-CVD5": "0.129", "hdPS": "0.114", "PS-Clinical": "0.118", "Demo + ECG": "0.126",
               "Demo + CLMBR-T": "0.112", "Demo + ECG + CLMBR-T": "0.106"}
EXPECT_VS = {"Demo + ECG": ("10.2", "higher", 0.03), "Demo + CLMBR-T": ("2.0", "lower", 0.53), "Demo + ECG + CLMBR-T": ("8.0", "lower", 0.012)}
FOOT = ["Demo = age, sex, index year; ECG = 32 PCs of the pre-index ECG embedding; CLMBR-T = 64 PCs of a foundation-model embedding of the",
        "coded pre-index EHR. Labels: paired differences vs hdPS over items observed in both arms; two-sided sign-flip P across 31 trials,",
        "unadjusted. † PS-Clinical on the ~45 items that are not its inputs."]
W_PX, H_PX = 1283, 800  # Figure 2's panel D slot: 1283 px wide; 835 px from its top to the bottom of the figure


def fp(p):
    """the deck's static-slide P format (build_lab_deck_v2.fp): <.001; 3 decimals below .1; else 2 decimals."""
    return "P < .001" if p < 0.001 else "P = " + (f"{p:.3f}"[1:] if p < 0.1 else f"{p:.2f}"[1:])


def blk(grid, T, rg, arm):
    return grid.block("main", rg, arm, True)[np.ix_(T, F.ITEMS)]


def level(grid, T, rg, arm):
    """mean over trials of each trial's mean |SMD| on its observed items (each arm's own masks; f4_numbers.py)."""
    return float(np.nanmean(blk(grid, T, rg, arm), 1).mean())


def contrast(grid, T, a, b):
    """a vs b on the items observed in both arms (the union of both masks), paired by trial (f4_numbers.contrast, balance part)."""
    Ma, Mb = blk(grid, T, *a), blk(grid, T, *b)
    m = np.isnan(Ma) | np.isnan(Mb)
    ma, mb = np.nanmean(np.where(m, np.nan, Ma), 1), np.nanmean(np.where(m, np.nan, Mb), 1)
    rr, lo, hi = BE.relred_ci(mb, ma)
    dm = mb - ma
    return dict(rr=float(rr), lo=float(lo), hi=float(hi), lower=int((dm > 0).sum()), k=len(dm), m_a=float(ma.mean()), m_b=float(mb.mean()),
                p_m_two=float(min(1, 2 * min(BE.signflip_1s(dm), BE.signflip_1s(-dm)))))


def vs_label(c):
    return f"{abs(c['rr']):.1f}% {'lower' if c['rr'] > 0 else 'higher'} than {REFARM} ({fp(c['p_m_two'])})"


def compute():
    grid, trials = F.load()
    T = BE.trial_set(trials, "s31")
    assert len(T) == 31 and not any(trials[i]["id"] == "protect-af" for i in T)
    arm = {lab: ra for lab, ra, _, _ in ROWS}
    V = dict(levels={lab: level(grid, T, *ra) for lab, ra, _, _ in ROWS},
             n_items={lab: float(np.isfinite(blk(grid, T, *ra)).sum(1).mean()) for lab, ra, _, _ in ROWS},
             vs={lab: contrast(grid, T, ra, arm[REFARM]) for lab, ra, _, g in ROWS if g == "rep"}, k_set=len(T))
    return V


def check(V):
    """the audited values (figure4.md, display precision) and the independent recomputation (recomputed_f4.json, 1e-9)."""
    bad = []
    for lab, e in EXPECT_MEAN.items():
        if f"{V['levels'][lab]:.3f}" != e:
            bad.append((lab, f"{V['levels'][lab]:.3f}", e))
    for lab, (pct, word, p) in EXPECT_VS.items():
        c = V["vs"][lab]
        got = (f"{abs(c['rr']):.1f}", "lower" if c["rr"] > 0 else "higher")
        # P: figure4.md shows 2 or 3 decimals; equal at the precision it shows
        nd = len(f"{p}".split(".")[1])
        if got != (pct, word) or round(c["p_m_two"], nd) != p:
            bad.append((lab, got, round(c["p_m_two"], nd), (pct, word, p)))
    R = json.load(open(REF))
    dev = 0.0
    for lab in EXPECT_MEAN:
        dev = max(dev, abs(V["levels"][lab] - R["levels"][lab]["level"]))
    for lab, c in V["vs"].items():
        r = R["contrasts"][f"{lab} vs {REFARM}"]
        for k in ("rr", "lo", "hi", "p_m_two"):
            dev = max(dev, abs(c[k] - r[k]))
        assert c["lower"] == r["lower"] and c["k"] == r["k"], lab
    if dev > 1e-9:
        bad.append(("recomputed_f4.json max deviation", dev))
    if bad:
        raise SystemExit(f"panel D values differ from the expected values: {bad}")
    return dev


def draw(V):
    fig = plt.figure(figsize=(W_PX / 300, H_PX / 300))
    ax = fig.add_axes([0.268, 0.265, 0.715, 0.615])
    vals = [V["levels"][lab] for lab, *_ in ROWS]
    ax.barh(YP, vals, color=[c for _, _, c, _ in ROWS], height=0.66, edgecolor="white", lw=0.6, zorder=2)
    xmax = 0.30
    hd = V["levels"][REFARM]
    for y, v in zip(YP, vals):
        x = v + xmax * 0.012
        if v < hd + 0.002 and x < hd + 0.0035:  # bar ends just short of / at the hdPS line: start the value right of the line
            x = hd + xmax * 0.012
        ax.text(x, y, f"{v:.3f}", va="center", ha="left", fontsize=5.8, color=F.NAVY, zorder=3,
                bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none"))  # readable over the hdPS line
    ax.axvline(V["levels"][REFARM], color=HDPS, ls="--", lw=0.7, zorder=1)
    for (lab, _, _, g), y in zip(ROWS, YP):
        if g == "rep":
            ax.text(xmax * 0.995, y, vs_label(V["vs"][lab]), ha="right", va="center", fontsize=5.6, color=F.NAVY, zorder=3)
    ax.axhline(DIV, color=F.GREY, lw=0.6, ls=":", zorder=1)
    for y, s in ((CAP_CONV, "Conventional PS"), (CAP_REP, "Demographics + AI representations")):
        ax.text(0.004, y, s, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=5.4, color=F.GREY, style="italic",
                bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none"), zorder=3)
    ax.set_yticks(YP, [YL.get(lab, lab) for lab, *_ in ROWS], fontsize=6.2)
    for t, (_, _, _, g) in zip(ax.get_yticklabels(), ROWS):
        t.set_color(F.GREY if g == "ref" else F.NAVY)
    ax.tick_params(axis="y", length=0, pad=3)
    ax.set_ylim(YP[-1] + 0.55, -0.55)
    ax.set_xlim(0, xmax)
    ax.set_xticks([0, 0.05, 0.10, 0.15], ["0", "0.05", "0.10", "0.15"], fontsize=6)
    ax.set_xlabel(f"Mean |SMD| over 54 held-out items (mean across {V['k_set']} trials)", fontsize=6.4, labelpad=2)
    ax.spines["left"].set_visible(False)
    ax.set_title("Overall balance: AI representations vs conventional PS", fontsize=7, loc="left", x=-0.315, y=1.02)
    F.letter(ax, "D", x=-0.362, y=1.03)
    fig.text(0.012, 0.012, "\n".join(FOOT), ha="left", va="bottom", fontsize=4.55, color=F.GREY, linespacing=1.3)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT.with_suffix(".png"), dpi=300)  # fixed size (no tight bbox): exactly W_PX x H_PX
    fig.savefig(OUT.with_suffix(".pdf"))
    plt.close(fig)
    from PIL import Image
    assert Image.open(OUT.with_suffix(".png")).size == (W_PX, H_PX)
    print("wrote", OUT.relative_to(ROOT), "(.png, .pdf)")


def main():
    os.umask(0o077)
    V = compute()
    dev = check(V)
    print(f"values match figure4.md (display precision) and recomputed_f4.json (max deviation {dev:.1e})")
    draw(V)
    out = dict(basis="version 1 cohorts; s31 (31 trials); main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1); 54 held-out "
                     "items, leakage-corrected masks (pipeline.md section 6); Demo = rung P1; contrasts on items observed in both arms",
               levels=V["levels"], n_items_mean=V["n_items"], vs_hdPS=V["vs"], labels={lab: vs_label(c) for lab, c in V["vs"].items()},
               k_set=V["k_set"], check=dict(expected_mean=EXPECT_MEAN, expected_vs=EXPECT_VS, recomputed_f4_max_dev=dev),
               png=str(OUT.with_suffix(".png").relative_to(ROOT)), size_px=[W_PX, H_PX])
    VALS.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(VALS, "w"), indent=1)
    print("wrote", VALS)
    for lab, *_ in ROWS:
        print(f"  {lab:22s} {V['levels'][lab]:.4f}" + (f"   {vs_label(V['vs'][lab])}" if lab in V["vs"] else ""))


if __name__ == "__main__":
    main()
