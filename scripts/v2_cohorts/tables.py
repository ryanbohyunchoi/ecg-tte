#!/usr/bin/env python
"""Markdown tables for docs/v2_cohorts/COHORT_FIXES.md from the aggregate outputs (OUT/flags/*.csv, OUT/summary/*.csv).
Writes OUT/summary/tables.md (aggregates only). Usage: tables.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2common as K  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import specs_v2 as SV  # noqa: E402

COH = ["v1", "v2", "v2old", "v2meas"]
CLAB = {"v1": "v1 cohorts", "v2": "spec-v2 (primary)", "v2old": "spec-v2, v1 PCs", "v2meas": "spec-v2, entry values measured"}
RLAB = {"P1": "PS-Demo", "P5": "PS-CVD5", "PS10": "CVD10", "Flags": "PS-Flags", "hdPS200": "hdPS",
        "clinical": "PS-Clinical (with LVEF, v1)", "clinical_nolvef": "PS-Clinical (no LVEF)"}
ALAB = {"ECG": "+ ECG", "CLMBR": "+ CLMBR-T", "ECG+CLMBR": "+ both"}


def f(x, d=1):
    return "" if pd.isna(x) else f"{x:.{d}f}"


def fp(x):
    if pd.isna(x):
        return ""
    return "<.001" if x < 0.001 else f"{x:.3f}"


def ci(r, k="relred54"):
    return f"{f(r[k])} ({f(r[k + '_lo'])} to {f(r[k + '_hi'])})"


def md(rows, cols):
    L = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    L += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]
    return "\n".join(L)


def get(S, cohort, sname, cfg, contrast):
    q = S[(S.cohort == cohort) & (S.set == sname) & (S.config == cfg) & (S.contrast == contrast)]
    return None if q.empty else q.iloc[0]


def trial_table():
    T = pd.read_csv(K.FLG / "exclusions_by_trial.csv")
    R = pd.read_csv(K.FLG / "exclusions_by_rule.csv")
    O = pd.read_csv(K.FLG / "outcome_events.csv").set_index("trial")
    rows = []
    for _, t in T.iterrows():
        rr = R[R.trial == t.trial]
        act = rr[rr.pct_removed_v2.astype(str) != "0.0"]
        fixes = sorted(set(int(x) for x in act.fix))
        lab = {1: "numeric", 2: "age", 3: "washout/class", 4: "gate/population"}
        fx = ", ".join(lab[x] for x in fixes)
        if t.trial in O.index:
            fx = (fx + ", " if fx else "") + "outcome"
        rows.append({"Trial": t.label, "S32": "yes" if t.trial in K.S32 else "", "S29": "yes" if t.trial in K.S29 else "",
                     "Fix types applied": fx or "none (no patient removed)",
                     "Rules removing patients": "; ".join(act.rule) or "-",
                     "% removed (v2)": t.pct_removed_v2, "treated / comparator": f"{t.pct_removed_v2_arm1} / {t.pct_removed_v2_arm0}",
                     "% removed (entry values measured)": t.pct_removed_v2meas})
    return md(rows, list(rows[0]))


def rule_table():
    R = pd.read_csv(K.FLG / "exclusions_by_rule.csv")
    rows = []
    for _, r in R.iterrows():
        rows.append({"Trial": r.label, "Rule": r.rule, "Fix": int(r.fix), "Definition": r.text, "Source": r.source,
                     "% removed": r.pct_removed_v2, "treated / comparator": f"{r.pct_removed_v2_arm1} / {r.pct_removed_v2_arm0}",
                     "% removed, measured required": r.pct_removed_v2meas})
    return md(rows, list(rows[0]))


def headline(S, cfg="main", cohorts=("v1", "v2", "v2old", "v2meas")):
    rows = []
    for sname in ("S32", "S29", "S38"):
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            for c in cohorts:
                r = get(S, c, sname, cfg, f"P5: {a} vs base")
                if r is None:
                    continue
                rows.append({"Set": sname, "Contrast": f"PS-CVD5 {ALAB[a]} vs PS-CVD5", "Cohorts": CLAB[c],
                             "m54 base -> arm": f"{f(r.m54_b, 3)} -> {f(r.m54_a, 3)}", "Rel. red. 54 (95% CI)": ci(r),
                             "Trials better": r.m54_better, "P": fp(r.m54_p), "q": fp(r.q_m54_p_fam),
                             "Rel. red. 58 (95% CI)": ci(r, "relred58"),
                             "abs dlogHR base -> arm": f"{f(r.absd_b, 3)} -> {f(r.absd_a, 3)}", "Closer": r.absd_better,
                             "P (sign-flip)": fp(r.absd_p), "P (benchmark perm.)": fp(r.bshuf_p)})
    return md(rows, list(rows[0]))


def configs(S):
    rows = []
    for sname in ("S32", "S29", "S38"):
        for cfg in K.CONFIGS:
            row = {"Set": sname, "Config": cfg}
            for a in ("ECG", "CLMBR", "ECG+CLMBR"):
                for c in ("v1", "v2"):
                    r = get(S, c, sname, cfg, f"P5: {a} vs base")
                    row[f"{ALAB[a]} {c}"] = f"{f(r.relred54)} (P {fp(r.m54_p)}; dHR P {fp(r.absd_p)})" if r is not None else ""
            rows.append(row)
    return md(rows, list(rows[0]))


def ladder(S, L, sname, cfg="main"):
    rows = []
    for rg in ("P1", "P5", "hdPS200", "clinical_nolvef", "PS10", "Flags", "clinical"):
        row = {"PS level": RLAB[rg] + (" (supplement)" if rg in ("PS10", "Flags") else " (v1 reference)" if rg == "clinical" else "")}
        for c in ("v1", "v2"):
            q = L[(L.cohort == c) & (L.set == sname) & (L.config == cfg) & (L.rung == rg) & (L.arm == "base") & (L.panel == "54")]
            row[f"base mean SMD54 {c}"] = f(q.mean_smd.iloc[0], 3) if len(q) else ""
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            for c in ("v1", "v2"):
                r = get(S, c, sname, cfg, f"{rg}: {a} vs base")
                row[f"{ALAB[a]} {c}"] = f"{f(r.relred54)} (P {fp(r.m54_p)})" if r is not None else ""
        rows.append(row)
    return md(rows, list(rows[0]))


def base2base(S, sname, cfg="main"):
    rows = []
    for lab in ("P1 base vs P5 base", "hdPS200 base vs P5 base", "clinical_nolvef base vs P5 base", "PS10 base vs P5 base",
                "Flags base vs P5 base", "P1+CLMBR vs Flags base", "P5+CLMBR vs hdPS200 base", "P5+ECG+CLMBR vs hdPS200 base",
                "P5+CLMBR vs clinical_nolvef base", "P5+ECG+CLMBR vs clinical_nolvef base", "P5+ECG vs clinical_nolvef base"):
        row = {"Contrast (two-sided)": lab}
        for c in ("v1", "v2"):
            r = get(S, c, sname, cfg, lab)
            row[c] = f"{f(r.relred54)} ({f(r.relred54_lo)} to {f(r.relred54_hi)}), P {fp(r.m54_p)}; dHR {f(r.absd_b, 3)}->{f(r.absd_a, 3)} P {fp(r.absd_p)}" if r is not None else ""
        rows.append(row)
    return md(rows, list(rows[0]))


def placebo(S, sname, cfg="main"):
    rows = []
    for rg in ("P5", "P1", "hdPS200", "clinical_nolvef"):
        for lab, side in (("shufECG vs base", "two"), ("shufCLMBR vs base", "two"), ("ECG vs shufECG", "one"),
                          ("CLMBR vs shufCLMBR", "one"), ("CLMBR vs ECG", "two"), ("ECG+CLMBR vs CLMBR", "one"),
                          ("ECG+CLMBR vs ECG", "one")):
            row = {"PS level": RLAB[rg], "Contrast": lab, "sided": side}
            for c in ("v1", "v2"):
                r = get(S, c, sname, cfg, f"{rg}: {lab}")
                row[c] = f"{ci(r)}, P {fp(r.m54_p)}; dHR P {fp(r.absd_p)}" if r is not None else ""
            rows.append(row)
    return md(rows, list(rows[0]))


def domains(D, sname, cfg="main"):
    rows = []
    for g in [x for x in dict.fromkeys(K.GROUP.values()) if x != "Coded record"] + ["Echo, all 35 items"]:
        row = {"Domain": g}
        for a in ("ECG", "CLMBR", "ECG+CLMBR"):
            for c in ("v1", "v2"):
                q = D[(D.cohort == c) & (D.set == sname) & (D.config == cfg) & (D.contrast == f"P5: {a} vs base") & (D.domain == g)]
                row[f"{ALAB[a]} {c}"] = f"{f(q.relred.iloc[0])} (P {fp(q.p.iloc[0])})" if len(q) else ""
        rows.append(row)
    return md(rows, list(rows[0]))


def per_trial(PT):
    rows = []
    for n in K.ALL:
        row = {"Trial": K.NAME[n]}
        for c in ("v1", "v2"):
            q = PT[(PT.cohort == c) & (PT.trial == n) & (PT.rung == "P5")].set_index("arm")
            row[f"m54 base {c}"] = f(q.loc["base", "m54"], 3)
            row[f"m54 +ECG {c}"] = f(q.loc["ECG", "m54"], 3)
            row[f"m54 +CLMBR-T {c}"] = f(q.loc["CLMBR", "m54"], 3)
            row[f"absd base {c}"] = f(q.loc["base", "absd"], 3)
        rows.append(row)
    return md(rows, list(rows[0]))


def failed():
    F = pd.read_csv(K.SUM / "failed_cells.csv")
    if F.empty:
        return "No failed cells."
    G = F.groupby(["cohort", "rung"]).n_trials_failed.sum().reset_index()
    return md(G.to_dict("records"), list(G.columns))


def main():
    K.umask()
    S = pd.read_csv(K.SUM / "contrasts.csv")
    D = pd.read_csv(K.SUM / "domains.csv")
    L = pd.read_csv(K.SUM / "ladder.csv")
    PT = pd.read_csv(K.SUM / "per_trial.csv")
    out = ["# Spec-v2 cohort tables (generated by scripts/v2_cohorts/tables.py)\n",
           "## Per trial: fixes and share removed\n", trial_table(),
           "\n## Per rule\n", rule_table(),
           "\n## Headline: PS-CVD5 + representation vs PS-CVD5, main configuration\n", headline(S),
           "\n## All six configurations (relative reduction 54 items, %; P balance; P |dlog HR|)\n", configs(S)]
    for sname in ("S32", "S29", "S38"):
        out += [f"\n## Ladder, {sname}, main configuration (relative reduction 54 items, %)\n", ladder(S, L, sname),
                f"\n## Base-to-base and head-to-heads, {sname}, main\n", base2base(S, sname),
                f"\n## Placebos and head-to-heads within rung, {sname}, main\n", placebo(S, sname),
                f"\n## Per domain, PS-CVD5, {sname}, main\n", domains(D, sname)]
    out += ["\n## Per trial, PS-CVD5, main configuration (trial-level aggregates)\n", per_trial(PT),
            "\n## Failed cells (< 11 matched pairs or failed fit), trials x configs x arms summed\n", failed()]
    (K.SUM / "tables.md").write_text("\n".join(out) + "\n")
    print("tables written")


if __name__ == "__main__":
    main()
