#!/usr/bin/env python
"""Build the CarDS Lab slide deck (2026-10-01): docs/presentation/ecg_tte_lab_2026_10_01.html.

Self-contained HTML (inline CSS/JS/SVG, logo as base64, no network resources). Embeds AGGREGATE data only:
per-trial summary statistics (|SMD| per held-out variable, log HR, SE, RCT log HR / SE) and per trial x confounder
simulation summaries (bias, coverage, partial R^2). No patient-level data, no identifiers, no patient counts.

Sources (read-only):
  audits/claude-v18-embed-compare/results.csv          (half == 'full'; rungs x arms; smd:<var>, loghr, se, rb, rs)
  audits/claude-v19-expanded-buckets/per_var.csv       (P1 expanded panel; unmatched/base/ECG/shufECG)
  audits/claude-v16-covars2b/dictionary.csv            (variable definitions only)
  audits/claude-v19-g2-simulation/summary_by_trial{,_adverse,_conly}.csv, relationship.csv, excluded_cells.csv
  docs/v17/trial_selection.json (fidelity, ECG relevance), docs/paper/table1_picot.md (names, PICOT, published HR)
  PowerPoint logo: trialemulate.pptx ppt/media/image1.png

Usage (tte-analysis env; make_acc_figure imports lifelines):
  python scripts/build_lab_deck.py [--pptx-media DIR] [--copy-to DIR]
"""
import argparse
import base64
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from make_acc_figure import VARS  # noqa: E402

A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
PPTX = Path("/mnt/raid0/rbc58/ecg-tte/trialemulate.pptx")
OUT = ROOT / "docs" / "presentation" / "ecg_tte_lab_2026_10_01.html"
RUNGS = ["P1", "P5", "P2", "sparse", "hdPS200", "clinical"]
ARMS = ["base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG", "noise96"]
AREA = {"AF": "AF", "HF": "HF", "DM": "Diabetes", "HTN": "Hypertension", "ACS/post-MI": "ACS / MI", "Other": "Other"}
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
SIM_VARIANTS = [("asd", "", "As designed"), ("adv", "_adverse", "Adverse orientation (post hoc)"),
                ("con", "_conly", "Outcome depends on C only (post hoc)")]
SIM_ARMS = ["base", "ECG", "shufECG", "noise32", "oracle"]
CONF = ["lvef", "ntprobnp", "bmi", "egfr"]


def r4(x):
    return None if x is None or not np.isfinite(x) else round(float(x), 4)


def r4s(x):
    """|SMD| rounded to 4 d.p. without crossing the 0.1 threshold (keeps % |SMD| < 0.1 exact)."""
    y = r4(x)
    if y is not None and (x < 0.1) != (y < 0.1):
        y = 0.09999 if x < 0.1 else 0.1
    return y


def table1():
    rows = {}
    for line in open(ROOT / "docs/paper/table1_picot.md"):
        if not line.startswith("| ") or line.startswith("| Area") or line.startswith("|---"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 9:
            rows[c[1]] = dict(pop=c[2], i=c[3], c=c[4], outcome=c[5], months=c[6], hr=c[7], qual=c[8])
    return rows


def logo_b64(media_dir):
    if media_dir and (Path(media_dir) / "image1.png").exists():
        raw = (Path(media_dir) / "image1.png").read_bytes()
    else:
        with zipfile.ZipFile(PPTX) as z:
            raw = z.read("ppt/media/image1.png")
    return base64.b64encode(raw).decode()


FLAGLAB = [("F1_in_hospital_start_not_mirrored", "in-hospital start"), ("F2_responder_runin", "run-in"),
           ("F3_discontinuation_switch_not_mirrored", "therapy switch"), ("F4_delayed_effect_long_followup", "long follow-up"),
           ("F5_other_time_zero_misalignment", "time zero")]


SENS_KEYS = ["pp_ipcw_365", "pp_ipcw_switch", "landmark90", "runin90"]


def build_data():
    R = pd.read_csv(A / "claude-v18-embed-compare/results.csv")
    R = R[R.half == "full"].copy()
    assert R.trial.nunique() == 38
    order = R[(R.rung == "P1") & (R.arm_role == "base")].sort_values("idx")
    sel = json.load(open(ROOT / "docs/v17/trial_selection.json"))["trials"]
    T1 = table1()
    # v1.9 adjudicated design-only quality items, points and tiers (docs/v19/QUALITY_REAUDIT.md)
    QT = {t["key"]: t for t in json.load(open(ROOT / "docs/v19/quality_tiers.json"))["trials"]}
    trials = []
    for _, r in order.iterrows():
        k = r.key
        s = sel.get(k) or sel[k.replace("_seq", "")]
        qual = "strict" if s["fidelity_include_strict"] else ("high" if s["fidelity_include"] else "lower")
        nm = T1NAME[k]
        t1 = T1[nm]
        assert {"strict": "High (strict)", "high": "High", "lower": "Lower"}[qual] == t1["qual"], (k, qual, t1["qual"])
        trials.append(dict(id=r.trial, name=SHORT.get(nm, nm), full=nm, area=AREA[r.category], qual=qual,
                           ecg=s["ecg_relevance"], rb=r4(r.rb), rs=r4(r.rs), hr=t1["hr"], ic=f"{t1['i']} vs {t1['c']}",
                           outcome=t1["outcome"], set=r.set,
                           flags=[lab for f, lab in FLAGLAB if s["flags"].get(f)],
                           comp=s["flags"]["comparator_fidelity"], outc=s["flags"]["outcome_fidelity"],
                           proxy=bool(s["flags"].get("record_only_placebo_proxy")),
                           qt=dict(f=[QT[k]["flags"][f"F{i}"] for i in range(1, 6)], c=QT[k]["comparator"][0].upper(),
                                   o=QT[k]["outcome"][0].upper(), p=QT[k]["points"], tier=QT[k]["tier"].split(" - ")[0],
                                   cls=QT[k]["class_3_adjudicated"])))
    tid = [t["id"] for t in trials]
    vn = [c for c, _, _ in VARS]
    bal, est = {}, {}
    for rg in RUNGS + ["none"]:
        bal[rg], est[rg] = {}, {}
        arms = ["unmatched"] if rg == "none" else ARMS
        for a in arms:
            g = R[(R.rung == rg) & (R.arm_role == a)].set_index("trial").loc[tid]
            M = g[[f"smd:{c}" for c in vn]].abs().to_numpy(float)
            for j, ex in enumerate(g.ex58.fillna("").astype(str)):
                for c in filter(None, ex.split(";")):
                    M[j, vn.index(c)] = np.nan
            bal[rg][a] = [[r4s(x) for x in row] for row in M]
            est[rg][a] = [[r4(x), r4(y)] for x, y in zip(g.loghr, g.se)]
    # sensitivity estimands (P1/P5; base, ECG, shufECG, unmatched): docs/v19/SENS_ADHERENCE.md, SENS_OUTPATIENT.md
    sens = {}
    C_ = pd.read_csv(A / "claude-v19-sens-adherence/cells.csv")
    O_ = pd.read_csv(A / "claude-v19-sens-outpatient/results_outpt.csv")
    ST = pd.read_csv(A / "claude-v19-sens-outpatient/setting.csv")
    out29 = set(ST[ST.rct_setting == "outpatient"].trial) - {"cabana-v2", "protect-af", "raft-af"}  # OUT-29 (a priori; SENS_OUTPATIENT_PLAN)
    O_ = O_[(O_.half == "full") & O_.trial.isin(out29)].assign(estimand="outpt")
    C_ = C_[C_.half == "full"]
    C_ = C_[~((C_.estimand == "runin90") & (C_.n_kept <= 50))]  # registered rule: run-in not estimable with <= 50 kept
    for e, G in pd.concat([C_[C_.estimand.isin(SENS_KEYS)], O_]).groupby("estimand"):
        sens[e] = {}
        for (ps, a), H in G.groupby(["ps", "arm_role"]):
            if a not in ("base", "ECG", "shufECG", "unmatched"):
                continue
            H = H.drop_duplicates("trial").set_index("trial").reindex(tid)
            sens[e].setdefault("none" if a == "unmatched" else ps, {})[a] = [[r4(x), r4(y)] if np.isfinite(x) and np.isfinite(y) else None
                                                                              for x, y in zip(H.loghr, H.se)]
    # expanded panel (all PS rungs x arms; scripts/v19/expanded_all_rungs.py)
    P = pd.read_csv(A / "claude-v19-expanded-buckets/per_var_all_rungs.csv")
    dic = pd.read_csv(A / "claude-v16-covars2b/dictionary.csv").set_index("variable")
    vb = P.drop_duplicates("var").set_index("var").bucket
    evars = sorted(vb.index, key=lambda v: (BUCKETS.index(vb[v]), v))
    exp_vars = []
    for v in evars:
        d = str(dic.definition.get(v, "")).split("; tokens")[0]
        lab = v.replace("_365", "").replace("_ever", " (ever)").replace("lab_", "").replace("rx_", "Rx ").replace("_", " ")
        exp_vars.append(dict(v=v, lab=lab[:34], b=vb[v], d=d[:140]))
    r3 = lambda x: None if not np.isfinite(x) else round(float(x), 3)
    exp = {}
    for (rg, a), G in P.groupby(["rung", "arm"]):
        W = G.pivot(index="trial", columns="var", values="smd").reindex(index=tid, columns=evars).abs()
        exp.setdefault(rg, {})[a] = [[r3(x) for x in row] for row in W.to_numpy(float)]
    # simulation
    G = A / "claude-v19-g2-simulation"
    exc = pd.read_csv(G / "excluded_cells.csv")
    rel = pd.read_csv(G / "relationship.csv").set_index(["trial", "conf"])
    scen = [[1.0, 1.0]] + [[o, h] for o in (1.25, 1.5, 2.0) for h in (1.25, 1.5, 2.0)]
    sim = dict(scen=scen, variants=[])
    cells = None
    for code, suf, lab in SIM_VARIANTS:
        S = pd.read_csv(G / f"summary_by_trial{suf}.csv")
        ex = pd.read_csv(G / f"excluded_cells{suf}.csv")
        for _, e in ex.iterrows():
            S = S[~((S.trial == e.trial) & (S.conf == e.conf))]
        if cells is None:
            cells = sorted({(t, c) for t, c in zip(S.trial, S.conf)}, key=lambda x: (CONF.index(x[1]), tid.index(x[0])))
        assert cells == sorted({(t, c) for t, c in zip(S.trial, S.conf)}, key=lambda x: (CONF.index(x[1]), tid.index(x[0])))
        S = S.set_index(["trial", "conf", "or_t", "hr_y", "arm"])
        B, C = {}, {}
        for a in SIM_ARMS:
            B[a] = [[r4(S.loc[(t, c, o, h, a), "bias"]) for (t, c) in cells] for o, h in scen]
            C[a] = [[r4(S.loc[(t, c, o, h, a), "coverage"]) for (t, c) in cells] for o, h in scen]
        sim["variants"].append(dict(code=code, lab=lab, bias=B, cov=C))
    assert len(cells) == 107 and not any((e.trial, e.conf) in cells for _, e in exc.iterrows())
    sim["cells"] = [dict(t=tid.index(t), c=c, r2=r4(rel.loc[(t, c), "r2_partial"])) for t, c in cells]
    return dict(trials=trials, vars=[dict(c=c, lab=lab, g=g) for c, lab, g in VARS], bal=bal, est=est,
                exp=dict(vars=exp_vars, buckets=BUCKETS, smd=exp), sim=sim, sens=sens)


def reference_values(D):
    """Values the default panel settings must reproduce (printed for the headless check)."""
    out = {}
    for a in ["base", "ECG", "shufECG"]:
        M = np.array([[np.nan if x is None else x for x in row] for row in D["bal"]["P1"][a]], float)
        out[f"P1 {a} %<0.1"] = float(np.mean(100 * (M < 0.1).sum(1) / (~np.isnan(M)).sum(1)))
    rb = np.array([t["rb"] for t in D["trials"]])
    for a in ["base", "ECG"]:
        L = np.array([x[0] for x in D["est"]["P1"][a]])
        out[f"P1 {a} |d|"] = float(np.mean(np.abs(L - rb)))
    L0 = np.array([x[0] for x in D["est"]["P1"]["base"]])
    L1 = np.array([x[0] for x in D["est"]["P1"]["ECG"]])
    out["P1 ECG closer"] = int((np.abs(L1 - rb) < np.abs(L0 - rb)).sum())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx-media", default=None)
    ap.add_argument("--copy-to", default=None)
    args = ap.parse_args()
    D = build_data()
    html = TEMPLATE.replace("__LOGO__", logo_b64(args.pptx_media)).replace("__DATA__", json.dumps(D, separators=(",", ":")))
    for bad in ("http://", "https://", "@import", "<link"):
        assert bad not in html.replace("http://www.w3.org/2000/svg", ""), bad
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(OUT, f"{len(html) / 1e6:.2f} MB")
    print(json.dumps(reference_values(D), indent=1))
    if args.copy_to:
        os.umask(0o077)
        Path(args.copy_to).mkdir(parents=True, exist_ok=True)
        shutil.copy(OUT, Path(args.copy_to) / OUT.name)
        os.chmod(Path(args.copy_to) / OUT.name, 0o600)

# ---- HTML template (inline CSS/JS/SVG; __DATA__ and __LOGO__ are filled by main) ----
TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ECG-TTE | CarDS Lab Presentation | October 1, 2026</title>
<style>
:root{--navy:#0E103C;--red:#DC5A55;--ink:#0E103C;--muted:#55576f;--faint:#8a8ca0;--line:#dcdde5;--band:#f3f3f7}
html,body{margin:0;height:100%;background:#15162a;overflow:hidden}
body{font-family:Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif;color:var(--ink)}
#stage{position:absolute;left:50%;top:50%;width:1280px;height:720px;transform-origin:center center;background:#fff}
.slide{position:absolute;inset:0;background:#fff;display:none;overflow:hidden}
.slide.active{display:block}
.ttl{position:absolute;left:19px;top:18px;min-width:298px;height:46px;background:var(--navy);color:#fff;font-weight:700;font-size:26px;
  display:flex;align-items:center;padding:0 18px;box-sizing:border-box;white-space:nowrap}
.num{position:absolute;right:23px;top:16px;width:54px;height:36px;background:var(--navy);color:#fff;font-size:18px;display:flex;align-items:center;justify-content:center}
.foot{position:absolute;left:0;bottom:13px;width:197px;height:35px;background:var(--navy);color:#fff;font-size:18px;display:flex;align-items:center;justify-content:center;letter-spacing:.6px}
.foot b{font-weight:700;margin-right:.45em}
.logo{position:absolute;right:22px;bottom:7px;width:54px;height:55px}
.body{position:absolute;left:48px;right:48px;top:92px;bottom:74px}
h2{font-size:30px;font-weight:700;margin:0 0 18px 0}
p,li{font-size:22px;line-height:1.38;margin:0 0 12px 0}
ul{margin:0;padding-left:26px}
.red{color:var(--red)}
.muted{color:var(--muted)}
.small{font-size:15px;line-height:1.35;color:var(--muted)}
.xs{font-size:12.5px;line-height:1.3;color:var(--muted)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:36px}
.card{border:2px solid var(--navy);padding:16px 18px;box-sizing:border-box}
.card h3{margin:0 0 8px 0;font-size:22px}
.card p{font-size:20px}
.tag{display:inline-block;background:var(--navy);color:#fff;font-weight:700;padding:2px 10px;margin-right:8px}
table.t{border-collapse:collapse;width:100%}
.qgrid{display:grid;grid-template-columns:0.8fr 1.05fr 1.35fr;gap:16px}
.qgrid h4{margin:0 0 6px;padding:6px 10px;background:var(--navy);color:#fff;font-size:17px;font-weight:600}
.qgrid table{border-collapse:collapse;width:100%}
.qgrid td{font-size:13px;padding:2px 6px;white-space:nowrap;border-bottom:1px solid var(--line);vertical-align:top;color:var(--navy)}
.qgrid td.n{font-weight:600;white-space:nowrap}
.qgrid td.r{color:#555}
.qgrid.q4{grid-template-columns:repeat(4,1fr)}
.qgrid td.p{text-align:right;color:#555}
.qgrid h4 .d{font-weight:400;font-size:13px;opacity:.85}
.qitems{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.qitems table{border-collapse:collapse;width:100%}
.qitems th{font-size:12.5px;font-weight:600;background:var(--navy);color:#fff;padding:4px 5px;text-align:center}
.qitems th.l,.qitems td.l{text-align:left}
.qitems td{font-size:12.5px;padding:2.5px 5px;border-bottom:1px solid var(--line);text-align:center;color:var(--navy);white-space:nowrap}
.qitems td.n{font-weight:600}
.qitems tr.tb td{border-top:2px solid var(--navy)}
.qitems td.P{color:var(--red);font-weight:700}
.qitems td.pt{font-weight:700}
.tier{display:inline-block;min-width:66px;padding:0 5px;font-size:12px;font-weight:600}
.tier.t0{background:var(--navy);color:#fff}.tier.t1{background:#5b5d86;color:#fff}.tier.t2{background:var(--band);color:var(--navy);outline:1px solid var(--line)}.tier.t3{background:#fbe3e2;color:#a8322e}
table.t td,table.t th{font-size:19px;padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
#agq-tab table.t td,#agq-tab table.t th{font-size:12.5px;padding:3px 8px}
#tab-domains td,#tab-domains th,#tab-buckets td,#tab-buckets th{font-size:14px;padding:4px 8px}
table.t th{background:var(--navy);color:#fff;font-weight:600}
/* title slide */
#s-title .tlogo{position:absolute;left:539px;top:212px;width:202px;height:204px}
#s-title .l1{position:absolute;left:0;right:0;top:452px;text-align:center;font-size:32px;font-weight:700;color:var(--navy)}
#s-title .l2{position:absolute;left:0;right:0;top:506px;text-align:center;font-size:30px;color:#595959}
#s-title .l3{position:absolute;left:0;right:0;top:562px;text-align:center;font-size:26px;color:#595959}
#s-title .l3 sup{font-size:.6em}
/* interactive panels */
.panel{position:absolute;left:16px;right:16px;top:74px;bottom:56px;display:grid;grid-template-columns:226px 1fr 296px;gap:12px}
.ctrl{font-size:13px;overflow:hidden;border-right:1px solid var(--line);padding-right:10px}
.ctrl label.h{display:block;font-weight:700;font-size:12px;letter-spacing:.3px;text-transform:uppercase;color:var(--navy);margin:8px 0 3px}
.ctrl select{width:100%;font:inherit;font-size:13px;padding:2px 3px;border:1px solid #b9bbc8;border-radius:3px;background:#fff;color:var(--ink)}
.ctrl .cb{display:flex;align-items:center;gap:5px;margin:1px 0;font-size:13px;cursor:pointer}
.ctrl .cb input{margin:0}
.ctrl .cb.dis{opacity:.35}
.ctrl input[type=range]{width:100%}
.sw{display:inline-block;width:14px;height:12px;flex:none}
.chart{position:relative;overflow:hidden}
.side{font-size:13px;border-left:1px solid var(--line);padding-left:12px;overflow-y:auto;overflow-x:hidden}
.side h4{margin:4px 0 6px;font-size:14px;text-transform:uppercase;letter-spacing:.3px}
.side table{border-collapse:collapse;width:100%}
.side td,.side th{font-size:12.5px;padding:3px 4px;border-bottom:1px solid var(--line);text-align:right}
.side th{font-weight:700;color:var(--navy);border-bottom:2px solid var(--navy)}
.side td:first-child,.side th:first-child{text-align:left}
.side .note{font-size:11.5px;color:var(--muted);line-height:1.35;margin:6px 0}
.side .hl{background:#fbeceb}
#s-bal .panel{grid-template-columns:210px 1fr 332px}
.side td .ci{display:block;font-size:10.5px;color:var(--muted)}
.fn{position:absolute;left:210px;right:90px;bottom:16px;font-size:11.5px;color:var(--muted);line-height:1.3}
svg text{font-family:Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif}
#tip{position:fixed;pointer-events:none;background:#fff;border:1px solid var(--navy);color:var(--ink);font:12px/1.35 Montserrat,"Helvetica Neue",Arial,sans-serif;
  padding:6px 8px;max-width:320px;display:none;z-index:10;box-shadow:0 2px 6px rgba(0,0,0,.15)}
#nav{position:fixed;left:50%;bottom:4px;transform:translateX(-50%);font:12px Montserrat,Arial,sans-serif;color:#9a9cb0;z-index:5;user-select:none}
#nav span{cursor:pointer;padding:0 8px}
@media print{#nav{display:none}}
</style>
</head>
<body>
<div id="stage">

<!-- 1 -->
<section class="slide" id="s-title">
  <img class="tlogo" alt="CarDS Lab logo" src="data:image/png;base64,__LOGO__">
  <div class="l1">CarDS Lab Presentation</div>
  <div class="l2">ECG-TTE</div>
  <div class="l3">October 1<sup>st</sup>, 2026</div>
</section>

<!-- 2 -->
<section class="slide" data-title="Background">
  <div class="body">
    <h2>Does X cause Y?</h2>
    <svg id="svg-rct" width="1184" height="360" viewBox="0 0 1184 360"></svg>
    <p style="margin-top:6px">Randomization balances measured and unmeasured characteristics: <i>ceteris paribus</i>.</p>
    <p>RCTs are costly and slow, and often exclude older, multimorbid and underrepresented patients.</p>
  </div>
</section>

<!-- 3 -->
<section class="slide" data-title="Problem">
  <div class="body">
    <h2>Does propensity score matching achieve <i>ceteris paribus</i>?</h2>
    <div style="display:grid;grid-template-columns:600px 1fr;gap:40px">
      <svg id="svg-psm" width="600" height="420" viewBox="0 0 600 420"></svg>
      <div style="padding-top:18px">
        <p>Propensity scores (PS) balance only what is measured.</p>
        <p>Claims record diagnoses, procedures and prescriptions consistently.</p>
        <p>EHR labs, vital signs and imaging are missing for many patients, and not at random.</p>
        <p>Many cardiovascular determinants of treatment and prognosis are <span class="red">physiological</span>.</p>
      </div>
    </div>
  </div>
</section>

<!-- 4 -->
<section class="slide" data-title="AI-ECG">
  <div class="body">
    <h2>The 12-lead ECG as a probe of physiology</h2>
    <svg id="svg-ecg" width="1184" height="250" viewBox="0 0 1184 250"></svg>
    <p style="margin-top:16px">Inexpensive and recorded routinely, for most patients.</p>
    <p>AI-ECG detects LV dysfunction, structural heart disease and other latent phenotypes.</p>
    <p>Foundation-model embeddings: general-purpose representations of cardiac physiology.</p>
    <p><b>Question:</b> does an ECG embedding capture confounding that structured data miss?</p>
  </div>
</section>

<!-- 5 -->
<section class="slide" data-title="Aims and hypotheses">
  <div class="body">
    <table class="t">
      <tr><th style="width:250px">Aim</th><th>Hypothesis: adding the ECG embedding to the PS ...</th></tr>
      <tr><td><b>1. Balance</b><br><span class="small">held-out characteristics</span></td><td>improves balance on clinical, laboratory and echocardiographic characteristics that no PS uses; a permuted-ECG placebo does not</td></tr>
      <tr><td><b>2. Agreement</b><br><span class="small">with RCT results</span></td><td>moves emulated hazard ratios toward each trial's own RCT result, beyond generic attenuation</td></tr>
      <tr><td><b>3. Bias removal</b><br><span class="small">known truth (plasmode)</span></td><td>removes part of the bias from a hidden physiological confounder, in proportion to how well the ECG encodes it</td></tr>
    </table>
  </div>
</section>

<!-- 6 -->
<section class="slide" data-title="Study design: trials">
  <div class="body">
    <h2>38 target trial emulations in Yale New Haven Health System EHR data</h2>
    <svg id="svg-trials" width="1184" height="350" viewBox="0 -20 1184 350"></svg>
    <p style="margin-top:10px">New-user, active-comparator designs; index dates 2011–2024; outcome = the trial's primary endpoint.</p>
    <p id="qual-count">Emulation quality (design items only): see next slides.</p>
  </div>
</section>

<!-- 6b -->
<section class="slide" data-title="Emulation quality">
  <div class="body">
    <h2>Emulation quality of the 38 trials</h2>
    <p class="small" style="margin:0 0 8px">Points = 1 per design flag (in-hospital start, run-in, baseline-therapy switch, follow-up ≥48 mo, time-zero issue) + comparator and outcome fidelity (moderate 1, poor 2). A poor item or ≥2 flags caps the tier at Moderate. Rated from trial protocols, blind to all results.</p>
    <div id="qual-grid" class="qgrid"></div>
    <p class="xs" id="qual-cls" style="margin-top:8px"></p>
  </div>
</section>

<!-- 6c -->
<section class="slide" data-title="Emulation quality: item-level breakdown">
  <div class="body">
    <div id="qual-items" class="qitems"></div>
    <p class="xs" style="margin-top:6px">✓ = design flag present. F1 in-hospital start not mirrored · F2 responder/tolerability run-in · F3 baseline-therapy switch at randomization · F4 follow-up ≥48 mo · F5 other time-zero issue. Comparator/outcome: G good (0), M moderate (1), P poor (2; placebo proxy, hypothesis-changing substitution, or endpoint not ascertainable). Tier: 0 Excellent, 1–2 Good, 3 Moderate, ≥4 Limited; a poor item or ≥2 flags caps the tier at Moderate. Design items only, blind to results (docs/v19/QUALITY_REAUDIT.md).</p>
  </div>
</section>

<!-- 7 -->
<section class="slide" data-title="Study design: PS ladder">
  <div class="body">
    <h2>Six PS specifications, each with and without the ECG</h2>
    <svg id="svg-ladder" width="1184" height="430" viewBox="0 0 1184 430"></svg>
    <p class="small" style="margin-top:4px">L2-penalized logistic PS; 1:1 greedy nearest-neighbour matching on the PS logit, caliper 0.2 SD. All other choices held constant across arms.</p>
  </div>
</section>

<!-- 8 -->
<section class="slide" data-title="Methods overview">
  <div class="body">
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:26px;margin-top:10px">
      <div class="card" style="height:260px"><h3><span class="tag">1</span>Held-out balance</h3>
        <p>58 characteristics that no PS uses: coded-record summaries, vital signs, labs, 35 echo measures.</p>
        <p>Endpoint: % with |SMD| &lt; 0.1 after matching.</p></div>
      <div class="card" style="height:260px"><h3><span class="tag">2</span>Agreement with RCT</h3>
        <p>Emulated vs published RCT hazard ratio.</p>
        <p>|Δ log HR|, statistical consistency, and a benchmark-shuffle test for trial-specific agreement.</p></div>
      <div class="card" style="height:260px"><h3><span class="tag">3</span>Plasmode simulation</h3>
        <p>Known true HR; a measured confounder hidden from every PS.</p>
        <p>Endpoint: % of bias removed by adding the ECG.</p></div>
    </div>
    <p style="margin-top:26px">Trials are the unit of replication: paired sign-flip tests across trials.</p>
  </div>
</section>

<!-- 9 -->
<section class="slide" data-title="Method 1: held-out balance">
  <div class="body">
    <div style="display:grid;grid-template-columns:1fr 500px;gap:36px">
      <div>
        <p>SMD = (mean<sub>T</sub> − mean<sub>C</sub>) / pooled SD before matching. "Held-out": not in the PS being evaluated.</p>
        <p>Per trial: % of held-out characteristics with |SMD| &lt; 0.1; arms compared within trial; one-sided sign-flip test across trials. Placebo: ECG embeddings permuted between patients.</p>
        <p><b>Primary panel (58).</b> Fixed before results. Directly measured physiology most relevant to cardiac confounding and to what an ECG can reflect: 35 echocardiographic measures, vital signs, laboratory values (incl. NT-proBNP), plus coded-record summaries.</p>
        <p><b>Expanded panel (~330 per trial).</b> Assembled afterwards from the literature: comorbidity indices, drug classes, healthcare use, devices, additional labs. Mostly coded-record items, partly proxied by PS diagnoses; excludes PS variables, treatment-revealing and ECG-proximal items. Used as a sensitivity analysis.</p>
      </div>
      <div><table class="t" id="tab-domains"></table><table class="t" id="tab-buckets" style="margin-top:10px"></table></div>
    </div>
  </div>
</section>

<!-- 10 -->
<section class="slide" data-title="Results 1: covariate balance explorer" id="s-bal">
  <div class="panel">
    <div class="ctrl" id="bal-ctrl"></div>
    <div class="chart"><svg id="bal-svg" width="714" height="590"></svg></div>
    <div class="side" id="bal-sum"></div>
  </div>
</section>

<!-- 11 -->
<section class="slide" data-title="Method 2: agreement with RCT results">
  <div class="body">
    <div style="display:grid;grid-template-columns:1fr 430px;gap:40px">
      <div>
        <p>Emulated HR: Cox model in the matched cohort, robust variance clustered on matched pairs. Reference: published RCT HR (primary endpoint).</p>
        <p><b>Distance:</b> |Δ log HR| = |log HR<sub>emulated</sub> − log HR<sub>RCT</sub>|.</p>
        <p><b>Consistency:</b> |z| &lt; 1.96, z = Δ / √(SE<sub>emulated</sub>² + SE<sub>RCT</sub>²).</p>
        <p><b>Benchmark shuffle:</b> reassign RCT results at random among trials. If the gain is as large with wrong benchmarks, it is generic attenuation, not trial-specific agreement.</p>
      </div>
      <svg id="svg-shuffle" width="430" height="400" viewBox="0 0 430 400"></svg>
    </div>
  </div>
</section>

<!-- 12 -->
<section class="slide" data-title="Results 2: trial emulation explorer" id="s-emu">
  <div class="panel" style="bottom:66px">
    <div class="ctrl" id="emu-ctrl"></div>
    <div class="chart"><svg id="emu-svg" width="714" height="580"></svg></div>
    <div class="side" id="emu-sum"></div>
  </div>
  <div class="fn">Trial-type categories were defined post hoc. The AF signal did not replicate in 5 prespecified AF trials (FRAIL-AF, LAAOS III, PROTECT AF, RAFT-AF, ACTIVE W; P1 |Δ| 0.254 → 0.199, 3/5 closer, p = 0.19; benchmark shuffle p = 0.28).</div>
</section>

<section class="slide" data-title="Agreement with RCTs by emulation quality" id="s-agq">
  <div class="panel" style="bottom:66px">
    <div class="ctrl" id="agq-ctrl"></div>
    <div class="chart" style="padding:4px 10px"><svg id="agq-svg" width="714" height="330"></svg><div id="agq-tab"></div></div>
    <div class="side" id="agq-note"></div>
  </div>
  <div class="fn">Quality groups from design items only (docs/v19/QUALITY_REAUDIT.md). RCT-DUPLICATE (Wang, JAMA 2023; post hoc): closely vs not closely emulated trials, r 0.93 vs 0.53, estimate agreement 88% vs 50%, standardized-difference agreement 88% vs 69%. Descriptive; no between-group test.</div>
</section>

<!-- 13 -->
<section class="slide" data-title="Method 3: plasmode simulation">
  <div class="body">
    <h2>A simulation built on real patients</h2>
    <svg id="svg-plasmode" width="1184" height="330" viewBox="0 0 1184 330"></svg>
    <p style="margin-top:6px">Real covariates, ECGs and follow-up are kept; treatment and outcome are simulated with a known true HR.</p>
    <p>A measured confounder C is hidden from every PS. Bias = estimate − truth.</p>
  </div>
</section>

<!-- 14 -->
<section class="slide" data-title="Method 3: simulation set-up">
  <div class="body">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:40px">
      <div>
        <p><b>Hidden confounder C:</b> echo LVEF, NT-proBNP, BMI or eGFR.</p>
        <p><b>Cells:</b> 107 trial × confounder combinations in 31 trials (≥300 per arm with C observed; 1 calibration failure excluded).</p>
        <p><b>Confounding grid:</b> OR per SD of C for treatment and HR per SD for the outcome, each 1.25, 1.5 or 2 (9 scenarios) plus a null.</p>
        <p><b>Replicates:</b> 50 subsamples (80%) per cell; true HR 0.80; PS refitted and re-matched each time.</p>
      </div>
      <div>
        <table class="t">
          <tr><th>Arm (demographic PS +)</th><th>Role</th></tr>
          <tr><td>nothing (base)</td><td>reference bias</td></tr>
          <tr><td>ECG, 32 PCs</td><td>test</td></tr>
          <tr><td>permuted ECG; 32 noise columns</td><td>placebos</td></tr>
          <tr><td>C itself (oracle)</td><td>ceiling</td></tr>
        </table>
        <p style="margin-top:16px;font-size:19px">% bias removed = 100 × (1 − Σ bias<sub>arm</sub> / Σ bias<sub>base</sub>)</p>
        <p style="font-size:19px">Compared with the ECG's cross-fitted partial R² for C (given demographics) in the real data.</p>
      </div>
    </div>
  </div>
</section>

<!-- 15 -->
<section class="slide" data-title="Results 3: plasmode explorer" id="s-sim">
  <div class="panel">
    <div class="ctrl" id="sim-ctrl"></div>
    <div class="chart"><svg id="sim-svg" width="714" height="590"></svg></div>
    <div class="side" id="sim-sum"></div>
  </div>
</section>

<!-- 16 -->
<section class="slide" data-title="Summary">
  <div class="body">
    <ol style="margin:0;padding-left:30px">
      <li><b>Balance.</b> With a demographic PS, held-out characteristics with |SMD| &lt; 0.1 rose from 51% to 57% (28/38 trials, p = 0.0002); permuted ECG: 51% → 52%. The gain shrinks as the PS gets richer (clinical PS: +1.3 points, p = 0.20).</li>
      <li><b>RCT agreement.</b> Mean |Δ log HR| fell from 0.26 to 0.21 (25/38 closer, p = 0.002), but benchmark shuffle p = 0.22: mostly <span class="red">generic attenuation</span>, not trial-specific. The AF signal did not replicate in 5 prespecified AF trials.</li>
      <li><b>Known truth.</b> The ECG removed 14% of hidden-confounder bias (oracle 93%; placebos 0–1.5%), roughly 100 × the ECG's R² for the confounder.</li>
      <li><b>Comparator.</b> CLMBR-T (structured-EHR model; exploratory) gave larger balance gains (+10.9 points at P1); ECG added +2.2 on top.</li>
    </ol>
  </div>
</section>

<!-- 17 -->
<section class="slide" data-title="Limitations and next steps">
  <div class="body grid2">
    <div>
      <h2>Limitations</h2>
      <ul>
        <li>One health system.</li>
        <li>RCT results are imperfect benchmarks; trial-type categories were post hoc.</li>
        <li>General-purpose ECG embedding: R² ≤ 0.35 for any confounder.</li>
        <li>Most analyses exploratory; CLMBR-T comparison tentative.</li>
      </ul>
    </div>
    <div>
      <h2>Next steps</h2>
      <ul>
        <li>External validation: MIMIC-IV, UK Biobank.</li>
        <li>Better ECG representations (task-specific, higher R² for physiology).</li>
        <li>Manuscript: JAMA Cardiology submission.</li>
      </ul>
    </div>
  </div>
</section>

</div>
<div id="tip"></div>
<div id="nav"><span id="nav-prev">&#8249;</span><span id="nav-count"></span><span id="nav-next">&#8250;</span></div>

<script>
"use strict";
const D = __DATA__;
const LOGO = "data:image/png;base64,__LOGO__";
const NAVY = "#0E103C", RED = "#DC5A55";
const ARM = {
  unmatched: {lab: "Unmatched", col: "#8a8d99", mk: "x"},
  base: {lab: "PS alone", col: NAVY, mk: "circle"},
  ECG: {lab: "+ ECG", col: RED, mk: "circle"},
  CLMBR: {lab: "+ CLMBR-T", col: "#2a78d6", mk: "square"},
  "CLMBR+ECG": {lab: "+ CLMBR-T + ECG", col: "#1baf7a", mk: "diamond"},
  shufECG: {lab: "+ permuted ECG", col: "#d69a00", mk: "tri", hollow: true},
  noise96: {lab: "+ noise (96 cols)", col: "#7a6a58", mk: "square", hollow: true},
  noise32: {lab: "+ noise (32 cols)", col: "#7a6a58", mk: "square", hollow: true},
  oracle: {lab: "+ C (oracle)", col: "#008300", mk: "diamond"}
};
const RUNG = {P1: "P1 demographics", P5: "P5 demo + 5 dx", P2: "P2 demo + 5 dx + obesity", sparse: "Sparse (demo + 9–13 dx)",
  hdPS200: "hdPS (+200 codes)", clinical: "Clinical (+vitals, labs, LVEF, meds, use)"};
const RSHORT = {P1: "P1", P5: "P5", P2: "P2", sparse: "sparse PS", hdPS200: "hdPS", clinical: "clinical PS"};
const AREAS = ["AF", "HF", "Diabetes", "Hypertension", "ACS / MI", "Other"];
const QUAL = {strict: "High (strict)", high: "High", lower: "Lower"};
const CONFLAB = {lvef: "Echo LVEF", ntprobnp: "NT-proBNP", bmi: "BMI", egfr: "eGFR"};
const NT = D.trials.length;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const fin = x => x !== null && x !== undefined && Number.isFinite(x);
const mean = a => { const b = a.filter(fin); return b.length ? b.reduce((s, x) => s + x, 0) / b.length : NaN; };
const median = a => { const b = a.filter(fin).sort((x, y) => x - y); const n = b.length; if (!n) return NaN; return n % 2 ? b[(n - 1) / 2] : (b[n / 2 - 1] + b[n / 2]) / 2; };
const fmtp = p => !Number.isFinite(p) ? "–" : p < 0.001 ? (p < 0.0001 ? "<0.0001" : p.toFixed(4)) : p < 0.01 ? p.toFixed(3) : p.toFixed(2);
const f1 = x => Number.isFinite(x) ? x.toFixed(1) : "–";
const f3 = x => Number.isFinite(x) ? x.toFixed(3) : "–";

/* ---------- statistics ---------- */
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function subsetSums(a) { let s = new Float64Array([0]); for (const v of a) { const n = new Float64Array(s.length * 2); for (let i = 0; i < s.length; i++) { n[2 * i] = s[i] + v; n[2 * i + 1] = s[i] - v; } s = n; } return s; }
/* exact one-sided sign-flip p for H1: mean(d) > 0; P(sum of randomly signed |d| >= observed), meet in the middle */
function signflip(d) {
  d = d.filter(fin); const k = d.length; if (!k) return NaN;
  const a = d.map(Math.abs), S = d.reduce((s, x) => s + x, 0), eps = 1e-10 * Math.max(a.reduce((s, x) => s + x, 0), 1e-300);
  const L = subsetSums(a.slice(0, k >> 1)), R = subsetSums(a.slice(k >> 1)).sort();
  let cnt = 0; const n = R.length;
  for (let i = 0; i < L.length; i++) { const thr = S - eps - L[i]; let lo = 0, hi = n; while (lo < hi) { const m = (lo + hi) >> 1; if (R[m] < thr) lo = m + 1; else hi = m; } cnt += n - lo; }
  return cnt / Math.pow(2, k);
}
/* benchmark shuffle: permute (rb, rs) among the k trials; stat = mean(|la - q| - |lb - q|); p = P(null <= obs) */
function benchShuffle(la, lb, rb, ndraw) {
  const k = la.length; if (k < 2) return NaN;
  const st = q => { let s = 0; for (let i = 0; i < k; i++) s += Math.abs(la[i] - q[i]) - Math.abs(lb[i] - q[i]); return s / k; };
  const obs = st(rb), rng = mulberry32(20261001), idx = rb.map((_, i) => i); let c = 0;
  for (let r = 0; r < ndraw; r++) {
    for (let i = k - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); const t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    if (st(idx.map(i => rb[i])) <= obs + 1e-12) c++;
  }
  return c / ndraw;
}

/* ---------- small SVG helpers ---------- */
const NS = "http://www.w3.org/2000/svg";
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
function trialOptions(withSingle) {
  let h = `<option value="all">All ${NT} trials</option><optgroup label="Clinical area">`;
  for (const a of AREAS) h += `<option value="area:${a}">${a} (${D.trials.filter(t => t.area === a).length})</option>`;
  h += `</optgroup><optgroup label="Emulation quality">`;
  const nq = q => D.trials.filter(t => q.includes(t.qt.tier.split(" ")[0])).length;
  for (const q of [["Excellent", "Good", "Moderate"], ["Excellent"], ["Good"], ["Excellent", "Good"], ["Moderate"], ["Limited"], ["Moderate", "Limited"]]) h += `<option value="q:${q.join(",")}">${q.join(" or ")} (${nq(q)})</option>`;
  h += `</optgroup><optgroup label="ECG relevance">`;
  for (const e of ["high", "medium", "low"]) h += `<option value="e:${e}">${e[0].toUpperCase() + e.slice(1)} (${D.trials.filter(t => t.ecg === e).length})</option>`;
  h += `</optgroup>`;
  if (withSingle) { h += `<optgroup label="Single trial">`; D.trials.map((t, i) => [t.name, i]).sort().forEach(([n, i]) => h += `<option value="t:${i}">${esc(n)}</option>`); h += `</optgroup>`; }
  return h;
}
function trialSet(v) {
  const idx = D.trials.map((_, i) => i);
  if (v === "all") return idx;
  const [k, x] = v.split(":");
  if (k === "area") return idx.filter(i => D.trials[i].area === x);
  if (k === "q") { const q = x.split(","); return idx.filter(i => q.includes(D.trials[i].qt.tier.split(" ")[0])); }
  if (k === "e") return idx.filter(i => D.trials[i].ecg === x);
  if (k === "t") return [+x];
  return idx;
}
function armBoxes(name, arms, defs) {
  return arms.map(a => `<label class="cb" data-arm="${a}"><input type="checkbox" name="${name}" value="${a}" ${defs.includes(a) ? "checked" : ""}>${swatch(a)}${ARM[a].lab}</label>`).join("");
}
const checked = name => [...document.querySelectorAll(`input[name="${name}"]:checked`)].map(x => x.value);
const rungSel = id => `<select id="${id}">` + Object.entries(RUNG).map(([k, v]) => `<option value="${k}">${v}</option>`).join("") + `</select>`;

/* =========================================================
   PANEL 1: balance explorer
   ========================================================= */
const GROUPS58 = [...new Set(D.vars.map(v => v.g))];
const GSHORT = {"Coded record": "Coded", "Vitals & core labs": "Vitals / labs", "Other labs": "Other labs", "Echo: LV structure": "LV structure",
  "Echo: LV function": "LV function", "Echo: diastolic / LA": "Diastolic / LA", "Echo: RV / pulmonary": "RV / pulm.", "Echo: valves / aorta": "Valves / aorta",
  "Comorbidities": "Comorbidities", "Medications": "Medications", "Healthcare use & testing": "Use & testing", "Additional labs & vitals": "Labs & vitals",
  "Devices & procedures": "Devices", "Preventive care": "Preventive", "Risk & frailty scores": "Scores"};
function balInit() {
  $("#bal-ctrl").innerHTML = `
  <label class="h">PS base</label>${rungSel("bal-rung")}
  <label class="h">Comparison arms</label>
  <div id="bal-arms">${armBoxes("bal-arm", ["unmatched", "base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG", "noise96"], ["unmatched", "base", "ECG", "shufECG"])}</div>
  <label class="h">Variable set</label>
  <select id="bal-set"><option value="v58">Primary 58, by variable</option><option value="d58">Primary 58, by domain</option>
   <option value="vexp">Expanded panel, by variable</option><option value="bexp">Expanded panel, by bucket</option>
   <option value="vall">All held-out (58 + expanded), by variable</option><option value="ball">All held-out, by domain/bucket</option></select>
  <label class="h">Domain</label><select id="bal-dom"></select>
  <label class="h">Show top <span id="bal-nlab"></span> by unmatched |SMD|</label><input type="range" id="bal-n" min="10" max="58" value="58">
  <label class="h">Trials</label><select id="bal-trials">${trialOptions(true)}</select>
  <label class="h">Across trials</label><select id="bal-stat"><option value="median">Median</option><option value="mean">Mean</option></select>
  <label class="h">Balance threshold</label><select id="bal-thr"><option value="0.1">|SMD| &lt; 0.10 (conventional)</option><option value="0.15">|SMD| &lt; 0.15</option><option value="0.2">|SMD| &lt; 0.20 (lenient)</option></select>
  <label class="cb" style="margin-top:8px"><input type="checkbox" id="bal-ref" checked>Threshold line</label>`;
  const onSet = () => {
    const s = $("#bal-set").value, exp = s.endsWith("exp"), all = s.endsWith("all");
    const groups = all ? GROUPS58.concat(D.exp.buckets) : exp ? D.exp.buckets : GROUPS58;
    $("#bal-dom").innerHTML = `<option value="all">All domains</option>` + groups.map(g => `<option>${esc(g)}</option>`).join("");
    const nmax = all ? 58 + D.exp.vars.length : exp ? D.exp.vars.length : 58; const r = $("#bal-n"); r.max = nmax; r.value = (exp || all) ? 60 : 58;
    balUpdate();
  };
  $("#bal-set").onchange = onSet;
  $("#bal-rung").onchange = balUpdate;
  for (const id of ["bal-dom", "bal-trials", "bal-stat", "bal-ref", "bal-thr"]) $("#" + id).onchange = balUpdate;
  $("#bal-n").oninput = balUpdate;
  $("#bal-arms").onchange = balUpdate;
  bindTips($("#bal-svg"));
  onSet();
}
function balModel() {
  const rung = $("#bal-rung").value, set = $("#bal-set").value, all = set.endsWith("all"), exp = set.endsWith("exp") || all;
  const avail = ["unmatched", "base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG", "noise96"];
  document.querySelectorAll("#bal-arms .cb").forEach(l => { const ok = avail.includes(l.dataset.arm); l.classList.toggle("dis", !ok); l.querySelector("input").disabled = !ok; });
  const arms = checked("bal-arm").filter(a => avail.includes(a));
  const T = trialSet($("#bal-trials").value);
  const stat = $("#bal-stat").value === "mean" ? mean : median;
  let vars, get; /* get(arm, trial, j) -> |SMD| or null */
  const get58 = (a, t, j) => { const b = D.bal[rung].base[t][j]; if (b === null) return null; return a === "unmatched" ? D.bal.none.unmatched[t][j] : D.bal[rung][a][t][j]; };
  const getX = (a, t, j) => a === "unmatched" ? D.exp.smd.none.unmatched[t][j] : D.exp.smd[rung][a][t][j];
  const v58 = D.vars.map((v, j) => ({j, lab: v.lab, g: v.g, def: ""}));
  const vX = D.exp.vars.map((v, j) => ({j: 1000 + j, lab: v.lab, g: v.b, def: v.d}));
  if (all) { vars = v58.concat(vX); get = (a, t, j) => j >= 1000 ? getX(a, t, j - 1000) : get58(a, t, j); }
  else if (exp) { vars = vX; get = (a, t, j) => getX(a, t, j - 1000); }
  else { vars = v58; get = get58; }
  const dom = $("#bal-dom").value;
  vars = vars.filter(v => dom === "all" || v.g === dom);
  vars.forEach(v => { v.u = stat(T.map(t => get("unmatched", t, v.j))); });
  vars = vars.filter(v => T.some(t => fin(get("base", t, v.j))));
  const N = +$("#bal-n").value;
  $("#bal-nlab").textContent = Math.min(N, vars.length) + " of " + vars.length;
  const top = new Set([...vars].sort((a, b) => (fin(b.u) ? b.u : -1) - (fin(a.u) ? a.u : -1)).slice(0, N).map(v => v.j));
  vars = vars.filter(v => top.has(v.j));
  return {rung, set, exp, all, arms, T, stat, vars, get};
}
function balUpdate() {
  const M = balModel(), {arms, T, stat, vars, get, exp, all} = M;
  const byDom = M.set.startsWith("d") || M.set.startsWith("b");
  const groups = all ? GROUPS58.concat(D.exp.buckets) : exp ? D.exp.buckets : GROUPS58;
  let rows = [];
  if (byDom) {
    for (const g of groups) { const vs = vars.filter(v => v.g === g); if (!vs.length) continue;
      const r = {lab: `${g} (${vs.length})`, g, val: {}, tipx: ""};
      for (const a of arms) r.val[a] = stat(T.map(t => mean(vs.map(v => get(a, t, v.j)))));
      rows.push(r); }
  } else {
    for (const g of groups) for (const v of vars.filter(v => v.g === g)) {
      const r = {lab: v.lab, g, val: {}, tipx: v.def};
      for (const a of arms) r.val[a] = stat(T.map(t => get(a, t, v.j)));
      rows.push(r); }
  }
  /* draw */
  const W = 714, H = 590, ml = byDom ? 210 : 182, mr = 24, mt = 28, mb = 40;
  const ph = H - mt - mb, rh = ph / Math.max(rows.length, 1);
  let xmax = 0.05; rows.forEach(r => arms.forEach(a => { if (fin(r.val[a])) xmax = Math.max(xmax, r.val[a]); }));
  xmax = Math.min(1.5, Math.ceil(xmax * 1.08 * 20) / 20);
  const xs = x => ml + (Math.min(x, xmax) / xmax) * (W - ml - mr);
  let s = "";
  const statLab = $("#bal-stat").value;
  s += `<text x="${ml}" y="16" font-size="13" font-weight="700" fill="${NAVY}">${byDom ? "Mean |SMD| per domain" : "|SMD| after matching"} (${statLab} across ${T.length} trial${T.length > 1 ? "s" : ""})</text>`;
  let prevG = null;
  rows.forEach((r, i) => {
    const y = mt + i * rh + rh / 2;
    if (i % 2 === 0) s += `<rect x="${ml}" y="${mt + i * rh}" width="${W - ml - mr}" height="${rh}" fill="${"#f5f5f8"}"/>`;
    if (r.g !== prevG && !byDom) { const gh = rh * rows.filter(q => q.g === r.g).length;
      s += `<line x1="4" x2="${W - mr}" y1="${mt + i * rh}" y2="${mt + i * rh}" stroke="#b9bbc8" stroke-width="0.8"/>`;
      const gl = GSHORT[r.g] || r.g; if (gh > gl.length * 5.2) s += `<text transform="translate(12 ${mt + i * rh + gh / 2}) rotate(-90)" font-size="9.5" font-weight="700" text-anchor="middle" fill="${RED}">${esc(gl)}</text>`; prevG = r.g; }
    const fs = Math.max(6, Math.min(12, rh * 0.8));
    if (rh >= 5.5) s += `<text x="${ml - 5}" y="${y + fs * 0.35}" font-size="${fs}" text-anchor="end" fill="${NAVY}">${esc(r.lab)}</text>`;
    const vals = arms.filter(a => fin(r.val[a]));
    if (vals.length > 1) { const mn = Math.min(...vals.map(a => r.val[a])), mx = Math.max(...vals.map(a => r.val[a]));
      s += `<line x1="${xs(mn)}" x2="${xs(mx)}" y1="${y}" y2="${y}" stroke="#c9cad4" stroke-width="1"/>`; }
    const tipTxt = `<b>${esc(r.lab)}</b>${r.tipx ? "<br><span style='color:#666'>" + esc(r.tipx) + "</span>" : ""}<br>` + arms.map(a => `${ARM[a].lab}: ${f3(r.val[a])}`).join("<br>");
    s += `<rect x="0" y="${mt + i * rh}" width="${W}" height="${rh}" fill="transparent" data-tip="${esc(tipTxt)}"/>`;
    for (const a of arms) if (fin(r.val[a])) s += marker(ARM[a].mk, xs(r.val[a]), y, Math.max(2.2, Math.min(5, rh * 0.38)), ARM[a].col, ARM[a].hollow, `pointer-events="none"`);
  });
  const y0 = mt + ph;
  s += `<line x1="${ml}" x2="${W - mr}" y1="${y0}" y2="${y0}" stroke="${NAVY}"/>`;
  const step = xmax > 0.6 ? 0.2 : xmax > 0.3 ? 0.1 : 0.05;
  for (let x = 0; x <= xmax + 1e-9; x += step) s += `<line x1="${xs(x)}" x2="${xs(x)}" y1="${y0}" y2="${y0 + 4}" stroke="${NAVY}"/><text x="${xs(x)}" y="${y0 + 16}" font-size="11" text-anchor="middle" fill="${NAVY}">${x.toFixed(2)}</text>`;
  s += `<text x="${(ml + W - mr) / 2}" y="${y0 + 33}" font-size="12" text-anchor="middle" fill="${NAVY}">|standardized mean difference|</text>`;
  const thr = +$("#bal-thr").value, thrL = thr.toFixed(2);
  if ($("#bal-ref").checked && thr <= xmax) s += `<line x1="${xs(thr)}" x2="${xs(thr)}" y1="${mt}" y2="${y0}" stroke="${RED}" stroke-dasharray="4 3" stroke-width="1.2" pointer-events="none"/>`;
  $("#bal-svg").innerHTML = s;
  /* summary: per-trial % of selected variables with |SMD| < thr, averaged across trials */
  const pct = a => T.map(t => { let n = 0, k = 0; for (const v of vars) { const x = get(a, t, v.j); if (fin(x)) { n++; if (x < thr) k++; } } return n ? 100 * k / n : NaN; });
  const trialMean = a => T.map(t => mean(vars.map(v => get(a, t, v.j))));
  const trialMax = a => T.map(t => { const x = vars.map(v => get(a, t, v.j)).filter(fin); return x.length ? Math.max(...x) : NaN; });
  const P = {}; for (const a of arms) P[a] = pct(a);
  const nOk = x => x.filter(fin).length, nBel = x => x.filter(v => fin(v) && v < thr).length;
  const SL = {unmatched: "Unmatched", base: "PS alone", ECG: "+ ECG", CLMBR: "+ CLMBR-T", "CLMBR+ECG": "+ CLMBR-T + ECG", shufECG: "+ perm. ECG", noise96: "+ noise"};
  const nAll = arms.map(a => nBel(trialMax(a))).reduce((x, y) => Math.max(x, y), 0);
  let h = `<h4>Balance, |SMD| &lt; ${thrL}</h4><table><tr><th>Arm</th><th>mean |SMD|</th><th>% vars</th><th>trials</th></tr>`;
  for (const a of arms) { const m = trialMean(a);
    h += `<tr><td>${swatch(a)} ${SL[a]}</td><td>${f3(mean(m))}</td><td>${f1(mean(P[a]))}</td><td>${nBel(m)}/${nOk(m)}</td></tr>`; }
  h += `</table><div class="note">% vars: shown variables below the threshold (mean over trials). Trials: trials whose mean |SMD| is below it${nAll ? "" : "; no trial had every shown variable below it"}.</div>`;
  /* relative reduction in mean |SMD| vs a reference arm: 100 * (1 - mean_t m_arm / mean_t m_ref), with a
     percentile bootstrap over trials (2,000 resamples, fixed seed) */
  const MS = {}; for (const a of arms) MS[a] = trialMean(a);
  const relRed = (ref, a) => {
    const idx = T.map((_, i) => i).filter(i => fin(MS[ref][i]) && fin(MS[a][i]));
    const rr = I => { let r = 0, x = 0; for (const i of I) { r += MS[ref][i]; x += MS[a][i]; } return 100 * (1 - x / r); };
    const est = rr(idx); if (idx.length < 3) return [est, NaN, NaN];
    let seed = 20261001; const rnd = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
    const bs = []; for (let b = 0; b < 2000; b++) bs.push(rr(idx.map(() => idx[Math.floor(rnd() * idx.length)])));
    bs.sort((x, y) => x - y); return [est, bs[49], bs[1949]];
  };
  const paired = (ref, refLab, cmp) => {
    const Pr = P[ref] || pct(ref);
    let t = `<h4 style="margin-top:10px">vs ${refLab} (paired by trial)</h4><table><tr><th>Arm</th><th>Δ pts</th><th>better</th><th>p</th><th>mean |SMD| reduction</th></tr>`;
    for (const a of cmp) { const d = T.map((_, i) => P[a][i] - Pr[i]);
      const ok = d.filter(fin); const p = T.length > 1 ? signflip(d) : NaN; const [rr, lo, hi] = relRed(ref, a);
      t += `<tr class="${a === "ECG" ? "hl" : ""}"><td>${SL[a]}</td><td>${(mean(d) >= 0 ? "+" : "") + f1(mean(d))}</td><td>${ok.filter(x => x > 0).length}/${ok.length}</td><td>${T.length > 1 ? fmtp(p) : "–"}</td><td>${f1(rr)}%${fin(lo) ? `<span class="ci">${f1(lo)} to ${f1(hi)}</span>` : ""}</td></tr>`; }
    return t + `</table>`;
  };
  const cU = arms.filter(a => a !== "unmatched"), cB = arms.filter(a => a !== "base" && a !== "unmatched");
  if (arms.includes("unmatched") && cU.length) h += paired("unmatched", "unmatched", cU);
  if (arms.includes("base") && cB.length) h += paired("base", "PS alone", cB);
  if ((arms.includes("unmatched") && cU.length) || (arms.includes("base") && cB.length))
    h += `<div class="note">Δ pts: change in % vars below the threshold; better: trials in which it rose; p: one-sided exact sign-flip test across trials. Mean |SMD| reduction: 1 − arm / reference mean |SMD| (no threshold), 95% CI by bootstrap over trials; vs unmatched = percent bias reduction.</div>`;
  else h += `<div class="note">Select "Unmatched" or "PS alone" and another arm to see paired comparisons.</div>`;
  h += `<div class="note">${M.exp ? "Expanded panel: about 330 pre-index characteristics per trial (comorbidities, medications, healthcare use, labs, devices, scores, preventive care), excluding variables in or derived from the selected PS, hdPS-selected codes and ECG-proximal variables." :
    "Primary panel: 58 characteristics not in any P-rung PS. At the clinical rung, variables in that PS are excluded."} Summary statistics only; no patient-level data.</div>`;
  $("#bal-sum").innerHTML = h;
}

/* =========================================================
   PANEL 2: trial emulation explorer
   ========================================================= */
function emuInit() {
  const sel = (id, opts) => `<select id="${id}">${opts}</select>`;
  $("#emu-ctrl").innerHTML = `
  <label class="h">Analysis</label>${sel("emu-est", `<option value="itt">Primary: all initiators (ITT)</option><option value="outpt">Outpatient initiators only</option><option value="pp_ipcw_365">Per-protocol (IPCW, 365-d grace)</option><option value="pp_ipcw_switch">Switch-only censoring (IPCW)</option><option value="landmark90">90-day landmark</option><option value="runin90">90-day run-in (repeat order)</option>`)}
  <label class="h">PS base</label>${rungSel("emu-rung")}
  <label class="h">Methods</label>
  <div id="emu-arms">${armBoxes("emu-arm", ["unmatched", "base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG", "noise96"], ["base", "ECG"])}</div>
  <label class="h">Clinical area</label>${sel("emu-area", `<option value="all">All</option>` + AREAS.map(a => `<option>${a}</option>`).join(""))}
  <label class="h">Emulation quality</label>${sel("emu-q", `<option value="all">All</option><optgroup label="Tier (points)"><option value="t:Excellent,Good,Moderate">Analysed set: excluding limited (32)</option><option value="t:Excellent">Excellent</option><option value="t:Good">Good</option><option value="t:Excellent,Good">Excellent or good</option><option value="t:Moderate">Moderate</option><option value="t:Limited">Limited</option><option value="t:Moderate,Limited">Moderate or limited</option></optgroup><optgroup label="3-class rule (adjudicated)"><option value="c:High (strict)">High (strict)</option><option value="c:High (strict),High">High, incl. strict</option><option value="c:Lower">Lower</option></optgroup>`)}
  <label class="h">ECG relevance</label>${sel("emu-e", `<option value="all">All</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option><option value="high,medium">High or medium</option>`)}
  <label class="h">Sort by</label>${sel("emu-sort", `<option value="area">Area, then RCT HR</option><option value="rct">RCT HR</option><option value="gap">|Δ| with PS alone</option><option value="chg">Change in |Δ| with ECG</option><option value="name">Name</option>`)}
  <div class="xs" style="margin-top:10px">Grey band: RCT 95% CI; black bar: RCT HR. Markers: emulated HR with 95% CI. Hover a row for values.</div>`;
  for (const id of ["emu-est", "emu-rung", "emu-area", "emu-q", "emu-e", "emu-sort"]) $("#" + id).onchange = emuUpdate;
  $("#emu-arms").onchange = emuUpdate;
  bindTips($("#emu-svg"));
  emuUpdate();
}
const NA2 = [NaN, NaN];
function emuEst(rung, a, t) { return estOf($("#emu-est").value, rung, a, t); }
function estOf(est, rung, a, t) {
  if (est === "itt") return a === "unmatched" ? D.est.none.unmatched[t] : D.est[rung][a][t];
  const S = D.sens[est]; const g = a === "unmatched" ? S.none : S[rung];
  return (g && g[a] && g[a][t]) || NA2;
}
const TIER = t => t.qt.tier.split(" ")[0];
const pearson = (x, y) => { const n = x.length; if (n < 3) return NaN; const mx = x.reduce((a, b) => a + b) / n, my = y.reduce((a, b) => a + b) / n;
  let sxy = 0, sxx = 0, syy = 0; for (let i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) ** 2; syy += (y[i] - my) ** 2; } return sxy / Math.sqrt(sxx * syy); };
/* RCT-DUPLICATE agreement metrics over trials T for one method */
function agree(est, rung, a, T) {
  const ok = T.filter(t => fin(estOf(est, rung, a, t)[0]));
  const L = ok.map(t => estOf(est, rung, a, t)), tr = ok.map(t => D.trials[t]);
  const d = L.map(([l], i) => Math.abs(l - tr[i].rb));
  return {n: ok.length, r: pearson(L.map(x => x[0]), tr.map(x => x.rb)), gap: mean(d),
    ea: ok.length ? d.filter((x, i) => x <= 1.96 * tr[i].rs).length / ok.length : NaN,
    sd: ok.length ? L.filter(([l, se], i) => Math.abs(l - tr[i].rb) / Math.sqrt(se * se + tr[i].rs * tr[i].rs) < 1.96).length / ok.length : NaN};
}
const pc = x => fin(x) ? Math.round(100 * x) + "%" : "–", f2 = x => fin(x) ? x.toFixed(2) : "–";
function emuUpdate() {
  const est = $("#emu-est").value;
  const ropt = $("#emu-rung").querySelectorAll("option");
  ropt.forEach(o => { o.disabled = est !== "itt" && !["P1", "P5"].includes(o.value); });
  if (est !== "itt" && !["P1", "P5"].includes($("#emu-rung").value)) $("#emu-rung").value = "P1";
  const avail = est === "itt" ? ["unmatched", "base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG", "noise96"] : ["unmatched", "base", "ECG", "shufECG"];
  document.querySelectorAll("#emu-arms .cb").forEach(l => { const ok = avail.includes(l.dataset.arm); l.classList.toggle("dis", !ok); l.querySelector("input").disabled = !ok; });
  const rung = $("#emu-rung").value, arms = checked("emu-arm").filter(a => avail.includes(a));
  const area = $("#emu-area").value, qv = $("#emu-q").value, e = $("#emu-e").value.split(",");
  const qok = tr => { if (qv === "all") return true; const [k, x] = qv.split(":"); const L = x.split(","); return k === "t" ? L.includes(TIER(tr)) : L.includes(tr.qt.cls); };
  let T = D.trials.map((_, i) => i).filter(i => (area === "all" || D.trials[i].area === area) && qok(D.trials[i]) && (e[0] === "all" || e.includes(D.trials[i].ecg)));
  if (est !== "itt") T = T.filter(t => fin(emuEst(rung, "base", t)[0]) && fin(emuEst(rung, "ECG", t)[0]));
  const gap = (a, t) => { const x = emuEst(rung, a, t)[0]; return fin(x) ? Math.abs(x - D.trials[t].rb) : NaN; };
  const srt = $("#emu-sort").value;
  const key = {area: t => [AREAS.indexOf(D.trials[t].area), D.trials[t].rb], rct: t => [D.trials[t].rb], name: t => [D.trials[t].name],
    gap: t => [-(gap("base", t) || 0)], chg: t => [(gap("ECG", t) - gap("base", t)) || 0]}[srt];
  T.sort((a, b) => { const ka = key(a), kb = key(b); for (let i = 0; i < ka.length; i++) { if (ka[i] < kb[i]) return -1; if (ka[i] > kb[i]) return 1; } return 0; });
  /* forest */
  const W = 714, H = 580, ml = 150, mr = 16, mt = 26, mb = 42, lo = Math.log(0.2), hi = Math.log(5);
  const ph = H - mt - mb, rh = ph / Math.max(T.length, 1);
  const xs = l => ml + (Math.max(lo, Math.min(hi, l)) - lo) / (hi - lo) * (W - ml - mr);
  const ESTLAB = {itt: "all initiators", outpt: "outpatient initiators", pp_ipcw_365: "per-protocol 365 d", pp_ipcw_switch: "switch-only", landmark90: "90-d landmark", runin90: "90-d run-in"};
  let s = `<text x="${ml}" y="15" font-size="13" font-weight="700" fill="${NAVY}">Hazard ratio, emulation vs RCT (PS ${RSHORT[rung]}; ${ESTLAB[est]}; ${T.length} trials)</text>`;
  for (const v of [0.25, 0.5, 1, 2, 4]) s += `<line x1="${xs(Math.log(v))}" x2="${xs(Math.log(v))}" y1="${mt}" y2="${mt + ph}" stroke="${v === 1 ? "#9a9cb0" : "#ececf1"}" stroke-width="${v === 1 ? 1.2 : 1}"/>`;
  const na = arms.length;
  T.forEach((t, i) => {
    const tr = D.trials[t], y0 = mt + i * rh, yc = y0 + rh / 2;
    if (i % 2 === 0) s += `<rect x="0" y="${y0}" width="${W}" height="${rh}" fill="#f7f7fa"/>`;
    s += `<rect x="${xs(tr.rb - 1.96 * tr.rs)}" y="${y0 + 1}" width="${xs(tr.rb + 1.96 * tr.rs) - xs(tr.rb - 1.96 * tr.rs)}" height="${Math.max(1, rh - 2)}" fill="#d9dae6"/>`;
    s += `<line x1="${xs(tr.rb)}" x2="${xs(tr.rb)}" y1="${y0 + 1}" y2="${y0 + rh - 1}" stroke="#000" stroke-width="2"/>`;
    const fs = Math.max(7, Math.min(12, rh * 0.75));
    s += `<text x="${ml - 6}" y="${yc + fs * 0.35}" font-size="${fs}" text-anchor="end" fill="${NAVY}">${esc(tr.name)}</text>`;
    const sp = Math.min(rh * 0.7, 4 * na) / Math.max(na - 1, 1);
    let tt = `<b>${esc(tr.full)}</b> (${esc(tr.area)}; quality ${esc(tr.qt.tier)}, ${tr.qt.p} pts; ECG relevance ${tr.ecg})<br>${esc(tr.ic)}<br>RCT: ${esc(tr.hr)}`;
    arms.forEach((a, k) => {
      const [l, se] = emuEst(rung, a, t); const yy = na > 1 ? yc - Math.min(rh * 0.7, 4 * na) / 2 + k * sp : yc;
      if (!fin(l)) { tt += `<br>${ARM[a].lab}: not estimable`; return; }
      s += `<line x1="${xs(l - 1.96 * se)}" x2="${xs(l + 1.96 * se)}" y1="${yy}" y2="${yy}" stroke="${ARM[a].col}" stroke-width="1.3" pointer-events="none"/>`;
      s += marker(ARM[a].mk, xs(l), yy, Math.max(2.2, Math.min(4.2, rh * 0.3)), ARM[a].col, ARM[a].hollow, `pointer-events="none"`);
      if (l < lo || l > hi) s += `<text x="${xs(l) + (l < lo ? -2 : 2)}" y="${yy + 3}" font-size="9" text-anchor="${l < lo ? "end" : "start"}" fill="${ARM[a].col}">${l < lo ? "◂" : "▸"}</text>`;
      const z = (l - tr.rb) / Math.sqrt(se * se + tr.rs * tr.rs);
      tt += `<br>${ARM[a].lab}: ${Math.exp(l).toFixed(2)} (${Math.exp(l - 1.96 * se).toFixed(2)}–${Math.exp(l + 1.96 * se).toFixed(2)}); |Δ log HR| ${Math.abs(l - tr.rb).toFixed(3)}; z ${z.toFixed(2)}`;
    });
    s += `<rect x="0" y="${y0}" width="${W}" height="${rh}" fill="transparent" data-tip="${esc(tt)}"/>`;
  });
  const yb = mt + ph;
  s += `<line x1="${ml}" x2="${W - mr}" y1="${yb}" y2="${yb}" stroke="${NAVY}"/>`;
  for (const v of [0.2, 0.25, 0.5, 1, 2, 4, 5]) s += `<line x1="${xs(Math.log(v))}" x2="${xs(Math.log(v))}" y1="${yb}" y2="${yb + 4}" stroke="${NAVY}"/><text x="${xs(Math.log(v))}" y="${yb + 16}" font-size="11" text-anchor="middle" fill="${NAVY}">${v}</text>`;
  s += `<text x="${(ml + W - mr) / 2}" y="${yb + 33}" font-size="12" text-anchor="middle" fill="${NAVY}">Hazard ratio (log scale; values beyond 0.2–5 marked ◂ ▸)</text>`;
  $("#emu-svg").innerHTML = s;
  /* summary */
  let h = `<h4>Selected set: ${T.length} trials</h4><table><tr><th>Method</th><th>mean |Δ|</th><th>r</th><th>est.</th><th>std.</th></tr>`;
  const cons = (a, t) => { const [l, se] = emuEst(rung, a, t); const tr = D.trials[t]; return fin(l) ? Math.abs((l - tr.rb) / Math.sqrt(se * se + tr.rs * tr.rs)) < 1.96 : null; };
  for (const a of arms) { const m = agree(est, rung, a, T);
    h += `<tr><td>${swatch(a)} ${ARM[a].lab}</td><td>${f3(m.gap)}</td><td>${f2(m.r)}</td><td>${pc(m.ea)}</td><td>${pc(m.sd)}</td></tr>`; }
  h += `</table>`;
  const cmp = arms.filter(a => a !== "base");
  if (arms.includes("base") && cmp.length && T.length > 1) {
    h += `<h4 style="margin-top:12px">vs PS alone (paired by trial)</h4><table><tr><th>Method</th><th>closer</th><th>sign-flip p</th><th>shuffle p</th></tr>`;
    for (const a of cmp) {
      const ok = T.filter(t => fin(emuEst(rung, a, t)[0]) && fin(emuEst(rung, "base", t)[0]));
      const d = ok.map(t => gap("base", t) - gap(a, t));
      const la = ok.map(t => emuEst(rung, a, t)[0]), lb = ok.map(t => emuEst(rung, "base", t)[0]), rb = ok.map(t => D.trials[t].rb);
      h += `<tr class="${a === "ECG" ? "hl" : ""}"><td>${ARM[a].lab}</td><td>${d.filter(x => x > 0).length}/${d.length}</td><td>${fmtp(signflip(d))}</td><td>${fmtp(benchShuffle(la, lb, rb, 2000))}</td></tr>`;
    }
    h += `</table><div class="note"><b>closer</b>: smaller |Δ log HR| than PS alone. <b>sign-flip p</b>: one-sided exact test on paired |Δ| reductions. <b>shuffle p</b>: RCT results randomly reassigned among the selected trials (2,000 draws); a large p means generic attenuation, not movement toward each trial's own result.</div>`;
  } else h += `<div class="note">Select "PS alone" and another method (and ≥2 trials) for paired tests.</div>`;
  h += `<div class="note">r: Pearson correlation of emulated vs RCT log HRs. est.: estimate agreement (emulated HR within the RCT 95% CI). std.: standardized-difference agreement (|z| &lt; 1.96 using both SEs). Counts are trials. p values unadjusted (exploratory).${est !== "itt" ? " Sensitivity analysis: trials without an estimate (procedure arms; run-in with too few patients kept; outpatient cohorts too small) are dropped." : ""}</div>`;
  $("#emu-sum").innerHTML = h;
}

/* =========================================================
   PANEL 3: plasmode explorer
   ========================================================= */
const SIMARMS = ["ECG", "shufECG", "noise32", "oracle"];
function simInit() {
  const sc = D.sim.scen.map((s, i) => i ? `<option value="${i}">OR ${s[0]} × HR ${s[1]}</option>` : "").join("");
  $("#sim-ctrl").innerHTML = `
  <label class="h">Simulation variant</label><select id="sim-var">${D.sim.variants.map((v, i) => `<option value="${i}">${esc(v.lab)}</option>`).join("")}</select>
  <label class="h">Hidden confounder</label><select id="sim-conf"><option value="all">All four</option>${Object.entries(CONFLAB).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}</select>
  <label class="h">Confounding strength</label><select id="sim-scen"><option value="grid">All 9 scenarios (pooled)</option>${sc}<option value="0">Null (OR 1, HR 1)</option></select>
  <label class="h">Arms (added to demographic PS)</label><div id="sim-arms">${armBoxes("sim-arm", SIMARMS, SIMARMS)}</div>
  <div class="xs" style="margin-top:10px">OR: treatment odds ratio per SD of C; HR: outcome hazard ratio per SD of C. Each point: one trial × confounder cell, pooled over the selected scenarios. y-axis clipped to −60 to 100 (clipped points drawn at the edge as triangles). Dashed line: % removed = 100 × R².</div>`;
  for (const id of ["sim-var", "sim-conf", "sim-scen"]) $("#" + id).onchange = simUpdate;
  $("#sim-arms").onchange = simUpdate;
  bindTips($("#sim-svg"));
  simUpdate();
}
function simUpdate() {
  const V = D.sim.variants[+$("#sim-var").value], conf = $("#sim-conf").value, scv = $("#sim-scen").value, arms = checked("sim-arm");
  const S = scv === "grid" ? [1, 2, 3, 4, 5, 6, 7, 8, 9] : [+scv];
  const cells = D.sim.cells.map((c, i) => ({...c, i})).filter(c => conf === "all" || c.c === conf);
  const nul = S.length === 1 && S[0] === 0;
  const sumB = (a, cs) => { let s = 0; for (const si of S) for (const c of cs) s += V.bias[a][si][c.i]; return s; };
  const prm = (a, cs) => nul ? NaN : 100 * (1 - sumB(a, cs) / sumB("base", cs));
  /* scatter */
  const W = 714, H = 590, ml = 58, mr = 28, mt = 28, mb = 48, x1 = 0.4, ylo = -60, yhi = 100;
  const xs = x => ml + Math.min(x1, Math.max(0, x)) / x1 * (W - ml - mr), ys = y => mt + (yhi - Math.min(yhi, Math.max(ylo, y))) / (yhi - ylo) * (H - mt - mb);
  let s = `<text x="${ml}" y="16" font-size="13" font-weight="700" fill="${NAVY}">% of PS-alone bias removed vs ECG partial R² for C (${cells.length} cells)</text>`;
  for (let y = -60; y <= 100; y += 20) s += `<line x1="${ml}" x2="${W - mr}" y1="${ys(y)}" y2="${ys(y)}" stroke="${y === 0 ? "#9a9cb0" : "#ececf1"}"/><text x="${ml - 6}" y="${ys(y) + 4}" font-size="11" text-anchor="end" fill="${NAVY}">${y}</text>`;
  for (let x = 0; x <= x1 + 1e-9; x += 0.1) s += `<line x1="${xs(x)}" x2="${xs(x)}" y1="${H - mb}" y2="${H - mb + 4}" stroke="${NAVY}"/><text x="${xs(x)}" y="${H - mb + 17}" font-size="11" text-anchor="middle" fill="${NAVY}">${x.toFixed(1)}</text>`;
  s += `<line x1="${ml}" x2="${W - mr}" y1="${H - mb}" y2="${H - mb}" stroke="${NAVY}"/><line x1="${ml}" x2="${ml}" y1="${mt}" y2="${H - mb}" stroke="${NAVY}"/>`;
  if (!nul) s += `<line x1="${xs(0)}" y1="${ys(0)}" x2="${xs(x1)}" y2="${ys(100 * x1)}" stroke="${NAVY}" stroke-dasharray="5 4" stroke-width="1.2"/><text x="${xs(x1) - 4}" y="${ys(100 * x1) - 6}" font-size="11" text-anchor="end" fill="${NAVY}">100 × R²</text>`;
  s += `<text x="${(ml + W - mr) / 2}" y="${H - 12}" font-size="12" text-anchor="middle" fill="${NAVY}">Partial R² of C on the ECG embedding, given demographics (real data, cross-fitted)</text>`;
  s += `<text transform="translate(16 ${(mt + H - mb) / 2}) rotate(-90)" font-size="12" text-anchor="middle" fill="${NAVY}">% of bias removed</text>`;
  if (!nul) {
    for (const a of arms) for (const c of cells) {
      const v = prm(a, [c]); if (!fin(v)) continue;
      const clip = v < ylo || v > yhi, x = xs(c.r2), y = ys(v);
      const tt = `<b>${esc(D.trials[c.t].name)} × ${CONFLAB[c.c]}</b><br>partial R² ${c.r2.toFixed(3)}<br>` + arms.map(b => `${ARM[b].lab}: ${f1(prm(b, [c]))}%`).join("<br>");
      s += clip ? `<path d="M${x} ${v > yhi ? y - 1 : y + 1}l4 ${v > yhi ? 7 : -7}h-8z" fill="${ARM[a].col}" data-tip="${esc(tt)}"/>` : marker(ARM[a].mk, x, y, 3.6, ARM[a].col, ARM[a].hollow, `data-tip="${esc(tt)}" fill-opacity="0.85"`);
    }
  } else s += `<text x="${(ml + W) / 2}" y="${ys(60)}" font-size="14" text-anchor="middle" fill="${NAVY}">Null scenario: no confounding by C, so % removed is undefined. See bias and coverage.</text>`;
  $("#sim-svg").innerHTML = s;
  /* summary */
  const showArms = ["base", ...arms];
  let h = `<h4>Pooled % of bias removed</h4>`;
  if (!nul) {
    const bw = 150, bx = v => 78 + (Math.max(-20, Math.min(100, v)) + 20) / 120 * bw, SL = {ECG: "ECG", shufECG: "Permuted", noise32: "Noise", oracle: "Oracle"};
    let b = `<svg width="286" height="${22 * arms.length + 22}"><line x1="${bx(0)}" x2="${bx(0)}" y1="2" y2="${22 * arms.length + 4}" stroke="#9a9cb0"/>`;
    arms.forEach((a, i) => { const v = prm(a, cells), y = 4 + i * 22;
      b += `<text x="74" y="${y + 12}" font-size="11" text-anchor="end" fill="${NAVY}">${SL[a]}</text>`;
      b += `<rect x="${Math.min(bx(0), bx(v))}" y="${y + 2}" width="${Math.abs(bx(v) - bx(0))}" height="14" fill="${ARM[a].col}"/>`;
      b += `<text x="${Math.max(bx(0), bx(v)) + 4}" y="${y + 13}" font-size="11.5" font-weight="700" fill="${NAVY}">${f1(v)}%</text>`; });
    for (const t of [0, 50, 100]) b += `<text x="${bx(t)}" y="${22 * arms.length + 18}" font-size="10" text-anchor="middle" fill="${NAVY}">${t}</text>`;
    h += b + `</svg>`;
  } else h += `<div class="note">Not defined under the null.</div>`;
  h += `<h4 style="margin-top:8px">Bias and 95% CI coverage</h4><table><tr><th>Arm</th><th>mean bias (log HR)</th><th>coverage %</th></tr>`;
  for (const a of showArms) { let sb = 0, sc = 0, n = 0; for (const si of S) for (const c of cells) { sb += V.bias[a][si][c.i]; sc += V.cov[a][si][c.i]; n++; }
    h += `<tr><td>${a === "base" ? swatch("base") + " PS alone" : swatch(a) + " " + ARM[a].lab}</td><td>${(sb / n).toFixed(3)}</td><td>${(sc / n).toFixed(1)}</td></tr>`; }
  h += `</table><div class="note">Pooled % removed = 100 × (1 − Σ bias<sub>arm</sub> / Σ bias<sub>PS alone</sub>) over the selected cells and scenarios. Coverage: mean over cells of the % of 50 replicates whose 95% CI contains the truth. True HR 0.80. Values are Monte Carlo summaries per cell.</div>`;
  if (V.code !== "asd") h += `<div class="note"><b>Post hoc variant.</b> ${V.code === "adv" ? "LVEF and eGFR sign-flipped so that higher C is clinically worse." : "Outcome depends on C and treatment only."}</div>`;
  $("#sim-sum").innerHTML = h;
}

/* =========================================================
   static schematics
   ========================================================= */
function box(x, y, w, h, txt, o) {
  o = o || {}; const fill = o.fill || "#fff", stroke = o.stroke || NAVY, col = o.col || NAVY, fs = o.fs || 17;
  const lines = txt.split("\n");
  let s = `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="${stroke}" stroke-width="${o.sw || 2}" ${o.dash ? `stroke-dasharray="${o.dash}"` : ""} rx="${o.rx || 0}"/>`;
  lines.forEach((l, i) => s += `<text x="${x + w / 2}" y="${y + h / 2 + (i - (lines.length - 1) / 2) * fs * 1.2 + fs * 0.35}" font-size="${fs}" text-anchor="middle" fill="${col}" font-weight="${o.bold ? 700 : 400}">${esc(l)}</text>`);
  return s;
}
function arrow(x1, y1, x2, y2, col, dash) {
  col = col || NAVY; const a = Math.atan2(y2 - y1, x2 - x1), L = 10;
  return `<line x1="${x1}" y1="${y1}" x2="${x2 - Math.cos(a) * 3}" y2="${y2 - Math.sin(a) * 3}" stroke="${col}" stroke-width="2" ${dash ? `stroke-dasharray="${dash}"` : ""}/>` +
    `<path d="M${x2} ${y2}L${x2 - L * Math.cos(a - 0.4)} ${y2 - L * Math.sin(a - 0.4)}L${x2 - L * Math.cos(a + 0.4)} ${y2 - L * Math.sin(a + 0.4)}Z" fill="${col}"/>`;
}
function ecgPath(x0, y0, w, beats, amp) {
  let d = `M${x0} ${y0}`; const bw = w / beats;
  for (let b = 0; b < beats; b++) { const x = x0 + b * bw, u = bw / 100;
    d += `L${x + 14 * u} ${y0}Q${x + 19 * u} ${y0 - amp * .15} ${x + 24 * u} ${y0}L${x + 30 * u} ${y0}L${x + 32 * u} ${y0 + amp * .12}L${x + 35 * u} ${y0 - amp}L${x + 38 * u} ${y0 + amp * .3}L${x + 40 * u} ${y0}L${x + 52 * u} ${y0}Q${x + 60 * u} ${y0 - amp * .32} ${x + 68 * u} ${y0}L${x + bw} ${y0}`; }
  return d;
}
function drawStatic() {
  /* RCT vs TTE */
  let s = `<text x="290" y="24" font-size="24" font-weight="700" text-anchor="middle" fill="${NAVY}">RCT</text><text x="890" y="24" font-size="24" font-weight="700" text-anchor="middle" fill="${NAVY}">Target trial emulation</text>`;
  s += box(170, 44, 240, 50, "Eligible population") + arrow(290, 94, 290, 132) + `<text x="302" y="120" font-size="15" fill="${RED}" font-style="italic">randomization</text>`;
  s += box(140, 134, 140, 46, "Treatment", {fill: NAVY, col: "#fff"}) + box(300, 134, 140, 46, "Control", {fill: NAVY, col: "#fff"});
  s += arrow(210, 180, 270, 222) + arrow(370, 180, 310, 222) + box(170, 224, 240, 50, "Causal effect", {bold: true});
  s += `<text x="290" y="310" font-size="16" text-anchor="middle" fill="${NAVY}"><tspan font-style="italic">ceteris paribus</tspan>: all other things being equal</text>`;
  s += `<line x1="592" x2="592" y1="10" y2="330" stroke="${"#dcdde5"}" stroke-width="2"/>`;
  s += box(730, 44, 320, 50, "Real-world data (EHR, registry, claims)", {fs: 16}) + arrow(890, 94, 890, 112);
  s += box(770, 114, 240, 40, "Eligibility criteria", {fs: 16}) + arrow(890, 154, 890, 172);
  s += box(730, 174, 320, 44, "PS matching on measured confounders", {fs: 16, stroke: RED}) + arrow(840, 218, 800, 240) + arrow(940, 218, 980, 240);
  s += box(700, 242, 180, 46, "Treatment received", {fill: NAVY, col: "#fff", fs: 16}) + box(900, 242, 180, 46, "Control received", {fill: NAVY, col: "#fff", fs: 16});
  s += `<text x="890" y="316" font-size="16" text-anchor="middle" fill="${NAVY}">specify the trial protocol, emulate it in routine-care data</text>`;
  $("#svg-rct").innerHTML = s;
  /* PSM problem */
  s = `<text x="225" y="24" font-size="19" font-weight="700" text-anchor="middle" fill="${NAVY}">Treated</text><text x="475" y="24" font-size="19" font-weight="700" text-anchor="middle" fill="${NAVY}">Comparator</text>`;
  s += `<text x="0" y="112" font-size="15" fill="${NAVY}" font-weight="700">structured</text>`;
  s += box(125, 44, 200, 130, "Demographics\nDiagnoses\nPrescriptions\n…", {fs: 16}) + box(375, 44, 200, 130, "Demographics\nDiagnoses\nPrescriptions\n…", {fs: 16});
  s += `<text x="350" y="120" font-size="34" text-anchor="middle" fill="${NAVY}">=</text>`;
  s += `<text x="0" y="274" font-size="15" fill="${RED}" font-weight="700">unmeasured</text>`;
  s += box(125, 206, 200, 150, "LV function\nCongestion\nAtrial substrate\nConduction", {fs: 16, fill: RED, col: "#fff", stroke: RED}) + box(375, 206, 200, 150, "LV function\nCongestion\nAtrial substrate\nConduction", {fs: 16, fill: RED, col: "#fff", stroke: RED});
  s += `<text x="350" y="292" font-size="34" text-anchor="middle" fill="${RED}">?</text>`;
  s += `<text x="350" y="396" font-size="15" text-anchor="middle" fill="${NAVY}">The PS balances the top row; the bottom row is not guaranteed.</text>`;
  $("#svg-psm").innerHTML = s;
  /* ECG pipeline */
  s = `<rect x="0" y="30" width="330" height="170" fill="#fff" stroke="${NAVY}" stroke-width="2"/>`;
  for (let r = 0; r < 3; r++) s += `<path d="${ecgPath(12, 75 + r * 50, 306, 3, 32)}" fill="none" stroke="${RED}" stroke-width="2"/>`;
  s += `<text x="165" y="226" font-size="16" text-anchor="middle" fill="${NAVY}">Raw 12-lead ECG (≤365 d before index)</text>`;
  s += arrow(340, 115, 400, 115) + box(405, 60, 250, 110, "Self-supervised\nECG encoder (BCL,\nsignal model)", {fill: NAVY, col: "#fff", fs: 16});
  s += arrow(660, 115, 720, 115);
  for (let i = 0; i < 16; i++) s += `<rect x="${728 + i * 13}" y="95" width="11" height="40" fill="${NAVY}" fill-opacity="${0.25 + 0.7 * Math.abs(Math.sin(i * 1.7))}"/>`;
  s += `<text x="832" y="160" font-size="15" text-anchor="middle" fill="${NAVY}">256-d embedding → 32 PCs</text>`;
  s += arrow(945, 115, 1000, 115) + box(1005, 70, 175, 90, "Added to\nthe PS", {fs: 17, bold: true, stroke: RED});
  $("#svg-ecg").innerHTML = s;
  /* trials */
  s = box(0, 20, 215, 90, "99 candidate\ncardiovascular RCTs", {fs: 17, bold: true}) + arrow(220, 65, 258, 65);
  s += `<rect x="262" y="0" width="460" height="200" fill="#f5f5f8" stroke="none"/>`;
  const crit = ["Active comparator (or accepted active proxy)", "Primary endpoint ascertainable from EHR", "Strategies identifiable from orders or procedures", "≥300 with an ECG in the smaller arm", "≥50 primary-outcome events", "No near-duplicate cohort (>80% shared records)"];
  crit.forEach((c, i) => s += `<text x="276" y="${30 + i * 30}" font-size="16" fill="${NAVY}">– ${esc(c)}</text>`);
  s += arrow(728, 65, 768, 65) + box(772, 20, 140, 90, "38\nemulated", {fs: 20, bold: true});
  s += arrow(842, 114, 842, 150) + box(772, 154, 140, 90, "32\nanalysed", {fs: 20, bold: true, fill: NAVY, col: "#fff"});
  const lim = D.trials.filter(t => t.qt.tier === "Limited").map(t => t.name);
  s += `<text x="832" y="130" font-size="13" text-anchor="end" fill="${RED}">− ${lim.length} limited</text><text x="832" y="145" font-size="13" text-anchor="end" fill="${RED}">quality</text>`;
  s += `<text x="0" y="275" font-size="14" fill="${NAVY}">Excluded for limited emulation quality (≥4 design points): ${esc(lim.join(", "))}.</text>`;
  const AR6 = ["AF", "Diabetes", "HF", "Hypertension", "ACS / MI", "Other"];
  const n38 = a => D.trials.filter(t => t.area === a).length, n32 = a => D.trials.filter(t => t.area === a && t.qt.tier !== "Limited").length;
  AR6.forEach((a, i) => { const y = 24 + i * 29, A = n38(a), B = n32(a);
    s += `<text x="1032" y="${y + 15}" font-size="15" text-anchor="end" fill="${NAVY}">${a}</text><rect x="1040" y="${y + 2}" width="${A * 8}" height="18" fill="#c9cbd8"/><rect x="1040" y="${y + 2}" width="${B * 8}" height="18" fill="${a === "AF" ? RED : NAVY}"/><text x="${1046 + A * 8}" y="${y + 16}" font-size="14" fill="${NAVY}">${B}${A !== B ? " / " + A : ""}</text>`; });
  s += `<text x="1040" y="-4" font-size="14" font-weight="700" fill="${NAVY}">Clinical area</text><text x="1040" y="12" font-size="12" fill="${NAVY}">analysed / emulated</text>`;
  $("#svg-trials").innerHTML = s;
  /* emulation quality */
  (function () {
    /* v1.9 graded tiers (docs/v19/quality_tiers.json; design items only, blind to results) */
    const G = [["Excellent", "close emulation", "0 points"], ["Good", "minor deviations", "1–2 points"],
      ["Moderate", "substantial deviations", "3 points, or capped"], ["Limited", "major deviations", "≥4 points"]];
    const TI = Object.fromEntries(G.map(([t], i) => [t, i]));
    const byTier = (a, b) => TI[a.qt.tier] - TI[b.qt.tier] || a.qt.p - b.qt.p || a.area.localeCompare(b.area) || a.name.localeCompare(b.name);
    let h = "";
    G.forEach(([t, lab, d]) => {
      const T = D.trials.filter(x => x.qt.tier === t).sort(byTier);
      h += `<div><h4>${t} — ${lab} (${T.length})<br><span class="d">${d}</span></h4><table>` +
        T.map(x => `<tr><td class="n">${esc(x.name)}</td><td>${esc(x.area)}</td><td class="p">${x.qt.p}</td></tr>`).join("") + `</table></div>`;
    });
    $("#qual-grid").classList.add("q4");
    $("#qual-grid").innerHTML = h;
    const nc = c => D.trials.filter(x => x.qt.cls === c).length, no = q => D.trials.filter(x => x.qual === q).length;
    $("#qual-cls").textContent = `Original 3-class rule, after re-audit: ${nc("High (strict)")} high (strict), ${nc("High")} high, ${nc("Lower")} lower ` +
      `(v1.7: ${no("strict")} / ${no("high")} / ${no("lower")}; changed: ` +
      D.trials.filter(x => QUAL[x.qual] !== x.qt.cls).map(x => `${x.name} ${QUAL[x.qual].toLowerCase()} → ${x.qt.cls.toLowerCase()}`).join(", ") + `). Right column: points.`;
    $("#qual-count").textContent = "Emulation quality (design items only): " + G.map(([t]) => `${D.trials.filter(x => x.qt.tier === t).length} ${t.toLowerCase()}`).join(", ") + " (next slides).";
    /* item-level breakdown: two side-by-side tables sorted by tier */
    const S = D.trials.slice().sort(byTier), half = Math.ceil(S.length / 2);
    const tab = R => `<table><tr><th class="l">Trial</th><th class="l">Area</th><th>F1</th><th>F2</th><th>F3</th><th>F4</th><th>F5</th><th>Comp.</th><th>Outc.</th><th>Pts</th><th class="l">Tier</th></tr>` +
      R.map((x, i) => `<tr${i && R[i - 1].qt.tier !== x.qt.tier ? ' class="tb"' : ""}><td class="l n">${esc(x.name)}</td><td class="l">${esc(x.area)}</td>` +
        x.qt.f.map(v => `<td>${v ? "✓" : ""}</td>`).join("") + `<td class="${x.qt.c}">${x.qt.c}</td><td class="${x.qt.o}">${x.qt.o}</td>` +
        `<td class="pt">${x.qt.p}</td><td class="l"><span class="tier t${TI[x.qt.tier]}">${x.qt.tier}</span></td></tr>`).join("") + `</table>`;
    $("#qual-items").innerHTML = `<div>${tab(S.slice(0, half))}</div><div>${tab(S.slice(half))}</div>`;
  })();
  /* ladder */
  const L = [["P1", "Demographics: age, sex, index year", "primary"], ["P5", "+ 5 diagnoses: HTN, T2D, CAD, AF, HF", ""], ["P2", "+ obesity", ""],
    ["Sparse", "Demographics + 9–13 CV diagnoses (prior year)", ""], ["hdPS", "+ 200 codes most associated with treatment", ""], ["Clinical", "+ vitals, labs, LVEF, meds, healthcare use", ""]];
  s = `<text x="0" y="18" font-size="15" font-weight="700" fill="${NAVY}">PS specification (structured data, thin → rich)</text>`;
  L.forEach(([k, t, tag], i) => { const y = 30 + i * 62, x = i * 26;
    s += `<rect x="${x}" y="${y}" width="${600 - x}" height="52" fill="${NAVY}" fill-opacity="${0.12 + i * 0.14}"/><text x="${x + 12}" y="${y + 32}" font-size="17" font-weight="700" fill="${i > 2 ? "#fff" : NAVY}">${k}</text><text x="${x + 100}" y="${y + 32}" font-size="15" fill="${i > 2 ? "#fff" : NAVY}">${esc(t)}</text>`;
    if (tag) s += `<text x="${600 - 10}" y="${y + 32}" font-size="13" text-anchor="end" font-weight="700" fill="${RED}">${tag}</text>`; });
  s += arrow(610, 205, 660, 205);
  s += `<text x="670" y="18" font-size="15" font-weight="700" fill="${NAVY}">Arms at every rung</text>`;
  const AR = [["PS alone", "reference", NAVY, false], ["+ ECG", "32 PCs of a 256-d BCL signal-model embedding", RED, false], ["+ permuted ECG", "placebo: embeddings shuffled between patients", "#d69a00", true],
    ["+ noise", "placebo: independent Gaussian columns", "#7a6a58", true], ["+ CLMBR-T", "exploratory comparator: structured-EHR foundation model, 64 PCs", "#2a78d6", false], ["+ CLMBR-T + ECG", "exploratory comparator", "#1baf7a", false]];
  AR.forEach(([a, t, c, hol], i) => { const y = 30 + i * 62;
    s += `<rect x="670" y="${y}" width="514" height="52" fill="#fff" stroke="${c}" stroke-width="2" ${hol ? 'stroke-dasharray="6 4"' : ""}/><text x="684" y="${y + 22}" font-size="16" font-weight="700" fill="${NAVY}">${a}</text><text x="684" y="${y + 42}" font-size="13.5" fill="${NAVY}">${esc(t)}</text>`; });
  $("#svg-ladder").innerHTML = s;
  /* domain table (method 1) */
  const cnt = {}; D.vars.forEach(v => cnt[v.g] = (cnt[v.g] || 0) + 1);
  const ex = {"Coded record": "medications, healthcare use, other codes, prognostic score", "Vitals & core labs": "LVEF, BP, heart rate, BMI, creatinine, K, Na, Hb", "Other labs": "NT-proBNP, eGFR, HbA1c, troponin, LDL, …"};
  let tb = `<tr><th>Held-out domain</th><th>n</th></tr>`;
  let echo = 0; for (const [g, n] of Object.entries(cnt)) { if (g.startsWith("Echo")) { echo += n; continue; } tb += `<tr><td>${g}<br><span class="small">${ex[g] || ""}</span></td><td>${n}</td></tr>`; }
  tb += `<tr><td>Echocardiography<br><span class="small">LV structure and function, diastolic / LA, RV / pulmonary, valves / aorta</span></td><td>${echo}</td></tr><tr><td><b>Total</b></td><td><b>${D.vars.length}</b></td></tr>`;
  $("#tab-domains").innerHTML = tb;
  const bc = {}; D.exp.vars.forEach(v => bc[v.b] = (bc[v.b] || 0) + 1);
  let tb2 = `<tr><th>Expanded panel bucket</th><th>n</th></tr>`; for (const b of D.exp.buckets) if (bc[b]) tb2 += `<tr><td>${esc(b)}</td><td>${bc[b]}</td></tr>`;
  $("#tab-buckets").innerHTML = tb2 + `<tr><td><b>Total (union across trials)</b></td><td><b>${D.exp.vars.length}</b></td></tr>`;
  /* shuffle schematic */
  s = `<text x="0" y="20" font-size="16" font-weight="700" fill="${NAVY}">Benchmark shuffle</text>`;
  const tr = [["Trial A", "0.79"], ["Trial B", "1.15"], ["Trial C", "0.66"], ["Trial D", "1.02"]], sh = [2, 3, 0, 1];
  tr.forEach(([n, h], i) => { const y = 50 + i * 70;
    s += box(0, y, 110, 44, n, {fs: 15}) + box(300, y, 120, 44, "RCT " + tr[sh[i]][1], {fs: 15, stroke: RED}) + `<line x1="112" y1="${y + 22}" x2="296" y2="${50 + sh.indexOf(i) * 70 + 22}" stroke="#c9cad4"/>` + arrow(112, y + 22, 296, y + 22, "#c9cad4", "4 4"); });
  s += `<text x="0" y="345" font-size="14" fill="${NAVY}">Recompute the |Δ| reduction against</text><text x="0" y="365" font-size="14" fill="${NAVY}">wrong benchmarks, many times.</text><text x="0" y="390" font-size="14" fill="${RED}">Observed gain must beat this null.</text>`;
  $("#svg-shuffle").innerHTML = s;
  /* plasmode */
  s = box(0, 30, 250, 110, "Real cohort\ncovariates, ECGs,\nfollow-up kept", {fs: 17});
  s += arrow(255, 85, 300, 85) + box(305, 30, 250, 110, "Simulate treatment\nfrom demographics + C", {fs: 17, fill: NAVY, col: "#fff"});
  s += arrow(560, 85, 605, 85) + box(610, 30, 250, 110, "Simulate outcome\ntrue HR = 0.80\n+ effect of C", {fs: 17, fill: NAVY, col: "#fff"});
  s += arrow(865, 85, 910, 85) + box(915, 30, 265, 110, "PS without C (± ECG)\nmatch, estimate HR\nbias = estimate − truth", {fs: 16, stroke: RED});
  /* DAG */
  s += box(470, 200, 190, 44, "C (e.g., LVEF)", {fs: 16, stroke: RED, dash: "6 4", bold: true});
  s += box(250, 270, 150, 44, "Treatment", {fs: 16}) + box(730, 270, 150, 44, "Outcome", {fs: 16});
  s += arrow(500, 244, 400, 274, RED) + arrow(630, 244, 730, 274, RED) + arrow(400, 292, 728, 292) + `<text x="565" y="286" font-size="14" text-anchor="middle" fill="${NAVY}">HR 0.80 (known)</text>`;
  s += box(960, 200, 170, 44, "ECG embedding", {fs: 16}) + arrow(662, 222, 956, 222, "#8a8ca0", "5 4") + `<text x="810" y="214" font-size="13" text-anchor="middle" fill="${NAVY}">encodes part of C (R²)</text>`;
  s += `<text x="20" y="232" font-size="14" fill="${RED}">C is hidden from every PS</text><text x="20" y="252" font-size="14" fill="${RED}">(except the oracle arm)</text>`;
  $("#svg-plasmode").innerHTML = s;
}

/* =========================================================
   deck mechanics
   ========================================================= */
const slides = [...document.querySelectorAll(".slide")];
slides.forEach((sl, i) => {
  if (!sl.dataset.title) return;
  sl.insertAdjacentHTML("afterbegin", `<div class="ttl">${sl.dataset.title}</div><div class="num">${i + 1}</div><div class="foot"><b>CarDS</b>LAB</div><img class="logo" alt="" src="${LOGO}">`);
});
let cur = 0;
function show(i) {
  cur = Math.max(0, Math.min(slides.length - 1, i));
  slides.forEach((s, k) => s.classList.toggle("active", k === cur));
  $("#nav-count").textContent = `${cur + 1} / ${slides.length}`;
  tip.style.display = "none";
  if (location.hash !== "#" + (cur + 1)) history.replaceState(null, "", "#" + (cur + 1));
}
function fit() { const s = Math.min(innerWidth / 1280, innerHeight / 720); $("#stage").style.transform = `translate(-50%,-50%) scale(${s})`; }
addEventListener("resize", fit);
addEventListener("keydown", e => {
  const tag = (e.target.tagName || "").toLowerCase(), inForm = tag === "select" || tag === "input";
  if (e.key === "PageDown" || (!inForm && (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === " "))) { e.preventDefault(); if (inForm) e.target.blur(); show(cur + 1); }
  else if (e.key === "PageUp" || (!inForm && (e.key === "ArrowLeft" || e.key === "ArrowUp"))) { e.preventDefault(); if (inForm) e.target.blur(); show(cur - 1); }
  else if (!inForm && e.key === "Home") show(0);
  else if (!inForm && e.key === "End") show(slides.length - 1);
  else if (!inForm && (e.key === "f" || e.key === "F")) { if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); else document.exitFullscreen(); }
});
$("#nav-prev").onclick = () => show(cur - 1);
$("#nav-next").onclick = () => show(cur + 1);
/* ---------- agreement by emulation quality ---------- */
const SPLITS = {tier2: ["Excellent + Good", t => ["Excellent", "Good"].includes(TIER(t)), "Moderate + Limited"],
  tier3: null, cls: ["High fidelity (3-class)", t => t.qt.cls !== "Lower", "Lower fidelity (3-class)"]};
function agqInit() {
  const sel = (id, opts) => `<select id="${id}">${opts}</select>`;
  $("#agq-ctrl").innerHTML = `
  <label class="h">Analysis</label>${sel("agq-est", $("#emu-est").innerHTML)}
  <label class="h">PS base</label>${rungSel("agq-rung")}
  <label class="h">Methods</label>
  <div id="agq-arms">${armBoxes("agq-arm", ["base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG"], ["base", "ECG"])}</div>
  <label class="h">Quality groups</label>${sel("agq-split", `<option value="tier2">Excellent + Good vs Moderate + Limited</option><option value="tier3">Excellent + Good vs Moderate vs Limited</option><option value="tier4">All four tiers</option><option value="cls">3-class rule: High vs Lower</option>`)}
  <label class="h">Metric plotted</label>${sel("agq-met", `<option value="sd">Standardized-difference agreement</option><option value="ea">Estimate agreement</option><option value="r">Pearson r</option>`)}`;
  for (const id of ["agq-est", "agq-rung", "agq-split", "agq-met"]) $("#" + id).onchange = agqUpdate;
  $("#agq-arms").onchange = agqUpdate;
  agqUpdate();
}
function agqGroups(v) {
  const idx = D.trials.map((_, i) => i);
  if (v === "tier2") return [["Excellent + Good", idx.filter(i => ["Excellent", "Good"].includes(TIER(D.trials[i])))], ["Moderate + Limited", idx.filter(i => ["Moderate", "Limited"].includes(TIER(D.trials[i])))]];
  if (v === "tier3") return [["Excellent + Good", idx.filter(i => ["Excellent", "Good"].includes(TIER(D.trials[i])))], ["Moderate", idx.filter(i => TIER(D.trials[i]) === "Moderate")], ["Limited", idx.filter(i => TIER(D.trials[i]) === "Limited")]];
  if (v === "tier4") return ["Excellent", "Good", "Moderate", "Limited"].map(q => [q, idx.filter(i => TIER(D.trials[i]) === q)]);
  return [["High fidelity", idx.filter(i => D.trials[i].qt.cls !== "Lower")], ["Lower fidelity", idx.filter(i => D.trials[i].qt.cls === "Lower")]];
}
function agqUpdate() {
  const est = $("#agq-est").value;
  $("#agq-rung").querySelectorAll("option").forEach(o => { o.disabled = est !== "itt" && !["P1", "P5"].includes(o.value); });
  if (est !== "itt" && !["P1", "P5"].includes($("#agq-rung").value)) $("#agq-rung").value = "P1";
  const avail = est === "itt" ? ["base", "ECG", "CLMBR", "CLMBR+ECG", "shufECG"] : ["base", "ECG", "shufECG"];
  document.querySelectorAll("#agq-arms .cb").forEach(l => { const ok = avail.includes(l.dataset.arm); l.classList.toggle("dis", !ok); l.querySelector("input").disabled = !ok; });
  const rung = $("#agq-rung").value, arms = checked("agq-arm").filter(a => avail.includes(a)), G = agqGroups($("#agq-split").value), met = $("#agq-met").value;
  const R = G.map(([g, T]) => [g, T, arms.map(a => agree(est, rung, a, T))]);
  /* grouped bars */
  const W = 714, H = 330, ml = 50, mb = 44, mt = 24, pw = W - ml - 10, ph = H - mt - mb;
  const lo = met === "r" ? -0.5 : 0, hi = 1.1, ys = v => mt + ph - (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo) * ph;
  let s = `<text x="${ml}" y="14" font-size="13" font-weight="700" fill="${NAVY}">${$("#agq-met").selectedOptions[0].text} by emulation quality (${RSHORT[rung]}; ${esc($("#agq-est").selectedOptions[0].text)})</text>`;
  for (let v = lo; v <= 1 + 1e-9; v += met === "r" ? 0.25 : 0.2) s += `<line x1="${ml}" x2="${W - 10}" y1="${ys(v)}" y2="${ys(v)}" stroke="#ececf1"/><text x="${ml - 6}" y="${ys(v) + 4}" font-size="11" text-anchor="end" fill="${NAVY}">${met === "r" ? v.toFixed(2) : Math.round(v * 100) + "%"}</text>`;
  const gw = pw / R.length, bw = Math.min(46, (gw - 30) / Math.max(arms.length, 1));
  R.forEach(([g, T, M], gi) => {
    const x0 = ml + gi * gw + (gw - bw * arms.length) / 2;
    M.forEach((m, k) => { const v = m[met]; if (!fin(v)) return; const x = x0 + k * bw, y = ys(v), y0 = ys(Math.max(0, lo));
      s += `<rect x="${x + 3}" y="${Math.min(y, y0)}" width="${bw - 6}" height="${Math.abs(y0 - y)}" fill="${ARM[arms[k]].col}"/><text x="${x + bw / 2}" y="${Math.min(y, y0) - 4}" font-size="11" text-anchor="middle" fill="${NAVY}">${met === "r" ? v.toFixed(2) : Math.round(v * 100)}</text>`; });
    s += `<text x="${ml + gi * gw + gw / 2}" y="${H - mb + 18}" font-size="13" text-anchor="middle" font-weight="700" fill="${NAVY}">${esc(g)} (${T.length})</text>`;
  });
  $("#agq-svg").innerHTML = s;
  let h = `<table class="t" style="margin-top:6px"><tr><th>Group</th><th>Method</th><th>n</th><th>r</th><th>Estimate agr.</th><th>Std-diff agr.</th><th>mean |Δ|</th></tr>`;
  R.forEach(([g, T, M]) => M.forEach((m, k) => h += `<tr><td>${k ? "" : esc(g)}</td><td>${swatch(arms[k])} ${ARM[arms[k]].lab}</td><td>${m.n}</td><td>${f2(m.r)}</td><td>${pc(m.ea)}</td><td>${pc(m.sd)}</td><td>${f3(m.gap)}</td></tr>`));
  $("#agq-tab").innerHTML = h + `</table>`;
  $("#agq-note").innerHTML = `<h4>Metrics (as RCT-DUPLICATE)</h4><div class="note"><b>r</b>: Pearson correlation of emulated vs RCT log HRs across trials.<br><b>Estimate agreement</b>: emulated HR inside the RCT 95% CI.<br><b>Std-diff agreement</b>: |z| &lt; 1.96 using both SEs.<br><b>mean |Δ|</b>: mean |log HR − RCT log HR|.</div><div class="note">Groups are descriptive (design items, blind to results); small groups give unstable r. No multiplicity adjustment.</div>`;
}

drawStatic(); balInit(); emuInit(); agqInit(); simInit(); fit();
show((parseInt(location.hash.slice(1), 10) || 1) - 1);
</script>
</body>
</html>
'''


if __name__ == "__main__":
    main()
