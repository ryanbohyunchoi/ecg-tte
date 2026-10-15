#!/usr/bin/env python
"""Phase 0: BDC Seven Bridges environment and data probe (aggregates only). Run first, inside a Data Studio,
after importing the study files into the project. It answers what cannot be answered from public metadata:

  env      Python and package versions, GPU, CPU, memory, free disk, internet reachability (GitHub, PyPI)
  files    every file under the input roots: counts and sizes by extension and by name pattern (digits masked);
           ECG XML files counted by study, visit label and file-name year
  tables   every tabular file (csv/tsv/txt[.gz], sas7bdat, xpt, parquet, dta, xlsx; also inside zip/tar archives):
           rows, columns, per-column type, non-missing share, distinct-value count, value counts for low-cardinality
           columns and p5/p50/p95 for numeric columns. Files that look like data dictionaries / codebooks are also
           copied verbatim into docs_extract/ (documentation, no participant data; review before sharing)
  xml      a random sample of ECG XML files per series: root tag, tag-path tree (no values), whitelisted technical
           values (sampling rate, units, lead IDs, sample counts, device), base64 waveform decode check
  pfb      Gen3 PFB (avro) files: entity types, record counts, field names (no values)

Every participant count 1-10 is written as '1-10'. No participant-level value, identifier, date or ECG file name
is written. Output: <out>/probe/probe.json, probe.md, probe_columns.tsv, docs_extract/.

Usage: python scripts/bdc/bdc_probe.py [--roots DIR ...] [--only env,files,tables,xml,pfb] [--xml-sample 30]
"""
from __future__ import annotations

import argparse
import base64
import collections
import gzip
import io
import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tarfile
import time
import traceback
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bdc_common as BC  # noqa: E402

SECTIONS = ["env", "files", "tables", "xml", "pfb"]
PKGS = ["numpy", "pandas", "scipy", "scikit-learn", "lifelines", "pyarrow", "fastavro", "pyreadstat", "openpyxl",
        "torch", "sevenbridges-python", "gen3"]
TABULAR = (".csv", ".tsv", ".txt", ".sas7bdat", ".xpt", ".parquet", ".dta", ".xlsx", ".xls")
DOC_HINT = re.compile(r"(dict|codebook|readme|data_?dictionary|format|variable|_dd\b|\bdd_|description)", re.I)
ID_HINT = re.compile(r"(^id$|_id$|^id_|subj|maskid|mask_id|dbgap|participant|patient|^pid$|sample|object_?id|guid|file)",
                     re.I)
ECG_NAME = re.compile(r"^(?P<study>[A-Za-z0-9]+)_ECG_(?:(?P<cohort>[A-Za-z0-9]+)_)?VISIT(?P<visit>\d+)_(?P<year>\d{4})\d{4}"
                      r"_\d+\.xml$", re.I)
LOWCARD = 15
DOC_MAX_ROWS = 3000  # a data dictionary / codebook sheet; larger 'DD_*' files are data
# XML leaf tags whose values are technical (not about the participant) and may be reported.
XML_WHITELIST = {"WaveformType", "SampleBase", "SampleExponent", "NumberofLeads", "LeadSampleCountTotal",
                 "LeadAmplitudeUnitsPerBit", "LeadAmplitudeUnits", "LeadID", "LeadSampleSize", "HighPassFilter",
                 "LowPassFilter", "ACFilter", "AcquisitionDevice", "AcquisitionSoftwareVersion", "AnalysisSoftwareVersion",
                 "MuseVersion", "SampleType", "LeadByteCountTotal", "DataType", "ECGSampleBase", "ECGSampleExponent"}
XML_YEAR_TAGS = {"AcquisitionDate"}


def mask_digits(name: str) -> str:
    return re.sub(r"\d", "#", name)


# ---------------------------------------------------------------- env
def env(roots) -> dict:
    v = {}
    try:
        import importlib.metadata as md  # Python >= 3.8
        get = md.version
    except ImportError:  # Python 3.7 (the stock BDC Data Studio image)
        import pkg_resources
        get = lambda name: pkg_resources.get_distribution(name).version  # noqa: E731
    for p in PKGS:
        try:
            v[p] = get(p)
        except Exception:  # noqa: BLE001  (not installed)
            v[p] = None
    gpu = None
    if shutil.which("nvidia-smi"):
        q = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                           capture_output=True, text=True)
        gpu = [x.strip() for x in q.stdout.splitlines() if x.strip()]
    net = {}
    import urllib.request
    for k, url in dict(github="https://github.com", pypi="https://pypi.org/simple/fastavro/",
                       gen3="https://gen3.biodatacatalyst.nhlbi.nih.gov/index/_status").items():
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=10) as r:
                net[k] = r.status
        except Exception as e:  # noqa: BLE001
            net[k] = type(e).__name__
    out = BC.out_root()
    du = shutil.disk_usage(str(out))
    mem = None
    try:
        mem = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2 ** 30, 1)
    except (ValueError, OSError):
        pass
    return dict(python=platform.python_version(), packages=v, gpu=gpu, cpus=os.cpu_count(), mem_gib=mem,
                disk_free_gib=round(du.free / 2 ** 30, 1), out_root=str(out), input_roots=[str(r) for r in roots],
                roots_exist={str(r): Path(r).exists() for r in roots}, network=net, git_sha=BC.git_sha(),
                sb_mounts=sorted(str(p) for p in Path("/sbgenomics").glob("*")) if Path("/sbgenomics").exists() else None)


# ---------------------------------------------------------------- files
def walk(roots):
    for r in roots:
        r = Path(r)
        if not r.exists():
            continue
        for dirpath, _dirs, files in os.walk(r, followlinks=True):
            for f in files:
                p = Path(dirpath) / f
                try:
                    size = p.stat().st_size
                except OSError:
                    size = None
                yield r, p, size


def iter_xml(roots):
    """(file name, loader returning bytes) for every XML file, including members of zip archives."""
    for _, p, _ in walk(roots):
        s = p.name.lower()
        if s.endswith(".xml"):
            yield p.name, p.parent.name, (lambda p=p: p.read_bytes())
        elif s.endswith(".zip"):
            try:
                with zipfile.ZipFile(p) as z:
                    names = [m for m in z.namelist() if m.lower().endswith(".xml")]
            except zipfile.BadZipFile:
                continue
            for m in names:
                yield (Path(m).name, mask_digits(p.name),
                       (lambda p=p, m=m: zipfile.ZipFile(p).read(m)))


def ext_of(p: Path) -> str:
    s = p.name.lower()
    for e in (".txt.gz", ".csv.gz", ".tsv.gz", ".tar.gz", ".sas7bdat", ".parquet", ".avro", ".xlsx"):
        if s.endswith(e):
            return e
    return p.suffix.lower() or "(none)"


def files(roots) -> dict:
    by_ext = collections.defaultdict(lambda: [0, 0])
    by_pat = collections.defaultdict(lambda: [0, 0, set()])
    ecg = collections.Counter()
    ecg_year = collections.Counter()
    for r, p, size in walk(roots):
        e = ext_of(p)
        by_ext[e][0] += 1
        by_ext[e][1] += size or 0
        rel_dir = str(p.parent.relative_to(r)) if p.parent != r else "."
        pat = mask_digits(p.name)
        key = (str(r), mask_digits(rel_dir), pat)
        by_pat[key][0] += 1
        by_pat[key][1] += size or 0
        by_pat[key][2].add(p.name)
    for name, _parent, _load in iter_xml(roots):
        m = ECG_NAME.match(name)
        if m:
            st = m["study"].upper() + (f"_{m['cohort']}" if m["cohort"] else "")
            ecg[(st, f"VISIT{m['visit']}")] += 1
            ecg_year[(st, m["year"])] += 1
    patterns = []
    for (root, d, pat), (n, sz, names) in sorted(by_pat.items()):
        row = dict(root=root, dir=d, pattern=pat, n_files=n, mb=round(sz / 2 ** 20, 1))
        if n <= 20 and not pat.lower().endswith(".xml"):
            row["names"] = sorted(names)  # documentation / table names (no per-participant series)
        patterns.append(row)
    return dict(
        by_extension={k: dict(n_files=v[0], gb=round(v[1] / 2 ** 30, 3)) for k, v in sorted(by_ext.items())},
        patterns=patterns,
        # XML in plain files and inside zips; a study imported both ways is counted twice
        ecg_xml_by_visit=[dict(study=s, visit=v, n_files=BC.suppress(n)) for (s, v), n in sorted(ecg.items())],
        ecg_xml_by_year=[dict(study=s, year=y, n_files=BC.suppress(n)) for (s, y), n in sorted(ecg_year.items())],
    )


# ---------------------------------------------------------------- tables
def _read_bytes_table(name: str, data: bytes):
    """DataFrame from a tabular file's bytes (name decides the reader)."""
    s = name.lower()
    if s.endswith(".gz"):
        data = gzip.decompress(data)
        s = s[:-3]
    bio = io.BytesIO(data)
    if s.endswith(".sas7bdat"):
        return pd.read_sas(bio, format="sas7bdat", encoding="latin-1")
    if s.endswith(".xpt"):
        return pd.read_sas(bio, format="xport", encoding="latin-1")
    if s.endswith(".parquet"):
        return pd.read_parquet(bio)
    if s.endswith(".dta"):
        return pd.read_stata(bio)
    if s.endswith((".xlsx", ".xls")):
        return pd.read_excel(bio, sheet_name=None)  # dict of sheets
    head = data[:20000].decode("latin-1", "replace")
    lines = [ln for ln in head.splitlines() if ln.strip() and not ln.startswith("#")]
    first = lines[0] if lines else ""
    sep = "\t" if first.count("\t") >= max(1, first.count(",")) else ","
    return pd.read_csv(bio, sep=sep, comment="#" if head.startswith("#") else None, low_memory=False,
                       encoding="latin-1")


def summarise_frame(D: pd.DataFrame) -> dict:
    cols = []
    id_cols = []
    for c in D.columns:
        x = D[c]
        nn = int(x.notna().sum())
        try:
            nu = int(x.nunique(dropna=True))
        except TypeError:
            nu = None
        row = dict(column=str(c), dtype=str(x.dtype), nonmissing_frac=round(nn / len(D), 3) if len(D) else None,
                   n_unique=(nu if nu is not None and nu <= LOWCARD else (f">{LOWCARD}" if nu is not None else None)))
        if ID_HINT.search(str(c)):
            id_cols.append(dict(column=str(c), n_unique=BC.round_count(nu or 0, 10)))
            row["id_like"] = True
        elif nu is not None and 0 < nu <= LOWCARD:
            vc = x.value_counts(dropna=True)
            # labels of categories with 1-10 participants are not written (a rare free-text value can identify);
            # only how many such categories exist
            row["values"] = {str(k)[:40]: int(v) for k, v in vc.items() if v > BC.MIN_COUNT}
            rare = int(((vc >= 1) & (vc <= BC.MIN_COUNT)).sum())
            if rare:
                row["values"]["(categories with 1-10)"] = rare
        elif pd.api.types.is_numeric_dtype(x) and nn > 50:
            q = np.nanpercentile(pd.to_numeric(x, errors="coerce").to_numpy(dtype=float), [5, 50, 95])
            row["p5_p50_p95"] = [float(f"{v:.4g}") for v in q]
        cols.append(row)
    return dict(n_rows=BC.round_count(len(D), 10), n_cols=int(D.shape[1]), id_columns=id_cols, columns=cols)


# BDC/BioLINCC cloning artifacts (Ledger copies of the SAS tables, ETL bookkeeping), not study tables
ARTIFACT = re.compile(r"^(sprint_a_\d|accord_a_\d|clones_|filter_|inflight_|join_|ensemble_)", re.I)


def _iter_tabular(roots, max_mb):
    """(display name, reader callable) for every tabular file, including archive members. Skips BDC cloning
    artifacts and any .sas7bdat whose same-stem .csv sits in the same folder (BioLINCC ships both)."""
    for r, p, size in walk(roots):
        s = p.name.lower()
        rel = str(p.relative_to(r))
        if ARTIFACT.match(p.name):
            continue
        if s.endswith(".sas7bdat") and (any(p.parent.glob(p.stem + ".csv")) or any(
                (p.parent / "CSV").glob(p.stem + ".csv"))):
            continue
        if size is not None and size > max_mb * 2 ** 20:
            yield rel, None, f"skipped: {round(size / 2 ** 20)} MB > --max-table-mb"
            continue
        if s.endswith(TABULAR) or s.endswith(tuple(e + ".gz" for e in (".csv", ".tsv", ".txt"))):
            yield rel, (lambda p=p: _read_bytes_table(p.name, p.read_bytes())), None
        elif s.endswith(".zip"):
            try:
                with zipfile.ZipFile(p) as z:
                    for m in z.namelist():
                        ml = m.lower()
                        if ml.endswith(".xml") and "ecg" in ml:
                            continue
                        if ml.endswith(TABULAR) or ml.endswith((".csv.gz", ".txt.gz")):
                            yield f"{rel}::{m}", (lambda p=p, m=m: _read_bytes_table(m, zipfile.ZipFile(p).read(m))), None
            except zipfile.BadZipFile as e:
                yield rel, None, f"bad zip: {e}"
        elif s.endswith((".tar", ".tar.gz", ".tgz")):
            try:
                with tarfile.open(p) as t:
                    for m in t.getmembers():
                        ml = m.name.lower()
                        if m.isfile() and (ml.endswith(TABULAR) or ml.endswith((".csv.gz", ".txt.gz"))):
                            yield (f"{rel}::{m.name}",
                                   (lambda p=p, n=m.name: _read_bytes_table(n, tarfile.open(p).extractfile(n).read())),
                                   None)
            except tarfile.TarError as e:
                yield rel, None, f"bad tar: {e}"


def tables(roots, out: Path, max_mb: int) -> dict:
    res = []
    docs = out / "docs_extract"
    for name, reader, err in _iter_tabular(roots, max_mb):
        base = name.split("::")[-1]
        if base.lower().endswith(".xml"):
            continue
        rec = dict(table=name)
        if reader is None:
            rec["error"] = err
            res.append(rec)
            continue
        t0 = time.time()
        try:
            D = reader()
        except Exception as e:  # noqa: BLE001
            rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            res.append(rec)
            BC.log(f"tables: {name}: {rec['error']}")
            continue
        frames = D if isinstance(D, dict) else {"": D}
        rec["sheets"] = {}
        rec["documentation"] = False
        for sheet, F in frames.items():
            # Copied verbatim only if it looks like documentation AND is small AND has no ID-like column: the imaging
            # 'DD_*' files can be per-file tables carrying subject IDs, which must only be summarised.
            is_doc = bool(DOC_HINT.search(base)) and len(F) <= DOC_MAX_ROWS and not any(
                ID_HINT.search(str(c)) for c in F.columns)
            if is_doc:
                rec["sheets"][str(sheet)] = dict(n_rows=len(F), n_cols=F.shape[1], columns=[str(c) for c in F.columns],
                                                 documentation=True)
                docs.mkdir(parents=True, exist_ok=True)
                safe = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{name}__{sheet}")[:180]
                F.to_csv(docs / f"{safe}.tsv", sep="\t", index=False)
                rec["documentation"] = True
            else:
                rec["sheets"][str(sheet)] = summarise_frame(F)
        rec["seconds"] = round(time.time() - t0, 1)
        res.append(rec)
        BC.log(f"tables: {name} ({'doc' if rec['documentation'] else 'data'}) {rec['seconds']} s")
    return dict(tables=res)


# ---------------------------------------------------------------- xml
def _xml_one(data: bytes) -> dict:
    root = ET.fromstring(data)
    paths = collections.Counter()
    values = collections.defaultdict(collections.Counter)
    years = collections.Counter()

    def visit(el, prefix):
        tag = el.tag.split("}")[-1]
        pth = f"{prefix}/{tag}"
        paths[re.sub(r"\[\d+\]", "", pth)] += 1
        txt = (el.text or "").strip()
        if tag in XML_WHITELIST and txt:
            values[tag][txt[:40]] += 1
        if tag in XML_YEAR_TAGS and txt:
            m = re.search(r"(18|19|20)\d\d", txt)
            years[m.group(0) if m else "unparsed"] += 1
        for ch in el:
            visit(ch, pth)

    visit(root, "")
    # GE MUSE waveform decode check
    waves = []
    for w in root.iter():
        if w.tag.split("}")[-1] != "Waveform":
            continue
        wt = (w.findtext("WaveformType") or "").strip()
        fs = (w.findtext("SampleBase") or "").strip()
        leads = []
        for ld in w.iter():
            if ld.tag.split("}")[-1] != "LeadData":
                continue
            raw = ld.findtext("WaveFormData")
            upb = ld.findtext("LeadAmplitudeUnitsPerBit")
            n_decl = ld.findtext("LeadSampleCountTotal")
            info = dict(lead=(ld.findtext("LeadID") or "").strip())
            if raw:
                try:
                    a = np.frombuffer(base64.b64decode(raw), dtype="<i2").astype(float)
                    a = a * float(upb or 1)
                    info.update(n=len(a), n_decl=int(n_decl) if n_decl else None,
                                p99abs=float(np.percentile(np.abs(a - np.median(a)), 99)) if len(a) else None,
                                flat=bool(len(a) and np.ptp(a) == 0))
                except Exception as e:  # noqa: BLE001
                    info["decode_error"] = type(e).__name__
            leads.append(info)
        waves.append(dict(type=wt, fs=fs, leads=leads))
    return dict(root=root.tag.split("}")[-1], paths=paths, values=values, years=years, waves=waves)


def xml(roots, n_sample: int, seed: int) -> dict:
    series = collections.defaultdict(list)
    for name, parent, load in iter_xml(roots):
        m = ECG_NAME.match(name)
        key = (m["study"].upper() + (f"_{m['cohort']}" if m["cohort"] else "")) if m else mask_digits(parent)
        series[key].append(load)
    rng = random.Random(seed)
    out = {}
    for key, ps in sorted(series.items()):
        sample = rng.sample(ps, min(n_sample, len(ps)))
        roots_c, paths, values, years = collections.Counter(), collections.Counter(), collections.defaultdict(
            collections.Counter), collections.Counter()
        wave_summ = collections.defaultdict(lambda: dict(files=0, n_leads=collections.Counter(), n_samples=collections.Counter(),
                                                         count_match=0, flat_leads=0, decode_errors=0, p99abs=[]))
        errors = collections.Counter()
        for load in sample:
            try:
                d = _xml_one(load())
            except Exception as e:  # noqa: BLE001
                errors[type(e).__name__] += 1
                continue
            roots_c[d["root"]] += 1
            for k in d["paths"]:
                paths[k] += 1  # files containing the path
            for t, c in d["values"].items():
                for v in c:
                    values[t][v] += 1  # files with this value
            years.update(d["years"])
            for w in d["waves"]:
                s = wave_summ[w["type"] or "(none)"]
                s["files"] += 1
                s["n_leads"][len(w["leads"])] += 1
                for ld in w["leads"]:
                    if "n" in ld:
                        s["n_samples"][ld["n"]] += 1
                        s["count_match"] += int(ld["n_decl"] is None or ld["n_decl"] == ld["n"])
                        s["flat_leads"] += int(ld["flat"])
                        if ld["p99abs"] is not None:
                            s["p99abs"].append(ld["p99abs"])
                    if "decode_error" in ld:
                        s["decode_errors"] += 1
        waves = {}
        for t, s in wave_summ.items():
            q = np.percentile(s["p99abs"], [10, 50, 90]).round(1).tolist() if s["p99abs"] else None
            waves[t] = dict(files=s["files"], n_leads=dict(s["n_leads"]), n_samples_per_lead=dict(s["n_samples"]),
                            sample_count_matches_declared=s["count_match"], flat_leads=s["flat_leads"],
                            decode_errors=s["decode_errors"], lead_p99abs_amplitude_p10_p50_p90=q)
        out[key] = dict(n_files_total=BC.suppress(len(ps)), n_sampled=len(sample), parse_errors=dict(errors),
                        root_tags=dict(roots_c), tag_paths_files=dict(sorted(paths.items())),
                        whitelisted_values_files={t: dict(c.most_common(30)) for t, c in values.items()},
                        acquisition_years=dict(sorted(years.items())), waveforms=waves)
        BC.log(f"xml: {key}: sampled {len(sample)} of {len(ps)}")
    return out


# ---------------------------------------------------------------- pfb
def pfb(roots) -> dict:
    found = [p for _, p, _ in walk(roots) if p.name.lower().endswith((".avro", ".pfb"))]
    if not found:
        return dict(files=0)
    try:
        import fastavro
    except ImportError:
        return dict(files=len(found), error="fastavro not installed: pip install fastavro")
    res = []
    for p in found:
        ents = collections.Counter()
        fields = collections.defaultdict(set)
        try:
            with open(p, "rb") as f:
                for rec in fastavro.reader(f):
                    name = rec.get("name", "?")
                    ents[name] += 1
                    obj = rec.get("object")
                    if isinstance(obj, dict):
                        fields[name].update(k for k, v in obj.items() if v is not None)
        except Exception as e:  # noqa: BLE001
            res.append(dict(file=mask_digits(p.name), error=f"{type(e).__name__}: {str(e)[:200]}"))
            continue
        res.append(dict(file=mask_digits(p.name), entities={k: BC.round_count(v, 10) for k, v in ents.items()},
                        fields={k: sorted(v) for k, v in fields.items()}))
    return dict(files=len(found), pfb=res)


# ---------------------------------------------------------------- report
def write_md(R: dict, path: Path) -> None:
    L = [f"# BDC probe ({R['when']}, git {R.get('env', {}).get('git_sha', '')[:10]})", ""]
    if "env" in R:
        e = R["env"]
        L += ["## Environment", f"- Python {e['python']}; CPUs {e['cpus']}; memory {e['mem_gib']} GiB; free disk "
              f"{e['disk_free_gib']} GiB; GPU {e['gpu']}", f"- input roots {e['roots_exist']}; out {e['out_root']}",
              f"- network {e['network']}; /sbgenomics: {e['sb_mounts']}",
              "- packages: " + ", ".join(f"{k} {v}" for k, v in e["packages"].items()), ""]
    if "files" in R:
        F = R["files"]
        L += ["## Files", "| extension | files | GB |", "|---|---|---|"]
        L += [f"| {k} | {v['n_files']} | {v['gb']} |" for k, v in F["by_extension"].items()]
        L += ["", "| dir | name pattern | files | MB | names (non-XML, ≤20) |", "|---|---|---|---|---|"]
        L += [f"| {p['dir']} | `{p['pattern']}` | {p['n_files']} | {p['mb']} | {', '.join(p.get('names', []))[:300]} |"
              for p in F["patterns"]]
        L += ["", "ECG XML by visit label:", "", "| study | visit | files |", "|---|---|---|"]
        L += [f"| {x['study']} | {x['visit']} | {x['n_files']} |" for x in F["ecg_xml_by_visit"]]
        L += [""]
    if "tables" in R:
        L += ["## Tables", "| table | sheet | rows | cols | ID-like columns (distinct) | note |", "|---|---|---|---|---|---|"]
        for t in R["tables"]["tables"]:
            if "error" in t:
                L.append(f"| {t['table']} | | | | | ERROR {t['error']} |")
                continue
            for s, v in t["sheets"].items():
                ids = "; ".join(f"{i['column']} ({i['n_unique']})" for i in v.get("id_columns", []))
                L.append(f"| {t['table']} | {s} | {v['n_rows']} | {v['n_cols']} | {ids} | "
                         f"{'documentation (copied)' if v.get('documentation') else ''} |")
        L += ["", "Column-level detail: probe_columns.tsv and probe.json.", ""]
    if "xml" in R:
        L += ["## ECG XML sample"]
        for k, v in R["xml"].items():
            L += [f"### {k}: {v['n_files_total']} files, {v['n_sampled']} sampled; roots {v['root_tags']}; "
                  f"parse errors {v['parse_errors']}"]
            for t, w in v["waveforms"].items():
                L.append(f"- waveform {t}: {w}")
            for t, c in v["whitelisted_values_files"].items():
                L.append(f"- {t}: {c}")
            L.append(f"- acquisition years: {v['acquisition_years']}")
            L.append("")
    if "pfb" in R:
        L += ["## PFB", "```", json.dumps(R["pfb"], indent=1)[:6000], "```", ""]
    L += ["## Errors", "```", json.dumps(R.get("errors", {}), indent=1)[:6000], "```"]
    path.write_text("\n".join(L))


def write_columns(R: dict, path: Path) -> None:
    rows = []
    for t in R.get("tables", {}).get("tables", []):
        for s, v in t.get("sheets", {}).items():
            if v.get("documentation"):
                continue
            for c in v.get("columns", []):
                rows.append(dict(table=t["table"], sheet=s, column=c["column"], dtype=c["dtype"],
                                 nonmissing_frac=c["nonmissing_frac"], n_unique=c["n_unique"],
                                 values=json.dumps(c.get("values")) if c.get("values") else "",
                                 p5_p50_p95=json.dumps(c.get("p5_p50_p95")) if c.get("p5_p50_p95") else ""))
    pd.DataFrame(rows).to_csv(path, sep="\t", index=False)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--roots", nargs="+", default=[r for r in BC.SB_INPUT_ROOTS if Path(r).exists()] or ["."])
    ap.add_argument("--only", default=",".join(SECTIONS))
    ap.add_argument("--xml-sample", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20261014)
    ap.add_argument("--max-table-mb", type=int, default=4000)
    a = ap.parse_args(argv)
    only = [s.strip() for s in a.only.split(",") if s.strip()]
    bad = [s for s in only if s not in SECTIONS]
    if bad:
        sys.exit(f"unknown sections {bad}; choose from {SECTIONS}")
    out = BC.out_root() / "probe"
    out.mkdir(parents=True, exist_ok=True)
    R = dict(when=time.strftime("%Y-%m-%d %H:%M %Z"), args=vars(a), errors={})
    for s in only:
        BC.log(f"section {s} ...")
        t0 = time.time()
        try:
            if s == "env":
                R[s] = env(a.roots)
            elif s == "files":
                R[s] = files(a.roots)
            elif s == "tables":
                R[s] = tables(a.roots, out, a.max_table_mb)
            elif s == "xml":
                R[s] = xml(a.roots, a.xml_sample, a.seed)
            elif s == "pfb":
                R[s] = pfb(a.roots)
        except Exception as e:  # noqa: BLE001
            R["errors"][s] = f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}"
            BC.log(f"section {s} FAILED: {type(e).__name__}: {e}")
        BC.log(f"section {s} done in {time.time() - t0:.0f} s")
        BC.write_json(out / "probe.json", R)
    write_md(R, out / "probe.md")
    write_columns(R, out / "probe_columns.tsv")
    BC.log(f"wrote {out}/probe.md, probe.json, probe_columns.tsv (review before sharing)")


if __name__ == "__main__":
    main()
