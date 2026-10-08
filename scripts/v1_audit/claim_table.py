"""Collect the headline contrasts of paper2.md under each correction (aggregates only) -> OUT/claim_rows.csv.

Sources: paper2 core/sensitivity.csv (as published, S32 / S38), defects/sweep_sensitivity.csv (leakage-clean S32 / S35 /
S38, original-mask S35, clean+soft S32), defects/d3_flagscv_s35.csv and core/flagscv.csv.
"""
from __future__ import annotations

import pandas as pd

import defect_impact as D

CORE, OUT = D.CORE, D.OUT
ROWS = [("main", "P5: ECG vs base"), ("main", "P5: CLMBR vs base"), ("main", "P5: ECG+CLMBR vs base"),
        ("main", "P5: shufECG vs base"), ("main", "P5: shufCLMBR vs base"), ("main", "P5: CLMBR vs ECG"),
        ("main", "P5: ECG+CLMBR vs CLMBR"), ("main", "P5: ECG+CLMBR vs ECG"),
        ("main", "P1: ECG vs base"), ("main", "P1: CLMBR vs base"), ("main", "P1: ECG+CLMBR vs base"), ("main", "P1: CLMBR vs ECG"),
        ("main", "hdPS200: ECG vs base"), ("main", "hdPS200: ECG vs shufECG"), ("main", "hdPS200: CLMBR vs base"),
        ("main", "hdPS200: CLMBR vs ECG"), ("main", "Flags: ECG vs base"), ("main", "Flags: CLMBR vs base"),
        ("main", "clinical: ECG vs base"), ("main", "clinical: CLMBR vs base"),
        ("main", "P1+CLMBR vs Flags base"), ("main", "P1+CLMBR32 vs Flags base"), ("main", "P1+CLMBR vs hdPS200 base"),
        ("main", "P5+CLMBR vs hdPS200 base"), ("main", "P5+CLMBR vs clinical base"), ("main", "P5+ECG+CLMBR vs clinical base"),
        ("main", "P5: CLMBR32 vs base")]
ROWS += [(c, k) for c in ("cal01", "m13", "iptw", "overlap", "gbm") for k in
         ("P5: ECG vs base", "P5: CLMBR vs base", "P5: ECG+CLMBR vs base", "P5: CLMBR vs ECG", "P5+CLMBR vs clinical base",
          "P5+ECG+CLMBR vs clinical base", "P1+CLMBR vs Flags base", "P1+CLMBR vs hdPS200 base", "clinical: ECG vs base",
          "clinical: CLMBR vs base")]
COLS = ["relred54", "relred54_lo", "relred54_hi", "m54_better", "m54_p", "q_m54_p_fam", "relred58", "absd_b", "absd_a", "absd_p",
        "bshuf_p", "q_absd_p_fam", "q_bshuf_p_fam", "n_trials"]


def main():
    S0 = pd.read_csv(CORE / "sensitivity.csv").assign(variant="paper2")
    S1 = pd.read_csv(OUT / "sweep_sensitivity.csv")
    S = pd.concat([S0, S1], ignore_index=True)
    keep = pd.MultiIndex.from_tuples(ROWS, names=["config", "contrast"])
    S = S.set_index(["config", "contrast"])
    S = S[S.index.isin(keep)].reset_index()
    out = S[["variant", "set", "config", "contrast"] + COLS].sort_values(["config", "contrast", "variant", "set"])
    out.to_csv(OUT / "claim_rows.csv", index=False)
    q = pd.concat([S0, S1]).groupby(["variant", "set", "config"]).q_m54_p_fam.apply(lambda x: int((x < .05).sum())).unstack()
    q["total"] = q.sum(1)
    qa = pd.concat([S0, S1]).groupby(["variant", "set"]).apply(
        lambda g: int(((g.q_absd_p_fam < .05) | (g.q_bshuf_p_fam < .05) | (g.q_cons_p_fam < .05)).sum()))
    q["agreement_rows_q05"] = qa
    q.to_csv(OUT / "q_counts_by_variant.csv")
    print(q.to_string())


if __name__ == "__main__":
    main()
