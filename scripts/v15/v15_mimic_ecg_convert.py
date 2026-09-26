#!/usr/bin/env python
"""MIMIC-IV-ECG WFDB -> Yale all_ecgs npy layout (v1.5 external pass).

Yale layout (verified 2026-09-26 against a sample of all_ecgs): float32, shape (5000, 12),
millivolts, 500 Hz, 10 s, leads I, II, III, aVR, aVL, aVF, V1-V6. MIMIC-IV-ECG headers store
I, II, III, aVR, aVF, aVL, V1-V6 (aVL/aVF swapped relative to Yale), so leads are reordered by
header name, never by position. Units are converted to mV from the header; fs != 500 is
resampled to 500 Hz. Short NaN dropouts (<= MAX_NAN_FRAC per lead) are linearly interpolated;
records with more missingness, < 10 s, missing leads or an all-flat signal are failures.

The output fileID is the MIMIC study_id (flat file <study_id>.npy under the npy root).
Needs wfdb on PYTHONPATH (/mnt/raid0/rbc58/ecg-tte/software/claude-v15-wfdb).
"""
import os

import numpy as np

MIMIC_ROOT = "/mnt/raid0/bb2238/physionet/physionet.org/files/mimic-iv-ecg/1.0"
NPY_ROOT = "/mnt/raid0/rbc58/ecg-tte/shared/claude-v15-mimic-ecg-npy"
STD_LEADS = ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]
UNIT_TO_MV = {"mv": 1.0, "uv": 1e-3, "µv": 1e-3, "v": 1e3}
MAX_NAN_FRAC = 0.2
FS, N = 500, 5000


def _fill_nan(x):
    for j in range(x.shape[1]):
        col = x[:, j]
        bad = ~np.isfinite(col)
        if bad.any():
            good = np.flatnonzero(~bad)
            col[bad] = np.interp(np.flatnonzero(bad), good, col[good])
    return x


def convert(study_id, path, npy_root=NPY_ROOT, overwrite=False):
    """Convert one record. Returns (status, detail); status in {ok, exists, fail}."""
    import wfdb
    from scipy.signal import resample

    out = os.path.join(npy_root, f"{study_id}.npy")
    if os.path.exists(out) and not overwrite:
        return "exists", ""
    try:
        r = wfdb.rdrecord(os.path.join(MIMIC_ROOT, path))
    except Exception as e:  # noqa: BLE001
        return "fail", f"read:{type(e).__name__}"
    names = [str(s).strip().upper() for s in r.sig_name]
    try:
        cols = [names.index(l) for l in STD_LEADS]
    except ValueError:
        return "fail", "leads"
    x = np.asarray(r.p_signal, dtype=np.float64)[:, cols]
    try:
        scale = np.array([UNIT_TO_MV[str(r.units[c]).strip().lower()] for c in cols])
    except KeyError:
        return "fail", "units"
    x = x * scale
    if float(r.fs) != FS:
        n_src = int(round(10 * float(r.fs)))
        if x.shape[0] < n_src:
            return "fail", "short"
        x = x[:n_src]
        nan = ~np.isfinite(x)
        if (nan.mean(0) > MAX_NAN_FRAC).any():
            return "fail", "nan"
        x = resample(_fill_nan(x), N, axis=0)
    if x.shape[0] < N:
        return "fail", "short"
    x = x[:N]
    nan_frac = (~np.isfinite(x)).mean(0)
    if (nan_frac > MAX_NAN_FRAC).any():
        return "fail", "nan"
    if nan_frac.any():
        x = _fill_nan(x)
    if not (np.nanstd(x, axis=0) > 1e-6).any():
        return "fail", "flat"
    tmp = os.path.join(npy_root, f".{study_id}.tmp.npy")
    np.save(tmp, x.astype(np.float32))
    os.replace(tmp, out)
    return "ok", "nan_filled" if nan_frac.any() else ""
