#!/usr/bin/env python
"""v1.5 aggregate summary across external trial directories (docs/PROTOCOL_V1_5_EXTERNAL.md).

Reads <trial dir>/analysis/{estimates,balance,plasmode_reps,plasmode_truth}.csv and rct.json written by
v15_analyze.py. Benchmark = rct.json our_orientation (log scale); its SE is derived from the reported CI
(inverted when our orientation is the reciprocal of the reported HR) and ci_level.

Per arm: RCT-DUPLICATE panel (v14_panel cat / kappa / dl): significance, estimate and standardised-
difference agreement; Pearson r (descriptive; >= 3 trials); ratio of ratios (DerSimonian-Laird pooled
exp(log HR_emul - log HR_RCT)); Heyard dispersion phi = Q/(k-1); mean |Δlog HR|.
rct.json our_lo/our_hi, when present, are used directly as the benchmark CI.
Feasibility rule 2 (>= 150 clinical-PS pairs) reported per trial in the status table.
Paired contrasts per trial: Δ|log HR - RCT| and Δ precision-standardised z^2 = Δ^2/(s^2 + s_RCT^2);
exact sign-flip test across trials (v13_summarize.sign_flip; descriptive with few trials).
Plasmode: bias = mean replicate log HR - arm truth; Monte Carlo 95% CIs by resampling replicates
(paired across arms for the bias reductions |bias_A| - |bias_B|). Balance: capture % on labs/vitals.

  python v15_summarize.py --cohort {mimic,ukb,all} [--glob PATTERN] [--out-dir DIR]
Markdown to stdout; CSVs to docs/v15/ (prefix = cohort).
"""
import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scipy.stats import binomtest  # noqa: E402
from v13_common import EXTRA, PRIMARY  # noqa: E402
from v13_common import bench as yale_bench  # noqa: E402
from v13_summarize import fit_syserr, md, sign_flip  # noqa: E402

EXACT_MAX = 20  # v13_summarize.sign_flip enumerates all 2^n sign patterns up to n = 20, else 20,000 MC draws (seed 0)


def sf(d):
    """(mean, p, method label) of the paired sign-flip test on d."""
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    if not len(d):
        return np.nan, np.nan, ""
    o, p = sign_flip(d)
    return o, p, ("exact" if len(d) <= EXACT_MAX else "MC 20k (seed 0)")
from v14_panel import cat, dl, kappa  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = Path(__file__).resolve().parent.parent.parent / "docs" / "v15"
FULL_ARMS = ["unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "ECGonly", "clinical"]
SUB = " [clmbr-subset]"
SUB_ARMS = [a + SUB for a in ("unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG")] + \
    ["CLMBR", "sparse+CLMBR", "sparse+CLMBR+ECG", "hdPS200+CLMBR"]
ARMS = FULL_ARMS + SUB_ARMS
# CLMBR contrasts are like-for-like: both arms in the CLMBR subset (UKB only)
CMP = [("C1", "sparse+ECG", "sparse"), ("C2", "hdPS200+ECG", "hdPS200"), ("ECGonly", "ECGonly", "unmatched"),
       ("C1 [sub]", "sparse+ECG" + SUB, "sparse" + SUB), ("C2 [sub]", "hdPS200+ECG" + SUB, "hdPS200" + SUB),
       ("CLMBR vs unmatched [sub]", "CLMBR", "unmatched" + SUB), ("sparse+CLMBR vs sparse [sub]", "sparse+CLMBR", "sparse" + SUB),
       ("sparse+CLMBR+ECG vs sparse+CLMBR", "sparse+CLMBR+ECG", "sparse+CLMBR"),
       ("sparse+CLMBR+ECG vs sparse+ECG [sub]", "sparse+CLMBR+ECG", "sparse+ECG" + SUB),
       ("hdPS200+CLMBR vs hdPS200 [sub]", "hdPS200+CLMBR", "hdPS200" + SUB)]
B_MC = 2000


def bench(r):
    o, hr, lo, hi = float(r["our_orientation"]), float(r["hr"]), float(r["lo"]), float(r["hi"])
    if r.get("our_lo") is not None and r.get("our_hi") is not None:  # benchmark CI already in our orientation
        lo, hi = float(r["our_lo"]), float(r["our_hi"])
    elif abs(o - hr) > 1e-6:
        lo, hi = 1 / hi, 1 / lo
    z = norm.ppf(0.5 + float(r.get("ci_level") or 0.95) / 2)
    return np.log(o), (np.log(hi) - np.log(lo)) / (2 * z)


def load(pattern, sub="analysis"):
    import re
    dirs = sorted(Path(p) for p in glob.glob(pattern)
                  if Path(p).is_dir() and ((Path(p) / "rct.json").exists() or (Path(p) / "READY_COHORT").exists()))  # trial dirs only
    status, E, BAL, PR, PT, SEC, NC = [], [], [], [], [], [], []
    for d in dirs:
        marks = [m for m in ("READY_COHORT", "READY_ECG", "READY_OUTCOMES", "READY_INFEASIBLE") if (d / m).exists() or (m == "READY_INFEASIBLE" and (d / "INFEASIBLE").exists())]
        an = d / sub
        done = (an / "estimates.csv").exists()
        status.append(dict(trial=re.sub(r"^claude-v15s?-", "", d.name), markers=",".join(m.split("_")[1].lower() for m in marks),
                           analysed=done, plasmode=(an / "plasmode_reps.csv").exists()))
        if not done:
            continue
        name = re.sub(r"^claude-v15s?-", "", d.name)
        r = json.load(open(d / "rct.json"))
        rb, rs = bench(r)
        e0 = pd.read_csv(an / "estimates.csv")
        e = e0[e0.outcome == "primary"].assign(trial=name, rb=rb, rs=rs, rct=r.get("trial"), key=r.get("key"))
        E.append(e)
        n = e0[e0.outcome.astype(str).str.startswith("nco_")].copy()
        if len(n):
            if "nco_usable" in n and n.nco_usable.notna().any():
                n["usable"] = n.nco_usable.astype(str).str.lower().isin(["true", "1", "1.0"])
            else:  # older rows: total events >= 11 derived from the suppressed counts (conservative)
                ev = lambda v: np.nan if str(v).startswith("<") else float(v)
                et, ec = n.events_treated.map(ev), n.events_control.map(ev)
                n["usable"] = (et.fillna(0) + ec.fillna(0)) >= 11
            n["usable"] &= n.loghr.notna() & n.se.notna()
            NC.append(n.assign(trial=name, cohort=name.split("-")[0]))
        for sb in r.get("secondary", []) or []:
            tc = str(sb.get("outcome_columns", "")).split("/")[0]
            g = e0[e0.outcome == f"sec_{tc[6:]}"]
            if tc.startswith("t_sec_") and len(g):
                b2, s2 = bench(sb)
                SEC.append(g.assign(trial=name, benchmark=sb.get("key"), endpoint=sb.get("endpoint"), rb=b2, rs=s2))
        mf = an / "meta.json"
        if mf.exists():
            status[-1]["n_clmbr_subset"] = json.load(open(mf)).get("n_clmbr_subset")
        if (an / "balance.csv").exists():
            BAL.append(pd.read_csv(an / "balance.csv").assign(trial=name))
        if (an / "plasmode_reps.csv").exists():
            p = pd.read_csv(an / "plasmode_reps.csv")
            if len(p):
                PR.append(p.assign(trial=name))
                PT.append(pd.read_csv(an / "plasmode_truth.csv").assign(trial=name))
    cc = lambda L: pd.concat(L, ignore_index=True) if L else pd.DataFrame()
    return pd.DataFrame(status), cc(E), cc(BAL), cc(PR), cc(PT), cc(SEC), cc(NC)


def panel(E):
    out = []
    for a in ARMS:
        g = E[E.arm == a].dropna(subset=["loghr", "se"])
        k = len(g)
        if not k:
            continue
        b, s, rb, rs = g.loghr.to_numpy(), g.se.to_numpy(), g.rb.to_numpy(), g.rs.to_numpy()
        ce, cr = cat(b, s), cat(rb, rs)
        z = (b - rb) / np.sqrt(s ** 2 + rs ** 2)
        mu, se, Q, I2 = dl(b - rb, s ** 2 + rs ** 2)
        out.append(dict(arm=a, trials=k, significance_agreement=np.mean(np.where(cr != 0, ce == cr, ce == 0)),
                        estimate_agreement=np.mean(np.abs(b - rb) <= 1.96 * rs), std_diff_agreement=np.mean(np.abs(z) < 1.96),
                        pearson_r=np.corrcoef(b, rb)[0, 1] if k >= 3 else np.nan, kappa=kappa(ce, cr) if k >= 2 else np.nan,
                        ratio_of_ratios=np.exp(mu), ror_lo=np.exp(mu - 1.96 * se), ror_hi=np.exp(mu + 1.96 * se),
                        I2=I2 if k >= 2 else np.nan, dispersion_phi=Q / (k - 1) if k >= 2 else np.nan, mean_abs_dlog=np.mean(np.abs(b - rb))))
    return pd.DataFrame(out)


def hr_table(E, arms=ARMS):
    f = lambda r: "–" if pd.isna(r.loghr) else f"{r.hr:.2f} ({r.lo:.2f}–{r.hi:.2f})"
    rows = []
    for tr, g in E.groupby("trial", sort=True):
        g = g.set_index("arm")
        rb, rs = g.rb.iloc[0], g.rs.iloc[0]
        row = dict(trial=tr, rct=f"{np.exp(rb):.2f} ({np.exp(rb - 1.96 * rs):.2f}–{np.exp(rb + 1.96 * rs):.2f})",
                   N=int(g.loc["unmatched", "n_treated"] + g.loc["unmatched", "n_control"]) if "unmatched" in g.index else np.nan)
        for a in arms:
            if a in g.index:
                row[a] = f(g.loc[a]) + ("" if pd.isna(g.loc[a, "pairs"]) else f" [{int(g.loc[a, 'pairs'])}]")
        rows.append(row)
    return pd.DataFrame(rows)


def contrasts(E):
    per, agg = [], []
    for lab, a2, a1 in CMP:
        x = E[E.arm == a2].set_index("trial")
        y = E[E.arm == a1].set_index("trial")
        tt = x.index.intersection(y.index)
        if not len(tt):
            continue
        x, y = x.loc[tt], y.loc[tt]
        dabs = (x.loghr - x.rb).abs() - (y.loghr - y.rb).abs()
        dz2 = (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2) - (y.loghr - y.rb) ** 2 / (y.se ** 2 + y.rs ** 2)
        for t in tt:
            per.append(dict(contrast=lab, first=a2, second=a1, trial=t, d_abs=dabs[t], d_z2=dz2[t],
                            abs_first=abs(x.loghr[t] - x.rb[t]), abs_second=abs(y.loghr[t] - y.rb[t])))
        ok = dabs.notna() & dz2.notna()
        o1, p1, m1 = sf(dabs[ok])
        o2, p2, _ = sf(dz2[ok])
        agg.append(dict(contrast=lab, first=a2, second=a1, trials=int(ok.sum()), closer=f"{int((dabs[ok] < 0).sum())}/{int(ok.sum())}",
                        mean_d_abs=o1, p_signflip_abs=p1, mean_d_z2=o2, p_signflip_z2=p2, signflip=m1))
    return pd.DataFrame(per), pd.DataFrame(agg)


def plasmode(PR, PT):
    if PR.empty:
        return pd.DataFrame(), pd.DataFrame()
    rng = np.random.default_rng(0)
    bias_rows, red_rows = [], []
    boots = {}
    for (tr, sc), g in PR.groupby(["trial", "scenario"]):
        W = g.pivot_table(index="rep", columns="arm", values="loghr")
        S = g.pivot_table(index="rep", columns="arm", values="se")
        truth = PT[(PT.trial == tr) & (PT.scenario == sc)].set_index("arm").truth_loghr
        reps = W.index.to_numpy()
        bi = rng.integers(0, len(reps), size=(B_MC, len(reps)))
        bb = {}
        for a in [x for x in ARMS if x in W]:
            v = W[a].to_numpy()
            ok = ~np.isnan(v)
            bias = np.nanmean(v) - truth[a]
            bs = np.nanmean(v[bi], axis=1) - truth[a]
            bb[a] = bs
            cover = np.nanmean(np.abs(v - truth[a]) <= 1.96 * S[a].to_numpy())
            bias_rows.append(dict(trial=tr, scenario=sc, arm=a, reps=int(ok.sum()), truth=truth[a], mean_loghr=np.nanmean(v), bias=bias,
                                  bias_lo=np.quantile(bs, 0.025), bias_hi=np.quantile(bs, 0.975), emp_sd=np.nanstd(v, ddof=1),
                                  rmse=np.sqrt(np.nanmean((v - truth[a]) ** 2)), coverage=cover,
                                  mean_pairs=g[g.arm == a].pairs.mean()))
        boots[(tr, sc)] = (bb, {a: np.nanmean(W[a]) - truth[a] for a in bb})
        for lab, a2, a1 in CMP:
            if a2 in bb and a1 in bb:
                b2, b1 = boots[(tr, sc)][1][a2], boots[(tr, sc)][1][a1]
                d = np.abs(bb[a1]) - np.abs(bb[a2])
                red_rows.append(dict(trial=tr, scenario=sc, contrast=lab, first=a2, second=a1, bias_second=b1, bias_first=b2,
                                     abs_bias_reduction=abs(b1) - abs(b2), lo=np.quantile(d, 0.025), hi=np.quantile(d, 0.975),
                                     pct_reduction=100 * (1 - abs(b2) / abs(b1)) if abs(b1) > 0 else np.nan))
    # pooled across trials (mean of per-trial reductions; replicates resampled within trial)
    trials = sorted(PR.trial.unique())
    for sc in sorted(PR.scenario.unique()):
        for lab, a2, a1 in CMP:
            ks = [(t, sc) for t in trials if (t, sc) in boots and a2 in boots[(t, sc)][0] and a1 in boots[(t, sc)][0]]
            if len(ks) < 2:
                continue
            pt = np.mean([abs(boots[k][1][a1]) - abs(boots[k][1][a2]) for k in ks])
            bs = np.mean([np.abs(boots[k][0][a1]) - np.abs(boots[k][0][a2]) for k in ks], axis=0)
            red_rows.append(dict(trial=f"pooled ({len(ks)}; mean |bias|)", scenario=sc, contrast=lab, first=a2, second=a1,
                                 bias_second=np.mean([abs(boots[k][1][a1]) for k in ks]), bias_first=np.mean([abs(boots[k][1][a2]) for k in ks]),
                                 abs_bias_reduction=pt, lo=np.quantile(bs, 0.025), hi=np.quantile(bs, 0.975), pct_reduction=np.nan))
    return pd.DataFrame(bias_rows), pd.DataFrame(red_rows)


POOL_CMP = [("C1", "sparse+ECG", "sparse"), ("C2", "hdPS200+ECG", "hdPS200"), ("ECGonly", "ECGonly", "unmatched")]


def yale_rows():
    """Yale phase-2 point estimates (imputation 1, bootstrap rep 0) for the 18 v1.3/v1.4 trials, v13_common.bench."""
    rows = []
    for n, (k, _) in {**PRIMARY, **EXTRA}.items():
        fs = [A / "claude-v13-bootstrap" / f"bs_{n}.csv", A / "claude-v14-ecgonly" / f"bs_{n}.csv"]
        if not fs[0].exists():
            continue
        d = pd.concat([pd.read_csv(f) for f in fs if f.exists()])
        d = d[d.rep == 0].drop_duplicates("arm").set_index("arm").rename(index={"clinical (reference)": "clinical"})
        rb, rs = yale_bench(k)
        for a in ("unmatched", "sparse", "sparse+ECG", "hdPS200", "hdPS200+ECG", "ECGonly", "clinical"):
            if a in d.index:
                rows.append(dict(source="yale", trial=f"yale-{n}", key=k, arm=a, loghr=d.loc[a, "loghr"], se=d.loc[a, "se"], rb=rb, rs=rs))
    return pd.DataFrame(rows)


def pooled_rct(E):
    """Yale + external emulations; headline = RCT-clustered (mean paired difference within each RCT key, then
    sign-flip across RCTs); the per-emulation count is descriptive only (emulations share RCT benchmarks)."""
    Y = yale_rows()
    X = E[E.arm.isin(FULL_ARMS)].assign(source=lambda d: d.trial.str.split("-").str[0])[["source", "trial", "key", "arm", "loghr", "se", "rb", "rs"]]
    D = pd.concat([Y, X], ignore_index=True)
    per, head, desc, rep_ = [], [], [], []
    for lab, a2, a1 in POOL_CMP:
        x = D[D.arm == a2].set_index("trial")
        y = D[D.arm == a1].set_index("trial")
        tt = x.index.intersection(y.index)
        x, y = x.loc[tt], y.loc[tt]
        g = pd.DataFrame({"source": x.source, "key": x.key,
                          "d_abs": (x.loghr - x.rb).abs() - (y.loghr - y.rb).abs(),
                          "d_z2": (x.loghr - x.rb) ** 2 / (x.se ** 2 + x.rs ** 2) - (y.loghr - y.rb) ** 2 / (y.se ** 2 + y.rs ** 2)}).dropna()
        per.append(g.assign(contrast=lab).reset_index())
        c = g.groupby("key").agg(d_abs=("d_abs", "mean"), d_z2=("d_z2", "mean"), emulations=("d_abs", "size"))
        o1, p1, m1 = sf(c.d_abs)
        o2, p2, m2 = sf(c.d_z2)
        k = int((c.d_abs < 0).sum())
        head.append(dict(contrast=lab, first=a2, second=a1, rcts=len(c), emulations=len(g), closer=f"{k}/{len(c)}",
                         p_sign=binomtest(k, len(c), 0.5).pvalue, mean_d_abs=o1, p_signflip_abs=p1, mean_d_z2=o2, p_signflip_z2=p2, signflip=m1))
        o1, p1, m1 = sf(g.d_abs)
        o2, p2, _ = sf(g.d_z2)
        k = int((g.d_abs < 0).sum())
        desc.append(dict(contrast=lab, emulations=len(g), closer=f"{k}/{len(g)}", p_sign=binomtest(k, len(g), 0.5).pvalue,
                         mean_d_abs=o1, p_signflip_abs=p1, mean_d_z2=o2, p_signflip_z2=p2, signflip=m1))
        for key, h in g.groupby("key"):
            yv, ev = h[h.source == "yale"], h[h.source != "yale"]
            if len(yv) and len(ev):
                for _, r in ev.iterrows():
                    rep_.append(dict(contrast=lab, key=key, external=r.name, yale_d_abs=yv.d_abs.iloc[0], external_d_abs=r.d_abs,
                                     same_direction=bool(np.sign(yv.d_abs.iloc[0]) == np.sign(r.d_abs))))
    return pd.concat(per, ignore_index=True), pd.DataFrame(head), pd.DataFrame(desc), pd.DataFrame(rep_)


def sensitivity(out):
    """MIMIC pre-audit (analysis_v1_preaudit) vs corrected (analysis); UKB main vs trial-eligibility (-elig), CV-death
    composite censored 2020-12-31 (-cvd) and both (-elig-cvd) variants (claude-v15s-ukb-<trial>-<variant>).
    Sensitivity variants never enter the main pooled analyses."""
    strip = lambda v: v.assign(trial=v.trial.str.replace(r"-(elig-cvd|elig|cvd)$", "", regex=True)) if len(v) else v
    sets = {"mimic pre-audit": load(str(A / "claude-v15-mimic-*"), "analysis_v1_preaudit")[1],
            "mimic corrected": load(str(A / "claude-v15-mimic-*"))[1],
            "ukb main": load(str(A / "claude-v15-ukb-*"))[1],
            "ukb elig": load(str(A / "claude-v15s-ukb-*-elig"))[1],
            "ukb cvd": load(str(A / "claude-v15s-ukb-*[a-z]-cvd"))[1],
            "ukb elig-cvd": load(str(A / "claude-v15s-ukb-*-elig-cvd"))[1]}
    if len(sets["ukb cvd"]):
        sets["ukb cvd"] = sets["ukb cvd"][~sets["ukb cvd"].trial.str.endswith("-elig-cvd")]
    for k, v in sets.items():
        if len(v):
            sets[k] = strip(v[v.arm.isin(FULL_ARMS + SUB_ARMS)])
    print("# v1.5 sensitivity analyses (post-audit; never pooled into the main analyses)\n")
    print("MIMIC: pre-audit specification (index-admission diagnoses in baseline/panel; no 28-day new-event rule) vs "
          "corrected primary (earlier-admission diagnoses; 28-day rule). UKB: main cohorts vs the trials' own eligibility "
          "criteria (elig), CV-death composites censored 2020-12-31 (cvd) and both (elig-cvd). The UKB ECG is an "
          "on-treatment covariate (recorded at the exposure-defining visit).\n")
    groups = [("mimic", ["mimic pre-audit", "mimic corrected"]), ("ukb", ["ukb main", "ukb elig", "ukb cvd", "ukb elig-cvd"])]
    f = lambda r: "–" if pd.isna(r.loghr) else f"{r.hr:.2f} ({r.lo:.2f}–{r.hi:.2f})" + ("" if pd.isna(r.pairs) else f" [{int(r.pairs)}]")
    allrows, crow = [], []
    for gname, vers in groups:
        av = [v for v in vers if len(sets[v])]
        missing = [v for v in vers if v not in av]
        if missing:
            print(f"({gname}: not available yet: {', '.join(missing)})\n")
        if len(av) < 2:
            continue
        L = pd.concat([sets[v][sets[v].arm.isin(FULL_ARMS)].assign(version=v) for v in av], ignore_index=True)
        L["cell"] = L.apply(f, axis=1)
        W = L.pivot_table(index=["trial", "arm"], columns="version", values="cell", aggfunc="first")[av].reset_index()
        W["arm"] = pd.Categorical(W.arm, FULL_ARMS)
        W = W.sort_values(["trial", "arm"])
        allrows.append(L.drop(columns=["cell"]))
        print(f"## HRs by version — {gname} (HR (95% CI) [pairs])\n")
        print(md(W, 3) + "\n")
        rows = []
        for v in av:
            S = sets[v]
            P = panel(S[S.arm.isin(FULL_ARMS)])
            Cp, Ca = contrasts(S)
            for _, r in Ca.iterrows():
                rows.append(dict(version=v, contrast=r.contrast, trials=r.trials, closer=r.closer, mean_d_abs=r.mean_d_abs,
                                 p_signflip_abs=r.p_signflip_abs, mean_d_z2=r.mean_d_z2, p_signflip_z2=r.p_signflip_z2))
            crow.append(Cp.assign(version=v))
            for _, r in P.iterrows():
                rows.append(dict(version=v, contrast=f"panel: {r.arm}", trials=r.trials, mean_d_abs=r.mean_abs_dlog,
                                 closer=f"est.agree {r.estimate_agreement:.2f}; phi {r.dispersion_phi:.2f}"))
        R = pd.DataFrame(rows)
        R.to_csv(out / f"sensitivity_{gname}_contrasts.csv", index=False)
        print(f"## Contrasts (mean Δ|log HR − RCT|, negative = first arm closer; exact sign-flip, descriptive) and panel — {gname}\n")
        print(md(R, 3) + "\n")
    if allrows:
        pd.concat(allrows).drop(columns=["trial_dir"], errors="ignore").to_csv(out / "sensitivity_hr_long.csv", index=False)
    if crow:
        pd.concat(crow).to_csv(out / "sensitivity_contrasts_by_trial.csv", index=False)


MIN_NCO_TRIAL = 6


def calibration(E, N):
    """OHDSI-style empirical calibration (v13_summarize.fit_syserr): b_i ~ N(mu, sigma^2 + se_i^2) over usable NCO
    estimates, per arm, pooled across the trials of each cohort, and per trial when >= MIN_NCO_TRIAL usable NCOs
    (else the cohort-pooled fit is used). Calibrated primary estimate: b - mu, SE sqrt(se^2 + sigma^2)."""
    N = N[N.usable]
    pooled, sysr, cal = [], [], []
    for (coh, a), g in N.groupby(["cohort", "arm"]):
        mu, sd, k = fit_syserr(g.loghr, g.se)
        pooled.append(dict(cohort=coh, arm=a, trials=g.trial.nunique(), nco_estimates=k, mu=mu, abs_mu=abs(mu), sigma=sd,
                           share_ci_excl_1=float(np.mean(np.abs(g.loghr) > 1.96 * g.se))))
    PO = pd.DataFrame(pooled)
    for (tr, a), p in E.groupby(["trial", "arm"]):
        coh = tr.split("-")[0]
        g = N[(N.trial == tr) & (N.arm == a)]
        mu, sd, k = fit_syserr(g.loghr, g.se) if len(g) >= MIN_NCO_TRIAL else (np.nan, np.nan, len(g))
        src = "trial"
        if np.isnan(mu):
            q = PO[(PO.cohort == coh) & (PO.arm == a)]
            mu, sd, src = (q.mu.iloc[0], q.sigma.iloc[0], "cohort-pooled") if len(q) else (np.nan, np.nan, "none")
        sysr.append(dict(trial=tr, cohort=coh, arm=a, nco_usable=len(g), source=src, mu=mu, sigma=sd,
                         share_ci_excl_1=float(np.mean(np.abs(g.loghr) > 1.96 * g.se)) if len(g) else np.nan))
        if not np.isnan(mu):
            r = p.iloc[0]
            b, se = r.loghr - mu, np.sqrt(r.se ** 2 + sd ** 2)
            cal.append(dict(trial=tr, arm=a, loghr=b, se=se, hr=np.exp(b), lo=np.exp(b - 1.96 * se), hi=np.exp(b + 1.96 * se),
                            pairs=r.pairs, rb=r.rb, rs=r.rs, calib_source=src))
    SY = pd.DataFrame(sysr)
    rows = []
    for lab, a2, a1 in CMP:
        x = SY[(SY.arm == a2) & (SY.source == "trial")].set_index("trial")
        y = SY[(SY.arm == a1) & (SY.source == "trial")].set_index("trial")
        tt = x.index.intersection(y.index)
        if not len(tt):
            continue
        dmu = x.mu.loc[tt].abs() - y.mu.loc[tt].abs()
        dsd = x.sigma.loc[tt] - y.sigma.loc[tt]
        rows.append(dict(contrast=lab, first=a2, second=a1, trials=len(tt), lower_abs_mu=f"{int((dmu < 0).sum())}/{len(tt)}",
                         mean_d_abs_mu=dmu.mean(), p_signflip_abs_mu=sf(dmu)[1],
                         mean_d_sigma=dsd.mean(), p_signflip_sigma=sf(dsd)[1], signflip=sf(dmu)[2]))
    return PO, SY, pd.DataFrame(rows), pd.DataFrame(cal)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cohort", choices=["mimic", "ukb", "all", "sensitivity"], required=True)
    ap.add_argument("--glob", default=None, help="override trial-dir glob (testing)")
    ap.add_argument("--out-dir", default=str(OUT))
    a = ap.parse_args()
    if a.cohort == "sensitivity":
        o = Path(a.out_dir)
        o.mkdir(parents=True, exist_ok=True)
        return sensitivity(o)
    pat = a.glob or str(A / f"claude-v15-{'*' if a.cohort == 'all' else a.cohort}-*")
    if a.cohort == "all" and not a.glob:
        pat = str(A / "claude-v15-[mu][ik][mb]*-*")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pre = a.cohort
    status, E, BAL, PR, PT, SEC, NC = load(pat)
    if a.cohort == "all" and not a.glob and len(status):
        status = status[status.trial.str.match(r"^(mimic|ukb)-")]
        keep = set(status.trial)
        E, BAL = (E[E.trial.isin(keep)] if len(E) else E), (BAL[BAL.trial.isin(keep)] if len(BAL) else BAL)
        PR, PT = (PR[PR.trial.isin(keep)] if len(PR) else PR), (PT[PT.trial.isin(keep)] if len(PT) else PT)
    print(f"# v1.5 external first pass — cohort: {a.cohort}\n")
    print("Exploratory (protocol v1.5). Benchmarks are rct.json our_orientation; SE from the reported CI. "
          "Pair counts in brackets. Event counts < 11 suppressed upstream. Aggregates only. Analysed N = the ECG-linked subset. "
          "UKB: prevalent users, and the ECG is an on-treatment covariate (recorded at the exposure-defining visit).\n")
    print("Engine validation (Yale LIFE, exact Yale design and population): unmatched, sparse, sparse+ECG, hdPS200, "
          "hdPS200+ECG and clinical log HRs reproduce Yale imputation-1 rep 0 to < 1e-15 (docs: compare_yale_exact.csv).\n")
    if len(E):
        cp = E[E.arm == "clinical"].set_index("trial").pairs
        status["clinical_pairs"] = status.trial.map(cp)
        status["pairs_rule_150"] = status.clinical_pairs.map(lambda v: "" if pd.isna(v) else ("pass" if v >= 150 else "FAIL"))
        U = E[E.arm == "unmatched"].set_index("trial")
        status["n_treated"] = status.trial.map(U.n_treated)
        status["n_control"] = status.trial.map(U.n_control)
        status["events_treated"] = status.trial.map(U.events_treated)
        status["events_control"] = status.trial.map(U.events_control)
        ev = lambda v: 0 if pd.isna(v) else (5 if str(v).startswith("<") else int(v))
        status["imprecise(<30 events/arm)"] = [("yes" if min(ev(a), ev(b)) < 30 else "") if not pd.isna(a) else ""
                                               for a, b in zip(status.events_treated, status.events_control)]
    print("## Trial directories\n")
    for c in ("clinical_pairs", "n_clmbr_subset", "n_treated", "n_control"):
        if c in status:
            status[c] = pd.to_numeric(status[c], errors="coerce").round().astype("Int64")
    print(md(status) if len(status) else "(none found)")
    status.to_csv(out / f"{pre}_status.csv", index=False)
    if E.empty:
        print("\nNo analysed trials yet.")
        return
    print("\n## Hazard ratios per trial (HR (95% CI) [pairs]) — full analysed cohort\n")
    H = hr_table(E, FULL_ARMS)
    H.to_csv(out / f"{pre}_hr_by_trial.csv", index=False)
    E.drop(columns=["trial_dir"], errors="ignore").to_csv(out / f"{pre}_estimates_long.csv", index=False)
    print(md(H) + "\n")
    if E.arm.isin(SUB_ARMS).any():
        print("## Hazard ratios — CLMBR subset (patients with a CLMBR embedding; like-for-like CLMBR comparisons)\n")
        H2 = hr_table(E[E.arm.isin(SUB_ARMS)], SUB_ARMS)
        H2.to_csv(out / f"{pre}_hr_by_trial_clmbr_subset.csv", index=False)
        print(md(H2.drop(columns=["N"])) + "\n")
    if len(SEC):
        S2 = SEC.assign(rct_hr=np.exp(SEC.rb), rct_lo=np.exp(SEC.rb - 1.96 * SEC.rs), rct_hi=np.exp(SEC.rb + 1.96 * SEC.rs),
                        d_log=SEC.loghr - SEC.rb, z=(SEC.loghr - SEC.rb) / np.sqrt(SEC.se ** 2 + SEC.rs ** 2))
        S2 = S2[["trial", "benchmark", "endpoint", "rct_hr", "rct_lo", "rct_hi", "arm", "hr", "lo", "hi", "pairs", "d_log", "z"]]
        S2.to_csv(out / f"{pre}_secondary_benchmarks.csv", index=False)
        print("## Secondary benchmarks (not in the panel or contrasts)\n")
        print(md(S2, 2) + "\n")
    P = panel(E)
    P.to_csv(out / f"{pre}_panel.csv", index=False)
    print("## RCT-DUPLICATE panel per arm\n")
    print("Pearson r descriptive only (>= 3 trials); phi = Heyard dispersion Q/(k-1) (1 = disagreement explained by sampling error).\n")
    print(md(P, 2) + "\n")
    Cp, Ca = contrasts(E)
    Cp.to_csv(out / f"{pre}_contrasts_by_trial.csv", index=False)
    Ca.to_csv(out / f"{pre}_contrasts.csv", index=False)
    print("## Paired contrasts (negative = first arm closer to the RCT)\n")
    print(md(Cp, 3) + "\n")
    print("Across trials (sign-flip: exact enumeration up to 20 trials, else MC; descriptive):\n")
    print(md(Ca, 3) + "\n")
    if a.cohort == "all" and not a.glob:
        Pp, Hd, Ds, Rp = pooled_rct(E)
        Pp.to_csv(out / "pooled_emulation_contrasts.csv", index=False)
        Hd.to_csv(out / "pooled_rct_clustered.csv", index=False)
        Ds.to_csv(out / "pooled_emulations_descriptive.csv", index=False)
        Rp.to_csv(out / "pooled_yale_external_replication.csv", index=False)
        print("## Pooled Yale + external — HEADLINE: RCT-clustered (post hoc; corrections item 1)\n")
        print("Yale phase-2 (imputation 1, rep 0; 18 trials) + external v1.5 emulations (main cohorts only; sensitivity variants "
              "excluded). Paired differences are averaged within each RCT benchmark (trial_specs key), then tested across RCTs "
              "(exact sign-flip; two-sided sign test on the count). Negative = first arm closer to the RCT.\n")
        print(md(Hd, 3) + "\n")
        print("Per-emulation (descriptive only; emulations of the same RCT share its benchmark and are not independent):\n")
        print(md(Ds, 3) + "\n")
        if len(Rp):
            print("Yale vs external direction of Δ|log HR − RCT| per shared RCT:\n")
            print(md(Rp, 3) + "\n")
            s_ = Rp.groupby("contrast").same_direction.agg(["sum", "size"])
            print("Same direction: " + ", ".join(f"{c} {int(r['sum'])}/{int(r['size'])}" for c, r in s_.iterrows()) + "\n")
    if len(NC):
        if a.cohort == "all" and not a.glob:
            NC = NC[NC.trial.isin(set(status.trial))]
        NC.drop(columns=["trial_dir"], errors="ignore").to_csv(out / f"{pre}_nco_estimates.csv", index=False)
        PO, SY, SC, CAL = calibration(E, NC)
        PO.to_csv(out / f"{pre}_nco_systematic_error_pooled.csv", index=False)
        SY.to_csv(out / f"{pre}_nco_systematic_error_by_trial.csv", index=False)
        SC.to_csv(out / f"{pre}_nco_contrasts.csv", index=False)
        CAL.to_csv(out / f"{pre}_calibrated_estimates.csv", index=False)
        print("## Negative-control outcomes and empirical calibration (OHDSI style)\n")
        print(f"Usable NCO estimate = NaN rows dropped per NCO, >= 11 NCO events in the arm's analysed sample. Systematic-error model "
              f"b ~ N(mu, sigma^2 + se^2) (v13 fit_syserr); per trial when >= {MIN_NCO_TRIAL} usable NCOs, else the cohort-pooled fit.\n")
        u = NC[NC.usable].groupby(["trial"]).outcome.nunique().rename("usable_NCOs (any arm)")
        print("Usable NCOs per trial: " + ", ".join(f"{k} {v}" for k, v in u.items()) + "\n")
        print("### Systematic error pooled across the cohort's trials, per arm\n")
        print(md(PO, 3) + "\n")
        est = SY[SY.source == "trial"]
        if len(est):
            T2 = est.groupby(["cohort", "arm"]).agg(trials_estimable=("trial", "nunique"), mean_abs_mu=("mu", lambda x: np.mean(np.abs(x))),
                                                    mean_sigma=("sigma", "mean"), mean_share_ci_excl_1=("share_ci_excl_1", "mean")).reset_index()
            print(f"### Per-trial fits (trials with >= {MIN_NCO_TRIAL} usable NCOs), summarised per arm\n")
            print(md(T2, 3) + "\n")
            W = est.pivot_table(index="trial", columns="arm", values="mu")
            W = W[[x for x in ARMS if x in W]]
            print("Per-trial mu (NCO log HR bias):\n")
            print(md(W.reset_index(), 3) + "\n")
        if len(SC):
            print("### Does adding ECG (or CLMBR) reduce systematic error? (per-trial fits; negative = first arm lower; exact sign-flip)\n")
            print(md(SC, 3) + "\n")
        if len(CAL):
            print("### RCT agreement after calibration of the primary estimates\n")
            CP = panel(CAL)
            CP.to_csv(out / f"{pre}_panel_calibrated.csv", index=False)
            print(md(CP, 2) + "\n")
            Cp2, Ca2 = contrasts(CAL)
            Ca2.to_csv(out / f"{pre}_contrasts_calibrated.csv", index=False)
            print("Paired contrasts after calibration:\n")
            print(md(Ca2, 3) + "\n")
    Bb, Br = plasmode(PR, PT)
    if len(Bb):
        Bb.to_csv(out / f"{pre}_plasmode_bias.csv", index=False)
        Br.to_csv(out / f"{pre}_plasmode_reduction.csv", index=False)
        print("## Plasmode bias per arm (true conditional HR 0.8; truth = marginal HR in the arm's matched population)\n")
        print("The outcome model excludes the ECG (as at Yale), so ECG arms can reduce plasmode bias only through their "
              "correlation with the clinical covariates; C1 reductions near zero are expected by construction.\n")
        print(md(Bb[["trial", "scenario", "arm", "reps", "truth", "bias", "bias_lo", "bias_hi", "emp_sd", "rmse", "coverage"]], 3) + "\n")
        print("## Plasmode bias reduction (|bias second| - |bias first|; positive = first arm less biased; MC 95% CI)\n")
        print(md(Br[["trial", "scenario", "contrast", "bias_second", "bias_first", "abs_bias_reduction", "lo", "hi", "pct_reduction"]], 3) + "\n")
    if len(BAL):
        BAL.to_csv(out / f"{pre}_balance.csv", index=False)
        for grp, arms_, ref, lab in (("labs_vitals", FULL_ARMS, "unmatched", "full cohort"), ("phys", FULL_ARMS, "unmatched", "full cohort"),
                                     ("labs_vitals", SUB_ARMS, "unmatched" + SUB, "CLMBR subset")):
            g = BAL[(BAL.group == grp) & BAL.arm.isin(arms_)]
            if g.empty:
                continue
            W = g.pivot_table(index="trial", columns="arm", values="capture_pct")
            W = W[[x for x in arms_ if x in W and x != ref]]
            U = g[g.arm == ref].set_index("trial")[["k", "unmatched_excess"]]
            W = U.join(W).reset_index()
            W["unmatched_excess"] = W.unmatched_excess.map(lambda v: f"{v:.3f}")
            print(f"## Balance capture % ({grp}, {lab}; observed values; blank where unmatched excess < 0.02)\n")
            print(md(W, 1) + "\n")
            med = g[g.arm != ref].groupby("arm").capture_pct.median().reindex([x for x in arms_ if x != ref]).dropna()
            if len(med):
                print("Median capture % across trials: " + ", ".join(f"{k} {v:.0f}" for k, v in med.items()) + "\n")


if __name__ == "__main__":
    main()
