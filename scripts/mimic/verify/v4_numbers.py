"""Verifier check 4: recompute the headline numbers of docs/mimic/MIMIC_EXTERNAL_VALIDATION.md from the restricted
cells with an independent implementation. Prints doc value vs recomputed value (aggregates only; no per-trial
pair counts, retention or ESS). Writes the comparison table to OUT/verify/numbers.csv (aggregates only)."""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

os.umask(0o077)
OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
AUD = "/mnt/raid0/rbc58/ecg-tte/audits"
P7 = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2"]
ALL8 = P7 + ["peptic"]
CLM = {"CLMBR", "ECG+CLMBR", "permCLMBR"}
SIGNS = {k: np.array(list(itertools.product([-1, 1], repeat=k)), float) for k in (7, 8)}
PERMS = {k: np.array(list(itertools.permutations(range(k)))) for k in (7,)}


def load(res):
    A = pd.concat([pd.read_csv(f"{OUT}/{res}/{k}_arms.csv") for k in ALL8], ignore_index=True)
    V = pd.concat([pd.read_csv(f"{OUT}/{res}/{k}_vars.csv") for k in ALL8], ignore_index=True)
    return A, V


def sflip(d, sided):
    d = np.asarray(d, float)
    null = SIGNS[len(d)] @ np.abs(d) / len(d)
    if sided == "one":
        return float(np.mean(null >= d.mean() - 1e-12))
    return float(np.mean(np.abs(null) >= abs(d.mean()) - 1e-12))


def boot(mb, ma):
    rng = np.random.default_rng(20261001)
    I = rng.integers(0, len(mb), size=(4000, len(mb)))
    r = 100 * (1 - ma[I].mean(1) / mb[I].mean(1))
    return np.percentile(r, [2.5, 97.5])


def bperm_exact(la, lb, rb):
    obs = np.mean(np.abs(la - rb) - np.abs(lb - rb))
    if len(rb) not in PERMS:
        return np.nan
    Q = rb[PERMS[len(rb)]]
    null = np.mean(np.abs(la - Q) - np.abs(lb - Q), axis=1)
    return float(np.mean(null <= obs + 1e-12))


def contrast(A, V, a, b, trials=P7, base="cvd5", pop="all", sided="one", masked=True):
    ma, mb, pa, pb, ea, eb, la, lb, rb, nit = [], [], [], [], [], [], [], [], [], []
    for t in trials:
        ca = A[(A.trial == t) & (A.base == base) & (A["pop"] == pop) & (A.arm == a)]
        cb = A[(A.trial == t) & (A.base == base) & (A["pop"] == pop) & (A.arm == b)]
        assert len(ca) == 1 and len(cb) == 1
        ca, cb = ca.iloc[0], cb.iloc[0]
        if ca.n_pairs < 11 or cb.n_pairs < 11:
            continue
        va = V[(V.trial == t) & (V.base == base) & (V["pop"] == pop) & (V.arm == a)].set_index("var")
        vb = V[(V.trial == t) & (V.base == base) & (V["pop"] == pop) & (V.arm == b)].set_index("var")
        assert va.index.equals(vb.index)
        keep = np.isfinite(va.abs_smd.to_numpy(float)) & np.isfinite(vb.abs_smd.to_numpy(float))
        if masked and ({a, b} & CLM):
            keep &= (va.block != "D").to_numpy()
        xa, xb = va.abs_smd.to_numpy(float)[keep], vb.abs_smd.to_numpy(float)[keep]
        ma.append(xa.mean()); mb.append(xb.mean()); nit.append(int(keep.sum()))
        pa.append(100 * np.mean(xa < 0.1)); pb.append(100 * np.mean(xb < 0.1))
        ea.append(abs(ca.loghr - ca.rct_loghr)); eb.append(abs(cb.loghr - cb.rct_loghr))
        la.append(ca.loghr); lb.append(cb.loghr); rb.append(ca.rct_loghr)
    ma, mb, ea, eb, la, lb, rb = map(lambda x: np.asarray(x, float), (ma, mb, ea, eb, la, lb, rb))
    rr = 100 * (1 - ma.mean() / mb.mean())
    lo, hi = boot(mb, ma)
    return dict(k=len(ma), items=(min(nit), max(nit)), rr=rr, lo=lo, hi=hi, lower=f"{int((ma < mb).sum())}/{len(ma)}",
                p=sflip(mb - ma, sided), pct_b=np.mean(pb), pct_a=np.mean(pa), ab=eb.mean(), aa=ea.mean(),
                closer=f"{int((ea < eb).sum())}/{len(ea)}", p_closer=sflip(eb - ea, sided), bperm=bperm_exact(la, lb, rb))


def agreement(A, arm, trials=P7, base="cvd5", pop="all"):
    s = A[(A.base == base) & (A["pop"] == pop) & (A.arm == arm) & A.trial.isin(trials)]
    b, se, rb, rs = (s[c].to_numpy(float) for c in ("loghr", "se", "rct_loghr", "rct_se"))
    return dict(r=np.corrcoef(b, rb)[0, 1], ea=f"{int((np.abs(b - rb) <= 1.96 * rs).sum())}/{len(b)}",
                sa=f"{int((np.abs(b - rb) / np.sqrt(se ** 2 + rs ** 2) < 1.96).sum())}/{len(b)}", m=np.mean(np.abs(b - rb)))


def peptic(A, V, arm, base="cvd5"):
    r = A[(A.trial == "peptic") & (A.base == base) & (A["pop"] == "all") & (A.arm == arm)].iloc[0]
    v = V[(V.trial == "peptic") & (V.base == base) & (V["pop"] == "all") & (V.arm == arm)]
    if arm in CLM:
        v = v[v.block != "D"]
    x = v.abs_smd.dropna().to_numpy(float)
    return dict(hr=np.exp(r.loghr), lo=np.exp(r.loghr - 1.96 * r.se), hi=np.exp(r.loghr + 1.96 * r.se),
                pct=100 * np.mean(x < 0.1), m=x.mean(), n=len(x))


ROWS = []


def chk(label, doc, got, nd=1, kind="num"):
    if kind == "num":
        g = round(float(got), nd)
        ok = abs(g - float(doc)) < 1e-9
        gs = f"{g:.{nd}f}"
    else:
        gs = str(got)
        ok = gs == str(doc)
    ROWS.append(dict(item=label, doc=str(doc), recomputed=gs, match="yes" if ok else "**NO**"))


def fmtp(p):
    return round(p, 3)


A, V = load("results")
Ap, Vp = load("results_prior")

# cell validity
for nm, AA in (("primary", A), ("prior", Ap)):
    print(nm, "cells", len(AA), "failed (<11 pairs)", int((AA.n_pairs < 11).sum()),
          "overlap-invalid", int((~((AA.retention >= 0.3) | (AA.n_pairs >= 50))).sum()),
          "cells with NaN loghr", int(AA.loghr.isna().sum()))
g = A[(A.base == "cvd5") & (A["pop"] == "all")]
for arm in ("base", "ECG", "CLMBR", "ECG+CLMBR", "permECG", "permCLMBR"):
    h = g[g.arm == arm]
    print(f"  cvd5|all {arm}: cells {len(h)}; retention bands <30 {int((h.retention < .3).sum())}, 30-50 {int(((h.retention >= .3) & (h.retention < .5)).sum())},"
          f" 50-90 {int(((h.retention >= .5) & (h.retention < .9)).sum())}, >=90 {int((h.retention >= .9).sum())}; median C {h.c_insample.median():.3f}")
chk("C median PS-CVD5", 0.662, g[g.arm == "base"].c_insample.median(), 3)
chk("C median + ECG", 0.704, g[g.arm == "ECG"].c_insample.median(), 3)
chk("C median + CLMBR-T", 0.793, g[g.arm == "CLMBR"].c_insample.median(), 3)
chk("C median + both", 0.807, g[g.arm == "ECG+CLMBR"].c_insample.median(), 3)
h = g[g.arm == "CLMBR"]; chk("+CLMBR-T cells retaining 50-90%", "1 of 8", f"{int(((h.retention >= .5) & (h.retention < .9)).sum())} of {len(h)}", kind="s")
h = g[g.arm == "ECG+CLMBR"]; chk("+both cells retaining 50-90%", "3 of 8", f"{int(((h.retention >= .5) & (h.retention < .9)).sum())} of {len(h)}", kind="s")
others = g[~g.arm.isin(["CLMBR", "ECG+CLMBR"])]
chk("all other cvd5|all cells retain >=90%", "True", bool((others.retention >= .9).all()), kind="s")
chk("CLMBR/both cells not in 50-90 retain >=90%", "True",
    bool((g[g.arm.isin(["CLMBR", "ECG+CLMBR"]) & ~((g.retention >= .5) & (g.retention < .9))].retention >= .9).all()), kind="s")
print("  item counts: unmasked", sorted(V[(V.base == "cvd5") & (V["pop"] == "all") & (V.arm == "base")].groupby("trial").size().unique()),
      "blocks", V[(V.trial == "plato") & (V.base == "cvd5") & (V["pop"] == "all") & (V.arm == "base")].block.value_counts().to_dict())

# primary contrasts
DOC = [  # label, a, b, sided, rr, lo, hi, lower, p, pct_b, pct_a, absd_b, absd_a, closer
    ("+ECG vs base", "ECG", "base", "one", 6.6, 2.4, 13.1, "6/7", .016, 45.6, 51.6, .344, .326, "4/7"),
    ("+CLMBR vs base", "CLMBR", "base", "one", 23.1, 16.0, 28.9, "7/7", .008, 44.2, 57.8, .344, .260, "6/7"),
    ("+both vs base", "ECG+CLMBR", "base", "one", 29.0, 21.6, 37.1, "7/7", .008, 44.2, 64.3, .344, .249, "6/7"),
    ("+both vs +CLMBR", "ECG+CLMBR", "CLMBR", "one", 7.7, 3.0, 14.1, "6/7", .016, 57.8, 64.3, .260, .249, "3/7"),
    ("+both vs +ECG", "ECG+CLMBR", "ECG", "one", 23.6, 18.5, 27.7, "7/7", .008, 51.9, 64.3, .326, .249, "7/7"),
    ("+CLMBR vs +ECG (2s)", "CLMBR", "ECG", "two", 17.2, 9.4, 23.1, "7/7", .016, 51.9, 57.8, .326, .260, "5/7"),
    ("+ECG vs +permECG", "ECG", "permECG", "one", 9.4, 6.2, 14.0, "7/7", .008, 46.7, 51.6, .323, .326, "4/7"),
    ("+CLMBR vs +permCLMBR", "CLMBR", "permCLMBR", "one", 23.6, 14.0, 30.4, "6/7", .016, 45.5, 57.8, .317, .260, "5/7"),
    ("+permECG vs base (2s)", "permECG", "base", "two", -3.1, -5.6, -0.3, "2/7", .094, 45.6, 46.7, .344, .323, "4/7"),
    ("+permCLMBR vs base (2s)", "permCLMBR", "base", "two", -0.6, -4.6, 4.5, "3/7", .812, 44.2, 45.5, .344, .317, "2/7"),
]
C = {}
for lab, a, b, sided, rr, lo, hi, lower, p, pb, pa, ab, aa, closer in DOC:
    c = contrast(A, V, a, b, sided=sided)
    C[lab] = c
    chk(f"{lab}: rel. red.", rr, c["rr"]); chk(f"{lab}: CI lo", lo, c["lo"]); chk(f"{lab}: CI hi", hi, c["hi"])
    chk(f"{lab}: trials lower", lower, c["lower"], kind="s"); chk(f"{lab}: sign-flip P", p, c["p"], 3)
    chk(f"{lab}: % <0.1 b", pb, c["pct_b"]); chk(f"{lab}: % <0.1 a", pa, c["pct_a"])
    chk(f"{lab}: |dlogHR| b", ab, c["ab"], 3); chk(f"{lab}: |dlogHR| a", aa, c["aa"], 3)
    chk(f"{lab}: closer", closer, c["closer"], kind="s")
    print(f"  {lab}: items {c['items']}, k {c['k']}")
chk("+CLMBR vs base: P closer (doc .023)", .023, C["+CLMBR vs base"]["p_closer"], 3)
print("bench-perm P exact (doc via 20,000 random draws): +ECG", round(C["+ECG vs base"]["bperm"], 3), "+CLMBR", round(C["+CLMBR vs base"]["bperm"], 3),
      "+both", round(C["+both vs base"]["bperm"], 3))
chk("bench-perm P +ECG (exact, 2 dp)", .84, C["+ECG vs base"]["bperm"], 2)
chk("bench-perm P +CLMBR (exact, 2 dp)", .70, C["+CLMBR vs base"]["bperm"], 2)
chk("bench-perm P +both (exact, 2 dp)", .43, C["+both vs base"]["bperm"], 2)

# agreement table
for arm, r, ea, sa, m in (("base", .69, "0/7", "4/7", .344), ("ECG", .69, "1/7", "4/7", .326), ("CLMBR", .75, "1/7", "5/7", .260),
                          ("ECG+CLMBR", .76, "4/7", "6/7", .249), ("permECG", .70, "1/7", "4/7", .323), ("permCLMBR", .61, "0/7", "4/7", .317)):
    g_ = agreement(A, arm)
    chk(f"agreement {arm}: r", r, g_["r"], 2); chk(f"agreement {arm}: est agree", ea, g_["ea"], kind="s")
    chk(f"agreement {arm}: std agree", sa, g_["sa"], kind="s"); chk(f"agreement {arm}: mean |dlogHR|", m, g_["m"], 3)

# PEPTIC
for arm, hr, lo, hi, pct, m in (("base", 1.51, 1.35, 1.69, 30.8, .179), ("ECG", 1.39, 1.24, 1.55, 42.3, .155), ("CLMBR", 1.00, 0.90, 1.11, 40.9, .129),
                                ("ECG+CLMBR", 0.95, 0.85, 1.06, 54.5, .116), ("permECG", 1.60, 1.42, 1.81, 30.8, .180), ("permCLMBR", 1.43, 1.28, 1.61, 31.8, .183)):
    q = peptic(A, V, arm)
    chk(f"PEPTIC {arm}: HR", hr, q["hr"], 2); chk(f"PEPTIC {arm}: lo", lo, q["lo"], 2); chk(f"PEPTIC {arm}: hi", hi, q["hi"], 2)
    chk(f"PEPTIC {arm}: % <0.1", pct, q["pct"]); chk(f"PEPTIC {arm}: mean |SMD|", m, q["m"], 3)
    print(f"  PEPTIC {arm}: items {q['n']}")
chk("PEPTIC RCT RR", 1.05, np.exp(A[A.trial == "peptic"].rct_loghr.iloc[0]), 2)

# sensitivities
SENS = [("anydm", dict(base="cvd5_anydm"), [(11.8, 7.4, 16.9, "7/7"), (29.0, 22.2, 33.6, "7/7"), (29.4, 22.6, 35.9, "7/7"), (0.6, -5.9, 8.9, "3/7")]),
        ("incl", dict(base="cvd5_incl"), [(11.5, 7.0, 17.7, "7/7"), (24.5, 18.9, 29.4, "7/7"), (29.9, 22.4, 36.3, "7/7"), (7.2, 4.0, 11.3, "7/7")]),
        ("noidx", dict(pop="no_index_day_ecg"), [(6.5, -0.4, 13.6, "5/7"), (17.4, 9.0, 26.8, "7/7"), (25.5, 20.9, 30.1, "7/7"), (9.8, 3.3, 14.9, "6/7")]),
        ("all8", dict(trials=ALL8), [(7.6, 3.2, 13.1, "7/8"), (24.8, 17.8, 30.2, "8/8"), (30.8, 23.4, 38.1, "8/8"), (8.0, 3.7, 13.5, "7/8")]),
        ("unmasked", dict(masked=False), [(6.6, 2.4, 13.1, "6/7"), (29.1, 20.8, 35.4, "7/7"), (34.7, 27.1, 42.7, "7/7"), (7.8, 2.4, 14.7, "6/7")])]
PAIRS = [("ECG", "base"), ("CLMBR", "base"), ("ECG+CLMBR", "base"), ("ECG+CLMBR", "CLMBR")]
for nm, kw, vals in SENS:
    for (a, b), (rr, lo, hi, lower) in zip(PAIRS, vals):
        c = contrast(A, V, a, b, **kw)
        chk(f"sens {nm} {a} vs {b}: rr", rr, c["rr"]); chk(f"sens {nm} {a} vs {b}: lo", lo, c["lo"]); chk(f"sens {nm} {a} vs {b}: hi", hi, c["hi"])
        chk(f"sens {nm} {a} vs {b}: lower", lower, c["lower"], kind="s")
# CLMBR vs base positive in every trial in every variant (doc section 8)
allpos = all(contrast(A, V, "CLMBR", "base", **kw)["lower"].split("/")[0] == contrast(A, V, "CLMBR", "base", **kw)["lower"].split("/")[1]
             for _, kw, _ in SENS) and C["+CLMBR vs base"]["lower"] == "7/7"
print("CLMBR lower in every trial in the 5 listed variants + primary:", allpos)

# prior-only sensitivity
for (a, b), (rr, lo, hi, lower) in zip(PAIRS, [(6.6, 2.4, 13.1, "6/7"), (7.7, 3.0, 14.0, "6/7"), (18.6, 12.5, 26.7, "7/7"), (11.9, 6.9, 16.8, "7/7")]):
    c = contrast(Ap, Vp, a, b)
    chk(f"prior {a} vs {b}: rr", rr, c["rr"]); chk(f"prior {a} vs {b}: lo", lo, c["lo"]); chk(f"prior {a} vs {b}: hi", hi, c["hi"])
    chk(f"prior {a} vs {b}: lower", lower, c["lower"], kind="s")
c = contrast(Ap, Vp, "CLMBR", "ECG", sided="two")
chk("prior CLMBR vs ECG: rr", 0.6, c["rr"]); chk("prior CLMBR vs ECG: lo", -2.4, c["lo"]); chk("prior CLMBR vs ECG: hi", 3.3, c["hi"])
c1, c2 = contrast(Ap, Vp, "CLMBR", "base"), contrast(Ap, Vp, "ECG+CLMBR", "base")
chk("prior |dlogHR| base", .344, c1["ab"], 3); chk("prior |dlogHR| +CLMBR", .278, c1["aa"], 3); chk("prior |dlogHR| +both", .240, c2["aa"], 3)
chk("prior bench-perm P +CLMBR (exact, 2dp)", .95, c1["bperm"], 2); chk("prior bench-perm P +both (exact, 2dp)", .57, c2["bperm"], 2)
for arm, hr, lo, hi in (("CLMBR", 1.28, 1.14, 1.43), ("ECG+CLMBR", 1.21, 1.08, 1.35)):
    q = peptic(Ap, Vp, arm)
    chk(f"prior PEPTIC {arm}: HR", hr, q["hr"], 2); chk(f"prior PEPTIC {arm}: lo", lo, q["lo"], 2); chk(f"prior PEPTIC {arm}: hi", hi, q["hi"], 2)
# prior run: base/ECG/permECG cells identical to primary
d = 0.0
for kind, AA, BB in (("arms", A, Ap), ("vars", V, Vp)):
    x = AA[AA.arm.isin(["base", "ECG", "permECG"])].reset_index(drop=True)
    y = BB[BB.arm.isin(["base", "ECG", "permECG"])].reset_index(drop=True)
    num = [c for c in x.columns if pd.api.types.is_numeric_dtype(x[c])]
    d = max(d, float(np.nanmax(np.abs(x[num].to_numpy(float) - y[num].to_numpy(float)))))
print("prior vs primary: base/ECG/permECG cells max |diff|", d)

# Yale s31
Y = pd.read_csv(f"{AUD}/claude-s31-20261014/summary_v1/contrasts.csv")
Y = Y[(Y.set == "S31") & (Y.config == "main")].set_index("contrast")
for lab, yl, rr, lo, hi, lower, p in (("+ECG vs base", "P5: ECG vs base", 8.7, 4.2, 13.5, "20/31", None), ("+CLMBR vs base", "P5: CLMBR vs base", 12.9, 7.6, 18.3, "23/31", None),
                                     ("+both vs base", "P5: ECG+CLMBR vs base", 14.6, 7.7, 21.1, "23/31", None),
                                     ("+both vs +CLMBR", "P5: ECG+CLMBR vs CLMBR", 2.0, -3.5, 6.9, "18/31", .238),
                                     ("+both vs +ECG", "P5: ECG+CLMBR vs ECG", 6.6, -0.0, 12.6, "18/31", .028),
                                     ("+CLMBR vs +ECG", "P5: CLMBR vs ECG", 4.7, -1.2, 9.6, "23/31", .126),
                                     ("+ECG vs +permECG", "P5: ECG vs shufECG", 8.3, 4.0, 12.7, "24/31", None),
                                     ("+CLMBR vs +permCLMBR", "P5: CLMBR vs shufCLMBR", 11.0, 4.6, 16.7, "26/31", None),
                                     ("+permECG vs base", "P5: shufECG vs base", 0.4, -3.5, 4.3, "14/31", .834),
                                     ("+permCLMBR vs base", "P5: shufCLMBR vs base", 2.2, -2.5, 6.7, "17/31", .394)):
    r = Y.loc[yl]
    chk(f"Yale {lab}: rr", rr, r.relred54); chk(f"Yale {lab}: lo", lo, r.relred54_lo); chk(f"Yale {lab}: hi", hi, r.relred54_hi)
    chk(f"Yale {lab}: lower", lower, r.m54_better, kind="s")
    if p is not None:
        chk(f"Yale {lab}: P", p, r.m54_p, 3)
    else:
        chk(f"Yale {lab}: P <.001", "True", bool(r.m54_p < .001), kind="s")

# coverage gate
R = pd.read_parquet(f"{OUT}/meds/restricted_cohort.parquet")
An = pd.read_parquet(f"{OUT}/analysed_pids.parquet")
Ra = R.merge(An, on=["trial", "pid"])
chk("analysed patients (8 trials)", "45,107", f"{len(Ra):,}", kind="s")
chk("analysed patients (7 trials)", "37,694", f"{int((Ra.trial != 'peptic').sum()):,}", kind="s")
chk("MEDS subjects", "78,183", f"{len(R):,}", kind="s")
chk("coverage share in vocab %", 82.1, 100 * Ra.n_in_vocab.sum() / Ra.n_events.sum())
chk("in-vocab events median", 211, np.median(Ra.n_in_vocab), 0)
chk("in-vocab events Q1", 93, np.percentile(Ra.n_in_vocab, 25), 0)
chk("in-vocab events Q3", 490, np.percentile(Ra.n_in_vocab, 75), 0)
chk("no prior coded history %", 0.2, 100 * (Ra.n_in_vocab == 0).mean())
chk("> 4096 (in-vocab events) %", 1.3, 100 * (Ra.n_in_vocab > 4096).mean())
chk("no coded history outside index admission %", 14.9, 100 * (Ra.n_history == 0).mean())
st = pd.read_parquet(f"{OUT}/clmbr/full/restricted_patient_status.parquet").merge(An, on=["trial", "pid"])
print("  truncated by tokenizer (tokens_available > 4096) among analysed: %.1f%%" % (100 * (st.tokens_available > 4096).mean()))
Rp = pd.read_parquet(f"{OUT}/meds_prior/restricted_cohort.parquet")
chk("prior: birth-only %", 10.6, 100 * (Rp.n_in_vocab == 0).mean())
chk("prior: median in-vocab events", 59, np.median(Rp.n_in_vocab), 0)

# Yale coverage (s31 trials; restricted_patient_status of each code-only run)
S31 = ['comet', 'paradigm-hf-seq', 'transform-hf', 'elite-ii', 'life', 'plato', 'aristotle', 'rocket-af', 'rely',
       'emperor-preserved-v2', 'east-afnet4', 'cabana-v2', 'empa-reg', 'carolina', 'leader', 'sustain6', 'canvas',
       'tecos', 'carmelina', 'valiant', 'insight', 'affirm', 'af-chf', 'precision', 'amplify', 'lodestar',
       'prove-it', 'frail-af', 'laaos3', 'raft-af', 'active-w']
YS = []
for n in S31:
    d = f"{AUD}/comet-clmbr-full-NAyb4G2x/report" if n == "comet" else f"{AUD}/claude-{n}-clmbr-codeonly/report"
    YS.append(pd.read_parquet(f"{d}/restricted_patient_status.parquet", columns=["status", "attempted", "accepted", "tokens_available"]))
YS = pd.concat(YS, ignore_index=True)
enc = YS[YS.status == "encoded"]
chk("Yale n patients", "313,867", f"{len(YS):,}", kind="s")
chk("Yale share in vocab %", 78.5, 100 * YS.accepted.sum() / YS.attempted.sum())
chk("Yale median accepted", 308, np.median(enc.accepted), 0)
chk("Yale Q1", 104, np.percentile(enc.accepted, 25), 0)
chk("Yale Q3", 757, np.percentile(enc.accepted, 75), 0)
nh = int(YS.status.isin(["no_clinical_events", "no_tokenizer_supported_clinical_events"]).sum())
chk("Yale no prior coded history", "<11 patients", "<11 patients" if 0 < nh < 11 else f"{nh}", kind="s")
chk("Yale truncated %", 1.3, 100 * (enc.tokens_available > 4096).mean())
print("  Yale status categories (shares):", {k: round(float(v), 4) for k, v in YS.status.value_counts(normalize=True).items()})

# domain coverage (all 78,183 subjects), with the independently verified dictionary code strings
import duckdb
codes = set(json.load(open(f"{OUT}/vocab/clmbr_code_strings.json"))["codes"])
con = duckdb.connect()
con.execute("SET threads=32")
D = con.execute(f"SELECT source_domain, code, count(*) n FROM read_parquet('{OUT}/meds/data/*.parquet') WHERE code <> 'MEDS_BIRTH' GROUP BY 1, 2").df()
D["iv"] = D.code.isin(codes)
tot = D.n.sum()
for dom, val in (("diagnosis", 88.1), ("drug", 60.5), ("lab", 83.4), ("procedure", 34.8), ("visit", 100.0)):
    g_ = D[D.source_domain == dom]
    chk(f"domain coverage {dom} %", val, 100 * g_.n[g_.iv].sum() / g_.n.sum())
chk("labs share of all events %", 86, 100 * D.n[D.source_domain == "lab"].sum() / tot, 0)
chk("MEDS rows (million, incl. birth)", 43.8, con.execute(f"SELECT count(*) FROM read_parquet('{OUT}/meds/data/*.parquet')").fetchone()[0] / 1e6)

T = pd.DataFrame(ROWS)
T.to_csv(f"{OUT}/verify/numbers.csv", index=False)
print(T.to_string(index=False))
print("checked", len(T), "mismatches", int((T.match != "yes").sum()))
