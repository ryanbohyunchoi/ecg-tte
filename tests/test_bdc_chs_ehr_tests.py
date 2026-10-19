"""CHS pre-specified added-information tests on synthetic data: the information test must credit a representation that
carries held-out signal beyond PS-Codes and not one that is pure noise; the multi-draw placebo must run and rank the real
arm; the ladder (PS-Demo, CVD10) and PS-Codes + EHR arms must appear in chs_emulate."""
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
    import chs_cohort as CH  # noqa: E402
    import chs_emulate as CE  # noqa: E402
    import chs_ehr_tests as CT  # noqa: E402
    OK = True
except SystemExit:
    OK = False


@unittest.skipUnless(OK, "lifelines / scikit-learn not installed")
class CHSEHRTests(unittest.TestCase):
    def test_tests(self):
        rng = np.random.default_rng(1)
        n = 1200
        lvm = rng.normal(150, 30, n)
        z = (lvm - 150) / 30
        arm = (rng.random(n) < 1 / (1 + np.exp(-1.2 * z))).astype(int)
        D = pd.DataFrame(dict(id=[str(i) for i in range(n)], EMU="E1_ccb_vs_thiazide", arm=arm, k=rng.integers(3, 8, n),
                              AGE=rng.normal(73, 5, n), MALE=rng.integers(0, 2, n), BLACK=0.0, HTN=1.0, DIAB=0.0, CAD=0.0,
                              AF=0.0, HF=0.0, SMOKE=0.0, CKD=rng.integers(0, 2, n).astype(float), COPD=0.0, PAD=0.0,
                              STROKE_TIA=0.0, VALVE=0.0, cluster="thiazide", ECG_FILE=[f"f{i}.xml" for i in range(n)]))
        D["k1"] = D.k - 1
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
            rows = [(i, "D:401") for i in range(n) if rng.random() < (0.6 if arm[i] else 0.1)]
            rows += [(i, f"M:X{j}06") for i in range(n) for j in range(30) if rng.random() < 0.1]
            pd.DataFrame(rows, columns=["row", "code"]).to_pickle(f"{t}/r/chs_codes.pkl")
            # 'clmbr': carries LV-mass signal the codes do not; 'backbone': pure noise
            S = pd.DataFrame(rng.normal(0, 1, (n, 16)), columns=[f"c{j}" for j in range(16)])
            S.iloc[:, :3] += 1.2 * z[:, None]
            S.insert(0, "row", D.row)
            S.to_pickle(f"{t}/r/chs_clmbr.pkl")
            B = pd.DataFrame(rng.normal(0, 1, (n, 16)), columns=[f"b{j}" for j in range(16)])
            B.insert(0, "row", D.row)
            B.to_pickle(f"{t}/r/chs_ehr_backbone.pkl")
            CT.main(["info", "--draws", "3"])
            I = pd.read_csv(Path(t) / "o" / "chs_ehr_tests" / "info.csv")
            lv = I[I["item"] == "echo_lv_mass"].set_index("rep")
            self.assertGreater(lv.loc["clmbr", "r2_codes_x"] - lv.loc["clmbr", "r2_codes"], 0.1)
            self.assertLess(abs(lv.loc["backbone", "r2_codes_x"] - lv.loc["backbone", "r2_codes"]), 0.02)
            self.assertGreater(lv.loc["ecg", "r2_codes_x"] - lv.loc["ecg", "r2_codes"], 0.1)
            rep = (Path(t) / "o" / "chs_ehr_tests" / "report_info.md").read_text()
            self.assertIn("| backbone |", rep)
            CT.main(["noise", "--draws", "4"])
            N = pd.read_csv(Path(t) / "o" / "chs_ehr_tests" / "noise.csv")
            self.assertEqual(set(N.rep), {"ecg", "clmbr", "backbone"})
            self.assertEqual(int((N.draw == -1).sum()), 5)             # ecg/base + 2 reps x {base, codes}
            self.assertEqual(int((N.draw >= 0).sum()), 5 * 4)
            g = N[(N.rep == "ecg") & (N.draw == -1)].iloc[0]
            self.assertLess(g.m_arm, 0.8 * g.m_ref)                    # the ECG carries the confounder
            self.assertIn("beyond chance", (Path(t) / "o" / "chs_ehr_tests" / "report_noise.md").read_text())
            # ladder and PS-Codes + EHR arms in the main analysis
            CE.main(["--protocol-locked", "--run", "lad", "--ladder", "--ehr", "clmbr"])
            C = pd.read_csv(Path(t) / "o" / "chs_emulate" / "lad" / "cells.csv").set_index("arm")
            for a_ in ("demo", "demo+ecg", "demo+perm", "cvd10", "cvd10+ecg", "cvd10+perm", "codes+ehr", "codes+permehr"):
                self.assertIn(a_, C.index)
            self.assertLess(C.loc["cvd10+ecg", "mean_smd_echo"], C.loc["cvd10", "mean_smd_echo"])


if __name__ == "__main__":
    unittest.main()
