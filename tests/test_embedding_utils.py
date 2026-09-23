import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from embedding_utils import anisotropy_report, labels_from_covariates, preprocess, probe_gate


class EmbeddingUtilsTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(0)

    def test_collapse_detected_and_centering_recovers_spread(self):
        signal = self.rng.normal(size=(400, 16))
        collapsed = 1000.0 + 1e-3 * signal  # large shared offset, tiny variation
        r = anisotropy_report(collapsed)
        self.assertTrue(r["collapsed"])
        self.assertLess(r["raw_pair_cosdist_q05_50_95"][1], 1e-6)
        self.assertGreater(r["centered_pair_cosdist_q05_50_95"][1], 0.5)
        self.assertFalse(anisotropy_report(signal)["collapsed"])

    def test_preprocess_shapes_and_unit_norm(self):
        X = self.rng.normal(size=(100, 20)) + 5
        Z, pcs = preprocess(X, k=8)
        self.assertEqual(Z.shape, (100, 8))
        self.assertEqual(pcs.shape, (100, 8))
        np.testing.assert_allclose(np.linalg.norm(Z, axis=1), 1.0, atol=1e-9)
        np.testing.assert_allclose(pcs.mean(0), 0.0, atol=1e-9)
        _, full = preprocess(X, k=None)
        self.assertEqual(full.shape[1], 20)

    def test_gate_passes_informative_and_fails_noise(self):
        n = 600
        y = self.rng.integers(0, 2, n)
        informative = np.c_[y + 0.3 * self.rng.normal(size=n), self.rng.normal(size=(n, 4))]
        noise = self.rng.normal(size=(n, 5))
        labels = pd.DataFrame({"male": y.astype(float)})
        thr = {"male": 0.85}
        self.assertTrue(probe_gate(informative, labels, thresholds=thr)["pass"].iloc[0])
        self.assertFalse(probe_gate(noise, labels, thresholds=thr)["pass"].iloc[0])

    def test_gate_skips_missing_labels_and_respects_nan(self):
        labels = pd.DataFrame({"afib": [0.0, 1.0] * 50 + [np.nan] * 10})
        out = probe_gate(self.rng.normal(size=(110, 3)), labels, modality="ehr")
        self.assertEqual(list(out["label"]), ["afib"])
        self.assertEqual(int(out["n"].iloc[0]), 100)

    def test_labels_from_covariates(self):
        cov = pd.DataFrame({"recorded_sex": ["Male", "Female"], "age_at_index": [70, 50],
                            "atrial_fibrillation": [1, 0], "lvef": [30.0, np.nan]})
        lab = labels_from_covariates(cov)
        self.assertEqual(lab["male"].tolist(), [1.0, 0.0])
        self.assertEqual(lab["age_ge_65"].tolist(), [1.0, 0.0])
        self.assertTrue(np.isnan(lab["lvef_le_40"].iloc[1]))


if __name__ == "__main__":
    unittest.main()
