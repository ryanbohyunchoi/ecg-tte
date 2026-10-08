#!/usr/bin/env python
"""Privacy scan of the non-restricted spec-v2 outputs (OUT/**/*.csv, *.json, *.md), docs/v2_cohorts/COHORT_FIXES.md and
scripts/v2_cohorts/*. Checks: identifier columns / values (analysed patient_key and person_id tokens); counts 1-10 in
count-like columns; formatted counts 1-10; small integers next to patient/event nouns in the markdown; count-derived columns
left in suppressed rows; parquet files without the restricted_ prefix. Writes OUT/privacy_scan.json; prints a summary only."""
import glob
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2common as K  # noqa: E402

import pandas as pd  # noqa: E402

bad = []
keys = set()
for f in glob.glob(str(K.CRIT / "keys" / "restricted_keys_*.parquet")):
    D = pd.read_parquet(f, columns=["patient_key", "person_id"])
    keys |= set(D.patient_key.astype(str)) | set(D.person_id.astype(str))
keys = {k for k in keys if len(k) >= 5}
COUNTLIKE = re.compile(r"^(n|k|n_t|n_c|n_pairs|n_ok|n_.*|k_.*|events.*|removed.*|retained|n_retained.*|n_analysed)$")
NOTCOUNT = {"n_trials", "n_rules", "n_items", "n_contrasts", "n_agree_pair", "n_trials_failed", "n_ref", "n_clusters",
            "n_flags", "n_yes", "n_no"}
files = sorted(glob.glob(str(K.OUT / "**" / "*.csv"), recursive=True))
for f in files:
    D = pd.read_csv(f, dtype=str, low_memory=False)
    for c in D.columns:
        if re.search(r"patient_key|person_id|mrn", c, re.I):
            bad.append((f, f"identifier column {c}"))
        vals = D[c].dropna().astype(str)
        if vals.isin(keys).any() and not COUNTLIKE.match(c):  # aggregate counts can coincide with short identifiers
            bad.append((f, f"value matching an analysed identifier in column {c}"))
        if COUNTLIKE.match(c) and c not in NOTCOUNT and not c.endswith(("_p", "_q")):
            v = pd.to_numeric(vals, errors="coerce")
            if ((v >= 1) & (v <= 10) & (v == v.round())).any():
                bad.append((f, f"count 1-10 in column {c}"))
        if vals.str.match(r"^\s*([1-9]|10) \(").any():
            bad.append((f, f"formatted count 1-10 in column {c}"))
    if "suppressed_lt11" in D:
        s = D.suppressed_lt11.astype(str).str.lower().eq("true")
        for c in ("ess_t", "ess_c", "retain"):
            if c in D and D.loc[s, c].notna().any():
                bad.append((f, f"count-derived column {c} in suppressed rows"))
NOUN = r"(patients?|persons?|people|events?|orders?|records?|ECGs|deaths?|pairs)"
texts = [Path(x) for x in glob.glob(str(K.OUT / "**" / "*.md"), recursive=True)]
texts += [Path(x) for x in glob.glob(str(K.OUT / "**" / "*.json"), recursive=True)]
doc = K.ROOT / "docs" / "v2_cohorts" / "COHORT_FIXES.md"
if doc.exists():
    texts.append(doc)
for p in texts:
    t = p.read_text()
    if p.suffix == ".md":
        for m in re.finditer(rf"(?<![\d.,<>~−-])\b([1-9]|10)\b(?![.,]\d|%|–|-|:)\s+(?:\w+\s+){{0,2}}{NOUN}", t):
            bad.append((str(p), f"possible small count: '{t[max(0, m.start() - 25):m.end() + 5]}'"))
    if set(re.findall(r"[A-Za-z0-9]{5,}", t)) & keys:
        bad.append((str(p), "identifier token present"))
for f in glob.glob(str(K.ROOT / "scripts" / "v2_cohorts" / "*")):
    if Path(f).is_file() and set(re.findall(r"[A-Za-z0-9]{5,}", Path(f).read_text(errors="ignore"))) & keys:
        bad.append((f, "identifier token in code"))
for f in glob.glob(str(K.OUT / "**" / "*"), recursive=True):
    p = Path(f)
    if p.is_file() and p.suffix == ".parquet" and not p.name.startswith("restricted_"):
        bad.append((f, "parquet without restricted_ prefix"))
out = dict(clean=not bad, files_csv=len(files), texts=len(texts), issues=bad, time=time.strftime("%Y-%m-%d %H:%M"))
(K.OUT / "privacy_scan.json").write_text(json.dumps(out, indent=1))
print("csv scanned:", len(files), "texts:", len(texts))
print("PASS" if not bad else "FINDINGS:")
for b in bad:
    print(" ", b)
