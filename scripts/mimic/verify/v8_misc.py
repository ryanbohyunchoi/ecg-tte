"""Verifier: remaining doc claims (aggregates only): MEDS qc block, the lab LOINC map (96 items, 95 in the
dictionary, all valid standard), the literal-lab-rule in-vocabulary share, the no-NDC share."""
import json
import sys

import pandas as pd

sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/mimic")
OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
from lab_loinc_map import LAB_LOINC  # noqa: E402  (a constant table; metadata only)

S = json.load(open(f"{OUT}/meds/summary.json"))
qc = S["qc"]
print("leakage_checks:", qc["leakage_checks"])
print("rx rows without NDC share of rx rows after exposure exclusion: %.3f" % (qc["rx_rows_without_ndc"] / (qc["rx_rows_before_t0"] - qc["rx_rows_exposure_excluded"])))
print("rx rows without NDC share of all pre-t0 rx rows: %.3f" % (qc["rx_rows_without_ndc"] / qc["rx_rows_before_t0"]))
print("dx rows unmapped share: %.4f" % (qc["dx_rows_unmapped"] / (qc["dx_rows_prior_admissions"] - qc["dx_rows_gate_excluded"])))
codes = set(json.load(open(f"{OUT}/vocab/clmbr_code_strings.json"))["codes"])
print("LOINC map entries", len(LAB_LOINC), "| in dictionary", sum(("LOINC/" + c) in codes for c in LAB_LOINC.values()),
      "| not in dictionary:", [c for c in LAB_LOINC.values() if ("LOINC/" + c) not in codes])
T = pd.read_csv(f"{OUT}/vocab/lab_loinc_verified.csv")
print("verified csv rows", len(T), "| ok (valid standard LOINC)", int(T.ok.sum()), "| in_dictionary", int(T.in_dictionary.sum()))
dc = S["domain_coverage"]
tot = sum(v["events"] for v in dc.values())
iv_nonlab = sum(v["events"] * v["share_in_vocab"] for k, v in dc.items() if k != "lab")
print("literal lab rule (all labs out of vocabulary): in-vocab share %.3f" % (iv_nonlab / tot))
print("events by domain:", {k: v["events"] for k, v in dc.items()}, "total", tot)
