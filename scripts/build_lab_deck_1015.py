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

Revision of 2026-10-14, Figure 2D job (docs/queue/figure2D.md): the new panel D (bars coloured by cardiac-physiology decision,
descriptive; trial names) is shown at click 3; once revealed, clicking it (or the hint under it) opens a popup (the existing
popup() mechanism) with four tabs of the same per-trial values: cardiac-physiology (default), clinical area, type of treatment
decision, physiologic label (PNGs from scripts/figures/make_figure2d_groupings.py). Every group count and mean is a claim, checked
against pair_stats on the group's trials and against EXPECT_F2D. Outputs of this builder go to audits/claude-fig2d-20261014/deck.

Revision of 2026-10-14, Figure 3 job (docs/queue/figure3.md): new slide 11 "Results: agreement with the RCTs (Figure 3)" directly
after the balance explorer (slides 11-17 become 12-18), built from the per-panel PNGs of scripts/figures/make_figure3_latent.py and
revealed A, B, C (one per click). Panel A's inset numbers and every B / C value are claims (figure3_values.json vs S31_RESULTS.md and
the log HRs). CLMBR-T is a comparison arm only. Outputs of this builder go to audits/claude-fig3-20261014/deck.

Revision of 2026-10-14, slide 9 panel D job (docs/queue/slide9_panelD.md; deck only, the paper's Figure 2 is unchanged): slide 9's
click 3 shows a new panel D, overall balance of demographics + AI representations (Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T)
vs conventional PS (PS-CVD5, hdPS, PS-Clinical), labels vs hdPS (scripts/figures/make_slide9_panelD_overall.py); its 7 means and 3
contrasts are claims, recomputed here from the cells (cross-rung, items observed in both arms) and gated against figure4.md. The
per-trial panel D and its groupings popup move unchanged to a new appendix A4 "Per-trial covariate balance improvement"; framework
v2.0 becomes A5 and the spec-v2 fixes A6. Outputs of this builder go to audits/claude-slide9d-20261014/deck.

Revision of 2026-10-14, slide 11 panel C job (docs/queue/slide11_figure3.md; deck only, the paper's Figure 3 is unchanged): slide 11's
click 3 shows a new full-width panel C under A and B, agreement with the RCTs (mean |dlog HR|) of demographics + AI representations
(Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T) vs conventional PS (PS-CVD5, hdPS, PS-Clinical), labelled vs PS-CVD5 and vs hdPS
(scripts/figures/make_slide11_panelC_agreement.py); its 7 means and 6 contrasts with P are claims, recomputed here from the version 1
cells and gated against figure4.md. The old panel C (agreement by emulation quality) moves with its claims to a new appendix A7
"Agreement by emulation quality", appended after A6 (no existing label changes) and linked from slide 11's "More:". Outputs of this
builder go to audits/claude-slide11c-20261014/deck.

Revision of 2026-10-14, third deck-edit job (docs/queue/QUEUE_2026_10_14_DECK3.md; no number changes): display labels AI-ECG (the
BCL ECG embedding) and AI-EHR (CLMBR-T) everywhere (relabel(); defined once on slides 4 and 7; raw-test wording kept); figure slides
headed "Figure 2. Covariate balance" / "Figure 3. Agreement with RCTs"; slide 8 = a copy of the slide 4 aims list with aim 2
highlighted plus the balance endpoints and tests; new slide 10 = the same with aim 3 highlighted plus the agreement methods; the
balance and trial emulation explorers leave the main sequence and become Supplementary Figures 2 and 3 (S2, S3: PS and
representation selects only, version 1 cohorts, the 31 trials, main configuration, 54 leakage-corrected items), opened from
slide 9's panel A and from a button after slide 11's last step, with "Back to Figure 2 / 3", Esc and the browser back button; the
deck data gain the + AI-EHR and + AI-ECG + AI-EHR arms (version 1, main configuration) for them. Robustness slide deleted; plasmode
and agreement by quality (two consecutive slides with the former Figure 3 panel C) moved to the appendix; appendix renumbered.

Main slides: 1 title; 2 Background (10-01); 3 Problem (10-01 schematic, click reveal of the unmeasured side + three points); 4 Aims
(four aims, revealed one at a time; the representations graphic between aims 1 and 2); 5 study overview (empty body); 6 LATENT-RCT
pipeline; 7 PSM experiments; 8 methods: covariate balancing (aims, aim 2); 9 Figure 2; 10 methods: agreement (aims, aim 3); 11
Figure 3; 12 MIMIC-IV; 13 take-home; 14 open decisions. Supplementary S2 (covariate balance explorer), S3 (trial emulation explorer).
Appendix A1-A9 (hash-linked; "More:" links on main slides, "Back to slide N" on every appendix slide): A1 emulation-quality
criteria + interactive quality viewer (v19; framework v2.0 toggle); A2 all 38 trials (Table 1, scrollable); A3 held-out panel and
leakage-corrected masking; A4 per-trial covariate balance improvement (the former Figure 2D panel and its groupings popup); A5
plasmode; A6 framework v2.0 (sensitivity); A7 spec-v2 cohort fixes (sensitivity); A8 agreement by emulation quality (the former
Figure 3 panel C); A9 agreement by emulation quality, interactive (the former main slide).

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
FIG2DD = A / "claude-fig2d-20261014"  # Figure 2D job (docs/queue/figure2D.md)
SCR = A / "claude-deck3-20261014/deck"  # claims table and validation inputs (deck3 run; earlier runs' copies stay in their audit folders)
FIG2 = ROOT / "docs/paper/figures_latent/figure2_covariate_balance.png"  # scripts/figures/make_figure2_latent.py
FIG2V = FIG2DD / "figure2_values.json"  # its aggregate values (validated there)
FIG2G = FIG2.parent / "panels" / "panelD_groupings"  # the panel D popup's tabs (scripts/figures/make_figure2d_groupings.py)
# panel D groups (improved, trials, mean points), displayed values; queue file figure2D.md. Three popup means differ by 0.1 from the
# queue file's, which were computed from 1-decimal per-trial values (make_figure2d_groupings.summaries): ACS / MI +5.6 (5.556),
# Hypertension and BP-lowering -4.6 (-4.630)
EXPECT_F2D = {"cardiac": "10 of 11|+9.9", "other": "9 of 20|-0.3", "all": "19 of 31|+3.3",
              "area": {"AF": "7 of 11|+4.5", "HF": "4 of 5|+7.4", "ACS / MI": "1 of 2|+5.6", "Hypertension": "1 of 2|-4.6", "Diabetes": "3 of 7|+0.8",
                       "Other": "3 of 4|+2.3"},
              "decision": {"Rhythm control (drug or ablation)": "5 of 5|+12.2", "HF / RAAS drug choice": "5 of 6|+8.0",
                           "Antithrombotic (incl. LAA occlusion)": "3 of 8|-0.5", "Glucose-lowering": "3 of 7|+0.8", "BP-lowering": "1 of 2|-4.6",
                           "Other (statin, NSAID)": "2 of 3|+0.6"},
              "physiologic": {"yes": "9 of 10|+8.5", "no": "10 of 21|+0.9"}}
F2D_NOTE = "Gains were concentrated in cardiac-physiology decisions (rhythm control, HF / RAAS drugs); descriptive grouping."
# slide 9 panel D job (docs/queue/slide9_panelD.md): the new panel D (deck only; scripts/figures/make_slide9_panelD_overall.py)
F2N = ROOT / "docs/paper/figures_latent/panels/deck/slide9_panelD_overall.png"
F2NV = A / "claude-slide9d-20261014/panelD_values.json"  # its aggregate values (gated there against figure4.md and recomputed_f4.json)
# rows: (label, rung, arm); expected displayed values (figure4.md, audited): mean |SMD| and the vs-hdPS labels (deck P format)
F2N_ROWS = [("Unmatched", "P5", "unmatched"), ("PS-CVD5", "P5", "base"), ("hdPS", "hdPS200", "base"), ("PS-Clinical", "clinical_nolvef", "base"),
            ("Demo + ECG", "P1", "ECG"), ("Demo + CLMBR-T", "P1", "CLMBR"), ("Demo + ECG + CLMBR-T", "P1", "ECG+CLMBR")]
EXPECT_F2N = {"Unmatched": "0.143", "PS-CVD5": "0.129", "hdPS": "0.114", "PS-Clinical": "0.118", "Demo + ECG": "0.126", "Demo + CLMBR-T": "0.112",
              "Demo + ECG + CLMBR-T": "0.106", "vs Demo + ECG": "10.2% higher|.029", "vs Demo + CLMBR-T": "2.0% lower|.53",
              "vs Demo + ECG + CLMBR-T": "8.0% lower|.012"}  # figure4.md P = .03 for Demo + ECG (2 decimals; .0286)
F2N_ALT = ("Figure 2 panel D (deck): overall balance, mean |SMD| over the 54 held-out items (31 trials): Unmatched; conventional PS "
           "(PS-CVD5, hdPS, PS-Clinical); demographics + AI representations (Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T), labelled vs hdPS.")
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
MAIN = ["s-title", "s-bg", "s-prob", "s-aims", "s-pipe", "s-meth1", "s-meth2", "s-res2", "s-meth3", "s-res3", "s-meth4", "s-mimic", "s-plasm", "s-plas",
        "s-take"]  # final touches 2026-10-15: open-decisions slide (s-dec) removed; deck3 (2026-10-14): new s-meth3 (aims, aim 3 + agreement methods) before Figure 3; the explorers (s-bal,
# s-emu) leave the main sequence (supplementary figures, SUPPF); s-rob is deleted; s-agq and s-plas move to the appendix
# supplementary figures (deck3): (id, label, title, the figure slide they open from and return to)
SUPPF = [("s-bal", "S2", "Supplementary Figure 2. Covariate balance explorer", "s-res2"),
         ("s-emu", "S3", "Supplementary Figure 3. Trial emulation", "s-res3")]
# appendix (deck3 2026-10-14, renumbered): plasmode (from slide 9) after the per-trial panel; agreement by quality = two consecutive
# slides (the former Figure 3 panel C, then the former main slide's interactive view), both from slide 11
APP = [("a-qual", "A1", "Emulation-quality criteria", "s-pipe"), ("a-t1", "A2", "All 38 trials (Table 1)", "s-pipe"),
       ("a-panel", "A3", "Held-out panel and leakage map", "s-meth2"), ("a-f2d", "A4", "Per-trial covariate balance improvement", "s-res2"),
       ("a-fw", "A5", "Framework v2.0 (sensitivity)", "s-res2"), ("a-fix", "A6", "Spec-v2 cohort fixes (sensitivity)", "s-res2"),
       ("a-f3q", "A7", "Agreement by emulation quality", "s-res3"), ("s-agq", "A8", "Agreement by emulation quality: interactive", "s-res3")]
# final touches (2026-10-15): slide 5 (empty study overview) removed; the plasmode returns to the main sequence after MIMIC-IV as a
# methods graphic (s-plasm) and the former appendix A5 results (s-plas); appendix renumbered A1-A8
SN = {s: str(i + 1) for i, s in enumerate(MAIN)}
SN.update({sid: lab for sid, lab, _, _ in SUPPF})
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


def back(sid, *labs):
    """the "Back to slide N" link; with labs, followed by "More:" links in the same line (deck3: A8 -> A9, A9 -> A1)."""
    m = (" · More: " + " · ".join(applink(l) for l in labs)) if labs else ""
    return f'<div class="xrefs"><a class="xref back" href="#{SN[sid]}" data-goto="{sid}" data-back="1">Back to slide <span class="lbl">{SN[sid]}</span></a>{m}</div>'


# ---------------------------------------------------------------- display labels (deck3, 2026-10-14)
# "ECG" -> "AI-ECG" (the BCL ECG embedding) and "CLMBR-T" -> "AI-EHR" in every label and text; analysis unchanged. Words that mean
# the raw test itself, and the two one-line definitions (slides 4 and 7), are protected; so is anything inside
# <!--norelabel-->...<!--/norelabel--> and every data: URI.
RAW_ECG = ["12-lead ECG", "with an ECG in", "raw ECG waveform", "ECG on or before index", "ECG foundation model embedding, BCL encoder",
           "EHR foundation model, CLMBR-T; coded history", "frozen CLMBR-T-base", "ECG and EHR foundation models"]
RELAB = [(r"CLMBR-T \+ ECG", "AI-ECG + AI-EHR"), (r"ECG \+ CLMBR-T", "AI-ECG + AI-EHR"), (r"(?<![\w-])CLMBR-T(?![\w-])", "AI-EHR"),
         (r"(?<![\w-])ECG(?![\w-])", "AI-ECG"), (r"\b[Tt]he AI-ECG ", "AI-ECG ")]  # "The ECG improves" -> "AI-ECG improves"


def relabel(h):
    out = []
    for k, part in enumerate(re.split(r'(<!--norelabel-->.*?<!--/norelabel-->|data:[a-z/+]+;base64,[A-Za-z0-9+/=]+)', h, flags=re.S)):
        if k % 2:
            out.append(part.replace("<!--norelabel-->", "").replace("<!--/norelabel-->", ""))
            continue
        keep = {}
        for i, w in enumerate(RAW_ECG):
            tok = f"\x00{i}\x00"
            if w in part:
                part = part.replace(w, tok)
                keep[tok] = w
        for a, b in RELAB:
            part = re.sub(a, b, part)
        for tok, w in keep.items():
            part = part.replace(tok, w)
        out.append(part)
    return "".join(out)


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


SX_RUNGS, SX_ARMS = ("P5", "PS10", "clinical_nolvef", "hdPS200"), ("CLMBR", "ECG+CLMBR")


def add_rep_arms(D, g1):
    """deck3 (2026-10-14): the + AI-EHR (CLMBR) and + AI-ECG + AI-EHR (ECG+CLMBR) arms of the version 1 cells, main configuration, the
    four PS of Supplementary Figures 2 and 3: per-trial |SMD| integers (as every other arm) and log HR / SE (V2.est_block's rules), plus
    their arm masks (BE.LEAK_ARM: the 4 coded items, none of the 54). Aggregates only."""
    R = g1["R"]
    for rg in SX_RUNGS:
        for a in SX_ARMS:
            D["S"]["main"][rg][a] = BE.enc(g1["G"][("main", rg, a)], BE.SC)
            h = R[(R.config == "main") & (R.rung == rg) & (R.arm == a)].set_index("trial").loc[g1["tids"]]
            D["EST"]["v1"]["main"][rg][a] = [None if f or not (np.isfinite(l) and np.isfinite(s)) else [round(float(l), 8), round(float(s), 8)]
                                             for f, l, s in zip(h.failed, h.loghr, h.se)]
    D["leak"]["arm"] = {a: [BE.VN.index(c) for c in BE.LEAK_ARM[a]] for a in SX_ARMS}
    assert not set(D["leak"]["arm"]["CLMBR"]) & set(BE.items("54"))


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
        <li class="build" data-step="1"><b>Missingness:</b> real-world EHR data are incomplete</li>
        <li class="build" data-step="2"><b>Missing physiology:</b> LV function, congestion, atrial substrate</li>
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
               '  s += `<g class="build rise" data-step="3">`;\n  s += `<text x="0" y="274" font-size="15" fill="${RED}" font-weight="700">unmeasured</text>`;')
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

    # deck3 (2026-10-14): the path headings are the one-line definitions of the two display labels
    for yc, head in ((100, DEF_ECG), (300, DEF_EHR)):
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
    for yc, lab, sub in ((100, "BCL encoder", None), (300, "CLMBR-T", None)):  # deck3: the encoders by name (the headings define them)
        s.append(arr(330, yc, 382, yc) + enc(390, yc, lab, sub) + arr(606, yc, 650, yc) + vec(660, yc - 56))
        s.append(txt(673, yc + 78, "embedding vector", fs=16, col=MU))
    s.append(f'<rect x="850" y="140" width="320" height="120" rx="8" fill="{NAVY}"/>' + txt(1010, 192, "Propensity score", fs=24, w=700, col="#fff")
             + txt(1010, 224, "matching", fs=24, w=700, col="#fff"))
    s.append(arr(696, 100, 846, 178) + arr(696, 300, 846, 222))
    s.append("</svg>")
    return f'<div class="aimfig only" data-step="2" data-of="1"><!--norelabel-->{"".join(s)}<!--/norelabel--></div>'


# the one-line definitions of the display labels (deck3, 2026-10-14): slide 4 (aims graphic) and slide 7 (PSM experiments)
DEF_ECG = "AI-ECG (ECG foundation model embedding, BCL encoder)"
DEF_EHR = "AI-EHR (EHR foundation model, CLMBR-T; coded history)"


def aims_list():
    """the slide 4 aims (number, icon, title, subtitle); reused by the aims copies on slides 8 and 10 (deck3)."""
    chip = lambda grp, what, done, st=None: (f'<div class="chip{" done" if done else ""}"><span class="cg">{grp}</span> {what} '
                                            f'<span class="st">{st or ("✓ done" if done else "planned")}</span></div>')
    return [
        (1, ICON["ecg"] + ICON["ehr"], "Integrate ECG and EHR foundation models into matching", "AI-ECG and AI-EHR · easy to operationalize"),
        (2, ICON["bal"], "Covariate balance", "on held-out measurements"),
        (3, ICON["rct"], "Trial emulation and agreement with RCTs", f"{sum(t['s31'] for t in CTX['trials'])} benchmark RCTs"),
        (4, ICON["glob"], "External validation",
         '<span class="chips">' + chip("EHR", "MIMIC-IV", True) + chip("Biobank", "All of Us", False)
         + chip("Trial cohorts", "SPRINT, ACCORD, WHI", False, "currently running") + "</span>"),
    ]


def aim_row(k, ic, t, s, cls, extra=""):
    return (f'<div class="aim {cls}"{extra}><div class="ic">{ic}</div><div class="num">{k}</div>'
            f'<div><div class="at">{esc(t)}</div><div class="as">{s if k == 4 else esc(s)}</div></div></div>')


def s_aims():
    sid = "s-aims"
    claim(SN[sid], "MIMIC-IV external validation done", "done", ROOT / "docs/v21/MIMIC_PAPER2.md", probe="7 cardiovascular trials", ref_src=ROOT / "docs/v21/MIMIC_PAPER2.md")
    st = {1: 1, 2: 3, 3: 4, 4: 5}  # click 2 = the representations graphic under aim 1 (aims_graphic); click 3 hides it and reveals aim 2
    rows = "".join(aim_row(k, ic, t, s, "fstep", f' data-step="{st[k]}"') for k, ic, t, s in aims_list())
    body = f"""<p class="goal">The goal of <b>LATENT-RCT</b> is to bring unstructured information into trial emulation.</p>
<div class="aims4">{rows}</div>{aims_graphic()}"""
    return sec(sid, "Aims", body, steps=6, cls="aimsl")


def aims_copy(hl):
    """deck3 (2026-10-14): a static copy of the slide 4 aims list (same layout, no graphic, no click reveal), aim hl highlighted and
    the other aims dimmed."""
    return '<div class="aims4 acopy">' + "".join(aim_row(k, ic, t, s, "ahl" if k == hl else "adim") for k, ic, t, s in aims_list()) + "</div>"


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
    # deck3 (2026-10-14): display labels, defined here once (as on slide 4): AI-ECG and AI-EHR
    C = [(ICON["ecg"], "+ AI-ECG", DEF_ECG.split(" ", 1)[1] + " → 32 PCs"), (ICON["ehr"], "+ AI-EHR", DEF_EHR.split(" ", 1)[1] + " → 64 PCs"),
         (ICON["ecg"] + ICON["ehr"], "+ AI-ECG + AI-EHR", "both"), (ICON["shuf"], "+ permuted placebo", "AI-ECG shuffled between patients")]
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
    """slide 8 (deck3 2026-10-14): a copy of the slide 4 aims list with aim 2 (covariate balance) highlighted, then, in one compact box,
    the balance endpoints and tests (the deck2 slide 8 wording, shortened); the held-out characteristics, the leakage map and the
    masking details stay on appendix A3 (s_apanel), linked bottom left."""
    sid = "s-meth2"
    sl = SN[sid]
    claim(sl, "held-out items", "54", PIPE, probe="54 non-coded items, leakage-corrected", ref_src=PIPE)
    claim(sl, "|SMD| threshold", "0.1", PIPE, probe="% of items with |SMD| < 0.1", ref_src=PIPE)
    claim(sl, "bootstrap CI over trials", "as stated", PIPE, probe="95% CI from 4,000 bootstrap resamples of trials", ref_src=PIPE)
    claim(sl, "exact sign-flip across trials", "as stated", PIPE, probe="exact sign-flip permutation across trials", ref_src=PIPE)
    claim(sl, "placebo = permuted ECG", "as stated", PIPE, probe="Permuted ECG (embeddings shuffled between patients within each trial; same dimension)", ref_src=PIPE)
    box = """<div class="mbx"><div><span class="mk">Endpoints</span><b>Primary:</b> relative reduction in mean |SMD| over the <b>54 held-out items</b> · <b>Secondary:</b> % of items with |SMD| &lt; 0.1</div>
<div><span class="mk">Tests</span>paired by trial · bootstrap CI · exact sign-flip · placebo (permuted AI-ECG)</div></div>"""
    return sec(sid, "Methods: covariate balancing", aims_copy(2) + box, links=more(SN["a-panel"]))


def s_methods_agree():
    """slide 10 (deck3 2026-10-14): the same aims copy with aim 3 (trial emulation and agreement with RCTs) highlighted, then the
    agreement methods in one compact box (the endpoint and tests already used by the deck and Figure 3; no new metrics)."""
    sid = "s-meth3"
    sl = SN[sid]
    claim(sl, "agreement metric |dlog HR| vs RCT", "as stated", PIPE, probe="| Metrics | |Δ log HR| vs RCT (paired, trials closer, sign-flip P)", ref_src=PIPE)
    claim(sl, "benchmark permutation: RCT results reassigned across trials", "as stated", PIPE,
          probe="Benchmark-permutation test (RCT results reassigned across trials", ref_src=PIPE)
    box = """<div class="mbx"><div><span class="mk">Endpoint</span>mean |Δ log HR| between the emulated and RCT hazard ratios (lower = closer)</div>
<div><span class="mk">Tests</span>paired by trial (exact sign-flip) · benchmark permutation (RCT results reassigned across trials)</div></div>"""
    return sec(sid, "Methods: agreement with RCTs", aims_copy(3) + box)


def s_methods_ext():
    """final touches (2026-10-15): the aims copy with aim 4 (external validation) highlighted, then its two endpoints: MIMIC-IV
    (the same pipeline in another health system) and the RCT rejection-sampling benchmark (pipeline.md section 8, Figure 5)."""
    sid = "s-meth4"
    sl = SN[sid]
    claim(sl, "RCT rejection sampling, share of the confounding gap closed", "as stated", PIPE,
          probe="primary metric = share of the confounding gap closed vs the oracle", ref_src=PIPE)
    box = """<div class="mbx"><div><span class="mk">MIMIC-IV</span>same pipeline in another health system: does the held-out balance gain and the agreement with the RCTs replicate?</div>
<div><span class="mk">Real trials</span>SPRINT, ACCORD, WHI: bias induced in the randomized arms by a withheld measurement; endpoint = % of bias removed</div></div>"""
    return sec(sid, "Methods: external validation", aims_copy(4) + box)


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
    for g, x in V["B"].items():
        js = BE.items("54") if g == "All 54" else V2.dom_items(g)
        for a in ("unmatched", "base", "ECG"):
            M = G1.block("main", "P5", a, True)[np.ix_(T, js)]
            ok = np.isfinite(M).any(1)
            claim(sl, f"Fig 2B {g} {a}", f"{x[a]:.3f}", FIG2V, ref=f"{np.nanmean(M[ok], 1).mean():.3f}", ref_how="explorer domain view (mean) on the cells")
    f2n_claims(sl)
    # deck2: no subtitle / source line; minimal title; panels revealed A + B, then C, then D. Slide 9 panel D job: D = the overall-balance
    # panel (no popup); the per-trial panel and its groupings popup are on A4, linked first under "More:"
    # deck3: manuscript-style heading; panel A (once revealed) opens Supplementary Figure 2 (fig2_panels); the plasmode is linked here
    return sec(sid, "Figure 2. Covariate balance", fig, links=more(SN["a-f2d"], SN["a-fw"], SN["a-fix"]))


def f2n_cells(T, rg, arm, ref=None):
    """slide 9 panel D, recomputed here from the version 1 cells (independent of the figure script): the explorer ladder level (mean
    over trials of each trial's mean |SMD| on its observed items, own masks) or, with ref = (rung, arm), the paired contrast vs ref on
    the items observed in both cells (pair_stats' formulae, across rungs): relative change in mean |SMD|, two-sided exact sign-flip P."""
    G1, js = CTX["G1"], BE.items("54")
    Ma = G1.block("main", rg, arm, True)[np.ix_(T, js)]
    if ref is None:
        ok = np.isfinite(Ma).any(1)
        assert ok.all()
        return float(np.nanmean(Ma[ok], 1).mean())
    Mb = G1.block("main", ref[0], ref[1], True)[np.ix_(T, js)]
    m = np.isnan(Ma) | np.isnan(Mb)
    ma, mb = np.nanmean(np.where(m, np.nan, Ma), 1), np.nanmean(np.where(m, np.nan, Mb), 1)
    dm = mb - ma
    rr = 100 * (1 - ma.mean() / mb.mean())
    return rr, min(1.0, 2 * min(BE.signflip_1s(dm), BE.signflip_1s(-dm)))


def f2n_claims(sl):
    """slide 9 panel D job: every value in the new panel D (7 means, 3 vs-hdPS contrasts with P) is a claim, shown from
    panelD_values.json and checked against f2n_cells on the cells; the displayed values are also gated against figure4.md."""
    assert F2N.exists() and F2NV.exists(), "run scripts/figures/make_slide9_panelD_overall.py first"
    V = json.load(open(F2NV))
    T = T_("s31")
    assert V["k_set"] == len(T) == 31
    got = {}
    for lab, rg, arm in F2N_ROWS:
        shown = f"{V['levels'][lab]:.3f}"
        claim(sl, f"Panel D mean |SMD| {lab}", shown, F2NV, ref=f"{f2n_cells(T, rg, arm):.3f}",
              ref_how="explorer ladder level on the version 1 cells (own masks)")
        got[lab] = shown
    for lab, rg, arm in F2N_ROWS[4:]:
        c = V["vs_hdPS"][lab]
        rr, p = f2n_cells(T, rg, arm, ref=("hdPS200", "base"))
        word = lambda x: "lower" if x > 0 else "higher"
        shown, ref = f"{abs(c['rr']):.1f}% {word(c['rr'])}", f"{abs(rr):.1f}% {word(rr)}"
        assert V["labels"][lab].startswith(f"{shown} than hdPS (P = {fp(c['p_m_two'])})"), V["labels"][lab]
        claim(sl, f"Panel D {lab} vs hdPS: relative change in mean |SMD|", shown, F2NV, ref=ref,
              ref_how="paired by trial on items observed in both cells (version 1 cells)")
        claim(sl, f"Panel D {lab} vs hdPS: P (two-sided sign-flip)", fp(c["p_m_two"]), F2NV, ref=fp(p), ref_how="exact two-sided sign-flip on the cells")
        got[f"vs {lab}"] = f"{shown}|{fp(c['p_m_two'])}"
    assert got == EXPECT_F2N, (got, EXPECT_F2N)


def F2FMT_P(p):
    """P as printed in the Figure 2 panels (make_figure2_latent.fmt_p; copied: importing the figure script resets matplotlib)."""
    return "P < .001" if p < 0.001 else f"P = {p:.3f}".replace("0.", ".") if p < 0.01 else f"P = {p:.2f}".replace("0.", ".")


def s_af2d():
    """appendix A4 (slide 9 panel D job): the per-trial panel D of Figure 2 (Figure 2D job's version, coloured by cardiac-physiology
    decision) with its groupings popup (moved unchanged from slide 9: click the panel or the hint), one summary line from the existing
    values (no new numbers) and a back-link to slide 9."""
    from PIL import Image
    sid = "a-f2d"
    sl = SN[sid]
    V = json.load(open(FIG2V))
    d = V["D"]
    r = ps(CTX["G1"], "main", "P5", "ECG", "base", "s31")
    claim(sl, "Fig 2D trials improved", f"{int(d['improved'])} of {int(d['k'])}", FIG2V, ref=f"{r['better']} of {r['k']}", ref_how="pair_stats on the cells")
    claim(sl, "Fig 2D mean change (points)", f"{d['mean']:+.1f}", FIG2V, ref=f"{r['dpts']:+.1f}", ref_how="pair_stats on the cells")
    claim(sl, "Fig 2D P", fp(d["p"]), FIG2V, ref=fp(r["p"]), ref_how="exact one-sided sign-flip on the cells")
    pshown = F2FMT_P(d["p"])  # as printed in the panel (make_figure2_latent.fmt_p)
    claim(sl, "Fig 2D P (as in the panel)", pshown, FIG2V, ref=F2FMT_P(r["p"]), ref_how="exact one-sided sign-flip on the cells")
    pops = fig2d_popup(sl, V)
    pim = Image.open(FIG2P / "figure2_covariate_balance_D.png").convert("RGB")
    disp_h = 488
    u, nb = uri(transp(pim).resize((round(pim.width * 2 * disp_h / pim.height), 2 * disp_h), Image.LANCZOS))
    CTX["a_f2d"] = dict(src_size=list(pim.size), disp_h=disp_h, bytes=nb)
    mean = f'{d["mean"]:+.1f}'.replace("-", "−")
    line = (f'{int(d["improved"])} of {int(d["k"])} trials improved; mean {mean} points in % of items with |SMD| &lt; 0.1; '
            f'{pshown} (exact one-sided sign-flip)')
    q = "19 of 31 trials improved; mean +3.3 points in % of items with |SMD| < 0.1; P = .02 (exact one-sided sign-flip)"  # queue file
    assert line.replace("&lt;", "<") == q, line
    claim(sl, "A4 summary line", q, FIG2V, probe=q, ref_src=ROOT / "docs/queue/slide9_panelD.md")
    body = (f'<p class="f2dl">{line}</p>'
            f'<div class="f2dbox" style="width:{disp_h * pim.width / pim.height:.0f}px;height:{disp_h}px">'
            f'<img class="f2d" data-pop="pop-f2d" alt="{esc("Per-trial covariate balance improvement (Figure 2 panel D). " + F2D_NOTE)}" src="{u}">'
            '<div class="f2hint" data-pop="pop-f2d">Click for other groupings ›</div></div>')
    return sec(sid, "Per-trial covariate balance improvement (PS-CVD5 + ECG vs PS-CVD5)", body, links=back("s-res2") + pops)


def fig2d_popup(sl, V):
    """Figure 2D job (docs/queue/figure2D.md): the panel D popup, one tab per descriptive grouping of the same per-trial values (PNGs
    from scripts/figures/make_figure2d_groupings.py). Every group count and mean shown in panel D or a tab is registered as a claim:
    the figure script's value (trial_dpct) vs build_balance_explorer.pair_stats on that group's trials, from the cells."""
    from PIL import Image
    G1, tr = CTX["G1"], CTX["trials"]
    T = T_("s31")
    full = {tr[i]["full"]: i for i in T}
    DG, PT = V["D_groups"], V["D_groups"]["popup_tabs"]
    card = [t for v in DG["cardiac_physiology"].values() for t in v]
    dec = PT["decision"]
    assert len(card) == 11 and set(card) <= set(full) and sorted(t for v in dec.values() for t in v) == sorted(full)
    grp = {"cardiac": [full[t] for t in card], "other": [i for i in T if tr[i]["full"] not in card], "all": list(T)}
    shown = {k: DG["summary"][k] for k in grp}
    for g in EXPECT_F2D["area"]:
        grp[("area", g)] = [i for i in T if tr[i]["area"] == g]
        shown[("area", g)] = PT["summary"]["area"][g]
    for g, ts in dec.items():
        grp[("decision", g)] = [full[t] for t in ts]
        shown[("decision", g)] = PT["summary"]["decision"][g]
    for g in ("yes", "no"):
        grp[("physiologic", g)] = [i for i in T if tr[i]["phys"] == (g == "yes")]
        shown[("physiologic", g)] = PT["summary"]["physiologic"][g]
    assert sum(len(grp[("area", g)]) for g in EXPECT_F2D["area"]) == 31
    for k, idx in grp.items():
        r = BE.pair_stats(G1, "main", "P5", "ECG", "base", sorted(idx), "54", True)
        a, n, m = shown[k]
        val = f"{a} of {n}|{m:+.1f}"
        exp = EXPECT_F2D[k] if isinstance(k, str) else EXPECT_F2D[k[0]][k[1]]
        assert val == exp, (k, val, exp)
        lab = k if isinstance(k, str) else f"{k[0]}: {k[1]}"
        claim(sl, f"Fig 2D group {lab}: improved; mean change (points)", val, FIG2V, ref=f"{r['better']} of {r['k']}|{r['dpts']:+.1f}",
              ref_how="pair_stats on the group's trials (cells)")
    cap = {0: "Panel D as in Figure 2: trials coloured by type of treatment decision (cardiac-physiology = rhythm control, HF / RAAS drug choice).",
           1: "Clustered by clinical area, sorted within each area; dashed line = group mean.",
           2: "Clustered by type of treatment decision (6 groups), sorted within each group; dashed line = group mean.",
           3: "Coloured by the blind physiologic trial label (docs/v21/TRIAL_LABELS.json; two blind LLM runs, clinician review pending)."}
    tabs, views = [], []
    for k, (fn, title) in enumerate(PT["tabs"]):
        im = Image.open(FIG2G / fn).convert("RGB")
        im = im.resize((1700, round(im.height * 1700 / im.width)), Image.LANCZOS) if im.width > 1700 else im
        b = io.BytesIO()
        im.save(b, "PNG", optimize=True)
        u = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
        tabs.append(f'<button type="button" class="f2tab{" on" if k == 0 else ""}" role="tab" aria-selected="{"true" if k == 0 else "false"}" data-tab="{k}">{esc(title)}</button>')
        views.append(f'<figure class="f2view" data-tab="{k}"{"" if k == 0 else " hidden"}><img alt="Figure 2D grouped by {esc(title.lower())}: per-trial change in % of items with |SMD| &lt; 0.1, PS-CVD5 + ECG vs PS-CVD5 (31 trials); descriptive grouping" src="{u}">'
                     f'<figcaption>{esc(cap[k])} <b>Descriptive grouping</b>: the same per-trial values in every tab; no tests of group differences.</figcaption></figure>')
    body = (f'<div class="f2tabs" role="tablist">{"".join(tabs)}</div>{"".join(views)}'
            '<p class="mp f2pn">PS-CVD5 + ECG vs PS-CVD5; change in % of the 54 leakage-corrected held-out items with |SMD| &lt; 0.1; the 31 analysed trials. '
            f'{esc(F2D_NOTE)}</p>')
    return popup("pop-f2d", "Figure 2D: other groupings of the same trials", body)


FIG2P = FIG2.parent / "panels"  # per-panel PNGs (same figure, same 300 dpi; legend hidden)
FIG2_STEP = {"A": 1, "B": 1, "C": 2, "D": 3}


# helpers for slides built from a figure's per-panel PNGs (Figure 2; Figure 3 job: lifted out of fig2_panels, unchanged)
def msd(A_, B_, y, x):
    h, w = B_.shape
    y0, x0, y1, x1 = max(0, y), max(0, x), min(A_.shape[0], y + h), min(A_.shape[1], x + w)
    if y1 - y0 < h * .85 or x1 - x0 < w * .85:
        return np.inf
    return ((A_[y0:y1, x0:x1] - B_[y0 - y:y1 - y, x0 - x:x1 - x]) ** 2).mean()


def uri(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode(), len(b.getvalue())


def transp(im):
    """colour-to-alpha against white: composited on white the image is unchanged, and white padding is fully transparent."""
    from PIL import Image
    a = np.asarray(im.convert("RGB")).astype(float) / 255
    al = (1 - a).max(2)
    col = np.where(al[..., None] > 0, (a - (1 - al[..., None])) / np.maximum(al[..., None], 1e-9), 0)
    return Image.fromarray(np.dstack([np.clip(col * 255 + .5, 0, 255), al * 255 + .5]).astype(np.uint8), "RGBA")


def locate(full, pim, K=8):
    """(mean squared difference, x, y) of a panel PNG in the full PNG: coarse search on 1/K-scale images, then a +-12 px refinement."""
    from PIL import Image
    W, H = full.size
    F = 255 - np.asarray(full.convert("L"), float)
    Fs = 255 - np.asarray(full.convert("L").resize((W // K, H // K), Image.BOX), float)
    P = 255 - np.asarray(pim.convert("L"), float)
    Ps = 255 - np.asarray(pim.convert("L").resize((pim.width // K, pim.height // K), Image.BOX), float)
    _, ys, xs = min((msd(Fs, Ps, y, x), y, x) for y in range(-6, Fs.shape[0]) for x in range(-6, Fs.shape[1]))
    m, y, x = min((msd(F, P, y, x), y, x) for y in range(ys * K - 12, ys * K + 13) for x in range(xs * K - 12, xs * K + 13))
    return m, x, y


def fig2_panels(disp_h=580):  # 560 before the Figure 2D job (the figure is now 5.85 in tall, 5.3 before)
    """Figure 2 rebuilt from its per-panel PNGs, laid out as in the full figure: each panel is located in the full PNG (coarse search
    on 1/8-scale images, then a +-12 px refinement at full resolution; the match is asserted), white made transparent so padded
    panel edges never hide a neighbour, and embedded at 2x the displayed size. The shared legend is cropped from the full figure's
    top band (above the panels) and shown from step 0."""
    from PIL import Image
    full = Image.open(FIG2).convert("RGB")
    W, H = full.size
    sc = 2 * disp_h / H

    pos, out, meta = {}, [], {}
    for L in "ABCD":
        pim = Image.open(FIG2P / f"figure2_covariate_balance_{L}.png").convert("RGB")
        m, x, y = locate(full, pim)
        assert m < 400, (L, m)  # sub-pixel edge differences only (A 7.6, B 28.6, C 127, D 195 on 2026-10-14)
        pos[L] = (x, y, pim.width, pim.height)
        u, nb = uri(transp(pim).resize((round(pim.width * sc), round(pim.height * sc)), Image.LANCZOS))
        meta[L] = dict(xy=[x, y], size=[pim.width, pim.height], msd=round(float(m), 2), bytes=nb)
        if L == "D":
            # slide 9 panel D job: the slot of Figure 2's panel D shows the overall-balance panel instead (same left / top / width; it
            # may extend below the old panel's bottom, within the figure box); no popup (the per-trial panel and its popup are on A4)
            nim = Image.open(F2N).convert("RGB")
            assert nim.width == pim.width and y + nim.height <= H, (nim.size, pim.size, y, H)
            u, nb = uri(transp(nim).resize((round(nim.width * sc), round(nim.height * sc)), Image.LANCZOS))
            meta[L] = dict(xy=[x, y], size=list(nim.size), replaced="slide9_panelD_overall.png (old panel D located: msd %.2f)" % m, bytes=nb)
            out.append(f'<img class="f2p build" data-step="{FIG2_STEP[L]}" alt="{esc(F2N_ALT)}" src="{u}" '
                       f'style="left:{100 * x / W:.3f}%;top:{100 * y / H:.3f}%;width:{100 * nim.width / W:.3f}%">')
            continue
        # deck3 (2026-10-14): panel A opens Supplementary Figure 2 (the covariate balance explorer); cursor / hover cue only
        so = ' data-sopen="S2" aria-label="Open Supplementary Figure 2"' if L == "A" else ""
        out.append(f'<img class="f2p build{" sopen" if so else ""}" data-step="{FIG2_STEP[L]}"{so} alt="{esc(f"Figure 2 panel {L}")}" src="{u}" '
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


def s_results3():
    """Figure 3 job (docs/queue/figure3.md): "Results: agreement with the RCTs (Figure 3)", directly after the balance explorer. Built
    from the per-panel PNGs of scripts/figures/make_figure3_latent.py, laid out as in the full figure; panels revealed A, B, C (one per
    click); minimal title, no subtitle or source line. Panel A's inset numbers (and every B / C value) are registered as claims, checked
    against figure3_values.json, docs/s31/S31_RESULTS.md and the log HRs (deck's embedded data for PS alone / + ECG; the cells for the
    CLMBR-T arms). CLMBR-T is a comparison arm only."""
    sid = "s-res3"
    sl = SN[sid]
    assert FIG3.exists() and FIG3V.exists(), "run scripts/figures/make_figure3_latent.py first"
    V = json.load(open(FIG3V))
    D, R = CTX["D"], CTX["g1"]["R"]
    T = T_("s31")
    assert len(T) == 31 and V["A"]["trials"] == 31
    ids = [D["trials"][i]["id"] for i in T]

    def cells(rg, a, m=None):
        """mean |dlog HR| vs RCT from the cells (main configuration, the s31 trials, or the subset m)."""
        x = R[(R.config == "main") & (R.rung == rg) & (R.arm == a)].set_index("trial").loc[ids]
        assert not x.failed.any()
        d = np.abs(x.loghr.to_numpy(float) - x.rb.to_numpy(float))
        return float(d[m].mean() if m is not None else d.mean())

    # panel A (static text on the slide): 0.232 -> 0.198; 20 of 31 trials closer
    a = V["A"]
    shown = f"{a['mean_absd_PS_CVD5']:.3f} → {a['mean_absd_PS_CVD5_ECG']:.3f}"
    assert a["inset"] == f"Mean |Δ log HR|: {shown} / {a['trials_closer']} of {a['trials']} trials closer"
    claim(sl, "Fig 3A mean |dlog HR| PS-CVD5 -> + ECG (31)", shown, FIG3V, probe=f"| \\|Δ log HR\\| vs RCT, PS-CVD5 → + ECG | {shown} ({a['trials_closer']}/{a['trials']} closer",
          ref_src=S31DOC)
    m = V2.agree_py(D, "v1", "main", "P5", "ECG", T)
    mb = V2.agree_py(D, "v1", "main", "P5", "base", T)
    claim(sl, "Fig 3A mean |dlog HR| PS-CVD5 -> + ECG (31): log HRs", shown, FIG3V, ref=f"{mb['absd']:.3f} → {m['absd']:.3f}",
          ref_how="recomputed from the deck's embedded log HRs (V2.agree_py)")
    claim(sl, "Fig 3A trials closer with + ECG", f"{a['trials_closer']} of {a['trials']}", FIG3V, ref=f"{m['closer']} of {m['kp']}",
          ref_how="recomputed from the deck's embedded log HRs (V2.agree_py)")
    # panel B (values in the image)
    lab = V["B_labels"]
    for rg in V["B"]:
        for arm in ("base", "ECG", "CLMBR", "ECG+CLMBR"):
            if arm in ("base", "ECG"):
                ref, how = f"{V2.agree_py(D, 'v1', 'main', rg, arm, T)['absd']:.3f}", "deck's embedded log HRs (V2.agree_py)"
            else:
                ref, how = f"{cells(rg, arm):.3f}", "log HRs of the version 1 cells"
            claim(sl, f"Fig 3B {lab[rg]} {arm} mean |dlog HR|", f"{V['B'][rg][arm]:.3f}", FIG3V, ref=ref, ref_how=how)
    # slide 11 panel C job: the old panel C (by emulation quality) and its claims are on A7 (s_af3q); the new panel C's claims here
    f3c_claims(sl, cells)
    # the new panel C must show the same PS-Demo + ECG / + CLMBR-T points as panel B (queue file: 0.207, 0.174)
    W3 = json.load(open(F3CV))
    for lab_, arm in (("Demo + ECG", "ECG"), ("Demo + CLMBR-T", "CLMBR")):
        assert f"{W3['levels'][lab_]:.3f}" == f"{V['B']['P1'][arm]:.3f}", (lab_, W3["levels"][lab_], V["B"]["P1"][arm])
    # deck3: manuscript-style heading; one click after panel C shows the Supplementary Figure 3 button (opens the emulation explorer)
    btn = '<button type="button" class="sbtn build" data-step="4" data-sopen="S3">Supplementary Figure 3.<br>Trial emulation</button>'
    return sec(sid, "Figure 3. Agreement with RCTs", fig3_panels() + btn, links=more(SN["a-f3q"]))


FIG3 = ROOT / "docs/paper/figures_latent/figure3_rct_agreement.png"  # scripts/figures/make_figure3_latent.py
FIG3V = A / "claude-fig3-20261014/figure3_values.json"  # its aggregate values (validated there)
FIG3_STEP = {"A": 1, "B": 2, "C": 3}
FIG3_ALT = {"A": "Figure 3 panel A: emulated vs RCT hazard ratios, PS-CVD5 and PS-CVD5 + ECG (31 trials).",
            "B": "Figure 3 panel B: agreement ladder, mean |Δ log HR| vs RCT across the PS ladder with + ECG, + CLMBR-T or both.",
            "C": "Figure 3 panel C (deck): agreement with the RCTs, mean |Δ log HR| vs RCT (31 trials): Unmatched; conventional PS (PS-CVD5, "
                 "hdPS, PS-Clinical); demographics + AI representations (Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T), labelled vs "
                 "PS-CVD5 and vs hdPS."}
FIG3_CAPTION = ("Figure 3. Agreement of emulated and RCT results (31 trials). A, Emulated vs RCT hazard ratios with PS-CVD5 and PS-CVD5 + ECG. "
                "B, Mean absolute difference from RCT log HRs across the PS ladder with the ECG, CLMBR-T or both added. C, Mean absolute "
                "difference from RCT log HRs with demographics + AI representations (Demo + ECG, Demo + CLMBR-T, Demo + ECG + CLMBR-T) vs "
                "conventional PS (PS-CVD5, hdPS, PS-Clinical) and unmatched; labels are paired differences vs PS-CVD5 and vs hdPS. Lower is "
                "closer to the RCT.")
# slide 11 panel C job (docs/queue/slide11_figure3.md): the new panel C (deck only; scripts/figures/make_slide11_panelC_agreement.py)
F3C = ROOT / "docs/paper/figures_latent/panels/deck/slide11_panelC_agreement.png"
F3CV = A / "claude-slide11c-20261014/panelC_values.json"  # its aggregate values (gated there against figure4.md and recomputed_f4.json)
F3C_ROWS = [("Unmatched", "P5", "unmatched"), ("PS-CVD5", "P5", "base"), ("hdPS", "hdPS200", "base"), ("PS-Clinical", "clinical_nolvef", "base"),
            ("Demo + ECG", "P1", "ECG"), ("Demo + CLMBR-T", "P1", "CLMBR"), ("Demo + ECG + CLMBR-T", "P1", "ECG+CLMBR")]
F3C_REFS = (("PS-CVD5", "P5", "base"), ("hdPS", "hdPS200", "base"))
# expected displayed values (figure4.md and the queue file, audited): mean |dlog HR|; paired difference (a - b) and two-sided P
EXPECT_F3C = {"Unmatched": "0.248", "PS-CVD5": "0.232", "hdPS": "0.182", "PS-Clinical": "0.171", "Demo + ECG": "0.207", "Demo + CLMBR-T": "0.174",
              "Demo + ECG + CLMBR-T": "0.164",
              "Demo + ECG vs PS-CVD5": "−0.026|P = .20", "Demo + CLMBR-T vs PS-CVD5": "−0.058|P = .055", "Demo + ECG + CLMBR-T vs PS-CVD5": "−0.068|P = .037",
              "Demo + ECG vs hdPS": "+0.025|P = .56", "Demo + CLMBR-T vs hdPS": "−0.008|P = .71", "Demo + ECG + CLMBR-T vs hdPS": "−0.018|P = .21"}
V18U = A / "claude-v18-embed-compare/results.csv"  # unmatched log HRs (rung "none", full cohort), as f4_numbers.py


def f3c_claims(sl, cells):
    """slide 11 panel C job: every value in the new panel C (7 means; 6 paired contrasts with their two-sided P) is a claim, shown from
    panelC_values.json and checked against an independent recomputation here: the version 1 cells' log HRs (cells(); the deck's own
    v1 grid with the PS-Clinical MI cells) and, for Unmatched, the v18 results' rung "none"; the contrasts are paired by trial with an
    exact two-sided sign-flip. The displayed values are also gated against figure4.md (EXPECT_F3C)."""
    assert F3C.exists() and F3CV.exists(), "run scripts/figures/make_slide11_panelC_agreement.py first"
    V = json.load(open(F3CV))
    D, R = CTX["D"], CTX["g1"]["R"]
    T = T_("s31")
    assert V["k_set"] == len(T) == 31
    ids = [D["trials"][i]["id"] for i in T]
    rb = np.array([D["trials"][i]["rb"] for i in T], float)

    def per(rg, arm):
        if arm == "unmatched":
            u = pd.read_csv(V18U)
            u = u[(u.half == "full") & (u.rung == "none")].set_index("trial").loc[ids]
            assert np.allclose(u.rb.to_numpy(float), rb, atol=1e-6)
            return np.abs(u.loghr.to_numpy(float) - rb)
        x = R[(R.config == "main") & (R.rung == rg) & (R.arm == arm)].set_index("trial").loc[ids]
        assert not x.failed.any() and np.allclose(x.rb.to_numpy(float), rb, atol=1e-6)
        return np.abs(x.loghr.to_numpy(float) - rb)

    dd = {lab: per(rg, arm) for lab, rg, arm in F3C_ROWS}
    got = {}
    for lab, rg, arm in F3C_ROWS:
        shown = f"{V['levels'][lab]:.3f}"
        if arm != "unmatched":
            assert abs(cells(rg, arm) - dd[lab].mean()) < 1e-6  # the Figure 3 claims' own helper agrees (cells' vs the deck's RCT log HRs)
        claim(sl, f"Fig 3C (deck) mean |dlog HR| {lab}", shown, F3CV, ref=f"{dd[lab].mean():.3f}",
              ref_how="log HRs of the version 1 cells (unmatched: v18 results, rung none) vs the deck's RCT log HRs")
        got[lab] = shown
    pfmt = lambda p: "P < .001" if p < 0.001 else "P = " + (f"{p:.3f}"[1:] if p < 0.1 else f"{p:.2f}"[1:])
    sgn = lambda x: f"{x:+.3f}".replace("-", "−")
    for lab, _, _ in F3C_ROWS[4:]:
        for b, _, _ in F3C_REFS:
            k = f"{lab} vs {b}"
            c = V["vs"][k]
            g = dd[b] - dd[lab]
            p = min(1.0, 2 * min(BE.signflip_1s(g), BE.signflip_1s(-g)))
            shown = f"{sgn(c['diff'])}|{pfmt(c['p_ag_two'])}"
            assert V["labels"][k] == f"{sgn(c['diff'])} ({pfmt(c['p_ag_two'])})", V["labels"][k]
            claim(sl, f"Fig 3C (deck) {k}: paired difference in mean |dlog HR|", sgn(c["diff"]), F3CV, ref=sgn(-g.mean()),
                  ref_how="paired by trial on the cells' log HRs")
            claim(sl, f"Fig 3C (deck) {k}: P (two-sided sign-flip)", pfmt(c["p_ag_two"]), F3CV, ref=pfmt(p), ref_how="exact two-sided sign-flip on the cells")
            got[k] = shown
    assert got == EXPECT_F3C, (got, EXPECT_F3C)


def fig3_panels(disp_h=580):
    """Figure 3 rebuilt from its per-panel PNGs, laid out as in the full figure (as fig2_panels; no shared legend); the caption (the
    speaker note; the deck has no notes) is the figure box's aria-label. Slide 11 panel C job: panels A and B as before; the slot under
    them shows the new full-width panel C (slide11_panelC_agreement.png: the figure's full width, bottom-aligned, below panel B); the
    figure box keeps its size."""
    from PIL import Image
    full = Image.open(FIG3).convert("RGB")
    W, H = full.size
    sc = 2 * disp_h / H
    pos, out, meta = {}, [], {}
    for L in "AB":
        pim = Image.open(FIG3.parent / "panels" / f"figure3_rct_agreement_{L}.png").convert("RGB")
        m, x, y = locate(full, pim)
        assert m < 400, (L, m)
        pos[L] = (x, y, pim.width, pim.height)
        u, nb = uri(transp(pim).resize((round(pim.width * sc), round(pim.height * sc)), Image.LANCZOS))
        meta[L] = dict(xy=[x, y], size=[pim.width, pim.height], msd=round(float(m), 2), bytes=nb)
        out.append(f'<img class="f3p build" data-step="{FIG3_STEP[L]}" alt="{esc(FIG3_ALT[L])}" src="{u}" '
                   f'style="left:{100 * x / W:.3f}%;top:{100 * y / H:.3f}%;width:{100 * pim.width / W:.3f}%">')
    assert pos["A"][0] < pos["B"][0]  # A | B on top
    nim = Image.open(F3C).convert("RGB")
    x, y = 0, H - nim.height
    assert nim.width == W and y >= max(p[1] + p[3] for p in pos.values()), (nim.size, W, H, pos)  # full width, below A and B
    u, nb = uri(transp(nim).resize((round(nim.width * sc), round(nim.height * sc)), Image.LANCZOS))
    meta["C"] = dict(xy=[x, y], size=list(nim.size), replaced="slide11_panelC_agreement.png (full width; the old panel C is on A7)", bytes=nb)
    out.append(f'<img class="f3p build" data-step="{FIG3_STEP["C"]}" alt="{esc(FIG3_ALT["C"])}" src="{u}" '
               f'style="left:{100 * x / W:.3f}%;top:{100 * y / H:.3f}%;width:{100 * nim.width / W:.3f}%">')
    CTX["fig3"] = dict(src_size=[W, H], disp_h=disp_h, panels=meta)
    return f'<div class="fig3box" role="img" aria-label="{esc(FIG3_CAPTION)}" style="width:{disp_h * W / H:.0f}px;height:{disp_h}px">{"".join(out)}</div>'


def s_af3q():
    """appendix A7 (slide 11 panel C job): "Agreement by emulation quality (PS-CVD5)", the former Figure 3 panel C (its PNG, unchanged)
    with its claims (moved from slide 11), one plain line of its values (figure3_values.json; no new numbers) and a back-link to
    slide 11."""
    from PIL import Image
    sid = "a-f3q"
    sl = SN[sid]
    V = json.load(open(FIG3V))
    D, R = CTX["D"], CTX["g1"]["R"]
    T = T_("s31")
    ids = [D["trials"][i]["id"] for i in T]

    def cells(rg, a, m):
        x = R[(R.config == "main") & (R.rung == rg) & (R.arm == a)].set_index("trial").loc[ids]
        assert not x.failed.any()
        return float(np.abs(x.loghr.to_numpy(float) - x.rb.to_numpy(float))[m].mean())

    tier = np.array([D["trials"][i]["tier"] for i in T])
    arms = ("base", "ECG", "CLMBR", "ECG+CLMBR")
    for k, tt in (("EG", ("Excellent", "Good")), ("MO", ("Moderate",))):  # moved unchanged from slide 11
        c = V["C"][k]
        msk = np.isin(tier, tt)
        claim(sl, f"Fig 3C {c['label']} trials", str(c["trials"]), FIG3V, ref=str(int(msk.sum())), ref_how="v19 tiers of the deck's trials")
        for arm in arms:
            claim(sl, f"Fig 3C {c['label']} {arm} mean |dlog HR|", f"{c[arm]:.3f}", FIG3V, ref=f"{cells('P5', arm, msk):.3f}", ref_how="log HRs of the version 1 cells")
    eg, mo = V["C"]["EG"], V["C"]["MO"]
    line = (f"Mean |Δ log HR| vs RCT with PS-CVD5: {eg['label']} ({eg['trials']}) {' / '.join(f'{eg[a]:.3f}' for a in arms)} vs "
            f"{mo['label']} ({mo['trials']}) {' / '.join(f'{mo[a]:.3f}' for a in arms)} (PS alone / + ECG / + CLMBR-T / + both)")
    q = ("Mean |Δ log HR| vs RCT with PS-CVD5: Excellent + Good (14) 0.230 / 0.176 / 0.149 / 0.152 vs Moderate (17) 0.235 / 0.217 / 0.185 / "
         "0.168 (PS alone / + ECG / + CLMBR-T / + both)")  # queue file
    assert line == q, line
    claim(sl, "A7 summary line", q, FIG3V, probe=q, ref_src=ROOT / "docs/queue/slide11_figure3.md")
    pim = Image.open(FIG3.parent / "panels" / "figure3_rct_agreement_C.png").convert("RGB")
    disp_h = 480
    u, nb = uri(transp(pim).resize((round(pim.width * 2 * disp_h / pim.height), 2 * disp_h), Image.LANCZOS))
    CTX["a_f3q"] = dict(src_size=list(pim.size), disp_h=disp_h, bytes=nb)
    body = (f'<p class="f3ql">{esc(line)}</p>'
            f'<img class="f3q" alt="{esc("Agreement by emulation quality (former Figure 3 panel C): mean |Δ log HR| vs RCT with PS-CVD5, PS alone, + ECG, + CLMBR-T, + CLMBR-T + ECG, by v19 tier (Excellent + Good; Moderate).")}" '
            f'src="{u}" style="width:{disp_h * pim.width / pim.height:.0f}px;height:{disp_h}px">')
    return sec(sid, "Agreement by emulation quality (PS-CVD5)", body, links=back("s-res3", SN["s-agq"]))  # deck3: A8 -> A9 (consecutive)


def s_agq():
    """appendix A9 (deck3 2026-10-14): the former main slide "Agreement with the RCTs by emulation quality" (the 2026-10-09 template's
    interactive view, unchanged apart from the display labels), after A8; back to slide 11, More: A1."""
    T = V2.TEMPLATE
    old = between(T, '<section class="slide" data-title="Agreement with the RCTs by emulation quality" id="s-agq">', "</section>\n", incl_b=True)
    body = between(old, '  <div class="panel"', "</section>")
    return f'<section class="slide app" id="s-agq" data-title="Agreement with the RCTs by emulation quality" data-app="{SN["s-agq"]}">\n{body}{back("s-res3", SN["a-qual"])}\n</section>\n', old


# deck3 (2026-10-14): the robustness slide (s_robust) is deleted, with its claims


def s_plasmode_methods():
    """final touches (2026-10-15): a simple visual of how the plasmode simulation works (design facts from the plasmode doc)."""
    sid = "s-plasm"
    claim(SN[sid], "plasmode cells and replicates", "107 / 50", V2.PLD, probe="107 analysed trial × confounder cells in 31 trials", ref_src=V2.PLD)
    steps = [("Real patients", ["real covariates,", "ECGs and follow-up"], "pts"),
             ("Hide a confounder C", ["LVEF · NT-proBNP", "BMI · eGFR"], "c"),
             ("Simulate treatment", ["assigned from C;", "true HR fixed at 0.80"], "rx"),
             ("Match without C", ["PS-CVD5", "vs PS-CVD5 + AI-ECG"], "ps"),
             ("Bias removed", ["% of C's bias", "removed vs unmatched"], "bar")]
    W, bw, gap, y0, bh = 1580, 270, 55, 20, 330
    g = [f'<svg viewBox="0 0 {W} 430" style="display:block;width:100%;height:auto;margin:34px auto 0">']
    for i, (t, sub, ic) in enumerate(steps):
        x = 6 + i * (bw + gap)
        cx = x + bw / 2
        hl = ic in ("c",)
        g.append(f'<rect x="{x}" y="{y0}" width="{bw}" height="{bh}" rx="12" fill="{"#fbe3e2" if hl else "#fff"}" stroke="{RED if hl else NAVY}" stroke-width="2"/>')
        g.append(f'<text x="{cx}" y="{y0 + 44}" text-anchor="middle" font-size="22" font-weight="700" fill="{NAVY}">{esc(t)}</text>')
        iy = y0 + 130
        if ic == "pts":
            for r in range(3):
                for c_ in range(4):
                    px, py = cx - 54 + c_ * 36, iy - 34 + r * 34
                    g.append(f'<circle cx="{px}" cy="{py - 8}" r="7" fill="{NAVY}"/><path d="M{px - 11} {py + 12} Q{px} {py - 6} {px + 11} {py + 12} Z" fill="{NAVY}"/>')
        elif ic == "c":
            g.append(f'<circle cx="{cx}" cy="{iy}" r="44" fill="#fff" stroke="{RED}" stroke-width="3" stroke-dasharray="7 5"/>'
                     f'<text x="{cx}" y="{iy + 15}" text-anchor="middle" font-size="44" font-weight="700" fill="{RED}">C</text>')
        elif ic == "rx":
            g.append(f'<text x="{cx - 50}" y="{iy + 6}" text-anchor="middle" font-size="30" font-weight="700" fill="{RED}">C</text>'
                     f'<line x1="{cx - 30}" y1="{iy - 4}" x2="{cx + 8}" y2="{iy - 30}" stroke="{NAVY}" stroke-width="2.5"/>'
                     f'<line x1="{cx - 30}" y1="{iy + 4}" x2="{cx + 8}" y2="{iy + 30}" stroke="{NAVY}" stroke-width="2.5"/>'
                     f'<rect x="{cx + 10}" y="{iy - 46}" width="78" height="30" rx="6" fill="{NAVY}"/><text x="{cx + 49}" y="{iy - 25}" text-anchor="middle" font-size="16" fill="#fff" font-weight="700">drug A</text>'
                     f'<rect x="{cx + 10}" y="{iy + 16}" width="78" height="30" rx="6" fill="#fff" stroke="{NAVY}" stroke-width="2"/><text x="{cx + 49}" y="{iy + 37}" text-anchor="middle" font-size="16" fill="{NAVY}" font-weight="700">drug B</text>')
        elif ic == "ps":
            for k in range(4):
                yy = iy - 42 + k * 28
                g.append(f'<circle cx="{cx - 46}" cy="{yy}" r="9" fill="{NAVY}"/><line x1="{cx - 34}" y1="{yy}" x2="{cx + 34}" y2="{yy}" stroke="#c9cbd6" stroke-width="2"/>'
                         f'<circle cx="{cx + 46}" cy="{yy}" r="9" fill="#fff" stroke="{NAVY}" stroke-width="2.5"/>')
            g.append(f'<text x="{cx}" y="{iy + 64}" text-anchor="middle" font-size="16" fill="{RED}" font-weight="700">C not in the PS</text>')
        else:
            base = iy + 52
            g.append(f'<line x1="{cx - 70}" y1="{base}" x2="{cx + 70}" y2="{base}" stroke="{NAVY}" stroke-width="2"/>'
                     f'<rect x="{cx - 52}" y="{base - 40}" width="40" height="40" fill="{NAVY}"/><rect x="{cx + 12}" y="{base - 66}" width="40" height="66" fill="{RED}"/>'
                     f'<text x="{cx - 32}" y="{base + 24}" text-anchor="middle" font-size="14" fill="{NAVY}">PS-CVD5</text><text x="{cx + 32}" y="{base + 24}" text-anchor="middle" font-size="14" fill="{RED}">+ AI-ECG</text>')
        for j, line_ in enumerate(sub):
            g.append(f'<text x="{cx}" y="{y0 + bh - 46 + j * 24}" text-anchor="middle" font-size="20" fill="#55576f">{esc(line_)}</text>')
        if i < len(steps) - 1:
            ax_ = x + bw + 6
            g.append(f'<path d="M{ax_} {y0 + bh / 2} L{ax_ + gap - 14} {y0 + bh / 2}" stroke="{NAVY}" stroke-width="2.5" fill="none"/>'
                     f'<path d="M{ax_ + gap - 18} {y0 + bh / 2 - 7} L{ax_ + gap - 10} {y0 + bh / 2} L{ax_ + gap - 18} {y0 + bh / 2 + 7}" stroke="{NAVY}" stroke-width="2.5" fill="none"/>')
    g.append(f'<text x="{W / 2}" y="{y0 + bh + 62}" text-anchor="middle" font-size="21" fill="#55576f">107 trial × C combinations, 50 simulated replicates each · oracle = PS that includes C</text>')
    g.append("</svg>")
    return sec(sid, "Plasmode simulation", "<!--norelabel-->" + "".join(g) + "<!--/norelabel-->")


def s_takehome():
    """final touches (2026-10-15): headlines only; every number is read from the s31 summaries / panel value files."""
    sid = "s-take"
    sl = SN[sid]
    lad = [(lab, stat_v1(sid, f"take-home {lab} + AI-ECG (31)", "s31", rg, "ECG")[0]) for rg, lab in
           [("P1", "PS-Demo"), ("P5", "PS-CVD5"), ("PS10", "PS-CVD10"), ("clinical_nolvef", "PS-Clinical"), ("hdPS200", "hdPS")]]
    D9, C11 = json.load(open(F2NV)), json.load(open(A / "claude-slide11c-20261014/panelC_values.json"))
    e_ = D9["vs_hdPS"]["Demo + CLMBR-T"]; b_ = D9["vs_hdPS"]["Demo + ECG + CLMBR-T"]
    claim(sl, "take-home Demo + AI-EHR vs hdPS", f"{e_['rr']:.1f}", F2NV, ref=f"{e_['rr']:.1f}", ref_how="json")
    claim(sl, "take-home Demo + AI-ECG + AI-EHR vs hdPS", f"{b_['rr']:.1f}", F2NV, ref=f"{b_['rr']:.1f}", ref_how="json")
    ag = C11["vs"]["Demo + ECG + CLMBR-T vs PS-CVD5"]
    a5, _ = agree_v1(sid, "take-home PS-CVD5 + AI-ECG agreement (31)", "s31", "P5")  # "0.232 → 0.198"
    PLc = pd.read_csv(V2.PLAS / "added_value_p5.csv")
    PLc = PLc[PLc.analysis == "null-corrected"].set_index(["conf", "contrast"])
    plas = float(PLc.loc[("all", "ECG over P5"), "added_pct_of_ref_bias"])
    claim(sl, "take-home plasmode AI-ECG over PS-CVD5", fx(plas), V2.PLAS / "added_value_p5.csv", ref=fx(plas), ref_how="csv")
    ladtxt = " · ".join(f"{lab} {fx(x['rr'])}%" for lab, x in lad)
    p2 = lambda p: f"P = {p:.3f}".replace("0.", ".") if p < 0.1 else f"P = {p:.2f}".replace("0.", ".")
    rows = [
        ("AI-ECG improves held-out balance when the PS is thin; the gain is smaller with richer PS",
         f"Reduction in held-out imbalance with + AI-ECG: {ladtxt}"),
        ("AI-EHR is as good as hdPS, and AI-ECG + AI-EHR is better",
         f"Demographics + AI-EHR: {e_['m_a']:.3f} vs hdPS {e_['m_b']:.3f} ({p2(e_['p_m_two'])}) · demographics + AI-ECG + AI-EHR: "
         f"{b_['rr']:.1f}% lower than hdPS ({p2(b_['p_m_two'])})"),
        ("Trial replication: AI representations bring hazard ratios closer to the RCTs",
         f"|Δ log HR| vs RCT: PS-CVD5 {ag['absd_b']:.3f} → demographics + AI-ECG + AI-EHR {ag['absd_a']:.3f} ({p2(ag['p_ag_two'])}) · "
         f"PS-CVD5 + AI-ECG {a5}"),
        ("Plasmode: AI-ECG removes part of a hidden confounder's bias",
         f"A further {fx(plas)}% of the bias that PS-CVD5 leaves, with the confounder in no PS"),
    ]
    body = '<div class="thl">' + "".join(f'<div class="th1"><div class="tn">{i + 1}</div><div><div class="tt">{esc(t)}</div>'
                                         f'<div class="ts2">{esc(sub)}</div></div></div>' for i, (t, sub) in enumerate(rows)) + "</div>"
    return sec(sid, "Take-home", body)


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


def s_afw(trials_old, Q):  # appendix A5 (A4 before the slide 9 panel D job)
    sid = "a-fw"
    n0 = len(V2.CL)
    h = V2.s_framework(trials_old, Q)
    cl_slide(n0, sid)
    h = one(h, "<p class=\"small\" style=\"margin-top:8px\">Analysed set = Excellent + Good + Moderate.",
            f"<p class=\"small\" style=\"margin-top:8px\"><b>Sensitivity analysis only</b> (primary: v19 tiers, {SN['a-qual']}). Analysed set = Excellent + Good + Moderate.")
    return retitle(h, sid, "Emulation-quality framework v2.0 (sensitivity)")


def s_afix(trials_old, EX, RR):  # appendix A6 (A5 before the slide 9 panel D job)
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
.xrefs{position:absolute;left:22px;bottom:19px;font-size:12.5px;color:var(--muted);z-index:4;max-width:1040px}
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
.thl{display:flex;flex-direction:column;gap:26px;margin-top:18px}.th1{display:flex;gap:22px;align-items:flex-start}.th1 .tn{flex:0 0 46px;height:46px;border-radius:50%;background:var(--navy);color:#fff;font-size:24px;font-weight:700;display:flex;align-items:center;justify-content:center}.th1 .tt{font-size:29px;font-weight:700;color:var(--navy);line-height:1.2}.th1 .ts2{font-size:19px;color:var(--muted);margin-top:6px}
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
/* Figure 2D job: the popup of other groupings of the per-trial panel D (tabs, one view at a time; on A4 since the slide 9 panel D job) */
.mbox .f2tabs{display:flex;gap:6px;margin:0 0 8px;flex-wrap:wrap}
.mbox .f2tab{border:2px solid var(--navy);background:#fff;color:var(--navy);font-weight:700;font-size:14px;line-height:1.2;font-family:inherit;padding:5px 12px;cursor:pointer}
.mbox .f2tab.on{background:var(--navy);color:#fff}
.mbox .f2tab:hover,.mbox .f2tab:focus{outline:2px solid var(--red);outline-offset:1px}
.mbox figure.f2view{margin:0;text-align:center}
.mbox figure.f2view[hidden]{display:none}
.mbox figure.f2view img{height:418px;width:auto;max-width:100%;display:block;margin:0 auto}
.mbox figure.f2view figcaption{font-size:13.5px;line-height:1.3;color:var(--navy);margin:4px 0 0;text-align:left}
.mbox p.f2pn{font-size:12.5px;color:var(--muted);margin-top:4px}
/* Figure 3 job: the agreement slide (Figure 3), built from its per-panel PNGs */
/* slide 9 panel D job: appendix A4, the per-trial panel D (opens the groupings popup) */
.f2dl{font-size:19px;margin:0 0 8px;color:var(--navy);text-align:center}
.f2dbox{position:relative;margin:0 auto}
.f2dbox img.f2d{display:block;width:100%;height:100%;cursor:pointer}
.f2dbox img.f2d:focus{outline:2px solid var(--red);outline-offset:2px}
.f2dbox .f2hint{position:absolute;right:0;bottom:-22px;font-size:15px;font-weight:700;color:var(--red);cursor:pointer;white-space:nowrap;border-bottom:1px dotted var(--red);line-height:1.2}
.fig3box{position:relative;margin:-10px auto 0}
.fig3box img.f3p{position:absolute;display:block;height:auto}
.fig3box img.f3p.build{transition:opacity .45s}
/* slide 11 panel C job: appendix A7, the former Figure 3 panel C (agreement by emulation quality) */
.f3ql{font-size:19px;margin:0 0 10px;color:var(--navy);text-align:center}
img.f3q{display:block;margin:0 auto}
/* deck3 (2026-10-14): aims copies (slides 8 and 10), the methods box, the supplementary-figure links and the simplified explorers */
.aims4.acopy .aim.adim{opacity:.25}
.aims4.acopy .aim.ahl{border-color:var(--red);background:#fbeceb}
.mbx{margin-top:18px;border:2px solid var(--navy);background:var(--band);padding:10px 18px;display:grid;gap:8px}
.mbx div{font-size:17.5px;line-height:1.35;color:var(--navy)}
.mbx .mk{display:inline-block;width:112px;font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:var(--red)}
.fig2box img.sopen{cursor:pointer}
.fig2box img.sopen:hover,.fig2box img.sopen:focus{outline:2px solid var(--red);outline-offset:3px}
.sbtn{position:absolute;right:0;bottom:0;width:236px;text-align:center;line-height:1.3;border:2px solid var(--navy);background:#fff;color:var(--navy);font-family:inherit;font-weight:700;font-size:14.5px;padding:6px 8px;cursor:pointer}
.sbtn:hover,.sbtn:focus{background:var(--navy);color:#fff}
.panel.sx{grid-template-columns:180px 1fr 270px}
.panel.sx .ctrl label.h{font-size:12px;margin:12px 0 4px}
.panel.sx .ctrl select{font-size:14px;padding:3px 4px}
.panel.sx .side{padding-left:14px}
.sxh{font-size:13px;font-weight:700;color:var(--navy);margin:6px 0 14px;line-height:1.3}
.sxn{margin:0 0 16px}
.sxl{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:var(--navy)}
.sxv{font-size:22px;font-weight:700;color:var(--navy);margin-top:2px;white-space:nowrap}
.sxs{font-size:12px;color:var(--muted)}
.xrefs a.sback{font-size:14px;font-weight:700}
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
/* Figure 2D job: the panel D popup's tabs (one view at a time; it opens on the first tab) */
function f2dInit() {
  const m = document.getElementById("pop-f2d"); if (!m) return;
  const set = k => { m.querySelectorAll(".f2tab").forEach(b => { const on = +b.dataset.tab === k; b.classList.toggle("on", on); b.setAttribute("aria-selected", on ? "true" : "false"); });
    m.querySelectorAll(".f2view").forEach(v => { v.hidden = +v.dataset.tab !== k; }); };
  m.querySelectorAll(".f2tab").forEach(b => b.addEventListener("click", e => { e.preventDefault(); set(+b.dataset.tab); }));
  document.querySelectorAll('[data-pop="pop-f2d"]').forEach(el => { el.addEventListener("click", () => set(0)); el.addEventListener("keydown", e => { if (e.key === "Enter") set(0); }); });
}
"""

def s_supp():
    """deck3 (2026-10-14): Supplementary Figures 2 and 3, the simplified explorers (SX_JS); out of the main sequence, reached from
    slide 9's panel A / slide 11's button, with "Back to Figure 2 / 3" (also Esc and the browser back button)."""
    out = []
    for sid, lab, title, frm in SUPPF:
        k = "s2" if sid == "s-bal" else "s3"
        fig = "Figure 2" if k == "s2" else "Figure 3"
        out.append(f'<section class="slide app supp" id="{sid}" data-title="{esc(title)}" data-app="{lab}" data-supp="1" data-back="{frm}">\n'
                   f'  <div class="panel sx">\n    <div class="ctrl" id="{k}-ctrl"></div>\n    <div class="chart"><svg id="{k}-svg" viewBox="0 0 760 590"></svg></div>\n'
                   f'    <div class="side" id="{k}-sum"></div>\n  </div>\n'
                   f'<div class="xrefs"><a class="sback" href="#{SN[frm]}" data-goto="{frm}">← Back to {fig}</a></div>\n</section>\n')
    return "".join(out)


SX_JS = r"""
/* ===== deck3 (2026-10-14): Supplementary Figures 2 and 3, the simplified explorers. Fixed: version 1 cohorts, the 31 trials, main
   configuration (1:1, caliper 0.2), 54 leakage-corrected held-out items, love plot / HR forest. Controls: PS and added representation.
   Statistics: the balance explorer's paired() (bootstrap CI, exact sign-flip) and the emulation explorer's agree() / closer(). ===== */
const SXPS = [["P5", "PS-CVD5"], ["PS10", "PS-CVD10"], ["clinical_nolvef", "PS-Clinical"], ["hdPS200", "hdPS"]];
const SXREP = [["ECG", "+ AI-ECG"], ["CLMBR", "+ AI-EHR"], ["ECG+CLMBR", "+ AI-ECG + AI-EHR"]];
const SXST = {unmatched: ["#8a8d99", "x", false], base: [NAVY, "circle", true], ECG: [RED, "circle", false], CLMBR: ["#2a7f62", "square", true],
  "ECG+CLMBR": ["#7b4fa0", "diamond", false]};
const SXG = {"Vitals & core labs": "Vitals, labs", "Other labs": "Other labs", "Echo: LV structure": "LV structure", "Echo: LV function": "LV func.",
  "Echo: diastolic / LA": "Diastolic", "Echo: RV / pulmonary": "RV / PA", "Echo: valves / aorta": "Valves"};
const umin = s => String(s).replace(/-/g, "−");
const sxP = p => !Number.isFinite(p) ? "–" : p < 0.001 ? "<.001" : p < 0.1 ? p.toFixed(3).slice(1) : p < 0.995 ? p.toFixed(2).slice(1) : p.toFixed(2);  /* the static slides' P format */
const sxMk = (a, x, y, r, extra) => { const [c, mk, ho] = SXST[a]; return marker(mk, x, y, r, c, ho, extra || ""); };
function sxCtrl(k, upd) {
  $(`#${k}-ctrl`).innerHTML = `<label class="h">PS</label><select id="${k}-ps">${SXPS.map(([v, l]) => `<option value="${v}"${v === "P5" ? " selected" : ""}>${l}</option>`).join("")}</select>` +
    `<label class="h">Added representation</label><select id="${k}-rep">${SXREP.map(([v, l]) => `<option value="${v}"${v === "ECG" ? " selected" : ""}>${l}</option>`).join("")}</select>`;
  $(`#${k}-ps`).onchange = upd; $(`#${k}-rep`).onchange = upd;
  bindTips($(`#${k}-svg`)); upd();
}
function sxSel(k) { const p = $(`#${k}-ps`), r = $(`#${k}-rep`), lp = p.selectedOptions[0].text; return {rung: p.value, a: r.value, lb: lp, la: lp + " " + r.selectedOptions[0].text}; }
function sxLegend(items, x0, y) { let s = "", x = x0; for (const [mk, lab] of items) { s += `<g transform="translate(${x} ${y})">${mk}<text x="14" y="4" font-size="12.5" fill="${NAVY}">${esc(lab)}</text></g>`; x += 34 + lab.length * 7.4; } return s; }
const sxNum = (lab, val, sub) => `<div class="sxn"><div class="sxl">${lab}</div><div class="sxv">${val}</div>${sub ? `<div class="sxs">${sub}</div>` : ""}</div>`;
function s2Update() {
  const {rung, a, lb, la} = sxSel("s2"), T = trialSet("s31"), get = getter("54", true, "v1"), cfg = "main", arms = ["unmatched", "base", a];
  const its = itemsOf("54").filter(v => T.some(t => fin(get(cfg, rung, "base", t, v.j))));
  const rows = its.map(v => ({lab: v.lab, g: v.g, val: Object.fromEntries(arms.map(x => [x, median(T.map(t => get(cfg, rung, x, t, v.j)))]))}));
  const W = 760, H = 590, ml = 186, mr = 24, mt = 30, mb = 40, ph = H - mt - mb, rh = ph / rows.length;
  let xmax = 0.05; rows.forEach(r => arms.forEach(x => { if (fin(r.val[x])) xmax = Math.max(xmax, r.val[x]); }));
  xmax = Math.min(1.5, Math.ceil(xmax * 1.08 * 20) / 20);
  const xs = x => ml + Math.min(x, xmax) / xmax * (W - ml - mr);
  let s = sxLegend([[sxMk("unmatched", 4, 0, 4.5), "Unmatched"], [sxMk("base", 4, 0, 4.5), lb], [sxMk(a, 4, 0, 4.5), la]], ml, 12);
  let prev = null;
  rows.forEach((r, i) => {
    const y = mt + i * rh + rh / 2;
    if (i % 2 === 0) s += `<rect x="${ml}" y="${mt + i * rh}" width="${W - ml - mr}" height="${rh}" fill="#f5f5f8"/>`;
    if (r.g !== prev) { const gh = rh * rows.filter(q => q.g === r.g).length, gl = SXG[r.g] || r.g;
      s += `<line x1="4" x2="${W - mr}" y1="${mt + i * rh}" y2="${mt + i * rh}" stroke="#b9bbc8" stroke-width="0.8"/>`;
      const gf = Math.min(9.5, (gh - 6) / (gl.length * 0.66));  /* rotated label sized to fit its group (bold, ~0.66 em per character) */
      if (gf >= 6) s += `<text transform="translate(12 ${mt + i * rh + gh / 2}) rotate(-90)" font-size="${gf.toFixed(1)}" font-weight="700" text-anchor="middle" fill="${RED}">${esc(gl)}</text>`;
      prev = r.g; }
    const fs = Math.max(6, Math.min(11, rh * 0.85));
    s += `<text x="${ml - 5}" y="${y + fs * 0.35}" font-size="${fs}" text-anchor="end" fill="${NAVY}">${esc(r.lab)}</text>`;
    const v = arms.filter(x => fin(r.val[x])).map(x => r.val[x]);
    if (v.length > 1) s += `<line x1="${xs(Math.min(...v))}" x2="${xs(Math.max(...v))}" y1="${y}" y2="${y}" stroke="#c9cad4" stroke-width="1"/>`;
    const tt = `<b>${esc(r.lab)}</b><br>` + [["unmatched", "Unmatched"], ["base", lb], [a, la]].map(([x, l]) => `${esc(l)}: ${f3(r.val[x])}`).join("<br>");
    s += `<rect x="0" y="${mt + i * rh}" width="${W}" height="${rh}" fill="transparent" data-tip="${esc(tt)}"/>`;
    for (const x of arms) if (fin(r.val[x])) s += sxMk(x, xs(r.val[x]), y, Math.max(2.2, Math.min(4.6, rh * 0.38)), `pointer-events="none"`);
  });
  const y0 = mt + ph, stp = xmax > 0.6 ? 0.2 : xmax > 0.3 ? 0.1 : 0.05;
  s += `<line x1="${ml}" x2="${W - mr}" y1="${y0}" y2="${y0}" stroke="${NAVY}"/>`;
  for (let x = 0; x <= xmax + 1e-9; x += stp) s += `<line x1="${xs(x)}" x2="${xs(x)}" y1="${y0}" y2="${y0 + 4}" stroke="${NAVY}"/><text x="${xs(x)}" y="${y0 + 16}" font-size="11" text-anchor="middle" fill="${NAVY}">${x.toFixed(2)}</text>`;
  s += `<text x="${(ml + W - mr) / 2}" y="${y0 + 33}" font-size="12" text-anchor="middle" fill="${NAVY}">|SMD| (median across ${T.length} trials)</text>`;
  s += `<line x1="${xs(0.1)}" x2="${xs(0.1)}" y1="${mt}" y2="${y0}" stroke="${RED}" stroke-dasharray="4 3" stroke-width="1.2" pointer-events="none"/>`;
  $("#s2-svg").innerHTML = s;
  const x = paired(get, cfg, rung, a, "base", T, itemsOf("54").map(v => v.j), 0.1);
  $("#s2-sum").innerHTML = `<div class="sxh">${esc(lb)} → ${esc(la)}</div>` + sxNum("Mean |SMD|", `${f3(x.m_ref)} → ${f3(x.m_arm)}`) +
    sxNum("Relative reduction", `${umin(f1(x.rr))}% (${umin(f1(x.lo))} to ${umin(f1(x.hi))})`, "95% CI") + sxNum("P", sxP(x.p_m)) + sxNum("Trials improved", `${x.lower}/${x.k}`);
}
function s3Update() {
  const {rung, a, lb, la} = sxSel("s3"), coh = "v1", cfg = "main", arms = ["base", a];
  const T = [...trialSet("s31")].sort((p, q) => { const kp = [AREAS.indexOf(D.trials[p].area), D.trials[p].rb], kq = [AREAS.indexOf(D.trials[q].area), D.trials[q].rb];
    for (let i = 0; i < 2; i++) { if (kp[i] < kq[i]) return -1; if (kp[i] > kq[i]) return 1; } return 0; });
  const W = 760, H = 590, ml = 150, mr = 16, mt = 30, mb = 42, lo = Math.log(0.2), hi = Math.log(5), ph = H - mt - mb, rh = ph / T.length;
  const xs = l => ml + (Math.max(lo, Math.min(hi, l)) - lo) / (hi - lo) * (W - ml - mr);
  let s = sxLegend([[`<rect x="-2" y="-6" width="12" height="12" fill="#d9dae6"/>`, "RCT 95% CI"], [`<line x1="4" x2="4" y1="-6" y2="6" stroke="#000" stroke-width="2"/>`, "RCT HR"],
    [sxMk("base", 4, 0, 4.5), lb], [sxMk(a, 4, 0, 4.5), la]], ml, 12);
  for (const v of [0.25, 0.5, 1, 2, 4]) s += `<line x1="${xs(Math.log(v))}" x2="${xs(Math.log(v))}" y1="${mt}" y2="${mt + ph}" stroke="${v === 1 ? "#9a9cb0" : "#ececf1"}" stroke-width="${v === 1 ? 1.2 : 1}"/>`;
  T.forEach((t, i) => {
    const tr = D.trials[t], y0 = mt + i * rh, yc = y0 + rh / 2;
    if (i % 2 === 0) s += `<rect x="0" y="${y0}" width="${W}" height="${rh}" fill="#f7f7fa"/>`;
    s += `<rect x="${xs(tr.rb - 1.96 * tr.rs)}" y="${y0 + 1}" width="${xs(tr.rb + 1.96 * tr.rs) - xs(tr.rb - 1.96 * tr.rs)}" height="${Math.max(1, rh - 2)}" fill="#d9dae6"/>`;
    s += `<line x1="${xs(tr.rb)}" x2="${xs(tr.rb)}" y1="${y0 + 1}" y2="${y0 + rh - 1}" stroke="#000" stroke-width="2"/>`;
    const fs = Math.max(7, Math.min(12, rh * 0.75));
    s += `<text x="${ml - 6}" y="${yc + fs * 0.35}" font-size="${fs}" text-anchor="end" fill="${NAVY}">${esc(tr.name)}</text>`;
    let tt = `<b>${esc(tr.full)}</b><br>RCT: ${Math.exp(tr.rb).toFixed(2)} (${Math.exp(tr.rb - 1.96 * tr.rs).toFixed(2)}–${Math.exp(tr.rb + 1.96 * tr.rs).toFixed(2)})`;
    arms.forEach((x, k) => {
      const [l, se] = estOf(coh, cfg, rung, x, t), yy = yc + (k ? 3 : -3), col = SXST[x][0], lab = k ? la : lb;
      if (!fin(l)) { tt += `<br>${esc(lab)}: –`; return; }
      s += `<line x1="${xs(l - 1.96 * se)}" x2="${xs(l + 1.96 * se)}" y1="${yy}" y2="${yy}" stroke="${col}" stroke-width="1.3" pointer-events="none"/>`;
      s += sxMk(x, xs(l), yy, Math.max(2.2, Math.min(4.2, rh * 0.3)), `pointer-events="none"`);
      if (l < lo || l > hi) s += `<text x="${xs(l) + (l < lo ? -2 : 2)}" y="${yy + 3}" font-size="9" text-anchor="${l < lo ? "end" : "start"}" fill="${col}">${l < lo ? "◂" : "▸"}</text>`;
      tt += `<br>${esc(lab)}: ${Math.exp(l).toFixed(2)} (${Math.exp(l - 1.96 * se).toFixed(2)}–${Math.exp(l + 1.96 * se).toFixed(2)})`;
    });
    s += `<rect x="0" y="${y0}" width="${W}" height="${rh}" fill="transparent" data-tip="${esc(tt)}"/>`;
  });
  const yb = mt + ph;
  s += `<line x1="${ml}" x2="${W - mr}" y1="${yb}" y2="${yb}" stroke="${NAVY}"/>`;
  for (const v of [0.2, 0.25, 0.5, 1, 2, 4, 5]) s += `<line x1="${xs(Math.log(v))}" x2="${xs(Math.log(v))}" y1="${yb}" y2="${yb + 4}" stroke="${NAVY}"/><text x="${xs(Math.log(v))}" y="${yb + 16}" font-size="11" text-anchor="middle" fill="${NAVY}">${v}</text>`;
  s += `<text x="${(ml + W - mr) / 2}" y="${yb + 33}" font-size="12" text-anchor="middle" fill="${NAVY}">Hazard ratio (log scale)</text>`;
  $("#s3-svg").innerHTML = s;
  const mb_ = agree(coh, cfg, rung, "base", T), ma = agree(coh, cfg, rung, a, T), c = closer(coh, cfg, rung, a, T);
  $("#s3-sum").innerHTML = `<div class="sxh">${esc(lb)} → ${esc(la)}</div>` + sxNum("Mean |Δ log HR| vs RCT", `${f3(mb_.gap)} → ${f3(ma.gap)}`) +
    sxNum("Trials closer", `${c.closer}/${c.k}`) + sxNum("Sign-flip P", sxP(c.p)) + sxNum("Benchmark-permutation P", sxP(c.perm));
}
function s2Init() { sxCtrl("s2", s2Update); }
function s3Init() { sxCtrl("s3", s3Update); }
/* supplementary-figure navigation: opened from slide 9's panel A / slide 11's button (pushes a history entry, so the browser back button
   returns); "Back to Figure N", Esc or the back button return to that slide with all its panels shown */
function suppOpen(key) { const j = indexOf(key); if (j < 0) return; history.pushState({supp: key}, "", "#" + label(j)); show(j); }
function suppBack() { const sl = slides[cur]; if (history.state && history.state.supp === sl.dataset.app) history.back(); else show(indexOf(sl.dataset.back), true); }
function suppInit() {
  document.querySelectorAll("[data-sopen]").forEach(el => {
    if (el.tagName !== "BUTTON") { el.setAttribute("tabindex", "0"); el.setAttribute("role", "button"); }
    const go = e => { e.preventDefault(); e.stopPropagation(); suppOpen(el.dataset.sopen); };
    el.addEventListener("click", go); el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") go(e); });
  });
  document.querySelectorAll("a.sback").forEach(a => a.addEventListener("click", e => { e.preventDefault(); e.stopPropagation(); suppBack(); }));
  addEventListener("popstate", () => { const j = fromHash(); if (j !== cur) show(j, !!slides[cur].dataset.supp && !slides[j].dataset.supp); });
  addEventListener("keydown", e => { if (e.key === "Escape" && !POP && slides[cur].dataset.supp) { e.preventDefault(); suppBack(); } });
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
  sl.insertAdjacentHTML("afterbegin", `<div class="ttl">${sl.dataset.app && !sl.dataset.supp ? sl.dataset.app + " · " : ""}${sl.dataset.title}</div><div class="rule top"></div><div class="num">${label(i)}</div>` +
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
/* deck3: the supplementary figures (data-supp) are outside the arrow-key sequence: it skips them, and on them the arrows do nothing
   (leave with Back, Esc or the browser back button) */
const seqStep = (i, d) => { while (i >= 0 && i < slides.length && slides[i].dataset.supp) i += d; return i; };
function next() { if (POP) { popClose(); return; } if (slides[cur].dataset.supp) return; if (step < nSteps(slides[cur])) { step++; applyBuild(); } else { const j = seqStep(cur + 1, 1); if (j < slides.length) show(j); } }
function prev() { if (POP) { popClose(); return; } if (slides[cur].dataset.supp) return; if (step > 0) { step--; applyBuild(); } else { const j = seqStep(cur - 1, -1); if (j >= 0) show(j, true); } }
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
    # deck3 (2026-10-14): display labels; the + AI-EHR arms (Supplementary Figures 2 and 3); the full explorer's controls, views and
    # summary are no longer used (the simplified explorers SX_JS replace them), so its code from the controls section on is dropped
    P += [('  ECG: {lab: "+ ECG", col: RED, mk: "circle"},', '  ECG: {lab: "+ AI-ECG", col: RED, mk: "circle"},'),
          ('  shufECG: {lab: "+ permuted ECG", col: "#d69a00", mk: "tri", hollow: true}\n};',
           '  shufECG: {lab: "+ permuted AI-ECG", col: "#d69a00", mk: "tri", hollow: true},\n  CLMBR: {lab: "+ AI-EHR", col: "#2a7f62", mk: "square", hollow: true},\n'
           '  "ECG+CLMBR": {lab: "+ AI-ECG + AI-EHR", col: "#7b4fa0", mk: "diamond"}\n};'),
          ('const SL = {unmatched: "Unmatched", base: "PS alone", ECG: "+ ECG", shufECG: "+ perm. ECG"};',
           'const SL = {unmatched: "Unmatched", base: "PS alone", ECG: "+ AI-ECG", shufECG: "+ perm. AI-ECG", CLMBR: "+ AI-EHR", "ECG+CLMBR": "+ AI-ECG + AI-EHR"};')]
    for a, b in P:
        js = one(js, a, b)
    i = js.index("/* =========================================================\n   controls")
    return js[:i]


def build_template(T1001, deck1001, D):
    T = V2.TEMPLATE
    h = T
    h = one(h, "<title>TRACE-ECG | CarDS Lab update | October 9, 2026</title>", "<title>LATENT-RCT | CarDS Lab | 15 October 2026</title>")
    h = one(h, "</style>", intro_css(T1001, deck1001) + EXTRA_CSS + "</style>")
    # deck3 (2026-10-14): the template's explorer sections go (the simplified Supplementary Figures 2 and 3 replace the balance and
    # emulation explorers, s_supp; agreement by quality is appendix A9, s_agq); every slide is placed through __STATIC1__
    h = one(h, between(h, '<section class="slide" data-title="Results 1: covariate balance explorer', "</section>\n", incl_b=True), "")
    h = one(h, between(h, '<section class="slide" data-title="Results 3: trial emulation explorer', "</section>\n", incl_b=True), "")
    h = one(h, s_agq()[1], "")
    h = one(h, between(h, "function emuInit() {", "function agqInit() {"), "")
    h = one(h, 'const TSRC = {tier: "Framework v2.0, rescored (spec-v2 cohorts)", tq1: "Framework v2.0, version 1 cohorts", t19: "v19 tiers (paper 1)"};',
            'const TSRC = {t19: "v19 tiers (paper 1; primary)", tv2: "Framework v2.0, rescored on spec-v2 cohorts (sensitivity)", tq1: "Framework v2.0, version 1 cohorts (sensitivity)"};')
    h = one(h, 'const cohOpt = `<option value="v2" selected>Spec-v2 fixed cohorts (primary)</option><option value="v1">Version 1 cohorts (as built)</option>`;',
            'const cohOpt = `<option value="v1" selected>Version 1 cohorts (primary)</option><option value="v2">Spec-v2 fixed cohorts (sensitivity)</option>`;')
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
    h = h[:i] + intro_js(T1001, deck1001) + QV_JS + POP_JS + NAV_JS + SX_JS + h[j:]
    h = one(h, '$("#nav-next").onclick = next;\n',
            '$("#nav-next").onclick = next;\n/* a click on a slide with builds (outside any control, link or popup) reveals the next step (2026-10-01 deck) */\n'
            '$("#stage").addEventListener("click", e => { if (!POP && nSteps(slides[cur]) && !e.target.closest("select,input,label,button,a,.ctrl,.side,.modal,[data-pop],[data-sopen]")) next(); });\n')
    h = one(h, "init(); emuInit(); agqInit(); fit();\nshow((parseInt(location.hash.slice(1), 10) || 1) - 1);",
            "drawIntro(); qvInit(); s2Init(); s3Init(); agqInit(); linkInit(); popInit(); f2dInit(); suppInit(); fit();\nshow(fromHash());")
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
    for rg in SX_RUNGS:  # deck3: every state of Supplementary Figure 2 (version 1, main, the 31 trials, 54 leakage-corrected items)
        for a in ("ECG",) + SX_ARMS:
            add("computed (pair_stats)", "v1", "main", rg, a, "base", "s31", "54", True, {},
                tag="S2 default (8.7% (4.2 to 13.5), 20/31)" if (rg, a) == ("P5", "ECG") else "S2")
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
    T = BE.trial_set(D["trials"], "s31")
    for rg in SX_RUNGS:  # deck3: every state of Supplementary Figure 3 (version 1, main, the 31 trials), from the deck's log HRs
        for a in ("ECG",) + SX_ARMS:
            E = D["EST"]["v1"]["main"][rg]
            TT = [t for t in T if E[a][t] is not None and E["base"][t] is not None]
            bs = V2.bshuf_py(np.array([E[a][t][0] for t in TT]), np.array([E["base"][t][0] for t in TT]), np.array([D["trials"][t]["rb"] for t in TT]))
            out.append(dict(coh="v1", cfg="main", rung=rg, arm=a, trials="s31", tag="S3", py=V2.agree_py(D, "v1", "main", rg, a, T),
                            py_base=V2.agree_py(D, "v1", "main", rg, "base", T), py_bshuf=bs))
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
    add_rep_arms(D, g1)  # deck3: + AI-EHR, + AI-ECG + AI-EHR (version 1, main configuration) for Supplementary Figures 2 and 3
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
    # deck3: the added arms, decoded from the embedded integers / log HRs, equal Figure 2C and Figure 3B (display precision)
    F2V, F3V = json.load(open(FIG2V)), json.load(open(FIG3V))
    for rg in SX_RUNGS:
        for a in ("ECG",) + SX_ARMS:
            re_, rf = ps(CTX["E1"], "main", rg, a, "base", "s31"), ps(CTX["G1"], "main", rg, a, "base", "s31")
            assert f"{re_['rr']:.1f}|{re_['lo']:.1f}|{re_['hi']:.1f}|{re_['lower']}|{fp(re_['p_m'])}" == f"{rf['rr']:.1f}|{rf['lo']:.1f}|{rf['hi']:.1f}|{rf['lower']}|{fp(rf['p_m'])}", (rg, a)
            assert f"{re_['rr']:.1f}" == f"{F2V['C'][rg]['rr_' + a][0]:.1f}", (rg, a, re_["rr"])
            assert f"{V2.agree_py(D, 'v1', 'main', rg, a, T_('s31'))['absd']:.3f}" == f"{F3V['B'][rg][a]:.3f}", (rg, a)
    EX = load_ex()
    RR = pd.read_csv(V2.RRS)
    T1001, deck1001 = L1.TEMPLATE, DECK1001.read_text()
    # deck3 (2026-10-14): main slides, then the supplementary figures, then the appendix, all through __STATIC1__; display labels
    # (relabel) applied to every slide's markup (the 10-01 Background / Problem slides have no representation labels)
    n0 = len(V2.CL)
    plas = V2.s_plasmode()
    mimic = V2.s_mimic()
    for c in V2.CL[n0:]:  # plasmode / MIMIC claims carry V2's slide numbers 14 / 15
        assert c["slide"] in (14, 15), c
        c["slide"] = SN["s-plas"] if c["slide"] == 14 else SN["s-mimic"]
    slides = [intro_markup(T1001, deck1001), s_aims(), s_pipe(), s_methods_design(), s_methods_panel(), s_results2(),
              s_methods_agree(), s_results3(), s_methods_ext(), retitle(mimic, "s-mimic", "External replication: MIMIC-IV (PS-CVD5 analog ± ECG)"),
              s_plasmode_methods(), retitle(plas, "s-plas", "Plasmode simulation: results"), s_takehome(), s_supp(), s_a2(), s_a3(), s_apanel(), s_af2d(),
              s_afw(trials_old, Q), s_afix(trials_old, EX, RR), s_af3q(), s_agq()[0]]
    h = build_template(T1001, deck1001, D)
    h = (h.replace("__TITLE__", s_title()).replace("__STATIC1__", "".join(relabel(x) for x in slides)).replace("__STATIC2__", "")
         .replace("__STATIC3__", "").replace("__STATIC4__", "")
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
    assert ids == MAIN + [s for s, _, _, _ in SUPPF] + [s for s, _, _, _ in APP], ids
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
    meta = dict(mi=mi, fig2=CTX.get("fig2"), fig3=CTX.get("fig3"), table1_diffs=CTX.get("table1_diffs"), slides=[(SN[s], t) for s, t in titles])
    json.dump(meta, open(SCR / "build_meta.json", "w"), indent=1, default=str)
    combos = balance_combos(D, g1, g2)
    json.dump(combos, open(SCR / "balance_combos.json", "w"), indent=0)
    json.dump(emu_refs(D), open(SCR / "emu_refs.json", "w"), indent=0)
    print(f"balance combos: {len(combos)}; table1 differences paper.md vs table1_picot.md: {len(CTX.get('table1_diffs') or [])}")


if __name__ == "__main__":
    main()
