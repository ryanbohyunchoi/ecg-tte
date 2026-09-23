"""Run the upstream BCL embedder with the input-scale fix.

Bug (found 2026-09-23): BCL checkpoints were trained on ECGs in microvolts, but
/mnt/raid0/bb2238/signals/preprocessed/all_ecgs stores millivolts. Feeding mV
makes the eval-mode BatchNorm inputs ~1000x too small, so every ECG maps to
~the same vector (COMET: mean pairwise cosine ~1.0000).

This wrapper multiplies every loaded waveform by --scale (default 1000) and
then calls the upstream `bcl_embed_torch.main`. Also pass a formats CSV with
no 250 Hz flags: all_ecgs files are already 500 Hz, and a `5_0` flag makes
process_ecg take 5 s and stretch it to 10 s.

Usage:
  python scripts/bcl_embed_uv.py --upstream-dir <.../upstream> [--scale 1000] -- <bcl_embed_torch args>
"""
import argparse
import sys


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-dir", required=True)
    ap.add_argument("--scale", type=float, default=1000.0)
    args, rest = ap.parse_known_args()
    if rest and rest[0] == "--":
        rest = rest[1:]
    sys.path.insert(0, args.upstream_dir)

    from modules import utils_torch
    original = utils_torch.load_ecg

    def load_scaled(fid, *a, **k):
        return original(fid, *a, **k) * args.scale

    utils_torch.load_ecg = load_scaled
    import bcl_embed_torch
    sys.argv = [bcl_embed_torch.__file__] + rest
    bcl_embed_torch.main()


if __name__ == "__main__":
    main()
