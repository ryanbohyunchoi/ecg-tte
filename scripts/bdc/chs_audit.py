#!/usr/bin/env python
"""CHS audit + echo/structure balance (POST HOC, descriptive; docs/bdc/CHS_PROTOCOL.md is locked and unchanged).

Re-runs the locked chs_emulate.py matching (deterministic: same PS, PCs, permutation seed and greedy matching) and reports:
  1. integrity checks per emulation: time zero after the visit k-1 day; ECG file from visit k-1 (label k-2); people in
     both arms; repeated people (sequential trials); PS c-statistic and share of the smaller arm matched; primary-outcome
     event rates per 1,000 person-years; crude Cox (lifelines, v13_common.cox) vs an independent numpy Cox; and that the
     re-run reproduces the locked cells.csv balance.
  2. per-item echo balance (structure: LV mass, septal and posterior wall thickness, LA dimension; function: LV function
     grade, E/A) for every arm, with a CHANCE FLOOR: the mean |SMD| expected if arm labels were assigned at random within
     the same matched sample (200 label permutations; 95th percentile also given).
  3. directional consistency: across emulation x echo item cells, how often adding the ECG lowers |SMD| vs the same PS
     without it, and vs the permuted-ECG placebo (counts and a descriptive two-sided sign test).

Inputs (restricted, BDC): chs_emulations, chs_ecg_bcl, chs_codes. Output (aggregate): <out>/chs_audit/report.md, echo.csv.
Usage: python scripts/bdc/chs_audit.py
"""
from __future__ import annotations

import math
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
from fig5_sprint import smd_abs  # noqa: E402
from sprint_cohort import cox_binary  # noqa: E402
from eval_longtail_balance import pcs  # noqa: E402
from v13_common import cox, match, ps_logit  # noqa: E402

S = BC.suppress
STRUCT = ["echo_lv_mass", "echo_septum", "echo_post_wall", "echo_la_dim"]
FUNC = ["echo_lv_function", "echo_e_a"]
ECHO = STRUCT + FUNC
N_PERM = 200
PAIRS = [("base", "base+ecg"), ("clinical", "clinical+ecg"), ("codes", "codes+ecg")]


def cstat(lg, t):
    from scipy.stats import rankdata
    r = rankdata(lg)
    n1 = t.sum()
    return float((r[t == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(t) - n1)))


def _smd_fixed_sd(V, sd, lab, idx):
    S_, st = V[idx], lab[idx]
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.abs(np.nanmean(S_[st == 1], axis=0) - np.nanmean(S_[st == 0], axis=0)) / sd
    d[~np.isfinite(sd) | (sd == 0)] = np.nan
    return d


def chance_floor(V, t, idx, rng):
    """Mean (and 95th percentile) |SMD| per column when the arm labels are permuted within the matched sample; the
    denominator is the real pre-match pooled SD (as in the observed SMD), so only chance assignment varies."""
    with np.errstate(invalid="ignore"):
        sd = np.sqrt((np.nanvar(V[t == 1], axis=0, ddof=1) + np.nanvar(V[t == 0], axis=0, ddof=1)) / 2)
    st = t[idx]
    A = []
    for _ in range(N_PERM):
        lab = t.copy()
        lab[idx] = rng.permutation(st)
        A.append(_smd_fixed_sd(V, sd, lab, idx))
    A = np.array(A)
    return np.nanmean(A, axis=0), np.nanpercentile(A, 95, axis=0)


def md(df, **kw) -> str:
    try:
        return df.to_markdown(**kw)
    except ImportError:  # no tabulate on the platform
        return "```\n" + df.to_string(**{k: v for k, v in kw.items() if k == "index"}) + "\n```"


def sign_p(k, n):
    """Two-sided exact sign test P for k successes out of n (descriptive)."""
    if n == 0:
        return float("nan")
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main(argv=None) -> None:
    t0 = time.time()
    rd = Path(os.environ.get("BDC_RESTRICTED", "/sbgenomics/workspace/bdc-restricted"))
    R = CE._read(rd / "chs_emulations")
    E = CE._read(rd / "chs_ecg_bcl")
    ecols = [c for c in E.columns if c.startswith("e") and c[1:].isdigit()]
    n_before = len(R)
    R = R.merge(E[["id", "ECG_FILE"] + ecols], on=["id", "ECG_FILE"], how="inner")
    try:
        K = CE._read(rd / "chs_codes")
    except SystemExit:
        K = None
    locked = BC.out_root() / "chs_emulate" / "main" / "cells.csv"
    L0 = pd.read_csv(locked) if locked.exists() else None
    integ, echo_rows = [], []
    rng = np.random.default_rng(20261019)
    for emu, D in R.groupby("EMU", sort=False):
        D = D.reset_index(drop=True)
        t = D.arm.to_numpy(int)
        if min(t.sum(), (1 - t).sum()) < 350:
            integ.append(dict(EMU=emu, note="infeasible (< 350): not analysed"))
            continue
        P = pcs(D[ecols].to_numpy(float), CE.N_PCS)
        Pp = P[np.random.default_rng(CE.SEED_PERM).permutation(len(P))]
        Xb = CE.design_matrix(D, CE.BASE)
        clin_cols = CE.BASE + [c for c in CE.CLIN_EXTRA if c in D]
        Xc = CE.design_matrix(D, clin_cols)
        Xk = CE.code_matrix(D, K) if K is not None and "row" in D else None
        arms = {"base": Xb, "base+ecg": np.c_[Xb, P], "base+perm": np.c_[Xb, Pp], "clinical": Xc, "clinical+ecg": np.c_[Xc, P]}
        if Xk is not None and Xk.shape[1]:
            arms["codes"] = np.c_[Xb, Xk.to_numpy(float)]
            arms["codes+ecg"] = np.c_[Xb, Xk.to_numpy(float), P]
        V = np.column_stack([pd.to_numeric(D[c], errors="coerce").to_numpy(float) for c in ECHO])
        Vall = np.column_stack([pd.to_numeric(D[c], errors="coerce").to_numpy(float) for c in CH.HELD])
        # ---- integrity
        lab = D.ECG_FILE.astype(str).str.extract(r"VISIT(\d+)_")[0].astype(float)
        both = len(set(D.id[t == 1]) & set(D.id[t == 0]))
        py = D.T_primary.clip(lower=0) / 365.25
        b_l, _ = cox(D.T_primary.to_numpy(float), D.E_primary.to_numpy(int), t)
        hr_np = cox_binary(D.T_primary, D.E_primary, D.arm)[0]
        rec = dict(EMU=emu, n_rows=S(len(D)), t0_after_k1_day=float((D.day0 > D.day_k1).mean()),
                   ecg_from_visit_k1=float((lab == D.k1 - 1).mean()), people_in_both_arms=S(both),
                   rows_per_person_max=int(D.groupby("id").size().max()),
                   rate_A_per_1000py=round(1000 * D.E_primary[t == 1].sum() / py[t == 1].sum(), 1),
                   rate_B_per_1000py=round(1000 * D.E_primary[t == 0].sum() / py[t == 0].sum(), 1),
                   crude_hr_lifelines=round(float(np.exp(b_l)), 3), crude_hr_numpy_breslow=round(hr_np, 3))
        idxs = {}
        for arm, X in arms.items():
            lg = ps_logit(X, t)
            idx, cl, _w = match(lg, t, cal=0.2, ratio=1)
            idxs[arm] = idx
            rec[f"cstat_{arm}"] = round(cstat(lg, t), 3)
            rec[f"pairs_{arm}"] = S(len(np.unique(cl)))
            if L0 is not None and arm in ("base", "base+ecg"):
                g = L0[(L0.EMU == emu) & (L0.arm == arm)]
                if len(g):
                    redo = CE.balance(Vall, list(CH.HELD), t, idx, set())["mean_smd"]
                    rec[f"reproduces_locked_{arm}"] = bool(abs(redo - float(g.mean_smd.iloc[0])) < 1e-9)
        rec["smaller_arm_matched_base"] = round(len(idxs["base"]) / 2 / min(t.sum(), (1 - t).sum()), 3)
        integ.append(rec)
        # ---- echo per item with chance floor
        for arm, idx in idxs.items():
            d = smd_abs(V, t, idx)
            fl_mean, fl_95 = chance_floor(V, t, idx, rng)
            st = t[idx]
            for j, it in enumerate(ECHO):
                n1 = int((~np.isnan(V[idx][st == 1, j])).sum())
                n0 = int((~np.isnan(V[idx][st == 0, j])).sum())
                echo_rows.append(dict(EMU=emu, arm=arm, item=it, group="structure" if it in STRUCT else "function",
                                      smd=float(d[j]) if n1 >= 11 and n0 >= 11 else np.nan, chance_mean=float(fl_mean[j]),
                                      chance_p95=float(fl_95[j]), n_A=S(n1), n_B=S(n0)))
        BC.log(f"{emu}: audited ({time.time() - t0:.0f} s)")
    I = pd.DataFrame(integ)
    Q = pd.DataFrame(echo_rows)
    out = BC.out_root() / "chs_audit"
    out.mkdir(parents=True, exist_ok=True)
    I.to_csv(out / "integrity.csv", index=False)
    Q.to_csv(out / "echo.csv", index=False)
    # ---- directional consistency
    L = [f"# CHS audit + echo balance (POST HOC, descriptive) ({time.strftime('%Y-%m-%d %H:%M')}, git {BC.git_sha()[:10]})", "",
         f"- rows in chs_emulations {S(n_before)}; with an ECG embedding {S(len(R))}", "", "## 1. Integrity", ""]
    L += [md(I, index=False), ""]
    L += ["## 2. Echo balance per item (|SMD| after matching; chance = mean |SMD| under random labels in the same matched sample)", ""]
    W = Q.pivot_table(index=["EMU", "item"], columns="arm", values="smd")
    F = Q.pivot_table(index=["EMU", "item"], columns="arm", values="chance_mean")
    cols = [c for c in ["base", "base+ecg", "base+perm", "clinical", "clinical+ecg", "codes", "codes+ecg"] if c in W.columns]
    T2 = W[cols].round(3)
    T2["chance(base)"] = F["base"].round(3)
    L += [md(T2), ""]
    L += ["## 3. Directional consistency (cells = emulation x echo item)", ""]
    for ref, arm in PAIRS + [("base+perm", "base+ecg")]:
        if ref not in W or arm not in W:
            continue
        for grp, items in (("all echo", ECHO), ("structure", STRUCT), ("function", FUNC)):
            sub = W[W.index.get_level_values("item").isin(items)][[ref, arm]].dropna()
            k, n = int((sub[arm] < sub[ref]).sum()), len(sub)
            L.append(f"- {arm} lower than {ref}, {grp}: {k}/{n} cells (sign test P = {sign_p(k, n):.2f}); "
                     f"mean |SMD| {sub[ref].mean():.3f} -> {sub[arm].mean():.3f}")
    above = (W["base"] > F["base"]).mean() if "base" in W else np.nan
    L += ["", f"- share of echo cells where the PS-Base matched |SMD| exceeds its chance floor: {above:.0%}",
          "", "All of sections 2-3 is post hoc and descriptive; the locked primary endpoint is unchanged."]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    BC.log(f"done in {time.time() - t0:.0f} s; outputs (aggregate) {out}")


if __name__ == "__main__":
    main()
