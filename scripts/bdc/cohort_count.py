#!/usr/bin/env python
"""CHS / MESA feasibility count: new users per drug-class comparison with an ECG before initiation (aggregates only).

Design (docs/bdc/COHORT_FEASIBILITY_CHS_MESA.md): annual (CHS) or exam-based (MESA) medication inventories give 0/1 class
flags per visit. A participant is a **new user of class A vs B at visit k** if A-containing therapy is recorded at k, no
B-containing therapy at k, and neither class at any earlier visit on record (>= 1 earlier visit required). Combination
products count for every class they contain (e.g. ACE + diuretic = ACEi and thiazide), so starting a product that
contains both comparators excludes the person. 'vs none' comparisons use initiators vs participants who never used the
class through visit k.

ECG before initiation: CHS - an ECG XML at the previous annual visit (file label VISITnn = CHS year nn+1);
MESA - the exam-1 ECG (VISIT01). Held-out physiology before initiation: CHS echo at baseline (BASE2) or Year 7; MESA
exam-1 cardiac MRI (olvedm1).

Inputs: the dbGaP phenotype tables (*.txt.gz, any consent group) and the Gen3 PFB tables of the ECG imaging project
(tsv/subject.tsv + tsv/imaging_file.tsv from 'Export to Seven Bridges') under /sbgenomics/project-files.
Output: <out>/cohort_count/<cohort>/report.md, counts.csv (counts 1-10 suppressed).

Usage: python scripts/bdc/cohort_count.py --cohort CHS    (or MESA)
"""
from __future__ import annotations

import argparse
import gzip
import io
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

# visit -> dbGaP table name tokens (several tokens = rows concatenated, e.g. CHS Year 5 = both cohorts)
CHS_VISITS = {2: ["BASE1"], 3: ["YR3"], 4: ["YR4"], 5: ["YR5OLD", "YR5NEW"], 6: ["YR6"], 7: ["YR7"], 8: ["YR8"],
              9: ["YR9"], 10: ["YR10"], 11: ["YR11"]}
MESA_VISITS = {1: ["MESA_Exam1Main"], 2: ["MESA_Exam2Main"], 3: ["MESA_Exam3Main"], 4: ["MESA_Exam4Main"],
               5: ["MESA_Exam5Main"]}
# class -> flag variables ({k} = MESA exam number); combination products listed under every class they contain
CHS_CLASSES = {"ACEI": ["ACE06", "ACED06"], "CCB": ["CCB06"], "DHP_CCB": ["AMLOD06", "NIFSR06", "NIFIR06"],
               "THIAZIDE": ["HCTZ06", "HCTZK06", "ACED06", "BETAD06"], "BETA": ["BETA06", "BETAD06"],
               "STATIN": ["STTN06"], "ASPIRIN": ["ASPIRIN"]}
MESA_CLASSES = {"ACEI": ["ace{k}c", "aced{k}c"], "ARB": ["a2a{k}c", "a2ad{k}c"], "CCB": ["ccb{k}c"],
                "THIAZIDE": ["hctz{k}c", "aced{k}c", "a2ad{k}c", "betad{k}c"], "BETA": ["beta{k}c", "betad{k}c"],
                "STATIN": ["sttn{k}c"], "ANY_HTN": ["htnmed{k}c"]}
COMPARISONS = {
    "CHS": [("CCB", "THIAZIDE", "ALLHAT amlodipine vs chlorthalidone"),
            ("DHP_CCB", "THIAZIDE", "ALLHAT (dihydropyridine CCB only)"),
            ("ACEI", "THIAZIDE", "ALLHAT lisinopril vs chlorthalidone / ANBP2"),
            ("ACEI", "CCB", "STOP-2"), ("THIAZIDE", "BETA", "MRC trial in older adults"),
            ("STATIN", None, "PROSPER (statin vs none)"), ("ASPIRIN", None, "ASPREE (aspirin vs none)")],
    "MESA": [("STATIN", None, "statin vs none"), ("ACEI+ARB", "CCB", "ACEi/ARB vs CCB"),
             ("ANY_HTN", None, "any antihypertensive vs none"), ("ACEI+ARB", "THIAZIDE", "ACEi/ARB vs thiazide")],
}
ECG_LABEL = {"CHS": lambda year: year - 1, "MESA": lambda exam: exam}  # visit -> VISITnn in the XML file names
ECG_NAME = re.compile(r"_ECG_(?:[A-Za-z0-9]+_)?VISIT(\d+)_\d{8}_\d+\.xml$", re.I)


# ---------------------------------------------------------------- reading dbGaP tables
def index(root: Path) -> list:
    out = []
    for dp, _d, fs in os.walk(root, followlinks=True):
        out += [Path(dp) / f for f in fs]
    return out


def read_dbgap(p: Path) -> pd.DataFrame:
    raw = gzip.decompress(p.read_bytes()) if p.name.endswith(".gz") else p.read_bytes()
    txt = "\n".join(ln for ln in raw.decode("latin-1").splitlines() if ln and not ln.startswith("#"))
    return pd.read_csv(io.StringIO(txt), sep="\t", low_memory=False)


def table(files: list, token: str) -> pd.DataFrame:
    """All consent groups of one dbGaP table (latest study version per consent group), stacked."""
    pat = re.compile(rf"^phs\d+\.v(\d+)\.pht\d+\.v\d+\.p\d+\.(c\d+)\.{re.escape(token)}\.[^/]*\.txt(\.gz)?$")
    best = {}
    for p in files:
        m = pat.match(p.name)
        if m:
            v, c = int(m.group(1)), m.group(2)
            if c not in best or v > best[c][0]:
                best[c] = (v, p)
    if not best:
        return pd.DataFrame()
    D = pd.concat([read_dbgap(p) for _, p in best.values()], ignore_index=True)
    D.columns = [str(c) for c in D.columns]
    return D


def key_col(D: pd.DataFrame) -> str:
    for c in ("dbGaP_Subject_ID", "Individual_ID", "sidno", "SUBJID"):
        if c in D.columns:
            return c
    raise SystemExit(f"no subject ID column among {list(D.columns)[:8]}")


# ---------------------------------------------------------------- build use matrix
def use_matrix(files, cohort):
    visits = CHS_VISITS if cohort == "CHS" else MESA_VISITS
    classes = CHS_CLASSES if cohort == "CHS" else MESA_CLASSES
    rows, seen, flagdist, extra = [], {}, {}, {}
    for k, toks in visits.items():
        parts = [table(files, t) for t in toks]
        parts = [p for p in parts if len(p)]
        if not parts:
            seen[k] = 0
            continue
        D = pd.concat(parts, ignore_index=True)
        kc = key_col(D)
        lower = {c.lower(): c for c in D.columns}
        U = pd.DataFrame({"id": D[kc].astype(str), "visit": k})
        for cls, flags in classes.items():
            cols = [lower.get(f.format(k=k).lower()) for f in flags]
            cols = [c for c in cols if c is not None]
            if not cols:
                U[cls] = np.nan
                continue
            M = D[cols].apply(pd.to_numeric, errors="coerce")
            for c in cols:
                vc = M[c].value_counts(dropna=False)
                flagdist[f"V{k}:{c}"] = {str(a): S(int(b)) for a, b in vc.items()}
            U[cls] = (M == 1).any(axis=1).astype(float).where(M.notna().any(axis=1))
        if cohort == "MESA":
            U["ACEI+ARB"] = U[["ACEI", "ARB"]].max(axis=1)
        rows.append(U)
        seen[k] = int(U.id.nunique())
        extra[k] = D  # kept for held-out lookups
    U = pd.concat(rows, ignore_index=True).drop_duplicates(["id", "visit"])
    return U, seen, flagdist, extra


def new_users(U: pd.DataFrame, a: str, b: str | None) -> pd.DataFrame:
    """Rows (id, visit, arm) of new users at their first qualifying visit; 'vs none' -> arm 0 = never user to that visit
    (each eligible person counted once, at their first eligible visit after the first)."""
    out = []
    U = U.sort_values(["id", "visit"])
    for pid, g in U.groupby("id", sort=False):
        g = g.dropna(subset=[a] + ([b] if b else []))
        if len(g) < 2:
            continue
        A = g[a].to_numpy() == 1
        B = (g[b].to_numpy() == 1) if b else np.zeros(len(g), bool)
        vis = g.visit.to_numpy()
        for i in range(1, len(g)):
            if A[:i].any() or B[:i].any():
                break
            if A[i] and not B[i]:
                out.append((pid, vis[i], 1))
                break
            if b and B[i] and not A[i]:
                out.append((pid, vis[i], 0))
                break
            if b is None and not A[i] and i == 1:
                # comparator: non-user at the first follow-up visit, counted once (sequential-trial style: the same
                # person may still become an initiator at a later visit)
                out.append((pid, vis[i], 0))
    return pd.DataFrame(out, columns=["id", "visit", "arm"])


# ---------------------------------------------------------------- ECG availability (Gen3 PFB tables)
def ecg_visits(files, cohort, U_ids: set):
    """{subject id: set of VISITnn with an XML}; matched on whichever subject.tsv column overlaps the phenotype IDs."""
    imgs = [p for p in files if p.name == "imaging_file.tsv"]
    for img in sorted(imgs, key=str, reverse=True):
        I = pd.read_csv(img, sep="\t", low_memory=False)
        fn = I.get("object.file_name", pd.Series(dtype=str)).astype(str)
        if not fn.str.upper().str.startswith(f"{cohort}_ECG").any():
            continue
        sub = pd.read_csv(img.parent / "subject.tsv", sep="\t", low_memory=False)
        best, n = None, 0
        for c in sub.columns:
            k = int(sub[c].astype(str).str.strip().isin(U_ids).sum())
            if k > n:
                best, n = c, k
        if best is None:
            return None, dict(error="no subject.tsv column matches the phenotype subject IDs")
        m = dict(zip(sub["id"], sub[best].astype(str).str.strip()))
        I["pid"] = I["relations.dst_id"].map(m)
        I["vlabel"] = fn.str.extract(ECG_NAME)[0].astype(float)
        V = I.dropna(subset=["pid", "vlabel"]).groupby("pid").vlabel.apply(lambda s: set(s.astype(int)))
        info = dict(export=img.parent.parent.name, key_column=best, subjects_matched=S(n), files=S(len(I)),
                    files_linked=S(int(I.pid.notna().sum())))
        return V.to_dict(), info
    return None, dict(error=f"no imaging_file.tsv with {cohort}_ECG files: export the ECG imaging project from Gen3")


def heldout_ok(cohort, extra, ids_visits: pd.DataFrame) -> pd.Series:
    """Pre-initiation held-out physiology present: CHS echo LV mass at baseline (BASE2) or Year 7 before visit k;
    MESA exam-1 CMR LV mass."""
    if cohort == "MESA":
        D = extra.get(1)
        if D is None or "olvedm1" not in {c.lower() for c in D.columns}:
            return pd.Series(np.nan, index=ids_visits.index)
        c = [x for x in D.columns if x.lower() == "olvedm1"][0]
        ok = set(D.loc[pd.to_numeric(D[c], errors="coerce").notna(), key_col(D)].astype(str))
        return ids_visits.id.isin(ok).astype(float)
    have = {}
    for k, col in ((2, "NEWLVM43"), (7, "MMLVMS43")):
        D = extra.get("BASE2" if k == 2 else 7)
        if D is None:
            continue
        cc = [x for x in D.columns if x.upper() == col]
        if cc:
            have[k] = set(D.loc[pd.to_numeric(D[cc[0]], errors="coerce").notna(), key_col(D)].astype(str))
    if not have:
        return pd.Series(np.nan, index=ids_visits.index)
    return ids_visits.apply(lambda r: float(any(r.id in s and kk < r.visit for kk, s in have.items())), axis=1)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cohort", choices=["CHS", "MESA"], required=True)
    ap.add_argument("--root", default=BC.SB_INPUT_ROOTS[0])
    a = ap.parse_args(argv)
    t0 = time.time()
    files = index(Path(a.root))
    U, seen, flagdist, extra = use_matrix(files, a.cohort)
    if a.cohort == "CHS":
        b2 = table(files, "BASE2")
        if len(b2):
            extra["BASE2"] = b2
    ev, ev_info = ecg_visits(files, a.cohort, set(U.id))
    rows = []
    for A_, B_, bench in COMPARISONS[a.cohort]:
        N = new_users(U, A_, B_)
        if ev is not None:
            lab = ECG_LABEL[a.cohort]
            need = (lambda v: lab(v - 1)) if a.cohort == "CHS" else (lambda v: 1)
            N["ecg"] = [float(need(v) in ev.get(i, set())) for i, v in zip(N.id, N.visit)]
        else:
            N["ecg"] = np.nan
        N["heldout"] = heldout_ok(a.cohort, extra, N) if len(N) else []
        for arm, g in N.groupby("arm"):
            rows.append(dict(comparison=f"{A_} vs {B_ or 'none'}", benchmark=bench, arm=A_ if arm == 1 else (B_ or "none"),
                             n_new_users=len(g), n_with_prior_ecg=int(g.ecg.sum()) if g.ecg.notna().all() else None,
                             n_with_ecg_and_heldout=int((g.ecg * g.heldout).sum()) if g.ecg.notna().all() and g.heldout.notna().all() else None,
                             by_visit={str(int(k)): S(int(v)) for k, v in g.visit.value_counts().sort_index().items()}))
    Ct = pd.DataFrame(rows)
    for c in ("n_new_users", "n_with_prior_ecg", "n_with_ecg_and_heldout"):
        Ct[c] = Ct[c].map(lambda v: S(v) if v is not None and not (isinstance(v, float) and np.isnan(v)) else None)
    out = BC.out_root() / "cohort_count" / a.cohort
    out.mkdir(parents=True, exist_ok=True)
    Ct.to_csv(out / "counts.csv", index=False)
    L = [f"# {a.cohort} new-user feasibility ({time.strftime('%Y-%m-%d %H:%M')}, git {BC.git_sha()[:10]})", "",
         f"- participants with medication data per visit: { {k: S(v) for k, v in seen.items()} }",
         f"- ECG linkage: {ev_info}", "",
         "| comparison | benchmark | arm | new users | with prior ECG | + held-out physiology | by visit |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r.comparison} | {r.benchmark} | {r.arm} | {r.n_new_users} | {r.n_with_prior_ecg} | {r.n_with_ecg_and_heldout} | {r.by_visit} |"
          for r in Ct.itertuples()]
    L += ["", "Feasibility rule (paper): >= 350 with an ECG in the smaller arm.", "",
          "## Flag value distributions (sanity check)", ""]
    L += [f"- {k}: {v}" for k, v in flagdist.items()]
    (out / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:8 + len(Ct)]))
    BC.log(f"done in {time.time() - t0:.0f} s; full report {out}/report.md")


if __name__ == "__main__":
    main()
