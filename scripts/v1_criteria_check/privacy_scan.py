#!/usr/bin/env python
"""Privacy scan of the non-restricted outputs of the v1 criteria check (aggregate CSVs, the report, the scripts).
Checks: (1) no identifier-like columns or values (patient_key / person_id / MRN; long digit strings matching analysed keys);
(2) no raw counts 1-10 in count-like CSV columns; (3) in the markdown, no integer 1-10 next to a patient/event noun;
(4) no restricted file outside OUT/keys, OUT/flags or a restricted_* name. Prints a pass/fail summary only."""
import glob
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v1_criteria_check")
import common as K  # noqa: E402

bad = []
keys = set()
for f in glob.glob(str(K.OUT / "keys" / "restricted_keys_*.parquet")):
    D = pd.read_parquet(f, columns=["patient_key", "person_id"])
    keys |= set(D.patient_key.astype(str)) | set(D.person_id.astype(str))
csvs = sorted(glob.glob(str(K.OUT / "*.csv")))
COUNTLIKE = re.compile(r"^(n|k|n_.*|k_.*|.*_n|statements|patients_.*|events.*|removed.*|retained|n_analysed)$")
for f in csvs:
    D = pd.read_csv(f, dtype=str)
    for c in D.columns:
        if re.search(r"patient_key|person_id|mrn", c, re.I):
            bad.append((f, f"identifier column {c}"))
        vals = D[c].dropna().astype(str)
        if vals.isin(keys).any() and not COUNTLIKE.match(c) and c not in ("n_analysed",):
            # numeric aggregates can coincide with short keys; flag only long values
            hit = vals[vals.isin(keys) & (vals.str.len() >= 6)]
            if len(hit):
                bad.append((f, f"value matching an analysed identifier in column {c}"))
        if COUNTLIKE.match(c):
            v = pd.to_numeric(vals, errors="coerce")
            if ((v >= 1) & (v <= 10) & (v == v.round())).any():
                bad.append((f, f"count 1-10 in column {c}"))
        # embedded counts in formatted strings, e.g. "7 (0.3%)"
        if vals.str.match(r"^\s*([1-9]|10) \(").any():
            bad.append((f, f"formatted count 1-10 in column {c}"))
md = Path("/home/rbc58/github/ecg-tte/docs/v1_criteria_check/TRIAL_CRITERIA_CHECK.md").read_text()
NOUN = r"(patients?|persons?|people|events?|orders?|records?|ECGs|deaths?|pairs)"
for m in re.finditer(rf"(?<![\d.,<>~−-])\b([1-9]|10)\b(?![.,]\d|%|–|-|:)\s+(?:\w+\s+){{0,2}}{NOUN}", md):
    bad.append(("TRIAL_CRITERIA_CHECK.md", f"possible small count: '{md[max(0, m.start() - 20):m.end() + 5]}'"))
# whole-token match (substring matches inside longer constants such as concept ids or seeds are not identifiers)
if set(re.findall(r"[A-Za-z0-9]{5,}", md)) & keys:
    bad.append(("TRIAL_CRITERIA_CHECK.md", "identifier token present"))
for f in glob.glob("/home/rbc58/github/ecg-tte/scripts/v1_criteria_check/*.py"):
    if set(re.findall(r"[A-Za-z0-9]{5,}", Path(f).read_text())) & keys:
        bad.append((f, "identifier token in code"))
for f in glob.glob(str(K.OUT / "**" / "*"), recursive=True):
    p = Path(f)
    if p.is_file() and p.suffix == ".parquet" and not p.name.startswith("restricted_"):
        bad.append((f, "parquet without restricted_ prefix"))
print("files scanned:", len(csvs), "csv + report + scripts")
print("PASS" if not bad else "FINDINGS:")
for b in bad:
    print(" ", b)
