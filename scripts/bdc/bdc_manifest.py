#!/usr/bin/env python
"""Build Seven Bridges DRS import manifests from the PUBLIC BDC Gen3 index (file metadata only; no login, no data).

Runs anywhere with internet (this server, or a Data Studio with project network access on). For each study it
lists the latest release of every indexed object and writes TSV manifests (columns drs_uri, name, plus metadata)
for the Seven Bridges "Add files > GA4GH DRS > manifest" import:

  m0_docs_<study>.tsv      every non-XML object of the ECG imaging project (data dictionary, readme, QC pdfs, PFB,
                           subject-ID key; not the WHI visit zips) and every object of the clinical (BioLINCC /
                           dbGaP) project except BDC's Ledger/ cloning inventories
  m1_probe_<study>.tsv     a fixed random sample of 50 ECG XML (baseline-period) for bdc_probe.py
  m2_baseline_<study>.tsv  the ECG XML in the baseline window (Figure 5 needs baseline ECGs only):
                           SPRINT file years 2010-2013, ACCORD 2001-2005, WHI the Visit1 zip

Old releases are dropped: when the same file path exists in several buckets (e.g. -r2 and -r3), only the most
recently created object is kept. ECG file names carry a file serial, not a participant ID (public index).

Usage: python -I scripts/bdc/bdc_manifest.py [--out docs/bdc/manifests] [--studies SPRINT ACCORD WHI]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

INDEX = "https://gen3.biodatacatalyst.nhlbi.nih.gov/index/index"
HOST = "gen3.biodatacatalyst.nhlbi.nih.gov"
# study -> (imaging ACLs, clinical ACLs, baseline rule)
STUDIES = {
    "SPRINT": (["phs003566.c1"], ["phs003483.c1"], dict(years=range(2010, 2014))),
    "ACCORD": (["phs003562.c1"], ["phs003551.c1"], dict(years=range(2001, 2006))),
    "WHI": (["phs003824.c1", "phs003824.c2"], ["phs000200.c1", "phs000200.c2"], dict(zip_visit="visit1")),
}
ECG = re.compile(r"_ECG_(?:[A-Za-z0-9]+_)?VISIT(\d+)_(\d{4})\d{4}_\d+\.xml$", re.I)


def fetch_acl(acl: str) -> list:
    """All index records for one ACL, paged by 'start' (= last did); de-duplicated by did."""
    out, seen, start = [], set(), None
    while True:
        q = dict(acl=acl, limit=1024)
        if start:
            q["start"] = start
        url = f"{INDEX}?{urllib.parse.urlencode(q)}"
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    recs = json.loads(r.read().decode())["records"]
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 4:
                    raise
                print(f"  retry {acl} ({type(e).__name__})", file=sys.stderr)
                time.sleep(5 * (attempt + 1))
        new = [r for r in recs if r["did"] not in seen]
        if not new:
            break
        for r in new:
            seen.add(r["did"])
        out += new
        start = recs[-1]["did"]
        if len(recs) < 1024:
            break
    return out


def path_of(rec: dict) -> str:
    """Object path within its bucket (prefers the gs:// or s3:// URL; bucket dropped)."""
    for u in rec.get("urls") or []:
        m = re.match(r"^(?:gs|s3)://[^/]+/(.+)$", u)
        if m:
            return m.group(1)
    return rec.get("file_name") or rec["did"]


def latest(records: list) -> list:
    """Keep the most recently created object per (consent ACL, file path): drops superseded releases, keeps consent
    groups apart (WHI c1 and c2 both have Data/Visit1/visit1.zip)."""
    best = {}
    for r in records:
        acl = ",".join(sorted(a for a in (r.get("acl") or []) if a != "admin"))
        k = (acl, path_of(r).lower())
        if k not in best or (r.get("created_date") or "") > (best[k].get("created_date") or ""):
            best[k] = r
    return list(best.values())


def row(rec: dict, study: str, kind: str) -> dict:
    p = path_of(rec)
    did = rec["did"]
    # drs_uri: the compact form Gen3 reports as each object's DRS self_uri; host form kept as a fallback
    return dict(drs_uri=f"drs://dg.4503:{did.split('/', 1)[-1]}", name=Path(p).name, folder=f"{study}/{str(Path(p).parent)}",
                object_id=did, host_drs_uri=f"drs://{HOST}/{did}", size=rec.get("size"),
                md5=(rec.get("hashes") or {}).get("md5"),
                consent=",".join(a for a in (rec.get("acl") or []) if a != "admin"))


def write(path: Path, rows: list) -> None:
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "docs" / "bdc" / "manifests"))
    ap.add_argument("--studies", nargs="+", default=list(STUDIES))
    ap.add_argument("--probe-n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261014)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for st in a.studies:
        img_acls, clin_acls, rule = STUDIES[st]
        img = latest([r for acl in img_acls for r in fetch_acl(acl)])
        clin = latest([r for acl in clin_acls for r in fetch_acl(acl)])
        xml = [r for r in img if path_of(r).lower().endswith(".xml")]
        other = [r for r in img if not path_of(r).lower().endswith(".xml")]
        by_year = collections.Counter()
        base = []
        for r in xml:
            m = ECG.search(path_of(r))
            if not m:
                continue
            by_year[m.group(2)] += 1
            if "years" in rule and int(m.group(2)) in rule["years"]:
                base.append(r)
        if "zip_visit" in rule:
            base = [r for r in other if path_of(r).lower().endswith(f"{rule['zip_visit']}.zip")]
            pool = [r for r in xml if re.search(r"VISIT0?1_", path_of(r), re.I)]
        else:
            pool = base
        rng = random.Random(a.seed)
        probe = rng.sample(sorted(pool, key=lambda r: r["did"]), min(a.probe_n, len(pool)))
        docs = [row(r, st, "imaging_doc") for r in other if not path_of(r).lower().endswith(".zip")]
        # BDC 'Ledger/' folders hold platform cloning inventories and duplicate copies of the SAS tables
        docs += [row(r, st, "clinical") for r in clin if not path_of(r).startswith("Ledger/")]
        write(out / f"m0_docs_{st}.tsv", docs)
        write(out / f"m1_probe_{st}.tsv", [row(r, st, "ecg_probe") for r in probe])
        write(out / f"m2_baseline_{st}.tsv", [row(r, st, "ecg_baseline") for r in base])
        # file counts, but 1-10 suppressed like every other count in this project
        yr = {y: (n if n > 10 else "1-10") for y, n in sorted(by_year.items())}
        summary[st] = dict(imaging_objects_latest=len(img), xml=len(xml), xml_by_file_year=yr,
                           imaging_other=len(other), clinical_objects_latest=len(clin),
                           clinical_gb=round(sum(r.get("size") or 0 for r in clin) / 2 ** 30, 2),
                           m0_rows=len(docs), m1_rows=len(probe), m2_rows=len(base),
                           m2_gb=round(sum(r.get("size") or 0 for r in base) / 2 ** 30, 2))
        print(st, json.dumps(summary[st]))
    (out / "manifest_summary.json").write_text(json.dumps(dict(when=time.strftime("%Y-%m-%d %H:%M"), studies=summary),
                                                          indent=1))


if __name__ == "__main__":
    main()
