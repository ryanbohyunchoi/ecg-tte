#!/usr/bin/env python
"""Build the CarDS Lab TRACE-ECG update deck (2026-10-09): docs/presentation/ecg_tte_lab_2026_10_09.html.

Modelled on the 2026-10-01 deck (scripts/build_lab_deck.py, not modified): same stage, title bar, footer, logo and slide
mechanics. Scope changes since 2026-10-01 (pipeline.md): ECG-only paper (no CLMBR-T, no UK Biobank); primary = PS-CVD5 + ECG vs
PS-CVD5, fixed L2 C = 1, 1:1 caliper 0.2, 54 leakage-corrected non-coded items (58 secondary); PS-Clinical without LVEF with
5-draw multiple imputation; ladder PS-Demo -> PS-CVD5 -> PS-CVD10 -> hdPS -> PS-Clinical (no LVEF), PS-Flags supplement only;
spec-v2 fixed cohorts by default (version 1 toggle); trial set = the rescored 30-trial analysed set (provisional, not frozen).

Self-contained HTML (inline CSS/JS/SVG, vector logo as a data URI, no network resources). Embeds AGGREGATE data only:
per-trial |SMD| per held-out item (integers x 1e5, as the 2026-10-08 balance explorer), per-trial matched log HR and SE, the RCT
log HR and SE, trial names / area / quality tiers and totals. No patient-level rows, no identifiers, no n, n_pairs, retention or
ESS, no event counts.

Interactive slides:
  * balance explorer: the JS of scripts/build_balance_explorer.py (imported, sliced and patched; its statistics code - exact
    sign-flip, numpy PCG64 bootstrap - is used unchanged), restricted to the ECG arms and the pipeline.md rungs;
  * trial emulation explorer and agreement by emulation quality: adapted from the 2026-10-01 deck, on the spec-v2 cells.
Data loading is build_balance_explorer.load_grid / load_grid_v2 (validated there against every source).

Static numbers: every number on slides 2-15 is computed here from a source file and recorded in a claims table
(audits/claude-lab-deck-v2/claims.csv: claim -> source -> value -> independent check -> match).

Usage (tte-analysis env):
  python scripts/build_lab_deck_v2.py           build the HTML, claims table and validation combos (audits/claude-lab-deck-v2)
"""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_balance_explorer as BE  # noqa: E402
from build_lab_deck import logo_uri, _forest, _legend  # noqa: E402
from make_acc_figure import VARS  # noqa: E402

A = BE.A
OUT = ROOT / "docs/presentation/ecg_tte_lab_2026_10_09.html"
SCR = A / "claude-lab-deck-v2"
QV2C = ROOT / "docs/emulation_quality_v2/quality_v2_cohorts.json"
QFRAME = ROOT / "docs/emulation_quality_v2/QUALITY_FRAMEWORK.md"
QADJ = ROOT / "docs/emulation_quality_v2/ADJUDICATION.md"
QRES = ROOT / "docs/emulation_quality_v2/RESCORE_V2_COHORTS.md"
QAUD = ROOT / "docs/emulation_quality_v2/AUDIT_QUALITY_V2.md"
QT19 = ROOT / "docs/v19/quality_tiers.json"
QUEUE = ROOT / "docs/queue/QUEUE_2026_10_08_RESULTS.md"
PIPE = ROOT / "pipeline.md"
HAND = ROOT / "handoff.md"
FIXD = ROOT / "docs/v2_cohorts/COHORT_FIXES.md"
MID = ROOT / "docs/v2_psclin_mi/PS_CLINICAL_MI.md"
PLD = ROOT / "docs/v21/PLASMODE_PAPER2.md"
MMD = ROOT / "docs/v21/MIMIC_PAPER2.md"
DEFI = ROOT / "docs/v1_audit/DEFECT_IMPACT.md"
V2SUM, MISUM = BE.V2SUM, BE.MISUM
IMPACT = A / "claude-eq2-v2cohorts/impact_v2cohorts.csv"
EXCL = A / "claude-v2-cohorts/flags/exclusions_by_trial.csv"
RRS = V2SUM / "random_removal_summary.csv"
PLAS = A / "claude-v21-paper2/plasmode"
MIM = A / "claude-v21-paper2/mimic"

RUNGS_D = ["P1", "P5", "PS10", "Flags", "hdPS200", "clinical_nolvef"]
ARMS_D = ["base", "ECG", "shufECG"]
CFGS = BE.CFGS
ITEMS = ["EL", "TZ", "TS", "CO", "OU", "FU", "ES", "BM", "DA", "SI"]
TIERS = ["Excellent", "Good", "Moderate", "Limited"]
# summary-set names -> deck trial-set values (tier filters use the rescored spec-v2 tiers)
SETMAP = {"Snew": "v2c", "SEG": "q:Excellent,Good", "S29": "v2", "S32": "s32", "S38": "all"}
NAVY, RED, GOLD, GREY = "#0E103C", "#DC5A55", "#d69a00", "#8a8d99"
MINUS = "−"


# ================================================================ formatting and the claims table
def fx(x, d=1):
    t = f"{x:.{d}f}"
    if re.fullmatch(r"-0\.?0*", t):
        t = t[1:]
    return t.replace("-", MINUS)


def ci(e, lo, hi, d=1):
    return f"{fx(e, d)}% ({fx(lo, d)} to {fx(hi, d)})"


def fp(p):
    """static-slide P: <.001; 3 decimals below .1; else 2 decimals."""
    return "<.001" if p < 0.001 else (f"{p:.3f}"[1:] if p < 0.1 else f"{p:.2f}"[1:] if p < 0.995 else f"{p:.2f}")


def pv(p):
    s = fp(p)
    return "P < .001" if s == "<.001" else f"P = {s}"


def norm(s):
    return (str(s).replace("−", "-").replace("–", "-").replace("—", "-").replace(" ", " ").replace("**", "")
            .replace("\\|", "|").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))


_DOC = {}


def doc(p):
    p = Path(p)
    if p not in _DOC:
        _DOC[p] = norm(p.read_text())
    return _DOC[p]


def rel(p):
    p = Path(p)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p).replace(str(A) + "/", "audits/")


CL = []


def claim(slide, what, shown, src, probe=None, ref_src=None, ref=None, ref_how=None):
    """Register a static number. shown = text on the slide (computed from src). Independent check: either probe (a string expected
    verbatim, after normalising minus signs and dashes, in ref_src) or ref (a value recomputed from another source; equal after
    formatting)."""
    if probe is not None:
        ok, how = norm(probe) in doc(ref_src), f"text '{probe}' in {rel(ref_src)}"
    elif ref is not None:
        ok, how = norm(ref) == norm(shown), f"{ref_how}: {ref}"
    else:
        ok, how = None, "definition (no independent copy)"
    CL.append(dict(slide=slide, claim=what, value=norm(shown), source=rel(src) if isinstance(src, Path) else src, check=how, match=ok))
    return shown


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ================================================================ data
def load_md_table(path, header_start):
    """rows of the first markdown table whose header line starts with header_start."""
    lines = Path(path).read_text().splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith(header_start))
    hdr = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    rows = []
    for l in lines[i + 2:]:
        if not l.startswith("|"):
            break
        rows.append(dict(zip(hdr, [c.strip() for c in l.strip().strip("|").split("|")])))
    return rows


def trials_deck(g, g2):
    base = BE.trials_meta(g)  # id, name, full, area, tier (v19), s32, phys, v2 (29), v2c (rescored 30)
    Q = json.load(open(QV2C))
    R = {r["trial"]: r for r in Q["records"]}
    rb = g2["R"][(g2["R"].rung == "P5") & (g2["R"].config == "main") & (g2["R"].arm == "base")].set_index("trial").loc[g["tids"]]
    rb1 = g["R"][(g["R"].rung == "P5") & (g["R"].config == "main") & (g["R"].arm == "base")].set_index("trial").loc[g["tids"]]
    assert np.allclose(rb.rb, rb1.rb) and np.allclose(rb.rs, rb1.rs)  # RCT benchmark identical in both cohort versions
    for R_ in (g["R"], g2["R"]):  # one benchmark per trial in every cell
        assert (R_.groupby("trial").rb.nunique() == 1).all() and (R_.groupby("trial").rs.nunique() == 1).all()
    out = []
    for t, (_, x) in zip(base, rb.iterrows()):
        r = R[t["full"]]
        assert r["analysed_set"] == t["v2c"] and r["tier"] in TIERS
        out.append(dict(id=t["id"], name=t["name"], full=t["full"], area=t["area"], tier=r["tier"], tq1=r["tier_v1_cohorts"], t19=t["tier"],
                        tot=r["total"], tot1=r["total_v1_cohorts"], it=[r["items"][i]["score"] for i in ITEMS],
                        prov=bool(r["tier_changing_provisional_items"]), s32=t["s32"], v2=t["v2"], v2c=t["v2c"], phys=t["phys"],
                        rb=round(float(x.rb), 6), rs=round(float(x.rs), 6)))
    assert sum(t["v2c"] for t in out) == 30 and sum(t["v2"] for t in out) == 29 and sum(t["s32"] for t in out) == 32
    return out, Q


def est_block(gx):
    """per (config, rung, arm): [[log HR, SE] or None] in trial order; failed cells (F1) are None."""
    R, tids, out = gx["R"], gx["tids"], {}
    for (cfg, rg, a), h in R.groupby(["config", "rung", "arm"]):
        if rg not in RUNGS_D or a not in ARMS_D:
            continue
        h = h.set_index("trial").loc[tids]
        L = []
        for f, l, s in zip(h.failed, h.loghr, h.se):
            L.append(None if f or not (np.isfinite(l) and np.isfinite(s)) else [round(float(l), 8), round(float(s), 8)])
        out.setdefault(cfg, {}).setdefault(rg, {})[a] = L
    return out


def build_data(g, g2, trials):
    S = {cfg: {rg: {a: BE.enc(g["G"][(cfg, rg, a)], BE.SC) for a in ARMS_D} for rg in RUNGS_D} for cfg in CFGS}
    S2 = {cfg: {rg: {a: BE.enc(g2["G"][(cfg, rg, a)], BE.SC) for a in ARMS_D} for rg in RUNGS_D} for cfg in CFGS}
    vix = {c: i for i, c in enumerate(BE.VN)}
    return dict(trials=trials, vars=[dict(c=c, lab=lab, g=gr) for c, lab, gr in VARS], sc=BE.SC, seed=BE.SEED, nb=BE.NB,
                S=S, U=BE.enc(g["U"], BE.SC), S2=S2, U2=BE.enc(g2["U"], BE.SC), ex=g["ex"], has_v2c=True,
                leak=dict(rung={r: [vix[c] for c in v] for r, v in BE.LEAK_RUNG.items() if r in RUNGS_D},
                          arm={}),
                E=dict(vars=[], buckets=[], sc=1000, S={}, U=[]),
                EST={"v1": est_block(g), "v2": est_block(g2)})


# ================================================================ Python references
def agree_py(D, coh, cfg, rung, a, T, ref="base"):
    """agreement metrics as scripts/v20/sens_primary32 (per arm) and the paired |dlog HR| contrast vs ref."""
    E = D["EST"][coh][cfg][rung]
    tr = D["trials"]

    def per(arm):
        x = [(E[arm][t], tr[t]) for t in T if E[arm][t] is not None]
        l = np.array([e[0] for e, _ in x])
        se = np.array([e[1] for e, _ in x])
        rb = np.array([q["rb"] for _, q in x])
        rs = np.array([q["rs"] for _, q in x])
        d = np.abs(l - rb)
        z = (l - rb) / np.sqrt(se ** 2 + rs ** 2)
        return dict(k=len(x), absd=float(d.mean()) if len(x) else np.nan, r=float(np.corrcoef(l, rb)[0, 1]) if len(x) > 2 else np.nan,
                    ea=float((100 * (d <= 1.96 * rs)).mean()) if len(x) else np.nan, cons=float((100 * (np.abs(z) < 1.96)).mean()) if len(x) else np.nan)
    m = per(a)
    ok = [t for t in T if E[a][t] is not None and E[ref][t] is not None]
    dd = np.array([abs(E[ref][t][0] - tr[t]["rb"]) - abs(E[a][t][0] - tr[t]["rb"]) for t in ok])
    m.update(closer=int((dd > 0).sum()), kp=len(ok), p_closer=BE.signflip_1s(dd) if len(ok) else np.nan)
    return m


# ================================================================ independent recomputation from the cells (claims checks)
GRID2 = {}  # filled in main(): full-precision spec-v2 grid (build_balance_explorer.load_grid_v2) and the deck data


def grid_rr(cfg, rg, a, b, ts, items, leak=True):
    """relative reduction in mean |SMD| (paired items, 4,000-resample trial bootstrap) recomputed from the spec-v2 cells."""
    G, D = GRID2["grid"], GRID2["D"]
    T = BE.trial_set(D["trials"], ts)
    Ma, Mb = G.block(cfg, rg, a, leak)[np.ix_(T, items)], G.block(cfg, rg, b, leak)[np.ix_(T, items)]
    m = np.isnan(Ma) | np.isnan(Mb)
    Ma, Mb = np.where(m, np.nan, Ma), np.where(m, np.nan, Mb)
    ok = (~m).sum(1) > 0
    return BE.relred_ci(np.nanmean(Mb[ok], 1), np.nanmean(Ma[ok], 1))


def dom_items(dname):
    return [j for j, (c, _, gr) in enumerate(VARS) if (gr.startswith("Echo") if dname == "Echo, all 35 items" else gr == dname)]


def bshuf_py(la, lb, rb, ndraw=20000, two=False):
    """scripts/v20/sens_primary32.bshuf (one-sided) and scripts/v21/paper2_grid.bshuf2 (two-sided), same statistic and draws."""
    st = lambda q: np.mean(np.abs(la - q) - np.abs(lb - q), axis=-1)
    obs = float(st(rb))
    rng = np.random.default_rng(0)
    IX = np.array([rng.permutation(len(rb)) for _ in range(ndraw)])
    null = st(rb[IX])
    return float(min(1.0, 2 * min((null <= obs + 1e-12).mean(), (null >= obs - 1e-12).mean()))) if two else float((null <= obs + 1e-12).mean())


def bshuf_deck(coh, cfg, rg, a, ts):
    D = GRID2["D"]
    E = D["EST"][coh][cfg][rg]
    T = [t for t in BE.trial_set(D["trials"], ts) if E[a][t] is not None and E["base"][t] is not None]
    la, lb = np.array([E[a][t][0] for t in T]), np.array([E["base"][t][0] for t in T])
    rb = np.array([D["trials"][t]["rb"] for t in T])
    return bshuf_py(la, lb, rb)


# ================================================================ SVG helpers (static slides)
def svg_bar_ci(rows, W=560, H=300, lo=-10, hi=20, title=""):
    """rows: [(label, sub, est, lo, hi, colour, bracket_text)] vertical bars with CI whiskers."""
    ml, mr, mt, mb = 46, 8, 26, 72
    ys = lambda v: mt + (hi - max(lo, min(hi, v))) / (hi - lo) * (H - mt - mb)
    cw = (W - ml - mr) / len(rows)
    s = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto">']
    if title:
        s.append(f'<text x="{ml}" y="14" font-size="13" font-weight="700" fill="{NAVY}">{esc(title)}</text>')
    for v in range(lo, hi + 1, 5):
        s.append(f'<line x1="{ml}" x2="{W - mr}" y1="{ys(v):.1f}" y2="{ys(v):.1f}" stroke="{NAVY if v == 0 else "#ececf2"}" stroke-width="{1.2 if v == 0 else 1}"/>'
                 f'<text x="{ml - 5}" y="{ys(v) + 4:.1f}" font-size="11" text-anchor="end" fill="{NAVY}">{fx(v, 0)}%</text>')
    for i, (lab, sub, e, l, h, col, br) in enumerate(rows):
        x = ml + i * cw + cw / 2
        bw = min(46, cw * 0.5)
        s.append(f'<rect x="{x - bw / 2:.1f}" y="{min(ys(e), ys(0)):.1f}" width="{bw:.1f}" height="{abs(ys(0) - ys(e)):.1f}" fill="{col}"/>')
        s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{ys(l):.1f}" y2="{ys(h):.1f}" stroke="{NAVY}" stroke-width="1.5"/>'
                 f'<line x1="{x - 6:.1f}" x2="{x + 6:.1f}" y1="{ys(l):.1f}" y2="{ys(l):.1f}" stroke="{NAVY}" stroke-width="1.5"/>'
                 f'<line x1="{x - 6:.1f}" x2="{x + 6:.1f}" y1="{ys(h):.1f}" y2="{ys(h):.1f}" stroke="{NAVY}" stroke-width="1.5"/>')
        s.append(f'<text x="{x:.1f}" y="{ys(max(h, e)) - 6:.1f}" font-size="13" font-weight="700" text-anchor="middle" fill="{NAVY}">{fx(e)}%</text>')
        s.append(f'<text x="{x:.1f}" y="{H - mb + 17}" font-size="12.5" font-weight="700" text-anchor="middle" fill="{RED if "CVD5" in lab and "10" not in lab else NAVY}">{esc(lab)}</text>'
                 f'<text x="{x:.1f}" y="{H - mb + 32}" font-size="10.5" text-anchor="middle" fill="{NAVY}">{esc(sub)}</text>'
                 f'<text x="{x:.1f}" y="{H - mb + 47}" font-size="10.5" text-anchor="middle" fill="#55576f">{esc(br[0])}</text>'
                 f'<text x="{x:.1f}" y="{H - mb + 61}" font-size="10.5" text-anchor="middle" fill="#55576f">{esc(br[1])}</text>')
    s.append("</svg>")
    return "".join(s)


def svg_hbars(rows, W=540, H=560, xmax=70, title=""):
    """rows: [(label, value or None, display, colour)] horizontal bars."""
    ml, mr, mt, mb = 128, 46, 22, 26
    rh = (H - mt - mb) / len(rows)
    xs = lambda v: ml + min(v, xmax) / xmax * (W - ml - mr)
    s = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto">']
    if title:
        s.append(f'<text x="0" y="13" font-size="13" font-weight="700" fill="{NAVY}">{esc(title)}</text>')
    for v in range(0, 71, 10):
        s.append(f'<line x1="{xs(v):.1f}" x2="{xs(v):.1f}" y1="{mt}" y2="{H - mb}" stroke="#ececf2"/>'
                 f'<text x="{xs(v):.1f}" y="{H - mb + 14}" font-size="10.5" text-anchor="middle" fill="{NAVY}">{v}%</text>')
    for i, (lab, v, disp, col) in enumerate(rows):
        y = mt + i * rh
        s.append(f'<text x="{ml - 5}" y="{y + rh * 0.72:.1f}" font-size="{min(11.5, rh * 0.82):.1f}" text-anchor="end" fill="{NAVY}">{esc(lab)}</text>')
        if v:
            s.append(f'<rect x="{ml}" y="{y + 1.5:.1f}" width="{max(xs(v) - ml, 1.5):.1f}" height="{rh - 3:.1f}" fill="{col}"/>')
        s.append(f'<text x="{(xs(v) if v else ml) + 4:.1f}" y="{y + rh * 0.72:.1f}" font-size="{min(10.5, rh * 0.8):.1f}" fill="{NAVY}">{esc(disp)}</text>')
    s.append("</svg>")
    return "".join(s)


def svg_grouped(groups, series, W=1150, H=300, lo=-10, hi=100, title=""):
    """groups: [(label, sublabel)]; series: [(name, colour, [values per group])] grouped vertical bars with value labels."""
    ml, mr, mt, mb = 46, 10, 18, 46
    ys = lambda v: mt + (hi - max(lo, min(hi, v))) / (hi - lo) * (H - mt - mb)
    gw = (W - ml - mr) / len(groups)
    bw = min(34, (gw - 24) / len(series))
    s = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto">']
    if title:
        s.append(f'<text x="{ml}" y="12" font-size="13" font-weight="700" fill="{NAVY}">{esc(title)}</text>')
    for v in range(0, hi + 1, 25):
        s.append(f'<line x1="{ml}" x2="{W - mr}" y1="{ys(v):.1f}" y2="{ys(v):.1f}" stroke="{NAVY if v == 0 else "#ececf2"}"/>'
                 f'<text x="{ml - 5}" y="{ys(v) + 4:.1f}" font-size="11" text-anchor="end" fill="{NAVY}">{v}%</text>')
    for gi, (gl, gs) in enumerate(groups):
        x0 = ml + gi * gw + (gw - bw * len(series)) / 2
        for k, (_, col, vals) in enumerate(series):
            v = vals[gi]
            x = x0 + k * bw
            s.append(f'<rect x="{x + 2:.1f}" y="{min(ys(v), ys(0)):.1f}" width="{bw - 4:.1f}" height="{abs(ys(0) - ys(v)):.1f}" fill="{col}"/>'
                     f'<text x="{x + bw / 2:.1f}" y="{min(ys(v), ys(0)) - 4:.1f}" font-size="10.5" text-anchor="middle" fill="{NAVY}">{fx(v, 0)}</text>')
        s.append(f'<text x="{ml + gi * gw + gw / 2:.1f}" y="{H - mb + 18}" font-size="13.5" font-weight="700" text-anchor="middle" fill="{NAVY}">{esc(gl)}</text>'
                 f'<text x="{ml + gi * gw + gw / 2:.1f}" y="{H - mb + 34}" font-size="11" text-anchor="middle" fill="#55576f">{esc(gs)}</text>')
    s.append("</svg>")
    return "".join(s)


def legend_sw(items):
    return "".join(f'<span style="margin-right:14px;white-space:nowrap"><span style="display:inline-block;width:11px;height:11px;background:{c};margin-right:4px"></span>{esc(n)}</span>'
                   for n, c in items)


# ================================================================ static slides
def slide(title, body, sid=None, cls=""):
    return f'<section class="slide {cls}"{f" id={chr(34)}{sid}{chr(34)}" if sid else ""} data-title="{esc(title)}">\n<div class="body">\n{body}\n</div>\n</section>\n'


def get_contrasts():
    MC = pd.read_csv(MISUM / "contrasts.csv")
    VC = pd.read_csv(V2SUM / "contrasts.csv")
    return MC, VC


def mrow(MC, st, rung, a, b="base", cfg="main"):
    r = MC[(MC.set == st) & (MC.config == cfg) & (MC.rung_a == rung) & (MC.rung_b == rung) & (MC.arm_a == a) & (MC.arm_b == b)
           & MC.kind.isin(["ladder", "within"])]
    assert len(r) == 1, (st, rung, a, b, cfg, len(r))
    return r.iloc[0]


def vrow(VC, coh, st, rung, a, b="base", cfg="main"):
    r = VC[(VC.cohort == coh) & (VC.set == st) & (VC.config == cfg) & (VC.rung_a == rung) & (VC.rung_b == rung) & (VC.arm_a == a)
           & (VC.arm_b == b) & (VC.kind == "within")]
    assert len(r) == 1, (coh, st, rung, a, b, cfg, len(r))
    return r.iloc[0]


def s_title():
    return """<section class="slide" id="s-title">
  <img class="tlogo" alt="CarDS Lab logo" src="__LOGO__">
  <div class="l1">CarDS Lab Presentation</div>
  <div class="l2">TRACE-ECG: AI-ECG representations for confounding control in target trial emulation</div>
  <div class="l3">Lab update · October 9<sup>th</sup>, 2026</div>
  <div class="l4">Results are provisional: the trial set is not frozen and the methods are not yet locked</div>
</section>
"""


def s_changes(trials, Q, MC, VC, EX):
    sl = 2
    med = claim(sl, "median % removed per trial (spec-v2 fixes)", f"{EX.pct_removed_v2.median():.0f}%", EXCL,
                probe="The median across the 38 trials is about 15%", ref_src=FIXD)
    mx = claim(sl, "largest % removed (VALIANT)", f"{EX.pct_removed_v2.max():.1f}%", EXCL, probe="| VALIANT | 60.2% |", ref_src=FIXD)
    n30 = claim(sl, "analysed set size (rescored)", str(len(Q["analysed_set"])), QV2C, ref=str(sum(t["v2c"] for t in trials)),
                ref_how="recomputed from records (analysed_set flags)")
    r2 = claim(sl, "R2: PS-CVD5 + ECG, CV-tuned PS", "4.7%", HAND, probe="S1 + ECG: 4.7% (−0.4 to 9.9)", ref_src=HAND)
    r2c = claim(sl, "R2 decomposition: 8.6% at C = 1", "8.6%", HAND, probe="8.6% at C = 1", ref_src=HAND)
    nob = sum(1 for _, _, gr in VARS if gr != "Coded record")
    n54 = claim(sl, "non-coded held-out items", str(nob), "scripts/make_acc_figure.VARS", probe="54 non-coded items, leakage-corrected", ref_src=PIPE)
    n58 = claim(sl, "all held-out items", str(len(VARS)), "scripts/make_acc_figure.VARS", probe="| 58 items |", ref_src=PIPE)
    return slide("What changed since 10-01", f"""
<ul class="chg">
  <li><b>Scope: the paper is ECG-only.</b> CLMBR-T was tested and dropped for clarity: with equal-information inputs it did not beat hdPS or PS-Flags. UK Biobank is out of scope.</li>
  <li><b>Primary analysis:</b> PS-CVD5 + ECG vs PS-CVD5 (was PS-Demo). Fixed L2 penalty C = 1 for every PS, 1:1 matching with caliper 0.2. A cross-validated penalty is a sensitivity analysis only, because it also shrinks the base covariates.</li>
  <li><b>Leakage audit.</b> Echo EF duplicates LVEF, eGFR is derived from creatinine, and the hdPS codes include the drug codes behind the medications item. So the primary panel is now <b>{n54} non-coded held-out items with leakage-corrected masking</b>; the {n58}-item panel is secondary.</li>
  <li><b>PS-Clinical has no LVEF</b> (no PS contains any echo measurement) and uses <b>5-draw multiple imputation</b>. Ladder: PS-Demo → PS-CVD5 → PS-CVD10 → hdPS → PS-Clinical (no LVEF). PS-Flags is supplement only.</li>
  <li><b>Blind data check of the cohort definitions → spec-v2 cohort fixes:</b> entry bounds, age, washouts, gates and 3 outcome rebuilds. Median {med} of patients removed per trial (range 0 to {mx}). PCs are recomputed within the fixed cohorts.</li>
  <li><b>Emulation-quality framework v2.0:</b> 10 items scored in points, two independent raters, adjudication and an independent audit, then rescored on the fixed cohorts. This gives a <b>{n30}-trial analysed set (provisional, not frozen)</b>.</li>
  <li><b>R2 restart (now on branch <code>r2</code>):</b> with a CV-tuned PS, PS-CVD5 + ECG fell to {r2} (not supported). Most of the drop came from the CV penalty ({r2c} at C = 1). We reverted to version 1, audited it, and then hardened it as above.</li>
</ul>""")


def s_flow(trials, Q):
    sl = 3
    tc = Q["tier_counts"]
    rc = {t: sum(x["tier"] == t for x in trials) for t in TIERS}
    for t in TIERS:
        claim(sl, f"tier count {t}", str(tc[t]), QV2C, ref=str(rc[t]), ref_how="recomputed from the 38 records")
    claim(sl, "tier counts 5/7/18/8", "/".join(str(tc[t]) for t in TIERS), QV2C, probe="5 Excellent / 7 Good / 18 Moderate / 8 Limited", ref_src=QUEUE)
    claim(sl, "candidates -> emulated", "99 -> 38", PIPE, probe="99 candidates → 38 emulated", ref_src=PIPE)
    claim(sl, "emulated trials", str(len(trials)), "cells (38 trials)", ref="38", ref_how="len(trials)")
    ent = sorted(t["full"] for t in trials if t["v2c"] and not t["s32"])
    lea = sorted(t["full"] for t in trials if t["s32"] and not t["v2c"])
    claim(sl, "entering vs paper 1's 32", ", ".join(Q["vs_paper1_32"]["entering"]), QV2C, ref=", ".join(ent), ref_how="recomputed (v2c and not s32)")
    claim(sl, "leaving vs paper 1's 32", ", ".join(Q["vs_paper1_32"]["leaving"]), QV2C, ref=", ".join(lea), ref_how="recomputed (s32 and not v2c)")
    e29 = sorted(t["full"] for t in trials if t["v2c"] and not t["v2"])
    claim(sl, "entering vs provisional 29", ", ".join(Q["vs_provisional_29"]["entering"]), QV2C, ref=", ".join(e29), ref_how="recomputed (v2c and not v2)")
    lim = [t["name"] for t in trials if t["tier"] == "Limited"]
    claim(sl, "Excellent + Good", str(len(Q["excellent_good"])), QV2C, ref=str(sum(t["tier"] in ("Excellent", "Good") for t in trials)), ref_how="recomputed from records")
    W = 1184
    s = [f'<svg viewBox="0 0 {W} 245" style="width:100%;height:auto">']

    def box(x, y, w, h, lines, fill="#fff", col=NAVY, fs=17, bold=True, stroke=NAVY):
        o = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        for i, l in enumerate(lines):
            o += f'<text x="{x + w / 2}" y="{y + h / 2 + (i - (len(lines) - 1) / 2) * fs * 1.25 + fs * 0.35:.1f}" font-size="{fs}" text-anchor="middle" fill="{col}" font-weight="{700 if bold and i == 0 else 400}">{esc(l)}</text>'
        return o

    def arr(x1, y1, x2, y2):
        a = math.atan2(y2 - y1, x2 - x1)
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2 - 3 * math.cos(a):.1f}" y2="{y2 - 3 * math.sin(a):.1f}" stroke="{NAVY}" stroke-width="2"/>'
                f'<path d="M{x2} {y2}L{x2 - 10 * math.cos(a - .4):.1f} {y2 - 10 * math.sin(a - .4):.1f}L{x2 - 10 * math.cos(a + .4):.1f} {y2 - 10 * math.sin(a + .4):.1f}Z" fill="{NAVY}"/>')
    s.append(box(0, 30, 190, 90, ["99 candidate", "cardiovascular RCTs"], fs=16))
    s.append(arr(192, 75, 238, 75))
    s.append(box(240, 20, 230, 110, ["Feasibility", "comparator, endpoint,", "strategies, sample size"], fill="#f5f5f8", fs=15))
    s.append(arr(472, 75, 518, 75))
    s.append(box(520, 30, 150, 90, ["38", "emulated"], fs=19))
    s.append(arr(672, 75, 718, 75))
    s.append(box(720, 20, 220, 110, ["Quality v2.0", "10 items, points;", "rescored, fixed cohorts"], fill="#f5f5f8", fs=15))
    s.append(arr(942, 75, 988, 75))
    s.append(box(990, 30, 192, 90, ["30 analysed", "provisional,", "not frozen"], fill=NAVY, col="#fff", fs=15, stroke=NAVY))
    # tier strip
    x0, wsc = 720, 460 / 38
    xx = x0
    cols = {"Excellent": NAVY, "Good": "#5b5d86", "Moderate": "#c9cbd8", "Limited": "#fbe3e2"}
    for t in TIERS:
        w = tc[t] * wsc
        s.append(f'<rect x="{xx:.1f}" y="150" width="{w:.1f}" height="30" fill="{cols[t]}"/><text x="{xx + w / 2:.1f}" y="170" font-size="13" font-weight="700" text-anchor="middle" fill="{"#fff" if t in ("Excellent", "Good") else (NAVY if t == "Moderate" else "#a8322e")}">{tc[t]}</text>'
                 f'<text x="{xx + w / 2:.1f}" y="196" font-size="11.5" text-anchor="middle" fill="{NAVY}">{t}</text>')
        xx += w
    s.append(f'<text x="720" y="142" font-size="12.5" fill="{NAVY}">Tiers (spec-v2 cohorts): Limited are excluded</text>')
    s.append(f'<text x="0" y="232" font-size="14" fill="{RED}">Excluded as Limited ({len(lim)}): {esc(", ".join(lim))}</text>')
    s.append("</svg>")
    AR = ["AF", "HF", "Diabetes", "Hypertension", "ACS / MI", "Other"]
    rows = "".join(f'<tr><td>{a}</td><td>{sum(t["area"] == a and t["v2c"] for t in trials)}</td><td>{sum(t["area"] == a for t in trials)}</td>'
                   f'<td>{sum(t["area"] == a and t["s32"] for t in trials)}</td></tr>' for a in AR)
    return slide("Data and trial flow", f"""
<h2>99 candidate RCTs → 38 emulations in YNHHS EHR data → 30 analysed</h2>
{"".join(s)}
<div style="display:grid;grid-template-columns:1.25fr 1fr;gap:34px;margin-top:4px">
  <table class="t tsm">
    <tr><th>Compared with</th><th>Entering</th><th>Leaving</th></tr>
    <tr><td>Paper 1's 32 (v19 tiers)</td><td>{esc(", ".join(Q["vs_paper1_32"]["entering"]))}</td><td>{esc(", ".join(Q["vs_paper1_32"]["leaving"]))}</td></tr>
    <tr><td>Provisional 29 (v2.0 tiers, version 1 cohorts)</td><td>{esc(", ".join(Q["vs_provisional_29"]["entering"]))} (its outcome defect is now fixed)</td><td>none</td></tr>
  </table>
  <table class="t tsm"><tr><th>Area</th><th>Analysed (30)</th><th>Emulated (38)</th><th>Paper 1 (32)</th></tr>{rows}</table>
</div>
<p class="small" style="margin-top:8px">New-user, active-comparator designs; outcome = each trial's primary endpoint. Sensitivity sets: Excellent + Good ({len(Q["excellent_good"])}), paper 1's 32, all 38.</p>""")


def s_framework(trials, Q):
    sl = 4
    it = load_md_table(QFRAME, "| ID | Domain | Item")
    assert [r["ID"] for r in it] == ITEMS
    rows = "".join(f'<tr><td class="n">{r["ID"]}</td><td>{esc(r["Item"].split(" (")[0])}</td><td class="nw">{esc(r["Points"])}</td></tr>' for r in it)
    for r in it:
        claim(sl, f"item {r['ID']} points", r["Points"], QFRAME, probe=f"| {r['ID']} | {r['Domain']} | {r['Item']} | {r['Points']} |", ref_src=QFRAME)
    tr = load_md_table(QFRAME, "| Order | Tier | Rule")
    trows = "".join(f'<tr><td class="n">{esc(r["Tier"].replace("**", ""))}</td><td>{esc(r["Rule"].replace("**", ""))}</td></tr>' for r in tr)
    ag = {r["Element"]: r for r in load_md_table(QADJ, "| Element | % exact agreement")}
    kap = lambda k: ag[k]["κ (95% CI)"]
    claim(sl, "EL kappa", kap("EL (0–2)"), QADJ, probe="EL weighted κ 0.311", ref_src=QAUD)
    claim(sl, "SI kappa", kap("SI (0–2)"), QADJ, probe="SI 0.663", ref_src=QAUD)
    claim(sl, "tier weighted kappa", "0.72", QADJ, probe="tier weighted κ 0.723", ref_src=QAUD)
    claim(sl, "same tier", "30/38", QADJ, probe="same tier in 30/38", ref_src=QAUD)
    claim(sl, "items agreed", "344/380", QADJ, probe="344/380 items agree", ref_src=QAUD)
    arow = "".join(f'<tr><td>{esc(k.split(" (")[0])}</td><td>{esc(ag[k]["% exact agreement"])}%</td><td>{esc(kap(k))}</td></tr>'
                   for k in ["EL (0–2)", "TZ (0–2)", "CO (0–2)", "OU (0–2)", "ES (0–1)", "SI (0–2)"])
    tier_k = ag["Tier, 4 levels"]["κ (95% CI)"].split(";")[0]
    set_k = ag["Analysed set"]["κ (95% CI)"]
    claim(sl, "analysed-set kappa", set_k, QADJ, probe="κ 0.77 (0.49–1.00)", ref_src=QADJ)
    icc = ag["Total (0–16)"]["κ (95% CI)"].split(";")[0]
    claim(sl, "total ICC", icc, QADJ, probe="ICC 0.89 (95% CI 0.82–0.94)", ref_src=QADJ)
    return slide("Emulation-quality framework v2.0", f"""
<div style="display:grid;grid-template-columns:0.95fr 1.2fr 0.95fr;gap:22px">
  <div><h3 class="h3">10 items (total 0–16; higher = worse)</h3><table class="t tq">{rows}</table></div>
  <div><h3 class="h3">Tiers (first rule that matches)</h3><table class="t tq">{trows}</table>
    <p class="small" style="margin-top:8px">Analysed set = Excellent + Good + Moderate. Rescored on the spec-v2 cohorts: defects that the fixes removed are no longer penalised. An entry bound that the data can apply, and that spec v2 applies, scores 0. Tiers: <b>{Q["tier_counts"]["Excellent"]} / {Q["tier_counts"]["Good"]} / {Q["tier_counts"]["Moderate"]} / {Q["tier_counts"]["Limited"]}</b>.</p></div>
  <div><h3 class="h3">Process and agreement</h3>
    <ul class="tight"><li>Two independent raters, blind to results, scored the trials from protocols, spec, code and data checks</li><li>Adjudication, then an independent audit (2 blocking findings: inconsistent unscored deviations; freeze conditions not met)</li><li>Rescored on the fixed cohorts; scores were hashed before any impact number was computed</li></ul>
    <table class="t tq"><tr><th>Element</th><th>Exact</th><th>κ (95% CI)</th></tr>{arow}
    <tr><td>Tier (4 levels)</td><td>{esc(ag["Tier, 4 levels"]["% exact agreement"])}%</td><td>{esc(tier_k)}</td></tr>
    <tr><td>Analysed set</td><td>{esc(ag["Analysed set"]["% exact agreement"])}%</td><td>{esc(set_k)}</td></tr>
    <tr><td>Total score</td><td></td><td>{esc(icc)}</td></tr></table>
    <p class="small red" style="margin-top:6px">The raters, adjudicator and auditor are runs of one LLM, so this is not human inter-rater reliability. Clinician review is pending.</p></div>
</div>""")


def s_tiers(trials, Q):
    sl = 5
    TI = {t: i for i, t in enumerate(TIERS)}
    S = sorted(trials, key=lambda x: (TI[x["tier"]], x["tot"], x["area"], x["name"]))
    nprov = sum(x["prov"] for x in trials)
    claim(sl, "trials with a tier-changing provisional score", str(nprov), QV2C, probe="9 tier-changing provisional scores remain", ref_src=QUEUE)
    for x in trials:
        if x["tier"] != x["tq1"]:
            pass
    tg = lambda t: f'<span class="tier t{TI[t]}">{t}</span>'
    tab = lambda R: ('<table><tr><th class="l">Trial</th>' + "".join(f"<th>{i}</th>" for i in ITEMS) +
                     '<th>Tot</th><th class="l">Tier (spec-v2)</th><th class="l">v2.0, v1 coh.</th><th class="l">v19 (paper 1)</th></tr>' +
                     "".join(f'<tr{" class=tb" if i and R[i - 1]["tier"] != x["tier"] else ""}><td class="l n">{esc(x["name"])}{"†" if x["prov"] else ""}</td>'
                             + "".join(f'<td class="{"P" if v == 2 else ""}">{v if v else ""}</td>' for v in x["it"])
                             + f'<td class="pt">{x["tot"]}</td><td class="l">{tg(x["tier"])}</td><td class="l">{tg(x["tq1"])}</td><td class="l">{tg(x["t19"])}</td></tr>'
                             for i, x in enumerate(R)) + "</table>")
    half = 19
    nch = sum(x["tier"] != x["tq1"] for x in trials)
    claim(sl, "tier changes v2.0 (v1 cohorts) -> spec-v2", str(nch), QV2C, ref=str(sum(1 for r in Q["records"] if r["tier"] != r["tier_v1_cohorts"])), ref_how="recomputed from records")
    return slide("Emulation quality per trial (framework v2.0, rescored on the spec-v2 cohorts)", f"""
<div class="qitems">{tab(S[:half])}{tab(S[half:])}</div>
<p class="xs" style="margin-top:6px">Item points (blank = 0; red = 2). Tot = total (0–16). † = a provisional item could change the tier ({nprov} trials; the set is not frozen). "v2.0, v1 coh." = adjudicated v2.0 tier on the version 1 cohorts ({nch} trials changed tier after the rescore). "v19" = paper 1's tiers (design flags and fidelity points).</p>""")


def s_fixes(trials, EX, RR):
    sl = 6
    fx_tab = {r["Trial"]: r for r in load_md_table(FIXD, "| Trial | S32 | S29 | Fix types applied")}
    EXm = EX.set_index("label")
    rows = []
    for t in sorted(trials, key=lambda x: -EXm.loc[x["full"], "pct_removed_v2"]):
        v = float(EXm.loc[t["full"], "pct_removed_v2"])
        dv = fx_tab[t["full"]]["% removed (v2)"]
        disp = "0" if v == 0 else ("<1%" if v < 1 else f"{v:.1f}%")
        if v >= 1:
            claim(sl, f"% removed {t['full']}", f"{v:.1f}", EXCL, ref=dv, ref_how="COHORT_FIXES.md per-trial table")
        else:
            claim(sl, f"% removed {t['full']} (shown as {disp})", disp, EXCL, ref=("0" if dv == "0.0" else "<1%" if (dv.startswith("<") or float(dv) < 1) else dv),
                  ref_how=f"COHORT_FIXES.md per-trial table ({dv})")
        types = fx_tab[t["full"]]["Fix types applied"].replace("washout/class", "washout").replace("gate/population", "gate").replace("none (no patient removed)", "none")
        rows.append((t["name"], v, f"{disp}  {types}" if v else "0  (none)", NAVY if t["v2c"] else "#b9bbc8"))
    n0 = int((EX.pct_removed_v2 == 0).sum())
    claim(sl, "trials that lost nobody", {6: "Six"}.get(n0, str(n0)), EXCL, probe=f"{ {6: 'Six'}.get(n0, str(n0)) } trials lost nobody", ref_src=FIXD)
    claim(sl, "random-removal draws", str(int(RR.draws.iloc[0])), RRS, probe="20 draws per trial", ref_src=FIXD)
    bars = svg_hbars(rows, W=560, H=560, xmax=90, title="% of the version 1 analysed cohort removed (navy = in the analysed 30)")
    R = RR.set_index(["set", "arm"])
    rr = []
    for st, lab in (("S32", "Paper 1's 32"), ("S29", "Provisional 29"), ("S38", "All 38")):
        x = R.loc[(st, "ECG")]
        v1, v2 = fx(x.relred54_v1), fx(x.relred54_v2)
        rnd = f"{fx(x.relred54_random_median)} ({fx(x.relred54_random_p5)} to {fx(x.relred54_random_p95)})"
        claim(sl, f"random removal {st} ECG", f"{v1} | {v2} | {rnd}", RRS, probe=f"| {st} | + ECG | {norm(v1)} | {norm(v2)} | {norm(rnd)} |", ref_src=FIXD)
        rr.append(f"<tr><td>{lab}</td><td>{v1}%</td><td><b>{v2}%</b></td><td>{rnd}</td></tr>")
    return slide("Spec-v2 cohort fixes: what was removed, and does it explain the smaller ECG gain?", f"""
<div style="display:grid;grid-template-columns:560px 1fr;gap:30px">
  <div>{bars}</div>
  <div>
    <h3 class="h3">Five kinds of fix (patients removed; no index date moves)</h3>
    <ol class="tight">
      <li><b>Published numeric entry bounds</b>: HbA1c, BP, natriuretic peptides, cholesterol, renal and other labs; "unknown passes"</li>
      <li><b>Age bounds</b> checked in all 38 (only CAROLINA removed anyone)</li>
      <li><b>Class washouts</b>: other GLP-1RA, other SGLT2i, saxagliptin/alogliptin, prior ARNI, metoprolol succinate</li>
      <li><b>Gate fixes</b>: LAAOS III AF before admission; LIFE definite LVH; COMET LVEF ≤35%; VALIANT LV dysfunction or HF</li>
      <li><b>Outcome rebuilds</b>: AMPLIFY, LODESTAR, PROVE IT</li>
    </ol>
    <h3 class="h3" style="margin-top:12px">Random-removal check (PS-CVD5 + ECG vs PS-CVD5, 54 items)</h3>
    <table class="t tsm"><tr><th>Set</th><th>Version 1</th><th>Spec-v2</th><th>Random removal, 20 draws: median (5th–95th pct)</th></tr>{"".join(rr)}</table>
    <p style="font-size:18px;margin-top:10px">Removing the <b>same numbers of patients at random</b> shrinks the gain just as much. So the drop from about 9% to 6.5% reflects <b>refitting on smaller cohorts</b>, not the fixes as such.</p>
    <p class="small">Not fixed (they need full rebuilds): CABANA (arm assignment) and TRANSFORM-HF (time zero); both stay scored. {({6: "Six"}.get(n0, str(n0)))} trials lost nobody.</p>
  </div>
</div>""")


def s_methods_design():
    sl = 7
    claim(sl, "ECG embedding dimension -> PCs", "256-d -> 32 PCs", PIPE, probe="256-d → 32 PCs within each trial", ref_src=PIPE)
    claim(sl, "index-day ECG share (version 1)", "37%", HAND, probe="37% of ECGs are on the index day", ref_src=HAND)
    claim(sl, "ECG window", "[index - 365 d, index]", PIPE, probe="[index − 365 d, index]", ref_src=PIPE)
    claim(sl, "failed-cell rule", "<11 matched pairs", PIPE, probe="Cells with <11 matched pairs", ref_src=PIPE)
    claim(sl, "caliper", "caliper 0.2 SD", PIPE, probe="caliper 0.2 SD", ref_src=PIPE)
    claim(sl, "fixed penalty", "C = 1", PIPE, probe="fixed C = 1 for every specification", ref_src=PIPE)
    L = [("PS-Demo", "age, sex, index year", "ladder"), ("PS-CVD5", "+ hypertension, T2D, CAD, AF, HF", "PRIMARY"),
         ("PS-CVD10", "PS-Demo + 10 fixed diagnoses (+ CKD, COPD/asthma, PAD, stroke/TIA, valve)", "comparison"),
         ("hdPS", "PS-Demo + 9–13 diagnoses + top 200 hdPS code levels", "ladder"),
         ("PS-Clinical (no LVEF)", "+ vitals, core labs, diagnoses, medication orders, utilisation; 5-draw MI", "richest"),
         ("PS-Flags", "PS-Demo + ICD-10 3-character flags (≥1%)", "supplement")]
    s = [f'<svg viewBox="0 0 640 400" style="width:100%;height:auto"><text x="0" y="16" font-size="15" font-weight="700" fill="{NAVY}">PS information ladder (thin → rich), each ± ECG ± permuted ECG</text>']
    for i, (k, t, tag) in enumerate(L):
        y, x = 28 + i * 60, min(i, 4) * 20
        sup = tag == "supplement"
        dash = 'stroke-dasharray="6 4"' if sup else ""
        s.append(f'<rect x="{x}" y="{y}" width="{632 - x}" height="52" fill="{"#fff" if sup else NAVY}" fill-opacity="{1 if sup else 0.12 + i * 0.15}" stroke="{NAVY}" stroke-width="{1.5 if sup else 0}" {dash}/>'
                 f'<text x="{x + 12}" y="{y + 22}" font-size="16" font-weight="700" fill="{"#fff" if (i >= 3 and not sup) else NAVY}">{esc(k)}</text>'
                 f'<text x="{x + 12}" y="{y + 42}" font-size="13" fill="{"#fff" if (i >= 3 and not sup) else NAVY}">{esc(t)}</text>'
                 f'<text x="622" y="{y + 22}" font-size="12.5" text-anchor="end" font-weight="700" fill="{RED if tag == "PRIMARY" else ("#fff" if (i >= 3 and not sup) else NAVY)}">{tag}</text>')
    s.append("</svg>")
    return slide("Methods: PS ladder, ECG representation and matching", f"""
<div style="display:grid;grid-template-columns:640px 1fr;gap:30px">
  <div>{"".join(s)}<p class="small">No PS contains any echocardiographic measurement. PS-Clinical without LVEF was re-imputed without LVEF, with 5 draws: per-item |SMD| is averaged across draws and HRs are combined by Rubin's rules.</p></div>
  <div>
    <div class="card"><h3>ECG representation</h3><p>BCL self-supervised signal encoder, <b>256-d → 32 PCs</b> computed within each (fixed) cohort. Latest 12-lead ECG in [index − 365 d, index], <b>index day included</b> (37% of ECGs, version 1 cohorts; disclosed per trial).</p></div>
    <div class="card" style="margin-top:12px"><h3>Placebo</h3><p><b>Permuted ECG</b>: the embeddings are shuffled between patients within each trial, so the dimension is the same and the information is gone.</p></div>
    <div class="card" style="margin-top:12px"><h3>PS and matching</h3><p>L2-penalised logistic PS on standardised covariates, <b>fixed C = 1</b> for every specification. <b>1:1 greedy nearest-neighbour matching on the PS logit, caliper 0.2 SD</b>, without replacement. Sensitivities: caliper 0.1, 1:3 matching, IPTW, overlap weights, gradient-boosted PS. A cell with &lt;11 matched pairs counts as failed.</p></div>
  </div>
</div>""")


def s_methods_panel():
    sl = 8
    from collections import Counter
    cnt = Counter(gr for _, _, gr in VARS)
    ex = {"Vitals & core labs": "observed LVEF, BP, heart rate, BMI, creatinine, K, Na, Hb", "Other labs": "NT-proBNP, eGFR, HbA1c, troponin, LDL, …",
          "Echo: LV structure": "", "Echo: LV function": "", "Echo: diastolic / LA": "", "Echo: RV / pulmonary": "", "Echo: valves / aorta": "",
          "Coded record": "medications, healthcare use, held-out codes, prognostic score"}
    rows = ""
    for gname in ["Vitals & core labs", "Other labs", "Echo: LV structure", "Echo: LV function", "Echo: diastolic / LA", "Echo: RV / pulmonary", "Echo: valves / aorta"]:
        rows += f'<tr><td>{esc(gname)}<span class="xs"> {esc(ex[gname])}</span></td><td>{cnt[gname]}</td></tr>'
    necho = sum(v for k, v in cnt.items() if k.startswith("Echo"))
    claim(sl, "echo items", str(necho), "scripts/make_acc_figure.VARS", probe="35 echo measures", ref_src=PIPE)
    claim(sl, "vitals/core labs items", str(cnt["Vitals & core labs"]), "scripts/make_acc_figure.VARS", probe="9 vitals and core labs", ref_src=PIPE)
    claim(sl, "other labs items", str(cnt["Other labs"]), "scripts/make_acc_figure.VARS", probe="10 other labs", ref_src=PIPE)
    rows += f'<tr><td><b>Primary panel (non-coded)</b></td><td><b>{len(VARS) - cnt["Coded record"]}</b></td></tr><tr><td>Coded record (secondary panel only)<span class="xs"> {esc(ex["Coded record"])}</span></td><td>{cnt["Coded record"]}</td></tr><tr><td><b>Secondary panel</b></td><td><b>{len(VARS)}</b></td></tr>'
    lab = {c: l for c, l, _ in VARS}
    grp = {c: g for c, _, g in VARS}
    RN = [("P1", "PS-Demo"), ("P5", "PS-CVD5"), ("PS10", "PS-CVD10"), ("Flags", "PS-Flags"), ("hdPS200", "hdPS"), ("clinical_nolvef", "PS-Clinical (no LVEF)")]
    lk = ""
    for r, nm in RN:
        m = BE.LEAK_RUNG[r]
        m54 = [lab[c] for c in m if grp[c] != "Coded record"]
        m58 = [c for c in m if grp[c] == "Coded record"]
        t54 = "none" if not m54 else (f"{len(m54) - 1} observed vitals/labs that are PS inputs (not LVEF) + eGFR" if r == "clinical_nolvef" else ", ".join(m54))
        t58 = "none" if not m58 else ("all 4 coded items" if len(m58) == 4 else "held-out codes, prognostic score")
        lk += f"<tr><td>{nm}</td><td>{esc(t54)}</td><td>{esc(t58)}</td></tr>"
    claim(sl, "bootstrap resamples", "4,000", PIPE, probe="95% CI from 4,000 bootstrap resamples of trials", ref_src=PIPE)
    claim(sl, "benchmark-permutation draws", "20,000", PIPE, probe="20,000 draws", ref_src=PIPE)
    claim(sl, "leakage rho threshold", "0.80 / 0.50", PIPE, probe="0.50 ≤ |ρ| < 0.80", ref_src=PIPE)
    claim(sl, "PS-Clinical (no LVEF) masks on 54 items", "8 + eGFR", "build_balance_explorer.LEAK_RUNG", probe="8 `smd_obs_*`; **not** LVEF) + **eGFR**", ref_src=PIPE)
    lk += "<tr><td>+ ECG, + permuted ECG</td><td>none</td><td>none</td></tr>"
    return slide("Methods: held-out panel, leakage map and endpoints", f"""
<div style="display:grid;grid-template-columns:0.9fr 1.15fr 0.95fr;gap:22px">
  <div><h3 class="h3">Held-out characteristics (not in the PS being judged)</h3><table class="t tq">{rows}</table></div>
  <div><h3 class="h3">Leakage-corrected masking (a cell's mask = PS mask ∪ arm mask)</h3>
    <table class="t tq"><tr><th>PS level / arm</th><th>Masked on the 54 items</th><th>Also masked on the 58</th></tr>{lk}</table>
    <p class="small" style="margin-top:6px">Rules: mask any held-out item that is the same quantity as, derived from, or in the same code family as a PS input, or has pooled |ρ| ≥ 0.80 with one. Soft proxies (0.50 ≤ |ρ| &lt; 0.80, e.g. BUN, LVESVi, GLS) stay in. Items that are PS inputs are always masked.</p></div>
  <div><h3 class="h3">Endpoints and tests</h3>
    <ul class="tight">
      <li><b>Primary:</b> relative reduction in mean |SMD| after matching = 1 − (mean over trials with the ECG / without it); 95% CI from 4,000 bootstrap resamples of trials</li>
      <li>Items are used only where they are observed in both compared cells</li>
      <li>Secondary endpoints: % of items with |SMD| &lt; 0.1; trials improved; per-domain reductions</li>
      <li>Exact sign-flip permutation across trials (one-sided vs base or placebo); BH-FDR within families</li>
      <li><b>Agreement (secondary):</b> Cox model in the matched cohort, pair-clustered; |Δ log HR| vs the RCT; <b>benchmark-permutation test</b> (RCT results reassigned across trials, 20,000 draws) required for any agreement claim</li>
    </ul></div>
</div>""")


def s_results2(MC, VC, IM, DM):
    sl = 10
    I = IM.set_index("set")
    nm = [("new set (rescored, spec-v2)", "Snew", "Analysed set, rescored, provisional"), ("Excellent + Good (rescored)", "SEG", "Excellent + Good"),
          ("provisional 29 (v2.0 adjudication)", "S29", "Provisional 29"), ("paper 1's 32", "S32", "Paper 1's 32"), ("all 38", "S38", "All 38")]
    rows = ""
    for key, st, lab in nm:
        x = I.loc[key]
        m = mrow(MC, st, "P5", "ECG")
        assert abs(m.relred54 - x.relred54) < 1e-9 and abs(m.relred54_hi - x.hi) < 1e-9  # impact table = MI summary rows
        rr = claim(sl, f"PS-CVD5 + ECG {st}", ci(x.relred54, x.lo, x.hi), IMPACT, probe=f"{norm(ci(x.relred54, x.lo, x.hi))}", ref_src=QRES)
        pe = claim(sl, f"P (mean |SMD|) {st}", fp(x.m54_p), IMPACT, ref=fp(m.m54_p), ref_how="MI summary contrasts.csv")
        sh = mrow(MC, st, "P5", "ECG", "shufECG")
        ps = claim(sl, f"ECG vs permuted {st}", f"{fx(sh.relred54)}%", MISUM / "contrasts.csv",
                   ref=(f"{fx(vrow(VC, 'v2', st, 'P5', 'ECG', 'shufECG').relred54)}%" if st in ("S29", "S32", "S38") else None) or f"{fx(sh.relred54)}%",
                   ref_how="v2_cohorts summary contrasts.csv" if st in ("S29", "S32", "S38") else "same file (no second copy)")
        v1 = f"{fx(vrow(VC, 'v1', st, 'P5', 'ECG').relred54)}%" if st in ("S29", "S32", "S38") else "–"
        if st in ("S29", "S32", "S38"):
            claim(sl, f"version 1 cohorts {st}", v1, V2SUM / "contrasts.csv",
                  probe=f"| {dict(S29='29 (provisional)', S32='32 (paper 1)', S38='38')[st]} | {norm(v1)}", ref_src=FIXD)
        ad = f"{x.absd_base:.3f} → {x.absd_ecg:.3f}"
        claim(sl, f"|dlog HR| {st}", ad, IMPACT, ref=f"{m.absd_b:.3f} → {m.absd_a:.3f}", ref_how="MI summary contrasts.csv")
        bp = claim(sl, f"benchmark-permutation P {st}", f"{x.bshuf_p:.2f}", IMPACT, ref=f"{m.bshuf_p:.2f}", ref_how="MI summary contrasts.csv")
        rows += (f'<tr class="{"hl" if st == "Snew" else ""}"><td>{lab} ({int(x.n_trials)})</td><td><b>{rr}</b></td><td>{x.m54_better}</td><td>{pe}</td>'
                 f'<td>{ps}</td><td>{v1}</td><td>{ad}</td><td>{bp}</td></tr>')
    # ladder on the 30 (MI summary, Snew) with the provisional 29 in brackets
    LAD = [("P1", "PS-Demo", "demographics"), ("P5", "PS-CVD5", "+ 5 diagnoses"), ("PS10", "PS-CVD10", "+ 10 diagnoses"),
           ("hdPS200", "hdPS", "+ 200 codes"), ("clinical_nolvef_mi", "PS-Clinical", "no LVEF; 5-draw MI")]
    bars = []
    for rg, lab, sub in LAD:
        x, y = mrow(MC, "Snew", rg, "ECG"), mrow(MC, "S29", rg, "ECG")
        claim(sl, f"ladder {lab} + ECG (30)", ci(x.relred54, x.relred54_lo, x.relred54_hi), MISUM / "contrasts.csv",
              probe=f"{norm(ci(x.relred54, x.relred54_lo, x.relred54_hi))}", ref_src=QUEUE if rg != "clinical_nolvef_mi" else MID)
        claim(sl, f"ladder {lab} + ECG (29)", f"{fx(y.relred54)}%", MISUM / "contrasts.csv", probe=f"[{norm(fx(y.relred54))}%", ref_src=QUEUE)
        bars.append((lab, sub, x.relred54, x.relred54_lo, x.relred54_hi, RED if rg == "P5" else NAVY, (pv(x.m54_p), f"[29 trials: {fx(y.relred54)}%]")))
    ladder = svg_bar_ci(bars, W=600, H=318, lo=-10, hi=20, title="+ ECG vs PS alone at each base (30 trials; 95% CI)")
    hd1 = vrow(VC, "v1", "S32", "hdPS200", "ECG")
    claim(sl, "hdPS + ECG on version 1 (32)", f"{fx(hd1.relred54)}%", V2SUM / "contrasts.csv", probe="It was 7.6% on version 1", ref_src=QUEUE)
    # domains
    D5 = DM[(DM.set == "Snew") & (DM.config == "main") & (DM.contrast == "P5: ECG vs base")].set_index("domain")
    DMI = DM[(DM.set == "Snew") & (DM.config == "main") & (DM.contrast == "clinical_nolvef_mi: ECG vs base")].set_index("domain")
    drows = ""
    for dname, lab in [("Vitals & core labs", "Vitals & core labs"), ("Other labs", "Other labs"), ("Echo: LV structure", "Echo: LV structure"),
                       ("Echo: LV function", "Echo: LV function"), ("Echo: diastolic / LA", "Echo: diastolic / LA"), ("Echo: RV / pulmonary", "Echo: RV / pulmonary"),
                       ("Echo: valves / aorta", "Echo: valves / aorta"), ("Echo, all 35 items", "Echo, all 35 items")]:
        a, b = D5.loc[dname], DMI.loc[dname]
        ra = grid_rr("main", "P5", "ECG", "base", "v2c", dom_items(dname))
        claim(sl, f"domain P5 {dname}", ci(a.relred, a.relred_lo, a.relred_hi), MISUM / "domains.csv", ref=ci(*ra[:3]), ref_how="recomputed from the spec-v2 cells")
        rbb = grid_rr("main", "clinical_nolvef", "ECG", "base", "v2c", dom_items(dname))
        claim(sl, f"domain MI {dname}", ci(b.relred, b.relred_lo, b.relred_hi), MISUM / "domains.csv", ref=ci(*rbb[:3]), ref_how="recomputed from the MI cells")
        drows += (f'<tr><td>{esc(lab)} ({int(a.n_items)})</td><td class="nw">{ci(a.relred, a.relred_lo, a.relred_hi)}</td>'
                  f'<td class="nw">{ci(b.relred, b.relred_lo, b.relred_hi) if int(b.n_items) else "masked"}{"*" if dname == "Vitals & core labs" else ""}</td></tr>')
    lv29 = DM[(DM.set == "S29") & (DM.config == "main") & (DM.contrast == "clinical_nolvef_mi: ECG vs base") & (DM.domain == "Vitals & core labs")].iloc[0]
    claim(sl, "MI observed LVEF gain (29)", ci(lv29.relred, lv29.relred_lo, lv29.relred_hi), MISUM / "domains.csv",
          probe="observed LVEF, the only vitals/labs item not masked: 16.0% (4.1 to 27.9)", ref_src=MID)
    return slide("Results 2: the primary contrast, the ladder and the domains (spec-v2 cohorts)", f"""
<table class="t tsm"><tr><th>PS-CVD5 + ECG vs PS-CVD5 (54 items)</th><th>Rel. reduction in mean |SMD| (95% CI)</th><th>Lower</th><th>P</th><th>ECG vs permuted ECG</th><th>Version 1 cohorts</th><th>|Δ log HR|: PS alone → + ECG</th><th>Benchmark-perm. P</th></tr>{rows}</table>
<div style="display:grid;grid-template-columns:600px 1fr;gap:24px;margin-top:10px">
  <div>{ladder}</div>
  <div><table class="t tq"><tr><th>Domain (items); 30 trials</th><th>+ ECG on PS-CVD5</th><th>+ ECG on PS-Clinical (no LVEF)</th></tr>{drows}</table>
  <p class="small" style="margin-top:6px">* On PS-Clinical, observed LVEF is the only vitals/labs item that is not masked. hdPS + ECG was {fx(hd1.relred54)}% on the version 1 cohorts (32 trials). Its fall to about 0 is flagged as a likely small-cohort artefact (see Decisions).</p></div>
</div>""")


def s_robust(MC, VC, RR, IM):
    sl = 12
    rows = []
    s = mrow(MC, "Snew", "P5", "shufECG")
    e = mrow(MC, "Snew", "P5", "ECG", "shufECG")
    rng = [mrow(MC, st, "P5", "ECG", "shufECG").relred54 for st in ("Snew", "SEG", "S29", "S32", "S38")]
    rtxt = f"{fx(min(rng))} to {fx(max(rng))}%"
    claim(sl, "ECG vs permuted range across sets", rtxt, MISUM / "contrasts.csv", probe="ECG vs permuted ECG: 6.3–8.1% in every set", ref_src=QUEUE)
    rows.append(("Placebo (permuted ECG)", f"Permuted vs PS alone: {ci(s.relred54, s.relred54_lo, s.relred54_hi)}, {pv(s.m54_p)} (two-sided). ECG vs permuted: {ci(e.relred54, e.relred54_lo, e.relred54_hi)}; {rtxt} across the five trial sets", "30"))
    cf = []
    for c, lab in (("main", "1:1, cal. 0.2"), ("cal01", "cal. 0.1"), ("m13", "1:3"), ("iptw", "IPTW"), ("overlap", "overlap"), ("gbm", "GBM PS")):
        x = mrow(MC, "Snew", "P5", "ECG", cfg=c)
        rc = grid_rr(c, "P5", "ECG", "base", "v2c", BE.items("54"))
        claim(sl, f"PS method {c} (30)", f"{fx(x.relred54)} ({fx(x.relred54_lo)} to {fx(x.relred54_hi)})", MISUM / "contrasts.csv",
              ref=f"{fx(rc[0])} ({fx(rc[1])} to {fx(rc[2])})", ref_how="recomputed from the spec-v2 cells")
        cf.append(f"{lab} {fx(x.relred54)}% ({fx(x.relred54_lo)} to {fx(x.relred54_hi)})")
    rows.append(("Six PS methods", "; ".join(cf) + ". All six CIs exclude 0", "30"))
    mi = mrow(MC, "Snew", "clinical_nolvef_mi", "ECG")
    dr = [MC[(MC.set == "Snew") & (MC.config == "main") & (MC.rung_a == f"clinical_nolvef#{k}") & (MC.arm_a == "ECG") & (MC.arm_b == "base")].iloc[0].relred54 for k in range(1, 6)]
    drt = f"{fx(min(dr))} to {fx(max(dr))}%"
    claim(sl, "MI draw range (30)", drt, MISUM / "contrasts.csv", probe="| 4.5% (1.2 to 7.9); 20/30; P = .006 | 5.9% (3.0 to 9.0); P < .001 | 2.4 to 5.7 |", ref_src=MID)
    rows.append(("Multiple imputation (PS-Clinical, no LVEF)", f"MI: {ci(mi.relred54, mi.relred54_lo, mi.relred54_hi)}, {pv(mi.m54_p)}; single draws {drt}. Single-draw estimates should not be reported", "30"))
    R = RR.set_index(["set", "arm"]).loc[("S32", "ECG")]
    claim(sl, "random removal S32", f"{fx(R.relred54_random_median)} ({fx(R.relred54_random_p5)} to {fx(R.relred54_random_p95)})", RRS,
          probe=f"| S32 | + ECG | {fx(R.relred54_v1)} | {fx(R.relred54_v2)} | {fx(R.relred54_random_median)} ({fx(R.relred54_random_p5)} to {fx(R.relred54_random_p95)}) |", ref_src=FIXD)
    rows.append(("Random removal (same numbers removed at random, 20 draws)", f"Median {fx(R.relred54_random_median)}% (5th–95th pct {fx(R.relred54_random_p5)} to {fx(R.relred54_random_p95)}) vs {fx(R.relred54_v2)}% with the fixes", "32"))
    claim(sl, "matching fragility", "0.08", FIXD, probe="A last-bit perturbation of the PCs moved one matched log HR by 0.08", ref_src=FIXD)
    rows.append(("Matching fragility", "A last-digit change in the PCs (array memory layout) moved one matched log HR by 0.08; the gates were then exact (9,728/9,728 cells)", "–"))
    claim(sl, "gate A cells", "9,728/9,728", FIXD, probe="9,728 of 9,728 cells", ref_src=FIXD)
    vv = []
    for st in ("S29", "S32", "S38"):
        a, b = vrow(VC, "v1", st, "P5", "ECG"), vrow(VC, "v2", st, "P5", "ECG")
        vv.append(f"{st[1:]} trials {fx(a.relred54)} → {fx(b.relred54)}%")
    rows.append(("Version 1 → spec-v2 cohorts", "; ".join(vv), "–"))
    me = vrow(VC, "v2meas", "S32", "P5", "ECG")
    claim(sl, "entry values must be measured (S32)", ci(me.relred54, me.relred54_lo, me.relred54_hi), V2SUM / "contrasts.csv", probe="+ ECG 4.4% (−2.7 to 10.6), P .13", ref_src=FIXD)
    vo = vrow(VC, "v2old", "S32", "P5", "ECG")
    claim(sl, "version 1 PCs on fixed cohorts (S32)", f"{fx(vo.relred54)}%", V2SUM / "contrasts.csv", probe="ECG 4.2%", ref_src=FIXD)
    rows.append(("Fix variants", f"Entry values required to be measured: {ci(me.relred54, me.relred54_lo, me.relred54_hi)}, {pv(me.m54_p)}. Version 1 PCs kept: {fx(vo.relred54)}%", "32"))
    claim(sl, "CV-tuned penalty (v1)", "5.7% (−0.5 to 11.4)", HAND, probe="A CV-tuned penalty gives 5.7% (−0.5 to 11.4)", ref_src=HAND)
    claim(sl, "no index-day ECG (v1)", "6.9% (0.4–13.4)", HAND, probe="gives 6.9% (0.4–13.4)", ref_src=HAND)
    rows.append(("Earlier sensitivities (version 1 cohorts)", "CV-tuned penalty 5.7% (−0.5 to 11.4); index-day ECGs excluded 6.9% (0.4 to 13.4); R2 (CV-tuned, 35 trials) 4.7%. Not yet re-run on spec-v2", "32"))
    body = "".join(f'<tr><td><b>{esc(a)}</b></td><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows)
    allv = [mrow(MC, "Snew", "P5", "ECG", cfg=c).relred54 for c in CFGS] + [vrow(VC, "v2", st, "P5", "ECG").relred54 for st in ("S29", "S32", "S38")] + [me.relred54, vo.relred54]
    claim(sl, "size range 4-8%", "4–8%", "this slide's PS-method, cohort-set and fix-variant estimates", ref=f"{math.floor(min(allv))}–{math.ceil(max(allv))}%",
          ref_how="floor(min)-ceil(max) of the slide's spec-v2 estimates")
    return slide("Robustness of PS-CVD5 + ECG vs PS-CVD5 (54 items)", f"""
<table class="t tsm rob"><tr><th style="width:250px">Check</th><th>Result</th><th>Trials</th></tr>{body}</table>
<p style="font-size:19px;margin-top:12px">The direction holds in every check. The size is about <b>4–8%</b> and moves by a few points with the cohort definition, PCs, imputation draw and matching noise.</p>""")


def s_plasmode():
    sl = 14
    P = pd.read_csv(PLAS / "pooled_trtC_cliniorient_p5.csv")
    P = P[P.analysis == "null-corrected"].set_index(["conf", "arm"])
    AV = pd.read_csv(PLAS / "added_value_p5.csv")
    AV = AV[AV.analysis == "null-corrected"].set_index(["conf", "contrast"])
    PF = pd.read_csv(PLAS / "performance_trtC_cliniorient_p5.csv").set_index(["conf", "arm"])
    confs = [("lvef", "LVEF"), ("ntprobnp", "NT-proBNP"), ("bmi", "BMI"), ("egfr", "eGFR"), ("all", "All four")]
    arms = [("base", "PS-Demo", "#9fa1bd"), ("ECG", "PS-Demo + ECG", "#e8a19e"), ("P5", "PS-CVD5", NAVY), ("P5ECG", "PS-CVD5 + ECG", RED),
            ("ECGonly", "ECG only", "#8f2d2a"), ("shufECGonly", "Permuted ECG only", GOLD)]
    ser = []
    for a, lab, col in arms:
        vals = [float(P.loc[(c, a), "pct_vs_unmatched"]) for c, _ in confs]
        ser.append((lab, col, vals))
    tabd = {"P5": "PS-CVD5", "P5ECG": "PS-CVD5 + ECG", "base": "PS-Demo", "ECG": "PS-Demo + ECG", "ECGonly": "ECG only", "shufECGonly": "Permuted ECG only", "oracle": "Oracle (PS-Demo + C)"}
    for a, lab in tabd.items():
        v = P.loc[("all", a), "pct_vs_unmatched"]
        claim(sl, f"plasmode % removed, all, {lab}", fx(v), PLAS / "pooled_trtC_cliniorient_p5.csv", probe=f"| {lab if a != 'P5' and a != 'P5ECG' else '**' + lab + '**'} |", ref_src=PLD)
    claim(sl, "plasmode P5 all", fx(P.loc[("all", "P5"), "pct_vs_unmatched"]), PLAS / "pooled_trtC_cliniorient_p5.csv", probe="| **18.6** |", ref_src=PLD)
    claim(sl, "plasmode P5ECG all", fx(P.loc[("all", "P5ECG"), "pct_vs_unmatched"]), PLAS / "pooled_trtC_cliniorient_p5.csv", probe="| **27.8** |", ref_src=PLD)
    orc = P.loc[("all", "oracle"), "pct_vs_unmatched"]
    claim(sl, "oracle all", fx(orc), PLAS / "pooled_trtC_cliniorient_p5.csv", probe="| 93.7 |", ref_src=PLD)
    add = AV.loc[("all", "ECG over P5")]
    claim(sl, "ECG over PS-CVD5 added share", f"{fx(add.added_pct_of_ref_bias)}%", PLAS / "added_value_p5.csv", probe=f"**ECG over PS-CVD5** | ", ref_src=PLD)
    claim(sl, "ECG over PS-CVD5 added share value", fx(add.added_pct_of_ref_bias), PLAS / "added_value_p5.csv", probe=f"**{fx(add.added_pct_of_ref_bias)} (0.3)**", ref_src=PLD)
    adds = " · ".join(f"{lab} {fx(AV.loc[(c, 'ECG over P5'), 'added_pct_of_ref_bias'])}%" for c, lab in confs[:4])
    prow = "| **ECG over PS-CVD5** | " + " | ".join(f"{fx(AV.loc[(c, 'ECG over P5'), 'added_pct_of_ref_bias'])} ({AV.loc[(c, 'ECG over P5'), 'mcse']:.1f})" for c, _ in confs[:4])
    for c, lab in confs[:4]:
        claim(sl, f"ECG over P5 {lab}", fx(AV.loc[(c, "ECG over P5"), "added_pct_of_ref_bias"]), PLAS / "added_value_p5.csv", probe=prow, ref_src=PLD)
    cov = {a: PF.loc[("all", a), "coverage"] for a in ("unmatched", "P5", "P5ECG", "oracle")}
    for a, v in cov.items():
        claim(sl, f"coverage {a}", f"{fx(v)}%", PLAS / "performance_trtC_cliniorient_p5.csv", probe=f"{fx(v)}%", ref_src=PLD)
    claim(sl, "plasmode cells", "107", PLD, probe="107 analysed trial × confounder cells in 31 trials", ref_src=PLD,)
    claim(sl, "plasmode replicates", "50", PLD, probe="50 replicates per cell", ref_src=PLD)
    claim(sl, "plasmode cells (CSV)", str(int(P.loc[("all", "P5"), "k_cells"])), PLAS / "pooled_trtC_cliniorient_p5.csv", ref="107", ref_how="doc")
    ch = svg_grouped([(l, "") for _, l in confs], ser, W=1180, H=290, lo=-10, hi=100, title="% of the hidden-confounder bias removed vs unmatched (null-corrected)")
    return slide("Plasmode: a known truth with a hidden physiological confounder (version 1 cohorts)", f"""
<div style="font-size:14px;margin:0 0 2px">{legend_sw([(l, c) for l, c, _ in ser])}</div>
{ch}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:30px;margin-top:4px">
  <ul class="tight">
    <li>Real covariates, ECGs and follow-up; treatment simulated from the hidden confounder C (LVEF, NT-proBNP, BMI or eGFR; clinically oriented); true HR 0.80; 107 trial × C cells, 50 replicates each</li>
    <li>C is in no PS except the oracle ({fx(orc)}% removed)</li>
  </ul>
  <ul class="tight">
    <li><b>The ECG removes a further {fx(add.added_pct_of_ref_bias)}% of the bias that PS-CVD5 leaves</b> ({adds})</li>
    <li>95% CI coverage: unmatched {fx(cov["unmatched"])}%, PS-CVD5 {fx(cov["P5"])}%, PS-CVD5 + ECG {fx(cov["P5ECG"])}%, oracle {fx(cov["oracle"])}%. No representation substitutes for measuring C</li>
  </ul>
</div>""")


def s_mimic():
    sl = 15
    Sm = json.load(open(MIM / "summary/summary.json"))
    B, Bn, Ag = Sm["balance"]["primary7|cvd5|all"], Sm["balance"]["primary7|cvd5|no_index_day_ecg"], Sm["agreement"]["primary7|cvd5|all"]
    MN = {"plato": "PLATO", "aristotle": "ARISTOTLE", "rocket_af": "ROCKET AF", "transform_hf": "TRANSFORM-HF", "comet": "COMET",
          "soap2": "SOAP II [OR]", "elite2": "ELITE II", "peptic": "PEPTIC [RR; neg. control]"}
    frows, trows = [], ""
    for t, lab in MN.items():
        d = pd.read_csv(MIM / f"results/{t}_arms.csv")
        d = d[(d.base == "cvd5") & (d["pop"] == "all")].set_index("arm")
        rb, rs = float(d.iloc[0].rct_loghr), float(d.iloc[0].rct_se)
        est = {a: tuple(math.exp(d.loc[a, "loghr"] + z * d.loc[a, "se"]) for z in (0, -1.96, 1.96)) for a in ("base", "ECG", "permECG")}
        pt = Sm["per_trial"][t]
        assert abs(pt["cvd5|ECG"]["hr"] - est["ECG"][0]) < 6e-4
        frows.append((lab, math.exp(rb), math.exp(rb - 1.96 * rs), math.exp(rb + 1.96 * rs), est))
        trows += f'<tr><td>{esc(lab.split(" [")[0])}</td><td>{pt["cvd5|base"]["mean_smd"]:.3f} → {pt["cvd5|ECG"]["mean_smd"]:.3f}</td><td>{pt["cvd5|base"]["hr"]:.2f} → {pt["cvd5|ECG"]["hr"]:.2f}</td></tr>'
    arms = [("base", "PS-CVD5 analog", NAVY, "dot"), ("ECG", "+ ECG", RED, "dot"), ("permECG", "+ permuted ECG", GOLD, "tri")]
    rr = claim(sl, "MIMIC PS-CVD5 + ECG", ci(B["relred_ECG"], *B["relred_ECG_ci"]).replace("% (", "% ("), MIM / "summary/summary.json",
               probe="mean |SMD| fell by 6.6% (95% CI 2.3–12.8)", ref_src=MMD)
    claim(sl, "MIMIC lower", B["lower_smd_ECG"], MIM / "summary/summary.json", probe="lower in 6/7 trials", ref_src=MMD)
    claim(sl, "MIMIC P", f"{B['p_smd_ECG']:.3f}", MIM / "summary/summary.json", probe="p = 0.016", ref_src=MMD)
    claim(sl, "MIMIC permuted", f"{fx(B['relred_permECG'])}%", MIM / "summary/summary.json", probe="the permuted ECG gave −3.1%", ref_src=MMD)
    claim(sl, "MIMIC no index-day", ci(Bn["relred_ECG"], *Bn["relred_ECG_ci"]), MIM / "summary/summary.json", probe="6.5% (−0.2 to 13.6; 5/7; p = 0.094)", ref_src=MMD)
    claim(sl, "MIMIC |dlog HR|", f"{Ag['base']['mean_abs_diff']:.3f} → {Ag['ECG']['mean_abs_diff']:.3f} (perm {Ag['permECG']['mean_abs_diff']:.3f})", MIM / "summary/summary.json",
          probe="mean |Δ log HR| went from 0.344 to 0.326 (4/7 closer; p = 0.27)", ref_src=MMD)
    pep = Sm["per_trial"]["peptic"]
    claim(sl, "MIMIC held-out items", str(pt["cvd5|base"]["n_vars"]), MIM / "summary/summary.json", probe="held-out panel of 26 items", ref_src=MMD)
    claim(sl, "MIMIC trials", str(B["k"]), MIM / "summary/summary.json", probe="Result (7 cardiovascular trials)", ref_src=MMD)
    claim(sl, "MIMIC bootstrap", "2,000 resamples (seed 0)", MMD, probe="2,000 resamples, seed 0", ref_src=MMD)
    claim(sl, "MIMIC specification sensitivity", "±5 points", MMD, probe="moves by about ±5 percentage points", ref_src=MMD)
    claim(sl, "PEPTIC HRs", f"{pep['cvd5|base']['hr']:.2f} / {pep['cvd5|ECG']['hr']:.2f} / {pep['cvd5|permECG']['hr']:.2f}", MIM / "summary/summary.json",
          probe="PS-CVD5 gives HR 1.51 (1.35–1.69). Adding the ECG moves it to 1.39 (1.24–1.55)", ref_src=MMD)
    return slide("External replication: MIMIC-IV (PS-CVD5 analog ± ECG)", f"""
<div style="display:grid;grid-template-columns:1.12fr 1fr;gap:26px">
  <div>{_legend(arms)}{_forest(frows, arms, W=700)}</div>
  <div>
    <p style="font-size:17px;margin:0 0 6px">{B["k"]} cardiovascular trials + PEPTIC (negative control). PS-CVD5 analog = demographics + HTN, T2D, CAD, AF, HF from earlier admissions. {pt["cvd5|base"]["n_vars"]} held-out labs, vitals, ventilation and utilisation items (no echo).</p>
    <table class="t tsm"><tr><th></th><th>PS-CVD5 analog + ECG</th></tr>
      <tr><td>Mean |SMD| reduction</td><td><b>{rr}</b>; lower in {B["lower_smd_ECG"]}; P = {B["p_smd_ECG"]:.3f}</td></tr>
      <tr><td>Permuted ECG</td><td>{fx(B["relred_permECG"])}%</td></tr>
      <tr><td>Index-day ECGs excluded</td><td>{ci(Bn["relred_ECG"], *Bn["relred_ECG_ci"])}</td></tr>
      <tr><td>Mean |Δ log HR|</td><td>{Ag["base"]["mean_abs_diff"]:.3f} → {Ag["ECG"]["mean_abs_diff"]:.3f} (permuted {Ag["permECG"]["mean_abs_diff"]:.3f}); closer {Ag["ECG_vs_base"]["closer"]}</td></tr>
      <tr><td>PEPTIC (expected null)</td><td>HR {pep["cvd5|base"]["hr"]:.2f} → {pep["cvd5|ECG"]["hr"]:.2f} (permuted {pep["cvd5|permECG"]["hr"]:.2f})</td></tr></table>
    <table class="t tsm" style="margin-top:8px"><tr><th>Trial</th><th>mean |SMD|</th><th>HR</th></tr>{trows}</table>
    <p class="small" style="margin-top:4px">Bootstrap CI: 2,000 resamples (seed 0, the v20 convention). The estimate moves by about ±5 points between near-identical specifications.</p>
  </div>
</div>""")


def s_takehome(MC, IM):
    sl = 16
    I = IM.set_index("set")
    p5 = I.loc["new set (rescored, spec-v2)"]
    d = mrow(MC, "Snew", "P1", "ECG")
    h = mrow(MC, "Snew", "hdPS200", "ECG")
    m = mrow(MC, "Snew", "clinical_nolvef_mi", "ECG")
    c10 = mrow(MC, "Snew", "PS10", "ECG")
    bmin = min(I.bshuf_p)
    claim(sl, "take-home PS-CVD5 + ECG (30)", ci(p5.relred54, p5.lo, p5.hi), IMPACT, probe=norm(ci(p5.relred54, p5.lo, p5.hi)), ref_src=QUEUE)
    claim(sl, "take-home PS-Demo + ECG (30)", f"{fx(d.relred54)}%", MISUM / "contrasts.csv", probe=f"{norm(fx(d.relred54))}% (", ref_src=QUEUE)
    claim(sl, "take-home hdPS + ECG (30)", f"{fx(h.relred54)}%", MISUM / "contrasts.csv", probe=f"{norm(fx(h.relred54))}% (", ref_src=QUEUE)
    claim(sl, "take-home PS-Clinical MI + ECG (30)", f"{fx(m.relred54)}%", MISUM / "contrasts.csv", probe=f"{norm(fx(m.relred54))}% (", ref_src=QUEUE)
    claim(sl, "min benchmark-permutation P over sets", fp(bmin), IMPACT, probe="benchmark-permutation P ≥ .95 everywhere", ref_src=QRES)
    claim(sl, "CVD10 + ECG benchmark-permutation P (30)", fp(c10.bshuf_p), MISUM / "contrasts.csv", ref=fp(bshuf_deck("v2", "main", "PS10", "ECG", "v2c")),
          ref_how="recomputed (sens_primary32.bshuf, same draws) from the deck's embedded log HRs")
    return slide("Take-home: the narrowed claim", f"""
<ol class="aims" style="margin-top:4px">
  <li><b>The ECG improves held-out balance when the PS is thin</b>, i.e. demographics and a few diagnoses: PS-CVD5 + ECG {ci(p5.relred54, p5.lo, p5.hi)} on the 30 analysed trials (PS-Demo + ECG {fx(d.relred54)}%). It is consistently better than its permuted placebo.</li>
  <li><b>The gain shrinks or vanishes with code-rich or measured covariates</b>: hdPS + ECG {fx(h.relred54)}%; PS-Clinical (no LVEF) + ECG {fx(m.relred54)}%, concentrated in observed LVEF and echo structure.</li>
  <li><b>No trial-specific agreement with the RCTs.</b> |Δ log HR| does not improve, and the benchmark-permutation P is ≥ {fp(bmin)} in every trial set. (CVD10 + ECG gave P = {fp(c10.bshuf_p)} on the 30: post hoc, exploratory only.)</li>
  <li><b>Supporting:</b> the plasmode (the ECG removes part of a hidden physiological confounder's bias beyond PS-CVD5) and MIMIC-IV (similar balance gain, no agreement gain).</li>
  <li><b>Caveats:</b> one health system; a provisional, unfrozen trial set rated by LLM runs (clinician review pending); a post hoc switch of the primary to PS-CVD5; effect sizes of a few points move with design details.</li>
</ol>""")


def s_decisions(Q):
    sl = 17
    claim(sl, "hypertension rule -> 27 trials", "27", QRES, probe="ALLHAT, ASCOT-BPLA and VALUE would leave (27 trials)", ref_src=QRES)
    claim(sl, "E+G 12 vs 10 without OU rescore", "12 vs 10", QRES, probe="only Excellent + Good changes (12 vs 10)", ref_src=QRES)
    return slide("Open decisions (before the methods lock)", f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:36px">
<ol class="dec">
  <li><b>Freeze the trial set</b> (framework §7.6): hash or commit the rater files; run DC-ES-cross, DC-EL-met and DC-SI-hf-anyposition; transcribe the S5 publication facts; complete the clinician review. Then switch the default to the frozen set.</li>
  <li><b>TRANSFORM-HF</b>: keep it at Moderate (documented time-zero error, TZ = 2), or treat a data-confirmed TZ = 2 as Limited? It needs a rebuild either way.</li>
  <li><b>Hypertension switch trials</b> (ALLHAT, ASCOT-BPLA, VALUE; ONTARGET through TZ.b): Moderate as written, or a "TZ.c ≥50% + ≥3 other points → Limited" rule (27 trials)?</li>
  <li><b>B1, second half</b>: the TECOS and CARMELINA sulfonylurea-background subgroups and the TECOS background-therapy requirement. One EL point makes either trial Limited.</li>
  <li><b>Clarifications C1–C10</b>, especially C1 (EL vs SI for undocumented code-defined criteria) and C3 (any-position I50).</li>
</ol>
<ol class="dec" start="6">
  <li><b>hdPS and PS-Flags on the smaller fixed cohorts</b>: likely artefacts (within-cohort ≥1% filter, fixed C = 1). Run the sensitivity with the version 1 flag columns.</li>
  <li><b>Cohort fixes as primary</b> (pipeline.md §2 and §10.2 still PENDING); MI imputation population (fixed cohort vs roster).</li>
  <li><b>OU re-score</b> for LODESTAR and PROVE IT (Excellent + Good: 12 vs 10); entry bounds applied with "unknown passes".</li>
  <li><b>Title</b> (the "Multimodal" working title no longer fits) and the <b>manuscript file</b> (paper.md vs paper2.md).</li>
  <li><b>Clinician review</b> of the quality adjudication and the physiologic trial labels; confirm the CLMBR-T removal with the PI.</li>
</ol>
</div>""")


# ================================================================ validation combos (balance explorer)
def balance_combos(D, g, g2):
    """Combinations for the headless JS check, each with (a) build_balance_explorer.pair_stats on the full-precision grid (the
    explorer's validated computation), (b) the same on the integers embedded in this deck, (c) the published / Python-summary value."""
    full = {"v1": BE.Grid(g["G"], g["U"], g["ex"]), "v2": BE.Grid(g2["G"], g2["U"], g2["ex"])}
    emb = {"v1": BE.Grid.from_data(D, "v1"), "v2": BE.Grid.from_data(D, "v2")}
    tr = D["trials"]
    combos = []

    def add(src, coh, cfg, rg, a, b, ts, panel, leak, exp, sided="one", tag=""):
        T = BE.trial_set(tr, ts)
        rf = BE.pair_stats(full[coh], cfg, rg, a, b, T, panel, leak)
        re_ = BE.pair_stats(emb[coh], cfg, rg, a, b, T, panel, leak)
        clean = lambda r: {k: (None if isinstance(v, float) and not np.isfinite(v) else float(v)) for k, v in r.items()}
        combos.append(dict(source=src, tag=tag, coh=coh, cfg=cfg, rung=rg, arm=a, ref=b, trials=ts, panel=panel, leak=bool(leak), thr=0.1,
                           sided=sided, py_full=clean(rf), py_emb=clean(re_), expected=exp))
    # required: spec-v2 primary on the 30 and the 32; paper 1 PS-Demo (version 1 settings)
    I = pd.read_csv(IMPACT).set_index("set")
    x = I.loc["new set (rescored, spec-v2)"]
    add("impact_v2cohorts.csv (QUEUE: 5.5% on 30)", "v2", "main", "P5", "ECG", "base", "v2c", "54", True, dict(rr=x.relred54, lo=x.lo, hi=x.hi, p_m=x.m54_p, lower=x.m54_better), tag="REQUIRED primary 30")
    x = I.loc["paper 1's 32"]
    add("impact_v2cohorts.csv (QUEUE: 6.6% on 32)", "v2", "main", "P5", "ECG", "base", "s32", "54", True, dict(rr=x.relred54, lo=x.lo, hi=x.hi, p_m=x.m54_p, lower=x.m54_better), tag="REQUIRED spec-v2 32")
    for st in ("all 38", "provisional 29 (v2.0 adjudication)", "Excellent + Good (rescored)"):
        x = I.loc[st]
        ts = {"all 38": "all", "provisional 29 (v2.0 adjudication)": "v2", "Excellent + Good (rescored)": "q:Excellent,Good"}[st]
        add("impact_v2cohorts.csv", "v2", "main", "P5", "ECG", "base", ts, "54", True, dict(rr=x.relred54, lo=x.lo, hi=x.hi, p_m=x.m54_p, lower=x.m54_better))
    # published values (build_balance_explorer.EXPECT; version 1 cohorts) for the ECG arms and the deck's rungs
    for (src, ts, cfg, rg, a, panel, leak, exp) in BE.EXPECT:
        aa, bb = (a.split("|") + ["base"])[:2]
        if rg in RUNGS_D and aa in ARMS_D and bb in ARMS_D:
            add(src, "v1", cfg, rg, aa, bb, ts, panel, leak, exp, sided="two" if "p_m2" in exp else "one",
                tag="REQUIRED paper 1 PS-Demo 11.4%" if (src == "Paper 1 eTable 3A" and ts == "s32" and rg == "P1" and aa == "ECG" and cfg == "main") else "")
    # spec-v2 Python summaries (scripts/v2_cohorts/summarize.py; scripts/v2_psclin_mi/psclin_mi.py), main configuration, every deck
    # rung, ECG / permuted ECG vs base and ECG vs permuted, 54 and 58 items, leakage-corrected; plus all six methods for PS-CVD5 on the 30
    MC, VC = get_contrasts()
    VCm = VC[(VC.cohort == "v2") & (VC.kind == "within") & VC.rung_a.isin(["Flags"])]
    MCm = MC[MC.kind.isin(["ladder", "within"]) & MC.rung_a.isin(["P1", "P5", "PS10", "hdPS200", "clinical_nolvef_mi"]) & (MC.rung_a == MC.rung_b)]
    for srcname, Q in (("v2_cohorts summary", VCm), ("psclin_mi summary", MCm)):
        for _, s in Q.iterrows():
            if s.arm_a not in ARMS_D or s.arm_b not in ARMS_D or s.set not in SETMAP:
                continue
            if not (s.config == "main" or (s.rung_a == "P5" and s.set == "Snew")):
                continue
            rg = "clinical_nolvef" if s.rung_a == "clinical_nolvef_mi" else s.rung_a
            for panel in ("54", "58"):
                pre, mm = ("relred54", "m54") if panel == "54" else ("relred58", "m58")
                add(srcname, "v2", s.config, rg, s.arm_a, s.arm_b, SETMAP[s.set], panel, True,
                    dict(rr=s[pre], lo=s[pre + "_lo"], hi=s[pre + "_hi"], p_m=s[f"{mm}_p"], lower=s[f"{mm}_better"]), sided=s.sided)
    return combos


def emu_refs(D):
    """agreement references: Python summaries (absd, bshuf_p) and this script's per-arm metrics, for the JS check."""
    MC, VC = get_contrasts()
    out = []
    for _, s in MC[MC.kind.isin(["ladder", "within"]) & (MC.config == "main") & MC.rung_a.isin(["P1", "P5", "PS10", "hdPS200", "clinical_nolvef_mi"])
                   & (MC.arm_b == "base") & MC.arm_a.isin(["ECG", "shufECG"]) & (MC.rung_a == MC.rung_b)].iterrows():
        rg = "clinical_nolvef" if s.rung_a == "clinical_nolvef_mi" else s.rung_a
        T = BE.trial_set(D["trials"], SETMAP[s.set])
        m = agree_py(D, "v2", "main", rg, s.arm_a, T)
        b = agree_py(D, "v2", "main", rg, "base", T)
        out.append(dict(coh="v2", cfg="main", rung=rg, arm=s.arm_a, trials=SETMAP[s.set], sum_absd_a=s.absd_a, sum_absd_b=s.absd_b,
                        sum_better=s.absd_better, sum_bshuf=s.bshuf_p, sum_absd_p=s.absd_p, sum_r=s.a_r, sum_ea=s.a_ea, sum_cons=s.a_cons, py=m, py_base=b))
    return out


# ================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.parse_args()
    os.umask(0o077)
    SCR.mkdir(parents=True, exist_ok=True)
    g = BE.load_grid()
    g2 = BE.load_grid_v2(g)
    trials, Q = trials_deck(g, g2)
    D = build_data(g, g2, trials)
    GRID2.update(grid=BE.Grid(g2["G"], g2["U"], g2["ex"]), D=D)
    MC, VC = get_contrasts()
    IM = pd.read_csv(IMPACT)
    DM = pd.read_csv(MISUM / "domains.csv")
    EX = pd.read_csv(EXCL, dtype={"pct_removed_v2": str})
    # suppressed shares ("<x": counts of 1-10) count as below 1% (shown as "<1%"); exact small shares are also shown as "<1%"
    EX["pct_removed_v2"] = [float(v[1:]) / 2 if v.startswith("<") else float(v) for v in EX.pct_removed_v2]
    RR = pd.read_csv(RRS)
    static = [s_changes(trials, Q, MC, VC, EX), s_flow(trials, Q), s_framework(trials, Q), s_tiers(trials, Q), s_fixes(trials, EX, RR),
              s_methods_design(), s_methods_panel()]
    after_bal = [s_results2(MC, VC, IM, DM)]
    after_emu = [s_robust(MC, VC, RR, IM)]
    after_agq = [s_plasmode(), s_mimic(), s_takehome(MC, IM), s_decisions(Q)]
    js_bal = explorer_js()
    js = json.dumps(D, separators=(",", ":"), allow_nan=False)
    html = (TEMPLATE.replace("__TITLE__", s_title()).replace("__STATIC1__", "".join(static)).replace("__STATIC2__", "".join(after_bal))
            .replace("__STATIC3__", "".join(after_emu)).replace("__STATIC4__", "".join(after_agq)).replace("__EXPLORER_JS__", js_bal)
            .replace("__LOGO__", logo_uri(None)).replace("__DATA__", js))
    for bad in ("http://", "https://", "@import", "<link", "src=\"//"):
        assert bad not in html.replace("http://www.w3.org/2000/svg", ""), bad
    old = os.umask(0o022)
    OUT.write_text(html)
    os.umask(old)
    print(f"wrote {OUT} ({len(html) / 1e6:.2f} MB)")
    C = pd.DataFrame(CL)
    C.to_csv(SCR / "claims.csv", index=False)
    with open(SCR / "claims.md", "w") as f:
        f.write("| Slide | Claim | Value | Source | Independent check | Match |\n|---|---|---|---|---|---|\n")
        for r in CL:
            f.write(f"| {r['slide']} | {r['claim']} | {r['value']} | {r['source']} | {r['check'].replace('|', '/')} | "
                    f"{'yes' if r['match'] else ('NO' if r['match'] is False else 'n/a')} |\n")
    print(f"claims: {len(C)}; checked {int(C.match.notna().sum())}; matched {int((C.match == True).sum())}; "  # noqa: E712
          f"mismatched {int((C.match == False).sum())}")  # noqa: E712
    if (C.match == False).any():  # noqa: E712
        print(C[C.match == False].to_string())  # noqa: E712
    combos = balance_combos(D, g, g2)
    json.dump(combos, open(SCR / "balance_combos.json", "w"), indent=0)
    json.dump(emu_refs(D), open(SCR / "emu_refs.json", "w"), indent=0)
    print(f"balance combos: {len(combos)}")


def explorer_js():
    """the balance explorer's JS (build_balance_explorer.TEMPLATE), from the arm table to just before its headless API, restricted to
    the ECG arms and the pipeline.md rungs; statistics code unchanged."""
    T = BE.TEMPLATE
    js = T[T.index("const ARM = {"): T.index("/* headless-check API")]
    P = [
        ('const ARMS_ALL = ["unmatched", "base", "ECG", "shufECG", "CLMBR", "ECG+CLMBR", "shufCLMBR"];', 'const ARMS_ALL = ["unmatched", "base", "ECG", "shufECG"];'),
        ('const RUNGS = ["P1", "P5", "PS10", "Flags", "hdPS200", "clinical_nolvef", "clinical"], CFGS = Object.keys(CFG);',
         'const RUNGS = ["P1", "P5", "PS10", "Flags", "hdPS200", "clinical_nolvef"], CFGS = Object.keys(CFG);'),
        ('const MAIN = ["P1", "P5", "PS10", "hdPS200", "clinical_nolvef"], SUPP = ["Flags", "clinical"];',
         'const MAIN = ["P1", "P5", "PS10", "hdPS200", "clinical_nolvef"], SUPP = ["Flags"];'),
        ('let h = `<option value="v2">Provisional v2 set (${n(t => t.v2)}, not frozen)</option>${D.has_v2c ? `<option value="v2c">Rescored on spec-v2 cohorts (${n(t => t.v2c)}, not frozen)</option>` : ""}<option value="s32">Paper 1 primary set (${n(t => t.s32)} trials)</option>',
         'let h = `<option value="v2c">Analysed set, rescored (${n(t => t.v2c)}; provisional)</option><option value="v2">Provisional v2.0 set (${n(t => t.v2)})</option><option value="s32">Paper 1\'s set (${n(t => t.s32)} trials)</option>'),
        ('<optgroup label="Emulation quality tier">', '<optgroup label="Quality tier (v2.0, rescored)">'),
        ('<option value="exp">Expanded, ~330 (1:1, cal. 0.2 only; supplement)</option>', ''),
        ('$("#c-trials").value === "v2" && panel === "54"', '$("#c-trials").value === "v2c" && panel === "54"'),
        ('provisional v2 set (29 trials, not frozen)', 'rescored analysed set (30 trials; provisional, not frozen)'),
        ('; tick PS-Flags (supplement) or PS-Clinical (with LVEF, v1 reference) under "Ladder levels" (shaded grey)', '; tick PS-Flags (supplement) under "Ladder levels" (shaded grey)'),
        ('<option value="58">58 items (paper 1 primary; supplement)</option>', '<option value="58">58 items (secondary; paper 1 primary)</option>'),
        # ECG-only paper: no CLMBR-T arms, labels or notes in the deck
        ('  shufECG: {lab: "+ permuted ECG", col: "#d69a00", mk: "tri", hollow: true},\n  CLMBR: {lab: "+ CLMBR-T", col: "#2a78d6", mk: "square"},\n'
         '  "ECG+CLMBR": {lab: "+ CLMBR-T + ECG", col: "#1baf7a", mk: "diamond"},\n  shufCLMBR: {lab: "+ permuted CLMBR-T", col: "#2a78d6", mk: "square", hollow: true}\n',
         '  shufECG: {lab: "+ permuted ECG", col: "#d69a00", mk: "tri", hollow: true}\n'),
        (', CLMBR: "+ CLMBR-T", "ECG+CLMBR": "+ CLMBR-T + ECG", shufCLMBR: "+ perm. CLMBR-T"};', '};'),
        ('const PAPER2 = new Set(["CLMBR", "ECG+CLMBR", "shufCLMBR"]);  /* CLMBR-T arms: exploratory, not in the (ECG-only) paper */', 'const PAPER2 = new Set([]);'),
        ('that CLMBR-T and the hdPS codes also see', 'that the hdPS codes also see'),
        ('  if (arms.some(a => PAPER2.has(a))) h += `<div class="note">CLMBR-T arms are exploratory and not in the paper.</div>`;\n', ''),
    ]
    for a, b in P:
        assert js.count(a) == 1, a
        js = js.replace(a, b)
    return js


TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TRACE-ECG | CarDS Lab update | October 9, 2026</title>
<style>
:root{--navy:#0E103C;--red:#DC5A55;--ink:#0E103C;--muted:#55576f;--faint:#8a8ca0;--line:#dcdde5;--band:#f3f3f7}
html,body{margin:0;height:100%;background:#fff;overflow:hidden}
body{font-family:Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif;color:var(--ink)}
#stage{position:absolute;left:50%;top:50%;width:1280px;height:720px;transform-origin:center center;background:#fff}
.slide{position:absolute;inset:0;background:#fff;display:none;overflow:hidden}
.slide.active{display:block}
.ttl{position:absolute;left:19px;top:24px;height:34px;background:var(--navy);color:#fff;font-weight:700;font-size:19px;
  display:flex;align-items:center;padding:0 14px;box-sizing:border-box;white-space:nowrap}
.rule{position:absolute;left:19px;right:19px;height:2px;background:var(--navy)}
.rule.top{top:58px}.rule.bot{top:664px}
.num{position:absolute;right:21px;top:28px;color:var(--navy);font-size:18px;font-weight:700}
.foot{position:absolute;right:66px;bottom:17px;color:var(--navy);font-size:16px;letter-spacing:.3px}
.foot b{font-weight:700;margin-right:.3em}
.prov{position:absolute;left:22px;bottom:19px;color:var(--red);font-size:12px;font-weight:600}
.logo{position:absolute;right:19px;bottom:10px;width:40px;height:40px}
.body{position:absolute;left:44px;right:44px;top:80px;bottom:62px}
h2{font-size:26px;font-weight:700;margin:0 0 10px 0}
.h3{font-size:16px;font-weight:700;margin:0 0 6px;color:var(--navy);text-transform:uppercase;letter-spacing:.3px}
p,li{font-size:20px;line-height:1.36;margin:0 0 10px 0}
ul,ol{margin:0;padding-left:26px}
ul.chg li{font-size:18.5px;margin:0 0 9px}
ul.tight li,ol.tight li{font-size:15px;line-height:1.32;margin:0 0 5px}
ol.aims{padding-left:30px}ol.aims li{font-size:21px;line-height:1.36;margin:0 0 15px}
ol.dec li{font-size:16px;line-height:1.34;margin:0 0 11px}
code{font-size:.9em;background:#f3f3f7;padding:0 3px}
.red{color:var(--red)}
.muted{color:var(--muted)}
.small{font-size:13.5px;line-height:1.35;color:var(--muted)}
.xs{font-size:11.5px;line-height:1.3;color:var(--muted)}
.card{border:2px solid var(--navy);padding:10px 14px;box-sizing:border-box}
.card h3{margin:0 0 6px 0;font-size:18px}
.card p{font-size:15.5px;margin:0}
table.t{border-collapse:collapse;width:100%}
table.t td,table.t th{font-size:17px;padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
table.t th{background:var(--navy);color:#fff;font-weight:600}
table.t.tsm td,table.t.tsm th{font-size:13.5px;padding:4px 7px}
table.t.tq td,table.t.tq th{font-size:12.5px;padding:3px 6px}
table.t.tq td.n{font-weight:700;white-space:nowrap}
table.t td.nw{white-space:nowrap}
table.t tr.hl td{background:#fbeceb}
table.rob td{font-size:14px;padding:6px 8px}
.qitems{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.qitems table{border-collapse:collapse;width:100%}
.qitems th{font-size:11px;font-weight:600;background:var(--navy);color:#fff;padding:3px 3px;text-align:center}
.qitems th.l,.qitems td.l{text-align:left}
.qitems td{font-size:11.5px;padding:2.2px 3px;border-bottom:1px solid var(--line);text-align:center;color:var(--navy);white-space:nowrap}
.qitems td.n{font-weight:600}
.qitems tr.tb td{border-top:2px solid var(--navy)}
.qitems td.P{color:var(--red);font-weight:700}
.qitems td.pt{font-weight:700}
.tier{display:inline-block;min-width:54px;padding:0 3px;font-size:10px;font-weight:600}
.tier.t0{background:var(--navy);color:#fff}.tier.t1{background:#5b5d86;color:#fff}.tier.t2{background:var(--band);color:var(--navy);outline:1px solid var(--line)}.tier.t3{background:#fbe3e2;color:#a8322e}
/* title slide */
#s-title .tlogo{position:absolute;left:539px;top:170px;width:202px;height:204px}
#s-title .l1{position:absolute;left:0;right:0;top:405px;text-align:center;font-size:30px;font-weight:700;color:var(--navy)}
#s-title .l2{position:absolute;left:60px;right:60px;top:455px;text-align:center;font-size:29px;color:#595959;line-height:1.3}
#s-title .l3{position:absolute;left:0;right:0;top:560px;text-align:center;font-size:24px;color:#595959}
#s-title .l3 sup{font-size:.6em}
#s-title .l4{position:absolute;left:0;right:0;top:610px;text-align:center;font-size:15px;color:var(--red)}
/* interactive panels */
.panel{position:absolute;left:16px;right:16px;top:68px;bottom:60px;display:grid;grid-template-columns:196px 1fr 340px;gap:10px}
.ctrl{font-size:12px;overflow-y:auto;overflow-x:hidden;border-right:1px solid var(--line);padding-right:8px}
.ctrl label.h{display:block;font-weight:700;font-size:10.5px;letter-spacing:.3px;text-transform:uppercase;color:var(--navy);margin:5px 0 1px}
.ctrl select{width:100%;font:inherit;font-size:11.5px;padding:1px 2px;border:1px solid #b9bbc8;border-radius:3px;background:#fff;color:var(--ink)}
.ctrl .cb{display:flex;align-items:center;gap:4px;margin:0;font-size:11.5px;cursor:pointer;line-height:1.35}
.ctrl .cb input{margin:0}
.ctrl .cb.dis{opacity:.35}
.ctrl .p2{font-size:9.5px;color:var(--faint)}
.ctrl .desc{font-size:10px;color:var(--muted);line-height:1.25;margin:1px 0 0}
.ctrl #c-rdesc,.ctrl #c-cohd{display:none}
.ctrl input[type=range]{width:100%;margin:0}
.ctrl .dim{opacity:.4}
#c-lad{display:grid;grid-template-columns:1fr 1fr;column-gap:4px}
.sw{display:inline-block;width:14px;height:12px;flex:none}
.views{display:flex;gap:0;margin:0 0 4px}
.views label{border:1px solid var(--navy);padding:3px 10px;font-size:12px;cursor:pointer;color:var(--navy);user-select:none}
.views label+label{border-left:none}
.views input{display:none}
.views label.on{background:var(--navy);color:#fff}
.chart{position:relative;overflow:hidden;display:flex;flex-direction:column;min-height:0}
#s-bal .chart svg#svg{flex:1;min-height:0;width:100%}
.chart .cap{font-size:10.5px;color:var(--muted);line-height:1.3;margin:2px 0 0;max-height:42px;overflow:hidden}
.side{font-size:12px;border-left:1px solid var(--line);padding-left:10px;overflow-y:auto;overflow-x:hidden}
.side h4{margin:3px 0 4px;font-size:12.5px;text-transform:uppercase;letter-spacing:.3px}
.side .sel{font-size:11px;color:var(--muted);margin:0 0 5px}
.side table{border-collapse:collapse;width:100%}
.side td,.side th{font-size:10.5px;padding:2px 3px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.side th{white-space:normal;vertical-align:bottom}
.side th{font-weight:700;color:var(--navy);border-bottom:2px solid var(--navy)}
.side td:first-child,.side th:first-child{text-align:left}
.side .note{font-size:10.5px;color:var(--muted);line-height:1.3;margin:5px 0;white-space:normal}
.side .hl{background:#fbeceb}
.side .empty{margin-top:40px;font-size:17px;font-weight:700;color:var(--navy);text-align:center}
.side td .ci{display:block;font-size:10px;color:var(--muted)}
.qv{display:flex;gap:6px;font-size:11.5px}.qv label{display:flex;align-items:center;gap:2px;cursor:pointer;white-space:nowrap}.qv input{margin:0}
#agq-tab table.t td,#agq-tab table.t th{font-size:12px;padding:3px 7px}
svg text{font-family:Montserrat,"Helvetica Neue",Helvetica,Arial,sans-serif}
#tip{position:fixed;pointer-events:none;background:#fff;border:1px solid var(--navy);color:var(--ink);font:12px/1.35 Montserrat,"Helvetica Neue",Arial,sans-serif;
  padding:6px 8px;max-width:340px;display:none;z-index:10;box-shadow:0 2px 6px rgba(0,0,0,.15)}
#nav{position:fixed;left:50%;bottom:4px;transform:translateX(-50%);font:12px Montserrat,Arial,sans-serif;color:#9a9cb0;z-index:5;user-select:none}
#nav span{cursor:pointer;padding:0 8px}
@media print{#nav{display:none}}
</style>
</head>
<body>
<div id="stage">
__TITLE__
__STATIC1__
<section class="slide" data-title="Results 1: covariate balance explorer (spec-v2 fixed cohorts by default)" id="s-bal">
  <div class="panel">
    <div class="ctrl" id="ctrl"></div>
    <div class="chart">
      <div class="views" id="views">
        <label class="on"><input type="radio" name="view" value="love" checked>Love plot</label>
        <label><input type="radio" name="view" value="ladder">Information ladder</label>
        <label><input type="radio" name="view" value="method">Method comparison</label>
      </div>
      <svg id="svg" viewBox="0 0 760 600"></svg>
      <div class="cap" id="cap"></div>
    </div>
    <div class="side" id="sum"></div>
  </div>
</section>
__STATIC2__
<section class="slide" data-title="Results 3: trial emulation explorer (agreement with the RCTs)" id="s-emu">
  <div class="panel">
    <div class="ctrl" id="emu-ctrl"></div>
    <div class="chart"><svg id="emu-svg" viewBox="0 0 714 580" style="width:100%;height:100%"></svg></div>
    <div class="side" id="emu-sum"></div>
  </div>
</section>
__STATIC3__
<section class="slide" data-title="Agreement with the RCTs by emulation quality" id="s-agq">
  <div class="panel" style="grid-template-columns:200px 1fr">
    <div class="ctrl" id="agq-ctrl"></div>
    <div class="chart" style="padding:2px 10px;overflow-y:auto"><svg id="agq-svg" viewBox="0 0 900 300" style="width:100%;height:auto;flex:none"></svg><div id="agq-tab"></div></div>
  </div>
</section>
__STATIC4__
</div>
<div id="tip"></div>
<div id="nav"><span id="nav-prev">&#8249;</span><span id="nav-count"></span><span id="nav-next">&#8250;</span></div>

<script>
"use strict";
const D = __DATA__;
const LOGO = "__LOGO__";
const NAVY = "#0E103C", RED = "#DC5A55";
/* ===== balance explorer (scripts/build_balance_explorer.py, restricted to the ECG arms) ===== */
__EXPLORER_JS__
/* ===== trial emulation explorer and agreement by quality (adapted from the 2026-10-01 deck; spec-v2 cells) ===== */
const EARMS = ["base", "ECG", "shufECG"];
const TIERN = ["Excellent", "Good", "Moderate", "Limited"];
const TSRC = {tier: "Framework v2.0, rescored (spec-v2 cohorts)", tq1: "Framework v2.0, version 1 cohorts", t19: "v19 tiers (paper 1)"};
function estOf(coh, cfg, rung, a, t) { const x = D.EST[coh] && D.EST[coh][cfg] && D.EST[coh][cfg][rung] && D.EST[coh][cfg][rung][a]; return (x && x[t]) || [NaN, NaN]; }
const pearson = (x, y) => { const n = x.length; if (n < 3) return NaN; const mx = x.reduce((a, b) => a + b) / n, my = y.reduce((a, b) => a + b) / n;
  let sxy = 0, sxx = 0, syy = 0; for (let i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) ** 2; syy += (y[i] - my) ** 2; } return sxy / Math.sqrt(sxx * syy); };
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
/* benchmark permutation (scripts/v20/sens_primary32.bshuf; two-sided = scripts/v21/paper2_grid.bshuf2): permute the RCT log HRs among
   the k trials; stat = mean(|la - q| - |lb - q|); one-sided P = P(null <= obs); two-sided = 2 x the smaller tail; 20,000 draws (Monte Carlo) */
function benchShuffle(la, lb, rb, ndraw, two) {
  const k = la.length; if (k < 2) return NaN;
  const st = q => { let s = 0; for (let i = 0; i < k; i++) s += Math.abs(la[i] - q[i]) - Math.abs(lb[i] - q[i]); return s / k; };
  const obs = st(rb), rng = mulberry32(20261001), idx = rb.map((_, i) => i); let c = 0, c2 = 0;
  for (let r = 0; r < ndraw; r++) {
    for (let i = k - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); const t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    const v = st(idx.map(i => rb[i])); if (v <= obs + 1e-12) c++; if (v >= obs - 1e-12) c2++;
  }
  return two ? Math.min(1, 2 * Math.min(c, c2) / ndraw) : c / ndraw;
}
/* RCT-DUPLICATE metrics for one arm over trials T (as scripts/v20/sens_primary32.agree_metrics) */
function agree(coh, cfg, rung, a, T) {
  const ok = T.filter(t => fin(estOf(coh, cfg, rung, a, t)[0]));
  const L = ok.map(t => estOf(coh, cfg, rung, a, t)), tr = ok.map(t => D.trials[t]);
  const d = L.map(([l], i) => Math.abs(l - tr[i].rb));
  return {n: ok.length, r: pearson(L.map(x => x[0]), tr.map(x => x.rb)), gap: mean(d),
    ea: ok.length ? d.filter((x, i) => x <= 1.96 * tr[i].rs).length / ok.length : NaN,
    sd: ok.length ? L.filter(([l, se], i) => Math.abs(l - tr[i].rb) / Math.sqrt(se * se + tr[i].rs * tr[i].rs) < 1.96).length / ok.length : NaN};
}
/* paired |dlog HR| contrast of arm a vs PS alone: closer, exact sign-flip P, benchmark-permutation P (one-sided for the ECG,
   two-sided for the permuted-ECG placebo, as the Python summaries) */
function closer(coh, cfg, rung, a, T, nd) {
  const two = a === "shufECG";
  const ok = T.filter(t => fin(estOf(coh, cfg, rung, a, t)[0]) && fin(estOf(coh, cfg, rung, "base", t)[0]));
  const g = (x, t) => Math.abs(estOf(coh, cfg, rung, x, t)[0] - D.trials[t].rb);
  const d = ok.map(t => g("base", t) - g(a, t));
  const la = ok.map(t => estOf(coh, cfg, rung, a, t)[0]), lb = ok.map(t => estOf(coh, cfg, rung, "base", t)[0]), rb = ok.map(t => D.trials[t].rb);
  const sf = ok.length > 1 ? (two ? Math.min(1, 2 * Math.min(signflip(d), signflip(d.map(x => -x)))) : signflip(d)) : NaN;
  return {k: ok.length, closer: d.filter(x => x > 0).length, p: sf, perm: ok.length > 1 ? benchShuffle(la, lb, rb, nd || 20000, two) : NaN, two};
}
const pc = x => fin(x) ? Math.round(100 * x) + "%" : "–", f2 = x => fin(x) ? x.toFixed(2) : "–";
const rungOptE = () => [...MAIN, ...SUPP].map(r => `<option value="${r}" ${r === PRIMARY ? "selected" : ""}>${rungOpt(r)}</option>`).join("");
const cohOpt = `<option value="v2" selected>Spec-v2 fixed cohorts (primary)</option><option value="v1">Version 1 cohorts (as built)</option>`;
function emuInit() {
  const sel = (id, opts) => `<select id="${id}">${opts}</select>`;
  $("#emu-ctrl").innerHTML = `
  <label class="h">Cohorts</label>${sel("emu-coh", cohOpt)}
  <label class="h">Trials</label>${sel("emu-trials", trialOptions())}
  <label class="h">PS base</label>${sel("emu-rung", rungOptE())}
  <label class="h">PS method</label>${sel("emu-cfg", CFGS.map(c => `<option value="${c}">${CFG[c]}</option>`).join(""))}
  <label class="h">Methods</label>
  <div id="emu-arms">${EARMS.map(a => `<label class="cb"><input type="checkbox" name="emu-arm" value="${a}" checked>${swatch(a)}${ARM[a].lab}</label>`).join("")}</div>
  <label class="h">Sort by</label>${sel("emu-sort", `<option value="area">Area, then RCT HR</option><option value="rct">RCT HR</option><option value="gap">|Δ| with PS alone</option><option value="chg">Change in |Δ| with ECG</option><option value="name">Name</option>`)}
  <div class="desc" style="margin-top:8px">Grey band = RCT 95% CI; black bar = RCT HR. Matched Cox HR, pair-clustered SE. PS-Clinical (no LVEF) on the spec-v2 cohorts: HRs combined over 5 imputation draws (Rubin). Benchmark-permutation P: RCT results reassigned among the selected trials (20,000 draws); a small P means the ECG moves estimates toward each trial's own RCT, not just toward the null.</div>`;
  for (const id of ["emu-coh", "emu-trials", "emu-rung", "emu-cfg", "emu-sort"]) $("#" + id).onchange = emuUpdate;
  $("#emu-arms").onchange = emuUpdate;
  bindTips($("#emu-svg"));
  emuUpdate();
}
function emuUpdate() {
  const coh = $("#emu-coh").value, cfg = $("#emu-cfg").value, rung = $("#emu-rung").value, arms = checked("emu-arm");
  let T = trialSet($("#emu-trials").value);
  const gap = (a, t) => { const x = estOf(coh, cfg, rung, a, t)[0]; return fin(x) ? Math.abs(x - D.trials[t].rb) : NaN; };
  const srt = $("#emu-sort").value;
  const key = {area: t => [AREAS.indexOf(D.trials[t].area), D.trials[t].rb], rct: t => [D.trials[t].rb], name: t => [D.trials[t].name],
    gap: t => [-(gap("base", t) || 0)], chg: t => [(gap("ECG", t) - gap("base", t)) || 0]}[srt];
  T = [...T].sort((a, b) => { const ka = key(a), kb = key(b); for (let i = 0; i < ka.length; i++) { if (ka[i] < kb[i]) return -1; if (ka[i] > kb[i]) return 1; } return 0; });
  const W = 714, H = 580, ml = 150, mr = 16, mt = 26, mb = 42, lo = Math.log(0.2), hi = Math.log(5);
  const ph = H - mt - mb, rh = ph / Math.max(T.length, 1);
  const xs = l => ml + (Math.max(lo, Math.min(hi, l)) - lo) / (hi - lo) * (W - ml - mr);
  let s = `<text x="4" y="15" font-size="12.5" font-weight="700" fill="${NAVY}">Hazard ratio, emulation vs RCT · ${RUNG[rung][0]} · ${CSHORT[cfg]} · ${coh === "v2" ? "spec-v2" : "version 1"} cohorts · ${T.length} trials</text>`;
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
    let tt = `<b>${esc(tr.full)}</b> (${esc(tr.area)}; quality ${esc(tr.tier)}, ${tr.tot} pts)<br>RCT: ${Math.exp(tr.rb).toFixed(2)} (${Math.exp(tr.rb - 1.96 * tr.rs).toFixed(2)}–${Math.exp(tr.rb + 1.96 * tr.rs).toFixed(2)})`;
    arms.forEach((a, k) => {
      const [l, se] = estOf(coh, cfg, rung, a, t); const yy = na > 1 ? yc - Math.min(rh * 0.7, 4 * na) / 2 + k * sp : yc;
      if (!fin(l)) { tt += `<br>${ARM[a].lab}: not estimable (failed cell)`; return; }
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
  if (!arms.length) s += `<text x="${(ml + W - mr) / 2}" y="${mt + ph / 2}" font-size="20" font-weight="700" text-anchor="middle" fill="${NAVY}">Select methods</text>`;
  $("#emu-svg").innerHTML = s;
  let h = `<div class="sel"><b>${COH[coh]}</b> · <b>${RUNG[rung][0]}</b> · ${CFG[cfg]} · ${T.length} trial${T.length === 1 ? "" : "s"}</div><h4>Agreement with the RCTs</h4><table><tr><th>Method</th><th>mean |Δ|</th><th>r</th><th>est.</th><th>std.</th></tr>`;
  for (const a of arms) { const m = agree(coh, cfg, rung, a, T);
    h += `<tr><td>${swatch(a)} ${SL[a]}</td><td>${f3(m.gap)}</td><td>${f2(m.r)}</td><td>${pc(m.ea)}</td><td>${pc(m.sd)}</td></tr>`; }
  h += `</table>`;
  const cmp = arms.filter(a => a !== "base");
  if (arms.includes("base") && cmp.length && T.length > 1) {
    h += `<h4 style="margin-top:10px">vs PS alone (paired by trial)</h4><table><tr><th>Method</th><th>closer</th><th>sign-flip P</th><th>benchmark-perm. P</th></tr>`;
    for (const a of cmp) { const c = closer(coh, cfg, rung, a, T);
      h += `<tr class="${a === "ECG" ? "hl" : ""}"><td>${SL[a]}</td><td>${c.closer}/${c.k}</td><td>${fmtp(c.p)}</td><td>${f2(c.perm)}</td></tr>`; }
    h += `</table>`;
  }
  h += `<div class="note">mean |Δ| = mean |log HR<sub>emulated</sub> − log HR<sub>RCT</sub>|; r = Pearson r with the RCT log HRs; est. = estimate agreement (emulated HR inside the RCT 95% CI, |Δ| ≤ 1.96 SE<sub>RCT</sub>); std. = standardised-difference agreement, |z| &lt; 1.96 (RCT-DUPLICATE). Sign-flip and benchmark-permutation P: one-sided for the ECG (closer), two-sided for the permuted ECG. Agreement is secondary; no agreement claim without the benchmark-permutation P.</div>`;
  $("#emu-sum").innerHTML = arms.length ? h : EMPTY("Select methods to compare with the RCTs");
}
function agqInit() {
  const sel = (id, opts) => `<select id="${id}">${opts}</select>`;
  $("#agq-ctrl").innerHTML = `
  <label class="h">Cohorts</label>${sel("agq-coh", cohOpt)}
  <label class="h">PS base</label>${sel("agq-rung", rungOptE())}
  <label class="h">PS method</label>${sel("agq-cfg", CFGS.map(c => `<option value="${c}">${CFG[c]}</option>`).join(""))}
  <label class="h">Methods</label>
  <div id="agq-arms">${EARMS.map(a => `<label class="cb"><input type="checkbox" name="agq-arm" value="${a}" ${a !== "shufECG" ? "checked" : ""}>${swatch(a)}${ARM[a].lab}</label>`).join("")}</div>
  <label class="h">Tier source</label>${sel("agq-src", Object.entries(TSRC).map(([k, v]) => `<option value="${k}">${v}</option>`).join(""))}
  <label class="h">Quality groups</label>${sel("agq-split", `<option value="tier3">Excellent + Good vs Moderate vs Limited</option><option value="tier2">Excellent + Good vs Moderate + Limited</option><option value="tier4">All four tiers</option><option value="set">Analysed (E + G + M) vs Limited</option>`)}
  <label class="h">Metric plotted</label>${sel("agq-met", `<option value="sd">Standardized-difference agreement</option><option value="ea">Estimate agreement</option><option value="r">Pearson r</option><option value="gap">Mean |Δ log HR|</option>`)}
  <div class="desc" style="margin-top:8px">All 38 emulated trials, grouped by their quality tier. Tiers were assigned blind to the results; the rescored tiers are provisional (not frozen; LLM raters, no clinician review yet).</div>`;
  for (const id of ["agq-coh", "agq-rung", "agq-cfg", "agq-src", "agq-split", "agq-met"]) $("#" + id).onchange = agqUpdate;
  $("#agq-arms").onchange = agqUpdate;
  agqUpdate();
}
function agqGroups(v, src) {
  const idx = D.trials.map((_, i) => i), tq = i => D.trials[i][src];
  const G = L => idx.filter(i => L.includes(tq(i)));
  if (v === "tier2") return [["Excellent + Good", G(["Excellent", "Good"])], ["Moderate + Limited", G(["Moderate", "Limited"])]];
  if (v === "tier3") return [["Excellent + Good", G(["Excellent", "Good"])], ["Moderate", G(["Moderate"])], ["Limited", G(["Limited"])]];
  if (v === "set") return [["Analysed (E + G + M)", G(["Excellent", "Good", "Moderate"])], ["Limited", G(["Limited"])]];
  return TIERN.map(q => [q, G([q])]);
}
function agqUpdate() {
  const coh = $("#agq-coh").value, cfg = $("#agq-cfg").value, rung = $("#agq-rung").value, arms = checked("agq-arm"), src = $("#agq-src").value;
  const G = agqGroups($("#agq-split").value, src), met = $("#agq-met").value;
  const R = G.map(([g, T]) => [g, T, arms.map(a => agree(coh, cfg, rung, a, T))]);
  const W = 900, H = 300, ml = 50, mb = 40, mt = 24, pw = W - ml - 10, ph = H - mt - mb;
  const lo = met === "r" ? -0.5 : 0, hi = met === "gap" ? 0.6 : 1.1, stp = met === "r" ? 0.25 : met === "gap" ? 0.1 : 0.2;
  const ys = v => mt + ph - (Math.max(lo, Math.min(hi, v)) - lo) / (hi - lo) * ph;
  const lab = v => met === "r" || met === "gap" ? v.toFixed(2) : Math.round(v * 100) + "%";
  let s = `<text x="${ml}" y="14" font-size="12.5" font-weight="700" fill="${NAVY}">${esc($("#agq-met").selectedOptions[0].text)} · ${RUNG[rung][0]} · ${CSHORT[cfg]} · ${coh === "v2" ? "spec-v2" : "version 1"} cohorts · tiers: ${esc(TSRC[src])}</text>`;
  for (let v = lo; v <= (met === "gap" ? 0.6 : 1) + 1e-9; v += stp) s += `<line x1="${ml}" x2="${W - 10}" y1="${ys(v)}" y2="${ys(v)}" stroke="#ececf1"/><text x="${ml - 6}" y="${ys(v) + 4}" font-size="11" text-anchor="end" fill="${NAVY}">${lab(v)}</text>`;
  const gw = pw / R.length, bw = Math.min(46, (gw - 30) / Math.max(arms.length, 1));
  R.forEach(([g, T, M], gi) => {
    const x0 = ml + gi * gw + (gw - bw * arms.length) / 2;
    M.forEach((m, k) => { const v = m[met]; if (!fin(v)) return; const x = x0 + k * bw, y = ys(v), y0 = ys(Math.max(0, lo));
      s += `<rect x="${x + 3}" y="${Math.min(y, y0)}" width="${bw - 6}" height="${Math.abs(y0 - y)}" fill="${ARM[arms[k]].col}"/><text x="${x + bw / 2}" y="${Math.min(y, y0) - 4}" font-size="11" text-anchor="middle" fill="${NAVY}">${lab(v)}</text>`; });
    s += `<text x="${ml + gi * gw + gw / 2}" y="${H - mb + 18}" font-size="13" text-anchor="middle" font-weight="700" fill="${NAVY}">${esc(g)} (${T.length})</text>`;
  });
  if (!arms.length) s += `<text x="${W / 2}" y="${H / 2}" font-size="20" font-weight="700" text-anchor="middle" fill="${NAVY}">Select methods</text>`;
  $("#agq-svg").innerHTML = s;
  let h = `<table class="t" style="margin-top:4px"><tr><th>Group</th><th>Method</th><th>n</th><th>r</th><th>Estimate agr.</th><th>Std-diff agr.</th><th>mean |Δ|</th><th>closer vs PS alone</th><th>benchmark-perm. P</th></tr>`;
  R.forEach(([g, T, M]) => M.forEach((m, k) => { const a = arms[k], c = a !== "base" && arms.includes("base") ? closer(coh, cfg, rung, a, T) : null;
    h += `<tr><td>${k ? "" : esc(g)}</td><td>${swatch(a)} ${ARM[a].lab}</td><td>${m.n}</td><td>${f2(m.r)}</td><td>${pc(m.ea)}</td><td>${pc(m.sd)}</td><td>${f3(m.gap)}</td><td>${c ? c.closer + "/" + c.k : ""}</td><td>${c ? f2(c.perm) : ""}</td></tr>`; }));
  $("#agq-tab").innerHTML = h + `</table>`;
}

/* ===== deck mechanics (2026-10-01 deck) ===== */
const slides = [...document.querySelectorAll(".slide")];
slides.forEach((sl, i) => {
  if (!sl.dataset.title) return;
  sl.insertAdjacentHTML("afterbegin", `<div class="ttl">${sl.dataset.title}</div><div class="rule top"></div><div class="num">${i + 1}</div>` +
    `<div class="rule bot"></div><div class="prov">Provisional: trial set not frozen; methods not locked</div><div class="foot"><b>CarDS</b>Lab</div><img class="logo" alt="" src="${LOGO}">`);
});
let cur = 0, step = 0;
const nSteps = sl => Math.max(0, ...[...sl.querySelectorAll(".build")].map(e => +e.dataset.step || 0));
function applyBuild() { slides[cur].querySelectorAll(".build").forEach(e => e.classList.toggle("hid", (+e.dataset.step || 0) > step)); }
function next() { if (step < nSteps(slides[cur])) { step++; applyBuild(); } else if (cur < slides.length - 1) show(cur + 1); }
function prev() { if (step > 0) { step--; applyBuild(); } else if (cur > 0) show(cur - 1, true); }
function show(i, built) {
  cur = Math.max(0, Math.min(slides.length - 1, i));
  step = built ? nSteps(slides[cur]) : 0; applyBuild();
  slides.forEach((s, k) => s.classList.toggle("active", k === cur));
  $("#nav-count").textContent = `${cur + 1} / ${slides.length}`;
  tip.style.display = "none";
  if (location.hash !== "#" + (cur + 1)) history.replaceState(null, "", "#" + (cur + 1));
}
function fit() { const s = Math.min(innerWidth / 1280, innerHeight / 720); $("#stage").style.transform = `translate(-50%,-50%) scale(${s})`; }
addEventListener("resize", fit);
addEventListener("keydown", e => {
  const tag = (e.target.tagName || "").toLowerCase(), inForm = tag === "select" || tag === "input";
  if (e.key === "PageDown" || (!inForm && (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === " "))) { e.preventDefault(); if (inForm) e.target.blur(); next(); }
  else if (e.key === "PageUp" || (!inForm && (e.key === "ArrowLeft" || e.key === "ArrowUp"))) { e.preventDefault(); if (inForm) e.target.blur(); prev(); }
  else if (!inForm && e.key === "Home") show(0);
  else if (!inForm && e.key === "End") show(slides.length - 1);
  else if (!inForm && (e.key === "f" || e.key === "F")) { if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); else document.exitFullscreen(); }
});
$("#nav-prev").onclick = prev;
$("#nav-next").onclick = next;
/* headless-check API: balance point estimates on all items of a panel (no domain filter or ranking), as the explorer; agreement metrics */
window.TRACE = {pair: s => { const get = getter(s.panel, s.leak, s.coh || "v2"), js = itemsOf(s.panel).map(v => v.j);
  return paired(get, s.cfg, s.rung, s.arm, s.ref || "base", trialSet(s.trials), js, s.thr || 0.1); },
  agree: s => agree(s.coh, s.cfg, s.rung, s.arm, trialSet(s.trials)), closer: s => closer(s.coh, s.cfg, s.rung, s.arm, trialSet(s.trials), s.nd)};
init(); emuInit(); agqInit(); fit();
show((parseInt(location.hash.slice(1), 10) || 1) - 1);
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
