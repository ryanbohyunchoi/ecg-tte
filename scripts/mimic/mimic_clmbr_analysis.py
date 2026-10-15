#!/usr/bin/env python
"""Step 3: MIMIC-IV PS-CVD5 analog x {base, + ECG, + CLMBR-T, + ECG + CLMBR-T, + permuted ECG, + permuted CLMBR-T}.

Design = the existing MIMIC PS-CVD5 analysis (scripts/v21/mimic_cvd5.py), unchanged: v15_analyze.TrialData per trial;
PS-CVD5 = v1.5 demo + HTN, T2D, CAD, AF, HF from earlier admissions (flags rebuilt in Step 0, equal to v21), constant
flags dropped; fixed C = 1 ridge logistic regression on standardised inputs (v13_common.ps_logit); 1:1 greedy nearest
neighbour on the logit, caliper 0.2 SD, without replacement (v13_common.match); Cox with robust SE clustered on pairs;
the 26-item held-out panel (mimic_replication.panel_for); ECG = 32 within-trial PCs; permuted placebos use the v21
within-trial permutation (seed 20261001), the same vector for the permuted CLMBR-T.
New: CLMBR-T = 64 within-trial PCs of the 768-d code-only embedding (v13_common.clm_pc: eval_longtail_balance.pcs on
the analysed patients of the trial); the index-day-ECG sensitivity reuses the full-cohort PCs (as v20 note 4).
Bases: cvd5 (primary) and the existing design-detail sensitivities cvd5_anydm, cvd5_incl; populations all and
no_index_day_ecg. Writes OUT/results/<k>_{arms,vars}.csv (restricted: they hold per-trial pair counts) and
OUT/results/gate_v21.json (base / ECG / permECG rows must equal the v21 results exactly).
"""
from __future__ import annotations

import glob
import json
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from mimic_common import CLMBR, OUT, status
import mimic_cvd5 as C5  # noqa: E402
import mimic_replication as M  # noqa: E402
import v15_analyze as VA  # noqa: E402
from eval_longtail_balance import pcs, smd_vector  # noqa: E402
from v13_common import cox, match, ps_logit  # noqa: E402

TRIALS = M.BUILT + M.NEW
BASES = ["cvd5", "cvd5_anydm", "cvd5_incl"]
ARMS = {"base": [], "ECG": ["ECG"], "permECG": ["permECG"], "CLMBR": ["CLMBR"], "ECG+CLMBR": ["ECG", "CLMBR"],
        "permCLMBR": ["permCLMBR"]}
RES = OUT / "results"
EMB = CLMBR / "full"


def clmbr_matrix(k, pids):
    E = pd.concat([pd.read_parquet(f, columns=["trial", "pid", "embedding"], filters=[("trial", "==", k)])
                   for f in sorted(glob.glob(str(EMB / "restricted_embeddings_part-*.parquet")))])
    assert not E.pid.duplicated().any(), f"{k}: more than one embedding per patient-index"
    E = E.set_index("pid").reindex(pids.astype(str))
    assert E.embedding.notna().all(), f"{k}: analysed patient without a CLMBR-T embedding"
    X = np.stack(E.embedding.to_numpy()).astype(float)
    assert X.shape[1] == 768 and np.isfinite(X).all()
    return X


def run_trial(k):
    D = VA.TrialData(M.tdir(k))
    F = pd.read_parquet(OUT / "step0" / "flags" / f"{k}.parquet").set_index("pid").reindex(D.pids)
    assert F.notna().all().all()
    C = {b: F[v].to_numpy(float) for b, v in C5.CVD5.items()}
    clm_pc = pcs(clmbr_matrix(k, D.pids), 64)
    rct = json.load(open(D.dir / "rct.json"))
    rb = np.log(rct["our_orientation"])
    rs = (np.log(rct["our_hi"]) - np.log(rct["our_lo"])) / (2 * 1.96)
    perm = np.random.default_rng(M.SEED).permutation(len(D.t))
    lag = D.lag if D.lag is not None else np.full(len(D.t), np.nan)
    pops = {"all": np.ones(len(D.t), bool), "no_index_day_ecg": ~(lag < 1)}
    REP = {"ECG": D.ecg_pc, "permECG": D.ecg_pc[perm], "CLMBR": clm_pc, "permCLMBR": clm_pc[perm]}
    V, cols, blk, MI, mi_cols = M.panel_for(D, k, "demo")
    rows, vrows = [], []
    for base in BASES:
        for pop, mask in pops.items():
            if min((D.t[mask] == 1).sum(), (D.t[mask] == 0).sum()) < 50:
                continue
            r = np.where(mask)[0]
            t = D.t[r]
            s_un = smd_vector(V[r], t, np.where(t == 1)[0], np.where(t == 0)[0])
            Cr = C[base][r]
            Cr = Cr[:, Cr.std(0) > 0]
            for arm, reps in ARMS.items():
                X = np.hstack([D.Gm["demo"][r], Cr] + [REP[x][r] for x in reps])  # order as mimic_cvd5.design
                lg = ps_logit(X, t)
                idx, cl, _ = match(lg, t)
                mt, mc = idx[t[idx] == 1], idx[t[idx] == 0]
                s = smd_vector(V[r], t, mt, mc)
                ok = np.isfinite(s)
                T, E = D.T[r], D.E[r].astype(int)
                b, se = cox(T[idx], E[idx], t[idx], cluster=cl)
                p = 1 / (1 + np.exp(-lg))
                n_small = int(min((t == 1).sum(), (t == 0).sum()))
                rows.append(dict(trial=k, base=base, arm=arm, pop=pop, n_pairs=len(idx) // 2, n_small=n_small,
                                 retention=len(idx) / 2 / n_small, n_inputs=X.shape[1], c_insample=float(roc_auc_score(t, lg)),
                                 share_extreme_ps=float(np.mean((p < 0.01) | (p > 0.99))), n_vars=int(ok.sum()),
                                 pct_bal=float(100 * np.mean(s[ok] < 0.1)), mean_smd=float(np.mean(s[ok])),
                                 loghr=b, se=se, rct_loghr=rb, rct_se=rs, rct_measure=rct.get("measure", "HR"),
                                 events=int(E[idx].sum()) if E[idx].sum() >= 11 else -1, n_dx_flags_in_ps=Cr.shape[1]))
                for c, bb, x, xu in zip(cols, blk, s, s_un):
                    vrows.append(dict(trial=k, base=base, arm=arm, pop=pop, var=c, block=bb, abs_smd=x, abs_smd_unmatched=xu))
    RES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(RES / f"{k}_arms.csv", index=False)
    pd.DataFrame(vrows).to_csv(RES / f"{k}_vars.csv", index=False)
    print(k, "done", flush=True)
    return k


def gate_v21():
    """base / ECG / permECG cells of the cvd5 bases must equal the Step 0 (= v21) results exactly."""
    out = []
    for k in TRIALS:
        for kind, keys, cmp in (("arms", ["base", "arm", "pop"], ["n_pairs", "n_vars", "pct_bal", "mean_smd", "loghr", "se"]),
                                ("vars", ["base", "arm", "pop", "var"], ["abs_smd", "abs_smd_unmatched"])):
            a = pd.read_csv(OUT / "step0" / "results" / f"{k}_{kind}.csv")
            b = pd.read_csv(RES / f"{k}_{kind}.csv")
            a = a[a.base.isin(BASES)].set_index(keys).sort_index()
            b = b[b.arm.isin(["base", "ECG", "permECG"])].set_index(keys).sort_index()
            same = a.index.equals(b.index)
            d = float((a[cmp] - b[cmp]).abs().max().max()) if same else np.inf
            nan_eq = bool((a[cmp].isna() == b[cmp].isna()).all().all()) if same else False
            out.append(dict(trial=k, table=kind, same_rows=same, max_abs_diff=d, nan_equal=nan_eq))
    g = pd.DataFrame(out)
    ok = bool(g.same_rows.all() and (g.max_abs_diff == 0).all() and g.nan_equal.all())
    res = dict(gate="PASS" if ok else "FAIL", n_tables=len(g), max_abs_diff=float(g.max_abs_diff.max()))
    json.dump(res, open(RES / "gate_v21.json", "w"))
    return res


def main():
    with Pool(8) as p:
        p.map(run_trial, TRIALS)
    g = gate_v21()
    print(g)
    status(f"step 3 analysis cells written (8 trials x 3 bases x 2 populations x 6 arms); v21 regression gate {g['gate']} "
           f"(max |diff| {g['max_abs_diff']})")
    return 0 if g["gate"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
