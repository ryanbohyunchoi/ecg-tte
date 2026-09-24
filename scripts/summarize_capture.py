"""Capture map: what each PS arm captures, by confounder domain (aggregate markdown).

Metric per trial, domain and arm: mean excess |SMD| over chance (evaluator). Capture % =
1 - excess(arm) / excess(unmatched), computed only where the unmatched excess is >= MIN_EXCESS
(otherwise there was nothing to capture and the cell is blank). Medians across trials are
reported separately for the pre-specified physiology-driven trials and the controls.

Usage: python summarize_capture.py [all|op]   (population: all initiators / outpatient)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import TRIALS  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
POP = sys.argv[1] if len(sys.argv) > 1 else "all"
MIN_EXCESS = 0.02
TRIALS_ORDER = [("comet", "comet"), ("paradigm_hf", "paradigm"), ("paradigm_hf_switch", "paradigm-hf-switch"),
                ("paragon_hf", "paragon-hf"), ("transform_hf", "transform-hf"), ("elite_ii", "elite-ii"),
                ("life", "life"), ("dionysos", "dionysos"), ("plato", "plato"), ("aristotle", "aristotle"),
                ("rocket_af", "rocket-af"), ("rely", "rely"), ("allhat", "allhat")]
DOMAINS = [("meds", "Medications (orders)"), ("util", "Healthcare use"), ("poolB", "Rest of coded record (pool B)"),
           ("phys_obs", "Vitals + basic labs + EF (core 9, measured)"), ("LVFUNC", "Echo: LV function"),
           ("LVSTRUCT", "Echo: LV structure / wall thickness"), ("DIAST", "Echo: diastolic function, LA"),
           ("RVPULM", "Echo: RV / pulmonary pressure"), ("VALVE", "Echo: valves"), ("AORTA", "Echo: aortic root"),
           ("BNP", "NT-proBNP"), ("LAB", "Other labs (9)"), ("ACCESS", "Echo performed (yes/no)"),
           ("prog_full", "Prognostic risk score")]
ARMS = ["sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]
EXTRA = ["sparse+noise32 (placebo)", "sparse+CLMBR", "hdPS200+ECG+CLMBR", "hdPS100+ECG", "hdPS500+ECG",
         "dxall", "dxall+ECG", "claims", "claims+ECG", "clinical+ECG"]
SHORT = {"phys_obs": "core-9 physiology"}


def load(n):
    p = A / f"claude-cap-{POP}-{n}" / "summary_pooled.csv"
    return pd.read_csv(p, index_col=0) if p.exists() else None


def main():
    rows = []
    for key, n in TRIALS_ORDER:
        d = load(n)
        if d is None:
            continue
        role = TRIALS[key]["role"]
        for dom, _ in DOMAINS:
            col = f"excess_{dom}"
            if col not in d:
                continue
            u = d.loc["unmatched", col]
            for arm in ARMS + EXTRA:
                if arm not in d.index:
                    continue
                v = d.loc[arm, col]
                cap = (1 - v / u) if (u >= MIN_EXCESS and not np.isnan(v)) else np.nan
                rows.append(dict(trial=n, role=role, domain=dom, arm=arm, excess=v, unmatched=u, capture=cap,
                                 pairs=d.loc[arm, "pairs"]))
    R = pd.DataFrame(rows)
    ntr = R.groupby("role").trial.nunique().to_dict()
    print(f"# Capture map — population: {'all initiators' if POP == 'all' else 'outpatient initiators'}\n")
    print(f"Trials: physiology n = {ntr.get('physiology', 0)}, control n = {ntr.get('control', 0)}. Cells: median % of the "
          f"unmatched excess imbalance removed (trials with unmatched excess >= {MIN_EXCESS} only; count in brackets). "
          "100% = balanced to the level of a randomised sample; negative = worse than before matching.\n")
    for role in ("physiology", "control"):
        S = R[R.role == role]
        print(f"\n## {role.capitalize()} trials\n")
        print("| Domain | " + " | ".join(ARMS) + " |")
        print("|---|" + "---|" * len(ARMS))
        for dom, label in DOMAINS:
            cells = []
            for arm in ARMS:
                x = S[(S.domain == dom) & (S.arm == arm)].capture.dropna()
                cells.append(f"{x.median():.0%} ({len(x)})" if len(x) else "–")
            print(f"| {label} | " + " | ".join(cells) + " |")
        pr = S[S.domain == "meds"].groupby("arm").pairs.median()
        print("| *Median pairs retained* | " + " | ".join(f"{pr.get(a, np.nan):.0f}" for a in ARMS) + " |")

    print("\n## H1/H4: what the ECG adds, per domain (median change in excess |SMD|; negative = better)\n")
    print("| Domain | Sparse → +ECG (physiology) | Sparse → +ECG (controls) | hdPS200 → +ECG (physiology) | hdPS200 → +ECG (controls) | Placebo: sparse → +noise (all) |")
    print("|---|---|---|---|---|---|")
    P = R.pivot_table(index=["trial", "role", "domain"], columns="arm", values="excess").reset_index()
    for dom, label in DOMAINS:
        X = P[P.domain == dom]
        if X.empty:
            continue
        def med(sub, a, b):
            v = (sub[b] - sub[a]).dropna()
            return f"{v.median():+.3f} ({(v < 0).sum()}/{len(v)} better)" if len(v) else "–"
        ph, co = X[X.role == "physiology"], X[X.role == "control"]
        print(f"| {label} | {med(ph, 'sparse', 'sparse+ECG')} | {med(co, 'sparse', 'sparse+ECG')} | "
              f"{med(ph, 'hdPS200', 'hdPS200+ECG')} | {med(co, 'hdPS200', 'hdPS200+ECG')} | "
              f"{med(X, 'sparse', 'sparse+noise32 (placebo)')} |")

    print("\n## H3: share of the sparse → clinical-PS gap closed (median across trials; gap >= 0.02 only)\n")
    print("| Domain | by +ECG | by hdPS200 | by hdPS200 + ECG |")
    print("|---|---|---|---|")
    for dom, label in DOMAINS:
        X = P[P.domain == dom]
        if X.empty or "clinical (reference)" not in X:
            continue
        gap = X["sparse"] - X["clinical (reference)"]
        ok = gap >= 0.02
        if ok.sum() == 0:
            continue
        f = lambda arm: ((X.loc[ok, "sparse"] - X.loc[ok, arm]) / gap[ok]).median()
        print(f"| {label} (n = {ok.sum()}) | {f('sparse+ECG'):.0%} | {f('hdPS200'):.0%} | {f('hdPS200+ECG'):.0%} |")

    print("\n## Per-trial excess |SMD| (unmatched / sparse / +ECG / hdPS200 / hdPS200+ECG / clinical)\n")
    for dom in ("phys_obs", "LVFUNC", "LVSTRUCT", "DIAST", "RVPULM", "VALVE", "BNP", "meds", "poolB"):
        X = P[P.domain == dom]
        if X.empty:
            continue
        print(f"\n**{dict(DOMAINS).get(dom, dom)}**\n")
        print("| Trial | Role | Unmatched | Sparse | +ECG | hdPS200 | hdPS200+ECG | Clinical |")
        print("|---|---|---|---|---|---|---|---|")
        for _, x in X.iterrows():
            print(f"| {x.trial} | {x.role} | " + " | ".join(f"{x.get(a, np.nan):.3f}" for a in
                  ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]) + " |")
    R.to_csv(A / f"claude-capture-long-{POP}.csv", index=False)


if __name__ == "__main__":
    main()
