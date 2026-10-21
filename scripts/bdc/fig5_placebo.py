#!/usr/bin/env python
"""Figure 5 follow-up (post hoc, audit 2026-10-21): multi-permutation placebo and bias reduction against the truth.

The locked engine (fig5_sprint.py) used one permutation of the ECG PCs for the placebo arm. A single permutation can
move the gap closed by tens of points, so this script repeats the placebo with K independent permutations and reports:
  - the gap closed by PS-Base + ECG (identical draws and seeds to the locked run, so it reproduces fig5_sprint),
  - the placebo distribution over K permutations (mean, 2.5-97.5 percentile, 95th percentile),
  - ECG minus the mean placebo gap, with a bootstrap CI over draws (paired: same draws for every arm),
  - bias reduction against the anchor-matched truth: 1 - mean(b_arm - truth) / mean(b_base - truth), for ECG and placebo,
  - for eGFR, post-match |SMD| of eGFR < 60 and SUB_CKD (is the ECG gain coming from the low-eGFR tail?).
Estimator, selection model, seeds and truth are imported from fig5_sprint.py unchanged. Outputs are aggregate only.

Usage: python scripts/bdc/fig5_placebo.py                      (hs-TnI, eGFR, NT-proBNP, UACR, Cornell at OR 3; 300 draws; K 20)
       python scripts/bdc/fig5_placebo.py --ors 2 3 5 --perms 20
"""
from __future__ import annotations

import argparse
import json
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
import fig5_sprint as F  # noqa: E402

DEFAULT_C = ["LOG_HSTNI", "EGFR", "LOG_NTPROBNP", "LOG_UMALCR", "ECG_CV"]
SEED_PERMS = 515151  # permutation k uses SEED_PERMS + k (the locked run used 424242)
EXTRA = ["EGFR_LT60", "SUB_CKD"]
G = {}


def _init(state):
    G.update(state)


def one_draw(job):
    c, OR, d = job
    ok, z = G["ok"][c], G["z"][c]
    _, acc = F.selection(z[ok], G["t"][ok], OR)
    u = np.random.default_rng(F.SEED0 + d).random(len(G["t"]))[ok]  # same uniforms as fig5_sprint.one_draw
    rows = np.flatnonzero(ok)[u < acc]
    t, yt, ye = G["t"][rows], G["yt"][rows], G["ye"][rows]
    V = G["V"][rows]
    Xb = G["Xbase"][rows]
    designs = {"base": Xb, "base+ecg": np.c_[Xb, G["P"][rows]], "oracle": np.c_[Xb, z[rows, None]]}
    for k, Pk in enumerate(G["Pperms"]):
        designs[f"perm{k:02d}"] = np.c_[Xb, Pk[rows]]
    anchor = 1 if (t == 1).sum() <= (t == 0).sum() else 0
    out = []
    for arm, Xa in designs.items():
        idx, cl, _w = F.match(F.ps_logit(Xa, t), t, cal=0.2, ratio=1)
        b, se = F.cox(yt[idx], ye[idx], t[idx], cluster=cl)
        smd = F.smd_abs(V, t, idx)
        out.append(dict(c=c, OR=OR, draw=d, arm=arm, anchor=anchor, loghr=b, se=se, n_pairs=int(len(np.unique(cl))),
                        **{f"smd_{v}": s for v, s in zip(G["vnames"], smd)}))
    return out


def gap_from(w: pd.DataFrame, arm: str) -> float:
    den = (w["base"] - w["oracle"]).sum()
    return float((w["base"] - w[arm]).sum() / den) if den != 0 else np.nan


def summarize(draws: pd.DataFrame, truths: dict, K: int, B: int = 2000) -> list:
    out = []
    perms = [f"perm{k:02d}" for k in range(K)]
    for (c, OR), g in draws.groupby(["c", "OR"], sort=False):
        w = g.pivot_table(index="draw", columns="arm", values="loghr").dropna()
        a = g.drop_duplicates("draw").set_index("draw").anchor.reindex(w.index)
        tr = truths[(c, OR)]
        ref = np.where(a.to_numpy() == 1, tr["t1"], tr["t0"])
        g_ecg = gap_from(w, "base+ecg")
        g_perm = np.array([gap_from(w, p) for p in perms])
        diff = g_ecg - g_perm.mean()
        rng = np.random.default_rng(20261001)
        bs = []
        for _ in range(B):
            kk = rng.integers(0, len(w), len(w))
            ws = w.iloc[kk]
            bs.append(gap_from(ws, "base+ecg") - np.mean([gap_from(ws, p) for p in perms]))
        bias = {arm: float((w[arm] - ref).mean()) for arm in ["base", "base+ecg", "oracle"] + perms}
        red = lambda arm: 1 - bias[arm] / bias["base"] if bias["base"] != 0 else np.nan  # noqa: E731
        r = dict(c=c, OR=OR, draws=len(w), perms=K, gap_ecg=g_ecg, gap_perm_mean=float(g_perm.mean()),
                 gap_perm_p2_5=float(np.percentile(g_perm, 2.5)), gap_perm_p97_5=float(np.percentile(g_perm, 97.5)),
                 gap_perm_p95=float(np.percentile(g_perm, 95)), gap_ecg_minus_perm=float(diff),
                 gap_ecg_minus_perm_lo=float(np.percentile(bs, 2.5)), gap_ecg_minus_perm_hi=float(np.percentile(bs, 97.5)),
                 ecg_beyond_all_perms=bool(g_ecg > g_perm.max()),
                 bias_base=bias["base"], bias_ecg=bias["base+ecg"], bias_oracle=bias["oracle"],
                 biasred_ecg=float(red("base+ecg")), biasred_oracle=float(red("oracle")),
                 biasred_perm_mean=float(np.mean([red(p) for p in perms])),
                 smd_c_base=float(g[g.arm == "base"][f"smd_{c}"].mean()), smd_c_ecg=float(g[g.arm == "base+ecg"][f"smd_{c}"].mean()),
                 smd_c_perm_mean=float(g[g.arm.isin(perms)][f"smd_{c}"].mean()))
        if c == "EGFR":
            for v in EXTRA:
                r[f"smd_{v}_base"] = float(g[g.arm == "base"][f"smd_{v}"].mean())
                r[f"smd_{v}_ecg"] = float(g[g.arm == "base+ecg"][f"smd_{v}"].mean())
                r[f"smd_{v}_perm_mean"] = float(g[g.arm.isin(perms)][f"smd_{v}"].mean())
        out.append(r)
    return out


def write_md(S: list, R: dict, path: Path) -> None:
    pc = lambda x: f"{100 * x:.1f}%"  # noqa: E731
    L = [f"# Figure 5 follow-up: multi-permutation placebo (POST HOC, audit 2026-10-21) run `{R['run']}` ({R['when']}, git {R['git'][:10]})", "",
         f"- outcome: {R['outcome']}; draws per cell: {R['draws']}; placebo permutations: {R['perms']}; n per C: {R['n_by_confounder']}", "",
         "| C | OR | gap closed, ECG | placebo mean (2.5-97.5%) | ECG minus placebo (95% CI) | ECG > every placebo | bias reduction vs truth: ECG / placebo mean / oracle |",
         "|---|---|---|---|---|---|---|"]
    for r in S:
        L.append(f"| {r['c']} | {r['OR']:g} | {pc(r['gap_ecg'])} | {pc(r['gap_perm_mean'])} ({pc(r['gap_perm_p2_5'])} to {pc(r['gap_perm_p97_5'])}) | "
                 f"{pc(r['gap_ecg_minus_perm'])} ({pc(r['gap_ecg_minus_perm_lo'])} to {pc(r['gap_ecg_minus_perm_hi'])}) | "
                 f"{'yes' if r['ecg_beyond_all_perms'] else 'no'} | {pc(r['biasred_ecg'])} / {pc(r['biasred_perm_mean'])} / {pc(r['biasred_oracle'])} |")
    L += ["", "## Post-match |SMD| of the hidden characteristic (base / ECG / placebo mean)", ""]
    L += [f"- {r['c']} OR {r['OR']:g}: {r['smd_c_base']:.3f} / {r['smd_c_ecg']:.3f} / {r['smd_c_perm_mean']:.3f}" for r in S]
    eg = [r for r in S if r["c"] == "EGFR"]
    if eg:
        L += ["", "## eGFR cells: low-eGFR tail (post-match |SMD|, base / ECG / placebo mean)", ""]
        for r in eg:
            L += [f"- OR {r['OR']:g}, {v}: {r[f'smd_{v}_base']:.3f} / {r[f'smd_{v}_ecg']:.3f} / {r[f'smd_{v}_perm_mean']:.3f}" for v in EXTRA]
    L += ["", "Post hoc follow-up of the locked Figure 5 run; gap closed and seeds as in fig5_sprint.py. Aggregates only."]
    path.write_text("\n".join(L) + "\n")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default="placebo20")
    ap.add_argument("--confounders", nargs="+", default=DEFAULT_C)
    ap.add_argument("--ors", nargs="+", type=float, default=[3.0])
    ap.add_argument("--draws", type=int, default=300)
    ap.add_argument("--perms", type=int, default=20)
    ap.add_argument("--outcome", choices=list(F.OUTCOMES), default="primary")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args(argv)
    t0 = time.time()
    D, P, _ = F.design(F.restricted_dir())
    tc, ec = F.OUTCOMES[a.outcome]
    t = D.RANDASSIGN.to_numpy(int)
    yt, ye = pd.to_numeric(D[tc], errors="coerce").to_numpy(float), pd.to_numeric(D[ec], errors="coerce").to_numpy(float)
    out_ok = np.isfinite(yt) & np.isfinite(ye)
    D["EGFR_LT60"] = (pd.to_numeric(D.EGFR, errors="coerce") < 60).astype(float).where(pd.to_numeric(D.EGFR, errors="coerce").notna())
    vnames = F.CONFOUNDERS + EXTRA
    V = np.column_stack([pd.to_numeric(D[c], errors="coerce").to_numpy(float) for c in vnames])
    state = dict(t=t, yt=yt, ye=np.nan_to_num(ye).astype(int), P=P, Xbase=F.impute(D, F.BASE), V=V, vnames=vnames, z={}, ok={},
                 Pperms=[P[np.random.default_rng(SEED_PERMS + k).permutation(len(P))] for k in range(a.perms)])
    truths = {}
    for c in a.confounders:
        x = pd.to_numeric(D[c], errors="coerce").to_numpy(float)
        ok = np.isfinite(x) & out_ok
        z = np.full(len(x), np.nan)
        z[ok] = (x[ok] - x[ok].mean()) / x[ok].std()
        state["z"][c], state["ok"][c] = z, ok
        for OR in a.ors:
            ps, _ = F.selection(z[ok], t[ok], OR)
            truths[(c, OR)] = F.truth(z[ok], t[ok], yt[ok], state["ye"][ok], ps)
    jobs = [(c, OR, d) for c in a.confounders for OR in a.ors for d in range(a.draws)]
    BC.log(f"{len(jobs)} draws x {3 + a.perms} arms on {a.workers} workers ...")
    rows = []
    with ProcessPoolExecutor(a.workers, initializer=_init, initargs=(state,)) as ex:
        for i, r in enumerate(ex.map(one_draw, jobs, chunksize=4)):
            rows += r
            if (i + 1) % 50 == 0:
                BC.log(f"  {i + 1}/{len(jobs)} draws ({time.time() - t0:.0f} s)")
    draws = pd.DataFrame(rows)
    S = summarize(draws, truths, a.perms)
    out = BC.out_root() / "fig5_sprint" / a.run
    out.mkdir(parents=True, exist_ok=True)
    draws.to_csv(out / "draws.csv", index=False)
    pd.DataFrame(S).to_csv(out / "summary.csv", index=False)
    R = dict(run=a.run, when=time.strftime("%Y-%m-%d %H:%M"), git=BC.git_sha(), outcome=a.outcome, draws=a.draws, perms=a.perms,
             n_by_confounder={c: BC.suppress(int(state["ok"][c].sum())) for c in a.confounders}, seconds=round(time.time() - t0))
    (out / "run.json").write_text(json.dumps(R, indent=1))
    write_md(S, R, out / "report.md")
    print((out / "report.md").read_text())
    BC.log(f"done in {time.time() - t0:.0f} s; outputs (aggregate): {out}")


if __name__ == "__main__":
    main()
