#!/usr/bin/env python
"""v1 audit (claims recheck): factual Methods statements of docs/paper/paper2.md (lines 25-51) and the cohort numbers of
Results line 77, recomputed from the trial objects and the cell-level grid output (not from the summary scripts).

Stage `trials` (8 workers): loads each of the 38 trials exactly as scripts/v21/paper2_grid.task does (v16_engine.load_trial)
  and returns only trial-level aggregates: cohort size, PS-Demo columns, PS-CVD5 design names, hdPS investigator dx count,
  PS-Clinical column groups, ECG raw / PC dimensions, CLMBR-T PC dimension, shuffle permutation validity, index-year range.
  -> audits/claude-v1-audit/claims/restricted_methods_trials.csv (restricted: per-trial n_t/n_c kept only there)
Stage `facts`: cohort numbers (line 77) from claude-v21-paper2/core/restricted_cells.parquet; flag counts from core/log.json;
  CLMBR-T truncation from claude-<trial>-clmbr-codeonly/report/summary.json; study-drug code presence from
  claude-v18-audit4/clmbr_leak_independent.csv and claude-v18-clmbr/leakage.csv; CLMBR-T parameter count from the
  safetensors header; label counts from docs/v21/TRIAL_LABELS.json. Prints aggregates only (counts 1-10 never printed).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import glob  # noqa: E402
import json  # noqa: E402
import struct  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path("/home/rbc58/github/ecg-tte")
A = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = A / "claude-v1-audit" / "claims"
CORE = A / "claude-v21-paper2" / "core"
for p in ("scripts/v18", "scripts/v17", "scripts/v16", "scripts"):
    sys.path.insert(0, str(ROOT / p))
MIN_CELL = 11


def S32_S38():
    QT = {t["key"]: t["tier"].split(" - ")[0] for t in json.loads((ROOT / "docs/v19/quality_tiers.json").read_text())["trials"]}
    R = pd.read_parquet(CORE / "restricted_cells.parquet", columns=["trial", "key"]).drop_duplicates()
    k = dict(zip(R.trial, R.key))
    s38 = sorted(k)
    return [t for t in s38 if QT[k[t]] != "Limited"], s38, k


def one(n):
    import v18_af_confirm as AF
    import v18_clmbr as C
    E = AF.V.E
    T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
    b5, psn5, hf = C.designs(T, n, C.P5DX)
    perm = T.shuffle_perm
    yrs = T.index_date.dt.year
    core = list(T.cov.columns)
    return dict(trial=n, n=len(T.t), n_t=int(T.t.sum()), n_c=int((1 - T.t).sum()), demo=";".join(T.demo), n_demo=len(T.demo),
                p5_names=";".join(psn5), p5_width=b5.shape[1], hf_var=hf, n_dxc=len(T.dxc), dxc=";".join(T.dxc),
                n_core=len(core), n_phys=len(T.phys), phys=";".join(T.phys), n_meds=len(T.meds), n_util=len(T.util),
                core_other=";".join(c for c in core if c not in set(T.demo) | set(T.dxc) | set(T.phys) | set(T.meds) | set(T.util)),
                ecg_raw_dim=T.ecg_raw.shape[1], ecg_pc_dim=T.ecg_pc.shape[1], clm_pc_dim=T.clm_pc.shape[1],
                clm_pc_rows_eq_n=T.clm_pc.shape[0] == len(T.t), perm_is_perm=bool(np.array_equal(np.sort(perm), np.arange(len(T.t)))),
                perm_fixed_frac=float((perm == np.arange(len(T.t))).mean()),
                year_min=int(yrs.min()), year_max=int(yrs.max()), year_na=int(yrs.isna().sum()))


def trials():
    from multiprocessing import Pool
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True)
    _, s38, _ = S32_S38()
    with Pool(8) as p:
        res = p.map(one, s38, chunksize=1)
    pd.DataFrame(res).to_csv(OUT / "restricted_methods_trials.csv", index=False)
    print("trials done", len(res))


def safetensors_params(f):
    with open(f, "rb") as fh:
        h = json.loads(fh.read(struct.unpack("<Q", fh.read(8))[0]))
    return int(sum(np.prod(v["shape"]) for k, v in h.items() if k != "__metadata__"))


def facts():
    os.umask(0o077)
    s32, s38, KEY = S32_S38()
    M = pd.read_csv(OUT / "restricted_methods_trials.csv").set_index("trial")
    pr = lambda *a: print(*a, flush=True)
    pr("== trial objects (38)")
    pr("demo sets:", M.demo.value_counts().to_dict())
    pr("P5 design sets:", M.p5_names.value_counts().to_dict())
    pr("HF variable:", M.hf_var.value_counts().to_dict(), "elx_chf trials:", list(M.index[M.hf_var == "elx_chf"]))
    for s, tr in (("S38", s38), ("S32", s32)):
        pr(s, "hdPS investigator dx (dxc) range", M.loc[tr, "n_dxc"].min(), "-", M.loc[tr, "n_dxc"].max(),
           "values", M.loc[tr, "n_dxc"].value_counts().sort_index().to_dict())
    pr("dxc names (union):", sorted(set(";".join(M.dxc).split(";"))))
    pr("phys (union):", sorted(set(";".join(M.phys.fillna("")).split(";")) - {""}))
    pr("n_meds range", M.n_meds.min(), M.n_meds.max(), "n_util range", M.n_util.min(), M.n_util.max(),
       "core_other:", M.core_other.fillna("").value_counts().to_dict())
    pr("ECG raw dim", M.ecg_raw_dim.value_counts().to_dict(), "ECG PCs", M.ecg_pc_dim.value_counts().to_dict(),
       "CLMBR PCs", M.clm_pc_dim.value_counts().to_dict(), "clm rows==n", bool(M.clm_pc_rows_eq_n.all()))
    pr("shuffle perm valid", bool(M.perm_is_perm.all()), "max fixed-point fraction", round(M.perm_fixed_frac.max(), 4))
    pr("index year range S38", M.year_min.min(), M.year_max.max(), "S32", M.loc[s32, "year_min"].min(), M.loc[s32, "year_max"].max(),
       "NA", int(M.year_na.sum()))
    pr("trials with first index year < 2012:", int((M.year_min < 2012).sum()), "; year-min distribution", M.year_min.value_counts().sort_index().to_dict())

    pr("== line 77 cohort numbers (restricted_cells, P5 base main)")
    R = pd.read_parquet(CORE / "restricted_cells.parquet")
    g = R[(R.rung == "P5") & (R.config == "main") & (R.arm == "base")].set_index("trial")
    assert (g.n == M.n.reindex(g.index)).all(), "cells n != trial objects n"
    n32 = g.loc[s32, "n"]
    pr("S32 patients total", int(n32.sum()), "median", float(n32.median()), "range", int(n32.min()), int(n32.max()))
    pr("S32 two middle n values (median ties):", sorted(n32)[15:17])
    p32 = g.loc[s32, "n_pairs"]
    pr("P5 pairs total", int(p32.sum()), "median", float(p32.median()), "range", int(p32.min()), int(p32.max()))
    ret = p32 / np.minimum(g.loc[s32, "n_t"], g.loc[s32, "n_c"])
    pr("P5 mean retention", round(100 * ret.mean(), 2), "median", round(100 * ret.median(), 2))
    # all rungs/arms CLMBR retention (cross-check of line 85 values that also sit in this scope's denominators)
    for rg, a in (("P5", "ECG"), ("P5", "CLMBR"), ("P5", "ECG+CLMBR")):
        h = R[(R.rung == rg) & (R.config == "main") & (R.arm == a)].set_index("trial").loc[s32]
        pr(f"{rg} {a} mean retention", round(100 * (h.n_pairs / np.minimum(h.n_t, h.n_c)).mean(), 2))
    pr("P5 base p_ps (= demo + 5):", g.p_ps.value_counts().to_dict())
    for rg in ("P1", "Flags", "hdPS200", "clinical"):
        h = R[(R.rung == rg) & (R.config == "main") & (R.arm == "base")].set_index("trial")
        pr(rg, "base p_ps range S38", int(h.p_ps.min()), int(h.p_ps.max()))
    pe = R[(R.config == "main")].pivot_table(index="trial", columns=["rung", "arm"], values="p_ps")
    for rg in ("P1", "P5", "Flags", "hdPS200", "clinical"):
        d = {a: sorted(set((pe[(rg, a)] - pe[(rg, "base")]).astype(int))) for a in ("ECG", "CLMBR", "ECG+CLMBR", "shufECG", "shufCLMBR")}
        pr(rg, "added columns per arm", d)

    pr("== PS-Flags counts (core/log.json)")
    L = pd.DataFrame(json.loads((CORE / "log.json").read_text())).set_index("trial")
    for s, tr in (("S38", s38), ("S32", s32)):
        f = L.loc[tr, "n_flags"]
        pr(s, "flags median", float(f.median()), "range", int(f.min()), int(f.max()))
    pr("flag lookback days", L.lookback_days.unique().tolist(), "exposure dx removed", int(L.n_expo_removed.sum()),
       "keys not in roster", int(L.n_keys_not_in_roster.sum()))
    pr("PROTECT AF n (cohort) and flags:", int(g.loc["protect-af", "n"]), int(L.loc["protect-af", "n_flags"]))
    hb = R[(R.rung == "hdPS200") & (R.config == "main") & (R.arm == "base")].set_index("trial")
    pr("hdPS p_ps - demo - dxc == 200 for all:", bool(((hb.p_ps - M.n_demo.reindex(hb.index) - M.n_dxc.reindex(hb.index)) == 200).all()))

    pr("== CLMBR-T")
    tr_rows = []
    for n in s38:
        d = A / ("comet-clmbr-full-NAyb4G2x" if n == "comet" else f"claude-{n}-clmbr-codeonly") / "report" / "summary.json"
        J = json.loads(d.read_text())
        tr_rows.append(dict(trial=n, mt=J.get("max_tokens"), mode=J.get("numeric_mode"), dim=J.get("embedding_dimension"),
                            enc=J["totals"]["encoded"], trunc=J["totals"].get("truncated_patients"), target=J.get("target_patients")))
    TR = pd.DataFrame(tr_rows).set_index("trial")
    TR["pct"] = 100 * TR.trunc / TR.enc
    pr("max_tokens", TR.mt.unique().tolist(), "numeric mode", TR["mode"].unique().tolist(), "dim", TR.dim.unique().tolist())
    for s, tr in (("S38", s38), ("S32", s32)):
        pr(s, "truncation % of encoded (roster) range", round(TR.loc[tr, "pct"].min(), 2), round(TR.loc[tr, "pct"].max(), 2))
    pr("top truncation:", TR.pct.sort_values(ascending=False).round(2).head(3).to_dict())
    pr("CLMBR-T parameters (safetensors header):", safetensors_params("/mnt/raid0/eo287/clmbr/model.safetensors"))
    LK = pd.read_csv(A / "claude-v18-audit4/clmbr_leak_independent.csv").set_index("trial")
    num = lambda s: pd.to_numeric(s, errors="coerce")
    for c in ("pct_own_any", "pct_own_vocab", "pct_other_any", "pct_other_vocab"):
        v = num(LK[c])
        pr(f"independent leak (38, roster) {c}: max {v.max():.2f} ({v.idxmax()}); trials covered {LK.shape[0]}")
    L18 = pd.read_csv(A / "claude-v18-clmbr/leakage.csv").set_index("trial")
    for c in ("pct_any_exposure_token", "pct_any_exposure_token_vocab"):
        v = num(L18[c])
        pr(f"v18 leakage (33, analysed) {c}: max {v.max():.2f} ({v.idxmax()})")
    v = np.fmax(num(LK.pct_own_vocab).fillna(0), num(LK.pct_other_vocab).fillna(0))
    pr("max(own_vocab, other_vocab) per trial, 38: max", round(float(v.max()), 2), v.idxmax())

    pr("== labels")
    LB = json.loads((ROOT / "docs/v21/TRIAL_LABELS.json").read_text())["labels"]
    name = {x["trial"]: x for x in LB}
    pr("physiologic yes (38):", sum(x["physiologic"] == "yes" for x in LB))


def years():
    """index-year tails outside 2011-2024 (trials flagged by stage facts); counts reported only as a 1-10 / >10 bucket."""
    import v18_af_confirm as AF
    E = AF.V.E
    M = pd.read_csv(OUT / "restricted_methods_trials.csv")
    for n in M.trial[(M.year_max > 2024) | (M.year_min < 2011)]:
        T = E.load_trial(n) if n in AF.V.OLD else E.load_trial(n, cache=False)
        y = T.index_date.dt.year
        k = int((y > 2024).sum())
        print(n, "index dates after 2024:", "0" if k == 0 else ("1-10 (suppressed)" if k < MIN_CELL else f">10 ({100 * k / len(y):.1f}%)"),
              "; last index month", "suppressed" if k < MIN_CELL else str(T.index_date.max().to_period("M")))


if __name__ == "__main__":
    {"trials": trials, "facts": facts, "years": years}[sys.argv[1]]()
