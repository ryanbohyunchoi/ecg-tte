"""CHS audit on the synthetic emulation data of test_bdc_chs_emulate: reproduces the locked run, chance floor, consistency."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "bdc"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import chs_audit as CA  # noqa: E402
    import chs_emulate as CE  # noqa: E402
    import chs_cohort as CH  # noqa: E402
    OK = True
except SystemExit:
    OK = False


@unittest.skipUnless(OK, "lifelines / scikit-learn not installed")
class CHSAudit(unittest.TestCase):
    def test_audit(self):
        rng = np.random.default_rng(0)
        n = 1200
        lvm = rng.normal(150, 30, n)
        z = (lvm - 150) / 30
        arm = (rng.random(n) < 1 / (1 + np.exp(-1.2 * z))).astype(int)
        D = pd.DataFrame(dict(id=[str(i) for i in range(n)], EMU="E1_ccb_vs_thiazide", arm=arm, k=4, k1=3, day0=730.0,
                              day_k1=365.0, AGE=rng.normal(73, 5, n), MALE=rng.integers(0, 2, n), BLACK=0.0, HTN=1.0,
                              DIAB=0.0, CAD=0.0, AF=0.0, HF=0.0, SMOKE=0.0, cluster="thiazide",
                              ECG_FILE=[f"CHS_ECG_VISIT02_19900101_{i:05d}.xml" for i in range(n)]))
        for it in CH.HELD:
            D[it] = rng.normal(0, 1, n)
        D["echo_lv_mass"] = lvm
        D["echo_septum"] = lvm / 15 + rng.normal(0, 0.5, n)
        for o in CE.OUTS:
            T = rng.exponential(2000 / np.exp(0.5 * z))
            D[f"T_{o}"], D[f"E_{o}"] = np.minimum(T, 1800), (T < 1800).astype(int)
        D["row"] = np.arange(n)
        E = pd.DataFrame(rng.normal(0, 1, (n, 64)), columns=[f"e{j}" for j in range(64)])
        E.iloc[:, :4] += 1.5 * z[:, None]
        E.insert(0, "ECG_FILE", D.ECG_FILE)
        E.insert(0, "id", D.id)
        with tempfile.TemporaryDirectory() as t:
            os.environ["BDC_RESTRICTED"], os.environ["BDC_TTE_OUT"] = f"{t}/r", f"{t}/o"
            Path(f"{t}/r").mkdir()
            D.to_pickle(f"{t}/r/chs_emulations.pkl")
            E.to_pickle(f"{t}/r/chs_ecg_bcl.pkl")
            CE.main(["--protocol-locked"])        # the locked run
            CA.main([])
            I = pd.read_csv(Path(t) / "o" / "chs_audit" / "integrity.csv")
            self.assertTrue(bool(I.reproduces_locked_base.iloc[0]) and bool(I["reproduces_locked_base+ecg"].iloc[0]))
            self.assertEqual(float(I.t0_after_k1_day.iloc[0]), 1.0)
            self.assertEqual(float(I.ecg_from_visit_k1.iloc[0]), 1.0)
            Q = pd.read_csv(Path(t) / "o" / "chs_audit" / "echo.csv")
            lv = Q[(Q.item == "echo_lv_mass")].set_index("arm")
            self.assertGreater(lv.loc["base", "smd"], lv.loc["base", "chance_p95"])   # real imbalance above chance
            self.assertLess(lv.loc["base+ecg", "smd"], lv.loc["base", "smd"])
            noise = Q[Q.item == "echo_lv_function"].set_index("arm")
            self.assertLess(noise.loc["base", "smd"], noise.loc["base", "chance_p95"] + 1e-9 + 0.2)
            rep = (Path(t) / "o" / "chs_audit" / "report.md").read_text()
            self.assertIn("Directional consistency", rep)


if __name__ == "__main__":
    unittest.main()
