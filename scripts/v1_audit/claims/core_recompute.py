#!/usr/bin/env python
"""v1 audit (claims recheck): independent recomputation of the paper2 core contrast grid from cell-level outputs.

Input (read-only): claude-v21-paper2/core/restricted_cells.parquet (+ restricted_flagscv_cells.parquet), docs/v19/quality_tiers.json,
docs/v17/trial_selection.json (comparator clusters), docs/v21/TRIAL_LABELS.json, scripts/make_acc_figure.py VARS (item groups).
Re-implemented here WITHOUT importing scripts/v20/sens_primary32.py or scripts/v21/paper2_grid.py: item pairing, mean |SMD|,
relative reduction + trial bootstrap, exact sign-flip (meet-in-the-middle), comparator-cluster p, benchmark permutation, Pearson r,
estimate / standardized-difference agreement, BH-FDR families, domain rows, label permutation tests, retention / ESS.
The resampling specs (seeds, draw counts) are taken from the Methods text (4,000 bootstrap, seed 20261001; 20,000 benchmark
permutations; 10,000 label permutations) so that values can be compared to the decimal.

Output (aggregates only): /mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/claims/core_recomputed.csv, domains_recomputed.csv,
labels_recomputed.csv, labdom_recomputed.csv, retention_recomputed.csv, flagscv_recomputed.csv, compare_vs_v21.csv.
Usage: core_recompute.py [--workers 16]
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import argparse  # noqa: E402
import ast  # noqa: E402
import json  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path("/home/rbc58/github/ecg-tte")
SRC = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/core")
OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/claims")


# ------------------------------------------------------------------ item list (parsed from source text, not imported)
def load_vars():
    src = (ROOT / "scripts/make_acc_figure.py").read_text()
    i = src.index("VARS = [")
    j = src.index("\n]\n", i)
    return ast.literal_eval(src[i + 7:j + 2])


VARS = load_vars()
VN = [c for c, _, _ in VARS]
GRP = {c: g for c, _, g in VARS}
NONC = [c for c in VN if GRP[c] != "Coded record"]
DOMS = [g for g in dict.fromkeys(GRP.values()) if g != "Coded record"]
ECHO = [c for c in VN if GRP[c].startswith("Echo:")]
assert len(VN) == 58 and len(NONC) == 54

CONFIGS = ["main", "cal01", "m13", "iptw", "overlap", "gbm"]
RUNGS = ["P1", "P5", "Flags", "hdPS200", "clinical"]


# ------------------------------------------------------------------ statistics (independent implementations)
def subset_sums(a):
    s = np.zeros(1)
    for v in a:
        s = np.concatenate([s + v, s - v])
    return s


def signflip_ge(d):
    """exact P(sum of randomly signed |d| >= sum(d)); NaNs dropped."""
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    k = len(d)
    if k == 0:
        return np.nan
    a = np.abs(d)
    obs = d.sum()
    tol = 1e-10 * max(a.sum(), 1e-300)
    h = k // 2
    L = subset_sums(a[:h])
    Rs = np.sort(subset_sums(a[h:]))
    # count pairs with L + R >= obs - tol
    cnt = len(Rs) * len(L) - np.searchsorted(Rs, obs - tol - L, side="left").sum()
    return cnt / 2.0 ** k


def p_one(d):
    return signflip_ge(d)


def p_two(d):
    d = np.asarray(d, float)
    return min(1.0, 2 * min(signflip_ge(d), signflip_ge(-d)))


def boot_relred(b, a, nb=4000, seed=20261001):
    b, a = np.asarray(b, float), np.asarray(a, float)
    ok = np.isfinite(b) & np.isfinite(a)
    b, a = b[ok], a[ok]
    est = 100 * (1 - a.mean() / b.mean())
    g = np.random.default_rng(seed)
    I = g.integers(0, len(b), size=(nb, len(b)))
    bs = 100 * (1 - a[I].mean(1) / b[I].mean(1))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return est, lo, hi, int(ok.sum())


_PERM = {}


def perms(k, ndraw=20000):
    if k not in _PERM:
        g = np.random.default_rng(0)
        _PERM[k] = np.array([g.permutation(k) for _ in range(ndraw)])
    return _PERM[k]


def bench_perm(la, lb, rb, two=False):
    ok = np.isfinite(la) & np.isfinite(lb)
    la, lb, rb = la[ok], lb[ok], rb[ok]
    stat = lambda q: np.mean(np.abs(la - q) - np.abs(lb - q), axis=-1)
    obs = float(stat(rb))
    null = stat(rb[perms(len(rb))])
    lo_ = (null <= obs + 1e-12).mean()
    if not two:
        return float(lo_)
    return float(min(1.0, 2 * min(lo_, (null >= obs - 1e-12).mean())))


def bh(p):
    p = np.asarray(p, float)
    q = np.full(len(p), np.nan)
    ok = np.isfinite(p)
    v = p[ok]
    m = len(v)
    if m:
        o = np.argsort(v)
        adj = v[o] * m / np.arange(1, m + 1)
        adj = np.minimum.accumulate(adj[::-1])[::-1]
        r = np.empty(m)
        r[o] = np.minimum(adj, 1)
        q[ok] = r
    return q


# ------------------------------------------------------------------ data
def load():
    R = pd.read_parquet(SRC / "restricted_cells.parquet")
    order = R.drop_duplicates("trial").sort_values("idx").trial.tolist()
    key = dict(R.drop_duplicates("trial")[["trial", "key"]].to_numpy())
    tiers = {t["key"]: t["tier"].split(" - ")[0] for t in json.load(open(ROOT / "docs/v19/quality_tiers.json"))["trials"]}
    S38 = order
    S32 = [t for t in order if tiers[key[t]] != "Limited"]
    cl = json.load(open(ROOT / "docs/v17/trial_selection.json"))["comparator_clusters"]["clusters"]
    clk = {k: c for c, ks in cl.items() for k in ks}
    CL = {t: clk[key[t]] for t in order}
    return R, order, key, tiers, S32, S38, CL


def blocks(R, order):
    B = {}
    for (rg, cfg, a), g in R.groupby(["rung", "config", "arm"]):
        present = set(g.trial)
        g = g.set_index("trial").reindex([t for t in order if t in present])
        S = g[[f"smd:{c}" for c in VN]].abs()
        S.columns = VN
        for t, ex in g.ex58.fillna("").items():
            for c in [x for x in str(ex).split(";") if x]:
                S.loc[t, c] = np.nan
        B[(rg, cfg, a)] = dict(S=S, lg=g.loghr, se=g.se, rb=g.rb, rs=g.rs, ret=g.retain, npairs=g.n_pairs,
                               ess_t=g.ess_t, ess_c=g.ess_c, n_t=g.n_t, n_c=g.n_c)
    return B


def agree(blk, tr):
    lg, se, rb, rs = (blk[k].loc[tr].to_numpy(float) for k in ("lg", "se", "rb", "rs"))
    absd = np.abs(lg - rb)
    z = (lg - rb) / np.sqrt(se ** 2 + rs ** 2)
    with np.errstate(invalid="ignore"):
        cons = 100.0 * (np.abs(z) < 1.96)       # NaN log HR -> 0 (as the v21 code; noted in the audit)
        ea = 100.0 * (absd <= 1.96 * rs)
    return absd, cons, ea, lg, rb


def contrast(B, CL, ka, kb, tr, side, full=True):
    A_, B_ = B[ka], B[kb]
    pf = p_one if side == "one" else p_two
    Sa, Sb = A_["S"].loc[tr], B_["S"].loc[tr]
    m = Sa.isna() | Sb.isna()
    Sa, Sb = Sa.mask(m), Sb.mask(m)
    out = {}
    for tag, items in (("54", NONC), ("58", VN)):
        ma, mb = Sa[items].mean(1), Sb[items].mean(1)
        la = 100 * (Sa[items] < 0.1).sum(1) / Sa[items].notna().sum(1)
        lb = 100 * (Sb[items] < 0.1).sum(1) / Sb[items].notna().sum(1)
        e, lo, hi, k = boot_relred(mb, ma)
        d = (mb - ma)
        out.update({f"m{tag}_a": ma.mean(), f"m{tag}_b": mb.mean(), f"relred{tag}": e, f"relred{tag}_lo": lo, f"relred{tag}_hi": hi,
                    f"m{tag}_k": k, f"m{tag}_better": f"{int((d > 0).sum())}/{int(d.notna().sum())}", f"m{tag}_p": pf(d),
                    f"lt01_{tag}_a": la.mean(), f"lt01_{tag}_b": lb.mean(), f"lt01_{tag}_p": pf(la - lb)})
        if full and tag == "54":
            c = pd.Series(d.to_numpy(), index=[CL[t] for t in tr]).dropna().groupby(level=0).mean()
            out["m54_cluster_p"] = pf(c.to_numpy())
            out["m54_loo_max_p"] = max(pf(d.drop(t)) for t in tr)
    if full:
        xa, ca, ea_a, lga, rb = agree(A_, tr)
        xb, cb, ea_b, lgb, _ = agree(B_, tr)
        dd = xb - xa
        out.update(absd_a=np.nanmean(xa), absd_b=np.nanmean(xb), absd_better=f"{int((dd > 0).sum())}/{int(np.isfinite(dd).sum())}",
                   absd_p=pf(dd), cons_p=pf(ca - cb), bshuf_p=bench_perm(lga, lgb, rb, two=(side == "two")))
        okp = np.isfinite(xa) & np.isfinite(xb)
        out.update(absd_a_pair=xa[okp].mean(), absd_b_pair=xb[okp].mean(), n_pair=int(okp.sum()))
        c = pd.Series(dd, index=[CL[t] for t in tr]).dropna().groupby(level=0).mean()
        out["absd_cluster_p"] = pf(c.to_numpy())
        for lab, x, cc, ee, lg in (("a", xa, ca, ea_a, lga), ("b", xb, cb, ea_b, lgb)):
            ok = np.isfinite(lg) & np.isfinite((B[ka] if lab == "a" else B[kb])["se"].loc[tr].to_numpy(float))
            out[f"{lab}_r"] = float(np.corrcoef(lg[ok], rb[ok])[0, 1])
            out[f"{lab}_ea_n"] = int((ee[ok] > 0).sum())
            out[f"{lab}_cons_n"] = int((cc[ok] > 0).sum())
            out[f"{lab}_k"] = int(ok.sum())
            r_ = (B[ka] if lab == "a" else B[kb])["ret"].loc[tr]
            npairs = (B[ka] if lab == "a" else B[kb])["npairs"].loc[tr]
            out[f"{lab}_retain"] = float(r_.mask((npairs >= 1) & (npairs < 11)).mean())
    dom = {}
    for g in DOMS:
        items = [c for c in VN if GRP[c] == g]
        ma, mb = Sa[items].mean(1), Sb[items].mean(1)
        e, lo, hi, k = boot_relred(mb, ma)
        dom[g] = dict(relred=e, lo=lo, hi=hi, p=pf(mb - ma), better=f"{int(((mb - ma) > 0).sum())}/{int((mb - ma).notna().sum())}")
    return out, dom


def contrast_list():
    L = []
    for cfg in CONFIGS:
        for rg in RUNGS:
            for a, b, s in (("ECG", "base", "one"), ("CLMBR", "base", "one"), ("ECG+CLMBR", "base", "one"),
                            ("ECG+CLMBR", "CLMBR", "one"), ("ECG+CLMBR", "ECG", "one"), ("CLMBR", "ECG", "two"),
                            ("shufECG", "base", "two"), ("shufCLMBR", "base", "two"), ("ECG", "shufECG", "one"),
                            ("CLMBR", "shufCLMBR", "one")):
                L.append((cfg, f"{rg}: {a} vs {b}", (rg, cfg, a), (rg, cfg, b), s))
        for ra, aa, rb_ in (("P1", "CLMBR", "Flags"), ("P1", "CLMBR", "hdPS200"), ("P5", "CLMBR", "hdPS200"),
                            ("P5", "CLMBR", "clinical"), ("P5", "ECG+CLMBR", "clinical")):
            L.append((cfg, f"{ra}+{aa} vs {rb_} base", (ra, cfg, aa), (rb_, cfg, "base"), "two"))
    for rg in ("P1", "P5"):
        for a, b, s in (("CLMBR32", "base", "one"), ("CLMBR32", "ECG", "two"), ("CLMBR", "CLMBR32", "two")):
            L.append(("main", f"{rg}: {a} vs {b}", (rg, "main", a), (rg, "main", b), s))
    L.append(("main", "P1+CLMBR32 vs Flags base", ("P1", "main", "CLMBR32"), ("Flags", "main", "base"), "two"))
    return L


G = {}


def job(args):
    sname, (cfg, lab, ka, kb, side) = args
    tr = G["sets"][sname]
    o, d = contrast(G["B"], G["CL"], ka, kb, tr, side)
    return dict(set=sname, config=cfg, contrast=lab, sided=side, **o), [dict(set=sname, config=cfg, contrast=lab, domain=g, **v)
                                                                         for g, v in d.items()]


def main(workers):
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    R, order, key, tiers, S32, S38, CL = load()
    B = blocks(R, order)
    G.update(B=B, CL=CL, sets={"S32": S32, "S38": S38})
    jobs = [(s, c) for s in ("S38", "S32") for c in contrast_list()]
    with Pool(workers) as p:
        res = p.map(job, jobs, chunksize=4)
    S = pd.DataFrame([r for r, _ in res])
    D = pd.DataFrame([x for _, ds in res for x in ds])
    for s in ("S32", "S38"):
        m = S.set == s
        for fam, cols in (("bal", ["m54_p", "lt01_54_p", "m58_p", "lt01_58_p"]), ("agr", ["absd_p", "cons_p", "bshuf_p"])):
            v = S.loc[m, cols].to_numpy().ravel()
            q = bh(v).reshape(-1, len(cols))
            for j, c in enumerate(cols):
                S.loc[m, f"q_{c}"] = q[:, j]
        md = D.set == s
        D.loc[md, "q_dom"] = bh(D.loc[md, "p"].to_numpy())
    S.to_csv(OUT / "core_recomputed.csv", index=False)
    D.to_csv(OUT / "domains_recomputed.csv", index=False)
    # compare with the v21 summary
    V = pd.read_csv(SRC / "sensitivity.csv")
    V = V.set_index(["set", "config", "contrast"])
    S2 = S.set_index(["set", "config", "contrast"])
    cmp = []
    for mine, theirs in (("relred54", "relred54"), ("relred54_lo", "relred54_lo"), ("relred54_hi", "relred54_hi"), ("m54_p", "m54_p"),
                         ("m54_cluster_p", "m54_cluster_p"), ("relred58", "relred58"), ("lt01_54_a", "lt01_54_a"), ("absd_a", "absd_a"),
                         ("absd_p", "absd_p"), ("bshuf_p", "bshuf_p"), ("cons_p", "cons_p"), ("q_m54_p", "q_m54_p_fam"),
                         ("q_absd_p", "q_absd_p_fam"), ("q_bshuf_p", "q_bshuf_p_fam"), ("a_r", "a_r"), ("a_retain", "a_retain"),
                         ("absd_cluster_p", "absd_cluster_p")):
        x = S2[mine].astype(float)
        y = V.loc[S2.index, theirs].astype(float)
        dv = (x - y).abs()
        cmp.append(dict(col=mine, n=int(dv.notna().sum()), maxdev=float(dv.max()), nan_mismatch=int((x.isna() ^ y.isna()).sum())))
    C = pd.DataFrame(cmp)
    C.to_csv(OUT / "compare_vs_v21.csv", index=False)
    print(C.to_string(index=False))
    Dv = pd.read_csv(SRC / "domains.csv").set_index(["set", "config", "contrast", "domain"])
    D2 = D.set_index(["set", "config", "contrast", "domain"])
    for mine, theirs in (("relred", "relred"), ("p", "p"), ("q_dom", "q_domain_fam")):
        dv = (D2[mine] - Dv.loc[D2.index, theirs]).abs()
        print("domains", mine, "maxdev", float(dv.max()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    main(min(ap.parse_args().workers, 16))
