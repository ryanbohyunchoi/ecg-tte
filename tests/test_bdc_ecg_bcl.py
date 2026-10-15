"""Standalone BCL embedder and MUSE converter.

Parity tests need the H100 (lab checkpoint, stored MIMIC embeddings and npy ECGs); elsewhere they skip and only the
synthetic converter test runs.
"""
import base64
import glob
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "bdc"))
import ecg_bcl as EB  # noqa: E402

CKPT = ("/mnt/nfs_model_saves/signal_model_saves/12Lead_BCL_training/CNN0_lead_time_transformer_10s_500Hz"
        "_BCL_LR0.0001_Dropout0.5_08_26_2026/trained_12lead_30.pt")
MIMIC_BCL = "/mnt/raid0/rbc58/ecg-tte/audits/claude-v15-mimic-bcl-aristotle/embeddings"
MIMIC_NPY = "/mnt/raid0/rbc58/ecg-tte/shared/claude-v15-mimic-ecg-npy"
YALE_NPY = "/mnt/raid0/bb2238/signals/preprocessed/all_ecgs"
try:
    import torch  # noqa: F401
    TORCH = True
except ImportError:
    TORCH = False


def to_muse(sig_uv: np.ndarray, upb=4.88, fs=500) -> bytes:
    """MUSE-like XML from a (5000, 12) uV signal in Yale order, storing only I, II, V1-V6 (as MUSE does)."""
    keep = {"I": 0, "II": 1, "V1": 6, "V2": 7, "V3": 8, "V4": 9, "V5": 10, "V6": 11}
    leads = []
    for name, j in keep.items():
        q = np.round(sig_uv[:, j] / upb).astype("<i2")
        leads.append(f"<LeadData><LeadSampleCountTotal>{len(q)}</LeadSampleCountTotal><LeadAmplitudeUnitsPerBit>{upb}"
                     f"</LeadAmplitudeUnitsPerBit><LeadAmplitudeUnits>MICROVOLTS</LeadAmplitudeUnits><LeadID>{name}</LeadID>"
                     f"<WaveFormData>{base64.b64encode(q.tobytes()).decode()}</WaveFormData></LeadData>")
    median = "<Waveform><WaveformType>Median</WaveformType><SampleBase>500</SampleBase></Waveform>"
    return (f"<RestingECG>{median}<Waveform><WaveformType>Rhythm</WaveformType><SampleBase>{fs}</SampleBase>"
            f"{''.join(leads)}</Waveform></RestingECG>").encode()


class ConverterSynthetic(unittest.TestCase):
    def test_derived_leads(self):
        rng = np.random.default_rng(0)
        i_, ii = rng.normal(0, 300, 5000), rng.normal(0, 300, 5000)
        v = rng.normal(0, 500, (5000, 6))
        sig = np.c_[i_, ii, ii - i_, -(i_ + ii) / 2, i_ - ii / 2, ii - i_ / 2, v]
        out = EB.muse_to_uv(to_muse(sig))
        self.assertEqual(out.shape, (5000, 12))
        self.assertLess(np.abs(out - sig).max(), 4.88 * 1.5 + 1e-6)  # quantisation (derived leads add two errors)

    def test_rejects(self):
        bad = b"<RestingECG><Waveform><WaveformType>Median</WaveformType></Waveform></RestingECG>"
        with self.assertRaises(ValueError):
            EB.muse_to_uv(bad)


@unittest.skipUnless(TORCH and Path(CKPT).exists() and Path(MIMIC_BCL).exists(), "torch / lab checkpoint / MIMIC embeddings not here")
class Parity(unittest.TestCase):
    def test_matches_upstream_embeddings(self):
        idx = pd.read_csv(f"{MIMIC_BCL}/shard_00000_index.csv", keep_default_na=False, dtype={"fileID": str})
        E0 = np.load(f"{MIMIC_BCL}/shard_00000.npy")
        ok = (idx.error == "").to_numpy()
        rows = np.flatnonzero(ok)[:96]
        model, cfg = EB.load_encoder(CKPT)
        arrs = [EB.preprocess(np.load(f"{MIMIC_NPY}/{idx.fileID[r]}.npy") * 1000.0) for r in rows]  # mV -> uV
        E = EB.embed_arrays(model, arrs, batch=32)
        R = E0[rows]
        rel = (np.linalg.norm(E - R, axis=1) / np.linalg.norm(R, axis=1)).max()
        cos = (E * R).sum(1) / np.linalg.norm(E, axis=1) / np.linalg.norm(R, axis=1)
        # the stored embeddings were computed on an H100 (TF32 matmuls); CPU fp32 differs by ~0.1% (2026-10-15:
        # rel <= 0.0015, cos >= 0.9999989)
        self.assertLess(rel, 5e-3, f"max relative error {rel}")
        self.assertGreater(cos.min(), 0.99999)

    def test_slim_checkpoint_identical(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            EB.make_slim(CKPT, f"{t}/slim.pt")
            m1, _ = EB.load_encoder(CKPT)
            m2, _ = EB.load_encoder(f"{t}/slim.pt")
            x = EB.preprocess(np.random.default_rng(2).normal(0, 300, (5000, 12)))
            e1, e2 = EB.embed_arrays(m1, [x]), EB.embed_arrays(m2, [x])
            self.assertEqual(float(np.abs(e1 - e2).max()), 0.0)


@unittest.skipUnless(TORCH and Path(YALE_NPY).exists() and Path(CKPT).exists(), "torch / Yale npy / lab checkpoint not here")
class YaleRoundTrip(unittest.TestCase):
    """Yale ECGs re-encoded as MUSE XML (8 stored leads, 4.88 uV/bit) and decoded: the derived limb leads differ from
    Yale's stored ones by ~1-2% of peak amplitude (source acquisition/filtering), but the embedding is unchanged
    (2026-10-15, n=200: cosine median 0.99987, min 0.9984; different ECGs ~0.06; self-match 100%)."""

    def test_derived_limb_leads_do_not_move_the_embedding(self):
        model, _ = EB.load_encoder(CKPT)
        A, B = [], []
        for f in sorted(glob.glob(f"{YALE_NPY}/2015_06/*.npy"))[:60]:
            x = np.load(f).astype(np.float64)
            x = x.T if x.shape[0] == 12 else x
            if x.shape[0] < 5000 or not np.isfinite(x).all():
                continue
            uv = x[:5000, :12] * 1000.0
            d = EB.muse_to_uv(to_muse(uv))
            rel = np.median(np.abs(d[:, 2:6] - uv[:, 2:6])) / max(1.0, np.abs(uv[:, 2:6]).max())
            self.assertLess(rel, 0.05)  # lead order / formulas right (a wrong order gives errors ~100%)
            A.append(EB.preprocess(uv))
            B.append(EB.preprocess(d))
        self.assertGreater(len(A), 30)
        Ea, Eb = EB.embed_arrays(model, A), EB.embed_arrays(model, B)
        cos = (Ea * Eb).sum(1) / np.linalg.norm(Ea, axis=1) / np.linalg.norm(Eb, axis=1)
        self.assertGreater(cos.min(), 0.995)


if __name__ == "__main__":
    unittest.main()
