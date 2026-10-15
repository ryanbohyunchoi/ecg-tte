"""Figure 5 engine on synthetic SPRINT-like data with a known answer (needs lifelines + scikit-learn)."""
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
    import fig5_sprint as F  # noqa: E402
    OK = True
except SystemExit:
    OK = False


def make(rdir: Path, n=2500, seed=0):
    rng = np.random.default_rng(seed)
    t = rng.integers(0, 2, n)
    egfr = rng.normal(70, 20, n)
    zc = (egfr - 70) / 20
    age = rng.normal(68, 9, n)
    # hazard depends strongly on the hidden C (eGFR) and on treatment (true HR 0.7)
    lam = 0.0004 * np.exp(np.log(0.7) * t - 0.8 * zc + 0.02 * (age - 68))
    T = rng.exponential(1 / lam)
    cens = 1600
    C = pd.DataFrame(dict(MASKID=[f"S{i:05d}" for i in range(n)], RANDASSIGN=t, AGE=age, FEMALE=rng.integers(0, 2, n),
                          RACE4=rng.choice(["WHITE", "BLACK", "HISPANIC", "OTHER"], n), SUB_CLINICALCVD=rng.integers(0, 2, n),
                          SUB_SUBCLINICALCVD=0, ATRIALFIB=rng.integers(0, 2, n), CONHEARTFAIL=0, SMOKE_3CAT=rng.integers(1, 4, n),
                          SBP=rng.normal(140, 15, n), DBP=78, N_AGENTS=2, ASPIRIN=1, STATIN=0, HEARTATT=0, EGFR=egfr,
                          SCREAT=1.0 / (egfr / 70), SUB_CKD=(egfr < 60).astype(int), LOG_UMALCR=rng.normal(2.5, 1, n),
                          BMI=rng.normal(30, 5, n), CHR=190.0, HDL=50.0, TRR=110.0, GLUR=97.0,
                          LOG_NTPROBNP=rng.normal(4.7, 1, n), LOG_HSTNI=rng.normal(1.5, 0.8, n), HRAVG=68.0, EDUCATION=7,
                          ECG_CV=rng.normal(1500, 600, n), LDL_CALC=rng.normal(110, 35, n),
                          T_PRIMARY=np.minimum(T, cens), EVENT_PRIMARY=(T < cens).astype(int),
                          T_PRIMARYORDEATH=np.minimum(T, cens), EVENT_PRIMARYORDEATH=(T < cens).astype(int)))
    rdir.mkdir(parents=True, exist_ok=True)
    C.to_pickle(rdir / "sprint_cohort.pkl")
    # "ECG embedding": 64 dims, a few carry a noisy copy of C, rest noise
    E = rng.normal(0, 1, (n, 64))
    E[:, :4] += 1.2 * zc[:, None]
    emb = pd.DataFrame(E, columns=[f"e{j}" for j in range(64)])
    emb.insert(0, "MASKID", C.MASKID)
    emb.to_pickle(rdir / "sprint_ecg_bcl.pkl")


@unittest.skipUnless(OK, "lifelines / scikit-learn not installed")
class Fig5Synthetic(unittest.TestCase):
    def test_known_answer(self):
        with tempfile.TemporaryDirectory() as t:
            os.environ["BDC_RESTRICTED"] = f"{t}/r"
            os.environ["BDC_TTE_OUT"] = f"{t}/o"
            make(Path(t) / "r")
            F.main(["--run", "test", "--confounders", "EGFR", "--ors", "3", "--draws", "12", "--workers", "2"])
            S = pd.read_csv(Path(t) / "o" / "fig5_sprint" / "test" / "summary.csv")
            g = S.set_index("arm")
            self.assertTrue(bool(g.loc["base", "gate_material_bias"]))
            # oracle close to truth, base biased
            self.assertLess(abs(g.loc["oracle", "bias"]), abs(g.loc["base", "bias"]) / 2)
            # ECG closes a real part of the gap; permuted ECG does not
            self.assertGreater(g.loc["base+ecg", "gap_closed"], 0.3)
            self.assertLess(abs(g.loc["base+perm", "gap_closed"]), 0.25)
            # balance on C improves with the ECG
            self.assertLess(g.loc["base+ecg", "mean_smd_c"], g.loc["base", "mean_smd_c"])
            # rich(-EGFR) must not contain EGFR or its derived inputs
            import json
            R = json.loads((Path(t) / "o" / "fig5_sprint" / "test" / "run.json").read_text())
            for k in ("EGFR", "SCREAT", "SUB_CKD"):
                self.assertNotIn(k, R["rich_inputs"]["EGFR"])
            self.assertTrue((Path(t) / "o" / "fig5_sprint" / "test" / "report.md").exists())

    def test_selection_preserves_share_and_bounds(self):
        rng = np.random.default_rng(3)
        z = rng.normal(0, 1, 5000)
        t = rng.integers(0, 2, 5000)
        ps, acc = F.selection(z, t, 3.0)
        self.assertAlmostEqual(ps.mean(), t.mean(), places=3)
        self.assertTrue((acc > 0).all() and (acc <= 1 + 1e-12).all())
        self.assertAlmostEqual(acc.max(), 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
