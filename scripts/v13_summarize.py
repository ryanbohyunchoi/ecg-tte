#!/usr/bin/env python
"""v1.3 summaries and pre-specified decision rules (docs/PROTOCOL_V1_3_AMENDMENT.md). Aggregate markdown
to stdout and CSV tables to docs/v13/.

Usage: python v13_summarize.py [--set primary|extension|combined]
"""
import argparse
import itertools
import zlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import NCO_EXT, TRIALS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "v13"
LAB = {"unmatched": "M0 unadjusted", "sparse": "M1 sparse", "sparse+ECG": "M2 sparse+ECG", "hdPS200": "M3 hdPS200",
       "hdPS200+ECG": "M4 hdPS200+ECG", "clinical (reference)": "R clinical", "R+": "R+ physiology ref"}
CONTRASTS = [("C1", "sparse+ECG", "sparse"), ("C2", "hdPS200+ECG", "hdPS200")]
PLACEBO = [("sparse+noise32", "sparse"), ("sparse+shufECG", "sparse"), ("sparse+ECG", "sparse+shufECG"),
           ("hdPS200+noise32", "hdPS200"), ("hdPS200+shufECG", "hdPS200"), ("hdPS200+ECG", "hdPS200+shufECG")]
DOSE = ["sparse+ECG8", "sparse+ECG16", "sparse+ECG", "sparse+ECG64", "sparse+ECGpheno",
        "hdPS200+ECG8", "hdPS200+ECG16", "hdPS200+ECG", "hdPS200+ECG64", "hdPS200+ECGpheno"]


def md(df, floatfmt=3):
    d = df.copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda v: "–" if pd.isna(v) else f"{v:.{floatfmt}f}")
    cols = list(d.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join(lines)


def trials_for(which):
    P = list(PRIMARY)
    E = [n for n in EXTRA if (A / f"claude-{n}-V13EXT_DONE").exists()]
    return {"primary": P, "extension": E, "combined": P + E}[which]


def key_of(n):
    return {**PRIMARY, **EXTRA}[n][0]


# ---------------------------------------------------------------- plasmode
def plasmode(trials, rng):
    rows, per = [], {}
    for n in trials:
        f = A / "claude-v13-plasmode" / f"reps_{n}.csv"
        if not f.exists():
            continue
        R = pd.read_csv(f, keep_default_na=False, na_values=[""])  # scenario "null" must not parse as NaN
        Tr = pd.read_csv(A / "claude-v13-plasmode" / f"truth_{n}.csv", keep_default_na=False, na_values=[""])
        R = R.merge(Tr[["scenario", "arm", "truth_loghr"]], on=["scenario", "arm"])
        R["err"] = R.loghr - R.truth_loghr
        R["cover"] = (R.loghr - 1.96 * R.se <= R.truth_loghr) & (R.truth_loghr <= R.loghr + 1.96 * R.se)
        per[n] = R
        g = R.groupby(["scenario", "arm"])
        s = pd.DataFrame({"bias": g.err.mean(), "emp_sd": g.loghr.std(), "rmse": g.err.apply(lambda e: np.sqrt(np.mean(e ** 2))),
                          "coverage": g.cover.mean(), "reps": g.err.size()}).reset_index()
        s["trial"] = n
        rows.append(s)
    if not rows:
        return None, None
    S = pd.concat(rows)
    # contrasts: reduction in |bias| (and in RMSE), pooled = mean over trials; MC CI by resampling replicates
    res = []
    E = {(n, sc, arm): g.sort_values("rep").err.to_numpy() for n, R in per.items() for (sc, arm), g in R.groupby(["scenario", "arm"])}
    for scen in S.scenario.unique():
        for lab, a2, a1 in CONTRASTS + [(f"{a}-vs-{b}", a, b) for a, b in PLACEBO]:
            pairs = [(E[(n, scen, a1)], E[(n, scen, a2)]) for n in per if (n, scen, a1) in E and (n, scen, a2) in E]
            if not pairs:
                continue
            est = np.mean([abs(np.nanmean(e1)) - abs(np.nanmean(e2)) for e1, e2 in pairs])
            bs = []
            for _ in range(500):
                v = []
                for e1, e2 in pairs:
                    ix = rng.integers(0, len(e1), len(e1))
                    v.append(abs(np.nanmean(e1[ix])) - abs(np.nanmean(e2[ix])))
                bs.append(np.mean(v))
            base_abs = np.mean([abs(np.nanmean(e1)) for e1, _ in pairs])
            res.append(dict(scenario=scen, contrast=lab, arm=a2, vs=a1, trials=len(pairs), bias_reduction=est,
                            lo=np.nanpercentile(bs, 2.5), hi=np.nanpercentile(bs, 97.5),
                            relative_reduction=est / base_abs if base_abs > 0 else np.nan))
    return S, pd.DataFrame(res)


# ---------------------------------------------------------------- bootstrap
def bootstrap(trials, rng, targets=("RCT", "R", "R+"), arms_pairs=None, folder="claude-v13-bootstrap"):
    D = {}
    for n in trials:
        f = A / folder / f"bs_{n}.csv"
        if f.exists():
            D[n] = pd.read_csv(f).pivot_table(index="rep", columns="arm", values="loghr")
    if not D:
        return None, None
    pairs = arms_pairs or (CONTRASTS + [(f"{a}-vs-{b}", a, b) for a, b in PLACEBO] +
                           [(f"{a}-vs-{a.split('+')[0]}", a, a.split("+")[0]) for a in DOSE])
    per_trial, cross = [], []
    rct_draw = {n: (bench(key_of(n))) for n in D}
    for tgt in targets:
        for lab, a2, a1 in pairs:
            vals = {}
            for n, P in D.items():
                if a2 not in P or a1 not in P:
                    continue
                b, se = rct_draw[n]
                reps = P.index.to_numpy()
                if tgt == "RCT":
                    t = np.where(reps == 0, b, b + se * np.random.default_rng(zlib.crc32(n.encode())).normal(size=len(reps)))
                else:
                    col = "clinical (reference)" if tgt == "R" else "R+"
                    if col not in P:
                        continue
                    t = P[col].to_numpy()
                d = (P[a2].to_numpy() - t) ** 2 - (P[a1].to_numpy() - t) ** 2
                dl = P[a2].to_numpy() - P[a1].to_numpy()
                vals[n] = pd.DataFrame({"rep": reps, "d": d, "dlog": dl}).set_index("rep")
                bsd = vals[n].d.drop(index=0).dropna()
                per_trial.append(dict(target=tgt, contrast=lab, trial=n, d_point=vals[n].d.loc[0], d_lo=bsd.quantile(0.025),
                                      d_hi=bsd.quantile(0.975), dlog_point=vals[n].dlog.loc[0],
                                      p_ecg_closer=float((bsd < 0).mean())))
            if not vals:
                continue
            M = pd.concat({n: v.d for n, v in vals.items()}, axis=1)
            point = M.loc[0].mean()
            bs = M.drop(index=0).mean(axis=1)  # trials resampled independently (each has its own replicates)
            loo = [M.drop(columns=[c]).loc[0].mean() for c in M.columns]
            cross.append(dict(target=tgt, contrast=lab, arm=a2, vs=a1, trials=M.shape[1], mean_d_sqerr=point,
                              lo=bs.quantile(0.025), hi=bs.quantile(0.975), share_trials_closer=float((M.loc[0] < 0).mean()),
                              loo_min=min(loo), loo_max=max(loo)))
    return pd.DataFrame(per_trial), pd.DataFrame(cross)


# ---------------------------------------------------------------- multiverse
def multiverse(trials):
    D = [pd.read_csv(A / "claude-v13-multiverse" / f"mv_{n}.csv") for n in trials if (A / "claude-v13-multiverse" / f"mv_{n}.csv").exists()]
    if not D:
        return None, None
    D = pd.concat(D)
    D1 = D[D.imputation == 1].copy()
    # seed-independent arms are estimated once (seed 0) per model/estimator: broadcast to all seeds
    base = D1[D1.seed == 0]
    fill = []
    for s in range(1, 5):
        b = base[~base.arm.str.startswith("hdPS") & ~base.arm.str.contains("noise")].copy()
        b["seed"] = s
        fill.append(b)
    D1 = pd.concat([D1] + fill)
    D1["b_rct"] = D1.trial.map(lambda n: bench(key_of(n))[0])
    rp = D1[D1.arm == "R+"][["trial", "model", "seed", "estimator", "loghr"]].rename(columns={"loghr": "b_rplus"})
    D1 = D1.merge(rp, on=["trial", "model", "seed", "estimator"], how="left")
    D1["err_rct"] = (D1.loghr - D1.b_rct).abs()
    D1["err_rplus"] = (D1.loghr - D1.b_rplus).abs()
    D1["sq_rct"] = (D1.loghr - D1.b_rct) ** 2
    D1["sq_rplus"] = (D1.loghr - D1.b_rplus) ** 2
    spec = D1.groupby(["model", "seed", "estimator", "arm"])[["err_rct", "err_rplus", "sq_rct", "sq_rplus"]].mean().reset_index()
    rows = []
    for lab, a2, a1 in CONTRASTS + [(f"{a}-vs-{b}", a, b) for a, b in PLACEBO]:
        x = spec[spec.arm == a2].merge(spec[spec.arm == a1], on=["model", "seed", "estimator"], suffixes=("_2", "_1"))
        for tgt in ("rct", "rplus"):
            for metric in ("err", "sq"):
                dd = x[f"{metric}_{tgt}_2"] - x[f"{metric}_{tgt}_1"]
                base = x[(x.model == "l2_C1") & (x.seed == 0) & (x.estimator == "match_cal0.2_1to1")]
                rows.append(dict(contrast=lab, target=tgt, metric="mean_abs" if metric == "err" else "mean_sq", specs=len(dd),
                                 share_favouring=float((dd < 0).mean()), median_diff=dd.median(), q10=dd.quantile(0.1),
                                 q90=dd.quantile(0.9), base_spec_diff=float((base[f"{metric}_{tgt}_2"] - base[f"{metric}_{tgt}_1"]).iloc[0])
                                 if len(base) else np.nan))
    return spec, pd.DataFrame(rows)


# ---------------------------------------------------------------- design / NCO calibration
def design(trials):
    D = [pd.read_csv(A / "claude-v13-design" / f"design_{n}.csv") for n in trials if (A / "claude-v13-design" / f"design_{n}.csv").exists()]
    return pd.concat(D) if D else None


def fit_syserr(b, se):
    b, se = np.asarray(b, float), np.asarray(se, float)
    ok = ~np.isnan(b) & ~np.isnan(se)
    b, se = b[ok], se[ok]
    if len(b) < 3:
        return np.nan, np.nan, len(b)
    nll = lambda p: -np.sum(norm.logpdf(b, p[0], np.sqrt(np.exp(2 * p[1]) + se ** 2)))
    r = minimize(nll, [0.0, np.log(0.1)], method="Nelder-Mead")
    return float(r.x[0]), float(np.exp(r.x[1])), len(b)


def agreement(df, bcol="loghr", secol="se"):
    """df rows: trial, arm, loghr, se. Returns per-arm agreement metrics vs RCT."""
    out = []
    for arm, g in df.groupby("arm"):
        g = g.dropna(subset=[bcol, secol])
        if g.empty:
            continue
        b = g[bcol].to_numpy()
        se = g[secol].to_numpy()
        br = np.array([bench(key_of(n))[0] for n in g.trial])
        sr = np.array([bench(key_of(n))[1] for n in g.trial])
        from trial_specs import PUBLISHED
        lo_r = np.array([np.log(min(PUBLISHED[key_of(n)]["ci"]) if abs(PUBLISHED[key_of(n)]["our_orientation"] - PUBLISHED[key_of(n)]["hr"]) < 1e-6
                                else 1 / max(PUBLISHED[key_of(n)]["ci"])) for n in g.trial])
        hi_r = np.array([np.log(max(PUBLISHED[key_of(n)]["ci"]) if abs(PUBLISHED[key_of(n)]["our_orientation"] - PUBLISHED[key_of(n)]["hr"]) < 1e-6
                                else 1 / min(PUBLISHED[key_of(n)]["ci"])) for n in g.trial])
        z = (b - br) / np.sqrt(se ** 2 + sr ** 2)
        d, v = b - br, se ** 2 + sr ** 2
        w = 1 / v
        mu_f = np.sum(w * d) / np.sum(w)
        Q = np.sum(w * (d - mu_f) ** 2)
        C = np.sum(w) - np.sum(w ** 2) / np.sum(w)
        tau2 = max(0.0, (Q - (len(d) - 1)) / C) if C > 0 else 0.0
        out.append(dict(arm=arm, trials=len(g), mean_abs_dlog=np.mean(np.abs(d)), estimate_agreement=int(np.sum((b >= lo_r) & (b <= hi_r))),
                        std_diff_agreement=int(np.sum(np.abs(z) < 1.96)), mean_abs_z=np.mean(np.abs(z)), tau=np.sqrt(tau2),
                        coverage=float(np.mean((b - 1.96 * se <= br) & (br <= b + 1.96 * se)))))
    return pd.DataFrame(out)


def sign_flip(d):
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    obs = d.mean()
    flips = np.array(list(itertools.product([-1, 1], repeat=len(d)))) if len(d) <= 16 else \
        np.random.default_rng(0).choice([-1, 1], size=(20000, len(d)))
    null = (flips * np.abs(d)).mean(1)
    return float(obs), float(np.mean(np.abs(null) >= abs(obs) - 1e-12))


def evalue(hr_ratio):
    rr = hr_ratio if hr_ratio >= 1 else 1 / hr_ratio
    return rr + np.sqrt(rr * (rr - 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="primary", choices=["primary", "extension", "combined"])
    a = ap.parse_args()
    trials = trials_for(a.set)
    OUT.mkdir(parents=True, exist_ok=True)
    tag = a.set
    rng = np.random.default_rng(20260925)
    print(f"# v1.3 exploratory robustness program — trial set: {tag} ({len(trials)} trials)\n")
    print("Trials: " + ", ".join(trials) + "\n")
    print("All analyses are exploratory (registered 2026-09-25 after phase 2; tag protocol-v1.3).\n")
    rules = {}

    # I1 plasmode
    S, C = plasmode(trials, rng)
    if S is not None:
        S.to_csv(OUT / f"plasmode_by_trial_{tag}.csv", index=False)
        C.to_csv(OUT / f"plasmode_contrasts_{tag}.csv", index=False)
        print("## I1 Plasmode simulation\n")
        P = S.groupby(["scenario", "arm"]).agg(trials=("trial", "nunique"), mean_bias=("bias", "mean"),
                                               mean_abs_bias=("bias", lambda x: np.mean(np.abs(x))), mean_rmse=("rmse", "mean"),
                                               mean_coverage=("coverage", "mean")).reset_index()
        P.to_csv(OUT / f"plasmode_pooled_{tag}.csv", index=False)
        for scen in ["base", "phys_only", "strong", "none", "null"]:
            x = P[(P.scenario == scen) & P.arm.isin(LAB)].copy()
            x["arm"] = x.arm.map(LAB)
            print(f"**Scenario {scen}** (true conditional HR {'1.0' if scen == 'null' else '0.8'}; bias vs the arm's marginal truth; log-HR scale)\n")
            print(md(x.drop(columns="scenario")) + "\n")
        c = C[C.contrast.isin(["C1", "C2"]) | C.contrast.str.contains("vs")].copy()
        print("Reduction in |bias| (positive = the first arm is less biased), mean over trials, Monte Carlo 95% CI:\n")
        print(md(c[["scenario", "contrast", "trials", "bias_reduction", "lo", "hi", "relative_reduction"]]) + "\n")
        for cn in ("C1", "C2"):
            r = C[(C.scenario == "base") & (C.contrast == cn)].iloc[0]
            rules[f"{cn} rule 1 (plasmode base: bias-reduction CI excludes 0, > 0)"] = bool(r.lo > 0)
            r = C[(C.scenario == "phys_only") & (C.contrast == cn)].iloc[0]
            rules[f"{cn} rule 1b (plasmode phys_only, supportive)"] = bool(r.lo > 0)
            a2 = dict(C1="sparse+ECG", C2="hdPS200+ECG")[cn]
            r = C[(C.scenario == "base") & (C.contrast == f"{a2}-vs-{a2.split('+')[0]}+shufECG")].iloc[0]
            rules[f"{cn} rule 3 (plasmode base: less biased than shuffled-ECG placebo)"] = bool(r.lo > 0)

    # I3/I4/I5 bootstrap
    PT, CR = bootstrap(trials, rng)
    if CR is not None:
        PT.to_csv(OUT / f"bootstrap_by_trial_{tag}.csv", index=False)
        CR.to_csv(OUT / f"bootstrap_cross_{tag}.csv", index=False)
        print("## I3 Within-trial paired bootstrap (200 replicates per trial)\n")
        print("Mean over trials of err(arm)² − err(comparator)² (negative = the first arm is closer to the target); "
              "95% CI across bootstrap replicates; leave-one-trial-out range of the point estimate.\n")
        print(md(CR[["target", "contrast", "trials", "mean_d_sqerr", "lo", "hi", "share_trials_closer", "loo_min", "loo_max"]], 4) + "\n")
        for cn in ("C1", "C2"):
            for tgt in ("RCT", "R+"):
                r = CR[(CR.target == tgt) & (CR.contrast == cn)]
                if len(r):
                    rules[f"{cn} rule 2 (bootstrap vs {tgt}: CI < 0)"] = bool(r.iloc[0].hi < 0)
            # rule 3: ECG beats placebo (real ECG closer than shuffled ECG vs R+ and RCT)
            a2 = dict(C1="sparse+ECG", C2="hdPS200+ECG")[cn]
            r = CR[(CR.target == "R+") & (CR.contrast == f"{a2}-vs-{a2.split('+')[0]}+shufECG")]
            if len(r):
                rules[f"{cn} rule 3 (beats shuffled-ECG placebo vs R+: CI < 0)"] = bool(r.iloc[0].hi < 0)
            r = CR[(CR.target == "R+") & (CR.contrast == cn)]
            if len(r):
                rules[f"{cn} rule 4b (leave-one-out: sign holds in every set vs R+)"] = bool(r.iloc[0].loo_max < 0)

    # I5 supervised SHD logits and second encoder (SHD-scored cohort)
    pairs5 = [("C1", "sparse+ECG", "sparse"), ("C2", "hdPS200+ECG", "hdPS200"), ("sparse+SHD-vs-sparse", "sparse+SHD", "sparse"),
              ("sparse+ENC2-vs-sparse", "sparse+ENC2", "sparse"), ("hdPS200+SHD-vs-hdPS200", "hdPS200+SHD", "hdPS200"),
              ("hdPS200+ENC2-vs-hdPS200", "hdPS200+ENC2", "hdPS200")]
    PT5, CR5 = bootstrap(trials, rng, arms_pairs=pairs5, folder="claude-v13-bootstrap-shd")
    if CR5 is not None:
        CR5.to_csv(OUT / f"bootstrap_shd_enc2_cross_{tag}.csv", index=False)
        PT5.to_csv(OUT / f"bootstrap_shd_enc2_by_trial_{tag}.csv", index=False)
        print("## I5 Supervised SHD logits and second ECG encoder (PRESENT-SHD LVEF<40 CNN penultimate layer, 32 PCs); SHD-scored cohort\n")
        print(md(CR5[["target", "contrast", "trials", "mean_d_sqerr", "lo", "hi", "share_trials_closer", "loo_min", "loo_max"]], 4) + "\n")

    # I6 multiverse
    SP, MV = multiverse(trials)
    if MV is not None:
        SP.to_csv(OUT / f"multiverse_specs_{tag}.csv", index=False)
        MV.to_csv(OUT / f"multiverse_summary_{tag}.csv", index=False)
        print("## I6 Multiverse (4 PS models × 5 hdPS split seeds × 10 estimators = 200 specifications; imputation 1)\n")
        print("Per specification: mean over trials of |log HR − target|; difference first arm − comparator (negative favours the first arm).\n")
        print(md(MV, 4) + "\n")
        for cn in ("C1", "C2"):
            for tgt in ("rct", "rplus"):
                for metric in ("mean_abs", "mean_sq"):
                    r = MV[(MV.contrast == cn) & (MV.target == tgt) & (MV.metric == metric)].iloc[0]
                    rules[f"{cn} rule 4a (multiverse vs {tgt}, {metric}: >= 80% of specifications favour ECG)"] = bool(r.share_favouring >= 0.8)

    # phase-2 primary estimates (frozen) for permutation, E-values, LOO
    ph = []
    for n in trials:
        f = A / f"claude-phase2-all-{n}.csv"
        if f.exists():
            d = pd.read_csv(f)
            d = d[(d.outcome == "primary") & (d.horizon == "trial") & (d.analysis == "matched")]
            d["trial"] = n
            ph.append(d)
    ph = pd.concat(ph) if ph else None
    if ph is not None:
        print("## I7 Exact sign-flip permutation (frozen phase-2 estimates vs RCT) and leave-one-trial-out\n")
        rows = []
        X = ph.pivot_table(index="trial", columns="method", values="loghr")
        br = pd.Series({n: bench(key_of(n))[0] for n in X.index})
        for lab, a2, a1 in CONTRASTS:
            d = (X[a2] - br) ** 2 - (X[a1] - br) ** 2
            obs, p = sign_flip(d)
            loo = [d.drop(i).mean() for i in d.index]
            rows.append(dict(contrast=lab, trials=int(d.notna().sum()), mean_d_sqerr=obs, p_signflip=p, loo_min=min(loo), loo_max=max(loo),
                             trials_ecg_closer=int((d < 0).sum())))
        print(md(pd.DataFrame(rows), 4) + "\n")
        if S is not None:  # detectability: plasmode-expected gain vs between-trial noise of the paired |Δ| difference
            print("**Detectability.** Trials needed to detect the plasmode-expected reduction in |log HR − RCT| (paired t, "
                  "two-sided α = 0.05, 80% power), using the between-trial SD of the frozen phase-2 paired differences:\n")
            dr = []
            for lab, a2, a1 in CONTRASTS:
                dabs = ((X[a2] - br).abs() - (X[a1] - br).abs()).dropna()
                for scen in ("base", "phys_only", "strong"):
                    dl = C[(C.scenario == scen) & (C.contrast == lab)].bias_reduction.iloc[0]
                    k = ((1.96 + 0.84) * dabs.std(ddof=1) / dl) ** 2 if dl > 0 else np.inf
                    dr.append(dict(contrast=lab, scenario=scen, expected_gain=dl, sd_paired_abs_diff=dabs.std(ddof=1), trials_needed=np.ceil(k)))
            print(md(pd.DataFrame(dr), 3) + "\n")
        print("## I9 E-values for the disagreement with the RCT (HR ratio; rare-outcome approximation)\n")
        ev = []
        for arm in LAB:
            if arm not in X or arm == "R+":
                continue
            e = [evalue(np.exp(X.loc[n, arm] - br[n])) for n in X.index if not np.isnan(X.loc[n, arm])]
            ev.append(dict(arm=LAB[arm], median_evalue=np.median(e), max_evalue=np.max(e)))
        print(md(pd.DataFrame(ev), 2) + "\n")

    # Part II and I8
    Dg = design(trials)
    if Dg is not None:
        Dg.to_csv(OUT / f"design_all_{tag}.csv", index=False)
        print("## Part II: closer to the trial (agreement with the RCT per analysis)\n")
        if ph is not None:  # validation: design 'primary' must reproduce phase 2
            v = Dg[Dg.analysis == "primary"].merge(ph.rename(columns={"method": "arm"})[["trial", "arm", "loghr"]], on=["trial", "arm"],
                                                   suffixes=("", "_p2"))
            print(f"Validation: max |log HR(design primary) − log HR(phase 2)| = {np.nanmax(np.abs(v.loghr - v.loghr_p2)):.2e} over {len(v)} arm-trials.\n")
        rows = []
        for an in ["primary", "strict", "transport", "transport_ess20", "pp_naive_365", "pp_ipcw_365", "pp_ipcw_180", "pp_ipcw_730",
                   "pp_naive_switch", "pp_ipcw_switch", "runin90"]:
            sub = Dg[Dg.analysis == an]
            if sub.empty:
                continue
            ag = agreement(sub)
            ag.insert(0, "analysis", an)
            rows.append(ag)
        AG = pd.concat(rows)
        AG["arm"] = AG.arm.map(LAB).fillna(AG.arm)
        AG.to_csv(OUT / f"design_agreement_{tag}.csv", index=False)
        print(md(AG, 3) + "\n")
        # I8 calibration
        print("## I8 Empirical calibration with expanded negative controls\n")
        N = Dg[Dg.analysis.isin(NCO_EXT.keys())].copy()
        N["ev"] = pd.to_numeric(N.events, errors="coerce")
        N = N[N.ev >= 11]
        cal, sysr = [], []
        for arm in N.arm.unique():
            pooled = fit_syserr(N[N.arm == arm].loghr, N[N.arm == arm].se)
            for n in trials:
                g = N[(N.arm == arm) & (N.trial == n)]
                mu, sd, k = fit_syserr(g.loghr, g.se)
                src = "trial"
                if k < 8 or np.isnan(mu):
                    mu, sd, k, src = pooled[0], pooled[1], pooled[2], "pooled"
                sysr.append(dict(arm=arm, trial=n, mu=mu, sigma=sd, nco_used=k, source=src))
                p = Dg[(Dg.arm == arm) & (Dg.trial == n) & (Dg.analysis == "primary")]
                if len(p):
                    cal.append(dict(trial=n, arm=arm, loghr=p.loghr.iloc[0] - mu, se=np.sqrt(p.se.iloc[0] ** 2 + sd ** 2)))
        SY = pd.DataFrame(sysr)
        SY.to_csv(OUT / f"nco_systematic_error_{tag}.csv", index=False)
        s = SY.groupby("arm").agg(mean_mu=("mu", "mean"), mean_abs_mu=("mu", lambda x: np.mean(np.abs(x))), mean_sigma=("sigma", "mean"),
                                  median_nco=("nco_used", "median")).reset_index()
        s["arm"] = s.arm.map(LAB).fillna(s.arm)
        print("Systematic error estimated from negative controls (per trial, pooled across trials if < 8 usable NCOs):\n")
        print(md(s, 3) + "\n")
        for lab, a2, a1 in CONTRASTS:
            x = SY[SY.arm == a2].set_index("trial").sigma - SY[SY.arm == a1].set_index("trial").sigma
            y = SY[SY.arm == a2].set_index("trial").mu.abs() - SY[SY.arm == a1].set_index("trial").mu.abs()
            o1, p1 = sign_flip(x.dropna())
            o2, p2 = sign_flip(y.dropna())
            print(f"- {lab} ({LAB[a2]} − {LAB[a1]}): mean Δσ = {o1:+.3f} (sign-flip p = {p1:.3f}); mean Δ|μ| = {o2:+.3f} (p = {p2:.3f})")
        CA = agreement(pd.DataFrame(cal))
        CA["arm"] = CA.arm.map(LAB).fillna(CA.arm)
        CA.to_csv(OUT / f"calibrated_agreement_{tag}.csv", index=False)
        print("\nAgreement with the RCT after empirical calibration of the primary estimates:\n")
        print(md(CA, 3) + "\n")

    print("## Pre-specified decision rules\n")
    for k, v in rules.items():
        print(f"- {k}: **{'met' if v else 'not met'}**")
    pd.Series(rules).to_csv(OUT / f"decision_rules_{tag}.csv")


if __name__ == "__main__":
    main()
