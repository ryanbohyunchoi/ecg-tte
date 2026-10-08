#!/usr/bin/env python
"""v1 code audit (MIMIC): (1) PS-CVD5-analog prior-admission flags (claude-v21-paper2/mimic/flags) vs the window-fixed
baseline dx of the 3 new trials (windowfix/trials/<k>/baseline.parquet) -> discordance counts (1-10 suppressed);
(2) missingness of the demographic PS columns (if any were missing, IterativeImputer would impute them from all
baseline columns, including the index-admission dx of the unfixed v20 new-trial dirs used by mimic_cvd5.py);
(3) independent recompute of the primary7 cvd5 relative reduction, sign-flip p and bootstrap CI from *_arms.csv.
Aggregates only. Output: /mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/code/mimic_flags_demo_check.csv
"""
import itertools
import os
import sys
from pathlib import Path

os.umask(0o077)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "v21"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import mimic_cvd5 as C5  # noqa: E402

M = C5.M
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/code")
WF = C5.OUT / "windowfix" / "trials"
P7 = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2"]


def sup(n):
    return "1-10" if 1 <= n <= 10 else int(n)


def main():
    rows = []
    for k in M.NEW:
        F = pd.read_parquet(C5.OUT / "flags" / f"{k}.parquet").set_index("pid")
        B = pd.read_parquet(WF / k / "baseline.parquet").assign(pid=lambda x: x.pid.astype(str)).set_index("pid")
        for c in ("hypertension", "diabetes", "ischemic_heart_disease_or_mi", "atrial_fibrillation", "heart_failure"):
            if c in B:
                b = B[c].reindex(F.index)
                rows.append(dict(check=f"{k}: cvd5 prior flag vs windowfix baseline [{c}]", value=sup(int((b.notna() & (b != F[c])).sum()))))
    for k in C5.TRIALS:
        D = M.VA.TrialData(M.tdir(k))
        demo = D.groups["demo"]
        rows.append(dict(check=f"{k}: demo cols / max missing frac / indicator cols",
                         value=f"{len(demo)} / {float(D.miss_frac[demo].max()):.4f} / {D.Gm['demo'].shape[1] - len(demo)}"))
    A = pd.concat([pd.read_csv(C5.OUT / "results" / f"{k}_arms.csv") for k in C5.TRIALS])
    for base in ("cvd5", "cvd5_anydm", "cvd5_incl"):
        for pop in ("all", "no_index_day_ecg"):
            s = A[(A.base == base) & (A["pop"] == pop) & A.trial.isin(P7)].pivot(index="trial", columns="arm", values="mean_smd").reindex(P7)
            for arm in ("ECG", "permECG"):
                mb, ma = s["base"].to_numpy(), s[arm].to_numpy()
                d = mb - ma
                sg = np.array(list(itertools.product([-1, 1], repeat=len(d))))
                p1 = float(np.mean((sg * np.abs(d)).mean(1) >= d.mean() - 1e-12))
                rng = np.random.default_rng(0)
                i = rng.integers(0, len(mb), (2000, len(mb)))
                r = 100 * (1 - ma[i].mean(1) / mb[i].mean(1))
                rows.append(dict(check=f"{base}|{pop}|{arm}: relred ratio-of-means / mean-of-ratios / lower / p1 / CI2000",
                                 value=f"{100 * (1 - ma.mean() / mb.mean()):.2f} / {100 * np.mean(1 - ma / mb):.2f} / {(ma < mb).sum()}/7 / "
                                       f"{p1:.4f} / [{np.percentile(r, 2.5):.1f}, {np.percentile(r, 97.5):.1f}]"))
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "mimic_flags_demo_check.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 200)
    print(R.to_string(index=False))


if __name__ == "__main__":
    main()
