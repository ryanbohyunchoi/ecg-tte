"""AoU statistics and cell runner vs the Yale originals (exact equality on synthetic data).

The Yale modules import only where the Yale trial caches exist (the H100 cluster); elsewhere (AoU) the parity tests skip
and only the self-contained tests run.
"""
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

S = Path(__file__).resolve().parents[1] / "scripts"
for p in (S / "aou", S, S / "v16", S / "v17", S / "v18", S / "v20", S / "v21"):
    sys.path.insert(0, str(p))
import aou_stats as ST  # noqa: E402
import aou_trial as AT  # noqa: E402

try:
    import sens_primary32 as SP  # noqa: E402
    import paper2_grid as P2  # noqa: E402
    import v16_engine as E  # noqa: E402
    YALE = True
except Exception:  # noqa: BLE001
    YALE = False


def synth_trial(n=600, seed=1, VARS=None):
    """Object with the attributes run_cell reads; H holds one component per item of VARS."""
    rng = np.random.default_rng(seed)

    class T:
        pass
    T.t = (rng.uniform(size=n) < 0.4).astype(int)
    x = rng.normal(size=(n, 5)) + 0.5 * T.t[:, None]
    T.X = x
    T.y_t = rng.exponential(400, size=n).clip(1, 900)
    T.y_e = (rng.uniform(size=n) < 0.3).astype(int)
    T.y_ok = rng.uniform(size=n) > 0.02
    cols = {}
    for c, _, _ in VARS:
        if c == "mean_meds":
            for j in range(3):
                cols[f"meds::m{j}"] = (rng.uniform(size=n) < 0.3 + 0.1 * T.t).astype(float)
        elif c == "mean_util":
            cols["util::outpatient_visits"] = rng.poisson(5, size=n).astype(float)
        elif c == "B_mean":
            for j in range(4):
                cols[f"B::dx_X{j}"] = (rng.uniform(size=n) < 0.2).astype(float)
        elif c == "smd_prog_full":
            cols["prog_full"] = rng.normal(size=n)
        elif c.startswith("smd_obs_"):
            v = rng.normal(size=n) + 0.3 * x[:, 0]
            v[rng.uniform(size=n) < 0.3] = np.nan
            cols["obs_" + c[len("smd_obs_"):]] = v
        else:
            v = rng.normal(size=n) + 0.2 * x[:, 1]
            v[rng.uniform(size=n) < 0.5] = np.nan
            cols[c] = v
    T.H = pd.DataFrame(cols)
    return T


def synth_cells(trials, VN, seed=3):
    rng = np.random.default_rng(seed)
    rows = []
    for i, t in enumerate(trials):
        rows.append(dict(trial=t, loghr=rng.normal(0, 0.3), se=abs(rng.normal(0.1, 0.03)) + 0.02, rb=rng.normal(-0.1, 0.2),
                         rs=0.08 + 0.01 * i, ex58="" if i % 3 else VN[0],
                         **{f"smd:{c}": abs(rng.normal(0.08, 0.05)) if rng.uniform() > 0.1 else np.nan for c in VN}))
    return pd.DataFrame(rows)


class SelfContained(unittest.TestCase):
    def test_rubin(self):
        b, se = ST.rubin([0.1, 0.2, 0.3], [0.1, 0.1, 0.1])
        self.assertAlmostEqual(b, 0.2)
        self.assertAlmostEqual(se, np.sqrt(0.01 + (1 + 1 / 3) * 0.01))
        self.assertTrue(np.isnan(ST.rubin([np.nan, np.nan], [0.1, 0.1])[0]))
        self.assertEqual(ST.rubin([0.5, np.nan], [0.2, 0.1]), (0.5, 0.2))

    def test_signflip_small(self):
        self.assertAlmostEqual(ST.signflip_1s([1.0, 1.0, 1.0]), 1 / 8)
        self.assertAlmostEqual(ST.p2s([1.0, 1.0, 1.0]), 2 / 8)

    def test_var_components_survey(self):
        H = pd.DataFrame({"sv_smoke_ever": [1.0], "obs_sbp": [120.0], "meds::a": [1.0]})
        vc = AT.var_components(H, [("sv_smoke_ever", "", ""), ("smd_obs_sbp", "", ""), ("mean_meds", "", "")])
        self.assertEqual(vc, {"sv_smoke_ever": ["sv_smoke_ever"], "smd_obs_sbp": ["obs_sbp"], "mean_meds": ["meds::a"]})


@unittest.skipUnless(YALE, "Yale modules not importable here")
class YaleParity(unittest.TestCase):
    def test_run_cell_equals_v16_engine(self):
        T = synth_trial(VARS=E.VARS)
        for est, psm in SP.CONFIGS.values():
            a = ST.run_cell(T, T.X, E.VARS, estimator=est, ps_model=psm)
            b = E.run_cell(T, T.X, estimator=est, ps_model=psm, cstat=None)
            for k in ["loghr", "se", "n", "n_t", "n_c", "n_pairs", "ess_t", "ess_c", "mean_smd", "n_vars"] + [f"smd:{c}" for c, _, _ in E.VARS]:
                x, y = a[k], b[k]
                self.assertTrue((np.isnan(x) and np.isnan(y)) if isinstance(x, float) and np.isnan(x) else x == y, (est, k, x, y))

    def test_signflip_and_tests(self):
        rng = np.random.default_rng(0)
        for k in (5, 11, 20):
            d = rng.normal(0.02, 0.05, size=k)
            self.assertEqual(ST.signflip_1s(d), SP.V.signflip_1s(d))
            self.assertEqual(ST.p1s(d), SP.p1s(d))
            self.assertEqual(ST.p2s(d), SP.p2s(d))
        B, Ev = rng.uniform(0.05, 0.2, 30), rng.uniform(0.05, 0.2, 30)
        self.assertEqual(ST.relred_ci(B, Ev), SP.relred_ci(B, Ev))
        la, lb, rb = rng.normal(size=12), rng.normal(size=12), rng.normal(size=12)
        self.assertEqual(ST.bshuf(la, lb, rb, ndraw=500), SP.bshuf(la, lb, rb, ndraw=500))
        self.assertEqual(ST.bshuf2(la, lb, rb, ndraw=500), P2.bshuf2(la, lb, rb, ndraw=500))
        self.assertTrue(np.array_equal(ST.bh_fdr([0.01, 0.2, np.nan, 0.03]), E.bh_fdr([0.01, 0.2, np.nan, 0.03]), equal_nan=True))

    def test_per_trial_and_contrast_row(self):
        tr = list(SP.ALL[:12])
        ga, gb = synth_cells(tr, SP.VN, 3), synth_cells(tr, SP.VN, 4)
        Fa, SMa = ST.per_trial(ga, SP.VN)
        Fa0, SMa0 = SP.per_trial(ga)
        pd.testing.assert_frame_equal(Fa, Fa0)
        pd.testing.assert_frame_equal(SMa, SMa0)
        Fb, SMb = ST.per_trial(gb, SP.VN)
        CLk = SP.V.cluster_of()
        CLn = {t: CLk[SP.KEY[t]] for t in tr}
        keep = [c for c in SP.VN if not c.startswith("pp_LV")]
        for side in ("one", "two"):
            r = ST.contrast_row(Fa, Fb, tr, side, CLn, P2.mask(SMa, keep), P2.mask(SMb, keep))
            r0 = SP.contrast_row(Fa, Fb, tr, side, CLk, P2.mask(SMa, keep), P2.mask(SMb, keep))
            self.assertEqual(set(r), set(r0))
            for k in r:
                self.assertTrue(r[k] == r0[k] or (pd.isna(r[k]) and pd.isna(r0[k])), (side, k, r[k], r0[k]))
        self.assertEqual(ST.agree_metrics(Fa), SP.agree_metrics(Fa))


if __name__ == "__main__":
    unittest.main()
