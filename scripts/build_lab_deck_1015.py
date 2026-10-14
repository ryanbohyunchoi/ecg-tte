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

Revision of 2026-10-14 (docs/queue/QUEUE_2026_10_14_S31.md; pipeline.md update 2026-10-14): PRIMARY trial set = "s31" (paper 1's
32 minus PROTECT AF, excluded at feasibility after the size rule was raised from >=300 to >=350 patients with an ECG in the smaller
arm): 99 -> 37 feasible -> 31 analysed (v19 tiers 3 / 11 / 17 / 6; AF 11). Disclosed as post hoc; paper 1's 32 (with PROTECT AF)
is a sensitivity analysis and stays selectable (as do all 38) in the explorers, where s31 is the default. Static s31 numbers come
from the s31 Python summaries (scripts/s31/s31_summaries.py; audits/claude-s31-20261014/summary_{v1,mi}) and are re-derived from
the cells (build_balance_explorer.pair_stats) or the deck's embedded data in the claims table; the robustness rows not in those
summaries are taken from docs/s31/S31_RESULTS.md (scripts/s31/s31_numbers.py) and probed there. Outputs of this builder now go to
audits/claude-s31-20261014/deck (the 2026-10-13 run in audits/claude-lab-deck-1015-v2 is kept).

Revision of 2026-10-14, second job (docs/queue/QUEUE_2026_10_14_DECK2.md): slide 4 gets a one-step graphic of the two
representations after aim 1 (raw ECG waveform -> AI-ECG encoder -> embedding; coded patient timeline -> CLMBR-T -> embedding; both
-> propensity score matching); slide 6 loses the former appendix A1 (trial selection; the popups keep the criteria, examples,
designs and dates) and the "blind to results" wording; Table 1 is one scrollable appendix slide; slide 7: Ridge (L2) logistic
regression, PS-Clinical before hdPS, no "no LVEF" labels, the former A6 (design history) removed; slide 8 = "Methods: covariate
balancing" (endpoints and tests), its panel / leakage map / masking moved to a new appendix slide; Figure 2 now precedes the
balance explorer and is built from the per-panel PNGs, revealed A + B, then C, then D, without the source line. Appendix renumbered.

Main slides: 1 title; 2 Background (10-01); 3 Problem (10-01 schematic, click reveal of the unmeasured side + three points); 4 Aims
(four aims, revealed one at a time; the representations graphic between aims 1 and 2); 5 study overview (empty body); 6 LATENT-RCT
pipeline; 7 PSM experiments; 8 methods: covariate balancing; 9 results 1 (Figure 2); 10 results 2 (balance explorer); 11 emulation
explorer; 12 robustness; 13 agreement by quality; 14 plasmode; 15 MIMIC-IV; 16 take-home; 17 open decisions. Appendix A1-A5
(hash-linked; "More:" links on main slides, "Back to slide N" on every appendix slide): A1 emulation-quality criteria + interactive
quality viewer (v19; framework v2.0 toggle); A2 all 38 trials (Table 1, scrollable); A3 held-out panel and leakage-corrected masking;
A4 framework v2.0 (sensitivity); A5 spec-v2 cohort fixes (sensitivity).

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
S31D = A / "claude-s31-20261014"  # s31 run (queue 2026-10-14)
SCR = A / "claude-deck2-20261014" / "deck"  # claims table and validation inputs (deck2 run; the s31 run's copy stays in S31D / "deck")
FIG2 = ROOT / "docs/paper/figures_latent/figure2_covariate_balance.png"  # scripts/figures/make_figure2_latent.py
FIG2V = S31D / "figure2_values.json"  # its aggregate values (validated there)
S31SUM = {"v1": S31D / "summary_v1", "mi": S31D / "summary_mi"}  # scripts/s31/s31_summaries.py (sets S31, S32; S32 gated)
S31DOC = ROOT / "docs/s31/S31_RESULTS.md"  # scripts/s31/s31_numbers.py
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
MAIN = ["s-title", "s-bg", "s-prob", "s-aims", "s-over", "s-pipe", "s-meth1", "s-meth2", "s-res2", "s-bal", "s-emu", "s-rob", "s-agq",
        "s-plas", "s-mimic", "s-take", "s-dec"]  # 2026-10-14 (deck2): Figure 2 (s-res2) before the balance explorer (s-bal)
# appendix (deck2, 2026-10-14): the former A1 (trial selection) and A6 (design history) are removed; Table 1 is one scrollable
# slide; the held-out panel, leakage map and masking moved from slide 8 to a new appendix slide; labels renumbered A1-A5
APP = [("a-qual", "A1", "Emulation-quality criteria", "s-pipe"), ("a-t1", "A2", "All 38 trials (Table 1)", "s-pipe"),
       ("a-panel", "A3", "Held-out panel and leakage map", "s-meth2"), ("a-fw", "A4", "Framework v2.0 (sensitivity)", "s-res2"),
       ("a-fix", "A5", "Spec-v2 cohort fixes (sensitivity)", "s-rob")]
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
    # s31 primary (2026-10-14): build_balance_explorer.trials_meta adds s31 / f37 / status (PROTECT AF excluded at feasibility)
    BM = {t["id"]: t for t in BE.trials_meta(g)}
    for t in out:
        t.update(s31=BM[t["id"]]["s31"], f37=BM[t["id"]]["f37"], status=BM[t["id"]]["status"])
    assert sum(t["s31"] for t in out) == 31 and sum(t["f37"] for t in out) == 37
    assert [t["full"] for t in out if not t["f37"]] == ["PROTECT AF"]
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
        return r.iloc[0], (S31SUM["mi"] if st == "S31" else MI_V1SUM) / "contrasts.csv"
    return V2.vrow(CTX["VC"], "v1", st, rg, a, b, cfg), (S31SUM["v1"] if st == "S31" else V2SUM) / "contrasts.csv"


def mis_row(st, rg, a, b="base", cfg="main"):
    """v1 MI summary (also holds the version 1 P1/P5/PS10/hdPS rows, incl. the rescored-30 'Snew' set)."""
    M = CTX["MIS"]
    r = M[(M.set == st) & (M.config == cfg) & (M.rung_a == rg) & (M.rung_b == rg) & (M.arm_a == a) & (M.arm_b == b) & M.kind.isin(["within", "ladder"])]
    assert len(r) == 1, (st, rg, a, b, cfg, len(r))
    return r.iloc[0]


SETS1 = {"s31": "S31", "s32": "S32", "all": "S38", "v2": "S29", "v2c": "Snew"}
SUMSETS = ("S31", "S32", "S38", "S29")  # sets with a version 1 Python summary row (S31: scripts/s31/s31_summaries.py)


def stat_v1(sid, what, ts, rg, a, b="base", cfg="main", panel="54"):
    """a version 1 contrast: shown from the Python summary where one exists (checked against BE.pair_stats on the cells), otherwise
    computed from the cells (checked against the deck's embedded integers). Returns (pair_stats dict, summary row or None)."""
    G1, E1 = CTX["G1"], CTX["E1"]
    r = ps(G1, cfg, rg, a, b, ts, panel)
    st = SETS1.get(ts)
    row, src = None, None
    if st in SUMSETS:
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
    if coh == "v1" and st in SUMSETS:
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
    ("≥ 350 with an ECG in the smaller arm\nand ≥ 50 events", "Size: ≥350 with an ECG in the smaller arm; ≥50 pooled events",
     "PROTECT AF (LAA closure) excluded: smaller arm < 350. PARAGON-HF, DAPA-HF/EMPEROR-Reduced and PARTNER were built in "
     "development but had fewer than 400 PS-Clinical pairs (development data-sufficiency rule) and are not among the emulated trials"),
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


SIZE_NOTE = ("Size threshold raised from 300 to 350 after near-separation was observed in the smallest trial (PROTECT AF); "
             "the 32-trial results are reported as a sensitivity analysis.")


def feas_rows():
    return "".join(f"<tr><td><b>{k}.</b> {esc(c)}</td><td>{esc(e)}</td></tr>" for k, (_, c, e) in enumerate(FEAS, 1))


def counts():
    """flow, tier and area counts of the s31 design, from the deck's trial records (claims checked against quality_tiers.json)."""
    tr = CTX["trials"]
    feas = [t for t in tr if t["f37"]]
    return dict(nf=len(feas), na=sum(t["s31"] for t in tr), tc={q: sum(t["tier"] == q for t in feas) for q in TIERS},
                ac={a: sum(t["area"] == a and t["s31"] for t in tr) for a in AREAS})


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


def aims_graphic():
    """slide 4, the click after aim 1 (deck2 2026-10-14): the two representations, (a) raw ECG waveform -> AI-ECG encoder -> embedding
    vector and (b) coded patient timeline -> CLMBR-T (EHR foundation model, coded history) -> embedding vector, both feeding propensity
    score matching. Shown for one step only (class "only"); aim 1 stays highlighted (data-of="1")."""
    MU, GR = "#5b5d86", "#8a8d99"
    s = ['<svg viewBox="0 0 1192 400" style="width:100%;height:auto" aria-label="The two representations used in propensity score matching">']

    def arr(x1, y1, x2, y2, col=NAVY):
        a = math.atan2(y2 - y1, x2 - x1)
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2 - 4 * math.cos(a):.1f}" y2="{y2 - 4 * math.sin(a):.1f}" stroke="{col}" stroke-width="3"/>'
                f'<path d="M{x2} {y2}L{x2 - 14 * math.cos(a - .42):.1f} {y2 - 14 * math.sin(a - .42):.1f}L{x2 - 14 * math.cos(a + .42):.1f} {y2 - 14 * math.sin(a + .42):.1f}Z" fill="{col}"/>')

    def txt(x, y, t, fs=17, w=400, col=NAVY, anc="middle", it=False):
        return (f'<text x="{x}" y="{y}" font-size="{fs}" font-weight="{w}" fill="{col}" text-anchor="{anc}"'
                + (' font-style="italic"' if it else "") + f'>{esc(t)}</text>')

    def beat(x0, yb, w, amp, inv):
        """one P-QRS-T complex across width w, baseline yb."""
        sg = -1 if inv else 1
        pts = [(0, 0), (.12, 0), (.17, -.12), (.22, 0), (.3, 0), (.33, .18), (.37, -1), (.41, .35), (.45, 0), (.58, 0), (.66, -.28), (.74, 0), (1, 0)]
        return " ".join(f"{x0 + px * w:.1f},{yb + sg * py * amp:.1f}" for px, py in pts)

    def vec(x, y, k=8, cw=26, ch=14):
        sh = [.95, .35, .7, .15, .55, .85, .25, .6][:k]
        return "".join(f'<rect x="{x}" y="{y + i * ch}" width="{cw}" height="{ch}" fill="{RED}" fill-opacity="{o}" stroke="{NAVY}" stroke-width="1.4"/>'
                       for i, o in enumerate(sh))

    def enc(x, yc, label, sub=None):
        o = f'<path d="M{x} {yc - 66} L{x + 210} {yc - 34} L{x + 210} {yc + 34} L{x} {yc + 66} Z" fill="#f3f3f7" stroke="{NAVY}" stroke-width="2.4" stroke-linejoin="round"/>'
        if not sub:
            return o + txt(x + 96, yc + 7, label, fs=20, w=700)
        return (o + txt(x + 96, yc - 12, label, fs=20, w=700) + "".join(txt(x + 96, yc + 14 + 19 * i, l, fs=14, col=MU) for i, l in enumerate(sub)))

    for yc, head in ((100, "ECG embedding"), (300, "EHR embedding")):
        s.append(txt(0, yc - 76, head, fs=17, w=700, col=RED, anc="start"))
    # (a) raw 12-lead ECG waveform: 3 rows x 4 columns of leads on ECG paper
    x0, y0, W, H = 0, 40, 320, 120
    s.append(f'<rect x="{x0}" y="{y0}" width="{W}" height="{H}" fill="#fdf3f2" stroke="{NAVY}" stroke-width="2" rx="4"/>')
    for gx in range(x0 + 16, x0 + W, 16):
        s.append(f'<line x1="{gx}" y1="{y0}" x2="{gx}" y2="{y0 + H}" stroke="#f3c9c6" stroke-width="0.8"/>')
    for gy in range(y0 + 15, y0 + H, 15):
        s.append(f'<line x1="{x0}" y1="{gy}" x2="{x0 + W}" y2="{gy}" stroke="#f3c9c6" stroke-width="0.8"/>')
    inv = {3, 7}  # aVR-like and V1-like leads drawn inverted
    amps = [11, 13, 7, 9, 8, 10, 9, 11, 13, 13, 12, 10]
    for li in range(12):
        r, c = li % 3, li // 3
        cx, yb = x0 + 6 + c * 78, y0 + 26 + r * 36
        s.append(f'<polyline points="{beat(cx, yb, 36, amps[li], li in inv)} {beat(cx + 36, yb, 36, amps[li], li in inv)}" fill="none" stroke="{NAVY}" stroke-width="1.6" stroke-linejoin="round"/>')
    s.append(txt(x0 + W / 2, y0 + H + 26, "raw ECG waveform (12-lead)", fs=16, col=MU))
    # (b) coded patient timeline: diagnoses, drugs and procedures as events over time, up to the index date
    x0, y0 = 0, 240
    s.append(f'<rect x="{x0}" y="{y0}" width="{W}" height="{H}" fill="#fff" stroke="{NAVY}" stroke-width="2" rx="4"/>')
    lanes = [("diagnoses", NAVY, [(118, 0), (160, 0), (205, 0), (238, 0), (282, 0)]), ("drugs", RED, [(140, 1), (175, 1), (228, 1), (262, 1), (295, 1)]),
             ("procedures", MU, [(150, 2), (250, 2), (288, 2)])]
    for k, (nm, col, ev) in enumerate(lanes):
        yy = y0 + 26 + k * 30
        s.append(txt(x0 + 12, yy + 5, nm, fs=14, col=col, anc="start", w=600))
        s.append(f'<line x1="{x0 + 108}" y1="{yy}" x2="{x0 + 306}" y2="{yy}" stroke="#dcdde5" stroke-width="1.4"/>')
        for ex, _ in ev:
            if k == 0:
                s.append(f'<circle cx="{ex}" cy="{yy}" r="6" fill="{col}"/>')
            elif k == 1:
                s.append(f'<rect x="{ex - 6}" y="{yy - 6}" width="12" height="12" fill="{col}"/>')
            else:
                s.append(f'<path d="M{ex} {yy - 7} L{ex + 7} {yy + 6} L{ex - 7} {yy + 6} Z" fill="{col}"/>')
    s.append(arr(x0 + 108, y0 + 106, x0 + 306, y0 + 106, col=GR) + txt(x0 + 200, y0 + 100, "time", fs=12.5, col=GR, it=True))
    s.append(f'<line x1="{x0 + 306}" y1="{y0 + 12}" x2="{x0 + 306}" y2="{y0 + 108}" stroke="{RED}" stroke-width="2" stroke-dasharray="4 3"/>')
    s.append(txt(x0 + W / 2, y0 + H + 26, "coded patient timeline", fs=16, col=MU))
    # encoders, embedding vectors, propensity score matching
    for yc, lab, sub in ((100, "AI-ECG encoder", None), (300, "CLMBR-T", ["EHR foundation model", "(coded history)"])):
        s.append(arr(330, yc, 382, yc) + enc(390, yc, lab, sub) + arr(606, yc, 650, yc) + vec(660, yc - 56))
        s.append(txt(673, yc + 78, "embedding vector", fs=16, col=MU))
    s.append(f'<rect x="850" y="140" width="320" height="120" rx="8" fill="{NAVY}"/>' + txt(1010, 192, "Propensity score", fs=24, w=700, col="#fff")
             + txt(1010, 224, "matching", fs=24, w=700, col="#fff"))
    s.append(arr(696, 100, 846, 178) + arr(696, 300, 846, 222))
    s.append("</svg>")
    return f'<div class="aimfig only" data-step="2" data-of="1">{"".join(s)}</div>'


def s_aims():
    sid = "s-aims"
    claim(SN[sid], "MIMIC-IV external validation done", "done", ROOT / "docs/v21/MIMIC_PAPER2.md", probe="7 cardiovascular trials", ref_src=ROOT / "docs/v21/MIMIC_PAPER2.md")
    chip = lambda grp, what, done: (f'<div class="chip{" done" if done else ""}"><span class="cg">{grp}</span> {what} '
                                    f'<span class="st">{"✓ done" if done else "planned"}</span></div>')
    aims = [
        (1, ICON["ecg"] + ICON["ehr"], "Integrate ECG and EHR foundation models into matching",
         "ECG encoder (BCL) · EHR foundation model (CLMBR-T) · easy to operationalize"),
        (2, ICON["bal"], "Covariate balance", "on held-out measurements"),
        (3, ICON["rct"], "Trial emulation and agreement with RCTs", f"{sum(t['s31'] for t in CTX['trials'])} benchmark RCTs"),
        (4, ICON["glob"], "External validation",
         '<span class="chips">' + chip("EHR", "MIMIC-IV", True) + chip("Biobank", "UK Biobank", False)
         + chip("Trial cohorts", "dbGaP: ACCORD, WHI, CHS", False) + "</span>"),
    ]
    st = {1: 1, 2: 3, 3: 4, 4: 5}  # click 2 = the representations graphic under aim 1 (aims_graphic); click 3 hides it and reveals aim 2
    rows = "".join(f'<div class="aim fstep" data-step="{st[k]}"><div class="ic">{ic}</div><div class="num">{k}</div>'
                   f'<div><div class="at">{esc(t)}</div><div class="as">{s if k == 4 else esc(s)}</div></div></div>' for k, ic, t, s in aims)
    body = f"""<p class="goal">The goal of <b>LATENT-RCT</b> is to bring unstructured information into trial emulation.</p>
<div class="aims4">{rows}</div>{aims_graphic()}"""
    return sec(sid, "Aims", body, steps=6, cls="aimsl")


def s_overview():
    """slide 5: kept (number, title bar, footer) with an empty body for the user's own content (user feedback 2026-10-13)."""
    return sec("s-over", "Study overview", "")


def s_pipe():
    sid = "s-pipe"
    tr = CTX["trials"]
    QJ = json.load(open(QT19))
    C_ = counts()
    nf, na, tc, ac = C_["nf"], C_["na"], C_["tc"], C_["ac"]
    QF = [x for x in QJ["trials"] if x["key"] != "protect_af"]  # independent count: quality_tiers.json minus the feasibility exclusion
    for t in TIERS:
        claim(SN[sid], f"v19 tier count {t} (of the {nf} feasible)", str(tc[t]), QT19, ref=str(sum(x["tier"].startswith(t) for x in QF)),
              ref_how="quality_tiers.json trials minus PROTECT AF")
    claim(SN[sid], "tier counts 3/11/17/6", " / ".join(str(tc[t]) for t in TIERS), QT19, probe="v19 tiers " + " / ".join(str(tc[t]) for t in TIERS), ref_src=PIPE)
    claim(SN[sid], "99 candidates -> 37 -> 31", f"99 → {nf} feasible → {na} analysed", PIPE, probe=f"99 → {nf} feasible → {na} analysed", ref_src=PIPE)
    claim(SN[sid], f"areas of the {na}", ", ".join(f"{a} {ac[a]}" for a in AREAS), QT19,
          ref=", ".join(f"{a} {sum(x['area'] == a and not x['tier'].startswith('Limited') for x in QF)}" for a in AREAS), ref_how="quality_tiers.json trials minus PROTECT AF")
    claim(SN[sid], "size threshold", ">=350 with an ECG in the smaller arm", PIPE, probe="≥300 to ≥350 patients with an ECG in the smaller arm", ref_src=PIPE)
    claim(SN[sid], "events threshold", ">=50 events", SUPP, probe="at least 50 pooled primary events", ref_src=SUPP)
    claim(SN[sid], "PROTECT AF removed by the size rule", "PROTECT AF", PIPE, probe="This removes only **PROTECT AF**", ref_src=PIPE)
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
    # the flow populates one step after another: 99 -> feasibility -> 37 -> emulation quality -> 31 analysed -> clinical areas
    s.append(box(0, yc - 50, 128, 100, ["99", "candidate", "RCTs"], fs=18))
    s.append('<g class="build" data-step="1">' + arr(130, yc, 160, yc))
    s.append(f'<g class="ptrig" data-pop="pop-feas" aria-label="Feasibility criteria: details"><rect x="162" y="{yc - 108}" width="408" height="216" fill="#f5f5f8" stroke="{NAVY}" stroke-width="2" rx="6"/>')
    s.append(f'<text x="176" y="{yc - 78}" font-size="18" font-weight="700" fill="{NAVY}">Feasibility criteria</text>')
    yy = yc - 48  # one row per criterion; a criterion label with a line break continues on an indented second row
    for i, (lab, _, _) in enumerate(FEAS):
        l1, *rest = lab.split("\n")
        s.append(f'<text x="176" y="{yy}" font-size="14.5" fill="{NAVY}"><tspan font-weight="700">{i + 1}.</tspan> {esc(l1)}</text>')
        for l2 in rest:
            yy += 21
            s.append(f'<text x="194" y="{yy}" font-size="14.5" fill="{NAVY}">{esc(l2)}</text>')
        yy += 26
    s.append(hint(176, yc + 98) + "</g></g>")
    s.append('<g class="build" data-step="2">' + arr(572, yc, 602, yc) + box(604, yc - 50, 112, 100, [str(nf), "feasible", "trials"], fs=18) + "</g>")
    qual = ["basic, rule-based points:", "• design flags F1–F5: 1 point each", "• comparator, outcome fidelity: 0 / 1 / 2",
            "Excellent 0 · Good 1–2 · Moderate 3", "Limited (≥4 points) excluded"]
    s.append('<g class="build" data-step="3">' + arr(718, yc, 748, yc))
    s.append(f'<g class="ptrig" data-pop="pop-qual" aria-label="Emulation-quality criteria: details"><rect x="750" y="{yc - 108}" width="324" height="216" fill="#f5f5f8" stroke="{NAVY}" stroke-width="2" rx="6"/>')
    s.append(f'<text x="764" y="{yc - 78}" font-size="18" font-weight="700" fill="{NAVY}">Emulation-quality criteria</text>')
    for i, l in enumerate(qual):
        s.append(f'<text x="764" y="{yc - 47 + i * 29}" font-size="15" fill="{RED if i == 4 else NAVY}">{esc(l)}</text>')
    s.append(hint(764, yc + 98).replace("the full criteria", "the rule") + "</g></g>")
    s.append('<g class="build" data-step="4">' + arr(1076, yc, 1100, yc) + box(1102, yc - 50, 90, 100, [str(na), "analysed"], fs=18, fill=NAVY, col="#fff") + "</g>")
    # bottom right (with the 31): emulation quality of the 37 feasible; bottom left (last step): the 31 by clinical area
    y0 = 290
    s.append(f'<g class="build" data-step="5"><text x="0" y="{y0}" font-size="17" font-weight="700" fill="{NAVY}">The {na} analysed trials by clinical area</text>')
    lab = {"AF": "Atrial fibrillation", "HF": "Heart failure", "Diabetes": "Diabetes", "Hypertension": "Hypertension", "ACS / MI": "ACS / MI", "Other": "Other"}
    order = sorted(AREAS, key=lambda a: -ac[a])
    for i, a in enumerate(order):
        y = y0 + 16 + i * 27
        s.append(f'<text x="170" y="{y + 15}" font-size="15" text-anchor="end" fill="{NAVY}">{lab[a]}</text>'
                 f'<rect x="180" y="{y + 2}" width="{ac[a] * 30}" height="19" fill="{RED if a == "AF" else NAVY}"/>'
                 f'<text x="{186 + ac[a] * 30}" y="{y + 17}" font-size="15" font-weight="700" fill="{NAVY}">{ac[a]}</text>')
    s.append("</g>")
    x1 = 700
    s.append(f'<g class="build" data-step="4"><text x="{x1}" y="{y0}" font-size="17" font-weight="700" fill="{NAVY}">Emulation quality of the {nf} feasible trials</text>')
    cols = {"Excellent": NAVY, "Good": "#5b5d86", "Moderate": "#c9cbd8", "Limited": "#fbe3e2"}
    xx, wsc = x1, 490 / nf
    for t in TIERS:
        w = tc[t] * wsc
        s.append(f'<rect x="{xx:.1f}" y="{y0 + 18}" width="{w:.1f}" height="40" fill="{cols[t]}" stroke="#fff"/>'
                 f'<text x="{xx + w / 2:.1f}" y="{y0 + 44}" font-size="16" font-weight="700" text-anchor="middle" fill="{"#fff" if t in ("Excellent", "Good") else (NAVY if t == "Moderate" else "#a8322e")}">{tc[t]}</text>'
                 f'<text x="{xx + w / 2:.1f}" y="{y0 + 78}" font-size="14" text-anchor="middle" fill="{NAVY if t != "Limited" else "#a8322e"}">{t}</text>')
        xx += w
    s.append(f'<line x1="{x1}" x2="{x1 + na * wsc:.1f}" y1="{y0 + 92}" y2="{y0 + 92}" stroke="{NAVY}" stroke-width="2"/>'
             f'<text x="{x1 + na / 2 * wsc:.1f}" y="{y0 + 112}" font-size="15" text-anchor="middle" fill="{NAVY}">analysed ({na})</text>'
             f'<text x="{x1 + (na + nf) / 2 * wsc:.1f}" y="{y0 + 112}" font-size="15" text-anchor="middle" fill="#a8322e">excluded</text></g>')
    s.append("</svg>")
    # the former appendix A1 (trial selection) is removed (deck2 2026-10-14); the feasibility popup keeps what it needs: the numbered
    # criteria with examples, the size-rule note, designs and dates. Its claims (formerly registered on A1) are registered here.
    claim(SN[sid], "ACTIVE W vs RE-LY overlap", "69%", SUPP, probe="69% between ACTIVE W and RE-LY", ref_src=SUPP)
    claim(SN[sid], "ACCOMPLISH reuses 96% of ALLHAT", "96%", CAND17, probe="ACCOMPLISH reuses 96% of the ALLHAT records", ref_src=CAND17)
    claim(SN[sid], "development data-sufficiency threshold", "400 PS-Clinical pairs", SUPP, probe="fewer than 400 matched pairs with PS-Clinical", ref_src=SUPP)
    claim(SN[sid], "index dates 2011-2024", "2011–2024", PIPE, probe="index dates 2011–2024", ref_src=PIPE)
    claim(SN[sid], "index dates: v1 audit 2025 note", "COMET into 2025", CLRE, probe="2011–2025: COMET has", ref_src=CLRE)
    claim(SN[sid], "size threshold 300 -> 350 (post hoc, PROTECT AF)", "300 -> 350", PIPE, probe="the threshold was raised after the near-separation was observed", ref_src=PIPE)
    qa, ta, fw = SN["a-qual"], SN["a-t1"], SN["a-fw"]
    qrule = QRULE.replace(" (design information only, blind to results)", "")  # deck2: no "blind to results" wording on slide 6 or its popups
    assert qrule != QRULE and "blind" not in qrule
    pops = popup("pop-feas", f"Feasibility criteria (stage 1: 99 candidates → {nf} feasible)",
                 f'<table class="t tq mt"><tr><th style="width:36%">Criterion</th><th>Example</th></tr>{feas_rows()}</table>'
                 f'<p class="small red" style="margin-top:6px"><b>{esc(SIZE_NOTE)}</b></p>'
                 f'<p class="small" style="margin-top:6px"><b>Designs and dates.</b> {DESIGNS}</p>', links="More: " + applink(ta))
    pops += popup("pop-qual", f"Emulation-quality criteria (stage 2: v19 points rule; {nf} → {na})",
                  f'<p class="mp">{qrule}</p><h4 class="mh4">Examples</h4><p class="mp">{"<br>".join(q_examples())}</p>'
                  f'<p class="small" style="margin-top:8px">Tier counts of the {nf} feasible: Excellent {tc["Excellent"]}, Good {tc["Good"]}, Moderate {tc["Moderate"]}, '
                  f'Limited {tc["Limited"]} (excluded). PROTECT AF (Good) was excluded earlier, at feasibility. Framework v2.0 tiers are a sensitivity analysis ({fw}).</p>',
                  links="More: " + applink(qa) + " (interactive quality viewer) · " + applink(fw))
    return sec(sid, "LATENT-RCT pipeline", "".join(s), links=more(qa, ta) + pops)  # popups outside .body: they cover the slide


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
    # deck2 (2026-10-14): order PS-Demo -> PS-CVD5 -> PS-CVD10 -> PS-Clinical -> hdPS (as Figure 2C); no "no LVEF" in the labels
    L = [("PS-Demo", "age, sex, index year", ""), ("PS-CVD5", "+ hypertension, T2D, CAD, AF, HF", "primary"),
         ("PS-CVD10", "+ CKD, COPD/asthma, PAD, stroke/TIA, valve disease", ""),
         ("PS-Clinical", f"+ measured vitals and labs, medication orders, visits; no echo; {mi} " + pl("pop-clin", "inputs"), ""),
         ("hdPS", "PS-Demo + 9–13 diagnoses + <b>200 yes/no code flags</b> (no values, no dates) " + pl("pop-hdps", "what are the flags?"), "")]
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
<div class="pmstrip"><b>PS and matching:</b> Ridge (L2) logistic regression, C = 1 · 1:1 nearest neighbour, caliper 0.2 · {pl("pop-match", "details")}</div>"""
    pops = popup("pop-hdps", "hdPS: the 200 yes/no code flags", """<ul class="mul">
<li><b>Base:</b> PS-Demo + 9–13 investigator-selected diagnoses (prior 365 days).</li>
<li><b>Candidate flags:</b> pre-index diagnosis, medication and procedure codes with ≥2% prevalence, each turned into yes/no flags for <i>any</i>, <i>sporadic</i> (≥ median count among patients with the code) and <i>frequent</i> (≥ 75th percentile) occurrence; laboratory tests as <i>was measured</i> yes/no.</li>
<li><b>No values, no dates:</b> a flag records only whether (and how often) a code occurs before index.</li>
<li><b>How the 200 are chosen:</b> ranked by |log prevalence ratio| between the two treatment groups (offset 0.001); the top 200 enter the PS.</li>
<li><b>Treatment-only ranking:</b> the outcome is never used (unlike the original algorithm).</li>
<li><b>Random half held out:</b> candidates come from a random half of the code features; the other half is reserved for balance assessment.</li>
<li><b>Exposure drugs excluded</b> from the candidates.</li>
</ul><p class="small">Schneeweiss S, et al. <i>Epidemiology</i> 2009;20:512–522 (adapted; supplement eMethods).</p>""")
    pops += popup("pop-clin", "PS-Clinical: inputs", f"""<ul class="mul">
<li><b>Demographics and diagnoses:</b> age, sex, index year; AF, hypertension, diabetes, ischaemic heart disease/MI, CKD, COPD/asthma, PAD, stroke, valve disease; trial-specific diagnoses (e.g. heart failure, TIA, liver disease, prior bleeding). Prior 365 days.</li>
<li><b>Measured values</b> (latest in the prior 90 days; BMI 365 days): systolic and diastolic BP, heart rate, BMI, creatinine, potassium, sodium, haemoglobin.</li>
<li><b>Medication orders</b> (3–10 relevant to the clinical area, prior 90 days) and <b>utilisation</b> (outpatient, ED, inpatient encounters).</li>
<li>LVEF and echo are never PS inputs.</li>
<li><b>Missing values: {mi}</b> by chained equations (covariates and treatment as predictors, no outcome). Per-item |SMD| averaged across the draws; HRs combined by Rubin's rules.</li>
<li><b>Leakage-corrected masks:</b> the 8 measured vitals/labs that are PS inputs, and eGFR (derived from creatinine), are not scored as held-out items at this level.</li>
</ul>""")
    pops += popup("pop-match", "PS and matching", """<ul class="mul">
<li><b>PS model:</b> Ridge (L2) logistic regression on standardised covariates, <b>fixed C = 1</b> for every level and arm (no tuning; a cross-validated penalty is a sensitivity analysis).</li>
<li><b>Representations</b> enter the PS as principal components computed within each trial: ECG (BCL self-supervised encoder, 256-d → 32 PCs; latest 12-lead ECG in [index − 365 d, index], index day included, 37% of ECGs) and CLMBR-T (frozen CLMBR-T-base on the coded record: diagnoses, drugs, procedures, measurement codes without values, visits; last 4,096 tokens, index day excluded; 768-d → 64 PCs).</li>
<li><b>Placebo:</b> permuted ECG, the embeddings shuffled between patients within each trial (same dimension, no information).</li>
<li><b>Matching:</b> 1:1 greedy nearest neighbour on the PS logit, <b>caliper 0.2 SD of the logit</b>, without replacement.</li>
<li><b>Failed cell:</b> fewer than 11 matched pairs.</li>
<li><b>Sensitivities:</b> caliper 0.1, 1:3 matching, IPTW, overlap weights, gradient-boosted PS.</li>
</ul>""")
    return sec(sid, "PSM experiments", body, links=pops)  # the former A6 (design history) and its link are removed (deck2)


def s_methods_panel():
    """slide 8 (deck2 2026-10-14): "Methods: covariate balancing", the endpoints and the tests only; the held-out characteristics,
    the leakage map and the masking details are on appendix A3 (s_apanel), linked bottom left."""
    sid = "s-meth2"
    sl = SN[sid]
    claim(sl, "held-out items", "54", PIPE, probe="54 non-coded items, leakage-corrected", ref_src=PIPE)
    claim(sl, "bootstrap resamples", "4,000", PIPE, probe="95% CI from 4,000 bootstrap resamples of trials", ref_src=PIPE)
    claim(sl, "|SMD| threshold", "0.1", PIPE, probe="% of items with |SMD| < 0.1", ref_src=PIPE)
    claim(sl, "exact sign-flip across trials", "as stated", PIPE, probe="exact sign-flip permutation across trials", ref_src=PIPE)
    claim(sl, "placebo = permuted ECG", "as stated", PIPE, probe="Permuted ECG (embeddings shuffled between patients within each trial; same dimension)", ref_src=PIPE)
    body = """<div class="cbal">
<div class="card cb1"><h3 class="h3">Endpoints</h3><ul class="cbl">
  <li><b>Primary:</b> relative reduction in mean |SMD| over the <b>54 held-out items</b> (measurements not in the PS: vitals, labs, echo)<div class="eq">1 − mean |SMD|<sub>PS + representation</sub> / mean |SMD|<sub>PS alone</sub></div></li>
  <li><b>Secondary:</b> % of items with |SMD| &lt; 0.1</li>
</ul></div>
<div class="card cb1"><h3 class="h3">Tests</h3><ul class="cbl">
  <li><b>Paired by trial:</b> each trial with vs without the representation</li>
  <li><b>Bootstrap CI:</b> 4,000 resamples of trials</li>
  <li><b>Exact sign-flip</b> permutation across trials</li>
  <li><b>Placebo:</b> permuted ECG (shuffled between patients)</li>
</ul></div>
</div>"""
    return sec(sid, "Methods: covariate balancing", body, links=more(SN["a-panel"]))


def s_apanel():
    """appendix A3 (deck2 2026-10-14): slide 8's former held-out characteristics and leakage-corrected masking (V2.s_methods_panel
    without its endpoints column; the secondary agreement endpoint kept as a note), plus the + CLMBR-T row (pipeline.md §6)."""
    sid = "a-panel"
    n0 = len(V2.CL)
    h = V2.s_methods_panel()
    cl_slide(n0, sid)
    V2.CL[n0:] = [c for c in V2.CL[n0:] if c["claim"] != "bootstrap resamples"]  # the endpoints column stays on slide 8 (claimed there)
    h = one(h, "<tr><td>PS-Flags</td><td>none</td><td>held-out codes, prognostic score</td></tr>", "")  # PS-Flags: supplement only
    h = one(h, "<tr><td>+ ECG, + permuted ECG</td><td>none</td><td>none</td></tr>",
            "<tr><td>+ CLMBR-T (any level)</td><td>none</td><td>all 4 coded items</td></tr><tr><td>+ ECG, + permuted ECG</td><td>none</td><td>none</td></tr>")
    claim(SN[sid], "+ CLMBR-T masks", "none on the 54; all 4 coded items on the 58", PIPE, probe="| + CLMBR-T (any level) | none | all 4 coded items |", ref_src=PIPE)
    ep = between(h, '  <div><h3 class="h3">Endpoints and tests</h3>', "</ul></div>\n", incl_b=True)
    agr = between(ep, "<li><b>Agreement (secondary):</b>", "</li>")[len("<li>"):]
    h = one(h, ep, "")
    h = one(h, "grid-template-columns:0.9fr 1.15fr 0.95fr;gap:22px", "grid-template-columns:0.85fr 1.15fr;gap:30px")
    h = one(h, "Items that are PS inputs are always masked.</p>",
            "Items that are PS inputs are always masked. Items are used only where they are observed in both compared cells.</p>"
            f'\n    <p class="small" style="margin-top:10px">{agr}.</p>')
    return retitle(h, sid, "Held-out panel and leakage-corrected masking")


def s_results2():
    """the balance results slide ("Results 2"; the user's "slide 13": love plot, domains, ladder): just the updated Figure 2
    (scripts/figures/make_figure2_latent.py), a minimal title and a one-line source note. Every number in the figure is registered
    as a claim and recomputed here from the version 1 cells with build_balance_explorer.pair_stats."""
    sid = "s-res2"
    sl = SN[sid]
    assert FIG2.exists() and FIG2V.exists(), "run scripts/figures/make_figure2_latent.py first"
    fig = fig2_panels()
    V = json.load(open(FIG2V))
    assert V["k_set"] == 31
    T = T_("s31")
    G1 = CTX["G1"]
    for rg, lab in (("P1", "PS-Demo"), ("P5", "PS-CVD5"), ("PS10", "PS-CVD10"), ("hdPS200", "hdPS"), ("clinical_nolvef", "PS-Clinical (no LVEF, MI)")):
        c = V["C"][rg]
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            r = ps(G1, "main", rg, a, "base", "s31")
            claim(sl, f"Fig 2C {lab} + {a} relative change", f"{c['rr_' + a][0]:.1f}%", FIG2V, ref=f"{r['rr']:.1f}%",
                  ref_how="recomputed from the version 1 cells (build_balance_explorer.pair_stats)")
        for a in ("unmatched", "base", "ECG", "CLMBR", "ECG+CLMBR"):
            M = G1.block("main", rg, a, True)[np.ix_(T, BE.items("54"))]
            ok = np.isfinite(M).any(1)
            claim(sl, f"Fig 2C {lab} {a} mean |SMD|", f"{c[a]:.3f}", FIG2V, ref=f"{np.nanmean(M[ok], 1).mean():.3f}", ref_how="explorer ladder level on the cells")
    d = V["D"]
    r = ps(G1, "main", "P5", "ECG", "base", "s31")
    claim(sl, "Fig 2D trials improved", f"{int(d['improved'])} of {int(d['k'])}", FIG2V, ref=f"{r['better']} of {r['k']}", ref_how="pair_stats on the cells")
    claim(sl, "Fig 2D mean change (points)", f"{d['mean']:+.1f}", FIG2V, ref=f"{r['dpts']:+.1f}", ref_how="pair_stats on the cells")
    claim(sl, "Fig 2D P", fp(d["p"]), FIG2V, ref=fp(r["p"]), ref_how="exact one-sided sign-flip on the cells")
    for g, x in V["B"].items():
        js = BE.items("54") if g == "All 54" else V2.dom_items(g)
        for a in ("unmatched", "base", "ECG"):
            M = G1.block("main", "P5", a, True)[np.ix_(T, js)]
            ok = np.isfinite(M).any(1)
            claim(sl, f"Fig 2B {g} {a}", f"{x[a]:.3f}", FIG2V, ref=f"{np.nanmean(M[ok], 1).mean():.3f}", ref_how="explorer domain view (mean) on the cells")
    # deck2: no subtitle / source line; minimal title; panels revealed A + B, then C, then D
    return sec(sid, "Results 1: covariate balance (Figure 2)", fig, links=more(SN["a-fw"], SN["a-fix"]))


FIG2P = FIG2.parent / "panels"  # per-panel PNGs (same figure, same 300 dpi; legend hidden)
FIG2_STEP = {"A": 1, "B": 1, "C": 2, "D": 3}


def fig2_panels(disp_h=560):
    """Figure 2 rebuilt from its per-panel PNGs, laid out as in the full figure: each panel is located in the full PNG (coarse search
    on 1/8-scale images, then a +-12 px refinement at full resolution; the match is asserted), white made transparent so padded
    panel edges never hide a neighbour, and embedded at 2x the displayed size. The shared legend is cropped from the full figure's
    top band (above the panels) and shown from step 0."""
    from PIL import Image
    full = Image.open(FIG2).convert("RGB")
    W, H = full.size
    F = 255 - np.asarray(full.convert("L"), float)
    K = 8
    Fs = 255 - np.asarray(full.convert("L").resize((W // K, H // K), Image.BOX), float)

    def msd(A_, B_, y, x):
        h, w = B_.shape
        y0, x0, y1, x1 = max(0, y), max(0, x), min(A_.shape[0], y + h), min(A_.shape[1], x + w)
        if y1 - y0 < h * .85 or x1 - x0 < w * .85:
            return np.inf
        return ((A_[y0:y1, x0:x1] - B_[y0 - y:y1 - y, x0 - x:x1 - x]) ** 2).mean()

    sc = 2 * disp_h / H

    def uri(im):
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode(), len(b.getvalue())

    def transp(im):
        """colour-to-alpha against white: composited on white the image is unchanged, and white padding is fully transparent."""
        a = np.asarray(im.convert("RGB")).astype(float) / 255
        al = (1 - a).max(2)
        col = np.where(al[..., None] > 0, (a - (1 - al[..., None])) / np.maximum(al[..., None], 1e-9), 0)
        return Image.fromarray(np.dstack([np.clip(col * 255 + .5, 0, 255), al * 255 + .5]).astype(np.uint8), "RGBA")

    pos, out, meta = {}, [], {}
    for L in "ABCD":
        pim = Image.open(FIG2P / f"figure2_covariate_balance_{L}.png").convert("RGB")
        P = 255 - np.asarray(pim.convert("L"), float)
        Ps = 255 - np.asarray(pim.convert("L").resize((pim.width // K, pim.height // K), Image.BOX), float)
        _, ys, xs = min((msd(Fs, Ps, y, x), y, x) for y in range(-6, Fs.shape[0]) for x in range(-6, Fs.shape[1]))
        m, y, x = min((msd(F, P, y, x), y, x) for y in range(ys * K - 12, ys * K + 13) for x in range(xs * K - 12, xs * K + 13))
        assert m < 400, (L, m)  # sub-pixel edge differences only (A 7.6, B 28.6, C 127, D 195 on 2026-10-14)
        pos[L] = (x, y, pim.width, pim.height)
        u, nb = uri(transp(pim).resize((round(pim.width * sc), round(pim.height * sc)), Image.LANCZOS))
        meta[L] = dict(xy=[x, y], size=[pim.width, pim.height], msd=round(float(m), 2), bytes=nb)
        out.append(f'<img class="f2p build" data-step="{FIG2_STEP[L]}" alt="Figure 2 panel {L}" src="{u}" '
                   f'style="left:{100 * x / W:.3f}%;top:{100 * y / H:.3f}%;width:{100 * pim.width / W:.3f}%">')
    assert pos["A"][0] < pos["B"][0] < pos["C"][0] and pos["D"][1] > pos["C"][1] and pos["B"][1] < pos["D"][1]
    # legend: the non-white bounding box of the band above the panels
    top = min(p[1] for p in pos.values())
    band = np.asarray(full.convert("L"))[:top - 2]
    ys_, xs_ = np.where(band < 200)
    lb = (max(0, xs_.min() - 6), max(0, ys_.min() - 4), min(W, xs_.max() + 7), min(top - 2, ys_.max() + 5))
    lg = transp(full.crop(lb))
    u, nb = uri(lg.resize((round(lg.width * sc), round(lg.height * sc)), Image.LANCZOS))
    meta["legend"] = dict(box=[int(v) for v in lb], bytes=nb)
    out.insert(0, f'<img class="f2p" alt="Figure 2 legend" src="{u}" style="left:{100 * lb[0] / W:.3f}%;top:{100 * lb[1] / H:.3f}%;width:{100 * (lb[2] - lb[0]) / W:.3f}%">')
    CTX["fig2"] = dict(src_size=[W, H], disp_h=disp_h, panels=meta)
    return f'<div class="fig2box" style="width:{disp_h * W / H:.0f}px;height:{disp_h}px">{"".join(out)}</div>'


def s_robust():
    sid = "s-rob"
    rows = []
    p31, _ = stat_v1(sid, "PS-CVD5 + ECG (31, primary)", "s31", "P5", "ECG")
    p32, _ = stat_v1(sid, "PS-CVD5 + ECG (32, with PROTECT AF)", "s32", "P5", "ECG")
    rows.append(("Paper 1's 32 (with PROTECT AF; sensitivity)", f"{ci(p32['rr'], p32['lo'], p32['hi'])}, {p32['lower']} trials lower, {pv(p32['p'])}; "
                 f"primary 31: {ci(p31['rr'], p31['lo'], p31['hi'])}, {p31['lower']}", "32"))
    s, _ = stat_v1(sid, "permuted ECG vs PS alone (31)", "s31", "P5", "shufECG")
    e, erow = stat_v1(sid, "ECG vs permuted (31)", "s31", "P5", "ECG", "shufECG")
    rng = [stat_v1(sid, f"ECG vs permuted ({ts})", ts, "P5", "ECG", "shufECG")[0]["rr"] for ts in ("q37:Excellent,Good", "f37", "v2", "v2c")] + [e["rr"]]
    rtxt = f"{fx(min(rng))} to {fx(max(rng))}%"
    rows.append(("Placebo (permuted ECG)", f"Permuted vs PS alone: {ci(s['rr'], s['lo'], s['hi'])}, {pv(s['p'])} (two-sided). ECG vs permuted: {ci(e['rr'], e['lo'], e['hi'])}; {rtxt} across five trial sets (31; Excellent + Good; all 37 feasible; v2.0 29 / 30)", "31"))
    cf, cfv = [], []
    for c, lab in (("main", "1:1, cal. 0.2"), ("cal01", "cal. 0.1"), ("m13", "1:3"), ("iptw", "IPTW"), ("overlap", "overlap"), ("gbm", "GBM PS")):
        x, _ = stat_v1(sid, f"PS method {c} (31)", "s31", "P5", "ECG", cfg=c)
        cf.append(f"{lab} {fx(x['rr'])}% ({fx(x['lo'])} to {fx(x['hi'])})")
        cfv.append(x)
    nex = sum(x["lo"] > 0 for x in cfv)
    neg = [lab for (c, lab), x in zip((("main", "1:1"), ("cal01", "cal. 0.1"), ("m13", "1:3"), ("iptw", "IPTW"), ("overlap", "overlap"), ("gbm", "GBM PS")), cfv) if x["rr"] <= 0]
    rows.append(("Six PS methods", "; ".join(cf) + f". {nex} of 6 CIs exclude 0" + (f"; the gradient-boosted PS shows no gain" if "GBM PS" in neg else ""), "31"))
    r5 = vc1("S31", "P5", "ECG")[0]
    r5m = mis_row("S31", "P5", "ECG") if CTX["mi"] else None
    clu = claim(SN[sid], "comparator-cluster sign-flip P (31)", fp(r5.m54_cluster_p), S31SUM["v1"] / "contrasts.csv", ref=None if r5m is None else fp(r5m.m54_cluster_p),
                ref_how="s31 MI summary (independent run of the endpoint code; P5 row)")
    loo = claim(SN[sid], "leave-one-trial-out max P (31)", fp(r5.m54_loo_max_p), S31SUM["v1"] / "contrasts.csv", ref=None if r5m is None else fp(r5m.m54_loo_max_p),
                ref_how="s31 MI summary (P5 row)")
    rows.append(("Comparator clusters; leave-one-trial-out", f"Cluster sign-flip {pv(r5.m54_cluster_p)} ({int(r5.m54_n_clusters)} comparator clusters); largest leave-one-out {pv(r5.m54_loo_max_p)}", "31"))
    if CTX["mi"]:
        mi, _ = stat_v1(sid, "PS-Clinical (no LVEF, MI) + ECG (31)", "s31", "clinical_nolvef", "ECG")
        M = CTX["MIS"]
        dr = [M[(M.set == "S31") & (M.config == "main") & (M.rung_a == f"clinical_nolvef#{k}") & (M.arm_a == "ECG") & (M.arm_b == "base")].iloc[0].relred54 for k in range(1, 6)]
        drt = claim(SN[sid], "MI draw range (31)", f"{fx(min(dr))} to {fx(max(dr))}%", S31SUM["mi"] / "contrasts.csv",
                    probe=f"single draws {fx(min(dr)).replace(V2.MINUS, '-')} to {fx(max(dr))}%", ref_src=S31DOC)
        rows.append(("Multiple imputation (PS-Clinical, no LVEF)", f"5-draw MI: {ci(mi['rr'], mi['lo'], mi['hi'])}, {pv(mi['p'])}; single draws {drt}. Single-draw estimates should not be reported", "31"))
    else:
        rows.append(("Multiple imputation (PS-Clinical, no LVEF)", "MI pending on the version 1 cohorts (single imputation shown)", "31"))
    RR = pd.read_csv(S31SUM["v1"] / "random_removal_summary.csv").set_index(["set", "arm"]).loc[("S31", "ECG")]
    r2 = BE.pair_stats(BE.Grid(CTX["g2"]["G"], CTX["g2"]["U"], CTX["g2"]["ex"]), "main", "P5", "ECG", "base", T_("s31"), "54", True)
    fv2 = claim(SN[sid], "spec-v2 fixed cohorts (31)", f"{fx(RR.relred54_v2)}%", S31SUM["v1"] / "random_removal_summary.csv", ref=f"{fx(r2['rr'])}%",
                ref_how="recomputed from the spec-v2 cells (build_balance_explorer.pair_stats, set s31)")
    rnd = claim(SN[sid], "random removal (31)", f"{fx(RR.relred54_random_median)} ({fx(RR.relred54_random_p5)} to {fx(RR.relred54_random_p95)})", S31SUM["v1"] / "random_removal_summary.csv",
                probe=f"random removal median {fx(RR.relred54_random_median)} ({fx(RR.relred54_random_p5)} to {fx(RR.relred54_random_p95)})", ref_src=S31DOC)
    rows.append((f"Spec-v2 cohort fixes (sensitivity; {SN['a-fix']})", f"{fx(RR.relred54_v1)}% → {fv2} with the fixes; removing the same numbers of patients at random: median {rnd}%, so the drop reflects smaller cohorts", "31"))
    v29, _ = stat_v1(sid, "framework v2.0 provisional 29 (v1 cohorts)", "v2", "P5", "ECG")
    v30, _ = stat_v1(sid, "framework v2.0 rescored 30 (v1 cohorts)", "v2c", "P5", "ECG")
    rows.append((f"Framework v2.0 trial sets (sensitivity; {SN['a-fw']})", f"Provisional 29: {ci(v29['rr'], v29['lo'], v29['hi'])}; rescored 30: {ci(v30['rr'], v30['lo'], v30['hi'])} (version 1 cohorts; defined before the size-rule change, both include PROTECT AF)", "29 / 30"))
    NB = json.load(open(S31D / "s31_numbers.json"))["S31"]
    cvr, nir = NB["cv_penalty_r2"], NB["no_index_day_ecg"]
    cvt = claim(SN[sid], "CV-tuned penalty (31)", ci(cvr["rr"], cvr["lo"], cvr["hi"]), S31D / "s31_numbers.json",
                probe=f"| CV log-loss penalty (R2 cells, scenario S1) | {norm(ci(cvr['rr'], cvr['lo'], cvr['hi']))}", ref_src=S31DOC)
    nit = claim(SN[sid], "no index-day ECG (31)", ci(nir["rr"], nir["lo"], nir["hi"]), S31D / "s31_numbers.json",
                probe=f"| Index-day ECGs excluded (ECG ≥ 1 day before index) | {norm(ci(nir['rr'], nir['lo'], nir['hi']))}", ref_src=S31DOC)
    claim(SN[sid], "R2 CV-tuned 35 trials", "4.7%", HAND, probe="S1 + ECG: 4.7% (−0.4 to 9.9)", ref_src=HAND)
    rows.append(("Earlier sensitivities (version 1 cohorts)", f"CV-tuned penalty {cvt}; index-day ECGs excluded {nit}; R2 (CV-tuned PS, its own 35-trial set) 4.7%", "31"))
    body = "".join(f'<tr><td><b>{esc(a)}</b></td><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows)
    allv = [x["rr"] for x in cfv] + [v29["rr"], v30["rr"], RR.relred54_v2, cvr["rr"], nir["rr"], p32["rr"]]
    pos = sum(v > 0 for v in allv)
    lo_, hi_ = math.floor(min(v for v in allv if v > 0)), math.ceil(max(allv))
    claim(SN[sid], "positive checks", f"{pos} of {len(allv)}", "this slide's estimates", ref=str(pos) + f" of {len(allv)}", ref_how="count of the slide's estimates > 0")
    claim(SN[sid], "size range", f"{lo_}–{hi_}%", "this slide's estimates", ref=f"{lo_}–{hi_}%", ref_how="floor(min positive)-ceil(max)")
    return sec(sid, "Robustness of PS-CVD5 + ECG vs PS-CVD5 (54 items; 31 trials)", f"""
<table class="t tsm rob"><tr><th style="width:250px">Check</th><th>Result</th><th>Trials</th></tr>{body}</table>
<p style="font-size:19px;margin-top:10px">The direction holds in {pos} of {len(allv)} estimates (all but the gradient-boosted PS). Where positive, the size is about <b>{lo_}–{hi_}%</b> and moves by a few points with the PS method, cohort definition, trial set and penalty.</p>""",
               links=more(SN["a-fix"], SN["a-fw"]))


def s_takehome():
    sid = "s-take"
    p5, _ = stat_v1(sid, "take-home PS-CVD5 + ECG (31)", "s31", "P5", "ECG")
    p32, _ = stat_v1(sid, "take-home PS-CVD5 + ECG (32, with PROTECT AF)", "s32", "P5", "ECG")
    d, _ = stat_v1(sid, "take-home PS-Demo + ECG (31)", "s31", "P1", "ECG")
    e, _ = stat_v1(sid, "take-home ECG vs permuted (31)", "s31", "P5", "ECG", "shufECG")
    c10, _ = stat_v1(sid, "take-home PS-CVD10 + ECG (31)", "s31", "PS10", "ECG")
    h, _ = stat_v1(sid, "take-home hdPS + ECG (31)", "s31", "hdPS200", "ECG")
    m, _ = stat_v1(sid, "take-home PS-Clinical + ECG (31)", "s31", "clinical_nolvef", "ECG")
    bps = [agree_v1(sid, f"take-home P5 agreement {ts}", ts, "P5")[1] for ts in ("s31", "f37", "v2")]
    _, bc10 = agree_v1(sid, "take-home CVD10 agreement 31", "s31", "PS10")
    clin = "5-draw MI" if CTX["mi"] else "single imputation; MI pending"
    RRF = pd.read_csv(S31SUM["v1"] / "random_removal_summary.csv").set_index(["set", "arm"]).loc[("S31", "ECG")]
    claim(SN[sid], "take-home fixed cohorts (31)", f"{fx(RRF.relred54_v2)}%", S31SUM["v1"] / "random_removal_summary.csv", probe=f"→ {fx(RRF.relred54_v2)}%; random removal", ref_src=S31DOC)
    return sec(sid, "Take-home", f"""
<ol class="aims" style="margin-top:4px">
  <li><b>The ECG improves held-out balance when the PS is thin</b> (demographics and a few diagnoses): PS-CVD5 + ECG {ci(p5['rr'], p5['lo'], p5['hi'])} on the 31 trials (PS-Demo + ECG {fx(d['rr'])}%; with PROTECT AF, 32 trials: {fx(p32['rr'])}%). It beats its permuted placebo ({fx(e['rr'])}%).</li>
  <li><b>The gain is smaller with richer PS:</b> PS-CVD10 + ECG {fx(c10['rr'])}%, hdPS + ECG {fx(h['rr'])}%, PS-Clinical (no LVEF; {clin}) + ECG {ci(m['rr'], m['lo'], m['hi'])}, concentrated in observed LVEF and echo structure.</li>
  <li><b>No trial-specific agreement with the RCTs</b> for PS-CVD5 + ECG: benchmark-permutation P ≥ {min(bps):.2f} in the 31, all 37 feasible and the 29-trial set. (CVD10 + ECG gave {pv(bc10)} on the 31: post hoc, exploratory only.)</li>
  <li><b>Supporting:</b> the plasmode (the ECG removes part of a hidden physiological confounder's bias beyond PS-CVD5) and MIMIC-IV (similar balance gain, no agreement gain).</li>
  <li><b>Caveats:</b> one health system; quality tiers graded post hoc with LLM-assisted raters (clinician review pending); post hoc switch of the primary to PS-CVD5; the return to version 1 cohorts was decided after the fixed-cohort results were known (fixed cohorts: {fx(RRF.relred54_v2)}%; both reported); the size rule was raised to ≥350 after the PROTECT AF near-separation was seen (32-trial results reported as a sensitivity).</li>
</ol>""")  # deck2: the former A6 (design history) link removed


def s_decisions():
    sid = "s-dec"
    mi, _ = stat_v1(sid, "open decision PS-Clinical (no LVEF, MI) + ECG (31)", "s31", "clinical_nolvef", "ECG")
    mtxt = f"{fx(mi['rr'])}%, {pv(mi['p'])} on the 31"
    return sec(sid, "Open decisions", """
<div style="display:grid;grid-template-columns:1fr 1fr;gap:36px">
<ol class="dec">
  <li><b>Clinician review</b> of the v19 emulation-quality tiers and the physiologic trial labels (both LLM-assisted so far).</li>
  <li><b>PS-Clinical (no LVEF), 5-draw MI on version 1 cohorts</b>: review the result (__MI__) and the unstable PS-alone HRs across draws; decide whether to add "was measured" flags.</li>
  <li><b>Disclosure</b> of the post hoc decisions: PS-CVD5 as primary; return to version 1 cohorts after the fixed-cohort results; feasibility size rule raised to ≥350 after the PROTECT AF near-separation (32-trial results as a sensitivity); spec-v2 fixes and framework v2.0 as sensitivities.</li>
  <li><b>Known version 1 cohort issues</b> (COMET metoprolol formulation and LVEF, EMPEROR-Preserved DPP-4i agents, class washouts, LIFE ECG-LVH, TRANSFORM-HF time zero): limitation text, or targeted rebuilds.</li>
  <li><b>Plasmode re-check</b> on the final trial set (pipeline.md §8, pending).</li>
</ol>
<ol class="dec" start="6">
  <li><b>CLMBR-T</b>: back on the aims slide and as a comparison arm (slide 7, Figure 2C); how and where its results return (main text vs supplement), to be confirmed with the PI.</li>
  <li><b>External validation scope</b>: UK Biobank and dbGaP trial cohorts (ACCORD, WHI, CHS) are planned, not started.</li>
  <li><b>Study name</b> LATENT-RCT (for now): "RCT" may be read as a randomized-trial label by journals and indexers (alternative: LATENT-TTE).</li>
  <li><b>Manuscript file</b> (paper.md vs paper2.md) and the methods lock (pipeline.md §10–11).</li>
</ol>
</div>""".replace("__MI__", mtxt))  # deck2: the former A6 link removed


# ================================================================ appendix
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
    out = ""
    sid = "a-t1"  # deck2 (2026-10-14): one appendix slide, the full table scrolls (formerly A3 + A3b)
    for r in rows:
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
        an = t["s31"]
        fe = "" if t["f37"] else f'<span class="fxl">{esc(t["status"])}</span>'  # PROTECT AF: excluded at feasibility (smaller arm < 350)
        if not t["f37"]:
            claim(SN[sid], f"Table 1 status {r['Trial']}", t["status"], ROOT / "scripts/build_balance_explorer.py", probe="excluded at feasibility (smaller arm < 350)",
                  ref_src=ROOT / "scripts/build_balance_explorer.py")
        out += (f'<tr class="{"an" if an else "ex"}"><td>{esc(r["Area"])}</td><td class="n">{esc(r["Trial"])}{fe}</td><td>{esc(r["Population"])}</td><td>{esc(r["Intervention"])}</td>'
                f'<td>{esc(r["Comparator"])}</td><td>{esc(r["Outcome (RCT primary endpoint)"])}</td><td>{esc(r["Time (mo)"])}</td><td>{esc(r["RCT estimate (CI)"])}</td>'
                f'<td class="nw">{esc(tq)}</td><td>{"yes" if an else "no"}</td></tr>')
    assert out.count("<tr") == 38 and out.count('<tr class="an">') == 31, (out.count("<tr"), out.count('<tr class="an">'))
    hdr = ('<colgroup><col style="width:68px"><col style="width:128px"><col style="width:170px"><col style="width:112px"><col style="width:118px">'
           '<col style="width:250px"><col style="width:24px"><col style="width:166px"><col style="width:86px"><col style="width:56px"></colgroup>') + '<thead><tr><th>Area</th><th>Trial</th><th>Population</th><th>Intervention</th><th>Comparator</th><th>Outcome (RCT primary endpoint)</th><th>Mo</th><th>RCT estimate (CI)</th><th>Quality (pts)</th><th>In 31</th></tr></thead>'
    foot = ('<p class="xs" style="margin-top:4px"><b>Scroll for all 38 trials</b> (AF, HF, hypertension, ACS / MI, diabetes, other). HR unless indicated; 95% CI unless indicated. '
            'Mo = trial-matched horizon. Quality = v19 tier (design points). <b>The 31 analysed</b> are highlighted (red bar, "yes"); grey = excluded (Limited, or PROTECT AF at '
            'feasibility: smaller arm &lt; 350). Source: docs/paper/table1_picot.md (= paper.md Table 1).</p>')
    return sec(sid, "All 38 emulated trials (paper Table 1)", f'<div class="t1wrap t1scroll" tabindex="0"><table class="t1">{hdr}<tbody>{out}</tbody></table></div>{foot}')


def s_a4(trials_old, Q):
    sid = "a-fw"
    n0 = len(V2.CL)
    h = V2.s_framework(trials_old, Q)
    cl_slide(n0, sid)
    h = one(h, "<p class=\"small\" style=\"margin-top:8px\">Analysed set = Excellent + Good + Moderate.",
            f"<p class=\"small\" style=\"margin-top:8px\"><b>Sensitivity analysis only</b> (primary: v19 tiers, {SN['a-qual']}). Analysed set = Excellent + Good + Moderate.")
    return retitle(h, sid, "Emulation-quality framework v2.0 (sensitivity)")


def s_a5(trials_old, EX, RR):
    sid = "a-fix"
    b31 = {t["id"]: t["s31"] for t in CTX["trials"]}
    t31 = [dict(t, v2c=b31[t["id"]]) for t in trials_old]  # colour = in the 31 (the primary set)
    n0 = len(V2.CL)
    h = V2.s_fixes(t31, EX, RR)
    cl_slide(n0, sid)
    h = one(h, "(navy = in the analysed 30)", "(navy = in the 31 analysed)")
    R31 = pd.read_csv(S31SUM["v1"] / "random_removal_summary.csv").set_index(["set", "arm"]).loc[("S31", "ECG")]
    v1, v2 = fx(R31.relred54_v1), fx(R31.relred54_v2)
    rnd = f"{fx(R31.relred54_random_median)} ({fx(R31.relred54_random_p5)} to {fx(R31.relred54_random_p95)})"
    claim(SN[sid], "random removal S31 ECG", f"{v1} | {v2} | {rnd}", S31SUM["v1"] / "random_removal_summary.csv",
          probe=f"{v1}% → {v2}%; random removal median {rnd}", ref_src=S31DOC)
    h = one(h, "<tr><td>Paper 1's 32</td>", f"<tr><td><b>31 (primary)</b></td><td>{v1}%</td><td><b>{v2}%</b></td><td>{rnd}</td></tr><tr><td>Paper 1's 32 (with PROTECT AF)</td>")
    h = one(h, '<h3 class="h3">Five kinds of fix', '<p class="small red" style="margin:0 0 4px"><b>Sensitivity analysis</b>; the primary analysis uses the version 1 cohorts.</p>\n    <h3 class="h3">Five kinds of fix')
    h = one(h, '<p style="font-size:18px;margin-top:10px">Removing the', '<p style="font-size:16px;margin-top:8px">Removing the')
    h = one(h, "So the drop from about 9% to 6.5% reflects", "So the drop from about 9% to 6.5–7% reflects")
    return retitle(h, sid, "Spec-v2 cohort fixes (sensitivity): what was removed, and does it explain the smaller ECG gain?")


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
.aimfig{position:absolute;left:30px;right:30px;top:178px;transition:opacity .45s,transform .45s}
.aimfig.hid{opacity:0;visibility:hidden;transform:translateY(14px)}
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
table.t1 tr.an td:first-child{box-shadow:inset 3px 0 0 var(--red)}
.t1scroll{height:526px;overflow-y:auto;overflow-x:hidden;border-bottom:2px solid var(--navy);outline:none}
table.t1 thead th{position:sticky;top:0;z-index:2}
table.t1 tr.an td:last-child{color:var(--red);font-weight:700}
table.t1 .fxl{display:block;font-weight:600;font-size:9px;color:#a8322e;white-space:normal;line-height:1.15}
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
/* slide 8: methods, covariate balancing (deck2) */
.cbal{display:grid;grid-template-columns:1.15fr 1fr;gap:40px;margin-top:30px}
.cbal .card{padding:22px 28px;min-height:330px}
.cbal .h3{font-size:20px;margin:0 0 14px}
ul.cbl{padding-left:26px;margin:0}
ul.cbl li{font-size:23px;line-height:1.38;margin:0 0 18px}
ul.cbl .eq{font-size:19px;margin:10px 0 0;padding:8px 12px;background:var(--band);display:inline-block}
ul.cbl .eq sub{font-size:.68em}
/* the balance results slide: Figure 2 */
.fig2box{position:relative;margin:-10px auto 0}
.fig2box img.f2p{position:absolute;display:block;height:auto}
.fig2box img.f2p.build{transition:opacity .45s}
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
/* ===== appendix A1: interactive emulation-quality viewer (v19 points; framework v2.0 toggle) ===== */
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
  <label class="h">Show</label><select id="qv-filt"><option value="all">All 38 emulated</option><option value="an">Analysed (31)</option><option value="ex">Excluded (Limited or feasibility)</option></select>
  <label class="cb" style="margin-top:8px"><input type="checkbox" id="qv-v2">Framework v2.0 (sensitivity)</label>
  <div class="desc" style="margin-top:8px">v19 points rule (primary): F1–F5 = design flags; Comp. / Outc. = comparator / outcome fidelity (G 0, M 1, P 2). Tier: Excellent 0, Good 1–2, Moderate 3 (or capped), Limited ≥4 (excluded). PROTECT AF is excluded earlier, at feasibility (smaller arm &lt; 350). Tick to add the framework v2.0 items (EL–SI, 0–2), its total and tiers. Click a row for the rationale.</div>`;
  for (const id of ["qv-sort", "qv-filt", "qv-v2"]) $("#" + id).onchange = qvUpdate;
  qvUpdate();
}
let QSEL = null;
function qvUpdate() {
  const v2 = $("#qv-v2").checked, srt = $("#qv-sort").value, f = $("#qv-filt").value;
  let T = D.trials.map((t, i) => i).filter(i => f === "all" || (f === "an" ? D.trials[i].s31 : !D.trials[i].s31));
  const key = {tier: t => [QTI[t.t19], t.tot, AREAS.indexOf(t.area), t.name], area: t => [AREAS.indexOf(t.area), QTI[t.t19], t.tot, t.name], name: t => [t.name],
    tv2: t => [QTI[t.tv2], t.tot2, t.name]}[srt];
  T.sort((a, b) => { const ka = key(D.trials[a]), kb = key(D.trials[b]); for (let i = 0; i < ka.length; i++) { if (ka[i] < kb[i]) return -1; if (ka[i] > kb[i]) return 1; } return 0; });
  const tg = q => `<span class="tier t${QTI[q]}">${q}</span>`;
  let h = `<table><tr><th class="l">Trial</th><th class="l">Area</th><th>F1</th><th>F2</th><th>F3</th><th>F4</th><th>F5</th><th>Comp.</th><th>Outc.</th><th>Pts</th><th class="l">v19 tier</th><th class="l">Analysed</th>` +
    (v2 ? QI2.map(x => `<th>${x}</th>`).join("") + `<th>Tot</th><th class="l">v2.0 (spec-v2)</th><th class="l">v2.0 (v1 coh.)</th><th>in 30</th>` : "") + `</tr>`;
  for (const i of T) { const t = D.trials[i];
    h += `<tr class="${t.s31 ? "" : "ex"} ${QSEL === i ? "sel" : ""}" data-i="${i}"><td class="l"><b>${esc(t.name)}</b>${v2 && t.prov ? "†" : ""}</td><td class="l">${esc(t.area)}</td>` +
      t.fl.map(v => `<td>${v ? "✓" : ""}</td>`).join("") + `<td class="${t.co === "P" ? "P" : ""}">${t.co}</td><td class="${t.ou === "P" ? "P" : ""}">${t.ou}</td><td><b>${t.tot}</b></td><td class="l">${tg(t.t19)}</td>` +
      `<td class="l">${t.s31 ? "yes" : t.f37 ? "no (≥4 pts)" : "no (feasibility)"}</td>` +
      (v2 ? t.it.map(v => `<td class="v2 ${v === 2 ? "P" : ""}">${v || ""}</td>`).join("") + `<td class="v2"><b>${t.tot2}</b></td><td class="l v2">${tg(t.tv2)}</td><td class="l v2">${tg(t.tq1)}</td><td class="v2">${t.v2c ? "✓" : ""}</td>` : "") + `</tr>`; }
  $("#qv-tab").innerHTML = h + `</table>`;
  $("#qv-tab").querySelectorAll("tr[data-i]").forEach(r => r.onclick = () => { QSEL = +r.dataset.i; qvUpdate(); });
  const t = QSEL === null ? null : D.trials[QSEL];
  $("#qv-det").innerHTML = !t ? `<div class="note" style="margin-top:20px">Click a trial for its items, points and rationale.</div>` :
    `<h4>${esc(t.full)}</h4><div class="note"><b>${esc(t.area)}</b>; horizon ${t.hz} mo</div><div class="note"><b>v19:</b> ${esc(qWhy(t))} → <b>${t.t19}</b>${t.cap ? " (capped)" : ""}; ${t.s31 ? "<b>analysed</b>" : `<b style='color:#a8322e'>${t.f37 ? "excluded (Limited)" : esc(t.status)}</b>`}</div>` +
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
const nSteps = sl => Math.max(+sl.dataset.steps || 0, ...[...sl.querySelectorAll(".build,.fstep,.only")].map(e => +e.dataset.step || 0));
function applyBuild() {
  const sl = slides[cur], last = Math.max(0, ...[...sl.querySelectorAll(".fstep")].map(e => +e.dataset.step || 0));
  /* .only = shown at its own step only (slide 4's representations graphic); while shown, the focus step it belongs to (data-of) stays undimmed */
  const on = [...sl.querySelectorAll(".only")].filter(e => +e.dataset.step === step).map(e => +e.dataset.of);
  sl.querySelectorAll(".only").forEach(e => e.classList.toggle("hid", +e.dataset.step !== step));
  sl.querySelectorAll(".build").forEach(e => e.classList.toggle("hid", (+e.dataset.step || 0) > step));
  sl.querySelectorAll(".fstep").forEach(e => { const k = +e.dataset.step || 0; e.classList.toggle("hid", k > step); e.classList.toggle("dim", k < step && step <= last && !on.includes(k)); });
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
  sl.querySelectorAll(".t1scroll").forEach(e => { e.scrollTop = 0; });  /* the Table 1 appendix always opens at its first rows */
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
         'let h = `<option value="s31">Primary: ${n(t => t.s31)} trials (paper 1\'s 32 minus PROTECT AF)</option><option value="s32">Sens.: paper 1\'s ${n(t => t.s32)} (with PROTECT AF)</option><option value="v2c">Sens.: framework v2.0, rescored (${n(t => t.v2c)})</option><option value="v2">Sens.: framework v2.0, provisional (${n(t => t.v2)})</option>'),
        ('<optgroup label="Quality tier (v2.0, rescored)">', '<optgroup label="Quality tier (v19, of the 37 feasible)">'),
        # s31 (2026-10-14): the 37 feasible / all 38, areas of the 31, tiers of the 37, physiologic label within the 31
        ('<option value="all">All ${NT} emulated trials</option><optgroup label="Clinical area (all 38)">`;',
         '<option value="f37">All ${n(t => t.f37)} feasible trials</option><option value="all">All ${NT} emulated (with PROTECT AF)</option><optgroup label="Clinical area (of the 31)">`;'),
        ('h += `<option value="area:${a}">${a} (${n(t => t.area === a)})</option>`;', 'h += `<option value="area31:${a}">${a} (${n(t => t.area === a && t.s31)})</option>`;'),
        ('h += `<option value="q:${q.join(",")}">${q.join(" or ")} (${n(t => q.includes(t.tier))})</option>`;',
         'h += `<option value="q37:${q.join(",")}">${q.join(" or ")} (${n(t => q.includes(t.tier) && t.f37)})</option>`;'),
        ('["yes", "s32", "Physiologic: yes, paper 1 set"], ["no", "s32", "Physiologic: no, paper 1 set"]', '["yes", "s31", "Physiologic: yes, the 31"], ["no", "s31", "Physiologic: no, the 31"]'),
        ('(${n(t => t.phys === (y === "yes") && (s === "all" || t.s32))})', '(${n(t => t.phys === (y === "yes") && (s === "all" || t[s]))})'),
        ('  if (v === "s32") return idx.filter(i => D.trials[i].s32);\n',
         '  if (v === "s31") return idx.filter(i => D.trials[i].s31);\n  if (v === "f37") return idx.filter(i => D.trials[i].f37);\n  if (v === "s32") return idx.filter(i => D.trials[i].s32);\n'),
        ('  if (k === "q") {', '  if (k === "q37") { const q = x.split(","); return idx.filter(i => q.includes(D.trials[i].tier) && D.trials[i].f37); }\n  if (k === "area31") return idx.filter(i => D.trials[i].area === x && D.trials[i].s31);\n  if (k === "q") {'),
        ('(s === "all" || D.trials[i].s32)); }', '(s === "all" || D.trials[i][s])); }'),
        ('<select id="c-coh"><option value="v2" selected>Spec-v2 fixed cohorts (primary)</option><option value="v1">Version 1 cohorts (as built)</option></select>',
         '<select id="c-coh"><option value="v1" selected>Version 1 cohorts (primary)</option><option value="v2">Spec-v2 fixed cohorts (sensitivity)</option></select>'),
        ('" Version 1: single imputation (draw 1)."', '" Version 1: ' + ('5-draw multiple imputation; per-item |SMD| averaged across the draws."' if CTX["mi"] else 'single imputation (draw 1); MI pending."')),
        ('"Cohorts as built for paper 1 (no fixes); the expanded panel exists only here."', '"Version 1 cohorts as built (primary; original selection criteria); the expanded panel exists only here."'),
        ('$("#c-trials").value === "v2c" && panel === "54"', '$("#c-trials").value === "s31" && panel === "54"'),
        ('<b>Primary analysis (pipeline.md; ECG-only paper):</b>', '<b>Primary analysis (pipeline.md, 2026-10-14):</b>'),
        ('rescored analysed set (30 trials; provisional, not frozen). ${M.coh === "v2" ? "Spec-v2 fixed cohorts." : "Version 1 cohorts (pre-fix reference)."}',
         'the 31 trials (paper 1\'s 32 minus PROTECT AF, excluded at feasibility; v19 tiers). ${M.coh === "v1" ? "Version 1 cohorts." : "Spec-v2 fixed cohorts (sensitivity analysis)."}'),
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
            '<section class="slide" data-title="Results 2: covariate balance explorer" id="s-bal">')  # deck2: after Figure 2 (Results 1)
    h = one(h, '    <div class="side" id="sum"></div>\n  </div>\n</section>', '    <div class="side" id="sum"></div>\n  </div>\n' + more(SN["a-fw"], SN["a-fix"]) + "\n</section>")
    h = one(h, '<div class="chart" style="padding:2px 10px;overflow-y:auto"><svg id="agq-svg" viewBox="0 0 900 300" style="width:100%;height:auto;flex:none"></svg><div id="agq-tab"></div></div>\n  </div>\n</section>',
            '<div class="chart" style="padding:2px 10px;overflow-y:auto"><svg id="agq-svg" viewBox="0 0 900 300" style="width:100%;height:auto;flex:none"></svg><div id="agq-tab"></div></div>\n  </div>\n' + more(SN["a-qual"]) + "\n</section>")
    h = one(h, 'const TSRC = {tier: "Framework v2.0, rescored (spec-v2 cohorts)", tq1: "Framework v2.0, version 1 cohorts", t19: "v19 tiers (paper 1)"};',
            'const TSRC = {t19: "v19 tiers (paper 1; primary)", tv2: "Framework v2.0, rescored on spec-v2 cohorts (sensitivity)", tq1: "Framework v2.0, version 1 cohorts (sensitivity)"};')
    h = one(h, 'const cohOpt = `<option value="v2" selected>Spec-v2 fixed cohorts (primary)</option><option value="v1">Version 1 cohorts (as built)</option>`;',
            'const cohOpt = `<option value="v1" selected>Version 1 cohorts (primary)</option><option value="v2">Spec-v2 fixed cohorts (sensitivity)</option>`;')
    h = one(h, "PS-Clinical (no LVEF) on the spec-v2 cohorts: HRs combined over 5 imputation draws (Rubin).",
            "PS-Clinical (no LVEF): HRs combined over 5 imputation draws (Rubin) on both cohort versions." if CTX["mi"] else
            "PS-Clinical (no LVEF): spec-v2 cohorts, HRs combined over 5 imputation draws (Rubin); version 1 cohorts, single imputation (MI pending).")
    h = one(h, "All 38 emulated trials, grouped by their quality tier. Tiers were assigned blind to the results; the rescored tiers are provisional (not frozen; LLM raters, no clinician review yet).",
            "The 37 feasible trials (default; PROTECT AF excluded at feasibility) or all 38 emulated, grouped by quality tier (default: v19 tiers, as paper 1). Tiers were assigned from design information, blind to the results, by LLM-assisted raters; no clinician review yet. Framework v2.0 tiers: sensitivity.")
    # agreement by quality (s31, 2026-10-14): a trial-set control, default = the 37 feasible (PROTECT AF excluded at feasibility)
    h = one(h, '  <label class="h">Cohorts</label>${sel("agq-coh", cohOpt)}\n  <label class="h">PS base</label>${sel("agq-rung", rungOptE())}',
            '  <label class="h">Cohorts</label>${sel("agq-coh", cohOpt)}\n  <label class="h">Trials</label>${sel("agq-set", `<option value="f37" selected>37 feasible (primary)</option><option value="all">All 38 (with PROTECT AF)</option>`)}\n'
            '  <label class="h">PS base</label>${sel("agq-rung", rungOptE())}')
    h = one(h, 'for (const id of ["agq-coh", "agq-rung", "agq-cfg", "agq-src", "agq-split", "agq-met"]) $("#" + id).onchange = agqUpdate;',
            'for (const id of ["agq-coh", "agq-set", "agq-rung", "agq-cfg", "agq-src", "agq-split", "agq-met"]) $("#" + id).onchange = agqUpdate;')
    h = one(h, '  const idx = D.trials.map((_, i) => i), tq = i => D.trials[i][src];',
            '  const idx = D.trials.map((_, i) => i).filter(i => $("#agq-set").value === "all" || D.trials[i].f37), tq = i => D.trials[i][src];')
    h = one(h, '${coh === "v2" ? "spec-v2" : "version 1"} cohorts · tiers: ${esc(TSRC[src])}</text>`;',
            '${coh === "v2" ? "spec-v2" : "version 1"} cohorts · ${$("#agq-set").value === "all" ? "all 38" : "37 feasible"} · ${esc(TSRC[src].split(" (")[0])}</text>`;')
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
    SM = {"S31": "s31", "S32": "s32", "S38": "all", "S29": "v2", "Snew": "v2c"}
    for _, s in V1.iterrows():
        if not (s.config == "main" or s.rung_a == "P5"):
            continue
        for panel in ("54", "58"):
            pre, mm = ("relred54", "m54") if panel == "54" else ("relred58", "m58")
            tag = "REQUIRED default (v1, 31, PS-CVD5, 54 leak)" if (s.set == "S31" and s.config == "main" and s.rung_a == "P5" and s.arm_a == "ECG" and s.arm_b == "base" and panel == "54") else ""
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
                    tag="REQUIRED PS-Clinical MI v1 31" if (s.set == "S31" and s.config == "main" and rg == "clinical_nolvef" and s.arm_a == "ECG" and s.arm_b == "base" and panel == "54") else "")
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
        for ts in ("q37:Excellent,Good", "q37:Moderate", "area31:AF", "area31:Diabetes", "phys:yes,s31", "f37", "q:Excellent,Good", "phys:yes,s32"):
            for rg in ("P1", "P5", "hdPS200", "clinical_nolvef"):
                add("computed (pair_stats)", coh, "main", rg, "ECG", "base", ts, "54", True, {})
    return combos


def emu_refs(D):
    out = []
    VC = CTX["VC"]
    V1 = VC[(VC.cohort == "v1") & (VC.kind == "within") & (VC.config == "main") & VC.rung_a.isin(["P1", "P5", "PS10", "hdPS200"]) & (VC.arm_b == "base")
            & VC.arm_a.isin(["ECG", "shufECG"])]
    SM = {"S31": "s31", "S32": "s32", "S38": "all", "S29": "v2", "Snew": "v2c"}
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
    VC = V2.get_contrasts()[1]
    s31v = pd.read_csv(S31SUM["v1"] / "contrasts.csv")
    assert json.load(open(S31D / "summary_gate.json"))["passed"]  # its S32 rows equal the committed summaries
    CTX.update(mi=mi, g1=g1, g2=g2, VC=pd.concat([VC, s31v[s31v.set == "S31"]], ignore_index=True))
    if mi:
        s31m = pd.read_csv(S31SUM["mi"] / "contrasts.csv")
        CTX["MIS"] = pd.concat([pd.read_csv(MI_V1SUM / "contrasts.csv"), s31m[s31m.set == "S31"]], ignore_index=True)
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
    # s31 primary from the cells = the s31 summary (8.7% (4.2 to 13.5), 20/31; docs/s31/S31_RESULTS.md)
    r = ps(CTX["G1"], "main", "P5", "ECG", "base", "s31")
    assert f"{r['rr']:.1f}|{r['lo']:.1f}|{r['hi']:.1f}|{r['lower']}/{r['k']}" == "8.7|4.2|13.5|20/31", r
    EX = load_ex()
    RR = pd.read_csv(V2.RRS)
    T1001, deck1001 = L1.TEMPLATE, DECK1001.read_text()
    # deck2: Figure 2 (s_results2) now precedes the balance explorer, so it joins the block before the explorer section
    static1 = [intro_markup(T1001, deck1001), s_aims(), s_overview(), s_pipe(), s_methods_design(), s_methods_panel(), s_results2()]
    static2 = []
    static3 = [s_robust()]
    static4 = [retitle(V2.s_plasmode(), "s-plas", "Plasmode: a known truth with a hidden physiological confounder (version 1 cohorts)"),
               retitle(V2.s_mimic(), "s-mimic", "External replication: MIMIC-IV (PS-CVD5 analog ± ECG)"),
               s_takehome(), s_decisions(), s_a2(), s_a3(), s_apanel(), s_a4(trials_old, Q), s_a5(trials_old, EX, RR)]
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
