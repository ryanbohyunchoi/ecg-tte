#!/usr/bin/env python
"""SPRINT step 1: cohort, ID linkage and baseline-ECG assignment (Figure 5; docs/bdc/BDC_FEASIBILITY.md).

Runs inside the BDC Data Studio. Reads the BioLINCC SPRINT CSVs and the Gen3 PFB tables (tsv/subject.tsv,
tsv/imaging_file.tsv) exported into the project, and:

  1. builds one row per randomized participant: arm, baseline covariates (the PS inputs and the hidden-confounder
     candidates), the baseline reading-centre ECG measures (positive controls) and outcomes;
  2. finds which Gen3 subject ID equals MASKID (overlap counts of every candidate column; no values written);
  3. assigns each participant's baseline ECG XML: the Gen3 files of a subject are ordered by file-name year and
     serial and aligned with that participant's reading-centre ECGs ordered by ECGDAYS (equal counts required;
     year spacing checked against ECGDAYS spacing); the first file is the baseline ECG when its ECGDAYS is in
     [-90, 30];
  4. checks the build: randomized-arm balance (|SMD| should be ~0) and the crude primary-outcome HR against the
     published 0.75 (Wright, NEJM 2015; SPRINT-POP outcomes).

Restricted output (participant-level, never leaves BDC): $BDC_RESTRICTED (default /sbgenomics/workspace/bdc-restricted)
/sprint_cohort.{parquet|pkl}. Aggregate output: <out>/sprint_cohort/report.md + report.json (counts 1-10 suppressed).

Usage: python scripts/bdc/sprint_cohort.py [--root /sbgenomics/project-files]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bdc_common as BC  # noqa: E402

S = BC.suppress
BASELINE_WINDOW = (-90, 30)  # ECGDAYS of a baseline ECG (randomization visit = day 0)
ECG_NAME = re.compile(r"_ECG_(?:[A-Za-z0-9]+_)?VISIT\d+_(\d{4})\d{4}_(\d+)\.xml$", re.I)

# SPRINT-POP baseline.csv columns used as-is
POP_COLS = ["AGE", "FEMALE", "RACE_BLACK", "RACE4", "SBP", "DBP", "N_AGENTS", "SMOKE_3CAT", "ASPIRIN", "STATIN",
            "EGFR", "SCREAT", "SUB_CKD", "SUB_CVD", "SUB_CLINICALCVD", "SUB_SUBCLINICALCVD", "CHR", "GLUR", "HDL",
            "TRR", "UMALCR", "BMI", "RISK10YRS", "INTENSIVE"]
# reading-centre ECG measures at baseline (positive controls: derived from the same ECG)
ECG_COLS = ["QRSDURATION", "CV", "CVP", "SL", "LVHCV", "LVHCVP", "LVHMC", "LVHSL", "LVHANY3", "AFIBFLUTTER", "QUAL"]


def restricted_dir() -> Path:
    p = Path(os.environ.get("BDC_RESTRICTED", "/sbgenomics/workspace/bdc-restricted"))
    os.umask(0o077)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------- file discovery
def index_files(root: Path) -> dict:
    """basename -> sorted list of paths (latest export folder last)."""
    idx = {}
    for dirpath, _d, files in os.walk(root, followlinks=True):
        for f in files:
            idx.setdefault(f, []).append(Path(dirpath) / f)
    return {k: sorted(v, key=str) for k, v in idx.items()}


def pick(idx: dict, name: str, prefer: str = "", required: bool = True):
    c = idx.get(name, [])
    if prefer:
        c = [p for p in c if prefer in str(p)] or c
    if not c:
        if required:
            raise SystemExit(f"missing input file {name} (prefer '{prefer}') under the project files; import it first")
        return None
    return c[-1]


def read_csv(p: Path) -> pd.DataFrame:
    return pd.read_csv(p, sep="\t" if p.suffix == ".tsv" else ",", low_memory=False, encoding="latin-1")


def pfb_tables(idx: dict):
    """subject.tsv and imaging_file.tsv from the same (latest) export that has imaging_file.tsv."""
    imgs = idx.get("imaging_file.tsv", [])
    if not imgs:
        raise SystemExit("missing tsv/imaging_file.tsv: export img_SPRINT_GRU from Gen3 to Seven Bridges first")
    img = imgs[-1]
    sub = img.parent / "subject.tsv"
    if not sub.exists():
        raise SystemExit(f"missing subject.tsv next to {img.parent}")
    return read_csv(sub), read_csv(img), str(img.parent.parent.name)


def fmt_patterns(v: pd.Series, k: int = 3) -> dict:
    """Most common ID shapes (letters -> A, digits -> #), with counts; never the IDs themselves."""
    pat = v.astype(str).str.replace(r"[A-Za-z]", "A", regex=True).str.replace(r"\d", "#", regex=True)
    return {p[:40]: S(int(n)) for p, n in pat.value_counts().head(k).items()}


# ---------------------------------------------------------------- statistics
def smd(x: pd.Series, t: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce")
    a, b = x[t == 1].dropna(), x[t == 0].dropna()
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    s = np.sqrt((a.var() + b.var()) / 2)
    return float((a.mean() - b.mean()) / s) if s > 1e-9 * max(1.0, abs(x.mean())) else 0.0


def cox_binary(time_, event, x):
    """Cox PH with one binary covariate, Breslow ties, Newton-Raphson. Returns (HR, lo95, hi95)."""
    d = pd.DataFrame(dict(t=time_, e=event, x=x)).dropna()
    d = d.sort_values("t", ascending=False)
    t, e, xv = d.t.to_numpy(float), d.e.to_numpy(int), d.x.to_numpy(float)
    if e.sum() == 0 or e[xv == 1].sum() == 0 or e[xv == 0].sum() == 0:
        return float("nan"), float("nan"), float("nan")
    b = 0.0
    for _ in range(50):
        r = np.exp(b * xv)
        s0, s1 = np.cumsum(r), np.cumsum(r * xv)  # risk sets: everyone with time >= t (sorted descending)
        # for tied times use the risk set at the first (largest index) occurrence
        last = pd.Series(np.arange(len(t))).groupby(t).transform("max").to_numpy()
        s0, s1 = s0[last], s1[last]
        m = e == 1
        p = s1[m] / s0[m]
        g = float((xv[m] - p).sum())
        h = float((p - p ** 2).sum())
        step = g / h
        b += step
        if abs(step) < 1e-10:
            break
    se = 1 / np.sqrt(h)
    return float(np.exp(b)), float(np.exp(b - 1.96 * se)), float(np.exp(b + 1.96 * se))


# ---------------------------------------------------------------- build
def build(root: Path) -> tuple[pd.DataFrame, dict]:
    idx = index_files(root)
    R = dict(when=time.strftime("%Y-%m-%d %H:%M"), git=BC.git_sha(), root=str(root))
    key = read_csv(pick(idx, "keyvar.csv", "SPRINT/data"))
    pop = read_csv(pick(idx, "baseline.csv", "SPRINT-POP"))
    inc = read_csv(pick(idx, "incl_excl.csv", "SPRINT/data"))
    hist = read_csv(pick(idx, "bl_history.csv", "SPRINT/data"))
    bio = read_csv(pick(idx, "sprint_biomarker_as_shared.csv", "Biomarkers"))
    ecg = read_csv(pick(idx, "ecg.csv", "SPRINT/data"))
    out = read_csv(pick(idx, "outcomes.csv", "SPRINT-POP"))
    psurv = read_csv(pick(idx, "primarysurv.csv", "SPRINT/data"))
    dsurv = read_csv(pick(idx, "alldeath.csv", "SPRINT/data"))
    for D in (key, pop, inc, hist, bio, ecg, out, psurv, dsurv):
        D["MASKID"] = D["MASKID"].astype(str).str.strip()

    C = key[["MASKID", "RANDASSIGN"]].merge(pop[["MASKID"] + [c for c in POP_COLS if c in pop]], on="MASKID", how="left")
    C = C.merge(inc[["MASKID", "HRAVG", "LVHCOMPECG", "CVDPOINTS", "CIGSMOKER"]], on="MASKID", how="left")
    C = C.merge(hist[["MASKID", "ATRIALFIB", "CONHEARTFAIL", "HEARTATT", "EDUCATION"]], on="MASKID", how="left")
    b0 = bio[bio.VISITCODE.astype(str).str.upper() == "RZ"][["MASKID", "NT_PROBNP", "HSTNI"]].drop_duplicates("MASKID")
    C = C.merge(b0, on="MASKID", how="left")
    C["LOG_NTPROBNP"] = np.log(pd.to_numeric(C.NT_PROBNP, errors="coerce").clip(lower=1))
    C["LOG_HSTNI"] = np.log(pd.to_numeric(C.HSTNI, errors="coerce").clip(lower=0.5))
    C["LOG_UMALCR"] = np.log(pd.to_numeric(C.UMALCR, errors="coerce").clip(lower=0.5))
    tg = pd.to_numeric(C.TRR, errors="coerce")
    C["LDL_CALC"] = (pd.to_numeric(C.CHR, errors="coerce") - pd.to_numeric(C.HDL, errors="coerce") - tg / 5).where(tg < 400)
    # outcomes: SPRINT-POP (2015 release; published HR 0.75) and the full adjudicated files
    C = C.merge(out[["MASKID", "EVENT_PRIMARY", "T_PRIMARY", "EVENT_DEATH", "T_DEATH", "EVENT_PRIMARYORDEATH",
                     "T_PRIMARYORDEATH", "EVENT_HF", "T_HF", "EVENT_CVDDEATH", "T_CVDDEATH"]], on="MASKID", how="left")
    for nm, D in (("FULL_PRIMARY", psurv), ("FULL_DEATH", dsurv)):
        C = C.merge(D[["MASKID", "EVENT", "EVENTDAYS", "EVENTDAYS_POSTI"]].rename(
            columns=dict(EVENT=f"EVENT_{nm}", EVENTDAYS=f"T_{nm}", EVENTDAYS_POSTI=f"POSTI_{nm}")), on="MASKID", how="left")
    R["n_randomized"] = len(C)
    R["n_by_arm"] = {str(k): S(v) for k, v in C.RANDASSIGN.value_counts().items()}
    R["arm_agrees_with_pop_INTENSIVE"] = S(int((C.RANDASSIGN == C.INTENSIVE).sum()))

    # ---- reading-centre ECGs
    ecg["ECGDAYS"] = pd.to_numeric(ecg.ECGDAYS, errors="coerce")
    ecg = ecg.sort_values(["MASKID", "ECGDAYS"])
    ecg["k"] = ecg.groupby("MASKID").cumcount()
    base = ecg[ecg.ECGDAYS.between(*BASELINE_WINDOW)].drop_duplicates("MASKID")
    C = C.merge(base[["MASKID", "ECGDAYS"] + [c for c in ECG_COLS if c in ecg]].rename(
        columns={c: f"ECG_{c}" for c in ["ECGDAYS"] + ECG_COLS}), on="MASKID", how="left")
    R["reading_centre"] = dict(n_ecgs=S(len(ecg)), n_participants=S(ecg.MASKID.nunique()),
                               n_with_baseline_ecg=S(len(base)),
                               ecgs_per_participant={str(k): S(v) for k, v in ecg.groupby("MASKID").size().value_counts().sort_index().items()})

    # ---- Gen3 subject <-> MASKID (exact, then token match: e.g. 'SPRINT_<MASKID>'); only counts and ID format
    # patterns (letters -> A, digits -> #) are written
    sub, img, export = pfb_tables(idx)
    R["pfb_export"] = export
    mask = set(C.MASKID)
    R["maskid_format"] = fmt_patterns(C.MASKID)
    cand, maps = {}, {}
    for col in sub.columns:
        if not (sub[col].dtype == object or "id" in col.lower()):
            continue
        v = sub[col].astype(str).str.strip()
        tok = v.map(lambda s: next((x for x in re.split(r"[_\-:./|]", s) if x in mask), None))
        cand[col] = dict(exact=S(int(v.isin(mask).sum())), token=S(int(tok.notna().sum())), format=fmt_patterns(v))
        maps[col] = v.where(v.isin(mask), tok)
    R["subject_id_overlap_with_MASKID"] = cand
    n_ok = {c: int(maps[c].notna().sum()) for c in maps}
    best = max(n_ok, key=n_ok.get) if n_ok else None
    if best is None or n_ok[best] < 0.5 * len(sub):
        R["linkage_error"] = "no subject column matches MASKID for at least half of the Gen3 subjects; see overlap table"
        return C, R
    R["subject_key_column"] = best
    sub["MASKID"] = maps[best]
    img = img.merge(sub[["id", "MASKID"]].rename(columns={"id": "relations.dst_id"}), on="relations.dst_id", how="left")
    R["imaging_files"] = S(len(img))
    R["imaging_files_linked_to_maskid"] = S(int(img.MASKID.isin(mask).sum()))

    # ---- XML files: year + serial from the file name; local path
    m = img["object.file_name"].astype(str).str.extract(ECG_NAME)
    img["year"], img["serial"] = pd.to_numeric(m[0], errors="coerce"), pd.to_numeric(m[1], errors="coerce")
    img["path"] = img["object.file_name"].map(lambda f: str(idx[f][-1]) if f in idx else None)
    R["imaging_files_found_locally"] = S(int(img.path.notna().sum()))
    img = img[img.MASKID.isin(mask)].sort_values(["MASKID", "year", "serial"])
    img["k"] = img.groupby("MASKID").cumcount()
    nf = img.groupby("MASKID").size().rename("n_files")
    ne = ecg.groupby("MASKID").size().rename("n_ecgs")
    cnt = pd.concat([nf, ne], axis=1).fillna(0)
    R["files_vs_reading_centre_counts"] = dict(equal=S(int((cnt.n_files == cnt.n_ecgs).sum())),
                                              more_files=S(int((cnt.n_files > cnt.n_ecgs).sum())),
                                              fewer_files=S(int((cnt.n_files < cnt.n_ecgs).sum())))
    eq = cnt.index[cnt.n_files == cnt.n_ecgs]
    A = img[img.MASKID.isin(eq)].merge(ecg[["MASKID", "k", "ECGDAYS"]], on=["MASKID", "k"], how="left")
    first = A.groupby("MASKID").first()
    dy = (A.year - A.MASKID.map(first.year))
    dd = (A.ECGDAYS - A.MASKID.map(first.ECGDAYS)) / 365.25
    ok = (dy - dd).abs() <= 1.5
    R["aligned_year_spacing_consistent"] = dict(files=S(len(A)), consistent=S(int(ok.sum())))
    badsubj = set(A.MASKID[~ok])
    bl = A[(A.k == 0) & A.ECGDAYS.between(*BASELINE_WINDOW) & ~A.MASKID.isin(badsubj)]
    C = C.merge(bl[["MASKID", "path", "object.object_id", "year"]].rename(
        columns={"path": "ECG_XML_PATH", "object.object_id": "ECG_OBJECT_ID", "year": "ECG_FILE_YEAR"}), on="MASKID", how="left")
    C["HAS_BASELINE_XML"] = C.ECG_XML_PATH.notna().astype(int)
    R["baseline_xml"] = dict(assigned=S(int(C.HAS_BASELINE_XML.sum())),
                             by_arm={str(k): S(int(v)) for k, v in C.groupby("RANDASSIGN").HAS_BASELINE_XML.sum().items()},
                             file_year={str(int(k)): S(int(v)) for k, v in C.ECG_FILE_YEAR.value_counts().sort_index().items()},
                             assigned_but_file_missing_locally=S(int((C.ECG_OBJECT_ID.notna() & C.ECG_XML_PATH.isna()).sum())))
    return C, R


def report(C: pd.DataFrame, R: dict) -> dict:
    t = C.RANDASSIGN
    cov = {}
    skip = {"MASKID", "RANDASSIGN", "INTENSIVE", "ECG_XML_PATH", "ECG_OBJECT_ID", "RACE4"}
    for c in C.columns:
        if c in skip or c.startswith(("EVENT_", "T_", "POSTI_")):
            continue
        x = pd.to_numeric(C[c], errors="coerce")
        if x.notna().sum() == 0:
            continue
        cov[c] = dict(nonmissing=round(float(x.notna().mean()), 3), mean=float(f"{x.mean():.4g}"),
                      sd=float(f"{x.std():.4g}"), smd_arm=round(smd(x, t), 3))
    R["covariates"] = cov
    R["max_abs_smd_between_randomized_arms"] = round(float(np.nanmax([abs(v["smd_arm"]) for v in cov.values()])), 3)
    hr = {}
    for ev, tt, lab in [("EVENT_PRIMARY", "T_PRIMARY", "primary (SPRINT-POP; published 0.75, 0.64-0.89)"),
                        ("EVENT_DEATH", "T_DEATH", "death (SPRINT-POP; published 0.73, 0.60-0.90)"),
                        ("EVENT_PRIMARYORDEATH", "T_PRIMARYORDEATH", "primary or death (SPRINT-POP)"),
                        ("EVENT_FULL_PRIMARY", "T_FULL_PRIMARY", "primary (full adjudicated file, incl. post-intervention)")]:
        if ev not in C or C[ev].notna().sum() == 0:
            continue
        e = pd.to_numeric(C[ev], errors="coerce")
        h = cox_binary(pd.to_numeric(C[tt], errors="coerce"), e, t)
        hr[lab] = dict(events_intensive=S(int(e[t == 1].sum())), events_standard=S(int(e[t == 0].sum())),
                       hr=round(h[0], 3), lo=round(h[1], 3), hi=round(h[2], 3))
        if not np.isfinite(h[0]):
            continue
        sub = C.HAS_BASELINE_XML == 1 if "HAS_BASELINE_XML" in C else None
        if sub is not None and sub.sum() > 100:
            h2 = cox_binary(pd.to_numeric(C[tt], errors="coerce")[sub], e[sub], t[sub])
            hr[lab]["with_baseline_ecg"] = dict(n=S(int(sub.sum())), events=S(int(e[sub].sum())),
                                                hr=round(h2[0], 3), lo=round(h2[1], 3), hi=round(h2[2], 3))
    R["randomized_hr"] = hr
    return R


def write_md(R: dict, path: Path) -> None:
    L = [f"# SPRINT cohort and linkage ({R['when']}, git {R.get('git', '')[:10]})", "",
         f"- randomized: {R['n_randomized']}; by arm (1 = intensive): {R['n_by_arm']}; RANDASSIGN = SPRINT-POP INTENSIVE: "
         f"{R['arm_agrees_with_pop_INTENSIVE']}",
         f"- reading-centre ECGs: {R['reading_centre']}",
         f"- PFB export: {R.get('pfb_export')}; subject key column: {R.get('subject_key_column')}",
         f"- subject-ID overlap with MASKID (count of Gen3 subjects): {R.get('subject_id_overlap_with_MASKID')}"]
    if "linkage_error" in R:
        L.append(f"- **LINKAGE ERROR:** {R['linkage_error']}")
    for k in ["imaging_files", "imaging_files_linked_to_maskid", "imaging_files_found_locally",
              "files_vs_reading_centre_counts", "aligned_year_spacing_consistent", "baseline_xml"]:
        if k in R:
            L.append(f"- {k}: {R[k]}")
    L += ["", f"## Randomized-arm balance (max |SMD| = {R.get('max_abs_smd_between_randomized_arms')})", "",
          "| variable | non-missing | mean | SD | SMD (intensive vs standard) |", "|---|---|---|---|---|"]
    L += [f"| {k} | {v['nonmissing']} | {v['mean']} | {v['sd']} | {v['smd_arm']} |" for k, v in R.get("covariates", {}).items()]
    L += ["", "## Randomized HR (intensive vs standard; crude Cox)", ""]
    for k, v in R.get("randomized_hr", {}).items():
        L.append(f"- {k}: {v}")
    path.write_text("\n".join(L) + "\n")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=BC.SB_INPUT_ROOTS[0])
    a = ap.parse_args(argv)
    C, R = build(Path(a.root))
    R = report(C, R)
    rdir = restricted_dir()
    try:
        C.to_parquet(rdir / "sprint_cohort.parquet", index=False)
        R["restricted_file"] = str(rdir / "sprint_cohort.parquet")
    except Exception:  # noqa: BLE001  (no pyarrow)
        C.to_pickle(rdir / "sprint_cohort.pkl")
        R["restricted_file"] = str(rdir / "sprint_cohort.pkl")
    out = BC.out_root() / "sprint_cohort"
    out.mkdir(parents=True, exist_ok=True)
    BC.write_json(out / "report.json", R)
    write_md(R, out / "report.md")
    print((out / "report.md").read_text())
    BC.log(f"restricted cohort: {R['restricted_file']} (stays in BDC); aggregate report: {out}/report.md")


if __name__ == "__main__":
    main()
