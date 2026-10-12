#!/usr/bin/env python
"""Build the CarDS Lab TRACE-ECG lab-meeting deck (2026-10-15): docs/presentation/ecg_tte_lab_2026_10_15.html.

Structure:
  1      the 2026-10-09 title slide, date line changed to "Lab meeting, Thursday 15 October 2026";
  2-6    slides 1-5 of the 2026-10-01 deck (Background; Problem; AI-ECG; Aims and hypotheses; Study design: trials), markup, CSS and
         schematic JS copied from scripts/build_lab_deck.py (not modified). One edit: the slide-5 line that pointed to the old
         design-only quality slides now reads "Emulation quality: framework v2.0 (next slides)."
  7-22   slides 2-17 of the 2026-10-09 deck, unchanged (regenerated with scripts/build_lab_deck_v2.py, not modified, and checked
         byte-identical to the committed docs/presentation/ecg_tte_lab_2026_10_09.html before splicing).

How the 10-01 slides keep their look inside the 10-09 page: their sections carry class "s1001"; the 10-01 stylesheet is copied with
every rule scoped to "section.s1001" (page-level rules such as html/body/#stage/#nav are left to the 10-09 sheet, which has the same
values); the 10-01 header chrome (title bar, rules, number, footer, logo) is identical to 10-09's, minus the red "Provisional" line,
which is not added to these five slides (it was not on the 10-01 deck). The schematics are drawn by the 10-01 drawStatic code (box,
arrow, ecgPath and the first five drawings), run inside a closure whose D holds only the trial names, areas and v19 tiers, taken from
the 10-09 deck's embedded trials (asserted equal to the 10-01 deck's). The 10-01 click-to-build behaviour (click on a slide with
builds reveals the next step) is added; the 10-09 slides have no builds, so nothing changes for them. Slide numbers and the
"n / N" counter are computed at load time, so slides 7-22 renumber automatically.

No new data are embedded: the page's data block is the 10-09 deck's (aggregates only).

Usage (tte-analysis env):
  python scripts/build_lab_deck_1015.py      build the HTML; write validation inputs to audits/claude-lab-deck-1015
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_lab_deck as L1  # noqa: E402
import build_lab_deck_v2 as V2  # noqa: E402

OUT = ROOT / "docs/presentation/ecg_tte_lab_2026_10_15.html"
DECK1001 = ROOT / "docs/presentation/ecg_tte_lab_2026_10_01.html"
DECK1009 = V2.OUT
SCR = V2.A / "claude-lab-deck-1015"
SCOPE = "section.s1001"
QUAL_OLD = '<p id="qual-count">Emulation quality (design items only): see next slides.</p>'
QUAL_NEW = '<p id="qual-count">Emulation quality: framework v2.0 (next slides).</p>'


def one(s, a, b):
    """replace exactly one occurrence."""
    assert s.count(a) == 1, (s.count(a), a[:120])
    return s.replace(a, b)


def between(s, a, b, incl_b=False):
    i = s.index(a)
    j = s.index(b, i)
    return s[i: j + (len(b) if incl_b else 0)]


# ================================================================ the 2026-10-09 deck (regenerated, as scripts/build_lab_deck_v2.main)
def build_1009():
    g = V2.BE.load_grid()
    g2 = V2.BE.load_grid_v2(g)
    trials, Q = V2.trials_deck(g, g2)
    D = V2.build_data(g, g2, trials)
    V2.GRID2.update(grid=V2.BE.Grid(g2["G"], g2["U"], g2["ex"]), D=D)
    MC, VC = V2.get_contrasts()
    IM = pd.read_csv(V2.IMPACT)
    DM = pd.read_csv(V2.MISUM / "domains.csv")
    EX = pd.read_csv(V2.EXCL, dtype={"pct_removed_v2": str})
    EX["pct_removed_v2"] = [float(v[1:]) / 2 if v.startswith("<") else float(v) for v in EX.pct_removed_v2]
    RR = pd.read_csv(V2.RRS)
    static = [V2.s_changes(trials, Q, MC, VC, EX), V2.s_flow(trials, Q), V2.s_framework(trials, Q), V2.s_tiers(trials, Q),
              V2.s_fixes(trials, EX, RR), V2.s_methods_design(), V2.s_methods_panel()]
    html = (V2.TEMPLATE.replace("__TITLE__", V2.s_title()).replace("__STATIC1__", "".join(static))
            .replace("__STATIC2__", V2.s_results2(MC, VC, IM, DM)).replace("__STATIC3__", V2.s_robust(MC, VC, RR, IM))
            .replace("__STATIC4__", "".join([V2.s_plasmode(), V2.s_mimic(), V2.s_takehome(MC, IM), V2.s_decisions(Q)]))
            .replace("__EXPLORER_JS__", V2.explorer_js()).replace("__LOGO__", V2.logo_uri(None))
            .replace("__DATA__", json.dumps(D, separators=(",", ":"), allow_nan=False)))
    return html, D, g, g2


# ================================================================ the 2026-10-01 intro slides (from scripts/build_lab_deck.TEMPLATE)
def intro_markup(T, deck1001):
    m = between(T, "<!-- 2 -->", "<!-- 6b -->")
    assert m in deck1001  # the committed 10-01 deck has exactly this markup
    titles = re.findall(r'<section class="slide" data-title="([^"]+)">', m)
    assert titles == ["Background", "Problem", "AI-ECG", "Aims and hypotheses", "Study design: trials"], titles
    m = m.replace('<section class="slide" data-title=', '<section class="slide s1001" data-title=')
    m = one(m, QUAL_OLD, QUAL_NEW)
    return m.rstrip() + "\n"


def scope_sel(sel):
    return ",".join(f"{SCOPE} {x.strip()}" for x in sel.split(","))


PAGE_LEVEL = {":root", "html,body", "body", "#stage", "#tip", "#nav", "#nav span"}


def intro_css(T, deck1001):
    css = between(T, "<style>\n", "</style>")[len("<style>\n"):]
    assert css in deck1001
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@media[^{]*\{[^{}]*\{[^{}]*\}\s*\}", "", css)  # print rule: page level (#nav), same as 10-09
    assert "@" not in css
    out, n = [], 0
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        sel = " ".join(sel.split())
        if sel in PAGE_LEVEL:
            continue
        out.append(f"{scope_sel(sel)}{{{body}}}")
        n += 1
    assert n > 60, n
    return ("/* ===== slides 2-6: the 2026-10-01 deck's stylesheet (scripts/build_lab_deck.py), scoped to its five slides ===== */\n"
            + "\n".join(out) + "\n")


def intro_js(T, deck1001):
    esc = next(l for l in T.splitlines() if l.startswith("const esc = "))
    helpers = between(T, "function box(", "function drawStatic() {")
    draw = between(T, "function drawStatic() {", '  $("#svg-trials").innerHTML = s;\n', incl_b=True)
    for x in (esc, helpers, draw):
        assert x in deck1001
    assert "D.trials" in draw and "qual-" not in draw  # the five intro drawings only; the quality tables are not drawn
    return f"""/* ===== slides 2-6: schematics of the 2026-10-01 deck (scripts/build_lab_deck.py drawStatic, first five drawings, unchanged).
   D here = trial names, areas and v19 tiers (the 10-01 deck's qt.tier), from this deck's embedded trials. ===== */
function drawIntro() {{
  const D1001 = {{trials: D.trials.map(t => ({{name: t.name, area: t.area, qt: {{tier: t.t19}}}}))}};
  (function (D) {{
const NAVY = "#0E103C", RED = "#DC5A55";
const $ = s => document.querySelector(s);
{esc}
{helpers}{draw}}}
drawStatic();
  }})(D1001);
}}
"""


def check_intro_trials(D, deck1001):
    i = deck1001.index("const D = ") + len("const D = ")
    j = deck1001.index(";\nconst LOGO", i)
    D1 = json.loads(deck1001[i:j])
    a = [(t["name"], t["area"], t["qt"]["tier"]) for t in D1["trials"]]
    b = [(t["name"], t["area"], t["t19"]) for t in D["trials"]]
    assert a == b, "trial names / areas / v19 tiers differ from the 10-01 deck"


# ================================================================ assemble
def build(html09, D, deck1001):
    T = L1.TEMPLATE
    check_intro_trials(D, deck1001)
    h = html09
    h = one(h, "<title>TRACE-ECG | CarDS Lab update | October 9, 2026</title>", "<title>TRACE-ECG | CarDS Lab meeting | October 15, 2026</title>")
    h = one(h, '<div class="l3">Lab update · October 9<sup>th</sup>, 2026</div>', '<div class="l3">Lab meeting, Thursday 15 October 2026</div>')
    # slides 2-6 right after the title slide
    t_end = h.index("</section>\n", h.index('<section class="slide" id="s-title">')) + len("</section>\n")
    h = h[:t_end] + intro_markup(T, deck1001) + h[t_end:]
    h = one(h, "</style>", intro_css(T, deck1001) + "</style>")
    # chrome: no "Provisional" line on the five 10-01 slides (it was not on that deck)
    h = one(h, '<div class="prov">Provisional: trial set not frozen; methods not locked</div>',
            '${sl.classList.contains("s1001") ? "" : `<div class="prov">Provisional: trial set not frozen; methods not locked</div>`}')
    # 10-01 click-to-build (only slides with builds react: the five intro slides)
    h = one(h, '$("#nav-next").onclick = next;\n',
            '$("#nav-next").onclick = next;\n/* a click on a slide with builds (outside any control) reveals the next step (2026-10-01 deck) */\n'
            '$("#stage").addEventListener("click", e => { if (nSteps(slides[cur]) && !e.target.closest("select,input,label,button,a,.ctrl,.side")) next(); });\n')
    h = one(h, "/* ===== deck mechanics (2026-10-01 deck) ===== */", intro_js(T, deck1001) + "\n/* ===== deck mechanics (2026-10-01 deck) ===== */")
    h = one(h, "init(); emuInit(); agqInit(); fit();", "drawIntro(); init(); emuInit(); agqInit(); fit();")
    for bad in ("http://", "https://", "@import", "<link", "src=\"//"):
        assert bad not in h.replace("http://www.w3.org/2000/svg", ""), bad
    n = len(re.findall(r'<section class="slide', h))
    assert n == 22, n
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-validation-inputs", action="store_true", help="skip writing balance_combos.json / emu_refs.json")
    args = ap.parse_args()
    os.umask(0o077)
    SCR.mkdir(parents=True, exist_ok=True)
    html09, D, g, g2 = build_1009()
    assert html09 == DECK1009.read_text(), "regenerated 10-09 deck differs from the committed file"
    print(f"10-09 deck regenerated: byte-identical to {DECK1009.relative_to(ROOT)}")
    h = build(html09, D, DECK1001.read_text())
    old = os.umask(0o022)
    OUT.write_text(h)
    os.umask(old)
    print(f"wrote {OUT} ({len(h) / 1e6:.2f} MB)")
    titles = re.findall(r'<section class="slide[^"]*"(?: id="[^"]+")? data-title="([^"]+)"', h)
    for i, t in enumerate(["Title"] + titles, 1):
        print(f"{i:2d}  {t}")
    if not args.no_validation_inputs:  # headless-check references, as the 10-09 build (aggregates only)
        json.dump(V2.balance_combos(D, g, g2), open(SCR / "balance_combos.json", "w"), indent=0)
        json.dump(V2.emu_refs(D), open(SCR / "emu_refs.json", "w"), indent=0)
        print(f"validation inputs -> {SCR}")


if __name__ == "__main__":
    main()
