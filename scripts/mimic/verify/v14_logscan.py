"""Verifier round 2: does any text file under the restricted output tree (logs, STATUS.md) hold a database / CSV error
message that could quote a raw source row? Prints file names and match COUNTS only (never the matching text)."""
import os
import re

OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
PAT = re.compile(r"(CSV Error|Conversion Error|InvalidInputException|Original Line|Error when sniffing|prescriptions\.csv\.gz.*line)", re.I)
ROWLIKE = re.compile(r"\b1\d{7}\b.*\b2\d{7}\b")  # an 8-digit subject_id-like and hadm_id-like number on one line
for root, _, files in os.walk(OUT):
    if "/verify" in root or "/data" in root:
        continue
    for f in files:
        if not f.endswith((".md", ".log", ".txt", ".sh", ".json", ".err", ".out")):
            continue
        p = os.path.join(root, f)
        try:
            n_pat = n_row = 0
            with open(p, errors="replace") as fh:
                for line in fh:
                    n_pat += bool(PAT.search(line))
                    n_row += bool(ROWLIKE.search(line))
        except Exception as e:
            print(p[len(OUT):], "unreadable", type(e).__name__)
            continue
        if n_pat or n_row:
            print(p[len(OUT):], "| error-pattern lines", n_pat, "| id-like lines", n_row)
print("scan done")
