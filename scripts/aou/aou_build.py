#!/usr/bin/env python
"""Per-trial AoU builds on the gold-shaped extract. The Yale builders run UNCHANGED wherever their inputs exist in AoU:

  cohort     scripts/build_trial_cohort.py (runpy; trial_specs.TRIALS[key] replaced in memory by the AoU-adapted spec,
             trial_common.suppress replaced by the AoU 1-20 rule; ECG/echo metadata = empty stubs)
  baseline   build_core_baseline.build + impute (5 draws, seed 20260923), LVEF removed before imputation (pipeline.md
             section 4: PS-Clinical without LVEF; AoU has no echo EF anyway)
  dx10       PS-CVD5 and CVD10 flags: v1_ps10 CODES, condition_source_value ICD-10 prefix in [index-365, index-1]
  flags      PS-Flags source counts: v21/ps_flags.py rule (3-character ICD-10, full history, index day excluded)
  panel      scripts/build_preindex_panel.py (runpy) on meds_gold (rx_ = first word of the drug concept name, lab_ = all
             measurement concepts), 365 days, >= 2 % / >= 20 %: the hdPS pool and the coded held-out items
  labs       build_physiology_panel_v2.LABS rule (latest value in [index-365, index-1]); echo columns do not exist in AoU
  survey     AoU survey items (aou_concepts.SURVEY_QUESTIONS, SURVEY_RULES below): latest answer on or before index
             (primary) and latest answer at any time (sensitivity, stable traits)
  outcomes   extract_outcomes.py logic re-implemented without the CT Vital Statistics linkage: all-cause death substitutes
             CV / CHD death (aou_specs), hospitalisation components unchanged (inpatient stays merged with gap <= 1 day,
             qualifying ICD-10 code dated within the stay, index stay excluded, MI within 28 days counts only as I22).
             Censoring: min(AoU EHR cutoff, last EHR activity + GRACE_DAYS) (primary; AoU participants leave the
             contributing health system) and the EHR cutoff only (sensitivity = the Yale rule).
  meds       build_comet_meds.build (unchanged) -> MEDS for CLMBR-T
  encode     encode_comet_clmbr.encode (unchanged; GPU, femr 0.2.3) -> CLMBR-T 768-d, code-only, last 4,096 tokens

Every trial directory is trials/<name>/<step>/ (private). Aggregates are suppressed at 1-20.

Usage: python scripts/aou/aou_build.py <step> [--trials a,b] [--workers 8]
       steps: cohort | baseline | dx10 | flags | panel | labs | survey | outcomes | meds | encode | all-cpu | status
"""
from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aou_common as AC  # noqa: E402

GRACE_DAYS = 30
FLAGS_LOOKBACK, FLAGS_STORE_MIN_PREV = 36500, 0.001
DX10 = None  # filled lazily from v1_ps10 CODES semantics (import of ps10.py is not AoU-safe: it imports the Yale grid)


def dx10_codes() -> dict:
    """= scripts/v1_ps10/ps10.py CODES (copied: ps10 imports the Yale grid at module level). Checked by tests/test_aou_build."""
    from trial_specs import DX_CORE
    return {"hypertension_v11": DX_CORE["hypertension"], "t2d": ["E11"], "cad_ihd": DX_CORE["ischemic_heart_disease_or_mi"],
            "atrial_fibrillation": DX_CORE["atrial_fibrillation"], "hf_any_365": ["I50", "I110", "I130", "I132"],
            "ckd": DX_CORE["ckd"], "copd_or_asthma": DX_CORE["copd_or_asthma"],
            "peripheral_arterial_disease": DX_CORE["peripheral_arterial_disease"],
            "stroke_tia": DX_CORE["stroke_history"] + ["G45"], "valve_disease": DX_CORE["valve_disease"]}


P5_COLS = ["hypertension_v11", "t2d", "cad_ihd", "atrial_fibrillation", "hf_any_365"]
CVD10_COLS = P5_COLS + ["ckd", "copd_or_asthma", "peripheral_arterial_disease", "stroke_tia", "valve_disease"]

# answer-name rules (lower-case substrings, first match wins); skip / prefer not / don't know -> missing.
# The probe lists the answer names present; review SURVEY_RULES against probe.json before the survey step.
MISSING_ANSWERS = ("skip", "prefer not", "don't know", "dont know", "not sure", "unknown")
SURVEY_RULES = {
    "smoke_100": [("yes", 1.0), ("no", 0.0)],
    "smoke_freq": [("every day", 1.0), ("some days", 1.0), ("not at all", 0.0)],
    "alcohol_any": [("yes", 1.0), ("no", 0.0)],
    "alcohol_freq": [("never", 0.0), ("monthly or less", 1.0), ("2-4 per month", 2.0), ("2 to 4", 2.0), ("2-3 per week", 3.0),
                     ("2 to 3", 3.0), ("4 or more", 4.0)],
    "education": [("advanced degree", 1.0), ("college graduate", 1.0), ("college one to three", 0.0), ("some college", 0.0),
                  ("twelve or ged", 0.0), ("high school", 0.0), ("nine through eleven", 0.0), ("one through four", 0.0),
                  ("five through eight", 0.0), ("never attended", 0.0)],
    "income": [("less 10k", 1.0), ("10k 25k", 1.0), ("25k 35k", 1.0), ("35k 50k", 0.0), ("50k 75k", 0.0), ("75k 100k", 0.0),
               ("100k 150k", 0.0), ("150k 200k", 0.0), ("more 200k", 0.0)],
    "employment": [("employed for wages", 1.0), ("self employed", 1.0), ("self-employed", 1.0), ("out of work", 0.0),
                   ("homemaker", 0.0), ("student", 0.0), ("retired", 0.0), ("unable to work", 0.0)],
    "insurance": [("yes", 1.0), ("no", 0.0)],
    "home_own": [("own", 1.0), ("rent", 0.0), ("other arrangement", 0.0)],
    "marital": [("married", 1.0), ("living with partner", 1.0), ("never married", 0.0), ("divorced", 0.0), ("widowed", 0.0),
                ("separated", 0.0)],
    "general_health": [("excellent", 5.0), ("very good", 4.0), ("good", 3.0), ("fair", 2.0), ("poor", 1.0)],
}
SURVEY_ITEMS = {  # held-out item -> (source item, label)
    "sv_smoke_ever": ("smoke_100", "Smoked >= 100 cigarettes"), "sv_smoke_current": ("smoke_freq", "Current smoking"),
    "sv_alcohol_any": ("alcohol_any", "Any alcohol"), "sv_alcohol_freq": ("alcohol_freq", "Drinking frequency (0-4)"),
    "sv_college": ("education", "College degree"), "sv_income_lt35k": ("income", "Household income < $35k"),
    "sv_employed": ("employment", "Employed"), "sv_insured": ("insurance", "Health insurance"),
    "sv_home_own": ("home_own", "Owns home"), "sv_partnered": ("marital", "Married / partnered"),
    "sv_general_health": ("general_health", "Self-rated health (1-5)"),
}


def code_answer(item: str, name) -> float:
    """Coded value of one survey answer: exact match of the answer (text after the last ':') first, then substring
    match for rules longer than 3 characters, in rule order; missing-type answers -> NaN."""
    if not isinstance(name, str):
        return np.nan
    s = name.lower()
    if any(m in s for m in MISSING_ANSWERS):
        return np.nan
    tail = s.rsplit(":", 1)[-1].strip()
    for sub, v in SURVEY_RULES[item]:
        if tail == sub:
            return v
    for sub, v in SURVEY_RULES[item]:
        if len(sub) > 3 and sub in tail:
            return v
    return np.nan


# ---------------------------------------------------------------- helpers
def cfg() -> dict:
    X = AC.paths()["extract"]
    if not (X / "config.json").exists():
        raise SystemExit("extract/config.json missing: run aou_extract.py stage1 first")
    return json.loads((X / "config.json").read_text())


def adapted() -> dict:
    import aou_specs as S
    return S.adapt_all(cfg()["ehr_cutoff"])


def roster(n: str) -> pd.DataFrame:
    return pd.read_parquet(AC.trial_dir(n) / "cohort" / "restricted_cohort.parquet")


def con(threads=8):
    from trial_common import connect
    return connect(threads, memory_limit=os.environ.get("AOU_DUCKDB_MEMORY", "48GB"))


def done(d: Path) -> bool:
    return (d / "DONE").exists()


def mark(d: Path, info: dict) -> None:
    AC.write_json(d / "summary_aou.json", info)
    (d / "DONE").write_text(time.strftime("%Y-%m-%d %H:%M") + "\n")


# ---------------------------------------------------------------- cohort (Yale builder, unchanged)
def step_cohort(n: str, A: dict, threads=8) -> dict:
    a = A[n]
    if "stopped" in a:
        return dict(trial=n, status="stopped", reason=a["stopped"])
    d = AC.trial_dir(n) / "cohort"
    if (d / "restricted_cohort.parquet").exists():
        return dict(trial=n, status="exists")
    AC.private_dir(d.parent)
    import trial_common
    import trial_specs
    trial_specs.TRIALS[a["key"]] = a["spec"]  # in memory only; trial_specs.py is not modified
    trial_common.suppress = lambda v, min_cell=AC.MIN_COUNT + 1: AC.suppress20(v)
    _connect = getattr(trial_common, "_yale_connect", trial_common.connect)
    trial_common._yale_connect = _connect
    trial_common.connect = lambda threads=8, memory_limit=None: _connect(threads, os.environ.get("AOU_DUCKDB_MEMORY", "48GB"))
    X = AC.paths()["extract"]
    argv = sys.argv
    sys.argv = ["build_trial_cohort.py", "--trial", a["key"], "--omop-dir", str(AC.paths()["gold"]),
                "--ecg-metadata", str(X / "stubs" / "ecg_metadata_empty.parquet"),
                "--echo-metadata", str(X / "stubs" / "echo_metadata_empty.parquet"), "--output-dir", str(d), "--threads", str(threads)]
    try:
        runpy.run_path(str(AC.SCRIPTS / "build_trial_cohort.py"), run_name="__main__")
    finally:
        sys.argv = argv
    AC.write_json(d / "aou_adaptation.json", a["record"])
    return dict(trial=n, status="built")


# ---------------------------------------------------------------- baseline (Yale build + impute)
def step_baseline(n: str, A: dict, threads=8, m=5) -> dict:
    from build_core_baseline import build, impute
    from trial_specs import DEMO, HELDOUT_PHYSIOLOGY
    d = AC.trial_dir(n) / "baseline"
    if done(d):
        return dict(trial=n, status="exists")
    AC.private_dir(d)
    a = A[n]
    ro = roster(n)
    X = AC.paths()["extract"]
    obs = build(con(threads), str(AC.paths()["gold"]), str(X / "stubs" / "echo_metadata_empty.parquet"), ro, a["spec"])
    assert obs["lvef"].isna().all(), "AoU has no echo EF; lvef must be empty"
    obs = obs.drop(columns=["lvef"])
    tr = ro.set_index("patient_key").treated.reindex(obs.index).to_numpy()
    o2 = obs.copy()
    o2.insert(0, "treated", tr)
    o2.reset_index().to_parquet(d / "restricted_baseline_observed.parquet")
    for i, Z in enumerate(impute(obs, tr, m, seed=AC.SEED_IMPUTE), start=1):
        Z = Z.copy()
        Z.insert(0, "treated", tr)
        Z.reset_index().to_parquet(d / f"restricted_completed_{i:02d}.parquet")
    spec = a["spec"]
    core = list(obs.columns)
    roles = dict(trial=a["key"], core=core, demo=DEMO, claims=[c for c in core if c not in HELDOUT_PHYSIOLOGY],
                 heldout_physiology=[c for c in HELDOUT_PHYSIOLOGY if c in core],
                 report_covariates=[c for c in spec["report_covariates"] if c != "lvef"], imputations=m,
                 exposure_features=sorted({f"rx_{kw.lower()}" for _, kws in spec["arms"] for kw in kws}
                                          | {f"rx_{kw.lower()}" for kw in spec.get("prior_class", [])}))
    AC.write_json(d / "roles.json", roles)
    miss = {c: round(float(obs[c].isna().mean()), 3) for c in core if obs[c].isna().any()}
    mark(d, dict(trial=n, n=AC.suppress20(len(obs)), n_cov=len(core), missing_frac=miss))
    return dict(trial=n, status="built")


# ---------------------------------------------------------------- PS-CVD5 / CVD10 flags
def step_dx10(n: str, A: dict, threads=8) -> dict:
    from trial_common import code_like, rp
    d = AC.trial_dir(n) / "dx10"
    if done(d):
        return dict(trial=n, status="exists")
    AC.private_dir(d)
    ro = roster(n)
    c = con(threads)
    c.register("r0", ro[["patient_key", "person_id", "index_date"]])
    c.execute("CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx FROM r0")
    codes = dx10_codes()
    allp = sorted({p for v in codes.values() for p in v})
    c.execute(f"""CREATE TEMP TABLE cond AS SELECT r.patient_key, upper(replace(x.condition_source_value, '.', '')) code
        FROM r JOIN {rp(str(AC.paths()['gold']), 'condition_occurrence')} x USING (person_id)
        WHERE x.condition_start_date BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY""")
    c.execute(f"DELETE FROM cond WHERE NOT {code_like('code', allp)}")
    out = pd.DataFrame(index=pd.Index(ro.patient_key, name="patient_key"))
    for k, pre in codes.items():
        s = c.execute(f"SELECT DISTINCT patient_key FROM cond WHERE {code_like('code', pre)}").df()
        out[k] = out.index.isin(s.patient_key).astype(float)
    out.reset_index().to_parquet(d / "restricted_dx10.parquet")
    mark(d, dict(trial=n, prevalence={k: round(float(v), 4) for k, v in out.mean().items()
                                      if AC.MIN_COUNT < out[k].sum() < len(out) - AC.MIN_COUNT}))
    return dict(trial=n, status="built")


# ---------------------------------------------------------------- PS-Flags source panel
def step_flags(n: str, A: dict, threads=8) -> dict:
    import duckdb
    d = AC.trial_dir(n) / "flags"
    if done(d):
        return dict(trial=n, status="exists")
    AC.private_dir(d)
    coh = roster(n)[["patient_key", "person_id", "index_date"]].drop_duplicates("patient_key")
    g = sorted(str(p) for p in (AC.paths()["gold"] / "condition_occurrence").rglob("*.parquet"))
    cn = duckdb.connect()
    cn.execute(f"SET threads={threads}")
    cn.register("coh_df", coh)
    cn.execute("CREATE TABLE pmap AS SELECT patient_key, CAST(index_date AS DATE) AS idx, CAST(person_id AS BIGINT) person_id FROM coh_df")
    npat = cn.execute("SELECT count(DISTINCT patient_key) FROM pmap").fetchone()[0]
    q = f"""SELECT m.patient_key, m.idx, t.condition_start_date AS day,
                   'dx_' || upper(substr(replace(condition_source_value, '.', ''), 1, 3)) AS f
            FROM read_parquet({g}, hive_partitioning=true) t JOIN pmap m USING (person_id)
            WHERE t.condition_start_date >= m.idx - INTERVAL {FLAGS_LOOKBACK} DAY AND t.condition_start_date < m.idx"""
    cn.execute(f"CREATE TABLE x AS SELECT patient_key, f, count(DISTINCT day) AS c FROM ({q}) WHERE f IS NOT NULL GROUP BY 1, 2")
    D = cn.execute(f"""SELECT patient_key, f, c FROM x WHERE f IN (SELECT f FROM x GROUP BY f
                       HAVING count(DISTINCT patient_key) >= {FLAGS_STORE_MIN_PREV * npat})""").df()
    W = D.pivot(index="patient_key", columns="f", values="c").reindex(coh.patient_key.unique()).fillna(0).astype("uint16")
    W.index.name = "patient_key"
    W.reset_index().to_parquet(d / "restricted_flags.parquet")
    mark(d, dict(trial=n, n_codes_stored=int(W.shape[1]), lookback_days=FLAGS_LOOKBACK))
    return dict(trial=n, status="built")


# ---------------------------------------------------------------- hdPS / coded panel (Yale builder, unchanged)
def step_panel(n: str, A: dict, threads=8) -> dict:
    d = AC.trial_dir(n) / "panel"
    if (d / "restricted_panel.parquet").exists():
        return dict(trial=n, status="exists")
    if not (AC.paths()["meds_gold"] / "measurement").exists():
        raise SystemExit("meds_gold/measurement missing: run aou_extract.py stage2 after the cohort step")
    argv = sys.argv
    sys.argv = ["build_preindex_panel.py", "--cohort-csv", str(AC.trial_dir(n) / "cohort" / "restricted_cohort.parquet"),
                "--omop-root", str(AC.paths()["meds_gold"]), "--output-dir", str(d), "--threads", str(threads)]
    os.umask(0o077)
    try:
        runpy.run_path(str(AC.SCRIPTS / "build_preindex_panel.py"), run_name="__main__")
    finally:
        sys.argv = argv
    return dict(trial=n, status="built")


# ---------------------------------------------------------------- labs (build_physiology_panel_v2 rule, labs only)
def step_labs(n: str, A: dict, threads=8) -> dict:
    from build_physiology_panel_v2 import LABS
    from trial_common import rp
    d = AC.trial_dir(n) / "labs"
    if done(d):
        return dict(trial=n, status="exists")
    AC.private_dir(d)
    r = roster(n)[["patient_key", "person_id", "index_date"]]
    c = con(threads)
    c.register("r0", r)
    c.execute("CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx FROM r0")
    c.register("labs", pd.DataFrame(list(LABS.items()), columns=["name", "cid"]))
    lab = c.execute(f"""SELECT r.patient_key, l.name, arg_max(m.value_as_number, m.measurement_datetime) v
        FROM r JOIN {rp(str(AC.paths()['gold']), 'measurement')} m USING (person_id) JOIN labs l ON m.measurement_concept_id = l.cid
        WHERE m.value_as_number IS NOT NULL AND m.measurement_date BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY
        GROUP BY 1, 2""").df().pivot(index="patient_key", columns="name", values="v")
    panel = lab.reindex(columns=list(LABS)).reindex(r.patient_key)
    panel.index.name = "patient_key"
    panel.astype(float).reset_index().to_parquet(d / "restricted_physiology_panel.parquet")
    mark(d, dict(trial=n, measured_frac={k: round(float(panel[k].notna().mean()), 4) for k in panel.columns}))
    return dict(trial=n, status="built")


# ---------------------------------------------------------------- survey
def step_survey(n: str, A: dict, threads=8) -> dict:
    import duckdb
    d = AC.trial_dir(n) / "survey"
    if done(d):
        return dict(trial=n, status="exists")
    AC.private_dir(d)
    r = roster(n)[["patient_key", "person_id", "index_date"]].copy()
    r["index_date"] = pd.to_datetime(r.index_date)
    S = duckdb.sql(f"SELECT * FROM read_parquet('{AC.paths()['extract'] / 'survey'}/*.parquet')").df()
    S = S[S.person_id.isin(set(r.person_id))].copy()
    S["v"] = [code_answer(i, a) for i, a in zip(S["item"], S.answer_name)]
    S["observation_date"] = pd.to_datetime(S.observation_date)
    S = S.merge(r, on="person_id")
    S = S[S.v.notna()].sort_values(["patient_key", "item", "observation_date"])
    out = {}
    for tag, sub in (("pre", S[S.observation_date <= S.index_date]), ("any", S)):
        last = sub.groupby(["patient_key", "item"]).v.last().unstack()
        F = pd.DataFrame(index=pd.Index(r.patient_key, name="patient_key"))
        for col, (src, _) in SURVEY_ITEMS.items():
            F[col] = last[src].reindex(F.index) if src in last else np.nan
        # current smoking: 0 for never-smokers (not asked the frequency question)
        if "smoke_100" in last:
            never = last["smoke_100"].reindex(F.index) == 0
            F.loc[never & F.sv_smoke_current.isna(), "sv_smoke_current"] = 0.0
        out[tag] = F
        F.reset_index().to_parquet(d / f"restricted_survey_{tag}.parquet")
    # coding review table: answer name -> coded value, participants per answer (suppressed); no participant rows
    rev = S.groupby(["item", "answer_name", "v"]).person_id.nunique().reset_index(name="persons")
    rev["persons"] = rev.persons.map(AC.suppress20)
    rev.to_csv(d / "answer_coding.csv", index=False)
    mark(d, dict(trial=n, observed_frac={t: {c: round(float(F[c].notna().mean()), 4) for c in F.columns} for t, F in out.items()}))
    return dict(trial=n, status="built")


# ---------------------------------------------------------------- outcomes
def step_outcomes(n: str, A: dict, threads=8) -> dict:
    from trial_common import code_like, rp
    from trial_specs import HORIZON_MONTHS
    d = AC.trial_dir(n) / "outcomes"
    if done(d):
        return dict(trial=n, status="exists")
    AC.private_dir(d)
    a = A[n]
    G = str(AC.paths()["gold"])
    comps = a["outcome"]
    admin_end = pd.Timestamp(cfg()["ehr_cutoff"])
    r = roster(n)[["patient_key", "person_id", "index_date"]]
    c = con(threads)
    c.register("r0", r)
    c.execute("CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx FROM r0")
    horizon_days = int(round(HORIZON_MONTHS[a["key"]] * 30.4375))
    follow_days = max(horizon_days, int(round(60 * 30.4375)))
    death = c.execute(f"SELECT r.patient_key, min(x.death_date) dd FROM r JOIN {rp(G, 'death')} x USING (person_id) GROUP BY 1").df() \
        .set_index("patient_key").dd
    last = pd.read_parquet(AC.paths()["extract"] / "restricted_last_ehr").set_index("person_id").last_ehr_date
    # stays (= extract_outcomes v1.2 SQL)
    c.execute(f"""CREATE TEMP TABLE iv AS SELECT v.person_id, v.visit_start_date s, coalesce(v.visit_end_date, v.visit_start_date) e
        FROM {rp(G, 'visit_occurrence')} v WHERE v.visit_concept_id = 9201 AND v.person_id IN (SELECT person_id FROM r)""")
    c.execute("""CREATE TEMP TABLE stays AS
        WITH o AS (SELECT *, max(e) OVER (PARTITION BY person_id ORDER BY s, e ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) pe FROM iv),
             g AS (SELECT *, sum(CASE WHEN pe IS NULL OR s > pe + INTERVAL 1 DAY THEN 1 ELSE 0 END)
                            OVER (PARTITION BY person_id ORDER BY s, e ROWS UNBOUNDED PRECEDING) gid FROM o)
        SELECT person_id, gid, min(s) s, max(e) e FROM g GROUP BY 1, 2""")
    c.execute("""CREATE TEMP TABLE idxstay AS SELECT r.patient_key, r.person_id, r.idx,
            coalesce(max(st.e) FILTER (WHERE st.s <= r.idx AND st.e >= r.idx), r.idx) idx_stay_end
        FROM r LEFT JOIN stays st USING (person_id) GROUP BY 1, 2, 3""")

    def first_hosp(codes, mi=False):
        cond = code_like("upper(replace(c.condition_source_value, '.', ''))", codes)
        if mi:
            cond = f"""({cond} AND (st.s > x.idx + INTERVAL 28 DAY OR upper(replace(c.condition_source_value, '.', '')) LIKE 'I22%'))"""
        return c.execute(f"""SELECT x.patient_key, min(st.s) d FROM idxstay x
            JOIN stays st ON st.person_id = x.person_id AND st.s > x.idx_stay_end
            JOIN {rp(G, 'condition_occurrence')} c ON c.person_id = x.person_id
            WHERE c.condition_start_date BETWEEN st.s AND st.e AND {cond}
            GROUP BY 1""").df().set_index("patient_key").d

    idx = pd.to_datetime(r.set_index("patient_key").index_date)
    keys = idx.index
    dd = pd.to_datetime(death.reindex(keys))
    death_before_index = dd.notna() & (dd < idx)
    dd = dd.where(~death_before_index)
    pid = r.set_index("patient_key").person_id
    lastd = pd.to_datetime(pid.map(last)).reindex(keys)
    hosp = {tuple(cp[1]): pd.to_datetime(first_hosp(cp[1], mi=any(x.startswith(("I21", "I22")) for x in cp[1])).reindex(keys))
            for cp in comps if not isinstance(cp, str)}

    def build(end):
        ev_dates = [dd if cp == "death" else hosp[tuple(cp[1])] for cp in comps]
        ev = pd.concat(ev_dates, axis=1).min(axis=1)
        stop = pd.concat([ev, end, dd], axis=1).min(axis=1)
        event = ev.notna() & (ev <= end) & ~(dd < ev)
        stop = stop.where(~event, ev)
        t = (stop - idx).dt.days.astype(float)
        return t.where(t > 0, 0.5), event.astype(int)

    cap = idx + pd.Timedelta(days=follow_days)
    end_admin = pd.Series(admin_end, index=keys).clip(upper=cap)
    end_last = pd.concat([end_admin, (lastd + pd.Timedelta(days=GRACE_DAYS)).fillna(idx)], axis=1).min(axis=1)
    res = pd.DataFrame(index=keys)
    res["t_primary"], res["e_primary"] = build(end_last)
    res["t_primary_admin"], res["e_primary_admin"] = build(end_admin)
    res["exclude_phase2"] = (death_before_index | (idx >= admin_end)).astype(int).to_numpy()
    res.index.name = "patient_key"
    res.reset_index().to_parquet(d / "restricted_outcomes.parquet")
    H = horizon_days
    ok = res.exclude_phase2 == 0
    ev = ((res.e_primary == 1) & (res.t_primary <= H) & ok).sum()
    mark(d, dict(trial=n, components=[str(x) for x in comps], horizon_days=H, follow_days=follow_days, grace_days=GRACE_DAYS,
                 admin_end=str(admin_end.date()), events_at_horizon=AC.suppress20(ev),
                 excluded=AC.suppress20(int((~ok).sum())), censored_before_horizon_by_last_ehr_frac=round(float(
                     ((res.t_primary < np.minimum(res.t_primary_admin, H)) & ok).mean()), 3)))
    return dict(trial=n, status="built")


# ---------------------------------------------------------------- CLMBR-T (Yale code, unchanged)
def step_meds(n: str, A: dict, threads=8) -> dict:
    from build_comet_meds import build
    d = AC.trial_dir(n) / "meds"
    if d.exists():
        return dict(trial=n, status="exists")
    MG = AC.paths()["meds_gold"]
    s = build(AC.trial_dir(n) / "cohort", MG, MG / "concept.parquet", d, shards=8)
    return dict(trial=n, status=s["status"])


def step_encode(n: str, A: dict, threads=8) -> dict:
    from encode_comet_clmbr import encode
    d = AC.trial_dir(n) / "clmbr"
    if d.exists():
        return dict(trial=n, status="exists")
    model = Path(os.environ.get("CLMBR_MODEL_ROOT", str(AC.out_root() / "models" / "clmbr-t-base"))).resolve()
    s = encode(AC.trial_dir(n) / "meds", model, d, "code-only", 4096, limit=int(os.environ.get("CLMBR_LIMIT", "0")))
    return dict(trial=n, status=s["status"])


STEPS = dict(cohort=step_cohort, baseline=step_baseline, dx10=step_dx10, flags=step_flags, panel=step_panel, labs=step_labs,
             survey=step_survey, outcomes=step_outcomes, meds=step_meds, encode=step_encode)
CPU_AFTER_STAGE2 = ["baseline", "dx10", "flags", "panel", "labs", "survey", "outcomes", "meds"]


def _job(args):
    step, n, threads = args
    A = adapted()
    t0 = time.time()
    try:
        r = STEPS[step](n, A, threads)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001  structured failure; no data in the message
        r = dict(trial=n, status="failed", error=type(e).__name__, detail=str(e)[:200])
    r.update(step=step, secs=round(time.time() - t0, 1))
    print(r, flush=True)
    return r


def status() -> pd.DataFrame:
    A = adapted()
    rows = []
    for n, a in A.items():
        row = dict(trial=n, key=a["key"], stopped=a.get("stopped", ""))
        for s in STEPS:
            dd = AC.trial_dir(n) / s
            row[s] = "done" if (done(dd) or (dd / "restricted_cohort.parquet").exists() or (dd / "restricted_panel.parquet").exists()
                                or (dd / "summary.json").exists()) else ""
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=list(STEPS) + ["all-cpu", "status"])
    ap.add_argument("--trials", default="")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    os.umask(0o077)
    if a.step == "status":
        print(status().to_string(index=False))
        return
    A = adapted()
    names = [x for x in a.trials.split(",") if x] or [n for n in AC.S38 if n in A]
    steps = CPU_AFTER_STAGE2 if a.step == "all-cpu" else [a.step]
    log = []
    for s in steps:
        jobs = [(s, n, a.threads) for n in names if "stopped" not in A[n] or s == "cohort"]
        if s in ("encode",) or a.workers <= 1:
            res = [_job(j) for j in jobs]
        else:
            from multiprocessing import get_context
            with get_context("spawn").Pool(min(a.workers, len(jobs))) as p:
                res = p.map(_job, jobs, chunksize=1)
        log += res
    L = AC.private_dir(AC.out_root() / "logs")
    pd.DataFrame(log).to_csv(L / f"build_{a.step}_{time.strftime('%Y%m%d_%H%M%S')}.csv", index=False)


if __name__ == "__main__":
    main()
