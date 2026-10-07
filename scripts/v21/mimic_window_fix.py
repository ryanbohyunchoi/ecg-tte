#!/usr/bin/env python
"""v2.1 sensitivity (paper2 reviewer item S5): diagnosis-window fix for the v20 MIMIC-IV new trials.

In v20, scripts/v20/mimic_build_new.py built SOAP II, ELITE II and PEPTIC with baseline `dx` flags from the index
admission or any earlier admission (admittime <= index admittime), panel dx_ codes including the index admission,
and panel px_ codes from any admission (chartdate in [t0-365 d, index day)). The 5 v1.5 trials were audit-fixed
(scripts/v15/v15_mimic_auditfix.py, AUDIT_V15 M2) to EARLIER admissions only. This script applies the v1.5
audit-fix rules to the 3 new trials, without modifying any v20 module or v20 output:
  * baseline dx flags (roles['dx'], v1.5 CONCEPTS): admissions with admittime < index admittime, index admission excluded;
  * panel dx_ (ICD-10 3-char / ICD-9 dx_i9_ 3-char, count of distinct admissions): earlier admissions with
    admittime in [t0-365 d, index admittime); panel px_: chartdate in [t0-365 d, index day), index admission excluded;
    >= 1% prevalence; rx_ / lab_ columns unchanged;
  * baseline columns that become constant are dropped (and removed from roles), as in the audit fix.
Everything else (cohort, outcomes, ECG embedding, rct.json, held-out panel, meds, labs/vitals, utilisation) is unchanged.

Subcommands
  build      fixed trial dirs in <OUT>/trials/<k> (restricted; unchanged files are symlinks to the v20 dirs)
  analyze    demo / sparse / hdPS200 / clinical x base / ECG / permECG x 2 populations for all 8 trials
             (5 v1.5 trials from their original dirs = gate; 3 new trials from the fixed dirs), 8 workers
  gate       the 5 v1.5 trials must equal v20 results exactly (all bases); new-trial demo rows reported (sanity)
  summarize  v20 summary metrics and the paper.md relative-reduction CIs (sens_primary32.relred_ci, 4,000
             resamples, seed 20261001, trial order MIMIC7), original v20 vs window-fixed, side by side
Outputs: /mnt/raid0/rbc58/ecg-tte/audits/claude-v21-paper2/mimic/windowfix/ (umask 077). Aggregates only.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import json  # noqa: E402
import sys  # noqa: E402
from multiprocessing import Pool  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mimic_cvd5 as C5  # noqa: E402  (imports v20 mimic_replication as C5.M and mimic_summary as C5.MS)

M, MS = C5.M, C5.MS
from v15_mimic_common import CONCEPTS  # noqa: E402

os.umask(0o077)
OUT = C5.OUT / "windowfix"
TRIALS = M.BUILT + M.NEW
BASES = ["demo", "sparse", "hdPS200", "clinical"]
LINK = ["cohort.parquet", "outcomes.parquet", "ecg_embedding.parquet", "rct.json", "index_time.parquet"]
MIMIC7 = ["plato", "aristotle", "rocket_af", "transform_hf", "comet", "soap2", "elite2"]  # = sens_primary32.MIMIC7


def fdir(k):
    return M.tdir(k) if k in M.BUILT else OUT / "trials" / k


# ------------------------------------------------------------------ build
def build(k):
    import duckdb
    src, dst = M.tdir(k), OUT / "trials" / k
    dst.mkdir(parents=True, exist_ok=True)
    for f in LINK:
        if not (dst / f).exists():
            (dst / f).symlink_to(src / f)
    b1 = pd.read_parquet(src / "baseline.parquet")
    p1 = pd.read_parquet(src / "panel.parquet")
    r1 = json.load(open(src / "roles.json"))
    d1 = pd.read_csv(src / "panel_dictionary.csv")
    it = pd.read_parquet(src / "index_time.parquet")
    assert list(b1.pid) == list(p1.pid) and set(it.pid) == set(b1.pid)
    con = duckdb.connect()
    con.execute("SET threads=8")
    for t in ("admissions", "diagnoses_icd", "procedures_icd"):
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{M.STAGE}/{t}.parquet')")
    con.register("it_df", it[["pid", "subject_id", "hadm_id", "index_datetime"]])
    con.execute("""CREATE TEMP TABLE c AS SELECT it.pid, it.subject_id, it.hadm_id, it.index_datetime t0,
                   CAST(it.index_datetime AS DATE) d0, ad.admittime FROM it_df it
                   JOIN admissions ad ON ad.subject_id = it.subject_id AND ad.hadm_id = it.hadm_id""")
    n = len(b1)
    assert con.execute("SELECT count(*) FROM c").fetchone()[0] == n
    dxcols = [c for c in r1["dx"] if c in CONCEPTS]
    rows = [(nm, 10, p) for nm in dxcols for p in CONCEPTS[nm][0]] + [(nm, 9, p) for nm in dxcols for p in CONCEPTS[nm][1]]
    con.register("concept", pd.DataFrame(rows, columns=["concept", "v", "prefix"]))
    cdx = con.execute("""SELECT DISTINCT c.pid, k.concept FROM c JOIN admissions ad ON ad.subject_id = c.subject_id
        AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id
        JOIN diagnoses_icd d ON CAST(d.subject_id AS BIGINT) = ad.subject_id AND CAST(d.hadm_id AS BIGINT) = ad.hadm_id
        JOIN concept k ON k.v = CAST(d.icd_version AS INT) AND starts_with(d.icd_code, k.prefix)""").df()
    b2 = b1.set_index("pid").copy()
    prev = {}
    for cname in dxcols:
        old = float(b2[cname].mean())
        b2[cname] = b2.index.isin(cdx[cdx.concept == cname].pid).astype(float)
        prev[cname] = (round(100 * old, 1), round(100 * float(b2[cname].mean()), 1))
    newconst = [c for c in b2.columns if b2[c].nunique(dropna=True) <= 1 and b1.set_index("pid")[c].nunique(dropna=True) > 1]
    b2 = b2.drop(columns=newconst)
    roles = {g: ([c for c in v if c not in newconst] if isinstance(v, list) else v) for g, v in r1.items()}
    other = [c for c in b1.columns if c != "pid" and c not in dxcols and c not in newconst]
    pd.testing.assert_frame_equal(b2[other].reset_index(drop=True), b1[other].reset_index(drop=True))
    # panel dx/px, earlier admissions only (v15_mimic_auditfix.py queries)
    q_dx = """SELECT c.pid, CASE WHEN CAST(d.icd_version AS INT) = 10 THEN 'dx_' || substr(d.icd_code, 1, 3)
                   ELSE 'dx_i9_' || substr(d.icd_code, 1, 3) END f, count(DISTINCT d.hadm_id) cnt
              FROM c JOIN admissions ad ON ad.subject_id = c.subject_id AND ad.admittime < c.admittime AND ad.hadm_id <> c.hadm_id
                   AND ad.admittime >= c.t0 - INTERVAL 365 DAY
              JOIN diagnoses_icd d ON CAST(d.subject_id AS BIGINT) = ad.subject_id AND CAST(d.hadm_id AS BIGINT) = ad.hadm_id
              GROUP BY 1, 2"""
    q_px = """SELECT c.pid, CASE WHEN p.icd_version = 10 THEN 'px_' || substr(p.icd_code, 1, 4)
                   ELSE 'px_i9_' || substr(p.icd_code, 1, 3) END f, count(DISTINCT p.chartdate) cnt
              FROM c JOIN procedures_icd p ON p.subject_id = c.subject_id AND p.hadm_id <> c.hadm_id
              WHERE p.chartdate < c.d0 AND p.chartdate >= c.d0 - INTERVAL 365 DAY GROUP BY 1, 2"""
    frames, dic = [], []
    for dom, q in (("dx", q_dx), ("px", q_px)):
        d = con.execute(f"""WITH x AS ({q}) SELECT f, list(pid) s, list(cnt) cc FROM x GROUP BY f
                            HAVING count(DISTINCT pid) >= {0.01 * n} ORDER BY f""").df()
        for f, s, cc in zip(d.f, d.s, d.cc):
            frames.append(pd.Series(np.asarray(cc, float), index=pd.Index(s), name=f))
            dic.append((f, dom))
    keep = [c for c in p1.columns if c.startswith(("rx_", "lab_"))]
    p2 = pd.concat(frames, axis=1).reindex(p1.pid).fillna(0.0) if frames else pd.DataFrame(index=p1.pid)
    p2 = pd.concat([p2.reset_index(drop=True), p1[keep].reset_index(drop=True)], axis=1)
    p2.insert(0, "pid", p1.pid.values)
    dd = pd.DataFrame(dic + [(f, dm) for f, dm in zip(d1.feature, d1.domain) if f in keep], columns=["feature", "domain"])
    assert list(dd.feature) == [c for c in p2.columns if c != "pid"]
    b2.reset_index().to_parquet(dst / "baseline.parquet", index=False)
    p2.to_parquet(dst / "panel.parquet", index=False)
    dd.to_csv(dst / "panel_dictionary.csv", index=False)
    json.dump(roles, open(dst / "roles.json", "w"), indent=1)
    cnt = lambda cols, pre: sum(c.startswith(pre) for c in cols)
    info = dict(trial=k, n=n, dx_prev_old_new=prev, newly_constant_dropped=newconst,
                panel_dx_old_new=(cnt(p1.columns, "dx_"), cnt(p2.columns, "dx_")),
                panel_px_old_new=(cnt(p1.columns, "px_"), cnt(p2.columns, "px_")), rx_lab_kept=len(keep))
    print(json.dumps(info), flush=True)
    return info


# ------------------------------------------------------------------ analyze / gate
def analyze(k):
    D = M.VA.TrialData(fdir(k))
    return C5.run_trial(k, D, BASES, OUT / "results")


def gate():
    out = []
    for k in TRIALS:
        for kind, keys in (("arms", ["base", "arm", "pop"]), ("vars", ["base", "arm", "pop", "var"])):
            ref = pd.read_csv(M.OUT / "results" / f"{k}_{kind}.csv")
            new = pd.read_csv(OUT / "results" / f"{k}_{kind}.csv")
            sel = BASES if k in M.BUILT else ["demo"]
            ref, new = ref[ref.base.isin(sel)], new[new.base.isin(sel)]
            a = ref.set_index(keys).sort_index()
            b = new.set_index(keys)[[c for c in ref.columns if c not in keys]].sort_index()
            same = a.index.equals(b.index)
            num = a.select_dtypes("number").columns
            d = float((a[num] - b[num]).abs().max().max()) if same else np.inf
            nan_ok = bool((a[num].isna() == b[num].isna()).all().all()) if same else False
            obj = [c for c in a.columns if c not in num]
            txt = bool((a[obj] == b[obj]).all().all()) if same else False
            out.append(dict(trial=k, role="gate" if k in M.BUILT else "sanity(demo)", table=kind, rows=len(a), same_rows=same,
                            max_abs_diff=d, nan_pattern_equal=nan_ok, text_equal=txt))
    g = pd.DataFrame(out)
    G = g[g.role == "gate"]
    ok = bool(G.same_rows.all() and (G.max_abs_diff == 0).all() and G.nan_pattern_equal.all() and G.text_equal.all())
    (OUT / "gate").mkdir(parents=True, exist_ok=True)
    g.to_csv(OUT / "gate/gate.csv", index=False)
    for f in ("PASS", "FAIL"):
        (OUT / "gate" / f).unlink(missing_ok=True)
    (OUT / "gate" / ("PASS" if ok else "FAIL")).write_text(json.dumps(dict(n=len(G), max_d=float(G.max_abs_diff.max()))))
    print(g.to_string(index=False), "\nGATE", "PASS" if ok else "FAIL", flush=True)
    return ok


# ------------------------------------------------------------------ summarize
def load(which):
    d = M.OUT / "results" if which == "v20" else OUT / "results"
    A = pd.concat([pd.read_csv(d / f"{k}_arms.csv") for k in TRIALS], ignore_index=True)
    return A[A.base.isin(BASES)]


def summarize():
    import sens_primary32 as SP  # noqa: E402  (scripts/v20; relred_ci = paper.md CIs)
    assert SP.MIMIC7 == MIMIC7 and SP.NB == 4000
    A = {w: load(w) for w in ("v20", "fixed")}
    rows, ag_rows = [], []
    for sname in ("primary7", "all8"):
        tr = MS.SETS[sname]
        for base in BASES:
            for pop in ("all", "no_index_day_ecg"):
                for w, X in A.items():
                    b = MS.balance(X, tr, base, pop)
                    g = X[(X["pop"] == pop) & (X.base == base) & X.trial.isin(tr)].pivot_table(index="trial", columns="arm", values="mean_smd").reindex(tr)
                    for arm in ("ECG", "permECG"):
                        e, lo, hi, kk = SP.relred_ci(g["base"], g[arm])
                        rows.append(dict(set=sname, base=base, pop=pop, version=w, arm=arm, k=kk,
                                         pct_bal_base=b["pct_bal_base"], pct_bal_arm=b[f"pct_bal_{arm}"], dpts=b[f"dpts_{arm}"],
                                         better=b[f"better_{arm}"], p_pts=b[f"p_{arm}"],
                                         relred=e, ci4000_lo=lo, ci4000_hi=hi, ci2000_v20=b[f"relred_{arm}_ci"],
                                         lower=b[f"lower_smd_{arm}"], p_smd=b[f"p_smd_{arm}"],
                                         **({f"relred_block{x}": b.get(f"relred_ECG_block{x}", np.nan) for x in "ABD"} if arm == "ECG" else {})))
                    ag = MS.agreement(X, tr, base, pop)
                    for arm in ("base", "ECG", "permECG"):
                        ag_rows.append(dict(set=sname, base=base, pop=pop, version=w, arm=arm, **ag[arm],
                                            **(ag["ECG_vs_base"] if arm == "ECG" else {})))
    R, G = pd.DataFrame(rows), pd.DataFrame(ag_rows)
    (OUT / "summary").mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT / "summary/balance.csv", index=False)
    G.to_csv(OUT / "summary/agreement.csv", index=False)
    # per-trial (new trials, all patients)
    P = []
    for w, X in A.items():
        for r in X[(X["pop"] == "all") & X.trial.isin(M.NEW)].itertuples():
            P.append(dict(version=w, trial=r.trial, base=r.base, arm=r.arm, n_pairs=int(r.n_pairs), pct_bal=round(r.pct_bal, 1),
                          mean_smd=round(r.mean_smd, 4), hr=round(float(np.exp(r.loghr)), 3),
                          lo=round(float(np.exp(r.loghr - 1.96 * r.se)), 3), hi=round(float(np.exp(r.loghr + 1.96 * r.se)), 3)))
    pd.DataFrame(P).to_csv(OUT / "summary/per_trial_new.csv", index=False)
    pd.set_option("display.width", 250)
    S = R[(R.set == "primary7") & (R.arm == "ECG")]
    print(S[["base", "pop", "version", "pct_bal_base", "pct_bal_arm", "dpts", "better", "p_pts", "relred", "ci4000_lo", "ci4000_hi",
             "lower", "p_smd"]].round(3).to_string(index=False))


if __name__ == "__main__":
    cmd = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    if cmd == "build":
        info = [build(k) for k in M.NEW]
        json.dump(info, open(OUT / "build_info.json", "w"), indent=1)
    elif cmd == "analyze":
        with Pool(8) as p:
            p.map(analyze, TRIALS)
    elif cmd == "gate":
        sys.exit(0 if gate() else 1)
    elif cmd == "summarize":
        assert (OUT / "gate" / "PASS").exists(), "gate has not passed"
        summarize()
