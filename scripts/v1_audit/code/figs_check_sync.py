"""v1 audit: re-run make_paper2_figures data extraction with save() disabled (no writes to docs/), compare CHECK with
docs/paper/figures_paper2/check_values.json; also unpaired vs paired agreement means used by Figure 5B."""
import json, sys, importlib.util, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
P = "/home/rbc58/github/ecg-tte/scripts/v21/make_paper2_figures.py"
spec = importlib.util.spec_from_file_location("mpf", P); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
M.save = lambda fig, path: plt.close(fig)
M.spot_checks()
for f in (M.figure1, M.figure2, M.figure3, M.figure4, M.figure5, M.efigure1, M.efigure2, M.efigure3, M.efigure4, M.efigure5):
    f()
new = json.loads(json.dumps(M.CHECK, default=str))
old = json.load(open("/home/rbc58/github/ecg-tte/docs/paper/figures_paper2/check_values.json"))
diff = [k for k in set(new) | set(old) if new.get(k) != old.get(k)]
print("CHECK keys", len(new), "differences vs committed check_values.json:", len(diff), diff[:10])
S = M.SENS
s = S[(S.set == "S32") & S.contrast.str.match(r"^P5: .* vs base$")]
d = (s.absd_a - s.absd_a_pair).abs() + (s.absd_b - s.absd_b_pair).abs()
print("P5 'vs base' rows where unpaired absd != paired:", int((d > 1e-12).sum()), "of", len(s))
if (d > 1e-12).any():
    print(s.loc[d > 1e-12, ["config", "contrast", "absd_b", "absd_a", "absd_b_pair", "absd_a_pair", "n_agree_pair", "absd_better"]].round(4).to_string(index=False))
a = S[S.set == "S32"]; d = (a.absd_a - a.absd_a_pair).abs() + (a.absd_b - a.absd_b_pair).abs()
print("all S32 rows unpaired!=paired:", int((d > 1e-9).sum()), sorted(a.loc[d > 1e-9, "contrast"].unique())[:12])
print("Fig2B base spread across arms (max-min m54_b per rung):")
for rg, _ in M.RUNGS:
    v = [M.S("S32", "main", f"{rg}: {x} vs base").m54_b for x in ("ECG", "CLMBR", "ECG+CLMBR")]
    print("  ", rg, round(max(v) - min(v), 5))
