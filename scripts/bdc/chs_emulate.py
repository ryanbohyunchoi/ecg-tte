#!/usr/bin/env python
"""CHS emulations (docs/bdc/CHS_PROTOCOL.md): per emulation, PS arms -> 1:1 caliper matching -> balance on the held-out
panel and Cox HR vs the RCT benchmark, with the paper's estimator (scripts/v13_common.ps_logit / match / cox).

Arms: crude, PS-Base, PS-Base + ECG, PS-Base + permuted ECG, PS-Clinical, PS-Clinical + ECG, PS-Codes (PS-Base + top-200
ICD-9 hospital codes and medication flags before visit k-1, hdPS-like), PS-Codes + ECG.
ECG = BCL 256-d -> 32 PCs within each emulation. Held-out balance: |SMD| per item over items observed in >= 11 participants
of each matched arm; PS-Clinical masks its own inputs and any item with |rho| >= 0.80 with one of them.

Inputs (restricted, BDC): chs_emulations.parquet (chs_cohort.py) and chs_ecg_bcl.parquet (ecg_bcl.py embed --name chs).
Outputs (aggregate): <out>/chs_emulate/<run>/cells.csv, summary.csv, report.md (counts 1-10 suppressed).

Refuses to run unless --protocol-locked is given (no ECG-adjusted estimate before the protocol is locked).
Usage: python scripts/bdc/chs_emulate.py --protocol-locked [--run main]
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
from fig5_sprint import impute, smd_abs  # noqa: E402
try:
    from eval_longtail_balance import pcs  # noqa: E402
    from v13_common import cox, match, ps_logit  # noqa: E402
except ImportError as e:  # pragma: no cover
    raise SystemExit(f"{e}: install lifelines + scikit-learn (see docs/bdc) first")

S = BC.suppress
N_PCS = 32
SEED_PERM = 424242
BASE = ["AGE", "MALE", "BLACK", "HTN", "DIAB", "CAD", "AF", "HF"]
CLIN_EXTRA = CH.CLINICAL_PS + ["SMOKE"]
BENCH_HR = {"E1_ccb_vs_thiazide": 0.98, "E1b_dhp_vs_thiazide": 0.98, "E2_acei_vs_thiazide": 0.99, "E3_acei_vs_ccb": None,
            "E4_thiazide_vs_beta": None, "E5_statin_vs_none": 0.85, "E6_aspirin_vs_none": 0.95}
OUTS = ["primary", "death", "hf", "mi", "stroke"]


def _read(p: Path) -> pd.DataFrame:
    for q in (p.with_suffix(".parquet"), p.with_suffix(".pkl")):
        if q.exists():
            return pd.read_parquet(q) if q.suffix == ".parquet" else pd.read_pickle(q)
    raise SystemExit(f"missing {p}.parquet/.pkl")


def design_matrix(D: pd.DataFrame, cols: list) -> np.ndarray:
    cols = [c for c in cols if c in D and pd.to_numeric(D[c], errors="coerce").notna().any()]
    X = impute(D, cols)
    vis = pd.get_dummies(D.k.astype(int), prefix="k", drop_first=True).to_numpy(float)  # calendar proxy
    return np.c_[X, vis] if vis.size else X


def masked_items(D: pd.DataFrame, ps_cols: list) -> set:
    """Held-out items that are PS inputs or have |Spearman rho| >= 0.80 with one (paper leakage rule)."""
    m = {c for c in CH.HELD if c in ps_cols}
    for it in CH.HELD:
        if it in m:
            continue
        for c in ps_cols:
            if c not in D or c == it:
                continue
            r = pd.concat([pd.to_numeric(D[it], errors="coerce"), pd.to_numeric(D[c], errors="coerce")], axis=1).dropna()
            if len(r) > 50 and abs(r.corr(method="spearman").iloc[0, 1]) >= 0.80:
                m.add(it)
                break
    return m


def balance(V: np.ndarray, items: list, t: np.ndarray, idx: np.ndarray, mask: set) -> dict:
    d = smd_abs(V, t, idx)
    st = t[idx]
    obs1 = (~np.isnan(V[idx][st == 1])).sum(0)
    obs0 = (~np.isnan(V[idx][st == 0])).sum(0)
    keep = [j for j, it in enumerate(items) if it not in mask and obs1[j] >= 11 and obs0[j] >= 11 and np.isfinite(d[j])]
    vals = {items[j]: float(d[j]) for j in keep}
    out = dict(mean_smd=float(np.mean(list(vals.values()))) if vals else np.nan, n_items=len(vals),
               pct_lt_0_1=float(np.mean([v < 0.1 for v in vals.values()])) if vals else np.nan)
    for dom in sorted({CH.DOMAIN(i) for i in items}):
        dv = [v for k, v in vals.items() if CH.DOMAIN(k) == dom]
        out[f"mean_smd_{dom}"] = float(np.mean(dv)) if dv else np.nan
    out.update({f"smd:{k}": v for k, v in vals.items()})
    return out


def code_matrix(D: pd.DataFrame, K: pd.DataFrame, top: int = 200, min_n: int = 20) -> pd.DataFrame:
    """PS-Codes inputs: binary code indicators for this emulation's rows, codes present in >= min_n people, ranked by
    |log prevalence ratio| between arms (treatment-only ranking, as in the paper's hdPS), top 200."""
    k = K[K.row.isin(set(D.row))]
    if not len(k):
        return pd.DataFrame(index=D.index)
    X = pd.crosstab(k.row, k.code).clip(upper=1).reindex(D.row).fillna(0)
    X.index = D.index
    X = X.loc[:, X.sum() >= min_n]
    if not X.shape[1]:
        return X
    t = D.arm.to_numpy()
    p1 = (X[t == 1].sum() + 0.5) / ((t == 1).sum() + 1)
    p0 = (X[t == 0].sum() + 0.5) / ((t == 0).sum() + 1)
    order = np.abs(np.log(p1 / p0)).sort_values(ascending=False).index[:top]
    return X[order]


def run_emulation(D: pd.DataFrame, P: np.ndarray, Xk: pd.DataFrame | None = None, Q: np.ndarray | None = None) -> list:
    t = D.arm.to_numpy(int)
    items = list(CH.HELD)
    V = np.column_stack([pd.to_numeric(D[c], errors="coerce").to_numpy(float) for c in items])
    Pp = P[np.random.default_rng(SEED_PERM).permutation(len(P))]
    Xb = design_matrix(D, BASE)
    clin_cols = BASE + [c for c in CLIN_EXTRA if c in D]
    Xc = design_matrix(D, clin_cols)
    mask_c = masked_items(D, clin_cols)
    arms = {"base": (Xb, set()), "base+ecg": (np.c_[Xb, P], set()), "base+perm": (np.c_[Xb, Pp], set()),
            "clinical": (Xc, mask_c), "clinical+ecg": (np.c_[Xc, P], mask_c)}
    if Q is not None:  # EXPLORATORY AI-EHR arms (--ehr): representation PCs, alone with base, with base + ECG, permuted
        Qp = Q[np.random.default_rng(SEED_PERM + 1).permutation(len(Q))]
        arms["base+ehr"] = (np.c_[Xb, Q], set())
        arms["base+ecg+ehr"] = (np.c_[Xb, P, Q], set())
        arms["base+permehr"] = (np.c_[Xb, Qp], set())
    if Xk is not None and Xk.shape[1]:
        Dk = pd.concat([D, Xk.add_prefix("code:")], axis=1)
        mask_k = masked_items(Dk, list(Xk.add_prefix("code:").columns))
        arms["codes"] = (np.c_[Xb, Xk.to_numpy(float)], mask_k)
        arms["codes+ecg"] = (np.c_[Xb, Xk.to_numpy(float), P], mask_k)
    rows = []
    idx_all = np.arange(len(D))
    r = dict(arm="crude", n_pairs=np.nan, **balance(V, items, t, idx_all, set()))
    for o in OUTS:
        b, se = cox(D[f"T_{o}"].to_numpy(float), D[f"E_{o}"].to_numpy(int), t)
        r.update({f"loghr_{o}": b, f"se_{o}": se, f"events_{o}": int(D[f"E_{o}"].sum())})
    rows.append(r)
    for arm, (X, mask) in arms.items():
        lg = ps_logit(X, t)
        idx, cl, _w = match(lg, t, cal=0.2, ratio=1)
        r = dict(arm=arm, n_pairs=int(len(np.unique(cl))), **balance(V, items, t, idx, mask))
        for o in OUTS:
            b, se = cox(D[f"T_{o}"].to_numpy(float)[idx], D[f"E_{o}"].to_numpy(int)[idx], t[idx], cluster=cl)
            r.update({f"loghr_{o}": b, f"se_{o}": se, f"events_{o}": int(D[f"E_{o}"].to_numpy(int)[idx].sum())})
        # sensitivity: SE clustered on person (sequential trials reuse people across visits and arms)
        pid = pd.factorize(D.id.to_numpy()[idx])[0]
        _, r["se_primary_person"] = cox(D.T_primary.to_numpy(float)[idx], D.E_primary.to_numpy(int)[idx], t[idx], cluster=pid)
        rows.append(r)
    return rows


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--protocol-locked", action="store_true", help="required: confirms docs/bdc/CHS_PROTOCOL.md is LOCKED")
    ap.add_argument("--run", default="main")
    ap.add_argument("--ehr", choices=["", "backbone", "clmbr", "clmbr_rich"], default="",
                    help="EXPLORATORY: add AI-EHR arms from chs_ehr_backbone (crude backbone) or chs_clmbr (CLMBR-T)")
    a = ap.parse_args(argv)
    if not a.protocol_locked:
        raise SystemExit("refusing to compute ECG-adjusted estimates: lock docs/bdc/CHS_PROTOCOL.md first, then pass "
                         "--protocol-locked")
    t0 = time.time()
    rd = Path(os.environ.get("BDC_RESTRICTED", "/sbgenomics/workspace/bdc-restricted"))
    R = _read(rd / "chs_emulations")
    E = _read(rd / "chs_ecg_bcl")
    ecols = [c for c in E.columns if c.startswith("e") and c[1:].isdigit()]
    R = R.merge(E[["id", "ECG_FILE"] + ecols], on=["id", "ECG_FILE"], how="inner")
    try:
        K = _read(rd / "chs_codes")
    except SystemExit:
        K = None
        BC.log("no chs_codes table: PS-Codes arms skipped")
    qcols = []
    if a.ehr:
        Qd = _read(rd / ("chs_ehr_backbone" if a.ehr == "backbone" else f"chs_{a.ehr}"))
        qcols = [c for c in Qd.columns if c != "row"]
        R = R.merge(Qd.rename(columns={c: f"q:{c}" for c in qcols}), on="row", how="inner")
        qcols = [f"q:{c}" for c in qcols]
        BC.log(f"EXPLORATORY --ehr {a.ehr}: {len(qcols)} dims merged")
    cells = []
    for emu, D in R.groupby("EMU", sort=False):
        D = D.reset_index(drop=True)
        if min((D.arm == 1).sum(), (D.arm == 0).sum()) < 350:
            cells.append(dict(EMU=emu, arm="(infeasible)", n_A=S(int((D.arm == 1).sum())), n_B=S(int((D.arm == 0).sum()))))
            continue
        P = pcs(D[ecols].to_numpy(float), N_PCS)
        Xk = code_matrix(D, K) if K is not None and "row" in D else None
        Q = pcs(D[qcols].to_numpy(float), min(64, len(qcols))) if qcols else None
        for r in run_emulation(D, P, Xk, Q):
            r.update(EMU=emu, cluster=D.cluster.iloc[0], n_A=int((D.arm == 1).sum()), n_B=int((D.arm == 0).sum()),
                     bench_hr=BENCH_HR.get(emu), n_code_features=0 if Xk is None else int(Xk.shape[1]))
            cells.append(r)
        BC.log(f"{emu}: done ({time.time() - t0:.0f} s)")
    C = pd.DataFrame(cells)
    for c in [c for c in C.columns if c.startswith(("events_", "n_A", "n_B", "n_pairs"))]:
        C[c] = C[c].map(lambda v: S(v) if isinstance(v, (int, np.integer)) or (isinstance(v, float) and np.isfinite(v) and v == int(v)) else v)
    out = BC.out_root() / "chs_emulate" / a.run
    out.mkdir(parents=True, exist_ok=True)
    C.to_csv(out / "cells.csv", index=False)
    # summary: relative reduction in mean held-out |SMD| with the ECG, per emulation and pooled
    L = [f"# CHS emulations `{a.run}` ({time.strftime('%Y-%m-%d %H:%M')}, git {BC.git_sha()[:10]})", "",
         "| emulation | arm | pairs | mean \\|SMD\\| held-out | echo | lab | vital | % items <0.1 | primary events | HR (95% CI) | RCT |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    ok = C[C.arm != "(infeasible)"]
    for r in ok.itertuples():
        b, se = getattr(r, "loghr_primary"), getattr(r, "se_primary")
        hr = f"{np.exp(b):.2f} ({np.exp(b - 1.96 * se):.2f}-{np.exp(b + 1.96 * se):.2f})" if np.isfinite(b) else "n/a"
        L.append(f"| {r.EMU} | {r.arm} | {r.n_pairs} | {r.mean_smd:.3f} | {getattr(r, 'mean_smd_echo', np.nan):.3f} | "
                 f"{getattr(r, 'mean_smd_lab', np.nan):.3f} | {getattr(r, 'mean_smd_vital', np.nan):.3f} | {r.pct_lt_0_1:.0%} | "
                 f"{r.events_primary} | {hr} | {r.bench_hr} |")
    L += ["", "## Relative reduction in mean held-out |SMD| with the ECG (items observed in both arms)", ""]
    smdcols = [c for c in C.columns if c.startswith("smd:")]
    pairs = [("base", "base+ecg"), ("base", "base+perm"), ("clinical", "clinical+ecg"), ("codes", "codes+ecg")]
    if a.ehr:
        pairs += [("base", "base+ehr"), ("base", "base+permehr"), ("base+ecg", "base+ecg+ehr"), ("base+ehr", "base+ecg+ehr"),
                  ("codes", "base+ehr")]
    for ref, arm in pairs:
        per, means = [], []
        for emu, g in ok.groupby("EMU", sort=False):
            g = g.set_index("arm")
            if ref in g.index and arm in g.index:
                common = [c for c in smdcols if np.isfinite(g.loc[ref, c]) and np.isfinite(g.loc[arm, c])]
                mr, ma = float(np.mean(g.loc[ref, common])), float(np.mean(g.loc[arm, common]))
                per.append((emu, g.loc[ref, "cluster"], 1 - ma / mr))
                means.append((mr, ma))
        if per:
            pooled = 1 - np.mean([m[1] for m in means]) / np.mean([m[0] for m in means])
            # exact one-sided sign-flip over comparator clusters (cluster mean of per-emulation reductions)
            cl = pd.DataFrame(per, columns=["EMU", "cluster", "rr"]).groupby("cluster").rr.mean().to_numpy()
            flips = np.array(np.meshgrid(*[[1, -1]] * len(cl))).reshape(len(cl), -1).T
            p1 = float(np.mean((flips * cl).mean(1) >= cl.mean() - 1e-12))
            L.append(f"- {arm} vs {ref}: pooled {pooled:.1%}; clusters {len(cl)}, sign-flip one-sided P = {p1:.3f} "
                     f"(minimum possible {1 / 2 ** len(cl):.3f}); " + "; ".join(f"{e} {v:.1%}" for e, _, v in per))
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    BC.log(f"done in {time.time() - t0:.0f} s; outputs (aggregate) {out}")


if __name__ == "__main__":
    main()
