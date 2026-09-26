"""Fill verified all-cause mortality benchmarks (docs/v15_rct_mortality.json) into the v1.5 death-outcome
trial dirs' rct.json, in OUR arm orientation (rct.json 'arms' = [first, second]). Aggregate literature values only."""
import glob, json, sys
from pathlib import Path
M = json.load(open(Path(__file__).resolve().parents[2] / "docs" / "v15_rct_mortality.json"))
# RCT orientation (first arm) and our first arm, per trial key; invert when our first arm is the RCT's second arm
RCT_FIRST = {"plato": "ticagrelor", "aristotle": "apixaban", "rocket_af": "rivaroxaban", "transform_hf": "torsemide",
             "comet": "carvedilol", "ontarget": "arb", "allhat": "amlodipine", "ascot": "amlodipine"}
for d in sorted(glob.glob("/mnt/raid0/rbc58/ecg-tte/audits/claude-v15d-*-death")):
    f = Path(d) / "rct.json"
    r = json.load(open(f))
    key = next(k for k in RCT_FIRST if f"-{k.replace('_', '_')}-" in d + "-" or d.split("-")[-2] == k or k in d.replace("-", "_"))
    b = M[key]
    first = r["arms"][0].lower()
    same = RCT_FIRST[key] in first
    hr, lo, hi = b["hr"], b["lo"], b["hi"]
    r.update(hr=hr, lo=lo, hi=hi, ci_level=b.get("ci_level", 0.95), benchmark_source=b.get("source_url"), benchmark_measure=b.get("measure"),
             benchmark_pending=False, our_orientation=hr if same else round(1 / hr, 4),
             our_lo=lo if same else round(1 / hi, 4), our_hi=hi if same else round(1 / lo, 4), endpoint="all-cause death")
    json.dump(r, open(f, "w"), indent=2)
    print(d.split("/")[-1], key, r["arms"], "same orientation" if same else "INVERTED", r["our_orientation"], r["our_lo"], r["our_hi"], r["ci_level"])
