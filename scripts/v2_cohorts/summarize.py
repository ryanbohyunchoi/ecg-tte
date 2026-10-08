#!/usr/bin/env python
"""Spec-v2 cohort summaries: version 1 cohorts vs spec-v2 cohorts, side by side, with the settled pipeline endpoints.

Cohorts: v1 (version 1 cells: claude-v21-paper2 core, claude-v1-ps10, claude-v1-psclin-nolvef), v2 (PRIMARY: spec-v2 rules,
PCs within the fixed cohort), v2old (v2 rows, version 1 PCs), v2meas (numeric bounds / COMET LVEF required measured).
Sets: S32 (paper 1), S29 (provisional framework-v2.0 set, quality_v2_final.json analysed_set), S38.
Masks (pipeline.md section 6, leakage-corrected): a cell's mask = rung mask | arm mask (placebos take the real arm's mask)
  P1: none | P5, Flags: B_mean, prognostic score | PS10: = scripts/v1_ps10 mask_rung | hdPS200: 4 coded items |
  clinical (v1, with LVEF): coded 4 + 9 observed + eGFR, echo EF, LV systolic grade | clinical_nolvef: coded 4 + 8 observed
  (not LVEF) + eGFR | CLMBR arms: 4 coded items.  On the 54 non-coded items only the clinical rungs mask anything.
F1 rule: a cell with < 11 matched pairs or a failed fit is failed (all its endpoints missing).
Endpoints and tests (paper2_grid._row, unchanged): relative reduction in mean |SMD| over the 54 items (PRIMARY) and the 58,
  4,000-resample trial bootstrap (seed 20261001); exact sign-flip across trials (one-sided for a representation vs its base or
  placebo; two-sided for head-to-heads, base-to-base and placebo-vs-base); |dlog HR| vs RCT with sign-flip P and the
  benchmark-permutation P (20,000 draws; two-sided analogue for two-sided contrasts); per-domain relative reductions.
  BH-FDR within (cohort, set) over the within-rung contrasts x configurations (balance family = paper2 BAL_FAM).

Usage: summarize.py run [--workers 32] [--cohorts v1,v2,v2old,v2meas]   -> OUT/summary/contrasts.csv, domains.csv,
       ladder.csv, failed_cells.csv, per_trial.csv;    summarize.py tables -> OUT/summary/tables.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2common as K  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import grid as GR  # noqa: E402
import ps10 as P10  # noqa: E402
import psclin_nolvef as PSC  # noqa: E402

P2, SP, E, V = K.P2, K.SP, K.E, K.V
VN, NONCODED, GROUP = K.VN, K.NONCODED, K.GROUP
MASK_RUNG = dict(PSC.MASK_RUNG)
MASK_RUNG["PS10"] = P10.mask_rung()["PS10"]
MASK_ARM = PSC.MASK_ARM
LABEL = {"P1": "PS-Demo", "P5": "PS-CVD5", "PS10": "CVD10", "Flags": "PS-Flags", "hdPS200": "hdPS",
         "clinical": "PS-Clinical (with LVEF, v1)", "clinical_nolvef": "PS-Clinical (no LVEF)"}
WITHIN = PSC.WITHIN
ECHO = PSC.ECHO


def cells(cohort):
    if cohort == "v1":
        return GR.reference()
    return pd.read_parquet(K.CEL / f"restricted_cells_{cohort}_all.parquet")


def failed(g):
    return g.cell_failed.fillna("").astype(str).ne("") | (g.n_pairs.notna() & (g.n_pairs < K.MIN_CELL))


def load_F(R):
    F, SM, RET, NF = {}, {}, {}, []
    for (rg, cfg, a), g in R.groupby(["rung", "config", "arm"]):
        g = g.set_index("trial", drop=False).loc[[t for t in K.ALL if t in set(g.trial)]]
        Fk, Sk = SP.per_trial(g)
        f = failed(g).to_numpy()
        if f.any():
            Sk.loc[f, :] = np.nan
            Fk.loc[f, ["lt01", "m58", "absd", "cons", "ea", "loghr", "se"]] = np.nan
            NF += [(rg, cfg, a, t) for t in g.trial[f]]
        m = set(MASK_RUNG[rg]) | set(MASK_ARM.get(a, []))
        Sk.loc[:, [c for c in Sk.columns if c in m]] = np.nan
        F[(rg, cfg, a)], SM[(rg, cfg, a)] = Fk, Sk
        RET[(rg, cfg, a)] = g.retain.mask(P2.small_pairs(g))
    return F, SM, RET, NF


def contrasts():
    L = []
    for cfg in K.CONFIGS:
        for rg in K.RUNGS:
            for a, b, side in WITHIN:
                L.append((cfg, f"{rg}: {a} vs {b}", "within", rg, a, rg, b, side))
        for rg in ("P1", "PS10", "Flags", "hdPS200", "clinical_nolvef"):
            L.append((cfg, f"{rg} base vs P5 base", "base2base", rg, "base", "P5", "base", "two"))
        for ra, aa, rb, ab in (("P1", "CLMBR", "Flags", "base"), ("P5", "CLMBR", "hdPS200", "base"),
                               ("P5", "ECG+CLMBR", "hdPS200", "base"), ("P5", "CLMBR", "clinical_nolvef", "base"),
                               ("P5", "ECG+CLMBR", "clinical_nolvef", "base"), ("P5", "ECG", "clinical_nolvef", "base")):
            L.append((cfg, f"{ra}+{aa} vs {rb} {ab}", "across", ra, aa, rb, ab, "two"))
    for rg in K.C32_RUNGS:
        for a, b, side in (("CLMBR32", "base", "one"), ("CLMBR", "CLMBR32", "two")):
            L.append(("main", f"{rg}: {a} vs {b}", "clmbr32", rg, a, rg, b, side))
    return L


EXTRA_DOM = {"Echo, all 35 items": ECHO}


def _row(args):
    cohort, sname, c = args
    row, dom = P2._row((sname, c))
    cfg, lab, kind, ra, aa, rb, ab, side = c
    F, SM, CL = P2._G["F"], P2._G["SM"], P2._G["CL"]
    tr = P2._G["SETS"][sname]
    ka, kb = (ra, cfg, aa), (rb, cfg, ab)
    for g, cols in EXTRA_DOM.items():
        d = P2.bal_light(F[ka], F[kb], P2.mask(SM[ka], cols), P2.mask(SM[kb], cols), tr, side, CL, full=False)
        dom.append(dict(set=sname, config=cfg, contrast=lab, kind=kind, sided=side, domain=g, n_items=len(cols),
                        mean_a=d["m58_a"], mean_b=d["m58_b"], better=d["m58_better"], p=d["m58_p"],
                        lt01_a=d["lt01_a"], lt01_b=d["lt01_b"], lt01_p=d["lt01_p"],
                        relred=d["relred"], relred_lo=d["relred_lo"], relred_hi=d["relred_hi"], k=d["relred_k"]))
    a_, b_ = SM[ka].loc[tr, NONCODED], SM[kb].loc[tr, NONCODED]
    k = (a_.notna() & b_.notna()).sum(1)
    row["k_trials_54"] = int((k > 0).sum())
    row["items54_median"] = float(k[k > 0].median()) if (k > 0).any() else np.nan
    row["cohort"] = cohort
    for d_ in dom:
        d_["cohort"] = cohort
    return row, dom


def ladder_levels(SM, cohort):
    rows = []
    for sname, tr in K.SETS.items():
        for (rg, cfg, a), S in SM.items():
            for pn, cols in (("54", NONCODED), ("58", VN), ("echo35", ECHO)):
                X = S.loc[tr, cols]
                m = X.mean(1)
                rows.append(dict(cohort=cohort, set=sname, rung=rg, label=LABEL[rg], config=cfg, arm=a, panel=pn,
                                 k_trials=int(m.notna().sum()), mean_smd=float(m.mean()),
                                 pct_lt01=float((100 * (X < 0.1).sum(1) / X.notna().sum(1)).mean())))
    return rows


def per_trial_rows(F, SM, cohort):
    out = []
    for cfg in ("main",):
        for rg in K.RUNGS:
            for a in K.ARMS:
                k = (rg, cfg, a)
                S54 = SM[k][NONCODED]
                for t in K.ALL:
                    out.append(dict(cohort=cohort, trial=t, key=K.KEY[t], rung=rg, config=cfg, arm=a,
                                    m54=float(S54.loc[t].mean()), absd=F[k].loc[t, "absd"], loghr=F[k].loc[t, "loghr"],
                                    se=F[k].loc[t, "se"], rb=F[k].loc[t, "rb"]))
    return out


def run(workers, cohorts):
    from multiprocessing import get_context
    K.umask()
    K.SUM.mkdir(parents=True, exist_ok=True)
    S_all, D_all, L_all, NF_all, PT_all = [], [], [], [], []
    for cohort in cohorts:
        t0 = time.time()
        R = cells(cohort)
        F, SM, RET, NF = load_F(R)
        NF_all += [dict(cohort=cohort, rung=a, config=b, arm=c, trial=d) for a, b, c, d in NF]
        P2._G.update(F=F, SM=SM, CL=V.cluster_of(), RET=RET, SETS=K.SETS)
        jobs = [(cohort, s, c) for s in ("S38", "S32", "S29") for c in contrasts()]
        with get_context("fork").Pool(min(workers, len(jobs))) as p:
            res = p.map(_row, jobs, chunksize=2)
        S = pd.DataFrame([r for r, _ in res])
        D = pd.DataFrame([d for _, ds in res for d in ds])
        for sname in K.SETS:
            ms = (S.set == sname) & S.kind.eq("within")
            long = S.loc[ms, P2.BAL_FAM].stack(dropna=True)
            q = pd.Series(E.bh_fdr(long.to_numpy()), index=long.index).unstack()
            for c in P2.BAL_FAM:
                S.loc[ms, f"q_{c}_fam"] = q[c] if c in q else np.nan
        S_all.append(S)
        D_all.append(D)
        L_all += ladder_levels(SM, cohort)
        PT_all += per_trial_rows(F, SM, cohort)
        print(cohort, len(S), f"{time.time() - t0:.0f}s", flush=True)
    S = pd.concat(S_all, ignore_index=True)
    tag = "" if cohorts == ["v1", "v2", "v2old", "v2meas"] else "_" + "_".join(cohorts)
    S.to_csv(K.SUM / f"contrasts{tag}.csv", index=False)
    pd.concat(D_all, ignore_index=True).to_csv(K.SUM / f"domains{tag}.csv", index=False)
    pd.DataFrame(L_all).to_csv(K.SUM / f"ladder{tag}.csv", index=False)
    NFd = pd.DataFrame(NF_all)
    (NFd.groupby(["cohort", "rung", "config", "arm"]).size().rename("n_trials_failed").reset_index() if len(NFd) else NFd).to_csv(
        K.SUM / f"failed_cells{tag}.csv", index=False)
    pd.DataFrame(PT_all).to_csv(K.SUM / f"per_trial{tag}.csv", index=False)  # trial-level aggregates (no counts)
    print("written", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--cohorts", default="v1,v2,v2old,v2meas")
    a = ap.parse_args()
    run(min(a.workers, 32), a.cohorts.split(","))
