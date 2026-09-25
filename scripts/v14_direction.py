#!/usr/bin/env python
"""Post-hoc (v1.4 addition G): directional consistency and closeness to the RCT, RCT-DUPLICATE-style metrics.

Per arm, across trials:
  direction    sign(log HR emulated) == sign(log HR RCT)            (all trials; and RCTs with CI excluding 1)
  regulatory   same significance and, if significant, same direction (Franklin 2021 / Wang 2023)
  within25     HR_emulated / HR_RCT in [0.8, 1.25]
  pearson / spearman of log HRs; calibration slope (OLS of emulated on RCT log HR)
Point estimates: bootstrap replicate 0 (full cohort, imputation 1; identical resamples across the v1.3 and
v1.4-F bootstrap files, so all arms are comparable). Uncertainty: 200 paired bootstrap replicates (patients
resampled within trial; RCT estimate drawn from its CI) -> 95% CI of each metric and of arm differences.
Subsets: all 18; closely emulated (rating 'close'); physiology; RCT significant.
"""
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import PUBLISHED, TRIALS, rating  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402
from v13_summarize import md  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "v14"
ARMS = ["unmatched", "demo", "ECGonly", "demo+ECG", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)", "R+"]
LAB = {"unmatched": "Unadjusted", "demo": "Demographics", "ECGonly": "ECG only", "demo+ECG": "Demographics + ECG", "sparse": "Sparse",
       "sparse+ECG": "Sparse + ECG", "hdPS200": "hdPS200", "hdPS200+ECG": "hdPS200 + ECG", "clinical (reference)": "Clinical PS",
       "R+": "R+ physiology ref"}
CMP = [("sparse+ECG", "sparse"), ("hdPS200+ECG", "hdPS200"), ("ECGonly", "unmatched"), ("demo+ECG", "demo"),
       ("sparse+ECG", "clinical (reference)"), ("hdPS200+ECG", "clinical (reference)")]


def load():
    names = {**PRIMARY, **EXTRA}
    L, meta = [], {}
    for n, (k, _) in names.items():
        f1, f2 = A / "claude-v13-bootstrap" / f"bs_{n}.csv", A / "claude-v14-ecgonly" / f"bs_{n}.csv"
        if not (f1.exists() and f2.exists()):
            continue
        a = pd.read_csv(f1)
        b = pd.read_csv(f2)
        b = b[b.arm.isin(["demo", "ECGonly", "demo+ECG"])]
        d = pd.concat([a, b])
        d = d[d.arm.isin(ARMS)]
        d["trial"] = n
        L.append(d)
        pairs = int(pd.read_csv(A / f"claude-cap4-all-{n}" / "summary_pooled.csv", index_col=0).loc["clinical (reference)", "pairs"])
        br, se = bench(k)
        lo, hi = PUBLISHED[k]["ci"]
        if abs(PUBLISHED[k]["our_orientation"] - PUBLISHED[k]["hr"]) > 1e-6:
            lo, hi = 1 / hi, 1 / lo
        meta[n] = dict(key=k, b=br, se=se, sig=(lo > 1) or (hi < 1), rating=rating(k, pairs)[1], role=TRIALS[k].get("role"))
    return pd.concat(L), meta


def metrics(B, S, rct_b, rct_sig):
    """B, S: trials x arms arrays of log HR and SE; rct_b: log HR per trial; rct_sig bool per trial."""
    z = B / S
    sig = np.abs(z) > 1.96
    out = {}
    for j in range(B.shape[1]):
        b, s = B[:, j], sig[:, j]
        ok = ~np.isnan(b)
        bb, rr, ss, rs = b[ok], rct_b[ok], s[ok], rct_sig[ok]
        dirn = np.sign(bb) == np.sign(rr)
        reg = np.where(rs, ss & dirn, ~ss)
        w25 = np.abs(bb - rr) <= np.log(1.25)
        pear = np.corrcoef(bb, rr)[0, 1] if len(bb) > 2 else np.nan
        spear = spearmanr(bb, rr).statistic if len(bb) > 2 else np.nan
        slope = np.polyfit(rr, bb, 1)[0] if len(bb) > 2 else np.nan
        out[j] = dict(direction=dirn.mean(), direction_sigRCT=dirn[rs].mean() if rs.any() else np.nan, regulatory=reg.mean(),
                      within25=w25.mean(), pearson=pear, spearman=spear, slope=slope, mean_abs=np.mean(np.abs(bb - rr)), k=len(bb))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    D, meta = load()
    trials = sorted(meta)
    subsets = {"all": trials, "close emulation": [t for t in trials if meta[t]["rating"] == "close"],
               "physiology": [t for t in trials if meta[t]["role"] == "physiology"],
               "RCT significant": [t for t in trials if meta[t]["sig"]]}
    Lb = D.pivot_table(index=["trial", "rep"], columns="arm", values="loghr").reindex(columns=ARMS)
    Ls = D.pivot_table(index=["trial", "rep"], columns="arm", values="se").reindex(columns=ARMS)
    reps = sorted(D.rep.unique())
    rct_draw = {t: np.r_[meta[t]["b"], meta[t]["b"] + meta[t]["se"] * np.random.default_rng(zlib.crc32(t.encode())).normal(size=len(reps) - 1)]
                for t in trials}
    print("# Directional consistency and closeness to the RCT (post-hoc v1.4 addition G; exploratory)\n")
    print("Point estimates from the full cohort (imputation 1). Inference for arm differences: exact McNemar (binary metrics) and "
          "sign-flip (mean |Δ|) tests across trials. Bootstrap intervals (lo, hi) are descriptive only: re-matching on resamples with "
          "duplicate patients is not valid for matching estimators (audit 2026-09-25).\n")
    rows, drows = [], []
    for sname, tr in subsets.items():
        res = []
        for ri, r in enumerate(reps):
            B = np.array([Lb.loc[(t, r)].to_numpy() for t in tr])
            S = np.array([Ls.loc[(t, r)].to_numpy() for t in tr])
            rb = np.array([rct_draw[t][ri] for t in tr])
            rs = np.array([meta[t]["sig"] for t in tr])
            res.append(metrics(B, S, rb, rs))
        for j, a in enumerate(ARMS):
            p = res[0][j]
            row = dict(subset=sname, arm=LAB[a], trials=p["k"])
            for m in ("direction", "direction_sigRCT", "regulatory", "within25", "pearson", "spearman", "slope", "mean_abs"):
                bs = np.array([x[j][m] for x in res[1:]], float)
                row[m] = p[m]
                row[m + "_ci"] = f"{np.nanpercentile(bs, 2.5):.2f}–{np.nanpercentile(bs, 97.5):.2f}"
            rows.append(row)
        for a2, a1 in CMP:
            j2, j1 = ARMS.index(a2), ARMS.index(a1)
            for m in ("direction", "regulatory", "within25", "pearson", "mean_abs"):
                p = res[0][j2][m] - res[0][j1][m]
                bs = np.array([x[j2][m] - x[j1][m] for x in res[1:]], float)
                lo, hi = np.nanpercentile(bs, [2.5, 97.5])
                better = (p < 0) if m == "mean_abs" else (p > 0)
                # audit fix: exact paired tests on the full-cohort estimates (bootstrap interval descriptive only)
                B0 = np.array([Lb.loc[(t, 0)].to_numpy() for t in tr]); S0 = np.array([Ls.loc[(t, 0)].to_numpy() for t in tr])
                rb0 = np.array([meta[t]["b"] for t in tr]); rs0 = np.array([meta[t]["sig"] for t in tr])
                def per_trial(j):
                    b, s_ = B0[:, j], S0[:, j]
                    sig = np.abs(b / s_) > 1.96
                    dirn = np.sign(b) == np.sign(rb0)
                    return {"direction": dirn.astype(float), "regulatory": np.where(rs0, sig & dirn, ~sig).astype(float),
                            "within25": (np.abs(b - rb0) <= np.log(1.25)).astype(float), "mean_abs": np.abs(b - rb0)}.get(m)
                pt = None
                if m in ("direction", "regulatory", "within25"):
                    x2, x1 = per_trial(j2), per_trial(j1)
                    k_up, k_dn = int(((x2 == 1) & (x1 == 0)).sum()), int(((x2 == 0) & (x1 == 1)).sum())
                    from scipy.stats import binomtest
                    pt = binomtest(k_up, k_up + k_dn, 0.5).pvalue if k_up + k_dn else 1.0
                    exact = f"McNemar exact: {k_up} gained vs {k_dn} lost, p = {pt:.3f}"
                elif m == "mean_abs":
                    from v13_summarize import sign_flip
                    pt = sign_flip(per_trial(j2) - per_trial(j1))[1]
                    exact = f"sign-flip p = {pt:.3f}"
                else:
                    exact = ""
                drows.append(dict(subset=sname, comparison=f"{LAB[a2]} − {LAB[a1]}", metric=m, trials=len(tr), difference=p, exact_test=exact, lo=lo, hi=hi,
                                  share_boot_favouring=float(np.mean(bs < 0) if m == "mean_abs" else np.mean(bs > 0)),
                                  favours_first=bool(better)))
    R = pd.DataFrame(rows)
    Dd = pd.DataFrame(drows)
    R.to_csv(OUT / "direction_metrics.csv", index=False)
    Dd.to_csv(OUT / "direction_differences.csv", index=False)
    for sname, tr in subsets.items():
        x = R[R.subset == sname]
        print(f"## {sname} ({len(tr)} trials: {', '.join(tr)})\n")
        show = x[["arm", "trials", "direction", "direction_sigRCT", "regulatory", "within25", "pearson", "pearson_ci", "slope", "mean_abs"]]
        print(md(show, 2) + "\n")
        y = Dd[Dd.subset == sname]
        print("Differences between arms (first − second; for mean_abs negative favours the first arm):\n")
        print(md(y[["comparison", "metric", "difference", "exact_test", "lo", "hi"]], 3) + "\n")
    print("Definitions: direction = same side of HR 1 as the RCT; direction_sigRCT = same, among RCTs whose CI excludes 1; "
          "regulatory = same significance and direction (RCT-DUPLICATE); within25 = emulated HR within 0.8–1.25× the RCT HR; "
          "slope = calibration slope of emulated on RCT log HR (1 = ideal).\n")


if __name__ == "__main__":
    main()
