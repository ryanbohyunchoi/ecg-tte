"""CHS emulation analysis on synthetic data: lock guard; the ECG improves held-out balance when it carries the confounder."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "bdc"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
try:
    import chs_emulate as CE  # noqa: E402
    import chs_cohort as CH  # noqa: E402
    OK = True
except SystemExit:
    OK = False


@unittest.skipUnless(OK, "lifelines / scikit-learn not installed")
class CHSEmulate(unittest.TestCase):
    def test_guard_and_balance(self):
        with self.assertRaises(SystemExit):
            CE.main([])
        rng = np.random.default_rng(0)
        n = 1200
        lvm = rng.normal(150, 30, n)
        z = (lvm - 150) / 30
        arm = (rng.random(n) < 1 / (1 + np.exp(-1.2 * z))).astype(int)   # treatment driven by held-out LV mass
        D = pd.DataFrame(dict(id=[str(i) for i in range(n)], EMU="E1_ccb_vs_thiazide", arm=arm, k=rng.integers(3, 8, n),
                              AGE=rng.normal(73, 5, n), MALE=rng.integers(0, 2, n), BLACK=0.0, HTN=1.0, DIAB=0.0, CAD=0.0,
                              AF=np.nan, HF=0.0, SMOKE=0.0, cluster="thiazide", ECG_FILE=[f"f{i}.xml" for i in range(n)]))
        for it in CH.HELD:
            D[it] = rng.normal(0, 1, n)
        D["echo_lv_mass"] = lvm
        D["echo_septum"] = lvm / 15 + rng.normal(0, 0.5, n)
        for o in CE.OUTS:
            T = rng.exponential(2000 / np.exp(0.5 * z))
            D[f"T_{o}"], D[f"E_{o}"] = np.minimum(T, 1800), (T < 1800).astype(int)
        E = pd.DataFrame(rng.normal(0, 1, (n, 64)), columns=[f"e{j}" for j in range(64)])
        E.iloc[:, :4] += 1.5 * z[:, None]
        E.insert(0, "ECG_FILE", D.ECG_FILE)
        E.insert(0, "id", D.id)
        with tempfile.TemporaryDirectory() as t:
            os.environ["BDC_RESTRICTED"], os.environ["BDC_TTE_OUT"] = f"{t}/r", f"{t}/o"
            Path(f"{t}/r").mkdir()
            D["row"] = np.arange(n)
            D.to_pickle(f"{t}/r/chs_emulations.pkl")
            # code features: one code strongly tied to treatment, many noise codes
            rows = [(i, "D:401") for i in range(n) if rng.random() < (0.6 if arm[i] else 0.1)]
            rows += [(i, f"M:X{j}06") for i in range(n) for j in range(30) if rng.random() < 0.1]
            pd.DataFrame(rows, columns=["row", "code"]).to_pickle(f"{t}/r/chs_codes.pkl")
            E.to_pickle(f"{t}/r/chs_ecg_bcl.pkl")
            CE.main(["--protocol-locked", "--run", "test"])
            C = pd.read_csv(Path(t) / "o" / "chs_emulate" / "test" / "cells.csv").set_index("arm")
            self.assertLess(C.loc["base+ecg", "mean_smd_echo"], 0.7 * C.loc["base", "mean_smd_echo"])
            self.assertGreater(C.loc["base+perm", "mean_smd_echo"], 0.8 * C.loc["base", "mean_smd_echo"])
            self.assertTrue(np.isfinite(C.loc["base+ecg", "loghr_primary"]))
            self.assertIn("codes+ecg", C.index)
            self.assertGreater(int(C.loc["codes", "n_code_features"]), 10)
            self.assertLess(C.loc["codes+ecg", "mean_smd_echo"], C.loc["codes", "mean_smd_echo"])


if __name__ == "__main__":
    unittest.main()
