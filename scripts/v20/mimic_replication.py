#!/usr/bin/env python
"""v2.0 MIMIC-IV external replication (docs/v20/MIMIC_REPLICATION_PLAN.md).

Subcommands
  gate                 recompute v1.5 primary-outcome estimates for the 5 built trials with the v1.5 engine and
                       compare with analysis/estimates.csv (|d log HR| < 1e-9)
  heldout <trial...>   build held-out blocks B (additional labs) and C (ventilation at t0) per trial dir
                       (restricted parquet keyed by pid, in the output dir)
  analyze <trial...>   balance + RCT agreement per trial: PS ladder (demo / sparse / hdPS200 / clinical-lite) x arms
                       (base / +ECG32 / +permuted ECG32); full ECG cohort and the no-index-day-ECG sensitivity
Trial dirs: v1.5 built trials in audits/claude-v15-mimic-<k>; new trials in <OUT>/trials/<k>.
Outputs (aggregates, umask 077): <OUT>/results/<trial>_{arms,vars}.csv. Nothing patient-level is printed.
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
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "v15"))
import v15_analyze as VA  # noqa: E402
from eval_longtail_balance import smd_vector  # noqa: E402
from v13_common import cox, match, ps_logit  # noqa: E402

os.umask(0o077)
AUD = Path("/mnt/raid0/rbc58/ecg-tte/audits")
OUT = AUD / "claude-v20-mimic-replication"
STAGE = AUD / "claude-v15-mimic-shared/stage"
VENT = AUD / "claude-v20-mimic-feasibility/stage/icu_vent.parquet"
BUILT = ["plato", "aristotle", "rocket_af", "transform_hf", "comet"]
NEW = ["soap2", "elite2", "peptic"]
SEED = 20261001
# block B: additional labs (itemids as panel_coverage.py; plausibility ranges)
LABS_B = {"nt_probnp": ([50963], 5, 70000), "troponin_t": ([51003], 0, 25), "lactate": ([50813], 0.2, 30),
          "albumin": ([50862], 0.5, 7), "bun": ([51006], 1, 300), "wbc": ([51301], 0.1, 200),
          "platelets": ([51265], 1, 2000), "inr": ([51237], 0.5, 15), "ldl": ([50905, 50906], 5, 500),
          "hba1c": ([50852], 3, 20), "bilirubin": ([50885], 0.05, 60), "alt": ([50861], 1, 10000),
          "bicarbonate": ([50882], 3, 60)}
BASES = {"demo": ["demo"], "sparse": ["demo", "dx"], "hdPS200": ["demo", "dx", "HD"], "clinical": VA.GROUPS}


def tdir(k):
    return AUD / f"claude-v15-mimic-{k}" if k in BUILT else OUT / "trials" / k


# ------------------------------------------------------------------ gate
def gate():
    rows = []
    for k in BUILT:
        D = VA.TrialData(tdir(k))
        ref = pd.read_csv(tdir(k) / "analysis/estimates.csv")
        ref = ref[(ref.population == "full") & (ref.outcome == "primary")].set_index("arm")
        arms = [a for a in VA.BASE_ARMS if a in ref.index]
        M = VA.fit_matches(D.designs(arms), D.t)
        est = VA.estimates(D, M, which=("primary",)).set_index("arm")
        for a in arms:
            rows.append(dict(trial=k, arm=a, loghr=est.loc[a, "loghr"], ref=ref.loc[a, "loghr"],
                             d=abs(est.loc[a, "loghr"] - ref.loc[a, "loghr"]), dse=abs(est.loc[a, "se"] - ref.loc[a, "se"])))
    g = pd.DataFrame(rows)
    (OUT / "gate").mkdir(parents=True, exist_ok=True)
    g.to_csv(OUT / "gate/gate.csv", index=False)
    ok = bool((g.d < 1e-9).all() and (g.dse < 1e-9).all())
    print(g.groupby("trial")[["d", "dse"]].max().to_string(), "\nGATE", "PASS" if ok else "FAIL", flush=True)
    (OUT / "gate" / ("PASS" if ok else "FAIL")).write_text(json.dumps(dict(n=len(g), max_d=float(g.d.max()))))
    return ok


# ------------------------------------------------------------------ held-out blocks B, C
def heldout(k):
    import duckdb
    it = pd.read_parquet(tdir(k) / "index_time.parquet")[["pid", "subject_id", "index_datetime"]]
    con = duckdb.connect()
    con.execute("SET threads=8")
    con.register("c", it)
    con.register("lmap", pd.DataFrame([(n, i) for n, (items, lo, hi) in LABS_B.items() for i in items], columns=["name", "itemid"]))
    lab = con.execute(f"""SELECT c.pid, m.name, arg_max(l.valuenum, l.charttime) v FROM c
        JOIN read_parquet('{STAGE}/labevents.parquet') l ON l.subject_id = c.subject_id
        JOIN lmap m ON m.itemid = l.itemid
        WHERE l.valuenum IS NOT NULL AND l.charttime < c.index_datetime
          AND l.charttime >= c.index_datetime - INTERVAL 365 DAY
        GROUP BY 1, 2""").df()
    H = pd.DataFrame(index=it.pid)
    for name, (items, lo, hi) in LABS_B.items():
        s = lab[lab.name == name].set_index("pid").v.reindex(H.index)
        H[name] = s.where((s >= lo) & (s <= hi))
    vent = con.execute(f"""SELECT DISTINCT c.pid FROM c JOIN read_parquet('{VENT}') v ON v.subject_id = c.subject_id
        WHERE v.starttime <= c.index_datetime AND (v.endtime IS NULL OR v.endtime >= c.index_datetime)""").df()
    H["vent_at_t0"] = H.index.isin(vent.pid).astype(float)
    (OUT / "heldout").mkdir(parents=True, exist_ok=True)
    H.reset_index().to_parquet(OUT / "heldout" / f"{k}.parquet", index=False)
    cov = {c: round(float(H[c].notna().mean()), 3) for c in LABS_B}
    print(k, "n", len(H), "coverage", cov, "vent", round(float(H.vent_at_t0.mean()), 3), flush=True)


# ------------------------------------------------------------------ analysis
def exact_signflip(d):
    d = np.asarray([x for x in d if np.isfinite(x)])
    k = len(d)
    if k == 0:
        return np.nan
    obs = d.mean()
    s = np.array(np.meshgrid(*[[-1, 1]] * k)).reshape(k, -1).T
    return float(np.mean((s * np.abs(d)).mean(1) >= obs - 1e-12))


def panel_for(D, k, base):
    """Held-out panel (observed values): A (labs_vitals) + D (util) unless in the PS (clinical), B + C always."""
    H = pd.read_parquet(OUT / "heldout" / f"{k}.parquet").set_index("pid").reindex(D.pids)
    raw = pd.read_parquet(D.dir / "baseline.parquet").assign(pid=lambda x: x.pid.astype(str)).drop_duplicates("pid").set_index("pid").reindex(D.pids)
    blocks = {}
    if base != "clinical":
        blocks["A"] = [c for c in D.lv_names]
        blocks["D"] = [c for c in D.util if c in raw]
    blocks["B"] = list(LABS_B)
    blocks["C"] = ["vent_at_t0"]
    cols, blk, V = [], [], []
    for b, names in blocks.items():
        for c in names:
            v = (raw[c] if b in ("A", "D") else H[c]).to_numpy(float)
            if np.nanstd(v) == 0 or np.all(np.isnan(v)):
                continue
            cols.append(c)
            blk.append(b)
            V.append(v)
    # missingness indicators (secondary panel) for A and B
    mi, mi_cols = [], []
    for b in ("A", "B"):
        for c in blocks.get(b, []):
            v = (raw[c] if b == "A" else H[c]).isna().to_numpy(float)
            if 0 < v.mean() < 1:
                mi.append(v)
                mi_cols.append(f"miss_{c}")
    return np.column_stack(V), cols, blk, (np.column_stack(mi) if mi else None), mi_cols


def run_design(D, rows_mask, base, arm, perm):
    r = np.where(rows_mask)[0]
    t = D.t[r]
    parts = [D.Gm[g][r] for g in BASES[base] if g != "HD"]
    if "HD" in BASES[base]:
        H, _ = D.hd(rows=r)
        parts.append(H)
    if arm == "ECG":
        parts.append(D.ecg_pc[r])
    elif arm == "permECG":
        parts.append(D.ecg_pc[perm][r])
    X = np.hstack(parts)
    lg = ps_logit(X, t)
    idx, cl, _ = match(lg, t)
    return r, t, idx, cl


def analyze_trial(k):
    D = VA.TrialData(tdir(k))
    rct = json.load(open(D.dir / "rct.json"))
    rb = np.log(rct["our_orientation"])
    rs = (np.log(rct["our_hi"]) - np.log(rct["our_lo"])) / (2 * 1.96)
    perm = np.random.default_rng(SEED).permutation(len(D.t))
    lag = D.lag if D.lag is not None else np.full(len(D.t), np.nan)
    pops = {"all": np.ones(len(D.t), bool), "no_index_day_ecg": ~(lag < 1)}
    rows, vrows = [], []
    for base in BASES:
        V, cols, blk, MI, mi_cols = panel_for(D, k, base)
        for pop, mask in pops.items():
            if min((D.t[mask] == 1).sum(), (D.t[mask] == 0).sum()) < 50:
                continue
            # unmatched reference (once per base/pop)
            r = np.where(mask)[0]
            t = D.t[r]
            s_un = smd_vector(V[r], t, np.where(t == 1)[0], np.where(t == 0)[0])
            for arm in ("base", "ECG", "permECG"):
                r, t, idx, cl = run_design(D, mask, base, arm, perm)
                mt, mc = idx[t[idx] == 1], idx[t[idx] == 0]
                s = smd_vector(V[r], t, mt, mc)
                smi = smd_vector(MI[r], t, mt, mc) if MI is not None else np.array([])
                ok = np.isfinite(s)
                T, E = D.T[r], D.E[r].astype(int)
                b, se = cox(T[idx], E[idx], t[idx], cluster=cl)
                row = dict(trial=k, base=base, arm=arm, pop=pop, n_pairs=len(idx) // 2, n_vars=int(ok.sum()),
                           pct_bal=float(100 * np.mean(s[ok] < 0.1)), mean_smd=float(np.mean(s[ok])),
                           mean_smd_unmatched=float(np.nanmean(s_un)),
                           pct_bal_miss=float(100 * np.mean(smi[np.isfinite(smi)] < 0.1)) if len(smi) else np.nan,
                           loghr=b, se=se, rct_loghr=rb, rct_se=rs, rct_measure=rct.get("measure", "HR"),
                           events=int(E[idx].sum()) if E[idx].sum() >= 11 else -1)
                for bb in sorted(set(blk)):
                    j = [i for i, x in enumerate(blk) if x == bb and np.isfinite(s[i])]
                    row[f"mean_smd_{bb}"] = float(np.mean(s[j])) if j else np.nan
                    row[f"pct_bal_{bb}"] = float(100 * np.mean(s[j] < 0.1)) if j else np.nan
                rows.append(row)
                for c, bb, x, xu in zip(cols, blk, s, s_un):
                    vrows.append(dict(trial=k, base=base, arm=arm, pop=pop, var=c, block=bb, abs_smd=x, abs_smd_unmatched=xu))
    (OUT / "results").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "results" / f"{k}_arms.csv", index=False)
    pd.DataFrame(vrows).to_csv(OUT / "results" / f"{k}_vars.csv", index=False)
    print(k, "done", flush=True)
    return k


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    OUT.mkdir(parents=True, exist_ok=True)
    if cmd == "gate":
        sys.exit(0 if gate() else 1)
    if cmd == "heldout":
        for k in args:
            heldout(k)
    if cmd == "analyze":
        assert (OUT / "gate" / "PASS").exists(), "reproduction gate has not passed"
        with Pool(min(8, len(args))) as p:
            p.map(analyze_trial, args)
