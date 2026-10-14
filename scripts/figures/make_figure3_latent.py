#!/usr/bin/env python
"""LATENT-RCT manuscript Figure 3 (agreement of emulated and RCT results), queue docs/queue/figure3.md (2026-10-14).

Basis: version 1 cohorts, the 31-trial primary set "s31" (paper 1's 32, v19 tiers, minus PROTECT AF: excluded at feasibility,
smaller arm < 350), main configuration (1:1 nearest neighbour on the PS logit, caliper 0.2, fixed C = 1). Log HRs are those of the
existing cells (no refitting), loaded as the s31 numbers (scripts/s31/s31_numbers.load: PS-Clinical (no LVEF) = the 5-draw MI
cells, Rubin-combined HRs); RCT log HRs are the cells' benchmarks. Same code path as the mock-ups
(audits/claude-fig3-20261014/mockup/f3_mock.py, f3_C_variants.py).

  A  emulated vs RCT HR (log-log), PS-CVD5 (open navy) and PS-CVD5 + ECG (red), a light line joining each trial's two estimates;
     inset: mean |dlog HR| PS-CVD5 -> + ECG and the number of trials closer to the RCT with + ECG
  B  agreement ladder: mean |dlog HR| vs RCT at PS-Demo, PS-CVD5, PS-CVD10, PS-Clinical (no LVEF, MI), hdPS; four arms (PS alone,
     + ECG, + CLMBR-T, + CLMBR-T + ECG), offset within each level and joined per arm, as Figure 2C. No P values, permutation bands or
     highlight.
  C  mean |dlog HR| vs RCT by emulation quality (v19 tiers from trials_meta: Excellent + Good, Moderate), PS-CVD5, the four arms.
CLMBR-T is shown as a comparison arm only (pipeline.md section 9, 2026-10-13); it is not part of any take-home claim.

Checks (the script stops if any fails): every value within 0.001 of the queue file's expected values (EXPECT); the ECG values equal
docs/s31/S31_RESULTS.md (section 2 ladder, section 4 tiers; 3 decimals) and the s31 summaries (audits/claude-s31-20261014/
s31_numbers.json, full precision); the trials-closer count equals the summary's.

Outputs: docs/paper/figures_latent/figure3_rct_agreement.{png,pdf} (300 dpi), panels/figure3_rct_agreement_{A,B,C}.{png,pdf};
aggregate values: audits/claude-fig3-20261014/figure3_values.json. Aggregates only (no patient counts, n_pairs, retention or ESS).

  python scripts/figures/make_figure3_latent.py
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
import matplotlib.ticker as mticker  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/s31"))
import make_figure2_latent as F2  # noqa: E402  (style: rcParams, colours, arm markers, panel export)
import s31_numbers as S  # noqa: E402

BE = S.BE
A = BE.A
OUT = ROOT / "docs/paper/figures_latent"
VALS = A / "claude-fig3-20261014/figure3_values.json"
S31J = A / "claude-s31-20261014/s31_numbers.json"
S31MD = ROOT / "docs/s31/S31_RESULTS.md"
SET = "s31"
NAVY, RED, GREY, LGREY, GREEN, PURPLE = F2.NAVY, F2.RED, F2.GREY, F2.LGREY, F2.GREEN, F2.PURPLE
RUNGS = [("P1", "PS-Demo"), ("P5", "PS-CVD5"), ("PS10", "PS-CVD10"), ("clinical_nolvef", "PS-Clinical\n(no LVEF, MI)"), ("hdPS200", "hdPS")]  # Figure 2C order
ARM4 = ["base", "ECG", "CLMBR", "ECG+CLMBR"]
LAB = {"base": "PS alone", "ECG": "+ AI-ECG", "CLMBR": "+ AI-EHR", "ECG+CLMBR": "+ AI-ECG + AI-EHR"}  # colours / markers: F2.ARMS; display
# labels AI-ECG (ECG embedding) / AI-EHR (CLMBR-T), deck3 queue 2026-10-14
TIERS = [("EG", "Excellent + Good", ("Excellent", "Good")), ("MO", "Moderate", ("Moderate",))]
# queue file figure3.md item 5 (PS alone / + ECG / + CLMBR-T / + CLMBR-T + ECG); stop if any value differs by more than 0.001
EXPECT = {"A": dict(base=0.232, ECG=0.198, closer=20, k=31),
          "B": {"P1": (0.255, 0.207, 0.174, 0.164), "P5": (0.232, 0.198, 0.169, 0.161), "PS10": (0.213, 0.173, 0.181, 0.157),
                "clinical_nolvef": (0.171, 0.151, 0.151, 0.152), "hdPS200": (0.182, 0.172, 0.184, 0.169)},
          "C": {"EG": (0.230, 0.176, 0.149, 0.152), "MO": (0.235, 0.217, 0.185, 0.168)}}
TOL = 0.001


# ---------------------------------------------------------------- data
def load():
    g = S.load()
    trials = BE.trials_meta(g)
    T = BE.trial_set(trials, SET)
    assert len(T) == 31 and not any(trials[i]["id"] == "protect-af" for i in T)
    assert [t["id"] for t in trials if t["s31"]] == [trials[i]["id"] for i in T]
    return g["R"], [trials[i] for i in T]


def est(R, ids, rg, a):
    """log HR and RCT log HR per trial (trial-set order), main configuration; failed cells (F1) would be missing (there are none)."""
    x = R[(R.config == "main") & (R.rung == rg) & (R.arm == a)].set_index("trial").loc[ids]
    l = x.loghr.to_numpy(float)
    assert not x.failed.any() and np.isfinite(l).all(), (rg, a)
    return l, x.rb.to_numpy(float)


def compute(R, TM):
    ids = [t["id"] for t in TM]
    tier = np.array([t["tier"] for t in TM])
    L, rb0 = {}, None
    for rg, _ in RUNGS:
        for a in ARM4:
            L[(rg, a)], rb = est(R, ids, rg, a)
            assert rb0 is None or np.array_equal(rb, rb0)  # one benchmark per trial in every cell
            rb0 = rb
    rb = rb0
    d = {k: np.abs(v - rb) for k, v in L.items()}
    V = {"k": len(ids)}
    V["A"] = dict(base=float(d[("P5", "base")].mean()), ECG=float(d[("P5", "ECG")].mean()),
                  closer=int((d[("P5", "ECG")] < d[("P5", "base")]).sum()), k=len(ids),
                  hr_rct=np.exp(rb), hr_base=np.exp(L[("P5", "base")]), hr_ecg=np.exp(L[("P5", "ECG")]))
    V["B"] = {rg: {a: float(d[(rg, a)].mean()) for a in ARM4} for rg, _ in RUNGS}
    V["C"] = {}
    for key, lab, tt in TIERS:
        m = np.isin(tier, tt)
        V["C"][key] = dict(label=lab, k=int(m.sum()), **{a: float(d[("P5", a)][m].mean()) for a in ARM4})
    assert V["C"]["EG"]["k"] + V["C"]["MO"]["k"] == len(ids)  # s31 has no Limited trials
    V["names"] = [t["name"] for t in TM]
    V["full"] = [t["full"] for t in TM]
    return V


# ---------------------------------------------------------------- checks
def check_expected(V):
    rows = [("A PS-CVD5", V["A"]["base"], EXPECT["A"]["base"]), ("A + ECG", V["A"]["ECG"], EXPECT["A"]["ECG"])]
    rows += [(f"B {rg} {a}", V["B"][rg][a], EXPECT["B"][rg][i]) for rg, _ in RUNGS for i, a in enumerate(ARM4)]
    rows += [(f"C {k} {a}", V["C"][k][a], EXPECT["C"][k][i]) for k, _, _ in TIERS for i, a in enumerate(ARM4)]
    bad = [r for r in rows if abs(r[1] - r[2]) > TOL]
    ints = (V["A"]["closer"], V["A"]["k"], V["C"]["EG"]["k"], V["C"]["MO"]["k"]) == (EXPECT["A"]["closer"], EXPECT["A"]["k"], 14, 17)
    if bad or not ints:
        raise SystemExit(f"Figure 3 values differ from the queue file's expected values by more than {TOL}: {bad}; counts ok: {ints}")
    disp = [r[0] for r in rows if f"{r[1]:.3f}" != f"{r[2]:.3f}"]  # within the tolerance but rounding differently (logged)
    return dict(n=len(rows), max_dev=max(abs(r[1] - r[2]) for r in rows), display_differs=disp)


def check_s31(V):
    """the ECG values against docs/s31/S31_RESULTS.md (3 decimals) and the s31 summaries (s31_numbers.json, full precision)."""
    md = S31MD.read_text()
    J = json.load(open(S31J))["S31"]
    n, dev = 0, 0.0
    lab = {"P1": "PS-Demo", "P5": "PS-CVD5", "PS10": "PS-CVD10", "clinical_nolvef": "PS-Clinical (no LVEF, MI)", "hdPS200": "hdPS"}
    for rg, _ in RUNGS:  # section 2: "| Level | 0.255 → 0.207; permutation P = .11 | ..."
        m = re.search(rf"^\| {re.escape(lab[rg])} \| (0\.\d{{3}}) → (0\.\d{{3}}); permutation", md, flags=re.M)
        assert m, rg
        assert (m.group(1), m.group(2)) == (f"{V['B'][rg]['base']:.3f}", f"{V['B'][rg]['ECG']:.3f}"), (rg, m.groups())
        x = J["ladder"][rg]
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):  # the summaries' |dlog HR| for every arm (contrast rows vs PS alone)
            dev = max(dev, abs(x[a]["absd_ref"] - V["B"][rg]["base"]), abs(x[a]["absd_arm"] - V["B"][rg][a]))
            n += 2
    # section 1 / the primary: 0.232 -> 0.198 (20/31 closer)
    p = J["primary"]
    assert p["absd_closer"] == f"{V['A']['closer']}/{V['A']['k']}", p["absd_closer"]
    assert re.search(rf"{V['A']['base']:.3f} → {V['A']['ECG']:.3f} \({V['A']['closer']}/{V['A']['k']} closer", md)
    dev = max(dev, abs(p["absd_ref"] - V["A"]["base"]), abs(p["absd_arm"] - V["A"]["ECG"]))
    n += 3
    # section 4: tiers ("| Excellent + Good (14 / 15) | PS-CVD5 | ... | 0.230 (0.216) |")
    tb = md[md.index("## 4. Agreement"):md.index("## 5.")]
    for key, lab_, _ in TIERS:
        blk = tb[tb.index(f"| {lab_} ("):]
        vals = re.findall(r"\| (0\.\d{3}) \(0\.\d{3}\) \|", blk)[:2]
        assert vals == [f"{V['C'][key]['base']:.3f}", f"{V['C'][key]['ECG']:.3f}"], (key, vals)
        x = J["agreement_by_tier"][lab_]
        assert x["trials"] == V["C"][key]["k"]
        dev = max(dev, abs(x["base"]["absd"] - V["C"][key]["base"]), abs(x["ECG"]["absd"] - V["C"][key]["ECG"]))
        n += 4
    assert dev < 1e-6, dev  # the summaries use the deck's log HRs (8 decimals)
    return dict(n_checked=n, max_dev_vs_s31_numbers=dev, md_3dp="all equal")


# ---------------------------------------------------------------- figure
def arm_handle(a, line=True, ms=4.2):
    _, col, mk, fc = F2.ARMS[a]
    return Line2D([], [], ls="-" if line else "none", lw=0.9, marker=mk, ms=ms if mk != "D" else ms - 0.6, mew=0.9, color=col, mfc=fc, label=LAB[a])


def hr_axis(ax, lo, hi, ticks):
    ax.set_xscale("log")
    ax.set_yscale("log")
    for a_ in (ax.xaxis, ax.yaxis):
        a_.set_major_locator(mticker.FixedLocator(ticks))
        a_.set_major_formatter(mticker.FixedFormatter([f"{t:g}" for t in ticks]))
        a_.set_minor_locator(mticker.NullLocator())


def panel_a(ax, V):
    x, y0, y1 = V["A"]["hr_rct"], V["A"]["hr_base"], V["A"]["hr_ecg"]
    for xi, a, b in zip(x, y0, y1):
        ax.plot([xi, xi], [a, b], color=LGREY, lw=0.8, zorder=1)
    ax.scatter(x, y0, s=15, facecolor="white", edgecolor=NAVY, lw=0.9, zorder=2, label="PS-CVD5")
    ax.scatter(x, y1, s=15, color=RED, edgecolor=RED, lw=0.9, zorder=3, label="PS-CVD5 + AI-ECG")
    xl, yl = (0.45, 2.1), (0.3, 2.6)
    assert xl[0] < x.min() and x.max() < xl[1] and yl[0] < min(y0.min(), y1.min()) and max(y0.max(), y1.max()) < yl[1]  # nothing clipped
    hr_axis(ax, *xl, [0.5, 0.67, 1, 1.5, 2])
    ax.plot([0.3, 2.6], [0.3, 2.6], ls="--", color=GREY, lw=0.8, zorder=0)
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.set_xlabel("RCT hazard ratio", fontsize=7)
    ax.set_ylabel("Emulated hazard ratio", fontsize=7)
    ax.text(0.03, 0.97, f"Mean |Δ log HR|: {V['A']['base']:.3f} → {V['A']['ECG']:.3f}\n{V['A']['closer']} of {V['A']['k']} trials closer",
            transform=ax.transAxes, va="top", ha="left", fontsize=6.5, linespacing=1.35)
    ax.legend(loc="lower right", frameon=False, fontsize=6.3, handletextpad=0.3, borderaxespad=0.2)
    ax.set_title("PS-CVD5 vs PS-CVD5 + AI-ECG", fontsize=7, loc="left")
    F2.letter(ax, "A", x=-0.2, y=1.04)


def panel_b(ax, V):
    xs = np.arange(len(RUNGS))
    offs = {"base": -0.24, "ECG": -0.08, "CLMBR": 0.08, "ECG+CLMBR": 0.24}
    for a, dx in offs.items():
        v = [V["B"][rg][a] for rg, _ in RUNGS]
        col = F2.ARMS[a][1]
        ax.plot(xs + dx, v, "-", color=col, lw=0.8, alpha=0.6, zorder=2)
        F2.scatter(ax, xs + dx, v, a, s=17 if a != "ECG+CLMBR" else 13, zorder=3)
    ax.set_xticks(xs, [l for _, l in RUNGS], rotation=30, ha="right", rotation_mode="anchor", fontsize=6.4)
    ax.set_xlim(-0.5, len(RUNGS) - 0.5)
    vals = [V["B"][rg][a] for rg, _ in RUNGS for a in ARM4]
    ax.set_ylim(0.12, 0.27)
    assert 0.12 < min(vals) and max(vals) < 0.27
    ax.set_ylabel(f"Mean |Δ log HR| vs RCT ({V['k']} trials)\nlower = closer to the RCT", fontsize=6.6)
    ax.set_title("Agreement ladder (fewer → more covariates)", fontsize=7, loc="left")
    ax.legend(handles=[arm_handle(a) for a in ARM4], loc="upper right", frameon=False, fontsize=5.9, ncol=2, handlelength=2.0,
              handletextpad=0.4, columnspacing=1.0, borderaxespad=0.1)
    F2.letter(ax, "B", x=-0.22, y=1.04)


def panel_c(ax, V):
    w = 0.19
    top = max(V["C"][k][a] for k, _, _ in TIERS for a in ARM4)
    ylim = (0, 0.27)
    assert top < ylim[1] * 0.93
    for j, (k, _, _) in enumerate(TIERS):
        for i, a in enumerate(ARM4):
            col = F2.ARMS[a][1]
            x, v = j + (i - 1.5) * w, V["C"][k][a]
            ax.bar(x, v, width=w * 0.9, color="white" if a == "base" else col, edgecolor=col, lw=1)
            ax.text(x, v + ylim[1] * 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=5.6)
    ax.set_xticks([0, 1], [f"{V['C'][k]['label']} ({V['C'][k]['k']})" for k, _, _ in TIERS], fontsize=7)
    ax.tick_params(axis="x", length=0, pad=4)
    ax.set_xlim(-0.55, 1.55)
    ax.set_ylim(*ylim)
    ax.set_ylabel("Mean |Δ log HR| vs RCT\nlower = closer", fontsize=6.6)
    ax.set_title("Agreement by emulation quality (PS-CVD5)", fontsize=7, loc="left")
    ax.legend(handles=[Patch(facecolor="white" if a == "base" else F2.ARMS[a][1], edgecolor=F2.ARMS[a][1], label=LAB[a]) for a in ARM4],
              loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=4, frameon=False, fontsize=6.2, handlelength=1.6, columnspacing=1.6)
    F2.letter(ax, "C", x=-0.2, y=1.04)


def figure3(V):
    fig = plt.figure(figsize=(7.4, 6.1))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.78], hspace=0.56, wspace=0.36, left=0.09, right=0.985, top=0.955, bottom=0.1)
    panel_a(fig.add_subplot(gs[0, 0]), V)
    panel_b(fig.add_subplot(gs[0, 1]), V)
    sub = gs[1, :].subgridspec(1, 3, width_ratios=[0.2, 1, 0.2])  # C centred under A and B
    panel_c(fig.add_subplot(sub[0, 1]), V)
    F2.save(fig, OUT / "figure3_rct_agreement")


def main():
    os.umask(0o077)
    R, TM = load()
    V = compute(R, TM)
    E = check_expected(V)
    print(f"expected values: {E['n']} checked, max deviation {E['max_dev']:.2e}; display rounding differs: {E['display_differs'] or 'none'}")
    C = check_s31(V)
    print(f"vs S31_RESULTS.md / s31_numbers.json: {C}")
    figure3(V)
    out = dict(
        basis="version 1 cohorts; the 31-trial primary set s31 (paper 1's 32, v19 tiers, minus PROTECT AF: excluded at feasibility); main "
              "configuration (1:1 nearest neighbour, caliper 0.2, C = 1); log HRs of the existing cells (PS-Clinical (no LVEF): 5-draw MI, Rubin)",
        metric="mean over trials of |emulated log HR - RCT log HR|",
        A=dict(mean_absd_PS_CVD5=round(V["A"]["base"], 6), mean_absd_PS_CVD5_ECG=round(V["A"]["ECG"], 6), trials_closer=V["A"]["closer"], trials=V["A"]["k"],
               inset=f"Mean |Δ log HR|: {V['A']['base']:.3f} → {V['A']['ECG']:.3f} / {V['A']['closer']} of {V['A']['k']} trials closer",
               per_trial_hr={f: dict(rct=round(float(r), 4), ps_cvd5=round(float(b), 4), ps_cvd5_ecg=round(float(e), 4))  # trial-level aggregates
                             for f, r, b, e in zip(V["full"], V["A"]["hr_rct"], V["A"]["hr_base"], V["A"]["hr_ecg"])}),
        B={rg: {a: round(V["B"][rg][a], 6) for a in ARM4} for rg, _ in RUNGS},
        B_labels={rg: l.replace("\n", " ") for rg, l in RUNGS},
        C={k: {**{a: round(V["C"][k][a], 6) for a in ARM4}, "label": V["C"][k]["label"], "trials": V["C"][k]["k"]} for k, _, _ in TIERS},
        arms=LAB, tiers="v19 (trials_meta)",
        check=dict(expected=dict(EXPECT, tol=TOL), vs_expected=E, vs_s31=C))
    VALS.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(VALS, "w"), indent=1, default=lambda o: list(o) if isinstance(o, tuple) else str(o))
    print("wrote", VALS)
    print("  A:", out["A"]["inset"])
    for rg, l in RUNGS:
        print(f"  B {l.replace(chr(10), ' '):28s}", " / ".join(f"{V['B'][rg][a]:.3f}" for a in ARM4))
    for k, _, _ in TIERS:
        print(f"  C {V['C'][k]['label']} ({V['C'][k]['k']}):", " / ".join(f"{V['C'][k][a]:.3f}" for a in ARM4))


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        main()
