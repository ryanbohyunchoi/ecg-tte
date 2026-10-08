#!/usr/bin/env python
"""v1 code audit: re-run paper2_plasmode.one() (unmodified, imported) for a few cells x replicates with the NEW arms and
compare with the published replicate outputs reps_<variant>_p5.csv (exact reproducibility of the new arms), plus a
synthetic unit test of g2b.pooled() (ratio of summed cell-mean errors, null correction). Aggregates only.
Output: /mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/code/plasmode_rerun_newarms.csv
"""
import os
import sys
from pathlib import Path

os.umask(0o077)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "v21"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import paper2_plasmode as P  # noqa: E402

OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v1-audit/code")
CELLS = [("trtC_adv", "comet", "lvef"), ("trtC_adv", "plato", "egfr"), ("trtC", "aristotle", "bmi"), ("trtC", "affirm", "ntprobnp")]
REPS = [0, 37]


def job(a):
    v, n, c, rep = a
    info = P.G2B.cells()[(n, c)]
    return v, P.one((n, c, rep, info, v, P.NEW_ARMS))


def synthetic():
    # 2 cells x 2 reps, arms ref/arm; errors chosen so the expected values are known
    rows = []
    for tr, base_err in (("t1", 0.2), ("t2", 0.4)):
        for rep in (0, 1):
            for (o, h) in ((1.0, 1.0), (2.0, 2.0)):
                null = o == 1.0
                rows += [dict(trial=tr, conf="lvef", or_t=o, hr_y=h, rep=rep, arm="unmatched", loghr=(0.01 if null else base_err), truth=0.0, se=0.1),
                         dict(trial=tr, conf="lvef", or_t=o, hr_y=h, rep=rep, arm="base", loghr=(0.02 if null else base_err / 2), truth=0.0, se=0.1)]
    R = pd.concat([pd.DataFrame(rows).assign(conf=c) for c in P.CONF], ignore_index=True)  # pooled() needs every confounder
    R["loghr"] += np.where(R.rep == 0, 0.001, -0.001)  # symmetric jitter (cancels in cell means; avoids zero empirical SE)
    R["err"] = R.loghr - R.truth
    R["cover"] = (R.err.abs() <= 1.96 * R.se).astype(float)
    S, _ = P.G2B.pooled(R, ["unmatched", "base"], ref_arms=("unmatched",), B=20)
    raw = S[(S.analysis == "raw") & (S.arm == "base") & (S.conf == "all")].pct_vs_unmatched.iloc[0]
    nc = S[(S.analysis == "null-corrected") & (S.arm == "base") & (S.conf == "all")].pct_vs_unmatched.iloc[0]
    exp_raw = 100 * (1 - (0.1 + 0.2) / (0.2 + 0.4))
    exp_nc = 100 * (1 - ((0.1 - 0.02) + (0.2 - 0.02)) / ((0.2 - 0.01) + (0.4 - 0.01)))
    return [dict(check="synthetic pooled raw % removed", value=raw, expected=exp_raw),
            dict(check="synthetic pooled null-corrected % removed", value=nc, expected=exp_nc)]


def main():
    from multiprocessing import Pool
    jobs = [(v, n, c, r) for v, n, c in CELLS for r in REPS]
    with Pool(min(8, len(jobs))) as p:
        res = p.map(job, jobs)
    out = []
    key = ["trial", "conf", "or_t", "hr_y", "rep", "arm"]
    for v in ("trtC_adv", "trtC"):
        R = pd.DataFrame([x for vv, o in res if vv == v for x in o])
        R = P.roundtrip(P.suppress(R))
        ref = pd.read_csv(P.OUT / f"reps_{v}_p5.csv", float_precision="round_trip")
        m = R.merge(ref, on=key, suffixes=("", "_ref"))
        dev = {k: float(np.nanmax(np.abs(m[k] - m[f"{k}_ref"]))) for k in ("loghr", "se", "truth", "n_an", "n_t", "n_sub")}
        out.append(dict(check=f"rerun new arms vs reps_{v}_p5.csv", rows=len(R), matched=len(m), **{f"maxdev_{k}": d for k, d in dev.items()}))
    out += synthetic()
    D = pd.DataFrame(out)
    D.to_csv(OUT / "plasmode_rerun_newarms.csv", index=False)
    print(D.to_string(index=False))


if __name__ == "__main__":
    main()
