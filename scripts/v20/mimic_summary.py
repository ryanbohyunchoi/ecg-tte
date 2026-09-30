#!/usr/bin/env python
"""v2.0 MIMIC-IV replication: summarise results/<trial>_arms.csv across trials (aggregates only).

Sets: primary = 7 cardiovascular trials (5 v1.5 + SOAP II + ELITE II); negative control = PEPTIC; all 8 = sensitivity.
Balance: per base PS and population, mean over trials of % |SMD|<0.1 and mean |SMD| for base / +ECG / +permuted ECG;
Delta (ECG - base), trials improved, exact one-sided sign-flip p; relative reduction in mean |SMD|
1 - mean_t(m_arm)/mean_t(m_base) with a percentile bootstrap CI over trials (2,000 resamples, seed 0).
Agreement: Pearson r of log HRs, estimate agreement (|b - rb| <= 1.96 rs), standardised-difference agreement
(|b - rb| / sqrt(se^2 + rs^2) < 1.96), mean |b - rb|; ECG vs base: trials closer, sign-flip p.
Writes <OUT>/summary/{summary.json, tables.md}.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mimic_replication import OUT, exact_signflip  # noqa: E402

BUILT = ["plato", "aristotle", "rocket_af", "transform_hf", "comet"]
SETS = {"primary7": BUILT + ["soap2", "elite2"], "built5": BUILT, "all8": BUILT + ["soap2", "elite2", "peptic"]}
NAMES = dict(plato="PLATO", aristotle="ARISTOTLE", rocket_af="ROCKET AF", transform_hf="TRANSFORM-HF", comet="COMET",
             soap2="SOAP II", elite2="ELITE II", peptic="PEPTIC")


def load():
    fs = sorted((OUT / "results").glob("*_arms.csv"))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)


def boot_rr(mb, ma, n=2000):
    mb, ma = np.asarray(mb, float), np.asarray(ma, float)
    rng = np.random.default_rng(0)
    i = rng.integers(0, len(mb), (n, len(mb)))
    r = 100 * (1 - ma[i].mean(1) / mb[i].mean(1))
    return [float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))]


def balance(A, trials, base, pop, metric="pct_bal"):
    S = A[(A.base == base) & (A["pop"] == pop) & A.trial.isin(trials)].pivot(index="trial", columns="arm")
    if S.empty or "base" not in S[metric]:
        return None
    out = dict(k=int(len(S)))
    for arm in ("base", "ECG", "permECG"):
        out[f"pct_bal_{arm}"] = float(S["pct_bal"][arm].mean())
        out[f"mean_smd_{arm}"] = float(S["mean_smd"][arm].mean())
    for arm in ("ECG", "permECG"):
        d = (S["pct_bal"][arm] - S["pct_bal"]["base"]).to_numpy()
        out[f"dpts_{arm}"] = float(np.mean(d))
        out[f"better_{arm}"] = f"{int((d > 0).sum())}/{len(d)}"
        out[f"p_{arm}"] = exact_signflip(d)
        mb, ma = S["mean_smd"]["base"].to_numpy(), S["mean_smd"][arm].to_numpy()
        out[f"relred_{arm}"] = float(100 * (1 - ma.mean() / mb.mean()))
        out[f"relred_{arm}_ci"] = boot_rr(mb, ma)
        out[f"lower_smd_{arm}"] = f"{int((ma < mb).sum())}/{len(mb)}"
        out[f"p_smd_{arm}"] = exact_signflip(mb - ma)
    for blk in ("A", "B", "D"):
        c = f"mean_smd_{blk}"
        if c in S and S[c]["base"].notna().any():
            out[f"relred_ECG_block{blk}"] = float(100 * (1 - S[c]["ECG"].mean() / S[c]["base"].mean()))
    return out


def agreement(A, trials, base, pop):
    S = A[(A.base == base) & (A["pop"] == pop) & A.trial.isin(trials)]
    res = {}
    for arm in ("base", "ECG", "permECG"):
        s = S[S.arm == arm].set_index("trial")
        b, se, rb, rs = s.loghr, s.se, s.rct_loghr, s.rct_se
        ok = np.isfinite(b) & np.isfinite(se)
        b, se, rb, rs = b[ok], se[ok], rb[ok], rs[ok]
        res[arm] = dict(k=int(len(b)), r=float(np.corrcoef(b, rb)[0, 1]) if len(b) > 2 else np.nan,
                        est_agree=f"{int((np.abs(b - rb) <= 1.96 * rs).sum())}/{len(b)}",
                        std_agree=f"{int((np.abs(b - rb) / np.sqrt(se ** 2 + rs ** 2) < 1.96).sum())}/{len(b)}",
                        mean_abs_diff=float(np.mean(np.abs(b - rb))))
    sb = S[S.arm == "base"].set_index("trial")
    se_ = S[S.arm == "ECG"].set_index("trial")
    d = (np.abs(sb.loghr - sb.rct_loghr) - np.abs(se_.loghr - se_.rct_loghr)).dropna().to_numpy()
    res["ECG_vs_base"] = dict(closer=f"{int((d > 0).sum())}/{len(d)}", p=exact_signflip(d))
    return res


def main():
    A = load()
    (OUT / "summary").mkdir(parents=True, exist_ok=True)
    have = sorted(A.trial.unique())
    summ = dict(trials_available=have, balance={}, agreement={}, per_trial={})
    for sname, tr in SETS.items():
        tr = [t for t in tr if t in have]
        for base in ("demo", "sparse", "hdPS200", "clinical"):
            for pop in ("all", "no_index_day_ecg"):
                key = f"{sname}|{base}|{pop}"
                b = balance(A, tr, base, pop)
                if b:
                    summ["balance"][key] = b
                    summ["agreement"][key] = agreement(A, tr, base, pop)
    P = A[(A["pop"] == "all")].copy()
    P["hr"] = np.exp(P.loghr)
    P["lo"] = np.exp(P.loghr - 1.96 * P.se)
    P["hi"] = np.exp(P.loghr + 1.96 * P.se)
    for t in have:
        summ["per_trial"][t] = {f"{r.base}|{r.arm}": dict(pct_bal=round(r.pct_bal, 1), mean_smd=round(r.mean_smd, 4),
                                                           hr=round(r.hr, 3), lo=round(r.lo, 3), hi=round(r.hi, 3),
                                                           n_pairs=int(r.n_pairs), n_vars=int(r.n_vars))
                                for r in P[P.trial == t].itertuples()}
    json.dump(summ, open(OUT / "summary/summary.json", "w"), indent=1, default=float)
    # tables.md
    L = ["# MIMIC-IV replication: generated tables (aggregates only)", ""]
    L += ["## Balance: % held-out |SMD| < 0.1 and relative reduction in mean |SMD| (mean over trials)", "",
          "| Set | Base PS | Population | k | % bal base | % bal +ECG | Δ pts | better | p | rel. red. mean |SMD| +ECG [95% CI] | lower mean |SMD| | p | % bal +perm | Δ perm | rel. red. perm |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, b in summ["balance"].items():
        s, base, pop = key.split("|")
        ci = b["relred_ECG_ci"]
        L.append(f"| {s} | {base} | {pop} | {b['k']} | {b['pct_bal_base']:.1f} | {b['pct_bal_ECG']:.1f} | {b['dpts_ECG']:+.1f} | "
                 f"{b['better_ECG']} | {b['p_ECG']:.3f} | {b['relred_ECG']:.1f} [{ci[0]:.1f}, {ci[1]:.1f}] | {b['lower_smd_ECG']} | "
                 f"{b['p_smd_ECG']:.3f} | {b['pct_bal_permECG']:.1f} | {b['dpts_permECG']:+.1f} | {b['relred_permECG']:.1f} |")
    L += ["", "## Relative reduction in mean |SMD| with ECG by block (A core labs/vitals, B additional labs, D utilisation)", "",
          "| Set | Base PS | Population | A | B | D |", "|---|---|---|---|---|---|"]
    for key, b in summ["balance"].items():
        s, base, pop = key.split("|")
        L.append(f"| {s} | {base} | {pop} | " + " | ".join(f"{b.get(f'relred_ECG_block{x}', np.nan):.1f}" for x in "ABD") + " |")
    L += ["", "## RCT agreement (trial primary outcome)", "",
          "| Set | Base PS | Population | Arm | k | r | estimate agreement | std-diff agreement | mean |Δ log HR| | ECG closer | p |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, ag in summ["agreement"].items():
        s, base, pop = key.split("|")
        for arm in ("base", "ECG", "permECG"):
            g = ag[arm]
            extra = f"{ag['ECG_vs_base']['closer']} | {ag['ECG_vs_base']['p']:.3f}" if arm == "ECG" else " | "
            L.append(f"| {s} | {base} | {pop} | {arm} | {g['k']} | {g['r']:.2f} | {g['est_agree']} | {g['std_agree']} | {g['mean_abs_diff']:.3f} | {extra} |")
    L += ["", "## Per trial (full ECG cohort)", "",
          "| Trial | Base PS | Arm | pairs | vars | % bal | mean |SMD| | HR (95% CI) |", "|---|---|---|---|---|---|---|---|"]
    for t in have:
        for kk, v in summ["per_trial"][t].items():
            base, arm = kk.split("|")
            L.append(f"| {NAMES.get(t, t)} | {base} | {arm} | {v['n_pairs']} | {v['n_vars']} | {v['pct_bal']} | {v['mean_smd']} | "
                     f"{v['hr']} ({v['lo']}–{v['hi']}) |")
    (OUT / "summary/tables.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main()
