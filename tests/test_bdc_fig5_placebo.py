"""Multi-permutation placebo follow-up (fig5_placebo.py) on synthetic SPRINT-like data: reproduces the locked engine's
base / ECG / oracle estimates draw by draw and returns a placebo distribution."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "bdc"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
try:
    import fig5_sprint as F  # noqa: E402
    import fig5_placebo as FP  # noqa: E402
    from test_bdc_fig5 import make  # noqa: E402
    OK = True
except SystemExit:
    OK = False


@unittest.skipUnless(OK, "lifelines / scikit-learn not installed")
class Fig5Placebo(unittest.TestCase):
    def test_reproduces_locked_engine_and_placebo(self):
        with tempfile.TemporaryDirectory() as t:
            os.environ["BDC_RESTRICTED"] = f"{t}/r"
            os.environ["BDC_TTE_OUT"] = f"{t}/o"
            make(Path(t) / "r")
            F.main(["--run", "lock", "--confounders", "EGFR", "--ors", "3", "--draws", "8", "--workers", "2"])
            FP.main(["--run", "pl", "--confounders", "EGFR", "--ors", "3", "--draws", "8", "--perms", "3", "--workers", "2"])
            o = Path(t) / "o" / "fig5_sprint"
            a = pd.read_csv(o / "lock" / "draws.csv")
            b = pd.read_csv(o / "pl" / "draws.csv")
            for arm in ("base", "base+ecg", "oracle"):
                x = a[a.arm == arm].set_index("draw").loghr.sort_index()
                y = b[b.arm == arm].set_index("draw").loghr.sort_index()
                self.assertLess(float((x - y).abs().max()), 1e-10, arm)
            S = pd.read_csv(o / "pl" / "summary.csv").iloc[0]
            self.assertEqual(int(S.perms), 3)
            self.assertGreater(S.gap_ecg, S.gap_perm_mean)  # the synthetic ECG carries C
            self.assertIn("smd_EGFR_LT60_ecg", S.index)
            self.assertTrue((o / "pl" / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
