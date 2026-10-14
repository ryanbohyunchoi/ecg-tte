#!/usr/bin/env python
"""Step 2 of the queue 2026-10-14: the headline numbers on the 31-trial primary set (s31 = paper 1's 32 minus PROTECT AF, excluded
at feasibility: smaller arm < 350), each next to its 32-trial value (paper 1's 32 with PROTECT AF; now a sensitivity analysis).

Sources (existing cells only; nothing refitted):
  audits/claude-v21-paper2/core/restricted_cells.parquet, audits/claude-v1-ps10/cells/restricted_cells.parquet,
  audits/claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet (PS-Clinical (no LVEF), 5-draw MI) via
  build_balance_explorer.load_grid (as the lab deck and Figure 2);
  the s31 Python summaries (scripts/s31/s31_summaries.py, sets S31 and S32; S32 gated equal to the committed runs);
  robustness only: audits/claude-v2-cohorts/summary/restricted_random_removal_cells.parquet (via the summaries),
  audits/claude-v1-audit/code/restricted_sens_no_index_day_ecg.parquet (ECGs >= 1 day before index),
  audits/claude-r2/core/restricted_cells.parquet (R2: CV log-loss penalty; scenario S1 = PS-CVD5 analog, 1:1 caliper 0.2).
Every summary value is re-derived from the cells with build_balance_explorer.pair_stats (max deviations reported); the agreement
metrics use the deck's code (build_lab_deck_v2.agree_py / bshuf_py) on the cells' log HRs; the CV-penalty and index-day rows are
gated against their published 32-trial values before the s31 value is taken.

Outputs: audits/claude-s31-20261014/s31_numbers.json (aggregates) and docs/s31/S31_RESULTS.md. Aggregates only: no patient counts,
no n_pairs, retention or ESS.

Usage (tte-analysis env): python scripts/s31/s31_numbers.py
"""
import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_balance_explorer as BE  # noqa: E402
import build_lab_deck_v2 as V2  # noqa: E402

A = BE.A
OUT = A / "claude-s31-20261014"
DOC = ROOT / "docs/s31/S31_RESULTS.md"
MI_V1 = A / "claude-v1-psclin-mi/cells/restricted_cells_v1_mi_v1layout.parquet"
NOIDX = A / "claude-v1-audit/code/restricted_sens_no_index_day_ecg.parquet"
R2C = A / "claude-r2/core/restricted_cells.parquet"
SETS = {"S31": "s31", "S32": "s32"}
RUNGS = [("P1", "PS-Demo"), ("P5", "PS-CVD5"), ("PS10", "PS-CVD10"), ("clinical_nolvef", "PS-Clinical (no LVEF, MI)"), ("hdPS200", "hdPS")]
ARMS = [("ECG", "+ ECG"), ("CLMBR", "+ CLMBR-T"), ("ECG+CLMBR", "+ CLMBR-T + ECG")]
CFGL = {"main": "1:1, caliper 0.2", "cal01": "1:1, caliper 0.1", "m13": "1:3", "iptw": "IPTW", "overlap": "Overlap weights",
        "gbm": "Gradient-boosted PS"}
ITEMS = BE.items("54")
DEV = {"rr": 0.0, "p": 0.0, "lower_mismatch": 0, "level": 0.0}


def load():
    """the lab deck's version 1 grid: BE.load_grid with PS-Clinical (no LVEF) = the 5-draw MI cells."""
    old = BE.NOLVEF
    BE.NOLVEF = MI_V1
    try:
        g = BE.load_grid()
    finally:
        BE.NOLVEF = old
    return g


def fx(x, d=1):
    t = f"{x:.{d}f}"
    return t[1:] if t in ("-0.0", "-0.00", "-0.000") else t


def fp(p):
    return V2.fp(p)


def pv(p):
    return V2.pv(p)  # 'P < .001' or 'P = .xx'


# ---------------------------------------------------------------- summaries (S31 / S32) with an independent re-derivation
VC = pd.read_csv(OUT / "summary_v1/contrasts.csv")
MC = pd.read_csv(OUT / "summary_mi/contrasts.csv")
VD = pd.read_csv(OUT / "summary_v1/domains.csv")
VL = pd.read_csv(OUT / "summary_v1/ladder.csv")
ML = pd.read_csv(OUT / "summary_mi/ladder.csv")
RRS = pd.read_csv(OUT / "summary_v1/random_removal_summary.csv")


def srow(st, rg, a, b="base", cfg="main"):
    if rg == "clinical_nolvef":
        M = MC[(MC.set == st) & (MC.config == cfg) & (MC.rung_a == "clinical_nolvef_mi") & (MC.rung_b == "clinical_nolvef_mi") & (MC.arm_a == a)
               & (MC.arm_b == b) & MC.kind.isin(["within", "ladder"])]
    else:
        M = VC[(VC.set == st) & (VC.config == cfg) & (VC.rung_a == rg) & (VC.rung_b == rg) & (VC.arm_a == a) & (VC.arm_b == b) & (VC.kind == "within")]
    assert len(M) == 1, (st, rg, a, b, cfg, len(M))
    return M.iloc[0]


def contrast(G, trials, st, rg, a, b="base", cfg="main"):
    s = srow(st, rg, a, b, cfg)
    r = BE.pair_stats(G, cfg, rg, a, b, BE.trial_set(trials, SETS[st]), "54", True)
    two = s.sided != "one"
    DEV["rr"] = max(DEV["rr"], abs(r["rr"] - s.relred54), abs(r["lo"] - s.relred54_lo), abs(r["hi"] - s.relred54_hi))
    DEV["p"] = max(DEV["p"], abs((r["p_m_two"] if two else r["p_m"]) - s.m54_p), abs((r["p_two"] if two else r["p"]) - s.lt01_54_p))
    DEV["lower_mismatch"] += int(f"{r['lower']}/{r['k']}" != s.m54_better)
    return dict(rr=s.relred54, lo=s.relred54_lo, hi=s.relred54_hi, p=s.m54_p, sided=s.sided, lower=s.m54_better, k=int(r["k"]),
                m_ref=s.m54_b, m_arm=s.m54_a, pct_ref=s.lt01_54_b, pct_arm=s.lt01_54_a, dpts=s.lt01_54_diff, better=s.lt01_54_better,
                p_pct=s.lt01_54_p, cluster_p=s.m54_cluster_p, n_clusters=int(s.m54_n_clusters), loo_max_p=s.m54_loo_max_p,
                q_fam=s.q_m54_p_fam, absd_ref=s.absd_b, absd_arm=s.absd_a, absd_closer=s.absd_better, absd_p=s.absd_p, bshuf_p=s.bshuf_p)


def level(G, T, rg, a):
    M = G.block("main", rg, a, True)[np.ix_(T, ITEMS)]
    ok = np.isfinite(M).any(1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return float(np.nanmean(M[ok], 1).mean()), int(ok.sum())


def ladder_check(st, rg, a, v):
    if rg == "clinical_nolvef":
        L = ML[(ML.set == st) & (ML.rung == "clinical_nolvef_mi") & (ML.config == "main") & (ML.arm == a) & (ML.panel.astype(str) == "54")]
    else:
        L = VL[(VL.set == st) & (VL.rung == rg) & (VL.config == "main") & (VL.arm == a) & (VL.panel.astype(str) == "54")]
    if len(L) == 1:
        DEV["level"] = max(DEV["level"], abs(float(L.mean_smd.iloc[0]) - v))
        return True
    return False


# ---------------------------------------------------------------- agreement (deck code: build_lab_deck_v2.agree_py / bshuf_py)
def deck_D(g, trials):
    R = g["R"]
    rb = R[(R.rung == "P5") & (R.config == "main") & (R.arm == "base")].set_index("trial").loc[g["tids"]]
    tr = [dict(t, rb=round(float(x.rb), 6), rs=round(float(x.rs), 6)) for t, (_, x) in zip(trials, rb.iterrows())]
    return dict(trials=tr, EST={"v1": V2.est_block(g)})


def agreement(D, ts, rg="P5", cfg="main"):
    T = BE.trial_set(D["trials"], ts)
    E = D["EST"]["v1"][cfg][rg]
    out = {}
    for a in ("base", "ECG", "shufECG"):
        m = V2.agree_py(D, "v1", cfg, rg, a, T)
        x = dict(k=m["k"], absd=m["absd"], r=m["r"], est_agree=m["ea"], std_agree=m["cons"])
        if a != "base":
            TT = [t for t in T if E[a][t] is not None and E["base"][t] is not None]
            x.update(closer=f"{m['closer']}/{m['kp']}", p_closer=m["p_closer"],
                     bshuf_p=V2.bshuf_py(np.array([E[a][t][0] for t in TT]), np.array([E["base"][t][0] for t in TT]),
                                         np.array([D["trials"][t]["rb"] for t in TT]), two=a == "shufECG"))
        out[a] = x
    return out


# ---------------------------------------------------------------- per-trial 54-item relative reduction (index-day, R2 CV penalty)
def relred_from_blocks(Mb, Ma):
    m = np.isnan(Ma) | np.isnan(Mb)
    Ma, Mb = np.where(m, np.nan, Ma), np.where(m, np.nan, Mb)
    ok = (~m).sum(1) > 0
    b, a = np.nanmean(Mb[ok], 1), np.nanmean(Ma[ok], 1)
    rr, lo, hi = BE.relred_ci(b, a)
    d = b - a
    return dict(rr=rr, lo=lo, hi=hi, lower=f"{int((d > 0).sum())}/{int(ok.sum())}", p=BE.signflip_1s(d), k=int(ok.sum()))


def no_index_day(g, keys):
    N = pd.read_parquet(NOIDX)
    cols = [f"smd:{BE.VN[j]}" for j in ITEMS]
    assert N.n_pairs_ge11.all()
    out = {}
    for st, ks in keys.items():
        tids = [t for t in g["tids"] if t in ks]
        blk = {a: N[N.arm == a].set_index("trial").loc[tids][cols].abs().to_numpy(float) for a in ("base", "ECG")}
        out[st] = relred_from_blocks(blk["base"], blk["ECG"])
    return out


def r2_cv(keys):
    R = pd.read_parquet(R2C)
    R = R[(R.scenario == "S1") & (R.estimator == "match02") & R.arm.isin(["base", "ECG"])]
    cols = [f"smd:{BE.VN[j]}" for j in ITEMS]
    fail = R.cell_failed.fillna("").astype(str).ne("") | (R.n_pairs.notna() & (R.n_pairs < BE.MIN_PAIRS))
    R = R.assign(failed=fail)
    out = {}
    for st, ks in keys.items():
        blk = {}
        for a in ("base", "ECG"):
            h = R[(R.arm == a) & R.trial.isin(ks)].sort_values("idx")
            M = h[cols].abs().to_numpy(float)
            M[h.failed.to_numpy()] = np.nan
            blk[a] = M
        out[st] = relred_from_blocks(blk["base"], blk["ECG"])
    return out


def main():
    os.umask(0o077)
    g = load()
    trials = BE.trials_meta(g)
    G = BE.Grid(g["G"], g["U"], g["ex"])
    keys = {st: {trials[i]["id"] for i in BE.trial_set(trials, ts)} for st, ts in SETS.items()}
    assert len(keys["S31"]) == 31 and keys["S32"] - keys["S31"] == {"protect-af"}
    N = {}
    for st, ts in SETS.items():
        T = BE.trial_set(trials, ts)
        x = dict(n_trials=len(T))
        x["primary"] = contrast(G, trials, st, "P5", "ECG")
        x["placebo"] = dict(shuf_vs_base=contrast(G, trials, st, "P5", "shufECG"), ecg_vs_shuf=contrast(G, trials, st, "P5", "ECG", "shufECG"))
        dm = VD[(VD.set == st) & (VD.config == "main") & (VD.contrast == "P5: ECG vs base")]
        x["domains"] = {r.domain: dict(n_items=int(r.n_items), rr=r.relred, lo=r.relred_lo, hi=r.relred_hi, m_ref=r.mean_b, m_arm=r.mean_a,
                                       lower=r.better, p=r.p) for r in dm.itertuples()}
        lad = {}
        for rg, lab in RUNGS:
            z = dict(label=lab)
            for a in ("unmatched", "base", "ECG", "CLMBR", "ECG+CLMBR"):
                v, k = level(G, T, rg, a)
                z[f"level_{a}"], z[f"k_{a}"] = v, k
                if a != "unmatched":
                    z[f"level_{a}_in_summary"] = ladder_check(st, rg, a, v)
            for a, _ in ARMS:
                z[a] = contrast(G, trials, st, rg, a)
            z["shufECG"] = contrast(G, trials, st, rg, "shufECG")
            lad[rg] = z
        x["ladder"] = lad
        x["methods"] = {c: contrast(G, trials, st, "P5", "ECG", cfg=c) for c in CFGL}
        x["mi_draws"] = [float(MC[(MC.set == st) & (MC.config == "main") & (MC.rung_a == f"clinical_nolvef#{k}") & (MC.arm_a == "ECG")
                                  & (MC.arm_b == "base")].iloc[0].relred54) for k in range(1, 6)]
        rr = RRS[(RRS.set == st) & (RRS.arm == "ECG")].iloc[0]
        x["spec_v2_fixes"] = dict(v1=rr.relred54_v1, v2=rr.relred54_v2, random_median=rr.relred54_random_median, random_p5=rr.relred54_random_p5,
                                  random_p95=rr.relred54_random_p95, draws=int(rr.draws))
        N[st] = x
    # set-dependent rows computed from the cells: placebo range over five trial sets, framework v2.0 sets, agreement by tier
    sets5 = {"S31": ["s31", "q37:Excellent,Good", "f37", "v2", "v2c"], "S32": ["s32", "q:Excellent,Good", "all", "v2", "v2c"]}
    for st, ss in sets5.items():
        N[st]["placebo"]["ecg_vs_shuf_sets"] = {ts: dict(rr=(r := BE.pair_stats(G, "main", "P5", "ECG", "shufECG", BE.trial_set(trials, ts), "54", True))["rr"],
                                                         lo=r["lo"], hi=r["hi"], k=r["k"]) for ts in ss}
        N[st]["framework_v2"] = {ts: dict(rr=(r := BE.pair_stats(G, "main", "P5", "ECG", "base", BE.trial_set(trials, ts), "54", True))["rr"],
                                          lo=r["lo"], hi=r["hi"], k=r["k"], p=r["p_m"]) for ts in ("v2", "v2c")}
    D = deck_D(g, trials)
    tiers = {"S31": [("Excellent + Good", "q37:Excellent,Good"), ("Moderate", "q37:Moderate"), ("Limited", "q37:Limited")],
             "S32": [("Excellent + Good", "q:Excellent,Good"), ("Moderate", "q:Moderate"), ("Limited", "q:Limited")]}
    for st, grp in tiers.items():
        N[st]["agreement_by_tier"] = {lab: dict(trials=len(BE.trial_set(trials, ts)), **agreement(D, ts)) for lab, ts in grp}
        N[st]["agreement_set"] = agreement(D, SETS[st])
        N[st]["agreement_all"] = agreement(D, "f37" if st == "S31" else "all")
        N[st]["agreement_v2"] = agreement(D, "v2")
        N[st]["cvd10_agreement"] = agreement(D, SETS[st], rg="PS10")
    # agreement gate: the deck code reproduces the summaries' |dlog HR| and benchmark-permutation P on both sets
    agate = 0.0
    for st in SETS:
        s = srow(st, "P5", "ECG")
        a = N[st]["agreement_set"]["ECG"]
        agate = max(agate, abs(a["absd"] - s.absd_a), abs(N[st]["agreement_set"]["base"]["absd"] - s.absd_b), abs(a["bshuf_p"] - s.bshuf_p))
    # robustness rows from other runs, gated on the published 32-trial values first
    ni = no_index_day(g, keys)
    assert f"{ni['S32']['rr']:.1f}|{ni['S32']['lo']:.1f}|{ni['S32']['hi']:.1f}|{ni['S32']['lower']}" == "6.9|0.4|13.4|19/32", ni["S32"]
    cv = r2_cv(keys)
    assert f"{cv['S32']['rr']:.1f}|{cv['S32']['lo']:.1f}|{cv['S32']['hi']:.1f}" == "5.7|-0.5|11.4", cv["S32"]
    for st in SETS:
        N[st]["no_index_day_ecg"] = ni[st]
        N[st]["cv_penalty_r2"] = cv[st]
    # primary gate: the s31 primary from the summaries equals the cells' pair_stats; the 32-trial primary is the published 8.8%
    p32 = N["S32"]["primary"]
    assert f"{p32['rr']:.1f}|{p32['lo']:.1f}|{p32['hi']:.1f}|{p32['lower']}" == "8.8|4.4|13.3|21/32", p32
    assert DEV["rr"] < 1e-6 and DEV["p"] < 1e-9 and DEV["lower_mismatch"] == 0 and DEV["level"] < 1e-9 and agate < 1e-6, (DEV, agate)  # deck log HRs: 8 decimals
    res = dict(basis="version 1 cohorts; PS-CVD5 primary; fixed C = 1; 1:1 caliper 0.2 (main); 54 held-out items, leakage-corrected masks; "
                     "PS-Clinical (no LVEF), 5-draw MI",
               sets=dict(S31="s31: paper 1's 32 (v19 tiers, Limited excluded) minus PROTECT AF (excluded at feasibility: smaller arm < 350)",
                         S32="paper 1's 32 (with PROTECT AF; sensitivity)"),
               checks=dict(summary_vs_cells_max_rr_dev=DEV["rr"], summary_vs_cells_max_p_dev=DEV["p"], lower_mismatches=DEV["lower_mismatch"],
                           ladder_levels_vs_summary_max_dev=DEV["level"], agreement_deck_code_vs_summary_max_dev=agate,
                           no_index_day_gate_S32="6.9 (0.4 to 13.4), 19/32", cv_penalty_gate_S32="5.7 (-0.5 to 11.4)",
                           primary_gate_S32="8.8 (4.4 to 13.3), 21/32",
                           summary_gate=json.load(open(OUT / "summary_gate.json"))["passed"]),
               S31=N["S31"], S32=N["S32"])
    json.dump(res, open(OUT / "s31_numbers.json", "w"), indent=1, default=float)
    print("wrote", OUT / "s31_numbers.json", "checks", res["checks"])
    write_md(res)


def ci(x):
    return f"{fx(x['rr'])}% ({fx(x['lo'])} to {fx(x['hi'])})"


def write_md(res):
    a, b = res["S31"], res["S32"]
    L = ["# The 31-trial primary set (s31): headline numbers next to the 32-trial values", "",
         "Queue 2026-10-14, Step 2 (`docs/queue/QUEUE_2026_10_14_S31.md`; `pipeline.md` update 2026-10-14). Built by "
         "`scripts/s31/s31_numbers.py` from the existing cells and the s31 Python summaries (`scripts/s31/s31_summaries.py`).", "",
         "- **s31 (primary):** paper 1's 32 trials (v19 tiers, Limited excluded) minus **PROTECT AF**, now excluded at feasibility "
         "(smaller arm < 350 patients with an ECG). Trial flow: 99 → 37 feasible → 31 analysed (tiers of the 37: 3 / 11 / 17 / 6).",
         "- **32 (sensitivity):** paper 1's 32 with PROTECT AF, the previous primary. The size-rule change is post hoc: it was made after "
         "near-separation of the rich PS models was seen in PROTECT AF.",
         "- **Design (unchanged):** version 1 cohorts; PS-CVD5 primary; fixed C = 1; 1:1 nearest neighbour, caliper 0.2; 54 held-out "
         "items with the leakage-corrected masks; PS-Clinical without LVEF, 5-draw MI.",
         "- **Endpoint:** relative reduction in the across-trial mean |SMD| (95% CI from 4,000 trial resamples); P = exact sign-flip "
         "across trials on the per-trial mean |SMD| (one-sided for a representation vs its base or placebo, two-sided otherwise).",
         "- **Checks:** "
         f"the S32 rows of every summary equal the committed runs (to ≤ 1.5e-14); every summary value is re-derived from the cells "
         f"(max deviation: {res['checks']['summary_vs_cells_max_rr_dev']:.1e} percentage points, {res['checks']['summary_vs_cells_max_p_dev']:.1e} in P; "
         f"0 mismatches in trial counts); the index-day and CV-penalty rows reproduce their published 32-trial values before the s31 value is taken.",
         "", "## 1. Primary: PS-CVD5 + ECG vs PS-CVD5", "", "| Quantity | s31 (primary) | 32 trials (sensitivity) |", "|---|---|---|"]
    pa, pb = a["primary"], b["primary"]
    L += [f"| Relative reduction in mean \\|SMD\\| | **{ci(pa)}** | {ci(pb)} |",
          f"| One-sided sign-flip P (mean \\|SMD\\|) | {fp(pa['p'])} | {fp(pb['p'])} |",
          f"| Trials with lower mean \\|SMD\\| | {pa['lower']} | {pb['lower']} |",
          f"| Mean \\|SMD\\|, PS-CVD5 → + ECG | {pa['m_ref']:.3f} → {pa['m_arm']:.3f} | {pb['m_ref']:.3f} → {pb['m_arm']:.3f} |",
          f"| Items with \\|SMD\\| < 0.1 | {pa['pct_ref']:.1f}% → {pa['pct_arm']:.1f}% ({pa['dpts']:+.1f} points; {pa['better']} trials improved; {pv(pa['p_pct'])}) | "
          f"{pb['pct_ref']:.1f}% → {pb['pct_arm']:.1f}% ({pb['dpts']:+.1f} points; {pb['better']}; {pv(pb['p_pct'])}) |",
          f"| BH-FDR q (within-set balance family) | {fp(pa['q_fam'])} | {fp(pb['q_fam'])} |",
          f"| Permuted ECG vs PS-CVD5 (two-sided P) | {ci(a['placebo']['shuf_vs_base'])}, {pv(a['placebo']['shuf_vs_base']['p'])} | "
          f"{ci(b['placebo']['shuf_vs_base'])}, {pv(b['placebo']['shuf_vs_base']['p'])} |",
          f"| ECG vs permuted ECG | {ci(a['placebo']['ecg_vs_shuf'])}, {pv(a['placebo']['ecg_vs_shuf']['p'])} | "
          f"{ci(b['placebo']['ecg_vs_shuf'])}, {pv(b['placebo']['ecg_vs_shuf']['p'])} |",
          f"| \\|Δ log HR\\| vs RCT, PS-CVD5 → + ECG | {pa['absd_ref']:.3f} → {pa['absd_arm']:.3f} ({pa['absd_closer']} closer; sign-flip {pv(pa['absd_p'])}) | "
          f"{pb['absd_ref']:.3f} → {pb['absd_arm']:.3f} ({pb['absd_closer']}; {pv(pb['absd_p'])}) |",
          f"| Benchmark-permutation P (trial-specificity) | {pa['bshuf_p']:.2f} | {pb['bshuf_p']:.2f} |", ""]
    L += ["### Domains (PS-CVD5 + ECG vs PS-CVD5)", "", "| Domain (items) | s31 | 32 trials |", "|---|---|---|"]
    for d in a["domains"]:
        x, y = a["domains"][d], b["domains"][d]
        L.append(f"| {d} ({x['n_items']}) | {ci(x)} | {ci(y)} |")
    L += ["", "## 2. PS ladder (main configuration)", "",
          "Mean \\|SMD\\| over the 54 items (mean across trials of each trial's mean); relative reduction vs PS alone (paired by trial).", "",
          "| Level | Unmatched | PS alone | + ECG | + CLMBR-T | + CLMBR-T + ECG | + ECG (s31) | + ECG (32) | + CLMBR-T (s31 / 32) | + CLMBR-T + ECG (s31 / 32) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for rg, lab in RUNGS:
        x, y = a["ladder"][rg], b["ladder"][rg]
        lv = " | ".join(f"{x['level_' + k]:.3f} ({y['level_' + k]:.3f})" for k in ("unmatched", "base", "ECG", "CLMBR", "ECG+CLMBR"))
        L.append(f"| {lab} | {lv} | {ci(x['ECG'])}, {pv(x['ECG']['p'])} | {ci(y['ECG'])}, {pv(y['ECG']['p'])} | "
                 f"{fx(x['CLMBR']['rr'])}% / {fx(y['CLMBR']['rr'])}% | {fx(x['ECG+CLMBR']['rr'])}% / {fx(y['ECG+CLMBR']['rr'])}% |")
    L += ["", "Levels: s31 value, with the 32-trial value in brackets. Trials behind each s31 point: "
          + "; ".join(f"{lab} " + "/".join(str(a['ladder'][rg]['k_' + k]) for k in ("base", "ECG", "CLMBR", "ECG+CLMBR")) for rg, lab in RUNGS)
          + " (PS alone / + ECG / + CLMBR-T / + both). " + ("Every arm has all 31 trials." if all(a["ladder"][rg]["k_" + k] == 31 for rg, _ in RUNGS for k in ("base", "ECG", "CLMBR", "ECG+CLMBR")) else
                                                       "Some arms have fewer than 31 trials (failed cells)."),
          "", "|Δ log HR| and benchmark-permutation P for + ECG at each level:", "", "| Level | s31 | 32 trials |", "|---|---|---|"]
    for rg, lab in RUNGS:
        x, y = a["ladder"][rg]["ECG"], b["ladder"][rg]["ECG"]
        L.append(f"| {lab} | {x['absd_ref']:.3f} → {x['absd_arm']:.3f}; permutation {pv(x['bshuf_p'])} | {y['absd_ref']:.3f} → {y['absd_arm']:.3f}; {pv(y['bshuf_p'])} |")
    L += ["", "## 3. Six PS methods (PS-CVD5 + ECG vs PS-CVD5)", "", "| Method | s31 | 32 trials |", "|---|---|---|"]
    for c, lab in CFGL.items():
        x, y = a["methods"][c], b["methods"][c]
        L.append(f"| {lab} | {ci(x)}, {pv(x['p'])}, {x['lower']} | {ci(y)}, {pv(y['p'])}, {y['lower']} |")
    L += ["", f"CIs excluding 0: s31 {sum(a['methods'][c]['lo'] > 0 for c in CFGL)} of 6; 32 trials {sum(b['methods'][c]['lo'] > 0 for c in CFGL)} of 6.",
          "", "## 4. Agreement with the RCTs by emulation quality (PS-CVD5, main configuration)", "",
          "Tiers are the v19 tiers of the 37 feasible trials (s31 column) or of the 38 (32-trial column). Agreement metrics: r = Pearson r "
          "with the RCT log HRs; estimate agreement = emulated HR inside the RCT 95% CI; standardized-difference agreement = |z| < 1.96. "
          "Benchmark-permutation P: one-sided for + ECG.", "",
          "| Group (trials, s31 / 32) | Arm | r | Estimate agr. | Std-diff agr. | Mean \\|Δ log HR\\| | Closer vs PS alone | Benchmark-perm. P |",
          "|---|---|---|---|---|---|---|---|"]
    for g_ in a["agreement_by_tier"]:
        x, y = a["agreement_by_tier"][g_], b["agreement_by_tier"][g_]
        for arm, lab in (("base", "PS-CVD5"), ("ECG", "+ ECG")):
            u, v = x[arm], y[arm]
            grp = f"{g_} ({x['trials']} / {y['trials']})" if arm == "base" else ""
            closer = "" if arm == "base" else f"{u['closer']} ({v['closer']})"
            perm = "" if arm == "base" else f"{u['bshuf_p']:.2f} ({v['bshuf_p']:.2f})"
            L.append(f"| {grp} | {lab} | {u['r']:.2f} ({v['r']:.2f}) | {u['est_agree']:.0f}% ({v['est_agree']:.0f}%) | "
                     f"{u['std_agree']:.0f}% ({v['std_agree']:.0f}%) | {u['absd']:.3f} ({v['absd']:.3f}) | {closer} | {perm} |")
    L += ["", "s31 value first, the 32-trial (38-trial tier) value in brackets.", "",
          f"Benchmark-permutation P for PS-CVD5 + ECG: s31 {a['agreement_set']['ECG']['bshuf_p']:.2f}, all 37 feasible {a['agreement_all']['ECG']['bshuf_p']:.2f}, "
          f"framework v2.0 provisional 29 {a['agreement_v2']['ECG']['bshuf_p']:.2f} (32-trial: {b['agreement_set']['ECG']['bshuf_p']:.2f}; all 38 "
          f"{b['agreement_all']['ECG']['bshuf_p']:.2f}). PS-CVD10 + ECG: s31 {pv(a['cvd10_agreement']['ECG']['bshuf_p'])} (32-trial "
          f"{pv(b['cvd10_agreement']['ECG']['bshuf_p'])}; post hoc, exploratory).",
          "", "## 5. Robustness rows of the lab deck (PS-CVD5 + ECG vs PS-CVD5, 54 items)", "", "| Check | s31 | 32 trials |", "|---|---|---|"]
    rng = lambda x: (min(v["rr"] for v in x["placebo"]["ecg_vs_shuf_sets"].values()), max(v["rr"] for v in x["placebo"]["ecg_vs_shuf_sets"].values()))
    ra, rb_ = rng(a), rng(b)
    L += [f"| ECG vs permuted, range over five trial sets | {fx(ra[0])} to {fx(ra[1])}% (s31; Excellent + Good of the 37; all 37; v2.0 29; v2.0 30) | "
          f"{fx(rb_[0])} to {fx(rb_[1])}% (32; Excellent + Good; all 38; 29; 30) |",
          f"| Comparator-cluster sign-flip P; largest leave-one-trial-out P | {fp(pa['cluster_p'])} ({pa['n_clusters']} clusters); {fp(pa['loo_max_p'])} | "
          f"{fp(pb['cluster_p'])} ({pb['n_clusters']} clusters); {fp(pb['loo_max_p'])} |",
          f"| PS-Clinical (no LVEF), 5-draw MI, + ECG | {ci(a['ladder']['clinical_nolvef']['ECG'])}, {pv(a['ladder']['clinical_nolvef']['ECG']['p'])}; "
          f"single draws {fx(min(a['mi_draws']))} to {fx(max(a['mi_draws']))}% | {ci(b['ladder']['clinical_nolvef']['ECG'])}, {pv(b['ladder']['clinical_nolvef']['ECG']['p'])}; "
          f"draws {fx(min(b['mi_draws']))} to {fx(max(b['mi_draws']))}% |",
          f"| Spec-v2 cohort fixes (point estimate; version 1 → fixed cohorts) | {fx(a['spec_v2_fixes']['v1'])}% → {fx(a['spec_v2_fixes']['v2'])}%; random removal median "
          f"{fx(a['spec_v2_fixes']['random_median'])} ({fx(a['spec_v2_fixes']['random_p5'])} to {fx(a['spec_v2_fixes']['random_p95'])}) | "
          f"{fx(b['spec_v2_fixes']['v1'])}% → {fx(b['spec_v2_fixes']['v2'])}%; {fx(b['spec_v2_fixes']['random_median'])} "
          f"({fx(b['spec_v2_fixes']['random_p5'])} to {fx(b['spec_v2_fixes']['random_p95'])}) |",
          f"| Framework v2.0 sets (version 1 cohorts; unchanged, both include PROTECT AF) | provisional 29: {ci(a['framework_v2']['v2'])}; rescored 30: {ci(a['framework_v2']['v2c'])} | same |",
          f"| CV log-loss penalty (R2 cells, scenario S1) | {ci(a['cv_penalty_r2'])}, {a['cv_penalty_r2']['lower']} | {ci(b['cv_penalty_r2'])}, {b['cv_penalty_r2']['lower']} |",
          f"| Index-day ECGs excluded (ECG ≥ 1 day before index) | {ci(a['no_index_day_ecg'])}, {pv(a['no_index_day_ecg']['p'])}, {a['no_index_day_ecg']['lower']} | "
          f"{ci(b['no_index_day_ecg'])}, {pv(b['no_index_day_ecg']['p'])}, {b['no_index_day_ecg']['lower']} |",
          "", "R2's own CV-tuned primary (35-trial R2 set, 56 R2 leakage-clean items: 4.7%) is a different design and is not re-derived here.",
          ""]
    DOC.parent.mkdir(parents=True, exist_ok=True)
    old = os.umask(0o022)
    DOC.write_text("\n".join(L))
    os.umask(old)
    print("wrote", DOC.relative_to(ROOT))


if __name__ == "__main__":
    main()
