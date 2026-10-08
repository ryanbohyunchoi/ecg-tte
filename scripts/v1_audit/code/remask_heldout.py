#!/usr/bin/env python
"""v1 audit: (1) independent re-derivation of headline paper2 balance contrasts from core/restricted_cells.parquet
(no refitting; own implementation of per-trial mean |SMD| over the 54 non-coded items, paired item masking, ratio-of-means
relative reduction, 4,000-resample trial bootstrap with seed 20261001, exact one-/two-sided sign-flip);
(2) impact of masking near-duplicate held-out items for PS-Clinical (docs/v2_planning/LESSONS_FROM_V1.md §1):
   strict = pp_LVFUNC__ef (echo EF ~ LVEF in PS-Clinical), pp_LAB__egfr (f(creatinine, age, sex), all in PS-Clinical)
   broad  = strict + pp_LAB__bun, pp_LVFUNC__lv_sys_grade
Aggregates only (trial-level means over 32 trials); writes OUT/remask.csv."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v21")
import paper2_grid as G
SP = G.SP
OUT = SP.A / "claude-v1-audit" / "code"
R = pd.read_parquet(G.OUT / "restricted_cells.parquet")
VN, NONC = G.VN, G.NONCODED

def smd_block(rg, cfg, arm, extra_mask=()):
    g = R[(R.rung == rg) & (R.config == cfg) & (R.arm == arm)].set_index("trial")
    S = g[[f"smd:{c}" for c in VN]].abs()
    S.columns = VN
    for t, ex in g.ex58.fillna("").items():
        for c in filter(None, ex.split(";")):
            S.loc[t, c] = np.nan
    for c in extra_mask:
        S[c] = np.nan
    return S[NONC]

def signflip(d, two):
    d = d[np.isfinite(d)]
    p1 = SP.V.signflip_1s(d)
    return min(1.0, 2 * min(p1, SP.V.signflip_1s(-d))) if two else p1

def contrast(ka, kb, tr, two, ma=(), mb=()):
    Sa, Sb = smd_block(*ka, extra_mask=ma).loc[tr], smd_block(*kb, extra_mask=mb).loc[tr]
    m = Sa.isna() | Sb.isna()
    a, b = Sa.mask(m).mean(1), Sb.mask(m).mean(1)
    est = 100 * (1 - a.mean() / b.mean())
    rng = np.random.default_rng(SP.SEED)
    I = rng.integers(0, len(a), size=(SP.NB, len(a)))
    bs = 100 * (1 - a.to_numpy()[I].mean(1) / b.to_numpy()[I].mean(1))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    d = (b - a).to_numpy()
    return dict(m54_b=b.mean(), m54_a=a.mean(), relred54=est, lo=lo, hi=hi, better=f"{int((d > 0).sum())}/{len(d)}", p=signflip(d, two))

S32 = SP.S32
H = pd.read_csv(G.OUT / "sensitivity.csv")
rows = []
spec = [("P5: ECG vs base", ("P5", "main", "ECG"), ("P5", "main", "base"), False),
        ("P5: CLMBR vs base", ("P5", "main", "CLMBR"), ("P5", "main", "base"), False),
        ("P5: ECG+CLMBR vs base", ("P5", "main", "ECG+CLMBR"), ("P5", "main", "base"), False),
        ("P1+CLMBR vs Flags base", ("P1", "main", "CLMBR"), ("Flags", "main", "base"), True)]
for lab, ka, kb, two in spec:
    r = contrast(ka, kb, S32, two)
    ref = H[(H.set == "S32") & (H.config == "main") & (H.contrast == lab)].iloc[0]
    rows.append(dict(check="reproduce", contrast=lab, mask="as published", **r, pub_relred54=ref.relred54, pub_lo=ref.relred54_lo,
                     pub_hi=ref.relred54_hi, pub_p=ref.m54_p))
STRICT = ["pp_LVFUNC__ef", "pp_LAB__egfr"]
BROAD = STRICT + ["pp_LAB__bun", "pp_LVFUNC__lv_sys_grade"]
for cfg in SP.CONFIGS:
    for lab, ka, kb, two in [("P5+CLMBR vs clinical base", ("P5", cfg, "CLMBR"), ("clinical", cfg, "base"), True),
                             ("P5+ECG+CLMBR vs clinical base", ("P5", cfg, "ECG+CLMBR"), ("clinical", cfg, "base"), True),
                             ("clinical: ECG vs base", ("clinical", cfg, "ECG"), ("clinical", cfg, "base"), False),
                             ("clinical: CLMBR vs base", ("clinical", cfg, "CLMBR"), ("clinical", cfg, "base"), False)]:
        ref = H[(H.set == "S32") & (H.config == cfg) & (H.contrast == lab)].iloc[0]
        for mname, mk in (("as published", ()), ("strict", STRICT), ("broad", BROAD)):
            ma = mk if ka[0] == "clinical" else ()
            r = contrast(ka, kb, S32, two, ma=ma, mb=mk)
            rows.append(dict(check=f"clinical remask {cfg}", contrast=lab, mask=mname, **r, pub_relred54=ref.relred54,
                             pub_lo=ref.relred54_lo, pub_hi=ref.relred54_hi, pub_p=ref.m54_p))
D = pd.DataFrame(rows)
os.umask(0o077); OUT.mkdir(parents=True, exist_ok=True)
D.to_csv(OUT / "remask.csv", index=False)
pd.set_option("display.width", 250)
print(D.round(4).to_string(index=False))
