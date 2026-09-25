"""v1.3 I5: second ECG representation = penultimate layer (input of the output layer) of the
PRESENT-SHD LVEF<40 signal CNN (score_shd_signal.MODELS['lvef_lt40']). Same ECG and preprocessing
as score_shd_signal.py (mV, first 5000 samples, median-filter baseline removal). Frozen, CPU.
Output (restricted): restricted_enc2.parquet (patient_key, embedding). No aggregate beyond counts.
Run with: TF_USE_LEGACY_KERAS=1 CUDA_VISIBLE_DEVICES="" <mosaic-env python> score_enc2.py ...
"""
import argparse
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_shd_signal import MODELS, UPSTREAM, load  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selection", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    os.umask(0o077)
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    sys.path.insert(0, UPSTREAM)
    import tensorflow as tf
    from modules.models import cnn_0
    sel = pd.read_parquet(a.selection)
    with Pool(a.workers) as pool:
        sigs = pool.map(load, sel.fileID.tolist(), chunksize=64)
    ok = np.array([s is not None for s in sigs])
    X = np.stack([s for s in sigs if s is not None])[..., None]
    m = cnn_0((None, 5000, 12, 1), 0.5, labels=["y"])
    m.load_weights(MODELS["lvef_lt40"]).assert_existing_objects_matched()
    sub = tf.keras.Model(m.input, m.get_layer("output").input)
    E = sub.predict(X, batch_size=256, verbose=0).astype(np.float32)
    pd.DataFrame({"patient_key": sel.patient_key.to_numpy()[ok], "embedding": list(E)}).to_parquet(out / "restricted_enc2.parquet")
    print(json.dumps(dict(n_ecg=int(len(sel)), n_scored=int(ok.sum()), dim=int(E.shape[1]))))


if __name__ == "__main__":
    main()
