#!/usr/bin/env python
"""CHS pre-specified tests of added information (EXPLORATORY; docs/bdc/CHS_EHR_EXPLORATORY.md §C, fixed 2026-10-19
before any was run).

  noise  Test 3: 50-draw permutation placebo for every added representation. ECG on PS-Base; each EHR representation
         (backbone, CLMBR-T, CLMBR-T rich, where present) on PS-Base and on PS-Codes. Same PS / matching / held-out balance
         as chs_emulate.py. Reports the real pooled relative reduction in mean held-out |SMD|, the placebo median and
         2.5-97.5% range, and the one-sided empirical P = (1 + #placebo >= real) / (N + 1); per emulation as well.
  info   Test 2: information without matching. Within each emulation, each held-out item is predicted by ridge regression
         (5-fold CV grouped by person; E5/E6 capped at 6,000 rows by a fixed random sample of people) from PS-Base,
         + PS-Codes features, + one representation (or ECG). dR2 = R2(PS-Codes + X) - R2(PS-Codes), against 10 permutations
         of X. Criterion: (a) mean dR2 over cells > 95th percentile of the placebo mean, and (b) dR2 > that cell's placebo
         maximum in >= half of cells.

Inputs (restricted, BDC): chs_emulations, chs_ecg_bcl, chs_codes, and any of chs_ehr_backbone / chs_clmbr / chs_clmbr_rich.
Outputs (aggregate): <out>/chs_ehr_tests/{noise,info}.csv and report_{noise,info}.md.
Usage: python scripts/bdc/chs_ehr_tests.py noise [--draws 50]   |   python scripts/bdc/chs_ehr_tests.py info [--draws 10]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import bdc_common as BC  # noqa: E402
import chs_cohort as CH  # noqa: E402
import chs_emulate as CE  # noqa: E402
from eval_longtail_balance import pcs  # noqa: E402
from v13_common import match, ps_logit  # noqa: E402

REPS = {"backbone": "chs_ehr_backbone", "clmbr": "chs_clmbr", "clmbr_rich": "chs_clmbr_rich"}
SEED_NOISE = 515151
SEED_INFO = 20261019
INFO_CAP = 6000


def load():
    rd = Path(os.environ.get("BDC_RESTRICTED", "/sbgenomics/workspace/bdc-restricted"))
    R = CE._read(rd / "chs_emulations")
    E = CE._read(rd / "chs_ecg_bcl")
    ecols = [c for c in E.columns if c.startswith("e") and c[1:].isdigit()]
    R = R.merge(E[["id", "ECG_FILE"] + ecols], on=["id", "ECG_FILE"], how="inner")
    K = CE._read(rd / "chs_codes")
    reps = {}
    for name, tab in REPS.items():
        try:
            Qd = CE._read(rd / tab)
        except SystemExit:
            continue
        cols = [c for c in Qd.columns if c != "row"]
        R = R.merge(Qd.rename(columns={c: f"{name}:{c}" for c in cols}), on="row", how="inner")
        reps[name] = [f"{name}:{c}" for c in cols]
    BC.log(f"representations present: {list(reps)}; rows {BC.suppress(len(R))}")
    return R, ecols, K, reps


def feasible(D):
    return min((D.arm == 1).sum(), (D.arm == 0).sum()) >= 350


def item_smds(V, items, t, X, mask):
    lg = ps_logit(X, t)
    idx, _cl, _w = match(lg, t, cal=0.2, ratio=1)
    b = CE.balance(V, items, t, idx, mask)
    return {k[4:]: v for k, v in b.items() if k.startswith("smd:")}


def common_means(ref: dict, arm: dict):
    c = [k for k in ref if k in arm]
    return (float(np.mean([ref[k] for k in c])), float(np.mean([arm[k] for k in c]))) if c else (np.nan, np.nan)


# ---------------------------------------------------------------- test 3: multi-draw placebo
def cmd_noise(a) -> None:
    t0 = time.time()
    R, ecols, K, reps = load()
    items = list(CH.HELD)
    rows = []
    for emu, D in R.groupby("EMU", sort=False):
        D = D.reset_index(drop=True)
        if not feasible(D):
            continue
        t = D.arm.to_numpy(int)
        V = np.column_stack([pd.to_numeric(D[c], errors="coerce").to_numpy(float) for c in items])
        Xb = CE.design_matrix(D, CE.BASE)
        Xk = CE.code_matrix(D, K)
        Dk = pd.concat([D, Xk.add_prefix("code:")], axis=1)
        mask_k = CE.masked_items(Dk, list(Xk.add_prefix("code:").columns))
        rungs = {"base": (Xb, set()), "codes": (np.c_[Xb, Xk.to_numpy(float)], mask_k)}
        refs = {r: item_smds(V, items, t, X, m) for r, (X, m) in rungs.items()}
        mats = {"ecg": pcs(D[ecols].to_numpy(float), CE.N_PCS)}
        mats.update({n: pcs(D[c].to_numpy(float), min(64, len(c))) for n, c in reps.items()})
        jobs = [("base", "ecg")] + [(r, n) for n in reps for r in ("base", "codes")]
        for rung, rep in jobs:
            Xr, mask = rungs[rung]
            M = mats[rep]
            for d in range(-1, a.draws):
                Md = M if d < 0 else M[np.random.default_rng(SEED_NOISE + d).permutation(len(M))]
                mr, ma = common_means(refs[rung], item_smds(V, items, t, np.c_[Xr, Md], mask))
                rows.append(dict(EMU=emu, rung=rung, rep=rep, draw=d, m_ref=mr, m_arm=ma))
            BC.log(f"{emu}: {rep} on {rung} done ({time.time() - t0:.0f} s)")
    N = pd.DataFrame(rows)
    out = BC.out_root() / "chs_ehr_tests"
    out.mkdir(parents=True, exist_ok=True)
    N.to_csv(out / "noise.csv", index=False)
    L = [f"# CHS test 3: multi-draw permutation placebo (EXPLORATORY, pre-specified) ({time.strftime('%Y-%m-%d %H:%M')}, "
         f"git {BC.git_sha()[:10]})", "", f"- draws per arm: {a.draws}; reduction = 1 - mean(arm) / mean(rung), mean held-out "
         "|SMD| over items observed in both; pooled over emulations as in chs_emulate", "",
         "| representation | on | real pooled | placebo median | placebo 2.5-97.5% | placebo 95th | P (one-sided) | beyond chance |",
         "|---|---|---|---|---|---|---|---|"]
    per = []
    for (rung, rep), g in N.groupby(["rung", "rep"], sort=False):
        pooled = g.groupby("draw").apply(lambda h: 1 - h.m_arm.mean() / h.m_ref.mean())
        real, plc = float(pooled.loc[-1]), pooled.drop(index=-1).to_numpy()
        p = (1 + int((plc >= real).sum())) / (len(plc) + 1)
        L.append(f"| {rep} | {rung} | {real:.1%} | {np.median(plc):.1%} | {np.percentile(plc, 2.5):.1%} to "
                 f"{np.percentile(plc, 97.5):.1%} | {np.percentile(plc, 95):.1%} | {p:.3f} | "
                 f"{'yes' if real > np.percentile(plc, 95) else 'no'} |")
        for emu, h in g.groupby("EMU", sort=False):
            rr = 1 - h.m_arm / h.m_ref
            r0, pl = float(rr[h.draw == -1].iloc[0]), rr[h.draw >= 0].to_numpy()
            per.append(f"| {rep} | {rung} | {emu} | {r0:.1%} | {np.median(pl):.1%} | {np.percentile(pl, 2.5):.1%} to "
                       f"{np.percentile(pl, 97.5):.1%} | {(1 + int((pl >= r0).sum())) / (len(pl) + 1):.3f} |")
    L += ["", "## Per emulation", "", "| representation | on | emulation | real | placebo median | placebo 2.5-97.5% | P |",
          "|---|---|---|---|---|---|---|"] + per
    L += ["", "Pre-specified criterion: beyond chance if the real pooled reduction exceeds the placebo 95th percentile. "
          "Post hoc, exploratory; locked endpoints unchanged."]
    (out / "report_noise.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    BC.log(f"done in {time.time() - t0:.0f} s; outputs (aggregate) {out}")


# ---------------------------------------------------------------- test 2: cross-validated information
def cv_r2(X, y, groups, folds=5):
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import GroupKFold
    from sklearn.preprocessing import StandardScaler
    pred = np.empty(len(y))
    for tr, te in GroupKFold(n_splits=folds).split(X, y, groups):
        sc = StandardScaler().fit(X[tr])
        m = RidgeCV(alphas=np.logspace(-2, 4, 13)).fit(sc.transform(X[tr]), y[tr])
        pred[te] = m.predict(sc.transform(X[te]))
    return float(1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2))


def cap_people(D, cap, seed):
    if len(D) <= cap:
        return D
    ids = D.id.drop_duplicates().to_numpy()
    ids = ids[np.random.default_rng(seed).permutation(len(ids))]
    n = D.groupby("id").size().reindex(ids).to_numpy()
    keep = set(ids[np.cumsum(n) <= cap])
    return D[D.id.isin(keep)]


def cmd_info(a) -> None:
    t0 = time.time()
    R, ecols, K, reps = load()
    items = list(CH.HELD)
    rows = []
    for emu, D in R.groupby("EMU", sort=False):
        D = D.reset_index(drop=True)
        if not feasible(D):
            continue
        # features on the full emulation (as the PS arms see them), then the fixed person sample
        Fb = CE.design_matrix(D, CE.BASE)
        Fk = np.c_[Fb, CE.code_matrix(D, K).to_numpy(float)]
        mats = {"ecg": pcs(D[ecols].to_numpy(float), CE.N_PCS)}
        mats.update({n: pcs(D[c].to_numpy(float), min(64, len(c))) for n, c in reps.items()})
        keep = cap_people(D, a.cap, SEED_INFO).index.to_numpy()
        Dk = D.loc[keep]
        g = Dk.id.to_numpy()
        for it in items:
            y_all = pd.to_numeric(Dk[it], errors="coerce").to_numpy(float)
            ok = np.isfinite(y_all)
            if ok.sum() < 200 or len(np.unique(g[ok])) < 10:
                continue
            y, gg, sel = y_all[ok], g[ok], keep[ok]
            r_base = cv_r2(Fb[sel], y, gg)
            r_codes = cv_r2(Fk[sel], y, gg)
            for rep, M in mats.items():
                rec = dict(EMU=emu, item=it, n=BC.suppress(int(ok.sum())), rep=rep, r2_base=r_base, r2_codes=r_codes,
                           r2_base_x=cv_r2(np.c_[Fb[sel], M[sel]], y, gg), r2_codes_x=cv_r2(np.c_[Fk[sel], M[sel]], y, gg))
                for d in range(a.draws):
                    Mp = M[np.random.default_rng(SEED_INFO + 1 + d).permutation(len(M))]
                    rec[f"r2_codes_perm{d}"] = cv_r2(np.c_[Fk[sel], Mp[sel]], y, gg)
                rows.append(rec)
        BC.log(f"{emu}: information test done ({time.time() - t0:.0f} s)")
    I = pd.DataFrame(rows)
    out = BC.out_root() / "chs_ehr_tests"
    out.mkdir(parents=True, exist_ok=True)
    I.to_csv(out / "info.csv", index=False)
    pc = [c for c in I.columns if c.startswith("r2_codes_perm")]
    L = [f"# CHS test 2: cross-validated information beyond PS-Codes (EXPLORATORY, pre-specified) "
         f"({time.strftime('%Y-%m-%d %H:%M')}, git {BC.git_sha()[:10]})", "",
         f"- ridge, 5-fold CV grouped by person; E5/E6 capped at {a.cap} rows (fixed person sample); {a.draws} permutations",
         "- dR2 = R2(PS-Codes + X) - R2(PS-Codes) per emulation x held-out item cell", "",
         "| X | cells | mean R2 PS-Codes | mean dR2 (real) | placebo mean dR2: median / 95th | (a) | cells dR2 > placebo max | (b) | adds information |",
         "|---|---|---|---|---|---|---|---|---|"]
    for rep, g in I.groupby("rep", sort=False):
        d_real = g.r2_codes_x - g.r2_codes
        d_plc = g[pc].sub(g.r2_codes, axis=0)
        means = d_plc.mean(0).to_numpy()
        crit_a = float(d_real.mean()) > np.percentile(means, 95)
        share = float((d_real > d_plc.max(1)).mean())
        crit_b = share >= 0.5
        L.append(f"| {rep} | {len(g)} | {g.r2_codes.mean():.3f} | {d_real.mean():+.4f} | {np.median(means):+.4f} / "
                 f"{np.percentile(means, 95):+.4f} | {'yes' if crit_a else 'no'} | {share:.0%} | {'yes' if crit_b else 'no'} | "
                 f"**{'yes' if crit_a and crit_b else 'no'}** |")
    L += ["", "## Context: increments on top of PS-Base only (no placebo)", "",
          "| X | mean R2 PS-Base | mean R2 PS-Base + X | mean R2 PS-Codes | mean R2 PS-Codes + X |", "|---|---|---|---|---|"]
    for rep, g in I.groupby("rep", sort=False):
        L.append(f"| {rep} | {g.r2_base.mean():.3f} | {g.r2_base_x.mean():.3f} | {g.r2_codes.mean():.3f} | {g.r2_codes_x.mean():.3f} |")
    L += ["", "## dR2 beyond PS-Codes by domain (mean over emulations)", ""]
    I["domain"] = I["item"].map(CH.DOMAIN)
    tab = I.assign(d=I.r2_codes_x - I.r2_codes).pivot_table(index="domain", columns="rep", values="d", aggfunc="mean")
    L += [CE_md(tab.round(4)), "", "Pre-specified criterion: adds information if (a) and (b) both hold. Post hoc, exploratory."]
    (out / "report_info.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    BC.log(f"done in {time.time() - t0:.0f} s; outputs (aggregate) {out}")


def CE_md(df) -> str:
    try:
        return df.to_markdown()
    except ImportError:
        return "```\n" + df.to_string() + "\n```"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    n = sp.add_parser("noise")
    n.add_argument("--draws", type=int, default=50)
    i = sp.add_parser("info")
    i.add_argument("--draws", type=int, default=10)
    i.add_argument("--cap", type=int, default=INFO_CAP)
    a = ap.parse_args(argv)
    {"noise": cmd_noise, "info": cmd_info}[a.cmd](a)


if __name__ == "__main__":
    main()
