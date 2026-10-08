"""Headless check of docs/presentation/ecg_tte_balance_explorer_2026_10_08.html after adding PS-Clinical (no LVEF).

Same checks as the original explorer check (audits/claude-balance-explorer/headless_check.py), plus the new rung:
  1. JS point estimates (window.TRACE.pair) vs the Python reference on the embedded data (py_ref_combos.json, written by
     scripts/build_balance_explorer.py --check); exact up to float round-off.
  2. JS vs the Python summaries of scripts/v1_psclin_nolvef/psclin_nolvef.py (full precision; the explorer embeds |SMD| as
     integers x 1e5, so agreement is to that rounding): every within-rung contrast vs PS alone for clinical_nolvef
     (6 configs x S32 / S38 x 5 arms x 54 / 58 items x leakage off / on) and every ladder level (TRACE.level).
  3. Default view still reproduces paper 1's primary numbers; the default ladder shows PS-Demo, PS-CVD5, hdPS,
     PS-Clinical (no LVEF).
  4. Every control toggled in each view (including the new ladder-level checkboxes); console / page errors collected.
  5. Screenshots.
Env (session scratchpad): PLAYWRIGHT_BROWSERS_PATH, PYTHONPATH (playwright), LD_LIBRARY_PATH (system libs).
Usage: python explorer_headless_check.py   (writes to audits/claude-v1-psclin-nolvef/explorer/)
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

os.umask(0o077)
HTML = Path("/home/rbc58/github/ecg-tte/docs/presentation/ecg_tte_balance_explorer_2026_10_08.html")
A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
SCR = A / "claude-balance-explorer"
OUT = A / "claude-v1-psclin-nolvef" / "explorer"
OUT.mkdir(parents=True, exist_ok=True)
combos = json.load(open(SCR / "py_ref_combos.json"))
NC = pd.read_csv(A / "claude-v1-psclin-nolvef/summary/contrasts.csv")
NC = NC[(NC.rung_a == "clinical_nolvef") & (NC.kind == "within") & (NC.arm_b == "base")]
LD = pd.read_csv(A / "claude-v1-psclin-nolvef/summary/ladder.csv")
LD = LD[LD.rung.isin(["P1", "P5", "Flags", "hdPS200", "clinical_nolvef", "clinical"]) & LD.panel.isin(["54", "58"])
        & LD.arm.isin(["base", "ECG", "shufECG", "CLMBR", "ECG+CLMBR", "shufCLMBR"])]
res = {"errors": [], "console": []}


def close(a, b, tol=1e-9):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, float) and math.isnan(a):
        return b is None
    return abs(a - b) <= tol * max(1.0, abs(b))


ROWS = "rs => rs.map(r => [...r.children].map(c => c.innerText.replace(/\\n/g, ' ')))"
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1500, "height": 1000})
    pg.on("console", lambda m: res["console"].append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: res["errors"].append(str(e)))
    t0 = time.time()
    pg.goto(HTML.as_uri())
    pg.wait_for_selector("#sum table")
    res["load_secs"] = round(time.time() - t0, 2)
    txt = pg.inner_text("#sum")
    res["default_has"] = {k: (k in txt) for k in ["49.8 → 55.0", "22/32", ".002", "11.4%", "6.3 to 16.0", "0.142 → 0.126", "-0.7%"]}
    res["rung_options"] = pg.eval_on_selector("#c-rung", "e => [...e.options].map(o => o.textContent)")
    res["ladder_default_checked"] = pg.eval_on_selector_all("#c-lad input:checked", "es => es.map(e => e.value)")
    # --- 1. JS vs Python on the embedded data
    keys = ["k", "pct_ref", "pct_arm", "dpts", "better", "p", "m_ref", "m_arm", "lower", "p_m", "rr", "lo", "hi"]
    dev, bad = {k: 0.0 for k in keys}, []
    for c in combos:
        js = pg.evaluate("s => { const r = TRACE.pair(s); for (const k in r) if (typeof r[k] === 'number' && !Number.isFinite(r[k])) r[k] = null; return r; }",
                         {k: c[k] for k in ("cfg", "rung", "arm", "trials", "panel", "leak", "thr")})
        for k in keys:
            a, b = js.get(k), c["py"].get(k)
            if a is not None and b is not None:
                dev[k] = max(dev[k], abs(a - b))
            if not close(a, b):
                bad.append(dict(combo={x: c[x] for x in ("cfg", "rung", "arm", "trials", "panel", "leak", "thr")}, key=k, js=a, py=b))
    res["js_vs_py"] = dict(n_combos=len(combos), n_combos_nolvef=sum(c["rung"] == "clinical_nolvef" for c in combos),
                           n_values=len(combos) * len(keys), max_abs_dev=dev, mismatches=bad[:20], n_mismatch=len(bad))
    # --- 2. JS vs the psclin_nolvef Python summaries (new rung)
    nr = []
    for _, s in NC.iterrows():
        for panel in ("54", "58"):
            pre, mm = ("relred54", "m54") if panel == "54" else ("relred58", "m58")
            js = pg.evaluate("s => TRACE.pair(s)", dict(cfg=s.config, rung="clinical_nolvef", arm=s.arm_a, trials="s32" if s.set == "S32" else "all",
                                                       panel=panel, leak=bool(s.variant == "clean"), thr=0.1))
            nr.append(dict(variant=s.variant, set=s.set, config=s.config, arm=s.arm_a, panel=panel, py_rr=s[pre], js_rr=js["rr"],
                           rr_dev=abs(js["rr"] - s[pre]), lo_dev=abs(js["lo"] - s[pre + "_lo"]), hi_dev=abs(js["hi"] - s[pre + "_hi"]),
                           m_dev=max(abs(js["m_ref"] - s[f"{mm}_b"]), abs(js["m_arm"] - s[f"{mm}_a"])),
                           rr_1dp_equal=f"{js['rr']:.1f}" == f"{s[pre]:.1f}",
                           better_ok=f"{js['lower']}/{js['k']}" == s[f"{mm}_better"],
                           p_m_dev=abs(js["p_m"] - s[f"{mm}_p"]) if s.sided == "one" else None))
    NX = pd.DataFrame(nr)
    NX.to_csv(OUT / "js_vs_python_nolvef_contrasts.csv", index=False)
    ld = []
    for _, s in LD.iterrows():
        v = pg.evaluate("s => TRACE.level(s)", dict(cfg=s.config, rung=s.rung, arm=s.arm, trials="s32" if s.set == "S32" else "all",
                                                    panel=str(s.panel), leak=bool(s.variant == "clean")))
        ld.append(dict(variant=s.variant, set=s.set, rung=s.rung, config=s.config, arm=s.arm, panel=s.panel, py=s.mean_smd, js=v,
                       dev=abs(v - s.mean_smd), equal_3dp=f"{v:.3f}" == f"{s.mean_smd:.3f}"))
    LX = pd.DataFrame(ld)
    LX.to_csv(OUT / "js_vs_python_ladder.csv", index=False)
    res["js_vs_nolvef_summaries"] = dict(rows=len(NX), max_rr_dev=float(NX.rr_dev.max()), max_ci_dev=float(max(NX.lo_dev.max(), NX.hi_dev.max())),
                                         max_m_dev=float(NX.m_dev.max()), rr_1dp_equal=int(NX.rr_1dp_equal.sum()),
                                         better_all_ok=bool(NX.better_ok.all()), max_p_m_dev=float(NX.p_m_dev.dropna().max()),
                                         rr_1dp_unequal_rows=NX[~NX.rr_1dp_equal][["variant", "set", "config", "arm", "panel", "py_rr", "js_rr"]].to_dict("records")[:10])
    res["js_vs_ladder"] = dict(rows=len(LX), max_dev=float(LX.dev.max()), equal_3dp=int(LX.equal_3dp.sum()))

    # --- 3/4. default ladder and toggles
    def setsel(sel, v):
        pg.eval_on_selector(sel, "(e, v) => { e.value = v; e.dispatchEvent(new Event('change', {bubbles: true})); }", v)

    pg.click("#views input[value=ladder] >> xpath=..")
    res["ladder_default_axis"] = pg.eval_on_selector_all("#svg text[font-weight='700']", "ts => ts.map(t => t.textContent)")
    pg.screenshot(path=str(OUT / "screenshot_ladder_default.png"), full_page=True)
    n_actions = 0
    for view in ("love", "ladder", "method"):
        pg.click(f"#views input[value={view}] >> xpath=..")
        n_actions += 1
        for sel in ("#c-trials", "#c-cfg", "#c-rung", "#c-panel", "#c-group", "#c-dom", "#c-rank", "#c-stat", "#c-thr"):
            vals = pg.eval_on_selector(sel, "e => [...e.options].map(o => o.value)")
            orig = pg.eval_on_selector(sel, "e => e.value")
            for v in vals:
                setsel(sel, v)
                n_actions += 1
            setsel(sel, orig)
        for a in pg.eval_on_selector_all("#c-arms input", "es => es.map(e => e.value)"):
            pg.click(f"#c-arms input[value='{a}']")
            pg.click(f"#c-arms input[value='{a}']")
            n_actions += 2
        for r in pg.eval_on_selector_all("#c-lad input", "es => es.map(e => e.value)"):
            pg.click(f"#c-lad input[value='{r}']")
            pg.click(f"#c-lad input[value='{r}']")
            n_actions += 2
        for cb in ("#c-leak", "#c-ref"):
            pg.click(cb)
            pg.click(cb)
            n_actions += 2
        for q in ("phys", "echo", "all"):
            pg.click(f"#c-qv input[value={q}]")
            n_actions += 1
        pg.click("#c-leak")
        for a in ("CLMBR", "ECG+CLMBR", "shufCLMBR", "unmatched"):
            pg.click(f"#c-arms input[value='{a}']")
        for r in ("P1", "P5", "Flags", "hdPS200", "clinical_nolvef", "clinical"):
            setsel("#c-rung", r)
            for pnl in ("58", "54", "exp"):
                setsel("#c-panel", pnl)
                n_actions += 2
        setsel("#c-panel", "58")
        setsel("#c-rung", "P1")
        pg.click("#c-leak")
        for a in ("CLMBR", "ECG+CLMBR", "shufCLMBR", "unmatched"):
            pg.click(f"#c-arms input[value='{a}']")
        setsel("#c-trials", "t:0")
        setsel("#c-rank", "gain")
        setsel("#c-rank", "u")
        setsel("#c-trials", "s32")
        n_actions += 4
    res["n_actions"] = n_actions
    pg.click("#views input[value=love] >> xpath=..")
    res["default_restored"] = pg.inner_text("#sum") == txt
    # new-rung views: PS-Clinical (no LVEF), 54 items, leakage-corrected, + ECG / + CLMBR-T / + both
    setsel("#c-rung", "clinical_nolvef")
    setsel("#c-panel", "54")
    pg.click("#c-leak")
    pg.click("#c-arms input[value='shufECG']")
    for a in ("CLMBR", "ECG+CLMBR"):
        pg.click(f"#c-arms input[value='{a}']")
    res["nolvef54_clean_summary_rows"] = pg.eval_on_selector_all("#sum table tr", ROWS)
    res["nolvef_leak_desc"] = pg.inner_text("#c-leakd")
    pg.screenshot(path=str(OUT / "screenshot_nolvef_love.png"), full_page=True)
    setsel("#c-dom", "echo")
    res["nolvef54_clean_echo_rows"] = pg.eval_on_selector_all("#sum table tr", ROWS)
    setsel("#c-dom", "all")
    pg.click("#views input[value=ladder] >> xpath=..")
    pg.screenshot(path=str(OUT / "screenshot_nolvef_ladder_clean54.png"), full_page=True)
    pg.click("#views input[value=method] >> xpath=..")
    pg.screenshot(path=str(OUT / "screenshot_nolvef_method.png"), full_page=True)
    br.close()

json.dump(res, open(OUT / "headless_results.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: res[k] for k in ("errors", "console", "load_secs", "default_has", "rung_options", "ladder_default_checked",
                                      "ladder_default_axis", "n_actions", "default_restored")}, indent=1, ensure_ascii=False))
print(json.dumps(res["js_vs_py"], indent=1))
print(json.dumps(res["js_vs_nolvef_summaries"], indent=1))
print(json.dumps(res["js_vs_ladder"], indent=1))
print(res["nolvef54_clean_summary_rows"])
sys.exit(1 if res["errors"] or res["js_vs_py"]["n_mismatch"] else 0)
