#!/usr/bin/env python
"""Step 1.5: CLMBR-T vocabulary coverage gate (aggregates only), MIMIC analysed patients vs the Yale s31 trials.

MIMIC (OUT/meds/restricted_cohort.parquet, restricted to the analysed pids of each trial, i.e. v15_analyze.TrialData:
cohort & baseline & panel & ECG & outcomes):
  - share of clinical events (birth excluded) whose code is in the CLMBR-T dictionary (code-type entries);
  - median (IQR) in-vocabulary events per patient (= tokens offered to the model, before the 4,096 cap);
  - share of patients with no prior coded history: no in-vocabulary clinical event (the model sees birth only); also
    reported: no history outside the index admission (earlier admissions, outpatient labs, ED visits without admission).
Yale (the s31 trials; CLMBR-T code-only runs, restricted_patient_status.parquet of each run, all cohort patients):
  - accepted / attempted clinical measurements (the encoder's tokenizer check, the same definition);
  - median (IQR) accepted measurements per encoded patient;
  - share of patients not encoded for lack of a supported clinical event (no_clinical_events,
    no_tokenizer_supported_clinical_events).
Stop rule (queue Step 1.5): share in vocabulary < 50%, or > 50% of analysed patients with no prior coded history ->
no inference. Writes OUT/coverage/{coverage.json, by_trial.csv}, OUT/analysed_pids.parquet (restricted), STOP or GO.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from mimic_common import AUD, MEDS, OUT, status, sup
import mimic_replication as M  # noqa: E402

TRIALS = M.BUILT + M.NEW
YALE_S31 = ['comet', 'paradigm-hf-seq', 'transform-hf', 'elite-ii', 'life', 'plato', 'aristotle', 'rocket-af', 'rely',
            'emperor-preserved-v2', 'east-afnet4', 'cabana-v2', 'empa-reg', 'carolina', 'leader', 'sustain6', 'canvas',
            'tecos', 'carmelina', 'valiant', 'insight', 'affirm', 'af-chf', 'precision', 'amplify', 'lodestar',
            'prove-it', 'frail-af', 'laaos3', 'raft-af', 'active-w']  # paper2_grid.S32 minus protect-af (scripts/s31)


def yale_dir(n):
    return AUD / ("comet-clmbr-full-NAyb4G2x/report" if n == "comet" else f"claude-{n}-clmbr-codeonly/report")


def analysed_pids():
    p = OUT / "analysed_pids.parquet"
    if p.exists():
        return pd.read_parquet(p)
    import v15_analyze as VA
    rows = [pd.DataFrame(dict(trial=k, pid=VA.TrialData(M.tdir(k)).pids.astype(str))) for k in TRIALS]
    A = pd.concat(rows, ignore_index=True)
    A.to_parquet(p, index=False)
    return A


def q(x):
    x = np.asarray(x, float)
    return [float(np.median(x)), float(np.percentile(x, 25)), float(np.percentile(x, 75))]


def mimic_stats(R):
    out = dict(n_patients=len(R), share_events_in_vocab=float(R.n_in_vocab.sum() / R.n_events.sum()),
               in_vocab_events_per_patient=q(R.n_in_vocab), events_per_patient=q(R.n_events),
               share_no_prior_coded_history=float((R.n_in_vocab == 0).mean()),
               share_no_clinical_events=float((R.n_events == 0).mean()),
               share_no_history_outside_index_admission=float((R.n_history == 0).mean()),
               share_over_4096_in_vocab=float((R.n_in_vocab > 4096).mean()))
    return out


def yale_stats(names):
    S = []
    for n in names:
        s = pq.read_table(yale_dir(n) / "restricted_patient_status.parquet").to_pandas()
        S.append(s.assign(trial=n))
    S = pd.concat(S, ignore_index=True)
    enc = S[S.status == "encoded"]
    nohist = S.status.isin(["no_clinical_events", "no_tokenizer_supported_clinical_events"])
    return dict(trials=len(names), n_patients=len(S), share_events_in_vocab=float(S.accepted.sum() / S.attempted.sum()),
                in_vocab_events_per_patient=q(enc.accepted), tokens_available_per_patient=q(enc.tokens_available),
                share_no_prior_coded_history=float(nohist.mean()), share_truncated_4096=float((enc.tokens_available > 4096).mean()),
                status_counts={k: sup(v) for k, v in S.status.value_counts().items()})


def main():
    R = pd.read_parquet(MEDS / "restricted_cohort.parquet")
    A = analysed_pids()
    R = R.merge(A, on=["trial", "pid"], how="inner")
    assert len(R) == len(A), "analysed pid without a MEDS subject"
    res = dict(mimic_all8=mimic_stats(R), mimic_primary7=mimic_stats(R[R.trial != "peptic"]),
               yale_s31=yale_stats(YALE_S31),
               yale_matching_trials=yale_stats(["plato", "aristotle", "rocket-af", "transform-hf", "comet", "elite-ii"]))
    bt = []
    for k, g in R.groupby("trial", sort=False):
        s = mimic_stats(g)
        nz = int((g.n_in_vocab == 0).sum())
        bt.append(dict(trial=k, n=len(g), share_in_vocab=round(s["share_events_in_vocab"], 3),
                       median_in_vocab=s["in_vocab_events_per_patient"][0], q1=s["in_vocab_events_per_patient"][1],
                       q3=s["in_vocab_events_per_patient"][2],
                       pct_no_prior_coded_history=round(100 * s["share_no_prior_coded_history"], 1) if (nz == 0 or nz >= 11) else "<11 patients",
                       pct_no_history_outside_index_adm=round(100 * s["share_no_history_outside_index_admission"], 1)))
    m = res["mimic_all8"]
    stop = m["share_events_in_vocab"] < 0.5 or m["share_no_prior_coded_history"] > 0.5
    res["stop_rule"] = dict(threshold_share_in_vocab=0.5, threshold_share_no_history=0.5, fired=bool(stop))
    (OUT / "coverage").mkdir(exist_ok=True)
    json.dump(res, open(OUT / "coverage" / "coverage.json", "w"), indent=1, default=str)
    pd.DataFrame(bt).to_csv(OUT / "coverage" / "by_trial.csv", index=False)
    for f in ("STOP", "GO"):
        (OUT / "coverage" / f).unlink(missing_ok=True)
    (OUT / "coverage" / ("STOP" if stop else "GO")).write_text("")
    print(json.dumps(res, indent=1, default=str))
    print(pd.DataFrame(bt).to_string(index=False))
    y = res["yale_s31"]
    status(f"step 1.5 coverage gate {'STOP' if stop else 'GO'}: MIMIC (8 trials, analysed) in-vocab share "
           f"{m['share_events_in_vocab']:.3f} vs Yale s31 {y['share_events_in_vocab']:.3f}; median in-vocab events "
           f"{m['in_vocab_events_per_patient'][0]:.0f} vs {y['in_vocab_events_per_patient'][0]:.0f}; no prior coded history "
           f"{100 * m['share_no_prior_coded_history']:.1f}% vs {100 * y['share_no_prior_coded_history']:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
