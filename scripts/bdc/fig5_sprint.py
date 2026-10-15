#!/usr/bin/env python
"""Figure 5 engine: hidden-confounder benchmark inside SPRINT by RCT rejection sampling (docs/bdc/FIG5_SPRINT_PROTOCOL.md).

For each withheld baseline confounder C and selection strength OR, each draw keeps participant i with probability
P*(T=t_i | C_i) / (P(T=t_i) * M) (Keith et al., TMLR 2023), so that arm membership depends on C, and then estimates
the intensive-vs-standard HR with the paper's estimator (scripts/v13_common.ps_logit / match / cox: L2 logistic PS,
C = 1; 1:1 greedy caliper 0.2 SD on the logit; Cox with pair-clustered robust SE) under each adjustment arm:
crude, PS-Base, PS-Base + ECG, PS-Base + permuted ECG, PS-Rich(-C), PS-Rich(-C) + ECG, oracle (PS-Base + C).

Inputs (restricted, inside BDC): sprint_cohort.parquet (scripts/bdc/sprint_cohort.py) and sprint_ecg_bcl.parquet
(scripts/bdc/ecg_bcl.py embed). Outputs (aggregate): <out>/fig5_sprint/<run>/draws.csv (one row per draw x arm:
log HR, SE, pairs, events, post-match |SMD| of every candidate C), summary.csv, report.md.

Usage: python scripts/bdc/fig5_sprint.py --run prelim --confounders EGFR LOG_NTPROBNP ECG_CV --ors 3 --draws 50
       python scripts/bdc/fig5_sprint.py --run full   (all 7 C x OR 2/3/5 x 300 draws)
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import bdc_common as BC  # noqa: E402

try:
    from eval_longtail_balance import pcs  # noqa: E402
    from v13_common import cox, match, ps_logit  # noqa: E402  (the paper's estimator, unchanged)
except ImportError as e:  # pragma: no cover
    raise SystemExit(f"{e}: run `pip install --user lifelines scikit-learn` in the Data Studio first")

SEED0 = 20261015
SEED_PERM = 424242
N_PCS = 32
CONFOUNDERS = ["EGFR", "LOG_NTPROBNP", "LOG_HSTNI", "BMI", "LOG_UMALCR", "ECG_CV", "LDL_CALC"]
ROLE = {"ECG_CV": "positive control", "LDL_CALC": "negative control"}
BASE = ["AGE", "FEMALE", "RACE_WHITE", "RACE_BLACK4", "RACE_HISPANIC", "SUB_CLINICALCVD", "SUB_SUBCLINICALCVD",
        "ATRIALFIB", "CONHEARTFAIL", "SMOKE_CURRENT"]
RICH_ADD = ["SBP", "DBP", "N_AGENTS", "ASPIRIN", "STATIN", "HEARTATT", "EGFR", "SCREAT", "SUB_CKD", "LOG_UMALCR", "BMI",
            "CHR", "HDL", "LOG_TRR", "GLUR", "LOG_NTPROBNP", "LOG_HSTNI", "HRAVG", "EDUCATION"]
DERIVED = {"EGFR": ["EGFR", "SCREAT", "SUB_CKD"], "LDL_CALC": ["CHR", "HDL", "LOG_TRR"]}
OUTCOMES = {"primary": ("T_PRIMARY", "EVENT_PRIMARY"), "primary_or_death": ("T_PRIMARYORDEATH", "EVENT_PRIMARYORDEATH")}
ARMS = ["crude", "base", "base+ecg", "base+perm", "rich", "rich+ecg", "oracle"]


def restricted_dir() -> Path:
    return Path(os.environ.get("BDC_RESTRICTED", "/sbgenomics/workspace/bdc-restricted"))


def _read(p: Path) -> pd.DataFrame:
    for q in (p.with_suffix(".parquet"), p.with_suffix(".pkl")):
        if q.exists():
            return pd.read_parquet(q) if q.suffix == ".parquet" else pd.read_pickle(q)
    raise SystemExit(f"missing {p}.parquet/.pkl: run the earlier BDC steps first")


def design(rdir: Path):
    """Analysis population (baseline ECG embedded), covariate matrices and the ECG PCs."""
    C = _read(rdir / "sprint_cohort")
    E = _read(rdir / "sprint_ecg_bcl")
    D = C.merge(E, on="MASKID", how="inner").reset_index(drop=True)
    D["RACE_WHITE"] = (D.RACE4 == "WHITE").astype(float)
    D["RACE_BLACK4"] = (D.RACE4 == "BLACK").astype(float)
    D["RACE_HISPANIC"] = (D.RACE4 == "HISPANIC").astype(float)
    D["SMOKE_CURRENT"] = (pd.to_numeric(D.SMOKE_3CAT, errors="coerce") == 3).astype(float)
    D["LOG_TRR"] = np.log(pd.to_numeric(D.TRR, errors="coerce").clip(lower=1))
    emb = D[[c for c in E.columns if c.startswith("e") and c[1:].isdigit()]].to_numpy(float)
    P = pcs(emb, N_PCS)
    perm = np.random.default_rng(SEED_PERM).permutation(len(P))
    return D, P, P[perm]


def impute(D: pd.DataFrame, cols) -> np.ndarray:
    """Median imputation + a missingness indicator for columns with any missing value."""
    out = []
    for c in cols:
        x = pd.to_numeric(D[c], errors="coerce").to_numpy(float)
        miss = np.isnan(x)
        if miss.any():
            x = np.where(miss, np.nanmedian(x), x)
            out.append(miss.astype(float))
        out.append(x)
    return np.column_stack(out)


def rich_cols(D: pd.DataFrame, c: str) -> list:
    drop = set(DERIVED.get(c, [c]))
    z = pd.to_numeric(D[c], errors="coerce")
    for k in RICH_ADD:
        if k in drop:
            continue
        r = pd.concat([z, pd.to_numeric(D[k], errors="coerce")], axis=1).dropna().corr(method="spearman").iloc[0, 1]
        if np.isfinite(r) and abs(r) >= 0.80:
            drop.add(k)
    return BASE + [k for k in RICH_ADD if k not in drop and k not in BASE]


def selection(z: np.ndarray, t: np.ndarray, OR: float):
    """P*(T=1|z) with mean equal to the randomized share (alpha by bisection), clipped to [0.05, 0.95]."""
    b, p1 = np.log(OR), t.mean()
    lo, hi = -10.0, 10.0
    for _ in range(100):
        a = (lo + hi) / 2
        m = np.clip(1 / (1 + np.exp(-(a + b * z))), 0.05, 0.95).mean()
        lo, hi = (a, hi) if m < p1 else (lo, a)
    ps = np.clip(1 / (1 + np.exp(-(a + b * z))), 0.05, 0.95)
    pt = np.where(t == 1, ps, 1 - ps)
    base = np.where(t == 1, p1, 1 - p1)
    M = (pt / base).max()
    return ps, pt / (base * M)


def smd_abs(V: np.ndarray, t: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """|SMD| per column in the sample idx, over the pooled SD of the pre-match (accepted) sample (= v16 smd_components)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        sd = np.sqrt((np.nanvar(V[t == 1], axis=0, ddof=1) + np.nanvar(V[t == 0], axis=0, ddof=1)) / 2)
        S, st = V[idx], t[idx]
        d = np.abs(np.nanmean(S[st == 1], axis=0) - np.nanmean(S[st == 0], axis=0)) / sd
    d[~np.isfinite(sd) | (sd == 0)] = np.nan
    return d


# worker state (set once per process)
G = {}


def _init(state):
    G.update(state)


def one_draw(job):
    c, OR, d = job
    t_all, yt_all, ye_all = G["t"], G["yt"], G["ye"]
    ok = G["ok"][c]
    z = G["z"][c]
    _, acc = selection(z[ok], t_all[ok], OR)
    rng = np.random.default_rng(SEED0 + d)
    u = rng.random(len(t_all))[ok]  # same uniforms for every C at a given draw
    rows = np.flatnonzero(ok)[u < acc]
    t, yt, ye = t_all[rows], yt_all[rows], ye_all[rows]
    V = G["V"][rows]
    X = {"base": G["Xbase"][rows], "ecg": G["P"][rows], "perm": G["Pperm"][rows], "rich": G["Xrich"][c][rows],
         "c": z[rows, None]}
    designs = {"base": X["base"], "base+ecg": np.c_[X["base"], X["ecg"]], "base+perm": np.c_[X["base"], X["perm"]],
               "rich": X["rich"], "rich+ecg": np.c_[X["rich"], X["ecg"]], "oracle": np.c_[X["base"], X["c"]]}
    out = []
    b, se = cox(yt, ye, t)
    out.append(dict(c=c, OR=OR, draw=d, arm="crude", n=len(rows), n_pairs=np.nan, events=int(ye.sum()), loghr=b, se=se,
                    **{f"smd_{k}": v for k, v in zip(G["vnames"], smd_abs(V, t, np.arange(len(rows))))}))
    for arm, Xa in designs.items():
        lg = ps_logit(Xa, t)
        idx, cl, _w = match(lg, t, cal=0.2, ratio=1)
        b, se = cox(yt[idx], ye[idx], t[idx], cluster=cl)
        out.append(dict(c=c, OR=OR, draw=d, arm=arm, n=len(rows), n_pairs=int(len(np.unique(cl))),
                        events=int(ye[idx].sum()), loghr=b, se=se,
                        **{f"smd_{k}": v for k, v in zip(G["vnames"], smd_abs(V, t, idx))}))
    return out


def truth(z, t, yt, ye, ps) -> float:
    """Randomized HR in the population matching targets: full-trial Cox weighted by P*(T=1|C)."""
    b, _ = cox(yt, ye, t, w=ps)
    return b


def gap(df: pd.DataFrame, arm: str, ref: str, B: int = 2000):
    """Share of the confounding gap closed: sum(b_ref - b_arm) / sum(b_ref - b_oracle), bootstrap over draws."""
    w = df.pivot_table(index="draw", columns="arm", values="loghr")
    w = w[[ref, arm, "oracle"]].dropna()
    num, den = (w[ref] - w[arm]).to_numpy(), (w[ref] - w["oracle"]).to_numpy()
    g = num.sum() / den.sum() if den.sum() != 0 else np.nan
    rng = np.random.default_rng(20261001)
    bs = []
    for _ in range(B):
        k = rng.integers(0, len(w), len(w))
        if den[k].sum() != 0:
            bs.append(num[k].sum() / den[k].sum())
    lo, hi = (np.percentile(bs, [2.5, 97.5]) if bs else (np.nan, np.nan))
    return float(g), float(lo), float(hi), len(w)


def summarize(draws: pd.DataFrame, truths: dict) -> pd.DataFrame:
    rows = []
    for (c, OR), g in draws.groupby(["c", "OR"]):
        tr = truths[(c, OR)]
        w = g.pivot_table(index="draw", columns="arm", values="loghr")
        induced = (w["base"] - w["oracle"]).dropna()
        mcse = induced.std(ddof=1) / np.sqrt(len(induced)) if len(induced) > 1 else np.nan
        gate = bool(induced.mean() != 0 and abs(induced.mean()) > 2 * mcse)
        for arm, a in g.groupby("arm"):
            cov = ((a.loghr - 1.96 * a.se <= tr) & (tr <= a.loghr + 1.96 * a.se)).mean()
            r = dict(c=c, role=ROLE.get(c, "physiology"), OR=OR, arm=arm, draws=int(a.loghr.notna().sum()),
                     mean_n=round(a.n.mean()), mean_pairs=round(a.n_pairs.mean()) if a.n_pairs.notna().any() else np.nan,
                     mean_events=round(a.events.mean()), mean_loghr=a.loghr.mean(), truth_loghr=tr,
                     bias=a.loghr.mean() - tr, emp_sd=a.loghr.std(ddof=1), rmse=np.sqrt(((a.loghr - tr) ** 2).mean()),
                     coverage=cov, mean_smd_c=a[f"smd_{c}"].mean(), induced_bias_base_minus_oracle=induced.mean(),
                     induced_mcse=mcse, gate_material_bias=gate)
            rows.append(r)
        for arm, ref in (("base+ecg", "base"), ("base+perm", "base"), ("rich+ecg", "rich")):
            gg, lo, hi, n = gap(g, arm, ref)
            for r in rows:
                if r["c"] == c and r["OR"] == OR and r["arm"] == arm:
                    r.update(gap_closed=gg, gap_lo=lo, gap_hi=hi, gap_draws=n)
    S = pd.DataFrame(rows)
    base_smd = S[S.arm == "base"].set_index(["c", "OR"]).mean_smd_c
    S["smd_c_relred_vs_base"] = 1 - S.mean_smd_c / S.set_index(["c", "OR"]).index.map(base_smd).to_numpy()
    return S


def r2_probe(D, P, Xbase, cols) -> dict:
    """5-fold ridge R2 of each C from the ECG PCs, PS-Base, and both (partial R2 = both - base)."""
    def cv_r2(X, y):
        f = np.random.default_rng(1).integers(0, 5, len(y))
        Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)
        pred = np.zeros(len(y))
        for k in range(5):
            tr, te = f != k, f == k
            A = np.c_[np.ones(tr.sum()), Xs[tr]]
            w = np.linalg.solve(A.T @ A + 10 * np.eye(A.shape[1]), A.T @ y[tr])
            pred[te] = np.c_[np.ones(te.sum()), Xs[te]] @ w
        return 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    out = {}
    for c in cols:
        y = pd.to_numeric(D[c], errors="coerce").to_numpy(float)
        m = np.isfinite(y)
        rb, re_, rbe = cv_r2(Xbase[m], y[m]), cv_r2(P[m], y[m]), cv_r2(np.c_[Xbase[m], P[m]], y[m])
        out[c] = dict(r2_ecg=round(float(re_), 3), r2_base=round(float(rb), 3), r2_base_ecg=round(float(rbe), 3),
                      partial_r2=round(float(rbe - rb), 3))
    return out


def write_md(S: pd.DataFrame, R: dict, path: Path) -> None:
    L = [f"# Figure 5 (SPRINT) run `{R['run']}` ({R['when']}, git {R['git'][:10]})", "",
         f"- population with baseline ECG embedding: {R['n']}; outcome: {R['outcome']}; draws per cell: {R['draws']}",
         f"- confounders: {R['confounders']}; OR per SD: {R['ors']}", ""]
    L += ["## Share of the confounding gap closed (ratio of means over draws; 95% bootstrap CI)", "",
          "| C | role | OR | gate | base+ECG | base+permuted | rich(−C)+ECG |", "|---|---|---|---|---|---|---|"]
    for (c, OR), g in S.groupby(["c", "OR"], sort=False):
        f = lambda a: (lambda r: f"{r.gap_closed:.1%} ({r.gap_lo:.1%} to {r.gap_hi:.1%})" if np.isfinite(r.gap_closed)
                       else "n/a")(g[g.arm == a].iloc[0])
        L.append(f"| {c} | {g.role.iloc[0]} | {OR:g} | {'yes' if g.gate_material_bias.iloc[0] else 'NO'} | "
                 f"{f('base+ecg')} | {f('base+perm')} | {f('rich+ecg')} |")
    L += ["", "## Per arm (mean over draws)", "",
          "| C | OR | arm | pairs | events | mean log HR | truth | bias | RMSE | coverage | post-match SMD(C) | SMD(C) vs base |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in S.itertuples():
        L.append(f"| {r.c} | {r.OR:g} | {r.arm} | {r.mean_pairs} | {r.mean_events} | {r.mean_loghr:.3f} | {r.truth_loghr:.3f} | "
                 f"{r.bias:+.3f} | {r.rmse:.3f} | {r.coverage:.2f} | {r.mean_smd_c:.3f} | {r.smd_c_relred_vs_base:+.1%} |")
    L += ["", "## How well the ECG predicts each C (5-fold ridge R²)", ""]
    L += [f"- {k}: {v}" for k, v in R["r2"].items()]
    path.write_text("\n".join(L) + "\n")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="prelim")
    ap.add_argument("--confounders", nargs="+", default=CONFOUNDERS)
    ap.add_argument("--ors", nargs="+", type=float, default=[2.0, 3.0, 5.0])
    ap.add_argument("--draws", type=int, default=300)
    ap.add_argument("--outcome", choices=list(OUTCOMES), default="primary")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args(argv)
    t0 = time.time()
    D, P, Pperm = design(restricted_dir())
    tc, ec = OUTCOMES[a.outcome]
    t = D.RANDASSIGN.to_numpy(int)
    yt, ye = pd.to_numeric(D[tc], errors="coerce").to_numpy(float), pd.to_numeric(D[ec], errors="coerce").to_numpy(float)
    out_ok = np.isfinite(yt) & np.isfinite(ye)
    vnames = CONFOUNDERS
    V = np.column_stack([pd.to_numeric(D[c], errors="coerce").to_numpy(float) for c in vnames])
    Xbase = impute(D, BASE)
    state = dict(t=t, yt=yt, ye=ye.astype(int, copy=False) if np.isfinite(ye).all() else np.nan_to_num(ye).astype(int),
                 P=P, Pperm=Pperm, Xbase=Xbase, V=V, vnames=vnames, z={}, ok={}, Xrich={})
    truths, rich_used = {}, {}
    for c in a.confounders:
        x = pd.to_numeric(D[c], errors="coerce").to_numpy(float)
        ok = np.isfinite(x) & out_ok
        z = np.full(len(x), np.nan)
        z[ok] = (x[ok] - x[ok].mean()) / x[ok].std()
        state["z"][c], state["ok"][c] = z, ok
        cols = rich_cols(D, c)
        rich_used[c] = [k for k in cols if k not in BASE]
        state["Xrich"][c] = impute(D, cols)
        for OR in a.ors:
            ps, _ = selection(z[ok], t[ok], OR)
            truths[(c, OR)] = truth(z[ok], t[ok], yt[ok], state["ye"][ok], ps)
    jobs = [(c, OR, d) for c in a.confounders for OR in a.ors for d in range(a.draws)]
    BC.log(f"{len(jobs)} draws x {len(ARMS)} arms on {a.workers} workers ...")
    rows = []
    with ProcessPoolExecutor(a.workers, initializer=_init, initargs=(state,)) as ex:
        for i, r in enumerate(ex.map(one_draw, jobs, chunksize=4)):
            rows += r
            if (i + 1) % 50 == 0:
                BC.log(f"  {i + 1}/{len(jobs)} draws ({time.time() - t0:.0f} s)")
    draws = pd.DataFrame(rows)
    S = summarize(draws, truths)
    out = BC.out_root() / "fig5_sprint" / a.run
    out.mkdir(parents=True, exist_ok=True)
    draws.to_csv(out / "draws.csv", index=False)
    S.to_csv(out / "summary.csv", index=False)
    R = dict(run=a.run, when=time.strftime("%Y-%m-%d %H:%M"), git=BC.git_sha(), n=BC.suppress(len(D)), outcome=a.outcome,
             draws=a.draws, confounders=a.confounders, ors=a.ors, rich_inputs=rich_used,
             r2=r2_probe(D, P, Xbase, a.confounders), seconds=round(time.time() - t0))
    BC.write_json(out / "run.json", R)
    write_md(S, R, out / "report.md")
    print((out / "report.md").read_text())
    BC.log(f"done in {R['seconds']} s; outputs (aggregate): {out}")


if __name__ == "__main__":
    main()
