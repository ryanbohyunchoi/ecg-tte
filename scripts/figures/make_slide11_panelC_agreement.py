#!/usr/bin/env python
"""Lab deck slide 11 (Figure 3 slide), new panel C (docs/queue/slide11_figure3.md, 2026-10-14): agreement with the RCTs,
demographics + AI representations vs conventional PS. DECK ONLY: the paper's Figure 3 (scripts/figures/make_figure3_latent.py and
its PNG/PDF) is unchanged; its old panel C (agreement by emulation quality) moves to a deck appendix slide.

Basis: s31 (31 trials), version 1 cohorts, main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1); log HRs of the
existing cells (no refitting). Demo = rung P1 (age, sex, index year). Unmatched HR = claude-v18-embed-compare/results.csv, rung
"none" (as f4_numbers.py). PS-Clinical = no LVEF, 5-draw MI (Rubin-combined log HRs).
  bars    mean over trials of |emulated log HR - RCT log HR|, left to right: Unmatched (reference); PS-CVD5, hdPS, PS-Clinical
          (conventional); Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T (demographics + AI representations)
  labels  above each representation bar: the paired difference in mean |dlog HR| vs PS-CVD5 and vs hdPS (trials with both cells;
          all 31), two-sided exact sign-flip P across the 31 trials, unadjusted
The numbers code is that of audits/claude-fig4-standalone-20261014/f4_numbers.py / f4_hdps.py (agreement part; copied here, the
audit files are not modified); the style and helpers are those of make_figure2_latent.py / make_figure3_latent.py (imported, not
modified). Every value is gated against the audited figure4.md values (display precision), audits/claude-fig4-standalone-20261014/
recomputed_f4.json (the independent recomputation; 1e-9) and Figure 3 panel B (make_figure3_latent.compute: the PS-Demo + ECG /
+ CLMBR-T points and the PS-alone points of PS-CVD5, hdPS, PS-Clinical; 1e-9). The script also checks that no two text labels
overlap and that nothing is clipped.

Deck3 (docs/queue/QUEUE_2026_10_14_DECK3.md): display labels AI-ECG / AI-EHR; no grey group headings, footnote or dagger. Numbers
unchanged.

Outputs: docs/paper/figures_latent/panels/deck/slide11_panelC_agreement.{png,pdf} (300 dpi, 2215 x 830 px: the full width of
Figure 3, under panels A and B); aggregate values: audits/claude-slide11c-20261014/panelC_values.json. Aggregates only (no patient
counts, n_pairs, retention or ESS).

  python scripts/figures/make_slide11_panelC_agreement.py
"""
import json
import os
import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_figure3_latent as M3  # noqa: E402  (imports make_figure2_latent: rcParams, colours, letter())

F = M3.F2
BE = F.BE
ROOT = F.ROOT
A = F.A
OUT = ROOT / "docs/paper/figures_latent/panels/deck/slide11_panelC_agreement"
VALS = A / "claude-slide11c-20261014/panelC_values.json"
REF = A / "claude-fig4-standalone-20261014/recomputed_f4.json"
HDPS = "#3a8fb7"
CLMBR = F.ARMS["CLMBR"][1]  # the colour of "PS + CLMBR-T" in Figure 2
# (label, (rung, arm), colour, group, tick label); left to right
BARS = [("Unmatched", ("P5", "unmatched"), F.GREY, "ref", "Unmatched"),
        ("PS-CVD5", ("P5", "base"), F.NAVY, "conv", "PS-CVD5"), ("hdPS", ("hdPS200", "base"), HDPS, "conv", "hdPS"),
        ("PS-Clinical", ("clinical_nolvef", "base"), F.GOLD, "conv", "PS-Clinical"),
        ("Demo + ECG", ("P1", "ECG"), F.RED, "rep", "Demo\n+ AI-ECG"), ("Demo + CLMBR-T", ("P1", "CLMBR"), CLMBR, "rep", "Demo\n+ AI-EHR"),
        ("Demo + ECG + CLMBR-T", ("P1", "ECG+CLMBR"), F.PURPLE, "rep", "Demo + AI-ECG\n+ AI-EHR")]  # tick labels: display labels AI-ECG / AI-EHR
# (deck3 queue 2026-10-14); no dagger (its footnote is removed)
XP = np.array([0, 1, 2, 3, 4.6, 6.0, 7.4])  # bar positions (the mock-up's); dotted divider between the groups
DIV = 3.8
REFS = ("PS-CVD5", "hdPS")
# figure4.md / the queue file (audited): mean |dlog HR| (3 decimals); the paired differences (3 decimals, sign) and two-sided P
EXPECT_MEAN = {"Unmatched": "0.248", "PS-CVD5": "0.232", "hdPS": "0.182", "PS-Clinical": "0.171", "Demo + ECG": "0.207",
               "Demo + CLMBR-T": "0.174", "Demo + ECG + CLMBR-T": "0.164"}
EXPECT_VS = {("Demo + ECG", "PS-CVD5"): ("-0.026", ".20"), ("Demo + CLMBR-T", "PS-CVD5"): ("-0.058", ".055"),
             ("Demo + ECG + CLMBR-T", "PS-CVD5"): ("-0.068", ".037"), ("Demo + ECG", "hdPS"): ("+0.025", ".56"),
             ("Demo + CLMBR-T", "hdPS"): ("-0.008", ".71"), ("Demo + ECG + CLMBR-T", "hdPS"): ("-0.018", ".21")}
EXPECT_BPERM = ".26"  # benchmark-permutation P, Demo + ECG + CLMBR-T vs PS-CVD5, two-sided (figure4.md; footnote)
FOOT = ["Demo = age, sex, index year; ECG = 32 PCs of the pre-index ECG embedding; CLMBR-T = 64 PCs of a foundation-model embedding of the coded "
        "pre-index EHR. Labels: paired differences;",
        "two-sided sign-flip P across 31 trials, unadjusted. † PS-Clinical without LVEF (5-draw MI). The gains are not trial-specific "
        "(benchmark-permutation P = .26 for Demo + ECG + CLMBR-T vs PS-CVD5, two-sided)."]
W_PX, H_PX = 2215, 830  # Figure 3's full width; from just under panel B (bottom at 967 px) to the bottom of the figure (1823 px)
TOP = 0.36  # y-axis limit


def fp(p):
    """P as the queue file asks (the deck's static-slide format): <.001; 3 decimals below .1; else 2 decimals."""
    return "P < .001" if p < 0.001 else "P = " + (f"{p:.3f}"[1:] if p < 0.1 else f"{p:.2f}"[1:])


def fd(d, minus="−"):
    """signed difference, 3 decimals (typographic minus in the figure; ASCII for the checks)."""
    return f"{d:+.3f}".replace("-", minus)


# ---------------------------------------------------------------- data (f4_numbers.py, agreement part)
def load():
    grid, trials = F.load()
    T = BE.trial_set(trials, "s31")
    assert len(T) == 31 and not any(trials[i]["id"] == "protect-af" for i in T)
    ids = [trials[i]["id"] for i in T]
    R = pd.concat([pd.read_parquet(A / "claude-v21-paper2/core/restricted_cells.parquet"),
                   pd.read_parquet(A / "claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet")])
    R = R[R.config == "main"]
    V18 = pd.read_csv(A / "claude-v18-embed-compare/results.csv")
    V18 = V18[(V18.half == "full") & (V18.rung == "none")]
    return R, V18, ids


def absd(R, V18, ids, rg, arm):
    """per-trial |log HR - RCT log HR| (f4_numbers.ag; failed cells would be missing: there are none)."""
    if arm == "unmatched":
        g = V18.set_index("trial").loc[ids]
    else:
        g = R[(R.rung == rg) & (R.arm == arm)].set_index("trial").loc[ids]
        if "cell_failed" in g:
            g.loc[g.cell_failed.fillna(False).astype(bool), "loghr"] = np.nan
    return (g.loghr - g.rb).abs().to_numpy(float), g.rb.to_numpy(float)


def compute():
    R, V18, ids = load()
    d, rb0 = {}, None
    for lab, (rg, arm), *_ in BARS:
        d[lab], rb = absd(R, V18, ids, rg, arm)
        assert np.isfinite(d[lab]).all(), lab
        assert rb0 is None or np.allclose(rb, rb0, atol=1e-9)  # one benchmark per trial
        rb0 = rb
    V = dict(levels={lab: float(np.nanmean(x)) for lab, x in d.items()}, vs={}, k_set=len(ids))
    for lab, _, _, g, _ in BARS:
        if g != "rep":
            continue
        for b in REFS:  # f4_numbers.contrast, agreement part: g = b - a on trials with both; two-sided exact sign-flip
            ok = np.isfinite(d[lab]) & np.isfinite(d[b])
            gg = d[b][ok] - d[lab][ok]
            V["vs"][f"{lab} vs {b}"] = dict(absd_a=float(d[lab][ok].mean()), absd_b=float(d[b][ok].mean()), diff=float(-gg.mean()),
                                            closer=int((gg > 0).sum()), k_ag=int(ok.sum()),
                                            p_ag_two=float(min(1, 2 * min(BE.signflip_1s(gg), BE.signflip_1s(-gg)))))
    return V


def label(V, a, b):
    c = V["vs"][f"{a} vs {b}"]
    return f"vs {b}:\n{fd(c['diff'])} ({fp(c['p_ag_two'])})"


# ---------------------------------------------------------------- checks
def check(V):
    """figure4.md / the queue file (display precision), recomputed_f4.json (1e-9) and Figure 3 panel B (1e-9)."""
    bad = []
    for lab, e in EXPECT_MEAN.items():
        if f"{V['levels'][lab]:.3f}" != e:
            bad.append((lab, f"{V['levels'][lab]:.3f}", e))
    for (a, b), (de, pe) in EXPECT_VS.items():
        c = V["vs"][f"{a} vs {b}"]
        got = (fd(c["diff"], "-"), fp(c["p_ag_two"]).split("= ")[1])
        if got != (de, pe) or c["k_ag"] != 31:
            bad.append((a, b, got, (de, pe), c["k_ag"]))
    R = json.load(open(REF))
    dev = 0.0
    for lab in EXPECT_MEAN:
        dev = max(dev, abs(V["levels"][lab] - R["levels"][lab]["absd"]))
    for k, c in V["vs"].items():
        r = R["contrasts"][k]
        dev = max(dev, abs(c["absd_a"] - r["absd_a"]), abs(c["absd_b"] - r["absd_b"]), abs(c["p_ag_two"] - r["p_ag_two"]),
                  abs(-c["diff"] - r["gain"]))
        if (c["closer"], c["k_ag"]) != (r["closer"], r["k_ag"]):
            bad.append((k, "closer / k", (c["closer"], c["k_ag"]), (r["closer"], r["k_ag"])))
    bp = R["contrasts"]["Demo + ECG + CLMBR-T vs PS-CVD5"]["bshuf_p_two"]
    if f"{bp:.2f}"[1:] != EXPECT_BPERM:
        bad.append(("benchmark-permutation P (footnote)", bp, EXPECT_BPERM))
    if dev > 1e-9:
        bad.append(("recomputed_f4.json max deviation", dev))
    # Figure 3 panel B (the paper figure's code path: scripts/s31/s31_numbers.load)
    R3, TM = M3.load()
    B = M3.compute(R3, TM)["B"]
    pairs = {"Demo + ECG": ("P1", "ECG"), "Demo + CLMBR-T": ("P1", "CLMBR"), "Demo + ECG + CLMBR-T": ("P1", "ECG+CLMBR"),
             "PS-CVD5": ("P5", "base"), "hdPS": ("hdPS200", "base"), "PS-Clinical": ("clinical_nolvef", "base")}
    dev3 = max(abs(V["levels"][lab] - B[rg][a]) for lab, (rg, a) in pairs.items())
    if dev3 > 1e-9:
        bad.append(("Figure 3 panel B max deviation", dev3))
    if bad:
        raise SystemExit(f"panel C values differ from the expected values: {bad}")
    return dict(recomputed_f4_max_dev=dev, figure3_B_max_dev=dev3, bperm_two=bp,
                figure3_B={lab: round(B[rg][a], 6) for lab, (rg, a) in pairs.items()})


def no_overlap(fig, texts, pad_px=2):
    """no two labels overlap (boxes grown by pad_px), and everything lies inside the figure."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = [(n, t.get_window_extent(r)) for n, t in texts]
    W, H = fig.canvas.get_width_height()
    out = [n for n, b in bb if b.x0 < 0 or b.y0 < 0 or b.x1 > W or b.y1 > H]
    hits = [(n1, n2) for (n1, b1), (n2, b2) in combinations(bb, 2)
            if b1.x0 - pad_px < b2.x1 and b2.x0 - pad_px < b1.x1 and b1.y0 - pad_px < b2.y1 and b2.y0 - pad_px < b1.y1]
    assert not out and not hits, (out, hits)
    gaps = []  # vertical gap (px) between each bar's stacked labels
    by = {}
    for n, b in bb:
        if "|" in n:
            by.setdefault(n.split("|")[0], {})[n.split("|")[1]] = b
    for k, s in by.items():
        if "PS-CVD5" in s:
            gaps += [s["PS-CVD5"].y0 - s["hdPS"].y1, s["hdPS"].y0 - s["value"].y1]
    return dict(labels=len(bb), min_gap_px=round(float(min(gaps)), 1))


# ---------------------------------------------------------------- figure
def draw(V):
    fig = plt.figure(figsize=(W_PX / 300, H_PX / 300))
    ax = fig.add_axes([0.086, 0.15, 0.906, 0.74])  # deck3: no footnote, so the axes use its space
    v = [V["levels"][lab] for lab, *_ in BARS]
    ax.bar(XP, v, color=[c for _, _, c, _, _ in BARS], width=0.66, edgecolor="white", lw=0.8, zorder=2)
    texts = []
    for (lab, _, _, g, _), x, vi in zip(BARS, XP, v):
        t = ax.annotate(f"{vi:.3f}", (x, vi), xytext=(0, 1.6), textcoords="offset points", ha="center", va="bottom", fontsize=5.8, color=F.NAVY)
        texts.append((f"{lab}|value", t))
        if g == "rep":  # stacked above the value: vs hdPS, then vs PS-CVD5 on top (as the mock-up), with a gap between the two
            t1 = ax.annotate(label(V, lab, "hdPS"), (x, vi), xytext=(0, 10.6), textcoords="offset points", ha="center", va="bottom",
                             fontsize=5.0, color=F.NAVY, linespacing=1.2)
            t2 = ax.annotate(label(V, lab, "PS-CVD5"), (x, vi), xytext=(0, 26.4), textcoords="offset points", ha="center", va="bottom",
                             fontsize=5.0, color=F.NAVY, linespacing=1.2)
            texts += [(f"{lab}|hdPS", t1), (f"{lab}|PS-CVD5", t2)]
    ax.set_xticks(XP, [tl for *_, tl in BARS], fontsize=6.2)  # all navy, as the mock-up
    ax.tick_params(axis="x", length=0, pad=3)
    ax.axvline(DIV, color=F.LGREY, lw=0.6, ls=":")
    # deck3 (2026-10-14): no grey group headings (the dotted separator stays)
    ax.set_xlim(-0.6, 8.1)
    ax.set_ylim(0, TOP)
    ax.set_yticks(np.arange(0, 0.351, 0.05), [f"{y:.2f}" for y in np.arange(0, 0.351, 0.05)], fontsize=6.2)
    ax.set_ylabel("Mean |Δ log HR| vs RCT\nlower = closer", fontsize=6.6)
    texts.append(("title", ax.set_title("Agreement: demographics + AI representations vs conventional PS", fontsize=7, loc="left")))
    F.letter(ax, "C", x=-0.08, y=1.03)
    # deck3: no footnote (FOOT is no longer drawn)
    fig.canvas.draw()
    texts += [(f"xtick {i}", t) for i, t in enumerate(ax.get_xticklabels())] + [("ylabel", ax.yaxis.label)]
    lay = no_overlap(fig, texts)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT.with_suffix(".png"), dpi=300)  # fixed size (no tight bbox): exactly W_PX x H_PX
    fig.savefig(OUT.with_suffix(".pdf"))
    plt.close(fig)
    from PIL import Image
    assert Image.open(OUT.with_suffix(".png")).size == (W_PX, H_PX)
    print("wrote", OUT.relative_to(ROOT), "(.png, .pdf);", lay)
    return lay


def main():
    os.umask(0o077)
    V = compute()
    C = check(V)
    print(f"values match figure4.md / the queue file (display precision), recomputed_f4.json (max deviation {C['recomputed_f4_max_dev']:.1e}) "
          f"and Figure 3 panel B (max deviation {C['figure3_B_max_dev']:.1e})")
    lay = draw(V)
    out = dict(basis="version 1 cohorts; s31 (31 trials); main configuration (1:1 NN, caliper 0.2 SD of the PS logit, ridge C = 1); log HRs "
                     "of the existing cells; Demo = rung P1; unmatched = claude-v18-embed-compare rung none; PS-Clinical = no LVEF, 5-draw MI",
               metric="mean over trials of |emulated log HR - RCT log HR|; contrasts = paired difference (a - b), two-sided exact sign-flip P",
               levels=V["levels"], vs=V["vs"], labels={k: f"{fd(c['diff'])} ({fp(c['p_ag_two'])})" for k, c in V["vs"].items()},
               k_set=V["k_set"], footnote=" ".join(FOOT),
               check=dict(expected_mean=EXPECT_MEAN, expected_vs={f"{a} vs {b}": e for (a, b), e in EXPECT_VS.items()}, **C), layout=lay,
               png=str(OUT.with_suffix(".png").relative_to(ROOT)), size_px=[W_PX, H_PX])
    VALS.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(VALS, "w"), indent=1)
    print("wrote", VALS)
    for lab, *_ in BARS:
        print(f"  {lab:22s} {V['levels'][lab]:.4f}" + "".join(f"   vs {b}: {out['labels'][f'{lab} vs {b}']}" for b in REFS if f"{lab} vs {b}" in V["vs"]))


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        main()
