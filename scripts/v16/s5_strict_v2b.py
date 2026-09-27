"""S5 strict NCO set re-run with the v2b cautions (AUDIT_V16_ROUND2 §3): summary-only on the saved
claude-v16-s5-nco/nco_estimates.csv (the NCO Cox fits do not change; only the strict-set membership does)."""
import os, sys
os.umask(0o077)
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts/v16"); sys.path.insert(0, "/home/rbc58/github/ecg-tte/scripts")
import s5_nco as S
OLD = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s5-nco"); OUT = Path("/mnt/raid0/rbc58/ecg-tte/audits/claude-v16-s5-nco-v2b")
N = pd.read_csv(OLD / "nco_estimates.csv")
cells = [c for c, _ in S.RUNGS]
M = S.nco_set(N, "strict")
PT = S.per_trial_metrics(M)
C = S.contrasts(PT, cells)
C.to_csv(OUT / "contrasts_strict_v2b.csv", index=False)
PT.to_csv(OUT / "per_trial_nco_metrics_strict_v2b.csv", index=False)
old = pd.read_csv(OLD / "contrasts_strict.csv")
k = ["half", "cell", "a", "b", "metric"]
J = old.merge(C, on=k, suffixes=("_v2", "_v2b"))
J = J[(J.half == "full") & (J.a == "ECG") & (J.b == "base")]
cols = ["cell", "metric", "d_v2", "p_v2", "q_bh_family_v2", "d_v2b", "k_v2b", "p_v2b", "q_bh_v2b", "q_bh_family_v2b", "p_cluster_v2b"]
J[cols].to_csv(OUT / "strict_v2_vs_v2b.csv", index=False)
ninc_old = S.nco_set(N[N.half == "full"], "main").groupby("trial").nco.nunique()
ninc = M[M.half == "full"].groupby("trial").nco.nunique()
print(pd.DataFrame({"main": ninc_old, "strict_v2b": ninc}).T.to_string())
pd.set_option("display.width", 250)
print(J[cols].round(4).to_string(index=False))
