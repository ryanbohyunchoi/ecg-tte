#!/usr/bin/env python
"""Core clinical baseline for any roster (trial cohort or external reference set).

Contract (COMET PSM table v2 analogue, rebuilt on OMOP gold):
  demographics   age_at_index (exact DOB), male (gender_concept_id 8507), index_year
  lvef           latest echo EF (5-90) in [index-365, index-1]
  vitals/labs    latest value in [index-L, index-1] (L per trial_specs.NUMERIC_CORE),
                 outside the plausible range -> missing (no older fallback)
  comorbidities  any ICD-10 prefix match in [index-365, index-1]
  medications    any order (token match) in [index-90, index-1]
  utilisation    visit counts by concept (9202/9203/9201) in [index-365, index-1]
  trial extras   declared in trial_specs (e.g. PLATO index-event characteristics)
The index day is excluded everywhere except declared index-event features.

Imputation (--imputations M > 0): M chained-equation datasets with
sklearn IterativeImputer(sample_posterior=True), seeded, using all covariates and
the treatment indicator as predictors; imputed values are clipped to the
plausible range. Observed values are preserved. No outcomes are used.

Outputs (restricted, private run dir):
  restricted_baseline_observed.parquet   patient_key, treated, covariates (NaN = missing)
  restricted_completed_XX.parquet        same, imputed (if --imputations > 0)
  roles.json                             covariate groups for the evaluator
  summary.json                           missingness / prevalence by arm (aggregate)
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import code_like, connect, create_drug_tokens, mrn_key, new_private_dir, rp, sha256, write_manifest  # noqa: E402
from trial_specs import (DEMO, DX_CORE, HELDOUT_PHYSIOLOGY, LVEF_LOOKBACK, NUMERIC_CORE,  # noqa: E402
                         PCI_CODES, STEMI_CODES, TRIALS, UTILISATION)


def build(con, gold, echo_meta, roster: pd.DataFrame, spec: dict) -> pd.DataFrame:
    con.register("roster_df", roster[["patient_key", "person_id", "index_date"]])
    con.execute("CREATE OR REPLACE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, "
                "CAST(index_date AS DATE) idx FROM roster_df")
    base = con.execute(f"""SELECT r.patient_key,
            date_diff('day', CAST(p.birth_datetime AS DATE), r.idx) / 365.25 age_at_index,
            CASE WHEN p.gender_concept_id = 8507 THEN 1.0 WHEN p.gender_concept_id = 8532 THEN 0.0 END male,
            year(r.idx)::DOUBLE index_year
        FROM r LEFT JOIN {rp(gold, 'person')} p USING (person_id)""").df().set_index("patient_key")

    con.execute(f"""CREATE OR REPLACE TEMP TABLE echo AS SELECT {mrn_key('MRN')} k, try_cast(EchoDate AS DATE) d, EF
        FROM read_parquet('{echo_meta}') WHERE EF BETWEEN 5 AND 90 AND try_cast(EchoDate AS DATE) IS NOT NULL""")
    lvef = con.execute(f"""SELECT r.patient_key, arg_max(e.EF, (e.d, e.EF)) lvef FROM r
        JOIN (SELECT person_id, {mrn_key('person_source_value')} k FROM {rp(gold, 'person')}) p USING (person_id)
        JOIN echo e ON e.k = p.k
        WHERE e.d BETWEEN r.idx - INTERVAL {LVEF_LOOKBACK} DAY AND r.idx - INTERVAL 1 DAY GROUP BY 1""").df()
    base = base.join(lvef.set_index("patient_key"))

    con.register("num_df", pd.DataFrame([(n, v[0], v[1], v[2], v[3]) for n, v in NUMERIC_CORE.items()],
                                        columns=["name", "cid", "days", "lo", "hi"]))
    meas = con.execute(f"""SELECT r.patient_key, n.name, arg_max(m.value_as_number, (m.measurement_datetime, m.value_as_number)) v
        FROM r JOIN {rp(gold, 'measurement')} m USING (person_id)
        JOIN num_df n ON m.measurement_concept_id = n.cid
        WHERE m.value_as_number IS NOT NULL
          AND m.measurement_date BETWEEN r.idx - n.days * INTERVAL 1 DAY AND r.idx - INTERVAL 1 DAY
        GROUP BY 1, 2""").df().pivot(index="patient_key", columns="name", values="v")
    for name, (_, _, lo, hi) in NUMERIC_CORE.items():
        s = meas[name] if name in meas else pd.Series(dtype=float)
        base[name] = s.where((s >= lo) & (s <= hi)).reindex(base.index)

    dx = dict(DX_CORE)
    dx.update({k: v for k, v in spec.get("extra_dx", {}).items() if v})
    allp = sorted({p for v in dx.values() for p in v} | set(STEMI_CODES))
    con.execute(f"""CREATE OR REPLACE TEMP TABLE cond AS SELECT r.patient_key, r.idx, c.condition_start_date d,
            upper(replace(c.condition_source_value, '.', '')) code
        FROM r JOIN {rp(gold, 'condition_occurrence')} c USING (person_id)
        WHERE c.condition_start_date BETWEEN r.idx - INTERVAL 365 DAY AND r.idx""")
    con.execute(f"DELETE FROM cond WHERE NOT {code_like('code', allp)}")
    for name, pre in dx.items():
        s = con.execute(f"""SELECT DISTINCT patient_key FROM cond WHERE d < idx AND {code_like('code', pre)}""").df()
        base[name] = base.index.isin(s.patient_key).astype(float)
    if "stemi_30d" in spec.get("extra_dx", {}):
        # index-event characteristic: STEMI code in [index-30, index] (index day included)
        s = con.execute(f"""SELECT DISTINCT patient_key FROM cond WHERE d >= idx - INTERVAL 30 DAY
                           AND {code_like('code', STEMI_CODES)}""").df()
        base["stemi_30d"] = base.index.isin(s.patient_key).astype(float)
    if spec.get("index_event_pci"):
        s = con.execute(f"""SELECT DISTINCT r.patient_key FROM r JOIN {rp(gold, 'procedure_occurrence')} p USING (person_id)
            WHERE p.procedure_date BETWEEN r.idx - INTERVAL 30 DAY AND r.idx
              AND {code_like('upper(p.procedure_source_value)', PCI_CODES)}""").df()
        base["pci_index_30d"] = base.index.isin(s.patient_key).astype(float)

    drugs = spec["drugs_90d"]
    create_drug_tokens(con, gold, [k for v in drugs.values() for k in v], table="btok", person_filter="r")
    tok = con.execute("""SELECT DISTINCT r.patient_key, b.tok FROM r JOIN btok b USING (person_id)
                         WHERE b.d BETWEEN r.idx - INTERVAL 90 DAY AND r.idx - INTERVAL 1 DAY""").df()
    for name, kws in drugs.items():
        keys = set(tok[tok.tok.isin({k.lower() for k in kws})].patient_key)
        base[name] = base.index.isin(keys).astype(float)

    vis = con.execute(f"""SELECT r.patient_key, v.visit_concept_id c, count(DISTINCT v.visit_occurrence_id) n
        FROM r JOIN {rp(gold, 'visit_occurrence')} v USING (person_id)
        WHERE v.visit_start_date BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY GROUP BY 1, 2""").df()
    for name, c in UTILISATION.items():
        base[name] = vis[vis.c == c].set_index("patient_key").n.reindex(base.index).fillna(0).astype(float)
    return base.reindex(roster.patient_key)


def impute(obs: pd.DataFrame, treated: np.ndarray, m: int, seed: int = 20260923):
    from sklearn.experimental import enable_iterative_imputer  # noqa: F401
    from sklearn.impute import IterativeImputer
    bounds = {"lvef": (5, 90), **{k: (v[2], v[3]) for k, v in NUMERIC_CORE.items()}}
    X = obs.copy()
    X["__treated"] = treated
    miss_cols = [c for c in obs.columns if obs[c].isna().any()]
    out = []
    for i in range(m):
        imp = IterativeImputer(sample_posterior=True, max_iter=10, random_state=seed + i, skip_complete=True)
        Z = pd.DataFrame(imp.fit_transform(X), index=X.index, columns=X.columns).drop(columns="__treated")
        for c in miss_cols:
            lo, hi = bounds.get(c, (obs[c].min(), obs[c].max()))
            Z[c] = Z[c].clip(lo, hi)
            if set(obs[c].dropna().unique()) <= {0.0, 1.0}:
                Z[c] = (Z[c] > 0.5).astype(float)
        Z[obs.notna()] = obs[obs.notna()]
        out.append(Z)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", required=True, choices=sorted(TRIALS))
    ap.add_argument("--roster", required=True, help="parquet with patient_key, person_id, index_date[, treated]")
    ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
    ap.add_argument("--echo-metadata", default="/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet")
    ap.add_argument("--imputations", type=int, default=5)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--threads", type=int, default=48)
    a = ap.parse_args()
    spec = TRIALS[a.trial]
    out = new_private_dir(a.output_dir)
    roster = pd.read_parquet(a.roster)
    if "person_id" not in roster:  # link by exact person_source_value (identity contract)
        con0 = connect(8)
        pm = con0.execute(f"SELECT person_source_value patient_key, person_id FROM {rp(a.omop_dir, 'person')}").df()
        roster = roster.merge(pm.drop_duplicates("patient_key", keep=False), on="patient_key", how="inner")
    if "treated" not in roster:
        roster["treated"] = 0
    con = connect(a.threads)
    obs = build(con, a.omop_dir, a.echo_metadata, roster, spec)
    treated = roster.set_index("patient_key").treated.reindex(obs.index).to_numpy()
    obs.insert(0, "treated", treated)
    obs.reset_index().to_parquet(out / "restricted_baseline_observed.parquet")
    cov = obs.drop(columns="treated")
    if a.imputations:
        for i, Z in enumerate(impute(cov, treated, a.imputations), start=1):
            Z.insert(0, "treated", treated)
            Z.reset_index().to_parquet(out / f"restricted_completed_{i:02d}.parquet")
    core = list(cov.columns)
    roles = dict(trial=a.trial, core=core, demo=DEMO,
                 claims=[c for c in core if c not in HELDOUT_PHYSIOLOGY],
                 heldout_physiology=[c for c in HELDOUT_PHYSIOLOGY if c in core],
                 report_covariates=spec["report_covariates"], imputations=a.imputations,
                 exposure_features=sorted({f"rx_{kw.lower()}" for _, kws in spec["arms"] for kw in kws}
                                          | {f"rx_{kw.lower()}" for kw in spec.get("prior_class", [])}))
    json.dump(roles, open(out / "roles.json", "w"), indent=2)
    by = {}
    for arm, g in obs.groupby("treated"):
        by[str(int(arm))] = dict(n=int(len(g)), missing_frac={c: round(float(g[c].isna().mean()), 3) for c in core if g[c].isna().any()},
                                 mean={c: round(float(g[c].mean()), 3) for c in core})
    json.dump(dict(trial=a.trial, n=int(len(obs)), by_treated=by, roster=str(a.roster)),
              open(out / "summary.json", "w"), indent=2)
    write_manifest(out, dict(script_sha256=sha256(Path(__file__)), roster_sha256=sha256(Path(a.roster))))
    print(json.dumps(by, indent=1)[:4000])


if __name__ == "__main__":
    main()
