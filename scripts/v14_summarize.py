#!/usr/bin/env python
"""v1.4 summary and hypotheses A-E (docs/PROTOCOL_V1_4_AMENDMENT.md). Markdown to stdout; CSV to docs/v14/."""
import glob
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_specs import TRIALS  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, bench  # noqa: E402
from v13_summarize import md  # noqa: E402

D = A / "claude-v14"
OUT = Path(__file__).resolve().parent.parent / "docs" / "v14"
CON = [("C1", "sparse+ECG", "sparse"), ("C2", "hdPS200+ECG", "hdPS200")]
LAB = {"sparse": "M1 sparse", "sparse+ECG": "M2 sparse+ECG", "hdPS200": "M3 hdPS200", "hdPS200+ECG": "M4 hdPS200+ECG",
       "clinical (reference)": "R clinical", "R+": "R+ physiology ref"}
KEY = {n: k for n, (k, _) in {**PRIMARY, **EXTRA}.items()}
B = 500


def read(kind):
    fs = glob.glob(str(D / f"{kind}_*_*.csv"))
    return pd.concat([pd.read_csv(f, keep_default_na=False, na_values=[""]) for f in fs]) if fs else pd.DataFrame()


def plasmode_errors():
    R, Tr = read("plasmode"), read("truth")
    if R.empty:
        return {}
    R = R.merge(Tr, on=["trial", "mode", "pool", "scenario", "arm"])
    R["err"] = R.loghr - R.truth_loghr
    E = {}
    for (tr, pool, sc, arm), g in R.groupby(["trial", "pool", "scenario", "arm"]):
        E[(tr, pool, sc, arm)] = g.sort_values("rep").err.to_numpy()
    # v1.3 resampled plasmode = dropout 0 / full cohort reference
    for f in glob.glob(str(A / "claude-v13-plasmode-rs" / "reps_*.csv")):
        n = Path(f).stem[5:]
        r = pd.read_csv(f, keep_default_na=False, na_values=[""])
        t = pd.read_csv(A / "claude-v13-plasmode-rs" / f"truth_{n}.csv", keep_default_na=False, na_values=[""])
        r = r.merge(t[["scenario", "arm", "truth_loghr"]], on=["scenario", "arm"])
        r["err"] = r.loghr - r.truth_loghr
        for (sc, arm), g in r.groupby(["scenario", "arm"]):
            E[(n, "dropout_0", sc, arm)] = g.sort_values("rep").err.to_numpy()
    return E


def reduction(E, pool, sc, a2, a1, rng, boot=True, only=None):
    """Mean over trials of |bias(a1)| - |bias(a2)| (positive = a2 less biased); per-trial rep resampling."""
    trials = sorted({k[0] for k in E if k[1] == pool and k[2] == sc and k[3] in (a1, a2)} & (set(only) if only else set(k[0] for k in E)))
    pairs = [(E[(t, pool, sc, a1)], E[(t, pool, sc, a2)]) for t in trials if (t, pool, sc, a1) in E and (t, pool, sc, a2) in E]
    if not pairs:
        return None
    est = np.mean([abs(np.nanmean(x)) - abs(np.nanmean(y)) for x, y in pairs])
    bs = None
    if boot:
        bs = np.array([np.mean([abs(np.nanmean(x[ix])) - abs(np.nanmean(y[ix]))
                                for x, y in pairs for ix in [rng.integers(0, len(x), len(x))]]) for _ in range(B)])
    return dict(trials=len(pairs), est=est, bs=bs, names=[t for t in trials if (t, pool, sc, a1) in E and (t, pool, sc, a2) in E])


def boot_d(Bt, pool, tgt, a2, a1, only=None):
    """Per rep: mean over trials of err(a2)^2 - err(a1)^2 vs target; returns (point, array over reps 1..200, n trials)."""
    sub = Bt[Bt.pool == pool]
    if only is not None:
        sub = sub[sub.trial.isin(only)]
    M = []
    for tr, g in sub.groupby("trial"):
        P = g.pivot_table(index="rep", columns="arm", values="loghr")
        if a1 not in P or a2 not in P:
            continue
        b, se = bench(KEY[tr])
        reps = P.index.to_numpy()
        if tgt == "RCT":
            t = np.where(reps == 0, b, b + se * np.random.default_rng(zlib.crc32(tr.encode())).normal(size=len(reps)))
        else:
            t = P["R+"].to_numpy()
        M.append(pd.Series((P[a2].to_numpy() - t) ** 2 - (P[a1].to_numpy() - t) ** 2, index=reps, name=tr))
    if not M:
        return None
    M = pd.concat(M, axis=1)
    return M.loc[0].mean(), M.drop(index=0).mean(axis=1).to_numpy(), M.shape[1]


def ci(x):
    return np.nanpercentile(x, 2.5), np.nanpercentile(x, 97.5)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260926)
    E = plasmode_errors()
    Bt = read("boot")
    print("# v1.4 — where does the ECG add information? (exploratory; tag protocol-v1.4)\n")
    pools = sorted({k[1] for k in E})
    rows = []
    for pool in pools:
        scen = sorted({k[2] for k in E if k[1] == pool})
        for sc in scen:
            for cn, a2, a1 in CON:
                r = reduction(E, pool, sc, a2, a1, rng)
                if r is None:
                    continue
                lo, hi = ci(r["bs"])
                rel = r["est"] / np.mean([abs(np.nanmean(E[(t, pool, sc, a1)])) for t in r["names"]])
                rows.append(dict(pool=pool, scenario=sc, contrast=cn, trials=r["trials"], bias_reduction=r["est"], lo=lo, hi=hi,
                                 relative=rel))
    PL = pd.DataFrame(rows)
    PL.to_csv(OUT / "plasmode_contrasts.csv", index=False)
    # absolute bias by arm
    ab = []
    for (tr, pool, sc, arm), e in E.items():
        ab.append(dict(trial=tr, pool=pool, scenario=sc, arm=arm, bias=np.nanmean(e), rmse=np.sqrt(np.nanmean(e ** 2))))
    AB = pd.DataFrame(ab)
    AB.to_csv(OUT / "plasmode_bias_by_trial.csv", index=False)
    print("## Plasmode: bias reduction from adding the ECG (log-HR scale; positive = ECG arm less biased)\n")
    print(md(PL, 4) + "\n")
    print("Mean |bias| by arm (across trials):\n")
    x = AB.groupby(["pool", "scenario", "arm"]).bias.apply(lambda v: np.mean(np.abs(v))).unstack("arm")
    x = x[[c for c in LAB if c in x.columns]].rename(columns=LAB).reset_index()
    print(md(x, 3) + "\n")
    # bootstrap
    br = []
    for pool in sorted(Bt.pool.unique()) if not Bt.empty else []:
        for cn, a2, a1 in CON:
            for tgt in ("RCT", "R+"):
                if pool == "hf_outcome" and tgt == "RCT":
                    continue
                r = boot_d(Bt, pool, tgt, a2, a1)
                if r is None:
                    continue
                lo, hi = ci(r[1])
                br.append(dict(pool=pool, contrast=cn, target=tgt, trials=r[2], mean_d_sqerr=r[0], lo=lo, hi=hi))
    BR = pd.DataFrame(br)
    BR.to_csv(OUT / "bootstrap_contrasts.csv", index=False)
    print("## Real-data paired bootstrap: mean over trials of err(ECG arm)² − err(comparator)² (negative = ECG closer)\n")
    print(md(BR, 4) + "\n")

    # hypotheses
    print("## Hypotheses\n")
    H = []

    def pl_diff(p1, p2, sc, cn):
        a2, a1 = {c: (x, y) for c, x, y in CON}[cn]
        t1 = {k[0] for k in E if k[1] == p1 and k[2] == sc and k[3] == a2}
        t2 = {k[0] for k in E if k[1] == p2 and k[2] == sc and k[3] == a2}
        common = sorted(t1 & t2)
        if not common:
            return None
        r1, r2 = reduction(E, p1, sc, a2, a1, rng, only=common), reduction(E, p2, sc, a2, a1, rng, only=common)
        if r1 is None or r2 is None:
            return None
        d = r1["bs"] - r2["bs"]
        return r1["est"] - r2["est"], *ci(d), len(common)

    def bs_diff(p1, p2, cn, tgt="R+"):
        a2, a1 = {c: (x, y) for c, x, y in CON}[cn]
        common = sorted(set(Bt[Bt.pool == p1].trial) & set(Bt[Bt.pool == p2].trial))
        r1, r2 = boot_d(Bt, p1, tgt, a2, a1, common), boot_d(Bt, p2, tgt, a2, a1, common)
        if r1 is None or r2 is None:
            return None
        return r1[0] - r2[0], *ci(r1[1] - r2[1]), len(common)

    for cn in ("C1", "C2"):
        for hyp, p1, p2, sc_list in (("A (low vs high code density)", "density_low", "density_high", ("base", "phys_only")),
                                     ("C (no echo vs echo)", "echo_no", "echo_yes", ("base", "phys_only")),
                                     ("B (dropout 0.75 vs 0)", "dropout_0.75", "dropout_0", ("base", "phys_only"))):
            for sc in sc_list:
                r = pl_diff(p1, p2, sc, cn)
                if r:
                    H.append(dict(hypothesis=hyp, contrast=cn, trials=r[3], test=f"plasmode {sc}: reduction({p1}) − reduction({p2})",
                                  estimate=r[0], lo=r[1], hi=r[2], supported=bool(r[1] > 0)))
            if not hyp.startswith("B"):
                r = bs_diff(p1, p2, cn)
                if r:
                    H.append(dict(hypothesis=hyp, contrast=cn, trials=r[3], test=f"bootstrap vs R+: d({p1}) − d({p2})",
                                  estimate=r[0], lo=r[1], hi=r[2], supported=bool(r[2] < 0)))
        for sc in ("echo_only", "echo_base", "echo_strong"):
            x = PL[(PL.pool == "echo_subcohort") & (PL.scenario == sc) & (PL.contrast == cn)]
            if len(x):
                x = x.iloc[0]
                H.append(dict(hypothesis="D (echo physiology as hidden confounder)", contrast=cn, trials=int(x.trials), test=f"plasmode {sc}: bias reduction",
                              estimate=x.bias_reduction, lo=x.lo, hi=x.hi, supported=bool(x.lo > 0)))
        x = PL[(PL.pool == "hf_outcome") & (PL.scenario == "base") & (PL.contrast == cn)]
        if len(x):
            x = x.iloc[0]
            H.append(dict(hypothesis="E (HF hospitalisation outcome)", contrast=cn, trials=int(x.trials), test="plasmode base: bias reduction",
                          estimate=x.bias_reduction, lo=x.lo, hi=x.hi, supported=bool(x.lo > 0)))
        x = BR[(BR.pool == "hf_outcome") & (BR.contrast == cn) & (BR.target == "R+")]
        if len(x):
            x = x.iloc[0]
            H.append(dict(hypothesis="E (HF hospitalisation outcome)", contrast=cn, trials=int(x.trials), test="bootstrap vs R+",
                          estimate=x.mean_d_sqerr, lo=x.lo, hi=x.hi, supported=bool(x.hi < 0)))
    HT = pd.DataFrame(H)
    HT.to_csv(OUT / "hypotheses.csv", index=False)
    print(md(HT, 4) + "\n")
    # stratum sizes
    metas = [pd.read_json(f, typ="series") for f in glob.glob(str(D / "meta_*_strata-echo.json"))]
    if metas:
        print("Stratum feasibility (smaller arm >= 100 required): see docs/v14/strata.csv\n")
        rows = []
        for m in metas:
            for p, v in m["pools"].items():
                rows.append(dict(trial=m["trial"], pool=p, n=v["n"], feasible=v["feasible"]))
        S = pd.DataFrame(rows)
        S.to_csv(OUT / "strata.csv", index=False)
        print(md(S.groupby("pool").agg(trials_feasible=("feasible", "sum"), median_n=("n", "median")).reset_index(), 0) + "\n")


if __name__ == "__main__":
    main()
