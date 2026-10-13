#!/usr/bin/env python
"""Build the CarDS Lab LATENT-RCT lab-meeting deck (15 October 2026): docs/presentation/ecg_tte_lab_2026_10_15.html.

Revision of 2026-10-13 (user feedback; pipeline.md update 2026-10-13):
  * PRIMARY = version 1 cohorts + paper 1's 32 trials (v19 tiers; Limited excluded: ALLHAT, ASCOT-BPLA, DECLARE-TIMI 58, ONTARGET,
    REWIND, VALUE), PS-CVD5, fixed C = 1, 1:1 caliper 0.2, 54 leakage-corrected items. Spec-v2 cohort fixes and framework v2.0 tiers
    (29 / 30 sets) are SENSITIVITIES (still selectable in the explorers). Study name LATENT-RCT. No "provisional" banners.
  * PS-Clinical (no LVEF) on the version 1 cohorts = the 5-draw MI cells of audits/claude-v1-psclin-mi (drop-in v1 layout; |SMD|
    averaged over draws, Rubin-combined HRs; docs/v1_psclin_mi/PS_CLINICAL_MI_V1.md). If that run is absent, the single-draw cells of
    audits/claude-v1-psclin-nolvef are used and labelled "single imputation; MI pending".

Revision of 2026-10-13 afternoon (docs/queue/QUEUE_2026_10_13_DECK.md step 2): slide 5 body left empty (for the user's own content);
slide 6 flow populates one step after another, numbered feasibility criteria, popups for both criteria boxes; slide 7 "PSM
experiments" (PS levels one at a time, then + ECG, + CLMBR-T, + ECG + CLMBR-T, + permuted placebo; popups for hdPS, PS-Clinical and
PS / matching; no PS-Flags, no ladder graphic); slide 10 = the updated Figure 2 (scripts/figures/make_figure2_latent.py) only.
Popups: Esc or the close button closes them; while one is open no key reaches the deck.

Main slides: 1 title; 2 Background (10-01); 3 Problem (10-01 schematic, click reveal of the unmeasured side + three points); 4 Aims
(four aims, revealed one at a time); 5 study overview (empty body); 6 LATENT-RCT pipeline; 7 PSM experiments; 8 held-out panel;
9 balance explorer; 10 results (Figure 2); 11 emulation explorer; 12 robustness; 13 agreement by quality;
14 plasmode; 15 MIMIC-IV; 16 take-home; 17 open decisions. Appendix A1-A6 (hash-linked; "More:" links on main slides, "Back to
slide N" on every appendix slide): A1 trial selection; A2 emulation-quality criteria + interactive quality viewer (v19; framework v2.0
toggle); A3 all 38 trials (Table 1); A4 framework v2.0 (sensitivity); A5 spec-v2 cohort fixes (sensitivity); A6 design history.

Reuses (not modified): scripts/build_lab_deck.py (10-01 stylesheet, schematics), scripts/build_lab_deck_v2.py (template, explorers,
static-slide helpers, claims table), scripts/build_balance_explorer.py (data loading and validated statistics). The 2026-10-09 deck is
regenerated first and checked byte-identical to the committed file (data-loading regression check).

Every static number is registered in a claims table (audits/claude-lab-deck-1015-v2/claims.{csv,md}) with an independent check:
numbers from the Python summaries are recomputed from the cells with build_balance_explorer.pair_stats; numbers computed here from the
cells are re-derived from the deck's embedded integers; text numbers are probed verbatim in their source documents.

Embedded data: aggregates only (per-trial |SMD| integers, per-trial log HR / SE, RCT benchmarks, trial names, areas, quality items and
rationales from design documents). No n, n_pairs, retention, ESS or patient keys.

Usage (tte-analysis env):
  python scripts/build_lab_deck_1015.py      build the HTML; claims table and validation inputs to audits/claude-lab-deck-1015-v2
"""
import argparse
import base64
import io
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_lab_deck as L1  # noqa: E402
import build_lab_deck_v2 as V2  # noqa: E402
from build_lab_deck_v2 import claim, fx, ci, fp, pv, esc, norm, NAVY, RED  # noqa: E402

BE = V2.BE
A = V2.A
OUT = ROOT / "docs/presentation/ecg_tte_lab_2026_10_15.html"
DECK1001 = ROOT / "docs/presentation/ecg_tte_lab_2026_10_01.html"
DECK1009 = V2.OUT
SCR = A / "claude-lab-deck-1015-v2"
FIG2 = ROOT / "docs/paper/figures_latent/figure2_covariate_balance.png"  # scripts/figures/make_figure2_latent.py
FIG2V = A / "claude-deckq-20261013/figure2_values.json"  # its aggregate values (validated there)
MIDIR = A / "claude-v1-psclin-mi"
MI_V1 = MIDIR / "cells/restricted_cells_v1_mi_v1layout.parquet"
MI_V1SUM = MIDIR / "summary"
MI_V1DOC = ROOT / "docs/v1_psclin_mi/PS_CLINICAL_MI_V1.md"
QT19 = ROOT / "docs/v19/quality_tiers.json"
QREA = ROOT / "docs/v19/QUALITY_REAUDIT.md"
SUPP = ROOT / "docs/paper/supplement.md"
PAPER = ROOT / "docs/paper/paper.md"
PICOT = ROOT / "docs/paper/table1_picot.md"
SEARCH = ROOT / "docs/trial_search/SEARCH_LOG.md"
AUDM = ROOT / "docs/paper/AUDIT_MANUSCRIPT_2026-10-01.md"
CLRE = ROOT / "docs/v1_audit/CLAIMS_RECHECK.md"
CAND17 = ROOT / "docs/v17/candidates.md"
PIPE, HAND, FIXD, QV2C = V2.PIPE, V2.HAND, V2.FIXD, V2.QV2C
V2SUM, MISUM = BE.V2SUM, BE.MISUM
SCOPE = "section.s1001"
AREAS = ["AF", "HF", "Diabetes", "Hypertension", "ACS / MI", "Other"]
TIERS = ["Excellent", "Good", "Moderate", "Limited"]
FID = {"good": 0, "moderate": 1, "poor": 2}
# main slides (ids, in order) and appendix slides (id, label, short title, default back-target)
MAIN = ["s-title", "s-bg", "s-prob", "s-aims", "s-over", "s-pipe", "s-meth1", "s-meth2", "s-bal", "s-res2", "s-emu", "s-rob", "s-agq",
        "s-plas", "s-mimic", "s-take", "s-dec"]
APP = [("a-sel", "A1", "Trial selection", "s-pipe"), ("a-qual", "A2", "Emulation-quality criteria", "s-pipe"),
       ("a-t1", "A3", "All 38 trials (Table 1)", "s-pipe"), ("a-t1b", "A3b", "All 38 trials (Table 1), continued", "s-pipe"), ("a-fw", "A4", "Framework v2.0 (sensitivity)", "s-res2"),
       ("a-fix", "A5", "Spec-v2 cohort fixes (sensitivity)", "s-rob"), ("a-hist", "A6", "Design history", "s-dec")]
SN = {s: str(i + 1) for i, s in enumerate(MAIN)}
SN.update({sid: lab for sid, lab, _, _ in APP})
APPT = {lab: t for _, lab, t, _ in APP}
CTX = {}


def one(s, a, b):
    """replace exactly one occurrence."""
    assert s.count(a) == 1, (s.count(a), a[:140])
    return s.replace(a, b)


def between(s, a, b, incl_b=False):
    i = s.index(a)
    j = s.index(b, i)
    return s[i: j + (len(b) if incl_b else 0)]


def cl_slide(n0, sid):
    """relabel the claims registered by a reused V2 slide function with this deck's slide label."""
    for c in V2.CL[n0:]:
        c["slide"] = SN[sid]


def more(*labs):
    return ('<div class="xrefs">More: ' + " · ".join(f'<a class="xref" href="#{l}" data-goto="{l}">{l} · {esc(APPT[l])}</a>' for l in labs)
            + "</div>")


def back(sid):
    return f'<div class="xrefs"><a class="xref back" href="#{SN[sid]}" data-goto="{sid}" data-back="1">Back to slide <span class="lbl">{SN[sid]}</span></a></div>'


def sec(sid, title, body, cls="", links="", steps=None, wrap=True):
    app = next((lab for s, lab, _, _ in APP if s == sid), None)
    attrs = f' id="{sid}" data-title="{esc(title)}"' + (f' data-app="{app}"' if app else "")
    if steps:
        attrs += f' data-steps="{steps}"'
    if app:
        cls = (cls + " app").strip()
        links = links or back(next(d for s, _, _, d in APP if s == sid))
    inner = f'<div class="body">\n{body}\n</div>' if wrap else body
    return f'<section class="slide {cls}"{attrs}>\n{inner}\n{links}\n</section>\n'


def retitle(html, sid, title, links="", cls=""):
    """re-head a V2 slide (one <section>) with this deck's id / title / appendix label and links."""
    m = re.match(r'<section class="slide [^"]*"(?: id="[^"]+")? data-title="[^"]+">\n', html)
    assert m, html[:200]
    body = html[m.end():]
    assert body.rstrip().endswith("</section>")
    body = body.rstrip()[: -len("</section>")].rstrip()
    app = next((lab for s, lab, _, _ in APP if s == sid), None)
    attrs = f' id="{sid}" data-title="{esc(title)}"' + (f' data-app="{app}"' if app else "")
    if app:
        cls = (cls + " app").strip()
        links = links or back(next(d for s, _, _, d in APP if s == sid))
    return f'<section class="slide {cls}"{attrs}>\n{body}\n{links}\n</section>\n'


# ================================================================ the 2026-10-09 deck (regenerated: data-loading regression check)
def build_1009(g, g2):
    trials, Q = V2.trials_deck(g, g2)
    D = V2.build_data(g, g2, trials)
    V2.GRID2.update(grid=BE.Grid(g2["G"], g2["U"], g2["ex"]), D=D)
    MC, VC = V2.get_contrasts()
    IM = pd.read_csv(V2.IMPACT)
    DM = pd.read_csv(V2.MISUM / "domains.csv")
    EX = load_ex()
    RR = pd.read_csv(V2.RRS)
    static = [V2.s_changes(trials, Q, MC, VC, EX), V2.s_flow(trials, Q), V2.s_framework(trials, Q), V2.s_tiers(trials, Q),
              V2.s_fixes(trials, EX, RR), V2.s_methods_design(), V2.s_methods_panel()]
    html = (V2.TEMPLATE.replace("__TITLE__", V2.s_title()).replace("__STATIC1__", "".join(static))
            .replace("__STATIC2__", V2.s_results2(MC, VC, IM, DM)).replace("__STATIC3__", V2.s_robust(MC, VC, RR, IM))
            .replace("__STATIC4__", "".join([V2.s_plasmode(), V2.s_mimic(), V2.s_takehome(MC, IM), V2.s_decisions(Q)]))
            .replace("__EXPLORER_JS__", V2.explorer_js()).replace("__LOGO__", V2.logo_uri(None))
            .replace("__DATA__", json.dumps(D, separators=(",", ":"), allow_nan=False)))
    return html, trials, Q


def load_ex():
    EX = pd.read_csv(V2.EXCL, dtype={"pct_removed_v2": str})
    EX["pct_removed_v2"] = [float(v[1:]) / 2 if v.startswith("<") else float(v) for v in EX.pct_removed_v2]
    return EX


# ================================================================ data for this deck
def load_v1(g):
    """version 1 grid with PS-Clinical (no LVEF) = the 5-draw MI cells (drop-in v1 layout) if the MI run is DONE."""
    if not (MIDIR / "DONE").exists() or not MI_V1.exists():
        return g, False
    a = pd.read_parquet(MI_V1)
    b = pd.read_parquet(BE.NOLVEF)
    b = b[b.rung == "clinical_nolvef"].reset_index(drop=True)
    k = ["config", "rung", "arm", "trial", "key"]
    assert list(a.columns) == list(b.columns) and (a[k].values == b[k].values).all()
    assert (a.ex58.fillna("") == b.ex58.fillna("")).all() and not a.cell_failed.fillna("").astype(str).ne("").any()
    old = BE.NOLVEF
    BE.NOLVEF = MI_V1
    try:
        g1 = BE.load_grid()
    finally:
        BE.NOLVEF = old
    assert g1["tids"] == g["tids"] and g1["ex"] == g["ex"]
    for key in g["G"]:  # every other rung identical
        if key[1] != "clinical_nolvef":
            assert np.array_equal(g["G"][key], g1["G"][key], equal_nan=True)
    return g1, True


def trials_new(trials_old, g):
    """deck trial records: tier = v19 (primary); framework v2.0 tiers kept as tv2 (rescored, spec-v2 cohorts) and tq1 (v1 cohorts)."""
    QT = {t["key"]: t for t in json.load(open(QT19))["trials"]}
    out = []
    for t, k in zip(trials_old, g["keys"]):
        q = QT[k]
        tier = q["tier"].split(" - ")[0]
        assert tier == t["t19"] and q["area"] == t["area"]
        fl = [int(q["flags"][f"F{i}"]) for i in range(1, 6)]
        pts = sum(fl) + FID[q["comparator"]] + FID[q["outcome"]]
        assert pts == q["points"], k
        out.append(dict(id=t["id"], name=t["name"], full=t["full"], area=t["area"], tier=tier, t19=tier, tv2=t["tier"], tq1=t["tq1"],
                        tot=pts, tot2=t["tot"], tot1=t["tot1"], it=t["it"], fl=fl, co=q["comparator"][0].upper(), ou=q["outcome"][0].upper(),
                        cap=bool(q["tier_capped"]), hz=int(q["horizon_months"]), rat=q["rationale"], prov=t["prov"], s32=t["s32"], v2=t["v2"],
                        v2c=t["v2c"], phys=t["phys"], rb=t["rb"], rs=t["rs"]))
    assert sum(t["tier"] != "Limited" for t in out) == 32 == sum(t["s32"] for t in out)
    return out


# ================================================================ statistics helpers
def T_(ts):
    return BE.trial_set(CTX["trials"], ts)


def ps(grid, cfg, rg, a, b, ts, panel="54"):
    return BE.pair_stats(grid, cfg, rg, a, b, T_(ts), panel, True)


def rr_txt(r):
    return ci(r["rr"], r["lo"], r["hi"])


def vc1(st, rg, a, b="base", cfg="main"):
    """version 1 summary row: scripts/v2_cohorts/summarize.py (cohort v1) or, for PS-Clinical (no LVEF), the v1 MI summary."""
    if rg == "clinical_nolvef" and CTX["mi"]:
        M = CTX["MIS"]
        r = M[(M.set == st) & (M.config == cfg) & (M.rung_a == "clinical_nolvef_mi") & (M.rung_b == "clinical_nolvef_mi") & (M.arm_a == a)
              & (M.arm_b == b) & M.kind.isin(["within", "ladder"])]
        assert len(r) == 1, (st, rg, a, b, cfg, len(r))
        return r.iloc[0], MI_V1SUM / "contrasts.csv"
    return V2.vrow(CTX["VC"], "v1", st, rg, a, b, cfg), V2SUM / "contrasts.csv"


def mis_row(st, rg, a, b="base", cfg="main"):
    """v1 MI summary (also holds the version 1 P1/P5/PS10/hdPS rows, incl. the rescored-30 'Snew' set)."""
    M = CTX["MIS"]
    r = M[(M.set == st) & (M.config == cfg) & (M.rung_a == rg) & (M.rung_b == rg) & (M.arm_a == a) & (M.arm_b == b) & M.kind.isin(["within", "ladder"])]
    assert len(r) == 1, (st, rg, a, b, cfg, len(r))
    return r.iloc[0]


SETS1 = {"s32": "S32", "all": "S38", "v2": "S29", "v2c": "Snew"}


def stat_v1(sid, what, ts, rg, a, b="base", cfg="main", panel="54"):
    """a version 1 contrast: shown from the Python summary where one exists (checked against BE.pair_stats on the cells), otherwise
    computed from the cells (checked against the deck's embedded integers). Returns (pair_stats dict, summary row or None)."""
    G1, E1 = CTX["G1"], CTX["E1"]
    r = ps(G1, cfg, rg, a, b, ts, panel)
    st = SETS1.get(ts)
    row, src = None, None
    if st in ("S32", "S38", "S29"):
        row, src = vc1(st, rg, a, b, cfg)
    elif st == "Snew" and CTX["mi"] and rg in ("P1", "P5", "PS10", "hdPS200", "clinical_nolvef"):
        row, src = mis_row(st, "clinical_nolvef_mi" if rg == "clinical_nolvef" else rg, a, b, cfg), MI_V1SUM / "contrasts.csv"
    sided = "two" if a == "shufECG" and b == "base" else "one"
    pk = "p_m_two" if sided == "two" else "p_m"
    pre, mm = ("relred54", "m54") if panel == "54" else ("relred58", "m58")
    if row is not None:
        shown = ci(row[pre], row[pre + "_lo"], row[pre + "_hi"])
        claim(SN[sid], what, shown, src, ref=rr_txt(r), ref_how="recomputed from the version 1 cells (build_balance_explorer.pair_stats)")
        claim(SN[sid], what + ": P", fp(row[f"{mm}_p"]), src, ref=fp(r[pk]), ref_how="recomputed from the cells (exact sign-flip)")
        claim(SN[sid], what + ": trials lower", row[f"{mm}_better"], src, ref=f"{r['lower']}/{r['k']}", ref_how="recomputed from the cells")
        out = dict(rr=row[pre], lo=row[pre + "_lo"], hi=row[pre + "_hi"], p=row[f"{mm}_p"], lower=row[f"{mm}_better"], k=r["k"],
                   m_ref=row[f"{mm}_b"], m_arm=row[f"{mm}_a"])
    else:
        re_ = ps(E1, cfg, rg, a, b, ts, panel)
        shown = rr_txt(r)
        claim(SN[sid], what, shown, "version 1 cells (build_balance_explorer.pair_stats)", ref=rr_txt(re_), ref_how="recomputed from the deck's embedded integers")
        claim(SN[sid], what + ": P", fp(r[pk]), "version 1 cells", ref=fp(re_[pk]), ref_how="embedded integers")
        out = dict(rr=r["rr"], lo=r["lo"], hi=r["hi"], p=r[pk], lower=f"{r['lower']}/{r['k']}", k=r["k"], m_ref=r["m_ref"], m_arm=r["m_arm"])
    return out, row


def agree_v1(sid, what, ts, rg, a="ECG", cfg="main", coh="v1"):
    """|dlog HR| base -> arm and the benchmark-permutation P (one-sided), from the summary where available, checked on the deck's HRs."""
    D = CTX["D"]
    T = T_(ts)
    m, mb = V2.agree_py(D, coh, cfg, rg, a, T), V2.agree_py(D, coh, cfg, rg, "base", T)
    E = D["EST"][coh][cfg][rg]
    TT = [t for t in T if E[a][t] is not None and E["base"][t] is not None]
    bs = V2.bshuf_py(np.array([E[a][t][0] for t in TT]), np.array([E["base"][t][0] for t in TT]), np.array([D["trials"][t]["rb"] for t in TT]))
    st = SETS1.get(ts)
    mine = f"{mb['absd']:.3f} → {m['absd']:.3f}"
    if coh == "v1" and st in ("S32", "S38", "S29"):
        row, src = vc1(st, rg, a, "base", cfg)
        shown = f"{row.absd_b:.3f} → {row.absd_a:.3f}"
        claim(SN[sid], what + ": |dlog HR|", shown, src, ref=mine, ref_how="recomputed from the deck's embedded log HRs")
        bsh = f"{row.bshuf_p:.2f}"
        claim(SN[sid], what + ": benchmark-permutation P", bsh, src, ref=f"{bs:.2f}", ref_how="recomputed (sens_primary32.bshuf, same draws) from the deck's log HRs")
        return shown, row.bshuf_p
    ref = mis_row(st, "clinical_nolvef_mi" if rg == "clinical_nolvef" else rg, a, "base", cfg) if (coh == "v1" and st == "Snew" and CTX["mi"]) else None
    claim(SN[sid], what + ": |dlog HR|", mine, "deck log HRs (V2.agree_py)", ref=None if ref is None else f"{ref.absd_b:.3f} → {ref.absd_a:.3f}",
          ref_how="v1 MI summary (set Snew)")
    claim(SN[sid], what + ": benchmark-permutation P", f"{bs:.2f}", "deck log HRs (sens_primary32.bshuf)", ref=None if ref is None else f"{ref.bshuf_p:.2f}",
          ref_how="v1 MI summary (set Snew)")
    return mine, bs


# ================================================================ static slides
def s_title():
    return """<section class="slide" id="s-title" data-title="Title" data-notitle="1">
  <img class="tlogo" alt="CarDS Lab logo" src="__LOGO__">
  <div class="l1">CarDS Lab Presentation</div>
  <div class="l2"><b style="color:#0E103C">LATENT-RCT</b>: learned representations for confounding control in target trial emulation</div>
  <div class="l3">15 October 2026</div>
</section>
"""


def intro_markup(T, deck1001):
    """Background (10-01 slide 2, unchanged) and Problem (10-01 slide 3 with a new header, reveal and three points)."""
    m = between(T, "<!-- 2 -->", "<!-- 4 -->")
    assert m in deck1001
    titles = re.findall(r'<section class="slide" data-title="([^"]+)">', m)
    assert titles == ["Background", "Problem"], titles
    m = one(m, '<section class="slide" data-title="Background">', '<section class="slide s1001" id="s-bg" data-title="Background">')
    old_prob = between(m, '<section class="slide" data-title="Problem">', "</section>", incl_b=True)
    new_prob = """<section class="slide s1001" id="s-prob" data-title="Problem">
  <div class="body">
    <h2>Propensity scores balance only what is measured</h2>
    <div style="display:grid;grid-template-columns:600px 1fr;gap:40px">
      <svg id="svg-psm" width="600" height="420" viewBox="0 0 600 420"></svg>
      <div style="padding-top:34px"><ol class="pts">
        <li class="build" data-step="2"><b>Missingness:</b> real-world EHR data are incomplete</li>
        <li class="build" data-step="3"><b>Missing physiology:</b> LV function, congestion, atrial substrate</li>
        <li class="build" data-step="4"><b>Hard to operationalize:</b> codes differ across systems</li>
      </ol></div>
    </div>
  </div>
</section>"""
    m = one(m, old_prob, new_prob)
    m = m.replace("<!-- 2 -->", "").replace("<!-- 3 -->", "")
    return m.strip() + "\n"


PAGE_LEVEL = {":root", "html,body", "body", "#stage", "#tip", "#nav", "#nav span"}


def intro_css(T, deck1001):
    css = between(T, "<style>\n", "</style>")[len("<style>\n"):]
    assert css in deck1001
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@media[^{]*\{[^{}]*\{[^{}]*\}\s*\}", "", css)
    assert "@" not in css
    out = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        sel = " ".join(sel.split())
        if sel in PAGE_LEVEL:
            continue
        out.append(",".join(f"{SCOPE} {x.strip()}" for x in sel.split(",")) + "{" + body + "}")
    assert len(out) > 60
    return "/* ===== slides 2-3: the 2026-10-01 deck's stylesheet (scripts/build_lab_deck.py), scoped to its slides ===== */\n" + "\n".join(out) + "\n"


def intro_js(T, deck1001):
    """10-01 schematics for Background and Problem (drawStatic up to the PSM drawing); the unmeasured side of the PSM drawing is
    wrapped in a build group (step 1)."""
    esc_l = next(l for l in T.splitlines() if l.startswith("const esc = "))
    helpers = between(T, "function box(", "function drawStatic() {")
    draw = between(T, "function drawStatic() {", "  /* ECG pipeline */")
    for x in (esc_l, helpers, draw):
        assert x in deck1001
    draw = one(draw, '  s += `<text x="0" y="274" font-size="15" fill="${RED}" font-weight="700">unmeasured</text>`;',
               '  s += `<g class="build rise" data-step="1">`;\n  s += `<text x="0" y="274" font-size="15" fill="${RED}" font-weight="700">unmeasured</text>`;')
    draw = one(draw, '  $("#svg-psm").innerHTML = s;', '  s += `</g>`;\n  $("#svg-psm").innerHTML = s;')
    return f"""/* ===== slides 2-3: schematics of the 2026-10-01 deck (scripts/build_lab_deck.py drawStatic: RCT/TTE and PSM drawings) ===== */
function drawIntro() {{
  (function () {{
const $ = s => document.querySelector(s);
{esc_l}
{helpers}{draw}}}
drawStatic();
  }})();
}}
"""


ICON = {
    "ecg": '<svg viewBox="0 0 64 44" width="64" height="44"><rect x="1" y="1" width="62" height="42" rx="4" fill="#fff" stroke="#0E103C" stroke-width="2"/>'
           '<path d="M5 26 L16 26 L19 22 L22 26 L26 26 L28 30 L31 8 L34 36 L37 26 L44 26 L47 21 L51 26 L59 26" fill="none" stroke="#DC5A55" stroke-width="2.4" stroke-linejoin="round"/></svg>',
    "ehr": '<svg viewBox="0 0 40 48" width="34" height="44"><path d="M3 3 H27 L37 13 V45 H3 Z" fill="#fff" stroke="#0E103C" stroke-width="2.2"/><path d="M27 3 V13 H37" fill="none" stroke="#0E103C" stroke-width="2"/>'
           '<rect x="9" y="18" width="20" height="3.4" fill="#0E103C"/><rect x="9" y="25" width="16" height="3.4" fill="#5b5d86"/><rect x="9" y="32" width="20" height="3.4" fill="#0E103C"/><rect x="9" y="39" width="12" height="3.4" fill="#5b5d86"/></svg>',
    "bal": '<svg viewBox="0 0 64 48" width="62" height="46"><line x1="32" y1="6" x2="32" y2="42" stroke="#0E103C" stroke-width="2.6"/><line x1="10" y1="12" x2="54" y2="12" stroke="#0E103C" stroke-width="2.6"/>'
           '<path d="M3 28 L10 12 L17 28 Z" fill="none" stroke="#0E103C" stroke-width="2"/><path d="M47 28 L54 12 L61 28 Z" fill="none" stroke="#0E103C" stroke-width="2"/>'
           '<path d="M2 28 Q10 36 18 28 Z" fill="#0E103C"/><path d="M46 28 Q54 36 62 28 Z" fill="#DC5A55"/><rect x="22" y="42" width="20" height="4" fill="#0E103C"/><circle cx="32" cy="6" r="3" fill="#0E103C"/></svg>',
    "rct": '<svg viewBox="0 0 64 48" width="62" height="46"><line x1="32" y1="2" x2="32" y2="46" stroke="#8a8d99" stroke-width="1.4" stroke-dasharray="3 3"/>'
           '<line x1="12" y1="10" x2="36" y2="10" stroke="#0E103C" stroke-width="2"/><rect x="21" y="6" width="8" height="8" fill="#0E103C"/>'
           '<line x1="18" y1="24" x2="44" y2="24" stroke="#DC5A55" stroke-width="2"/><circle cx="30" cy="24" r="4.5" fill="#DC5A55"/>'
           '<line x1="26" y1="38" x2="56" y2="38" stroke="#0E103C" stroke-width="2"/><rect x="37" y="34" width="8" height="8" fill="#0E103C"/></svg>',
    "glob": '<svg viewBox="0 0 48 48" width="46" height="46"><circle cx="24" cy="24" r="20" fill="#fff" stroke="#0E103C" stroke-width="2.4"/><ellipse cx="24" cy="24" rx="9" ry="20" fill="none" stroke="#0E103C" stroke-width="1.8"/>'
            '<line x1="4" y1="24" x2="44" y2="24" stroke="#0E103C" stroke-width="1.8"/><path d="M8 13 H40 M8 35 H40" stroke="#0E103C" stroke-width="1.4"/></svg>',
}


# feasibility criteria (stage 1), numbered: (short label for the pipeline box, criterion, example); shared by slide 6 (box and popup)
# and appendix A1
FEAS = [
    ("comparator: active, or an accepted proxy", "Active comparator, or an accepted proxy",
     "Placebo-controlled CVOTs emulated with RCT-DUPLICATE proxies: DPP-4i (EMPA-REG OUTCOME, LEADER) or sulfonylurea (TECOS)"),
    ("primary endpoint ascertainable in the EHR", "Primary endpoint ascertainable in the EHR", "DIONYSOS excluded: AF recurrence needs rhythm monitoring"),
    ("intervention and comparator identifiable", "Intervention and comparator identifiable",
     "From medication orders or procedure codes; a strategy never used in 2011–2024 fails"),
    ("≥300 with ECG in the smaller arm, ≥50 events", "Size: ≥300 with an ECG in the smaller arm; ≥50 pooled events",
     "PARAGON-HF, DAPA-HF/EMPEROR-Reduced and PARTNER were built in development but had fewer than 400 PS-Clinical pairs "
     "(development data-sufficiency rule) and are not among the 38"),
    ("not a near-duplicate cohort", "Not a near-duplicate (≥80% shared patient–index-date records)",
     "ACCOMPLISH excluded (96% of ALLHAT's records); 50–80% kept, e.g. ACTIVE W vs RE-LY 69%"),
]
QRULE = ("<b>Points</b> (design information only, blind to results): design flags F1 in-hospital start not mirrored · F2 selective run-in · "
         "F3 baseline-therapy switch at randomization not reproduced · F4 horizon ≥48 months · F5 other time-zero misalignment, <b>1 point each</b>; "
         "comparator and outcome fidelity good / moderate / poor = <b>0 / 1 / 2</b> (poor = placebo proxy or hypothesis-changing substitution; "
         "endpoint not validly ascertainable). <b>Tiers:</b> Excellent 0 · Good 1–2 (no poor item, ≤1 flag) · Moderate 3, or 1–2 with a poor item "
         "or 2 flags · <b class=\"red\">Limited ≥4: excluded</b>. Two raters (LLM-assisted), 82% agreement on the 3-class result (κ 0.71), then adjudication.")


DESIGNS = ("<b>New-user, active-comparator</b> designs (time zero = first order of either drug, no comparator order in the prior 365 days); "
           "<b>sequential add-on or switch</b> designs where the trial tested adding or switching therapy against continuing it (e.g. rhythm "
           "control added to rate control; switching from warfarin). Outcome = the trial's primary endpoint. Index dates <b>2011–2024</b> "
           "(pipeline.md; paper). Note: the version 1 audit found COMET index dates extending into 2025.")


def feas_rows():
    return "".join(f"<tr><td><b>{k}.</b> {esc(c)}</td><td>{esc(e)}</td></tr>" for k, (_, c, e) in enumerate(FEAS, 1))


def q_examples(sid=None):
    """worked v19 points examples (ARISTOTLE, COMET, EMPA-REG OUTCOME, ALLHAT); claims registered when sid is given."""
    tr = CTX["trials"]
    QJ = {t["trial"]: t for t in json.load(open(QT19))["trials"]}
    ex = []
    for nm in ("ARISTOTLE", "COMET", "EMPA-REG OUTCOME", "ALLHAT"):
        t = next(x for x in tr if x["full"] == nm)
        parts = [f"F{i + 1}" for i, v in enumerate(t["fl"]) if v] + [f"comparator {dict(G='good', M='moderate', P='poor')[t['co']]} ({FID[QJ[nm]['comparator']]})",
                                                                      f"outcome {dict(G='good', M='moderate', P='poor')[t['ou']]} ({FID[QJ[nm]['outcome']]})"]
        ex.append(f"<b>{esc(t['name'])}</b>: {', '.join(parts)} = {t['tot']} point{'' if t['tot'] == 1 else 's'} → {t['tier']}")
        if sid:
            claim(SN[sid], f"example {nm}", f"{t['tot']} points, {t['tier']}", QT19, ref=f"{QJ[nm]['points']} points, {QJ[nm]['tier'].split(' - ')[0]}",
                  ref_how="quality_tiers.json points/tier")
    return ex


def popup(pid, title, body, links=""):
    """a modal popup inside its slide (opened by an element with data-pop="pid"; closed by its button, a click outside it, or Esc)."""
    return (f'<div class="modal" id="{pid}" role="dialog" aria-modal="true" aria-label="{esc(title)}" hidden><div class="mbox">'
            f'<button class="mclose" type="button" aria-label="Close">✕ Close</button><h3 class="mh">{esc(title)}</h3>{body}'
            + (f'<div class="mlinks">{links}</div>' if links else "") + "</div></div>")


def applink(lab):
    return f'<a class="xref" href="#{lab}" data-goto="{lab}">{lab} · {esc(APPT[lab])}</a>'


def s_aims():
    sid = "s-aims"
    claim(SN[sid], "MIMIC-IV external validation done", "done", ROOT / "docs/v21/MIMIC_PAPER2.md", probe="7 cardiovascular trials", ref_src=ROOT / "docs/v21/MIMIC_PAPER2.md")
    chip = lambda grp, what, done: (f'<div class="chip{" done" if done else ""}"><span class="cg">{grp}</span> {what} '
                                    f'<span class="st">{"✓ done" if done else "planned"}</span></div>')
    aims = [
        (1, ICON["ecg"] + ICON["ehr"], "Integrate ECG and EHR foundation models into matching",
         "ECG encoder (BCL) · EHR foundation model (CLMBR-T) · easy to operationalize"),
        (2, ICON["bal"], "Covariate balance", "on held-out measurements"),
        (3, ICON["rct"], "Trial emulation and agreement with RCTs", "32 benchmark RCTs"),
        (4, ICON["glob"], "External validation",
         '<span class="chips">' + chip("EHR", "MIMIC-IV", True) + chip("Biobank", "UK Biobank", False)
         + chip("Trial cohorts", "dbGaP: ACCORD, WHI, CHS", False) + "</span>"),
    ]
    rows = "".join(f'<div class="aim fstep" data-step="{k}"><div class="ic">{ic}</div><div class="num">{k}</div>'
                   f'<div><div class="at">{esc(t)}</div><div class="as">{s if k == 4 else esc(s)}</div></div></div>' for k, ic, t, s in aims)
    body = f"""<p class="goal">The goal of <b>LATENT-RCT</b> is to bring unstructured information into trial emulation.</p>
<div class="aims4">{rows}</div>"""
    return sec(sid, "Aims", body, steps=5, cls="aimsl")


def s_overview():
    """slide 5: kept (number, title bar, footer) with an empty body for the user's own content (user feedback 2026-10-13)."""
    return sec("s-over", "Study overview", "")


def s_pipe():
    sid = "s-pipe"
    tr = CTX["trials"]
    QJ = json.load(open(QT19))
    tc = {t: sum(x["tier"] == t for x in tr) for t in TIERS}
    for t in TIERS:
        claim(SN[sid], f"v19 tier count {t}", str(tc[t]), QT19, ref=str(next(v for k, v in QJ["counts_tier"].items() if k.startswith(t))),
              ref_how="quality_tiers.json counts_tier")
    claim(SN[sid], "tier counts 3/12/17/6", "/".join(str(tc[t]) for t in TIERS), QT19, probe="3 were rated excellent, 12 good, 17 moderate and 6 limited", ref_src=SUPP)
    claim(SN[sid], "99 candidates -> 38 -> 32", "99 -> 38 -> 32", PAPER, probe="Of 99 candidate trials, 38 met the feasibility criteria and were emulated, and 32 were retained", ref_src=PAPER)
    ac = {a: sum(t["area"] == a and t["s32"] for t in tr) for a in AREAS}
    claim(SN[sid], "areas of the 32", ", ".join(f"{a} {ac[a]}" for a in AREAS), QT19,
          probe="atrial fibrillation (12), diabetes (7), heart failure (5), hypertension (2), acute coronary syndromes or myocardial infarction (2) and other indications (4)",
          ref_src=PAPER)
    claim(SN[sid], "size threshold", ">=300 with an ECG in the smaller arm; >=50 events", SUPP, probe="at least 300 patients with an ECG in the smaller arm and at least 50 pooled primary events", ref_src=SUPP)
    claim(SN[sid], "near-duplicate threshold", ">=80% shared records", SUPP, probe="Cohorts sharing 80% or more of patient–index date records", ref_src=SUPP)
    claim(SN[sid], "points rule", "F1-F5 1 point each; comparator/outcome 0/1/2; Limited >=4", QT19, probe="Each flag scored 1 point, and comparator and outcome fidelity scored 0, 1 or 2 points", ref_src=SUPP)
    W, H = 1192, 470
    s = [f'<svg viewBox="-3 0 {W + 6} {H}" style="width:100%;height:auto">']  # 3-unit pad: the edge boxes keep their borders

    def box(x, y, w, h, lines, fill="#fff", col=NAVY, fs=17, stroke=NAVY, bold0=True, anchor="middle", sw=2):
        o = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="6"/>'
        tx = x + w / 2 if anchor == "middle" else x + 14
        for i, l in enumerate(lines):
            yy = y + h / 2 + (i - (len(lines) - 1) / 2) * fs * 1.3 + fs * 0.35
            o += f'<text x="{tx}" y="{yy:.1f}" font-size="{fs}" text-anchor="{anchor}" fill="{col}" font-weight="{700 if bold0 and i == 0 else 400}">{esc(l)}</text>'
        return o

    def arr(x1, y1, x2, y2):
        a = math.atan2(y2 - y1, x2 - x1)
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2 - 3 * math.cos(a):.1f}" y2="{y2 - 3 * math.sin(a):.1f}" stroke="{NAVY}" stroke-width="2.5"/>'
                f'<path d="M{x2} {y2}L{x2 - 12 * math.cos(a - .4):.1f} {y2 - 12 * math.sin(a - .4):.1f}L{x2 - 12 * math.cos(a + .4):.1f} {y2 - 12 * math.sin(a + .4):.1f}Z" fill="{NAVY}"/>')
    yc = 130
    hint = lambda x, y: (f'<circle cx="{x + 7}" cy="{y - 4.5}" r="7.5" fill="{RED}"/><text x="{x + 7}" y="{y}" font-size="12" font-weight="700" '
                         f'text-anchor="middle" fill="#fff">i</text><text x="{x + 20}" y="{y}" font-size="12.5" font-style="italic" fill="{RED}">'
                         'click for the full criteria and examples</text>')
    # the flow populates one step after another: 99 -> feasibility -> 38 -> emulation quality -> 32 analysed -> clinical areas
    s.append(box(0, yc - 50, 128, 100, ["99", "candidate", "RCTs"], fs=18))
    s.append('<g class="build" data-step="1">' + arr(130, yc, 160, yc))
    s.append(f'<g class="ptrig" data-pop="pop-feas" aria-label="Feasibility criteria: details"><rect x="162" y="{yc - 108}" width="408" height="216" fill="#f5f5f8" stroke="{NAVY}" stroke-width="2" rx="6"/>')
    s.append(f'<text x="176" y="{yc - 78}" font-size="18" font-weight="700" fill="{NAVY}">Feasibility criteria</text>')
    for i, (lab, _, _) in enumerate(FEAS):
        s.append(f'<text x="176" y="{yc - 47 + i * 29}" font-size="14.5" fill="{NAVY}"><tspan font-weight="700">{i + 1}.</tspan> {esc(lab)}</text>')
    s.append(hint(176, yc + 98) + "</g></g>")
    s.append('<g class="build" data-step="2">' + arr(572, yc, 602, yc) + box(604, yc - 50, 112, 100, ["38", "feasible", "trials"], fs=18) + "</g>")
    qual = ["basic, rule-based points:", "• design flags F1–F5: 1 point each", "• comparator, outcome fidelity: 0 / 1 / 2",
            "Excellent 0 · Good 1–2 · Moderate 3", "Limited (≥4 points) excluded"]
    s.append('<g class="build" data-step="3">' + arr(718, yc, 748, yc))
    s.append(f'<g class="ptrig" data-pop="pop-qual" aria-label="Emulation-quality criteria: details"><rect x="750" y="{yc - 108}" width="324" height="216" fill="#f5f5f8" stroke="{NAVY}" stroke-width="2" rx="6"/>')
    s.append(f'<text x="764" y="{yc - 78}" font-size="18" font-weight="700" fill="{NAVY}">Emulation-quality criteria</text>')
    for i, l in enumerate(qual):
        s.append(f'<text x="764" y="{yc - 47 + i * 29}" font-size="15" fill="{RED if i == 4 else NAVY}">{esc(l)}</text>')
    s.append(hint(764, yc + 98).replace("the full criteria", "the rule") + "</g></g>")
    s.append('<g class="build" data-step="4">' + arr(1076, yc, 1100, yc) + box(1102, yc - 50, 90, 100, ["32", "analysed"], fs=18, fill=NAVY, col="#fff") + "</g>")
    # bottom right (with the 32): emulation quality of the 38; bottom left (last step): the 32 by clinical area
    y0 = 290
    s.append(f'<g class="build" data-step="5"><text x="0" y="{y0}" font-size="17" font-weight="700" fill="{NAVY}">The 32 analysed trials by clinical area</text>')
    lab = {"AF": "Atrial fibrillation", "HF": "Heart failure", "Diabetes": "Diabetes", "Hypertension": "Hypertension", "ACS / MI": "ACS / MI", "Other": "Other"}
    order = sorted(AREAS, key=lambda a: -ac[a])
    for i, a in enumerate(order):
        y = y0 + 16 + i * 27
        s.append(f'<text x="170" y="{y + 15}" font-size="15" text-anchor="end" fill="{NAVY}">{lab[a]}</text>'
                 f'<rect x="180" y="{y + 2}" width="{ac[a] * 30}" height="19" fill="{RED if a == "AF" else NAVY}"/>'
                 f'<text x="{186 + ac[a] * 30}" y="{y + 17}" font-size="15" font-weight="700" fill="{NAVY}">{ac[a]}</text>')
    s.append("</g>")
    x1 = 700
    s.append(f'<g class="build" data-step="4"><text x="{x1}" y="{y0}" font-size="17" font-weight="700" fill="{NAVY}">Emulation quality of the 38 feasible trials</text>')
    cols = {"Excellent": NAVY, "Good": "#5b5d86", "Moderate": "#c9cbd8", "Limited": "#fbe3e2"}
    xx, wsc = x1, 490 / 38
    for t in TIERS:
        w = tc[t] * wsc
        s.append(f'<rect x="{xx:.1f}" y="{y0 + 18}" width="{w:.1f}" height="40" fill="{cols[t]}" stroke="#fff"/>'
                 f'<text x="{xx + w / 2:.1f}" y="{y0 + 44}" font-size="16" font-weight="700" text-anchor="middle" fill="{"#fff" if t in ("Excellent", "Good") else (NAVY if t == "Moderate" else "#a8322e")}">{tc[t]}</text>'
                 f'<text x="{xx + w / 2:.1f}" y="{y0 + 78}" font-size="14" text-anchor="middle" fill="{NAVY if t != "Limited" else "#a8322e"}">{t}</text>')
        xx += w
    s.append(f'<line x1="{x1}" x2="{x1 + 32 * wsc:.1f}" y1="{y0 + 92}" y2="{y0 + 92}" stroke="{NAVY}" stroke-width="2"/>'
             f'<text x="{x1 + 16 * wsc:.1f}" y="{y0 + 112}" font-size="15" text-anchor="middle" fill="{NAVY}">analysed (32)</text>'
             f'<text x="{x1 + 35 * wsc:.1f}" y="{y0 + 112}" font-size="15" text-anchor="middle" fill="#a8322e">excluded</text>')
    s.append(f'<text x="{x1}" y="{y0 + 150}" font-size="14" fill="#55576f">Ratings from design information only, blind to all emulation results.</text></g>')
    s.append("</svg>")
    pops = popup("pop-feas", "Feasibility criteria (stage 1: 99 candidates → 38 emulated)",
                 f'<table class="t tq mt"><tr><th style="width:36%">Criterion</th><th>Example</th></tr>{feas_rows()}</table>'
                 f'<p class="small" style="margin-top:8px"><b>Designs and dates.</b> {DESIGNS}</p>', links="More: " + applink("A1") + " · " + applink("A3"))
    pops += popup("pop-qual", "Emulation-quality criteria (stage 2: v19 points rule; 38 → 32)",
                  f'<p class="mp">{QRULE}</p><h4 class="mh4">Examples</h4><p class="mp">{"<br>".join(q_examples())}</p>'
                  f'<p class="small" style="margin-top:8px">Tier counts of the 38: Excellent {tc["Excellent"]}, Good {tc["Good"]}, Moderate {tc["Moderate"]}, '
                  f'Limited {tc["Limited"]} (excluded). Framework v2.0 tiers are a sensitivity analysis (A4).</p>', links="More: " + applink("A2") + " (interactive quality viewer) · " + applink("A4"))
    return sec(sid, "LATENT-RCT pipeline", "".join(s), links=more("A1", "A2", "A3") + pops)  # popups outside .body: they cover the slide


ICON["shuf"] = ('<svg viewBox="0 0 48 44" width="46" height="42"><path d="M4 12 H14 C24 12 24 32 34 32 H40" fill="none" stroke="#0E103C" stroke-width="2.6"/>'
                '<path d="M4 32 H14 C24 32 24 12 34 12 H40" fill="none" stroke="#DC5A55" stroke-width="2.6"/>'
                '<path d="M38 6 L45 12 L38 18 Z" fill="#DC5A55"/><path d="M38 26 L45 32 L38 38 Z" fill="#0E103C"/></svg>')


def s_methods_design():
    """slide 7, "PSM experiments" (user feedback 2026-10-13): the PS levels one at a time, then the four comparison arms one at a
    time; details (hdPS, PS-Clinical, PS and matching) in popups. No PS-Flags; no ladder graphic."""
    sid = "s-meth1"
    sl = SN[sid]
    mi = "5-draw MI" if CTX["mi"] else "single imputation (MI pending)"
    claim(sl, "fixed penalty", "C = 1", PIPE, probe="fixed C = 1 for every specification", ref_src=PIPE)
    claim(sl, "caliper", "caliper 0.2 SD", PIPE, probe="caliper 0.2 SD", ref_src=PIPE)
    claim(sl, "failed-cell rule", "<11 matched pairs", PIPE, probe="Cells with <11 matched pairs", ref_src=PIPE)
    claim(sl, "ECG embedding dimension -> PCs", "256-d -> 32 PCs", PIPE, probe="256-d → 32 PCs within each trial", ref_src=PIPE)
    claim(sl, "CLMBR-T dimension -> PCs", "768-d -> 64 PCs", PIPE, probe="768-d → **64 PCs within each trial**", ref_src=PIPE)
    claim(sl, "CLMBR-T context", "last 4,096 tokens, index day excluded", PIPE, probe="last 4,096 tokens, **index day excluded**", ref_src=PIPE)
    claim(sl, "index-day ECG share (version 1)", "37%", HAND, probe="37% of ECGs are on the index day", ref_src=HAND)
    claim(sl, "ECG window", "[index - 365 d, index]", PIPE, probe="[index − 365 d, index]", ref_src=PIPE)
    claim(sl, "hdPS: top 200 indicators", "200", SUPP, probe="the top 200 indicators were added to the base covariates", ref_src=SUPP)
    claim(sl, "hdPS: candidate prevalence", ">=2%", SUPP, probe="with a prevalence of at least 2% were converted into indicators", ref_src=SUPP)
    claim(sl, "hdPS: base diagnoses", "9 to 13", SUPP, probe="demographics and 9 to 13 investigator-selected diagnoses", ref_src=SUPP)
    claim(sl, "hdPS: treatment-only ranking, random half, exposure drugs", "as stated", SUPP,
          probe="candidates were drawn from a random half of the code features, the other half being reserved for balance assessment, and the trial's exposure drugs were excluded",
          ref_src=SUPP)
    claim(sl, "hdPS: offset 0.001", "0.001", SUPP, probe="(with an offset of 0.001)", ref_src=SUPP)
    claim(sl, "PS-Clinical medication orders 3-10", "3 to 10", SUPP, probe="3 to 10 medication orders relevant to the clinical area", ref_src=SUPP)
    if CTX["mi"]:
        claim(sl, "PS-Clinical (no LVEF) 5-draw MI on version 1 cohorts", "5 draws", MI_V1DOC, probe="re-imputed with 5 independent draws", ref_src=MI_V1DOC)
    pl = lambda pid, txt: f'<a class="plink" href="#" data-pop="{pid}"><span class="ib">i</span>{txt}</a>'
    L = [("PS-Demo", "age, sex, index year", ""), ("PS-CVD5", "+ hypertension, T2D, CAD, AF, HF", "primary"),
         ("PS-CVD10", "+ CKD, COPD/asthma, PAD, stroke/TIA, valve disease", ""),
         ("hdPS", "PS-Demo + 9–13 diagnoses + <b>200 yes/no code flags</b> (no values, no dates) " + pl("pop-hdps", "what are the flags?"), ""),
         ("PS-Clinical (no LVEF)", f"+ measured vitals and labs, medication orders, visits; no echo; {mi} " + pl("pop-clin", "inputs"), "")]
    lv = "".join(f'<div class="lvl build{" prim" if tag else ""}" data-step="{k}"><div class="ln">{esc(n)}{f"<span class=tg>{tag}</span>" if tag else ""}</div>'
                 f'<div class="ld">{d}</div></div>' for k, (n, d, tag) in enumerate(L, 1))
    C = [(ICON["ecg"], "+ ECG representation", "ECG encoder → 32 PCs"), (ICON["ehr"], "+ CLMBR-T", "EHR foundation model → 64 PCs"),
         (ICON["ecg"] + ICON["ehr"], "+ ECG + CLMBR-T", "both"), (ICON["shuf"], "+ permuted placebo", "ECG shuffled between patients")]
    cm = "".join(f'<div class="cmp build" data-step="{len(L) + k}"><div class="cn">{k}</div><div class="ci">{ic}</div><div><div class="ct">{esc(t)}</div>'
                 f'<div class="cs">{esc(s)}</div></div></div>' for k, (ic, t, s) in enumerate(C, 1))
    body = f"""<div class="psm">
<div><h3 class="h3">PS levels (thin → rich)</h3>{lv}</div>
<div><h3 class="h3 build" data-step="{len(L) + 1}">Compared at every level</h3>{cm}</div>
</div>
<div class="pmstrip"><b>PS and matching:</b> logistic PS, C = 1 · 1:1 nearest neighbour, caliper 0.2 · {pl("pop-match", "details")}</div>"""
    pops = popup("pop-hdps", "hdPS: the 200 yes/no code flags", """<ul class="mul">
<li><b>Base:</b> PS-Demo + 9–13 investigator-selected diagnoses (prior 365 days).</li>
<li><b>Candidate flags:</b> pre-index diagnosis, medication and procedure codes with ≥2% prevalence, each turned into yes/no flags for <i>any</i>, <i>sporadic</i> (≥ median count among patients with the code) and <i>frequent</i> (≥ 75th percentile) occurrence; laboratory tests as <i>was measured</i> yes/no.</li>
<li><b>No values, no dates:</b> a flag records only whether (and how often) a code occurs before index.</li>
<li><b>How the 200 are chosen:</b> ranked by |log prevalence ratio| between the two treatment groups (offset 0.001); the top 200 enter the PS.</li>
<li><b>Treatment-only ranking:</b> the outcome is never used (unlike the original algorithm).</li>
<li><b>Random half held out:</b> candidates come from a random half of the code features; the other half is reserved for balance assessment.</li>
<li><b>Exposure drugs excluded</b> from the candidates.</li>
</ul><p class="small">Schneeweiss S, et al. <i>Epidemiology</i> 2009;20:512–522 (adapted; supplement eMethods).</p>""")
    pops += popup("pop-clin", "PS-Clinical (no LVEF): inputs", f"""<ul class="mul">
<li><b>Demographics and diagnoses:</b> age, sex, index year; AF, hypertension, diabetes, ischaemic heart disease/MI, CKD, COPD/asthma, PAD, stroke, valve disease; trial-specific diagnoses (e.g. heart failure, TIA, liver disease, prior bleeding). Prior 365 days.</li>
<li><b>Measured values</b> (latest in the prior 90 days; BMI 365 days): systolic and diastolic BP, heart rate, BMI, creatinine, potassium, sodium, haemoglobin.</li>
<li><b>Medication orders</b> (3–10 relevant to the clinical area, prior 90 days) and <b>utilisation</b> (outpatient, ED, inpatient encounters).</li>
<li><b>No LVEF and no echo measurement</b> in any PS: echo is the held-out test domain.</li>
<li><b>Missing values: {mi}</b> by chained equations (covariates and treatment as predictors, no outcome; LVEF neither imputed nor used). Per-item |SMD| averaged across the draws; HRs combined by Rubin's rules.</li>
<li><b>Leakage-corrected masks:</b> the 8 measured vitals/labs that are PS inputs, and eGFR (derived from creatinine), are not scored as held-out items at this level.</li>
</ul>""")
    pops += popup("pop-match", "PS and matching", """<ul class="mul">
<li><b>PS model:</b> L2-penalised logistic regression on standardised covariates, <b>fixed C = 1</b> for every level and arm (no tuning; a cross-validated penalty is a sensitivity analysis).</li>
<li><b>Representations</b> enter the PS as principal components computed within each trial: ECG (BCL self-supervised encoder, 256-d → 32 PCs; latest 12-lead ECG in [index − 365 d, index], index day included, 37% of ECGs) and CLMBR-T (frozen CLMBR-T-base on the coded record: diagnoses, drugs, procedures, measurement codes without values, visits; last 4,096 tokens, index day excluded; 768-d → 64 PCs).</li>
<li><b>Placebo:</b> permuted ECG, the embeddings shuffled between patients within each trial (same dimension, no information).</li>
<li><b>Matching:</b> 1:1 greedy nearest neighbour on the PS logit, <b>caliper 0.2 SD of the logit</b>, without replacement.</li>
<li><b>Failed cell:</b> fewer than 11 matched pairs.</li>
<li><b>Sensitivities:</b> caliper 0.1, 1:3 matching, IPTW, overlap weights, gradient-boosted PS.</li>
</ul>""")
    return sec(sid, "PSM experiments", body, links=more("A6") + pops)


def s_methods_panel():
    sid = "s-meth2"
    n0 = len(V2.CL)
    h = V2.s_methods_panel()
    cl_slide(n0, sid)
    h = one(h, "<tr><td>PS-Flags</td><td>none</td><td>held-out codes, prognostic score</td></tr>", "")  # PS-Flags: appendix note only (A6)
    return retitle(h, sid, "Methods: held-out panel, leakage map and endpoints")


def s_results2():
    """the balance results slide ("Results 2"; the user's "slide 13": love plot, domains, ladder): just the updated Figure 2
    (scripts/figures/make_figure2_latent.py), a minimal title and a one-line source note. Every number in the figure is registered
    as a claim and recomputed here from the version 1 cells with build_balance_explorer.pair_stats."""
    sid = "s-res2"
    sl = SN[sid]
    from PIL import Image
    assert FIG2.exists() and FIG2V.exists(), "run scripts/figures/make_figure2_latent.py first"
    im = Image.open(FIG2).convert("RGB")
    w, h = im.size
    H = 1160  # 2x the displayed height (580 px)
    im = im.resize((round(w * H / h), H), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    uri = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    CTX["fig2"] = dict(src_size=[w, h], embedded_size=list(im.size), bytes=len(b.getvalue()))
    V = json.load(open(FIG2V))
    T = T_("s32")
    G1 = CTX["G1"]
    for rg, lab in (("P1", "PS-Demo"), ("P5", "PS-CVD5"), ("PS10", "PS-CVD10"), ("hdPS200", "hdPS"), ("clinical_nolvef", "PS-Clinical (no LVEF, MI)")):
        c = V["C"][rg]
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            r = ps(G1, "main", rg, a, "base", "s32")
            claim(sl, f"Fig 2C {lab} + {a} relative change", f"{c['rr_' + a][0]:.1f}%", FIG2V, ref=f"{r['rr']:.1f}%",
                  ref_how="recomputed from the version 1 cells (build_balance_explorer.pair_stats)")
        for a in ("unmatched", "base", "ECG", "CLMBR", "ECG+CLMBR"):
            M = G1.block("main", rg, a, True)[np.ix_(T, BE.items("54"))]
            ok = np.isfinite(M).any(1)
            claim(sl, f"Fig 2C {lab} {a} mean |SMD|", f"{c[a]:.3f}", FIG2V, ref=f"{np.nanmean(M[ok], 1).mean():.3f}", ref_how="explorer ladder level on the cells")
    d = V["D"]
    r = ps(G1, "main", "P5", "ECG", "base", "s32")
    claim(sl, "Fig 2D trials improved", f"{int(d['improved'])} of {int(d['k'])}", FIG2V, ref=f"{r['better']} of {r['k']}", ref_how="pair_stats on the cells")
    claim(sl, "Fig 2D mean change (points)", f"{d['mean']:+.1f}", FIG2V, ref=f"{r['dpts']:+.1f}", ref_how="pair_stats on the cells")
    claim(sl, "Fig 2D P", fp(d["p"]), FIG2V, ref=fp(r["p"]), ref_how="exact one-sided sign-flip on the cells")
    for g, x in V["B"].items():
        js = BE.items("54") if g == "All 54" else V2.dom_items(g)
        for a in ("unmatched", "base", "ECG"):
            M = G1.block("main", "P5", a, True)[np.ix_(T, js)]
            ok = np.isfinite(M).any(1)
            claim(sl, f"Fig 2B {g} {a}", f"{x[a]:.3f}", FIG2V, ref=f"{np.nanmean(M[ok], 1).mean():.3f}", ref_how="explorer domain view (mean) on the cells")
    note = ("Version 1 cohorts · paper 1's 32 trials · 1:1 matching, caliper 0.2, C = 1 · 54 held-out items, leakage-corrected masks · "
            "PS-Clinical: 5-draw MI · scripts/figures/make_figure2_latent.py")
    body = (f'<img class="fig2" alt="Figure 2: covariate balance on the 54 held-out items" src="{uri}">'
            f'<div class="fig2src">{esc(note)}</div>')
    return sec(sid, "Results 2: covariate balance (Figure 2)", body, links=more("A4", "A5"))


def s_robust():
    sid = "s-rob"
    rows = []
    s, _ = stat_v1(sid, "permuted ECG vs PS alone (32)", "s32", "P5", "shufECG")
    e, erow = stat_v1(sid, "ECG vs permuted (32)", "s32", "P5", "ECG", "shufECG")
    rng = [stat_v1(sid, f"ECG vs permuted ({ts})", ts, "P5", "ECG", "shufECG")[0]["rr"] for ts in ("q:Excellent,Good", "all", "v2", "v2c")] + [e["rr"]]
    rtxt = f"{fx(min(rng))} to {fx(max(rng))}%"
    rows.append(("Placebo (permuted ECG)", f"Permuted vs PS alone: {ci(s['rr'], s['lo'], s['hi'])}, {pv(s['p'])} (two-sided). ECG vs permuted: {ci(e['rr'], e['lo'], e['hi'])}; {rtxt} across the five trial sets", "32"))
    cf, cfv = [], []
    for c, lab in (("main", "1:1, cal. 0.2"), ("cal01", "cal. 0.1"), ("m13", "1:3"), ("iptw", "IPTW"), ("overlap", "overlap"), ("gbm", "GBM PS")):
        x, _ = stat_v1(sid, f"PS method {c} (32)", "s32", "P5", "ECG", cfg=c)
        cf.append(f"{lab} {fx(x['rr'])}% ({fx(x['lo'])} to {fx(x['hi'])})")
        cfv.append(x)
    nex = sum(x["lo"] > 0 for x in cfv)
    neg = [lab for (c, lab), x in zip((("main", "1:1"), ("cal01", "cal. 0.1"), ("m13", "1:3"), ("iptw", "IPTW"), ("overlap", "overlap"), ("gbm", "GBM PS")), cfv) if x["rr"] <= 0]
    rows.append(("Six PS methods", "; ".join(cf) + f". {nex} of 6 CIs exclude 0" + (f"; the gradient-boosted PS shows no gain" if "GBM PS" in neg else ""), "32"))
    r5 = vc1("S32", "P5", "ECG")[0]
    r5m = mis_row("S32", "P5", "ECG") if CTX["mi"] else None
    clu = claim(SN[sid], "comparator-cluster sign-flip P (32)", fp(r5.m54_cluster_p), V2SUM / "contrasts.csv", ref=None if r5m is None else fp(r5m.m54_cluster_p),
                ref_how="v1 MI summary (independent run of the endpoint code; P5 row)")
    loo = claim(SN[sid], "leave-one-trial-out max P (32)", fp(r5.m54_loo_max_p), V2SUM / "contrasts.csv", ref=None if r5m is None else fp(r5m.m54_loo_max_p),
                ref_how="v1 MI summary (P5 row)")
    rows.append(("Comparator clusters; leave-one-trial-out", f"Cluster sign-flip {pv(r5.m54_cluster_p)} ({int(r5.m54_n_clusters)} comparator clusters); largest leave-one-out {pv(r5.m54_loo_max_p)}", "32"))
    if CTX["mi"]:
        mi, _ = stat_v1(sid, "PS-Clinical (no LVEF, MI) + ECG (32)", "s32", "clinical_nolvef", "ECG")
        M = CTX["MIS"]
        dr = [M[(M.set == "S32") & (M.config == "main") & (M.rung_a == f"clinical_nolvef#{k}") & (M.arm_a == "ECG") & (M.arm_b == "base")].iloc[0].relred54 for k in range(1, 6)]
        drt = claim(SN[sid], "MI draw range (32)", f"{fx(min(dr))} to {fx(max(dr))}%", MI_V1SUM / "contrasts.csv", probe="(range −1.8 to 6.0)", ref_src=MI_V1DOC)
        sg = M[(M.set == "S32") & (M.config == "main") & (M.rung_a == "clinical_nolvef_v1single") & (M.arm_a == "ECG") & (M.arm_b == "base")]
        rows.append(("Multiple imputation (PS-Clinical, no LVEF)", f"5-draw MI: {ci(mi['rr'], mi['lo'], mi['hi'])}, {pv(mi['p'])}; single draws {drt}. Single-draw estimates should not be reported", "32"))
    else:
        rows.append(("Multiple imputation (PS-Clinical, no LVEF)", "MI pending on the version 1 cohorts (single imputation shown)", "32"))
    RR = pd.read_csv(V2.RRS).set_index(["set", "arm"]).loc[("S32", "ECG")]
    fv2 = claim(SN[sid], "spec-v2 fixed cohorts (32)", f"{fx(RR.relred54_v2)}%", V2.RRS, probe="PS-CVD5 + ECG 6.6% vs 8.8% on version 1", ref_src=PIPE)
    rnd = claim(SN[sid], "random removal (32)", f"{fx(RR.relred54_random_median)} ({fx(RR.relred54_random_p5)} to {fx(RR.relred54_random_p95)})", V2.RRS,
                probe=f"| S32 | + ECG | {fx(RR.relred54_v1)} | {fx(RR.relred54_v2)} | {fx(RR.relred54_random_median)} ({fx(RR.relred54_random_p5)} to {fx(RR.relred54_random_p95)}) |", ref_src=FIXD)
    rows.append(("Spec-v2 cohort fixes (sensitivity; A5)", f"{fx(RR.relred54_v1)}% → {fv2} with the fixes; removing the same numbers of patients at random: median {rnd}%, so the drop reflects smaller cohorts", "32"))
    v29, _ = stat_v1(sid, "framework v2.0 provisional 29 (v1 cohorts)", "v2", "P5", "ECG")
    v30, _ = stat_v1(sid, "framework v2.0 rescored 30 (v1 cohorts)", "v2c", "P5", "ECG")
    rows.append(("Framework v2.0 trial sets (sensitivity; A4)", f"Provisional 29: {ci(v29['rr'], v29['lo'], v29['hi'])}; rescored 30: {ci(v30['rr'], v30['lo'], v30['hi'])} (version 1 cohorts)", "29 / 30"))
    claim(SN[sid], "CV-tuned penalty (v1)", "5.7% (−0.5 to 11.4)", HAND, probe="A CV-tuned penalty gives 5.7% (−0.5 to 11.4)", ref_src=HAND)
    claim(SN[sid], "no index-day ECG (v1)", "6.9% (0.4–13.4)", HAND, probe="gives 6.9% (0.4–13.4)", ref_src=HAND)
    claim(SN[sid], "R2 CV-tuned 35 trials", "4.7%", HAND, probe="S1 + ECG: 4.7% (−0.4 to 9.9)", ref_src=HAND)
    rows.append(("Earlier sensitivities (version 1 cohorts)", "CV-tuned penalty 5.7% (−0.5 to 11.4); index-day ECGs excluded 6.9% (0.4 to 13.4); R2 (CV-tuned PS, 35 trials) 4.7%", "32"))
    body = "".join(f'<tr><td><b>{esc(a)}</b></td><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows)
    allv = [x["rr"] for x in cfv] + [v29["rr"], v30["rr"], RR.relred54_v2, 5.7, 6.9]
    pos = sum(v > 0 for v in allv)
    lo_, hi_ = math.floor(min(v for v in allv if v > 0)), math.ceil(max(allv))
    claim(SN[sid], "positive checks", f"{pos} of {len(allv)}", "this slide's estimates", ref=str(pos) + f" of {len(allv)}", ref_how="count of the slide's estimates > 0")
    claim(SN[sid], "size range", f"{lo_}–{hi_}%", "this slide's estimates", ref=f"{lo_}–{hi_}%", ref_how="floor(min positive)-ceil(max)")
    return sec(sid, "Robustness of PS-CVD5 + ECG vs PS-CVD5 (54 items; paper 1's 32)", f"""
<table class="t tsm rob"><tr><th style="width:250px">Check</th><th>Result</th><th>Trials</th></tr>{body}</table>
<p style="font-size:19px;margin-top:12px">The direction holds in {pos} of {len(allv)} estimates (all but the gradient-boosted PS). Where positive, the size is about <b>{lo_}–{hi_}%</b> and moves by a few points with the PS method, cohort definition, trial set and penalty.</p>""",
               links=more("A5", "A4"))


def s_takehome():
    sid = "s-take"
    p5, _ = stat_v1(sid, "take-home PS-CVD5 + ECG (32)", "s32", "P5", "ECG")
    d, _ = stat_v1(sid, "take-home PS-Demo + ECG (32)", "s32", "P1", "ECG")
    e, _ = stat_v1(sid, "take-home ECG vs permuted (32)", "s32", "P5", "ECG", "shufECG")
    c10, _ = stat_v1(sid, "take-home PS-CVD10 + ECG (32)", "s32", "PS10", "ECG")
    h, _ = stat_v1(sid, "take-home hdPS + ECG (32)", "s32", "hdPS200", "ECG")
    m, _ = stat_v1(sid, "take-home PS-Clinical + ECG (32)", "s32", "clinical_nolvef", "ECG")
    bps = [agree_v1(sid, f"take-home P5 agreement {ts}", ts, "P5")[1] for ts in ("s32", "all", "v2")]
    _, bc10 = agree_v1(sid, "take-home CVD10 agreement 32", "s32", "PS10")
    claim(SN[sid], "CVD10 + ECG permutation P .003 (pipeline)", fp(bc10), V2SUM / "contrasts.csv", probe="CVD10 + ECG showed a trial-specific signal (permutation P = .003)", ref_src=PIPE)
    clin = "5-draw MI" if CTX["mi"] else "single imputation; MI pending"
    return sec(sid, "Take-home", f"""
<ol class="aims" style="margin-top:4px">
  <li><b>The ECG improves held-out balance when the PS is thin</b> (demographics and a few diagnoses): PS-CVD5 + ECG {ci(p5['rr'], p5['lo'], p5['hi'])} on paper 1's 32 trials (PS-Demo + ECG {fx(d['rr'])}%). It beats its permuted placebo ({fx(e['rr'])}%).</li>
  <li><b>The gain is smaller with richer PS:</b> PS-CVD10 + ECG {fx(c10['rr'])}%, hdPS + ECG {fx(h['rr'])}%, PS-Clinical (no LVEF; {clin}) + ECG {ci(m['rr'], m['lo'], m['hi'])}, concentrated in observed LVEF and echo structure.</li>
  <li><b>No trial-specific agreement with the RCTs</b> for PS-CVD5 + ECG: benchmark-permutation P ≥ {min(bps):.2f} in the 32, all 38 and the 29-trial set. (CVD10 + ECG gave P = {fp(bc10)} on the 32: post hoc, exploratory only.)</li>
  <li><b>Supporting:</b> the plasmode (the ECG removes part of a hidden physiological confounder's bias beyond PS-CVD5) and MIMIC-IV (similar balance gain, no agreement gain).</li>
  <li><b>Caveats:</b> one health system; quality tiers graded post hoc with LLM-assisted raters (clinician review pending); post hoc switch of the primary to PS-CVD5; the return to version 1 cohorts was decided after the fixed-cohort results were known (fixed cohorts: 6.6%; both reported).</li>
</ol>""", links=more("A6"))


def s_decisions():
    sid = "s-dec"
    return sec(sid, "Open decisions", """
<div style="display:grid;grid-template-columns:1fr 1fr;gap:36px">
<ol class="dec">
  <li><b>Clinician review</b> of the v19 emulation-quality tiers and the physiologic trial labels (both LLM-assisted so far).</li>
  <li><b>PS-Clinical (no LVEF), 5-draw MI on version 1 cohorts</b>: review the result (3.2%, P = .075 on the 32) and the unstable PS-alone HRs across draws; decide whether to add "was measured" flags.</li>
  <li><b>Disclosure</b> of the post hoc decisions: PS-CVD5 as primary; return to version 1 cohorts after the fixed-cohort results; spec-v2 fixes and framework v2.0 as sensitivities.</li>
  <li><b>Known version 1 cohort issues</b> (COMET metoprolol formulation and LVEF, EMPEROR-Preserved DPP-4i agents, class washouts, LIFE ECG-LVH, TRANSFORM-HF time zero): limitation text, or targeted rebuilds.</li>
  <li><b>Plasmode re-check</b> on the final trial set (pipeline.md §8, pending).</li>
</ol>
<ol class="dec" start="6">
  <li><b>CLMBR-T</b>: back on the aims slide and as a comparison arm (slide 7, Figure 2C); how and where its results return (main text vs supplement), to be confirmed with the PI.</li>
  <li><b>External validation scope</b>: UK Biobank and dbGaP trial cohorts (ACCORD, WHI, CHS) are planned, not started.</li>
  <li><b>Study name</b> LATENT-RCT (for now): "RCT" may be read as a randomized-trial label by journals and indexers (alternative: LATENT-TTE).</li>
  <li><b>Manuscript file</b> (paper.md vs paper2.md) and the methods lock (pipeline.md §10–11).</li>
</ol>
</div>""", links=more("A6"))


# ================================================================ appendix
def s_a1():
    sid = "a-sel"
    claim(SN[sid], "three stages 18 / 15 / 5", "18 / 15 / 5", SUPP, probe="18 trials in which the analytic approach was developed; 15 trials, drawn largely from RCT-DUPLICATE", ref_src=SUPP)
    claim(SN[sid], "99 = 63 + 8 + 28; range 99-104", "63 + 8 + 28 = 99; 99–104", AUDM, probe="trial_specs.py (63 unique after collapsing 3 design variants) + v17 candidates (8) + v18 AF candidates (28)", ref_src=AUDM)
    claim(SN[sid], "defensible range 99-104", "99–104", AUDM, probe="Defensible range 99–104", ref_src=AUDM)
    claim(SN[sid], "PRISMA: 161 eligible", "161", SEARCH, probe="Eligible (meet E1-E7)                                161", ref_src=SEARCH)
    claim(SN[sid], "PRISMA: 68/161 = 42%", "42%", SEARCH, ref=f"{round(100 * 68 / 161)}%", ref_how="68/161")
    claim(SN[sid], "PRISMA: recall 68/70 = 97%", "97%", SEARCH, ref=f"{round(100 * 68 / 70)}%", ref_how="68/70")
    claim(SN[sid], "PRISMA: hits / unique", "5,646 / 4,611", SEARCH, probe="5,646 hits, 4,611 unique PMIDs", ref_src=SEARCH)
    claim(SN[sid], "PRISMA: CT.gov records", "908", SEARCH, probe="The query returned **908 registry records**", ref_src=SEARCH)
    claim(SN[sid], "PRISMA: new A-C candidates", "38", SEARCH, probe="[38 A-C, 4 of them legacy]", ref_src=SEARCH)
    claim(SN[sid], "ACTIVE W vs RE-LY overlap", "69%", SUPP, probe="69% between ACTIVE W and RE-LY", ref_src=SUPP)
    claim(SN[sid], "ACCOMPLISH reuses 96% of ALLHAT", "96%", CAND17, probe="ACCOMPLISH reuses 96% of the ALLHAT records", ref_src=CAND17)
    claim(SN[sid], "development data-sufficiency threshold", "400 PS-Clinical pairs", SUPP, probe="fewer than 400 matched pairs with PS-Clinical", ref_src=SUPP)
    claim(SN[sid], "index dates 2011-2024", "2011–2024", PIPE, probe="index dates 2011–2024", ref_src=PIPE)
    claim(SN[sid], "index dates: v1 audit 2025 note", "COMET into 2025", CLRE, probe="2011–2025: COMET has", ref_src=CLRE)
    return sec(sid, "Trial selection in depth", """
<div style="display:grid;grid-template-columns:1.05fr 1fr;gap:26px">
<div>
  <h3 class="h3">How the 99 candidates were assembled (three waves)</h3>
  <table class="t tq"><tr><th>Wave</th><th>Source of candidates</th><th>Emulated</th></tr>
  <tr><td class="n">1. Development</td><td>Landmark cardiovascular trials and investigator review (63 unique candidates after collapsing design variants)</td><td>18 (analytic approach developed here)</td></tr>
  <tr><td class="n">2. v1.7, prespecified</td><td>List drawn largely from RCT-DUPLICATE, plus investigator scouting (8 further candidates)</td><td>15 (specs, benchmarks and plan committed before any result)</td></tr>
  <tr><td class="n">3. v1.8, prespecified</td><td>AF scouting (28 candidates); the AF hypothesis arose from a post hoc wave-2 pattern</td><td>5</td></tr></table>
  <p class="small" style="margin-top:5px"><b>Counting rule:</b> one RCT = one candidate; design variants of a trial count once, grouped screening entries count separately: 63 + 8 + 28 = 99. Ambiguous groupings (a peri-procedural group; PARTNER 2A/3) give a defensible range of 99–104 (manuscript audit 2026-10-01).</p>
  <h3 class="h3" style="margin-top:8px">Coverage check: PRISMA-style structured search (2026-10-13)</h3>
  <p class="small">PubMed (10 area queries, 6 journals; 5,646 hits, 4,611 unique records), ClinicalTrials.gov (908 records), the RCT-DUPLICATE list and a guideline hand search; one LLM screener. <b>161</b> eligible trials: <b>42%</b> already in the pool (68/161); <b>97% recall</b> of the pool's eligible trials (68/70); 38 new candidates in groups A–C (exploratory) and an infeasible group D. Not used for the current 38.</p>
</div>
<div>
  <h3 class="h3">Feasibility criteria, with examples</h3>
  <table class="t tq"><tr><th>Criterion</th><th>Example</th></tr>
  {FEAS_ROWS}</table>
  <h3 class="h3" style="margin-top:8px">Designs and dates</h3>
  <p class="small">{DESIGNS}</p>
</div>
</div>""".replace("{FEAS_ROWS}", feas_rows()).replace("{DESIGNS}", DESIGNS))


def s_a2():
    sid = "a-qual"
    ex = q_examples(sid)
    claim(SN[sid], "re-rating agreement 82% / kappa 0.71", "82%; κ 0.71", SUPP, probe="Agreement on the three-class result was 82% (Cohen κ, 0.71)", ref_src=SUPP)
    return sec(sid, "Emulation-quality criteria (v19 points rule) and quality viewer", f"""
<div class="qrule">
  <div>{QRULE}</div>
  <div class="qex">{'<br>'.join(ex)}</div>
</div>
<div class="qview">
  <div class="ctrl" id="qv-ctrl"></div>
  <div id="qv-tab"></div>
  <div class="side" id="qv-det"></div>
</div>""")


def s_a3():
    rows_p = V2.load_md_table(PAPER, "| Area")
    rows_t = V2.load_md_table(PICOT, "| Area")
    assert len(rows_p) == len(rows_t) == 38
    diffs = [(a["Trial"], k, a[k], b[k]) for a, b in zip(rows_p, rows_t) for k in a if a[k] != b.get(k)]
    CTX["table1_diffs"] = diffs
    rows = rows_t  # table1_picot.md preferred (the user's working copy); differences reported
    tr = {t["full"]: t for t in CTX["trials"]}
    out, parts = "", []
    for k, r in enumerate(rows):
        sid = "a-t1" if r["Area"] in ("AF", "HF") else "a-t1b"
        if k and sid != prev:
            parts.append(out)
            out = ""
        prev = sid
        t = tr[r["Trial"]]
        tq = r["Emulation quality (points)"]
        claim(SN[sid], f"Table 1 tier {r['Trial']}", tq, PICOT, ref=f"{t['tier']} ({t['tot']})", ref_how="quality_tiers.json")
        claim(SN[sid], f"Table 1 horizon {r['Trial']}", r["Time (mo)"], PICOT, ref=str(t["hz"]), ref_how="quality_tiers.json horizon_months")
        rct = r["RCT estimate (CI)"].split(" [")[0]
        hr = math.exp(t["rb"])
        v = rct.split(" ")[0]
        inv = f"{hr:.2f}" != v and f"{1 / hr:.2f}" == v  # benchmark stored in the emulation's arm orientation (e.g. COMET)
        claim(SN[sid], f"Table 1 RCT estimate {r['Trial']}", v, PICOT, ref=f"{1 / hr if inv else hr:.2f}",
              ref_how="deck RCT benchmark " + ("1/exp(rb) (arms stored in the reverse orientation)" if inv else "exp(rb)"))
        an = t["s32"]
        out += (f'<tr class="{"an" if an else "ex"}"><td>{esc(r["Area"])}</td><td class="n">{esc(r["Trial"])}</td><td>{esc(r["Population"])}</td><td>{esc(r["Intervention"])}</td>'
                f'<td>{esc(r["Comparator"])}</td><td>{esc(r["Outcome (RCT primary endpoint)"])}</td><td>{esc(r["Time (mo)"])}</td><td>{esc(r["RCT estimate (CI)"])}</td>'
                f'<td class="nw">{esc(tq)}</td><td>{"yes" if an else "no"}</td></tr>')
    parts.append(out)
    assert len(parts) == 2 and [x.count("<tr") for x in parts] == [17, 21], [x.count("<tr") for x in parts]
    hdr = ('<colgroup><col style="width:68px"><col style="width:128px"><col style="width:170px"><col style="width:112px"><col style="width:118px">'
           '<col style="width:250px"><col style="width:24px"><col style="width:166px"><col style="width:86px"><col style="width:56px"></colgroup>') + '<tr><th>Area</th><th>Trial</th><th>Population</th><th>Intervention</th><th>Comparator</th><th>Outcome (RCT primary endpoint)</th><th>Mo</th><th>RCT estimate (CI)</th><th>Quality (pts)</th><th>In 32</th></tr>'
    foot = '<p class="xs" style="margin-top:4px">HR unless indicated; 95% CI unless indicated. Mo = trial-matched horizon. Quality = v19 tier (design points); Limited (grey) excluded. Source: docs/paper/table1_picot.md (= paper.md Table 1).</p>'
    return "".join(sec(sid, f"All 38 emulated trials (paper Table 1), {k + 1} of 2: {areas}", f'<div class="t1wrap"><table class="t1">{hdr}{p}</table></div>{foot}')
                   for k, (sid, areas, p) in enumerate(zip(("a-t1", "a-t1b"), ("AF, HF", "hypertension, ACS / MI, diabetes, other"), parts)))


def s_a4(trials_old, Q):
    sid = "a-fw"
    n0 = len(V2.CL)
    h = V2.s_framework(trials_old, Q)
    cl_slide(n0, sid)
    h = one(h, "<p class=\"small\" style=\"margin-top:8px\">Analysed set = Excellent + Good + Moderate.",
            "<p class=\"small\" style=\"margin-top:8px\"><b>Sensitivity analysis only</b> (primary: v19 tiers, A2). Analysed set = Excellent + Good + Moderate.")
    return retitle(h, sid, "Emulation-quality framework v2.0 (sensitivity)")


def s_a5(trials_old, EX, RR):
    sid = "a-fix"
    t32 = [dict(t, v2c=t["s32"]) for t in trials_old]  # colour = in paper 1's 32 (the primary set)
    n0 = len(V2.CL)
    h = V2.s_fixes(t32, EX, RR)
    cl_slide(n0, sid)
    h = one(h, "(navy = in the analysed 30)", "(navy = in paper 1's 32)")
    h = one(h, '<h3 class="h3">Five kinds of fix', '<p class="small red" style="margin:0 0 4px"><b>Sensitivity analysis</b>; the primary analysis uses the version 1 cohorts.</p>\n    <h3 class="h3">Five kinds of fix')
    h = one(h, '<p style="font-size:18px;margin-top:10px">Removing the', '<p style="font-size:16px;margin-top:8px">Removing the')
    return retitle(h, sid, "Spec-v2 cohort fixes (sensitivity): what was removed, and does it explain the smaller ECG gain?")


def s_a6():
    sid = "a-hist"
    claim(SN[sid], "R2 4.7%; 8.6% at C = 1", "4.7%; 8.6%", HAND, probe="8.6% at C = 1", ref_src=HAND)
    claim(SN[sid], "fixed cohorts 6.6% vs 8.8%", "6.6% vs 8.8%", PIPE, probe="PS-CVD5 + ECG 6.6% vs 8.8% on version 1", ref_src=PIPE)
    return sec(sid, "Design history (10-01 → 10-15)", """
<div style="display:grid;grid-template-columns:1fr 1fr;gap:34px">
<div><h3 class="h3">10-01 → 10-09</h3><ul class="chg">
  <li><b>Primary contrast:</b> PS-CVD5 + ECG vs PS-CVD5 (paper 1: PS-Demo); fixed L2 penalty C = 1 for every PS; 1:1 matching, caliper 0.2.</li>
  <li><b>Leakage audit:</b> echo EF duplicates LVEF and eGFR derives from creatinine, so the primary panel is 54 non-coded items with leakage-corrected masking (58 items secondary).</li>
  <li><b>PS-Clinical without LVEF</b> (no PS contains any echo measurement), 5-draw multiple imputation.</li>
  <li><b>R2 restart</b> (branch <code>r2</code>): with a CV-tuned PS, PS-CVD5 + ECG fell to 4.7%, mostly from the CV penalty (8.6% at C = 1). Reverted to version 1, audited, hardened.</li>
  <li><b>Explored:</b> spec-v2 cohort fixes and emulation-quality framework v2.0.</li>
</ul></div>
<div><h3 class="h3">10-09 → 10-13 (user decisions)</h3><ul class="chg">
  <li><b>Primary back to version 1 cohorts and paper 1's 32 trials</b> (v19 tiers). Decided after the fixed-cohort results were known (6.6% vs 8.8%): both are reported.</li>
  <li><b>Spec-v2 cohort fixes</b> (A5) and <b>framework v2.0 tiers</b> (A4; 29 / 30 trials) become sensitivity analyses.</li>
  <li><b>PS-Clinical (no LVEF)</b>: 5-draw MI re-run on the version 1 cohorts.</li>
  <li><b>Study name LATENT-RCT</b> (replaces TRACE-ECG); <b>CLMBR-T</b> back on the aims, and as a comparison arm in the PSM experiments (slide 7) and Figure 2C.</li>
  <li><b>Note: PS-Flags</b> (PS-Demo + yes/no ICD-10 3-character diagnosis flags, ≥1% prevalence) is a supplement comparator only; it is not on the main slides and is selectable, off by default, in the balance explorer.</li>
</ul></div>
</div>""")


# ================================================================ CSS / JS added to the template
EXTRA_CSS = r"""
/* ===== LATENT-RCT deck (2026-10-15) additions ===== */
.xrefs{position:absolute;left:22px;bottom:19px;font-size:12.5px;color:var(--muted);z-index:4;max-width:880px}
.xrefs a{color:var(--navy);text-decoration:underline;cursor:pointer}
.slide.app .ttl{background:#5b5d86}
.slide .build{transition:opacity .35s}
.slide .build.hid{opacity:0;visibility:hidden}
section.s1001 .build.rise{transition:opacity .8s ease,transform .8s ease}
section.s1001 .build.rise.hid{transform:translateY(26px)}
section.s1001 ol.pts{padding-left:32px;margin:0}
section.s1001 ol.pts li{font-size:25px;line-height:1.35;margin:0 0 30px}
.fstep{transition:opacity .45s,transform .45s}
.fstep.hid{opacity:0;visibility:hidden;transform:translateY(14px)}
.fstep.dim{opacity:.25}
.aimsl p.goal{font-size:27px;margin:4px 0 22px;line-height:1.3}
.aims4{display:flex;flex-direction:column;gap:16px}
.aim{display:grid;grid-template-columns:120px 40px 1fr;align-items:center;gap:14px;border:2px solid var(--navy);padding:10px 16px;min-height:72px}
.aim .ic{display:flex;gap:6px;align-items:center;justify-content:center}
.aim .ic svg{transform:scale(1.25)}
.aim .num{position:static;font-size:30px;font-weight:700;color:var(--red);text-align:center}
.aim .at{font-size:23px;font-weight:700;line-height:1.25}
.aim .as{font-size:16px;color:var(--muted);margin-top:3px;line-height:1.3}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin-top:2px}
.chip{border:2px dashed #8a8d99;padding:3px 10px;font-size:15px;color:var(--navy)}
.chip.done{border:2px solid #1a7f4b;background:#eaf6ef}
.chip .cg{font-weight:700}
.chip .st{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;margin-left:6px;color:#8a8d99}
.chip.done .st{color:#1a7f4b}
.slide.full{background:#fff}
.fullfig{position:absolute;left:0;top:0;width:1280px;height:720px}
.figph{position:absolute;inset:40px;border:3px dashed var(--red);display:flex;align-items:center;justify-content:center;text-align:center;font-size:22px;color:var(--red)}
.qrule{display:grid;grid-template-columns:1.6fr 1fr;gap:14px;font-size:11.2px;line-height:1.3;margin:-8px 0 4px}
.qrule .qex{font-size:10.8px;background:var(--band);padding:4px 8px}
.qview{display:grid;grid-template-columns:150px 1fr 220px;gap:10px;height:478px}
.qview .ctrl{border-right:1px solid var(--line);padding-right:6px}
.qview .side{overflow-y:auto}
#qv-tab{overflow:hidden}
#qv-tab table{border-collapse:collapse;width:100%}
#qv-tab th{font-size:9.5px;font-weight:600;background:var(--navy);color:#fff;padding:2px 2px;text-align:center}
#qv-tab td{font-size:9.6px;padding:0 2px;border-bottom:1px solid var(--line);text-align:center;color:var(--navy);white-space:nowrap;line-height:10.2px;height:10.2px}
#qv-tab td.l,#qv-tab th.l{text-align:left}
#qv-tab td.P{color:var(--red);font-weight:700}
#qv-tab td.v2{background:#f6f6fa}
#qv-tab tr.ex td{color:#a8322e}
#qv-tab tr:hover td,#qv-tab tr.sel td{background:#fbeceb;cursor:pointer}
#qv-tab .tier{min-width:46px;font-size:9px}
.t1wrap{margin-top:-6px}
table.t1{border-collapse:collapse;width:100%;table-layout:fixed}
table.t1 th{font-size:10.5px;background:var(--navy);color:#fff;padding:2px 3px;text-align:left;font-weight:600}
table.t1 td{font-size:10px;padding:1.2px 3px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.25;color:var(--navy)}
table.t1 td.n{font-weight:700;white-space:nowrap}
table.t1 td.nw{white-space:nowrap}
table.t1 tr.an td{background:#fff}
table.t1 tr.ex td{color:#8a8d99;background:#f6f6f8}
/* popups (slides 6 and 7) */
.modal{position:absolute;inset:0;background:rgba(14,16,60,.38);display:flex;align-items:center;justify-content:center;z-index:60}
.modal[hidden]{display:none}
.mbox{position:relative;background:#fff;border:2px solid var(--navy);width:1060px;max-height:610px;overflow-y:auto;padding:16px 26px 14px;box-sizing:border-box;box-shadow:0 10px 32px rgba(0,0,0,.28)}
.mclose{position:absolute;top:10px;right:12px;border:2px solid var(--navy);background:#fff;color:var(--navy);font-weight:700;font-size:14px;font-family:inherit;padding:3px 10px;cursor:pointer}
.mclose:hover,.mclose:focus{background:var(--navy);color:#fff}
.mbox h3.mh{font-size:21px;margin:0 90px 10px 0;color:var(--navy)}
.mbox h4.mh4{font-size:15px;margin:10px 0 4px;color:var(--navy);text-transform:uppercase;letter-spacing:.3px}
.mbox .mp{font-size:15px;line-height:1.4;margin:0;color:var(--navy)}
.mbox table.mt td,.mbox table.mt th{font-size:14px;padding:5px 8px}
.mbox ul.mul{margin:0 0 6px;padding-left:22px}
.mbox ul.mul li{font-size:16px;line-height:1.38;margin:0 0 7px;color:var(--navy)}
.mbox .mlinks{font-size:13px;color:var(--muted);margin-top:8px}
.mbox .mlinks a{color:var(--navy);text-decoration:underline}
g.ptrig{cursor:pointer}
g.ptrig:hover rect,g.ptrig:focus rect{stroke:var(--red);stroke-width:3}
g.ptrig:focus{outline:none}
a.plink{color:var(--red);font-weight:700;font-size:.9em;text-decoration:none;border-bottom:1px dotted var(--red);white-space:nowrap;cursor:pointer}
a.plink .ib{display:inline-block;width:1.15em;height:1.15em;line-height:1.15em;border-radius:50%;background:var(--red);color:#fff;text-align:center;font-size:.8em;margin-right:4px;vertical-align:.08em}
/* slide 7: PSM experiments */
.psm{display:grid;grid-template-columns:640px 1fr;gap:34px}
.lvl{display:grid;grid-template-columns:230px 1fr;align-items:center;gap:10px;border-left:7px solid var(--navy);background:#f3f3f7;padding:8px 14px;margin:0 0 9px;min-height:58px;box-sizing:border-box}
.lvl.prim{border-left-color:var(--red);background:#fbeceb}
.lvl .ln{font-size:21px;font-weight:700;color:var(--navy)}
.lvl .ln .tg{display:block;font-size:12px;font-weight:700;color:var(--red);text-transform:uppercase;letter-spacing:.4px}
.lvl .ld{font-size:16px;line-height:1.3;color:var(--navy)}
.cmp{display:grid;grid-template-columns:34px 128px 1fr;align-items:center;gap:8px;border:2px solid var(--navy);padding:6px 12px;margin:0 0 10px;min-height:64px;box-sizing:border-box}
.cmp .cn{font-size:26px;font-weight:700;color:var(--red);text-align:center}
.cmp .ci{display:flex;gap:6px;align-items:center;justify-content:center}
.cmp .ct{font-size:21px;font-weight:700;color:var(--navy)}
.cmp .cs{font-size:14.5px;color:var(--muted)}
.pmstrip{position:absolute;left:0;right:0;bottom:6px;font-size:17px;color:var(--navy);border-top:1px solid var(--line);padding-top:8px}
/* the balance results slide: Figure 2 */
img.fig2{display:block;margin:-6px auto 0;height:556px;width:auto;max-width:100%}
.fig2src{text-align:center;font-size:12px;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
"""
POP_JS = r"""
/* ===== popups (slides 6 and 7): open on click / Enter; close with the button, a click outside the box, or Esc. While a popup is
   open, no key reaches the deck (arrows do not navigate); navigating away closes it. ===== */
let POP = null;
function popClose() { if (POP) { POP.hidden = true; const t = POP._trig; POP = null; if (t && t.focus) t.focus({preventScroll: true}); } }
function popOpen(id, trig) { const m = document.getElementById(id); if (!m) return; if (POP) popClose(); m.hidden = false; m._trig = trig; POP = m; const b = m.querySelector(".mclose"); if (b) b.focus({preventScroll: true}); }
function popInit() {
  document.querySelectorAll("[data-pop]").forEach(el => {
    el.setAttribute("tabindex", "0"); el.setAttribute("role", "button");
    el.addEventListener("click", e => { e.preventDefault(); e.stopPropagation(); popOpen(el.dataset.pop, el); });
    el.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); e.stopPropagation(); popOpen(el.dataset.pop, el); } });
  });
  document.querySelectorAll(".modal").forEach(m => m.addEventListener("click", e => {
    e.stopPropagation();
    if (e.target === m || e.target.closest(".mclose")) { e.preventDefault(); popClose(); }
  }));
  addEventListener("keydown", e => { if (!POP) return; e.stopImmediatePropagation(); if (e.key === "Escape") { e.preventDefault(); popClose(); } else if (e.key === " ") e.preventDefault(); }, true);
}
"""

QV_JS = r"""
/* ===== A2: interactive emulation-quality viewer (v19 points; framework v2.0 toggle) ===== */
const QFID = {G: "good", M: "moderate", P: "poor"}, QPT = {G: 0, M: 1, P: 2}, QI2 = ["EL", "TZ", "TS", "CO", "OU", "FU", "ES", "BM", "DA", "SI"];
const QTI = {Excellent: 0, Good: 1, Moderate: 2, Limited: 3};
function qWhy(t) {
  const parts = t.fl.map((v, i) => v ? "F" + (i + 1) : null).filter(Boolean);
  if (QPT[t.co]) parts.push(`comparator ${QFID[t.co]} (${QPT[t.co]})`);
  if (QPT[t.ou]) parts.push(`outcome ${QFID[t.ou]} (${QPT[t.ou]})`);
  return (parts.length ? parts.join(" + ") : "no deviation") + ` = ${t.tot} point${t.tot === 1 ? "" : "s"}`;
}
function qvInit() {
  $("#qv-ctrl").innerHTML = `
  <label class="h">Sort by</label><select id="qv-sort"><option value="tier">v19 tier, points</option><option value="area">Area</option><option value="name">Trial</option><option value="tv2">v2.0 tier (sens.)</option></select>
  <label class="h">Show</label><select id="qv-filt"><option value="all">All 38</option><option value="an">Analysed (32)</option><option value="ex">Excluded (Limited)</option></select>
  <label class="cb" style="margin-top:8px"><input type="checkbox" id="qv-v2">Framework v2.0 (sensitivity)</label>
  <div class="desc" style="margin-top:8px">v19 points rule (primary): F1–F5 = design flags; Comp. / Outc. = comparator / outcome fidelity (G 0, M 1, P 2). Tier: Excellent 0, Good 1–2, Moderate 3 (or capped), Limited ≥4 (excluded). Tick to add the framework v2.0 items (EL–SI, 0–2), its total and tiers. Click a row for the rationale.</div>`;
  for (const id of ["qv-sort", "qv-filt", "qv-v2"]) $("#" + id).onchange = qvUpdate;
  qvUpdate();
}
let QSEL = null;
function qvUpdate() {
  const v2 = $("#qv-v2").checked, srt = $("#qv-sort").value, f = $("#qv-filt").value;
  let T = D.trials.map((t, i) => i).filter(i => f === "all" || (f === "an" ? D.trials[i].s32 : !D.trials[i].s32));
  const key = {tier: t => [QTI[t.t19], t.tot, AREAS.indexOf(t.area), t.name], area: t => [AREAS.indexOf(t.area), QTI[t.t19], t.tot, t.name], name: t => [t.name],
    tv2: t => [QTI[t.tv2], t.tot2, t.name]}[srt];
  T.sort((a, b) => { const ka = key(D.trials[a]), kb = key(D.trials[b]); for (let i = 0; i < ka.length; i++) { if (ka[i] < kb[i]) return -1; if (ka[i] > kb[i]) return 1; } return 0; });
  const tg = q => `<span class="tier t${QTI[q]}">${q}</span>`;
  let h = `<table><tr><th class="l">Trial</th><th class="l">Area</th><th>F1</th><th>F2</th><th>F3</th><th>F4</th><th>F5</th><th>Comp.</th><th>Outc.</th><th>Pts</th><th class="l">v19 tier</th><th class="l">Analysed</th>` +
    (v2 ? QI2.map(x => `<th>${x}</th>`).join("") + `<th>Tot</th><th class="l">v2.0 (spec-v2)</th><th class="l">v2.0 (v1 coh.)</th><th>in 30</th>` : "") + `</tr>`;
  for (const i of T) { const t = D.trials[i];
    h += `<tr class="${t.s32 ? "" : "ex"} ${QSEL === i ? "sel" : ""}" data-i="${i}"><td class="l"><b>${esc(t.name)}</b>${v2 && t.prov ? "†" : ""}</td><td class="l">${esc(t.area)}</td>` +
      t.fl.map(v => `<td>${v ? "✓" : ""}</td>`).join("") + `<td class="${t.co === "P" ? "P" : ""}">${t.co}</td><td class="${t.ou === "P" ? "P" : ""}">${t.ou}</td><td><b>${t.tot}</b></td><td class="l">${tg(t.t19)}</td>` +
      `<td class="l">${t.s32 ? "yes" : "no (≥4 pts)"}</td>` +
      (v2 ? t.it.map(v => `<td class="v2 ${v === 2 ? "P" : ""}">${v || ""}</td>`).join("") + `<td class="v2"><b>${t.tot2}</b></td><td class="l v2">${tg(t.tv2)}</td><td class="l v2">${tg(t.tq1)}</td><td class="v2">${t.v2c ? "✓" : ""}</td>` : "") + `</tr>`; }
  $("#qv-tab").innerHTML = h + `</table>`;
  $("#qv-tab").querySelectorAll("tr[data-i]").forEach(r => r.onclick = () => { QSEL = +r.dataset.i; qvUpdate(); });
  const t = QSEL === null ? null : D.trials[QSEL];
  $("#qv-det").innerHTML = !t ? `<div class="note" style="margin-top:20px">Click a trial for its items, points and rationale.</div>` :
    `<h4>${esc(t.full)}</h4><div class="note"><b>${esc(t.area)}</b>; horizon ${t.hz} mo</div><div class="note"><b>v19:</b> ${esc(qWhy(t))} → <b>${t.t19}</b>${t.cap ? " (capped)" : ""}; ${t.s32 ? "<b>analysed</b>" : "<b style='color:#a8322e'>excluded (Limited)</b>"}</div>` +
    `<div class="note">${esc(t.rat)}</div>` + (v2 ? `<div class="note"><b>Framework v2.0 (sensitivity):</b> total ${t.tot2} → ${t.tv2} (spec-v2 cohorts), ${t.tq1} (version 1 cohorts)${t.prov ? "; † a provisional item could change the tier" : ""}</div>` : "");
}
"""

NAV_JS = r"""
/* ===== deck mechanics (2026-10-01 deck; 2026-10-15: appendix labels, hash links, focus builds) ===== */
const slides = [...document.querySelectorAll(".slide")];
const label = i => slides[i].dataset.app || String(i + 1);
slides.forEach((sl, i) => {
  if (sl.dataset.notitle || sl.classList.contains("full")) return;
  sl.insertAdjacentHTML("afterbegin", `<div class="ttl">${sl.dataset.app ? sl.dataset.app + " · " : ""}${sl.dataset.title}</div><div class="rule top"></div><div class="num">${label(i)}</div>` +
    `<div class="rule bot"></div><div class="foot"><b>CarDS</b>Lab</div><img class="logo" alt="" src="${LOGO}">`);
});
let cur = 0, step = 0, backTo = null;
const nSteps = sl => Math.max(+sl.dataset.steps || 0, ...[...sl.querySelectorAll(".build,.fstep")].map(e => +e.dataset.step || 0));
function applyBuild() {
  const sl = slides[cur], last = Math.max(0, ...[...sl.querySelectorAll(".fstep")].map(e => +e.dataset.step || 0));
  sl.querySelectorAll(".build").forEach(e => e.classList.toggle("hid", (+e.dataset.step || 0) > step));
  sl.querySelectorAll(".fstep").forEach(e => { const k = +e.dataset.step || 0; e.classList.toggle("hid", k > step); e.classList.toggle("dim", k < step && step <= last); });
}
function next() { if (POP) { popClose(); return; } if (step < nSteps(slides[cur])) { step++; applyBuild(); } else if (cur < slides.length - 1) show(cur + 1); }
function prev() { if (POP) { popClose(); return; } if (step > 0) { step--; applyBuild(); } else if (cur > 0) show(cur - 1, true); }
function indexOf(key) {
  if (key === null || key === undefined || key === "") return -1;
  let i = slides.findIndex(s => s.dataset.app === key || s.id === key);
  if (i < 0 && /^\d+$/.test(key)) i = +key - 1;
  return i >= 0 && i < slides.length ? i : -1;
}
const fromHash = () => Math.max(0, indexOf(decodeURIComponent(location.hash.slice(1))));
function show(i, built) {
  popClose();
  cur =Math.max(0, Math.min(slides.length - 1, i));
  step = built ? nSteps(slides[cur]) : 0; applyBuild();
  slides.forEach((s, k) => s.classList.toggle("active", k === cur));
  $("#nav-count").textContent = `${slides[cur].dataset.app ? slides[cur].dataset.app + " · " : ""}${cur + 1} / ${slides.length}`;
  tip.style.display = "none";
  const sl = slides[cur];
  sl.querySelectorAll("a.xref.back").forEach(a => { const j = backTo !== null && !slides[backTo].dataset.app ? backTo : indexOf(a.dataset.goto);
    a.dataset.target = j; a.querySelector(".lbl").textContent = label(j); a.setAttribute("href", "#" + label(j)); });
  if (location.hash !== "#" + label(cur)) history.replaceState(null, "", "#" + label(cur));
}
function linkInit() {
  document.querySelectorAll("a.xref").forEach(a => a.addEventListener("click", e => {
    e.preventDefault(); e.stopPropagation();
    if (a.classList.contains("back")) { const j = +a.dataset.target; backTo = null; show(j >= 0 ? j : indexOf(a.dataset.goto), true); return; }
    const j = indexOf(a.dataset.goto); if (j < 0) return;
    if (!slides[cur].dataset.app) backTo = cur;
    show(j);
  }));
  addEventListener("hashchange", () => { const j = fromHash(); if (j !== cur) show(j); });
}
function fit() { const s = Math.min(innerWidth / 1280, innerHeight / 720); $("#stage").style.transform = `translate(-50%,-50%) scale(${s})`; }
"""


# ================================================================ explorer patches
def patch_explorer(js):
    P = [
        ('let h = `<option value="v2c">Analysed set, rescored (${n(t => t.v2c)}; provisional)</option><option value="v2">Provisional v2.0 set (${n(t => t.v2)})</option><option value="s32">Paper 1\'s set (${n(t => t.s32)} trials)</option>',
         'let h = `<option value="s32">Primary: paper 1\'s ${n(t => t.s32)} (v19 tiers)</option><option value="v2c">Sens.: framework v2.0, rescored (${n(t => t.v2c)})</option><option value="v2">Sens.: framework v2.0, provisional (${n(t => t.v2)})</option>'),
        ('<optgroup label="Quality tier (v2.0, rescored)">', '<optgroup label="Quality tier (v19, paper 1)">'),
        ('<select id="c-coh"><option value="v2" selected>Spec-v2 fixed cohorts (primary)</option><option value="v1">Version 1 cohorts (as built)</option></select>',
         '<select id="c-coh"><option value="v1" selected>Version 1 cohorts (primary)</option><option value="v2">Spec-v2 fixed cohorts (sensitivity)</option></select>'),
        ('" Version 1: single imputation (draw 1)."', '" Version 1: ' + ('5-draw multiple imputation; per-item |SMD| averaged across the draws."' if CTX["mi"] else 'single imputation (draw 1); MI pending."')),
        ('"Cohorts as built for paper 1 (no fixes); the expanded panel exists only here."', '"Version 1 cohorts as built (primary; original selection criteria); the expanded panel exists only here."'),
        ('$("#c-trials").value === "v2c" && panel === "54"', '$("#c-trials").value === "s32" && panel === "54"'),
        ('<b>Primary analysis (pipeline.md; ECG-only paper):</b>', '<b>Primary analysis (pipeline.md, 2026-10-13):</b>'),
        ('rescored analysed set (30 trials; provisional, not frozen). ${M.coh === "v2" ? "Spec-v2 fixed cohorts." : "Version 1 cohorts (pre-fix reference)."}',
         'paper 1\'s 32 trials (v19 tiers). ${M.coh === "v1" ? "Version 1 cohorts." : "Spec-v2 fixed cohorts (sensitivity analysis)."}'),
        ('const COH = {v2: "Spec-v2 fixed cohorts", v1: "Version 1 cohorts"};', 'const COH = {v2: "Spec-v2 fixed cohorts (sensitivity)", v1: "Version 1 cohorts"};'),
    ]
    for a, b in P:
        js = one(js, a, b)
    return js


def build_template(T1001, deck1001, D):
    T = V2.TEMPLATE
    h = T
    h = one(h, "<title>TRACE-ECG | CarDS Lab update | October 9, 2026</title>", "<title>LATENT-RCT | CarDS Lab | 15 October 2026</title>")
    h = one(h, "</style>", intro_css(T1001, deck1001) + EXTRA_CSS + "</style>")
    h = one(h, '<section class="slide" data-title="Results 1: covariate balance explorer (spec-v2 fixed cohorts by default)" id="s-bal">',
            '<section class="slide" data-title="Results 1: covariate balance explorer" id="s-bal">')
    h = one(h, '    <div class="side" id="sum"></div>\n  </div>\n</section>', '    <div class="side" id="sum"></div>\n  </div>\n' + more("A4", "A5") + "\n</section>")
    h = one(h, '<div class="chart" style="padding:2px 10px;overflow-y:auto"><svg id="agq-svg" viewBox="0 0 900 300" style="width:100%;height:auto;flex:none"></svg><div id="agq-tab"></div></div>\n  </div>\n</section>',
            '<div class="chart" style="padding:2px 10px;overflow-y:auto"><svg id="agq-svg" viewBox="0 0 900 300" style="width:100%;height:auto;flex:none"></svg><div id="agq-tab"></div></div>\n  </div>\n' + more("A2") + "\n</section>")
    h = one(h, 'const TSRC = {tier: "Framework v2.0, rescored (spec-v2 cohorts)", tq1: "Framework v2.0, version 1 cohorts", t19: "v19 tiers (paper 1)"};',
            'const TSRC = {t19: "v19 tiers (paper 1; primary)", tv2: "Framework v2.0, rescored on spec-v2 cohorts (sensitivity)", tq1: "Framework v2.0, version 1 cohorts (sensitivity)"};')
    h = one(h, 'const cohOpt = `<option value="v2" selected>Spec-v2 fixed cohorts (primary)</option><option value="v1">Version 1 cohorts (as built)</option>`;',
            'const cohOpt = `<option value="v1" selected>Version 1 cohorts (primary)</option><option value="v2">Spec-v2 fixed cohorts (sensitivity)</option>`;')
    h = one(h, "PS-Clinical (no LVEF) on the spec-v2 cohorts: HRs combined over 5 imputation draws (Rubin).",
            "PS-Clinical (no LVEF): HRs combined over 5 imputation draws (Rubin) on both cohort versions." if CTX["mi"] else
            "PS-Clinical (no LVEF): spec-v2 cohorts, HRs combined over 5 imputation draws (Rubin); version 1 cohorts, single imputation (MI pending).")
    h = one(h, "All 38 emulated trials, grouped by their quality tier. Tiers were assigned blind to the results; the rescored tiers are provisional (not frozen; LLM raters, no clinician review yet).",
            "All 38 emulated trials, grouped by quality tier (default: v19 tiers, as paper 1). Tiers were assigned from design information, blind to the results, by LLM-assisted raters; no clinician review yet. Framework v2.0 tiers: sensitivity.")
    # deck mechanics: replace from the chrome block to the fit() function
    i = h.index("/* ===== deck mechanics (2026-10-01 deck) ===== */")
    j = h.index('addEventListener("resize", fit);', i)
    h = h[:i] + intro_js(T1001, deck1001) + QV_JS + POP_JS + NAV_JS + h[j:]
    h = one(h, '$("#nav-next").onclick = next;\n',
            '$("#nav-next").onclick = next;\n/* a click on a slide with builds (outside any control, link or popup) reveals the next step (2026-10-01 deck) */\n'
            '$("#stage").addEventListener("click", e => { if (!POP && nSteps(slides[cur]) && !e.target.closest("select,input,label,button,a,.ctrl,.side,.modal,[data-pop]")) next(); });\n')
    h = one(h, "init(); emuInit(); agqInit(); fit();\nshow((parseInt(location.hash.slice(1), 10) || 1) - 1);",
            "drawIntro(); qvInit(); init(); emuInit(); agqInit(); linkInit(); popInit(); fit();\nshow(fromHash());")
    return h


# ================================================================ validation inputs (headless check)
def balance_combos(D, g1, g2):
    full = {"v1": BE.Grid(g1["G"], g1["U"], g1["ex"]), "v2": BE.Grid(g2["G"], g2["U"], g2["ex"])}
    emb = {"v1": BE.Grid.from_data(D, "v1"), "v2": BE.Grid.from_data(D, "v2")}
    tr = D["trials"]
    combos = []
    clean = lambda r: {k: (None if isinstance(v, float) and not np.isfinite(v) else float(v)) for k, v in r.items()}

    def add(src, coh, cfg, rg, a, b, ts, panel, leak, exp, sided="one", tag=""):
        T = BE.trial_set(tr, ts)
        combos.append(dict(source=src, tag=tag, coh=coh, cfg=cfg, rung=rg, arm=a, ref=b, trials=ts, panel=panel, leak=bool(leak), thr=0.1, sided=sided,
                           py_full=clean(BE.pair_stats(full[coh], cfg, rg, a, b, T, panel, leak)), py_emb=clean(BE.pair_stats(emb[coh], cfg, rg, a, b, T, panel, leak)),
                           expected=exp))
    VC = CTX["VC"]
    V1 = VC[(VC.cohort == "v1") & (VC.kind == "within") & VC.arm_a.isin(["ECG", "shufECG"]) & VC.arm_b.isin(["base", "shufECG"])
            & VC.rung_a.isin(["P1", "P5", "PS10", "Flags", "hdPS200"] + ([] if CTX["mi"] else ["clinical_nolvef"]))]
    SM = {"S32": "s32", "S38": "all", "S29": "v2", "Snew": "v2c"}
    for _, s in V1.iterrows():
        if not (s.config == "main" or s.rung_a == "P5"):
            continue
        for panel in ("54", "58"):
            pre, mm = ("relred54", "m54") if panel == "54" else ("relred58", "m58")
            tag = "REQUIRED default (v1, 32, PS-CVD5, 54 leak)" if (s.set == "S32" and s.config == "main" and s.rung_a == "P5" and s.arm_a == "ECG" and s.arm_b == "base" and panel == "54") else ""
            add("v2_cohorts summary (cohort v1)", "v1", s.config, s.rung_a, s.arm_a, s.arm_b, SM[s.set], panel, True,
                dict(rr=s[pre], lo=s[pre + "_lo"], hi=s[pre + "_hi"], p_m=s[f"{mm}_p"], lower=s[f"{mm}_better"]), sided=s.sided, tag=tag)
    if CTX["mi"]:
        M = CTX["MIS"]
        M = M[M.kind.isin(["within", "ladder"]) & (M.rung_a == M.rung_b) & M.rung_a.isin(["clinical_nolvef_mi", "P5"]) & M.arm_a.isin(["ECG", "shufECG"])
              & M.arm_b.isin(["base", "shufECG"]) & M.set.isin(list(SM))]
        for _, s in M.iterrows():
            if s.config != "main" and s.rung_a != "clinical_nolvef_mi":
                continue
            rg = "clinical_nolvef" if s.rung_a == "clinical_nolvef_mi" else s.rung_a
            for panel in ("54", "58"):
                pre, mm = ("relred54", "m54") if panel == "54" else ("relred58", "m58")
                add("v1 MI summary", "v1", s.config, rg, s.arm_a, s.arm_b, SM[s.set], panel, True,
                    dict(rr=s[pre], lo=s[pre + "_lo"], hi=s[pre + "_hi"], p_m=s[f"{mm}_p"], lower=s[f"{mm}_better"]), sided=s.sided,
                    tag="REQUIRED PS-Clinical MI v1 32" if (s.set == "S32" and s.config == "main" and rg == "clinical_nolvef" and s.arm_a == "ECG" and s.arm_b == "base" and panel == "54") else "")
    for (src, ts, cfg, rg, a, panel, leak, exp) in BE.EXPECT:
        aa, bb = (a.split("|") + ["base"])[:2]
        if rg in V2.RUNGS_D and aa in V2.ARMS_D and bb in V2.ARMS_D and not (rg == "clinical_nolvef"):
            add(src, "v1", cfg, rg, aa, bb, ts, panel, leak, exp, sided="two" if "p_m2" in exp else "one",
                tag="REQUIRED paper 1 PS-Demo 11.4%" if (src == "Paper 1 eTable 3A" and ts == "s32" and rg == "P1" and aa == "ECG" and cfg == "main") else "")
    MC = pd.read_csv(MISUM / "contrasts.csv")
    MCm = MC[MC.kind.isin(["ladder", "within"]) & MC.rung_a.isin(["P1", "P5", "PS10", "hdPS200", "clinical_nolvef_mi"]) & (MC.rung_a == MC.rung_b)
             & (MC.config == "main") & MC.set.isin(["S32", "S38", "S29", "Snew"]) & MC.arm_a.isin(["ECG", "shufECG"]) & MC.arm_b.isin(["base", "shufECG"])]
    for _, s in MCm.iterrows():
        rg = "clinical_nolvef" if s.rung_a == "clinical_nolvef_mi" else s.rung_a
        add("psclin_mi summary (spec-v2)", "v2", "main", rg, s.arm_a, s.arm_b, SM[s.set], "54", True,
            dict(rr=s.relred54, lo=s.relred54_lo, hi=s.relred54_hi, p_m=s.m54_p, lower=s.m54_better), sided=s.sided)
    for coh in ("v1", "v2"):  # computed-only combinations (no summary): v19 tier filters, areas
        for ts in ("q:Excellent,Good", "q:Moderate", "area:AF", "area:Diabetes", "phys:yes,s32"):
            for rg in ("P1", "P5", "hdPS200", "clinical_nolvef"):
                add("computed (pair_stats)", coh, "main", rg, "ECG", "base", ts, "54", True, {})
    return combos


def emu_refs(D):
    out = []
    VC = CTX["VC"]
    V1 = VC[(VC.cohort == "v1") & (VC.kind == "within") & (VC.config == "main") & VC.rung_a.isin(["P1", "P5", "PS10", "hdPS200"]) & (VC.arm_b == "base")
            & VC.arm_a.isin(["ECG", "shufECG"])]
    SM = {"S32": "s32", "S38": "all", "S29": "v2", "Snew": "v2c"}
    rows = [(s, s.rung_a) for _, s in V1.iterrows()]
    if CTX["mi"]:
        M = CTX["MIS"]
        rows += [(s, "clinical_nolvef") for _, s in M[(M.kind == "within") & (M.config == "main") & (M.rung_a == "clinical_nolvef_mi") & (M.arm_b == "base")
                                                       & M.arm_a.isin(["ECG", "shufECG"]) & M.set.isin(list(SM))].iterrows()]
    for s, rg in rows:
        T = BE.trial_set(D["trials"], SM[s.set])
        out.append(dict(coh="v1", cfg="main", rung=rg, arm=s.arm_a, trials=SM[s.set], sum_absd_a=s.absd_a, sum_absd_b=s.absd_b, sum_better=s.absd_better,
                        sum_bshuf=s.bshuf_p, py=V2.agree_py(D, "v1", "main", rg, s.arm_a, T), py_base=V2.agree_py(D, "v1", "main", rg, "base", T)))
    return out


# ================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.parse_args()
    os.umask(0o077)
    SCR.mkdir(parents=True, exist_ok=True)
    g = BE.load_grid()
    g2 = BE.load_grid_v2(g)
    html09, trials_old, Q = build_1009(g, g2)
    assert html09 == DECK1009.read_text(), "regenerated 10-09 deck differs from the committed file"
    print(f"10-09 deck regenerated: byte-identical to {DECK1009.relative_to(ROOT)}")
    V2.CL.clear()
    g1, mi = load_v1(g)
    CTX.update(mi=mi, g1=g1, g2=g2, VC=V2.get_contrasts()[1])
    if mi:
        CTX["MIS"] = pd.read_csv(MI_V1SUM / "contrasts.csv")
    print("PS-Clinical (no LVEF), version 1 cohorts:", "5-draw MI cells" if mi else "single imputation (MI pending)")
    trials = trials_new(trials_old, g1)
    CTX["trials"] = trials
    D = V2.build_data(g1, g2, trials)
    D["EST"]["v1"] = V2.est_block(g1)  # (build_data already uses g1; explicit for clarity)
    CTX["D"] = D
    V2.GRID2.update(grid=BE.Grid(g2["G"], g2["U"], g2["ex"]), D=D)
    CTX["G1"], CTX["E1"] = BE.Grid(g1["G"], g1["U"], g1["ex"]), BE.Grid.from_data(D, "v1")
    # check the PS-Clinical MI cells against the MI summary on the primary contrast (coordinator reference 3.2% (-1.0 to 7.2), 19/32)
    if mi:
        r = ps(CTX["G1"], "main", "clinical_nolvef", "ECG", "base", "s32")
        assert f"{r['rr']:.1f}|{r['lo']:.1f}|{r['hi']:.1f}|{r['lower']}" == "3.2|-1.0|7.2|19", r
    EX = load_ex()
    RR = pd.read_csv(V2.RRS)
    T1001, deck1001 = L1.TEMPLATE, DECK1001.read_text()
    static1 = [intro_markup(T1001, deck1001), s_aims(), s_overview(), s_pipe(), s_methods_design(), s_methods_panel()]
    static2 = [s_results2()]
    static3 = [s_robust()]
    static4 = [retitle(V2.s_plasmode(), "s-plas", "Plasmode: a known truth with a hidden physiological confounder (version 1 cohorts)"),
               retitle(V2.s_mimic(), "s-mimic", "External replication: MIMIC-IV (PS-CVD5 analog ± ECG)"),
               s_takehome(), s_decisions(), s_a1(), s_a2(), s_a3(), s_a4(trials_old, Q), s_a5(trials_old, EX, RR), s_a6()]
    for c in V2.CL:  # plasmode / MIMIC claims carry V2's slide numbers 14 / 15
        if c["slide"] in (14, 15):
            c["slide"] = SN["s-plas"] if c["slide"] == 14 else SN["s-mimic"]
    h = build_template(T1001, deck1001, D)
    h = (h.replace("__TITLE__", s_title()).replace("__STATIC1__", "".join(static1)).replace("__STATIC2__", "".join(static2))
         .replace("__STATIC3__", "".join(static3)).replace("__STATIC4__", "".join(static4))
         .replace("__EXPLORER_JS__", patch_explorer(V2.explorer_js())).replace("__LOGO__", V2.logo_uri(None))
         .replace("__DATA__", json.dumps(D, separators=(",", ":"), allow_nan=False)))
    for bad in ("http://", "https://", "@import", "<link", "src=\"//", "__"):
        if bad == "__":
            assert not re.search(r"__[A-Z0-9]+__", h), re.search(r"__[A-Z0-9]+__", h).group(0)
            continue
        assert bad not in h.replace("http://www.w3.org/2000/svg", ""), bad
    vis = re.sub(r"<script>.*?</script>", " ", h, flags=re.S)
    assert "TRACE-ECG" not in re.sub(r"Study name LATENT-RCT</b> \(replaces TRACE-ECG\)", "", vis), "old study name left in the visible text"
    assert not re.search(r"[Pp]rovisional:|not frozen", vis), re.search(r".{60}([Pp]rovisional:|not frozen).{30}", vis)
    secs = re.findall(r'<section class="slide[^"]*"[^>]*>', h)
    ids = [re.search(r' id="([^"]+)"', x).group(1) for x in secs]
    assert ids == MAIN + [s for s, _, _, _ in APP], ids
    old = os.umask(0o022)
    OUT.write_text(h)
    os.umask(old)
    print(f"wrote {OUT} ({len(h) / 1e6:.2f} MB)")
    titles = [(re.search(r' id="([^"]+)"', x).group(1), re.search(r' data-title="([^"]+)"', x).group(1)) for x in secs]
    for sid, t in titles:
        print(f"{SN[sid]:>3}  {t}")
    C = pd.DataFrame(V2.CL)
    C.to_csv(SCR / "claims.csv", index=False)
    with open(SCR / "claims.md", "w") as f:
        f.write("| Slide | Claim | Value | Source | Independent check | Match |\n|---|---|---|---|---|---|\n")
        for r in V2.CL:
            f.write(f"| {r['slide']} | {r['claim']} | {r['value']} | {r['source']} | {r['check'].replace('|', '/')} | "
                    f"{'yes' if r['match'] else ('NO' if r['match'] is False else 'n/a')} |\n")
    print(f"claims: {len(C)}; checked {int(C.match.notna().sum())}; matched {int((C.match == True).sum())}; "  # noqa: E712
          f"mismatched {int((C.match == False).sum())}")  # noqa: E712
    if (C.match == False).any():  # noqa: E712
        print(C[C.match == False].to_string())  # noqa: E712
    meta = dict(mi=mi, fig2=CTX.get("fig2"), table1_diffs=CTX.get("table1_diffs"), slides=[(SN[s], t) for s, t in titles])
    json.dump(meta, open(SCR / "build_meta.json", "w"), indent=1, default=str)
    combos = balance_combos(D, g1, g2)
    json.dump(combos, open(SCR / "balance_combos.json", "w"), indent=0)
    json.dump(emu_refs(D), open(SCR / "emu_refs.json", "w"), indent=0)
    print(f"balance combos: {len(combos)}; table1 differences paper.md vs table1_picot.md: {len(CTX.get('table1_diffs') or [])}")


if __name__ == "__main__":
    main()
