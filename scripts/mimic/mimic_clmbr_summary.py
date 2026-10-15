#!/usr/bin/env python
"""Step 3 endpoints from OUT/results/<k>_{arms,vars}.csv (aggregates only; no pair counts, retention or ESS per trial).

Sets: primary7 (the 7 cardiovascular trials; mimic_summary.SETS), all8 (+ PEPTIC, sensitivity); PEPTIC reported alone.
Leakage mask (pipeline.md section 6, applied to the CLMBR-T arms): CLMBR-T reads coded visits (Visit/IP, Visit/ER with
their times), so the 4 utilisation items of block D (prior admissions and ED visits in 365 d, days from admission to
t0, ICU before t0) are derivable from its input and are masked whenever a CLMBR-T arm (real or permuted) is in either
compared cell. A code-only model also sees which labs were ordered; that touches only the lab missingness indicators
(secondary panel, not used here). Lab and vital VALUES are not in the code-only input and are kept, as at Yale (the
54-item panel is unmasked for CLMBR-T). Items enter a contrast only where observed in both cells.
Endpoints per contrast (a vs b): relative reduction 1 - mean_t(m_a) / mean_t(m_b) in the per-trial mean |SMD| with a
4,000-resample trial-bootstrap CI (seed 20261001); trials lower; exact sign-flip P (one-sided for a representation vs
its base or placebo, two-sided for placebo vs base and head-to-heads); % |SMD| < 0.1 (mean of per-trial %); mean
|d log HR| vs the RCT, trials closer, sign-flip P and the benchmark-permutation P (20,000 draws, seed 0). Cells with
< 11 pairs are failed and drop that trial from the contrast; the overlap rule (>= 30% of the smaller arm matched or
>= 50 pairs) is a cell-validity check (counts reported).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from mimic_common import OUT, relred_ci, status
import mimic_replication as M  # noqa: E402
import mimic_summary as MS  # noqa: E402

RES = OUT / "results"
SUM = OUT / "summary"
TRIALS = M.BUILT + M.NEW
P7 = MS.SETS["primary7"]
CLM = {"CLMBR", "ECG+CLMBR", "permCLMBR"}
MASK_CLMBR_BLOCKS = {"D"}
CONTRASTS = [  # (label, arm a, arm b, sided)
    ("+ ECG vs PS-CVD5", "ECG", "base", "one"),
    ("+ CLMBR-T vs PS-CVD5", "CLMBR", "base", "one"),
    ("+ ECG + CLMBR-T vs PS-CVD5", "ECG+CLMBR", "base", "one"),
    ("+ ECG + CLMBR-T vs + CLMBR-T", "ECG+CLMBR", "CLMBR", "one"),
    ("+ ECG + CLMBR-T vs + ECG", "ECG+CLMBR", "ECG", "one"),
    ("+ CLMBR-T vs + ECG", "CLMBR", "ECG", "two"),
    ("+ ECG vs + permuted ECG", "ECG", "permECG", "one"),
    ("+ CLMBR-T vs + permuted CLMBR-T", "CLMBR", "permCLMBR", "one"),
    ("+ permuted ECG vs PS-CVD5", "permECG", "base", "two"),
    ("+ permuted CLMBR-T vs PS-CVD5", "permCLMBR", "base", "two"),
]
YALE_LABEL = {"+ ECG vs PS-CVD5": "P5: ECG vs base", "+ CLMBR-T vs PS-CVD5": "P5: CLMBR vs base",
              "+ ECG + CLMBR-T vs PS-CVD5": "P5: ECG+CLMBR vs base", "+ ECG + CLMBR-T vs + CLMBR-T": "P5: ECG+CLMBR vs CLMBR",
              "+ ECG + CLMBR-T vs + ECG": "P5: ECG+CLMBR vs ECG", "+ CLMBR-T vs + ECG": "P5: CLMBR vs ECG",
              "+ ECG vs + permuted ECG": "P5: ECG vs shufECG", "+ CLMBR-T vs + permuted CLMBR-T": "P5: CLMBR vs shufCLMBR",
              "+ permuted ECG vs PS-CVD5": "P5: shufECG vs base", "+ permuted CLMBR-T vs PS-CVD5": "P5: shufCLMBR vs base"}
YALE_S31 = OUT.parent / "claude-s31-20261014/summary_v1/contrasts.csv"


def signflip(d, sided):
    d = np.asarray([x for x in d if np.isfinite(x)])
    if not len(d):
        return np.nan
    if sided == "one":
        return M.exact_signflip(d)
    k = len(d)
    s = np.array(np.meshgrid(*[[-1, 1]] * k)).reshape(k, -1).T
    return float(np.mean(np.abs((s * np.abs(d)).mean(1)) >= abs(d.mean()) - 1e-12))


def bshuf(la, lb, rb, ndraw=20000):
    """Benchmark permutation (as scripts/v20/sens_primary32.bshuf): stat = mean(|la - q| - |lb - q|), RCT results
    reassigned across trials; one-sided P(null <= obs) (a closer)."""
    st = lambda q: np.mean(np.abs(la - q) - np.abs(lb - q), axis=-1)
    obs = float(st(rb))
    rng = np.random.default_rng(0)
    IX = np.array([rng.permutation(len(rb)) for _ in range(ndraw)])
    return float((st(rb[IX]) <= obs + 1e-12).mean())


def load():
    A = pd.concat([pd.read_csv(RES / f"{k}_arms.csv") for k in TRIALS], ignore_index=True)
    V = pd.concat([pd.read_csv(RES / f"{k}_vars.csv") for k in TRIALS], ignore_index=True)
    A["failed"] = A.n_pairs < 11
    A["overlap_ok"] = (A.retention >= 0.30) | (A.n_pairs >= 50)
    return A, V


def mask_items(V, a, b, masked=True):
    blocks = MASK_CLMBR_BLOCKS if masked and ({a, b} & CLM) else set()
    return V[~V.block.isin(blocks)]


def contrast(A, V, trials, a, b, base="cvd5", pop="all", sided="one", masked=True, drop_invalid=False):
    S = A[(A.base == base) & (A["pop"] == pop) & A.trial.isin(trials)].set_index(["trial", "arm"])
    W = mask_items(V[(V.base == base) & (V["pop"] == pop) & V.trial.isin(trials)], a, b, masked)
    rows = []
    for t in trials:
        if (t, a) not in S.index or (t, b) not in S.index:
            continue
        ca, cb = S.loc[(t, a)], S.loc[(t, b)]
        if ca.failed or cb.failed or (drop_invalid and not (ca.overlap_ok and cb.overlap_ok)):
            continue
        va = W[(W.trial == t) & (W.arm == a)].set_index("var").abs_smd
        vb = W[(W.trial == t) & (W.arm == b)].set_index("var").abs_smd.reindex(va.index)
        ok = va.notna() & vb.notna()
        rows.append(dict(trial=t, m_a=va[ok].mean(), m_b=vb[ok].mean(), p_a=100 * (va[ok] < 0.1).mean(),
                         p_b=100 * (vb[ok] < 0.1).mean(), n_items=int(ok.sum()),
                         e_a=abs(ca.loghr - ca.rct_loghr), e_b=abs(cb.loghr - cb.rct_loghr),
                         la=ca.loghr, lb=cb.loghr, rb=ca.rct_loghr))
    R = pd.DataFrame(rows)
    est, lo, hi = relred_ci(R.m_b, R.m_a)
    d = (R.m_b - R.m_a).to_numpy()
    dp = (R.p_a - R.p_b).to_numpy()
    de = (R.e_b - R.e_a).dropna()
    g = R.dropna(subset=["la", "lb"])
    return dict(k=len(R), items=f"{int(R.n_items.min())}-{int(R.n_items.max())}", m_a=float(R.m_a.mean()), m_b=float(R.m_b.mean()),
                relred=est, lo=lo, hi=hi, lower=f"{int((d > 0).sum())}/{len(d)}", p=signflip(d, sided), sided=sided,
                pct_a=float(R.p_a.mean()), pct_b=float(R.p_b.mean()), dpts=float(dp.mean()),
                better_pts=f"{int((dp > 0).sum())}/{len(dp)}", p_pts=signflip(dp, sided),
                absd_a=float(g.e_a.mean()), absd_b=float(g.e_b.mean()), closer=f"{int((de > 0).sum())}/{len(de)}",
                p_closer=signflip(de.to_numpy(), sided),
                p_bshuf=bshuf(g.la.to_numpy(), g.lb.to_numpy(), g.rb.to_numpy()) if len(g) > 2 else np.nan)


def agreement(A, trials, base="cvd5", pop="all"):
    out = {}
    for arm in ["base", "ECG", "CLMBR", "ECG+CLMBR", "permECG", "permCLMBR"]:
        s = A[(A.base == base) & (A["pop"] == pop) & (A.arm == arm) & A.trial.isin(trials) & ~A.failed]
        s = s[np.isfinite(s.loghr) & np.isfinite(s.se)]
        b, se, rb, rs = s.loghr, s.se, s.rct_loghr, s.rct_se
        out[arm] = dict(k=len(s), r=float(np.corrcoef(b, rb)[0, 1]), est_agree=f"{int((np.abs(b - rb) <= 1.96 * rs).sum())}/{len(s)}",
                        std_agree=f"{int((np.abs(b - rb) / np.sqrt(se ** 2 + rs ** 2) < 1.96).sum())}/{len(s)}",
                        mean_abs_dloghr=float(np.mean(np.abs(b - rb))))
    return out


def peptic(A, V, base="cvd5"):
    out = {}
    for arm in ["base", "ECG", "CLMBR", "ECG+CLMBR", "permECG", "permCLMBR"]:
        r = A[(A.trial == "peptic") & (A.base == base) & (A["pop"] == "all") & (A.arm == arm)].iloc[0]
        v = mask_items(V[(V.trial == "peptic") & (V.base == base) & (V["pop"] == "all") & (V.arm == arm)], arm, arm)
        v = v.abs_smd.dropna()
        out[arm] = dict(hr=float(np.exp(r.loghr)), lo=float(np.exp(r.loghr - 1.96 * r.se)), hi=float(np.exp(r.loghr + 1.96 * r.se)),
                        pct_bal=float(100 * (v < 0.1).mean()), mean_smd=float(v.mean()), failed=bool(r.failed),
                        rct=float(np.exp(r.rct_loghr)))
    return out


def validity(A):
    out = {}
    for (base, pop), g in A.groupby(["base", "pop"]):
        out[f"{base}|{pop}"] = dict(cells=len(g), failed_lt11_pairs=int(g.failed.sum()), overlap_invalid=int((~g.overlap_ok).sum()),
                                    retention_bands={arm: dict(lt30=int((h.retention < .3).sum()), r30_50=int(((h.retention >= .3) & (h.retention < .5)).sum()),
                                                               r50_90=int(((h.retention >= .5) & (h.retention < .9)).sum()), ge90=int((h.retention >= .9).sum()))
                                                     for arm, h in g.groupby("arm")},
                                    median_c_insample={arm: round(float(h.c_insample.median()), 3) for arm, h in g.groupby("arm")},
                                    cells_with_extreme_ps_over_10pct=int((g.share_extreme_ps > 0.10).sum()))
    return out


def yale():
    if not YALE_S31.exists():
        return {}
    C = pd.read_csv(YALE_S31)
    C = C[(C.set == "S31") & (C.config == "main")].set_index("contrast")
    out = {}
    for lab, y in YALE_LABEL.items():
        if y in C.index:
            r = C.loc[y]
            out[lab] = dict(relred=float(r.relred54), lo=float(r.relred54_lo), hi=float(r.relred54_hi), lower=r.m54_better,
                            p=float(r.m54_p), pct_a=float(r.lt01_54_a), pct_b=float(r.lt01_54_b), absd_a=float(r.absd_a),
                            absd_b=float(r.absd_b), closer=r.absd_better, p_bshuf=float(r.bshuf_p), k=int(r.n_trials))
    return out


def main():
    A, V = load()
    S = dict(contrasts={}, agreement={}, peptic={}, validity=validity(A), yale_s31=yale(), gates={})
    for setname, tr in (("primary7", P7), ("all8", TRIALS)):
        for base, pop in (("cvd5", "all"), ("cvd5", "no_index_day_ecg"), ("cvd5_anydm", "all"), ("cvd5_incl", "all")):
            for lab, a, b, sided in CONTRASTS:
                S["contrasts"][f"{setname}|{base}|{pop}|{lab}"] = contrast(A, V, tr, a, b, base, pop, sided)
            S["agreement"][f"{setname}|{base}|{pop}"] = agreement(A, tr, base, pop)
    for lab, a, b, sided in CONTRASTS:  # sensitivities of the primary cell: unmasked panel; overlap-invalid cells dropped
        S["contrasts"][f"primary7|cvd5|all|{lab}|unmasked"] = contrast(A, V, P7, a, b, sided=sided, masked=False)
        S["contrasts"][f"primary7|cvd5|all|{lab}|overlap_valid_only"] = contrast(A, V, P7, a, b, sided=sided, drop_invalid=True)
    for base in ("cvd5", "cvd5_anydm", "cvd5_incl"):
        S["peptic"][base] = peptic(A, V, base)
    # gates: the +ECG point estimates equal the v21 published values (same cells, same panel)
    v21 = json.load(open(OUT.parent / "claude-v21-paper2/mimic/summary/summary.json"))["balance"]
    gate = {}
    for base, pop in (("cvd5", "all"), ("cvd5", "no_index_day_ecg"), ("cvd5_anydm", "all"), ("cvd5_incl", "all")):
        c = S["contrasts"][f"primary7|{base}|{pop}|+ ECG vs PS-CVD5"]
        ref = v21[f"primary7|{base}|{pop}"]
        gate[f"{base}|{pop}"] = dict(relred=c["relred"], v21=ref["relred_ECG"], pct=(c["pct_b"], c["pct_a"]),
                                     v21_pct=(ref["pct_bal_base"], ref["pct_bal_ECG"]),
                                     ok=bool(abs(c["relred"] - ref["relred_ECG"]) < 1e-9 and abs(c["pct_a"] - ref["pct_bal_ECG"]) < 1e-9
                                             and abs(c["pct_b"] - ref["pct_bal_base"]) < 1e-9))
    S["gates"]["ecg_point_estimates_equal_v21"] = gate
    S["gates"]["v21_cells"] = json.load(open(RES / "gate_v21.json"))
    SUM.mkdir(parents=True, exist_ok=True)
    json.dump(S, open(SUM / "summary.json", "w"), indent=1, default=float)
    write_tables(S)
    ok = all(g["ok"] for g in gate.values()) and S["gates"]["v21_cells"]["gate"] == "PASS"
    c = S["contrasts"]
    status("step 3 summary written; gates " + ("PASS" if ok else "FAIL") + "; primary7: " + "; ".join(
        f"{lab} {c[f'primary7|cvd5|all|{lab}']['relred']:.1f}% ({c[f'primary7|cvd5|all|{lab}']['lo']:.1f} to {c[f'primary7|cvd5|all|{lab}']['hi']:.1f})"
        for lab, *_ in CONTRASTS[:4]))
    return 0 if ok else 1


def f1(x):
    return "—" if x is None or not np.isfinite(x) else f"{x:.1f}"


def fp(p):
    return "—" if p is None or not np.isfinite(p) else ("<.001" if p < 0.001 else f"{p:.3f}".replace("0.", ".", 1))


def write_tables(S):
    L = ["# MIMIC-IV CLMBR-T external validation: generated tables (aggregates only)", ""]
    L += ["## Balance contrasts (26-item held-out panel; utilisation masked for CLMBR-T arms)", "",
          "| Set | Base | Population | Contrast | k | items | mean \\|SMD\\| b → a | rel. red. % (95% CI) | lower | P | % <0.1 b → a | Δ pts (better; P) | \\|Δ log HR\\| b → a | closer (P) | bench.-perm. P |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, c in S["contrasts"].items():
        parts = key.split("|")
        s, base, pop, lab = parts[:4]
        if len(parts) == 5:
            lab = f"{lab} [{parts[4]}]"
        L.append(f"| {s} | {base} | {pop} | {lab} | {c['k']} | {c['items']} | {c['m_b']:.3f} → {c['m_a']:.3f} | {f1(c['relred'])} ({f1(c['lo'])} to {f1(c['hi'])}) | "
                 f"{c['lower']} | {fp(c['p'])} ({c['sided']}) | {c['pct_b']:.1f} → {c['pct_a']:.1f} | {c['dpts']:+.1f} ({c['better_pts']}; {fp(c['p_pts'])}) | "
                 f"{c['absd_b']:.3f} → {c['absd_a']:.3f} | {c['closer']} ({fp(c['p_closer'])}) | {fp(c['p_bshuf'])} |")
    L += ["", "## RCT agreement by arm", "", "| Set | Base | Population | Arm | k | r | estimate agreement | std-diff agreement | mean \\|Δ log HR\\| |",
          "|---|---|---|---|---|---|---|---|---|"]
    for key, ag in S["agreement"].items():
        s, base, pop = key.split("|")
        for arm, g in ag.items():
            L.append(f"| {s} | {base} | {pop} | {arm} | {g['k']} | {g['r']:.2f} | {g['est_agree']} | {g['std_agree']} | {g['mean_abs_dloghr']:.3f} |")
    L += ["", "## PEPTIC (negative control; RCT RR 1.05)", "", "| Base | Arm | HR (95% CI) | % \\|SMD\\| < 0.1 | mean \\|SMD\\| |", "|---|---|---|---|---|"]
    for base, P in S["peptic"].items():
        for arm, g in P.items():
            L.append(f"| {base} | {arm} | {g['hr']:.2f} ({g['lo']:.2f}–{g['hi']:.2f}) | {g['pct_bal']:.1f} | {g['mean_smd']:.3f} |")
    L += ["", "## Cell validity (counts of cells; no per-trial values)", "", "```", json.dumps(S["validity"], indent=1), "```",
          "", "## Yale s31 (54 items; PS-CVD5; main configuration)", "", "| Contrast | k | rel. red. % (95% CI) | lower | P | % <0.1 b → a | \\|Δ log HR\\| b → a | closer | bench.-perm. P |",
          "|---|---|---|---|---|---|---|---|---|"]
    for lab, y in S["yale_s31"].items():
        L.append(f"| {lab} | {y['k']} | {f1(y['relred'])} ({f1(y['lo'])} to {f1(y['hi'])}) | {y['lower']} | {fp(y['p'])} | {y['pct_b']:.1f} → {y['pct_a']:.1f} | "
                 f"{y['absd_b']:.3f} → {y['absd_a']:.3f} | {y['closer']} | {fp(y['p_bshuf'])} |")
    L += ["", "## Gates", "", "```", json.dumps(S["gates"], indent=1, default=float), "```"]
    (SUM / "tables.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
