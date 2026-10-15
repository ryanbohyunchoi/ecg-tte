"""Verifier: independent export of the CLMBR-T dictionary code strings (mosaic env, msgpack) and comparison with the
builder's OUT/vocab/clmbr_code_strings.json (aggregate counts only)."""
import hashlib
import json
import msgpack

MODEL = "/mnt/raid0/eo287/clmbr/dictionary.msgpack"
OUT = "/mnt/raid0/rbc58/ecg-tte/audits/claude-mimic-clmbr-20261014"
raw = open(MODEL, "rb").read()
d = msgpack.unpackb(raw, raw=False, strict_map_key=False)
print("top-level keys:", list(d.keys()) if isinstance(d, dict) else type(d))
voc = d["vocab"] if isinstance(d, dict) else d
types = {}
codes = set()
for e in voc:
    t = e.get("type")
    types[t] = types.get(t, 0) + 1
    if t == "code":
        codes.add(e["code_string"])
print("entry types:", types)
J = json.load(open(f"{OUT}/vocab/clmbr_code_strings.json"))
print("json dictionary_sha256 == file sha256:", J["dictionary_sha256"] == hashlib.sha256(raw).hexdigest())
jc = set(J["codes"])
print("own code-type strings", len(codes), "| json", len(jc), "| equal", codes == jc)
for pfx in ("LOINC/", "SNOMED/", "RxNorm/", "RxNorm Extension/", "ICD9Proc/", "ICD10PCS/", "ICD10CM/", "ICD9CM/", "Visit/", "MIMIC_LAB/", "NDC/"):
    print(f"  {pfx}: {sum(c.startswith(pfx) for c in codes)}")
print("Visit codes:", sorted(c for c in codes if c.startswith("Visit/")))
