#!/usr/bin/env python
"""CHS emulation cohorts (docs/bdc/CHS_PROTOCOL.md): one row per new user per emulation, with arm, PS covariates and
held-out items from visit k-1 or earlier, the visit k-1 ECG XML, and outcomes from time zero (visit k).

Restricted output (stays in BDC): $BDC_RESTRICTED/chs_emulations.{parquet|pkl}.
Aggregate output: <out>/chs_cohort/report.md (per emulation and arm: n, n with ECG, held-out coverage, pre-match |SMD|
of the held-out items, primary-outcome events; counts 1-10 suppressed). No HRs are computed here.

Usage: python scripts/bdc/chs_cohort.py
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bdc_common as BC  # noqa: E402
import cohort_count as CC  # noqa: E402  (tested dbGaP reader, use matrix, new-user rule, ECG linkage)

S = BC.suppress
MO = 30.4375
# visit table -> CHS year; BASEBOTH/YR5NEW rows belong to each person's entry visit (2 = original, 5 = new cohort)
TABLE_VISIT = {"BASE1": 2, "BASE2": 2, "YR3": 3, "YR4": 4, "YR5OLD": 5, "YR5NEW": 5, "YR6": 6, "YR7": 7, "YR8": 8, "YR9": 9,
               "YR10": 10, "YR11": 11, "CYST_C_YR5": 5}
STATIC = ["BASEBOTH", "EVENT_SUMMARY", "CARE_AFIB", "CHS_Event16", "EVENT_TIME_TO_CENSUS"]
# held-out items: name -> candidate columns (first non-missing per table); latest value at or before visit k-1
HELD = {
    "echo_lv_mass": ["NEWLVM43", "MMLVMS43"], "echo_lv_function": ["LVEF43", "LVFNCT43"], "echo_la_dim": ["MMLAD43"],
    "echo_septum": ["MMVSTD43"], "echo_post_wall": ["MMLVWD43"], "echo_e_a": ["E_A"],
    "lab_creatinine": ["CREADJ", "CRE44"], "lab_ldl": ["LDLADJ", "LDLUNADJ"], "lab_hdl": ["HDL44"], "lab_tg": ["TRIG44"],
    "lab_glucose": ["GLUADJ", "GLU44"], "lab_insulin": ["INS44"], "lab_albumin": ["ALBADJ", "ALB44"], "lab_fibrinogen": ["FIB44"],
    "lab_crp": ["CRPBLADJ"], "lab_cystatin_c": ["CYSTATC"],
    "vital_sbp": ["AVZMSYS", "AVESYS"], "vital_dbp": ["AVZMDIA", "AVEDIA"], "vital_bmi": ["BMI"],
    "func_gait_time": ["TIME27"], "func_fev1": ["FEV118"], "vasc_aai": ["AAI"],
}
DOMAIN = lambda item: item.split("_")[0]  # noqa: E731
CLINICAL_PS = ["vital_sbp", "vital_dbp", "vital_bmi", "lab_creatinine", "lab_ldl", "lab_hdl", "lab_glucose", "lab_albumin"]
# event types in CHS_Event16
EV = {"MI": 1, "STROKE": 3, "CHF": 4}
EMUS = [  # name, A, B (None = sequential vs none), age range, extra exclusion, primary outcome components, horizon (mo)
    dict(name="E1_ccb_vs_thiazide", A="CCB", B="THIAZIDE", age=(0, 200), excl=["HF"], primary=["MI", "CHD_DEATH"], H=60,
         bench="ALLHAT amlodipine vs chlorthalidone RR 0.98 (0.90-1.07)", cluster="thiazide"),
    dict(name="E1b_dhp_vs_thiazide", A="DHP_CCB", B="THIAZIDE", age=(0, 200), excl=["HF"], primary=["MI", "CHD_DEATH"], H=60,
         bench="ALLHAT (dihydropyridine only) RR 0.98", cluster="thiazide"),
    dict(name="E2_acei_vs_thiazide", A="ACEI", B="THIAZIDE", age=(0, 200), excl=["HF"], primary=["MI", "CHD_DEATH"], H=60,
         bench="ALLHAT lisinopril vs chlorthalidone RR 0.99 (0.91-1.08)", cluster="thiazide"),
    dict(name="E3_acei_vs_ccb", A="ACEI", B="CCB", age=(70, 84), excl=[], primary=["CV_DEATH"], H=60,
         bench="STOP-2 ACEi vs CCB CV death ~1.0", cluster="acei_ccb"),
    dict(name="E4_thiazide_vs_beta", A="THIAZIDE", B="BETA", age=(65, 74), excl=[], primary=["STROKE", "MI", "CHD_DEATH"],
         H=70, bench="MRC older adults (no head-to-head HR)", cluster="thiazide"),
    dict(name="E5_statin_vs_none", A="STATIN", B=None, age=(70, 82), excl=[], primary=["MI", "STROKE", "CHD_DEATH"], H=39,
         bench="PROSPER HR 0.85 (0.74-0.97)", cluster="statin"),
    dict(name="E6_aspirin_vs_none", A="ASPIRIN", B=None, age=(70, 200), excl=["CAD", "STROKE_HX", "HF", "AF"],
         primary=["MI", "STROKE", "CHF"], H=56, bench="ASPREE CVD HR 0.95 (0.83-1.08)", cluster="aspirin"),
]
SECONDARY = {"death": ["DEATH"], "hf": ["CHF"], "mi": ["MI"], "stroke": ["STROKE"]}
# medication flags never used as code features for an emulation (its exposures, and summary flags containing them)
AHT = r"(ACE|ACED|A2A|A2AD|CCB|CCBIR|CCBSR|AMLOD|NIFSR|NIFIR|DLTSR|DLTIR|VERSR|VERIR|HCTZ|HCTZK|LOOP|KSPR|BETA|BETAD|ALPHA|DIURET|HTNMED|ANYACE|ANYBETA|ANYDIUR|VASO|ACEI|CLON|RESER)\d*06"
EXPOSURE_FLAGS = {"E1_ccb_vs_thiazide": AHT, "E1b_dhp_vs_thiazide": AHT, "E2_acei_vs_thiazide": AHT, "E3_acei_vs_ccb": AHT,
                  "E4_thiazide_vs_beta": AHT, "E5_statin_vs_none": r"(STTN|LIPID|FIBR|NIAC|RESIN)\d*06",
                  "E6_aspirin_vs_none": r"(ASA|ASPIRIN|NSAID|ADPI|WARF)\d*06|ASPIRIN"}


def restricted_dir() -> Path:
    p = Path(os.environ.get("BDC_RESTRICTED", "/sbgenomics/workspace/bdc-restricted"))
    os.umask(0o077)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load(files):
    """Visit tables (long measurement table), static tables, the use matrix and the ECG file map."""
    CC.WANT.clear()
    cols = {c for v in HELD.values() for c in v} | {"DPMEP43", "DPMAP43", "STDYTIME", "PERSTAT", "AGEBL", "GEND01",
                                                    "RACE01", "BPHI", "DIABADA", "SMOKE", "INSULN06", "OHGA06", "HTNMED06"}
    cols |= {f"AGEY{k}" for k in range(3, 12)}
    cols |= {"MIBLMOD", "ANBLMOD", "CHBLMOD", "STBLMOD", "INCMI", "TTOMI", "INCANG", "TTOANG", "INCANGIO", "TTOANGI",
             "INCBYPS", "TTOBYPS", "INCCHF", "TTOCHF", "INCSTRK", "TTOSTK", "DEATH", "TTODTH", "CAUSE80", "INCAFIB",
             "TTOAFIB", "PREVALENT", "EVTYPE", "TTOEVENT", "TTOFCNDT", "TTONFCND"}
    cols |= {f.upper() for fl in CC.CHS_CLASSES.values() for f in fl}
    cols |= {f"DCODE{i}" for i in range(1, 11)} | {f"PCODE{i}" for i in range(1, 11)} | {"ADDAYS58"}
    CC.WANT.update(cols)
    CC.WANT_RE[:] = [r"[A-Z0-9]+06"]  # every medication-class flag (98 per visit table)
    T = {}
    for t in list(TABLE_VISIT) + STATIC + ["ICD9"]:
        t0 = time.time()
        T[t] = CC.table(files, t)
        BC.log(f"  read {t}: {len(T[t])} rows ({time.time() - t0:.0f} s)")
    U, seen, _, _ = CC.use_matrix(files, "CHS")
    return T, U, seen


def key(D):
    return D[CC.key_col(D)].astype(str).str.strip().map(lambda v: CC.XW.get(v, v))


def long_measures(T) -> pd.DataFrame:
    """(id, visit, item, value) for held-out/clinical items, age, study day, diabetes meds."""
    rows = []
    entry = {}
    bb = T["BASEBOTH"]
    if len(bb):
        bid = key(bb)
        per = pd.to_numeric(bb.get("PERSTAT", pd.Series(1, index=bb.index)), errors="coerce").fillna(1)
        entry = dict(zip(bid, np.where(per == 2, 5, 2)))
    for t, D in T.items():
        if not len(D) or (t not in TABLE_VISIT and t != "BASEBOTH"):
            continue
        ids = key(D)
        vis = ids.map(entry).fillna(2).astype(int) if t == "BASEBOTH" else pd.Series(TABLE_VISIT[t], index=D.index)
        up = {c.upper(): c for c in D.columns}
        if "DPMEP43" in up and "DPMAP43" in up:
            D = D.copy()
            D["E_A"] = pd.to_numeric(D[up["DPMEP43"]], errors="coerce") / pd.to_numeric(D[up["DPMAP43"]], errors="coerce")
            up["E_A"] = "E_A"
        items = dict(HELD)
        items["age"] = ["AGEBL"] + [f"AGEY{k}" for k in range(3, 12)]
        items["day"] = ["STDYTIME"]
        items["diab_med"] = ["INSULN06", "OHGA06"]
        items["htn_med"] = ["HTNMED06"]
        for it, cands in items.items():
            got = [up[c] for c in cands if c in up]
            if not got:
                continue
            x = pd.concat([pd.to_numeric(D[g], errors="coerce") for g in got], axis=1)
            v = x.max(axis=1) if it in ("diab_med", "htn_med") else x.bfill(axis=1).iloc[:, 0]
            rows.append(pd.DataFrame(dict(id=ids, visit=vis, item=it, value=v)))
    L = pd.concat(rows, ignore_index=True).dropna(subset=["value"])
    # entry visits have no STDYTIME: day 0
    L = pd.concat([L, pd.DataFrame(dict(id=list(entry), visit=list(entry.values()), item="day", value=0.0))])
    return L.drop_duplicates(["id", "visit", "item"], keep="first"), entry


def exact(L: pd.DataFrame, R: pd.DataFrame, item: str, at: str) -> pd.Series:
    """Value of item at exactly visit R[at] (NaN if not recorded at that visit). Vectorised join."""
    x = L[L.item == item][["id", "visit", "value"]].drop_duplicates(["id", "visit"])
    q = pd.DataFrame({"id": R.id.to_numpy(), "visit": R[at].astype(int).to_numpy(), "_r": np.arange(len(R))})
    m = q.merge(x, on=["id", "visit"], how="left").sort_values("_r")
    return pd.Series(m.value.to_numpy(), index=R.index)


def latest_before(L: pd.DataFrame, R: pd.DataFrame, item: str, upto: str = "k1") -> pd.Series:
    """Latest value of item at a visit <= R[upto] per row of R (columns id, k1). Vectorised as-of join."""
    x = L[L.item == item][["id", "visit", "value"]].dropna().sort_values("visit")
    if not len(x):
        return pd.Series(np.nan, index=R.index)
    q = pd.DataFrame({"id": R.id.to_numpy(), "visit": R[upto].astype(int).to_numpy(), "_r": np.arange(len(R))})
    q = q.sort_values("visit")
    x = x.astype({"visit": int})
    m = pd.merge_asof(q, x, on="visit", by="id", direction="backward").sort_values("_r")
    return pd.Series(m.value.to_numpy(), index=R.index)


def sequential(U: pd.DataFrame, a: str) -> pd.DataFrame:
    """Sequential trials vs none: at each visit k, initiators (first use at k) and non-users through k (>= 1 prior visit)."""
    out = []
    for pid, g in U.sort_values(["id", "visit"]).groupby("id", sort=False):
        g = g.dropna(subset=[a])
        A, vis = g[a].to_numpy() == 1, g.visit.to_numpy()
        for i in range(1, len(g)):
            if A[:i].any():
                break
            out.append((pid, vis[i], int(A[i])))
            if A[i]:
                break
    return pd.DataFrame(out, columns=["id", "visit", "arm"])


def build(root: Path):
    BC.log("indexing project files ...")
    files = CC.index(root)
    BC.log(f"{len(files)} files; reading CHS tables ...")
    T, U, seen = load(files)
    BC.log("tables read; building measurements ...")
    L, entry = long_measures(T)
    ev_files, ev_info = CC.ecg_visits(files, "CHS", set(U.id))
    paths = {p.name: str(p) for p in files if p.name.upper().startswith("CHS_ECG") and p.name.lower().endswith(".xml")}
    # file name per (id, VISIT label) from the PFB table
    ecg_name = {}
    for img in [p for p in files if p.name == "imaging_file.tsv"]:
        I = pd.read_csv(img, sep="\t", low_memory=False, dtype=str)
        if not I["object.file_name"].str.upper().str.startswith("CHS_ECG").any():
            continue
        sub = pd.read_csv(img.parent / "subject.tsv", sep="\t", low_memory=False, dtype=str)
        best = max(sub.columns, key=lambda c: sub[c].astype(str).str.strip().isin(CC.XW).sum())
        m = dict(zip(sub["id"], sub[best].astype(str).str.strip().map(CC.XW)))
        I["pid"] = I["relations.dst_id"].map(m)
        I["lab"] = I["object.file_name"].str.extract(CC.ECG_NAME)[0].astype(float)
        for pid, lab, fn in I.dropna(subset=["pid", "lab"])[["pid", "lab", "object.file_name"]].itertuples(index=False):
            ecg_name.setdefault((pid, int(lab)), fn)
        break
    ES = T["EVENT_SUMMARY"]
    es = pd.DataFrame({"id": key(ES)}) if len(ES) else pd.DataFrame(columns=["id"])
    for c in ("MIBLMOD", "ANBLMOD", "CHBLMOD", "STBLMOD", "INCMI", "TTOMI", "INCANG", "TTOANG", "INCANGIO", "TTOANGI",
              "INCBYPS", "TTOBYPS", "INCCHF", "TTOCHF", "INCSTRK", "TTOSTK", "DEATH", "TTODTH", "CAUSE80"):
        es[c] = pd.to_numeric(ES[c], errors="coerce") if c in ES else np.nan
    es = es.drop_duplicates("id").set_index("id")
    AF = T["CARE_AFIB"]
    af = pd.DataFrame({"id": key(AF), "INCAFIB": pd.to_numeric(AF.get("INCAFIB"), errors="coerce"),
                       "TTOAFIB": pd.to_numeric(AF.get("TTOAFIB"), errors="coerce"),
                       "PREV": pd.to_numeric(AF.get("PREVALENT"), errors="coerce")}).drop_duplicates("id").set_index("id") if len(AF) else None
    E16 = T["CHS_Event16"]
    e16 = pd.DataFrame({"id": key(E16), "EVTYPE": pd.to_numeric(E16["EVTYPE"], errors="coerce"),
                        "T": pd.to_numeric(E16["TTOEVENT"], errors="coerce")}).dropna() if len(E16) else pd.DataFrame(columns=["id", "EVTYPE", "T"])
    CEN = T["EVENT_TIME_TO_CENSUS"]
    cen = pd.DataFrame({"id": key(CEN), "CF": pd.to_numeric(CEN.get("TTOFCNDT"), errors="coerce"),
                        "CN": pd.to_numeric(CEN.get("TTONFCND"), errors="coerce")}).drop_duplicates("id").set_index("id") if len(CEN) else None
    BB = T["BASEBOTH"]
    st = pd.DataFrame({"id": key(BB)})
    for c in ("GEND01", "RACE01", "BPHI", "DIABADA", "SMOKE"):
        st[c] = pd.to_numeric(BB[c], errors="coerce") if c in BB else np.nan
    st = st.drop_duplicates("id").set_index("id")

    allrows = []
    t_start = time.time()
    for E in EMUS:
        BC.log(f"{E['name']}: building ({time.time() - t_start:.0f} s)")
        N = CC.new_users(U, E["A"], E["B"]) if E["B"] else sequential(U, E["A"])
        if not len(N):
            continue
        N = N.rename(columns={"visit": "k"})
        N["k1"] = N.k - 1
        N["EMU"] = E["name"]
        N["day0"] = exact(L, N, "day", "k")       # study day of visit k (time zero); must be recorded at k
        N["day_k1"] = exact(L, N, "day", "k1")
        N["AGE"] = latest_before(L, N, "age")
        for c in ("GEND01", "RACE01", "BPHI", "DIABADA", "SMOKE"):
            N[c] = N.id.map(st[c]) if c in st else np.nan
        N["MALE"] = (N.GEND01 == 1).astype(float)
        N["BLACK"] = (N.RACE01 == 2).astype(float)
        N["HTN"] = ((N.BPHI == 1) | (latest_before(L, N, "htn_med") == 1)).astype(float)
        N["DIAB"] = (N.DIABADA.isin([3, 4]) | (latest_before(L, N, "diab_med") == 1)).astype(float)

        def prior(flag_prev, inc, tto):
            p = es.reindex(N.id)
            return ((p[flag_prev].to_numpy() == 1) | ((p[inc].to_numpy() == 1) & (p[tto].to_numpy() <= N.day_k1.to_numpy()))).astype(float)
        N["CAD"] = np.maximum.reduce([prior("MIBLMOD", "INCMI", "TTOMI"), prior("ANBLMOD", "INCANG", "TTOANG"),
                                      ((es.reindex(N.id).INCANGIO.to_numpy() == 1) & (es.reindex(N.id).TTOANGI.to_numpy() <= N.day_k1.to_numpy())).astype(float),
                                      ((es.reindex(N.id).INCBYPS.to_numpy() == 1) & (es.reindex(N.id).TTOBYPS.to_numpy() <= N.day_k1.to_numpy())).astype(float)])
        N["HF"] = prior("CHBLMOD", "INCCHF", "TTOCHF")
        N["STROKE_HX"] = prior("STBLMOD", "INCSTRK", "TTOSTK")
        if af is not None:
            a_ = af.reindex(N.id)
            N["AF"] = ((a_.PREV.to_numpy() == 1) | ((a_.INCAFIB.to_numpy() == 1) & (a_.TTOAFIB.to_numpy() <= N.day_k1.to_numpy()))).astype(float)
        else:
            N["AF"] = np.nan
        for it in HELD:
            N[it] = latest_before(L, N, it)
        # eligibility
        ok = N.AGE.between(*E["age"]) & N.day0.notna()
        for x in E["excl"]:
            ok &= N[x] != 1
        N = N[ok].copy()
        # ECG: visit k-1 = file label k-2
        N["ECG_FILE"] = [ecg_name.get((i, int(k1) - 1)) for i, k1 in zip(N.id, N.k1)]
        N["ECG_XML_PATH"] = N.ECG_FILE.map(paths)
        # outcomes from time zero (day0)
        ids = N.id.to_numpy()
        e_ = es.reindex(ids)
        death_t = np.where(e_.DEATH.to_numpy() == 1, e_.TTODTH.to_numpy(), np.inf)
        cause = e_.CAUSE80.to_numpy()
        c_ = cen.reindex(ids) if cen is not None else None
        cens = np.nanmin(np.c_[c_.CF.to_numpy(), c_.CN.to_numpy()], axis=1) if c_ is not None else np.full(len(N), np.inf)
        cens = np.where(np.isnan(cens), np.inf, cens)
        d0 = N.day0.to_numpy()
        firsts = {}
        for nm, code in EV.items():
            x = e16[e16.EVTYPE == code]
            m = x.merge(pd.DataFrame({"id": ids, "d0": d0, "r": np.arange(len(ids))}), on="id")
            m = m[m["T"] > m.d0]
            f = np.full(len(ids), np.inf)
            if len(m):
                mm = m.groupby("r")["T"].min()
                f[mm.index.to_numpy()] = mm.to_numpy()
            firsts[nm] = f
        firsts["DEATH"] = death_t
        firsts["CHD_DEATH"] = np.where(cause == 1, death_t, np.inf)
        firsts["CV_DEATH"] = np.where(np.isin(cause, [1, 2, 3]), death_t, np.inf)
        H = E["H"] * MO
        for oname, comps in [("primary", E["primary"])] + list(SECONDARY.items()):
            ev_t = np.min(np.c_[tuple(firsts[c] for c in comps)], axis=1)
            # stop at censoring, horizon or death (a fatal component event at the death date still counts: ev_t == stop)
            stop = np.minimum.reduce([cens, d0 + H, death_t])
            ev = (ev_t <= stop) & (ev_t > d0)
            N[f"T_{oname}"] = (np.where(ev, ev_t, stop) - d0)
            N[f"E_{oname}"] = ev.astype(int)
        N["cluster"] = E["cluster"]
        N["bench"] = E["bench"]
        allrows.append(N)
    R = pd.concat(allrows, ignore_index=True) if allrows else pd.DataFrame()
    BC.log(f"code features for {len(R)} rows ...")
    K = code_features(T, R) if len(R) else pd.DataFrame(columns=["row", "code"])
    if len(R):
        R["row"] = np.arange(len(R))
        R["n_codes"] = R.row.map(K.groupby("row").size()).fillna(0).astype(int)
        R["n_hosp_codes"] = R.row.map(K[K.code.str.match(r"^[DP]:")].groupby("row").size()).fillna(0).astype(int)
    return R, dict(seen=seen, ecg=ev_info, n_xml_local=S(len(paths)), codes=K)


def code_features(T, R: pd.DataFrame) -> pd.DataFrame:
    """Long (row, code) table: ICD-9 diagnosis (3-digit, 'D:') and procedure (2-digit, 'P:') codes of hospitalisations
    admitted before the visit k-1 study day, and medication-class flags ('M:') recorded at visit k-1 (excluding each
    emulation's exposure drugs and summary flags that contain them)."""
    import re as _re
    R = R.reset_index(drop=True)
    out = []
    H = T.get("ICD9", pd.DataFrame())
    if len(H):
        hid = key(H)
        ad = pd.to_numeric(H.get("ADDAYS58"), errors="coerce")
        rows = []
        for i in range(1, 11):
            for pre, col, n in (("D", f"DCODE{i}", 3), ("P", f"PCODE{i}", 2)):
                if col in H:
                    c = H[col].astype(str).str.strip().str.replace(".", "", regex=False)
                    ok = c.str.len().ge(n) & ~c.isin(["nan", "", "."])
                    rows.append(pd.DataFrame({"id": hid[ok], "day": ad[ok], "code": pre + ":" + c[ok].str[:n]}))
        HC = pd.concat(rows, ignore_index=True).dropna(subset=["day"]) if rows else pd.DataFrame(columns=["id", "day", "code"])
        m = R[["id", "day_k1"]].reset_index().rename(columns={"index": "row"}).merge(HC, on="id")
        m = m[m.day < m.day_k1]
        out.append(m[["row", "code"]])
    # medication flags at visit k-1
    for t, D in T.items():
        if t not in TABLE_VISIT or not len(D) or t == "CYST_C_YR5":
            continue
        v = TABLE_VISIT[t]
        flags = [c for c in D.columns if _re.fullmatch(r"[A-Z0-9]+06", str(c).upper())]
        if not flags:
            continue
        ids = key(D)
        M = D[flags].apply(pd.to_numeric, errors="coerce").eq(1)
        M.insert(0, "id", ids.to_numpy())
        long = M.melt(id_vars="id", var_name="flag", value_name="on")
        long = long[long.on]
        rr = R[R.k1 == v][["id", "EMU"]].reset_index().rename(columns={"index": "row"})
        mm = rr.merge(long, on="id")
        for emu, g in mm.groupby("EMU"):
            g = g[~g.flag.str.upper().str.fullmatch(EXPOSURE_FLAGS.get(emu, "$^"))]
            out.append(pd.DataFrame({"row": g.row, "code": "M:" + g.flag.str.upper()}))
    return pd.concat(out, ignore_index=True).drop_duplicates() if out else pd.DataFrame(columns=["row", "code"])


def report(R: pd.DataFrame, info: dict, path: Path) -> None:
    L = [f"# CHS emulation cohorts ({time.strftime('%Y-%m-%d %H:%M')}, git {BC.git_sha()[:10]})", "",
         f"- ECG linkage: {info['ecg']}; local XML files: {info['n_xml_local']}", "",
         "| emulation | arm | n | with ECG file | follow-up >0 | primary events | mean held-out coverage | pre-match mean \\|SMD\\| (held-out) |",
         "|---|---|---|---|---|---|---|---|"]
    for e, g in R.groupby("EMU", sort=False):
        t = g.arm.to_numpy()
        smds = []
        for it in HELD:
            x = pd.to_numeric(g[it], errors="coerce")
            a, b = x[t == 1].dropna(), x[t == 0].dropna()
            if len(a) > 10 and len(b) > 10:
                s = np.sqrt((a.var() + b.var()) / 2)
                if s > 0:
                    smds.append(abs(a.mean() - b.mean()) / s)
        for arm in (1, 0):
            h = g[g.arm == arm]
            cov = float(np.mean([h[it].notna().mean() for it in HELD])) if len(h) else np.nan
            L.append(f"| {e} | {'A' if arm else 'B'} | {S(len(h))} | {S(int(h.ECG_XML_PATH.notna().sum()))} | "
                     f"{S(int((h.T_primary > 0).sum()))} | {S(int(h.E_primary.sum()))} | {cov:.2f} | "
                     f"{np.mean(smds):.3f} ({len(smds)} items) |")
    L += ["", "## Held-out item coverage (share non-missing, all rows)", ""]
    L += [f"- {it} ({DOMAIN(it)}): {R[it].notna().mean():.2f}" for it in HELD]
    if "n_codes" in R:
        L += ["", "## Code features before time zero (PS-Codes rung)", ""]
        for e, g in R.groupby("EMU", sort=False):
            L.append(f"- {e}: any hospital code {(g.n_hosp_codes > 0).mean():.0%}; median codes per person "
                     f"{g.n_codes.median():.0f} (hospital {g.n_hosp_codes.median():.0f})")
    L += ["", "## PS covariate coverage / prevalence", ""]
    for c in ("AGE", "MALE", "BLACK", "HTN", "DIAB", "CAD", "AF", "HF"):
        L.append(f"- {c}: non-missing {R[c].notna().mean():.2f}, mean {pd.to_numeric(R[c], errors='coerce').mean():.3f}")
    path.write_text("\n".join(L) + "\n")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=BC.SB_INPUT_ROOTS[0])
    a = ap.parse_args(argv)
    t0 = time.time()
    R, info = build(Path(a.root))
    rd = restricted_dir()
    K = info.pop("codes")
    try:
        R.to_parquet(rd / "chs_emulations.parquet", index=False)
        K.to_parquet(rd / "chs_codes.parquet", index=False)
        rf = rd / "chs_emulations.parquet"
    except Exception:  # noqa: BLE001
        R.to_pickle(rd / "chs_emulations.pkl")
        K.to_pickle(rd / "chs_codes.pkl")
        rf = rd / "chs_emulations.pkl"
    out = BC.out_root() / "chs_cohort"
    out.mkdir(parents=True, exist_ok=True)
    report(R, info, out / "report.md")
    print((out / "report.md").read_text())
    BC.log(f"restricted: {rf} (stays in BDC); {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
