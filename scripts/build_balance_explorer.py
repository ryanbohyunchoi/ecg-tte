#!/usr/bin/env python
"""Build the standalone TRACE-ECG covariate balance explorer: docs/presentation/ecg_tte_balance_explorer_2026_10_08.html.

Based on the balance explorer slide of the 2026-10-01 lab deck (scripts/build_lab_deck.py, slide "s-bal" and its JS
"PANEL 1"); look, love plot and statistics are copied from there and extended with the paper 2 grid, six PS methods,
an information-ladder view, a method-comparison view, the 54-item panel and a leakage-corrected masking toggle.

Self-contained HTML (inline CSS/JS/SVG, no network resources). Embeds AGGREGATE data only: per-trial |SMD| for each
held-out characteristic (integers x 1e5), per-trial masking lists, trial names / area / quality tier / physiologic
label. No patient-level rows, no identifiers and no counts (no n, n_t, n_c, n_pairs, retention or ESS).

Sources (read-only):
  audits/claude-v21-paper2/core/restricted_cells.parquet   38 trials x 5 rungs x 6 arms x 6 configurations (main grid)
  audits/claude-v1-psclin-nolvef/cells/restricted_cells.parquet   rung clinical_nolvef = PS-Clinical without LVEF, re-imputed
                                                            (scripts/v1_psclin_nolvef/psclin_nolvef.py; user decision 2026-10-08)
  audits/claude-v1-psclin-nolvef/summary/{contrasts,ladder}.csv   Python summaries of that rung (validation targets)
  audits/claude-v1-ps10/cells/restricted_cells.parquet      rung PS10 = PS-CVD10 (PS-Demo + 10 fixed diagnoses; scripts/v1_ps10/ps10.py;
                                                            docs/v1_ps10/PS10.md; main-ladder comparison per pipeline.md section 4)
  audits/claude-v1-ps10/summary/{contrasts,levels}.csv      Python summaries of that grid (validation targets)
  docs/emulation_quality_v2/quality_v2_final.json           provisional v2 analysed set (29 trials; not frozen)
  audits/claude-v20-sens-primary32/restricted_cells.parquet paper 1 source (checked: identical where they overlap)
  audits/claude-v18-embed-compare/results.csv               unmatched |SMD| (rung 'none'); matched cells checked = grid
  audits/claude-v19-expanded-buckets/per_var_all_rungs.csv  expanded panel (main configuration only)
  audits/claude-v16-covars2b/dictionary.csv                 expanded-panel variable definitions
  scripts/make_acc_figure.VARS (= v16_engine.VARS)          58 held-out items, labels and groups
  docs/v19/quality_tiers.json, docs/paper/paper.md Table 1, docs/v21/TRIAL_LABELS.json   trial metadata
Rules: cells with fewer than 11 matched pairs (or failed fits) are treated as failed (all items missing; v1 audit F1).
Leakage-corrected masks: docs/v1_audit/DEFECT_IMPACT.md section 1 ("clean"; scripts/v1_audit/defect_impact.py masks); PS-CVD10 as
PS-CVD5 (docs/v1_ps10/PS10.md section 3; pipeline.md section 6).
Defaults (pipeline.md sections 4-6; user scope change 2026-10-08: the paper is ECG-only): PS-CVD5, 1:1 caliper 0.2, 54
leakage-corrected items, PS alone / + ECG / + permuted ECG, provisional v2 set of 29 trials. CLMBR-T arms stay selectable, off by
default and labelled exploratory (not in the paper). Cohorts are version 1.

Usage (tte-analysis env):
  python scripts/build_balance_explorer.py            build the HTML (+ aggregate JSON copy in the audits folder)
  python scripts/build_balance_explorer.py --check    also write the Python validation tables to the audits folder
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from make_acc_figure import VARS  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
CELLS = A / "claude-v21-paper2/core/restricted_cells.parquet"
NOLVEF = A / "claude-v1-psclin-nolvef/cells/restricted_cells.parquet"
NLSUM = A / "claude-v1-psclin-nolvef/summary"
PS10C = A / "claude-v1-ps10/cells/restricted_cells.parquet"
PS10S = A / "claude-v1-ps10/summary"
QV2 = ROOT / "docs/emulation_quality_v2/quality_v2_final.json"
SP32 = A / "claude-v20-sens-primary32/restricted_cells.parquet"
V18 = A / "claude-v18-embed-compare/results.csv"
EXPV = A / "claude-v19-expanded-buckets/per_var_all_rungs.csv"
DICT = A / "claude-v16-covars2b/dictionary.csv"
SENS2 = A / "claude-v21-paper2/core/sensitivity.csv"
SWEEP = A / "claude-v1-audit/defects/sweep_sensitivity.csv"
OUT = ROOT / "docs/presentation/ecg_tte_balance_explorer_2026_10_08.html"
SCR = A / "claude-balance-explorer"

CFGS = ["main", "cal01", "m13", "iptw", "overlap", "gbm"]
RUNGS = ["P1", "P5", "PS10", "Flags", "hdPS200", "clinical_nolvef", "clinical"]
ARMS = ["base", "ECG", "shufECG", "CLMBR", "ECG+CLMBR", "shufCLMBR"]
V18ARM = {"ECG+CLMBR": "CLMBR+ECG"}
MIN_PAIRS = 11
SC, SCX = 100000, 1000  # |SMD| stored as integers: x 1e5 (58-item grid), x 1e3 (expanded panel, as in the deck)
THRS = (0.1, 0.15, 0.2)
SEED, NB = 20261001, 4000
VN = [c for c, _, _ in VARS]
GROUP = {c: g for c, _, g in VARS}
CODED4 = ["mean_meds", "mean_util", "B_mean", "smd_prog_full"]
OBS9 = [f"smd_obs_{c}" for c in ("lvef", "sbp", "dbp", "heart_rate", "bmi", "creatinine", "potassium", "sodium", "hemoglobin")]
CLIN_NEAR = ["pp_LAB__egfr", "pp_LVFUNC__ef", "pp_LVFUNC__lv_sys_grade"]
OBS8 = [c for c in OBS9 if c != "smd_obs_lvef"]
# leakage-clean map, DEFECT_IMPACT.md section 1 table (a cell's mask = rung mask | arm mask; placebos take the real arm's mask).
# PS-Clinical without LVEF keeps the masks whose source covariates remain in the PS (CODED4, 8 observed vitals/labs, eGFR);
# echo EF, LV systolic grade and observed LVEF are held out (docs/v1_psclin_nolvef/PS_CLINICAL_NO_LVEF.md).
# PS-CVD10 = PS-CVD5's mask (B_mean, prognostic score); B_mean is also in its ex58 (R4 hit; docs/v1_ps10/PS10.md section 3).
LEAK_RUNG = {"P1": [], "P5": ["B_mean", "smd_prog_full"], "PS10": ["B_mean", "smd_prog_full"], "Flags": ["B_mean", "smd_prog_full"], "hdPS200": CODED4,
             "clinical_nolvef": CODED4 + OBS8 + ["pp_LAB__egfr"], "clinical": CODED4 + OBS9 + CLIN_NEAR}
LEAK_ARM = {"CLMBR": CODED4, "ECG+CLMBR": CODED4, "shufCLMBR": CODED4}
T1NAME = {"aristotle": "ARISTOTLE", "rocket_af": "ROCKET-AF", "rely": "RE-LY", "east_afnet4": "EAST-AFNET 4", "cabana": "CABANA",
          "affirm": "AFFIRM", "af_chf": "AF-CHF", "frail_af": "FRAIL-AF", "laaos3": "LAAOS III", "protect_af": "PROTECT AF",
          "raft_af": "RAFT-AF", "active_w": "ACTIVE W", "comet": "COMET", "paradigm_hf_seq": "PARADIGM-HF",
          "transform_hf": "TRANSFORM-HF", "elite_ii": "ELITE II", "emperor_preserved": "EMPEROR-Preserved", "life": "LIFE",
          "allhat": "ALLHAT", "value": "VALUE", "ascot": "ASCOT-BPLA", "insight": "INSIGHT", "plato": "PLATO", "valiant": "VALIANT",
          "empa_reg": "EMPA-REG OUTCOME", "carolina": "CAROLINA", "leader": "LEADER", "sustain6": "SUSTAIN-6", "rewind": "REWIND",
          "declare": "DECLARE-TIMI 58", "canvas": "CANVAS Program", "tecos": "TECOS", "carmelina": "CARMELINA",
          "ontarget": "ONTARGET", "precision": "PRECISION", "amplify": "AMPLIFY", "lodestar": "LODESTAR",
          "prove_it": "PROVE IT-TIMI 22"}
SHORT = {"EMPA-REG OUTCOME": "EMPA-REG", "CANVAS Program": "CANVAS", "DECLARE-TIMI 58": "DECLARE", "PROVE IT-TIMI 22": "PROVE IT",
         "EMPEROR-Preserved": "EMPEROR-Pres."}
BUCKETS = ["Comorbidities", "Medications", "Healthcare use & testing", "Additional labs & vitals", "Devices & procedures",
           "Preventive care", "Risk & frailty scores"]


# ================================================================ data
def load_grid():
    """full-precision |SMD| blocks (trial x 58) per (config, rung, arm) with ex58 masking and the F1 rule applied."""
    R = pd.read_parquet(CELLS)
    N = pd.read_parquet(NOLVEF)
    P10 = pd.read_parquet(PS10C)
    assert set(P10.rung) == {"PS10"} and list(P10.columns) == list(R.columns)
    R = pd.concat([R, N[N.rung == "clinical_nolvef"], P10], ignore_index=True)
    R = R[R.arm.isin(ARMS)].copy()
    order = R[(R.rung == "P1") & (R.config == "main") & (R.arm == "base")].sort_values("idx")
    tids, keys = order.trial.tolist(), order.key.tolist()
    assert len(tids) == 38
    R["failed"] = R.cell_failed.fillna("").astype(str).ne("") | (R.n_pairs.notna() & (R.n_pairs < MIN_PAIRS))
    G, nfail = {}, []
    ex = {rg: [None] * 38 for rg in RUNGS}
    for (cfg, rg, a), g in R.groupby(["config", "rung", "arm"]):
        g = g.set_index("trial").loc[tids]
        M = g[[f"smd:{c}" for c in VN]].abs().to_numpy(float)
        for i, e in enumerate(g.ex58.fillna("").astype(str)):
            s = sorted(VN.index(c) for c in filter(None, e.split(";")))
            M[i, s] = np.nan
            assert ex[rg][i] in (None, s)
            ex[rg][i] = s
        f = g.failed.to_numpy()
        M[f] = np.nan
        nfail += [(cfg, rg, a, tids[i]) for i in np.flatnonzero(f)]
        G[(cfg, rg, a)] = M
    U = pd.read_csv(V18)
    U = U[(U.half == "full") & (U.rung == "none") & (U.arm_role == "unmatched")].set_index("trial").loc[tids]
    UM = U[[f"smd:{c}" for c in VN]].abs().to_numpy(float)
    return dict(tids=tids, keys=keys, G=G, U=UM, ex=ex, failed=nfail, R=R)


def verify_sources(g):
    """grid vs paper 1 source (v20) and vs v18 (whose rung 'none' supplies the unmatched |SMD|)."""
    R, tids = g["R"], g["tids"]
    cols = [f"smd:{c}" for c in VN] + ["loghr", "se"]
    out = {}
    P = pd.read_parquet(SP32)
    P = P[P.k_pcs.isin([0, 32])]
    dev, ncell, exmis = 0.0, 0, 0
    for (cfg, rg, a), h in P.groupby(["config", "rung", "arm"]):
        x = R[(R.config == cfg) & (R.rung == rg) & (R.arm == a)].set_index("trial").loc[tids]
        y = h.set_index("trial").loc[tids]
        X, Y = x[cols].to_numpy(float), y[cols].to_numpy(float)
        assert (np.isnan(X) == np.isnan(Y)).all()
        dev = max(dev, float(np.nanmax(np.abs(X - Y))))
        exmis += int((x.ex58.fillna("") != y.ex58.fillna("")).sum())
        ncell += len(tids)
    out["v20_vs_grid"] = dict(cells=ncell, max_abs_dev=dev, ex58_mismatch=exmis)
    V = pd.read_csv(V18)
    V = V[V.half == "full"]
    dev, ncell = 0.0, 0
    for rg in ["P1", "P5", "hdPS200", "clinical"]:
        for a in ARMS:
            x = R[(R.config == "main") & (R.rung == rg) & (R.arm == a)].set_index("trial").loc[tids]
            y = V[(V.rung == rg) & (V.arm_role == V18ARM.get(a, a))].set_index("trial").loc[tids]
            X, Y = x[cols].to_numpy(float), y[cols].to_numpy(float)
            assert (np.isnan(X) == np.isnan(Y)).all(), (rg, a)
            dev = max(dev, float(np.nanmax(np.abs(X - Y))))
            ncell += len(tids)
    out["v18_vs_grid_main"] = dict(cells=ncell, max_abs_dev=dev)
    out["unmatched_in_grid"] = bool((R.rung == "none").any() or (R.arm == "unmatched").any())
    out["unmatched_source"] = "claude-v18-embed-compare/results.csv (half full, rung none, arm unmatched), as build_lab_deck.py"
    out["unmatched_finite_items"] = int(np.isfinite(g["U"]).sum())
    return out


def enc(M, sc):
    """|SMD| -> integers x sc (None = missing); values never cross the 0.10 / 0.15 / 0.20 thresholds by rounding."""
    M = np.asarray(M, float)
    V = np.rint(M * sc)
    for th in THRS:
        t = round(th * sc)
        V = np.where((M < th) & (V >= t), t - 1, V)
    return [None if not np.isfinite(x) else int(x) for x in V.ravel()]


def dec(L, sc, shape):
    return np.array([np.nan if v is None else v for v in L], float).reshape(shape) / sc


def trials_meta(g):
    QT = {t["key"]: t for t in json.load(open(ROOT / "docs/v19/quality_tiers.json"))["trials"]}
    LB = {x["trial"]: x for x in json.load(open(ROOT / "docs/v21/TRIAL_LABELS.json"))["labels"]}
    paper = (ROOT / "docs/paper/paper.md").read_text()
    v2 = set(json.load(open(QV2))["analysed_set"])
    assert len(v2) == 29 and v2 <= set(T1NAME.values())
    out = []
    for tid, k in zip(g["tids"], g["keys"]):
        nm = T1NAME[k]
        assert nm in paper, nm
        tier = QT[k]["tier"].split(" - ")[0]
        out.append(dict(id=tid, name=SHORT.get(nm, nm), full=nm, area=QT[k]["area"], tier=tier, s32=tier != "Limited",
                        phys=LB[nm]["physiologic"] == "yes", v2=nm in v2))
    assert sum(t["s32"] for t in out) == 32 and sum(t["phys"] for t in out) == 11 and sum(t["v2"] for t in out) == 29
    return out


def expanded(g):
    P = pd.read_csv(EXPV)
    dic = pd.read_csv(DICT).set_index("variable")
    vb = P.drop_duplicates("var").set_index("var").bucket
    evars = sorted(vb.index, key=lambda v: (BUCKETS.index(vb[v]), v))
    vars_ = []
    for v in evars:
        d = str(dic.definition.get(v, "")).split("; tokens")[0]
        lab = v.replace("_365", "").replace("_ever", " (ever)").replace("lab_", "").replace("rx_", "Rx ").replace("_", " ")
        vars_.append(dict(v=v, lab=lab[:34], b=vb[v], d=d[:140]))
    fail = {(rg, a, t) for cfg, rg, a, t in g["failed"] if cfg == "main"}
    S, U = {}, None
    inv = {v: k for k, v in V18ARM.items()}
    for (rg, a), G_ in P.groupby(["rung", "arm"]):
        a = inv.get(a, a)
        if rg not in RUNGS + ["none"] or (rg != "none" and a not in ARMS):
            continue
        assert set(G_.trial) <= set(g["tids"])
        W = G_.pivot(index="trial", columns="var", values="smd").reindex(index=g["tids"], columns=evars).abs().to_numpy(float)
        for i, t in enumerate(g["tids"]):
            if (rg, a, t) in fail:
                W[i] = np.nan
        if rg == "none":
            U = enc(W, SCX)
        else:
            S.setdefault(rg, {})[a] = enc(W, SCX)
    return dict(vars=vars_, buckets=BUCKETS, sc=SCX, S=S, U=U)


def build_data(g):
    trials = trials_meta(g)
    S = {cfg: {rg: {a: enc(g["G"][(cfg, rg, a)], SC) for a in ARMS if (cfg, rg, a) in g["G"]} for rg in RUNGS} for cfg in CFGS}
    vix = {c: i for i, c in enumerate(VN)}
    return dict(trials=trials, vars=[dict(c=c, lab=lab, g=gr) for c, lab, gr in VARS], sc=SC, seed=SEED, nb=NB,
                S=S, U=enc(g["U"], SC), ex=g["ex"],
                leak=dict(rung={r: [vix[c] for c in v] for r, v in LEAK_RUNG.items()},
                          arm={a: [vix[c] for c in v] for a, v in LEAK_ARM.items()}),
                E=expanded(g))


# ================================================================ statistics (Python reference; mirrors the JS)
def signflip_1s(d):
    """exact one-sided sign-flip p, H1 mean(d) > 0 (scripts/v17/v17_confirm.signflip_1s)."""
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    k = len(d)
    if k == 0:
        return np.nan
    a = np.abs(d)
    S = d.sum()
    eps = 1e-10 * max(a.sum(), 1e-300)

    def sums(x):
        s = np.zeros(1)
        for v in x:
            s = np.concatenate([s + v, s - v])
        return s
    L, Rr = sums(a[: k // 2]), np.sort(sums(a[k // 2:]))
    return float((len(Rr) - np.searchsorted(Rr, S - eps - L, side="left")).sum()) / 2.0 ** k


def relred_ci(B, Ev):
    """scripts/v20/sens_primary32.relred_ci: 1 - mean(E)/mean(B) over trials; 4,000 trial resamples, fresh seed."""
    est = 100 * (1 - Ev.mean() / B.mean())
    if len(B) < 3:
        return est, np.nan, np.nan
    I = np.random.default_rng(SEED).integers(0, len(B), size=(NB, len(B)))
    bs = 100 * (1 - Ev[I].mean(1) / B[I].mean(1))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return est, lo, hi


class Grid:
    """getter over trial x item blocks (full precision or decoded from the embedded integers)."""

    def __init__(self, G, U, ex):
        self.G, self.U, self.ex = G, U, ex

    @classmethod
    def from_data(cls, D):
        sh = (len(D["trials"]), len(D["vars"]))
        G = {(c, r, a): dec(L, D["sc"], sh) for c, x in D["S"].items() for r, y in x.items() for a, L in y.items()}
        return cls(G, dec(D["U"], D["sc"], sh), D["ex"])

    def block(self, cfg, rg, arm, leak):
        if arm == "unmatched":
            M = self.U.copy()
            for i, s in enumerate(self.ex[rg]):
                M[i, s] = np.nan
        else:
            M = self.G[(cfg, rg, arm)].copy()
        if leak:
            m = set(LEAK_RUNG[rg]) | (set(LEAK_ARM.get(arm, [])) if arm != "unmatched" else set())
            M[:, [VN.index(c) for c in m]] = np.nan
        return M


def items(panel):
    return [j for j, c in enumerate(VN) if panel == "58" or GROUP[c] != "Coded record"]


def pair_stats(grid, cfg, rg, a, b, T, panel="58", leak=False, thr=0.1):
    js = items(panel)
    Ma, Mb = grid.block(cfg, rg, a, leak)[np.ix_(T, js)], grid.block(cfg, rg, b, leak)[np.ix_(T, js)]
    m = np.isnan(Ma) | np.isnan(Mb)
    Ma, Mb = np.where(m, np.nan, Ma), np.where(m, np.nan, Mb)
    n = (~m).sum(1)
    ok = n > 0
    Ma, Mb, n = Ma[ok], Mb[ok], n[ok]
    pa, pb = 100 * (Ma < thr).sum(1) / n, 100 * (Mb < thr).sum(1) / n
    ma, mb = np.nanmean(Ma, 1), np.nanmean(Mb, 1)
    d, dm = pa - pb, mb - ma
    rr, lo, hi = relred_ci(mb, ma)
    return dict(k=int(ok.sum()), pct_ref=pb.mean(), pct_arm=pa.mean(), dpts=d.mean(), better=int((d > 0).sum()), p=signflip_1s(d),
                m_ref=mb.mean(), m_arm=ma.mean(), lower=int((dm > 0).sum()), p_m=signflip_1s(dm), rr=rr, lo=lo, hi=hi,
                p_two=min(1.0, 2 * min(signflip_1s(d), signflip_1s(-d))), p_m_two=min(1.0, 2 * min(signflip_1s(dm), signflip_1s(-dm))))


def trial_set(trials, v):
    idx = list(range(len(trials)))
    if v == "s32":
        return [i for i in idx if trials[i]["s32"]]
    if v == "v2":
        return [i for i in idx if trials[i]["v2"]]
    if v == "all":
        return idx
    k, x = v.split(":", 1)
    if k == "area":
        return [i for i in idx if trials[i]["area"] == x]
    if k == "q":
        return [i for i in idx if trials[i]["tier"] in x.split(",")]
    if k == "phys":
        y, s = x.split(",")
        return [i for i in idx if trials[i]["phys"] == (y == "yes") and (s == "all" or trials[i]["s32"])]
    if k == "t":
        return [int(x)]
    raise ValueError(v)


# ================================================================ validation (Python, full precision vs published)
RN = {"P1": "PS-Demo", "P5": "PS-CVD5", "PS10": "PS-CVD10", "Flags": "PS-Flags", "hdPS200": "hdPS", "clinical": "PS-Clinical",
      "clinical_nolvef": "PS-Clinical (no LVEF)"}
# expected values: docs/paper/supplement.md eTable 3A / 7A (paper 1); docs/v21/PAPER2_RESULTS.md and core/sensitivity.csv
# (paper 2); docs/v1_audit/DEFECT_IMPACT.md (leakage-clean and F1)
EXPECT = [
    # (source, set, cfg, rung, arm, panel, leak, dict of expected)
    ("Paper 1 eTable 3A", "s32", "main", "P1", "ECG", "58", False, dict(rr=11.4, lo=6.3, hi=16.0, pct_ref=49.8, pct_arm=55.0, better="22/32", p=".002", m_ref=0.142, m_arm=0.126)),
    ("Paper 1 eTable 3A", "s32", "main", "P1", "shufECG", "58", False, dict(rr=-0.7, lo=-5.2, hi=4.1)),
    ("Paper 1 eTable 3A", "s32", "main", "P5", "ECG", "58", False, dict(rr=9.0, lo=4.8, hi=13.3, pct_ref=53.6, pct_arm=57.6, better="21/32", p=".003", m_ref=0.128, m_arm=0.117)),
    ("Paper 1 eTable 3A", "s32", "main", "P5", "shufECG", "58", False, dict(rr=1.1, lo=-2.4, hi=4.8)),
    ("Paper 1 eTable 3A", "s32", "main", "hdPS200", "ECG", "58", False, dict(rr=7.6, lo=1.9, hi=12.8, pct_ref=58.9, pct_arm=63.8, better="23/32", p="<.001", m_ref=0.113, m_arm=0.105)),
    ("Paper 1 eTable 3A", "s32", "main", "hdPS200", "shufECG", "58", False, dict(rr=2.8, lo=-1.4, hi=7.0)),
    ("Paper 1 eTable 3A", "s32", "main", "clinical", "ECG", "58", False, dict(rr=-1.2, lo=-6.5, hi=3.9, pct_ref=61.9, pct_arm=62.2, better="15/32", p=".41", m_ref=0.109, m_arm=0.111)),
    ("Paper 1 eTable 3A", "s32", "main", "clinical", "shufECG", "58", False, dict(rr=-3.4, lo=-8.6, hi=1.2)),
    ("Paper 1 eTable 3A", "all", "main", "P1", "ECG", "58", False, dict(rr=12.6, lo=7.8, hi=16.6, pct_ref=51.4, pct_arm=57.2, better="28/38", p="<.001")),
    ("Paper 1 eTable 3A", "all", "main", "P5", "ECG", "58", False, dict(rr=9.2, lo=5.4, hi=13.3, pct_ref=55.6, pct_arm=59.5, better="25/38", p=".001")),
    ("Paper 1 eTable 3A", "all", "main", "hdPS200", "ECG", "58", False, dict(rr=7.6, lo=2.3, hi=12.4, pct_ref=61.6, pct_arm=65.7, better="24/38", p="<.001")),
    ("Paper 1 eTable 3A", "all", "main", "clinical", "ECG", "58", False, dict(rr=-0.5, lo=-5.3, hi=4.3, pct_ref=64.4, pct_arm=65.7, better="19/38", p=".20")),
    ("Paper 1 eTable 7A", "s32", "cal01", "P1", "ECG", "58", False, dict(rr=12.2, lo=6.9, hi=17.1, pct_ref=50.4, pct_arm=55.6, p=".003")),
    ("Paper 1 eTable 7A", "s32", "m13", "P1", "ECG", "58", False, dict(rr=13.6, lo=9.8, hi=17.5, pct_ref=51.0, pct_arm=57.8, p="<.001")),
    ("Paper 1 eTable 7A", "s32", "iptw", "P1", "ECG", "58", False, dict(rr=11.2, lo=7.2, hi=15.2, pct_ref=51.3, pct_arm=55.9, p="<.001")),
    ("Paper 1 eTable 7A", "s32", "overlap", "P1", "ECG", "58", False, dict(rr=14.4, lo=10.6, hi=18.2, pct_ref=51.6, pct_arm=59.0, p="<.001")),
    ("Paper 1 eTable 7A", "s32", "gbm", "P1", "ECG", "58", False, dict(rr=6.6, lo=1.5, hi=11.2, pct_ref=50.1, pct_arm=51.4, p=".21")),
    ("Paper 1 eTable 7A", "s32", "cal01", "P1", "shufECG", "58", False, dict(rr=-0.8)),
    ("Paper 1 eTable 7A", "s32", "gbm", "P1", "shufECG", "58", False, dict(rr=-1.3)),
    ("Paper 2 results", "s32", "main", "P5", "ECG", "54", False, dict(rr=8.8, lo=4.4, hi=13.3)),
    ("Paper 2 results", "s32", "main", "P5", "CLMBR", "54", False, dict(rr=12.4, lo=7.1, hi=17.7)),
    ("Paper 2 results", "s32", "main", "P5", "ECG+CLMBR", "54", False, dict(rr=13.5, lo=6.6, hi=20.4)),
    ("Paper 2 results", "s32", "main", "hdPS200", "ECG", "54", False, dict(rr=7.6, lo=1.7, hi=13.0)),
    ("Paper 2 results", "s32", "main", "hdPS200", "CLMBR", "54", False, dict(rr=-3.5)),
    ("Paper 2 results", "s32", "main", "clinical", "ECG", "54", False, dict(rr=-1.3)),
    ("Paper 2 results", "s32", "main", "clinical", "CLMBR", "54", False, dict(rr=0.8)),
    ("Paper 2 results", "s32", "main", "Flags", "CLMBR", "54", False, dict(rr=-2.9)),
    ("v1 audit F1 (DEFECT_IMPACT)", "s32", "main", "hdPS200", "ECG+CLMBR", "54", False, dict(rr=8.5)),
    ("v1 audit leakage-clean (58 items)", "s32", "main", "P5", "CLMBR", "58", True, dict(rr=12.4)),
    ("v1 audit leakage-clean (58 items)", "s32", "main", "P5", "ECG+CLMBR", "58", True, dict(rr=13.5)),
    ("v1 audit leakage-clean (58 items)", "s32", "main", "P5", "ECG", "58", True, dict(rr=8.8)),
    ("v1 audit leakage-clean (54 items)", "s32", "main", "clinical", "ECG", "54", True, dict(rr=-1.7)),
    ("v1 audit leakage-clean (54 items)", "s32", "main", "clinical", "CLMBR", "54", True, dict(rr=1.5)),
    ("Paper 2 text (paper2.md l.109)", "s32", "iptw", "P5", "ECG", "54", False, dict(rr=4.8, lo=1.5, hi=8.5)),
    ("Paper 2 text (paper2.md l.109)", "s32", "gbm", "P5", "ECG", "54", False, dict(rr=-1.1, lo=-7.3, hi=4.3)),
    ("Paper 2 text (paper2.md l.109)", "s32", "gbm", "P5", "CLMBR", "54", False, dict(rr=6.9, lo=1.1, hi=12.7)),
    ("Paper 2 text (paper2.md l.109)", "s32", "overlap", "P5", "ECG+CLMBR", "54", False, dict(rr=16.2)),
    ("Paper 2 text (paper2.md l.109)", "s32", "cal01", "P5", "ECG+CLMBR", "54", False, dict(rr=15.8)),
]
N_PAPER = len(EXPECT)  # 141 values from paper 1 / paper 2 / v1 audit
# PS-CVD10 (docs/v1_ps10/PS10.md sections 5.1-5.4; "v1" variant = leak off, "clean" = leak on). arm "a|b" = a vs b.
# lower = trials with lower mean |SMD|; p_m = one-sided sign-flip P on mean |SMD|; p_m2 = two-sided (placebos, head-to-heads).
_P10 = "PS10.md"
EXPECT += [
    (_P10 + " 5.1", "s32", "main", "PS10", "ECG", "54", False, dict(rr=5.0, lo=-0.8, hi=10.3, lower="23/32", p_m=".051", m_ref=0.121, m_arm=0.115, pct_ref=56.6, pct_arm=58.9, p=".086")),
    (_P10 + " 5.1", "s32", "main", "PS10", "ECG", "54", True, dict(rr=5.0, lo=-0.8, hi=10.3, lower="23/32", p_m=".051")),
    (_P10 + " 5.1", "s32", "main", "PS10", "ECG", "58", False, dict(rr=4.9, lo=-0.6, hi=10.1, p_m=".048", m_ref=0.120, m_arm=0.114)),
    (_P10 + " 5.1", "s32", "main", "PS10", "ECG", "58", True, dict(rr=5.0, lo=-0.6, hi=10.2, p_m=".046")),
    (_P10 + " 5.1", "all", "main", "PS10", "ECG", "54", False, dict(rr=4.8, lo=-0.5, hi=9.8, lower="27/38", p_m=".042", m_ref=0.115, m_arm=0.109, pct_ref=58.8, pct_arm=60.7)),
    (_P10 + " 5.1", "all", "main", "PS10", "ECG", "58", False, dict(rr=4.8, lo=-0.4, hi=9.6, p_m=".039")),
    (_P10 + " 5.1", "s32", "main", "PS10", "shufECG", "54", False, dict(rr=-1.1, lo=-5.8, hi=3.4, lower="11/32", p_m2=".64")),
    (_P10 + " 5.1", "s32", "main", "PS10", "ECG|shufECG", "54", False, dict(rr=6.1, lo=0.0, hi=11.0, lower="24/32", p_m=".020")),
    (_P10 + " 5.2", "s32", "cal01", "PS10", "ECG", "54", False, dict(rr=5.8, lo=-0.0, hi=11.3, lower="24/32", p_m=".029")),
    (_P10 + " 5.2", "s32", "m13", "PS10", "ECG", "54", False, dict(rr=5.2, lo=1.0, hi=9.5, lower="19/32", p_m=".012")),
    (_P10 + " 5.2", "s32", "iptw", "PS10", "ECG", "54", False, dict(rr=3.6, lo=0.8, hi=7.0, lower="24/32", p_m=".008")),
    (_P10 + " 5.2", "s32", "overlap", "PS10", "ECG", "54", False, dict(rr=6.9, lo=3.8, hi=10.6, lower="27/32", p_m="<.001")),
    (_P10 + " 5.2", "s32", "gbm", "PS10", "ECG", "54", False, dict(rr=2.4, lo=-1.5, hi=6.2, lower="18/32", p_m=".12")),
    (_P10 + " 5.2", "s32", "cal01", "PS10", "shufECG", "54", False, dict(rr=-0.1, p_m2=".97")),
    (_P10 + " 5.2", "s32", "m13", "PS10", "shufECG", "54", False, dict(rr=-1.6, p_m2=".24")),
    (_P10 + " 5.2", "s32", "iptw", "PS10", "shufECG", "54", False, dict(rr=-0.4, p_m2=".71")),
    (_P10 + " 5.2", "s32", "overlap", "PS10", "shufECG", "54", False, dict(rr=-0.6, lo=-1.2, hi=-0.1, p_m2=".028")),
    (_P10 + " 5.2", "s32", "gbm", "PS10", "shufECG", "54", False, dict(rr=-0.5, p_m2=".72")),
    (_P10 + " 5.2", "s32", "main", "PS10", "CLMBR", "54", False, dict(rr=7.4, lo=1.8, hi=12.6, lower="21/32", p_m=".009")),
    (_P10 + " 5.2", "s32", "cal01", "PS10", "CLMBR", "54", False, dict(rr=7.4, lo=1.8, hi=12.3, p_m=".008")),
    (_P10 + " 5.2", "s32", "m13", "PS10", "CLMBR", "54", False, dict(rr=7.9, lo=2.8, hi=13.2, p_m=".003")),
    (_P10 + " 5.2", "s32", "iptw", "PS10", "CLMBR", "54", False, dict(rr=-7.1, lo=-20.8, hi=4.9, p_m=".83")),
    (_P10 + " 5.2", "s32", "overlap", "PS10", "CLMBR", "54", False, dict(rr=9.7, lo=5.4, hi=14.3, p_m="<.001")),
    (_P10 + " 5.2", "s32", "gbm", "PS10", "CLMBR", "54", False, dict(rr=8.7, lo=4.3, hi=12.9, p_m=".001")),
    (_P10 + " 5.2", "s32", "main", "PS10", "ECG+CLMBR", "54", False, dict(rr=7.0, lo=0.8, hi=13.2, lower="24/32", p_m=".018")),
    (_P10 + " 5.2", "s32", "cal01", "PS10", "ECG+CLMBR", "54", False, dict(rr=7.4, lo=0.9, hi=13.8, p_m=".019")),
    (_P10 + " 5.2", "s32", "m13", "PS10", "ECG+CLMBR", "54", False, dict(rr=9.9, lo=4.2, hi=15.7, p_m=".001")),
    (_P10 + " 5.2", "s32", "iptw", "PS10", "ECG+CLMBR", "54", False, dict(rr=-6.0, lo=-25.1, hi=7.5, p_m=".65")),
    (_P10 + " 5.2", "s32", "overlap", "PS10", "ECG+CLMBR", "54", False, dict(rr=12.3, lo=7.0, hi=17.9, p_m="<.001")),
    (_P10 + " 5.2", "s32", "gbm", "PS10", "ECG+CLMBR", "54", False, dict(rr=8.3, lo=2.2, hi=14.1, p_m=".007")),
    (_P10 + " 5.2", "s32", "main", "PS10", "shufCLMBR", "54", False, dict(rr=-2.7, lo=-7.2, hi=1.1, lower="13/32", p_m2=".21")),
    (_P10 + " 5.2", "s32", "cal01", "PS10", "shufCLMBR", "54", False, dict(rr=-1.6, p_m2=".49")),
    (_P10 + " 5.2", "s32", "m13", "PS10", "shufCLMBR", "54", False, dict(rr=-0.5, p_m2=".63")),
    # PS10.md prints P .11 here, a double rounding of 0.1048; its summary/tables.md gives 0.105
    (_P10 + " 5.2 / tables.md", "s32", "iptw", "PS10", "shufCLMBR", "54", False, dict(rr=-2.3, p_m2=".105")),
    (_P10 + " 5.2", "s32", "overlap", "PS10", "shufCLMBR", "54", False, dict(rr=-0.5, p_m2=".33")),
    (_P10 + " 5.2", "s32", "gbm", "PS10", "shufCLMBR", "54", False, dict(rr=-5.0, lo=-10.1, hi=-0.9, p_m2=".021")),
    (_P10 + " 5.2 (S38)", "all", "cal01", "PS10", "ECG", "54", False, dict(rr=6.3)),
    (_P10 + " 5.2 (S38)", "all", "m13", "PS10", "ECG", "54", False, dict(rr=5.4)),
    (_P10 + " 5.2 (S38)", "all", "iptw", "PS10", "ECG", "54", False, dict(rr=4.0)),
    (_P10 + " 5.2 (S38)", "all", "overlap", "PS10", "ECG", "54", False, dict(rr=7.5)),
    (_P10 + " 5.2 (S38)", "all", "gbm", "PS10", "ECG", "54", False, dict(rr=2.4)),
    (_P10 + " 5.2 (S38)", "all", "cal01", "PS10", "CLMBR", "54", False, dict(rr=7.9)),
    (_P10 + " 5.2 (S38)", "all", "m13", "PS10", "CLMBR", "54", False, dict(rr=8.4)),
    (_P10 + " 5.2 (S38)", "all", "iptw", "PS10", "CLMBR", "54", False, dict(rr=-5.7)),
    (_P10 + " 5.2 (S38)", "all", "overlap", "PS10", "CLMBR", "54", False, dict(rr=10.0)),
    (_P10 + " 5.2 (S38)", "all", "gbm", "PS10", "CLMBR", "54", False, dict(rr=9.0)),
    (_P10 + " 5.4", "s32", "main", "PS10", "CLMBR", "58", False, dict(rr=8.4)),
    (_P10 + " 5.4", "s32", "main", "PS10", "CLMBR", "58", True, dict(rr=7.4)),
    (_P10 + " 5.4", "s32", "main", "PS10", "ECG+CLMBR", "58", False, dict(rr=8.3)),
    (_P10 + " 5.4", "s32", "main", "PS10", "ECG+CLMBR", "58", True, dict(rr=7.0)),
    (_P10 + " 5.4", "all", "main", "PS10", "CLMBR", "54", False, dict(rr=7.4, lo=2.1, hi=12.0, lower="26/38", p_m=".004")),
    (_P10 + " 5.4", "all", "main", "PS10", "ECG+CLMBR", "54", False, dict(rr=8.2, lo=2.6, hi=14.0, lower="30/38", p_m=".004")),
    (_P10 + " 5.4", "all", "main", "PS10", "shufCLMBR", "54", False, dict(rr=-3.0, p_m2=".13")),
    (_P10 + " 5.4", "s32", "main", "PS10", "CLMBR|shufCLMBR", "54", False, dict(rr=9.9, lo=5.4, hi=14.4, lower="25/32", p_m="<.001")),
    (_P10 + " 5.4", "s32", "main", "PS10", "ECG+CLMBR|CLMBR", "54", False, dict(rr=-0.2, lo=-6.3, hi=5.9, lower="18/32", p_m=".52")),
    (_P10 + " 5.4", "s32", "main", "PS10", "ECG+CLMBR|ECG", "54", False, dict(rr=2.5, lo=-3.3, hi=8.1, p_m=".20")),
    (_P10 + " 5.4", "s32", "main", "PS10", "CLMBR|ECG", "54", False, dict(rr=2.5, lo=-3.1, hi=7.5, p_m2=".38")),
]


def fmtp(p):
    return "<.001" if p < 0.001 else (f"{p:.3f}"[1:] if p < 0.01 else f"{p:.2f}"[1:] if p < 0.995 else f"{p:.2f}")


def check(g, D):
    os.umask(0o077)
    SCR.mkdir(parents=True, exist_ok=True)
    trials = D["trials"]
    full, emb = Grid(g["G"], g["U"], g["ex"]), Grid.from_data(D)
    rows = []
    for n_row, (src, ts, cfg, rg, a, panel, leak, exp) in enumerate(EXPECT):
        T = trial_set(trials, ts)
        a, b = (a.split("|") + ["base"])[:2]
        r = pair_stats(full, cfg, rg, a, b, T, panel, leak)
        re_ = pair_stats(emb, cfg, rg, a, b, T, panel, leak)
        got = dict(rr=round(r["rr"], 1), lo=round(r["lo"], 1), hi=round(r["hi"], 1), pct_ref=round(r["pct_ref"], 1),
                   pct_arm=round(r["pct_arm"], 1), better=f"{r['better']}/{r['k']}", p=fmtp(r["p"]),
                   m_ref=round(r["m_ref"], 3), m_arm=round(r["m_arm"], 3), lower=f"{r['lower']}/{r['k']}", p_m=fmtp(r["p_m"]),
                   p_m2=fmtp(r["p_m_two"]))
        emb_txt = dict(rr=f"{re_['rr']:.1f}", lo=f"{re_['lo']:.1f}", hi=f"{re_['hi']:.1f}", p_m=fmtp(re_["p_m"]), p_m2=fmtp(re_["p_m_two"]),
                       p=fmtp(re_["p"]), lower=f"{re_['lower']}/{re_['k']}", better=f"{re_['better']}/{re_['k']}")
        pex = dict(p=r["p"], p_m=r["p_m"], p_m2=r["p_m_two"])
        for key, ev in exp.items():
            gv = got[key]
            if key in pex and not (ev.startswith("<") or len(ev) == 3):
                # P given to 3 decimals (PS10.md): compare the exact P rounded to the stated precision
                gv = f"{pex[key]:.3f}"[1:]
            ok = (gv == ev) if isinstance(ev, str) else abs(gv - ev) < 0.051 if key in ("rr", "lo", "hi", "pct_ref", "pct_arm") else abs(gv - ev) < 5e-4
            rows.append(dict(source=src, paper=n_row < N_PAPER, trials=ts, method=cfg, base=RN[rg], arm=a, ref=b, panel=panel, leak=leak,
                             metric=key, expected=ev, reproduced=gv, match=bool(ok),
                             embedded_minus_full=float(re_[key] - r[key]) if key in re_ and not isinstance(ev, str) else 0.0,
                             embedded_text=emb_txt.get(key, ""), exact_rr=r["rr"], exact_p=pex.get(key, np.nan)))
    V = pd.DataFrame(rows)
    V.to_csv(SCR / "validation_published.csv", index=False)
    # full cross-check against paper 2's own summary (within-rung contrasts vs base, all configs, S32/S38, 54 and 58 items)
    S2 = pd.read_csv(SENS2)
    S2 = S2[(S2.kind == "within") & (S2.arm_b == "base")]
    xr = []
    withf1 = Grid(g["G"], g["U"], g["ex"])  # F1 applied (as embedded)
    # a no-F1 grid for exact comparison with paper 2 as run (it kept cells with 1-10 pairs)
    R = g["R"]
    G0 = {}
    for (cfg, rg, a), h in R.groupby(["config", "rung", "arm"]):
        h = h.set_index("trial").loc[g["tids"]]
        M = h[[f"smd:{c}" for c in VN]].abs().to_numpy(float)
        for i, s in enumerate(g["ex"][rg]):
            M[i, s] = np.nan
        G0[(cfg, rg, a)] = M
    nof1 = Grid(G0, g["U"], g["ex"])
    for _, s in S2.iterrows():
        T = trial_set(trials, "s32" if s.set == "S32" else "all")
        for panel, rc, bc, pc, lc in (("54", "relred54", "m54_better", "lt01_54_p", "lt01_54_b"), ("58", "relred58", "m58_better", "lt01_58_p", "lt01_58_b")):
            r0 = pair_stats(nof1, s.config, s.rung_a, s.arm_a, "base", T, panel)
            r1 = pair_stats(withf1, s.config, s.rung_a, s.arm_a, "base", T, panel)
            xr.append(dict(set=s.set, config=s.config, rung=s.rung_a, arm=s.arm_a, panel=panel, paper2_rr=s[rc], noF1_rr=r0["rr"],
                           noF1_dev=abs(r0["rr"] - s[rc]), noF1_lo_dev=abs(r0["lo"] - s[rc + "_lo"]), noF1_hi_dev=abs(r0["hi"] - s[rc + "_hi"]),
                           noF1_p_dev=abs((r0["p"] if s.sided == "one" else r0["p_two"]) - s[pc]), noF1_lt_dev=abs(r0["pct_ref"] - s[lc]),
                           noF1_mbetter_ok=f"{r0['lower']}/{r0['k']}" == s[bc], F1_rr=r1["rr"], F1_lo=r1["lo"], F1_hi=r1["hi"],
                           F1_k=r1["k"], F1_changes=abs(r1["rr"] - r0["rr"]) > 1e-12 or r1["k"] != r0["k"]))
    X = pd.DataFrame(xr)
    X.to_csv(SCR / "crosscheck_paper2_sensitivity.csv", index=False)
    # leakage-clean cross-check against the v1 audit sweep (variant clean; rows untouched by F1)
    W = pd.read_csv(SWEEP)
    W = W[(W.variant == "clean") & (W.kind == "within") & (W.arm_b == "base") & W.set.isin(["S32", "S38"])]
    lr = []
    for _, s in W.iterrows():
        T = trial_set(trials, "s32" if s.set == "S32" else "all")
        for panel, rc in (("54", "relred54"), ("58", "relred58")):
            r0 = pair_stats(nof1, s.config, s.rung_a, s.arm_a, "base", T, panel, leak=True)
            lr.append(dict(set=s.set, config=s.config, rung=s.rung_a, arm=s.arm_a, panel=panel, audit_rr=s[rc], noF1_rr=r0["rr"],
                           dev=abs(r0["rr"] - s[rc]), lo_dev=abs(r0["lo"] - s[rc + "_lo"]), hi_dev=abs(r0["hi"] - s[rc + "_hi"])))
    L = pd.DataFrame(lr)
    L.to_csv(SCR / "crosscheck_leakage_clean_sweep.csv", index=False)
    # PS-Clinical (no LVEF): every within-rung contrast vs PS alone (6 configs x S32 / S38 x 54 / 58 items x leakage off / on)
    # and every unpaired ladder level against the Python summaries of scripts/v1_psclin_nolvef/psclin_nolvef.py (F1 applied)
    NC = pd.read_csv(NLSUM / "contrasts.csv")
    NC = NC[(NC.rung_a == "clinical_nolvef") & (NC.kind == "within") & (NC.arm_b == "base")]
    nr = []
    for _, s in NC.iterrows():
        T = trial_set(trials, "s32" if s.set == "S32" else "all")
        for panel in ("54", "58"):
            pre = "relred54" if panel == "54" else "relred58"
            mm, lt = ("m54", "lt01_54") if panel == "54" else ("m58", "lt01_58")
            r1 = pair_stats(withf1, s.config, "clinical_nolvef", s.arm_a, "base", T, panel, leak=s.variant == "clean")
            nr.append(dict(variant=s.variant, set=s.set, config=s.config, arm=s.arm_a, panel=panel, py_rr=s[pre], rr=r1["rr"],
                           rr_dev=abs(r1["rr"] - s[pre]), ci_dev=max(abs(r1["lo"] - s[pre + "_lo"]), abs(r1["hi"] - s[pre + "_hi"])),
                           m_dev=max(abs(r1["m_ref"] - s[f"{mm}_b"]), abs(r1["m_arm"] - s[f"{mm}_a"])),
                           pct_dev=max(abs(r1["pct_ref"] - s[f"{lt}_b"]), abs(r1["pct_arm"] - s[f"{lt}_a"])),
                           p_lt_dev=abs((r1["p"] if s.sided == "one" else r1["p_two"]) - s[f"{lt}_p"]),
                           p_m_dev=abs((r1["p_m"] if s.sided == "one" else r1["p_m_two"]) - s[f"{mm}_p"]),
                           better_ok=f"{r1['lower']}/{r1['k']}" == s[f"{mm}_better"]))
    NX = pd.DataFrame(nr)
    NX.to_csv(SCR / "crosscheck_nolvef_contrasts.csv", index=False)
    LD = pd.read_csv(NLSUM / "ladder.csv")
    LD = LD[LD.rung.isin(RUNGS) & LD.panel.isin(["54", "58"]) & LD.arm.isin(ARMS)]
    ld = []
    for _, s in LD.iterrows():
        T = trial_set(trials, "s32" if s.set == "S32" else "all")
        M = withf1.block(s.config, s.rung, s.arm, s.variant == "clean")[np.ix_(T, items(str(s.panel)))]
        ok = np.isfinite(M).any(1)
        lv = float(np.nanmean(M[ok], 1).mean())
        ld.append(dict(variant=s.variant, set=s.set, rung=s.rung, config=s.config, arm=s.arm, panel=s.panel, py=s.mean_smd, explorer=lv,
                       dev=abs(lv - s.mean_smd), k_ok=int(ok.sum()) == s.k_trials))
    LX = pd.DataFrame(ld)
    LX.to_csv(SCR / "crosscheck_nolvef_ladder.csv", index=False)
    # PS-CVD10: every same-rung contrast in scripts/v1_ps10/ps10.py's summary (PS-CVD10 within-rung, incl. head-to-heads and
    # placebo references, and its PS-Demo / PS-CVD5 / hdPS / PS-Clinical ladder rows; v1 = leak off, clean = leak on; F1 applied)
    PC = pd.read_csv(PS10S / "contrasts.csv")
    PC = PC[PC.kind.isin(["within", "ladder"]) & (PC.rung_a == PC.rung_b)]
    pr = []
    for _, s in PC.iterrows():
        T = trial_set(trials, "s32" if s.set == "S32" else "all")
        for panel in ("54", "58"):
            pre, mm, lt = ("relred54", "m54", "lt01_54") if panel == "54" else ("relred58", "m58", "lt01_58")
            r1 = pair_stats(withf1, s.config, s.rung_a, s.arm_a, s.arm_b, T, panel, leak=s.variant == "clean")
            two = s.sided != "one"
            pr.append(dict(variant=s.variant, set=s.set, config=s.config, kind=s.kind, rung=s.rung_a, arm=s.arm_a, ref=s.arm_b, panel=panel,
                           sided=s.sided, py_rr=s[pre], rr=r1["rr"], rr_dev=abs(r1["rr"] - s[pre]),
                           ci_dev=max(abs(r1["lo"] - s[pre + "_lo"]), abs(r1["hi"] - s[pre + "_hi"])),
                           m_dev=max(abs(r1["m_ref"] - s[f"{mm}_b"]), abs(r1["m_arm"] - s[f"{mm}_a"])),
                           pct_dev=max(abs(r1["pct_ref"] - s[f"{lt}_b"]), abs(r1["pct_arm"] - s[f"{lt}_a"])),
                           p_lt_dev=abs((r1["p_two"] if two else r1["p"]) - s[f"{lt}_p"]),
                           p_m_dev=abs((r1["p_m_two"] if two else r1["p_m"]) - s[f"{mm}_p"]),
                           better_ok=f"{r1['lower']}/{r1['k']}" == s[f"{mm}_better"]))
    PX = pd.DataFrame(pr)
    PX.to_csv(SCR / "crosscheck_ps10_contrasts.csv", index=False)
    PL = pd.read_csv(PS10S / "levels.csv")
    PL = PL[PL.rung.isin(RUNGS) & PL.panel.astype(str).isin(["54", "58"]) & PL.arm.isin(ARMS)]
    pl = []
    for _, s in PL.iterrows():
        T = trial_set(trials, "s32" if s.set == "S32" else "all")
        M = withf1.block(s.config, s.rung, s.arm, s.variant == "clean")[np.ix_(T, items(str(s.panel)))]
        ok = np.isfinite(M).any(1)
        lv = float(np.nanmean(M[ok], 1).mean())
        pc = float((100 * (M[ok] < 0.1).sum(1) / np.isfinite(M[ok]).sum(1)).mean())
        pl.append(dict(variant=s.variant, set=s.set, rung=s.rung, config=s.config, arm=s.arm, panel=s.panel, py=s.mean_smd, explorer=lv,
                       dev=abs(lv - s.mean_smd), pct_dev=abs(pc - s.pct_lt01), k_ok=int(ok.sum()) == s.k_trials))
    PLX = pd.DataFrame(pl)
    PLX.to_csv(SCR / "crosscheck_ps10_levels.csv", index=False)
    # PS-CVD10 targets for the JS (headless) check: Python summary values at full precision, PS-CVD10 vs base, all arms,
    # main configuration, S32 / S38, 54 / 58 items, leakage off / on
    tg = PC[(PC.kind == "within") & (PC.config == "main") & (PC.arm_b == "base")]
    targets = []
    for _, s in tg.iterrows():
        for panel in ("54", "58"):
            pre, mm = ("relred54", "m54") if panel == "54" else ("relred58", "m58")
            targets.append(dict(cfg="main", rung="PS10", arm=s.arm_a, trials="s32" if s.set == "S32" else "all", panel=panel,
                                leak=bool(s.variant == "clean"), thr=0.1, sided=s.sided, rr=s[pre], lo=s[pre + "_lo"], hi=s[pre + "_hi"],
                                p_m=s[f"{mm}_p"], lower=s[f"{mm}_better"], m_ref=s[f"{mm}_b"], m_arm=s[f"{mm}_a"]))
    json.dump(targets, open(SCR / "ps10_js_targets.json", "w"), indent=0)
    # combos for the JS identity check (Python on the embedded integers)
    rng = np.random.default_rng(7)
    sets = ["s32", "all", "v2", "area:AF", "q:Good", "q:Excellent,Good", "phys:yes,all", "phys:no,s32", "area:Diabetes"]
    combos = []
    for i, (cfg, rg) in enumerate([(c, r) for c in CFGS for r in RUNGS]):
        for k in range(2):
            a = ARMS[1:][(i + 3 * k) % 5]
            combos.append(dict(cfg=cfg, rung=rg, arm=a, trials=sets[(i + k) % len(sets)], panel=["58", "54"][(i + k) % 2],
                               leak=bool((i // 2 + k) % 2), thr=[0.1, 0.15, 0.2][int(rng.integers(0, 3))]))
    for c in combos:
        r = pair_stats(emb, c["cfg"], c["rung"], c["arm"], "base", trial_set(trials, c["trials"]), c["panel"], c["leak"], c["thr"])
        r.pop("p_two")
        r.pop("p_m_two")
        c["py"] = {k: (None if isinstance(v, float) and not np.isfinite(v) else float(v)) for k, v in r.items()}
    # the default view (pipeline.md primary) for the UI read-out check
    for a in ("ECG", "shufECG"):
        c = dict(cfg="main", rung="P5", arm=a, trials="v2", panel="54", leak=True, thr=0.1, default_view=True)
        r = pair_stats(emb, "main", "P5", a, "base", trial_set(trials, "v2"), "54", True, 0.1)
        r.pop("p_two")
        r.pop("p_m_two")
        c["py"] = {k: (None if isinstance(v, float) and not np.isfinite(v) else float(v)) for k, v in r.items()}
        combos.append(c)
    json.dump(combos, open(SCR / "py_ref_combos.json", "w"), indent=0)
    Vp, Vq = V[V.paper], V[~V.paper]
    summ = dict(published_checks=len(Vp), published_match=int(Vp.match.sum()), ps10_doc_checks=len(Vq), ps10_doc_match=int(Vq.match.sum()),
                paper2_rows=len(X), paper2_noF1_max_rr_dev=float(X.noF1_dev.max()), paper2_noF1_max_ci_dev=float(max(X.noF1_lo_dev.max(), X.noF1_hi_dev.max())),
                paper2_noF1_max_p_dev=float(X.noF1_p_dev.max()), paper2_noF1_max_pct_dev=float(X.noF1_lt_dev.max()),
                paper2_noF1_mbetter_all_ok=bool(X.noF1_mbetter_ok.all()), F1_changed_rows=int(X.F1_changes.sum()),
                leak_rows=len(L), leak_max_rr_dev=float(L.dev.max()), leak_max_ci_dev=float(max(L.lo_dev.max(), L.hi_dev.max())),
                nolvef_rows=len(NX), nolvef_max_rr_dev=float(NX.rr_dev.max()), nolvef_max_ci_dev=float(NX.ci_dev.max()),
                nolvef_max_m_dev=float(NX.m_dev.max()), nolvef_max_pct_dev=float(NX.pct_dev.max()),
                nolvef_max_p_dev=float(max(NX.p_lt_dev.max(), NX.p_m_dev.max())), nolvef_better_all_ok=bool(NX.better_ok.all()),
                ladder_rows=len(LX), ladder_max_dev=float(LX.dev.max()), ladder_k_all_ok=bool(LX.k_ok.all()),
                ps10_rows=len(PX), ps10_max_rr_dev=float(PX.rr_dev.max()), ps10_max_ci_dev=float(PX.ci_dev.max()),
                ps10_max_m_dev=float(PX.m_dev.max()), ps10_max_pct_dev=float(PX.pct_dev.max()),
                ps10_max_p_dev=float(max(PX.p_lt_dev.max(), PX.p_m_dev.max())), ps10_better_all_ok=bool(PX.better_ok.all()),
                ps10_level_rows=len(PLX), ps10_level_max_dev=float(PLX.dev.max()), ps10_level_max_pct_dev=float(PLX.pct_dev.max()),
                ps10_level_k_all_ok=bool(PLX.k_ok.all()), ps10_js_targets=len(targets),
                max_embedded_minus_full=float(V.embedded_minus_full.abs().max()), js_combos=len(combos))
    json.dump(summ, open(SCR / "validation_summary.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))
    print(V[~V.match].to_string() if (~V.match).any() else "all published values reproduced")
    print(X[X.F1_changes][["set", "config", "rung", "arm", "panel", "paper2_rr", "F1_rr", "F1_lo", "F1_hi", "F1_k"]].to_string())


# ================================================================ HTML
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    os.umask(0o077)
    SCR.mkdir(parents=True, exist_ok=True)
    g = load_grid()
    vs = verify_sources(g)
    print(json.dumps(vs, indent=1))
    assert vs["v20_vs_grid"]["max_abs_dev"] == 0 and vs["v20_vs_grid"]["ex58_mismatch"] == 0
    assert vs["v18_vs_grid_main"]["max_abs_dev"] <= 1e-12  # csv round trip
    json.dump(vs, open(SCR / "source_checks.json", "w"), indent=1)
    D = build_data(g)
    js = json.dumps(D, separators=(",", ":"), allow_nan=False)
    (SCR / "explorer_data.json").write_text(js)
    html = TEMPLATE.replace("__DATA__", js)
    old = os.umask(0o022)
    OUT.write_text(html)
    os.umask(old)
    print(f"wrote {OUT} ({len(html) / 1e6:.2f} MB); failed cells (F1) treated as missing: {len(g['failed'])}")
    if args.check:
        check(g, D)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TRACE-ECG covariate balance explorer</title>
<style>
:root{--navy:#0E103C;--red:#DC5A55;--ink:#0E103C;--muted:#55576f;--faint:#8a8ca0;--line:#dcdde5;--band:#f3f3f7}
html,body{margin:0;background:#fff}
body{font-family:Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif;color:var(--ink);min-width:1280px}
header{padding:12px 18px 6px;border-bottom:2px solid var(--navy)}
header h1{margin:0;font-size:21px;display:inline-block;background:var(--navy);color:#fff;padding:4px 12px}
header .sub{display:inline-block;margin-left:12px;font-size:13px;color:var(--muted)}
header .notes{font-size:11.5px;color:var(--muted);line-height:1.4;margin-top:6px;max-width:1500px}
.panel{display:grid;grid-template-columns:256px minmax(640px,1fr) 430px;gap:12px;padding:8px 16px 4px}
.ctrl{font-size:13px;border-right:1px solid var(--line);padding-right:10px}
.ctrl label.h{display:block;font-weight:700;font-size:11.5px;letter-spacing:.3px;text-transform:uppercase;color:var(--navy);margin:8px 0 2px}
.ctrl select{width:100%;font:inherit;font-size:12.5px;padding:2px 3px;border:1px solid #b9bbc8;border-radius:3px;background:#fff;color:var(--ink)}
.ctrl .cb{display:flex;align-items:center;gap:5px;margin:1px 0;font-size:12.5px;cursor:pointer}
.ctrl .cb input{margin:0}
.ctrl .cb.dis{opacity:.35}
.ctrl .p2{font-size:10.5px;color:var(--faint)}
.ctrl .desc{font-size:11px;color:var(--muted);line-height:1.3;margin:2px 0 0}
.ctrl input[type=range]{width:100%}
.ctrl .dim{opacity:.4}
.sw{display:inline-block;width:14px;height:12px;flex:none}
.views{display:flex;gap:0;margin:0 0 6px}
.views label{border:1px solid var(--navy);padding:4px 12px;font-size:13px;cursor:pointer;color:var(--navy);user-select:none}
.views label+label{border-left:none}
.views input{display:none}
.views label.on{background:var(--navy);color:#fff}
.chart{position:relative}
.chart .cap{font-size:11.5px;color:var(--muted);line-height:1.35;margin:4px 0 0}
.side{font-size:13px;border-left:1px solid var(--line);padding-left:12px}
.side h4{margin:4px 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.3px}
.side .sel{font-size:12px;color:var(--muted);margin:0 0 6px}
.side table{border-collapse:collapse;width:100%}
.side td,.side th{font-size:12px;padding:3px 4px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.side th{font-weight:700;color:var(--navy);border-bottom:2px solid var(--navy)}
.side td:first-child,.side th:first-child{text-align:left}
.side .note{font-size:11px;color:var(--muted);line-height:1.35;margin:6px 0}
.side .hl{background:#fbeceb}
.side .empty{margin-top:40px;font-size:17px;font-weight:700;color:var(--navy);text-align:center}
.side td .ci{display:block;font-size:10.5px;color:var(--muted)}
.qv{display:flex;gap:8px;font-size:12.5px}.qv label{display:flex;align-items:center;gap:2px;cursor:pointer;white-space:nowrap}.qv input{margin:0}
footer{font-size:11px;color:var(--muted);padding:6px 18px 14px;line-height:1.4;border-top:1px solid var(--line);margin-top:6px}
svg text{font-family:Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif}
#tip{position:fixed;pointer-events:none;background:#fff;border:1px solid var(--navy);color:var(--ink);font:12px/1.35 Montserrat,"Helvetica Neue",Arial,sans-serif;
  padding:6px 8px;max-width:340px;display:none;z-index:10;box-shadow:0 2px 6px rgba(0,0,0,.15)}
</style>
</head>
<body>
<header>
  <h1>TRACE-ECG: covariate balance explorer</h1><span class="sub">38 emulated trials, YNHHS; held-out characteristics not in any PS. Updated 2026-10-08 (PS-CVD10 in the main ladder; defaults set to the pipeline.md primary).</span>
  <div class="notes">
    <b>The paper is ECG-only.</b> <b>Primary (pipeline.md; the default view):</b> PS-CVD5 + ECG vs PS-CVD5, 1:1 caliper 0.2, fixed L2 penalty C = 1, 54 non-coded items with leakage-corrected masking (permuted ECG as the placebo); the provisional v2 analysed set of 29 trials (emulation quality v2.0, adjudicated but not frozen). The CLMBR-T arms are not in the paper; they stay selectable as exploratory, off by default. <b>Cohorts are version 1:</b> the spec-v2 fixed cohorts and the 5-draw multiple-imputation PS-Clinical (no LVEF) will replace them when ready. <b>Paper 1 primary</b> (still selectable): PS-Demo, 58 items, masking off, paper 1's 32 trials.
    <b>Main information ladder:</b> PS-Demo → PS-CVD5 (primary) → PS-CVD10 (comparison) → hdPS → PS-Clinical (no LVEF). PS-Flags (supplement) and PS-Clinical (with LVEF, v1 reference) are selectable but off by default. <b>PS-CVD10</b> = PS-Demo + 10 fixed diagnoses (hypertension, T2D, CAD/MI, AF, HF, CKD, COPD/asthma, PAD, stroke/TIA, valve disease). <b>PS-Clinical (no LVEF)</b> removes LVEF and re-imputes without it (single imputation here), so no PS uses an echo measurement.
    <b>Data:</b> per-trial |SMD| from the paper 2 grid (<code>audits/claude-v21-paper2/core</code>; 6 arms × 6 PS methods), PS-Clinical (no LVEF) from <code>audits/claude-v1-psclin-nolvef</code> and PS-CVD10 from <code>audits/claude-v1-ps10</code> (same engine, arms and methods; PS-CVD5 rebuilt through the PS-CVD10 code reproduces the grid exactly). Unmatched |SMD| come from the v1.8 embedding comparison (same cohorts).
    <b>Leakage-corrected masking</b> (pipeline.md §6; v1 audit, DEFECT_IMPACT §1) also removes held-out items that duplicate or are derived from a PS input: for PS-Clinical (no LVEF), eGFR (plus the 4 coded-record items); for PS-Clinical (with LVEF), echo EF, LV systolic grade and eGFR (plus the 4 coded-record items); for hdPS and for every (exploratory) CLMBR-T arm, real or permuted, the 4 coded-record items; for PS-CVD5, PS-CVD10 and PS-Flags, held-out codes and the prognostic score (PS-CVD10 masks held-out codes even with masking off). Nothing on the 54-item panel is masked for PS-Demo, PS-CVD5, PS-CVD10, PS-Flags or hdPS. Cells with fewer than 11 matched pairs are treated as failed (missing). Aggregates only.
  </div>
</header>
<div class="panel">
  <div class="ctrl" id="ctrl"></div>
  <div class="chart">
    <div class="views" id="views">
      <label class="on"><input type="radio" name="view" value="love" checked>Love plot</label>
      <label><input type="radio" name="view" value="ladder">Information ladder</label>
      <label><input type="radio" name="view" value="method">Method comparison</label>
    </div>
    <svg id="svg" viewBox="0 0 760 600" style="width:100%;height:auto"></svg>
    <div class="cap" id="cap"></div>
  </div>
  <div class="side" id="sum"></div>
</div>
<footer>
  <b>Definitions.</b> |SMD| = absolute standardized mean difference between initiators of the two drugs after matching or weighting. % balanced = share of a trial's items with |SMD| below the threshold, averaged over trials. Paired comparisons (vs PS alone) use, within each trial, only items observed in both arms, as in both papers. Relative reduction = 1 − (mean over trials of the arm's mean |SMD|) / (same for PS alone); 95% CI from 4,000 trial-level bootstrap resamples with numpy's generator and seed 20261001, reproduced here exactly. P = exact one-sided sign-flip test over trials (H1: the arm improves balance), on % balanced (paper 1's prespecified endpoint) and on mean |SMD| (paper 2's primary). The quality tiers and physiologic labels were assigned after the primary analyses (the labels by an LLM, blind to the results, with no clinician review). The expanded panel (~330 items) exists only for 1:1 caliper 0.2 and PS-Demo, PS-CVD5, hdPS and PS-Clinical (with LVEF), and is not leakage-masked.
</footer>
<div id="tip"></div>
<script>
"use strict";
const D = __DATA__;
const NAVY = "#0E103C", RED = "#DC5A55";
const ARM = {
  unmatched: {lab: "Unmatched", col: "#8a8d99", mk: "x"},
  base: {lab: "PS alone", col: NAVY, mk: "circle"},
  ECG: {lab: "+ ECG", col: RED, mk: "circle"},
  shufECG: {lab: "+ permuted ECG", col: "#d69a00", mk: "tri", hollow: true},
  CLMBR: {lab: "+ CLMBR-T", col: "#2a78d6", mk: "square"},
  "ECG+CLMBR": {lab: "+ CLMBR-T + ECG", col: "#1baf7a", mk: "diamond"},
  shufCLMBR: {lab: "+ permuted CLMBR-T", col: "#2a78d6", mk: "square", hollow: true}
};
const SL = {unmatched: "Unmatched", base: "PS alone", ECG: "+ ECG", shufECG: "+ perm. ECG", CLMBR: "+ CLMBR-T", "ECG+CLMBR": "+ CLMBR-T + ECG", shufCLMBR: "+ perm. CLMBR-T"};
const ARMS_ALL = ["unmatched", "base", "ECG", "shufECG", "CLMBR", "ECG+CLMBR", "shufCLMBR"];
const PAPER2 = new Set(["CLMBR", "ECG+CLMBR", "shufCLMBR"]);  /* CLMBR-T arms: exploratory, not in the (ECG-only) paper */
const CFG = {main: "1:1, caliper 0.2 (primary)", cal01: "1:1, caliper 0.1", m13: "1:3 matching, caliper 0.2",
  iptw: "Inverse probability weighting", overlap: "Overlap weighting", gbm: "Gradient-boosted PS (1:1, caliper 0.2)"};
const CSHORT = {main: "1:1, cal. 0.2", cal01: "1:1, cal. 0.1", m13: "1:3", iptw: "IPTW", overlap: "Overlap", gbm: "GBM PS"};
const RUNG = {P1: ["PS-Demo", "Age, sex and index year (paper 1 primary)."],
  P5: ["PS-CVD5", "PS-Demo + hypertension, type 2 diabetes, CAD, AF and heart failure. Primary (pipeline.md)."],
  PS10: ["PS-CVD10", "PS-Demo + 10 fixed diagnoses: hypertension, T2D, CAD/MI, AF, HF, CKD, COPD/asthma, PAD, stroke/TIA, valve disease (main-ladder comparison)."],
  Flags: ["PS-Flags", "Supplement: PS-Demo + ~530 yes/no ICD-10 3-character diagnosis flags (full history, ≥1% prevalence)."],
  hdPS200: ["hdPS", "Demographics + 9–13 investigator-selected diagnoses + 200 empirically selected code features."],
  clinical_nolvef: ["PS-Clinical (no LVEF)", "Adds vital signs, labs, medications and healthcare use, but no LVEF or any other echo measurement, so all 35 echo items and observed LVEF stay held out. Covariates re-imputed without LVEF (their held-out copies are masked)."],
  clinical: ["PS-Clinical (with LVEF, v1)", "Version 1 reference, replaced by PS-Clinical (no LVEF): vital signs, labs, LVEF, medications and healthcare use (their held-out copies are masked). LVEF leaks into echo EF and LV systolic grade (leakage-corrected masking removes them)."]};
/* RUNGS: x order of the information ladder (main levels in pipeline.md order; the supplement / reference levels slot in
   by information when ticked). MAIN / SUPP: grouping in the controls. */
const RUNGS = ["P1", "P5", "PS10", "Flags", "hdPS200", "clinical_nolvef", "clinical"], CFGS = Object.keys(CFG);
const MAIN = ["P1", "P5", "PS10", "hdPS200", "clinical_nolvef"], SUPP = ["Flags", "clinical"];
const ROLE = {P5: "primary", PS10: "comparison", Flags: "supplement", clinical: "v1 reference"};
const RSUB = {P1: "demographics", P5: "+ 5 diagnoses", PS10: "+ 10 diagnoses", Flags: "+ ~530 dx flags", hdPS200: "+ 200 codes", clinical_nolvef: "+ vitals, labs; no echo", clinical: "+ vitals, labs, LVEF"};
const DEF_LADDER = MAIN, PRIMARY = "P5";
const rungOpt = r => `${RUNG[r][0]}${ROLE[r] ? " (" + ROLE[r] + ")" : ""}`;
const AREAS = ["AF", "HF", "Diabetes", "Hypertension", "ACS / MI", "Other"];
const TIERS = [["Excellent"], ["Good"], ["Moderate"], ["Limited"], ["Excellent", "Good"], ["Excellent", "Good", "Moderate"], ["Moderate", "Limited"]];
const NT = D.trials.length, NV = D.vars.length, SEED = D.seed, NB = D.nb;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const fin = x => x !== null && x !== undefined && Number.isFinite(x);
const mean = a => { const b = a.filter(fin); return b.length ? b.reduce((s, x) => s + x, 0) / b.length : NaN; };
const median = a => { const b = a.filter(fin).sort((x, y) => x - y); const n = b.length; if (!n) return NaN; return n % 2 ? b[(n - 1) / 2] : (b[n / 2 - 1] + b[n / 2]) / 2; };
const fmtp = p => !Number.isFinite(p) ? "–" : p < 0.001 ? "<.001" : p < 0.01 ? p.toFixed(3).slice(1) : p < 0.995 ? p.toFixed(2).slice(1) : p.toFixed(2);
const f1 = x => Number.isFinite(x) ? x.toFixed(1) : "–";
const f3 = x => Number.isFinite(x) ? x.toFixed(3) : "–";
const sgn1 = x => { const t = f1(x); return t === "-0.0" ? "0.0" : (x > 0 && t !== "0.0" ? "+" : "") + t; };

/* ---------- data (integers x sc; null = missing) ---------- */
const dec = (a, sc) => { const f = new Float64Array(a.length); for (let i = 0; i < a.length; i++) f[i] = a[i] === null ? NaN : a[i] / sc; return f; };
const S = {}; for (const c in D.S) { S[c] = {}; for (const r in D.S[c]) { S[c][r] = {}; for (const a in D.S[c][r]) S[c][r][a] = dec(D.S[c][r][a], D.sc); } }
const U = dec(D.U, D.sc);
const EX = {}; for (const r in D.ex) EX[r] = D.ex[r].map(l => new Set(l));
const LK = {rung: {}, arm: {}};
for (const r in D.leak.rung) LK.rung[r] = new Set(D.leak.rung[r]);
for (const a in D.leak.arm) LK.arm[a] = new Set(D.leak.arm[a]);
const NX = D.E.vars.length, XS = {}, XU = dec(D.E.U, D.E.sc);
for (const r in D.E.S) { XS[r] = {}; for (const a in D.E.S[r]) XS[r][a] = dec(D.E.S[r][a], D.E.sc); }

/* getter(panel, leak)(cfg, rung, arm, trial, item) -> |SMD| or NaN */
function getter(panel, leak) {
  if (panel === "exp") return (cfg, rung, arm, t, j) => {
    if (arm === "unmatched") return XU[t * NX + j];
    if (cfg !== "main") return NaN;
    const A = XS[rung] && XS[rung][arm]; return A ? A[t * NX + j] : NaN; };
  return (cfg, rung, arm, t, j) => {
    if (leak && (LK.rung[rung].has(j) || (LK.arm[arm] && LK.arm[arm].has(j)))) return NaN;
    if (arm === "unmatched") return EX[rung][t].has(j) ? NaN : U[t * NV + j];
    const A = S[cfg] && S[cfg][rung] && S[cfg][rung][arm]; return A ? A[t * NV + j] : NaN; };
}
function itemsOf(panel) {
  if (panel === "exp") return D.E.vars.map((v, j) => ({j, lab: v.lab, g: v.b, def: v.d}));
  return D.vars.map((v, j) => ({j, lab: v.lab, g: v.g, def: ""})).filter(v => panel === "58" || v.g !== "Coded record");
}

/* ---------- statistics ---------- */
function subsetSums(a) { let s = new Float64Array([0]); for (const v of a) { const n = new Float64Array(s.length * 2); for (let i = 0; i < s.length; i++) { n[2 * i] = s[i] + v; n[2 * i + 1] = s[i] - v; } s = n; } return s; }
/* exact one-sided sign-flip p for H1: mean(d) > 0; P(sum of randomly signed |d| >= observed), meet in the middle */
function signflip(d) {
  d = d.filter(fin); const k = d.length; if (!k) return NaN;
  const a = d.map(Math.abs), S_ = d.reduce((s, x) => s + x, 0), eps = 1e-10 * Math.max(a.reduce((s, x) => s + x, 0), 1e-300);
  const L = subsetSums(a.slice(0, k >> 1)), R = subsetSums(a.slice(k >> 1)).sort();
  let cnt = 0; const n = R.length;
  for (let i = 0; i < L.length; i++) { const thr = S_ - eps - L[i]; let lo = 0, hi = n; while (lo < hi) { const m = (lo + hi) >> 1; if (R[m] < thr) lo = m + 1; else hi = m; } cnt += n - lo; }
  return cnt / Math.pow(2, k);
}
/* numpy default_rng(seed).integers(0, k, size=(nb, k)), reproduced exactly: SeedSequence -> PCG64 (XSL-RR, 128-bit LCG in
   BigInt) -> 32-bit Lemire bounded draws. Lets the bootstrap CIs match the papers' Python bit for bit. */
function npSeedState(seed) {
  const MULT_A = 0x931e8875, MULT_B = 0x58f38ded, ML = 0xca01f9dd, MR = 0x4973f715;
  let hc = 0x43b0d7e5;
  const hashmix = v => { v = (v ^ hc) >>> 0; hc = Math.imul(hc, MULT_A) >>> 0; v = Math.imul(v, hc) >>> 0; return (v ^ (v >>> 16)) >>> 0; };
  const mix = (x, y) => { const r = (Math.imul(ML, x) - Math.imul(MR, y)) >>> 0; return (r ^ (r >>> 16)) >>> 0; };
  const ent = [seed >>> 0], pool = [0, 0, 0, 0];
  for (let i = 0; i < 4; i++) pool[i] = hashmix(i < ent.length ? ent[i] : 0);
  for (let s = 0; s < 4; s++) for (let d = 0; d < 4; d++) if (s !== d) pool[d] = mix(pool[d], hashmix(pool[s]));
  let hb = 0x8b51f9dd; const w = [];
  for (let i = 0; i < 8; i++) { let v = (pool[i % 4] ^ hb) >>> 0; hb = Math.imul(hb, MULT_B) >>> 0; v = Math.imul(v, hb) >>> 0; w.push((v ^ (v >>> 16)) >>> 0); }
  return [0, 1, 2, 3].map(i => BigInt(w[2 * i]) | (BigInt(w[2 * i + 1]) << 32n));
}
function npPCG64(seed) {
  const M128 = (1n << 128n) - 1n, M64 = (1n << 64n) - 1n, MUL = 0x2360ED051FC65DA44385DF649FCCF645n;
  const v = npSeedState(seed), s0 = (v[0] << 64n) | v[1], i0 = (v[2] << 64n) | v[3];
  const inc = ((i0 << 1n) | 1n) & M128; let st = 0n;
  const step = () => { st = (st * MUL + inc) & M128; };
  step(); st = (st + s0) & M128; step();
  let has32 = false, buf = 0;
  const next64 = () => { step(); const x = ((st >> 64n) ^ st) & M64, rot = Number(st >> 122n); return ((x >> BigInt(rot)) | (x << BigInt((64 - rot) & 63))) & M64; };
  const next32 = () => { if (has32) { has32 = false; return buf; } const n = next64(); has32 = true; buf = Number(n >> 32n); return Number(n & 0xFFFFFFFFn); };
  return {next32};
}
function npIntegers(seed, k, count) {
  const g = npPCG64(seed), out = new Int32Array(count), thr = (0xFFFFFFFF - (k - 1)) % k, K = BigInt(k);
  for (let c = 0; c < count; c++) {
    let m = BigInt(g.next32()) * K, lo = Number(m & 0xFFFFFFFFn);
    if (lo < k) while (lo < thr) { m = BigInt(g.next32()) * K; lo = Number(m & 0xFFFFFFFFn); }
    out[c] = Number(m >> 32n);
  }
  return out;
}
const IDX = {};
const bootIdx = k => IDX[k] || (IDX[k] = npIntegers(SEED, k, NB * k));
const pctl = (a, q) => { const h = (a.length - 1) * q / 100, lo = Math.floor(h); return lo + 1 < a.length ? a[lo] + (h - lo) * (a[lo + 1] - a[lo]) : a[lo]; };
/* relative reduction 100 * (1 - mean_t E / mean_t B) and its 4,000-resample trial bootstrap percentile CI */
function relRed(B, E) {
  const k = B.length; if (!k) return [NaN, NaN, NaN];
  let sb = 0, se = 0; for (let i = 0; i < k; i++) { sb += B[i]; se += E[i]; }
  const est = 100 * (1 - (se / k) / (sb / k)); if (k < 3) return [est, NaN, NaN];
  const I = bootIdx(k), bs = new Float64Array(NB);
  for (let r = 0; r < NB; r++) { let x = 0, y = 0; for (let i = 0; i < k; i++) { const q = I[r * k + i]; x += E[q]; y += B[q]; } bs[r] = 100 * (1 - (x / k) / (y / k)); }
  bs.sort(); return [est, pctl(bs, 2.5), pctl(bs, 97.5)];
}
/* per-arm levels on the arm's own observed items */
function levels(get, cfg, rung, arm, T, js, thr) {
  const m = [], p = [];
  for (const t of T) { let n = 0, s = 0, k = 0; for (const j of js) { const x = get(cfg, rung, arm, t, j); if (x === x) { n++; s += x; if (x < thr) k++; } }
    m.push(n ? s / n : NaN); p.push(n ? 100 * k / n : NaN); }
  return {m, p};
}
/* paired contrast arm a vs reference b: items observed in both arms of a trial */
function paired(get, cfg, rung, a, b, T, js, thr, opt) {
  opt = opt || {}; const pa = [], pb = [], ma = [], mb = [];
  for (const t of T) { let n = 0, ka = 0, kb = 0, sa = 0, sb = 0;
    for (const j of js) { const x = get(cfg, rung, a, t, j), y = get(cfg, rung, b, t, j); if (x !== x || y !== y) continue; n++; sa += x; sb += y; if (x < thr) ka++; if (y < thr) kb++; }
    if (n) { pa.push(100 * ka / n); pb.push(100 * kb / n); ma.push(sa / n); mb.push(sb / n); } }
  const k = pa.length, d = pa.map((x, i) => x - pb[i]), dm = mb.map((x, i) => x - ma[i]);
  const [rr, lo, hi] = opt.noci ? [k ? 100 * (1 - mean(ma) / mean(mb)) : NaN, NaN, NaN] : relRed(mb, ma);
  return {k, pct_ref: mean(pb), pct_arm: mean(pa), dpts: mean(d), better: d.filter(x => x > 0).length, p: opt.nop || k < 2 ? NaN : signflip(d),
    m_ref: mean(mb), m_arm: mean(ma), lower: dm.filter(x => x > 0).length, p_m: opt.nop || k < 2 ? NaN : signflip(dm), rr, lo, hi};
}

/* ---------- small SVG helpers (from the lab deck) ---------- */
function marker(mk, x, y, r, col, hollow, extra) {
  extra = extra || ""; const f = hollow ? "#fff" : col, sw = hollow ? 1.6 : 1;
  const st = `fill="${f}" stroke="${hollow ? col : "#fff"}" stroke-width="${sw}" ${extra}`;
  if (mk === "square") return `<rect x="${x - r * .85}" y="${y - r * .85}" width="${r * 1.7}" height="${r * 1.7}" ${st}/>`;
  if (mk === "diamond") return `<path d="M${x} ${y - r * 1.2}L${x + r * 1.2} ${y}L${x} ${y + r * 1.2}L${x - r * 1.2} ${y}Z" ${st}/>`;
  if (mk === "tri") return `<path d="M${x} ${y - r * 1.15}L${x + r * 1.1} ${y + r * .8}L${x - r * 1.1} ${y + r * .8}Z" ${st}/>`;
  if (mk === "x") return `<path d="M${x - r * .8} ${y - r * .8}L${x + r * .8} ${y + r * .8}M${x - r * .8} ${y + r * .8}L${x + r * .8} ${y - r * .8}" stroke="${col}" stroke-width="2" fill="none" ${extra}/>`;
  return `<circle cx="${x}" cy="${y}" r="${r}" ${st}/>`;
}
function swatch(a) { const A = ARM[a]; return `<svg class="sw" viewBox="0 0 14 12">${marker(A.mk, 7, 6, 4.2, A.col, A.hollow)}</svg>`; }
const tip = $("#tip");
function bindTips(svg) {
  svg.onmousemove = e => { const t = e.target.closest("[data-tip]"); if (!t) { tip.style.display = "none"; return; }
    tip.innerHTML = t.getAttribute("data-tip"); tip.style.display = "block";
    const w = tip.offsetWidth, h = tip.offsetHeight; let x = e.clientX + 14, y = e.clientY + 14;
    if (x + w > innerWidth - 4) x = e.clientX - w - 14; if (y + h > innerHeight - 4) y = e.clientY - h - 14;
    tip.style.left = x + "px"; tip.style.top = y + "px"; };
  svg.onmouseleave = () => { tip.style.display = "none"; };
}

/* ---------- trial filters ---------- */
function trialOptions() {
  const n = f => D.trials.filter(f).length;
  let h = `<option value="v2">Provisional v2 set (${n(t => t.v2)}, not frozen)</option><option value="s32">Paper 1 primary set (${n(t => t.s32)} trials)</option><option value="all">All ${NT} emulated trials</option><optgroup label="Clinical area (all 38)">`;
  for (const a of AREAS) h += `<option value="area:${a}">${a} (${n(t => t.area === a)})</option>`;
  h += `</optgroup><optgroup label="Emulation quality tier">`;
  for (const q of TIERS) h += `<option value="q:${q.join(",")}">${q.join(" or ")} (${n(t => q.includes(t.tier))})</option>`;
  h += `</optgroup><optgroup label="Physiologic label (LLM, blind to results)">`;
  for (const [y, s, lab] of [["yes", "all", "Physiologic: yes, all 38"], ["no", "all", "Physiologic: no, all 38"], ["yes", "s32", "Physiologic: yes, paper 1 set"], ["no", "s32", "Physiologic: no, paper 1 set"]])
    h += `<option value="phys:${y},${s}">${lab} (${n(t => t.phys === (y === "yes") && (s === "all" || t.s32))})</option>`;
  h += `</optgroup><optgroup label="Single trial">`;
  D.trials.map((t, i) => [t.name, i]).sort().forEach(([nm, i]) => h += `<option value="t:${i}">${esc(nm)}</option>`);
  return h + `</optgroup>`;
}
function trialSet(v) {
  const idx = D.trials.map((_, i) => i);
  if (v === "s32") return idx.filter(i => D.trials[i].s32);
  if (v === "v2") return idx.filter(i => D.trials[i].v2);
  if (v === "all") return idx;
  const [k, x] = v.split(":");
  if (k === "area") return idx.filter(i => D.trials[i].area === x);
  if (k === "q") { const q = x.split(","); return idx.filter(i => q.includes(D.trials[i].tier)); }
  if (k === "phys") { const [y, s] = x.split(","); return idx.filter(i => D.trials[i].phys === (y === "yes") && (s === "all" || D.trials[i].s32)); }
  if (k === "t") return [+x];
  return idx;
}
const checked = name => [...document.querySelectorAll(`input[name="${name}"]:checked`)].map(x => x.value);
const EMPTY = msg => `<div class="empty">${msg}</div>`;

/* =========================================================
   controls
   ========================================================= */
const GROUPS58 = [...new Set(D.vars.map(v => v.g))];
const GSHORT = {"Coded record": "Coded", "Vitals & core labs": "Vitals / labs", "Other labs": "Other labs", "Echo: LV structure": "LV structure",
  "Echo: LV function": "LV function", "Echo: diastolic / LA": "Diastolic / LA", "Echo: RV / pulmonary": "RV / pulm.", "Echo: valves / aorta": "Valves / aorta",
  "Comorbidities": "Comorbidities", "Medications": "Medications", "Healthcare use & testing": "Use & testing", "Additional labs & vitals": "Labs & vitals",
  "Devices & procedures": "Devices", "Preventive care": "Preventive", "Risk & frailty scores": "Scores"};
const DEF_ARMS = ["base", "ECG", "shufECG"];
function init() {
  $("#ctrl").innerHTML = `
  <label class="h">Trials</label><select id="c-trials">${trialOptions()}</select>
  <label class="h">PS method</label><select id="c-cfg">${CFGS.map(c => `<option value="${c}">${CFG[c]}</option>`).join("")}</select>
  <label class="h">Information level (PS base)</label><select id="c-rung"><optgroup label="Main ladder">${MAIN.map(r => `<option value="${r}" ${r === PRIMARY ? "selected" : ""}>${rungOpt(r)}</option>`).join("")}</optgroup><optgroup label="Supplement / reference">${SUPP.map(r => `<option value="${r}">${rungOpt(r)}</option>`).join("")}</optgroup></select>
  <div class="desc" id="c-rdesc"></div>
  <label class="h">Ladder levels (information ladder view)</label>
  <div id="c-lad">${[...MAIN, ...SUPP].map(r => `<label class="cb"><input type="checkbox" name="c-lad" value="${r}" ${DEF_LADDER.includes(r) ? "checked" : ""}><span>${r === PRIMARY ? "<b>" + RUNG[r][0] + "</b>" : RUNG[r][0]}${ROLE[r] ? ` <span class="p2">(${ROLE[r]})</span>` : ""}</span></label>`).join("")}</div>
  <label class="h">Comparison arms</label>
  <div id="c-arms">${ARMS_ALL.map(a => `<label class="cb" data-arm="${a}"><input type="checkbox" name="c-arm" value="${a}" ${DEF_ARMS.includes(a) ? "checked" : ""}>${swatch(a)}<span>${ARM[a].lab}${PAPER2.has(a) ? ' <span class="p2">(not in paper; exploratory)</span>' : a === "shufECG" ? ' <span class="p2">(placebo)</span>' : ""}</span></label>`).join("")}</div>
  <label class="h">Held-out panel</label><select id="c-panel"><option value="54" selected>54 non-coded (primary)</option><option value="58">58 items (paper 1 primary; supplement)</option><option value="exp">Expanded, ~330 (1:1, cal. 0.2 only; supplement)</option></select>
  <label class="cb" style="margin-top:5px" id="c-leakl"><input type="checkbox" id="c-leak" checked>Leakage-corrected masking</label>
  <div class="desc" id="c-leakd"></div>
  <label class="h">Show</label><select id="c-group"><option value="v">By variable</option><option value="d">By domain</option></select>
  <label class="h">Quick view</label>
  <div id="c-qv" class="qv"><label><input type="radio" name="c-qv" value="all" checked>All</label><label><input type="radio" name="c-qv" value="phys">Physiology</label><label><input type="radio" name="c-qv" value="echo">Echo</label></div>
  <label class="h">Domain</label><select id="c-dom"></select>
  <label class="h">Rank variables by</label><select id="c-rank"><option value="u">Unmatched |SMD|</option><option value="gain">ECG gain over PS alone</option></select>
  <label class="h">Show top <span id="c-nlab"></span></label><input type="range" id="c-n" min="5" max="54" value="54">
  <label class="h">Across trials (love plot)</label><select id="c-stat"><option value="median">Median</option><option value="mean">Mean</option></select>
  <label class="h">Balance threshold</label><select id="c-thr"><option value="0.1">|SMD| &lt; 0.10 (standard)</option><option value="0.15">|SMD| &lt; 0.15</option><option value="0.2">|SMD| &lt; 0.20</option></select>
  <label class="cb" style="margin-top:6px"><input type="checkbox" id="c-ref" checked>Threshold line</label>`;
  const onPanel = () => {
    const p = $("#c-panel").value, exp = p === "exp";
    const groups = exp ? D.E.buckets : p === "54" ? GROUPS58.filter(g => g !== "Coded record") : GROUPS58;
    const cur = $("#c-dom").value;
    $("#c-dom").innerHTML = `<option value="all">All domains</option><option value="phys">Physiology only (vitals, labs, echo)</option><option value="echo">Echocardiography only</option>` + groups.map(g => `<option>${esc(g)}</option>`).join("");
    if ([...$("#c-dom").options].some(o => o.value === cur)) $("#c-dom").value = cur;
    const nmax = itemsOf(p).length, r = $("#c-n"); r.max = nmax; r.value = $("#c-rank").value === "gain" ? 15 : nmax;
    $("#c-leak").disabled = exp; $("#c-leakl").classList.toggle("dis", exp);
    update();
  };
  $("#c-panel").onchange = onPanel;
  document.querySelectorAll('#c-qv input').forEach(r => r.onchange = () => { $("#c-dom").value = r.value; update(); });
  $("#c-dom").addEventListener("change", () => { const v = $("#c-dom").value, q = document.querySelector(`#c-qv input[value="${v}"]`);
    document.querySelectorAll('#c-qv input').forEach(x => x.checked = x === q); });
  $("#c-rank").onchange = () => { const r = $("#c-n"); r.value = $("#c-rank").value === "gain" ? 15 : r.max; update(); };
  for (const id of ["c-trials", "c-cfg", "c-rung", "c-leak", "c-group", "c-dom", "c-stat", "c-thr", "c-ref"]) $("#" + id).addEventListener("change", update);
  $("#c-n").oninput = update;
  $("#c-arms").onchange = update;
  $("#c-lad").onchange = update;
  document.querySelectorAll('#views input').forEach(r => r.onchange = () => {
    document.querySelectorAll('#views label').forEach(l => l.classList.toggle("on", l.querySelector("input").checked)); update(); });
  bindTips($("#svg"));
  onPanel();
}

/* =========================================================
   model: current selection
   ========================================================= */
function model() {
  const cfg = $("#c-cfg").value, rung = $("#c-rung").value, panel = $("#c-panel").value, leak = $("#c-leak").checked && panel !== "exp";
  const view = checked("view")[0] || "love", get = getter(panel, leak), arms = checked("c-arm"), T = trialSet($("#c-trials").value);
  const stat = $("#c-stat").value === "mean" ? mean : median, thr = +$("#c-thr").value, rank = $("#c-rank").value;
  $("#c-rdesc").textContent = RUNG[rung][1];
  const lm = [...new Set([...LK.rung[rung], ...arms.flatMap(a => LK.arm[a] ? [...LK.arm[a]] : [])])].filter(j => panel === "58" || D.vars[j].g !== "Coded record").map(j => D.vars[j].lab);
  $("#c-leakd").textContent = panel === "exp" ? "Not applied to the expanded panel." : leak ? (lm.length ? `Also masked here: ${lm.join(", ")}.` : "Nothing extra to mask for this base and these arms.")
    : "Off: only the items that are themselves PS inputs are masked (as in both papers).";
  ["c-group", "c-stat", "c-ref"].forEach(id => $("#" + id).classList.toggle("dim", view !== "love"));
  const dom = $("#c-dom").value, exp = panel === "exp";
  const isPhys = v => !exp ? v.g !== "Coded record" : v.g === "Additional labs & vitals" && !/missing/i.test(v.lab);
  let pool = itemsOf(panel).filter(v => dom === "all" || (dom === "phys" ? isPhys(v) : dom === "echo" ? !exp && v.g.startsWith("Echo") : v.g === dom));
  pool.forEach(v => { v.u = stat(T.map(t => get(cfg, rung, "unmatched", t, v.j)));
    v.gain = stat(T.map(t => { const b = get(cfg, rung, "base", t, v.j), e = get(cfg, rung, "ECG", t, v.j); return fin(b) && fin(e) ? b - e : NaN; })); });
  let vars = pool.filter(v => T.some(t => fin(get(cfg, rung, "base", t, v.j))));
  const N = +$("#c-n").value;
  $("#c-nlab").textContent = Math.min(N, vars.length) + " of " + vars.length;
  const key = rank === "gain" ? (v => v.gain) : (v => v.u);
  const ranked = [...vars].sort((a, b) => (fin(key(b)) ? key(b) : -9) - (fin(key(a)) ? key(a) : -9)).slice(0, N);
  const top = new Set(ranked.map(v => v.j));
  const restricted = rank === "gain" || N < vars.length;
  vars = rank === "gain" ? ranked : vars.filter(v => top.has(v.j));
  /* items for the ladder / method views: the same selection, re-masked at each base and method */
  const lvars = restricted ? vars : pool;
  return {cfg, rung, panel, leak, view, get, arms, T, stat, thr, rank, vars, lvars, exp, restricted, byDom: $("#c-group").value === "d"};
}
function update() {
  const M = model();
  if (M.view === "ladder") drawLadder(M); else if (M.view === "method") drawMethod(M); else drawLove(M);
  summary(M);
}

/* =========================================================
   A. love plot / domain view (lab deck)
   ========================================================= */
function drawLove(M) {
  const {cfg, rung, arms, T, stat, vars, get, exp, byDom} = M;
  const groups = exp ? D.E.buckets : GROUPS58;
  let rows = [];
  if (byDom) {
    for (const g of groups) { const vs = vars.filter(v => v.g === g); if (!vs.length) continue;
      const r = {lab: `${g} (${vs.length})`, g, val: {}, tipx: ""};
      for (const a of arms) r.val[a] = stat(T.map(t => mean(vs.map(v => get(cfg, rung, a, t, v.j)))));
      rows.push(r); }
  } else if (M.rank === "gain") {
    for (const v of vars) { const r = {lab: v.lab, g: v.g, val: {}, tipx: `${v.g}${v.def ? "; " + v.def : ""}; ECG gain ${f3(v.gain)}`};
      for (const a of arms) r.val[a] = stat(T.map(t => get(cfg, rung, a, t, v.j)));
      rows.push(r); }
  } else {
    for (const g of groups) for (const v of vars.filter(v => v.g === g)) { const r = {lab: v.lab, g, val: {}, tipx: v.def};
      for (const a of arms) r.val[a] = stat(T.map(t => get(cfg, rung, a, t, v.j)));
      rows.push(r); }
  }
  const W = 760, ml = byDom ? 210 : 186, mr = 24, mt = 28, mb = 40, H = Math.min(1000, Math.max(600, mt + mb + 12 * rows.length));
  $("#svg").setAttribute("viewBox", `0 0 ${W} ${H}`);
  const ph = H - mt - mb, rh = ph / Math.max(rows.length, 1);
  let xmax = 0.05; rows.forEach(r => arms.forEach(a => { if (fin(r.val[a])) xmax = Math.max(xmax, r.val[a]); }));
  xmax = Math.min(1.5, Math.ceil(xmax * 1.08 * 20) / 20);
  const xs = x => ml + (Math.min(x, xmax) / xmax) * (W - ml - mr);
  let s = `<text x="4" y="16" font-size="12.5" font-weight="700" fill="${NAVY}">${byDom ? "Mean |SMD| per domain" : "|SMD| after matching or weighting"} (${$("#c-stat").value} across ${T.length} trial${T.length > 1 ? "s" : ""}${M.rank === "gain" ? "; ranked by ECG gain" : ""}) · ${RUNG[rung][0]} · ${CSHORT[cfg]}</text>`;
  let prevG = null;
  rows.forEach((r, i) => {
    const y = mt + i * rh + rh / 2;
    if (i % 2 === 0) s += `<rect x="${ml}" y="${mt + i * rh}" width="${W - ml - mr}" height="${rh}" fill="#f5f5f8"/>`;
    if (r.g !== prevG && !byDom && M.rank !== "gain") { const gh = rh * rows.filter(q => q.g === r.g).length;
      s += `<line x1="4" x2="${W - mr}" y1="${mt + i * rh}" y2="${mt + i * rh}" stroke="#b9bbc8" stroke-width="0.8"/>`;
      const gl = GSHORT[r.g] || r.g; if (gh > gl.length * 5.2) s += `<text transform="translate(12 ${mt + i * rh + gh / 2}) rotate(-90)" font-size="9.5" font-weight="700" text-anchor="middle" fill="${RED}">${esc(gl)}</text>`; prevG = r.g; }
    const fs = Math.max(6, Math.min(12, rh * 0.8));
    if (rh >= 5.5) s += `<text x="${ml - 5}" y="${y + fs * 0.35}" font-size="${fs}" text-anchor="end" fill="${NAVY}">${esc(r.lab)}</text>`;
    const vals = arms.filter(a => fin(r.val[a]));
    if (vals.length > 1) { const mn = Math.min(...vals.map(a => r.val[a])), mx = Math.max(...vals.map(a => r.val[a]));
      s += `<line x1="${xs(mn)}" x2="${xs(mx)}" y1="${y}" y2="${y}" stroke="#c9cad4" stroke-width="1"/>`; }
    const red = fin(r.val.base) && fin(r.val.ECG) && r.val.base > 0 ? `<br>ECG vs PS alone: ${f1(100 * (1 - r.val.ECG / r.val.base))}% reduction` : "";
    const tipTxt = `<b>${esc(r.lab)}</b>${r.tipx ? "<br><span style='color:#666'>" + esc(r.tipx) + "</span>" : ""}<br>` + arms.map(a => `${ARM[a].lab}: ${f3(r.val[a])}`).join("<br>") + red;
    s += `<rect x="0" y="${mt + i * rh}" width="${W}" height="${rh}" fill="transparent" data-tip="${esc(tipTxt)}"/>`;
    for (const a of arms) if (fin(r.val[a])) s += marker(ARM[a].mk, xs(r.val[a]), y, Math.max(2.2, Math.min(5, rh * 0.38)), ARM[a].col, ARM[a].hollow, `pointer-events="none"`);
  });
  const y0 = mt + ph;
  s += `<line x1="${ml}" x2="${W - mr}" y1="${y0}" y2="${y0}" stroke="${NAVY}"/>`;
  const step = xmax > 0.6 ? 0.2 : xmax > 0.3 ? 0.1 : 0.05;
  for (let x = 0; x <= xmax + 1e-9; x += step) s += `<line x1="${xs(x)}" x2="${xs(x)}" y1="${y0}" y2="${y0 + 4}" stroke="${NAVY}"/><text x="${xs(x)}" y="${y0 + 16}" font-size="11" text-anchor="middle" fill="${NAVY}">${x.toFixed(2)}</text>`;
  s += `<text x="${(ml + W - mr) / 2}" y="${y0 + 33}" font-size="12" text-anchor="middle" fill="${NAVY}">|standardized mean difference|</text>`;
  const thr = M.thr;
  if ($("#c-ref").checked && thr <= xmax) s += `<line x1="${xs(thr)}" x2="${xs(thr)}" y1="${mt}" y2="${y0}" stroke="${RED}" stroke-dasharray="4 3" stroke-width="1.2" pointer-events="none"/>`;
  const msg = !arms.length ? "Select comparison arms" : !rows.length ? (M.exp ? "Expanded panel: 1:1 caliper 0.2 and PS-Demo, PS-CVD5, hdPS or PS-Clinical (with LVEF) only" : "No data for this selection") : "";
  if (msg) s += `<text x="${(ml + W - mr) / 2}" y="${mt + ph / 2}" font-size="${msg.length > 40 ? 14 : 20}" font-weight="700" text-anchor="middle" fill="${NAVY}" pointer-events="none"><tspan style="paint-order:stroke" stroke="#fff" stroke-width="6">${esc(msg)}</tspan></text>`;
  $("#svg").innerHTML = s;
  $("#cap").innerHTML = `Each row is one held-out characteristic (or domain), summarised across the selected trials. Hover for values. Items in a PS base are masked from that base${M.leak ? ", plus the leakage-corrected items" : ""}.`;
}

/* =========================================================
   B. information ladder: mean |SMD| by PS base, per arm
   ========================================================= */
function drawLadder(M) {
  const {cfg, arms, T, lvars, get, thr} = M, js = lvars.map(v => v.j);
  const LR = RUNGS.filter(r => checked("c-lad").includes(r));
  const W = 760, H = 600, ml = 64, mr = 24, mt = 100, mb = 70;
  $("#svg").setAttribute("viewBox", `0 0 ${W} ${H}`);
  const shown = arms.filter(a => a !== "unmatched");
  const L = {}, Uu = {}, RR = {}, RRx = {};
  for (const r of LR) {
    L[r] = {}; for (const a of shown) L[r][a] = mean(levels(get, cfg, r, a, T, js, thr).m);
    Uu[r] = mean(levels(get, cfg, r, "unmatched", T, js, thr).m);
    RR[r] = paired(get, cfg, r, "ECG", "base", T, js, thr, {nop: true});
    RRx[r] = {}; for (const a of shown) if (a !== "base" && a !== "ECG") RRx[r][a] = paired(get, cfg, r, a, "base", T, js, thr, {nop: true, noci: true});
  }
  let ymax = 0.02; for (const r of LR) { for (const a of shown) if (fin(L[r][a])) ymax = Math.max(ymax, L[r][a]); if (fin(Uu[r])) ymax = Math.max(ymax, Uu[r]); }
  ymax = Math.ceil(ymax * 1.1 * 50) / 50;
  const cw = (W - ml - mr) / Math.max(LR.length, 1), xs = i => ml + (i + 0.5) * cw, ys = y => mt + (1 - y / ymax) * (H - mt - mb);
  const fit = (txt, fs, w) => Math.max(6.5, Math.min(fs, 0.94 * cw / ((w || 0.6) * String(txt).length))).toFixed(1);
  const crowded = cw < 120, LSHORT = {clinical_nolvef: "PS-Clin. (no LVEF)", clinical: "PS-Clin. v1 (LVEF)"};
  let s = `<text x="${ml}" y="18" font-size="13" font-weight="700" fill="${NAVY}">Mean |SMD| as the PS gets more information (mean across ${T.length} trial${T.length > 1 ? "s" : ""}) · ${CSHORT[cfg]}</text>`;
  LR.forEach((r, i) => { if (r === PRIMARY) s += `<rect x="${ml + i * cw}" y="${mt - 50}" width="${cw}" height="${H - mb - mt + 50}" fill="#fbeceb"/>`;
    else if (SUPP.includes(r)) s += `<rect x="${ml + i * cw}" y="${mt - 50}" width="${cw}" height="${H - mb - mt + 50}" fill="#f5f5f8"/>`; });
  s += `<text x="${ml}" y="36" font-size="11.5" fill="${NAVY}">Red labels: change in mean |SMD| with + ECG vs PS alone at that base, paired by trial (95% bootstrap CI)</text>`;
  const step = ymax > 0.2 ? 0.05 : ymax > 0.1 ? 0.02 : 0.01;
  for (let y = 0; y <= ymax + 1e-9; y += step) s += `<line x1="${ml}" x2="${W - mr}" y1="${ys(y)}" y2="${ys(y)}" stroke="#ececf2"/><text x="${ml - 6}" y="${ys(y) + 4}" font-size="11" text-anchor="end" fill="${NAVY}">${y.toFixed(2)}</text>`;
  s += `<text transform="translate(16 ${(mt + H - mb) / 2}) rotate(-90)" font-size="12" text-anchor="middle" fill="${NAVY}">mean |SMD| over the selected items</text>`;
  if (thr <= ymax) s += `<line x1="${ml}" x2="${W - mr}" y1="${ys(thr)}" y2="${ys(thr)}" stroke="${RED}" stroke-dasharray="4 3" stroke-width="1"/><text x="${W - mr}" y="${ys(thr) - 4}" font-size="10" text-anchor="end" fill="${RED}">${thr.toFixed(2)}</text>`;
  /* unmatched reference */
  const up = LR.map((r, i) => fin(Uu[r]) ? `${xs(i)},${ys(Uu[r])}` : null).filter(Boolean);
  if (up.length > 1) s += `<polyline points="${up.join(" ")}" fill="none" stroke="${ARM.unmatched.col}" stroke-width="1.6" stroke-dasharray="6 4"/>`;
  LR.forEach((r, i) => { if (fin(Uu[r])) s += marker("x", xs(i), ys(Uu[r]), 5, ARM.unmatched.col, false, `data-tip="${esc(`<b>Unmatched</b> (${RUNG[r][0]} item mask)<br>mean |SMD| ${f3(Uu[r])}`)}"`); });
  if (up.length) { const r0 = LR.findIndex(r => fin(Uu[r])); s += `<text x="${xs(r0) - 12}" y="${ys(Uu[LR[r0]]) + 4}" font-size="11" fill="${ARM.unmatched.col}" text-anchor="end">Unmatched</text>`; }
  for (const a of shown) {
    const pts = LR.map((r, i) => fin(L[r][a]) ? `${xs(i)},${ys(L[r][a])}` : null).filter(Boolean);
    if (pts.length > 1) s += `<polyline points="${pts.join(" ")}" fill="none" stroke="${ARM[a].col}" stroke-width="1.8" ${ARM[a].hollow ? 'stroke-dasharray="3 3"' : ""} pointer-events="none"/>`;
  }
  LR.forEach((r, i) => {
    for (const a of shown) if (fin(L[r][a])) {
      const ex = a === "ECG" ? RR[r] : RRx[r][a];
      const t = `<b>${RUNG[r][0]}, ${ARM[a].lab}</b><br>mean |SMD| ${f3(L[r][a])}` + (ex ? `<br>vs PS alone: ${f1(ex.rr)}% reduction${fin(ex.lo) ? ` (${f1(ex.lo)} to ${f1(ex.hi)})` : ""}; ${ex.k} trials paired` : "");
      s += marker(ARM[a].mk, xs(i), ys(L[r][a]), 5.5, ARM[a].col, ARM[a].hollow, `data-tip="${esc(t)}"`);
    }
    const e = RR[r], hasE = S[cfg] && S[cfg][r] && fin(e.rr);
    const top = hasE ? (e.rr >= 0 ? f1(e.rr) + "% lower" : f1(-e.rr) + "% higher") : "–", ci = hasE && fin(e.lo) ? `reduction ${f1(e.lo)} to ${f1(e.hi)}` : "";
    s += `<text x="${xs(i)}" y="${mt - 40}" font-size="11" text-anchor="middle" fill="${RED}">+ ECG</text>`;
    s += `<text x="${xs(i)}" y="${mt - 25}" font-size="${fit(top, 12.5, 0.66)}" font-weight="700" text-anchor="middle" fill="${RED}">${top}</text>`;
    if (ci) s += `<text x="${xs(i)}" y="${mt - 11}" font-size="${fit(ci, 10.5)}" text-anchor="middle" fill="${RED}">${ci}</text>`;
    const nm = (crowded && LSHORT[r]) || RUNG[r][0], sub = RSUB[r] + (ROLE[r] && !crowded ? ` · ${ROLE[r]}` : "");
    s += `<text x="${xs(i)}" y="${H - mb + 20}" font-size="${fit(nm, 12.5, 0.66)}" font-weight="700" text-anchor="middle" fill="${r === PRIMARY ? RED : NAVY}">${nm}</text>`;
    s += `<text x="${xs(i)}" y="${H - mb + 36}" font-size="${fit(sub, 10.5)}" text-anchor="middle" fill="${r === PRIMARY ? RED : NAVY}">${sub}</text>`;
  });
  s += `<line x1="${ml}" x2="${W - mr}" y1="${H - mb}" y2="${H - mb}" stroke="${NAVY}"/>`;
  s += `<text x="${(ml + W - mr) / 2}" y="${H - 12}" font-size="12" text-anchor="middle" fill="${NAVY}">PS base, in order of information →</text>`;
  if (!shown.length || !LR.length) s += `<text x="${(ml + W - mr) / 2}" y="${(mt + H - mb) / 2}" font-size="20" font-weight="700" text-anchor="middle" fill="${NAVY}">${!LR.length ? "Select ladder levels" : "Select comparison arms"}</text>`;
  $("#svg").innerHTML = s;
  $("#cap").innerHTML = `Points: mean over trials of each trial's mean |SMD| on its observed items (${js.length} item${js.length === 1 ? "" : "s"} selected${M.restricted ? ", as chosen in the love plot" : ""}); items in each base are masked from that base${M.leak ? ", plus the leakage-corrected items" : ""}, so the item set shrinks at PS-Clinical (less so without LVEF, where the echo items and observed LVEF stay in). Labels and tooltips are paired within trial. Default levels = the main ladder: PS-Demo, PS-CVD5 (primary, shaded red), PS-CVD10 (comparison), hdPS, PS-Clinical (no LVEF); tick PS-Flags (supplement) or PS-Clinical (with LVEF, v1 reference) under "Ladder levels" (shaded grey). PS-Flags loses one trial with fewer than 11 matched pairs.${M.exp ? " Expanded panel: no PS-CVD10, PS-Flags or PS-Clinical (no LVEF) data." : ""}`;
}

/* =========================================================
   C. method comparison: relative reduction vs PS alone, six PS methods
   ========================================================= */
function drawMethod(M) {
  const {rung, arms, T, lvars, get, thr} = M, js = lvars.map(v => v.j);
  let cmp = arms.filter(a => a !== "unmatched" && a !== "base"); if (!cmp.length) cmp = ["ECG", "shufECG"];
  const R = {}; let lo = -5, hi = 5;
  for (const c of CFGS) { R[c] = {}; for (const a of cmp) { const x = paired(get, c, rung, a, "base", T, js, thr, {nop: M.rank === "gain"}); R[c][a] = x;
    for (const v of [x.rr, x.lo, x.hi]) if (fin(v)) { lo = Math.min(lo, v); hi = Math.max(hi, v); } } }
  lo = Math.floor(lo / 5) * 5; hi = Math.ceil(hi / 5) * 5;
  const W = 760, H = 600, ml = 64, mr = 20, mt = 56, mb = 76;
  $("#svg").setAttribute("viewBox", `0 0 ${W} ${H}`);
  const gw = (W - ml - mr) / CFGS.length, xs = (i, k) => ml + i * gw + gw * (k + 1) / (cmp.length + 1), ys = y => mt + (hi - y) / (hi - lo) * (H - mt - mb);
  let s = `<text x="${ml}" y="18" font-size="13" font-weight="700" fill="${NAVY}">Relative reduction in mean |SMD| vs PS alone, by PS method · ${RUNG[rung][0]} · ${T.length} trial${T.length > 1 ? "s" : ""}</text>`;
  s += `<text x="${ml}" y="36" font-size="11.5" fill="${NAVY}">Point = estimate; bar = 95% bootstrap CI (4,000 trial resamples); above 0 = better balance than PS alone</text>`;
  const step = hi - lo > 40 ? 10 : 5;
  CFGS.forEach((c, i) => { if (i % 2 === 0) s += `<rect x="${ml + i * gw}" y="${mt}" width="${gw}" height="${H - mt - mb}" fill="#f5f5f8"/>`; });
  for (let y = lo; y <= hi + 1e-9; y += step) s += `<line x1="${ml}" x2="${W - mr}" y1="${ys(y)}" y2="${ys(y)}" stroke="${y === 0 ? NAVY : "#ececf2"}" ${y === 0 ? 'stroke-width="1.2"' : ""}/><text x="${ml - 6}" y="${ys(y) + 4}" font-size="11" text-anchor="end" fill="${NAVY}">${y}%</text>`;
  s += `<text transform="translate(16 ${(mt + H - mb) / 2}) rotate(-90)" font-size="12" text-anchor="middle" fill="${NAVY}">relative reduction in mean |SMD|, %</text>`;
  CFGS.forEach((c, i) => {
    cmp.forEach((a, k) => { const x = R[c][a]; if (!fin(x.rr)) return; const X = xs(i, k);
      if (fin(x.lo)) s += `<line x1="${X}" x2="${X}" y1="${ys(x.lo)}" y2="${ys(x.hi)}" stroke="${ARM[a].col}" stroke-width="1.8"/>`;
      const t = `<b>${CFG[c]}</b><br>${ARM[a].lab} vs PS alone, ${RUNG[rung][0]}<br>relative reduction ${f1(x.rr)}%${fin(x.lo) ? ` (${f1(x.lo)} to ${f1(x.hi)})` : ""}<br>mean |SMD| ${f3(x.m_ref)} → ${f3(x.m_arm)}; lower in ${x.lower}/${x.k}${fin(x.p_m) ? `, P ${fmtp(x.p_m)}` : ""}<br>% balanced ${f1(x.pct_ref)} → ${f1(x.pct_arm)}; better in ${x.better}/${x.k}${fin(x.p) ? `, P ${fmtp(x.p)}` : ""}`;
      s += marker(ARM[a].mk, X, ys(x.rr), 5.5, ARM[a].col, ARM[a].hollow, `data-tip="${esc(t)}"`);
      s += `<text x="${X}" y="${(fin(x.lo) ? ys(x.hi) : ys(x.rr)) - 7}" font-size="10" text-anchor="middle" fill="${ARM[a].col}" pointer-events="none">${f1(x.rr)}</text>`; });
    const nm = CSHORT[c];
    s += `<text x="${ml + (i + 0.5) * gw}" y="${H - mb + 20}" font-size="12.5" font-weight="${c === "main" ? 700 : 400}" text-anchor="middle" fill="${NAVY}">${nm}</text>`;
    s += `<text x="${ml + (i + 0.5) * gw}" y="${H - mb + 36}" font-size="10.5" text-anchor="middle" fill="${NAVY}">${["primary", "matching", "matching", "weighting", "weighting", "1:1, cal. 0.2"][i]}</text>`;
  });
  let lx = ml; cmp.forEach(a => { s += `<g transform="translate(${lx} ${H - 22})">${marker(ARM[a].mk, 6, -4, 5, ARM[a].col, ARM[a].hollow)}<text x="16" y="0" font-size="12" fill="${NAVY}">${ARM[a].lab}</text></g>`; lx += 30 + ARM[a].lab.length * 7.2; });
  $("#svg").innerHTML = s;
  $("#cap").innerHTML = `Paired within trial (items observed in both arms; ${js.length} item${js.length === 1 ? "" : "s"} selected${M.restricted ? ", as chosen in the love plot" : ""}). Hover for mean |SMD|, % balanced and sign-flip P${M.rank === "gain" ? " (not shown: items chosen by ECG gain)" : ""}. Only checked arms are shown (+ ECG and + permuted ECG if none).${M.exp ? " Expanded panel: 1:1 caliper 0.2 only." : ""}`;
}

/* =========================================================
   summary panel (selected base x method)
   ========================================================= */
function summary(M) {
  const {cfg, rung, arms, T, vars, get, thr, panel} = M, js = vars.map(v => v.j), thrL = thr.toFixed(2);
  const one = T.length < 2, gain = M.rank === "gain";
  let h = `<div class="sel"><b>${RUNG[rung][0]}</b> · ${CFG[cfg]} · ${panel === "exp" ? "expanded panel" : panel + "-item panel"}${M.leak ? " (leakage-corrected)" : ""} · ${js.length} shown · ${T.length} trial${T.length > 1 ? "s" : ""}${one ? ` (${esc(D.trials[T[0]].full)})` : ""}</div>`;
  if (!arms.length) { $("#sum").innerHTML = h + EMPTY("Select comparison arms"); return; }
  h += `<h4>Balance, |SMD| &lt; ${thrL}</h4><table><tr><th>Arm</th><th>mean |SMD|</th><th>% items</th><th>trials mean &lt; ${thrL}</th></tr>`;
  for (const a of arms) { const L = levels(get, cfg, rung, a, T, js, thr), ok = L.m.filter(fin);
    h += `<tr><td>${swatch(a)} ${SL[a]}</td><td>${f3(mean(L.m))}</td><td>${f1(mean(L.p))}</td><td>${ok.length ? `${ok.filter(x => x < thr).length}/${ok.length}` : "–"}</td></tr>`; }
  h += `</table>`;
  const cmp = arms.filter(a => a !== "base" && a !== "unmatched");
  if (cmp.length) {
    const P = cmp.map(a => [a, paired(get, cfg, rung, a, "base", T, js, thr, {nop: gain})]);
    h += `<h4 style="margin-top:12px">vs PS alone, paired by trial</h4>`;
    if (gain) h += `<div class="note" style="color:${RED}">Variables chosen by ECG gain: the comparisons below are descriptive (selected on the result), so P is not shown.</div>`;
    h += `<table><tr><th>% balanced</th><th>PS alone → arm</th><th>Δ pts</th><th>better</th><th>P</th></tr>`;
    for (const [a, x] of P) h += `<tr class="${a === "ECG" ? "hl" : ""}"><td>${SL[a]}</td><td>${f1(x.pct_ref)} → ${f1(x.pct_arm)}</td><td>${sgn1(x.dpts)}</td><td>${x.k ? `${x.better}/${x.k}` : "–"}</td><td>${gain || one ? "–" : fmtp(x.p)}</td></tr>`;
    h += `</table><table style="margin-top:8px"><tr><th>mean |SMD|</th><th>PS alone → arm</th><th>lower</th><th>P</th><th>rel. reduction</th></tr>`;
    for (const [a, x] of P) h += `<tr class="${a === "ECG" ? "hl" : ""}"><td>${SL[a]}</td><td>${f3(x.m_ref)} → ${f3(x.m_arm)}</td><td>${x.k ? `${x.lower}/${x.k}` : "–"}</td><td>${gain || one ? "–" : fmtp(x.p_m)}</td><td>${f1(x.rr)}%${fin(x.lo) ? `<span class="ci">${f1(x.lo)} to ${f1(x.hi)}</span>` : ""}</td></tr>`;
    h += `</table>`;
    const kmin = Math.min(...P.map(([, x]) => x.k));
    if (kmin < T.length) h += `<div class="note">Some trials drop out of a contrast (failed cell, fewer than 11 matched pairs, or no observed items): k = trials paired, shown as the denominator.</div>`;
  }
  h += `<div class="note">"% items" and "% balanced": share of a trial's items with |SMD| &lt; ${thrL}, averaged over trials. "better" = % balanced higher; "lower" = mean |SMD| lower. P: exact one-sided sign-flip test over trials. Relative reduction: 1 − ratio of across-trial means, 95% CI from 4,000 trial resamples (seed 20261001).${M.restricted && !gain ? " Items restricted to the top of the unmatched-|SMD| ranking." : ""} Per-arm rows use each arm's observed items; paired rows use items observed in both arms.</div>`;
  if (panel === "exp" && arms.some(a => PAPER2.has(a) || a === "ECG") && (rung === "hdPS200" || arms.some(a => PAPER2.has(a))))
    h += `<div class="note" style="color:${RED}">Expanded panel: most items are coded-record characteristics (comorbidities, medications, use) that CLMBR-T and the hdPS codes also see, so gains with those are partly mechanical (not leakage-masked).</div>`;
  if (rung === PRIMARY && cfg === "main" && M.leak && $("#c-trials").value === "v2" && panel === "54" && js.length === 54)
    h += `<div class="note"><b>Primary analysis (pipeline.md; ECG-only paper):</b> PS-CVD5 + ECG vs PS-CVD5, 1:1 caliper 0.2, fixed L2 C = 1, 54 leakage-corrected items, provisional v2 set (29 trials, not frozen). Version 1 cohorts; values will change with the spec-v2 cohorts.</div>`;
  if (arms.some(a => PAPER2.has(a))) h += `<div class="note">CLMBR-T arms are exploratory and not in the paper.</div>`;
  if (panel !== "exp" && rung === "P1" && cfg === "main" && !M.leak && $("#c-trials").value === "s32" && panel === "58" && js.length === 58)
    h += `<div class="note"><b>Paper 1 primary analysis</b> (PS-Demo + ECG): 11.4% (6.3 to 16.0); 49.8% → 55.0% balanced; 22/32 trials; P = .002.</div>`;
  $("#sum").innerHTML = h;
}

/* headless-check API: point estimates on all items of a panel (no domain filter or ranking) */
window.TRACE = {pair: s => { const get = getter(s.panel, s.leak && s.panel !== "exp"), js = itemsOf(s.panel).map(v => v.j);
  return paired(get, s.cfg, s.rung, s.arm, s.ref || "base", trialSet(s.trials), js, s.thr || 0.1); },
  level: s => { const get = getter(s.panel, s.leak && s.panel !== "exp"), js = itemsOf(s.panel).map(v => v.j);
  return mean(levels(get, s.cfg, s.rung, s.arm, trialSet(s.trials), js, s.thr || 0.1).m); }};
init();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
