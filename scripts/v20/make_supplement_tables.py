#!/usr/bin/env python
"""Build the eTables of docs/paper/supplement.md from aggregate outputs (no patient-level data).

Writes each eTable between <!-- ETABLE:n:BEGIN --> and <!-- ETABLE:n:END --> markers in supplement.md, so the
tables can be regenerated after any rerun. Sources (aggregates only):
  docs/paper/table1_picot.md, docs/v19/quality_tiers.json          eTable 1
  build_lab_deck.build_data() (58-panel labels, expanded buckets)  eTable 2
  audits/claude-v20-sens-primary32/{sensitivity,ci,pcsweep,cells}.csv
  make_paper_figures helpers (estimates, agreement, bootstrap)     eTables 3-5, 8
  audits/claude-v20-mimic-replication/{results,summary}            eTable 6
  docs/v17/V17_CONFIRMATION_RESULTS.md, docs/v18/AF_CONFIRMATION_RESULTS.md (transcribed)  eTable 9
Counts of 1-10 are suppressed (none occur in these tables)."""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/v20"))
import make_paper_figures as F  # noqa: E402  (builds the deck data D; no figures are drawn on import)

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
SUP = ROOT / "docs/paper/supplement.md"
SP = A / "claude-v20-sens-primary32"
SENS = pd.read_csv(SP / "sensitivity.csv")
CI = pd.read_csv(SP / "ci.csv")
PCS = pd.read_csv(SP / "pcsweep.csv")
CELLS = pd.read_csv(SP / "cells.csv", usecols=["key", "rung", "config", "arm", "n", "n_pairs"])
TIERS = json.load(open(ROOT / "docs/v19/quality_tiers.json"))["trials"]
RUNG = {"P1": "PS-Demo", "P5": "PS-CVD5", "hdPS200": "hdPS", "clinical": "PS-Clinical"}
SET = {"S32": "32 primary trials", "S38": "38 emulated trials"}


def f1(x):
    return "—" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.1f}"


def f3(x):
    return "—" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.3f}"


def fp(p):
    if p is None or (isinstance(p, float) and not math.isfinite(p)):
        return "—"
    return "<.001" if p < 0.001 else (f"{p:.3f}".lstrip("0") if p < 0.1 else f"{p:.2f}".lstrip("0"))


def ci_s(e, lo, hi):
    return f"{e:.1f} ({lo:.1f} to {hi:.1f})"


MINUS = re.compile(r"(?<![A-Za-z0-9])-(?=\d)")


def md(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(MINUS.sub("\u2212", str(c)) for c in r) + " |" for r in rows]
    return "\n".join(out)


def table1_rows():
    """Parse Table 1 (PICOT) rows by trial name."""
    rows = {}
    for line in open(ROOT / "docs/paper/table1_picot.md"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 9 and cells[1] and not set(cells[1]) <= set("-") and cells[1] != "Trial":
            rows[cells[1]] = cells
    return rows


# ------------------------------------------------------------------ eTable 1
def etable1():
    T1 = table1_rows()
    base = CELLS[(CELLS.rung == "P1") & (CELLS.config == "main") & (CELLS.arm == "base")].set_index("key")
    order = {"Excellent": 0, "Good": 1, "Moderate": 2, "Limited": 3}
    rows = []
    for t in sorted(TIERS, key=lambda x: (x["area"], order[x["tier"].split()[0]], x["trial"])):
        name = t["trial"]
        p = T1.get(name)
        if p is None:  # name variants between Table 1 and the tier file
            p = next((v for k, v in T1.items() if k.replace(" ", "").replace("-", "").lower()[:6] == name.replace(" ", "").replace("-", "").lower()[:6]), None)
        assert p is not None, name
        fl = ", ".join(k for k, v in t["flags"].items() if v) or "none"
        tier = t["tier"].split()[0]
        b = base.loc[t["key"]]
        rows.append([t["area"], name + (" †" if tier == "Limited" else ""), p[2], f"{p[3]} vs {p[4]}", p[5], t["horizon_months"],
                     fl, f"{t['comparator']} / {t['outcome']}", f"{tier} ({t['points']})", f"{int(b.n):,}", f"{int(b.n_pairs):,}", t["rationale"]])
    head = ["Area", "Trial", "Eligibility (population)", "Treatment strategies (intervention vs comparator)", "Outcome", "Horizon, mo",
            "Design flags", "Comparator / outcome fidelity", "Quality (points)", "Patients with ECG", "Matched pairs (PS-Demo)", "Design notes and adaptations"]
    b32 = base[~base.index.isin([x["key"] for x in TIERS if x["tier"].startswith("Limited")])]
    foot = (f"† Limited-quality emulation, excluded from the primary analysis set. Primary set totals: {int(b32.n.sum()):,} patients with an ECG "
            f"(median {int(b32.n.median()):,} per trial) and {int(b32.n_pairs.sum()):,} matched pairs with PS-Demo. "
            "Design flags: F1, in-hospital initiation not mirrored; F2, selective run-in; F3, discontinuation or replacement of baseline therapy at "
            "randomization not reproduced; F4, horizon ≥48 months with a delayed treatment effect; F5, other time-zero misalignment (eMethods 3). "
            "Time zero was the first order of the intervention or comparator in new users, or the first add-on or switch order in sequential designs "
            "(eMethods 2). Sources: Table 1; docs/v19/quality_tiers.json; cohort counts from the primary analysis outputs.")
    return md(head, rows) + "\n\n" + foot


# ------------------------------------------------------------------ eTable 2
def etable2():
    defs = {"Coded record": "Mean |SMD| over medication-order classes (90 d), utilization counts (365 d) and held-out code features (365 d); prognostic risk score for the trial's primary outcome",
            "Vitals & core labs": "Latest value before index (90 d; 365 d for BMI and LVEF), compared among patients with an observed value",
            "Other labs": "Latest value in the 365 days before index, compared among patients with an observed value",
            "Echo: LV structure": "Latest structured echocardiogram in the 365 days before index (index dates from July 31, 2016)",
            "Echo: LV function": "As above", "Echo: diastolic / LA": "As above", "Echo: RV / pulmonary": "As above", "Echo: valves / aorta": "As above"}
    rows = []
    for g in F.GROUPS:
        labs = [v["lab"] for v in F.D["vars"] if v["g"] == g]
        rows.append([g, len(labs), ", ".join(labs), defs.get(g, "")])
    part_a = md(["Domain", "n", "Characteristics", "Definition and window"], rows)
    bc = {}
    for v in F.D["exp"]["vars"]:
        bc[v["b"]] = bc.get(v["b"], 0) + 1
    part_b = md(["Expanded-panel domain", "Variables (union across trials)"], [[b, bc[b]] for b in F.D["exp"]["buckets"] if b in bc] + [["Total", sum(bc.values())]])
    src = [["Khera et al., ACEi/ARB and COVID-19 (claims PS)", "JAHA 2021; PMID 33624516"],
           ["LEGEND-T2DM and LEGEND-HTN (large-scale PS; OHDSI)", "BMJ Open 2022, PMID 35680274; JACC 2024, PMID 39197980; Nat Commun 2026, PMID 41935054; Lancet 2019, PMID 31668726"],
           ["Thangaraj et al., TOPCAT phenomapping in YNHHS", "Circ Cardiovasc Qual Outcomes 2025; PMID 40261065"],
           ["Biswas et al., DISCO (AI-ECG phenotypic matching)", "Eur Heart J 2025 (Suppl)"],
           ["Dhingra, Croon et al., AI-ECG prognostic adjustment", "Eur Heart J 2025, PMID 39804243; JACC 2025, PMID 40139886; Circulation 2025, PMID 40888124"],
           ["RCT-DUPLICATE registered protocols (PARADIGM-HF and others)", "NCT04736433 and related registrations"],
           ["EMPRISE (Patorno, Htoo et al.)", "Circulation 2019, PMID 30955357; Cardiovasc Diabetol 2024, PMID 38331813"],
           ["ARISTOPHANES (Lip et al.)", "Stroke 2018; PMID 30571400"],
           ["Sentinel propensity score tools", "Sentinel Initiative methods reports"],
           ["High-dimensional PS (Schneeweiss; Rassen)", "Epidemiology 2009, PMID 19487948; Pharmacoepidemiol Drug Saf 2023"],
           ["Fan et al., HF target trial emulation in CPRD", "Nat Commun 2026"],
           ["OHDSI FeatureExtraction default covariates", "OHDSI software documentation"]]
    part_c = md(["Source used to derive the expanded panel", "Citation"], src)
    foot = ("Part A lists the 58 primary held-out characteristics; at PS-Clinical, the 11 characteristics included in that PS are excluded (47 remain). "
            "Part B lists expanded-panel domains; per trial, about 245 to 336 characteristics remain after exclusions (eMethods 6). Part C lists the 12 "
            "sources of the literature review. Abbreviations: BMI, body mass index; LA, left atrium; LV, left ventricle; LVEF, LV ejection fraction; "
            "RV, right ventricle. Sources: docs/v16/COVARIATES2.md, docs/v16/LIT_COVARIATES.md, scripts/build_physiology_panel_v2.py.")
    return "**A. Primary held-out panel (58 characteristics)**\n\n" + part_a + "\n\n**B. Expanded panel**\n\n" + part_b + "\n\n**C. Literature sources**\n\n" + part_c + "\n\n" + foot


# ------------------------------------------------------------------ eTable 3
def expanded_relred(I, seed):
    """Expanded panel, PS-Demo: relative reduction in mean |SMD| (paired variables), fixed-seed bootstrap."""
    B = F.arr(F.D["exp"]["smd"]["P1"]["base"])
    E = F.arr(F.D["exp"]["smd"]["P1"]["ECG"])
    bad = np.isnan(B) | np.isnan(E)
    B[bad] = np.nan
    E[bad] = np.nan
    with np.errstate(all="ignore"):
        mb, me = np.nanmean(B, 1), np.nanmean(E, 1)
    return F.relred(mb, me, I, np.random.default_rng(seed)), float(np.nanmean(mb[I])), float(np.nanmean(me[I]))


def etable3():
    rows = []
    for st in ("S32", "S38"):
        for rg in RUNG:
            m = SENS[(SENS.set == st) & (SENS.config == "main") & (SENS.rung == rg)]
            e = m[m.contrast == "ECG vs base"].iloc[0]
            s = m[m.contrast == "shufECG vs base"].iloc[0]
            rows.append([SET[st], RUNG[rg], f3(e.m58_b), f3(e.m58_a), ci_s(e.relred, e.relred_lo, e.relred_hi), f"{f1(e.lt01_b)} → {f1(e.lt01_a)}",
                         e.lt01_better, fp(e.lt01_p), fp(e.lt01_cluster_p), fp(e.lt01_loo_max_p), fp(e.q_lt01_p_main), ci_s(s.relred, s.relred_lo, s.relred_hi)])
    part_a = md(["Trial set", "PS", "Mean |SMD|, PS alone", "Mean |SMD|, PS + ECG", "Relative reduction, % (95% CI)", "% |SMD| <0.1, PS alone → + ECG",
                 "Trials improved", "P", "Cluster P", "Leave-one-out max P", "q", "Permuted ECG, relative reduction, % (95% CI)"], rows)
    drows = []
    for dom in ["All 58"] + list(F.GROUPS):
        r = []
        for st in ("S32", "S38"):
            for arm in ("ECG", "shufECG"):
                c = CI[(CI.source == "YNHHS") & (CI.set == st) & (CI.rung == "P1") & (CI.domain == dom) & (CI.arm == arm)]
                r.append(ci_s(*c.iloc[0][["est", "lo", "hi"]]) if len(c) else "—")
        drows.append([dom] + r)
    part_b = md(["Domain (PS-Demo)", "32 trials, + ECG", "32 trials, + permuted ECG", "38 trials, + ECG", "38 trials, + permuted ECG"], drows)
    erows = []
    for lab, I, seed in (("32 primary trials", F.I32, 20261006), ("38 emulated trials", F.I38, 20261007)):
        (e, lo, hi), mb, me = expanded_relred(I, seed)
        erows.append([lab, f3(mb), f3(me), ci_s(e, lo, hi)])
    part_c = md(["Expanded panel (PS-Demo)", "Mean |SMD|, PS alone", "Mean |SMD|, PS + ECG", "Relative reduction, % (95% CI)"], erows)
    foot = ("Relative reduction is 1 minus the ratio of the across-trial mean of the per-trial mean |SMD| with and without the added components; 95% CIs "
            "from 4,000 bootstrap resamples of trials with a fixed seed, using the characteristics observed in both compared arms. P values are exact "
            "one-sided sign-flip tests across trials for the proportion of characteristics with |SMD| <0.1; cluster P groups trials that share a "
            "comparator; q is the false discovery rate–adjusted P within the analysis family. Sources: docs/v20/SENS_PRIMARY32.md; expanded panel "
            "recomputed from the aggregate balance outputs.")
    return "**A. Primary panel by PS specification**\n\n" + part_a + "\n\n**B. Relative reduction by domain**\n\n" + part_b + "\n\n**C. Expanded panel**\n\n" + part_c + "\n\n" + foot


# ------------------------------------------------------------------ eTable 4
def etable4():
    rows = []
    for st in ("S32", "S38"):
        for rg in RUNG:
            e = SENS[(SENS.set == st) & (SENS.config == "main") & (SENS.rung == rg) & (SENS.contrast == "ECG vs base")].iloc[0]
            k = int(e.n_trials)
            rows.append([SET[st], RUNG[rg], f"{f3(e.absd_b)} → {f3(e.absd_a)}", e.absd_better, fp(e.absd_p), fp(e.absd_cluster_p), fp(e.absd_loo_max_p),
                         fp(e.q_absd_p_main), fp(e.bshuf_p), f"{e.base_r:.2f} → {e.arm_r:.2f}",
                         f"{round(e.base_ea * k / 100)} → {round(e.arm_ea * k / 100)}", f"{round(e.base_cons * k / 100)} → {round(e.arm_cons * k / 100)}"])
    foot = ("Values are PS alone → PS + ECG. Mean |Δ log HR|, mean absolute difference between emulated and RCT log HRs. Estimate agreement, emulated HR "
            "within the RCT 95% CI; standardized difference agreement, |z| <1.96 with both standard errors (trials, n). Benchmark-permutation P: RCT "
            "results reassigned across trials 20,000 times. Source: docs/v20/SENS_PRIMARY32.md.")
    return md(["Trial set", "PS", "Mean |Δ log HR|", "Trials closer", "P", "Cluster P", "Leave-one-out max P", "q", "Benchmark-permutation P",
               "Pearson r", "Estimate agreement, n", "Standardized difference agreement, n"], rows) + "\n\n" + foot


# ------------------------------------------------------------------ eTable 5
def etable5():
    grp = [("Excellent or good (n = 15)", np.array([i for i in F.I32 if F.TIER[i] in ("Excellent", "Good")])),
           ("Moderate (n = 17)", np.array([i for i in F.I32 if F.TIER[i] == "Moderate"]))]
    rows = []
    for glab, idx in grp:
        for rg, lab in F.RUNGS:
            Lb, Sb = F.est(rg, "base")
            Le, Se = F.est(rg, "ECG")
            ok = idx[np.isfinite(Lb[idx]) & np.isfinite(Le[idx])]
            b, e = F.agree(Lb[ok], Sb[ok], F.RB[ok], F.RS[ok]), F.agree(Le[ok], Se[ok], F.RB[ok], F.RS[ok])
            db, de = np.abs(Lb[ok] - F.RB[ok]), np.abs(Le[ok] - F.RB[ok])
            rows.append([glab, lab, f"{b['gap']:.3f} → {e['gap']:.3f}", f"{int((de < db).sum())}/{len(ok)}", fp(F.signflip_exact(db - de)),
                         f"{b['r']:.2f} → {e['r']:.2f}", f"{b['ea']:.0f} → {e['ea']:.0f}", f"{b['sd']:.0f} → {e['sd']:.0f}"])
    foot = ("Values are PS alone → PS + ECG; estimate and standardized difference agreement are percentages of trials. P, exact one-sided sign-flip "
            "test for the mean absolute difference. Comparisons by emulation quality are post hoc (eMethods 3).")
    return md(["Emulation quality", "PS", "Mean |Δ log HR|", "Trials closer", "P", "Pearson r", "Estimate agreement, %", "Standardized difference agreement, %"], rows) + "\n\n" + foot


# ------------------------------------------------------------------ eTable 6
MNAME = {"plato": "PLATO", "aristotle": "ARISTOTLE", "rocket_af": "ROCKET AF", "transform_hf": "TRANSFORM-HF", "comet": "COMET",
         "soap2": "SOAP II", "elite2": "ELITE II", "peptic": "PEPTIC (negative control)"}
MRUNG = {"demo": "PS-Demo", "sparse": "PS-Sparse", "hdPS200": "hdPS", "clinical": "PS-Clinical-lite"}


def etable6():
    M = A / "claude-v20-mimic-replication"
    rows = []
    for t, lab in MNAME.items():
        d = pd.read_csv(M / f"results/{t}_arms.csv")
        d = d[(d.base == "demo") & (d["pop"] == "all")].set_index("arm")
        r0 = d.iloc[0]
        ev = int(d.loc["base", "events"])
        rct = f"{math.exp(r0.rct_loghr):.2f} ({math.exp(r0.rct_loghr - 1.96 * r0.rct_se):.2f}–{math.exp(r0.rct_loghr + 1.96 * r0.rct_se):.2f})"
        meas = str(r0.rct_measure).split(" ")[0]
        hr = lambda a: f"{math.exp(d.loc[a, 'loghr']):.2f} ({math.exp(d.loc[a, 'loghr'] - 1.96 * d.loc[a, 'se']):.2f}–{math.exp(d.loc[a, 'loghr'] + 1.96 * d.loc[a, 'se']):.2f})"
        rows.append([lab, f"{int(d.loc['base', 'n_pairs']):,}", f"{ev:,}" if ev > 10 else "<11", f"{f1(d.loc['base', 'pct_bal'])} / {f1(d.loc['ECG', 'pct_bal'])} / {f1(d.loc['permECG', 'pct_bal'])}",
                     hr("base"), hr("ECG"), hr("permECG"), rct + ("" if meas == "HR" else f" [{meas}]")])
    part_a = md(["Trial", "Matched pairs (PS-Demo)", "Events", "% |SMD| <0.1: PS alone / + ECG / + permuted ECG", "HR, PS alone", "HR, + ECG", "HR, + permuted ECG", "RCT estimate (95% CI)"], rows)
    S = json.load(open(M / "summary/summary.json"))
    brow = []
    for rg, lab in MRUNG.items():
        for pop, plab in (("all", "All patients"), ("no_index_day_ecg", "Excluding index-day ECGs")):
            b = S["balance"][f"primary7|{rg}|{pop}"]
            g = S["agreement"][f"primary7|{rg}|{pop}"]
            brow.append([lab, plab, ci_s(b["relred_ECG"], *b["relred_ECG_ci"]), b["lower_smd_ECG"], f1(b["relred_permECG"]),
                         f"{g['base']['mean_abs_diff']:.3f} → {g['ECG']['mean_abs_diff']:.3f}", g["ECG_vs_base"]["closer"], fp(g["ECG_vs_base"]["p"]),
                         f"{g['permECG']['mean_abs_diff']:.3f}", f"{g['base']['r']:.2f} → {g['ECG']['r']:.2f}", f"{g['base']['std_agree']} → {g['ECG']['std_agree']}"])
    part_b = md(["PS", "Population", "Relative reduction in mean |SMD|, % (95% CI)", "Trials with lower mean |SMD|", "Permuted ECG, %", "Mean |Δ log HR|, PS alone → + ECG",
                 "Trials closer", "P", "Mean |Δ log HR|, + permuted ECG", "Pearson r", "Standardized difference agreement"], brow)
    foot = ("Part A: PEPTIC is a negative-control trial with no expected effect. [OR] and [RR] mark RCT benchmarks reported as odds ratio (SOAP II) or "
            "relative risk (PEPTIC). Part B: summaries across the 7 cardiovascular trials. Source: docs/v20/MIMIC_REPLICATION.md.")
    return "**A. Per-trial cohorts, balance and HRs (PS-Demo)**\n\n" + part_a + "\n\n**B. Summary by PS specification**\n\n" + part_b + "\n\n" + foot


# ------------------------------------------------------------------ eTable 7
CONF = {"main": "1:1 matching, caliper 0.2 (primary)", "cal01": "1:1 matching, caliper 0.1", "m13": "1:3 matching", "iptw": "Inverse probability weighting",
        "overlap": "Overlap weighting", "gbm": "Gradient-boosted PS (5-fold cross-fitted)"}


def etable7():
    rows = []
    for st in ("S32", "S38"):
        for cf, lab in CONF.items():
            m = SENS[(SENS.set == st) & (SENS.config == cf) & (SENS.rung == "P1")]
            e = m[m.contrast == "ECG vs base"].iloc[0]
            s = m[m.contrast == "shufECG vs base"].iloc[0]
            rows.append([SET[st], lab, ci_s(e.relred, e.relred_lo, e.relred_hi), f"{f1(e.lt01_b)} → {f1(e.lt01_a)}", fp(e.lt01_p), f1(s.relred),
                         f"{f3(e.absd_b)} → {f3(e.absd_a)}", fp(e.absd_p), fp(e.bshuf_p)])
    part_a = md(["Trial set", "Approach (PS-Demo)", "Relative reduction, % (95% CI)", "% |SMD| <0.1", "P", "Permuted ECG, %", "Mean |Δ log HR|", "P", "Benchmark-permutation P"], rows)
    prow = []
    for st in ("S32", "S38"):
        for k in sorted(PCS.k_pcs.unique()):
            e = PCS[(PCS.set == st) & (PCS.k_pcs == k) & (PCS.contrast == "ECG vs base")].iloc[0]
            prow.append([SET[st], int(k), ci_s(e.relred, e.relred_lo, e.relred_hi), f"{f1(e.lt01_b)} → {f1(e.lt01_a)}", fp(e.lt01_p),
                         f"{f3(e.absd_b)} → {f3(e.absd_a)}", fp(e.absd_p), fp(e.bshuf_p)])
    part_b = md(["Trial set", "ECG principal components", "Relative reduction, % (95% CI)", "% |SMD| <0.1", "P", "Mean |Δ log HR|", "P", "Benchmark-permutation P"], prow)
    foot = ("Values are PS-Demo → PS-Demo + ECG. The primary analysis uses 32 principal components. Source: docs/v20/SENS_PRIMARY32.md.")
    return "**A. Matching, weighting and PS model**\n\n" + part_a + "\n\n**B. Number of ECG principal components**\n\n" + part_b + "\n\n" + foot


# ------------------------------------------------------------------ eTable 8
EST = [("itt", "Initiation (primary)"), ("pp_ipcw_365", "Per-protocol, 365-day grace (IPCW)"), ("pp_ipcw_switch", "Switch-only (IPCW)"),
       ("landmark90", "90-day landmark"), ("runin90", "90-day run-in")]


def etable8():
    def getE(e, a):
        if e == "itt":
            return F.est("P1", a)
        L = F.D["sens"][e]["P1"][a]
        return (np.array([np.nan if x is None else x[0] for x in L]), np.array([np.nan if x is None else x[1] for x in L]))
    rows = []
    for lab_set, I in (("32 primary trials", F.I32), ("38 emulated trials", F.I38)):
        for e, lab in EST:
            Lb, _ = getE(e, "base")
            Le, _ = getE(e, "ECG")
            ok = I[np.isfinite(Lb[I]) & np.isfinite(Le[I])]
            db, de = np.abs(Lb[ok] - F.RB[ok]), np.abs(Le[ok] - F.RB[ok])
            rows.append([lab_set, lab, len(ok), f"{db.mean():.3f} → {de.mean():.3f}", f"{int((de < db).sum())}/{len(ok)}", fp(F.signflip_exact(db - de))])
    foot = ("Values are PS-Demo → PS-Demo + ECG. Trials with a one-time procedure arm are not applicable to on-treatment estimands, and the run-in analysis "
            "was not estimable in trials with 50 or fewer patients retained (eMethods 9). IPCW, inverse-probability-of-censoring weights. P, exact "
            "one-sided sign-flip test. Source: docs/v19/SENS_ADHERENCE.md (recomputed for each trial set).")
    return md(["Trial set", "Estimand", "Trials, n", "Mean |Δ log HR|", "Trials closer", "P"], rows) + "\n\n" + foot


# ------------------------------------------------------------------ eTable 9
def etable9():
    rows = [["15 trials (second stage)", "PS-Demo", "% |SMD| <0.1", "52.4 → 58.3", "11/15", ".033", "—"],
            ["15 trials (second stage)", "PS-Demo", "Mean |Δ log HR|", "0.250 → 0.208", "8/15", ".074", ".97"],
            ["15 trials (second stage)", "Demographics + 6 diagnoses*", "% |SMD| <0.1", "57.2 → 59.0", "9/15", ".17", "—"],
            ["15 trials (second stage)", "Demographics + 6 diagnoses*", "Mean |Δ log HR|", "0.192 → 0.193", "7/15", ".52", ".36"],
            ["5 AF trials (third stage)", "PS-Demo", "% |SMD| <0.1", "39.7 → 43.1", "3/5", ".34", "—"],
            ["5 AF trials (third stage)", "PS-Demo", "Mean |Δ log HR|", "0.254 → 0.199", "3/5", ".19", ".28"],
            ["5 AF trials (third stage)", "PS-CVD5", "% |SMD| <0.1", "43.4 → 46.9", "4/5", ".19", "—"],
            ["5 AF trials (third stage)", "PS-CVD5", "Mean |Δ log HR|", "0.135 → 0.212", "1/5", ".97", "1.00"]]
    foot = ("Analyses specified and committed before results were computed (eMethods 3). Values are PS alone → PS + ECG; P, exact one-sided sign-flip "
            "test across trials; benchmark-permutation P as in eTable 4. *The second-stage plan specified a PS of demographics, the five diagnoses of "
            "PS-CVD5 and obesity. The ECG did not reproduce the agreement finding in the 5 AF trials. Sources: docs/v17/V17_CONFIRMATION_RESULTS.md; "
            "docs/v18/AF_CONFIRMATION_RESULTS.md.")
    return md(["Prespecified set", "PS", "Outcome", "PS alone → + ECG", "Trials improved", "P", "Benchmark-permutation P"], rows) + "\n\n" + foot


TABLES = {1: etable1, 2: etable2, 3: etable3, 4: etable4, 5: etable5, 6: etable6, 7: etable7, 8: etable8, 9: etable9}

if __name__ == "__main__":
    s = SUP.read_text()
    for n, fn in TABLES.items():
        b, e = f"<!-- ETABLE:{n}:BEGIN -->", f"<!-- ETABLE:{n}:END -->"
        assert s.count(b) == 1 and s.count(e) == 1, n
        s = s[:s.index(b) + len(b)] + "\n" + fn() + "\n" + s[s.index(e):]
        print("eTable", n, "ok")
    SUP.write_text(s)
