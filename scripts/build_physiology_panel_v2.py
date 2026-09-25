"""Held-out physiology evaluation panel v2 (never enters any PS).

Source for echo: the full structured echo report
/mnt/raid0/bb2238/metadata/echo_metadata_2026_06_12.parquet (~797K studies, 2015-07..2026-06),
latest study in [index-365, index-1] per patient. Only structured measurement/grade columns
are read; free-text (Findings, Conclusions, Indications, comments) and clinician fields are
never loaded. Labs from OMOP gold measurement, latest in the same window.

Columns are named <DOMAIN>__<variable>; the evaluator summarises balance per domain:
  LVSTRUCT  IVSd (cleaned), LVPWd, LVIDd, LVEDV/LVESV indexed, wall-thickness grade, IVSd > 15 mm
  LVFUNC    EF, LV stroke volume index, GLS, LV systolic-function grade
  DIAST     E/A, E/e' avg, e' medial/lateral, LA volume index, LA size grade, diastolic grade, LVDD flag
  RVPULM    TAPSE, RV S', RVSP, RVIDd, RAP, RV size grade, RV systolic grade
  VALVE     AV peak velocity/mean gradient, TV peak gradient, AS/AR/MR/TR grades, mod/sev AS/AR/MR/MS flags
  AORTA     aortic root
  ACCESS    echo performed in the window (binary; not missing when absent)
  BNP       NT-proBNP
  LAB       hs-TnT, eGFR, albumin, BUN, glucose, HbA1c, WBC, platelets, LDL
Ordinal grades: none 0, trace/minimal 0.5, mild 1, mild-mod 1.5, moderate 2, mod-sev 2.5, severe 3
(non-graded descriptors such as "asymmetric" or "indeterminate" -> missing).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_common import connect, mrn_key, new_private_dir, rp  # noqa: E402

ECHO = "/mnt/raid0/bb2238/metadata/echo_metadata_2026_06_12.parquet"
NUM = {"LVSTRUCT": {"cleanedIVSd": "ivsd", "LVPWd": "lvpwd", "LVIDd": "lvidd", "LVEDVIndexed": "lvedvi",
                    "LVESVIndexed": "lvesvi"},
       "LVFUNC": {"EF": "ef", "LVSVIndexed": "lvsvi", "GLS%": "gls"},
       "DIAST": {"E/A": "e_a", "E/E'Avg": "e_eprime", "E'Medial": "eprime_med", "E'Lateral": "eprime_lat",
                 "LAVolIndexed": "lavi"},
       "RVPULM": {"TAPSE": "tapse", "RVS'Vel": "rv_s", "RVSP(mmHg)": "rvsp", "RVIDd": "rvidd", "RAP(mmHg)": "rap"},
       "VALVE": {"AVPkVel(m/s)": "av_vmax", "AVMnGrad(mmHg)": "av_mean_grad", "TVPkGrad": "tv_peak_grad"},
       "AORTA": {"AORoot": "ao_root"}}
GRADE = {"LVSTRUCT": {"LVWallThickness": "wall_thickness_grade"},
         "LVFUNC": {"LVSystolicFunction": "lv_sys_grade"},
         "DIAST": {"cleanedLVDiastolicFunction": "diastolic_grade", "LASize": "la_size_grade"},
         "RVPULM": {"RVSize": "rv_size_grade", "RVSystolicFunction": "rv_sys_grade"},
         "VALVE": {"AVStenosis": "as_grade", "AVRegurg": "ar_grade", "MVRegurgitation": "mr_grade",
                   "TVRegurgitation": "tr_grade"}}
FLAG = {"LVSTRUCT": {"IVSdAbove15": "ivsd_gt15"}, "DIAST": {"LVDD": "lvdd"},
        "VALVE": {"ModerateOrSevereAS": "modsev_as", "ModerateOrSevereAR": "modsev_ar",
                  "ModerateOrSevereMR": "modsev_mr", "ModerateOrSevereMS": "modsev_ms"}}
LIMITS = {"LVSTRUCT__ivsd": (0.4, 3.0), "LVSTRUCT__lvpwd": (0.4, 3.0), "LVSTRUCT__lvidd": (2.0, 9.0),
          "LVSTRUCT__lvedvi": (10, 300), "LVSTRUCT__lvesvi": (3, 250), "LVFUNC__ef": (5, 90), "LVFUNC__lvsvi": (5, 150),
          "LVFUNC__gls": (3, 40), "DIAST__e_a": (0.2, 6), "DIAST__e_eprime": (2, 50), "DIAST__eprime_med": (1, 30),
          "DIAST__eprime_lat": (1, 30), "DIAST__lavi": (5, 200), "RVPULM__tapse": (0.5, 4.5), "RVPULM__rv_s": (2, 30),
          "RVPULM__rvsp": (10, 130), "RVPULM__rvidd": (1.5, 7.0), "RVPULM__rap": (0, 25), "VALVE__av_vmax": (0.5, 7),
          "VALVE__av_mean_grad": (1, 120), "VALVE__tv_peak_grad": (2, 150), "AORTA__ao_root": (1.5, 6.0)}  # v1.1
LEVEL = {"none": 0, "trivial": 0.5, "normal": 0, "preserved": 0, "visually normal": 0, "trace": 0.5, "minimal": 0.5,
         "low normal": 0.5, "mild": 1, "mildly increased": 1, "mildly decreased": 1, "mildly dilated": 1,
         "mild-mod": 1.5, "decreased": 1.5, "increased": 1.5, "dilated": 1.5, "visually dilated": 1.5,
         "moderate": 2, "moderately increased": 2, "moderately decreased": 2, "moderately dilated": 2,
         "mod increased": 2, "mod-sev": 2.5, "severe": 3, "severely increased": 3, "severely decreased": 3,
         "severely dilated": 3, "sev increased": 3, "hyperdynamic": -0.5}
LABS = {"BNP__ntprobnp": 3029187, "LAB__hs_troponin_t": 40769783, "LAB__egfr": 40764999, "LAB__albumin": 3024561,
        "LAB__bun": 3013682, "LAB__glucose": 3004501, "LAB__hba1c": 3004410, "LAB__wbc": 3000905,
        "LAB__platelets": 3024929, "LAB__ldl": 3028288}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--roster", required=True)
    ap.add_argument("--omop-dir", default="/mnt/raid0/rbc58/omop/gold")
    ap.add_argument("--output-dir", required=True)
    a = ap.parse_args()
    out = new_private_dir(a.output_dir)
    con = connect(48)
    r = pd.read_parquet(a.roster)[["patient_key", "person_id", "index_date"]]
    con.register("r0", r)
    con.execute("CREATE TEMP TABLE r AS SELECT patient_key, CAST(person_id AS BIGINT) person_id, "
                "CAST(index_date AS DATE) idx FROM r0")
    con.register("labs", pd.DataFrame(list(LABS.items()), columns=["name", "cid"]))
    lab = con.execute(f"""SELECT r.patient_key, l.name, arg_max(m.value_as_number, m.measurement_datetime) v
        FROM r JOIN {rp(a.omop_dir, 'measurement')} m USING (person_id) JOIN labs l ON m.measurement_concept_id = l.cid
        WHERE m.value_as_number IS NOT NULL AND m.measurement_date BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY
        GROUP BY 1, 2""").df().pivot(index="patient_key", columns="name", values="v")

    src = {c: f"{d}__{v}" for part in (NUM, GRADE, FLAG) for d, m in part.items() for c, v in m.items()}
    sel = ", ".join(f'e."{c}" AS "{v}"' for c, v in src.items())
    ech = con.execute(f"""WITH e AS (SELECT {mrn_key('MRN')} k, try_cast(EchoDate AS DATE) d, CAST(AccessionNumber AS VARCHAR) acc, {', '.join(f'"{c}"' for c in src)}
                                     FROM read_parquet('{ECHO}'))
        SELECT r.patient_key, e.d, e.acc, {sel} FROM r
        JOIN (SELECT person_id, {mrn_key('person_source_value')} k FROM {rp(a.omop_dir, 'person')}) p USING (person_id)
        JOIN e ON e.k = p.k WHERE e.d BETWEEN r.idx - INTERVAL 365 DAY AND r.idx - INTERVAL 1 DAY""").df()
    ech = ech.sort_values(["patient_key", "d", "acc"]).groupby("patient_key").tail(1).set_index("patient_key").drop(columns=["d", "acc"])
    for d, m in GRADE.items():
        for v in m.values():
            col = f"{d}__{v}"
            raw = ech[col]
            lev = dict(LEVEL, decreased=np.nan) if v == "wall_thickness_grade" else LEVEL  # v1.1: 'decreased' wall is not a grade
            ech[col] = raw.where(raw.notna()).map(lambda x, lev=lev: lev.get(str(x).strip().lower()) if pd.notna(x) else np.nan)
    for d, m in FLAG.items():
        for v in m.values():
            col = f"{d}__{v}"
            ech[col] = ech[col].map({True: 1.0, False: 0.0, "true": 1.0, "false": 0.0})
    for d, m in NUM.items():
        for v in m.values():
            ech[f"{d}__{v}"] = pd.to_numeric(ech[f"{d}__{v}"], errors="coerce")
    ech["LVFUNC__gls"] = ech["LVFUNC__gls"].abs()  # v1.1: reported with mixed sign; use magnitude
    for c, (lo, hi) in LIMITS.items():
        ech[c] = ech[c].where(ech[c].between(lo, hi))
    panel = pd.concat([lab, ech], axis=1).reindex(r.patient_key)
    panel["ACCESS__echo_done"] = panel.index.isin(ech.index).astype(float)
    panel.index.name = "patient_key"
    panel = panel.astype(float)
    panel.reset_index().to_parquet(out / "restricted_physiology_panel.parquet")
    summ = dict(n=int(len(panel)), echo_source=ECHO, echo_done_frac=round(float(panel.ACCESS__echo_done.mean()), 4),
                measured_frac={c: round(float(panel[c].notna().mean()), 4) for c in panel.columns})
    json.dump(summ, open(out / "summary.json", "w"), indent=2)
    print(json.dumps({k: summ[k] for k in ("n", "echo_done_frac")}))


if __name__ == "__main__":
    main()
