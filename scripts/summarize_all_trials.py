"""Cross-trial aggregate tables (markdown) for report.md. Reads only aggregate outputs.

Usage: python summarize_all_trials.py > tables.md
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import TRIALS  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
ORDER = [("comet", "comet"), ("paradigm_hf", "paradigm"), ("paragon_hf", "paragon-hf"), ("transform_hf", "transform-hf"),
         ("elite_ii", "elite-ii"), ("life", "life"), ("dionysos", "dionysos"),
         ("plato", "plato"), ("triton", "triton"), ("aristotle", "aristotle"), ("rocket_af", "rocket-af"),
         ("rely", "rely"), ("allhat", "allhat")]
BASE = {"comet": "claude-comet-baseline-export-v2"}


def load(path):
    return pd.read_csv(path, index_col=0) if path.exists() else None


def pct(x):
    return f"{100 * x:.1f}%"


def rel(d, m, ref="clinical", col="B_frac_gt_0_1"):
    return f"{100 * (d.loc[m, col] / d.loc[ref, col] - 1):+.0f}%"


rows, lt, sp, notes = [], [], [], []
for key, n in ORDER:
    spec = TRIALS[key]
    full = load(A / f"claude-longtail-v2-{n}" / "summary_pooled.csv")
    sparse = load(A / f"claude-sparse-dx-{n}" / "summary_pooled.csv")
    failed = (A / f"claude-{n}-FAILED_FEASIBILITY").exists()
    meta = next(iter(sorted((A / f"claude-longtail-v2-{n}").glob("meta_imp1_seed0.json"))), None) if full is not None else None
    meta = json.load(open(meta)) if meta else {}
    prog = A / f"claude-{n}-progref-v1" / "scores-v3" / "metrics.json"
    prog = json.load(open(prog)) if prog.exists() else {}
    arms = [a for a, _ in spec["arms"]]
    status = "done" if full is not None else ("failed feasibility" if failed else "not run")
    rows.append(f"| {spec['name']} | {spec['role']} | {arms[0]} vs {arms[1]} | {spec['published_hr']} | "
                f"{meta.get('n_treated', '–')} / {meta.get('n_control', '–')} | "
                f"{full.loc['clinical', 'pairs']:.0f} |" if full is not None else
                f"| {spec['name']} | {spec['role']} | {arms[0]} vs {arms[1]} | {spec['published_hr']} | – | – |")
    rows[-1] += f" {prog.get('prog_full_test_auc', '–')} | {status} |"
    if full is not None:
        lt.append(dict(trial=spec["name"], role=spec["role"],
                       clinical=full.loc["clinical", "B_frac_gt_0_1"], chance=full.loc["clinical", "B_frac_chance"],
                       pairs=full.loc["clinical", "pairs"],
                       x_clin=full.loc["clinical", "B_frac_excess"], x_ecg=full.loc["clinical+ECG", "B_frac_excess"],
                       x_clmbr=full.loc["clinical+CLMBR", "B_frac_excess"], x_hd=full.loc["clinical+hdPS200", "B_frac_excess"],
                       x_stack=full.loc["clinical+hdPS200+ECG+CLMBR", "B_frac_excess"],
                       ecg=full.loc["clinical+ECG", "B_frac_gt_0_1"] / full.loc["clinical", "B_frac_gt_0_1"] - 1,
                       clmbr=full.loc["clinical+CLMBR", "B_frac_gt_0_1"] / full.loc["clinical", "B_frac_gt_0_1"] - 1,
                       hdps200=full.loc["clinical+hdPS200", "B_frac_gt_0_1"] / full.loc["clinical", "B_frac_gt_0_1"] - 1,
                       stacked=full.loc["clinical+hdPS200+ECG+CLMBR", "B_frac_gt_0_1"] / full.loc["clinical", "B_frac_gt_0_1"] - 1,
                       ret=full.loc["clinical+hdPS200+ECG+CLMBR", "pairs"] / full.loc["clinical", "pairs"] - 1,
                       prog_clin=full.loc["clinical", "smd_prog_full"], prog_clmbr=full.loc["clinical+CLMBR", "smd_prog_full"],
                       prog_hdps=full.loc["clinical+hdPS200", "smd_prog_full"]))
    if sparse is not None:
        u = sparse.loc["unmatched"]
        dx, de = sparse.loc["dx"], sparse.loc["dx+ECGpc"]
        sp.append(dict(trial=spec["name"], role=spec["role"], phys_unmatched=u.mean_phys_obs,
                       phys_dx=dx.mean_phys_obs, phys_dx_ecg=de.mean_phys_obs,
                       phys_gain=(de.mean_phys_obs - dx.mean_phys_obs) / dx.mean_phys_obs,
                       placebo_phys=sparse.loc[[i for i in sparse.index if "placebo" in i][0], "mean_phys_obs"],
                       lvef_dx=dx.get("smd_obs_lvef", np.nan), lvef_dx_ecg=de.get("smd_obs_lvef", np.nan),
                       lvef_clin=sparse.loc["clinical"].get("smd_obs_lvef", np.nan),
                       B_dx=dx.B_frac_gt_0_1, B_dx_ecg=de.B_frac_gt_0_1,
                       B_dx_hd_ecg=sparse.loc["dx+hdPS200+ECGpc", "B_frac_gt_0_1"],
                       phys_dx_hd_ecg=sparse.loc["dx+hdPS200+ECGpc", "mean_phys_obs"]))

print("## Trials\n")
print("| Trial | Role | Comparison | Published HR | ECG+CLMBR population (arm 1 / arm 2) | Pairs, clinical PS | Prognostic AUC | Status |")
print("|---|---|---|---|---|---|---|---|")
print("\n".join(rows))
if lt:
    d = pd.DataFrame(lt)
    print("\n## Long-tail balance: change in pool-B share with |SMD| > 0.1 vs the clinical PS\n")
    print("| Trial | Role | Clinical PS | + ECG | + CLMBR | + hdPS200 | + hdPS200 + ECG + CLMBR | Pairs lost (stack) | Prog SMD clin / +CLMBR / +hdPS200 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in d.itertuples():
        print(f"| {r.trial} | {r.role} | {pct(r.clinical)} | {r.ecg:+.0%} | {r.clmbr:+.0%} | {r.hdps200:+.0%} | {r.stacked:+.0%} | "
              f"{-r.ret:.0%} | {r.prog_clin:.3f} / {r.prog_clmbr:.3f} / {r.prog_hdps:.3f} |")
    print(f"\nMedian across trials: +ECG {d.ecg.median():+.0%}, +CLMBR {d.clmbr.median():+.0%}, "
          f"+hdPS200 {d.hdps200.median():+.0%}, stack {d.stacked.median():+.0%}. "
          f"hdPS200 better than CLMBR by > 5 points of relative change in {(d.hdps200 < d.clmbr - 0.05).sum()} of {len(d)} trials, "
          f"CLMBR better in {(d.clmbr < d.hdps200 - 0.05).sum()}.")
    print("\nSame, as excess over the chance floor (percentage points); trials with < 500 clinical-PS pairs are flagged.\n")
    print("| Trial | Pairs (clinical) | Chance floor | Clinical | + ECG | + CLMBR | + hdPS200 | + hdPS200 + ECG + CLMBR |")
    print("|---|---|---|---|---|---|---|---|")
    for r in d.itertuples():
        flag = " ⚠" if r.pairs < 500 else ""
        print(f"| {r.trial}{flag} | {r.pairs:.0f} | {pct(r.chance)} | {pct(r.x_clin)} | {pct(r.x_ecg)} | {pct(r.x_clmbr)} | "
              f"{pct(r.x_hd)} | {pct(r.x_stack)} |")
if sp:
    s = pd.DataFrame(sp)
    print("\n## Sparse PS (demographics + diagnoses) ± raw ECG PCs: measured physiology\n")
    print("| Trial | Role | Unmatched phys | dx | dx + noise (placebo) | dx + ECGpc | Change | Measured LVEF dx → dx+ECGpc (clinical PS) | Pool-B dx → dx+ECGpc | dx + hdPS200 + ECGpc: pool-B / phys |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in s.itertuples():
        print(f"| {r.trial} | {r.role} | {r.phys_unmatched:.3f} | {r.phys_dx:.3f} | {r.placebo_phys:.3f} | {r.phys_dx_ecg:.3f} | "
              f"{r.phys_gain:+.0%} | {r.lvef_dx:.2f} → {r.lvef_dx_ecg:.2f} ({r.lvef_clin:.2f}) | {pct(r.B_dx)} → {pct(r.B_dx_ecg)} | "
              f"{pct(r.B_dx_hd_ecg)} / {r.phys_dx_hd_ecg:.3f} |")
    if len(s) >= 4:
        rho = s[["phys_unmatched", "phys_gain"]].corr(method="spearman").iloc[0, 1]
        print(f"\nSpearman correlation, unmatched physiologic imbalance vs relative ECG gain (n = {len(s)} trials): {rho:.2f}. "
              f"Mean gain: physiology trials {s[s.role == 'physiology'].phys_gain.mean():+.0%}, "
              f"controls {s[s.role == 'control'].phys_gain.mean():+.0%}.")

if sp:
    print("\n## Measured-LVEF imbalance by PS (sparse-set runs; measured EF only)\n")
    print("| Trial | Role | Unmatched | Demo + dx | Demo + dx + ECGpc | Claims (dx + meds + visits) | Claims + ECGpc | Clinical (EF in PS) | Phys mean: claims → claims + ECGpc |")
    print("|---|---|---|---|---|---|---|---|---|")
    big = []
    for key, n in ORDER:
        s_ = load(A / f"claude-sparse-dx-{n}" / "summary_pooled.csv")
        if s_ is None or "smd_obs_lvef" not in s_:
            continue
        L = s_.smd_obs_lvef
        print(f"| {TRIALS[key]['name']} | {TRIALS[key]['role']} | {L['unmatched']:.2f} | {L['dx']:.2f} | {L['dx+ECGpc']:.2f} | "
              f"{L['claims']:.2f} | {L['claims+ECGpc']:.2f} | {L['clinical']:.2f} | "
              f"{s_.loc['claims', 'mean_phys_obs']:.3f} → {s_.loc['claims+ECGpc', 'mean_phys_obs']:.3f} |")
        if L["dx"] >= 0.1:
            big.append((L["dx+ECGpc"] - L["dx"]) / L["dx"])
    if big:
        print(f"\nTrials where the sparse (demo + dx) PS leaves measured-LVEF SMD >= 0.1: {len(big)}; "
              f"ECG PCs reduce it by a median of {-np.median(big):.0%} (range {-max(big):.0%} to {-min(big):.0%}).")

print("\n## Sensitivity: outpatient initiators only (index order not during an inpatient stay)\n")
print("| Trial | Role | Cohort n before ECG/CLMBR restriction (arm 1 / arm 2) | Measured LVEF: demo + dx → + ECGpc | Phys mean: demo + dx → + ECGpc | Pool-B: demo + dx → + ECGpc |")
print("|---|---|---|---|---|---|")
big = []
for key, n in ORDER:
    base = "comet" if n == "comet" else n
    s_ = load(A / f"claude-sparse-dx-outpt-{base}" / "summary_pooled.csv")
    if s_ is None:
        continue
    m = json.load(open(A / f"claude-{base}-baseline-outpt" / "summary.json"))["remaining_by_treated"]
    L = s_.smd_obs_lvef if "smd_obs_lvef" in s_ else None
    print(f"| {TRIALS[key]['name']} | {TRIALS[key]['role']} | {m.get('1')} / {m.get('0')} | "
          f"{L['dx']:.2f} → {L['dx+ECGpc']:.2f} | {s_.loc['dx', 'mean_phys_obs']:.3f} → {s_.loc['dx+ECGpc', 'mean_phys_obs']:.3f} | "
          f"{pct(s_.loc['dx', 'B_frac_gt_0_1'])} → {pct(s_.loc['dx+ECGpc', 'B_frac_gt_0_1'])} |")
    if L["dx"] >= 0.1:
        big.append((L["dx+ECGpc"] - L["dx"]) / L["dx"])
if big:
    print(f"\nOutpatient initiators, trials with demo + dx measured-LVEF SMD >= 0.1: {len(big)}; ECG PCs reduce it by a median of "
          f"{-np.median(big):.0%} (range {-max(big):.0%} to {-min(big):.0%}).")
