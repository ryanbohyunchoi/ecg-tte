#!/usr/bin/env python
"""Phase 0: AoU environment and data probe (aggregates only). Run first, inside the Workbench, and review probe.json
before any extraction. It answers the questions the AoU port cannot answer from outside:

  env        Python and package versions, GPU, CPU, memory, free disk, Hugging Face reachability (CLMBR-T weights)
  cdr        WORKSPACE_CDR, tables present, row counts (rounded)
  dates      EHR date range by table (latest dates set the AoU EHR cutoff), visits by year
  person     persons, persons with EHR visits, sex-at-birth and gender concept distributions
  death      aou_death: participants with a primary death record, share with a cause concept, by source
  dx_vocab   condition source vocabulary (ICD-9-CM / ICD-10-CM / other) by year
  visits     visit_concept_id distribution and the 9201/9203/9202 roll-up coverage
  drug_type  drug_type_concept_id distribution
  meas       per held-out / PS lab item: LOINC codes resolved, persons with a value, unit distribution, median
  survey     per survey item: question resolved, persons answering, answer codes with counts
  arms       per trial and arm (AoU-adapted spec): resolved drug concepts, persons with an exposure in the index window
  size       rows per table for the union of candidate persons (extraction size)

Every count is suppressed at 1-20 ('<=20') and totals are rounded to 100 (aou_common.round_count). No participant-level
value, identifier or date is written. Output: $AOU_TTE_OUT/probe/probe.json (+ probe.md).

Usage: python scripts/aou/aou_probe.py [--only env,cdr,...] [--ehr-cutoff YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aou_common as AC  # noqa: E402
import aou_concepts as K  # noqa: E402

SECTIONS = ["env", "cdr", "dates", "person", "death", "dx_vocab", "visits", "drug_type", "meas", "survey", "arms", "size"]
PKGS = ["numpy", "pandas", "scipy", "scikit-learn", "lifelines", "duckdb", "pyarrow", "google-cloud-bigquery",
        "google-cloud-bigquery-storage", "db-dtypes", "torch", "femr", "meds", "transformers", "xformers", "safetensors"]
rc = AC.round_count
s20 = AC.suppress20


def env() -> dict:
    import importlib.metadata as md
    v = {}
    for p in PKGS:
        try:
            v[p] = md.version(p)
        except md.PackageNotFoundError:
            v[p] = None
    gpu = None
    if shutil.which("nvidia-smi"):
        q = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
        gpu = [x.strip() for x in q.stdout.splitlines() if x.strip()]
    hf = None
    try:
        import urllib.request
        req = urllib.request.Request("https://huggingface.co/api/models/StanfordShahLab/clmbr-t-base", method="GET")
        with urllib.request.urlopen(req, timeout=10) as r:
            hf = dict(status=r.status, gated=json.loads(r.read().decode()).get("gated"))
    except Exception as e:  # noqa: BLE001
        hf = dict(error=type(e).__name__)
    du = shutil.disk_usage(str(AC.out_root().parent if not AC.out_root().exists() else AC.out_root()))
    mem = None
    try:
        mem = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2 ** 30, 1)
    except (ValueError, OSError):
        pass
    return dict(python=platform.python_version(), packages=v, gpu=gpu, cpus=os.cpu_count(), mem_gib=mem,
                disk_free_gib=round(du.free / 2 ** 30, 1), out_root=str(AC.out_root()), huggingface_clmbr_t=hf,
                git_sha=AC.git_sha(), workspace_cdr=os.environ.get("WORKSPACE_CDR"))


def cdr(D, q) -> dict:
    T = q(f"SELECT table_id, row_count FROM `{D}.__TABLES__` ORDER BY table_id")
    return dict(tables={r.table_id: rc(r.row_count, 1000) for r in T.itertuples()})


def dates(D, q) -> dict:
    specs = [("visit_occurrence", "visit_start_date"), ("condition_occurrence", "condition_start_date"),
             ("drug_exposure", "drug_exposure_start_date"), ("procedure_occurrence", "procedure_date"),
             ("measurement", "measurement_date")]
    out = {}
    for t, c in specs:
        # 0.1% / 99.9% / max of the date distribution (no individual record), excluding implausible future dates
        r = q(f"""SELECT APPROX_QUANTILES({c}, 1000)[OFFSET(1)] p001, APPROX_QUANTILES({c}, 1000)[OFFSET(999)] p999,
                  MAX({c}) mx FROM `{D}.{t}` WHERE {c} <= CURRENT_DATE()""").iloc[0]
        out[t] = dict(p001=str(r.p001), p999=str(r.p999), max=str(r.mx))
    by = q(f"""SELECT EXTRACT(YEAR FROM visit_start_date) y, COUNT(*) n, COUNT(DISTINCT person_id) p
               FROM `{D}.visit_occurrence` GROUP BY 1 ORDER BY 1""")
    out["visits_by_year"] = {int(r.y): dict(visits=rc(r.n), persons=rc(r.p)) for r in by.itertuples() if r.y is not None}
    return out


def person(D, q) -> dict:
    n = q(f"SELECT COUNT(*) n FROM `{D}.person`").n[0]
    ehr = q(f"SELECT COUNT(DISTINCT person_id) n FROM `{D}.visit_occurrence`").n[0]
    sx = q(f"""SELECT p.sex_at_birth_concept_id cid, c.concept_name nm, COUNT(*) n FROM `{D}.person` p
               LEFT JOIN `{D}.concept` c ON c.concept_id = p.sex_at_birth_concept_id GROUP BY 1, 2 ORDER BY n DESC""")
    gd = q(f"""SELECT p.gender_concept_id cid, c.concept_name nm, COUNT(*) n FROM `{D}.person` p
               LEFT JOIN `{D}.concept` c ON c.concept_id = p.gender_concept_id GROUP BY 1, 2 ORDER BY n DESC""")
    return dict(persons=rc(n), persons_with_ehr_visit=rc(ehr),
                sex_at_birth=[dict(concept_id=int(r.cid) if r.cid == r.cid else None, name=r.nm, n=rc(r.n)) for r in sx.itertuples()],
                gender=[dict(concept_id=int(r.cid) if r.cid == r.cid else None, name=r.nm, n=rc(r.n)) for r in gd.itertuples()])


def death(D, q, tables) -> dict:
    out = {}
    if "aou_death" in tables:
        r = q(f"""SELECT COUNT(DISTINCT person_id) p,
                  COUNT(DISTINCT IF(COALESCE(cause_concept_id, 0) > 0, person_id, NULL)) pc
                  FROM `{D}.aou_death` WHERE primary_death_record""").iloc[0]
        src = q(f"SELECT src_id s, COUNT(DISTINCT person_id) p FROM `{D}.aou_death` WHERE primary_death_record GROUP BY 1")
        out["aou_death"] = dict(persons=rc(r.p), persons_with_cause_concept=rc(r.pc), by_src={str(x.s): rc(x.p) for x in src.itertuples()},
                                share_with_cause=round(float(r.pc) / max(float(r.p), 1), 3) if r.p > AC.MIN_COUNT else None)
    if "death" in tables:
        out["death"] = dict(persons=rc(q(f"SELECT COUNT(DISTINCT person_id) n FROM `{D}.death`").n[0]))
    return out


def dx_vocab(D, q) -> dict:
    r = q(f"""SELECT EXTRACT(YEAR FROM co.condition_start_date) y, COALESCE(sc.vocabulary_id, 'none') v, COUNT(*) n
              FROM `{D}.condition_occurrence` co LEFT JOIN `{D}.concept` sc ON sc.concept_id = co.condition_source_concept_id
              GROUP BY 1, 2""")
    out = {}
    for x in r.itertuples():
        if x.y is not None and 2005 <= x.y <= 2030:
            out.setdefault(int(x.y), {})[x.v] = rc(x.n)
    return dict(by_year=dict(sorted(out.items())))


def visits(D, q) -> dict:
    r = q(f"""SELECT v.visit_concept_id cid, c.concept_name nm, r.rolled, COUNT(*) n FROM `{D}.visit_occurrence` v
              LEFT JOIN `{D}.concept` c ON c.concept_id = v.visit_concept_id
              LEFT JOIN ({K.visit_rollup_sql(D)}) r ON r.visit_concept_id = v.visit_concept_id
              GROUP BY 1, 2, 3 ORDER BY n DESC LIMIT 40""")
    return dict(top=[dict(concept_id=int(x.cid), name=x.nm, rolled=int(x.rolled) if x.rolled == x.rolled else None, n=rc(x.n))
                     for x in r.itertuples()])


def drug_type(D, q) -> dict:
    r = q(f"""SELECT de.drug_type_concept_id cid, c.concept_name nm, COUNT(*) n FROM `{D}.drug_exposure` de
              LEFT JOIN `{D}.concept` c ON c.concept_id = de.drug_type_concept_id GROUP BY 1, 2 ORDER BY n DESC""")
    return dict(types=[dict(concept_id=int(x.cid), name=x.nm, n=rc(x.n)) for x in r.itertuples()])


def meas(D, q) -> dict:
    L = q(K.loinc_sql(D))
    out = {item: dict(yale_cid=cid, loinc_listed=codes, loinc_resolved=sorted(L[L.item == item].code)) for item, (cid, codes) in K.MEAS_MAP.items()}
    r = q(f"""WITH l AS ({K.loinc_sql(D)})
        SELECT l.item, me.unit_concept_id u, uc.concept_name un, COUNT(DISTINCT me.person_id) p, COUNT(*) n,
               APPROX_QUANTILES(me.value_as_number, 4)[OFFSET(2)] med
        FROM `{D}.measurement` me JOIN l ON l.concept_id = me.measurement_concept_id
        LEFT JOIN `{D}.concept` sc ON sc.concept_id = me.measurement_source_concept_id
        LEFT JOIN `{D}.concept` uc ON uc.concept_id = me.unit_concept_id
        WHERE me.value_as_number IS NOT NULL AND COALESCE(sc.vocabulary_id, '') != 'PPI'
        GROUP BY 1, 2, 3""")
    for item, g in r.groupby("item"):
        g = g.sort_values("n", ascending=False)
        out[item]["persons_any_unit"] = rc(g.p.sum())  # upper bound (a person can have several units)
        out[item]["units"] = [dict(unit_concept_id=int(x.u) if x.u == x.u else None, unit=x.un, persons=rc(x.p), rows=rc(x.n),
                                   median=round(float(x.med), 3) if x.p > AC.MIN_COUNT and x.med == x.med else None)
                              for x in g.head(6).itertuples()]
    ppi = q(f"""WITH l AS ({K.loinc_sql(D)}) SELECT l.item, COUNT(DISTINCT me.person_id) p FROM `{D}.measurement` me
               JOIN l ON l.concept_id = me.measurement_concept_id JOIN `{D}.concept` sc ON sc.concept_id = me.measurement_source_concept_id
               WHERE sc.vocabulary_id = 'PPI' GROUP BY 1""")
    for x in ppi.itertuples():
        out[x.item]["persons_program_physical_measurement_excluded"] = rc(x.p)
    return out


def survey(D, q) -> dict:
    Qs = q(K.survey_question_sql(D))
    out = {k: dict(code=c, resolved=bool((Qs.item == k).any())) for k, c in K.SURVEY_QUESTIONS.items()}
    r = q(f"""WITH s AS ({K.survey_question_sql(D)})
        SELECT s.item, ac.concept_code acode, ac.concept_name aname, COUNT(DISTINCT o.person_id) p,
               APPROX_QUANTILES(o.observation_date, 2)[OFFSET(1)] med_date
        FROM `{D}.observation` o JOIN s ON s.concept_id = o.observation_source_concept_id
        LEFT JOIN `{D}.concept` ac ON ac.concept_id = o.value_source_concept_id
        GROUP BY 1, 2, 3""")
    for item, g in r.groupby("item"):
        out[item]["persons"] = rc(g.p.sum())
        out[item]["median_answer_date_year"] = int(min(g.med_date).year) if len(g) else None
        out[item]["answers"] = [dict(code=x.acode, name=x.aname, persons=rc(x.p)) for x in g.sort_values("p", ascending=False).itertuples()]
    return out


def arms(D, q, cutoff) -> dict:
    import aou_specs as S
    from trial_specs import TRIALS  # noqa: F401
    A = S.adapt_all(cutoff)
    out = {}
    for n, a in A.items():
        if "stopped" in a:
            out[n] = dict(stopped=a["stopped"])
            continue
        sp = a["spec"]
        win = f"BETWEEN DATE '{sp['index_start']}' AND DATE '{sp['index_end']}'"
        res = dict(index_window=[sp["index_start"], sp["index_end"]], changes=a["record"]["changes"], arms={})
        procedure_arm0 = sp.get("design") in ("procedure", "proc_vs_drug") or sp.get("arm0_procedure")
        for i, (arm, kws) in enumerate(sp["arms"]):
            if sp.get("design") == "procedure" or (i == 0 and procedure_arm0):
                sql = K.procedure_rows_sql(D, kws)
                nconc = None
            else:
                sql = K.drug_rows_sql(D, kws)
                nconc = int(q(f"SELECT COUNT(*) n FROM ({K.drug_concept_sql(D, kws)})").n[0])
            p = q(f"SELECT COUNT(DISTINCT person_id) p FROM ({sql}) WHERE d {win}").p[0]
            res["arms"][arm] = dict(drug_concepts_matched=nconc, persons_in_window=rc(p))
        out[n] = res
        print(n, res["arms"], flush=True)
    return out


def size(D, q, cutoff) -> dict:
    import aou_specs as S
    A = S.adapt_all(cutoff)
    kws = sorted({k for a in A.values() if "spec" in a for i, (arm, ks) in enumerate(a["spec"]["arms"])
                  if not (a["spec"].get("design") == "procedure" or (i == 0 and (a["spec"].get("design") == "proc_vs_drug" or a["spec"].get("arm0_procedure"))))
                  for k in ks})
    cand = f"SELECT DISTINCT person_id FROM ({K.drug_rows_sql(D, kws)}) WHERE d >= DATE '{AC.ICD10_ERA_START}'"
    out = dict(candidate_persons_drug_arms=rc(q(f"SELECT COUNT(*) n FROM ({cand})").n[0]))
    for t in ("condition_occurrence", "drug_exposure", "procedure_occurrence", "visit_occurrence", "measurement", "observation"):
        out[f"rows_{t}"] = rc(q(f"SELECT COUNT(*) n FROM `{D}.{t}` WHERE person_id IN ({cand})").n[0], 100000)
    return out


def to_md(P: dict) -> str:
    L = ["# AoU probe (aggregates only; counts 1-20 suppressed, totals rounded)", "", f"Generated {P['when']}; git {P.get('env', {}).get('git_sha')}", ""]
    for k, v in P.items():
        if k == "when":
            continue
        L += [f"## {k}", "", "```json", json.dumps(v, indent=1, default=str)[:20000], "```", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default=",".join(SECTIONS))
    ap.add_argument("--ehr-cutoff", default=os.environ.get("AOU_EHR_CUTOFF", "2023-06-30"),
                    help="index_end cap for the arms/size sections (set from the dates section)")
    a = ap.parse_args()
    out = AC.private_dir(AC.paths()["probe"])
    P = json.loads((out / "probe.json").read_text()) if (out / "probe.json").exists() else {}
    want = [s for s in a.only.split(",") if s]
    if "env" in want:
        P["env"] = env()
    if set(want) - {"env"}:
        D = AC.cdr()
        client = AC.bq_client()
        q = lambda sql: AC.bq_df(sql, client)  # noqa: E731
        tables = set(q(f"SELECT table_id FROM `{D}.__TABLES__`").table_id)
        fns = dict(cdr=lambda: cdr(D, q), dates=lambda: dates(D, q), person=lambda: person(D, q), death=lambda: death(D, q, tables),
                   dx_vocab=lambda: dx_vocab(D, q), visits=lambda: visits(D, q), drug_type=lambda: drug_type(D, q),
                   meas=lambda: meas(D, q), survey=lambda: survey(D, q), arms=lambda: arms(D, q, a.ehr_cutoff),
                   size=lambda: size(D, q, a.ehr_cutoff))
        for s in want:
            if s == "env":
                continue
            t0 = time.time()
            try:
                P[s] = fns[s]()
            except Exception as e:  # noqa: BLE001  (structured, no data in the message)
                P[s] = dict(error=type(e).__name__, detail=str(e)[:300])
            print(f"{s}: {time.time() - t0:.0f}s", flush=True)
            AC.write_json(out / "probe.json", dict(P, when=time.strftime("%Y-%m-%d %H:%M")))
    P["when"] = time.strftime("%Y-%m-%d %H:%M")
    AC.write_json(out / "probe.json", P)
    (out / "probe.md").write_text(to_md(P))
    print("wrote", out / "probe.json")


if __name__ == "__main__":
    main()
