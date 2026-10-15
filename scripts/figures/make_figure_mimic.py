#!/usr/bin/env python
"""MIMIC-IV external validation figures, styled like Figures 2 and 3 (docs/mimic/MIMIC_EXTERNAL_VALIDATION.md).

  figure_mimic_balance    A love plot (26 held-out items), B by domain, C Yale vs MIMIC-IV relative reduction,
                          D per trial (change in % |SMD| < 0.1), as Figure 2
  figure_mimic_agreement  A emulated vs RCT estimate, B agreement by arm (with placebos), C PEPTIC negative control,
                          as Figure 3

Primary MIMIC configuration: 7 cardiovascular trials, PS-CVD5 analog, all analysed patients; AI-EHR (CLMBR-T) input =
history before the index admission time (index ED stay kept; user decision 2026-10-15). Utilisation (block D) is masked
whenever an AI-EHR arm is in a contrast (22 items), as in the doc. Every plotted summary is checked against
audits/claude-mimic-clmbr-20261014/summary_prior/summary.json. Inputs are per-trial aggregate cells (restricted, read
in place); the figures carry no counts.
Output: docs/paper/figures_latent/figure_mimic_{balance,agreement}.{png,pdf} + panels/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_figure2_latent as F  # noqa: E402  (style, colours, letter/save helpers)

from matplotlib.patches import Patch  # noqa: E402
plt, Line2D = F.plt, F.Line2D
NAVY, RED, GREEN, PURPLE, GREY, LGREY, CARD, OTHER = F.NAVY, F.RED, F.GREEN, F.PURPLE, F.GREY, F.LGREY, F.CARD, F.OTHER
ROOT = F.ROOT
OUT = ROOT / "docs/paper/figures_latent"
A = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014")
RES, SUMJ = A / "results_prior", A / "summary_prior" / "summary.json"
TRIALS = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2"]
NAME = dict(plato="PLATO", aristotle="ARISTOTLE", rocket_af="ROCKET AF", transform_hf="TRANSFORM-HF", comet="COMET",
            soap2="SOAP II", elite2="ELITE II")
CARDIAC = {"transform_hf", "comet", "elite2"}  # Figure 2D's cardiac-physiology group (HF / RAAS drug choice)
BLOCK = {"A": "Core labs, vitals", "B": "Other labs", "C": "Ventilation", "D": "Utilisation"}
VLAB = dict(creatinine="Creatinine", potassium="Potassium", sodium="Sodium", hemoglobin="Hemoglobin", sbp="Systolic BP",
            dbp="Diastolic BP", heart_rate="Heart rate", bmi="BMI", nt_probnp="NT-proBNP", troponin_t="Troponin T",
            lactate="Lactate", albumin="Albumin", bun="BUN", wbc="WBC", platelets="Platelets", inr="INR", ldl="LDL",
            hba1c="HbA1c", bilirubin="Total bilirubin", alt="ALT", bicarbonate="Bicarbonate", vent_at_t0="Ventilation at t0",
            prior_admissions_365d="Admissions, prior 365 d", ed_visits_365d="ED visits, prior 365 d",
            days_admit_to_index="Days admission to t0", icu_before_index="ICU before t0")
ARMS = F.ARMS


def load():
    V = pd.concat([pd.read_csv(RES / f"{t}_vars.csv") for t in TRIALS + ["peptic"]])
    R = pd.concat([pd.read_csv(RES / f"{t}_arms.csv") for t in TRIALS + ["peptic"]])
    V, R = V[(V.base == "cvd5") & (V["pop"] == "all")], R[(R.base == "cvd5") & (R["pop"] == "all")]
    return V, R, json.load(open(SUMJ))


def smd(V, arm, masked=False):
    """trial x item |SMD| (unmatched from the base rows)."""
    v = V[V.trial.isin(TRIALS) & (V.arm == ("base" if arm == "unmatched" else arm))]
    if masked:
        v = v[v.block != "D"]
    return v.pivot_table(index="trial", columns="var", values="abs_smd_unmatched" if arm == "unmatched" else "abs_smd").loc[TRIALS]


def check(a, b, what, tol=5e-4):
    assert abs(a - b) <= tol, f"{what}: figure {a} vs summary {b}"


# ------------------------------------------------------------------ balance figure (as Figure 2)
def fig_balance(V, R, S):
    C = S["contrasts"]
    fig = plt.figure(figsize=(7.2, 6.4))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.05, 0.95, 1.1], height_ratios=[1.0, 0.82], wspace=1.05, hspace=0.75)
    hs = [Line2D([], [], ls="none", marker=mk, ms=4.2 if mk != "D" else 3.6, mew=0.9, color=col, mfc=col if fc is None else fc, label=lab)
          for lab, col, mk, fc in ARMS.values()]
    fig.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.55, 0.995), ncol=5, frameon=False, fontsize=6.8, handletextpad=0.2, columnspacing=1.2)

    # A: love plot (median across 7 trials), unmatched / PS-CVD5 / + AI-ECG, 26 items by block
    ax = fig.add_subplot(gs[:, 0])
    items = [v for b in "ABCD" for v in V[(V.trial == "plato") & (V.arm == "base") & (V.block == b)]["var"]]
    blk = V.drop_duplicates("var").set_index("var").block
    y = -np.arange(len(items))
    for arm in ("unmatched", "base", "ECG"):
        med = smd(V, arm)[items].median()
        lab, col, mk, fc = ARMS[arm]
        if arm == "unmatched":
            ax.scatter(med, y, marker="x", s=12, color=col, lw=0.8, zorder=3)
        else:
            ax.scatter(med, y, marker=mk, s=14, color=col, facecolor=fc if fc else col, lw=0.9, zorder=4)
    ax.axvline(0.1, color=RED, lw=0.7, ls="--")
    prev = None
    for i, v in enumerate(items):
        if prev and blk[v] != prev:
            ax.axhline(y[i] + 0.5, color=LGREY, lw=0.6)
        prev = blk[v]
    for b in "ABCD":
        idx = [i for i, v in enumerate(items) if blk[v] == b]
        ax.text(1.02, (y[idx[0]] + y[idx[-1]]) / 2, BLOCK[b], transform=ax.get_yaxis_transform(), rotation=270, va="center",
                ha="left", fontsize=6, color=RED, fontweight="bold")
    ax.set_yticks(y, [VLAB[v] for v in items], fontsize=5.6)
    ax.set_ylim(y[-1] - 0.7, 0.7)
    ax.set_xlabel("|SMD| (median across 7 trials)", fontsize=7)
    ax.set_title("PS-CVD5 ± AI-ECG, 26 held-out items", fontsize=7.5, loc="left", x=-0.55)
    F.letter(ax, "A", x=-0.75)

    # B: by domain (mean across trials of each trial's domain mean)
    ax = fig.add_subplot(gs[0, 1])
    rows = [("All", None)] + [(BLOCK[b], b) for b in "ABCD"]
    for arm in ("unmatched", "base", "ECG"):
        M = smd(V, arm)
        vals = [M[[v for v in M.columns if b is None or blk[v] == b]].mean(1).mean() for _, b in rows]
        lab, col, mk, fc = ARMS[arm]
        yy = -np.arange(len(rows))
        if arm == "unmatched":
            ax.scatter(vals, yy, marker="x", s=14, color=col, lw=0.9, zorder=3)
        else:
            ax.scatter(vals, yy, marker=mk, s=18, color=col, facecolor=fc if fc else col, lw=1.0, zorder=4)
        if arm == "base":
            check(vals[0], C["primary7|cvd5|all|+ ECG vs PS-CVD5"]["m_b"], "B all, PS-CVD5")
        if arm == "ECG":
            check(vals[0], C["primary7|cvd5|all|+ ECG vs PS-CVD5"]["m_a"], "B all, + AI-ECG")
    n = {b: int((blk[smd(V, 'base').columns] == b).sum()) for b in "ABCD"}
    ax.set_yticks(-np.arange(len(rows)), [f"All 26" if b is None else f"{lab} ({n[b]})" for lab, b in rows], fontsize=6.6)
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.axvline(0.1, color=RED, lw=0.7, ls="--")
    ax.set_xlabel("Mean |SMD| (mean across 7 trials)", fontsize=7)
    ax.set_title("PS-CVD5 ± AI-ECG, by domain", fontsize=7.5, loc="left", x=-0.6)
    F.letter(ax, "B", x=-0.75)

    # C: Yale vs MIMIC-IV relative reduction in mean |SMD| vs PS-CVD5 (bars, as Figure 3C), 95% CI
    ax = fig.add_subplot(gs[0, 2])
    CON = [("+ ECG vs PS-CVD5", "+ AI-ECG", RED), ("+ CLMBR-T vs PS-CVD5", "+ AI-EHR", GREEN),
           ("+ ECG + CLMBR-T vs PS-CVD5", "+ both", PURPLE), ("+ ECG + CLMBR-T vs + CLMBR-T", "AI-ECG on\ntop of AI-EHR", RED)]
    w = 0.36
    for i, (lab, txt, col) in enumerate(CON):
        for dx, src, filled in ((-w / 2, S["yale_s31"][lab], True), (w / 2, C[f"primary7|cvd5|all|{lab}"], False)):
            ax.bar(i + dx, src["relred"], width=w * 0.92, color=col if filled else "white", edgecolor=col, lw=1.0)
            ax.plot([i + dx] * 2, [src["lo"], src["hi"]], color=NAVY, lw=0.7)
            ax.text(i + dx, max(src["hi"], 0) + 0.6, f"{src['relred']:.1f}", ha="center", va="bottom", fontsize=4.8, rotation=90)
    ax.axhline(0, color=NAVY, lw=0.6)
    ax.set_xticks(range(len(CON)), [c[1] for c in CON], fontsize=6.0, rotation=30, ha="right")
    ax.set_ylabel("Reduction in mean |SMD|\nvs PS-CVD5 (%)", fontsize=6.8)
    ax.set_ylim(-5, 37)
    ax.legend(handles=[Patch(facecolor=GREY, edgecolor=GREY, label="Yale (31 trials)"),
                       Patch(facecolor="white", edgecolor=GREY, label="MIMIC-IV (7 trials)")],
              loc="upper left", frameon=False, fontsize=5.8, handlelength=1.0)
    ax.set_title("Yale vs MIMIC-IV", fontsize=7.5, loc="left")
    F.letter(ax, "C", x=-0.42)

    # D: per trial, change in % |SMD| < 0.1 (26 items), + AI-ECG vs PS-CVD5, coloured as Figure 2D
    ax = fig.add_subplot(gs[1, 1:])
    P = R[R.trial.isin(TRIALS)].pivot_table(index="trial", columns="arm", values="pct_bal")
    d = (P["ECG"] - P["base"]).loc[TRIALS]
    c = C["primary7|cvd5|all|+ ECG vs PS-CVD5"]
    check(d.mean(), c["dpts"], "D mean points")
    assert f"{int((d > 0).sum())}/7" == c["better_pts"], "D trials improved"
    o = sorted(TRIALS, key=lambda t: (-d[t], NAME[t]))
    ax.bar(range(7), [d[t] for t in o], color=[CARD if t in CARDIAC else OTHER for t in o], width=0.7)
    ax.axhline(0, color=NAVY, lw=0.6)
    ax.set_xticks(range(7), [NAME[t] for t in o], rotation=40, ha="right", fontsize=6.2)
    for tl, t in zip(ax.get_xticklabels(), o):
        tl.set_color(CARD if t in CARDIAC else GREY)
        tl.set_fontweight("bold" if t in CARDIAC else "normal")
    ax.set_ylabel("Change in % of items\nwith |SMD| < 0.1", fontsize=6.8)

    def summ(ts):
        x = d[list(ts)]
        return f"{int((x > 0).sum())} of {len(x)} improved; mean {x.mean():+.1f} points".replace("-", "−")
    card, oth = [t for t in TRIALS if t in CARDIAC], [t for t in TRIALS if t not in CARDIAC]
    ax.legend(handles=[Patch(color=CARD, label=f"{F.D_LEG['cardiac']}: {summ(card)}"), Patch(color=OTHER, label=f"{F.D_LEG['other']}: {summ(oth)}")],
              loc="upper right", frameon=False, fontsize=6.2, handlelength=1.4)
    ax.text(0.99, 0.70, f"All 7 trials: {summ(TRIALS)}\nmean |SMD| lower in {c['lower']}; P = {c['p']:.3f}".replace("0.", ".").replace("-", "−"),
            transform=ax.transAxes, ha="right", va="top", fontsize=6.0)
    ax.set_ylim(-6, 32)
    ax.set_xlim(-0.6, 6.6)
    ax.set_title("PS-CVD5 + AI-ECG vs PS-CVD5, per trial", fontsize=7.5, loc="left")
    F.letter(ax, "D", x=-0.12)
    F.save(fig, OUT / "figure_mimic_balance")


# ------------------------------------------------------------------ agreement figure (as Figure 3)
def fig_agreement(R, S):
    C, AG = S["contrasts"], S["agreement"]["primary7|cvd5|all"]
    fig = plt.figure(figsize=(7.2, 5.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.9], width_ratios=[1.0, 1.05], hspace=0.6, wspace=0.42)
    T = R[R.trial.isin(TRIALS)].set_index(["trial", "arm"])

    # A: emulated vs RCT estimate, PS-CVD5 vs + AI-ECG (7 trials)
    ax = fig.add_subplot(gs[0, 0])
    rct = np.exp(T.xs("base", level="arm").loc[TRIALS, "rct_loghr"])
    b, e = np.exp(T.xs("base", level="arm").loc[TRIALS, "loghr"]), np.exp(T.xs("ECG", level="arm").loc[TRIALS, "loghr"])
    for t in TRIALS:
        ax.plot([rct[t]] * 2, [b[t], e[t]], color=LGREY, lw=1.0, zorder=1)
    ax.scatter(rct, b, s=22, facecolor="white", edgecolor=NAVY, lw=1.1, zorder=3, label="PS-CVD5")
    ax.scatter(rct, e, s=22, color=RED, zorder=4, label="PS-CVD5 + AI-ECG")
    OFF = dict(plato=(0.97, 1.0, "right"), aristotle=(0.97, 0.9, "right"), rocket_af=(0.97, 1.04, "right"),
               transform_hf=(0.97, 1.0, "right"), comet=(1.04, 1.02, "left"), soap2=(1.05, 0.97, "left"), elite2=(1.05, 1.09, "left"))
    for t in TRIALS:
        fx, fy, ha = OFF[t]
        ax.text(rct[t] * fx, np.sqrt(b[t] * e[t]) * fy, NAME[t], fontsize=5.2, color=GREY, ha=ha, va="center")
    lim = (0.4, 2.2)
    ax.plot(lim, lim, color=GREY, lw=0.9, ls="--")
    ax.set_xscale("log"); ax.set_yscale("log")
    tk = [0.5, 0.67, 1, 1.5, 2]
    ax.set_xticks(tk, [f"{x:g}" for x in tk]); ax.set_yticks(tk, [f"{x:g}" for x in tk]); ax.minorticks_off()
    ax.set_xlim(*lim); ax.set_ylim(0.37, lim[1])
    ax.set_xlabel("RCT estimate (HR; OR for SOAP II)", fontsize=7)
    ax.set_ylabel("Emulated hazard ratio", fontsize=7)
    c = C["primary7|cvd5|all|+ ECG vs PS-CVD5"]
    check(float(np.mean(np.abs(np.log(b) - np.log(rct)))), c["absd_b"], "A |dlogHR| base")
    check(float(np.mean(np.abs(np.log(e) - np.log(rct)))), c["absd_a"], "A |dlogHR| ECG")
    ax.text(0.04, 0.96, f"Mean |Δ log HR|: {c['absd_b']:.3f} → {c['absd_a']:.3f}\n{c['closer'].replace('/', ' of ')} trials closer",
            transform=ax.transAxes, va="top", fontsize=6.4)
    ax.legend(loc="lower right", frameon=False, fontsize=6.2, handletextpad=0.2)
    ax.set_title("PS-CVD5 vs PS-CVD5 + AI-ECG", fontsize=7.5, loc="left")
    F.letter(ax, "A", x=-0.2)

    # B: agreement by arm (mean |dlogHR|), with the placebos
    ax = fig.add_subplot(gs[0, 1])
    BA = [("base", "PS\nalone", "white", NAVY, None), ("ECG", "+ AI-ECG", RED, RED, "+ ECG vs PS-CVD5"),
          ("CLMBR", "+ AI-EHR", GREEN, GREEN, "+ CLMBR-T vs PS-CVD5"), ("ECG+CLMBR", "+ both", PURPLE, PURPLE, "+ ECG + CLMBR-T vs PS-CVD5"),
          ("permECG", "permuted\nAI-ECG", LGREY, GREY, None), ("permCLMBR", "permuted\nAI-EHR", LGREY, GREY, None)]
    for i, (arm, txt, fc, ec, lab) in enumerate(BA):
        val = float(np.mean(np.abs(T.xs(arm, level="arm").loc[TRIALS, "loghr"] - T.xs(arm, level="arm").loc[TRIALS, "rct_loghr"])))
        check(val, AG[arm]["mean_abs_dloghr"], f"B {arm}")
        ax.bar(i, val, width=0.72, color=fc, edgecolor=ec, lw=1.1)
        ax.text(i, val + 0.006, f"{val:.3f}", ha="center", va="bottom", fontsize=5.6)
        if lab:
            ax.text(i, 0.012, f"P = {C[f'primary7|cvd5|all|{lab}']['p_bshuf']:.2f}".replace("0.", "."), ha="center", fontsize=4.9,
                    color="white" if fc not in ("white", LGREY) else NAVY, rotation=90, va="bottom")
    ax.set_xticks(range(len(BA)), [x[1] for x in BA], fontsize=6.0)
    ax.set_ylabel("Mean |Δ log HR| vs RCT (7 trials)\nlower = closer to the RCT", fontsize=6.8)
    ax.set_ylim(0, 0.42)
    ax.text(0.99, 0.97, "P: benchmark permutation vs PS alone", transform=ax.transAxes, ha="right", va="top", fontsize=5.6, color=GREY)
    ax.set_title("Agreement by arm (PS-CVD5)", fontsize=7.5, loc="left")
    F.letter(ax, "B", x=-0.2)

    # C: PEPTIC negative control (forest)
    ax = fig.add_subplot(gs[1, :])
    PE = S["peptic"]["cvd5"]
    PA = [("base", "PS-CVD5", NAVY, "white"), ("ECG", "+ AI-ECG", RED, RED), ("CLMBR", "+ AI-EHR", GREEN, "white"),
          ("ECG+CLMBR", "+ AI-ECG + AI-EHR", PURPLE, PURPLE), ("permECG", "+ permuted AI-ECG", GREY, GREY), ("permCLMBR", "+ permuted AI-EHR", GREY, "white")]
    pe = R[R.trial == "peptic"].set_index("arm")
    for i, (arm, txt, col, fc) in enumerate(PA):
        g = PE[arm]
        check(float(np.exp(pe.loc[arm, "loghr"])), g["hr"], f"C PEPTIC {arm}", 5e-3)
        ax.plot([g["lo"], g["hi"]], [-i, -i], color=col, lw=1.3)
        mk = {"base": "o", "ECG": "o", "CLMBR": "s", "ECG+CLMBR": "D", "permECG": "o", "permCLMBR": "s"}[arm]
        ax.plot(g["hr"], -i, mk, ms=5 if mk != "D" else 4.4, color=col, mfc=fc, mew=1.1)
        ax.text(2.25, -i, f"{g['hr']:.2f} ({g['lo']:.2f}–{g['hi']:.2f})", va="center", fontsize=6.2)
    ax.axvline(1.05, color=NAVY, lw=0.8, ls="--")
    ax.text(1.06, 0.55, "RCT RR 1.05", fontsize=6.2, ha="left")
    ax.set_xscale("log")
    tk = [0.8, 1, 1.25, 1.6, 2]
    ax.set_xticks(tk, [f"{x:g}" for x in tk]); ax.minorticks_off(); ax.set_xlim(0.78, 2.2)
    ax.set_yticks([-i for i in range(len(PA))], [p[1] for p in PA], fontsize=6.6)
    ax.set_ylim(-len(PA) + 0.4, 1.0)
    ax.set_xlabel("Hazard ratio, death at 90 d (log scale)", fontsize=7)
    ax.set_title("Negative-control trial: PEPTIC (PPI vs H2RA in ventilated ICU patients)", fontsize=7.5, loc="left")
    F.letter(ax, "C", x=-0.12)
    F.save(fig, OUT / "figure_mimic_agreement")


def main():
    V, R, S = load()
    fig_balance(V, R, S)
    fig_agreement(R, S)


if __name__ == "__main__":
    main()
