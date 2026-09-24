"""Pool long-tail v2 runs: mean and [min, max] over imputations x splits per method.

B_frac_chance: expected share of features with |SMD| > 0.1 from chance alone in a
randomised 1:1 sample of the same number of pairs (SMD ~ N(0, 2/pairs)):
2 * (1 - Phi(0.1 * sqrt(pairs / 2))). B_frac_excess = observed - chance. Methods that
trim more pairs have a higher chance floor, so compare excess as well as raw share.
"""
import glob
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

out = sys.argv[1]
d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{out}/longtail_imp*_seed*.csv"))])
d["B_frac_chance"] = 2 * (1 - norm.cdf(0.1 * np.sqrt(d.pairs / 2)))
d["B_frac_excess"] = d.B_frac_gt_0_1 - d.B_frac_chance
num = d.drop(columns=["imputation", "split_seed"]).groupby("method", sort=False)
mean, lo, hi = num.mean(), num.min(), num.max()
mean["runs"] = num.size()
mean["B_frac_min"], mean["B_frac_max"] = lo.B_frac_gt_0_1, hi.B_frac_gt_0_1
mean.to_csv(f"{out}/summary_pooled.csv")
cols = [c for c in ["runs", "pairs", "B_frac_gt_0_1", "B_frac_min", "B_frac_max", "B_frac_chance", "B_frac_excess", "B_mean", "core_max", "core_n_gt_0_1",
                    "smd_lvef", "smd_obs_lvef", "smd_prog_core", "smd_prog_full", "cstat_core", "cstat_core_poolB"] if c in mean]
pd.set_option("display.width", 250)
print(mean[cols].round(3).to_string())
