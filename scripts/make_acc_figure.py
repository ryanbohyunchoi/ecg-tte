#!/usr/bin/env python
"""ACC abstract figure + table from committed aggregate Yale outputs (18 trials; no patient-level data).
Figure: A love plot (median |SMD| after matching across trials, per balancing variable not used by the sparse PS),
B per-trial |log HR - RCT| sparse vs sparse+ECG, C agreement metrics per PS.
Table: per-trial HRs vs RCT for each PS + summary rows.
Outputs: docs/abstract/acc_figure.{png,pdf}, acc_table.{png,md}, acc_stats.json
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import TRIALS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
V14, OUT = ROOT / "docs" / "v14", ROOT / "docs" / "abstract"
ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]
LAB = {"unmatched": "Unmatched", "sparse": "Sparse PS", "sparse+ECG": "Sparse PS + ECG", "hdPS200": "hdPS", "hdPS200+ECG": "hdPS + ECG",
       "clinical (reference)": "Clinical PS"}
COL = {"unmatched": "#868e96", "sparse": "#74c0fc", "sparse+ECG": "#d9480f", "hdPS200": "#4263eb", "hdPS200+ECG": "#f08c00",
       "clinical (reference)": "#2b8a3e"}
MK = {"unmatched": "x", "sparse": "o", "sparse+ECG": "o", "hdPS200": "^", "hdPS200+ECG": "^", "clinical (reference)": "s"}
names = {**PRIMARY, **EXTRA}
trials = [n for n in names if (A / "claude-v13-bootstrap" / f"bs_{n}.csv").exists()]

VARS = [  # (column in summary_pooled, label, group)
    ("mean_meds", "Medications (mean over classes)", "Coded record"), ("mean_util", "Healthcare use (mean)", "Coded record"),
    ("B_mean", "Held-out dx/drug/procedure codes (mean)", "Coded record"), ("smd_prog_full", "Prognostic risk score", "Coded record"),
    ("smd_obs_lvef", "LVEF", "Vitals & core labs"), ("smd_obs_sbp", "Systolic BP", "Vitals & core labs"), ("smd_obs_dbp", "Diastolic BP", "Vitals & core labs"),
    ("smd_obs_heart_rate", "Heart rate", "Vitals & core labs"), ("smd_obs_bmi", "BMI", "Vitals & core labs"),
    ("smd_obs_creatinine", "Creatinine", "Vitals & core labs"), ("smd_obs_potassium", "Potassium", "Vitals & core labs"),
    ("smd_obs_sodium", "Sodium", "Vitals & core labs"), ("smd_obs_hemoglobin", "Hemoglobin", "Vitals & core labs"),
    ("pp_BNP__ntprobnp", "NT-proBNP", "Other labs"), ("pp_LAB__albumin", "Albumin", "Other labs"), ("pp_LAB__bun", "BUN", "Other labs"),
    ("pp_LAB__egfr", "eGFR", "Other labs"), ("pp_LAB__glucose", "Glucose", "Other labs"), ("pp_LAB__hba1c", "HbA1c", "Other labs"),
    ("pp_LAB__hs_troponin_t", "hs-Troponin T", "Other labs"), ("pp_LAB__ldl", "LDL", "Other labs"), ("pp_LAB__platelets", "Platelets", "Other labs"),
    ("pp_LAB__wbc", "WBC", "Other labs"),
    ("pp_LVSTRUCT__ivsd", "IVSd", "Echo: LV structure"), ("pp_LVSTRUCT__lvpwd", "LVPWd", "Echo: LV structure"),
    ("pp_LVSTRUCT__lvidd", "LVIDd", "Echo: LV structure"), ("pp_LVSTRUCT__lvedvi", "LVEDVi", "Echo: LV structure"),
    ("pp_LVSTRUCT__lvesvi", "LVESVi", "Echo: LV structure"), ("pp_LVSTRUCT__wall_thickness_grade", "Wall-thickness grade", "Echo: LV structure"),
    ("pp_LVSTRUCT__ivsd_gt15", "IVSd > 15 mm", "Echo: LV structure"),
    ("pp_LVFUNC__ef", "Echo EF", "Echo: LV function"), ("pp_LVFUNC__lvsvi", "LV stroke volume index", "Echo: LV function"),
    ("pp_LVFUNC__gls", "Global longitudinal strain", "Echo: LV function"), ("pp_LVFUNC__lv_sys_grade", "LV systolic grade", "Echo: LV function"),
    ("pp_DIAST__e_a", "E/A", "Echo: diastolic / LA"), ("pp_DIAST__e_eprime", "E/e'", "Echo: diastolic / LA"),
    ("pp_DIAST__eprime_med", "e' septal", "Echo: diastolic / LA"), ("pp_DIAST__eprime_lat", "e' lateral", "Echo: diastolic / LA"),
    ("pp_DIAST__lavi", "LA volume index", "Echo: diastolic / LA"), ("pp_DIAST__diastolic_grade", "Diastolic grade", "Echo: diastolic / LA"),
    ("pp_DIAST__la_size_grade", "LA size grade", "Echo: diastolic / LA"), ("pp_DIAST__lvdd", "LV diastolic dysfunction", "Echo: diastolic / LA"),
    ("pp_RVPULM__tapse", "TAPSE", "Echo: RV / pulmonary"), ("pp_RVPULM__rv_s", "RV S'", "Echo: RV / pulmonary"),
    ("pp_RVPULM__rvsp", "RVSP", "Echo: RV / pulmonary"), ("pp_RVPULM__rvidd", "RV diameter", "Echo: RV / pulmonary"),
    ("pp_RVPULM__rap", "RA pressure", "Echo: RV / pulmonary"), ("pp_RVPULM__rv_size_grade", "RV size grade", "Echo: RV / pulmonary"),
    ("pp_RVPULM__rv_sys_grade", "RV systolic grade", "Echo: RV / pulmonary"),
    ("pp_VALVE__av_vmax", "AV Vmax", "Echo: valves / aorta"), ("pp_VALVE__av_mean_grad", "AV mean gradient", "Echo: valves / aorta"),
    ("pp_VALVE__tv_peak_grad", "TR peak gradient", "Echo: valves / aorta"), ("pp_VALVE__as_grade", "AS grade", "Echo: valves / aorta"),
    ("pp_VALVE__ar_grade", "AR grade", "Echo: valves / aorta"), ("pp_VALVE__mr_grade", "MR grade", "Echo: valves / aorta"),
    ("pp_VALVE__tr_grade", "TR grade", "Echo: valves / aorta"), ("pp_VALVE__modsev_mr", "Mod/severe MR", "Echo: valves / aorta"),
    ("pp_AORTA__ao_root", "Aortic root", "Echo: valves / aorta"),
]


def love_data():
    rows = []
    for n in trials:
        s = pd.read_csv(A / f"claude-cap4-all-{n}" / "summary_pooled.csv", index_col=0)
        for c, lab, g in VARS:
            if c in s:
                for a in ARMS:
                    if a in s.index and not pd.isna(s.loc[a, c]):
                        rows.append(dict(trial=n, var=lab, group=g, arm=a, smd=abs(s.loc[a, c])))
    D = pd.DataFrame(rows)
    ntr = D.groupby(["group", "var"]).trial.nunique()
    return D.groupby(["group", "var", "arm"]).smd.median().unstack("arm"), ntr


def trial_estimates():
    rows = []
    for n in trials:
        d = pd.read_csv(A / "claude-v13-bootstrap" / f"bs_{n}.csv")
        d = d[d.rep == 0].set_index("arm")
        k = names[n][0]
        b, se = bench(k)
        nm = TRIALS[k]["name"].split(" (")[0].split(":")[0].replace(" switcher, sequential", "").replace(" amlodipine vs thiazide", "")
        r = dict(trial=n, key=k, name=nm, rct=np.exp(b), rct_lo=np.exp(b - 1.96 * se), rct_hi=np.exp(b + 1.96 * se), rb=b, rs=se)
        for a in ARMS:
            r[a] = d.loc[a, "loghr"]
            r[a + "_se"] = d.loc[a, "se"]
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 8.5, "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    L, ntr = love_data()
    groups = list(dict.fromkeys(g for _, _, g in VARS))
    order = [(g, lab) for c, lab, g in VARS if (g, lab) in L.index]
    fig = plt.figure(figsize=(13.5, 11.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.1, 1], wspace=0.42, hspace=0.35)
    axA = fig.add_subplot(gs[:, 0])
    y = np.arange(len(order))[::-1]
    ypos = dict(zip(order, y))
    for i, o in enumerate(order):
        if i % 2 == 0:
            axA.axhspan(ypos[o] - 0.5, ypos[o] + 0.5, color="#f4f5f7", zorder=0)
    for a in ARMS:
        axA.scatter([L.loc[o, a] for o in order], [ypos[o] for o in order], marker=MK[a], s=24, color=COL[a], label=LAB[a], zorder=3,
                    linewidths=1.2 if a == "unmatched" else 0.4, edgecolors=None if a == "unmatched" else "white")
    axA.axvline(0.1, color="#999", ls="--", lw=0.8)
    axA.set_yticks(y)
    axA.set_yticklabels([lab for _, lab in order], fontsize=7)
    for g in groups:
        ys = [ypos[o] for o in order if o[0] == g]
        if ys:
            short = {"Coded record": "Coded record", "Vitals & core labs": "Vitals / labs", "Other labs": "Other labs",
                     "Echo: LV structure": "LV struct.", "Echo: LV function": "LV func.", "Echo: diastolic / LA": "Diastolic / LA",
                     "Echo: RV / pulmonary": "RV / pulm.", "Echo: valves / aorta": "Valves / aorta"}[g]
            axA.annotate(short, xy=(1.0, (max(ys) + min(ys)) / 2), xycoords=("axes fraction", "data"), xytext=(5, 0), textcoords="offset points",
                         rotation=270, va="center", ha="left", fontsize=7.5, fontweight="bold", color="#444")
            axA.axhline(min(ys) - 0.5, color="#bbb", lw=0.6)
    axA.set_xlabel("|Standardized mean difference| after matching\n(median across the 18 trials)")
    axA.set_xlim(0, float(np.nanmax(L.values)) * 1.05)
    axA.set_ylim(-0.7, len(order) - 0.3)
    axA.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.45, -0.075), ncol=6, columnspacing=0.8, handletextpad=0.2)
    axA.set_title("A  Balance on characteristics not in the sparse PS (love plot)", loc="left", fontweight="bold")
    phys = [o for o in order if o[0] != "Coded record"]
    better = int(sum(L.loc[o, "sparse+ECG"] < L.loc[o, "sparse"] for o in phys))
    better_h = int(sum(L.loc[o, "hdPS200+ECG"] < L.loc[o, "hdPS200"] for o in phys))
    better_all = int(sum(L.loc[o, "sparse+ECG"] < L.loc[o, "sparse"] for o in order))
    below = {a: int(sum(L.loc[o, a] < 0.1 for o in order)) for a in ARMS}
    grp_mean = {g: {a: round(float(np.mean([L.loc[o, a] for o in order if o[0] == g])), 3) for a in ARMS} for g in groups}
    # B
    T = trial_estimates()
    axB = fig.add_subplot(gs[0, 1])
    d0, d1 = (T["sparse"] - T.rb).abs(), (T["sparse+ECG"] - T.rb).abs()
    closer = int((d1 < d0).sum())
    for a0, a1 in zip(d0, d1):
        axB.plot([0, 1], [a0, a1], color="#2b8a3e" if a1 < a0 else "#c92a2a", alpha=0.65, lw=1.3)
        axB.scatter([0, 1], [a0, a1], color=[COL["sparse"], COL["sparse+ECG"]], s=20, zorder=3)
    axB.plot([0, 1], [d0.mean(), d1.mean()], color="black", lw=2.6, zorder=4)
    axB.text(1.05, d1.mean(), f"mean {d1.mean():.2f}", va="center", fontsize=8)
    axB.text(-0.05, d0.mean(), f"mean {d0.mean():.2f}", va="center", ha="right", fontsize=8)
    top = T.loc[d0.idxmax()]
    axB.annotate(top["name"], xy=(0, d0.max()), xytext=(0.06, d0.max() + 0.02), fontsize=7.5, color="#555")
    axB.set_ylim(-0.02, d0.max() * 1.12)
    axB.set_xticks([0, 1])
    axB.set_xticklabels(["Sparse PS", "Sparse PS + ECG"])
    axB.set_xlim(-0.4, 1.4)
    axB.set_ylabel("|log HR (emulation) − log HR (RCT)|")
    axB.set_title("B  Distance from the RCT result, per trial", loc="left", fontweight="bold")
    axB.text(0.5, 0.62, f"Closer to the RCT with ECG\nin {closer} of {len(T)} trials (green)", transform=axB.transAxes, ha="center", va="top",
             fontsize=8.5, bbox=dict(facecolor="white", edgecolor="#ddd", boxstyle="round,pad=0.3"))
    # C
    axC = fig.add_subplot(gs[1, 1])
    pan = pd.read_csv(V14 / "panel_all.csv").set_index("arm")
    pl = {"sparse": "Sparse", "sparse+ECG": "Sparse + ECG", "hdPS200": "hdPS200", "hdPS200+ECG": "hdPS200 + ECG", "clinical (reference)": "Clinical PS"}
    arms = ["sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]
    sd = [100 * pan.loc[pl[a], "std_diff_agreement"] for a in arms]
    phi = [pan.loc[pl[a], "dispersion_phi"] for a in arms]
    x = np.arange(len(arms))
    axC.bar(x - 0.2, sd, 0.38, color=[COL[a] for a in arms], edgecolor="white")
    for xi, v in zip(x, sd):
        axC.text(xi - 0.2, v + 1.5, f"{v:.0f}%", ha="center", fontsize=8)
    axC.set_ylabel("Trials statistically consistent with RCT (%)")
    axC.set_ylim(0, 100)
    axC2 = axC.twinx()
    axC2.plot(x + 0.2, phi, "o", color="black", ms=7)
    for xi, v in zip(x, phi):
        axC2.text(xi + 0.2, v + 0.2, f"{v:.1f}", ha="center", fontsize=8)
    axC2.set_ylabel("Excess disagreement φ (●)")
    axC2.set_ylim(0, max(phi) * 1.35)
    axC2.spines["top"].set_visible(False)
    axC.set_xticks(x)
    axC.set_xticklabels([LAB[a] for a in arms], fontsize=7.5, rotation=15)
    axC.set_title("C  Agreement with 18 RCT hazard ratios", loc="left", fontweight="bold")
    axC.text(0.01, 0.98, "Bars: % of trials statistically consistent with the RCT.\nφ: disagreement beyond sampling error (1 = none).",
             transform=axC.transAxes, va="top", fontsize=7.5, color="#333")
    fig.suptitle("AI-ECG embeddings for confounding control in 18 emulated cardiovascular trials (Yale New Haven Health System)",
                 fontsize=11.5, fontweight="bold", y=0.995)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"acc_figure.{ext}", dpi=300, bbox_inches="tight")

    # table
    cols = ["sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]
    tt = T.sort_values("name").reset_index(drop=True)
    hdr = ["Trial", "RCT HR (95% CI)"] + [LAB[a] for a in cols]
    lines, bold = [], []
    for _, r in tt.iterrows():
        errs = {a: abs(r[a] - r.rb) for a in cols}
        best = min(errs, key=errs.get)
        cells = [r["name"], f"{r.rct:.2f} ({r.rct_lo:.2f}–{r.rct_hi:.2f})"]
        for a in cols:
            cells.append(f"{np.exp(r[a]):.2f} ({np.exp(r[a] - 1.96 * r[a + '_se']):.2f}–{np.exp(r[a] + 1.96 * r[a + '_se']):.2f})")
        lines.append(cells)
        bold.append(2 + cols.index(best))
    summ = [["Mean |Δlog HR| vs RCT", ""] + [f"{(T[a] - T.rb).abs().mean():.2f}" for a in cols],
            ["Consistent with RCT", ""] + [f"{100 * pan.loc[pl[a], 'std_diff_agreement']:.0f}%" for a in cols],
            ["Estimate agreement", ""] + [f"{100 * pan.loc[pl[a], 'estimate_agreement']:.0f}%" for a in cols],
            ["Excess disagreement φ", ""] + [f"{pan.loc[pl[a], 'dispersion_phi']:.1f}" for a in cols]]
    mdl = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for c, b in zip(lines, bold):
        mdl.append("| " + " | ".join(f"**{v}**" if j == b else v for j, v in enumerate(c)) + " |")
    mdl += ["| " + " | ".join(c) + " |" for c in summ]
    (OUT / "acc_table.md").write_text("Emulated vs RCT hazard ratios (95% CI), 18 Yale emulations. Bold = PS closest to the RCT for that trial.\n\n"
                                      + "\n".join(mdl) + "\n")
    fig2, ax = plt.subplots(figsize=(13, 0.3 * (len(lines) + len(summ) + 3)))
    ax.axis("off")
    tb = ax.table(cellText=lines + summ, colLabels=hdr, loc="center", cellLoc="center", colLoc="center")
    tb.auto_set_font_size(False)
    tb.set_fontsize(7.5)
    tb.scale(1, 1.3)
    for (i, j), c in tb.get_celld().items():
        if j == 0:
            c.set_width(0.2)
    for (i, j), c in tb.get_celld().items():
        c.set_edgecolor("#dee2e6")
        if i == 0:
            c.set_facecolor("#e9ecef")
            c.set_text_props(fontweight="bold")
        elif i > len(lines):
            c.set_facecolor("#f8f9fa")
            if j == 0:
                c.set_text_props(fontweight="bold")
        elif j == bold[i - 1]:
            c.set_text_props(fontweight="bold", color="#b02a00")
    ax.set_title("Emulated vs RCT hazard ratios, 18 Yale emulations (bold red = PS closest to the RCT)", fontsize=10, fontweight="bold")
    fig2.savefig(OUT / "acc_table.png", dpi=300, bbox_inches="tight")
    stats = dict(n_vars=len(order), n_phys_vars=len(phys), sparse_ecg_better_phys=better, hdps_ecg_better_phys=better_h, sparse_ecg_better_all=better_all,
                 vars_below_0_1=below, group_mean_smd=grp_mean, closer=closer, mean_abs_sparse=round(float(d0.mean()), 3),
                 mean_abs_ecg=round(float(d1.mean()), 3))
    json.dump(stats, open(OUT / "acc_stats.json", "w"), indent=2)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
