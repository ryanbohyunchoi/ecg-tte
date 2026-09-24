"""Synthetic tests for the generic long-tail evaluator (v2) helpers."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import eval_longtail_balance as E  # noqa: E402
from trial_common import code_like, mrn_key, suppress  # noqa: E402
import unittest  # noqa: E402


class LongtailV2Tests(unittest.TestCase):

    def test_hdps_levels_once_sporadic_frequent(self):
        counts = pd.DataFrame({"dx_A": [0, 1, 1, 2, 4, 8], "dx_B": [0, 0, 1, 1, 1, 1]})
        lv = E.hdps_levels(counts)
        # dx_A users: 1,1,2,4,8 -> median 2, q75 4 -> three distinct levels
        assert {"dx_A__once", "dx_A__spor", "dx_A__freq"} <= set(lv.columns)
        assert lv["dx_A__freq"].tolist() == [0, 0, 0, 0, 1, 1]
        # dx_B has only count 1: sporadic/frequent identical to once -> dropped
        assert [c for c in lv.columns if c.startswith("dx_B")] == ["dx_B__once"]

    def test_hdps_levels_binary_only(self):
        counts = pd.DataFrame({"dx_A": [0, 1, 3, 9]})
        assert list(E.hdps_levels(counts, binary_only=True).columns) == ["dx_A__once"]

    def test_hdps_rank_is_exposure_only_prevalence_ratio(self):
        t = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        lv = pd.DataFrame({"strong": [1, 1, 1, 0, 0, 0, 0, 0], "null": [1, 0, 1, 0, 1, 0, 1, 0]})
        assert list(E.hdps_rank(lv, t))[0] == "strong"

    def test_ps_greedy_anchor_smaller_arm_and_caliper(self):
        rng = np.random.default_rng(0)
        t = np.r_[np.ones(50, int), np.zeros(200, int)]
        lg = np.r_[rng.normal(1, 1, 50), rng.normal(0, 1, 200)]
        mt, mc = E.ps_greedy(lg, t)
        assert len(mt) == len(mc) <= 50
        assert set(t[mt]) == {1} and set(t[mc]) == {0}
        assert len(set(mc)) == len(mc)  # without replacement
        width = 0.2 * np.sqrt((lg[t == 1].var() + lg[t == 0].var()) / 2)
        assert np.all(np.abs(lg[mt] - lg[mc]) <= width + 1e-12)
        # flipping labels makes arm 0 the anchor; result is still (treated, control)
        mt2, mc2 = E.ps_greedy(-lg, 1 - t)
        assert set((1 - t)[mt2]) == {1}

    def test_smd_vector_prematch_sd_and_nan_rules(self):
        t = np.array([1, 1, 1, 0, 0, 0])
        v = np.array([[1.0, 5.0, np.nan], [0.0, 5.0, 2.0], [1.0, 5.0, 4.0],
                      [0.0, 5.0, 1.0], [0.0, 5.0, 3.0], [0.0, 5.0, 2.0]])
        d = E.smd_vector(v, t, np.array([0, 1, 2]), np.array([3, 4, 5]))
        assert np.isclose(d[0], (2 / 3) / np.sqrt((1 / 3 + 0) / 2))
        assert np.isnan(d[1])  # constant column: undefined, not zero
        assert np.isfinite(d[2])  # NaN values ignored in means

    def test_cstat_after_matching_null_near_half(self):
        rng = np.random.default_rng(1)
        n = 2000
        X = rng.normal(size=(n, 20))
        t = rng.integers(0, 2, n)
        auc = E.cstat_after_matching(X, t, np.where(t == 1)[0], np.where(t == 0)[0], C=1.0)
        assert 0.44 < auc < 0.56
        X[:, 0] += 1.5 * t
        auc2 = E.cstat_after_matching(X, t, np.where(t == 1)[0], np.where(t == 0)[0], C=1.0)
        assert auc2 > 0.75

    def test_trial_common_sql_fragments(self):
        assert code_like("c", ["I50", "I21"]) == "(c LIKE 'I50%' OR c LIKE 'I21%')"
        assert "regexp_replace" in mrn_key("MRN")
        assert suppress(0) == 0 and suppress(5) == "<11" and suppress(11) == 11


if __name__ == '__main__':
    unittest.main()
