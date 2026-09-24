"""v3 cross-trial tables (aggregate markdown): primary analysis population per trial,
expanded physiology panel, sparse vs hdPS deltas, dx-select vs dx-all.

Primary population: outpatient initiators, except trials whose RCT initiated treatment in
hospital (PLATO: ACS; TRANSFORM-HF: at HF discharge), where all initiators are primary.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import TRIALS  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
ORDER = [("comet", "comet"), ("paradigm_hf", "paradigm"), ("paragon_hf", "paragon-hf"), ("transform_hf", "transform-hf"),
         ("elite_ii", "elite-ii"), ("life", "life"), ("dionysos", "dionysos"), ("plato", "plato"),
         ("aristotle", "aristotle"), ("rocket_af", "rocket-af"), ("rely", "rely"), ("allhat", "allhat")]
INPATIENT_TRIALS = {"plato", "transform-hf"}


def load(kind, n, primary=True):
    all_ = (n in INPATIENT_TRIALS) == primary
    ver = "v3b" if kind == "sparse" else "v3"
    p = A / f"claude-{ver}-{kind}{'-all' if all_ else ''}-{n}" / "summary_pooled.csv"
    return pd.read_csv(p, index_col=0) if p.exists() else None


def f(x, d=3):
    return "–" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def g(d, m, c):
    return d.loc[m, c] if (d is not None and m in d.index and c in d.columns) else np.nan


def table_phys(primary=True):
    label = "PRIMARY" if primary else "SECONDARY (other population)"
    print(f"\n### Physiology balance, sparse and hdPS arms — {label}\n")
    print("Mean excess |SMD| over chance (measured values; chance = expected |SMD| under randomisation given measured n). Core-9 = EF, SBP, DBP, HR, BMI, creatinine, K, Na, Hb; labs-10 = NT-proBNP, "
          "hs-TnT, eGFR, albumin, BUN, glucose, HbA1c, WBC, platelets, LDL.\n")
    arms = ["dx", "dx+ECGpc", "dx+hdPS200", "dx+hdPS200+ECGpc", "claims+hdPS200", "claims+hdPS200+ECGpc", "clinical", "clinical+hdPS200"]
    print("| Trial | Population | Pairs (dx) | " + " | ".join(arms) + " |")
    print("|---|---|---|" + "---|" * len(arms))
    rows = []
    for key, n in ORDER:
        d = load("sparse", n, primary)
        if d is None:
            continue
        pop = "all initiators" if (n in INPATIENT_TRIALS) == primary else "outpatient"
        cells = []
        for m in arms:
            core, labs = g(d, m, "excess_phys_obs"), g(d, m, "excess_labs")
            cells.append(f"{f(core)} / {f(labs)}")
        print(f"| {TRIALS[key]['name'].replace(' (adapted)', '')} | {pop} | {f(g(d, 'dx', 'pairs'), 0)} | " + " | ".join(cells) + " |")
        rows.append(dict(trial=n, role=TRIALS[key]["role"], **{f"{m}|core": g(d, m, "excess_phys_obs") for m in arms},
                         **{f"{m}|labs": g(d, m, "excess_labs") for m in arms},
                         **{f"{m}|lvef": g(d, m, "smd_obs_lvef") for m in arms},
                         **{f"{m}|bnp": g(d, m, "pp_lab_ntprobnp") for m in arms},
                         **{f"{m}|echo": g(d, m, "excess_echo") for m in arms},
                         **{f"{m}|echo_chance": g(d, m, "chance_echo") for m in arms}))
    return pd.DataFrame(rows)


def deltas(r):
    print("\n### Deltas (absolute change in mean excess |SMD| over chance; negative = better balance)\n")
    print("| Trial | Role | ECG vs none (dx base): core / labs | hdPS200 vs none (dx base): core / labs | "
          "ECG added to dx+hdPS200: core / labs | ECG added to claims+hdPS200: core / labs | Measured LVEF: dx → dx+ECG | dx+hdPS200 → +ECG | NT-proBNP: dx → dx+ECG | dx+hdPS200 → +ECG |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    rel = lambda a, b: b - a  # absolute change in mean excess |SMD|
    out = []
    for x in r.itertuples(index=False):
        x = x._asdict() if hasattr(x, "_asdict") else dict(x)
    for _, x in r.iterrows():
        e_c, e_l = rel(x["dx|core"], x["dx+ECGpc|core"]), rel(x["dx|labs"], x["dx+ECGpc|labs"])
        h_c, h_l = rel(x["dx|core"], x["dx+hdPS200|core"]), rel(x["dx|labs"], x["dx+hdPS200|labs"])
        he_c, he_l = rel(x["dx+hdPS200|core"], x["dx+hdPS200+ECGpc|core"]), rel(x["dx+hdPS200|labs"], x["dx+hdPS200+ECGpc|labs"])
        ce_c, ce_l = rel(x["claims+hdPS200|core"], x["claims+hdPS200+ECGpc|core"]), rel(x["claims+hdPS200|labs"], x["claims+hdPS200+ECGpc|labs"])
        out.append(dict(trial=x.trial, role=x.role, e_c=e_c, e_l=e_l, h_c=h_c, h_l=h_l, he_c=he_c, he_l=he_l, ce_c=ce_c, ce_l=ce_l,
                        lv0=x["dx|lvef"], lv1=x["dx+ECGpc|lvef"], lv2=x["dx+hdPS200|lvef"], lv3=x["dx+hdPS200+ECGpc|lvef"]))
        print(f"| {x.trial} | {x.role} | {e_c:+.3f} / {e_l:+.3f} | {h_c:+.3f} / {h_l:+.3f} | {he_c:+.3f} / {he_l:+.3f} | "
              f"{ce_c:+.3f} / {ce_l:+.3f} | {f(x['dx|lvef'], 2)} → {f(x['dx+ECGpc|lvef'], 2)} | "
              f"{f(x['dx+hdPS200|lvef'], 2)} → {f(x['dx+hdPS200+ECGpc|lvef'], 2)} | "
              f"{f(x['dx|bnp'], 2)} → {f(x['dx+ECGpc|bnp'], 2)} | {f(x['dx+hdPS200|bnp'], 2)} → {f(x['dx+hdPS200+ECGpc|bnp'], 2)} |")
    o = pd.DataFrame(out)
    for role in ("physiology", "control"):
        s = o[o.role == role]
        print(f"\nMedian ({role}, n = {len(s)}): ECG on dx base core {s.e_c.median():+.3f}, labs {s.e_l.median():+.3f}; "
              f"hdPS200 on dx base core {s.h_c.median():+.3f}, labs {s.h_l.median():+.3f}; "
              f"ECG added to dx+hdPS200 core {s.he_c.median():+.3f}, labs {s.he_l.median():+.3f}; "
              f"ECG added to claims+hdPS200 core {s.ce_c.median():+.3f}, labs {s.ce_l.median():+.3f}. "
              f"ECG better than hdPS200 on core physiology in {(s.e_c < s.h_c).sum()} of {len(s)}.")
    big = o[o.lv0 >= 0.1]
    if len(big):
        print(f"\nTrials with dx-base measured-LVEF SMD >= 0.1: {len(big)} ({', '.join(big.trial)}). Median LVEF SMD: dx {big.lv0.median():.2f}, "
              f"dx+ECG {big.lv1.median():.2f}, dx+hdPS200 {big.lv2.median():.2f}, dx+hdPS200+ECG {big.lv3.median():.2f}.")


def echo_table(r):
    print("\n### Echo report measurements: mean excess |SMD| over chance (PanEcho labels; measured in 1–5% of patients)\n")
    print("| Trial | Chance level (dx) | dx | dx+ECGpc | dx+hdPS200 | dx+hdPS200+ECGpc | clinical |")
    print("|---|---|---|---|---|---|---|")
    for _, x in r.iterrows():
        print(f"| {x.trial} | {f(x['dx|echo_chance'])} | {f(x['dx|echo'])} | {f(x['dx+ECGpc|echo'])} | {f(x['dx+hdPS200|echo'])} | "
              f"{f(x['dx+hdPS200+ECGpc|echo'])} | {f(x['clinical|echo'])} |")
    m = r[[c for c in r.columns if c.endswith("|echo")]].median()
    print(f"\nMedian across trials: dx {m['dx|echo']:.3f}, dx+ECGpc {m['dx+ECGpc|echo']:.3f}, dx+hdPS200 {m['dx+hdPS200|echo']:.3f}, "
          f"dx+hdPS200+ECGpc {m['dx+hdPS200+ECGpc|echo']:.3f}, clinical {m['clinical|echo']:.3f}.")


def dxall_table():
    print("\n### Selected cardiology diagnoses (dx) vs all diagnosis codes (dxall), primary population\n")
    print("Physiology columns: mean excess |SMD| over chance.\n")
    print("| Trial | Pairs dx / dxall | Core-9 phys dx / dxall / dxall+ECG | Labs dx / dxall / dxall+ECG | Non-dx pool-B > 0.1: dx / dxall / dxall+ECG |")
    print("|---|---|---|---|---|")
    for key, n in ORDER:
        d = load("sparse", n, True)
        if d is None:
            continue
        print(f"| {n} | {f(g(d,'dx','pairs'),0)} / {f(g(d,'dxall','pairs'),0)} | {f(g(d,'dx','excess_phys_obs'))} / {f(g(d,'dxall','excess_phys_obs'))} / "
              f"{f(g(d,'dxall+ECGpc','excess_phys_obs'))} | {f(g(d,'dx','excess_labs'))} / {f(g(d,'dxall','excess_labs'))} / {f(g(d,'dxall+ECGpc','excess_labs'))} | "
              f"{f(g(d,'dx','B_nondx_frac_gt_0_1'),3)} / {f(g(d,'dxall','B_nondx_frac_gt_0_1'),3)} / {f(g(d,'dxall+ECGpc','B_nondx_frac_gt_0_1'),3)} |")


def longtail_table():
    print("\n### Long-tail balance (full design), primary population: pool-B share > 0.1 (excess over chance)\n")
    print("| Trial | Pairs clinical | Clinical | + ECG | + CLMBR | + hdPS200 | + hdPS200 + ECG + CLMBR |")
    print("|---|---|---|---|---|---|---|")
    for key, n in ORDER:
        d = load("full", n, True)
        if d is None:
            continue
        cells = [f"{100 * g(d, m, 'B_frac_gt_0_1'):.1f}% ({100 * g(d, m, 'B_frac_excess'):.1f})" for m in
                 ["clinical", "clinical+ECG", "clinical+CLMBR", "clinical+hdPS200", "clinical+hdPS200+ECG+CLMBR"]]
        print(f"| {n} | {f(g(d, 'clinical', 'pairs'), 0)} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    r = table_phys(True)
    deltas(r)
    echo_table(r)
    dxall_table()
    longtail_table()
    r2 = table_phys(False)
    print("\n#### Secondary population deltas")
    deltas(r2)
