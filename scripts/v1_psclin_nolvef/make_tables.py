#!/usr/bin/env python
"""Markdown tables for docs/v1_psclin_nolvef/PS_CLINICAL_NO_LVEF.md from the psclin_nolvef.py summaries (aggregates only:
trial counts, means, CIs, P values). Usage: python make_tables.py > OUT/summary/tables.md"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

A = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-psclin-nolvef")
S = pd.read_csv(A / "summary/contrasts.csv")
D = pd.read_csv(A / "summary/domains.csv")
L = pd.read_csv(A / "summary/ladder.csv")
CFGS = ["main", "cal01", "m13", "iptw", "overlap", "gbm"]
ARMLAB = {"ECG": "+ ECG", "shufECG": "+ permuted ECG", "CLMBR": "+ CLMBR-T", "ECG+CLMBR": "+ CLMBR-T + ECG", "shufCLMBR": "+ permuted CLMBR-T",
          "CLMBR32": "+ CLMBR-T (32 PCs)"}
RL = {"P1": "PS-Demo", "P5": "PS-CVD5", "Flags": "PS-Flags", "hdPS200": "hdPS", "clinical": "PS-Clinical (with LVEF)",
      "clinical_nolvef": "PS-Clinical (no LVEF)", "clinical_nolvef_drop": "PS-Clinical (no LVEF, column dropped)"}


def fp(p):
    if pd.isna(p):
        return "–"
    return "<.001" if p < 0.001 else (f"{p:.3f}"[1:] if p < 0.01 else f"{p:.2f}"[1:] if p < 0.995 else f"{p:.2f}")


def ci(e, lo, hi):
    return f"{e:.1f}% ({lo:.1f} to {hi:.1f})" if np.isfinite(lo) else f"{e:.1f}%"


def row(variant, sname, cfg, contrast):
    q = S[(S.variant == variant) & (S.set == sname) & (S.config == cfg) & (S.contrast == contrast)]
    assert len(q) == 1, (variant, sname, cfg, contrast, len(q))
    return q.iloc[0]


def md(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


P = []


def headline(variant, sname, rg, cfg="main", arms=("ECG", "shufECG", "CLMBR", "ECG+CLMBR", "shufCLMBR")):
    rows = []
    for a in arms:
        r = row(variant, sname, cfg, f"{rg}: {a} vs base")
        rows.append([ARMLAB[a], f"{r.m54_b:.3f} → {r.m54_a:.3f}", ci(r.relred54, r.relred54_lo, r.relred54_hi), r.m54_better, fp(r.m54_p),
                     fp(r.get("q_m54_p_nolvef_fam", np.nan)) if rg == "clinical_nolvef" else "–",
                     f"{r.lt01_54_b:.1f} → {r.lt01_54_a:.1f}", fp(r.lt01_54_p), ci(r.relred58, r.relred58_lo, r.relred58_hi), fp(r.m58_p),
                     f"{r.absd_b:.3f} → {r.absd_a:.3f}", r.absd_better, fp(r.absd_p), fp(r.bshuf_p), r.sided,
                     f"{r.items54_median:.0f}"])
    return md(["Arm vs PS alone", "mean \\|SMD\\| (54)", "rel. reduction 54 (95% CI)", "trials better", "P", "q (rung family)",
               "% \\|SMD\\|<0.1", "P (%)", "rel. reduction 58 (95% CI)", "P (58)", "\\|Δ log HR\\| vs RCT", "trials closer", "P",
               "permutation P", "sided", "items paired (median)"], rows)


def configs(variant, sname, rg, arms=("ECG", "shufECG", "CLMBR", "ECG+CLMBR", "shufCLMBR")):
    rows = []
    for cfg in CFGS:
        rr = [cfg]
        for a in arms:
            r = row(variant, sname, cfg, f"{rg}: {a} vs base")
            rr.append(f"{ci(r.relred54, r.relred54_lo, r.relred54_hi)}; {r.m54_better}; P {fp(r.m54_p)}")
        rows.append(rr)
    return md(["config"] + [ARMLAB[a] for a in arms], rows)


def agreement(variant, sname, rg, arms=("ECG", "shufECG", "CLMBR", "ECG+CLMBR", "shufCLMBR")):
    rows = []
    for cfg in CFGS:
        rr = [cfg]
        for a in arms:
            r = row(variant, sname, cfg, f"{rg}: {a} vs base")
            rr.append(f"{r.absd_b:.3f} → {r.absd_a:.3f}; {r.absd_better}; P {fp(r.absd_p)}; perm. P {fp(r.bshuf_p)}")
        rows.append(rr)
    return md(["config"] + [ARMLAB[a] for a in arms], rows)


def domains(variant, sname, rg, cfg="main", arms=("ECG", "CLMBR", "ECG+CLMBR", "shufECG")):
    doms = [d for d in dict.fromkeys(D.domain)]
    rows = []
    for g in doms:
        rr = [g]
        for a in arms:
            q = D[(D.variant == variant) & (D.set == sname) & (D.config == cfg) & (D.contrast == f"{rg}: {a} vs base") & (D.domain == g)]
            if not len(q):
                rr.append("–")
                continue
            d = q.iloc[0]
            rr.append("masked" if not np.isfinite(d.mean_b) else
                      f"{d.mean_b:.3f} → {d.mean_a:.3f}; {ci(d.relred, d.relred_lo, d.relred_hi)}; {d.better}; P {fp(d.p)}")
        rows.append(rr)
    return md(["domain (items)"] + [ARMLAB[a] for a in arms], rows)


def lvef_bought(variant, sname, nl="clinical_nolvef"):
    rows = []
    for cfg in CFGS:
        r = row(variant, sname, cfg, f"clinical base vs {nl} base")
        e = row(variant, sname, cfg, f"{nl} ECG vs clinical base")
        f = row(variant, sname, cfg, f"clinical ECG vs {nl} ECG")
        rows.append([cfg, f"{r.m54_b:.3f} → {r.m54_a:.3f}", ci(r.relred54, r.relred54_lo, r.relred54_hi), r.m54_better, fp(r.m54_p),
                     ci(r.relred58, r.relred58_lo, r.relred58_hi), fp(r.m58_p), f"{r.absd_b:.3f} → {r.absd_a:.3f}", fp(r.absd_p),
                     f"{e.m54_b:.3f} → {e.m54_a:.3f}; {ci(e.relred54, e.relred54_lo, e.relred54_hi)}; P {fp(e.m54_p)}",
                     f"{ci(f.relred54, f.relred54_lo, f.relred54_hi)}; P {fp(f.m54_p)}", f"{r.items54_median:.0f}"])
    return md(["config", "mean \\|SMD\\| no LVEF → with LVEF (54)", "rel. reduction from adding LVEF (54)", "trials better with LVEF",
               "P (two-sided)", "same, 58 items", "P (58)", "\\|Δ log HR\\| no LVEF → with LVEF", "P",
               "with-LVEF PS alone → no-LVEF PS + ECG (54); rel. reduction", "with-LVEF + ECG vs no-LVEF + ECG (54)",
               "items paired (median)"], rows)


def ladder(variant, sname, cfg="main", panel="common45", rungs=("P1", "P5", "Flags", "hdPS200", "clinical_nolvef", "clinical")):
    rows = []
    for rg in rungs:
        rr = [RL[rg]]
        for a in ("base", "ECG", "CLMBR", "ECG+CLMBR"):
            q = L[(L.variant == variant) & (L.set == sname) & (L.config == cfg) & (L.rung == rg) & (L.arm == a) & (L.panel == panel)]
            rr.append(f"{q.iloc[0].mean_smd:.3f}" if len(q) else "–")
        r = row(variant, sname, cfg, f"{rg}: ECG vs base")
        rr.append(ci(r.relred54, r.relred54_lo, r.relred54_hi))
        q = L[(L.variant == variant) & (L.set == sname) & (L.config == cfg) & (L.rung == rg) & (L.arm == "base") & (L.panel == panel)]
        rr.append(f"{q.iloc[0].items_median:.0f}")
        rows.append(rr)
    return md(["PS base", "PS alone", "+ ECG", "+ CLMBR-T", "+ CLMBR-T + ECG", "+ ECG vs PS alone, paired, own 54-item set (95% CI)",
               "items (median)"], rows)


def across(variant, sname, cfg="main"):
    rows = []
    for c in ("P5+CLMBR vs clinical_nolvef base", "P5+ECG+CLMBR vs clinical_nolvef base", "P5+ECG vs clinical_nolvef base",
              "hdPS200+base vs clinical_nolvef base", "clinical_nolvef base vs P5 base", "clinical_nolvef base vs hdPS200 base"):
        r = row(variant, sname, cfg, c)
        rows.append([c, f"{r.m54_b:.3f} → {r.m54_a:.3f}", ci(r.relred54, r.relred54_lo, r.relred54_hi), r.m54_better, fp(r.m54_p), r.sided,
                     f"{r.absd_b:.3f} → {r.absd_a:.3f}", fp(r.absd_p), fp(r.bshuf_p)])
    return md(["contrast (a vs b)", "mean \\|SMD\\| b → a (54)", "rel. reduction (a vs b)", "trials a better", "P", "sided",
               "\\|Δ log HR\\| b → a", "P", "permutation P"], rows)


def clmbr32(variant, sname):
    rows = []
    for rg in ("clinical_nolvef", "clinical_nolvef_drop", "clinical"):
        for c in ("CLMBR32 vs base", "CLMBR32 vs ECG", "CLMBR vs CLMBR32"):
            r = row(variant, sname, "main", f"{rg}: {c}")
            rows.append([RL[rg], c, f"{r.m54_b:.3f} → {r.m54_a:.3f}", ci(r.relred54, r.relred54_lo, r.relred54_hi), r.m54_better, fp(r.m54_p), r.sided])
    return md(["PS base", "contrast", "mean \\|SMD\\| b → a (54)", "rel. reduction", "trials a better", "P", "sided"], rows)


out = []
for sname in ("S32", "S38"):
    out.append(f"\n## {sname}\n")
    for variant in ("clean", "v1"):
        for rg in ("clinical_nolvef", "clinical_nolvef_drop", "clinical"):
            out.append(f"\n### Headline, main config, {RL[rg]}, masking {variant}, {sname}\n\n" + headline(variant, sname, rg))
        out.append(f"\n### All configurations, {RL['clinical_nolvef']}, masking {variant}, {sname} (relative reduction 54 items; trials better; P)\n\n"
                   + configs(variant, sname, "clinical_nolvef"))
        out.append(f"\n### All configurations, {RL['clinical']}, masking {variant}, {sname}\n\n" + configs(variant, sname, "clinical"))
        out.append(f"\n### All configurations, {RL['clinical_nolvef_drop']}, masking {variant}, {sname}\n\n" + configs(variant, sname, "clinical_nolvef_drop"))
        out.append(f"\n### Agreement, all configurations, {RL['clinical_nolvef']}, masking {variant}, {sname}\n\n" + agreement(variant, sname, "clinical_nolvef"))
        for rg in ("clinical_nolvef", "clinical"):
            out.append(f"\n### Domains, main, {RL[rg]}, masking {variant}, {sname}\n\n" + domains(variant, sname, rg))
        for cfg in CFGS:
            out.append(f"\n### Domains (echo / LVEF rows), {cfg}, {RL['clinical_nolvef']}, masking {variant}, {sname}\n\n"
                       + domains(variant, sname, "clinical_nolvef", cfg=cfg))
        for nl in ("clinical_nolvef", "clinical_nolvef_drop"):
            out.append(f"\n### What LVEF bought: {RL['clinical']} vs {RL[nl]} (PS alone), masking {variant}, {sname}\n\n" + lvef_bought(variant, sname, nl))
        for panel in ("common45", "54", "58", "echo35"):
            out.append(f"\n### Ladder, main, items {panel}, masking {variant}, {sname}\n\n" + ladder(variant, sname, panel=panel))
        out.append(f"\n### Across-rung contrasts, main, masking {variant}, {sname}\n\n" + across(variant, sname))
        out.append(f"\n### CLMBR-T 32 PCs, main, masking {variant}, {sname}\n\n" + clmbr32(variant, sname))
F = pd.read_csv(A / "summary/failed_cells.csv")
out.append("\n## Failed cells (F1: < 11 matched pairs or failed fit; trial counts)\n\n" + md(list(F.columns), F.values.tolist()))
print("\n".join(out))
