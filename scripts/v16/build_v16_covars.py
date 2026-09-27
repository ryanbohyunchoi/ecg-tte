#!/usr/bin/env python
"""v1.6 extra covariates (docs/V16_SWEEP_PLAN.md axis S1 + held-out balance candidates).

For each of the 18 trials (make_acc_figure.trials) writes
  /mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars/<trial>.parquet
keyed by patient_key (every row of the trial's cohort roster restricted_cohort.parquet, a superset of
v13_common.Trial keys), plus aggregate summary files and docs/v16/COVARIATES.md.

Conventions (match build_core_baseline.py): windows use the cohort index_date; diagnoses are any ICD-10
prefix match with a date in [index-365, index-1]; medication orders are drug_exposure token matches;
utilisation from visit_occurrence. The index day is excluded everywhere. Diagnosis codes are searched in
OMOP gold condition_occurrence AND observation (OMOP routed many Z/R/W codes, e.g. Z68 BMI codes and fall
W-codes, to observation); build_core_baseline used condition_occurrence only, which holds every E/I/F code.
Race/ethnicity come from the Yale Epic patient table (PATIENT_RACE_ALL / PATIENT_ETHNICITY) because
OMOP gold folds 'Not Listed' race into Unknown and unknown ethnicity into 'Not Hispanic'.

Restricted outputs stay under the private output dir (umask 077); stdout and markdown are aggregates
with counts 1-10 (and complements 1-10) suppressed.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from trial_common import code_like, connect, create_drug_tokens, mrn_key, rp, sha256  # noqa: E402
from trial_specs import STATIN  # noqa: E402
from v13_common import A, EXTRA, PRIMARY, paths  # noqa: E402

GOLD = "/mnt/raid0/rbc58/omop/gold"
PATIENTS = "/mnt/raid0/rbc58/ecg-tte/shared/clinical-sources-v1-t9ZGomLT/snapshot/Data_2025_04_03_patients"
OUT = A / "claude-v16-covars"
DOC = HERE.parent.parent / "docs" / "v16" / "COVARIATES.md"
STATIN_ALL = sorted(set(STATIN) | {"pravachol", "mevacor", "lescol", "livalo", "zypitamag", "vytorin", "caduet", "altoprev"})

# name: ICD-10 prefixes (dots removed), searched in condition_occurrence + observation, [index-365, index-1]
DX = {
    "hyperlipidemia": ["E780", "E781", "E782", "E783", "E784", "E785"],
    "t2d": ["E11"],
    "tobacco_current": ["F17", "Z720"],
    "tobacco_ever": ["F17", "Z720", "Z87891"],
    "obesity": ["E660", "E661", "E662", "E668", "E669", "Z683", "Z684"],
}
# frailty proxy: count of distinct indicator domains (dx-only adaptation of the Kim/Segal claims-based
# frailty indicator domains; DME HCPCS codes are too sparse in gold to use)
FRAILTY = {
    "dementia": ["F01", "F02", "F03", "G30", "G31"],
    "delirium_cognitive": ["F05", "R41"],
    "falls": [f"W{i:02d}" for i in range(20)] + ["R296", "Z9181"],
    "gait_mobility": ["R26"],
    "weakness_debility": ["R53", "M6281"],
    "malnutrition_weight_loss": ["E40", "E41", "E42", "E43", "E44", "E45", "E46", "R634", "R636", "R64"],
    "pressure_ulcer": ["L89"],
    "incontinence": ["R32", "N394", "R15"],
    "care_dependence": ["Z74", "Z993"],
    "parkinsonism": ["G20", "G21"],
    "depression": ["F32", "F33"],
    "sensory_impairment": ["H54", "H90", "H91"],
    "osteoporosis_hip_fracture": ["M80", "M81", "S72"],
}
FROM_V11 = {"cad_ihd": "ischemic_heart_disease_or_mi", "hypertension_v11": "hypertension",
            "diabetes_v11": "diabetes", "hospital_admissions_v11": "hospital_admissions"}
ASIAN = ("asian", "chinese", "filipino", "japanese", "korean", "vietnamese")
HISP = {"hispanic or latina/o/x", "puerto rican", "mexican, mexican american, chicano/a", "cuban"}
BIN_REPORT = ["race_white", "race_black", "race_asian", "race_other_unknown", "race_unknown", "race_multiple",
              "hispanic", "ethnicity_unknown", "hyperlipidemia", "statin_order_90d", "statin_order_365d", "hld_or_statin",
              "t2d", "diabetes_v11", "cad_ihd", "hypertension_v11", "tobacco_current", "tobacco_ever", "obesity",
              "frailty_any", "frailty_ge2", "prior_hf_hosp_365", "prior_hf_hosp_365_v14"]
NUM_REPORT = ["frailty_count", "inpatient_days_365", "hospital_admissions_v11"]


HEADER = """
# v1.6 extra covariates (race, hyperlipidemia, T2D, CAD, held-out balance candidates)

Built by `scripts/v16/build_v16_covars.py` (exploratory, for `docs/V16_SWEEP_PLAN.md` axis S1 and extra
held-out balance variables). Restricted per-trial files:
`/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-covars/<trial>.parquet`, keyed by `patient_key`, one row per
row of the trial's cohort roster (`restricted_cohort.parquet`, a superset of `v13_common.Trial.keys`),
with `treated` included. All values are measured strictly before the cohort `index_date`.

## Conventions
- **Windows match `build_core_baseline.py`:** diagnoses = any ICD-10 prefix (dots removed) dated in
  [index−365, index−1]; medication orders = `drug_exposure` token match (same tokeniser,
  `trial_common.create_drug_tokens`); index day excluded.
- **Code source:** OMOP gold `condition_occurrence` **plus** `observation` (OMOP routed many Z/R/W codes,
  e.g. Z68 BMI codes and W00–W19 fall codes, to `observation`). The v1.1 baseline used
  `condition_occurrence` only; all E/I/F codes live there, so for E78/E11/F17 the two agree. All gold
  source values are ICD-10-CM (no ICD-9); SNOMED `condition_concept_id` was not used.
- **Race / ethnicity:** Yale Epic patient table (`clinical-sources-v1` snapshot `Data_2025_04_03_patients`,
  `PATIENT_RACE_ALL`, `PATIENT_ETHNICITY`), linked roster `person_id` → gold `person.person_source_value`
  (MRN) → `PAT_MRN_ID` (digits, leading zeros stripped). Chosen over OMOP `person` because OMOP folds
  "Not Listed" race into Unknown and **maps unknown ethnicity to "Not Hispanic"** (no unknown category).
  Time-invariant (current registration value).

## Definitions
| Column | Definition |
|---|---|
| `race_white` | only listed race is White (after dropping "Unknown"/"Not Listed") |
| `race_black` | any listed race Black or African American (incl. multiracial) |
| `race_asian` | any listed race Asian, Asian Indian, Chinese, Filipino, Japanese, Korean, Vietnamese; not Black |
| `race_other_unknown` | none of the above: AIAN, NHPI, Middle Eastern/North African, other multiracial, Unknown, Not Listed, unlinked |
| `race_unknown` | no informative race (Unknown / Not Listed / blank / unlinked); subset of `race_other_unknown` |
| `race_multiple` | two or more informative races listed |
| `hispanic` | ethnicity Hispanic or Latina/o/x, Puerto Rican, Mexican/Mexican American/Chicano/a, Cuban (unknown → 0) |
| `ethnicity_unknown` | ethnicity Unknown / blank / unlinked |
| `hyperlipidemia` | E78.0–E78.5 (excludes E78.6 lipoprotein deficiency, E78.7 bile-acid, E78.8/E78.9 other) |
| `statin_order_90d` / `statin_order_365d` | statin order in [index−90 / −365, index−1]; tokens = `trial_specs.STATIN` + pravachol, mevacor, lescol, livalo, zypitamag, vytorin, caduet, altoprev. Several trials already carry `statin_order` (90 d) in their v1.1 baseline/PS |
| `hld_or_statin` | `hyperlipidemia` OR `statin_order_365d` (sensitivity; statin is treatment-adjacent, not a pure confounder) |
| `t2d` | E11 (type 2 only; existing v1.1 `diabetes` = E08–E11, E13) |
| `diabetes_v11`, `hypertension_v11`, `hospital_admissions_v11` | copied from `claude-<trial>-baseline-v11/restricted_baseline_observed.parquet` |
| `cad_ihd` | copy of v1.1 `ischemic_heart_disease_or_mi` (I20–I25, 365 d): covers stable angina, ACS, chronic IHD, old MI → sufficient as CAD |
| `tobacco_current` | F17 (nicotine dependence) or Z72.0 (Z72.0 has zero rows in gold) |
| `tobacco_ever` | `tobacco_current` or Z87.891 (history of nicotine dependence) |
| `obesity` | E66.0/.1/.2/.8/.9 (E66.3 overweight excluded) or Z68.3x/Z68.4x (BMI ≥ 30) |
| `frailty_count` | number of 13 frailty-indicator domains with ≥1 code (dx-only adaptation of the Kim/Segal claims frailty indicator domains; DME HCPCS too sparse in gold): dementia (F01–F03, G30, G31); delirium/cognitive (F05, R41); falls (W00–W19, R29.6, Z91.81); gait/mobility (R26); weakness/debility (R53, M62.81); malnutrition/weight loss (E40–E46, R63.4, R63.6, R64); pressure ulcer (L89); incontinence (R32, N39.4, R15); care dependence (Z74, Z99.3); parkinsonism (G20, G21); depression (F32, F33); sensory impairment (H54, H90, H91); osteoporosis/hip fracture (M80, M81, S72). Not a validated index |
| `frailty_any`, `frailty_ge2` | `frailty_count` ≥ 1 / ≥ 2 |
| `inpatient_days_365` | inpatient (9201) days in stays starting in [index−365, index−1], truncated at index−1 (v14 stay-merge rules) |
| `prior_hf_hosp_365` | inpatient stay starting ≥ index−365 and **ending ≤ index−1** with an I50 code dated within the stay |
| `prior_hf_hosp_365_v14` | copy of `claude-<trial>-hf-v14` flag: stay starting in [index−365, **index**] with I50 → can include the index stay (not strictly pre-index; kept for reference) |

## Not built / gaps
- **Area deprivation (ADI):** no ADI/SVI/ZCTA table exists on raid0 (searched file names to depth 6), and
  OMOP gold has no `location` table. The Epic patient table has a current ZIP, so ADI is feasible if a
  ZIP/ZCTA-level ADI file is provided (current address, not address at index).
- **Smoking status from social history / observation values:** not in gold; only dx codes are available.
- **Prior hospitalisations:** already exists (`hospital_admissions`, 9201 visit count in 365 d) but it is in
  the v1.1 core set and so in clinical/sparse PS designs; `inpatient_days_365` is offered as a
  held-out utilisation variable instead.
- Held-out status: none of the new columns are in any existing PS except the v11 copies and
  `statin_order_*` (equal or close to `statin_order` in trials that use it).
"""


def trial_list():
    sys.path.insert(0, str(HERE.parent))
    from make_acc_figure import trials
    return list(trials)


def analysis_keys(n):
    """Keys of v13_common.Trial(n) (intersection of baseline, ECG, CLMBR, phenotypes, panel) read cheaply."""
    P = paths(n)
    ks = pd.read_parquet(f"{A}/claude-{n}-baseline-v11/restricted_completed_01.parquet", columns=["patient_key"]).patient_key
    common = pd.Index(ks)
    ehr = (f"{A}/comet-clmbr-full-NAyb4G2x/report/restricted_embeddings_part-*.parquet" if n == "comet"
           else f"{A}/claude-{n}-clmbr-codeonly/report/restricted_embeddings_part-*.parquet")
    for pat in (P["ecg"], ehr, P["ph"], P["panel"]):
        k = pd.concat([pd.read_parquet(f, columns=["patient_key"]) for f in sorted(glob.glob(pat))]).patient_key
        common = common.intersection(pd.Index(k))
    return common


def race_map(s: pd.Series) -> pd.DataFrame:
    toks = s.fillna("").str.lower().str.split(";").apply(lambda xs: {x.strip() for x in xs} - {"", "unknown", "not listed"})
    black = toks.apply(lambda t: any("black" in x for x in t))
    asian = toks.apply(lambda t: any(x.startswith(ASIAN) for x in t)) & ~black
    white = toks.apply(lambda t: t == {"white"})
    return pd.DataFrame({"race_white": white, "race_black": black, "race_asian": asian,
                         "race_other_unknown": ~(white | black | asian), "race_unknown": toks.apply(len) == 0,
                         "race_multiple": toks.apply(len) > 1}).astype(float)


def build_all(con, rosters: pd.DataFrame) -> pd.DataFrame:
    con.register("r0", rosters[["trial", "patient_key", "person_id", "index_date"]])
    con.execute("""CREATE TEMP TABLE r AS SELECT trial, patient_key, CAST(person_id AS BIGINT) person_id,
                   CAST(index_date AS DATE) idx FROM r0""")
    con.execute("CREATE TEMP TABLE pp AS SELECT DISTINCT person_id FROM r")
    base = rosters[["trial", "patient_key"]].copy()
    K = ["trial", "patient_key"]

    # race / ethnicity (Yale Epic patient table, linked by normalised MRN = person.person_source_value)
    pat = f"read_parquet('{PATIENTS}/*.parquet')"
    demo = con.execute(f"""SELECT r.trial, r.patient_key, q.PATIENT_RACE_ALL race, q.PATIENT_ETHNICITY eth,
            p.race_concept_id omop_race, (q.k IS NOT NULL) linked
        FROM r LEFT JOIN (SELECT person_id, race_concept_id, {mrn_key('person_source_value')} k FROM {rp(GOLD, 'person')}) p
             USING (person_id)
        LEFT JOIN (SELECT {mrn_key('PAT_MRN_ID')} k, PATIENT_RACE_ALL, PATIENT_ETHNICITY FROM {pat}) q ON q.k = p.k""").df()
    demo = demo.drop_duplicates(K)
    rm = race_map(demo.race)
    eth = demo.eth.fillna("").str.strip().str.lower()
    rm["hispanic"] = eth.isin(HISP).astype(float)
    rm["ethnicity_unknown"] = (~eth.isin(HISP | {"not hispanic or latina/o/x"})).astype(float)
    omop = demo.omop_race.map({8527: "white", 8516: "black", 8515: "asian", 38003574: "asian", 38003581: "asian",
                               38003592: "asian", 38003585: "asian", 38003584: "asian"}).fillna("other")
    ours = np.select([rm.race_white == 1, rm.race_black == 1, rm.race_asian == 1], ["white", "black", "asian"], "other")
    agree = dict(linked_frac=round(float(demo.linked.mean()), 4), race_agreement_with_omop=round(float((omop.values == ours).mean()), 4))
    base = base.merge(pd.concat([demo[K].reset_index(drop=True), rm.reset_index(drop=True)], axis=1), on=K, how="left")

    # diagnoses: condition_occurrence + observation, prefix match, [idx-365, idx-1]
    allp = sorted({p for v in DX.values() for p in v} | {p for v in FRAILTY.values() for p in v})
    con.execute(f"""CREATE TEMP TABLE codes AS
        SELECT person_id, d, code FROM (
            SELECT person_id, condition_start_date d, upper(replace(condition_source_value, '.', '')) code
              FROM {rp(GOLD, 'condition_occurrence')} WHERE person_id IN (SELECT person_id FROM pp)
            UNION ALL
            SELECT person_id, observation_date d, upper(replace(observation_source_value, '.', '')) code
              FROM {rp(GOLD, 'observation')} WHERE person_id IN (SELECT person_id FROM pp))
        WHERE {code_like('code', allp)}""")
    con.execute("""CREATE TEMP TABLE cw AS SELECT DISTINCT r.trial, r.patient_key, c.code FROM r JOIN codes c USING (person_id)
                   WHERE c.d BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY""")
    flag = lambda pre: set(map(tuple, con.execute(f"SELECT DISTINCT trial, patient_key FROM cw WHERE {code_like('code', pre)}").df().values))
    kt = list(map(tuple, base[K].values))
    for name, pre in DX.items():
        s = flag(pre)
        base[name] = [float(k in s) for k in kt]
    fr = np.zeros(len(base))
    for name, pre in FRAILTY.items():
        s = flag(pre)
        fr += np.array([k in s for k in kt], float)
    base["frailty_count"] = fr
    base["frailty_any"] = (fr >= 1).astype(float)
    base["frailty_ge2"] = (fr >= 2).astype(float)

    # statin orders (same token rule as build_core_baseline medications)
    create_drug_tokens(con, GOLD, STATIN_ALL, table="stok", person_filter="pp")
    for days in (90, 365):
        s = set(map(tuple, con.execute(f"""SELECT DISTINCT r.trial, r.patient_key FROM r JOIN stok b USING (person_id)
            WHERE b.d BETWEEN r.idx - INTERVAL {days} DAY AND r.idx - INTERVAL 1 DAY""").df().values))
        base[f"statin_order_{days}d"] = [float(k in s) for k in kt]
    base["hld_or_statin"] = ((base.hyperlipidemia == 1) | (base.statin_order_365d == 1)).astype(float)

    # inpatient stays (v14_extract stay rules: 9201 visits merged when overlapping / within 1 day)
    con.execute(f"""CREATE TEMP TABLE iv AS SELECT person_id, visit_start_date s, coalesce(visit_end_date, visit_start_date) e
        FROM {rp(GOLD, 'visit_occurrence')} WHERE visit_concept_id = 9201 AND person_id IN (SELECT person_id FROM pp)""")
    con.execute("""CREATE TEMP TABLE stays AS
        WITH o AS (SELECT *, max(e) OVER (PARTITION BY person_id ORDER BY s, e ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) pe FROM iv),
             g AS (SELECT *, sum(CASE WHEN pe IS NULL OR s > pe + INTERVAL 1 DAY THEN 1 ELSE 0 END)
                            OVER (PARTITION BY person_id ORDER BY s, e ROWS UNBOUNDED PRECEDING) gid FROM o)
        SELECT person_id, gid, min(s) s, max(e) e FROM g GROUP BY 1, 2""")
    days = con.execute("""SELECT r.trial, r.patient_key,
            sum(date_diff('day', st.s, least(st.e, r.idx - INTERVAL 1 DAY)) + 1) n
        FROM r JOIN stays st USING (person_id)
        WHERE st.s BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY GROUP BY 1, 2""").df()
    base = base.merge(days.rename(columns={"n": "inpatient_days_365"}), on=K, how="left")
    base["inpatient_days_365"] = base.inpatient_days_365.fillna(0).astype(float)
    # prior HF hospitalisation, strictly pre-index: stay starting in [idx-365, idx-1] and ending before idx,
    # with an I50 code dated within the stay
    con.execute(f"""CREATE TEMP TABLE i50 AS SELECT DISTINCT person_id, condition_start_date d FROM {rp(GOLD, 'condition_occurrence')}
        WHERE person_id IN (SELECT person_id FROM pp)
          AND {code_like("upper(replace(condition_source_value, '.', ''))", ["I50"])}""")
    s = set(map(tuple, con.execute("""SELECT DISTINCT r.trial, r.patient_key FROM r
        JOIN stays st ON st.person_id = r.person_id AND st.s >= r.idx - INTERVAL 365 DAY AND st.e <= r.idx - INTERVAL 1 DAY
        JOIN i50 c ON c.person_id = r.person_id AND c.d BETWEEN st.s AND st.e""").df().values))
    base["prior_hf_hosp_365"] = [float(k in s) for k in kt]
    return base, agree


def sup(c, n):
    return "<11" if (1 <= c <= 10 or 1 <= n - c <= 10) else f"{c:,} ({100 * c / n:.1f}%)" if n else "0"


def smd(a, b):
    a, b = a.dropna(), b.dropna()
    v = (a.var() + b.var()) / 2
    return float((a.mean() - b.mean()) / np.sqrt(v)) if v > 0 else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--trials", nargs="*", help="v1.7: trial names (default: the 18 v1.6 trials)")
    ap.add_argument("--out", default=None, help="v1.7: output dir (default claude-v16-covars)")
    ap.add_argument("--blind", action="store_true", help="v1.7: no by-arm summary / SMD, no markdown (blinded new trials)")
    a = ap.parse_args()
    global OUT
    if a.out:
        OUT = Path(a.out)
    os.umask(0o077)
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    names = {**PRIMARY, **EXTRA}
    trials = a.trials or trial_list()
    ros = []
    for n in trials:
        r = pd.read_parquet(f"{A}/{names[n][1]}/restricted_cohort.parquet")[["patient_key", "person_id", "treated", "treatment_arm", "index_date"]]
        r = r.drop_duplicates("patient_key")
        r.insert(0, "trial", n)
        ros.append(r)
    ros = pd.concat(ros, ignore_index=True)
    con = connect(a.threads)
    allc, agree = build_all(con, ros)
    rows, cover = [], {}
    for n in trials:
        d = allc[allc.trial == n].drop(columns="trial").set_index("patient_key")
        r = ros[ros.trial == n].set_index("patient_key")
        d.insert(0, "treated", r.treated.reindex(d.index).astype(int))
        obs = pd.read_parquet(f"{A}/claude-{n}-baseline-v11/restricted_baseline_observed.parquet").set_index("patient_key")
        for new, old in FROM_V11.items():
            d[new] = obs[old].reindex(d.index).astype(float) if old in obs else np.nan
        hf = f"{A}/claude-{n}-hf-v14/restricted_hf_outcome.parquet"
        d["prior_hf_hosp_365_v14"] = (pd.read_parquet(hf).set_index("patient_key").prior_hf_hosp_365.reindex(d.index).astype(float)
                                      if os.path.exists(hf) else np.nan)
        d.reset_index().to_parquet(OUT / f"{n}.parquet")
        keys = analysis_keys(n)
        cover[n] = dict(roster=int(len(d)), trial_keys=int(len(keys)), trial_keys_covered=int(keys.isin(d.index).sum()),
                        v11_keys_covered=round(float(obs.index.isin(d.index).mean()), 4),
                        arms={int(t): str(a) for t, a in r.groupby("treated").treatment_arm.agg(lambda x: x.mode().iloc[0]).items()})
        if a.blind:
            continue
        g = d.loc[d.index.intersection(keys)]
        g1, g0 = g[g.treated == 1], g[g.treated == 0]
        for v in BIN_REPORT + NUM_REPORT:
            row = dict(trial=n, variable=v, n_treated=len(g1), n_control=len(g0),
                       missing_frac=round(float(g[v].isna().mean()), 4), smd=round(smd(g1[v], g0[v]), 3))
            if v in BIN_REPORT:
                row["treated"] = sup(int(g1[v].sum()), len(g1))
                row["control"] = sup(int(g0[v].sum()), len(g0))
            else:
                row["treated"] = f"{g1[v].mean():.2f} (sd {g1[v].std():.2f})"
                row["control"] = f"{g0[v].mean():.2f} (sd {g0[v].std():.2f})"
            rows.append(row)
    json.dump(dict(coverage=cover, linkage=agree, script_sha256=sha256(Path(__file__)), blind=a.blind), open(OUT / "summary.json", "w"), indent=2)
    if not a.blind:
        S = pd.DataFrame(rows)
        S.to_csv(OUT / "summary_by_arm.csv", index=False)
        write_md(S, cover, agree)
    print(json.dumps(dict(coverage=cover, linkage=agree), indent=1))


def write_md(S, cover, agree):
    L = [HEADER.strip(), "",
         f"## Linkage and coverage",
         f"- Roster rows linked to the Yale Epic patient table: {100 * agree['linked_frac']:.2f}% (unlinked rows get race/ethnicity unknown).",
         f"- Agreement of the 4-level race used here with OMOP `race_concept_id` (collapsed the same way): "
         f"{100 * agree['race_agreement_with_omop']:.1f}%.", "",
         "| Trial | treated arm | comparator arm | roster rows | Trial keys | Trial keys covered |", "|---|---|---|---|---|---|"]
    for n, c in cover.items():
        L.append(f"| {n} | {c['arms'].get(1)} | {c['arms'].get(0)} | {c['roster']:,} | {c['trial_keys']:,} | {c['trial_keys_covered']:,} |")
    L += ["", "## Prevalence by arm (analysis population = v13_common.Trial keys)",
          "Binary: count (%) of treated / comparator; `<11` = count or its complement in 1–10 (suppressed). "
          "Numeric: mean (sd). SMD = treated − comparator, pooled-SD; unadjusted. Missing = fraction NaN "
          "(only `prior_hf_hosp_365_v14`/v11 copies can be NaN).", ""]
    miss = S.groupby("variable").missing_frac.max()
    L.append("Maximum missing fraction across trials: " + ", ".join(f"`{v}` {m:.3f}" for v, m in miss.items() if m > 0) + (
        "" if (miss > 0).any() else "none") + ".")
    for n, g in S.groupby("trial", sort=False):
        L += ["", f"### {n} (treated n = {g.n_treated.iloc[0]:,}; comparator n = {g.n_control.iloc[0]:,})", "",
              "| Variable | Treated | Comparator | SMD |", "|---|---|---|---|"]
        L += [f"| {r.variable} | {r.treated} | {r.control} | {r.smd:+.3f} |" for r in g.itertuples()]
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
