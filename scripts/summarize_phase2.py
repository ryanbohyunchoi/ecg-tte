"""Phase-2 summary (protocol v1 section 8, amendment v1.1 D): agreement with the RCT and with the
full-data reference, paired comparisons across trials, negative controls. Aggregate markdown.

Usage: python summarize_phase2.py [all|op|shd|2016]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import NCO, PUBLISHED, TRIALS  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
POP = sys.argv[1] if len(sys.argv) > 1 else "all"
ORDER = [("comet", "comet"), ("paradigm_hf", "paradigm"), ("paradigm_hf_seq", "paradigm-hf-seq"),
         ("paragon_hf", "paragon-hf"), ("transform_hf", "transform-hf"), ("elite_ii", "elite-ii"), ("life", "life"),
         ("plato", "plato"), ("aristotle", "aristotle"), ("rocket_af", "rocket-af"), ("rely", "rely"),
         ("allhat", "allhat"), ("dapa_hf", "dapa-hf"), ("partner", "partner")]
ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "clinical (reference)"]
if POP == "shd":
    ARMS = ARMS + ["sparse+SHD", "sparse+ECG+SHD", "hdPS200+ECG+SHD"]
LABEL = {"unmatched": "M0 unadjusted", "sparse": "M1 sparse", "sparse+ECG": "M2 sparse+ECG", "hdPS200": "M3 hdPS200",
         "hdPS200+ECG": "M4 hdPS200+ECG", "clinical (reference)": "R clinical (reference)",
         "sparse+SHD": "sparse+SHD", "sparse+ECG+SHD": "sparse+ECG+SHD", "hdPS200+ECG+SHD": "hdPS200+ECG+SHD"}


def bench(key):
    p = PUBLISHED[key]
    lo, hi = p["ci"]
    if abs(p["our_orientation"] - p["hr"]) > 1e-6:  # orientation flipped (COMET)
        lo, hi = 1 / hi, 1 / lo
    b = np.log(p["our_orientation"])
    se = (np.log(hi) - np.log(lo)) / (2 * 1.96)
    return b, se, lo, hi


def primary_set():
    keep = []
    for key, n in ORDER:
        f = A / f"claude-cap4-all-{n}" / "summary_pooled.csv"
        if f.exists() and pd.read_csv(f, index_col=0).loc["clinical (reference)", "pairs"] >= 400:
            keep.append(n)
    return keep


def load():
    rows = []
    for key, n in ORDER:
        f = A / f"claude-phase2-{POP}-{n}.csv"
        if f.exists():
            d = pd.read_csv(f)
            d["key"], d["name"] = key, n
            rows.append(d)
    return pd.concat(rows) if rows else pd.DataFrame()


def fmt(r):
    return "–" if pd.isna(r.hr) else f"{r.hr:.2f} ({r.lo:.2f}–{r.hi:.2f})"


def main():
    D = load()
    if D.empty:
        print("no phase-2 results")
        return
    P = primary_set()
    print(f"# Phase 2 — population: {POP}\n")
    print("Primary analysis set (clinical-PS pairs >= 400, all initiators; DIONYSOS not emulable): " + ", ".join(P) + "\n")
    prim = D[(D.outcome == "primary") & (D.horizon == "trial") & (D.analysis == "matched")]
    print("## Primary outcome, trial horizon, matched (HR, 95% CI; our arm order = arm 1 vs arm 2)\n")
    print("| Trial | Set | RCT benchmark | " + " | ".join(LABEL[a] for a in ARMS) + " |")
    print("|---|---|---|" + "---|" * len(ARMS))
    for key, n in ORDER:
        x = prim[prim.name == n].set_index("method")
        if x.empty:
            continue
        b, se, lo, hi = bench(key)
        cells = [fmt(x.loc[a]) if a in x.index else "–" for a in ARMS]
        print(f"| {TRIALS[key]['name'].replace(' (adapted)', '')} | {'primary' if n in P else 'suppl.'} | "
              f"{np.exp(b):.2f} ({lo:.2f}–{hi:.2f}) | " + " | ".join(cells) + " |")

    def metrics(sub, arms, trials):
        out = []
        ref = sub[sub.method == "clinical (reference)"].set_index("name")
        for a in arms:
            s = sub[(sub.method == a) & (sub.name.isin(trials))].dropna(subset=["loghr"])
            if s.empty:
                continue
            est = reg = std = 0
            dr, dref = [], []
            for r in s.itertuples():
                b, se, lo, hi = bench(r.key)
                est += int(lo <= r.hr <= hi)
                rct_sig, obs_sig = (lo > 1 or hi < 1), (r.lo > 1 or r.hi < 1)
                same_dir = np.sign(r.loghr) == np.sign(b)
                reg += int((rct_sig and obs_sig and same_dir) or (not rct_sig and not obs_sig))
                std += int(abs((r.loghr - b) / np.sqrt(r.se ** 2 + se ** 2)) < 1.96)
                dr.append(abs(r.loghr - b))
                if r.name in ref.index and not pd.isna(ref.loc[r.name, "loghr"]):
                    dref.append(abs(r.loghr - ref.loc[r.name, "loghr"]))
            out.append(dict(arm=LABEL[a], trials=len(s), estimate_agreement=est, regulatory_agreement=reg,
                            std_diff_agreement=std, mean_abs_dlog_rct=np.mean(dr),
                            mean_abs_dlog_ref=np.mean(dref) if dref else np.nan,
                            pearson_r=np.corrcoef(s.loghr, [bench(k)[0] for k in s.key])[0, 1] if len(s) > 2 else np.nan))
        return pd.DataFrame(out)

    print("\n## Agreement with the RCT and with the full-data reference (primary set, primary outcome)\n")
    M = metrics(prim, ARMS, P)
    print("| Arm | Trials | Estimate agreement | Regulatory agreement | Std-difference agreement | Mean abs log-HR diff vs RCT | Mean abs log-HR diff vs reference R | Pearson r (log HR vs RCT) |")
    print("|---|---|---|---|---|---|---|---|")
    for r in M.itertuples():
        print(f"| {r.arm} | {r.trials} | {r.estimate_agreement}/{r.trials} | {r.regulatory_agreement}/{r.trials} | "
              f"{r.std_diff_agreement}/{r.trials} | {r.mean_abs_dlog_rct:.3f} | {r.mean_abs_dlog_ref:.3f} | {r.pearson_r:.2f} |")

    print("\n## Paired comparisons across primary-set trials (Wilcoxon signed-rank, two-sided)\n")
    X = prim[prim.name.isin(P)].pivot_table(index="name", columns="method", values="loghr")
    ref = X.get("clinical (reference)")
    rct = pd.Series({n: bench(k)[0] for k, n in ORDER}).reindex(X.index)
    for a, b in (("sparse+ECG", "sparse"), ("hdPS200+ECG", "hdPS200"), ("hdPS200", "sparse"), ("hdPS200+ECG", "sparse")):
        if a not in X or b not in X:
            continue
        for tgt, T in (("RCT", rct), ("reference R", ref)):
            da, db = (X[a] - T).abs(), (X[b] - T).abs()
            ok = da.notna() & db.notna()
            if ok.sum() >= 3 and (da[ok] - db[ok]).abs().sum() > 0:
                p = wilcoxon(da[ok], db[ok]).pvalue
                print(f"- |log HR − {tgt}|: {LABEL[a]} vs {LABEL[b]}: median {da[ok].median():.3f} vs {db[ok].median():.3f}; "
                      f"{a} closer in {(da[ok] < db[ok]).sum()}/{ok.sum()} trials; p = {p:.3f}")

    print("\n## Negative-control outcomes (trial horizon, matched; expected HR = 1)\n")
    nco = D[D.outcome.isin(NCO.keys()) & (D.horizon == "trial") & (D.analysis == "matched") & D.name.isin(P)]
    print("| Arm | Estimates | CI excludes 1 | Mean abs log HR |")
    print("|---|---|---|---|")
    for a in ARMS:
        s = nco[nco.method == a].dropna(subset=["loghr"])
        if len(s):
            print(f"| {LABEL[a]} | {len(s)} | {((s.lo > 1) | (s.hi < 1)).sum()} | {s.loghr.abs().mean():.3f} |")

    print("\n## Sensitivity analyses (primary set): agreement summaries\n")
    print("| Analysis | Arm | Estimate agreement | Regulatory agreement | Mean abs log-HR diff vs RCT | vs reference R |")
    print("|---|---|---|---|---|---|")
    for lab, sel in (("overlap-weighted", (D.outcome == "primary") & (D.horizon == "trial") & (D.analysis == "overlap_weighted")),
                     ("12-month horizon", (D.outcome == "primary") & (D.horizon == "12m") & (D.analysis == "matched")),
                     ("60-month horizon", (D.outcome == "primary") & (D.horizon == "60m") & (D.analysis == "matched")),
                     ("no-cause deaths = non-CV", (D.outcome == "primary_cv_noncause_as_nonCV") & (D.horizon == "trial") & (D.analysis == "matched"))):
        sub = D[sel]
        if lab.startswith("no-cause"):  # trials without CV death use the primary estimate
            sub = pd.concat([sub, prim[~prim.name.isin(sub.name.unique())]])
        m = metrics(sub, ARMS, P)
        for r in m.itertuples():
            print(f"| {lab} | {r.arm} | {r.estimate_agreement}/{r.trials} | {r.regulatory_agreement}/{r.trials} | "
                  f"{r.mean_abs_dlog_rct:.3f} | {r.mean_abs_dlog_ref:.3f} |")


if __name__ == "__main__":
    main()
