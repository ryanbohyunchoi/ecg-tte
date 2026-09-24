"""Held-out physiology evaluation panel (never enters any PS).

For a roster (patient_key, person_id, index_date): the latest value in
[index-365, index-1] of
  labs (OMOP gold measurement concepts): NT-proBNP, hs-troponin T, eGFR, albumin, BUN,
      glucose, HbA1c, WBC, platelets, LDL
  echo report measurements (PanEcho study-level labels, /mnt/raid0/gih5/echo_data, linked
      to EchoDate via accession number): wall thickness, LV/LA/RV size and function,
      diastolic indices, valve grades, pulmonary pressures. Available for a curated
      2015-2022 subset only (1-5% of each cohort).
Values are left missing when unmeasured; the evaluator scores balance on measured values
only and reports how many were measured. Aggregate summary only is printed.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import connect, mrn_key, new_private_dir, rp  # noqa: E402

LABS = {"ntprobnp": 3029187, "hs_troponin_t": 40769783, "egfr": 40764999, "albumin": 3024561, "bun": 3013682,
        "glucose": 3004501, "hba1c": 3004410, "wbc": 3000905, "platelets": 3024929, "ldl": 3028288}
ECHO = {"IVSd": "ivsd", "LVPWd": "lvpwd", "LVIDd": "lvidd", "LVIDs": "lvids", "LVEDV": "lvedv", "LVESV": "lvesv",
        "LAVol": "la_vol", "LAIDs2D": "la_dim", "E|EAvg": "e_e_prime", "RVSP": "rvsp", "TAPSE": "tapse",
        "RVIDd": "rvidd", "AORoot": "ao_root", "AVPkVel(m|s)": "av_peak_vel", "TVPkGrad": "tv_peak_grad",
        "LVWallThickness-increased-any": "lv_wall_thick_incr", "LVDiastolicFunction": "lv_diastolic_fn",
        "LVSystolicFunction": "lv_systolic_fn", "RVSystolicFunction": "rv_systolic_fn", "LASize": "la_size",
        "RVSize": "rv_size", "AVStenosis": "av_stenosis", "AVRegurg": "av_regurg",
        "MVRegurgitation": "mv_regurg", "TVRegurgitation": "tv_regurg", "LVWallMotionAbnormalities": "lv_wma"}
PANECHO = "/mnt/raid0/gih5/echo_data"
ACC = "/mnt/raid0/rbc58/mm_vhd/metadata/echo_accession_number.parquet"

ap = argparse.ArgumentParser()
ap.add_argument("--roster", required=True)
ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
ap.add_argument("--output-dir", required=True)
a = ap.parse_args()
out = new_private_dir(a.output_dir)
con = connect(48)
r = pd.read_parquet(a.roster)[["patient_key", "person_id", "index_date"]]
con.register("r0", r)
con.execute("CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, CAST(index_date AS DATE) idx FROM r0")
con.register("labs", pd.DataFrame(list(LABS.items()), columns=["name", "cid"]))
lab = con.execute(f"""SELECT r.patient_key, l.name, arg_max(m.value_as_number, m.measurement_datetime) v
    FROM r JOIN {rp(a.omop_dir, 'measurement')} m USING (person_id) JOIN labs l ON m.measurement_concept_id = l.cid
    WHERE m.value_as_number IS NOT NULL AND m.measurement_date BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY
    GROUP BY 1, 2""").df().pivot(index="patient_key", columns="name", values="v").add_prefix("lab_")
files = ",".join(f"'{PANECHO}/041824_{s}_labels.csv'" for s in ("train", "val", "test"))
sel = ", ".join(f'avg(try_cast("{k}" AS DOUBLE)) AS "{v}"' for k, v in ECHO.items())
con.execute(f"""CREATE TEMP TABLE st AS SELECT e.k, e.d, s.* EXCLUDE (acc_num) FROM
    (SELECT acc_num, {sel} FROM read_csv([{files}], union_by_name=true, all_varchar=true, header=true) GROUP BY acc_num) s
    JOIN (SELECT AccessionNumber, {mrn_key('MRN')} k, try_cast(EchoDate AS DATE) d FROM read_parquet('{ACC}')) e
    ON e.AccessionNumber = s.acc_num""")
cols = ", ".join(f'arg_max(st."{v}", st.d) AS "echo_{v}"' for v in ECHO.values())
echo = con.execute(f"""SELECT r.patient_key, {cols} FROM r
    JOIN (SELECT person_id, {mrn_key('person_source_value')} k FROM {rp(a.omop_dir, 'person')}) p USING (person_id)
    JOIN st ON st.k = p.k WHERE st.d BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY
    GROUP BY 1""").df().set_index("patient_key")
panel = pd.concat([lab, echo], axis=1).reindex(r.patient_key)
panel.index.name = "patient_key"
panel.reset_index().to_parquet(out / "restricted_physiology_panel.parquet")
summ = dict(n=int(len(panel)), measured_frac={c: round(float(panel[c].notna().mean()), 4) for c in panel.columns})
json.dump(summ, open(out / "summary.json", "w"), indent=2)
print(json.dumps(dict(n=summ["n"], labs={k: v for k, v in summ["measured_frac"].items() if k.startswith("lab_")},
                      echo_any=round(float(echo.notna().any(axis=1).reindex(r.patient_key).fillna(False).mean()), 4))))
